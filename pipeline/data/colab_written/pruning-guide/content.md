<!-- infographic-hero -->
![Model Pruning: From Magnitude Pruning to Lottery Ticket Hypothesis 핵심 요약](figures/infographic.svg)

*Figure: Model Pruning: From Magnitude Pruning to Lottery Ticket Hypothesis 한 장 요약 인포그래픽*

# 모델 프루닝 완전 가이드: Magnitude 프루닝부터 Lottery Ticket까지

## 소개

딥러닝 모델의 파라미터 중 상당수는 최종 예측에 거의 기여하지 않습니다. **프루닝(Pruning)**은 이러한 불필요한 연결(가중치)이나 뉴런을 제거하여 모델을 압축하는 기술로, 생물학적 시냅스 가지치기에서 영감을 받은 방법입니다.

이 튜토리얼에서는 기본적인 Magnitude 프루닝부터 Lottery Ticket Hypothesis까지 다양한 프루닝 기법을 PyTorch로 구현하고, 각 기법의 성능을 비교 분석합니다.

---

## 1. 모델 프루닝이란?

모델 프루닝은 신경망에서 중요도가 낮은 연결(가중치)이나 뉴런을 제거하여 모델을 압축하는 기술입니다.

### 프루닝의 기본 원리
```
원본 네트워크 -> 중요도 평가 -> 가지치기 -> 압축된 네트워크
```

### 핵심 개념
- **희소성(Sparsity)**: 전체 파라미터 중 0인 파라미터의 비율
- **중요도(Importance)**: 파라미터가 모델 성능에 미치는 영향
- **마스크(Mask)**: 어떤 파라미터를 제거할지 결정하는 이진 마스크

---

## 2. 프루닝의 장점과 단점

### 장점
- **모델 크기 감소**: 50-90% 이상 압축 가능
- **추론 속도 향상**: 특히 구조적 프루닝에서 효과적
- **메모리 사용량 감소**: 엣지 디바이스 배포에 유리
- **정규화 효과**: 과적합 감소 가능

### 단점
- **정확도 손실**: 과도한 프루닝 시 성능 저하
- **재학습 필요**: Fine-tuning 과정 필수
- **하드웨어 의존성**: 비구조적 프루닝은 특수 하드웨어 필요
- **구현 복잡도**: 최적 프루닝 전략 찾기 어려움

---

## 3. 프루닝의 종류

| 분류 | 방식 | 압축률 | 하드웨어 호환성 |
|------|------|--------|---------------|
| **비구조적 프루닝** | 개별 가중치 제거 | 90%+ | 특수 하드웨어 필요 |
| **구조적 프루닝** | 채널/필터 단위 제거 | 50-70% | 일반 하드웨어 호환 |

### 프루닝 기준
- **Magnitude-based**: 가중치 크기 기반 (가장 단순)
- **Gradient-based**: 그래디언트 정보 활용
- **Taylor expansion**: 손실 함수의 테일러 급수 활용
- **Lottery Ticket Hypothesis**: 초기화 값으로 재학습

---

## 4. 실습 환경 설정

```python
import torch
import torch.nn as nn
import torch.nn.utils.prune as prune
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import numpy as np
import copy
import time
import os

# 랜덤 시드 고정
torch.manual_seed(42)
np.random.seed(42)

# GPU 사용 가능 여부 확인
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
```

---

## 5. 프루닝용 CNN 모델 정의

프루닝 실습을 위한 VGG 스타일의 CNN 모델을 정의합니다.

```python
class PrunableCNN(nn.Module):
    """프루닝 실습을 위한 CNN 모델"""
    def __init__(self, num_classes=10):
        super(PrunableCNN, self).__init__()

        # Convolutional layers
        self.features = nn.Sequential(
            # Block 1
            nn.Conv2d(3, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),

            # Block 2
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        # Fully connected layers
        self.classifier = nn.Sequential(
            nn.Linear(128 * 8 * 8, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x
```

2개의 합성곱 블록(각 2개의 Conv-BN-ReLU)과 3개의 완전 연결 레이어로 구성되어 있습니다. Dropout을 포함하여 과적합을 방지합니다.

---

## 6. 유틸리티 함수 정의

프루닝 실험에서 반복적으로 사용하는 유틸리티 함수들을 정의합니다.

```python
def calculate_sparsity(model):
    """모델의 희소성 계산"""
    zeros = 0
    total = 0

    for name, module in model.named_modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            if hasattr(module, 'weight_mask'):
                zeros += (module.weight_mask == 0).sum().item()
                total += module.weight_mask.numel()
            else:
                zeros += (module.weight == 0).sum().item()
                total += module.weight.numel()

    sparsity = zeros / total if total > 0 else 0
    return sparsity * 100

def count_parameters(model):
    """모델의 파라미터 수 계산"""
    total_params = sum(p.numel() for p in model.parameters())
    nonzero_params = sum((p != 0).sum().item() for p in model.parameters())
    return total_params, nonzero_params

def print_model_size(model):
    """모델 크기 정보 출력"""
    total, nonzero = count_parameters(model)
    sparsity = calculate_sparsity(model)

    print(f"총 파라미터: {total:,}")
    print(f"0이 아닌 파라미터: {nonzero:,}")
    print(f"희소성: {sparsity:.2f}%")
    if nonzero > 0:
        print(f"압축률: {total/nonzero:.2f}x")

def get_model_size(model):
    """모델 크기 측정 (MB)"""
    torch.save(model.state_dict(), "temp_model.pth")
    size_mb = os.path.getsize("temp_model.pth") / 1e6
    os.remove("temp_model.pth")
    return size_mb

def measure_inference_time(model, input_shape=(1, 3, 32, 32), num_runs=100):
    """추론 시간 측정"""
    model.eval()
    device = next(model.parameters()).device
    dummy_input = torch.randn(input_shape).to(device)

    # Warm-up
    for _ in range(10):
        with torch.no_grad():
            _ = model(dummy_input)

    start_time = time.time()
    for _ in range(num_runs):
        with torch.no_grad():
            _ = model(dummy_input)
    end_time = time.time()

    avg_time = (end_time - start_time) / num_runs * 1000  # ms
    return avg_time
```

`calculate_sparsity`는 프루닝 마스크가 적용된 경우와 아닌 경우를 모두 처리합니다. PyTorch의 `prune` 모듈은 `weight_mask` 속성을 통해 마스크를 관리합니다.

---

## 7. 데이터 준비 및 학습/평가 함수

```python
def load_cifar10(batch_size=128):
    """CIFAR-10 데이터셋 로드"""
    transform = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
    ])

    trainset = torchvision.datasets.CIFAR10(
        root='./data', train=True, download=True, transform=transform
    )
    trainloader = torch.utils.data.DataLoader(
        trainset, batch_size=batch_size, shuffle=True, num_workers=2
    )

    testset = torchvision.datasets.CIFAR10(
        root='./data', train=False, download=True, transform=transform
    )
    testloader = torch.utils.data.DataLoader(
        testset, batch_size=batch_size, shuffle=False, num_workers=2
    )

    return trainloader, testloader

def train_model(model, train_loader, epochs=10, device='cpu', lr=0.001):
    """모델 학습"""
    model = model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    model.train()
    for epoch in range(epochs):
        running_loss = 0.0
        correct = 0
        total = 0

        for i, (inputs, labels) in enumerate(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

            if i % 100 == 99:
                print(f'[Epoch {epoch + 1}, Batch {i + 1}] '
                      f'Loss: {running_loss / 100:.3f}, '
                      f'Acc: {100 * correct / total:.2f}%')
                running_loss = 0.0

        scheduler.step()

    return model

def evaluate_model(model, test_loader, device='cpu'):
    """모델 평가"""
    model = model.to(device)
    model.eval()
    correct = 0
    total = 0

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    accuracy = 100 * correct / total
    return accuracy
```

---

## 8. Magnitude-based 프루닝 (비구조적)

가장 기본적인 프루닝 방법입니다. 가중치의 **절대값이 작은 것**부터 제거합니다. 직관적으로, 값이 작은 가중치는 출력에 미치는 영향이 적다는 가정에 기반합니다.

```python
def magnitude_pruning(model, pruning_rate=0.2):
    """크기 기반 비구조적 프루닝"""
    for name, module in model.named_modules():
        if isinstance(module, nn.Conv2d):
            prune.l1_unstructured(module, name='weight', amount=pruning_rate)
        elif isinstance(module, nn.Linear):
            prune.l1_unstructured(module, name='weight', amount=pruning_rate)

    return model

def remove_pruning(model):
    """프루닝 마스크를 영구적으로 적용"""
    for name, module in model.named_modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            if hasattr(module, 'weight_mask'):
                prune.remove(module, 'weight')
    return model
```

PyTorch의 `prune.l1_unstructured`는 L1 norm 기준으로 하위 `amount` 비율의 가중치를 0으로 마스킹합니다. `remove_pruning`을 호출하면 마스크가 가중치에 영구적으로 반영됩니다.

---

## 9. 구조적 프루닝 (Structured Pruning)

비구조적 프루닝은 임의의 위치의 가중치를 제거하므로 희소 행렬 연산이 필요합니다. 반면, **구조적 프루닝**은 채널이나 필터 단위로 제거하여 일반 하드웨어에서도 속도 향상을 얻을 수 있습니다.

```python
def structured_pruning(model, pruning_rate=0.2):
    """구조적 프루닝 - 채널 단위"""
    for name, module in model.named_modules():
        if isinstance(module, nn.Conv2d):
            # L2 norm 기준으로 채널 프루닝
            prune.ln_structured(module, name='weight', amount=pruning_rate,
                              n=2, dim=0)  # dim=0은 출력 채널

    return model

def get_channel_importance(conv_layer):
    """채널별 중요도 계산"""
    weights = conv_layer.weight.data
    # 각 출력 채널의 L2 norm 계산
    importance = torch.norm(weights.view(weights.size(0), -1), p=2, dim=1)
    return importance
```

`dim=0`은 출력 채널 방향을 의미합니다. 각 출력 채널의 L2 norm이 작은 채널부터 제거합니다. 이 방식은 제거된 채널에 해당하는 전체 필터가 사라지므로, 실제 연산량이 줄어듭니다.

---

## 10. 반복적 프루닝 (Iterative Pruning)

한 번에 많은 가중치를 제거하면 성능이 급격히 떨어집니다. **반복적 프루닝**은 소량씩 점진적으로 프루닝하고, 매 단계마다 Fine-tuning을 수행합니다.

```python
def iterative_pruning(model, train_loader, test_loader, target_sparsity=0.9,
                     num_iterations=10, device='cpu'):
    """반복적 프루닝 with fine-tuning"""

    model = model.to(device)

    # 프루닝 스케줄 생성
    sparsities = np.linspace(0, target_sparsity, num_iterations)

    results = []

    for i, sparsity in enumerate(sparsities):
        print(f"\n=== 반복 {i+1}/{num_iterations}, "
              f"목표 희소성: {sparsity*100:.1f}% ===")

        # 프루닝 적용
        if i > 0:
            pruning_rate = (sparsity - sparsities[i-1]) / (1 - sparsities[i-1])
            model = magnitude_pruning(model, pruning_rate)

        # Fine-tuning
        if i > 0:
            print("Fine-tuning...")
            model = train_model(model, train_loader, epochs=3, device=device)

        # 평가
        accuracy = evaluate_model(model, test_loader, device)
        current_sparsity = calculate_sparsity(model)

        results.append({
            'iteration': i+1,
            'target_sparsity': sparsity * 100,
            'actual_sparsity': current_sparsity,
            'accuracy': accuracy
        })

        print(f"실제 희소성: {current_sparsity:.2f}%, 정확도: {accuracy:.2f}%")

    return model, results
```

핵심 포인트는 `pruning_rate` 계산입니다. 이미 프루닝된 상태에서 추가로 프루닝할 때, 남은 가중치 대비 비율을 계산해야 합니다.

예를 들어, 현재 30%가 프루닝된 상태에서 50% 희소성을 달성하려면:
$$ \text{pruning\_rate} = \frac{0.5 - 0.3}{1 - 0.3} \approx 0.286 $$

즉, 남은 70%의 가중치 중 약 28.6%를 추가 제거합니다.

---

## 11. Lottery Ticket Hypothesis

Frankle & Carlin (2018)이 제안한 **Lottery Ticket Hypothesis**는 매우 흥미로운 발견입니다:

> "밀집 네트워크에는 초기화 시점부터 독립적으로 학습하여 원래 네트워크와 비슷한 성능에 도달할 수 있는 희소 서브네트워크(당첨 복권)가 존재한다."

핵심 아이디어는:
1. 네트워크를 학습한다
2. 작은 가중치를 프루닝한다
3. **남은 가중치를 초기값으로 되돌린다** (이것이 핵심!)
4. 초기값 상태에서 다시 학습한다

```python
class LotteryTicketPruning:
    """Lottery Ticket Hypothesis 구현"""

    def __init__(self, model, pruning_rate=0.2):
        self.original_model = copy.deepcopy(model)
        self.pruning_rate = pruning_rate
        self.initial_state = None
        self.masks = {}

    def save_initial_weights(self):
        """초기 가중치 저장"""
        self.initial_state = copy.deepcopy(
            self.original_model.state_dict()
        )

    def create_mask(self, model):
        """현재 모델 기반으로 마스크 생성"""
        self.masks = {}

        for name, module in model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                weight = module.weight.data.abs()
                threshold = torch.quantile(
                    weight.flatten(), self.pruning_rate
                )
                mask = weight > threshold
                self.masks[name + '.weight'] = mask

    def apply_mask(self, model):
        """마스크를 모델에 적용"""
        for name, module in model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                key = name + '.weight'
                if key in self.masks:
                    module.weight.data *= self.masks[key]

    def find_winning_ticket(self, train_loader, test_loader, iterations=3,
                          epochs_per_iteration=5, device='cpu'):
        """우승 복권 찾기"""

        self.save_initial_weights()
        results = []

        for iteration in range(iterations):
            print(f"\n=== Lottery Ticket 반복 "
                  f"{iteration+1}/{iterations} ===")

            # 모델 초기화
            model = copy.deepcopy(self.original_model)
            model.load_state_dict(self.initial_state)
            model = model.to(device)

            # 이전 마스크가 있으면 적용
            if self.masks:
                self.apply_mask(model)

            # 학습
            print("모델 학습 중...")
            model = train_model(
                model, train_loader,
                epochs=epochs_per_iteration, device=device
            )

            # 새로운 마스크 생성
            self.create_mask(model)

            # 초기 가중치로 되돌리고 마스크 적용
            model.load_state_dict(self.initial_state)
            self.apply_mask(model)

            # 재학습
            print("재학습 중...")
            model = train_model(
                model, train_loader,
                epochs=epochs_per_iteration, device=device
            )

            # 평가
            accuracy = evaluate_model(model, test_loader, device)
            sparsity = calculate_sparsity(model)

            results.append({
                'iteration': iteration + 1,
                'sparsity': sparsity,
                'accuracy': accuracy
            })

            print(f"희소성: {sparsity:.2f}%, 정확도: {accuracy:.2f}%")

            # 다음 반복을 위해 pruning rate 증가
            self.pruning_rate = min(self.pruning_rate + 0.2, 0.9)

        return model, results
```

Lottery Ticket의 핵심은 `find_winning_ticket` 메서드에서 볼 수 있듯이, 학습 후 만들어진 마스크를 **초기 가중치에 적용**한 후 다시 학습하는 것입니다. 이를 통해 처음부터 효율적인 구조를 가진 서브네트워크를 발견합니다.

---

## 12. 고급 기법: 그래디언트 기반 프루닝

Magnitude 기반 프루닝은 가중치의 크기만 고려합니다. 그러나 **작은 가중치도 그래디언트가 크면 학습에 중요할 수 있습니다.** 그래디언트 기반 프루닝은 이를 고려합니다.

```python
class GradientBasedPruning:
    """그래디언트 정보를 활용한 프루닝"""

    def __init__(self, model):
        self.model = model
        self.gradients = {}
        self.register_hooks()

    def register_hooks(self):
        """그래디언트 수집을 위한 hook 등록"""
        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                module.register_backward_hook(
                    self.save_gradient(name)
                )

    def save_gradient(self, name):
        def hook(module, grad_input, grad_output):
            if hasattr(module, 'weight'):
                grad = module.weight.grad
                if grad is not None:
                    if name not in self.gradients:
                        self.gradients[name] = []
                    self.gradients[name].append(grad.abs().clone())
        return hook

    def compute_importance(self):
        """평균 그래디언트 기반 중요도 계산"""
        importance_scores = {}

        for name, grad_list in self.gradients.items():
            if grad_list:
                avg_grad = torch.stack(grad_list).mean(dim=0)
                importance_scores[name] = avg_grad

        return importance_scores

    def prune_by_gradient(self, pruning_rate=0.2):
        """그래디언트 기반 프루닝 적용"""
        importance_scores = self.compute_importance()

        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)) \
               and name in importance_scores:
                importance = importance_scores[name]
                threshold = torch.quantile(
                    importance.flatten(), pruning_rate
                )
                mask = importance > threshold

                with torch.no_grad():
                    module.weight.data *= mask
```

그래디언트 기반 프루닝은 backward hook을 통해 학습 중 그래디언트를 수집하고, 평균 그래디언트가 작은 가중치를 제거합니다.

---

## 13. 고급 기법: Taylor Expansion 프루닝

Taylor expansion 기반 프루닝은 손실 함수에 대한 1차 테일러 전개를 사용하여, 각 파라미터를 제거했을 때의 손실 변화량을 추정합니다.

$$
\Delta L \approx |\frac{\partial L}{\partial a_i} \cdot a_i|
$$

여기서 $a_i$는 활성화 값이고, 이 값이 작을수록 해당 채널을 제거해도 손실에 미치는 영향이 작습니다.

```python
def taylor_pruning(model, data_loader, pruning_rate=0.2):
    """Taylor expansion을 이용한 중요도 계산"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()

    gradients = {}
    activations = {}

    def forward_hook(name):
        def hook(module, input, output):
            activations[name] = output.detach()
        return hook

    def backward_hook(name):
        def hook(module, grad_input, grad_output):
            gradients[name] = grad_output[0].detach()
        return hook

    # Hook 등록
    handles = []
    for name, module in model.named_modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            handles.append(
                module.register_forward_hook(forward_hook(name))
            )
            handles.append(
                module.register_backward_hook(backward_hook(name))
            )

    # 데이터 통과
    criterion = nn.CrossEntropyLoss()
    for inputs, targets in data_loader:
        inputs, targets = inputs.to(device), targets.to(device)
        outputs = model(inputs)
        loss = criterion(outputs, targets)
        loss.backward()
        break  # 한 배치만 사용

    # Hook 제거
    for handle in handles:
        handle.remove()

    # Taylor importance 계산 및 프루닝
    for name, module in model.named_modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)) \
           and name in activations:
            # Importance = |gradient * activation|
            importance = (
                gradients[name] * activations[name]
            ).abs().mean(dim=0)

            if len(importance.shape) > 1:  # Conv2d
                importance = importance.mean(dim=(1, 2))  # 채널별 평균

            # 프루닝 적용
            num_channels = importance.shape[0]
            num_prune = int(num_channels * pruning_rate)
            _, indices = torch.topk(importance, num_prune, largest=False)

            mask = torch.ones_like(module.weight.data)
            mask[indices] = 0
            prune.custom_from_mask(module, name='weight', mask=mask)

    return model
```

---

## 14. 고급 기법: 동적 희소 학습 (Dynamic Sparse Training)

기존 프루닝은 한 번 제거한 연결을 복구하지 않습니다. **동적 희소 학습**은 학습 중에 연결을 제거하면서 동시에 새로운 연결을 추가합니다.

```python
class DynamicSparseTraining:
    """학습 중 동적으로 연결을 추가/제거"""

    def __init__(self, model, sparsity=0.9, update_frequency=100):
        self.model = model
        self.sparsity = sparsity
        self.update_frequency = update_frequency
        self.step = 0
        self.masks = self.create_initial_masks()

    def create_initial_masks(self):
        """초기 마스크 생성 (랜덤)"""
        masks = {}

        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)):
                shape = module.weight.shape
                mask = torch.rand(shape) > self.sparsity
                masks[name] = mask.to(module.weight.device)
                module.weight.data *= masks[name]

        return masks

    def update_connections(self):
        """Grow and prune connections"""
        for name, module in self.model.named_modules():
            if isinstance(module, (nn.Conv2d, nn.Linear)) \
               and name in self.masks:
                weights = module.weight.data
                mask = self.masks[name]

                # Prune: 작은 가중치 제거
                alive_weights = weights[mask.bool()]
                percentile = 20
                threshold = torch.quantile(
                    alive_weights.abs(), percentile/100
                )
                new_mask = (weights.abs() > threshold) & mask.bool()

                # Grow: 그래디언트가 큰 위치에 연결 추가
                num_removed = mask.sum() - new_mask.sum()
                if num_removed > 0 and hasattr(module.weight, 'grad') \
                   and module.weight.grad is not None:
                    grad_magnitude = module.weight.grad.abs()
                    grad_magnitude[mask.bool()] = 0

                    _, indices = torch.topk(
                        grad_magnitude.flatten(), num_removed.item()
                    )
                    new_connections = torch.zeros_like(
                        mask.flatten()
                    )
                    new_connections[indices] = 1
                    new_connections = new_connections.reshape(mask.shape)

                    new_mask = new_mask | new_connections.bool()

                self.masks[name] = new_mask.float()
                module.weight.data *= self.masks[name]

    def step_update(self):
        """학습 스텝마다 호출"""
        self.step += 1
        if self.step % self.update_frequency == 0:
            self.update_connections()
```

동적 희소 학습의 핵심은 **Grow and Prune** 전략입니다:
- **Prune**: 현재 활성 연결 중 가중치가 작은 것을 제거
- **Grow**: 제거한 만큼의 새로운 연결을 그래디언트가 큰 위치에 추가

이를 통해 전체 희소성은 유지하면서 네트워크 구조가 학습 과정에서 진화합니다.

---

## 15. 종합 비교 실험

모든 프루닝 기법을 CIFAR-10에서 비교 실험합니다.

```python
def comprehensive_pruning_comparison(model, train_loader, test_loader):
    """다양한 프루닝 기법 비교"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    results = {
        'method': [], 'sparsity': [], 'accuracy': [],
        'inference_time': [], 'model_size': []
    }

    # 1. 원본 모델
    original_model = copy.deepcopy(model).to(device)
    original_acc = evaluate_model(original_model, test_loader, device)
    results['method'].append('Original')
    results['sparsity'].append(0)
    results['accuracy'].append(original_acc)
    results['inference_time'].append(measure_inference_time(original_model))
    results['model_size'].append(get_model_size(original_model))

    # 2. Magnitude Pruning (50%)
    mag_model = copy.deepcopy(model).to(device)
    mag_model = magnitude_pruning(mag_model, pruning_rate=0.5)
    mag_model = train_model(mag_model, train_loader, epochs=5, device=device)
    results['method'].append('Magnitude (50%)')
    results['sparsity'].append(calculate_sparsity(mag_model))
    results['accuracy'].append(evaluate_model(mag_model, test_loader, device))
    results['inference_time'].append(measure_inference_time(mag_model))
    results['model_size'].append(get_model_size(mag_model))

    # 3. Structured Pruning (30%)
    struct_model = copy.deepcopy(model).to(device)
    struct_model = structured_pruning(struct_model, pruning_rate=0.3)
    struct_model = train_model(
        struct_model, train_loader, epochs=5, device=device
    )
    results['method'].append('Structured (30%)')
    results['sparsity'].append(calculate_sparsity(struct_model))
    results['accuracy'].append(
        evaluate_model(struct_model, test_loader, device)
    )
    results['inference_time'].append(measure_inference_time(struct_model))
    results['model_size'].append(get_model_size(struct_model))

    return results

# 실행
train_loader, test_loader = load_cifar10(batch_size=128)
model = PrunableCNN().to(device)
model = train_model(model, train_loader, epochs=5, device=device)
results = comprehensive_pruning_comparison(model, train_loader, test_loader)
```

> 비교 결과를 시각화하면, 정확도 vs 희소성 트레이드오프, 추론 시간 비교, 모델 크기 비교, 그리고 정확도-희소성 산점도의 4개 차트가 출력됩니다. Magnitude 프루닝은 높은 희소성을 달성하면서도 Fine-tuning을 통해 정확도를 유지하고, 구조적 프루닝은 실제 추론 속도 향상에 더 효과적임을 확인할 수 있습니다.

---

## 16. 시각화: 가중치 분포 변화

프루닝 전후의 가중치 분포를 시각화하면 프루닝의 효과를 직관적으로 이해할 수 있습니다.

```python
def visualize_weight_distribution(model):
    """가중치 분포 시각화"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.ravel()

    layer_idx = 0
    for name, module in model.named_modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            if layer_idx >= 4:
                break

            weights = module.weight.data.cpu().numpy().flatten()

            axes[layer_idx].hist(
                weights, bins=50, alpha=0.7,
                color='blue', edgecolor='black'
            )
            axes[layer_idx].axvline(
                x=0, color='red', linestyle='--', alpha=0.5
            )
            axes[layer_idx].set_title(f'{name} Weight Distribution')
            axes[layer_idx].set_xlabel('Weight Value')
            axes[layer_idx].set_ylabel('Frequency')

            zeros = (weights == 0).sum()
            total = len(weights)
            sparsity = zeros / total * 100

            stats_text = (f'Sparsity: {sparsity:.1f}%\n'
                         f'Mean: {weights.mean():.4f}\n'
                         f'Std: {weights.std():.4f}')
            axes[layer_idx].text(
                0.7, 0.9, stats_text,
                transform=axes[layer_idx].transAxes,
                verticalalignment='top',
                bbox=dict(
                    boxstyle='round', facecolor='wheat', alpha=0.5
                )
            )

            layer_idx += 1

    plt.tight_layout()
    plt.show()
```

> 프루닝 후 가중치 분포를 시각화하면, 0 주변에 큰 스파이크가 형성되는 것을 확인할 수 있습니다. 이는 프루닝된 가중치들이 0으로 설정되었기 때문입니다. 나머지 가중치들은 원래의 분포를 유지합니다.

---

## 17. Best Practices

### 프루닝 전략 선택 가이드

| 시나리오 | 추천 기법 | 이유 |
|---------|----------|------|
| 빠른 모델 압축 | Magnitude Pruning | 구현 간단, 효과적 |
| 엣지 디바이스 배포 | Structured Pruning | 하드웨어 호환성 |
| 최고 성능 추구 | Iterative Pruning + Fine-tuning | 점진적 압축 |
| 연구/실험 | Lottery Ticket | 이론적 의미 |
| 학습 중 적용 | Dynamic Sparse Training | 별도 프루닝 단계 불필요 |

### 실전 팁

1. **점진적 프루닝**: 한 번에 50% 이상 프루닝하지 말고, 10-20%씩 반복적으로 수행
2. **Fine-tuning 필수**: 프루닝 후 반드시 재학습하여 성능 회복
3. **레이어별 차별화**: 첫 번째 레이어와 마지막 레이어는 보수적으로 프루닝
4. **검증 세트 모니터링**: 프루닝 비율을 높이면서 검증 정확도를 지속 모니터링
5. **구조적 프루닝 우선**: 실제 속도 향상이 필요하면 구조적 프루닝을 먼저 시도

---

## 결론

이 튜토리얼에서는 다양한 모델 프루닝 기법의 원리와 PyTorch 구현을 살펴보았습니다.

**핵심 정리:**

1. **Magnitude Pruning**은 가장 기본적이고 효과적인 방법으로, 가중치의 절대값이 작은 것부터 제거합니다
2. **구조적 프루닝**은 채널/필터 단위로 제거하여 실제 하드웨어에서 속도 향상을 얻을 수 있습니다
3. **반복적 프루닝**은 점진적으로 프루닝하고 Fine-tuning하여 높은 압축률에서도 성능을 유지합니다
4. **Lottery Ticket Hypothesis**는 초기 가중치 중 효율적인 서브네트워크를 발견하는 이론적으로 의미 있는 접근법입니다
5. **그래디언트/Taylor 기반 프루닝**은 가중치 크기뿐만 아니라 학습 역학까지 고려하여 더 정교한 프루닝을 수행합니다

프루닝은 양자화(Quantization), 지식 증류(Knowledge Distillation)와 함께 사용하면 시너지 효과를 낼 수 있습니다. 실제 프로덕션 환경에서는 이 세 가지 기법을 조합하여 최적의 모델 경량화를 달성하는 것이 일반적입니다.