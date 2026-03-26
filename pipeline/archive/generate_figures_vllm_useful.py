#!/usr/bin/env python3
"""
vLLM (OpenAI 호환 API) 기반 아키텍처 다이어그램 생성.

로컬 GPU 서버의 vLLM에서 SVG 생성 → PNG 변환.
Qwen3-30B-A3B 등 OpenAI 호환 API를 제공하는 모델 사용.

사용법:
  python generate_figures_vllm.py --vllm-url http://localhost:8080/v1
  python generate_figures_vllm.py --vllm-url http://localhost:8080/v1 --slug transformer
  python generate_figures_vllm.py --vllm-url http://localhost:8080/v1 --force --slug albert,edm
  python generate_figures_vllm.py --dry-run
"""
import json
import os
import sys
import time
import argparse
from pathlib import Path

from openai import OpenAI

from svg_utils import extract_svg, svg_to_png, save_svg, validate_png
from generate_arch_figures import (
    SYSTEM_PROMPT, build_prompt, classify_architecture,
    ARCH_DIR,
)

# ── 설정 ──────────────────────────────────────────────────────────────
DEFAULT_VLLM_URL = 'http://localhost:8080/v1'
MAX_RETRIES = 5  # 로컬이므로 공격적 재시도
RETRY_DELAY = 2  # 초
OUTPUT_WIDTH = 1920
MIN_PNG_SIZE_KB = 10  # 최소 PNG 크기 (KB)


def generate_figure_vllm(client, model: str, prompt: str, output_path: Path,
                         max_tokens: int = 16384) -> bool:
    """vLLM OpenAI 호환 API로 SVG 생성 → PNG 변환."""
    svg_path = output_path.with_suffix('.svg')

    # Qwen3용 래퍼: SVG만 출력하도록 강조
    enhanced_prompt = (
        prompt + "\n\nIMPORTANT: Output ONLY valid SVG code. "
        "No markdown fences, no explanation, no text before or after the SVG."
    )

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": enhanced_prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.5,
            )

            text = response.choices[0].message.content
            svg_code = extract_svg(text)

            if not svg_code:
                print(f"      [WARN] SVG 추출 실패 (시도 {attempt}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                continue

            # SVG 저장 + PNG 변환
            save_svg(svg_code, svg_path)
            if svg_to_png(svg_code, output_path, output_width=OUTPUT_WIDTH):
                # PNG 크기 검증
                if validate_png(output_path, min_size_kb=MIN_PNG_SIZE_KB):
                    return True
                else:
                    size_kb = output_path.stat().st_size / 1024
                    print(f"      [WARN] PNG 크기 미달: {size_kb:.0f}KB < {MIN_PNG_SIZE_KB}KB (시도 {attempt}/{MAX_RETRIES})")
            else:
                print(f"      [WARN] PNG 변환 실패 (시도 {attempt}/{MAX_RETRIES})")

        except Exception as e:
            print(f"      [ERROR] 시도 {attempt}/{MAX_RETRIES}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    return False


def main():
    parser = argparse.ArgumentParser(description='vLLM 기반 아키텍처 다이어그램 생성 (SVG→PNG)')
    parser.add_argument('--vllm-url', type=str, default=DEFAULT_VLLM_URL,
                        help=f'vLLM API URL (기본: {DEFAULT_VLLM_URL})')
    parser.add_argument('--model', type=str, default='',
                        help='모델명 (미지정 시 vLLM에서 첫 번째 모델 사용)')
    parser.add_argument('--slug', type=str, help='특정 아키텍처 slug만 생성 (쉼표 구분)')
    parser.add_argument('--force', action='store_true', help='기존 이미지 덮어쓰기')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    parser.add_argument('--max-tokens', type=int, default=16384,
                        help='최대 생성 토큰 (기본: 16384)')
    args = parser.parse_args()

    # vLLM 클라이언트 초기화
    client = None
    model = args.model

    if not args.dry_run:
        client = OpenAI(api_key='not-needed', base_url=args.vllm_url)

        # 모델명 자동 감지
        if not model:
            try:
                models = client.models.list()
                model = models.data[0].id
                print(f"감지된 모델: {model}")
            except Exception as e:
                print(f"모델 목록 조회 실패: {e}")
                sys.exit(1)

    # 대상 디렉토리 수집
    if args.slug:
        slugs = [s.strip() for s in args.slug.split(',')]
        dirs = [ARCH_DIR / s for s in slugs]
        for d in dirs:
            if not d.exists():
                print(f"디렉토리 없음: {d}")
                sys.exit(1)
    else:
        dirs = sorted(d for d in ARCH_DIR.iterdir() if d.is_dir())

    total = len(dirs)
    generated = 0
    skipped = 0
    failed = 0

    print(f"대상 아키텍처: {total}개 (모델: {model or 'auto'}, vLLM: {args.vllm_url})")
    print("=" * 60)

    for i, arch_dir in enumerate(dirs, 1):
        entry_json = arch_dir / 'entry.json'
        if not entry_json.exists():
            print(f"  [{i}/{total}] [SKIP] entry.json 없음: {arch_dir.name}")
            skipped += 1
            continue

        with open(entry_json, encoding='utf-8') as f:
            data = json.load(f)

        name = data.get('name', arch_dir.name)
        slug = arch_dir.name
        arch_type = classify_architecture(data)
        output_path = arch_dir / 'figures' / 'architecture.png'

        # 기존 이미지 체크
        if output_path.exists() and not args.force:
            print(f"  [{i}/{total}] [SKIP] 이미 존재: {slug}")
            skipped += 1
            continue

        prompt = build_prompt(data)

        if args.dry_run:
            print(f"  [{i}/{total}] [DRY-RUN] {name} (type={arch_type})")
            print(f"    출력: {output_path}")
            print(f"    프롬프트 길이: {len(prompt)}자")
            continue

        print(f"  [{i}/{total}] [GENERATE] {name} (type={arch_type})...")
        success = generate_figure_vllm(client, model, prompt, output_path,
                                       max_tokens=args.max_tokens)

        if success:
            generated += 1
            size_kb = output_path.stat().st_size / 1024
            print(f"    -> 저장: {output_path.name} ({size_kb:.0f}KB)")
        else:
            failed += 1
            print(f"    -> [FAIL] 생성 실패: {slug}")

        # 로컬이므로 최소 대기
        if i < total:
            time.sleep(0.5)

    print("=" * 60)
    print(f"완료: 생성 {generated}개, 스킵 {skipped}개, 실패 {failed}개")


if __name__ == '__main__':
    main()
