<!-- infographic-hero -->
![Linear Regression 핵심 요약](figures/infographic.svg)

*Figure: Linear Regression 한 장 요약 인포그래픽*

## 개요: 가장 단순하고 강력한 예측 모델

**선형 회귀(Linear Regression)**는 입력 변수(특성)와 연속적인 출력 변수(타깃) 사이의 선형 관계를 모델링하는 지도학습 알고리즘입니다. 1805년 Legendre와 Gauss가 천문 관측 오차를 최소화하기 위해 최소제곱법(Least Squares)을 개발한 것이 기원으로, 200년이 지난 지금도 실무에서 가장 먼저 적용해보는 기준 모델(Baseline Model)입니다.

선형 회귀가 지금도 강력한 이유는 세 가지입니다:

- **해석 가능성**: 각 계수($w_j$)가 특성 한 단위 변화에 대한 타깃의 변화량을 직접 의미합니다.
- **연산 효율성**: 해석적 해(Closed-form Solution)가 존재하여 반복 학습 없이도 최적 파라미터를 구할 수 있습니다.
- **이론적 기반**: 통계적 추론(신뢰구간, 가설 검정)과 직접 연결되어 결과를 검증할 수 있습니다.

복잡한 모델이 항상 좋은 것은 아닙니다. 관계가 실제로 선형에 가깝거나, 데이터가 적거나, 해석이 중요한 상황이라면 선형 회귀가 XGBoost보다 나은 선택일 수 있습니다.

---

## 수학적 표현

### 단변량 선형 회귀

입력 변수가 하나인 단순 선형 회귀(Simple Linear Regression)는 다음과 같이 표현됩니다:

$$\hat{y} = w_1 x + b$$

여기서 $w_1$은 기울기(slope), $b$는 절편(intercept)입니다. 시각적으로 이는 데이터 포인트를 통과하는 가장 잘 맞는 직선을 찾는 문제입니다.

### 다변량 선형 회귀

입력 변수가 $n$개인 다중 선형 회귀(Multiple Linear Regression)는:

$$\hat{y} = w_1 x_1 + w_2 x_2 + \cdots + w_n x_n + b = \mathbf{w}^T \mathbf{x} + b$$

여기서 $\mathbf{w} = [w_1, w_2, \ldots, w_n]^T$는 가중치 벡터, $\mathbf{x} = [x_1, x_2, \ldots, x_n]^T$는 특성 벡터입니다.

### 행렬 표현

$m$개의 샘플을 한꺼번에 표현할 때는 행렬 형식이 편리합니다. 절편 항을 포함하기 위해 각 샘플에 1을 추가한 설계 행렬(Design Matrix) $X \in \mathbb{R}^{m \times (n+1)}$을 사용합니다:

$$X = \begin{bmatrix} 1 & x_1^{(1)} & x_2^{(1)} & \cdots & x_n^{(1)} \\ 1 & x_1^{(2)} & x_2^{(2)} & \cdots & x_n^{(2)} \\ \vdots & \vdots & \vdots & \ddots & \vdots \\ 1 & x_1^{(m)} & x_2^{(m)} & \cdots & x_n^{(m)} \end{bmatrix}, \quad \mathbf{w} = \begin{bmatrix} b \\ w_1 \\ \vdots \\ w_n \end{bmatrix}$$

그러면 전체 예측은 간결하게:

$$\hat{\mathbf{y}} = X\mathbf{w}$$

---

## 손실 함수 (Loss Function)

### 잔차 제곱합 (RSS, Residual Sum of Squares)

모델이 얼마나 틀렸는지는 **잔차(Residual)** $e_i = y_i - \hat{y}_i$로 측정합니다. 잔차에 절댓값 대신 제곱을 취하는 이유는 두 가지입니다: 미분이 용이하고, 큰 오차에 더 강한 패널티를 부여합니다.

$$\mathcal{L}_{\text{RSS}} = \sum_{i=1}^{m} (y_i - \hat{y}_i)^2 = \|\mathbf{y} - X\mathbf{w}\|_2^2$$

### 평균 제곱 오차 (MSE, Mean Squared Error)

샘플 수 $m$으로 나누어 스케일을 정규화한 것이 MSE입니다:

$$\mathcal{L}_{\text{MSE}} = \frac{1}{m} \sum_{i=1}^{m} (y_i - \hat{y}_i)^2$$

MSE는 단위가 타깃의 제곱이므로, 해석 편의를 위해 RMSE(Root MSE) $= \sqrt{\mathcal{L}_{\text{MSE}}}$를 함께 사용합니다. 또한 예측 오차의 비율적 평가가 필요하면 MAE나 MAPE도 고려합니다. 평가 지표 전반은 [[regression-metrics]]에서 자세히 다룹니다.

---

## 파라미터 추정 방법

![OLS 시각화: 최소제곱법으로 데이터에 가장 잘 맞는 직선 찾기](figures/ols_visualization.png)
*OLS(최소제곱법): 데이터 포인트들과 회귀 직선 사이의 잔차 제곱합을 최소화하는 최적의 파라미터를 찾는 과정을 보여준다.*

### 방법 1: OLS 해석적 해 (정규방정식)

$\mathcal{L}_{\text{RSS}} = \|\mathbf{y} - X\mathbf{w}\|_2^2$를 $\mathbf{w}$에 대해 미분하고 0으로 놓으면:

$$\frac{\partial \mathcal{L}}{\partial \mathbf{w}} = -2X^T(\mathbf{y} - X\mathbf{w}) = 0$$

$$X^TX\mathbf{w} = X^T\mathbf{y}$$

$X^TX$가 역행렬 가능(가역)하다면, 닫힌 형태의 최적해인 **정규방정식(Normal Equation)**을 구할 수 있습니다:

$$\hat{\mathbf{w}}_{\text{OLS}} = (X^TX)^{-1}X^T\mathbf{y}$$

$X^+=(X^TX)^{-1}X^T$를 **무어-펜로즈 유사역행렬(Moore-Penrose Pseudoinverse)**이라 하며, $\hat{\mathbf{w}} = X^+\mathbf{y}$로 쓸 수 있습니다.

**OLS의 장점**: 단 한 번의 계산으로 정확한 최적해를 얻습니다. 하이퍼파라미터(학습률, 반복 횟수)가 없습니다.

**OLS의 단점**: 행렬 역산의 계산 복잡도는 $O(n^3)$입니다. 특성 수 $n$이 수만 개를 넘으면 메모리와 연산 비용이 급증합니다. 또한 $X^TX$가 특이행렬(Singular Matrix)이면 역행렬이 존재하지 않습니다(다중공선성 문제).

### 방법 2: 경사하강법 (Gradient Descent)

대규모 데이터에서는 반복적 최적화인 경사하강법을 사용합니다. MSE 손실에 대한 기울기는:

$$\frac{\partial \mathcal{L}_{\text{MSE}}}{\partial \mathbf{w}} = \frac{2}{m} X^T(X\mathbf{w} - \mathbf{y})$$

파라미터 업데이트 규칙:

$$\mathbf{w} \leftarrow \mathbf{w} - \alpha \frac{\partial \mathcal{L}}{\partial \mathbf{w}} = \mathbf{w} - \frac{2\alpha}{m} X^T(X\mathbf{w} - \mathbf{y})$$

여기서 $\alpha > 0$은 **학습률(Learning Rate)**입니다. 학습률이 너무 크면 발산하고, 너무 작으면 수렴이 느립니다.

실제로는 전체 데이터를 한 번에 쓰는 배치 경사하강법(BGD) 대신, 소규모 미니배치(Mini-batch GD)나 샘플 하나씩 업데이트하는 확률적 경사하강법(SGD)을 사용합니다.

### 두 방법 비교

| 기준 | OLS (정규방정식) | 경사하강법 |
|------|-----------------|------------|
| 수렴 | 단 1번 계산으로 정확한 해 | 반복 수렴, 근사해 |
| 특성 수 $n$ | $n < 10{,}000$ 이하 권장 | 대규모 $n$에도 적합 |
| 샘플 수 $m$ | 메모리에 $X$ 적재 필요 | 미니배치로 처리 가능 |
| 특성 스케일링 | 불필요 | 필수 (학습률 안정화) |
| 다중공선성 | 역행렬 불가 | 여전히 작동하나 불안정 |

---

![선형 회귀 잔차 분석: 잔차 패턴을 통한 모델 진단](figures/linear_regression_residual.png)
*잔차 분석: 잔차 vs 예측값 플롯에서 패턴이 없으면 선형성과 등분산성 가정이 충족되며, 패턴이 보이면 모델 개선이 필요하다.*

## 선형 회귀의 5가지 가정 (Gauss-Markov 조건)

OLS 추정량이 **BLUE(Best Linear Unbiased Estimator)**이 되기 위해서는 다음 다섯 가지 가정이 필요합니다. 가정 위반 시 계수 추정이 편향되거나 표준오차가 왜곡됩니다.

### 1. 선형성 (Linearity)

타깃 $y$가 특성 $\mathbf{x}$와 파라미터 $\mathbf{w}$에 대해 선형이어야 합니다:

$$y_i = \mathbf{w}^T \mathbf{x}_i + \epsilon_i$$

**진단**: 잔차(Residuals) vs 예측값($\hat{y}$) 산점도에서 패턴이 없어야 합니다. 곡선 패턴이 보이면 비선형 변환(로그, 제곱근) 또는 다항 특성을 추가합니다.

### 2. 오차 독립성 (Independence of Errors)

각 관측의 오차항 $\epsilon_i$는 서로 독립이어야 합니다:

$$\text{Cov}(\epsilon_i, \epsilon_j) = 0 \quad (i \neq j)$$

**진단**: 시계열 데이터에서 자주 위반됩니다. Durbin-Watson 통계량(2에 가까울수록 독립)으로 확인합니다. 위반 시 시계열 모델(ARIMA)이나 일반화 최소제곱법(GLS)을 고려합니다.

### 3. 등분산성 (Homoscedasticity)

모든 관측에서 오차의 분산이 일정해야 합니다:

$$\text{Var}(\epsilon_i) = \sigma^2 \quad \text{(상수)}$$

분산이 일정하지 않은 경우를 **이분산성(Heteroscedasticity)**이라 합니다.

**진단**: 잔차 vs 예측값 산점도에서 깔때기(funnel) 모양이 보이면 위반입니다. Breusch-Pagan 검정으로 확인합니다. 위반 시 타깃 변수에 로그 변환을 적용하거나 가중 최소제곱법(WLS)을 사용합니다.

### 4. 오차의 정규성 (Normality of Errors)

오차항은 정규분포를 따라야 합니다:

$$\epsilon_i \sim \mathcal{N}(0, \sigma^2)$$

이 가정은 소표본에서 신뢰구간과 가설 검정(t-test, F-test)의 유효성을 위해 필요합니다. 대표본에서는 중심극한정리에 의해 완화됩니다.

**진단**: Q-Q plot(Quantile-Quantile plot)에서 점들이 대각선에 가까이 위치해야 합니다. Shapiro-Wilk 검정으로 확인합니다.

### 5. 다중공선성 없음 (No Perfect Multicollinearity)

독립 변수들 사이에 완전한 선형 관계가 없어야 합니다. 완전 다중공선성이 있으면 $X^TX$가 특이행렬이 되어 OLS 해가 존재하지 않습니다.

---

## 다중공선성 (Multicollinearity)

완전한 다중공선성이 아니더라도 독립 변수들 간에 강한 선형 관계가 있으면 계수 추정이 불안정해집니다. 계수의 표준오차가 커지고, 부호가 이론과 반대로 나오거나 값이 급변하는 현상이 나타납니다.

### VIF (Variance Inflation Factor)

각 독립 변수 $x_j$를 나머지 변수들로 회귀분석한 결정계수 $R_j^2$를 이용해 계산합니다:

$$\text{VIF}_j = \frac{1}{1 - R_j^2}$$

- $\text{VIF} = 1$: 다중공선성 없음
- $\text{VIF} < 5$: 허용 가능
- $\text{VIF} \geq 10$: 심각한 다중공선성, 조치 필요

해결 방법:
1. **변수 제거**: VIF가 높은 변수 중 하나를 제거합니다.
2. **차원 축소**: PCA로 상관된 변수들을 주성분으로 변환합니다.
3. **정규화**: Ridge 회귀($L_2$ 페널티)로 계수 추정을 안정화합니다. 자세한 내용은 [[regularized-regression]]을 참고하세요.

---

## 계수 해석

### 비표준화 계수 $w_j$

$w_j$는 **다른 변수들을 고정했을 때, $x_j$가 1단위 증가하면 $\hat{y}$가 $w_j$만큼 변한다**는 뜻입니다(편미분 해석). 예를 들어 집값 모델에서 `면적(m²)` 계수가 50(만 원)이라면, 다른 조건이 같을 때 면적이 1m² 넓어질수록 예측 집값이 50만 원 증가한다고 해석합니다.

단, 비표준화 계수는 특성마다 단위(스케일)가 달라 서로 크기를 직접 비교할 수 없습니다.

### 표준화 계수 (Standardized Coefficients, Beta)

특성들을 평균 0, 표준편차 1로 표준화한 뒤 회귀분석하면, 계수들을 직접 비교하여 **어떤 변수가 타깃에 더 큰 영향**을 미치는지 파악할 수 있습니다:

$$\tilde{x}_j = \frac{x_j - \mu_j}{\sigma_j}, \quad \tilde{w}_j = w_j \cdot \frac{\sigma_j}{\sigma_y}$$

$|\tilde{w}_j|$가 클수록 해당 변수의 상대적 중요도가 높습니다.

### 결정계수 $R^2$

모델이 전체 분산의 얼마나 설명하는지 나타내는 지표입니다:

$$R^2 = 1 - \frac{\text{RSS}}{\text{TSS}} = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$

$R^2 = 1$은 완벽한 예측, $R^2 = 0$은 단순 평균 예측과 동일함을 의미합니다. 변수를 추가할수록 $R^2$는 항상 증가하므로, 변수 수에 패널티를 부여한 **수정 $R^2$(Adjusted $R^2$)**를 함께 확인합니다:

$$\bar{R}^2 = 1 - (1 - R^2) \frac{m - 1}{m - n - 1}$$

---

## Python 코드: sklearn + statsmodels 회귀 분석 및 진단

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson

# ── 1. 데이터 로드 및 분할 ─────────────────────────────────────────────────
housing = fetch_california_housing(as_frame=True)
X, y = housing.data, housing.target  # 타깃: 주택 중위 가격 (단위: $100,000)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ── 2. sklearn으로 빠른 학습 및 평가 ──────────────────────────────────────
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

model = LinearRegression()
model.fit(X_train_s, y_train)

y_pred = model.predict(X_test_s)
mse  = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
r2   = r2_score(y_test, y_pred)

print(f"RMSE : {rmse:.4f}")
print(f"R²   : {r2:.4f}")

# 비표준화 계수와 표준화 계수 확인
coef_df = pd.DataFrame({
    "feature"   : X.columns,
    "coef"      : model.coef_,          # 비표준화 (스케일된 입력 기준)
    "std_coef"  : model.coef_ * X_train.std().values / y_train.std()
}).sort_values("std_coef", key=abs, ascending=False)
print(coef_df)

# ── 3. statsmodels로 통계적 추론 ──────────────────────────────────────────
# 절편 항 추가 (statsmodels는 자동으로 추가하지 않음)
X_train_sm = sm.add_constant(X_train_s)
ols_model  = sm.OLS(y_train, X_train_sm).fit()
print(ols_model.summary())  # 계수, p-value, 신뢰구간, F-통계량 등

# ── 4. VIF 계산으로 다중공선성 진단 ───────────────────────────────────────
vif_data = pd.DataFrame()
vif_data["feature"] = X.columns
vif_data["VIF"]     = [
    variance_inflation_factor(X_train_s, i)
    for i in range(X_train_s.shape[1])
]
print("\nVIF 진단:")
print(vif_data.sort_values("VIF", ascending=False))

# ── 5. 잔차 진단 플롯 ─────────────────────────────────────────────────────
residuals = y_train.values - ols_model.fittedvalues

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

# (a) 잔차 vs 예측값: 선형성 & 등분산성 확인
axes[0].scatter(ols_model.fittedvalues, residuals, alpha=0.3, s=10)
axes[0].axhline(0, color="red", lw=1)
axes[0].set_xlabel("예측값")
axes[0].set_ylabel("잔차")
axes[0].set_title("잔차 vs 예측값")

# (b) Q-Q Plot: 정규성 확인
sm.qqplot(residuals, line="s", ax=axes[1])
axes[1].set_title("Q-Q Plot (정규성 검정)")

# (c) 잔차 히스토그램
axes[2].hist(residuals, bins=50, edgecolor="white")
axes[2].set_xlabel("잔차")
axes[2].set_title("잔차 분포")

plt.tight_layout()
plt.savefig("residual_diagnostics.png", dpi=150)
plt.show()

# ── 6. Durbin-Watson 통계량으로 자기상관 검정 ─────────────────────────────
dw_stat = durbin_watson(residuals)
print(f"\nDurbin-Watson 통계량: {dw_stat:.4f}")
print("  해석: 2에 가까우면 자기상관 없음, 0이면 양의 자기상관, 4면 음의 자기상관")
```

<!-- Execution error: ModuleNotFoundError: No module named 'statsmodels' -->

### OLS 정규방정식을 NumPy로 직접 구현

```python
# numpy만으로 OLS 해석적 해 계산
X_b = np.c_[np.ones((X_train_s.shape[0], 1)), X_train_s]  # 절편 열 추가

# 정규방정식: w_hat = (X^T X)^{-1} X^T y
w_hat = np.linalg.lstsq(X_b, y_train.values, rcond=None)[0]  # pinv 사용 (수치 안정)
print("절편 (b):", w_hat[0])
print("가중치 (w):", w_hat[1:])
```

<!-- Execution error: NameError: name 'X_train_s' is not defined -->

`np.linalg.lstsq`는 $X^+\mathbf{y}$를 SVD 분해로 계산하여, $X^TX$가 근사적 특이행렬일 때도 수치적으로 안정적인 해를 제공합니다.

---

## 정리

선형 회귀는 "단순하다"는 인상과 달리, OLS 추정 이론, 경사하강법 최적화, 통계적 가정 검증, 다중공선성 진단까지 머신러닝의 핵심 개념을 모두 포함하고 있습니다. 이 알고리즘을 제대로 이해하면 더 복잡한 모델로 나아가는 단단한 기반이 됩니다.

핵심 내용을 정리하면:

1. **예측**: $\hat{\mathbf{y}} = X\mathbf{w}$, 입력과 타깃의 선형 관계를 모델링합니다.
2. **학습**: OLS 해석적 해 $(X^TX)^{-1}X^T\mathbf{y}$ 또는 경사하강법으로 파라미터를 추정합니다.
3. **진단**: 5가지 Gauss-Markov 가정을 잔차 플롯, VIF, 통계 검정으로 확인합니다.
4. **해석**: 계수 $w_j$는 편미분 효과, 표준화 계수는 상대적 중요도를 나타냅니다.
5. **한계**: 비선형 관계, 다중공선성에 취약하며, 이를 해결하기 위해 [[regularized-regression]]과 [[polynomial-regression]]으로 확장합니다.

> **다음 글 안내**: 다중공선성과 과적합을 동시에 해결하는 Ridge, Lasso, ElasticNet은 [[regularized-regression]]에서, 비선형 관계를 선형 모델로 포착하는 방법은 [[polynomial-regression]]에서 다룹니다. 분류 문제로 확장하려면 [[logistic-regression]]을 참고하세요.

## 관련 문서

- [[regularized-regression|Ridge / Lasso / ElasticNet]]
- [[polynomial-regression|다항 회귀]]
- [[logistic-regression|로지스틱 회귀]]
- [[regression-metrics|회귀 평가 지표]]
- [[feature-engineering|특성 공학]]
- [[data-preprocessing|데이터 전처리]]
- [[optimization-theory|경사하강법 이론]]