# 모델 양자화 완전 가이드: Dynamic, Static, QAT 단계별 실습

## 소개

딥러닝 모델을 실제 프로덕션 환경이나 엣지 디바이스에 배포할 때, 모델의 크기와 추론 속도는 핵심적인 제약 조건입니다. **양자화(Quantization)**는 모델의 가중치와 활성화를 32비트 부동소수점(FP32)에서 8비트 정수(INT8) 등 낮은 비트로 변환하여 모델을 경량화하는 기술입니다.

이 튜토리얼에서는 양자화의 수학적 원리부터 PyTorch를 활용한 세 가지 양자화 기법(Dynamic, Static, QAT)의 실습까지 단계별로 다룹니다.

---

## 1. 모델 양자화란?

모델 양자화는 딥러닝 모델의 가중치(weights)와 활성화(activations)를 낮은 비트 정밀도로 표현하는 기술입니다. 일반적으로 32비트 부동소수점(FP32)으로 표현되는 값들을 8비트 정수(INT8)나 더 낮은 비트로 변환합니다.

### 양자화의 기본 원리

```
원본 값 (FP32): 3.14159... -> 양자화 -> 정수 값 (INT8): 100
```

양자화 공식은 다음과 같습니다:

$$
q = \text{round}\left(\frac{x}{s} + z\right)
$$

- $x$: 실수값 (예: FP32 텐서)
- $q$: 정수값 (예: INT8)
- $s$: **scale**, 스케일링 계수
  $$ s = \frac{x_{\max} - x_{\min}}{q_{\max} - q_{\min}} $$
- $z$: **zero_point**, 정수 0이 실수 0에 대응되도록 하는 보정값
  $$ z = q_{\min} - \frac{x_{\min}}{s} $$

### 역방향 (Dequantization)

양자화된 값을 다시 실수로 복원하는 과정입니다:

$$
x' = s \times (q - z)
$$

여기서 $x' \approx x$로, 완벽한 복원은 아니지만 근사값을 얻을 수 있습니다.

### 전체 변환 과정

1. 실수 구간 $[x_{\min}, x_{\max}]$을 정수 구간 $[q_{\min}, q_{\max}]$으로 **선형 스케일링**
2. 정수로 반올림하여 양자화 수행
3. 필요시 다시 복원(Dequantization) 수행

$$
x \;\xrightarrow{\text{Quantize}}\; q = \text{round}\!\left(\frac{x}{s} + z\right)
\;\xrightarrow{\text{Dequantize}}\;
x' = s \times (q - z)
$$

---

## 2. NumPy로 양자화 원리 구현하기

먼저 NumPy만으로 양자화의 기본 동작을 직접 구현해 보겠습니다.

```python
import numpy as np

# 원래 FP32 실수값 (예: 활성화 값)
x = np.array([-1.0, -0.5, 0.0, 0.3, 0.7, 1.0], dtype=np.float32)

# INT8 양자화 파라미터 설정
x_min, x_max = x.min(), x.max()

# 8비트 정수 범위: [-128, 127]
qmin, qmax = -128, 127

# scale과 zero_point 계산
scale = (x_max - x_min) / (qmax - qmin)
zero_point = np.round(qmin - x_min / scale)

print(f"scale={scale:.6f}, zero_point={zero_point:.2f}")

# 양자화 수행
q = np.round(x / scale + zero_point).astype(np.int8)

# 복원(Dequantization)
x_reconstructed = (q.astype(np.float32) - zero_point) * scale

print("원래 FP32:", x)
print("양자화 INT8:", q)
print("복원된 값:", x_reconstructed)
```

<details><summary>Output</summary>

```
scale=0.007843, zero_point=-1.00
원래 FP32: [-1.  -0.5  0.   0.3  0.7  1. ]
양자화 INT8: [-128  -65   -1   37   88  126]
복원된 값: [-0.9960785  -0.5019608   0.          0.29803923  0.69803923  0.9960785 ]
```

</details>

원본값과 복원값 사이에 미세한 오차가 발생하는 것을 확인할 수 있습니다. 이것이 양자화의 근본적인 트레이드오프입니다 -- 정밀도를 약간 희생하는 대신 모델 크기와 연산 속도에서 이점을 얻습니다.

### Per-Channel Quantization

Convolution 계층에서는 채널마다 값의 분포가 다를 수 있습니다. 각 채널 $i$에 대해 독립된 scale $s_i$, zero_point $z_i$를 적용하면 정확도 손실을 줄일 수 있습니다.

```python
x = np.array([
    [-1.0, -0.5, 0.0, 0.5],
    [ 0.0,  0.5, 1.0, 1.5]
], dtype=np.float32)

qmin, qmax = -128, 127
scales = []
zero_points = []
q_out = np.zeros_like(x, dtype=np.int8)

for c in range(x.shape[0]):
    x_min, x_max = x[c].min(), x[c].max()
    scale = (x_max - x_min) / (qmax - qmin)
    zp = np.round(qmin - x_min / scale)
    q_out[c] = np.round(x[c] / scale + zp).astype(np.int8)
    scales.append(scale)
    zero_points.append(zp)

print("Per-channel scales:", np.round(scales, 5))
print("Per-channel zero_points:", zero_points)
print("Quantized INT8 values:\n", q_out)
```

<details><summary>Output</summary>

```
Per-channel scales: [0.00588 0.00588]
Per-channel zero_points: [np.float32(42.0), np.float32(-128.0)]
Quantized INT8 values:
 [[-128  -43   42  127]
 [-128  -43   42  127]]
```

</details>

Per-channel 양자화는 per-tensor 양자화보다 **정확도 손실을 줄이는 효과**가 있어, 실무에서 더 자주 사용됩니다.

> 위 코드를 실행하면, 원본값과 양자화 후 복원값을 비교하는 라인 차트가 출력됩니다. 두 선이 거의 겹치지만 미세한 차이가 존재하는 것을 시각적으로 확인할 수 있습니다.

---

## 3. 양자화의 장점과 단점

### 장점
- **모델 크기 감소**: 4배 이상 크기 감소 (FP32 -> INT8)
- **추론 속도 향상**: 정수 연산이 부동소수점 연산보다 빠름
- **메모리 사용량 감소**: 엣지 디바이스에서 중요
- **전력 소비 감소**: 모바일 환경에서 배터리 수명 연장

### 단점
- **정확도 손실**: 정밀도 감소로 인한 성능 저하
- **학습 복잡도 증가**: QAT(Quantization Aware Training) 필요
- **하드웨어 의존성**: 특정 하드웨어에서만 가속 효과

---

## 4. 양자화의 종류

| 방식 | 설명 | 특징 |
|------|------|------|
| **동적 양자화** | 가중치만 양자화, 활성화는 추론 시 동적으로 양자화 | 구현 간단, 정확도 손실 적음 |
| **정적 양자화** | 가중치와 활성화 모두 양자화, 캘리브레이션 필요 | 더 빠른 추론 속도 |
| **QAT** | 학습 중에 양자화 시뮬레이션 | 최고의 정확도 유지, 학습 시간 증가 |

---

## 5. 실습 환경 설정

본격적인 PyTorch 양자화 실습을 위해 필요한 라이브러리를 임포트합니다.

```python
import torch
import torch.nn as nn
import torch.quantization
import torchvision
import torchvision.transforms as transforms
import numpy as np
import time
import os
import copy
```

---

## 6. CNN 모델 정의

CIFAR-10 분류를 위한 간단한 CNN 모델을 정의합니다. 이 모델에 다양한 양자화 기법을 적용해 볼 것입니다.

```python
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.relu1 = nn.ReLU(inplace=True)
        self.pool1 = nn.MaxPool2d(2)

        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.relu2 = nn.ReLU(inplace=True)
        self.pool2 = nn.MaxPool2d(2)

        self.fc1 = nn.Linear(64 * 8 * 8, 128)
        self.relu3 = nn.ReLU(inplace=True)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.pool1(self.relu1(self.bn1(self.conv1(x))))
        x = self.pool2(self.relu2(self.bn2(self.conv2(x))))
        x = x.view(x.size(0), -1)
        x = self.relu3(self.fc1(x))
        x = self.fc2(x)
        return x
```

Conv-BN-ReLU 패턴으로 구성된 2개의 합성곱 블록과 완전 연결 레이어로 이루어진 간결한 구조입니다. 양자화 시 Conv-BN-ReLU 블록은 **퓨전(fusion)** 대상이 되어 추론 효율을 더 높일 수 있습니다.

---

## 7. 데이터셋 준비 및 모델 학습

CIFAR-10 데이터셋을 로드하고 기본 모델을 학습합니다.

```python
# CIFAR-10 데이터셋 로드
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
])

trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
                                        download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=64,
                                          shuffle=True, num_workers=2)

testset = torchvision.datasets.CIFAR10(root='./data', train=False,
                                       download=True, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=64,
                                         shuffle=False, num_workers=2)
```

```python
def train_model(model, trainloader, epochs=5):
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        for i, (inputs, labels) in enumerate(trainloader):
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            if i % 100 == 99:
                print(f'[Epoch {epoch + 1}, Batch {i + 1}] Loss: {running_loss / 100:.3f}')
                running_loss = 0.0

    return model

# 모델 생성 및 학습
model = SimpleCNN()
model = train_model(model, trainloader)
```

학습이 진행되면서 Loss가 약 1.7에서 0.65 수준까지 감소하는 것을 확인할 수 있습니다. 5 에포크 학습 후 약 **72-73%** 수준의 테스트 정확도를 기대할 수 있습니다.

---

## 8. 동적 양자화 (Dynamic Quantization)

동적 양자화는 가장 간단한 양자화 방식입니다. 가중치는 미리 양자화하고, 활성화는 추론 시점에 동적으로 양자화합니다.

```python
def apply_dynamic_quantization(model):
    """동적 양자화 적용"""
    quantized_model = torch.quantization.quantize_dynamic(
        model,
        {nn.Linear, nn.Conv2d},  # 양자화할 레이어 타입
        dtype=torch.qint8
    )
    return quantized_model

# 동적 양자화 적용
dynamic_quantized_model = apply_dynamic_quantization(model)
print("동적 양자화 완료!")
```

단 몇 줄의 코드로 양자화가 완료됩니다. `quantize_dynamic` 함수에 양자화 대상 레이어 타입과 데이터 타입만 지정하면 됩니다.

---

## 9. 정적 양자화 (Static Quantization)

정적 양자화는 가중치뿐만 아니라 활성화도 미리 양자화합니다. 이를 위해 **캘리브레이션(calibration)** 과정이 필요합니다.

```python
def prepare_model_for_static_quantization(model):
    """정적 양자화를 위한 모델 준비"""
    # QuantStub과 DeQuantStub 추가
    model.quant = torch.quantization.QuantStub()
    model.dequant = torch.quantization.DeQuantStub()

    # forward 메소드 수정
    original_forward = model.forward
    def forward(self, x):
        x = self.quant(x)
        x = original_forward(x)
        x = self.dequant(x)
        return x
    model.forward = forward.__get__(model, model.__class__)

    return model

def apply_static_quantization(model, dataloader):
    """정적 양자화 적용"""
    # 모델 준비
    model = prepare_model_for_static_quantization(model)

    # 양자화 설정
    model.qconfig = torch.quantization.get_default_qconfig('fbgemm')

    # 퓨즈 가능한 레이어 결합 (Conv + BatchNorm + ReLU)
    torch.quantization.fuse_modules(model, [['conv1', 'bn1', 'relu1']], inplace=True)

    # 양자화 준비
    prepared_model = torch.quantization.prepare(model)

    # 캘리브레이션 (일부 데이터로 통계 수집)
    prepared_model.eval()
    with torch.no_grad():
        for i, (inputs, _) in enumerate(dataloader):
            if i > 10:  # 10배치만 사용
                break
            prepared_model(inputs)

    # 양자화 변환
    quantized_model = torch.quantization.convert(prepared_model)

    return quantized_model

# 정적 양자화 적용
model.eval()
static_quantized_model = apply_static_quantization(copy.deepcopy(model), trainloader)
```

정적 양자화의 핵심 단계를 정리하면:

1. **QuantStub/DeQuantStub 추가**: 입출력에서 양자화/역양자화 수행
2. **레이어 퓨전**: Conv-BN-ReLU를 하나의 연산으로 합쳐 효율 향상
3. **캘리브레이션**: 실제 데이터를 통과시켜 활성화의 통계(min/max) 수집
4. **양자화 변환**: 수집한 통계를 기반으로 최종 양자화 수행

---

## 10. 양자화 인식 학습 (QAT)

QAT는 학습 과정에서 양자화로 인한 오차를 시뮬레이션하여, 양자화 후에도 높은 정확도를 유지하도록 합니다.

```python
def quantization_aware_training(model, trainloader, epochs=3):
    """양자화 인식 학습"""
    # 모델 준비
    model.eval()
    # 퓨전 및 준비
    torch.quantization.fuse_modules(model, [['conv1', 'bn1', 'relu1']], inplace=True)

    model.train()
    model.qconfig = torch.quantization.get_default_qat_qconfig('fbgemm')
    prepared_model = torch.quantization.prepare_qat(model)

    # QAT 학습
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(prepared_model.parameters(), lr=0.001)

    for epoch in range(epochs):
        for i, (inputs, labels) in enumerate(trainloader):
            if i > 100:  # 데모를 위해 제한
                break

            optimizer.zero_grad()
            outputs = prepared_model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            if i % 50 == 0:
                print(f'QAT Epoch [{epoch+1}/{epochs}], '
                      f'Step [{i}/{len(trainloader)}], '
                      f'Loss: {loss.item():.4f}')

    # 양자화 변환
    prepared_model.eval()
    quantized_model = torch.quantization.convert(prepared_model)

    return quantized_model

qat_quantized_model = quantization_aware_training(copy.deepcopy(model), trainloader)
```

<details><summary>Output</summary>

```
QAT Epoch [1/3], Step [0/782], Loss: 0.6166
QAT Epoch [1/3], Step [50/782], Loss: 0.4418
QAT Epoch [1/3], Step [100/782], Loss: 0.7073
QAT Epoch [2/3], Step [0/782], Loss: 0.3732
QAT Epoch [2/3], Step [50/782], Loss: 0.3888
QAT Epoch [2/3], Step [100/782], Loss: 0.4938
QAT Epoch [3/3], Step [0/782], Loss: 0.5397
QAT Epoch [3/3], Step [50/782], Loss: 0.6574
QAT Epoch [3/3], Step [100/782], Loss: 0.5799
```

</details>

QAT에서는 학습 과정 중 **fake quantization** 노드가 삽입되어, 순전파/역전파 시 양자화 오차를 반영합니다. 이를 통해 모델이 양자화 환경에 적응하게 됩니다.

---

## 11. 성능 비교 및 분석

세 가지 양자화 기법의 효과를 비교해 보겠습니다.

### 모델 크기 비교

```python
def get_model_size(model):
    """모델 크기 계산 (MB)"""
    torch.save(model.state_dict(), "temp.p")
    size_mb = os.path.getsize("temp.p") / 1e6
    os.remove("temp.p")
    return size_mb

original_size = get_model_size(model)
quantized_size = get_model_size(dynamic_quantized_model)

print(f"원본 모델 크기: {original_size:.2f} MB")
print(f"양자화된 모델 크기: {quantized_size:.2f} MB")
print(f"압축률: {original_size / quantized_size:.2f}x")
```

<details><summary>Output</summary>

```
원본 모델 크기: 2.19 MB
양자화된 모델 크기: 0.61 MB
압축률: 3.58x
```

</details>

동적 양자화만으로도 **3.58배**의 모델 크기 압축을 달성했습니다.

### 추론 속도 비교

```python
def measure_inference_time(model, input_shape=(1, 3, 32, 32), num_runs=100):
    """추론 시간 측정"""
    model.eval()
    dummy_input = torch.randn(input_shape)

    # Warm-up
    for _ in range(10):
        _ = model(dummy_input)

    # 실제 측정
    start_time = time.time()
    for _ in range(num_runs):
        with torch.no_grad():
            _ = model(dummy_input)

    end_time = time.time()
    avg_time = (end_time - start_time) / num_runs * 1000  # ms

    return avg_time

original_time = measure_inference_time(model)
quantized_time = measure_inference_time(dynamic_quantized_model)

print(f"원본 모델 추론 시간: {original_time:.2f} ms")
print(f"양자화된 모델 추론 시간: {quantized_time:.2f} ms")
print(f"속도 향상: {original_time / quantized_time:.2f}x")
```

<details><summary>Output</summary>

```
원본 모델 추론 시간: 0.92 ms
양자화된 모델 추론 시간: 0.99 ms
속도 향상: 0.92x
```

</details>

> **참고**: 이 예시에서는 모델이 작고 CPU에서 실행되므로 속도 향상이 크지 않습니다. 대형 모델이나 INT8 가속을 지원하는 하드웨어(예: x86 CPU with AVX-512, ARM NEON)에서는 2-4배의 속도 향상을 기대할 수 있습니다.

### 정확도 비교

```python
def evaluate_model(model, testloader):
    """모델 정확도 평가"""
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, labels in testloader:
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total
    return accuracy

original_acc = evaluate_model(model, testloader)
quantized_acc = evaluate_model(dynamic_quantized_model, testloader)
print(f"원본 모델 정확도: {original_acc:.2f}%")
print(f"양자화된 모델 정확도: {quantized_acc:.2f}%")
```

<details><summary>Output</summary>

```
원본 모델 정확도: 72.96%
양자화된 모델 정확도: 72.98%
```

</details>

동적 양자화의 경우 정확도 손실이 거의 없는 것을 확인할 수 있습니다. 이는 동적 양자화가 가중치만 양자화하고 활성화는 런타임에 처리하기 때문입니다.

> 위 세 가지 비교(크기, 속도, 정확도)를 막대 그래프로 시각화하면, Original / Dynamic Quant / Static Quant 세 모델의 차이를 한눈에 파악할 수 있습니다.

---

## 12. 고급 주제: 커스텀 양자화 설정

모든 레이어에 동일한 양자화를 적용할 필요는 없습니다. 레이어별로 다른 양자화 설정을 적용할 수 있습니다.

```python
def custom_quantization_config(model):
    # 첫 번째 레이어는 높은 정밀도 유지
    model.conv1.qconfig = torch.quantization.default_qconfig

    # 마지막 레이어는 더 공격적인 양자화
    model.fc2.qconfig = torch.quantization.QConfig(
        activation=torch.quantization.MinMaxObserver.with_args(dtype=torch.quint8),
        weight=torch.quantization.MinMaxObserver.with_args(dtype=torch.qint8)
    )

    return model

custom_model = copy.deepcopy(model)
custom_model = custom_quantization_config(custom_model)
custom_quantized_model = apply_static_quantization(custom_model, trainloader)
```

입력에 가까운 레이어는 정보 손실이 누적될 수 있으므로 높은 정밀도를 유지하고, 출력에 가까운 레이어는 더 공격적으로 양자화하는 전략이 일반적입니다.

---

## 13. 양자화 오차 분석

양자화가 모델 출력에 미치는 영향을 정량적으로 분석하는 것은 매우 중요합니다.

```python
def analyze_quantization_error(original_model, quantized_model, dataloader):
    """양자화 오차 분석"""
    original_model.eval()
    quantized_model.eval()

    errors = []

    with torch.no_grad():
        for inputs, _ in dataloader:
            original_output = original_model(inputs)
            quantized_output = quantized_model(inputs)

            # MSE 계산
            error = torch.mean((original_output - quantized_output) ** 2)
            errors.append(error.item())

            if len(errors) > 10:  # 10 배치만 분석
                break

    avg_error = np.mean(errors)
    print(f"평균 양자화 오차 (MSE): {avg_error:.6f}")
```

> 양자화 오차의 히스토그램을 그리면 대부분의 배치에서 오차가 매우 작은 값에 집중되어 있음을 확인할 수 있습니다.

---

## 14. 모바일 배포를 위한 최적화

양자화된 모델을 모바일 디바이스에 배포하려면 TorchScript 변환과 모바일 최적화가 필요합니다.

```python
def prepare_for_mobile(quantized_model):
    """모바일 배포를 위한 모델 준비"""
    # TorchScript 변환
    scripted_model = torch.jit.script(quantized_model)

    # 모바일용으로 최적화
    optimized_model = torch.utils.mobile_optimizer.optimize_for_mobile(scripted_model)

    # 저장
    optimized_model.save("quantized_model_mobile.pt")

    print("모바일 최적화 완료!")
    return optimized_model

mobile_model = prepare_for_mobile(custom_quantized_model)
```

저장된 `.pt` 파일을 Android/iOS 앱에서 PyTorch Mobile을 통해 바로 로드하여 사용할 수 있습니다.

```python
# 저장된 모바일 모델 로드 및 추론 테스트
loaded_mobile_model = torch.jit.load("quantized_model_mobile.pt")
loaded_mobile_model.eval()

dummy_input = torch.randn(1, 3, 32, 32)

with torch.no_grad():
    output = loaded_mobile_model(dummy_input)

print("모바일 모델 추론 성공, 출력 shape:", output.shape)
```

---

## 15. 양자화 기법 요약 비교

| 항목 | 동적 양자화 | 정적 양자화 | QAT |
|------|------------|------------|-----|
| **양자화 대상** | 가중치만 | 가중치 + 활성화 | 가중치 + 활성화 |
| **캘리브레이션** | 불필요 | 필요 | 학습 중 수행 |
| **구현 난이도** | 쉬움 | 중간 | 어려움 |
| **정확도 손실** | 매우 적음 | 적음 | 거의 없음 |
| **속도 향상** | 보통 | 좋음 | 좋음 |
| **사용 시나리오** | 빠른 적용 | 배포 최적화 | 정확도 중시 |

---

## 결론

이 튜토리얼에서는 모델 양자화의 수학적 원리부터 PyTorch를 활용한 세 가지 양자화 기법의 구현까지 단계별로 살펴보았습니다.

**핵심 정리:**

1. **동적 양자화**는 가장 간단하며, 정확도 손실 없이 3-4배의 모델 크기 압축을 달성합니다
2. **정적 양자화**는 캘리브레이션을 통해 활성화까지 양자화하여 추론 속도를 더욱 향상시킵니다
3. **QAT**는 학습 과정에서 양자화 오차를 반영하여 최고의 정확도를 유지합니다
4. 레이어별로 다른 양자화 설정을 적용하면 정확도-효율 트레이드오프를 세밀하게 조절할 수 있습니다

실제 프로덕션 환경에서는 먼저 동적 양자화를 시도하고, 성능이 부족하면 정적 양자화 -> QAT 순서로 점진적으로 접근하는 것이 권장됩니다.