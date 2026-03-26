#!/usr/bin/env python3
"""
content.json 전체 보강 스크립트: 위키링크 추가 + 태그 정리.

1. 관계 그래프 빌드 (entry.json relations + papers.csv related_architecture)
2. 위키링크 삽입 (content.json content 끝에 ## 관련 문서 섹션)
3. 카테고리 중복 태그 제거

사용법:
    python pipeline/enrich_content.py              # 실제 적용
    python pipeline/enrich_content.py --dry-run    # 미리보기
"""
import csv
import json
import re
import argparse
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ARCH_DIR = BASE_DIR / "data" / "architectures_written"
PAPERS_DIR = BASE_DIR / "data" / "papers_written"
CSV_PATH = BASE_DIR / "data" / "papers.csv"

# 카테고리와 중복되는 태그 (제거 대상)
CATEGORY_TAGS = {
    'LLM', 'llm', 'Transformer', 'transformer',
    'SSM', 'ssm', 'State Space Model',
    'Diffusion', 'diffusion', 'Diffusion Model',
    'Vision', 'vision', 'Computer Vision',
    'Multimodal', 'multimodal',
    'Agent', 'agent', 'Agents',
    'AI', 'ai', 'AI/ML', 'ML', 'ml',
    'Deep Learning', 'deep learning',
    'Machine Learning', 'machine learning',
    'NLP', 'nlp',
}


def load_arch_names() -> dict[str, str]:
    """slug → display name 매핑 로드."""
    names = {}
    for entry_dir in ARCH_DIR.iterdir():
        if not entry_dir.is_dir():
            continue
        entry_json = entry_dir / "entry.json"
        if entry_json.exists():
            with open(entry_json, encoding="utf-8") as f:
                data = json.load(f)
                names[data["slug"]] = data["name"]
        # content.json에서도 이름 가져올 수 있음
        content_json = entry_dir / "content.json"
        if content_json.exists():
            with open(content_json, encoding="utf-8") as f:
                data = json.load(f)
                if data.get("slug") and data.get("title"):
                    names[data["slug"]] = data["title"]
    # papers_written에서도 slug → title 매핑
    for paper_dir in PAPERS_DIR.iterdir():
        if not paper_dir.is_dir():
            continue
        content_json = paper_dir / "content.json"
        if content_json.exists():
            with open(content_json, encoding="utf-8") as f:
                data = json.load(f)
                slug = data.get("slug", "")
                title = data.get("title", "")
                if slug and title:
                    names[slug] = title
    return names


def build_relation_graph() -> dict[str, list[tuple[str, str]]]:
    """
    관계 그래프 빌드. slug → [(target_slug, relation_type), ...]
    양방향 추가 (A→B면 B→A도).
    """
    graph: dict[str, list[tuple[str, str]]] = defaultdict(list)

    # 1. entry.json relations (196개)
    for entry_dir in ARCH_DIR.iterdir():
        if not entry_dir.is_dir():
            continue
        entry_json = entry_dir / "entry.json"
        if not entry_json.exists():
            continue
        with open(entry_json, encoding="utf-8") as f:
            data = json.load(f)
        slug = data["slug"]
        for rel in data.get("relations", []):
            target = rel["to"]
            rel_type = rel["type"]
            graph[slug].append((target, rel_type))
            # 역방향 추가
            reverse_type = _reverse_relation(rel_type)
            graph[target].append((slug, reverse_type))

    # 2. papers.csv related_architecture (paper slug ↔ architecture slug)
    if CSV_PATH.exists():
        with open(CSV_PATH, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                arch_slug = row.get("related_architecture", "").strip()
                if not arch_slug:
                    continue
                # paper의 slug는 papers_written에서 찾아야 함
                # papers.csv의 title로 slug를 유추하기 어려우므로
                # related_architecture만 연결
                # → 이미 entry.json relations에 포함됨

    # 중복 제거
    for slug in graph:
        graph[slug] = list(set(graph[slug]))

    return graph


def _reverse_relation(rel_type: str) -> str:
    """관계 역방향 변환."""
    reverse = {
        'evolved_from': 'evolved_into',
        'evolved_into': 'evolved_from',
        'inspired_by': 'inspired',
        'inspired': 'inspired_by',
        'technique_used': 'used_by',
        'used_by': 'technique_used',
        'variant_of': 'has_variant',
        'has_variant': 'variant_of',
    }
    return reverse.get(rel_type, rel_type)


def _relation_label(rel_type: str) -> str:
    """관계 타입 → 한글 레이블."""
    labels = {
        'evolved_from': '발전 기반',
        'evolved_into': '후속 모델',
        'inspired_by': '영감',
        'inspired': '영감을 줌',
        'technique_used': '사용 기법',
        'used_by': '적용 모델',
        'variant_of': '변형 원본',
        'has_variant': '변형 모델',
    }
    return labels.get(rel_type, rel_type)


def build_wikilink_section(slug: str, graph: dict, names: dict) -> str:
    """위키링크 ## 관련 문서 섹션 생성."""
    relations = graph.get(slug, [])
    if not relations:
        return ""

    # 관계 타입별 그룹화
    by_type: dict[str, list[str]] = defaultdict(list)
    for target, rel_type in relations:
        by_type[rel_type].append(target)

    lines = ["## 관련 문서\n"]

    # 정렬된 관계 타입 순서
    type_order = ['evolved_from', 'evolved_into', 'inspired_by', 'inspired',
                  'variant_of', 'has_variant', 'technique_used', 'used_by']

    for rel_type in type_order:
        targets = by_type.get(rel_type, [])
        if not targets:
            continue
        for target in sorted(targets):
            display = names.get(target, target)
            label = _relation_label(rel_type)
            lines.append(f"- [[{target}|{display}]] — {label}")

    return "\n".join(lines) + "\n"


def remove_related_section(content: str) -> str:
    """기존 ## 관련 문서 섹션 제거."""
    # ## 관련 문서부터 다음 ##까지 또는 끝까지
    pattern = r'\n*## 관련 문서\n[\s\S]*?(?=\n## |\Z)'
    return re.sub(pattern, '', content).rstrip()


def clean_tags(tags: list[str]) -> list[str]:
    """카테고리 중복 태그 제거."""
    return [t for t in tags if t not in CATEGORY_TAGS]


def process_content_json(path: Path, slug: str, graph: dict, names: dict,
                         dry_run: bool) -> dict[str, int]:
    """단일 content.json 처리: 위키링크 추가 + 태그 정리."""
    stats = {"wikilink_added": 0, "tags_removed": 0, "modified": 0}

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    modified = False

    # 위키링크 추가
    wikilink_section = build_wikilink_section(slug, graph, names)
    if wikilink_section:
        content = data.get("content", "")
        content = remove_related_section(content)
        content = content.rstrip() + "\n\n" + wikilink_section
        if content != data.get("content", ""):
            data["content"] = content
            modified = True
            stats["wikilink_added"] = 1

    # 태그 정리
    tags = data.get("tags", [])
    cleaned = clean_tags(tags)
    removed_count = len(tags) - len(cleaned)
    if removed_count > 0:
        data["tags"] = cleaned
        modified = True
        stats["tags_removed"] = removed_count

    if modified:
        stats["modified"] = 1
        if not dry_run:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    return stats


def main():
    parser = argparse.ArgumentParser(description='content.json 위키링크 + 태그 보강')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    args = parser.parse_args()

    prefix = "[DRY-RUN] " if args.dry_run else ""
    print(f"\n{prefix}enrich_content.py 시작")
    print("=" * 60)

    # 1. 관계 그래프 빌드
    print("관계 그래프 빌드 중...")
    graph = build_relation_graph()
    names = load_arch_names()
    total_relations = sum(len(v) for v in graph.values())
    print(f"  노드: {len(graph)}개, 관계: {total_relations}개 (양방향)")

    # 2. architectures_written content.json 처리
    total = {"wikilink_added": 0, "tags_removed": 0, "modified": 0}
    arch_count = 0

    for entry_dir in sorted(ARCH_DIR.iterdir()):
        if not entry_dir.is_dir():
            continue
        content_path = entry_dir / "content.json"
        if not content_path.exists():
            continue

        slug = entry_dir.name
        stats = process_content_json(content_path, slug, graph, names, args.dry_run)
        arch_count += 1

        for k, v in stats.items():
            total[k] += v

        if stats["modified"]:
            rels = len(graph.get(slug, []))
            print(f"  {prefix}[ARCH] {slug}: 위키링크 {rels}개, 태그 -{stats['tags_removed']}")

    # 3. papers_written content.json 처리
    paper_count = 0
    for paper_dir in sorted(PAPERS_DIR.iterdir()):
        if not paper_dir.is_dir():
            continue
        content_path = paper_dir / "content.json"
        if not content_path.exists():
            continue

        # slug 추출 (content.json에서)
        with open(content_path, encoding="utf-8") as f:
            data = json.load(f)
        slug = data.get("slug", "")
        if not slug:
            continue

        # related_architecture로 연결 확인
        arch_slug = data.get("related_architecture", "")
        if arch_slug and arch_slug in graph:
            # paper slug가 graph에 없으면 architecture의 관계를 paper에도 연결
            if slug not in graph and slug != arch_slug:
                graph[slug] = graph.get(arch_slug, [])[:]

        stats = process_content_json(content_path, slug, graph, names, args.dry_run)
        paper_count += 1

        for k, v in stats.items():
            total[k] += v

        if stats["modified"]:
            rels = len(graph.get(slug, []))
            print(f"  {prefix}[PAPER] {slug}: 위키링크 {rels}개, 태그 -{stats['tags_removed']}")

    print("=" * 60)
    print(f"{prefix}완료:")
    print(f"  처리: architectures {arch_count}개, papers {paper_count}개")
    print(f"  위키링크 추가: {total['wikilink_added']}개")
    print(f"  태그 제거: {total['tags_removed']}개")
    print(f"  수정된 파일: {total['modified']}개")


if __name__ == "__main__":
    main()
