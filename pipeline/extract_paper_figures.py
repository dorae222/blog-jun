#!/usr/bin/env python3
"""
Phase D: 논문 PDF에서 figure 이미지 추출 (arXiv 기반)

ArchitectureEntry의 paper_url에서 arXiv ID를 추출하고,
arxiv 라이브러리로 PDF를 다운로드한 뒤 PyMuPDF(fitz)로 이미지를 추출한다.

사용법:
  python extract_paper_figures.py --arxiv-only          # arXiv URL만 처리
  python extract_paper_figures.py --all                  # 전체 paper_url 처리
  python extract_paper_figures.py --slug gpt-4           # 특정 slug만
  python extract_paper_figures.py --metadata             # 메타데이터만 업데이트
  python extract_paper_figures.py --dry-run              # 미리보기
  python extract_paper_figures.py --slug bert --dry-run  # 특정 slug 미리보기

출력 디렉토리:
  pipeline/data/papers_written/{slug}/figures/
"""
import argparse
import json
import os
import re
import sys
import time
import tempfile
import shutil
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────────────────────────────
PIPELINE_DIR = Path(__file__).resolve().parent
DATA_DIR = PIPELINE_DIR / "data"
ARCH_DIR = DATA_DIR / "architectures_written"
PAPERS_DIR = DATA_DIR / "papers_written"
BACKEND_DIR = PIPELINE_DIR.parent / "backend"

# ── 이미지 필터 기준 ──────────────────────────────────────────────────
MIN_WIDTH = 200       # px
MIN_HEIGHT = 200      # px
MIN_FILE_SIZE = 10240  # 10KB (bytes)

# ── arXiv 속도 제한 ───────────────────────────────────────────────────
ARXIV_DELAY = 3  # arXiv API 호출 간 최소 대기 시간 (초)


# ── arXiv ID 추출 ─────────────────────────────────────────────────────
def extract_arxiv_id(url: str) -> str | None:
    """
    arXiv URL에서 논문 ID를 추출한다.

    지원 형식:
      - https://arxiv.org/abs/1706.03762
      - https://arxiv.org/abs/1706.03762v1
      - https://arxiv.org/pdf/1706.03762
      - https://arxiv.org/pdf/1706.03762v2
      - http://arxiv.org/abs/1706.03762

    Returns:
        arXiv ID 문자열 또는 None (파싱 실패 시)
    """
    if not url:
        return None

    # 새 형식: YYMM.NNNNN (또는 YYMM.NNNNNvN)
    # 구 형식: category/NNNNNNN (예: hep-th/9802150)
    patterns = [
        r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)',
        r'arxiv\.org/(?:abs|pdf)/([\w\-]+/\d{7}(?:v\d+)?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            # 버전 번호 제거 (v1, v2 등)
            arxiv_id = re.sub(r'v\d+$', '', match.group(1))
            return arxiv_id
    return None


# ── Django DB에서 엔트리 로드 ─────────────────────────────────────────
def load_entries_from_db(slug_filter: str | None = None,
                         arxiv_only: bool = False) -> list[dict]:
    """
    Django DB의 ArchitectureEntry에서 paper_url이 있는 레코드를 로드한다.

    Args:
        slug_filter: 특정 slug만 필터링 (None이면 전체)
        arxiv_only: True이면 arXiv URL만 포함

    Returns:
        [{"slug": ..., "name": ..., "paper_url": ..., "arxiv_id": ...}, ...]
    """
    try:
        sys.path.insert(0, str(BACKEND_DIR))
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
        import django
        django.setup()
        from blog.models import ArchitectureEntry

        qs = ArchitectureEntry.objects.exclude(paper_url="")
        if slug_filter:
            qs = qs.filter(slug=slug_filter)

        entries = []
        for entry in qs.iterator():
            arxiv_id = extract_arxiv_id(entry.paper_url)
            if arxiv_only and not arxiv_id:
                continue
            entries.append({
                "slug": entry.slug,
                "name": entry.name,
                "paper_url": entry.paper_url,
                "arxiv_id": arxiv_id,
            })
        print(f"[DB] ArchitectureEntry {len(entries)}건 로드 완료")
        return entries

    except Exception as e:
        print(f"[WARN] Django DB 접속 실패: {e}")
        print("[FALLBACK] JSON 파일에서 로드합니다...")
        return load_entries_from_json(slug_filter, arxiv_only)


# ── JSON 파일 폴백 로드 ───────────────────────────────────────────────
def load_entries_from_json(slug_filter: str | None = None,
                           arxiv_only: bool = False) -> list[dict]:
    """
    Django 없이 data/architectures_written/*/entry.json에서 엔트리를 로드한다.
    독립 실행(standalone) 모드에서 사용.

    Args:
        slug_filter: 특정 slug만 필터링
        arxiv_only: True이면 arXiv URL만 포함

    Returns:
        [{"slug": ..., "name": ..., "paper_url": ..., "arxiv_id": ...}, ...]
    """
    entries = []
    if not ARCH_DIR.exists():
        print(f"[ERROR] 아키텍처 디렉토리 없음: {ARCH_DIR}")
        return entries

    # slug 필터가 지정된 경우 해당 디렉토리만 탐색
    if slug_filter:
        dirs = [ARCH_DIR / slug_filter]
    else:
        dirs = sorted(ARCH_DIR.iterdir())

    for entry_dir in dirs:
        if not entry_dir.is_dir():
            continue
        json_path = entry_dir / "entry.json"
        if not json_path.exists():
            continue
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"  [WARN] JSON 읽기 실패: {json_path} ({e})")
            continue

        paper_url = data.get("paper_url", "")
        if not paper_url:
            continue

        arxiv_id = extract_arxiv_id(paper_url)
        if arxiv_only and not arxiv_id:
            continue

        entries.append({
            "slug": data.get("slug", entry_dir.name),
            "name": data.get("name", entry_dir.name),
            "paper_url": paper_url,
            "arxiv_id": arxiv_id,
        })

    print(f"[JSON] entry.json {len(entries)}건 로드 완료")
    return entries


# ── PDF 다운로드 및 이미지 추출 ───────────────────────────────────────
def download_and_extract(slug: str, arxiv_id: str, output_dir: Path,
                         dry_run: bool = False) -> dict:
    """
    arXiv에서 PDF를 다운로드하고 PyMuPDF로 이미지를 추출한다.

    Args:
        slug: 아키텍처 슬러그 (출력 디렉토리명)
        arxiv_id: arXiv 논문 ID (예: "1706.03762")
        output_dir: 이미지 저장 기본 디렉토리 (papers_written/{slug}/figures/)
        dry_run: True이면 실제 다운로드/추출 없이 정보만 출력

    Returns:
        결과 딕셔너리 {"slug", "arxiv_id", "status", "figures_count", "metadata"}
    """
    import arxiv
    import fitz  # PyMuPDF

    result = {
        "slug": slug,
        "arxiv_id": arxiv_id,
        "status": "pending",
        "figures_count": 0,
        "metadata": {},
    }

    # 1. arXiv 메타데이터 조회
    print(f"\n{'='*60}")
    print(f"[{slug}] arXiv ID: {arxiv_id}")
    print(f"{'='*60}")

    try:
        search = arxiv.Search(id_list=[arxiv_id])
        client = arxiv.Client()
        papers = list(client.results(search))
        if not papers:
            print(f"  [ERROR] arXiv에서 논문을 찾을 수 없음: {arxiv_id}")
            result["status"] = "not_found"
            return result

        paper = papers[0]
        result["metadata"] = {
            "title": paper.title,
            "authors": [a.name for a in paper.authors[:5]],
            "published": paper.published.strftime("%Y-%m-%d") if paper.published else "",
            "updated": paper.updated.strftime("%Y-%m-%d") if paper.updated else "",
            "categories": paper.categories,
            "pdf_url": paper.pdf_url,
        }
        print(f"  제목: {paper.title}")
        print(f"  저자: {', '.join(a.name for a in paper.authors[:3])} et al.")
        print(f"  발행: {paper.published.strftime('%Y-%m-%d') if paper.published else 'N/A'}")

    except Exception as e:
        print(f"  [ERROR] arXiv 메타데이터 조회 실패: {e}")
        result["status"] = "metadata_error"
        return result

    if dry_run:
        print(f"  [DRY-RUN] PDF 다운로드 및 이미지 추출 건너뜀")
        result["status"] = "dry_run"
        return result

    # 2. PDF 다운로드 (임시 디렉토리 사용)
    tmp_dir = Path(tempfile.mkdtemp(prefix="arxiv_"))
    pdf_path = tmp_dir / f"{arxiv_id.replace('/', '_')}.pdf"

    try:
        print(f"  PDF 다운로드 중...")
        paper.download_pdf(dirpath=str(tmp_dir), filename=pdf_path.name)
        if not pdf_path.exists():
            print(f"  [ERROR] PDF 다운로드 실패: 파일이 생성되지 않음")
            result["status"] = "download_error"
            return result
        pdf_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        print(f"  PDF 다운로드 완료: {pdf_size_mb:.1f} MB")

    except Exception as e:
        print(f"  [ERROR] PDF 다운로드 실패: {e}")
        result["status"] = "download_error"
        return result

    # 3. PyMuPDF로 이미지 추출
    try:
        figures_dir = output_dir / slug / "figures"
        figures_dir.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(str(pdf_path))
        total_pages = len(doc)
        print(f"  PDF 페이지 수: {total_pages}")

        extracted = 0
        skipped = 0

        for page_idx in range(total_pages):
            page = doc[page_idx]
            images = page.get_images(full=True)

            for img_idx, img_info in enumerate(images):
                xref = img_info[0]

                try:
                    base_image = doc.extract_image(xref)
                except Exception:
                    skipped += 1
                    continue

                if not base_image:
                    skipped += 1
                    continue

                img_bytes = base_image["image"]
                img_ext = base_image.get("ext", "png")
                width = base_image.get("width", 0)
                height = base_image.get("height", 0)

                # 필터: 크기 및 파일 사이즈 기준
                if width < MIN_WIDTH or height < MIN_HEIGHT:
                    skipped += 1
                    continue
                if len(img_bytes) < MIN_FILE_SIZE:
                    skipped += 1
                    continue

                # 파일 저장
                fig_name = f"p{page_idx + 1:02d}_fig{img_idx + 1:02d}.{img_ext}"
                fig_path = figures_dir / fig_name
                fig_path.write_bytes(img_bytes)
                extracted += 1
                print(f"    [{fig_name}] {width}x{height}, "
                      f"{len(img_bytes) / 1024:.1f}KB")

        doc.close()
        result["figures_count"] = extracted
        result["status"] = "success"
        print(f"  추출 완료: {extracted}개 figure 저장, {skipped}개 스킵됨")
        print(f"  저장 위치: {figures_dir}")

    except Exception as e:
        print(f"  [ERROR] 이미지 추출 실패: {e}")
        result["status"] = "extraction_error"

    finally:
        # 임시 PDF 정리
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return result


# ── 메타데이터만 업데이트 ─────────────────────────────────────────────
def update_metadata_only(entries: list[dict], dry_run: bool = False) -> list[dict]:
    """
    arXiv 메타데이터만 조회해서 entry.json에 추가 정보를 기록한다.
    이미지 추출은 수행하지 않는다.

    Args:
        entries: 엔트리 목록
        dry_run: True이면 파일 수정 없이 미리보기

    Returns:
        결과 리스트
    """
    import arxiv

    results = []
    total = len(entries)

    for idx, entry in enumerate(entries, 1):
        slug = entry["slug"]
        arxiv_id = entry.get("arxiv_id")

        if not arxiv_id:
            print(f"  [{idx}/{total}] {slug}: arXiv ID 없음, 건너뜀")
            continue

        print(f"\n[{idx}/{total}] {slug} (arXiv: {arxiv_id})")

        try:
            search = arxiv.Search(id_list=[arxiv_id])
            client = arxiv.Client()
            papers = list(client.results(search))
            if not papers:
                print(f"  논문 찾을 수 없음")
                results.append({"slug": slug, "status": "not_found"})
                continue

            paper = papers[0]
            metadata = {
                "arxiv_title": paper.title,
                "arxiv_authors": [a.name for a in paper.authors[:10]],
                "arxiv_published": paper.published.strftime("%Y-%m-%d") if paper.published else "",
                "arxiv_categories": paper.categories,
                "arxiv_pdf_url": paper.pdf_url,
            }
            print(f"  제목: {paper.title}")

            if not dry_run:
                # entry.json 업데이트
                entry_path = ARCH_DIR / slug / "entry.json"
                if entry_path.exists():
                    data = json.loads(entry_path.read_text(encoding="utf-8"))
                    data.update(metadata)
                    entry_path.write_text(
                        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    print(f"  entry.json 업데이트 완료")
                else:
                    print(f"  [WARN] entry.json 없음: {entry_path}")
            else:
                print(f"  [DRY-RUN] entry.json 업데이트 건너뜀")

            results.append({"slug": slug, "status": "success", "metadata": metadata})

        except Exception as e:
            print(f"  [ERROR] 메타데이터 조회 실패: {e}")
            results.append({"slug": slug, "status": "error", "error": str(e)})

        # arXiv 속도 제한 준수
        if idx < total:
            print(f"  (arXiv 속도 제한 대기: {ARXIV_DELAY}초)")
            time.sleep(ARXIV_DELAY)

    return results


# ── 메인 처리 루프 ────────────────────────────────────────────────────
def process_entries(entries: list[dict], dry_run: bool = False) -> list[dict]:
    """
    엔트리 목록을 순회하며 PDF 다운로드 및 이미지 추출을 수행한다.

    Args:
        entries: 엔트리 목록
        dry_run: True이면 실제 다운로드/추출 없이 미리보기

    Returns:
        결과 리스트
    """
    results = []
    total = len(entries)

    for idx, entry in enumerate(entries, 1):
        slug = entry["slug"]
        arxiv_id = entry.get("arxiv_id")

        print(f"\n[{idx}/{total}] {slug}")

        if not arxiv_id:
            print(f"  arXiv ID 없음 (paper_url: {entry.get('paper_url', '')})")
            print(f"  arXiv URL이 아닌 경우 수동 다운로드가 필요합니다.")
            results.append({
                "slug": slug,
                "status": "skipped_no_arxiv",
                "paper_url": entry.get("paper_url", ""),
            })
            continue

        # 이미 figure가 있는 경우 건너뜀
        existing_dir = PAPERS_DIR / slug / "figures"
        if existing_dir.exists() and any(existing_dir.iterdir()):
            existing_count = len(list(existing_dir.glob("*.png")) +
                                 list(existing_dir.glob("*.jpg")) +
                                 list(existing_dir.glob("*.jpeg")))
            if existing_count > 0 and not dry_run:
                print(f"  이미 {existing_count}개 figure 존재, 건너뜀 "
                      f"(재추출하려면 디렉토리 삭제 후 재실행)")
                results.append({
                    "slug": slug,
                    "status": "skipped_exists",
                    "figures_count": existing_count,
                })
                continue

        # PDF 다운로드 및 이미지 추출
        result = download_and_extract(slug, arxiv_id, PAPERS_DIR, dry_run=dry_run)
        results.append(result)

        # arXiv 속도 제한 준수 (3초 대기)
        if idx < total:
            print(f"\n  (arXiv 속도 제한 대기: {ARXIV_DELAY}초)")
            time.sleep(ARXIV_DELAY)

    return results


# ── 결과 요약 출력 ────────────────────────────────────────────────────
def print_summary(results: list[dict]) -> None:
    """처리 결과를 요약해서 출력한다."""
    print(f"\n{'='*60}")
    print("처리 결과 요약")
    print(f"{'='*60}")

    status_counts = {}
    total_figures = 0

    for r in results:
        status = r.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        total_figures += r.get("figures_count", 0)

    print(f"  전체 처리: {len(results)}건")
    for status, count in sorted(status_counts.items()):
        label = {
            "success": "성공",
            "dry_run": "미리보기",
            "skipped_exists": "이미 존재 (건너뜀)",
            "skipped_no_arxiv": "arXiv URL 아님 (건너뜀)",
            "not_found": "arXiv에서 찾을 수 없음",
            "download_error": "다운로드 실패",
            "extraction_error": "추출 실패",
            "metadata_error": "메타데이터 조회 실패",
        }.get(status, status)
        print(f"    {label}: {count}건")

    if total_figures > 0:
        print(f"  총 추출 figure: {total_figures}개")

    # 실패 건 상세
    failures = [r for r in results if r.get("status", "").endswith("error")]
    if failures:
        print(f"\n  실패 상세:")
        for r in failures:
            print(f"    - {r['slug']}: {r.get('status', '')} "
                  f"({r.get('error', 'N/A')})")

    # arXiv URL이 아닌 건 안내
    non_arxiv = [r for r in results if r.get("status") == "skipped_no_arxiv"]
    if non_arxiv:
        print(f"\n  arXiv가 아닌 paper_url ({len(non_arxiv)}건):")
        for r in non_arxiv:
            print(f"    - {r['slug']}: {r.get('paper_url', '')}")


# ── CLI 엔트리포인트 ──────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="논문 PDF에서 figure 이미지를 추출합니다 (Phase D)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python extract_paper_figures.py --arxiv-only          # arXiv URL만 처리
  python extract_paper_figures.py --all                  # 전체 paper_url 처리
  python extract_paper_figures.py --slug gpt-4           # 특정 slug만
  python extract_paper_figures.py --metadata             # 메타데이터만 업데이트
  python extract_paper_figures.py --dry-run              # 미리보기
  python extract_paper_figures.py --slug bert --dry-run  # 특정 slug 미리보기
        """,
    )

    # 처리 범위 옵션 (상호 배타적)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument(
        "--arxiv-only",
        action="store_true",
        help="arXiv URL이 있는 엔트리만 처리",
    )
    scope.add_argument(
        "--all",
        action="store_true",
        help="paper_url이 있는 전체 엔트리 처리",
    )
    scope.add_argument(
        "--slug",
        type=str,
        help="특정 slug의 엔트리만 처리",
    )
    scope.add_argument(
        "--metadata",
        action="store_true",
        help="arXiv 메타데이터만 조회/업데이트 (이미지 추출 없음)",
    )

    # 공통 옵션
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 다운로드/저장 없이 미리보기만",
    )
    parser.add_argument(
        "--no-django",
        action="store_true",
        help="Django DB 없이 JSON 파일에서 로드 (독립 실행)",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Phase D: 논문 Figure 추출 파이프라인")
    print("=" * 60)

    # 엔트리 로드
    if args.no_django:
        entries = load_entries_from_json(
            slug_filter=args.slug,
            arxiv_only=args.arxiv_only,
        )
    else:
        slug_filter = args.slug if args.slug else None
        arxiv_only = args.arxiv_only or args.metadata
        entries = load_entries_from_db(
            slug_filter=slug_filter,
            arxiv_only=arxiv_only,
        )

    if not entries:
        print("\n[INFO] 처리할 엔트리가 없습니다.")
        return

    print(f"\n처리 대상: {len(entries)}건")
    if args.dry_run:
        print("[DRY-RUN 모드] 실제 변경 없이 미리보기만 수행합니다.")

    # 처리 실행
    if args.metadata:
        results = update_metadata_only(entries, dry_run=args.dry_run)
    else:
        results = process_entries(entries, dry_run=args.dry_run)

    # 결과 요약
    print_summary(results)

    # 결과를 JSON 파일로 저장 (dry-run이 아닌 경우)
    if not args.dry_run:
        report_path = DATA_DIR / "figure_extraction_report.json"
        report_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"\n결과 리포트 저장: {report_path}")


if __name__ == "__main__":
    main()
