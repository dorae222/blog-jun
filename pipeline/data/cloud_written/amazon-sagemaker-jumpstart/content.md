# Amazon SageMaker JumpStart

## 개요

Amazon SageMaker JumpStart는 머신러닝 여정을 가속화하기 위해 AWS가 제공하는 머신러닝 허브입니다. 사전 훈련된 파운데이션 모델(Foundation Model), 빌트인 알고리즘, 그리고 엔드투엔드 솔루션 템플릿을 한곳에서 제공하여, 데이터 과학자와 ML 엔지니어가 모델 개발부터 배포까지의 전 과정을 효율적으로 수행할 수 있도록 지원합니다.

전통적인 ML 워크플로에서는 모델 선택, 데이터 전처리, 훈련 인프라 구성, 하이퍼파라미터 튜닝, 배포 환경 설정 등 수많은 단계를 거쳐야 합니다. SageMaker JumpStart는 이러한 복잡성을 대폭 줄여주며, 클릭 몇 번 또는 몇 줄의 코드만으로 최신 ML 모델을 배포하고 파인튜닝할 수 있는 환경을 제공합니다.

2024년 기준으로 JumpStart는 Hugging Face, Meta(LLaMA), Stability AI, AI21 Labs 등 다양한 모델 제공자의 600개 이상의 사전 훈련 모델을 지원하며, 자연어 처리(NLP), 컴퓨터 비전(CV), 테이블 데이터 분석, 생성형 AI 등 광범위한 ML 태스크를 커버합니다.

## 핵심 기능

### 1. 파운데이션 모델 허브

JumpStart의 가장 핵심적인 기능은 파운데이션 모델 허브입니다. 대규모 언어 모델(LLM)부터 이미지 생성 모델까지 다양한 최신 모델을 원클릭으로 배포할 수 있습니다.

지원되는 주요 모델 카테고리는 다음과 같습니다.

- **텍스트 생성**: Meta LLaMA 2/3, Falcon, Mistral, AI21 Jurassic
- **텍스트 임베딩**: BGE, GTE, Cohere Embed
- **이미지 생성**: Stable Diffusion XL, SDXL Turbo
- **멀티모달**: LLaVA, IDEFICS
- **음성 인식**: Whisper

AWS CLI를 통해 사용 가능한 JumpStart 모델 목록을 조회할 수 있습니다.

```bash
# JumpStart에서 사용 가능한 모델 사양 목록 조회
aws sagemaker list-model-packages \
  --model-package-group-name "jumpstart-dft-" \
  --region us-east-1 \
  --output json

# 특정 모델 패키지의 상세 정보 확인
aws sagemaker describe-model-package \
  --model-package-name "arn:aws:sagemaker:us-east-1:123456789012:model-package/jumpstart-model-example" \
  --region us-east-1
```

### 2. 원클릭 배포(One-Click Deploy)

SageMaker Studio UI에서 모델을 선택하고 "Deploy" 버튼을 클릭하면, 적절한 인스턴스 타입과 컨테이너 이미지가 자동으로 선택되어 실시간 추론 엔드포인트가 생성됩니다. SDK를 사용한 프로그래밍 방식의 배포도 지원합니다.

```python
from sagemaker.jumpstart.model import JumpStartModel

# Meta LLaMA 2 7B 모델 배포
model = JumpStartModel(
    model_id="meta-textgeneration-llama-2-7b-f",
    instance_type="ml.g5.2xlarge",
    role="arn:aws:iam::123456789012:role/SageMakerRole"
)

predictor = model.deploy(
    initial_instance_count=1,
    endpoint_name="llama-2-7b-endpoint"
)

# 추론 테스트
response = predictor.predict({
    "inputs": "AWS SageMaker JumpStart는",
    "parameters": {
        "max_new_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.9
    }
})
print(response)
```

### 3. 파인튜닝(Fine-Tuning)

JumpStart는 사전 훈련 모델에 대한 전이 학습(Transfer Learning)과 도메인 적응(Domain Adaptation)을 손쉽게 수행할 수 있는 파인튜닝 기능을 제공합니다.

```python
from sagemaker.jumpstart.estimator import JumpStartEstimator

# 파인튜닝 작업 설정
estimator = JumpStartEstimator(
    model_id="meta-textgeneration-llama-2-7b-f",
    instance_type="ml.g5.12xlarge",
    instance_count=1,
    role="arn:aws:iam::123456789012:role/SageMakerRole",
    hyperparameters={
        "epoch": "3",
        "learning_rate": "2e-5",
        "per_device_train_batch_size": "4",
        "instruction_tuned": "True"
    }
)

# S3에 업로드된 훈련 데이터로 파인튜닝 시작
estimator.fit({
    "training": "s3://my-bucket/training-data/"
})

# 파인튜닝된 모델 배포
predictor = estimator.deploy(
    initial_instance_count=1,
    instance_type="ml.g5.2xlarge"
)
```

### 4. 솔루션 템플릿

JumpStart는 특정 비즈니스 문제를 해결하기 위한 엔드투엔드 솔루션 템플릿을 제공합니다. 이 템플릿에는 데이터 준비, 모델 훈련, 배포, 모니터링에 이르는 전체 파이프라인이 포함되어 있습니다.

주요 솔루션 템플릿은 다음과 같습니다.

- **수요 예측(Demand Forecasting)**: 시계열 데이터 기반 수요 예측 파이프라인
- **사기 탐지(Fraud Detection)**: 트랜잭션 데이터 기반 이상 탐지 워크플로
- **문서 이해(Document Understanding)**: 비정형 문서에서 정보 추출
- **추천 시스템(Personalized Recommendations)**: 사용자 행동 데이터 기반 추천 엔진

### 5. 모델 평가(Model Evaluation)

JumpStart는 배포 전 모델 성능을 평가할 수 있는 내장 평가 도구를 제공합니다. 다양한 벤치마크 데이터셋에 대한 성능 메트릭을 확인하고, 여러 모델 간 비교 분석이 가능합니다.

```bash
# SageMaker 엔드포인트 상태 확인
aws sagemaker describe-endpoint \
  --endpoint-name "llama-2-7b-endpoint" \
  --region us-east-1 \
  --query '{EndpointStatus: EndpointStatus, InstanceType: ProductionVariants[0].InstanceType}'
```

## 아키텍처/동작 원리

### JumpStart 내부 아키텍처

JumpStart의 동작 원리는 다음과 같은 계층 구조로 이루어져 있습니다.

1. **모델 레지스트리 계층**: AWS가 관리하는 S3 버킷에 사전 훈련 모델 아티팩트가 저장되어 있습니다. 모델 메타데이터(지원 인스턴스 타입, 컨테이너 이미지, 하이퍼파라미터 기본값 등)는 JumpStart 카탈로그에서 관리됩니다.

2. **컨테이너 계층**: 각 모델에 최적화된 추론/훈련 컨테이너 이미지가 ECR(Elastic Container Registry)에 준비되어 있습니다. Deep Learning Containers(DLC)를 기반으로 하며, 모델 서빙 프레임워크(TGI, DJL, Triton 등)가 사전 구성되어 있습니다.

3. **인프라 계층**: SageMaker의 관리형 인프라 위에서 모델이 실행됩니다. GPU 인스턴스(ml.g5, ml.p4d, ml.p5 등)가 자동으로 프로비저닝되며, 로드 밸런싱과 오토스케일링이 적용됩니다.

4. **API 계층**: SageMaker Python SDK와 REST API를 통해 프로그래밍 방식으로 모델을 관리할 수 있습니다.

### 모델 배포 흐름

모델 배포 시 내부적으로 다음 과정이 진행됩니다.

1. JumpStart 카탈로그에서 모델 메타데이터를 조회합니다.
2. 모델 아티팩트를 AWS 관리 S3 버킷에서 사용자 계정의 S3 버킷으로 복사합니다.
3. 적절한 DLC 컨테이너 이미지를 선택합니다.
4. SageMaker Model 객체를 생성합니다.
5. SageMaker Endpoint Configuration을 생성합니다.
6. SageMaker Endpoint를 생성하고 모델을 로드합니다.

```bash
# 배포된 JumpStart 모델의 엔드포인트 설정 확인
aws sagemaker describe-endpoint-config \
  --endpoint-config-name "llama-2-7b-endpoint-config" \
  --region us-east-1 \
  --output json

# 모델 아티팩트 위치 확인
aws sagemaker describe-model \
  --model-name "jumpstart-llama-2-7b-model" \
  --region us-east-1 \
  --query 'PrimaryContainer.{Image: Image, ModelDataUrl: ModelDataUrl}'
```

### 파인튜닝 동작 원리

파인튜닝 시에는 다음과 같은 과정이 진행됩니다.

1. 사용자가 제공한 훈련 데이터를 S3에서 훈련 인스턴스로 다운로드합니다.
2. 사전 훈련 모델의 가중치를 로드합니다.
3. LoRA(Low-Rank Adaptation) 또는 전체 파라미터 파인튜닝을 수행합니다.
4. 체크포인트와 최종 모델 아티팩트를 S3에 저장합니다.

JumpStart는 기본적으로 QLoRA(Quantized LoRA)를 사용하여 메모리 효율적인 파인튜닝을 지원하며, 이를 통해 7B 파라미터 모델도 단일 GPU에서 파인튜닝할 수 있습니다.

## 실전 활용

### 사례 1: RAG(Retrieval-Augmented Generation) 파이프라인 구축

JumpStart의 LLM과 임베딩 모델을 활용하여 RAG 파이프라인을 구축하는 방법입니다.

```python
from sagemaker.jumpstart.model import JumpStartModel
import json

# 임베딩 모델 배포
embed_model = JumpStartModel(
    model_id="huggingface-sentencesimilarity-bge-large-en",
    instance_type="ml.g5.xlarge"
)
embed_predictor = embed_model.deploy()

# LLM 배포
llm_model = JumpStartModel(
    model_id="meta-textgeneration-llama-2-13b-f",
    instance_type="ml.g5.12xlarge"
)
llm_predictor = llm_model.deploy()

# RAG 쿼리 실행
def rag_query(question, context_docs):
    # 컨텍스트와 질문을 결합한 프롬프트 생성
    context = "\n".join(context_docs)
    prompt = f"""다음 컨텍스트를 바탕으로 질문에 답변하십시오.

컨텍스트:
{context}

질문: {question}
답변:"""
    
    response = llm_predictor.predict({
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.3
        }
    })
    return response
```

### 사례 2: 이미지 분류 모델 파인튜닝

사전 훈련된 ResNet 모델을 커스텀 데이터셋으로 파인튜닝하는 예시입니다.

```python
from sagemaker.jumpstart.estimator import JumpStartEstimator

# 이미지 분류 모델 파인튜닝
estimator = JumpStartEstimator(
    model_id="pytorch-ic-resnet50",
    instance_type="ml.p3.2xlarge",
    hyperparameters={
        "epochs": "10",
        "batch-size": "32",
        "learning-rate": "0.001",
        "optimizer": "adam"
    }
)

estimator.fit({
    "training": "s3://my-bucket/image-classification/train/",
    "validation": "s3://my-bucket/image-classification/val/"
})

# 파인튜닝 완료 후 배포
predictor = estimator.deploy(
    initial_instance_count=1,
    instance_type="ml.m5.xlarge"
)
```

### 사례 3: 대규모 모델의 비용 최적화 배포

대규모 모델을 비용 효율적으로 배포하기 위한 전략입니다.

```python
from sagemaker.jumpstart.model import JumpStartModel

# 양자화된 모델 사용으로 비용 절감
model = JumpStartModel(
    model_id="meta-textgeneration-llama-2-7b-f",
    instance_type="ml.g5.2xlarge",
    env={
        "OPTION_QUANTIZE": "bitsandbytes8",  # 8비트 양자화
        "OPTION_MAX_ROLLING_BATCH_SIZE": "4",
        "OPTION_TENSOR_PARALLEL_DEGREE": "1"
    }
)

predictor = model.deploy(
    initial_instance_count=1,
    endpoint_name="llama-2-7b-quantized"
)
```

```bash
# 엔드포인트 오토스케일링 설정
aws application-autoscaling register-scalable-target \
  --service-namespace sagemaker \
  --resource-id "endpoint/llama-2-7b-quantized/variant/AllTraffic" \
  --scalable-dimension "sagemaker:variant:DesiredInstanceCount" \
  --min-capacity 1 \
  --max-capacity 3

# 스케일링 정책 적용 (평균 GPU 사용률 60% 기준)
aws application-autoscaling put-scaling-policy \
  --service-namespace sagemaker \
  --resource-id "endpoint/llama-2-7b-quantized/variant/AllTraffic" \
  --scalable-dimension "sagemaker:variant:DesiredInstanceCount" \
  --policy-name "gpu-utilization-scaling" \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 60.0,
    "CustomizedMetricSpecification": {
      "MetricName": "GPUUtilization",
      "Namespace": "aws/sagemaker",
      "Dimensions": [{"Name": "EndpointName", "Value": "llama-2-7b-quantized"}],
      "Statistic": "Average"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'
```

## 모범 사례/보안

### 보안 모범 사례

1. **IAM 최소 권한 원칙**: JumpStart 모델에 접근하는 역할에는 필요한 최소한의 권한만 부여합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateModel",
        "sagemaker:CreateEndpointConfig",
        "sagemaker:CreateEndpoint",
        "sagemaker:InvokeEndpoint"
      ],
      "Resource": "arn:aws:sagemaker:us-east-1:123456789012:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-sagemaker-bucket/*"
    }
  ]
}
```

2. **VPC 격리**: 추론 엔드포인트를 VPC 내에 배포하여 네트워크 수준의 격리를 확보합니다.

3. **데이터 암호화**: 모델 아티팩트와 추론 데이터는 AWS KMS를 사용하여 저장 시(at rest) 및 전송 시(in transit) 암호화합니다.

4. **엔드포인트 접근 제어**: VPC 엔드포인트(PrivateLink)를 통해 인터넷을 거치지 않고 SageMaker API에 접근합니다.

### 비용 최적화 모범 사례

1. **적절한 인스턴스 선택**: 모델 크기에 맞는 인스턴스를 선택합니다. 7B 모델은 ml.g5.2xlarge, 13B 모델은 ml.g5.12xlarge, 70B 모델은 ml.p4d.24xlarge가 일반적입니다.

2. **양자화 적용**: 프로덕션 환경에서 허용 가능한 품질 저하 범위 내에서 8비트 또는 4비트 양자화를 적용합니다.

3. **오토스케일링 설정**: 트래픽 패턴에 따라 인스턴스 수를 자동으로 조절합니다.

4. **Savings Plans 활용**: 장기적으로 사용할 엔드포인트에는 SageMaker Savings Plans를 적용하여 최대 64%의 비용을 절감합니다.

5. **사용하지 않는 엔드포인트 정리**: 개발/테스트 환경의 엔드포인트는 사용하지 않을 때 삭제합니다.

```bash
# 실행 중인 모든 JumpStart 엔드포인트 목록 확인
aws sagemaker list-endpoints \
  --status-equals "InService" \
  --region us-east-1 \
  --query 'Endpoints[?contains(EndpointName, `jumpstart`)].{Name: EndpointName, Created: CreationTime}' \
  --output table

# 사용하지 않는 엔드포인트 삭제
aws sagemaker delete-endpoint \
  --endpoint-name "jumpstart-unused-endpoint" \
  --region us-east-1
```

### 운영 모범 사례

1. **모델 버전 관리**: SageMaker Model Registry와 연동하여 모델 버전을 체계적으로 관리합니다.
2. **CloudWatch 모니터링**: 엔드포인트의 지연 시간, 처리량, 오류율을 지속적으로 모니터링합니다.
3. **A/B 테스트**: 프로덕션 변형(Production Variants)을 활용하여 새 모델과 기존 모델을 비교합니다.
4. **Shadow 테스트**: 새 모델을 프로덕션에 배포하기 전에 Shadow 모드로 실제 트래픽을 미러링하여 테스트합니다.

## 관련 서비스 비교

### JumpStart vs Amazon Bedrock

| 항목 | SageMaker JumpStart | Amazon Bedrock |
|------|-------------------|----------------|
| 모델 커스터마이징 | 전체 파인튜닝/LoRA 지원 | 제한적 커스터마이징 |
| 인프라 관리 | 사용자가 인스턴스 타입 선택 | 완전 관리형(서버리스) |
| 모델 선택 | 600+ 오픈소스 모델 | 선별된 파운데이션 모델 |
| 가격 모델 | 인스턴스 기반 시간당 과금 | 토큰/이미지 기반 과금 |
| 제어 수준 | 높음(컨테이너, 환경변수 등) | 낮음(API 기반) |
| 적합한 사용 사례 | 커스텀 모델/파인튜닝 필요 시 | 빠른 프로토타이핑, API 기반 통합 |

### JumpStart vs Hugging Face on SageMaker

| 항목 | JumpStart | Hugging Face DLC |
|------|-----------|------------------|
| 설정 편의성 | 원클릭 배포 | 코드 기반 설정 필요 |
| 모델 범위 | AWS 검증 모델 | Hugging Face Hub 전체 |
| 최적화 | AWS 최적화 적용 | 사용자 직접 최적화 |
| 컨테이너 | 자동 선택 | 수동 선택 가능 |

### JumpStart vs 자체 모델 학습

| 항목 | JumpStart | 자체 학습 |
|------|-----------|----------|
| 초기 비용 | 낮음 | 높음(데이터 수집, GPU 비용) |
| 시간 투자 | 수분~수시간 | 수주~수개월 |
| 성능 최적화 | 제한적 | 완전한 제어 |
| 모델 소유권 | 라이선스에 따름 | 완전 소유 |

## 요약

Amazon SageMaker JumpStart는 ML 워크플로를 획기적으로 단순화하는 강력한 도구입니다. 사전 훈련된 파운데이션 모델의 원클릭 배포, 효율적인 파인튜닝, 그리고 엔드투엔드 솔루션 템플릿을 통해 ML 프로젝트의 시작 단계에서 프로덕션 배포까지의 시간을 대폭 단축할 수 있습니다.

핵심 요점을 정리하면 다음과 같습니다.

- JumpStart는 600개 이상의 사전 훈련 모델을 제공하며, LLM부터 CV 모델까지 광범위한 태스크를 지원합니다.
- 원클릭 배포와 SDK 기반 프로그래밍 방식 모두 지원하여 유연한 워크플로를 구성할 수 있습니다.
- LoRA/QLoRA 기반의 메모리 효율적 파인튜닝으로 커스텀 도메인 적응이 가능합니다.
- 양자화, 오토스케일링, 적절한 인스턴스 선택을 통해 비용을 최적화할 수 있습니다.
- IAM, VPC, KMS 등 AWS 보안 서비스와 긴밀하게 통합되어 엔터프라이즈급 보안을 확보할 수 있습니다.
- 빠른 프로토타이핑이 필요한 경우 Bedrock을, 깊은 커스터마이징이 필요한 경우 JumpStart를 선택하는 것이 적절합니다.

JumpStart는 특히 ML 전문 인력이 제한적인 조직이나, 빠르게 ML 기반 프로덕트를 출시해야 하는 스타트업에 매우 유용한 서비스입니다. 다만, 대규모 프로덕션 환경에서는 모델 모니터링, 버전 관리, CI/CD 파이프라인 등 MLOps 관련 서비스들과 함께 사용하는 것을 권장합니다.