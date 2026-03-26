#!/usr/bin/env python3
"""
논문 리뷰 퍼블리싱 스크립트

content.md 작성 완료 후: 검증 → figure_reference.json 생성 → 인덱스 갱신 → DB 임포트

사용법:
  python pipeline/publish_paper.py --slug tidar                   # 단일 논문
  python pipeline/publish_paper.py --all-modified                 # 최근 수정된 논문 자동 감지
  python pipeline/publish_paper.py --slug tidar --skip-import     # 인덱스만, DB 임포트 생략
  python pipeline/publish_paper.py --dry-run                      # 미리보기만
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# ──────────────────────────────────────────────
# 경로 상수
# ──────────────────────────────────────────────
PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PIPELINE_DIR.parent
PAPERS_DIR = PIPELINE_DIR / "data" / "papers_written"
CONTENT_INDEX = PIPELINE_DIR / "data" / "blog-jun-content.json"
BUILD_INDEX_SCRIPT = PIPELINE_DIR / "useful" / "build_content_index.py"
IMPORT_SCRIPT = PIPELINE_DIR / "import_papers_written.py"

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}

# 마크다운 figure 참조 패턴
FIG_REF_PATTERN = re.compile(
    r'!\[([^\]]*)\]\(figures/([^)]+)\)'
)
FIG_WITH_CAPTION = re.compile(
    r'!\[([^\]]*)\]\(figures/([^)]+\.(?:png|jpg|jpeg|webp|gif|svg))\)\s*\n\s*\*([^*]+)\*',
    re.MULTILINE,
)
SECTION_HEADER = re.compile(r'^## .+', re.MULTILINE)


# ──────────────────────────────────────────────
# 터미널 색상 유틸
# ──────────────────────────────────────────────
class Color:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def ok(msg: str) -> str:
    return f"{Color.GREEN}[OK]{Color.RESET} {msg}"


def warn(msg: str) -> str:
    return f"{Color.YELLOW}[WARN]{Color.RESET} {msg}"


def err(msg: str) -> str:
    return f"{Color.RED}[FAIL]{Color.RESET} {msg}"


def info(msg: str) -> str:
    return f"{Color.CYAN}[INFO]{Color.RESET} {msg}"


def header(msg: str) -> str:
    return f"\n{Color.BOLD}{msg}{Color.RESET}"


# ──────────────────────────────────────────────
# 논문 디렉토리 탐색
# ──────────────────────────────────────────────
def find_paper_dir(slug: str) -> Path | None:
    """slug로 논문 디렉토리를 찾는다. 번호 접두사({N}_{slug}) 패턴도 지원."""
    # 정확히 일치하는 디렉토리
    exact = PAPERS_DIR / slug
    if exact.is_dir():
        return exact

    # {N}_{slug} 패턴
    for d in PAPERS_DIR.iterdir():
        if not d.is_dir():
            continue
        match = re.match(r'^\d+_(.+)$', d.name)
        if match and match.group(1) == slug:
            return d

    return None


def find_modified_papers() -> list[Path]:
    """최근 수정된 content.md를 가진 논문 디렉토리 목록 반환.

    기준: content.md의 mtime > blog-jun-content.json의 mtime
    blog-jun-content.json이 없으면 모든 content.md가 대상.
    """
    index_mtime = CONTENT_INDEX.stat().st_mtime if CONTENT_INDEX.exists() else 0
    modified = []

    for paper_dir in sorted(PAPERS_DIR.iterdir()):
        if not paper_dir.is_dir():
            continue
        content_md = paper_dir / "content.md"
        if not content_md.exists():
            continue
        if content_md.stat().st_mtime > index_mtime:
            modified.append(paper_dir)

    return modified


# ──────────────────────────────────────────────
# 검증: content.md
# ──────────────────────────────────────────────
def validate_content_md(paper_dir: Path) -> tuple[bool, list[str]]:
    """content.md 검증. (통과 여부, 메시지 목록) 반환."""
    messages = []
    passed = True
    content_md = paper_dir / "content.md"

    # 존재 여부
    if not content_md.exists():
        messages.append(err("content.md가 없습니다."))
        return False, messages

    text = content_md.read_text(encoding="utf-8")

    # 최소 길이
    if len(text) < 100:
        messages.append(err(f"content.md가 너무 짧습니다 ({len(text)}자, 최소 100자)."))
        passed = False
    else:
        messages.append(ok(f"content.md 길이: {len(text):,}자"))

    # 섹션 수 (## 헤더)
    sections = SECTION_HEADER.findall(text)
    if len(sections) < 3:
        messages.append(err(f"섹션이 부족합니다 ({len(sections)}개, 최소 3개 필요)."))
        passed = False
    else:
        messages.append(ok(f"섹션: {len(sections)}개"))

    # Figure 참조 검증 (깨진 참조 확인)
    figures_dir = paper_dir / "figures"
    available_files = set()
    if figures_dir.is_dir():
        available_files = {
            f.name for f in figures_dir.iterdir()
            if f.suffix.lower() in IMAGE_EXTENSIONS
        }

    broken_refs = []
    for m in FIG_REF_PATTERN.finditer(text):
        fig_filename = m.group(2).strip()
        if fig_filename not in available_files:
            broken_refs.append(fig_filename)

    if broken_refs:
        messages.append(err(f"깨진 figure 참조 {len(broken_refs)}개:"))
        for ref in broken_refs:
            messages.append(f"    - figures/{ref}")
        passed = False
    else:
        ref_count = len(FIG_REF_PATTERN.findall(text))
        messages.append(ok(f"Figure 참조: {ref_count}개 (깨진 참조 없음)"))

    return passed, messages


# ──────────────────────────────────────────────
# 검증: content.json
# ──────────────────────────────────────────────
def validate_content_json(paper_dir: Path) -> tuple[bool, list[str]]:
    """content.json 검증. (통과 여부, 메시지 목록) 반환."""
    messages = []
    passed = True
    content_json = paper_dir / "content.json"

    if not content_json.exists():
        messages.append(err("content.json이 없습니다."))
        return False, messages

    try:
        data = json.loads(content_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        messages.append(err(f"content.json 파싱 실패: {e}"))
        return False, messages

    # 필수 필드
    required_fields = ["title", "slug", "arxiv_url"]
    for field in required_fields:
        value = data.get(field, "")
        if not value or not str(value).strip():
            messages.append(err(f"필수 필드 누락: {field}"))
            passed = False
        else:
            messages.append(ok(f"{field}: {str(value)[:60]}"))

    # 선택 필드 (경고만)
    optional_fields = ["summary", "tags", "year", "venue"]
    for field in optional_fields:
        value = data.get(field)
        if not value or (isinstance(value, (str, list)) and not value):
            messages.append(warn(f"선택 필드 누락: {field}"))

    return passed, messages


# ──────────────────────────────────────────────
# figure_reference.json 자동 생성/갱신
# ──────────────────────────────────────────────
def generate_figure_reference(paper_dir: Path, dry_run: bool = False) -> dict:
    """content.md를 파싱하여 figure_reference.json을 생성/갱신한다."""
    content_md = paper_dir / "content.md"
    text = content_md.read_text(encoding="utf-8") if content_md.exists() else ""
    figures_dir = paper_dir / "figures"

    # content.json에서 slug 읽기
    content_json = paper_dir / "content.json"
    slug = paper_dir.name
    if content_json.exists():
        data = json.loads(content_json.read_text(encoding="utf-8"))
        slug = data.get("slug", slug)
    # 번호 접두사 제거
    slug_match = re.match(r'^\d+_(.+)$', slug)
    if slug_match:
        slug = slug_match.group(1)

    # figures/metadata.json 로드 (캡션 보강용)
    metadata_map: dict[str, dict] = {}
    metadata_path = figures_dir / "metadata.json" if figures_dir.is_dir() else None
    if metadata_path and metadata_path.exists():
        items = json.loads(metadata_path.read_text(encoding="utf-8"))
        for item in items:
            fname = item.get("filename", "")
            if fname:
                metadata_map[fname] = {
                    "caption": item.get("caption", ""),
                    "figure_number": item.get("figure_number", ""),
                    "has_caption": bool(item.get("caption", "")),
                }

    # figures/ 디렉토리 내 실제 이미지 파일 목록
    available_files = []
    if figures_dir.is_dir():
        available_files = sorted([
            f.name for f in figures_dir.iterdir()
            if f.suffix.lower() in IMAGE_EXTENSIONS
        ])

    # 섹션 헤더 목록
    sections = [m.group() for m in SECTION_HEADER.finditer(text)]

    # 섹션 위치 계산 (figure가 어느 섹션에 속하는지 파악용)
    section_positions = [(m.start(), m.group()) for m in SECTION_HEADER.finditer(text)]

    def find_section(pos: int) -> str | None:
        current = None
        for spos, stitle in section_positions:
            if spos <= pos:
                current = stitle
            else:
                break
        return current

    # content.md 내 figure 참조 파싱
    existing_refs = []
    referenced_filenames = set()
    for m in FIG_REF_PATTERN.finditer(text):
        alt = m.group(1).strip()
        filename = m.group(2).strip()
        section = find_section(m.start())
        existing_refs.append({
            "filename": filename,
            "section": section,
            "alt": alt,
        })
        referenced_filenames.add(filename)

    # figures 엔트리 구성: 모든 가용 파일에 대해
    figures_entries = []
    for fname in available_files:
        meta = metadata_map.get(fname, {})
        caption = meta.get("caption", "")
        figure_number = meta.get("figure_number", "")
        has_caption = bool(caption)
        figures_entries.append({
            "filename": fname,
            "caption": caption,
            "figure_number": figure_number,
            "has_caption": has_caption,
        })

    result = {
        "slug": slug,
        "figures": figures_entries,
        "sections": sections,
        "existing_refs": existing_refs,
        "total_figures": len(available_files),
        "total_existing_refs": len(existing_refs),
    }

    # 파일 쓰기
    fig_ref_path = paper_dir / "figure_reference.json"
    if not dry_run:
        fig_ref_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return result


# ──────────────────────────────────────────────
# 외부 스크립트 실행
# ──────────────────────────────────────────────
def run_build_index(dry_run: bool = False) -> bool:
    """build_content_index.py 실행."""
    if not BUILD_INDEX_SCRIPT.exists():
        print(err(f"인덱스 빌드 스크립트 없음: {BUILD_INDEX_SCRIPT}"))
        return False

    if dry_run:
        print(info(f"[DRY-RUN] 실행 예정: python3 {BUILD_INDEX_SCRIPT}"))
        return True

    print(info(f"인덱스 빌드 실행: {BUILD_INDEX_SCRIPT.name}"))
    result = subprocess.run(
        ["python3", str(BUILD_INDEX_SCRIPT)],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(err("인덱스 빌드 실패:"))
        if result.stderr:
            for line in result.stderr.strip().split("\n"):
                print(f"    {line}")
        return False

    # 마지막 몇 줄만 출력 (요약)
    output_lines = result.stdout.strip().split("\n")
    for line in output_lines[-5:]:
        print(f"    {Color.DIM}{line}{Color.RESET}")
    return True


def run_import(dry_run: bool = False) -> bool:
    """import_papers_written.py --update 실행."""
    if not IMPORT_SCRIPT.exists():
        print(err(f"임포트 스크립트 없음: {IMPORT_SCRIPT}"))
        return False

    if dry_run:
        print(info("[DRY-RUN] 실행 예정: python3 import_papers_written.py --update"))
        return True

    print(info(f"DB 임포트 실행: {IMPORT_SCRIPT.name} --update"))
    result = subprocess.run(
        ["python3", str(IMPORT_SCRIPT), "--update"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(warn("DB 임포트 실패 (Django 환경 미설정일 수 있음):"))
        if result.stderr:
            # 첫 5줄만 표시 (Django import 에러는 길 수 있음)
            stderr_lines = result.stderr.strip().split("\n")
            for line in stderr_lines[:5]:
                print(f"    {line}")
            if len(stderr_lines) > 5:
                print(f"    ... ({len(stderr_lines) - 5}줄 생략)")
        return False

    output_lines = result.stdout.strip().split("\n")
    for line in output_lines[-3:]:
        print(f"    {Color.DIM}{line}{Color.RESET}")
    return True


# ──────────────────────────────────────────────
# 단일 논문 처리
# ──────────────────────────────────────────────
def process_paper(paper_dir: Path, dry_run: bool = False) -> bool:
    """단일 논문 검증 + figure_reference.json 생성. 성공 시 True 반환."""
    dir_name = paper_dir.name
    print(header(f"=== {dir_name} ==="))

    # 1. content.md 검증
    print(header("1. content.md 검증"))
    md_passed, md_msgs = validate_content_md(paper_dir)
    for msg in md_msgs:
        print(f"  {msg}")

    # 2. content.json 검증
    print(header("2. content.json 검증"))
    json_passed, json_msgs = validate_content_json(paper_dir)
    for msg in json_msgs:
        print(f"  {msg}")

    # 3. figure_reference.json 생성/갱신
    print(header("3. figure_reference.json 생성"))
    fig_ref = generate_figure_reference(paper_dir, dry_run=dry_run)
    total_figs = fig_ref["total_figures"]
    total_refs = fig_ref["total_existing_refs"]

    if dry_run:
        print(f"  {info('[DRY-RUN] figure_reference.json 생성 예정')}")
    else:
        print(f"  {ok('figure_reference.json 갱신 완료')}")

    print(f"  {info(f'가용 figure: {total_figs}개, content.md 내 참조: {total_refs}개')}")

    unreferenced = total_figs - total_refs
    if unreferenced > 0:
        print(f"  {warn(f'미참조 figure: {unreferenced}개')}")

    return md_passed and json_passed


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="논문 리뷰 퍼블리싱: 검증 → 인덱스 → DB 임포트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python pipeline/publish_paper.py --slug tidar
  python pipeline/publish_paper.py --all-modified
  python pipeline/publish_paper.py --slug tidar --skip-import
  python pipeline/publish_paper.py --all-modified --dry-run
        """,
    )
    parser.add_argument("--slug", type=str, help="논문 slug (예: tidar, attention-is-all-you-need)")
    parser.add_argument("--all-modified", action="store_true", help="최근 수정된 content.md 자동 감지")
    parser.add_argument("--skip-import", action="store_true", help="DB 임포트 생략 (인덱스만 갱신)")
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 미리보기")
    args = parser.parse_args()

    # 인자 검증
    if not args.slug and not args.all_modified:
        parser.error("--slug 또는 --all-modified 중 하나를 지정하세요.")

    if args.slug and args.all_modified:
        parser.error("--slug와 --all-modified는 동시에 사용할 수 없습니다.")

    if args.dry_run:
        print(f"{Color.BOLD}{Color.YELLOW}=== DRY-RUN 모드 ==={Color.RESET}")

    # ── 대상 논문 결정 ──
    paper_dirs: list[Path] = []

    if args.slug:
        paper_dir = find_paper_dir(args.slug)
        if not paper_dir:
            print(err(f"논문 디렉토리를 찾을 수 없습니다: {args.slug}"))
            print(f"  검색 경로: {PAPERS_DIR}")
            sys.exit(1)
        paper_dirs = [paper_dir]

    elif args.all_modified:
        paper_dirs = find_modified_papers()
        if not paper_dirs:
            print(ok("수정된 논문이 없습니다 (인덱스 대비 최신 상태)."))
            sys.exit(0)
        print(info(f"수정 감지: {len(paper_dirs)}개 논문"))
        for d in paper_dirs:
            print(f"  - {d.name}")

    # ── 각 논문 처리 (검증 + figure_reference.json) ──
    all_passed = True
    processed = 0

    for paper_dir in paper_dirs:
        passed = process_paper(paper_dir, dry_run=args.dry_run)
        if not passed:
            all_passed = False
        processed += 1

    # ── 요약 ──
    print(header("=== 처리 요약 ==="))
    print(f"  처리 논문: {processed}개")

    if not all_passed:
        print(f"  {err('검증 실패 항목이 있습니다. 위 오류를 확인하세요.')}")
        print(f"  {info('인덱스/임포트를 건너뜁니다.')}")
        sys.exit(1)

    print(f"  {ok('모든 검증 통과')}")

    # ── 4. 인덱스 빌드 ──
    print(header("4. 인덱스 빌드"))
    index_ok = run_build_index(dry_run=args.dry_run)
    if index_ok:
        print(f"  {ok('인덱스 빌드 완료')}")
    else:
        print(f"  {err('인덱스 빌드 실패')}")

    # ── 5. DB 임포트 ──
    if args.skip_import:
        print(header("5. DB 임포트"))
        print(f"  {info('--skip-import 지정됨, 건너뜀')}")
    else:
        print(header("5. DB 임포트"))
        import_ok = run_import(dry_run=args.dry_run)
        if import_ok:
            print(f"  {ok('DB 임포트 완료')}")
        else:
            print(f"  {warn('DB 임포트 실패 (로컬 Django 환경이 필요합니다)')}")

    # ── 최종 결과 ──
    print(header("=== 완료 ==="))
    if args.dry_run:
        print(f"  {info('[DRY-RUN] 실제 변경 없음')}")
    else:
        print(f"  {ok('퍼블리싱 완료')}")
    sys.exit(0)


if __name__ == "__main__":
    main()
