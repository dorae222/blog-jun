#!/usr/bin/env python3
"""
Anthropic Message Batches API를 사용한 아키텍처 다이어그램 일괄 생성

3단계로 동작:
  1) submit  - 배치 요청 제출 (기존 figure 없는 것만)
  2) poll    - 배치 완료 대기
  3) process - 결과 다운로드 → SVG 추출 → PNG 변환

사용법:
  python batch_generate_figures.py submit                    # 배치 제출
  python batch_generate_figures.py poll <batch_id>           # 완료 대기
  python batch_generate_figures.py process <batch_id>        # 결과 처리
  python batch_generate_figures.py all                       # 전체 자동 (submit→poll→process)
  python batch_generate_figures.py all --force               # 기존 이미지 포함 전체 재생성
"""
import json
import os
import re
import sys
import time
import argparse
from pathlib import Path

import anthropic
import cairosvg

# ── 설정 ──────────────────────────────────────────────────────────────
ARCH_DIR = Path(__file__).parent / 'data' / 'architectures_written'
DEFAULT_MODEL = 'claude-opus-4-6'
OUTPUT_WIDTH = 1920
POLL_INTERVAL = 30  # 초

# generate_arch_figures.py에서 프롬프트 재사용
from generate_arch_figures import (
    SYSTEM_PROMPT, build_prompt, extract_svg, classify_architecture
)


def collect_targets(force: bool = False, slug: str | None = None) -> list[tuple[str, dict]]:
    """figure 생성이 필요한 아키텍처 수집"""
    if slug:
        slugs = [s.strip() for s in slug.split(',')]
        dirs = [ARCH_DIR / s for s in slugs]
    else:
        dirs = sorted(d for d in ARCH_DIR.iterdir() if d.is_dir())

    targets = []
    for arch_dir in dirs:
        entry_json = arch_dir / 'entry.json'
        if not entry_json.exists():
            continue

        output_path = arch_dir / 'figures' / 'architecture.png'
        if output_path.exists() and not force:
            continue

        with open(entry_json, encoding='utf-8') as f:
            data = json.load(f)
        targets.append((arch_dir.name, data))

    return targets


def submit_batch(client: anthropic.Anthropic, targets: list[tuple[str, dict]],
                 model: str) -> str:
    """배치 요청 제출, batch_id 반환"""
    requests = []
    for slug, data in targets:
        prompt = build_prompt(data)
        requests.append({
            "custom_id": slug,
            "params": {
                "model": model,
                "max_tokens": 16000,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
        })

    print(f"배치 제출: {len(requests)}개 요청 (모델: {model})")
    batch = client.messages.batches.create(requests=requests)
    print(f"배치 ID: {batch.id}")
    print(f"상태: {batch.processing_status}")
    return batch.id


def poll_batch(client: anthropic.Anthropic, batch_id: str) -> bool:
    """배치 완료까지 폴링"""
    print(f"배치 {batch_id} 완료 대기 중...")
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        total = counts.processing + counts.succeeded + counts.errored + counts.canceled + counts.expired
        done = counts.succeeded + counts.errored + counts.canceled + counts.expired

        print(f"  진행: {done}/{total} (성공: {counts.succeeded}, "
              f"에러: {counts.errored}, 처리중: {counts.processing})")

        if batch.processing_status == "ended":
            print(f"배치 완료! 성공: {counts.succeeded}, 에러: {counts.errored}")
            return counts.succeeded > 0

        time.sleep(POLL_INTERVAL)


def process_batch(client: anthropic.Anthropic, batch_id: str) -> None:
    """배치 결과 다운로드 → SVG 추출 → PNG 변환"""
    print(f"배치 {batch_id} 결과 처리 중...")

    generated = 0
    failed = 0

    for result in client.messages.batches.results(batch_id):
        slug = result.custom_id
        output_dir = ARCH_DIR / slug / 'figures'
        output_path = output_dir / 'architecture.png'
        svg_path = output_dir / 'architecture.svg'

        if result.result.type == "succeeded":
            message = result.result.message
            text = message.content[0].text
            svg_code = extract_svg(text)

            if not svg_code:
                print(f"  [{slug}] SVG 추출 실패")
                failed += 1
                continue

            output_dir.mkdir(parents=True, exist_ok=True)

            # SVG 저장
            svg_path.write_text(svg_code, encoding='utf-8')

            # SVG → PNG 변환
            try:
                cairosvg.svg2png(
                    bytestring=svg_code.encode('utf-8'),
                    write_to=str(output_path),
                    output_width=OUTPUT_WIDTH,
                    background_color='white',
                )
                size_kb = output_path.stat().st_size / 1024
                print(f"  [{slug}] 생성 완료 ({size_kb:.0f}KB)")
                generated += 1
            except Exception as e:
                print(f"  [{slug}] PNG 변환 실패: {e}")
                failed += 1
        else:
            error_type = result.result.type
            print(f"  [{slug}] 배치 에러: {error_type}")
            failed += 1

    print("=" * 60)
    print(f"완료: 생성 {generated}개, 실패 {failed}개")


def main():
    parser = argparse.ArgumentParser(description='Batch API 기반 아키텍처 다이어그램 일괄 생성')
    parser.add_argument('command', choices=['submit', 'poll', 'process', 'all'],
                        help='실행 단계')
    parser.add_argument('batch_id', nargs='?', help='배치 ID (poll/process 시 필수)')
    parser.add_argument('--slug', type=str, help='특정 아키텍처만')
    parser.add_argument('--force', action='store_true', help='기존 이미지 덮어쓰기')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL,
                        help=f'Claude 모델 (기본: {DEFAULT_MODEL})')
    args = parser.parse_args()

    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY', ''))

    if args.command == 'submit':
        targets = collect_targets(force=args.force, slug=args.slug)
        if not targets:
            print("생성할 figure가 없습니다 (전부 이미 존재)")
            return
        submit_batch(client, targets, args.model)

    elif args.command == 'poll':
        if not args.batch_id:
            print("batch_id를 지정하세요: python batch_generate_figures.py poll <batch_id>")
            sys.exit(1)
        poll_batch(client, args.batch_id)

    elif args.command == 'process':
        if not args.batch_id:
            print("batch_id를 지정하세요: python batch_generate_figures.py process <batch_id>")
            sys.exit(1)
        process_batch(client, args.batch_id)

    elif args.command == 'all':
        targets = collect_targets(force=args.force, slug=args.slug)
        if not targets:
            print("생성할 figure가 없습니다 (전부 이미 존재)")
            return
        print(f"대상: {len(targets)}개 아키텍처")
        print("=" * 60)
        batch_id = submit_batch(client, targets, args.model)
        poll_batch(client, batch_id)
        process_batch(client, batch_id)


if __name__ == '__main__':
    main()
