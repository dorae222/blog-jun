# MFU 최적화 실전 프로젝트

## 소개

이 튜토리얼에서는 딥러닝 모델의 **MFU(Model FLOPs Utilization)**를 측정하고, 다양한 최적화 기법을 적용하여 성능을 개선하는 실전 프로젝트를 수행합니다.

### 프로젝트 단계

1. **모델 선정**: 최적화 대상 모델 선택 (ResNet18)
2. **베이스라인 측정**: 최적화 전 성능 프로파일링 및 MFU 수치 기록
3. **병목 분석**: PyTorch Profiler로 병목 레이어 및 연산 식별
4. **최적화 적용**: TorchScript, Mixed Precision, Channels Last 등
5. **결과 분석**: 최적화 전/후 MFU 비교 및 성능 향상 측정

### 평가 기준

- **우수**: MFU 20% 이상 향상
- **양호**: MFU 10-20% 향상
- **기본**: MFU 5% 이상 향상

---

## 1단계: 환경 설정 및 라이브러리 임포트

```python
import torch
import torch.nn as nn
import torchvision.models as models
import time
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from torch.profiler import profile, ProfilerActivity, record_function
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# 시드 설정
torch.manual_seed(42)
np.random.seed(42)

# 디바이스 설정
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")
if device.type == 'cuda':
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"Memory Available: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
```

<details><summary>Output</summary>

```
Using device: cuda
GPU: NVIDIA A100-SXM4-40GB
Memory Available: 42.47 GB
```

</details>

---

## 2단계: 모델 선정

이 프로젝트에서는 **ResNet18**을 사용합니다. 비교적 가벼우면서도 실용적인 모델로, 최적화 효과를 명확하게 확인할 수 있습니다.

```python
model_name = "ResNet18"
model = models.resnet18(pretrained=False)
input_shape = (1, 3, 224, 224)
theoretical_flops = 1.814e9  # 약 1.8 GFLOPs

model = model.to(device)
model.eval()

print(f"선택된 모델: {model_name}")
print(f"입력 shape: {input_shape}")
print(f"이론적 FLOPs: {theoretical_flops/1e9:.2f} GFLOPs")

total_params = sum(p.numel() for p in model.parameters())
trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print(f"전체 파라미터: {total_params:,}")
print(f"학습 가능 파라미터: {trainable_params:,}")
```

<details><summary>Output</summary>

```
선택된 모델: ResNet18
입력 shape: (1, 3, 224, 224)
이론적 FLOPs: 1.81 GFLOPs
전체 파라미터: 11,689,512
학습 가능 파라미터: 11,689,512
```

</details>

### 모델 선택 가이드

환경에 따라 다른 모델을 선택할 수도 있습니다:

| 난이도 | 모델 | 메모리 |
|--------|------|--------|
| 초급 | ResNet18, MobileNetV2 | ~2-4GB |
| 중급 | BERT-small, ViT-tiny | ~4-8GB |
| 고급 | EfficientNet, YOLOv5-small | ~8-12GB |

---

## 3단계: 베이스라인 MFU 측정

MFU = (실제 달성 FLOPs / 하드웨어 최대 FLOPs) x 100%

### GPU Peak FLOPs 설정

```python
def get_gpu_peak_flops(device_name: str) -> float:
    """GPU의 이론적 최대 FP32 FLOPs를 반환합니다."""
    gpu_specs = {
        'T4': 8.1,        # Tesla T4
        'P100': 9.3,      # Tesla P100
        'V100': 15.7,     # Tesla V100
        'A100': 19.5,     # A100 (FP32)
        'RTX': 10.0,      # 일반 RTX 계열
    }
    for key, value in gpu_specs.items():
        if key in device_name:
            return value * 1e12
    return 8.1e12  # 기본값 (T4 기준)
```

### 베이스라인 성능 측정

```python
def measure_baseline_performance(model, input_shape, num_iterations=100, warmup=10):
    """베이스라인 성능을 측정합니다."""
    model.eval()
    dummy_input = torch.randn(*input_shape).to(device)

    # Warmup
    with torch.no_grad():
        for _ in range(warmup):
            _ = model(dummy_input)

    if device.type == 'cuda':
        torch.cuda.synchronize()

    # 실제 측정
    inference_times = []
    with torch.no_grad():
        for i in range(num_iterations):
            start = time.time()
            _ = model(dummy_input)
            if device.type == 'cuda':
                torch.cuda.synchronize()
            end = time.time()
            inference_times.append(end - start)

    avg_time = np.mean(inference_times)
    achieved_flops = theoretical_flops / avg_time

    device_name = torch.cuda.get_device_name(0) if device.type == 'cuda' else 'CPU'
    peak_flops = get_gpu_peak_flops(device_name)
    mfu = (achieved_flops / peak_flops) * 100

    return {
        'avg_time_ms': avg_time * 1000,
        'std_time_ms': np.std(inference_times) * 1000,
        'throughput_fps': 1.0 / avg_time,
        'achieved_flops': achieved_flops,
        'peak_flops': peak_flops,
        'mfu_percent': mfu,
        'device_name': device_name
    }, inference_times

baseline_results, baseline_times = measure_baseline_performance(model, input_shape)
```

<details><summary>Output (베이스라인 성능)</summary>

```
============================================================
              BASELINE Performance
============================================================
Device: NVIDIA A100-SXM4-40GB

[Latency]
  Average: 2.78 ms (+/-0.46)
  Min: 2.45 ms
  Max: 4.21 ms

[Throughput]
  FPS: 359.46

[FLOPs Utilization]
  Achieved FLOPs: 0.65 TFLOPs
  Peak FLOPs: 19.50 TFLOPs
  MFU: 3.34%
============================================================
```

</details>

베이스라인 MFU는 약 3.34%입니다. A100의 FP32 피크 성능이 19.5 TFLOPS인데, 실제로는 0.65 TFLOPS만 활용하고 있다는 의미입니다.

---

## 4단계: 병목 분석 (PyTorch Profiler)

PyTorch Profiler를 사용하여 어떤 연산이 시간을 많이 소비하는지 분석합니다.

```python
def profile_model(model, input_shape, num_iterations=10):
    """PyTorch Profiler를 사용하여 모델을 프로파일링합니다."""
    model.eval()
    dummy_input = torch.randn(*input_shape).to(device)

    with profile(
        activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
        record_shapes=True,
        profile_memory=True,
        with_stack=True
    ) as prof:
        with record_function("model_inference"):
            for _ in range(num_iterations):
                with torch.no_grad():
                    _ = model(dummy_input)

    return prof

prof = profile_model(model, input_shape)

# CPU 시간 기준 상위 10개 연산
print(prof.key_averages().table(sort_by="cpu_time_total", row_limit=10))

# CUDA 시간 기준 상위 10개 연산
print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))
```

<details><summary>Output (CPU 시간 기준 상위 연산)</summary>

```
Name                          Self CPU    CPU total   Self CUDA   CUDA total
---                           --------    ---------   ---------   ----------
model_inference                25.2ms      78.8ms       0.0us       8.5ms
aten::conv2d                    0.9ms      23.2ms       0.0us       6.4ms
aten::batch_norm                1.0ms      22.5ms       0.0us       1.1ms
aten::cudnn_convolution         9.6ms      16.9ms       6.4ms       6.4ms
aten::cudnn_batch_norm          9.8ms      17.5ms       1.1ms       1.1ms
cudaLaunchKernel                7.3ms       7.3ms       0.0us       0.0us
```

</details>

### 분석 결과

- **cudnn_convolution**: CUDA 시간의 75%를 차지 (6.4ms / 8.5ms)
- **cudnn_batch_norm**: CUDA 시간의 13% 차지
- **nchwToNhwcKernel**: 메모리 레이아웃 변환에 2.6ms 소비 (31%)

메모리 레이아웃 변환(NCHW -> NHWC)이 상당한 시간을 차지하고 있어, **Channels Last 메모리 포맷**이 효과적일 수 있음을 시사합니다.

### 메모리 사용량 분석

```python
# 메모리 사용량 기준 상위 연산
print(prof.key_averages().table(sort_by="self_cuda_memory_usage", row_limit=10))
```

<details><summary>Output</summary>

```
Name                          Self CUDA Mem
---                           -------------
aten::cudnn_convolution         94.75 MB
aten::empty                     94.75 MB
aten::max_pool2d_with_indices   22.97 MB
```

</details>

Convolution 연산이 가장 많은 GPU 메모리를 사용합니다.

---

## 5단계: 최적화 적용

### 5-1. TorchScript 최적화 (Operator Fusion)

TorchScript는 모델을 정적 그래프로 변환하여 연산 최적화(fusion, 불필요한 연산 제거 등)를 적용합니다.

```python
dummy_input = torch.randn(*input_shape).to(device)

# TorchScript로 변환
scripted_model = torch.jit.trace(model, dummy_input)
scripted_model = torch.jit.optimize_for_inference(scripted_model)

# 성능 측정
scripted_results, scripted_times = measure_baseline_performance(scripted_model, input_shape)

speedup = baseline_results['avg_time_ms'] / scripted_results['avg_time_ms']
mfu_improvement = scripted_results['mfu_percent'] - baseline_results['mfu_percent']
print(f"Speedup: {speedup:.2f}x")
print(f"MFU Improvement: {mfu_improvement:+.2f}%")
```

<details><summary>Output</summary>

```
============================================================
              TorchScript Optimized
============================================================
Device: NVIDIA A100-SXM4-40GB

[Latency]
  Average: 1.19 ms (+/-0.09)

[Throughput]
  FPS: 840.58

[FLOPs Utilization]
  Achieved FLOPs: 1.52 TFLOPs
  Peak FLOPs: 19.50 TFLOPs
  MFU: 7.82%
============================================================

Speedup: 2.34x
MFU Improvement: +4.48%
```

</details>

TorchScript 변환만으로 **2.34배 속도 향상**, MFU가 3.34%에서 7.82%로 **+4.48% 개선**되었습니다. 이는 연산 그래프 최적화와 operator fusion의 효과입니다.

### 5-2. Dynamic Quantization (INT8)

Dynamic Quantization은 INT8을 사용하여 연산을 경량화합니다. 다만 현재 PyTorch에서는 **CPU에서만 지원**됩니다.

```python
# CPU에서만 동작하는 Dynamic Quantization
if device.type == 'cpu':
    quantized_model = torch.quantization.quantize_dynamic(
        model.cpu(),
        {nn.Linear, nn.Conv2d},
        dtype=torch.qint8
    )
    # 성능 측정 및 모델 크기 비교
else:
    print("Dynamic quantization은 CPU에서만 지원됩니다.")
    print("GPU 추론에는 TensorRT 또는 ONNX Runtime with static quantization을 사용하세요.")
```

GPU 환경에서는 TensorRT나 ONNX Runtime을 사용한 static quantization이 권장됩니다.

### 5-3. Mixed Precision (FP16) with AMP

Automatic Mixed Precision(AMP)은 연산별로 FP16/FP32를 자동으로 결정하여 속도와 정확도의 균형을 맞춥니다.

```python
def measure_amp_performance(model, input_shape, num_iterations=100, warmup=10):
    model.eval()
    dummy_input = torch.randn(*input_shape).to(device)

    with torch.no_grad():
        with torch.cuda.amp.autocast():
            for _ in range(warmup):
                _ = model(dummy_input)

    torch.cuda.synchronize()

    inference_times = []
    with torch.no_grad():
        with torch.cuda.amp.autocast():
            for _ in range(num_iterations):
                start = time.time()
                _ = model(dummy_input)
                torch.cuda.synchronize()
                end = time.time()
                inference_times.append(end - start)

    avg_time = np.mean(inference_times)
    achieved_flops = theoretical_flops / avg_time
    peak_flops = get_gpu_peak_flops(torch.cuda.get_device_name(0))
    mfu = (achieved_flops / peak_flops) * 100

    return {
        'avg_time_ms': avg_time * 1000,
        'throughput_fps': 1.0 / avg_time,
        'mfu_percent': mfu,
        # ...
    }, inference_times

amp_results, amp_times = measure_amp_performance(model, input_shape)

speedup = baseline_results['avg_time_ms'] / amp_results['avg_time_ms']
mfu_improvement = amp_results['mfu_percent'] - baseline_results['mfu_percent']
print(f"Speedup: {speedup:.2f}x")
print(f"MFU Improvement: {mfu_improvement:+.2f}%")
```

<details><summary>Output</summary>

```
============================================================
              Mixed Precision (FP16)
============================================================
Latency Average: 3.35 ms
Throughput FPS: 298.89
MFU: 2.78%

Speedup: 0.83x
MFU Improvement: -0.56%
```

</details>

흥미롭게도 Mixed Precision이 오히려 느려졌습니다. 이는 ResNet18이 비교적 작은 모델이라 AMP의 오버헤드가 이점을 상쇄하기 때문입니다. **더 큰 모델(ResNet50, BERT 등)에서는 AMP의 효과가 분명하게 나타납니다.**

### 5-4. Channels Last Memory Format

GPU의 convolution 커널은 NHWC(Channels Last) 포맷에 최적화되어 있는 경우가 많습니다. 메모리 레이아웃을 변환하여 성능을 개선할 수 있습니다.

```python
# 모델을 channels_last로 변환
model_channels_last = model.to(memory_format=torch.channels_last)

def measure_channels_last_performance(model, input_shape, num_iterations=100, warmup=10):
    model.eval()
    # 입력도 channels_last로 변환해야 함
    dummy_input = torch.randn(*input_shape).to(device).to(memory_format=torch.channels_last)

    with torch.no_grad():
        for _ in range(warmup):
            _ = model(dummy_input)
    # ... (측정 로직)

channels_last_results, channels_last_times = measure_channels_last_performance(
    model_channels_last, input_shape
)
```

<details><summary>Output</summary>

```
============================================================
              Channels Last Memory Format
============================================================
Latency Average: 3.10 ms
Throughput FPS: 322.50
MFU: 3.00%

Speedup: 0.90x
MFU Improvement: -0.34%
```

</details>

배치 크기 1에서는 Channels Last도 큰 효과가 없었습니다. 더 큰 배치 크기에서 효과가 나타날 수 있습니다.

### 5-5. 통합 최적화 (TorchScript + AMP + Channels Last)

여러 최적화 기법을 조합하여 적용합니다.

```python
# 모델 준비: Channels Last + TorchScript
combined_model = model.to(memory_format=torch.channels_last)
dummy_input_cl = torch.randn(*input_shape).to(device).to(memory_format=torch.channels_last)

combined_model = torch.jit.trace(combined_model, dummy_input_cl)
combined_model = torch.jit.optimize_for_inference(combined_model)

# AMP와 함께 측정
def measure_combined_performance(model, input_shape, num_iterations=100, warmup=10):
    model.eval()
    dummy_input = torch.randn(*input_shape).to(device).to(memory_format=torch.channels_last)

    with torch.no_grad():
        with torch.cuda.amp.autocast():
            for _ in range(warmup):
                _ = model(dummy_input)

    torch.cuda.synchronize()
    inference_times = []

    with torch.no_grad():
        with torch.cuda.amp.autocast():
            for _ in range(num_iterations):
                start = time.time()
                _ = model(dummy_input)
                torch.cuda.synchronize()
                end = time.time()
                inference_times.append(end - start)

    avg_time = np.mean(inference_times)
    achieved_flops = theoretical_flops / avg_time
    peak_flops = get_gpu_peak_flops(torch.cuda.get_device_name(0))
    mfu = (achieved_flops / peak_flops) * 100

    return {
        'avg_time_ms': avg_time * 1000,
        'throughput_fps': 1.0 / avg_time,
        'mfu_percent': mfu,
        'achieved_flops': achieved_flops,
        'peak_flops': peak_flops,
        'device_name': torch.cuda.get_device_name(0),
        # ...
    }, inference_times

combined_results, combined_times = measure_combined_performance(combined_model, input_shape)
```

<details><summary>Output</summary>

```
============================================================
              COMBINED Optimizations
============================================================
Device: NVIDIA A100-SXM4-40GB

[Latency]
  Average: 1.45 ms (+/-0.08)

[Throughput]
  FPS: 689.75

[FLOPs Utilization]
  Achieved FLOPs: 1.25 TFLOPs
  Peak FLOPs: 19.50 TFLOPs
  MFU: 6.42%

Total Speedup: 1.92x
Total MFU Improvement: +3.07%
============================================================
```

</details>

---

## 6단계: 결과 분석 및 비교

### 최적화 비교 테이블

| Optimization | Latency (ms) | Throughput (FPS) | MFU (%) | Speedup | MFU 변화 |
|-------------|-------------|-----------------|---------|---------|----------|
| **Baseline** | 2.78 | 359.46 | 3.34 | 1.00x | +0.00 |
| **TorchScript** | 1.19 | 840.58 | 7.82 | 2.34x | **+4.48** |
| **Mixed Precision** | 3.35 | 298.89 | 2.78 | 0.83x | -0.56 |
| **Channels Last** | 3.10 | 322.50 | 3.00 | 0.90x | -0.34 |
| **Combined** | 1.45 | 689.75 | 6.42 | 1.92x | +3.07 |

### 핵심 발견 사항

1. **TorchScript가 가장 효과적**: 단독으로 2.34배 속도 향상, MFU +4.48% 개선
2. **Mixed Precision 역효과**: 작은 모델에서는 AMP 오버헤드가 더 큼
3. **Channels Last 미미한 효과**: 배치 크기 1에서는 메모리 레이아웃 변환의 이점이 적음
4. **통합 최적화는 TorchScript 단독보다 약간 낮음**: 오히려 AMP와 Channels Last의 오버헤드가 추가됨

> 시각화: Latency, Throughput, MFU, Speedup을 비교하는 4개의 bar chart와 Latency 분포를 보여주는 box plot이 생성됩니다. TorchScript가 모든 지표에서 가장 우수한 성능을 보입니다.

---

## 7단계: 최종 보고서

```
============================================================
         MFU OPTIMIZATION PROJECT - FINAL REPORT
============================================================

PROJECT INFORMATION
Model: ResNet18
Device: NVIDIA A100-SXM4-40GB
Input Shape: (1, 3, 224, 224)
Theoretical FLOPs: 1.81 GFLOPs

BASELINE PERFORMANCE
Latency: 2.78 ms
Throughput: 359.46 FPS
MFU: 3.34%

OPTIMIZED PERFORMANCE (Combined)
Latency: 1.45 ms (47.9% reduction)
Throughput: 689.75 FPS (91.9% increase)
MFU: 6.42% (+3.07% improvement)

OVERALL IMPROVEMENT
Speedup: 1.92x
MFU Improvement: +3.07%
Performance Gain: 91.9%
```

### MFU가 여전히 낮은 이유

ResNet18은 약 1.8 GFLOPs의 연산량을 가진 비교적 작은 모델입니다. A100의 FP32 피크 성능(19.5 TFLOPS)과 비교하면, **모델이 GPU의 연산 능력을 충분히 활용할 만큼 크지 않습니다.** 배치 크기를 키우거나 더 큰 모델을 사용하면 MFU가 크게 향상됩니다.

---

## 추가 최적화 방향

### 프로덕션 환경에서의 고급 최적화

1. **TensorRT**: NVIDIA의 고성능 추론 엔진. INT8/FP16 최적화, layer fusion, kernel auto-tuning 지원
2. **ONNX Runtime**: 크로스 플랫폼 추론 최적화
3. **Model Pruning**: 불필요한 연결(가중치)을 제거하여 모델 경량화
4. **Knowledge Distillation**: 큰 모델의 지식을 작은 모델로 전달
5. **배치 크기 최적화**: GPU 메모리가 허용하는 최대 배치 크기를 찾아 처리량 극대화

### 실무 팁

- 프로파일링을 통해 병목 지점을 먼저 식별하세요
- 한 번에 하나의 최적화만 적용하여 효과를 개별적으로 측정하세요
- 정확도와 성능의 트레이드오프를 항상 고려하세요
- 실제 데이터로 최종 검증을 수행하세요

### 참고 자료

- [PyTorch Performance Tuning Guide](https://pytorch.org/tutorials/recipes/recipes/tuning_guide.html)
- [TorchScript](https://pytorch.org/docs/stable/jit.html)
- [Quantization](https://pytorch.org/docs/stable/quantization.html)
- [Automatic Mixed Precision](https://pytorch.org/docs/stable/amp.html)
- [Profiler](https://pytorch.org/tutorials/recipes/recipes/profiler_recipe.html)

---

## 결론

이 프로젝트에서는 ResNet18 모델의 MFU를 측정하고 다양한 최적화 기법을 적용해보았습니다. 핵심 교훈을 정리하면:

1. **TorchScript(JIT)가 가장 효과적**: 연산 그래프 최적화와 operator fusion으로 2.34배 속도 향상을 달성했습니다.
2. **최적화 기법은 상황에 따라 다름**: Mixed Precision, Channels Last 등은 모델 크기와 배치 크기에 따라 효과가 달라집니다. 작은 모델에서는 오히려 오버헤드가 될 수 있습니다.
3. **프로파일링이 먼저**: 최적화를 적용하기 전에 PyTorch Profiler로 병목을 정확히 파악해야 합니다.
4. **MFU는 모델 크기에 좌우**: 작은 모델로는 GPU의 연산 능력을 충분히 활용하기 어렵습니다. 실무에서는 배치 크기를 키우거나, 더 큰 모델을 사용할 때 MFU 최적화의 가치가 극대화됩니다.
5. **단계적 접근**: 한 번에 하나의 최적화를 적용하고 효과를 측정하는 것이 가장 효과적인 전략입니다.