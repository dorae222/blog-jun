"""
Scan Obsidian vault and catalog markdown files for blog processing.
Excludes: 80.Certificate/, 90.Settings/, hidden dirs, trash
Adds: quality grading, content flags, image reference collection, skip/large markers
"""
import json
import re
from collections import Counter
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent / "hyeongjun"
EXCLUDE_DIRS = {"80.Certificate", "90.Settings", "trash", "_scripts", ".obsidian", ".trash"}
OUTPUT_FILE = Path(__file__).parent / "data" / "catalog.json"

# 00.Inbox 수동 제외 대상 파일명
MANUAL_SKIP_FILES = {
    "HOME.md",
}

CATEGORY_MAP = {
    "10.Cloud": ("Cloud", "☁️", "#FF9900"),
    "20.AI": ("AI/ML", "🤖", "#FF6F00"),
    "30.Data": ("Data Engineering", "📊", "#336791"),
    "40.DEV": ("Development", "💻", "#3776AB"),
    "50.Foundation": ("Foundation", "📐", "#6366F1"),
    "60.Project": ("Projects", "🚀", "#059669"),
    "70.Program": ("Programs", "🎓", "#EC4899"),
}

# 이미지 참조 패턴 (4가지)
# 1. ![[path]] Obsidian wiki-link (with optional |size)
RE_IMG_WIKILINK = re.compile(r'!\[\[([^\]|]+?)(?:\|[^\]]*?)?\]\]')
# 2. ![alt](path) 표준 마크다운 (로컬 경로만, 외부 URL/data URI 제외)
RE_IMG_MARKDOWN = re.compile(r'!\[([^\]]*)\]\((?!https?://|attachment:|data:)([^)]+)\)')
# 3. ![](attachment:image.png) Jupyter
RE_IMG_JUPYTER = re.compile(r'!\[[^\]]*\]\(attachment:([^)]+)\)')
# 4. 외부 URL
RE_IMG_EXTERNAL = re.compile(r'!\[[^\]]*\]\((https?://[^)]+)\)')


def extract_image_refs(content: str) -> list[dict]:
    """마크다운 콘텐츠에서 모든 이미지 참조를 추출."""
    refs = []

    for m in RE_IMG_WIKILINK.finditer(content):
        refs.append({"type": "wikilink", "ref": m.group(1).strip()})

    for m in RE_IMG_MARKDOWN.finditer(content):
        refs.append({"type": "markdown", "ref": m.group(2).strip()})

    for m in RE_IMG_JUPYTER.finditer(content):
        refs.append({"type": "jupyter", "ref": m.group(1).strip()})

    for m in RE_IMG_EXTERNAL.finditer(content):
        refs.append({"type": "external", "ref": m.group(1).strip()})

    return refs


def get_quality_grade(char_count: int) -> str:
    """글자 수 기반 품질 등급."""
    if char_count < 50:
        return "SKIP"
    if char_count < 100:
        return "C"
    if char_count < 500:
        return "B"
    return "A"


def get_content_flags(content: str) -> dict:
    """콘텐츠 특성 플래그."""
    return {
        "has_latex": bool(re.search(r'\$\$.+?\$\$|\$[^$\n]+\$', content, re.DOTALL)),
        "has_code": bool(re.search(r'```', content)),
        "has_images": bool(RE_IMG_WIKILINK.search(content) or RE_IMG_MARKDOWN.search(content)),
        "has_tables": bool(re.search(r'^\|.+\|$', content, re.MULTILINE)),
        "has_frontmatter": content.strip().startswith("---"),
    }


def scan_vault():
    """Scan vault and return file catalog with quality grades and image refs."""
    catalog = []

    for md_file in sorted(VAULT_ROOT.rglob("*.md")):
        rel_path = md_file.relative_to(VAULT_ROOT)
        parts = rel_path.parts

        # Skip excluded directories
        if any(part in EXCLUDE_DIRS or part.startswith(".") for part in parts):
            continue

        # Skip manual exclusion files
        if rel_path.name in MANUAL_SKIP_FILES:
            continue

        # Determine top-level category
        top_dir = parts[0] if len(parts) > 1 else ""
        cat_info = CATEGORY_MAP.get(top_dir, ("Uncategorized", "📁", "#6B7280"))

        # Read content
        try:
            content = md_file.read_text(encoding="utf-8")
        except Exception:
            content = ""

        # Extract title from first heading or filename
        title = rel_path.stem
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped.startswith("# ") and not stripped.startswith("# ---"):
                title = stripped[2:].strip()
                break

        char_count = len(content)
        word_count = len(content.split())
        quality = get_quality_grade(char_count)
        flags = get_content_flags(content)
        image_refs = extract_image_refs(content)

        entry = {
            "path": str(rel_path),
            "title": title,
            "top_category": top_dir,
            "category_name": cat_info[0],
            "category_icon": cat_info[1],
            "category_color": cat_info[2],
            "subcategory": parts[1] if len(parts) > 2 else "",
            "word_count": word_count,
            "char_count": char_count,
            "quality": quality,
            "skip": quality == "SKIP",
            "large": char_count > 100000,
            **flags,
            "image_refs": image_refs,
        }

        catalog.append(entry)

    return catalog


def print_stats(catalog: list[dict]):
    """카탈로그 통계 출력."""
    total = len(catalog)
    skipped = sum(1 for e in catalog if e["skip"])
    large = sum(1 for e in catalog if e["large"])
    active = total - skipped

    print(f"\n=== Vault Scan Results ===")
    print(f"Total files: {total}")
    print(f"Active: {active} | Skipped (SKIP): {skipped} | Large (>100K): {large}")

    # 품질 분포
    grade_dist = Counter(e["quality"] for e in catalog)
    print(f"\nQuality distribution:")
    for grade in ["A", "B", "C", "SKIP"]:
        print(f"  {grade}: {grade_dist.get(grade, 0)}")

    # 카테고리 분포
    print(f"\nCategory distribution:")
    cat_dist = Counter(e["category_name"] for e in catalog if not e["skip"])
    for cat, count in cat_dist.most_common():
        print(f"  {cat}: {count}")

    # 콘텐츠 플래그 통계
    print(f"\nContent flags (active files only):")
    active_entries = [e for e in catalog if not e["skip"]]
    for flag in ["has_latex", "has_code", "has_images", "has_tables", "has_frontmatter"]:
        count = sum(1 for e in active_entries if e[flag])
        print(f"  {flag}: {count}")

    # 이미지 참조 통계
    total_refs = sum(len(e["image_refs"]) for e in catalog)
    ref_types = Counter()
    for e in catalog:
        for ref in e["image_refs"]:
            ref_types[ref["type"]] += 1
    print(f"\nImage references: {total_refs} total")
    for rtype, count in ref_types.most_common():
        print(f"  {rtype}: {count}")


def main():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    catalog = scan_vault()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    print_stats(catalog)
    print(f"\nCatalog saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
