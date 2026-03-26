## 개요

머신러닝 프로젝트에서 데이터 전처리는 전체 작업 시간의 60~80%를 차지한다고 알려져 있습니다. 데이터 과학자들은 데이터 수집, 정제, 변환, 피처 엔지니어링에 막대한 시간을 투자하며, 이 과정은 반복적이고 오류가 발생하기 쉽습니다.

Amazon SageMaker Data Wrangler는 이러한 데이터 준비 과정을 대폭 간소화하는 시각적 데이터 전처리 도구입니다. 코드를 최소화하면서도 복잡한 데이터 변환을 수행할 수 있으며, 다양한 데이터 소스에서 데이터를 가져오고, 변환하고, ML 학습에 적합한 형태로 내보내는 전체 과정을 하나의 인터페이스에서 관리할 수 있습니다.

### Data Wrangler의 핵심 가치

1. **시간 절감**: SQL과 PySpark 코드를 수동으로 작성하는 것에 비해 데이터 준비 시간을 최대 80% 단축합니다.
2. **재현성**: 모든 데이터 변환 과정을 .flow 파일로 저장하여, 동일한 전처리 파이프라인을 반복 실행할 수 있습니다.
3. **확장성**: 소규모 데이터에서 프로토타이핑한 후, 동일한 변환을 PySpark 기반의 대규모 데이터셋에 적용할 수 있습니다.
4. **통합성**: SageMaker의 다른 서비스(Feature Store, Pipelines, Processing)와 원활하게 통합됩니다.

## 핵심 기능

### 1. 데이터 소스 연결

Data Wrangler는 40개 이상의 데이터 소스와 직접 연결할 수 있습니다.

**AWS 네이티브 소스**
- Amazon S3 (CSV, Parquet, JSON, ORC, Avro)
- Amazon Athena (SQL 쿼리)
- Amazon Redshift (데이터 웨어하우스)
- Amazon EMR (Hive 테이블)
- AWS Lake Formation (데이터 레이크)

**서드파티 소스**
- Snowflake
- Databricks
- Salesforce Data Cloud
- Google BigQuery
- SAP HANA
- Facebook Ads
- Google Analytics

각 데이터 소스에서 데이터를 가져올 때 SQL 쿼리를 사용하여 필요한 데이터만 선택적으로 로드할 수 있으며, 여러 소스의 데이터를 조인하여 하나의 데이터셋으로 결합할 수도 있습니다.

### 2. 내장 데이터 변환

Data Wrangler는 300개 이상의 내장 변환(Built-in Transforms)을 제공합니다.

**수치형 변환**
- 표준화(Standardization): Z-score, Min-Max 등
- 정규화(Normalization)
- 로그 변환
- 구간화(Binning): 등간격, 등빈도, 사용자 정의
- 결측값 대체: 평균, 중앙값, 최빈값, 사용자 정의 값

**범주형 변환**
- 원핫 인코딩(One-Hot Encoding)
- 레이블 인코딩(Label Encoding)
- 순서 인코딩(Ordinal Encoding)
- 타겟 인코딩(Target Encoding)
- 빈도 기반 인코딩

**텍스트 변환**
- 토큰화(Tokenization)
- 벡터화(TF-IDF, Count Vectorizer)
- 정규 표현식 추출/대체
- 대소문자 변환
- 불용어 제거

**날짜/시간 변환**
- 날짜 파싱 및 형식 변환
- 날짜 구성 요소 추출 (연, 월, 일, 요일, 시간 등)
- 시간 차이 계산
- 주기적 인코딩 (sin/cos 변환)

**피처 엔지니어링**
- 수학 연산 (열 간 사칙 연산)
- 집계 함수 (그룹별 평균, 합계, 카운트 등)
- 윈도우 함수 (이동 평균, 누적 합계 등)
- 피처 교차(Feature Cross)

### 3. 데이터 품질 분석

Data Wrangler는 데이터 품질을 자동으로 분석하는 다양한 기능을 제공합니다.

**자동 데이터 인사이트**
- 데이터 타입 자동 감지 및 추천
- 결측값 패턴 분석
- 중복 행 탐지
- 이상값 탐지 (IQR, Z-score 기반)
- 클래스 불균형 감지

**통계 분석**
- 기술 통계량 (평균, 중앙값, 표준편차, 분위수)
- 분포 시각화 (히스토그램, 박스플롯)
- 상관관계 분석 (피어슨, 스피어만)
- 타겟 변수와의 관계 분석

**타겟 누출(Target Leakage) 탐지**
- 타겟 변수와 비정상적으로 높은 상관관계를 가진 피처를 자동으로 탐지합니다.
- 이는 ML 모델에서 흔히 발생하는 실수 중 하나로, 학습 시에는 높은 성능을 보이지만 실전에서는 사용할 수 없는 피처를 포함하는 문제입니다.

### 4. 커스텀 변환

내장 변환으로 충족되지 않는 경우, 사용자 정의 변환을 작성할 수 있습니다.

**Python (Pandas) 커스텀 변환**
```python
import pandas as pd

# 복합 피처 생성 예시
df['income_to_loan_ratio'] = df['annual_income'] / df['loan_amount']
df['credit_utilization'] = df['current_balance'] / df['credit_limit']
df['employment_stability'] = df['years_employed'].apply(
    lambda x: 'stable' if x >= 5 else 'unstable'
)
```

**PySpark 커스텀 변환**
```python
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# 윈도우 함수를 활용한 피처 생성
window_spec = Window.partitionBy('customer_id').orderBy('transaction_date').rowsBetween(-30, 0)
df = df.withColumn('rolling_avg_amount', F.avg('amount').over(window_spec))
df = df.withColumn('transaction_count_30d', F.count('*').over(window_spec))
```

**SQL 커스텀 변환**
```sql
SELECT
    *,
    CASE
        WHEN age < 30 THEN 'young'
        WHEN age < 50 THEN 'middle'
        ELSE 'senior'
    END AS age_group,
    NTILE(10) OVER (ORDER BY income) AS income_decile
FROM dataset
```

### 5. 데이터 시각화

Data Wrangler는 다양한 시각화 기능을 제공합니다.

- 히스토그램 및 밀도 플롯
- 산점도 및 상관관계 행렬
- 박스플롯
- 바이올린 플롯
- 타겟 대비 피처 분포
- 시계열 플롯

## 아키텍처/동작 원리

### Data Wrangler Flow 파일 구조

Data Wrangler의 모든 작업은 .flow 파일(JSON 형식)에 저장됩니다. 이 파일은 데이터 소스, 변환 순서, 각 변환의 파라미터를 포함하는 DAG(Directed Acyclic Graph) 구조입니다.

```
[데이터 소스 노드]
  - S3, Redshift, Athena 등
       |
       v
[변환 노드 체인]
  - 변환 1: 결측값 처리
  - 변환 2: 인코딩
  - 변환 3: 피처 엔지니어링
  - ...
       |
       v
[분석 노드]
  - 데이터 품질 리포트
  - 편향 분석
       |
       v
[내보내기 노드]
  - S3, Feature Store, Pipeline 등
```

### 실행 환경

Data Wrangler는 두 가지 실행 모드를 지원합니다.

**인터랙티브 모드 (프로토타이핑)**
- SageMaker Studio 내에서 ml.m5.4xlarge 인스턴스 위에서 실행
- 데이터 샘플(기본 50,000행)을 사용하여 빠르게 변환을 테스트
- 즉각적인 시각적 피드백 제공

**처리 모드 (프로덕션)**
- SageMaker Processing Job으로 전환하여 전체 데이터셋에 변환 적용
- PySpark 기반으로 분산 처리 수행
- 다중 인스턴스를 활용한 수평 확장 가능

### 내보내기 옵션

Data Wrangler에서 처리된 데이터는 다양한 대상으로 내보낼 수 있습니다.

- **Amazon S3**: CSV, Parquet 형식으로 저장
- **SageMaker Feature Store**: 피처 그룹으로 직접 인제스트
- **SageMaker Pipelines**: 파이프라인 단계로 자동화
- **SageMaker Processing Job**: 대규모 배치 처리
- **Python 노트북**: 자동 생성된 코드를 노트북에서 실행

## 실전 활용

### 사용 사례 1: S3에서 데이터를 로드하여 변환

```bash
# 원본 데이터 확인
aws s3 ls s3://my-data-bucket/raw-data/ --recursive --human-readable

# 데이터 샘플 다운로드하여 확인
aws s3 cp s3://my-data-bucket/raw-data/transactions.csv - | head -5

# SageMaker Studio 도메인 및 Data Wrangler 실행 확인
aws sagemaker list-domains --query 'Domains[].{DomainId:DomainId,Status:Status}'

# Data Wrangler 앱 상태 확인
aws sagemaker list-apps \
  --domain-id-equals d-xxxxxxxxxxxx \
  --query 'Apps[?AppType==`KernelGateway`].{Name:AppName,Status:Status}'
```

### 사용 사례 2: Data Wrangler Flow를 Processing Job으로 실행

Data Wrangler에서 생성한 .flow 파일을 대규모 데이터에 적용하는 방법입니다.

```bash
# .flow 파일 S3 업로드
aws s3 cp my-preprocessing.flow \
  s3://my-data-bucket/wrangler-flows/my-preprocessing.flow

# Processing Job 생성
aws sagemaker create-processing-job \
  --processing-job-name wrangler-processing-$(date +%Y%m%d-%H%M%S) \
  --processing-resources '{
    "ClusterConfig": {
      "InstanceCount": 2,
      "InstanceType": "ml.m5.4xlarge",
      "VolumeSizeInGB": 100
    }
  }' \
  --app-specification '{
    "ImageUri": "174368400705.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-data-wrangler-container:1.x"
  }' \
  --processing-inputs '[
    {
      "InputName": "flow",
      "S3Input": {
        "S3Uri": "s3://my-data-bucket/wrangler-flows/my-preprocessing.flow",
        "LocalPath": "/opt/ml/processing/flow",
        "S3DataType": "S3Prefix",
        "S3InputMode": "File"
      }
    },
    {
      "InputName": "input-data",
      "S3Input": {
        "S3Uri": "s3://my-data-bucket/raw-data/",
        "LocalPath": "/opt/ml/processing/input",
        "S3DataType": "S3Prefix",
        "S3InputMode": "File"
      }
    }
  ]' \
  --processing-output-config '{
    "Outputs": [{
      "OutputName": "output",
      "S3Output": {
        "S3Uri": "s3://my-data-bucket/processed-data/",
        "LocalPath": "/opt/ml/processing/output",
        "S3UploadMode": "EndOfJob"
      }
    }]
  }' \
  --role-arn arn:aws:iam::123456789012:role/SageMakerRole

# 작업 진행 상태 모니터링
aws sagemaker describe-processing-job \
  --processing-job-name wrangler-processing-$(date +%Y%m%d-%H%M%S) \
  --query '{Status: ProcessingJobStatus, Duration: ProcessingEndTime}'
```

### 사용 사례 3: Python SDK를 활용한 프로그래매틱 변환

```python
import sagemaker
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.wrangler.processing import DataWranglerProcessor

session = sagemaker.Session()
role = sagemaker.get_execution_role()

# Data Wrangler Processor 생성
processor = DataWranglerProcessor(
    role=role,
    data_wrangler_flow_source="s3://my-data-bucket/wrangler-flows/my-preprocessing.flow",
    instance_count=2,
    instance_type="ml.m5.4xlarge",
    volume_size_in_gb=100,
    sagemaker_session=session,
)

# Processing Job 실행
processor.run(
    inputs=[
        ProcessingInput(
            source="s3://my-data-bucket/raw-data/",
            destination="/opt/ml/processing/input",
            input_name="input-data",
        )
    ],
    outputs=[
        ProcessingOutput(
            source="/opt/ml/processing/output",
            destination="s3://my-data-bucket/processed-data/",
            output_name="output",
        )
    ],
)
```

### 사용 사례 4: Feature Store로 직접 내보내기

```bash
# Feature Group 생성
aws sagemaker create-feature-group \
  --feature-group-name customer-features \
  --record-identifier-feature-name customer_id \
  --event-time-feature-name event_time \
  --feature-definitions '[
    {"FeatureName": "customer_id", "FeatureType": "String"},
    {"FeatureName": "event_time", "FeatureType": "String"},
    {"FeatureName": "income_to_loan_ratio", "FeatureType": "Fractional"},
    {"FeatureName": "credit_utilization", "FeatureType": "Fractional"},
    {"FeatureName": "employment_stability", "FeatureType": "String"},
    {"FeatureName": "rolling_avg_amount", "FeatureType": "Fractional"}
  ]' \
  --online-store-config '{"EnableOnlineStore": true}' \
  --offline-store-config '{
    "S3StorageConfig": {
      "S3Uri": "s3://my-data-bucket/feature-store/"
    }
  }' \
  --role-arn arn:aws:iam::123456789012:role/SageMakerRole

# Feature Group 상태 확인
aws sagemaker describe-feature-group \
  --feature-group-name customer-features \
  --query '{Status: FeatureGroupStatus, OnlineStore: OnlineStoreConfig}'
```

## 모범 사례/보안

### 데이터 전처리 모범 사례

1. **샘플링 기반 프로토타이핑**: 대규모 데이터셋에서 작업할 때는 먼저 샘플 데이터(기본 50,000행)로 변환을 설계하고 검증한 후, 전체 데이터셋에 적용합니다.

2. **변환 순서 최적화**: 필터링과 열 삭제를 먼저 수행하여 이후 변환의 데이터 볼륨을 줄입니다.

3. **Flow 파일 버전 관리**: .flow 파일을 Git으로 버전 관리하여 변환 이력을 추적합니다.

4. **데이터 품질 검사 자동화**: 변환 파이프라인에 데이터 품질 검증 단계를 포함하여, 입력 데이터가 예상 스키마와 일치하는지 확인합니다.

5. **피처 재사용**: Feature Store와 연동하여 한 번 생성한 피처를 여러 모델에서 재사용합니다.

### 비용 최적화

1. **인스턴스 타입 선택**: 데이터 크기에 맞는 적절한 인스턴스를 선택합니다. 작은 데이터셋에는 ml.m5.xlarge, 대규모 데이터에는 ml.m5.4xlarge 이상을 사용합니다.

2. **자동 종료 설정**: Data Wrangler 세션이 유휴 상태일 때 자동으로 종료되도록 Lifecycle Configuration을 설정합니다.

3. **스팟 인스턴스 활용**: Processing Job 실행 시 스팟 인스턴스를 사용하면 비용을 최대 90% 절감할 수 있습니다.

### 보안 모범 사례

1. **데이터 접근 제어**: Data Wrangler가 접근할 수 있는 데이터 소스를 IAM 정책으로 제한합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::approved-data-bucket",
        "arn:aws:s3:::approved-data-bucket/*"
      ]
    },
    {
      "Effect": "Deny",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::sensitive-data-bucket",
        "arn:aws:s3:::sensitive-data-bucket/*"
      ]
    }
  ]
}
```

2. **암호화**: 처리 중인 데이터와 출력 데이터 모두 KMS 암호화를 적용합니다.

3. **VPC 설정**: Data Wrangler를 VPC 내에서 실행하여 데이터가 외부 네트워크로 노출되지 않도록 합니다.

4. **감사 로깅**: CloudTrail을 통해 Data Wrangler의 모든 API 호출을 기록합니다.

## 관련 서비스 비교

### SageMaker Data Wrangler vs AWS Glue DataBrew

| 항목 | SageMaker Data Wrangler | AWS Glue DataBrew |
|------|------------------------|--------------------|
| 주요 대상 | ML 데이터 전처리 | 범용 데이터 정제 |
| 실행 환경 | SageMaker Studio | 독립형 서비스 |
| ML 특화 변환 | 풍부 (인코딩, 스케일링 등) | 기본적 |
| Feature Store 연동 | 네이티브 지원 | 미지원 |
| SageMaker 통합 | 깊은 통합 | 별도 설정 필요 |
| 가격 | 인스턴스 시간 기반 | 세션 + 노드 기반 |
| 데이터 소스 | 40+ | 80+ |

### SageMaker Data Wrangler vs Pandas

| 항목 | SageMaker Data Wrangler | Pandas |
|------|------------------------|--------|
| 인터페이스 | 시각적 + 코드 | 코드 전용 |
| 확장성 | PySpark 기반 분산 처리 | 단일 머신 메모리 제한 |
| 재현성 | .flow 파일 자동 저장 | 수동 코드 관리 |
| 학습 곡선 | 낮음 | 중간~높음 |
| 유연성 | 높음 (커스텀 코드 지원) | 매우 높음 |
| 비용 | 유료 | 무료 |

### SageMaker Data Wrangler vs Databricks Feature Engineering

| 항목 | SageMaker Data Wrangler | Databricks Feature Engineering |
|------|------------------------|--------------------------------|
| 시각적 인터페이스 | 있음 | 제한적 |
| 노트북 통합 | SageMaker Studio | Databricks Notebooks |
| Feature Store | SageMaker Feature Store | Unity Catalog |
| 분산 처리 | PySpark (Processing Job) | Spark (네이티브) |
| 데이터 레이크 | S3 + Lake Formation | Delta Lake |

## 요약

Amazon SageMaker Data Wrangler는 ML 데이터 전처리를 위한 강력하고 직관적인 도구입니다. 시각적 인터페이스를 통해 복잡한 데이터 변환을 쉽게 수행할 수 있으며, SageMaker 에코시스템과의 깊은 통합으로 엔드투엔드 ML 워크플로우를 효율적으로 구성할 수 있습니다.

핵심 특징을 정리하면 다음과 같습니다.

- **40개 이상의 데이터 소스**: S3, Redshift, Athena, Snowflake 등 다양한 소스에서 데이터 수집
- **300개 이상의 내장 변환**: 수치형, 범주형, 텍스트, 날짜/시간 등 포괄적인 변환 기능
- **커스텀 변환 지원**: Python, PySpark, SQL로 사용자 정의 변환 작성 가능
- **자동 데이터 품질 분석**: 결측값, 이상값, 타겟 누출 등을 자동으로 탐지
- **Feature Store 통합**: 생성한 피처를 Feature Store에 직접 저장하여 재사용
- **파이프라인 자동화**: SageMaker Pipelines에 데이터 전처리 단계로 통합
- **확장 가능한 처리**: PySpark 기반 분산 처리로 대규모 데이터셋 지원

Data Wrangler는 특히 데이터 전처리에 많은 시간을 투자하고 있는 팀, 시각적 인터페이스를 선호하는 데이터 분석가, SageMaker 기반 ML 워크플로우를 운영하는 조직에 적합합니다. 다만 고도로 복잡한 변환 로직이 필요하거나, SageMaker 외의 ML 플랫폼을 사용하는 경우에는 Pandas, PySpark, 또는 AWS Glue DataBrew를 검토하는 것이 바람직합니다.