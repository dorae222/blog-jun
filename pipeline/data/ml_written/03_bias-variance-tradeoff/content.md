# 편향-분산 트레이드오프: 모델 복잡도와 일반화

## 1. 개요

머신러닝에서 가장 근본적인 질문 중 하나는 **"왜 학습 데이터에서 잘 동작하는 모델이 새로운 데이터에서는 성능이 떨어지는가?"**입니다. 이 질문의 핵심에 **편향-분산 트레이드오프(Bias-Variance Tradeoff)**가 있습니다.

모든 ML 실무자가 이 개념을 이해해야 하는 이유는 명확합니다:

- **모델 선택(Model Selection)**: 어떤 알고리즘을 선택할지, 얼마나 복잡한 모델을 사용할지 결정하는 기준이 됩니다
- **하이퍼파라미터 튜닝**: 정규화 강도, 트리 깊이, 네트워크 크기 등 핵심 하이퍼파라미터 조정의 이론적 근거입니다
- **디버깅**: 모델이 기대한 성능을 내지 못할 때, 문제의 원인이 편향인지 분산인지 진단할 수 있습니다
- **데이터 전략**: 데이터를 더 수집해야 하는지, 피처 엔지니어링이 필요한지 판단하는 데 도움을 줍니다

편향-분산 트레이드오프를 제대로 이해하면, 시행착오를 줄이고 체계적으로 모델 성능을 개선할 수 있습니다.

---

## 2. 수학적 정의

### 2.1 기대 테스트 오차 분해

입력 $x$에 대한 실제 관계가 $y = f(x) + \epsilon$이라 하겠습니다. 여기서 $\epsilon$은 평균 0, 분산 $\sigma^2$인 노이즈입니다. 학습 데이터 $D$로 훈련한 모델 $\hat{f}_D(x)$의 **기대 테스트 오차(Expected Test Error)**는 다음과 같이 분해됩니다:

$$
E_D[(y - \hat{f}_D(x))^2] = \underbrace{(f(x) - E_D[\hat{f}_D(x)])^2}_{\text{Bias}^2} + \underbrace{E_D[(\hat{f}_D(x) - E_D[\hat{f}_D(x)])^2]}_{\text{Variance}} + \underbrace{\sigma^2}_{\text{Irreducible Error}}
$$

즉, **총 오차 = 편향² + 분산 + 기약 오차**입니다.

### 2.2 편향 (Bias)

$$
\text{Bias}[\hat{f}(x)] = f(x) - E_D[\hat{f}_D(x)]
$$

**편향(Bias)**은 모델이 데이터의 진짜 패턴을 얼마나 놓치는지를 나타냅니다. 여러 다른 학습 데이터셋으로 모델을 반복 학습했을 때, 예측값의 평균이 실제값에서 얼마나 벗어나 있는지를 측정합니다.

- **높은 편향**: 모델이 너무 단순하여 데이터의 복잡한 패턴을 포착하지 못함
- 예: 비선형 데이터에 선형 회귀를 적용하는 경우

### 2.3 분산 (Variance)

$$
\text{Var}[\hat{f}(x)] = E_D[(\hat{f}_D(x) - E_D[\hat{f}_D(x)])^2]
$$

**분산(Variance)**은 학습 데이터가 바뀔 때 모델 예측이 얼마나 달라지는지를 나타냅니다. 같은 모델 구조라도 학습 데이터에 따라 예측이 크게 흔들리면 분산이 높은 것입니다.

- **높은 분산**: 모델이 학습 데이터의 노이즈까지 학습하여, 데이터가 조금만 바뀌어도 예측이 크게 변함
- 예: 매우 깊은 결정 트리(Decision Tree)나 과도한 다항 회귀

### 2.4 기약 오차 (Irreducible Error)

$$
\sigma^2 = \text{Var}[\epsilon]
$$

**기약 오차(Irreducible Error)**는 데이터 자체에 내재된 노이즈로, 어떤 모델을 사용하더라도 줄일 수 없습니다. 측정 오차, 누락된 변수, 본질적인 무작위성 등이 원인입니다.

### 2.5 트레이드오프의 핵심

모델 복잡도를 높이면 편향은 줄어들지만 분산은 커지고, 복잡도를 낮추면 분산은 줄어들지만 편향이 커집니다. **총 오차를 최소화하는 최적의 복잡도**를 찾는 것이 편향-분산 트레이드오프의 핵심입니다.

---

## 3. 과적합(Overfitting)과 과소적합(Underfitting)

![편향-분산 분해 곡선: 모델 복잡도에 따른 편향, 분산, 총 오차의 변화](figures/bias_variance_decomposition.png)
*편향-분산 분해: 모델 복잡도가 증가하면 편향은 감소하지만 분산이 증가하여 총 오차에 U자형 곡선이 나타난다.*

### 3.1 모델 복잡도에 따른 오차 곡선

모델 복잡도(예: 다항식 차수, 트리 깊이, 뉴런 수)를 $x$축, 오차를 $y$축에 놓으면 특징적인 U자형 곡선이 나타납니다:

| 영역 | 학습 오차 | 테스트 오차 | 상태 |
|------|-----------|-------------|------|
| 낮은 복잡도 | 높음 | 높음 | **과소적합 (Underfitting)** |
| 적절한 복잡도 | 적당 | 최저 | **최적 (Sweet Spot)** |
| 높은 복잡도 | 매우 낮음 | 높음 | **과적합 (Overfitting)** |

- **과소적합 (Underfitting)**: 고편향 + 저분산. 모델이 너무 단순하여 학습 데이터조차 제대로 설명하지 못합니다.
- **과적합 (Overfitting)**: 저편향 + 고분산. 모델이 학습 데이터의 노이즈까지 암기하여 새로운 데이터에 대한 일반화 성능이 떨어집니다.

![과소적합 vs 과적합: 단순 모델과 복잡 모델의 피팅 비교](figures/underfit_vs_overfit.png)
*과소적합과 과적합 비교: 낮은 복잡도(좌)는 데이터 패턴을 포착하지 못하고, 높은 복잡도(우)는 노이즈까지 학습하여 일반화 성능이 떨어진다.*

### 3.2 실제 현상 예시

**주택 가격 예측**을 생각해 봅시다:

- **과소적합**: 면적 하나만으로 가격을 예측하는 단순 선형 모델. 위치, 층수, 연식 등 중요한 변수를 무시합니다.
- **과적합**: 학습 데이터의 모든 집에 대해 정확한 가격을 외우는 모델. 특정 집의 고유한 특성(이전 소유자, 계약 시점)까지 반영하여 새로운 집의 가격은 예측하지 못합니다.
- **적절한 모델**: 면적, 위치, 연식 등 핵심 변수를 활용하되, 적절한 정규화로 노이즈를 걸러내는 모델.

---

## 4. 학습 곡선 (Learning Curve)

### 4.1 학습 곡선이란?

**학습 곡선(Learning Curve)**은 학습 데이터의 크기를 점진적으로 늘려가며 학습 오차와 검증 오차를 관찰하는 진단 도구입니다. $x$축에 학습 데이터 수, $y$축에 오차를 배치합니다.

### 4.2 고편향 모델의 학습 곡선

- 학습 오차: 데이터가 늘어나면 약간 증가한 뒤 빠르게 수렴
- 검증 오차: 데이터가 늘어나도 크게 줄지 않고 높은 수준에서 수렴
- **두 곡선이 높은 오차에서 가까워짐** → 데이터를 더 모아도 개선이 미미
- **처방**: 더 복잡한 모델 사용, 피처 추가, 정규화 강도 감소

### 4.3 고분산 모델의 학습 곡선

- 학습 오차: 매우 낮은 수준 유지
- 검증 오차: 학습 오차보다 훨씬 높지만, 데이터가 늘수록 점차 감소
- **두 곡선 사이에 큰 간격(gap)** → 데이터를 더 모으면 개선 가능
- **처방**: 데이터 추가 수집, 피처 축소, 정규화 강도 증가, 앙상블(Ensemble) 기법 활용

### 4.4 진단 요약

| 지표 | 고편향 | 고분산 |
|------|--------|--------|
| 학습 오차 | 높음 | 매우 낮음 |
| 검증 오차 | 높음 (학습 오차와 유사) | 높음 (학습 오차와 큰 차이) |
| 데이터 추가 효과 | 거의 없음 | 효과적 |
| 해결 방향 | 모델 복잡도 증가 | 정규화 강화 또는 데이터 추가 |

---

## 5. 정규화 (Regularization) 개요

**정규화(Regularization)**는 모델의 복잡도를 명시적으로 제한하여 과적합을 방지하는 기법입니다. 손실 함수에 가중치의 크기에 대한 페널티 항을 추가합니다:

$$
\text{Loss} = \text{RSS} + \lambda \sum_{i=1}^{p} |w_i|^p
$$

여기서 $\lambda \geq 0$는 정규화 강도를 조절하는 하이퍼파라미터입니다.

### 5.1 L1 정규화 (Lasso)

$$
\text{Loss}_{\text{L1}} = \sum_{i=1}^{n}(y_i - \hat{y}_i)^2 + \lambda \sum_{j=1}^{p} |w_j|
$$

- 가중치의 **절댓값 합**에 페널티를 부과
- 일부 가중치를 정확히 0으로 만들어 **희소 해(Sparse Solution)**를 유도
- **피처 선택(Feature Selection)** 효과: 중요하지 않은 피처를 자동으로 제거
- 편향-분산 관점: 편향을 약간 높이는 대신 분산을 크게 줄임

### 5.2 L2 정규화 (Ridge)

$$
\text{Loss}_{\text{L2}} = \sum_{i=1}^{n}(y_i - \hat{y}_i)^2 + \lambda \sum_{j=1}^{p} w_j^2
$$

- 가중치의 **제곱합**에 페널티를 부과
- 가중치를 0에 가깝게 **축소(Shrinkage)**하지만 정확히 0으로 만들지는 않음
- 모든 피처를 유지하면서 각 피처의 영향력을 균등하게 줄임
- 다중공선성(Multicollinearity) 문제가 있을 때 특히 효과적

### 5.3 L1 vs L2 비교

| 특성 | L1 (Lasso) | L2 (Ridge) |
|------|------------|------------|
| 페널티 | $\lambda\sum\|w_j\|$ | $\lambda\sum w_j^2$ |
| 해의 특성 | 희소 (Sparse) | 밀집 (Dense) |
| 피처 선택 | 자동 수행 | 수행하지 않음 |
| 다중공선성 | 하나의 피처만 선택 | 상관된 피처에 가중치 분배 |
| 적합한 상황 | 중요 피처가 소수일 때 | 모든 피처가 기여할 때 |

### 5.4 정규화 강도 $\lambda$와 편향-분산

- $\lambda = 0$: 정규화 없음 → 저편향, 고분산 (과적합 위험)
- $\lambda \to \infty$: 극단적 정규화 → 고편향, 저분산 (과소적합 위험)
- **최적의 $\lambda$**: 교차 검증(Cross-Validation)으로 탐색

---

## 6. Python 시각화 코드

다음 코드는 편향-분산 트레이드오프를 다항 회귀(Polynomial Regression)를 통해 시각적으로 보여줍니다.

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_val_score

# 실제 함수 정의
np.random.seed(42)
def true_function(x):
    return np.sin(1.5 * np.pi * x)

# 데이터 생성
n_samples = 30
X = np.sort(np.random.rand(n_samples))
y = true_function(X) + np.random.randn(n_samples) * 0.3

# 1. 다양한 복잡도의 모델 피팅 시각화
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
degrees = [1, 4, 15]  # 과소적합, 적절, 과적합
titles = ['Underfitting\n(Degree=1, High Bias)',
          'Good Fit\n(Degree=4, Balanced)',
          'Overfitting\n(Degree=15, High Variance)']

X_test = np.linspace(0, 1, 100)

for ax, degree, title in zip(axes, degrees, titles):
    ax.scatter(X, y, color='steelblue', s=30, alpha=0.7, label='Train Data')
    ax.plot(X_test, true_function(X_test), 'g--', alpha=0.6, label='True Function')

    model = make_pipeline(PolynomialFeatures(degree), LinearRegression())
    model.fit(X.reshape(-1, 1), y)
    y_pred = model.predict(X_test.reshape(-1, 1))
    ax.plot(X_test, y_pred, 'r-', linewidth=2, label=f'Poly (d={degree})')

    ax.set_title(title, fontsize=12)
    ax.set_ylim(-2, 2)
    ax.legend(fontsize=8)
    ax.set_xlabel('x')
    ax.set_ylabel('y')

plt.tight_layout()
plt.savefig('bias_variance_fit.png', dpi=150, bbox_inches='tight')
plt.show()

# 2. 편향-분산 트레이드오프 곡선
max_degree = 15
degrees_range = range(1, max_degree + 1)
train_errors = []
test_errors = []

for d in degrees_range:
    model = make_pipeline(PolynomialFeatures(d), LinearRegression())
    model.fit(X.reshape(-1, 1), y)

    # 학습 오차
    y_train_pred = model.predict(X.reshape(-1, 1))
    train_mse = np.mean((y - y_train_pred) ** 2)
    train_errors.append(train_mse)

    # 교차 검증 오차 (테스트 오차 근사)
    cv_scores = cross_val_score(model, X.reshape(-1, 1), y,
                                 cv=5, scoring='neg_mean_squared_error')
    test_errors.append(-cv_scores.mean())

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(list(degrees_range), train_errors, 'b-o', markersize=5, label='Train Error')
ax.plot(list(degrees_range), test_errors, 'r-o', markersize=5, label='Test Error (CV)')
ax.axvline(x=4, color='green', linestyle='--', alpha=0.7, label='Optimal Complexity')
ax.fill_between([1, 4], 0, max(test_errors) * 1.1,
                alpha=0.1, color='blue', label='High Bias Zone')
ax.fill_between([4, max_degree], 0, max(test_errors) * 1.1,
                alpha=0.1, color='red', label='High Variance Zone')
ax.set_xlabel('Model Complexity (Polynomial Degree)', fontsize=12)
ax.set_ylabel('Mean Squared Error', fontsize=12)
ax.set_title('Bias-Variance Tradeoff', fontsize=14)
ax.legend(fontsize=10)
ax.set_ylim(0, max(test_errors) * 1.1)
plt.tight_layout()
plt.savefig('bias_variance_tradeoff.png', dpi=150, bbox_inches='tight')
plt.show()

# 3. 편향-분산 분해 시뮬레이션
n_experiments = 200
n_train = 25
x_eval = 0.5  # 평가 지점

degrees_sim = [1, 3, 5, 10, 15]
bias_sq_list = []
variance_list = []

for d in degrees_sim:
    predictions = []
    for _ in range(n_experiments):
        X_train = np.random.rand(n_train)
        y_train = true_function(X_train) + np.random.randn(n_train) * 0.3

        model = make_pipeline(PolynomialFeatures(d), LinearRegression())
        model.fit(X_train.reshape(-1, 1), y_train)
        pred = model.predict([[x_eval]])[0]
        predictions.append(pred)

    predictions = np.array(predictions)
    f_true = true_function(x_eval)
    bias_sq = (f_true - predictions.mean()) ** 2
    variance = predictions.var()
    bias_sq_list.append(bias_sq)
    variance_list.append(variance)

# 시각화
fig, ax = plt.subplots(figsize=(8, 5))
x_pos = np.arange(len(degrees_sim))
width = 0.35

bars1 = ax.bar(x_pos - width/2, bias_sq_list, width,
               label='Bias²', color='steelblue', alpha=0.8)
bars2 = ax.bar(x_pos + width/2, variance_list, width,
               label='Variance', color='coral', alpha=0.8)

total_error = [b + v for b, v in zip(bias_sq_list, variance_list)]
ax.plot(x_pos, total_error, 'k--o', linewidth=2,
        markersize=8, label='Bias² + Variance')

ax.set_xlabel('Polynomial Degree', fontsize=12)
ax.set_ylabel('Error', fontsize=12)
ax.set_title('Bias-Variance Decomposition (Simulation)', fontsize=14)
ax.set_xticks(x_pos)
ax.set_xticklabels([str(d) for d in degrees_sim])
ax.legend(fontsize=10)
plt.tight_layout()
plt.savefig('bias_variance_decomposition.png', dpi=150, bbox_inches='tight')
plt.show()
```

![Bias-Variance-Tradeoff Fig 1](/media/figures/outputs/bias-variance-tradeoff/bias-variance-tradeoff_fig_1.png)

![Bias-Variance-Tradeoff Fig 2](/media/figures/outputs/bias-variance-tradeoff/bias-variance-tradeoff_fig_2.png)

![Bias-Variance-Tradeoff Fig 3](/media/figures/outputs/bias-variance-tradeoff/bias-variance-tradeoff_fig_3.png)

위 코드는 세 가지 시각화를 생성합니다:

1. **모델 복잡도별 피팅 결과**: 과소적합(1차), 적절한 피팅(4차), 과적합(15차)을 직관적으로 비교
2. **편향-분산 트레이드오프 곡선**: 복잡도 증가에 따른 학습/테스트 오차의 변화와 최적 지점
3. **편향-분산 분해 시뮬레이션**: 200회 반복 실험을 통해 실제 편향²과 분산을 측정하고 총 오차와의 관계를 시각화

---

## 정리

편향-분산 트레이드오프는 머신러닝의 가장 근본적인 원리입니다:

- **편향(Bias)**: 모델의 가정이 틀려서 발생하는 체계적 오차
- **분산(Variance)**: 학습 데이터 변화에 대한 모델의 불안정성
- **최적의 모델**: 편향과 분산의 합이 최소가 되는 복잡도를 가진 모델

실무에서는 **학습 곡선 분석**으로 현재 모델이 고편향/고분산 중 어디에 해당하는지 진단하고, **교차 검증(Cross-Validation)**으로 최적의 정규화 강도를 찾으며, **앙상블(Ensemble)** 기법으로 분산을 줄이는 전략을 조합하여 일반화 성능을 극대화합니다.