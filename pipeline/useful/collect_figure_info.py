#!/usr/bin/env python3
"""
figure_reference.json 생성 스크립트

각 numbered paper에 대해:
1. figures/metadata.json 읽기 (있으면)
2. 없으면: ls figures/fig_*.png 만 기록 (캡션 없음)
3. content.json에서 섹션 구조 추출 (## 헤더만)
4. 현재 figure 참조 추출 (![...](figures/...) 패턴)
출력: pipeline/data/papers_written/{slug}/figure_reference.json
"""
import json
import os
import re
import glob
import sys

PAPERS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "papers_written"
)


def collect_figure_info(paper_dir: str) -> dict:
    """단일 논문 디렉토리에 대한 figure 참조 정보 수집."""
    content_path = os.path.join(paper_dir, "content.json")
    if not os.path.exists(content_path):
        return None

    with open(content_path, "r", encoding="utf-8") as f:
        content_data = json.load(f)

    slug = content_data.get("slug", os.path.basename(paper_dir))
    body = content_data.get("content", "")

    # 1. figures/metadata.json 읽기
    metadata_path = os.path.join(paper_dir, "figures", "metadata.json")
    figures = []
    if os.path.exists(metadata_path):
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        for item in metadata:
            figures.append({
                "filename": item.get("filename", ""),
                "caption": item.get("caption", ""),
                "figure_number": item.get("figure_number", ""),
                "has_caption": True
            })
    else:
        # metadata.json 없으면 figures/ 디렉토리의 fig_*.png 파일 목록만
        fig_pattern = os.path.join(paper_dir, "figures", "fig_*.png")
        fig_files = sorted(glob.glob(fig_pattern))
        for fig_path in fig_files:
            fname = os.path.basename(fig_path)
            figures.append({
                "filename": fname,
                "caption": "",
                "figure_number": "",
                "has_caption": False
            })

    # 2. content.json에서 섹션 구조 추출 (## 헤더)
    sections = []
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            sections.append(stripped)

    # 3. 현재 figure 참조 추출
    # 패턴: ![...](figures/filename.png) 혹은 ![...](figures/filename.png) 뒤 *캡션* 형태
    existing_refs = []
    fig_ref_pattern = re.compile(r'!\[([^\]]*)\]\((figures/[^)]+\.png)\)')

    # 섹션별로 매핑
    current_section = None
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("## "):
            current_section = stripped
        matches = fig_ref_pattern.findall(line)
        for alt, path in matches:
            filename = os.path.basename(path)
            existing_refs.append({
                "filename": filename,
                "section": current_section or "## (unknown)",
                "alt": alt
            })

    return {
        "slug": slug,
        "figures": figures,
        "sections": sections,
        "existing_refs": existing_refs,
        "total_figures": len(figures),
        "total_existing_refs": len(existing_refs)
    }


def main():
    # numbered paper 디렉토리만 처리 (숫자로 시작하는 것)
    paper_dirs = sorted(glob.glob(os.path.join(PAPERS_DIR, "[0-9]*")))

    total = 0
    skipped = 0

    for paper_dir in paper_dirs:
        name = os.path.basename(paper_dir)
        result = collect_figure_info(paper_dir)

        if result is None:
            print(f"[SKIP] {name}: content.json 없음")
            skipped += 1
            continue

        # figure_reference.json 저장
        output_path = os.path.join(paper_dir, "figure_reference.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        has_meta = "✓" if result["figures"] and result["figures"][0]["has_caption"] else "○"
        print(
            f"[{has_meta}] {name}: "
            f"{result['total_figures']}개 figure, "
            f"{len(result['sections'])}개 섹션, "
            f"{result['total_existing_refs']}개 기존 참조"
        )
        total += 1

    print(f"\n완료: {total}개 논문 처리 (건너뜀: {skipped}개)")


if __name__ == "__main__":
    main()
