# Flow Matching: 시뮬레이션 없는 연속 정규화 흐름 학습

## 개요

Flow Matching(FM)은 2022년 Meta AI의 Yaron Lipman 등이 제안한 생성 모델 프레임워크로, 연속 정규화 흐름(Continuous Normalizing Flows, CNF)을 확장성 있고 시뮬레이션 없이 학습 가능하게 만든 핵심 기법이다. 기존 CNF는 학습 시 ODE 시뮬레이션이 필요하여 계산 비용이 막대했으나, Flow Matching은 단순 회귀 손실로 벡터 필드를 직접 학습할 수 있음을 보였다. 이후 SD3, Flux, Sora 등 현대 대규모 확산 모델들이 채택한 핵심 학습 기법이다.

- **논문**: [Flow Matching for Generative Modeling](https://arxiv.org/abs/2210.02747)
- **코드**: [atong01/conditional-flow-matching](https://github.com/atong01/conditional-flow-matching)
- **발표**: 2022년 10월, Meta AI Research
- **라이선스**: MIT

![Diffusion 경로와 Optimal Transport 경로의 궤적 비교 - 곡선 vs 직선](figures/fig_14_1.png)
*Figure 1: Diffusion vs OT 궤적 비교 - Diffusion 경로(좌)는 곡선 궤적을 따르지만, Optimal Transport 경로(우)는 직선 궤적으로 더 효율적인 ODE 적분을 가능하게 한다. (Source: Lipman et al., 2022)*

## 아키텍처 상세

### 연속 정규화 흐름 (CNF)

CNF는 ODE를 통해 노이즈 분포 $p_0$에서 데이터 분포 $p_1$으로의 변환을 정의한다:

$$\frac{d\phi_t(x)}{dt} = v_t(\phi_t(x))$$

확률 밀도의 변환은 연속 방정식(continuity equation)을 따른다:

$$\frac{\partial p_t}{\partial t} + \nabla \cdot (u_t \cdot p_t) = 0$$

### Flow Matching 목표 함수

FM은 벡터 필드 $u_t(x)$를 직접 회귀 학습한다:

$$\mathcal{L}_{\text{FM}} = \mathbb{E}_{t \sim \mathcal{U}[0,1], x \sim p_t(x)}\left[\|v_\theta(x, t) - u_t(x)\|^2\right]$$

문제: $u_t(x)$와 $p_t(x)$를 직접 알 수 없다.

### Conditional Flow Matching (CFM)

해결책으로 조건부 변형을 제안한다:

$$\mathcal{L}_{\text{CFM}} = \mathbb{E}_{t, q(x_1), p_t(x|x_1)}\left[\|v_\theta(x, t) - u_t(x|x_1)\|^2\right]$$

핵심 정리: $\nabla_\theta \mathcal{L}_{\text{CFM}} = \nabla_\theta \mathcal{L}_{\text{FM}}$이므로, CFM은 FM과 동일한 그래디언트를 가진다.

### Optimal Transport Conditional Flow Matching (OT-CFM)

OT-CFM에서 조건부 확률 경로는 가장 단순한 직선 보간이다:

$$x_t = (1 - t) x_0 + t x_1$$

대응하는 벡터 필드는 상수:

$$u_t(x | x_1) = x_1 - x_0$$

이 직선 궤적(straight path)은 적분 시 수치 오차가 최소화되어 4~8 NFE만으로도 고품질 샘플링이 가능하다.

![OT 경로의 직선 궤적 - 노이즈에서 데이터로의 직접적 이동 경로](figures/fig_14_2.png)
*Figure 2: OT-CFM의 직선 궤적 - 각 노이즈 샘플이 대응하는 데이터 포인트까지 직선으로 이동하여, ODE 적분 시 수치 오차가 최소화된다. (Source: Lipman et al., 2022)*

| 경로 유형 | 수학적 정의 | NFE 효율 | 관련 모델 |
|----------|-----------|---------|---------|
| 직선 경로 (OT) | $x_t = (1-t)x_0 + tx_1$ | 4~8 | Flow Matching, Rectified Flow |
| VP 경로 (DDPM) | $x_t = \sqrt{\bar{\alpha}_t}x_0 + \sqrt{1-\bar{\alpha}_t}\epsilon$ | 50~100 | DDPM, DDIM |
| VE 경로 (SMLD) | $x_t = x_0 + \sigma_t \epsilon$ | 100~1000 | Score-SDE VE |

### Rectified Flow와의 관계

OT-CFM은 Rectified Flow(Xingchao Liu et al., 2022)와 수학적으로 동치이다. 두 연구는 독립적으로 동시에 발표되었으며, 동일한 직선 궤적 학습 아이디어에 도달하였다.

## 핵심 혁신

1. **시뮬레이션 없는 학습**: ODE 시뮬레이션 없이 단순 회귀로 CNF를 학습할 수 있음을 증명하였다.
2. **직선 궤적**: 최적 수송 경로를 선택하면 ODE 적분 시 수치 오차가 최소화되어 매우 적은 NFE로 고품질 생성이 가능하다.
3. **통합 프레임워크**: DDPM, Score-SDE, Rectified Flow 등 기존 확산 모델을 특수한 경우로 포함하는 일반적 프레임워크를 제시하였다.
4. **단순한 학습 목표**: $\|v_\theta(x_t, t) - (x_1 - x_0)\|^2$라는 매우 단순한 MSE 손실로 학습할 수 있다.

## 벤치마크/성능

| 방법 | 데이터셋 | FID (↓) | NFE |
|------|---------|---------|-----|
| OT-CFM | ImageNet 64 | 5.93 | 10 |
| OT-CFM | ImageNet 256 | 6.35 | 100 |
| VP-CFM (DDPM 유사) | ImageNet 64 | 6.73 | 10 |
| DDPM | ImageNet 64 | 16.4 | 10 (DDIM) |
| DDPM | ImageNet 64 | 6.95 | 100 (DDIM) |

동일한 NFE 예산에서 OT-CFM이 DDPM보다 일관되게 우수한 FID를 달성한다.

![NFE에 따른 수치 오차와 샘플 품질 비교 - FM-OT가 적은 NFE로 낮은 오차 달성](figures/fig_21_1.png)
*Figure 3: NFE 효율성 비교 - OT 경로를 사용한 Flow Matching(FM-OT)이 Diffusion 기반 방법(SM-Dif, FM-Dif) 대비 적은 NFE에서도 낮은 수치 오차를 유지한다. (Source: Lipman et al., 2022)*

## 관련 모델 비교

| 특성 | Flow Matching | DDPM | Score-SDE | Rectified Flow |
|------|-------------|------|-----------|----------------|
| 궤적 유형 | 직선 | 곡선 | 곡선 | 직선 |
| 학습 방식 | 회귀 | ELBO | Score Matching | 회귀 |
| 시뮬레이션 | 불필요 | 불필요 | 불필요 | 불필요 |
| 필요 NFE | 4-8 | 50-1000 | 50-1000 | 4-8 |
| 수학적 관계 | = OT-CFM | VP 경로 | SDE 일반화 | = OT-CFM |

## 학습 상세

- **데이터셋**: ImageNet-1k (64×64, 256×256), CelebA-HQ
- **아키텍처**: 표준 U-Net (벡터 필드 근사기)
- **노이즈 분포**: $p_0 = \mathcal{N}(0, I)$
- **데이터 분포**: $p_1 = q_{\text{data}}$
- **시간**: $t \sim \mathcal{U}[0, 1]$

## 실무 활용

![OT-CFM으로 학습한 CNF의 ImageNet-128 비조건부 생성 샘플](figures/fig_1.png)
*Figure 4: ImageNet-128 생성 결과 - OT 경로를 사용한 Flow Matching으로 학습한 CNF가 생성한 다양한 고품질 이미지 샘플. (Source: Lipman et al., 2022)*

### 1. 현대 대규모 모델의 학습 기법

SD3, Flux, Sora 등 최신 모델들이 DDPM 대신 Flow Matching을 채택하여, 더 적은 NFE로 고품질 생성을 달성하고 있다.

### 2. 빠른 추론

직선 궤적 덕분에 4~8 NFE만으로 고품질 샘플을 생성할 수 있어, 실시간 응용에 유리하다.

### 3. 다양한 도메인 확장

이미지뿐 아니라 비디오, 오디오, 분자 구조, 3D 포인트 클라우드 등 다양한 연속 데이터에 Flow Matching을 적용할 수 있다.

## 한계 및 전망

### 한계

1. **독립 커플링의 한계**: 실제 OT 커플링이 아닌 독립 커플링을 사용하므로 완벽한 직선 궤적이 보장되지 않는다.
2. **이산 데이터**: 텍스트 등 이산 데이터에 직접 적용하기 어렵다 (이산 Flow Matching 연구가 진행 중).

### 후속 발전

- **SD3 (2024)**: MMDiT + Flow Matching의 결합
- **Flux (2024)**: Hybrid DiT + Flow Matching
- **Conditional Flow Matching 확장**: Riemannian Flow Matching, Discrete Flow Matching
- **Multi-sample FM**: 미니배치 OT 커플링으로 궤적 직선성 향상

Flow Matching은 확산 모델의 학습과 샘플링을 근본적으로 재정립한 프레임워크로, DDPM 이후 가장 중요한 이론적 발전 중 하나이다.

### 기술적 의의

Flow Matching의 핵심 통찰은 "분포 간의 변환을 학습할 때, 궤적이 직선일수록 ODE 적분이 쉬워진다"는 매우 직관적인 원리이다. DDPM의 곡선 궤적(VP/VE SDE)이 수백~수천 스텝을 필요로 했던 근본적 이유가 바로 궤적의 곡률이었으며, Flow Matching은 이를 직선으로 교정함으로써 문제를 해결하였다. 이론적으로 Flow Matching은 CNF, Score-based 모델, 확률적 보간법(Stochastic Interpolation)을 모두 특수한 경우로 포함하는 통합 프레임워크이다. 실무적으로는 SD3와 Flux가 Flow Matching을 채택한 이후, 새로운 확산 모델을 설계할 때 DDPM 대신 Flow Matching을 기본으로 선택하는 것이 업계 표준이 되어가고 있다.

## 관련 문서

- [[score-sde|Score-based SDE (Stochastic Differential Equations)]] - 영감
- [[rectified-flow|Rectified Flow]] - 변형 모델
- [[flux|FLUX.1]] - 적용 모델
