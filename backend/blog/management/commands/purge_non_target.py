"""
Cloud + Data Engineering 카테고리 외 포스트를 백업 후 삭제하는 관리 명령어.
사용법:
    python manage.py purge_non_target --dry-run
    python manage.py purge_non_target --backup-dir /opt/blog-jun-backup
"""
import json
import os
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Count

from blog.models import Category, Post, Tag

# 유지 대상 부모 카테고리 slug
KEEP_SLUGS = {"cloud", "data-eng"}


class Command(BaseCommand):
    help = "Cloud + Data Engineering 외 포스트를 JSON 백업 후 삭제합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="실제 삭제 없이 대상만 확인합니다.",
        )
        parser.add_argument(
            "--backup-dir",
            default="/tmp/blog-purge-backup",
            help="백업 파일 저장 디렉토리 (기본: /tmp/blog-purge-backup)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        backup_dir = Path(options["backup_dir"])
        prefix = "[DRY-RUN] " if dry_run else ""

        self.stdout.write(f"\n{prefix}purge_non_target 시작")
        self.stdout.write("=" * 60)

        # 유지 대상 카테고리 ID 수집
        # 조건: slug가 KEEP_SLUGS에 포함되거나 parent__slug가 KEEP_SLUGS에 포함
        keep_cats = Category.objects.filter(
            slug__in=KEEP_SLUGS
        ) | Category.objects.filter(
            parent__slug__in=KEEP_SLUGS
        )
        keep_cat_ids = set(keep_cats.values_list("id", flat=True))

        # 제거 대상 포스트: 유지 카테고리에 속하지 않는 모든 포스트
        target_posts = Post.objects.exclude(category_id__in=keep_cat_ids)
        post_count = target_posts.count()

        self.stdout.write(f"\n{prefix}제거 대상 Post: {post_count}개")

        # 카테고리별 카운트 출력
        if post_count > 0:
            cat_counts = (
                target_posts.values("category__slug", "category__name")
                .annotate(count=Count("id"))
                .order_by("category__slug")
            )
            for item in cat_counts:
                slug = item["category__slug"] or "(카테고리 없음)"
                name = item["category__name"] or ""
                self.stdout.write(f"  {slug} ({name}): {item['count']}개")

        # 고아 태그 예상 (삭제 후 기준으로 예측)
        target_post_ids = set(target_posts.values_list("id", flat=True))
        orphan_tag_ids = set(
            Tag.objects.annotate(total=Count("posts"))
            .filter(total__gt=0)
            .filter(posts__id__in=target_post_ids)
            .values_list("id", flat=True)
        )
        # 삭제 대상 포스트에만 연결된 태그 (유지 포스트에도 연결된 태그는 제외)
        surviving_tag_ids = set(
            Tag.objects.filter(posts__isnull=False)
            .exclude(posts__id__in=target_post_ids)
            .values_list("id", flat=True)
        )
        orphan_tag_ids -= surviving_tag_ids
        orphan_count = len(orphan_tag_ids)
        self.stdout.write(f"\n{prefix}삭제 예정 고아 Tag: {orphan_count}개")

        # 빈 카테고리 (유지 대상이 아니고 포스트가 없는 카테고리)
        empty_non_keep_cats = (
            Category.objects.exclude(id__in=keep_cat_ids)
            .annotate(post_count=Count("posts"))
            .filter(post_count=0)
        )
        # 제거 대상 포스트 삭제 후 비어질 카테고리 포함
        removable_cats = Category.objects.exclude(id__in=keep_cat_ids)
        removable_cat_count = removable_cats.count()
        self.stdout.write(f"\n{prefix}삭제 대상 Category: {removable_cat_count}개")
        for cat in removable_cats.order_by("slug"):
            posts_here = Post.objects.filter(category=cat).count()
            self.stdout.write(f"  {cat.slug} ({cat.name}): post {posts_here}개")

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n[DRY-RUN] 실제 삭제 없이 종료합니다.\n"
                f"  Post:     {post_count}개 제거 예정\n"
                f"  Tag:      {orphan_count}개 고아 제거 예정\n"
                f"  Category: {removable_cat_count}개 제거 예정"
            ))
            return

        if post_count == 0:
            self.stdout.write(self.style.SUCCESS("\n제거 대상 포스트가 없습니다. 완료."))
            return

        # --- 백업 ---
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"purge_backup_{timestamp}.json"

        self.stdout.write(f"\n백업 저장 중: {backup_file}")
        backup_data = []
        for post in target_posts.select_related("category").prefetch_related("tags"):
            backup_data.append({
                "id": post.id,
                "title": post.title,
                "slug": post.slug,
                "post_type": post.post_type,
                "category": post.category.slug if post.category else None,
                "status": post.status,
                "content": post.content,
                "summary": post.summary,
                "created_at": post.created_at.isoformat(),
            })

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS(f"  -> 백업 완료: {len(backup_data)}개 포스트"))

        # --- 삭제 ---
        self.stdout.write("\nPost 삭제 중...")
        deleted_posts, _ = target_posts.delete()
        self.stdout.write(self.style.SUCCESS(f"  -> {deleted_posts}개 객체 삭제 완료"))

        # 고아 태그 삭제
        orphaned_tags = Tag.objects.annotate(post_count=Count("posts")).filter(post_count=0)
        actual_orphan_count = orphaned_tags.count()
        self.stdout.write(f"\n고아 Tag 삭제 중: {actual_orphan_count}개")
        orphaned_tags.delete()
        self.stdout.write(self.style.SUCCESS(f"  -> {actual_orphan_count}개 고아 Tag 삭제 완료"))

        # 빈 카테고리 삭제 (유지 대상 제외)
        empty_removable = (
            Category.objects.exclude(id__in=keep_cat_ids)
            .annotate(post_count=Count("posts"))
            .filter(post_count=0)
        )
        empty_cat_count = empty_removable.count()
        self.stdout.write(f"\n빈 Category 삭제 중: {empty_cat_count}개")
        for cat in empty_removable:
            self.stdout.write(f"  삭제: {cat.slug} ({cat.name})")
        empty_removable.delete()
        self.stdout.write(self.style.SUCCESS(f"  -> {empty_cat_count}개 Category 삭제 완료"))

        # 요약
        self.stdout.write(f"\n{'=' * 60}")
        self.stdout.write(self.style.SUCCESS("purge 완료 요약:"))
        self.stdout.write(f"  백업 파일:    {backup_file}")
        self.stdout.write(f"  Post 삭제:    {deleted_posts}개")
        self.stdout.write(f"  고아 Tag 삭제: {actual_orphan_count}개")
        self.stdout.write(f"  Category 삭제: {empty_cat_count}개")
        self.stdout.write(self.style.SUCCESS("\npurge_non_target 완료!"))
