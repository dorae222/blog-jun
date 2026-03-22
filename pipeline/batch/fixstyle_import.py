"""
fixstyle 재처리 결과 DB 반영.

batch_rewrite_import.py 대비 차이점:
- custom_id가 source_path 형식 → source_path로 조회
- custom_id가 'post-{id}' 형식  → Post.id로 직접 조회
- should_archive=True 또는 quality_score < 3 → archived 처리 (보수적 기준)
- 포스트 없으면 → catalog.json에서 category 조회 → 새 Post CREATE
- 기존 get_or_create_tags(), make_unique_slug() 그대로 재사용

실행:
    python pipeline/batch_fixstyle_import.py
    python pipeline/batch_fixstyle_import.py --input pipeline/data/fixstyle_output.jsonl
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
from blog.models import Category, Post, Tag

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_INPUT_FILE = DATA_DIR / "fixstyle_output.jsonl"
CATALOG_FILE = DATA_DIR / "catalog.json"

# 카테고리 맵 (batch_import.py와 동일)
PARENT_CATEGORY_MAP = {
    "10.Cloud":   ("Cloud",            "cloud",       "☁️", "#FF9900"),
    "20.AI":      ("AI/ML",            "ai-ml",       "🤖", "#FF6F00"),
    "40.DEV":     ("Development",      "development", "💻", "#3776AB"),
    "30.Data":    ("Data Engineering", "data-eng",    "📊", "#336791"),
    "60.Project": ("Projects",         "projects",    "🚀", "#059669"),
}

SUB_CATEGORY_MAP = {
    "11.AWS":              ("AWS",           "aws",           "🟠", "#FF6600", "10.Cloud"),
    "12.Docker":           ("Docker",        "docker",        "🐳", "#2496ED", "10.Cloud"),
    "13.DevOps":           ("DevOps",        "devops",        "⚙️",  "#0DB7ED", "10.Cloud"),
    "29. LLM & GenAI":     ("LLM & GenAI",   "llm-genai",     "✨", "#7C3AED", "20.AI"),
    "23. DL Basic":        ("Deep Learning", "deep-learning", "🧠", "#EA4C89", "20.AI"),
    "28. Paper Review":    ("Paper Review",  "paper-review",  "📄", "#6366F1", "20.AI"),
}

# quality_score 이 값 미만이면 archived
ARCHIVE_SCORE_THRESHOLD = 3


def _load_catalog() -> dict:
    """catalog.json을 {source_path: item} 딕셔너리로 로드."""
    if not CATALOG_FILE.exists():
        return {}
    with open(CATALOG_FILE, encoding="utf-8") as f:
        return {item["path"]: item for item in json.load(f)}


def _ensure_categories() -> tuple[dict, dict]:
    """부모/서브 카테고리 get_or_create. (parent_cats, sub_cats) 반환."""
    parent_cats = {}
    for code, (name, slug, icon, color) in PARENT_CATEGORY_MAP.items():
        cat, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "code": code, "icon": icon, "color": color},
        )
        parent_cats[code] = cat

    sub_cats = {}
    for code, (name, slug, icon, color, parent_code) in SUB_CATEGORY_MAP.items():
        parent = parent_cats.get(parent_code)
        cat, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "code": code, "icon": icon, "color": color, "parent": parent},
        )
        sub_cats[code] = cat

    return parent_cats, sub_cats


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


def resolve_post(custom_id: str) -> Post | None:
    """
    custom_id 형식에 따라 포스트 조회:
    - 'post-{id}' → Post.id로 조회
    - 그 외         → source_path로 조회
    """
    if custom_id.startswith("post-"):
        try:
            post_id = int(custom_id[5:])
            return Post.objects.filter(id=post_id).first()
        except ValueError:
            pass
    return Post.objects.filter(source_path=custom_id).first()


def _create_post(custom_id: str, result: dict, catalog: dict, parent_cats: dict, sub_cats: dict, author) -> Post | None:
    """catalog.json 기반으로 새 Post 생성."""
    cat_info = catalog.get(custom_id, {})
    top_cat = cat_info.get("top_category", "")
    sub_code = cat_info.get("sub_category_code")
    post_category = sub_cats.get(sub_code) if sub_code else parent_cats.get(top_cat)

    raw_title = result.get("title", cat_info.get("title", custom_id))
    raw_slug = raw_title.lower().replace(" ", "-")[:300]
    raw_slug = "".join(c for c in raw_slug if c.isalnum() or c in "-_가-힣")
    if not raw_slug:
        raw_slug = custom_id.replace("/", "-").replace(".md", "")
    slug = make_unique_slug(raw_slug)

    def s(text):
        return (text or "").replace("\x00", "")

    post = Post.objects.create(
        title=s(raw_title),
        slug=slug,
        content=s(result.get("content", "")),
        summary=s(result.get("summary", ""))[:500],
        category=post_category,
        author=author,
        status="published",
        post_type=result.get("post_type", "article"),
        quality_score=float(result.get("quality_score", 5.0)),
        source_path=custom_id,
    )
    tag_objs = get_or_create_tags(result.get("tags", []))
    post.tags.set(tag_objs)
    return post


def import_fixstyle_results(input_file: Path):
    catalog = _load_catalog()
    parent_cats, sub_cats = _ensure_categories()
    author = User.objects.filter(is_superuser=True).first()

    updated = 0
    created = 0
    archived = 0
    errors = 0

    with open(input_file, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                print(f"[L{line_num}] JSON 파싱 오류")
                errors += 1
                continue

            custom_id = item.get("custom_id", "")

            # 배치 API 응답 형식 확인
            if item.get("response", {}).get("status_code") != 200:
                code = item.get("response", {}).get("status_code", "N/A")
                print(f"[L{line_num}] {custom_id[:50]} — HTTP {code}")
                errors += 1
                continue

            try:
                result = json.loads(
                    item["response"]["body"]["choices"][0]["message"]["content"]
                )
            except (KeyError, json.JSONDecodeError) as e:
                print(f"[L{line_num}] {custom_id[:50]} — 결과 파싱 오류: {e}")
                errors += 1
                continue

            # 아카이브 판정 (포스트 조회 전에 먼저 확인)
            should_archive = result.get("should_archive", False)
            quality_score = float(result.get("quality_score", 5.0))

            post = resolve_post(custom_id)

            if post is None:
                # DB에 없으면 새로 생성 (전체 배치 후 DB 초기화 시나리오)
                if should_archive or quality_score < ARCHIVE_SCORE_THRESHOLD:
                    reason = result.get("archive_reason", "")
                    print(f"[SKIP-ARCHIVE] {custom_id[:50]} (score={quality_score:.1f})")
                    archived += 1
                    continue
                if not author:
                    print(f"[L{line_num}] superuser 없음 — 포스트 생성 불가")
                    errors += 1
                    continue
                try:
                    post = _create_post(custom_id, result, catalog, parent_cats, sub_cats, author)
                    print(f"[CREATE] {post.id}: {post.title[:50]}")
                    created += 1
                except Exception as e:
                    print(f"[L{line_num}] {custom_id[:50]} — 생성 오류: {e}")
                    errors += 1
                continue

            if should_archive or quality_score < ARCHIVE_SCORE_THRESHOLD:
                reason = result.get("archive_reason", "")
                print(
                    f"[ARCHIVE] {post.id}: {post.title[:50]} "
                    f"(score={quality_score:.1f}, reason={reason[:60]})"
                )
                post.status = "archived"
                post.save(update_fields=["status"])
                archived += 1
                continue

            # 기존 포스트 업데이트
            post.title = result["title"]
            post.content = result["content"]
            post.summary = result.get("summary", "")[:500]
            post.quality_score = quality_score
            post.save(update_fields=["title", "content", "summary", "quality_score", "updated_at"])

            tag_objs = get_or_create_tags(result.get("tags", []))
            post.tags.set(tag_objs)
            updated += 1

    print(f"\n=== Fixstyle Import 완료 ===")
    print(f"Updated:  {updated}")
    print(f"Created:  {created}")
    print(f"Archived: {archived}")
    print(f"Errors:   {errors}")


def main():
    parser = argparse.ArgumentParser(description="fixstyle 결과 DB 반영")
    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_INPUT_FILE),
        help="fixstyle 결과 JSONL 파일 경로",
    )
    args = parser.parse_args()
    input_file = Path(args.input)
    if not input_file.exists():
        print(f"파일을 찾을 수 없습니다: {input_file}")
        return
    import_fixstyle_results(input_file)


if __name__ == "__main__":
    main()
