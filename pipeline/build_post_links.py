#!/usr/bin/env python3
"""
모든 Post의 content에서 [[...]] 위키 링크를 찾아 PostLink를 일괄 생성.

사용법:
  python pipeline/build_post_links.py              # 실제 생성
  python pipeline/build_post_links.py --dry-run    # 변경 없이 미리보기
"""
import re
import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from blog.models import Post, PostLink


WIKI_LINK_RE = re.compile(r'\[\[([^\]|]+?)(?:\|[^\]]*?)?\]\]')


def build_links(dry_run: bool = False):
    posts = Post.objects.filter(status='published')
    # title → post 매핑 (소문자)
    title_map = {}
    slug_map = {}
    for p in posts:
        title_map[p.title.lower()] = p
        slug_map[p.slug.lower()] = p

    created = 0
    scanned = 0

    for post in posts:
        if not post.content:
            continue
        scanned += 1
        targets = WIKI_LINK_RE.findall(post.content)
        for target in targets:
            target_clean = target.strip()
            if not target_clean:
                continue

            # title 또는 slug로 매칭
            to_post = title_map.get(target_clean.lower()) or slug_map.get(target_clean.lower())
            if not to_post or to_post == post:
                continue

            if dry_run:
                print(f"  [DRY-RUN] {post.slug} → {to_post.slug} ('{target_clean}')")
                created += 1
                continue

            _, was_created = PostLink.objects.get_or_create(
                from_post=post,
                to_post=to_post,
                defaults={'link_text': target_clean},
            )
            if was_created:
                created += 1

    if dry_run:
        print(f"\n[DRY-RUN] {scanned}개 포스트 스캔, {created}개 PostLink 생성 예정")
    else:
        print(f"\n완료: {scanned}개 포스트 스캔, {created}개 PostLink 생성")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='위키 링크 → PostLink 일괄 생성')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    args = parser.parse_args()
    build_links(dry_run=args.dry_run)
