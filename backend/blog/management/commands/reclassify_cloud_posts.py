"""
Cloud 포스트를 올바른 서브카테고리로 재분류.
태그 및 제목 키워드 기반 매핑. AWS는 10개 도메인별 서브카테고리로 세분화.

사용법:
    python manage.py reclassify_cloud_posts --dry-run
    python manage.py reclassify_cloud_posts
"""
import re

from django.core.management.base import BaseCommand

from blog.models import Category, Post


# 태그 → 서브카테고리 slug 매핑 (AWS 10개 도메인별 세분화)
TAG_TO_SUBCATEGORY = {
    # aws-compute
    'ec2': 'aws-compute', 'lambda': 'aws-compute', 'ecs': 'aws-compute',
    'eks': 'aws-compute', 'fargate': 'aws-compute', 'batch': 'aws-compute',
    'lightsail': 'aws-compute', 'auto-scaling': 'aws-compute', 'ami': 'aws-compute',
    # aws-storage
    's3': 'aws-storage', 'ebs': 'aws-storage', 'efs': 'aws-storage',
    'glacier': 'aws-storage', 'storage-gateway': 'aws-storage', 'fsx': 'aws-storage',
    # aws-database
    'rds': 'aws-database', 'aurora': 'aws-database', 'dynamodb': 'aws-database',
    'elasticache': 'aws-database', 'redshift': 'aws-database', 'documentdb': 'aws-database',
    'neptune': 'aws-database', 'memorydb': 'aws-database',
    # aws-networking
    'vpc': 'aws-networking', 'route53': 'aws-networking', 'cloudfront': 'aws-networking',
    'elb': 'aws-networking', 'alb': 'aws-networking', 'nlb': 'aws-networking',
    'api-gateway': 'aws-networking', 'direct-connect': 'aws-networking',
    'transit-gateway': 'aws-networking', 'subnet': 'aws-networking',
    'security-group': 'aws-networking', 'nat-gateway': 'aws-networking',
    # aws-security
    'iam': 'aws-security', 'kms': 'aws-security', 'waf': 'aws-security',
    'guardduty': 'aws-security', 'security-hub': 'aws-security',
    'cognito': 'aws-security', 'macie': 'aws-security', 'shield': 'aws-security',
    'certificate-manager': 'aws-security', 'secrets-manager': 'aws-security',
    # aws-analytics
    'athena': 'aws-analytics', 'glue': 'aws-analytics', 'kinesis': 'aws-analytics',
    'emr': 'aws-analytics', 'quicksight': 'aws-analytics',
    'opensearch': 'aws-analytics', 'msk': 'aws-analytics',
    'lake-formation': 'aws-analytics', 'data-pipeline': 'aws-analytics',
    'data-pipelines': 'aws-analytics', 'etl': 'aws-analytics', 'mwaa': 'aws-analytics',
    # aws-ai-ml
    'sagemaker': 'aws-ai-ml', 'bedrock': 'aws-ai-ml', 'rekognition': 'aws-ai-ml',
    'comprehend': 'aws-ai-ml', 'polly': 'aws-ai-ml', 'personalize': 'aws-ai-ml',
    'textract': 'aws-ai-ml', 'forecast': 'aws-ai-ml', 'lex': 'aws-ai-ml',
    # aws-devtools
    'codebuild': 'aws-devtools', 'codepipeline': 'aws-devtools',
    'cloudformation': 'aws-devtools', 'cdk': 'aws-devtools',
    'codeguru': 'aws-devtools', 'codedeploy': 'aws-devtools', 'sam': 'aws-devtools',
    # aws-management
    'cloudwatch': 'aws-management', 'cloudtrail': 'aws-management',
    'config': 'aws-management', 'systems-manager': 'aws-management',
    'organizations': 'aws-management', 'trusted-advisor': 'aws-management',
    'control-tower': 'aws-management',
    # aws-integration
    'sqs': 'aws-integration', 'sns': 'aws-integration',
    'eventbridge': 'aws-integration', 'step-functions': 'aws-integration',
    'appflow': 'aws-integration', 'mq': 'aws-integration', 'appsync': 'aws-integration',
    # 일반 AWS (도메인 특정 안 되는 경우)
    'aws': 'aws-compute', 'amazon': 'aws-compute',
    # Docker / LXD / DevOps
    'docker': 'docker', 'container': 'docker', 'dockerfile': 'docker',
    'docker-compose': 'docker',
    'lxd': 'lxd', 'lxc': 'lxd', 'system-container': 'lxd',
    'devops': 'devops', 'cicd': 'devops', 'ci-cd': 'devops',
    'github-actions': 'devops', 'terraform': 'devops', 'ansible': 'devops',
    'monitoring': 'devops', 'prometheus': 'devops', 'grafana': 'devops',
}

# 제목 키워드 → 서브카테고리 (태그로 분류 안 된 경우 fallback)
TITLE_KEYWORDS = {
    # aws-compute
    'ec2': 'aws-compute', 'lambda': 'aws-compute', 'ecs ': 'aws-compute',
    'eks ': 'aws-compute', 'fargate': 'aws-compute', 'lightsail': 'aws-compute',
    # aws-storage
    's3 ': 'aws-storage', 's3-': 'aws-storage',
    'ebs ': 'aws-storage', 'efs ': 'aws-storage', 'glacier': 'aws-storage',
    # aws-database
    'rds': 'aws-database', 'aurora': 'aws-database', 'dynamodb': 'aws-database',
    'elasticache': 'aws-database', 'redshift': 'aws-database',
    # aws-networking
    'vpc': 'aws-networking', 'route53': 'aws-networking', 'route 53': 'aws-networking',
    'cloudfront': 'aws-networking', 'elb': 'aws-networking', 'alb': 'aws-networking',
    'api gateway': 'aws-networking', '서브넷': 'aws-networking', 'subnet': 'aws-networking',
    'nat gateway': 'aws-networking', '보안 그룹': 'aws-networking',
    # aws-security
    'iam': 'aws-security', 'waf': 'aws-security', 'cognito': 'aws-security',
    'guardduty': 'aws-security', 'kms': 'aws-security',
    # aws-analytics
    'athena': 'aws-analytics', 'glue': 'aws-analytics', 'kinesis': 'aws-analytics',
    'emr': 'aws-analytics', 'opensearch': 'aws-analytics',
    # aws-ai-ml
    'sagemaker': 'aws-ai-ml', 'bedrock': 'aws-ai-ml',
    # aws-devtools
    'cloudformation': 'aws-devtools', 'cdk': 'aws-devtools',
    # aws-management
    'cloudwatch': 'aws-management', 'cloudtrail': 'aws-management',
    # aws-integration
    'sqs': 'aws-integration', 'sns': 'aws-integration',
    'eventbridge': 'aws-integration', 'step functions': 'aws-integration',
    # 일반 AWS
    'aws': 'aws-compute', 'amazon': 'aws-compute',
    # Docker / LXD
    'docker': 'docker', 'dockerfile': 'docker',
    'lxd': 'lxd', 'lxc': 'lxd',
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

        # 기존 'aws' 카테고리 (있으면 재분류 대상)
        old_aws = Category.objects.filter(slug='aws').first()

        # Cloud 부모 + 모든 하위 카테고리 + 기존 aws 카테고리의 포스트 조회
        all_cloud_cats = [cloud_parent] + list(sub_cats.values())
        if old_aws and old_aws not in all_cloud_cats:
            all_cloud_cats.append(old_aws)
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
            # 이미 새 서브카테고리에 할당된 경우 (기존 'aws' 제외)
            if (post.category.slug in sub_cats
                    and post.category != cloud_parent
                    and post.category != old_aws):
                already_correct += 1
                continue

            # 태그 기반 분류
            target_slug = _classify_by_tags(post, TAG_TO_SUBCATEGORY)

            # 제목 기반 fallback
            if not target_slug:
                target_slug = _classify_by_title(post.title, TITLE_KEYWORDS)

            # 여전히 분류 안 되면 aws-compute로 기본 할당 (대부분 AWS 콘텐츠)
            if not target_slug:
                target_slug = 'aws-compute'
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
