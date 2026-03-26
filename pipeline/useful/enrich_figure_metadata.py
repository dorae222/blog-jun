#!/usr/bin/env python3
"""
metadata.json 없는 논문에 대해 ar5iv 크롤링으로 figure 메타데이터 보강

대상: content_index.json에서 has_metadata_json=False이고 arxiv_url이 있는 논문
처리: scrape_arxiv_figures.scrape_figures() 재사용하여 metadata.json 생성
출력: pipeline/data/ar5iv_enrich_report.json
"""
import json
import sys
import time
from pathlib import Path

# pipeline 루트를 sys.path에 추가 (scrape_arxiv_figures import용)
PIPELINE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PIPELINE_DIR))

from scrape_arxiv_figures import scrape_figures, extract_arxiv_id

DATA_DIR = PIPELINE_DIR / "data"
CONTENT_INDEX_PATH = DATA_DIR / "blog-jun-content.json"
REPORT_PATH = DATA_DIR / "ar5iv_enrich_report.json"

RATE_LIMIT = 3  # seconds


def main():
    # content_index.json 읽기
    print("content_index.json 읽는 중...")
    idx = json.loads(CONTENT_INDEX_PATH.read_text(encoding="utf-8"))
    papers = idx["papers"]

    # 대상 필터: metadata.json 없음 + arxiv_url 있음
    targets = []
    for p in papers:
        if p["figures"]["has_metadata_json"]:
            continue
        arxiv_url = p.get("paper_source", {}).get("arxiv_url") or p.get("arxiv_url")
        if not arxiv_url:
            continue
        arxiv_id = extract_arxiv_id(arxiv_url)
        if not arxiv_id:
            continue
        targets.append({
            "slug": p["slug"],
            "arxiv_url": arxiv_url,
            "arxiv_id": arxiv_id,
        })

    print(f"대상 논문: {len(targets)}개 (전체 {len(papers)}개 중 metadata.json 없음)")

    if not targets:
        print("처리할 논문이 없습니다.")
        return

    # 각 논문 처리
    results = []
    total = len(targets)

    for idx_num, t in enumerate(targets, 1):
        slug = t["slug"]
        arxiv_id = t["arxiv_id"]

        print(f"\n[{idx_num}/{total}] {slug} (arXiv: {arxiv_id})")

        result = scrape_figures(arxiv_id=arxiv_id, slug=slug, include_tables=False)
        result["slug"] = slug
        result["arxiv_url"] = t["arxiv_url"]
        results.append(result)

        if idx_num < total:
            print(f"  (속도 제한 대기: {RATE_LIMIT}초)")
            time.sleep(RATE_LIMIT)

    # 결과 요약
    success = [r for r in results if r.get("figures_count", 0) > 0]
    not_found = [r for r in results if r.get("status") == "not_found"]
    failed = [r for r in results if r.get("status") in ("request_error", "no_images", "no_figures")]
    no_url = [r for r in results if r.get("status") == "no_arxiv_url"]

    total_new_figures = sum(r.get("figures_count", 0) for r in results)

    print(f"\n{'='*60}")
    print("보강 결과 요약")
    print(f"{'='*60}")
    print(f"  처리 논문: {total}개")
    print(f"  성공 (새 metadata.json 생성): {len(success)}개")
    print(f"  ar5iv 페이지 없음 (404):       {len(not_found)}개")
    print(f"  기타 실패:                      {len(failed)}개")
    print(f"  총 새로 다운로드된 figure:       {total_new_figures}개")

    if success:
        print(f"\n  성공 논문:")
        for r in success:
            print(f"    - {r['slug']}: {r['figures_count']}개 figure")

    if not_found:
        print(f"\n  ar5iv 없는 논문 (404):")
        for r in not_found:
            print(f"    - {r['slug']}")

    # 리포트 저장
    REPORT_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n리포트 저장: {REPORT_PATH}")
    print("\n다음 단계: python3 pipeline/useful/build_content_index.py")


if __name__ == "__main__":
    main()
