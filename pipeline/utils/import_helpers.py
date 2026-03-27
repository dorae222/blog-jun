"""Import 스크립트 공통 유틸리티 — upload_figure, replace_figure_paths 등."""
import os
import sys
from pathlib import Path

# Django 부트스트랩
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / 'backend'
if _BACKEND_DIR.exists():
    if str(_BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(_BACKEND_DIR))
elif Path('/app/config').exists():
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')


def ensure_django():
    """Django가 초기화되어 있지 않으면 setup() 호출."""
    import django
    if not django.apps.apps.ready:
        django.setup()


def upload_figure(post, fig_path: Path, dry_run: bool = False) -> str | None:
    """figure 파일을 PostImage로 업로드하고 media URL을 반환."""
    if not fig_path.exists():
        print(f"    [WARN] figure 파일 없음: {fig_path}")
        return None
    if dry_run:
        print(f"    [DRY-RUN] figure 업로드 예정: {fig_path.name}")
        return f"/media/posts/dry-run/{fig_path.name}"

    from django.core.files import File
    from blog.models import PostImage

    with open(fig_path, 'rb') as f:
        img = PostImage.objects.create(
            post=post,
            alt_text=fig_path.stem,
            original_path=str(fig_path),
        )
        img.image.save(fig_path.name, File(f), save=True)
    return img.image.url


def replace_figure_paths(content: str, figure_url_map: dict) -> str:
    """마크다운 내 figures/ 상대 경로 → 서버 media URL 치환."""
    for local_path, media_url in figure_url_map.items():
        content = content.replace(f"figures/{local_path}", media_url)
        content = content.replace(f"./figures/{local_path}", media_url)
    return content


def upload_figures_for_post(
    post, figures_dir: Path, dry_run: bool = False, existing_figs: dict | None = None
) -> dict:
    """디렉토리 내 모든 figure를 업로드하고 {filename: url} 매핑을 반환."""
    figure_url_map = {}
    if not figures_dir.exists():
        return figure_url_map

    if existing_figs is None:
        existing_figs = {}

    for fig_path in sorted(figures_dir.iterdir()):
        if fig_path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'):
            continue
        if fig_path.name in existing_figs:
            figure_url_map[fig_path.name] = existing_figs[fig_path.name]
            continue
        url = upload_figure(post, fig_path, dry_run)
        if url:
            figure_url_map[fig_path.name] = url

    return figure_url_map


def get_default_author():
    """기본 작성자 (superuser 또는 첫 번째 사용자) 반환."""
    from django.contrib.auth.models import User
    return User.objects.filter(is_superuser=True).first() or User.objects.first()
