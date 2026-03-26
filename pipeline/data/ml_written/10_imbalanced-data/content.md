## 개요: 클래스 불균형 문제란?

현실 세계의 ML 문제에서 클래스 불균형(Class Imbalance)은 예외가 아니라 **규칙**에 가깝습니다. 사기 거래 탐지에서 사기 건수는 전체의 0.1% 미만이고, 암 진단에서 양성 케이스는 수천 명 중 한두 명에 불과합니다. 제조 공정의 불량 검출, 네트워크 침입 탐지, 대출 부도 예측 — 모두 같은 문제를 공유합니다.

### 정확도의 함정 (Accuracy Paradox)

클래스 불균형이 왜 문제가 되는지 가장 직관적인 예를 들어보겠습니다.

어떤 데이터셋에 정상 거래 99,000건, 사기 거래 1,000건이 있다고 합시다. 이때 "모든 거래를 정상으로 예측"하는 모델을 만들면:

$$\text{Accuracy} = \frac{99{,}000}{100{,}000} = 99\%$$

**99% 정확도!** 하지만 이 모델은 사기를 단 한 건도 잡지 못합니다. 비즈니스적으로 완전히 무가치한 모델이지만 정확도 지표만 보면 훌륭해 보입니다.

이것이 **정확도의 함정(Accuracy Paradox)**입니다. 불균형 데이터에서 단순 정확도는 모델의 실제 성능을 심각하게 왜곡합니다.

### 클래스 불균형의 분류

| 불균형 수준 | 비율 | 예시 |
|-------------|------|------|
| 경미 (Mild) | 1:4 ~ 1:10 | 일부 의료 데이터 |
| 중간 (Moderate) | 1:10 ~ 1:100 | 대출 부도 예측 |
| 심각 (Severe) | 1:100 ~ 1:1000 | 사기 탐지 |
| 극심 (Extreme) | 1:1000 이상 | 희귀 질환 진단 |

---

## 불균형 탐지와 진단

### 클래스 비율 확인

모델을 훈련하기 전에 반드시 클래스 분포를 시각화해야 합니다:

```python
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

# 클래스 분포 확인
class_counts = Counter(y)
for cls, count in class_counts.items():
    ratio = count / len(y) * 100
    print(f"클래스 {cls}: {count}건 ({ratio:.2f}%)")

# 불균형 비율
majority = max(class_counts.values())
minority = min(class_counts.values())
print(f"\n불균형 비율: {majority // minority}:1")
```

<!-- Execution error: NameError: name 'y' is not defined -->

### 올바른 평가 지표 선택

불균형 데이터에서는 정확도 대신 다음 지표를 사용해야 합니다.

**혼동 행렬 기반 지표**

| 지표 | 수식 | 의미 |
|------|------|------|
| 정밀도 (Precision) | $\frac{TP}{TP+FP}$ | 양성 예측 중 실제 양성 비율 |
| 재현율 (Recall) | $\frac{TP}{TP+FN}$ | 실제 양성 중 탐지된 비율 |
| F1-Score | $\frac{2 \cdot P \cdot R}{P+R}$ | 정밀도와 재현율의 조화평균 |
| F-beta | $\frac{(1+\beta^2) \cdot P \cdot R}{\beta^2 \cdot P+R}$ | $\beta > 1$이면 재현율 중시 |

**랭킹 기반 지표**

- **ROC-AUC**: 임계값에 무관한 전반적인 분리 능력. 불균형이 심할수록 낙관적으로 보일 수 있음.
- **PR-AUC (Average Precision)**: Precision-Recall 곡선의 넓이. 불균형 데이터에서 ROC-AUC보다 훨씬 정직한 지표.

> 실무 팁: 사기 탐지처럼 소수 클래스를 놓치는 비용이 클 때는 **재현율(Recall)**을 우선시하고, PR-AUC를 주 평가 지표로 사용하세요.

---

## 오버샘플링 (Over-sampling)

![리샘플링 방법 비교: 오버샘플링, 언더샘플링, 결합 방법의 효과](figures/resampling_comparison.png)
*리샘플링 비교: 원본 데이터, 랜덤 오버샘플링, SMOTE, 랜덤 언더샘플링 적용 후의 클래스 분포 변화를 시각적으로 비교한다.*

소수 클래스의 샘플 수를 인위적으로 늘려서 균형을 맞추는 방법입니다.

### 단순 복제 (Random Oversampling)

소수 클래스 샘플을 무작위로 복제합니다. 구현이 단순하지만 **과적합** 위험이 높습니다. 복제된 샘플은 새로운 정보를 추가하지 않으므로 모델이 특정 샘플을 암기할 수 있습니다.

```python
from imblearn.over_sampling import RandomOverSampler

ros = RandomOverSampler(random_state=42)
X_resampled, y_resampled = ros.fit_resample(X_train, y_train)
```

![SMOTE 동작 시각화: 소수 클래스 사이에 합성 샘플을 생성하는 과정](figures/smote_visualization.png)
*SMOTE 알고리즘: 소수 클래스의 기존 샘플 사이에 보간점을 생성하여 합성 샘플을 만드는 과정을 2D 공간에서 보여준다.*

### SMOTE: Synthetic Minority Over-sampling Technique

Chawla et al.(2002)이 제안한 SMOTE는 소수 클래스의 실제 샘플 사이에 **보간점(Interpolation Point)**을 생성하여 합성 샘플을 만듭니다.

**알고리즘 동작 방식**

1. 소수 클래스의 샘플 $x_i$를 선택
2. $x_i$의 k-최근접 이웃(k-NN) 중 무작위로 $x_{knn}$을 선택
3. 두 샘플 사이에 합성 샘플 $x_{new}$를 생성:

$$x_{new} = x_i + \lambda \cdot (x_{knn} - x_i)$$

여기서 $\lambda \in [0, 1]$는 균등 분포에서 무작위로 추출됩니다.

이 공식은 $x_i$와 $x_{knn}$을 잇는 선분 위의 임의 점을 생성한다는 의미입니다. 단순 복제와 달리 새로운 정보를 추가하므로 과적합 위험이 낮습니다.

```python
from imblearn.over_sampling import SMOTE

smote = SMOTE(
    sampling_strategy='auto',  # 소수 클래스를 다수 클래스 수만큼 생성
    k_neighbors=5,             # k-NN 파라미터
    random_state=42
)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

print(f"리샘플링 전: {Counter(y_train)}")
print(f"리샘플링 후: {Counter(y_resampled)}")
```

<!-- Execution error: ModuleNotFoundError: No module named 'imblearn' -->

**SMOTE의 주의사항**

- **반드시 훈련 데이터에만 적용**해야 합니다. 테스트 데이터에 적용하면 데이터 누수(Data Leakage)가 발생합니다.
- 범주형 특성이 포함된 경우 표준 SMOTE를 그대로 사용하면 안 됩니다. `SMOTENC`를 사용하세요.
- 경계 영역에서 노이즈 샘플 근처에 합성 샘플이 생성될 수 있습니다.

### ADASYN: Adaptive Synthetic Sampling

He et al.(2008)이 제안한 ADASYN은 SMOTE를 개선하여, **분류하기 어려운 샘플(경계 근처) 주변에 더 많은 합성 샘플**을 생성합니다.

핵심 아이디어: 소수 클래스 샘플 $x_i$의 k-NN 이웃 중 다수 클래스 비율 $r_i$를 계산하고, 이 비율에 비례하여 생성할 샘플 수를 결정합니다. 경계에 가까울수록(다수 클래스 이웃이 많을수록) 더 많은 샘플을 생성합니다.

```python
from imblearn.over_sampling import ADASYN

adasyn = ADASYN(random_state=42)
X_resampled, y_resampled = adasyn.fit_resample(X_train, y_train)
```

ADASYN은 SMOTE보다 경계 학습에 집중하지만, 아웃라이어 주변에도 샘플을 생성할 수 있다는 단점이 있습니다.

---

## 언더샘플링 (Under-sampling)

다수 클래스의 샘플을 줄여서 균형을 맞추는 방법입니다. 데이터 자체가 충분히 많을 때 유효합니다.

### 랜덤 언더샘플링 (Random Undersampling)

다수 클래스에서 무작위로 샘플을 제거합니다. 빠르고 단순하지만 유용한 정보를 잃을 수 있습니다.

```python
from imblearn.under_sampling import RandomUnderSampler

rus = RandomUnderSampler(random_state=42)
X_resampled, y_resampled = rus.fit_resample(X_train, y_train)
```

### Tomek Links: 경계 정리

두 샘플 $x_i$(소수 클래스)와 $x_j$(다수 클래스)가 서로의 최근접 이웃이면 이를 **Tomek Link**라 합니다. 이 경우 결정 경계 근처의 다수 클래스 샘플 $x_j$를 제거하여 경계를 명확하게 만듭니다.

Tomek Links는 단독으로 사용하면 제거되는 양이 적어 완전한 균형을 달성하기 어렵습니다. 주로 오버샘플링과 결합하여 경계 정리에 활용합니다.

```python
from imblearn.under_sampling import TomekLinks

tl = TomekLinks()
X_resampled, y_resampled = tl.fit_resample(X_train, y_train)
```

### NearMiss: 거리 기반 선택

NearMiss는 소수 클래스와의 거리를 기준으로 다수 클래스 샘플을 선택적으로 제거합니다. 세 가지 버전이 있습니다:

- **NearMiss-1**: 소수 클래스 샘플들과의 평균 거리가 가장 작은 다수 클래스 샘플을 선택
- **NearMiss-2**: 소수 클래스 샘플들과의 평균 거리가 가장 큰 다수 클래스 샘플을 선택 (원거리 소수 포함)
- **NearMiss-3**: 각 소수 클래스 샘플에 대해 가장 가까운 다수 클래스 샘플을 선택

```python
from imblearn.under_sampling import NearMiss

nm = NearMiss(version=1)
X_resampled, y_resampled = nm.fit_resample(X_train, y_train)
```

---

## 결합 방법 (Combination)

오버샘플링과 언더샘플링을 함께 적용하면 각 방법의 단점을 보완할 수 있습니다.

### SMOTE + Tomek Links

SMOTE로 소수 클래스를 보강한 후, Tomek Links로 경계 근처의 노이즈를 정리합니다. 가장 널리 사용되는 결합 전략 중 하나입니다.

```python
from imblearn.combine import SMOTETomek

smt = SMOTETomek(random_state=42)
X_resampled, y_resampled = smt.fit_resample(X_train, y_train)
```

### SMOTE + ENN (Edited Nearest Neighbours)

ENN은 k-NN으로 잘못 분류되는 샘플을 제거하는 방법입니다. SMOTE로 생성된 노이즈 샘플까지 정리할 수 있어 경계가 더욱 깔끔해집니다.

```python
from imblearn.combine import SMOTEENN

smote_enn = SMOTEENN(random_state=42)
X_resampled, y_resampled = smote_enn.fit_resample(X_train, y_train)
```

---

## 알고리즘 수준 접근법

데이터를 변형하지 않고, 알고리즘 자체를 수정하거나 학습 설정을 조정하는 방법입니다.

### class_weight 파라미터 활용

대부분의 sklearn 분류기는 `class_weight='balanced'` 옵션을 지원합니다. 이 설정은 클래스 빈도에 반비례하는 가중치를 손실 함수에 적용합니다:

$$w_c = \frac{N}{K \cdot N_c}$$

여기서 $N$은 전체 샘플 수, $K$는 클래스 수, $N_c$는 클래스 $c$의 샘플 수입니다. 소수 클래스에 더 높은 가중치를 부여하여 모델이 소수 클래스를 더 중시하게 만듭니다.

```python
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC

# 방법 1: balanced 자동 설정
lr = LogisticRegression(class_weight='balanced')
rf = RandomForestClassifier(class_weight='balanced')
svc = SVC(class_weight='balanced')

# 방법 2: 수동 지정
lr_manual = LogisticRegression(class_weight={0: 1, 1: 10})
```

### 임계값(Threshold) 조정

기본적으로 이진 분류에서 임계값은 0.5입니다. 하지만 불균형 데이터에서는 임계값을 낮추면 소수 클래스를 더 많이 탐지할 수 있습니다. 이는 Precision-Recall 트레이드오프를 활용하는 방식입니다.

```python
from sklearn.metrics import precision_recall_curve
import numpy as np

# 확률 예측
y_prob = model.predict_proba(X_test)[:, 1]

# PR 곡선으로 최적 임계값 탐색
precisions, recalls, thresholds = precision_recall_curve(y_test, y_prob)

# F1이 최대인 임계값 선택
f1_scores = 2 * precisions * recalls / (precisions + recalls + 1e-8)
best_threshold = thresholds[np.argmax(f1_scores[:-1])]
print(f"최적 임계값: {best_threshold:.3f}")

# 임계값 적용
y_pred_adjusted = (y_prob >= best_threshold).astype(int)
```

<!-- Execution error: NameError: name 'model' is not defined -->

### Focal Loss (딥러닝)

Lin et al.(2017)의 RetinaNet 논문에서 제안된 Focal Loss는 쉽게 분류되는 다수 클래스 샘플의 기여를 줄이고, 어렵게 분류되는 소수 클래스 샘플에 집중하도록 손실 함수를 수정합니다:

$$FL(p_t) = -\alpha_t (1 - p_t)^\gamma \log(p_t)$$

여기서 $(1 - p_t)^\gamma$가 핵심입니다. $p_t$가 크면(쉬운 샘플) 가중치가 작아지고, $p_t$가 작으면(어려운 샘플) 가중치가 커집니다. $\gamma = 0$이면 표준 Cross-Entropy와 동일합니다.

---

## 실전 선택 가이드

어떤 방법을 선택해야 하는지는 데이터의 특성과 비즈니스 요구사항에 따라 달라집니다.

### 상황별 권장 전략

| 상황 | 권장 방법 |
|------|-----------|
| 데이터가 충분히 많음 (> 10만 건) | 랜덤 언더샘플링 또는 class_weight |
| 데이터가 적음 (< 1만 건) | SMOTE 또는 ADASYN |
| 경계가 복잡하고 노이즈가 많음 | SMOTE + Tomek 또는 SMOTE + ENN |
| 범주형 특성 혼재 | SMOTENC |
| 딥러닝 모델 사용 | Focal Loss 또는 class_weight |
| 빠른 베이스라인 필요 | class_weight='balanced' |
| 극심한 불균형 (1:1000 이상) | 이상 탐지(Anomaly Detection) 접근 고려 |

### 실전 워크플로우

1. **먼저 class_weight='balanced'로 시작**: 데이터를 변형하지 않아 가장 안전합니다.
2. **임계값 조정**: PR 곡선으로 비즈니스 요구에 맞는 임계값을 찾습니다.
3. **SMOTE 적용**: 성능이 부족할 때 오버샘플링을 추가합니다.
4. **결합 방법 시도**: SMOTE + Tomek으로 경계를 정리합니다.
5. **평가는 반드시 PR-AUC와 F1으로**: 정확도는 절대 주 지표로 사용하지 않습니다.

> 중요: 리샘플링은 **반드시 교차 검증의 각 폴드 내부에서 적용**해야 합니다. sklearn Pipeline과 imbalanced-learn의 Pipeline을 함께 사용하면 이 문제를 자동으로 처리할 수 있습니다.

---

## Python 코드: imbalanced-learn 실전 예시

### 설치

```bash
pip install imbalanced-learn
```

### 전체 파이프라인 예시

```python
import numpy as np
from collections import Counter
from sklearn.datasets import make_classification
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, average_precision_score
from imblearn.over_sampling import SMOTE
from imblearn.combine import SMOTETomek
from imblearn.pipeline import Pipeline  # sklearn이 아닌 imblearn의 Pipeline!

# 불균형 데이터 생성 (99:1 비율)
X, y = make_classification(
    n_samples=10000,
    n_features=20,
    weights=[0.99, 0.01],  # 다수:소수 = 99:1
    random_state=42
)
print(f"클래스 분포: {Counter(y)}")

# 방법 1: class_weight 활용 (가장 간단)
model_weighted = RandomForestClassifier(
    class_weight='balanced',
    n_estimators=100,
    random_state=42
)

# 방법 2: SMOTE + 분류기 파이프라인
# imblearn Pipeline은 fit 시 자동으로 리샘플링 적용
pipeline_smote = Pipeline([
    ('smote', SMOTE(random_state=42)),
    ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
])

# 방법 3: SMOTETomek + 분류기
pipeline_smotetomek = Pipeline([
    ('smt', SMOTETomek(random_state=42)),
    ('clf', RandomForestClassifier(n_estimators=100, random_state=42))
])

# Stratified K-Fold 교차 검증 (클래스 비율 유지)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

models = {
    'class_weight=balanced': model_weighted,
    'SMOTE + RF': pipeline_smote,
    'SMOTETomek + RF': pipeline_smotetomek,
}

for name, model in models.items():
    # PR-AUC(average_precision)로 평가
    scores = cross_val_score(
        model, X, y,
        cv=skf,
        scoring='average_precision'  # PR-AUC
    )
    print(f"[{name}] PR-AUC: {scores.mean():.4f} (+/- {scores.std():.4f})")

# 최종 모델 상세 평가
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

pipeline_smote.fit(X_train, y_train)
y_pred = pipeline_smote.predict(X_test)
y_prob = pipeline_smote.predict_proba(X_test)[:, 1]

print("\n=== 상세 분류 리포트 ===")
print(classification_report(y_test, y_pred, target_names=['정상', '사기']))
print(f"PR-AUC: {average_precision_score(y_test, y_prob):.4f}")

# 임계값 최적화
from sklearn.metrics import precision_recall_curve

precisions, recalls, thresholds = precision_recall_curve(y_test, y_prob)
f1_scores = 2 * precisions * recalls / (precisions + recalls + 1e-8)
best_idx = np.argmax(f1_scores[:-1])
best_threshold = thresholds[best_idx]

print(f"\n최적 임계값: {best_threshold:.3f}")
print(f"최적 임계값에서 Precision: {precisions[best_idx]:.3f}")
print(f"최적 임계값에서 Recall: {recalls[best_idx]:.3f}")
print(f"최적 임계값에서 F1: {f1_scores[best_idx]:.3f}")

y_pred_optimized = (y_prob >= best_threshold).astype(int)
print("\n=== 임계값 최적화 후 ===")
print(classification_report(y_test, y_pred_optimized, target_names=['정상', '사기']))
```

```output
<!-- Pre-computed result needed -->
```

---

## 정리

클래스 불균형은 실전 ML의 핵심 난제 중 하나입니다. 핵심 원칙을 정리하면:

1. **정확도는 불균형 데이터의 주 지표가 될 수 없습니다.** PR-AUC와 F1을 사용하세요.
2. **가장 먼저 `class_weight='balanced'`를 시도**하세요. 데이터 변형 없이 효과적입니다.
3. **SMOTE는 훈련 데이터에만, 교차 검증 내부에서 적용**해야 합니다. imblearn의 Pipeline을 활용하세요.
4. **임계값 조정**은 비용이 없는 강력한 도구입니다. Precision-Recall 트레이드오프를 활용하세요.
5. **만능 해결책은 없습니다.** 데이터 크기, 특성 유형, 비즈니스 요구사항에 따라 전략을 선택하세요.

> 관련 문서: 평가 지표에 대한 상세한 내용은 [[classification-metrics]]를 참고하세요. 데이터 전처리 전반에 대해서는 [[feature-engineering]]과 [[data-preprocessing]]을, 불균형 데이터에서도 강건한 트리 앙상블에 대해서는 [[random-forest]]를 참고하세요.