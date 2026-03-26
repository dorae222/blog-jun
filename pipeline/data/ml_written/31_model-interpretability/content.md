## 1. 개요: 왜 해석 가능성이 중요한가

머신러닝 모델의 성능이 비약적으로 향상되면서, 의료·금융·법률 등 고위험 도메인에서의 활용이 급증하고 있다. 그러나 XGBoost, LightGBM, 딥러닝 같은 고성능 모델은 내부 구조가 복잡해 '왜 이런 예측을 내렸는가'를 직관적으로 설명하기 어렵다. 이를 **블랙박스(black-box)** 문제라 부른다.

해석 가능성(interpretability)이 중요한 이유는 세 가지로 요약된다.

- **규제 준수**: EU AI Act, 금융위원회 가이드라인 등은 자동화 의사결정에 설명 의무를 부과한다. 대출 거절·보험 거부 사유를 명시하지 못하면 법적 리스크가 발생한다.
- **신뢰 구축**: 의사나 판사가 모델 결과를 신뢰하려면 근거가 필요하다. 예측 정확도가 높더라도 설명이 없으면 현장 채택률이 낮다.
- **디버깅과 개선**: 모델이 데이터 누수(leakage)나 숏컷 학습을 하고 있는지 탐지하려면 내부 판단 근거를 들여다봐야 한다. 해석 도구는 모델 오류의 원인을 찾는 강력한 진단 수단이다.

---

## 2. Feature Importance의 한계

### 트리 기반 Feature Importance

사이킷런의 `feature_importances_`는 각 분기에서 해당 피처가 불순도(Gini, Entropy)를 얼마나 감소시켰는지를 평균 낸 값이다. 계산이 빠르고 직관적이지만 치명적인 편향이 있다.

**고카디널리티(high-cardinality) 변수 우대**: 분기 횟수가 많을수록 중요도가 높게 측정된다. 랜덤 ID나 우편번호처럼 고유값이 많은 변수는 실제로 의미 없어도 높은 중요도를 받는다. Strobl et al.(2007)은 이를 실험적으로 증명했다.

### Permutation Importance

특정 피처 $j$의 값을 무작위로 섞은 뒤 성능 하락을 측정한다.

$$\text{PI}_j = \text{score}(\text{original}) - \text{score}(\text{permuted}_j)$$

모델 구조에 의존하지 않아 더 신뢰할 수 있지만, **상관 변수 문제**가 남는다. 두 피처가 강하게 상관될 때 하나를 섞어도 다른 하나가 보완하므로 중요도가 과소평가된다.

---

## 3. PDP (Partial Dependence Plot)

### 한계 효과

PDP는 관심 피처 $x_j$가 예측에 미치는 평균적 효과를 보여준다. 나머지 피처 $X_{\backslash j}$의 분포를 주변화(marginalize)해 계산한다.

$$\text{PDP}(x_j) = E_{X_{\backslash j}}[\hat{f}(x_j, X_{\backslash j})] \approx \frac{1}{n}\sum_{i=1}^{n}\hat{f}(x_j, x_{\backslash j}^{(i)})$$

모든 샘플에 대해 $x_j$를 특정 값으로 고정하고 예측을 평균 내는 방식이다. x축은 피처값, y축은 평균 예측값이 된다.

### ICE (Individual Conditional Expectation)

PDP가 평균을 보여준다면, ICE는 각 샘플별 조건부 기대값을 개별 곡선으로 그린다. 이질적인 효과(heterogeneous effect)를 포착하는 데 유용하다. 일부 샘플은 피처가 증가할 때 예측이 오르고, 다른 샘플은 반대로 움직일 수 있는데, PDP는 이를 평균화해 숨겨버린다.

ICE 곡선들을 평균 낸 것이 PDP이므로, 두 시각화를 함께 보면 평균 효과와 개별 이질성을 동시에 파악할 수 있다.

---

## 4. LIME (Local Interpretable Model-agnostic Explanations)

Ribeiro et al.(2016)이 제안한 LIME은 복잡한 모델의 **로컬(local) 이웃**에서 단순한 선형 모델로 근사하는 방법이다.

### 핵심 아이디어

복잡한 모델 $f$를 전역적으로 설명하기 어렵더라도, 특정 입력 $x$ 주변의 좁은 영역에서는 선형 모델 $g$로 충분히 근사할 수 있다는 가정에서 출발한다.

### 알고리즘

1. **샘플링**: 설명하려는 입력 $x$ 주변에서 변형 샘플 $z'$을 생성한다. 이미지라면 슈퍼픽셀을 on/off하고, 텍스트라면 단어를 제거한다.
2. **가중치 부여**: $x$와 유사할수록 높은 가중치를 주는 커널 함수 $\pi_x(z) = \exp(-D(x,z)^2/\sigma^2)$를 적용한다.
3. **가중 선형 회귀**: 블랙박스 모델 $f$로 샘플을 예측하고, 그 결과를 타깃으로 삼아 가중 선형 회귀를 학습한다.

$$\xi(x) = \arg\min_{g \in G} \mathcal{L}(f, g, \pi_x) + \Omega(g)$$

### LIME의 한계

- **불안정성**: 샘플링이 확률적이므로 같은 입력에 대해 실행할 때마다 다른 설명이 나올 수 있다.
- **로컬 충실도(local fidelity)**: 설명은 $x$ 주변에서만 유효하며, 조금만 벗어나면 틀릴 수 있다.
- **이웃 정의 문제**: 커널 폭 $\sigma$의 선택이 결과에 크게 영향을 미친다.

---

## 5. SHAP (SHapley Additive exPlanations)

Lundberg & Lee(2017)가 제안한 SHAP은 협력 게임 이론의 **Shapley Value**를 머신러닝 해석에 적용한 방법이다. LIME보다 수학적으로 탄탄한 기반을 갖는다.

### 게임 이론적 배경

$n$명의 플레이어(피처)가 협력해 가치(예측값)를 만들어낼 때, 각 플레이어의 공정한 기여도를 Shapley Value라 한다. 핵심 아이디어는 모든 가능한 피처 부분집합(coalition)에서 해당 피처를 추가했을 때의 한계 기여(marginal contribution)를 평균 내는 것이다.

$$\phi_i = \sum_{S \subseteq F \setminus \{i\}} \frac{|S|!(|F|-|S|-1)!}{|F|!}\left[f(S \cup \{i\}) - f(S)\right]$$

여기서 $F$는 전체 피처 집합, $S$는 피처 $i$를 제외한 부분집합, $|S|!(|F|-|S|-1)!/|F|!$는 해당 순서가 나타날 확률이다.

### 속성 분해

SHAP의 핵심 성질은 예측값을 피처별 기여도의 합으로 분해할 수 있다는 것이다.

$$f(x) = \phi_0 + \sum_{i=1}^{n} \phi_i$$

$\phi_0$는 전체 학습 데이터의 평균 예측값(베이스라인)이고, $\phi_i$는 피처 $i$가 베이스라인에서 실제 예측으로 얼마나 밀어붙였는지를 나타낸다. 양수면 예측을 올렸고, 음수면 내렸다.

SHAP은 다음 세 가지 공리를 만족한다.
- **효율성(Efficiency)**: 모든 Shapley Value의 합 $= f(x) - f(\text{baseline})$
- **대칭성(Symmetry)**: 동일한 기여를 하는 두 피처는 동일한 값을 가진다.
- **더미(Dummy)**: 어떤 연합에도 기여하지 않는 피처의 값은 0이다.

### TreeSHAP

정확한 Shapley Value 계산은 $O(2^n)$으로 피처 수가 늘면 폭발적으로 느려진다. Lundberg et al.(2018)은 트리 기반 모델(XGBoost, LightGBM, Random Forest)에 특화된 **TreeSHAP** 알고리즘을 제안해 $O(TLD^2)$ (트리 수 $T$, 리프 수 $L$, 깊이 $D$)로 정확한 값을 계산한다.

---

## 6. SHAP 시각화 유형

### Force Plot

개별 샘플 하나의 예측을 설명한다. 빨간 막대는 예측을 올린 피처, 파란 막대는 내린 피처를 보여준다. 베이스라인(E[f(x)])에서 출발해 각 피처의 기여가 화살표처럼 예측값을 밀어붙이는 직관적 시각화다.

### Summary Plot (Beeswarm Plot)

전체 데이터셋에 걸친 피처 중요도와 방향성을 동시에 보여준다. y축은 피처(중요도 순), x축은 SHAP 값, 점의 색은 원래 피처값(빨강=높음, 파랑=낮음)이다. 어떤 피처가 얼마나 중요하고, 어떤 방향으로 예측에 영향을 주는지 한눈에 파악할 수 있다.

### Dependence Plot

특정 피처의 SHAP 값을 y축, 피처 원래 값을 x축으로 그린다. PDP와 달리 개별 점이 찍혀 분산을 확인할 수 있다. 색상으로 두 번째 피처를 인코딩하면 **피처 간 상호작용(interaction)**을 탐지할 수 있다.

---

## 7. Python 코드: XGBoost 모델 SHAP 해석

```python
import numpy as np
import pandas as pd
import xgboost as xgb
import shap
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 데이터 준비
data = load_breast_cancer()
X = pd.DataFrame(data.data, columns=data.feature_names)
y = data.target

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# XGBoost 학습
model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=4,
    learning_rate=0.05,
    use_label_encoder=False,
    eval_metric='logloss',
    random_state=42
)
model.fit(X_train, y_train)

# ── SHAP 계산 (TreeSHAP) ──────────────────────────────────────────
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_test)   # shape: (n_samples, n_features)

# 1) Summary Plot: 전체 피처 중요도 + 방향
shap.summary_plot(shap_values, X_test, plot_type="beeswarm")

# 2) Bar Plot: 절댓값 평균으로 랭킹
shap.summary_plot(shap_values, X_test, plot_type="bar")

# 3) Force Plot: 첫 번째 샘플 개별 설명
shap.initjs()
shap.force_plot(
    explainer.expected_value,
    shap_values[0],
    X_test.iloc[0]
)

# 4) Dependence Plot: worst radius와 상호작용 탐지
shap.dependence_plot(
    "worst radius",
    shap_values,
    X_test,
    interaction_index="worst concave points"  # 자동 감지도 가능
)

# 5) Waterfall Plot: 개별 예측의 단계별 기여
shap.plots.waterfall(explainer(X_test)[0])

# ── LIME 비교 ──────────────────────────────────────────────────────
from lime import lime_tabular

lime_explainer = lime_tabular.LimeTabularExplainer(
    X_train.values,
    feature_names=X_train.columns.tolist(),
    class_names=['malignant', 'benign'],
    mode='classification'
)

# 첫 번째 테스트 샘플 설명
exp = lime_explainer.explain_instance(
    X_test.iloc[0].values,
    model.predict_proba,
    num_features=10
)
exp.show_in_notebook(show_table=True)

# SHAP vs LIME 비교: 피처 중요도 랭킹 상관관계
shap_importance = pd.Series(
    np.abs(shap_values).mean(axis=0),
    index=X_test.columns
).sort_values(ascending=False)

print("SHAP Top-5 피처:")
print(shap_importance.head(5))
```

```output
<!-- Pre-computed result needed -->
```

**코드 해설**: `shap.TreeExplainer`는 XGBoost의 트리 구조를 직접 분석해 정확한 Shapley Value를 빠르게 계산한다. `shap_values`의 각 행은 해당 샘플에서 각 피처의 기여도이며, 합산하면 `explainer.expected_value`에서 실제 예측 로짓까지의 차이와 일치한다(효율성 공리).

---

## 정리: SHAP vs LIME vs PDP

| 항목 | PDP | LIME | SHAP |
|------|-----|------|------|
| 범위 | 전역(Global) | 로컬(Local) | 로컬+전역 |
| 속도 | 빠름 | 중간 | 트리: 빠름, 일반: 느림 |
| 안정성 | 높음 | 낮음(샘플링 의존) | 높음 |
| 이론적 근거 | 약함 | 중간 | 강함(게임 이론) |
| 상호작용 포착 | 제한적 | 어려움 | Interaction Values 지원 |

실무에서는 SHAP을 기본 도구로 사용하되, 빠른 전역 이해에는 PDP를, 텍스트·이미지 도메인의 직관적 설명에는 LIME을 보조적으로 활용하는 것이 일반적이다.

고성능과 해석 가능성은 더 이상 트레이드오프가 아니다. SHAP과 LIME은 복잡한 모델을 현업 전문가와 규제 기관에게 설명 가능한 언어로 번역해준다. 모델을 배포하기 전에 반드시 해석 도구로 검증하는 습관을 갖자.