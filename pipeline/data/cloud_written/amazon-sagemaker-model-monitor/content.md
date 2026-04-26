<!-- infographic-hero -->
![Amazon SageMaker Model Monitor 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker Model Monitor 한 장 요약 인포그래픽*

# Amazon SageMaker Model Monitor

## 개요

Amazon SageMaker Model Monitor는 프로덕션 환경에 배포된 머신러닝 모델의 품질을 지속적으로 모니터링하는 완전 관리형 서비스입니다. 모델이 배포된 이후에도 시간이 지남에 따라 입력 데이터의 분포가 변하거나(데이터 드리프트), 모델의 예측 정확도가 저하되는(모델 드리프트) 현상이 발생할 수 있습니다. Model Monitor는 이러한 문제를 자동으로 탐지하고 경고를 발생시켜, ML 모델의 신뢰성을 유지하는 데 핵심적인 역할을 합니다.

실제 프로덕션 환경에서 ML 모델이 실패하는 가장 흔한 원인 중 하나는 훈련 데이터와 실제 추론 데이터 사이의 분포 차이입니다. 예를 들어, 고객 이탈 예측 모델을 2023년 데이터로 훈련했는데, 2024년에 고객의 행동 패턴이 크게 변했다면 모델의 예측 정확도는 급격히 떨어질 수 있습니다. Model Monitor는 이러한 상황을 조기에 감지하여 모델 재훈련 시점을 판단하는 데 도움을 줍니다.

Model Monitor는 네 가지 유형의 모니터링을 제공합니다.

- **데이터 품질 모니터링(Data Quality Monitoring)**: 입력 데이터의 통계적 특성 변화를 감지합니다.
- **모델 품질 모니터링(Model Quality Monitoring)**: 모델의 예측 정확도 변화를 추적합니다.
- **바이어스 드리프트 모니터링(Bias Drift Monitoring)**: 모델의 편향성 변화를 감지합니다.
- **특성 기여도 드리프트 모니터링(Feature Attribution Drift Monitoring)**: 특성 중요도의 변화를 추적합니다.

## 핵심 기능

### 1. 데이터 품질 모니터링

데이터 품질 모니터링은 Model Monitor의 가장 기본적이고 핵심적인 기능입니다. 훈련 데이터를 기준(Baseline)으로 설정하고, 실시간 추론 데이터와 비교하여 통계적으로 유의미한 변화가 발생하면 위반(Violation)을 보고합니다.

모니터링되는 통계 지표는 다음과 같습니다.

- **수치형 특성**: 평균, 표준편차, 최솟값, 최댓값, 중앙값, 사분위수, 결측값 비율
- **범주형 특성**: 고유값 수, 최빈값, 분포 비율, 결측값 비율
- **전체 데이터**: 레코드 수, 특성 수, 데이터 유형 일관성

```python
from sagemaker.model_monitor import DefaultModelMonitor
from sagemaker.model_monitor.dataset_format import DatasetFormat
import sagemaker

session = sagemaker.Session()
role = sagemaker.get_execution_role()

# 기본 모니터 생성
my_monitor = DefaultModelMonitor(
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
    volume_size_in_gb=20,
    max_runtime_in_seconds=3600
)

# 베이스라인 생성 (훈련 데이터 기반)
my_monitor.suggest_baseline(
    baseline_dataset="s3://my-bucket/training-data/baseline.csv",
    dataset_format=DatasetFormat.csv(header=True),
    output_s3_uri="s3://my-bucket/model-monitor/baseline-results/",
    wait=True
)
```

### 2. 모니터링 스케줄 설정

모니터링 작업은 cron 표현식을 사용하여 주기적으로 실행되도록 스케줄링할 수 있습니다.

```python
from sagemaker.model_monitor import CronExpressionGenerator

# 매시간 모니터링 실행
my_monitor.create_monitoring_schedule(
    monitor_schedule_name="my-model-monitor-schedule",
    endpoint_input="my-prediction-endpoint",
    output_s3_uri="s3://my-bucket/model-monitor/reports/",
    statistics=my_monitor.baseline_statistics(),
    constraints=my_monitor.suggested_constraints(),
    schedule_cron_expression=CronExpressionGenerator.hourly()
)
```

```bash
# 모니터링 스케줄 상태 확인
aws sagemaker describe-monitoring-schedule \
  --monitoring-schedule-name "my-model-monitor-schedule" \
  --region us-east-1 \
  --query '{Status: MonitoringScheduleStatus, LastStatus: LastMonitoringExecutionSummary.MonitoringExecutionStatus}'

# 모니터링 실행 이력 조회
aws sagemaker list-monitoring-executions \
  --monitoring-schedule-name "my-model-monitor-schedule" \
  --region us-east-1 \
  --sort-by CreationTime \
  --sort-order Descending \
  --max-results 5 \
  --output table
```

### 3. 모델 품질 모니터링

모델 품질 모니터링은 Ground Truth(실제 레이블)와 모델 예측을 비교하여 모델의 성능을 추적합니다.

```python
from sagemaker.model_monitor import ModelQualityMonitor

model_quality_monitor = ModelQualityMonitor(
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
    volume_size_in_gb=20,
    max_runtime_in_seconds=1800,
    sagemaker_session=session
)

# 모델 품질 베이스라인 생성
model_quality_monitor.suggest_baseline(
    baseline_dataset="s3://my-bucket/model-quality/baseline.csv",
    dataset_format=DatasetFormat.csv(header=True),
    output_s3_uri="s3://my-bucket/model-monitor/model-quality-baseline/",
    problem_type="BinaryClassification",
    inference_attribute="prediction",
    probability_attribute="probability",
    ground_truth_attribute="label"
)
```

### 4. 바이어스 드리프트 모니터링

SageMaker Clarify와 통합되어 모델의 편향성 변화를 모니터링합니다. 특히 공정성이 중요한 금융, 채용, 의료 분야에서 필수적입니다.

```python
from sagemaker.model_monitor import BiasAnalysisConfig
from sagemaker.clarify import (
    BiasConfig,
    DataConfig,
    ModelConfig
)

bias_config = BiasConfig(
    label_values_or_threshold=[1],
    facet_name="gender",
    facet_values_or_threshold=[0]
)

analysis_config = BiasAnalysisConfig(
    bias_config=bias_config,
    headers=["feature1", "feature2", "gender", "label"],
    label="label"
)
```

### 5. 특성 기여도 드리프트 모니터링

SHAP(SHapley Additive exPlanations) 값을 기반으로 특성 중요도의 변화를 추적합니다. 이를 통해 모델의 의사결정 패턴이 시간에 따라 어떻게 변하는지 파악할 수 있습니다.

```python
from sagemaker.model_monitor import ExplainabilityAnalysisConfig
from sagemaker.clarify import SHAPConfig

shap_config = SHAPConfig(
    baseline=[[0.5, 0.3, 0.1, 0.8]],
    num_samples=100,
    agg_method="mean_abs"
)

explainability_config = ExplainabilityAnalysisConfig(
    explainability_config=shap_config,
    headers=["feature1", "feature2", "feature3", "feature4"],
    model_config=ModelConfig(
        model_name="my-model",
        instance_type="ml.m5.xlarge",
        instance_count=1
    )
)
```

## 아키텍처/동작 원리

### 데이터 캡처(Data Capture) 메커니즘

Model Monitor의 핵심 동작 원리는 데이터 캡처에서 시작됩니다. SageMaker 엔드포인트에 데이터 캡처를 활성화하면, 모든 추론 요청과 응답이 S3에 자동으로 저장됩니다.

```python
from sagemaker.model_monitor import DataCaptureConfig

# 데이터 캡처 설정
data_capture_config = DataCaptureConfig(
    enable_capture=True,
    sampling_percentage=100,  # 전체 트래픽의 100% 캡처
    destination_s3_uri="s3://my-bucket/model-monitor/data-capture/",
    capture_options=["REQUEST", "RESPONSE"],
    csv_content_types=["text/csv"],
    json_content_types=["application/json"]
)

# 엔드포인트 배포 시 데이터 캡처 활성화
predictor = model.deploy(
    initial_instance_count=1,
    instance_type="ml.m5.xlarge",
    data_capture_config=data_capture_config,
    endpoint_name="monitored-endpoint"
)
```

### 모니터링 파이프라인 흐름

전체 모니터링 파이프라인은 다음 단계로 구성됩니다.

1. **데이터 캡처**: 추론 요청/응답이 S3에 JSONL 형식으로 저장됩니다.
2. **스케줄링**: 설정된 cron 표현식에 따라 Processing Job이 트리거됩니다.
3. **통계 계산**: 캡처된 데이터에 대한 통계를 계산합니다.
4. **베이스라인 비교**: 계산된 통계를 베이스라인과 비교합니다.
5. **위반 탐지**: 설정된 임계값을 초과하는 항목을 위반으로 기록합니다.
6. **보고서 생성**: 통계 보고서와 위반 보고서를 S3에 저장합니다.
7. **알림 발송**: CloudWatch 이벤트를 통해 알림을 발송합니다.

```bash
# 데이터 캡처 파일 확인
aws s3 ls s3://my-bucket/model-monitor/data-capture/monitored-endpoint/AllTraffic/ \
  --recursive \
  --human-readable \
  --summarize

# 최근 모니터링 결과 확인
aws s3 ls s3://my-bucket/model-monitor/reports/ \
  --recursive \
  --human-readable
```

### 베이스라인과 위반 탐지

베이스라인은 두 가지 파일로 구성됩니다.

- **statistics.json**: 각 특성의 통계적 특성 (평균, 분산, 분포 등)
- **constraints.json**: 각 특성이 만족해야 하는 제약 조건 (데이터 타입, 범위, 결측 허용률 등)

위반 탐지 시 사용되는 주요 메트릭은 다음과 같습니다.

- **KL Divergence**: 두 확률 분포 간의 차이를 측정합니다.
- **L-infinity Norm**: 두 분포 간 최대 차이를 측정합니다.
- **Jensen-Shannon Divergence**: KL Divergence의 대칭 버전입니다.
- **Chi-squared Test**: 범주형 데이터의 분포 변화를 검증합니다.

## 실전 활용

### 사례 1: 실시간 추론 엔드포인트 모니터링

전자상거래 사이트의 상품 추천 모델을 모니터링하는 전체 워크플로입니다.

```python
import sagemaker
from sagemaker.model_monitor import (
    DefaultModelMonitor,
    CronExpressionGenerator,
    DataCaptureConfig
)
from sagemaker.model_monitor.dataset_format import DatasetFormat

session = sagemaker.Session()
role = sagemaker.get_execution_role()

# 1단계: 데이터 캡처가 활성화된 엔드포인트 배포
data_capture_config = DataCaptureConfig(
    enable_capture=True,
    sampling_percentage=50,  # 트래픽의 50%만 캡처 (비용 절감)
    destination_s3_uri="s3://my-bucket/capture/recommendation-model/"
)

# 2단계: 베이스라인 생성
monitor = DefaultModelMonitor(
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
    volume_size_in_gb=30
)

monitor.suggest_baseline(
    baseline_dataset="s3://my-bucket/training-data/recommendations-baseline.csv",
    dataset_format=DatasetFormat.csv(header=True),
    output_s3_uri="s3://my-bucket/baseline/recommendation-model/"
)

# 3단계: 모니터링 스케줄 생성 (매일 자정 실행)
monitor.create_monitoring_schedule(
    monitor_schedule_name="recommendation-model-monitor",
    endpoint_input="recommendation-endpoint",
    output_s3_uri="s3://my-bucket/reports/recommendation-model/",
    statistics=monitor.baseline_statistics(),
    constraints=monitor.suggested_constraints(),
    schedule_cron_expression=CronExpressionGenerator.daily()
)
```

### 사례 2: CloudWatch 알림과 자동 대응

Model Monitor의 위반 감지 시 CloudWatch 알림을 발송하고 자동 대응하는 구성입니다.

```python
import boto3
import json

# CloudWatch Events 규칙 생성
events_client = boto3.client('events')

# SageMaker Model Monitor 위반 감지 시 트리거되는 규칙
events_client.put_rule(
    Name='model-monitor-violation-rule',
    EventPattern=json.dumps({
        "source": ["aws.sagemaker"],
        "detail-type": ["SageMaker Model Monitor Constraint Violation"],
        "detail": {
            "MonitoringScheduleName": ["recommendation-model-monitor"]
        }
    }),
    State='ENABLED',
    Description='Model Monitor 위반 감지 시 알림'
)

# SNS 토픽으로 알림 전송
events_client.put_targets(
    Rule='model-monitor-violation-rule',
    Targets=[
        {
            'Id': 'sns-notification',
            'Arn': 'arn:aws:sns:us-east-1:123456789012:model-alerts'
        },
        {
            'Id': 'lambda-retraining',
            'Arn': 'arn:aws:lambda:us-east-1:123456789012:function:trigger-retraining'
        }
    ]
)
```

```bash
# CloudWatch 메트릭으로 모니터링 상태 확인
aws cloudwatch get-metric-statistics \
  --namespace "aws/sagemaker" \
  --metric-name "ModelMonitorViolations" \
  --dimensions Name=EndpointName,Value=recommendation-endpoint \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-31T23:59:59Z" \
  --period 86400 \
  --statistics Sum \
  --region us-east-1
```

### 사례 3: 커스텀 모니터링 컨테이너

기본 제공 모니터링 외에 커스텀 비즈니스 로직을 추가하는 방법입니다.

```python
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.model_monitor import MonitoringExecution

# 커스텀 모니터링 스크립트
custom_monitoring_script = """
import pandas as pd
import json
import os

def monitor(data_path, output_path):
    # 캡처된 데이터 로드
    data = pd.read_csv(data_path)
    
    violations = []
    
    # 커스텀 비즈니스 규칙 1: 평균 예측 확률이 너무 높거나 낮은 경우
    avg_prob = data['prediction_probability'].mean()
    if avg_prob < 0.1 or avg_prob > 0.9:
        violations.append({
            'feature': 'prediction_probability',
            'type': 'business_rule_violation',
            'description': f'평균 예측 확률({avg_prob:.4f})이 정상 범위(0.1-0.9)를 벗어남'
        })
    
    # 커스텀 비즈니스 규칙 2: 특정 카테고리 비율 확인
    category_dist = data['category'].value_counts(normalize=True)
    for cat, ratio in category_dist.items():
        if ratio > 0.5:
            violations.append({
                'feature': 'category',
                'type': 'distribution_violation',
                'description': f'카테고리 {cat}의 비율({ratio:.2%})이 50%를 초과'
            })
    
    # 결과 저장
    result = {
        'violations': violations,
        'statistics': {
            'record_count': len(data),
            'avg_prediction_probability': avg_prob,
            'category_distribution': category_dist.to_dict()
        }
    }
    
    with open(os.path.join(output_path, 'custom_report.json'), 'w') as f:
        json.dump(result, f, indent=2)
"""
```

## 모범 사례/보안

### 모니터링 전략 모범 사례

1. **적절한 샘플링 비율 설정**: 트래픽이 매우 높은 엔드포인트에서는 100% 캡처 대신 10~50% 샘플링을 사용하여 비용을 절감합니다.

2. **다층적 모니터링**: 데이터 품질, 모델 품질, 바이어스, 특성 기여도 모니터링을 동시에 구성하여 다각적으로 모델 상태를 파악합니다.

3. **경고 임계값 튜닝**: 초기에는 느슨한 임계값으로 시작하여 오탐(False Positive)을 줄이고, 점진적으로 조정합니다.

4. **베이스라인 주기적 갱신**: 모델을 재훈련할 때마다 베이스라인도 함께 갱신합니다.

5. **자동 대응 파이프라인 구축**: 위반 감지 시 자동으로 알림 발송, 로그 분석, 모델 재훈련 트리거 등의 대응 파이프라인을 구축합니다.

### 보안 고려사항

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ModelMonitorAccess",
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateMonitoringSchedule",
        "sagemaker:DescribeMonitoringSchedule",
        "sagemaker:ListMonitoringExecutions",
        "sagemaker:StopMonitoringSchedule",
        "sagemaker:DeleteMonitoringSchedule"
      ],
      "Resource": "arn:aws:sagemaker:*:*:monitoring-schedule/*"
    },
    {
      "Sid": "S3DataCaptureAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket/model-monitor/*",
        "arn:aws:s3:::my-bucket/capture/*"
      ]
    }
  ]
}
```

- 데이터 캡처 파일에 민감한 정보(PII)가 포함될 수 있으므로, S3 버킷에 적절한 접근 제어와 암호화를 적용합니다.
- 모니터링 결과 보고서에 대한 접근 권한을 제한하여, 관련 담당자만 확인할 수 있도록 합니다.
- VPC 내에서 모니터링 작업이 실행되도록 네트워크 격리를 설정합니다.

### 비용 최적화

```bash
# 모니터링 스케줄 목록 및 상태 확인 (불필요한 스케줄 정리)
aws sagemaker list-monitoring-schedules \
  --region us-east-1 \
  --status-equals Scheduled \
  --output table

# 오래된 데이터 캡처 파일 정리를 위한 S3 수명 주기 정책 확인
aws s3api get-bucket-lifecycle-configuration \
  --bucket my-bucket \
  --output json
```

## 관련 서비스 비교

### Model Monitor vs CloudWatch 커스텀 메트릭

| 항목 | Model Monitor | CloudWatch 커스텀 메트릭 |
|------|--------------|------------------------|
| 설정 복잡도 | 낮음 (내장 기능) | 높음 (직접 구현) |
| 통계 분석 | 자동 (분포 비교, 드리프트 탐지) | 수동 (사용자 정의) |
| 비용 | Processing Job 비용 | 메트릭/알람 비용 |
| 유연성 | 제한적 (정해진 프레임워크) | 높음 (자유로운 구현) |
| ML 특화 기능 | 지원 (SHAP, 바이어스 등) | 미지원 |

### Model Monitor vs Evidently AI

| 항목 | Model Monitor | Evidently AI |
|------|--------------|-------------|
| 관리 방식 | 완전 관리형 | 오픈소스/셀프 호스팅 |
| AWS 통합 | 네이티브 | 추가 구성 필요 |
| 시각화 | CloudWatch/Studio | 자체 대시보드 |
| 비용 | AWS 인프라 비용 | 무료 (인프라 비용만) |
| 커스터마이징 | 제한적 | 높음 |

### Model Monitor vs Whylogs

| 항목 | Model Monitor | Whylogs |
|------|--------------|--------|
| 접근 방식 | 배치 모니터링 | 프로파일 기반 |
| 실시간 지원 | 제한적 | 지원 |
| 저장 효율 | S3에 원본 저장 | 통계 프로파일만 저장 |
| 경량성 | 무거움 (Processing Job) | 가벼움 |

## 요약

Amazon SageMaker Model Monitor는 프로덕션 ML 모델의 건전성을 유지하기 위한 필수 도구입니다. 이 글에서 다룬 핵심 내용을 정리하면 다음과 같습니다.

- Model Monitor는 데이터 품질, 모델 품질, 바이어스 드리프트, 특성 기여도 드리프트의 네 가지 모니터링 유형을 제공합니다.
- 데이터 캡처 메커니즘을 통해 추론 요청/응답을 자동으로 S3에 저장하고, 스케줄링된 Processing Job으로 분석합니다.
- 베이스라인을 기준으로 통계적 방법(KL Divergence, Chi-squared Test 등)을 사용하여 드리프트를 탐지합니다.
- CloudWatch Events, SNS, Lambda와 연동하여 위반 감지 시 자동 알림 및 대응 파이프라인을 구축할 수 있습니다.
- 적절한 샘플링 비율 설정, 다층적 모니터링, 베이스라인 주기적 갱신이 주요 모범 사례입니다.
- SageMaker Clarify와 통합되어 공정성 및 설명 가능성 모니터링도 지원합니다.

ML 모델을 프로덕션에 배포하는 것은 시작일 뿐이며, 지속적인 모니터링과 유지보수가 모델의 비즈니스 가치를 결정합니다. Model Monitor는 이 과정을 자동화하고 체계화하는 데 핵심적인 역할을 하며, MLOps 파이프라인의 필수 구성 요소로 자리잡고 있습니다.