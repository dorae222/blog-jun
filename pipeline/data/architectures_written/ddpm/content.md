# DDPM: 디노이징 확산 확률 모델 (Denoising Diffusion Probabilistic Models)

## 개요

DDPM(Denoising Diffusion Probabilistic Models)은 2020년 UC Berkeley의 Jonathan Ho, Ajay Jain, Pieter Abbeel이 발표한 확산 모델의 핵심 기반 논문이다. 이 연구는 데이터에 점진적으로 가우시안 노이즈를 추가하는 **순전파 과정(Forward Process)**과 이를 역으로 복원하는 **역전파 과정(Reverse Process)**을 정의하고, UNet이 각 타임스텝에서 노이즈를 예측하도록 학습한다. GAN보다 안정적인 학습과 다양성 높은 샘플 생성이 가능해 이미지 생성 연구의 패러다임을 전환시켰다.

DDPM 이전에는 GAN(Generative Adversarial Networks)이 이미지 생성의 주류 방법이었으나, 학습 불안정성과 mode collapse 문제가 있었다. DDPM은 이러한 한계를 극복하며 확산 기반 생성 모델의 시대를 열었고, 이후 Stable Diffusion, DALL-E 2, Imagen 등 현대 이미지 생성 모델의 이론적 토대가 되었다.

## 아키텍처 상세

### 순전파 과정 (Forward Process)

순전파 과정은 $T$ 타임스텝(보통 $T=1000$)에 걸쳐 데이터 $\mathbf{x}_0$에 가우시안 노이즈를 추가해 순수 노이즈 $\mathbf{x}_T$로 변환한다:

$$q(\mathbf{x}_t | \mathbf{x}_{t-1}) = \mathcal{N}(\mathbf{x}_t; \sqrt{1-\beta_t}\mathbf{x}_{t-1}, \beta_t\mathbf{I})$$

이 과정은 닫힌 형태(closed-form)로 표현 가능하여, 임의 타임스텝 $t$의 $\mathbf{x}_t$를 직접 샘플링할 수 있다:

$$q(\mathbf{x}_t | \mathbf{x}_0) = \mathcal{N}(\mathbf{x}_t; \sqrt{\bar{\alpha}_t}\mathbf{x}_0, (1-\bar{\alpha}_t)\mathbf{I})$$

여기서 $\bar{\alpha}_t = \prod_{s=1}^{t}(1-\beta_s)$이다.

### 역전파 과정 (Reverse Process)

역전파 과정에서는 UNet 기반의 노이즈 예측 모델 $\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)$가 각 스텝의 노이즈를 예측한다:

$$p_\theta(\mathbf{x}_{t-1}|\mathbf{x}_t) = \mathcal{N}(\mathbf{x}_{t-1}; \boldsymbol{\mu}_\theta(\mathbf{x}_t, t), \sigma_t^2\mathbf{I})$$

### UNet 백본

UNet은 타임스텝 임베딩(sinusoidal)을 조건으로 받고, 중간 해상도 특징맵에 Self-Attention을 적용해 장거리 의존성을 모델링한다. 주요 구성 요소:

- **인코더-디코더 구조**: 다운샘플링/업샘플링 경로 + Skip Connection
- **ResBlock**: GroupNorm + SiLU 활성화 + 타임스텝 조건 주입
- **Self-Attention**: 중간 해상도(16x16)에서 적용
- **타임스텝 임베딩**: Sinusoidal positional encoding

### 손실 함수

학습 손실은 실제 노이즈와 예측 노이즈 사이의 MSE로 단순화된다:

$$\mathcal{L}_{\text{simple}} = \mathbb{E}_{t, \mathbf{x}_0, \boldsymbol{\epsilon}}\left[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)\|^2\right]$$

## 핵심 혁신

1. **단순한 학습 목표**: 복잡한 ELBO를 단순 MSE 손실로 재구성하여 학습 효율성을 극대화
2. **닫힌 형태 샘플링**: 임의 타임스텝에서 직접 noisy sample을 생성 가능
3. **안정적인 학습**: GAN과 달리 adversarial training이 불필요하여 학습이 매우 안정적
4. **다양성**: Mode collapse 없이 데이터 분포의 전체 모드를 커버하는 다양한 샘플 생성

## 벤치마크/성능

| 모델 | 데이터셋 | FID (↓) | IS (↑) | 비고 |
|------|---------|---------|--------|------|
| DDPM | CIFAR-10 | 3.17 | 9.46 | 무조건부 생성 |
| BigGAN | CIFAR-10 | 14.73 | 9.22 | 조건부 생성 |
| StyleGAN2 | CIFAR-10 | 2.92 | 9.83 | - |
| Improved DDPM | CIFAR-10 | 2.94 | - | Nichol et al. 2021 |
| DDPM | LSUN Bedroom | 4.89 | - | 256x256 |

DDPM은 CIFAR-10에서 Inception Score 기준 GAN을 처음으로 능가하였으며, FID 3.17이라는 경쟁력 있는 수치를 달성했다.

## 관련 모델 비교

| 특성 | DDPM | GAN | VAE | Score Matching |
|------|------|-----|-----|----------------|
| 학습 안정성 | 매우 높음 | 낮음 | 높음 | 높음 |
| 샘플 다양성 | 높음 | 낮음(mode collapse) | 중간 | 높음 |
| 샘플 품질 | 높음 | 높음 | 중간 | 높음 |
| 생성 속도 | 느림(1000 스텝) | 빠름(1 스텝) | 빠름(1 스텝) | 느림 |
| 가능도 계산 | 근사적 | 불가 | 가능 | 불가 |

## 실무 활용

### PyTorch 구현 예시

```python
import torch
import torch.nn as nn

class SimpleDDPM:
    def __init__(self, T=1000, beta_start=1e-4, beta_end=0.02):
        self.T = T
        self.betas = torch.linspace(beta_start, beta_end, T)
        self.alphas = 1.0 - self.betas
        self.alpha_bars = torch.cumprod(self.alphas, dim=0)
    
    def forward_diffusion(self, x0, t, noise=None):
        """순전파: x0에서 xt를 직접 샘플링"""
        if noise is None:
            noise = torch.randn_like(x0)
        alpha_bar_t = self.alpha_bars[t].view(-1, 1, 1, 1)
        xt = torch.sqrt(alpha_bar_t) * x0 + torch.sqrt(1 - alpha_bar_t) * noise
        return xt, noise
    
    def training_loss(self, model, x0):
        """단순화된 학습 손실"""
        t = torch.randint(0, self.T, (x0.shape[0],))
        xt, noise = self.forward_diffusion(x0, t)
        predicted_noise = model(xt, t)
        return nn.functional.mse_loss(predicted_noise, noise)
    
    @torch.no_grad()
    def sample(self, model, shape):
        """역전파 샘플링"""
        x = torch.randn(shape)
        for t in reversed(range(self.T)):
            t_batch = torch.full((shape[0],), t, dtype=torch.long)
            predicted_noise = model(x, t_batch)
            alpha_t = self.alphas[t]
            alpha_bar_t = self.alpha_bars[t]
            x = (1 / torch.sqrt(alpha_t)) * (
                x - (self.betas[t] / torch.sqrt(1 - alpha_bar_t)) * predicted_noise
            )
            if t > 0:
                x += torch.sqrt(self.betas[t]) * torch.randn_like(x)
        return x
```

### 주요 활용 분야

- **이미지 생성**: 무조건부/조건부 이미지 합성
- **이미지 인페인팅**: 마스크된 영역 복원
- **Super-Resolution**: 저해상도 이미지 고해상도화
- **후속 모델 기반**: Stable Diffusion, DALL-E 2, Imagen 등의 핵심 프로세스

## 한계 및 전망

### 한계

1. **느린 샘플링 속도**: $T=1000$ 스텝의 순차적 디노이징이 필요하여 실시간 생성이 어려움
2. **고정된 노이즈 스케줄**: 선형 스케줄이 모든 데이터셋에 최적이 아닐 수 있음
3. **픽셀 공간 연산**: 고해상도 이미지 처리 시 메모리 및 연산 비용 급증
4. **조건부 생성 한계**: 원본 DDPM은 무조건부 생성만 지원

### 후속 발전

- **DDIM (2020)**: 결정론적 샘플링으로 10-50 스텝만에 비슷한 품질 달성
- **Improved DDPM (2021)**: 학습 가능한 분산, 코사인 스케줄 도입
- **LDM (2022)**: 잠재 공간에서의 확산으로 연산 비용 대폭 절감
- **Consistency Model (2023)**: 단일 스텝 생성 가능
- **Flow Matching (2022)**: 직선 궤적으로 더 효율적인 샘플링

DDPM은 현대 확산 모델 연구의 출발점으로서, 그 이론적 프레임워크는 오늘날까지 대부분의 이미지/비디오 생성 모델의 기반이 되고 있다. 2024-2025년 기준으로도 DDPM의 순전파-역전파 프레임워크는 Sora, FLUX, Stable Diffusion 3 등 최신 모델에서 핵심적으로 활용되고 있다.

## 관련 문서

- [[diffusion-thermo|Diffusion (Thermodynamics) - Deep Unsupervised Learning using Nonequilibrium Thermodynamics]] — 발전 기반
- [[classifier-guidance|Classifier Guidance (ADM)]] — 후속 모델
- [[ddim|DDIM (Denoising Diffusion Implicit Models)]] — 후속 모델
- [[dit|DiT (Diffusion Transformers)]] — 후속 모델
- [[edm|EDM (Elucidating Diffusion Models)]] — 후속 모델
- [[imagen|Imagen]] — 후속 모델
- [[ldm|LDM (Latent Diffusion Models)]] — 후속 모델
- [[vdm|VDM]] — 후속 모델
- [[score-sde|Score-based SDE (Stochastic Differential Equations)]] — 영감을 줌
