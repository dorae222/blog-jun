"""
Cloud 포스트를 올바른 서브카테고리로 재분류.
slug 기반 수동 매핑 우선, 태그/제목 키워드 fallback.

사용법:
    python manage.py reclassify_cloud_posts --dry-run
    python manage.py reclassify_cloud_posts
"""
from django.core.management.base import BaseCommand

from blog.models import Category, Post


# ── slug → 서브카테고리 수동 매핑 (최우선) ──
SLUG_TO_SUBCATEGORY = {
    # aws-compute (12)
    'auto-scaling-groupasg': 'aws-compute',
    'amazon-ec2-enhanced-networking--네트워크-성능-향상-기능': 'aws-compute',
    'amazon-ec2-m1-mac-인스턴스': 'aws-compute',
    'amazon-elastic-container-service-amazon-ecs': 'aws-compute',
    'aws-batch': 'aws-compute',
    'aws-app-runner-개요-및-활용': 'aws-compute',
    'aws-elastic-beanstalk-개요': 'aws-compute',
    'amazon-lightsail-간단하고-저비용의-aws-클라우드-플랫폼': 'aws-compute',
    'aws-wavelength-개요-5g-엣지-컴퓨팅': 'aws-compute',
    'aws-compute-optimizer-빠른-개요': 'aws-compute',
    'aws-outposts-온프레미스에서의-aws-확장': 'aws-compute',
    'aws-app-mesh': 'aws-compute',
    # aws-storage (4)
    'amazon-simple-storage-serviceamazon-s3-개요': 'aws-storage',
    'aws-storage-gateway': 'aws-storage',
    'aws-transfer-family': 'aws-storage',
    'aws-backup-개요-및-주요-기능': 'aws-storage',
    # aws-database (21)
    'amazon-rds': 'aws-database',
    'amazon-rds-bluegreen-배포와-카나리canary-배포-개요': 'aws-database',
    'amazon-aurora-개요': 'aws-database',
    'amazon-aurora-postgresql': 'aws-database',
    'amazon-dynamodb-streams': 'aws-database',
    'amazon-elasticache인메모리-캐시-서비스-개요': 'aws-database',
    'amazon-elasticache-for-redis-redis-oss-클러스터-개요': 'aws-database',
    'amazon-timestream--서버리스-시계열-데이터베이스': 'aws-database',
    'amazon-redshift-개요': 'aws-database',
    'amazon-redshift-advisor--쿼리-기반-성능비용-최적화-권장': 'aws-database',
    'amazon-redshift-cluster': 'aws-database',
    'amazon-redshift-data-api-소개': 'aws-database',
    'amazon-redshift-federated-query-요약-및-athena-비교': 'aws-database',
    'amazon-redshift-materialized-viewmv': 'aws-database',
    'amazon-redshift-ml--sql로-수행하는-redshift-내-머신러닝': 'aws-database',
    'amazon-redshift-query-editor-v2': 'aws-database',
    'amazon-redshift-spectrum': 'aws-database',
    'amazon-redshift-super': 'aws-database',
    'amazon-redshift-table': 'aws-database',
    '-amazon-redshift-unload란': 'aws-database',
    'amazon-redshift-view뷰-개요': 'aws-database',
    # aws-networking (17)
    'elastic-ip-eip': 'aws-networking',
    'internet-gateway-igw': 'aws-networking',
    'virtual-private-gateway-vgw': 'aws-networking',
    'vpc-flow-logs': 'aws-networking',
    'nat-gateway-nat-게이트웨이': 'aws-networking',
    'amazon-api-gateway-소개': 'aws-networking',
    'amazon-cloudfront': 'aws-networking',
    'aws-direct-connect-정리': 'aws-networking',
    'aws-direct-connect-gateway-dx-gateway-개요': 'aws-networking',
    'aws-direct-connect-location': 'aws-networking',
    'aws-direct-connect--resiliency-복원력-설계': 'aws-networking',
    'aws-transit-gateway-tgw': 'aws-networking',
    'aws-transit-gateway에서-site-to-site-vpn-ecmp-equal-cost-multi-path': 'aws-networking',
    'aws-vpn-cloudhub': 'aws-networking',
    'aws-global-accelerator': 'aws-networking',
    'aws-privatelink-개요': 'aws-networking',
    'aws-cloud-map--서비스-디스커버리-및-리소스-매핑-서비스-개요': 'aws-networking',
    # aws-security (9)
    'aws-waf-적용-대상-및-주요-특징': 'aws-security',
    'aws-waf와-shield를-이용한-ddos-방어': 'aws-security',
    '-aws-security-hub란': 'aws-security',
    'aws-secrets-manager': 'aws-security',
    'aws-secrets-manager에-batchgetsecretvalue가-존재하나요': 'aws-security',
    'aws-cloudhsm-hardware-security-module': 'aws-security',
    'aws-certificate-manager-acm': 'aws-security',
    '-aws-network-firewall란': 'aws-security',
    '-bastion-host란': 'aws-security',
    # aws-analytics (33)
    'amazon-athena-개요-및-활용': 'aws-analytics',
    'amazon-athena-federated-query': 'aws-analytics',
    'amazon-athena-workgroup-vs-data-catalog-정리': 'aws-analytics',
    'amazon-datazone-개요-및-핵심-기능': 'aws-analytics',
    'amazon-kinesis-agent': 'aws-analytics',
    'amazon-kinesis-client-librarykcl--개요와-핵심-기능': 'aws-analytics',
    'amazon-kinesis-data-firehose': 'aws-analytics',
    'amazon-kinesis-data-streams-kds-개요': 'aws-analytics',
    'amazon-kinesis-요약-kpu-기반-과금-및-주요-특징': 'aws-analytics',
    'amazon-kinesis-producer-librarykpl-정리--aggregation과-consumer-영향': 'aws-analytics',
    'amazon-managed-service-for-apache-flink-구-amazon-kinesis-data-analytics-for-apache-flink': 'aws-analytics',
    'amazon-opensearch-service-개요': 'aws-analytics',
    'amazon-quicksight': 'aws-analytics',
    'amazon-quicksight-ml-insights': 'aws-analytics',
    'amazon-quicksight-인메모리-분석-엔진-spice-개요': 'aws-analytics',
    'aws-clean-rooms-개요-및-활용': 'aws-analytics',
    'aws-data-exchange-개요-및-활용': 'aws-analytics',
    'aws-glue-개요-및-주요-특징': 'aws-analytics',
    'aws-glue-classifier-개요': 'aws-analytics',
    'aws-glue-crawler-개요': 'aws-analytics',
    'aws-glue-databrew-개요-및-핵심-기능-정리': 'aws-analytics',
    'aws-glue-data-catalog': 'aws-analytics',
    'aws-glue-data-quality': 'aws-analytics',
    'aws-glue-dynamicframe란': 'aws-analytics',
    'aws-glue-findmatches': 'aws-analytics',
    'aws-glue-for-apache-spark': 'aws-analytics',
    'aws-glue-job-개요': 'aws-analytics',
    'aws-glue-job-bookmark': 'aws-analytics',
    'aws-glue-resolvechoice': 'aws-analytics',
    'aws-glue-studio-개요-및-핵심-포인트': 'aws-analytics',
    'aws-glue-trigger': 'aws-analytics',
    'aws-glue-workflow': 'aws-analytics',
    'aws-lake-formation-소개--데이터-레이크-구축과-보안-관리': 'aws-analytics',
    # aws-ai-ml (42)
    'amazon-augmented-ai-amazon-a2i': 'aws-ai-ml',
    'amazon-bedrock': 'aws-ai-ml',
    'amazon-bedrock-agents': 'aws-ai-ml',
    'amazon-bedrock-guardrails': 'aws-ai-ml',
    'amazon-bedrock-studio': 'aws-ai-ml',
    'amazon-comprehend-개요': 'aws-ai-ml',
    'amazon-personalize-개요': 'aws-ai-ml',
    'amazon-polly--텍스트를-음성으로-변환하는-서비스': 'aws-ai-ml',
    'amazon-q-business--엔터프라이즈용-생성형-ai-기반-업무-비서': 'aws-ai-ml',
    'amazon-q-developer': 'aws-ai-ml',
    'amazon-rekognition': 'aws-ai-ml',
    'amazon-rekognition-content-moderation-소개': 'aws-ai-ml',
    'amazon-sagemaker-서버리스-추론': 'aws-ai-ml',
    'amazon-sagemaker-도메인--도메인을-운영한다는-의미': 'aws-ai-ml',
    'amazon-sagemaker-모델-카드': 'aws-ai-ml',
    'amazon-sagemaker-모델-카드-소개': 'aws-ai-ml',
    'amazon-sagemaker-ai-개요': 'aws-ai-ml',
    'amazon-sagemaker-asynchronous-inference': 'aws-ai-ml',
    'amazon-sagemaker-autopilot': 'aws-ai-ml',
    'amazon-sagemaker-batch-transform': 'aws-ai-ml',
    'amazon-sagemaker-canvas': 'aws-ai-ml',
    'amazon-sagemaker-clarify': 'aws-ai-ml',
    'amazon-sagemaker-data-wrangler': 'aws-ai-ml',
    'amazon-sagemaker-data-wrangler-소개': 'aws-ai-ml',
    'amazon-sagemaker-debugger': 'aws-ai-ml',
    'amazon-sagemaker-엔드포인트endpoint-개요': 'aws-ai-ml',
    'amazon-sagemaker-experiments-개요': 'aws-ai-ml',
    'amazon-sagemaker-feature-store': 'aws-ai-ml',
    'amazon-sagemaker-ground-truth-소개': 'aws-ai-ml',
    'amazon-sagemaker-inference-recommender': 'aws-ai-ml',
    'amazon-sagemaker-jumpstart': 'aws-ai-ml',
    'amazon-sagemaker-jumpstart-개요': 'aws-ai-ml',
    'amazon-sagemaker-model-monitor': 'aws-ai-ml',
    'amazon-sagemaker-model-registry': 'aws-ai-ml',
    'amazon-sagemaker-model-registry-개요-및-워크플로': 'aws-ai-ml',
    'amazon-sagemaker-neo': 'aws-ai-ml',
    'amazon-sagemaker-notebook': 'aws-ai-ml',
    'amazon-sagemaker-real-time-inference': 'aws-ai-ml',
    'amazon-sagemaker-serverless-inference': 'aws-ai-ml',
    'amazon-sagemaker-studio': 'aws-ai-ml',
    'amazon-sagemaker-studio-classic': 'aws-ai-ml',
    'aws-panorama-개요-및-활용-가이드': 'aws-ai-ml',
    # aws-devtools (4)
    'amazon-codeguru--서비스-개요-및-활용-안내': 'aws-devtools',
    'aws-codedeploy-빠른-개요': 'aws-devtools',
    'aws-codepipeline': 'aws-devtools',
    'aws-cloud9-개요-및-활용': 'aws-devtools',
    # aws-management (18)
    'aws-cloudtrail이란': 'aws-management',
    'aws-config-구성-변경-추적과-규정-준수-관리': 'aws-management',
    'aws-control-tower-개요-및-구성': 'aws-management',
    'aws-control-tower-account-factory': 'aws-management',
    'aws-datasync-개요-및-주요-기능-정리': 'aws-management',
    'aws-health-dashboard--계정서비스-상태-모니터링': 'aws-management',
    'aws-migration-hub--마이그레이션-중앙-추적관리-서비스': 'aws-management',
    'aws-opsworks-개요-및-활용-가이드': 'aws-management',
    'aws-organizations--멀티-계정-관리와-중앙-거버넌스': 'aws-management',
    'aws-service-catalog-개요특징활용': 'aws-management',
    'aws-systems-manager-개요-및-주요-기능': 'aws-management',
    'aws-systems-manager-agent-ssm-agent': 'aws-management',
    'aws-systems-manager-opsitems': 'aws-management',
    'aws-systems-manager-parameter-store': 'aws-management',
    'aws-trusted-advisor-개요-및-활용-가이드': 'aws-management',
    'aws-well-architected-framework': 'aws-management',
    'aws-application-discovery-serviceads-개요-및-활용': 'aws-management',
    'aws-application-migration-service-aws-mgn-개요': 'aws-management',
    # aws-integration (6)
    'amazon-appflow-개요-saas와-aws-간-보안자동화-데이터-통합': 'aws-integration',
    'amazon-eventbridge-scheduler': 'aws-integration',
    'amazon-eventbridge-scheduler-개요-및-활용-가이드': 'aws-integration',
    'amazon-mq-표준-메시지-브로커의-완전관리형-서비스': 'aws-integration',
    'aws-appsync-서버리스-graphql-및-실시간-api-서비스-개요': 'aws-integration',
    'aws-step-functions-개요-및-사용-사례': 'aws-integration',
}

# 태그 → 서브카테고리 fallback (slug에 없는 미래 포스트용)
# 주의: 'aws', 'amazon' 같은 generic 태그는 제외 (default fallback으로 처리)
TAG_TO_SUBCATEGORY = {
    # aws-compute
    'ec2': 'aws-compute', 'lambda': 'aws-compute', 'ecs': 'aws-compute',
    'eks': 'aws-compute', 'fargate': 'aws-compute', 'lightsail': 'aws-compute',
    'auto-scaling': 'aws-compute', 'ami': 'aws-compute',
    'elastic-beanstalk': 'aws-compute', 'app-runner': 'aws-compute',
    # aws-storage
    's3': 'aws-storage', 'ebs': 'aws-storage', 'efs': 'aws-storage',
    'glacier': 'aws-storage', 'storage-gateway': 'aws-storage', 'fsx': 'aws-storage',
    'amazon-s3': 'aws-storage', 'aws-storage-gateway': 'aws-storage',
    # aws-database
    'rds': 'aws-database', 'aurora': 'aws-database', 'dynamodb': 'aws-database',
    'elasticache': 'aws-database', 'redshift': 'aws-database', 'documentdb': 'aws-database',
    'neptune': 'aws-database', 'memorydb': 'aws-database', 'timestream': 'aws-database',
    'amazon-rds': 'aws-database', 'amazon-aurora': 'aws-database',
    'amazon-redshift': 'aws-database', 'amazon-timestream': 'aws-database',
    # aws-networking
    'vpc': 'aws-networking', 'route53': 'aws-networking', 'cloudfront': 'aws-networking',
    'elb': 'aws-networking', 'alb': 'aws-networking', 'nlb': 'aws-networking',
    'direct-connect': 'aws-networking', 'transit-gateway': 'aws-networking',
    'subnet': 'aws-networking', 'security-group': 'aws-networking',
    'nat-gateway': 'aws-networking', 'elastic-ip': 'aws-networking',
    'aws-direct-connect': 'aws-networking', 'aws-global-accelerator': 'aws-networking',
    'aws-privatelink': 'aws-networking', 'aws-cloud-map': 'aws-networking',
    'amazon-api-gateway': 'aws-networking', 'api-gateway': 'aws-networking',
    # aws-security
    'iam': 'aws-security', 'kms': 'aws-security', 'waf': 'aws-security',
    'guardduty': 'aws-security', 'security-hub': 'aws-security',
    'cognito': 'aws-security', 'macie': 'aws-security', 'shield': 'aws-security',
    'certificate-manager': 'aws-security', 'secrets-manager': 'aws-security',
    'aws-waf': 'aws-security', 'aws-secrets-manager': 'aws-security',
    'aws-security-hub': 'aws-security', 'cloudhsm': 'aws-security',
    # aws-analytics
    'athena': 'aws-analytics', 'glue': 'aws-analytics', 'kinesis': 'aws-analytics',
    'emr': 'aws-analytics', 'quicksight': 'aws-analytics',
    'opensearch': 'aws-analytics', 'msk': 'aws-analytics',
    'lake-formation': 'aws-analytics', 'data-pipeline': 'aws-analytics',
    'etl': 'aws-analytics', 'mwaa': 'aws-analytics',
    'amazon-athena': 'aws-analytics', 'aws-glue': 'aws-analytics',
    'amazon-kinesis': 'aws-analytics', 'amazon-quicksight': 'aws-analytics',
    'amazon-opensearch-service': 'aws-analytics', 'amazon-datazone': 'aws-analytics',
    'aws-clean-rooms': 'aws-analytics', 'aws-data-exchange': 'aws-analytics',
    # aws-ai-ml
    'sagemaker': 'aws-ai-ml', 'bedrock': 'aws-ai-ml', 'rekognition': 'aws-ai-ml',
    'comprehend': 'aws-ai-ml', 'polly': 'aws-ai-ml', 'personalize': 'aws-ai-ml',
    'textract': 'aws-ai-ml', 'forecast': 'aws-ai-ml', 'lex': 'aws-ai-ml',
    'amazon-sagemaker': 'aws-ai-ml', 'amazon-bedrock': 'aws-ai-ml',
    'amazon-rekognition': 'aws-ai-ml', 'amazon-comprehend': 'aws-ai-ml',
    'amazon-personalize': 'aws-ai-ml', 'amazon-q': 'aws-ai-ml',
    'aws-panorama': 'aws-ai-ml', 'amazon-a2i': 'aws-ai-ml',
    # aws-devtools
    'codebuild': 'aws-devtools', 'codepipeline': 'aws-devtools',
    'cloudformation': 'aws-devtools', 'cdk': 'aws-devtools',
    'codeguru': 'aws-devtools', 'codedeploy': 'aws-devtools', 'sam': 'aws-devtools',
    'amazon-codeguru': 'aws-devtools', 'aws-codepipeline': 'aws-devtools',
    'cloud9': 'aws-devtools',
    # aws-management
    'cloudwatch': 'aws-management', 'cloudtrail': 'aws-management',
    'systems-manager': 'aws-management', 'organizations': 'aws-management',
    'trusted-advisor': 'aws-management', 'control-tower': 'aws-management',
    'aws-config': 'aws-management', 'aws-systems-manager': 'aws-management',
    'aws-control-tower': 'aws-management', 'aws-organizations': 'aws-management',
    'aws-datasync': 'aws-management', 'aws-migration-hub': 'aws-management',
    'aws-opsworks': 'aws-management',
    # aws-integration
    'sqs': 'aws-integration', 'sns': 'aws-integration',
    'eventbridge': 'aws-integration', 'step-functions': 'aws-integration',
    'appflow': 'aws-integration', 'mq': 'aws-integration', 'appsync': 'aws-integration',
    'amazon-eventbridge': 'aws-integration', 'amazon-mq': 'aws-integration',
    'aws-appsync': 'aws-integration', 'amazon-appflow': 'aws-integration',
    # Docker / LXD / DevOps
    'docker': 'docker', 'container': 'docker', 'dockerfile': 'docker',
    'docker-compose': 'docker',
    'lxd': 'lxd', 'lxc': 'lxd', 'system-container': 'lxd',
    'devops': 'devops', 'cicd': 'devops', 'ci-cd': 'devops',
    'github-actions': 'devops', 'terraform': 'devops', 'ansible': 'devops',
    'prometheus': 'devops', 'grafana': 'devops',
}


def _classify_by_tags(post, tag_map):
    """태그 기반 서브카테고리 분류 (generic 태그 제외)"""
    tag_names = [t.name.lower() for t in post.tags.all()]
    for tag_name in tag_names:
        if tag_name in tag_map:
            return tag_map[tag_name]
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
        slug_matched = 0
        tag_matched = 0
        defaulted = 0

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

            # 1순위: slug 수동 매핑
            target_slug = SLUG_TO_SUBCATEGORY.get(post.slug)
            match_method = 'SLUG' if target_slug else None

            # 2순위: 태그 기반 분류
            if not target_slug:
                target_slug = _classify_by_tags(post, TAG_TO_SUBCATEGORY)
                match_method = 'TAG' if target_slug else None

            # 3순위: aws-compute 기본 할당
            if not target_slug:
                target_slug = 'aws-compute'
                match_method = 'DEFAULT'
                defaulted += 1

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
            if match_method == 'SLUG':
                slug_matched += 1
            elif match_method == 'TAG':
                tag_matched += 1
            self.stdout.write(
                f"  {prefix}[{match_method}] {post.slug}: {old_cat} → {target_slug}"
            )

        self.stdout.write("=" * 60)
        self.stdout.write(
            f"{prefix}완료: {moved}개 이동 (slug:{slug_matched}, tag:{tag_matched}, "
            f"default:{defaulted}), {already_correct}개 정상, {unmapped}개 매핑없음"
        )
