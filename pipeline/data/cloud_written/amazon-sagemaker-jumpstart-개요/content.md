<!-- infographic-hero -->
![Amazon SageMaker JumpStart 개요 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker JumpStart 개요 한 장 요약 인포그래픽*

# Amazon SageMaker JumpStart 개요

## 개요

Amazon SageMaker JumpStart는 AWS의 완전 관리형 머신러닝 플랫폼인 SageMaker의 핵심 구성 요소로, 사전 훈련된 모델과 솔루션을 활용하여 ML 프로젝트를 빠르게 시작할 수 있도록 설계된 서비스입니다. 이 글에서는 JumpStart의 전체적인 구조와 주요 개념을 살펴보고, 처음 사용자가 알아야 할 핵심 사항을 체계적으로 정리합니다.

머신러닝 프로젝트를 처음 시작할 때 가장 큰 진입 장벽은 모델 선택, 인프라 구성, 데이터 파이프라인 설계 등 기술적 복잡성입니다. JumpStart는 이 진입 장벽을 낮추기 위해 다음 세 가지 핵심 구성 요소를 제공합니다.

- **모델 허브(Model Hub)**: 수백 개의 사전 훈련 모델을 탐색, 배포, 파인튜닝할 수 있는 카탈로그입니다.
- **솔루션 템플릿(Solution Templates)**: 특정 비즈니스 문제를 해결하기 위한 엔드투엔드 ML 파이프라인입니다.
- **예제 노트북(Example Notebooks)**: 각 모델과 솔루션의 사용법을 단계별로 설명하는 Jupyter 노트북입니다.

JumpStart는 SageMaker Studio 또는 SageMaker Python SDK를 통해 접근할 수 있으며, 모든 기능은 프로그래밍 방식으로도 사용할 수 있어 MLOps 파이프라인에 통합하기에 적합합니다.

## 핵심 기능

### 1. 모델 카탈로그 구조

JumpStart의 모델 카탈로그는 다음과 같은 카테고리로 구성되어 있습니다.

**태스크 기반 분류**:
- **텍스트 생성(Text Generation)**: GPT 계열, LLaMA, Falcon, Mistral 등
- **텍스트 분류(Text Classification)**: BERT, RoBERTa, DistilBERT 등
- **질의응답(Question Answering)**: 추출형/생성형 QA 모델
- **번역(Translation)**: MarianMT, NLLB 등
- **요약(Summarization)**: BART, T5, Pegasus 등
- **이미지 분류(Image Classification)**: ResNet, EfficientNet, ViT 등
- **객체 탐지(Object Detection)**: YOLO, DETR, SSD 등
- **이미지 생성(Image Generation)**: Stable Diffusion, SDXL 등
- **임베딩(Embedding)**: BGE, GTE, Sentence-BERT 등
- **테이블 데이터(Tabular)**: XGBoost, LightGBM, CatBoost, AutoGluon 등

**모델 제공자 기반 분류**:
- Hugging Face
- Meta (LLaMA 계열)
- Stability AI (Stable Diffusion 계열)
- AI21 Labs (Jurassic 계열)
- Cohere
- LightOn

```bash
# SageMaker에서 사용 가능한 JumpStart 모델 ID 목록을 Python으로 조회
# (AWS CLI와 함께 사용하는 스크립트)
aws sagemaker list-model-packages \
  --model-approval-status Approved \
  --region us-east-1 \
  --max-results 20 \
  --output table
```

### 2. 모델 메타데이터 시스템

각 JumpStart 모델에는 다음과 같은 메타데이터가 포함되어 있습니다.

- **모델 ID**: 고유 식별자 (예: `meta-textgeneration-llama-2-7b-f`)
- **모델 버전**: 시맨틱 버전 관리
- **지원 인스턴스 타입**: 추론/훈련별 권장 인스턴스 목록
- **컨테이너 이미지**: 모델 서빙을 위한 Docker 이미지 URI
- **하이퍼파라미터**: 훈련 시 조정 가능한 파라미터와 기본값
- **라이선스 정보**: 모델 사용 라이선스(Apache 2.0, LLaMA License 등)
- **데이터 형식**: 입출력 데이터의 형식 사양

```python
from sagemaker.jumpstart.notebook_utils import list_jumpstart_models

# 텍스트 생성 모델 목록 조회
text_gen_models = list_jumpstart_models(
    filter_domain="NATURAL_LANGUAGE_PROCESSING",
    filter_task="TEXT_GENERATION"
)

for model_id in text_gen_models[:10]:
    print(f"Model ID: {model_id}")
```

### 3. 접근 방식

JumpStart에 접근하는 방법은 크게 세 가지입니다.

**방법 1: SageMaker Studio UI**

SageMaker Studio의 왼쪽 네비게이션 패널에서 "JumpStart" 메뉴를 통해 시각적으로 모델을 탐색하고 배포할 수 있습니다. 코드 작성 없이 마우스 클릭만으로 모델을 배포할 수 있어 가장 접근성이 높은 방법입니다.

**방법 2: SageMaker Python SDK**

프로그래밍 방식으로 모델을 관리할 수 있어, CI/CD 파이프라인이나 자동화 스크립트에 적합합니다.

```python
from sagemaker.jumpstart.model import JumpStartModel

# 모델 객체 생성 (배포 전 설정 확인)
model = JumpStartModel(
    model_id="huggingface-text2text-flan-t5-xl",
    role="arn:aws:iam::123456789012:role/SageMakerRole"
)

# 배포 가능한 인스턴스 타입 확인
print(f"기본 인스턴스: {model.instance_type}")
print(f"모델 데이터: {model.model_data}")
```

**방법 3: AWS CLI / boto3**

기존 AWS 인프라 자동화 도구와의 통합에 적합합니다.

```bash
# SageMaker 도메인 내 JumpStart 관련 리소스 조회
aws sagemaker list-models \
  --name-contains "jumpstart" \
  --region us-east-1 \
  --sort-by CreationTime \
  --sort-order Descending \
  --max-results 10 \
  --output table
```

### 4. 사전 요구 사항

JumpStart를 사용하기 위한 사전 요구 사항은 다음과 같습니다.

- **AWS 계정**: 활성화된 AWS 계정이 필요합니다.
- **SageMaker 도메인**: SageMaker Studio를 사용하려면 SageMaker 도메인이 설정되어 있어야 합니다.
- **IAM 역할**: SageMaker 실행 역할에 필요한 권한이 부여되어야 합니다.
- **서비스 할당량**: GPU 인스턴스(ml.g5, ml.p3, ml.p4d 등)에 대한 서비스 할당량이 충분해야 합니다.
- **S3 버킷**: 모델 아티팩트와 훈련 데이터를 저장할 S3 버킷이 필요합니다.

```bash
# SageMaker 도메인 생성 상태 확인
aws sagemaker list-domains \
  --region us-east-1 \
  --output json

# GPU 인스턴스 할당량 확인 (ml.g5.xlarge 기준)
aws service-quotas get-service-quota \
  --service-code sagemaker \
  --quota-code "L-5765E346" \
  --region us-east-1
```

## 아키텍처/동작 원리

### JumpStart 서비스 아키텍처

JumpStart는 내부적으로 다음과 같은 아키텍처로 구성됩니다.

**1단계 - 카탈로그 서비스**

JumpStart 카탈로그는 AWS가 관리하는 중앙화된 모델 레지스트리입니다. 각 모델의 메타데이터, 지원 리전, 인스턴스 타입 호환성 정보가 이 카탈로그에 저장되어 있습니다. SageMaker SDK는 이 카탈로그에서 모델 정보를 조회하여 배포 또는 훈련에 필요한 설정을 자동으로 구성합니다.

**2단계 - 모델 아티팩트 저장소**

AWS가 관리하는 S3 버킷에 사전 훈련 모델의 가중치 파일이 저장되어 있습니다. 모델 배포 시 이 아티팩트가 사용자의 SageMaker 인스턴스로 다운로드됩니다. 대규모 모델(70B+ 파라미터)의 경우 수십 GB에 달하는 아티팩트를 효율적으로 전송하기 위해 S3 가속 전송이 사용됩니다.

**3단계 - 컨테이너 레지스트리**

각 모델에 최적화된 서빙 컨테이너 이미지가 ECR에 저장되어 있습니다. 주요 서빙 프레임워크는 다음과 같습니다.

- **HuggingFace TGI(Text Generation Inference)**: 텍스트 생성 모델에 최적화
- **DJL(Deep Java Library) Serving**: 대규모 모델의 분산 추론 지원
- **Triton Inference Server**: 멀티프레임워크 지원, 배치 처리 최적화
- **MMS(Multi Model Server)**: 경량 모델 서빙

**4단계 - SageMaker 인프라**

모델이 실제로 실행되는 관리형 인프라 계층입니다. EC2 인스턴스 프로비저닝, 컨테이너 실행, 로드 밸런싱, 헬스 체크, 오토스케일링 등을 SageMaker가 자동으로 관리합니다.

### 모델 선택 의사결정 트리

적절한 JumpStart 모델을 선택하기 위한 의사결정 과정은 다음과 같습니다.

1. **태스크 정의**: 해결하고자 하는 ML 태스크를 명확히 합니다 (분류, 생성, 탐지 등).
2. **데이터 유형 확인**: 입력 데이터의 유형을 확인합니다 (텍스트, 이미지, 테이블 등).
3. **성능 요구사항**: 지연 시간, 처리량, 정확도 요구사항을 정의합니다.
4. **비용 제약**: 사용 가능한 예산과 인스턴스 유형을 결정합니다.
5. **라이선스 확인**: 상용 사용 가능 여부를 확인합니다.

## 실전 활용

### 시작하기: 첫 번째 JumpStart 모델 배포

처음 JumpStart를 사용하는 사용자를 위한 단계별 가이드입니다.

**1단계: 환경 설정**

```bash
# SageMaker Python SDK 설치/업데이트
pip install --upgrade sagemaker boto3

# 현재 SageMaker SDK 버전 확인
python -c "import sagemaker; print(sagemaker.__version__)"
```

**2단계: 모델 탐색**

```python
from sagemaker.jumpstart.notebook_utils import (
    list_jumpstart_models,
    get_jumpstart_content_bucket
)

# 사용 가능한 모든 모델 태스크 확인
all_models = list_jumpstart_models()
print(f"총 모델 수: {len(all_models)}")

# 텍스트 생성 모델만 필터링
text_gen = list_jumpstart_models(
    filter_domain="NATURAL_LANGUAGE_PROCESSING",
    filter_task="TEXT_GENERATION"
)
print(f"텍스트 생성 모델 수: {len(text_gen)}")

# 콘텐츠 버킷 확인
bucket = get_jumpstart_content_bucket()
print(f"JumpStart 콘텐츠 버킷: {bucket}")
```

**3단계: 모델 배포**

```python
import sagemaker
from sagemaker.jumpstart.model import JumpStartModel

# 세션 설정
session = sagemaker.Session()
role = sagemaker.get_execution_role()

# Flan-T5 XL 모델 배포 (범용 텍스트 생성)
model = JumpStartModel(
    model_id="huggingface-text2text-flan-t5-xl",
    role=role
)

predictor = model.deploy(
    initial_instance_count=1,
    endpoint_name="flan-t5-xl-quickstart"
)

# 추론 테스트
response = predictor.predict({
    "inputs": "Translate to Korean: Machine learning is transforming every industry."
})
print(response)
```

**4단계: 리소스 정리**

```python
# 엔드포인트 삭제 (비용 절감)
predictor.delete_endpoint()
predictor.delete_model()
```

```bash
# CLI로 엔드포인트 삭제 확인
aws sagemaker describe-endpoint \
  --endpoint-name "flan-t5-xl-quickstart" \
  --region us-east-1 2>&1 || echo "엔드포인트가 성공적으로 삭제되었습니다."
```

### 모델 비교 실습

동일한 태스크에 대해 여러 모델을 비교하는 방법입니다.

```python
from sagemaker.jumpstart.model import JumpStartModel
import time

# 비교할 모델 목록
models_to_compare = [
    {"id": "huggingface-text2text-flan-t5-base", "instance": "ml.g5.xlarge"},
    {"id": "huggingface-text2text-flan-t5-xl", "instance": "ml.g5.2xlarge"},
    {"id": "huggingface-text2text-flan-t5-xxl", "instance": "ml.g5.12xlarge"}
]

test_prompt = "Summarize: Amazon SageMaker is a fully managed machine learning service that provides every developer and data scientist with the ability to build, train, and deploy machine learning models quickly."

results = []
for model_info in models_to_compare:
    model = JumpStartModel(
        model_id=model_info["id"],
        instance_type=model_info["instance"]
    )
    predictor = model.deploy()
    
    start = time.time()
    response = predictor.predict({"inputs": test_prompt})
    latency = time.time() - start
    
    results.append({
        "model": model_info["id"],
        "latency_ms": round(latency * 1000, 2),
        "response": response
    })
    
    predictor.delete_endpoint()
    predictor.delete_model()

# 결과 비교
for r in results:
    print(f"모델: {r['model']}")
    print(f"지연시간: {r['latency_ms']}ms")
    print(f"응답: {r['response']}")
    print("---")
```

### JumpStart와 SageMaker Pipelines 통합

JumpStart 모델을 SageMaker Pipelines에 통합하여 자동화된 ML 워크플로를 구축할 수 있습니다.

```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import TrainingStep
from sagemaker.jumpstart.estimator import JumpStartEstimator

# JumpStart 기반 훈련 단계 정의
estimator = JumpStartEstimator(
    model_id="huggingface-text2text-flan-t5-base",
    instance_type="ml.g5.2xlarge",
    hyperparameters={
        "epochs": "5",
        "learning_rate": "1e-5"
    }
)

training_step = TrainingStep(
    name="JumpStartFineTuning",
    estimator=estimator,
    inputs={
        "training": "s3://my-bucket/data/train/"
    }
)

pipeline = Pipeline(
    name="JumpStartPipeline",
    steps=[training_step]
)

pipeline.upsert(role_arn=role)
pipeline.start()
```

## 모범 사례/보안

### 시작 단계의 모범 사례

1. **소규모로 시작**: 처음에는 작은 모델(Base, Small)로 시작하여 워크플로를 검증한 후, 점진적으로 큰 모델로 전환합니다.

2. **할당량 사전 확인**: GPU 인스턴스에 대한 서비스 할당량을 미리 확인하고, 필요한 경우 증가를 요청합니다.

```bash
# 현재 SageMaker 엔드포인트 인스턴스 할당량 조회
aws service-quotas list-service-quotas \
  --service-code sagemaker \
  --region us-east-1 \
  --query 'Quotas[?contains(QuotaName, `endpoint`)].{Name: QuotaName, Value: Value}' \
  --output table

# 할당량 증가 요청
aws service-quotas request-service-quota-increase \
  --service-code sagemaker \
  --quota-code "L-5765E346" \
  --desired-value 8 \
  --region us-east-1
```

3. **비용 경고 설정**: CloudWatch 알림을 설정하여 예상치 못한 비용 발생을 방지합니다.

4. **태그 관리**: 모든 JumpStart 리소스에 태그를 부여하여 비용 추적과 리소스 관리를 용이하게 합니다.

### 보안 설정 체크리스트

- IAM 역할에 최소 권한 원칙을 적용했는지 확인합니다.
- 모델 엔드포인트가 VPC 내에서만 접근 가능하도록 설정합니다.
- S3 버킷의 모델 아티팩트에 대한 접근 권한을 제한합니다.
- CloudTrail을 활성화하여 API 호출을 감사합니다.
- KMS 키를 사용하여 모델 아티팩트와 추론 데이터를 암호화합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "JumpStartMinimalAccess",
      "Effect": "Allow",
      "Action": [
        "sagemaker:ListModels",
        "sagemaker:DescribeModel",
        "sagemaker:CreateModel",
        "sagemaker:CreateEndpointConfig",
        "sagemaker:CreateEndpoint",
        "sagemaker:DescribeEndpoint",
        "sagemaker:InvokeEndpoint",
        "sagemaker:DeleteEndpoint",
        "sagemaker:DeleteEndpointConfig",
        "sagemaker:DeleteModel"
      ],
      "Resource": "arn:aws:sagemaker:us-east-1:123456789012:*"
    }
  ]
}
```

## 관련 서비스 비교

### JumpStart 접근 방식 비교

| 접근 방식 | 장점 | 단점 | 적합한 사용 사례 |
|----------|------|------|----------------|
| Studio UI | 코드 불필요, 직관적 | 자동화 어려움 | 탐색, 프로토타이핑 |
| Python SDK | 유연함, 자동화 가능 | 코드 작성 필요 | MLOps, 파이프라인 |
| AWS CLI/boto3 | 인프라 통합 용이 | 모델 세부 설정 제한적 | 인프라 자동화 |

### JumpStart vs SageMaker Built-in Algorithms

| 항목 | JumpStart | Built-in Algorithms |
|------|-----------|--------------------|
| 모델 범위 | 외부 모델 포함 (Hugging Face 등) | AWS 자체 알고리즘 |
| 사전 훈련 | 대부분 사전 훈련됨 | 사전 훈련 없음 (처음부터 학습) |
| 커스터마이징 | 파인튜닝 | 전체 학습 |
| 데이터 요구량 | 적음 (전이 학습) | 많음 (처음부터 학습) |
| 모델 크기 | 대형 모델 포함 | 중소형 |

### JumpStart vs Amazon Bedrock 선택 가이드

**JumpStart를 선택해야 하는 경우**:
- 모델을 직접 파인튜닝해야 하는 경우
- GPU 인스턴스 타입을 세밀하게 제어해야 하는 경우
- 오픈소스 모델을 사용해야 하는 경우
- 커스텀 추론 로직이 필요한 경우

**Bedrock을 선택해야 하는 경우**:
- 인프라 관리 없이 API만으로 사용하고 싶은 경우
- 토큰 기반 종량제 과금이 유리한 경우
- 빠른 프로토타이핑이 목적인 경우
- Anthropic Claude, Amazon Titan 등 특정 모델이 필요한 경우

## 요약

Amazon SageMaker JumpStart는 ML 프로젝트의 시작점을 크게 낮춰주는 핵심 서비스입니다. 이 글에서 다룬 주요 내용을 정리하면 다음과 같습니다.

- JumpStart는 모델 허브, 솔루션 템플릿, 예제 노트북의 세 가지 핵심 구성 요소로 이루어져 있습니다.
- 600개 이상의 사전 훈련 모델을 NLP, CV, 테이블 데이터 등 다양한 카테고리에서 제공합니다.
- Studio UI, Python SDK, AWS CLI 세 가지 방식으로 접근할 수 있으며, 각각의 장단점이 있습니다.
- 내부적으로 카탈로그 서비스, 모델 아티팩트 저장소, 컨테이너 레지스트리, SageMaker 인프라의 4계층 구조로 동작합니다.
- 처음 사용 시에는 소규모 모델로 시작하여 워크플로를 검증하고, 할당량과 비용을 사전에 확인하는 것이 중요합니다.
- 보안 측면에서는 IAM 최소 권한, VPC 격리, 데이터 암호화, CloudTrail 감사가 필수적입니다.
- 파인튜닝이 필요한 경우 JumpStart를, API 기반 간편 사용이 필요한 경우 Bedrock을 선택하는 것이 적절합니다.

JumpStart는 특히 ML 경험이 적은 팀이 빠르게 프로토타입을 만들고 검증하는 데 매우 효과적이며, 경험이 풍부한 ML 엔지니어에게도 생산성을 높이는 도구로 활용됩니다. 다음 단계로는 실제 프로젝트에서 JumpStart 모델을 배포하고 파인튜닝하는 심화 과정을 진행하는 것을 권장합니다.