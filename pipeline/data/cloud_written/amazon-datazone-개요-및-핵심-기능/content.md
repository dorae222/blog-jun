<!-- infographic-hero -->
![Amazon DataZone 개요 및 핵심 기능 핵심 요약](figures/infographic.svg)

*Figure: Amazon DataZone 개요 및 핵심 기능 한 장 요약 인포그래픽*

# Amazon DataZone 개요 및 핵심 기능

## 개요

Amazon DataZone은 2023년 re:Invent에서 GA(Generally Available)로 발표된 데이터 관리 서비스입니다. 조직 내의 데이터를 안전하게 카탈로그화하고, 검색하고, 공유하고, 거버넌스할 수 있는 통합 플랫폼을 제공합니다.

현대 조직에서 데이터는 여러 팀, 여러 계정, 여러 서비스에 분산되어 있습니다. 데이터 생산자(Producer)는 자신이 만든 데이터를 안전하게 공유하고 싶고, 데이터 소비자(Consumer)는 필요한 데이터를 빠르게 찾아 활용하고 싶습니다. Amazon DataZone은 이러한 데이터 메시(Data Mesh) 패러다임을 AWS 네이티브로 구현한 서비스입니다.

### DataZone의 핵심 가치

- **데이터 민주화**: 기술적 지식이 없는 비즈니스 사용자도 데이터를 검색하고 활용할 수 있습니다.
- **거버넌스 내재화**: 데이터 접근 요청, 승인, 감사 프로세스가 서비스에 내장되어 있습니다.
- **셀프 서비스**: 데이터 소비자가 IT 부서의 도움 없이 직접 데이터를 찾고 사용할 수 있습니다.
- **크로스 계정**: 여러 AWS 계정에 분산된 데이터를 중앙에서 관리할 수 있습니다.

### DataZone vs 기존 접근 방식

DataZone 이전에는 데이터 공유를 위해 S3 버킷 정책, Lake Formation 권한, IAM 역할 등을 개별적으로 설정해야 했습니다. DataZone은 이러한 복잡한 인프라 설정을 추상화하여, 비즈니스 친화적인 "발행-구독(Publish-Subscribe)" 모델로 단순화합니다.

## 핵심 기능

### 도메인 (Domain)

DataZone의 최상위 조직 단위입니다. 일반적으로 하나의 비즈니스 단위나 부서에 매핑됩니다. 도메인은 데이터 거버넌스의 경계를 정의하며, 도메인 내의 모든 프로젝트, 자산, 환경을 관리합니다.

### 프로젝트 (Project)

도메인 내에서 데이터 작업을 수행하는 팀 또는 이니셔티브 단위입니다. 프로젝트는 멤버십을 가지며, 프로젝트 멤버만 해당 프로젝트의 데이터 자산에 접근할 수 있습니다.

### 환경 (Environment)

프로젝트에 연결된 AWS 리소스의 집합입니다. 예를 들어, Athena 쿼리 환경, Redshift 환경 등이 해당됩니다. 환경 프로필(Environment Profile)을 통해 표준화된 환경을 반복적으로 생성할 수 있습니다.

### 데이터 소스 (Data Source)

DataZone이 데이터를 발견하고 카탈로그화할 수 있는 원본 데이터 위치입니다. Glue Data Catalog, Redshift 등이 데이터 소스로 등록될 수 있습니다.

### 데이터 자산 (Data Asset)

카탈로그에 등록된 개별 데이터셋입니다. 테이블, 뷰, 파일 등이 데이터 자산이 될 수 있으며, 각 자산에는 비즈니스 메타데이터(설명, 태그, 용어집 용어)가 부착됩니다.

### 발행과 구독 (Publish and Subscribe)

데이터 공유의 핵심 메커니즘입니다.

- **발행(Publish)**: 데이터 생산자가 자신의 데이터 자산을 DataZone 마켓플레이스에 등록합니다.
- **구독(Subscribe)**: 데이터 소비자가 마켓플레이스에서 데이터를 검색하고, 접근을 요청합니다.
- **승인(Approve)**: 데이터 소유자 또는 관리자가 구독 요청을 승인하면, 자동으로 필요한 IAM/Lake Formation 권한이 설정됩니다.

### 비즈니스 용어집 (Glossary)

조직 전체에서 사용하는 비즈니스 용어를 정의하고 관리합니다. 용어집은 데이터 자산에 태깅되어, 비즈니스 사용자가 기술적 테이블 이름 대신 비즈니스 용어로 데이터를 검색할 수 있게 합니다.

### 데이터 포털 (Data Portal)

웹 기반 사용자 인터페이스로, 데이터 검색, 구독 요청, 데이터 탐색 등을 수행할 수 있습니다. SSO(Single Sign-On) 연동을 지원하여, 별도의 AWS 콘솔 접근 없이 사용할 수 있습니다.

## 아키텍처/동작 원리

### 전체 아키텍처

DataZone의 아키텍처는 다음과 같은 계층으로 구성됩니다.

```
[DataZone Domain]
  |
  +-- [Data Portal] -- SSO 연동 -- [비즈니스 사용자]
  |
  +-- [Catalog] -- 비즈니스 메타데이터, 용어집, 검색
  |
  +-- [Project A: 데이터 생산자]
  |     +-- Environment: Glue/S3
  |     +-- Data Source: Glue Data Catalog
  |     +-- Published Assets: customer_events, order_history
  |
  +-- [Project B: 데이터 소비자]
  |     +-- Environment: Athena
  |     +-- Subscribed Assets: customer_events
  |
  +-- [Governance]
        +-- Subscription Approval Workflow
        +-- Audit Trail
        +-- Access Policies
```

### 발행-구독 워크플로 상세

1. **데이터 소스 등록**: 데이터 생산자가 Glue Data Catalog 또는 Redshift를 데이터 소스로 등록합니다.
2. **메타데이터 수집**: DataZone이 데이터 소스에서 기술적 메타데이터(스키마, 파티션 등)를 자동으로 수집합니다.
3. **비즈니스 메타데이터 보강**: 데이터 소유자가 비즈니스 설명, 용어집 용어, 태그를 추가합니다.
4. **발행**: 데이터 자산을 마켓플레이스에 발행합니다.
5. **검색 및 구독 요청**: 데이터 소비자가 포털에서 데이터를 검색하고 구독을 요청합니다.
6. **승인**: 데이터 소유자가 구독 요청을 검토하고 승인합니다.
7. **자동 권한 부여**: DataZone이 Lake Formation 권한, IAM 역할 등을 자동으로 설정합니다.
8. **데이터 접근**: 소비자가 자신의 환경(Athena, Redshift 등)에서 데이터에 접근합니다.

### 크로스 계정 아키텍처

DataZone은 AWS Organizations와 연동하여 여러 AWS 계정에 걸친 데이터 거버넌스를 지원합니다.

```
[Management Account]
  +-- DataZone Domain

[Account A: Data Lake]
  +-- Project: Data Lake Team
  +-- Glue Data Catalog
  +-- S3 Data

[Account B: Analytics]
  +-- Project: Analytics Team
  +-- Athena Environment
  +-- Subscribed to Account A's data

[Account C: ML]
  +-- Project: ML Team
  +-- SageMaker Environment
  +-- Subscribed to Account A's data
```

## 실전 활용

### 도메인 및 프로젝트 생성 (AWS CLI)

```bash
# DataZone 도메인 생성
DOMAIN_ID=$(aws datazone create-domain \
  --name "analytics-domain" \
  --description "Analytics department data domain" \
  --domain-execution-role "arn:aws:iam::123456789012:role/DataZoneDomainRole" \
  --query 'id' --output text)

echo "Domain ID: $DOMAIN_ID"

# 프로젝트 생성 (데이터 생산자)
PRODUCER_PROJECT_ID=$(aws datazone create-project \
  --domain-identifier "$DOMAIN_ID" \
  --name "data-lake-team" \
  --description "Data Lake team - data producer" \
  --query 'id' --output text)

echo "Producer Project ID: $PRODUCER_PROJECT_ID"

# 프로젝트 생성 (데이터 소비자)
CONSUMER_PROJECT_ID=$(aws datazone create-project \
  --domain-identifier "$DOMAIN_ID" \
  --name "analytics-team" \
  --description "Analytics team - data consumer" \
  --query 'id' --output text)

echo "Consumer Project ID: $CONSUMER_PROJECT_ID"

# 프로젝트 멤버 추가
aws datazone create-project-membership \
  --domain-identifier "$DOMAIN_ID" \
  --project-identifier "$CONSUMER_PROJECT_ID" \
  --member '{"userIdentifier": "user@example.com"}' \
  --designation "PROJECT_CONTRIBUTOR"
```

### 데이터 소스 등록 및 자산 발행

```bash
# Glue Data Catalog 데이터 소스 등록
DATA_SOURCE_ID=$(aws datazone create-data-source \
  --domain-identifier "$DOMAIN_ID" \
  --project-identifier "$PRODUCER_PROJECT_ID" \
  --name "glue-analytics-catalog" \
  --type "GLUE" \
  --environment-identifier "env-123456" \
  --configuration '{
    "glueRunConfiguration": {
      "relationalFilterConfigurations": [
        {
          "databaseName": "analytics_db",
          "filterExpressions": [{
            "expression": "*",
            "type": "INCLUDE"
          }]
        }
      ]
    }
  }' \
  --enable-setting "ENABLED" \
  --schedule '{"schedule": "cron(0 12 * * ? *)", "timezone": "Asia/Seoul"}' \
  --query 'id' --output text)

echo "Data Source ID: $DATA_SOURCE_ID"

# 데이터 소스 실행 (메타데이터 수집)
aws datazone start-data-source-run \
  --domain-identifier "$DOMAIN_ID" \
  --data-source-identifier "$DATA_SOURCE_ID"

# 도메인 내 자산 목록 검색
aws datazone search \
  --domain-identifier "$DOMAIN_ID" \
  --search-scope "ASSET" \
  --search-text "customer events"
```

### 구독 워크플로

```bash
# 구독 요청 생성
SUBSCRIPTION_REQUEST_ID=$(aws datazone create-subscription-request \
  --domain-identifier "$DOMAIN_ID" \
  --request-reason "월간 고객 행동 분석 리포트 생성을 위해 customer_events 데이터 접근이 필요합니다." \
  --subscribed-principals '[{"project": {"identifier": "'"$CONSUMER_PROJECT_ID"'"}}]' \
  --subscribed-listings '[{"identifier": "listing-abc123"}]' \
  --query 'id' --output text)

echo "Subscription Request ID: $SUBSCRIPTION_REQUEST_ID"

# 구독 요청 승인 (데이터 소유자)
aws datazone accept-subscription-request \
  --domain-identifier "$DOMAIN_ID" \
  --identifier "$SUBSCRIPTION_REQUEST_ID" \
  --decision-comment "승인합니다. 읽기 전용 접근만 허용됩니다."

# 구독 목록 조회
aws datazone list-subscriptions \
  --domain-identifier "$DOMAIN_ID" \
  --subscribing-project-identifier "$CONSUMER_PROJECT_ID"
```

### 용어집 관리

```bash
# 용어집 생성
GLOSSARY_ID=$(aws datazone create-glossary \
  --domain-identifier "$DOMAIN_ID" \
  --owning-project-identifier "$PRODUCER_PROJECT_ID" \
  --name "비즈니스 용어집" \
  --description "조직 전체에서 사용하는 데이터 비즈니스 용어 정의" \
  --query 'id' --output text)

# 용어 추가
aws datazone create-glossary-term \
  --domain-identifier "$DOMAIN_ID" \
  --glossary-identifier "$GLOSSARY_ID" \
  --name "MAU" \
  --short-description "Monthly Active Users" \
  --long-description "월간 활성 사용자 수. 해당 월에 최소 1회 이상 로그인한 순수 사용자 수를 의미합니다. 중복 로그인은 1회로 계산합니다."

aws datazone create-glossary-term \
  --domain-identifier "$DOMAIN_ID" \
  --glossary-identifier "$GLOSSARY_ID" \
  --name "전환율" \
  --short-description "Conversion Rate" \
  --long-description "특정 행동을 완료한 사용자의 비율. 일반적으로 (구매 완료 수 / 페이지 방문 수) * 100으로 계산합니다."
```

### Python을 활용한 자동화

```python
import boto3
import json

def setup_datazone_governance(domain_name, teams_config):
    """DataZone 거버넌스 환경을 자동으로 설정하는 함수"""
    client = boto3.client('datazone')

    # 도메인 생성
    domain = client.create_domain(
        name=domain_name,
        description=f'{domain_name} data governance domain',
        domainExecutionRole='arn:aws:iam::123456789012:role/DataZoneDomainRole'
    )
    domain_id = domain['id']
    print(f"Domain created: {domain_id}")

    projects = {}
    for team in teams_config:
        # 프로젝트 생성
        project = client.create_project(
            domainIdentifier=domain_id,
            name=team['name'],
            description=team['description']
        )
        projects[team['name']] = project['id']
        print(f"Project created: {team['name']} ({project['id']})")

        # 멤버 추가
        for member in team.get('members', []):
            client.create_project_membership(
                domainIdentifier=domain_id,
                projectIdentifier=project['id'],
                member={'userIdentifier': member['email']},
                designation=member.get('role', 'PROJECT_CONTRIBUTOR')
            )
            print(f"  Member added: {member['email']}")

    return domain_id, projects

# 사용 예시
teams = [
    {
        'name': 'data-platform',
        'description': 'Data Platform team - data producers',
        'members': [
            {'email': 'platform-lead@example.com', 'role': 'PROJECT_OWNER'},
            {'email': 'engineer1@example.com', 'role': 'PROJECT_CONTRIBUTOR'}
        ]
    },
    {
        'name': 'analytics',
        'description': 'Analytics team - data consumers',
        'members': [
            {'email': 'analyst-lead@example.com', 'role': 'PROJECT_OWNER'},
            {'email': 'analyst1@example.com', 'role': 'PROJECT_CONTRIBUTOR'}
        ]
    }
]

domain_id, projects = setup_datazone_governance('my-org-analytics', teams)
```

## 모범 사례/보안

### 거버넌스 모범 사례

**1. 도메인 설계**: 비즈니스 단위 또는 데이터 도메인별로 DataZone 도메인을 생성합니다. 너무 세분화하면 관리가 복잡해지고, 너무 넓으면 거버넌스 효과가 떨어집니다.

**2. 데이터 분류 체계**: 데이터를 민감도에 따라 분류하고(공개, 내부, 기밀, 극비), 각 분류에 맞는 구독 승인 프로세스를 설정합니다.

**3. 용어집 표준화**: 조직 전체에서 사용하는 비즈니스 용어를 DataZone 용어집에 등록하고, 데이터 자산에 매핑합니다. 이를 통해 "같은 데이터를 다른 이름으로 부르는" 문제를 해결할 수 있습니다.

**4. 자동 메타데이터 수집**: 데이터 소스의 스케줄을 설정하여 메타데이터를 정기적으로 수집합니다. 수동 관리는 시간이 지남에 따라 메타데이터가 부정확해지는 문제를 야기합니다.

### 보안 모범 사례

**1. IAM 역할 최소 권한**: DataZone 도메인 실행 역할에는 필요한 최소한의 권한만 부여합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:GetTable",
        "glue:GetTables",
        "glue:GetPartitions"
      ],
      "Resource": [
        "arn:aws:glue:ap-northeast-2:123456789012:catalog",
        "arn:aws:glue:ap-northeast-2:123456789012:database/*",
        "arn:aws:glue:ap-northeast-2:123456789012:table/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lakeformation:GetDataAccess",
        "lakeformation:GrantPermissions",
        "lakeformation:RevokePermissions"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["ram:CreateResourceShare", "ram:AssociateResourceShare"],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ram:RequestedResourceType": "datazone:Domain"
        }
      }
    }
  ]
}
```

**2. SSO 연동**: DataZone 포털을 AWS IAM Identity Center(SSO)와 연동하여, 기업 ID로 로그인할 수 있도록 합니다.

**3. 구독 승인 프로세스**: 민감한 데이터에 대해서는 수동 승인 프로세스를 적용하고, 승인 이력을 감사합니다.

**4. 구독 만료 정책**: 데이터 구독에 만료 기간을 설정하여, 더 이상 필요하지 않은 접근 권한이 자동으로 회수되도록 합니다.

### 운영 모범 사례

- 데이터 품질 지표를 데이터 자산의 메타데이터에 포함시켜, 소비자가 데이터 신뢰도를 판단할 수 있게 합니다.
- 데이터 소유자를 명확히 지정하고, 소유자 변경 시 프로세스를 수립합니다.
- 정기적으로 구독 현황을 검토하여, 미사용 구독을 정리합니다.

## 관련 서비스 비교

### DataZone vs Lake Formation

| 항목 | Amazon DataZone | AWS Lake Formation |
|------|----------------|--------------------|
| 초점 | 데이터 거버넌스 및 공유 | 데이터 레이크 보안 |
| 사용자 | 비즈니스 사용자 포함 | 데이터 엔지니어/관리자 |
| 인터페이스 | 웹 포털 (비기술적) | AWS 콘솔 (기술적) |
| 데이터 공유 | 발행-구독 모델 | 직접 권한 부여 |
| 검색 기능 | 비즈니스 메타데이터 기반 | 기술적 메타데이터 |
| 관계 | Lake Formation 위에서 동작 | DataZone의 기반 기술 |

DataZone은 Lake Formation을 내부적으로 사용하여 실제 접근 제어를 수행합니다. Lake Formation이 "엔진"이라면, DataZone은 "대시보드"에 해당합니다.

### DataZone vs AWS Glue Data Catalog

Glue Data Catalog은 기술적 메타데이터(스키마, 파티션)를 관리하는 반면, DataZone은 비즈니스 메타데이터(설명, 용어집, 데이터 품질)까지 포함한 포괄적 카탈로그를 제공합니다. DataZone은 Glue Data Catalog을 데이터 소스로 사용합니다.

### DataZone vs 오픈소스 대안 (Apache Atlas, DataHub)

| 항목 | Amazon DataZone | Apache Atlas / DataHub |
|------|----------------|----------------------|
| 운영 방식 | 완전 관리형 | 자체 운영 필요 |
| AWS 통합 | 네이티브 | 커스텀 구현 필요 |
| 접근 제어 | 자동 (Lake Formation) | 별도 구현 필요 |
| 비용 | 사용량 기반 과금 | 인프라 비용만 |
| 유연성 | AWS 생태계 한정 | 멀티 클라우드 가능 |

## 요약

Amazon DataZone은 조직의 데이터 거버넌스와 공유를 현대화하는 서비스입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **데이터 메시 구현**: 발행-구독 모델을 통해 데이터 생산자와 소비자 간의 데이터 공유를 체계화합니다.
- **비즈니스 친화적**: 웹 포털, 비즈니스 용어집, 자연어 검색을 통해 비기술적 사용자도 데이터를 활용할 수 있습니다.
- **자동 거버넌스**: 구독 승인 시 Lake Formation 권한이 자동으로 설정되어, 수작업 없이 안전한 데이터 접근이 가능합니다.
- **크로스 계정**: AWS Organizations와 연동하여 멀티 계정 환경에서의 데이터 거버넌스를 지원합니다.
- **Lake Formation 기반**: 내부적으로 Lake Formation을 활용하여 컬럼 수준의 세밀한 접근 제어를 제공합니다.
- **핵심 구성요소**: 도메인, 프로젝트, 환경, 데이터 소스, 데이터 자산, 용어집이 DataZone의 핵심 빌딩 블록입니다.

DataZone은 데이터가 자산으로서의 가치를 발휘할 수 있도록, 데이터의 발견, 이해, 접근, 활용의 전 과정을 체계화하는 서비스입니다.