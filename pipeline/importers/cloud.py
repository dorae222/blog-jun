#!/usr/bin/env python3
"""
pipeline/data/cloud_written/*/content.json → Post(article) import/update

기존 Cloud 포스트의 content와 summary를 확장된 내용으로 업데이트하고,
없는 포스트는 새로 생성합니다.

사용법:
  python -m pipeline.importers.cloud --dry-run    # 변경 없이 미리보기
  python -m pipeline.importers.cloud              # 실제 임포트
"""
import json
import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from blog.models import Post, Category, Tag

DATA_DIR = Path(__file__).resolve().parent.parent / 'data' / 'cloud_written'


def import_cloud(dry_run: bool = False):
    if not DATA_DIR.exists():
        print(f"cloud_written 디렉토리 없음: {DATA_DIR}")
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

        title = data.get('title', '').strip()
        if not title:
            print(f"[SKIP] title 없음: {data_dir.name}")
            continue

        slug = data.get('slug') or slugify(title, allow_unicode=True)[:300]
        content = data.get('content', '')
        summary = data.get('summary', '')
        tags_raw = data.get('tags', [])
        cat_slug = data.get('category_slug', 'cloud')
        category = categories.get(cat_slug) or categories.get('cloud')

        if not category:
            print(f"[SKIP] 카테고리 없음: {cat_slug} → {slug}")
            skipped += 1
            continue

        existing = Post.objects.filter(slug=slug).first()

        if existing:
            # 기존 포스트 업데이트 (content, summary, category)
            if dry_run:
                old_len = len(existing.content or '')
                new_len = len(content)
                print(f"  [DRY-RUN UPDATE] {slug}: {old_len} → {new_len} chars, cat={cat_slug}")
            else:
                existing.content = content
                existing.summary = summary
                existing.category = category
                existing.save(update_fields=['content', 'summary', 'category'])
                # 태그 업데이트
                for tag_name in tags_raw:
                    tag_slug_val = slugify(tag_name, allow_unicode=True)[:100]
                    if not tag_slug_val:
                        continue
                    tag, _ = Tag.objects.get_or_create(
                        slug=tag_slug_val, defaults={'name': tag_name}
                    )
                    existing.tags.add(tag)
                print(f"  [UPDATE] {slug} ({cat_slug})")
            updated += 1
        else:
            # 새 포스트 생성
            if dry_run:
                words = len(content.split())
                print(f"  [DRY-RUN CREATE] {slug} ({words} words) → {cat_slug}")
            else:
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
                    tag_slug_val = slugify(tag_name, allow_unicode=True)[:100]
                    if not tag_slug_val:
                        continue
                    tag, _ = Tag.objects.get_or_create(
                        slug=tag_slug_val, defaults={'name': tag_name}
                    )
                    post.tags.add(tag)
                print(f"  [CREATE] {slug} ({cat_slug})")
            created += 1

    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"\n{prefix}완료: 생성 {created}개, 업데이트 {updated}개, 스킵 {skipped}개")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='cloud_written → Post import/update')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    args = parser.parse_args()
    import_cloud(dry_run=args.dry_run)
