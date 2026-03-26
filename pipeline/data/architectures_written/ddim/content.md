# DDIM: 디노이징 확산 암묵 모델

**Stanford University** · **2020-10-06** · **Diffusion** · **MIT**

## 개요

DDIM(Denoising Diffusion Implicit Models)은 2020년 Stanford University의 Jiaming Song, Chenlin Meng, Stefano Ermon이 발표한 논문으로, 확산 모델(Diffusion Model)의 샘플링 속도를 근본적으로 개선한 결정론적 샘플링 기법이다. 확산 모델은 데이터에 점진적으로 가우시안 노이즈를 추가하는 forward 과정과, 이를 역으로 제거하며 이미지를 생성하는 reverse 과정으로 구성된다. DDPM(Denoising Diffusion Probabilistic Models)은 이 reverse 과정을 마르코프 체인(Markov chain)으로 모델링하여 매 스텝마다 확률적 전이를 수행하였고, 그 결과 고품질 이미지를 얻으려면 1000번의 순차적 디노이징 스텝이 필요하였다. 이는 GAN이나 VAE 대비 수십~수백 배 느린 추론 속도를 의미하며, 확산 모델의 실용적 활용에 큰 장벽이 되었다.

DDIM은 이 문제를 근본적으로 해결하였다. 핵심 통찰은 DDPM의 forward 과정을 마르코프 체인이 아닌 **비마르코프(non-Markovian) 과정**으로 재정의하더라도 동일한 marginal 분포 $q(\mathbf{x}_t|\mathbf{x}_0)$를 유지할 수 있다는 점이다. 이를 통해 역방향 샘플링 과정에서 확률적 노이즈 주입의 크기를 자유롭게 조절할 수 있으며, 노이즈를 완전히 제거($\sigma_t=0$)하면 결정론적 ODE(Ordinary Differential Equation) 샘플러가 된다. 결정론적 특성 덕분에 동일한 초기 노이즈에서 항상 동일한 이미지가 재현되며, 이 성질은 이미지 편집과 잠재 공간 보간에서 핵심적으로 활용된다. DDIM은 재학습 없이 기존 DDPM 체크포인트를 그대로 사용하면서 10~50 스텝만으로 유사한 품질의 이미지를 생성할 수 있음을 증명하였고, 이후 Stable Diffusion, DALL-E 2 등 거의 모든 확산 기반 생성 모델의 기본 샘플러로 채택되면서 확산 모델의 실용화를 이끈 핵심 돌파구로 평가받는다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

### 비마르코프 Forward Process 재정의

DDPM의 forward 과정은 $q(\mathbf{x}_{1:T}|\mathbf{x}_0) = \prod_{t=1}^{T} q(\mathbf{x}_t|\mathbf{x}_{t-1})$로 정의되는 마르코프 체인이다. 각 전이는 $q(\mathbf{x}_t|\mathbf{x}_{t-1}) = \mathcal{N}(\sqrt{1-\beta_t}\mathbf{x}_{t-1}, \beta_t\mathbf{I})$이며, 누적 분포는 $q(\mathbf{x}_t|\mathbf{x}_0) = \mathcal{N}(\sqrt{\bar{\alpha}_t}\mathbf{x}_0, (1-\bar{\alpha}_t)\mathbf{I})$이다.

DDIM은 동일한 marginal $q(\mathbf{x}_t|\mathbf{x}_0)$를 만족하는 비마르코프 과정 $q_\sigma(\mathbf{x}_{1:T}|\mathbf{x}_0)$를 정의한다. 조건부 역방향 분포는 다음과 같다:

$$q_\sigma(\mathbf{x}_{t-1}|\mathbf{x}_t, \mathbf{x}_0) = \mathcal{N}\left(\sqrt{\bar{\alpha}_{t-1}}\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_{t-1}-\sigma_t^2}\cdot\frac{\mathbf{x}_t - \sqrt{\bar{\alpha}_t}\mathbf{x}_0}{\sqrt{1-\bar{\alpha}_t}}, \sigma_t^2\mathbf{I}\right)$$

여기서 $\sigma_t$는 각 스텝의 확률성(stochasticity)을 제어하는 파라미터로, $\sigma_t = \eta\sqrt{(1-\bar{\alpha}_{t-1})/(1-\bar{\alpha}_t)}\sqrt{1-\bar{\alpha}_t/\bar{\alpha}_{t-1}}$로 정의된다. $\eta=1$이면 DDPM과 동일하고, $\eta=0$이면 완전히 결정론적인 DDIM이 된다.

### 역방향 샘플링 공식

학습된 노이즈 예측 네트워크 $\boldsymbol{\epsilon}_\theta$를 사용한 역방향 샘플링 공식은 다음과 같다:

$$\mathbf{x}_{t-1} = \sqrt{\bar{\alpha}_{t-1}}\underbrace{\left(\frac{\mathbf{x}_t - \sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)}{\sqrt{\bar{\alpha}_t}}\right)}_{\hat{\mathbf{x}}_0\text{ (예측된 원본)}} + \underbrace{\sqrt{1-\bar{\alpha}_{t-1}-\sigma_t^2}\cdot\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t)}_{\text{방향 벡터}} + \underbrace{\sigma_t\boldsymbol{\epsilon}_t}_{\text{확률적 노이즈}}$$

이 공식은 세 부분으로 해석된다: (1) 현재 노이즈 예측에서 추정한 원본 이미지 $\hat{\mathbf{x}}_0$를 타겟 노이즈 레벨로 스케일링, (2) 예측된 노이즈 방향으로의 이동, (3) 선택적 확률적 노이즈 주입.

### 결정론적 샘플링과 DDIM Inversion

$\sigma_t=0$($\eta=0$)으로 설정하면 확률적 노이즈 항이 사라져 결정론적 ODE 샘플러가 된다. 이는 확률 흐름 ODE(Probability Flow ODE)와 수학적으로 동치이며, 동일한 초기 잠재 변수 $\mathbf{x}_T$에서 항상 동일한 이미지 $\mathbf{x}_0$가 재현된다.

이 결정론적 특성은 **DDIM Inversion**을 가능하게 한다. Forward ODE를 따라 실제 이미지를 잠재 공간으로 인코딩한 뒤, 조건(텍스트 프롬프트 등)을 변경하여 다시 디코딩하면 원본 이미지의 구조를 유지하면서 의미적 편집이 가능하다. 이 기법은 Prompt-to-Prompt, Null-text Inversion 등 텍스트 기반 이미지 편집의 핵심 기술로 자리잡았다.

### 가속 샘플링 (Accelerated Sampling)

DDIM은 전체 $T=1000$ 타임스텝에서 $S \ll T$개를 균등하게 선택하여 서브시퀀스 $\{\tau_1, \tau_2, \ldots, \tau_S\}$를 구성한다. 선택된 타임스텝 간의 간격이 커지더라도 비마르코프 정의 덕분에 marginal 분포가 유지되므로, 10~50 스텝만으로도 1000 스텝에 근접하는 품질을 달성한다.

## 핵심 혁신

DDIM의 가장 중요한 기여는 확산 모델의 forward-reverse 과정이 반드시 마르코프적일 필요가 없다는 이론적 통찰이다. 이를 통해 다섯 가지 핵심 혁신이 달성되었다: (1) **재학습 불필요** -- 기존 DDPM 체크포인트를 그대로 활용하여 즉시 가속화 가능, (2) **결정론적 샘플링** -- 동일 초기 노이즈에서 항상 동일한 이미지 생성으로 재현성 확보, (3) **DDIM Inversion** -- 실제 이미지를 잠재 공간에 정확히 인코딩하여 편집 파이프라인 구성 가능, (4) **유연한 속도-품질 트레이드오프** -- $\eta$ 파라미터와 스텝 수로 연속적 조절, (5) **잠재 공간 보간** -- 두 잠재 벡터 사이의 구형 선형 보간(slerp)으로 의미 있는 중간 이미지 생성. 이 혁신들은 확산 모델을 학술적 호기심에서 실용적 도구로 전환시킨 전환점이었다.

## 벤치마크/성능

| 데이터셋 | 모델 | 스텝 수 | FID (↓) | IS (↑) |
|---------|------|---------|---------|--------|
| CIFAR-10 | DDIM | 10 | 13.36 | - |
| CIFAR-10 | DDIM | 20 | 6.84 | - |
| CIFAR-10 | DDIM | 50 | 4.67 | 8.78 |
| CIFAR-10 | DDIM | 100 | 4.04 | 8.95 |
| CIFAR-10 | DDPM | 1000 | 3.17 | 9.46 |
| CelebA 64x64 | DDIM | 50 | ~6.5 | - |
| LSUN Bedroom | DDIM | 50 | ~8.2 | - |

50 스텝 DDIM은 1000 스텝 DDPM의 FID 3.17에 근접하는 4.67을 달성하며, **20배 이상의 속도 향상**을 보인다. 특히 동일 NFE(Number of Function Evaluations) 예산에서 DDPM의 확률적 샘플러보다 일관되게 낮은 FID를 기록하여, 결정론적 샘플링의 효과를 실증하였다. CelebA와 LSUN 등 고해상도 데이터셋에서도 안정적인 성능을 유지한다.

## 학습

DDIM은 별도의 재학습이 필요하지 않으며, DDPM의 사전학습된 체크포인트를 그대로 활용한다. 실험은 CIFAR-10(32x32), CelebA(64x64), LSUN(256x256) 등 표준 벤치마크에서 진행되었다. 학습 목표 함수는 DDPM과 동일한 $\mathcal{L} = \mathbb{E}_{t,\mathbf{x}_0,\boldsymbol{\epsilon}}[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\sqrt{\bar{\alpha}_t}\mathbf{x}_0 + \sqrt{1-\bar{\alpha}_t}\boldsymbol{\epsilon}, t)\|^2]$이다. DDIM의 기여는 학습이 아니라 추론 시의 샘플링 전략 변경에 있다.

## 관련 모델

DDIM은 DDPM에서 직접 발전하였으며, 이후 DPM-Solver(고차 ODE 솔버), PLMS/DEIS(다단계 방법), Flow Matching(직선 궤적), Consistency Model(단일 스텝 생성) 등 후속 샘플링 가속화 연구들의 이론적 출발점이 되었다.

## 참고 자료

- [논문: Denoising Diffusion Implicit Models](https://arxiv.org/abs/2010.02502)
- [코드](https://github.com/ermongroup/ddim)

## 관련 문서

- [[ddpm|DDPM (Denoising Diffusion Probabilistic Models)]] — 발전 기반