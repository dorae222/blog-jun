<!-- infographic-hero -->
![Amazon SageMaker AI 개요: 엔드투엔드 ML 플랫폼의 모든 것 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker AI 개요: 엔드투엔드 ML 플랫폼의 모든 것 한 장 요약 인포그래픽*

# Amazon SageMaker AI 개요: 엔드투엔드 ML 플랫폼의 모든 것

## 개요

Amazon SageMaker는 AWS의 머신러닝 전용 플랫폼으로, 데이터 준비부터 모델 훈련, 튜닝, 배포, 모니터링까지 ML 라이프사이클의 모든 단계를 통합적으로 지원합니다. 2017년 re:Invent에서 처음 발표된 이후 지속적으로 기능이 확장되어, 현재는 30개 이상의 하위 서비스와 기능을 포괄하는 거대한 ML 에코시스템이 되었습니다.

2024년 re:Invent에서 AWS는 SageMaker의 차세대 버전인 **SageMaker AI**를 발표했습니다. 기존 SageMaker의 모든 기능을 포함하면서, 생성형 AI 시대에 맞춰 대규모 언어 모델(LLM) 훈련 및 배포, 모델 평가, 거버넌스 기능이 대폭 강화되었습니다. 또한 Amazon SageMaker Unified Studio를 통해 데이터 분석, ML 개발, 생성형 AI 애플리케이션 개발을 하나의 통합 환경에서 수행할 수 있게 되었습니다.

이 글에서는 SageMaker AI의 전체 구조를 조망하고, 각 구성 요소가 어떤 역할을 하며 어떻게 연결되는지를 체계적으로 정리합니다.

## 핵심 기능

SageMaker AI의 기능은 ML 라이프사이클의 각 단계에 따라 분류할 수 있습니다.

### 1단계: 데이터 준비 (Data Preparation)

| 서비스 | 설명 |
|--------|------|
| SageMaker Data Wrangler | 시각적 인터페이스로 데이터 전처리 워크플로우 구성 |
| SageMaker Processing | 사전/사후 처리를 위한 관리형 컴퓨팅 (Spark, scikit-learn) |
| SageMaker Feature Store | 피처 저장소 (온라인/오프라인 스토어) |
| SageMaker Ground Truth | 데이터 라벨링 서비스 (인간 + 자동 라벨링) |
| SageMaker Clarify | 데이터 편향 분석, 모델 설명 가능성 |

### 2단계: 모델 개발 (Model Development)

| 서비스 | 설명 |
|--------|------|
| SageMaker Studio | 통합 개발 환경 (IDE) |
| SageMaker Notebooks | 관리형 Jupyter 노트북 인스턴스 |
| SageMaker Experiments | 실험 추적 및 비교 |
| SageMaker Autopilot | AutoML - 자동 모델 생성 및 튜닝 |
| SageMaker JumpStart | 사전 훈련된 모델 허브 / Foundation Models |
| SageMaker Canvas | 노코드 ML (비개발자용) |

### 3단계: 모델 훈련 (Model Training)

| 서비스 | 설명 |
|--------|------|
| SageMaker Training | 관리형 훈련 인프라 (분산 훈련 지원) |
| SageMaker Debugger | 훈련 중 실시간 디버깅 및 프로파일링 |
| SageMaker HyperPod | 대규모 모델 훈련용 관리형 클러스터 |
| Automatic Model Tuning | 하이퍼파라미터 자동 최적화 (HPO) |

### 4단계: 모델 배포 (Model Deployment)

| 서비스 | 설명 |
|--------|------|
| Real-time Inference | 실시간 추론 엔드포인트 |
| Serverless Inference | 서버리스 추론 (Scale to Zero) |
| Asynchronous Inference | 비동기 추론 (대용량/긴 처리 시간) |
| Batch Transform | 대량 일괄 추론 |
| SageMaker Neo | 모델 컴파일/최적화 (엣지 배포) |
| Multi-Model Endpoints | 하나의 엔드포인트에서 여러 모델 서빙 |
| Shadow Testing | 새 모델을 실 트래픽으로 테스트 (A/B) |

### 5단계: 운영 및 거버넌스 (Operations & Governance)

| 서비스 | 설명 |
|--------|------|
| SageMaker Model Registry | 모델 버전 관리 및 승인 워크플로우 |
| SageMaker Model Monitor | 배포된 모델의 성능/드리프트 모니터링 |
| SageMaker Model Cards | 모델 문서화 및 거버넌스 |
| SageMaker Pipelines | ML 워크플로우 오케스트레이션 (CI/CD) |
| SageMaker Model Dashboard | 모델 상태 통합 대시보드 |

### SageMaker 시작하기 - CLI 기본 명령어

```bash
# SageMaker 도메인 목록 조회
aws sagemaker list-domains \
  --region ap-northeast-2

# 노트북 인스턴스 생성
aws sagemaker create-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --instance-type ml.t3.medium \
  --role-arn "arn:aws:iam::123456789012:role/SageMakerRole" \
  --volume-size-in-gb 20 \
  --region ap-northeast-2

# 노트북 인스턴스 상태 확인
aws sagemaker describe-notebook-instance \
  --notebook-instance-name "ml-dev-notebook" \
  --query '[NotebookInstanceStatus, InstanceType, VolumeSizeInGB]' \
  --region ap-northeast-2

# 훈련 작업 목록 조회
aws sagemaker list-training-jobs \
  --sort-by CreationTime \
  --sort-order Descending \
  --max-results 10 \
  --region ap-northeast-2

# 엔드포인트 목록 조회
aws sagemaker list-endpoints \
  --sort-by CreationTime \
  --sort-order Descending \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### SageMaker AI 전체 아키텍처

```
+=====================================================================+
|                    SageMaker Unified Studio                          |
|  (데이터 분석 + ML 개발 + GenAI 앱 개발 통합 환경)                    |
+=====================================================================+
|                                                                     |
|  +--[Data Prep]--+  +--[Dev/Train]--+  +--[Deploy]--+  +--[Ops]--+ |
|  | Data Wrangler |  | Studio        |  | Real-time  |  | Model   | |
|  | Processing    |  | Experiments   |  | Serverless |  | Monitor | |
|  | Feature Store |  | Training      |  | Async      |  | Model   | |
|  | Ground Truth  |  | Debugger      |  | Batch      |  | Registry| |
|  | Clarify       |  | HPO           |  | Neo        |  | Cards   | |
|  +---------------+  | Autopilot     |  | Multi-Model|  | Pipeline| |
|                      | JumpStart     |  +------------+  +---------+ |
|                      | HyperPod     |                               |
|                      +---------------+                               |
|                                                                     |
+=====================================================================+
|                    Infrastructure Layer                              |
|  +------------+  +-----------+  +----------+  +------------------+  |
|  | EC2/ECS    |  | S3        |  | VPC      |  | IAM / KMS / CW   |  |
|  | (Training  |  | (Data &   |  | (Network |  | (Security &      |  |
|  |  Inference)|  |  Models)  |  |  Isolate)|  |  Monitoring)     |  |
|  +------------+  +-----------+  +----------+  +------------------+  |
+=====================================================================+
```

### ML 라이프사이클 워크플로우

일반적인 SageMaker 기반 ML 프로젝트의 흐름은 다음과 같습니다.

```
1. 데이터 준비
   S3 (원본 데이터)
       |
   Processing Job (전처리)
       |
   Feature Store (피처 저장)
       |
2. 모델 개발 및 훈련
   Studio (탐색적 분석, 프로토타이핑)
       |
   Training Job (모델 훈련)
       |
   HPO (하이퍼파라미터 최적화)
       |
   Experiments (실험 기록/비교)
       |
3. 모델 평가 및 등록
   Clarify (Bias/Explainability 분석)
       |
   Model Registry (모델 등록)
       |
   Model Cards (문서화)
       |
4. 배포 및 운영
   Endpoint (추론 서비스)
       |
   Model Monitor (드리프트 감지)
       |
   [성능 저하 감지시] --> 2단계로 회귀 (재훈련)
```

### SageMaker 훈련 작업의 내부 동작

훈련 작업(Training Job)은 SageMaker의 핵심 기능입니다. 내부적으로 다음과 같이 동작합니다.

1. **인스턴스 프로비저닝**: 지정된 인스턴스 유형으로 훈련 환경을 생성합니다.
2. **컨테이너 실행**: ECR에서 훈련 컨테이너 이미지를 풀링하여 실행합니다.
3. **데이터 로딩**: S3에서 훈련 데이터를 로컬 스토리지로 복사합니다 (또는 Pipe 모드로 스트리밍).
4. **훈련 실행**: 컨테이너 내에서 훈련 스크립트가 실행됩니다.
5. **아티팩트 업로드**: 훈련 완료 후 모델 아티팩트(model.tar.gz)를 S3에 업로드합니다.
6. **인스턴스 해제**: 훈련 환경이 자동으로 정리됩니다.

```python
import sagemaker
from sagemaker.estimator import Estimator

session = sagemaker.Session()
role = sagemaker.get_execution_role()

estimator = Estimator(
    image_uri='123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/my-training:latest',
    role=role,
    instance_count=2,
    instance_type='ml.p3.2xlarge',
    output_path='s3://my-bucket/output/',
    max_run=86400,  # 최대 24시간
    sagemaker_session=session,
    hyperparameters={
        'epochs': 50,
        'batch-size': 64,
        'learning-rate': 0.001
    }
)

# 분산 훈련 실행
estimator.fit({
    'train': 's3://my-bucket/data/train/',
    'validation': 's3://my-bucket/data/validation/'
})
```

### 데이터 입력 모드 비교

| 입력 모드 | 동작 방식 | 적합한 경우 |
|-----------|-----------|------------|
| File Mode | S3 -> 로컬 디스크 복사 후 훈련 | 데이터 전체를 반복적으로 읽는 경우 |
| Pipe Mode | S3에서 스트리밍으로 직접 읽기 | 대용량 데이터, 순차적 읽기 |
| FastFile Mode | S3를 POSIX 파일 시스템처럼 마운트 | 랜덤 액세스가 필요한 대용량 데이터 |

## 실전 활용

### 1. SageMaker Pipelines로 ML 워크플로우 자동화

```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.step_collections import RegisterModel
from sagemaker.processing import ScriptProcessor

# 전처리 단계 정의
script_processor = ScriptProcessor(
    image_uri='123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sklearn:latest',
    role=role,
    instance_count=1,
    instance_type='ml.m5.xlarge',
    command=['python3']
)

preprocess_step = ProcessingStep(
    name='PreprocessData',
    processor=script_processor,
    code='preprocessing.py',
    inputs=[
        sagemaker.processing.ProcessingInput(
            source='s3://my-bucket/raw-data/',
            destination='/opt/ml/processing/input'
        )
    ],
    outputs=[
        sagemaker.processing.ProcessingOutput(
            output_name='train',
            source='/opt/ml/processing/output/train',
            destination='s3://my-bucket/processed/train/'
        ),
        sagemaker.processing.ProcessingOutput(
            output_name='test',
            source='/opt/ml/processing/output/test',
            destination='s3://my-bucket/processed/test/'
        )
    ]
)

# 훈련 단계 정의
train_step = TrainingStep(
    name='TrainModel',
    estimator=estimator,
    inputs={
        'train': sagemaker.inputs.TrainingInput(
            s3_data=preprocess_step.properties.ProcessingOutputConfig
                .Outputs['train'].S3Output.S3Uri
        )
    }
)

# 모델 등록 단계
register_step = RegisterModel(
    name='RegisterModel',
    estimator=estimator,
    model_data=train_step.properties.ModelArtifacts.S3ModelArtifacts,
    content_types=['application/json'],
    response_types=['application/json'],
    inference_instances=['ml.m5.large'],
    model_package_group_name='fraud-detection-models',
    approval_status='PendingManualApproval'
)

# 파이프라인 정의 및 실행
pipeline = Pipeline(
    name='fraud-detection-pipeline',
    steps=[preprocess_step, train_step, register_step],
    sagemaker_session=session
)

pipeline.upsert(role_arn=role)
pipeline.start()
```

### 2. JumpStart로 Foundation Model 활용

```bash
# JumpStart에서 사용 가능한 모델 목록 조회
aws sagemaker list-hub-content-versions \
  --hub-name SageMakerPublicHub \
  --hub-content-name meta-llama-llama-3-8b \
  --hub-content-type Model \
  --region ap-northeast-2
```

```python
from sagemaker.jumpstart.model import JumpStartModel

# JumpStart 모델 배포
model = JumpStartModel(
    model_id='meta-textgeneration-llama-3-8b',
    role=role
)

predictor = model.deploy(
    initial_instance_count=1,
    instance_type='ml.g5.2xlarge',
    endpoint_name='llama3-8b-endpoint'
)

# 추론
response = predictor.predict({
    'inputs': 'Explain machine learning in simple terms:',
    'parameters': {
        'max_new_tokens': 256,
        'temperature': 0.7
    }
})
print(response)
```

### 3. Model Monitor로 운영 중 모니터링

```bash
# 모델 모니터링 스케줄 생성
aws sagemaker create-monitoring-schedule \
  --monitoring-schedule-name "fraud-model-monitor" \
  --monitoring-schedule-config '{
    "ScheduleConfig": {
      "ScheduleExpression": "cron(0 */6 * * ? *)" 
    },
    "MonitoringJobDefinition": {
      "MonitoringInputs": [{
        "EndpointInput": {
          "EndpointName": "fraud-detection-endpoint",
          "LocalPath": "/opt/ml/processing/input"
        }
      }],
      "MonitoringOutputConfig": {
        "MonitoringOutputs": [{
          "S3Output": {
            "S3Uri": "s3://my-bucket/monitoring/output/",
            "LocalPath": "/opt/ml/processing/output"
          }
        }]
      },
      "MonitoringResources": {
        "ClusterConfig": {
          "InstanceCount": 1,
          "InstanceType": "ml.m5.large",
          "VolumeSizeInGB": 20
        }
      },
      "MonitoringAppSpecification": {
        "ImageUri": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-model-monitor-analyzer:latest"
      },
      "RoleArn": "arn:aws:iam::123456789012:role/SageMakerMonitorRole"
    }
  }' \
  --region ap-northeast-2
```

## 모범 사례/보안

### 비용 최적화 전략

1. **Managed Spot Training**: 훈련 작업에 Spot 인스턴스를 사용하면 최대 90% 비용 절감이 가능합니다. 체크포인트를 설정하여 Spot 중단에 대비해야 합니다.

```python
estimator = Estimator(
    # ... 기본 설정 ...
    use_spot_instances=True,
    max_wait=7200,  # Spot 대기 최대 시간
    checkpoint_s3_uri='s3://my-bucket/checkpoints/'
)
```

2. **인스턴스 사용량 모니터링**: 유휴 상태의 노트북 인스턴스와 엔드포인트를 정기적으로 정리합니다.
3. **적절한 추론 옵션 선택**: 트래픽 패턴에 따라 실시간/서버리스/비동기/배치 중 적합한 것을 선택합니다.
4. **다중 모델 엔드포인트**: 유사한 프레임워크의 모델 여러 개를 하나의 엔드포인트에서 서빙하면 인프라 비용을 절감할 수 있습니다.

### 보안 체계

- **네트워크 격리**: VPCOnly 모드로 도메인을 구성하고, 필요한 VPC 엔드포인트만 생성합니다.
- **암호화**: S3 버킷(SSE-KMS), EBS 볼륨, 네트워크 통신(TLS 1.2+) 모두 암호화합니다.
- **IAM 최소 권한**: 역할별로 필요한 SageMaker API만 허용하고, 조건 키로 인스턴스 유형과 리전을 제한합니다.
- **감사 로깅**: CloudTrail로 모든 SageMaker API 호출을 기록합니다.

### SageMaker 도입 전략

```
[Phase 1: 탐색 (1-2개월)]
- Studio/Canvas로 빠른 프로토타이핑
- JumpStart에서 사전 훈련 모델 테스트
- 소규모 데이터로 Autopilot 실행

[Phase 2: 개발 (2-4개월)]
- 커스텀 훈련 컨테이너 구축
- Feature Store 도입
- Experiments로 실험 관리 시작

[Phase 3: 자동화 (3-6개월)]
- Pipelines로 ML 워크플로우 자동화
- Model Registry로 모델 버전 관리
- Model Monitor로 운영 모니터링 구축

[Phase 4: 고도화 (지속)]
- HyperPod로 대규모 훈련
- Multi-Model Endpoints 최적화
- Model Cards로 거버넌스 체계 구축
```

## 관련 서비스 비교

| 항목 | Amazon SageMaker AI | Google Vertex AI | Azure ML | Databricks ML |
|------|-------------------|-----------------|----------|---------------|
| 노트북 | Studio (JupyterLab) | Workbench (JupyterLab) | Notebooks | Databricks Notebook |
| AutoML | Autopilot | AutoML | AutoML | AutoML |
| 모델 훈련 | Training Jobs | Custom Training | Compute Clusters | MLflow + Spark |
| 모델 서빙 | 4가지 옵션 | Endpoints | Endpoints | Model Serving |
| 피처 스토어 | Feature Store | Feature Store | Feature Store (미리보기) | Feature Store |
| 파이프라인 | Pipelines | Pipelines | Pipelines | Workflows |
| 모델 레지스트리 | Model Registry | Model Registry | Model Registry | MLflow Registry |
| Foundation Models | JumpStart | Model Garden | Model Catalog | Foundation Model APIs |
| 대규모 훈련 | HyperPod | Vertex AI Training | 해당 없음 | Mosaic ML |
| 노코드 ML | Canvas | 미지원 | Designer | 미지원 |
| 비용 모델 | 사용량 기반 | 사용량 기반 | 사용량 기반 | DBU 기반 |

## 요약

Amazon SageMaker AI는 ML 라이프사이클의 모든 단계를 포괄하는 AWS의 종합 ML 플랫폼입니다.

- **데이터 준비**(Data Wrangler, Processing, Feature Store, Ground Truth)부터 **훈련**(Training, Debugger, HPO, HyperPod), **배포**(실시간/서버리스/비동기/배치), **운영**(Model Monitor, Registry, Cards, Pipelines)까지 30개 이상의 서비스를 통합합니다.
- **SageMaker AI**(2024)는 생성형 AI 시대에 맞춰 Foundation Model 지원과 Unified Studio를 강화한 차세대 버전입니다.
- **SageMaker Pipelines**로 ML 워크플로우를 CI/CD 수준으로 자동화할 수 있으며, **JumpStart**를 통해 사전 훈련된 모델을 빠르게 배포할 수 있습니다.
- 도입은 **점진적 접근**이 권장됩니다. Studio/JumpStart로 시작하여, 조직의 ML 성숙도에 따라 Pipelines, Feature Store, Model Monitor 등을 단계적으로 도입하는 것이 효과적입니다.
- **비용 관리**의 핵심은 Spot Training 활용, 유휴 리소스 정리, 트래픽 패턴에 맞는 추론 옵션 선택입니다.