"""
Cloud 부모 카테고리에 직접 할당된 포스트를 올바른 서브카테고리로 재분류.
태그 및 제목 키워드 기반 매핑 사용.

사용법:
    python manage.py reclassify_cloud_posts --dry-run
    python manage.py reclassify_cloud_posts
"""
import re

from django.core.management.base import BaseCommand

from blog.models import Category, Post


# 태그 → 서브카테고리 slug 매핑
TAG_TO_SUBCATEGORY = {
    'aws': 'aws',
    'amazon': 'aws',
    'ec2': 'aws',
    's3': 'aws',
    'lambda': 'aws',
    'rds': 'aws',
    'vpc': 'aws',
    'iam': 'aws',
    'cloudformation': 'aws',
    'cloudwatch': 'aws',
    'sagemaker': 'aws',
    'redshift': 'aws',
    'glue': 'aws',
    'athena': 'aws',
    'kinesis': 'aws',
    'dynamodb': 'aws',
    'aurora': 'aws',
    'ecs': 'aws',
    'eks': 'aws',
    'fargate': 'aws',
    'bedrock': 'aws',
    'elasticache': 'aws',
    'route53': 'aws',
    'cloudfront': 'aws',
    'sns': 'aws',
    'sqs': 'aws',
    'step-functions': 'aws',
    'eventbridge': 'aws',
    'cognito': 'aws',
    'waf': 'aws',
    'kms': 'aws',
    'elb': 'aws',
    'alb': 'aws',
    'nlb': 'aws',
    'ebs': 'aws',
    'efs': 'aws',
    'emr': 'aws',
    'msk': 'aws',
    'mwaa': 'aws',
    'data-pipelines': 'aws',
    'etl': 'aws',
    'docker': 'docker',
    'container': 'docker',
    'dockerfile': 'docker',
    'docker-compose': 'docker',
    'lxd': 'lxd',
    'lxc': 'lxd',
    'system-container': 'lxd',
    'devops': 'devops',
    'cicd': 'devops',
    'ci-cd': 'devops',
    'github-actions': 'devops',
    'terraform': 'devops',
    'ansible': 'devops',
    'monitoring': 'devops',
    'prometheus': 'devops',
    'grafana': 'devops',
}

# 제목 키워드 → 서브카테고리 (태그로 분류 안 된 경우 fallback)
TITLE_KEYWORDS = {
    'aws': 'aws',
    'amazon': 'aws',
    'sagemaker': 'aws',
    'redshift': 'aws',
    'cloudfront': 'aws',
    'cloudwatch': 'aws',
    'cloudformation': 'aws',
    'cloudtrail': 'aws',
    'lambda': 'aws',
    'ec2': 'aws',
    'iam': 'aws',
    'vpc': 'aws',
    'elb': 'aws',
    'alb': 'aws',
    'ebs': 'aws',
    'efs': 'aws',
    'rds': 'aws',
    's3 ': 'aws',
    'glue': 'aws',
    'athena': 'aws',
    'kinesis': 'aws',
    'dynamodb': 'aws',
    'aurora': 'aws',
    'bedrock': 'aws',
    'docker': 'docker',
    'dockerfile': 'docker',
    'lxd': 'lxd',
    'lxc': 'lxd',
}


def _classify_by_tags(post, tag_map):
    """태그 기반 서브카테고리 분류"""
    tag_names = [t.name.lower() for t in post.tags.all()]
    for tag_name in tag_names:
        if tag_name in tag_map:
            return tag_map[tag_name]
    return None


def _classify_by_title(title, title_keywords):
    """제목 키워드 기반 분류 (fallback)"""
    title_lower = title.lower()
    for keyword, slug in title_keywords.items():
        if keyword in title_lower:
            return slug
    return None


class Command(BaseCommand):
    help = "Cloud 포스트를 올바른 서브카테고리로 재분류"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='변경 없이 미리보기',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        prefix = "[DRY-RUN] " if dry_run else ""

        # Cloud 부모 카테고리
        try:
            cloud_parent = Category.objects.get(slug='cloud')
        except Category.DoesNotExist:
            self.stderr.write(
                "Cloud 카테고리(slug='cloud')가 없습니다. "
                "seed_cloud_categories를 먼저 실행하세요."
            )
            return

        # 서브카테고리 로드
        sub_cats = {
            cat.slug: cat
            for cat in Category.objects.filter(parent=cloud_parent)
        }
        self.stdout.write(f"서브카테고리: {list(sub_cats.keys())}")

        # Cloud 부모 + 모든 하위 카테고리의 포스트 조회
        all_cloud_cats = [cloud_parent] + list(sub_cats.values())
        posts = Post.objects.filter(
            category__in=all_cloud_cats
        ).prefetch_related('tags')

        moved = 0
        already_correct = 0
        unmapped = 0
        to_aws_default = 0

        self.stdout.write(
            f"\n{prefix}reclassify_cloud_posts 시작 (총 {posts.count()}개 포스트)"
        )
        self.stdout.write("=" * 60)

        for post in posts:
            # 이미 서브카테고리에 할당된 경우
            if post.category.slug in sub_cats and post.category != cloud_parent:
                already_correct += 1
                continue

            # 태그 기반 분류
            target_slug = _classify_by_tags(post, TAG_TO_SUBCATEGORY)

            # 제목 기반 fallback
            if not target_slug:
                target_slug = _classify_by_title(post.title, TITLE_KEYWORDS)

            # 여전히 분류 안 되면 AWS로 기본 할당 (대부분 AWS 콘텐츠)
            if not target_slug:
                target_slug = 'aws'
                to_aws_default += 1

            target_cat = sub_cats.get(target_slug)
            if not target_cat:
                unmapped += 1
                self.stdout.write(
                    f"  [WARN] 서브카테고리 '{target_slug}' 없음: {post.slug}"
                )
                continue

            if post.category == target_cat:
                already_correct += 1
                continue

            old_cat = post.category.slug
            if not dry_run:
                post.category = target_cat
                post.save(update_fields=['category'])

            moved += 1
            self.stdout.write(
                f"  {prefix}[MOVE] {post.slug}: {old_cat} → {target_slug}"
            )

        self.stdout.write("=" * 60)
        self.stdout.write(
            f"{prefix}완료: {moved}개 이동, {already_correct}개 정상, "
            f"{unmapped}개 매핑없음, {to_aws_default}개 AWS 기본할당"
        )
