<!-- infographic-hero -->
![Amazon SageMaker Neo 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker Neo 한 장 요약 인포그래픽*

# Amazon SageMaker Neo

## 개요

Amazon SageMaker Neo는 머신러닝 모델을 특정 하드웨어에 최적화하여 컴파일하는 서비스입니다. 한 번 훈련한 모델을 다양한 하드웨어 플랫폼(클라우드 인스턴스, 엣지 디바이스, 모바일 기기)에서 최적의 성능으로 실행할 수 있도록 자동 최적화를 수행합니다.

ML 모델을 프로덕션 환경에 배포할 때 가장 흔히 직면하는 문제 중 하나는 하드웨어 종속성입니다. PyTorch로 훈련한 모델을 NVIDIA GPU에서는 잘 실행되지만, ARM 프로세서 기반 엣지 디바이스에서는 호환성 문제나 성능 저하가 발생할 수 있습니다. SageMaker Neo는 이 문제를 해결하기 위해 Apache TVM 기반의 오픈소스 컴파일러 프레임워크인 Neo-AI를 활용합니다.

Neo의 핵심 가치 제안은 다음과 같습니다.

- **성능 향상**: 모델 컴파일을 통해 추론 지연 시간을 최대 25배 단축할 수 있습니다.
- **하드웨어 독립성**: 동일한 모델을 클라우드(Intel, AMD, NVIDIA GPU), 엣지(ARM, Qualcomm), 모바일(Android, iOS) 등 다양한 플랫폼에 배포할 수 있습니다.
- **비용 절감**: 최적화된 모델은 더 작은 인스턴스에서도 동일한 성능을 낼 수 있어 인프라 비용을 절감할 수 있습니다.
- **프레임워크 호환성**: TensorFlow, PyTorch, MXNet, XGBoost, ONNX 등 주요 프레임워크를 지원합니다.

## 핵심 기능

### 1. 모델 컴파일(Model Compilation)

Neo의 핵심 기능은 모델 컴파일입니다. 훈련된 모델을 대상 하드웨어에 최적화된 실행 파일로 변환합니다.

```python
import boto3
import sagemaker
from sagemaker.pytorch import PyTorchModel

session = sagemaker.Session()
role = sagemaker.get_execution_role()

# PyTorch 모델을 Neo로 컴파일
pytorch_model = PyTorchModel(
    model_data='s3://my-bucket/models/resnet50/model.tar.gz',
    role=role,
    framework_version='2.0',
    py_version='py310',
    entry_point='inference.py'
)

# 클라우드 GPU (ml.c5) 타겟으로 컴파일
compiled_model = pytorch_model.compile(
    target_instance_family='ml_c5',
    input_shape={'input': [1, 3, 224, 224]},
    output_path='s3://my-bucket/compiled-models/resnet50/',
    role=role,
    job_name='neo-resnet50-compilation',
    framework='pytorch',
    framework_version='2.0'
)
```

```bash
# Neo 컴파일 작업 상태 확인
aws sagemaker describe-compilation-job \
  --compilation-job-name "neo-resnet50-compilation" \
  --region us-east-1 \
  --query '{Status: CompilationJobStatus, Target: OutputConfig.TargetDevice, StartTime: CreationTime}'

# 컴파일 작업 목록 조회
aws sagemaker list-compilation-jobs \
  --region us-east-1 \
  --sort-by CreationTime \
  --sort-order Descending \
  --max-results 10 \
  --output table
```

### 2. 지원 대상 플랫폼

Neo는 매우 광범위한 하드웨어 플랫폼을 지원합니다.

**클라우드 인스턴스**:
- `ml_c4`, `ml_c5`: Intel CPU 최적화
- `ml_m4`, `ml_m5`: 범용 인스턴스
- `ml_p2`, `ml_p3`: NVIDIA GPU (Tesla K80/V100)
- `ml_g4dn`: NVIDIA T4 GPU
- `ml_g5`: NVIDIA A10G GPU
- `ml_inf1`: AWS Inferentia 칩
- `ml_inf2`: AWS Inferentia2 칩

**엣지 디바이스**:
- `jetson_nano`, `jetson_tx1`, `jetson_tx2`, `jetson_xavier`: NVIDIA Jetson 시리즈
- `rasp3b`, `rasp4b`: Raspberry Pi
- `deeplens`: AWS DeepLens
- `imx8qm`: NXP i.MX 8
- `amba_cv22`, `amba_cv25`: Ambarella CV
- `sitara_am57x`: Texas Instruments Sitara

**모바일 플랫폼**:
- `android`: ARM 기반 안드로이드 디바이스
- `coreml`: Apple CoreML (iOS/macOS)

### 3. Neo Runtime (DLR)

Neo로 컴파일된 모델은 DLR(Deep Learning Runtime)을 통해 실행됩니다. DLR은 경량 런타임으로, 다양한 하드웨어에서 일관된 API로 모델을 실행할 수 있습니다.

```python
import dlr
import numpy as np

# DLR을 사용한 컴파일된 모델 로드 및 추론
model = dlr.DLRModel(
    model_path='/path/to/compiled/model',
    dev_type='gpu',  # 'cpu' 또는 'gpu'
    dev_id=0
)

# 입력 데이터 준비
input_data = np.random.rand(1, 3, 224, 224).astype('float32')

# 추론 실행
output = model.run(input_data)
print(f"추론 결과 shape: {output[0].shape}")
print(f"예측 클래스: {np.argmax(output[0])}")
```

### 4. AWS Inferentia 통합

Neo는 AWS의 커스텀 ML 칩인 Inferentia와 깊게 통합되어 있습니다. Inferentia 칩은 추론 워크로드에 특화되어 있으며, GPU 대비 최대 70%의 비용 절감을 제공합니다.

```python
# Inferentia (inf1) 타겟으로 컴파일
compiled_inf_model = pytorch_model.compile(
    target_instance_family='ml_inf1',
    input_shape={'input': [1, 3, 224, 224]},
    output_path='s3://my-bucket/compiled-models/resnet50-inf1/',
    role=role,
    job_name='neo-resnet50-inf1',
    framework='pytorch',
    framework_version='2.0',
    compiler_options=json.dumps({
        'dtype': 'float16',  # FP16 최적화
        'num-neuroncores': 4  # Neuron 코어 수 지정
    })
)

# Inferentia 인스턴스에 배포
predictor = compiled_inf_model.deploy(
    initial_instance_count=1,
    instance_type='ml.inf1.xlarge'
)
```

```bash
# Inferentia 컴파일 작업 상세 정보 확인
aws sagemaker describe-compilation-job \
  --compilation-job-name "neo-resnet50-inf1" \
  --region us-east-1 \
  --query '{Status: CompilationJobStatus, OutputConfig: OutputConfig, ModelArtifacts: ModelArtifacts}' \
  --output json
```

### 5. 배치 컴파일

여러 타겟 플랫폼에 대해 동시에 컴파일을 수행하는 자동화 스크립트입니다.

```python
import boto3
import json

sm_client = boto3.client('sagemaker')

# 여러 타겟 플랫폼에 대한 컴파일 작업 생성
targets = [
    {'family': 'ml_c5', 'name': 'cloud-cpu'},
    {'family': 'ml_g4dn', 'name': 'cloud-gpu-t4'},
    {'family': 'ml_inf1', 'name': 'inferentia'},
    {'family': 'jetson_xavier', 'name': 'edge-jetson'}
]

for target in targets:
    job_name = f"neo-resnet50-{target['name']}"
    
    sm_client.create_compilation_job(
        CompilationJobName=job_name,
        RoleArn='arn:aws:iam::123456789012:role/SageMakerRole',
        InputConfig={
            'S3Uri': 's3://my-bucket/models/resnet50/model.tar.gz',
            'DataInputConfig': json.dumps({'input': [1, 3, 224, 224]}),
            'Framework': 'PYTORCH'
        },
        OutputConfig={
            'S3OutputLocation': f's3://my-bucket/compiled-models/{target["name"]}/',
            'TargetDevice': target['family'] if 'jetson' in target['family'] else None,
            'TargetPlatform': {
                'Os': 'LINUX',
                'Arch': 'X86_64'
            } if 'ml_' in target['family'] else None
        },
        StoppingCondition={
            'MaxRuntimeInSeconds': 900
        }
    )
    print(f"컴파일 작업 시작: {job_name} -> {target['family']}")
```

## 아키텍처/동작 원리

### Neo 컴파일 파이프라인

Neo의 내부 동작은 다음과 같은 단계로 진행됩니다.

**1단계: 모델 파싱**

입력 모델(PyTorch, TensorFlow 등)을 프레임워크 독립적인 중간 표현(IR, Intermediate Representation)으로 변환합니다. 이 과정에서 모델의 연산 그래프가 추출됩니다.

**2단계: 그래프 최적화**

연산 그래프에 다양한 최적화 패스를 적용합니다.
- **연산 융합(Operator Fusion)**: 여러 연산을 하나로 합쳐 메모리 접근을 줄입니다.
- **상수 폴딩(Constant Folding)**: 컴파일 시점에 계산 가능한 연산을 미리 수행합니다.
- **레이아웃 변환(Layout Transformation)**: 대상 하드웨어에 최적인 데이터 레이아웃으로 변환합니다.
- **양자화(Quantization)**: 부동소수점 연산을 정수 연산으로 변환하여 속도를 향상시킵니다.

**3단계: 코드 생성**

최적화된 그래프를 대상 하드웨어에 맞는 기계어 코드로 변환합니다. NVIDIA GPU의 경우 CUDA 커널이, ARM CPU의 경우 NEON 명령어가, Inferentia의 경우 NeuronCore 명령어가 생성됩니다.

**4단계: 런타임 패키징**

생성된 코드와 DLR 런타임을 하나의 패키지로 묶어 배포 가능한 형태로 만듭니다.

### Apache TVM 기반 아키텍처

Neo의 핵심 엔진은 Apache TVM이라는 오픈소스 딥러닝 컴파일러 프레임워크입니다. TVM은 다음과 같은 구조로 동작합니다.

```
[PyTorch/TF/MXNet 모델]
         |
    [Relay IR] -- 프레임워크 독립 중간 표현
         |
    [Graph 최적화] -- 연산 융합, 상수 폴딩 등
         |
    [TIR(Tensor IR)] -- 저수준 텐서 연산 표현
         |
    [Auto-Tuning] -- 하드웨어별 최적 설정 탐색
         |
    [Code Generation] -- LLVM/CUDA/OpenCL 코드 생성
         |
    [DLR Runtime] -- 경량 실행 환경
```

### 입력 형상(Input Shape) 제약

Neo 컴파일 시 입력 형상을 고정해야 합니다. 이는 컴파일 타임 최적화를 위한 필수 요건입니다. 동적 입력 크기가 필요한 경우에는 여러 입력 형상에 대해 별도로 컴파일하거나, 패딩을 사용하여 고정 크기로 맞추는 전략이 필요합니다.

```python
# 여러 배치 크기에 대한 컴파일
batch_sizes = [1, 4, 8, 16]

for batch_size in batch_sizes:
    input_shape = {'input': [batch_size, 3, 224, 224]}
    job_name = f"neo-resnet50-batch{batch_size}"
    
    sm_client.create_compilation_job(
        CompilationJobName=job_name,
        RoleArn=role,
        InputConfig={
            'S3Uri': 's3://my-bucket/models/resnet50/model.tar.gz',
            'DataInputConfig': json.dumps(input_shape),
            'Framework': 'PYTORCH'
        },
        OutputConfig={
            'S3OutputLocation': f's3://my-bucket/compiled/batch{batch_size}/',
            'TargetPlatform': {
                'Os': 'LINUX',
                'Arch': 'X86_64',
                'Accelerator': 'NVIDIA'
            }
        },
        StoppingCondition={'MaxRuntimeInSeconds': 900}
    )
```

## 실전 활용

### 사례 1: 이미지 분류 모델 최적화 배포

ResNet50 모델을 Neo로 컴파일하여 추론 성능을 비교하는 전체 워크플로입니다.

```python
import sagemaker
from sagemaker.pytorch import PyTorchModel
import time
import json

session = sagemaker.Session()
role = sagemaker.get_execution_role()

# 원본 모델 배포
original_model = PyTorchModel(
    model_data='s3://my-bucket/models/resnet50/model.tar.gz',
    role=role,
    framework_version='2.0',
    py_version='py310',
    entry_point='inference.py'
)

original_predictor = original_model.deploy(
    initial_instance_count=1,
    instance_type='ml.c5.xlarge',
    endpoint_name='resnet50-original'
)

# Neo 컴파일 모델 배포
compiled_model = original_model.compile(
    target_instance_family='ml_c5',
    input_shape={'input': [1, 3, 224, 224]},
    output_path='s3://my-bucket/compiled/resnet50-c5/',
    role=role,
    framework='pytorch',
    framework_version='2.0'
)

compiled_predictor = compiled_model.deploy(
    initial_instance_count=1,
    instance_type='ml.c5.xlarge',
    endpoint_name='resnet50-neo-compiled'
)

# 성능 비교 테스트
import numpy as np

test_input = np.random.rand(1, 3, 224, 224).astype('float32').tobytes()

def benchmark(predictor, name, iterations=100):
    latencies = []
    for _ in range(iterations):
        start = time.time()
        predictor.predict(test_input)
        latencies.append((time.time() - start) * 1000)
    
    avg = np.mean(latencies)
    p50 = np.percentile(latencies, 50)
    p99 = np.percentile(latencies, 99)
    
    print(f"{name}: 평균={avg:.1f}ms, P50={p50:.1f}ms, P99={p99:.1f}ms")
    return {'avg': avg, 'p50': p50, 'p99': p99}

original_perf = benchmark(original_predictor, "원본 모델")
compiled_perf = benchmark(compiled_predictor, "Neo 컴파일 모델")

speedup = original_perf['avg'] / compiled_perf['avg']
print(f"속도 향상: {speedup:.2f}x")
```

### 사례 2: 엣지 디바이스 배포 (NVIDIA Jetson)

```python
# Jetson Xavier 타겟으로 컴파일
sm_client.create_compilation_job(
    CompilationJobName='resnet50-jetson-xavier',
    RoleArn=role,
    InputConfig={
        'S3Uri': 's3://my-bucket/models/resnet50/model.tar.gz',
        'DataInputConfig': '{"input": [1, 3, 224, 224]}',
        'Framework': 'PYTORCH'
    },
    OutputConfig={
        'S3OutputLocation': 's3://my-bucket/compiled/jetson-xavier/',
        'TargetDevice': 'jetson_xavier'
    },
    StoppingCondition={
        'MaxRuntimeInSeconds': 900
    }
)
```

```bash
# 컴파일된 모델 아티팩트 다운로드 (엣지 디바이스에서 실행)
aws s3 cp \
  s3://my-bucket/compiled/jetson-xavier/model-jetson_xavier.tar.gz \
  /tmp/compiled-model.tar.gz

# 아티팩트 압축 해제
tar -xzf /tmp/compiled-model.tar.gz -C /opt/ml/model/
```

엣지 디바이스에서의 실행 코드입니다.

```python
# Jetson Xavier에서 DLR로 모델 실행
import dlr
import numpy as np
import cv2
import time

# 컴파일된 모델 로드
model = dlr.DLRModel(
    model_path='/opt/ml/model/',
    dev_type='gpu',
    dev_id=0
)

# 카메라 입력 처리
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # 전처리
    input_img = cv2.resize(frame, (224, 224))
    input_img = input_img.transpose(2, 0, 1).astype('float32') / 255.0
    input_img = np.expand_dims(input_img, axis=0)
    
    # 추론
    start = time.time()
    output = model.run(input_img)
    latency = (time.time() - start) * 1000
    
    predicted_class = np.argmax(output[0])
    confidence = np.max(output[0])
    
    print(f"클래스: {predicted_class}, 신뢰도: {confidence:.4f}, 지연시간: {latency:.1f}ms")

cap.release()
```

### 사례 3: Inferentia 기반 비용 최적화

```python
# GPU vs Inferentia 비용 비교를 위한 배포

# GPU 배포 (g4dn.xlarge: $0.736/hr)
gpu_predictor = compiled_model.deploy(
    initial_instance_count=1,
    instance_type='ml.g4dn.xlarge',
    endpoint_name='resnet50-gpu'
)

# Inferentia 배포 (inf1.xlarge: $0.297/hr)
inf_model = pytorch_model.compile(
    target_instance_family='ml_inf1',
    input_shape={'input': [1, 3, 224, 224]},
    output_path='s3://my-bucket/compiled/resnet50-inf1/',
    role=role,
    framework='pytorch',
    framework_version='2.0'
)

inf_predictor = inf_model.deploy(
    initial_instance_count=1,
    instance_type='ml.inf1.xlarge',
    endpoint_name='resnet50-inferentia'
)

# 비용 대비 성능 분석
gpu_perf = benchmark(gpu_predictor, "GPU (g4dn.xlarge)")
inf_perf = benchmark(inf_predictor, "Inferentia (inf1.xlarge)")

print(f"\n=== 비용 분석 ===")
print(f"GPU 시간당 비용: $0.736")
print(f"Inferentia 시간당 비용: $0.297")
print(f"비용 절감률: {(1 - 0.297/0.736) * 100:.1f}%")
```

## 모범 사례/보안

### 컴파일 최적화 모범 사례

1. **입력 형상 최적화**: 실제 프로덕션에서 가장 자주 사용되는 배치 크기로 컴파일합니다.

2. **프레임워크 버전 일치**: 훈련 시 사용한 프레임워크 버전과 컴파일 시 지정하는 버전을 일치시킵니다.

3. **정확도 검증**: 컴파일 후 반드시 원본 모델과 컴파일된 모델의 출력을 비교하여 정확도 손실이 허용 범위 내인지 확인합니다.

4. **벤치마킹 프로토콜**: 워밍업 추론을 수행한 후 성능을 측정합니다. 처음 몇 회의 추론은 JIT 컴파일로 인해 느릴 수 있습니다.

5. **컴파일 실패 대응**: 일부 연산이 지원되지 않아 컴파일이 실패할 수 있습니다. 이 경우 모델 구조를 수정하거나 지원되는 연산으로 대체합니다.

### 보안 모범 사례

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "NeoCompilationAccess",
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateCompilationJob",
        "sagemaker:DescribeCompilationJob",
        "sagemaker:ListCompilationJobs",
        "sagemaker:StopCompilationJob"
      ],
      "Resource": "arn:aws:sagemaker:*:*:compilation-job/*"
    },
    {
      "Sid": "S3ModelAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket/models/*",
        "arn:aws:s3:::my-bucket/compiled/*"
      ]
    }
  ]
}
```

- 컴파일된 모델 아티팩트를 S3에 저장할 때 KMS 암호화를 적용합니다.
- 엣지 디바이스에 배포되는 모델의 경우, 디바이스 인증과 모델 무결성 검증을 구현합니다.
- IoT Greengrass와 통합하여 엣지 디바이스의 모델 업데이트를 안전하게 관리합니다.

```bash
# 컴파일된 모델의 S3 암호화 상태 확인
aws s3api head-object \
  --bucket my-bucket \
  --key compiled/resnet50-c5/model-ml_c5.tar.gz \
  --query '{ServerSideEncryption: ServerSideEncryption, SSEKMSKeyId: SSEKMSKeyId}'
```

## 관련 서비스 비교

### Neo vs TensorRT

| 항목 | SageMaker Neo | NVIDIA TensorRT |
|------|--------------|----------------|
| 하드웨어 지원 | 멀티 플랫폼 | NVIDIA GPU 전용 |
| 관리 방식 | 완전 관리형 | 셀프 관리 |
| 프레임워크 지원 | 다양 (PyTorch, TF, MXNet 등) | ONNX, TF-TRT |
| 최적화 수준 | 범용 최적화 | GPU 특화 최적화 (더 깊음) |
| 비용 | 컴파일 비용 무료 | 오픈소스 무료 |
| 적합한 사용 사례 | 멀티 플랫폼 배포 | NVIDIA GPU 최대 성능 |

### Neo vs ONNX Runtime

| 항목 | SageMaker Neo | ONNX Runtime |
|------|--------------|-------------|
| 표준 | 독자 (TVM 기반) | ONNX 표준 |
| 하드웨어 최적화 | 자동 | Execution Provider별 |
| AWS 통합 | 네이티브 | 추가 구성 필요 |
| 동적 입력 | 미지원 (고정) | 지원 |
| 생태계 | AWS 한정 | 멀티 클라우드 |

### Neo vs AWS Inferentia (Neuron SDK)

| 항목 | SageMaker Neo | Neuron SDK |
|------|--------------|------------|
| 대상 | 범용 하드웨어 | Inferentia 전용 |
| 최적화 깊이 | 범용 | Inferentia 특화 (더 깊음) |
| 사용 복잡도 | 낮음 | 중간 |
| 성능 | 좋음 | Inferentia에서 최고 |
| 제어 수준 | 낮음 | 높음 (파이프라인 스케줄링 등) |

## 요약

Amazon SageMaker Neo는 ML 모델의 하드웨어 최적화와 크로스 플랫폼 배포를 단순화하는 핵심 서비스입니다. 주요 내용을 정리하면 다음과 같습니다.

- Neo는 Apache TVM 기반의 컴파일러로, 모델을 특정 하드웨어에 최적화하여 추론 성능을 최대 25배 향상시킵니다.
- 클라우드(Intel/AMD/NVIDIA), 엣지(Jetson/Raspberry Pi), 모바일(Android/iOS) 등 광범위한 플랫폼을 지원합니다.
- AWS Inferentia와 통합하여 GPU 대비 최대 70%의 비용 절감이 가능합니다.
- DLR(Deep Learning Runtime)을 통해 컴파일된 모델을 경량 환경에서 실행할 수 있습니다.
- 컴파일 시 입력 형상이 고정되므로, 실제 프로덕션 워크로드에 맞는 형상을 선택하는 것이 중요합니다.
- 컴파일 후 반드시 정확도 검증과 성능 벤치마킹을 수행해야 합니다.
- 엣지 배포 시에는 IoT Greengrass와의 통합을 통해 안전한 모델 업데이트 파이프라인을 구축하는 것을 권장합니다.

Neo는 특히 다양한 하드웨어 플랫폼에 동일한 모델을 배포해야 하거나, 추론 비용을 최적화해야 하는 프로젝트에서 큰 가치를 제공합니다.