<!-- infographic-hero -->
![KNN (K-Nearest Neighbors) 핵심 요약](figures/infographic.svg)

*Figure: KNN (K-Nearest Neighbors) 한 장 요약 인포그래픽*

## 개요

KNN(K-Nearest Neighbors, K-최근접 이웃)은 머신러닝에서 가장 직관적인 알고리즘 중 하나입니다. 핵심 아이디어는 단순합니다. **새로운 데이터 포인트가 주어지면, 학습 데이터에서 가장 가까운 K개의 이웃을 찾고, 그 이웃들의 다수결(분류) 또는 평균(회귀)으로 예측값을 결정합니다.**

KNN이 중요한 이유는 세 가지입니다. 첫째, 모델 파라미터를 명시적으로 학습하지 않는 **비파라메트릭(Non-parametric)** 알고리즘이므로 데이터 분포에 대한 가정이 없습니다. 둘째, 결정 경계(Decision Boundary)가 복잡한 비선형 문제에도 자연스럽게 적응합니다. 셋째, 알고리즘이 단순해 해석이 쉽고 베이스라인 모델로 널리 활용됩니다. 반면, 예측 시점에 전체 학습 데이터를 참조해야 하므로 대용량 데이터에서 계산 비용이 급증한다는 근본적인 한계가 있습니다.

---

## 수학적 배경

### 거리 측정(Distance Metric)

KNN의 핵심은 '가까움'을 어떻게 정의하느냐입니다. 가장 널리 쓰이는 세 가지 거리 공식을 살펴봅니다.

**유클리드 거리(Euclidean Distance)** ( 직선 거리로, 가장 일반적으로 사용됩니다.

$$d_E(x, y) = \sqrt{\sum_{i=1}^{n}(x_i - y_i)^2}$$

**맨하탄 거리(Manhattan Distance)** ) 격자 위를 이동하는 것처럼 각 축의 절댓값 차이를 합산합니다. 이상치(Outlier)에 덜 민감한 특성이 있습니다.

$$d_M(x, y) = \sum_{i=1}^{n}|x_i - y_i|$$

**민코프스키 거리(Minkowski Distance)**, 유클리드와 맨하탄 거리를 일반화한 공식으로, 차수 $p$에 따라 동작이 달라집니다. $p=1$이면 맨하탄, $p=2$이면 유클리드 거리와 동일합니다.

$$d_p(x, y) = \left(\sum_{i=1}^{n}|x_i - y_i|^p\right)^{\frac{1}{p}}$$

$p \to \infty$로 가면 체비쇼프 거리(Chebyshev Distance)로 수렴하며, 각 축의 최대 절댓값 차이만 취합니다.

### K 값 선택의 영향

K는 KNN에서 가장 중요한 하이퍼파라미터입니다.

- **K가 작을수록(예: K=1)**: 훈련 데이터의 노이즈에 민감해져 **과적합(Overfitting)** 위험이 높습니다. 결정 경계가 매우 복잡하고 불규칙해집니다.
- **K가 클수록(예: K=전체 데이터 수)**: 모든 이웃을 참조하므로 다수 클래스로만 예측하게 되어 **과소적합(Underfitting)**이 발생합니다. 결정 경계가 지나치게 단순해집니다.
- **최적 K**: 교차 검증(Cross-Validation)을 통해 Bias-Variance Tradeoff를 최소화하는 지점을 탐색합니다. 이진 분류에서는 동점을 방지하기 위해 일반적으로 **홀수 K**를 사용합니다.

---

![KNN 결정 경계: K 값에 따른 결정 경계 변화](figures/knn_decision_boundaries.png)
*KNN 결정 경계: K가 작으면 복잡하고 불규칙한 경계(과적합), K가 크면 단순하고 매끄러운 경계(과소적합)가 형성된다.*

## 알고리즘 심화

### 탐색 구조: KD-Tree와 Ball Tree

Brute Force 방식(모든 점과의 거리를 계산)은 $O(n \cdot d)$ 시간이 소요되어 대용량 데이터에 부적합합니다. 이를 개선하기 위한 두 가지 인덱싱 구조가 있습니다.

- **KD-Tree**: 피처 공간을 축에 따라 이진 분할하는 트리 구조입니다. 저차원($d < 20$) 데이터에서 평균 $O(\log n)$으로 빠른 탐색이 가능하지만, 고차원에서는 성능이 급격히 저하됩니다.
- **Ball Tree**: 데이터를 초구(Hypersphere) 단위로 분할합니다. KD-Tree보다 구축 비용이 높지만 고차원 및 비유클리드 거리 함수에서 더 안정적입니다.

scikit-learn의 `KNeighborsClassifier`는 `algorithm` 파라미터로 `'auto'`, `'ball_tree'`, `'kd_tree'`, `'brute'`를 지원합니다.

### 가중 KNN(Weighted KNN)

기본 KNN은 모든 이웃을 동등하게 취급합니다. 가중 KNN은 가까운 이웃일수록 더 큰 가중치를 부여합니다. 거리의 역수를 가중치로 사용하는 것이 일반적입니다.

$$\hat{y} = \frac{\sum_{i=1}^{K} w_i \cdot y_i}{\sum_{i=1}^{K} w_i}, \quad w_i = \frac{1}{d(x, x_i)}$$

scikit-learn에서는 `weights='distance'`로 설정합니다.

### 차원의 저주(Curse of Dimensionality)

KNN의 가장 큰 약점은 고차원 데이터에서 극명하게 드러납니다. 차원이 증가할수록 모든 데이터 포인트 간의 거리가 수렴하여 '가깝다/멀다'의 의미가 희석됩니다. 예를 들어 100차원 공간에서는 가장 가까운 이웃과 가장 먼 이웃 간의 거리 차이가 거의 없어집니다. 10차원 단위 하이퍼큐브에서 전체 공간의 1%에 해당하는 이웃을 찾으려면 각 축 방향으로 $0.01^{1/10} \approx 0.63$, 즉 전체 범위의 63%를 커버해야 합니다. 이를 해결하려면 PCA 등 차원 축소를 선행하거나, 도메인에 맞는 거리 함수를 설계해야 합니다.

---

## Python 구현

### 분류: KNeighborsClassifier

```python
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report

# 데이터 로드 및 분할
iris = load_iris()
X, y = iris.data, iris.target
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 피처 스케일링 (KNN에서 필수!)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# KNN 분류기 학습 및 평가
knn_clf = KNeighborsClassifier(
    n_neighbors=5,
    weights='distance',   # 거리 가중 KNN
    metric='euclidean',
    algorithm='auto'
)
knn_clf.fit(X_train_scaled, y_train)
y_pred = knn_clf.predict(X_test_scaled)

print(classification_report(y_test, y_pred, target_names=iris.target_names))
```

```output
precision    recall  f1-score   support

      setosa       1.00      1.00      1.00        10
  versicolor       0.91      1.00      0.95        10
   virginica       1.00      0.90      0.95        10

    accuracy                           0.97        30
   macro avg       0.97      0.97      0.97        30
weighted avg       0.97      0.97      0.97        30
```

### 회귀: KNeighborsRegressor

```python
from sklearn.datasets import fetch_california_housing
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_squared_error, r2_score

# 데이터 준비
housing = fetch_california_housing()
X, y = housing.data, housing.target
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled  = scaler.transform(X_test)

# KNN 회귀
knn_reg = KNeighborsRegressor(n_neighbors=10, weights='distance')
knn_reg.fit(X_train_scaled, y_train)
y_pred = knn_reg.predict(X_test_scaled)

rmse = mean_squared_error(y_test, y_pred, squared=False)
print(f"RMSE: {rmse:.4f}")
print(f"R\u00b2:   {r2_score(y_test, y_pred):.4f}")
```

```output
<!-- Pre-computed result needed -->
```

### GridSearchCV로 최적 K 탐색

```python
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline

# Pipeline으로 스케일링 + KNN 통합
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('knn', KNeighborsClassifier())
])

param_grid = {
    'knn__n_neighbors': list(range(1, 31, 2)),  # 홀수 K: 1, 3, 5, ..., 29
    'knn__weights':     ['uniform', 'distance'],
    'knn__metric':      ['euclidean', 'manhattan']
}

grid_search = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1,
    verbose=1
)
grid_search.fit(X_train, y_train)

print(f"최적 파라미터: {grid_search.best_params_}")
print(f"최적 CV 정확도: {grid_search.best_score_:.4f}")
print(f"테스트 정확도: {grid_search.score(X_test, y_test):.4f}")
```

<!-- Execution error: ValueError: 
All the 300 fits failed.
It is very likely that your model is misconfigured.
You can try to debug the error by setting error_score='raise'.

Below are more details about the failures:
--------------------------------------------------------------------------------
300 fits failed with the following error:
Traceback (most recent call last):
  File "/usr/local/lib/python3.12/dist-packages/sklearn/model_selection/_validation.py", line 833, in _fit_and_score
    estimator.fit(X_train, y_train, **fit_params)
  File "/usr/local/lib/python3.12/dist-packages/sklearn/base.py", line 1336, in wrapper
    return fit_method(estimator, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/sklearn/pipeline.py", line 621, in fit
    self._final_estimator.fit(Xt, y, **last_step_params["fit"])
  File "/usr/local/lib/python3.12/dist-packages/sklearn/base.py", line 1336, in wrapper
    return fit_method(estimator, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/sklearn/neighbors/_classification.py", line 243, in fit
    return self._fit(X, y)
           ^^^^^^^^^^^^^^^
  File "/usr/local/lib/python3.12/dist-packages/sklearn/neighbors/_base.py", line 501, in _fit
    check_classification_targets(y)
  File "/usr/local/lib/python3.12/dist-packages/sklearn/utils/multiclass.py", line 221, in check_classification_targets
    raise ValueError(
ValueError: Unknown label type: continuous. Maybe you are trying to fit a classifier, which expects discrete classes on a regression target with continuous values.
 -->

---

## 시각화: K 값에 따른 결정 경계

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_moons
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier

# 비선형 데이터 생성
X, y = make_moons(n_samples=300, noise=0.25, random_state=42)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 결정 경계를 그릴 메시 그리드 생성
h = 0.02
x_min, x_max = X_scaled[:, 0].min() - 0.5, X_scaled[:, 0].max() + 0.5
y_min, y_max = X_scaled[:, 1].min() - 0.5, X_scaled[:, 1].max() + 0.5
xx, yy = np.meshgrid(np.arange(x_min, x_max, h),
                     np.arange(y_min, y_max, h))

k_values = [1, 5, 15, 30]
fig, axes = plt.subplots(1, 4, figsize=(20, 4))

for ax, k in zip(axes, k_values):
    knn = KNeighborsClassifier(n_neighbors=k)
    knn.fit(X_scaled, y)

    Z = knn.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    ax.contourf(xx, yy, Z, alpha=0.4, cmap='RdBu')
    ax.scatter(X_scaled[:, 0], X_scaled[:, 1],
               c=y, cmap='RdBu', edgecolors='k', s=30)
    ax.set_title(f'K = {k}', fontsize=14, fontweight='bold')
    ax.set_xlabel('Feature 1')
    ax.set_ylabel('Feature 2')

plt.suptitle('KNN Decision Boundary for Different K Values', fontsize=16, y=1.02)
plt.tight_layout()
plt.savefig('knn_decision_boundary.png', dpi=150, bbox_inches='tight')
plt.show()
```

![KNN 결정 경계 변화](figures/knn_decision_boundaries.png)

*Figure 1: KNN 결정 경계: K=1(과적합)부터 K=30(과소적합)까지 K 값에 따른 결정 경계의 변화를 보여준다.*

K=1일 때 매우 들쭉날쭉한 결정 경계(과적합)부터, K=30일 때 부드럽고 단순한 경계(과소적합)까지 시각적으로 확인할 수 있습니다. 최적 K는 그 사이 어딘가에 존재하며, 교차 검증으로 탐색합니다.

---

![K 값에 따른 정확도 변화: 최적의 K를 선택하는 기준](figures/knn_k_vs_accuracy.png)
*K 값과 정확도: K가 너무 작으면 노이즈에 민감하고, 너무 크면 세밀한 패턴을 놓치며, 교차 검증으로 최적 K를 선택한다.*

## 실전 팁

### KNN을 언제 사용할까?

- 데이터 크기가 **수만 건 이하**로 비교적 소규모인 경우
- 데이터 분포에 대한 사전 가정을 하고 싶지 않을 때
- **베이스라인 모델**을 빠르게 구축해 성능의 하한을 확인할 때
- 추천 시스템에서 아이템 또는 사용자 간 유사도 기반 탐색
- 이상 탐지(Anomaly Detection): 이웃과의 거리가 매우 먼 포인트를 이상치로 판단

### 장단점 요약

| 구분 | 내용 |
|------|------|
| **장점** | 구현 단순, 학습 시간 없음, 비선형 경계 자연 표현, 멀티클래스 기본 지원 |
| **단점** | 예측 시 $O(n \cdot d)$ 연산, 대용량 데이터 불리, 고차원 취약, 메모리에 전체 학습 데이터 보유 필요 |

### 피처 스케일링이 필수인 이유

거리 기반 알고리즘인 KNN은 피처의 **스케일(단위)에 극도로 민감**합니다. 예를 들어 나이(0~100)와 연봉(0~100,000,000)을 스케일링 없이 사용하면, 거리 계산이 연봉 피처에 완전히 지배당합니다. `StandardScaler`(평균 0, 표준편차 1로 정규화) 또는 `MinMaxScaler`(0~1 범위로 변환)를 반드시 적용해야 합니다.

```python
# 올바른 방법: Pipeline으로 스케일링과 모델을 묶어 데이터 누수 방지
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('knn', KNeighborsClassifier(n_neighbors=7))
])
pipe.fit(X_train, y_train)
# scaler는 X_train 기준으로만 fit되어 데이터 누수(Leakage)가 없습니다.
```

### 대용량 데이터에서의 대안

수백만 건 이상의 데이터에서는 KNN이 실용적이지 않습니다. 이 경우 다음 대안을 고려하세요.

- **Approximate Nearest Neighbor (ANN)**: FAISS, Annoy, HNSW 라이브러리를 활용한 근사 탐색으로 정확도를 일부 희생하고 속도를 획기적으로 향상
- **LSH (Locality-Sensitive Hashing)**: 해시 함수로 유사한 데이터를 같은 버킷에 그룹화해 탐색 범위를 좁힘
- **다른 알고리즘 전환**: 대용량에는 SVM, 랜덤 포레스트, XGBoost 등이 훨씬 효율적

---

## 마무리

KNN은 '단순함의 미학'을 보여주는 알고리즘입니다. 복잡한 모델링 없이 데이터 자체의 구조를 활용하는 이 방식은, 소규모 데이터에서 강력한 베이스라인을 제공합니다. 핵심 체크리스트를 정리하면 다음과 같습니다.

1. **피처 스케일링은 선택이 아닌 필수**입니다.
2. **K는 홀수**로 설정하고 교차 검증으로 탐색하세요.
3. **고차원 데이터**라면 PCA로 차원을 줄이거나 다른 알고리즘을 검토하세요.
4. **대용량 데이터**에서는 KD-Tree/Ball Tree로도 한계가 있으니 ANN 라이브러리를 활용하세요.
5. Pipeline으로 스케일러와 모델을 묶어 **데이터 누수(Data Leakage)**를 방지하세요.