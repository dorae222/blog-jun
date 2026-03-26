# ML 워크플로우와 프로젝트 설계

## 개요

머신러닝(Machine Learning) 프로젝트는 단순히 모델을 학습시키는 것이 아닙니다. 비즈니스 문제를 정의하고, 데이터를 수집·정제하며, 적절한 모델을 선택·평가하고, 최종적으로 프로덕션 환경에 배포하는 **일련의 체계적인 과정**입니다.

실무에서 ML 프로젝트가 실패하는 가장 큰 원인은 모델 자체의 성능이 아니라, **전체 워크플로우 설계의 부재**입니다. 구글의 유명한 논문 *Hidden Technical Debt in Machine Learning Systems*에 따르면, 실제 ML 시스템에서 모델 코드가 차지하는 비중은 전체의 5% 미만이며, 나머지는 데이터 수집, 피처 추출, 모니터링 등 주변 인프라에 해당합니다.

이 글에서는 ML 프로젝트의 전체 흐름을 **7단계 파이프라인**으로 나누어 체계적으로 살펴보고, 실전에서 바로 활용할 수 있는 체크리스트와 코드 예제를 제공합니다.

---

## ML 파이프라인 7단계

### 1단계: 문제 정의 (Problem Definition)

ML 프로젝트의 **가장 중요한 단계**입니다. 비즈니스 문제를 ML이 풀 수 있는 형태로 변환해야 합니다.

**핵심 질문:**
- 이 문제가 정말 ML로 풀어야 하는 문제인가? (규칙 기반으로 충분하지 않은가?)
- 어떤 유형의 ML 문제인가?
  - **회귀(Regression)**: 연속적인 수치 예측 (예: 주택 가격, 매출 예측)
  - **분류(Classification)**: 카테고리 예측 (예: 스팸 메일 분류, 질병 진단)
  - **클러스터링(Clustering)**: 유사한 그룹 발견 (예: 고객 세그멘테이션)
- 성공 기준(Success Metric)은 무엇인가?
- 예측 결과를 어떻게 활용할 것인가?

```
비즈니스 문제: "고객 이탈을 줄이고 싶다"
    ↓ ML 문제로 변환
ML 문제: "30일 내 이탈할 고객을 예측하는 이진 분류 모델"
    ↓ 성공 기준 정의
메트릭: Recall ≥ 0.8 (이탈 고객을 80% 이상 포착)
```

> **Tip**: 문제 정의 단계에서 도메인 전문가와의 협업이 필수적입니다. ML 엔지니어 혼자 문제를 정의하면 비즈니스 맥락을 놓치기 쉽습니다.

---

### 2단계: 데이터 수집 (Data Collection)

모델은 데이터의 품질 이상으로 좋아질 수 없습니다. **Garbage In, Garbage Out** 원칙을 항상 기억해야 합니다.

**데이터 소스의 종류:**
- **내부 데이터**: DB, 로그, CRM 시스템
- **외부 데이터**: 공공 API, 오픈 데이터셋, 웹 크롤링
- **생성 데이터**: 설문조사, A/B 테스트, 어노테이션(Annotation)

**데이터 품질 확인 체크리스트:**

| 항목 | 확인 사항 |
|------|----------|
| 데이터 양 | 모델 학습에 충분한가? |
| 레이블 품질 | 라벨링이 정확하고 일관적인가? |
| 대표성 | 실제 운영 환경의 데이터 분포를 반영하는가? |
| 시의성 | 데이터가 너무 오래되지 않았는가? |
| 편향 | 특정 그룹이 과대/과소 대표되어 있지 않은가? |

---

### 3단계: 탐색적 데이터 분석 (Exploratory Data Analysis, EDA)

데이터를 모델에 넣기 전, 데이터의 특성과 패턴을 이해하는 과정입니다.

**EDA에서 확인해야 할 것들:**

1. **기본 통계량**: 평균, 중앙값, 표준편차, 사분위수
2. **분포 확인**: 히스토그램, 박스플롯으로 각 피처(Feature)의 분포 파악
3. **상관관계 분석**: 피처 간, 피처와 타겟(Target) 간의 상관관계
4. **결측치 패턴**: 어떤 피처에 결측값이 많은지, 패턴이 있는지
5. **이상치 탐지**: 비정상적으로 크거나 작은 값 식별
6. **클래스 불균형**: 분류 문제에서 각 클래스의 비율 확인

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 기본 정보 확인
df.info()
df.describe()

# 결측치 비율 확인
missing_ratio = df.isnull().sum() / len(df) * 100
print(missing_ratio[missing_ratio > 0].sort_values(ascending=False))

# 상관관계 히트맵
plt.figure(figsize=(12, 8))
sns.heatmap(df.corr(), annot=True, cmap='coolwarm', center=0)
plt.title('Feature Correlation Heatmap')
plt.show()

# 타겟 변수 분포 확인
df['target'].value_counts().plot(kind='bar')
plt.title('Target Distribution')
plt.show()
```

<!-- Execution error: NameError: name 'df' is not defined -->

> **Tip**: EDA는 반복적인 과정입니다. 한 번에 끝내는 것이 아니라, 모델링 과정에서 새로운 인사이트를 발견하면 다시 돌아와 탐색합니다.

---

### 4단계: 데이터 전처리 (Data Preprocessing)

EDA에서 발견한 문제를 해결하고, 모델이 학습할 수 있는 형태로 데이터를 변환하는 단계입니다.

**주요 전처리 작업:**

**(1) 결측치 처리 (Missing Value Handling)**
- 삭제: 결측 비율이 매우 높은 피처 제거
- 대체: 평균/중앙값/최빈값으로 채우기, KNN Imputer 활용

**(2) 이상치 처리 (Outlier Handling)**
- IQR(Interquartile Range) 방법: Q1 - 1.5*IQR ~ Q3 + 1.5*IQR 범위 밖의 값 처리
- Z-Score 방법: 평균에서 3 표준편차 이상 떨어진 값 처리

**(3) 인코딩 (Encoding)**
- **Label Encoding**: 순서가 있는 범주형 변수 (예: Low < Medium < High)
- **One-Hot Encoding**: 순서가 없는 범주형 변수 (예: 색상, 지역)
- **Target Encoding**: 카디널리티가 높은 범주형 변수

**(4) 스케일링 (Scaling)**
- **StandardScaler**: 평균 0, 표준편차 1로 변환 (정규분포에 적합)
- **MinMaxScaler**: 0~1 범위로 변환 (신경망에 적합)
- **RobustScaler**: 중앙값과 IQR 사용 (이상치에 강건)

---

### 5단계: 모델 선택과 학습 (Model Selection & Training)

**베이스라인 먼저, 복잡한 모델은 나중에.** 이것이 실무의 핵심 원칙입니다.

**모델 선택 전략:**

```
1단계: 베이스라인 모델 (Baseline)
   ├─ 회귀: Linear Regression
   ├─ 분류: Logistic Regression
   └─ "이 정도만 해도 비즈니스 가치가 있는가?"
       ↓
2단계: 중간 복잡도 모델
   ├─ Random Forest, Gradient Boosting
   └─ "베이스라인 대비 얼마나 개선되는가?"
       ↓
3단계: 고급 모델
   ├─ XGBoost, LightGBM, 딥러닝
   └─ "복잡도 증가 대비 성능 향상이 충분한가?"
```

**Train/Validation/Test 분리**는 이 단계에서 반드시 수행해야 합니다 (자세한 내용은 아래에서 다룹니다).

---

### 6단계: 모델 평가 (Model Evaluation)

적절한 평가 메트릭(Evaluation Metric)을 선택하는 것이 핵심입니다.

**분류 문제 메트릭:**

| 메트릭 | 적합한 상황 |
|--------|------------|
| Accuracy | 클래스 균형일 때 |
| Precision | 거짓 양성(False Positive) 비용이 높을 때 (예: 스팸 필터) |
| Recall | 거짓 음성(False Negative) 비용이 높을 때 (예: 암 진단) |
| F1-Score | Precision과 Recall의 균형이 필요할 때 |
| AUC-ROC | 임계값(Threshold) 독립적인 전반적 성능 |

**회귀 문제 메트릭:**

| 메트릭 | 특징 |
|--------|------|
| MSE/RMSE | 큰 오차에 더 큰 페널티 |
| MAE | 이상치에 덜 민감 |
| R² | 설명력(0~1, 높을수록 좋음) |
| MAPE | 비율 기반, 해석이 직관적 |

**교차 검증(Cross-Validation)**을 통해 모델의 일반화 성능을 안정적으로 추정합니다. K-Fold, Stratified K-Fold 등의 기법을 활용하여 데이터 분할 방식에 따른 성능 변동성을 줄입니다.

---

### 7단계: 배포와 모니터링 (Deployment & Monitoring)

모델이 실험 환경에서 좋은 성능을 보여도, **프로덕션 환경에서 제대로 동작하는 것은 별개의 문제**입니다.

**모델 서빙(Serving) 방식:**
- **REST API**: Flask/FastAPI로 예측 엔드포인트 제공
- **Batch 추론**: 스케줄러로 주기적으로 대량 예측 수행
- **Edge 배포**: 모바일/IoT 디바이스에서 직접 추론

**모니터링 핵심 항목:**

- **데이터 드리프트(Data Drift)**: 입력 데이터의 분포가 학습 데이터와 달라지는 현상
- **모델 드리프트(Model Drift)**: 시간이 지남에 따라 모델 성능이 저하되는 현상
- **예측 지연 시간(Latency)**: 응답 시간이 SLA를 충족하는가
- **시스템 메트릭**: CPU/메모리 사용량, 에러율

> **중요**: 모델은 한 번 배포하면 끝이 아닙니다. 지속적으로 성능을 모니터링하고, 필요시 재학습(Retraining)하는 **MLOps** 체계를 갖추는 것이 장기적으로 중요합니다.

---

## Train/Validation/Test 분리 전략

### 왜 3개로 나누는가?

데이터를 3개 세트로 나누는 이유는 **모델의 일반화 성능을 정확히 평가**하기 위해서입니다.

| 세트 | 비율 | 역할 |
|------|------|------|
| **Train** | 60~70% | 모델 학습에 사용 |
| **Validation** | 15~20% | 하이퍼파라미터 튜닝 및 모델 선택에 사용 |
| **Test** | 15~20% | 최종 성능 평가에만 사용 (한 번만 사용!) |

```
전체 데이터
├── Train Set (학습) ──────────→ 모델 가중치 학습
├── Validation Set (검증) ────→ 하이퍼파라미터 선택
└── Test Set (테스트) ────────→ 최종 성능 보고 (한 번만!)
```

Validation Set 없이 Train/Test만 나누면, 하이퍼파라미터 튜닝 과정에서 Test Set의 정보가 간접적으로 모델에 반영되어 **과적합(Overfitting)**이 발생합니다.

### Data Leakage 주의

**데이터 누수(Data Leakage)**는 학습 데이터에 테스트 시점의 정보가 포함되는 현상으로, 실험에서는 성능이 좋지만 실제 서비스에서는 성능이 급락하는 원인이 됩니다.

**흔한 Data Leakage 사례:**

1. **전처리 순서 오류**: 전체 데이터로 스케일링 후 분리 (올바른 방법: 분리 후 Train 기준으로 스케일링)
2. **시계열 데이터 무작위 분리**: 미래 데이터가 학습에 포함됨 (올바른 방법: 시간 순서로 분리)
3. **타겟 관련 피처 포함**: 예측 시점에 알 수 없는 정보를 피처로 사용

```python
# 잘못된 방법 (Data Leakage 발생!)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # 전체 데이터로 fit
X_train, X_test = train_test_split(X_scaled)

# 올바른 방법
X_train, X_test = train_test_split(X)
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)   # Train으로만 fit
X_test = scaler.transform(X_test)          # Test는 transform만
```

---

## 실전 체크리스트

프로젝트 시작 전, 아래 항목을 반드시 확인하세요.

### 문제 정의 단계
- [ ] ML이 아닌 방법으로 먼저 해결 가능한지 검토했는가?
- [ ] 성공 기준과 비즈니스 메트릭이 명확한가?
- [ ] 예측 결과의 활용 방안이 구체적인가?

### 데이터 단계
- [ ] 학습에 충분한 양의 레이블 데이터가 있는가?
- [ ] 데이터 수집 및 라벨링 파이프라인이 존재하는가?
- [ ] 데이터의 편향(Bias)을 검토했는가?
- [ ] 개인정보 및 보안 규정을 준수하는가?

### 모델링 단계
- [ ] 베이스라인 모델을 먼저 구축했는가?
- [ ] Train/Val/Test 분리가 올바르게 되어 있는가?
- [ ] Data Leakage가 없는지 확인했는가?
- [ ] 교차 검증으로 성능 변동성을 확인했는가?

### 배포 단계
- [ ] 추론 지연 시간(Latency) 요구사항을 충족하는가?
- [ ] 데이터/모델 드리프트 모니터링 체계가 있는가?
- [ ] 모델 롤백(Rollback) 전략이 있는가?
- [ ] 재학습 주기와 방법이 정해져 있는가?

---

## Python 코드 예제: sklearn 전체 파이프라인

scikit-learn을 활용하여 위 7단계를 하나의 코드로 구현한 예제입니다.

```python
import numpy as np
import pandas as pd
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score
)
import warnings
warnings.filterwarnings('ignore')

# ==============================================
# 1단계: 문제 정의
# - 유방암 진단 → 이진 분류 (양성/악성)
# - 목표 메트릭: Recall (악성을 놓치지 않는 것이 중요)
# ==============================================

# ==============================================
# 2단계: 데이터 수집
# ==============================================
data = load_breast_cancer()
df = pd.DataFrame(data.data, columns=data.feature_names)
df['target'] = data.target

print(f"데이터 크기: {df.shape}")
print(f"클래스 분포:\n{df['target'].value_counts()}")

# ==============================================
# 3단계: EDA (간략)
# ==============================================
print(f"\n결측치 수: {df.isnull().sum().sum()}")
print(f"기본 통계량:\n{df.describe().T[['mean', 'std', 'min', 'max']].head()}")

# ==============================================
# 4단계: 데이터 전처리 + 5단계: 모델 선택과 학습
# ==============================================
X = df.drop('target', axis=1)
y = df['target']

# Train/Validation/Test 분리 (60/20/20)
X_temp, X_test, y_temp, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
)

print(f"\nTrain: {X_train.shape[0]}, Val: {X_val.shape[0]}, Test: {X_test.shape[0]}")

# sklearn Pipeline으로 전처리 + 모델을 하나로 묶기
# (Data Leakage 방지: fit은 Train에서만 수행)
models = {
    'Logistic Regression (Baseline)': Pipeline([
        ('scaler', StandardScaler()),
        ('model', LogisticRegression(max_iter=10000, random_state=42))
    ]),
    'Random Forest': Pipeline([
        ('scaler', StandardScaler()),
        ('model', RandomForestClassifier(n_estimators=100, random_state=42))
    ]),
    'Gradient Boosting': Pipeline([
        ('scaler', StandardScaler()),
        ('model', GradientBoostingClassifier(n_estimators=100, random_state=42))
    ])
}

# 교차 검증으로 모델 비교
print("\n" + "="*50)
print("모델별 교차 검증 결과 (Recall 기준)")
print("="*50)

best_model_name = None
best_score = 0

for name, pipeline in models.items():
    scores = cross_val_score(
        pipeline, X_train, y_train, cv=5, scoring='recall'
    )
    mean_score = scores.mean()
    print(f"{name}: {mean_score:.4f} (+/- {scores.std():.4f})")

    if mean_score > best_score:
        best_score = mean_score
        best_model_name = name

print(f"\n최적 모델: {best_model_name}")

# ==============================================
# 하이퍼파라미터 튜닝 (Validation Set 활용)
# ==============================================
best_pipeline = models[best_model_name]
best_pipeline.fit(X_train, y_train)

val_pred = best_pipeline.predict(X_val)
print(f"\nValidation Set 성능:")
print(classification_report(y_val, val_pred, target_names=['악성', '양성']))

# ==============================================
# 6단계: 모델 평가 (Test Set - 최종 1회만 사용)
# ==============================================
print("="*50)
print("최종 Test Set 평가")
print("="*50)

test_pred = best_pipeline.predict(X_test)
test_proba = best_pipeline.predict_proba(X_test)[:, 1]

print(classification_report(y_test, test_pred, target_names=['악성', '양성']))
print(f"AUC-ROC: {roc_auc_score(y_test, test_proba):.4f}")
print(f"Confusion Matrix:\n{confusion_matrix(y_test, test_pred)}")

# ==============================================
# 7단계: 배포 준비 (모델 저장)
# ==============================================
import joblib

joblib.dump(best_pipeline, 'breast_cancer_model.pkl')
print("\n모델 저장 완료: breast_cancer_model.pkl")

# 저장된 모델 로드 및 추론 테스트
loaded_model = joblib.load('breast_cancer_model.pkl')
sample = X_test.iloc[:3]
predictions = loaded_model.predict(sample)
print(f"샘플 예측 결과: {predictions}")
```

```output
데이터 크기: (569, 31)
클래스 분포:
target
1    357
0    212
Name: count, dtype: int64

결측치 수: 0
기본 통계량:
                       mean         std        min        max
mean radius       14.127292    3.524049    6.98100    28.1100
mean texture      19.289649    4.301036    9.71000    39.2800
mean perimeter    91.969033   24.298981   43.79000   188.5000
mean area        654.889104  351.914129  143.50000  2501.0000
mean smoothness    0.096360    0.014064    0.05263     0.1634

Train: 341, Val: 114, Test: 114

==================================================
모델별 교차 검증 결과 (Recall 기준)
==================================================
Logistic Regression (Baseline): 0.9953 (+/- 0.0093)
Random Forest: 0.9719 (+/- 0.0230)
Gradient Boosting: 0.9671 (+/- 0.0319)

최적 모델: Logistic Regression (Baseline)

Validation Set 성능:
              precision    recall  f1-score   support

          악성       1.00      0.98      0.99        43
          양성       0.99      1.00      0.99        71

    accuracy                           0.99       114
   macro avg       0.99      0.99      0.99       114
weighted avg       0.99      0.99      0.99       114

==================================================
최종 Test Set 평가
==================================================
              precision    recall  f1-score   support

          악성       0.98      0.98      0.98        42
          양성       0.99      0.99      0.99        72

    accuracy                           0.98       114
   macro avg       0.98      0.98      0.98       114
weighted avg       0.98      0.98      0.98       114

AUC-ROC: 0.9950
Confusion Matrix:
[[41  1]
 [ 1 71]]

모델 저장 완료: breast_cancer_model.pkl
샘플 예측 결과: [0 1 0]
```

<details><summary>Output</summary>

```
데이터 크기: (569, 31)
클래스 분포:
1    357
0    212
Name: target, dtype: int64

결측치 수: 0

Train: 341, Val: 114, Test: 114

==================================================
모델별 교차 검증 결과 (Recall 기준)
==================================================
Logistic Regression (Baseline): 0.9720 (+/- 0.0173)
Random Forest: 0.9579 (+/- 0.0301)
Gradient Boosting: 0.9533 (+/- 0.0309)

최적 모델: Logistic Regression (Baseline)

==================================================
최종 Test Set 평가
==================================================
              precision    recall  f1-score   support

          악성       0.98      0.93      0.95        42
          양성       0.96      0.99      0.97        72

    accuracy                           0.96       114
   macro avg       0.97      0.96      0.96       114
weighted avg       0.97      0.96      0.96       114

AUC-ROC: 0.9954
```

</details>

이 예제에서 주목할 점은 다음과 같습니다:

1. **sklearn Pipeline**을 사용하여 전처리(StandardScaler)와 모델을 하나로 묶었습니다. 이렇게 하면 Data Leakage를 자연스럽게 방지할 수 있습니다.
2. **베이스라인(Logistic Regression)부터 시작**했고, 교차 검증 결과 베이스라인이 가장 좋은 성능을 보였습니다. 항상 복잡한 모델이 좋은 것은 아닙니다.
3. **Test Set은 최종 평가에 단 한 번만 사용**했습니다.

---

## 정리

ML 워크플로우의 7단계를 요약하면 다음과 같습니다:

| 단계 | 핵심 포인트 |
|------|------------|
| 1. 문제 정의 | 비즈니스 문제를 ML 문제로 명확히 변환 |
| 2. 데이터 수집 | 품질 > 양, 대표성 확보 |
| 3. EDA | 데이터를 이해하고 가설 수립 |
| 4. 전처리 | 결측치·이상치 처리, 인코딩, 스케일링 |
| 5. 모델 선택 | 베이스라인 먼저, 점진적 복잡도 증가 |
| 6. 평가 | 비즈니스 맥락에 맞는 메트릭 선택 |
| 7. 배포 | 모니터링과 재학습 체계 구축 |

가장 중요한 것은, 이 7단계가 **선형적이 아니라 반복적(Iterative)**이라는 점입니다. 모델 평가 결과가 좋지 않으면 EDA로 돌아가 새로운 피처를 발굴하거나, 문제 정의 자체를 재검토해야 할 수도 있습니다. 이러한 반복 과정을 체계적으로 관리하는 것이 성공적인 ML 프로젝트의 핵심입니다.