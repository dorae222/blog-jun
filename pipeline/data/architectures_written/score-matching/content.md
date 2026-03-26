# Score 기반 생성 모델: NCSN과 Langevin Dynamics

## 개요

Score matching과 Langevin dynamics를 결합한 생성 모델은 2019년 Stanford University의 Yang Song과 Stefano Ermon이 "Generative Modeling by Estimating Gradients of the Data Distribution"에서 제안한 패러다임이다. 이 연구의 핵심 아이디어는 데이터 분포 $p(\mathbf{x})$ 자체를 모델링하는 대신, 그 그래디언트인 **score function** $\nabla_{\mathbf{x}} \log p(\mathbf{x})$을 신경망으로 학습하는 것이다.

Score function만 알면 **Langevin dynamics**를 통해 데이터 분포에서 샘플링할 수 있다는 통찰이 핵심이다. 다양한 수준의 가우시안 노이즈에 대한 score를 동시에 학습하는 **Noise Conditional Score Network(NCSN)**을 제안하여, annealed Langevin dynamics로 고품질 샘플을 생성한다.

다음 그림은 Score 기반 생성 모델(NCSN)의 전체 아키텍처를 보여준다.

![NCSN 아키텍처 다이어그램](figures/architecture.png)
*Figure 1: NCSN 전체 구조 — 다중 노이즈 수준의 Forward 과정, RefineNet 기반 Score Network, Denoising Score Matching 학습 목표, Annealed Langevin Dynamics 샘플링 알고리즘. (Source: Song & Ermon, 2019)*

## 아키텍처 상세

### Score Function 정의

Score function은 데이터 분포의 로그 밀도의 그래디언트로 정의된다:

$$\mathbf{s}(\mathbf{x}) = \nabla_{\mathbf{x}} \log p(\mathbf{x})$$

이 벡터 필드는 데이터 밀도가 높은 방향을 가리키며, 정규화 상수를 알 필요가 없다는 장점이 있다.

### Score Matching 학습 목표

직접적인 score matching은 비용이 크므로, **Denoising Score Matching(DSM)**을 사용한다:

$$\mathcal{L}_{DSM} = \frac{1}{2}\mathbb{E}_{\mathbf{x}, \tilde{\mathbf{x}}} \left[\|\mathbf{s}_\theta(\tilde{\mathbf{x}}) - \nabla_{\tilde{\mathbf{x}}} \log q_\sigma(\tilde{\mathbf{x}}|\mathbf{x})\|^2\right]$$

가우시안 노이즈의 경우 이 target score는 닫힌 형태로 계산된다:

$$\nabla_{\tilde{\mathbf{x}}} \log q_\sigma(\tilde{\mathbf{x}}|\mathbf{x}) = -\frac{\tilde{\mathbf{x}} - \mathbf{x}}{\sigma^2}$$

### Noise Conditional Score Network (NCSN)

NCSN은 다양한 노이즈 수준 $\{\sigma_i\}_{i=1}^L$에서 동시에 score를 학습하는 신경망이다. 아키텍처는 U-Net 기반의 RefineNet을 사용하며, 노이즈 수준 $\sigma_i$를 추가 조건으로 입력받는다.

노이즈 수준은 기하급수적으로 감소하도록 설정한다:

$$\sigma_1 > \sigma_2 > \cdots > \sigma_L$$

학습 목표는 모든 노이즈 수준에 대한 가중 합이다:

$$\mathcal{L} = \frac{1}{L}\sum_{i=1}^{L} \lambda(\sigma_i) \mathbb{E}\left[\|\mathbf{s}_\theta(\tilde{\mathbf{x}}, \sigma_i) + \frac{\tilde{\mathbf{x}} - \mathbf{x}}{\sigma_i^2}\|^2\right]$$

### Annealed Langevin Dynamics

샘플링은 높은 노이즈 수준에서 시작하여 점진적으로 낮은 노이즈 수준으로 전환하는 annealed Langevin dynamics로 수행된다:

$$\mathbf{x}_{k+1} = \mathbf{x}_k + \frac{\alpha_i}{2} \mathbf{s}_\theta(\mathbf{x}_k, \sigma_i) + \sqrt{\alpha_i}\mathbf{z}_k, \quad \mathbf{z}_k \sim \mathcal{N}(0, \mathbf{I})$$

각 노이즈 수준에서 $T$ 스텝의 Langevin dynamics를 수행한 후 다음 수준으로 전환한다.

다음 그림은 데이터 분포의 score function과 학습된 score network의 비교로, score matching의 핵심 아이디어를 시각적으로 보여준다.

![데이터 score function과 학습된 score network 비교](figures/fig_3.png)
*Figure 1: Score function 시각화 — 가우시안 혼합 분포의 실제 데이터 score. 화살표가 데이터 밀도가 높은 방향을 가리키며, 주황색이 진할수록 밀도가 높다. 고밀도 영역에서는 score 추정이 정확하지만 저밀도 영역에서는 부정확해지는 문제를 노이즈 추가로 해결한다. (Source: Song & Ermon, 2019)*

아래는 Langevin dynamics와 annealed Langevin dynamics의 샘플링 품질 차이를 보여준다.

![Langevin dynamics vs Annealed Langevin dynamics 비교](figures/fig_5.png)
*Figure 2: 가우시안 혼합에서의 샘플링 비교 — (a) 정확한 샘플링, (b) 일반 Langevin dynamics, (c) Annealed Langevin dynamics. 일반 Langevin dynamics는 모드 간 비율을 잘못 추정하지만, annealed 방식은 정확한 비율을 복원한다. (Source: Song & Ermon, 2019)*

다음은 annealed Langevin dynamics의 중간 샘플링 과정으로, 노이즈에서 점진적으로 이미지가 생성되는 과정을 보여준다.

![Annealed Langevin dynamics의 중간 샘플링 과정](figures/fig_7.png)
*Figure 3: Annealed Langevin dynamics 중간 샘플 — CelebA(상)와 CIFAR-10(하)에서 높은 노이즈에서 시작하여 점차 깨끗한 이미지로 수렴하는 과정. 초기 노이즈 수준에서 전역 구조가 형성되고, 후기 단계에서 세부 디테일이 추가된다. (Source: Song & Ermon, 2019)*

## 핵심 혁신

1. **Score function 학습**: 분포 자체가 아닌 그래디언트를 학습하여 정규화 상수 문제를 회피
2. **다중 노이즈 수준**: 저밀도 영역에서의 score 추정 문제를 노이즈 추가로 해결
3. **Annealed Langevin dynamics**: 높은 노이즈에서 시작하여 점진적으로 정밀화
4. **Denoising Score Matching**: 효율적이고 안정적인 학습 목표 제공

## 벤치마크/성능

| 모델 | 데이터셋 | IS (↑) | FID (↓) | 비고 |
|------|---------|--------|---------|------|
| NCSN | CIFAR-10 | 8.87 | 25.32 | L=10 노이즈 수준 |
| NCSNv2 | CIFAR-10 | 8.40 | 10.87 | Improved 버전 |
| NCSN++ (VE) | CIFAR-10 | 9.89 | 2.20 | Score SDE 내 |
| DDPM | CIFAR-10 | 9.46 | 3.17 | 비교 기준 |

NCSN++는 CIFAR-10에서 당시 SOTA인 FID 2.20을 달성하여 DDPM을 능가했다.

## 관련 모델 비교

| 특성 | Score Matching | DDPM | VAE | GAN |
|------|---------------|------|-----|-----|
| 학습 대상 | Score function | 노이즈 | 재구성 + KL | 적대적 |
| 샘플링 방법 | Langevin dynamics | 역확산 | 디코더 | 생성기 |
| 이론 기반 | Score matching | 변분 추론 | 변분 추론 | 게임 이론 |
| 가능도 계산 | 간접적 | 근사적 | 가능 | 불가 |
| 학습 안정성 | 높음 | 높음 | 높음 | 낮음 |

## 실무 활용

### PyTorch 구현 예시

```python
import torch
import torch.nn as nn

class ScoreNetwork(nn.Module):
    def __init__(self, base_model, num_noise_levels=10):
        super().__init__()
        self.base_model = base_model  # U-Net 등
        self.sigma_embed = nn.Embedding(num_noise_levels, 128)
    
    def forward(self, x, sigma_idx):
        """노이즈 수준에 조건화된 score 예측"""
        sigma_emb = self.sigma_embed(sigma_idx)
        return self.base_model(x, sigma_emb)

def dsm_loss(score_net, x, sigmas):
    """Denoising Score Matching 손실"""
    # 랜덤 노이즈 수준 선택
    idx = torch.randint(0, len(sigmas), (x.shape[0],))
    sigma = sigmas[idx].view(-1, 1, 1, 1)
    
    # 노이즈 추가
    noise = torch.randn_like(x)
    x_noisy = x + sigma * noise
    
    # Score 예측 및 손실 계산
    score_pred = score_net(x_noisy, idx)
    target = -noise / sigma  # = -(x_noisy - x) / sigma^2
    loss = (sigma ** 2 * (score_pred - target) ** 2).mean()
    return loss

@torch.no_grad()
def annealed_langevin(score_net, sigmas, shape, steps_per_level=100, eps=2e-5):
    """Annealed Langevin Dynamics 샘플링"""
    x = torch.randn(shape)
    for i, sigma in enumerate(sigmas):
        alpha = eps * (sigma / sigmas[-1]) ** 2
        for _ in range(steps_per_level):
            score = score_net(x, torch.full((shape[0],), i, dtype=torch.long))
            x = x + alpha / 2 * score + torch.sqrt(alpha) * torch.randn_like(x)
    return x
```

### 주요 활용 분야

- **이론적 기반**: Score SDE, Flow Matching 등 후속 프레임워크의 핵심 이론
- **이미지 생성**: NCSN, NCSNv2, NCSN++ 등 실용적 생성 모델
- **역문제 해결**: Score function을 활용한 이미지 복원, 초해상도, 인페인팅
- **과학적 시뮬레이션**: 분자 동역학, 단백질 구조 예측 등

## 한계 및 전망

### 한계

1. **느린 샘플링**: 각 노이즈 수준에서 수백 스텝의 Langevin dynamics가 필요
2. **노이즈 수준 설계**: $\sigma_i$ 시퀀스의 선택이 성능에 큰 영향
3. **이산적 노이즈 수준**: 유한 개의 노이즈 수준이 연속적 과정을 완벽히 근사하지 못함

### 후속 발전

- **Score SDE (2021)**: 연속 시간 SDE 프레임워크로 DDPM과 통합
- **DDPM (2020)**: Score matching의 이산 버전으로 해석 가능
- **Flow Matching (2022)**: Score에서 벡터 필드로의 관점 전환
- **EDM (2022)**: Preconditioning을 통한 체계적 설계 공간 분석

Score matching 패러다임은 확산 모델의 이론적 기반을 제공하며, 현재까지도 새로운 생성 모델 개발에서 핵심적인 역할을 하고 있다.

## 관련 문서

- [[score-sde|Score-based SDE (Stochastic Differential Equations)]] — 후속 모델
- [[diffusion-thermo|Diffusion (Thermodynamics) - Deep Unsupervised Learning using Nonequilibrium Thermodynamics]] — 영감
