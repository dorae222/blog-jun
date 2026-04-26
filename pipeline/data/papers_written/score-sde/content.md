<!-- infographic-hero -->
![Score-Based Generative Modeling through Stochastic Differential Equations 핵심 요약](figures/infographic.svg)

*Figure: Score-Based Generative Modeling through Stochastic Differential Equations 한 장 요약 인포그래픽*

## 개요

"Score-Based Generative Modeling through Stochastic Differential Equations"(Song et al., ICLR 2021)은 스코어 기반 생성 모델(SMLD/NCSN)과 확산 확률 모델(DDPM)을 **연속 확률미분방정식(SDE)** 이라는 단일 프레임워크로 통합한 연구입니다. 논문은 기존의 이산적(discrete) 노이즈 추가 과정을 연속 시간(continuous-time)으로 일반화하여, 두 계열의 방법론이 각각 VE-SDE(Variance Exploding SDE)와 VP-SDE(Variance Preserving SDE)의 특수 사례임을 보입니다.

이 통합 시각은 단순한 이론적 우아함에 그치지 않습니다. 연속 SDE 프레임워크는 **Probability Flow ODE**를 통한 결정론적 샘플링, 정확한 로그 우도 계산, 유일한 잠재 공간 표현이라는 새로운 능력을 생성 모델에 부여합니다. CIFAR-10에서 FID 2.20을 달성하며 당시 최고 수준을 기록했고, 이후 DDIM, EDM, Consistency Model 등 수많은 후속 연구의 이론적 토대가 되었습니다.

## 배경 및 문제

### 스코어 기반 생성 모델의 두 계보

2021년 이전까지 노이즈를 활용한 생성 모델은 두 갈래로 발전하고 있었습니다.

**SMLD / NCSN (Song & Ermon, 2019, 2020)**: 서로 다른 수준($\sigma_1 < \sigma_2 < \cdots < \sigma_N$)의 가우시안 노이즈를 데이터에 추가한 뒤, 각 노이즈 수준에서의 스코어 함수 $\nabla_{\mathbf{x}} \log p_{\sigma_i}(\mathbf{x})$를 학습합니다. 생성 시에는 Annealed Langevin Dynamics로 노이즈 수준을 점차 줄이며 샘플을 정제합니다.

**DDPM (Ho et al., 2020)**: 마르코프 체인으로 $T$번의 작은 가우시안 노이즈를 순차적으로 추가하고, 역방향 마르코프 체인을 신경망으로 학습합니다. ELBO 최적화를 통해 단순한 노이즈 예측 목표를 도출했습니다.

두 방법은 표면적으로 달라 보이지만 본질적으로 같은 아이디어를 다른 방식으로 구현하고 있었습니다. Song et al.은 이 두 방법론 모두 연속 시간 SDE의 이산화(discretization)임을 밝혔습니다.

### 이산화의 한계

기존 이산 접근의 문제점은 명확합니다. 노이즈 수준의 수 $N$ 또는 타임스텝 $T$가 생성 품질과 속도 사이의 트레이드오프를 결정하며, 이론적으로 최적의 연속 궤적을 이산 과정으로 근사하는 데서 오는 오차가 불가피합니다. 연속 SDE 프레임워크는 이 제약을 원리적으로 제거합니다.

## 핵심 아이디어

### 순방향 SDE: 데이터를 노이즈로

데이터 분포 $p_0(\mathbf{x})$에서 출발하여 시간 $t \in [0, T]$에 따라 점차 단순한 사전 분포(prior) $p_T(\mathbf{x})$로 변환하는 과정을 Itô SDE로 기술합니다:

$$d\mathbf{x} = f(\mathbf{x}, t)dt + g(t)d\mathbf{w}$$

여기서 $f(\cdot, t): \mathbb{R}^d \to \mathbb{R}^d$는 드리프트(drift) 계수, $g(t) \in \mathbb{R}$은 확산(diffusion) 계수, $\mathbf{w}$는 표준 위너 과정(Wiener process)입니다. 충분히 큰 $T$와 적절한 $f, g$ 선택 시 $p_T$는 $\mathcal{N}(0, \mathbf{I})$에 수렴합니다.

아래 그림은 이 프레임워크의 핵심 직관을 보여줍니다. 데이터에서 노이즈로의 순방향 SDE를 시간 역순으로 풀면, 스코어 함수만으로 노이즈에서 데이터를 복원할 수 있습니다.

![역방향 SDE를 통한 스코어 기반 생성 모델](figures/fig_1.png)
*순방향 SDE가 데이터를 노이즈 분포로 변환하고, 각 시간 $t$에서의 스코어 $\nabla_{\mathbf{x}} \log p_t(\mathbf{x})$를 알면 역방향 SDE를 풀어 데이터를 생성할 수 있다.*

### 역방향 SDE: 노이즈에서 데이터로

Anderson(1982)의 결과에 따르면, 위 순방향 SDE에 대응하는 역방향 SDE가 존재합니다:

$$d\mathbf{x} = \left[f(\mathbf{x}, t) - g(t)^2 \nabla_{\mathbf{x}} \log p_t(\mathbf{x})\right]dt + g(t)d\bar{\mathbf{w}}$$

$\bar{\mathbf{w}}$는 시간이 역방향으로 흐르는 위너 과정이며, $dt$는 음의 무한소 시간 스텝입니다. 핵심은 역방향 SDE가 **스코어 함수** $\nabla_{\mathbf{x}} \log p_t(\mathbf{x})$에만 의존한다는 점입니다. 스코어 함수를 신경망 $s_\theta(\mathbf{x}, t)$로 근사하면, $p_T$에서 시작하여 역방향 SDE를 시뮬레이션함으로써 데이터를 생성할 수 있습니다.

다음 그림은 순방향/역방향 SDE와 Probability Flow ODE의 샘플 궤적을 시각화한 것입니다. 왼쪽은 확률적(stochastic) SDE 궤적, 오른쪽은 결정론적(deterministic) ODE 궤적으로, 두 경로 모두 동일한 주변 분포 $p_t(\mathbf{x})$를 공유합니다.

![SDE 궤적과 Probability Flow ODE 궤적 비교](figures/p04_fig01.png)
*SDE(색상 곡선)와 Probability Flow ODE(검은 곡선)의 샘플 궤적. 배경 색상은 확률 밀도를 나타내며, 두 과정이 동일한 주변 분포를 공유하면서도 경로의 확률성이 다름을 보여준다.*

## 방법론

다음 그림은 VE-SDE와 VP-SDE의 전이 커널(perturbation kernel)이 시간에 따라 어떻게 변하는지 시각적으로 비교한 것입니다. VE-SDE는 분산이 폭발적으로 증가하는 반면, VP-SDE는 분산을 일정하게 유지하며 평균이 0으로 수축합니다.

![VE-SDE와 VP-SDE의 전이 커널 비교](figures/fig_2.png)
*Figure 1: VE-SDE(좌)와 VP-SDE(우)의 전이 커널 시각화 ( VE-SDE는 평균이 보존되고 분산이 증가하며, VP-SDE는 평균이 0으로 수축하면서 분산이 1로 유지된다. 이산 모델(SMLD, DDPM)과 연속 SDE가 정확히 일치함을 확인할 수 있다. (Song et al., 2021)*

### VE-SDE: SMLD의 연속 시간 극한

노이즈 스케줄 $\sigma(t)$가 단조 증가할 때, SMLD의 연속 시간 버전은 **VE-SDE**(Variance Exploding SDE)입니다:

$$d\mathbf{x} = \sqrt{\frac{d[\sigma^2(t)]}{dt}}\, d\mathbf{w}$$

드리프트 항이 없으므로 평균은 보존되고 분산만 증가합니다. 전이 확률은:

$$p_{0t}(\mathbf{x}(t) \mid \mathbf{x}(0)) = \mathcal{N}\!\left(\mathbf{x}(t);\ \mathbf{x}(0),\ [\sigma^2(t) - \sigma^2(0)]\mathbf{I}\right)$$

분산이 무한히 커질 수 있기 때문에 "분산 폭발"이라 부릅니다. 논문에서는 $\sigma(t) = \sigma_{\min}\left(\sigma_{\max}/\sigma_{\min}\right)^t$의 기하 스케줄을 사용합니다($\sigma_{\min}=0.01$, $\sigma_{\max}=1348$).

아래 그림은 VE-SDE의 전이 커널(perturbation kernel) 분산이 시간에 따라 어떻게 변하는지를 보여줍니다. 이산 SMLD의 노이즈 스케줄과 연속 VE-SDE가 거의 완벽하게 일치하며, $t \to 1$에서 분산이 폭발적으로 증가하는 특성이 명확히 드러납니다.

![VE-SDE 전이 커널의 분산 변화](figures/fig_6.png)
*VE-SDE와 이산 SMLD의 전이 커널 분산 비교. 연속 시간 SDE(파란 실선)가 이산 SMLD(빨간 점선)의 정확한 극한임을 확인할 수 있다. 시간이 1에 가까워질수록 분산이 급격히 증가한다.*

### VP-SDE: DDPM의 연속 시간 극한

DDPM의 연속 시간 버전은 **VP-SDE**(Variance Preserving SDE)입니다:

$$d\mathbf{x} = -\frac{1}{2}\beta(t)\mathbf{x}\, dt + \sqrt{\beta(t)}\, d\mathbf{w}$$

$\beta(t)$는 연속 노이즈 스케줄로, DDPM의 $\{\beta_i\}_{i=1}^{N}$을 연속화한 것입니다. 이 SDE는 분산을 1로 유지하려는 경향이 있어 "분산 보존"이라 부릅니다. 전이 확률의 평균과 분산은:

$$p_{0t}(\mathbf{x}(t) \mid \mathbf{x}(0)) = \mathcal{N}\!\left(\mathbf{x}(t);\ e^{-\frac{1}{2}\int_0^t \beta(s)ds}\mathbf{x}(0),\ \left(1 - e^{-\int_0^t \beta(s)ds}\right)\mathbf{I}\right)$$

또한 sub-VP-SDE라는 변종도 제안하는데, VP-SDE보다 더 작은 분산을 가지며 로그 우도 면에서 더 유리합니다.

### 스코어 네트워크 학습

시간에 따라 변하는 스코어 함수 $s_\theta(\mathbf{x}, t) \approx \nabla_{\mathbf{x}} \log p_t(\mathbf{x})$를 학습하기 위한 통합 목표는 **가중치 조합 손실**입니다:

$$\min_\theta\ \mathbb{E}_t \!\left[\lambda(t)\, \mathbb{E}_{\mathbf{x}(0)}\, \mathbb{E}_{\mathbf{x}(t) \mid \mathbf{x}(0)} \!\left[\left\|s_\theta(\mathbf{x}(t), t) - \nabla_{\mathbf{x}(t)} \log p_{0t}(\mathbf{x}(t) \mid \mathbf{x}(0))\right\|_2^2\right]\right]$$

타임스텝 $t \sim \mathcal{U}[0, T]$로 연속 샘플링하고, 전이 커널 $p_{0t}(\mathbf{x}(t)|\mathbf{x}(0))$이 해석적으로 알려져 있으므로 조건부 스코어 $\nabla_{\mathbf{x}(t)} \log p_{0t}(\mathbf{x}(t)|\mathbf{x}(0))$도 닫힌 형태로 계산됩니다. 예를 들어 VE-SDE의 경우:

$$\nabla_{\mathbf{x}(t)} \log p_{0t}(\mathbf{x}(t) \mid \mathbf{x}(0)) = -\frac{\mathbf{x}(t) - \mathbf{x}(0)}{\sigma^2(t) - \sigma^2(0)}$$

가중치 $\lambda(t)$로는 Fisher Divergence의 균형을 맞추기 위해 $\lambda(t) = g(t)^2$이 이론적으로 권장됩니다.

### Probability Flow ODE: 결정론적 샘플링

모든 SDE에 대해 동일한 주변 확률 분포 $p_t(\mathbf{x})$를 공유하는 **ODE**가 존재합니다:

$$d\mathbf{x} = \left[f(\mathbf{x}, t) - \frac{1}{2}g(t)^2 \nabla_{\mathbf{x}} \log p_t(\mathbf{x})\right]dt$$

이 Probability Flow ODE는 확률성 없이 결정론적으로 샘플링하며, 기존 ODE 솔버(RK45 등)를 활용할 수 있습니다. 더 중요하게는, 이 ODE가 **데이터와 잠재 코드 사이의 가역 변환**을 정의하므로 정확한 로그 우도 계산이 가능해집니다(Instantaneous Change of Variables, Chen et al. 2018). 또한 특정 데이터의 잠재 표현을 구하거나 보간(interpolation)하는 것도 가능합니다.

아래 그림은 Probability Flow ODE의 세 가지 핵심 장점을 보여줍니다. 적응적 스텝 사이즈 ODE 솔버를 통한 효율적 샘플링, NFE(Neural Function Evaluations) 감소에 따른 품질 변화, 그리고 잠재 공간에서의 매끄러운 보간이 가능합니다.

![Probability Flow ODE의 장점: 적응적 샘플링, NFE 비교, 잠재 공간 보간](figures/fig_3.png)
*Probability Flow ODE의 핵심 능력. 왼쪽: 수치 정밀도에 따른 적응적 스텝 사이즈 솔버의 평가 시점. 가운데: NFE를 14/86/548로 변화시킨 생성 결과 비교. 오른쪽: 잠재 공간에서의 구형 보간(spherical interpolation)으로 자연스러운 이미지 전환.*

### 수치 SDE 솔버와 Predictor-Corrector 샘플러

논문은 역방향 SDE를 더 효율적으로 시뮬레이션하기 위한 **Predictor-Corrector(PC) 샘플러**를 제안합니다. Predictor 단계에서는 수치 SDE 솔버(Euler-Maruyama, reverse diffusion)로 $\mathbf{x}_t \to \mathbf{x}_{t-\Delta t}$를 예측하고, Corrector 단계에서는 Langevin MCMC로 현재 추정치를 현재 시각 $t$의 분포로 교정합니다. 이 두 단계를 번갈아 수행하면 이산화 오차가 축적되는 것을 방지할 수 있습니다.

## 실험 결과

### CIFAR-10 이미지 생성 품질

| 모델 | FID ↓ | IS ↑ |
|------|-------|------|
| DDPM (Ho et al., 2020) | 3.17 | 9.46 |
| NCSN++ (Song & Ermon, 2020) | 10.87 | 8.40 |
| **VE-SDE (PC 샘플러)** | **2.20** | **9.89** |
| VP-SDE (PC 샘플러) | 2.55 | 9.58 |
| sub-VP-SDE (PC 샘플러) | 2.61 | 9.56 |
| VE-SDE (Probability Flow ODE) | 3.21 | - |

PC 샘플러를 사용한 VE-SDE가 FID 2.20으로 당시 최고 수준을 달성했습니다. Probability Flow ODE 기반의 결정론적 샘플러도 FID 3.21로 경쟁력 있는 성능을 보였습니다.

아래는 클래스 조건부 CIFAR-10 샘플(자동차, 말)로, Score SDE 프레임워크가 무조건부 생성을 넘어 조건부 생성에서도 우수한 품질을 달성함을 보여줍니다.

![Score SDE 클래스 조건부 CIFAR-10 생성 샘플](figures/fig_4_1.png)
*Figure 2: Score SDE의 클래스 조건부 CIFAR-10 32x32 샘플 ) 상단 4행은 자동차, 하단 4행은 말 클래스. Classifier Guidance를 SDE 프레임워크 안에서 자연스럽게 적용하여 클래스별 고품질 이미지를 생성한다. (Song et al., 2021)*

Score SDE는 인페인팅과 컬러화 같은 역문제(inverse problem)에도 직접 적용할 수 있습니다. 순방향 SDE의 구조를 활용해 조건부 생성을 별도 학습 없이 수행합니다.

![Score SDE를 활용한 인페인팅 및 컬러화 결과](figures/fig_4_2.jpg)
*Figure 3: LSUN 256x256에서의 인페인팅(상단 2행)과 컬러화(하단 2행) ( 첫 번째 열이 원본, 두 번째 열이 마스크/흑백 입력이며, 나머지 열은 조건부 생성 결과. 동일 입력에서 다양한 그럴듯한 완성 결과를 생성한다. (Song et al., 2021)*

### 로그 우도 및 잠재 공간 분석

Probability Flow ODE를 이용한 정확한 로그 우도 계산 결과:

| 모델 | NLL (bpd) ↓ |
|------|-------------|
| DDPM | 3.70 |
| Flow++ | 3.29 |
| **sub-VP-SDE (Probability Flow ODE)** | **2.99** |

sub-VP-SDE가 Flow 기반 모델에 준하는 로그 우도를 달성했으며, 동시에 고품질 샘플을 생성합니다. 이는 생성 품질과 우도 추정이 상충(trade-off)된다는 기존 통념을 깨는 결과입니다.

Probability Flow ODE의 잠재 공간은 의미론적으로 풍부한 구조를 가지고 있습니다. 아래 그림은 CelebA-HQ 256x256에서 구형 보간(spherical interpolation)과 온도 조절(temperature rescaling)을 수행한 결과입니다.

![Probability Flow ODE 잠재 공간 보간 및 온도 조절](figures/fig_9_1.png)
*Figure 4: VP-SDE Probability Flow ODE의 CelebA-HQ 256x256 잠재 공간 활용 ) 상단: 두 샘플 간 구형 보간으로 자연스러운 속성 전환(포즈, 표정, 배경). 하단: 잠재 코드의 norm을 줄이면(temperature 감소) 더 선명하지만 평균에 가까운 이미지가 생성된다. (Song et al., 2021)*

특히 주목할 만한 결과는 Probability Flow ODE가 정의하는 잠재 공간의 **유일성(uniqueness)**입니다. 서로 다른 아키텍처로 독립 학습한 두 모델(Model A, Model B)이 동일한 이미지에 대해 거의 동일한 잠재 코드를 산출합니다. 아래 그림에서 각 차원별 상관계수의 히스토그램은 대부분 $r \approx 1$에 집중되어 있으며, 특정 차원 $x_1(T)$에 대해 $r = 0.96$이라는 높은 상관을 보여줍니다. 이는 Probability Flow ODE의 잠재 공간이 모델 아키텍처에 독립적인 고유한 데이터 표현을 학습함을 의미합니다.

![독립 학습된 두 모델 간 잠재 코드의 차원별 상관계수](figures/fig_11_2.png)
*독립적으로 학습된 두 모델(Model A, B)의 잠재 코드 간 차원별 상관계수 분포. 대부분의 차원에서 $r \approx 1$에 가까우며, 이는 Probability Flow ODE의 잠재 공간이 모델에 독립적인 유일한 표현을 제공함을 시사한다.*

## 의의 및 한계

### 의의

- **통합적 이해**: SMLD와 DDPM이라는 독립적으로 발전하던 두 방법론이 하나의 수학적 프레임워크의 특수 사례임을 밝혀, 이 분야에 대한 심층적인 이해를 제공합니다.
- **새로운 설계 공간**: VE/VP/sub-VP SDE를 넘어 임의의 드리프트와 확산 계수를 가진 SDE를 탐색할 수 있는 원리적 방법을 제시합니다. 이는 이후 EDM(Karras et al., 2022)에서 최적 SDE를 탐색하는 연구로 이어졌습니다.
- **Probability Flow ODE**: 결정론적 샘플링, 정확한 우도 계산, 잠재 공간 인코딩이라는 세 가지 능력을 동시에 부여합니다. DDIM이 경험적으로 발견한 비마르코프 샘플링을 이론적으로 설명하는 프레임워크이기도 합니다.
- **조건부 생성 통합**: 클래스 조건부 생성을 위한 Classifier Guidance를 SDE 프레임워크 안에서 자연스럽게 유도할 수 있습니다.
- **광범위한 영향**: DDIM, EDM, Consistency Model, Flow Matching, Stable Diffusion 3 등 현대 생성 모델의 이론적 뼈대를 형성합니다.

### 한계

- **느린 샘플링**: PC 샘플러는 여전히 수천 번의 함수 평가를 필요로 합니다. 이 문제는 DDIM(50 스텝), Consistency Model(1~2 스텝) 등으로 이후 해결되었습니다.
- **Probability Flow ODE의 수치 불안정성**: 정확한 로그 우도 계산은 비교적 비용이 높고, 역방향 ODE 적분의 수치 오차가 누적될 수 있습니다.
- **아키텍처 의존성**: U-Net 기반 스코어 네트워크 설계가 여전히 경험적 선택에 크게 의존합니다.
- **픽셀 공간 동작**: 고해상도 이미지에서 메모리와 계산 부담이 급격히 증가합니다. 이후 LDM이 잠재 공간으로 이동함으로써 이를 해결했습니다.

## 코드 예제

### Score SDE 핵심 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class VESDE:
    """Variance Exploding SDE (SMLD의 연속 시간 극한).

    순방향 SDE: dx = sqrt(d[σ²(t)]/dt) dw
    전이 확률: p_{0t}(x(t)|x(0)) = N(x(0), [σ²(t)-σ²(0)]I)
    """

    def __init__(self, sigma_min=0.01, sigma_max=1348.0, N=1000):
        self.sigma_min = sigma_min
        self.sigma_max = sigma_max
        self.N = N  # 이산화 스텝 수 (샘플링용)

    def sigma(self, t):
        """σ(t) = σ_min * (σ_max/σ_min)^t (기하 스케줄)"""
        return self.sigma_min * (self.sigma_max / self.sigma_min) ** t

    def marginal_prob(self, x0, t):
        """주변 전이 확률의 평균과 표준편차 반환."""
        sigma_t = self.sigma(t)
        sigma_0 = self.sigma(torch.zeros_like(t))
        std = torch.sqrt(sigma_t ** 2 - sigma_0 ** 2)
        mean = x0
        return mean, std

    def prior_sampling(self, shape):
        """사전 분포 p_T ~ N(0, σ_max² I)에서 샘플링."""
        return torch.randn(*shape) * self.sigma_max

    def score_from_noise_pred(self, noise_pred, t):
        """VE-SDE에서 스코어 = -ε / σ(t) (NCSN++ 컨벤션)."""
        sigma_t = self.sigma(t).view(-1, *([1] * (noise_pred.ndim - 1)))
        return -noise_pred / sigma_t


class VPSDE:
    """Variance Preserving SDE (DDPM의 연속 시간 극한).

    순방향 SDE: dx = -½β(t)x dt + sqrt(β(t)) dw
    """

    def __init__(self, beta_min=0.1, beta_max=20.0, N=1000):
        self.beta_min = beta_min
        self.beta_max = beta_max
        self.N = N

    def beta(self, t):
        """β(t) = β_min + t(β_max - β_min) (선형 스케줄)"""
        return self.beta_min + t * (self.beta_max - self.beta_min)

    def log_mean_coeff(self, t):
        """log E[x(t)|x(0)]의 계수: -½ ∫₀ᵗ β(s)ds"""
        return -0.25 * t ** 2 * (self.beta_max - self.beta_min) - 0.5 * t * self.beta_min

    def marginal_prob(self, x0, t):
        """주변 전이 확률의 평균과 표준편차 반환."""
        log_coeff = self.log_mean_coeff(t)
        mean_coeff = torch.exp(log_coeff).view(-1, *([1] * (x0.ndim - 1)))
        std = torch.sqrt(1.0 - torch.exp(2.0 * log_coeff))
        std = std.view(-1, *([1] * (x0.ndim - 1)))
        return mean_coeff * x0, std

    def prior_sampling(self, shape):
        """사전 분포 p_T ~ N(0, I)에서 샘플링."""
        return torch.randn(*shape)


def score_matching_loss(sde, score_net, x0, eps=1e-5):
    """연속 스코어 매칭 손실 계산.

    목표:
      min_θ E_t [λ(t) E_{x(0)} E_{x(t)|x(0)} [||s_θ(x(t),t) - ∇ log p_{0t}||²]]
    """
    # t ~ Uniform(eps, 1)
    t = torch.rand(x0.shape[0], device=x0.device) * (1.0 - eps) + eps

    # 전이 확률에서 x(t) 샘플링
    mean, std = sde.marginal_prob(x0, t)
    noise = torch.randn_like(x0)
    xt = mean + std * noise

    # 조건부 스코어 (ground truth): ∇ log p_{0t}(x(t)|x(0)) = -noise / std
    target_score = -noise / std

    # 스코어 네트워크 예측
    t_input = t.view(-1, *([1] * (x0.ndim - 1)))
    predicted_score = score_net(xt, t)

    # 가중치 λ(t) = std²(t) (Fisher Divergence 균형)
    weight = std ** 2
    loss = torch.mean(weight * torch.sum((predicted_score - target_score) ** 2,
                                          dim=tuple(range(1, x0.ndim))))
    return loss


@torch.no_grad()
 def euler_maruyama_sampler(sde, score_net, shape, num_steps=1000, device='cuda'):
    """역방향 SDE를 Euler-Maruyama 방법으로 시뮬레이션.

    역방향 SDE: dx = [f(x,t) - g²∇ log p_t(x)]dt + g dw̄
    """
    # 사전 분포에서 시작
    x = sde.prior_sampling(shape).to(device)

    # 이산 타임스텝 (T → 0)
    timesteps = torch.linspace(1.0, 1e-3, num_steps, device=device)
    dt = timesteps[0] - timesteps[1]  # 양수 dt (시간 역방향)

    for t_val in timesteps:
        t_batch = torch.full((shape[0],), t_val, device=device)

        # 스코어 예측
        score = score_net(x, t_batch)

        # VE-SDE 역방향: dx = σ²(t) * score * dt + σ(t) * dw̄
        if isinstance(sde, VESDE):
            sigma_t = sde.sigma(t_batch).view(-1, 1, 1, 1)
            drift = sigma_t ** 2 * score
            diffusion = sigma_t
        # VP-SDE 역방향: dx = [-½β(t)x - β(t)*score] * dt + sqrt(β(t)) * dw̄
        elif isinstance(sde, VPSDE):
            beta_t = sde.beta(t_batch).view(-1, 1, 1, 1)
            drift = -0.5 * beta_t * x - beta_t * score
            diffusion = torch.sqrt(beta_t)

        # Euler-Maruyama 업데이트
        noise = torch.randn_like(x)
        x = x + drift * dt + diffusion * torch.sqrt(dt) * noise

    return x


# 사용 예시
if __name__ == '__main__':
    # SDE 초기화
    ve_sde = VESDE(sigma_min=0.01, sigma_max=1348.0)
    vp_sde = VPSDE(beta_min=0.1, beta_max=20.0)

    # 스코어 네트워크 (실제로는 NCSNv2 또는 DDPM U-Net 사용)
    class DummyScoreNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv2d(3, 64, 3, padding=1), nn.SiLU(),
                nn.Conv2d(64, 3, 3, padding=1)
            )
        def forward(self, x, t):
            return self.net(x)

    score_net = DummyScoreNet().cuda()
    optimizer = torch.optim.Adam(score_net.parameters(), lr=2e-4)

    # 학습 스텝 (VP-SDE)
    x0 = torch.randn(8, 3, 32, 32).cuda()
    loss = score_matching_loss(vp_sde, score_net, x0)
    loss.backward()
    optimizer.step()
    print(f'Score matching loss: {loss.item():.4f}')

    # 샘플 생성
    samples = euler_maruyama_sampler(ve_sde, score_net, (4, 3, 32, 32))
    print(f'Generated samples shape: {samples.shape}')  # (4, 3, 32, 32)
```

## 관련 문서

- [[score-matching|Score Matching]] ( 스코어 기반 생성 모델의 이론적 배경
- [[ddpm|DDPM]] ) VP-SDE의 이산 시간 특수 사례
- [[ddim|DDIM]] ( Probability Flow ODE의 경험적 발견 (Score SDE로 이론화됨)
- [[edm|EDM: Elucidating the Design Space]] ) Score SDE 프레임워크에서 최적 SDE 탐색
- [[consistency-model|Consistency Models]] ( Score SDE 궤적에서의 단일 스텝 생성
- [[flow-matching|Flow Matching]] ) ODE 기반 생성의 후속 발전
- [[cfg|Classifier-Free Guidance]] ( 조건부 생성을 위한 Score SDE 확장
- [[ldm|Latent Diffusion Models]] ) Score SDE를 잠재 공간으로 확장한 Stable Diffusion의 기반
