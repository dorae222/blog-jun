# Amazon SageMaker Autopilot: AutoML로 모델 개발을 자동화하는 방법

## 개요

머신러닝 모델을 개발하는 과정은 데이터 탐색, 피처 엔지니어링, 알고리즘 선택, 하이퍼파라미터 튜닝, 모델 평가 등 수많은 단계를 거칩니다. 각 단계에서 최적의 선택을 하기 위해서는 상당한 전문 지식과 실험 시간이 필요합니다. AutoML(Automated Machine Learning)은 이 과정을 자동화하여, 데이터만 제공하면 최적의 모델을 자동으로 찾아주는 기술입니다.

Amazon SageMaker Autopilot은 AWS의 AutoML 서비스입니다. 테이블형(Tabular) 데이터를 입력으로 받아 데이터 전처리, 알고리즘 선택, 하이퍼파라미터 튜닝을 자동으로 수행하고, 최적의 모델을 제안합니다. 특히 다른 AutoML 서비스와 차별화되는 점은 **자동 생성된 노트북**을 제공한다는 것입니다. Autopilot이 수행한 모든 과정(데이터 분석, 피처 엔지니어링, 모델 훈련)을 코드로 확인하고 수정할 수 있어, 블랙박스가 아닌 투명한 AutoML을 실현합니다.

Autopilot V2에서는 시계열 예측(Time-series Forecasting), 자연어 처리(Text Classification), 이미지 분류(Image Classification) 등 기존 테이블형 데이터를 넘어선 문제 유형도 지원하기 시작했습니다.

## 핵심 기능

### 지원하는 문제 유형

| 문제 유형 | 설명 | 목적 함수 예시 |
|-----------|------|---------------|
| Binary Classification | 이진 분류 (예/아니오) | F1, AUC, Accuracy |
| Multiclass Classification | 다중 클래스 분류 | F1 Macro, Accuracy |
| Regression | 연속값 예측 | MSE, MAE, R2 |
| Time-series Forecasting | 시계열 예측 (V2) | MASE, WAPE, RMSE |
| Text Classification | 텍스트 분류 (V2) | F1, Accuracy |
| Image Classification | 이미지 분류 (V2) | F1, Accuracy |

### Autopilot 모드

Autopilot은 두 가지 모드로 동작할 수 있습니다.

**1. HPO 모드 (기본)**
- 데이터 분석 후 최적의 알고리즘과 하이퍼파라미터를 자동 탐색합니다.
- 최대 250개의 훈련 작업을 실행하여 최적 조합을 찾습니다.
- 사용 가능한 알고리즘: XGBoost, Linear Learner, Deep Learning (MLP)

**2. Ensembling 모드**
- AutoGluon 프레임워크를 기반으로 여러 모델을 앙상블합니다.
- 단일 훈련 작업으로 여러 알고리즘을 동시에 훈련하고 스태킹합니다.
- 일반적으로 HPO 모드보다 더 높은 성능을 달성하지만, 훈련 시간이 더 길 수 있습니다.

### Autopilot 작업 생성

```bash
# Autopilot 작업 생성 (HPO 모드)
aws sagemaker create-auto-ml-job-v2 \
  --auto-ml-job-name "churn-prediction-autopilot" \
  --auto-ml-job-input-data-config '[{
    "ChannelType": "training",
    "ContentType": "text/csv;header=present",
    "DataSource": {
      "S3DataSource": {
        "S3DataType": "S3Prefix",
        "S3Uri": "s3://my-data-bucket/churn-data/train.csv"
      }
    }
  }]' \
  --output-data-config '{"S3OutputPath": "s3://my-data-bucket/autopilot-output/"}' \
  --auto-ml-problem-type-config '{
    "TabularJobConfig": {
      "TargetAttributeName": "Churn",
      "ProblemType": "BinaryClassification",
      "CompletionCriteria": {
        "MaxCandidates": 50,
        "MaxRuntimePerTrainingJobInSeconds": 3600,
        "MaxAutoMLJobRuntimeInSeconds": 86400
      },
      "Mode": "HYPERPARAMETER_TUNING"
    }
  }' \
  --role-arn "arn:aws:iam::123456789012:role/SageMakerRole" \
  --region ap-northeast-2

# 작업 상태 확인
aws sagemaker describe-auto-ml-job-v2 \
  --auto-ml-job-name "churn-prediction-autopilot" \
  --region ap-northeast-2
```

### Ensembling 모드

```bash
# Autopilot 작업 생성 (Ensembling 모드)
aws sagemaker create-auto-ml-job-v2 \
  --auto-ml-job-name "churn-prediction-ensemble" \
  --auto-ml-job-input-data-config '[{
    "ChannelType": "training",
    "ContentType": "text/csv;header=present",
    "DataSource": {
      "S3DataSource": {
        "S3DataType": "S3Prefix",
        "S3Uri": "s3://my-data-bucket/churn-data/train.csv"
      }
    }
  }]' \
  --output-data-config '{"S3OutputPath": "s3://my-data-bucket/autopilot-output/"}' \
  --auto-ml-problem-type-config '{
    "TabularJobConfig": {
      "TargetAttributeName": "Churn",
      "ProblemType": "BinaryClassification",
      "Mode": "ENSEMBLING"
    }
  }' \
  --role-arn "arn:aws:iam::123456789012:role/SageMakerRole" \
  --region ap-northeast-2
```

### 결과 조회 및 최적 모델 선택

```bash
# 후보 모델 목록 조회
aws sagemaker list-candidates-for-auto-ml-job \
  --auto-ml-job-name "churn-prediction-autopilot" \
  --sort-by FinalObjectiveMetricValue \
  --sort-order Descending \
  --max-results 5 \
  --region ap-northeast-2

# 최적 모델의 상세 정보 조회
aws sagemaker describe-auto-ml-job-v2 \
  --auto-ml-job-name "churn-prediction-autopilot" \
  --query 'BestCandidate' \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### Autopilot 처리 단계

```
+------------------------------------------------------------------+
|                    Autopilot 자동화 파이프라인                      |
+------------------------------------------------------------------+
|                                                                  |
|  [1단계: 데이터 분석 (Analyzing)]                                  |
|  - 데이터 유형 감지 (수치형, 범주형, 텍스트)                        |
|  - 결측치 분석                                                    |
|  - 타겟 변수 분포 확인                                            |
|  - 문제 유형 자동 판별 (지정하지 않은 경우)                         |
|                         |                                        |
|                         v                                        |
|  [2단계: 피처 엔지니어링 (Feature Engineering)]                    |
|  - 수치형: 결측치 보간, 스케일링, 정규화                            |
|  - 범주형: 원핫 인코딩, 타겟 인코딩                                 |
|  - 텍스트: TF-IDF, 임베딩                                         |
|  - 자동 노트북 생성 (Data Exploration / Candidate Definition)      |
|                         |                                        |
|                         v                                        |
|  [3단계: 모델 훈련 (Training)]                                    |
|  HPO 모드:                                                       |
|  - XGBoost, Linear Learner, MLP 각각에 대해                      |
|  - Bayesian Optimization으로 하이퍼파라미터 탐색                   |
|  - 최대 250개 훈련 작업 실행                                      |
|                                                                  |
|  Ensembling 모드:                                                |
|  - AutoGluon 기반 다중 알고리즘 훈련                               |
|  - Weighted Ensemble / Stacking                                  |
|                         |                                        |
|                         v                                        |
|  [4단계: 모델 선택 (Model Selection)]                             |
|  - 목적 지표 기준으로 후보 모델 순위 매김                           |
|  - 최적 모델(Best Candidate) 선정                                 |
|  - 리더보드 생성                                                  |
+------------------------------------------------------------------+
```

### 자동 생성 노트북의 구조

Autopilot은 두 종류의 노트북을 자동으로 생성합니다.

**1. Data Exploration Notebook**
- 데이터의 기본 통계 정보 (컬럼별 타입, 결측치, 분포)
- 타겟 변수 분포 시각화
- 피처 간 상관관계 분석
- 이상치(Outlier) 탐지

**2. Candidate Definition Notebook**
- 피처 엔지니어링 파이프라인 코드
- 각 알고리즘별 하이퍼파라미터 탐색 범위
- 훈련 설정 (인스턴스 유형, 데이터 분할 비율)

이 노트북들은 S3의 출력 경로에 저장되며, 사용자가 다운로드하여 수정한 후 직접 실행할 수도 있습니다. 이것이 Autopilot의 핵심 차별점입니다. AutoML이 수행한 모든 과정을 코드로 확인하고 커스터마이즈할 수 있습니다.

### HPO (Hyperparameter Optimization) 전략

Autopilot의 HPO 모드는 Bayesian Optimization을 사용합니다.

1. **초기 탐색**: 랜덤하게 여러 하이퍼파라미터 조합을 시도합니다.
2. **서로게이트 모델 구축**: 초기 결과를 기반으로 "하이퍼파라미터 -> 성능" 관계를 모델링합니다.
3. **지능적 탐색**: 서로게이트 모델이 높은 성능을 예측하는 영역을 집중적으로 탐색합니다.
4. **수렴**: 성능 개선이 미미해질 때까지 반복합니다.

이 과정에서 조기 종료(Early Stopping)가 적용되어, 성능이 좋지 않은 훈련 작업은 조기에 중단하여 리소스를 절약합니다.

## 실전 활용

### 1. Python SDK를 활용한 Autopilot 실행

```python
import sagemaker
from sagemaker.automl.automl import AutoML

session = sagemaker.Session()
role = sagemaker.get_execution_role()

automl = AutoML(
    role=role,
    target_attribute_name='Churn',
    problem_type='BinaryClassification',
    sagemaker_session=session,
    max_candidates=50,
    mode='HYPERPARAMETER_TUNING',
    output_path='s3://my-data-bucket/autopilot-output/',
    job_objective={'MetricName': 'F1'}
)

# Autopilot 작업 실행
automl.fit(
    inputs='s3://my-data-bucket/churn-data/train.csv',
    job_name='churn-autopilot-v1',
    wait=True,  # 완료까지 대기
    logs=True   # 로그 출력
)

# 결과 확인
best_candidate = automl.describe_auto_ml_job()['BestCandidate']
print(f"최적 모델: {best_candidate['CandidateName']}")
print(f"알고리즘: {best_candidate['InferenceContainers'][0]['Image']}")

for metric in best_candidate['FinalAutoMLJobObjectiveMetric']:
    print(f"{metric.get('MetricName', 'Metric')}: {metric.get('Value', 'N/A')}")
```

### 2. 최적 모델 직접 배포

```python
# Autopilot이 찾은 최적 모델을 엔드포인트로 배포
predictor = automl.deploy(
    initial_instance_count=1,
    instance_type='ml.m5.large',
    endpoint_name='churn-autopilot-endpoint',
    candidate=best_candidate  # 특정 후보 모델 지정 (생략 시 최적 모델)
)

# 추론 테스트
import pandas as pd
test_data = pd.read_csv('test_sample.csv')
result = predictor.predict(test_data.to_csv(index=False, header=False))
print(f"예측 결과: {result}")

# 엔드포인트 정리
predictor.delete_endpoint()
```

### 3. 시계열 예측 (Autopilot V2)

```bash
# 시계열 예측 Autopilot 작업
aws sagemaker create-auto-ml-job-v2 \
  --auto-ml-job-name "sales-forecast-autopilot" \
  --auto-ml-job-input-data-config '[{
    "ChannelType": "training",
    "ContentType": "text/csv;header=present",
    "DataSource": {
      "S3DataSource": {
        "S3DataType": "S3Prefix",
        "S3Uri": "s3://my-data-bucket/sales-data/train.csv"
      }
    }
  }]' \
  --output-data-config '{"S3OutputPath": "s3://my-data-bucket/forecast-output/"}' \
  --auto-ml-problem-type-config '{
    "TimeSeriesForecastingJobConfig": {
      "ForecastFrequency": "D",
      "ForecastHorizon": 30,
      "ForecastQuantiles": ["p10", "p50", "p90"],
      "TimeSeriesConfig": {
        "TargetAttributeName": "sales",
        "TimestampAttributeName": "date",
        "ItemIdentifierAttributeName": "product_id"
      },
      "CompletionCriteria": {
        "MaxAutoMLJobRuntimeInSeconds": 43200
      }
    }
  }' \
  --role-arn "arn:aws:iam::123456789012:role/SageMakerRole" \
  --region ap-northeast-2
```

### 4. 후보 모델 비교 분석

```python
import boto3

sm = boto3.client('sagemaker', region_name='ap-northeast-2')

def compare_candidates(job_name, top_n=10):
    """Autopilot 후보 모델들을 비교합니다."""
    candidates = sm.list_candidates_for_auto_ml_job(
        AutoMLJobName=job_name,
        SortBy='FinalObjectiveMetricValue',
        SortOrder='Descending',
        MaxResults=top_n
    )

    print(f"{'Rank':<6} {'Candidate':<40} {'Metric':<12} {'Value':<10}")
    print('-' * 70)

    for i, candidate in enumerate(candidates['Candidates'], 1):
        name = candidate['CandidateName']
        objective = candidate.get('FinalAutoMLJobObjectiveMetric', {})
        metric_name = objective.get('MetricName', 'N/A')
        value = objective.get('Value', 0)

        # 알고리즘 추출
        containers = candidate.get('InferenceContainers', [])
        algo = 'Unknown'
        if containers:
            image = containers[-1].get('Image', '')
            if 'xgboost' in image:
                algo = 'XGBoost'
            elif 'linear-learner' in image:
                algo = 'Linear Learner'
            elif 'pytorch' in image or 'mxnet' in image:
                algo = 'Deep Learning'

        print(f"{i:<6} {name[:38]:<40} {metric_name:<12} {value:<10.4f} ({algo})")

compare_candidates('churn-prediction-autopilot')
```

## 모범 사례/보안

### 데이터 준비 가이드라인

1. **충분한 데이터량**: 최소 500행 이상을 권장합니다. 1,000행 이상이면 더 안정적인 결과를 얻을 수 있습니다.
2. **타겟 변수 분포**: 극심한 클래스 불균형(1:100 이상)이 있으면 성능이 저하될 수 있습니다. 오버샘플링/언더샘플링을 사전에 적용하는 것을 고려합니다.
3. **결측치 처리**: Autopilot이 자동으로 결측치를 처리하지만, 도메인 지식이 필요한 결측치는 사전에 처리하는 것이 좋습니다.
4. **피처 수**: 열(feature) 수가 행(sample) 수보다 많으면 과적합 위험이 있습니다.
5. **CSV 형식**: 헤더 행이 포함된 CSV 파일을 사용합니다. 구분자는 쉼표(,)를 권장합니다.

### 비용 최적화

```
[비용에 영향을 미치는 설정]
- MaxCandidates: 후보 모델 수 (많을수록 비용 증가, 성능 개선 가능성 증가)
- MaxRuntimePerTrainingJobInSeconds: 개별 훈련 작업 최대 시간
- MaxAutoMLJobRuntimeInSeconds: 전체 Autopilot 작업 최대 시간

[비용 절감 전략]
- 탐색 단계: MaxCandidates=20, 소규모 데이터 샘플로 시작
- 본격 실행: 데이터 검증 후 MaxCandidates=50~100으로 확대
- Ensembling 모드는 단일 훈련 작업이지만 인스턴스 시간이 길어질 수 있음
```

### Autopilot을 사용하지 말아야 하는 경우

- **비정형 데이터 중심**: 이미지/비디오/오디오가 주요 입력인 경우 (테이블형 데이터에 최적화)
- **특수 알고리즘 필요**: 그래프 신경망, 강화학습 등 Autopilot이 지원하지 않는 알고리즘이 필요한 경우
- **실시간 학습 필요**: 온라인 러닝이 필요한 경우
- **해석 가능성이 최우선**: SHAP, LIME 등 세밀한 해석이 필요한 규제 환경

### IAM 권한

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateAutoMLJobV2",
        "sagemaker:DescribeAutoMLJobV2",
        "sagemaker:ListCandidatesForAutoMLJob",
        "sagemaker:StopAutoMLJob"
      ],
      "Resource": "arn:aws:sagemaker:ap-northeast-2:123456789012:automl-job/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-data-bucket",
        "arn:aws:s3:::my-data-bucket/*"
      ]
    }
  ]
}
```

## 관련 서비스 비교

| 항목 | SageMaker Autopilot | Google Vertex AI AutoML | Azure AutoML | H2O AutoML (OSS) |
|------|--------------------|-----------------------|-------------|------------------|
| 지원 데이터 | 테이블, 시계열, 텍스트, 이미지 | 테이블, 이미지, 비디오, 텍스트 | 테이블, 시계열, NLP, CV | 테이블형 중심 |
| 알고리즘 | XGBoost, Linear, MLP, AutoGluon | 자체 Neural Architecture Search | LightGBM, XGBoost, 앙상블 등 | GBM, DL, GLM, 스택 앙상블 |
| 투명성 | 자동 생성 노트북 (코드 확인 가능) | 블랙박스 (모델 내부 비공개) | ONNX 내보내기, 설명 가능성 | 오픈소스 (완전 투명) |
| Ensembling | AutoGluon 기반 스태킹 | 미지원 | 스택 앙상블 지원 | Stacked Ensemble |
| 배포 통합 | SageMaker 엔드포인트 직접 배포 | Vertex AI 엔드포인트 | Azure ML 엔드포인트 | 별도 인프라 필요 |
| 비용 모델 | 훈련 인스턴스 시간 | 노드 시간 | 컴퓨팅 시간 | 무료 (인프라 별도) |
| SageMaker Canvas | 노코드 UI에서 Autopilot 실행 | 해당 없음 | ML Studio 디자이너 | 해당 없음 |

## 요약

Amazon SageMaker Autopilot은 테이블형 데이터를 위한 AWS의 AutoML 서비스입니다.

- **데이터만 제공하면** 피처 엔지니어링, 알고리즘 선택, 하이퍼파라미터 튜닝을 자동으로 수행하여 최적의 모델을 찾아줍니다.
- **HPO 모드**는 XGBoost/Linear Learner/MLP에 대해 Bayesian Optimization을, **Ensembling 모드**는 AutoGluon 기반 스태킹 앙상블을 수행합니다.
- **자동 생성 노트북**을 통해 Autopilot이 수행한 모든 과정을 코드로 확인하고 수정할 수 있어, 투명한 AutoML을 실현합니다.
- **Autopilot V2**에서 시계열 예측, 텍스트 분류, 이미지 분류 등 다양한 문제 유형을 추가로 지원합니다.
- Autopilot은 **빠른 프로토타이핑**과 **베이스라인 모델 수립**에 특히 유용합니다. 수동 ML 파이프라인의 대체가 아닌, 보완적 도구로 활용하는 것이 올바른 접근입니다.
- 데이터 품질이 결과의 핵심이므로, 충분한 데이터량, 적절한 클래스 균형, 도메인 지식에 기반한 전처리가 선행되어야 합니다.