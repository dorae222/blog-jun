---
title: Amazon OpenSearch Service 개요
slug: "amazon-opensearch-service-개요"
category: cloud
tags: ["amazon-opensearch-service", "aws", "cloud", "elasticsearch", "log-analysis", "monitoring", "opensearch", "security", "ultrawarm"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.444550+00:00"
---

Amazon OpenSearch Service는 AWS 클라우드에서 OpenSearch 클러스터를 손쉽게 배포, 운영 및 확장할 수 있게 해주는 관리형 서비스입니다. OpenSearch Service의 도메인(domain)은 OpenSearch 클러스터와 동의어로, 특정 설정, 인스턴스 유형과 수, 스토리지 리소스를 갖춘 클러스터를 의미합니다. Amazon OpenSearch Service는 OpenSearch와 레거시 Elasticsearch OSS(공식적으로 공개된 마지막 OSS 버전인 7.10까지)를 지원하며, 도메인을 생성할 때 사용할 검색 엔진을 선택할 수 있습니다.

**_OpenSearch_**는 로그 분석, 실시간 애플리케이션 모니터링, 클릭 스트림 분석 등 다양한 사용 사례를 위한 완전한 오픈 소스 검색 및 분석 엔진입니다. 자세한 내용은 [OpenSearch 설명서](https://opensearch.org/docs/)를 참조하세요.

Amazon OpenSearch Service는 OpenSearch 클러스터에 필요한 모든 리소스를 프로비저닝하고 시작합니다. 실패한 OpenSearch 노드를 자동으로 감지해 교체하므로 자체 관리형 인프라에서 발생하는 운영 오버헤드를 줄여줍니다. API 호출 한 번 또는 콘솔 클릭 몇 번으로 클러스터를 조정할 수 있습니다.

![](/media/posts/imported/aws/Pasted%20image%2020250610023633.png)

## Amazon OpenSearch Service의 기능

OpenSearch Service에는 다음과 같은 기능이 포함되어 있습니다.

**크기 조정**

- 비용 효율적인 Graviton 인스턴스를 포함한 다양한 CPU, 메모리 및 스토리지 구성(인스턴스 유형)
- 최대 1002개의 데이터 노드 지원
- 연결된 스토리지의 최대 25PB 지원
- 읽기 전용 데이터를 위한 비용 효율적인 [UltraWarm](https://docs.aws.amazon.com/ko_kr/opensearch-service/latest/developerguide/ultrawarm.html) 및 [콜드 스토리지](https://docs.aws.amazon.com/ko_kr/opensearch-service/latest/developerguide/cold-storage.html)

**보안**

- AWS Identity and Access Management(IAM) 기반 액세스 제어
- Amazon VPC 및 VPC 보안 그룹과의 손쉬운 통합
- 저장 데이터 암호화 및 노드 간 암호화
- OpenSearch 대시보드에 대한 Amazon Cognito, HTTP 기본 인증 또는 SAML 인증 지원
- 인덱스 수준, 문서 수준 및 필드 수준 보안
- 감사 로그
- Dashboards 멀티테넌시

**안정성**

- 리소스를 여러 지리적 위치(리전 및 가용 영역)에 배포 가능
- 동일 리전의 두 개 또는 세 개 가용 영역에 노드 할당(다중 AZ)
- 클러스터 관리 작업 부담을 줄여주는 전용 프라이머리 노드
- 자동 스냅샷을 통한 도메인 백업 및 복원

**유연성**

- 비즈니스 인텔리전스(BI) 애플리케이션 통합을 위한 SQL 지원
- 검색 결과 개선을 위한 사용자 지정 패키지 지원

**유명 서비스와의 통합**

- OpenSearch 대시보드를 사용한 데이터 시각화
- OpenSearch Service 도메인의 지표 및 설정 알림 모니터링을 위한 Amazon CloudWatch 통합
- 도메인 구성 API 호출 감사를 위한 AWS CloudTrail 통합
- 스트리밍 데이터를 OpenSearch Service로 로드하기 위한 Amazon S3, Amazon Kinesis 및 Amazon DynamoDB 통합
- 특정 임계값 초과 시 알림을 위한 Amazon SNS 통합

## OpenSearch를 직접 운영할 때와 Amazon OpenSearch Service를 사용할 때
### OpenSearch

> **NOTE:**
> - 조직이 자체 프로비저닝한 클러스터를 수동으로 모니터링하고 유지 관리할 의지와 적절한 기술 역량을 보유하고 있는 경우
> - 코드 수준에서 완전한 제어(컴파일 포함)를 유지하려는 경우
> - 오픈 소스 소프트웨어를 선호하거나 내부적으로 맞춤화하여 사용하려는 경우
> - 다중 클라우드 전략으로 벤더 종속적이지 않은 기술이 필요한 경우
> - 팀이 프로덕션 이슈를 직접 해결할 수 있는 역량을 갖춘 경우
> - 제품을 자유롭게 사용·수정·확장하길 원하거나 새 기능을 즉시 사용하고 싶은 경우

### Amazon OpenSearch Service

> **NOTE:**
> - 인프라를 직접 관리·모니터링·유지 관리하고 싶지 않은 경우
> - Amazon S3의 내구성과 저비용을 활용해 여러 스토리지 계층으로 데이터를 계층화하여 증가하는 분석 비용을 관리하려는 경우
> - DynamoDB, Amazon DocumentDB(MongoDB 호환), IAM, CloudWatch, CloudFormation 등 다른 AWS 서비스와의 통합을 활용하려는 경우
> - 예방적 유지 관리 및 프로덕션 문제 발생 시 지원에 쉽게 접근할 수 있어야 하는 경우
> - 자체 복구, 선제적 유지 관리, 복원력 및 백업 같은 관리형 기능을 활용하려는 경우

https://docs.aws.amazon.com/ko_kr/opensearch-service/latest/developerguide/what-is.html