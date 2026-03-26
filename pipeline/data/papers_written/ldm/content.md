## 개요

"High-Resolution Image Synthesis with Latent Diffusion Models"(Rombach et al., CVPR 2022)은 확산 모델(diffusion model)의 뛰어난 생성 품질을 유지하면서 픽셀 공간이 아닌 **압축된 잠재 공간(latent space)**에서 확산 과정을 수행함으로써 계산 비용을 획기적으로 줄인 논문입니다. 이 연구는 Stable Diffusion의 기반 아키텍처가 되어 이미지 생성 AI의 대중화를 이끌었으며, 2025년 기준 Google Scholar 인용 수가 2만 회를 넘어서는 등 딥러닝 역사상 가장 영향력 있는 논문 중 하나로 자리매김했습니다.

DDPM 등 기존 확산 모델은 픽셀 공간에서 동작하기 때문에 고해상도(512x512 이상) 이미지를 생성하려면 엄청난 계산 자원이 필요했습니다. LDM은 이 문제를 두 단계로 분리하여 해결합니다. 먼저 지각적 압축(perceptual compression) 모델로 이미지를 4~16배 압축된 잠재 표현으로 변환한 뒤, 이 작은 잠재 공간에서 확산 과정을 학습합니다. 그 결과 학습 비용과 추론 비용 모두 크게 절감되면서도 생성 품질은 픽셀 공간 모델과 동등하거나 우수합니다.

## 배경 및 문제

### 픽셀 공간 확산 모델의 계산 문제

2020년 DDPM(Ho et al.)의 등장 이후 확산 모델은 GAN을 능가하는 생성 품질로 주목받았습니다. 그러나 확산 모델은 구조적으로 수백~수천 번의 반복적 신경망 평가가 필요하며, 고해상도 이미지에 직접 적용하면 두 가지 근본적인 문제가 발생합니다.

첫째, **학습 비용**의 문제입니다. 256x256 픽셀 이미지는 약 200K차원의 공간에서 확산 과정이 일어납니다. ADM(Dhariwal & Nichol, 2021)처럼 픽셀 공간에서 고해상도 이미지를 다루는 모델은 수백 GPU-day의 학습이 필요합니다.

둘째, **추론 비용**의 문제입니다. 512x512 이미지를 1000 스텝으로 생성하면 U-Net을 1000번 통과해야 하며, 각 통과 시 입력 텐서가 매우 큽니다.

### 지각적 압축의 핵심 통찰

논문의 핵심 통찰은 이미지 정보를 두 종류로 구분한 것입니다.

- **고주파 지각 세부 정보**: 픽셀 수준의 질감, 색상 미세 변화 등 — VQ-VAE나 KL-AE 같은 오토인코더로 효율적으로 처리 가능
- **의미론적 구성 정보**: 구도, 객체 배치, 전반적 스타일 등 — 확산 모델이 학습해야 할 진짜 과제

기존 픽셀 공간 확산 모델은 이 두 종류를 구분하지 않고 모두 학습해야 했습니다. LDM은 첫 번째를 오토인코더에 위임하고, 확산 모델은 두 번째에만 집중하게 만들어 학습 효율을 비약적으로 끌어올립니다.

아래 그림은 이 핵심 통찰을 rate-distortion 관점에서 시각화한 것입니다. 대부분의 비트가 지각적으로 무의미한 세부 정보에 사용되며, LDM은 오토인코더로 이 부분을 먼저 처리한 뒤 의미론적 압축에만 생성 모델을 집중시킵니다.

![지각적 압축과 의미론적 압축의 관계](figures/fig_2.jpg)
*지각적 압축(Perceptual Compression)과 의미론적 압축(Semantic Compression)의 역할 분리. 오토인코더+GAN이 지각적으로 무의미한 고주파 세부 정보를 제거한 뒤, LDM이 의미론적 구성 학습에 집중한다.*

## 핵심 아이디어

### 2단계 학습 프레임워크

LDM은 학습을 명확히 두 단계로 분리합니다.

**1단계: 지각적 압축 모델 학습**

VQ-regularized 오토인코더(VQ-VAE 계열) 또는 KL-regularized 오토인코더를 학습합니다. 인코더 $\mathcal{E}$는 이미지 $x \in \mathbb{R}^{H \times W \times 3}$를 잠재 벡터 $z = \mathcal{E}(x) \in \mathbb{R}^{h \times w \times c}$로 변환하고, 디코더 $\mathcal{D}$는 이를 다시 픽셀 공간으로 복원합니다($\tilde{x} = \mathcal{D}(z)$). 다운샘플링 배율 $f = H/h = W/w$는 실험에서 $f \in \{4, 8, 16, 32\}$를 비교하며, 논문은 $f = 4$ 또는 $f = 8$이 품질-효율성 균형에서 최적임을 보입니다.

오토인코더 학습에는 세 가지 손실이 결합됩니다.
- **재구성 손실**: 픽셀 단위 $\ell_1$ 또는 $\ell_2$ 손실
- **지각적 손실(Perceptual Loss)**: VGG 기반 특징 공간 손실로 블러 현상을 방지
- **패치 기반 적대적 손실**: PatchGAN discriminator로 고주파 세부 정보 보존

KL-AE의 경우 잠재 공간의 분산을 억제하는 약한 KL 규제가 추가됩니다($\lambda_{\text{KL}} \approx 10^{-6}$).

오토인코더의 재구성 품질은 다음 예시에서 확인할 수 있습니다. 원본 이미지(배경)와 잠재 공간을 거쳐 복원된 이미지(확대 영역)를 비교하면, $f=8$ 압축에서도 세밀한 디테일이 잘 보존됨을 알 수 있습니다.

![오토인코더 재구성 품질 - 원본과 복원 비교](figures/fig_1_1.jpg)
![오토인코더 재구성 품질 - 원본과 복원 비교 (얼굴)](figures/fig_1_5.jpg)
*Figure 1: LDM 오토인코더의 재구성 품질 — 원본(배경)과 잠재 공간 복원(확대 영역) 비교. 접시의 질감, 색상 그라데이션과 얼굴의 피부 디테일, 눈동자 등 고주파 정보가 정밀하게 보존된다. (Rombach et al., 2022)*

**2단계: 잠재 공간에서 LDM 학습**

1단계에서 학습된 인코더 $\mathcal{E}$를 고정하고, 잠재 공간에서 DDPM과 동일한 확산 과정을 학습합니다. 잠재 표현 $z$는 픽셀 공간 $x$보다 훨씬 작으므로(예: 512x512 -> 64x64x4) 계산 효율이 대폭 향상됩니다.

다음 그림은 LDM의 전체 아키텍처를 보여줍니다. 왼쪽의 오토인코더가 픽셀 공간을 잠재 공간으로 압축하고, 중앙의 U-Net이 잠재 공간에서 확산 과정을 수행하며, 오른쪽의 Cross-Attention 메커니즘이 텍스트 등 다양한 조건 신호를 통합합니다.

![LDM 전체 아키텍처](figures/fig_3.png)
*LDM 아키텍처 개요. 인코더 E가 이미지를 잠재 공간으로 압축한 뒤, 확산 모델이 잠재 공간에서 노이즈 제거를 학습한다. Cross-Attention을 통해 텍스트, 의미 맵 등 다양한 조건을 통합할 수 있다.*

### LDM 손실 함수

잠재 공간에서의 확산 목표는 DDPM의 노이즈 예측 목표를 그대로 채택하되, 입력이 픽셀 $x$ 대신 잠재 벡터 $z = \mathcal{E}(x)$임이 다릅니다:

$$L_{LDM} = \mathbb{E}_{\mathcal{E}(x), \epsilon\sim\mathcal{N}(0,1), t}\left[\|\epsilon - \epsilon_\theta(z_t, t, \tau_\theta(y))\|^2_2\right]$$

각 항의 의미는 다음과 같습니다.
- $\mathcal{E}(x)$: 고정된 인코더로 픽셀을 잠재 표현으로 변환
- $z_t = \sqrt{\bar{\alpha}_t}\mathcal{E}(x) + \sqrt{1-\bar{\alpha}_t}\epsilon$: 타임스텝 $t$에서의 노이즈된 잠재 벡터
- $\epsilon_\theta$: 잠재 공간에서 동작하는 U-Net (노이즈 예측)
- $\tau_\theta(y)$: 조건 신호 $y$(텍스트, 클래스 등)를 처리하는 도메인별 인코더

조건이 없는 경우($y = \varnothing$)에는 $\tau_\theta$ 없이 표준 DDPM 손실과 동일합니다.

### Cross-Attention 기반 조건부 생성

LDM의 또 다른 핵심 기여는 Cross-Attention 메커니즘을 통한 유연한 조건부 생성입니다. 텍스트, 의미 맵, 클래스 레이블 등 다양한 모달리티의 조건 신호를 U-Net에 통합할 수 있습니다.

U-Net의 중간 특징 $\varphi_i(z_t) \in \mathbb{R}^{N \times d_\epsilon^i}$와 조건 신호의 인코딩 $\tau_\theta(y) \in \mathbb{R}^{M \times d_\tau}$ 사이에 Cross-Attention을 적용합니다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d}}\right)V$$

$$Q = W_Q^{(i)}\varphi_i(z_t), \quad K = W_K^{(i)}\tau_\theta(y), \quad V = W_V^{(i)}\tau_\theta(y)$$

$W_Q^{(i)} \in \mathbb{R}^{d \times d_\epsilon^i}$, $W_K^{(i)}, W_V^{(i)} \in \mathbb{R}^{d \times d_\tau}$는 학습 가능한 선형 투영 행렬입니다. 쿼리는 잠재 특징으로부터, 키와 값은 조건 신호로부터 만들어지므로 U-Net이 조건 신호의 어느 부분에 집중할지 스스로 학습합니다.

텍스트 조건의 경우 $\tau_\theta$로 BERT나 CLIP 텍스트 인코더를 사용하며, 각 U-Net 레이어에 Cross-Attention 레이어가 추가됩니다. 이로써 LDM은 단일 아키텍처로 텍스트-이미지 생성, 레이아웃-이미지 생성, 의미 맵 기반 이미지 합성, 클래스 조건 생성을 모두 수행할 수 있습니다.

## 방법론

### 잠재 공간 설계: VQ vs. KL 정규화

논문은 두 가지 정규화 방법을 비교합니다.

**VQ-regularization (VQ-VAE)**: 잠재 공간을 이산(discrete) 코드북으로 양자화합니다. 잠재 표현이 코드북 벡터의 인덱스 시퀀스가 되며, VQGAN(Esser et al., 2021)이 이 방식의 대표적 구현입니다.

**KL-regularization**: 연속(continuous) 잠재 공간을 표준 정규 분포에 가깝게 유도하는 약한 KL 패널티를 적용합니다. 잠재 표현이 연속 벡터가 되며, 실험 결과 KL-regularized 모델이 재구성 품질과 FID 균형에서 우수한 성능을 보입니다. Stable Diffusion에서는 KL-AE (다운샘플링 $f=8$)가 채택됩니다.

### 다운샘플링 배율 선택

| 배율 $f$ | 잠재 크기 (512 입력 기준) | 계산 효율 | 재구성 품질 |
|---------|----------------------|---------|----------|
| $f=4$ | 128x128x3 | 보통 | 매우 높음 |
| $f=8$ | 64x64x4 | 높음 | 높음 |
| $f=16$ | 32x32x4 | 매우 높음 | 보통 |
| $f=32$ | 16x16x4 | 극대 | 낮음 |

너무 큰 배율은 오토인코더에 과도한 부담을 주어 재구성 손실이 증가하고 생성 품질이 저하됩니다. 논문은 $f=4$ (고품질 우선) 또는 $f=8$ (효율 우선)을 권장합니다.

다운샘플링 배율에 따른 학습 효율 차이는 아래 그래프에서 명확하게 확인할 수 있습니다. 픽셀 공간 모델(LDM-1)은 동일 학습 스텝에서 가장 느린 수렴을 보이며, LDM-32처럼 과도한 압축은 FID 하한이 높아 품질에 한계가 있습니다. LDM-4와 LDM-8이 수렴 속도와 최종 품질 모두에서 최적의 균형을 달성합니다.

![다운샘플링 배율별 FID 수렴 곡선](figures/fig_6_1.jpg)
*다운샘플링 배율 f에 따른 FID vs. 학습 스텝 비교 (ImageNet 256x256). LDM-1(픽셀 공간)은 수렴이 느리고, LDM-32는 과도한 압축으로 품질이 제한된다. LDM-4~8이 최적의 균형점이다.*

### U-Net 아키텍처

잠재 공간용 U-Net은 기존 확산 U-Net을 기반으로 하되 Cross-Attention 레이어가 추가됩니다.

- **ResBlock**: 각 해상도 레벨에서의 기본 블록, 타임스텝 임베딩을 AdaGN 방식으로 주입
- **Self-Attention**: 공간 해상도가 낮은 레이어에 적용 (메모리 절약)
- **Cross-Attention**: 각 Transformer 블록에 추가, 조건 신호를 처리
- **Transformer Block 구조**: LayerNorm -> Self-Attn -> LayerNorm -> Cross-Attn -> LayerNorm -> FFN
- **타임스텝 임베딩**: Sinusoidal 임베딩 -> MLP -> 각 ResBlock에 주입

| 파라미터 | Stable Diffusion v1 |
|---------|--------------------|
| 오토인코더 압축률 | $f=8$ |
| 잠재 채널 수 | $c=4$ |
| U-Net 파라미터 | ~860M |
| 텍스트 인코더 | CLIP ViT-L/14 |
| 학습 데이터 | LAION-5B |

### Classifier-Free Guidance (CFG)

LDM은 Classifier-Free Guidance(Ho & Salimans, 2022)를 지원합니다. 학습 시 조건 $y$를 일정 확률(논문에서는 10%)로 빈 조건 $\varnothing$으로 대체하여 조건부 모델과 무조건부 모델을 하나의 네트워크로 동시에 학습합니다.

추론 시 다음과 같이 두 예측을 선형 결합합니다:

$$\tilde{\epsilon}_\theta(z_t, y) = \epsilon_\theta(z_t, \varnothing) + s \cdot \left(\epsilon_\theta(z_t, y) - \epsilon_\theta(z_t, \varnothing)\right)$$

가이던스 스케일 $s > 1$로 설정하면 조건에 더 충실한 이미지가 생성되는 대신 다양성이 감소합니다. Stable Diffusion에서는 기본적으로 $s = 7.5$가 사용됩니다.

## 실험 결과

### 무조건부 이미지 생성

**CelebA-HQ 256x256:**

| 모델 | FID ↓ |
|------|-------|
| VQGAN (Esser et al., 2021) | 10.2 |
| LSGM (Vahdat et al., 2021) | 7.22 |
| **LDM-4 (ours)** | **5.11** |

**LSUN-Church 256x256:**

| 모델 | FID ↓ |
|------|-------|
| DALL-E (Ramesh et al., 2021) | 10.4 |
| VQGAN | 14.2 |
| **LDM-8 (ours)** | **4.02** |

다음은 LDM이 다양한 데이터셋에서 생성한 256x256 샘플 예시입니다. CelebA-HQ 얼굴과 LSUN-Church 건축물 모두 높은 사실성과 디테일을 보여줍니다.

![LDM CelebA-HQ 256x256 생성 샘플](figures/fig_4_1.jpg)
![LDM LSUN-Church 256x256 생성 샘플](figures/fig_4_7.jpg)
*Figure 2: LDM으로 생성한 CelebA-HQ(좌)와 LSUN-Church(우) 256x256 샘플 — 잠재 공간에서의 확산만으로도 얼굴의 세밀한 표정과 건축물의 복잡한 구조를 정밀하게 생성한다. (Rombach et al., 2022)*

### 텍스트-이미지 생성 (MS-COCO 256x256)

| 모델 | FID ↓ | CLIP Score ↑ |
|------|-------|-------------|
| DALL-E (zero-shot) | 27.5 | 27.4 |
| GLIDE (Nichol et al., 2022) | 12.24 | — |
| **LDM-KL-8-G (ours)** | **12.63** | **30.5** |

Cross-Attention 메커니즘을 통한 텍스트-이미지 생성의 결과는 인상적입니다. 아래는 사용자 프롬프트로 생성한 예시로, 추상적 개념("Latent Diffusion" 표지판)과 창의적 조합("반은 쥐, 반은 문어")을 정확하게 시각화합니다.

![LDM 텍스트-이미지 생성: Latent Diffusion 표지판](figures/fig_5_1.jpg)
![LDM 텍스트-이미지 생성: 반쥐반문어 합성 동물](figures/fig_5_3.jpg)
*Figure 3: LDM-8(KL)의 텍스트-이미지 생성 샘플 (LAION 학습, CFG $s=10.0$) — "A street sign that reads Latent Diffusion"(좌)과 "A creature that is half mouse half octopus"(우). Cross-Attention이 텍스트의 의미를 정확히 반영한 이미지를 생성한다. (Rombach et al., 2022)*

### 계산 효율성

LDM의 가장 중요한 기여 중 하나는 계산 효율성입니다. 동일한 FID를 달성하기 위한 학습 계산량을 비교하면:

- **ADM (픽셀 공간, 512x512)**: ~1000 V100-days
- **LDM-4 (잠재 공간, 512x512 출력)**: ~160 V100-days — **약 6배 절감**

DDIM 50 스텝으로도 고품질 이미지를 생성할 수 있어, 실질적인 생성 시간은 픽셀 공간 DDPM 대비 수십 배 단축됩니다.

아래 그래프는 다운샘플링 배율별 샘플링 처리량(throughput)과 FID의 관계를 보여줍니다. 각 선의 마커는 DDIM 샘플링 스텝 수(10, 20, 50, 100, 200)를 나타내며, LDM-4~8이 높은 처리량과 낮은 FID를 동시에 달성하는 것을 확인할 수 있습니다.

![FID 대비 샘플링 처리량](figures/fig_9_1.jpg)
*FID vs. 샘플링 처리량 비교 (CelebA-HQ). 각 마커는 DDIM 10~200 스텝에 해당한다. LDM-4~8이 높은 처리량과 낮은 FID를 동시에 달성하며, LDM-1(픽셀 공간)은 처리량이 극도로 낮다.*

### 다양한 조건부 생성 태스크

LDM은 단일 아키텍처로 여러 조건부 생성 태스크를 수행합니다.

- **Text-to-Image**: LAION 데이터셋으로 학습한 Stable Diffusion이 대표 사례
- **Layout-to-Image**: OpenImages 레이아웃 어노테이션으로 조건부 생성
- **Semantic Synthesis**: ADE20K 의미 분할 맵에서 이미지 합성 (FID 17.61)
- **Super-Resolution**: 픽셀 공간 모델 대비 더 디테일한 결과 생성
- **Inpainting**: 마스크된 영역을 자연스럽게 채움 (Places 데이터셋 SOTA)

## 의의 및 한계

### 의의

**Stable Diffusion의 기반**: LDM은 Stability AI의 Stable Diffusion으로 구현되어 공개되었으며, 오픈소스 이미지 생성 AI의 사실상 표준이 되었습니다. SD v1.4/1.5, SDXL, SD v3 등 수많은 파생 모델과 ControlNet, LoRA, DreamBooth 같은 파인튜닝 기법이 모두 LDM 아키텍처를 기반으로 합니다.

**계산 민주화**: 고해상도 이미지 생성을 소비자 GPU(VRAM 8GB)에서도 실행 가능한 수준으로 낮추었습니다. 픽셀 공간 확산 모델은 사실상 연구 기관의 전유물이었지만, LDM 이후 개인 연구자도 고품질 이미지 생성을 실험할 수 있게 되었습니다.

**유연한 조건부 생성**: Cross-Attention 기반 설계는 텍스트, 이미지, 레이아웃, 의미 맵 등 어떤 모달리티의 조건도 통일된 방식으로 통합할 수 있습니다. 이 유연성이 이후 멀티모달 생성 연구의 폭발적 성장을 가능하게 했습니다.

**패러다임 일반화**: 지각 압축과 생성 모델을 분리하는 패러다임은 비디오 생성(Sora, CogVideoX), 오디오 생성, 3D 생성 등 다양한 도메인으로 확산되었습니다.

### 한계

**오토인코더 병목**: 오토인코더의 재구성 품질이 전체 파이프라인의 상한을 결정합니다. 압축 과정에서 손실된 고주파 세부 정보는 아무리 확산 모델이 뛰어나도 복원할 수 없습니다.

**2단계 학습의 복잡성**: 오토인코더와 확산 모델을 별도로 학습해야 하므로 파이프라인이 복잡하고 두 모델이 서로 맞춤화되지 않습니다.

**텍스트 정렬 품질**: 원논문의 BERT 기반 텍스트 인코더는 CLIP 대비 텍스트-이미지 정렬 품질이 낮습니다. Stable Diffusion v2 이후 OpenCLIP으로 교체되었으나, 복잡한 텍스트 프롬프트에서 여전히 한계가 있습니다.

**샘플링 속도**: DDIM 50 스텝으로도 단일 이미지 생성에 수 초가 걸립니다. 이후 Consistency Model, LCM(Latent Consistency Model), SDXL-Turbo 같은 후속 연구가 1~4 스텝 생성을 가능하게 만들었습니다.

## 코드 예제

### Stable Diffusion으로 이미지 생성 (Diffusers 라이브러리)

```python
import torch
import numpy as np
from diffusers import StableDiffusionPipeline, DDIMScheduler
from diffusers import AutoencoderKL, UNet2DConditionModel
from transformers import CLIPTextModel, CLIPTokenizer
from PIL import Image


# === 1. Stable Diffusion 파이프라인으로 이미지 생성 ===
def generate_image_with_sd(
    prompt: str,
    negative_prompt: str = "",
    model_id: str = "runwayml/stable-diffusion-v1-5",
    num_steps: int = 50,
    guidance_scale: float = 7.5,
    seed: int = 42,
) -> Image.Image:
    """Stable Diffusion (LDM 기반)으로 텍스트-이미지 생성.

    핵심 과정:
    1. CLIP 텍스트 인코더: 프롬프트 → 텍스트 임베딩 τ_θ(y)
    2. 잠재 공간 초기화: z_T ~ N(0, I) (64×64×4)
    3. DDIM 역방향 과정: ε_θ(z_t, t, τ_θ(y))로 노이즈 예측
       - CFG: ε̃ = ε_uncond + s·(ε_cond - ε_uncond)
    4. VAE 디코더: z_0 → 픽셀 이미지 (64×64×4 → 512×512×3)
    """
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # 파이프라인 로드 (LDM 아키텍처: VAE + U-Net + CLIP)
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        safety_checker=None,
    ).to(device)

    # DDIM 스케줄러: 1000 스텝 → 50 스텝으로 가속 샘플링
    pipe.scheduler = DDIMScheduler.from_config(pipe.scheduler.config)

    generator = torch.Generator(device=device).manual_seed(seed)

    with torch.autocast(device):
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_steps,
            guidance_scale=guidance_scale,   # CFG 스케일 s
            height=512,
            width=512,
            generator=generator,
        )

    return result.images[0]


# === 2. LDM 오토인코더 직접 사용 (인코딩/디코딩) ===
class LDMAutoEncoder:
    """LDM의 KL-regularized VAE 래퍼 (f=8 압축).

    512×512×3 픽셀  →  64×64×4 잠재 코드 (약 48배 압축)
    """

    SCALE_FACTOR = 0.18215  # SD의 잠재 코드 정규화 상수

    def __init__(self, model_id: str = "stabilityai/stable-diffusion-2", device: str = "cuda"):
        self.device = device
        self.vae = AutoencoderKL.from_pretrained(model_id, subfolder="vae").to(device)
        self.vae.eval()

    @torch.no_grad()
    def encode(self, images: torch.Tensor) -> torch.Tensor:
        """이미지 → 잠재 코드. images: (B, 3, H, W) in [-1, 1]"""
        posterior = self.vae.encode(images.to(self.device)).latent_dist
        # 재파라미터화 트릭: z ~ N(μ, σ²)
        z = posterior.sample() * self.SCALE_FACTOR
        return z  # (B, 4, H/8, W/8)

    @torch.no_grad()
    def decode(self, z: torch.Tensor) -> torch.Tensor:
        """잠재 코드 → 이미지. z: (B, 4, H/8, W/8)"""
        images = self.vae.decode(z / self.SCALE_FACTOR).sample
        return images.clamp(-1, 1)  # (B, 3, H, W)


# === 3. Cross-Attention 핵심 구현 ===
class CrossAttention(torch.nn.Module):
    """LDM U-Net 내부 Cross-Attention.

    Q = W_Q · φ_i(z_t)   (이미지 잠재 특징)
    K = W_K · τ_θ(y)     (조건 인코딩: 텍스트 등)
    V = W_V · τ_θ(y)
    Attention(Q,K,V) = softmax(QKᵀ/√d)·V
    """

    def __init__(self, query_dim: int, context_dim: int, heads: int = 8, dim_head: int = 64):
        super().__init__()
        inner = heads * dim_head
        self.heads = heads
        self.scale = dim_head ** -0.5
        # 쿼리는 이미지 잠재에서, 키·값은 조건 신호에서
        self.to_q = torch.nn.Linear(query_dim, inner, bias=False)
        self.to_k = torch.nn.Linear(context_dim, inner, bias=False)
        self.to_v = torch.nn.Linear(context_dim, inner, bias=False)
        self.to_out = torch.nn.Linear(inner, query_dim)

    def forward(self, x: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        """
        x:       (B, N, query_dim)   — 이미지 공간 토큰
        context: (B, M, context_dim) — 텍스트/조건 토큰
        """
        B, N, _ = x.shape
        h = self.heads

        q = self.to_q(x).reshape(B, N, h, -1).permute(0, 2, 1, 3)          # (B,h,N,d)
        k = self.to_k(context).reshape(B, -1, h, -1).permute(0, 2, 1, 3)   # (B,h,M,d)
        v = self.to_v(context).reshape(B, -1, h, -1).permute(0, 2, 1, 3)   # (B,h,M,d)

        # Attention(Q,K,V) = softmax(QKᵀ/√d)·V
        attn = torch.einsum('bhnd,bhmd->bhnm', q, k) * self.scale
        attn = attn.softmax(dim=-1)                                          # (B,h,N,M)
        out = torch.einsum('bhnm,bhmd->bhnd', attn, v)                      # (B,h,N,d)

        out = out.permute(0, 2, 1, 3).reshape(B, N, -1)
        return self.to_out(out)


# === 사용 예시 ===
if __name__ == "__main__":
    # 이미지 생성
    image = generate_image_with_sd(
        prompt="a serene mountain landscape at sunset, photorealistic, 4k",
        negative_prompt="blurry, low quality, cartoon",
        num_steps=50,
        guidance_scale=7.5,
        seed=42,
    )
    image.save("ldm_output.png")
    print(f"생성된 이미지: {image.size}")

    # 잠재 공간 압축률 확인
    print("\n잠재 공간 압축 비율 (f=8)")
    print(f"  픽셀 공간: 512×512×3 = {512*512*3:,} 차원")
    print(f"  잠재 공간: 64×64×4  = {64*64*4:,} 차원")
    print(f"  압축률: {512*512*3 / (64*64*4):.1f}x")
```

## 관련 문서

- [[ddpm|DDPM: Denoising Diffusion Probabilistic Models]] — LDM의 기반이 되는 확산 모델
- [[ddim|DDIM: Denoising Diffusion Implicit Models]] — LDM 샘플링 가속화에 활용
- [[cfg|Classifier-Free Guidance]] — LDM 조건부 생성의 핵심 기법
- [[controlnet|ControlNet]] — LDM에 공간 조건(자세, 엣지)을 추가하는 후속 연구
- [[sdxl|SDXL: Improving Latent Diffusion Models]] — LDM 아키텍처를 개선한 Stable Diffusion XL
- [[sd3|Stable Diffusion 3]] — Flow Matching으로 발전한 LDM 후속작
- [[dalle-2|DALL-E 2]] — CLIP 기반 계층적 이미지 생성, 동시기 연구
- [[clip|CLIP]] — LDM 텍스트 인코더로 활용되는 멀티모달 표현 학습
