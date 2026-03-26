## 개요

AutoML(Automated Machine Learning)은 머신러닝 파이프라인에서 인간의 반복적 개입을 최소화하고, 모델 개발 과정을 자동화하는 기술 분야입니다. 전통적인 ML 워크플로에서 데이터 과학자는 수많은 실험을 수작업으로 반복해야 했습니다. AutoML은 이 과정을 체계적으로 자동화합니다.

AutoML이 자동화하는 핵심 영역은 세 가지입니다.

- **하이퍼파라미터 최적화(HPO, Hyperparameter Optimization)**: 학습률, 트리 깊이, 정규화 강도 등 모델 성능에 결정적인 파라미터를 자동으로 탐색합니다.
- **모델 선택(Model Selection)**: 주어진 데이터와 문제 유형에 맞는 최적의 알고리즘을 자동으로 비교·선정합니다.
- **특성 공학(Feature Engineering)**: 원본 피처에서 유용한 파생 변수를 자동 생성하거나 불필요한 피처를 제거합니다.

AutoML은 ML 전문 지식이 부족한 도메인 전문가도 고품질 모델을 구축할 수 있도록 돕고, 숙련된 데이터 과학자에게는 탐색 시간을 대폭 단축시켜 줍니다.

---

## 수학적 배경

### 하이퍼파라미터 최적화(HPO)

HPO의 목표는 검증 손실을 최소화하는 하이퍼파라미터 벡터 $\lambda^*$를 찾는 것입니다.

$$\lambda^* = \arg\min_{\lambda \in \Lambda} \mathcal{L}(\mathcal{A}_{\lambda}, \mathcal{D}_{\text{train}}, \mathcal{D}_{\text{val}})$$

여기서 $\mathcal{A}_{\lambda}$는 하이퍼파라미터 $\lambda$로 설정된 학습 알고리즘, $\mathcal{D}_{\text{train}}$과 $\mathcal{D}_{\text{val}}$은 각각 훈련·검증 데이터셋입니다.

### 베이지안 최적화(Bayesian Optimization)

단순 그리드/랜덤 탐색과 달리, 베이지안 최적화는 **대리 모델(surrogate model)**을 통해 이전 평가 결과를 활용해 다음 탐색 지점을 지능적으로 선택합니다.

1. **대리 모델**: 목적 함수 $f(\lambda)$를 가우시안 프로세스(GP)로 근사합니다.

   $$f(\lambda) \sim \mathcal{GP}(\mu(\lambda),\ k(\lambda, \lambda'))$$

2. **획득 함수(Acquisition Function)**: 다음 후보 $\lambda$를 선택하기 위해 기대 향상도(EI, Expected Improvement)를 최대화합니다.

   $$\text{EI}(\lambda) = \mathbb{E}\left[\max(f(\lambda) - f(\lambda^+),\ 0)\right]$$

   $f(\lambda^+)$는 현재까지의 최선 관측값입니다.

### TPE(Tree-structured Parzen Estimator)

Optuna 등에서 사용하는 TPE는 GP 대신 두 개의 밀도 모델 $l(\lambda)$, $g(\lambda)$를 추정합니다.

$$\text{EI}(\lambda) \propto \frac{l(\lambda)}{g(\lambda)}$$

- $l(\lambda)$: 성능이 좋았던 관측값들의 밀도
- $g(\lambda)$: 성능이 나빴던 관측값들의 밀도

이 비율이 높은 지점을 다음 탐색 후보로 선택합니다.

### NAS(Neural Architecture Search)

NAS는 신경망 구조 자체를 탐색 공간 $\mathcal{A}$로 정의하고, 검증 성능을 최대화하는 아키텍처 $a^*$를 찾습니다.

$$a^* = \arg\max_{a \in \mathcal{A}}\ \text{val\_acc}(a)$$

탐색 전략에 따라 **Random Search**, **Evolutionary Algorithm**, **Gradient-based(DARTS)** 방법이 존재합니다.

---

![탐색 공간: 하이퍼파라미터 탐색 공간에서 Grid, Random, Bayesian 탐색 전략 비교](figures/search_space.png)
*탐색 공간: Grid Search는 균일하게, Random Search는 무작위로, Bayesian Optimization은 이전 결과를 활용하여 효율적으로 탐색한다.*

## 주요 알고리즘과 라이브러리

### HPO 라이브러리

| 라이브러리 | 핵심 알고리즘 | 특징 |
|---|---|---|
| **SMAC** | 랜덤 포레스트 기반 베이지안 최적화 | 범주형 파라미터에 강점 |
| **Hyperopt** | TPE | 분산 탐색 지원 |
| **Optuna** | TPE + CMA-ES | 직관적 API, 동적 탐색 공간, 가지치기 지원 |

### Full-Pipeline AutoML

- **Auto-sklearn**: scikit-learn 알고리즘 전체를 대상으로 SMAC 기반 탐색. 앙상블 자동 구성 포함.
- **H2O AutoML**: 대용량 데이터에 강하며 AutoML 리더보드를 제공. XGBoost, GBM, 딥러닝, 스태킹 앙상블 자동 실행.
- **FLAML**: Microsoft에서 개발. 계산 자원이 제한된 환경에서 빠른 탐색을 위해 최적화됨.
- **Google AutoML**: Cloud 기반으로 이미지·텍스트·표 데이터에 대한 완전 관리형 AutoML 서비스.

### NAS 방법론

- **Random NAS**: 무작위 아키텍처 샘플링. 간단하지만 강력한 베이스라인.
- **Evolutionary NAS**: 유전 알고리즘으로 아키텍처를 교배·돌연변이하며 진화. EfficientNet 탐색에 사용.
- **Gradient-based NAS (DARTS)**: 이산적 구조 선택을 연속적 혼합 가중치로 완화하여 그래디언트로 최적화.

  $$\bar{o}^{(i,j)}(x) = \sum_{o \in \mathcal{O}} \frac{\exp(\alpha_o^{(i,j)})}{\sum_{o'} \exp(\alpha_{o'}^{(i,j)})} \cdot o(x)$$

---

## Python 구현

### Optuna + XGBoost 하이퍼파라미터 최적화

```python
import optuna
import xgboost as xgb
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import numpy as np

# 데이터 준비
X, y = load_breast_cancer(return_X_y=True)

def objective(trial):
    """Optuna 목적 함수: 하이퍼파라미터를 샘플링하고 CV 점수를 반환"""
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 50, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 1e-3, 0.3, log=True),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 1.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 1.0, log=True),
        "eval_metric": "logloss",
        "use_label_encoder": False,
        "random_state": 42,
    }
    model = xgb.XGBClassifier(**params)
    # 5-fold CV ROC-AUC 평균을 최대화
    score = cross_val_score(model, X, y, cv=5, scoring="roc_auc").mean()
    return score

# 탐색 실행 (100회 시도, TPE 샘플러)
study = optuna.create_study(
    direction="maximize",
    sampler=optuna.samplers.TPESampler(seed=42),
    pruner=optuna.pruners.MedianPruner(n_startup_trials=10)
)
study.optimize(objective, n_trials=100, show_progress_bar=True)

print(f"Best AUC: {study.best_value:.4f}")
print(f"Best params: {study.best_params}")

# 최적 파라미터로 최종 모델 훈련
best_model = xgb.XGBClassifier(**study.best_params, random_state=42)
best_model.fit(X, y)
```

```output
<!-- Pre-computed result needed -->
```

### Auto-sklearn 간단 예제

```python
import autosklearn.classification
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

X, y = load_breast_cancer(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Auto-sklearn: 5분 탐색, 메모리 3GB 제한
automl = autosklearn.classification.AutoSklearnClassifier(
    time_left_for_this_task=300,   # 총 탐색 시간 (초)
    per_run_time_limit=30,          # 단일 모델 평가 제한 (초)
    memory_limit=3072,              # 메모리 제한 (MB)
    ensemble_size=20,               # 앙상블 구성 모델 수
    seed=42
)
automl.fit(X_train, y_train)

y_pred_proba = automl.predict_proba(X_test)[:, 1]
print(f"Auto-sklearn AUC: {roc_auc_score(y_test, y_pred_proba):.4f}")

# 선택된 모델 앙상블 확인
print(automl.leaderboard())
```

```output
<!-- Pre-computed result needed -->
```

---

![베이지안 최적화: 대리 모델과 획득 함수를 활용한 반복적 탐색 과정 시각화](figures/bayesian_optimization.png)
*베이지안 최적화: 가우시안 프로세스 대리 모델이 목적 함수를 근사하고, 획득 함수가 탐색과 활용의 균형을 맞추며 최적점을 찾아간다.*

## 시각화

### HPO 탐색 과정 시각화

Optuna는 탐색 히스토리와 파라미터 중요도를 바로 시각화할 수 있는 API를 제공합니다.

```python
import optuna.visualization as vis
import plotly.io as pio

# 1. 최적화 히스토리 플롯: 시도 횟수에 따른 목적 함수 변화
fig_history = vis.plot_optimization_history(study)
fig_history.update_layout(title="HPO 최적화 히스토리 (Optuna TPE)")
fig_history.show()

# 2. 파라미터 중요도 플롯: 각 하이퍼파라미터가 성능에 미치는 영향
fig_importance = vis.plot_param_importances(study)
fig_importance.update_layout(title="하이퍼파라미터 중요도")
fig_importance.show()

# 3. 등고선 플롯: 두 파라미터 간 상호작용 시각화
fig_contour = vis.plot_contour(
    study,
    params=["learning_rate", "max_depth"]
)
fig_contour.show()

# 4. 슬라이스 플롯: 각 파라미터 값에 따른 목적 함수 분포
fig_slice = vis.plot_slice(study)
fig_slice.show()
```

**시각화 해석 가이드**

- **최적화 히스토리**: 초반에는 랜덤 탐색과 유사하게 분산이 크지만, 시도 횟수가 늘어날수록 TPE가 좋은 영역에 집중하며 점차 수렴합니다.
- **파라미터 중요도**: Fanova 기반으로 계산되며, 중요도가 높은 파라미터에 탐색 공간을 집중하는 전략에 활용합니다.
- **등고선 플롯**: 두 파라미터 사이의 상호작용(interaction)을 파악해 탐색 공간 재설계에 참고합니다.

---

## 실전 팁

### AutoML의 한계

AutoML이 만능은 아닙니다. 다음 상황에서는 수동 접근이 더 효과적일 수 있습니다.

1. **도메인 지식이 핵심인 경우**: 의료·금융 등 도메인 특화 피처 공학이 모델 성능을 크게 좌우할 때.
2. **데이터가 극히 작을 때**: AutoML의 교차검증 기반 평가 자체가 신뢰할 수 없을 정도로 샘플이 부족한 경우.
3. **해석 가능성이 최우선인 경우**: AutoML이 선택한 복잡한 앙상블은 해석이 어렵습니다. 규제 환경(의료·금융)에서는 단순 모델이 요구될 수 있습니다.
4. **실시간 추론 지연 요구사항이 엄격한 경우**: 탐색 결과 모델이 프로덕션 지연 요건을 충족하지 못할 수 있습니다.

### 탐색 공간 설계

효과적인 HPO를 위해 탐색 공간을 과도하게 넓게 설정하면 계산 낭비가 발생합니다.

```python
# 비추천: 지나치게 넓은 범위
trial.suggest_float("learning_rate", 1e-10, 10.0)

# 추천: 도메인 지식 기반 합리적 범위
trial.suggest_float("learning_rate", 1e-3, 0.3, log=True)  # 로그 스케일 사용
```

- **로그 스케일**: 학습률, 정규화 강도처럼 크기 차이가 큰 파라미터는 `log=True`로 설정.
- **조건부 탐색 공간**: 특정 알고리즘에서만 의미 있는 파라미터는 조건부로 정의.
- **범주형 파라미터**: `suggest_categorical`로 알고리즘 종류 선택.

### 계산 예산 관리

- **조기 종료(Pruning)**: Optuna의 `MedianPruner`나 `HyperbandPruner`로 성능이 낮은 시도를 중간에 중단.
- **병렬 탐색**: `n_jobs=-1` 또는 분산 스터디(`RDBStorage`)로 여러 CPU/GPU에서 동시 탐색.
- **Warm Starting**: 이전 탐색 결과를 초기 시드로 활용해 탐색 효율 향상.
- **예산 할당 원칙**: 전체 계산 예산의 20% 를 탐색에, 80%는 최종 모델 훈련에 배정하는 것이 일반적.

### 결과 해석과 재현성

```python
# 탐색 결과 저장 및 재현
import joblib

# 스터디 저장 (SQLite 사용)
storage = optuna.storages.RDBStorage("sqlite:///study.db")
study = optuna.create_study(
    study_name="xgb_automl",
    storage=storage,
    load_if_exists=True  # 기존 탐색 이어서 진행
)

# 최적 파라미터를 JSON으로 저장
import json
with open("best_params.json", "w") as f:
    json.dump(study.best_params, f, indent=2, ensure_ascii=False)
```

- **시드 고정**: 재현성을 위해 `TPESampler(seed=42)` 필수.
- **실험 추적**: MLflow나 Weights & Biases와 연동해 모든 시도를 기록.
- **통계적 유의성**: 베스트 파라미터와 기본값 사이의 성능 차이를 paired t-test로 검증.

---

## 정리

AutoML은 반복적인 실험 과정을 자동화해 개발 효율을 높여주지만, 도구를 효과적으로 활용하려면 내부 알고리즘에 대한 이해가 필수적입니다. 베이지안 최적화와 TPE의 원리를 파악하고, 탐색 공간을 합리적으로 설계하며, 계산 예산을 전략적으로 배분해야 합니다. AutoML은 데이터 과학자를 대체하는 것이 아니라, 반복 작업을 위임받아 더 창의적이고 고차원적인 의사결정에 집중할 수 있게 해주는 협력 도구입니다.