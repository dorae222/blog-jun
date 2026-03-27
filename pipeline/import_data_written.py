#!/usr/bin/env python3
"""
pipeline/data/data_written/*/content.json → Post(article) import

사용법:
  python pipeline/import_data_written.py              # 실제 임포트
  python pipeline/import_data_written.py --dry-run    # 변경 없이 미리보기
"""
import json
import sys
import os
import argparse
from pathlib import Path

_here = Path(__file__).resolve()
_backend = _here.parent.parent / 'backend'
if _backend.exists():
    sys.path.insert(0, str(_backend))
elif Path('/app/config').exists():
    sys.path.insert(0, '/app')
sys.path.insert(0, str(_here.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from blog.models import Post, Category, Tag

from utils.import_helpers import upload_figure, replace_figure_paths, get_default_author

DATA_DIR = Path(__file__).parent / 'data' / 'data_written'


def import_data(dry_run: bool = False, update: bool = False):
    if not DATA_DIR.exists():
        print(f"data_written 디렉토리 없음: {DATA_DIR}")
        sys.exit(1)

    author = User.objects.first()
    if not author:
        print("User가 없습니다.")
        sys.exit(1)

    categories = {cat.slug: cat for cat in Category.objects.all()}
    created = 0
    updated = 0
    skipped = 0

    for data_dir in sorted(DATA_DIR.iterdir()):
        if not data_dir.is_dir():
            continue

        content_json = data_dir / 'content.json'
        if not content_json.exists():
            print(f"[SKIP] content.json 없음: {data_dir.name}")
            continue

        with open(content_json, encoding='utf-8') as f:
            data = json.load(f)

        title = data.get('title_ko') or data.get('title', '').strip()
        if not title:
            print(f"[SKIP] title 없음: {data_dir.name}")
            continue

        slug = data.get('slug') or slugify(title, allow_unicode=True)[:300]

        existing = Post.objects.filter(slug=slug).first()
        if existing and not update:
            print(f"  [SKIP] Post 이미 존재: {slug}")
            skipped += 1
            continue

        cat_slug = data.get('category_slug', 'data-engineering')
        category = categories.get(cat_slug) or categories.get('ai-ml')

        # content.md 우선, 없으면 content.json의 content 필드 폴백
        content_md = data_dir / 'content.md'
        content = content_md.read_text(encoding='utf-8') if content_md.exists() else data.get('content', '')
        summary = data.get('summary', '')
        tags_raw = data.get('tags', [])

        if existing and update:
            if not dry_run:
                # figure 업로드 + 경로 치환
                figures_dir = data_dir / 'figures'
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
                existing.tags.clear()
                for tag_name in tags_raw:
                    tag_slug_val = slugify(tag_name, allow_unicode=True)[:100]
                    if not tag_slug_val:
                        continue
                    tag, _ = Tag.objects.get_or_create(slug=tag_slug_val, defaults={'name': tag_name})
                    existing.tags.add(tag)
                print(f"  [UPDATE] content + tags 업데이트: {slug}")
            else:
                print(f"  [DRY-RUN] 업데이트 예정: {slug}")
            updated += 1
            continue

        if dry_run:
            words = len(content.split())
            print(f"  [DRY-RUN] Post 생성 예정: {slug} ({words} words) → {cat_slug}")
            continue

        post = Post.objects.create(
            title=title,
            slug=slug,
            content=content,
            summary=summary,
            category=category,
            author=author,
            status='published',
            post_type='article',
            published_at=timezone.now(),
            is_pinned=data.get('is_pinned', False),
        )

        for tag_name in tags_raw:
            tag_slug = slugify(tag_name, allow_unicode=True)[:100]
            if not tag_slug:
                continue
            tag, _ = Tag.objects.get_or_create(
                slug=tag_slug,
                defaults={'name': tag_name},
            )
            post.tags.add(tag)

        # figures 업로드 및 URL 치환
        figures_dir = data_dir / 'figures'
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

        created += 1
        print(f"  [CREATE] Post: {slug}")

    if not dry_run:
        print(f"\n완료: Post {created}개 생성, {updated}개 업데이트, {skipped}개 스킵")
    else:
        print(f"\n[DRY-RUN 완료] 실제 변경 없음.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='data_written → Post import')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    parser.add_argument('--update', action='store_true', help='기존 포스트 content + tags 업데이트')
    args = parser.parse_args()
    import_data(dry_run=args.dry_run, update=args.update)
