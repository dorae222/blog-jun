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

# Django 설정
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from django.utils.text import slugify
from django.core.files import File
from blog.models import ArchitectureEntry, ArchitectureConcept, ArchitectureRelation, Post


ARCH_WRITTEN_DIR = Path(__file__).parent / 'data' / 'architectures_written'


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


def import_architectures(dry_run: bool = False):
    if not ARCH_WRITTEN_DIR.exists():
        print(f"architectures_written 디렉토리 없음: {ARCH_WRITTEN_DIR}")
        sys.exit(1)

    dirs = sorted(ARCH_WRITTEN_DIR.iterdir())
    created = 0
    updated = 0
    skipped = 0

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

        defaults = {
            'organization': data.get('organization', ''),
            'release_date': release_date,
            'decoder_type': decoder_type,
            'param_scale': data.get('param_scale', ''),
            'context_length': data.get('context_length', ''),
            'attention_type': data.get('attention_type', ''),
            'normalization': data.get('normalization', ''),
            'activation': data.get('activation', ''),
            'position_encoding': data.get('position_encoding', ''),
            'vocab_size': data.get('vocab_size', ''),
            'hidden_dim': data.get('hidden_dim', ''),
            'num_layers': data.get('num_layers', ''),
            'num_heads': data.get('num_heads', ''),
            'num_experts': data.get('num_experts', ''),
            'active_experts': data.get('active_experts', ''),
            'description': data.get('description', ''),
            'key_detail': data.get('key_detail', ''),
            'training_detail': data.get('training_detail', ''),
            'paper_url': data.get('paper_url', ''),
            'code_url': data.get('code_url', ''),
            'license_type': data.get('license_type', ''),
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

        # related_post 연결 (slug 기준)
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
                _, was_created = ArchitectureRelation.objects.get_or_create(
                    from_entry=from_entry,
                    to_entry=to_entry,
                    relation_type=rel_type,
                    defaults={'description': rel.get('description', '')}
                )
                if was_created:
                    rel_created += 1
        print(f"  Relations: {rel_created}개 생성")

    if not dry_run:
        print(f"\n완료: ArchitectureEntry {created}개 생성, {updated}개 업데이트, {skipped}개 스킵")
    else:
        print(f"\n[DRY-RUN 완료] 실제 변경 없음.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='architectures_written → ArchitectureEntry import')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    args = parser.parse_args()
    import_architectures(dry_run=args.dry_run)
