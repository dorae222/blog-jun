#!/usr/bin/env python3
"""
Cloud 카테고리 불필요 컨텐츠 정리.
삭제가 아닌 status='draft'로 변경하여 API 노출만 차단 (복구 가능).

사용법:
  python pipeline/cleanup_cloud.py --dry-run    # 변경 없이 대상 확인
  python pipeline/cleanup_cloud.py              # 실제 정리
"""
import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from django.db.models import Q
from blog.models import Post, Category

# 삭제 대상 키워드 (제목에 포함되면 가이드성 메모로 판단)
GUIDE_KEYWORDS = [
    '에러', '설치', '설정', 'Error', 'Install', 'Setup',
    'error', 'install', 'setup', '오류',
]


def cleanup_cloud(dry_run: bool = False):
    # Cloud 카테고리 및 하위 카테고리 조회
    cloud_cats = Category.objects.filter(
        Q(slug='cloud') | Q(parent__slug='cloud')
    )
    cloud_slugs = list(cloud_cats.values_list('slug', flat=True))

    if not cloud_slugs:
        print("Cloud 카테고리를 찾을 수 없습니다.")
        return

    posts = Post.objects.filter(
        category__slug__in=cloud_slugs,
        status='published',
    )
    total = posts.count()
    print(f"Cloud published 포스트: {total}개\n")

    to_draft = []

    for post in posts:
        reasons = []
        content_len = len(post.content or '')

        # 기준 1: 너무 짧은 메모
        if content_len < 200:
            reasons.append(f'short ({content_len}자)')

        # 기준 2: 가이드성 제목
        title_lower = post.title.lower()
        for kw in GUIDE_KEYWORDS:
            if kw.lower() in title_lower:
                reasons.append(f'guide keyword: {kw}')
                break

        # 기준 3: 낮은 quality_score
        if post.quality_score is not None and post.quality_score < 5:
            reasons.append(f'low quality ({post.quality_score})')

        # 유지 조건: 조회수 > 0이면 짧아도 유지
        if post.view_count and post.view_count > 0:
            continue

        # 유지 조건: 500자 이상이면서 가이드 키워드만 해당되는 경우 유지
        if content_len >= 500 and len(reasons) == 1 and 'guide keyword' in reasons[0]:
            continue

        if reasons:
            to_draft.append((post, reasons))

    print(f"Draft 변환 대상: {len(to_draft)}개\n")

    for post, reasons in to_draft:
        reason_str = ', '.join(reasons)
        if dry_run:
            print(f"  [DRY-RUN] {post.slug} — {reason_str}")
        else:
            post.status = 'draft'
            post.save(update_fields=['status'])
            print(f"  [DRAFT] {post.slug} — {reason_str}")

    keep = total - len(to_draft)
    if dry_run:
        print(f"\n[DRY-RUN] 유지: {keep}개, Draft 변환 예정: {len(to_draft)}개")
    else:
        print(f"\n완료: 유지: {keep}개, Draft 변환: {len(to_draft)}개")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Cloud 불필요 컨텐츠 정리')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    args = parser.parse_args()
    cleanup_cloud(dry_run=args.dry_run)
