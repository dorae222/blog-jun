## 개요

전통적인 머신러닝은 파라미터를 하나의 고정된 값으로 추정합니다. 예를 들어 선형 회귀에서 최적 가중치 $w^*$를 최소제곱법으로 구하면 그 값이 '정답'으로 간주됩니다. 하지만 현실에서는 데이터가 부족하거나 노이즈가 많은 경우가 흔하며, 이런 상황에서 단일 점 추정(point estimate)은 과신(overconfidence)을 낳습니다.

**베이지안 머신러닝(Bayesian Machine Learning)**은 이 문제를 근본적으로 다르게 접근합니다. 파라미터 자체를 확률 변수로 보고, 데이터를 관찰한 후 파라미터에 대한 **믿음(belief)**을 확률 분포 형태로 업데이트합니다. 이를 통해 세 가지 핵심 강점을 얻습니다.

- **불확실성 정량화**: 예측값뿐 아니라 그 예측이 얼마나 불확실한지도 함께 출력합니다.
- **사전 지식 활용**: 도메인 지식이나 이전 실험 결과를 Prior로 녹여낼 수 있습니다.
- **소용량 데이터에 강함**: 데이터가 적어도 Prior가 정규화(regularization) 역할을 하여 과적합을 억제합니다.

---

## 수학적 배경

### 베이즈 정리

모든 베이지안 추론의 출발점은 **베이즈 정리**입니다.

$$p(\theta | D) = \frac{p(D | \theta)\, p(\theta)}{p(D)} \propto p(D | \theta)\, p(\theta)$$

각 항의 의미는 다음과 같습니다.

| 항 | 명칭 | 의미 |
|---|---|---|
| $p(\theta)$ | Prior (사전 분포) | 데이터를 보기 전 파라미터에 대한 믿음 |
| $p(D \| \theta)$ | Likelihood (우도) | 파라미터 $\theta$ 하에서 데이터 $D$가 관측될 확률 |
| $p(\theta \| D)$ | Posterior (사후 분포) | 데이터를 관측한 후 업데이트된 파라미터의 분포 |
| $p(D)$ | Evidence (증거) | 정규화 상수, 계산 비용이 큰 주범 |

### Conjugate Prior

Prior와 Likelihood의 함수형이 맞아서 Posterior가 Prior와 같은 분포족에 속하는 경우를 **Conjugate Prior**라 합니다. 예를 들어 Likelihood가 가우시안이면 Prior도 가우시안으로 설정하면 Posterior 역시 가우시안이 됩니다. 이를 통해 적분 계산 없이 닫힌 형태(closed-form)의 Posterior를 얻을 수 있습니다.

### Bayesian Linear Regression

입력 $X \in \mathbb{R}^{N \times D}$, 출력 $y \in \mathbb{R}^N$, 가중치 $w \in \mathbb{R}^D$에 대해:

$$y = Xw + \epsilon, \quad \epsilon \sim \mathcal{N}(0, \sigma^2 I)$$

Prior를 $p(w) = \mathcal{N}(0, \alpha^{-1}I)$로 설정하면, Posterior도 가우시안이 됩니다.

$$p(w | X, y) = \mathcal{N}(w | m_N, S_N)$$

$$S_N = \left(\alpha I + \frac{1}{\sigma^2} X^T X\right)^{-1}, \quad m_N = \frac{1}{\sigma^2} S_N X^T y$$

새로운 입력 $x^*$에 대한 예측 분포는:

$$p(y^* | x^*, X, y) = \mathcal{N}\left(y^* \mid m_N^T x^*,\; (x^*)^T S_N x^* + \sigma^2\right)$$

예측 분산 $(x^*)^T S_N x^* + \sigma^2$는 **모델 불확실성**(epistemic)과 **데이터 노이즈**(aleatoric)를 모두 담습니다.

---

## 주요 알고리즘

### 1. MAP vs Full Bayesian

**MAP(Maximum A Posteriori)**는 Posterior를 최대화하는 단일 점 $\hat{w}_{MAP} = \arg\max_w p(w|D)$를 구합니다. L2 정규화 선형 회귀와 수학적으로 동일하며, 계산이 빠르지만 불확실성 정보를 잃습니다.

**Full Bayesian**은 Posterior 전체를 유지하고 예측 시 적분합니다. 불확실성 전파가 가능하지만 계산 비용이 큽니다.

### 2. Gaussian Process (GP)

**가우시안 프로세스**는 함수에 대한 분포를 직접 정의하는 비모수적(non-parametric) 베이지안 방법입니다. 임의의 유한 점 집합에서의 함수값이 결합 가우시안 분포를 따른다고 가정합니다.

$$f(x) \sim \mathcal{GP}(m(x),\, k(x, x'))$$

- $m(x)$: 평균 함수 (보통 0으로 설정)
- $k(x, x')$: **커널 함수(공분산 함수)** — 두 점 사이의 유사성을 정의

대표적인 커널 함수:
- **RBF (Radial Basis Function)**: $k(x, x') = \sigma_f^2 \exp\left(-\frac{\|x - x'\|^2}{2l^2}\right)$
- **Matérn**: 비평탄(non-smooth) 함수 모델링에 적합
- **Linear**: 선형 관계 가정

GP 예측 분포는 닫힌 형태로 계산됩니다.

$$p(f^* | x^*, X, y) = \mathcal{N}(\mu^*, \Sigma^*)$$

$$\mu^* = K_{*}(K + \sigma^2 I)^{-1}y, \quad \Sigma^* = K_{**} - K_*(K + \sigma^2 I)^{-1}K_*^T$$

### 3. MCMC (Markov Chain Monte Carlo)

Posterior가 닫힌 형태로 계산되지 않을 때 사용하는 **샘플링 기반** 근사 방법입니다. Markov Chain을 구성해 Posterior 분포에서 샘플을 뽑고, 그 샘플로 기댓값·분산 등을 추정합니다. 대표 알고리즘으로 Metropolis-Hastings, HMC(Hamiltonian Monte Carlo), NUTS가 있습니다. **Stan**, **PyMC** 등이 MCMC를 사용합니다.

### 4. Variational Inference (VI)

MCMC보다 빠른 **최적화 기반** 근사 방법입니다. 다루기 쉬운 분포族 $q(\theta)$를 정의하고, KL Divergence $\text{KL}(q \| p)$를 최소화해 Posterior $p(\theta|D)$에 가장 가까운 $q^*$를 찾습니다. **ELBO(Evidence Lower Bound)**를 최대화하는 방식으로 구현됩니다. **Pyro**, **TensorFlow Probability**에서 자동 미분과 결합해 대규모 데이터에도 적용 가능합니다.

---

## Python 구현

### Bayesian Ridge Regression (scikit-learn)

```python
import numpy as np
from sklearn.linear_model import BayesianRidge
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split

# 데이터 생성
X, y = make_regression(n_samples=100, n_features=5, noise=10, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Bayesian Ridge 학습
model = BayesianRidge(
    max_iter=300,
    tol=1e-3,
    fit_intercept=True
)
model.fit(X_train, y_train)

# 예측 + 불확실성
y_pred, y_std = model.predict(X_test, return_std=True)

print(f"예측값 (첫 5개): {y_pred[:5].round(2)}")
print(f"예측 표준편차 (첫 5개): {y_std[:5].round(2)}")
print(f"추정된 alpha (precision): {model.alpha_:.4f}")
print(f"추정된 lambda (weight precision): {model.lambda_:.4f}")
```

```output
예측값 (첫 5개): [ 177.52 -292.33  111.49  178.35  400.5 ]
예측 표준편차 (첫 5개): [ 9.52 10.1   9.7   9.84 10.06]
추정된 alpha (precision): 0.0115
추정된 lambda (weight precision): 0.0002
```

### Gaussian Process Regression (scikit-learn)

```python
import numpy as np
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, WhiteKernel

np.random.seed(42)

# 학습 데이터: 스파스하게 샘플링
X_train = np.sort(np.random.uniform(0, 10, 15)).reshape(-1, 1)
y_train = np.sin(X_train).ravel() + np.random.normal(0, 0.2, X_train.shape[0])

# 커널 정의: RBF + 노이즈
kernel = RBF(length_scale=1.0, length_scale_bounds=(1e-2, 10.0)) \
       + WhiteKernel(noise_level=0.1, noise_level_bounds=(1e-5, 1.0))

# GP 학습 (커널 하이퍼파라미터는 MLE로 자동 최적화)
gpr = GaussianProcessRegressor(
    kernel=kernel,
    n_restarts_optimizer=10,
    normalize_y=True
)
gpr.fit(X_train, y_train)

# 예측
X_test = np.linspace(0, 10, 200).reshape(-1, 1)
y_pred, y_std = gpr.predict(X_test, return_std=True)

print(f"최적화된 커널: {gpr.kernel_}")
print(f"Log-Marginal-Likelihood: {gpr.log_marginal_likelihood_value_:.3f}")
```

```output
최적화된 커널: RBF(length_scale=0.873) + WhiteKernel(noise_level=0.185)
Log-Marginal-Likelihood: -17.783
```

---

## 시각화: Gaussian Process 예측 구간

```python
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.family'] = 'AppleGothic'  # macOS 한글 폰트

fig, ax = plt.subplots(figsize=(10, 5))

# 실제 함수
X_true = np.linspace(0, 10, 300)
y_true = np.sin(X_true)
ax.plot(X_true, y_true, 'k--', linewidth=1.5, label='실제 함수 sin(x)', alpha=0.6)

# 학습 데이터
ax.scatter(X_train, y_train, color='black', s=60, zorder=5, label='학습 데이터')

# GP 예측 평균
ax.plot(X_test.ravel(), y_pred, color='royalblue', linewidth=2, label='GP 예측 평균')

# 불확실성 띠: 1σ, 2σ
ax.fill_between(
    X_test.ravel(),
    y_pred - 2 * y_std,
    y_pred + 2 * y_std,
    alpha=0.2, color='royalblue', label='95% 신뢰 구간 (±2σ)'
)
ax.fill_between(
    X_test.ravel(),
    y_pred - y_std,
    y_pred + y_std,
    alpha=0.35, color='royalblue', label='68% 신뢰 구간 (±1σ)'
)

ax.set_xlabel('x')
ax.set_ylabel('y')
ax.set_title('Gaussian Process 회귀: 예측 불확실성 시각화')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('gp_uncertainty.png', dpi=150)
plt.show()
```

![Bayesian-Ml Fig 1](/media/figures/outputs/bayesian-ml/bayesian-ml_fig_1.png)

시각화 결과에서 주목할 포인트:
- 학습 데이터 근처: 불확실성 띠가 좁아짐 (데이터가 충분)
- 데이터가 없는 구간: 불확실성 띠가 넓어짐 (모델이 스스로 모른다고 표현)
- 이 **자기 인식(self-awareness)**이 베이지안 방법의 가장 큰 실용적 가치입니다.

---

## 실전 팁

### 언제 베이지안 방법을 선택할까?

| 상황 | 권장 방법 | 이유 |
|---|---|---|
| 데이터 수백 건 이하 | 베이지안 | Prior가 정규화 역할, 과적합 억제 |
| 예측 불확실성이 비즈니스 결정에 필요 | 베이지안 | 신뢰 구간 제공 |
| 의료/금융 등 위험 민감 도메인 | 베이지안 | 잘못된 자신감 방지 |
| 데이터 수백만 건, 속도 우선 | 빈도주의/딥러닝 | 베이지안은 계산 비용 큼 |
| 실시간 스트리밍 데이터 | 온라인 베이지안 업데이트 고려 | Posterior를 Prior로 재활용 |

### 계산 비용 문제

GP의 경우 행렬 역산 $O(N^3)$이 병목이며, 학습 데이터 수가 수천을 넘으면 느려집니다. 이를 해결하는 방법:
- **Sparse GP**: 가상 유도점(inducing point)으로 근사
- **Deep Kernel Learning**: 딥러닝으로 특징 추출 후 GP 적용
- **Variational GP** (GPyTorch): GPU 가속 + Variational Inference 결합

### 주요 라이브러리

| 라이브러리 | 언어 | 특징 |
|---|---|---|
| **scikit-learn** | Python | BayesianRidge, GaussianProcessRegressor — 입문용 |
| **GPy** | Python | GP 전문 라이브러리, 다양한 커널 |
| **GPyTorch** | Python (PyTorch) | GPU 가속 GP, 대규모 데이터 대응 |
| **PyMC** | Python | MCMC 기반 전체 베이지안 모델링 |
| **Stan** | DSL + R/Python 인터페이스 | HMC/NUTS, 연구/학술 표준 |
| **Pyro** | Python (PyTorch) | VI + MCMC, 딥러닝과 자연스럽게 결합 |
| **TensorFlow Probability** | Python (TF) | 대규모 VI, 구글 생태계 |

### 베이지안 워크플로 권장 순서

1. **Prior 설계** — 도메인 지식 반영, Prior Predictive Check로 타당성 검증
2. **모델 적합** — MAP → Full Bayesian 순서로 점진적으로 복잡도 높이기
3. **Posterior 진단** — R-hat, ESS(유효 샘플 수) 확인 (MCMC 사용 시)
4. **Posterior Predictive Check** — 모델이 실제 데이터 분포를 재현하는지 확인
5. **모델 비교** — WAIC, LOO-CV로 모델 선택

---

## 정리

베이지안 머신러닝은 단순히 "또 다른 회귀 알고리즘"이 아닙니다. 불확실성을 일급 시민(first-class citizen)으로 다루는 **통계적 사고의 전환**입니다. 데이터가 풍부하고 속도가 우선인 환경에서는 딥러닝이 강하지만, 데이터가 희소하거나 예측의 신뢰도가 중요한 의사결정에 직결될 때 베이지안 접근은 대체 불가능한 도구입니다. Gaussian Process로 시작해 점차 PyMC나 Pyro로 확장해 나가는 경로가 실무 학습에 권장됩니다.