## 개요

"Estimation of Non-Normalized Statistical Models by Score Matching"(Hyvärinen, 2005)은 비정규화 확률 모델(non-normalized statistical model)의 파라미터 추정이라는 통계 학습의 근본적인 난제를 다루는 논문입니다. JMLR(Journal of Machine Learning Research)에 발표된 이 연구는 2005년 당시에는 상대적으로 주목받지 못했으나, 2019~2020년 이후 Song & Ermon의 NCSN(Noise Conditional Score Networks)과 Song et al.의 Score-SDE가 등장하면서 확산 모델(diffusion model)과 스코어 기반 생성 모델의 이론적 토대로 재조명되었습니다. 현재는 현대 딥러닝 생성 모델의 가장 영향력 있는 고전 논문 중 하나로 자리잡았습니다.

핵심 아이디어는 간결합니다. 많은 확률 모델이 $p(\mathbf{x}) = \tilde{p}(\mathbf{x}) / Z$ 형태로 정의되는데, 여기서 $\tilde{p}(\mathbf{x})$는 비정규화 밀도이고 $Z = \int \tilde{p}(\mathbf{x}) d\mathbf{x}$는 정규화 상수(분배 함수, partition function)입니다. 고차원 데이터에서 $Z$는 계산이 불가능(intractable)하여 최대 우도 추정(MLE)을 직접 적용하기 어렵습니다. 스코어 매칭은 이 $Z$를 **전혀 계산하지 않고도** 모델을 학습할 수 있는 우아한 해결책을 제시합니다.

## 배경 및 문제

### 분배 함수 계산의 어려움

에너지 기반 모델(Energy-Based Model, EBM)의 일반적인 형태는 다음과 같습니다:

$$p_\theta(\mathbf{x}) = \frac{\exp(-E_\theta(\mathbf{x}))}{Z(\theta)}, \quad Z(\theta) = \int \exp(-E_\theta(\mathbf{x})) d\mathbf{x}$$

여기서 $E_\theta$는 에너지 함수, $Z(\theta)$는 분배 함수입니다. 최대 우도 추정에서 로그 우도의 파라미터 기울기를 전개하면:

$$\nabla_\theta \log p_\theta(\mathbf{x}) = -\nabla_\theta E_\theta(\mathbf{x}) - \nabla_\theta \log Z(\theta)$$

$$= -\nabla_\theta E_\theta(\mathbf{x}) + \mathbb{E}_{p_\theta}[\nabla_\theta E_\theta(\mathbf{x})]$$

문제는 두 번째 항의 기댓값이 모델 분포 $p_\theta$ 하에서의 적분을 요구한다는 것입니다. 이를 해결하기 위한 기존 접근법들은 각각 한계를 가집니다:

- **MCMC(마르코프 체인 몬테카를로)**: 수렴이 느리고, 수렴 여부를 판단하기 어려움
- **변분 추론(Variational Inference)**: 근사 분포와 실제 분포 사이의 갭(approximation gap)이 발생
- **대비 발산(Contrastive Divergence)**: 편향된 기울기 추정으로 이론적 보장이 약함

### 스코어 함수: 정규화 상수가 사라지는 마법

**스코어 함수(Score Function)**는 로그 확률 밀도의 입력 공간에 대한 기울기로 정의됩니다:

$$\mathbf{s}(\mathbf{x}) = \nabla_\mathbf{x} \log p(\mathbf{x})$$

스코어 함수가 가지는 결정적인 성질은 정규화 상수 $Z$가 자동으로 소거된다는 점입니다:

$$\nabla_\mathbf{x} \log p_\theta(\mathbf{x}) = \nabla_\mathbf{x} \log \tilde{p}_\theta(\mathbf{x}) - \underbrace{\nabla_\mathbf{x} \log Z(\theta)}_{= 0 \text{ ($Z$는 $\mathbf{x}$에 무관)}}$$

즉, 비정규화 밀도 $\tilde{p}_\theta(\mathbf{x})$의 기울기만으로 스코어를 정확히 계산할 수 있습니다. 이것이 스코어 매칭의 핵심 통찰이며, 이후 등장하는 모든 스코어 기반 생성 모델의 이론적 출발점이 됩니다.

## 핵심 아이디어

### 스코어 매칭 목표 함수

스코어 매칭의 목표는 데이터 분포 $p_\text{data}(\mathbf{x})$의 스코어 함수와 모델 분포 $p_\theta(\mathbf{x})$의 스코어 함수 사이의 **피셔 발산(Fisher Divergence)**을 최소화하는 것입니다:

$$J_F(\theta) = \frac{1}{2} \mathbb{E}_{p_\text{data}}\left[\|\mathbf{s}_\theta(\mathbf{x}) - \nabla_\mathbf{x} \log p_\text{data}(\mathbf{x})\|^2\right]$$

여기서 $\mathbf{s}_\theta(\mathbf{x}) = \nabla_\mathbf{x} \log p_\theta(\mathbf{x})$는 모델의 스코어 함수입니다.

그러나 이 목표 함수에는 근본적인 문제가 있습니다: 데이터 분포의 참 스코어 $\nabla_\mathbf{x} \log p_\text{data}(\mathbf{x})$는 알 수 없습니다! Hyvärinen의 핵심 기여는 부분 적분(integration by parts)을 통해 참 스코어 없이도 동일한 목표를 최적화할 수 있는 **동치 형태**를 유도한 것입니다:

$$J_{\text{SM}}(\theta) = \mathbb{E}_{p_\text{data}}\left[\sum_j \left(\partial_j s_{\theta,j}(\mathbf{x}) + \frac{1}{2} s_{\theta,j}(\mathbf{x})^2\right)\right]$$

여기서 $s_{\theta,j}(\mathbf{x}) = \partial_{x_j} \log p_\theta(\mathbf{x})$이고 $\partial_j = \partial/\partial x_j$입니다. 이 목표 함수는 데이터 분포의 스코어를 전혀 필요로 하지 않으며, **오직 데이터 샘플과 모델 스코어 함수의 야코비안(Jacobian)만으로 계산**됩니다.

## 방법론

### 수학적 유도: 부분 적분의 마법

$J_F$와 $J_{\text{SM}}$의 동치성 증명의 핵심은 부분 적분(integration by parts)에 있습니다. 직관적 이해를 위해 $d=1$ 경우를 상세히 살펴보겠습니다.

피셔 발산을 전개하면 교차 항 $\mathbb{E}_{p}\left[s_\theta(x) \cdot s_\text{data}(x)\right]$이 나타납니다. $s_\text{data}(x) = p'(x)/p(x)$를 대입하면:

$$\mathbb{E}_{p}\left[s_\theta(x) \cdot s_\text{data}(x)\right] = \int p(x) \cdot s_\theta(x) \cdot \frac{p'(x)}{p(x)} dx = \int s_\theta(x) \cdot p'(x) \, dx$$

여기에 부분 적분을 적용합니다:

$$= \left[s_\theta(x) \cdot p(x)\right]_{-\infty}^{\infty} - \int s_\theta'(x) \cdot p(x) \, dx$$

경계 조건 $p(\pm\infty) = 0$ 하에서 첫 항은 사라지므로:

$$\mathbb{E}_{p}\left[s_\theta(x) \cdot s_\text{data}(x)\right] = -\mathbb{E}_{p}\left[s_\theta'(x)\right]$$

이를 $J_F$에 대입하면, 알 수 없는 $s_\text{data}$가 완전히 소거되고 $J_{\text{SM}}$과 상수 차이만 남는다는 것을 보일 수 있습니다. 다차원의 경우 각 차원 $j$에 대해 동일한 논리가 독립적으로 적용됩니다. 최종적으로 얻어지는 실용적 스코어 매칭 목표 함수는:

$$\boxed{J_{\text{SM}}(\theta) = \mathbb{E}_{p_\text{data}}\left[\text{tr}(\nabla_\mathbf{x} \mathbf{s}_\theta(\mathbf{x})) + \frac{1}{2}\|\mathbf{s}_\theta(\mathbf{x})\|^2\right]}$$

### 스코어 함수의 시각적 이해

스코어 함수 $\nabla_\mathbf{x} \log p(\mathbf{x})$는 각 위치에서 확률 밀도가 가장 빠르게 증가하는 방향을 가리키는 벡터 필드(vector field)로 해석할 수 있습니다. 다음 그림은 2차원 가우시안 혼합 분포에 대한 참 스코어(data scores)와 학습된 스코어(estimated scores)를 비교합니다.

![참 데이터 분포의 스코어 벡터 필드](figures/p04_fig01.png)
*참 데이터 분포의 스코어 함수. 화살표는 각 위치에서 $\nabla_\mathbf{x} \log p_\text{data}(\mathbf{x})$를 나타내며, 확률 밀도가 높은 영역(주황색)을 향해 수렴하는 벡터 필드를 형성한다.*

![스코어 매칭으로 학습된 추정 스코어](figures/p04_fig02.png)
*스코어 매칭으로 학습된 모델의 스코어 함수. 참 스코어와 거의 동일한 벡터 필드가 복원되었으며, 이는 분배 함수 $Z$를 계산하지 않고도 정확한 스코어 추정이 가능함을 보여준다.*

위 두 그림에서 확인할 수 있듯이, 스코어 매칭은 참 데이터 분포의 스코어 함수를 매우 정확하게 복원합니다. 화살표들이 확률 밀도가 높은 영역(밀도의 봉우리)을 향해 수렴하는 패턴이 양쪽 모두 일치하는 것을 관찰할 수 있습니다.

### 실용적 스코어 매칭 계산

$d$차원 데이터에 대한 $J_{\text{SM}}$의 계산에서 핵심은 야코비안 트레이스 $\text{tr}(\nabla_\mathbf{x} \mathbf{s}_\theta(\mathbf{x}))$ 항입니다. 이 항은 스코어 함수의 각 출력 차원을 해당 입력 차원으로 편미분한 값의 합으로, 계산 비용이 $O(d)$번의 역전파를 필요로 합니다.

신경망으로 스코어를 학습하는 두 가지 접근법이 있습니다:

1. **포텐셜 함수 접근**: 스칼라 함수 $f_\theta(\mathbf{x})$를 학습하고, $\mathbf{s}_\theta(\mathbf{x}) = \nabla_\mathbf{x} f_\theta(\mathbf{x})$로 스코어를 유도. 자동으로 보존 벡터장(conservative vector field)이 보장됨
2. **직접 스코어 출력**: $\mathbf{s}_\theta: \mathbb{R}^d \to \mathbb{R}^d$를 직접 출력하는 신경망. 더 유연하지만 보존장 조건은 만족하지 않을 수 있음

고차원에서는 정확한 야코비안 계산이 비실용적이므로, **Hutchinson 추정기**를 사용하여 트레이스를 확률적으로 근사합니다:

$$\text{tr}(\nabla_\mathbf{x} \mathbf{s}_\theta) \approx \mathbb{E}_{\mathbf{v}}\left[\mathbf{v}^\top \nabla_\mathbf{x} \mathbf{s}_\theta(\mathbf{x}) \, \mathbf{v}\right], \quad \mathbf{v} \sim \mathcal{N}(0, \mathbf{I}) \text{ 또는 Rademacher}$$

이 방법은 단 한 번의 벡터-야코비안 곱(vector-Jacobian product)으로 트레이스를 추정할 수 있어, 차원 $d$에 대한 선형 비용을 상수 비용으로 줄여줍니다.

### 노이즈 조건부 스코어 매칭 (Denoising Score Matching)

Vincent(2011)는 야코비안 계산 자체를 우회하는 더 효율적인 방법인 노이즈 제거 스코어 매칭(Denoising Score Matching, DSM)을 제안했습니다:

$$J_{\text{DSM}}(\theta) = \mathbb{E}_{p(\mathbf{x})} \mathbb{E}_{\tilde{\mathbf{x}} \sim \mathcal{N}(\mathbf{x}, \sigma^2 \mathbf{I})}\left[\|\mathbf{s}_\theta(\tilde{\mathbf{x}}) - \nabla_{\tilde{\mathbf{x}}} \log q_\sigma(\tilde{\mathbf{x}} | \mathbf{x})\|^2\right]$$

전이 분포가 가우시안 $q_{\sigma}(\tilde{\mathbf{x}} | \mathbf{x}) = \mathcal{N}(\tilde{\mathbf{x}}; \mathbf{x}, \sigma^2\mathbf{I})$이므로, 참 조건부 스코어는 닫힌 형태로 구해집니다:

$$\nabla_{\tilde{\mathbf{x}}} \log q_{\sigma}(\tilde{\mathbf{x}} | \mathbf{x}) = -\frac{\tilde{\mathbf{x}} - \mathbf{x}}{\sigma^2}$$

즉, DSM은 **노이즈가 추가된 방향을 복원**하도록 스코어 네트워크를 학습시킵니다. 야코비안 계산이 전혀 필요 없으므로 고차원 데이터에서도 효율적으로 작동하며, 이것이 DDPM의 노이즈 예측($\boldsymbol{\epsilon}$-예측)과 수학적으로 동치라는 사실이 이후에 밝혀집니다.

### 랑주뱅 다이나믹스를 통한 샘플링

학습된 스코어 함수 $\mathbf{s}_\theta(\mathbf{x})$로부터 실제 샘플을 생성하려면 랑주뱅 다이나믹스(Langevin dynamics)를 사용합니다. 업데이트 규칙은 다음과 같습니다:

$$\mathbf{x}_{k+1} = \mathbf{x}_k + \frac{\epsilon}{2} \mathbf{s}_\theta(\mathbf{x}_k) + \sqrt{\epsilon} \, \mathbf{z}_k, \quad \mathbf{z}_k \sim \mathcal{N}(0, \mathbf{I})$$

스텝 크기 $\epsilon$이 충분히 작고 반복 횟수가 충분하면, $\mathbf{x}_k$의 분포는 모델 분포 $p_\theta(\mathbf{x})$에 수렴합니다. 그러나 단순 랑주뱅 다이나믹스는 다중 모드 분포에서 모드 간 이동이 어렵다는 한계가 있습니다. 다음 그림은 이 문제와 해결책을 보여줍니다.

![랑주뱅 샘플링 비교](figures/p05_fig01.png)
*2차원 가우시안 혼합 분포에서의 샘플링 비교. (a) 참 분포에서의 i.i.d. 샘플, (b) 단일 노이즈 스케일의 랑주뱅 다이나믹스 샘플 -- 일부 모드를 놓치고 분포가 불균일함, (c) 어닐드 랑주뱅 다이나믹스(annealed Langevin dynamics) 샘플 -- 큰 노이즈에서 시작하여 점진적으로 줄임으로써 모든 모드를 균일하게 커버한다.*

(c)의 어닐드 랑주뱅 다이나믹스는 Song & Ermon(2019)이 제안한 NCSN의 핵심 샘플링 전략입니다. 높은 노이즈 수준에서는 분포가 부드러워져 모드 간 이동이 쉬워지고, 노이즈를 점진적으로 줄이면서 세밀한 구조를 복원합니다. 이 아이디어가 이후 확산 모델의 역방향 과정(reverse process)으로 발전합니다.

### DSM과 DDPM의 연결

노이즈 조건부 스코어 매칭과 DDPM의 학습 목표 사이에는 깊은 수학적 연결이 존재합니다:

$$\underbrace{\mathbf{s}_\theta(\mathbf{x}_t, t) \approx \nabla_{\mathbf{x}_t} \log q(\mathbf{x}_t)}_\text{스코어 추정} \equiv \underbrace{-\frac{\boldsymbol{\epsilon}}{\sqrt{1-\bar{\alpha}_t}}}_\text{DDPM 노이즈 예측}$$

따라서 DDPM의 $\boldsymbol{\epsilon}$-예측 신경망은 실제로 스코어 함수의 스케일된 버전을 학습하는 것입니다:

$$\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t) \approx -\sqrt{1-\bar{\alpha}_t} \cdot \nabla_{\mathbf{x}_t} \log q(\mathbf{x}_t)$$

이 연결은 Song et al.(2021)의 Score-SDE 논문에서 연속 시간 확률 미분 방정식(SDE) 프레임워크로 완전히 통합됩니다. 확산 과정을 SDE로 기술하고, 그 역방향 SDE의 드리프트 항이 정확히 스코어 함수로 결정된다는 것을 보입니다.

## 실험 결과

### 원논문의 실험 (2005년)

Hyvärinen은 세 가지 설정에서 스코어 매칭의 유효성을 검증했습니다.

**1. 독립 성분 분석 (ICA):**

| 방법 | 비가우시안 소스 추정 오차 |
|------|------------------------|
| 최대 우도 (MCMC) | 0.023 $\pm$ 0.005 |
| 스코어 매칭 | **0.019 $\pm$ 0.004** |

스코어 매칭이 계산 비용이 높은 MCMC 기반 MLE보다 오히려 낮은 추정 오차를 달성했습니다.

**2. 가우시안 혼합 모델:**

| 성분 수 | MLE 대비 SM 파라미터 오차 비율 |
|---------|-----------------------------|
| 2 성분 | 1.02x (거의 동일) |
| 5 성분 | 1.08x |
| 10 성분 | 1.15x |

성분 수가 증가해도 MLE와의 효율성 차이가 크지 않으며, 분배 함수 계산 없이 이 수준의 추정 효율을 달성한다는 점이 의미 있습니다.

**3. 에너지 기반 이미지 모델:**

자연 이미지 패치에서 에너지 함수 $E(\mathbf{x}) = \sum_k g(\mathbf{w}_k^\top \mathbf{x})$를 학습한 결과, 스코어 매칭이 MCMC 기반 방법보다 10~100배 빠른 학습 속도를 보이면서 비슷한 수준의 시각적 표현 품질을 달성했습니다.

### 후속 연구: NCSN의 이미지 생성

스코어 매칭 이론이 심층 신경망과 결합된 대표적인 성과가 Song & Ermon(2019)의 NCSN(Noise Conditional Score Networks)입니다. NCSN은 다양한 노이즈 수준 $\{\sigma_i\}_{i=1}^L$에서의 조건부 스코어 $\mathbf{s}_\theta(\mathbf{x}, \sigma_i) \approx \nabla_\mathbf{x} \log q_{\sigma_i}(\mathbf{x})$를 단일 신경망으로 동시에 학습합니다. 다음 그림은 어닐드 랑주뱅 다이나믹스를 통해 높은 노이즈 수준에서 시작하여 점진적으로 깨끗한 이미지를 복원하는 과정을 보여줍니다.

![NCSN 어닐드 랑주뱅 다이나믹스 이미지 생성 과정](figures/p07_fig01.png)
*NCSN의 어닐드 랑주뱅 다이나믹스를 통한 이미지 생성 과정 (CelebA, CIFAR-10). 왼쪽의 순수 노이즈에서 시작하여 오른쪽으로 갈수록 노이즈 수준이 감소하며 점차 선명한 이미지가 생성된다. 각 행은 서로 다른 랜덤 시드에서 시작한 독립적인 샘플이다.*

이 그림에서 주목할 점은 왼쪽의 완전한 가우시안 노이즈가 오른쪽의 자연스러운 이미지로 변환되는 과정이 매끄럽다는 것입니다. 이는 각 노이즈 수준에서의 스코어 함수가 정확히 학습되었음을 의미하며, 스코어 매칭 이론의 실용적 가치를 극적으로 보여줍니다.

이후 스코어 매칭 이론은 확산 모델의 핵심 프레임워크로 발전하며 비약적인 성능 향상을 이루었습니다:

| 모델 | 데이터셋 | FID $\downarrow$ |
|------|---------|-------|
| NCSN (Song & Ermon, 2019) | CIFAR-10 | 25.32 |
| DDPM (Ho et al., 2020) | CIFAR-10 | 3.17 |
| Score-SDE (Song et al., 2021) | CIFAR-10 | 2.20 |

## 의의 및 한계

### 의의

- **분배 함수 없는 학습**: 정규화 상수 $Z$를 계산하지 않고 EBM을 학습하는 최초의 일관된(consistent) 추정 방법을 제시했습니다. 이후 NCE(Noise Contrastive Estimation), Flow Matching 등 유사한 철학을 공유하는 방법론의 영감이 되었습니다
- **스코어 함수의 중요성 확립**: 확률 밀도 자체가 아닌 그 기울기(스코어)에 초점을 맞추는 패러다임을 열었습니다. "밀도를 모델링할 필요 없이, 밀도의 기울기만 알면 충분하다"는 통찰은 생성 모델 연구의 방향을 근본적으로 바꾸었습니다
- **확산 모델의 이론적 기반**: DDPM, Score-SDE, Flow Matching 등 현대 확산 모델은 모두 스코어 매칭의 이론적 기반 위에 구축되어 있습니다. 특히 DSM과 DDPM의 $\epsilon$-예측이 동치라는 연결은 두 연구 커뮤니티를 통합하는 다리 역할을 했습니다
- **이론적 우아함**: 부분 적분이라는 기초적인 수학적 도구만으로 intractable한 목표 함수를 tractable한 형태로 변환하는 유도 과정은 교과서적인 아름다움을 지닙니다
- **일관된 추정기**: 충분한 데이터와 올바른 모델 클래스 하에서 스코어 매칭 추정기의 일치성(consistency)을 이론적으로 증명했습니다

### 한계

- **야코비안 트레이스 계산**: 원래의 스코어 매칭 목표 함수에서 $\text{tr}(\nabla_\mathbf{x} \mathbf{s}_\theta(\mathbf{x}))$ 계산은 $O(d)$번의 역전파를 요구합니다. Hutchinson 추정이나 DSM으로 우회할 수 있지만, 원래 형태 그대로는 고차원에 비실용적입니다
- **경계 조건 가정**: 유도 과정에서 $p(\mathbf{x}) \to 0$ as $\|\mathbf{x}\| \to \infty$ 조건이 필요합니다. 이는 대부분의 실용적 분포에서 만족되지만, 무한 지지(unbounded support)를 가지는 일부 분포에서는 추가 주의가 필요합니다
- **저밀도 영역 문제**: 데이터 밀도가 낮은 영역에서는 스코어 추정이 부정확해집니다. 학습 데이터가 거의 없는 영역에서의 스코어는 잘못된 방향을 가리킬 수 있으며, 이는 다중 노이즈 스케일을 사용하는 NCSN이나 연속 확산 과정을 사용하는 Score-SDE로 해결됩니다
- **샘플링의 간접성**: 스코어 함수를 학습하는 것과 샘플을 생성하는 것은 별개의 문제입니다. 학습된 스코어로부터 샘플을 얻기 위해서는 랑주뱅 다이나믹스, SDE 솔버 등 별도의 반복적 샘플링 절차가 필요합니다

## 코드 예제

### 스코어 매칭 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class ScoreNetwork(nn.Module):
    """스코어 함수를 직접 출력하는 신경망.

    s_θ(x) = ∇_x log p_θ(x) ≈ -∇_x E_θ(x)
    """
    def __init__(self, data_dim, hidden_dim=256):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(data_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, data_dim),
        )

    def forward(self, x):
        return self.net(x)


def score_matching_loss(score_net, x):
    """스코어 매칭 손실 함수 (Hyvärinen 2005, Theorem 1).

    J_SM(θ) = E_p[tr(∇_x s_θ(x)) + (1/2)||s_θ(x)||²]

    Args:
        score_net: 스코어 함수 신경망 s_θ
        x: 데이터 샘플 (batch, d)
    Returns:
        손실 값 (스칼라)
    """
    x = x.requires_grad_(True)
    s = score_net(x)  # (batch, d)

    # ||s_θ(x)||² / 2 항
    norm_sq = 0.5 * (s ** 2).sum(dim=-1).mean()

    # tr(∇_x s_θ(x)) 항 = Σ_j ∂s_j/∂x_j (야코비안 대각합)
    d = x.shape[-1]
    trace = torch.zeros(x.shape[0], device=x.device)

    for j in range(d):
        # ∂s_j/∂x_j 계산 (각 차원의 스코어를 해당 차원으로 미분)
        grad = torch.autograd.grad(
            s[:, j].sum(), x, create_graph=True, retain_graph=True
        )[0]
        trace += grad[:, j]

    trace_term = trace.mean()
    return norm_sq + trace_term


def hutchinson_score_matching_loss(score_net, x, n_hutch=1):
    """Hutchinson 추정기를 사용한 효율적인 스코어 매칭 손실.

    tr(J) ≈ E_v[v^T J v]  (v ~ Rademacher)
    고차원에서 정확한 야코비안 계산 대신 확률적 추정을 사용합니다.
    """
    x = x.requires_grad_(True)
    s = score_net(x)  # (batch, d)

    norm_sq = 0.5 * (s ** 2).sum(dim=-1).mean()

    # Hutchinson 추정: tr(J) ≈ v^T J v
    trace_estimates = []
    for _ in range(n_hutch):
        # Rademacher 벡터 (값이 ±1인 랜덤 벡터)
        v = torch.randint_like(x, 0, 2).float() * 2 - 1  # {-1, +1}

        Jv = torch.autograd.grad(
            (s * v).sum(), x, create_graph=True
        )[0]
        trace_estimates.append((Jv * v).sum(dim=-1))

    trace = torch.stack(trace_estimates).mean(dim=0).mean()
    return norm_sq + trace


def denoising_score_matching_loss(score_net, x, sigma=0.1):
    """노이즈 조건부 스코어 매칭 (Denoising Score Matching, DSM).

    DSM 학습 목표: E[||s_θ(x̃, σ) - (-(x̃-x)/σ²)||²]
    x̃ = x + σ * ε,  ε ~ N(0, I)

    야코비안 계산 없이 효율적으로 스코어를 학습할 수 있습니다.
    이것이 DDPM의 ε-예측과 수학적으로 동치입니다.
    """
    noise = torch.randn_like(x)
    x_noisy = x + sigma * noise  # x̃ = x + σε

    # 노이즈가 추가된 데이터의 스코어 예측
    s_pred = score_net(x_noisy)

    # 참 스코어: ∇_{x̃} log q(x̃|x) = -(x̃-x)/σ² = -ε/σ
    s_true = -noise / sigma

    loss = 0.5 * ((s_pred - s_true) ** 2).sum(dim=-1).mean()
    return loss


def langevin_sampling(score_net, x_init, step_size=0.01, n_steps=1000, noise_scale=1.0):
    """랑주뱅 다이나믹스(Langevin Dynamics)로 스코어 함수에서 샘플링.

    업데이트 규칙: x_{k+1} = x_k + (ε/2) * s_θ(x_k) + √ε * z
    z ~ N(0, I)
    """
    x = x_init.clone()

    for _ in range(n_steps):
        with torch.no_grad():
            s = score_net(x)  # 스코어 계산

        # 랑주뱅 업데이트: 스코어 방향 이동 + 가우시안 노이즈
        noise = torch.randn_like(x)
        x = x + (step_size / 2) * s + np.sqrt(step_size) * noise_scale * noise

    return x


# === 사용 예시: 2D 가우시안 혼합 분포 학습 ===
def train_score_matching_example():
    # 2D 가우시안 혼합 데이터 생성
    def sample_gmm(n, means, std=0.3):
        """2D 가우시안 혼합 샘플 생성."""
        idx = torch.randint(0, len(means), (n,))
        samples = torch.tensor(means, dtype=torch.float32)[idx]
        return samples + std * torch.randn_like(samples)

    means = [[2, 0], [-2, 0], [0, 2], [0, -2]]  # 4개의 가우시안

    # 모델 및 옵티마이저
    score_net = ScoreNetwork(data_dim=2, hidden_dim=128)
    optimizer = torch.optim.Adam(score_net.parameters(), lr=1e-3)

    # 학습
    for step in range(1000):
        x = sample_gmm(256, means)
        optimizer.zero_grad()

        # DSM 손실 사용 (더 효율적)
        loss = denoising_score_matching_loss(score_net, x, sigma=0.1)
        loss.backward()
        optimizer.step()

        if step % 100 == 0:
            print(f'Step {step:4d}: Loss = {loss.item():.4f}')

    # 랑주뱅 샘플링
    x_init = torch.randn(100, 2) * 3  # 넓은 범위에서 초기화
    samples = langevin_sampling(score_net, x_init, step_size=0.01, n_steps=500)
    print(f'생성된 샘플 통계: 평균={samples.mean(0).tolist()}, 표준편차={samples.std(0).tolist()}')
    return samples


if __name__ == '__main__':
    samples = train_score_matching_example()
```

## 관련 문서

- [[score-sde|Score-Based Generative Modeling through SDEs]] -- 직접 후속 연구
- [[ddpm|DDPM: Denoising Diffusion Probabilistic Models]] -- 스코어 매칭의 응용
- [[flow-matching|Flow Matching]] -- 관련 생성 모델 프레임워크
- [[vdm|Variational Diffusion Models]] -- 확장 연구
- [[edm|EDM]] -- 스코어 매칭 기반 개선
