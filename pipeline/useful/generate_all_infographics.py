"""
모든 포스트에 대해 인포그래픽 SVG/PNG 일괄 생성.

사용법:
    python3 pipeline/useful/generate_all_infographics.py            # 모든 카테고리
    python3 pipeline/useful/generate_all_infographics.py papers     # 단일 카테고리
    python3 pipeline/useful/generate_all_infographics.py --no-png   # SVG만
    python3 pipeline/useful/generate_all_infographics.py --force    # 기존 덮어쓰기

출력: pipeline/data/{category}_written/{slug}/figures/infographic.svg (+ .png)
"""
from __future__ import annotations
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipeline" / "generators"))

from infographic_v3 import render_card  # noqa: E402
from infographic_adapter import adapt   # noqa: E402

DATA_ROOT = ROOT / "pipeline" / "data"

CATEGORIES = [
    ("papers_written",          "paper",        "content.json"),
    ("architectures_written",   "architecture", "entry.json"),
    ("cloud_written",           "cloud",        "content.json"),
    ("ml_written",              "ml",           "content.json"),
    ("data_written",            "data",         "content.json"),
    ("colab_written",           "colab",        "content.json"),
]


def generate_for_post(slug_dir: Path, content_type: str, json_name: str,
                       force: bool, render_png: bool) -> tuple[str, str]:
    """단일 포스트 인포그래픽 생성. 반환: (status, message)"""
    json_path = slug_dir / json_name
    if not json_path.exists():
        return ("skip", f"no {json_name}")

    figures_dir = slug_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    svg_path = figures_dir / "infographic.svg"
    png_path = figures_dir / "infographic.png"

    if svg_path.exists() and not force:
        return ("skip", "exists")

    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        args = adapt(content_type, data)
        svg = render_card(**args)
        svg_path.write_text(svg, encoding="utf-8")
        if render_png:
            r = subprocess.run(
                ["rsvg-convert", "-w", "1800", "-h", "1380", str(svg_path), "-o", str(png_path)],
                capture_output=True, timeout=15,
            )
            if r.returncode != 0:
                return ("error", f"rsvg-convert failed: {r.stderr.decode()[:60]}")
        return ("ok", "")
    except Exception as e:
        return ("error", str(e)[:80])


def run(category_filter: str | None, force: bool, render_png: bool):
    total = {"ok": 0, "skip": 0, "error": 0}
    errors = []

    for cat_dir, content_type, json_name in CATEGORIES:
        if category_filter and cat_dir != category_filter and content_type != category_filter:
            continue
        cat_path = DATA_ROOT / cat_dir
        if not cat_path.exists():
            continue
        slugs = sorted([p for p in cat_path.iterdir() if p.is_dir()])
        print(f"\n[{content_type}] {cat_dir} — {len(slugs)} posts")
        for i, slug_dir in enumerate(slugs, 1):
            status, msg = generate_for_post(slug_dir, content_type, json_name, force, render_png)
            total[status] += 1
            if status == "error":
                errors.append((slug_dir.name, msg))
                if len(errors) <= 5:
                    print(f"  [ERR] {slug_dir.name}: {msg}")
            if i % 50 == 0 or i == len(slugs):
                print(f"  {i}/{len(slugs)} (ok={total['ok']} skip={total['skip']} err={total['error']})")

    print(f"\n=== TOTAL: ok={total['ok']}, skip={total['skip']}, error={total['error']} ===")
    if errors:
        print(f"\n첫 {min(10, len(errors))}개 에러:")
        for name, msg in errors[:10]:
            print(f"  - {name}: {msg}")


def main():
    args = sys.argv[1:]
    force = "--force" in args
    no_png = "--no-png" in args
    cat = None
    for a in args:
        if not a.startswith("--"):
            cat = a
            break
    run(cat, force=force, render_png=not no_png)


if __name__ == "__main__":
    main()
