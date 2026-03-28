# LDM (Latent Diffusion Models): 잠재 공간에서의 효율적 확산 모델

**CompVis / LMU Munich** · **2022-01-05** · **Diffusion** · **Diffusion UNet** · **오픈소스**

## 개요

Latent Diffusion Models(LDM)는 2022년 CompVis/LMU Munich의 Robin Rombach, Andreas Blattmann, Dominik Lorenz, Patrick Esser, Björn Ommer가 발표한 연구로, 확산 모델의 가장 근본적인 문제였던 계산 비용을 혁신적으로 해결한 아키텍처이다. 기존 DDPM, ADM 등 픽셀 공간 확산 모델은 고해상도 이미지를 직접 처리해야 하므로 수백 GPU-day의 학습 비용이 필요했다. LDM은 이 문제를 "인식 압축(Perceptual Compression)"과 "의미적 생성(Semantic Generation)"을 분리하는 두 단계 접근으로 해결하였다.

핵심 아이디어는 사전학습된 VAE로 이미지를 저차원 잠재 공간으로 압축한 뒤, 그 잠재 공간에서만 확산 과정을 수행하는 것이다. 예를 들어, 512×512×3 이미지는 64×64×4 잠재 벡터로 압축되어 데이터 크기가 48배 줄어든다. 이로써 동일한 GPU 예산에서 훨씬 빠른 학습과 추론이 가능해졌으며, 일반 소비자급 GPU에서도 고해상도 이미지 생성이 가능해졌다.

LDM은 Cross-Attention 메커니즘을 통해 텍스트, 클래스, 레이아웃, 세그멘테이션 맵 등 다양한 조건을 유연하게 주입할 수 있는 범용적 조건부 생성 프레임워크를 제시하였다. 이 아키텍처는 이후 Stable Diffusion 시리즈의 기반이 되어 오픈소스 이미지 생성 혁명을 이끌었으며, SDXL, ControlNet, IP-Adapter 등 수많은 후속 연구와 응용의 토대가 되었다.

- **논문**: [High-Resolution Image Synthesis with Latent Diffusion Models](https://arxiv.org/abs/2112.10752)
- **코드**: [CompVis/latent-diffusion](https://github.com/CompVis/latent-diffusion)
- **발표**: 2022년 1월, CompVis / LMU Munich
- **라이선스**: MIT

![LDM 아키텍처 — VAE 잠재 공간에서 확산 과정을 수행하고 Cross-Attention으로 조건을 주입하는 구조](figures/architecture.svg)

*Figure 1: LDM 아키텍처 — 사전학습된 VAE로 이미지를 저차원 잠재 공간에 압축한 뒤, U-Net에서 확산 과정을 수행하고 Cross-Attention으로 텍스트·클래스 등 다양한 조건을 유연하게 주입한다.*

![인식 압축과 의미적 압축의 관계 — Rate-Distortion 곡선에서 LDM의 위치](figures/fig_2.jpg)
*Figure 1: 인식 압축 vs 의미적 압축 — 대부분의 이미지 비트는 인식 불가능한 디테일에 해당하며, Autoencoder+GAN이 이를 제거(인식 압축)한 후 LDM이 의미적 생성을 담당한다. (Source: Rombach et al., 2022)*

## 아키텍처 상세

### 두 단계 파이프라인

LDM의 핵심 구조는 세 가지 구성 요소로 이루어진다:

**1단계 — 인식 압축 (Perceptual Compression):**

사전학습된 오토인코더가 이미지를 잠재 공간으로 인코딩한다:

$$z = \mathcal{E}(x), \quad x \in \mathbb{R}^{H \times W \times 3}, \quad z \in \mathbb{R}^{h \times w \times c}$$

여기서 다운샘플링 인수 $f = H/h = W/w$이다. 논문은 $f \in \{1, 2, 4, 8, 16, 32\}$를 실험하였다.

VAE에는 두 가지 정규화 방식이 사용된다:
- **KL-정규화**: 잠재 분포를 표준 정규분포로 정규화하는 작은 KL 페널티
- **VQ-정규화**: VQ-VAE처럼 잠재 벡터를 코드북으로 양자화

**2단계 — 잠재 확산 (Latent Diffusion):**

U-Net 기반 디노이저 $\epsilon_\theta$가 잠재 공간에서 노이즈를 예측한다:

$$\mathcal{L}_{\text{LDM}} = \mathbb{E}_{\mathcal{E}(x), \epsilon \sim \mathcal{N}(0,1), t} \left[ \| \epsilon - \epsilon_\theta(z_t, t) \|_2^2 \right]$$

**3단계 — 디코딩:**

생성된 잠재 벡터를 VAE 디코더로 복원한다:

$$\hat{x} = \mathcal{D}(\hat{z})$$

### 다운샘플링 인수 분석

논문의 중요한 실험 중 하나는 최적 다운샘플링 인수를 찾는 것이다:

| 다운샘플링 인수 $f$ | 잠재 공간 크기 | FID (↓) | 학습 효율 |
|-------------------|------------|---------|----------|
| $f=1$ (픽셀 공간) | 256×256×3 | 기준선 | 매우 느림 |
| $f=4$ (LDM-4) | 64×64×3 | 우수 | 빠름 |
| $f=8$ (LDM-8) | 32×32×4 | **최적** | **매우 빠름** |
| $f=16$ (LDM-16) | 16×16×16 | 열화 | 가장 빠름 |
| $f=32$ (LDM-32) | 8×8×64 | 심각 열화 | 가장 빠름 |

$f=4$~$f=8$이 품질과 효율의 최적 균형점으로, 이후 Stable Diffusion은 KL-f8을 표준으로 채택하였다.

![다운샘플링 인수별 FID vs 학습 진행도 비교 — LDM-4~8이 최적 균형](figures/fig_6_1.jpg)
*Figure 3: 다운샘플링 인수별 학습 효율 비교 — LDM-1(픽셀 공간)은 학습이 매우 느리고, LDM-32는 과도한 압축으로 품질이 저하된다. LDM-4~8이 FID와 학습 속도의 최적 균형을 보여준다. (Source: Rombach et al., 2022)*

### Cross-Attention 조건 메커니즘

![LDM의 조건 주입 방식 — 연결(concatenation)과 Cross-Attention 메커니즘 비교](figures/fig_3.png)
*Figure 2: LDM 조건 주입 아키텍처 — 입력 연결 방식과 Cross-Attention 방식으로 텍스트, 시맨틱 맵, 이미지 등 다양한 조건을 U-Net에 주입한다. (Source: Rombach et al., 2022)*

LDM의 두 번째 핵심 기여는 범용적 조건 주입 메커니즘이다. 도메인별 인코더 $\tau_\theta$가 조건 입력 $y$를 중간 표현으로 변환하고, Cross-Attention으로 U-Net에 주입한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d}}\right) \cdot V$$

$$Q = W_Q^{(i)} \cdot \varphi_i(z_t), \quad K = W_K^{(i)} \cdot \tau_\theta(y), \quad V = W_V^{(i)} \cdot \tau_\theta(y)$$

여기서 $\varphi_i(z_t)$는 U-Net의 $i$번째 레이어의 중간 표현이고, $\tau_\theta(y)$는 조건 인코더의 출력이다. 이 설계의 핵심 장점은 $\tau_\theta$만 바꾸면 어떤 조건이든 동일한 방식으로 주입할 수 있다는 것이다:

| 조건 유형 | 인코더 $\tau_\theta$ | 응용 |
|---------|-------------------|------|
| 텍스트 | CLIP / BERT | 텍스트-이미지 생성 |
| 클래스 | 임베딩 룩업 | 클래스 조건부 생성 |
| 레이아웃 | CNN | 레이아웃-이미지 |
| 시맨틱 맵 | CNN | 시맨틱 합성 |
| 이미지 | CLIP 이미지 인코더 | 이미지 변형 |

### U-Net 구조

LDM의 U-Net은 시간 임베딩이 결합된 ResNet 블록과 Spatial Transformer 블록으로 구성된다. Spatial Transformer는 Self-Attention으로 공간적 관계를 학습하고, Cross-Attention으로 조건 정보를 주입한다.

$$h_{\text{out}} = \text{CrossAttn}(\text{SelfAttn}(\text{LN}(h_{\text{in}})), \tau_\theta(y)) + h_{\text{in}}$$

## 핵심 혁신

1. **잠재 공간 확산**: 픽셀 공간 대신 VAE 잠재 공간에서 확산을 수행하여 계산 비용을 수십 배 절감하면서도 생성 품질을 유지하였다. 이는 인식 압축과 의미적 생성의 분리라는 핵심 통찰에 기반한다.

2. **범용적 Cross-Attention 조건화**: 도메인별 인코더 + Cross-Attention이라는 단순하면서도 강력한 프레임워크로, 텍스트, 이미지, 레이아웃, 시맨틱 맵 등 어떤 조건이든 동일한 방식으로 주입할 수 있음을 보였다.

3. **최적 압축 비율 발견**: 다운샘플링 인수 $f$에 대한 체계적 실험으로 $f=4$~$f=8$이 품질-효율 최적점임을 확인하였다. 이 결과는 이후 모든 잠재 확산 모델의 설계 기준이 되었다.

4. **실용적 접근성**: 일반 소비자급 GPU(10GB VRAM)에서도 고해상도 이미지 생성을 가능하게 하여, 확산 모델의 대중화를 이끌었다.

## 벤치마크/성능

| 작업 | 데이터셋 | FID (↓) | 비교 |
|------|---------|---------|------|
| 무조건부 생성 | CelebA-HQ 256 | **5.11** | DDPM: 7.89 |
| 무조건부 생성 | LSUN-Churches 256 | **4.02** | ADM: 7.89 |
| 무조건부 생성 | LSUN-Bedroom 256 | **2.95** | - |
| 텍스트-이미지 | MS-COCO 256 | **12.63** | GLIDE: 12.24 |
| 레이아웃-이미지 | COCO Stuff | **40.91** | - |
| 인페인팅 | Places 512 | 경쟁력 | - |
| 초해상도 | ImageNet | 경쟁력 | SR3 비교 |

동일한 연산 예산에서 LDM은 픽셀 공간 확산 모델 대비 일관되게 우수한 FID를 달성한다.

## 관련 모델 비교

| 특성 | LDM | DDPM | ADM | DALL·E |
|------|-----|------|-----|--------|
| 확산 공간 | 잠재 | 픽셀 | 픽셀 | 잠재 (dVAE) |
| 백본 | U-Net | U-Net | U-Net | Transformer |
| 조건화 | Cross-Attention | 없음 | Classifier | 자기회귀 |
| 해상도 확장 | 매우 유리 | 불리 | 불리 | 유리 |
| GPU 요구량 | 낮음 | 높음 | 매우 높음 | 높음 |
| 생성 품질 | 우수 | 우수 | 최우수 | 우수 |

## 학습 상세

- **데이터셋**: CelebA-HQ, FFHQ, LSUN-Churches/Bedroom (무조건부), LAION-400M (텍스트-이미지)
- **VAE**: KL-정규화 또는 VQ-정규화 오토인코더, 별도 사전학습 후 동결
- **최적화**: Adam, 학습률 ~1e-4, 배치 크기 32
- **하드웨어**: V100 GPU 기준 수일~수주 (작업 및 규모에 따라)
- **노이즈 스케줄**: 선형 스케줄 $\beta_1=0.0015$, $\beta_T=0.0195$, $T=1000$
- **샘플링**: DDIM 샘플러 지원 (50~200 스텝)

## 실무 활용

![LAION 데이터셋으로 학습한 LDM-8의 텍스트-이미지 생성 샘플](figures/fig_5_1.jpg)
*Figure 4: 텍스트-이미지 생성 — LAION 데이터셋으로 학습한 LDM-8(KL)이 사용자 텍스트 프롬프트에서 생성한 이미지. 이 모델이 Stable Diffusion의 직접적 전신이다. (Source: Rombach et al., 2022)*

### 1. Stable Diffusion의 기반

LDM은 Stable Diffusion 1.x/2.x의 직접적 기반 아키텍처이다. Stability AI는 LDM의 KL-f8 VAE + U-Net + CLIP Cross-Attention 구조를 대규모 데이터(LAION-5B)로 학습하여 Stable Diffusion을 만들었다.

### 2. 효율적 커스텀 학습

잠재 공간에서의 학습은 LoRA, Textual Inversion, DreamBooth 등 파라미터 효율적 미세조정 기법과 자연스럽게 결합되어, 소비자급 GPU에서도 개인화된 이미지 생성이 가능하다.

### 3. 다양한 조건부 생성

Cross-Attention 조건화의 범용성 덕분에 ControlNet(포즈, 에지, 깊이 맵), IP-Adapter(이미지 조건), T2I-Adapter 등 다양한 조건부 생성 확장이 가능하다.

## 한계 및 전망

### 한계

1. **VAE 병목**: 잠재 공간 압축 과정에서 고주파 디테일이 손실될 수 있다. 특히 텍스트 렌더링, 미세한 패턴 등에서 한계가 나타난다.
2. **2단계 학습의 비효율**: VAE와 확산 모델을 별도로 학습해야 하므로 전체 파이프라인의 end-to-end 최적화가 불가능하다.
3. **U-Net 스케일링 한계**: U-Net 구조는 Transformer와 달리 명확한 스케일링 법칙이 없어, 모델 확장 시 체계적 설계가 어렵다.

### 후속 발전

- **Stable Diffusion (2022)**: LDM을 LAION-5B로 대규모 학습
- **SDXL (2023)**: 3.5B U-Net + 이중 텍스트 인코더로 1024×1024 생성
- **ControlNet (2023)**: LDM에 공간적 조건을 추가하는 플러그인 아키텍처
- **SD3 (2024)**: U-Net을 MMDiT로 대체하여 스케일링 가능성 확보

LDM은 확산 모델을 실용화한 가장 중요한 연구로, "잠재 공간에서의 확산"이라는 패러다임을 확립하여 이후 모든 상용 이미지 생성 모델의 기반이 되었다.

### 기술적 의의

LDM의 핵심 통찰인 "인식 압축과 의미적 생성의 분리"는 이미지 생성 분야를 근본적으로 바꾸었다. 기존 접근(DDPM, ADM)이 "더 크고 더 강력한 모델"로 품질을 높이려 했다면, LDM은 "더 스마트한 공간에서 작업"함으로써 동일한 품질을 훨씬 적은 비용으로 달성할 수 있음을 보였다. 이 아이디어는 이후 비디오 생성(Sora, CogVideoX), 3D 생성, 오디오 생성 등 다양한 모달리티로 확장되어, 잠재 공간 생성 모델의 표준 설계 패턴이 되었다. 특히 Cross-Attention 조건화 메커니즘은 확산 모델의 다재다능함(versatility)을 가능하게 한 핵심 기법으로, ControlNet, IP-Adapter, T2I-Adapter, Inpainting, Outpainting 등 확산 모델 생태계 전체의 기반이 되었다.

## 관련 문서

- [[ddpm|DDPM (Denoising Diffusion Probabilistic Models)]] — 발전 기반
- [[controlnet|ControlNet]] — 후속 모델
- [[sdxl|SDXL (Stable Diffusion XL)]] — 후속 모델
