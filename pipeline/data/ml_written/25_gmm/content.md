<!-- infographic-hero -->
![Gaussian Mixture Models (GMM) 핵심 요약](figures/infographic.svg)

*Figure: Gaussian Mixture Models (GMM) 한 장 요약 인포그래픽*

## 개요

**가우시안 혼합 모델(Gaussian Mixture Model, GMM)**은 데이터가 $K$개의 가우시안 분포가 혼합된 형태로 생성된다고 가정하는 생성 모델이자 확률적 군집화 알고리즘입니다.

K-Means가 각 데이터 포인트를 하나의 클러스터에만 할당하는 **Hard Clustering**인 반면, GMM은 각 포인트가 모든 클러스터에 속할 확률을 계산하는 **Soft Clustering**을 수행합니다. 이를 통해 타원형 형태의 클러스터, 서로 다른 크기와 밀도를 가진 클러스터, 그리고 겹치는 클러스터까지 훨씬 유연하게 모델링할 수 있습니다.

GMM은 군집화뿐만 아니라 밀도 추정(Density Estimation), 이상치 탐지(Anomaly Detection), 생성 모델의 기반으로도 폭넓게 활용됩니다.

---

## 수학적 배경

### GMM 확률 밀도 함수

GMM은 $K$개의 가우시안 성분(Component)의 가중 합으로 전체 데이터의 확률 밀도를 표현합니다.

$$p(x) = \sum_{k=1}^{K} \pi_k \, \mathcal{N}(x \mid \mu_k, \Sigma_k)$$

각 기호의 의미는 다음과 같습니다.

- $\pi_k$: $k$번째 성분의 **혼합 가중치(Mixing Weight)**. $\sum_{k=1}^{K} \pi_k = 1$, $\pi_k \geq 0$ 조건을 만족합니다.
- $\mu_k$: $k$번째 가우시안 분포의 **평균 벡터**
- $\Sigma_k$: $k$번째 가우시안 분포의 **공분산 행렬**
- $\mathcal{N}(x \mid \mu_k, \Sigma_k)$: 다변수 가우시안 분포의 확률 밀도 함수

다변수 가우시안의 확률 밀도 함수는 다음과 같이 정의됩니다.

$$\mathcal{N}(x \mid \mu, \Sigma) = \frac{1}{(2\pi)^{d/2} |\Sigma|^{1/2}} \exp\left(-\frac{1}{2}(x - \mu)^T \Sigma^{-1} (x - \mu)\right)$$

### 잠재 변수와 사후 확률(Responsibility)

각 데이터 포인트 $x_i$가 $k$번째 성분에서 생성되었을 사후 확률, 즉 **Responsibility** $r_{ik}$는 베이즈 정리로 계산합니다.

$$r_{ik} = p(z_i = k \mid x_i) = \frac{\pi_k \, \mathcal{N}(x_i \mid \mu_k, \Sigma_k)}{\sum_{j=1}^{K} \pi_j \, \mathcal{N}(x_i \mid \mu_j, \Sigma_j)}$$

이 $r_{ik}$ 값이 Soft Clustering의 핵심으로, 각 데이터 포인트가 각 클러스터에 속할 확률을 나타냅니다.

---

![GMM 등고선: 가우시안 혼합 모델의 타원형 클러스터와 확률 등고선](figures/gmm_contours.png)
*GMM 등고선: 각 가우시안 성분의 평균과 공분산으로 정의된 타원형 등고선이 데이터의 밀도 분포를 확률적으로 표현한다.*

## 알고리즘: EM (Expectation-Maximization)

GMM의 파라미터 $\{\pi_k, \mu_k, \Sigma_k\}_{k=1}^{K}$는 직접 해석적으로 풀 수 없기 때문에, **EM 알고리즘**을 이용해 로그-우도(Log-Likelihood)를 반복적으로 최대화합니다.

$$\log p(X) = \sum_{i=1}^{N} \log \left( \sum_{k=1}^{K} \pi_k \, \mathcal{N}(x_i \mid \mu_k, \Sigma_k) \right)$$

### E-Step (Expectation): Responsibility 계산

현재 파라미터를 고정한 상태에서, 각 데이터 포인트가 각 성분에 속할 사후 확률을 계산합니다.

$$r_{ik} = \frac{\pi_k \, \mathcal{N}(x_i \mid \mu_k, \Sigma_k)}{\sum_{j=1}^{K} \pi_j \, \mathcal{N}(x_i \mid \mu_j, \Sigma_j)}$$

### M-Step (Maximization): 파라미터 업데이트

E-Step에서 계산한 $r_{ik}$를 고정한 후, 파라미터를 업데이트합니다.

각 성분의 유효 데이터 수 $N_k = \sum_{i=1}^{N} r_{ik}$를 정의하면,

$$\mu_k^{\text{new}} = \frac{1}{N_k} \sum_{i=1}^{N} r_{ik} \, x_i$$

$$\Sigma_k^{\text{new}} = \frac{1}{N_k} \sum_{i=1}^{N} r_{ik} (x_i - \mu_k^{\text{new}})(x_i - \mu_k^{\text{new}})^T$$

$$\pi_k^{\text{new}} = \frac{N_k}{N}$$

E-Step과 M-Step을 로그-우도가 수렴할 때까지 반복합니다.

### K-Means와 GMM 비교

| 항목 | K-Means | GMM |
|------|---------|-----|
| 할당 방식 | Hard (0 or 1) | Soft (확률) |
| 클러스터 형태 | 구형(Spherical) | 타원형(Elliptical) |
| 파라미터 | 중심점 $\mu_k$ | $\pi_k, \mu_k, \Sigma_k$ |
| 이론적 기반 | 거리 최소화 | 최대 우도 추정 |
| 밀도 추정 | 불가 | 가능 |

### 공분산 구조 선택

sklearn의 `GaussianMixture`는 `covariance_type` 파라미터로 공분산 구조를 제어합니다.

- **full**: 각 성분이 완전한 공분산 행렬을 가짐. 가장 유연하지만 파라미터 수가 많음.
- **tied**: 모든 성분이 동일한 공분산 행렬을 공유.
- **diag**: 대각 공분산 행렬. 특성 간 상관관계 무시.
- **spherical**: 각 성분이 단일 분산값 사용. K-Means에 가장 가까운 형태.

---

## Python 구현

### 기본 GMM 피팅 및 클러스터 할당

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from sklearn.datasets import make_blobs

# 샘플 데이터 생성 (3개의 클러스터)
X, y_true = make_blobs(
    n_samples=300,
    centers=[[0, 0], [3, 3], [6, 0]],
    cluster_std=[0.8, 1.2, 0.6],
    random_state=42
)

# GMM 모델 학습
gmm = GaussianMixture(
    n_components=3,
    covariance_type='full',
    n_init=5,         # 여러 초기값 시도
    random_state=42
)
gmm.fit(X)

# Hard 클러스터 레이블
labels = gmm.predict(X)

# Soft 클러스터 확률 (각 포인트가 각 클러스터에 속할 확률)
proba = gmm.predict_proba(X)
print("첫 번째 샘플의 클러스터 소속 확률:", proba[0].round(4))

# 학습된 파라미터 확인
print("\n혼합 가중치 (pi_k):", gmm.weights_.round(4))
print("클러스터 평균 (mu_k):\n", gmm.means_.round(4))
```

```output
첫 번째 샘플의 클러스터 소속 확률: [0.000e+00 9.999e-01 1.000e-04]

혼합 가중치 (pi_k): [0.3448 0.3401 0.315 ]
클러스터 평균 (mu_k):
 [[ 5.9528 -0.0372]
 [-0.0864  0.065 ]
 [ 3.1365  3.1487]]
```

### BIC/AIC로 최적 K 선택

최적의 성분 수 $K$를 선택할 때는 **BIC(Bayesian Information Criterion)** 또는 **AIC(Akaike Information Criterion)**를 사용합니다. 두 지표 모두 낮을수록 더 좋은 모델을 의미합니다.

```python
# K 범위에 대해 BIC/AIC 계산
k_range = range(1, 10)
bic_scores = []
aic_scores = []

for k in k_range:
    gmm = GaussianMixture(
        n_components=k,
        covariance_type='full',
        n_init=3,
        random_state=42
    )
    gmm.fit(X)
    bic_scores.append(gmm.bic(X))
    aic_scores.append(gmm.aic(X))

# 최적 K 선택
best_k_bic = k_range[np.argmin(bic_scores)]
best_k_aic = k_range[np.argmin(aic_scores)]
print(f"BIC 기준 최적 K: {best_k_bic}")
print(f"AIC 기준 최적 K: {best_k_aic}")

# BIC/AIC 곡선 시각화
plt.figure(figsize=(8, 4))
plt.plot(k_range, bic_scores, 'o-', label='BIC', color='steelblue')
plt.plot(k_range, aic_scores, 's--', label='AIC', color='tomato')
plt.axvline(x=best_k_bic, color='steelblue', linestyle=':', alpha=0.7)
plt.xlabel('클러스터 수 K')
plt.ylabel('정보 기준 값')
plt.title('BIC/AIC를 이용한 최적 K 선택')
plt.legend()
plt.tight_layout()
plt.show()
```

```output
BIC 기준 최적 K: 3
AIC 기준 최적 K: 3
```

![GMM 등고선과 BIC 선택](figures/bic_model_selection.png)

*Figure 1: BIC/AIC 모델 선택: 성분 수에 따른 BIC/AIC 값 변화와 최적 K=3 결정 과정을 보여준다.*

### 이상치 탐지 활용

```python
# 학습 데이터로 GMM 피팅
gmm_anomaly = GaussianMixture(n_components=3, covariance_type='full', random_state=42)
gmm_anomaly.fit(X)

# 각 샘플의 로그-우도 점수 계산
log_likelihood = gmm_anomaly.score_samples(X)

# 하위 5%를 이상치로 판단
threshold = np.percentile(log_likelihood, 5)
anomalies = X[log_likelihood < threshold]
normal = X[log_likelihood >= threshold]

print(f"이상치 탐지 임계값 (로그-우도): {threshold:.4f}")
print(f"이상치 수: {len(anomalies)}, 정상 샘플 수: {len(normal)}")
```

```output
이상치 탐지 임계값 (로그-우도): -5.2621
이상치 수: 15, 정상 샘플 수: 285
```

---

![BIC 모델 선택: 성분 수에 따른 BIC/AIC 값 변화와 최적 K 결정](figures/bic_model_selection.png)
*BIC 모델 선택: BIC와 AIC 곡선에서 최솟값을 보이는 성분 수를 최적 K로 선택하며, BIC가 과적합 방지에 더 보수적인 기준을 제공한다.*

## 시각화

### 가우시안 타원형 클러스터 시각화

```python
import matplotlib.patches as mpatches
from matplotlib.patches import Ellipse

def draw_ellipse(position, covariance, ax, n_std=2.0, **kwargs):
    """공분산 행렬로부터 타원형 신뢰 구간을 그립니다."""
    # 고유값 분해로 타원의 축과 각도 계산
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = eigenvalues.argsort()[::-1]
    eigenvalues, eigenvectors = eigenvalues[order], eigenvectors[:, order]
    angle = np.degrees(np.arctan2(*eigenvectors[:, 0][::-1]))
    width, height = 2 * n_std * np.sqrt(eigenvalues)
    ellipse = Ellipse(xy=position, width=width, height=height,
                      angle=angle, **kwargs)
    ax.add_patch(ellipse)

# 최적 K로 GMM 재학습
gmm_final = GaussianMixture(n_components=3, covariance_type='full', random_state=42)
gmm_final.fit(X)
labels_final = gmm_final.predict(X)

fig, ax = plt.subplots(figsize=(8, 6))
colors = ['steelblue', 'tomato', 'seagreen']

for k, color in enumerate(colors):
    mask = labels_final == k
    ax.scatter(X[mask, 0], X[mask, 1], c=color, s=20, alpha=0.6,
               label=f'Cluster {k+1}')
    # 1σ, 2σ 타원 시각화
    for n_std, alpha in [(1.0, 0.3), (2.0, 0.15)]:
        draw_ellipse(gmm_final.means_[k], gmm_final.covariances_[k],
                     ax, n_std=n_std, facecolor=color, alpha=alpha)

ax.scatter(gmm_final.means_[:, 0], gmm_final.means_[:, 1],
           c='black', s=100, marker='x', zorder=5, label='Centroids')
ax.set_title('GMM 클러스터링 결과 (타원형 신뢰 구간)')
ax.legend()
plt.tight_layout()
plt.show()
```

![GMM 클러스터링 결과](figures/gmm_contours.png)

*Figure 2: GMM 클러스터링 결과: 가우시안 혼합 모델의 타원형 신뢰 구간(1σ, 2σ)과 각 클러스터의 중심점을 시각화한다.*

---

## 실전 팁

### K-Means의 한계 극복

K-Means는 구형(spherical) 클러스터만 인식할 수 있고, 클러스터 크기와 밀도가 모두 동일하다고 가정합니다. GMM은 공분산 행렬 $\Sigma_k$를 통해 타원형 클러스터와 서로 다른 밀도를 자연스럽게 처리합니다. 특히 실제 데이터에서 클러스터가 겹치는 경우, Soft Assignment 덕분에 경계 영역의 불확실성을 확률적으로 표현할 수 있습니다.

### 이상치 탐지 활용

`score_samples()` 메서드는 각 샘플의 로그-우도를 반환합니다. 정상 분포에서 벗어난 샘플은 로그-우도가 매우 낮으므로, 하위 백분위수를 임계값으로 설정해 이상치를 탐지할 수 있습니다. 이 방법은 단변수/다변수 이상치 탐지 모두에 효과적입니다.

### 수렴 문제 대응

GMM은 초기값에 민감하며 로컬 최적해에 빠질 수 있습니다. 이를 완화하기 위해 `n_init` 파라미터로 여러 초기화를 시도하고, `init_params='kmeans'`(기본값)로 K-Means 결과를 초기값으로 활용하는 것이 권장됩니다. 또한 `reg_covar` 파라미터(기본값 `1e-6`)는 공분산 행렬이 특이 행렬(Singular Matrix)이 되는 것을 방지하는 정규화 항입니다.

### 성분 수 선택 전략

- **BIC 우선**: 과적합 패널티가 강해 일반적으로 BIC가 더 안정적인 K를 선택합니다.
- **도메인 지식 활용**: 데이터의 실제 의미를 고려해 K의 범위를 제한합니다.
- **시각적 확인**: 2D/3D로 투영 후 타원형 클러스터가 실제 데이터 구조를 잘 표현하는지 확인합니다.
- **엘보우 방법**: BIC/AIC 곡선에서 감소 폭이 급격히 줄어드는 지점(Elbow)을 최적 K로 선택합니다.

### covariance_type 선택 가이드

데이터 차원이 높거나 샘플이 적을 때는 `full` 대신 `diag` 또는 `tied`를 사용해 파라미터 수를 줄이고 과적합을 방지하세요. 반대로 충분한 데이터가 있고 클러스터 간 형태 차이가 크다면 `full`이 가장 표현력 있는 선택입니다.