## 1. 개요: 왜 이 3가지가 실전을 지배하는가

머신러닝 실전 경쟁에서 XGBoost, LightGBM, CatBoost는 오랫동안 최강자 자리를 지켜왔다. 캐글(Kaggle) 우승 솔루션의 절반 이상이 이 세 알고리즘 중 하나 혹은 앙상블 조합을 사용한다는 통계도 있을 만큼, 정형 데이터(tabular data) 분야에서는 딥러닝조차 이들을 쉽게 넘어서지 못한다.

이 세 알고리즘의 공통 뿌리는 **그래디언트 부스팅(Gradient Boosting)**이다. 약한 학습기(weak learner)인 결정 트리를 순차적으로 쌓되, 이전 트리가 틀린 잔차(residual)를 다음 트리가 보정하는 방식이다. 그러나 같은 원리를 구현하는 방식에서 세 라이브러리는 완전히 다른 철학을 선택했다.

- **XGBoost**: 수학적 엄밀성과 정규화에 집중, 2016년 출시 이후 사실상 표준이 됨
- **LightGBM**: Microsoft가 개발, 속도와 메모리 효율을 극한까지 끌어올린 실용주의적 접근
- **CatBoost**: Yandex가 개발, 범주형(categorical) 특성 처리와 데이터 누수(leakage) 방지에 초점

각각의 핵심 철학을 이해하면 문제 유형에 따라 최적의 도구를 선택할 수 있다.

---

## 2. XGBoost: 수학적 정밀함으로 일군 혁명

### 2차 테일러 전개 근사

XGBoost의 가장 중요한 혁신은 손실 함수를 **2차 테일러 전개(Second-order Taylor Expansion)**로 근사한다는 점이다. 기존 그래디언트 부스팅이 1차 미분(그래디언트)만 사용하는 것과 달리, XGBoost는 2차 미분(헤시안)까지 활용한다.

$t$번째 트리를 학습할 때의 목적 함수는 다음과 같이 근사된다:

$$\mathcal{L}^{(t)} \approx \sum_{i=1}^{n} \left[ g_i f_t(x_i) + \frac{1}{2} h_i f_t^2(x_i) \right] + \Omega(f_t)$$

여기서 $g_i = \partial_{\hat{y}^{(t-1)}} l(y_i, \hat{y}^{(t-1)})$는 1차 그래디언트, $h_i = \partial^2_{\hat{y}^{(t-1)}} l(y_i, \hat{y}^{(t-1)})$는 2차 헤시안이다. 2차 정보를 사용하면 손실 함수의 곡률(curvature)을 반영하므로 수렴 속도가 빠르고, 다양한 손실 함수에 일반화하기 쉽다.

### 정규화 항

XGBoost는 트리의 복잡도를 직접 목적 함수에 포함시킨다. 정규화 항 $\Omega$는 다음과 같다:

$$\Omega(f) = \gamma T + \frac{1}{2} \lambda \sum_{j=1}^{T} w_j^2$$

- $T$: 트리의 리프 노드 수
- $w_j$: 각 리프 노드의 예측값(가중치)
- $\gamma$: 리프 노드를 추가할 때 최소한으로 필요한 손실 감소량 (리프 수 페널티)
- $\lambda$: L2 정규화 계수 (가중치 크기 페널티)

이 구조 덕분에 XGBoost는 과적합을 목적 함수 수준에서 원천 억제한다. 최적 리프 가중치는 목적 함수를 $w_j$에 대해 미분하면 닫힌 형태로 구할 수 있다:

$$w_j^* = -\frac{\sum_{i \in I_j} g_i}{\sum_{i \in I_j} h_i + \lambda}$$

그리고 분기(split) 점수는 다음 공식으로 평가한다:

$$\text{Gain} = \frac{1}{2} \left[ \frac{G_L^2}{H_L + \lambda} + \frac{G_R^2}{H_R + \lambda} - \frac{(G_L + G_R)^2}{H_L + H_R + \lambda} \right] - \gamma$$

Gain이 0보다 작으면 해당 분기는 수행하지 않는다. 이 조건이 곧 $\gamma$의 역할이다.

### 열 병렬화와 Sparsity 처리

XGBoost는 **Column Subsampling(colsample_bytree)**을 지원하여 트리마다 사용할 특성을 랜덤하게 선택한다. 이는 랜덤 포레스트와 유사한 다양성 증가 효과를 낸다. 또한 결측값이나 희소한(sparse) 특성을 처리하기 위해 기본 방향(default direction)을 자동 학습하여, 별도의 결측값 처리 없이도 안정적으로 동작한다.

### 주요 하이퍼파라미터

| 파라미터 | 역할 | 권장 범위 |
|----------|------|----------|
| `max_depth` | 트리 최대 깊이 | 3~10 |
| `learning_rate` | 학습률 (shrinkage) | 0.01~0.3 |
| `n_estimators` | 트리 개수 | 100~1000+ |
| `subsample` | 행 샘플링 비율 | 0.5~1.0 |
| `colsample_bytree` | 열(특성) 샘플링 비율 | 0.5~1.0 |
| `reg_alpha` | L1 정규화 계수 | 0~1 |
| `reg_lambda` | L2 정규화 계수 | 0~10 |
| `gamma` | 분기 최소 손실 감소량 | 0~5 |

---

![트리 성장 전략: Level-wise vs Leaf-wise 성장 방식의 구조적 차이](figures/tree_growth_strategy.png)
*트리 성장 전략: Level-wise는 같은 깊이의 모든 노드를 동시에 분기하고, Leaf-wise는 손실 감소가 가장 큰 리프를 우선 분기하여 더 효율적인 학습을 달성한다.*

## 3. LightGBM: 속도와 효율의 혁신

Microsoft가 2017년 공개한 LightGBM은 XGBoost보다 최대 20배 빠른 학습 속도와 더 낮은 메모리 사용량을 달성하였다. 핵심은 두 가지 알고리즘 혁신에 있다.

### GOSS: Gradient-based One-Side Sampling

그래디언트 부스팅에서 그래디언트가 큰 샘플은 현재 모델이 틀린 핵심 사례들이다. 반면 그래디언트가 작은 샘플은 이미 잘 학습된 사례이며, 정보 기여도가 낮다.

**GOSS**는 이 점에 착안한다:
1. 절대 그래디언트가 상위 $a \times 100\%$인 샘플은 **전부 유지**한다.
2. 나머지 $(1-a) \times 100\%$ 중에서 무작위로 $b \times 100\%$만 **샘플링**한다.
3. 샘플링된 작은 그래디언트 샘플에는 $\frac{1-a}{b}$ 가중치를 곱해 분포를 보정한다.

이 방식으로 데이터 크기를 크게 줄이면서도 중요한 정보는 손실 없이 보존한다. 분기 이득 추정 오차가 $\mathcal{O}(\frac{1}{n^{2/3}})$ 수준으로 수렴함이 이론적으로 보장된다.

### EFB: Exclusive Feature Bundling

실제 데이터에서 원-핫 인코딩(one-hot encoding)을 적용하면 특성 차원이 폭발적으로 늘어난다. 그런데 이런 희소 특성들은 서로 **동시에 0이 아닌 값을 갖지 않는** 경우가 많다(상호 배타적).

**EFB**는 상호 배타적인 특성들을 하나의 번들로 묶어 차원 수를 줄인다:
1. 두 특성이 동시에 0이 아닌 비율(충돌률)을 계산한다.
2. 충돌률이 일정 임계값 $\epsilon$ 이하인 특성들을 그래프의 노드로 표현하고, 그래프 색칠 문제(graph coloring)로 최소 번들 수를 구한다.
3. 번들 내 특성들은 값 범위를 이동(offset)하여 단일 특성으로 합친다.

이를 통해 특성 수가 수천 개에서 수백 개로 줄어들어 분기 탐색 속도가 대폭 향상된다.

### Leaf-wise 성장 vs Level-wise 성장

기존 결정 트리 라이브러리 대부분은 **Level-wise(너비 우선)** 방식으로 트리를 성장시킨다. 같은 깊이의 모든 노드를 동시에 분기한다.

LightGBM은 **Leaf-wise(최선 우선)** 방식을 채택한다. 손실 감소가 가장 큰 리프 노드를 우선적으로 분기한다. 같은 수의 분기로 더 낮은 손실을 달성할 수 있어 효율적이다. 단, 데이터가 적을 때는 과적합 위험이 있으므로 `num_leaves`와 `min_child_samples` 파라미터로 제어해야 한다.

### LightGBM 주요 파라미터

| 파라미터 | 역할 | 권장 범위 |
|----------|------|----------|
| `num_leaves` | 최대 리프 수 (복잡도 제어) | 31~255 |
| `learning_rate` | 학습률 | 0.01~0.1 |
| `n_estimators` | 트리 개수 | 100~2000 |
| `min_child_samples` | 리프 최소 샘플 수 | 20~100 |
| `feature_fraction` | 특성 샘플링 비율 | 0.5~1.0 |
| `bagging_fraction` | 행 샘플링 비율 | 0.5~1.0 |
| `reg_alpha` | L1 정규화 | 0~1 |
| `reg_lambda` | L2 정규화 | 0~10 |

---

## 4. CatBoost: 범주형 데이터의 왕

Yandex가 2017년 출시한 CatBoost는 범주형(categorical) 특성이 많은 실무 데이터셋에서 강점을 보인다. 두 가지 핵심 혁신이 있다.

### Ordered Boosting: 데이터 누수 방지

일반적인 그래디언트 부스팅은 같은 학습 데이터로 잔차를 계산하고 트리를 학습한다. 이 과정에서 **타겟 통계(target statistics)**를 이용하면 학습 데이터 자신의 타겟 정보가 모델 학습에 누수(leakage)될 수 있다.

**Ordered Boosting**은 이를 방지한다:
1. 학습 데이터를 시간적 순서 또는 무작위 순열로 정렬한다.
2. $i$번째 샘플의 잔차를 계산할 때, **$i$번째보다 앞에 있는 데이터만** 사용한 모델로 예측한다.
3. 즉, 샘플 $x_i$는 자기 자신을 학습에 사용하지 않은 모델로 평가된다.

이는 교차 검증과 유사한 방식으로 편향을 줄이며, 특히 소규모 데이터셋에서 일반화 성능이 크게 향상된다.

### 범주형 특성 자동 처리: Target Statistics

범주형 특성을 수치로 변환하는 CatBoost의 방식은 **Ordered Target Statistics(OTS)**다:

$$\hat{x}_i^k = \frac{\sum_{j < i} [x_j^k = x_i^k] \cdot y_j + \alpha \cdot P}{\sum_{j < i} [x_j^k = x_i^k] + \alpha}$$

여기서 $P$는 전체 타겟의 평균, $\alpha$는 평활화(smoothing) 계수다. 순서 기반으로 이전 샘플들의 정보만 사용하므로 데이터 누수 없이 범주형 특성을 타겟과 연관 지어 인코딩한다. 별도 전처리(Label Encoding, One-Hot Encoding) 없이 원시 범주형 열을 그대로 입력할 수 있다.

### 대칭 트리(Symmetric Trees)

CatBoost는 **대칭 트리(Oblivious Decision Tree)** 구조를 사용한다. 같은 깊이의 모든 노드가 동일한 특성과 분기점을 사용한다. 이 구조는 더 단순하여 과적합에 강하고, 예측 시 룩업 테이블(lookup table)로 구현 가능해 추론 속도가 빠르다. 다만 XGBoost, LightGBM 대비 표현력이 일부 제한된다.

---

![부스팅 프레임워크 비교: XGBoost, LightGBM, CatBoost의 핵심 특성 비교](figures/framework_comparison.png)
*부스팅 프레임워크 비교: XGBoost, LightGBM, CatBoost 세 프레임워크의 학습 속도, 메모리 효율, 범주형 처리 등 핵심 특성을 비교한다.*

## 5. 3대장 비교 표

| 항목 | XGBoost | LightGBM | CatBoost |
|------|---------|----------|----------|
| 출시 연도 | 2016 | 2017 | 2017 |
| 개발사 | DMLC | Microsoft | Yandex |
| 학습 속도 | 중간 | 빠름 | 느림 |
| 메모리 사용량 | 많음 | 적음 | 중간 |
| 범주형 특성 처리 | 수동 인코딩 필요 | 내장 지원 | 자동 처리 (최강) |
| 결측값 처리 | 자동 | 자동 | 자동 |
| 트리 성장 방식 | Level-wise | Leaf-wise | 대칭 트리 |
| 데이터 누수 방지 | 없음 | 없음 | Ordered Boosting |
| 소규모 데이터 | 양호 | 과적합 주의 | 우수 |
| 대규모 데이터 | 양호 | 우수 | 양호 |
| 적합 상황 | 범용, 첫 번째 선택 | 대용량, 속도 중시 | 범주형 많을 때 |

---

## 6. 하이퍼파라미터 튜닝 가이드

세 모델 모두 하이퍼파라미터 민감도가 높으므로 체계적인 튜닝이 중요하다.

**공통 원칙**
1. **학습률(learning_rate)은 작게, 트리 수(n_estimators)는 크게**: `learning_rate=0.05`로 고정 후 Early Stopping으로 최적 트리 수를 탐색하는 것이 일반적이다.
2. **Early Stopping 활용**: 검증 세트 성능이 개선되지 않으면 조기 종료하여 과적합을 방지한다. `early_stopping_rounds=50` 정도가 무난하다.
3. **정규화 우선 탐색**: `max_depth`(XGBoost/CatBoost) 또는 `num_leaves`(LightGBM)를 먼저 조정해 과적합 여부를 확인한 후, 세밀한 파라미터를 탐색한다.

**XGBoost 튜닝 순서**
- Step 1: `max_depth` (3→10), `min_child_weight` (1→10) ( 트리 복잡도 제어
- Step 2: `subsample` (0.5→1.0), `colsample_bytree` (0.5→1.0) ) 샘플링으로 다양성 확보
- Step 3: `gamma`, `reg_alpha`, `reg_lambda` ( 정규화 미세 조정
- Step 4: `learning_rate` 낮추고 `n_estimators` 재탐색

**LightGBM 튜닝 순서**
- Step 1: `num_leaves` (31→255) ) Leaf-wise 복잡도 핵심
- Step 2: `min_child_samples` ( 소규모 리프 방지 (과적합 억제)
- Step 3: `feature_fraction`, `bagging_fraction` ) 다양성 확보
- Step 4: `reg_alpha`, `reg_lambda` ( 정규화

**CatBoost 튜닝 순서**
- Step 1: `depth` (4→10), `l2_leaf_reg` ) 트리 복잡도
- Step 2: `border_count` ( 수치형 특성 분기 후보 수
- Step 3: `random_strength`, `bagging_temperature` ) 과적합 방지 노이즈

**도구 추천**: Optuna를 이용한 베이지안 최적화(Bayesian Optimization)가 그리드 서치보다 효율적이다.

---

## 7. Python 코드: 3가지 모델 비교 실험

```python
import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import roc_auc_score, accuracy_score
import time

import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier

# ────────────────────────────────────────
# 1. 데이터 준비
# ────────────────────────────────────────
np.random.seed(42)
X, y = make_classification(
    n_samples=100_000,
    n_features=50,
    n_informative=20,
    n_redundant=10,
    random_state=42
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
X_tr, X_val, y_tr, y_val = train_test_split(
    X_train, y_train, test_size=0.2, random_state=42
)

results = {}

# ────────────────────────────────────────
# 2. XGBoost
# ────────────────────────────────────────
xgb_model = xgb.XGBClassifier(
    n_estimators=1000,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    gamma=0.0,
    use_label_encoder=False,
    eval_metric='logloss',
    random_state=42,
    n_jobs=-1
)

start = time.time()
xgb_model.fit(
    X_tr, y_tr,
    eval_set=[(X_val, y_val)],
    early_stopping_rounds=50,
    verbose=False
)
xgb_time = time.time() - start

xgb_pred = xgb_model.predict_proba(X_test)[:, 1]
results['XGBoost'] = {
    'AUC': roc_auc_score(y_test, xgb_pred),
    'Accuracy': accuracy_score(y_test, xgb_model.predict(X_test)),
    'Time(s)': round(xgb_time, 2),
    'Best Iter': xgb_model.best_iteration
}

# ────────────────────────────────────────
# 3. LightGBM
# ────────────────────────────────────────
lgb_model = lgb.LGBMClassifier(
    n_estimators=1000,
    num_leaves=63,
    learning_rate=0.05,
    feature_fraction=0.8,
    bagging_fraction=0.8,
    bagging_freq=5,
    min_child_samples=20,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42,
    n_jobs=-1
)

start = time.time()
callbacks = [lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)]
lgb_model.fit(
    X_tr, y_tr,
    eval_set=[(X_val, y_val)],
    callbacks=callbacks
)
lgb_time = time.time() - start

lgb_pred = lgb_model.predict_proba(X_test)[:, 1]
results['LightGBM'] = {
    'AUC': roc_auc_score(y_test, lgb_pred),
    'Accuracy': accuracy_score(y_test, lgb_model.predict(X_test)),
    'Time(s)': round(lgb_time, 2),
    'Best Iter': lgb_model.best_iteration_
}

# ────────────────────────────────────────
# 4. CatBoost
# ────────────────────────────────────────
cat_model = CatBoostClassifier(
    iterations=1000,
    depth=6,
    learning_rate=0.05,
    l2_leaf_reg=3.0,
    random_strength=1.0,
    bagging_temperature=1.0,
    eval_metric='AUC',
    random_seed=42,
    verbose=False
)

start = time.time()
cat_model.fit(
    X_tr, y_tr,
    eval_set=(X_val, y_val),
    early_stopping_rounds=50
)
cat_time = time.time() - start

cat_pred = cat_model.predict_proba(X_test)[:, 1]
results['CatBoost'] = {
    'AUC': roc_auc_score(y_test, cat_pred),
    'Accuracy': accuracy_score(y_test, cat_model.predict(X_test)),
    'Time(s)': round(cat_time, 2),
    'Best Iter': cat_model.best_iteration_
}

# ────────────────────────────────────────
# 5. 결과 출력
# ────────────────────────────────────────
result_df = pd.DataFrame(results).T
result_df['AUC'] = result_df['AUC'].map('{:.4f}'.format)
result_df['Accuracy'] = result_df['Accuracy'].map('{:.4f}'.format)
print(result_df.to_string())

# ────────────────────────────────────────
# 6. 특성 중요도 시각화 (상위 15개)
# ────────────────────────────────────────
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

for ax, (name, model, feat_imp) in zip(axes, [
    ('XGBoost',  xgb_model, xgb_model.feature_importances_),
    ('LightGBM', lgb_model, lgb_model.feature_importances_),
    ('CatBoost', cat_model, cat_model.get_feature_importance()),
]):
    top15_idx = np.argsort(feat_imp)[-15:]
    ax.barh(range(15), feat_imp[top15_idx])
    ax.set_yticks(range(15))
    ax.set_yticklabels([f'feature_{i}' for i in top15_idx])
    ax.set_title(f'{name} Feature Importance')

plt.tight_layout()
plt.show()
```

<!-- Execution error: ModuleNotFoundError: No module named 'xgboost' -->

### 실험 결과 해석

100,000개 샘플, 50개 특성의 합성 이진 분류 데이터셋에서 일반적으로 다음과 같은 패턴이 관찰된다:
- **LightGBM**: 학습 속도가 가장 빠르다 (XGBoost 대비 3~10배 빠른 경우가 많음)
- **AUC 성능**: 세 모델 모두 유사한 성능을 보이며, 데이터 특성에 따라 승자가 달라진다
- **CatBoost**: 범주형 특성이 없는 순수 수치형 데이터에서는 상대적으로 느리고 이점이 줄어든다

---

## 결론

부스팅 3대장은 각자 뚜렷한 강점을 갖는다. 실무에서는 다음 기준으로 출발점을 선택하면 효과적이다:

- 처음 시작하거나 범용성을 원한다면 → **XGBoost**
- 데이터가 크고 속도가 중요하다면 → **LightGBM**
- 범주형 특성이 많고 전처리를 줄이고 싶다면 → **CatBoost**

실제 캐글 솔루션에서는 세 모델을 앙상블하여 다양성(diversity)을 확보하는 전략이 흔하다. 단일 모델 성능의 차이보다, 올바른 교차 검증 설계와 특성 공학(feature engineering)이 최종 성능에 훨씬 큰 영향을 미친다는 점을 잊지 말자.