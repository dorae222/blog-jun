#!/usr/bin/env python3
"""
Architecture ↔ Paper 연결 감사 및 자동 매핑 스크립트.

기능:
1. 현재 연결 상태 분석 (entry.json / content.json)
2. 슬러그 겹침으로 자동 매핑 가능한 항목 식별
3. --fix 옵션으로 데이터 파일 자동 업데이트

사용법:
  python audit_connections.py              # 감사만 (dry-run)
  python audit_connections.py --fix        # 자동 매핑 적용
  python audit_connections.py --verbose    # 상세 출력
"""

import json
import os
import sys
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent / 'data'
ARCH_DIR = BASE_DIR / 'architectures_written'
PAPER_DIR = BASE_DIR / 'papers_written'


def load_architectures():
    """모든 architecture entry.json 로드."""
    entries = {}
    for d in sorted(ARCH_DIR.iterdir()):
        entry_file = d / 'entry.json'
        if not d.is_dir() or not entry_file.exists():
            continue
        with open(entry_file) as f:
            data = json.load(f)
        slug = data.get('slug', d.name)
        entries[slug] = {
            'dir': d,
            'slug': slug,
            'name': data.get('name', slug),
            'related_post_slug': (data.get('related_post_slug') or '').strip(),
            'has_content_md': (d / 'content.md').exists(),
            'data': data,
        }
    return entries


def load_papers():
    """모든 paper content.json 로드."""
    entries = {}
    for d in sorted(PAPER_DIR.iterdir()):
        content_file = d / 'content.json'
        if not d.is_dir() or not content_file.exists():
            continue
        with open(content_file) as f:
            data = json.load(f)
        slug = data.get('slug', '')
        if not slug:
            continue
        entries[slug] = {
            'dir': d,
            'dir_name': d.name,
            'slug': slug,
            'title': data.get('title', slug),
            'related_architecture': (data.get('related_architecture') or '').strip(),
            'has_content_md': (d / 'content.md').exists(),
            'data': data,
        }
    return entries


def analyze(archs, papers, verbose=False):
    """연결 상태 분석."""
    arch_slugs = set(archs.keys())
    paper_slugs = set(papers.keys())
    overlap = arch_slugs & paper_slugs

    # Architecture → Post 연결 상태
    arch_linked = {s: a for s, a in archs.items() if a['related_post_slug']}
    arch_unlinked = {s: a for s, a in archs.items() if not a['related_post_slug']}

    # Paper → Architecture 연결 상태
    paper_linked = {s: p for s, p in papers.items() if p['related_architecture']}
    paper_unlinked = {s: p for s, p in papers.items() if not p['related_architecture']}

    # 자동 매핑 가능: 슬러그 겹치는데 양쪽 모두 비어있는 경우
    auto_mappable = []
    for slug in sorted(overlap):
        arch = archs[slug]
        paper = papers[slug]
        arch_empty = not arch['related_post_slug']
        paper_empty = not paper['related_architecture']
        if arch_empty or paper_empty:
            auto_mappable.append({
                'slug': slug,
                'arch_empty': arch_empty,
                'paper_empty': paper_empty,
                'arch_name': arch['name'],
                'paper_title': paper['title'],
            })

    # 이미 연결된 겹침
    already_linked = []
    for slug in sorted(overlap):
        arch = archs[slug]
        paper = papers[slug]
        if arch['related_post_slug'] and paper['related_architecture']:
            already_linked.append(slug)

    # Paper-only (매칭 architecture 없음)
    paper_only = sorted(paper_slugs - arch_slugs)
    # Architecture-only (매칭 paper 없음)
    arch_only = sorted(arch_slugs - paper_slugs)

    return {
        'total_archs': len(archs),
        'total_papers': len(papers),
        'arch_linked': len(arch_linked),
        'arch_unlinked': len(arch_unlinked),
        'paper_linked': len(paper_linked),
        'paper_unlinked': len(paper_unlinked),
        'overlap_count': len(overlap),
        'already_linked': already_linked,
        'auto_mappable': auto_mappable,
        'paper_only': paper_only,
        'arch_only': arch_only,
        'arch_unlinked_slugs': sorted(arch_unlinked.keys()),
        'paper_unlinked_slugs': sorted(paper_unlinked.keys()),
    }


def print_report(stats, verbose=False):
    """감사 리포트 출력."""
    print('=' * 60)
    print('Architecture ↔ Paper 연결 감사 리포트')
    print('=' * 60)

    print(f'\n## 전체 현황')
    print(f'  Architecture 총: {stats["total_archs"]}')
    print(f'  Paper 총:        {stats["total_papers"]}')
    print(f'  슬러그 겹침:      {stats["overlap_count"]}')

    print(f'\n## Architecture → Post 연결')
    print(f'  연결됨:  {stats["arch_linked"]} ({stats["arch_linked"]*100//stats["total_archs"]}%)')
    print(f'  미연결:  {stats["arch_unlinked"]} ({stats["arch_unlinked"]*100//stats["total_archs"]}%)')

    print(f'\n## Paper → Architecture 연결')
    print(f'  연결됨:  {stats["paper_linked"]} ({stats["paper_linked"]*100//stats["total_papers"]}%)')
    print(f'  미연결:  {stats["paper_unlinked"]} ({stats["paper_unlinked"]*100//stats["total_papers"]}%)')

    print(f'\n## 자동 매핑 가능 (슬러그 겹침, 한쪽+ 비어있음)')
    print(f'  총: {len(stats["auto_mappable"])}개')
    for m in stats['auto_mappable']:
        flags = []
        if m['arch_empty']:
            flags.append('arch→post 비어있음')
        if m['paper_empty']:
            flags.append('paper→arch 비어있음')
        print(f'  - {m["slug"]:30s} [{", ".join(flags)}]')

    if verbose:
        print(f'\n## Paper-only (매칭 architecture 없음): {len(stats["paper_only"])}개')
        for s in stats['paper_only']:
            print(f'  - {s}')

        print(f'\n## Architecture-only (매칭 paper 없음): {len(stats["arch_only"])}개')
        for s in stats['arch_only']:
            print(f'  - {s}')

    print(f'\n## 이미 양방향 연결: {len(stats["already_linked"])}개')


def apply_fixes(archs, papers, stats, verbose=False):
    """자동 매핑 적용 (entry.json + content.json 업데이트)."""
    fixed_arch = 0
    fixed_paper = 0

    for m in stats['auto_mappable']:
        slug = m['slug']

        # Architecture entry.json 업데이트
        if m['arch_empty'] and slug in archs:
            arch = archs[slug]
            arch['data']['related_post_slug'] = slug
            entry_file = arch['dir'] / 'entry.json'
            with open(entry_file, 'w') as f:
                json.dump(arch['data'], f, indent=2, ensure_ascii=False)
            fixed_arch += 1
            if verbose:
                print(f'  [FIX] arch entry.json: {slug} → related_post_slug="{slug}"')

        # Paper content.json 업데이트
        if m['paper_empty'] and slug in papers:
            paper = papers[slug]
            paper['data']['related_architecture'] = slug
            content_file = paper['dir'] / 'content.json'
            with open(content_file, 'w') as f:
                json.dump(paper['data'], f, indent=2, ensure_ascii=False)
            fixed_paper += 1
            if verbose:
                print(f'  [FIX] paper content.json: {slug} → related_architecture="{slug}"')

    print(f'\n## 자동 매핑 적용 완료')
    print(f'  Architecture entry.json 업데이트: {fixed_arch}개')
    print(f'  Paper content.json 업데이트: {fixed_paper}개')
    return fixed_arch, fixed_paper


def main():
    parser = argparse.ArgumentParser(description='Architecture ↔ Paper 연결 감사')
    parser.add_argument('--fix', action='store_true', help='자동 매핑 적용')
    parser.add_argument('--verbose', '-v', action='store_true', help='상세 출력')
    args = parser.parse_args()

    archs = load_architectures()
    papers = load_papers()
    stats = analyze(archs, papers, verbose=args.verbose)
    print_report(stats, verbose=args.verbose)

    if args.fix:
        apply_fixes(archs, papers, stats, verbose=args.verbose)
    else:
        if stats['auto_mappable']:
            print(f'\n💡 --fix 옵션으로 {len(stats["auto_mappable"])}개 자동 매핑 적용 가능')


if __name__ == '__main__':
    main()
