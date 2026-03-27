# Diffusion Models 완전 정복: DDPM에서 Stable Diffusion까지

## 개요

확산 모델(Diffusion Models)은 이미지, 비디오, 오디오 생성에서 혁명적인 성과를 거둔 생성 모델 패러다임입니다. 데이터에 점진적으로 노이즈를 추가하는 순방향 과정(forward process)과, 학습된 신경망으로 노이즈를 제거하는 역방향 과정(reverse process)을 통해 고품질 데이터를 생성합니다.

GAN이 지배하던 이미지 생성 분야에서 DDPM이 GAN을 능가한 이후, Stable Diffusion, DALL-E, Midjourney, Sora 등 현대 생성 AI의 근간이 되었습니다. 이 가이드는 확산 모델의 **수학적 기초부터 최신 응용까지** 전체 발전 흐름을 체계적으로 정리합니다.

### 왜 확산 모델을 공부해야 하는가?

확산 모델은 단순히 이미지 생성 도구가 아닙니다. Score Matching, SDE, Flow Matching 등 깊은 수학적 기초 위에 세워져 있으며, 최근에는 텍스트 생성, 분자 설계, 로봇 제어 등 다양한 영역으로 확장되고 있습니다. 기초 이론을 탄탄히 이해하면 응용의 폭이 크게 넓어집니다.

---

## 핵심 흐름: Diffusion 기술 발전 타임라인

### Phase 1: 이론적 기초 (2011-2019)

확산 모델의 수학적 토대가 마련된 시기입니다.

**Score Matching과 확산 과정의 연결**

- **2011**: [Score Matching](/post/score-matching) ( 데이터의 Score Function(∇log p(x))을 직접 추정하는 기법. Denoising Score Matching이 실용적 학습 방법을 제공.
- **2015**: Deep Unsupervised Learning using Nonequilibrium Thermodynamics ) 확산 과정을 생성 모델로 처음 제안. 비평형 열역학에서 영감.
- **2019**: Noise Conditional Score Networks (NCSN) ( 다양한 노이즈 수준에서 Score Matching을 적용하여 고해상도 이미지 생성.

### Phase 2: 확산 모델의 실용화 (2020-2021)

DDPM이 GAN을 능가하면서 확산 모델이 주류 생성 모델로 자리잡았습니다.

**핵심 모델들**

- [DDPM](/post/ddpm) (2020): 확산 확률 모델의 실용화. 가우시안 노이즈 추가/제거 과정을 간단한 목적함수로 학습. CIFAR-10 FID 3.17로 GAN 능가.
- [DDIM](/post/ddim) (2020): DDPM의 결정론적 샘플링 변형. 스텝 수를 크게 줄여 생성 속도 향상. DDPM 대비 10-50배 빠른 샘플링.
- [Score-SDE](/post/score-sde) (2020): Score Matching과 확산 모델을 SDE(확률적 미분방정식) 프레임워크로 통합. 연속 시간 확산 과정의 이론적 기초.
- [D3PM](/post/d3pm) (2021): 이산(discrete) 데이터를 위한 확산 모델. 텍스트, 이미지 세그멘테이션 등에 적용.
- [VDM](/post/vdm) (2021): Variational Diffusion Models. 노이즈 스케줄을 학습 가능한 파라미터로 설정.

**Guidance 기법**

- [Classifier Guidance](/post/classifier-guidance) (2021): 별도 분류기의 기울기를 사용하여 조건부 생성 품질 향상.
- [Classifier-Free Guidance (CFG)](/post/cfg) (2022): 분류기 없이 조건부/무조건부 생성을 결합. 대부분의 현대 확산 모델이 채택.

### Phase 3: Latent Diffusion과 상용화 (2022-2023)

픽셀 공간에서 잠재 공간으로의 전환이 확산 모델의 실용적 상용화를 가능하게 했습니다.

**이미지 생성의 혁명**

- [LDM (Latent Diffusion Models)](/post/ldm) (2022): VAE로 이미지를 잠재 공간으로 압축한 뒤 확산 과정 수행. 연산 비용 대폭 절감. Stable Diffusion의 기반.
- [GLIDE](/post/glide) (2022): 텍스트 조건부 이미지 생성. Classifier-Free Guidance 적용.
- [DALL-E 2](/post/dalle-2) (2022): CLIP 임베딩 기반 이미지 생성. Prior + Decoder 구조.
- [Imagen](/post/imagen) (2022): 대형 언어 모델(T5)을 텍스트 인코더로 활용. 초고해상도 이미지 생성.
- [ControlNet](/post/controlnet) (2023): 사전학습된 확산 모델에 공간적 조건(edge, depth, pose 등)을 추가. 정밀한 이미지 제어.
- [SDXL](/post/sdxl) (2023): Stable Diffusion의 대폭 확장. 고해상도, 더 정확한 텍스트 반영.
- [DALL-E 3](/post/dalle-3) (2023): 개선된 캡션 생성으로 텍스트-이미지 정합성 대폭 향상.
- [PixArt-α](/post/pixart-alpha) (2023): DiT(Diffusion Transformer) 기반. 효율적 학습.

**가속화와 효율화**

- [EDM](/post/edm) (2022): Elucidating the Design Space. 확산 모델의 설계 공간을 체계적으로 분석하고 최적 구성 도출.
- [Consistency Model](/post/consistency-model) (2023): 한 스텝만에 고품질 이미지 생성. Diffusion 과정의 자기일관성(self-consistency) 활용.
- [DiT](/post/dit) (2023): U-Net을 Transformer로 대체. 스케일링에 유리한 아키텍처.

### Phase 4: Flow Matching과 차세대 (2024-현재)

Flow Matching 패러다임의 부상과 비디오/3D 생성으로의 확장이 이 시기의 특징입니다.

**Flow Matching 패러다임**

- [Rectified Flow](/post/rectified-flow) (2022): 직선 경로를 따르는 ODE 기반 생성. 노이즈에서 데이터까지 최단 경로.
- [Flow Matching](/post/flow-matching) (2023): 확산 모델을 연속 정규화 흐름(CNF)으로 재해석. 더 단순한 학습 목적함수.
- [SD3 (Stable Diffusion 3)](/post/sd3) (2024): MMDiT(Multi-Modal DiT) 아키텍처. Flow Matching 기반.
- [FLUX](/post/flux) (2024): Black Forest Labs의 Flow Matching 기반 모델. SD 창시자팀의 새 프로젝트.
- [FLUX.2](/post/flux-2) (2025): Ultra 모드로 고해상도 생성 능력 확장.

**비디오 생성**

- [CogVideoX](/post/cogvideox) (2024): 3D VAE + Expert Transformer 기반 비디오 생성.
- [HunyuanVideo](/post/hunyuanvideo) (2024): Tencent의 오픈소스 비디오 생성 모델.
- [Sora](/post/sora) (2024): OpenAI의 비디오 생성 모델. 시간적 일관성과 물리 시뮬레이션.
- [Sora 2](/post/sora-2) (2025): 개선된 비디오 생성 품질과 제어.
- [Kling](/post/kling) (2024): Kuaishou의 비디오 생성 모델.
- [Kling 3](/post/kling-3) (2025): 향상된 비디오 품질.
- [Veo](/post/veo) (2024): Google DeepMind의 비디오 생성.
- [Veo 3](/post/veo-3) (2025): 네이티브 오디오 통합 비디오 생성.
- [Runway Gen-4](/post/runway-gen4) (2025): World Model 기반 비디오 생성.

**텍스트 확산 모델**

- [Diffusion-LM](/post/diffusion-lm) (2022): 연속 확산 모델을 텍스트 생성에 적용. 제어 가능한 텍스트 생성.
- [DiffuSeq](/post/diffu-seq) (2022): Sequence-to-Sequence 태스크용 확산 모델.
- [MDLM](/post/mdlm) (2024): Masked Discrete Language Models. 이산 확산으로 언어 모델링.
- [SEDD](/post/sedd) (2024): Score Entropy Discrete Diffusion. 이산 데이터의 Score Matching.
- [BD3LM](/post/bd3lm) (2024): Block Discrete Denoising Diffusion Language Model.
- [DLLM](/post/dllm) (2024): Discrete Latent Language Model.
- [AR-Diffusion](/post/ar-diffusion) (2024): 자기회귀와 확산의 결합.
- [LLaDA](/post/llada) (2024): Large Language Diffusion with Masking.
- [TiDAR](/post/tidar-think-in-diffusion-talk-in-autoregression) (2025): Think in Diffusion, Talk in Autoregression.

---

## 주요 Diffusion 모델 요약 테이블

| 모델 | 연도 | 유형 | 핵심 기여 | 응용 |
|------|------|------|----------|------|
| [Score Matching](/post/score-matching) | 2011 | 이론 | Score Function 추정 | 기초 |
| [DDPM](/post/ddpm) | 2020 | 기초 | 확산 모델 실용화 | 이미지 |
| [DDIM](/post/ddim) | 2020 | 가속 | 결정론적 빠른 샘플링 | 이미지 |
| [Score-SDE](/post/score-sde) | 2020 | 이론 | SDE 통합 프레임워크 | 이론 |
| [Classifier Guidance](/post/classifier-guidance) | 2021 | 기법 | 분류기 기반 조건부 생성 | 이미지 |
| [CFG](/post/cfg) | 2022 | 기법 | 분류기 없는 가이던스 | 이미지 |
| [LDM](/post/ldm) | 2022 | 아키텍처 | 잠재 공간 확산 | 이미지 |
| [DALL-E 2](/post/dalle-2) | 2022 | 응용 | CLIP + 확산 | 이미지 |
| [Imagen](/post/imagen) | 2022 | 응용 | T5 텍스트 인코더 | 이미지 |
| [EDM](/post/edm) | 2022 | 분석 | 설계 공간 최적화 | 이미지 |
| [ControlNet](/post/controlnet) | 2023 | 제어 | 공간 조건 추가 | 이미지 |
| [SDXL](/post/sdxl) | 2023 | 응용 | 고해상도 SD | 이미지 |
| [Consistency Model](/post/consistency-model) | 2023 | 가속 | 단일 스텝 생성 | 이미지 |
| [DiT](/post/dit) | 2023 | 아키텍처 | Transformer 기반 확산 | 이미지 |
| [Flow Matching](/post/flow-matching) | 2023 | 이론 | CNF 학습 단순화 | 이론 |
| [SD3](/post/sd3) | 2024 | 아키텍처 | MMDiT + Flow Matching | 이미지 |
| [FLUX](/post/flux) | 2024 | 아키텍처 | Flow 기반 고품질 생성 | 이미지 |
| [Sora](/post/sora) | 2024 | 응용 | 비디오 생성 | 비디오 |

---

## Diffusion 모델의 핵심 개념

### 1. 수학적 기초

확산 모델은 세 가지 수학적 관점에서 이해할 수 있습니다.

- **확률적 관점**: [DDPM](/post/ddpm) ) 마르코프 체인으로 노이즈 추가/제거
- **Score 관점**: [Score Matching](/post/score-matching), [Score-SDE](/post/score-sde) ( Score Function 추정
- **Flow 관점**: [Flow Matching](/post/flow-matching), [Rectified Flow](/post/rectified-flow) ) 연속 정규화 흐름

#### 순방향 과정 (Forward Process) 직관적 이해

순방향 과정은 "깨끗한 데이터에 점진적으로 노이즈를 추가하여 완전한 가우시안 노이즈로 변환하는 과정"입니다. 직관적으로, 선명한 사진에 반복적으로 TV 화면의 정적(static) 노이즈를 섞는 것과 같습니다.

수학적으로, 시각 $t$에서의 노이즈 추가는 다음과 같이 정의됩니다:

$$q(x_t | x_{t-1}) = \mathcal{N}(x_t; \sqrt{1-\beta_t} \cdot x_{t-1},\ \beta_t \mathbf{I})$$

여기서 $\beta_t$는 노이즈 스케줄로, 각 스텝에서 추가되는 노이즈의 양을 결정합니다. 핵심적인 성질은 임의의 시각 $t$에서의 노이즈 샘플을 **한 번에** 계산할 수 있다는 점입니다:

$$q(x_t | x_0) = \mathcal{N}(x_t; \sqrt{\bar{\alpha}_t} \cdot x_0,\ (1-\bar{\alpha}_t) \mathbf{I})$$

여기서 $\bar{\alpha}_t = \prod_{s=1}^{t}(1-\beta_s)$입니다. 이 성질 덕분에 학습 시 중간 스텝을 모두 계산할 필요 없이, 임의의 $t$에 대한 노이즈 샘플을 즉시 생성할 수 있어 효율적입니다.

:::info
$\bar{\alpha}_t$가 0에 가까워질수록 원본 데이터의 정보가 사라지고 순수 가우시안 노이즈에 가까워집니다. DDPM은 $T=1000$에서 $\bar{\alpha}_T \approx 0$이 되도록 스케줄을 설계합니다.
:::

#### 역방향 과정 (Reverse Process) 직관적 이해

역방향 과정은 "노이즈에서 데이터를 복원하는 과정"으로, 신경망이 각 시각에서 추가된 노이즈를 예측하여 제거합니다. 직관적으로, TV 정적 노이즈에서 시작하여 한 프레임씩 선명하게 만들어가는 과정입니다.

역방향 과정의 수학적 표현은 다음과 같습니다:

$$p_\theta(x_{t-1} | x_t) = \mathcal{N}(x_{t-1};\ \mu_\theta(x_t, t),\ \sigma_t^2 \mathbf{I})$$

핵심은 $\mu_\theta$를 어떻게 매개변수화하느냐입니다. DDPM은 노이즈 $\epsilon$을 예측하는 방식을 채택합니다:

$$\mu_\theta(x_t, t) = \frac{1}{\sqrt{\alpha_t}} \left(x_t - \frac{\beta_t}{\sqrt{1-\bar{\alpha}_t}} \epsilon_\theta(x_t, t)\right)$$

학습 목적함수는 단순한 MSE로 귀결됩니다:

$$\mathcal{L}_{\text{simple}} = \mathbb{E}_{t, x_0, \epsilon} \left[\|\epsilon - \epsilon_\theta(\sqrt{\bar{\alpha}_t} x_0 + \sqrt{1-\bar{\alpha}_t}\epsilon,\ t)\|^2\right]$$

### 2. DDPM에서 DDIM으로: 결정론적 샘플링의 등장

[DDPM](/post/ddpm)의 가장 큰 실용적 문제는 1000스텝의 순차적 샘플링이 필요하다는 점이었습니다. [DDIM](/post/ddim)은 이 문제를 해결하기 위해 핵심적인 관찰을 합니다: **DDPM의 학습 목적함수는 마르코프 가정 없이도 유효하다.**

DDIM은 비마르코프(non-Markovian) 순방향 과정을 정의하여, 역방향 샘플링을 **결정론적(deterministic)** ODE로 변환합니다:

$$x_{t-1} = \sqrt{\bar{\alpha}_{t-1}} \cdot \hat{x}_0(x_t, t) + \sqrt{1-\bar{\alpha}_{t-1}} \cdot \epsilon_\theta(x_t, t)$$

여기서 $\hat{x}_0 = \frac{x_t - \sqrt{1-\bar{\alpha}_t} \cdot \epsilon_\theta(x_t, t)}{\sqrt{\bar{\alpha}_t}}$는 현재 노이즈 예측으로부터 복원한 원본 추정값입니다.

이 결정론적 매핑의 핵심 이점은 다음과 같습니다:

| 특성 | DDPM | DDIM |
|------|------|------|
| 샘플링 스텝 | 1000 | 10-50 |
| 결정론적 | 아니오 (확률적) | 예 |
| 인코딩 가능 | 아니오 | 예 (잠재 공간 매핑) |
| 보간 가능 | 제한적 | 잠재 공간에서 가능 |
| 생성 품질 | 높음 | 스텝 수에 의존 |

### 3. Score-SDE: 연속 시간 통합 프레임워크

[Score-SDE](/post/score-sde)는 DDPM과 Score Matching을 **확률적 미분방정식(SDE)** 프레임워크로 통합합니다:

$$dx = f(x, t)dt + g(t)dw \quad \text{(순방향 SDE)}$$

$$dx = [f(x, t) - g(t)^2 \nabla_x \log p_t(x)]dt + g(t)d\bar{w} \quad \text{(역방향 SDE)}$$

이 프레임워크에서 DDPM은 Variance Preserving SDE의 이산화에 해당하고, Score Matching은 $\nabla_x \log p_t(x)$를 학습하는 것에 해당합니다. 또한 역방향 SDE에 대응하는 **확률 흐름 ODE(Probability Flow ODE)**도 존재하며, 이것이 DDIM의 이론적 근거가 됩니다.

### 4. LDM: 잠재 공간으로의 전환

[LDM](/post/ldm)(Latent Diffusion Model)은 확산 모델의 실용적 상용화를 가능하게 한 결정적 전환점입니다. 핵심 아이디어는 **픽셀 공간 대신 VAE의 잠재 공간에서 확산을 수행**하는 것입니다:

1. **인코딩**: 이미지 $x \in \mathbb{R}^{H \times W \times 3}$을 VAE 인코더로 잠재 벡터 $z \in \mathbb{R}^{h \times w \times c}$로 압축 (보통 8배 다운샘플)
2. **확산**: 잠재 공간에서 DDPM/DDIM 수행
3. **디코딩**: 생성된 잠재 벡터를 VAE 디코더로 이미지로 복원

| 비교 | 픽셀 확산 (DDPM) | 잠재 확산 (LDM) |
|------|-----------------|----------------|
| 입력 차원 | 256×256×3 = 196,608 | 32×32×4 = 4,096 |
| 연산 비용 | 매우 높음 | ~48배 절감 |
| 해상도 | 256×256 제한적 | 512×512+ 실용적 |
| 텍스트 조건 | 직접 처리 | Cross-Attention으로 결합 |

LDM의 성공은 Stable Diffusion으로 이어졌고, 이후 SDXL, SD3 등 모든 상업적 확산 모델의 표준 아키텍처가 되었습니다.

### 5. Flow Matching: 더 단순한 학습 패러다임

[Flow Matching](/post/flow-matching)은 확산 모델을 **연속 정규화 흐름(Continuous Normalizing Flow, CNF)**으로 재해석합니다. SDE 대신 ODE만을 사용하며, 학습 목적함수가 더 단순합니다:

$$\mathcal{L}_{FM} = \mathbb{E}_{t, x_0, x_1} \left[\|v_\theta(x_t, t) - (x_1 - x_0)\|^2\right]$$

여기서 $x_t = (1-t) \cdot x_0 + t \cdot x_1$로, 노이즈($x_0$)에서 데이터($x_1$)까지의 **직선 경로**를 따릅니다. [Rectified Flow](/post/rectified-flow)는 이 직선 경로를 더욱 최적화하여 적은 스텝으로 고품질 생성을 가능하게 합니다.

Flow Matching의 장점은 다음과 같습니다:

- **단순한 목적함수**: 속도장(velocity field)을 직접 회귀
- **유연한 경로 설계**: 직선, 곡선 등 다양한 보간 경로 가능
- **안정적 학습**: 분산이 낮아 학습이 빠르고 안정적
- **ODE 기반**: 확률적 노이즈 없이 결정론적 생성

[SD3](/post/sd3)와 [FLUX](/post/flux)는 Flow Matching을 채택한 대표적 상용 모델입니다.

### 6. 아키텍처 진화

- **U-Net 시대**: DDPM ~ Stable Diffusion. U-Net + Cross-Attention
- **DiT 시대**: [DiT](/post/dit), [SD3](/post/sd3), [FLUX](/post/flux). Transformer 기반. 스케일링에 유리
- **하이브리드**: 비디오 모델(Sora 등)은 3D 구조와 Transformer 결합

U-Net에서 DiT로의 전환은 Vision Transformer의 성공에 영감을 받았습니다. DiT는 이미지 패치를 토큰으로 취급하고, 타임스텝과 클래스 조건을 Adaptive Layer Norm(adaLN)으로 주입합니다. 이 설계는 모델 크기를 키울수록 성능이 일관되게 향상되는 **스케일링 법칙**을 확산 모델에 가져왔습니다.

### 7. 조건부 생성의 발전

- **무조건부** → **분류기 기반** ([Classifier Guidance](/post/classifier-guidance)) → **분류기-없는** ([CFG](/post/cfg)) → **정밀 제어** ([ControlNet](/post/controlnet))

CFG의 수식은 다음과 같습니다:

$$\tilde{\epsilon}_\theta = \epsilon_\theta(x_t, \emptyset) + s \cdot (\epsilon_\theta(x_t, c) - \epsilon_\theta(x_t, \emptyset))$$

가이던스 스케일 $s$가 1보다 클수록 조건에 더 충실한 생성이 이루어지며, 대부분의 상용 모델은 $s = 7.5$ 전후를 기본값으로 사용합니다.

### 8. 샘플링 가속

- **많은 스텝**: DDPM (1000 스텝)
- **적은 스텝**: [DDIM](/post/ddim) (10-50 스텝)
- **단일 스텝**: [Consistency Model](/post/consistency-model) (1 스텝)
- **Flow 기반**: [Rectified Flow](/post/rectified-flow) (직선 경로, 적은 스텝)

:::tip
실무에서 가장 널리 사용되는 샘플러는 **DPM-Solver++**(20-25 스텝)와 **Euler**(25-50 스텝)입니다. Consistency Model은 1스텝 생성이 가능하지만, 다중 스텝에서의 품질은 아직 기존 방법에 미치지 못합니다.
:::

---

## 추천 학습 경로

### 초심자 (확산 모델 입문)

수학적 기초와 핵심 모델을 이해합니다.

1. [DDPM](/post/ddpm) ( 확산 모델의 기본 원리 (순방향/역방향 과정)
2. [DDIM](/post/ddim) ) 결정론적 샘플링의 이해
3. [CFG](/post/cfg) ( 조건부 생성의 핵심
4. [LDM](/post/ldm) ) Latent Diffusion과 Stable Diffusion의 원리
5. [Diffusion 열역학 배경](/post/diffusion-thermo) ( 열역학적 관점

### 중급 (이론 심화)

수학적 기초를 깊이 이해하고 다양한 변형을 학습합니다.

1. [Score Matching](/post/score-matching) ) Score Function 추정 이론
2. [Score-SDE](/post/score-sde) ( SDE 프레임워크
3. [EDM](/post/edm) ) 설계 공간 분석
4. [Classifier Guidance](/post/classifier-guidance) → [CFG](/post/cfg) ( 가이던스 기법
5. [Flow Matching](/post/flow-matching) + [Rectified Flow](/post/rectified-flow) ) Flow 기반 접근
6. [Consistency Model](/post/consistency-model) ( 가속화 기법
7. [D3PM](/post/d3pm) + [SEDD](/post/sedd) ) 이산 확산 모델

### 고급 (최신 연구)

최신 아키텍처와 응용을 추적합니다.

1. [DiT](/post/dit) → [SD3](/post/sd3) → [FLUX](/post/flux) ( Transformer 기반 확산
2. [Sora](/post/sora) + [CogVideoX](/post/cogvideox) ) 비디오 생성
3. [MDLM](/post/mdlm) + [SEDD](/post/sedd) + [BD3LM](/post/bd3lm) ( 텍스트 확산 모델
4. [ControlNet](/post/controlnet) ) 정밀 제어
5. [TiDAR](/post/tidar-think-in-diffusion-talk-in-autoregression) ( 확산과 자기회귀 결합

---

## 관련 카테고리

- [AI/ML 아키텍처 로드맵](/post/ai-ml-architecture-roadmap) ) 전체 AI/ML 지형도
- [컴퓨터 비전 딥러닝 로드맵](/post/computer-vision-dl-roadmap) ( 비전 모델과의 연결
- [AI 핵심 기법 총정리](/post/ai-core-techniques-guide) ) 확산 모델에 사용되는 기법들
