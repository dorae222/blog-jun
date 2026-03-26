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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.files import File
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify as django_slugify
from blog.models import Post, Category, PostImage, ArchitectureEntry, Tag


PAPERS_WRITTEN_DIR = Path(__file__).parent / 'data' / 'papers_written'

# 통합 카테고리 매퍼 사용
sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.category_mapper import CategoryMapper
_mapper = CategoryMapper()


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


def import_papers(dry_run: bool = False, update: bool = False):
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
    created_images = 0
    updated_posts = 0
    skipped = 0

    for paper_dir in dirs:
        if not paper_dir.is_dir():
            continue

        content_json = paper_dir / 'content.json'
        if not content_json.exists():
            print(f"[SKIP] content.json 없음: {paper_dir.name}")
            continue

        with open(content_json, encoding='utf-8') as f:
            data = json.load(f)

        title = data.get('title', '').strip()
        if not title:
            print(f"[SKIP] title 없음: {paper_dir.name}")
            continue

        slug = data.get('slug') or slugify(title, allow_unicode=True)[:300]

        # content.md 우선, 없으면 content.json의 content 필드 폴백
        content_md = paper_dir / 'content.md'
        content = content_md.read_text(encoding='utf-8') if content_md.exists() else data.get('content', '')
        summary = data.get('summary', '')
        tags_raw = data.get('tags', [])

        existing = Post.objects.filter(slug=slug).first()
        if existing and not update:
            print(f"  [SKIP] Post 이미 존재: {title}")
            skipped += 1
            continue
        if existing and update:
            if not dry_run:
                # figure 업로드 + 경로 치환 (update 시에도 필요)
                figures_dir = paper_dir / 'figures'
                figure_url_map = {}
                if figures_dir.exists():
                    # 이미 업로드된 figure 파일명 세트
                    existing_figs = set(
                        pi.image.name.split('/')[-1]
                        for pi in existing.images.all()
                        if pi.image
                    )
                    for fig_file in sorted(figures_dir.iterdir()):
                        if fig_file.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}:
                            continue
                        if fig_file.name in existing_figs:
                            # 이미 업로드된 figure → 기존 URL 사용
                            pi = existing.images.filter(image__endswith=fig_file.name).first()
                            if pi:
                                figure_url_map[fig_file.name] = pi.image.url
                            continue
                        url = upload_figure(existing, fig_file, dry_run=False)
                        if url:
                            figure_url_map[fig_file.name] = url
                            created_images += 1
                            print(f"    [IMG] {fig_file.name} → {url}")

                # content 내 figures/ 경로 → media URL 치환
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
                for tag_name in tags_raw:
                    tag_slug = slugify(tag_name, allow_unicode=True)[:100]
                    if not tag_slug:
                        continue
                    tag, _ = Tag.objects.get_or_create(slug=tag_slug, defaults={'name': tag_name})
                    existing.tags.add(tag)
                print(f"  [UPDATE] content + tags 업데이트: {title}")
            else:
                print(f"  [DRY-RUN] 업데이트 예정: {title}")
            updated_posts += 1
            continue

        # 카테고리 결정 (통합 매퍼 사용)
        cat_key = data.get('category_slug') or data.get('sub_category') or data.get('category', '')
        cat_slug = _mapper.resolve(cat_key, 'paper_review')
        category = categories.get(cat_slug) or categories.get('ai-ml')

        if dry_run:
            print(f"  [DRY-RUN] Post 생성 예정: {title} → {cat_slug}")
            figures_dir = paper_dir / 'figures'
            if figures_dir.exists():
                figs = list(figures_dir.iterdir())
                print(f"    figures: {len(figs)}개")
            continue

        post = Post.objects.create(
            title=title,
            slug=slug,
            content=content,
            summary=summary,
            category=category,
            author=author,
            status='published',
            post_type=data.get('post_type', 'paper_review'),
            published_at=timezone.now(),
            is_pinned=data.get('is_pinned', False),
            arxiv_url=data.get('arxiv_url', ''),
            paper_year=data.get('year') if data.get('year') else None,
            paper_authors=data.get('authors', ''),
            venue=data.get('venue', ''),
        )
        created_posts += 1
        print(f"  [CREATE] Post: {title}")

        # 태그 연결
        for tag_name in tags_raw:
            tag_slug = slugify(tag_name, allow_unicode=True)[:100]
            if not tag_slug:
                continue
            tag, _ = Tag.objects.get_or_create(slug=tag_slug, defaults={'name': tag_name})
            post.tags.add(tag)

        # figures 업로드 및 URL 치환
        figures_dir = paper_dir / 'figures'
        figure_url_map = {}
        if figures_dir.exists():
            for fig_file in sorted(figures_dir.iterdir()):
                if fig_file.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}:
                    continue
                url = upload_figure(post, fig_file, dry_run=False)
                if url:
                    figure_url_map[fig_file.name] = url
                    created_images += 1
                    print(f"    [IMG] {fig_file.name} → {url}")

        # 마크다운 내 figure 경로 치환 후 저장
        if figure_url_map:
            post.content = replace_figure_paths(content, figure_url_map)
            post.save(update_fields=['content'])

        # related_architecture 연결
        arch_slug = data.get('related_architecture', '').strip()
        if arch_slug:
            try:
                arch = ArchitectureEntry.objects.get(slug=arch_slug)
                arch.related_post = post
                arch.save(update_fields=['related_post'])
                print(f"    [LINK] ArchitectureEntry 연결: {arch_slug}")
            except ArchitectureEntry.DoesNotExist:
                print(f"    [WARN] ArchitectureEntry 없음: {arch_slug}")

    if not dry_run:
        print(f"\n완료: Post {created_posts}개 생성, {updated_posts}개 업데이트, PostImage {created_images}개 업로드, {skipped}개 스킵")
    else:
        print(f"\n[DRY-RUN 완료] 실제 변경 없음.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='papers_written → Post + PostImage import')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    parser.add_argument('--update', action='store_true', help='기존 포스트 content + tags 업데이트')
    args = parser.parse_args()
    import_papers(dry_run=args.dry_run, update=args.update)
