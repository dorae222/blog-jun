"""
Import batch-processed results into Django database.
Run as: python manage.py shell < pipeline/batch_import.py
Or as a management command.

Updated for Notion HTML pipeline (카테고리 매핑 재구축).
"""
import json
import sys
import os
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from django.contrib.auth.models import User
from blog.models import Post, Category, Tag, Series, PostLink

DATA_DIR = Path(__file__).parent / "data"
BATCH_OUTPUT_FILE = DATA_DIR / "batch_output.jsonl"
CATALOG_FILE = DATA_DIR / "catalog.json"

# 부모 카테고리: Cloud + Data Engineering만 유지
PARENT_CATEGORY_MAP = {
    "10.Cloud": ("Cloud",           "cloud",    "☁️", "#FF9900"),
    "30.Data":  ("Data Engineering", "data-eng", "📊", "#336791"),
}

# 서브카테고리: Cloud + Data Engineering 하위만 유지
# (name, slug, icon, color, parent_code)
SUB_CATEGORY_MAP = {
    # Cloud
    "11.AWS":    ("AWS",    "aws",    "🟠", "#FF6600", "10.Cloud"),
    "12.Docker": ("Docker", "docker", "🐳", "#2496ED", "10.Cloud"),
    "13.DevOps": ("DevOps", "devops", "⚙️", "#0DB7ED", "10.Cloud"),
    "14.LXD":    ("LXD",    "lxd",    "lxd", "#E95420", "10.Cloud"),
    # Data Engineering
    "Hadoop":           ("Hadoop",           "hadoop",         "🐘", "#FF6F00", "30.Data"),
    "Spark":            ("Spark",            "spark",          "⚡", "#E25A1C", "30.Data"),
    "Hive":             ("Hive",             "hive",           "🐝", "#FDEE21", "30.Data"),
    "Pig":              ("Pig",              "pig",            "🐷", "#FCA5A5", "30.Data"),
    "SQOOP":            ("SQOOP",            "sqoop",          "🔄", "#60A5FA", "30.Data"),
    "Big Data Intro":   ("Big Data Intro",   "big-data-intro", "📊", "#8B5CF6", "30.Data"),
    "Data Visualization": ("Data Visualization", "data-viz",   "📈", "#34D399", "30.Data"),
    "Setting":          ("Setting",          "data-setting",   "⚙️",  "#9CA3AF", "30.Data"),
    "Troubleshooting":  ("Troubleshooting",  "troubleshooting", "🔧", "#EF4444", "30.Data"),
}


def import_results():
    # Load catalog for metadata
    with open(CATALOG_FILE) as f:
        catalog = {item["path"]: item for item in json.load(f)}

    # Load batch results
    results = {}
    with open(BATCH_OUTPUT_FILE) as f:
        for line in f:
            data = json.loads(line)
            custom_id = data["custom_id"]
            if data["response"]["status_code"] == 200:
                content = data["response"]["body"]["choices"][0]["message"]["content"]
                try:
                    results[custom_id] = json.loads(content)
                except json.JSONDecodeError:
                    print(f"  Skipping {custom_id}: invalid JSON")

    # Get or create author
    author = User.objects.filter(is_superuser=True).first()
    if not author:
        print("No superuser found! Create one first.")
        return

    # 1단계: 부모 카테고리 생성
    parent_cats = {}
    for code, (name, slug, icon, color) in PARENT_CATEGORY_MAP.items():
        cat, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "code": code, "icon": icon, "color": color},
        )
        parent_cats[code] = cat

    # 2단계: 서브카테고리 생성 (parent 지정)
    sub_cats = {}
    for subcat_name, (name, slug, icon, color, parent_code) in SUB_CATEGORY_MAP.items():
        parent = parent_cats.get(parent_code)
        cat, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "code": subcat_name, "icon": icon, "color": color, "parent": parent},
        )
        sub_cats[subcat_name] = cat

    created = 0
    skipped = 0

    for path, result in results.items():
        cat_info = catalog.get(path, {})
        parent_code = cat_info.get("parent_code", "")
        subcategory = cat_info.get("subcategory", "")

        # Slug 생성
        slug = result.get("title", "").lower().replace(" ", "-")[:300]
        slug = "".join(c for c in slug if c.isalnum() or c in "-_가-힣")
        if not slug:
            slug = path.replace("/", "-").replace(".html", "")

        if Post.objects.filter(slug=slug).exists():
            skipped += 1
            continue

        # Create tags (batch output + properties 메타데이터)
        tag_names = list(result.get("tags", []))

        # Properties에서 기술 스택 태그 추가 (dir1 포트폴리오)
        properties = cat_info.get("properties", {})
        if isinstance(properties, dict):
            tech_stack = properties.get("기술 스택", [])
            if isinstance(tech_stack, list):
                for tech in tech_stack:
                    tag_slug_candidate = tech.lower().replace(" ", "-")
                    if tag_slug_candidate not in [t.lower().replace(" ", "-") for t in tag_names]:
                        tag_names.append(tech)

        tag_objects = []
        for tag_name in tag_names:
            tag_slug = tag_name.lower().replace(" ", "-")[:100]
            tag, _ = Tag.objects.get_or_create(
                slug=tag_slug,
                defaults={"name": tag_name},
            )
            tag_objects.append(tag)

        # 카테고리 결정: 서브카테고리 > 부모 카테고리
        post_category = sub_cats.get(subcategory) if subcategory else parent_cats.get(parent_code)
        if not post_category:
            post_category = parent_cats.get(parent_code)

        def s(text):
            """Strip NUL bytes that PostgreSQL rejects."""
            return (text or "").replace("\x00", "")

        post = Post.objects.create(
            title=s(result.get("title", cat_info.get("title", path))),
            slug=slug,
            content=s(result.get("content", "")),
            summary=s(result.get("summary", ""))[:500],
            category=post_category,
            author=author,
            status="published",
            post_type=result.get("post_type", "article"),
            quality_score=result.get("quality_score", 5.0),
            source_path=path,
        )
        post.tags.set(tag_objects)

        # 표지 이미지 업로드 (covers/{slug}/cover.png 존재 시)
        cover_path = DATA_DIR / "covers" / slug / "cover.png"
        if cover_path.exists():
            from django.core.files import File
            with open(cover_path, "rb") as cf:
                post.cover_image.save(f"{slug}_cover.png", File(cf), save=True)
            print(f"  Cover image uploaded for {slug}")

        created += 1

    print(f"Imported {created} posts, skipped {skipped}")

    # PostLink 생성: content_links가 있는 결과에서 관계 추출
    links_created = 0
    for path, result in results.items():
        content_links = result.get('content_links', [])
        if not content_links:
            continue

        slug = result.get("title", "").lower().replace(" ", "-")[:300]
        slug = "".join(c for c in slug if c.isalnum() or c in "-_가-힣")
        from_post = Post.objects.filter(slug=slug).first()
        if not from_post:
            continue

        for link_data in content_links:
            target = link_data.get('target', '')
            if not target:
                continue
            to_post = Post.objects.filter(title__icontains=target).first()
            if to_post and to_post != from_post:
                _, created_link = PostLink.objects.get_or_create(
                    from_post=from_post, to_post=to_post,
                    defaults={'link_text': target}
                )
                if created_link:
                    links_created += 1

    if links_created:
        print(f"Created {links_created} post links")


if __name__ == "__main__":
    import_results()
