#!/usr/bin/env python3
"""
논문 figure를 content.json에 통합하고, Django PostImage 레코드를 생성합니다.

작업 흐름:
1. papers_written/{slug}/figures/ 에서 figure 파일 수집
2. figures/metadata.json 에서 캡션 정보 로드
3. content.json의 markdown에 ![caption](figures/...) 참조 삽입
4. media/figures/papers/{slug}/ 로 파일 복사
5. PostImage 레코드 생성 (image_type='paper_figure')

사용법:
    python -m pipeline.generators.figure_integrator --slug bert
    python -m pipeline.generators.figure_integrator --all
    python -m pipeline.generators.figure_integrator --dry-run --all
"""
import argparse
import json
import os
import re
import shutil
from pathlib import Path

PAPERS_DIR = Path("pipeline/data/papers_written")
# Docker: /app/media, 로컬: backend/media
MEDIA_DIR = Path("media") if Path("media").exists() else Path("backend/media")


def find_paper_dirs() -> list[Path]:
    """papers_written 디렉토리에서 모든 논문 디렉토리 반환."""
    if not PAPERS_DIR.exists():
        return []
    return sorted(
        d for d in PAPERS_DIR.iterdir()
        if d.is_dir() and (d / "content.json").exists()
    )


def load_metadata(paper_dir: Path) -> list[dict]:
    """figures/metadata.json 로드. 없으면 파일 이름 기반으로 생성."""
    meta_path = paper_dir / "figures" / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)

    # metadata.json 없으면 파일 기반으로 자동 생성
    fig_dir = paper_dir / "figures"
    if not fig_dir.exists():
        return []

    figures = []
    for idx, fp in enumerate(sorted(fig_dir.glob("*.png")), start=1):
        figures.append({
            "filename": fp.name,
            "caption": "",
            "figure_number": idx,
            "source_url": "",
        })
    # SVG도 포함
    for idx, fp in enumerate(sorted(fig_dir.glob("*.svg")), start=len(figures) + 1):
        if fp.name == "architecture.svg":
            figures.append({
                "filename": fp.name,
                "caption": "Architecture Diagram",
                "figure_number": idx,
                "source_url": "",
            })
    return figures


def integrate_figures_into_content(
    content: str,
    slug: str,
    figures: list[dict],
) -> str:
    """content markdown에 figure 참조가 없으면 적절한 위치에 삽입."""
    if not figures:
        return content

    # 이미 figure 참조가 있으면 스킵
    if re.search(r'!\[.*?\]\(.*?figures/', content):
        return content

    # Introduction/Method 섹션 사이, 또는 첫 번째 ## 뒤에 삽입
    figure_block = "\n\n"
    for fig in figures:
        if fig["filename"].endswith(".svg"):
            continue  # SVG는 별도 처리
        caption = fig.get("caption", f"Figure {fig.get('figure_number', '')}")
        figure_block += f"![{caption}](/media/figures/papers/{slug}/{fig['filename']})\n\n"

    # ## 패턴 찾기 — 두 번째 ## 앞에 삽입 (첫 번째는 보통 Introduction)
    h2_pattern = re.compile(r'^## ', re.MULTILINE)
    matches = list(h2_pattern.finditer(content))

    if len(matches) >= 2:
        insert_pos = matches[1].start()
        return content[:insert_pos] + figure_block + content[insert_pos:]
    elif matches:
        # ## 하나만 있으면 끝에 추가
        return content + figure_block
    else:
        # ## 없으면 끝에 추가
        return content + figure_block


def copy_figures_to_media(paper_dir: Path, slug: str, dry_run: bool = False) -> int:
    """figures/ → media/figures/papers/{slug}/ 복사."""
    fig_dir = paper_dir / "figures"
    if not fig_dir.exists():
        return 0

    target_dir = MEDIA_DIR / "figures" / "papers" / slug
    copied = 0

    for fp in sorted(fig_dir.iterdir()):
        if fp.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            if not dry_run:
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fp, target_dir / fp.name)
            copied += 1

    return copied


def process_paper(slug: str, dry_run: bool = False, verbose: bool = True) -> dict:
    """단일 논문 figure 통합 처리."""
    # 논문 디렉토리 찾기 (접두사 번호 포함)
    paper_dir = None
    for d in PAPERS_DIR.iterdir():
        if not d.is_dir() or not (d / "content.json").exists():
            continue
        if d.name.endswith(f"_{slug}") or d.name == slug:
            paper_dir = d
            break

    if not paper_dir:
        # slug로 직접 매칭 시도
        for d in PAPERS_DIR.iterdir():
            if d.is_dir():
                cj = d / "content.json"
                if cj.exists():
                    with open(cj, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if data.get("slug") == slug:
                        paper_dir = d
                        break

    if not paper_dir:
        if verbose:
            print(f"  [SKIP] {slug}: 디렉토리 없음")
        return {"slug": slug, "status": "not_found", "figures": 0}

    # content.json 로드
    content_path = paper_dir / "content.json"
    with open(content_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Figure 메타데이터 로드
    figures = load_metadata(paper_dir)
    png_figures = [f for f in figures if f["filename"].endswith(".png")]

    if not png_figures:
        if verbose:
            print(f"  [SKIP] {slug}: PNG figure 없음")
        return {"slug": slug, "status": "no_figures", "figures": 0}

    # content에 figure 참조 삽입
    original_content = data.get("content", "")
    updated_content = integrate_figures_into_content(original_content, slug, png_figures)

    content_changed = updated_content != original_content

    if content_changed and not dry_run:
        data["content"] = updated_content
        with open(content_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # media로 파일 복사
    copied = copy_figures_to_media(paper_dir, slug, dry_run=dry_run)

    status = "updated" if content_changed else "already_has_figures"
    if verbose:
        action = "[DRY-RUN]" if dry_run else ""
        print(f"  {action} {slug}: {status}, {copied} figures copied")

    return {"slug": slug, "status": status, "figures": copied}


def main():
    parser = argparse.ArgumentParser(description="논문 figure를 content.json에 통합")
    parser.add_argument("--slug", help="단일 논문 slug")
    parser.add_argument("--all", action="store_true", help="전체 논문 처리")
    parser.add_argument("--dry-run", action="store_true", help="변경 없이 확인만")
    parser.add_argument("--verbose", action="store_true", default=True)
    args = parser.parse_args()

    if args.slug:
        result = process_paper(args.slug, dry_run=args.dry_run, verbose=args.verbose)
        print(f"\n결과: {result}")
    elif args.all:
        paper_dirs = find_paper_dirs()
        print(f"총 {len(paper_dirs)}개 논문 처리 시작...\n")

        stats = {"updated": 0, "no_figures": 0, "already_has_figures": 0, "not_found": 0}
        for pd in paper_dirs:
            cj = pd / "content.json"
            with open(cj, "r", encoding="utf-8") as f:
                data = json.load(f)
            slug = data.get("slug", pd.name)
            result = process_paper(slug, dry_run=args.dry_run, verbose=args.verbose)
            stats[result["status"]] = stats.get(result["status"], 0) + 1

        print(f"\n=== 완료 ===")
        for k, v in stats.items():
            print(f"  {k}: {v}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
