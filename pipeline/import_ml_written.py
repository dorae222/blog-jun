#!/usr/bin/env python3
"""
pipeline/data/ml_written/*/content.json → Post(article) + PDF 첨부 import

사용법:
  python pipeline/import_ml_written.py              # 실제 임포트
  python pipeline/import_ml_written.py --dry-run    # 변경 없이 미리보기
  python pipeline/import_ml_written.py --reset       # 기존 ml 포스트 모두 삭제 후 재임포트
"""
import json
import os
import sys
import argparse
from pathlib import Path

# Django 설정 — 로컬(backend/)과 Docker(/app) 모두 지원
_here = Path(__file__).resolve()
_backend = _here.parent.parent / 'backend'
if _backend.exists():
    sys.path.insert(0, str(_backend))          # 로컬: pipeline/../backend/
else:
    sys.path.insert(0, str(_here.parent.parent))  # Docker: /app (config/ 바로 아래)
sys.path.insert(0, str(_here.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

import django
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from blog.models import Post, Category, Tag

from utils.import_helpers import upload_figure, replace_figure_paths, get_default_author
from utils.category_mapper import CategoryMapper
from utils.post_factory import get_or_create_tags

_mapper = CategoryMapper()

ML_WRITTEN_DIR = Path(__file__).parent / 'data' / 'ml_written'


def import_ml(dry_run: bool = False, reset: bool = False, update: bool = False):
    if not ML_WRITTEN_DIR.exists():
        print(f"ml_written 디렉토리 없음: {ML_WRITTEN_DIR}")
        sys.exit(1)

    author = User.objects.first()
    if not author:
        print("User가 없습니다. createsuperuser를 먼저 실행하세요.")
        sys.exit(1)

    # ml 카테고리 조회 (없으면 생성)
    ml_category = _mapper.resolve_with_fallback('ml', 'article', 'ml')
    if ml_category is None:
        ml_category, cat_created = Category.objects.get_or_create(
            slug='ml',
            defaults={'name': 'ML', 'order': 10},
        )
        if cat_created:
            print(f"[INFO] Category 생성: ml")

    if reset and not dry_run:
        deleted, _ = Post.objects.filter(category=ml_category).delete()
        print(f"[RESET] 기존 ML 포스트 {deleted}개 삭제")

    dirs = sorted(ML_WRITTEN_DIR.iterdir())
    created_posts = 0
    updated_posts = 0
    skipped = 0

    for item_dir in dirs:
        if not item_dir.is_dir():
            continue

        content_json = item_dir / 'content.json'
        if not content_json.exists():
            print(f"[SKIP] content.json 없음: {item_dir.name}")
            continue

        with open(content_json, encoding='utf-8') as f:
            data = json.load(f)

        title = data.get('title', '').strip()
        title_ko = data.get('title_ko', '').strip()
        display_title = title_ko or title
        if not display_title:
            print(f"[SKIP] title 없음: {item_dir.name}")
            continue

        slug = data.get('slug') or slugify(title, allow_unicode=True)[:300]
        # content.md 우선, 없으면 content.json의 content 필드 폴백
        content_md = item_dir / 'content.md'
        content = content_md.read_text(encoding='utf-8') if content_md.exists() else data.get('content', '')
        summary = data.get('summary', '')
        tags_raw = data.get('tags', [])

        existing = Post.objects.filter(slug=slug).first()
        if existing and not update:
            print(f"  [SKIP] 이미 존재: {display_title}")
            skipped += 1
            continue
        if existing and update:
            if not dry_run:
                # figure 업로드 + 경로 치환 (update 시에도 필요)
                figures_dir = item_dir / 'figures'
                figure_url_map = {}
                if figures_dir.exists():
                    existing_figs = set(
                        pi.image.name.split('/')[-1]
                        for pi in existing.images.all()
                        if pi.image
                    )
                    for fig_file in sorted(figures_dir.iterdir()):
                        if fig_file.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}:
                            continue
                        if fig_file.name in existing_figs:
                            pi = existing.images.filter(image__endswith=fig_file.name).first()
                            if pi:
                                figure_url_map[fig_file.name] = pi.image.url
                            continue
                        url = upload_figure(existing, fig_file, dry_run=False)
                        if url:
                            figure_url_map[fig_file.name] = url
                            print(f"    [IMG] {fig_file.name} → {url}")

                updated_content = replace_figure_paths(content, figure_url_map) if figure_url_map else content
                existing.content = updated_content
                existing.summary = summary
                update_fields = ['content', 'summary']
                is_pinned = data.get('is_pinned', False)
                if is_pinned != existing.is_pinned:
                    existing.is_pinned = is_pinned
                    update_fields.append('is_pinned')
                existing.save(update_fields=update_fields)
                # 태그 갱신
                existing.tags.clear()
                for tag in get_or_create_tags(tags_raw):
                    existing.tags.add(tag)
                print(f"  [UPDATE] content + tags 업데이트: {display_title}")
            else:
                print(f"  [DRY-RUN] 업데이트 예정: {display_title}")
            updated_posts += 1
            continue
        pdf_attachment = data.get('pdf_attachment')

        if dry_run:
            print(f"  [DRY-RUN] 생성 예정: {display_title} (slug={slug})")
            if pdf_attachment:
                pdf_path = item_dir / 'figures' / pdf_attachment
                print(f"    PDF: {pdf_path} (exists={pdf_path.exists()})")
            continue

        post = Post.objects.create(
            title=display_title,
            slug=slug,
            content=content,
            summary=summary,
            category=ml_category,
            author=author,
            status='published',
            post_type='article',
            published_at=timezone.now(),
            source_path=str(content_json),
            is_pinned=data.get('is_pinned', False),
        )
        created_posts += 1
        print(f"  [CREATE] {display_title}")

        # 태그 연결
        for tag in get_or_create_tags(tags_raw):
            post.tags.add(tag)

        # figures 업로드 및 URL 치환
        figures_dir = item_dir / 'figures'
        figure_url_map = {}
        if figures_dir.exists():
            for fig_file in sorted(figures_dir.iterdir()):
                if fig_file.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}:
                    continue
                url = upload_figure(post, fig_file, dry_run=False)
                if url:
                    figure_url_map[fig_file.name] = url
                    print(f"    [IMG] {fig_file.name} → {url}")

        if figure_url_map:
            post.content = replace_figure_paths(content, figure_url_map)
            post.save(update_fields=['content'])

        # PDF 첨부
        if pdf_attachment:
            pdf_path = item_dir / 'figures' / pdf_attachment
            if pdf_path.exists():
                with open(pdf_path, 'rb') as pf:
                    post.pdf_file.save(pdf_path.name, File(pf), save=True)
                print(f"    [PDF] {pdf_path.name} 첨부 완료")
            else:
                print(f"    [WARN] PDF 파일 없음: {pdf_path}")

    if not dry_run:
        print(f"\n완료: Post {created_posts}개 생성, {updated_posts}개 업데이트, {skipped}개 스킵")
    else:
        print(f"\n[DRY-RUN 완료] 실제 변경 없음.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ml_written → Post import')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    parser.add_argument('--reset', action='store_true', help='기존 ML 포스트 삭제 후 재임포트')
    parser.add_argument('--update', action='store_true', help='기존 포스트 content 업데이트')
    args = parser.parse_args()
    import_ml(dry_run=args.dry_run, reset=args.reset, update=args.update)
