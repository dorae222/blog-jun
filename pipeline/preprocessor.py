"""
Preprocess Notion-exported markdown files.
Handles 22 markdown issues + 5 image issues in 8 phases:
  A: Preserve (LaTeX, code, mermaid → placeholders)
  B: Delete metadata (YAML frontmatter, Notion metadata)
  C: Clean Notion artifacts (page IDs, UUIDs, CSV/DB refs, embeds)
  D: Standardize image references (4 patterns → blog URLs via image_map)
  E: Convert Obsidian syntax (wiki-links, callouts)
  F: Clean HTML (<aside>, <details>, <img>, <font>)
  G: Clean text (headers, lists, blank lines, bare URLs)
  H: Restore preserved blocks
"""
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

VAULT_ROOT = Path(__file__).resolve().parent.parent.parent / "hyeongjun"
DATA_DIR = Path(__file__).parent / "data"
CATALOG_FILE = DATA_DIR / "catalog.json"
IMAGE_MAP_FILE = DATA_DIR / "image_map.json"
PREPROCESSED_DIR = DATA_DIR / "preprocessed"
REPORT_FILE = DATA_DIR / "preprocess_report.json"

# ─── Phase A: Preserve ───────────────────────────────────────────────

def preserve_blocks(content: str) -> tuple[str, dict]:
    """LaTeX, 코드 블록, Mermaid를 플레이스홀더로 치환.

    순서 중요: 코드 블록 먼저 (코드 안의 $ 보호), 그 다음 LaTeX.
    """
    blocks = {"code": [], "mermaid": [], "latex_block": [], "latex_inline": []}

    # 1. Mermaid 다이어그램 (코드 블록의 특수 케이스)
    def save_mermaid(m):
        blocks["mermaid"].append(m.group(0))
        return f"__MERMAID_{len(blocks['mermaid']) - 1}__"
    content = re.sub(r'```mermaid\n[\s\S]*?```', save_mermaid, content)

    # 2. 코드 블록 (```...```)
    def save_code(m):
        blocks["code"].append(m.group(0))
        return f"__CODE_{len(blocks['code']) - 1}__"
    content = re.sub(r'```[\s\S]*?```', save_code, content)

    # 3. LaTeX 블록 ($$...$$) + \begin{}...\end{}
    def save_latex_block(m):
        blocks["latex_block"].append(m.group(0))
        return f"__LATEXBLOCK_{len(blocks['latex_block']) - 1}__"
    content = re.sub(r'\$\$[\s\S]*?\$\$', save_latex_block, content)
    content = re.sub(r'\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}', save_latex_block, content)

    # 4. LaTeX 인라인 ($...$) — 코드/블록 밖에서만
    def save_latex_inline(m):
        blocks["latex_inline"].append(m.group(0))
        return f"__LATEXINLINE_{len(blocks['latex_inline']) - 1}__"
    content = re.sub(r'(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)', save_latex_inline, content)

    return content, blocks


def restore_blocks(content: str, blocks: dict) -> str:
    """플레이스홀더를 원본 블록으로 복원. (역순: LaTeX → 코드 → Mermaid)"""
    # LaTeX 인라인 복원
    for i, block in enumerate(blocks["latex_inline"]):
        content = content.replace(f"__LATEXINLINE_{i}__", block)
    # LaTeX 블록 복원
    for i, block in enumerate(blocks["latex_block"]):
        content = content.replace(f"__LATEXBLOCK_{i}__", block)
    # 코드 블록 복원
    for i, block in enumerate(blocks["code"]):
        content = content.replace(f"__CODE_{i}__", block)
    # Mermaid 복원
    for i, block in enumerate(blocks["mermaid"]):
        content = content.replace(f"__MERMAID_{i}__", block)
    return content


# ─── Phase B: Delete metadata ────────────────────────────────────────

def remove_metadata(content: str, stats: Counter) -> str:
    """YAML frontmatter + Notion 메타데이터 제거."""
    # YAML frontmatter (파일 시작의 ---\n...\n---)
    m = re.match(r'^---\n[\s\S]*?\n---\n?', content)
    if m:
        content = content[m.end():]
        stats["yaml_frontmatter_removed"] += 1

    # Notion 메타데이터 (생성일:, 최종 편집일:, Created:, Last Edited:)
    content, n = re.subn(
        r'^(생성일|최종\s*편집일?|Created|Last\s*Edited)\s*[:：].*$',
        '', content, flags=re.MULTILINE
    )
    stats["notion_metadata_removed"] += n

    return content


# ─── Phase C: Notion artifacts ───────────────────────────────────────

def clean_notion_artifacts(content: str, stats: Counter) -> str:
    """Notion 특유의 아티팩트 정리."""
    # C-7: Notion 페이지 ID URL → 링크 텍스트만
    # [텍스트](https://www.notion.so/Title-abc123...?pvs=21)
    content, n = re.subn(
        r'\[([^\]]+)\]\(https?://(?:www\.)?notion\.so/[^)]*\)',
        r'\1', content
    )
    stats["notion_page_url_cleaned"] += n

    # C-8: Notion UUID 파일 참조 (32자리 hex ID 포함 링크)
    # [텍스트](path%20abc123def456789012345678901234) 또는 [텍스트](path abc123...)
    # (?<!!) 로 이미지 링크(![...]) 제외 — 이미지는 Phase D에서 처리
    content, n = re.subn(
        r'(?<!!)\[([^\]]+)\]\([^)]*[a-f0-9]{32}[^)]*\)',
        r'\1', content
    )
    stats["notion_uuid_ref_cleaned"] += n

    # C-9: Notion CSV/DB 참조
    content, n = re.subn(
        r'\[([^\]]*)\]\([^\)]*\.csv\)',
        '', content
    )
    stats["notion_csv_ref_removed"] += n

    # C-10: 임베디드 PDF/동영상 참조
    content, n = re.subn(
        r'!\[[^\]]*\]\([^\)]*\.(?:pdf|mp4|mov|avi|wmv)\)',
        '', content
    )
    stats["embedded_media_removed"] += n

    return content


# ─── Phase D: Image reference standardization ────────────────────────

def _decode_url_encoding(path: str) -> str:
    """URL 인코딩 디코딩 (%25→%, %20→ 공백 등)."""
    # 이중 인코딩 처리 (%2520 → %20 → 공백)
    decoded = unquote(unquote(path))
    return decoded


def _resolve_ref_to_url(ref: str, source_path: str, ref_map: dict) -> str | None:
    """이미지 참조를 블로그 URL로 변환."""
    decoded_ref = _decode_url_encoding(ref.strip())

    # 직접 매치
    if decoded_ref in ref_map:
        return ref_map[decoded_ref]

    # 파일명만으로 매치
    filename = Path(decoded_ref).name
    if filename in ref_map:
        return ref_map[filename]

    # 90.Settings/ 접두사 제거 매치
    if decoded_ref.startswith("90.Settings/"):
        short = decoded_ref[len("90.Settings/"):]
        if short in ref_map:
            return ref_map[short]

    # 상대 경로 → vault 절대 경로 변환 후 매치
    if source_path:
        source_dir = str(Path(source_path).parent)
        # ../../90.Settings/... 같은 상대 경로
        try:
            abs_ref = str((Path(source_dir) / decoded_ref).resolve())
            # vault root 기준으로 정규화
            for key in ref_map:
                if Path(key).name == filename:
                    return ref_map[key]
        except (ValueError, OSError):
            pass

    return None


def convert_images(content: str, source_path: str, ref_map: dict, stats: Counter) -> str:
    """4가지 이미지 참조 패턴을 블로그 URL로 변환."""

    # D-11/12/13: ![[path|150]], ![[path||400]], ![[path]] → ![](blog_url)
    def replace_wikilink_img(m):
        full_ref = m.group(1)
        # |size 또는 ||size 제거
        ref = re.split(r'\|+', full_ref)[0].strip()
        url = _resolve_ref_to_url(ref, source_path, ref_map)
        if url:
            stats["wikilink_img_converted"] += 1
            return f"![]({url})"
        stats["wikilink_img_unresolved"] += 1
        return ""  # resolve 실패 시 제거

    content = re.sub(r'!\[\[([^\]]+?)\]\]', replace_wikilink_img, content)

    # D-14: ![alt](relative_local_path) → ![alt](blog_url)
    def replace_markdown_img(m):
        alt = m.group(1)
        path = m.group(2)
        # 이미 변환됨 또는 외부 URL → 스킵
        if path.startswith(("http://", "https://", "attachment:", "/media/")):
            return m.group(0)

        url = _resolve_ref_to_url(path, source_path, ref_map)
        if url:
            stats["markdown_img_converted"] += 1
            return f"![{alt}]({url})"
        stats["markdown_img_unresolved"] += 1
        return f"![{alt}]({path})"  # 변환 실패 시 원본 유지

    content = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', replace_markdown_img, content)

    # D-15: ![](attachment:img) → 제거 (Jupyter 첨부, 블로그에서 사용 불가)
    content, n = re.subn(r'!\[[^\]]*\]\(attachment:[^)]+\)', '', content)
    stats["jupyter_attachment_removed"] += n

    return content


# ─── Phase E: Obsidian syntax ─────────────────────────────────────────

def convert_obsidian_syntax(content: str, stats: Counter) -> str:
    """Obsidian 전용 문법을 표준 마크다운으로 변환."""

    # E-18: [[내부 링크]] → 텍스트만
    # [[링크|표시텍스트]] → 표시텍스트
    def replace_wikilink(m):
        inner = m.group(1)
        if "|" in inner:
            return inner.split("|", 1)[1]
        return inner
    content, n = re.subn(r'(?<!!)\[\[([^\]]+)\]\]', replace_wikilink, content)
    stats["wikilink_converted"] += n

    # E-19: > [!NOTE] / > [!특징] 콜아웃 → > **Note:** / > **특징:**
    def replace_callout(m):
        callout_type = m.group(1)
        stats["callout_converted"] += 1
        return f"> **{callout_type}:**"
    content = re.sub(r'>\s*\[!([^\]]+)\]', replace_callout, content)

    return content


# ─── Phase F: HTML cleanup ────────────────────────────────────────────

def clean_html(content: str, stats: Counter) -> str:
    """HTML 태그 정리."""

    # F-20: <aside> → blockquote
    content, n = re.subn(r'<aside>\s*', '> ', content)
    stats["aside_converted"] += n
    content = re.sub(r'\s*</aside>', '', content)

    # F-21: <details><summary> → ### 헤더 + 내용
    def replace_details(m):
        summary = m.group(1) if m.group(1) else ""
        body = m.group(2) if m.group(2) else ""
        stats["details_converted"] += 1
        result = f"### {summary}\n\n{body.strip()}" if summary else body.strip()
        return result
    content = re.sub(
        r'<details>\s*<summary>(.*?)</summary>([\s\S]*?)</details>',
        replace_details, content
    )
    # 닫히지 않은 details/summary 잔여물
    content = re.sub(r'<details>\s*<summary>(.*?)</summary>', r'### \1', content)
    content = re.sub(r'</details>', '', content)

    # F-22: <img src="..." width="..."> → ![](src)
    def replace_img_tag(m):
        src = m.group(1)
        stats["img_tag_converted"] += 1
        return f"![]({src})"
    content = re.sub(r'<img\s+[^>]*src=["\']([^"\']+)["\'][^>]*/?\s*>', replace_img_tag, content)

    # F-23: <font color="...">text</font> → text
    content, n = re.subn(r'<font[^>]*>([\s\S]*?)</font>', r'\1', content)
    stats["font_tag_removed"] += n

    # 기타 빈 HTML 태그 정리
    content = re.sub(r'<br\s*/?>', '\n', content)
    content = re.sub(r'</?(?:div|span|p)(?:\s[^>]*)?>', '', content)

    return content


# ─── Phase G: Text cleanup ────────────────────────────────────────────

def clean_text(content: str, stats: Counter) -> str:
    """텍스트 레벨 정리."""

    # G-24: ##text → ## text (헤더 공백)
    content, n = re.subn(r'^(#{1,6})([^\s#])', r'\1 \2', content, flags=re.MULTILINE)
    stats["header_space_fixed"] += n

    # G-25: 비표준 리스트 마커 (», ✓, ◦, ▪) → -
    content, n = re.subn(r'^(\s*)[»✓◦▪►•]\s+', r'\1- ', content, flags=re.MULTILINE)
    stats["nonstandard_list_marker_fixed"] += n

    # G-26: 빈 링크 [text]() → text
    content, n = re.subn(r'\[([^\]]*)\]\(\s*\)', r'\1', content)
    stats["empty_link_fixed"] += n

    # G-27: 과도한 빈 줄 (3줄+ → 2줄)
    content, n = re.subn(r'\n{4,}', '\n\n\n', content)
    stats["excessive_blank_lines_fixed"] += n

    return content


# ─── Main pipeline ─────────────────────────────────────────────────────

def preprocess_content(content: str, source_path: str = "", ref_map: dict = None) -> tuple[str, dict]:
    """전체 전처리 파이프라인.

    Args:
        content: 마크다운 콘텐츠
        source_path: 소스 파일의 vault 상대 경로
        ref_map: image_processor가 생성한 참조→URL 매핑

    Returns:
        (전처리된 콘텐츠, 이슈별 처리 횟수 dict)
    """
    if ref_map is None:
        ref_map = {}

    stats = Counter()

    # Phase A: 보존
    content, blocks = preserve_blocks(content)

    # Phase B: 메타데이터 삭제
    content = remove_metadata(content, stats)

    # Phase C: Notion 아티팩트
    content = clean_notion_artifacts(content, stats)

    # Phase D: 이미지 참조 표준화
    content = convert_images(content, source_path, ref_map, stats)

    # Phase E: Obsidian 문법
    content = convert_obsidian_syntax(content, stats)

    # Phase F: HTML 정리
    content = clean_html(content, stats)

    # Phase G: 텍스트 정리
    content = clean_text(content, stats)

    # Phase H: 복원
    content = restore_blocks(content, blocks)

    return content.strip(), dict(stats)


def preprocess_file(file_path: Path, source_path: str = "", ref_map: dict = None) -> tuple[str, dict]:
    """단일 파일 전처리."""
    content = file_path.read_text(encoding="utf-8")
    return preprocess_content(content, source_path, ref_map)


def main():
    """전체 카탈로그 전처리 + 리포트 생성."""
    if not CATALOG_FILE.exists():
        print("Error: Run scanner.py first!")
        return

    with open(CATALOG_FILE) as f:
        catalog = json.load(f)

    # image_map 로드
    ref_map = {}
    if IMAGE_MAP_FILE.exists():
        with open(IMAGE_MAP_FILE) as f:
            map_data = json.load(f)
        ref_map = map_data.get("ref_map", {})
        print(f"Loaded image map: {len(ref_map)} entries")
    else:
        print("Warning: No image_map.json found. Run image_processor.py first for image path conversion.")

    PREPROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    total_stats = Counter()
    file_reports = []
    processed = 0
    skipped = 0

    for item in catalog:
        if item.get("skip", False):
            skipped += 1
            continue

        file_path = VAULT_ROOT / item["path"]
        if not file_path.exists():
            continue

        content, file_stats = preprocess_file(file_path, item["path"], ref_map)
        out_path = PREPROCESSED_DIR / item["path"].replace("/", "__")
        out_path.write_text(content, encoding="utf-8")

        total_stats.update(file_stats)
        processed += 1

        if any(v > 0 for v in file_stats.values()):
            file_reports.append({
                "path": item["path"],
                "stats": dict(file_stats),
            })

    # 리포트 생성
    report = {
        "total_files": len(catalog),
        "processed": processed,
        "skipped": skipped,
        "issue_counts": dict(total_stats.most_common()),
        "files_with_changes": len(file_reports),
        "file_details": file_reports,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # 결과 출력
    print(f"\n=== Preprocessing Results ===")
    print(f"Processed: {processed} | Skipped: {skipped}")
    print(f"Files with changes: {len(file_reports)}")
    print(f"\nIssue counts:")
    for issue, count in total_stats.most_common():
        print(f"  {issue}: {count}")
    print(f"\nPreprocessed files saved to {PREPROCESSED_DIR}")
    print(f"Report saved to {REPORT_FILE}")


if __name__ == "__main__":
    main()
