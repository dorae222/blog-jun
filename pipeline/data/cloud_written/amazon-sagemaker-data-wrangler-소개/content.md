<!-- infographic-hero -->
![Amazon SageMaker Data Wrangler 소개 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker Data Wrangler 소개 한 장 요약 인포그래픽*

## 개요

Amazon SageMaker Data Wrangler는 머신러닝 데이터 준비를 위한 시각적 도구로, AWS SageMaker Studio 내에서 사용할 수 있습니다. 이 글에서는 Data Wrangler를 처음 접하는 사용자를 위해, 기본 개념부터 실전 워크플로우까지를 단계별로 안내합니다.

### 데이터 준비가 중요한 이유

ML 모델의 성능은 학습 데이터의 품질에 직접적으로 의존합니다. 아무리 정교한 알고리즘을 사용하더라도 입력 데이터가 불량하면 좋은 결과를 기대할 수 없습니다. 이를 "Garbage In, Garbage Out(GIGO)"이라고 합니다.

데이터 준비 과정에서 흔히 직면하는 과제는 다음과 같습니다.

1. **데이터 분산**: 필요한 데이터가 여러 시스템(DB, 데이터 레이크, API 등)에 분산되어 있습니다.
2. **데이터 품질 문제**: 결측값, 이상값, 중복, 불일치 등 다양한 품질 이슈가 존재합니다.
3. **피처 엔지니어링**: 원시 데이터를 ML 모델이 학습할 수 있는 형태의 피처로 변환해야 합니다.
4. **스케일링 문제**: 프로토타이핑에서 사용한 전처리 로직을 대규모 데이터에 적용하기 어렵습니다.
5. **재현성**: 동일한 전처리를 반복 수행할 수 있어야 합니다.

SageMaker Data Wrangler는 이 모든 과제를 하나의 통합 인터페이스에서 해결합니다.

### Data Wrangler의 위치

SageMaker Data Wrangler는 ML 라이프사이클에서 "데이터 준비" 단계를 담당합니다.

```
[문제 정의] --> [데이터 수집] --> [데이터 준비 (Data Wrangler)] --> [모델 학습] --> [모델 평가] --> [모델 배포]
```

## 핵심 기능

### 1. Data Wrangler 시작하기

Data Wrangler를 시작하려면 SageMaker Studio에 접속한 후 새 Data Wrangler 흐름(Flow)을 생성합니다. Flow는 데이터 소스에서 최종 출력까지의 전체 데이터 변환 과정을 나타내는 시각적 워크플로우입니다.

AWS CLI를 사용하여 SageMaker Studio 환경을 확인하는 방법입니다.

```bash
# SageMaker 도메인 확인
aws sagemaker list-domains \
  --query 'Domains[].{DomainId:DomainId, DomainName:DomainName, Status:Status}' \
  --output table

# 사용자 프로필 확인
aws sagemaker list-user-profiles \
  --domain-id-equals d-xxxxxxxxxxxx \
  --query 'UserProfiles[].{UserProfileName:UserProfileName, Status:Status}' \
  --output table

# SageMaker Studio Presigned URL 생성 (브라우저에서 열기)
aws sagemaker create-presigned-domain-url \
  --domain-id d-xxxxxxxxxxxx \
  --user-profile-name default-user \
  --query 'AuthorizedUrl' \
  --output text
```

### 2. 데이터 가져오기

Data Wrangler에서 데이터를 가져오는 가장 일반적인 방법은 Amazon S3에서 직접 로드하는 것입니다.

```bash
# S3 버킷에 학습 데이터 업로드
aws s3 cp ./raw_data/customers.csv \
  s3://my-wrangler-bucket/input/customers.csv

aws s3 cp ./raw_data/transactions.csv \
  s3://my-wrangler-bucket/input/transactions.csv

aws s3 cp ./raw_data/products.csv \
  s3://my-wrangler-bucket/input/products.csv

# 업로드 확인
aws s3 ls s3://my-wrangler-bucket/input/ --human-readable --summarize
```

Data Wrangler UI에서 "Import" 탭을 클릭하면 S3 버킷을 탐색하고 파일을 선택할 수 있습니다. CSV, Parquet, JSON 형식을 지원하며, 미리보기를 통해 데이터 구조를 확인할 수 있습니다.

**Amazon Athena를 통한 데이터 가져오기**

SQL 쿼리를 사용하여 S3 데이터 레이크에서 필요한 데이터만 선택적으로 가져올 수도 있습니다.

```bash
# Athena 쿼리 실행으로 데이터 확인
aws athena start-query-execution \
  --query-string "SELECT * FROM customer_db.transactions WHERE year = 2024 LIMIT 100" \
  --result-configuration '{"OutputLocation": "s3://my-wrangler-bucket/athena-results/"}' \
  --work-group primary

# 쿼리 상태 확인
aws athena get-query-execution \
  --query-execution-id <query-execution-id> \
  --query 'QueryExecution.Status.State'
```

### 3. 데이터 탐색 및 품질 확인

Data Wrangler는 데이터를 가져온 직후 자동으로 기본적인 데이터 프로파일링을 수행합니다.

**자동 생성되는 정보**
- 각 열의 데이터 타입 (숫자형, 문자형, 날짜형 등)
- 결측값 비율
- 고유값 개수
- 기본 통계량 (평균, 중앙값, 최소/최대)
- 분포 히스토그램

**Data Quality Report 생성**

Data Wrangler의 "Analysis" 탭에서 "Data Quality and Insights Report"를 생성하면 다음과 같은 상세 분석을 얻을 수 있습니다.

- 각 열의 상세 통계 (분위수, 왜도, 첨도)
- 결측값 패턴 분석 (MCAR, MAR, MNAR 여부 추정)
- 이상값 탐지 (IQR 방법, Z-score 방법)
- 열 간 상관관계 매트릭스
- 중복 행 비율
- 타겟 누출(Target Leakage) 경고

### 4. 데이터 변환 적용

Data Wrangler의 핵심은 시각적으로 데이터 변환을 적용하는 것입니다. "Transform" 탭에서 "Add step"을 클릭하면 300개 이상의 내장 변환 중에서 선택할 수 있습니다.

**가장 자주 사용하는 변환 유형별 예시**

**결측값 처리**
- 수치형 열: 평균, 중앙값, 또는 특정 값으로 대체
- 범주형 열: 최빈값 또는 "Unknown"으로 대체
- 결측값이 많은 열: 삭제

**인코딩**
- 범주형 변수를 원핫 인코딩으로 변환
- 순서가 있는 범주형 변수를 순서 인코딩으로 변환
- 높은 카디널리티 범주형 변수를 타겟 인코딩으로 변환

**스케일링**
- Min-Max 스케일링: 값을 0~1 범위로 변환
- Standard 스케일링: 평균 0, 표준편차 1로 변환
- Robust 스케일링: 이상값에 덜 민감한 스케일링

**피처 생성**
- 날짜에서 요일, 월, 분기 등 추출
- 수치형 열 간 비율 계산
- 텍스트 길이, 단어 수 등 추출

각 변환을 추가하면 Data Wrangler는 즉시 샘플 데이터에 변환을 적용하여 결과를 미리보기로 보여줍니다. 이를 통해 변환이 의도대로 작동하는지 바로 확인할 수 있습니다.

### 5. 커스텀 변환

내장 변환으로 충분하지 않은 경우, Python(Pandas), PySpark, SQL을 사용하여 사용자 정의 변환을 작성할 수 있습니다.

```python
# Pandas 커스텀 변환 예시
import pandas as pd

# 복합 피처 생성
df['purchase_frequency'] = df.groupby('customer_id')['order_id'].transform('count')
df['avg_order_value'] = df.groupby('customer_id')['order_amount'].transform('mean')
df['days_since_last_purchase'] = (pd.Timestamp.now() - pd.to_datetime(df['last_purchase_date'])).dt.days

# 조건부 피처 생성
df['customer_segment'] = pd.cut(
    df['total_spending'],
    bins=[0, 100, 500, 1000, float('inf')],
    labels=['bronze', 'silver', 'gold', 'platinum']
)
```

### 6. 데이터 내보내기

변환이 완료되면 처리된 데이터를 다양한 대상으로 내보낼 수 있습니다.

**S3로 내보내기**

가장 기본적인 방법으로, CSV 또는 Parquet 형식으로 S3에 저장합니다.

```bash
# Data Wrangler에서 내보낸 데이터 확인
aws s3 ls s3://my-wrangler-bucket/output/ --recursive --human-readable

# 처리된 데이터 다운로드
aws s3 cp s3://my-wrangler-bucket/output/processed_data.csv ./processed_data.csv

# 행 수 확인
aws s3 cp s3://my-wrangler-bucket/output/processed_data.csv - | wc -l
```

**SageMaker Feature Store로 내보내기**

생성된 피처를 Feature Store에 저장하면 다른 모델에서도 재사용할 수 있습니다.

**SageMaker Pipelines로 내보내기**

Data Wrangler Flow를 SageMaker Pipeline의 한 단계로 포함시켜 자동화할 수 있습니다.

**Python 노트북으로 내보내기**

Data Wrangler에서 수행한 모든 변환을 Python 코드로 자동 생성하여 노트북에서 실행할 수 있습니다.

## 아키텍처/동작 원리

### Flow 파일의 구조

Data Wrangler의 모든 작업은 .flow 파일에 JSON 형식으로 저장됩니다. 이 파일은 다음과 같은 구조를 가집니다.

```json
{
  "metadata": {
    "version": 1,
    "disable_limits": false
  },
  "nodes": [
    {
      "node_id": "source-node-1",
      "type": "SOURCE",
      "parameters": {
        "dataset_definition": {
          "datasetSourceType": "S3",
          "name": "customers.csv",
          "s3ExecutionContext": {
            "s3Uri": "s3://my-wrangler-bucket/input/customers.csv",
            "s3ContentType": "csv"
          }
        }
      },
      "outputs": [{"name": "default"}]
    },
    {
      "node_id": "transform-node-1",
      "type": "TRANSFORM",
      "parameters": {
        "transform_type": "HandleMissing",
        "columns": ["income"],
        "strategy": "fill_with_median"
      },
      "inputs": [{"name": "default", "node_id": "source-node-1"}],
      "outputs": [{"name": "default"}]
    }
  ]
}
```

### 실행 엔진

Data Wrangler는 두 가지 실행 모드를 가집니다.

**인터랙티브 모드**
- SageMaker Studio 내의 KernelGateway 앱에서 실행
- 기본적으로 데이터의 처음 50,000행을 샘플링하여 변환을 적용
- 실시간으로 변환 결과를 미리보기
- ml.m5.4xlarge 인스턴스에서 실행

**배치 모드 (Processing Job)**
- SageMaker Processing Job으로 전환하여 전체 데이터셋에 적용
- PySpark 기반으로 분산 처리
- 다중 인스턴스를 사용한 수평 확장 지원
- 대규모 데이터셋(수 TB)에도 적용 가능

### SageMaker 에코시스템과의 통합

```
[Data Wrangler]
    |
    +---> [SageMaker Feature Store] : 피처 저장 및 재사용
    |
    +---> [SageMaker Pipelines] : 자동화된 ML 파이프라인
    |
    +---> [SageMaker Autopilot] : AutoML 학습
    |
    +---> [SageMaker Training] : 커스텀 모델 학습
    |
    +---> [SageMaker Clarify] : 편향 분석
```

## 실전 활용

### 실습: 고객 이탈 예측을 위한 데이터 준비

전자상거래 고객 데이터를 사용하여 이탈 예측 모델을 위한 데이터를 준비하는 전체 워크플로우입니다.

**1단계: 데이터 업로드**

```bash
# 실습용 데이터 생성 및 업로드
aws s3 mb s3://wrangler-tutorial-bucket --region ap-northeast-2

# 고객 정보 데이터 업로드
aws s3 cp customer_info.csv s3://wrangler-tutorial-bucket/input/customer_info.csv

# 거래 이력 데이터 업로드
aws s3 cp transaction_history.csv s3://wrangler-tutorial-bucket/input/transaction_history.csv

# 고객 서비스 로그 업로드
aws s3 cp support_tickets.csv s3://wrangler-tutorial-bucket/input/support_tickets.csv

# 업로드 확인
aws s3 ls s3://wrangler-tutorial-bucket/input/ --human-readable
```

**2단계: Data Wrangler Flow 생성**

SageMaker Studio에서 새 Data Wrangler Flow를 생성하고, 세 개의 데이터 소스를 임포트합니다.

**3단계: 데이터 조인**

customer_id를 키로 세 데이터셋을 조인합니다.
- customer_info LEFT JOIN transaction_history ON customer_id
- 결과 LEFT JOIN support_tickets ON customer_id

**4단계: 변환 적용**

1. 결측값 처리: income 열의 결측값을 중앙값으로 대체
2. 날짜 파싱: registration_date에서 가입 경과일 계산
3. 집계: customer_id별 총 거래 금액, 평균 거래 금액, 거래 횟수 계산
4. 인코딩: 지역(region) 열을 원핫 인코딩
5. 스케일링: 수치형 피처를 Standard Scaling

**5단계: 데이터 품질 검증 및 내보내기**

```bash
# 처리된 데이터 확인
aws s3 ls s3://wrangler-tutorial-bucket/output/ --human-readable

# 데이터 크기 및 형식 확인
aws s3api head-object \
  --bucket wrangler-tutorial-bucket \
  --key output/processed_churn_data.csv

# 처리된 데이터로 SageMaker 학습 작업 시작 준비
aws s3 cp s3://wrangler-tutorial-bucket/output/processed_churn_data.csv \
  s3://wrangler-tutorial-bucket/training/train.csv
```

### 실습: Redshift에서 데이터 가져오기

```bash
# Redshift 클러스터 상태 확인
aws redshift describe-clusters \
  --cluster-identifier my-analytics-cluster \
  --query 'Clusters[0].{Status:ClusterStatus, Endpoint:Endpoint.Address}'

# Redshift에서 Data Wrangler로 데이터를 가져오려면
# SageMaker Studio에서 Redshift 연결을 설정해야 합니다.
# 아래 명령으로 Redshift에 대한 IAM 역할 연결을 확인합니다.
aws redshift describe-clusters \
  --cluster-identifier my-analytics-cluster \
  --query 'Clusters[0].IamRoles[].IamRoleArn'
```

## 모범 사례/보안

### 입문자를 위한 모범 사례

1. **작은 데이터셋으로 시작**: 처음에는 수천~수만 행의 작은 데이터셋으로 Data Wrangler의 기능을 익힌 후, 점차 대규모 데이터로 확장합니다.

2. **변환 단계를 작게 유지**: 하나의 변환 단계에서 너무 많은 작업을 수행하지 말고, 각 단계를 작고 명확하게 유지합니다. 이렇게 하면 문제가 발생했을 때 어느 단계에서 문제가 생겼는지 쉽게 파악할 수 있습니다.

3. **미리보기를 적극 활용**: 각 변환을 추가할 때마다 미리보기를 확인하여 의도대로 작동하는지 검증합니다.

4. **Flow 파일 백업**: .flow 파일을 정기적으로 S3에 백업하거나 Git으로 버전 관리합니다.

5. **내보내기 전 데이터 품질 검사**: 최종 데이터를 내보내기 전에 반드시 Data Quality Report를 생성하여 이상이 없는지 확인합니다.

### 보안 설정

1. **SageMaker 도메인 보안 설정**

```bash
# VPC 내에서 SageMaker 도메인 생성
aws sagemaker create-domain \
  --domain-name secure-ml-domain \
  --auth-mode IAM \
  --default-user-settings '{
    "ExecutionRole": "arn:aws:iam::123456789012:role/SageMakerRole",
    "SecurityGroups": ["sg-0123456789abcdef0"]
  }' \
  --subnet-ids subnet-0123456789abcdef0 subnet-0123456789abcdef1 \
  --vpc-id vpc-0123456789abcdef0 \
  --app-network-access-type VpcOnly
```

2. **데이터 암호화**: 모든 데이터는 전송 중(TLS 1.2)과 저장 시(AWS KMS)에 암호화됩니다.

3. **네트워크 격리**: VpcOnly 모드로 SageMaker 도메인을 설정하면 모든 트래픽이 VPC 내에서만 이동합니다.

4. **접근 제어**: IAM 정책을 통해 Data Wrangler 사용자가 접근할 수 있는 데이터 소스를 제한합니다.

## 관련 서비스 비교

### Data Wrangler vs 수동 코딩

| 항목 | Data Wrangler | 수동 Python 코딩 |
|------|--------------|-------------------|
| 속도 | 빠름 (드래그 앤 드롭) | 느림 (코드 작성 필요) |
| 재현성 | .flow 파일 자동 저장 | 수동 관리 필요 |
| 확장성 | 자동 분산 처리 | 수동 최적화 필요 |
| 시각화 | 내장 시각화 | 별도 라이브러리 필요 |
| 유연성 | 높음 (커스텀 코드 지원) | 최상 |
| 비용 | 인스턴스 비용 발생 | 로컬에서 무료 |
| 학습 곡선 | 낮음 | 중간~높음 |

### Data Wrangler vs AWS Glue DataBrew

| 항목 | Data Wrangler | Glue DataBrew |
|------|--------------|---------------|
| 대상 | ML 데이터 전처리 | 범용 데이터 정제 |
| ML 특화 기능 | 풍부 | 제한적 |
| SageMaker 통합 | 네이티브 | 별도 설정 |
| Feature Store | 직접 연동 | 미지원 |
| 독립 서비스 여부 | Studio 내 기능 | 독립 서비스 |

### Data Wrangler vs Apache Spark

| 항목 | Data Wrangler | Apache Spark |
|------|--------------|---------------|
| 인터페이스 | 시각적 + 코드 | 코드 전용 |
| 설정 복잡도 | 낮음 (관리형) | 높음 (클러스터 관리) |
| 프로토타이핑 | 매우 빠름 | 상대적으로 느림 |
| 대규모 처리 | 지원 (Processing Job) | 네이티브 지원 |
| 생태계 | AWS | 범용 |

## 요약

Amazon SageMaker Data Wrangler는 ML 데이터 준비를 위한 직관적이고 강력한 도구입니다. 시각적 인터페이스를 통해 코드 없이도 복잡한 데이터 변환을 수행할 수 있으며, 필요한 경우 Python, PySpark, SQL로 커스텀 변환을 작성할 수 있습니다.

이 글에서 다룬 핵심 내용을 정리하면 다음과 같습니다.

- **데이터 가져오기**: S3, Athena, Redshift 등 다양한 소스에서 데이터를 쉽게 로드
- **데이터 탐색**: 자동 프로파일링과 Data Quality Report로 데이터 품질 파악
- **시각적 변환**: 300개 이상의 내장 변환을 드래그 앤 드롭으로 적용
- **커스텀 변환**: Pandas, PySpark, SQL로 사용자 정의 로직 작성 가능
- **내보내기**: S3, Feature Store, Pipelines 등 다양한 대상으로 결과 전달
- **재현성**: .flow 파일로 전체 변환 과정을 저장하고 반복 실행 가능

Data Wrangler를 처음 사용하는 경우, 작은 데이터셋으로 시작하여 기본 변환 기능을 익힌 후, 점차 커스텀 변환과 대규모 데이터 처리로 확장하는 것을 권장합니다. SageMaker Studio 내에서 Data Wrangler를 시작하여 직접 경험해 보시기 바랍니다.