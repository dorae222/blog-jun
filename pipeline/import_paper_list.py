#!/usr/bin/env python3
"""
papers.csv → Post(paper_review) + ArchitectureEntry 임포트 스크립트

사용법:
  python import_paper_list.py              # 실제 임포트
  python import_paper_list.py --dry-run    # 변경 없이 미리보기
"""
import csv
import os
import sys
import argparse
from pathlib import Path

# Django 설정
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from blog.models import Post, Category, ArchitectureEntry


CSV_PATH = Path(__file__).parent / 'data' / 'papers.csv'

# 카테고리 매핑 (csv category → DB Category slug)
CATEGORY_MAP = {
    'transformer': 'ai',
    'nlp': 'ai',
    'llm': 'ai',
    'alignment': 'ai',
    'moe': 'ai',
    'scaling': 'ai',
    'technique': 'ai',
    'finetuning': 'ai',
    'rag': 'ai',
    'vision': 'ai',
    'multimodal': 'ai',
    'ssm': 'ai',
}


def import_papers(dry_run=False):
    if not CSV_PATH.exists():
        print(f"CSV 파일을 찾을 수 없습니다: {CSV_PATH}")
        sys.exit(1)

    # 기본 작성자
    author = User.objects.first()
    if not author:
        print("User가 없습니다. createsuperuser를 먼저 실행하세요.")
        sys.exit(1)

    # AI 카테고리 가져오기
    categories = {}
    for cat in Category.objects.all():
        categories[cat.slug] = cat

    created_posts = 0
    created_entries = 0
    skipped = 0

    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row['title'].strip()
            slug = slugify(title, allow_unicode=True)[:300]

            # Post 중복 체크
            if Post.objects.filter(slug=slug).exists():
                print(f"  [SKIP] Post 이미 존재: {title}")
                skipped += 1
                continue

            cat_slug = CATEGORY_MAP.get(row['category'], 'ai')
            category = categories.get(cat_slug)

            # 기본 컨텐츠 생성
            content = f"# {row['title']}\n\n"
            content += f"**{row['title_ko']}**\n\n"
            content += f"- **Year**: {row['year']}\n"
            content += f"- **Venue**: {row['venue']}\n"
            content += f"- **Authors**: {row['authors']}\n"
            content += f"- **arXiv**: [{row['arxiv_url']}]({row['arxiv_url']})\n\n"
            content += f"## 요약\n\n{row['summary_ko']}\n\n"
            content += f"## 핵심 기여\n\n{row['key_contribution']}\n\n"
            content += "## 상세 리뷰\n\n> TODO: 상세 리뷰를 작성하세요.\n"

            if dry_run:
                print(f"  [DRY-RUN] Post 생성 예정: {title} (slug={slug})")
            else:
                post = Post.objects.create(
                    title=title,
                    slug=slug,
                    content=content,
                    summary=row['summary_ko'],
                    category=category,
                    author=author,
                    status='draft',
                    post_type='paper_review',
                )
                created_posts += 1
                print(f"  [CREATE] Post: {title}")

                # ArchitectureEntry 생성 (related_architecture가 있는 경우)
                arch_slug = row.get('related_architecture', '').strip()
                if arch_slug and not ArchitectureEntry.objects.filter(slug=arch_slug).exists():
                    if not dry_run:
                        ArchitectureEntry.objects.create(
                            name=title,
                            slug=arch_slug,
                            organization=row['authors'].split(' et al.')[0] if 'et al.' in row['authors'] else row['authors'],
                            paper_url=row['arxiv_url'],
                            description=row['summary_ko'],
                            key_detail=row['key_contribution'],
                            related_post=post,
                        )
                        created_entries += 1
                        print(f"  [CREATE] ArchitectureEntry: {arch_slug}")
                    else:
                        print(f"  [DRY-RUN] ArchitectureEntry 생성 예정: {arch_slug}")

    print(f"\n완료: Post {created_posts}개 생성, ArchitectureEntry {created_entries}개 생성, {skipped}개 스킵")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='papers.csv → Post + ArchitectureEntry 임포트')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    args = parser.parse_args()

    import_papers(dry_run=args.dry_run)
