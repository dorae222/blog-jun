"""
모든 Post + ArchitectureEntry를 파일로 내보내기 Django management command.

사용법:
    python manage.py export_content
    python manage.py export_content --output-dir /app/content
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from blog.models import ArchitectureEntry, Post


def _yaml_escape(value):
    """YAML 값 이스케이프 (PyYAML 의존 없이 수동 포맷)."""
    s = str(value)
    if any(c in s for c in (':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'")):
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return s


def _build_frontmatter(post, arch_slug=None):
    """Post에서 YAML frontmatter 문자열 생성."""
    lines = ["---"]
    lines.append(f"title: {_yaml_escape(post.title)}")
    lines.append(f"slug: {_yaml_escape(post.slug)}")
    lines.append(f"category: {_yaml_escape(post.category.slug if post.category else '')}")

    tags = list(post.tags.values_list('name', flat=True))
    if tags:
        tag_items = ", ".join(f'"{t}"' for t in tags)
        lines.append(f"tags: [{tag_items}]")
    else:
        lines.append("tags: []")

    lines.append(f"status: {_yaml_escape(post.status)}")
    lines.append(f"post_type: {_yaml_escape(post.post_type)}")
    lines.append(f"quality_score: {post.quality_score}")
    lines.append(f"created_at: {_yaml_escape(post.created_at.isoformat() if post.created_at else '')}")

    if arch_slug:
        lines.append(f"architecture_entry: {_yaml_escape(arch_slug)}")

    lines.append("---")
    return "\n".join(lines)


class Command(BaseCommand):
    help = "모든 Post + ArchitectureEntry를 마크다운/JSON 파일로 내보내기"

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            default='/app/content',
            help='출력 디렉토리 (기본: /app/content)',
        )

    def handle(self, *args, **options):
        output_dir = Path(options['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)

        # ArchitectureEntry slug → Post 역매핑
        arch_post_map = {}
        for arch in ArchitectureEntry.objects.filter(related_post__isnull=False).select_related('related_post'):
            arch_post_map[arch.related_post_id] = arch.slug

        # Post 내보내기
        posts = Post.objects.select_related('category').prefetch_related('tags').all()
        exported_posts = 0

        for post in posts:
            cat_slug = post.category.slug if post.category else "_uncategorized"
            cat_dir = output_dir / cat_slug
            cat_dir.mkdir(parents=True, exist_ok=True)

            arch_slug = arch_post_map.get(post.id)
            frontmatter = _build_frontmatter(post, arch_slug)
            md_content = f"{frontmatter}\n\n{post.content}"

            file_path = cat_dir / f"{post.slug}.md"
            file_path.write_text(md_content, encoding="utf-8")
            exported_posts += 1

        # ArchitectureEntry 메타데이터 내보내기
        arch_dir = output_dir / "_architectures"
        arch_dir.mkdir(parents=True, exist_ok=True)
        exported_archs = 0

        for arch in ArchitectureEntry.objects.all():
            meta = {
                "name": arch.name,
                "slug": arch.slug,
                "organization": arch.organization,
                "release_date": str(arch.release_date) if arch.release_date else None,
                "architecture_category": arch.architecture_category,
                "decoder_type": arch.decoder_type,
                "param_scale": arch.param_scale,
                "context_length": arch.context_length,
                "attention_type": arch.attention_type,
                "normalization": arch.normalization,
                "activation": arch.activation,
                "position_encoding": arch.position_encoding,
                "vocab_size": arch.vocab_size,
                "hidden_dim": arch.hidden_dim,
                "num_layers": arch.num_layers,
                "num_heads": arch.num_heads,
                "num_experts": arch.num_experts,
                "active_experts": arch.active_experts,
                "description": arch.description,
                "key_detail": arch.key_detail,
                "training_detail": arch.training_detail,
                "paper_url": arch.paper_url,
                "code_url": arch.code_url,
                "license_type": arch.license_type,
                "is_open_source": arch.is_open_source,
                "related_post_slug": arch.related_post.slug if arch.related_post else None,
                "concepts": list(arch.concepts.values_list('name', flat=True)),
            }
            file_path = arch_dir / f"{arch.slug}.json"
            file_path.write_text(
                json.dumps(meta, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            exported_archs += 1

        self.stdout.write(self.style.SUCCESS(
            f"완료: Post {exported_posts}개, ArchitectureEntry {exported_archs}개 내보내기 → {output_dir}"
        ))
