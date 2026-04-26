<!-- infographic-hero -->
![Understanding GPU Utilization and MFU (Model FLOPs Utilization) 핵심 요약](figures/infographic.svg)

*Figure: Understanding GPU Utilization and MFU (Model FLOPs Utilization) 한 장 요약 인포그래픽*

# GPU 활용률과 MFU(Model FLOPs Utilization) 이해하기

## 소개

딥러닝 모델을 학습하거나 추론할 때, GPU를 얼마나 효율적으로 사용하고 있는지 파악하는 것은 매우 중요합니다. 흔히 `nvidia-smi`로 확인하는 **GPU Utilization**과 실제 연산 효율을 나타내는 **MFU(Model FLOPs Utilization)**는 서로 다른 의미를 가지고 있습니다.

이 튜토리얼에서는 FLOPs와 MACs의 기본 개념부터 시작하여, GPU 활용률과 MFU의 차이를 실습을 통해 직접 확인해보겠습니다.

---

## 1. 실습 환경 확인

먼저 현재 사용 가능한 GPU 환경을 확인합니다.

```python
import sys, torch, platform

print("Python:", sys.version)
print("PyTorch:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
```

<details><summary>Output</summary>

```
Python: 3.12.12
PyTorch: 2.9.0+cu126
CUDA available: True
GPU: NVIDIA A100-SXM4-80GB
```

</details>

---

## 2. FLOPs/MACs 계산 실습 - calflops 라이브러리

`calflops` 라이브러리를 사용하면 모델의 FLOPs와 MACs를 간편하게 계산할 수 있습니다.

> calflops 설치: `pip install calflops`

```python
import torch
from calflops import calculate_flops

def parse_flop_string(s):
    return float(s.strip().split()[0])

# ResNet18 모델 로드
model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', weights='ResNet18_Weights.DEFAULT')

flops, macs, params = calculate_flops(
    model=model,
    input_shape=(1, 3, 224, 224),
    print_results=False
)

print(type(flops))
print(params)
print(f"FLOPs: {parse_flop_string(flops):.2f}G, MACs: {parse_flop_string(macs):.2f}G")
```

<details><summary>Output</summary>

```
<class 'str'>
11.69 M
FLOPs: 3.64G, MACs: 1.81G
```

</details>

ResNet18은 약 3.64 GFLOPs의 연산량을 가지며, MACs는 그 절반인 약 1.81G입니다. 이는 **1 MAC = 2 FLOPs**라는 관계를 잘 보여줍니다.

---

## 3. GPU Utilization vs MFU 개념 비교

### 학습 목표

**GPU Utilization(활용률)**과 **MFU(Model FLOPs Utilization)**의 차이를 이해하고, 직접 실험을 통해 두 지표가 서로 다른 의미를 가지는 이유를 파악합니다.

### 핵심 개념 비교

| 항목 | GPU Utilization | MFU (Model FLOPs Utilization) |
|------|----------------|------------------------------|
| **정의** | GPU가 현재 얼마나 바쁘게 동작 중인지 (%) | GPU가 낼 수 있는 최대 연산 성능 대비 실제 모델이 활용한 비율 (%) |
| **측정 방법** | `nvidia-smi` 명령어 등으로 실시간 사용률 확인 | FLOPs, 실행 시간, GPU 이론 성능을 기반으로 계산 |
| **의미** | GPU가 일하는 시간의 비율 | GPU가 "얼마나 효율적으로" 일했는가 |
| **주요 병목 요인** | 데이터 로딩, I/O, 동기화 지연 | 연산 최적화 부족, 배치 크기, 커널 효율 |
| **활용 목적** | 시스템 상태 확인 | 모델 최적화 및 효율 분석 |

### MFU란?

> Specific Workload (Train 1 Step, Inference 1 batch, token generation)가 실제로 GPU에서 수행한 유효한 연산량(**Effective FLOPs**)을 GPU의 이론 피크 연산량(**Peak FLOPs**)으로 정규화한 값입니다.

- **MFU가 높다** -> 계산 유닛을 비교적 잘 쓰고 있다 (Compute 효율이 좋다)
- **MFU가 낮다** -> 대개 계산이 아니라 메모리/동기화/커널 런치/통신/입출력 등이 발목 잡는다 (또는 텐서코어를 못 쓴다)

---

## 4. MFU 계산 실습

### 4.1 GPU 환경 확인

```python
import torch, time, os

print("CUDA available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
```

### 4.2 간단한 모델 정의 (Conv + FC)

```python
import torch.nn as nn

class SimpleCNN(nn.Module):
    def __init__(self):
        super().__init__()
        # 입력: (1,3,224,224), 커널: (32,3,3,3), 출력: (1,32,112,112)
        # 출력 크기 = (N+2P-F)/S+1 = (224+2-3)/2+1 = 112
        self.conv = nn.Conv2d(3, 32, 3, stride=2, padding=1)
        # FC: (1, 32*112*112) @ (32*112*112, 10) => (1, 10)
        self.fc = nn.Linear(32 * 112 * 112, 10)

    def forward(self, x):
        x = torch.relu(self.conv(x))
        x = x.view(x.size(0), -1)
        return self.fc(x)

model = SimpleCNN().cuda().eval()
```

간단한 CNN 모델을 정의했습니다. Conv2d 레이어 하나와 Linear 레이어 하나로 구성된 최소한의 구조입니다.

### 4.3 FLOPs 계산 (모델 연산량)

Convolution과 FC의 FLOPs를 수식으로 직접 계산합니다.

```python
# FLOPs = 2 * H_out * W_out * Cin * Cout * Kh * Kw
H, W, Cin, Cout, Kh, Kw = 224, 224, 3, 32, 3, 3
flops_conv = 2 * H/2 * W/2 * Cin * Cout * Kh * Kw  # stride=2이므로 출력 크기 H/2, W/2
flops_fc = 2 * (32 * 112 * 112) * 10
total_flops = flops_conv + flops_fc
print(f"총 FLOPs: {total_flops/1e9:.3f} GFLOPs")
```

<details><summary>Output</summary>

```
총 FLOPs: 0.030 GFLOPs
```

</details>

### 4.4 실행 시간 측정 (Forward + Backward)

50회 반복 학습의 평균 시간을 측정합니다. `torch.cuda.synchronize()`로 GPU 연산이 완전히 끝난 후 시간을 측정하는 것이 중요합니다.

```python
x = torch.randn(32, 3, 224, 224).cuda()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()
y = torch.randint(0, 10, (32,)).cuda()

torch.cuda.synchronize()
start = time.time()

for _ in range(50):  # 50 iterations
    optimizer.zero_grad()
    out = model(x)
    loss = criterion(out, y)
    loss.backward()
    optimizer.step()

torch.cuda.synchronize()
end = time.time()
train_time = (end - start) / 50
print(f"평균 반복당 학습 시간: {train_time:.4f} 초")
```

<details><summary>Output</summary>

```
평균 반복당 학습 시간: 0.0257 초
```

</details>

### 4.5 MFU 계산

MFU 계산식은 다음과 같습니다:

$$
\mathrm{MFU}
= \frac{\text{FLOPs per sample (or token)} \times \text{samples (or tokens) per second}}
{\text{GPU peak FLOPs per second}}
$$

$$
= \frac{\text{Total FLOPs} / \text{Execution time}}
{\text{Theoretical GPU FLOPs}} \times 100
$$

- $\text{GPU peak FLOPs per second}$: GPU가 낼 수 있는 최대 부동소수점 연산량 (A100 기준 $19.5 \times 10^{12}$ FLOPs/s)

```python
gpu_theoretical_flops = 19.5e12  # A100 기준 (FP32)
mfu = (total_flops / train_time) / gpu_theoretical_flops * 100
print(f"MFU(Model FLOPs Utilization): {mfu:.2f}%")
```

<details><summary>Output</summary>

```
MFU(Model FLOPs Utilization): 0.01%
```

</details>

### 4.6 GPU Utilization 확인

```python
# nvidia-smi로 GPU 활용률 확인
# nvidia-smi --query-gpu=utilization.gpu,utilization.memory,memory.used --format=csv
```

<details><summary>Output</summary>

```
utilization.gpu [%], utilization.memory [%], memory.used [MiB]
18 %, 10 %, 809 MiB
```

</details>

### 4.7 결과 비교

| 지표 | 의미 | 계산 기준 | 예시 값 |
|------|------|----------|--------|
| **GPU Utilization** | GPU가 바쁘게 일한 비율 | 실시간 GPU 활용률(%) | 예: 85% |
| **MFU** | GPU의 이론 연산 대비 실제 효율 | FLOPs / 이론 FLOPs | 예: 25% |

GPU 활용률은 높더라도, 실제 연산 효율(MFU)은 낮을 수 있습니다. 이는 데이터 로딩 지연, 메모리 대역폭 한계, 작은 배치 크기 등의 요인 때문입니다.

---

## 5. FLOPs (Floating Point Operations) 개념 정리

### 정의

**FLOPs(Floating Point Operations)**란 모델이 수행하는 **부동소수점 연산의 총 개수**를 의미합니다. 신경망이 학습 또는 추론 과정에서 곱셈, 덧셈, 나눗셈, 지수 등의 실수 연산이 몇 번 수행되었는가를 정량적으로 나타내는 지표입니다.

### FLOPs가 중요한 이유

| 항목 | 설명 |
|------|------|
| **계산 복잡도 지표** | 모델의 연산량을 정량화하여 복잡도를 비교할 수 있음 |
| **성능/속도 예측** | FLOPs가 많을수록 GPU 연산량과 실행 시간이 증가함 |
| **효율성 판단 기준** | FLOPs가 적을수록 계산 효율이 높고, 경량 모델에 유리함 |
| **하드웨어 비교 기준** | 서로 다른 GPU/TPU 환경 간 모델 효율을 정량 비교 가능 |

---

## 6. 부동소수점 표준: IEEE 754 요약

### 개요

**IEEE 754**는 컴퓨터에서 실수를 표현하고 연산하는 국제 표준입니다. 핵심 아이디어는 실수를 **부호(Sign), 지수(Exponent), 가수(Fraction)**로 나눠 정규화된 과학적 표기로 저장한다는 것입니다.

실수 값은 (정규수의 경우) 다음으로 해석됩니다:

$$
(-1)^s \times (1.f)_2 \times 2^{\,e - \text{bias}}
$$

- $s$: 부호 비트(0=양수, 1=음수)
- $f$: 가수부(숨겨진 1 포함 전제)
- $e$: 지수부 정수값
- $\text{bias}$: 형식별 바이어스

### 대표 포맷

| 포맷 | 총 비트 | 부호 | 지수 | 가수 | 바이어스 |
|---|---:|---:|---:|---:|---:|
| **binary32 (float)** | 32 | 1 | 8 | 23 | 127 |
| **binary64 (double)** | 64 | 1 | 11 | 52 | 1023 |

정밀도(유효 십진자리 근사): float는 약 7자리, double은 약 15~16자리입니다.

### 특수 값 인코딩

- **정규수(normal)**: $0 < e < \text{max}$ -> $(-1)^s (1.f) 2^{e-\text{bias}}$
- **서브노말(subnormal)**: $e=0$, $f \neq 0$ -> 아주 작은 수의 연속성 보장
- **0**: $e=0$, $f=0$ -> `+0`, `-0` 존재
- **무한대**: $e=\text{max}$, $f=0$ -> `+inf`, `-inf`
- **NaN**: $e=\text{max}$, $f \neq 0$ -> qNaN(quiet), sNaN(signaling)

### 핵심 지표

- **기계 엡실론**: float의 경우 $\epsilon \approx 2^{-23} \approx 1.19 \times 10^{-7}$
- **ULP (Unit in the Last Place)**: 인접 표현 가능 수 간 간격

### 자주 겪는 현상

- `0.1 + 0.2 != 0.3` (이진 표현 불가능)
- $(a+b)+c \neq a+(b+c)$ (연산 비결합성)
- 비슷한 큰 수의 차에서 유효자리 손실 (소실/취소)

### 확장 포맷

딥러닝에서는 binary128, **bfloat16**(지수 8/가수 7) 등 하드웨어/ML 특화 포맷도 사용됩니다.

---

## 7. FC (Fully Connected) 레이어의 FLOPs 계산

### 개념

완전연결(FC) 레이어는 입력 뉴런($N_{in}$)과 출력 뉴런($N_{out}$)이 모두 연결된 형태입니다. 각 출력 뉴런은 모든 입력 값에 대해 가중치 곱셈과 누산을 수행합니다.

$$
FLOPs = 2 \times N_{in} \times N_{out}
$$

### 왜 2를 곱하는가?

- 1개의 연결선(Weight)은 `입력 x 가중치` -> **곱셈 연산 (1 FLOP)**
- 여러 입력의 곱셈 결과를 모두 더함 -> **덧셈 연산 (1 FLOP)**
- 하나의 weight 연결당 "곱셈 + 덧셈" = **2 FLOPs**

### 예시

$N_{in} = 4$, $N_{out} = 3$인 경우:

$$
FLOPs = 2 \times 4 \times 3 = 24
$$

곱셈 12번 + 덧셈 12번 = 총 24 FLOPs

### 실습 코드

```python
import torch
import torch.nn as nn

# FC (Linear) 레이어 정의
N_in, N_out = 4, 3
fc = nn.Linear(N_in, N_out, bias=False)

# 입력 데이터 (배치 크기 1)
x = torch.randn(1, N_in)
y = fc(x)

print("입력 크기:", x.shape)
print("출력 크기:", y.shape)

# FLOPs 계산
flops = 2 * N_in * N_out
print(f"이론적 FLOPs: {flops} 회 연산 (곱셈 + 덧셈 포함)")
```

<details><summary>Output</summary>

```
입력 크기: torch.Size([1, 4])
출력 크기: torch.Size([1, 3])
이론적 FLOPs: 24 회 연산 (곱셈 + 덧셈 포함)
```

</details>

---

## 8. Convolution 레이어의 FLOPs 계산

### 개념

컨볼루션은 곱셈(Multiply)과 덧셈(Add) 연산으로 구성된 대표적인 계산 집약적 연산입니다. 하나의 출력 픽셀을 얻기 위해 수행되는 연산 수는:

$$
\text{연산 수} = K_h \times K_w \times C_{in}
$$

### FLOPs 계산 공식

$$
FLOPs = 2 \times H_{out} \times W_{out} \times K_h \times K_w \times C_{in} \times C_{out}
$$

| 항목 | 의미 |
|------|------|
| $H_{out}, W_{out}$ | 출력 Feature Map의 높이, 너비 |
| $K_h, K_w$ | 커널(필터)의 높이, 너비 |
| $C_{in}$ | 입력 채널 수 |
| $C_{out}$ | 출력 채널(필터 개수) 수 |
| 2배 | Multiply + Add 연산을 모두 포함 |

### 예시

입력 $(C_{in}, H, W) = (3, 4, 4)$, 커널 $(K_h, K_w) = (3, 3)$, $C_{out} = 1$, 출력 $(H_{out}, W_{out}) = (2, 2)$인 경우:

$$
FLOPs = 2 \times 2 \times 2 \times 3 \times 3 \times 3 \times 1 = 216
$$

### 실습 코드

```python
import torch
import torch.nn as nn

# 입력 및 커널 정의
x = torch.randn(1, 3, 4, 4)   # (배치, 채널, 높이, 너비)
conv = nn.Conv2d(in_channels=3, out_channels=1, kernel_size=3, stride=1, padding=0)

# 연산 수행
y = conv(x)
print("출력 크기:", y.shape)  # (1,1,2,2)

# FLOPs 계산 공식 적용
H_out, W_out = y.shape[2], y.shape[3]
K_h, K_w = conv.kernel_size
C_in, C_out = conv.in_channels, conv.out_channels

flops = 2 * H_out * W_out * K_h * K_w * C_in * C_out
print(f"이론적 FLOPs: {flops} 회 연산")
```

<details><summary>Output</summary>

```
출력 크기: torch.Size([1, 1, 2, 2])
이론적 FLOPs: 216 회 연산
```

</details>

---

## 9. MACs (Multiply-Accumulate Operations) 개념

### 정의

**MACs (Multiply-Accumulate Operations)**는 딥러닝 연산에서 자주 등장하는 곱셈과 덧셈 연산의 조합입니다.

$$
y = (a \times b) + c
$$

따라서 **1 MAC = 1 곱셈 + 1 덧셈 = 2 FLOPs**로 환산할 수 있습니다.

### 수학적 관계

$$
1\ \text{MAC} = 2\ \text{FLOPs}
$$

| 연산 종류 | FLOPs 수 | 설명 |
|-----------|---------|------|
| 곱셈(Multiply) | 1 | 실수 x 실수 |
| 덧셈(Add) | 1 | 곱셈 결과를 누산기에 더함 |
| **합계** | **2 FLOPs** | 1 MAC 수행당 2개의 부동소수점 연산 |

### 컨볼루션의 MACs

$$
\text{MACs} = H_{out} \times W_{out} \times K_h \times K_w \times C_{in} \times C_{out}
$$

### FC의 MACs

$$
\text{MACs} = N_{in} \times N_{out}
$$

### 실습 코드

```python
import torch
import torch.nn as nn

# 간단한 모델 정의
model = nn.Sequential(
    nn.Conv2d(3, 16, 3, stride=1, padding=1),
    nn.ReLU(),
    nn.Conv2d(16, 32, 3, stride=1, padding=1),
    nn.ReLU(),
    nn.Flatten(),
    nn.Linear(32 * 32 * 32, 10)
)

x = torch.randn(1, 3, 32, 32)

# MACs 계산 예시 (첫 번째 Conv 레이어)
H_out, W_out = 32, 32
K_h, K_w = 3, 3
C_in, C_out = 3, 16

conv1_macs = H_out * W_out * K_h * K_w * C_in * C_out
print(f"Conv1 MACs: {conv1_macs / 1e6:.2f} MMACs")
```

<details><summary>Output</summary>

```
Conv1 MACs: 0.44 MMACs
```

</details>

### FLOPs vs MACs 비교 요약

| 구분 | 의미 | 단위 예시 | 관계 |
|------|------|----------|------|
| **MACs** | 실제 하드웨어의 연산 조합 단위 (Multiply + Add) | GMAC | -- |
| **FLOPs** | 부동소수점 연산 횟수 (곱셈 또는 덧셈) | GFLOPs | 1 MAC = 2 FLOPs |

하나의 MAC 연산은 부동소수점 곱셈 1회와 덧셈 1회로 이루어지며, 따라서 **1 MAC = 2 FLOPs**로 표현됩니다.

---

## 10. MFU 측정 도구 사용법 - PyTorch Profiler

### PyTorch Profiler란?

`PyTorch Profiler`는 모델 학습/추론 중 CPU/GPU 연산, 커널, 메모리, I/O 등을 정밀하게 측정해 병목(bottleneck)을 찾아내는 도구입니다. TensorBoard와 연동해 시각화할 수 있습니다.

### 측정 항목

- **연산 시간**: op별/레이어별 `self_cpu_time_total`, `self_cuda_time_total`
- **호출 횟수 & 입력 shape**: `count`, `record_shapes`
- **CUDA 커널/스트림 타임라인**: launch 간격, 동기화 지연
- **메모리/파라미터**: `profile_memory=True` 옵션
- **데이터 로딩**: I/O 비용

### 실습: PyTorch Profiler로 MFU 측정

```python
import torch
import os
from torch.profiler import profile, record_function, ProfilerActivity

# 1. 모델 및 입력 정의
model = torch.nn.Linear(1024, 1024).cuda()
input_data = torch.randn(16, 1024).cuda()

# 2. FLOPs 계산 (이론값)
batch_size = 16
in_features = 1024
out_features = 1024
flops_per_forward = 2 * batch_size * in_features * out_features
print(f"[INFO] Estimated FLOPs per forward: {flops_per_forward/1e6:.2f} MFLOPs")

# 3. FLOPs 측정 (Profiler)
with profile(activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
             with_flops=True, record_shapes=True) as prof:
    with record_function("linear_forward"):
        output = model(input_data)

total_flops = sum([
    evt.flops for evt in prof.key_averages()
    if hasattr(evt, "flops") and evt.flops is not None
])
print(f"[INFO] FLOPs measured by profiler: {total_flops/1e6:.2f} MFLOPs")

# 4. CUDA 실행 시간 측정 (정확한 방식)
torch.cuda.synchronize()
start_event = torch.cuda.Event(enable_timing=True)
end_event = torch.cuda.Event(enable_timing=True)

num_iter = 10000

start_event.record()
for _ in range(num_iter):
    _ = model(input_data)
end_event.record()

torch.cuda.synchronize()
elapsed_time_ms = start_event.elapsed_time(end_event)
avg_time_s = (elapsed_time_ms / num_iter) / 1000.0

print(f"[INFO] Avg forward time per iteration: {avg_time_s*1e3:.4f} ms")

# 5. Throughput & MFU 계산
throughput_gflops = (flops_per_forward / avg_time_s) / 1e9
gpu_peak_flops = 312_000  # A100 FP16 기준 (GFLOPs)
mfu = (throughput_gflops / gpu_peak_flops) * 100

print(f"[RESULT] Throughput: {throughput_gflops:.2f} GFLOPs/s")
print(f"[RESULT] MFU (Model FLOPs Utilization): {mfu:.4f}%")
```

<details><summary>Output</summary>

```
[INFO] Estimated FLOPs per forward: 33.55 MFLOPs
[INFO] FLOPs measured by profiler: 33.55 MFLOPs
[INFO] Avg forward time per iteration: 0.0516 ms
[RESULT] Throughput: 650.14 GFLOPs/s
[RESULT] MFU (Model FLOPs Utilization): 0.2084%
```

</details>

Profiler가 측정한 FLOPs(33.55M)가 이론값과 정확히 일치하는 것을 확인할 수 있습니다. 단순 Linear 레이어의 MFU가 약 0.21%로 매우 낮은 이유는 연산량이 작아 GPU의 연산 능력을 충분히 활용하지 못하기 때문입니다.

### TensorBoard로 시각화

측정 결과를 TensorBoard에 기록하여 시각적으로 확인할 수도 있습니다.

```python
from torch.utils.tensorboard import SummaryWriter

log_dir = "./log_mfu"
os.makedirs(log_dir, exist_ok=True)

writer = SummaryWriter(log_dir)
writer.add_scalar("Performance/FLOPs_per_forward(M)", flops_per_forward/1e6)
writer.add_scalar("Performance/Throughput_GFLOPs_per_s", throughput_gflops)
writer.add_scalar("Performance/MFU_percent", mfu)
writer.add_scalar("Performance/Avg_forward_time_ms", avg_time_s*1e3)
writer.close()

print(f"[INFO] TensorBoard scalar metrics saved to {log_dir}")
# 시각화: tensorboard --logdir=./log_mfu --port=6006
```

---

## 기대 학습 효과

- GPU 활용률과 실제 연산 효율의 차이를 정량적으로 이해
- 모델 구조, 배치 크기, 최적화 기법이 효율에 미치는 영향 인식
- MFU 계산을 통해 병목 구간을 찾아 성능 최적화 방향 제시 가능

## 결론

이 튜토리얼에서는 GPU 활용률(GPU Utilization)과 MFU(Model FLOPs Utilization)의 차이를 살펴보았습니다. 핵심 내용을 정리하면:

1. **GPU Utilization**은 GPU가 얼마나 바쁜지를 나타내고, **MFU**는 GPU가 얼마나 효율적으로 일하는지를 나타냅니다.
2. **FLOPs**는 모델의 연산량을 정량화하는 지표이며, **1 MAC = 2 FLOPs**의 관계를 가집니다.
3. IEEE 754 부동소수점 표준을 이해하면 딥러닝에서 발생하는 수치 오차 현상을 이해하는 데 도움이 됩니다.
4. **PyTorch Profiler**를 사용하면 모델의 FLOPs를 정밀하게 측정하고, TensorBoard와 연동하여 시각화할 수 있습니다.
5. 단순한 모델에서는 MFU가 매우 낮게 나올 수 있으며, 이는 GPU의 연산 능력을 충분히 활용하지 못하기 때문입니다.

다음 튜토리얼에서는 Layer별 FLOPs를 분석하고, 다양한 프로파일링 도구를 활용하여 모델의 병목 구간을 찾아보겠습니다.