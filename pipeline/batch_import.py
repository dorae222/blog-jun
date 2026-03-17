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
from blog.models import Post, Category, Tag, Series

DATA_DIR = Path(__file__).parent / "data"
BATCH_OUTPUT_FILE = DATA_DIR / "batch_output.jsonl"
CATALOG_FILE = DATA_DIR / "catalog.json"

# 부모 카테고리: 4개 (Cloud 제외 — Obsidian 볼트에서 유지)
PARENT_CATEGORY_MAP = {
    "20.AI":      ("AI/ML",            "ai-ml",       "🤖", "#FF6F00"),
    "30.Data":    ("Data Engineering",  "data-eng",    "📊", "#336791"),
    "40.DEV":     ("Development",      "development", "💻", "#3776AB"),
    "60.Project": ("Projects",         "projects",    "🚀", "#059669"),
}

# 서브카테고리: Notion 폴더 기반 매핑
# (name, slug, icon, color, parent_code)
SUB_CATEGORY_MAP = {
    # AI/ML
    "Deep Learning":    ("Deep Learning",    "deep-learning",    "🧠", "#EA4C89", "20.AI"),
    "Machine Learning": ("Machine Learning", "machine-learning", "📈", "#10B981", "20.AI"),
    "Statistics":       ("Statistics",       "statistics",       "📊", "#6366F1", "20.AI"),
    "Time Series":      ("Time Series",      "time-series",      "📉", "#F59E0B", "20.AI"),
    "Paper Review":     ("Paper Review",     "paper-review",     "📄", "#6366F1", "20.AI"),
    # Data Engineering
    "Hadoop":           ("Hadoop",           "hadoop",           "🐘", "#FF6F00", "30.Data"),
    "Spark":            ("Spark",            "spark",            "⚡", "#E25A1C", "30.Data"),
    "Hive":             ("Hive",             "hive",             "🐝", "#FDEE21", "30.Data"),
    "Pig":              ("Pig",              "pig",              "🐷", "#FCA5A5", "30.Data"),
    "SQOOP":            ("SQOOP",            "sqoop",            "🔄", "#60A5FA", "30.Data"),
    "Big Data Intro":   ("Big Data Intro",   "big-data-intro",   "📊", "#8B5CF6", "30.Data"),
    "Data Visualization": ("Data Visualization", "data-viz",     "📈", "#34D399", "30.Data"),
    "Setting":          ("Setting",          "data-setting",     "⚙️",  "#9CA3AF", "30.Data"),
    "Troubleshooting":  ("Troubleshooting",  "troubleshooting",  "🔧", "#EF4444", "30.Data"),
    # Development
    "Backend":          ("Backend",          "backend",          "🖥️", "#3776AB", "40.DEV"),
    "Frontend":         ("Frontend",         "frontend",         "🎨", "#61DAFB", "40.DEV"),
    "Database":         ("Database",         "database",         "🗄️", "#336791", "40.DEV"),
    "Linux":            ("Linux",            "linux",            "🐧", "#FCC624", "40.DEV"),
    "Git":              ("Git",              "git",              "🔀", "#F05032", "40.DEV"),
    "Design":           ("Design",           "design",           "🎨", "#A259FF", "40.DEV"),
    # Projects
    "AI Projects":       ("AI Projects",       "ai-projects",       "🤖", "#7C3AED", "60.Project"),
    "Business Projects": ("Business Projects", "business-projects", "💼", "#059669", "60.Project"),
    "Data Projects":     ("Data Projects",     "data-projects",     "📊", "#2563EB", "60.Project"),
    "2023 Summer":       ("2023 Summer",       "2023-summer",       "☀️", "#F59E0B", "60.Project"),
    "2023 Semester":     ("2023 Semester",      "2023-semester",     "📚", "#8B5CF6", "60.Project"),
    "General":           ("General",            "general",           "📁", "#6B7280", "60.Project"),
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
        created += 1

    print(f"Imported {created} posts, skipped {skipped}")


if __name__ == "__main__":
    import_results()
