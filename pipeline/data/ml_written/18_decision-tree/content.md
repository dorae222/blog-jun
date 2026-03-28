## 규칙으로 설명할 수 있는 모델

머신러닝 모델 중 가장 직관적으로 설명 가능한 것이 **의사결정 나무(Decision Tree)**다. 각 노드가 하나의 질문("나이가 30 이상인가?")이고, 예측 결과까지의 경로가 곧 분류 규칙이다. 이 투명성 덕분에 의사결정 나무는 의료 진단, 금융 신용 평가, 법적 규제가 있는 도메인에서 특히 중요하게 사용된다.

또한 **배깅(Random Forest)과 부스팅(Gradient Boosting)**의 기반 학습기(Base Learner)로서, 현대 앙상블 방법의 핵심 구성 요소이기도 하다.

## 나무 구조의 용어

- **루트 노드(Root Node)**: 최상단, 전체 데이터셋으로 시작
- **내부 노드(Internal Node)**: 분기 조건(특성과 임계값)을 담음
- **리프 노드(Leaf Node)**: 최종 예측값(클래스 레이블 또는 평균값)
- **깊이(Depth)**: 루트에서 리프까지의 최대 분기 횟수
- **순도(Purity)**: 한 노드 안에 같은 클래스의 비율이 높을수록 순도가 높다

## 분기 기준 1: 엔트로피와 정보 이득

정보 이론에서 차용한 **엔트로피(Entropy)**는 노드의 불순도를 측정한다. 노드 안의 모든 샘플이 같은 클래스이면 엔트로피 = 0, 클래스가 완전히 뒤섞이면 최대가 된다.

$$H(S) = -\sum_{c=1}^{C} p_c \log_2 p_c$$

여기서 $p_c$는 노드 $S$에서 클래스 $c$의 비율이다. 관례적으로 $0 \log 0 = 0$으로 처리한다.

**정보 이득(Information Gain)**은 분기 전후의 엔트로피 감소량이다.

$$\text{IG}(S, A) = H(S) - \sum_{v \in \text{values}(A)} \frac{|S_v|}{|S|} H(S_v)$$

의사결정 나무는 모든 특성과 모든 가능한 임계값을 시도하여 정보 이득이 가장 큰 분기를 선택한다.

**예시**: 노드에 양성 10개, 음성 10개가 있다면
$$H = -(0.5 \log_2 0.5 + 0.5 \log_2 0.5) = 1 \text{ bit}$$

양성 9개, 음성 1개라면
$$H = -(0.9 \log_2 0.9 + 0.1 \log_2 0.1) \approx 0.469 \text{ bit}$$

![불순도 함수 비교: 엔트로피, 지니 불순도, 분류 오류율의 곡선](figures/impurity_functions.png)
*불순도 함수 비교: 엔트로피와 지니 불순도는 유사한 형태를 보이며, 클래스 비율이 균등할 때 최대, 한 클래스만 있을 때 0이 된다.*

## 분기 기준 2: 지니 불순도

**지니 불순도(Gini Impurity)**는 엔트로피의 계산적으로 더 효율적인 대안이다. scikit-learn의 기본값이다.

$$G(S) = 1 - \sum_{c=1}^{C} p_c^2$$

순수한 노드에서 G = 0, 클래스가 균등하게 분포하면 G = $1 - 1/C$가 된다. 이진 분류의 경우 최댓값은 0.5다.

**엔트로피 vs 지니 비교**:
- 지니는 로그 계산이 없어 빠르다
- 엔트로피는 더 균형 잡힌 나무를 생성하는 경향이 있다
- 실전에서 두 기준의 성능 차이는 미미하다

![의사결정 나무 분할 시각화: 특성 공간의 재귀적 분할 과정](figures/decision_tree_partitioning.png)
*의사결정 나무 분할: 각 노드에서 최적의 특성과 임계값으로 공간을 재귀적으로 분할하여 클래스 영역을 형성하는 과정을 보여준다.*

## CART 알고리즘

scikit-learn의 의사결정 나무는 **CART(Classification And Regression Trees)** 알고리즘을 사용한다. CART의 특징은:
- 항상 **이진 분기(Binary Split)**만 생성한다
- 연속형 특성: 특성값 정렬 후 모든 가능한 임계값 탐색
- 범주형 특성: 원-핫 인코딩 후 이진 분기로 처리
- 회귀에서는 **MSE(평균 제곱 오차)** 최소화를 기준으로 분기

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor, plot_tree, export_text
from sklearn.datasets import load_iris, make_classification
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score

# 붓꽃 분류
iris = load_iris()
X_train, X_test, y_train, y_test = train_test_split(
    iris.data, iris.target, test_size=0.2, random_state=42, stratify=iris.target
)

# 의사결정 나무 학습 (과적합 상태)
dt = DecisionTreeClassifier(criterion='gini', random_state=42)
dt.fit(X_train, y_train)

print(f"훈련 정확도: {dt.score(X_train, y_train):.4f}")
print(f"테스트 정확도: {dt.score(X_test, y_test):.4f}")
print(f"나무 깊이: {dt.get_depth()}")
print(f"리프 노드 수: {dt.get_n_leaves()}")

# 나무 시각화
plt.figure(figsize=(20, 10))
plot_tree(dt, feature_names=iris.feature_names,
          class_names=iris.target_names,
          filled=True, rounded=True, fontsize=10)
plt.title('Decision Tree (Unpruned)')
plt.tight_layout()
plt.show()

# 텍스트 규칙 출력
rules = export_text(dt, feature_names=list(iris.feature_names))
print(rules[:800])  # 앞부분만 출력
```

```output
훈련 정확도: 1.0000
테스트 정확도: 0.9333
나무 깊이: 5
리프 노드 수: 8
|--- petal length (cm) <= 2.45
|   |--- class: 0
|--- petal length (cm) >  2.45
|   |--- petal width (cm) <= 1.65
|   |   |--- petal length (cm) <= 4.95
|   |   |   |--- class: 1
|   |   |--- petal length (cm) >  4.95
|   |   |   |--- sepal length (cm) <= 6.15
|   |   |   |   |--- sepal width (cm) <= 2.45
|   |   |   |   |   |--- class: 2
|   |   |   |   |--- sepal width (cm) >  2.45
|   |   |   |   |   |--- class: 1
|   |   |   |--- sepal length (cm) >  6.15
|   |   |   |   |--- class: 2
|   |--- petal width (cm) >  1.65
|   |   |--- petal length (cm) <= 4.85
|   |   |   |--- sepal width (cm) <= 3.00
|   |   |   |   |--- class: 2
|   |   |   |--- sepal width (cm) >  3.00
|   |   |   |   |--- class: 1
|   |   |--- petal length (cm) >  4.85
|   |   |   |--- class: 2
```

![의사결정 나무 구조 시각화](figures/decision_tree_partitioning.png)

*Figure 1: 의사결정 나무 구조: 학습된 나무의 분기 조건과 각 리프 노드의 클래스 분류 결과를 트리 형태로 시각화한다.*

## 과적합 제어: 사전 가지치기 (Pre-Pruning)

제한 없이 자라도록 두면 의사결정 나무는 훈련 데이터를 완전히 암기해버린다. **사전 가지치기**는 나무 성장을 조기에 멈추는 방법이다.

```python
# 주요 하이퍼파라미터 설명
# max_depth        : 나무 최대 깊이. 가장 중요한 파라미터
# min_samples_split: 분기에 필요한 최소 샘플 수
# min_samples_leaf : 리프 노드의 최소 샘플 수
# max_features     : 각 분기에서 고려할 최대 특성 수
# min_impurity_decrease: 분기로 얻어야 하는 최소 불순도 감소량

param_grid = {
    'max_depth': [2, 3, 4, 5, None],
    'min_samples_split': [2, 5, 10, 20],
    'min_samples_leaf': [1, 2, 5, 10],
    'criterion': ['gini', 'entropy']
}

grid_search = GridSearchCV(
    DecisionTreeClassifier(random_state=42),
    param_grid, cv=5, scoring='accuracy', n_jobs=-1
)
grid_search.fit(X_train, y_train)

print(f"최적 파라미터: {grid_search.best_params_}")
print(f"최적 CV 정확도: {grid_search.best_score_:.4f}")

best_dt = grid_search.best_estimator_
print(f"테스트 정확도: {best_dt.score(X_test, y_test):.4f}")
print(classification_report(y_test, best_dt.predict(X_test), target_names=iris.target_names))
```

```output
최적 파라미터: {'criterion': 'gini', 'max_depth': 4, 'min_samples_leaf': 1, 'min_samples_split': 2}
최적 CV 정확도: 0.9417
테스트 정확도: 0.9333
              precision    recall  f1-score   support

      setosa       1.00      1.00      1.00        10
  versicolor       0.90      0.90      0.90        10
   virginica       0.90      0.90      0.90        10

    accuracy                           0.93        30
   macro avg       0.93      0.93      0.93        30
weighted avg       0.93      0.93      0.93        30
```

## 사후 가지치기 (Post-Pruning): CCP

**비용-복잡도 가지치기(Cost-Complexity Pruning, CCP)**는 나무를 완전히 성장시킨 후 복잡도 패널티를 적용해 불필요한 가지를 제거하는 방법이다.

$$\text{비용}(T) = \text{오차}(T) + \alpha \cdot |T|$$

$|T|$는 리프 노드 수, $\alpha$는 정규화 강도다. $\alpha$가 클수록 단순한 나무가 만들어진다.

```python
# CCP 경로 계산
dt_full = DecisionTreeClassifier(random_state=42)
path = dt_full.cost_complexity_pruning_path(X_train, y_train)
ccp_alphas = path.ccp_alphas[:-1]  # 마지막 값(루트만 남음)은 제외

# 각 alpha에 대해 교차 검증
from sklearn.model_selection import cross_val_score
cv_scores = []
for alpha in ccp_alphas:
    dt_ccp = DecisionTreeClassifier(ccp_alpha=alpha, random_state=42)
    scores = cross_val_score(dt_ccp, X_train, y_train, cv=5)
    cv_scores.append(scores.mean())

best_alpha = ccp_alphas[np.argmax(cv_scores)]
dt_pruned = DecisionTreeClassifier(ccp_alpha=best_alpha, random_state=42)
dt_pruned.fit(X_train, y_train)
print(f"최적 alpha: {best_alpha:.6f}")
print(f"가지치기 후 깊이: {dt_pruned.get_depth()}")
print(f"가지치기 후 테스트 정확도: {dt_pruned.score(X_test, y_test):.4f}")
```

```output
최적 alpha: 0.000000
가지치기 후 깊이: 5
가지치기 후 테스트 정확도: 0.9333
```

## 특성 중요도

의사결정 나무는 학습 후 각 특성의 기여도를 자동으로 계산한다. 각 특성이 분기에 사용될 때 불순도 감소량의 가중 합계가 **특성 중요도(Feature Importance)**다.

```python
feature_importances = best_dt.feature_importances_
sorted_idx = np.argsort(feature_importances)[::-1]

plt.figure(figsize=(8, 4))
plt.bar(range(len(feature_importances)),
        feature_importances[sorted_idx])
plt.xticks(range(len(feature_importances)),
           [iris.feature_names[i] for i in sorted_idx],
           rotation=45, ha='right')
plt.title('특성 중요도')
plt.tight_layout()
plt.show()
```

![특성 중요도 시각화](figures/impurity_functions.png)

*Figure 2: 특성 중요도: 의사결정 나무가 학습한 각 특성의 불순도 감소 기여도를 막대 그래프로 비교한다.*

## 의사결정 나무의 장단점

**장점**
- 화이트 박스 모델로 규칙을 사람이 이해하고 설명할 수 있다
- 특성 스케일링이 불필요하다 (거리 계산 없음)
- 수치형·범주형 혼합 데이터를 모두 다룰 수 있다
- 비선형 결정 경계를 자동으로 학습한다
- 특성 중요도를 자연스럽게 제공한다

**단점**
- 정규화 없이는 훈련 데이터에 쉽게 과적합한다
- 데이터의 작은 변화에 불안정하다 (분산이 높음)
- 전역 최적해가 아닌 탐욕적(Greedy) 방법으로 분기를 찾는다
- 클래스 불균형에 취약하다
- 대각선 결정 경계를 표현하기 어렵다 (항상 축에 수직)

이런 단점들이 바로 **랜덤 포레스트**와 **그래디언트 부스팅** 같은 앙상블 방법이 탄생한 이유다.

## 범주형 변수와 결측값 처리

의사결정 나무는 이론적으로 범주형 변수를 직접 다룰 수 있지만, scikit-learn의 CART 구현은 수치형 입력만 받는다. 따라서 범주형 변수는 전처리가 필요하다.

**범주형 변수 처리 방법**:
- **원-핫 인코딩(One-Hot Encoding)**: 가장 일반적인 방법이지만, 카디널리티가 높은 변수(도시명, 제품 ID 등)에서는 특성 수가 폭발한다. 또한 원-핫 인코딩된 변수는 각 분기에서 하나의 범주만 분리할 수 있어, 여러 범주를 한쪽으로 묶는 자연스러운 분기를 만들지 못한다.
- **순서 인코딩(Ordinal Encoding)**: 범주에 임의 정수를 부여하는 방법이다. 트리 모델은 순서 관계를 가정하지 않고 임계값 기반으로 분기하므로, 순서가 없는 범주에도 사용 가능하다. 실전에서는 원-핫보다 효율적인 경우가 많다.
- **타깃 인코딩(Target Encoding)**: 각 범주를 해당 범주의 타깃 평균으로 치환한다. 고카디널리티 변수에 효과적이지만, 과적합 방지를 위해 교차 검증 기반으로 적용해야 한다.

```python
from sklearn.preprocessing import OrdinalEncoder
from sklearn.compose import ColumnTransformer

# 범주형/수치형 혼합 데이터 처리 파이프라인
preprocessor = ColumnTransformer(
    transformers=[
        ('num', 'passthrough', ['age', 'income']),
        ('cat', OrdinalEncoder(handle_unknown='use_encoded_value',
                               unknown_value=-1),
         ['city', 'education'])
    ]
)
```

**결측값 처리**에서도 의사결정 나무는 고유한 장점이 있다. XGBoost와 LightGBM은 결측값을 네이티브로 처리하여, 각 분기에서 결측값을 가진 샘플을 왼쪽 또는 오른쪽 자식 노드 중 더 유리한 방향으로 자동 배정한다. scikit-learn의 경우 `HistGradientBoostingClassifier`가 이 기능을 지원한다. 기본 `DecisionTreeClassifier`는 결측값을 허용하지 않으므로, `SimpleImputer`로 사전 대체가 필요하다.

## 나무의 불안정성과 해석 가능성의 한계

의사결정 나무의 가장 큰 실전적 문제 중 하나는 **불안정성(Instability)**이다. 학습 데이터의 작은 변화가 완전히 다른 트리 구조를 만들어낼 수 있다. 이는 탐욕적(Greedy) 분기 방식에서 비롯된다.

루트 노드에서 최적 분기 특성이 바뀌면, 그 아래의 모든 구조가 연쇄적으로 달라진다. 예를 들어, 두 특성의 정보 이득이 거의 같을 때 훈련 데이터에서 샘플 몇 개만 바뀌어도 루트 분기가 완전히 변경될 수 있다. 이 현상은 나무가 깊을수록, 데이터가 적을수록 심해진다.

이 불안정성은 해석 가능성에도 영향을 준다. 의사결정 나무가 "화이트 박스 모델"이라고 하지만, 데이터가 조금만 달라져도 완전히 다른 규칙이 나온다면 그 규칙을 신뢰할 수 있을까? 실전에서는 다음과 같은 대응 방법이 있다:

- **여러 번 학습**: 데이터를 약간씩 변형하여 여러 트리를 학습하고, 공통적으로 나타나는 분기 패턴을 신뢰한다.
- **안정성 지표 활용**: 부트스트랩 샘플에서 동일한 변수가 루트에 선택되는 빈도를 측정한다.
- **랜덤 포레스트의 특성 중요도**: 단일 트리의 규칙보다 앙상블의 특성 중요도가 훨씬 안정적인 해석을 제공한다.

## 지니 불순도 vs 엔트로피: 실전에서의 차이

앞서 "실전에서 두 기준의 성능 차이는 미미하다"고 언급했지만, 차이가 발생하는 특정 상황이 있다.

**엔트로피가 유리한 경우**: 엔트로피는 클래스 비율의 변화에 더 민감하다. 이진 분류에서 클래스 비율이 (0.5, 0.5)에서 (0.4, 0.6)으로 변할 때, 엔트로피는 1.0에서 0.971로, 지니는 0.5에서 0.48로 변한다. 엔트로피의 변화율이 더 크기 때문에, 클래스 간 미세한 분포 차이를 구분해야 하는 다중 클래스 문제에서 엔트로피가 더 균형 잡힌 트리를 생성하는 경향이 있다.

**지니가 유리한 경우**: 지니 불순도는 로그 연산이 없으므로 계산이 빠르다. 대규모 데이터셋에서 수만 번의 분기 평가가 이루어지므로, 지니의 계산 효율성은 실질적인 속도 차이로 이어진다. 또한 지니는 가장 빈번한 클래스를 분리하는 데 집중하는 경향이 있어, 이진 분류에서 직관적으로 이해하기 쉬운 분기를 만든다.

**결론적으로**: 대부분의 경우 scikit-learn의 기본값인 지니 불순도로 충분하다. 다중 클래스 분류에서 균형 잡힌 트리가 필요하거나, 정보 이론 기반의 해석이 중요한 경우에만 엔트로피를 선택하면 된다. 성능 차이보다는 **가지치기 파라미터**와 **트리 깊이**가 최종 성능에 훨씬 큰 영향을 미친다.