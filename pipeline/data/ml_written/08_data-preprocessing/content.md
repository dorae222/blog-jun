## 개요: Garbage In, Garbage Out

머신러닝에서 자주 인용되는 격언이 있습니다. **"Garbage In, Garbage Out(GIGO)"** — 쓰레기를 입력하면 쓰레기가 출력된다는 뜻입니다. 아무리 정교한 모델을 설계하더라도, 입력 데이터의 품질이 낮으면 모델의 예측 성능은 기대 이하로 떨어질 수밖에 없습니다.

실무 경험에 따르면 데이터 사이언티스트는 전체 업무 시간의 **60~80%**를 데이터 수집, 정제, 전처리에 사용합니다. 이 사실은 데이터 전처리가 얼마나 중요한 작업인지를 단적으로 보여줍니다.

데이터 전처리(Data Preprocessing)는 크게 다음 단계로 구성됩니다:

1. **탐색적 데이터 분석(EDA)**: 데이터의 구조와 분포를 파악
2. **결측치 처리**: 누락된 값을 적절히 대체하거나 제거
3. **이상치 탐지 및 처리**: 비정상적인 값을 식별하고 처리
4. **데이터 분리**: 학습/검증/테스트 셋으로 올바르게 분할
5. **스케일링 및 변환**: 모델 학습에 적합한 형태로 변환

이 글에서는 각 단계를 이론과 Python 코드를 함께 다루겠습니다.

---

## 탐색적 데이터 분석(EDA)

**탐색적 데이터 분석(Exploratory Data Analysis, EDA)**은 데이터를 본격적으로 처리하기 전에 그 구조, 분포, 이상 패턴을 파악하는 과정입니다. EDA를 충분히 수행하지 않으면 잘못된 전처리를 적용하거나 중요한 패턴을 놓칠 수 있습니다.

### 데이터 형태 파악

가장 먼저 할 일은 데이터의 기본적인 형태와 통계를 확인하는 것입니다.

```python
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# 데이터 기본 정보 확인
print(df.shape)        # (행, 열) 수
print(df.dtypes)       # 각 열의 데이터 타입
df.info()              # 타입 + 결측치 개수 + 메모리 사용량

# 수치형 변수 기술 통계
df.describe()
# count, mean, std, min, 25%, 50%, 75%, max

# 범주형 변수 빈도 확인
df['category_col'].value_counts()
df['category_col'].value_counts(normalize=True)  # 비율로 확인

# 결측치 현황
df.isnull().sum()
df.isnull().mean() * 100  # 결측 비율(%) 확인
```

<!-- Execution error: FileNotFoundError: [Errno 2] No such file or directory: 'data.csv' -->

`df.describe()`가 반환하는 수치들을 해석할 때는 다음에 주목합니다:
- **mean과 50%(중앙값)의 차이**: 크면 분포가 치우쳐 있음(왜도)
- **std(표준편차)**가 mean보다 크면 분산이 매우 큰 변수
- **min/max**가 극단적이면 이상치 가능성

### 분포 시각화

수치형 변수의 분포를 이해하는 데는 **히스토그램**과 **박스플롯**이 핵심입니다.

```python
import matplotlib.pyplot as plt
import seaborn as sns

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

# 히스토그램: 분포의 형태(정규분포 여부, 왜도 등) 파악
axes[0].hist(df['feature'], bins=50, edgecolor='black')
axes[0].set_title('Histogram')

# 박스플롯: 중앙값, IQR, 이상치를 한눈에 확인
axes[1].boxplot(df['feature'].dropna())
axes[1].set_title('Box Plot')
plt.show()

# 두 변수의 관계: 산점도
plt.figure(figsize=(8, 6))
plt.scatter(df['feature_x'], df['feature_y'], alpha=0.3)
plt.xlabel('feature_x')
plt.ylabel('feature_y')
plt.title('Scatter Plot')
plt.show()
```

<!-- Execution error: NameError: name 'df' is not defined -->

### 상관관계 히트맵

변수들 사이의 선형 관계를 파악하려면 **피어슨 상관계수(Pearson Correlation)**를 히트맵으로 시각화합니다.

$$r = \frac{\sum_{i=1}^{n}(x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n}(x_i - \bar{x})^2} \cdot \sqrt{\sum_{i=1}^{n}(y_i - \bar{y})^2}}$$

$r$ 값은 $[-1, 1]$ 범위이며, $|r| > 0.8$ 이상이면 다중공선성(Multicollinearity)을 의심합니다.

```python
corr_matrix = df.select_dtypes(include=[np.number]).corr()

plt.figure(figsize=(12, 10))
sns.heatmap(
    corr_matrix,
    annot=True,
    fmt='.2f',
    cmap='RdBu_r',
    center=0,
    square=True
)
plt.title('Feature Correlation Heatmap')
plt.tight_layout()
plt.show()
```

<!-- Execution error: NameError: name 'df' is not defined -->

---

## 결측치(Missing Values) 처리

![결측치 처리 방법 비교: 삭제, 단순 대체, 예측 기반 대체의 효과](figures/missing_value_handling.png)
*결측치 처리 전략: MCAR/MAR/MNAR 유형에 따른 삭제, 단순 대체, 예측 기반 대체 방법의 적용 기준과 효과를 비교한다.*

결측치를 무조건 평균으로 채우거나 해당 행을 삭제하는 것은 위험할 수 있습니다. 결측치의 **발생 메커니즘**을 먼저 이해해야 올바른 처리 전략을 선택할 수 있습니다.

### MCAR / MAR / MNAR 구분

Rubin(1976)은 결측 메커니즘을 세 가지로 분류했습니다:

| 유형 | 설명 | 예시 | 처리 전략 |
|------|------|------|-----------|
| **MCAR** (Missing Completely At Random) | 결측이 다른 변수와 완전히 무관 | 설문지 일부가 물에 젖어 훼손 | 단순 대체 또는 삭제 가능 |
| **MAR** (Missing At Random) | 결측이 관측된 다른 변수에 의존 | 나이가 많을수록 소득을 기재하지 않는 경향 | 예측 기반 대체 권장 |
| **MNAR** (Missing Not At Random) | 결측이 결측된 값 자체에 의존 | 우울증 환자가 우울 점수를 응답하지 않음 | 가장 처리가 어려움, 도메인 지식 필요 |

MCAR인지 테스트하는 간단한 방법은 **Little's MCAR Test**를 사용하거나, 결측 여부를 이진 변수로 만들어 다른 변수와의 상관을 확인하는 것입니다.

### 단순 대체 (Simple Imputation)

```python
from sklearn.impute import SimpleImputer

# 수치형: 평균/중앙값 대체
imputer_mean = SimpleImputer(strategy='mean')      # 정규 분포에 적합
imputer_median = SimpleImputer(strategy='median')  # 왜도가 클 때 권장

# 범주형: 최빈값 대체
imputer_mode = SimpleImputer(strategy='most_frequent')

# 상수값으로 대체 (예: 0 또는 'Unknown')
imputer_const = SimpleImputer(strategy='constant', fill_value=0)

X_imputed = imputer_median.fit_transform(X_train)
```

**주의**: 평균 대체는 분산을 과소 추정하고 상관 구조를 왜곡합니다. 결측 비율이 5% 이하일 때만 단순 대체를 권장합니다.

### 예측 기반 대체 (Predictive Imputation)

결측 비율이 높거나 MAR 상황에서는 다른 변수를 이용해 결측값을 **예측**하는 방법이 더 정확합니다.

```python
from sklearn.impute import KNNImputer, IterativeImputer

# KNN Imputation: K개의 가장 유사한 샘플의 평균으로 대체
knn_imputer = KNNImputer(n_neighbors=5, weights='uniform')
X_knn = knn_imputer.fit_transform(X_train)

# IterativeImputer (MICE 방식): 각 변수를 나머지 변수로 반복 회귀하여 대체
from sklearn.experimental import enable_iterative_imputer  # 실험적 기능 활성화
iter_imputer = IterativeImputer(
    max_iter=10,      # 반복 횟수
    random_state=42,
    estimator=None    # None이면 BayesianRidge 사용
)
X_iter = iter_imputer.fit_transform(X_train)
```

**IterativeImputer**는 R의 `mice` 패키지와 유사한 방식으로, 여러 변수 간의 관계를 모델링하여 결측값을 채웁니다. 시간이 오래 걸리지만 정확도가 높습니다.

### 삭제 전략

- **Listwise Deletion (완전 케이스 분석)**: 결측치가 하나라도 있는 행을 모두 삭제합니다 (`df.dropna()`). 데이터 손실이 크지만 구현이 단순합니다.
- **Pairwise Deletion**: 분석에 사용하는 변수 쌍에 결측이 없는 관측치만 사용합니다. 상관 행렬 계산 등에 사용됩니다.

일반적으로 결측 비율이 **40% 이상**인 변수는 삭제를 검토하고, **5% 이하**는 단순 대체, 그 사이는 예측 기반 대체를 고려합니다.

### 결측 여부를 피처로 활용

MNAR 상황에서는 결측 자체가 유의미한 신호일 수 있습니다. 이 경우 **결측 지시 변수(Missing Indicator)**를 추가적인 피처로 활용합니다.

```python
from sklearn.impute import MissingIndicator

# 결측 여부를 이진 피처로 추가
indicator = MissingIndicator(features='missing-only')
missing_flags = indicator.fit_transform(X_train)
# X_train에 missing_flags를 concat하여 피처로 추가
```

예를 들어, 대출 심사 데이터에서 소득 정보를 제출하지 않은 것 자체가 신용 위험의 신호일 수 있습니다.

---

## 이상치(Outlier) 탐지와 처리

이상치는 다른 관측치들과 현저히 다른 값을 가진 데이터 포인트입니다. 이상치가 실제 오류인지, 아니면 중요한 현상(예: 사기 거래)인지를 구분하는 것이 핵심입니다.

### IQR 방법

**사분위수 범위(Interquartile Range, IQR)** 방법은 분포 가정이 없는 비모수적 방법입니다.

$$IQR = Q_3 - Q_1$$

$$\text{정상 범위} = [Q_1 - 1.5 \cdot IQR,\ Q_3 + 1.5 \cdot IQR]$$

이 범위를 벗어나는 값을 이상치로 간주합니다. 박스플롯의 수염(Whisker)이 바로 이 기준을 시각화한 것입니다.

```python
Q1 = df['feature'].quantile(0.25)
Q3 = df['feature'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

outliers = df[(df['feature'] < lower_bound) | (df['feature'] > upper_bound)]
print(f"이상치 개수: {len(outliers)}")
```

<!-- Execution error: NameError: name 'df' is not defined -->

### Z-score 방법

데이터가 정규분포를 따를 때는 **Z-score**를 사용합니다.

$$z = \frac{x - \mu}{\sigma}$$

$|z| > 3$ 인 값은 전체 분포에서 상위/하위 0.15% 이내에 해당하므로 이상치로 판단합니다.

```python
from scipy import stats

z_scores = np.abs(stats.zscore(df['feature'].dropna()))
outlier_mask = z_scores > 3
print(f"이상치 비율: {outlier_mask.mean():.2%}")
```

<!-- Execution error: NameError: name 'df' is not defined -->

**주의**: Z-score는 평균과 표준편차 자체가 이상치에 영향을 받기 때문에, 이상치가 많은 데이터에서는 수정된 Z-score(Modified Z-score)를 사용하는 것이 더 강건합니다.

$$\tilde{z} = \frac{0.6745 \cdot (x - \tilde{x})}{MAD}, \quad MAD = \text{median}(|x_i - \tilde{x}|)$$

### Isolation Forest

**Isolation Forest**는 이상치를 "고립(Isolate)"하기 어렵다는 직관에 기반한 앙상블 방법입니다. 정상 데이터는 고립시키기 위해 더 많은 분할이 필요하고, 이상치는 적은 분할로 쉽게 고립됩니다. 이상치 점수는 고립에 필요한 분할 깊이(Path Length)의 역수입니다.

```python
from sklearn.ensemble import IsolationForest

isolation_forest = IsolationForest(
    contamination=0.05,  # 예상 이상치 비율 (도메인 지식 활용)
    random_state=42,
    n_estimators=100
)

# -1: 이상치, 1: 정상
predictions = isolation_forest.fit_predict(X_train)
outlier_mask = predictions == -1
print(f"탐지된 이상치: {outlier_mask.sum()}개")
```

<!-- Execution error: NameError: name 'X_train' is not defined -->

Isolation Forest는 다변량(Multivariate) 이상치를 탐지할 수 있다는 점에서 IQR, Z-score보다 강력합니다. 자세한 내용은 [[anomaly-detection]]에서 다룹니다.

### 처리 방법

이상치를 탐지한 후에는 다음 전략 중 하나를 선택합니다:

| 방법 | 설명 | 적합한 상황 |
|------|------|-------------|
| **제거** | 이상치 행을 삭제 | 데이터 입력 오류가 명확할 때 |
| **대체** | IQR 경계값 또는 중앙값으로 교체 (Winsorizing) | 이상치를 완전히 제거하기 어려울 때 |
| **변환** | 로그, Box-Cox, Yeo-Johnson 변환 | 분포의 왜도를 줄이고 싶을 때 |
| **유지** | 이상치를 그대로 사용 | 이상치가 실제 현상이고 모델이 강건할 때 |

```python
from scipy.stats import boxcox
from sklearn.preprocessing import PowerTransformer

# 로그 변환 (양수 데이터에만 적용)
df['feature_log'] = np.log1p(df['feature'])  # log(1+x)로 0값 처리

# Box-Cox 변환 (최적 lambda 자동 탐색, 양수만 가능)
transformed, lmbda = boxcox(df['feature'] + 1)  # +1로 0 방지

# Yeo-Johnson 변환 (음수도 처리 가능)
pt = PowerTransformer(method='yeo-johnson')
df['feature_yj'] = pt.fit_transform(df[['feature']])

# Winsorizing: 이상치를 경계값으로 대체
df['feature_clipped'] = df['feature'].clip(
    lower=lower_bound,
    upper=upper_bound
)
```

---

## 데이터 분리 전략

올바른 데이터 분리는 모델 성능을 공정하게 평가하기 위한 필수 요건입니다. 분리 전략을 잘못 적용하면 **데이터 누수(Data Leakage)**가 발생하여 실제 성능보다 낙관적인 결과를 얻게 됩니다.

### 랜덤 분리 vs 계층화 분리

기본적인 랜덤 분리는 클래스 불균형이 있을 때 각 분할에 클래스 비율이 다를 수 있습니다. **계층화 분리(Stratified Split)**는 각 분할에서 클래스 비율을 원본과 동일하게 유지합니다.

```python
from sklearn.model_selection import train_test_split

# 랜덤 분리
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 계층화 분리 (분류 문제에서 권장)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 학습/검증/테스트 3분할
X_temp, X_test, y_temp, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
X_train, X_val, y_train, y_val = train_test_split(
    X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp  # 0.25 * 0.8 = 0.2
)
print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
```

<!-- Execution error: NameError: name 'X' is not defined -->

### 시계열 데이터의 분리 주의점

시계열 데이터를 랜덤 분리하면 **미래 데이터로 과거를 예측**하는 상황이 발생합니다. 반드시 시간 순서를 지켜서 분리해야 합니다.

```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, val_idx in tscv.split(X):
    X_train_fold, X_val_fold = X[train_idx], X[val_idx]
    y_train_fold, y_val_fold = y[train_idx], y[val_idx]
    # 시간 순서: train의 마지막 시점 < val의 첫 시점 보장
```

### Data Leakage 방지

데이터 누수는 테스트 시점에는 사용할 수 없는 정보가 학습에 사용될 때 발생합니다. 가장 흔한 실수는 **분리 전에 전처리를 적용**하는 것입니다.

```python
# 잘못된 방법: 전체 데이터로 fit 후 분리 -> 누수 발생!
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)  # 테스트 데이터 정보가 스케일링에 포함됨
X_train, X_test = train_test_split(X_scaled, test_size=0.2)

# 올바른 방법: 분리 후 학습 데이터로만 fit
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)  # 학습 데이터로만 fit
X_test_scaled = scaler.transform(X_test)         # 테스트 데이터는 transform만
```

---

![스케일링 방법 비교: StandardScaler, MinMaxScaler, RobustScaler의 변환 결과](figures/scaling_comparison.png)
*스케일링 비교: 동일한 데이터에 StandardScaler, MinMaxScaler, RobustScaler를 적용한 결과를 비교하여 이상치가 있을 때의 차이를 보여준다.*

## Python 전처리 파이프라인

지금까지 다룬 내용을 sklearn의 `Pipeline`과 `ColumnTransformer`를 이용해 하나의 견고한 파이프라인으로 구성합니다. 파이프라인을 사용하면 누수 방지와 코드 재사용성을 동시에 달성할 수 있습니다.

```python
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, PowerTransformer
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report

# --- 1. 데이터 로드 및 EDA ---
df = pd.read_csv('data.csv')
print("데이터 형태:", df.shape)
print("\n결측치 현황 (%):\n", df.isnull().mean() * 100)
print("\n기술 통계:\n", df.describe())

# --- 2. 데이터 분리 (전처리 전에 먼저 분리) ---
target_col = 'target'
feature_cols = [c for c in df.columns if c != target_col]
X = df[feature_cols]
y = df[target_col]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# --- 3. 피처 타입 구분 ---
numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
print(f"\n수치형 피처: {numeric_features}")
print(f"범주형 피처: {categorical_features}")

# --- 4. 이상치 처리 (학습 데이터에서만 탐지) ---
def remove_outliers_iqr(X_df, cols, factor=1.5):
    """IQR 방법으로 이상치를 경계값으로 대체(Winsorizing)"""
    X_clean = X_df.copy()
    for col in cols:
        Q1 = X_clean[col].quantile(0.25)
        Q3 = X_clean[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - factor * IQR
        upper = Q3 + factor * IQR
        X_clean[col] = X_clean[col].clip(lower, upper)
    return X_clean

X_train_clean = remove_outliers_iqr(X_train, numeric_features)

# --- 5. 수치형 변수 처리 파이프라인 ---
numeric_pipeline = Pipeline(steps=[
    ('imputer', KNNImputer(n_neighbors=5)),       # 결측치: KNN 대체
    ('transformer', PowerTransformer(method='yeo-johnson')),  # 분포 정규화
    ('scaler', StandardScaler()),                  # 표준화
])

# --- 6. 범주형 변수 처리 파이프라인 ---
categorical_pipeline = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),  # 결측치: 최빈값 대체
    ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
])

# --- 7. ColumnTransformer로 통합 ---
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_pipeline, numeric_features),
        ('cat', categorical_pipeline, categorical_features),
    ],
    remainder='drop'  # 지정되지 않은 컬럼 제거
)

# --- 8. 전체 ML 파이프라인 구성 ---
full_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', RandomForestClassifier(n_estimators=100, random_state=42)),
])

# --- 9. 교차 검증으로 성능 평가 ---
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
cv_scores = cross_val_score(full_pipeline, X_train_clean, y_train, cv=cv, scoring='f1_weighted')
print(f"\n교차 검증 F1-Score: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

# --- 10. 최종 학습 및 테스트 평가 ---
full_pipeline.fit(X_train_clean, y_train)
y_pred = full_pipeline.predict(X_test)  # 테스트 데이터는 자동으로 transform만 적용
print("\n=== 테스트 셋 최종 평가 ===")
print(classification_report(y_test, y_pred))
```

<!-- Execution error: FileNotFoundError: [Errno 2] No such file or directory: 'data.csv' -->

이 파이프라인의 핵심 장점은 다음과 같습니다:

- **누수 방지**: 학습/테스트 분리를 가장 먼저 수행하고, 파이프라인이 `fit`과 `transform`을 자동으로 분리 적용
- **재사용성**: 동일한 파이프라인 객체로 새로운 데이터를 전처리할 수 있음
- **일관성**: 모든 전처리 단계가 순서대로 보장되어 실수를 방지

---

## 정리

데이터 전처리는 모델의 복잡성을 높이는 것보다 훨씬 큰 성능 개선을 가져올 수 있습니다. 핵심 내용을 정리합니다:

1. **EDA를 충분히 수행하라**: 데이터를 모르면 잘못된 전처리를 적용하게 됩니다.
2. **결측 메커니즘(MCAR/MAR/MNAR)을 파악하라**: 결측의 원인에 따라 대체 전략이 달라집니다.
3. **이상치는 제거보다 이해가 먼저다**: 오류인지, 실제 현상인지를 도메인 지식으로 판단하세요.
4. **분리를 먼저, 전처리는 나중에**: 데이터 누수를 방지하는 가장 중요한 원칙입니다.
5. **sklearn Pipeline으로 자동화하라**: 코드의 재사용성과 안정성을 동시에 확보합니다.

> **다음 글 안내**: 전처리된 데이터에서 더 유의미한 피처를 만드는 방법은 [[feature-engineering]]을 참고하세요. 클래스 불균형 문제를 다루는 방법은 [[imbalanced-data]]에서 다룹니다.

## 관련 문서

- [[ml-workflow]] - ML 워크플로우 전체 개요
- [[feature-engineering]] - 피처 엔지니어링
- [[imbalanced-data]] - 불균형 데이터 처리
- [[sklearn-pipeline]] - scikit-learn Pipeline 심화
- [[anomaly-detection]] - 이상치 탐지 심화
- [[cross-validation]] - 교차 검증 전략