"""
재작성 결과 DB 반영 스크립트.

- source_path로 기존 포스트를 찾아 UPDATE
- should_archive=true 또는 quality_score < 4 → status='archived'
- 매핑 없으면 신규 생성 (batch_import.py 로직 동일)

실행:
    python pipeline/batch_rewrite_import.py
    python pipeline/batch_rewrite_import.py --input pipeline/data/rewrite_output.jsonl
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
DEFAULT_OUTPUT_FILE = DATA_DIR / "rewrite_output.jsonl"
CATALOG_FILE = DATA_DIR / "catalog.json"

CATEGORY_MAP = {
    "10.Cloud":      ("Cloud", "cloud", "#FF9900"),
    "20.AI":         ("AI/ML", "ai-ml", "#FF6F00"),
    "30.Data":       ("Data Engineering", "data-engineering", "#336791"),
    "40.DEV":        ("Development", "development", "#3776AB"),
    "50.Foundation": ("Foundation", "foundation", "#6366F1"),
    "60.Project":    ("Projects", "projects", "#059669"),
    "70.Program":    ("Programs", "programs", "#EC4899"),
}


def make_unique_slug(base_slug: str) -> str:
    slug = base_slug[:290]
    if not Post.objects.filter(slug=slug).exists():
        return slug
    for i in range(1, 10000):
        candidate = f"{slug[:285]}-{i}"
        if not Post.objects.filter(slug=candidate).exists():
            return candidate
    raise ValueError(f"슬러그 생성 실패: {base_slug}")


def build_slug(title: str, path: str) -> str:
    slug = slugify(title, allow_unicode=True)[:290]
    if not slug:
        slug = path.replace("/", "-").replace(".md", "")[:290]
    return slug


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


def import_rewrite_results(output_file: Path):
    with open(CATALOG_FILE) as f:
        catalog = {item["path"]: item for item in json.load(f)}

    author = User.objects.filter(is_superuser=True).first()
    if not author:
        print("슈퍼유저가 없습니다. 먼저 createsuperuser를 실행하세요.")
        return

    # 카테고리 생성/조회
    categories = {}
    for code, (name, slug, color) in CATEGORY_MAP.items():
        cat, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "code": code, "color": color},
        )
        categories[code] = cat

    updated = 0
    archived = 0
    created = 0
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
                errors += 1
                continue

            try:
                result = json.loads(
                    item["response"]["body"]["choices"][0]["message"]["content"]
                )
            except (KeyError, json.JSONDecodeError):
                errors += 1
                continue

            # source_path로 기존 포스트 조회
            post = Post.objects.filter(source_path=custom_id).first()

            if post is None:
                # 신규 생성
                cat_info = catalog.get(custom_id, {})
                top_cat = cat_info.get("top_category", "")
                base_slug = build_slug(result.get("title", ""), custom_id)
                slug = make_unique_slug(base_slug)

                post = Post.objects.create(
                    title=result.get("title", custom_id),
                    slug=slug,
                    content=result.get("content", ""),
                    summary=result.get("summary", "")[:500],
                    category=categories.get(top_cat),
                    author=author,
                    status="published",
                    post_type="article",
                    quality_score=result.get("quality_score", 5.0),
                    source_path=custom_id,
                )
                tag_objs = get_or_create_tags(result.get("tags", []))
                post.tags.set(tag_objs)
                created += 1
                continue

            # 아카이브 판정
            should_archive = result.get("should_archive", False)
            quality_score = result.get("quality_score", 5.0)
            if should_archive or quality_score < 4:
                post.status = "archived"
                post.save(update_fields=["status"])
                archived += 1
                continue

            # 업데이트
            post.title = result["title"]
            post.content = result["content"]
            post.summary = result.get("summary", "")[:500]
            post.quality_score = quality_score
            post.save(update_fields=["title", "content", "summary", "quality_score", "updated_at"])

            tag_objs = get_or_create_tags(result.get("tags", []))
            post.tags.set(tag_objs)
            updated += 1

    print(f"\n=== Rewrite Import 완료 ===")
    print(f"Updated:  {updated}")
    print(f"Created:  {created}")
    print(f"Archived: {archived}")
    print(f"Errors:   {errors}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=str,
        default=str(DEFAULT_OUTPUT_FILE),
        help="재작성 결과 JSONL 파일 경로",
    )
    args = parser.parse_args()
    output_file = Path(args.input)
    if not output_file.exists():
        print(f"파일을 찾을 수 없습니다: {output_file}")
        return
    import_rewrite_results(output_file)


if __name__ == "__main__":
    main()
