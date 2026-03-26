# AWS & Cloud 인프라 학습 가이드

## 개요

Amazon Web Services(AWS)는 200개 이상의 서비스를 제공하는 세계 최대의 클라우드 플랫폼입니다. 컴퓨팅, 스토리지, 데이터베이스, 네트워킹, 보안, 분석, AI/ML 등 IT 인프라의 모든 영역을 포괄하며, 현대 소프트웨어 개발과 운영의 핵심 기반이 되었습니다.

이 가이드는 AWS 클라우드 인프라의 핵심 서비스를 **10개 도메인별로 체계적으로 정리**합니다. 각 서비스의 역할, 상호 관계, 그리고 실무에서의 활용 패턴을 이해하는 데 초점을 맞춥니다.

### 왜 AWS를 체계적으로 공부해야 하는가?

AWS 서비스의 수는 압도적이지만, 핵심 서비스를 도메인별로 분류하면 명확한 구조가 보입니다. 각 도메인의 대표 서비스를 먼저 이해하고, 필요에 따라 세부 서비스로 확장하는 접근이 효율적입니다. 또한 AWS 자격증(SAA, SAP, MLS 등)을 준비하는 데도 이 체계적 접근이 큰 도움이 됩니다.

---

## 10개 도메인 개요

### 1. Compute (컴퓨팅)

클라우드의 가장 기본적인 구성 요소입니다. 서버를 프로비저닝하고 애플리케이션을 실행합니다.

| 서비스 | 핵심 기능 | 관련 포스트 |
|--------|----------|------------|
| EC2 | 가상 서버 (인스턴스) | [EC2 M1 Mac](/post/amazon-ec2-m1-mac-인스턴스) |
| EC2 Enhanced Networking | 네트워크 성능 향상 | [Enhanced Networking](/post/amazon-ec2-enhanced-networking--네트워크-성능-향상-기능) |
| Auto Scaling Group | 자동 스케일링 | [ASG](/post/auto-scaling-groupasg) |
| ECS | 컨테이너 오케스트레이션 | [ECS](/post/amazon-elastic-container-service-amazon-ecs) |
| Elastic Beanstalk | PaaS (자동 배포/관리) | [Elastic Beanstalk](/post/aws-elastic-beanstalk-개요) |
| Lightsail | 간편한 가상 서버 | [Lightsail](/post/amazon-lightsail-간단하고-저비용의-aws-클라우드-플랫폼) |
| App Runner | 컨테이너 앱 실행 | [App Runner](/post/aws-app-runner-개요-및-활용) |
| Batch | 배치 컴퓨팅 | [AWS Batch](/post/aws-batch) |
| Wavelength | 5G 엣지 컴퓨팅 | [Wavelength](/post/aws-wavelength-개요-5g-엣지-컴퓨팅) |
| Outposts | 온프레미스 AWS 확장 | [Outposts](/post/aws-outposts-온프레미스에서의-aws-확장) |

**핵심 흐름**: EC2 (기본) → ASG (스케일링) → ECS (컨테이너) → App Runner (서버리스 컨테이너) → Lambda (이벤트 기반)

### 2. Storage (스토리지)

데이터를 저장하고 관리하는 서비스입니다.

| 서비스 | 핵심 기능 | 관련 포스트 |
|--------|----------|------------|
| S3 | 객체 스토리지 | [S3](/post/amazon-simple-storage-serviceamazon-s3-개요) |
| Storage Gateway | 하이브리드 스토리지 | [Storage Gateway](/post/aws-storage-gateway) |
| DataSync | 데이터 전송 자동화 | [DataSync](/post/aws-datasync-개요-및-주요-기능-정리) |
| Transfer Family | SFTP/FTPS 관리형 | [Transfer Family](/post/aws-transfer-family) |
| Backup | 중앙화된 백업 | [Backup](/post/aws-backup-개요-및-주요-기능) |

**핵심**: S3는 AWS의 가장 핵심 서비스 중 하나입니다. 거의 모든 AWS 서비스가 S3와 연동됩니다.

### 3. Database (데이터베이스)

다양한 유형의 데이터베이스를 관리형 서비스로 제공합니다.

| 서비스 | 유형 | 관련 포스트 |
|--------|------|------------|
| RDS | 관계형 DB | [RDS](/post/amazon-rds) |
| Aurora | 고성능 관계형 DB | [Aurora](/post/amazon-aurora-개요), [Aurora PostgreSQL](/post/amazon-aurora-postgresql) |
| DynamoDB | NoSQL (Key-Value) | [DynamoDB Streams](/post/amazon-dynamodb-streams) |
| ElastiCache | 인메모리 캐시 | [ElastiCache](/post/amazon-elasticache인메모리-캐시-서비스-개요), [Redis](/post/amazon-elasticache-for-redis-redis-oss-클러스터-개요) |
| Redshift | 데이터 웨어하우스 | [Redshift](/post/amazon-redshift-개요) |
| Timestream | 시계열 DB | [Timestream](/post/amazon-timestream--서버리스-시계열-데이터베이스) |
| OpenSearch | 검색/분석 엔진 | [OpenSearch](/post/amazon-opensearch-service-개요) |

**Redshift 심화**: Redshift는 데이터 분석의 핵심 서비스입니다.

| Redshift 기능 | 관련 포스트 |
|--------------|------------|
| 클러스터 관리 | [Cluster](/post/amazon-redshift-cluster) |
| 테이블 설계 | [Table](/post/amazon-redshift-table) |
| 뷰(View) | [View](/post/amazon-redshift-view뷰-개요) |
| Materialized View | [MV](/post/amazon-redshift-materialized-viewmv) |
| Spectrum | [Spectrum](/post/amazon-redshift-spectrum) |
| Federated Query | [Federated Query](/post/amazon-redshift-federated-query-요약-및-athena-비교) |
| SUPER 타입 | [SUPER](/post/amazon-redshift-super) |
| UNLOAD | [UNLOAD](/post/amazon-redshift-unload란) |
| ML 통합 | [Redshift ML](/post/amazon-redshift-ml--sql로-수행하는-redshift-내-머신러닝) |
| Data API | [Data API](/post/amazon-redshift-data-api-소개) |
| Query Editor v2 | [Query Editor v2](/post/amazon-redshift-query-editor-v2) |
| Advisor | [Advisor](/post/amazon-redshift-advisor--쿼리-기반-성능비용-최적화-권장) |

### 4. Networking (네트워킹)

VPC, 로드밸런서, DNS, CDN 등 네트워크 인프라를 구성합니다.

| 서비스 | 핵심 기능 | 관련 포스트 |
|--------|----------|------------|
| VPC | 가상 프라이빗 네트워크 | - |
| VPC Flow Logs | 네트워크 트래픽 로깅 | [Flow Logs](/post/vpc-flow-logs) |
| Internet Gateway | VPC 인터넷 연결 | [IGW](/post/internet-gateway-igw) |
| NAT Gateway | 프라이빗 서브넷 아웃바운드 | [NAT Gateway](/post/nat-gateway-nat-게이트웨이) |
| Virtual Private Gateway | VPN 연결 | [VGW](/post/virtual-private-gateway-vgw) |
| Elastic IP | 고정 공인 IP | [EIP](/post/elastic-ip-eip) |
| CloudFront | CDN | [CloudFront](/post/amazon-cloudfront) |
| Transit Gateway | 대규모 네트워크 연결 | [TGW](/post/aws-transit-gateway-tgw) |
| Direct Connect | 전용선 연결 | [Direct Connect](/post/aws-direct-connect-정리), [DX Location](/post/aws-direct-connect-location), [DX Gateway](/post/aws-direct-connect-gateway-dx-gateway-개요), [Resiliency](/post/aws-direct-connect--resiliency-복원력-설계) |
| PrivateLink | 프라이빗 서비스 접근 | [PrivateLink](/post/aws-privatelink-개요) |
| Global Accelerator | 글로벌 네트워크 가속 | [Global Accelerator](/post/aws-global-accelerator) |
| App Mesh | 서비스 메시 | [App Mesh](/post/aws-app-mesh) |
| Cloud Map | 서비스 디스커버리 | [Cloud Map](/post/aws-cloud-map--서비스-디스커버리-및-리소스-매핑-서비스-개요) |
| VPN CloudHub | 다중 사이트 VPN | [VPN CloudHub](/post/aws-vpn-cloudhub) |
| TGW ECMP | 대역폭 확장 | [TGW ECMP](/post/aws-transit-gateway에서-site-to-site-vpn-ecmp-equal-cost-multi-path) |
| Bastion Host | 보안 접속 중계 | [Bastion Host](/post/bastion-host란) |

### 5. Security (보안)

IAM, 암호화, 방화벽, 감사 등 보안 인프라를 제공합니다.

| 서비스 | 핵심 기능 | 관련 포스트 |
|--------|----------|------------|
| ACM | SSL/TLS 인증서 관리 | [ACM](/post/aws-certificate-manager-acm) |
| CloudHSM | 하드웨어 보안 모듈 | [CloudHSM](/post/aws-cloudhsm-hardware-security-module) |
| Secrets Manager | 비밀 관리 | [Secrets Manager](/post/aws-secrets-manager), [BatchGetSecretValue](/post/aws-secrets-manager에-batchgetsecretvalue가-존재하나요) |
| WAF | 웹 방화벽 | [WAF](/post/aws-waf-적용-대상-및-주요-특징), [WAF+Shield](/post/aws-waf와-shield를-이용한-ddos-방어) |
| Network Firewall | 네트워크 방화벽 | [Network Firewall](/post/aws-network-firewall란) |
| Security Hub | 보안 중앙 관리 | [Security Hub](/post/aws-security-hub란) |
| CloudTrail | API 감사 로그 | [CloudTrail](/post/aws-cloudtrail이란) |

### 6. Analytics (분석)

데이터 수집, 처리, 분석, 시각화 파이프라인을 구성합니다.

| 서비스 | 핵심 기능 | 관련 포스트 |
|--------|----------|------------|
| Athena | 서버리스 SQL 쿼리 | [Athena](/post/amazon-athena-개요-및-활용), [Federated Query](/post/amazon-athena-federated-query), [Workgroup vs Data Catalog](/post/amazon-athena-workgroup-vs-data-catalog-정리) |
| Glue | 서버리스 ETL | [Glue](/post/aws-glue-개요-및-주요-특징) |
| QuickSight | BI/시각화 | [QuickSight](/post/amazon-quicksight), [ML Insights](/post/amazon-quicksight-ml-insights), [SPICE](/post/amazon-quicksight-인메모리-분석-엔진-spice-개요) |
| Kinesis | 실시간 스트리밍 | [KDS](/post/amazon-kinesis-data-streams-kds-개요), [Firehose](/post/amazon-kinesis-data-firehose), [KPU](/post/amazon-kinesis-요약-kpu-기반-과금-및-주요-특징) |
| Lake Formation | 데이터 레이크 | [Lake Formation](/post/aws-lake-formation-소개--데이터-레이크-구축과-보안-관리) |
| DataZone | 데이터 거버넌스 | [DataZone](/post/amazon-datazone-개요-및-핵심-기능) |
| Data Exchange | 데이터 교환 | [Data Exchange](/post/aws-data-exchange-개요-및-활용) |
| Clean Rooms | 프라이버시 보존 분석 | [Clean Rooms](/post/aws-clean-rooms-개요-및-활용) |
| AppFlow | SaaS 데이터 통합 | [AppFlow](/post/amazon-appflow-개요-saas와-aws-간-보안자동화-데이터-통합) |

**Glue 심화**: Glue는 AWS 분석 파이프라인의 핵심입니다.

| Glue 기능 | 관련 포스트 |
|----------|------------|
| Job | [Glue Job](/post/aws-glue-job-개요) |
| Crawler | [Crawler](/post/aws-glue-crawler-개요) |
| Data Catalog | [Data Catalog](/post/aws-glue-data-catalog) |
| Data Quality | [Data Quality](/post/aws-glue-data-quality) |
| DataBrew | [DataBrew](/post/aws-glue-databrew-개요-및-핵심-기능-정리) |
| Studio | [Studio](/post/aws-glue-studio-개요-및-핵심-포인트) |
| Spark | [Glue for Spark](/post/aws-glue-for-apache-spark) |
| Classifier | [Classifier](/post/aws-glue-classifier-개요) |
| DynamicFrame | [DynamicFrame](/post/aws-glue-dynamicframe란) |
| FindMatches | [FindMatches](/post/aws-glue-findmatches) |
| Job Bookmark | [Job Bookmark](/post/aws-glue-job-bookmark) |
| ResolveChoice | [ResolveChoice](/post/aws-glue-resolvechoice) |
| Trigger | [Trigger](/post/aws-glue-trigger) |
| Workflow | [Workflow](/post/aws-glue-workflow) |

**Kinesis 심화**:

| Kinesis 기능 | 관련 포스트 |
|-------------|------------|
| Data Streams | [KDS](/post/amazon-kinesis-data-streams-kds-개요) |
| Data Firehose | [Firehose](/post/amazon-kinesis-data-firehose) |
| Agent | [Kinesis Agent](/post/amazon-kinesis-agent) |
| KCL | [KCL](/post/amazon-kinesis-client-librarykcl--개요와-핵심-기능) |
| KPL | [KPL](/post/amazon-kinesis-producer-librarykpl-정리--aggregation과-consumer-영향) |
| Flink | [Flink](/post/amazon-managed-service-for-apache-flink-구-amazon-kinesis-data-analytics-for-apache-flink) |

### 7. AI/ML (인공지능/머신러닝)

AI/ML 모델의 학습, 배포, 관리를 위한 서비스입니다.

| 서비스 | 핵심 기능 | 관련 포스트 |
|--------|----------|------------|
| Bedrock | 생성형 AI 서비스 | [Bedrock](/post/amazon-bedrock), [Agents](/post/amazon-bedrock-agents), [Guardrails](/post/amazon-bedrock-guardrails), [Studio](/post/amazon-bedrock-studio) |
| SageMaker | ML 플랫폼 | [SageMaker](/post/amazon-sagemaker-ai-개요) |
| Q Developer | AI 코딩 어시스턴트 | [Q Developer](/post/amazon-q-developer) |
| Q Business | 엔터프라이즈 AI 비서 | [Q Business](/post/amazon-q-business--엔터프라이즈용-생성형-ai-기반-업무-비서) |
| Comprehend | 자연어 이해 | [Comprehend](/post/amazon-comprehend-개요) |
| Rekognition | 이미지/비디오 분석 | [Rekognition](/post/amazon-rekognition), [Content Moderation](/post/amazon-rekognition-content-moderation-소개) |
| Personalize | 추천 시스템 | [Personalize](/post/amazon-personalize-개요) |
| Polly | 텍스트→음성 | [Polly](/post/amazon-polly--텍스트를-음성으로-변환하는-서비스) |
| A2I | 인간 검토 워크플로우 | [A2I](/post/amazon-augmented-ai-amazon-a2i) |
| Panorama | 엣지 컴퓨터 비전 | [Panorama](/post/aws-panorama-개요-및-활용-가이드) |

**SageMaker 심화**: SageMaker는 ML 라이프사이클 전체를 관리하는 플랫폼입니다.

| SageMaker 기능 | 관련 포스트 |
|---------------|------------|
| Domain | [도메인](/post/amazon-sagemaker-도메인--도메인을-운영한다는-의미) |
| Studio | [Studio](/post/amazon-sagemaker-studio), [Studio Classic](/post/amazon-sagemaker-studio-classic) |
| Notebook | [Notebook](/post/amazon-sagemaker-notebook) |
| Autopilot | [Autopilot](/post/amazon-sagemaker-autopilot) |
| Canvas | [Canvas](/post/amazon-sagemaker-canvas) |
| JumpStart | [JumpStart](/post/amazon-sagemaker-jumpstart), [개요](/post/amazon-sagemaker-jumpstart-개요) |
| Data Wrangler | [Data Wrangler](/post/amazon-sagemaker-data-wrangler), [소개](/post/amazon-sagemaker-data-wrangler-소개) |
| Feature Store | [Feature Store](/post/amazon-sagemaker-feature-store) |
| Experiments | [Experiments](/post/amazon-sagemaker-experiments-개요) |
| Clarify | [Clarify](/post/amazon-sagemaker-clarify) |
| Debugger | [Debugger](/post/amazon-sagemaker-debugger) |
| Model Monitor | [Model Monitor](/post/amazon-sagemaker-model-monitor) |
| Model Registry | [Model Registry](/post/amazon-sagemaker-model-registry), [워크플로](/post/amazon-sagemaker-model-registry-개요-및-워크플로) |
| Model Card | [모델 카드](/post/amazon-sagemaker-모델-카드), [소개](/post/amazon-sagemaker-모델-카드-소개) |
| Neo | [Neo](/post/amazon-sagemaker-neo) |
| Ground Truth | [Ground Truth](/post/amazon-sagemaker-ground-truth-소개) |
| Inference Recommender | [Inference Recommender](/post/amazon-sagemaker-inference-recommender) |
| Real-time Inference | [Real-time](/post/amazon-sagemaker-real-time-inference) |
| Batch Transform | [Batch Transform](/post/amazon-sagemaker-batch-transform) |
| Async Inference | [Async](/post/amazon-sagemaker-asynchronous-inference) |
| Serverless Inference | [Serverless](/post/amazon-sagemaker-serverless-inference), [서버리스 추론](/post/amazon-sagemaker-서버리스-추론) |
| Endpoint | [Endpoint](/post/amazon-sagemaker-엔드포인트endpoint-개요) |

### 8. DevTools (개발자 도구)

CI/CD, 개발 환경, 코드 관리 등 개발 워크플로우를 지원합니다.

| 서비스 | 핵심 기능 | 관련 포스트 |
|--------|----------|------------|
| CodePipeline | CI/CD 파이프라인 | [CodePipeline](/post/aws-codepipeline) |
| CodeDeploy | 배포 자동화 | [CodeDeploy](/post/aws-codedeploy-빠른-개요) |
| CodeGuru | AI 코드 리뷰 | [CodeGuru](/post/amazon-codeguru--서비스-개요-및-활용-안내) |
| Cloud9 | 클라우드 IDE | [Cloud9](/post/aws-cloud9-개요-및-활용) |
| AppSync | GraphQL API | [AppSync](/post/aws-appsync-서버리스-graphql-및-실시간-api-서비스-개요) |
| API Gateway | REST/WebSocket API | [API Gateway](/post/amazon-api-gateway-소개) |

### 9. Management (관리)

계정 관리, 모니터링, 구성 관리, 거버넌스 등을 담당합니다.

| 서비스 | 핵심 기능 | 관련 포스트 |
|--------|----------|------------|
| Organizations | 멀티 계정 관리 | [Organizations](/post/aws-organizations--멀티-계정-관리와-중앙-거버넌스) |
| Control Tower | 랜딩 존 설정 | [Control Tower](/post/aws-control-tower-개요-및-구성), [Account Factory](/post/aws-control-tower-account-factory) |
| Systems Manager | 운영 관리 | [SSM](/post/aws-systems-manager-개요-및-주요-기능), [Parameter Store](/post/aws-systems-manager-parameter-store), [SSM Agent](/post/aws-systems-manager-agent-ssm-agent), [OpsItems](/post/aws-systems-manager-opsitems) |
| Config | 구성 변경 추적 | [Config](/post/aws-config-구성-변경-추적과-규정-준수-관리) |
| Trusted Advisor | 모범 사례 권장 | [Trusted Advisor](/post/aws-trusted-advisor-개요-및-활용-가이드) |
| Compute Optimizer | 리소스 최적화 | [Compute Optimizer](/post/aws-compute-optimizer-빠른-개요) |
| Health Dashboard | 서비스 상태 모니터링 | [Health Dashboard](/post/aws-health-dashboard--계정서비스-상태-모니터링) |
| Service Catalog | 서비스 카탈로그 | [Service Catalog](/post/aws-service-catalog-개요특징활용) |
| OpsWorks | 구성 관리 | [OpsWorks](/post/aws-opsworks-개요-및-활용-가이드) |
| Well-Architected Framework | 아키텍처 모범 사례 | [WAF](/post/aws-well-architected-framework) |

### 10. Integration (통합)

서비스 간 연결, 이벤트 처리, 워크플로우 오케스트레이션을 담당합니다.

| 서비스 | 핵심 기능 | 관련 포스트 |
|--------|----------|------------|
| Step Functions | 워크플로우 오케스트레이션 | [Step Functions](/post/aws-step-functions-개요-및-사용-사례) |
| EventBridge | 이벤트 버스 | [Scheduler](/post/amazon-eventbridge-scheduler), [가이드](/post/amazon-eventbridge-scheduler-개요-및-활용-가이드) |
| Amazon MQ | 메시지 브로커 | [Amazon MQ](/post/amazon-mq-표준-메시지-브로커의-완전관리형-서비스) |

---

## 핵심 아키텍처 패턴

### 1. 3-Tier 웹 애플리케이션

가장 기본적인 AWS 아키텍처입니다.

```
Internet → CloudFront → ALB → EC2/ECS (App) → RDS/Aurora (DB)
                                    ↕
                              ElastiCache (Cache)
                                    ↕
                                S3 (Storage)
```

관련 포스트: [CloudFront](/post/amazon-cloudfront), [ECS](/post/amazon-elastic-container-service-amazon-ecs), [RDS](/post/amazon-rds), [S3](/post/amazon-simple-storage-serviceamazon-s3-개요)

### 2. 서버리스 아키텍처

서버 관리 없이 이벤트 기반으로 동작하는 아키텍처입니다.

```
API Gateway → Lambda → DynamoDB
                 ↕
            S3 / SQS / SNS
```

관련 포스트: [API Gateway](/post/amazon-api-gateway-소개)

### 3. 데이터 분석 파이프라인

데이터 수집부터 분석, 시각화까지의 파이프라인입니다.

```
Sources → Kinesis/Glue → S3 Data Lake → Athena/Redshift → QuickSight
                                ↕
                         Lake Formation (거버넌스)
```

관련 포스트: [Kinesis](/post/amazon-kinesis-data-streams-kds-개요), [Glue](/post/aws-glue-개요-및-주요-특징), [Athena](/post/amazon-athena-개요-및-활용), [Redshift](/post/amazon-redshift-개요), [QuickSight](/post/amazon-quicksight)

### 4. ML 파이프라인

ML 모델의 학습부터 배포까지의 파이프라인입니다.

```
Data → SageMaker (Train) → Model Registry → Endpoint (Inference)
  ↕                              ↕
S3 (Data)              Model Monitor (모니터링)
```

관련 포스트: [SageMaker](/post/amazon-sagemaker-ai-개요), [Bedrock](/post/amazon-bedrock)

### 5. 하이브리드 네트워크

온프레미스와 AWS를 연결하는 아키텍처입니다.

```
On-premises → Direct Connect / VPN → Transit Gateway → VPCs
                                              ↕
                                      PrivateLink (서비스 접근)
```

관련 포스트: [Direct Connect](/post/aws-direct-connect-정리), [TGW](/post/aws-transit-gateway-tgw), [PrivateLink](/post/aws-privatelink-개요)

### 6. 마이그레이션

온프레미스에서 AWS로의 마이그레이션 전략입니다.

| 서비스 | 역할 | 관련 포스트 |
|--------|------|------------|
| Migration Hub | 마이그레이션 추적 | [Migration Hub](/post/aws-migration-hub--마이그레이션-중앙-추적관리-서비스) |
| ADS | 서버 인벤토리 수집 | [ADS](/post/aws-application-discovery-serviceads-개요-및-활용) |
| MGN | 서버 마이그레이션 | [MGN](/post/aws-application-migration-service-aws-mgn-개요) |
| RDS Blue/Green | DB 마이그레이션 | [Blue/Green](/post/amazon-rds-bluegreen-배포와-카나리canary-배포-개요) |

---

## 추천 학습 경로

### 초심자 (AWS 입문)

기본 서비스를 이해하고 간단한 아키텍처를 구성합니다.

1. **기본 개념**: [S3](/post/amazon-simple-storage-serviceamazon-s3-개요) → [RDS](/post/amazon-rds) → [CloudFront](/post/amazon-cloudfront)
2. **네트워킹 기초**: [IGW](/post/internet-gateway-igw) → [NAT Gateway](/post/nat-gateway-nat-게이트웨이) → [VPC Flow Logs](/post/vpc-flow-logs)
3. **보안 기초**: [ACM](/post/aws-certificate-manager-acm) → [Secrets Manager](/post/aws-secrets-manager)
4. **컴퓨팅**: [ECS](/post/amazon-elastic-container-service-amazon-ecs) → [ASG](/post/auto-scaling-groupasg)
5. **관리**: [Organizations](/post/aws-organizations--멀티-계정-관리와-중앙-거버넌스) → [CloudTrail](/post/aws-cloudtrail이란)

### 중급 (아키텍트 역량)

복잡한 아키텍처를 설계하고 최적화합니다. SAA 자격증 수준.

1. **고급 네트워킹**: [Direct Connect](/post/aws-direct-connect-정리) → [TGW](/post/aws-transit-gateway-tgw) → [PrivateLink](/post/aws-privatelink-개요)
2. **데이터 분석**: [Glue](/post/aws-glue-개요-및-주요-특징) → [Athena](/post/amazon-athena-개요-및-활용) → [Redshift](/post/amazon-redshift-개요) → [QuickSight](/post/amazon-quicksight)
3. **스트리밍**: [Kinesis](/post/amazon-kinesis-data-streams-kds-개요) → [Firehose](/post/amazon-kinesis-data-firehose) → [Flink](/post/amazon-managed-service-for-apache-flink-구-amazon-kinesis-data-analytics-for-apache-flink)
4. **보안 심화**: [WAF](/post/aws-waf-적용-대상-및-주요-특징) → [Security Hub](/post/aws-security-hub란) → [Config](/post/aws-config-구성-변경-추적과-규정-준수-관리)
5. **거버넌스**: [Control Tower](/post/aws-control-tower-개요-및-구성) → [Lake Formation](/post/aws-lake-formation-소개--데이터-레이크-구축과-보안-관리)

### 고급 (AI/ML 특화)

AWS에서 AI/ML 파이프라인을 구축합니다. MLS 자격증 수준.

1. **ML 플랫폼**: [SageMaker](/post/amazon-sagemaker-ai-개요) 전체 기능 심화
2. **생성형 AI**: [Bedrock](/post/amazon-bedrock) → [Agents](/post/amazon-bedrock-agents) → [Guardrails](/post/amazon-bedrock-guardrails)
3. **AI 서비스**: [Comprehend](/post/amazon-comprehend-개요) → [Rekognition](/post/amazon-rekognition) → [Personalize](/post/amazon-personalize-개요)
4. **MLOps**: Model Registry → Model Monitor → Endpoint 관리
5. **코딩 지원**: [Q Developer](/post/amazon-q-developer) → [Q Business](/post/amazon-q-business--엔터프라이즈용-생성형-ai-기반-업무-비서)

---

## 관련 카테고리

- [AI/ML 아키텍처 로드맵](/post/ai-ml-architecture-roadmap) — AI/ML 기술 전체 지형도
- [머신러닝 기초부터 실전까지](/post/ml-fundamentals-roadmap) — ML 이론과 실습
