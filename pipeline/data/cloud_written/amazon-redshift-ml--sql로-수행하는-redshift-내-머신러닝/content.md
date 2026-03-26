## 개요

Amazon Redshift ML은 SQL 문만으로 Redshift 데이터 웨어하우스 내에서 머신러닝 모델을 생성, 학습, 추론할 수 있는 기능입니다. 내부적으로 Amazon SageMaker Autopilot을 활용하여 최적의 모델을 자동으로 선택하고 학습하며, 학습된 모델을 Redshift 내 SQL 함수로 배포하여 SELECT 문에서 직접 호출할 수 있습니다.

전통적으로 데이터 웨어하우스의 데이터로 머신러닝을 수행하려면 다음과 같은 과정이 필요했습니다.

1. Redshift에서 데이터를 추출 (UNLOAD)
2. S3로 전송
3. SageMaker 노트북에서 데이터 전처리
4. 모델 학습 및 하이퍼파라미터 튜닝
5. 모델 배포 (엔드포인트 생성)
6. 추론 결과를 다시 Redshift로 로드

Redshift ML은 이 6단계를 CREATE MODEL 한 줄로 대체합니다. 데이터 분석가나 SQL 개발자가 별도의 ML 프레임워크 지식 없이도 예측 모델을 활용할 수 있도록 설계되었습니다.

---

## 핵심 기능

### 1. CREATE MODEL 문법

Redshift ML의 핵심은 CREATE MODEL SQL 문입니다.

```sql
-- 자동 모델 생성 (SageMaker Autopilot)
CREATE MODEL customer_churn_model
FROM (
    SELECT 
        customer_tenure_months,
        monthly_charges,
        total_charges,
        contract_type,
        payment_method,
        internet_service,
        num_support_tickets,
        churn_flag  -- 타겟 컬럼
    FROM customer_data
    WHERE data_split = 'train'
)
TARGET churn_flag
FUNCTION predict_churn
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftMLRole'
SETTINGS (
    S3_BUCKET 'my-redshift-ml-bucket',
    MAX_RUNTIME 7200  -- 최대 학습 시간 (초)
);
```

```bash
# Data API를 통한 모델 생성
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --db-user admin \
  --sql "CREATE MODEL customer_churn_model FROM (SELECT customer_tenure_months, monthly_charges, total_charges, contract_type, payment_method, churn_flag FROM customer_data WHERE data_split = 'train') TARGET churn_flag FUNCTION predict_churn IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftMLRole' SETTINGS (S3_BUCKET 'my-redshift-ml-bucket');" \
  --region ap-northeast-2
```

### 2. 지원 모델 유형

Redshift ML은 다음 문제 유형을 자동으로 인식합니다.

| 문제 유형 | 타겟 컬럼 특성 | 자동 선택 알고리즘 |
|----------|--------------|------------------|
| 이진 분류 (Binary Classification) | 2개 범주 (Yes/No 등) | XGBoost, Linear Learner |
| 다중 분류 (Multi-class Classification) | 3개 이상 범주 | XGBoost, Multi-class Linear Learner |
| 회귀 (Regression) | 연속 숫자 | XGBoost, Linear Learner |

문제 유형을 명시적으로 지정할 수도 있습니다.

```sql
-- 문제 유형 명시
CREATE MODEL price_prediction_model
FROM training_data
TARGET price
FUNCTION predict_price
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftMLRole'
PROBLEM_TYPE REGRESSION
OBJECTIVE 'MSE'
SETTINGS (
    S3_BUCKET 'my-redshift-ml-bucket',
    MAX_RUNTIME 3600
);
```

### 3. BYOM (Bring Your Own Model)

자체 학습한 SageMaker 모델이나 사전 훈련된 모델을 Redshift에 가져와 SQL 함수로 사용할 수 있습니다.

```sql
-- SageMaker 엔드포인트의 모델을 Redshift 함수로 등록
CREATE MODEL remote_fraud_model
FUNCTION detect_fraud (transaction_amount FLOAT, merchant_category VARCHAR, hour_of_day INT)
RETURNS VARCHAR
SAGEMAKER 'fraud-detection-endpoint'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftMLRole';
```

### 4. XGBoost 모델 직접 지정

Autopilot 대신 XGBoost를 직접 지정하여 학습 시간을 단축할 수 있습니다.

```sql
CREATE MODEL quick_prediction_model
FROM training_data
TARGET label
FUNCTION quick_predict
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftMLRole'
MODEL_TYPE XGBOOST
SETTINGS (
    S3_BUCKET 'my-redshift-ml-bucket',
    MAX_RUNTIME 1800
);
```

---

## 아키텍처/동작 원리

### Redshift ML 내부 동작 흐름

```
[1. CREATE MODEL 실행]
Redshift Cluster
    |- 학습 데이터를 S3로 UNLOAD (자동)
    |
    v
[2. SageMaker Autopilot 호출]
Amazon SageMaker
    |- 데이터 분석 (데이터 타입, 결측치, 분포 등)
    |- 다수의 후보 파이프라인 생성
    |- 각 파이프라인으로 모델 학습
    |- 최적 모델 선택 (Cross-Validation)
    |- 모델 아티팩트를 S3에 저장
    |
    v
[3. 모델 배포]
Redshift Cluster
    |- SageMaker 모델을 로컬로 컴파일
    |- SQL 함수로 등록
    |- 추론 시 Redshift 내부에서 직접 실행
    |
    v
[4. 추론 (예측)]
SELECT predict_churn(...) → 로컬 추론 실행
```

핵심 포인트는 학습은 SageMaker에서, 추론은 Redshift 내부에서 수행된다는 것입니다. 추론 시 외부 서비스 호출이 없어 지연이 매우 낮습니다.

### SageMaker Autopilot의 역할

Autopilot은 다음 작업을 자동으로 수행합니다.

1. **데이터 탐색**: 컬럼 타입 추론, 결측치 분석, 카디널리티 확인
2. **특성 공학(Feature Engineering)**: 원-핫 인코딩, 수치 정규화, 결측치 대체
3. **알고리즘 선택**: 문제 유형에 따라 적합한 알고리즘 후보 선정
4. **하이퍼파라미터 튜닝**: Bayesian Optimization으로 최적 파라미터 탐색
5. **모델 평가**: K-Fold Cross-Validation으로 성능 평가
6. **최적 모델 선택**: 평가 지표 기준 최고 성능 모델 선택

### IAM 역할 요구사항

Redshift ML에 필요한 IAM 역할은 다음 권한을 포함해야 합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateAutoMLJob",
        "sagemaker:DescribeAutoMLJob",
        "sagemaker:CreateModel",
        "sagemaker:CreateEndpointConfig",
        "sagemaker:CreateEndpoint",
        "sagemaker:DescribeEndpoint",
        "sagemaker:InvokeEndpoint",
        "sagemaker:CreateCompilationJob"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:GetBucketLocation",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-redshift-ml-bucket",
        "arn:aws:s3:::my-redshift-ml-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::123456789012:role/SageMakerExecutionRole"
    }
  ]
}
```

---

## 실전 활용

### 1. 고객 이탈 예측

```sql
-- 모델 학습
CREATE MODEL churn_model
FROM (
    SELECT 
        tenure_months,
        monthly_charges,
        total_charges,
        contract_type,
        payment_method,
        internet_service,
        online_security,
        tech_support,
        num_support_tickets,
        churn  -- 'Yes' or 'No'
    FROM customer_features
)
TARGET churn
FUNCTION predict_churn
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftMLRole'
PROBLEM_TYPE BINARY_CLASSIFICATION
OBJECTIVE 'F1'
SETTINGS (
    S3_BUCKET 'my-redshift-ml-bucket',
    MAX_RUNTIME 7200
);

-- 모델 상태 확인
SHOW MODEL churn_model;

-- 이탈 위험 고객 목록 추출
SELECT 
    customer_id,
    customer_name,
    monthly_charges,
    contract_type,
    predict_churn(
        tenure_months,
        monthly_charges,
        total_charges,
        contract_type,
        payment_method,
        internet_service,
        online_security,
        tech_support,
        num_support_tickets
    ) as churn_prediction
FROM current_customers
WHERE predict_churn(
        tenure_months, monthly_charges, total_charges,
        contract_type, payment_method, internet_service,
        online_security, tech_support, num_support_tickets
    ) = 'Yes'
ORDER BY monthly_charges DESC;
```

```bash
# 모델 상태를 Data API로 확인
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --db-user admin \
  --sql "SHOW MODEL churn_model;" \
  --region ap-northeast-2
```

### 2. 매출 예측 (회귀)

```sql
-- 매출 예측 모델
CREATE MODEL revenue_forecast_model
FROM (
    SELECT 
        month_number,
        product_category,
        marketing_spend,
        num_promotions,
        avg_price,
        competitor_price,
        season,
        monthly_revenue  -- 타겟: 연속 숫자
    FROM historical_revenue
)
TARGET monthly_revenue
FUNCTION forecast_revenue
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftMLRole'
PROBLEM_TYPE REGRESSION
OBJECTIVE 'MSE'
SETTINGS (
    S3_BUCKET 'my-redshift-ml-bucket',
    MAX_RUNTIME 3600
);

-- 다음 분기 매출 예측
SELECT 
    product_category,
    planned_marketing_spend,
    forecast_revenue(
        month_number,
        product_category,
        planned_marketing_spend,
        planned_promotions,
        current_avg_price,
        competitor_price,
        season
    ) as predicted_revenue
FROM next_quarter_plan
ORDER BY predicted_revenue DESC;
```

### 3. 이상 탐지 (분류 활용)

```sql
-- 이상 거래 탐지 모델
CREATE MODEL fraud_detection_model
FROM (
    SELECT 
        transaction_amount,
        merchant_category,
        hour_of_day,
        day_of_week,
        distance_from_home,
        is_international,
        avg_transaction_amount_30d,
        transaction_count_24h,
        is_fraud  -- 0 또는 1
    FROM labeled_transactions
)
TARGET is_fraud
FUNCTION detect_fraud
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftMLRole'
PROBLEM_TYPE BINARY_CLASSIFICATION
OBJECTIVE 'F1'
SETTINGS (
    S3_BUCKET 'my-redshift-ml-bucket',
    MAX_RUNTIME 5400
);

-- 실시간(배치) 이상 거래 스크리닝
SELECT 
    transaction_id,
    customer_id,
    transaction_amount,
    detect_fraud(
        transaction_amount, merchant_category, hour_of_day,
        day_of_week, distance_from_home, is_international,
        avg_transaction_amount_30d, transaction_count_24h
    ) as fraud_flag
FROM recent_transactions
WHERE detect_fraud(
    transaction_amount, merchant_category, hour_of_day,
    day_of_week, distance_from_home, is_international,
    avg_transaction_amount_30d, transaction_count_24h
) = 1;
```

### 4. 모델 성능 평가

```sql
-- 학습 메트릭 확인
SHOW MODEL churn_model;

-- 결과 예시:
-- Model Name: churn_model
-- Schema: public
-- Owner: admin
-- Creation Time: 2024-01-15 10:30:00
-- Model State: READY
-- Validation:Accuracy: 0.892
-- Validation:F1: 0.856
-- Validation:AUC: 0.923

-- 테스트 데이터셋으로 추가 평가
SELECT 
    churn as actual,
    predict_churn(
        tenure_months, monthly_charges, total_charges,
        contract_type, payment_method, internet_service,
        online_security, tech_support, num_support_tickets
    ) as predicted,
    COUNT(*) as cnt
FROM customer_features
WHERE data_split = 'test'
GROUP BY actual, predicted
ORDER BY actual, predicted;
```

---

## 모범 사례/보안

### 모델 품질 향상

1. **충분한 학습 데이터**: 최소 수천 건 이상의 레코드를 확보합니다. 분류 문제에서는 각 클래스의 비율이 너무 불균형하지 않도록 주의합니다.
2. **특성 공학**: 의미 있는 파생 특성(Feature)을 미리 계산하여 학습 데이터에 포함시킵니다.
3. **데이터 분할**: 학습/검증/테스트 데이터를 사전에 분리합니다.
4. **MAX_RUNTIME 충분히 설정**: Autopilot의 탐색 시간이 충분해야 최적 모델을 찾을 수 있습니다.
5. **정기적 재학습**: 데이터 분포가 변하면(Data Drift) 모델을 재학습합니다.

### 비용 관리

- CREATE MODEL 실행 시 SageMaker Autopilot 비용이 발생합니다.
- 학습 시간(MAX_RUNTIME)에 따라 비용이 달라집니다.
- 추론(예측)은 Redshift 내부에서 실행되므로 추가 비용이 없습니다.
- BYOM으로 SageMaker 엔드포인트를 사용하는 경우, 엔드포인트 비용이 별도로 발생합니다.

```bash
# SageMaker Autopilot 작업 상태 확인
aws sagemaker describe-auto-ml-job \
  --auto-ml-job-name redshift-auto-churn-model \
  --query "{Status:AutoMLJobStatus,BestCandidate:BestCandidate.CandidateName}" \
  --region ap-northeast-2
```

### 보안

- 학습 데이터가 S3에 임시 저장되므로, S3 버킷에 적절한 암호화(SSE-S3 또는 SSE-KMS)를 적용합니다.
- IAM 역할은 최소 권한 원칙을 따르며, 특정 S3 버킷과 SageMaker 리소스에만 접근을 허용합니다.
- 모델 함수에 대한 GRANT/REVOKE로 접근 권한을 관리합니다.

---

## 관련 서비스 비교

| 항목 | Redshift ML | SageMaker Studio | SageMaker Autopilot (직접) |
|------|------------|-----------------|---------------------------|
| 인터페이스 | SQL | Python (Notebook) | Python API / Console |
| 대상 사용자 | SQL 개발자, 분석가 | ML 엔지니어, 데이터 과학자 | ML 엔지니어 |
| 커스터마이징 | 제한적 (문제 유형, 목표 지표) | 무제한 | 중간 |
| 특성 공학 | SQL로 사전 처리 | Python으로 자유롭게 | Autopilot 자동 처리 |
| 지원 알고리즘 | XGBoost, Linear Learner 등 | 수백 종 | XGBoost, Linear 등 |
| 추론 위치 | Redshift 내부 (빠름) | SageMaker 엔드포인트 | SageMaker 엔드포인트 |
| 학습 비용 | SageMaker 비용 | SageMaker 비용 | SageMaker 비용 |
| 추론 비용 | Redshift에 포함 | 엔드포인트 비용 | 엔드포인트 비용 |
| 적합 시나리오 | DW 데이터 기반 간단한 예측 | 복잡한 ML 파이프라인 | 코드 없는 자동 ML |

---

## 요약

Amazon Redshift ML은 SQL 개발자와 데이터 분석가가 별도의 ML 프레임워크 없이도 머신러닝을 활용할 수 있는 혁신적인 기능입니다.

1. **CREATE MODEL 한 줄로 완성**: 데이터 추출, 학습, 튜닝, 배포의 전 과정이 자동화됩니다.
2. **SageMaker Autopilot 활용**: 최적의 알고리즘과 하이퍼파라미터를 자동으로 선택합니다.
3. **SQL 함수로 추론**: SELECT 문에서 예측 함수를 직접 호출하여 기존 쿼리에 자연스럽게 통합합니다.
4. **추론 비용 없음**: 학습된 모델은 Redshift 내부에서 실행되어 추가 추론 비용이 없습니다.
5. **BYOM 지원**: 자체 학습한 SageMaker 모델도 SQL 함수로 등록하여 사용할 수 있습니다.
6. **분류, 회귀 자동 인식**: 타겟 컬럼의 특성에 따라 문제 유형을 자동으로 판단합니다.

Redshift ML은 복잡한 ML 파이프라인을 대체하는 것이 아니라, 데이터 웨어하우스 내에서 간단하고 빠르게 예측을 수행해야 하는 시나리오에 최적화된 도구입니다.