## 개요

Gradient Boosting은 **약한 학습기(weak learner)** 여러 개를 순차적으로 결합해 강한 예측 모델을 만드는 앙상블 기법입니다. 핵심 아이디어는 간단합니다. 현재 모델이 예측을 잘못한 부분, 즉 **잔차(residual)**를 다음 모델이 집중적으로 학습하도록 합니다. 이 과정을 반복하면 전체 모델의 오류가 점차 줄어들게 됩니다.

Random Forest가 독립적인 트리들을 병렬로 학습한 뒤 평균을 내는 방식이라면, Gradient Boosting은 트리를 **하나씩 순서대로** 추가하면서 이전 트리들의 실수를 보정합니다. 이 순차적(sequential) 구조 덕분에 높은 예측 정확도를 달성하지만, 병렬화가 어렵고 하이퍼파라미터 튜닝에 주의가 필요합니다.

---

## 수학적 배경

### 함수 공간에서의 경사 하강법

Gradient Boosting은 **함수 공간(function space)**에서의 경사 하강법으로 이해할 수 있습니다. 우리가 최소화하려는 손실 함수를 $L(y, F(x))$라 할 때, $m$번째 단계에서 모델을 다음과 같이 업데이트합니다.

$$F_m(x) = F_{m-1}(x) + \eta \cdot h_m(x)$$

여기서:
- $F_m(x)$: $m$번째 단계의 누적 모델
- $\eta$: 학습률(shrinkage), $0 < \eta \leq 1$
- $h_m(x)$: $m$번째 약한 학습기(주로 결정 트리)

### 유사 잔차 (Pseudo-residuals)

각 단계에서 새로운 트리 $h_m(x)$는 손실 함수의 **음의 기울기(negative gradient)**를 학습 목표로 삼습니다. 이를 **유사 잔차(pseudo-residual)**라 부릅니다.

$$r_{im} = -\left[\frac{\partial L(y_i, F(x_i))}{\partial F(x_i)}\right]_{F = F_{m-1}}$$

손실 함수가 **MSE(Mean Squared Error)**인 회귀 문제의 경우:

$$L(y, F) = \frac{1}{2}(y - F)^2 \implies r_{im} = y_i - F_{m-1}(x_i)$$

즉, MSE에서 유사 잔차는 실제 잔차와 동일합니다. 이것이 "잔차를 학습한다"는 직관과 연결됩니다.

**로그 손실(Log Loss)**을 사용하는 분류 문제에서는:

$$L(y, F) = -\left[y \log p + (1-y) \log(1-p)\right], \quad p = \sigma(F(x))$$

$$r_{im} = y_i - p_{m-1}(x_i)$$

이처럼 손실 함수를 바꾸는 것만으로도 다양한 문제에 적용할 수 있습니다.

---

![순차적 잔차 학습: 그래디언트 부스팅의 단계별 잔차 보정 과정](figures/sequential_residual_fitting.png)
*순차적 잔차 학습: 이전 모델의 잔차를 다음 모델이 학습하면서 전체 앙상블의 예측이 점차 정교해지는 과정을 보여준다.*

## 알고리즘 단계별 설명

### GBM 알고리즘 (Friedman, 2001)

```
1. 초기 모델 F_0(x)를 상수로 초기화
   F_0(x) = argmin_γ Σ L(y_i, γ)

2. For m = 1, 2, ..., M:
   a. 유사 잔차 계산:
      r_im = -∂L(y_i, F(x_i)) / ∂F(x_i)  (F = F_{m-1} 에서 평가)

   b. 약한 학습기 h_m(x)를 유사 잔차에 피팅:
      h_m = DecisionTree.fit(X, r)

   c. 최적 스텝 크기 γ_m 계산:
      γ_m = argmin_γ Σ L(y_i, F_{m-1}(x_i) + γ · h_m(x_i))

   d. 모델 업데이트:
      F_m(x) = F_{m-1}(x) + η · γ_m · h_m(x)

3. 최종 모델: F_M(x) 반환
```

### 주요 하이퍼파라미터

**Shrinkage (학습률, `learning_rate`)**

학습률 $\eta$는 각 트리의 기여도를 줄여 과적합을 방지합니다. 작은 $\eta$ ($\leq 0.1$)는 일반화 성능이 좋지만 더 많은 트리(`n_estimators`)가 필요합니다. 학습률과 트리 수는 **역의 관계**입니다.

**Subsampling**

각 트리를 학습할 때 전체 데이터의 일부(예: 80%)만 무작위로 사용합니다. Stochastic GBM이라 부르며, 분산을 줄이고 학습 속도를 높이는 효과가 있습니다.

**트리 깊이 (`max_depth`)**

GBM에서 개별 트리는 보통 얕은 트리(depth 3~5)를 사용합니다. 깊은 트리는 분산이 크고 과적합 위험이 있으며, 얕은 트리는 바이어스가 크지만 앙상블을 통해 보완됩니다.

| 하이퍼파라미터 | 권장 범위 | 효과 |
|---|---|---|
| `n_estimators` | 100~500 | 트리 수, 클수록 정확하지만 과적합 위험 |
| `learning_rate` | 0.01~0.1 | 작을수록 안정적, n_estimators와 함께 조정 |
| `max_depth` | 3~5 | 개별 트리 깊이 |
| `subsample` | 0.6~0.9 | 행 샘플링 비율 |
| `min_samples_leaf` | 5~20 | 리프 노드 최소 샘플 수 |

---

## Python 구현

### 분류 예제 (GradientBoostingClassifier)

```python
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

# 데이터 생성
X, y = make_classification(
    n_samples=2000,
    n_features=20,
    n_informative=15,
    n_redundant=5,
    random_state=42
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 모델 학습
gbc = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=4,
    subsample=0.8,
    min_samples_leaf=10,
    random_state=42
)
gbc.fit(X_train, y_train)

# 평가
y_pred = gbc.predict(X_test)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(classification_report(y_test, y_pred))
```

```output
Accuracy: 0.9325
              precision    recall  f1-score   support

           0       0.92      0.95      0.94       207
           1       0.94      0.92      0.93       193

    accuracy                           0.93       400
   macro avg       0.93      0.93      0.93       400
weighted avg       0.93      0.93      0.93       400
```

### 회귀 예제 + 학습 곡선

```python
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.datasets import make_regression
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

# 데이터 생성
X, y = make_regression(n_samples=1000, n_features=10, noise=20, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 모델 학습
gbr = GradientBoostingRegressor(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=4,
    subsample=0.8,
    random_state=42
)
gbr.fit(X_train, y_train)

# staged_predict로 학습 과정 추적
train_errors = []
test_errors = []
for y_train_pred in gbr.staged_predict(X_train):
    train_errors.append(mean_squared_error(y_train, y_train_pred))
for y_test_pred in gbr.staged_predict(X_test):
    test_errors.append(mean_squared_error(y_test, y_test_pred))

# 학습 곡선 시각화
plt.figure(figsize=(10, 5))
plt.plot(train_errors, label='Train MSE', linewidth=2)
plt.plot(test_errors, label='Test MSE', linewidth=2, linestyle='--')
plt.xlabel('Number of Trees')
plt.ylabel('MSE')
plt.title('Gradient Boosting - 학습 곡선 (MSE)')
plt.legend()
plt.tight_layout()
plt.show()

print(f"최종 Test MSE: {test_errors[-1]:.2f}")
print(f"최적 트리 수: {np.argmin(test_errors) + 1}")
```

```output
최종 Test MSE: 1270.98
최적 트리 수: 300
```

![Gradient-Boosting Fig 1](/media/figures/outputs/gradient-boosting/gradient-boosting_fig_1.png)

---

![학습률 효과: 학습률에 따른 모델 수렴 속도와 과적합 양상 비교](figures/learning_rate_effect.png)
*학습률 효과: 학습률이 낮을수록 수렴이 느리지만 일반화 성능이 좋고, 높을수록 빠르게 수렴하지만 과적합 위험이 증가한다.*

## 시각화

### Feature Importance

```python
import matplotlib.pyplot as plt
import numpy as np

# Feature Importance 추출 및 정렬
feature_names = [f'Feature {i}' for i in range(X_train.shape[1])]
importances = gbr.feature_importances_
indices = np.argsort(importances)[::-1]

plt.figure(figsize=(10, 6))
plt.bar(
    range(len(importances)),
    importances[indices],
    color='steelblue',
    edgecolor='white'
)
plt.xticks(
    range(len(importances)),
    [feature_names[i] for i in indices],
    rotation=45,
    ha='right'
)
plt.title('Gradient Boosting - Feature Importance')
plt.ylabel('Importance')
plt.tight_layout()
plt.show()
```

![Gradient-Boosting Fig 2](/media/figures/outputs/gradient-boosting/gradient-boosting_fig_2.png)

### 잔차 감소 과정 시각화

```python
# 단계별 예측값과 실제 잔차 시각화
stages = [10, 50, 100, 200, 300]
fig, axes = plt.subplots(1, len(stages), figsize=(18, 4), sharey=True)

for ax, stage in zip(axes, stages):
    # staged_predict는 제너레이터이므로 직접 인덱싱 불가 -> itertools 활용
    preds = list(gbr.staged_predict(X_test))
    residuals = y_test - preds[stage - 1]
    ax.hist(residuals, bins=30, color='coral', edgecolor='white')
    ax.set_title(f'Step {stage}\nMSE={mean_squared_error(y_test, preds[stage-1]):.1f}')
    ax.set_xlabel('Residual')

axes[0].set_ylabel('Count')
fig.suptitle('학습 단계별 잔차 분포', fontsize=14)
plt.tight_layout()
plt.show()
```

![Gradient-Boosting Fig 3](/media/figures/outputs/gradient-boosting/gradient-boosting_fig_3.png)

---

## 실전 팁

### GBM vs XGBoost vs LightGBM 비교

| 항목 | Sklearn GBM | XGBoost | LightGBM |
|---|---|---|---|
| 속도 | 느림 | 빠름 | 매우 빠름 |
| 메모리 | 보통 | 보통 | 효율적 |
| 결측치 처리 | 사전 처리 필요 | 자동 처리 | 자동 처리 |
| 범주형 변수 | 인코딩 필요 | 인코딩 필요 | 네이티브 지원 |
| 트리 성장 방식 | Level-wise | Level-wise | Leaf-wise |
| 주요 장점 | 구현 이해 용이 | 정규화·조기 종료 | 초대용량 데이터 |

SKLearn GBM은 학습 속도가 느려 대용량 데이터에는 부적합하지만, 알고리즘의 원리를 이해하고 실험하기에 이상적입니다. 실무에서는 XGBoost나 LightGBM을 사용하는 것이 일반적입니다.

### 과적합 방지법

1. **학습률 축소 + 트리 수 증가**: `learning_rate=0.01`과 `n_estimators=1000`을 함께 사용
2. **Early Stopping**: `validation_fraction`과 `n_iter_no_change`로 검증 손실이 개선되지 않으면 조기 종료
3. **서브샘플링**: `subsample < 1.0`으로 행 샘플링 (Stochastic GBM)
4. **트리 복잡도 제한**: `max_depth`, `min_samples_leaf`, `max_features` 조정

```python
# Early Stopping 적용 예시
gbr_es = GradientBoostingRegressor(
    n_estimators=1000,
    learning_rate=0.01,
    max_depth=4,
    subsample=0.8,
    validation_fraction=0.1,   # 검증 데이터 비율
    n_iter_no_change=20,       # 20 라운드 동안 개선 없으면 중단
    tol=1e-4,
    random_state=42
)
gbr_es.fit(X_train, y_train)
print(f"사용된 트리 수: {gbr_es.n_estimators_}")
```

```output
사용된 트리 수: 1000
```

### 하이퍼파라미터 튜닝 전략

처음에는 `learning_rate=0.1`과 적당한 `n_estimators`(100~200)로 빠르게 실험하고, 좋은 구조를 찾은 뒤 `learning_rate`를 줄이고 `n_estimators`를 늘려 성능을 끌어올리는 2단계 전략이 효과적입니다. GridSearchCV보다는 Optuna, Hyperopt 같은 베이즈 최적화 라이브러리를 사용하면 효율적으로 탐색할 수 있습니다.

---

## 정리

Gradient Boosting은 함수 공간에서의 경사 하강법이라는 우아한 수학적 토대 위에 세워진 강력한 앙상블 방법입니다. 순차적으로 잔차를 보정하는 단순한 아이디어가 다양한 손실 함수와 결합되어 회귀, 분류, 랭킹 등 폭넓은 문제에 적용됩니다. XGBoost와 LightGBM은 이 GBM 알고리즘의 계산 효율성을 극적으로 개선한 구현체로, 현재도 정형 데이터 경진 대회에서 최고 성능을 자랑합니다. GBM의 원리를 제대로 이해하면 이 두 라이브러리의 파라미터 의미와 튜닝 방향도 훨씬 명확하게 파악할 수 있습니다.