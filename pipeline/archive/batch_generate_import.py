"""
생성된 30건 콘텐츠 DB 삽입 스크립트.

- 모든 포스트를 status='draft'로 삽입 (검토 후 수동 publish)
- category_slug로 카테고리 매핑

실행:
    python pipeline/batch_generate_import.py
    python pipeline/batch_generate_import.py --input pipeline/data/generate_output.jsonl
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

from django.contrib.auth.models import User
from django.utils.text import slugify
from blog.models import Post, Category, Tag

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_OUTPUT_FILE = DATA_DIR / "generate_output.jsonl"


def make_unique_slug(base_slug: str) -> str:
    slug = base_slug[:290]
    if not Post.objects.filter(slug=slug).exists():
        return slug
    for i in range(1, 10000):
        candidate = f"{slug[:285]}-{i}"
        if not Post.objects.filter(slug=candidate).exists():
            return candidate
    raise ValueError(f"슬러그 생성 실패: {base_slug}")


def get_or_create_tags(tag_names: list) -> list:
    tag_objects = []
    for name in tag_names:
        tag_slug = name.lower().replace(" ", "-")[:100]
        tag, _ = Tag.objects.get_or_create(
            slug=tag_slug,
            defaults={"name": name},
        )
        tag_objects.append(tag)
    return tag_objects


def import_generate_results(output_file: Path):
    author = User.objects.filter(is_superuser=True).first()
    if not author:
        print("슈퍼유저가 없습니다. 먼저 createsuperuser를 실행하세요.")
        return

    created = 0
    skipped = 0
    errors = 0

    with open(output_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                errors += 1
                continue

            custom_id = item["custom_id"]

            if item.get("response", {}).get("status_code") != 200:
                print(f"  Error response for {custom_id}: status {item.get('response', {}).get('status_code')}")
                errors += 1
                continue

            try:
                result = json.loads(
                    item["response"]["body"]["choices"][0]["message"]["content"]
                )
            except (KeyError, json.JSONDecodeError):
                errors += 1
                continue

            title = result.get("title", "")
            if not title:
                errors += 1
                continue

            base_slug = slugify(title, allow_unicode=True)[:290]
            if not base_slug:
                base_slug = custom_id
            slug = make_unique_slug(base_slug)

            # category_slug로 카테고리 조회
            category_slug = result.get("category_slug", "")
            category = Category.objects.filter(slug=category_slug).first()

            post = Post.objects.create(
                title=title,
                slug=slug,
                content=result.get("content", ""),
                summary=result.get("summary", "")[:500],
                category=category,
                author=author,
                status="draft",
                post_type="tutorial",
                quality_score=result.get("quality_score", 7.0),
                source_path=f"generated/{custom_id}",
            )
            tag_objs = get_or_create_tags(result.get("tags", []))
            post.tags.set(tag_objs)
            created += 1

    print(f"\n=== Generate Import 완료 ===")
    print(f"Created (draft): {created}")
    print(f"Skipped: {skipped}")
    print(f"Errors:  {errors}")
    print(f"\nAdmin에서 draft 포스트를 검토 후 publish 하세요.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=str,
        default=str(DEFAULT_OUTPUT_FILE),
        help="생성 결과 JSONL 파일 경로",
    )
    args = parser.parse_args()
    output_file = Path(args.input)
    if not output_file.exists():
        print(f"파일을 찾을 수 없습니다: {output_file}")
        return
    import_generate_results(output_file)


if __name__ == "__main__":
    main()
