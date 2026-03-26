## 1. Pipeline이 없으면 생기는 문제들

scikit-learn으로 머신러닝 모델을 만들 때, 많은 개발자들이 전처리와 모델 학습을 분리해서 작성한다. 처음에는 코드가 단순해 보이지만 이 방식은 세 가지 심각한 문제를 낳는다.

### 교차 검증 중 Data Leakage

가장 위험한 문제는 Data Leakage다. 교차 검증(Cross-Validation)을 수행할 때, 전처리를 미리 전체 데이터에 적용하면 검증 fold의 정보가 학습에 스며든다.

```python
# 잘못된 방법 - Data Leakage 발생
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LogisticRegression

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # 전체 데이터로 fit → 검증 데이터 정보 유출!

model = LogisticRegression()
scores = cross_val_score(model, X_scaled, y, cv=5)
# 이 점수는 실제보다 낙관적으로 나온다
```

위 코드에서 `scaler.fit_transform(X)`는 검증 fold에 포함될 데이터의 평균과 표준편차도 함께 사용해 스케일링한다. 즉, 모델이 검증 데이터를 학습 시점에 이미 '본' 셈이 되어 성능이 과대평가된다. 실제 배포 환경에서는 이 검증 fold처럼 학습 때 보지 못한 데이터가 들어오므로, 검증 점수와 실제 성능 사이에 큰 괴리가 생긴다.

### 배포 시 전처리 코드 불일치

두 번째 문제는 배포(Deployment) 단계에서 발생한다. 학습 코드와 추론 코드가 분리되면, 개발자가 실수로 전처리 파라미터를 다르게 적용할 수 있다.

```python
# 학습 시
scaler = StandardScaler()
scaler.fit(X_train)
X_train_scaled = scaler.transform(X_train)
model.fit(X_train_scaled, y_train)

# 배포 서버에서 (실수로 다시 fit)
scaler_new = StandardScaler()
X_new_scaled = scaler_new.fit_transform(X_new)  # 학습 때의 mean/std와 다름!
prediction = model.predict(X_new_scaled)  # 잘못된 예측
```

학습 때 사용한 `scaler`의 `mean_`과 `scale_` 파라미터를 추론 서버에서도 동일하게 적용해야 하지만, 코드가 분리되어 있으면 이를 보장하기 어렵다.

### 코드 중복과 유지보수 어려움

세 번째로, 동일한 전처리 로직이 학습·검증·추론 코드에 각각 존재하면 유지보수가 복잡해진다. 특성 하나를 추가하거나 전처리 방식을 바꿀 때 세 곳을 모두 수정해야 하고, 하나라도 빠뜨리면 버그가 발생한다.

sklearn Pipeline은 이 세 문제를 단번에 해결한다.

---

![sklearn Pipeline 다이어그램: 전처리부터 모델 학습까지의 파이프라인 구조 시각화](figures/sklearn_pipeline_diagram.png)
*sklearn Pipeline 다이어그램: 데이터 전처리, 특성 변환, 모델 학습이 하나의 파이프라인으로 연결되어 일관된 워크플로를 보장한다.*

## 2. sklearn Pipeline 기본

`Pipeline`은 여러 변환 단계(Transformer)와 최종 추정기(Estimator)를 순서대로 연결한 하나의 객체다. 마지막 단계를 제외한 모든 단계는 `fit`과 `transform` 메서드를 모두 가진 Transformer여야 한다.

```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# (이름, 객체) 튜플의 리스트로 단계를 정의
pipe = Pipeline([
    ('scaler', StandardScaler()),
    ('model', LogisticRegression(max_iter=1000))
])

# fit: X_train을 scaler로 fit_transform한 후, 그 결과로 model을 fit
pipe.fit(X_train, y_train)

# predict: X_test를 scaler로 transform한 후, model로 predict
y_pred = pipe.predict(X_test)  # 자동으로 스케일링 → 예측

# 파이프라인 자체의 score 메서드도 사용 가능
print(pipe.score(X_test, y_test))
```

<!-- Execution error: NameError: name 'X_train' is not defined -->

`pipe.fit(X_train, y_train)` 한 줄이 내부적으로 다음 두 단계를 순서대로 실행한다.

1. `scaler.fit_transform(X_train)` → 스케일된 훈련 데이터 생성
2. `model.fit(스케일된 훈련 데이터, y_train)` → 모델 학습

`pipe.predict(X_test)` 역시 내부적으로 `scaler.transform(X_test)` 후 `model.predict()`를 수행한다. 개별 단계에는 이름으로 접근할 수 있다.

```python
# 단계별 객체 접근
print(pipe['scaler'].mean_)      # 인덱스 이름으로 접근
print(pipe.named_steps['model']) # named_steps 딕셔너리로 접근
```

<!-- Execution error: AttributeError: 'StandardScaler' object has no attribute 'mean_' -->

`make_pipeline`을 사용하면 이름을 자동으로 지정할 수 있다. 단, 이 경우 같은 클래스의 객체를 두 개 이상 넣으면 이름 충돌이 발생하므로 주의한다.

```python
from sklearn.pipeline import make_pipeline

pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
# 단계 이름: 'standardscaler', 'logisticregression'
```

---

## 3. Pipeline과 교차 검증: Data Leakage 방지

Pipeline의 가장 큰 가치는 교차 검증과 결합할 때 드러난다. `cross_val_score`에 파이프라인 객체를 전달하면, **각 fold마다 독립적으로 전처리가 수행**된다.

```python
from sklearn.model_selection import cross_val_score
import numpy as np

# 올바른 방법 - Data Leakage 없음
scores = cross_val_score(pipe, X, y, cv=5, scoring='accuracy')
print(f"CV 정확도: {np.mean(scores):.4f} ± {np.std(scores):.4f}")
```

<!-- Execution error: NameError: name 'X' is not defined -->

내부 동작을 시각화하면 다음과 같다.

```
Fold 1: [Train Fold 2,3,4,5] → scaler.fit_transform → model.fit
         [Val Fold 1]          → scaler.transform    → model.predict

Fold 2: [Train Fold 1,3,4,5] → scaler.fit_transform → model.fit
         [Val Fold 2]          → scaler.transform    → model.predict
...
```

각 fold의 검증 데이터는 해당 fold의 학습 데이터로만 fit된 scaler로 변환된다. 검증 데이터의 통계치가 학습에 전혀 영향을 주지 않으므로 Data Leakage가 원천 차단된다.

`StratifiedKFold`나 `RepeatedKFold` 같은 고급 분할 전략과도 자연스럽게 결합된다.

```python
from sklearn.model_selection import StratifiedKFold, cross_validate

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = cross_validate(pipe, X, y, cv=cv,
                         scoring=['accuracy', 'roc_auc'],
                         return_train_score=True)
print(f"Train AUC: {results['train_roc_auc'].mean():.4f}")
print(f"Val AUC:   {results['test_roc_auc'].mean():.4f}")
```

<!-- Execution error: NameError: name 'X' is not defined -->

---

![Pipeline 장점: Pipeline 사용 전후의 코드 복잡도와 Data Leakage 방지 효과 비교](figures/pipeline_benefit.png)
*Pipeline 장점: Pipeline을 사용하면 교차 검증 시 Data Leakage를 자동으로 방지하고, 배포 시 전처리 코드 불일치 문제를 해결한다.*

## 4. ColumnTransformer: 특성 유형별 다른 전처리

실제 데이터는 수치형(numerical)과 범주형(categorical) 특성이 섞여 있다. `ColumnTransformer`를 사용하면 열마다 다른 전처리를 병렬로 적용할 수 있다.

```python
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

# 특성 목록 정의
num_features = ['age', 'fare', 'sibsp', 'parch']
cat_features = ['sex', 'embarked', 'pclass']

# 수치형 파이프라인: 결측값 대체 → 스케일링
num_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

# 범주형 파이프라인: 결측값 대체 → 원-핫 인코딩
cat_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
])

# ColumnTransformer로 병렬 결합
preprocessor = ColumnTransformer([
    ('num', num_pipeline, num_features),
    ('cat', cat_pipeline, cat_features)
])

# 전체 파이프라인 구성
full_pipe = Pipeline([
    ('preprocessor', preprocessor),
    ('model', RandomForestClassifier(n_estimators=100, random_state=42))
])

full_pipe.fit(X_train, y_train)
print(f"Test Accuracy: {full_pipe.score(X_test, y_test):.4f}")
```

<!-- Execution error: NameError: name 'X_train' is not defined -->

`remainder` 파라미터를 사용하면 명시적으로 지정하지 않은 열을 처리하는 방법을 지정할 수 있다. `remainder='passthrough'`로 설정하면 나머지 열을 변환 없이 그대로 통과시킨다.

```python
preprocessor = ColumnTransformer([
    ('num', StandardScaler(), num_features),
    ('cat', OneHotEncoder(), cat_features)
], remainder='passthrough')  # 나머지 열은 그대로 유지
```

---

## 5. Custom Transformer 만들기

sklearn에 내장되지 않은 전처리 로직이 필요할 때는 Custom Transformer를 직접 만들 수 있다. `BaseEstimator`와 `TransformerMixin`을 상속하면 `fit`, `transform`, `fit_transform`, `get_params`, `set_params` 등의 메서드를 자동으로 얻는다.

```python
from sklearn.base import BaseEstimator, TransformerMixin
import numpy as np

class LogTransformer(BaseEstimator, TransformerMixin):
    """양수 특성에 log1p 변환을 적용하는 커스텀 트랜스포머"""

    def __init__(self, add_original=False):
        # __init__의 파라미터 이름과 어트리뷰트 이름이 반드시 일치해야 함
        self.add_original = add_original

    def fit(self, X, y=None):
        # 학습 단계: 이 트랜스포머는 학습할 파라미터가 없으므로 self만 반환
        return self

    def transform(self, X, y=None):
        X_log = np.log1p(np.abs(X))
        if self.add_original:
            # 원본 특성과 로그 변환 특성을 함께 반환
            return np.hstack([X, X_log])
        return X_log

# Custom Transformer는 Pipeline 안에서 동일하게 사용 가능
pipe = Pipeline([
    ('log', LogTransformer(add_original=True)),
    ('scaler', StandardScaler()),
    ('model', LogisticRegression())
])
```

`fit` 단계에서 학습 데이터의 통계량을 저장해야 하는 경우, 어트리뷰트 이름 끝에 언더스코어(`_`)를 붙이는 관례를 따른다.

```python
class OutlierClipper(BaseEstimator, TransformerMixin):
    """학습 데이터의 분위수 기준으로 이상치를 클리핑"""

    def __init__(self, lower_q=0.01, upper_q=0.99):
        self.lower_q = lower_q
        self.upper_q = upper_q

    def fit(self, X, y=None):
        # fit된 파라미터는 언더스코어로 구분
        self.lower_ = np.quantile(X, self.lower_q, axis=0)
        self.upper_ = np.quantile(X, self.upper_q, axis=0)
        return self

    def transform(self, X, y=None):
        return np.clip(X, self.lower_, self.upper_)
```

---

## 6. Pipeline과 GridSearchCV 결합

Pipeline의 각 단계 파라미터는 `단계이름__파라미터이름` 형식(더블 언더스코어)으로 접근할 수 있어 `GridSearchCV`와 완벽하게 연동된다.

```python
from sklearn.model_selection import GridSearchCV

# 탐색할 파라미터 그리드 정의
# 형식: {단계이름__파라미터: 값 리스트}
param_grid = {
    # 모델 하이퍼파라미터
    'model__n_estimators': [100, 200, 300],
    'model__max_depth': [None, 5, 10],
    # 전처리 파라미터 (ColumnTransformer 내부 접근)
    'preprocessor__num__imputer__strategy': ['mean', 'median'],
    'preprocessor__cat__encoder__handle_unknown': ['ignore', 'infrequent_if_exist']
}

grid_search = GridSearchCV(
    full_pipe,
    param_grid,
    cv=5,
    scoring='roc_auc',
    n_jobs=-1,
    verbose=1
)

grid_search.fit(X_train, y_train)

print(f"최적 파라미터: {grid_search.best_params_}")
print(f"최적 CV AUC:  {grid_search.best_score_:.4f}")
print(f"Test AUC:    {grid_search.score(X_test, y_test):.4f}")

# 최적 파이프라인 추출
best_pipe = grid_search.best_estimator_
```

<!-- Execution error: NameError: name 'X_train' is not defined -->

`RandomizedSearchCV`와도 동일한 방식으로 결합되며, 대규모 탐색 공간에서 효율적인 하이퍼파라미터 최적화가 가능하다.

---

## 7. FunctionTransformer: 간단한 함수를 Transformer로

한두 줄짜리 단순 변환은 클래스 전체를 작성하는 대신 `FunctionTransformer`로 빠르게 Pipeline에 통합할 수 있다.

```python
from sklearn.preprocessing import FunctionTransformer
import numpy as np

# numpy 함수를 그대로 Transformer로 변환
log_transformer = FunctionTransformer(np.log1p, validate=True)

# 람다 함수도 사용 가능 (단, joblib 직렬화 시 문제가 생길 수 있으므로 주의)
def clip_outliers(X, lower=-3, upper=3):
    return np.clip(X, lower, upper)

clip_transformer = FunctionTransformer(
    clip_outliers,
    kw_args={'lower': -2.5, 'upper': 2.5},
    validate=True
)

pipe = Pipeline([
    ('log', log_transformer),
    ('clip', clip_transformer),
    ('scaler', StandardScaler()),
    ('model', LogisticRegression())
])
```

`validate=True`를 설정하면 입력이 2D 배열인지 자동으로 검증한다. 복잡한 로직이나 `fit` 단계에서 학습이 필요한 경우에는 반드시 Custom Transformer 클래스를 작성해야 한다.

---

## 8. Pipeline 저장과 로드

학습 완료된 Pipeline을 `joblib` 또는 `pickle`로 직렬화하면 전처리 파라미터와 모델 가중치가 하나의 파일에 함께 저장된다. 배포 서버에서 이 파일을 로드하면 학습 환경과 동일한 전처리가 자동으로 보장된다.

```python
import joblib

# 저장 - 전처리 파라미터 + 모델 가중치가 하나의 파일에
joblib.dump(full_pipe, 'titanic_pipeline.joblib')

# 로드 - 배포 서버 또는 다른 환경에서
loaded_pipe = joblib.load('titanic_pipeline.joblib')

# 로드 후 바로 예측 가능 (별도 전처리 불필요)
new_data = pd.DataFrame([{
    'age': 29, 'fare': 7.25, 'sibsp': 0, 'parch': 0,
    'sex': 'male', 'embarked': 'S', 'pclass': 3
}])
prediction = loaded_pipe.predict(new_data)
proba = loaded_pipe.predict_proba(new_data)
print(f"생존 예측: {prediction[0]}, 생존 확률: {proba[0][1]:.4f}")
```

<!-- Execution error: NotFittedError: This Pipeline instance is not fitted yet. Call 'fit' with appropriate arguments before using this estimator. -->

`joblib`은 NumPy 배열을 포함하는 대형 객체를 `pickle`보다 훨씬 빠르고 메모리 효율적으로 직렬화한다. 프로덕션 환경에서는 `pickle` 대신 `joblib`을 권장한다.

> 주의: 저장·로드 환경의 Python 버전과 sklearn 버전이 일치해야 한다. 버전 관리를 위해 `model_version`을 파일명에 포함하거나 MLflow 같은 모델 레지스트리를 함께 사용하는 것이 좋다.

---

## 9. 실전 완전 예시: 타이타닉 데이터로 전체 파이프라인 구축

지금까지 배운 내용을 타이타닉 생존 예측 문제에 통합해 완전한 ML 파이프라인을 구축한다.

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import classification_report
import joblib

# ── 1. 데이터 로드 ──────────────────────────────────────────
df = pd.read_csv('titanic.csv')
X = df[['age', 'fare', 'sibsp', 'parch', 'sex', 'embarked', 'pclass']]
y = df['survived']
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# ── 2. Custom Transformer: 가족 크기 특성 생성 ────────────
class FamilySizeAdder(BaseEstimator, TransformerMixin):
    """sibsp + parch + 1 = 가족 크기 파생 특성 추가"""
    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X = X.copy()
        X['family_size'] = X['sibsp'] + X['parch'] + 1
        X['is_alone'] = (X['family_size'] == 1).astype(int)
        return X

# ── 3. 특성 정의 (파생 특성 포함) ────────────────────────────
num_features = ['age', 'fare', 'sibsp', 'parch', 'family_size']
cat_features = ['sex', 'embarked', 'pclass', 'is_alone']

# ── 4. 수치형/범주형 서브 파이프라인 ─────────────────────────
num_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

cat_pipe = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
])

preprocessor = ColumnTransformer([
    ('num', num_pipe, num_features),
    ('cat', cat_pipe, cat_features)
])

# ── 5. 전체 파이프라인 조립 ──────────────────────────────────
full_pipe = Pipeline([
    ('feature_engineering', FamilySizeAdder()),
    ('preprocessor', preprocessor),
    ('model', GradientBoostingClassifier(random_state=42))
])

# ── 6. 교차 검증으로 성능 추정 (Data Leakage 없음) ────────────
cv_scores = cross_val_score(full_pipe, X_train, y_train, cv=5, scoring='roc_auc')
print(f"CV AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

# ── 7. GridSearchCV로 하이퍼파라미터 최적화 ──────────────────
param_grid = {
    'model__n_estimators': [100, 200],
    'model__learning_rate': [0.05, 0.1],
    'model__max_depth': [3, 5],
    'preprocessor__num__imputer__strategy': ['mean', 'median']
}

grid_search = GridSearchCV(
    full_pipe, param_grid, cv=5,
    scoring='roc_auc', n_jobs=-1, verbose=1
)
grid_search.fit(X_train, y_train)

print(f"\n최적 파라미터: {grid_search.best_params_}")
print(f"최적 CV AUC:  {grid_search.best_score_:.4f}")

# ── 8. 최종 평가 ─────────────────────────────────────────────
best_pipe = grid_search.best_estimator_
y_pred = best_pipe.predict(X_test)
print("\n분류 리포트:")
print(classification_report(y_test, y_pred, target_names=['사망', '생존']))

# ── 9. 파이프라인 저장 ────────────────────────────────────────
joblib.dump(best_pipe, 'titanic_best_pipeline.joblib')
print("\n파이프라인 저장 완료: titanic_best_pipeline.joblib")

# ── 10. 로드 후 새 데이터 예측 ───────────────────────────────
loaded_pipe = joblib.load('titanic_best_pipeline.joblib')
new_passenger = pd.DataFrame([{
    'age': 25, 'fare': 30.0, 'sibsp': 1, 'parch': 0,
    'sex': 'female', 'embarked': 'C', 'pclass': 2
}])
proba = loaded_pipe.predict_proba(new_passenger)[0]
print(f"\n새 승객 생존 확률: {proba[1]:.4f}")
```

<!-- Execution error: FileNotFoundError: [Errno 2] No such file or directory: 'titanic.csv' -->

---

## 마무리

sklearn Pipeline은 단순한 편의 도구가 아니라 **재현 가능한 ML 시스템의 기반**이다. 전처리와 모델을 하나의 객체로 묶음으로써 Data Leakage를 방지하고, 배포 코드를 단순화하며, 하이퍼파라미터 탐색의 범위를 전처리까지 확장한다. ColumnTransformer로 이기종 특성을, Custom Transformer로 도메인 특화 로직을, FunctionTransformer로 빠른 함수 통합을 수행하는 패턴을 익혀두면 어떤 실전 프로젝트에도 견고한 ML 파이프라인을 구축할 수 있다.