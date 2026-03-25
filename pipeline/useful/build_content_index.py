#!/usr/bin/env python3
"""
전체 컨텐츠 목록 종합 인덱스 생성 스크립트

모든 201개 논문 디렉토리를 순회하여 content_index.json 생성:
- content.json 메타데이터 (content 전문 제외)
- 섹션 헤더 목록
- figures/ 디렉토리 내 모든 이미지 파일
- figure_reference.json (영문 캡션, 있으면)
- content 파싱으로 추출한 한국어 alt/캡션 및 섹션 위치

출력: pipeline/data/content_index.json
"""
import json
import os
import re
import glob
from datetime import datetime

PAPERS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "papers_written"
)
OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "content_index.json"
)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}

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


def process_paper(paper_dir: str) -> dict:
    """단일 논문 디렉토리 처리."""
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

        content_text = data.get("content", "")
        entry["sections"] = extract_sections(content_text)
    else:
        entry["sections"] = []

    # content에서 figure 참조 파싱
    content_figs = parse_content_figures(content_text)  # {filename: {...}}

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

    # 각 파일에 대해 종합 정보 구성
    items = []
    for fname in all_files:
        ref_info = fig_ref_map.get(fname, {})
        content_ref = content_figs.get(fname, {})

        item = {
            "filename": fname,
            "caption_en": ref_info.get("caption_en", ""),
            "figure_number": ref_info.get("figure_number", ""),
            "has_caption_en": ref_info.get("has_caption_en", False),
            "referenced_in_content": fname in content_figs,
            "section": content_ref.get("section"),
            "alt_ko": content_ref.get("alt_ko"),
            "caption_ko": content_ref.get("caption_ko"),
        }
        items.append(item)

    # figure_reference.json에만 있고 files에 없는 경우 (희귀하지만 처리)
    for fname, ref_info in fig_ref_map.items():
        if fname not in all_files:
            content_ref = content_figs.get(fname, {})
            items.append({
                "filename": fname,
                "caption_en": ref_info.get("caption_en", ""),
                "figure_number": ref_info.get("figure_number", ""),
                "has_caption_en": ref_info.get("has_caption_en", False),
                "referenced_in_content": fname in content_figs,
                "section": content_ref.get("section"),
                "alt_ko": content_ref.get("alt_ko"),
                "caption_ko": content_ref.get("caption_ko"),
                "file_missing": True,
            })

    entry["figures"] = {
        "total_available": len(all_files),
        "total_referenced": len(content_figs),
        "has_figure_reference_json": has_fig_ref,
        "items": items,
    }

    return entry


def main():
    # 모든 논문 디렉토리 순회
    all_dirs = sorted([
        d for d in glob.glob(os.path.join(PAPERS_DIR, "*"))
        if os.path.isdir(d)
    ])

    papers = []
    total_figure_files = 0
    total_figure_refs = 0
    papers_with_content = 0
    papers_figures_only = 0

    for paper_dir in all_dirs:
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

    output = {
        "generated_at": datetime.now().isoformat(),
        "stats": {
            "total_dirs": len(all_dirs),
            "papers_with_content": papers_with_content,
            "papers_figures_only": papers_figures_only,
            "total_figure_files": total_figure_files,
            "total_figure_refs_in_content": total_figure_refs,
        },
        "papers": papers_sorted,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✓ 완료: {OUTPUT_PATH}")
    print(f"  총 디렉토리: {len(all_dirs)}개")
    print(f"  컨텐츠 있음: {papers_with_content}개")
    print(f"  Figure만 있음: {papers_figures_only}개")
    print(f"  총 figure 파일: {total_figure_files}개")
    print(f"  총 figure 참조: {total_figure_refs}개")
    print(f"  출력 크기: {os.path.getsize(OUTPUT_PATH) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
