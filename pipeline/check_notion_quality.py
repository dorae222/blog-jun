"""Notion export 파일 품질 검증 — 빈 파일/손실 파일 식별.

실행:
    python pipeline/check_notion_quality.py
    python pipeline/check_notion_quality.py --min-lines 5
    python pipeline/check_notion_quality.py --dir /path/to/export
"""
import argparse
from pathlib import Path

DEFAULT_NOTION_DIR = Path("/Users/dorae222/Downloads/my page/[My Page]")
DEFAULT_MIN_LINES = 10


def check_quality(notion_dir: Path, min_lines: int = DEFAULT_MIN_LINES):
    if not notion_dir.exists():
        print(f"디렉토리가 존재하지 않습니다: {notion_dir}")
        return

    short_files = []
    total = 0

    for md_file in notion_dir.rglob("*.md"):
        total += 1
        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore").strip()
        except Exception:
            short_files.append((md_file, 0))
            continue

        lines = text.split("\n")
        non_empty = [l for l in lines if l.strip()]
        if len(non_empty) < min_lines:
            short_files.append((md_file, len(non_empty)))

    short_files.sort(key=lambda x: x[1])

    print(f"=== Notion Export 품질 검증 ===")
    print(f"검사 디렉토리: {notion_dir}")
    print(f"총 .md 파일: {total}개")
    print(f"손실 의심 ({min_lines}줄 미만): {len(short_files)}개 ({len(short_files)/max(total,1)*100:.1f}%)")
    print()

    for f, n in short_files:
        rel = f.relative_to(notion_dir)
        # 파일 내용 미리보기 (첫 3줄)
        try:
            preview = f.read_text(encoding="utf-8", errors="ignore").strip()[:200]
            preview = preview.replace("\n", " | ")
        except Exception:
            preview = "(읽기 실패)"
        print(f"  {n}줄: {rel}")
        print(f"       → {preview[:100]}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Notion export 품질 검증")
    parser.add_argument(
        "--dir", type=str, default=str(DEFAULT_NOTION_DIR),
        help=f"Notion export 디렉토리 (기본: {DEFAULT_NOTION_DIR})",
    )
    parser.add_argument(
        "--min-lines", type=int, default=DEFAULT_MIN_LINES,
        help=f"이 줄 수 미만이면 손실 의심 (기본: {DEFAULT_MIN_LINES})",
    )
    args = parser.parse_args()
    check_quality(Path(args.dir), args.min_lines)


if __name__ == "__main__":
    main()
