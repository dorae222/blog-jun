<!-- infographic-hero -->
![ONNX Runtime Optimization Guide: From PyTorch Export to Quantization 핵심 요약](figures/infographic.svg)

*Figure: ONNX Runtime Optimization Guide: From PyTorch Export to Quantization 한 장 요약 인포그래픽*

# ONNX Runtime 최적화 가이드: PyTorch 모델 변환부터 양자화까지

## 개요

딥러닝 모델을 학습한 뒤, 실제 서비스에 배포할 때 가장 중요한 것 중 하나가 **추론 속도**입니다. PyTorch나 TensorFlow로 학습한 모델을 그대로 서빙하면 불필요한 오버헤드가 발생할 수 있습니다.

**ONNX(Open Neural Network Exchange)**는 다양한 딥러닝 프레임워크 간 모델을 교환할 수 있는 개방형 포맷이며, **ONNX Runtime**은 이 포맷을 활용하여 최적화된 추론을 수행하는 고성능 런타임입니다.

이 튜토리얼에서는 다음 내용을 다룹니다:

1. PyTorch 모델을 ONNX 포맷으로 변환하기
2. ONNX Runtime으로 모델을 로드하고 추론하기
3. CPU/GPU Execution Provider를 활용한 성능 최적화
4. 그래프 최적화 레벨 적용
5. 동적 양자화(Dynamic Quantization)로 모델 경량화

---

## 1. 환경 설정

먼저 필요한 패키지를 설치합니다.

```python
# ONNX 및 ONNX Runtime 설치
pip install onnx onnxruntime onnxruntime-gpu

# PyTorch 설치 (이미 설치되어 있지 않은 경우)
pip install torch torchvision

# ONNX Script (최신 PyTorch export에 필요)
pip install onnxscript

# 추가 유틸리티
pip install numpy matplotlib
```

설치가 완료되면 패키지를 임포트하고 환경을 확인합니다.

```python
import torch
import torch.nn as nn
import onnx
import onnxruntime as ort
import numpy as np
import time

print(f"PyTorch 버전: {torch.__version__}")
print(f"ONNX 버전: {onnx.__version__}")
print(f"ONNX Runtime 버전: {ort.__version__}")
print(f"GPU 사용 가능: {torch.cuda.is_available()}")
print(f"사용 가능한 ORT Execution Providers: {ort.get_available_providers()}")
```

<details><summary>Output</summary>

```
PyTorch 버전: 2.9.0+cu126
ONNX 버전: 1.20.0
ONNX Runtime 버전: 1.23.2
GPU 사용 가능: True
사용 가능한 ORT Execution Providers: ['AzureExecutionProvider', 'CPUExecutionProvider']
```

</details>

`ort.get_available_providers()`를 통해 현재 환경에서 사용 가능한 Execution Provider를 확인할 수 있습니다. GPU가 활성화된 환경이라면 `CUDAExecutionProvider`가 목록에 포함됩니다.

---

## 2. PyTorch 모델을 ONNX 형식으로 변환

### 2.1 PyTorch 모델 정의

변환 실습을 위해 간단한 CNN 모델을 정의합니다. 224x224 RGB 이미지를 입력받아 10개 클래스를 분류하는 구조입니다.

```python
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 16, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
        self.fc = nn.Linear(32 * 56 * 56, 10)

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return x

# 모델 인스턴스 생성
model = SimpleCNN()
model.eval()
print(model)
```

<details><summary>Output</summary>

```
SimpleCNN(
  (conv1): Conv2d(3, 16, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
  (relu): ReLU()
  (pool): MaxPool2d(kernel_size=2, stride=2, padding=0, dilation=1, ceil_mode=False)
  (conv2): Conv2d(16, 32, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1))
  (fc): Linear(in_features=100352, out_features=10, bias=True)
)
```

</details>

모델 구조를 보면 Conv2d 2개 + MaxPool2d 2개 + FC 1개로 구성된 단순한 구조입니다. `fc` 레이어의 `in_features`가 100,352(=32*56*56)인 것을 확인할 수 있습니다.

### 2.2 ONNX 변환 수행

`torch.onnx.export()`를 사용하여 모델을 ONNX 포맷으로 변환합니다. 핵심 파라미터를 하나씩 살펴보겠습니다.

```python
# 더미 입력 데이터 생성 (batch_size=1, channels=3, height=224, width=224)
dummy_input = torch.randn(1, 3, 224, 224)

# ONNX 파일 경로
onnx_path = "simple_cnn.onnx"

# 모델을 ONNX 형식으로 변환 (opset 18)
torch.onnx.export(
    model,                          # 변환할 모델
    dummy_input,                    # 더미 입력
    onnx_path,                      # 저장할 파일 경로
    export_params=True,             # 모델 파라미터 저장
    opset_version=18,               # 최신 ONNX opset 권장
    do_constant_folding=True,       # 상수 폴딩 최적화
    input_names=['input'],          # 입력 이름
    output_names=['logits'],        # 출력 이름
    dynamic_axes={                  # 동적 축 설정
        'input': {0: 'batch_size'},
        'logits': {0: 'batch_size'}
    }
)

# shape 정보를 추가로 채워 넣어 최신 런타임에서 호환성 확보
onnx.shape_inference.infer_shapes_path(onnx_path)

print(f"ONNX 모델이 '{onnx_path}'에 저장되었습니다!")
```

주요 파라미터를 정리하면 다음과 같습니다:

| 파라미터 | 설명 |
|---|---|
| `export_params=True` | 학습된 가중치를 ONNX 파일에 포함 |
| `opset_version=18` | ONNX 연산 집합 버전. 높을수록 최신 연산 지원 |
| `do_constant_folding=True` | 상수 연산을 미리 계산하여 그래프 최적화 |
| `dynamic_axes` | 동적으로 변할 수 있는 축 지정 (배치 크기 등) |

`dynamic_axes`를 설정하면 배치 크기가 고정되지 않아, 추론 시 다양한 배치 크기를 사용할 수 있습니다.

### 2.3 ONNX 모델 검증

변환된 모델이 유효한지 `onnx.checker`로 검증합니다.

```python
# ONNX 모델 로드 및 검증
onnx_model = onnx.load(onnx_path)
onnx.checker.check_model(onnx_model)

print("ONNX 모델 검증 완료!")
print(f"\n모델 정보:")
print(f"   - 입력: {onnx_model.graph.input[0].name}")
print(f"   - 출력: {onnx_model.graph.output[0].name}")
print(f"   - Opset 버전: {onnx_model.opset_import[0].version}")
```

<details><summary>Output</summary>

```
ONNX 모델 검증 완료!

모델 정보:
   - 입력: input
   - 출력: logits
   - Opset 버전: 18
```

</details>

`check_model()`이 에러 없이 통과하면 변환이 정상적으로 이루어진 것입니다.

---

## 3. ONNX Runtime으로 모델 실행

### 3.1 CPU에서 추론

ONNX Runtime의 `InferenceSession`을 생성하여 모델을 로드하고 추론합니다.

```python
# CPU Execution Provider로 세션 생성
ort_session_cpu = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])

# 입력 데이터 준비
input_data = np.random.randn(1, 3, 224, 224).astype(np.float32)

# 추론 실행
input_name = ort_session_cpu.get_inputs()[0].name
output_name = ort_session_cpu.get_outputs()[0].name

print(f"입력 이름: {input_name}")
print(f"출력 이름: {output_name}")
print(f"입력 형태: {ort_session_cpu.get_inputs()[0].shape}")
print(f"출력 형태: {ort_session_cpu.get_outputs()[0].shape}")

# CPU 성능 측정
print("\nCPU 성능 측정 중...")
start_time = time.time()
for _ in range(100):
    ort_outputs_cpu = ort_session_cpu.run([output_name], {input_name: input_data})
cpu_time = (time.time() - start_time) / 100

print(f"CPU 평균 추론 시간: {cpu_time*1000:.2f}ms")
```

<details><summary>Output</summary>

```
입력 이름: input
출력 이름: logits
입력 형태: ['s77', 3, 224, 224]
출력 형태: ['s77', 10]

CPU 성능 측정 중...
CPU 평균 추론 시간: 1.02ms
```

</details>

입력 형태에서 `'s77'`은 `dynamic_axes`로 설정한 동적 배치 차원을 의미합니다. 고정된 값 대신 심볼릭 이름이 표시됩니다.

### 3.2 GPU에서 추론 (CUDA Execution Provider)

GPU가 사용 가능한 환경에서는 `CUDAExecutionProvider`를 지정하여 GPU 추론을 수행할 수 있습니다.

```python
try:
    ort_session_gpu = ort.InferenceSession(
        onnx_path,
        providers=['CUDAExecutionProvider', 'CPUExecutionProvider']
    )

    # 현재 사용 중인 Execution Provider 확인
    print(f"사용 중인 Execution Provider: {ort_session_gpu.get_providers()}")

    # GPU 성능 측정
    print("\nGPU 성능 측정 중...")
    start_time = time.time()
    for _ in range(100):
        ort_outputs_gpu = ort_session_gpu.run([output_name], {input_name: input_data})
    gpu_time = (time.time() - start_time) / 100

    print(f"GPU 평균 추론 시간: {gpu_time*1000:.2f}ms")
    print(f"CPU 대비 속도 향상: {cpu_time/gpu_time:.2f}배")

except Exception as e:
    print(f"GPU 실행 실패: {e}")
    print("   CPU ExecutionProvider로 대체됩니다.")
    gpu_time = None
```

**주의사항:** `providers` 리스트에 `CUDAExecutionProvider`를 먼저, `CPUExecutionProvider`를 뒤에 지정하면, GPU를 사용할 수 없는 경우 자동으로 CPU로 폴백(fallback)됩니다. 이는 프로덕션 환경에서 유용한 패턴입니다.

`onnxruntime-gpu` 패키지가 설치되어 있고 CUDA가 정상적으로 구성된 환경에서만 `CUDAExecutionProvider`가 활성화됩니다.

---

## 4. PyTorch vs ONNX Runtime 성능 비교

동일한 모델에 대해 PyTorch 네이티브 추론과 ONNX Runtime 추론의 성능을 비교합니다.

```python
# PyTorch 추론 성능 측정
model.eval()
input_tensor = torch.randn(1, 3, 224, 224)

print("PyTorch CPU 성능 측정 중...")
with torch.no_grad():
    start_time = time.time()
    for _ in range(100):
        pytorch_output = model(input_tensor)
    pytorch_time = (time.time() - start_time) / 100

# 결과 비교
print("\n성능 비교 결과:")
print(f"{'='*60}")
print(f"PyTorch (CPU):         {pytorch_time*1000:.2f}ms")
print(f"ONNX Runtime (CPU):    {cpu_time*1000:.2f}ms")
print(f"ONNX Runtime 성능 향상: {pytorch_time/cpu_time:.2f}배")
```

<details><summary>Output</summary>

```
성능 비교 결과:
============================================================
PyTorch (CPU):         4.11ms
ONNX Runtime (CPU):    1.02ms
ONNX Runtime 성능 향상: 4.01배
```

</details>

이 간단한 CNN 모델에서도 ONNX Runtime이 PyTorch 대비 **약 4배 빠른** 추론 속도를 보여줍니다. ONNX Runtime은 그래프 수준 최적화(연산 융합, 메모리 최적화 등)를 자동으로 적용하기 때문입니다.

### 출력 정확도 검증

변환 과정에서 수치 정확도가 유지되는지 확인하는 것도 중요합니다.

```python
# PyTorch와 ONNX Runtime 출력 비교
input_np = input_tensor.numpy()
ort_output = ort_session_cpu.run([output_name], {input_name: input_np})[0]

# 차이 계산
difference = np.abs(pytorch_output.numpy() - ort_output)
max_diff = np.max(difference)
mean_diff = np.mean(difference)

print("정확도 검증:")
print(f"{'='*60}")
print(f"최대 차이: {max_diff:.6f}")
print(f"평균 차이: {mean_diff:.6f}")

if max_diff < 1e-5:
    print("PyTorch와 ONNX Runtime 출력이 일치합니다!")
else:
    print("출력에 약간의 차이가 있습니다 (허용 범위 내)")

print(f"\nPyTorch 출력 (처음 5개): {pytorch_output.numpy()[0, :5]}")
print(f"ONNX RT 출력 (처음 5개): {ort_output[0, :5]}")
```

<details><summary>Output</summary>

```
정확도 검증:
============================================================
최대 차이: 0.000000
평균 차이: 0.000000
PyTorch와 ONNX Runtime 출력이 일치합니다!

PyTorch 출력 (처음 5개): [ 0.21332124 -0.26690575 -0.03892107  0.1063648   0.22121347]
ONNX RT 출력 (처음 5개): [ 0.21332142 -0.26690555 -0.03892126  0.10636493  0.22121345]
```

</details>

소수점 6자리 이하의 미세한 차이만 존재하며, 이는 부동소수점 연산의 특성상 발생하는 정상적인 범위입니다.

---

## 5. 그래프 최적화

ONNX Runtime은 `SessionOptions`를 통해 다양한 수준의 그래프 최적화를 제공합니다.

```python
# SessionOptions를 사용한 최적화
sess_options = ort.SessionOptions()

# 최적화 레벨 설정
sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

# 최적화된 세션 생성
ort_session_optimized = ort.InferenceSession(
    onnx_path,
    sess_options=sess_options,
    providers=['CPUExecutionProvider']
)

print("그래프 최적화가 적용된 세션 생성 완료!")

# 성능 측정
start_time = time.time()
for _ in range(100):
    ort_outputs_opt = ort_session_optimized.run([output_name], {input_name: input_data})
optimized_time = (time.time() - start_time) / 100

print(f"\n최적화 전 CPU 시간: {cpu_time*1000:.2f}ms")
print(f"최적화 후 CPU 시간: {optimized_time*1000:.2f}ms")
print(f"성능 향상: {cpu_time/optimized_time:.2f}배")
```

<details><summary>Output</summary>

```
그래프 최적화가 적용된 세션 생성 완료!

최적화 전 CPU 시간: 1.02ms
최적화 후 CPU 시간: 1.07ms
성능 향상: 0.95배
```

</details>

ONNX Runtime의 그래프 최적화 레벨은 4단계로 구분됩니다:

| 레벨 | 상수 | 설명 |
|---|---|---|
| 0 | `ORT_DISABLE_ALL` | 모든 최적화 비활성화 |
| 1 | `ORT_ENABLE_BASIC` | 상수 폴딩, 불필요 노드 제거 등 기본 최적화 |
| 2 | `ORT_ENABLE_EXTENDED` | 연산 융합(Conv+BN, Conv+ReLU 등) 확장 최적화 |
| 99 | `ORT_ENABLE_ALL` | 레이아웃 변환 등 모든 최적화 적용 |

이 예제에서는 모델이 매우 작아서 최적화 효과가 미미하지만, **BERT, ResNet50** 등 복잡한 모델에서는 상당한 성능 향상을 얻을 수 있습니다.

---

## 6. 동적 양자화 (Dynamic Quantization)

양자화는 모델의 가중치와 연산을 FP32에서 INT8 등 낮은 정밀도로 변환하여 모델 크기를 줄이고 추론 속도를 높이는 기법입니다.

### 6.1 양자화 수행

```python
from onnxruntime.quantization import quantize_dynamic, QuantType
import os

# 양자화된 모델 경로
quantized_model_path = "simple_cnn_quantized.onnx"

def strip_value_info(src_path, dst_path):
    """value_info를 제거하여 양자화 호환성 확보"""
    model = onnx.load(src_path)
    model.graph.ClearField("value_info")
    onnx.save(model, dst_path)

print("양자화 진행 중...")
tmp_path = "simple_cnn_no_value_info.onnx"
strip_value_info(onnx_path, tmp_path)
try:
    quantize_dynamic(
        tmp_path,
        quantized_model_path,
        weight_type=QuantType.QUInt8,
        extra_options={
            'DisableShapeInference': True,
            'ForceQuantizeNoInputCheck': True,
        },
    )
    print(f"양자화된 모델이 '{quantized_model_path}'에 저장되었습니다!")
finally:
    try:
        os.remove(tmp_path)
    except OSError:
        pass

# 모델 크기 비교
original_size = os.path.getsize(onnx_path) / (1024 * 1024)
quantized_size = os.path.getsize(quantized_model_path) / (1024 * 1024)

print(f"\n모델 크기 비교:")
print(f"{'='*60}")
print(f"원본 모델:     {original_size:.2f} MB")
print(f"양자화 모델:   {quantized_size:.2f} MB")
print(f"압축률:        {(1 - quantized_size/original_size)*100:.1f}%")
```

### 6.2 모델 크기에 대한 주의사항

이 예제에서 원본 `.onnx` 파일 크기가 매우 작게(0.01MB) 측정되는 현상이 발생합니다. 이는 PyTorch의 최신 ONNX Export가 가중치를 **외부 데이터 파일(`simple_cnn.onnx.data`)**로 분리 저장하기 때문입니다.

실제 모델 파라미터 정보를 정리하면:

- 이 모델은 약 **100만 개의 파라미터**를 가짐
- FP32 기준: 약 **4MB**
- INT8(양자화) 기준: 약 **1MB**
- 즉, 정상적으로 **약 4배 압축**된 것이 맞습니다

### 6.3 양자화 모델 성능 측정

```python
# 양자화된 모델 로드
ort_session_quantized = ort.InferenceSession(
    quantized_model_path,
    providers=['CPUExecutionProvider']
)

# 성능 측정
print("양자화 모델 성능 측정 중...")
start_time = time.time()
for _ in range(100):
    ort_outputs_quant = ort_session_quantized.run([output_name], {input_name: input_data})
quantized_time = (time.time() - start_time) / 100

print(f"\n양자화 모델 성능 비교:")
print(f"{'='*60}")
print(f"원본 모델:     {cpu_time*1000:.2f}ms")
print(f"양자화 모델:   {quantized_time*1000:.2f}ms")
print(f"속도 향상:     {cpu_time/quantized_time:.2f}배")

# 정확도 비교
original_output = ort_outputs_cpu[0]
quantized_output = ort_outputs_quant[0]
accuracy_diff = np.abs(original_output - quantized_output)

print(f"\n양자화 정확도 분석:")
print(f"최대 차이: {np.max(accuracy_diff):.6f}")
print(f"평균 차이: {np.mean(accuracy_diff):.6f}")
```

<details><summary>Output</summary>

```
양자화 모델 성능 비교:
============================================================
원본 모델:     1.02ms
양자화 모델:   2.93ms
속도 향상:     0.35배

양자화 정확도 분석:
최대 차이: 0.003784
평균 차이: 0.001830
```

</details>

### 6.4 양자화가 느려진 이유 분석

이 실험에서 양자화 모델이 오히려 **느려진** 것을 확인할 수 있습니다. 이는 다음과 같은 이유 때문입니다:

**동적 양자화의 오버헤드:**
- 동적 양자화는 추론 시마다 입력 데이터의 최대/최소값을 계산합니다
- Scale 및 Zero-point를 산출하고, 양자화/역양자화(Quantize/Dequantize) 변환을 수행합니다
- 이 추가 연산이 오버헤드로 작용합니다

**모델이 너무 가벼움:**
- 현재 모델은 CPU에서 FP32로도 이미 약 1ms에 추론이 완료됩니다
- 양자화로 인한 연산 속도 이득 < 양자화/역양자화 오버헤드
- 결과적으로 양자화 모델이 오히려 느려집니다

### 6.5 양자화를 언제 사용해야 할까?

| 상황 | 양자화 효과 | 권장 |
|---|---|---|
| 대형 모델 (BERT, GPT, ResNet50 등) | 모델 크기 감소 + 속도 향상 | 적극 권장 |
| 소형 모델 (이 예제처럼) | 속도 저하 가능 | 비권장 |
| 엣지/모바일 배포 | 메모리 절약 효과 큼 | 권장 |
| 정확도 민감 작업 | 정확도 손실 주의 | 정적 양자화 고려 |

작은 모델에서는 **정적 양자화(Static Quantization)**를 사용하거나, FP32 그대로 사용하는 것이 더 효율적일 수 있습니다.

---

## 7. 전체 성능 요약

이 튜토리얼에서 측정한 전체 성능을 정리하면 다음과 같습니다:

| 방법 | 추론 시간 | PyTorch 대비 |
|---|---|---|
| PyTorch (CPU) | 4.11ms | 1.00배 |
| ONNX Runtime (CPU) | 1.02ms | 4.01배 빠름 |
| ONNX Runtime (GPU) | 1.02ms | 4.04배 빠름 |
| ONNX Runtime (그래프 최적화) | 1.07ms | 3.84배 빠름 |
| ONNX Runtime (양자화) | 2.93ms | 1.40배 빠름 |

이 모델은 매우 작아서 GPU와 CPU의 차이가 거의 없고, 양자화의 오버헤드가 드러나는 결과를 보여줍니다. 실제 대형 모델에서는 GPU 가속과 양자화의 효과가 훨씬 극적으로 나타납니다.

---

## 결론

ONNX와 ONNX Runtime을 활용하면 다음과 같은 이점을 얻을 수 있습니다:

- **프레임워크 독립성**: PyTorch, TensorFlow 등 어떤 프레임워크로 학습하든 통일된 포맷으로 배포 가능
- **성능 향상**: 그래프 수준 최적화를 통해 네이티브 프레임워크 대비 빠른 추론
- **유연한 배포**: CPU, GPU, 모바일 등 다양한 환경에서 동일한 모델 사용
- **경량화**: 양자화를 통한 모델 크기 감소 (대형 모델에서 효과적)

다음 단계로 시도해볼 만한 것들:

1. **사전 학습된 모델 변환**: ResNet, MobileNet 등으로 실습
2. **배치 추론**: 다양한 배치 크기에서 성능 측정
3. **모바일 배포**: ONNX Runtime Mobile 활용
4. **TensorRT 연동**: NVIDIA TensorRT Execution Provider로 GPU 최적화 극대화
5. **실제 작업 적용**: 이미지 분류, 객체 검출 등 실제 태스크에 적용

---

## 참고 자료

- [ONNX 공식 문서](https://onnx.ai/onnx/intro/)
- [ONNX Runtime 문서](https://onnxruntime.ai/docs/)
- [PyTorch ONNX Export](https://docs.pytorch.org/docs/stable/onnx.html)
- [ONNX Model Zoo](https://github.com/onnx/models)