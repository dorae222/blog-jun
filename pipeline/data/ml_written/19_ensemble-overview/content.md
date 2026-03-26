## 왜 여러 모델을 결합하는가

단일 모델은 항상 한계가 있다. 결정 나무는 불안정하고 과적합하기 쉬우며, 선형 모델은 비선형 패턴을 놓친다. **앙상블(Ensemble)**은 이 한계를 서로 다른 특성을 가진 여러 모델을 결합해 극복한다.

핵심 직관은 "오류의 다양성"이다. 10명의 전문가가 각기 다른 이유로 틀린다면, 다수결을 취했을 때 정답에 가까워진다. 반대로 모두 같은 이유로 틀린다면 아무리 많은 전문가를 모아도 소용없다. **다양성(Diversity)**이 앙상블의 핵심이다.

## 편향-분산 관점으로 이해하기

모든 앙상블 전략은 편향-분산 분해(Bias-Variance Decomposition)의 관점에서 이해할 수 있다.

$$\text{총 오류} = \text{Bias}^2 + \text{Variance} + \text{환원 불가 노이즈}$$

- **편향(Bias)**: 모델이 진짜 패턴에서 얼마나 체계적으로 벗어나는가 (과소적합의 원인)
- **분산(Variance)**: 훈련 데이터가 달라질 때 예측이 얼마나 흔들리는가 (과적합의 원인)

$M$개의 독립적인 학습기 각각의 분산이 $\sigma^2$이고, 학습기 간 예측 상관계수가 $\rho$라면 앙상블의 분산은:

$$\text{Var}\!\left(\frac{1}{M}\sum_{i=1}^{M} h_i\right) = \rho \sigma^2 + \frac{1-\rho}{M}\sigma^2$$

$M \to \infty$이면 두 번째 항은 0에 수렴하고, $\rho = 0$이면 분산이 $\sigma^2 / M$으로 줄어든다. **배깅은 분산을 줄이고, 부스팅은 편향을 줄인다.** 이것이 두 전략의 근본적인 차이다.

![배깅 vs 부스팅 비교: 병렬 학습과 순차 학습의 구조적 차이](figures/bagging_vs_boosting.png)
*배깅 vs 부스팅: 배깅은 독립적인 모델을 병렬로 학습하여 분산을 줄이고, 부스팅은 이전 모델의 오류를 순차적으로 보정하여 편향을 줄인다.*

## 배깅: 분산을 줄이는 앙상블

**배깅(Bootstrap Aggregating)**은 원본 데이터에서 복원 추출(Bootstrap Sampling)로 여러 부분집합을 만들고, 각 부분집합에서 독립적으로 모델을 학습한 뒤 결과를 종합한다.

**학습 과정**:
1. 원본 데이터 $D$에서 복원 추출로 $B$개의 부트스트랩 샘플 $D_1, \ldots, D_B$ 생성 (각 샘플은 원본과 같은 크기)
2. 각 샘플에서 독립적으로 기본 학습기 $h_b$ 훈련
3. 예측값 결합: 분류는 다수결, 회귀는 평균

$$\hat{y} = \frac{1}{B} \sum_{b=1}^{B} h_b(\mathbf{x}) \quad \text{(회귀)}$$

배깅은 복잡한 모델(깊은 결정 나무)처럼 **분산이 높은 학습기**에 특히 효과적이다. 복원 추출로 각 부트스트랩 샘플이 달라지고, 이로 인해 학습기들이 서로 다른 예측을 하게 되어 평균화 시 분산이 줄어든다.

**OOB(Out-of-Bag) 평가**: 부트스트랩 샘플에 포함되지 않은 약 37%의 샘플로 별도 검증 없이도 모델 성능을 추정할 수 있다.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import BaggingClassifier, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score

X, y = make_classification(
    n_samples=1000, n_features=20, n_informative=15,
    n_redundant=5, random_state=42
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 단일 결정 나무 (고분산, 과적합)
single_tree = DecisionTreeClassifier(random_state=42)
single_tree.fit(X_train, y_train)
print(f"단일 나무 - Train: {single_tree.score(X_train, y_train):.4f} | Test: {single_tree.score(X_test, y_test):.4f}")

# 배깅으로 분산 감소
bagging = BaggingClassifier(
    estimator=DecisionTreeClassifier(random_state=42),
    n_estimators=200,
    max_samples=0.8,
    bootstrap=True,
    oob_score=True,   # OOB 점수 계산
    n_jobs=-1,
    random_state=42
)
bagging.fit(X_train, y_train)
print(f"배깅 - Test: {bagging.score(X_test, y_test):.4f} | OOB: {bagging.oob_score_:.4f}")
```

```output
단일 나무 - Train: 1.0000 | Test: 0.7900
배깅 - Test: 0.8750 | OOB: 0.8875
```

## 부스팅: 편향을 줄이는 앙상블

**부스팅(Boosting)**은 학습기를 순차적으로 쌓으며, 이전 학습기가 틀린 샘플에 더 집중하도록 유도한다. 편향이 높은 단순한 모델(얕은 결정 나무, Decision Stump)을 반복 결합해 점점 정교한 예측기를 만든다.

**그래디언트 부스팅의 핵심**: $t$번째 모델은 이전 앙상블 $F_{t-1}$의 잔차(의사 잔차, Pseudo-Residual)를 학습한다.

$$F_t(\mathbf{x}) = F_{t-1}(\mathbf{x}) + \eta \cdot h_t(\mathbf{x})$$

여기서 $h_t$는 손실 함수의 음의 그래디언트를 타깃으로 학습한다.

$$h_t = \arg\min_h \sum_{i=1}^{N} \left[-\frac{\partial L(y_i, F_{t-1}(\mathbf{x}_i))}{\partial F_{t-1}(\mathbf{x}_i)} - h(\mathbf{x}_i)\right]^2$$

**AdaBoost**의 경우, 오분류된 샘플의 가중치를 높여 다음 학습기가 그 샘플에 집중하게 한다. 각 학습기의 기여도 $\alpha_t$는 오류율 $\epsilon_t$에 반비례한다.

$$\alpha_t = \frac{1}{2} \ln\!\left(\frac{1 - \epsilon_t}{\epsilon_t}\right)$$

```python
from sklearn.ensemble import GradientBoostingClassifier, AdaBoostClassifier

# 그래디언트 부스팅
gb = GradientBoostingClassifier(
    n_estimators=200,
    learning_rate=0.05,   # 낮은 학습률 + 많은 나무 = 일반적으로 좋은 성능
    max_depth=3,          # 각 나무는 얕게 (약한 학습기)
    subsample=0.8,        # 확률적 그래디언트 부스팅 (분산 감소 효과)
    random_state=42
)
gb.fit(X_train, y_train)
print(f"그래디언트 부스팅 - Test: {gb.score(X_test, y_test):.4f}")

# AdaBoost
ada = AdaBoostClassifier(
    estimator=DecisionTreeClassifier(max_depth=1),  # Decision Stump
    n_estimators=200,
    learning_rate=0.5,
    random_state=42
)
ada.fit(X_train, y_train)
print(f"AdaBoost - Test: {ada.score(X_test, y_test):.4f}")

# 학습 과정 시각화 (반복 횟수에 따른 성능 변화)
import matplotlib.pyplot as plt
train_scores = []
test_scores  = []
for i, pred in enumerate(gb.staged_predict(X_train)):
    train_scores.append(accuracy_score(y_train, pred))
for i, pred in enumerate(gb.staged_predict(X_test)):
    test_scores.append(accuracy_score(y_test, pred))

plt.figure(figsize=(10, 5))
plt.plot(train_scores, label='Train Accuracy')
plt.plot(test_scores,  label='Test Accuracy')
plt.xlabel('Number of Estimators')
plt.ylabel('Accuracy')
plt.title('Gradient Boosting: 반복 횟수에 따른 성능')
plt.legend()
plt.grid(True)
plt.show()
```

```output
그래디언트 부스팅 - Test: 0.9100
AdaBoost - Test: 0.8100
```

![Ensemble-Overview Fig 1](/media/figures/outputs/ensemble-overview/ensemble-overview_fig_1.png)

## 스태킹: 메타 학습

**스태킹(Stacking)**은 서로 다른 알고리즘의 예측값을 새로운 특성으로 사용해 메타 학습기(Meta-Learner)를 훈련하는 2단계 앙상블이다.

**핵심**: 1단계 학습기(Base Learner)의 예측값이 메타 학습기의 입력이 된다. 데이터 누수(Data Leakage)를 방지하기 위해 1단계 예측은 반드시 교차 검증으로 생성해야 한다.

```python
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC

# 1단계: 다양한 알고리즘으로 Base Learner 구성
base_estimators = [
    ('rf',  RandomForestClassifier(n_estimators=100, random_state=42)),
    ('gb',  GradientBoostingClassifier(n_estimators=100, random_state=42)),
    ('svc', SVC(probability=True, kernel='rbf', random_state=42))
]

# 2단계: 메타 학습기
stacking = StackingClassifier(
    estimators=base_estimators,
    final_estimator=LogisticRegression(max_iter=1000),
    cv=5,                        # 5-Fold CV로 Base Learner 예측 생성
    stack_method='predict_proba', # 확률값을 메타 특성으로 활용
    n_jobs=-1
)

stacking.fit(X_train, y_train)
print(f"스태킹 - Test: {stacking.score(X_test, y_test):.4f}")
```

```output
스태킹 - Test: 0.9350
```

## 보팅: 간단한 결합

**보팅(Voting)**은 여러 학습기의 예측을 단순히 합산하는 가장 직관적인 앙상블이다.

- **하드 보팅(Hard Voting)**: 각 학습기의 클래스 예측에서 다수결을 취한다.
- **소프트 보팅(Soft Voting)**: 각 학습기의 클래스 확률을 평균 내어, 확률이 가장 높은 클래스를 선택한다. 일반적으로 하드 보팅보다 성능이 좋다.

$$\hat{y}_{\text{soft}} = \arg\max_c \frac{1}{M} \sum_{m=1}^{M} P_m(y = c \mid \mathbf{x})$$

```python
from sklearn.ensemble import VotingClassifier

voting = VotingClassifier(
    estimators=[
        ('rf',  RandomForestClassifier(n_estimators=100, random_state=42)),
        ('gb',  GradientBoostingClassifier(n_estimators=100, random_state=42)),
        ('lr',  LogisticRegression(max_iter=1000, random_state=42))
    ],
    voting='soft',       # 'hard' 또는 'soft'
    weights=[2, 2, 1]    # RF와 GB에 2배 가중치
)
voting.fit(X_train, y_train)
print(f"소프트 보팅 - Test: {voting.score(X_test, y_test):.4f}")
```

```output
소프트 보팅 - Test: 0.8900
```

![앙상블 다양성: 학습기 간 상관관계가 낮을수록 앙상블 성능이 향상](figures/ensemble_diversity.png)
*앙상블 다양성: 개별 학습기들이 서로 다른 오류 패턴을 보일수록 결합 시 성능이 향상되며, 높은 다양성이 앙상블의 핵심이다.*

## 다양성의 중요성

학습기들의 예측이 서로 높게 상관되어 있으면 앙상블 효과가 없다. 다양성을 확보하는 방법:

1. **데이터 다양화**: 부트스트랩 샘플링, 다른 데이터 부분집합
2. **특성 다양화**: 랜덤 포레스트처럼 각 분기에서 일부 특성만 고려
3. **알고리즘 다양화**: 선형 모델 + 트리 모델 + 커널 모델 혼합
4. **하이퍼파라미터 다양화**: 같은 알고리즘이지만 다른 설정

## 앙상블 전략 선택 가이드

| 상황 | 추천 | 이유 |
|---|---|---|
| 복잡한 모델이 과적합 | 배깅 | 분산 감소 |
| 단순한 모델이 과소적합 | 부스팅 | 편향 감소 |
| 최고 성능 추구 | 스태킹 | 다양한 알고리즘 결합 |
| 빠른 구현 필요 | 랜덤 포레스트 | 배깅의 최적화 구현 |
| 노이즈가 많은 데이터 | 배깅 | 부스팅은 노이즈에 취약 |
| 불균형 클래스 | 부스팅 | 오분류 샘플에 집중 |

단일 모델로 성능이 막혔을 때 앙상블은 가장 믿을 수 있는 다음 단계다. 랜덤 포레스트와 그래디언트 부스팅(XGBoost, LightGBM)이 표 형태 데이터에서 꾸준히 최상위 성능을 기록하는 것은 이 두 전략의 힘을 입증한다.