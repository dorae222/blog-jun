# EDM (Elucidating Diffusion Models): 확산 모델 설계 공간 분석

## 개요

"Elucidating the Design Space of Diffusion-Based Generative Models"(EDM)는 2022년 NVIDIA의 Tero Karras 등이 발표한 연구로, 기존 확산 모델들의 설계 선택을 체계적으로 분해하고 각 구성 요소의 영향을 독립적으로 분석한 포괄적 연구이다. CIFAR-10에서 FID 1.97로 당시 무조건부 이미지 생성 SOTA를 갱신하였다.

- **논문**: [Elucidating the Design Space of Diffusion-Based Generative Models](https://arxiv.org/abs/2206.00364)
- **코드**: [NVlabs/edm](https://github.com/NVlabs/edm)
- **발표**: 2022년 6월, NVIDIA
- **라이선스**: CC BY-NC-SA 4.0

## 아키텍처 상세

![EDM Preconditioning 프레임워크 아키텍처](figures/architecture.png)

*Figure 1: EDM의 Preconditioning 프레임워크와 설계 공간 분석 구조. (Karras et al., 2022)*

### Preconditioning 프레임워크

EDM의 핵심 기여는 네트워크 입출력을 노이즈 수준 $\sigma$에 따라 스케일링하는 네 가지 함수를 이론적으로 유도한 것이다:

$$D_\theta(\mathbf{x}; \sigma) = c_{\text{skip}}(\sigma) \cdot \mathbf{x} + c_{\text{out}}(\sigma) \cdot F_\theta(c_{\text{in}}(\sigma) \cdot \mathbf{x}; c_{\text{noise}}(\sigma))$$

| 함수 | 역할 | 수식 |
|------|------|------|
| $c_{\text{skip}}(\sigma)$ | 스킵 연결 가중치 | $\sigma_{\text{data}}^2 / (\sigma^2 + \sigma_{\text{data}}^2)$ |
| $c_{\text{out}}(\sigma)$ | 출력 스케일링 | $\sigma \cdot \sigma_{\text{data}} / \sqrt{\sigma^2 + \sigma_{\text{data}}^2}$ |
| $c_{\text{in}}(\sigma)$ | 입력 스케일링 | $1 / \sqrt{\sigma^2 + \sigma_{\text{data}}^2}$ |
| $c_{\text{noise}}(\sigma)$ | 노이즈 조건화 | $\ln(\sigma) / 4$ |

이 설계의 핵심 원리:
- $c_{\text{in}}$은 네트워크 입력의 분산을 항상 1로 정규화
- $c_{\text{out}}$은 네트워크 출력의 크기를 정규화
- $c_{\text{skip}}$은 적절한 스킵 연결로 학습 목표를 단순화
- 결과적으로 $F_\theta$의 학습 목표가 모든 $\sigma$에서 균일한 크기를 가짐

### 노이즈 수준 분포

학습 시 노이즈 수준 $\sigma$의 샘플링 분포를 로그-노멀로 정의한다:

$$\ln \sigma \sim \mathcal{N}(P_{\text{mean}}, P_{\text{std}}^2)$$

기본값: $P_{\text{mean}} = -1.2$, $P_{\text{std}} = 1.2$

### 학습 손실

가중 MSE 손실:

$$\mathcal{L} = \mathbb{E}_{\sigma, \mathbf{x}, \mathbf{n}} \left[\lambda(\sigma) \cdot \|D_\theta(\mathbf{x} + \sigma \mathbf{n}; \sigma) - \mathbf{x}\|^2\right]$$

가중치 $\lambda(\sigma) = 1 / c_{\text{out}}(\sigma)^2$로 설정하여 모든 $\sigma$에서 손실 기여도를 균일화한다.

### 고급 샘플러: Heun + Stochastic

EDM은 두 가지 핵심 샘플러를 제안한다:

**1. 2차 Heun 적분기 (결정론적):**

$$\mathbf{x}_{i+1}^{\text{Euler}} = \mathbf{x}_i + (t_{i+1} - t_i) \cdot D_\theta'(\mathbf{x}_i; t_i)$$
$$\mathbf{x}_{i+1}^{\text{Heun}} = \mathbf{x}_i + \frac{t_{i+1} - t_i}{2} \cdot (D_\theta'(\mathbf{x}_i; t_i) + D_\theta'(\mathbf{x}_{i+1}^{\text{Euler}}; t_{i+1}))$$

Heun 방법은 Euler 대비 수치 오차를 줄여 같은 NFE에서 더 높은 품질을 달성한다.

**2. Stochastic Sampler (확률론적):**

각 스텝에서 Langevin 노이즈를 추가하여 다양성을 높이고, 작은 오차를 보정한다.

### 직교적 설계 분리

EDM 논문의 방법론적 기여는 각 설계 요소를 직교적으로 분리하여 독립적으로 최적화한 것이다:

| 설계 요소 | 독립 분석 | 최적 선택 |
|----------|---------|---------|
| 네트워크 입출력 | Preconditioning | $c_{\text{skip}}, c_{\text{out}}, c_{\text{in}}, c_{\text{noise}}$ |
| 노이즈 분포 | 학습 효율 | 로그-노멀 |
| ODE 적분기 | 샘플 품질 | 2차 Heun |
| 확률성 | 다양성/품질 | Stochastic Langevin |
| 시간 이산화 | 효율 | 기하급수적 스케줄 |

## 핵심 혁신

1. **Preconditioning 프레임워크**: 기존 확산 모델들의 ad hoc 설계를 이론적으로 정당화하고 최적화한 범용적 프레임워크이다.
2. **로그-노멀 노이즈 분포**: 학습 시 노이즈 수준의 샘플링을 최적화하여 학습 효율을 크게 향상시켰다.
3. **Heun 샘플러**: 2차 적분기를 도입하여 동일 NFE에서 1차 방법(Euler) 대비 품질을 크게 향상시켰다.
4. **체계적 설계 공간 분석**: 확산 모델의 각 구성 요소를 독립적으로 분석하는 방법론을 제시하였다.

## 벤치마크/성능

| 데이터셋 | FID (↓) | NFE | 비교 |
|---------|---------|-----|------|
| CIFAR-10 | **1.97** | 35 | DDPM: 3.17 (1000 NFE) |
| FFHQ 64×64 | **2.39** | 79 | StyleGAN2: 2.84 |
| AFHQv2 64×64 | **1.96** | 79 | - |
| ImageNet 64×64 | **2.44** | 79 | ADM: 2.07 (250 NFE) |

## 관련 모델 비교

| 특성 | EDM | DDPM | Score-SDE | DDIM |
|------|-----|------|-----------|------|
| 핵심 기여 | 설계 최적화 | 기본 프레임워크 | 연속 SDE | 빠른 샘플링 |
| Preconditioning | 이론적 유도 | 경험적 | N/A | N/A |
| 샘플러 | Heun 2차 | DDPM | Predictor-Corrector | DDIM ODE |
| CIFAR-10 FID | 1.97 | 3.17 | 2.20 | 4.67 (50) |
| NFE | 18-35 | 1000 | ~1000 | 10-100 |

## 학습 상세

- **데이터셋**: CIFAR-10, FFHQ 64, AFHQv2 64, ImageNet 64
- **아키텍처**: U-Net (~55M CIFAR / ~280M ImageNet)
- **$\sigma_{\text{data}}$**: 데이터 표준편차 (CIFAR-10: 0.5)
- **하드웨어**: 8× A100 GPU
- **연산량**: ~100M 이미지 학습 (CIFAR-10)

## 실무 활용

### 1. Consistency Model의 교사 모델

EDM의 Preconditioning과 Heun 샘플러는 Consistency Model의 교사 ODE 솔버로 직접 활용된다.

### 2. 고품질 무조건부 생성

FID 2 이하의 무조건부 이미지 생성이 필요한 연구에서 EDM은 표준 베이스라인이다.

### 3. 확산 모델 설계 가이드

새로운 확산 모델을 설계할 때 EDM의 Preconditioning, 노이즈 분포, 샘플러 선택 등을 참고하는 것이 사실상 표준이 되었다.

## 한계 및 전망

### 한계

1. **해상도 한계**: 원논문은 64×64까지만 실험하였다.
2. **조건부 생성 미검증**: 텍스트 등 복잡한 조건부 생성에는 직접 적용되지 않았다.

### 후속 발전

- **EDM2 (2024)**: 고해상도(512×512)와 더 큰 모델 규모로 확장
- **Consistency Model**: EDM을 교사 모델로 활용한 단일 스텝 생성
- **SD3**: EDM 스타일 Preconditioning을 MMDiT에 적용

EDM은 확산 모델의 설계를 이론적으로 정립하고 최적화한 기준점 연구로, 이후 모든 확산 모델 연구의 기본 참조가 되었다.

### 기술적 의의

EDM의 Preconditioning 프레임워크는 확산 모델의 학습을 "네트워크가 균일한 크기의 목표를 예측하도록 정규화하는 문제"로 재정의함으로써, 기존 DDPM의 $\epsilon$-예측이나 $\mathbf{x}_0$-예측이 왜 동작하는지에 대한 통일적 해석을 제공하였다. 이 프레임워크는 이후 Consistency Model, EDM2, Score Distillation Sampling(SDS) 등 다양한 후속 연구의 수학적 기반이 되었으며, 특히 Karras 샘플링 스케줄은 Stable Diffusion WebUI(Automatic1111)에서 가장 널리 사용되는 샘플러 설정 중 하나가 되었다. 확산 모델 엔지니어링에서 "EDM Preconditioning을 적용했는가"는 사실상 표준적인 체크리스트 항목이 되었다.

## 관련 문서

- [[ddpm|DDPM (Denoising Diffusion Probabilistic Models)]] — 발전 기반
