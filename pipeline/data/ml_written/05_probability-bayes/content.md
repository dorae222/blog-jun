## 1. 개요: 왜 ML에서 확률론이 필수인가

머신러닝의 본질은 **불확실성(Uncertainty)의 정량화**입니다. 현실 세계의 데이터는 언제나 노이즈를 포함하고, 우리가 관측하는 정보는 항상 불완전합니다. 결정론적(Deterministic) 시스템이 "고양이인가 아닌가?"에 Yes/No만을 반환한다면, 확률론적(Probabilistic) 시스템은 "고양이일 확률 87%, 개일 확률 10%, 기타 3%"처럼 **불확실성의 정도를 함께 표현**합니다.

확률론이 ML에서 중요한 이유를 세 가지로 정리할 수 있습니다:

- **모델 불확실성 표현**: 단순 예측값이 아닌 신뢰 구간(Confidence Interval)을 제공합니다. 의료 진단에서 "암일 확률 62%"는 단순 "암이 아님"보다 훨씬 가치 있는 정보입니다.
- **지식과 데이터의 결합**: 사전 지식(Prior Knowledge)과 관측 데이터(Evidence)를 수학적으로 통합하는 베이즈 정리는 데이터가 부족한 상황에서도 합리적인 추론을 가능하게 합니다.
- **알고리즘의 이론적 토대**: 로지스틱 회귀, 나이브 베이즈, GMM, 가우시안 프로세스 등 핵심 ML 알고리즘들은 확률론적 관점에서만 완전히 이해할 수 있습니다.

이 글에서는 확률의 기초 개념부터 베이즈 정리, MLE/MAP 추정, 주요 확률 분포까지 ML 실무에 꼭 필요한 확률론의 핵심을 체계적으로 다룹니다.

---

## 2. 확률의 기초

### 2.1 결합 확률 (Joint Probability)

**결합 확률(Joint Probability)** $P(A \cap B)$ 는 사건 $A$와 $B$가 **동시에** 발생할 확률입니다. 두 변수 $X$, $Y$에 대한 결합 분포 $P(X, Y)$는 두 변수가 특정 값을 동시에 취할 확률을 나타내며, 이산 확률변수의 경우 다음이 성립합니다:

$$\sum_x \sum_y P(X=x, Y=y) = 1$$

예를 들어, 이메일의 스팸 여부($Y$)와 특정 단어 포함 여부($X$)의 결합 분포를 알면 스팸 필터의 핵심 재료를 갖게 됩니다.

### 2.2 주변 확률 (Marginal Probability)

**주변 확률(Marginal Probability)** 은 결합 분포에서 다른 변수를 "합산(Marginalize)"하여 특정 변수 하나만의 분포를 얻는 것입니다:

$$P(A) = \sum_b P(A, B=b) \quad \text{(이산)}$$
$$P(A) = \int P(A, B=b) \, db \quad \text{(연속)}$$

이 과정을 **주변화(Marginalization)** 라고 부릅니다. 예를 들어 환자의 나이와 질병 유무의 결합 분포를 알고 있을 때, 나이를 주변화하면 전체 집단에서의 질병 유병률 $P(\text{질병})$을 얻을 수 있습니다.

### 2.3 조건부 확률 (Conditional Probability)

**조건부 확률(Conditional Probability)** 은 사건 $B$가 발생했다는 정보가 주어졌을 때 사건 $A$가 발생할 확률입니다:

$$P(A|B) = \frac{P(A \cap B)}{P(B)}, \quad P(B) > 0$$

이 식은 ML에서 매우 중요합니다. "데이터 $\mathcal{D}$가 주어졌을 때 파라미터 $\theta$의 분포 $P(\theta | \mathcal{D})$"가 바로 조건부 확률의 형태이기 때문입니다.

연쇄 법칙(Chain Rule)을 이용하면 다변수 결합 분포를 조건부 확률의 곱으로 분해할 수 있습니다:

$$P(A, B, C) = P(A | B, C) \cdot P(B | C) \cdot P(C)$$

### 2.4 독립성 (Independence)

두 사건 $A$와 $B$가 **독립(Independent)** 이라면, 한 사건의 발생이 다른 사건의 확률에 전혀 영향을 주지 않습니다:

$$P(A|B) = P(A) \quad \Leftrightarrow \quad P(A \cap B) = P(A) \cdot P(B)$$

더 나아가 $A$와 $B$가 $C$가 주어졌을 때 독립이라면 **조건부 독립(Conditional Independence)** 이라 하며:

$$P(A|B, C) = P(A|C)$$

나이브 베이즈(Naive Bayes) 분류기는 각 특성(Feature)이 클래스 레이블이 주어졌을 때 조건부 독립임을 가정합니다. 이 강한 가정이 "나이브(Naive, 순진한)"라는 이름의 유래입니다.

---

## 3. 베이즈 정리

![베이즈 정리 시각화: 사전 확률, 우도, 사후 확률의 관계](figures/bayes_theorem.png)
*베이즈 정리: 사전 확률(Prior)과 우도(Likelihood)를 결합하여 사후 확률(Posterior)을 도출하는 과정을 직관적으로 보여준다.*

### 3.1 베이즈 정리의 유도

조건부 확률의 정의로부터 베이즈 정리(Bayes' Theorem)를 유도할 수 있습니다. $P(A \cap B) = P(A|B)P(B) = P(B|A)P(A)$에서:

$$P(A|B) = \frac{P(B|A) \cdot P(A)}{P(B)}$$

ML의 맥락에서 파라미터 $\theta$와 데이터 $\mathcal{D}$에 적용하면:

$$\boxed{P(\theta | \mathcal{D}) = \frac{P(\mathcal{D} | \theta) \cdot P(\theta)}{P(\mathcal{D})}}$$

각 항의 의미를 풀면:

| 항 | 이름 | 의미 |
|---|------|------|
| $P(\theta \| \mathcal{D})$ | **사후 확률 (Posterior)** | 데이터를 관측한 후 파라미터에 대한 믿음 |
| $P(\mathcal{D} \| \theta)$ | **우도 (Likelihood)** | 파라미터가 $\theta$일 때 데이터가 관측될 확률 |
| $P(\theta)$ | **사전 확률 (Prior)** | 데이터를 보기 전 파라미터에 대한 사전 믿음 |
| $P(\mathcal{D})$ | **증거 (Evidence)** | 모든 가능한 파라미터에 대한 데이터의 주변 확률 |

분모 $P(\mathcal{D}) = \int P(\mathcal{D}|\theta) P(\theta) \, d\theta$는 $\theta$에 무관한 정규화 상수이므로, 실무에서는 흔히 다음과 같이 비례 관계로 표현합니다:

$$P(\theta | \mathcal{D}) \propto P(\mathcal{D} | \theta) \cdot P(\theta)$$

> **핵심 직관**: 사후 확률(Posterior) = 우도(Likelihood) × 사전 확률(Prior)
> 데이터가 쌓일수록 우도의 영향이 커지고, 사전 확률의 영향은 점점 희석됩니다.

### 3.2 직관적 예시: 의료 진단

희귀 질병 검사를 생각해 봅시다:

- 유병률(Prior): $P(\text{질병}) = 0.001$ (1,000명 중 1명)
- 검사 민감도(True Positive Rate): $P(\text{양성}|\text{질병}) = 0.99$
- 위양성률(False Positive Rate): $P(\text{양성}|\text{정상}) = 0.05$

검사 결과가 양성일 때 실제로 질병이 있을 확률은:

$$P(\text{질병}|\text{양성}) = \frac{0.99 \times 0.001}{0.99 \times 0.001 + 0.05 \times 0.999} \approx 0.0194$$

**결과**: 양성 판정을 받아도 실제 질병 확률은 약 2%에 불과합니다. 유병률(Prior)이 매우 낮으면, 높은 정확도의 검사도 사후 확률을 크게 바꾸지 못합니다. 이것이 베이즈 정리의 놀라운 통찰입니다.

![베이지안 업데이트 과정: 데이터가 쌓이면서 사후 분포가 좁아지는 과정](figures/bayesian_update.png)
*베이지안 업데이트: 관측 데이터가 증가할수록 사후 분포가 점점 좁아지며 진짜 파라미터 값에 수렴하는 과정을 보여준다.*

### 3.3 베이즈 업데이트: 순차적 학습

베이즈 정리의 강력함은 **순차적 업데이트(Sequential Updating)** 에 있습니다. 새 데이터를 관측할 때마다 이전의 사후 확률이 새로운 사전 확률이 되어 믿음을 갱신합니다:

$$P(\theta | \mathcal{D}_1) \xrightarrow{\text{새 데이터 } \mathcal{D}_2} P(\theta | \mathcal{D}_1, \mathcal{D}_2)$$

이 성질은 온라인 학습(Online Learning)과 능동 학습(Active Learning)의 이론적 토대가 됩니다.

---

## 4. MLE vs MAP 추정

### 4.1 최대 우도 추정 (MLE)

**최대 우도 추정(Maximum Likelihood Estimation, MLE)** 은 관측된 데이터를 가장 잘 설명하는 파라미터를 찾는 방법입니다. 사전 확률 $P(\theta)$를 고려하지 않고, 오직 우도만을 최대화합니다:

$$\hat{\theta}_{\text{MLE}} = \arg\max_{\theta} P(\mathcal{D}|\theta) = \arg\max_{\theta} \prod_{i=1}^{N} P(x_i | \theta)$$

계산의 편의를 위해 로그를 취한 **로그 우도(Log-Likelihood)** 를 최대화합니다 (로그 함수가 단조 증가이므로 최적해는 동일):

$$\hat{\theta}_{\text{MLE}} = \arg\max_{\theta} \sum_{i=1}^{N} \log P(x_i | \theta)$$

**예시**: 동전을 $N$번 던져 앞면이 $k$번 나왔을 때, MLE로 추정한 앞면 확률은 $\hat{p} = k/N$입니다. 직관적으로도 자연스러운 결과입니다.

**MLE의 한계**: 데이터가 적을 때 과적합이 발생하기 쉽습니다. 동전을 3번 던져 모두 앞면이 나오면 MLE는 $\hat{p} = 1.0$으로 추정하여, 앞면이 항상 나온다고 결론 내립니다.

### 4.2 최대 사후 확률 추정 (MAP)

**최대 사후 확률 추정(Maximum A Posteriori Estimation, MAP)** 은 베이즈 정리를 이용해 사전 확률을 추가로 반영합니다:

$$\hat{\theta}_{\text{MAP}} = \arg\max_{\theta} P(\theta | \mathcal{D}) = \arg\max_{\theta} P(\mathcal{D}|\theta) \cdot P(\theta)$$

로그를 취하면:

$$\hat{\theta}_{\text{MAP}} = \arg\max_{\theta} \left[ \sum_{i=1}^{N} \log P(x_i | \theta) + \log P(\theta) \right]$$

$\log P(\theta)$ 항이 **정규화(Regularization)** 의 역할을 하여 파라미터가 극단적인 값으로 치우치는 것을 방지합니다.

**동전 예시 재방문**: 베타 분포 $\text{Beta}(\alpha, \beta)$를 사전 분포로 사용하면, MAP 추정값은 $\hat{p} = (k + \alpha - 1) / (N + \alpha + \beta - 2)$가 됩니다. $\alpha = \beta = 2$ (사전에 균등하게 기대)일 때, 3번 중 3번 앞면이 나왔다면 $\hat{p} = 4/5 = 0.8$로 훨씬 합리적인 추정을 합니다.

### 4.3 정규화와의 연결: Ridge = 가우시안 Prior MAP

**Ridge 회귀(L2 정규화)** 는 가우시안 사전 확률 $P(\mathbf{w}) = \mathcal{N}(0, \sigma_p^2 I)$을 가정한 MAP 추정과 동일합니다:

$$\hat{\mathbf{w}}_{\text{Ridge}} = \arg\min_{\mathbf{w}} \left[ \|\mathbf{y} - X\mathbf{w}\|^2 + \lambda \|\mathbf{w}\|^2 \right]$$

이것은 MAP 목적함수에서 $-\log P(\mathbf{w}) \propto \|\mathbf{w}\|^2$ (가우시안 로그 확률의 음수)로 도출됩니다. 정규화 강도 $\lambda$는 사전 분포의 분산 $\sigma_p^2$의 역수에 비례합니다.

**Lasso 회귀(L1 정규화)** 는 **라플라스 사전 확률(Laplace Prior)** $P(w_j) \propto \exp(-|w_j|/b)$를 가정한 MAP 추정에 해당합니다:

$$\hat{\mathbf{w}}_{\text{Lasso}} = \arg\min_{\mathbf{w}} \left[ \|\mathbf{y} - X\mathbf{w}\|^2 + \lambda \|\mathbf{w}\|_1 \right]$$

라플라스 분포는 가우시안보다 꼬리가 두껍고 0 근방에서 첨예(Sharp)합니다. 이 성질이 가중치를 정확히 0으로 만드는 희소 해(Sparse Solution)를 유도합니다.

| 정규화 | 사전 분포 | 특성 |
|--------|---------|------|
| Ridge (L2) | 가우시안 $\mathcal{N}(0, \sigma^2)$ | 가중치를 작게 축소, 희소하지 않음 |
| Lasso (L1) | 라플라스 $\text{Laplace}(0, b)$ | 일부 가중치를 정확히 0으로, 특성 선택 효과 |
| Elastic Net | 가우시안 + 라플라스 혼합 | L1과 L2의 장점 결합 |

---

## 5. 주요 확률 분포와 ML에서의 활용

### 5.1 정규 분포 (Normal Distribution)

$$X \sim \mathcal{N}(\mu, \sigma^2): \quad f(x) = \frac{1}{\sigma\sqrt{2\pi}} \exp\!\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)$$

정규 분포는 ML에서 가장 자주 등장하는 분포입니다:
- **선형 회귀**: 잔차(Residual) $\epsilon \sim \mathcal{N}(0, \sigma^2)$ 가정 → 최소제곱법 = MLE
- **Ridge 회귀**: 가중치의 사전 분포로 사용
- **가우시안 프로세스(Gaussian Process)**: 함수 전체에 대한 사전 분포
- **정규화 레이어(Batch Normalization)**: 활성화 분포를 정규화
- **중심 극한 정리(CLT)**: 충분히 많은 독립 확률변수의 합은 정규 분포에 수렴

### 5.2 베르누이 분포 (Bernoulli Distribution)

$$X \sim \text{Bernoulli}(p): \quad P(X=1) = p, \quad P(X=0) = 1-p$$

이진(Binary) 결과를 모델링합니다:
- **로지스틱 회귀**: 클래스 레이블 $y \in \{0, 1\}$의 분포 모델링
- **이진 분류**: 출력층 활성화 함수 시그모이드 $\sigma(z) = 1/(1+e^{-z})$는 베르누이 파라미터를 출력
- **드롭아웃(Dropout)**: 뉴런의 활성화/비활성화를 베르누이 분포로 샘플링

### 5.3 다항 분포 (Multinomial / Categorical Distribution)

$$P(X=k) = p_k, \quad \sum_{k=1}^{K} p_k = 1$$

$K$개 중 하나를 선택하는 분류 문제에 사용됩니다:
- **다중 분류**: 소프트맥스(Softmax) 함수가 다항 분포의 파라미터를 출력
- **나이브 베이즈**: 텍스트 분류에서 단어 빈도를 다항 분포로 모델링
- **LDA(Latent Dirichlet Allocation)**: 문서의 토픽 분포를 디리클레-다항 모델로 학습

### 5.4 베타 분포 (Beta Distribution)

$$X \sim \text{Beta}(\alpha, \beta): \quad f(x) = \frac{x^{\alpha-1}(1-x)^{\beta-1}}{B(\alpha, \beta)}, \quad x \in [0, 1]$$

$[0, 1]$ 범위의 확률 값 자체에 대한 분포입니다:
- **베이지안 A/B 테스트**: 전환율(Conversion Rate)의 사전/사후 분포
- **베르누이/이항 분포의 켤레 사전 분포(Conjugate Prior)**: 베타 × 우도(이항) = 베타(사후), 닫힌 형태의 업데이트 가능
- **Thompson Sampling**: 탐색-착취 균형을 위한 베이지안 강화학습

### 5.5 켤레 사전 분포 (Conjugate Prior)

우도와 사전 분포가 동일한 함수형(Functional Form)의 사후 분포를 만들 때, 이를 **켤레(Conjugate)** 쌍이라 합니다. 이 성질은 베이즈 추론을 해석적(Analytically)으로 풀 수 있게 해줍니다:

| 우도 | 켤레 사전 분포 | 사후 분포 |
|------|------------|--------|
| 이항 (Binomial) | 베타 (Beta) | 베타 (Beta) |
| 정규 (Normal, 평균 추정) | 정규 (Normal) | 정규 (Normal) |
| 다항 (Multinomial) | 디리클레 (Dirichlet) | 디리클레 (Dirichlet) |
| 포아송 (Poisson) | 감마 (Gamma) | 감마 (Gamma) |

---

## 6. Python 코드: 분포 시각화와 베이즈 업데이트

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# ── 1. 주요 확률 분포 시각화 ──────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(12, 9))
fig.suptitle('ML에서 자주 쓰이는 확률 분포', fontsize=15)

x = np.linspace(-4, 4, 300)

# 정규 분포
ax = axes[0, 0]
for mu, sigma, label in [(0, 1, 'N(0,1)'), (0, 2, 'N(0,4)'), (1, 0.5, 'N(1,0.25)')]:
    ax.plot(x, stats.norm.pdf(x, mu, sigma), label=label, lw=2)
ax.set_title('정규 분포 (Normal)')
ax.legend()
ax.set_xlabel('x'); ax.set_ylabel('PDF')

# 베타 분포
ax = axes[0, 1]
x_beta = np.linspace(0.001, 0.999, 300)
for a, b, label in [(1, 1, 'Beta(1,1)'), (2, 5, 'Beta(2,5)'), (5, 2, 'Beta(5,2)'), (2, 2, 'Beta(2,2)')]:
    ax.plot(x_beta, stats.beta.pdf(x_beta, a, b), label=label, lw=2)
ax.set_title('베타 분포 (Beta)')
ax.legend(fontsize=8)
ax.set_xlabel('p'); ax.set_ylabel('PDF')

# 이항 분포 (Binomial)
ax = axes[1, 0]
k = np.arange(0, 21)
for n, p, label in [(20, 0.3, 'Binom(20,0.3)'), (20, 0.5, 'Binom(20,0.5)'), (20, 0.7, 'Binom(20,0.7)')]:
    ax.bar(k + (0.2 * [0.3, 0.5, 0.7].index(p) - 0.2),
           stats.binom.pmf(k, n, p), width=0.2, alpha=0.7, label=label)
ax.set_title('이항 분포 (Binomial)')
ax.legend(fontsize=8)
ax.set_xlabel('k (성공 횟수)'); ax.set_ylabel('PMF')

# 라플라스 vs 정규 (Lasso vs Ridge prior)
ax = axes[1, 1]
for dist, label, color in [
    (stats.norm(0, 1), '가우시안 (Ridge prior)', 'steelblue'),
    (stats.laplace(0, 1/np.sqrt(2)), '라플라스 (Lasso prior)', 'coral')
]:
    ax.plot(x, dist.pdf(x), label=label, lw=2, color=color)
ax.set_title('사전 분포 비교: Ridge vs Lasso')
ax.legend(fontsize=9)
ax.set_xlabel('w'); ax.set_ylabel('PDF')

plt.tight_layout()
plt.savefig('probability_distributions.png', dpi=150, bbox_inches='tight')
plt.show()

# ── 2. 베이즈 업데이트 시뮬레이션 (동전 예시) ──────────────────────
# 사전 분포: Beta(2, 2), 균등에 가깝지만 극단은 억제
# 관측: 진짜 p = 0.7인 동전을 점진적으로 던짐

np.random.seed(42)
true_p = 0.7
alpha_prior, beta_prior = 2, 2
observations = np.random.binomial(1, true_p, size=100)  # 100번 시뮬레이션

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
fig.suptitle('베이즈 업데이트: 동전 앞면 확률 추정', fontsize=13)

steps = [5, 20, 100]  # 관측 횟수
x_p = np.linspace(0, 1, 300)

for ax, n_obs in zip(axes, steps):
    data = observations[:n_obs]
    heads = data.sum()
    tails = n_obs - heads

    # 켤레 사전: Beta(α, β) + 이항 우도 → Beta(α + heads, β + tails)
    alpha_post = alpha_prior + heads
    beta_post  = beta_prior  + tails

    # MLE 추정
    mle_estimate = heads / n_obs
    # MAP 추정 (Beta의 최빈값)
    map_estimate = (alpha_post - 1) / (alpha_post + beta_post - 2)

    ax.plot(x_p, stats.beta.pdf(x_p, alpha_prior, beta_prior),
            'b--', lw=1.5, alpha=0.6, label=f'Prior Beta({alpha_prior},{beta_prior})')
    ax.plot(x_p, stats.beta.pdf(x_p, alpha_post, beta_post),
            'r-', lw=2.5, label=f'Posterior Beta({alpha_post},{beta_post})')
    ax.axvline(true_p, color='green', lw=2, linestyle=':', label=f'True p={true_p}')
    ax.axvline(mle_estimate, color='orange', lw=1.5, linestyle='--',
               label=f'MLE={mle_estimate:.2f}')
    ax.axvline(map_estimate, color='purple', lw=1.5, linestyle='-.',
               label=f'MAP={map_estimate:.2f}')

    ax.set_title(f'N={n_obs}번 관측 (앞면={heads}회)')
    ax.set_xlabel('p (앞면 확률)')
    ax.set_ylabel('밀도')
    ax.legend(fontsize=7)
    ax.set_xlim(0, 1)

plt.tight_layout()
plt.savefig('bayes_update.png', dpi=150, bbox_inches='tight')
plt.show()

# ── 3. MLE vs MAP 비교 (적은 데이터에서의 차이) ────────────────────
print("\n=== MLE vs MAP 비교 (적은 데이터) ===")
for n_flip in [3, 10, 30, 100]:
    data = observations[:n_flip]
    heads = data.sum()
    mle = heads / n_flip
    map_est = (alpha_prior + heads - 1) / (alpha_prior + beta_prior + n_flip - 2)
    print(f"N={n_flip:3d}, 앞면={heads:2d} | MLE={mle:.3f}, MAP={map_est:.3f} (진짜 p={true_p})")
```

```output
=== MLE vs MAP 비교 (적은 데이터) ===
N=  3, 앞면= 1 | MLE=0.333, MAP=0.400 (진짜 p=0.7)
N= 10, 앞면= 6 | MLE=0.600, MAP=0.583 (진짜 p=0.7)
N= 30, 앞면=23 | MLE=0.767, MAP=0.750 (진짜 p=0.7)
N=100, 앞면=70 | MLE=0.700, MAP=0.696 (진짜 p=0.7)
```

![베이즈 정리와 확률 분포 시각화](figures/bayes_theorem.png)

*Figure 1: 확률 분포 시각화: 정규, 베타, 이항 분포의 파라미터별 형태와 Ridge/Lasso의 사전 분포 차이를 비교한다.*

![베이지안 업데이트 과정](figures/bayesian_update.png)

*Figure 2: 베이지안 업데이트: 데이터가 늘어날수록 사후 분포가 좁아지며 진짜 확률에 수렴하는 과정을 보여준다.*

코드를 실행하면 두 가지 핵심 결과를 얻습니다:

1. **분포 시각화**: 정규, 베타, 이항 분포의 파라미터별 형태와 Ridge/Lasso의 사전 분포 차이를 직접 확인합니다. 라플라스 분포가 가우시안보다 0 근방에서 훨씬 뾰족하다는 것이 L1 희소성의 원인임을 시각적으로 이해할 수 있습니다.

2. **베이즈 업데이트**: 데이터가 늘어날수록 사후 분포(Posterior)가 좁아지며 진짜 확률에 수렴합니다. 데이터가 적을 때(N=5) MLE는 불안정하지만, MAP는 사전 분포 덕분에 더 안정적인 추정을 보입니다. N=100이 되면 MLE와 MAP 모두 비슷하게 수렴합니다.

---

## 정리

확률론은 ML의 언어입니다. 이 글에서 다룬 핵심을 정리합니다:

1. **결합·주변·조건부 확률**은 ML 알고리즘의 기본 언어입니다. 특히 조건부 확률 $P(y|x)$는 지도학습의 모든 분류/회귀 문제의 수학적 표현입니다.

2. **베이즈 정리** $P(\theta|\mathcal{D}) \propto P(\mathcal{D}|\theta)P(\theta)$는 사전 지식(Prior)과 데이터(Likelihood)를 결합하여 파라미터에 대한 최선의 믿음(Posterior)을 도출합니다.

3. **MLE**는 우도만을 최대화하며 데이터가 충분할 때 강력합니다. **MAP**는 사전 분포를 추가하여 데이터가 적을 때도 안정적인 추정을 제공하며, 정규화(Regularization)의 확률론적 토대가 됩니다.

4. **Ridge = 가우시안 Prior MAP, Lasso = 라플라스 Prior MAP**임을 이해하면, 정규화 기법을 단순한 트릭이 아닌 확률론적 추론의 관점에서 파악할 수 있습니다.

5. **주요 분포들**(정규, 베르누이, 다항, 베타)은 각각 고유한 ML 컨텍스트에서 활용되며, 켤레 사전 분포의 개념은 베이지안 추론을 효율적으로 만들어 줍니다.

> **다음 글 안내**: 확률과 정보의 관계를 다루는 정보 이론(엔트로피, KL 발산, 상호 정보량)은 [[information-theory]]를, 나이브 베이즈 분류기의 실제 구현은 [[naive-bayes]]를 참고하세요. 베이지안 ML의 심화 내용은 [[bayesian-ml]]에서 다룹니다.

## 관련 문서

- [[naive-bayes|나이브 베이즈 분류기]]
- [[information-theory|정보 이론: 엔트로피와 KL 발산]]
- [[bayesian-ml|베이지안 머신러닝]]
- [[logistic-regression|로지스틱 회귀와 조건부 확률]]
- [[regularized-regression|Ridge와 Lasso 정규화 회귀]]