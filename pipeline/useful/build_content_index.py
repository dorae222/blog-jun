#!/usr/bin/env python3
"""
전체 컨텐츠 목록 종합 인덱스 생성 스크립트

모든 카테고리 디렉토리를 순회하여 blog-jun-content.json 생성:
- papers: 상세 (figures, improvement_plan 포함)
- architectures, cloud, ml, data, colab: 경량 엔트리

출력: pipeline/data/blog-jun-content.json
"""
import json
import os
import re
import glob
from datetime import datetime

DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data"
)
PAPERS_DIR = os.path.join(DATA_DIR, "papers_written")
OUTPUT_PATH = os.path.join(DATA_DIR, "blog-jun-content.json")

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}

# 비-papers 카테고리 정의
OTHER_CATEGORIES = {
    "architectures": "architectures_written",
    "cloud": "cloud_written",
    "ml": "ml_written",
    "data": "data_written",
    "colab": "colab_written",
}


# figures/metadata.json에서 source_url 추출용
def load_figures_metadata(paper_dir: str) -> dict:
    """figures/metadata.json → {filename: {source_url, caption, figure_number, has_caption}}"""
    metadata_path = os.path.join(paper_dir, "figures", "metadata.json")
    if not os.path.exists(metadata_path):
        return {}
    with open(metadata_path, "r", encoding="utf-8") as f:
        items = json.load(f)
    result = {}
    for item in items:
        fname = item.get("filename", "")
        if fname:
            result[fname] = {
                "source_url": item.get("source_url") or item.get("url") or None,
                "caption": item.get("caption", ""),
                "figure_number": item.get("figure_number", ""),
                "has_caption": bool(item.get("caption", "")),
            }
    return result

# content 전문에서 figure 참조 파싱:
# 패턴1: ![alt](figures/filename)\n*caption*  (줄바꿈 후 캡션)
# 패턴2: ![alt](figures/filename)  (캡션 없음)
FIG_WITH_CAPTION = re.compile(
    r'!\[([^\]]*)\]\(figures/([^)]+\.(?:png|jpg|jpeg|webp|gif|svg))\)\s*\n\s*\*([^*]+)\*',
    re.MULTILINE
)
FIG_NO_CAPTION = re.compile(
    r'!\[([^\]]*)\]\(figures/([^)]+\.(?:png|jpg|jpeg|webp|gif|svg))\)'
)
SECTION_HEADER = re.compile(r'^## .+', re.MULTILINE)


def parse_content_figures(content: str) -> dict:
    """
    content 마크다운에서 figure 참조를 파싱.
    반환: {filename: {"alt_ko": str, "caption_ko": str, "section": str}}
    """
    result = {}

    # 섹션별 위치 계산
    section_positions = [(m.start(), m.group()) for m in SECTION_HEADER.finditer(content)]

    def find_section(pos: int) -> str:
        """pos 이전의 가장 가까운 ## 섹션 헤더 반환."""
        current = None
        for spos, stitle in section_positions:
            if spos <= pos:
                current = stitle
            else:
                break
        return current

    # 캡션 있는 figure 먼저 추출
    for m in FIG_WITH_CAPTION.finditer(content):
        alt = m.group(1).strip()
        filename = m.group(2).strip()
        caption = m.group(3).strip()
        section = find_section(m.start())
        result[filename] = {
            "alt_ko": alt,
            "caption_ko": caption,
            "section": section,
        }

    # 캡션 없는 figure (아직 없는 것만)
    for m in FIG_NO_CAPTION.finditer(content):
        alt = m.group(1).strip()
        filename = m.group(2).strip()
        if filename not in result:
            section = find_section(m.start())
            result[filename] = {
                "alt_ko": alt,
                "caption_ko": None,
                "section": section,
            }

    return result


def extract_sections(content: str) -> list:
    """content에서 ## 섹션 헤더 목록 추출."""
    return [m.group() for m in SECTION_HEADER.finditer(content)]


def get_figure_files(paper_dir: str) -> list:
    """figures/ 디렉토리 내 모든 이미지 파일 목록 (정렬)."""
    fig_dir = os.path.join(paper_dir, "figures")
    if not os.path.isdir(fig_dir):
        return []
    files = []
    for fname in sorted(os.listdir(fig_dir)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            files.append(fname)
    return files


def read_content_text(item_dir: str) -> str:
    """content.md 우선, 없으면 content.json의 content 필드 폴백."""
    content_md_path = os.path.join(item_dir, "content.md")
    if os.path.exists(content_md_path):
        with open(content_md_path, "r", encoding="utf-8") as f:
            return f.read()
    content_json_path = os.path.join(item_dir, "content.json")
    if os.path.exists(content_json_path):
        with open(content_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("content", "")
    return ""


def process_paper(paper_dir: str) -> dict:
    """단일 논문 디렉토리 처리 (상세 모드)."""
    dir_name = os.path.basename(paper_dir)

    # numbered 여부
    match = re.match(r'^(\d+)_(.+)$', dir_name)
    numbered = bool(match)
    number = int(match.group(1)) if match else None
    slug_from_dir = match.group(2) if match else dir_name

    content_path = os.path.join(paper_dir, "content.json")
    has_content = os.path.exists(content_path)

    entry = {
        "slug": slug_from_dir,
        "dir": dir_name,
        "numbered": numbered,
        "number": number,
        "has_content": has_content,
    }

    # content.json 읽기
    content_text = ""
    if has_content:
        with open(content_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # slug는 content.json 우선
        entry["slug"] = data.get("slug", slug_from_dir)

        # 메타데이터 필드 (content 전문 제외)
        for field in ["id", "title", "title_ko", "category", "sub_category",
                      "year", "venue", "authors", "arxiv_url", "summary",
                      "quality_score", "tags", "related_architecture"]:
            entry[field] = data.get(field)

        content_text = read_content_text(paper_dir)
        entry["sections"] = extract_sections(content_text)
    else:
        entry["sections"] = []

    # content에서 figure 참조 파싱
    content_figs = parse_content_figures(content_text)  # {filename: {...}}

    # figures/metadata.json 읽기 (source_url 포함)
    metadata_map = load_figures_metadata(paper_dir)  # {filename: {source_url, ...}}

    # figure_reference.json 읽기
    fig_ref_path = os.path.join(paper_dir, "figure_reference.json")
    has_fig_ref = os.path.exists(fig_ref_path)
    fig_ref_map = {}  # {filename: {caption_en, figure_number, has_caption_en}}
    if has_fig_ref:
        with open(fig_ref_path, "r", encoding="utf-8") as f:
            fig_ref = json.load(f)
        for fig in fig_ref.get("figures", []):
            fname = fig.get("filename", "")
            fig_ref_map[fname] = {
                "caption_en": fig.get("caption", ""),
                "figure_number": fig.get("figure_number", ""),
                "has_caption_en": bool(fig.get("has_caption", False)),
            }

    # figures/ 디렉토리 스캔
    all_files = get_figure_files(paper_dir)

    def make_content_description(caption_ko, caption_en, alt_ko):
        """LLM 없이 content_description 생성."""
        if caption_ko:
            return caption_ko[:100]
        if caption_en:
            return caption_en[:100]
        if alt_ko:
            return alt_ko
        return None

    # 각 파일에 대해 종합 정보 구성
    items = []
    source_url_count = 0
    for fname in all_files:
        ref_info = fig_ref_map.get(fname, {})
        content_ref = content_figs.get(fname, {})
        meta = metadata_map.get(fname, {})

        # source_url: metadata.json 우선, 없으면 null
        source_url = meta.get("source_url")
        if source_url:
            source_url_count += 1

        caption_ko = content_ref.get("caption_ko")
        caption_en = ref_info.get("caption_en") or meta.get("caption", "")
        alt_ko = content_ref.get("alt_ko")

        item = {
            "filename": fname,
            "figure_number": ref_info.get("figure_number") or meta.get("figure_number", ""),
            "has_caption_en": ref_info.get("has_caption_en", False) or meta.get("has_caption", False),
            "caption_en": caption_en,
            "source_url": source_url,
            "content_description": make_content_description(caption_ko, caption_en, alt_ko),
            "referenced_in_content": fname in content_figs,
            "section": content_ref.get("section"),
            "alt_ko": alt_ko,
            "caption_ko": caption_ko,
        }
        items.append(item)

    # figure_reference.json에만 있고 files에 없는 경우 (희귀하지만 처리)
    for fname, ref_info in fig_ref_map.items():
        if fname not in all_files:
            content_ref = content_figs.get(fname, {})
            meta = metadata_map.get(fname, {})
            source_url = meta.get("source_url")
            if source_url:
                source_url_count += 1
            caption_ko = content_ref.get("caption_ko")
            caption_en = ref_info.get("caption_en") or meta.get("caption", "")
            alt_ko = content_ref.get("alt_ko")
            items.append({
                "filename": fname,
                "figure_number": ref_info.get("figure_number") or meta.get("figure_number", ""),
                "has_caption_en": ref_info.get("has_caption_en", False) or meta.get("has_caption", False),
                "caption_en": caption_en,
                "source_url": source_url,
                "content_description": make_content_description(caption_ko, caption_en, alt_ko),
                "referenced_in_content": fname in content_figs,
                "section": content_ref.get("section"),
                "alt_ko": alt_ko,
                "caption_ko": caption_ko,
                "file_missing": True,
            })

    # paper_source 구성
    arxiv_url = entry.get("arxiv_url")
    ar5iv_url = None
    if arxiv_url:
        arxiv_id = arxiv_url.rstrip("/").split("/")[-1]
        ar5iv_url = f"https://ar5iv.labs.arxiv.org/html/{arxiv_id}"

    entry["paper_source"] = {
        "arxiv_url": arxiv_url,
        "ar5iv_url": ar5iv_url,
        "figures_have_source_url": source_url_count > 0,
        "figures_source_url_count": source_url_count,
    }

    entry["figures"] = {
        "total_available": len(all_files),
        "total_referenced": len(content_figs),
        "has_figure_reference_json": has_fig_ref,
        "has_metadata_json": bool(metadata_map),
        "items": items,
    }

    return entry


def process_other_category(category_name: str, dir_name: str) -> list:
    """비-papers 카테고리 경량 처리."""
    category_dir = os.path.join(DATA_DIR, dir_name)
    if not os.path.isdir(category_dir):
        print(f"  [WARN] 디렉토리 없음: {dir_name}")
        return []

    all_dirs = sorted([
        d for d in glob.glob(os.path.join(category_dir, "*"))
        if os.path.isdir(d)
    ])

    entries = []
    for item_dir in all_dirs:
        item_name = os.path.basename(item_dir)

        # content.json 또는 entry.json 읽기
        content_json_path = os.path.join(item_dir, "content.json")
        entry_json_path = os.path.join(item_dir, "entry.json")

        data = {}
        has_content_json = os.path.exists(content_json_path)
        has_entry_json = os.path.exists(entry_json_path)

        if has_content_json:
            with open(content_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        elif has_entry_json:
            with open(entry_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        # content 텍스트 읽기 (섹션 수 계산용)
        content_text = read_content_text(item_dir)
        sections = extract_sections(content_text)
        has_content = bool(content_text.strip())

        # figures 확인
        figure_files = get_figure_files(item_dir)
        has_figures = len(figure_files) > 0

        # title 결정
        title = (data.get("title_ko") or data.get("title")
                 or data.get("name") or item_name)

        # slug 결정
        slug = data.get("slug") or item_name

        # tags
        tags = data.get("tags", [])

        entry = {
            "slug": slug,
            "dir": item_name,
            "title": title,
            "category": category_name,
            "has_content": has_content,
            "sections": sections,
            "section_count": len(sections),
            "has_figures": has_figures,
            "figure_count": len(figure_files),
            "tags": tags,
        }

        # 카테고리별 추가 필드
        if category_name == "architectures" and has_entry_json:
            entry["organization"] = data.get("organization")
            entry["architecture_category"] = data.get("architecture_category")

        if data.get("summary"):
            entry["summary"] = data["summary"]

        # 경량 improvement_plan
        if has_content and has_figures:
            plan_type = "content_with_figures"
            priority = 3
            summary = f"컨텐츠 + figure {len(figure_files)}개. 배치 검토 필요."
        elif has_content:
            plan_type = "content_review"
            priority = 4
            summary = "컨텐츠 검토 필요."
        elif has_figures:
            plan_type = "write_content"
            priority = 5
            summary = f"컨텐츠 없음. figure {len(figure_files)}개 보유."
        else:
            plan_type = "write_content"
            priority = 5
            summary = "컨텐츠 및 figure 없음."

        entry["improvement_plan"] = {
            "status": "pending",
            "priority": priority,
            "type": plan_type,
            "summary": summary,
        }

        entries.append(entry)

    return entries


def main():
    # === papers ===
    all_paper_dirs = sorted([
        d for d in glob.glob(os.path.join(PAPERS_DIR, "*"))
        if os.path.isdir(d)
    ])

    papers = []
    total_figure_files = 0
    total_figure_refs = 0
    papers_with_content = 0
    papers_figures_only = 0

    for paper_dir in all_paper_dirs:
        entry = process_paper(paper_dir)
        papers.append(entry)

        total_figure_files += entry["figures"]["total_available"]
        total_figure_refs += entry["figures"]["total_referenced"]
        if entry["has_content"]:
            papers_with_content += 1
        else:
            papers_figures_only += 1

    # 번호 논문을 앞으로, 비번호 논문은 slug 순으로 정렬
    numbered = sorted([p for p in papers if p["numbered"]], key=lambda x: x["number"])
    non_numbered = sorted([p for p in papers if not p["numbered"]], key=lambda x: x["slug"])
    papers_sorted = numbered + non_numbered

    # === 비-papers 카테고리 ===
    other_sections = {}
    other_counts = {}
    for cat_name, dir_name in OTHER_CATEGORIES.items():
        print(f"처리 중: {cat_name} ({dir_name})...")
        entries = process_other_category(cat_name, dir_name)
        other_sections[cat_name] = entries
        other_counts[cat_name] = len(entries)
        print(f"  → {len(entries)}개 엔트리")

    # === 출력 구성 ===
    total = len(papers_sorted) + sum(other_counts.values())

    output = {
        "generated_at": datetime.now().isoformat(),
        "stats": {
            "total": total,
            "by_type": {
                "papers": len(papers_sorted),
                **other_counts,
            },
            "papers_with_content": papers_with_content,
            "papers_figures_only": papers_figures_only,
            "total_figure_files": total_figure_files,
            "total_figure_refs_in_content": total_figure_refs,
        },
        "papers": papers_sorted,
    }

    # 비-papers 섹션 추가
    for cat_name in OTHER_CATEGORIES:
        output[cat_name] = other_sections[cat_name]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 완료: {OUTPUT_PATH}")
    print(f"  총 엔트리: {total}개")
    print(f"  papers: {len(papers_sorted)}개 (컨텐츠 {papers_with_content}, figure만 {papers_figures_only})")
    for cat_name, count in other_counts.items():
        print(f"  {cat_name}: {count}개")
    print(f"  총 figure 파일 (papers): {total_figure_files}개")
    print(f"  총 figure 참조 (papers): {total_figure_refs}개")
    print(f"  출력 크기: {os.path.getsize(OUTPUT_PATH) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
