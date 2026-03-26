#!/usr/bin/env python3
"""
content.json의 content 필드를 content.md 파일로 분리

Before: content.json { "title": ..., "content": "마크다운..." }
After:  content.json { "title": ... }  (content 필드 제거)
        content.md   "마크다운..."

content.md가 이미 존재하면 스킵 (중복 실행 안전).
모든 written 디렉토리 대상 (papers, architectures, cloud, ml, data, colab).
"""
import json
import os
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

WRITTEN_DIRS = [
    "papers_written",
    "architectures_written",
    "cloud_written",
    "ml_written",
    "data_written",
    "colab_written",
]


def process_directory(target_dir: Path) -> tuple[int, int, int]:
    """단일 written 디렉토리 처리. (created, skipped, no_content) 반환."""
    created = 0
    skipped = 0
    no_content = 0

    if not target_dir.exists():
        print(f"  [WARN] 디렉토리 없음: {target_dir.name}")
        return created, skipped, no_content

    for item_dir in sorted(target_dir.iterdir()):
        if not item_dir.is_dir():
            continue

        content_json = item_dir / "content.json"
        if not content_json.exists():
            continue

        content_md = item_dir / "content.md"

        with open(content_json, encoding="utf-8") as f:
            data = json.load(f)

        if "content" not in data:
            no_content += 1
            continue

        if content_md.exists():
            # content 필드가 content.json에 남아 있으면 제거
            if "content" in data:
                del data["content"]
                with open(content_json, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            skipped += 1
            continue

        # content.md 저장
        content_md.write_text(data["content"], encoding="utf-8")

        # content.json에서 content 필드 제거
        del data["content"]
        with open(content_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  [OK] {item_dir.name}/content.md")
        created += 1

    return created, skipped, no_content


def main():
    total_created = 0
    total_skipped = 0
    total_no_content = 0

    for dir_name in WRITTEN_DIRS:
        target_dir = DATA_DIR / dir_name
        print(f"\n{'='*50}")
        print(f"처리 중: {dir_name}")
        print(f"{'='*50}")

        created, skipped, no_content = process_directory(target_dir)
        total_created += created
        total_skipped += skipped
        total_no_content += no_content

        print(f"  생성: {created}개 / 스킵: {skipped}개 / content 없음: {no_content}개")

    print(f"\n{'='*50}")
    print(f"✓ 전체 완료")
    print(f"  content.md 생성: {total_created}개")
    print(f"  이미 존재 (스킵): {total_skipped}개")
    print(f"  content 필드 없음: {total_no_content}개")


if __name__ == "__main__":
    main()
