# Score SDE: 확률 미분 방정식을 통한 확산 모델 통합 프레임워크

## 개요

Score-based Generative Modeling through Stochastic Differential Equations는 2021년 Stanford University의 Yang Song, Jascha Sohl-Dickstein, Diederik P. Kingma 등이 발표한 연구로, 확산 기반 생성 모델을 연속적인 **확률 미분 방정식(SDE)** 프레임워크로 통합한 획기적인 이론적 업적이다.

기존의 SMLD(Score Matching with Langevin Dynamics)와 DDPM이 서로 다른 접근처럼 보였으나, 이 논문은 두 방법이 모두 특정 SDE의 이산화(discretization)임을 증명하여 확산 모델의 통일된 수학적 기반을 제시하였다.

## 아키텍처 상세

### Forward SDE

Forward SDE는 데이터를 점진적으로 노이즈로 변환한다:

$$d\mathbf{x} = \mathbf{f}(\mathbf{x},t)dt + g(t)d\mathbf{w}$$

여기서 $\mathbf{f}$는 drift 계수, $g$는 diffusion 계수, $\mathbf{w}$는 위너 과정이다.

### Reverse-time SDE

Anderson의 역방향 SDE 정리에 의해:

$$d\mathbf{x} = \left[\mathbf{f}(\mathbf{x},t) - g(t)^2\nabla_\mathbf{x}\log p_t(\mathbf{x})\right]dt + g(t)d\bar{\mathbf{w}}$$

신경망 $s_\theta(\mathbf{x},t) \approx \nabla_\mathbf{x}\log p_t(\mathbf{x})$를 학습하면 임의의 $t$에서 score를 근사할 수 있다.

### Probability Flow ODE

SDE를 결정론적 ODE로 변환할 수 있다:

$$d\mathbf{x} = \left[\mathbf{f}(\mathbf{x},t) - \frac{1}{2}g(t)^2\nabla_\mathbf{x}\log p_t(\mathbf{x})\right]dt$$

이 ODE는 역전 가능하여 정확한 로그 가능도 계산이 가능하다.

### SDE 변형

| SDE 유형 | 설명 | DDPM과의 관계 |
|----------|------|-------------|
| VP-SDE | 분산 보존(Variance Preserving) | DDPM의 연속 버전 |
| VE-SDE | 분산 폭발(Variance Exploding) | SMLD의 연속 버전 |
| sub-VP-SDE | VP-SDE의 변형 | 더 나은 가능도 |

### Predictor-Corrector 샘플러

PC 샘플러는 수치 SDE 솔버(predictor)와 Langevin MCMC(corrector)를 조합한다:

1. **Predictor**: Euler-Maruyama 또는 reverse diffusion으로 한 스텝 전진
2. **Corrector**: Langevin dynamics로 현재 스텝의 샘플 품질 개선

## 핵심 혁신

1. **통일된 프레임워크**: DDPM과 Score Matching이 동일 SDE의 이산화임을 증명
2. **연속 시간 확장**: 이산 타임스텝에서 연속 시간으로 자연스러운 확장
3. **Probability Flow ODE**: 결정론적 샘플링과 정확한 가능도 계산 동시 달성
4. **PC 샘플러**: Predictor와 Corrector의 조합으로 유연한 샘플링 전략 설계

## 벤치마크/성능

| 모델 | 데이터셋 | FID (↓) | IS (↑) | NLL (↓) |
|------|---------|---------|--------|--------|
| Score SDE (VE) | CIFAR-10 | 2.20 | 9.89 | - |
| Score SDE (VP) | CIFAR-10 | 2.41 | 9.68 | 2.99 BPD |
| DDPM | CIFAR-10 | 3.17 | 9.46 | 3.75 BPD |
| Score SDE | CelebA-HQ 1024 | ~7.0 | - | - |

CIFAR-10에서 FID 2.20, IS 9.89를 달성하여 당시 SOTA를 기록하였다.

## 관련 모델 비교

| 특성 | Score SDE | DDPM | DDIM | Flow Matching |
|------|-----------|------|------|---------------|
| 시간 정의 | 연속 | 이산 | 이산 | 연속 |
| 확률/결정론적 | 둘 다 가능 | 확률적 | 결정론적 | 결정론적 |
| 가능도 계산 | 가능(PF ODE) | 근사적 | 불가 | 가능 |
| 이론적 통일 | DDPM+SMLD 통합 | 독립 | DDPM 가속 | SDE의 발전 |

## 실무 활용

### PyTorch 구현 예시

```python
import torch
import torch.nn as nn

class ScoreSDE:
    def __init__(self, score_model, sde_type='vp'):
        self.score_model = score_model
        self.sde_type = sde_type
    
    def drift_and_diffusion(self, x, t):
        """SDE 계수 계산"""
        if self.sde_type == 'vp':
            beta_t = 0.1 + (20.0 - 0.1) * t  # 선형 스케줄
            drift = -0.5 * beta_t * x
            diffusion = torch.sqrt(beta_t)
        elif self.sde_type == 've':
            sigma_t = 0.01 * (50.0 / 0.01) ** t
            drift = torch.zeros_like(x)
            diffusion = sigma_t * torch.sqrt(2 * torch.log(torch.tensor(50.0/0.01)))
        return drift, diffusion
    
    def reverse_sde_step(self, x, t, dt, score):
        """역방향 SDE 한 스텝"""
        f, g = self.drift_and_diffusion(x, t)
        reverse_drift = f - g**2 * score
        noise = torch.randn_like(x)
        x_prev = x - reverse_drift * dt + g * torch.sqrt(dt) * noise
        return x_prev
    
    def probability_flow_ode_step(self, x, t, dt, score):
        """Probability Flow ODE 한 스텝"""
        f, g = self.drift_and_diffusion(x, t)
        ode_drift = f - 0.5 * g**2 * score
        x_prev = x - ode_drift * dt
        return x_prev
    
    @torch.no_grad()
    def pc_sample(self, shape, N=1000, corrector_steps=1):
        """Predictor-Corrector 샘플링"""
        dt = 1.0 / N
        x = torch.randn(shape)
        for i in range(N):
            t = 1.0 - i * dt
            t_tensor = torch.full((shape[0],), t)
            # Predictor step
            score = self.score_model(x, t_tensor)
            x = self.reverse_sde_step(x, t, dt, score)
            # Corrector steps (Langevin)
            for _ in range(corrector_steps):
                score = self.score_model(x, t_tensor - dt)
                noise = torch.randn_like(x)
                step_size = 0.01
                x = x + step_size * score + torch.sqrt(2*step_size) * noise
        return x
```

### 주요 활용 분야

- **이론적 기반**: 현대 확산 모델(EDM, Flow Matching, Consistency Model)의 수학적 토대
- **확률적 + 결정론적 샘플링**: PC 샘플러로 유연한 생성 전략
- **가능도 계산**: Probability Flow ODE를 통한 정확한 밀도 추정
- **역문제 해결**: 이미지 복원, 의료 영상 재구성 등

## 한계 및 전망

### 한계

1. **샘플링 비용**: PC 샘플러는 수천 NFE가 필요할 수 있음
2. **수치적 불안정성**: SDE 시뮬레이션에서 수치 오차 누적
3. **복잡한 수학**: 실무 적용 시 이론적 이해 장벽이 높음

### 후속 발전

- **EDM (2022)**: Preconditioning을 통한 체계적 설계 최적화
- **Flow Matching (2022)**: ODE 기반으로 SDE 복잡성 제거
- **Consistency Model (2023)**: ODE 궤적의 일관성을 활용한 단일 스텝 생성
- **Rectified Flow (2022)**: 직선 궤적으로 더 효율적인 전송

Score SDE는 확산 모델의 수학적 기반을 확립한 기념비적 연구로, 그 프레임워크는 2025년 현재까지도 새로운 생성 모델 개발의 출발점이 되고 있다.

## 관련 문서

- [[score-matching|Score-based Generative Model (NCSN)]] — 발전 기반
- [[consistency-model|Consistency Model]] — 후속 모델
- [[ddpm|DDPM (Denoising Diffusion Probabilistic Models)]] — 영감
- [[flow-matching|Flow Matching]] — 영감을 줌
