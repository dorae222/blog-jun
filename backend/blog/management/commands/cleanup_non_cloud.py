"""
10.Cloud 이외의 카테고리에 속한 Post, 고아 Tag, 비-Cloud Category를 정리하는 관리 명령어.
사용법:
    python manage.py cleanup_non_cloud --dry-run
    python manage.py cleanup_non_cloud
"""
from django.core.management.base import BaseCommand
from django.db.models import Count

from blog.models import Category, Post, Tag


class Command(BaseCommand):
    help = "10.Cloud 이외의 카테고리 데이터를 정리합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="실제 삭제 없이 대상만 확인합니다.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        prefix = "[DRY-RUN] " if dry_run else ""

        self.stdout.write(f"\n{prefix}DB 클린업 시작")
        self.stdout.write("=" * 50)

        # 1) 비-Cloud 카테고리에 속한 Post 삭제
        non_cloud_categories = Category.objects.exclude(code__startswith="10.Cloud")
        non_cloud_posts = Post.objects.filter(category__in=non_cloud_categories)
        # 카테고리 없는 포스트도 포함
        no_category_posts = Post.objects.filter(category__isnull=True)
        target_posts = non_cloud_posts | no_category_posts

        post_count = target_posts.count()
        self.stdout.write(f"\n{prefix}삭제 대상 Post: {post_count}개")

        if post_count > 0:
            # 카테고리별 카운트
            cat_counts = (
                target_posts.values("category__code", "category__name")
                .annotate(count=Count("id"))
                .order_by("category__code")
            )
            for item in cat_counts:
                code = item["category__code"] or "(카테고리 없음)"
                name = item["category__name"] or ""
                self.stdout.write(f"  {code} ({name}): {item['count']}개")

            if not dry_run:
                deleted, details = target_posts.delete()
                self.stdout.write(self.style.SUCCESS(f"  -> {deleted}개 객체 삭제 완료"))

        # 2) 고아 Tag 정리 (포스트가 없는 태그)
        orphaned_tags = Tag.objects.annotate(post_count=Count("posts")).filter(
            post_count=0
        )
        orphan_count = orphaned_tags.count()
        self.stdout.write(f"\n{prefix}고아 Tag: {orphan_count}개")

        if orphan_count > 0 and not dry_run:
            orphaned_tags.delete()
            self.stdout.write(self.style.SUCCESS(f"  -> {orphan_count}개 고아 Tag 삭제 완료"))

        # 3) 비-Cloud Category 삭제
        non_cloud_cat_count = non_cloud_categories.count()
        self.stdout.write(f"\n{prefix}삭제 대상 Category: {non_cloud_cat_count}개")

        if non_cloud_cat_count > 0:
            for cat in non_cloud_categories:
                self.stdout.write(f"  {cat.code} - {cat.name}")

            if not dry_run:
                deleted, _ = non_cloud_categories.delete()
                self.stdout.write(
                    self.style.SUCCESS(f"  -> {deleted}개 Category 삭제 완료")
                )

        # 요약
        self.stdout.write(f"\n{'=' * 50}")
        self.stdout.write(f"{prefix}클린업 요약:")
        self.stdout.write(f"  Post 삭제:     {post_count}개")
        self.stdout.write(f"  고아 Tag 삭제: {orphan_count}개")
        self.stdout.write(f"  Category 삭제: {non_cloud_cat_count}개")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n[DRY-RUN] 실제 삭제는 수행하지 않았습니다.")
            )
        else:
            self.stdout.write(self.style.SUCCESS("\n클린업 완료!"))
