<!-- infographic-hero -->
![Amazon SageMaker Debugger 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker Debugger 한 장 요약 인포그래픽*

## 개요

머신러닝 모델 학습은 종종 예측하기 어려운 문제를 수반합니다. 그래디언트 소실(Vanishing Gradient), 과적합(Overfitting), 학습률 문제, 가중치 초기화 실패 등 다양한 이유로 학습이 실패하거나 비효율적으로 진행될 수 있습니다. 이러한 문제는 학습이 완료된 후에야 발견되는 경우가 많아, 상당한 시간과 비용을 낭비하게 됩니다.

Amazon SageMaker Debugger는 이러한 학습 문제를 실시간으로 탐지하고 진단하는 도구입니다. Debugger는 학습 과정에서 발생하는 텐서(가중치, 그래디언트, 출력 등)를 수집하고, 내장 규칙(Built-in Rules)을 통해 잠재적 문제를 자동으로 감지하며, 시스템 리소스(CPU, GPU, 메모리, 네트워크) 사용 현황을 프로파일링합니다.

### SageMaker Debugger의 세 가지 핵심 영역

1. **실시간 학습 모니터링**: 학습 진행 중 텐서 값을 수집하여 문제를 조기에 발견합니다.
2. **자동 문제 탐지**: 30개 이상의 내장 규칙이 일반적인 학습 문제를 자동으로 감지합니다.
3. **시스템 프로파일링**: GPU/CPU 활용률, 메모리 사용량, I/O 병목 등을 분석하여 학습 효율을 최적화합니다.

### Debugger가 해결하는 주요 문제

전통적인 ML 학습 디버깅에서 겪는 어려움은 다음과 같습니다.

- **블랙박스 학습**: 학습이 진행되는 동안 내부 상태를 파악하기 어렵습니다.
- **사후 분석 한계**: 학습이 완료된 후에야 문제를 발견하면, 이미 시간과 비용이 낭비된 후입니다.
- **리소스 비효율**: GPU가 유휴 상태이거나, 데이터 로딩이 병목인 경우를 파악하기 어렵습니다.
- **수동 디버깅**: print문이나 로그를 통한 수동 디버깅은 비효율적이고 체계적이지 않습니다.

SageMaker Debugger는 이 모든 문제를 자동화된 방식으로 해결합니다.

## 핵심 기능

### 1. 텐서 수집 (Tensor Collection)

Debugger는 학습 과정에서 다양한 텐서를 자동으로 수집합니다.

**수집 가능한 텐서 유형**

- **가중치(Weights)**: 모델의 각 레이어의 가중치 값
- **그래디언트(Gradients)**: 역전파 과정의 그래디언트 값
- **편향(Biases)**: 모델의 편향 파라미터
- **활성화(Activations)**: 각 레이어의 활성화 출력
- **손실(Losses)**: 학습 및 검증 손실 값
- **커스텀 텐서**: 사용자가 정의한 임의의 텐서

**수집 설정**

텐서 수집은 DebuggerHookConfig를 통해 설정합니다. 수집 빈도, 수집 대상, 저장 위치 등을 세밀하게 제어할 수 있습니다.

```python
from sagemaker.debugger import DebuggerHookConfig, CollectionConfig

debugger_hook_config = DebuggerHookConfig(
    s3_output_path="s3://my-debugger-bucket/tensors/",
    collection_configs=[
        CollectionConfig(
            name="weights",
            parameters={
                "save_interval": "100",  # 100스텝마다 수집
                "save_steps": "0,50,100,500,1000",  # 특정 스텝에서 수집
            }
        ),
        CollectionConfig(
            name="gradients",
            parameters={"save_interval": "100"}
        ),
        CollectionConfig(
            name="losses",
            parameters={"save_interval": "10"}  # 손실은 더 자주 수집
        ),
        CollectionConfig(
            name="feature_importance",
            parameters={"save_interval": "500"}
        ),
    ]
)
```

### 2. 내장 규칙 (Built-in Rules)

Debugger는 30개 이상의 내장 규칙을 제공하여 일반적인 학습 문제를 자동으로 탐지합니다.

**학습 문제 탐지 규칙**

| 규칙 이름 | 탐지 대상 |
|----------|----------|
| VanishingGradient | 그래디언트가 0에 수렴하여 학습이 정체 |
| ExplodingTensor | 텐서 값이 무한대로 발산 |
| Overfit | 학습 손실은 감소하나 검증 손실이 증가 |
| Overtraining | 학습이 더 이상 개선되지 않음 |
| PoorWeightInitialization | 가중치 초기화 문제 |
| LossNotDecreasing | 손실이 감소하지 않음 |
| SaturatedActivation | 활성화 함수가 포화 상태 |
| WeightUpdateRatio | 가중치 업데이트가 너무 크거나 작음 |
| AllZero | 텐서 값이 모두 0 |
| ClassImbalance | 배치 내 클래스 불균형 |
| DeadRelu | ReLU 뉴런이 항상 0을 출력 |
| TensorVariance | 텐서의 분산이 비정상적 |
| UnchangedTensor | 텐서 값이 변하지 않음 |

**시스템 프로파일링 규칙**

| 규칙 이름 | 탐지 대상 |
|----------|----------|
| LowGPUUtilization | GPU 활용률이 낮음 |
| CPUBottleneck | CPU가 병목 |
| IOBottleneck | 데이터 로딩이 병목 |
| LoadBalancing | 다중 GPU 간 작업 불균형 |
| StepOutlier | 특정 스텝의 실행 시간이 비정상적 |
| MaxInitializationTime | 초기화 시간이 너무 김 |
| OverallSystemUsage | 전체 시스템 리소스 사용 현황 |
| BatchSize | 배치 크기가 최적이 아님 |
| GPUMemoryIncrease | GPU 메모리가 지속적으로 증가 |
| Dataloader | 데이터 로더 성능 문제 |

### 3. 시스템 프로파일링

Debugger의 프로파일링 기능은 학습 인프라의 성능을 상세하게 분석합니다.

**수집되는 시스템 메트릭**

- **GPU**: 활용률, 메모리 사용량, 온도, 전력 소비
- **CPU**: 활용률, 컨텍스트 스위칭, 인터럽트
- **메모리**: RSS, 가상 메모리, 페이지 폴트
- **네트워크**: 송수신 바이트, 패킷 수 (분산 학습 시)
- **디스크 I/O**: 읽기/쓰기 속도, IOPS

**프레임워크 프로파일링**

PyTorch와 TensorFlow의 학습 루프를 상세하게 프로파일링합니다.

- 순전파(Forward Pass) 시간
- 역전파(Backward Pass) 시간
- 파라미터 업데이트 시간
- 데이터 로딩 시간
- 전처리 시간
- 통신 시간 (분산 학습 시)

### 4. 실시간 알림 및 자동 조치

규칙 위반이 감지되면 다음 조치를 취할 수 있습니다.

- **CloudWatch 알림**: 규칙 위반 시 CloudWatch에 메트릭과 로그를 기록
- **학습 중단**: 심각한 문제(ExplodingTensor 등) 발생 시 학습을 자동으로 중단하여 비용 낭비 방지
- **SNS 알림**: 이메일 또는 SMS로 알림 발송
- **Lambda 트리거**: 규칙 위반 시 Lambda 함수를 실행하여 커스텀 조치 수행

## 아키텍처/동작 원리

### Debugger 아키텍처

```
[학습 인스턴스]
  - 학습 컨테이너
  - Debugger Hook (텐서 수집 에이전트)
  - 시스템 프로파일러
       |
       | (텐서 데이터, 시스템 메트릭)
       v
[Amazon S3]
  - 텐서 저장소
  - 프로파일링 데이터
       |
       v
[규칙 평가 인스턴스 (별도 컨테이너)]
  - 내장 규칙 실행
  - 커스텀 규칙 실행
  - 규칙 위반 감지
       |
       v
[CloudWatch / SNS / Lambda]
  - 알림 및 자동 조치

[SageMaker Studio]
  - 실시간 시각화 대시보드
  - 텐서 분석 노트북
```

### Hook 메커니즘

Debugger Hook은 학습 프레임워크(PyTorch, TensorFlow, MXNet, XGBoost)에 투명하게 삽입되어 텐서를 수집합니다.

**PyTorch에서의 동작**
- torch.nn.Module의 forward hook과 backward hook을 자동으로 등록합니다.
- 각 레이어의 입력, 출력, 그래디언트를 수집합니다.
- smdebug 라이브러리가 학습 스크립트에 자동으로 통합됩니다.

**TensorFlow에서의 동작**
- tf.keras.callbacks.Callback을 통해 학습 루프에 삽입됩니다.
- 각 배치/에포크 종료 시 텐서를 수집합니다.
- tf.debugging.experimental.enable_dump_debug_info와 유사한 방식으로 동작합니다.

### 규칙 평가 프로세스

규칙 평가는 학습 인스턴스와 별도의 인스턴스에서 실행됩니다. 이를 통해 학습 성능에 영향을 주지 않으면서 실시간으로 문제를 탐지할 수 있습니다.

1. **텐서 수집**: Hook이 텐서를 S3에 저장
2. **규칙 인스턴스 실행**: 규칙 평가 컨테이너가 별도 인스턴스에서 실행
3. **텐서 읽기**: 규칙 인스턴스가 S3에서 텐서를 읽음
4. **규칙 평가**: 각 규칙의 조건을 평가
5. **결과 보고**: 위반 여부를 CloudWatch 및 SageMaker API에 보고

## 실전 활용

### 사용 사례 1: PyTorch 학습 작업에 Debugger 적용

```bash
# 학습 스크립트 및 데이터를 S3에 업로드
aws s3 cp train.py s3://my-training-bucket/code/train.py
aws s3 sync ./data/ s3://my-training-bucket/data/

# Debugger를 포함한 학습 작업 생성
aws sagemaker create-training-job \
  --training-job-name debugger-demo-$(date +%Y%m%d-%H%M%S) \
  --algorithm-specification '{
    "TrainingImage": "763104351884.dkr.ecr.ap-northeast-2.amazonaws.com/pytorch-training:1.13-gpu-py39",
    "TrainingInputMode": "File"
  }' \
  --role-arn arn:aws:iam::123456789012:role/SageMakerRole \
  --input-data-config '[
    {
      "ChannelName": "training",
      "DataSource": {
        "S3DataSource": {
          "S3DataType": "S3Prefix",
          "S3Uri": "s3://my-training-bucket/data/",
          "S3DataDistributionType": "FullyReplicated"
        }
      }
    }
  ]' \
  --output-data-config '{
    "S3OutputPath": "s3://my-training-bucket/output/"
  }' \
  --resource-config '{
    "InstanceType": "ml.p3.2xlarge",
    "InstanceCount": 1,
    "VolumeSizeInGB": 50
  }' \
  --stopping-condition '{"MaxRuntimeInSeconds": 7200}' \
  --debugger-hook-config '{
    "S3OutputPath": "s3://my-training-bucket/debugger-output/",
    "CollectionConfigurations": [
      {
        "CollectionName": "weights",
        "CollectionParameters": {"save_interval": "100"}
      },
      {
        "CollectionName": "gradients",
        "CollectionParameters": {"save_interval": "100"}
      },
      {
        "CollectionName": "losses",
        "CollectionParameters": {"save_interval": "10"}
      }
    ]
  }' \
  --debugger-rule-configurations '[
    {
      "RuleConfigurationName": "VanishingGradient",
      "RuleEvaluatorImage": "929884845733.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-debugger-rules:latest",
      "RuleParameters": {"rule_to_invoke": "VanishingGradient", "threshold": "0.0000001"}
    },
    {
      "RuleConfigurationName": "ExplodingTensor",
      "RuleEvaluatorImage": "929884845733.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-debugger-rules:latest",
      "RuleParameters": {"rule_to_invoke": "ExplodingTensor"}
    },
    {
      "RuleConfigurationName": "Overfit",
      "RuleEvaluatorImage": "929884845733.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-debugger-rules:latest",
      "RuleParameters": {
        "rule_to_invoke": "Overfit",
        "patience": "5",
        "ratio_threshold": "0.1"
      }
    },
    {
      "RuleConfigurationName": "LossNotDecreasing",
      "RuleEvaluatorImage": "929884845733.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-debugger-rules:latest",
      "RuleParameters": {
        "rule_to_invoke": "LossNotDecreasing",
        "patience": "10"
      }
    }
  ]' \
  --profiler-config '{
    "S3OutputPath": "s3://my-training-bucket/profiler-output/",
    "ProfilingIntervalInMilliseconds": 500,
    "ProfilingParameters": {
      "DetailedProfilingConfig": "{\"StartStep\": 5, \"NumSteps\": 10}",
      "DataloaderProfilingConfig": "{\"StartStep\": 5, \"NumSteps\": 10}"
    }
  }' \
  --profiler-rule-configurations '[
    {
      "RuleConfigurationName": "LowGPUUtilization",
      "RuleEvaluatorImage": "929884845733.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-debugger-rules:latest",
      "RuleParameters": {
        "rule_to_invoke": "LowGPUUtilization",
        "threshold_p95": "70",
        "threshold_p5": "10"
      }
    },
    {
      "RuleConfigurationName": "ProfilerReport",
      "RuleEvaluatorImage": "929884845733.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-debugger-rules:latest",
      "RuleParameters": {"rule_to_invoke": "ProfilerReport"}
    }
  ]'

# 학습 작업 상태 및 Debugger 규칙 상태 확인
aws sagemaker describe-training-job \
  --training-job-name debugger-demo-$(date +%Y%m%d-%H%M%S) \
  --query '{
    TrainingStatus: TrainingJobStatus,
    DebugRuleStatuses: DebugRuleEvaluationStatuses[].{Rule: RuleConfigurationName, Status: RuleEvaluationStatus},
    ProfilerRuleStatuses: ProfilerRuleEvaluationStatuses[].{Rule: RuleConfigurationName, Status: RuleEvaluationStatus}
  }'
```

### 사용 사례 2: Python SDK를 활용한 Debugger 설정

```python
import sagemaker
from sagemaker.debugger import (
    Rule,
    DebuggerHookConfig,
    CollectionConfig,
    ProfilerConfig,
    FrameworkProfile,
    ProfilerRule,
    rule_configs,
)
from sagemaker.pytorch import PyTorch

role = sagemaker.get_execution_role()
session = sagemaker.Session()

# Debugger Hook 설정
debugger_hook_config = DebuggerHookConfig(
    s3_output_path=f"s3://{session.default_bucket()}/debugger/",
    collection_configs=[
        CollectionConfig(name="weights", parameters={"save_interval": "100"}),
        CollectionConfig(name="gradients", parameters={"save_interval": "100"}),
        CollectionConfig(name="losses", parameters={"save_interval": "10"}),
    ]
)

# 학습 문제 탐지 규칙 설정
rules = [
    Rule.sagemaker(rule_configs.vanishing_gradient()),
    Rule.sagemaker(rule_configs.exploding_tensor()),
    Rule.sagemaker(rule_configs.overfit()),
    Rule.sagemaker(rule_configs.overtraining()),
    Rule.sagemaker(rule_configs.loss_not_decreasing()),
    Rule.sagemaker(rule_configs.dead_relu()),
    Rule.sagemaker(
        rule_configs.class_imbalance(),
        rule_parameters={"threshold": "10"}
    ),
]

# 프로파일링 설정
profiler_config = ProfilerConfig(
    system_monitor_interval_millis=500,
    framework_profile_params=FrameworkProfile(
        start_step=5,
        num_steps=10,
    )
)

# 프로파일링 규칙
profiler_rules = [
    ProfilerRule.sagemaker(rule_configs.LowGPUUtilization()),
    ProfilerRule.sagemaker(rule_configs.CPUBottleneck()),
    ProfilerRule.sagemaker(rule_configs.IOBottleneck()),
    ProfilerRule.sagemaker(rule_configs.ProfilerReport()),
]

# 학습 작업 생성
estimator = PyTorch(
    entry_point="train.py",
    source_dir="./code",
    role=role,
    instance_count=1,
    instance_type="ml.p3.2xlarge",
    framework_version="1.13",
    py_version="py39",
    debugger_hook_config=debugger_hook_config,
    rules=rules,
    profiler_config=profiler_config,
    profiler_rules=profiler_rules,
)

estimator.fit({"training": "s3://my-training-bucket/data/"})
```

### 사용 사례 3: Debugger 결과 분석

```bash
# Debugger 출력 파일 확인
aws s3 ls s3://my-training-bucket/debugger-output/ --recursive --summarize

# 프로파일러 리포트 다운로드
aws s3 sync s3://my-training-bucket/profiler-output/profiler-report/ ./profiler-report/

# 규칙 평가 결과 확인
aws sagemaker describe-training-job \
  --training-job-name debugger-demo-20240101-120000 \
  --query 'DebugRuleEvaluationStatuses' \
  --output table

# CloudWatch에서 Debugger 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace "/aws/sagemaker/TrainingJobs" \
  --metric-name "train:loss" \
  --dimensions Name=TrainingJobName,Value=debugger-demo-20240101-120000 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 60 \
  --statistics Average
```

### 사용 사례 4: 커스텀 규칙 작성

내장 규칙 외에 사용자 정의 규칙을 작성할 수 있습니다.

```python
# custom_rule.py
from smdebug.rules import Rule

class CustomGradientNormRule(Rule):
    def __init__(self, base_trial, threshold=10.0):
        super().__init__(base_trial)
        self.threshold = threshold

    def invoke_at_step(self, step):
        for tname in self.base_trial.tensor_names(collection="gradients"):
            tensor = self.base_trial.tensor(tname)
            tensor_value = tensor.value(step)
            grad_norm = tensor_value.flatten()
            l2_norm = (grad_norm ** 2).sum() ** 0.5

            if l2_norm > self.threshold:
                self.logger.info(
                    f"Step {step}: Gradient norm of {tname} is {l2_norm:.4f}, "
                    f"exceeding threshold {self.threshold}"
                )
                return True  # 규칙 위반

        return False  # 정상
```

## 모범 사례/보안

### 디버깅 모범 사례

1. **단계적 디버깅 접근**: 먼저 시스템 프로파일링으로 인프라 문제를 해결한 후, 텐서 분석으로 모델 문제를 디버깅합니다.

2. **텐서 수집 빈도 최적화**: 텐서 수집은 학습 성능에 영향을 줄 수 있으므로, 적절한 수집 빈도를 설정합니다.
   - 프로토타이핑 단계: 높은 빈도 (10~50 스텝마다)
   - 프로덕션 학습: 낮은 빈도 (100~500 스텝마다)
   - 손실 값: 자주 수집 (10 스텝마다)
   - 가중치/그래디언트: 상대적으로 낮은 빈도

3. **관련 규칙만 활성화**: 모든 규칙을 동시에 활성화하면 규칙 평가 비용이 증가합니다. 현재 디버깅 목적에 맞는 규칙만 선택적으로 활성화합니다.

4. **프로파일링은 초반에만**: 시스템 프로파일링은 학습 초반 몇 스텝에서만 수행하여 성능 영향을 최소화합니다.

5. **자동 중단 설정**: ExplodingTensor와 같이 명백한 문제에 대해서는 자동 학습 중단을 설정하여 비용을 절감합니다.

### 비용 최적화

1. **규칙 평가 인스턴스 최적화**: 규칙 평가에는 별도 인스턴스가 사용됩니다. ml.t3.medium 등 저렴한 인스턴스를 사용합니다.

2. **S3 라이프사이클 정책**: 디버깅 데이터에 대해 S3 라이프사이클 정책을 설정하여 오래된 텐서 데이터를 자동 삭제합니다.

```bash
# S3 라이프사이클 정책 설정
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-training-bucket \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "DeleteOldDebuggerData",
      "Status": "Enabled",
      "Filter": {"Prefix": "debugger-output/"},
      "Expiration": {"Days": 30}
    }]
  }'
```

3. **선택적 수집**: 모든 텐서를 수집하지 말고, 문제가 의심되는 레이어의 텐서만 선택적으로 수집합니다.

### 보안

1. **데이터 암호화**: Debugger가 S3에 저장하는 텐서 데이터는 KMS로 암호화합니다.

2. **IAM 최소 권한**: Debugger 규칙 평가 역할에는 필요한 최소한의 S3 읽기 권한과 SageMaker API 호출 권한만 부여합니다.

3. **VPC 설정**: 학습 작업과 규칙 평가를 VPC 내에서 실행합니다.

## 관련 서비스 비교

### SageMaker Debugger vs TensorBoard

| 항목 | SageMaker Debugger | TensorBoard |
|------|-------------------|-------------|
| 자동 문제 탐지 | 30+ 내장 규칙 | 없음 (수동 분석) |
| 시스템 프로파일링 | 내장 지원 | 제한적 (TF Profiler) |
| 자동 조치 | 학습 중단/알림 가능 | 없음 |
| 관리형 | 완전 관리형 | 자체 운영 |
| 프레임워크 | PyTorch/TF/MXNet/XGBoost | 주로 TensorFlow |
| 분산 학습 지원 | 네이티브 | 제한적 |
| 비용 | 유료 | 무료 (인프라 비용 별도) |

### SageMaker Debugger vs PyTorch Profiler

| 항목 | SageMaker Debugger | PyTorch Profiler |
|------|-------------------|------------------|
| 대상 | 모든 SageMaker 프레임워크 | PyTorch 전용 |
| 규칙 기반 탐지 | 지원 | 미지원 |
| 인프라 | 관리형 | 자체 운영 |
| S3 통합 | 네이티브 | 별도 구현 |
| 커스텀 규칙 | 지원 | 미지원 |
| 시각화 | SageMaker Studio | TensorBoard |

### SageMaker Debugger vs Weights & Biases (W&B)

| 항목 | SageMaker Debugger | Weights & Biases |
|------|-------------------|------------------|
| 실험 추적 | 제한적 | 풍부 |
| 자동 규칙 탐지 | 30+ 규칙 | 없음 |
| 시스템 프로파일링 | 상세 | 기본적 |
| 협업 기능 | SageMaker Studio | 웹 대시보드 |
| 가격 | 인스턴스 기반 | 구독 기반 |
| AWS 통합 | 네이티브 | 플러그인 |

## 요약

Amazon SageMaker Debugger는 ML 학습 과정의 투명성을 높이고, 문제를 조기에 발견하며, 시스템 리소스 활용을 최적화하는 강력한 도구입니다.

핵심 특징을 정리하면 다음과 같습니다.

- **실시간 텐서 수집**: 가중치, 그래디언트, 활성화, 손실 등 다양한 텐서를 학습 중에 수집
- **30개 이상의 내장 규칙**: 그래디언트 소실, 과적합, 텐서 폭발 등 일반적인 학습 문제를 자동 탐지
- **시스템 프로파일링**: GPU/CPU 활용률, 메모리, I/O 등 인프라 성능을 상세 분석
- **프레임워크 프로파일링**: 순전파, 역전파, 데이터 로딩 등 학습 루프의 각 단계를 분석
- **자동 조치**: 문제 발견 시 학습 중단, 알림 발송 등 자동 대응
- **커스텀 규칙**: 사용자 정의 규칙으로 도메인 특화 문제 탐지
- **비침입적**: 학습 코드를 수정하지 않고도 디버깅 및 프로파일링 가능

SageMaker Debugger는 특히 대규모 학습 작업에서 비용 효율성을 높이고, 학습 실패의 원인을 빠르게 파악하는 데 큰 가치를 제공합니다. GPU 인스턴스 비용이 높은 만큼, Debugger를 통해 학습 효율을 최적화하면 상당한 비용 절감 효과를 얻을 수 있습니다.