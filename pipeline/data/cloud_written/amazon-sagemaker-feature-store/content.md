<!-- infographic-hero -->
![Amazon SageMaker Feature Store 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker Feature Store 한 장 요약 인포그래픽*

# Amazon SageMaker Feature Store

## 개요

Amazon SageMaker Feature Store는 머신러닝(ML) 파이프라인에서 사용되는 피처(Feature)를 중앙에서 저장하고 관리하며 공유할 수 있는 완전관리형 피처 저장소입니다. 머신러닝 프로젝트에서 가장 흔히 발생하는 문제 중 하나는 학습 시 사용한 피처와 추론 시 사용하는 피처 간의 불일치(Training-Serving Skew)입니다. 이러한 불일치는 모델 성능 저하의 주요 원인이 됩니다.

SageMaker Feature Store는 이 문제를 근본적으로 해결하기 위해 설계되었습니다. Online Store는 실시간 추론을 위한 저지연 피처 조회를 제공하고, Offline Store는 S3 기반으로 대규모 학습 데이터셋을 위한 피처 저장을 담당합니다. 두 저장소가 동일한 피처 정의(Feature Definition)를 공유하므로 학습과 추론 간의 데이터 일관성이 자연스럽게 보장됩니다.

여러 팀이 동일한 피처를 중복 생성하는 비효율을 방지하고, 피처의 재사용성을 극대화하여 ML 개발 생산성을 크게 향상시키는 것이 Feature Store의 핵심 가치입니다.

## 핵심 기능

### Feature Group

Feature Group은 관련된 피처들을 논리적으로 묶은 단위로, 관계형 데이터베이스의 테이블과 유사한 개념입니다. 각 Feature Group은 고유한 이름과 스키마(Feature Definition)를 가지며, Record Identifier와 Event Time이라는 두 가지 필수 필드를 포함해야 합니다.

- **Record Identifier**: 각 레코드를 고유하게 식별하는 키 (예: customer_id, product_id)
- **Event Time**: 피처가 생성되거나 업데이트된 시점을 나타내는 타임스탬프

### Online Store

실시간 추론을 위한 저지연 피처 저장소입니다. 밀리초 단위의 응답 시간을 제공하여 실시간 추천 시스템, 사기 탐지 등의 워크로드에 적합합니다. 최신 피처 값만 유지하며, GetRecord API를 통해 단일 레코드를 빠르게 조회할 수 있습니다.

### Offline Store

S3 기반의 대용량 피처 저장소로, 모델 학습과 배치 예측에 사용됩니다. Parquet 포맷으로 저장되어 Athena, Spark, SageMaker Processing Job 등으로 직접 쿼리할 수 있습니다. 모든 피처의 이력(History)이 보존되어 시점 기반 피처 조회(Point-in-Time Query)가 가능합니다.

### Feature Store 검색 및 탐색

SageMaker Studio에서 Feature Store를 시각적으로 탐색하고, 특정 피처를 검색할 수 있습니다. 피처의 메타데이터, 통계 정보, 사용 이력 등을 확인하여 재사용 가능한 피처를 쉽게 발견할 수 있습니다.

### 실시간 피처 수집

PutRecord API를 통해 실시간으로 피처를 Online Store와 Offline Store에 동시에 저장할 수 있습니다. 스트리밍 데이터 소스(Kinesis, Kafka 등)와 연동하여 실시간 피처 파이프라인을 구축할 수 있습니다.

## 아키텍처 / 동작 원리

### 전체 아키텍처

SageMaker Feature Store의 아키텍처는 크게 세 가지 계층으로 구성됩니다.

1. **수집 계층(Ingestion Layer)**: PutRecord API 또는 배치 수집을 통해 피처 데이터를 Feature Store에 저장합니다. 실시간 스트림(Kinesis Data Streams)이나 배치 처리(SageMaker Processing Job) 모두 지원합니다.

2. **저장 계층(Storage Layer)**: Online Store(DynamoDB 기반)와 Offline Store(S3 + Glue Catalog 기반)로 이원화되어 있습니다. PutRecord 호출 시 두 저장소에 동시 기록됩니다.

3. **소비 계층(Consumption Layer)**: GetRecord API로 실시간 피처를 조회하거나, Athena/Spark로 Offline Store를 쿼리하여 학습 데이터셋을 생성합니다.

### 데이터 흐름

```
데이터 소스 --> PutRecord API --> Online Store (저지연 조회)
                            +--> Offline Store (S3 Parquet)
                                    |
                                    +--> Athena 쿼리 --> 학습 데이터셋
                                    +--> Spark 처리 --> 배치 예측
```

### Point-in-Time 쿼리

Offline Store에서는 Event Time을 기준으로 특정 시점의 피처 상태를 조회할 수 있습니다. 이는 학습 데이터셋을 생성할 때 데이터 유출(Data Leakage)을 방지하는 데 핵심적인 기능입니다. 예를 들어, 2025년 1월 시점의 고객 피처만 사용하여 해당 월의 이탈 예측 모델을 학습할 수 있습니다.

## 실전 활용

### Feature Group 생성 (Python SDK)

```python
import sagemaker
from sagemaker.feature_store.feature_group import FeatureGroup
from sagemaker.feature_store.feature_definition import FeatureDefinition, FeatureTypeEnum
import pandas as pd
import time

session = sagemaker.Session()
role = sagemaker.get_execution_role()

# Feature Group 정의
feature_group = FeatureGroup(
    name="customer-features",
    sagemaker_session=session
)

# 피처 정의
feature_definitions = [
    FeatureDefinition(feature_name="customer_id", feature_type=FeatureTypeEnum.STRING),
    FeatureDefinition(feature_name="age", feature_type=FeatureTypeEnum.INTEGRAL),
    FeatureDefinition(feature_name="total_purchases", feature_type=FeatureTypeEnum.INTEGRAL),
    FeatureDefinition(feature_name="avg_order_value", feature_type=FeatureTypeEnum.FRACTIONAL),
    FeatureDefinition(feature_name="churn_probability", feature_type=FeatureTypeEnum.FRACTIONAL),
    FeatureDefinition(feature_name="event_time", feature_type=FeatureTypeEnum.FRACTIONAL),
]

# Feature Group 생성 (Online + Offline Store 활성화)
feature_group.load_feature_definitions(data_frame=customer_df)
feature_group.create(
    s3_uri=f"s3://{bucket}/feature-store/",
    record_identifier_name="customer_id",
    event_time_feature_name="event_time",
    role_arn=role,
    enable_online_store=True
)

# Feature Group 생성 완료 대기
feature_group.describe()
print("Feature Group 상태:", feature_group.describe()['FeatureGroupStatus'])
```

### 피처 데이터 수집 (Ingestion)

```python
import pandas as pd
import time

# 피처 데이터 준비
customer_data = pd.DataFrame({
    "customer_id": ["C001", "C002", "C003"],
    "age": [28, 35, 42],
    "total_purchases": [15, 42, 8],
    "avg_order_value": [55.30, 120.50, 35.20],
    "churn_probability": [0.12, 0.05, 0.67],
    "event_time": [time.time()] * 3
})

# 배치 수집
feature_group.ingest(data_frame=customer_data, max_workers=3, wait=True)
print("피처 수집 완료")
```

### Online Store에서 실시간 피처 조회

```python
import boto3

featurestore_client = boto3.client('sagemaker-featurestore-runtime')

# 단일 레코드 조회
response = featurestore_client.get_record(
    FeatureGroupName='customer-features',
    RecordIdentifierValueAsString='C001'
)

print("조회 결과:")
for feature in response['Record']:
    print(f"  {feature['FeatureName']}: {feature['ValueAsString']}")
```

### AWS CLI를 활용한 Feature Store 관리

```bash
# Feature Group 목록 조회
aws sagemaker list-feature-groups \
  --sort-by CreationTime \
  --sort-order Descending

# Feature Group 상세 정보 조회
aws sagemaker describe-feature-group \
  --feature-group-name "customer-features"

# Online Store에서 레코드 조회
aws sagemaker-featurestore-runtime get-record \
  --feature-group-name "customer-features" \
  --record-identifier-value-as-string "C001"

# Feature Group 삭제
aws sagemaker delete-feature-group \
  --feature-group-name "old-feature-group"

# Offline Store 데이터 Athena로 쿼리
aws athena start-query-execution \
  --query-string "SELECT * FROM customer_features WHERE age > 30" \
  --result-configuration OutputLocation=s3://my-bucket/athena-results/
```

### Offline Store에서 학습 데이터셋 생성 (Athena 쿼리)

```python
from sagemaker.feature_store.dataset_builder import DatasetBuilder

# Point-in-Time 쿼리를 통한 학습 데이터셋 생성
query = feature_group.athena_query()
query_string = f"""
SELECT customer_id, age, total_purchases, avg_order_value, churn_probability
FROM "{feature_group.name}"
WHERE event_time <= 1706745600
ORDER BY event_time DESC
"""

query.run(query_string=query_string, output_location=f"s3://{bucket}/query-results/")
query.wait()

# 결과를 DataFrame으로 변환
training_df = query.as_dataframe()
print(f"학습 데이터셋 크기: {training_df.shape}")
```

## 모범 사례 및 보안

### 설계 모범 사례

- **피처 그룹 설계**: 도메인별로 Feature Group을 분리합니다 (예: customer_features, product_features, transaction_features). 하나의 거대한 Feature Group보다는 논리적으로 관련된 피처끼리 그룹화하는 것이 관리와 재사용에 유리합니다.
- **Event Time 관리**: Event Time을 정확하게 설정하여 Point-in-Time 쿼리의 정확성을 보장합니다. UTC 기준의 Unix timestamp 사용을 권장합니다.
- **Online Store 활용 기준**: 실시간 추론이 필요한 피처만 Online Store를 활성화합니다. 학습 전용 피처는 Offline Store만으로 충분합니다.
- **버전 관리**: Feature Group 이름에 버전을 포함하거나(customer_features_v2), 태그로 버전을 관리합니다.

### 보안 설정

- **IAM 정책**: Feature Group별로 세분화된 접근 제어를 적용합니다. 민감한 피처가 포함된 Feature Group에는 특정 역할만 접근 가능하도록 설정합니다.
- **KMS 암호화**: Online Store와 Offline Store 모두 AWS KMS를 사용한 서버 측 암호화를 적용합니다.
- **VPC 엔드포인트**: Feature Store API 호출을 VPC 내부로 제한하여 데이터가 인터넷을 거치지 않도록 합니다.
- **CloudTrail 로깅**: Feature Store의 모든 API 호출을 CloudTrail로 기록하여 감사 추적을 확보합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateFeatureGroup",
        "sagemaker:DescribeFeatureGroup",
        "sagemaker:ListFeatureGroups"
      ],
      "Resource": "arn:aws:sagemaker:*:*:feature-group/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker-featurestore-runtime:GetRecord",
        "sagemaker-featurestore-runtime:PutRecord"
      ],
      "Resource": "arn:aws:sagemaker:*:*:feature-group/customer-features"
    }
  ]
}
```

## 관련 서비스 비교

| 항목 | SageMaker Feature Store | Feast (오픈소스) | Tecton | Databricks Feature Store |
|------|------------------------|-----------------|--------|-------------------------|
| **유형** | AWS 관리형 | 오픈소스 | SaaS | Databricks 통합 |
| **Online Store** | DynamoDB 기반 | Redis/DynamoDB 등 선택 | 자체 제공 | 자체 제공 |
| **Offline Store** | S3 (Parquet) | BigQuery/S3 등 선택 | S3/Snowflake 등 | Delta Lake |
| **Point-in-Time 쿼리** | 지원 | 지원 | 지원 | 지원 |
| **SageMaker 통합** | 완전 통합 | SDK 연동 필요 | 연동 가능 | 비통합 |
| **실시간 수집** | PutRecord API | Kafka 연동 | 스트리밍 지원 | Spark Streaming |
| **비용** | 사용량 기반 | 인프라 비용만 | 구독료 | Databricks 요금 |
| **멀티 클라우드** | AWS 전용 | 멀티 클라우드 | 멀티 클라우드 | Databricks 플랫폼 |

SageMaker Feature Store는 AWS 환경에 최적화되어 있으며, SageMaker의 학습, 추론, 파이프라인과 가장 자연스럽게 연동됩니다. 멀티 클라우드 환경이 필요한 경우에는 Feast나 Tecton이 더 유연한 선택이 될 수 있습니다.

## 요약

Amazon SageMaker Feature Store는 ML 파이프라인에서 피처의 일관성과 재사용성을 보장하는 핵심 인프라입니다. Online Store(실시간 추론용)와 Offline Store(학습/배치용)의 이원화된 구조를 통해 Training-Serving Skew 문제를 근본적으로 해결하며, Feature Group 기반의 체계적인 피처 관리를 가능하게 합니다.

특히 여러 팀이 동일한 피처를 공유해야 하는 대규모 ML 조직에서 Feature Store는 중복 작업을 방지하고 데이터 품질을 보장하는 데 큰 역할을 합니다. AWS 환경에서 MLOps 파이프라인을 구축하는 경우, SageMaker Feature Store를 피처 관리의 중심 저장소로 활용하면 학습과 추론 간의 데이터 일관성을 효과적으로 유지할 수 있습니다.