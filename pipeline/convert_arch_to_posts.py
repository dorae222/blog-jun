"""
ArchitectureEntry → Post 변환 스크립트.
각 ArchitectureEntry를 풍부한 마크다운 Post로 변환하고,
related_post 필드로 연결합니다.

Usage: python manage.py shell < pipeline/convert_arch_to_posts.py
"""
import sys
import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from django.contrib.auth.models import User
from blog.models import Post, Category, Tag, ArchitectureEntry


def build_markdown(entry):
    """ArchitectureEntry에서 풍부한 마크다운 아티클 생성."""
    sections = []

    # 헤더
    sections.append(f"# {entry.name}\n")

    # 기본 정보
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

    # 설명
    if entry.description:
        sections.append(f"## Overview\n\n{entry.description}\n")

    # 핵심 특징
    if entry.key_detail:
        sections.append(f"## Key Features\n\n{entry.key_detail}\n")

    # 아키텍처 상세
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

    # 학습 정보
    if entry.training_detail:
        sections.append(f"## Training\n\n{entry.training_detail}\n")

    # 링크
    links = []
    if entry.paper_url:
        links.append(f"- [Paper]({entry.paper_url})")
    if entry.code_url:
        links.append(f"- [Code]({entry.code_url})")

    if links:
        sections.append("## References\n\n" + "\n".join(links) + "\n")

    return "\n".join(sections)


def get_ai_category():
    """AI/ML 부모 카테고리 가져오기 또는 생성."""
    cat, _ = Category.objects.get_or_create(
        slug="ai-ml",
        defaults={"name": "AI/ML", "code": "20.AI", "icon": "🤖", "color": "#FF6F00"},
    )
    return cat


# 아키텍처 카테고리 → 서브카테고리 slug 매핑
ARCH_CAT_TO_SUB = {
    'llm': 'llm',
    'ssm': 'ssm',
    'diffusion': 'diffusion',
    'vision': 'vision',
    'multimodal': 'multimodal',
    'agent': 'agent',
    'technique': 'technique',
}


def convert_all():
    author = User.objects.filter(is_superuser=True).first()
    if not author:
        print("No superuser found!")
        return

    ai_cat = get_ai_category()
    entries = ArchitectureEntry.objects.all()
    created = 0
    linked = 0
    skipped = 0

    for entry in entries:
        # 이미 related_post가 있으면 스킵
        if entry.related_post:
            skipped += 1
            continue

        # 이미 같은 slug의 Post가 있으면 연결만
        existing = Post.objects.filter(slug=entry.slug).first()
        if existing:
            entry.related_post = existing
            entry.save(update_fields=["related_post"])
            linked += 1
            continue

        # 서브카테고리 결정
        sub_slug = ARCH_CAT_TO_SUB.get(entry.architecture_category, 'llm')
        sub_cat, _ = Category.objects.get_or_create(
            slug=sub_slug,
            defaults={
                "name": sub_slug.upper(),
                "parent": ai_cat,
                "icon": "🤖",
                "color": "#FF6F00",
            },
        )

        content = build_markdown(entry)
        summary = (entry.key_detail or entry.description or "")[:500]

        post = Post.objects.create(
            title=entry.name,
            slug=entry.slug,
            content=content,
            summary=summary,
            category=sub_cat,
            author=author,
            status="published",
            post_type="article",
            quality_score=7.0,
        )

        # 기존 figure가 있으면 cover_image로 복사
        if entry.figure:
            post.cover_image = entry.figure
            post.save(update_fields=["cover_image"])

        # concepts를 태그로 변환
        for concept in entry.concepts.all():
            tag, _ = Tag.objects.get_or_create(
                slug=concept.slug,
                defaults={"name": concept.name},
            )
            post.tags.add(tag)

        # related_post 연결
        entry.related_post = post
        entry.save(update_fields=["related_post"])

        created += 1

    print(f"Created {created} posts, linked {linked} existing, skipped {skipped}")


if __name__ == "__main__":
    convert_all()
