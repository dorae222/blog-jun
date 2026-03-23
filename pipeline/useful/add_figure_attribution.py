#!/usr/bin/env python3
"""
papers_written / architectures_written 컨텐츠에 figure 출처 표기를 추가합니다.

papers_written: content.json의 figure 아래 arXiv 출처 추가
architectures_written: entry.json의 paper_url 활용

사용법:
    python pipeline/useful/add_figure_attribution.py --papers
    python pipeline/useful/add_figure_attribution.py --architectures
    python pipeline/useful/add_figure_attribution.py --all --dry-run
"""
import argparse
import json
import re
import sys
from pathlib import Path

PAPERS_DIR = Path("pipeline/data/papers_written")
ARCH_DIR = Path("pipeline/data/architectures_written")


def add_paper_attribution(dry_run: bool = False) -> dict:
    """papers_written의 figure 아래에 출처 표기 추가."""
    if not PAPERS_DIR.exists():
        print(f"papers_written 디렉토리 없음: {PAPERS_DIR}")
        return {"status": "error"}

    updated = 0
    skipped = 0

    for paper_dir in sorted(PAPERS_DIR.iterdir()):
        if not paper_dir.is_dir():
            continue
        content_json = paper_dir / "content.json"
        if not content_json.exists():
            continue

        with open(content_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        content = data.get("content", "")
        title = data.get("title", "")
        arxiv_url = data.get("arxiv_url", "")
        authors = data.get("authors", "")
        venue = data.get("venue", "")
        year = data.get("year", "")

        if not arxiv_url:
            skipped += 1
            continue

        # 이미 출처 표기가 있으면 스킵
        if "*출처:" in content:
            skipped += 1
            continue

        # figure 이미지 패턴 찾기: ![...](...)
        fig_pattern = re.compile(r'(!\[.*?\]\([^)]+\))')
        matches = list(fig_pattern.finditer(content))

        if not matches:
            skipped += 1
            continue

        # 출처 문자열 생성
        author_short = authors.split(",")[0].strip() + " et al." if authors else ""
        venue_str = f"{venue} {year}".strip() if venue or year else ""
        parts = [p for p in [author_short, venue_str] if p]
        attribution_suffix = f" — {', '.join(parts)}" if parts else ""
        attribution = f"\n*출처: [{title}]({arxiv_url}){attribution_suffix}*"

        if dry_run:
            slug = data.get("slug", paper_dir.name)
            print(f"  [DRY-RUN] {slug}: {len(matches)}개 figure에 출처 추가 예정")
            continue

        # 역순으로 삽입 (offset 보존)
        for match in reversed(matches):
            insert_pos = match.end()
            # 이미 바로 뒤에 출처가 있으면 스킵
            after = content[insert_pos:insert_pos + 10]
            if after.strip().startswith("*출처:"):
                continue
            content = content[:insert_pos] + "\n" + attribution + content[insert_pos:]

        data["content"] = content
        with open(content_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        slug = data.get("slug", paper_dir.name)
        print(f"  [UPDATE] {slug}: {len(matches)}개 figure에 출처 추가")
        updated += 1

    return {"type": "papers", "updated": updated, "skipped": skipped}


def add_architecture_attribution(dry_run: bool = False) -> dict:
    """architectures_written의 content에 논문 링크 + 출처 추가."""
    if not ARCH_DIR.exists():
        print(f"architectures_written 디렉토리 없음: {ARCH_DIR}")
        return {"status": "error"}

    updated = 0
    skipped = 0

    for arch_dir in sorted(ARCH_DIR.iterdir()):
        if not arch_dir.is_dir():
            continue

        # entry.json에서 paper_url 확인
        entry_json = arch_dir / "entry.json"
        content_json = arch_dir / "content.json"

        if not content_json.exists():
            continue

        paper_url = ""
        if entry_json.exists():
            with open(entry_json, "r", encoding="utf-8") as f:
                entry = json.load(f)
            paper_url = entry.get("paper_url", "")

        if not paper_url:
            skipped += 1
            continue

        with open(content_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        content = data.get("content", "")
        title = data.get("title", "")

        # 이미 출처 표기 있으면 스킵
        if "*출처:" in content:
            skipped += 1
            continue

        # figure 패턴 찾기
        fig_pattern = re.compile(r'(!\[.*?\]\([^)]+\))')
        matches = list(fig_pattern.finditer(content))

        if not matches:
            skipped += 1
            continue

        attribution = f"\n*출처: [{paper_url}]({paper_url}) · Architecture Diagram*"

        if dry_run:
            slug = data.get("slug", arch_dir.name)
            print(f"  [DRY-RUN] {slug}: {len(matches)}개 figure에 출처 추가 예정")
            continue

        for match in reversed(matches):
            insert_pos = match.end()
            after = content[insert_pos:insert_pos + 10]
            if after.strip().startswith("*출처:"):
                continue
            content = content[:insert_pos] + "\n" + attribution + content[insert_pos:]

        data["content"] = content
        with open(content_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        slug = data.get("slug", arch_dir.name)
        print(f"  [UPDATE] {slug}")
        updated += 1

    return {"type": "architectures", "updated": updated, "skipped": skipped}


def main():
    parser = argparse.ArgumentParser(description="Figure 출처 표기 추가")
    parser.add_argument("--papers", action="store_true", help="papers_written에 출처 추가")
    parser.add_argument("--architectures", action="store_true", help="architectures_written에 출처 추가")
    parser.add_argument("--all", action="store_true", help="전체")
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 미리보기")
    args = parser.parse_args()

    if args.papers or args.all:
        print("\n=== papers_written 출처 표기 ===")
        result = add_paper_attribution(dry_run=args.dry_run)
        print(f"완료: {result}")

    if args.architectures or args.all:
        print("\n=== architectures_written 출처 표기 ===")
        result = add_architecture_attribution(dry_run=args.dry_run)
        print(f"완료: {result}")

    if not (args.papers or args.architectures or args.all):
        parser.print_help()


if __name__ == "__main__":
    main()
