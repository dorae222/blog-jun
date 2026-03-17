"""
pipeline/data/preprocessed/ 에서 10.Cloud__ 이외의 파일을 archive로 이동하는 스크립트.
대상 접두사: 00.Inbox__, 20.AI__, 30.Data__, 40.DEV__, 50.Foundation__, 60.Project__, 70.Program__
"""
import argparse
import shutil
from pathlib import Path

# 이동 대상 접두사
NON_CLOUD_PREFIXES = (
    "00.Inbox__",
    "20.AI__",
    "30.Data__",
    "40.DEV__",
    "50.Foundation__",
    "60.Project__",
    "70.Program__",
)

BASE_DIR = Path(__file__).resolve().parent
PREPROCESSED_DIR = BASE_DIR / "data" / "preprocessed"
ARCHIVE_DIR = BASE_DIR / "data" / "archive" / "non_cloud_removed"


def cleanup(dry_run: bool = False):
    if not PREPROCESSED_DIR.exists():
        print(f"[ERROR] 디렉토리가 존재하지 않습니다: {PREPROCESSED_DIR}")
        return

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    moved_files = []
    skipped_files = []

    for filepath in sorted(PREPROCESSED_DIR.iterdir()):
        if not filepath.is_file():
            continue

        if filepath.name.startswith(NON_CLOUD_PREFIXES):
            moved_files.append(filepath)
        else:
            skipped_files.append(filepath)

    # 요약 출력
    print(f"{'[DRY-RUN] ' if dry_run else ''}Pipeline 클린업 결과")
    print(f"{'=' * 50}")
    print(f"전체 파일 수: {len(moved_files) + len(skipped_files)}")
    print(f"이동 대상:    {len(moved_files)}")
    print(f"유지 (Cloud): {len(skipped_files)}")
    print()

    if moved_files:
        # 접두사별 카운트
        prefix_counts = {}
        for f in moved_files:
            prefix = f.name.split("__")[0] + "__"
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

        print("접두사별 이동 파일 수:")
        for prefix, count in sorted(prefix_counts.items()):
            print(f"  {prefix:<20s} {count}개")
        print()

    if dry_run:
        print("[DRY-RUN] 실제 파일 이동은 수행하지 않았습니다.")
        if moved_files:
            print("\n이동 예정 파일:")
            for f in moved_files:
                print(f"  {f.name}")
    else:
        for filepath in moved_files:
            dest = ARCHIVE_DIR / filepath.name
            shutil.move(str(filepath), str(dest))
            print(f"  이동: {filepath.name}")
        print(f"\n총 {len(moved_files)}개 파일을 {ARCHIVE_DIR}로 이동했습니다.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="non-Cloud 파일을 archive로 이동")
    parser.add_argument("--dry-run", action="store_true", help="실제 이동 없이 대상 파일만 확인")
    args = parser.parse_args()

    cleanup(dry_run=args.dry_run)
