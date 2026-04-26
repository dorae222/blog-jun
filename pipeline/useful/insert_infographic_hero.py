"""
각 포스트의 content.md 최상단에 infographic hero 이미지 삽입.

전략:
- figures/infographic.svg 가 있는 포스트 대상
- content.md 시작 부분에 다음 패턴이 없으면 삽입:
    ![<title> 핵심 요약](figures/infographic.svg)
    *Figure: <title> 한 장 요약 인포그래픽*
- 이미 한 번이라도 삽입된 포스트는 건너뜀 (멱등)

사용법:
    python3 pipeline/useful/insert_infographic_hero.py            # 전체
    python3 pipeline/useful/insert_infographic_hero.py papers     # 단일 카테고리
    python3 pipeline/useful/insert_infographic_hero.py --dry-run  # 미리보기
"""
from __future__ import annotations
import sys
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "pipeline" / "data"

CATEGORIES = [
    ("papers_written",        "content.json"),
    ("architectures_written", "entry.json"),
    ("cloud_written",         "content.json"),
    ("ml_written",            "content.json"),
    ("data_written",          "content.json"),
    ("colab_written",         "content.json"),
]

# 삽입 마커 (이 라인이 있으면 이미 삽입된 것으로 간주)
HERO_MARKER = "<!-- infographic-hero -->"


def hero_block(title: str, slug: str) -> str:
    """삽입할 markdown 블록"""
    safe_title = title.replace("[", "(").replace("]", ")")
    return (
        f"{HERO_MARKER}\n"
        f"![{safe_title} 핵심 요약](figures/infographic.svg)\n\n"
        f"*Figure: {safe_title} 한 장 요약 인포그래픽*\n\n"
    )


def process_post(slug_dir: Path, json_name: str, dry_run: bool) -> str:
    """단일 포스트 처리. 반환: status"""
    md_path = slug_dir / "content.md"
    json_path = slug_dir / json_name
    svg_path = slug_dir / "figures" / "infographic.svg"

    if not md_path.exists() or not json_path.exists():
        return "skip-missing"
    if not svg_path.exists():
        return "skip-no-svg"

    md_text = md_path.read_text(encoding="utf-8")
    if HERO_MARKER in md_text:
        return "skip-already"

    data = json.loads(json_path.read_text(encoding="utf-8"))
    title = data.get("name") or data.get("title") or data.get("title_ko") or slug_dir.name

    block = hero_block(title, slug_dir.name)
    new_text = block + md_text

    if dry_run:
        return "would-insert"

    md_path.write_text(new_text, encoding="utf-8")
    return "ok"


def run(category_filter: str | None, dry_run: bool):
    total: dict[str, int] = {}
    for cat_dir, json_name in CATEGORIES:
        if category_filter and not (category_filter in cat_dir):
            continue
        cat_path = DATA_ROOT / cat_dir
        if not cat_path.exists():
            continue
        slugs = sorted([p for p in cat_path.iterdir() if p.is_dir()])
        cat_stats = {"ok": 0, "skip-already": 0, "skip-no-svg": 0, "skip-missing": 0, "would-insert": 0}
        for slug_dir in slugs:
            status = process_post(slug_dir, json_name, dry_run)
            cat_stats[status] = cat_stats.get(status, 0) + 1
            total[status] = total.get(status, 0) + 1
        print(f"[{cat_dir}] {cat_stats}")
    print(f"\n=== TOTAL: {total} ===")


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    cat = next((a for a in args if not a.startswith("--")), None)
    run(cat, dry_run=dry_run)


if __name__ == "__main__":
    main()
