## 개요

Rectified Flow(Liu et al., ICLR 2023)는 노이즈 분포 $\pi_0$와 데이터 분포 $\pi_1$ 사이를 **직선 경로(straight-line path)**로 연결하는 ODE 기반 생성 모델이다. 기존 확산 모델이 수백 스텝의 수치 적분을 요구하는 것과 달리, Rectified Flow는 흐름 궤적을 직선에 가깝게 만드는 **Reflow** 절차를 도입하여 이론적으로 단일 스텝 생성을 가능하게 한다.

이 논문은 이미지 생성뿐 아니라 도메인 전환(image-to-image transfer)에도 동일한 프레임워크를 적용할 수 있음을 보이며, 이후 InstaFlow, Stable Diffusion 3(SD3) 등 영향력 있는 후속 연구들의 기반이 되었다.

다음 그림은 Rectified Flow의 핵심 결과를 요약한다. 1-Rectified Flow는 2 스텝만으로도 합리적인 이미지를 생성하며, 2-Rectified Flow(Reflow 1회 적용)는 단 1 스텝(Distilled)으로도 고품질 결과를 달성한다.

![1-Rectified Flow와 2-Rectified Flow의 스텝별 생성 결과](figures/fig_1.jpg)
*Figure 1: Rectified Flow의 이미지 생성(위 2행: 가우시안 노이즈 → 고양이 얼굴)과 이미지 전환(아래 2행: 사람 얼굴 → 고양이 얼굴). 1-Rectified Flow는 $N \geq 2$ 에서 양호한 결과를 보이며, 2-Rectified Flow는 직선화된 궤적 덕분에 $N=1$ 에서도 고품질 생성이 가능하다. (Liu et al., 2023)*

---

## 배경 및 문제

### 확산 모델의 비효율성

DDPM, Score SDE 등 기존 확산 모델은 데이터를 점진적으로 노이즈로 변환하고, 역방향 SDE/ODE를 수치적으로 풀어 샘플을 생성한다. 이 과정은 수백에서 수천 번의 함수 평가(NFE)를 필요로 한다. ODE solver를 활용한 DDIM 등이 스텝 수를 줄였지만, 궤적 자체가 비선형이기 때문에 적분 오차가 쌓이는 문제가 남는다.

### 핵심 질문

> 두 분포 $\pi_0$와 $\pi_1$ 사이를 **직선**으로 잇는 ODE 벡터 필드를 직접 학습할 수 있는가?

직선 궤적은 적분 오차가 가장 작고, 이론적으로 단 한 번의 Euler 스텝만으로도 정확한 샘플을 얻을 수 있다. 이것이 Rectified Flow의 핵심 동기다.

---

## 핵심 아이디어

### Rectified Flow ODE

시간 $t \in [0, 1]$에서 흐름 $Z_t$를 다음 ODE로 정의한다:

$$\frac{dZ_t}{dt} = v(Z_t, t)$$

여기서 $v: \mathbb{R}^d \times [0,1] \to \mathbb{R}^d$는 학습할 벡터 필드다. $Z_0 \sim \pi_0$(가우시안 노이즈), $Z_1 \sim \pi_1$(데이터 분포)이 되도록 $v$를 훈련한다.

### 학습 목표

독립 커플링 $X_0 \sim \pi_0,\ X_1 \sim \pi_1$에서 선형 보간으로 경로를 구성한다:

$$X_t = tX_1 + (1-t)X_0, \quad t \in [0, 1]$$

그러면 이상적인 속도 방향은 $X_1 - X_0$이고, 훈련 손실은:

$$\min_v \int_0^1 \mathbb{E}\left[\|(X_1 - X_0) - v(X_t, t)\|^2\right]dt$$

이 손실은 **각 시간 $t$에서 벡터 필드가 직선 방향을 예측하도록** 강제한다. 결정적으로, 이 목표는 단순한 회귀 문제로 표현되므로 학습이 안정적이다.

### Reflow: 점진적 직선화

독립 커플링으로 학습한 1-Rectified Flow의 궤적은 서로 교차하면서 곡선을 이룬다. 아래 그림은 이 문제를 2차원 toy 예제로 보여준다. 보라색 점($\pi_0$)과 빨간 점($\pi_1$) 사이의 독립 커플링 궤적이 중앙에서 심하게 교차하고 있다.

![독립 커플링의 교차 궤적](figures/fig_2_1.png)
*Figure 2(a): 독립 커플링 $(X_0, X_1) \sim \pi_0 \times \pi_1$의 선형 보간. 서로 다른 데이터 쌍의 경로가 중앙에서 교차하여 ODE 벡터 필드가 방향을 결정하기 어렵다.*

Reflow는 이 교차 문제를 반복적으로 해결한다:

1. 현재 Rectified Flow $v^{(k)}$로 ODE를 풀어 새로운 커플링 $(X_0, X_1^{(k)}) \sim \pi_{\mathrm{RF}}^{(k)}$를 생성한다.
2. 이 커플링으로 다음 세대 $v^{(k+1)}$을 훈련한다.

$$\pi_{\mathrm{RF}}^{(k)}: X_0 \sim \pi_0,\ X_1^{(k)} = \Phi_{v^{(k)}}(X_0)$$

반복할수록 커플링이 **최적 수송(OT)**에 가까워지고 궤적이 직선화된다. 아래 그림은 Reflow 후 궤적이 교차 없이 직선으로 변한 결과를 보여준다.

![Reflow 후 직선화된 궤적](figures/fig_2_4.png)
*Figure 2(d): Reflow로 재학습한 후의 Rectified Flow. 궤적이 교차 없이 직선을 따르며, Euler 1스텝으로도 정확한 전달이 가능하다.*

직선 궤적은 교차하지 않으므로, Euler 방법의 단 1스텝으로도 높은 품질의 샘플을 생성할 수 있다.

---

## 방법론

### 커플링 선택의 영향

| 커플링 | 설명 | 궤적 특성 |
|--------|------|----------|
| 독립 $\pi_0 \otimes \pi_1$ | 노이즈와 데이터를 무작위로 짝지음 | 초기에 곡선, Reflow로 개선 |
| OT 커플링 | Wasserstein 거리 최소화 쌍 | 이미 직선에 가까움 |

Rectified Flow와 VP ODE의 궤적 차이는 다음 2D 예제에서 명확히 드러난다. Rectified Flow는 Reflow 1회만으로 궤적이 거의 직선이 되는 반면, VP ODE는 Reflow 후에도 곡선 궤적이 유지된다.

![Rectified Flow 초기 궤적](figures/fig_4_1.png)
![Rectified Flow Reflow 후 직선화된 궤적](figures/fig_4_2.png)
*Figure 2: Rectified Flow의 Reflow 전(좌)과 후(우) 궤적 비교 — 가우시안 혼합 분포(빨간 점)를 타겟으로 할 때, 초기 교차 궤적이 Reflow 1회로 각 모드를 향한 직선 경로로 정리된다. VP ODE와 sub-VP ODE는 동일한 Reflow를 적용해도 곡선이 유지된다. (Liu et al., 2023)*

Flow Matching(Lipman et al., 2022)의 OT-CFM은 사실상 OT 커플링을 사용하는 Rectified Flow와 동치임을 논문은 지적한다. Rectified Flow의 차별점은 **독립 커플링에서 출발해도 Reflow로 OT에 수렴할 수 있다**는 절차적 보장이다.

Reflow를 반복할수록 궤적 직선성과 수송 비용이 어떻게 개선되는지 아래 그래프에서 정량적으로 확인할 수 있다.

![Reflow 반복에 따른 직선성 및 수송 비용 변화](figures/fig_3_4.png)
*Figure 3(d): Reflow 단계별 직선성(straightness, 파란색)과 상대 L2 수송 비용(transport cost, 초록색). 두 값 모두 0에 수렴할수록 직선 경로 및 최적 수송에 가까워지며, 초기 몇 회의 Reflow만으로도 급격히 개선된다.*

### 단일 스텝 증류

Reflow로 충분히 직선화된 후, 추가로 **증류(distillation)**를 적용하면 진정한 단일 스텝 생성 모델을 얻는다:

$$\mathcal{L}_{\mathrm{distill}} = \mathbb{E}\left[\|\hat{X}_1 - X_1\|^2\right]$$

여기서 $\hat{X}_1 = Z_0 + v_{\theta}(Z_0, 0)$은 단일 Euler 스텝 예측이고, $X_1$은 멀티스텝 ODE 해다. 이 접근법은 Consistency Models(Song et al., 2023)와 목표가 유사하지만, Rectified Flow의 직선 구조 덕분에 증류 대상의 품질이 더 높다.

Rectified Flow의 직선 궤적과 균일 속도 특성은 스텝 수에 따른 이산화 품질에 직접적으로 영향을 미친다. 아래 그림은 Rectified Flow가 단일 스텝으로도 분포의 평균을 정확히 생성하고 2 스텝이면 전체 분포를 커버하는 반면, VP ODE는 시간 후반부에 업데이트가 집중되어 적은 스텝에서 품질이 저하됨을 보여준다.

![스텝 수에 따른 Rectified Flow 궤적 시각화](figures/fig_5_1.png)
*Figure 3: Rectified Flow의 직선 궤적과 균일 시간 진행 — $\pi_0$(보라 점)에서 $\pi_1$(빨간 점)까지 직선으로 이동하며, $N=1$ 스텝으로도 분포의 평균에 도달한다. $N=2$ 이면 전체 분포를 충분히 커버한다. (Liu et al., 2023)*

### 이론적 성질

**교차 방지(Non-crossing)**: 직선 궤적은 시간-공간에서 교차하지 않는다. 교차가 없으면 모든 $t$에서 결정론적 매핑이 보장되어 ODE 적분 오차가 최소화된다.

**Monge Map 근사**: 충분한 Reflow 반복 후, Rectified Flow는 $\pi_0$에서 $\pi_1$으로의 OT 맵에 수렴함을 이론적으로 보인다.

---

## 실험 결과

### 이미지 생성 (CIFAR-10, CelebA-HQ)

| 모델 | NFE | FID ↓ |
|------|-----|-------|
| DDPM | 1000 | 3.17 |
| DDIM | 10 | 4.67 |
| 1-Rectified Flow | 1 | 378.9 |
| 2-Rectified Flow | 1 | 12.21 |
| 2-Rectified Flow + Distill | 1 | **4.85** |

Reflow 1회만으로도 단일 스텝 FID가 크게 개선되며, 증류를 결합하면 DDIM 10스텝과 유사한 품질을 **단 1 NFE**로 달성한다.

직선화의 효과는 이미지 공간에서도 직관적으로 확인할 수 있다. 아래 그림에서 1-Rectified Flow는 곡선 궤적 때문에 적은 스텝에서 예측이 부정확하지만, 2-Rectified Flow는 궤적이 거의 직선이어서 매우 이른 시점($t = 0.025$)부터 최종 이미지를 정확히 예측한다.

![1-Rectified Flow와 2-Rectified Flow의 궤적 비교](figures/fig_10.jpg)
*Figure 10: sub-VP ODE(곡선 궤적)와 Rectified Flow(직선 궤적)의 비교. 왼쪽 다이어그램은 곡선 경로에서 중간 시점의 예측 $\hat{z}_1^t$가 최종 결과 $z_1$과 크게 다른 반면, 직선 경로에서는 임의의 시점에서도 정확한 예측이 가능함을 보여준다. 2-Rectified Flow는 $t = 0.01$부터 이미 선명한 이미지를 예측한다.*

### 이미지 전환 (Image-to-Image Transfer)

Rectified Flow는 생성 모델로만 쓰이지 않는다. $\pi_0$를 소스 도메인, $\pi_1$을 타겟 도메인으로 설정하면 도메인 전환 모델로도 작동한다. 논문은 낮/밤 변환, 스타일 전환 등에서 CycleGAN 대비 경쟁력 있는 결과를 보인다.

### SD3에서의 활용

Stable Diffusion 3(Esser et al., 2024)는 Rectified Flow를 핵심 플로우 공식으로 채택하고, transformer 아키텍처(DiT)와 결합하여 텍스트-이미지 생성에서 SOTA를 달성했다.

---

## 의의 및 한계

### 의의

- **단순성**: 복잡한 노이즈 스케줄이나 score 함수 추정 없이, 직선 보간 경로 + MSE 회귀만으로 구현 가능하다.
- **확장성**: 독립 커플링 → Reflow → 증류라는 명확한 3단계 파이프라인은 대규모 모델(SD3, InstaFlow)에도 그대로 적용된다.
- **이론적 완결성**: OT 수렴 보장, 비교차 성질 등 수학적 근거가 탄탄하다.

### 한계

- **Reflow 비용**: 커플링 데이터를 생성하기 위해 기존 모델로 전체 데이터셋을 다시 샘플링해야 하므로, 반복 비용이 상당하다.
- **독립 커플링의 초기 품질**: 첫 번째 Rectified Flow는 곡선 궤적이 많아 단독으로는 품질이 낮다. 반드시 Reflow나 증류가 필요하다.
- **OT 수렴 속도**: 이론적으로 OT에 수렴하지만, 실제로는 Reflow 반복 횟수와 모델 용량에 크게 의존한다.

---

## 코드 예제

```python
import torch
import torch.nn as nn
from torch.optim import Adam

# 1. 벡터 필드 네트워크 (단순 MLP 예시)
class VectorField(nn.Module):
    def __init__(self, dim=2, hidden=256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim + 1, hidden), nn.SiLU(),
            nn.Linear(hidden, hidden),  nn.SiLU(),
            nn.Linear(hidden, dim)
        )

    def forward(self, x, t):
        # x: (B, dim), t: (B,) or scalar
        if t.dim() == 0:
            t = t.expand(x.shape[0])
        xt = torch.cat([x, t.unsqueeze(-1)], dim=-1)
        return self.net(xt)


# 2. Rectified Flow 학습
def train_rectified_flow(model, pi0_samples, pi1_samples, epochs=1000, lr=1e-3):
    """독립 커플링으로 1-Rectified Flow 학습"""
    optimizer = Adam(model.parameters(), lr=lr)

    for epoch in range(epochs):
        # 독립 커플링: 무작위로 짝을 지음
        x0 = pi0_samples[torch.randperm(len(pi0_samples))]
        x1 = pi1_samples[torch.randperm(len(pi1_samples))]
        B = x0.shape[0]

        # 균일 시간 샘플링
        t = torch.rand(B, device=x0.device)

        # 선형 보간으로 중간 경로 생성
        xt = t.unsqueeze(-1) * x1 + (1 - t).unsqueeze(-1) * x0

        # 목표 방향: x1 - x0 (직선)
        target = x1 - x0

        # MSE 손실
        pred = model(xt, t)
        loss = ((pred - target) ** 2).mean()

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    return model


# 3. ODE 샘플링 (Euler 방법)
@torch.no_grad()
def sample_euler(model, z0, steps=10):
    """z0: (B, dim) 가우시안 노이즈 → 데이터 샘플"""
    z = z0.clone()
    dt = 1.0 / steps

    for i in range(steps):
        t = torch.full((z.shape[0],), i * dt, device=z.device)
        v = model(z, t)
        z = z + v * dt

    return z


# 4. Reflow: 새 커플링 생성 후 재학습
def reflow(model, pi0_samples, steps=100):
    """현재 모델로 ODE를 풀어 새 (x0, x1) 커플링 생성"""
    x0 = pi0_samples
    x1_new = sample_euler(model, x0, steps=steps)  # 멀티스텝으로 고품질 커플링 생성
    return x0, x1_new


# 5. 전체 파이프라인
dim = 2
model = VectorField(dim=dim)

# Step 1: 독립 커플링으로 1-Rectified Flow 학습
pi0 = torch.randn(10000, dim)  # 가우시안 노이즈
pi1 = ...                       # 실제 데이터 분포 샘플
model = train_rectified_flow(model, pi0, pi1)

# Step 2: Reflow - 커플링 재생성 후 재학습
for _ in range(2):  # Reflow 2회 반복
    x0_new, x1_new = reflow(model, pi0, steps=100)
    model = train_rectified_flow(model, x0_new, x1_new)

# Step 3: 단일 스텝 샘플링 (증류 후 또는 충분한 Reflow 후)
z0 = torch.randn(16, dim)
samples = sample_euler(model, z0, steps=1)  # 1-step generation
```

---

## 관련 문서

- [Flow Matching for Generative Modeling](../flow-matching/) - Lipman et al., ICLR 2023: OT-CFM은 OT 커플링을 사용하는 Rectified Flow와 동치
- [InstaFlow: One Step is Enough for High-Quality Diffusion-Based Text-to-Image Generation](../instaflow/) - Rectified Flow + Reflow를 Stable Diffusion에 적용한 1-step 이미지 생성
- [Stable Diffusion 3](../stable-diffusion-3/) - Rectified Flow + DiT 아키텍처의 대규모 텍스트-이미지 모델
- [Consistency Models](../consistency-models/) - Song et al., 2023: 다른 방식으로 단일 스텝 생성을 달성하는 접근법
- [DDIM](../ddim/) - Song et al., ICLR 2021: 결정론적 샘플링으로 확산 모델 속도를 높인 선행 연구