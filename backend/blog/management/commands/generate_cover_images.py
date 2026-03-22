"""
커버 이미지 자동 생성 관리 명령어.

paper_cover + category_gradient는 무료 (SVG 템플릿),
architecture_diagram은 Claude API 사용 (~$2-5).

사용법:
  python manage.py generate_cover_images                    # 전체 (이미지 없는 것만)
  python manage.py generate_cover_images --category llm     # 카테고리 필터
  python manage.py generate_cover_images --post-type paper_review
  python manage.py generate_cover_images --slug gpt-4       # 단일 포스트
  python manage.py generate_cover_images --dry-run           # 미리보기
  python manage.py generate_cover_images --force             # 기존 덮어쓰기
  python manage.py generate_cover_images --strategy paper_cover  # 전략 강제
"""
import sys
import tempfile
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db.models import Q

from blog.models import Post

# pipeline 디렉토리를 path에 추가 (Docker: /app/pipeline, 로컬: repo root)
PIPELINE_DIR = Path('/app/pipeline')
if not PIPELINE_DIR.exists():
    PIPELINE_DIR = Path(__file__).resolve().parents[4] / 'pipeline'
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from cover_templates import (
    generate_paper_cover_svg,
    generate_category_cover_svg,
    generate_architecture_cover_prompt,
    classify_strategy,
)
from svg_utils import svg_to_png, sanitize_svg


class Command(BaseCommand):
    help = '커버 이미지가 없는 포스트에 자동으로 커버 이미지 생성'

    def add_arguments(self, parser):
        parser.add_argument('--category', type=str, help='카테고리 slug 필터')
        parser.add_argument('--post-type', type=str, help='포스트 타입 필터')
        parser.add_argument('--slug', type=str, help='특정 포스트 slug')
        parser.add_argument('--dry-run', action='store_true', help='미리보기 (변경 없음)')
        parser.add_argument('--force', action='store_true', help='기존 이미지 덮어쓰기')
        parser.add_argument('--strategy', type=str,
                            choices=['paper_cover', 'category_gradient', 'architecture_diagram'],
                            help='전략 강제 지정')

    def handle(self, *args, **options):
        qs = Post.objects.filter(status='published').select_related('category')

        if options['slug']:
            qs = Post.objects.filter(slug=options['slug']).select_related('category')
        elif not options['force']:
            qs = qs.filter(Q(cover_image='') | Q(cover_image__isnull=True))

        if options['category']:
            qs = qs.filter(
                Q(category__slug=options['category']) |
                Q(category__parent__slug=options['category'])
            )

        if options['post_type']:
            qs = qs.filter(post_type=options['post_type'])

        posts = list(qs.order_by('category__slug', 'title'))
        total = len(posts)

        self.stdout.write(f'대상 포스트: {total}개')
        self.stdout.write('=' * 60)

        generated = 0
        skipped = 0
        failed = 0

        for i, post in enumerate(posts, 1):
            cat_slug = post.category.slug if post.category else ''
            cat_name = post.category.name if post.category else ''
            cat_color = post.category.color if post.category else ''

            # 전략 결정
            has_arch = post.architecture_entries.exists()
            if options['strategy']:
                strategy = options['strategy']
            else:
                strategy = classify_strategy(cat_slug, post.post_type, has_arch)

            # force 모드가 아니면 기존 이미지 스킵
            if post.cover_image and not options['force']:
                self.stdout.write(f'  [{i}/{total}] [SKIP] 이미 존재: {post.slug}')
                skipped += 1
                continue

            if options['dry_run']:
                self.stdout.write(
                    f'  [{i}/{total}] [DRY-RUN] {post.title[:50]}'
                    f' (cat={cat_slug}, strategy={strategy})'
                )
                continue

            # SVG 생성
            svg_str = None
            if strategy == 'paper_cover':
                tag_names = list(post.tags.values_list('name', flat=True)[:5])
                date_str = ''
                if post.published_at:
                    date_str = post.published_at.strftime('%Y-%m-%d')
                elif post.created_at:
                    date_str = post.created_at.strftime('%Y-%m-%d')
                svg_str = generate_paper_cover_svg(
                    title=post.title,
                    summary=post.summary or '',
                    category_name=cat_name,
                    tags=tag_names,
                    date=date_str,
                )
            elif strategy == 'category_gradient':
                svg_str = generate_category_cover_svg(
                    title=post.title,
                    category_slug=cat_slug,
                    category_color=cat_color,
                )
            elif strategy == 'architecture_diagram':
                # Claude API 전략 — 별도 실행 필요
                self.stdout.write(
                    f'  [{i}/{total}] [SKIP-API] {post.slug}'
                    ' (architecture_diagram은 별도 실행 필요)'
                )
                skipped += 1
                continue

            if not svg_str:
                self.stdout.write(f'  [{i}/{total}] [FAIL] SVG 생성 실패: {post.slug}')
                failed += 1
                continue

            svg_str = sanitize_svg(svg_str)

            # SVG → PNG 변환
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = Path(tmp.name)

            success = svg_to_png(svg_str, tmp_path, output_width=1792, background_color=None)
            if not success:
                self.stdout.write(f'  [{i}/{total}] [FAIL] PNG 변환 실패: {post.slug}')
                tmp_path.unlink(missing_ok=True)
                failed += 1
                continue

            # 파일 저장
            png_bytes = tmp_path.read_bytes()
            tmp_path.unlink(missing_ok=True)

            filename = f'cover_{post.slug[:80]}.png'
            post.cover_image.save(filename, ContentFile(png_bytes), save=True)

            size_kb = len(png_bytes) / 1024
            self.stdout.write(
                f'  [{i}/{total}] [OK] {post.title[:40]}'
                f' ({strategy}, {size_kb:.0f}KB)'
            )
            generated += 1

        self.stdout.write('=' * 60)
        self.stdout.write(
            f'완료: 생성 {generated}개, 스킵 {skipped}개, 실패 {failed}개'
        )
