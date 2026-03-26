# 로지스틱 회귀: 분류를 위한 확률 모델

## 1. 개요: 왜 선형 회귀를 분류에 쓸 수 없는가

분류 문제에서 가장 먼저 떠오르는 아이디어는 "선형 회귀를 그대로 쓰면 안 될까?"이다. 예를 들어 스팸 메일(1)과 정상 메일(0)을 구분한다고 하자. 선형 회귀를 적용하면 $\hat{y} = \mathbf{w}^T\mathbf{x} + b$를 계산하고, $\hat{y} \geq 0.5$이면 1, 아니면 0으로 판정하는 방식을 생각할 수 있다.

하지만 이 접근에는 치명적인 문제가 있다. 첫째, 선형 회귀의 출력은 $(-\infty, +\infty)$ 범위를 가지므로 확률로 해석할 수 없다. 둘째, 이상치(outlier)가 하나만 추가되어도 결정 경계가 크게 흔들린다. 셋째, 회귀 손실(MSE)은 분류 문제의 본질에 맞지 않는다.

**로지스틱 회귀(Logistic Regression)**는 이 문제를 해결하기 위해 선형 함수의 출력을 시그모이드 함수에 통과시켜 $[0, 1]$ 범위의 확률값으로 변환한다. 이름에 '회귀'가 붙어 있지만 실제로는 분류 알고리즘이다.

---

![시그모이드 함수: 선형 출력을 확률로 변환하는 S자 곡선](figures/sigmoid_function.png)
*시그모이드 함수: 입력값 z를 (0, 1) 범위의 확률로 변환하며, z=0에서 0.5를 출력하고 양 극단에서 0과 1에 수렴한다.*

## 2. 시그모이드 함수 (Sigmoid)

시그모이드 함수는 어떤 실수 입력도 $(0, 1)$ 구간으로 압축시키는 함수이다:

$$\sigma(z) = \frac{1}{1 + e^{-z}}$$

여기서 $z = \mathbf{w}^T\mathbf{x} + b$는 선형 결합이다. 로지스틱 회귀의 예측은 다음과 같이 정의된다:

$$\hat{y} = P(y=1 \mid \mathbf{x}) = \sigma(\mathbf{w}^T\mathbf{x} + b)$$

시그모이드의 주요 성질은 다음과 같다:
- $z \to +\infty$이면 $\sigma(z) \to 1$
- $z \to -\infty$이면 $\sigma(z) \to 0$
- $z = 0$이면 $\sigma(0) = 0.5$
- 도함수: $\sigma'(z) = \sigma(z)(1 - \sigma(z))$

$z$가 크면 클수록 클래스 1일 확률이 높아지고, 작으면 작을수록 클래스 0일 확률이 높아진다. 이 구조 덕분에 로지스틱 회귀는 확률적 분류기로 해석할 수 있다.

---

## 3. 오즈비(Odds)와 로짓(Logit)

로지스틱 회귀를 더 깊이 이해하려면 오즈비와 로짓 개념이 필요하다.

**오즈비(Odds Ratio)**는 어떤 사건이 일어날 확률과 일어나지 않을 확률의 비이다:

$$\text{odds} = \frac{P(y=1)}{P(y=0)} = \frac{P(y=1)}{1 - P(y=1)}$$

확률이 0.8이면 오즈는 $0.8/0.2 = 4$이다. "성공할 가능성이 실패할 가능성의 4배"라는 의미이다.

**로짓(Logit)**은 오즈의 로그값이다:

$$\text{logit}(p) = \log\left(\frac{p}{1-p}\right)$$

이제 시그모이드 함수를 역방향으로 생각해보자. $\hat{y} = \sigma(z)$라 하면:

$$\log\left(\frac{\hat{y}}{1 - \hat{y}}\right) = z = \mathbf{w}^T\mathbf{x} + b$$

즉, **로지스틱 회귀는 로그 오즈비(log-odds)를 선형 함수로 모델링**한다. 이것이 로지스틱 회귀의 핵심 해석이다. 오즈비 공간에서 본다면 로지스틱 회귀도 결국 선형 모델이다.

---

## 4. 손실 함수: Binary Cross-Entropy

### 최대우도추정(MLE)으로부터의 유도

로지스틱 회귀의 손실 함수는 임의로 정한 것이 아니라, 최대우도추정(Maximum Likelihood Estimation, MLE)으로부터 자연스럽게 유도된다.

$n$개의 학습 데이터 $\{(\mathbf{x}_i, y_i)\}_{i=1}^n$가 있을 때, 각 샘플의 우도(likelihood)는:

$$P(y_i \mid \mathbf{x}_i) = \hat{y}_i^{y_i}(1 - \hat{y}_i)^{1 - y_i}$$

전체 데이터에 대한 로그 우도(log-likelihood)를 최대화하면:

$$\log \mathcal{L} = \sum_{i=1}^n \left[ y_i \log \hat{y}_i + (1 - y_i) \log(1 - \hat{y}_i) \right]$$

이를 최소화 문제로 전환(부호 반전 후 평균)하면 **Binary Cross-Entropy 손실함수**가 된다:

$$\mathcal{L} = -\frac{1}{n} \sum_{i=1}^n \left[ y_i \log \hat{y}_i + (1 - y_i) \log(1 - \hat{y}_i) \right]$$

MSE와 달리 Binary Cross-Entropy는 시그모이드 함수와 결합했을 때 볼록 함수(convex function)가 되어 전역 최솟값을 보장하고, 경사하강법이 안정적으로 수렴한다.

---

![결정 경계 시각화: 로지스틱 회귀의 선형 결정 경계와 클래스 분리](figures/decision_boundary.png)
*결정 경계: 로지스틱 회귀가 두 클래스를 분리하는 선형 결정 경계를 형성하며, 경계에서 멀수록 예측 확률이 높아진다.*

## 5. 결정 경계 (Decision Boundary)

학습된 모델에서 클래스를 결정하는 기준은 일반적으로 확률 0.5이다:

$$P(y=1 \mid \mathbf{x}) = 0.5 \iff \sigma(\mathbf{w}^T\mathbf{x} + b) = 0.5 \iff \mathbf{w}^T\mathbf{x} + b = 0$$

즉, **결정 경계는 $\mathbf{w}^T\mathbf{x} + b = 0$이 되는 초평면(hyperplane)**이다. 2차원에서는 직선, 3차원에서는 평면이 된다.

**선형 결정 경계의 한계**: 로지스틱 회귀는 본질적으로 선형 분류기이므로 XOR 문제처럼 선형으로 분리되지 않는 데이터에는 적합하지 않다. 이 한계를 극복하려면 다항식 특성(polynomial features)을 추가하거나, SVM의 커널 기법, 신경망 등을 사용해야 한다.

결정 임계값(threshold)은 0.5로 고정된 것이 아니다. 클래스 불균형이나 비용 민감도에 따라 조정할 수 있으며, 이는 ROC 곡선과 AUC로 평가된다.

---

## 6. 다중 분류 (Multiclass Classification)

로지스틱 회귀는 이진 분류가 기본이지만, 다중 클래스 문제로 확장할 수 있다.

### One-vs-Rest (OvR)

$K$개의 클래스가 있을 때, 각 클래스에 대해 "해당 클래스 vs 나머지 전체"를 판별하는 이진 분류기를 $K$개 학습한다. 예측 시에는 $K$개 분류기의 출력 중 가장 높은 값을 선택한다. 구현이 단순하지만, 각 분류기가 불균형한 데이터를 학습하게 된다.

### Softmax Regression (Multinomial Logistic Regression)

$K$개의 클래스를 동시에 모델링하는 방법이다. 각 클래스에 대한 가중치 벡터 $\mathbf{w}_k$를 학습하고, Softmax 함수로 확률을 정규화한다:

$$P(y=k \mid \mathbf{x}) = \frac{e^{\mathbf{w}_k^T\mathbf{x} + b_k}}{\sum_{j=1}^K e^{\mathbf{w}_j^T\mathbf{x} + b_j}}$$

출력의 합이 항상 1이 되며, 손실 함수로 Categorical Cross-Entropy를 사용한다:

$$\mathcal{L} = -\frac{1}{n} \sum_{i=1}^n \sum_{k=1}^K \mathbf{1}[y_i = k] \log P(y=k \mid \mathbf{x}_i)$$

Softmax Regression은 신경망의 마지막 레이어에서 널리 사용되는 구조이기도 하다.

---

## 7. 계수(Coefficient) 해석

로지스틱 회귀의 가장 큰 장점 중 하나는 계수를 해석할 수 있다는 점이다.

특성 $x_j$의 계수가 $w_j$일 때, $x_j$가 1 단위 증가하면 **로그 오즈비가 $w_j$만큼 변한다**:

$$\Delta\log\left(\frac{P(y=1)}{P(y=0)}\right) = w_j$$

오즈비로 변환하면 $e^{w_j}$만큼 곱해진다. 예를 들어 $w_j = 0.5$이면 $x_j$가 1 증가할 때 오즈비가 $e^{0.5} \approx 1.65$배가 된다. $w_j < 0$이면 해당 특성이 클래스 1의 확률을 감소시키는 방향으로 작용한다.

이러한 해석 가능성 때문에 로지스틱 회귀는 의료, 금융, 사회과학 분야에서 통계 분석 도구로 광범위하게 사용된다.

---

## 8. 정규화 (Regularization)

로지스틱 회귀도 과적합 위험이 있으며, 정규화 항을 추가해 이를 제어한다.

### L2 정규화 (Ridge)

$$\mathcal{L}_{\text{ridge}} = -\frac{1}{n} \sum_{i=1}^n \left[ y_i \log \hat{y}_i + (1-y_i) \log(1-\hat{y}_i) \right] + \lambda \|\mathbf{w}\|_2^2$$

모든 계수를 0 방향으로 축소하지만 완전히 0으로 만들지는 않는다. sklearn에서 `C = 1/λ` 파라미터로 제어하며 기본값은 L2이다.

### L1 정규화 (Lasso) — Feature Selection 효과

$$\mathcal{L}_{\text{lasso}} = -\frac{1}{n} \sum_{i=1}^n \left[ y_i \log \hat{y}_i + (1-y_i) \log(1-\hat{y}_i) \right] + \lambda \|\mathbf{w}\|_1$$

L1은 일부 계수를 정확히 0으로 만드는 **희소성(sparsity)** 효과가 있다. 이 덕분에 자동으로 불필요한 특성을 제거하는 Feature Selection 기능을 수행한다. 고차원 데이터에서 관련 특성만 남기고 나머지를 제거하여 모델을 단순화할 때 유용하다.

실무에서는 특성 수가 많을 때 L1(또는 Elastic Net)을 먼저 적용해 중요한 특성을 선별하고, 이후 다른 모델로 연결하는 파이프라인을 구성하는 경우가 많다.

---

## 9. Python 구현 예시

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.preprocessing import StandardScaler

# 1. 데이터 생성
X, y = make_classification(
    n_samples=500, n_features=2, n_informative=2,
    n_redundant=0, random_state=42
)

# 2. 전처리 및 분할
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

# 3. 모델 학습 (L2 정규화 기본값, C=1)
model = LogisticRegression(penalty='l2', C=1.0, max_iter=1000, random_state=42)
model.fit(X_train, y_train)

# 4. 평가
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]
print(classification_report(y_test, y_pred))
print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")

# 5. 계수 해석
print("\n계수 (log-odds 기준):")
for i, coef in enumerate(model.coef_[0]):
    print(f"  x{i}: {coef:.4f}  (오즈비 = {np.exp(coef):.4f})")

# 6. 결정 경계 시각화
fig, ax = plt.subplots(figsize=(8, 6))

# 배경 색상 (확률 값으로 채우기)
x_min, x_max = X_scaled[:, 0].min() - 0.5, X_scaled[:, 0].max() + 0.5
y_min, y_max = X_scaled[:, 1].min() - 0.5, X_scaled[:, 1].max() + 0.5
xx, yy = np.meshgrid(
    np.linspace(x_min, x_max, 300),
    np.linspace(y_min, y_max, 300)
)
Z = model.predict_proba(np.c_[xx.ravel(), yy.ravel()])[:, 1]
Z = Z.reshape(xx.shape)

contour = ax.contourf(xx, yy, Z, levels=20, cmap='RdBu', alpha=0.6)
plt.colorbar(contour, ax=ax, label='P(y=1|x)')

# 결정 경계 (P=0.5 선)
ax.contour(xx, yy, Z, levels=[0.5], colors='black', linewidths=2)

# 데이터 산점도
scatter = ax.scatter(
    X_scaled[:, 0], X_scaled[:, 1],
    c=y, cmap='RdBu', edgecolors='k', s=40, alpha=0.8
)

ax.set_xlabel('Feature 1')
ax.set_ylabel('Feature 2')
ax.set_title('로지스틱 회귀 결정 경계 (검은 선: P=0.5)')
plt.tight_layout()
plt.show()

# 7. L1 정규화로 Feature Selection 확인 (고차원 예시)
X_high, y_high = make_classification(
    n_samples=300, n_features=20, n_informative=5,
    n_redundant=5, random_state=42
)
X_high_scaled = StandardScaler().fit_transform(X_high)

model_l1 = LogisticRegression(penalty='l1', C=0.1, solver='liblinear', random_state=42)
model_l1.fit(X_high_scaled, y_high)

n_zero = np.sum(model_l1.coef_[0] == 0)
print(f"\nL1 정규화 결과: 20개 특성 중 {n_zero}개 계수가 0으로 제거됨")
```

```output
precision    recall  f1-score   support

           0       0.91      0.84      0.88        50
           1       0.85      0.92      0.88        50

    accuracy                           0.88       100
   macro avg       0.88      0.88      0.88       100
weighted avg       0.88      0.88      0.88       100

ROC-AUC: 0.9476

계수 (log-odds 기준):
  x0: 3.2515  (오즈비 = 25.8283)
  x1: 0.4387  (오즈비 = 1.5506)

L1 정규화 결과: 20개 특성 중 15개 계수가 0으로 제거됨
```

![Logistic-Regression Fig 1](/media/figures/outputs/logistic-regression/logistic-regression_fig_1.png)

---

## 요약

| 항목 | 내용 |
|------|------|
| 핵심 함수 | 시그모이드 $\sigma(z) = 1/(1+e^{-z})$ |
| 출력 | $P(y=1\mid\mathbf{x}) \in (0, 1)$ |
| 손실 함수 | Binary Cross-Entropy (MLE 유도) |
| 결정 경계 | $\mathbf{w}^T\mathbf{x} + b = 0$ (선형) |
| 다중 분류 | OvR 또는 Softmax Regression |
| 계수 해석 | 로그 오즈비 변화량 |
| 정규화 | L2(Ridge), L1(Lasso, Feature Selection) |
| 장점 | 빠른 학습, 해석 가능, 확률 출력 |
| 단점 | 선형 결정 경계, 비선형 패턴에 취약 |

로지스틱 회귀는 분류 문제의 **베이스라인**으로 항상 먼저 시도해볼 만한 모델이다. 해석 가능성과 계산 효율성이 뛰어나고, 정규화와 결합하면 고차원 데이터에서도 안정적으로 작동한다. 복잡한 모델을 도입하기 전에 로지스틱 회귀가 충분히 잘 작동하는지 확인하는 것이 실무에서 중요한 습관이다.