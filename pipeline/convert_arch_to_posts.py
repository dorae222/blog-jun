"""
ArchitectureEntry → Post 변환 스크립트.
content.json이 존재하면 우선 사용, 없으면 entry.json에서 자동 생성.

Usage:
  python pipeline/convert_arch_to_posts.py              # 실제 변환
  python pipeline/convert_arch_to_posts.py --dry-run    # 미리보기
"""
import json
import sys
import os
import argparse
from pathlib import Path

# Docker 환경: /app/config가 존재하면 backend=/app, 아니면 로컬 경로
_docker_backend = Path("/app")
_local_backend = Path(__file__).resolve().parent.parent / "backend"
BACKEND_DIR = _docker_backend if (_docker_backend / "config").is_dir() else _local_backend

_docker_data = Path("/pipeline/data/architectures_written")
_local_data = Path(__file__).resolve().parent / "data" / "architectures_written"
ARCH_DATA_DIR = _docker_data if _docker_data.is_dir() else _local_data

sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev" if BACKEND_DIR == _local_backend else "config.settings.prod")

import django
django.setup()

from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from blog.models import Post, Category, Tag, ArchitectureEntry


def build_markdown(entry):
    """ArchitectureEntry에서 기본 마크다운 아티클 생성 (content.json 없을 때 fallback)."""
    sections = []
    sections.append(f"# {entry.name}\n")

    meta_lines = []
    if entry.organization:
        meta_lines.append(f"**Organization:** {entry.organization}")
    if entry.release_date:
        meta_lines.append(f"**Release:** {entry.release_date}")
    if entry.param_scale:
        meta_lines.append(f"**Parameters:** {entry.param_scale}")
    if entry.context_length:
        meta_lines.append(f"**Context Length:** {entry.context_length}")
    if entry.license_type:
        meta_lines.append(f"**License:** {entry.license_type}")
    if entry.is_open_source:
        meta_lines.append("**Open Source:** Yes")
    if meta_lines:
        sections.append(" | ".join(meta_lines) + "\n")

    if entry.description:
        sections.append(f"## Overview\n\n{entry.description}\n")
    if entry.key_detail:
        sections.append(f"## Key Features\n\n{entry.key_detail}\n")

    specs = []
    if entry.attention_type:
        specs.append(f"- **Attention:** {entry.attention_type}")
    if entry.normalization:
        specs.append(f"- **Normalization:** {entry.normalization}")
    if entry.activation:
        specs.append(f"- **Activation:** {entry.activation}")
    if entry.position_encoding:
        specs.append(f"- **Position Encoding:** {entry.position_encoding}")
    if entry.vocab_size:
        specs.append(f"- **Vocab Size:** {entry.vocab_size}")
    if entry.hidden_dim:
        specs.append(f"- **Hidden Dim:** {entry.hidden_dim}")
    if entry.num_layers:
        specs.append(f"- **Layers:** {entry.num_layers}")
    if entry.num_heads:
        specs.append(f"- **Heads:** {entry.num_heads}")
    if entry.num_experts:
        specs.append(f"- **Experts:** {entry.num_experts} (active: {entry.active_experts or 'N/A'})")
    if specs:
        sections.append("## Architecture Details\n\n" + "\n".join(specs) + "\n")

    if entry.training_detail:
        sections.append(f"## Training\n\n{entry.training_detail}\n")

    links = []
    if entry.paper_url:
        links.append(f"- [Paper]({entry.paper_url})")
    if entry.code_url:
        links.append(f"- [Code]({entry.code_url})")
    if links:
        sections.append("## References\n\n" + "\n".join(links) + "\n")

    return "\n".join(sections)


def load_content_json(slug):
    """content.json이 존재하면 로드, 없으면 None."""
    content_path = ARCH_DATA_DIR / slug / "content.json"
    if content_path.exists():
        with open(content_path, encoding="utf-8") as f:
            return json.load(f)
    return None


def get_ai_category():
    cat, _ = Category.objects.get_or_create(
        slug="ai-ml",
        defaults={"name": "AI/ML", "code": "20.AI", "icon": "Brain", "color": "#FF6F00"},
    )
    return cat


ARCH_CAT_TO_SUB = {
    'llm': 'llm',
    'ssm': 'ssm',
    'diffusion': 'diffusion',
    'vision': 'vision',
    'multimodal': 'multimodal',
    'agent': 'agent',
    'technique': 'technique',
}


def convert_all(dry_run=False):
    author = User.objects.filter(is_superuser=True).first()
    if not author:
        print("No superuser found!")
        return

    ai_cat = get_ai_category()
    entries = ArchitectureEntry.objects.all()
    created = 0
    linked = 0
    skipped = 0
    from_content_json = 0

    for entry in entries:
        if entry.related_post:
            skipped += 1
            continue

        existing = Post.objects.filter(slug=entry.slug).first()
        if existing:
            if not dry_run:
                entry.related_post = existing
                entry.save(update_fields=["related_post"])
            linked += 1
            continue

        # content.json 우선 사용
        cj = load_content_json(entry.slug)
        if cj and cj.get("content"):
            content = cj["content"]
            summary = cj.get("summary", "")[:500]
            title = cj.get("title_ko") or cj.get("title") or entry.name
            tags_raw = cj.get("tags", [])
            from_content_json += 1
        else:
            content = build_markdown(entry)
            summary = (entry.key_detail or entry.description or "")[:500]
            title = entry.name
            tags_raw = []

        sub_slug = ARCH_CAT_TO_SUB.get(entry.architecture_category, 'llm')

        if dry_run:
            src = "content.json" if cj and cj.get("content") else "entry.json"
            words = len(content.split())
            print(f"  [{src:12s}] {entry.slug:30s} → {sub_slug:12s} ({words:5d} words)")
            continue

        SUB_DEFAULTS = {
            'llm':       {"name": "LLM",       "icon": "Brain",    "color": "#6366F1"},
            'ssm':       {"name": "SSM",       "icon": "Zap",      "color": "#F59E0B"},
            'diffusion': {"name": "Diffusion", "icon": "Sparkles", "color": "#EC4899"},
            'vision':    {"name": "Vision",    "icon": "Eye",      "color": "#10B981"},
            'multimodal':{"name": "Multimodal","icon": "Layers",   "color": "#8B5CF6"},
            'agent':     {"name": "Agent",     "icon": "Bot",      "color": "#F97316"},
            'technique': {"name": "Technique", "icon": "Wrench",   "color": "#14B8A6"},
        }
        sub_def = SUB_DEFAULTS.get(sub_slug, {"name": sub_slug.upper(), "icon": "Brain", "color": "#6366F1"})
        sub_cat, _ = Category.objects.get_or_create(
            slug=sub_slug,
            defaults={
                "name": sub_def["name"],
                "parent": ai_cat,
                "icon": sub_def["icon"],
                "color": sub_def["color"],
            },
        )

        post = Post.objects.create(
            title=title,
            slug=entry.slug,
            content=content,
            summary=summary,
            category=sub_cat,
            author=author,
            status="published",
            post_type="article",
            quality_score=7.0 if not cj else 8.0,
            published_at=timezone.now(),
        )

        if entry.figure:
            post.cover_image = entry.figure
            post.save(update_fields=["cover_image"])

        # concepts + content.json tags → Tag
        all_tags = set()
        for concept in entry.concepts.all():
            all_tags.add((concept.slug, concept.name))
        for tag_name in tags_raw:
            tag_slug = slugify(tag_name, allow_unicode=True)[:100]
            if tag_slug:
                all_tags.add((tag_slug, tag_name))

        for tag_slug, tag_name in all_tags:
            tag, _ = Tag.objects.get_or_create(
                slug=tag_slug,
                defaults={"name": tag_name},
            )
            post.tags.add(tag)

        entry.related_post = post
        entry.save(update_fields=["related_post"])
        created += 1

    if dry_run:
        print(f"\n[DRY-RUN] content.json: {from_content_json}, fallback: {len(list(entries)) - from_content_json - linked - skipped}")
    else:
        print(f"\nCreated {created} posts ({from_content_json} from content.json), linked {linked} existing, skipped {skipped}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ArchitectureEntry → Post 변환')
    parser.add_argument('--dry-run', action='store_true', help='변경 없이 미리보기')
    args = parser.parse_args()
    convert_all(dry_run=args.dry_run)
