"""
포스트를 시리즈에 할당하는 관리 명령어.
카테고리 필터링 + 제목 기준 정렬로 시리즈 순서를 자동 지정.

사용법:
    python manage.py assign_series --category aws-networking --series vpc-networking-guide --order-by title
    python manage.py assign_series --create --series-name "VPC 네트워킹 완벽 가이드" --series-slug vpc-networking-guide --category aws-networking
    python manage.py assign_series --dry-run --category aws-networking --series vpc-networking-guide
"""
from django.core.management.base import BaseCommand

from blog.models import Category, Post, Series


class Command(BaseCommand):
    help = "포스트를 시리즈에 할당합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            '--series',
            type=str,
            help='시리즈 slug',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='카테고리 slug (포스트 필터링)',
        )
        parser.add_argument(
            '--order-by',
            type=str,
            default='title',
            choices=['title', 'created_at', 'published_at'],
            help='시리즈 순서 결정 기준 (기본: title)',
        )
        parser.add_argument(
            '--create',
            action='store_true',
            help='시리즈가 없으면 생성',
        )
        parser.add_argument(
            '--series-name',
            type=str,
            help='--create 시 시리즈 이름',
        )
        parser.add_argument(
            '--series-slug',
            type=str,
            help='--create 시 시리즈 slug (--series 대신 사용 가능)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='변경 없이 미리보기',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        prefix = "[DRY-RUN] " if dry_run else ""

        series_slug = options['series'] or options.get('series_slug')
        if not series_slug:
            self.stderr.write("--series 또는 --series-slug 필수")
            return

        # 시리즈 가져오기 또는 생성
        series = Series.objects.filter(slug=series_slug).first()
        if not series:
            if options['create']:
                name = options.get('series_name') or series_slug.replace('-', ' ').title()
                if not dry_run:
                    series = Series.objects.create(slug=series_slug, name=name)
                self.stdout.write(f"{prefix}시리즈 생성: {name} ({series_slug})")
                if dry_run:
                    return
            else:
                self.stderr.write(
                    f"시리즈 '{series_slug}' 없음. --create 옵션으로 생성 가능."
                )
                return

        # 포스트 필터링
        from django.db.models import Q
        qs = Post.objects.filter(status='published')
        if options['category']:
            cat_slug = options['category']
            qs = qs.filter(
                Q(category__slug=cat_slug) | Q(category__parent__slug=cat_slug)
            )

        qs = qs.order_by(options['order_by'])

        assigned = 0
        self.stdout.write(f"\n{prefix}시리즈 '{series.name}' 에 포스트 할당")
        self.stdout.write(f"카테고리: {options.get('category', '전체')}")
        self.stdout.write(f"정렬: {options['order_by']}")
        self.stdout.write("=" * 60)

        for idx, post in enumerate(qs, start=1):
            if not dry_run:
                post.series = series
                post.series_order = idx
                post.save(update_fields=['series', 'series_order'])
            assigned += 1
            self.stdout.write(
                f"  {prefix}[{idx}] {post.title[:60]} ({post.slug})"
            )

        self.stdout.write("=" * 60)
        self.stdout.write(f"{prefix}완료: {assigned}개 포스트 할당")
