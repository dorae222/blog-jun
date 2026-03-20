#!/usr/bin/env python3
"""
논문/아키텍처 figures 이미지 품질 검증 스크립트 (Pillow 기반)

사용법:
  python pipeline/verify_figures.py
  python pipeline/verify_figures.py --dir papers_written
  python pipeline/verify_figures.py --dir architectures_written
"""
import json
import sys
import argparse
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("[ERROR] Pillow가 설치되지 않았습니다: pip install Pillow")
    sys.exit(1)


BASE_DIR = Path(__file__).parent / 'data'
OUTPUT_FILE = BASE_DIR / 'figure_verify_report.json'

CHECKS = {
    'min_size_bytes': 5 * 1024,    # 5KB 미만 → 깨진 이미지 의심
    'min_width': 100,               # 100px 미만 → 추적 픽셀 의심
    'min_height': 100,
    'allowed_formats': {'PNG', 'JPEG', 'WEBP', 'GIF'},
}

VALID_SUFFIXES = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}


def check_image(path: Path) -> dict:
    result = {
        'path': str(path),
        'passed': False,
        'errors': [],
        'size_bytes': 0,
        'width': 0,
        'height': 0,
        'format': '',
    }

    if not path.exists():
        result['errors'].append('파일 없음')
        return result

    size_bytes = path.stat().st_size
    result['size_bytes'] = size_bytes

    if size_bytes < CHECKS['min_size_bytes']:
        result['errors'].append(f"파일 크기 너무 작음: {size_bytes}B < {CHECKS['min_size_bytes']}B")

    try:
        with Image.open(path) as img:
            img.verify()

        with Image.open(path) as img:
            width, height = img.size
            fmt = img.format or ''
            result['width'] = width
            result['height'] = height
            result['format'] = fmt

            if width < CHECKS['min_width']:
                result['errors'].append(f"너비 너무 작음: {width}px")
            if height < CHECKS['min_height']:
                result['errors'].append(f"높이 너무 작음: {height}px")
            if fmt not in CHECKS['allowed_formats']:
                result['errors'].append(f"허용되지 않는 포맷: {fmt}")
    except Exception as e:
        result['errors'].append(f"이미지 열기 실패: {e}")

    result['passed'] = len(result['errors']) == 0
    return result


def scan_directory(base: Path) -> list:
    results = []
    if not base.exists():
        print(f"[SKIP] 디렉토리 없음: {base}")
        return results

    for paper_dir in sorted(base.iterdir()):
        if not paper_dir.is_dir():
            continue
        figures_dir = paper_dir / 'figures'
        if not figures_dir.exists():
            continue
        for fig in sorted(figures_dir.iterdir()):
            if fig.suffix.lower() not in VALID_SUFFIXES:
                continue
            result = check_image(fig)
            results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description='Figure 이미지 품질 검증')
    parser.add_argument(
        '--dir',
        choices=['papers_written', 'architectures_written', 'all'],
        default='all',
        help='검증할 디렉토리 (기본: all)',
    )
    args = parser.parse_args()

    all_results = []

    if args.dir in ('papers_written', 'all'):
        print("📄 논문 figures 검증 중...")
        papers_results = scan_directory(BASE_DIR / 'papers_written')
        all_results.extend(papers_results)

    if args.dir in ('architectures_written', 'all'):
        print("🏗️  아키텍처 figures 검증 중...")
        arch_results = scan_directory(BASE_DIR / 'architectures_written')
        all_results.extend(arch_results)

    passed = [r for r in all_results if r['passed']]
    failed = [r for r in all_results if not r['passed']]

    print(f"\n=== 검증 결과 ===")
    print(f"총 {len(all_results)}개 / 통과 {len(passed)}개 / 실패 {len(failed)}개")

    if failed:
        print("\n❌ 실패 목록:")
        for r in failed:
            print(f"  {r['path']}")
            for err in r['errors']:
                print(f"    - {err}")

    report = {
        'total': len(all_results),
        'passed': len(passed),
        'failed': len(failed),
        'pass_rate': f"{len(passed)/len(all_results)*100:.1f}%" if all_results else "N/A",
        'passed_list': [r['path'] for r in passed],
        'failed_list': failed,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n리포트 저장: {OUTPUT_FILE}")

    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
