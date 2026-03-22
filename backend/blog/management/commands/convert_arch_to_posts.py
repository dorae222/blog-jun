"""
ArchitectureEntry → Post 변환 Django management command.
content.json이 존재하면 우선 사용, 없으면 DB 필드에서 마크다운 자동 생성.

사용법:
    python manage.py convert_arch_to_posts
    python manage.py convert_arch_to_posts --arch-dir /pipeline/data/architectures_written
    python manage.py convert_arch_to_posts --dry-run
"""
import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from blog.models import ArchitectureEntry, Category, Post, Tag

# architecture_category → 서브카테고리 slug 매핑
ARCH_CAT_TO_SUB = {
    'llm': 'llm',
    'ssm': 'ssm',
    'diffusion': 'diffusion',
    'vision': 'vision',
    'multimodal': 'multimodal',
    'agent': 'agent',
    'technique': 'technique',
}

SUB_DEFAULTS = {
    'llm':        {"name": "LLM",       "icon": "Brain",    "color": "#6366F1"},
    'ssm':        {"name": "SSM",       "icon": "Zap",      "color": "#F59E0B"},
    'diffusion':  {"name": "Diffusion", "icon": "Sparkles", "color": "#EC4899"},
    'vision':     {"name": "Vision",    "icon": "Eye",      "color": "#10B981"},
    'multimodal': {"name": "Multimodal","icon": "Layers",   "color": "#8B5CF6"},
    'agent':      {"name": "Agent",     "icon": "Bot",      "color": "#F97316"},
    'technique':  {"name": "Technique", "icon": "Wrench",   "color": "#14B8A6"},
}


def build_markdown(entry):
    """ArchitectureEntry DB 필드에서 마크다운 아티클 생성 (content.json 없을 때 fallback)."""
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


class Command(BaseCommand):
    help = "ArchitectureEntry → Post 변환 (content.json 우선, 없으면 DB fallback)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--arch-dir',
            default='/pipeline/data/architectures_written',
            help='content.json 디렉토리 경로 (기본: /pipeline/data/architectures_written)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='변경 없이 미리보기',
        )

    def _load_content_json(self, arch_dir, slug):
        """content.json이 존재하면 로드, 없으면 None."""
        content_path = arch_dir / slug / "content.json"
        if content_path.exists():
            with open(content_path, encoding="utf-8") as f:
                return json.load(f)
        return None

    def _get_ai_category(self):
        cat, _ = Category.objects.get_or_create(
            slug="ai-ml",
            defaults={"name": "AI/ML", "code": "20.AI", "icon": "Brain", "color": "#FF6F00"},
        )
        return cat

    def _get_or_create_sub_category(self, sub_slug, ai_cat):
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
        return sub_cat

    def handle(self, *args, **options):
        arch_dir = Path(options['arch_dir'])
        dry_run = options['dry_run']
        prefix = "[DRY-RUN] " if dry_run else ""

        author = User.objects.filter(is_superuser=True).first()
        if not author:
            self.stderr.write("superuser가 없습니다. createsuperuser를 먼저 실행하세요.")
            return

        ai_cat = self._get_ai_category()
        entries = ArchitectureEntry.objects.all()

        created = 0
        linked = 0
        skipped = 0
        from_content_json = 0

        self.stdout.write(f"\n{prefix}convert_arch_to_posts 시작")
        self.stdout.write(f"arch-dir: {arch_dir} (exists: {arch_dir.is_dir()})")
        self.stdout.write("=" * 60)

        with transaction.atomic():
            for entry in entries:
                # 이미 Post에 연결됨
                if entry.related_post:
                    skipped += 1
                    continue

                # 같은 slug의 Post가 이미 존재 → 연결만
                existing = Post.objects.filter(slug=entry.slug).first()
                if existing:
                    if not dry_run:
                        entry.related_post = existing
                        entry.save(update_fields=["related_post"])
                    self.stdout.write(f"  [LINK] {entry.slug} → 기존 Post 연결")
                    linked += 1
                    continue

                # content.json 우선 사용
                cj = self._load_content_json(arch_dir, entry.slug)
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
                    src = "content.json" if cj and cj.get("content") else "DB fallback"
                    words = len(content.split())
                    self.stdout.write(
                        f"  [{src:12s}] {entry.slug:30s} → {sub_slug:12s} ({words:5d} words)"
                    )
                    continue

                sub_cat = self._get_or_create_sub_category(sub_slug, ai_cat)

                post = Post.objects.create(
                    title=title,
                    slug=entry.slug,
                    content=content,
                    summary=summary,
                    category=sub_cat,
                    author=author,
                    status="published",
                    post_type="article",
                    quality_score=8.0 if (cj and cj.get("content")) else 7.0,
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
                self.stdout.write(f"  [CREATE] {entry.slug}")

            # dry-run이면 롤백
            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write("=" * 60)
        total = entries.count()
        if dry_run:
            fallback = total - from_content_json - linked - skipped
            self.stdout.write(self.style.WARNING(
                f"[DRY-RUN 완료] content.json: {from_content_json}, "
                f"DB fallback: {fallback}, link: {linked}, skip: {skipped}"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"완료: Post {created}개 생성 (content.json: {from_content_json}), "
                f"기존 연결: {linked}, 스킵: {skipped}"
            ))
