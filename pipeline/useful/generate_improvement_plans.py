#!/usr/bin/env python3
"""
각 논문별 컨텐츠 개선 계획(improvement_plan)을 content_index.json에 추가

계획 내용:
- priority 1: content 있음 + metadata.json 있음 + 미참조 figure > 0 (즉시 실행 가능)
- priority 2: content 있음 + metadata.json 없음 + arxiv_url 있음 (scrape 후 실행)
- priority 3: content 있음 + 미참조 figure 0개 (컨텐츠 개선만 필요)
- priority 4: content 없음 + figures 많음
- priority 5: content 없음 + figures 적음

figure→section 매핑: caption_en 키워드 기반 (LLM 없음)
"""
import json
import re
from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PIPELINE_DIR / "data"
CONTENT_INDEX_PATH = DATA_DIR / "blog-jun-content.json"

# architecture 파일 제외 패턴
ARCH_FILENAMES = {"architecture.png", "architecture.svg"}

# figure→섹션 카테고리별 키워드
SECTION_KEYWORDS = {
    "실험": [
        "result", "experiment", "performance", "benchmark", "comparison",
        "ablation", "evaluation", "score", "accuracy", "metric", "baseline",
        "table", "improvement", "sota", "state-of-the-art",
    ],
    "방법": [
        "architecture", "framework", "model", "method", "approach",
        "design", "pipeline", "structure", "overview", "proposed",
        "workflow", "diagram", "illustration", "schematic",
    ],
    "배경": [
        "background", "related", "prior", "preliminary", "motivation",
        "existing", "previous",
    ],
    "훈련": [
        "training", "loss", "convergence", "optimization", "learning curve",
        "epoch", "gradient", "schedule",
    ],
}

# 섹션 이름 → 카테고리 매핑 (한국어 섹션 헤더)
SECTION_CATEGORY_HINTS = {
    "실험": ["실험", "결과", "평가", "성능", "비교", "분석", "ablation"],
    "방법": ["방법", "아키텍처", "모델", "구조", "제안", "접근", "기법", "설계"],
    "배경": ["배경", "관련", "선행", "기존", "관련 연구"],
    "훈련": ["훈련", "학습", "최적화", "손실"],
    "개요": ["개요", "소개", "서론", "introduction", "overview"],
}


def classify_caption(caption_en: str) -> str | None:
    """caption_en 키워드 기반으로 섹션 카테고리 반환."""
    if not caption_en:
        return None
    lower = caption_en.lower()
    for category, keywords in SECTION_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return category
    return None


def find_best_section(category: str, sections: list[str]) -> str | None:
    """카테고리에 맞는 최적 섹션 헤더 선택."""
    if not sections:
        return None
    hints = SECTION_CATEGORY_HINTS.get(category, [])
    for section in sections:
        lower = section.lower()
        if any(h in lower for h in hints):
            return section
    return None


def get_default_section(sections: list[str]) -> str | None:
    """기본 섹션: 방법론 계열 섹션 중 첫 번째."""
    for section in sections:
        lower = section.lower()
        if any(h in lower for h in SECTION_CATEGORY_HINTS["방법"]):
            return section
    # 방법론 없으면 두 번째 섹션 (개요 다음)
    if len(sections) >= 2:
        return sections[1]
    return sections[0] if sections else None


def generate_plan(paper: dict) -> dict:
    """단일 논문에 대한 improvement_plan 생성."""
    has_content = paper.get("has_content", False)
    sections = paper.get("sections", [])
    figs = paper["figures"]
    items = figs.get("items", [])
    has_metadata = figs.get("has_metadata_json", False)
    arxiv_url = paper.get("paper_source", {}).get("arxiv_url") or paper.get("arxiv_url")
    total_available = figs.get("total_available", 0)

    # architecture 파일 제외한 실제 figure 목록
    real_items = [f for f in items if f["filename"].lower() not in ARCH_FILENAMES]
    unreferenced = [f for f in real_items if not f.get("referenced_in_content", False)]
    unreferenced_count = len(unreferenced)

    has_arch = any(f["filename"].lower() in ARCH_FILENAMES for f in items)

    notes = []
    if has_arch:
        notes.append("architecture.png/svg 파일 존재 (UI 표시용, 삽입 계획 제외)")

    # priority 및 type 결정
    if not has_content:
        plan_type = "write_content"
        priority = 4 if total_available >= 3 else 5
        summary = f"컨텐츠 없음. figure {total_available}개 보유. 컨텐츠 작성 후 figure 삽입 필요."
        return {
            "status": "pending",
            "priority": priority,
            "type": plan_type,
            "summary": summary,
            "needs_metadata_scrape": False,
            "unreferenced_count": unreferenced_count,
            "figure_insertions": [],
            "sections_without_figures": [],
            "notes": notes,
        }

    # content 있는 경우
    if unreferenced_count == 0:
        plan_type = "figure_insertion"
        priority = 3
        summary = "figure 모두 참조됨. 컨텐츠 품질 개선 검토 필요."
        return {
            "status": "pending",
            "priority": priority,
            "type": plan_type,
            "summary": summary,
            "needs_metadata_scrape": not has_metadata and bool(arxiv_url),
            "unreferenced_count": 0,
            "figure_insertions": [],
            "sections_without_figures": [],
            "notes": notes,
        }

    # 미참조 figure 있는 경우
    if has_metadata:
        priority = 1
        plan_type = "figure_insertion"
    elif arxiv_url:
        priority = 2
        plan_type = "metadata_scrape_needed"
    else:
        priority = 2
        plan_type = "figure_insertion"

    # figure_insertions 상한: 섹션 수의 2배 또는 최소 10, 최대 20
    max_insertions = max(min(len(sections) * 2, 20), 10)

    # figure → section 매핑
    figure_insertions = []
    section_usage: dict[str, int] = {}  # 섹션별 배치 수

    for fig in unreferenced[:max_insertions]:
        fname = fig["filename"]
        caption_en = fig.get("caption_en", "")
        source_url = fig.get("source_url")

        # 카테고리 분류
        category = classify_caption(caption_en)

        if category and sections:
            suggested = find_best_section(category, sections)
            mapping_basis = "keyword_match"
        else:
            suggested = get_default_section(sections)
            mapping_basis = "position"

        if suggested is None and sections:
            suggested = sections[0]
            mapping_basis = "position"

        # 섹션 내 몇 번째 문단 뒤에 배치할지 (연속 배치 시 순서 증가)
        after_nth = section_usage.get(suggested, 0) + 1
        # 한 섹션에 3개 이상 몰리면 after_nth 증가로 분산
        after_nth_adjusted = min(after_nth, 3)
        section_usage[suggested] = section_usage.get(suggested, 0) + 1

        entry = {
            "filename": fname,
            "caption_en": caption_en,
            "source_url": source_url,
            "suggested_section": suggested,
            "after_nth_paragraph": after_nth_adjusted,
            "mapping_basis": mapping_basis,
        }
        figure_insertions.append(entry)

    # 섹션별 figure 보유 현황
    sections_with_figs = set()
    for f in real_items:
        if f.get("referenced_in_content") and f.get("section"):
            sections_with_figs.add(f["section"])
    sections_without_figures = [s for s in sections if s not in sections_with_figs
                                  and "개요" not in s.lower() and "관련" not in s.lower()]

    n_insertions = len(figure_insertions)
    summary = (
        f"{unreferenced_count}개 미삽입 figure 중 {n_insertions}개 섹션 배치 계획"
        + (" (metadata 크롤링 선행 필요)" if plan_type == "metadata_scrape_needed" else "")
    )

    return {
        "status": "pending",
        "priority": priority,
        "type": plan_type,
        "summary": summary,
        "needs_metadata_scrape": plan_type == "metadata_scrape_needed",
        "unreferenced_count": unreferenced_count,
        "figure_insertions": figure_insertions,
        "sections_without_figures": sections_without_figures,
        "notes": notes,
    }


def main():
    print("content_index.json 읽는 중...")
    data = json.loads(CONTENT_INDEX_PATH.read_text(encoding="utf-8"))
    papers = data["papers"]

    priority_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    total_insertions = 0

    for paper in papers:
        plan = generate_plan(paper)
        paper["improvement_plan"] = plan
        priority_counts[plan["priority"]] = priority_counts.get(plan["priority"], 0) + 1
        total_insertions += len(plan.get("figure_insertions", []))

    # 저장
    CONTENT_INDEX_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"✓ improvement_plan 추가 완료: {CONTENT_INDEX_PATH}")
    print(f"  총 논문: {len(papers)}개")
    for pr in sorted(priority_counts):
        labels = {
            1: "즉시 실행 가능 (content + metadata + 미참조 figure)",
            2: "scrape/figure 배치 필요",
            3: "figure 모두 참조됨",
            4: "컨텐츠 없음 (figures 3개+)",
            5: "컨텐츠 없음 (figures 적음)",
        }
        print(f"  Priority {pr} ({labels[pr]}): {priority_counts[pr]}개")
    print(f"  총 figure 삽입 계획: {total_insertions}개")

    p1_papers = [p for p in papers if p["improvement_plan"]["priority"] == 1]
    if p1_papers:
        print(f"\nPriority 1 논문 ({len(p1_papers)}개):")
        for p in sorted(p1_papers, key=lambda x: -x["improvement_plan"]["unreferenced_count"])[:10]:
            plan = p["improvement_plan"]
            print(f"  {p['slug']}: {plan['unreferenced_count']}개 미참조, {len(plan['figure_insertions'])}개 삽입 계획")


if __name__ == "__main__":
    main()
