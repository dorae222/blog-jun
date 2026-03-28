# 최적화 이론: 경사하강법과 그 변종들

## 1. 개요: 학습 = 최적화 문제

머신러닝의 학습(Training) 과정은 본질적으로 **최적화(Optimization)** 문제입니다. 우리가 가진 데이터 $\{(x_i, y_i)\}_{i=1}^{n}$에 대해 모델 파라미터 $\theta$를 조정하여 손실 함수(Loss Function) $\mathcal{L}(\theta)$를 최소화하는 파라미터를 찾는 것이 목표입니다:

$$
\theta^* = \arg\min_{\theta} \mathcal{L}(\theta)
$$

예를 들어 회귀 문제에서 평균 제곱 오차(MSE)는 $\mathcal{L}(\theta) = \frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2$이며, 분류 문제에서 크로스 엔트로피는 $\mathcal{L}(\theta) = -\frac{1}{n}\sum_{i=1}^{n}[y_i \log \hat{y}_i + (1-y_i)\log(1-\hat{y}_i)]$입니다.

최적화 알고리즘(옵티마이저)의 선택은 모델의 수렴 속도, 최종 성능, 학습 안정성에 직접적인 영향을 미칩니다. 선형 회귀처럼 볼록 함수(Convex Function)라면 전역 최솟값(Global Minimum)이 보장되지만, 딥러닝의 손실 지형(Loss Landscape)은 수백만 개의 파라미터가 만들어내는 고차원 비볼록 공간으로, 안장점(Saddle Point), 지역 최솟값(Local Minimum), 평탄 구간(Plateau) 등 다양한 함정이 존재합니다. 이 때문에 단순한 최적화 방법으로는 한계가 있으며, 수십 년에 걸쳐 다양한 옵티마이저가 개발되어 왔습니다.

---

## 2. 기본 경사하강법 (Gradient Descent)

![경사하강법 경로 비교: 다양한 옵티마이저의 손실 지형 위 최적화 경로](figures/gradient_descent_paths.png)
*경사하강법 경로: GD, 모멘텀, RMSProp, Adam 등 다양한 옵티마이저가 비볼록 손실 지형에서 최솟값을 향해 이동하는 경로를 비교한다.*

### 2.1 기본 업데이트 규칙

경사하강법(Gradient Descent, GD)은 손실 함수의 그래디언트(Gradient) 방향의 반대 방향으로 파라미터를 이동시키는 가장 기본적인 최적화 알고리즘입니다:

$$
\theta \leftarrow \theta - \alpha \nabla_\theta \mathcal{L}(\theta)
$$

여기서 $\alpha > 0$는 **학습률(Learning Rate)**이며, $\nabla_\theta \mathcal{L}(\theta)$는 손실 함수의 파라미터에 대한 그래디언트입니다. 그래디언트는 손실이 가장 가파르게 증가하는 방향을 가리키므로, 음의 그래디언트 방향으로 이동하면 손실이 감소합니다.

### 2.2 학습률의 중요성

학습률 $\alpha$는 최적화 과정에서 가장 민감한 하이퍼파라미터입니다:

- **$\alpha$가 너무 크면**: 손실이 발산(Diverge)하거나 최솟값 주변에서 진동(Oscillation)하여 수렴하지 못합니다.
- **$\alpha$가 너무 작으면**: 수렴 속도가 극히 느려지고, 실용적인 시간 내에 학습이 완료되지 않습니다.
- **적절한 $\alpha$**: 안정적으로 손실이 감소하며 합리적인 속도로 수렴합니다.

일반적인 시작값으로는 $\alpha = 0.01$ 또는 $\alpha = 0.001$을 사용하고, 손실 곡선을 보며 조정합니다.

### 2.3 볼록 vs 비볼록 최적화

**볼록 최적화(Convex Optimization)**에서는 지역 최솟값이 곧 전역 최솟값이므로, 경사하강법이 반드시 최적해에 수렴합니다. 선형 회귀, 로지스틱 회귀, SVM(소프트 마진)이 여기에 해당합니다.

**비볼록 최적화(Non-convex Optimization)**에서는 손실 지형이 복잡하여 다음과 같은 문제가 발생합니다:
- **지역 최솟값(Local Minimum)**: 주변보다는 낮지만 전역 최솟값은 아닌 지점
- **안장점(Saddle Point)**: 일부 방향에서는 최솟값이지만 다른 방향에서는 최댓값인 지점 ( 고차원에서 더 흔하게 발생
- **평탄 구간(Plateau)**: 그래디언트가 거의 0에 가까워 학습이 멈추는 듯 보이는 구간

흥미롭게도, 딥러닝 실무에서 지역 최솟값은 생각만큼 큰 문제가 아닙니다. 고차원 공간에서 진짜 지역 최솟값(모든 방향에서 최솟값)은 매우 드물고, 대부분의 "막히는" 지점은 안장점이기 때문입니다.

---

## 3. SGD와 Mini-Batch GD

### 3.1 세 가지 경사하강법 변종 비교

전체 학습 데이터를 어떻게 사용하느냐에 따라 세 가지 변종이 있습니다:

**배치 경사하강법(Batch GD)**:
- 매 업데이트마다 전체 데이터셋을 사용하여 그래디언트를 계산
- 장점: 그래디언트 추정이 정확하여 수렴이 안정적
- 단점: 데이터가 크면 매 스텝이 매우 느리고, 메모리 요구량이 큼

**확률적 경사하강법(Stochastic GD, SGD)**:
- 매 업데이트마다 단 하나의 샘플만 사용
- 장점: 업데이트가 빠르고, 잡음(Noise)으로 인해 지역 최솟값 탈출 가능
- 단점: 그래디언트 추정의 분산이 커서 수렴 경로가 불안정하고 진동이 심함

**미니배치 경사하강법(Mini-Batch GD)**:
- 매 업데이트마다 작은 배치(보통 32~512개)의 샘플을 사용
- 장점: 배치 GD와 SGD의 장점을 절충 ) GPU 병렬 연산 효율적, 적절한 잡음으로 정규화 효과
- 현대 딥러닝의 표준 방법

| 특성 | 배치 GD | SGD | 미니배치 GD |
|------|---------|-----|-------------|
| 그래디언트 추정 정확도 | 정확 | 부정확 (고분산) | 중간 |
| 업데이트 속도 | 느림 | 빠름 | 빠름 |
| 수렴 안정성 | 안정 | 불안정 | 중간 |
| GPU 효율성 | 낮음 | 매우 낮음 | 높음 |
| 지역 최솟값 탈출 | 어려움 | 쉬움 | 중간 |

### 3.2 잡음의 역할: 지역 최솟값 탈출

SGD의 확률적 특성은 단순한 단점이 아니라, 오히려 **암묵적 정규화(Implicit Regularization)** 효과를 가집니다. 잡음이 있는 그래디언트는 얕은 지역 최솟값(Narrow Local Minimum)에서 탈출하는 데 도움을 주며, 더 평탄하고 일반화 성능이 좋은 넓은 최솟값(Flat Minimum)으로 수렴하는 경향이 있습니다. 배치 크기가 작을수록 잡음이 크고, 이 특성을 활용하기 위해 의도적으로 작은 배치를 사용하기도 합니다.

---

## 4. 모멘텀 (Momentum)

### 4.1 모멘텀의 직관

기본 SGD의 가장 큰 문제는 그래디언트의 방향이 매 스텝마다 크게 변동하여 수렴이 느리다는 점입니다. **모멘텀(Momentum)**은 물리학의 관성 개념을 차용하여, 이전 업데이트 방향의 일부를 현재 업데이트에 누적합니다:

$$
v_t = \beta v_{t-1} + \alpha \nabla_\theta \mathcal{L}(\theta)
$$
$$
\theta \leftarrow \theta - v_t
$$

여기서 $v_t$는 속도(Velocity) 벡터이고, $\beta$는 모멘텀 계수(보통 0.9)입니다. 과거 그래디언트들이 지수적으로 감소하는 가중치로 합산되어, 일관된 방향으로는 빠르게 가속되고 진동하는 방향은 상쇄됩니다. 이는 좁고 긴 골짜기(손실 지형에서 흔히 나타나는 형태) 형태의 최적화 지형에서 특히 효과적입니다.

### 4.2 Nesterov Momentum

**Nesterov 가속 경사법(Nesterov Accelerated Gradient, NAG)**은 모멘텀의 개선 버전으로, 현재 위치가 아닌 **미래 위치(Look-ahead)**에서 그래디언트를 계산합니다:

$$
v_t = \beta v_{t-1} + \alpha \nabla_\theta \mathcal{L}(\theta - \beta v_{t-1})
$$
$$
\theta \leftarrow \theta - v_t
$$

기본 모멘텀이 "달리다가 그제서야 방향을 보는" 것이라면, NAG는 "모멘텀으로 이동할 것으로 예상되는 위치에서 미리 방향을 확인하는" 방식입니다. 이로 인해 반응이 더 빠르고, 최솟값에 가까워질수록 속도를 줄이는 효과가 있어 수렴이 더 안정적입니다. 이론적으로 NAG는 볼록 함수에서 $O(1/t^2)$ 수렴 속도를 보장하며, 기본 GD의 $O(1/t)$보다 빠릅니다.

---

## 5. 적응적 학습률 방법들

### 5.1 문제 인식: 파라미터마다 다른 스케일

기본 SGD와 모멘텀의 한계는 **모든 파라미터에 동일한 학습률**을 적용한다는 점입니다. 실제로 자주 등장하는 피처의 파라미터와 드물게 등장하는 피처의 파라미터는 업데이트 필요량이 다릅니다. NLP에서 희소한 단어 임베딩이 대표적인 예입니다. 적응적 학습률(Adaptive Learning Rate) 방법들은 각 파라미터의 과거 그래디언트 정보를 이용하여 파라미터별로 학습률을 자동 조정합니다.

### 5.2 AdaGrad

**AdaGrad(Adaptive Gradient)**는 각 파라미터에 대한 그래디언트의 제곱합을 누적하여, 많이 업데이트된 파라미터의 학습률을 줄이고 적게 업데이트된 파라미터의 학습률을 크게 유지합니다:

$$
G_t = G_{t-1} + g_t^2
$$
$$
\theta \leftarrow \theta - \frac{\alpha}{\sqrt{G_t + \epsilon}} g_t
$$

여기서 $g_t = \nabla_\theta \mathcal{L}(\theta_t)$이고, $\epsilon$은 수치 안정성을 위한 작은 값(보통 $10^{-8}$)입니다. 희소한 그래디언트에 효과적이지만, $G_t$가 단조 증가하여 학습이 진행될수록 학습률이 0에 수렴하는 **학습률 소멸(Learning Rate Vanishing)** 문제가 있습니다.

### 5.3 RMSProp

**RMSProp(Root Mean Square Propagation)**은 AdaGrad의 학습률 소멸 문제를 **지수 이동 평균(Exponential Moving Average)**으로 해결합니다:

$$
E[g^2]_t = \rho \cdot E[g^2]_{t-1} + (1-\rho) \cdot g_t^2
$$
$$
\theta \leftarrow \theta - \frac{\alpha}{\sqrt{E[g^2]_t + \epsilon}} g_t
$$

감쇠 계수 $\rho$(보통 0.9)를 통해 오래된 그래디언트 정보는 지수적으로 소멸시키고 최근 그래디언트에 더 높은 가중치를 부여합니다. 이로써 학습률이 0으로 수렴하는 문제를 방지하면서 적응적 조정을 유지합니다. RNN 학습에서 특히 효과적인 것으로 알려져 있습니다.

### 5.4 Adam

**Adam(Adaptive Moment Estimation)**은 현재 가장 널리 사용되는 옵티마이저로, **모멘텀**(1차 모멘트, 그래디언트의 이동 평균)과 **RMSProp**(2차 모멘트, 그래디언트 제곱의 이동 평균)을 결합합니다:

**1차 모멘트 (편향 없는 이동 평균):**
$$
m_t = \beta_1 m_{t-1} + (1-\beta_1) g_t
$$

**2차 모멘트 (편향 없는 그래디언트 제곱 이동 평균):**
$$
v_t = \beta_2 v_{t-1} + (1-\beta_2) g_t^2
$$

**편향 보정(Bias Correction):**
$$
\hat{m}_t = \frac{m_t}{1-\beta_1^t}, \quad \hat{v}_t = \frac{v_t}{1-\beta_2^t}
$$

**파라미터 업데이트:**
$$
\theta \leftarrow \theta - \frac{\alpha}{\sqrt{\hat{v}_t} + \epsilon} \hat{m}_t
$$

일반적인 기본값은 $\beta_1 = 0.9$, $\beta_2 = 0.999$, $\epsilon = 10^{-8}$이며, 학습률은 $\alpha = 0.001$에서 시작합니다.

### 5.5 편향 보정의 중요성

편향 보정이 필요한 이유는 초기화 때문입니다. $m_0 = 0$, $v_0 = 0$으로 초기화하면 학습 초반($t$가 작을 때) $m_t$와 $v_t$가 실제 값보다 0에 가깝게 **편향(Bias)**됩니다. 예를 들어 $t=1$일 때 $m_1 = (1-\beta_1)g_1 = 0.1 g_1$으로, 실제 그래디언트보다 10배 작습니다. 편향 보정 $\hat{m}_1 = m_1 / (1-0.9) = g_1$으로 이를 보정합니다. $t$가 커질수록 $\beta_1^t \to 0$이 되어 보정 효과는 사라집니다.

---

![학습률 비교: 학습률 크기에 따른 수렴 속도와 안정성 차이](figures/learning_rate_comparison.png)
*학습률 비교: 학습률이 너무 크면 발산하고, 너무 작으면 수렴이 느리며, 적절한 학습률에서 안정적으로 최솟값에 도달한다.*

## 6. 학습률 스케줄링 (Learning Rate Scheduling)

고정된 학습률보다 학습 과정에서 학습률을 동적으로 조정하면 성능이 크게 개선됩니다.

### 6.1 Step Decay

일정 에포크마다 학습률을 고정 비율로 감소시킵니다:

$$
\alpha_t = \alpha_0 \cdot \gamma^{\lfloor t / s \rfloor}
$$

여기서 $\gamma$는 감쇠율(보통 0.1 또는 0.5), $s$는 감쇠 주기입니다. 직관적이고 구현이 쉽지만, 언제 감쇠할지를 미리 결정해야 합니다.

### 6.2 Cosine Annealing

학습률을 코사인 함수 형태로 부드럽게 감소시킵니다:

$$
\alpha_t = \alpha_{\min} + \frac{1}{2}(\alpha_{\max} - \alpha_{\min})\left(1 + \cos\frac{\pi t}{T}\right)
$$

급격한 변화 없이 부드럽게 학습률이 감소하여 최적화 경로가 안정적입니다. **Cosine Annealing with Warm Restarts(SGDR)**는 주기적으로 학습률을 재시작하여 여러 지역 최솟값을 탐색하는 변종입니다.

### 6.3 Warmup

학습 초반에 학습률을 작게 시작해서 점진적으로 목표 학습률까지 증가시키는 기법입니다:

$$
\alpha_t = \alpha_{\max} \cdot \frac{t}{T_{\text{warmup}}}, \quad t \leq T_{\text{warmup}}
$$

대형 배치 학습이나 Transformer 학습에서 특히 중요합니다. 학습 초반에는 파라미터와 Adam의 2차 모멘트 추정이 불안정하여 큰 학습률이 발산을 유발할 수 있기 때문입니다. BERT, GPT 등 대부분의 트랜스포머 모델이 Warmup + Cosine Decay 조합을 사용합니다.

---

## 7. 실전 옵티마이저 선택 가이드

| 상황 | 권장 옵티마이저 | 이유 |
|------|----------------|------|
| 딥러닝 일반 | **Adam** ($\alpha=0.001$) | 적응적 학습률, 빠른 수렴, 튜닝 부담 적음 |
| 이미지 분류 (ResNet 등) | **SGD + 모멘텀** + LR 스케줄 | 최종 성능이 Adam보다 높은 경우 많음 |
| NLP / Transformer | **AdamW** + Warmup + Cosine Decay | 희소 임베딩 적응, 가중치 감쇠 안정적 적용 |
| 희소 피처 (추천 시스템) | **AdaGrad** 또는 **Adam** | 드문 피처에 큰 업데이트 허용 |
| RNN 계열 | **RMSProp** 또는 **Adam** | 그래디언트 폭발/소멸에 안정적 |
| 볼록 최적화 (선형 모델) | **SGD** 또는 **L-BFGS** | 수렴 보장, 효율적 |
| 빠른 프로토타이핑 | **Adam** | 학습률 튜닝 없이도 준수한 성능 |

**AdamW**는 Adam의 가중치 감쇠(Weight Decay) 처리 방식을 개선한 버전입니다. Adam에서 L2 정규화는 그래디언트에 포함되어 적응적 스케일링의 영향을 받지만, AdamW는 가중치 감쇠를 그래디언트 업데이트와 분리하여 더 일관된 정규화 효과를 제공합니다.

실무 팁:
- Adam으로 시작해서 학습이 어느 정도 안정화되면 SGD+모멘텀으로 파인튜닝하는 전략도 효과적
- 배치 크기를 키울 때는 학습률도 비례하여 증가 (Linear Scaling Rule)
- 그래디언트 클리핑(Gradient Clipping)은 RNN, Transformer에서 폭발적 그래디언트 방지에 필수

---

## 8. Python 코드: 옵티마이저 비교 시각화

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# ============================================================
# 1. 2D 손실 지형에서 각 옵티마이저 경로 시각화
# ============================================================

def beale_function(x, y):
    """Beale 함수: 비볼록 테스트 함수, 최솟값 (3, 0.5)"""
    return ((1.5 - x + x*y)**2 +
            (2.25 - x + x*y**2)**2 +
            (2.625 - x + x*y**3)**2)

def beale_gradient(x, y):
    """Beale 함수의 수치 그래디언트"""
    h = 1e-5
    gx = (beale_function(x+h, y) - beale_function(x-h, y)) / (2*h)
    gy = (beale_function(x, y+h) - beale_function(x, y-h)) / (2*h)
    return np.array([gx, gy])


class GradientDescent:
    def __init__(self, lr=0.001):
        self.lr = lr
        self.name = f'GD (lr={lr})'

    def step(self, params, grad):
        return params - self.lr * grad


class MomentumOptimizer:
    def __init__(self, lr=0.001, beta=0.9):
        self.lr, self.beta = lr, beta
        self.v = None
        self.name = f'Momentum (lr={lr}, β={beta})'

    def step(self, params, grad):
        if self.v is None:
            self.v = np.zeros_like(params)
        self.v = self.beta * self.v + self.lr * grad
        return params - self.v


class AdaGradOptimizer:
    def __init__(self, lr=0.1, eps=1e-8):
        self.lr, self.eps = lr, eps
        self.G = None
        self.name = f'AdaGrad (lr={lr})'

    def step(self, params, grad):
        if self.G is None:
            self.G = np.zeros_like(params)
        self.G += grad ** 2
        return params - self.lr / (np.sqrt(self.G) + self.eps) * grad


class RMSPropOptimizer:
    def __init__(self, lr=0.01, rho=0.9, eps=1e-8):
        self.lr, self.rho, self.eps = lr, rho, eps
        self.E = None
        self.name = f'RMSProp (lr={lr})'

    def step(self, params, grad):
        if self.E is None:
            self.E = np.zeros_like(params)
        self.E = self.rho * self.E + (1 - self.rho) * grad ** 2
        return params - self.lr / (np.sqrt(self.E) + self.eps) * grad


class AdamOptimizer:
    def __init__(self, lr=0.1, beta1=0.9, beta2=0.999, eps=1e-8):
        self.lr, self.beta1, self.beta2, self.eps = lr, beta1, beta2, eps
        self.m, self.v, self.t = None, None, 0
        self.name = f'Adam (lr={lr})'

    def step(self, params, grad):
        if self.m is None:
            self.m = np.zeros_like(params)
            self.v = np.zeros_like(params)
        self.t += 1
        self.m = self.beta1 * self.m + (1 - self.beta1) * grad
        self.v = self.beta2 * self.v + (1 - self.beta2) * grad ** 2
        m_hat = self.m / (1 - self.beta1 ** self.t)
        v_hat = self.v / (1 - self.beta2 ** self.t)
        return params - self.lr / (np.sqrt(v_hat) + self.eps) * m_hat


def run_optimizer(optimizer, start, n_steps=200):
    """옵티마이저를 실행하고 경로를 반환"""
    path = [start.copy()]
    params = start.copy()
    for _ in range(n_steps):
        grad = beale_gradient(params[0], params[1])
        # 그래디언트 클리핑 (발산 방지)
        grad = np.clip(grad, -10, 10)
        params = optimizer.step(params, grad)
        params = np.clip(params, -4.5, 4.5)  # 경계 제한
        path.append(params.copy())
    return np.array(path)


# 시각화
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# 손실 지형 그리드
x_range = np.linspace(-4.5, 4.5, 300)
y_range = np.linspace(-4.5, 4.5, 300)
X, Y = np.meshgrid(x_range, y_range)
Z = beale_function(X, Y)

start = np.array([-3.0, -1.0])
optimizers = [
    GradientDescent(lr=0.001),
    MomentumOptimizer(lr=0.001, beta=0.9),
    RMSPropOptimizer(lr=0.01),
    AdamOptimizer(lr=0.1),
]
colors = ['blue', 'green', 'orange', 'red']

# 왼쪽: 경로 시각화
ax = axes[0]
cf = ax.contourf(X, Y, Z, levels=50, cmap='viridis',
                  norm=LogNorm(vmin=Z.min()+1e-5, vmax=Z.max()))
plt.colorbar(cf, ax=ax, label='Loss (log scale)')
ax.plot(*[3, 0.5], 'w*', markersize=15, label='Global Min (3, 0.5)')

for opt, color in zip(optimizers, colors):
    path = run_optimizer(opt, start)
    ax.plot(path[:, 0], path[:, 1], '-', color=color,
            linewidth=1.5, alpha=0.8, label=opt.name)
    ax.plot(path[0, 0], path[0, 1], 'o', color=color, markersize=8)
    ax.plot(path[-1, 0], path[-1, 1], 's', color=color, markersize=8)

ax.set_title('Optimizer Paths on Beale Function', fontsize=13)
ax.set_xlabel('x')
ax.set_ylabel('y')
ax.legend(fontsize=8, loc='upper right')
ax.set_xlim(-4.5, 4.5)
ax.set_ylim(-4.5, 4.5)

# 오른쪽: 손실 수렴 곡선
ax = axes[1]
for opt, color in zip(optimizers, colors):
    # 옵티마이저 초기화 (새 인스턴스)
    opt2 = opt.__class__(**{k: v for k, v in opt.__dict__.items()
                             if k not in ['m', 'v', 'G', 'E', 't', 'name']
                             and not k.startswith('_')})
    path = run_optimizer(opt2, start)
    losses = [beale_function(p[0], p[1]) for p in path]
    ax.plot(losses, color=color, linewidth=2, label=opt.name)

ax.set_yscale('log')
ax.set_xlabel('Iteration', fontsize=12)
ax.set_ylabel('Loss (log scale)', fontsize=12)
ax.set_title('Convergence Comparison', fontsize=13)
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('optimizer_comparison.png', dpi=150, bbox_inches='tight')
plt.show()


# ============================================================
# 2. 학습률 스케줄링 시각화
# ============================================================

def cosine_annealing(t, T, lr_min=0.0001, lr_max=0.01):
    return lr_min + 0.5 * (lr_max - lr_min) * (1 + np.cos(np.pi * t / T))

def step_decay(t, lr_0=0.01, gamma=0.5, step=50):
    return lr_0 * (gamma ** (t // step))

def warmup_cosine(t, T_warmup=20, T_total=200, lr_max=0.01, lr_min=0.0001):
    if t < T_warmup:
        return lr_max * (t / T_warmup)
    return cosine_annealing(t - T_warmup, T_total - T_warmup, lr_min, lr_max)

T = 200
timesteps = np.arange(T)

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(timesteps, [step_decay(t) for t in timesteps],
        label='Step Decay (γ=0.5, step=50)', linewidth=2)
ax.plot(timesteps, [cosine_annealing(t, T) for t in timesteps],
        label='Cosine Annealing', linewidth=2)
ax.plot(timesteps, [warmup_cosine(t) for t in timesteps],
        label='Warmup + Cosine Decay', linewidth=2, linestyle='--')
ax.axvline(x=20, color='gray', linestyle=':', alpha=0.7, label='Warmup End (t=20)')

ax.set_xlabel('Iteration', fontsize=12)
ax.set_ylabel('Learning Rate', fontsize=12)
ax.set_title('Learning Rate Scheduling Strategies', fontsize=14)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('lr_scheduling.png', dpi=150, bbox_inches='tight')
plt.show()
```

![옵티마이저 경로 비교](figures/gradient_descent_paths.png)

*Figure 1: 옵티마이저 경로 비교: Beale 함수 등고선 위에서 GD, 모멘텀, RMSProp, Adam의 최적화 경로와 수렴 속도를 비교한다.*

![학습률 스케줄 비교](figures/learning_rate_comparison.png)

*Figure 2: 학습률 스케줄 비교: Step Decay, Cosine Annealing, Warmup+Cosine 세 가지 스케줄링 전략의 학습률 변화 양상을 보여준다.*

위 코드는 두 가지 시각화를 생성합니다:

1. **옵티마이저 경로 비교**: Beale 함수(비볼록 테스트 함수)의 등고선 위에 GD, 모멘텀, RMSProp, Adam의 최적화 경로와 수렴 속도를 함께 시각화합니다.
2. **학습률 스케줄 비교**: Step Decay, Cosine Annealing, Warmup+Cosine 세 가지 스케줄링 전략의 학습률 변화 양상을 보여줍니다.

---

## 정리

최적화 이론은 머신러닝의 학습 과정을 이해하는 핵심 기반입니다:

- **기본 GD**: 이론적 기초. 볼록 문제에 적합하지만 딥러닝에는 너무 단순
- **SGD + 모멘텀**: 딥러닝 황금 표준. 최종 성능이 높지만 학습률 튜닝 필요
- **Adam**: 범용적이고 강건한 선택. 빠른 수렴과 적은 튜닝 부담
- **학습률 스케줄링**: 고정 학습률의 한계를 뛰어넘는 필수 기법

실무에서는 Adam으로 시작하여 모델이 수렴하는 것을 확인한 후, 문제의 특성과 최종 성능 요구에 따라 옵티마이저와 스케줄링 전략을 세밀하게 조정하는 것이 좋습니다.