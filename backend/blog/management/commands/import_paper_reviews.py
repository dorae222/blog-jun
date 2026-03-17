"""
papers_written 디렉토리에서 Post(paper_review) + PostImage import Django management command.

사용법:
    python manage.py import_paper_reviews
    python manage.py import_paper_reviews --papers-dir /papers_written
    python manage.py import_paper_reviews --dry-run
"""
import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from blog.models import ArchitectureEntry, Category, Post, PostImage

# papers.csv category → DB slug (22개 매핑)
CATEGORY_SLUG_MAP = {
    'transformer':  'model-architecture',
    'nlp':          'model-architecture',
    'llm':          'model-architecture',
    'vision':       'model-architecture',
    'multimodal':   'model-architecture',
    'ssm':          'model-architecture',
    'moe':          'efficient-ai',
    'scaling':      'efficient-ai',
    'efficiency':   'efficient-ai',
    'alignment':    'alignment-rlhf',
    'finetuning':   'alignment-rlhf',
    'rag':          'rag-knowledge',
    'retrieval':    'rag-knowledge',
    'technique':    'core-techniques',
    'prompting':    'prompting-icl',
    'icl':          'prompting-icl',
    'benchmark':    'benchmark-eval',
    'evaluation':   'benchmark-eval',
    'agents':       'agents-tools',
    'tools':        'agents-tools',
    'data':         'data-security',
    'security':     'data-security',
}


def _upload_figure(post, fig_path: Path, stdout) -> str | None:
    """figure 파일을 PostImage로 업로드하고 media URL을 반환."""
    if not fig_path.exists():
        stdout.write(f"    [WARN] figure 파일 없음: {fig_path}")
        return None
    with open(fig_path, 'rb') as f:
        img = PostImage.objects.create(
            post=post,
            alt_text=fig_path.stem,
            original_path=str(fig_path),
        )
        img.image.save(fig_path.name, File(f), save=True)
    return img.image.url


def _replace_figure_paths(content: str, figure_url_map: dict) -> str:
    """마크다운 내 figures/ 상대 경로 → 서버 media URL 치환."""
    for local_path, media_url in figure_url_map.items():
        content = content.replace(f"figures/{local_path}", media_url)
        content = content.replace(f"./figures/{local_path}", media_url)
    return content


class Command(BaseCommand):
    help = "papers_written 디렉토리에서 Post(paper_review) import"

    def add_arguments(self, parser):
        parser.add_argument(
            '--papers-dir',
            default='/papers_written',
            help='papers_written 경로 (기본: /papers_written)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='변경 없이 미리보기',
        )

    def handle(self, *args, **options):
        papers_dir = Path(options['papers_dir'])
        dry_run = options['dry_run']
        prefix = "[DRY-RUN] " if dry_run else ""

        if not papers_dir.exists():
            self.stderr.write(f"papers_written 디렉토리 없음: {papers_dir}")
            return

        author = User.objects.first()
        if not author:
            self.stderr.write("User가 없습니다. createsuperuser를 먼저 실행하세요.")
            return

        categories = {cat.slug: cat for cat in Category.objects.all()}

        dirs = sorted(papers_dir.iterdir())
        created_posts = 0
        created_images = 0
        skipped = 0

        self.stdout.write(f"\n{prefix}import_paper_reviews 시작: {papers_dir}")
        self.stdout.write("=" * 60)

        for paper_dir in dirs:
            if not paper_dir.is_dir():
                continue

            content_json = paper_dir / 'content.json'
            if not content_json.exists():
                self.stdout.write(f"[SKIP] content.json 없음: {paper_dir.name}")
                continue

            with open(content_json, encoding='utf-8') as f:
                data = json.load(f)

            title = data.get('title', '').strip()
            if not title:
                self.stdout.write(f"[SKIP] title 없음: {paper_dir.name}")
                continue

            slug = data.get('slug') or slugify(title, allow_unicode=True)[:300]

            if Post.objects.filter(slug=slug).exists():
                self.stdout.write(f"  [SKIP] Post 이미 존재: {title}")
                skipped += 1
                continue

            # 카테고리 결정
            cat_key = data.get('sub_category') or data.get('category', '')
            cat_slug = CATEGORY_SLUG_MAP.get(cat_key, 'model-architecture')
            category = categories.get(cat_slug) or categories.get('ai-ml')

            content = data.get('content', '')
            summary = data.get('summary', '')

            if dry_run:
                self.stdout.write(f"  {prefix}Post 생성 예정: {title} → {cat_slug}")
                figures_dir = paper_dir / 'figures'
                if figures_dir.exists():
                    figs = list(figures_dir.iterdir())
                    self.stdout.write(f"    figures: {len(figs)}개")
                continue

            post = Post.objects.create(
                title=title,
                slug=slug,
                content=content,
                summary=summary,
                category=category,
                author=author,
                status='published',
                post_type='paper_review',
            )
            created_posts += 1
            self.stdout.write(f"  [CREATE] Post: {title}")

            # figures 업로드 및 URL 치환
            figures_dir = paper_dir / 'figures'
            figure_url_map = {}
            if figures_dir.exists():
                for fig_file in sorted(figures_dir.iterdir()):
                    if fig_file.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
                        continue
                    url = _upload_figure(post, fig_file, self.stdout)
                    if url:
                        figure_url_map[fig_file.name] = url
                        created_images += 1
                        self.stdout.write(f"    [IMG] {fig_file.name} → {url}")

            # 마크다운 내 figure 경로 치환 후 저장
            if figure_url_map:
                post.content = _replace_figure_paths(content, figure_url_map)
                post.save(update_fields=['content'])

            # related_architecture 연결
            arch_slug = data.get('related_architecture', '').strip()
            if arch_slug:
                try:
                    arch = ArchitectureEntry.objects.get(slug=arch_slug)
                    arch.related_post = post
                    arch.save(update_fields=['related_post'])
                    self.stdout.write(f"    [LINK] ArchitectureEntry 연결: {arch_slug}")
                except ArchitectureEntry.DoesNotExist:
                    self.stdout.write(f"    [WARN] ArchitectureEntry 없음: {arch_slug}")

        self.stdout.write("=" * 60)
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY-RUN 완료] 실제 변경 없음."))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"완료: Post {created_posts}개 생성, "
                f"PostImage {created_images}개 업로드, "
                f"{skipped}개 스킵"
            ))
