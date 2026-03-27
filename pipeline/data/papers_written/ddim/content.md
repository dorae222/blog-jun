## 개요

DDIM(Denoising Diffusion Implicit Models)은 Song et al.이 ICLR 2021에서 발표한 논문으로, DDPM의 느린 샘플링 문제를 근본적으로 해결한다. DDPM은 고품질 이미지를 생성하지만 역방향 샘플링에 1000 스텝이 필요해 실용성이 크게 제한된다. DDIM은 마르코프 제약을 제거한 새로운 확산 프로세스 계열을 정의함으로써, **동일하게 학습된 모델을 재사용**하면서도 50 스텝 내외의 결정론적 샘플링으로 유사한 품질을 달성한다.

이 논문이 제시하는 두 가지 핵심 기여는 다음과 같다. 첫째, 마르코프 가정 없이도 DDPM과 동일한 학습 목적함수를 사용할 수 있는 비마르코프 확산 프로세스의 이론적 체계를 확립했다. 둘째, $\sigma_t = 0$ 으로 설정하면 완전 결정론적 ODE 궤적을 따르는 샘플러를 구성할 수 있어, 동일 잠재 변수에서 항상 동일 이미지가 생성되는 재현 가능성과 DDIM Inversion을 통한 이미지 편집이 가능해진다.

## 배경 및 문제

DDPM과 DDIM의 근본적인 차이는 다음 그래피컬 모델에서 확인할 수 있다. DDPM은 마르코프 체인(왼쪽)으로 각 잠재 변수가 직전 상태에만 의존하지만, DDIM의 비마르코프 모델(오른쪽)은 $\mathbf{x}_0$ 에 대한 직접적 의존성을 도입하여 스텝을 유연하게 건너뛸 수 있는 구조를 가진다.

![DDPM의 마르코프 확산 그래피컬 모델](figures/fig_1_1.png)
![DDIM의 비마르코프 확산 그래피컬 모델](figures/fig_1_2.png)
*Figure 1: 마르코프 확산 모델(위)과 비마르코프 추론 모델(아래)의 그래피컬 모델 비교 ( 비마르코프 모델은 $q(\mathbf{x}_{t-1}|\mathbf{x}_t, \mathbf{x}_0)$ 형태로 $\mathbf{x}_0$ 에 직접 조건화한다. (Song et al., 2021)*

DDPM은 가우시안 마르코프 체인을 순방향 프로세스로 사용한다. 시간 $t$ 에서의 잠재 변수 $\mathbf{x}_t$ 는 이전 상태 $\mathbf{x}_{t-1}$ 에만 의존하며, 이 마르코프 구조 덕분에 임의 시각의 주변 분포를 닫힌 형태로 표현할 수 있다:

$$q(\mathbf{x}_t|\mathbf{x}_0) = \mathcal{N}\!\left(\sqrt{\bar{\alpha}_t}\,\mathbf{x}_0,\,(1-\bar{\alpha}_t)\mathbf{I}\right)$$

여기서 $\bar{\alpha}_t = \prod_{s=1}^{t}(1 - \beta_s)$ 이다. 이 표현 덕분에 학습 목적함수 $L_{\text{simple}} = \mathbb{E}_{\mathbf{x}_0,\,\boldsymbol{\epsilon},\,t}\left[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)\|^2\right]$ 를 간결하게 유도할 수 있다.

그러나 역방향 생성 과정은 매 스텝마다 모델 $\boldsymbol{\epsilon}_\theta$ 를 호출해야 하므로, $T=1000$ 인 DDPM은 단일 이미지 생성에 수십 초가 소요된다. GAN 대비 수백 배 느린 속도는 실시간 응용이나 대규모 생성에 심각한 병목이 된다. 스텝을 단순히 건너뛰면 마르코프 가정이 깨져 FID가 37 이상으로 급락한다는 것이 실험으로 확인된다.

## 핵심 아이디어

DDIM의 핵심 통찰은 **학습 목적함수가 주변 분포 $q(\mathbf{x}_t|\mathbf{x}_0)$ 에만 의존한다**는 점이다. 즉, 이 주변 분포를 보존하는 한 순방향 프로세스의 전이 분포(transition distribution)는 자유롭게 재설계할 수 있다. 이를 통해 마르코프가 아닌 순방향 프로세스 계열을 새롭게 정의한다:

$$q_\sigma(\mathbf{x}_{1:T}|\mathbf{x}_0) = q_\sigma(\mathbf{x}_T|\mathbf{x}_0)\prod_{t=2}^{T} q_\sigma(\mathbf{x}_{t-1}|\mathbf{x}_t, \mathbf{x}_0)$$

각 역전이는 다음과 같이 정의되며:

$$q_\sigma(\mathbf{x}_{t-1}|\mathbf{x}_t, \mathbf{x}_0) = \mathcal{N}\!\left(\sqrt{\bar{\alpha}_{t-1}}\,\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_{t-1}-\sigma_t^2}\cdot\frac{\mathbf{x}_t - \sqrt{\bar{\alpha}_t}\,\mathbf{x}_0}{\sqrt{1-\bar{\alpha}_t}},\;\sigma_t^2\mathbf{I}\right)$$

$\sigma_t \geq 0$ 은 각 스텝의 확률성(stochasticity)을 조절하는 파라미터로, 이를 통해 DDPM부터 완전 결정론적 샘플러까지 연속적인 스펙트럼을 구성할 수 있다.

이 정의가 올바른 주변 분포 $q_\sigma(\mathbf{x}_t|\mathbf{x}_0) = \mathcal{N}(\sqrt{\bar{\alpha}_t}\mathbf{x}_0, (1-\bar{\alpha}_t)\mathbf{I})$ 를 유지하는지 귀납법으로 검증할 수 있다. 이로써 DDPM으로 학습된 $\boldsymbol{\epsilon}_\theta$ 를 재학습 없이 그대로 활용할 수 있다는 점이 보장된다.

## 방법론

**DDIM 샘플링 방정식**은 학습된 노이즈 예측기 $\boldsymbol{\epsilon}_\theta^{(t)}$ 를 사용해 $\mathbf{x}_0$ 의 추정치 $\hat{\mathbf{x}}_0$ 를 구한 뒤, 이를 활용해 $\mathbf{x}_{t-1}$ 을 계산한다:

$$\mathbf{x}_{t-1} = \sqrt{\bar{\alpha}_{t-1}}\,\hat{\mathbf{x}}_0 + \sqrt{1-\bar{\alpha}_{t-1}-\sigma_t^2}\cdot\boldsymbol{\epsilon}_\theta^{(t)} + \sigma_t\boldsymbol{\epsilon}_t$$

여기서 $\hat{\mathbf{x}}_0 = \frac{\mathbf{x}_t - \sqrt{1-\bar{\alpha}_t}\,\boldsymbol{\epsilon}_\theta^{(t)}}{\sqrt{\bar{\alpha}_t}}$ 이고, $\boldsymbol{\epsilon}_t \sim \mathcal{N}(\mathbf{0}, \mathbf{I})$ 는 독립 가우시안 노이즈다.

**$\sigma_t = 0$ 설정 시**: 모든 확률적 노이즈 항이 제거되어 완전한 결정론적 ODE 궤적을 따른다:

$$\mathbf{x}_{t-1} = \sqrt{\bar{\alpha}_{t-1}}\,\hat{\mathbf{x}}_0 + \sqrt{1-\bar{\alpha}_{t-1}}\cdot\boldsymbol{\epsilon}_\theta^{(t)}$$

동일한 초기 잠재 변수 $\mathbf{x}_T$ 로부터 항상 동일한 이미지가 생성된다. 이는 연속 시간 상미분방정식을 이산화한 것과 동치임을 보일 수 있다.

**$\sigma_t = \sqrt{(1-\bar{\alpha}_{t-1})/(1-\bar{\alpha}_t)}\cdot\sqrt{1-\bar{\alpha}_t/\bar{\alpha}_{t-1}}$ 설정 시**: DDPM의 역방향 프로세스와 동일해진다. 이 두 극단 사이에서 $\eta \in [0,1]$ 파라미터로 $\sigma_t = \eta\,\tilde{\beta}_t$ 를 조정하면 확률성의 정도를 연속적으로 제어할 수 있다.

다음 그림은 $\eta$ 값에 따른 생성 결과의 변화를 보여준다. $\eta=0$ (완전 결정론적)일 때 가장 선명한 이미지가 생성되며, $\eta$ 가 커질수록 확률적 노이즈가 추가되어 동일한 초기 잠재 변수에서도 다른 이미지가 생성된다.

![eta 값에 따른 CIFAR-10 샘플 품질 변화](figures/fig_5_1.png)
*Figure 2: $\eta$ 에 따른 CIFAR-10 샘플 비교 ($\dim(\tau)=10$): $\eta=0$ (DDIM)에서 $\eta=1$ (DDPM)까지 확률성이 증가하며, 최하단 $\hat{\sigma}$ 행은 DDPM 스텝 건너뛰기 방식의 품질 열화를 보여준다. (Song et al., 2021)*

CelebA 데이터셋에서도 동일한 경향이 관찰된다. $\eta=0$ 의 결정론적 DDIM이 가장 선명한 얼굴을 생성하며, $\eta$ 가 증가할수록 세부 디테일이 변화한다. 특히 $\hat{\sigma}$ 행(DDPM 방식 스텝 건너뛰기)은 10 스텝에서 완전히 붕괴된 노이즈 이미지를 생성한다.

![eta 값에 따른 CelebA 샘플 품질 변화](figures/fig_5_3.png)
*Figure 3: $\eta$ 에 따른 CelebA 샘플 비교 ($\dim(\tau)=10$): CIFAR-10과 마찬가지로 $\eta=0$ 에서 가장 높은 품질을 보이며, DDPM 스텝 건너뛰기($\hat{\sigma}$)는 심각한 품질 저하를 초래한다. (Song et al., 2021)*

**가속 샘플링**: $\{1, \dots, T\}$ 에서 길이 $S$ 인 부분 수열 $\tau = \{\tau_1, \dots, \tau_S\}$ 를 선택하고, 해당 스텝들에만 역방향 전이를 적용한다. $T=1000$ 에서 $S=50$ 으로 설정하면 20배 가속이 가능하며, $S=100$ 이면 품질 저하가 거의 없다.

다음 그래피컬 모델은 이 가속 생성의 원리를 보여준다. 부분 수열 $\tau = [1, 3]$ 을 선택하면 $\mathbf{x}_2$ 를 건너뛰고 $\mathbf{x}_3 \to \mathbf{x}_1 \to \mathbf{x}_0$ 경로만 따르며, 건너뛴 스텝의 정보는 $q(\mathbf{x}_2|\mathbf{x}_1, \mathbf{x}_0)$ 등 비마르코프 전이를 통해 암묵적으로 반영된다.

![DDIM 가속 샘플링의 그래피컬 모델](figures/fig_4.png)
*가속 생성을 위한 그래피컬 모델 ($\tau = [1, 3]$): 중간 스텝 $\mathbf{x}_2$ 를 건너뛰고 부분 수열의 스텝만 사용하여 역방향 전이를 수행한다*

**DDIM Inversion**: 결정론적 특성 덕분에 실제 이미지 $\mathbf{x}_0$ 로부터 해당하는 잠재 변수 $\mathbf{x}_T$ 를 역산할 수 있다:

$$\mathbf{x}_{t+1} = \sqrt{\bar{\alpha}_{t+1}}\,\hat{\mathbf{x}}_0(\mathbf{x}_t) + \sqrt{1-\bar{\alpha}_{t+1}}\cdot\boldsymbol{\epsilon}_\theta^{(t)}$$

이를 통해 실제 이미지를 잠재 코드로 인코딩한 뒤 편집하는 파이프라인이 가능해진다. 두 잠재 벡터 사이의 구면 선형 보간(SLERP) 또한 의미 있는 이미지 변환을 생성한다.

## 실험 결과

CIFAR-10과 CelebA-HQ, LSUN 데이터셋에서 측정한 주요 결과:

| 방법 | 스텝 수 | FID (CIFAR-10) | 비고 |
|------|---------|----------------|------|
| DDPM | 1000 | 3.17 | 기준선 |
| DDPM (스텝 건너뛰기) | 100 | 37.5 | 마르코프 위반 |
| DDIM ($\sigma_t=0$) | 200 | 3.76 | \~5x 가속 |
| DDIM ($\sigma_t=0$) | 100 | 4.16 | \~10x 가속 |
| DDIM ($\sigma_t=0$) | 50 | 4.67 | \~20x 가속 |
| DDIM ($\sigma_t=0$) | 20 | 6.84 | \~50x 가속 |

다음 그래프는 스텝 수에 따른 50k 이미지 생성 소요 시간을 보여준다. DDIM은 스텝 수를 줄임으로써 생성 시간을 선형적으로 단축할 수 있다.

![CIFAR-10에서 스텝 수별 샘플링 소요 시간](figures/fig_10_1.png)
*Figure 4: CIFAR-10에서 스텝 수에 따른 50k 이미지 생성 소요 시간 (Nvidia 2080 Ti 기준) ) 스텝 수 감소에 비례하여 생성 시간이 줄어든다. (Song et al., 2021)*

50 스텝의 DDIM은 1000 스텝 DDPM과 비교해 **20배 빠르면서도 유사한 FID 4.67**을 달성한다. 동일 스텝에서 $\eta$ 값을 변화시키면 $\eta=0$ (결정론적)이 가장 낮은 FID를 보이는 경향이 있으며, CelebA-HQ 256x256에서는 100 스텝 DDIM이 1000 스텝 DDPM(FID 7.79)보다 오히려 낮은 FID 7.33을 기록하기도 했다. 이는 결정론적 경로가 확률적 탐색의 노이즈를 제거해 더 일관된 이미지를 생성하기 때문으로 해석된다.

DDIM의 결정론적 특성은 동일한 초기 잠재 변수 $\mathbf{x}_T$ 에서 스텝 수를 변화시켜도 의미적으로 일관된 이미지를 생성한다는 점에서 확인된다. 아래 CIFAR-10 실험은 동일한 $\mathbf{x}_T$ 로부터 10, 20, 50, 100, 1000 스텝으로 생성한 결과를 보여주며, 각 행이 동일한 잠재 변수에 대응한다.

![동일 잠재 변수에서 다양한 스텝으로 생성한 CIFAR-10 DDIM 샘플](figures/fig_13_1.png)
*Figure 5: 동일한 $\mathbf{x}_T$ 에서 스텝 수(10, 20, 50, 100, 1000)를 변화시킨 CIFAR-10 DDIM 샘플 ( 각 행은 동일 잠재 변수를 공유하며, 스텝 수가 줄어도 객체의 구조와 색감이 일관되게 유지된다. (Song et al., 2021)*

CelebA에서도 이러한 일관성이 확인된다. 다음 그림은 동일 $\mathbf{x}_T$ 로부터 20, 50, 100, 1000 스텝으로 생성한 CelebA 샘플을 비교한 것으로, 스텝 수와 무관하게 동일 인물의 유사한 포즈와 표정이 유지됨을 보여준다.

![동일 잠재 변수에서 스텝 수에 따른 CelebA DDIM 샘플 일관성](figures/fig_29.png)
*Figure 6: 동일한 $\mathbf{x}_T$ 에서 스텝 수(20, 50, 100, 1000)를 변화시킨 CelebA DDIM 샘플 ) 스텝 수가 줄어도 생성되는 이미지의 정체성, 포즈, 배경이 일관되게 유지된다. (Song et al., 2021)*

잠재 공간 보간 실험에서도 DDIM은 DDPM 대비 더 매끄럽고 의미 있는 중간 이미지를 생성한다. 두 잠재 벡터 $\mathbf{x}_T^{(1)}$, $\mathbf{x}_T^{(2)}$ 사이의 구면 선형 보간(SLERP)을 적용하면, 아래와 같이 자연스러운 속성 변환이 관찰된다.

![CelebA 잠재 공간 보간 결과](figures/fig_17_1.png)
*Figure 7: CelebA DDIM 잠재 공간 보간 ($\dim(\tau)=50$) ( 두 얼굴 사이의 구면 선형 보간이 피부색, 머리 스타일, 얼굴 윤곽 등의 속성을 매끄럽게 전환하며, 중간 이미지도 자연스러운 얼굴을 유지한다. (Song et al., 2021)*

LSUN Church 데이터셋에서도 100 스텝 DDIM과 DDPM의 품질 차이가 뚜렷하게 나타난다. DDPM은 100 스텝으로 줄이면 구조적 왜곡이 발생하지만, DDIM은 동일 스텝에서도 정밀한 건축물 디테일을 유지한다.

![LSUN Church 100 스텝 DDPM 샘플](figures/fig_30_1.png)
![LSUN Church 100 스텝 DDIM 샘플](figures/fig_30_2.png)
*Figure 8: LSUN Church 100 스텝 샘플 비교 ) DDPM(위)과 DDIM(아래). DDIM은 적은 스텝에서도 건축물의 구조와 세부 디테일을 효과적으로 보존한다. (Song et al., 2021)*

DDIM Inversion을 통한 재구성 충실도도 높게 측정되었다. 이는 실제 이미지를 잠재 코드로 인코딩한 뒤 다시 디코딩했을 때 원본과 거의 동일한 이미지가 복원됨을 의미하며, 이후 이미지 편집 파이프라인의 핵심 전제 조건이 된다.

## 의의 및 한계

**의의**: DDIM은 확산 모델의 실용화에 결정적인 기여를 했다. 기존에 학습된 DDPM 모델을 그대로 재사용하면서 추론 속도를 획기적으로 개선할 수 있다는 점은, 이미 공개된 수많은 사전 학습 모델에 즉시 적용 가능한 실용성을 의미한다. 결정론적 ODE 관점을 도입함으로써 이후 DDPM++, DPM-Solver, PNDM 등 더 정교한 ODE 솔버 기반 샘플러 연구의 토대를 마련했다. DDIM Inversion은 현재 Stable Diffusion 기반 이미지 편집 파이프라인(Prompt-to-Prompt, Null-text Inversion, InstructPix2Pix 등)의 핵심 구성 요소로 광범위하게 활용된다.

**한계**: DDIM Inversion은 Classifier-Free Guidance(CFG) 사용 시 재구성 오차가 발생하며, 이를 해결하기 위해 Null-text Inversion 등 후속 연구가 필요했다. ODE 이산화 오차로 인해 스텝 수를 극단적으로 줄이면(10 스텝 이하) 품질 저하가 두드러진다. DPM-Solver 계열은 이 문제를 고차 ODE 솔버로 개선하여 5-10 스텝 수준에서도 우수한 품질을 달성한다. 또한 기본 DDIM은 여전히 GAN의 단일 포워드 패스보다 훨씬 느리다.

## 코드 예제

`diffusers` 라이브러리를 사용해 DDIM 샘플러를 적용하는 예시다. `eta=0` 이 순수 DDIM(결정론적), `eta=1` 이 DDPM에 해당한다.

```python
from diffusers import DDIMScheduler, UNet2DModel
import torch

# 사전 학습된 DDPM 모델 로드 후 DDIM 스케줄러로 교체
# 추가 학습 없이 기존 모델 가중치를 그대로 사용
scheduler = DDIMScheduler.from_pretrained(
    "google/ddpm-cifar10-32",
    beta_schedule="linear",
)
unet = UNet2DModel.from_pretrained("google/ddpm-cifar10-32").cuda()

# 샘플링 스텝 수 설정: DDPM 1000 스텝 → DDIM 50 스텝 (20배 가속)
scheduler.set_timesteps(num_inference_steps=50)

# 초기 잠재 변수 샘플링 (고정 시드로 재현 가능)
generator = torch.Generator(device="cuda").manual_seed(42)
image = torch.randn(
    (1, unet.config.in_channels, unet.config.sample_size, unet.config.sample_size),
    generator=generator,
    device="cuda",
)

# 결정론적 역방향 프로세스
# eta=0: sigma_t=0 → DDIM (완전 결정론적 ODE 궤적)
# eta=1: DDPM과 동일한 분산을 사용하는 확률적 샘플링
for t in scheduler.timesteps:
    with torch.no_grad():
        noise_pred = unet(image, t).sample
    image = scheduler.step(
        noise_pred, t, image, eta=0.0
    ).prev_sample

# [-1, 1] → [0, 1] 정규화 후 저장
image = (image / 2 + 0.5).clamp(0, 1)
print(f"생성 완료: {image.shape}")  # torch.Size([1, 3, 32, 32])

# DDIM Inversion 예시 (실제 이미지 → 잠재 코드)
from diffusers import DDIMInverseScheduler

inv_scheduler = DDIMInverseScheduler.from_pretrained(
    "google/ddpm-cifar10-32",
    beta_schedule="linear",
)
inv_scheduler.set_timesteps(num_inference_steps=50)

# real_image: 편집하고 싶은 실제 이미지 텐서 (1, C, H, W)
latent = real_image  # 실제 이미지에서 시작
for t in inv_scheduler.timesteps:
    with torch.no_grad():
        noise_pred = unet(latent, t).sample
    latent = inv_scheduler.step(noise_pred, t, latent).prev_sample

# latent: 실제 이미지에 대응하는 잠재 코드 x_T
# 이를 편집한 뒤 DDIM으로 디코딩하면 이미지 편집 파이프라인 구성 가능
```

## 관련 문서

- [[DDPM]] ( DDIM이 기반으로 하는 원조 확산 모델; 마르코프 체인 기반 1000 스텝 샘플링
- [[Score-Based Generative Models]] ) 연속 시간 SDE/ODE 관점으로 DDIM을 통합하는 프레임워크
- [[DPM-Solver]] ( 고차 ODE 솔버를 활용해 5-10 스텝 고품질 샘플링을 달성
- [[Latent Diffusion Models]] ) DDIM 샘플러를 잠재 공간에 적용한 Stable Diffusion의 기반
- [[Null-text Inversion]] ( CFG 환경에서 DDIM Inversion의 재구성 오차를 해결
- [[Consistency Models]] ) DDIM ODE 궤적을 직접 학습해 단일 스텝 생성을 달성
