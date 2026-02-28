"""
Import batch-processed results into Django database.
Run as: python manage.py shell < pipeline/batch_import.py
Or as a management command.
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

CATEGORY_MAP = {
    "10.Cloud": ("Cloud", "cloud", "☁️", "#FF9900"),
    "20.AI": ("AI/ML", "ai-ml", "🤖", "#FF6F00"),
    "30.Data": ("Data Engineering", "data-engineering", "📊", "#336791"),
    "40.DEV": ("Development", "development", "💻", "#3776AB"),
    "50.Foundation": ("Foundation", "foundation", "📐", "#6366F1"),
    "60.Project": ("Projects", "projects", "🚀", "#059669"),
    "70.Program": ("Programs", "programs", "🎓", "#EC4899"),
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

    # Create categories
    categories = {}
    for code, (name, slug, icon, color) in CATEGORY_MAP.items():
        cat, _ = Category.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "code": code, "icon": icon, "color": color},
        )
        categories[code] = cat

    created = 0
    skipped = 0

    for path, result in results.items():
        cat_info = catalog.get(path, {})
        top_cat = cat_info.get("top_category", "")

        # Skip if post already exists
        slug = result.get("title", "").lower().replace(" ", "-")[:300]
        slug = "".join(c for c in slug if c.isalnum() or c in "-_가-힣")
        if not slug:
            slug = path.replace("/", "-").replace(".md", "")

        if Post.objects.filter(slug=slug).exists():
            skipped += 1
            continue

        # Create tags
        tag_objects = []
        for tag_name in result.get("tags", []):
            tag_slug = tag_name.lower().replace(" ", "-")[:100]
            tag, _ = Tag.objects.get_or_create(
                slug=tag_slug,
                defaults={"name": tag_name},
            )
            tag_objects.append(tag)

        post = Post.objects.create(
            title=result.get("title", cat_info.get("title", path)),
            slug=slug,
            content=result.get("content", ""),
            summary=result.get("summary", "")[:500],
            category=categories.get(top_cat),
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
