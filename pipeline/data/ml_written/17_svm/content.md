## 1. 개요 ( 마진 최대화의 직관

분류 문제를 풀 때, 두 클래스를 나누는 경계선은 무수히 많이 존재할 수 있다. 로지스틱 회귀나 퍼셉트론 같은 모델은 단순히 '오분류가 없는' 경계를 찾는 데 그친다. 그렇다면 무수히 많은 후보 중 **어떤 경계가 가장 좋은가?**

**SVM(Support Vector Machine)** 은 이 질문에 명확한 답을 제시한다. 바로 두 클래스로부터 **가장 멀리 떨어진** 경계, 즉 **마진(Margin)을 최대화하는 초평면(hyperplane)** 이 최적이라는 것이다.

마진이 클수록 새로운 데이터가 들어왔을 때 경계 근처에서 흔들릴 확률이 줄어든다. 이는 단순한 직관을 넘어 VC 이론(통계적 학습 이론)에 의해 뒷받침되는 수학적 근거이며, SVM이 특히 소규모 데이터셋에서 강력한 일반화 성능을 보이는 이유이기도 하다.

---

![SVM 마진과 서포트 벡터: 최대 마진 초평면과 경계를 결정하는 서포트 벡터](figures/svm_margin_support_vectors.png)
*SVM 마진과 서포트 벡터: 두 클래스 사이의 마진을 최대화하는 초평면과, 마진 경계에 위치한 서포트 벡터를 보여준다.*

## 2. 하드 마진 SVM

### 결정 초평면

$p$차원 공간에서 초평면(hyperplane)은 다음과 같이 정의된다.

$$\mathbf{w}^T\mathbf{x} + b = 0$$

여기서 $\mathbf{w}$는 초평면의 법선 벡터(normal vector)이고, $b$는 편향(bias)이다. 이 초평면을 기준으로 양의 클래스($y=+1$)는 $\mathbf{w}^T\mathbf{x} + b > 0$, 음의 클래스($y=-1$)는 $\mathbf{w}^T\mathbf{x} + b < 0$ 쪽에 위치한다.

### 마진의 정의

임의의 점 $\mathbf{x}$에서 초평면까지의 거리는 $\frac{|\mathbf{w}^T\mathbf{x} + b|}{\|\mathbf{w}\|}$로 계산된다. SVM은 두 클래스 경계면(각각 $\mathbf{w}^T\mathbf{x} + b = +1$과 $\mathbf{w}^T\mathbf{x} + b = -1$)을 설정하고, 이 두 면 사이의 거리, 즉 **마진**을 다음과 같이 정의한다.

$$\text{Margin} = \frac{2}{\|\mathbf{w}\|}$$

### 최적화 문제

마진을 최대화하는 것은 $\|\mathbf{w}\|$를 최소화하는 것과 동치다. 계산의 편의를 위해 $\frac{1}{2}\|\mathbf{w}\|^2$를 최소화하며, 제약 조건은 모든 데이터 포인트가 올바른 쪽에 위치해야 한다는 것이다.

$$\min_{\mathbf{w}, b} \frac{1}{2}\|\mathbf{w}\|^2 \quad \text{subject to} \quad y_i(\mathbf{w}^T\mathbf{x}_i + b) \geq 1, \; \forall i$$

이는 **볼록 이차 계획법(Convex Quadratic Programming)** 문제로, 전역 최솟값이 항상 유일하게 존재한다.

### 서포트 벡터(Support Vectors)의 역할

최적 초평면을 결정하는 데 실질적으로 기여하는 것은 경계면($\mathbf{w}^T\mathbf{x} + b = \pm 1$) 위에 놓인 데이터 포인트들뿐이다. 이를 **서포트 벡터**라 부른다. 나머지 학습 데이터를 제거하거나 위치를 바꿔도, 서포트 벡터만 그대로라면 결정 경계는 변하지 않는다. 이는 SVM이 **희소 해(sparse solution)** 를 가진다는 점에서 메모리 효율적이기도 하다.

---

## 3. 소프트 마진 SVM (C 파라미터)

현실 데이터는 완벽히 선형 분리되지 않는 경우가 대부분이다. 하드 마진 SVM은 노이즈나 이상치 한 개만 있어도 해가 존재하지 않을 수 있다. 이를 해결하기 위해 **슬랙 변수(slack variable)** $\xi_i \geq 0$를 도입한다.

슬랙 변수는 각 샘플이 마진을 얼마나 위반하는지를 측정한다. $\xi_i = 0$이면 마진을 완전히 만족, $0 < \xi_i \leq 1$이면 마진 안쪽에 있지만 올바른 쪽, $\xi_i > 1$이면 결정 경계를 넘어 오분류된 상태다.

소프트 마진 SVM의 최적화 문제는 다음과 같다.

$$\min_{\mathbf{w}, b, \boldsymbol{\xi}} \frac{1}{2}\|\mathbf{w}\|^2 + C \sum_{i=1}^{n} \xi_i$$
$$\text{subject to} \quad y_i(\mathbf{w}^T\mathbf{x}_i + b) \geq 1 - \xi_i, \quad \xi_i \geq 0, \; \forall i$$

**C 파라미터**는 마진 위반에 대한 페널티를 조절한다.

- **C가 크면**: 위반을 강하게 패널티하므로 하드 마진에 가까워진다. 훈련 데이터에 과적합될 위험이 있다.
- **C가 작으면**: 위반을 허용하여 더 넓은 마진을 선택한다. 정규화 효과가 강해져 일반화 성능이 높아질 수 있다.

이 관계를 요약하면: $C \uparrow \Rightarrow$ 편향 감소, 분산 증가 / $C \downarrow \Rightarrow$ 편향 증가, 분산 감소.

---

![커널 트릭 시각화: 비선형 데이터를 고차원 공간으로 매핑하여 선형 분리](figures/kernel_trick.png)
*커널 트릭: 원래 공간에서 선형 분리가 불가능한 데이터를 커널 함수를 통해 고차원 공간에 매핑하면 선형 초평면으로 분류할 수 있다.*

## 4. 커널 트릭(Kernel Trick)

선형 SVM은 선형 분리가 가능한 데이터에만 효과적이다. 비선형 데이터를 처리하려면 데이터를 고차원 공간으로 변환(매핑)한 뒤 선형 분리를 시도할 수 있다. 그러나 고차원 변환은 계산 비용이 폭발적으로 증가한다.

**커널 트릭**은 이 문제를 우아하게 해결한다. SVM의 최적화 문제를 쌍대 형식(dual form)으로 변환하면, 데이터 포인트는 항상 내적(inner product) 형태인 $\phi(\mathbf{x}_i)^T\phi(\mathbf{x}_j)$로만 등장한다. 커널 함수 $k(\mathbf{x}_i, \mathbf{x}_j)$를 사용하면 실제 고차원 매핑 $\phi$를 계산하지 않고도 내적 값을 직접 구할 수 있다.

$$k(\mathbf{x}_i, \mathbf{x}_j) = \phi(\mathbf{x}_i)^T\phi(\mathbf{x}_j)$$

### 대표적인 커널 함수

**RBF (가우시안) 커널** ) 가장 널리 사용되며, 무한 차원의 특성 공간에 대응한다.

$$k(\mathbf{x}, \mathbf{x}') = \exp\left(-\gamma\|\mathbf{x} - \mathbf{x}'\|^2\right)$$

$\gamma$가 크면 각 훈련 샘플의 영향 범위가 좁아져 과적합 위험이 높고, $\gamma$가 작으면 영향 범위가 넓어져 부드러운 경계가 형성된다.

**다항식 커널** ( 특성 간의 상호작용을 포착한다.

$$k(\mathbf{x}, \mathbf{x}') = (\mathbf{x}^T\mathbf{x}' + c)^d$$

$d$는 다항식 차수, $c$는 저차원 항의 영향을 조절하는 상수다.

**선형 커널** ) $k(\mathbf{x}, \mathbf{x}') = \mathbf{x}^T\mathbf{x}'$. 고차원 희소 데이터(예: 텍스트 분류)에 적합하며 SVM 중 가장 빠르다.

**시그모이드 커널**, $k(\mathbf{x}, \mathbf{x}') = \tanh(\alpha\mathbf{x}^T\mathbf{x}' + c)$. 신경망과 유사한 구조를 모델링할 수 있으나, 특정 조건에서만 유효한 커널이다.

---

## 5. C와 γ 파라미터 튜닝

SVM 성능은 **C**와 **γ**(RBF 커널 사용 시) 파라미터에 크게 의존한다. 일반적으로 **그리드 서치(Grid Search)** + **교차 검증(Cross-Validation)** 조합이 권장된다.

권장 탐색 범위:
- $C$: $[0.001, 0.01, 0.1, 1, 10, 100, 1000]$
- $\gamma$: $[10^{-4}, 10^{-3}, 10^{-2}, 10^{-1}, 1, 10]$ 또는 `'scale'`/`'auto'`

두 파라미터는 서로 상호작용하므로 반드시 **동시에** 탐색해야 한다. C가 클수록 $\gamma$를 작게 설정하는 방향이 안정적인 경우가 많다. 데이터가 클 때는 `RandomizedSearchCV`가 더 효율적이다.

---

## 6. SVM 회귀 (SVR)

SVM은 분류뿐 아니라 회귀 문제에도 적용할 수 있다. **SVR(Support Vector Regression)** 은 예측값과 실제값의 차이가 $\varepsilon$ 이내이면 손실을 0으로 간주하는 **$\varepsilon$-튜브** 개념을 사용한다.

$$\min \frac{1}{2}\|\mathbf{w}\|^2 + C\sum_{i=1}^{n}(\xi_i + \xi_i^*)$$
$$\text{subject to} \quad y_i - (\mathbf{w}^T\mathbf{x}_i + b) \leq \varepsilon + \xi_i, \quad (\mathbf{w}^T\mathbf{x}_i + b) - y_i \leq \varepsilon + \xi_i^*, \quad \xi_i, \xi_i^* \geq 0$$

$\varepsilon$이 클수록 더 많은 오차를 허용하는 넓은 튜브가 형성되고, $C$는 튜브 밖에 있는 샘플의 패널티를 조절한다. SVR도 커널 트릭을 그대로 활용할 수 있어 비선형 회귀 문제에도 강력하다.

---

## 7. 장단점 및 사용 시나리오

### 장점
- **이론적 견고함**: 마진 최대화는 VC 이론에 의해 일반화 오차 상한을 보장한다.
- **고차원 효과적**: 특성 수 $p$가 샘플 수 $n$보다 많은 경우(예: 유전체 데이터, 텍스트)에도 잘 동작한다.
- **커널 유연성**: 도메인 지식을 커널 설계에 반영할 수 있다.
- **희소 해**: 서포트 벡터만으로 모델이 결정되므로 메모리 효율적이다.
- **이상치 내성**: 소프트 마진을 통해 이상치의 영향을 제한할 수 있다.

### 단점
- **대규모 데이터에 느림**: 훈련 시간 복잡도가 $O(n^2)$~$O(n^3)$로 샘플 수가 많아지면 비현실적이다.
- **확률 미출력**: 기본 SVM은 클래스 확률을 출력하지 않는다. Platt 스케일링으로 추정은 가능하지만 추가 비용이 든다.
- **파라미터 민감성**: C, $\gamma$, 커널 선택에 따라 성능 차이가 크며, 체계적인 튜닝이 필요하다.
- **특성 스케일 의존**: 반드시 정규화(StandardScaler 등) 전처리가 필요하다.

### 추천 사용 시나리오
- 샘플 수 < 10만, 특성 수가 많은 경우
- 텍스트 분류, 이미지 분류 (딥러닝 이전 시대의 표준)
- 의료·생물 정보학처럼 고차원 소규모 데이터
- 명확한 마진 구조가 예상되는 이진 분류 문제

---

## 8. Python 코드

### SVC 기본 사용 및 결정 경계 시각화

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification, make_moons
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV, cross_val_score
from sklearn.metrics import classification_report

# 데이터 생성
X, y = make_moons(n_samples=300, noise=0.2, random_state=42)

# 전처리 + SVM 파이프라인
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('svm', SVC(kernel='rbf', C=1.0, gamma='scale', probability=True))
])
pipeline.fit(X, y)

# 교차 검증 점수
scores = cross_val_score(pipeline, X, y, cv=5, scoring='accuracy')
print(f"CV Accuracy: {scores.mean():.4f} ± {scores.std():.4f}")

# 결정 경계 시각화
def plot_decision_boundary(model, X, y, title='Decision Boundary'):
    scaler = model.named_steps['scaler']
    X_scaled = scaler.transform(X)

    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 300),
                         np.linspace(y_min, y_max, 300))
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    plt.figure(figsize=(7, 5))
    plt.contourf(xx, yy, Z, alpha=0.3, cmap='coolwarm')
    plt.scatter(X[:, 0], X[:, 1], c=y, cmap='coolwarm', edgecolors='k', s=40)

    # 서포트 벡터 표시
    svm = model.named_steps['svm']
    sv = scaler.inverse_transform(svm.support_vectors_)
    plt.scatter(sv[:, 0], sv[:, 1], s=120, facecolors='none',
                edgecolors='k', linewidths=2, label='Support Vectors')
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.show()

plot_decision_boundary(pipeline, X, y, title='RBF SVM 결정 경계')
```

```output
CV Accuracy: 0.9267 ± 0.0249
```

![Svm Fig 1](/media/figures/outputs/svm/svm_fig_1.png)

### 커널 비교

```python
kernels = ['linear', 'poly', 'rbf', 'sigmoid']
fig, axes = plt.subplots(1, 4, figsize=(20, 4))

for ax, kernel in zip(axes, kernels):
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('svm', SVC(kernel=kernel, C=1.0, gamma='scale'))
    ])
    model.fit(X, y)

    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 200),
                         np.linspace(y_min, y_max, 200))
    Z = model.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

    ax.contourf(xx, yy, Z, alpha=0.3, cmap='coolwarm')
    ax.scatter(X[:, 0], X[:, 1], c=y, cmap='coolwarm', edgecolors='k', s=20)
    cv_acc = cross_val_score(model, X, y, cv=5).mean()
    ax.set_title(f'{kernel} (CV: {cv_acc:.3f})')

plt.suptitle('커널별 결정 경계 비교', fontsize=14, y=1.02)
plt.tight_layout()
plt.show()
```

![Svm Fig 2](/media/figures/outputs/svm/svm_fig_2.png)

### 그리드 서치로 C와 γ 튜닝

```python
param_grid = {
    'svm__C': [0.01, 0.1, 1, 10, 100],
    'svm__gamma': [0.001, 0.01, 0.1, 1, 'scale']
}

grid_search = GridSearchCV(
    pipeline, param_grid, cv=5,
    scoring='accuracy', n_jobs=-1, verbose=1
)
grid_search.fit(X, y)

print(f"최적 파라미터: {grid_search.best_params_}")
print(f"최적 CV 정확도: {grid_search.best_score_:.4f}")

# 히트맵으로 파라미터 영향 시각화
import pandas as pd
results = pd.DataFrame(grid_search.cv_results_)

# 'scale' 제외 후 수치형만 히트맵
num_results = results[results['param_svm__gamma'] != 'scale'].copy()
pivot = num_results.pivot_table(
    index='param_svm__C',
    columns='param_svm__gamma',
    values='mean_test_score'
)
plt.figure(figsize=(8, 5))
import seaborn as sns
sns.heatmap(pivot, annot=True, fmt='.3f', cmap='YlOrRd')
plt.title('C vs γ 그리드 서치 결과 (CV Accuracy)')
plt.tight_layout()
plt.show()
```

```output
Fitting 5 folds for each of 25 candidates, totalling 125 fits
최적 파라미터: {'svm__C': 1, 'svm__gamma': 1}
최적 CV 정확도: 0.9633
```

![Svm Fig 3](/media/figures/outputs/svm/svm_fig_3.png)

위 코드를 실행하면 각 커널의 결정 경계 형태와 C·γ 파라미터가 성능에 미치는 영향을 직관적으로 확인할 수 있다. 실무에서는 항상 `StandardScaler`를 먼저 적용하고, `Pipeline`으로 전처리와 모델을 묶어 데이터 누수(data leakage)를 방지하는 것이 중요하다.