#!/usr/bin/env python3
"""
아키텍처 Figure 자동 품질 검증.

검사 항목:
- PNG 파일 존재 여부
- 파일 크기 (≥ 10KB)
- 이미지 해상도 (≥ 800x600)
- SVG 소스 존재 여부

사용법:
  python audit_figures.py --report     # 전체 검사 + 리포트
  python audit_figures.py --failing    # 기준 미달 목록만
  python audit_figures.py --json       # JSON 형식 출력
  python audit_figures.py --slug transformer  # 특정 slug만
"""
import json
import argparse
from pathlib import Path

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

ARCH_DIR = Path(__file__).parent / 'data' / 'architectures_written'
MIN_SIZE_KB = 10
MIN_WIDTH = 800
MIN_HEIGHT = 600


def audit_figure(arch_dir: Path) -> dict:
    """단일 아키텍처의 figure 품질 검사."""
    slug = arch_dir.name
    png_path = arch_dir / 'figures' / 'architecture.png'
    svg_path = arch_dir / 'figures' / 'architecture.svg'
    entry_json = arch_dir / 'entry.json'

    result = {
        'slug': slug,
        'has_entry': entry_json.exists(),
        'has_png': png_path.exists(),
        'has_svg': svg_path.exists(),
        'png_size_kb': 0,
        'width': 0,
        'height': 0,
        'issues': [],
        'pass': True,
    }

    if not entry_json.exists():
        result['issues'].append('entry.json 없음')
        result['pass'] = False
        return result

    if not png_path.exists():
        result['issues'].append('PNG 파일 없음')
        result['pass'] = False
        return result

    # 파일 크기 검사
    size_kb = png_path.stat().st_size / 1024
    result['png_size_kb'] = round(size_kb, 1)
    if size_kb < MIN_SIZE_KB:
        result['issues'].append(f'PNG 크기 부족: {size_kb:.1f}KB < {MIN_SIZE_KB}KB')
        result['pass'] = False

    # 해상도 검사
    if HAS_PIL:
        try:
            with Image.open(png_path) as img:
                w, h = img.size
                result['width'] = w
                result['height'] = h
                if w < MIN_WIDTH or h < MIN_HEIGHT:
                    result['issues'].append(f'해상도 부족: {w}x{h} < {MIN_WIDTH}x{MIN_HEIGHT}')
                    result['pass'] = False
        except Exception as e:
            result['issues'].append(f'이미지 열기 실패: {e}')
            result['pass'] = False

    if not svg_path.exists():
        result['issues'].append('SVG 소스 없음 (경고)')

    return result


def main():
    parser = argparse.ArgumentParser(description='아키텍처 Figure 품질 검증')
    parser.add_argument('--report', action='store_true', help='전체 리포트')
    parser.add_argument('--failing', action='store_true', help='실패 항목만 출력')
    parser.add_argument('--json', action='store_true', help='JSON 형식 출력')
    parser.add_argument('--slug', type=str, help='특정 slug만')
    args = parser.parse_args()

    if args.slug:
        slugs = [s.strip() for s in args.slug.split(',')]
        dirs = [ARCH_DIR / s for s in slugs if (ARCH_DIR / s).exists()]
    else:
        dirs = sorted(d for d in ARCH_DIR.iterdir() if d.is_dir())

    results = [audit_figure(d) for d in dirs]

    passing = [r for r in results if r['pass']]
    failing = [r for r in results if not r['pass']]
    missing_png = [r for r in results if not r['has_png']]

    if args.json:
        print(json.dumps({
            'total': len(results),
            'passing': len(passing),
            'failing': len(failing),
            'missing_png': len(missing_png),
            'results': results if args.report else failing,
        }, indent=2, ensure_ascii=False))
        return

    if args.failing:
        if not failing:
            print("모든 figure가 품질 기준을 통과했습니다.")
            return
        print(f"기준 미달: {len(failing)}개")
        print("-" * 60)
        for r in failing:
            issues = ', '.join(r['issues'])
            print(f"  {r['slug']}: {issues}")
        return

    # 기본: 전체 리포트
    print(f"Figure 품질 검사 리포트")
    print(f"{'=' * 60}")
    print(f"전체: {len(results)}개")
    print(f"통과: {len(passing)}개")
    print(f"실패: {len(failing)}개")
    print(f"PNG 없음: {len(missing_png)}개")
    if not HAS_PIL:
        print("  (Pillow 미설치: 해상도 검사 스킵)")
    print()

    if failing:
        print("실패 목록:")
        print("-" * 60)
        for r in failing:
            issues = ', '.join(r['issues'])
            print(f"  {r['slug']}: {issues}")

    if missing_png:
        print(f"\nPNG 미생성 목록 ({len(missing_png)}개):")
        for r in missing_png:
            print(f"  {r['slug']}")


if __name__ == '__main__':
    main()
