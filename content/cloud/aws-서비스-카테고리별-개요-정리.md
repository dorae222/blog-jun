---
title: AWS 서비스 카테고리별 개요 (정리)
slug: "aws-서비스-카테고리별-개요-정리"
category: cloud
tags: ["analytics", "aws", "aws-services", "cloud", "containers", "database", "migration", "monitoring", "security", "serverless"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.469798+00:00"
---

[AWS 서비스 소개 링크](https://docs.aws.amazon.com/whitepapers/latest/aws-overview/amazon-web-services-cloud-platform.html)

- Security, Identity, and Compliance
- Compute
- Networking and Content Delivery
- Storage
- Database
- Migration and Transfer
- Management and Governance
- Application Integration
- Analytics
- Containers
- Cloud Financial Management
- Serverless
- Developer Tools
- Basic Concept


## 📊 Analytics

| 개념                                            | 설명                       | 키워드 및 예제 상황      |
| --------------------------------------------- | ------------------------ | ---------------- |
| Amazon Athena                             | S3에 저장된 데이터를 SQL로 분석     | S3 쿼리, 분석 용이      |
| AWS Data Exchange                         | 타사 데이터셋 구독 및 다운로드        | 데이터 제공자와 소비자 연결  |
| AWS Data Pipeline                         | ETL 작업 자동화 서비스           | 주기적 데이터 이동       |
| Amazon EMR      | Hadoop/Spark 기반 빅데이터 처리  | 대규모 데이터 분석       |
| AWS Glue                                  | ETL 서버리스 서비스             | 다양한 소스에서 변환 및 적재 |
| Amazon Kinesis                            | 스트리밍 데이터 처리              | 실시간 분석           |
| AWS Lake Formation                        | 데이터 레이크 생성 및 관리          | 권한 설정, 카탈로그 관리   |
| Amazon Managed Streaming for Apache Kafka | Kafka 완전관리형 서비스          | Kafka 활용         |
| Amazon OpenSearch Service                 | Elasticsearch 기반 검색 및 분석 | 로그 분석, 검색        |
| Amazon QuickSight                         | BI 도구, 대시보드 시각화          | 시각적 리포트 작성       |
| Amazon Redshift                           | 대규모 데이터 웨어하우스            | SQL 분석, BI 도구 통합 |

---

## 🔗 Application Integration

| 개념                                                       | 설명                           | 키워드 및 예제 상황     |
| -------------------------------------------------------- | ---------------------------- | --------------- |
| Amazon AppFlow                                       | SaaS 앱 간 데이터 통합              | Salesforce ↔ S3 |
| AWS AppSync                                          | GraphQL API 생성 및 관리          | 실시간 데이터 조회      |
| Amazon EventBridge                                   | 이벤트 기반 통합 서비스                | SaaS 이벤트 수신     |
| Amazon MQ                                            | ActiveMQ/RabbitMQ 호환 메시지 브로커 | 마이그레이션 시 유용     |
| Amazon SNS | 푸시 메시지 및 알림 전송               | Pub/Sub         |
| Amazon SQS         | 분산 메시지 큐 서비스                 | 비동기 처리          |
| AWS Step Functions                                   | 서버리스 워크플로우 관리                | Lambda 조합 순서화   |

---

## 💰 Cloud Financial Management

| 개념                            | 설명            | 키워드 및 예제 상황            |
| ----------------------------- | ------------- | ---------------------- |
| AWS Budgets               | 비용 및 사용량 모니터링 | 초과 지출 방지               |
| AWS Cost and Usage Report | 상세 비용 보고서 생성  | CSV 포맷 리포트             |
| AWS Cost Explorer         | 비용 분석 시각화 도구  | 월별 비교                  |
| Saving Plan               | 장기 사용 할인제     | EC2, Lambda 등 장기 할인 계약 |

---

## 🖥️ Compute

| 개념                                        | 설명                 | 키워드 및 예제 상황   |
| ----------------------------------------- | ------------------ | ------------- |
| AWS Batch                             | 대규모 배치 컴퓨팅 관리      | 자동 스케줄링       |
| AWS Elastic Beanstalk                 | 웹앱 배포 자동화          | PaaS 환경       |
| AWS Outposts                          | 온프레미스에 AWS 확장      | 하이브리드 클라우드    |
| AWS Serverless Application Repository | 서버리스 앱 공유 및 배포     | 빠른 배포         |
| VMware Cloud on AWS                   | VMware 워크로드 마이그레이션 | 하이브리드 클라우드 환경 |
| AWS Wavelength                        | 5G MEC 인프라 제공      | 초저지연 애플리케이션   |

---

## 📦 Containers

| 개념                                         | 설명                  | 키워드 및 예제 상황      |
| ------------------------------------------ | ------------------- | ---------------- |
| Amazon ECS Anywhere                    | 온프레미스 ECS 실행        | 로컬 환경에 컨테이너 배포   |
| Amazon EKS Anywhere                    | 온프레미스 Kubernetes 관리 | 로컬 EKS 클러스터      |
| Amazon EKS Distro                      | 오픈소스 Kubernetes 배포판 | 자체 환경에서 EKS 구성   |
| Amazon ECR                                 | 이미지 저장소 서비스         | Docker 이미지 저장    |
| ECS  | AWS 관리형 컨테이너 서비스    | 오케스트레이션, Fargate |
| EKS | Kubernetes 관리 서비스   | 자동화된 클러스터 운영     |

---

## 🗃️ Database

| 개념                                                            | 설명                         | 키워드 및 예제 상황         |
| ------------------------------------------------------------- | -------------------------- | ------------------- |
| Amazon Aurora                                             | MySQL/PostgreSQL 호환 고성능 DB | 자동 스케일              |
| Aurora Serverless                                         | 자동 확장형 Aurora              | 사용량 기반 요금           |
| Amazon DocumentDB                                         | MongoDB 호환 문서 DB           | JSON 기반 문서 저장       |
| Amazon DynamoDB                                           | NoSQL 키-값 DB               | 고성능, 저지연            |
| Amazon ElastiCache                                        | Redis/Memcached 캐시 서비스     | 인메모리 캐싱             |
| Amazon Keyspaces  | Apache Cassandra 호환 DB     | 분산형 NoSQL           |
| Amazon Neptune                                            | 그래프 DB                     | 관계형 데이터 분석          |
| Amazon QLDB | 변경 불가능한 원장형 DB             | 감사, 거래 기록           |
| Amazon RDS            | 관계형 DB 관리 서비스              | MySQL, PostgreSQL 등 |
| Amazon Redshift                                           | 데이터 웨어하우스                  | 대규모 쿼리 처리           |

---

## 🛠️ Developer Tools

| 개념            | 설명                  | 키워드 및 예제 상황         |
| ------------- | ------------------- | ------------------- |
| AWS X-Ray | 분산 애플리케이션의 성능 분석 도구 | 요청 추적, 성능 분석, 병목 탐지 |

---

## 🌐 프론트엔드 웹 및 모바일

| 개념                     | 설명                       | 키워드 및 예제 상황            |
| ---------------------- | ------------------------ | ---------------------- |
| AWS Amplify        | 프론트엔드 및 모바일 앱 개발 및 배포 도구 | 신속한 앱 배포, 호스팅          |
| Amazon API Gateway | API 생성 및 관리 서비스          | REST API, WebSocket 지원 |
| AWS Device Farm    | 실 디바이스 테스트 환경 제공         | 크로스 디바이스 테스트           |
| Amazon Pinpoint    | 고객 행동 분석 및 마케팅 캠페인 수행    | SMS, 이메일 캠페인           |

---

## 🤖 ML and AI

| 개념                        | 설명                 | 키워드 및 예제 상황         |
| ------------------------- | ------------------ | ------------------- |
| Amazon Comprehend     | NLP 서비스 (텍스트 분석)   | 감정 분석, 개체 추출        |
| Amazon Forecast       | 시계열 예측             | 수요 예측, 시간 기반 분석     |
| Amazon Fraud Detector | 이상 징후 탐지           | 사기 탐지 자동화           |
| Amazon Kendra         | 문서 기반 지능형 검색 서비스   | 기업 문서 검색 최적화        |
| Amazon Lex            | 음성 및 텍스트 챗봇 생성     | 챗봇, 대화형 인터페이스       |
| Amazon Polly          | 텍스트를 음성으로 변환       | TTS, 다국어 음성         |
| Amazon Rekognition    | 이미지 및 영상 분석        | 얼굴 인식, 객체 탐지        |
| Amazon SageMaker      | 머신러닝 모델 생성, 훈련, 배포 | End-to-End ML 파이프라인 |
| Amazon Textract       | 문서 내 텍스트/표 추출      | OCR, 폼 데이터 추출       |
| Amazon Transcribe     | 음성을 텍스트로 변환        | STT, 자막 생성          |
| Amazon Translate      | 기계 번역 서비스          | 자동 번역, 다국어 지원       |

---

## 🛡️ Management and Governance

| 개념                                     | 설명              | 키워드 및 예제 상황           |
| -------------------------------------- | --------------- | --------------------- |
| CloudFormation | 인프라를 코드로 관리     | 템플릿 기반 배포             |
| CloudTrail         | API 호출 추적       | 감사 로그 기록              |
| Amazon CloudWatch                  | 로그 및 지표 수집/모니터링 | 알람 설정, 모니터링           |
| AWS Compute Optimizer              | 리소스 최적화 추천      | 비용 절감, 과잉/과소 프로비저닝 탐지 |
| AWS Config                         | 리소스 변경 추적       | 구성 감사, 규정 준수          |
| AWS Control Tower                  | 다계정 환경 통합 관리    | 계정 템플릿, 정책 적용         |
| AWS Health Dashboard               | 서비스 상태 실시간 확인   | 운영 이슈 탐지              |
| AWS License Manager                | 라이선스 추적 및 관리    | 소프트웨어 자산 관리           |
| Amazon Managed Grafana             | 모니터링 대시보드       | CloudWatch 시각화        |
| AWS Management Console             | AWS 서비스 웹 인터페이스 | GUI 기반 관리             |
| AWS Organizations                  | 계정 및 결제 관리      | 중앙 통제형 다계정 구조         |
| AWS Systems Manager                | 하이브리드 환경 관리     | 패치, 파라미터 저장           |
| AWS Trusted Advisor                | 리소스 최적화 가이드     | 보안, 성능, 비용 권장         |
| AWS Well-Architected Tool          | 아키텍처 진단 도구      | 모범 사례 기반 점검           |

---

## 🎞️ 미디어 서비스

| 개념                               | 설명           | 키워드 및 예제 상황   |
| -------------------------------- | ------------ | ------------- |
| Amazon Elastic Transcoder    | 미디어 파일 포맷 변환 | 스트리밍 준비       |
| Amazon Kinesis Video Streams | 실시간 비디오 스트리밍 | IoT 카메라 영상 수집 |

---

## 🔄 Migration and Transfer

| 개념                                    | 설명                 | 키워드 및 예제 상황          |
| ------------------------------------- | ------------------ | -------------------- |
| AWS Application Discovery Service | 마이그레이션 전 애플리케이션 분석 | 종속성 분석               |
| AWS Application Migration Service | 서버 마이그레이션 자동화      | Lift & Shift 마이그레이션  |
| AWS Database Migration Service    | 데이터베이스 이전 지원       | 이기종 간 마이그레이션         |
| AWS DataSync                      | 온프레미스 ↔ AWS 데이터 전송 | S3, FSx 대상           |
| AWS Migration Hub                 | 마이그레이션 상태 대시보드     | 진행 현황 추적             |
| AWS Snow Family                   | 대용량 오프라인 데이터 전송    | Snowball, Snowmobile |
| AWS Transfer Family               | SFTP/FTPS 지원 파일 전송 | Amazon EFS, S3 대상    |

---

## 🌐 Networking and Content Delivery

| 개념                                | 설명                | 키워드 및 예제 상황    |
| --------------------------------- | ----------------- | -------------- |
| AWS Client VPN                | 클라이언트 기반 VPN      | 원격 근무 지원       |
| CloudFront | 콘텐츠 전송 네트워크(CDN)  | DDoS 완화, 캐싱    |
| AWS Direct Connect            | 온프레미스 ↔ AWS 전용 연결 | 고속, 안정적 연결     |
| AWS Global Accelerator        | 글로벌 트래픽 가속화       | 지연 시간 감소       |
| AWS PrivateLink               | VPC 내부 서비스 연결     | 프라이빗 네트워크 통신   |
| AWS Site-to-Site VPN          | 사이트 간 보안 연결       | 온프레미스 ↔ VPC 터널 |
| AWS Transit Gateway           | 다중 VPC 연결 허브      | 네트워크 통합        |

---

## 🔐 Security, Identity, and Compliance

| 개념                          | 설명              | 키워드 및 예제 상황      |
| --------------------------- | --------------- | ---------------- |
| AWS Artifact            | 규정 및 보고서 제공     | 감사 문서 다운로드       |
| AWS Audit Manager       | 감사 워크플로우 자동화    | 컴플라이언스 감사 준비     |
| AWS Certificate Manager | SSL 인증서 관리      | HTTPS 인증서 배포     |
| AWS CloudHSM            | 전용 하드웨어 키 저장    | FIPS 인증 키        |
| Amazon Cognito          | 사용자 인증 및 연동     | SSO, MFA         |
| Amazon Detective        | 보안 이벤트 조사       | 이상 행동 분석         |
| AWS Directory Service   | Microsoft AD 통합 | LDAP 호환          |
| AWS Firewall Manager    | 방화벽 정책 중앙 관리    | 조직 전체 규칙 적용      |
| Amazon GuardDuty        | 위협 탐지 서비스       | 이상 징후 탐지         |
| AWS IAM Identity Center | 중앙 집중식 SSO      | 액세스 제어           |
| Amazon Inspector        | 취약점 분석          | 자동화된 보안 검사       |
| Amazon Macie            | 민감 정보 식별        | PII 데이터 탐지       |
| AWS Network Firewall    | VPC 레벨 방화벽      | 트래픽 필터링          |
| AWS RAM                 | 리소스 공유 서비스      | 계정 간 공유 설정       |
| 00.Inbox/02.AWS/AWS Secrets Manager     | 암호 및 키 저장소      | 민감 정보 보호         |
| AWS Security Hub        | 보안 이벤트 통합       | 통합 보안 상태         |
| AWS Shield              | DDoS 공격 방어      | 기본/고급 보호         |
| AWS WAF                 | 웹 애플리케이션 방화벽    | SQL Injection 차단 |

---

## ⚙️ Serverless

| 개념              | 설명                  | 키워드 및 예제 상황 |
| --------------- | ------------------- | ----------- |
| AWS AppSync | GraphQL 기반 서버리스 API | 실시간 동기화     |
| AWS Fargate | 컨테이너 서버리스 실행        | 인프라 관리 불필요  |
| AWS Lambda  | 이벤트 기반 함수 실행        | 짧은 트리거성 작업  |

---

## 💾 Storage

| 개념                                  | 설명                           | 키워드 및 예제 상황    |
| ----------------------------------- | ---------------------------- | -------------- |
| AWS Backup                      | 백업 서비스                       | 데이터 복구 용이      |
| EBS | EC2용 블록 스토리지                 | 고성능 디스크        |
| EFS | EC2용 네트워크 파일 시스템             | 공유 파일 시스템      |
| Amazon FSx                      | Windows/NetApp/Lustre 파일 시스템 | 고성능 파일 스토리지    |
| AWS Storage Gateway             | 온프레미스 ↔ AWS 연결 스토리지          | 하이브리드 클라우드 저장소 |
