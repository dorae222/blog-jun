<!-- infographic-hero -->
![Amazon SageMaker Inference Recommender - 최적 추론 인스턴스 자동 추천 가이드 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker Inference Recommender - 최적 추론 인스턴스 자동 추천 가이드 한 장 요약 인포그래픽*

# Amazon SageMaker Inference Recommender - 최적 추론 인스턴스 자동 추천 가이드

## 개요

Amazon SageMaker Inference Recommender는 머신러닝 모델의 추론 배포에 최적화된 컴퓨팅 인스턴스 유형과 구성을 자동으로 벤치마킹하여 추천하는 완전관리형 서비스입니다. ML 엔지니어가 수동으로 여러 인스턴스 유형을 하나씩 테스트하는 번거로운 과정 없이, 모델 특성에 맞는 최적의 인프라 구성을 데이터 기반으로 결정할 수 있습니다.

추론 배포 시 인스턴스 선택은 비용과 성능에 직접적인 영향을 미칩니다. 과도한 사양의 인스턴스를 선택하면 불필요한 비용이 발생하고, 부족한 사양을 선택하면 지연 시간이 증가하여 서비스 품질이 저하됩니다. Inference Recommender는 이러한 트레이드오프를 자동화된 벤치마크를 통해 해결하며, 비용 대비 최적의 성능을 달성할 수 있는 균형점을 찾아줍니다.

주요 활용 시나리오는 다음과 같습니다.

- 신규 모델 배포 전 최적 인스턴스 유형 선정
- 모델 업데이트 후 기존 인스턴스 구성의 적합성 재검증
- GPU vs CPU 인스턴스 간 비용 대비 성능 비교
- Auto Scaling 기준선이 되는 단일 인스턴스 처리량 측정
- 다양한 모델 서빙 프레임워크(TensorFlow Serving, TorchServe 등) 간 성능 비교

## 핵심 기능

### Default Job (기본 추천)

Default Job은 AWS가 축적한 수천 개의 사전 벤치마킹 데이터를 기반으로, 모델 프레임워크와 크기에 적합한 인스턴스 유형 Top 3를 빠르게 추천합니다. 별도의 샘플 데이터나 부하 테스트 없이 모델 등록만으로 추천을 받을 수 있으며, 약 2분 이내에 결과가 제공됩니다.

Default Job에서 고려하는 요소는 다음과 같습니다.

- 모델 프레임워크 (PyTorch, TensorFlow, XGBoost, MXNet 등)
- 모델 아티팩트 크기 (model.tar.gz 파일 크기)
- 컨테이너 이미지 유형 (CPU/GPU, 프레임워크 버전)
- NearestModelName 힌트 (유사한 공개 모델 이름)

### Advanced Job (상세 벤치마크)

Advanced Job은 실제 샘플 페이로드를 사용하여 사용자가 지정한 인스턴스 유형들에 대해 상세한 부하 테스트를 수행합니다. 실제로 엔드포인트를 프로비저닝하고, 점진적으로 동시 요청 수를 증가시키며 처리량과 지연 시간의 관계를 측정합니다.

| 구분 | Default Job | Advanced Job |
|------|------------|-------------|
| 실행 시간 | 약 2분 | 최대 2시간 |
| 샘플 데이터 | 불필요 | 필수 (S3 경로 지정) |
| 벤치마크 방식 | 사전 데이터 기반 매칭 | 실제 부하 테스트 수행 |
| 인스턴스 선택 | 자동 (Top 3 추천) | 사용자 지정 (최대 10개) |
| 트래픽 패턴 | 고정 | 커스텀 (Phases 설정) |
| 결과 상세도 | 기본 추천 | P50/P90/P99 지연 시간, 처리량, 비용 |
| SLA 조건 설정 | 불가 | 가능 (MaxLatency, MaxInvocations) |

### 벤치마크 지표

Inference Recommender는 다음 지표를 측정하여 리포트합니다.

- **Invocations Per Minute (IPM)**: 분당 처리 가능한 추론 요청 수
- **Model Latency P50/P90/P99**: 모델 추론 지연 시간 백분위 (밀리초)
- **Cost Per Hour**: 인스턴스 시간당 비용
- **Cost Per Inference**: 추론 건당 예상 비용 (비용/처리량)
- **Max Invocations**: 지연 시간 SLA를 만족하는 최대 동시 요청 수
- **CPU/Memory Utilization**: 인스턴스 리소스 사용률

## 아키텍처 및 동작 원리

Inference Recommender의 전체 워크플로우는 다음과 같은 단계로 진행됩니다.

```
[1. 모델 등록 (Model Registry / Model Package)]
                    |
                    v
[2. Inference Recommender Job 생성]
                    |
            +-------+-------+
            |               |
      [Default Job]   [Advanced Job]
            |               |
            v               v
  [사전 벤치마크       [인스턴스별 엔드포인트
   데이터 조회]        프로비저닝 및 부하 테스트]
            |               |
            v               v
  [Top 3 인스턴스     [상세 벤치마크 결과
   빠른 추천]          지표 리포트]
            |               |
            +-------+-------+
                    |
                    v
      [3. 최적 인스턴스 선택 및 배포]
```

Advanced Job의 부하 테스트는 Phases 방식으로 진행됩니다. 각 Phase에서 InitialNumberOfUsers(초기 동시 사용자 수)와 SpawnRate(초당 추가 사용자 수)를 설정할 수 있습니다. 예를 들어, Phase 1에서 1명으로 시작하여 초당 1명씩 추가하고, Phase 2에서 5명으로 시작하여 초당 2명씩 추가하는 형태로 점진적 부하를 가합니다.

벤치마크 중 Stopping Conditions를 설정하면, 지연 시간이 임계값을 초과하거나 최대 요청 수에 도달한 시점에서 자동으로 테스트가 중단됩니다.

## 실전 활용

### AWS CLI를 사용한 Default Job 실행

```bash
# 1. Model Package Group 생성
aws sagemaker create-model-package-group \
    --model-package-group-name my-bert-model-group \
    --model-package-group-description "BERT 기반 텍스트 분류 모델"

# 2. Model Package 등록
aws sagemaker create-model-package \
    --model-package-group-name my-bert-model-group \
    --inference-specification '{
        "Containers": [{
            "Image": "763104351884.dkr.ecr.ap-northeast-2.amazonaws.com/pytorch-inference:2.0-gpu-py310",
            "ModelDataUrl": "s3://my-bucket/models/bert/model.tar.gz",
            "Framework": "PYTORCH",
            "FrameworkVersion": "2.0",
            "NearestModelName": "bert-base-uncased"
        }],
        "SupportedContentTypes": ["application/json"],
        "SupportedResponseMIMETypes": ["application/json"]
    }'

# 3. Default Inference Recommender Job 생성
aws sagemaker create-inference-recommendations-job \
    --job-name bert-default-rec-$(date +%Y%m%d-%H%M%S) \
    --job-type Default \
    --role-arn arn:aws:iam::123456789012:role/SageMakerRole \
    --input-config '{
        "ModelPackageVersionArn": "arn:aws:sagemaker:ap-northeast-2:123456789012:model-package/my-bert-model-group/1"
    }'

# 4. 결과 조회
aws sagemaker describe-inference-recommendations-job \
    --job-name bert-default-rec-20240101-120000 \
    --query 'InferenceRecommendations[].{Instance:EndpointConfiguration.InstanceType,CostPerHour:Metrics.CostPerHour,Latency:Metrics.ModelLatency,MaxInvocations:Metrics.MaxInvocations}' \
    --output table
```

### Advanced Job으로 상세 벤치마크

```bash
# 샘플 페이로드를 S3에 업로드
echo '{"inputs": "Amazon SageMaker를 활용한 머신러닝 모델 배포 방법에 대해 설명합니다."}' > sample_payload.json
aws s3 cp sample_payload.json s3://my-bucket/inference-test/payload/sample_payload.json

# Advanced Inference Recommender Job 생성
aws sagemaker create-inference-recommendations-job \
    --job-name bert-advanced-rec-$(date +%Y%m%d-%H%M%S) \
    --job-type Advanced \
    --role-arn arn:aws:iam::123456789012:role/SageMakerRole \
    --input-config '{
        "ModelPackageVersionArn": "arn:aws:sagemaker:ap-northeast-2:123456789012:model-package/my-bert-model-group/1",
        "EndpointConfigurations": [
            {"InstanceType": "ml.g4dn.xlarge"},
            {"InstanceType": "ml.g5.xlarge"},
            {"InstanceType": "ml.p3.2xlarge"},
            {"InstanceType": "ml.c5.4xlarge"},
            {"InstanceType": "ml.c6i.4xlarge"}
        ],
        "JobDurationInSeconds": 7200,
        "TrafficPattern": {
            "TrafficType": "PHASES",
            "Phases": [
                {"InitialNumberOfUsers": 1, "SpawnRate": 1, "DurationInSeconds": 300},
                {"InitialNumberOfUsers": 5, "SpawnRate": 2, "DurationInSeconds": 300},
                {"InitialNumberOfUsers": 10, "SpawnRate": 5, "DurationInSeconds": 600}
            ]
        }
    }' \
    --stopping-conditions '{
        "MaxInvocations": 5000,
        "ModelLatencyThresholds": [
            {"Percentile": "P95", "ValueInMilliseconds": 500}
        ]
    }'
```

### SageMaker Python SDK 활용

```python
import sagemaker
from sagemaker import ModelPackage
from sagemaker.session import Session

session = Session()
role = 'arn:aws:iam::123456789012:role/SageMakerRole'

model_package = ModelPackage(
    role=role,
    model_package_arn='arn:aws:sagemaker:ap-northeast-2:123456789012:model-package/my-group/1',
    sagemaker_session=session
)

# Default Job 실행
default_result = model_package.right_size(
    sample_payload_url='s3://my-bucket/inference-test/payload/',
    supported_content_types=['application/json'],
    framework='PYTORCH'
)

# Advanced Job 실행
advanced_result = model_package.right_size(
    sample_payload_url='s3://my-bucket/inference-test/payload/',
    supported_content_types=['application/json'],
    framework='PYTORCH',
    job_duration_in_seconds=7200,
    endpoint_configurations=[
        {'InstanceType': 'ml.g4dn.xlarge'},
        {'InstanceType': 'ml.g5.xlarge'},
        {'InstanceType': 'ml.c5.4xlarge'}
    ]
)

# 결과 분석
for rec in advanced_result:
    instance = rec['EndpointConfiguration']['InstanceType']
    latency = rec['Metrics']['ModelLatency']
    cost = rec['Metrics']['CostPerHour']
    ipm = rec['Metrics']['MaxInvocations']
    print(f'{instance}: Latency={latency}ms, Cost=${cost}/hr, MaxIPM={ipm}')
```

## 모범 사례 및 보안

### 효율적인 벤치마킹 전략

- Default Job으로 먼저 후보 인스턴스 유형을 3~5개로 좁힌 후, Advanced Job으로 상세 벤치마크를 수행합니다. 이 2단계 접근법이 시간과 비용 면에서 가장 효율적입니다.
- 실제 운영 데이터를 대표하는 샘플 페이로드를 사용합니다. 평균적인 입력 크기뿐 아니라, 최대 크기의 입력과 최소 크기의 입력을 모두 포함하여 다양한 시나리오를 커버합니다.
- 트래픽 패턴의 Phases를 실제 서비스의 시간대별 패턴과 유사하게 설정합니다. 피크 시간대의 동시 요청 수를 정확히 반영해야 합니다.

### 비용 최적화 원칙

- P95 지연 시간 SLA를 만족하는 가장 저렴한 인스턴스를 선택합니다.
- GPU 인스턴스(ml.g4dn, ml.g5, ml.p3)가 필요한 딥러닝 모델과 CPU(ml.c5, ml.c6i)로 충분한 전통적 ML 모델(XGBoost, LightGBM 등)을 명확히 구분합니다.
- Graviton 기반 인스턴스(ml.c7g)는 CPU 추론에서 비용 대비 성능이 우수한 경우가 많으므로 후보에 포함합니다.
- 벤치마크 결과에서 Cost Per Inference 지표를 기준으로 최종 선택합니다.

### 보안 고려사항

- Inference Recommender Job 실행 IAM 역할에 최소 권한을 부여합니다.
- 샘플 페이로드에 PII(개인식별정보)나 민감한 데이터를 포함하지 않습니다. 필요 시 동일한 형태의 합성 데이터를 생성하여 사용합니다.
- S3에 저장된 모델 아티팩트와 샘플 데이터에 KMS 암호화를 적용합니다.
- VPC 구성을 통해 벤치마크 트래픽이 퍼블릭 인터넷을 경유하지 않도록 설정합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateInferenceRecommendationsJob",
        "sagemaker:DescribeInferenceRecommendationsJob",
        "sagemaker:StopInferenceRecommendationsJob"
      ],
      "Resource": "arn:aws:sagemaker:ap-northeast-2:123456789012:inference-recommendations-job/*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::my-bucket/inference-test/*"
    }
  ]
}
```

## 관련 서비스 비교

| 항목 | Inference Recommender | SageMaker Neo | SageMaker Serverless Inference |
|------|----------------------|---------------|-------------------------------|
| 목적 | 인스턴스 유형 최적화 | 모델 컴파일 최적화 | 서버리스 추론 배포 |
| 최적화 대상 | 인프라 선택 | 모델 바이너리 최적화 | 인프라 자동 관리 |
| 실행 시점 | 배포 전 벤치마킹 | 배포 전 컴파일 | 배포 시 자동 적용 |
| 비용 영향 | 인스턴스 비용 절감 | 추론 속도 향상으로 비용 절감 | 유휴 시간 비용 제거 |
| 적합한 상황 | 상시 운영 엔드포인트 | 특정 하드웨어 최적화 | 간헐적 트래픽 워크로드 |

Inference Recommender와 SageMaker Neo는 상호 보완적입니다. Neo로 모델을 최적화한 후 Inference Recommender로 최적 인스턴스를 선택하면, 두 가지 최적화 효과를 동시에 얻을 수 있습니다.

## 요약

Amazon SageMaker Inference Recommender는 ML 모델 배포 시 최적의 인스턴스 유형을 데이터 기반으로 선택할 수 있도록 지원하는 핵심 서비스입니다. Default Job으로 2분 내 빠른 추천을 받고, Advanced Job으로 실제 부하 환경에서의 상세 벤치마크를 수행할 수 있습니다. 모델 배포 전 반드시 Inference Recommender를 실행하여 비용 대비 최적의 성능을 확보하고, 불필요한 인프라 지출을 방지하는 것을 권장합니다. 특히 모델을 업데이트하거나 트래픽 패턴이 변경될 때마다 재벤치마킹을 수행하면 지속적으로 최적의 구성을 유지할 수 있습니다.