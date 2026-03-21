#!/usr/bin/env python3
"""
기존 9개 AI 서브카테고리 → 7개로 재매핑하는 일회성 스크립트.

1. 기존 9개 slug에 할당된 포스트를 7개 slug로 이동
2. 빈 카테고리 삭제 (선택)

사용법:
  python pipeline/migrate_ai_categories.py --dry-run    # 미리보기
  python pipeline/migrate_ai_categories.py              # 실제 마이그레이션
"""
import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from blog.models import Post, Category

# 기존 9개 → 7개 매핑
REMAP = {
    'model-architecture': 'llm',       # 대부분 LLM 관련
    'efficient-ai':       'technique',
    'alignment-rlhf':     'technique',
    'rag-knowledge':      'technique',
    'core-techniques':    'technique',
    'prompting-icl':      'technique',
    'benchmark-eval':     'technique',
    'agents-tools':       'agent',
    'data-security':      'technique',
}


def migrate(dry_run: bool = False):
    categories = {cat.slug: cat for cat in Category.objects.all()}
    moved = 0

    for old_slug, new_slug in REMAP.items():
        old_cat = categories.get(old_slug)
        new_cat = categories.get(new_slug)

        if not old_cat:
            print(f"[SKIP] 기존 카테고리 없음: {old_slug}")
            continue
        if not new_cat:
            print(f"[SKIP] 대상 카테고리 없음: {new_slug} (seed_ai_categories 먼저 실행하세요)")
            continue

        posts = Post.objects.filter(category=old_cat)
        count = posts.count()

        if count == 0:
            print(f"  {old_slug} → {new_slug}: 포스트 없음")
            continue

        if dry_run:
            print(f"  [DRY-RUN] {old_slug} → {new_slug}: {count}개 이동 예정")
        else:
            posts.update(category=new_cat)
            print(f"  [MOVED] {old_slug} → {new_slug}: {count}개 이동 완료")

        moved += count

    # 빈 카테고리 정리 (선택)
    if not dry_run:
        for old_slug in REMAP.keys():
            old_cat = categories.get(old_slug)
            if old_cat and old_cat.post_set.count() == 0:
                print(f"  [DELETE] 빈 카테고리 삭제: {old_slug}")
                old_cat.delete()

    status = "DRY-RUN" if dry_run else "완료"
    print(f"\n[{status}] {moved}개 포스트 재매핑")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AI 카테고리 9→7 마이그레이션')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    args = parser.parse_args()
    migrate(dry_run=args.dry_run)
