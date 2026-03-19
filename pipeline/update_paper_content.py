#!/usr/bin/env python3
"""
papers_written content.json → 기존 Post.content 업데이트

slug 기준으로 Post를 찾아 content 필드만 업데이트합니다.
사용법:
  python pipeline/update_paper_content.py            # 실제 업데이트
  python pipeline/update_paper_content.py --dry-run  # 미리보기
"""
import json
import os
import sys
import argparse
from pathlib import Path

# Django 설정
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

import django
django.setup()

from django.utils.text import slugify
from blog.models import Post


PAPERS_WRITTEN_DIR = Path(__file__).parent / 'data' / 'papers_written'


def main():
    parser = argparse.ArgumentParser(description='papers_written → Post.content 업데이트')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    args = parser.parse_args()
    dry_run = args.dry_run

    paper_dirs = sorted(PAPERS_WRITTEN_DIR.iterdir())
    updated = 0
    skipped = 0
    not_found = 0

    for paper_dir in paper_dirs:
        if not paper_dir.is_dir():
            continue

        content_json = paper_dir / 'content.json'
        if not content_json.exists():
            print(f"[SKIP] content.json 없음: {paper_dir.name}")
            continue

        with open(content_json, encoding='utf-8') as f:
            data = json.load(f)

        title = data.get('title', '').strip()
        slug = data.get('slug') or slugify(title, allow_unicode=True)[:300]
        content = data.get('content', '')

        try:
            post = Post.objects.get(slug=slug)
        except Post.DoesNotExist:
            print(f"[NOT FOUND] slug={slug} ({title})")
            not_found += 1
            continue

        if post.content == content:
            print(f"  [NO CHANGE] {title}")
            skipped += 1
            continue

        if dry_run:
            print(f"  [DRY-RUN] 업데이트 예정: {title} (id={post.id})")
            updated += 1
            continue

        post.content = content
        post.save(update_fields=['content'])
        print(f"  [UPDATED] {title} (id={post.id})")
        updated += 1

    mode = "(DRY-RUN) " if dry_run else ""
    print(f"\n{mode}완료: {updated}개 업데이트, {skipped}개 변경없음, {not_found}개 미발견")


if __name__ == '__main__':
    main()
