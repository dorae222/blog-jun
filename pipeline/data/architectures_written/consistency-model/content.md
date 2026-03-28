# Consistency Model: 일관성 모델

## 개요

Consistency Models는 2023년 OpenAI의 Yang Song 등이 발표한 연구로, 확산 모델의 가장 큰 단점인 수십~수백 번의 반복 샘플링을 극적으로 줄여 **단일 스텝 또는 소수 스텝**으로 고품질 이미지를 생성하는 새로운 생성 모델 패밀리이다. 확률 흐름 ODE 궤적 위의 모든 점이 동일한 시작점으로 수렴한다는 사실을 활용하여, 궤적 위 어떤 점에서도 시작점을 직접 예측하는 '일관성 함수'를 학습한다.

- **논문**: [Consistency Models](https://arxiv.org/abs/2303.01469)
- **코드**: [openai/consistency_models](https://github.com/openai/consistency_models)
- **발표**: 2023년 3월, OpenAI
- **라이선스**: MIT

![Consistency Model 전체 구조 - PF-ODE 궤적 매핑, 두 가지 학습 방법, 단일/다단계 생성](figures/architecture.png)
*Figure 1: Consistency Model 전체 구조 - PF-ODE 궤적 위의 임의 점을 원점으로 직접 매핑하는 일관성 함수, Consistency Distillation(CD)과 Consistency Training(CT) 두 가지 학습 방법, 그리고 단일/다단계 생성 방식. (Source: Song et al., 2023)*

## 아키텍처 상세

### 확률 흐름 ODE와 일관성 함수

확산 모델의 확률 흐름 ODE는 다음과 같이 정의된다:

$$\frac{d\mathbf{x}_t}{dt} = -t \cdot \nabla_{\mathbf{x}} \log p_t(\mathbf{x}_t)$$

이 ODE의 해 궤적(solution trajectory) 위의 임의의 점 $(\mathbf{x}_t, t)$에서, ODE를 $t_{\min}$까지 적분하면 동일한 점 $\mathbf{x}_{t_{\min}}$에 도달한다. Consistency function $f: (\mathbf{x}_t, t) \mapsto \mathbf{x}_{t_{\min}}$은 이 매핑을 직접 학습한다.

![일관성 함수의 핵심 개념 - ODE 궤적 위 모든 점이 동일한 시작점으로 매핑](figures/fig_2.jpg)
*Figure 2: 일관성 함수 개념도 - 여러 ODE 궤적(색상별)에서, 궤적 위의 모든 점 $(x_t, t)$, $(x_{t'}, t')$이 동일한 시작점 $(x_0, 0)$으로 매핑된다. 이를 통해 노이즈에서 한 번의 함수 평가로 깨끗한 이미지를 직접 예측할 수 있다. (Source: Song et al., 2023)*

### 일관성 함수의 조건

$f_\theta$는 두 가지 조건을 만족해야 한다:

1. **경계 조건**: $f_\theta(\mathbf{x}_{t_{\min}}, t_{\min}) = \mathbf{x}_{t_{\min}}$
2. **자기 일관성**: 동일 ODE 궤적 위의 모든 $(t, t')$에 대해 $f_\theta(\mathbf{x}_t, t) = f_\theta(\mathbf{x}_{t'}, t')$

이를 보장하기 위해 출력을 다음과 같이 파라미터화한다:

$$f_\theta(\mathbf{x}_t, t) = c_{\text{skip}}(t) \cdot \mathbf{x}_t + c_{\text{out}}(t) \cdot F_\theta(\mathbf{x}_t, t)$$

$t_{\min}$에서 $c_{\text{skip}} = 1$, $c_{\text{out}} = 0$이 되도록 설계하여 경계 조건을 자동으로 만족시킨다. EDM의 Preconditioning 프레임워크를 그대로 활용한다.

### 학습 방법 1: Consistency Distillation (CD)

사전학습된 확산 모델(교사 모델)을 활용하는 증류 방식:

$$\mathcal{L}^N_{CD} = \mathbb{E}\left[d\left(f_\theta(\mathbf{x}_{t_{n+1}}, t_{n+1}), f_{\theta^-}(\hat{\mathbf{x}}^{\phi}_{t_n}, t_n)\right)\right]$$

여기서:
- $\hat{\mathbf{x}}^{\phi}_{t_n}$: 교사 ODE 솔버로 $\mathbf{x}_{t_{n+1}}$에서 한 스텝 진행한 결과
- $f_{\theta^-}$: EMA로 업데이트되는 타겟 네트워크
- $d(\cdot, \cdot)$: LPIPS 등의 거리 함수

### 학습 방법 2: Consistency Training (CT)

교사 모델 없이 독립적으로 학습:

$$\mathcal{L}^N_{CT} = \mathbb{E}\left[d\left(f_\theta(\mathbf{x}_{t_{n+1}}, t_{n+1}), f_{\theta^-}(\mathbf{x}_{t_n}, t_n)\right)\right]$$

CT에서는 타임스텝 이산화 수 $N$을 점진적으로 증가시키는 커리큘럼 학습 전략이 사용된다.

![확률 흐름 ODE에서 일관성 함수가 궤적 위 모든 점을 데이터로 매핑하는 과정](figures/fig_1.jpg)
*Figure 3: PF-ODE 궤적 시각화 - 데이터에서 노이즈까지의 확률 흐름 ODE 위에서, 일관성 함수 $f_\theta$가 임의 시점 $(x_t, t)$을 원래 데이터 $(x_0, 0)$으로 직접 매핑한다. (Source: Song et al., 2023)*

### 다단계 샘플링 (Multistep Sampling)

단일 스텝 생성 후 품질을 추가로 향상시킬 수 있는 다단계 방법:

1. $\hat{\mathbf{x}}_0 = f_\theta(\mathbf{x}_T, T)$ (단일 스텝 예측)
2. $\mathbf{x}_{t_n} = \sqrt{\bar{\alpha}_{t_n}} \hat{\mathbf{x}}_0 + \sqrt{1 - \bar{\alpha}_{t_n}} \boldsymbol{\epsilon}$ (노이즈 재주입)
3. $\hat{\mathbf{x}}_0 = f_\theta(\mathbf{x}_{t_n}, t_n)$ (재예측)
4. 반복

## 핵심 혁신

1. **단일 스텝 생성**: 확산 모델 역사상 최초로 단일 스텝에서 경쟁력 있는 FID를 달성하였다.
2. **재학습 불필요(CD)**: 기존 확산 모델 체크포인트를 교사로 활용하여 일관성 모델로 증류할 수 있다.
3. **독립 학습(CT)**: 교사 모델 없이도 일관성 조건을 만족하도록 직접 학습이 가능하다.
4. **유연한 품질-속도 제어**: 단일 스텝부터 다단계 샘플링까지 추론 시간에 자유롭게 선택 가능하다.

![EDM vs CT 단일 스텝 vs CT 2-스텝 생성 비교](figures/fig_13_1.png)
*Figure 4: 생성 품질 비교 - EDM 교사 모델(상단), CT 단일 스텝 생성(중단), CT 2-스텝 생성(하단)의 결과. 동일한 초기 노이즈에서 생성되었으며, 2-스텝만으로도 교사 모델에 근접한 품질을 달성한다. (Source: Song et al., 2023)*

## 벤치마크/성능

| 방법 | 데이터셋 | 스텝 수 | FID (↓) |
|------|---------|---------|---------|
| CD (Consistency Distillation) | CIFAR-10 | 1 | 3.55 |
| CD | CIFAR-10 | 2 | **2.93** |
| CT (Consistency Training) | CIFAR-10 | 1 | 8.70 |
| CT | CIFAR-10 | 2 | 5.83 |
| CD | ImageNet 64×64 | 1 | 6.20 |
| CD | ImageNet 64×64 | 2 | 4.70 |
| DDIM | CIFAR-10 | 10 | 13.36 |
| DDIM | CIFAR-10 | 50 | 4.67 |
| EDM (교사 모델) | CIFAR-10 | 35 | 1.97 |

CD 2스텝이 DDIM 50스텝과 유사한 FID를 약 25배 적은 연산으로 달성한다.

## 관련 모델 비교

| 특성 | Consistency Model | DDIM | Progressive Distillation | Rectified Flow |
|------|-----------------|------|------------------------|----------------|
| 최소 스텝 수 | 1 | 10+ | 4 | 1 (Reflow 후) |
| 교사 모델 필요 | CD: 필요, CT: 불필요 | 불필요 | 필요 | 불필요 |
| 다단계 개선 | 가능 | 가능 | 제한적 | 제한적 |
| 이론적 기반 | PF-ODE 일관성 | 비마르코프 | KL 증류 | 최적 수송 |
| 발표 연도 | 2023 | 2020 | 2022 | 2022 |

## 학습 상세

- **데이터셋**: CIFAR-10 (32×32), ImageNet (64×64)
- **기반 아키텍처**: EDM U-Net (~300M 파라미터)
- **교사 모델 (CD)**: 사전학습된 EDM 확산 모델
- **커리큘럼**: 타임스텝 이산화 $N$을 점진적으로 증가
- **거리 함수**: LPIPS (Learned Perceptual Image Patch Similarity)
- **최적화**: Adam, EMA 적용

## 실무 활용

### 1. 실시간 이미지 생성

단일 스텝 생성으로 기존 확산 모델 대비 10~100배 빠른 추론이 가능하여, 실시간 응용에 적합하다. Latent Consistency Model(LCM)은 이 기법을 Stable Diffusion에 적용하여 4스텝 생성을 달성하였다.

### 2. 빠른 증류 파이프라인

기존에 학습된 고품질 확산 모델을 Consistency Distillation으로 빠르게 가속화할 수 있다. FLUX.1-schnell은 유사한 개념으로 8스텝 생성을 지원한다.

### 3. 이미지 편집 및 인페인팅

다단계 샘플링과 조건부 생성을 결합하여 빠른 이미지 편집 파이프라인을 구성할 수 있다.

## 한계 및 전망

### 한계

1. **단일 스텝 품질 한계**: 교사 모델(EDM FID 1.97) 대비 단일 스텝(FID 3.55)은 여전히 품질 격차가 존재한다.
2. **CT의 불안정성**: 교사 없는 학습은 CD 대비 품질이 낮으며 학습이 불안정할 수 있다.
3. **대규모 모델 적용 어려움**: 고해상도·대규모 모델에서의 증류는 추가적인 엔지니어링이 필요하다.

### 후속 발전

- **iCT (improved CT, 2024)**: 교사 없는 학습의 품질을 CD 수준으로 끌어올림
- **Latent Consistency Model (LCM)**: Stable Diffusion에 적용하여 4스텝 고해상도 생성
- **SDXL-Turbo**: Adversarial Diffusion Distillation으로 1~4스텝 생성
- **Consistency Flow Matching**: Flow Matching과 일관성 학습의 결합

Consistency Model은 확산 모델의 추론 속도 한계를 근본적으로 돌파한 연구로, 실시간 생성 AI의 실현 가능성을 제시하였다.

## 관련 문서

- [[score-sde|Score-based SDE (Stochastic Differential Equations)]] - 발전 기반
