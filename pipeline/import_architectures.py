#!/usr/bin/env python3
"""
pipeline/data/architectures_written/*/entry.json → ArchitectureEntry import

사용법:
  python pipeline/import_architectures.py              # 실제 임포트
  python pipeline/import_architectures.py --dry-run    # 변경 없이 미리보기
"""
import json
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Django 설정 (Docker 컨테이너: /app, 로컬: backend/)
_backend_dir = Path(__file__).resolve().parent.parent / 'backend'
if _backend_dir.exists():
    sys.path.insert(0, str(_backend_dir))
elif Path('/app/config').exists():
    sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from django.core.files import File
from blog.models import ArchitectureEntry, ArchitectureConcept, ArchitectureRelation, Post, Category, Tag, PostImage


ARCH_WRITTEN_DIR = Path(__file__).parent / 'data' / 'architectures_written'


def upload_post_figure(post, fig_path: Path) -> str | None:
    """figure 파일을 PostImage로 업로드하고 media URL을 반환."""
    if not fig_path.exists():
        return None
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


# architecture_category → Blog Category slug 매핑
ARCH_CATEGORY_MAP = {
    'llm': 'llm',
    'vision': 'vision',
    'multimodal': 'multimodal',
    'ssm': 'ssm',
    'diffusion': 'diffusion',
    'agent': 'agent',
}


def get_or_create_concept(name: str) -> ArchitectureConcept:
    slug = slugify(name, allow_unicode=True)
    concept, _ = ArchitectureConcept.objects.get_or_create(
        slug=slug,
        defaults={
            'name': name,
            'abbreviation': name if len(name) <= 10 else '',
        },
    )
    return concept


def import_architectures(dry_run: bool = False, update: bool = False):
    if not ARCH_WRITTEN_DIR.exists():
        print(f"architectures_written 디렉토리 없음: {ARCH_WRITTEN_DIR}")
        sys.exit(1)

    dirs = sorted(ARCH_WRITTEN_DIR.iterdir())
    created = 0
    updated = 0
    skipped = 0
    post_created = 0
    post_updated = 0

    for arch_dir in dirs:
        if not arch_dir.is_dir():
            continue

        entry_json = arch_dir / 'entry.json'
        if not entry_json.exists():
            print(f"[SKIP] entry.json 없음: {arch_dir.name}")
            continue

        with open(entry_json, encoding='utf-8') as f:
            data = json.load(f)

        name = data.get('name', '').strip()
        slug = data.get('slug') or slugify(name, allow_unicode=True)
        if not name or not slug:
            print(f"[SKIP] name/slug 없음: {arch_dir.name}")
            continue

        if dry_run:
            exists = ArchitectureEntry.objects.filter(slug=slug).exists()
            action = "업데이트 예정" if exists else "생성 예정"
            print(f"  [DRY-RUN] {action}: {name} ({slug})")
            fig_path = arch_dir / data.get('figure', 'figures/architecture.png')
            if fig_path.exists():
                print(f"    figure: {fig_path.name}")
            content_md = arch_dir / 'content.md'
            if content_md.exists():
                post_exists = Post.objects.filter(slug=slug).exists()
                print(f"    content.md: {len(content_md.read_text(encoding='utf-8'))} chars (Post {'exists' if post_exists else 'new'})")
            continue

        # release_date 파싱
        release_date = None
        rd_str = data.get('release_date', '')
        if rd_str:
            try:
                release_date = datetime.strptime(rd_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        # decoder_type 매핑
        valid_decoder_types = {c.value for c in ArchitectureEntry.DecoderType}
        raw_dt = data.get('decoder_type', 'dense')
        decoder_type = raw_dt if raw_dt in valid_decoder_types else 'dense'

        # architecture_category 매핑
        valid_categories = {c.value for c in ArchitectureEntry.ArchitectureCategory}
        raw_cat = data.get('architecture_category', 'llm')
        architecture_category = raw_cat if raw_cat in valid_categories else 'llm'

        # branch_type 매핑
        valid_branches = {c.value for c in ArchitectureEntry.BranchType}
        raw_branch = data.get('branch_type', '')
        branch_type = raw_branch if raw_branch in valid_branches else ''

        # None → '' 변환 (DB NOT NULL 필드 호환) + max_length truncate
        def s(val, default='', max_len=0):
            v = val if val is not None else default
            return str(v)[:max_len] if max_len else str(v)

        defaults = {
            'organization': s(data.get('organization'), max_len=200),
            'release_date': release_date,
            'decoder_type': decoder_type,
            'param_scale': s(data.get('param_scale'), max_len=200),
            'context_length': s(data.get('context_length'), max_len=200),
            'attention_type': s(data.get('attention_type'), max_len=200),
            'normalization': s(data.get('normalization'), max_len=200),
            'activation': s(data.get('activation'), max_len=200),
            'position_encoding': s(data.get('position_encoding'), max_len=200),
            'vocab_size': s(data.get('vocab_size'), max_len=200),
            'hidden_dim': s(data.get('hidden_dim'), max_len=200),
            'num_layers': s(data.get('num_layers'), max_len=200),
            'num_heads': s(data.get('num_heads'), max_len=200),
            'num_experts': s(data.get('num_experts'), max_len=200),
            'active_experts': s(data.get('active_experts'), max_len=200),
            'description': s(data.get('description')),
            'key_detail': s(data.get('key_detail')),
            'training_detail': s(data.get('training_detail')),
            'paper_url': s(data.get('paper_url')),
            'code_url': s(data.get('code_url')),
            'license_type': s(data.get('license_type'), max_len=200),
            'architecture_category': architecture_category,
            'branch_type': branch_type,
            'is_open_source': data.get('is_open_source', True),
        }

        entry, created_flag = ArchitectureEntry.objects.update_or_create(
            slug=slug,
            defaults=defaults,
        )

        if created_flag:
            created += 1
            print(f"  [CREATE] ArchitectureEntry: {name}")
        else:
            updated += 1
            print(f"  [UPDATE] ArchitectureEntry: {name}")

        # concepts M2M 연결
        concepts_raw = data.get('concepts', [])
        if concepts_raw:
            concepts = [get_or_create_concept(c) for c in concepts_raw]
            entry.concepts.set(concepts)

        # figure 업로드
        fig_rel = data.get('figure', '')
        if fig_rel:
            fig_path = arch_dir / fig_rel
        else:
            fig_path = arch_dir / 'figures' / 'architecture.png'

        if fig_path.exists():
            with open(fig_path, 'rb') as f:
                entry.figure.save(fig_path.name, File(f), save=True)
            entry.figure_placeholder = False
            entry.save(update_fields=['figure_placeholder'])
            print(f"    [IMG] {fig_path.name} → {entry.figure.url}")
        else:
            print(f"    [WARN] figure 없음: {fig_path}")

        # content.md → Post 생성/업데이트 + ArchitectureEntry 연결
        content_md = arch_dir / 'content.md'
        content_json = arch_dir / 'content.json'
        if content_md.exists():
            content_text = content_md.read_text(encoding='utf-8')
            # content.json에서 메타데이터 읽기
            content_meta = {}
            if content_json.exists():
                with open(content_json, encoding='utf-8') as f:
                    content_meta = json.load(f)

            post_title = content_meta.get('title_ko') or content_meta.get('title') or name
            post_slug = content_meta.get('slug') or slug
            post_summary = content_meta.get('summary', '')
            post_tags = content_meta.get('tags', [])

            # 카테고리 결정
            cat_slug = ARCH_CATEGORY_MAP.get(data.get('architecture_category', ''), 'llm')
            categories = {c.slug: c for c in Category.objects.all()}
            post_category = categories.get(cat_slug) or categories.get('ai-ml')

            author = User.objects.first()
            existing_post = Post.objects.filter(slug=post_slug).first()

            if existing_post:
                if update:
                    # figure 업로드 + 경로 치환
                    figures_dir = arch_dir / 'figures'
                    figure_url_map = {}
                    if figures_dir.exists():
                        existing_figs = set(
                            pi.image.name.split('/')[-1]
                            for pi in existing_post.images.all()
                            if pi.image
                        )
                        for fig_file in sorted(figures_dir.iterdir()):
                            if fig_file.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}:
                                continue
                            if fig_file.name in existing_figs:
                                pi = existing_post.images.filter(image__endswith=fig_file.name).first()
                                if pi:
                                    figure_url_map[fig_file.name] = pi.image.url
                                continue
                            url = upload_post_figure(existing_post, fig_file)
                            if url:
                                figure_url_map[fig_file.name] = url
                                print(f"      [IMG] {fig_file.name} → {url}")

                    updated_content = replace_figure_paths(content_text, figure_url_map) if figure_url_map else content_text
                    existing_post.content = updated_content
                    existing_post.summary = post_summary
                    existing_post.save(update_fields=['content', 'summary'])
                    existing_post.tags.clear()
                    for tag_name in post_tags:
                        tag_slug_val = slugify(tag_name, allow_unicode=True)[:100]
                        if tag_slug_val:
                            tag, _ = Tag.objects.get_or_create(slug=tag_slug_val, defaults={'name': tag_name})
                            existing_post.tags.add(tag)
                    entry.related_post = existing_post
                    entry.save(update_fields=['related_post'])
                    post_updated += 1
                    print(f"    [POST-UPDATE] {post_title}")
                else:
                    # 연결만
                    if not entry.related_post:
                        entry.related_post = existing_post
                        entry.save(update_fields=['related_post'])
                    print(f"    [POST-SKIP] 이미 존재: {post_slug}")
            elif author:
                from django.utils import timezone as tz
                new_post = Post.objects.create(
                    title=post_title,
                    slug=post_slug,
                    content=content_text,
                    summary=post_summary,
                    category=post_category,
                    author=author,
                    status='published',
                    post_type='paper_review',
                    published_at=tz.now(),
                )
                for tag_name in post_tags:
                    tag_slug_val = slugify(tag_name, allow_unicode=True)[:100]
                    if tag_slug_val:
                        tag, _ = Tag.objects.get_or_create(slug=tag_slug_val, defaults={'name': tag_name})
                        new_post.tags.add(tag)

                # figures 업로드 및 URL 치환
                figures_dir = arch_dir / 'figures'
                figure_url_map = {}
                if figures_dir.exists():
                    for fig_file in sorted(figures_dir.iterdir()):
                        if fig_file.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg'}:
                            continue
                        url = upload_post_figure(new_post, fig_file)
                        if url:
                            figure_url_map[fig_file.name] = url
                            print(f"      [IMG] {fig_file.name} → {url}")

                if figure_url_map:
                    new_post.content = replace_figure_paths(content_text, figure_url_map)
                    new_post.save(update_fields=['content'])

                entry.related_post = new_post
                entry.save(update_fields=['related_post'])
                post_created += 1
                print(f"    [POST-CREATE] {post_title}")
        else:
            # content.md 없는 경우 기존 related_post_slug 연결 시도
            related_slug = data.get('related_post_slug', '')
            if related_slug:
                try:
                    post = Post.objects.get(slug=related_slug)
                    entry.related_post = post
                    entry.save(update_fields=['related_post'])
                    print(f"    [LINK] Post 연결: {related_slug}")
                except Post.DoesNotExist:
                    print(f"    [WARN] Post 없음: {related_slug}")

    # 2차 패스: relations 처리 (모든 entry가 생성된 후)
    if not dry_run:
        rel_created = 0
        for arch_dir in dirs:
            if not arch_dir.is_dir():
                continue
            entry_json = arch_dir / 'entry.json'
            if not entry_json.exists():
                continue
            with open(entry_json, encoding='utf-8') as f:
                data = json.load(f)
            slug = data.get('slug') or slugify(data.get('name', ''), allow_unicode=True)
            relations = data.get('relations', [])
            if not relations:
                continue
            try:
                from_entry = ArchitectureEntry.objects.get(slug=slug)
            except ArchitectureEntry.DoesNotExist:
                continue
            for rel in relations:
                to_slug = rel.get('to', '')
                rel_type = rel.get('type', 'evolved_from')
                try:
                    to_entry = ArchitectureEntry.objects.get(slug=to_slug)
                except ArchitectureEntry.DoesNotExist:
                    print(f"    [WARN] relation target 없음: {to_slug}")
                    continue
                obj, was_created = ArchitectureRelation.objects.get_or_create(
                    from_entry=from_entry,
                    to_entry=to_entry,
                    relation_type=rel_type,
                    defaults={'description': rel.get('description', '')}
                )
                if was_created:
                    rel_created += 1
                elif rel.get('description') and not obj.description:
                    obj.description = rel['description']
                    obj.save(update_fields=['description'])
        print(f"  Relations: {rel_created}개 생성")

    if not dry_run:
        print(f"\n완료: ArchitectureEntry {created}개 생성, {updated}개 업데이트, {skipped}개 스킵")
        print(f"  Post {post_created}개 생성, {post_updated}개 업데이트")
    else:
        print(f"\n[DRY-RUN 완료] 실제 변경 없음.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='architectures_written → ArchitectureEntry import')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    parser.add_argument('--update', action='store_true', help='기존 Post content + tags 업데이트')
    args = parser.parse_args()
    import_architectures(dry_run=args.dry_run, update=args.update)
