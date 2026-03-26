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

![Polynomial-Regression Fig 1](/media/figures/outputs/polynomial-regression/polynomial-regression_fig_1.png)

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

![Polynomial-Regression Fig 2](/media/figures/outputs/polynomial-regression/polynomial-regression_fig_2.png)

![Polynomial-Regression Fig 3](/media/figures/outputs/polynomial-regression/polynomial-regression_fig_3.png)

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

## 정리

다항 회귀는 특성 공학의 가장 기본적인 형태로, 선형 모델의 표현력을 곡선까지 확장시킨다. 그러나 차수가 증가할수록 모델 복잡도가 폭발적으로 커지므로 학습 곡선과 교차 검증으로 과적합을 반드시 모니터링해야 한다. 실전에서는 Ridge 정규화와 결합하거나, 도메인 지식을 활용한 로그·제곱근 변환을 먼저 시도하는 것이 좋은 출발점이다.