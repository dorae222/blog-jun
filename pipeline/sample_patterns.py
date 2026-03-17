"""
DB 포스트를 패턴으로 분류하고 패턴별 1개씩 샘플링.

분류 기준:
- post_type: article / tutorial / til / paper_review / project
- has_math: content에 $ 포함 여부
- has_images: content에 ![ 포함 여부
- has_code: content에 ``` 포함 여부

출력: pipeline/data/sample_posts.json
형식: [{"pattern": "tutorial|math|code", "post_id": 123, "source_path": "..."}, ...]

실행:
    python pipeline/sample_patterns.py
    python pipeline/sample_patterns.py --limit 3  # 패턴당 최대 3개
"""
import argparse
import json
import sys
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from blog.models import Post

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_FILE = DATA_DIR / "sample_posts.json"


def classify_post(post) -> str:
    """포스트를 분류하여 패턴 문자열 반환. 예: 'tutorial|math|code'"""
    content = post.content or ""
    parts = [post.post_type or "article"]

    if "$" in content:
        parts.append("math")
    if "![" in content:
        parts.append("images")
    if "```" in content:
        parts.append("code")

    return "|".join(parts)


def sample_patterns(per_pattern_limit: int = 1) -> list[dict]:
    posts = (
        Post.objects.filter(status="published")
        .only("id", "title", "content", "source_path", "post_type")
    )

    # 패턴별 샘플 수집
    pattern_buckets: dict[str, list[dict]] = {}

    for post in posts:
        pattern = classify_post(post)
        if pattern not in pattern_buckets:
            pattern_buckets[pattern] = []

        if len(pattern_buckets[pattern]) < per_pattern_limit:
            pattern_buckets[pattern].append({
                "pattern":     pattern,
                "post_id":     post.id,
                "title":       post.title[:80] if post.title else "",
                "source_path": post.source_path or "",
            })

    # 모든 버킷 합치기
    samples = []
    for pattern, items in sorted(pattern_buckets.items()):
        samples.extend(items)

    return samples


def main():
    parser = argparse.ArgumentParser(description="포스트 패턴 분류 + 샘플링")
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="패턴당 최대 샘플 수 (기본: 1)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help="출력 JSON 파일 경로",
    )
    args = parser.parse_args()

    samples = sample_patterns(per_pattern_limit=args.limit)

    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)

    print(f"\n=== Pattern Sampling 완료 ===")
    print(f"총 샘플: {len(samples)}건 → {dest}")
    print()

    # 패턴별 요약
    patterns_seen = {}
    for s in samples:
        p = s["pattern"]
        patterns_seen.setdefault(p, []).append(s["post_id"])

    for pattern, ids in sorted(patterns_seen.items()):
        print(f"  [{pattern}] → post_id: {ids}")

    print(f"\nNext:")
    print(f"  python pipeline/batch_fixstyle.py \\")
    print(f"    --sample {dest} \\")
    print(f"    --output pipeline/data/fixstyle_sample_input.jsonl")


if __name__ == "__main__":
    main()
