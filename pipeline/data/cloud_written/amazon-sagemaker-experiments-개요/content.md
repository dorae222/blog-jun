## 개요

머신러닝 개발은 본질적으로 실험적인 과정입니다. 최적의 모델을 찾기 위해 수십에서 수백 번의 실험을 반복하며, 각 실험에서 데이터셋, 하이퍼파라미터, 알고리즘, 피처 조합 등을 변경합니다. 이 과정에서 각 실험의 설정과 결과를 체계적으로 기록하지 않으면, 어떤 조합이 최상의 성능을 보였는지 추적하기 어려워집니다.

Amazon SageMaker Experiments는 이러한 ML 실험 관리 문제를 해결하는 서비스입니다. 모든 실험의 하이퍼파라미터, 메트릭, 데이터셋, 모델 아티팩트를 자동으로 추적하고, 실험 간 비교와 시각화를 제공합니다.

### 실험 관리가 중요한 이유

체계적인 실험 관리 없이 ML 개발을 진행하면 다음과 같은 문제가 발생합니다.

1. **재현성 부족**: "지난주에 좋은 결과를 냈던 설정이 뭐였지?"라는 질문에 답할 수 없습니다.
2. **비효율적인 탐색**: 이미 시도했던 하이퍼파라미터 조합을 다시 시도하게 됩니다.
3. **협업 어려움**: 팀원 간에 실험 결과를 공유하기 어렵습니다.
4. **의사결정 근거 부족**: 왜 특정 모델을 선택했는지에 대한 근거가 불명확합니다.
5. **감사 추적 불가**: 프로덕션에 배포된 모델이 어떤 실험에서 나왔는지 추적이 어렵습니다.

## 핵심 기능

### 1. 계층적 실험 구조

SageMaker Experiments는 세 계층의 구조로 실험을 조직합니다.

**Experiment (실험)**
- 최상위 수준의 논리적 그룹
- 하나의 ML 문제 또는 프로젝트를 나타냄
- 예: "고객 이탈 예측", "제품 추천 모델"

**Run (실행, 구 Trial)**
- Experiment 내의 개별 실험 실행
- 특정 하이퍼파라미터 세트로의 한 번의 학습을 나타냄
- 예: "learning_rate=0.01, batch_size=32로 학습"

**Run의 구성 요소**
- 파라미터(Parameters): 입력 하이퍼파라미터
- 메트릭(Metrics): 성능 지표 (정확도, 손실 등)
- 아티팩트(Artifacts): 모델 파일, 데이터셋 등
- 메타데이터(Metadata): 실행 시간, 인스턴스 타입 등

```
Experiment: customer-churn-prediction
  |
  +-- Run 1: xgboost-baseline
  |     Parameters: {max_depth: 5, eta: 0.1, num_round: 100}
  |     Metrics: {accuracy: 0.85, f1: 0.82, auc: 0.89}
  |     Artifacts: {model: s3://...model.tar.gz, data: s3://...train.csv}
  |
  +-- Run 2: xgboost-tuned
  |     Parameters: {max_depth: 8, eta: 0.05, num_round: 200}
  |     Metrics: {accuracy: 0.88, f1: 0.85, auc: 0.92}
  |
  +-- Run 3: lightgbm-experiment
  |     Parameters: {num_leaves: 31, learning_rate: 0.1, n_estimators: 150}
  |     Metrics: {accuracy: 0.87, f1: 0.84, auc: 0.91}
  |
  +-- Run 4: neural-network
        Parameters: {hidden_layers: [128, 64], lr: 0.001, epochs: 50}
        Metrics: {accuracy: 0.89, f1: 0.86, auc: 0.93}
```

### 2. 자동 추적

SageMaker Experiments는 SageMaker의 학습 작업(Training Job), 처리 작업(Processing Job), 변환 작업(Transform Job)과 자동으로 통합됩니다. 학습 작업을 실행할 때 실험 이름과 실행 이름을 지정하면, 하이퍼파라미터, 입출력 데이터, 메트릭이 자동으로 기록됩니다.

### 3. 수동 로깅

SageMaker SDK를 사용하여 커스텀 메트릭, 파라미터, 아티팩트를 직접 로깅할 수 있습니다.

```python
from sagemaker.experiments.run import Run
import sagemaker

session = sagemaker.Session()

with Run(
    experiment_name="customer-churn-prediction",
    run_name="custom-metrics-run",
    sagemaker_session=session,
) as run:
    # 파라미터 로깅
    run.log_parameter("algorithm", "xgboost")
    run.log_parameter("max_depth", 8)
    run.log_parameter("learning_rate", 0.05)
    run.log_parameter("num_boost_round", 200)
    run.log_parameter("subsample", 0.8)

    # 메트릭 로깅 (학습 중 반복)
    for epoch in range(100):
        train_loss = train_one_epoch(model, train_loader)
        val_loss, val_accuracy = evaluate(model, val_loader)

        run.log_metric("train_loss", train_loss, step=epoch)
        run.log_metric("val_loss", val_loss, step=epoch)
        run.log_metric("val_accuracy", val_accuracy, step=epoch)

    # 최종 메트릭
    run.log_metric("final_accuracy", 0.89)
    run.log_metric("final_f1", 0.86)
    run.log_metric("final_auc", 0.93)

    # 아티팩트 로깅
    run.log_artifact(
        name="training_data",
        value="s3://my-bucket/data/train.csv",
        media_type="text/csv",
    )
    run.log_artifact(
        name="model",
        value="s3://my-bucket/models/model.tar.gz",
        media_type="application/gzip",
    )

    # 파일 직접 로깅
    run.log_file(
        file_path="confusion_matrix.png",
        name="confusion_matrix",
        media_type="image/png",
    )
```

### 4. 실험 비교 및 시각화

SageMaker Studio에서 여러 실행의 결과를 테이블 형태로 비교하고, 차트로 시각화할 수 있습니다.

- **테이블 비교**: 모든 실행의 파라미터와 메트릭을 한 눈에 비교
- **산점도**: 두 메트릭 간의 관계 시각화
- **병렬 좌표**: 여러 하이퍼파라미터와 메트릭 간의 관계를 동시에 시각화
- **시계열 차트**: 학습 과정에서의 메트릭 변화 추이 비교

### 5. SageMaker Pipelines 통합

Experiments는 SageMaker Pipelines와 통합되어, 파이프라인의 각 실행을 자동으로 실험으로 기록합니다. 이를 통해 자동화된 ML 파이프라인에서도 모든 실행을 체계적으로 추적할 수 있습니다.

## 아키텍처/동작 원리

### 데이터 모델

SageMaker Experiments의 내부 데이터 모델은 다음과 같습니다.

```
[Experiment]
  - ExperimentName (PK)
  - DisplayName
  - Description
  - CreationTime
  - Tags
       |
       | 1:N
       v
[Run (Trial)]
  - RunName (PK)
  - ExperimentName (FK)
  - DisplayName
  - CreationTime
  - Status
       |
       | 1:N
       v
[Run Components]
  - Parameters: Key-Value 쌍
  - Metrics: Name-Value-Step 튜플
  - Artifacts: Name-URI-MediaType 튜플
  - InputDatasets: S3 경로 목록
  - OutputDatasets: S3 경로 목록
```

### 메트릭 저장 방식

메트릭은 두 가지 방식으로 저장됩니다.

1. **최종 메트릭(Summary Metrics)**: 실행 종료 시의 최종 값. Experiments API에 직접 저장됩니다.
2. **시계열 메트릭(Time-series Metrics)**: 학습 과정의 스텝별 메트릭. CloudWatch Metrics에 저장되며, Studio에서 시계열 차트로 시각화됩니다.

### SageMaker 서비스와의 통합

```
[SageMaker Training Job] --자동 추적--> [Experiments]
[SageMaker Processing Job] --자동 추적--> [Experiments]
[SageMaker Pipelines] --자동 추적--> [Experiments]
[SageMaker Autopilot] --자동 추적--> [Experiments]
[SageMaker HyperParameter Tuning] --자동 추적--> [Experiments]
[커스텀 코드 (SDK)] --수동 로깅--> [Experiments]
```

## 실전 활용

### 사용 사례 1: AWS CLI로 실험 관리

```bash
# 실험 생성
aws sagemaker create-experiment \
  --experiment-name customer-churn-prediction \
  --display-name "Customer Churn Prediction" \
  --description "고객 이탈 예측 모델 개발을 위한 실험"

# 실험 목록 조회
aws sagemaker list-experiments \
  --sort-by CreationTime \
  --sort-order Descending \
  --max-results 10

# 특정 실험의 상세 정보
aws sagemaker describe-experiment \
  --experiment-name customer-churn-prediction

# 실험에 속한 Trial(Run) 목록 조회
aws sagemaker list-trials \
  --experiment-name customer-churn-prediction \
  --sort-by CreationTime \
  --sort-order Descending

# Trial(Run) 상세 정보 조회
aws sagemaker describe-trial \
  --trial-name xgboost-baseline-run

# Trial Component (학습 작업 등) 상세 조회
aws sagemaker describe-trial-component \
  --trial-component-name xgboost-baseline-training-job \
  --query '{
    Parameters: Parameters,
    Metrics: Metrics,
    InputArtifacts: InputArtifacts,
    OutputArtifacts: OutputArtifacts
  }'
```

### 사용 사례 2: 학습 작업과 Experiments 통합

```bash
# Experiments를 지정한 학습 작업 생성
aws sagemaker create-training-job \
  --training-job-name churn-xgboost-tuned-$(date +%Y%m%d-%H%M%S) \
  --algorithm-specification '{
    "TrainingImage": "366743142698.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-xgboost:1.7-1",
    "TrainingInputMode": "File"
  }' \
  --role-arn arn:aws:iam::123456789012:role/SageMakerRole \
  --input-data-config '[
    {
      "ChannelName": "train",
      "DataSource": {
        "S3DataSource": {
          "S3DataType": "S3Prefix",
          "S3Uri": "s3://my-bucket/data/train/",
          "S3DataDistributionType": "FullyReplicated"
        }
      },
      "ContentType": "text/csv"
    },
    {
      "ChannelName": "validation",
      "DataSource": {
        "S3DataSource": {
          "S3DataType": "S3Prefix",
          "S3Uri": "s3://my-bucket/data/validation/",
          "S3DataDistributionType": "FullyReplicated"
        }
      },
      "ContentType": "text/csv"
    }
  ]' \
  --output-data-config '{
    "S3OutputPath": "s3://my-bucket/output/"
  }' \
  --resource-config '{
    "InstanceType": "ml.m5.xlarge",
    "InstanceCount": 1,
    "VolumeSizeInGB": 30
  }' \
  --stopping-condition '{"MaxRuntimeInSeconds": 3600}' \
  --hyper-parameters '{
    "max_depth": "8",
    "eta": "0.05",
    "num_round": "200",
    "subsample": "0.8",
    "colsample_bytree": "0.8",
    "objective": "binary:logistic",
    "eval_metric": "auc"
  }' \
  --experiment-config '{
    "ExperimentName": "customer-churn-prediction",
    "TrialName": "xgboost-tuned-run",
    "TrialComponentDisplayName": "XGBoost Tuned Training"
  }'

# 학습 완료 후 실험 결과 확인
aws sagemaker describe-training-job \
  --training-job-name churn-xgboost-tuned-$(date +%Y%m%d-%H%M%S) \
  --query '{
    Status: TrainingJobStatus,
    FinalMetrics: FinalMetricDataList,
    HyperParameters: HyperParameters
  }'
```

### 사용 사례 3: Python SDK로 하이퍼파라미터 튜닝과 Experiments 통합

```python
import sagemaker
from sagemaker.xgboost import XGBoost
from sagemaker.tuner import HyperparameterTuner, IntegerParameter, ContinuousParameter
from sagemaker.experiments.run import Run

session = sagemaker.Session()
role = sagemaker.get_execution_role()

# XGBoost Estimator 생성
estimator = XGBoost(
    entry_point="train.py",
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
    framework_version="1.7-1",
    hyperparameters={
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "num_round": 200,
    },
)

# 하이퍼파라미터 범위 정의
hyperparameter_ranges = {
    "max_depth": IntegerParameter(3, 12),
    "eta": ContinuousParameter(0.01, 0.3),
    "subsample": ContinuousParameter(0.5, 1.0),
    "colsample_bytree": ContinuousParameter(0.5, 1.0),
    "min_child_weight": IntegerParameter(1, 10),
}

# 튜너 생성 (Experiments 자동 통합)
tuner = HyperparameterTuner(
    estimator=estimator,
    objective_metric_name="validation:auc",
    hyperparameter_ranges=hyperparameter_ranges,
    max_jobs=20,
    max_parallel_jobs=4,
    strategy="Bayesian",
)

# 튜닝 작업 실행 (Experiments에 자동 기록)
tuner.fit(
    inputs={
        "train": f"s3://{session.default_bucket()}/data/train/",
        "validation": f"s3://{session.default_bucket()}/data/validation/",
    },
)

# 최적 하이퍼파라미터 확인
best_params = tuner.best_training_job()
print(f"Best training job: {best_params}")
```

### 사용 사례 4: 실험 검색 및 분석

```bash
# 특정 조건의 Trial Component 검색
aws sagemaker search \
  --resource TrialComponent \
  --search-expression '{
    "Filters": [
      {
        "Name": "Parents.ExperimentName",
        "Operator": "Equals",
        "Value": "customer-churn-prediction"
      },
      {
        "Name": "Metrics.validation:auc.Last",
        "Operator": "GreaterThan",
        "Value": "0.9"
      }
    ],
    "SortBy": "Metrics.validation:auc.Last",
    "SortOrder": "Descending"
  }' \
  --max-results 5

# 실험 간 메트릭 비교를 위한 데이터 추출
aws sagemaker list-trial-components \
  --trial-name xgboost-baseline-run \
  --query 'TrialComponentSummaries[].{Name:TrialComponentName,Status:Status.PrimaryStatus}'
```

### 사용 사례 5: 실험 정리

```bash
# 오래된 실험 삭제 (Trial Component -> Trial -> Experiment 순서로 삭제)

# Trial Component 삭제
aws sagemaker delete-trial-component \
  --trial-component-name old-training-job-component

# Trial에서 Trial Component 연결 해제
aws sagemaker disassociate-trial-component \
  --trial-name old-trial \
  --trial-component-name old-training-job-component

# Trial 삭제
aws sagemaker delete-trial --trial-name old-trial

# Experiment 삭제 (모든 Trial이 삭제된 후)
aws sagemaker delete-experiment \
  --experiment-name old-experiment
```

## 모범 사례/보안

### 실험 관리 모범 사례

1. **명명 규칙 수립**: 실험과 실행에 일관된 명명 규칙을 적용합니다.
   - Experiment: `{프로젝트}-{문제유형}` (예: ecommerce-churn-prediction)
   - Run: `{알고리즘}-{주요파라미터}-{날짜}` (예: xgboost-depth8-20240101)

2. **모든 것을 기록**: 하이퍼파라미터뿐만 아니라 데이터셋 버전, 전처리 방법, 피처 목록, 환경 설정 등 재현에 필요한 모든 정보를 기록합니다.

3. **메트릭 표준화**: 팀 내에서 사용하는 메트릭 이름과 형식을 표준화합니다.
   - 예: `train:loss`, `validation:accuracy`, `test:f1_score`

4. **태그 활용**: 실험과 실행에 태그를 부여하여 분류와 검색을 용이하게 합니다.

5. **정기적 정리**: 실패하거나 불필요한 실험을 주기적으로 정리하여 관리 부담을 줄입니다.

6. **Model Registry 연동**: 최종 선택된 모델은 SageMaker Model Registry에 등록하여 배포 파이프라인으로 연결합니다.

### 보안 모범 사례

1. **IAM 접근 제어**: 실험 데이터에 대한 접근을 팀 역할에 따라 제한합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateExperiment",
        "sagemaker:CreateTrial",
        "sagemaker:CreateTrialComponent",
        "sagemaker:UpdateTrialComponent",
        "sagemaker:AddAssociation",
        "sagemaker:Search"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/team": "${aws:PrincipalTag/team}"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:DescribeExperiment",
        "sagemaker:DescribeTrial",
        "sagemaker:DescribeTrialComponent",
        "sagemaker:ListExperiments",
        "sagemaker:ListTrials",
        "sagemaker:ListTrialComponents"
      ],
      "Resource": "*"
    }
  ]
}
```

2. **데이터 보호**: 실험에 기록된 아티팩트 경로(S3 URI)에 대한 접근을 적절히 제어합니다.

3. **감사 추적**: CloudTrail을 통해 실험 생성, 수정, 삭제 이력을 기록합니다.

## 관련 서비스 비교

### SageMaker Experiments vs MLflow

| 항목 | SageMaker Experiments | MLflow |
|------|----------------------|--------|
| 호스팅 | 완전 관리형 | 자체 운영 / SaaS |
| SageMaker 통합 | 네이티브 | 플러그인 |
| UI | SageMaker Studio | MLflow UI |
| 모델 레지스트리 | SageMaker Model Registry | MLflow Model Registry |
| 프레임워크 지원 | SageMaker 에코시스템 | 범용 (다양한 프레임워크) |
| 비용 | SageMaker 사용료에 포함 | 오픈소스 (인프라 비용 별도) |
| 커뮤니티 | AWS 생태계 | 대규모 오픈소스 커뮤니티 |

### SageMaker Experiments vs Weights & Biases (W&B)

| 항목 | SageMaker Experiments | Weights & Biases |
|------|----------------------|------------------|
| 시각화 | 기본적 (Studio 내) | 매우 풍부 |
| 협업 | SageMaker Studio 공유 | 웹 대시보드, 팀 기능 |
| 자동 추적 | SageMaker 서비스 | 다양한 프레임워크 |
| 하이퍼파라미터 스윕 | SageMaker Tuner 연동 | W&B Sweeps |
| 시스템 메트릭 | Debugger 연동 | 자동 수집 |
| 가격 | AWS 종량제 | 구독 기반 |

### SageMaker Experiments vs Neptune.ai

| 항목 | SageMaker Experiments | Neptune.ai |
|------|----------------------|------------|
| UI/UX | 기본적 | 풍부 |
| 실시간 모니터링 | 제한적 | 우수 |
| AWS 통합 | 네이티브 | 별도 설정 |
| 대규모 실험 관리 | 우수 | 우수 |
| 가격 | AWS 종량제 | 구독 기반 |

## 요약

Amazon SageMaker Experiments는 ML 실험의 체계적 관리를 위한 핵심 도구입니다. 실험의 모든 측면을 추적, 비교, 시각화하여 효율적인 모델 개발을 지원합니다.

핵심 특징을 정리하면 다음과 같습니다.

- **계층적 구조**: Experiment > Run > Components의 구조로 실험을 체계적으로 조직
- **자동 추적**: SageMaker Training, Processing, Pipelines와 자동 통합
- **수동 로깅**: Python SDK를 통한 커스텀 메트릭, 파라미터, 아티팩트 로깅
- **실험 비교**: 테이블, 차트를 통한 다중 실험 비교 및 시각화
- **검색 기능**: 메트릭 조건으로 실험을 필터링하고 정렬
- **Pipeline 통합**: SageMaker Pipelines의 각 실행을 자동으로 실험으로 기록
- **Model Registry 연동**: 최적 모델을 Registry에 등록하여 배포 파이프라인으로 연결

SageMaker Experiments는 특히 SageMaker 에코시스템 내에서 ML 워크플로우를 운영하는 조직에 적합합니다. 이미 SageMaker를 사용하고 있다면 추가 비용 없이 Experiments를 활용하여 실험 관리를 체계화할 수 있습니다. 다만, 보다 풍부한 시각화나 프레임워크 독립적인 실험 추적이 필요한 경우에는 MLflow나 Weights and Biases를 검토하는 것도 좋은 선택입니다.