## 개요

현실 세계의 데이터는 대부분 선형으로 분리되지 않습니다. 단순한 직선이나 초평면(hyperplane)으로는 분류 경계를 표현하기 어려운 경우가 많습니다. **커널 방법론(Kernel Methods)**은 이 문제를 우아하게 해결하는 수학적 프레임워크입니다.

핵심 아이디어는 **커널 트릭(Kernel Trick)**입니다. 데이터를 원래 입력 공간 $\mathcal{X}$에서 고차원(또는 무한 차원)의 특성 공간 $\mathcal{F}$로 매핑하는 함수 $\phi: \mathcal{X} \rightarrow \mathcal{F}$를 상상해 보겠습니다. 고차원 공간에서는 선형으로 분리 가능한 경우가 많아지므로, 선형 알고리즘을 그대로 적용할 수 있습니다. 그런데 커널 함수 $k(x, x')$를 사용하면 **$\phi(x)$를 명시적으로 계산하지 않고도** 두 벡터의 내적 $\phi(x)^T \phi(x')$를 구할 수 있습니다. 이 덕분에 계산 비용을 획기적으로 절감하면서 비선형 학습이 가능합니다.

---

## 수학적 배경

### 커널 함수의 정의

커널 함수 $k: \mathcal{X} \times \mathcal{X} \rightarrow \mathbb{R}$는 특성 맵 $\phi$에 의한 내적으로 정의됩니다:

$$k(x, x') = \phi(x)^T \phi(x')$$

이 정의에 따르면 커널 값은 두 데이터 포인트가 특성 공간에서 얼마나 유사한지를 나타내는 **유사도 측도**로 해석할 수 있습니다.

### Mercer 조건

임의의 함수 $k$가 유효한 커널(즉 어떤 $\phi$에 대한 내적으로 표현 가능)이 되려면 **Mercer 조건**을 만족해야 합니다. 구체적으로, 임의의 유한 집합 $\{x_1, \ldots, x_n\}$에 대해 구성된 **그람 행렬(Gram matrix)** $K_{ij} = k(x_i, x_j)$가 **양반정치(positive semi-definite)**이어야 합니다:

$$\sum_{i,j} c_i c_j k(x_i, x_j) \geq 0, \quad \forall c_i \in \mathbb{R}$$

Mercer 조건을 만족하면 커널에 대응하는 RKHS(재현 커널 힐베르트 공간)가 유일하게 존재합니다.

### 주요 커널 함수

**RBF(Radial Basis Function) / 가우시안 커널**은 가장 많이 사용되는 커널로, 무한 차원 특성 공간에 해당합니다:

$$k(x, x') = \exp\!\left(-\gamma \|x - x'\|^2\right)$$

여기서 $\gamma > 0$은 폭(bandwidth)을 제어하는 하이퍼파라미터입니다. $\gamma$가 클수록 결정 경계가 더 복잡해집니다.

**다항 커널(Polynomial Kernel)**은 $d$차 다항 특성을 암묵적으로 사용합니다:

$$k(x, x') = (x^T x' + c)^d$$

**시그모이드 커널(Sigmoid Kernel)**은 신경망의 활성화 함수와 관련이 있습니다:

$$k(x, x') = \tanh(\alpha x^T x' + \beta)$$

단, 이 커널은 모든 파라미터 조합에서 Mercer 조건을 만족하지는 않습니다.

---

![커널 변환: 저차원에서 비선형 분리 불가능한 데이터가 고차원 특성 공간에서 선형 분리 가능해지는 과정](figures/kernel_transformation.png)
*커널 변환: 원래 입력 공간에서 분리할 수 없는 데이터를 커널 함수를 통해 고차원으로 매핑하면 선형 결정 경계로 분류할 수 있다.*

## 알고리즘

### RKHS (재현 커널 힐베르트 공간)

**RKHS(Reproducing Kernel Hilbert Space)**는 커널 방법론의 이론적 토대입니다. 임의의 Mercer 커널 $k$에 대해 유일한 힐베르트 공간 $\mathcal{H}_k$가 존재하며, 다음 **재현 성질(reproducing property)**을 가집니다:

$$f(x) = \langle f, k(\cdot, x) \rangle_{\mathcal{H}_k}, \quad \forall f \in \mathcal{H}_k$$

**표현 정리(Representer Theorem)**에 의하면, 정규화를 포함한 대부분의 학습 문제의 최적해는 훈련 데이터의 커널 함수의 선형 결합으로 표현됩니다:

$$f^*(x) = \sum_{i=1}^{n} \alpha_i k(x_i, x)$$

이 덕분에 무한 차원 공간에서의 최적화 문제가 $n$차원 문제로 축소됩니다.

### Kernel PCA

일반 PCA는 공분산 행렬의 선형 고유벡터를 구합니다. **Kernel PCA**는 데이터를 특성 공간 $\mathcal{F}$로 매핑한 뒤 그 공간에서 PCA를 수행합니다. 특성 공간에서의 중심화된 그람 행렬 $\tilde{K}$를 고유 분해하여 비선형 주성분을 추출합니다:

$$\tilde{K} = K - \mathbf{1}_n K - K \mathbf{1}_n + \mathbf{1}_n K \mathbf{1}_n$$

### Kernel Ridge Regression

릿지 회귀에 커널 트릭을 적용한 **Kernel Ridge Regression**은 다음 문제를 풀어 비선형 회귀를 수행합니다:

$$\min_{\alpha} \|y - K\alpha\|^2 + \lambda \alpha^T K \alpha$$

닫힌 형태의 해는 $\alpha^* = (K + \lambda I)^{-1} y$입니다.

### SVM과 커널 트릭

SVM의 이중 문제(dual problem)는 데이터 포인트의 내적 $x_i^T x_j$에만 의존합니다. 이를 커널 함수 $k(x_i, x_j)$로 교체하면 자동으로 비선형 SVM이 됩니다:

$$\max_{\alpha} \sum_i \alpha_i - \frac{1}{2} \sum_{i,j} \alpha_i \alpha_j y_i y_j k(x_i, x_j)$$

---

## Python 구현

아래는 sklearn을 사용하여 커널 방법론을 적용하는 예제입니다.

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_circles, make_moons
from sklearn.decomposition import KernelPCA, PCA
from sklearn.kernel_ridge import KernelRidge
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# ── 데이터 생성 ──────────────────────────────────────────
X, y = make_circles(n_samples=400, factor=0.3, noise=0.05, random_state=42)
X = StandardScaler().fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ── SVM: 선형 vs RBF 커널 비교 ──────────────────────────
svm_linear = SVC(kernel='linear', C=1.0)
svm_rbf    = SVC(kernel='rbf', C=1.0, gamma=0.5)

svm_linear.fit(X_train, y_train)
svm_rbf.fit(X_train, y_train)

print(f"선형 SVM 정확도: {accuracy_score(y_test, svm_linear.predict(X_test)):.4f}")
print(f"RBF  SVM 정확도: {accuracy_score(y_test, svm_rbf.predict(X_test)):.4f}")

# ── Decision Boundary 시각화 헬퍼 ────────────────────────
def plot_decision_boundary(ax, model, X, y, title):
    h = 0.02
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
    xx, yy = np.meshgrid(
        np.arange(x_min, x_max, h),
        np.arange(y_min, y_max, h)
    )
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    ax.contourf(xx, yy, Z, alpha=0.3, cmap='RdBu')
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap='RdBu', edgecolors='k', s=20)
    ax.set_title(title)
    ax.set_xlim(xx.min(), xx.max())
    ax.set_ylim(yy.min(), yy.max())

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
plot_decision_boundary(axes[0], svm_linear, X, y, "선형 SVM (Linear Kernel)")
plot_decision_boundary(axes[1], svm_rbf,    X, y, "커널 SVM (RBF Kernel)")
plt.suptitle("SVM Decision Boundary 비교", fontsize=14)
plt.tight_layout()
plt.show()

# ── Kernel PCA vs PCA 비교 ────────────────────────────────
X_moon, y_moon = make_moons(n_samples=400, noise=0.05, random_state=42)

pca        = PCA(n_components=2)
kpca_rbf   = KernelPCA(n_components=2, kernel='rbf', gamma=15)

X_pca  = pca.fit_transform(X_moon)
X_kpca = kpca_rbf.fit_transform(X_moon)

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, data, title in zip(
    axes,
    [X_moon, X_pca, X_kpca],
    ["원본 데이터", "PCA", "Kernel PCA (RBF)"]
):
    ax.scatter(data[:, 0], data[:, 1], c=y_moon, cmap='RdBu', edgecolors='k', s=20)
    ax.set_title(title)
plt.suptitle("PCA vs Kernel PCA 비교", fontsize=14)
plt.tight_layout()
plt.show()

# ── Kernel Ridge Regression ───────────────────────────────
np.random.seed(42)
X_reg = np.sort(np.random.uniform(-3, 3, 100)).reshape(-1, 1)
y_reg = np.sin(X_reg).ravel() + np.random.normal(0, 0.2, 100)

krr = KernelRidge(kernel='rbf', alpha=0.1, gamma=1.0)
krr.fit(X_reg, y_reg)

X_plot = np.linspace(-3, 3, 300).reshape(-1, 1)
y_pred = krr.predict(X_plot)

plt.figure(figsize=(8, 4))
plt.scatter(X_reg, y_reg, alpha=0.6, label='훈련 데이터')
plt.plot(X_plot, y_pred, 'r-', linewidth=2, label='Kernel Ridge Regression')
plt.plot(X_plot, np.sin(X_plot), 'g--', linewidth=1, label='실제 함수')
plt.legend()
plt.title("Kernel Ridge Regression 예시")
plt.show()
```

```output
선형 SVM 정확도: 0.6500
RBF  SVM 정확도: 1.0000
```

![커널 변환과 결정 경계](figures/kernel_transformation.png)

*Figure 1: 커널 변환 시각화: 선형 SVM과 RBF SVM의 결정 경계 비교, Kernel PCA vs PCA 비교, 커널 함수 간 성능 차이를 보여준다.*

![커널별 결정 경계 비교](figures/kernel_comparison.png)

*Figure 2: 커널 비교: 동일한 데이터에 선형, 다항식, RBF 커널을 적용했을 때 결정 경계의 복잡도와 유연성 차이를 보여준다.*

---

![커널 비교: 선형, 다항식, RBF 커널의 결정 경계 차이 비교](figures/kernel_comparison.png)
*커널 비교: 동일한 데이터에 선형, 다항식, RBF 커널을 적용했을 때 생성되는 결정 경계의 복잡도와 유연성이 뚜렷하게 달라진다.*

## 시각화 해석

위 코드를 실행하면 다음과 같은 결과를 확인할 수 있습니다.

**SVM Decision Boundary 비교:** 동심원(make_circles) 데이터에서 선형 SVM은 직선 경계밖에 그리지 못해 분류 성능이 낮지만, RBF 커널 SVM은 원형에 가까운 비선형 경계를 학습하여 높은 정확도를 달성합니다.

**Kernel PCA vs PCA 비교:** 초승달(make_moons) 데이터에서 표준 PCA는 두 클래스가 여전히 뒤섞인 형태로 투영되지만, RBF 커널 PCA는 두 클래스를 선형 분리 가능한 형태로 펼쳐줍니다.

---

## 실전 팁

### 하이퍼파라미터 조정

**RBF 커널의 $\gamma$ (감마):** 결정 경계의 복잡도를 제어합니다. 값이 너무 크면 과적합(overfitting), 너무 작으면 과소적합(underfitting)이 발생합니다. `sklearn`에서 `gamma='scale'`(기본값) 또는 `gamma='auto'`를 출발점으로 삼고, 로그 스케일(`1e-3` ~ `1e2`)로 그리드 서치하는 것을 권장합니다.

**SVM의 $C$ (규제 파라미터):** 마진 위반을 얼마나 허용할지 결정합니다. $C$가 크면 마진이 좁아지고 훈련 오차가 줄지만 과적합 위험이 높아집니다. `GridSearchCV`나 `RandomizedSearchCV`로 $\gamma$와 $C$를 동시에 탐색하면 효율적입니다.

### 커널 선택 가이드

| 상황 | 추천 커널 |
|------|----------|
| 일반적인 비선형 분류 | RBF 커널 (기본 선택) |
| 텍스트/문서 분류 | 선형 커널 (고차원 희소 데이터) |
| 특성 간 상호작용이 중요할 때 | 다항 커널 |
| 주기성이 있는 데이터 | 주기 커널 (Periodic Kernel) |
| 도메인 지식이 있을 때 | 커스텀 커널 직접 설계 |

### 계산 비용 문제 ($O(n^2)$ 문제)

커널 방법론의 가장 큰 단점은 그람 행렬 $K$의 계산 및 저장에 $O(n^2)$ 공간과 시간이 필요하다는 점입니다. 훈련 데이터가 10만 건을 넘으면 메모리 부족이 현실적인 문제가 됩니다.

**대용량 데이터 대안:**

- **Random Fourier Features (RFF):** Bochner 정리를 이용해 RBF 커널을 근사하는 랜덤 특성을 생성합니다. `sklearn.kernel_approximation.RBFSampler`로 쉽게 사용할 수 있으며, 이후 선형 SVM을 적용합니다.

```python
from sklearn.kernel_approximation import RBFSampler
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import make_pipeline

# 근사 커널 SVM (대용량 데이터에 적합)
model = make_pipeline(
    RBFSampler(gamma=0.5, n_components=1000, random_state=42),
    SGDClassifier(max_iter=1000)
)
model.fit(X_train, y_train)
print(f"근사 커널 SVM 정확도: {accuracy_score(y_test, model.predict(X_test)):.4f}")
```

```output
근사 커널 SVM 정확도: 1.0000
```

- **Nyström 방법:** 훈련 데이터의 일부를 landmark로 선택해 커널 행렬을 저랭크 근사합니다. `sklearn.kernel_approximation.Nystroem`을 활용합니다.
- **딥러닝 대안:** 데이터가 매우 많고 복잡한 비선형성이 필요하다면 신경망(특히 ResNet, Transformer)이 실용적입니다. 다만 커널 방법론은 이론적 보장과 해석 가능성이 강점입니다.

### 검증 전략

소규모 데이터(n < 10,000)에서는 5-fold Cross-Validation으로 `C`와 `gamma`를 튜닝하고, 최종 모델 선택 시 검증 곡선(Validation Curve)으로 과적합 여부를 시각적으로 확인하는 것이 좋습니다.

---

## 마무리

커널 방법론은 수십 년의 이론적 기반 위에 세워진 견고한 머신러닝 기법입니다. 딥러닝이 대용량 이미지·텍스트 데이터에서 두각을 나타내지만, 중소규모 정형 데이터에서는 커널 SVM이나 Gaussian Process(가우시안 프로세스, 커널 방법론의 확률적 확장)가 여전히 경쟁력 있는 선택지입니다. 또한 커널 방법론의 이론은 딥러닝의 Neural Tangent Kernel(NTK) 분석으로 이어지며, 현대 ML 이론의 중요한 연결 고리 역할을 하고 있습니다.