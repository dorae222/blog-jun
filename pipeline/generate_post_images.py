#!/usr/bin/env python3
"""
DALL-E를 사용한 Paper Review 포스트 대표 이미지 생성 스크립트

사용법:
  python generate_post_images.py                      # 모든 paper_review 포스트
  python generate_post_images.py --paper-id 5         # 특정 포스트만
  python generate_post_images.py --dry-run             # 미리보기
  python generate_post_images.py --output-dir ./imgs   # 출력 디렉토리 지정
"""
import os
import sys
import argparse
import requests
from pathlib import Path

# Django 설정
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

import django
django.setup()

from blog.models import Post
from openai import OpenAI


DEFAULT_OUTPUT_DIR = Path(__file__).parent / 'data' / 'images'


def generate_prompt(post):
    """포스트 제목과 요약으로 DALL-E 프롬프트 생성"""
    return (
        f"A clean, modern technical illustration for a blog post about: {post.title}. "
        f"Summary: {post.summary[:200] if post.summary else 'AI research paper review'}. "
        "Style: minimalist, professional, tech blog hero image, abstract geometric patterns, "
        "gradient colors, no text, no watermarks, 16:9 aspect ratio."
    )


def generate_images(paper_id=None, dry_run=False, output_dir=None):
    output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key and not dry_run:
        print("OPENAI_API_KEY 환경 변수를 설정하세요.")
        sys.exit(1)

    client = OpenAI(api_key=api_key) if not dry_run else None

    # 대상 포스트 조회
    qs = Post.objects.filter(post_type='paper_review')
    if paper_id:
        qs = qs.filter(id=paper_id)

    posts = list(qs)
    if not posts:
        print("대상 포스트가 없습니다.")
        return

    print(f"대상 포스트: {len(posts)}개")

    for post in posts:
        output_path = output_dir / f"{post.slug}.png"
        if output_path.exists():
            print(f"  [SKIP] 이미 존재: {output_path.name}")
            continue

        prompt = generate_prompt(post)

        if dry_run:
            print(f"  [DRY-RUN] {post.title}")
            print(f"    Prompt: {prompt[:100]}...")
            continue

        try:
            print(f"  [GENERATE] {post.title}...")
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1792x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url

            # 이미지 다운로드
            img_data = requests.get(image_url, timeout=60).content
            with open(output_path, 'wb') as f:
                f.write(img_data)
            print(f"    -> 저장: {output_path}")

        except Exception as e:
            print(f"    [ERROR] {post.title}: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DALL-E 기반 포스트 이미지 생성')
    parser.add_argument('--paper-id', type=int, help='특정 포스트 ID')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    parser.add_argument('--output-dir', type=str, help='출력 디렉토리 (기본: pipeline/data/images/)')
    args = parser.parse_args()

    generate_images(
        paper_id=args.paper_id,
        dry_run=args.dry_run,
        output_dir=args.output_dir,
    )
