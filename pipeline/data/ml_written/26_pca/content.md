## 개요: 왜 차원 축소가 필요한가

현실 세계의 데이터는 대부분 고차원입니다. 유전체 연구에서 하나의 샘플은 수만 개의 유전자 발현 값을 갖고, 이미지 한 장은 수백만 픽셀로 이루어지며, 사용자 행동 데이터는 수천 개의 피처를 포함할 수 있습니다. 이처럼 차원이 높아질수록 여러 문제가 발생합니다.

첫째, **차원의 저주(Curse of Dimensionality)**입니다. 차원이 증가할수록 동일한 데이터 밀도를 유지하기 위해 필요한 샘플 수가 기하급수적으로 늘어납니다. 결과적으로 고차원 공간에서는 데이터 포인트들이 서로 멀리 떨어져 희박하게 분포하게 되어, 거리 기반 알고리즘의 성능이 급격히 저하됩니다.

둘째, **다중공선성(Multicollinearity)** 문제입니다. 피처들 사이에 강한 상관관계가 존재하면 모델이 불안정해지고, 계수 해석이 어려워집니다.

셋째, **계산 비용**과 **시각화의 어려움**입니다. 고차원 데이터를 그대로 다루면 학습 시간이 길어지고, 2차원이나 3차원으로 시각화할 수 없어 데이터의 패턴을 직관적으로 파악하기 어렵습니다.

**주성분 분석(PCA, Principal Component Analysis)**은 이러한 문제를 해결하기 위한 가장 고전적이고 강력한 차원 축소 기법입니다. PCA는 데이터의 분산(정보량)을 최대한 보존하면서 저차원 표현을 찾습니다. 원본 피처들의 선형 결합으로 새로운 축(주성분)을 만들어, 중요한 정보는 살리고 불필요한 중복과 노이즈는 제거합니다.

---

![PCA 2D 투영: 고차원 데이터를 상위 2개 주성분으로 투영한 산점도](figures/pca_2d_projection.png)
*PCA 2D 투영: 고차원 데이터를 상위 2개 주성분 축으로 투영하여 클래스 간 분리와 데이터 구조를 시각화한다.*

## PCA의 직관: 분산이 정보다

PCA의 핵심 아이디어는 놀랍도록 단순합니다. **데이터가 가장 넓게 퍼져 있는 방향이 가장 많은 정보를 담고 있는 방향**이라는 것입니다.

간단한 예시를 생각해봅시다. 키와 몸무게 데이터가 있다고 할 때, 이 두 변수는 강한 양의 상관관계를 가집니다. 2차원 산점도에서 데이터는 특정 방향(오른쪽 위)으로 길게 늘어진 타원형 분포를 보입니다. 이 타원의 **장축 방향**이 데이터가 가장 많이 퍼져 있는 방향, 즉 분산이 최대인 방향입니다. 이것이 첫 번째 주성분(PC1)입니다.

PC1 방향과 **직교(수직)**하는 방향, 즉 타원의 단축 방향이 두 번째 주성분(PC2)입니다. PC2는 PC1이 설명하지 못한 나머지 분산을 최대화합니다.

이처럼 주성분들은 다음 두 가지 성질을 만족합니다:

1. **분산 최대화**: 각 주성분은 이전 주성분들이 설명하지 못한 분산 중 최대를 설명합니다.
2. **직교성(Orthogonality)**: 모든 주성분 쌍은 서로 직교합니다. 이는 주성분들 사이에 선형 상관관계가 없음을 의미합니다.

결과적으로 데이터를 상위 $k$개의 주성분 축으로 투영하면, $d$차원 데이터를 $k$차원($k \ll d$)으로 축소하면서도 대부분의 정보(분산)를 보존할 수 있습니다.

---

## 수학적 유도

### 1단계: 데이터 중심화 (Centering)

$N$개의 $d$차원 데이터 포인트로 구성된 행렬 $X \in \mathbb{R}^{N \times d}$에서 시작합니다. 먼저 각 피처의 평균을 0으로 만드는 **중심화(Centering)**를 수행합니다:

$$\tilde{X} = X - \bar{X}, \quad \bar{X}_{ij} = \frac{1}{N} \sum_{i=1}^{N} X_{ij}$$

중심화는 PCA가 원점에서부터 분산 방향을 탐색할 수 있도록 데이터를 이동시킵니다. 스케일이 다른 피처들이 있을 경우(예: 키 cm vs 몸무게 kg), 표준편차로 나누는 **표준화(Standardization)**도 함께 수행하는 것이 일반적입니다.

### 2단계: 공분산 행렬 계산

중심화된 데이터 $\tilde{X}$의 **공분산 행렬(Covariance Matrix)** $\Sigma \in \mathbb{R}^{d \times d}$는 다음과 같이 계산됩니다:

$$\Sigma = \frac{1}{N-1} \tilde{X}^T \tilde{X}$$

공분산 행렬의 $(i, j)$ 원소 $\sigma_{ij}$는 $i$번째와 $j$번째 피처 사이의 공분산을 나타냅니다. 대각 원소 $\sigma_{ii}$는 $i$번째 피처의 분산입니다. $\Sigma$는 대칭 행렬(Symmetric Matrix)이며 양의 반정부호(Positive Semi-Definite) 행렬입니다.

### 3단계: 고유값 분해 (Eigendecomposition)

공분산 행렬 $\Sigma$에 **고유값 분해(Eigendecomposition)**를 적용합니다:

$$\Sigma = Q \Lambda Q^T$$

- $Q \in \mathbb{R}^{d \times d}$: 열이 고유벡터(Eigenvector)인 직교 행렬 ($Q^T Q = I$)
- $\Lambda = \text{diag}(\lambda_1, \lambda_2, \ldots, \lambda_d)$: 고유값이 내림차순으로 정렬된 대각 행렬 ($\lambda_1 \geq \lambda_2 \geq \cdots \geq \lambda_d \geq 0$)

$i$번째 고유벡터 $\mathbf{q}_i$(즉, $Q$의 $i$번째 열)가 $i$번째 **주성분(Principal Component)**의 방향입니다. 고유값 $\lambda_i$는 해당 주성분 방향에서의 분산 크기입니다.

### 4단계: 주성분으로의 투영

상위 $k$개의 고유벡터로 구성된 투영 행렬 $Q_k = [\mathbf{q}_1, \mathbf{q}_2, \ldots, \mathbf{q}_k] \in \mathbb{R}^{d \times k}$를 사용하여 데이터를 저차원 공간으로 투영합니다:

$$Z = \tilde{X} Q_k \in \mathbb{R}^{N \times k}$$

각 데이터 포인트 $\mathbf{x} \in \mathbb{R}^d$의 변환은 다음과 같습니다:

$$\mathbf{z} = Q_k^T \tilde{\mathbf{x}}$$

$\mathbf{z} \in \mathbb{R}^k$가 $k$차원으로 축소된 표현입니다. 역변환(Reconstruction)도 가능합니다:

$$\hat{\mathbf{x}} = Q_k \mathbf{z} + \bar{\mathbf{x}} = Q_k Q_k^T \tilde{\mathbf{x}} + \bar{\mathbf{x}}$$

$k < d$이면 일부 정보가 손실되며, 이 손실이 **재구성 오차(Reconstruction Error)**입니다. PCA는 이 재구성 오차를 최소화하는 동시에 투영된 데이터의 분산을 최대화하는 기법입니다. 이 두 목적함수는 수학적으로 동치입니다.

---

![분산 설명률: 각 주성분의 분산 설명 비율과 누적 분산 설명률](figures/explained_variance_ratio.png)
*분산 설명률: Scree Plot과 누적 EVR 곡선으로 상위 주성분이 전체 분산의 대부분을 설명하는 것을 확인할 수 있다.*

## 분산 설명률 (Explained Variance Ratio)

### EVR이란?

몇 개의 주성분을 선택해야 할까요? 이 질문에 답하는 핵심 지표가 **분산 설명률(Explained Variance Ratio, EVR)**입니다. $k$번째 주성분의 EVR은 다음과 같이 정의됩니다:

$$\text{EVR}_k = \frac{\lambda_k}{\sum_{i=1}^{d} \lambda_i}$$

$\text{EVR}_k$는 $k$번째 주성분이 전체 분산 중 몇 퍼센트를 설명하는지를 나타냅니다. 상위 $k$개 주성분까지의 **누적 분산 설명률(Cumulative EVR)**은:

$$\text{Cumulative EVR}(k) = \frac{\sum_{i=1}^{k} \lambda_i}{\sum_{i=1}^{d} \lambda_i}$$

실무에서는 누적 EVR이 **80~95%**가 되는 최소 $k$를 선택하는 것이 일반적입니다.

### Scree Plot으로 주성분 수 결정

**스크리 플롯(Scree Plot)**은 각 주성분의 고유값(또는 EVR)을 가로축에 주성분 번호, 세로축에 고유값을 놓고 그린 꺾은선 그래프입니다. 그래프에서 기울기가 급격히 완만해지는 지점, 즉 **엘보우(Elbow)**를 찾아 주성분 수를 결정합니다. 엘보우 이후의 주성분들은 추가되어도 설명력 향상이 미미하기 때문입니다.

```
고유값
  |
  *
  |  *
  |     *
  |        * * * * * *   ← 여기서부터 완만 (엘보우)
  |________________________
       1  2  3  4  5  6  주성분 번호
```

---

## SVD와의 관계

### 공분산 행렬 대신 SVD를 쓰는 이유

실제 PCA 구현(예: sklearn)에서는 공분산 행렬을 명시적으로 계산한 뒤 고유값 분해를 하는 대신, 데이터 행렬 $\tilde{X}$에 직접 **특이값 분해(SVD)**를 적용합니다:

$$\tilde{X} = U \Sigma V^T$$

- $U \in \mathbb{R}^{N \times N}$: 좌 특이벡터 행렬 (데이터 포인트의 새 좌표)
- $\Sigma \in \mathbb{R}^{N \times d}$: 특이값 $\sigma_1 \geq \sigma_2 \geq \cdots \geq 0$이 대각선에 위치
- $V^T \in \mathbb{R}^{d \times d}$: 우 특이벡터 행렬의 전치

**주성분 방향은 $V$의 열벡터**입니다. 즉, $V$의 $i$번째 열이 $i$번째 주성분 방향이고, 고유값과 특이값의 관계는 다음과 같습니다:

$$\lambda_i = \frac{\sigma_i^2}{N-1}$$

이를 확인해봅시다. 공분산 행렬을 SVD로 표현하면:

$$\Sigma = \frac{1}{N-1} \tilde{X}^T \tilde{X} = \frac{1}{N-1} (U \Sigma V^T)^T (U \Sigma V^T) = \frac{1}{N-1} V \Sigma^T U^T U \Sigma V^T = V \frac{\Sigma^T \Sigma}{N-1} V^T$$

$Q = V$이고 $\Lambda = \frac{\Sigma^T \Sigma}{N-1}$임을 확인할 수 있습니다. SVD 기반 계산이 선호되는 이유는 두 가지입니다. 첫째, $\tilde{X}^T \tilde{X}$를 명시적으로 계산하지 않으므로 **수치 안정성(Numerical Stability)**이 높습니다. 둘째, $d \gg N$인 경우(피처 수 > 샘플 수) $N \times N$ 행렬만 다루면 되므로 **계산 효율**이 좋습니다.

---

## PCA의 가정과 한계

PCA는 강력하지만 다음과 같은 가정과 한계를 갖습니다.

**선형성 가정**: PCA는 주성분이 원본 피처의 **선형 결합**이라고 가정합니다. 데이터에 비선형 구조(예: 스위스 롤, 원형 분포)가 존재한다면 PCA는 이를 효과적으로 포착하지 못합니다.

**분산 = 중요성 가정**: PCA는 분산이 큰 방향이 중요한 정보를 담고 있다고 가정합니다. 그러나 분류 문제에서는 클래스를 가장 잘 구분하는 방향이 분산이 가장 큰 방향과 다를 수 있습니다. 예를 들어 두 클래스가 좁은 골짜기 형태로 분포한 경우, PCA의 첫 번째 주성분은 클래스 구분에 무용할 수 있습니다.

**이상치 민감성**: 공분산 행렬은 이상치(Outlier)에 민감합니다. 극단적인 값 하나가 주성분 방향을 크게 왜곡할 수 있습니다. Robust PCA와 같은 변형이 이 문제를 해결합니다.

**해석 가능성 저하**: 주성분은 원본 피처들의 선형 조합이므로 직관적 해석이 어렵습니다. "키와 몸무게의 가중 평균"이라는 설명은 가능하지만, 비즈니스 맥락에서 의미 있는 해석을 연결하기 어려울 수 있습니다.

---

## Kernel PCA: 비선형 차원 축소

PCA의 선형성 한계를 극복하기 위해 **커널 PCA(Kernel PCA)**가 제안되었습니다. 커널 트릭(Kernel Trick)을 활용하여 데이터를 명시적으로 고차원 특징 공간에 매핑하지 않고도 비선형 PCA를 수행합니다.

커널 함수 $k(\mathbf{x}_i, \mathbf{x}_j)$로 정의되는 **커널 행렬(Kernel Matrix)** $K \in \mathbb{R}^{N \times N}$에 중심화를 적용한 후 고유값 분해를 수행합니다:

$$\tilde{K} = K - \mathbf{1}_N K - K \mathbf{1}_N + \mathbf{1}_N K \mathbf{1}_N$$

$$\tilde{K} \mathbf{\alpha} = \lambda N \mathbf{\alpha}$$

자주 사용되는 커널:
- **RBF(Gaussian) 커널**: $k(\mathbf{x}, \mathbf{y}) = \exp\left(-\frac{\|\mathbf{x} - \mathbf{y}\|^2}{2\sigma^2}\right)$, 비선형 클러스터 분리에 효과적
- **다항식 커널**: $k(\mathbf{x}, \mathbf{y}) = (\mathbf{x}^T \mathbf{y} + c)^p$

단점은 $N \times N$ 커널 행렬을 저장하고 분해해야 하므로 $O(N^2)$ 메모리와 $O(N^3)$ 연산이 필요하여, 대용량 데이터에는 적용이 어렵습니다.

---

## LDA와의 비교

**선형 판별 분석(LDA, Linear Discriminant Analysis)**은 PCA와 자주 비교되는 차원 축소 기법입니다. 두 방법의 핵심적인 차이를 정리하면:

| 구분 | PCA | LDA |
|---|---|---|
| 학습 방식 | 비지도(Unsupervised) | 지도(Supervised) |
| 목적함수 | 투영된 데이터의 **분산 최대화** | **클래스 간 분산 / 클래스 내 분산 최대화** |
| 클래스 정보 | 사용 안 함 | 레이블 $y$ 필요 |
| 최대 성분 수 | 최대 $d$개 | 최대 $C-1$개 ($C$: 클래스 수) |
| 주요 활용 | 비지도 탐색, 노이즈 제거 | 분류 전처리, 특징 추출 |

PCA는 레이블 없이 데이터 구조를 탐색할 때, LDA는 분류 성능을 높이기 위한 차원 축소에 적합합니다. 분류 문제라면 LDA가 더 나은 투영을 제공하는 경우가 많지만, 클래스 수가 적거나 가우시안 분포 가정이 맞지 않으면 PCA가 더 robust합니다.

---

## 실전 활용

**1. 노이즈 제거(Denoising)**: 상위 $k$개 주성분으로 투영 후 역변환하면, 분산이 낮은 주성분(주로 노이즈)이 제거됩니다. 이미지 복원, 신호 처리에 활용됩니다.

**2. 데이터 시각화**: 고차원 데이터를 2~3차원으로 축소하여 산점도로 표현합니다. 클러스터 구조, 이상치, 그룹 간 분리 등을 직관적으로 파악할 수 있습니다.

**3. 계산 속도 향상**: 수천 개의 피처를 수십~수백 개로 줄이면 후속 알고리즘(SVM, 로지스틱 회귀 등)의 학습 속도가 크게 빨라집니다.

**4. 다중공선성 해결**: 상관된 피처들을 직교하는 주성분으로 변환하면 다중공선성이 완전히 제거됩니다. 선형 회귀 이전 전처리로 활용됩니다.

**5. 이상 탐지(Anomaly Detection)**: 재구성 오차 $\|\mathbf{x} - \hat{\mathbf{x}}\|^2$가 큰 포인트는 정상 분포에서 벗어난 이상치일 가능성이 높습니다.

---

## Python 코드: sklearn PCA + Scree Plot + 2D 시각화

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import load_iris

# ─── 1. 데이터 로드 및 전처리 ───────────────────────────────────────────
iris = load_iris()
X, y = iris.data, iris.target          # (150, 4), 4개 피처
labels = iris.target_names             # ['setosa', 'versicolor', 'virginica']

# 표준화: 평균 0, 표준편차 1 (단위가 다른 피처들을 동등하게)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ─── 2. PCA 전체 주성분으로 분석 (주성분 수 결정용) ────────────────────
pca_full = PCA()
pca_full.fit(X_scaled)

evr = pca_full.explained_variance_ratio_          # 각 주성분의 EVR
cumulative_evr = np.cumsum(evr)                   # 누적 EVR

print("고유값 (분산):", pca_full.explained_variance_.round(4))
print("분산 설명률 (EVR):", evr.round(4))
print("누적 분산 설명률:", cumulative_evr.round(4))
# 고유값 (분산): [2.9185 0.9137 0.1471 0.0208]
# 분산 설명률 (EVR): [0.7296 0.2285 0.0368 0.0052]
# 누적 분산 설명률: [0.7296 0.9581 0.9949 1.0000]

# ─── 3. Scree Plot ───────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# 왼쪽: 개별 EVR (Scree Plot)
axes[0].bar(range(1, len(evr) + 1), evr, color='steelblue', alpha=0.8)
axes[0].plot(range(1, len(evr) + 1), evr, 'o-', color='steelblue')
axes[0].set_xlabel('주성분 번호')
axes[0].set_ylabel('분산 설명률 (EVR)')
axes[0].set_title('Scree Plot')
axes[0].set_xticks(range(1, len(evr) + 1))

# 오른쪽: 누적 EVR
axes[1].plot(range(1, len(cumulative_evr) + 1), cumulative_evr,
             'o-', color='darkorange')
axes[1].axhline(y=0.95, color='red', linestyle='--', label='95% 기준선')
axes[1].set_xlabel('주성분 수 (k)')
axes[1].set_ylabel('누적 분산 설명률')
axes[1].set_title('누적 EVR')
axes[1].set_xticks(range(1, len(cumulative_evr) + 1))
axes[1].legend()
axes[1].set_ylim([0, 1.05])

plt.tight_layout()
plt.savefig('scree_plot.png', dpi=150, bbox_inches='tight')
plt.show()

# ─── 4. 2차원 시각화 (k=2) ──────────────────────────────────────────────
pca_2d = PCA(n_components=2)
X_pca = pca_2d.fit_transform(X_scaled)    # (150, 2)

print(f"\n차원 축소: {X_scaled.shape} → {X_pca.shape}")
print(f"PC1 + PC2 설명률: {pca_2d.explained_variance_ratio_.sum():.2%}")

# 주성분 적재량(Loadings): 각 원본 피처가 주성분에 기여하는 정도
loadings = pca_2d.components_             # (2, 4)
feature_names = iris.feature_names
print("\n주성분 적재량 (PC1, PC2):")
for i, feat in enumerate(feature_names):
    print(f"  {feat}: PC1={loadings[0, i]:+.3f}, PC2={loadings[1, i]:+.3f}")

# 2D 산점도 그리기
fig, ax = plt.subplots(figsize=(8, 6))
colors = ['tomato', 'steelblue', 'forestgreen']
for idx, (label, color) in enumerate(zip(labels, colors)):
    mask = y == idx
    ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
               c=color, label=label, alpha=0.7, edgecolors='white', s=60)

ax.set_xlabel(f'PC1 ({evr[0]:.1%} 설명)')
ax.set_ylabel(f'PC2 ({evr[1]:.1%} 설명)')
ax.set_title('Iris 데이터 PCA 2D 시각화')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('pca_2d.png', dpi=150, bbox_inches='tight')
plt.show()

# ─── 5. 재구성 오차 (Reconstruction Error) ────────────────────────────
for k in [1, 2, 3, 4]:
    pca_k = PCA(n_components=k)
    X_transformed = pca_k.fit_transform(X_scaled)
    X_reconstructed = pca_k.inverse_transform(X_transformed)
    error = np.mean((X_scaled - X_reconstructed) ** 2)
    print(f"k={k}: 재구성 MSE = {error:.4f},  누적 EVR = {np.sum(pca_full.explained_variance_ratio_[:k]):.4f}")
# k=1: 재구성 MSE = 0.2704,  누적 EVR = 0.7296
# k=2: 재구성 MSE = 0.1048,  누적 EVR = 0.9581
# k=3: 재구성 MSE = 0.0051,  누적 EVR = 0.9949
# k=4: 재구성 MSE = 0.0000,  누적 EVR = 1.0000
```

```output
고유값 (분산): [2.9381 0.9202 0.1477 0.0209]
분산 설명률 (EVR): [0.7296 0.2285 0.0367 0.0052]
누적 분산 설명률: [0.7296 0.9581 0.9948 1.    ]

차원 축소: (150, 4) → (150, 2)
PC1 + PC2 설명률: 95.81%

주성분 적재량 (PC1, PC2):
  sepal length (cm): PC1=+0.521, PC2=+0.377
  sepal width (cm): PC1=-0.269, PC2=+0.923
  petal length (cm): PC1=+0.580, PC2=+0.024
  petal width (cm): PC1=+0.565, PC2=+0.067
k=1: 재구성 MSE = 0.2704,  누적 EVR = 0.7296
k=2: 재구성 MSE = 0.0419,  누적 EVR = 0.9581
k=3: 재구성 MSE = 0.0052,  누적 EVR = 0.9948
k=4: 재구성 MSE = 0.0000,  누적 EVR = 1.0000
```

![분산 설명률 시각화](figures/explained_variance_ratio.png)

*Figure 1: 분산 설명률: 각 주성분의 분산 설명 비율과 누적 분산 설명률을 통해 상위 2개 주성분으로 전체 분산의 약 95.8%를 설명함을 보여준다.*

![PCA 2D 투영 산점도](figures/pca_2d_projection.png)

*Figure 2: PCA 2D 투영: 아이리스 데이터를 상위 2개 주성분으로 투영한 결과, setosa는 명확히 분리되고 versicolor와 virginica는 다소 겹친다.*

아이리스 데이터는 4개의 피처를 갖지만, 상위 2개의 주성분만으로 전체 분산의 약 95.8%를 설명합니다. 2D 산점도를 보면 setosa는 명확히 분리되고, versicolor와 virginica는 다소 겹치는 것을 확인할 수 있습니다.

---

## 정리

**PCA**는 다음 단계로 동작합니다:

1. 데이터 **중심화(표준화)** → 스케일 통일
2. **공분산 행렬** $\Sigma = \frac{1}{N-1}\tilde{X}^T\tilde{X}$ 계산
3. **고유값 분해** $\Sigma = Q\Lambda Q^T$ → 고유벡터(주성분 방향) 추출
4. **분산 설명률** 기준으로 상위 $k$개 주성분 선택
5. 데이터를 $k$차원으로 **투영** $Z = \tilde{X}Q_k$

PCA의 핵심 강점은 단순하고 해석 가능하며 계산 효율이 높다는 점입니다. 그러나 선형 구조만 포착한다는 한계로 인해 비선형 데이터에는 Kernel PCA, t-SNE, UMAP 같은 대안을 함께 고려해야 합니다.

> **다음 글 안내**: PCA의 한계를 극복하는 비선형 차원 축소 기법인 t-SNE와 UMAP을 살펴보려면 [[tsne-umap]]을, PCA의 수학적 토대인 선형대수를 복습하려면 [[linear-algebra-for-ml]]을 참고하세요.

## 관련 문서

- [[linear-algebra-for-ml|ML을 위한 선형대수 핵심 정리]]
- [[tsne-umap|t-SNE와 UMAP: 비선형 차원 축소]]
- [[kmeans-clustering|K-평균 군집화]]
- [[feature-engineering|피처 엔지니어링]]
- [[kernel-methods|커널 방법론]]
- [[anomaly-detection|이상 탐지]]