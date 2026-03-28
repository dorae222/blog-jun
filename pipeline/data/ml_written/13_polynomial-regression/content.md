## 왜 직선만으로는 부족한가

선형 회귀는 강력하고 해석하기 쉬운 모델이지만, 현실 데이터는 직선 관계보다 곡선 관계를 가지는 경우가 훨씬 많다. 주택 가격과 면적의 관계, 약물 농도와 효과, 자동차 속도와 연비처럼 많은 실제 현상이 비선형 패턴을 따른다.

이때 선형 회귀를 그대로 적용하면 높은 편향(Bias)을 가지는 모델이 만들어진다. 선형 모델이 데이터의 곡선 구조를 학습하지 못해 체계적으로 틀리는 것이다. **다항 회귀(Polynomial Regression)**는 이 문제를 입력 특성을 변환하는 방식으로 해결한다.

## 다항 회귀의 핵심 아이디어

다항 회귀의 핵심은 단순하다. 원래 특성 $x$에서 $x^2, x^3, \ldots, x^d$ 같은 거듭제곱 항을 새로운 특성으로 추가한 뒤, 이 확장된 특성 공간에서 선형 회귀를 수행한다.

$$\hat{y} = w_0 + w_1 x + w_2 x^2 + \cdots + w_d x^d$$

이 식은 $x$에 대해 비선형이지만, **계수 $w$에 대해서는 선형**이다. 따라서 선형 회귀의 최소자승법을 그대로 적용할 수 있다. 입력 공간은 비선형이지만 파라미터 공간은 선형인 것이 다항 회귀의 묘미다.

다변량 경우로 확장하면, 두 특성 $x_1, x_2$에 대해 2차 다항 특성은 다음과 같이 생성된다.

$$\{1,\ x_1,\ x_2,\ x_1^2,\ x_1 x_2,\ x_2^2\}$$

특성 수가 $n$개이고 차수가 $d$일 때 생성되는 특성의 수는 $\binom{n+d}{d}$로 기하급수적으로 증가한다는 점을 기억해야 한다.

## scikit-learn으로 구현하기

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

# 비선형 데이터 생성 (2차 함수 + 노이즈)
np.random.seed(42)
X = np.linspace(-3, 3, 200).reshape(-1, 1)
y = 0.5 * X**2 + X + 2 + np.random.randn(200, 1) * 0.5

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 여러 차수의 다항 회귀 비교
degrees = [1, 2, 5, 15]
fig, axes = plt.subplots(1, 4, figsize=(20, 5))
X_plot = np.linspace(-3, 3, 300).reshape(-1, 1)

for ax, degree in zip(axes, degrees):
    model = Pipeline([
        ('poly', PolynomialFeatures(degree=degree, include_bias=False)),
        ('linear', LinearRegression())
    ])
    model.fit(X_train, y_train)
    y_pred = model.predict(X_plot)

    train_rmse = np.sqrt(mean_squared_error(y_train, model.predict(X_train)))
    test_rmse  = np.sqrt(mean_squared_error(y_test,  model.predict(X_test)))

    ax.scatter(X_train, y_train, alpha=0.4, s=15, label='train')
    ax.plot(X_plot, y_pred, color='red', linewidth=2)
    ax.set_title(f'Degree {degree}\nTrain RMSE: {train_rmse:.3f} | Test RMSE: {test_rmse:.3f}')
    ax.legend()

plt.tight_layout()
plt.show()
```

![다항 회귀 차수별 비교](figures/polynomial_degrees_comparison.png)

*Figure 1: 다항 회귀 차수별 비교: 차수 1(직선)은 과소적합, 차수 2는 적절한 피팅, 차수 15는 노이즈까지 학습하여 과적합이 발생한다.*

차수 1(직선)은 곡선을 전혀 포착하지 못하고, 차수 2는 실제 함수에 근접한다. 차수 15에서는 학습 데이터의 노이즈까지 암기해버려 테스트 오차가 폭등하는 **과적합(Overfitting)**이 일어난다.

## 학습 곡선으로 과적합 진단하기

학습 곡선(Learning Curve)은 훈련 세트 크기를 점진적으로 늘리면서 훈련 오차와 검증 오차를 함께 그린 그래프다. 과적합된 모델은 훈련 오차는 낮지만 검증 오차는 높아 두 곡선 사이에 큰 간격이 생긴다.

```python
from sklearn.model_selection import learning_curve

def plot_learning_curve(model, X, y, title):
    train_sizes, train_scores, val_scores = learning_curve(
        model, X, y,
        train_sizes=np.linspace(0.1, 1.0, 10),
        cv=5, scoring='neg_mean_squared_error'
    )
    train_rmse = np.sqrt(-train_scores.mean(axis=1))
    val_rmse   = np.sqrt(-val_scores.mean(axis=1))

    plt.figure(figsize=(8, 5))
    plt.plot(train_sizes, train_rmse, 'o-', label='Training RMSE')
    plt.plot(train_sizes, val_rmse,   's-', label='Validation RMSE')
    plt.title(title)
    plt.xlabel('Training set size')
    plt.ylabel('RMSE')
    plt.legend()
    plt.grid(True)
    plt.show()

# 과적합 모델 vs 적절한 모델 비교
for deg, label in [(2, 'Degree 2 (적절)'), (15, 'Degree 15 (과적합)')]:
    pipe = Pipeline([
        ('poly', PolynomialFeatures(degree=deg)),
        ('linear', LinearRegression())
    ])
    plot_learning_curve(pipe, X, y.ravel(), label)
```

![학습/테스트 오차 vs 다항 차수](figures/train_test_error_vs_degree.png)

*Figure 2: 학습 곡선 비교: 차수 2(적절한 모델)와 차수 15(과적합 모델)의 학습/검증 RMSE 변화를 통해 과적합을 진단한다.*

## 로그·제곱근 변환: 비선형 변환의 다른 형태

다항 특성 외에도 도메인 지식을 활용한 비선형 변환이 자주 쓰인다.

**로그 변환**은 오른쪽으로 치우친 분포(소득, 주택 가격, 인구 등)를 정규 분포에 가깝게 만들고, 곱셈 관계를 덧셈 관계로 바꾼다.

$$y = e^{\beta_0 + \beta_1 \log x} = e^{\beta_0} \cdot x^{\beta_1}$$

**제곱근 변환**은 분산이 평균에 비례하는 카운트 데이터(포아송 분포)에 효과적이다.

```python
import pandas as pd
from sklearn.preprocessing import FunctionTransformer

# 로그 변환 파이프라인
log_transformer = FunctionTransformer(np.log1p, validate=True)

pipe_log = Pipeline([
    ('log', log_transformer),
    ('linear', LinearRegression())
])

# 제곱근 변환
sqrt_transformer = FunctionTransformer(np.sqrt, validate=True)

# 적용 예시 (양수 특성에만 사용 가능)
X_pos = np.abs(X) + 0.1  # 양수 보장
pipe_log.fit(X_pos, y)
```

![학습/테스트 오차 vs 다항 차수: 과적합 진단 곡선](figures/train_test_error_vs_degree.png)
*학습/테스트 오차 vs 차수: 차수가 증가할수록 학습 오차는 계속 감소하지만, 테스트 오차는 특정 지점 이후 증가하여 과적합을 나타낸다.*

## 어떤 차수를 선택해야 하는가

차수 선택은 편향-분산 트레이드오프의 핵심이다. 실전에서는 다음 방법을 활용한다.

1. **교차 검증(Cross-Validation)**: 여러 차수에 대해 CV 점수를 비교한다.
2. **정규화(Regularization)**: Ridge/Lasso를 결합하면 높은 차수도 안전하게 사용할 수 있다. 불필요한 계수를 0으로 수렴시켜 과적합을 자동으로 억제한다.
3. **학습 곡선**: 데이터가 충분하면 더 높은 차수도 감당할 수 있다.

```python
from sklearn.linear_model import RidgeCV

# Ridge 정규화 + 고차 다항 특성
pipe_ridge = Pipeline([
    ('poly', PolynomialFeatures(degree=10, include_bias=False)),
    ('ridge', RidgeCV(alphas=np.logspace(-3, 3, 50), cv=5))
])
pipe_ridge.fit(X_train, y_train.ravel())
print(f"최적 alpha: {pipe_ridge.named_steps['ridge'].alpha_:.4f}")
print(f"Test RMSE: {np.sqrt(mean_squared_error(y_test, pipe_ridge.predict(X_test))):.4f}")
```

```output
최적 alpha: 0.3728
Test RMSE: 0.4481
```

## 다항 회귀 vs 다른 비선형 모델: 언제 무엇을 선택할 것인가

다항 회귀는 비선형 관계를 모델링하는 유일한 방법이 아니다. 실전에서는 문제의 특성에 따라 여러 대안이 존재하며, 각각의 장단점을 이해하는 것이 중요하다.

**스플라인 회귀(Spline Regression)**는 데이터 영역을 구간(knot)으로 나누고 각 구간에서 저차 다항식을 피팅한다. 3차 스플라인(Cubic Spline)이 가장 널리 쓰이며, 구간 경계에서 연속성과 미분 가능성을 보장한다. 다항 회귀가 전체 데이터에 하나의 고차 다항식을 피팅하는 반면, 스플라인은 국소적으로 저차 다항식을 사용하므로 Runge 현상(고차 다항식의 경계 진동)을 피할 수 있다. 데이터의 서로 다른 영역에서 다른 패턴을 보일 때 스플라인이 다항 회귀보다 훨씬 유리하다.

**일반화 가법 모형(GAM, Generalized Additive Model)**은 각 특성에 비선형 함수를 개별적으로 적용한 뒤 합산하는 모델이다.

$$\hat{y} = \beta_0 + f_1(x_1) + f_2(x_2) + \cdots + f_p(x_p)$$

각 $f_j$는 스플라인이나 다른 비모수적 함수로 추정된다. GAM은 해석 가능성과 유연성의 균형이 뛰어나며, 각 특성의 개별 효과를 시각화할 수 있다는 장점이 있다. 다만 특성 간 교호작용(interaction)을 자동으로 학습하지 못한다는 한계가 있다.

**커널 회귀(Kernel Regression)**는 예측 지점 근처의 데이터에 가중치를 부여하여 국소적으로 회귀를 수행한다. 대역폭(bandwidth) 파라미터로 평활도를 조절하며, 데이터의 밀도에 따라 적응적으로 복잡도가 결정된다. 특성 수가 적고 데이터가 충분할 때 강력하지만, 고차원에서는 "차원의 저주"로 인해 성능이 급격히 하락한다.

| 모델 | 최적 사용 상황 | 주요 장점 | 주요 단점 |
|---|---|---|---|
| 다항 회귀 | 전역적 매끄러운 곡선, 저차(2~4차) | 구현 단순, 해석 용이 | 고차에서 불안정 |
| 스플라인 | 구간별 패턴 변화, 복잡한 곡선 | Runge 현상 없음 | knot 위치 선택 필요 |
| GAM | 다변량, 각 특성별 비선형 | 개별 효과 해석 가능 | 교호작용 수동 추가 |
| 커널 회귀 | 저차원, 데이터 풍부 | 모델 가정 최소 | 고차원에 취약 |

실전에서는 특성 수가 적고 관계가 단순할 때 다항 회귀, 국소적 복잡성이 있으면 스플라인, 다변량 해석이 필요하면 GAM을 우선 고려한다.

## 실전 사례: 주택 가격 예측에서의 다항 회귀

다항 회귀가 실제로 어떻게 활용되는지 주택 가격 예측 사례로 살펴보자. 주택 면적과 가격의 관계는 전형적인 비선형 패턴이다. 작은 면적에서는 면적 증가에 따라 가격이 급격히 오르지만, 큰 면적에서는 증가폭이 완만해진다.

```python
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
import numpy as np

# 주택 면적(평방미터)과 가격(억원) 시뮬레이션
np.random.seed(42)
area = np.random.uniform(30, 200, 300).reshape(-1, 1)
# 실제 관계: 로그적 증가 + 노이즈
price = 0.8 * np.log(area) - 1.5 + np.random.randn(300, 1) * 0.3

# 다항 회귀 차수별 교차 검증 성능 비교
for degree in [1, 2, 3, 4]:
    pipe = Pipeline([
        ('scaler', StandardScaler()),
        ('poly', PolynomialFeatures(degree=degree, include_bias=False)),
        ('ridge', Ridge(alpha=1.0))
    ])
    scores = cross_val_score(pipe, area, price.ravel(), cv=5,
                             scoring='neg_mean_squared_error')
    rmse = np.sqrt(-scores.mean())
    print(f"차수 {degree}: CV RMSE = {rmse:.4f}")
```

```output
차수 1: CV RMSE = 0.3842
차수 2: CV RMSE = 0.3105
차수 3: CV RMSE = 0.3098
차수 4: CV RMSE = 0.3101
```

2차 다항식에서 성능이 크게 개선되고, 3차 이후로는 거의 향상이 없다. 이는 실제 관계가 로그 함수에 가깝기 때문이다. 이런 경우 다항 회귀보다 로그 변환이 더 적절한 선택이며, 도메인 지식의 중요성을 잘 보여준다.

의료 분야에서도 다항 회귀는 **용량-반응 곡선(Dose-Response Curve)** 모델링에 널리 쓰인다. 약물 농도와 효과의 관계는 S자(sigmoidal) 곡선을 따르는 경우가 많으며, 저차 다항 회귀로 효과적 농도 범위를 추정할 수 있다.

## 다항 회귀의 정규화 심화: Ridge, Lasso, 그리고 수치 안정성

앞서 Ridge 정규화를 간략히 소개했지만, 다항 회귀에서 정규화는 선택이 아닌 필수다. 고차 다항식의 계수는 매우 큰 값을 가질 수 있어 수치적 불안정성을 초래한다.

**Ridge 회귀(L2 정규화)**는 다음 목적 함수를 최소화한다.

$$J(\mathbf{w}) = \|\mathbf{y} - \mathbf{X}\mathbf{w}\|_2^2 + \alpha \|\mathbf{w}\|_2^2$$

Ridge는 모든 계수를 0에 가깝게 축소하되 완전히 0으로 만들지는 않는다. 다항 회귀에서 Ridge는 고차 항의 계수를 억제하여 사실상 유효 차수를 낮추는 효과를 가진다. $\alpha$가 충분히 크면 차수 10의 다항식도 차수 2~3 수준의 복잡도로 동작할 수 있다.

**Lasso 회귀(L1 정규화)**는 불필요한 다항 항의 계수를 정확히 0으로 만든다.

$$J(\mathbf{w}) = \|\mathbf{y} - \mathbf{X}\mathbf{w}\|_2^2 + \alpha \|\mathbf{w}\|_1$$

Lasso는 자동 특성 선택 기능이 있어, 어떤 차수의 항이 실제로 필요한지 알 수 없을 때 유용하다. 예를 들어 차수 10으로 설정하더라도 Lasso가 $x^2$와 $x^3$ 항의 계수만 남기고 나머지를 0으로 만들 수 있다.

**Elastic Net**은 Ridge와 Lasso를 결합한 정규화로, 상관된 다항 특성이 많을 때 Lasso보다 안정적인 결과를 제공한다.

```python
from sklearn.linear_model import Lasso, ElasticNet

# Lasso로 자동 특성 선택
pipe_lasso = Pipeline([
    ('scaler', StandardScaler()),
    ('poly', PolynomialFeatures(degree=10, include_bias=False)),
    ('lasso', Lasso(alpha=0.01, max_iter=10000))
])
pipe_lasso.fit(X_train, y_train.ravel())

# 어떤 항의 계수가 살아남았는지 확인
coefs = pipe_lasso.named_steps['lasso'].coef_
nonzero = np.sum(coefs != 0)
print(f"전체 특성 수: {len(coefs)}, 0이 아닌 계수: {nonzero}")
```

핵심은 다항 회귀에서 정규화 없이 높은 차수를 사용하면 안 된다는 것이다. 특히 **조건수(Condition Number)**가 기하급수적으로 증가하여 역행렬 계산이 수치적으로 불안정해진다.

## 계산 복잡도: 고차 다항식이 비싼 이유

다항 회귀의 계산 비용은 차수와 특성 수에 따라 급격히 증가한다. 특성 수 $n$, 차수 $d$일 때 생성되는 다항 특성의 수는 $\binom{n+d}{d}$이다. 몇 가지 예를 살펴보면:

| 특성 수 $(n)$ | 차수 $(d)$ | 다항 특성 수 |
|---|---|---|
| 5 | 2 | 21 |
| 5 | 5 | 252 |
| 10 | 3 | 286 |
| 10 | 5 | 3,003 |
| 20 | 3 | 1,771 |
| 20 | 5 | 53,130 |

20개 특성에 5차 다항식을 적용하면 5만 개 이상의 특성이 생성된다. 이는 메모리와 학습 시간 모두에 큰 부담이 된다. 선형 회귀의 정규 방정식은 $O(p^2 N + p^3)$의 복잡도를 가지며 ($p$: 특성 수, $N$: 샘플 수), 다항 특성 확장 후에는 $p$가 폭발적으로 커져 실용적이지 않을 수 있다.

이런 이유로 실전에서는 다변량 데이터에 고차 다항 회귀를 직접 적용하기보다, **interaction_only=True** 옵션으로 교호작용 항만 생성하거나, 트리 기반 모델이나 커널 방법으로 우회하는 것이 일반적이다.

## 실전에서의 함정과 주의사항

다항 회귀를 실전에 적용할 때 반드시 알아야 할 함정들이 있다.

### 특성 스케일링의 중요성

다항 특성은 원래 특성의 거듭제곱이므로, 스케일이 다른 특성이 있으면 다항 변환 후 스케일 차이가 극적으로 벌어진다. 예를 들어 $x = 1000$이면 $x^3 = 10^9$이 된다. **반드시 다항 변환 전에 표준화(StandardScaler)를 수행**해야 수치적 안정성을 확보할 수 있다.

```python
# 올바른 순서: 스케일링 → 다항 변환 → 회귀
correct_pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('poly', PolynomialFeatures(degree=5)),
    ('ridge', Ridge(alpha=1.0))
])

# 잘못된 순서: 다항 변환 → 스케일링 (수치 불안정)
wrong_pipe = Pipeline([
    ('poly', PolynomialFeatures(degree=5)),
    ('scaler', StandardScaler()),
    ('ridge', Ridge(alpha=1.0))
])
```

### 외삽의 위험

다항 회귀의 가장 치명적인 약점은 **외삽(Extrapolation)**이다. 학습 데이터 범위 밖에서 다항 함수는 급격히 발산하거나 수렴한다. 5차 다항식이 학습 범위 안에서 아무리 잘 피팅되더라도, 범위 밖에서는 $x^5$ 항이 지배하면서 비현실적인 예측을 만들어낸다. 이는 스플라인이나 GAM에서도 동일하게 발생하는 문제이지만, 고차 다항식에서 특히 심각하다.

### 다중공선성

다항 특성 $x, x^2, x^3, \ldots$는 서로 강하게 상관되어 있다. 이 **다중공선성(Multicollinearity)**은 계수 추정의 분산을 크게 높이고, 개별 계수의 해석을 불가능하게 만든다. 직교 다항식(Orthogonal Polynomials)을 사용하면 이 문제를 완화할 수 있지만, scikit-learn에서는 StandardScaler + Ridge 조합이 더 실용적인 해결책이다.

## 정리

다항 회귀는 특성 공학의 가장 기본적인 형태로, 선형 모델의 표현력을 곡선까지 확장시킨다. 그러나 차수가 증가할수록 모델 복잡도가 폭발적으로 커지므로 학습 곡선과 교차 검증으로 과적합을 반드시 모니터링해야 한다. 고차 다항식의 수치 불안정성, 외삽의 위험, 계산 비용 폭발 등을 고려하면, 실전에서는 2~3차를 넘기지 않는 것이 안전하다. Ridge 정규화와 결합하거나, 도메인 지식을 활용한 로그·제곱근 변환을 먼저 시도하고, 더 복잡한 비선형 관계가 필요하면 스플라인이나 GAM으로 전환하는 것이 좋은 전략이다.