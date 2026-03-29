"""
35개 AWS 서비스 엔트리와 50+ 관계를 시딩하는 관리 명령어.

CloudServiceEntry, CloudServiceRelation 모델에 데이터를 생성/업데이트합니다.
get_or_create + defaults 패턴으로 멱등(idempotent) 실행 가능.

사용법:
    python manage.py seed_cloud_services
"""
from django.core.management.base import BaseCommand

from blog.models import CloudServiceEntry, CloudServiceRelation, Post


# ---------------------------------------------------------------------------
# 35 AWS Services
# ---------------------------------------------------------------------------
# launch_year: WebSearch로 검증된 실제 AWS 출시 연도
# ---------------------------------------------------------------------------
SERVICES = [
    # ── Compute (5) ──────────────────────────────────────────────────────
    {
        "name": "Amazon EC2",
        "slug": "ec2",
        "provider": "aws",
        "service_domain": "compute",
        "launch_year": 2006,
        "is_serverless": False,
        "is_managed": False,
        "pricing_model": "on-demand",
        "importance": 10,
        "description": "가상 서버 인스턴스를 제공하는 AWS 핵심 컴퓨팅 서비스",
        "key_detail": "다양한 인스턴스 타입(범용, 컴퓨팅 최적화, 메모리 최적화 등)을 제공하며, "
                      "온디맨드/예약/스팟 등 유연한 과금 모델을 지원합니다.",
        "use_cases": "웹 서버, 애플리케이션 서버, 배치 처리, HPC, 게임 서버",
        "docs_url": "https://docs.aws.amazon.com/ec2/",
        "icon_name": "ec2",
    },
    {
        "name": "AWS Lambda",
        "slug": "lambda",
        "provider": "aws",
        "service_domain": "compute",
        "launch_year": 2014,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 9,
        "description": "서버리스 함수 실행 서비스",
        "key_detail": "이벤트 기반으로 코드를 실행하며, 서버 프로비저닝 없이 밀리초 단위 과금으로 "
                      "비용 효율적인 컴퓨팅을 제공합니다.",
        "use_cases": "이벤트 처리, API 백엔드, 데이터 변환, 스케줄링, IoT 백엔드",
        "docs_url": "https://docs.aws.amazon.com/lambda/",
        "icon_name": "lambda",
    },
    {
        "name": "Amazon ECS",
        "slug": "ecs",
        "provider": "aws",
        "service_domain": "compute",
        "launch_year": 2014,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "AWS 네이티브 컨테이너 오케스트레이션 서비스",
        "key_detail": "Docker 컨테이너를 EC2 또는 Fargate 위에서 실행하며, "
                      "AWS 서비스들과 깊이 통합된 컨테이너 관리를 제공합니다.",
        "use_cases": "마이크로서비스, 배치 작업, CI/CD 파이프라인, 웹 애플리케이션",
        "docs_url": "https://docs.aws.amazon.com/ecs/",
        "icon_name": "ecs",
    },
    {
        "name": "Amazon EKS",
        "slug": "eks",
        "provider": "aws",
        "service_domain": "compute",
        "launch_year": 2018,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "관리형 Kubernetes 서비스",
        "key_detail": "Kubernetes 컨트롤 플레인을 AWS가 관리하며, "
                      "온프레미스와 동일한 Kubernetes API로 컨테이너를 운영할 수 있습니다.",
        "use_cases": "마이크로서비스, 하이브리드 클라우드, ML 워크로드, 멀티 클라우드 전략",
        "docs_url": "https://docs.aws.amazon.com/eks/",
        "icon_name": "eks",
    },
    {
        "name": "AWS Fargate",
        "slug": "fargate",
        "provider": "aws",
        "service_domain": "compute",
        "launch_year": 2017,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "서버리스 컨테이너 실행 엔진",
        "key_detail": "EC2 인스턴스를 직접 관리하지 않고 컨테이너를 실행하며, "
                      "ECS와 EKS 모두에서 사용할 수 있는 서버리스 컴퓨팅 레이어입니다.",
        "use_cases": "마이크로서비스, 배치 처리, 이벤트 기반 워크로드",
        "docs_url": "https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html",
        "icon_name": "fargate",
    },
    # ── Storage (3) ──────────────────────────────────────────────────────
    {
        "name": "Amazon S3",
        "slug": "s3",
        "provider": "aws",
        "service_domain": "storage",
        "launch_year": 2006,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 10,
        "description": "무제한 확장 가능한 객체 스토리지 서비스",
        "key_detail": "99.999999999%(11 9s) 내구성을 제공하며, 정적 웹 호스팅부터 "
                      "데이터 레이크까지 AWS 생태계 전반의 핵심 스토리지입니다.",
        "use_cases": "데이터 레이크, 백업, 정적 웹 호스팅, 로그 저장, ML 학습 데이터",
        "docs_url": "https://docs.aws.amazon.com/s3/",
        "icon_name": "s3",
    },
    {
        "name": "Amazon EBS",
        "slug": "ebs",
        "provider": "aws",
        "service_domain": "storage",
        "launch_year": 2008,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "provisioned",
        "importance": 7,
        "description": "EC2 인스턴스용 블록 스토리지 서비스",
        "key_detail": "EC2에 연결되는 고성능 블록 스토리지로, SSD(gp3/io2)와 HDD(st1/sc1) "
                      "볼륨 타입을 제공하며 스냅샷 기반 백업을 지원합니다.",
        "use_cases": "데이터베이스, 파일 시스템, 부팅 볼륨, 트랜잭션 워크로드",
        "docs_url": "https://docs.aws.amazon.com/ebs/",
        "icon_name": "ebs",
    },
    {
        "name": "Amazon EFS",
        "slug": "efs",
        "provider": "aws",
        "service_domain": "storage",
        "launch_year": 2015,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 6,
        "description": "관리형 NFS 파일 시스템 서비스",
        "key_detail": "여러 EC2 인스턴스에서 동시 마운트 가능한 탄력적 파일 시스템으로, "
                      "자동 확장/축소되며 NFS v4 프로토콜을 지원합니다.",
        "use_cases": "공유 파일 스토리지, CMS, 개발 환경, 빅데이터 분석",
        "docs_url": "https://docs.aws.amazon.com/efs/",
        "icon_name": "efs",
    },
    # ── Database (5) ─────────────────────────────────────────────────────
    {
        "name": "Amazon RDS",
        "slug": "rds",
        "provider": "aws",
        "service_domain": "database",
        "launch_year": 2009,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "on-demand",
        "importance": 8,
        "description": "관리형 관계형 데이터베이스 서비스",
        "key_detail": "MySQL, PostgreSQL, MariaDB, Oracle, SQL Server 등 6개 엔진을 지원하며, "
                      "자동 백업/패치/복제 기능으로 운영 부담을 줄여줍니다.",
        "use_cases": "웹 애플리케이션 DB, ERP/CRM, 전자상거래, SaaS 백엔드",
        "docs_url": "https://docs.aws.amazon.com/rds/",
        "icon_name": "rds",
    },
    {
        "name": "Amazon Aurora",
        "slug": "aurora",
        "provider": "aws",
        "service_domain": "database",
        "launch_year": 2014,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "on-demand",
        "importance": 8,
        "description": "클라우드 네이티브 고성능 관계형 데이터베이스",
        "key_detail": "MySQL/PostgreSQL 호환이면서 상용 DB 수준 성능(MySQL 대비 5배, "
                      "PostgreSQL 대비 3배)을 제공하는 AWS 자체 개발 데이터베이스입니다.",
        "use_cases": "고성능 OLTP, SaaS 멀티테넌트, 글로벌 애플리케이션",
        "docs_url": "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/",
        "icon_name": "aurora",
    },
    {
        "name": "Amazon DynamoDB",
        "slug": "dynamodb",
        "provider": "aws",
        "service_domain": "database",
        "launch_year": 2012,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 8,
        "description": "완전 관리형 NoSQL 키-값/문서 데이터베이스",
        "key_detail": "한 자릿수 밀리초 지연시간을 보장하며, 자동 확장과 글로벌 테이블로 "
                      "대규모 워크로드를 처리하는 서버리스 NoSQL DB입니다.",
        "use_cases": "게임 리더보드, IoT 데이터, 세션 관리, 실시간 입찰, 장바구니",
        "docs_url": "https://docs.aws.amazon.com/dynamodb/",
        "icon_name": "dynamodb",
    },
    {
        "name": "Amazon ElastiCache",
        "slug": "elasticache",
        "provider": "aws",
        "service_domain": "database",
        "launch_year": 2011,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "on-demand",
        "importance": 6,
        "description": "관리형 인메모리 캐싱 서비스",
        "key_detail": "Redis와 Memcached를 지원하는 완전 관리형 인메모리 캐시로, "
                      "마이크로초 단위 응답 시간으로 데이터베이스 부하를 줄여줍니다.",
        "use_cases": "세션 스토어, DB 캐싱, 실시간 분석, 메시지 브로커",
        "docs_url": "https://docs.aws.amazon.com/elasticache/",
        "icon_name": "elasticache",
    },
    {
        "name": "Amazon Redshift",
        "slug": "redshift",
        "provider": "aws",
        "service_domain": "database",
        "launch_year": 2012,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "on-demand",
        "importance": 7,
        "description": "페타바이트급 클라우드 데이터 웨어하우스",
        "key_detail": "열 기반(columnar) 스토리지와 MPP(대규모 병렬 처리) 아키텍처로 "
                      "대규모 분석 쿼리를 빠르게 처리하는 데이터 웨어하우스입니다.",
        "use_cases": "비즈니스 인텔리전스, 데이터 웨어하우스, ETL, 대규모 로그 분석",
        "docs_url": "https://docs.aws.amazon.com/redshift/",
        "icon_name": "redshift",
    },
    # ── Networking (5) ───────────────────────────────────────────────────
    {
        "name": "Amazon VPC",
        "slug": "vpc",
        "provider": "aws",
        "service_domain": "networking",
        "launch_year": 2009,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "free",
        "importance": 9,
        "description": "AWS 가상 사설 네트워크",
        "key_detail": "AWS 리소스를 논리적으로 격리된 가상 네트워크에서 운영하며, "
                      "서브넷, 라우팅, 보안 그룹 등으로 네트워크를 완전히 제어합니다.",
        "use_cases": "네트워크 격리, 하이브리드 연결, 멀티 티어 아키텍처, 보안 존 구성",
        "docs_url": "https://docs.aws.amazon.com/vpc/",
        "icon_name": "vpc",
    },
    {
        "name": "Amazon Route 53",
        "slug": "route53",
        "provider": "aws",
        "service_domain": "networking",
        "launch_year": 2010,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "확장 가능한 DNS 및 도메인 등록 서비스",
        "key_detail": "100% SLA를 제공하는 관리형 DNS로, 도메인 등록/DNS 라우팅/"
                      "상태 확인 기능을 통합 제공합니다.",
        "use_cases": "도메인 관리, 글로벌 트래픽 라우팅, 장애 조치, 서비스 디스커버리",
        "docs_url": "https://docs.aws.amazon.com/route53/",
        "icon_name": "route53",
    },
    {
        "name": "Amazon CloudFront",
        "slug": "cloudfront",
        "provider": "aws",
        "service_domain": "networking",
        "launch_year": 2008,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 8,
        "description": "글로벌 CDN(콘텐츠 전송 네트워크) 서비스",
        "key_detail": "전 세계 400개 이상의 엣지 로케이션에서 콘텐츠를 캐싱하여 "
                      "저지연 전송을 제공하며, Lambda@Edge로 엣지 컴퓨팅도 지원합니다.",
        "use_cases": "정적 콘텐츠 배포, 동적 API 가속, 동영상 스트리밍, 보안(DDoS 방어)",
        "docs_url": "https://docs.aws.amazon.com/cloudfront/",
        "icon_name": "cloudfront",
    },
    {
        "name": "Elastic Load Balancing (ALB/ELB)",
        "slug": "alb",
        "provider": "aws",
        "service_domain": "networking",
        "launch_year": 2009,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 8,
        "description": "애플리케이션 트래픽 분산을 위한 로드 밸런서",
        "key_detail": "ALB(L7)/NLB(L4)/CLB(Classic) 세 가지 타입을 제공하며, "
                      "경로 기반 라우팅, WebSocket, gRPC 등 최신 프로토콜을 지원합니다.",
        "use_cases": "웹 애플리케이션 부하 분산, 마이크로서비스 라우팅, SSL 종료, 블루/그린 배포",
        "docs_url": "https://docs.aws.amazon.com/elasticloadbalancing/",
        "icon_name": "elb",
    },
    {
        "name": "Amazon API Gateway",
        "slug": "api-gateway",
        "provider": "aws",
        "service_domain": "networking",
        "launch_year": 2015,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 8,
        "description": "API 생성/배포/관리를 위한 완전 관리형 서비스",
        "key_detail": "REST/HTTP/WebSocket API를 생성하고, Lambda와 통합하여 "
                      "서버리스 백엔드를 구축하며, 인증/스로틀링/캐싱을 기본 제공합니다.",
        "use_cases": "서버리스 API, 마이크로서비스 진입점, 모바일 백엔드, B2B API",
        "docs_url": "https://docs.aws.amazon.com/apigateway/",
        "icon_name": "api-gateway",
    },
    # ── Security (3) ─────────────────────────────────────────────────────
    {
        "name": "AWS IAM",
        "slug": "iam",
        "provider": "aws",
        "service_domain": "security",
        "launch_year": 2011,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "free",
        "importance": 10,
        "description": "AWS 리소스 접근 제어를 위한 자격 증명 관리 서비스",
        "key_detail": "사용자/역할/정책 기반의 세밀한 접근 제어를 제공하며, "
                      "모든 AWS 서비스의 인증/인가 기반이 되는 핵심 보안 서비스입니다.",
        "use_cases": "접근 제어, 역할 기반 권한 관리, 크로스 계정 접근, 서비스 간 인증",
        "docs_url": "https://docs.aws.amazon.com/iam/",
        "icon_name": "iam",
    },
    {
        "name": "AWS KMS",
        "slug": "kms",
        "provider": "aws",
        "service_domain": "security",
        "launch_year": 2014,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "암호화 키 생성 및 관리 서비스",
        "key_detail": "FIPS 140-2 검증된 HSM으로 암호화 키를 관리하며, "
                      "S3/EBS/RDS 등 AWS 서비스의 데이터 암호화에 통합됩니다.",
        "use_cases": "데이터 암호화, 디지털 서명, 봉투 암호화, 키 로테이션",
        "docs_url": "https://docs.aws.amazon.com/kms/",
        "icon_name": "kms",
    },
    {
        "name": "Amazon Cognito",
        "slug": "cognito",
        "provider": "aws",
        "service_domain": "security",
        "launch_year": 2014,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "웹/모바일 앱을 위한 사용자 인증 서비스",
        "key_detail": "사용자 풀(User Pool)과 자격 증명 풀(Identity Pool)로 "
                      "회원가입/로그인/소셜 연동/MFA를 쉽게 구현할 수 있습니다.",
        "use_cases": "앱 인증, 소셜 로그인, SAML/OIDC 연동, 임시 AWS 자격 증명 발급",
        "docs_url": "https://docs.aws.amazon.com/cognito/",
        "icon_name": "cognito",
    },
    # ── Analytics (4) ────────────────────────────────────────────────────
    {
        "name": "Amazon Athena",
        "slug": "athena",
        "provider": "aws",
        "service_domain": "analytics",
        "launch_year": 2016,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "S3 데이터를 SQL로 직접 분석하는 서버리스 쿼리 서비스",
        "key_detail": "Presto 기반으로 S3에 저장된 데이터를 별도 인프라 없이 "
                      "표준 SQL로 조회하며, 스캔한 데이터량 기준으로 과금됩니다.",
        "use_cases": "로그 분석, 데이터 레이크 쿼리, 비즈니스 리포팅, 임시 분석",
        "docs_url": "https://docs.aws.amazon.com/athena/",
        "icon_name": "athena",
    },
    {
        "name": "AWS Glue",
        "slug": "glue",
        "provider": "aws",
        "service_domain": "analytics",
        "launch_year": 2017,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "서버리스 데이터 통합(ETL) 서비스",
        "key_detail": "데이터 카탈로그로 메타데이터를 관리하고, Spark 기반 ETL 작업을 "
                      "서버리스로 실행하여 데이터 레이크 구축을 지원합니다.",
        "use_cases": "ETL 파이프라인, 데이터 카탈로그, 데이터 레이크 구축, 스키마 관리",
        "docs_url": "https://docs.aws.amazon.com/glue/",
        "icon_name": "glue",
    },
    {
        "name": "Amazon Kinesis",
        "slug": "kinesis",
        "provider": "aws",
        "service_domain": "analytics",
        "launch_year": 2013,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "실시간 스트리밍 데이터 수집/처리 서비스",
        "key_detail": "Data Streams/Firehose/Analytics 세 가지 구성으로 "
                      "대규모 실시간 데이터를 수집, 변환, 분석할 수 있습니다.",
        "use_cases": "실시간 로그 분석, IoT 데이터 수집, 클릭스트림 분석, 실시간 대시보드",
        "docs_url": "https://docs.aws.amazon.com/kinesis/",
        "icon_name": "kinesis",
    },
    {
        "name": "Amazon EMR",
        "slug": "emr",
        "provider": "aws",
        "service_domain": "analytics",
        "launch_year": 2009,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 6,
        "description": "빅데이터 처리를 위한 관리형 클러스터 플랫폼",
        "key_detail": "Apache Spark, Hadoop, Hive, Presto 등을 관리형 클러스터로 실행하며, "
                      "페타바이트급 데이터 처리와 ML 워크로드를 지원합니다.",
        "use_cases": "대규모 데이터 처리, ETL, ML 학습, 유전체 분석, 로그 분석",
        "docs_url": "https://docs.aws.amazon.com/emr/",
        "icon_name": "emr",
    },
    # ── AI/ML (3) ────────────────────────────────────────────────────────
    {
        "name": "Amazon SageMaker",
        "slug": "sagemaker",
        "provider": "aws",
        "service_domain": "ai_ml",
        "launch_year": 2017,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 8,
        "description": "ML 모델 빌드/학습/배포를 위한 통합 플랫폼",
        "key_detail": "데이터 준비부터 모델 학습, 튜닝, 배포까지 ML 전체 라이프사이클을 "
                      "관리하며, 내장 알고리즘과 노트북 환경을 제공합니다.",
        "use_cases": "ML 모델 개발, AutoML, 모델 모니터링, MLOps 파이프라인",
        "docs_url": "https://docs.aws.amazon.com/sagemaker/",
        "icon_name": "sagemaker",
    },
    {
        "name": "Amazon Bedrock",
        "slug": "bedrock",
        "provider": "aws",
        "service_domain": "ai_ml",
        "launch_year": 2023,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 8,
        "description": "파운데이션 모델(FM) 기반 생성형 AI 서비스",
        "key_detail": "Claude, Llama, Titan 등 주요 FM을 API로 제공하며, "
                      "RAG/에이전트/파인튜닝 기능으로 생성형 AI 애플리케이션을 구축합니다.",
        "use_cases": "챗봇, 텍스트 생성, 요약, 코드 생성, RAG 기반 검색",
        "docs_url": "https://docs.aws.amazon.com/bedrock/",
        "icon_name": "bedrock",
    },
    {
        "name": "Amazon Comprehend",
        "slug": "comprehend",
        "provider": "aws",
        "service_domain": "ai_ml",
        "launch_year": 2017,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 5,
        "description": "자연어 처리(NLP) 서비스",
        "key_detail": "텍스트에서 감성/엔티티/키프레이즈/언어를 자동 분석하며, "
                      "커스텀 분류 모델 학습도 지원하는 관리형 NLP 서비스입니다.",
        "use_cases": "감성 분석, 텍스트 분류, 엔티티 추출, 토픽 모델링",
        "docs_url": "https://docs.aws.amazon.com/comprehend/",
        "icon_name": "comprehend",
    },
    # ── Integration (4) ─────────────────────────────────────────────────
    {
        "name": "Amazon SQS",
        "slug": "sqs",
        "provider": "aws",
        "service_domain": "integration",
        "launch_year": 2004,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 8,
        "description": "완전 관리형 메시지 큐 서비스",
        "key_detail": "AWS 최초의 서비스(2004)로, 표준 큐와 FIFO 큐를 제공하며 "
                      "마이크로서비스 간 비동기 통신과 디커플링을 구현합니다.",
        "use_cases": "작업 큐, 마이크로서비스 디커플링, 버퍼링, 배치 처리",
        "docs_url": "https://docs.aws.amazon.com/sqs/",
        "icon_name": "sqs",
    },
    {
        "name": "Amazon SNS",
        "slug": "sns",
        "provider": "aws",
        "service_domain": "integration",
        "launch_year": 2010,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "관리형 Pub/Sub 메시징 서비스",
        "key_detail": "토픽 기반 발행/구독(Pub/Sub) 패턴으로 메시지를 팬아웃하며, "
                      "Lambda/SQS/HTTP/이메일/SMS 등 다양한 구독 엔드포인트를 지원합니다.",
        "use_cases": "이벤트 알림, 팬아웃 패턴, 모바일 푸시, 이메일/SMS 알림",
        "docs_url": "https://docs.aws.amazon.com/sns/",
        "icon_name": "sns",
    },
    {
        "name": "Amazon EventBridge",
        "slug": "eventbridge",
        "provider": "aws",
        "service_domain": "integration",
        "launch_year": 2019,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "서버리스 이벤트 버스 서비스",
        "key_detail": "AWS 서비스/SaaS/커스텀 소스의 이벤트를 규칙 기반으로 라우팅하며, "
                      "스키마 레지스트리와 아카이브/리플레이 기능을 제공합니다.",
        "use_cases": "이벤트 기반 아키텍처, SaaS 통합, 크론 스케줄링, 크로스 계정 이벤트",
        "docs_url": "https://docs.aws.amazon.com/eventbridge/",
        "icon_name": "eventbridge",
    },
    {
        "name": "AWS Step Functions",
        "slug": "step-functions",
        "provider": "aws",
        "service_domain": "integration",
        "launch_year": 2016,
        "is_serverless": True,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "서버리스 워크플로 오케스트레이션 서비스",
        "key_detail": "상태 머신(State Machine) 기반으로 Lambda/ECS/SNS 등 "
                      "AWS 서비스를 시각적으로 연결하여 복잡한 비즈니스 워크플로를 구성합니다.",
        "use_cases": "주문 처리, ETL 파이프라인, ML 워크플로, 승인 프로세스",
        "docs_url": "https://docs.aws.amazon.com/step-functions/",
        "icon_name": "step-functions",
    },
    # ── Management (3) ───────────────────────────────────────────────────
    {
        "name": "Amazon CloudWatch",
        "slug": "cloudwatch",
        "provider": "aws",
        "service_domain": "management",
        "launch_year": 2009,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 8,
        "description": "AWS 리소스 모니터링 및 관찰 서비스",
        "key_detail": "메트릭/로그/알람/대시보드를 통합 제공하며, "
                      "거의 모든 AWS 서비스의 운영 데이터를 수집하고 시각화합니다.",
        "use_cases": "인프라 모니터링, 로그 분석, 알람 설정, 자동 스케일링 트리거",
        "docs_url": "https://docs.aws.amazon.com/cloudwatch/",
        "icon_name": "cloudwatch",
    },
    {
        "name": "AWS CloudTrail",
        "slug": "cloudtrail",
        "provider": "aws",
        "service_domain": "management",
        "launch_year": 2013,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "pay-per-use",
        "importance": 7,
        "description": "AWS API 호출 감사 및 로깅 서비스",
        "key_detail": "모든 AWS API 호출을 기록하여 누가/언제/무엇을 했는지 "
                      "추적하며, 보안 감사와 컴플라이언스의 핵심 도구입니다.",
        "use_cases": "보안 감사, 컴플라이언스, 변경 추적, 인시던트 조사",
        "docs_url": "https://docs.aws.amazon.com/cloudtrail/",
        "icon_name": "cloudtrail",
    },
    {
        "name": "AWS CloudFormation",
        "slug": "cloudformation",
        "provider": "aws",
        "service_domain": "management",
        "launch_year": 2011,
        "is_serverless": False,
        "is_managed": True,
        "pricing_model": "free",
        "importance": 8,
        "description": "인프라를 코드로 관리하는 IaC 서비스",
        "key_detail": "JSON/YAML 템플릿으로 AWS 리소스를 선언적으로 프로비저닝하며, "
                      "스택 단위로 인프라 생성/업데이트/삭제를 자동화합니다.",
        "use_cases": "IaC, 환경 복제, 재해 복구, 멀티 리전 배포",
        "docs_url": "https://docs.aws.amazon.com/cloudformation/",
        "icon_name": "cloudformation",
    },
]


# ---------------------------------------------------------------------------
# 50+ Relations
# ---------------------------------------------------------------------------
# (from_slug, to_slug, relation_type, description)
# ---------------------------------------------------------------------------
RELATIONS = [
    # ── Lambda integrations ──────────────────────────────────────────────
    ("lambda", "s3", "integrates_with", "S3 이벤트로 Lambda 함수 트리거"),
    ("lambda", "dynamodb", "integrates_with", "DynamoDB Streams로 Lambda 트리거"),
    ("lambda", "api-gateway", "integrates_with", "API Gateway 백엔드로 Lambda 실행"),
    ("lambda", "sqs", "integrates_with", "SQS 메시지를 Lambda가 폴링 처리"),
    ("lambda", "sns", "integrates_with", "SNS 구독으로 Lambda 트리거"),
    ("lambda", "eventbridge", "integrates_with", "EventBridge 규칙으로 Lambda 트리거"),
    ("lambda", "cloudwatch", "integrates_with", "Lambda 로그/메트릭을 CloudWatch로 전송"),
    ("lambda", "kinesis", "integrates_with", "Kinesis 스트림 레코드를 Lambda가 처리"),
    # ── ECS dependencies & integrations ──────────────────────────────────
    ("ecs", "vpc", "depends_on", "ECS 태스크는 VPC 서브넷에서 실행"),
    ("ecs", "ec2", "depends_on", "EC2 시작 유형 사용 시 EC2 인스턴스 필요"),
    ("ecs", "alb", "integrates_with", "ALB를 통한 ECS 서비스 로드 밸런싱"),
    ("ecs", "cloudwatch", "integrates_with", "ECS 컨테이너 로그를 CloudWatch로 전송"),
    # ── EKS dependencies ─────────────────────────────────────────────────
    ("eks", "vpc", "depends_on", "EKS 클러스터는 VPC 내에서 운영"),
    ("eks", "ec2", "depends_on", "EKS 워커 노드로 EC2 인스턴스 사용"),
    ("eks", "iam", "integrates_with", "IRSA로 Pod에 IAM 역할 연결"),
    # ── Fargate ──────────────────────────────────────────────────────────
    ("fargate", "ecs", "part_of", "ECS의 서버리스 시작 유형으로 동작"),
    ("fargate", "eks", "integrates_with", "EKS에서도 Fargate 프로파일 사용 가능"),
    ("fargate", "vpc", "depends_on", "Fargate 태스크는 VPC 내에서 실행"),
    # ── Aurora ───────────────────────────────────────────────────────────
    ("aurora", "rds", "evolved_from", "RDS 기반으로 클라우드 네이티브 재설계"),
    ("aurora", "vpc", "depends_on", "Aurora 클러스터는 VPC 서브넷 그룹 필요"),
    # ── CloudFront integrations ──────────────────────────────────────────
    ("cloudfront", "s3", "integrates_with", "S3 버킷을 오리진으로 콘텐츠 캐싱"),
    ("cloudfront", "alb", "integrates_with", "ALB를 오리진으로 동적 콘텐츠 가속"),
    ("cloudfront", "lambda", "integrates_with", "Lambda@Edge로 엣지 컴퓨팅 실행"),
    ("cloudfront", "route53", "integrates_with", "Route 53으로 CloudFront 도메인 연결"),
    # ── API Gateway integrations ─────────────────────────────────────────
    ("api-gateway", "lambda", "integrates_with", "Lambda 함수를 API 백엔드로 연결"),
    ("api-gateway", "cognito", "integrates_with", "Cognito User Pool로 API 인증"),
    ("api-gateway", "cloudwatch", "integrates_with", "API 호출 로그/메트릭을 CloudWatch로 전송"),
    # ── ALB dependency ───────────────────────────────────────────────────
    ("alb", "vpc", "depends_on", "ALB는 VPC 서브넷에 배치"),
    ("alb", "ec2", "integrates_with", "EC2 인스턴스를 대상 그룹으로 로드 밸런싱"),
    # ── Glue integrations ────────────────────────────────────────────────
    ("glue", "s3", "integrates_with", "S3를 데이터 레이크 스토리지로 활용"),
    ("glue", "athena", "integrates_with", "Glue Data Catalog을 Athena 테이블로 공유"),
    ("glue", "redshift", "integrates_with", "Redshift로 ETL 결과 적재"),
    ("glue", "rds", "integrates_with", "RDS에서 데이터 추출/적재"),
    # ── Kinesis integrations ─────────────────────────────────────────────
    ("kinesis", "s3", "integrates_with", "Firehose로 S3에 스트리밍 데이터 저장"),
    ("kinesis", "lambda", "integrates_with", "스트림 레코드를 Lambda로 실시간 처리"),
    ("kinesis", "redshift", "integrates_with", "Firehose로 Redshift에 데이터 적재"),
    # ── SageMaker integrations ───────────────────────────────────────────
    ("sagemaker", "s3", "integrates_with", "S3에서 학습 데이터 로드/모델 저장"),
    ("sagemaker", "ecs", "integrates_with", "ECR 컨테이너 이미지로 학습/추론 실행"),
    ("sagemaker", "iam", "integrates_with", "IAM 역할로 SageMaker 리소스 접근 제어"),
    ("sagemaker", "cloudwatch", "integrates_with", "학습 메트릭/엔드포인트 모니터링"),
    # ── Bedrock integrations ─────────────────────────────────────────────
    ("bedrock", "s3", "integrates_with", "S3에서 지식 베이스 데이터 소스 로드"),
    ("bedrock", "lambda", "integrates_with", "Lambda에서 Bedrock API 호출"),
    ("bedrock", "iam", "integrates_with", "IAM 정책으로 모델 접근 제어"),
    # ── Comprehend integrations ──────────────────────────────────────────
    ("comprehend", "s3", "integrates_with", "S3에서 분석 대상 텍스트 데이터 로드"),
    ("comprehend", "lambda", "integrates_with", "Lambda에서 Comprehend API 호출"),
    # ── Step Functions integrations ──────────────────────────────────────
    ("step-functions", "lambda", "integrates_with", "Lambda 함수를 워크플로 단계로 실행"),
    ("step-functions", "ecs", "integrates_with", "ECS 태스크를 워크플로 단계로 실행"),
    ("step-functions", "sns", "integrates_with", "워크플로에서 SNS 알림 전송"),
    ("step-functions", "sqs", "integrates_with", "워크플로에서 SQS 메시지 전송"),
    ("step-functions", "dynamodb", "integrates_with", "워크플로에서 DynamoDB 읽기/쓰기"),
    ("step-functions", "bedrock", "integrates_with", "워크플로에서 Bedrock 모델 호출"),
    # ── EventBridge integrations ─────────────────────────────────────────
    ("eventbridge", "lambda", "integrates_with", "이벤트 규칙으로 Lambda 트리거"),
    ("eventbridge", "sqs", "integrates_with", "이벤트를 SQS 큐로 전달"),
    ("eventbridge", "sns", "integrates_with", "이벤트를 SNS 토픽으로 전달"),
    ("eventbridge", "step-functions", "integrates_with", "이벤트로 Step Functions 실행 시작"),
    # ── CloudWatch integrations ──────────────────────────────────────────
    ("cloudwatch", "ec2", "integrates_with", "EC2 인스턴스 메트릭/로그 수집"),
    ("cloudwatch", "ecs", "integrates_with", "ECS 컨테이너 메트릭/로그 수집"),
    ("cloudwatch", "rds", "integrates_with", "RDS 인스턴스 메트릭 모니터링"),
    ("cloudwatch", "lambda", "integrates_with", "Lambda 실행 로그/메트릭 자동 수집"),
    ("cloudwatch", "sns", "integrates_with", "알람 발생 시 SNS 토픽으로 알림 전송"),
    # ── CloudTrail integrations ──────────────────────────────────────────
    ("cloudtrail", "s3", "integrates_with", "API 호출 로그를 S3 버킷에 저장"),
    ("cloudtrail", "cloudwatch", "integrates_with", "CloudTrail 로그를 CloudWatch Logs로 전송"),
    # ── CloudFormation integrations ──────────────────────────────────────
    ("cloudformation", "iam", "integrates_with", "IAM으로 스택 생성 권한 제어"),
    ("cloudformation", "s3", "integrates_with", "S3에 템플릿 파일 저장"),
    ("cloudformation", "lambda", "integrates_with", "커스텀 리소스로 Lambda 함수 실행"),
    ("cloudformation", "cloudwatch", "integrates_with", "스택 이벤트를 CloudWatch로 모니터링"),
    # ── ElastiCache dependency ───────────────────────────────────────────
    ("elasticache", "vpc", "depends_on", "ElastiCache 클러스터는 VPC 서브넷 그룹 필요"),
    # ── RDS dependency ───────────────────────────────────────────────────
    ("rds", "vpc", "depends_on", "RDS 인스턴스는 VPC 서브넷 그룹에서 실행"),
    ("rds", "kms", "integrates_with", "KMS 키로 저장 데이터 암호화"),
    # ── Redshift dependency ──────────────────────────────────────────────
    ("redshift", "vpc", "depends_on", "Redshift 클러스터는 VPC 내에서 운영"),
    ("redshift", "s3", "integrates_with", "S3에서 데이터 로드(COPY) 및 언로드(UNLOAD)"),
    # ── DynamoDB integrations ────────────────────────────────────────────
    ("dynamodb", "cloudwatch", "integrates_with", "DynamoDB 테이블 메트릭을 CloudWatch로 전송"),
    ("dynamodb", "kms", "integrates_with", "KMS 키로 저장 데이터 암호화"),
    # ── S3 integrations ──────────────────────────────────────────────────
    ("s3", "kms", "integrates_with", "KMS 키로 객체 서버 측 암호화(SSE-KMS)"),
    ("s3", "cloudtrail", "integrates_with", "S3 API 호출을 CloudTrail로 감사"),
    ("s3", "eventbridge", "integrates_with", "S3 이벤트 알림을 EventBridge로 전송"),
    # ── IAM broad integrations ───────────────────────────────────────────
    ("iam", "cloudtrail", "integrates_with", "IAM API 호출을 CloudTrail로 감사"),
    # ── EMR integrations ─────────────────────────────────────────────────
    ("emr", "s3", "integrates_with", "S3를 EMRFS 기반 데이터 스토리지로 활용"),
    ("emr", "vpc", "depends_on", "EMR 클러스터는 VPC 내에서 실행"),
    ("emr", "ec2", "depends_on", "EMR 노드로 EC2 인스턴스 사용"),
    # ── Athena integrations ──────────────────────────────────────────────
    ("athena", "s3", "integrates_with", "S3에 저장된 데이터를 직접 쿼리"),
    ("athena", "glue", "integrates_with", "Glue Data Catalog을 메타스토어로 사용"),
    # ── SNS-SQS fan-out ──────────────────────────────────────────────────
    ("sns", "sqs", "integrates_with", "SNS→SQS 팬아웃 패턴으로 메시지 분배"),
    ("sns", "lambda", "integrates_with", "SNS 구독으로 Lambda 트리거"),
    # ── EBS dependency ───────────────────────────────────────────────────
    ("ebs", "ec2", "depends_on", "EC2 인스턴스에 블록 스토리지로 연결"),
    ("ebs", "kms", "integrates_with", "KMS 키로 볼륨 암호화"),
    # ── EFS dependency ───────────────────────────────────────────────────
    ("efs", "vpc", "depends_on", "EFS 마운트 타겟은 VPC 서브넷에 배치"),
    ("efs", "ec2", "integrates_with", "여러 EC2 인스턴스에서 동시 마운트"),
    # ── Cognito integrations ─────────────────────────────────────────────
    ("cognito", "lambda", "integrates_with", "커스텀 인증 트리거로 Lambda 실행"),
    ("cognito", "iam", "integrates_with", "자격 증명 풀로 임시 IAM 자격 증명 발급"),
    # ── Route 53 integrations ────────────────────────────────────────────
    ("route53", "alb", "integrates_with", "ALB를 Alias 레코드로 DNS 연결"),
    ("route53", "cloudfront", "integrates_with", "CloudFront를 Alias 레코드로 DNS 연결"),
    ("route53", "s3", "integrates_with", "S3 정적 웹 호스팅을 DNS 연결"),
    # ── Alternatives ─────────────────────────────────────────────────────
    ("ecs", "eks", "alternative_to", "AWS 네이티브 vs Kubernetes 컨테이너 오케스트레이션"),
    ("sqs", "kinesis", "alternative_to", "메시지 큐 vs 스트리밍 — 사용 패턴에 따라 선택"),
    ("rds", "dynamodb", "alternative_to", "관계형 vs NoSQL — 워크로드 특성에 따라 선택"),
    ("athena", "redshift", "alternative_to", "서버리스 쿼리 vs 전용 웨어하우스"),
    ("sns", "eventbridge", "alternative_to", "단순 Pub/Sub vs 이벤트 라우팅/필터링"),
]


class Command(BaseCommand):
    help = "35개 AWS 클라우드 서비스와 50+ 관계를 시딩합니다."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== AWS Cloud Services 시딩 시작 ===\n"))

        # ── 1. 서비스 생성/업데이트 ──────────────────────────────────────
        created_count = 0
        updated_count = 0
        svc_map = {}  # slug → CloudServiceEntry

        for svc_data in SERVICES:
            slug = svc_data["slug"]
            defaults = {
                "name": svc_data["name"],
                "provider": svc_data["provider"],
                "service_domain": svc_data["service_domain"],
                "launch_year": svc_data["launch_year"],
                "is_serverless": svc_data["is_serverless"],
                "is_managed": svc_data["is_managed"],
                "pricing_model": svc_data["pricing_model"],
                "importance": svc_data["importance"],
                "description": svc_data["description"],
                "key_detail": svc_data["key_detail"],
                "use_cases": svc_data["use_cases"],
                "docs_url": svc_data["docs_url"],
                "icon_name": svc_data["icon_name"],
            }
            obj, created = CloudServiceEntry.objects.update_or_create(
                slug=slug, defaults=defaults
            )
            svc_map[slug] = obj
            if created:
                created_count += 1
                self.stdout.write(f"  [NEW] {obj.name} ({slug})")
            else:
                updated_count += 1
                self.stdout.write(f"  [UPD] {obj.name} ({slug})")

        self.stdout.write(
            f"\n  서비스: {created_count}개 생성, {updated_count}개 업데이트 "
            f"(총 {len(SERVICES)}개)\n"
        )

        # ── 2. 관계 생성 ────────────────────────────────────────────────
        rel_created = 0
        rel_skipped = 0

        for from_slug, to_slug, rel_type, desc in RELATIONS:
            from_svc = svc_map.get(from_slug)
            to_svc = svc_map.get(to_slug)
            if not from_svc or not to_svc:
                self.stdout.write(
                    self.style.WARNING(
                        f"  [SKIP] {from_slug} → {to_slug}: 서비스를 찾을 수 없음"
                    )
                )
                rel_skipped += 1
                continue

            _, created = CloudServiceRelation.objects.get_or_create(
                from_service=from_svc,
                to_service=to_svc,
                relation_type=rel_type,
                defaults={"description": desc},
            )
            if created:
                rel_created += 1
            else:
                rel_skipped += 1

        self.stdout.write(
            f"\n  관계: {rel_created}개 생성, {rel_skipped}개 스킵 "
            f"(총 {len(RELATIONS)}개 정의)\n"
        )

        # ── 3. 관련 포스트 연결 ─────────────────────────────────────────
        linked_count = 0
        for svc in CloudServiceEntry.objects.filter(provider="aws"):
            post = Post.objects.filter(slug__icontains=svc.slug).first()
            if post and svc.related_post != post:
                svc.related_post = post
                svc.save(update_fields=["related_post"])
                linked_count += 1
                self.stdout.write(f"  [LINK] {svc.slug} → {post.slug}")

        self.stdout.write(f"\n  포스트 연결: {linked_count}개\n")

        self.stdout.write(self.style.SUCCESS(
            f"\n=== 시딩 완료! 서비스 {len(SERVICES)}개, "
            f"관계 {rel_created}개 생성 ===\n"
        ))
