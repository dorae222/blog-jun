"""
Cloud 카테고리에서 옵시디언 백업(hyeongjun_backup_20260227/10.Cloud)에 없는 포스트를 삭제.
백업의 카테고리 인덱스 파일([[위키링크]])을 기준으로 유효한 AWS 서비스 목록을 추출.

사용법:
    python manage.py purge_cloud_irrelevant --dry-run
    python manage.py purge_cloud_irrelevant
"""
import json
import re
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from blog.models import Category, Post, Tag


def _normalize(text):
    """제목을 정규화하여 비교 가능하게 변환"""
    if not text:
        return ""
    # 이모지 및 특수 앞글자 제거
    text = re.sub(r'^[📘📗📙📕📖💡🧾🔍🛡️⚙️🔐🌐☁️🧱🔧📊🟠🐳]+\s*', '', text)
    text = text.lower()
    text = re.sub(r'[^a-z0-9가-힣\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# 옵시디언 백업(hyeongjun_backup_20260227/10.Cloud/11.AWS/) 카테고리 인덱스에서
# 추출한 [[위키링크]] 기반 유효 서비스 목록 (정규화된 형태, 이미지 링크 제외)
VALID_AWS_SERVICES = {
    "amazon api gateway", "amazon appflow", "amazon application composer",
    "amazon athena", "amazon augmented ai", "amazon aurora", "amazon bedrock",
    "amazon cloudfront", "amazon cloudsearch", "amazon codeguru",
    "amazon comprehend", "amazon comprehend medical", "amazon datazone",
    "amazon doument db", "amazon dynamodb", "amazon ec2",
    "amazon ec2 auto scaling", "amazon ec2 image builder",
    "amazon ecs anywhere", "amazon eks anywhere",
    "amazon elastic block store", "amazon elastic container registry",
    "amazon elastic container service", "amazon elastic file system",
    "amazon elastic kubernetes service", "amazon elastic mapreduce",
    "amazon elasticache", "amazon eventbridge", "amazon fargate",
    "amazon file cache", "amazon finspace", "amazon forest",
    "amazon fraud detector", "amazon fsx for lustre",
    "amazon fsx for windows file server", "amazon kendra",
    "amazon keyspaces for apache cassandra", "amazon kinesis", "amazon lex",
    "amazon lightsail", "amazon linux 2023", "amazon lookout for equipment",
    "amazon lookout for metrics", "amazon lookout for vision",
    "amazon managed grafana", "amazon managed service for apache airflow",
    "amazon managed service for apache flink",
    "amazon managed service for prometheus",
    "amazon managed streaming for apache kafka",
    "amazon memory db for redis", "amazon monitron", "amazon mq",
    "amazon neptune", "amazon opensearch service", "amazon opensearch service 1",
    "amazon partyrock", "amazon personalize", "amazon polly",
    "amazon q", "amazon q developer",
    "amazon quantum ledger database amazon qldb", "amazon quicksight",
    "amazon rds", "amazon rds for db2", "amazon rds on vmware",
    "amazon redshift", "amazon rekognition",
    "amazon relational database service", "amazon route 53",
    "amazon sagemaker",
    "amazon simple notification service sns",
    "amazon simple queue service sqs", "amazon simple storage service",
    "amazon simple workflow service", "amazon step functions",
    "amazon textract", "amazon timestream", "amazon transcribe", "amazon vpc",
    "amazon vpc lattice", "amzon fsx for netapp ontap",
    "amzon fsx for openzfs", "availability zone",
    "aws app mesh", "aws app runner", "aws app2container",
    "aws application cost profiler", "aws application discovery service",
    "aws application migration service", "aws appsync", "aws auto scaling",
    "aws b2b data interchange", "aws backup", "aws batch",
    "aws billing conductor", "aws budgets", "aws clean rooms",
    "aws cloud devlopment kit", "aws cloud map", "aws cloud9",
    "aws cloudformation", "aws cloudtrail", "aws cloudwatch",
    "aws codebuild", "aws codedeploy", "aws codepipeline",
    "aws command line interface", "aws compute optimizer", "aws config",
    "aws console mobile application", "aws control tower",
    "aws cost and usage report", "aws cost explorer", "aws data exchange",
    "aws data pipeline", "aws database migration service", "aws datasync",
    "aws deepcomposer", "aws deepracer", "aws direct connect",
    "aws elastic beanstalk", "aws elastic disaster recovery",
    "aws entity resolution", "aws fargate", "aws global accelerator",
    "aws glue", "aws health", "aws healthlake", "aws healthscribe",
    "aws lake formation", "aws lambda", "aws launch wizard",
    "aws license manager", "aws mainframe modernization service",
    "aws migration hub", "aws opsworks", "aws organizations", "aws outposts",
    "aws panorama", "aws private 5g", "aws privatelink", "aws proton",
    "aws serverless application repository", "aws service catalog",
    "aws snow family", "aws snowball", "aws step functions",
    "aws storage gateway", "aws systems manager", "aws transfer family",
    "aws transit gateway", "aws trusted advisor", "aws user notifications",
    "aws verified access", "aws vpn", "aws waf", "aws wavelength",
    "aws well architected tool", "aws well architected framework",
    "aws iam identity center", "aws certificate manager",
    "aws key management service", "aws secrets manager",
    "aws shield", "aws shield advanced",
    "aws cloudhsm", "aws firewall manager", "aws network firewall",
    "aws security hub", "aws guardduty",
    "aws inspector", "aws macie", "aws detective",
    "data protection", "detection and response",
    "edge location", "elastic load balancer",
    "global servies", "governance and compliance",
    "identity and access management iam",
    "integrated private wireless on aws",
    "network and app protection",
    "red hat openshift service on aws",
    "region", "region scpoed", "reserved instance ri reporting",
    "saving plan", "vmware cloud on aws",
    # 추가 기본 개념 (AWS 학습 맥락에서 유효)
    "bastion host", "nat gateway", "nat instance",
    "classless inter domain routing", "domain name system",
    "virtual private gateway", "virtual private network",
    "internet gateway", "security group",
    "network access control lists", "vpc flow logs",
    "auto scaling group", "placement group",
    "elastic ip", "elastic load balancer",
    "application load balancer", "network load balancer",
    "gateway load balancer",
}


def _is_match(title_normalized):
    """정규화된 제목이 유효 서비스 목록과 매칭되는지 확인"""
    # 정확 매칭
    if title_normalized in VALID_AWS_SERVICES:
        return True
    # 접두어 매칭: 유효 서비스명으로 시작하는 경우
    # (예: "amazon ec2 enhanced networking" ← "amazon ec2")
    for valid in VALID_AWS_SERVICES:
        if len(valid) >= 4 and title_normalized.startswith(valid):
            return True
        if len(valid) >= 6 and valid.startswith(title_normalized):
            return True
    return False


class Command(BaseCommand):
    help = "Cloud 카테고리에서 옵시디언 백업에 없는 포스트를 백업 후 삭제합니다."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="실제 삭제 없이 대상만 확인합니다.",
        )
        parser.add_argument(
            "--backup-dir",
            default="/tmp/blog-purge-cloud-backup",
            help="백업 파일 저장 디렉토리",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        backup_dir = Path(options["backup_dir"])
        prefix = "[DRY-RUN] " if dry_run else ""

        self.stdout.write(f"\n{prefix}purge_cloud_irrelevant 시작")
        self.stdout.write("=" * 60)

        # Cloud 카테고리 포스트 조회
        cloud_posts = Post.objects.filter(
            Q(category__slug="cloud") | Q(category__parent__slug="cloud")
        ).select_related("category").prefetch_related("tags")

        total = cloud_posts.count()
        matched = []
        unmatched = []

        for post in cloud_posts:
            title_norm = _normalize(post.title)
            if _is_match(title_norm):
                matched.append(post)
            else:
                unmatched.append(post)

        self.stdout.write(f"\n총 Cloud 포스트: {total}개")
        self.stdout.write(f"백업 매칭: {len(matched)}개")
        self.stdout.write(f"미매칭 (제거 후보): {len(unmatched)}개")

        if unmatched:
            self.stdout.write(f"\n{prefix}제거 대상 목록:")
            for post in sorted(unmatched, key=lambda p: p.title):
                tags = ", ".join(t.name for t in post.tags.all()[:5])
                self.stdout.write(f"  [{post.slug}] {post.title}")
                if tags:
                    self.stdout.write(f"       tags: {tags}")

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n[DRY-RUN] 실제 삭제 없이 종료합니다. "
                f"제거 대상: {len(unmatched)}개"
            ))
            return

        if not unmatched:
            self.stdout.write(self.style.SUCCESS("\n제거 대상이 없습니다."))
            return

        # 백업
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"cloud_purge_{timestamp}.json"

        backup_data = []
        for post in unmatched:
            backup_data.append({
                "id": post.id,
                "title": post.title,
                "slug": post.slug,
                "category": post.category.slug if post.category else None,
                "tags": [t.name for t in post.tags.all()],
                "content": post.content,
                "summary": post.summary,
                "created_at": post.created_at.isoformat(),
            })

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        self.stdout.write(f"\n백업 완료: {backup_file}")

        # 삭제
        unmatched_ids = [p.id for p in unmatched]
        deleted_count, _ = Post.objects.filter(id__in=unmatched_ids).delete()
        self.stdout.write(f"삭제 완료: {deleted_count}개 포스트")

        # 고아 태그 정리
        orphaned_tags = Tag.objects.annotate(
            post_count=Count("posts")
        ).filter(post_count=0)
        orphan_count = orphaned_tags.count()
        orphaned_tags.delete()
        self.stdout.write(f"고아 태그 삭제: {orphan_count}개")

        self.stdout.write(self.style.SUCCESS(
            f"\npurge_cloud_irrelevant 완료! "
            f"(삭제: {deleted_count}개, 백업: {backup_file})"
        ))
