#!/usr/bin/env python3
"""
pipeline/data/papers_written/*/content.json → Post(paper_review) + PostImage import

사용법:
  python pipeline/import_papers_written.py              # 실제 임포트
  python pipeline/import_papers_written.py --dry-run    # 변경 없이 미리보기
"""
import json
import os
import re
import sys
import argparse
import shutil
from pathlib import Path

# Django 설정
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.files import File
from django.conf import settings
from django.utils import timezone
from blog.models import Post, Category, PostImage, ArchitectureEntry


PAPERS_WRITTEN_DIR = Path(__file__).resolve().parent.parent / 'data' / 'papers_written'

# papers.csv category / sub_category → DB slug (7개 서브카테고리)
CATEGORY_SLUG_MAP = {
    'transformer':        'llm',
    'nlp':                'llm',
    'llm':                'llm',
    'llm-architecture':   'llm',
    'pretraining':        'llm',
    'vision':             'vision',
    'multimodal':         'multimodal',
    'ssm':                'ssm',
    'diffusion':          'diffusion',
    'moe':                'technique',
    'scaling':            'technique',
    'efficiency':         'technique',
    'efficient-training': 'technique',
    'alignment':          'technique',
    'finetuning':         'technique',
    'rag':                'technique',
    'retrieval':          'technique',
    'technique':          'technique',
    'attention-mechanism':'technique',
    'prompting':          'technique',
    'icl':                'technique',
    'few-shot-learning':  'technique',
    'benchmark':          'technique',
    'evaluation':         'technique',
    'agents':             'agent',
    'tools':              'agent',
    'data':               'technique',
    'security':           'technique',
}


def upload_figure(post, fig_path: Path, dry_run: bool) -> str | None:
    """figure 파일을 PostImage로 업로드하고 media URL을 반환."""
    if not fig_path.exists():
        print(f"    [WARN] figure 파일 없음: {fig_path}")
        return None
    if dry_run:
        print(f"    [DRY-RUN] figure 업로드 예정: {fig_path.name}")
        return f"/media/posts/dry-run/{fig_path.name}"
    with open(fig_path, 'rb') as f:
        img = PostImage.objects.create(
            post=post,
            alt_text=fig_path.stem,
            original_path=str(fig_path),
        )
        img.image.save(fig_path.name, File(f), save=True)
    return img.image.url


def replace_figure_paths(content: str, figure_url_map: dict) -> str:
    """마크다운 내 figures/ 상대 경로 → 서버 media URL 치환."""
    for local_path, media_url in figure_url_map.items():
        content = content.replace(f"figures/{local_path}", media_url)
        content = content.replace(f"./figures/{local_path}", media_url)
    return content


def import_papers(dry_run: bool = False, force_images: bool = False):
    if not PAPERS_WRITTEN_DIR.exists():
        print(f"papers_written 디렉토리 없음: {PAPERS_WRITTEN_DIR}")
        sys.exit(1)

    author = User.objects.first()
    if not author:
        print("User가 없습니다. createsuperuser를 먼저 실행하세요.")
        sys.exit(1)

    categories = {cat.slug: cat for cat in Category.objects.all()}

    dirs = sorted(PAPERS_WRITTEN_DIR.iterdir())
    created_posts = 0
    updated_posts = 0
    created_images = 0
    skipped = 0

    for paper_dir in dirs:
        if not paper_dir.is_dir():
            continue

        content_json = paper_dir / 'content.json'
        if not content_json.exists():
            continue

        with open(content_json, encoding='utf-8') as f:
            data = json.load(f)

        title = data.get('title', '').strip()
        if not title:
            continue

        slug = data.get('slug') or slugify(title, allow_unicode=True)[:300]

        # 카테고리 결정
        cat_key = data.get('sub_category') or data.get('category', '')
        cat_slug = CATEGORY_SLUG_MAP.get(cat_key, 'llm')
        category = categories.get(cat_slug) or categories.get('ai-ml')

        content = data.get('content', '')
        summary = data.get('summary', '')

        existing = Post.objects.filter(slug=slug).first()

        if existing:
            if dry_run:
                old_len = len(existing.content or '')
                new_len = len(content)
                print(f"  [DRY-RUN UPDATE] {slug}: {old_len} → {new_len} chars")
            else:
                # --force-images: 기존 PostImage 삭제 후 재업로드
                if force_images:
                    deleted_count = PostImage.objects.filter(post=existing).delete()[0]
                    if deleted_count:
                        print(f"    [FORCE] 기존 이미지 {deleted_count}개 삭제")

                # figures 업로드 및 URL 치환
                figures_dir = paper_dir / 'figures'
                figure_url_map = {}
                if figures_dir.exists():
                    for fig_file in sorted(figures_dir.iterdir()):
                        if fig_file.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
                            continue
                        # 이미 업로드된 figure 스킵 (force_images 시 이미 삭제됨)
                        if PostImage.objects.filter(post=existing, alt_text=fig_file.stem).exists():
                            continue
                        url = upload_figure(existing, fig_file, dry_run=False)
                        if url:
                            figure_url_map[fig_file.name] = url
                            created_images += 1

                # content 보존: 이미지 없으면 기존 content 유지 (상대경로 덮어쓰기 방지)
                updated_content = replace_figure_paths(content, figure_url_map) if figure_url_map else existing.content
                existing.content = updated_content
                existing.summary = summary
                existing.category = category
                existing.save(update_fields=['content', 'summary', 'category'])
                fig_count = PostImage.objects.filter(post=existing).count()
                print(f"  [UPDATE] {slug} ({fig_count} figs)")
            updated_posts += 1
        else:
            if dry_run:
                print(f"  [DRY-RUN CREATE] {slug} → {cat_slug}")
                continue

            post = Post.objects.create(
                title=title,
                slug=slug,
                content=content,
                summary=summary,
                category=category,
                author=author,
                status='published',
                post_type='paper_review',
                published_at=timezone.now(),
            )
            created_posts += 1

            # figures 업로드 및 URL 치환
            figures_dir = paper_dir / 'figures'
            figure_url_map = {}
            if figures_dir.exists():
                for fig_file in sorted(figures_dir.iterdir()):
                    if fig_file.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
                        continue
                    url = upload_figure(post, fig_file, dry_run=False)
                    if url:
                        figure_url_map[fig_file.name] = url
                        created_images += 1

            if figure_url_map:
                post.content = replace_figure_paths(content, figure_url_map)
                post.save(update_fields=['content'])

            print(f"  [CREATE] {slug} ({len(figure_url_map)} figs)")

    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"\n{prefix}완료: 생성 {created_posts}개, 업데이트 {updated_posts}개, 이미지 {created_images}개, 스킵 {skipped}개")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='papers_written → Post + PostImage import')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    parser.add_argument('--force-images', action='store_true', help='기존 PostImage 삭제 후 재업로드')
    args = parser.parse_args()
    import_papers(dry_run=args.dry_run, force_images=args.force_images)
