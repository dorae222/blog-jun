# Diffusion (Thermodynamics): 비평형 열역학 기반 확산 생성 모델

## 개요

"Deep Unsupervised Learning using Nonequilibrium Thermodynamics"는 2015년 Stanford University의 Jascha Sohl-Dickstein 등이 발표한 논문으로, 비평형 열역학(non-equilibrium thermodynamics)에서 영감을 받아 **확산 과정을 생성 모델로 정립한 최초의 논문**이다. 이 연구는 현대 확산 모델(DDPM, Score-SDE, Stable Diffusion 등)의 이론적 출발점이며, 생성 모델 연구의 방향을 근본적으로 전환시킨 선구적 업적이다.

- **논문**: [Deep Unsupervised Learning using Nonequilibrium Thermodynamics](https://arxiv.org/abs/1503.03585)
- **발표**: 2015년 3월, Stanford University
- **라이선스**: N/A (학술 논문)

다음 그림은 비평형 열역학 기반 확산 모델의 전체 구조를 보여준다.

![비평형 열역학 기반 확산 모델 아키텍처](figures/architecture.png)
*Figure 1: 확산 모델 전체 구조 — Forward Process(점진적 노이즈 추가), Reverse Process(학습된 디노이징), U-Net 아키텍처, ELBO 학습 목표, 노이즈 스케줄을 포함한 이론적 프레임워크. (Source: Sohl-Dickstein et al., 2015)*

## 아키텍처 상세

### 열역학적 직관

열역학에서 확산 현상은 물질이 고농도에서 저농도로 이동하며 결국 균일한 분포(열역학적 평형 상태)에 도달하는 과정이다. 이 논문은 이를 확률 분포의 변환으로 재해석하였다:

- **복잡한 데이터 분포** $q(\mathbf{x}_0)$ → 점진적 노이즈 추가 → **단순한 가우시안** $\mathcal{N}(0, \mathbf{I})$
- **가우시안 노이즈** → 역과정 학습 → **데이터 분포** 복원

### Forward Process (확산 과정)

Forward process는 원본 데이터 $\mathbf{x}_0$에 점진적으로 가우시안 노이즈를 추가하는 Markov chain으로 정의된다:

$$q(\mathbf{x}_t | \mathbf{x}_{t-1}) = \mathcal{N}(\mathbf{x}_t; \sqrt{1 - \beta_t} \mathbf{x}_{t-1}, \beta_t \mathbf{I})$$

여기서 $\beta_t$는 각 단계의 노이즈 스케줄이다. 충분한 단계 $T$ 후:

$$\mathbf{x}_T \sim \mathcal{N}(0, \mathbf{I})$$

임의의 $t$에서의 주변 분포는 닫힌 형식으로 계산 가능하다:

$$q(\mathbf{x}_t | \mathbf{x}_0) = \mathcal{N}(\mathbf{x}_t; \sqrt{\bar{\alpha}_t} \mathbf{x}_0, (1 - \bar{\alpha}_t) \mathbf{I})$$

여기서 $\bar{\alpha}_t = \prod_{s=1}^{t}(1 - \beta_s)$이다.

### Reverse Process (역과정)

역과정은 신경망이 학습하는 조건부 가우시안으로 정의된다:

$$p_\theta(\mathbf{x}_{t-1} | \mathbf{x}_t) = \mathcal{N}(\mathbf{x}_{t-1}; \boldsymbol{\mu}_\theta(\mathbf{x}_t, t), \boldsymbol{\Sigma}_\theta(\mathbf{x}_t, t))$$

핵심 통찰은 forward process의 각 단계가 아주 작은 양의 노이즈만 추가하므로, 역과정도 가우시안으로 근사할 수 있다는 것이다.

### 학습 목표: ELBO 최대화

학습 목표는 Evidence Lower Bound(ELBO)를 최대화하는 것이다:

$$\mathcal{L} = \mathbb{E}_q\left[-\log p_\theta(\mathbf{x}_0 | \mathbf{x}_1) + \sum_{t=2}^{T} D_{\text{KL}}\left(q(\mathbf{x}_{t-1} | \mathbf{x}_t, \mathbf{x}_0) \| p_\theta(\mathbf{x}_{t-1} | \mathbf{x}_t)\right) + D_{\text{KL}}(q(\mathbf{x}_T | \mathbf{x}_0) \| p(\mathbf{x}_T))\right]$$

각 항의 의미:
- **$\mathcal{L}_0$**: 재구성 항 — 최종 디코딩 품질
- **$\mathcal{L}_{t}$**: 확산 손실 — 각 스텝에서의 디노이징 정확도
- **$\mathcal{L}_T$**: Prior 일치 항 — $\mathbf{x}_T$가 가우시안에 수렴하는 정도

### 두 가지 확산 변형

논문은 두 가지 확산 유형을 제안하였다:

| 유형 | 데이터 타입 | 노이즈 분포 | 적용 범위 |
|------|-----------|-----------|---------|
| Gaussian Diffusion | 연속 데이터 | 가우시안 | 이미지, 오디오 |
| Binomial Diffusion | 이진/이산 데이터 | 이항 | 텍스트, 이산 토큰 |

다음 그림은 2D Swiss Roll 데이터에서의 forward 확산 과정을 보여주는 개념 검증 실험 결과이다.

![Swiss Roll 데이터의 forward 확산 과정](figures/fig_1_1.png)
*Figure 1: Swiss Roll 데이터에서의 확산 과정 — 복잡한 나선형 데이터 분포가 점진적인 가우시안 노이즈 추가를 통해 등방 가우시안으로 변환되는 forward process의 시작점. (Source: Sohl-Dickstein et al., 2015)*

다음은 MNIST 데이터셋에서 학습된 확산 모델의 생성 샘플이다.

![확산 모델로 생성된 MNIST 샘플](figures/fig_6.png)
*Figure 2: 확산 확률 모델로 생성된 MNIST 숫자 샘플 — 평균이 아닌 실제 가우시안/이항 분포에서 추출한 진정한 샘플로, 초기 확산 모델의 생성 능력을 보여준다. (Source: Sohl-Dickstein et al., 2015)*

## 핵심 혁신

1. **확산 과정의 생성 모델 정립**: 열역학적 확산 과정을 확률적 생성 모델로 처음 정립한 선구적 아이디어이다.
2. **Markov Chain을 통한 점진적 변환**: 복잡한 분포를 단순한 분포로, 또는 그 역으로 점진적으로 변환하는 프레임워크는 이후 모든 확산 모델의 핵심 원리가 되었다.
3. **학습 안정성**: GAN과 달리 모드 붕괴(mode collapse) 없이 안정적으로 학습할 수 있다.
4. **이론적 정당성**: 변분 추론(ELBO) 기반의 수학적으로 정당한 학습 목표를 제공한다.

## 벤치마크/성능

| 데이터셋 | 방법 | 성능 | 비고 |
|---------|------|------|------|
| Swiss Roll (2D) | 확산 모델 | 분포 복원 성공 | 개념 검증 |
| MNIST | 확산 모델 | 합리적 품질 | 초기 실험 |
| CIFAR-10 | 확산 모델 | GAN 대비 낮음 | 초기 단계 |
| CIFAR-10 | DDPM (2020) | FID 3.17 | 후속 개선 |
| CIFAR-10 | EDM (2022) | FID 1.97 | 최적화 |

초기 구현의 생성 품질은 동시대 GAN이나 VAE에 미치지 못했으나, 이론적 정당성과 학습 안정성을 입증하는 데 초점이 맞추어져 있었다.

## 관련 모델 비교

| 특성 | 확산 모델 (2015) | VAE (2013) | GAN (2014) | 정규화 흐름 (2015) |
|------|---------------|-----------|-----------|-----------------|
| 학습 안정성 | 높음 | 높음 | 낮음 | 높음 |
| 모드 커버리지 | 높음 | 높음 | 낮음 | 높음 |
| 생성 속도 | 매우 느림 | 빠름 | 빠름 | 빠름 |
| 이론적 기반 | ELBO | ELBO | 적대적 | Exact Likelihood |
| 생성 품질 (당시) | 보통 | 보통 | 높음 | 낮음 |

## 학습 상세

- **데이터셋**: Swiss Roll (2D), MNIST, CIFAR-10
- **확산 단계**: $T = 1000 \sim 2000$ 스텝
- **노이즈 스케줄**: $\beta_t$를 선형적으로 증가
- **디노이저**: 기본 MLP 구조 (이후 연구에서 U-Net으로 대체)
- **최적화**: 표준 SGD/Adam

## 실무 활용

### 1. 확산 모델의 이론적 토대

현대 모든 확산 기반 생성 모델(DDPM, Score-SDE, Stable Diffusion, DALL-E, Sora 등)의 이론적 출발점이다. Forward/Reverse process, ELBO 학습 목표의 기본 프레임워크가 이 논문에서 확립되었다.

### 2. 확률적 생성 프레임워크

확산 모델의 학습 안정성과 모드 커버리지 특성은 GAN의 한계를 극복하는 대안으로, 이미지 생성을 넘어 오디오, 비디오, 3D, 분자 설계 등 다양한 영역에 확산 모델이 적용되는 기초가 되었다.

### 3. 교육 목적

확산 모델의 수학적 기초를 이해하기 위한 필독 논문으로, DDPM과 함께 확산 모델 입문에 핵심적인 참고 자료이다.

## 한계 및 전망

### 한계

1. **낮은 생성 품질**: 초기 구현은 단순한 MLP 디노이저를 사용하여 생성 품질이 제한적이었다.
2. **매우 느린 생성 속도**: 1000~2000 스텝의 순차적 디노이징이 필요하여 실시간 활용이 불가능했다.
3. **고정된 노이즈 스케줄**: 선형 스케줄이 모든 데이터에 최적은 아니며, 이후 VDM에서 학습 가능한 스케줄로 발전하였다.

### 후속 발전의 역사

- **DDPM (2020)**: U-Net 디노이저 + $\epsilon$-예측으로 생성 품질 혁신
- **Score-SDE (2021)**: 연속 시간 SDE 프레임워크로 일반화
- **DDIM (2020)**: 결정론적 샘플링으로 속도 개선
- **LDM (2022)**: 잠재 공간 확산으로 효율성 혁명
- **Stable Diffusion (2022)**: LDM 기반 오픈소스 모델로 대중화

이 논문은 2015년 발표 당시에는 큰 주목을 받지 못했으나, 2020년 DDPM의 성공 이후 재조명되면서 확산 모델 혁명의 진정한 시작점으로 인정받고 있다. 과학적 호기심에서 시작된 열역학-확률론의 교차점이 현재 AI 이미지 생성의 지배적 패러다임이 되었다는 점에서, 기초 연구의 장기적 가치를 보여주는 대표적 사례이다.

## 관련 문서

- [[ddpm|DDPM (Denoising Diffusion Probabilistic Models)]] — 후속 모델
- [[score-matching|Score-based Generative Model (NCSN)]] — 영감을 줌
