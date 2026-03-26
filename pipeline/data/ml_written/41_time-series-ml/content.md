## 1. 개요: 시계열 데이터란 무엇인가

시계열(Time Series)은 시간 순서에 따라 기록된 데이터의 수열이다. 주가, 기온, 트래픽 로그, 월별 매출처럼 "언제 측정했는가"가 데이터의 의미를 결정한다. 일반적인 ML에서는 샘플 간에 독립 동일 분포(i.i.d.)를 가정하지만, 시계열에서는 **현재 값이 과거 값에 의존**한다. 이 자기상관(autocorrelation) 구조를 무시하면 모델은 데이터의 핵심 패턴을 놓친다.

시계열 데이터에는 세 가지 핵심 패턴이 있다.

- **추세(Trend)**: 장기적으로 증가하거나 감소하는 방향성. 예) 매년 증가하는 전자상거래 거래량.
- **계절성(Seasonality)**: 고정된 주기로 반복되는 패턴. 예) 연말마다 급증하는 소매 매출.
- **자기상관(Autocorrelation)**: 현재 값이 직전 시점들의 값과 상관관계를 갖는 성질. 오늘 기온과 어제 기온은 강한 양의 상관을 보인다.

이 세 가지 구조를 체계적으로 분리하고 모델링하는 것이 시계열 분석의 핵심이다.

---

![시계열 분해: 원본 시계열을 추세, 계절성, 잔차 성분으로 분리한 결과](figures/time_series_decomposition.png)
*시계열 분해: 원본 데이터에서 장기 추세, 주기적 계절성, 불규칙 잔차를 분리하면 각 패턴을 독립적으로 분석할 수 있다.*

## 2. 시계열 분해 (Time Series Decomposition)

시계열을 분해하면 각 패턴을 독립적으로 분석하고 예측할 수 있다. 분해 방식에는 두 가지 주요 모형이 있다.

**가법 모형(Additive Model)**

$$Y_t = T_t + S_t + R_t$$

추세, 계절성, 잔차가 서로 더해지는 구조다. 계절 변동 폭이 시간에 따라 일정할 때 적합하다. 예를 들어 여름 전력 소비량의 피크가 매년 비슷한 절대량만큼 증가하는 경우다.

**승법 모형(Multiplicative Model)**

$$Y_t = T_t \times S_t \times R_t$$

추세가 커질수록 계절 변동 폭도 비례해서 커질 때 사용한다. 매출이 성장하면서 연말 피크의 절대값도 같이 커지는 경우가 전형적이다. 로그 변환을 적용하면 승법 모형을 가법 모형으로 바꿀 수 있다.

Python에서는 `statsmodels`의 `seasonal_decompose` 함수로 빠르게 분해할 수 있다.

```python
from statsmodels.tsa.seasonal import seasonal_decompose
import pandas as pd

result = seasonal_decompose(series, model='additive', period=12)
result.plot()
```

---

## 3. 정상성 (Stationarity)

대부분의 고전 시계열 모델은 **정상성(Stationarity)**을 가정한다. 정상 시계열은 시간이 지나도 통계적 성질이 변하지 않는다.

**약 정상성(Weak Stationarity)** 조건:
1. 평균이 시간에 무관하게 일정: $E[Y_t] = \mu$
2. 분산이 시간에 무관하게 유한: $\text{Var}(Y_t) = \sigma^2 < \infty$
3. 자기공분산이 절대 시점이 아닌 시차(lag)에만 의존: $\text{Cov}(Y_t, Y_{t+k}) = \gamma(k)$

실제 데이터는 대부분 추세나 계절성 때문에 비정상(non-stationary)이다. **단위근(Unit Root)**이 존재하면 시계열은 확률적 추세를 가지며 비정상이다.

### ADF 검정 (Augmented Dickey-Fuller Test)

단위근 검정의 가장 대표적인 방법이다. 귀무가설($H_0$)은 "단위근이 존재한다(비정상)", 대립가설($H_1$)은 "단위근이 없다(정상)"이다. p-value가 0.05 미만이면 정상 시계열로 판단한다.

```python
from statsmodels.tsa.stattools import adfuller

result = adfuller(series)
print(f'ADF Statistic: {result[0]:.4f}')
print(f'p-value: {result[1]:.4f}')
# p-value < 0.05 → 정상 시계열
```

<!-- Execution error: ModuleNotFoundError: No module named 'statsmodels' -->

### 차분 (Differencing)으로 정상성 확보

비정상 시계열은 차분으로 정상화한다. 1차 차분은 $\Delta Y_t = Y_t - Y_{t-1}$이다. 차분 횟수 $d$가 ARIMA의 두 번째 파라미터가 된다.

$$\Delta^d Y_t = (1 - B)^d Y_t$$

여기서 $B$는 후방이동 연산자(backshift operator)로 $B Y_t = Y_{t-1}$을 의미한다.

---

![자기상관 함수: 다양한 시차(lag)에 따른 자기상관 계수와 편자기상관 함수 시각화](figures/autocorrelation.png)
*자기상관 함수: ACF와 PACF 플롯을 통해 시계열의 자기상관 구조를 파악하고 적절한 모델 차수를 결정할 수 있다.*

## 4. 자기상관 (Autocorrelation)

### ACF (AutoCorrelation Function)

ACF는 시계열과 자기 자신의 시차(lag) $k$ 버전 사이의 상관계수다.

$$\rho(k) = \frac{\text{Cov}(Y_t, Y_{t-k})}{\text{Var}(Y_t)}$$

ACF 플롯에서 lag $k$에서 유의한 스파이크가 존재하면, 해당 lag까지 MA(Moving Average) 항이 필요함을 시사한다.

### PACF (Partial AutoCorrelation Function)

PACF는 중간 시차의 영향을 제거한 후, 시계열과 lag $k$ 버전 사이의 순수한 상관관계다. PACF 플롯에서 lag $p$까지 유의한 값이 있다면 AR(p) 모델이 적절함을 나타낸다.

**모수 결정 원칙**:
- ACF가 lag $q$ 이후 급격히 절단(cutoff) → MA($q$)
- PACF가 lag $p$ 이후 급격히 절단 → AR($p$)
- 두 함수 모두 점진적으로 감소 → ARMA 혼합 모델

```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 1, figsize=(10, 6))
plot_acf(series, lags=40, ax=axes[0])
plot_pacf(series, lags=40, ax=axes[1])
plt.tight_layout()
```

---

## 5. ARIMA 모델

ARIMA(Autoregressive Integrated Moving Average)는 시계열 예측의 고전적 표준 모델이다.

### AR(p): 자기회귀 모델

현재 값이 과거 $p$개 값의 선형 결합으로 결정된다.

$$y_t = c + \sum_{i=1}^{p} \phi_i y_{t-i} + \epsilon_t$$

$\phi_i$는 AR 계수, $\epsilon_t \sim N(0, \sigma^2)$는 백색 잡음이다.

### MA(q): 이동평균 모델

현재 값이 과거 $q$개 오차항의 선형 결합으로 결정된다.

$$y_t = c + \epsilon_t + \sum_{i=1}^{q} \theta_i \epsilon_{t-i}$$

$\theta_i$는 MA 계수다. AR과 달리 MA 모델은 오차의 파급 효과가 유한하게 끝난다.

### ARIMA(p, d, q)

비정상 시계열을 $d$회 차분하여 정상화한 뒤 ARMA$(p, q)$를 적합한다.

$$\phi(B)(1-B)^d y_t = c + \theta(B)\epsilon_t$$

여기서 $\phi(B) = 1 - \phi_1 B - \cdots - \phi_p B^p$, $\theta(B) = 1 + \theta_1 B + \cdots + \theta_q B^q$다.

### SARIMA: 계절성 확장

ARIMA에 계절 주기 $m$을 반영한 SARIMA$(p, d, q)(P, D, Q)_m$은 계절적 AR, MA, 차분 항을 추가한다. 예를 들어 월별 데이터라면 $m=12$를 사용한다.

```python
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX

# ARIMA 예시
model = ARIMA(train, order=(1, 1, 1))
result = model.fit()
forecast = result.forecast(steps=12)
print(result.summary())

# SARIMA 예시 (월별 데이터, 계절주기=12)
sarima_model = SARIMAX(train, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
sarima_result = sarima_model.fit(disp=False)
```

<!-- Execution error: ModuleNotFoundError: No module named 'statsmodels' -->

모수 선택은 AIC(Akaike Information Criterion) 또는 BIC(Bayesian Information Criterion)를 최소화하는 방향으로 진행한다. `pmdarima` 라이브러리의 `auto_arima`는 이 탐색을 자동화해준다.

---

## 6. Prophet (Facebook/Meta)

Prophet은 Meta(구 Facebook)에서 2017년 공개한 시계열 예측 라이브러리로, 비즈니스 현장의 시계열에 최적화되어 있다.

**Prophet의 분해 모형**:

$$y(t) = g(t) + s(t) + h(t) + \epsilon_t$$

- $g(t)$: 추세 함수. 선형 또는 로지스틱 성장 곡선으로 모델링.
- $s(t)$: 계절성 함수. 푸리에 급수(Fourier Series)로 표현.
- $h(t)$: 공휴일·이벤트 효과.
- $\epsilon_t$: 잔차 오차.

**Prophet의 강점**:
- 누락 데이터에 강건: 내부적으로 결측치를 처리.
- 이상치에 덜 민감: 추세 변화점(changepoint)을 자동 감지.
- 도메인 전문가가 직관적으로 파라미터를 조정 가능.
- 연간·주간·일간 계절성을 동시에 처리.

```python
from prophet import Prophet
import pandas as pd

# Prophet은 'ds'(날짜)와 'y'(값) 컬럼을 요구
df = pd.DataFrame({'ds': date_index, 'y': values})

model = Prophet(
    changepoint_prior_scale=0.05,  # 추세 유연성 조정
    seasonality_mode='multiplicative',  # 승법 계절성
    yearly_seasonality=True,
    weekly_seasonality=True
)

# 공휴일 효과 추가
model.add_country_holidays(country_name='KR')
model.fit(df)

# 미래 데이터프레임 생성 및 예측
future = model.make_future_dataframe(periods=90)  # 90일 예측
forecast = model.predict(future)

# 예측 구성 요소 시각화
fig = model.plot_components(forecast)
```

---

## 7. 시계열 교차 검증: Walk-Forward Validation

일반 ML에서는 데이터를 무작위로 분할해 교차 검증한다. 그러나 **시계열은 시간 순서를 반드시 지켜야** 한다. 미래 데이터를 학습에 사용하는 데이터 누출(data leakage)을 피해야 하기 때문이다.

**Walk-Forward Validation** (Rolling Origin Evaluation):
1. 초기 학습 윈도우로 모델 학습
2. 바로 다음 시점(또는 구간)을 예측
3. 학습 윈도우를 한 스텝 앞으로 이동
4. 위 과정을 반복하여 여러 예측값 수집
5. 전체 예측 오차의 평균으로 성능 평가

```python
from sklearn.model_selection import TimeSeriesSplit
import numpy as np

tscv = TimeSeriesSplit(n_splits=5)
errors = []

for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

    model = ARIMA(y_train, order=(1, 1, 1)).fit()
    pred = model.forecast(steps=len(y_test))
    mae = np.mean(np.abs(pred - y_test))
    errors.append(mae)

print(f'평균 MAE: {np.mean(errors):.4f}')
```

<!-- Execution error: NameError: name 'X' is not defined -->

평가 지표로는 MAE(Mean Absolute Error), RMSE(Root Mean Squared Error), MAPE(Mean Absolute Percentage Error)가 주로 사용된다. 단, MAPE는 실제값이 0에 가까울 때 발산하므로 SMAPE(Symmetric MAPE)를 대안으로 쓰기도 한다.

---

## 8. 실전 워크플로우 요약

시계열 분석의 표준 절차는 다음과 같다.

1. **탐색적 분석**: 시각화로 추세·계절성·이상치 파악
2. **정상성 검정**: ADF 검정 → 비정상이면 차분 적용
3. **ACF/PACF 분석**: ARIMA 모수 $(p, d, q)$ 후보 결정
4. **모델 적합**: ARIMA 또는 SARIMA 학습, AIC/BIC로 모수 선택
5. **잔차 진단**: 잔차가 백색 잡음인지 Ljung-Box 검정으로 확인
6. **예측 및 평가**: Walk-Forward Validation으로 일반화 성능 측정
7. **대안 고려**: 선형 패턴이 복잡하거나 누락 데이터가 많으면 Prophet 사용

복잡한 비선형 패턴이나 다변량 입력이 필요한 경우에는 LSTM, Temporal Fusion Transformer 같은 딥러닝 기반 모델로 확장하는 것도 좋은 선택이다.

---

## 핵심 정리

| 개념 | 핵심 포인트 |
|---|---|
| 정상성 | 평균·분산이 시간 불변. ADF 검정으로 확인 |
| 차분 | 비정상 시계열 → 정상화. 차분 횟수 = $d$ |
| ACF/PACF | MA 차수 $q$, AR 차수 $p$ 결정의 단서 |
| ARIMA$(p,d,q)$ | 가장 범용적인 고전 시계열 모델 |
| SARIMA | ARIMA에 계절 주기 추가 |
| Prophet | 비즈니스 시계열, 공휴일 효과, 누락 데이터에 강건 |
| Walk-Forward CV | 시계열 전용 교차 검증. 미래 정보 누출 방지 |
