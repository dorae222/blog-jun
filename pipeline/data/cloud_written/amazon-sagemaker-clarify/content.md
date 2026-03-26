## 개요

머신러닝 모델이 비즈니스 의사결정에 점점 더 많이 활용되면서, 모델의 공정성(Fairness)과 투명성(Transparency)에 대한 요구가 급격히 증가하고 있습니다. 모델이 특정 인구 집단에 대해 불공정한 예측을 하거나, 예측의 근거를 설명할 수 없다면 심각한 법적, 윤리적 문제가 발생할 수 있습니다.

Amazon SageMaker Clarify는 이러한 문제를 해결하기 위해 AWS가 제공하는 편향 탐지 및 모델 설명 도구입니다. Clarify는 ML 라이프사이클 전반에 걸쳐 편향을 탐지하고, 모델의 예측 결과를 해석 가능하게 만들어, 책임감 있는 AI(Responsible AI)를 구현할 수 있도록 지원합니다.

### 왜 편향 탐지와 모델 설명이 중요한가

실제 비즈니스에서 ML 모델 편향이 문제가 된 사례는 수없이 많습니다.

- **채용 AI**: 특정 성별에 대해 불리한 평가를 내리는 사례
- **대출 심사 AI**: 특정 인종이나 지역에 대해 불공정한 승인률을 보이는 사례
- **의료 AI**: 특정 인구 집단에 대해 부정확한 진단을 내리는 사례
- **보험 AI**: 보호 속성(나이, 성별 등)에 기반한 차별적 가격 책정 사례

이러한 문제는 단순히 윤리적 차원을 넘어, EU의 AI Act, 미국의 Algorithmic Accountability Act 등 규제 준수 측면에서도 반드시 해결해야 합니다.

SageMaker Clarify는 다음 세 가지 핵심 역할을 수행합니다.

1. **사전 학습 편향 분석(Pre-training Bias Analysis)**: 학습 데이터 자체에 존재하는 편향을 탐지
2. **사후 학습 편향 분석(Post-training Bias Analysis)**: 학습된 모델이 만들어내는 편향을 측정
3. **모델 설명(Model Explainability)**: SHAP 알고리즘을 활용하여 개별 예측의 근거를 설명

## 핵심 기능

### 1. 사전 학습 편향 분석 (Pre-training Bias Metrics)

학습 데이터에서 편향을 탐지하기 위해 Clarify는 다음과 같은 메트릭을 제공합니다.

**CI (Class Imbalance, 클래스 불균형)**
- 특정 그룹이 데이터셋에서 과대 또는 과소 대표되는 정도를 측정합니다.
- 값의 범위: -1 ~ +1 (0에 가까울수록 균형)
- 예: 대출 신청 데이터에서 남성/여성 비율이 8:2라면 CI는 높은 값을 보입니다.

**DPL (Difference in Proportions of Labels, 레이블 비율 차이)**
- 서로 다른 그룹 간 긍정적 결과(예: 대출 승인)의 비율 차이를 측정합니다.
- 예: 남성의 대출 승인률이 70%이고 여성의 승인률이 40%라면 DPL = 0.3

**KL (Kullback-Leibler Divergence)**
- 두 그룹의 결과 분포가 얼마나 다른지를 정보 이론 관점에서 측정합니다.

**JS (Jensen-Shannon Divergence)**
- KL Divergence의 대칭 버전으로, 두 분포 간의 차이를 0~1 범위로 정규화합니다.

**LP (Lp-norm)**
- 두 그룹 간 레이블 분포의 Lp-norm 거리를 측정합니다.

**TVD (Total Variation Distance)**
- 두 그룹의 레이블 분포 간 최대 차이를 측정합니다.

**KS (Kolmogorov-Smirnov Statistic)**
- 두 그룹의 누적 분포 함수 간 최대 차이를 측정합니다.

**CDDL (Conditional Demographic Disparity in Labels)**
- 다른 속성을 통제한 후에도 특정 인구통계학적 그룹에 대한 레이블 불균형이 존재하는지 측정합니다.

### 2. 사후 학습 편향 분석 (Post-training Bias Metrics)

모델 학습 후 예측 결과에서 편향을 측정하는 메트릭입니다.

**DPPL (Difference in Positive Proportions in Predicted Labels)**
- 예측된 긍정 레이블의 비율이 그룹 간에 얼마나 다른지 측정합니다.

**DI (Disparate Impact)**
- 불리한 그룹의 긍정 예측 비율을 유리한 그룹의 비율로 나눈 값입니다.
- DI < 0.8이면 일반적으로 차별이 존재한다고 판단합니다 (80% 규칙).

**DCA (Difference in Conditional Acceptance)**
- 실제 긍정인 샘플 중 긍정으로 예측된 비율의 그룹 간 차이입니다 (True Positive Rate 차이).

**DCR (Difference in Conditional Rejection)**
- 실제 부정인 샘플 중 부정으로 예측된 비율의 그룹 간 차이입니다 (True Negative Rate 차이).

**RD (Recall Difference)**
- 그룹 간 재현율(Recall)의 차이를 측정합니다.

**AD (Accuracy Difference)**
- 그룹 간 정확도의 차이를 측정합니다.

**TE (Treatment Equality)**
- 그룹 간 False Positive와 False Negative의 비율 차이를 측정합니다.

### 3. SHAP 기반 모델 설명

Clarify는 SHAP(SHapley Additive exPlanations) 알고리즘을 사용하여 모델의 예측을 설명합니다. SHAP은 게임 이론의 Shapley Value 개념에 기반하며, 각 피처가 특정 예측에 얼마나 기여했는지를 정량적으로 보여줍니다.

**글로벌 SHAP**: 전체 데이터셋에 대한 각 피처의 평균적 중요도를 나타냅니다.

**로컬 SHAP**: 개별 예측에 대해 각 피처가 해당 예측에 얼마나 기여했는지를 나타냅니다.

Clarify는 Kernel SHAP 알고리즘을 사용하여 모델에 구애받지 않는(model-agnostic) 설명을 제공합니다. 이는 어떤 ML 알고리즘으로 학습된 모델이든 설명할 수 있다는 것을 의미합니다.

### 4. 자연어 처리(NLP) 모델 설명

Clarify는 텍스트 데이터를 입력으로 사용하는 NLP 모델에 대해서도 설명을 제공할 수 있습니다. 입력 텍스트의 각 토큰(단어)이 예측에 미치는 영향을 시각화하여, 모델이 어떤 단어에 주목하여 예측을 내렸는지를 파악할 수 있습니다.

### 5. 컴퓨터 비전(CV) 모델 설명

이미지 분류 모델에 대해서는 입력 이미지의 어떤 영역이 예측에 가장 큰 영향을 미쳤는지를 히트맵으로 시각화합니다.

## 아키텍처/동작 원리

### Clarify 처리 파이프라인

Clarify의 내부 동작은 SageMaker Processing Job을 기반으로 합니다.

```
[입력 데이터]
     |
     v
[SageMaker Processing Job]
  - Clarify 컨테이너 실행
  - 편향 메트릭 계산 / SHAP 값 계산
  - 분산 처리 (다중 인스턴스 지원)
     |
     v
[결과 출력]
  - JSON 형식의 편향 리포트
  - SHAP 값 파일
  - PDF/HTML 시각화 리포트
     |
     v
[SageMaker Studio 시각화]
  - 인터랙티브 차트
  - 피처 중요도 그래프
  - 편향 메트릭 대시보드
```

### SHAP 계산 프로세스 상세

Kernel SHAP의 동작 원리는 다음과 같습니다.

1. **기준값(Baseline) 설정**: 입력 피처의 기대값 또는 지정된 기준 데이터셋을 설정합니다.
2. **피처 마스킹**: 각 피처를 순차적으로 마스킹(기준값으로 대체)하여 해당 피처가 없을 때의 예측값을 계산합니다.
3. **Shapley Value 계산**: 모든 가능한 피처 조합에 대해 각 피처의 한계 기여도(marginal contribution)를 계산합니다.
4. **집계**: 계산된 Shapley Value를 집계하여 글로벌/로컬 피처 중요도를 산출합니다.

이 과정은 계산 비용이 높기 때문에, Clarify는 샘플링 기법을 사용하여 근사적으로 SHAP 값을 계산하며, 분산 처리를 통해 대규모 데이터셋에서도 효율적으로 작동합니다.

### 실시간 설명 (Online Explainability)

Clarify는 SageMaker 실시간 엔드포인트와 통합하여, 추론 요청마다 실시간으로 SHAP 설명을 제공할 수도 있습니다. 이 기능은 고객 대면 애플리케이션에서 "왜 이런 결과가 나왔는지"를 즉시 설명해야 하는 경우에 유용합니다.

## 실전 활용

### 사용 사례 1: 대출 심사 모델의 편향 분석

대출 심사 ML 모델에 대한 편향 분석을 수행하는 전체 워크플로우입니다.

```bash
# 학습 데이터 업로드
aws s3 cp loan_application_data.csv \
  s3://my-clarify-bucket/data/loan/train.csv

# Clarify 분석 설정 파일 업로드
aws s3 cp clarify_config.json \
  s3://my-clarify-bucket/config/
```

Clarify 분석 설정 파일(JSON) 예시입니다.

```json
{
  "dataset_type": "text/csv",
  "headers": [
    "age", "gender", "income", "employment_years",
    "credit_score", "loan_amount", "approved"
  ],
  "label": "approved",
  "label_values_or_threshold": [1],
  "facet": [
    {
      "name_or_index": "gender",
      "value_or_threshold": [0]
    },
    {
      "name_or_index": "age",
      "value_or_threshold": [40]
    }
  ],
  "methods": {
    "pre_training_bias": {
      "methods": ["CI", "DPL", "KL", "JS", "LP", "TVD", "KS", "CDDL"]
    },
    "post_training_bias": {
      "methods": ["DPPL", "DI", "DCA", "DCR", "RD", "AD", "TE"]
    },
    "shap": {
      "baseline": "s3://my-clarify-bucket/data/loan/baseline.csv",
      "num_samples": 1000,
      "agg_method": "mean_abs",
      "save_local_shap_values": true
    }
  }
}
```

SageMaker Processing Job을 통해 Clarify 분석을 실행합니다.

```bash
# Clarify Processing Job 생성 및 실행
aws sagemaker create-processing-job \
  --processing-job-name loan-bias-analysis-$(date +%Y%m%d) \
  --processing-resources '{
    "ClusterConfig": {
      "InstanceCount": 1,
      "InstanceType": "ml.c5.xlarge",
      "VolumeSizeInGB": 30
    }
  }' \
  --app-specification '{
    "ImageUri": "306415355426.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-clarify-processing:1.0"
  }' \
  --processing-inputs '[
    {
      "InputName": "dataset",
      "S3Input": {
        "S3Uri": "s3://my-clarify-bucket/data/loan/train.csv",
        "LocalPath": "/opt/ml/processing/input/data",
        "S3DataType": "S3Prefix",
        "S3InputMode": "File"
      }
    },
    {
      "InputName": "analysis_config",
      "S3Input": {
        "S3Uri": "s3://my-clarify-bucket/config/clarify_config.json",
        "LocalPath": "/opt/ml/processing/input/config",
        "S3DataType": "S3Prefix",
        "S3InputMode": "File"
      }
    }
  ]' \
  --processing-output-config '{
    "Outputs": [{
      "OutputName": "analysis_result",
      "S3Output": {
        "S3Uri": "s3://my-clarify-bucket/output/loan-bias/",
        "LocalPath": "/opt/ml/processing/output",
        "S3UploadMode": "EndOfJob"
      }
    }]
  }' \
  --role-arn arn:aws:iam::123456789012:role/SageMakerClarifyRole

# 작업 상태 확인
aws sagemaker describe-processing-job \
  --processing-job-name loan-bias-analysis-$(date +%Y%m%d) \
  --query '{Status: ProcessingJobStatus, EndTime: ProcessingEndTime}'

# 결과 다운로드
aws s3 sync s3://my-clarify-bucket/output/loan-bias/ ./bias-results/
```

### 사용 사례 2: SageMaker Pipeline에 Clarify 통합

ML 파이프라인에 편향 분석을 자동화하여 포함시키는 Python 코드입니다.

```python
from sagemaker.clarify import (
    SageMakerClarifyProcessor,
    BiasConfig,
    DataConfig,
    ModelConfig,
    SHAPConfig,
)

# Clarify Processor 설정
clarify_processor = SageMakerClarifyProcessor(
    role="arn:aws:iam::123456789012:role/SageMakerClarifyRole",
    instance_count=1,
    instance_type="ml.c5.xlarge",
    sagemaker_session=sagemaker_session,
)

# 데이터 설정
data_config = DataConfig(
    s3_data_input_path="s3://my-clarify-bucket/data/loan/train.csv",
    s3_output_path="s3://my-clarify-bucket/output/",
    label="approved",
    headers=["age", "gender", "income", "employment_years",
             "credit_score", "loan_amount", "approved"],
    dataset_type="text/csv",
)

# 편향 설정
bias_config = BiasConfig(
    label_values_or_threshold=[1],
    facet_name="gender",
    facet_values_or_threshold=[0],
)

# 모델 설정
model_config = ModelConfig(
    model_name="loan-approval-model",
    instance_type="ml.m5.xlarge",
    instance_count=1,
    content_type="text/csv",
    accept_type="text/csv",
)

# SHAP 설정
shap_config = SHAPConfig(
    baseline="s3://my-clarify-bucket/data/loan/baseline.csv",
    num_samples=500,
    agg_method="mean_abs",
    save_local_shap_values=True,
)

# 사전 학습 편향 분석 실행
clarify_processor.run_pre_training_bias(
    data_config=data_config,
    data_bias_config=bias_config,
)

# 사후 학습 편향 분석 + 모델 설명 실행
clarify_processor.run_bias_and_explainability(
    data_config=data_config,
    bias_config=bias_config,
    model_config=model_config,
    explainability_config=shap_config,
)
```

### 사용 사례 3: 모델 모니터링에서 Clarify 활용

프로덕션 환경에서 지속적으로 편향을 모니터링합니다.

```bash
# Model Bias Monitor 스케줄 생성
aws sagemaker create-model-bias-job-definition \
  --job-definition-name loan-bias-monitor \
  --model-bias-app-specification '{
    "ImageUri": "306415355426.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-clarify-processing:1.0",
    "ConfigUri": "s3://my-clarify-bucket/config/monitor_config.json"
  }' \
  --model-bias-job-input '{
    "EndpointInput": {
      "EndpointName": "loan-approval-endpoint",
      "LocalPath": "/opt/ml/processing/input/endpoint",
      "S3DataDistributionType": "FullyReplicated",
      "S3InputMode": "File"
    },
    "GroundTruthS3Input": {
      "S3Uri": "s3://my-clarify-bucket/ground-truth/"
    }
  }' \
  --model-bias-job-output-config '{
    "MonitoringOutputs": [{
      "S3Output": {
        "S3Uri": "s3://my-clarify-bucket/monitoring-output/",
        "LocalPath": "/opt/ml/processing/output",
        "S3UploadMode": "EndOfJob"
      }
    }]
  }' \
  --job-resources '{
    "ClusterConfig": {
      "InstanceCount": 1,
      "InstanceType": "ml.c5.xlarge",
      "VolumeSizeInGB": 30
    }
  }' \
  --role-arn arn:aws:iam::123456789012:role/SageMakerClarifyRole

# 모니터링 스케줄 생성 (매일 실행)
aws sagemaker create-monitoring-schedule \
  --monitoring-schedule-name loan-bias-daily-monitor \
  --monitoring-schedule-config '{
    "ScheduleConfig": {
      "ScheduleExpression": "cron(0 9 * * ? *)"
    },
    "MonitoringJobDefinitionName": "loan-bias-monitor",
    "MonitoringType": "ModelBias"
  }'

# 모니터링 결과 확인
aws sagemaker list-monitoring-executions \
  --monitoring-schedule-name loan-bias-daily-monitor \
  --sort-by CreationTime \
  --sort-order Descending \
  --max-results 5
```

## 모범 사례/보안

### 편향 분석 모범 사례

1. **다중 편향 메트릭 활용**: 단일 메트릭에 의존하지 말고, 여러 편향 메트릭을 종합적으로 분석합니다. 하나의 메트릭에서는 편향이 없어 보여도 다른 메트릭에서는 편향이 드러날 수 있습니다.

2. **교차 분석(Intersectional Analysis) 수행**: 단일 보호 속성(예: 성별)뿐만 아니라, 여러 속성의 교차점(예: 여성이면서 고령자)에서의 편향도 분석합니다.

3. **사전/사후 학습 편향을 모두 분석**: 데이터 편향과 모델 편향은 다를 수 있으므로, 두 단계 모두에서 편향을 측정합니다.

4. **임계값(Threshold) 설정**: 조직의 공정성 기준에 따라 각 편향 메트릭의 허용 임계값을 사전에 설정합니다.

5. **지속적 모니터링**: 프로덕션 환경에서 편향은 시간이 지남에 따라 변화할 수 있으므로(데이터 드리프트), Clarify의 모니터링 기능을 활용하여 지속적으로 추적합니다.

### 보안 모범 사례

1. **데이터 접근 제어**: Clarify가 처리하는 데이터에는 민감한 개인 정보가 포함될 수 있으므로, 세분화된 IAM 정책을 적용합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateProcessingJob",
        "sagemaker:DescribeProcessingJob"
      ],
      "Resource": "arn:aws:sagemaker:ap-northeast-2:123456789012:processing-job/clarify-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-clarify-bucket/*",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}
```

2. **결과 데이터 보호**: Clarify의 분석 결과에는 민감한 정보(어떤 피처가 편향을 유발하는지 등)가 포함될 수 있으므로, 결과 데이터에 대한 접근도 제한합니다.

3. **VPC 내 실행**: Clarify Processing Job을 VPC 내에서 실행하여 네트워크 수준의 격리를 보장합니다.

4. **감사 추적**: CloudTrail을 활용하여 Clarify 작업의 실행 이력과 결과 접근 이력을 기록합니다.

### 규제 준수

Clarify의 편향 분석 결과는 다음 규제에 대한 준수 증거로 활용할 수 있습니다.

- **EU AI Act**: 고위험 AI 시스템에 대한 투명성 및 공정성 요구사항
- **ECOA (Equal Credit Opportunity Act)**: 대출 심사에서의 차별 금지
- **Fair Housing Act**: 주택 관련 의사결정에서의 차별 금지

## 관련 서비스 비교

### SageMaker Clarify vs Google Vertex AI의 What-If Tool

| 항목 | SageMaker Clarify | Vertex AI What-If Tool |
|------|-------------------|------------------------|
| 편향 메트릭 수 | 15+ 메트릭 | 제한적 |
| SHAP 지원 | 네이티브 지원 | 별도 라이브러리 필요 |
| NLP/CV 설명 | 지원 | 제한적 |
| 파이프라인 통합 | SageMaker Pipelines | Vertex AI Pipelines |
| 모니터링 | 내장 모니터링 스케줄 | 별도 설정 필요 |
| 오프라인/온라인 | 모두 지원 | 주로 오프라인 |

### SageMaker Clarify vs 오픈소스 도구

| 항목 | SageMaker Clarify | Fairlearn | AI Fairness 360 |
|------|-------------------|-----------|------------------|
| 관리형 서비스 | 완전 관리형 | 자체 운영 | 자체 운영 |
| 확장성 | 자동 분산 처리 | 수동 확장 | 수동 확장 |
| AWS 통합 | 네이티브 | 별도 구현 | 별도 구현 |
| 메트릭 범위 | 포괄적 | 포괄적 | 매우 포괄적 |
| 비용 | 유료 (인스턴스 기반) | 무료 | 무료 |
| 시각화 | SageMaker Studio 통합 | 별도 구현 | 별도 구현 |

### SageMaker Clarify vs SageMaker Model Monitor

| 항목 | SageMaker Clarify | SageMaker Model Monitor |
|------|-------------------|-------------------------|
| 주요 목적 | 편향 탐지 + 모델 설명 | 데이터/모델 품질 모니터링 |
| 분석 시점 | 학습 전/후 + 프로덕션 | 주로 프로덕션 |
| 편향 분석 | 전문적인 편향 메트릭 | 없음 |
| SHAP 설명 | 지원 | 없음 |
| 데이터 드리프트 | 없음 | 지원 |
| 모델 품질 | 없음 | 지원 |

## 요약

Amazon SageMaker Clarify는 책임감 있는 AI를 구현하기 위한 필수 도구입니다. ML 모델의 편향을 탐지하고, 예측의 근거를 설명함으로써, 조직이 공정하고 투명한 AI 시스템을 구축할 수 있도록 지원합니다.

핵심 특징을 정리하면 다음과 같습니다.

- **포괄적 편향 메트릭**: 사전/사후 학습 단계에서 15개 이상의 편향 메트릭을 제공하여 다각도로 공정성을 평가
- **SHAP 기반 모델 설명**: 모델에 구애받지 않는 설명 기능으로 예측의 투명성 확보
- **NLP/CV 모델 지원**: 텍스트와 이미지 모델에 대해서도 설명 제공
- **파이프라인 통합**: SageMaker Pipelines에 편향 분석을 자동화 단계로 포함
- **지속적 모니터링**: 프로덕션 환경에서 편향의 시간적 변화를 추적
- **규제 준수 지원**: EU AI Act 등 AI 관련 규제에 대한 준수 증거 확보

머신러닝 모델을 프로덕션에 배포하는 모든 조직은 Clarify를 ML 워크플로우에 통합하여, 편향 탐지와 모델 설명을 표준 프로세스로 확립하는 것을 권장합니다. 특히 금융, 의료, 채용 등 고위험 의사결정 분야에서는 Clarify의 활용이 필수적입니다.