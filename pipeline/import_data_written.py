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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from blog.models import Post, Category, Tag

DATA_DIR = Path(__file__).parent / 'data' / 'data_written'


def import_data(dry_run: bool = False):
    if not DATA_DIR.exists():
        print(f"data_written 디렉토리 없음: {DATA_DIR}")
        sys.exit(1)

    author = User.objects.first()
    if not author:
        print("User가 없습니다.")
        sys.exit(1)

    categories = {cat.slug: cat for cat in Category.objects.all()}
    created = 0
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

        if Post.objects.filter(slug=slug).exists():
            print(f"  [SKIP] Post 이미 존재: {slug}")
            skipped += 1
            continue

        cat_slug = data.get('category_slug', 'data-engineering')
        category = categories.get(cat_slug) or categories.get('ai-ml')

        content = data.get('content', '')
        summary = data.get('summary', '')
        tags_raw = data.get('tags', [])

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

        created += 1
        print(f"  [CREATE] Post: {slug}")

    if not dry_run:
        print(f"\n완료: Post {created}개 생성, {skipped}개 스킵")
    else:
        print(f"\n[DRY-RUN 완료] 실제 변경 없음.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='data_written → Post import')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    args = parser.parse_args()
    import_data(dry_run=args.dry_run)
