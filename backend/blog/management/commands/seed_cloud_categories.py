"""
10.Cloud 카테고리 계층 구조를 생성하는 관리 명령어 (13개 서브카테고리).
기존 aws → 10개 AWS 도메인별 서브카테고리로 세분화.

사용법:
    python manage.py seed_cloud_categories
"""
from django.core.management.base import BaseCommand

from blog.models import Category


CLOUD_CHILDREN = [
    # 기존 유지
    {
        "code": "10.Cloud.02",
        "name": "Docker",
        "slug": "docker",
        "icon": "docker",
        "color": "#2496ED",
        "description": "docker, container",
    },
    {
        "code": "10.Cloud.03",
        "name": "LXD",
        "slug": "lxd",
        "icon": "lxd",
        "color": "#E95420",
        "description": "lxd, system container",
    },
    {
        "code": "10.Cloud.04",
        "name": "DevOps",
        "slug": "devops",
        "icon": "devops",
        "color": "#0DB7ED",
        "description": "cicd, deployment, monitoring",
    },
    # AWS 세분화 (기존 aws → 10개로 분할)
    {
        "code": "10.Cloud.10",
        "name": "AWS Compute",
        "slug": "aws-compute",
        "icon": "aws",
        "color": "#FF9900",
        "description": "EC2, Lambda, ECS, EKS, Fargate, Batch, Lightsail",
    },
    {
        "code": "10.Cloud.11",
        "name": "AWS Storage",
        "slug": "aws-storage",
        "icon": "aws",
        "color": "#3F8624",
        "description": "S3, EBS, EFS, Glacier, Storage Gateway, FSx",
    },
    {
        "code": "10.Cloud.12",
        "name": "AWS Database",
        "slug": "aws-database",
        "icon": "aws",
        "color": "#C925D1",
        "description": "RDS, Aurora, DynamoDB, ElastiCache, Redshift, DocumentDB, Neptune",
    },
    {
        "code": "10.Cloud.13",
        "name": "AWS Networking",
        "slug": "aws-networking",
        "icon": "aws",
        "color": "#8C4FFF",
        "description": "VPC, Route53, CloudFront, ELB/ALB/NLB, API Gateway, Direct Connect, Transit Gateway",
    },
    {
        "code": "10.Cloud.14",
        "name": "AWS Security",
        "slug": "aws-security",
        "icon": "aws",
        "color": "#DD344C",
        "description": "IAM, KMS, WAF, GuardDuty, Security Hub, Cognito, Macie, Shield",
    },
    {
        "code": "10.Cloud.15",
        "name": "AWS Analytics",
        "slug": "aws-analytics",
        "icon": "aws",
        "color": "#8C4FFF",
        "description": "Athena, Glue, Kinesis, EMR, QuickSight, OpenSearch, MSK, Lake Formation",
    },
    {
        "code": "10.Cloud.16",
        "name": "AWS AI/ML",
        "slug": "aws-ai-ml",
        "icon": "aws",
        "color": "#01A88D",
        "description": "SageMaker, Bedrock, Rekognition, Comprehend, Polly, Personalize, Textract",
    },
    {
        "code": "10.Cloud.17",
        "name": "AWS DevTools",
        "slug": "aws-devtools",
        "icon": "aws",
        "color": "#C17B9E",
        "description": "CodeBuild, CodePipeline, CodeDeploy, CloudFormation, CDK, CodeGuru",
    },
    {
        "code": "10.Cloud.18",
        "name": "AWS Management",
        "slug": "aws-management",
        "icon": "aws",
        "color": "#E7157B",
        "description": "CloudWatch, CloudTrail, Config, Systems Manager, Organizations, Trusted Advisor",
    },
    {
        "code": "10.Cloud.19",
        "name": "AWS Integration",
        "slug": "aws-integration",
        "icon": "aws",
        "color": "#E7157B",
        "description": "SQS, SNS, EventBridge, Step Functions, AppFlow, MQ, AppSync",
    },
]


class Command(BaseCommand):
    help = "10.Cloud 카테고리와 13개 하위 카테고리를 생성(upsert)합니다."

    def handle(self, *args, **options):
        # 부모 카테고리 upsert (slug 기준)
        parent, created = Category.objects.update_or_create(
            slug="cloud",
            defaults={
                "code": "10.Cloud",
                "name": "Cloud",
                "icon": "Cloud",
                "color": "#FF9900",
                "order": 10,
            },
        )
        status = "생성" if created else "업데이트"
        self.stdout.write(f"부모 카테고리: {parent.name} ({parent.code}) - {status}")

        # 기존 aws 카테고리가 있으면 보존 (재분류 후 삭제 또는 유지)
        old_aws = Category.objects.filter(slug='aws').first()
        if old_aws:
            self.stdout.write(
                f"  [INFO] 기존 aws 카테고리 존재 (포스트 {old_aws.posts.count()}개) "
                "→ reclassify_cloud_posts로 재분류 후 처리"
            )

        # 하위 카테고리 upsert (slug 기준)
        for idx, child_data in enumerate(CLOUD_CHILDREN):
            try:
                child = Category.objects.get(slug=child_data["slug"])
                child.code = child_data["code"]
                child.name = child_data["name"]
                child.icon = child_data["icon"]
                child.color = child_data["color"]
                child.parent = parent
                child.order = idx + 1
                child.save()
                created = False
            except Category.DoesNotExist:
                child = Category.objects.create(
                    slug=child_data["slug"],
                    code=child_data["code"],
                    name=child_data["name"],
                    icon=child_data["icon"],
                    color=child_data["color"],
                    parent=parent,
                    order=idx + 1,
                )
                created = True
            status = "생성" if created else "업데이트"
            self.stdout.write(f"  {child.code} - {child.name} ({child.slug}): {status}")

        self.stdout.write(self.style.SUCCESS(
            f"\nCloud 카테고리 시딩 완료! ({len(CLOUD_CHILDREN)}개 서브카테고리)"
        ))
