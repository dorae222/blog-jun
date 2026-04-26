<!-- infographic-hero -->
![Classification Metrics Complete Guide 핵심 요약](figures/infographic.svg)

*Figure: Classification Metrics Complete Guide 한 장 요약 인포그래픽*

## 1. 개요: 왜 지표 선택이 중요한가

분류 모델을 만들었다면 반드시 마주치는 질문이 있다. "이 모델, 얼마나 좋은가요?" 가장 직관적인 대답은 정확도(Accuracy)다. "100개 중 95개 맞혔어요"라고 말하면 누구나 고개를 끄덕인다. 그런데 이 숫자가 얼마나 믿을 수 있을까?

예를 들어 암 진단 모델을 만들었다고 하자. 전체 환자 중 실제 암 환자가 1%라면, 모델이 무조건 "정상"이라고 예측하기만 해도 정확도 99%를 달성한다. 하지만 이 모델은 쓸모없다. 암 환자를 단 한 명도 잡지 못하기 때문이다.

반대로 스팸 필터를 생각해보자. "의심스러운 것은 모두 스팸"이라고 분류하면 스팸을 놓치는 일은 없지만, 중요한 업무 메일까지 스팸함에 처박히게 된다. 이처럼 **어떤 실수가 더 치명적인가**에 따라 모델을 평가하는 기준이 달라져야 한다.

좋은 데이터 사이언티스트는 문제의 비즈니스 맥락을 이해하고 그에 맞는 지표를 선택한다. 이 글에서는 분류 모델 평가에 사용되는 핵심 지표들을 체계적으로 정리한다.

---

![혼동 행렬과 ROC 곡선: 분류 모델의 핵심 평가 도구](figures/confusion_matrix_roc.png)
*혼동 행렬과 ROC 곡선: 혼동 행렬은 TP, TN, FP, FN의 분포를 보여주고, ROC 곡선은 임계값 변화에 따른 TPR-FPR 관계를 시각화한다.*

## 2. 혼동 행렬(Confusion Matrix)

모든 분류 지표의 출발점은 혼동 행렬이다. 이진 분류(Positive/Negative)에서 모델의 예측 결과는 네 가지 경우로 나뉜다.

|  | 예측: Positive | 예측: Negative |
|---|---|---|
| **실제: Positive** | TP (True Positive) | FN (False Negative) |
| **실제: Negative** | FP (False Positive) | TN (True Negative) |

각 항목의 의미를 직관적으로 이해하려면 도메인 예시가 도움이 된다.

**사기 탐지(Fraud Detection) 예시**
- **TP**: 실제 사기 거래를 사기로 올바르게 탐지함 → 가장 이상적인 결과
- **TN**: 정상 거래를 정상으로 올바르게 판단함 → 정상 작동
- **FP**: 정상 거래를 사기로 잘못 탐지함 → 고객 불편, 거래 차단
- **FN**: 실제 사기 거래를 정상으로 놓침 → 금전적 손실 발생

**의료 진단(Cancer Detection) 예시**
- **TP**: 실제 암 환자를 암으로 진단함 → 적시에 치료 시작
- **TN**: 정상인을 정상으로 진단함 → 불필요한 치료 없음
- **FP**: 정상인을 암으로 진단함 → 불필요한 검사/수술, 심리적 고통
- **FN**: 실제 암 환자를 정상으로 놓침 → 치료 기회 상실, 생명 위험

의료에서 FN의 대가는 생명이고, 사기 탐지에서 FN의 대가는 금전 손실이다. 이 차이가 지표 선택에 직접적인 영향을 미친다.

---

## 3. 기본 지표들

### 3.1 정확도 (Accuracy)

$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$

전체 예측 중 맞힌 비율이다. 클래스가 균형 잡혀 있을 때는 직관적이고 유용하지만, **클래스 불균형(Class Imbalance)** 상황에서는 심각하게 오도할 수 있다.

### 3.2 정밀도 (Precision)

$$\text{Precision} = \frac{TP}{TP + FP}$$

"모델이 Positive라고 예측한 것 중 실제로 Positive인 비율"이다. FP를 최소화하고 싶을 때, 즉 **잘못된 경보(False Alarm)의 비용이 클 때** 중요하다.

예: 스팸 필터에서 Precision이 낮으면 정상 메일을 스팸으로 분류하는 일이 잦아진다.

### 3.3 재현율 (Recall / Sensitivity / TPR)

$$\text{Recall} = \frac{TP}{TP + FN}$$

"실제 Positive 중 모델이 올바르게 탐지한 비율"이다. FN을 최소화하고 싶을 때, 즉 **놓치는 것의 비용이 클 때** 중요하다.

예: 암 진단에서 Recall이 낮으면 실제 환자를 놓치는 비율이 높아진다.

### 3.4 특이도 (Specificity / TNR)

$$\text{Specificity} = \frac{TN}{TN + FP}$$

"실제 Negative 중 모델이 올바르게 Negative로 분류한 비율"이다. Recall(TPR)의 반대 개념으로, ROC 곡선에서 x축(FPR = 1 - Specificity)을 구성하는 데 사용된다.

---

## 4. F1 Score와 F-beta

### 4.1 Precision-Recall 트레이드오프

Precision과 Recall은 반비례 관계에 있다. 분류 임계값(threshold)을 낮추면(더 적극적으로 Positive 예측) Recall은 올라가지만 Precision은 내려간다. 반대로 임계값을 높이면 Precision은 올라가지만 Recall은 내려간다. 이 트레이드오프를 하나의 숫자로 표현한 것이 F1 Score다.

### 4.2 F1 Score

$$F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$

Precision과 Recall의 **조화평균(Harmonic Mean)**이다. 산술평균과 달리 조화평균은 두 값 중 하나라도 낮으면 전체 점수가 크게 낮아진다. Precision = 1.0, Recall = 0.0이면 F1 = 0.0이 되어, 한쪽만 극단적으로 높은 모델을 걸러낼 수 있다.

### 4.3 F-beta Score

$$F_\beta = (1 + \beta^2) \cdot \frac{\text{Precision} \cdot \text{Recall}}{\beta^2 \cdot \text{Precision} + \text{Recall}}$$

$\beta$는 Recall을 Precision보다 얼마나 더 중요하게 볼 것인지를 조절하는 파라미터다.

- $\beta = 1$: F1 Score (Precision = Recall 동등)
- $\beta = 2$ (F2 Score): Recall을 Precision보다 2배 중요하게 → 의료 진단, 보안 시스템
- $\beta = 0.5$ (F0.5 Score): Precision을 Recall보다 더 중요하게 → 스팸 필터, 추천 시스템

비즈니스 요구사항에 따라 $\beta$를 조절하면 도메인에 맞는 단일 지표를 사용할 수 있다.

---

## 5. ROC Curve와 AUC

### 5.1 ROC Curve란?

ROC(Receiver Operating Characteristic) 곡선은 분류 임계값을 0부터 1까지 변화시키면서 **TPR(True Positive Rate, Recall)** 과 **FPR(False Positive Rate)** 의 관계를 시각화한 것이다.

$$\text{FPR} = \frac{FP}{FP + TN} = 1 - \text{Specificity}$$

- x축: FPR (False Alarm Rate, 높을수록 나쁨)
- y축: TPR / Recall (높을수록 좋음)

임계값이 0이면 모두 Positive로 예측하여 TPR = 1, FPR = 1이 되고, 임계값이 1이면 모두 Negative로 예측하여 TPR = 0, FPR = 0이 된다. 이 두 극단 사이에서 곡선이 그려진다.

### 5.2 AUC (Area Under the Curve)

AUC는 ROC 곡선 아래의 넓이다.

- **AUC = 0.5**: 랜덤 분류기 (대각선) ( 아무 의미 없음
- **AUC = 1.0**: 완벽한 분류기 ) 모든 임계값에서 FPR = 0, TPR = 1
- **AUC = 0.5~0.7**: 약한 모델
- **AUC = 0.7~0.9**: 실용적인 모델
- **AUC > 0.9**: 매우 강력한 모델

AUC의 확률론적 해석: "임의의 Positive 샘플이 임의의 Negative 샘플보다 높은 점수를 받을 확률"이다. 이는 임계값에 독립적인 지표이기 때문에 모델 비교에 유용하다.

### 5.3 ROC-AUC의 장점과 한계

**장점**: 임계값 선택에 무관하게 모델 전체의 성능을 하나의 숫자로 요약할 수 있다.

**한계**: 클래스 불균형 데이터에서 FPR이 낮은 값에서도 AUC가 높게 나올 수 있어 실제 성능을 과대평가할 수 있다.

---

![Precision-Recall 곡선: 불균형 데이터에서의 정밀도-재현율 트레이드오프](figures/precision_recall_curve.png)
*Precision-Recall 곡선: 불균형 데이터에서 ROC 곡선보다 더 정직하게 소수 클래스에 대한 모델 성능을 보여준다.*

## 6. PR Curve (Precision-Recall Curve)

### 6.1 왜 PR Curve인가?

불균형 데이터에서 ROC 곡선은 낙관적으로 보일 수 있다. Negative 클래스가 압도적으로 많으면 FPR이 작아도 실제 FP의 수는 많을 수 있기 때문이다. PR Curve는 Precision과 Recall의 관계를 직접 시각화하여 **소수 클래스(Positive)에 대한 성능을 더 정직하게** 드러낸다.

- x축: Recall (TPR)
- y축: Precision

임계값을 낮출수록 오른쪽(Recall 증가), 높일수록 왼쪽(Recall 감소)으로 이동한다. 곡선이 오른쪽 위 모서리(Recall=1, Precision=1)에 가까울수록 좋은 모델이다.

### 6.2 AP (Average Precision)

AP(Average Precision)는 PR Curve 아래 면적을 근사한 값으로, ROC-AUC처럼 단일 숫자로 PR 성능을 요약한다.

$$\text{AP} = \sum_n (R_n - R_{n-1}) \cdot P_n$$

여기서 $P_n$과 $R_n$은 n번째 임계값에서의 Precision과 Recall이다. **불균형 데이터에서는 ROC-AUC 대신 PR-AUC(AP)를 주요 지표로 사용하는 것이 권장**된다.

---

## 7. 다중 클래스 분류 지표

이진 분류를 넘어 클래스가 3개 이상인 경우, Precision/Recall/F1을 어떻게 집계할지 결정해야 한다.

### 7.1 Macro Average

각 클래스에 대해 지표를 계산한 뒤 단순 평균을 낸다.

$$\text{Macro F1} = \frac{1}{K} \sum_{k=1}^{K} F1_k$$

모든 클래스를 동등하게 취급한다. **소수 클래스의 성능도 동등하게 반영**되므로, 클래스 불균형 상황에서 소수 클래스의 성능을 확인하고 싶을 때 유용하다.

### 7.2 Micro Average

모든 클래스의 TP, FP, FN을 합산한 뒤 한 번에 계산한다.

$$\text{Micro F1} = \frac{2 \cdot \sum TP}{2 \cdot \sum TP + \sum FP + \sum FN}$$

샘플 수가 많은 클래스가 전체 지표에 더 큰 영향을 미친다. **데이터 전체에 걸친 평균 성능**을 측정할 때 적합하다.

### 7.3 Weighted Average

각 클래스의 F1 Score를 해당 클래스의 샘플 수(support)로 가중 평균한다.

$$\text{Weighted F1} = \sum_{k=1}^{K} w_k \cdot F1_k, \quad w_k = \frac{n_k}{N}$$

클래스 불균형 데이터에서 **전체 성능을 보고할 때** 가장 많이 사용된다.

| 방식 | 특징 | 적합한 상황 |
|---|---|---|
| Macro | 클래스 동등 취급 | 소수 클래스 성능도 중요할 때 |
| Micro | 샘플 수 반영 | 전체 샘플 레벨 성능 중요 시 |
| Weighted | 샘플 비율 가중 | 클래스 불균형 데이터 보고 |

---

## 8. 언제 어떤 지표를? (실전 가이드)

지표는 비즈니스 문제와 데이터 특성을 함께 고려해서 선택해야 한다.

**의료 진단 (암, 감염병 탐지)**
- 우선 지표: **Recall (Sensitivity)**
- 이유: FN(환자를 놓치는 것)의 비용이 FP(건강인을 과진단하는 것)보다 훨씬 크다. 조금 더 많이 검사하더라도 놓치지 않는 것이 중요하다.
- 보조 지표: F2 Score, Specificity (불필요한 수술 최소화)

**스팸 필터**
- 우선 지표: **Precision**
- 이유: FP(정상 메일을 스팸으로 분류)의 비용이 FN(스팸을 받는 것)보다 크다. 중요한 메일을 놓치는 것이 더 치명적이다.
- 보조 지표: F0.5 Score

**사기 탐지 (Credit Card Fraud)**
- 우선 지표: **PR-AUC, F1 Score**
- 이유: 극심한 클래스 불균형(정상 거래 99%+). ROC-AUC는 과대평가될 수 있으며, FN(사기 놓침)과 FP(정상 차단)를 균형 있게 봐야 한다.
- 보조 지표: Recall (놓치는 사기 최소화), Precision (고객 불편 최소화)

**클래스 균형 데이터의 일반적인 분류**
- 우선 지표: **Accuracy, ROC-AUC**
- 이유: 클래스가 균형 잡혀 있으면 정확도도 신뢰할 수 있다.

**불균형 데이터 (일반)**
- 우선 지표: **F1 Score, PR-AUC**
- 이유: Accuracy는 다수 클래스에 의해 오도되므로 F1이나 PR-AUC가 더 정직한 평가를 제공한다.

---

## 9. Python 코드: sklearn 완전 예시

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    fbeta_score,
    roc_auc_score,
    average_precision_score,
    classification_report,
    RocCurveDisplay,
    PrecisionRecallDisplay,
)
import matplotlib.pyplot as plt

# ── 1. 데이터 생성 (불균형: 양성 10%) ──────────────────────────────
X, y = make_classification(
    n_samples=5000,
    n_features=20,
    weights=[0.9, 0.1],  # 90% Negative, 10% Positive
    random_state=42,
)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

# ── 2. 모델 학습 ────────────────────────────────────────────────────
model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)            # 임계값 0.5 기준 예측
y_prob = model.predict_proba(X_test)[:, 1]  # Positive 확률

# ── 3. 혼동 행렬 ────────────────────────────────────────────────────
cm = confusion_matrix(y_test, y_pred)
TN, FP, FN, TP = cm.ravel()
print(f"혼동 행렬:\n{cm}")
print(f"TP={TP}, TN={TN}, FP={FP}, FN={FN}")

# ── 4. 기본 지표 계산 ───────────────────────────────────────────────
print("\n=== 주요 분류 지표 ===")
print(f"Accuracy  : {accuracy_score(y_test, y_pred):.4f}")
print(f"Precision : {precision_score(y_test, y_pred):.4f}")
print(f"Recall    : {recall_score(y_test, y_pred):.4f}")
print(f"F1 Score  : {f1_score(y_test, y_pred):.4f}")
print(f"F2 Score  : {fbeta_score(y_test, y_pred, beta=2):.4f}")
print(f"F0.5 Score: {fbeta_score(y_test, y_pred, beta=0.5):.4f}")

# ── 5. 임계값 기반 지표 (확률 점수 필요) ───────────────────────────
print(f"ROC-AUC   : {roc_auc_score(y_test, y_prob):.4f}")
print(f"PR-AUC(AP): {average_precision_score(y_test, y_prob):.4f}")

# ── 6. 분류 리포트 (다중 클래스도 동일 사용) ──────────────────────
print("\n=== Classification Report ===")
print(classification_report(y_test, y_pred, target_names=["Negative", "Positive"]))

# ── 7. 시각화: ROC Curve & PR Curve ────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

RocCurveDisplay.from_predictions(
    y_test, y_prob, ax=axes[0], name="Logistic Regression"
)
axes[0].plot([0, 1], [0, 1], "k--", label="Random (AUC=0.5)")
axes[0].set_title("ROC Curve")
axes[0].legend()

PrecisionRecallDisplay.from_predictions(
    y_test, y_prob, ax=axes[1], name="Logistic Regression"
)
axes[1].set_title("Precision-Recall Curve")

plt.tight_layout()
plt.savefig("classification_metrics.png", dpi=150)
plt.show()

# ── 8. 임계값 조정 예시 ─────────────────────────────────────────────
print("\n=== 임계값별 Precision / Recall 변화 ===")
for threshold in [0.3, 0.4, 0.5, 0.6, 0.7]:
    y_pred_th = (y_prob >= threshold).astype(int)
    p = precision_score(y_test, y_pred_th, zero_division=0)
    r = recall_score(y_test, y_pred_th, zero_division=0)
    f1 = f1_score(y_test, y_pred_th, zero_division=0)
    print(f"  threshold={threshold:.1f} → Precision={p:.3f}, Recall={r:.3f}, F1={f1:.3f}")
```

```output
혼동 행렬:
[[1320   23]
 [  77   80]]
TP=80, TN=1320, FP=23, FN=77

=== 주요 분류 지표 ===
Accuracy  : 0.9333
Precision : 0.7767
Recall    : 0.5096
F1 Score  : 0.6154
F2 Score  : 0.5472
F0.5 Score: 0.7030
ROC-AUC   : 0.9235
PR-AUC(AP): 0.7033

=== Classification Report ===
              precision    recall  f1-score   support

    Negative       0.94      0.98      0.96      1343
    Positive       0.78      0.51      0.62       157

    accuracy                           0.93      1500
   macro avg       0.86      0.75      0.79      1500
weighted avg       0.93      0.93      0.93      1500


=== 임계값별 Precision / Recall 변화 ===
  threshold=0.3 → Precision=0.620, Recall=0.675, F1=0.646
  threshold=0.4 → Precision=0.696, Recall=0.611, F1=0.651
  threshold=0.5 → Precision=0.777, Recall=0.510, F1=0.615
  threshold=0.6 → Precision=0.818, Recall=0.401, F1=0.538
  threshold=0.7 → Precision=0.897, Recall=0.331, F1=0.484
```

![Precision-Recall 곡선과 임계값 분석](figures/precision_recall_curve.png)

*Figure 1: Precision-Recall 트레이드오프: 임계값 변화에 따른 Precision과 Recall의 상반 관계를 시각화하여 비즈니스 요구에 맞는 최적 임계값 선택을 돕는다.*

위 코드를 실행하면 임계값이 낮아질수록 Recall은 높아지고 Precision은 낮아지는 트레이드오프를 직접 확인할 수 있다. 실전에서는 비즈니스 요구사항에 따라 최적 임계값을 선택하는 과정이 모델 개발만큼 중요하다.

---

## 마무리

분류 지표의 핵심 요약:

- **Accuracy**: 클래스 균형 데이터의 빠른 확인용
- **Precision**: FP 비용이 클 때 (스팸, 추천)
- **Recall**: FN 비용이 클 때 (의료, 보안)
- **F1**: Precision과 Recall의 균형이 필요할 때
- **F-beta**: 도메인 요구에 따라 가중치 조절
- **ROC-AUC**: 균형 데이터에서 임계값 무관한 모델 비교
- **PR-AUC**: 불균형 데이터에서 ROC-AUC 대체

좋은 지표는 모델이 풀어야 할 비즈니스 문제에서 출발한다. 숫자를 높이는 것이 아니라, 올바른 숫자를 높이는 것이 목표임을 항상 기억하자.