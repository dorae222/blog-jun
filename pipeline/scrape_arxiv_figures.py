#!/usr/bin/env python3
"""ar5iv HTML에서 논문 figure를 크롤링합니다.

PDF에서 figure 추출이 실패한(0개) 논문에 대해 ar5iv.labs.arxiv.org의
HTML 렌더링 페이지에서 figure/table 이미지를 다운로드합니다.

사용법:
  python pipeline/scrape_arxiv_figures.py --slug bert           # 단일 논문
  python pipeline/scrape_arxiv_figures.py --missing-only        # figure 0인 논문만
  python pipeline/scrape_arxiv_figures.py --all                 # 전체 재크롤링
  python pipeline/scrape_arxiv_figures.py --slug bert --tables  # 테이블도 추출

출력:
  pipeline/data/papers_written/{slug}/figures/fig_{idx}.png
  pipeline/data/papers_written/{slug}/figures/metadata.json
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ── 경로 설정 ──────────────────────────────────────────────────────────
PIPELINE_DIR = Path(__file__).resolve().parent
DATA_DIR = PIPELINE_DIR / "data"
PAPERS_DIR = DATA_DIR / "papers_written"
ARCH_DIR = DATA_DIR / "architectures_written"

# ── 상수 ───────────────────────────────────────────────────────────────
BASE_URL = "https://ar5iv.labs.arxiv.org"
RATE_LIMIT = 3  # seconds — arXiv 정책 준수
REQUEST_TIMEOUT = 30  # seconds
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


# ── arXiv ID 추출 ─────────────────────────────────────────────────────
def extract_arxiv_id(url: str) -> str | None:
    """arXiv URL에서 논문 ID를 추출한다.

    지원 형식:
      - https://arxiv.org/abs/1810.04805
      - https://arxiv.org/abs/1810.04805v1
      - https://arxiv.org/pdf/1810.04805
      - http://arxiv.org/abs/hep-th/9802150

    Returns:
        arXiv ID 문자열 (버전 번호 제거) 또는 None
    """
    if not url:
        return None

    patterns = [
        r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)',
        r'arxiv\.org/(?:abs|pdf)/([\w\-]+/\d{7}(?:v\d+)?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            # 버전 번호 제거 (v1, v2 등)
            return re.sub(r'v\d+$', '', match.group(1))
    return None


# ── 논문 메타데이터 로드 ───────────────────────────────────────────────
def load_paper_metadata(slug: str) -> dict | None:
    """slug에 해당하는 논문의 arxiv_url을 찾는다.

    두 가지 소스를 순서대로 탐색:
      1. papers_written/{*_slug 또는 slug}/content.json → arxiv_url
      2. architectures_written/{slug}/entry.json → paper_url

    Returns:
        {"slug": ..., "arxiv_url": ..., "arxiv_id": ...} 또는 None
    """
    # 1. papers_written에서 content.json 탐색 (번호 접두사 포함)
    for paper_dir in sorted(PAPERS_DIR.iterdir()):
        if not paper_dir.is_dir():
            continue
        content_path = paper_dir / "content.json"
        if not content_path.exists():
            continue
        try:
            data = json.loads(content_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("slug") == slug:
            arxiv_url = data.get("arxiv_url", "")
            arxiv_id = extract_arxiv_id(arxiv_url)
            if arxiv_id:
                return {"slug": slug, "arxiv_url": arxiv_url, "arxiv_id": arxiv_id}

    # 2. architectures_written에서 entry.json 탐색
    entry_path = ARCH_DIR / slug / "entry.json"
    if entry_path.exists():
        try:
            data = json.loads(entry_path.read_text(encoding="utf-8"))
            paper_url = data.get("paper_url", "")
            arxiv_id = extract_arxiv_id(paper_url)
            if arxiv_id:
                return {"slug": slug, "arxiv_url": paper_url, "arxiv_id": arxiv_id}
        except (json.JSONDecodeError, OSError):
            pass

    # 3. architectures_written에서 content.json 탐색 (참고 자료 섹션)
    content_path = ARCH_DIR / slug / "content.json"
    if content_path.exists():
        try:
            data = json.loads(content_path.read_text(encoding="utf-8"))
            content_text = data.get("content", "")
            # content 본문에서 arxiv URL 추출
            match = re.search(r'https?://arxiv\.org/abs/[\d.]+', content_text)
            if match:
                arxiv_url = match.group(0)
                arxiv_id = extract_arxiv_id(arxiv_url)
                if arxiv_id:
                    return {"slug": slug, "arxiv_url": arxiv_url, "arxiv_id": arxiv_id}
        except (json.JSONDecodeError, OSError):
            pass

    return None


def get_all_slugs() -> list[str]:
    """papers_written 내 모든 논문 slug를 반환한다."""
    slugs = set()
    for paper_dir in sorted(PAPERS_DIR.iterdir()):
        if not paper_dir.is_dir():
            continue
        # 번호 접두사가 있는 디렉토리에서 slug 추출
        content_path = paper_dir / "content.json"
        if content_path.exists():
            try:
                data = json.loads(content_path.read_text(encoding="utf-8"))
                s = data.get("slug")
                if s:
                    slugs.add(s)
                    continue
            except (json.JSONDecodeError, OSError):
                pass
        # content.json이 없는 경우 디렉토리명 자체가 slug
        dir_name = paper_dir.name
        # 번호 접두사 제거 (예: "2_bert" → "bert")
        if re.match(r'^\d+_', dir_name):
            dir_name = re.sub(r'^\d+_', '', dir_name)
        slugs.add(dir_name)
    return sorted(slugs)


def get_slugs_missing_figures() -> list[str]:
    """figure가 0개인 논문의 slug 목록을 반환한다.

    figures/ 디렉토리가 비어있거나 이미지 파일이 없는 경우를 탐지.
    """
    missing = []
    for paper_dir in sorted(PAPERS_DIR.iterdir()):
        if not paper_dir.is_dir():
            continue

        # slug 결정
        dir_name = paper_dir.name
        content_path = paper_dir / "content.json"
        if content_path.exists():
            try:
                data = json.loads(content_path.read_text(encoding="utf-8"))
                slug = data.get("slug", dir_name)
            except (json.JSONDecodeError, OSError):
                slug = dir_name
        else:
            # 번호 접두사 제거
            slug = re.sub(r'^\d+_', '', dir_name) if re.match(r'^\d+_', dir_name) else dir_name

        # figures 디렉토리 확인
        figures_dir = paper_dir / "figures"
        if not figures_dir.exists():
            missing.append(slug)
            continue

        # 이미지 파일 존재 여부 확인 (.png, .jpg, .jpeg, .webp, .gif)
        image_exts = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}
        has_images = any(
            f.suffix.lower() in image_exts
            for f in figures_dir.iterdir()
            if f.is_file()
        )
        if not has_images:
            missing.append(slug)

    return sorted(set(missing))


# ── ar5iv 크롤링 ──────────────────────────────────────────────────────
def scrape_figures(
    arxiv_id: str,
    slug: str,
    include_tables: bool = False,
) -> dict:
    """ar5iv HTML에서 figure (및 선택적으로 table) 이미지를 크롤링한다.

    Args:
        arxiv_id: arXiv 논문 ID (예: "1810.04805")
        slug: 논문 slug (출력 디렉토리명)
        include_tables: True이면 ltx_table도 추출

    Returns:
        {
            "slug": str,
            "arxiv_id": str,
            "status": str,
            "figures_count": int,
            "figures": [{"filename": ..., "caption": ..., "figure_number": ..., "source_url": ...}],
        }
    """
    result = {
        "slug": slug,
        "arxiv_id": arxiv_id,
        "status": "pending",
        "figures_count": 0,
        "figures": [],
    }

    html_url = f"{BASE_URL}/html/{arxiv_id}"
    print(f"\n{'='*60}")
    print(f"[{slug}] ar5iv 크롤링: {html_url}")
    print(f"{'='*60}")

    # 1. HTML 페이지 가져오기
    try:
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(html_url, headers=headers, timeout=REQUEST_TIMEOUT)
        if resp.status_code == 404:
            print(f"  [WARN] ar5iv 페이지 없음 (404): {html_url}")
            result["status"] = "not_found"
            return result
        resp.raise_for_status()
        print(f"  HTML 로드 완료 ({len(resp.text):,} bytes)")
    except requests.RequestException as e:
        print(f"  [ERROR] HTML 요청 실패: {e}")
        result["status"] = "request_error"
        return result

    # 2. BeautifulSoup 파싱
    soup = BeautifulSoup(resp.text, "html.parser")

    # 3. figure 요소 추출
    selectors = ["figure.ltx_figure"]
    if include_tables:
        selectors.append("figure.ltx_table")

    figure_elements = []
    for selector in selectors:
        figure_elements.extend(soup.select(selector))

    if not figure_elements:
        # 폴백: 일부 논문은 클래스명이 다를 수 있음
        figure_elements = soup.find_all("figure")

    print(f"  발견된 figure 요소: {len(figure_elements)}개")

    if not figure_elements:
        result["status"] = "no_figures"
        return result

    # 4. 출력 디렉토리 생성
    # slug에 해당하는 디렉토리 찾기 (번호 접두사 포함 가능)
    figures_dir = _resolve_figures_dir(slug)
    figures_dir.mkdir(parents=True, exist_ok=True)

    # 5. 각 figure에서 이미지 추출 및 다운로드
    downloaded = 0
    metadata_list = []

    for fig_idx, figure in enumerate(figure_elements, 1):
        # 캡션 추출
        figcaption = figure.find("figcaption")
        caption_text = ""
        if figcaption:
            caption_text = figcaption.get_text(separator=" ", strip=True)

        # figure 번호 추출 (예: "Figure 1:", "Table 2:")
        figure_number = ""
        if caption_text:
            num_match = re.match(
                r'((?:Figure|Fig\.|Table)\s*\d+)', caption_text, re.IGNORECASE
            )
            if num_match:
                figure_number = num_match.group(1)

        # 이미지 태그 찾기
        img_tags = figure.find_all("img")
        if not img_tags:
            print(f"  [fig_{fig_idx}] 이미지 태그 없음, 건너뜀")
            continue

        for img_sub_idx, img in enumerate(img_tags):
            src = img.get("src", "")
            if not src:
                continue

            # 상대 URL을 절대 URL로 변환
            img_url = urljoin(html_url + "/", src)

            # data: URI는 건너뜀
            if src.startswith("data:"):
                continue

            # 이미지 다운로드
            try:
                img_resp = requests.get(
                    img_url, headers=headers, timeout=REQUEST_TIMEOUT
                )
                img_resp.raise_for_status()
            except requests.RequestException as e:
                print(f"  [fig_{fig_idx}] 이미지 다운로드 실패: {e}")
                continue

            # 파일 확장자 결정
            content_type = img_resp.headers.get("Content-Type", "")
            if "png" in content_type or src.endswith(".png"):
                ext = "png"
            elif "jpeg" in content_type or "jpg" in content_type or src.endswith((".jpg", ".jpeg")):
                ext = "jpg"
            elif "svg" in content_type or src.endswith(".svg"):
                ext = "svg"
            elif "gif" in content_type or src.endswith(".gif"):
                ext = "gif"
            elif "webp" in content_type or src.endswith(".webp"):
                ext = "webp"
            else:
                ext = "png"  # 기본값

            # 파일명 결정
            if len(img_tags) > 1:
                filename = f"fig_{fig_idx}_{img_sub_idx + 1}.{ext}"
            else:
                filename = f"fig_{fig_idx}.{ext}"

            # 저장
            fig_path = figures_dir / filename
            fig_path.write_bytes(img_resp.content)
            downloaded += 1

            file_size_kb = len(img_resp.content) / 1024
            print(f"  [{filename}] {file_size_kb:.1f}KB ← {src}")

            metadata_list.append({
                "filename": filename,
                "caption": caption_text,
                "figure_number": figure_number,
                "source_url": img_url,
            })

    # 6. 메타데이터 저장
    if metadata_list:
        meta_path = figures_dir / "metadata.json"
        meta_path.write_text(
            json.dumps(metadata_list, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\n  메타데이터 저장: {meta_path}")

    result["figures_count"] = downloaded
    result["figures"] = metadata_list
    result["status"] = "success" if downloaded > 0 else "no_images"
    print(f"\n  총 {downloaded}개 이미지 다운로드 완료")
    print(f"  저장 위치: {figures_dir}")

    return result


def _resolve_figures_dir(slug: str) -> Path:
    """slug에 해당하는 figures 디렉토리 경로를 반환한다.

    번호 없는 디렉토리(예: papers_written/bert/)를 우선하고,
    없으면 번호 있는 디렉토리(예: papers_written/2_bert/)를 사용.
    둘 다 없으면 slug 이름으로 새로 생성.
    """
    # 1. 번호 없는 디렉토리
    plain_dir = PAPERS_DIR / slug / "figures"
    if (PAPERS_DIR / slug).exists():
        return plain_dir

    # 2. 번호 있는 디렉토리 탐색
    for paper_dir in PAPERS_DIR.iterdir():
        if not paper_dir.is_dir():
            continue
        match = re.match(r'^\d+_(.+)$', paper_dir.name)
        if match and match.group(1) == slug:
            return paper_dir / "figures"

    # 3. 새 디렉토리 생성
    return plain_dir


# ── 메인 처리 로직 ────────────────────────────────────────────────────
def process_slugs(
    slugs: list[str],
    include_tables: bool = False,
) -> list[dict]:
    """slug 목록을 순회하며 ar5iv에서 figure를 크롤링한다.

    Args:
        slugs: 처리할 slug 목록
        include_tables: True이면 테이블도 추출

    Returns:
        결과 리스트
    """
    results = []
    total = len(slugs)

    for idx, slug in enumerate(slugs, 1):
        print(f"\n[{idx}/{total}] {slug} 처리 중...")

        # 메타데이터에서 arxiv_id 추출
        meta = load_paper_metadata(slug)
        if not meta:
            print(f"  [WARN] arxiv URL을 찾을 수 없음: {slug}")
            results.append({
                "slug": slug,
                "status": "no_arxiv_url",
                "figures_count": 0,
            })
            continue

        arxiv_id = meta["arxiv_id"]
        print(f"  arXiv ID: {arxiv_id}")

        # 크롤링 실행
        result = scrape_figures(
            arxiv_id=arxiv_id,
            slug=slug,
            include_tables=include_tables,
        )
        results.append(result)

        # arXiv 속도 제한 준수
        if idx < total:
            print(f"\n  (속도 제한 대기: {RATE_LIMIT}초)")
            time.sleep(RATE_LIMIT)

    return results


# ── 결과 요약 ─────────────────────────────────────────────────────────
def print_summary(results: list[dict]) -> None:
    """처리 결과를 요약 출력한다."""
    print(f"\n{'='*60}")
    print("크롤링 결과 요약")
    print(f"{'='*60}")

    status_counts: dict[str, int] = {}
    total_figures = 0

    for r in results:
        status = r.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        total_figures += r.get("figures_count", 0)

    print(f"  전체 처리: {len(results)}건")
    status_labels = {
        "success": "성공",
        "no_figures": "HTML에 figure 없음",
        "no_images": "figure 내 이미지 없음",
        "not_found": "ar5iv 페이지 없음 (404)",
        "request_error": "요청 실패",
        "no_arxiv_url": "arXiv URL 없음",
    }
    for status, count in sorted(status_counts.items()):
        label = status_labels.get(status, status)
        print(f"    {label}: {count}건")

    print(f"  총 다운로드 이미지: {total_figures}개")

    # 성공한 논문 목록
    successes = [r for r in results if r.get("figures_count", 0) > 0]
    if successes:
        print(f"\n  성공 ({len(successes)}건):")
        for r in successes:
            print(f"    - {r['slug']}: {r['figures_count']}개")

    # 실패한 논문 목록
    failures = [r for r in results if r.get("status") not in ("success",) and r.get("figures_count", 0) == 0]
    if failures:
        print(f"\n  실패/건너뜀 ({len(failures)}건):")
        for r in failures:
            print(f"    - {r['slug']}: {status_labels.get(r.get('status', ''), r.get('status', ''))}")


# ── CLI 엔트리포인트 ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="ar5iv HTML에서 논문 figure를 크롤링합니다.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python pipeline/scrape_arxiv_figures.py --slug bert           # 단일 논문
  python pipeline/scrape_arxiv_figures.py --missing-only        # figure 0인 논문만
  python pipeline/scrape_arxiv_figures.py --all                 # 전체 재크롤링
  python pipeline/scrape_arxiv_figures.py --slug bert --tables  # 테이블도 추출
        """,
    )

    # 처리 범위 (상호 배타적)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--slug",
        type=str,
        help="특정 slug의 논문만 크롤링",
    )
    scope.add_argument(
        "--missing-only",
        action="store_true",
        help="figure가 0개인 논문만 크롤링",
    )
    scope.add_argument(
        "--all",
        action="store_true",
        help="전체 논문 재크롤링",
    )

    # 추가 옵션
    parser.add_argument(
        "--tables",
        action="store_true",
        help="테이블(ltx_table)도 함께 추출",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 다운로드 없이 대상 논문만 확인",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("ar5iv Figure 크롤러")
    print("=" * 60)

    # 대상 slug 결정
    if args.slug:
        slugs = [args.slug]
    elif args.missing_only:
        slugs = get_slugs_missing_figures()
        print(f"\nfigure 0개인 논문: {len(slugs)}건")
    else:  # --all
        slugs = get_all_slugs()
        print(f"\n전체 논문: {len(slugs)}건")

    if not slugs:
        print("\n[INFO] 처리할 논문이 없습니다.")
        return

    # 대상 목록 출력
    print(f"\n처리 대상 ({len(slugs)}건):")
    for s in slugs:
        meta = load_paper_metadata(s)
        arxiv_id = meta["arxiv_id"] if meta else "???"
        print(f"  - {s} (arXiv: {arxiv_id})")

    if args.dry_run:
        print("\n[DRY-RUN] 실제 크롤링 없이 종료합니다.")
        return

    # 크롤링 실행
    results = process_slugs(slugs, include_tables=args.tables)

    # 결과 요약
    print_summary(results)

    # 결과 리포트 저장
    report_path = DATA_DIR / "ar5iv_scrape_report.json"
    report_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\n결과 리포트 저장: {report_path}")


if __name__ == "__main__":
    main()
