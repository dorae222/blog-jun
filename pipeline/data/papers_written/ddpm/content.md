## 개요

"Denoising Diffusion Probabilistic Models"(Ho et al., 2020)은 확산 확률 모델(diffusion probabilistic model)을 이용하여 고품질 이미지를 생성하는 방법을 제안한 논문입니다. 논문 발표 당시 GAN(Generative Adversarial Network)이 이미지 생성 분야의 지배적인 패러다임이었지만, DDPM은 GAN 없이도 CIFAR-10에서 FID 3.17, 256×256 LSUN Bedroom에서 FID 6.36이라는 당시 최고 수준의 이미지 품질을 달성했습니다.

DDPM의 핵심 아이디어는 물리학의 확산 과정(diffusion process)에서 영감을 받은 것으로, 데이터에 점진적으로 노이즈를 추가하여 순수 가우시안 노이즈로 변환하는 과정(forward process)을 정의하고, 이를 역으로 수행하여 노이즈에서 데이터를 복원하는 역방향 과정(reverse process)을 신경망으로 학습합니다. 이 논문은 2024년 기준 Google Scholar 인용 수 1만 8천 회 이상으로, 딥러닝 역사상 가장 영향력 있는 논문 중 하나가 되었습니다.

## 배경 및 문제

### 생성 모델의 계보

2020년 이전까지 딥러닝 기반 이미지 생성의 주류는 다음과 같았습니다:

- **GAN (Goodfellow et al., 2014)**: 생성자(Generator)와 판별자(Discriminator)가 경쟁하는 구조. StyleGAN, BigGAN 등이 높은 품질을 달성했으나 학습 불안정성, 모드 붕괴(mode collapse), 다양성 부족 등의 문제가 있었습니다
- **VAE (Kingma & Welling, 2014)**: 잠재 공간에서 확률적 생성을 수행하지만, 생성 이미지가 흐릿(blurry)하고 품질이 GAN에 비해 낮았습니다
- **흐름 기반 모델 (Normalizing Flows)**: 정확한 우도(likelihood)를 계산할 수 있지만 아키텍처 제약이 크고 계산 비용이 높았습니다
- **자동회귀 모델 (PixelCNN 등)**: 픽셀 단위 생성으로 이론적으로 완전한 분포 모델링이 가능하지만 생성 속도가 극히 느렸습니다

### 확산 모델의 이론적 배경

DDPM에 직접적인 영향을 준 이전 연구들:

- **Sohl-Dickstein et al. (2015)**: 확산 과정을 생성 모델에 처음 적용했으나 샘플 품질이 낮았습니다
- **Song & Ermon (2019)**: 스코어 매칭(score matching)을 통한 생성 모델을 제안하여 가능성을 보여주었습니다

Ho et al.의 기여는 확산 모델의 학습 목표를 단순화하고, 이미지 생성에 최적화된 아키텍처와 학습 방법을 통해 처음으로 GAN을 능가하는 품질을 달성한 것입니다.

## 핵심 아이디어

### 순방향 과정 (Forward Process)

DDPM은 데이터 $\mathbf{x}_0 \sim q(\mathbf{x}_0)$에 총 $T$번의 작은 가우시안 노이즈를 순차적으로 추가하는 **마르코프 체인**을 정의합니다:

$$q(\mathbf{x}_t | \mathbf{x}_{t-1}) = \mathcal{N}(\mathbf{x}_t; \sqrt{1-\beta_t}\mathbf{x}_{t-1}, \beta_t \mathbf{I})$$

여기서 $\beta_t \in (0, 1)$은 각 타임스텝에서의 노이즈 스케줄입니다. 논문에서는 $T=1000$, $\beta_1=10^{-4}$에서 $\beta_T=0.02$로 선형 증가하는 스케줄을 사용합니다.

이 과정의 핵심 성질은 **임의의 타임스텝 $t$에서의 노이즈된 이미지를 원본 이미지 $\mathbf{x}_0$로부터 직접 샘플링**할 수 있다는 것입니다. $\alpha_t = 1 - \beta_t$, $\bar{\alpha}_t = \prod_{s=1}^{t} \alpha_s$로 정의하면:

$$q(\mathbf{x}_t | \mathbf{x}_0) = \mathcal{N}(\mathbf{x}_t; \sqrt{\bar{\alpha}_t}\mathbf{x}_0, (1-\bar{\alpha}_t)\mathbf{I})$$

즉, $\mathbf{x}_t = \sqrt{\bar{\alpha}_t}\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon}$으로 한 번에 계산할 수 있습니다($\boldsymbol{\epsilon} \sim \mathcal{N}(0, \mathbf{I})$). $T \to \infty$이면 $q(\mathbf{x}_T) \approx \mathcal{N}(0, \mathbf{I})$가 됩니다.

다음 그래프 모델은 DDPM의 순방향 과정과 역방향 과정의 마르코프 체인 구조를 보여줍니다.

![DDPM의 방향성 그래프 모델](figures/fig_2.png)
*DDPM의 방향성 그래프 모델(directed graphical model). 순방향 과정 $q(\mathbf{x}_t|\mathbf{x}_{t-1})$은 데이터에 점진적으로 노이즈를 추가하고, 역방향 과정 $p_\theta(\mathbf{x}_{t-1}|\mathbf{x}_t)$는 학습된 신경망으로 노이즈를 단계적으로 제거합니다.*

### 역방향 과정 (Reverse Process)

생성을 위해서는 순수 노이즈 $\mathbf{x}_T \sim \mathcal{N}(0, \mathbf{I})$에서 역방향으로 노이즈를 제거해야 합니다. 참 역방향 분포는:

$$q(\mathbf{x}_{t-1} | \mathbf{x}_t) = q(\mathbf{x}_t | \mathbf{x}_{t-1}) \cdot \frac{q(\mathbf{x}_{t-1})}{q(\mathbf{x}_t)}$$

이는 전체 데이터 분포에 의존하므로 직접 계산이 불가능합니다. DDPM은 이를 가우시안 분포로 근사하는 신경망 $p_\theta$를 학습합니다:

$$p_\theta(\mathbf{x}_{t-1} | \mathbf{x}_t) = \mathcal{N}(\mathbf{x}_{t-1}; \boldsymbol{\mu}_\theta(\mathbf{x}_t, t), \boldsymbol{\Sigma}_\theta(\mathbf{x}_t, t))$$

중요한 관찰: $\mathbf{x}_0$가 주어질 때 역방향 조건부 분포는 tractable합니다:

$$q(\mathbf{x}_{t-1} | \mathbf{x}_t, \mathbf{x}_0) = \mathcal{N}(\mathbf{x}_{t-1}; \tilde{\boldsymbol{\mu}}_t(\mathbf{x}_t, \mathbf{x}_0), \tilde{\beta}_t \mathbf{I})$$

$$\tilde{\boldsymbol{\mu}}_t(\mathbf{x}_t, \mathbf{x}_0) = \frac{\sqrt{\bar{\alpha}_{t-1}}\beta_t}{1-\bar{\alpha}_t}\mathbf{x}_0 + \frac{\sqrt{\alpha_t}(1-\bar{\alpha}_{t-1})}{1-\bar{\alpha}_t}\mathbf{x}_t, \quad \tilde{\beta}_t = \frac{1-\bar{\alpha}_{t-1}}{1-\bar{\alpha}_t}\beta_t$$

## 방법론

### 학습 목표 단순화

변분 하한(ELBO)을 최적화하면 다음과 같은 손실 함수를 얻습니다:

$$L_{\text{VLB}} = \mathbb{E}_q\left[\underbrace{D_{\text{KL}}(q(\mathbf{x}_T|\mathbf{x}_0) \| p(\mathbf{x}_T))}_{L_T} + \sum_{t=2}^{T}\underbrace{D_{\text{KL}}(q(\mathbf{x}_{t-1}|\mathbf{x}_t,\mathbf{x}_0) \| p_\theta(\mathbf{x}_{t-1}|\mathbf{x}_t))}_{L_{t-1}} - \underbrace{\log p_\theta(\mathbf{x}_0|\mathbf{x}_1)}_{L_0}\right]$$

Ho et al.의 핵심 기여는 이 복잡한 손실 함수를 **단순한 노이즈 예측 목표**로 단순화한 것입니다. $\mathbf{x}_t = \sqrt{\bar{\alpha}_t}\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon}$을 $\mathbf{x}_0$에 대해 정리하면:

$$\mathbf{x}_0 = \frac{\mathbf{x}_t - \sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon}}{\sqrt{\bar{\alpha}_t}}$$

이를 $\tilde{\boldsymbol{\mu}}_t$에 대입하면, 모델이 예측해야 할 것은 결국 **원래 추가된 노이즈 $\boldsymbol{\epsilon}$**임을 알 수 있습니다. 따라서 단순화된 학습 목표는:

$$L_{\text{simple}} = \mathbb{E}_{t \sim [1,T], \mathbf{x}_0 \sim q(\mathbf{x}_0), \boldsymbol{\epsilon} \sim \mathcal{N}(0,\mathbf{I})}\left[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)\|^2\right]$$

즉, 타임스텝 $t$에서의 노이즈된 이미지 $\mathbf{x}_t$와 타임스텝 $t$를 입력으로 받아 원래 노이즈 $\boldsymbol{\epsilon}$을 예측하도록 U-Net 구조의 신경망 $\boldsymbol{\epsilon}_\theta$를 학습합니다.

### U-Net 아키텍처

논문에서는 PixelCNN++ 구조에서 영감받은 U-Net 아키텍처를 사용합니다:

- **인코더-디코더 구조**: 점진적 다운샘플링과 업샘플링으로 멀티스케일 특징을 포착합니다
- **Skip Connection**: 인코더와 디코더를 연결하여 세밀한 공간 정보를 보존합니다
- **Residual Block**: 각 해상도 레벨에서 여러 개의 ResBlock을 사용합니다
- **Self-Attention**: 16×16 해상도에서 Self-Attention Layer를 삽입합니다
- **타임스텝 임베딩**: Transformer의 Sinusoidal Positional Encoding에서 영감받은 임베딩을 각 ResBlock에 주입합니다

타임스텝 $t$는 다음과 같이 임베딩됩니다:

$$\text{Embed}(t) = \text{MLP}([\sin(t/10000^{2i/d}), \cos(t/10000^{2i/d})])_{i=1}^{d/2}$$

이 임베딩은 ResBlock의 중간 활성화에 더해져(additively conditioning) 모델이 현재 타임스텝을 인식하게 합니다.

### 샘플링 알고리즘

**학습 알고리즘:**
```
반복:
  1. x_0 ~ q(x_0)        -- 학습 데이터 샘플링
  2. t ~ Uniform({1,...,T}) -- 타임스텝 랜덤 샘플링
  3. ε ~ N(0, I)           -- 노이즈 샘플링
  4. 경사 하강: ∇_θ ||ε - ε_θ(√α̅_t x_0 + √(1-α̅_t)ε, t)||²
```

**생성 알고리즘 (Reverse Process):**
```
x_T ~ N(0, I)
for t = T, T-1, ..., 1:
  z ~ N(0, I)  (t > 1이면), z = 0 (t = 1이면)
  x_{t-1} = 1/√α_t * (x_t - β_t/√(1-α̅_t) * ε_θ(x_t, t)) + √β_t * z
```

### 분산 스케줄과 모델 설계

논문에서는 다음 하이퍼파라미터를 사용합니다:

| 설정 | 값 |
|------|----|
| 타임스텝 $T$ | 1000 |
| 노이즈 스케줄 | 선형: $\beta_1=10^{-4}$ → $\beta_T=0.02$ |
| 분산 $\Sigma_\theta$ | 고정: $\tilde{\beta}_t \mathbf{I}$ 또는 $\beta_t \mathbf{I}$ |
| 학습률 | $2 \times 10^{-4}$ (Adam) |
| 배치 크기 | 128 |
| 모델 채널 | 128 (CIFAR-10), 128 (256×256) |

## 실험 결과

### 이미지 품질 비교 (FID 기준)

**CIFAR-10 (32×32):**

| 모델 | FID ↓ | IS ↑ |
|------|-------|------|
| StyleGAN (Karras et al., 2019) | 8.73 | 9.26 |
| EBM (Du & Mordatch, 2019) | 38.2 | 8.30 |
| Flow++ (Ho et al., 2019) | 46.0 | - |
| WGAN-GP (Gulrajani et al., 2017) | 36.4 | 7.86 |
| Score Matching (Song & Ermon, 2019) | 25.32 | 8.87 |
| **DDPM (ours)** | **3.17** | **9.46** |

**LSUN Bedroom (256×256):**

| 모델 | FID ↓ |
|------|-------|
| ProgressiveGAN (Karras et al., 2018) | 8.34 |
| NVAE (Vahdat & Kautz, 2020) | 83.9 |
| **DDPM (ours)** | **6.36** (반복 없음) |

### 로그 우도 (Bits per Dim)

| 데이터셋 | DDPM |
|---------|------|
| CIFAR-10 | 3.70 bpd |
| LSUN Bedroom | 3.00 bpd |

GAN과 비교하여 DDPM은 로그 우도도 우수하여, 단순 샘플 품질을 넘어 확률적으로도 더 정확한 생성 분포를 학습함을 보여줍니다.

### Ablation: 학습 목표 비교

논문은 다양한 학습 목표를 실험적으로 비교합니다:

| 목표 | FID ↓ |
|------|-------|
| $\mathbf{x}_0$ 예측 (원본 이미지 예측) | 13.9 |
| $\boldsymbol{\epsilon}$ 예측 (노이즈 예측, $L_{\text{simple}}$) | **3.17** |
| $\boldsymbol{\mu}$ 예측 (평균 예측) | 6.64 |
| VLB 직접 최적화 | 7.43 |

노이즈 $\boldsymbol{\epsilon}$을 예측하는 단순화된 목표가 가장 좋은 성능을 보여줍니다. 이는 이론적으로도 해석 가능한데, 노이즈 예측은 스코어 함수 $\nabla_{\mathbf{x}_t} \log q(\mathbf{x}_t)$를 암묵적으로 학습하는 것과 동치이기 때문입니다.

### 점진적 생성 과정

역방향 과정에서 $\hat{\mathbf{x}}_0$ 예측이 시간에 따라 어떻게 변화하는지 시각화하면, DDPM의 생성 메커니즘을 직관적으로 이해할 수 있습니다.

![CIFAR-10 점진적 생성 과정](figures/fig_12.jpg)
*CIFAR-10 무조건부 생성의 점진적 과정. 각 행은 하나의 샘플이며, 왼쪽(순수 노이즈)에서 오른쪽(최종 이미지)으로 $\hat{\mathbf{x}}_0$ 예측이 점차 선명해집니다. 초기에는 전체적인 구조와 색상이 결정되고, 후반부에서 세부 디테일이 완성됩니다.*

### 잠재 공간의 의미 있는 구조

DDPM의 잠재 공간은 의미론적으로 잘 구조화되어 있습니다. 동일한 잠재 변수 $\mathbf{x}_t$를 공유하되 서로 다른 역방향 샘플링 경로를 따르면, 생성된 이미지들이 높은 수준의 속성(포즈, 피부색 등)을 공유하면서도 세부적으로는 다양한 결과를 보여줍니다.

![확률적 디코딩을 통한 속성 공유](figures/fig_13.jpg)
*동일한 잠재 변수에서의 확률적 디코딩. 각 그룹의 우측 하단이 공유 잠재 변수 $\mathbf{x}_t$이고, 나머지 세 이미지는 $p_\theta(\mathbf{x}_0|\mathbf{x}_t)$에서 독립적으로 샘플링한 결과입니다. $t$가 클수록(노이즈가 많을수록) 전체적 구조만 공유하고, $t$가 작을수록 더 유사한 이미지를 생성합니다.*

이러한 계층적 잠재 구조를 활용하면 확산 공간에서의 보간(interpolation)도 가능합니다. 두 이미지를 확산시킨 후 잠재 공간에서 선형 보간하고 역방향 과정을 수행하면, 픽셀 공간 보간과 달리 의미론적으로 자연스러운 중간 이미지를 생성할 수 있습니다.

![확산 공간에서의 이미지 보간](figures/fig_14.jpg)
*CelebA-HQ 256x256에서의 확산 공간 보간. 왼쪽 다이어그램은 보간 방식을 설명합니다. 두 소스 이미지를 500 타임스텝 확산시킨 후 잠재 공간에서 $\lambda$로 선형 보간하여 역방향 과정을 수행합니다. 결과물은 이미지 매니폴드 위에서 자연스럽게 전이됩니다.*

## 의의 및 한계

### 의의

- **GAN을 능가하는 품질**: 학습 안정성 문제 없이 GAN을 처음으로 체계적으로 능가했습니다. 모드 붕괴, 학습 불안정성 등 GAN의 고질적 문제 없이 고품질 생성이 가능합니다
- **단순하고 안정적인 학습**: 노이즈 예측이라는 단순한 회귀 목표는 GAN의 불안정한 min-max 게임에 비해 훨씬 안정적입니다
- **이론적 근거**: 변분 하한을 기반으로 하여 이론적으로 엄밀한 확률 모델입니다
- **현대 AI의 토대**: Stable Diffusion, DALL-E 2, Midjourney, Imagen, Sora 등 모든 현대 이미지/비디오 생성 AI의 기반이 되었습니다
- **다양한 응용**: 이미지 편집, 인페인팅, 슈퍼해상도, 의료 이미지 생성 등에 광범위하게 적용됩니다

### 한계

- **느린 샘플링**: $T=1000$번의 U-Net 포워드 패스가 필요하여 GAN 대비 수백~수천 배 느립니다. 256×256 이미지 하나를 생성하는 데 수 초~수십 초가 걸립니다
- **높은 계산 비용**: 학습 및 추론 모두 큰 계산 자원이 필요합니다
- **픽셀 공간에서의 동작**: 고해상도 이미지 생성 시 메모리와 계산 비용이 급격히 증가합니다 (이 문제는 이후 LDM이 잠재 공간에서 동작함으로써 해결합니다)
- **조건부 생성의 어려움**: 기본 DDPM은 무조건부 생성만 수행하며, 텍스트나 클래스 조건 생성을 위해서는 추가적인 방법이 필요합니다 (Classifier Guidance, Classifier-Free Guidance 등)

## 코드 예제

### DDPM 핵심 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from tqdm import tqdm


class DDPM:
    """Denoising Diffusion Probabilistic Models 구현.
    
    논문: Ho et al. (2020) - https://arxiv.org/abs/2006.11239
    """
    
    def __init__(self, model, T=1000, beta_start=1e-4, beta_end=0.02, device='cuda'):
        self.model = model  # U-Net ε_θ(x_t, t)
        self.T = T
        self.device = device
        
        # 노이즈 스케줄 설정 (선형 스케줄)
        self.betas = torch.linspace(beta_start, beta_end, T).to(device)
        self.alphas = 1.0 - self.betas
        self.alpha_bars = torch.cumprod(self.alphas, dim=0)  # ᾱ_t = Π_{s=1}^{t} α_s
        
        # 자주 쓰이는 값들 미리 계산
        self.sqrt_alpha_bars = torch.sqrt(self.alpha_bars)
        self.sqrt_one_minus_alpha_bars = torch.sqrt(1.0 - self.alpha_bars)
        self.sqrt_recip_alphas = torch.sqrt(1.0 / self.alphas)
        
        # 역방향 과정 분산: β̃_t = (1-ᾱ_{t-1})/(1-ᾱ_t) * β_t
        alpha_bars_prev = F.pad(self.alpha_bars[:-1], (1, 0), value=1.0)
        self.posterior_variance = self.betas * (1.0 - alpha_bars_prev) / (1.0 - self.alpha_bars)
    
    def q_sample(self, x0, t, noise=None):
        """순방향 과정: x_0에서 임의 타임스텝 t의 x_t를 샘플링.
        
        수식: x_t = √ᾱ_t * x_0 + √(1-ᾱ_t) * ε
        """
        if noise is None:
            noise = torch.randn_like(x0)
        
        sqrt_alpha_bar = self.sqrt_alpha_bars[t].view(-1, 1, 1, 1)
        sqrt_one_minus = self.sqrt_one_minus_alpha_bars[t].view(-1, 1, 1, 1)
        
        return sqrt_alpha_bar * x0 + sqrt_one_minus * noise
    
    def p_losses(self, x0, t, noise=None):
        """학습 손실 계산: L_simple = E[||ε - ε_θ(x_t, t)||²]"""
        if noise is None:
            noise = torch.randn_like(x0)
        
        # 순방향 과정으로 x_t 생성
        xt = self.q_sample(x0, t, noise)
        
        # 신경망으로 노이즈 예측
        predicted_noise = self.model(xt, t)
        
        # MSE 손실 (노이즈 예측)
        loss = F.mse_loss(predicted_noise, noise)
        return loss
    
    @torch.no_grad()
    def p_sample(self, xt, t):
        """역방향 과정의 한 스텝: x_t에서 x_{t-1} 샘플링.
        
        수식: x_{t-1} = 1/√α_t * (x_t - β_t/√(1-ᾱ_t) * ε_θ(x_t, t)) + √β̃_t * z
        """
        betas_t = self.betas[t].view(-1, 1, 1, 1)
        sqrt_one_minus_t = self.sqrt_one_minus_alpha_bars[t].view(-1, 1, 1, 1)
        sqrt_recip_t = self.sqrt_recip_alphas[t].view(-1, 1, 1, 1)
        
        # ε_θ(x_t, t) 예측
        model_mean = sqrt_recip_t * (
            xt - betas_t / sqrt_one_minus_t * self.model(xt, t)
        )
        
        if t[0] == 0:
            return model_mean
        
        # 노이즈 추가
        posterior_variance_t = self.posterior_variance[t].view(-1, 1, 1, 1)
        noise = torch.randn_like(xt)
        return model_mean + torch.sqrt(posterior_variance_t) * noise
    
    @torch.no_grad()
    def sample(self, shape):
        """역방향 과정 전체: x_T ~ N(0,I)에서 x_0 생성."""
        device = self.device
        batch_size = shape[0]
        
        # 순수 노이즈에서 시작
        xt = torch.randn(shape, device=device)
        
        # T번 역방향 스텝 반복
        for t in tqdm(reversed(range(0, self.T)), total=self.T, desc='Sampling'):
            t_batch = torch.full((batch_size,), t, device=device, dtype=torch.long)
            xt = self.p_sample(xt, t_batch)
        
        return xt
    
    def train_step(self, optimizer, x0):
        """한 번의 학습 스텝."""
        optimizer.zero_grad()
        
        # 랜덤 타임스텝 샘플링
        t = torch.randint(0, self.T, (x0.shape[0],), device=self.device).long()
        
        # 손실 계산 및 역전파
        loss = self.p_losses(x0, t)
        loss.backward()
        optimizer.step()
        
        return loss.item()


# 간단한 U-Net 타임스텝 임베딩 예시
class TimestepEmbedding(nn.Module):
    """Sinusoidal 타임스텝 임베딩 + MLP."""
    def __init__(self, dim):
        super().__init__()
        self.dim = dim
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.SiLU(),
            nn.Linear(dim * 4, dim),
        )
    
    def forward(self, t):
        # Sinusoidal 임베딩
        half = self.dim // 2
        freqs = torch.exp(
            -torch.arange(half, device=t.device) * (np.log(10000) / (half - 1))
        )
        args = t[:, None].float() * freqs[None]
        embedding = torch.cat([torch.cos(args), torch.sin(args)], dim=-1)
        return self.mlp(embedding)


# 사용 예시
if __name__ == '__main__':
    # 더미 U-Net (실제로는 full U-Net 구현 필요)
    class DummyUNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = nn.Conv2d(3, 3, 3, padding=1)
            self.t_emb = TimestepEmbedding(128)
        
        def forward(self, x, t):
            return self.conv(x)  # 실제로는 타임스텝 임베딩을 활용
    
    model = DummyUNet().cuda()
    ddpm = DDPM(model, T=1000)
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-4)
    
    # 학습 스텝
    x0 = torch.randn(8, 3, 32, 32).cuda()  # CIFAR-10 크기
    loss = ddpm.train_step(optimizer, x0)
    print(f'Loss: {loss:.4f}')
    
    # 샘플링
    samples = ddpm.sample((4, 3, 32, 32))
    print(f'Generated samples: {samples.shape}')  # (4, 3, 32, 32)
```

## 관련 문서

- [[ddim|DDIM: Denoising Diffusion Implicit Models]] -- 후속 연구 (가속 샘플링)
- [[ldm|Latent Diffusion Models]] -- 후속 연구 (잠재 공간으로 확장)
- [[score-sde|Score-Based Generative Modeling through SDEs]] -- 관련 연구
- [[score-matching|Score Matching]] -- 이론적 배경
- [[cfg|Classifier-Free Guidance]] -- 조건부 생성 확장
- [[classifier-guidance|Classifier Guidance]] -- 조건부 생성 확장
- [[consistency-model|Consistency Models]] -- 후속 연구 (단일 스텝 생성)
