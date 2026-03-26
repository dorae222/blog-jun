## 1. 개요: 모델 선택의 핵심, 일반화 성능 추정

머신러닝 모델을 만드는 최종 목표는 **학습 데이터에 잘 맞는 모델**이 아니라, **본 적 없는 데이터에 잘 동작하는 모델**이다. 이 능력을 **일반화(Generalization)** 라 부른다.

모델을 선택하고 평가할 때 가장 중요한 질문은 이것이다:

> "이 모델의 성능 추정치가 실제 배포 환경에서도 믿을 수 있는가?"

단순히 전체 데이터로 학습하고 같은 데이터로 평가하면 **낙관적 편향(optimistic bias)** 이 생긴다. 이를 피하기 위해 데이터를 학습용과 평가용으로 분리하는 전략이 필요하고, 그 전략 중 가장 강력한 도구가 **교차 검증(Cross-Validation)** 이다.

---

## 2. Hold-Out vs. Cross-Validation

### Hold-Out 방식

가장 단순한 방법은 데이터를 한 번 나누는 **홀드아웃(Hold-Out)** 이다.

$$D = D_{train} \cup D_{test}, \quad D_{train} \cap D_{test} = \emptyset$$

일반적으로 70~80%를 학습에, 20~30%를 테스트에 할당한다. 직관적이고 빠르지만 **심각한 단점**이 있다.

- 분할 방식에 따라 성능 추정치가 크게 달라진다 (분산이 높다)
- 운 좋은 분할이면 과대평가, 운 나쁜 분할이면 과소평가된다
- 데이터가 적을 때 학습 데이터가 줄어들어 모델 품질이 떨어진다

즉, Hold-Out은 **운에 의존하는 평가**라는 근본적 문제를 가진다.

### K-Fold Cross-Validation

K-Fold CV는 이 문제를 해결한다. 데이터를 $K$개의 동일한 크기의 **폴드(fold)** 로 나누고, $K$번 반복하면서 매번 다른 폴드를 검증용으로 사용한다.

$$\text{CV Score} = \frac{1}{K} \sum_{k=1}^{K} \mathcal{L}(f^{(-k)}, D_k)$$

여기서 $f^{(-k)}$는 $k$번째 폴드를 제외한 나머지 데이터로 학습한 모델, $D_k$는 $k$번째 폴드(검증 세트)이다.

**K-Fold의 장점:**
- 모든 데이터가 정확히 한 번씩 검증에 사용된다 → 데이터 효율적 활용
- $K$번의 독립적인 추정치를 평균하므로 분산이 낮아진다
- 작은 데이터셋에서 특히 효과적이다

**편향-분산 트레이드오프:** $K$가 클수록 편향은 낮아지지만 각 폴드 간 학습 세트가 겹쳐 추정치의 분산이 높아진다. 실무에서는 **$K=5$ 또는 $K=10$** 이 일반적으로 좋은 균형점이다.

---

## 3. K-Fold 교차 검증의 다양한 변형

### Stratified K-Fold (층화 K-겹 교차 검증)

**분류 문제**에서 기본 K-Fold를 사용하면 클래스 불균형이 있을 때 특정 폴드에 한 클래스가 몰릴 수 있다. Stratified K-Fold는 **각 폴드의 클래스 비율을 전체 데이터와 동일하게 유지**한다.

예를 들어 양성:음성 = 1:9인 데이터라면, 각 폴드에서도 이 비율이 유지된다. 불균형 데이터에서는 반드시 Stratified K-Fold를 사용해야 신뢰할 수 있는 평가가 가능하다.

```python
from sklearn.model_selection import StratifiedKFold

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for train_idx, val_idx in skf.split(X, y):
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
```

### Leave-One-Out (LOO)

LOO는 $K = N$ (샘플 수)인 극단적 케이스다. 매번 한 샘플만 검증에 사용하고 나머지 $N-1$개로 학습한다.

$$\text{LOO CV} = \frac{1}{N} \sum_{i=1}^{N} \mathcal{L}(f^{(-i)}, x_i)$$

편향은 가장 낮지만, 계산 비용이 $O(N)$배로 비싸고 추정치의 분산이 높은 편이다. **데이터가 극히 적을 때(50개 미만)** 고려해볼 수 있다.

### Time Series Split (시계열 분할)

시계열 데이터에서는 미래 정보가 과거 학습에 섞이는 **데이터 누수(data leakage)** 를 반드시 방지해야 한다. 랜덤 분할은 절대 사용해선 안 되며, **항상 학습 세트가 검증 세트보다 시간적으로 앞서야** 한다.

Time Series Split은 이를 보장한다:

- Fold 1: Train `[1~4]` → Val `[5]`
- Fold 2: Train `[1~5]` → Val `[6]`
- Fold 3: Train `[1~6]` → Val `[7]`

학습 윈도우가 점점 커지는 **expanding window** 방식이다. 고정 크기 학습 윈도우가 필요하면 `max_train_size` 파라미터로 조절할 수 있다.

### Group K-Fold (그룹 K-겹 교차 검증)

동일한 피험자/환자/사용자 등이 학습 세트와 검증 세트에 **동시에 등장하는 것**을 막아야 할 때 사용한다. 예를 들어 의료 데이터에서 같은 환자의 여러 측정값이 있을 때, 같은 환자가 train과 val에 나뉘면 실제보다 성능이 좋게 추정된다.

Group K-Fold는 동일 그룹이 반드시 같은 폴드에 속하도록 보장한다.

```python
from sklearn.model_selection import GroupKFold

gkf = GroupKFold(n_splits=5)
for train_idx, val_idx in gkf.split(X, y, groups=patient_ids):
    ...
```

---

## 4. Nested Cross-Validation (중첩 교차 검증)

교차 검증으로 하이퍼파라미터를 튜닝하면 한 가지 함정이 있다. 검증 세트를 하이퍼파라미터 선택에 사용했으므로, 그 성능 추정치는 낙관적으로 편향된다.

이를 해결하는 것이 **Nested CV**다. 두 개의 루프를 중첩한다.

- **외부 루프 (Outer Loop):** 최종 모델 성능을 불편 추정하는 역할. $K_{out}$개의 폴드로 분할
- **내부 루프 (Inner Loop):** 외부 루프의 학습 세트 안에서 하이퍼파라미터를 튜닝. $K_{in}$개의 폴드로 분할

```
전체 데이터
  └─ [외부 Fold 1] 학습 + 테스트
       └─ [내부 Fold 1~5] 하이퍼파라미터 탐색
  └─ [외부 Fold 2] 학습 + 테스트
       └─ [내부 Fold 1~5] 하이퍼파라미터 탐색
  ...
```

외부 루프의 각 테스트 폴드 성능을 평균하면 **하이퍼파라미터 튜닝 과정까지 포함한 진정한 일반화 성능 추정치**를 얻는다. 계산 비용은 $O(K_{out} \times K_{in})$배로 높아지지만, 모델 선택의 신뢰도가 가장 높은 방법이다.

---

## 5. 하이퍼파라미터 탐색 방법

### Grid Search (격자 탐색)

정해진 하이퍼파라미터 후보들의 **모든 조합**을 탐색한다.

$$\text{탐색 횟수} = \prod_{i=1}^{k} |H_i|$$

예를 들어 파라미터 3개, 각각 후보가 5개씩이면 $5^3 = 125$번 학습이 필요하다. 파라미터가 늘어날수록 **지수적으로 복잡도가 증가($O(n^k)$)** 하는 **차원의 저주**에 빠진다.

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    'C': [0.01, 0.1, 1, 10, 100],
    'kernel': ['rbf', 'linear'],
    'gamma': ['scale', 'auto', 0.001, 0.01]
}
grid_search = GridSearchCV(SVC(), param_grid, cv=5, scoring='f1', n_jobs=-1)
grid_search.fit(X_train, y_train)
print(grid_search.best_params_, grid_search.best_score_)
```

<!-- Execution error: NameError: name 'SVC' is not defined -->

장점: 모든 조합을 보장하므로 최적값을 놓치지 않는다. 단점: 후보 공간이 커지면 현실적으로 불가능하다.

### Random Search (랜덤 탐색)

Bergstra & Bengio (2012)의 연구에서 **Random Search가 Grid Search보다 효율적임**을 보였다. 핵심 통찰은 이것이다: 많은 하이퍼파라미터 조합에서 **일부 파라미터만 성능에 실질적 영향**을 미친다. Grid Search는 중요하지 않은 파라미터에도 동일한 밀도로 탐색하지만, Random Search는 연속 분포에서 샘플링하므로 **중요한 파라미터 축을 더 다양하게 탐색**한다.

$$\text{효율적 탐색 확률} = 1 - \left(1 - \frac{1}{n}\right)^T \approx 1 - e^{-T/n}$$

$n$개 구간 중 최적이 있을 때 $T$번 랜덤 시도하면 위 확률로 최적 근방을 찾는다.

```python
from sklearn.model_selection import RandomizedSearchCV
from scipy.stats import loguniform, randint

param_dist = {
    'C': loguniform(1e-3, 1e3),        # 로그 균등분포
    'kernel': ['rbf', 'linear'],
    'gamma': loguniform(1e-4, 1e0)
}
random_search = RandomizedSearchCV(
    SVC(), param_dist, n_iter=50, cv=5,
    scoring='f1', random_state=42, n_jobs=-1
)
random_search.fit(X_train, y_train)
```

실무 팁: 연속 하이퍼파라미터는 `scipy.stats`의 분포 객체로 지정하면 균등한 확률로 샘플링된다. 특히 학습률 같은 파라미터는 `loguniform`을 쓰는 것이 좋다.

### Bayesian Optimization (베이지안 최적화)

Grid/Random Search는 **이전 시도의 결과를 전혀 활용하지 않는다.** Bayesian Optimization은 다르다. 탐색 결과를 축적해 **사후 확률 모델(surrogate model)** 을 구축하고, 이를 이용해 다음에 탐색할 지점을 지능적으로 선택한다.

**가우시안 프로세스(Gaussian Process, GP)** 를 surrogate로 쓰는 경우:

$$f(\mathbf{x}) \sim \mathcal{GP}(\mu(\mathbf{x}), k(\mathbf{x}, \mathbf{x}'))$$

관측된 점들을 조건화해 $f$의 사후 분포 $p(f | \mathcal{D})$를 업데이트한다. 이 사후 분포에서 **어디를 다음에 탐색할지** 결정하는 함수를 **획득 함수(Acquisition Function)** 라 한다.

가장 널리 쓰이는 **Expected Improvement (EI):**

$$\text{EI}(\mathbf{x}) = \mathbb{E}[\max(f(\mathbf{x}) - f^*, 0)]$$

$$= (\mu(\mathbf{x}) - f^*) \Phi(Z) + \sigma(\mathbf{x}) \phi(Z), \quad Z = \frac{\mu(\mathbf{x}) - f^*}{\sigma(\mathbf{x})}$$

여기서 $f^*$는 현재까지의 최고 성능, $\Phi$는 표준 정규 CDF, $\phi$는 PDF다. EI는 **현재 최고 성능을 얼마나 개선할 수 있는지의 기대값**으로, 평균이 높은 지점(exploitation)과 불확실성이 높은 지점(exploration)의 균형을 자동으로 맞춘다.

#### Optuna

```python
import optuna

def objective(trial):
    C = trial.suggest_float('C', 1e-3, 1e3, log=True)
    kernel = trial.suggest_categorical('kernel', ['rbf', 'linear'])
    gamma = trial.suggest_float('gamma', 1e-4, 1.0, log=True)

    model = SVC(C=C, kernel=kernel, gamma=gamma)
    scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1')
    return scores.mean()

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
print(study.best_params)
```

<!-- Execution error: ModuleNotFoundError: No module named 'optuna' -->

Optuna는 기본적으로 **TPE(Tree-structured Parzen Estimator)** 알고리즘을 사용한다. GP보다 고차원 공간에서 효율적이며, 조건부 탐색(어떤 파라미터 값에 따라 다른 파라미터를 달리 탐색)도 자연스럽게 지원한다.

#### Hyperopt

```python
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials

space = {
    'C': hp.loguniform('C', -3, 3),
    'kernel': hp.choice('kernel', ['rbf', 'linear']),
    'gamma': hp.loguniform('gamma', -4, 0)
}

def objective(params):
    model = SVC(**params)
    score = cross_val_score(model, X_train, y_train, cv=5).mean()
    return {'loss': -score, 'status': STATUS_OK}

best = fmin(fn=objective, space=space, algo=tpe.suggest, max_evals=100)
```

---

## 6. 조기 종료 (Early Stopping)

딥러닝이나 Gradient Boosting처럼 반복적으로 학습하는 모델에서는 **조기 종료(Early Stopping)** 가 하이퍼파라미터 튜닝의 핵심 요소다. 검증 손실이 일정 에폭/라운드 이상 개선되지 않으면 학습을 중단한다.

$$\text{stop if} \quad \mathcal{L}_{val}(t) > \mathcal{L}_{val}^{\text{best}} \quad \text{for } patience \text{ steps}$$

XGBoost/LightGBM에서는 `early_stopping_rounds` 파라미터로, Keras/PyTorch에서는 콜백으로 쉽게 구현할 수 있다. 이 경우 **트리 개수(n_estimators)나 에폭 수를 별도로 튜닝할 필요가 없어** 탐색 공간이 크게 줄어든다.

---

## 7. 실전 팁: 어떤 방법을 언제?

| 상황 | 권장 방법 |
|---|---|
| 파라미터 ≤ 3개, 후보 적음 | Grid Search |
| 파라미터 많고 연속적 | Random Search |
| 튜닝 비용이 높고 trial 수 제한 | Bayesian Optimization (Optuna) |
| 시계열 데이터 | Time Series Split |
| 클래스 불균형 분류 | Stratified K-Fold |
| 환자/사용자 단위 데이터 | Group K-Fold |
| 최종 모델 성능 불편 추정 | Nested CV |
| 데이터 < 100개 | LOO 또는 K=10 Fold |

**공통 원칙:**
1. 테스트 세트는 최종 평가 한 번만 사용한다. 여러 번 보면 오염된다.
2. 전처리(스케일링, 인코딩)는 반드시 각 폴드의 학습 세트만으로 fit하고 검증 세트에 transform만 적용한다. 전체 데이터로 fit하면 데이터 누수다.
3. 성능 지표는 평균뿐만 아니라 **표준편차**도 함께 보고하고 해석한다.
4. `sklearn.pipeline.Pipeline`을 사용하면 전처리 누수를 자동으로 방지할 수 있다.

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score

pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('clf', SVC())
])

# cross_val_score는 각 폴드마다 scaler를 fit_transform → transform으로 안전하게 처리
scores = cross_val_score(pipe, X, y, cv=StratifiedKFold(5), scoring='f1_macro')
print(f"F1: {scores.mean():.4f} ± {scores.std():.4f}")
```

<!-- Execution error: NameError: name 'X' is not defined -->

---

## 마무리

교차 검증과 하이퍼파라미터 튜닝은 별개의 작업이 아니라 **모델 선택의 파이프라인** 안에서 함께 설계되어야 한다. 적절한 CV 전략 없이 튜닝한 하이퍼파라미터는 신뢰하기 어렵고, 튜닝 없이 기본 파라미터로만 평가한 모델은 잠재력을 제대로 드러내지 못한다. 데이터의 특성(시계열, 클래스 불균형, 그룹 구조)을 파악하고, 그에 맞는 검증 전략을 선택하는 것이 좋은 머신러닝의 출발점이다.