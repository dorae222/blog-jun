<!-- infographic-hero -->
![Regression Discontinuity and Instrumental Variables 핵심 요약](figures/infographic.svg)

*Figure: Regression Discontinuity and Instrumental Variables 한 장 요약 인포그래픽*

# RD와 IV: 임계점과 도구변수를 활용한 인과 추론

랜덤화 실험(RCT)이 항상 가능하다면 인과 추론은 쉽다. 그러나 현실에서는 윤리적·실용적 이유로 직접 개입하기 어려운 경우가 많다. 이때 활용하는 두 가지 강력한 준실험(quasi-experiment) 방법이 **회귀 불연속 설계(Regression Discontinuity, RD)**와 **도구변수(Instrumental Variables, IV)**다. Goldfarb, Tucker & Wang(2022)의 디지털 마케팅 인과 추론 강의를 토대로 두 방법의 원리, 가정, 한계를 체계적으로 살펴본다.

---

## Part A: 회귀 불연속 설계 (Regression Discontinuity)

### 1. 핵심 개념

회귀 불연속 설계는 **임계값(cutoff/threshold)** 주변에서 처치 여부가 불연속적으로 변하는 상황을 자연 실험으로 활용한다. 핵심 아이디어는 다음과 같다: 임계값 바로 위와 바로 아래의 개체들은 **관측되지 않은 특성이 거의 동일**하다고 볼 수 있으므로, 이 두 집단을 비교하면 인과 효과를 측정할 수 있다.

예를 들어 장학금 기준이 80점이라면, 79점과 81점의 학생들은 능력이나 노력에서 큰 차이가 없을 가능성이 높다. 그러나 한 집단은 장학금을 받고 다른 집단은 받지 못한다. 이 차이가 순수 처치 효과가 된다.

### 2. 실제 예시: 취업 교육 프로그램

취업 교육 코스 수강 자격 기준이 **시험 점수 50점**이라고 하자. 50점 이상이면 프로그램에 참여하고, 50점 미만이면 참여하지 못한다. 연구자가 관심 있는 질문은: *이 프로그램이 실제로 소득(Y)을 높이는가?*

단순 비교(프로그램 참여자 vs 비참여자)는 선택 편향(selection bias)이 발생한다. 시험을 더 잘 보는 사람이 원래 더 높은 소득 잠재력을 가질 수 있기 때문이다. 그러나 임계값 50점 **근처**에서 보면, 49점과 51점의 응시자는 거의 같은 능력을 갖는다. 이 국소적 비교를 통해 프로그램의 인과 효과를 추정할 수 있다.

### 3. 수학적 표현

RD 추정의 기본 모형은 다음과 같다:

$$Y_{it} = \beta_1 I(Z_{it} \geq \bar{z}) + X_{it}\beta + \mu_i + \tau_t + \epsilon_{it}$$

- $Y_{it}$: 결과 변수 (소득)
- $Z_{it}$: 실행 변수(running variable) (시험 점수)
- $\bar{z}$: 임계값 (50점)
- $I(Z_{it} \geq \bar{z})$: 처치 지시 변수 (1이면 처치, 0이면 대조)
- $X_{it}$: 공변량 벡터
- $\mu_i$: 개체 고정효과
- $\tau_t$: 시간 고정효과
- $\epsilon_{it}$: 오차항

$\beta_1$은 임계값 근처에서의 **LATE(Local Average Treatment Effect)**, 즉 임계값 근방 개체들에 대한 평균 처치 효과를 의미한다. 이는 전체 모집단에 대한 ATE(Average Treatment Effect)와 다를 수 있음에 유의해야 한다.

### 4. 핵심 가정

RD가 인과 효과를 식별하려면 두 가지 조건이 필요하다:

**가정 1: 임계값의 외생성(Exogeneity of Threshold)**
임계값 $\bar{z}$ 자체가 임의적으로(arbitrarily) 설정되어야 한다. 임계값이 특정 집단에 유리하게 조작되었다면, 임계값 근처 비교의 신뢰성이 무너진다.

**가정 2: 조작 불가능성(Non-manipulation)**
개체들이 임계값 근처에서 연속적으로 분포해야 하며, 임계값을 전략적으로 넘거나 피하도록 실행 변수를 조작하는 행위가 없어야 한다. 만약 학생들이 의도적으로 딱 50점을 넘도록 시험을 봤다면, 50점 바로 위 집단은 더 이상 무작위적이지 않다.

또한 임계값을 제외하고 다른 모든 변수들은 임계값 근처에서 **연속적**이어야 한다 ( 즉, 처치 이외의 다른 것이 임계값에서 갑자기 변하면 안 된다.

### 5. Sharp RD vs Fuzzy RD

| 구분 | Sharp RD | Fuzzy RD |
|------|---------|----------|
| 처치 결정 | 임계값 기준으로 100% 결정 | 임계값이 처치 확률에만 영향 |
| 예시 | 점수 50점 이상 → 반드시 수강 | 점수 50점 이상 → 수강 확률 증가 |
| 추정 방법 | 직접 불연속 비교 | IV 방식으로 처리 (임계값이 도구변수) |
| 해석 | 임계값에서의 순수 처치 효과 | LATE (준수자 집단의 처치 효과) |

Fuzzy RD는 임계값을 **도구변수**로 사용하는 IV 방법과 연결된다 ) 이 점이 Part B와의 중요한 연결 고리다.

### 6. 검증: McCrary Density Test

RD 가정의 핵심인 조작 불가능성을 검증하는 대표적 방법이 **McCrary Density Test**다. 아이디어는 간단하다: 만약 개체들이 실행 변수를 조작하지 않았다면, 임계값 근처에서 실행 변수의 분포가 **연속적**이어야 한다.

임계값 근처에서 밀도 함수(density function)에 불연속이 관찰된다면 ( 예를 들어 50점 이상 학생이 비정상적으로 많다면 ) 이는 조작의 증거가 된다. 이를 시각적으로 확인하거나 통계적 검정으로 확인할 수 있다.

추가적으로, 임계값 근처에서 **공변량 균형(covariate balance)**을 확인하는 것도 중요하다. 인구통계학적 특성, 과거 소득 등이 임계값에서 불연속이 없다면, 두 집단이 실제로 비슷하다는 증거가 된다.

---

## Part B: 도구변수 (Instrumental Variables)

### 7. 내생성(Endogeneity) 문제

OLS 회귀에서 인과 추론이 실패하는 가장 흔한 이유는 **내생성(endogeneity)**이다. 설명 변수 $x$와 오차항 $\epsilon$이 상관될 때 발생하며, 세 가지 원인이 있다:

**(1) 역인과관계(Reverse Causality)**: $x$가 $y$에 영향을 주는 동시에 $y$도 $x$에 영향을 준다. 예: 광고비를 많이 쓰면 매출이 늘고, 매출이 많으면 광고비도 늘린다.

**(2) 누락 변수 편향(Omitted Variable Bias)**: $x$와 $y$ 모두에 영향을 미치는 변수 $u$를 모형에 포함하지 못할 때 발생한다. 예: 학력은 소득과 임금 모두에 영향을 미치는 숨겨진 변수일 수 있다.

**(3) 측정 오류(Measurement Error)**: 독립 변수가 오차를 포함하여 측정될 때 계수 추정이 편향된다 (감쇠 편향, attenuation bias).

이 세 가지 문제가 있으면 OLS 추정량은 일치성을 잃고, 결과를 인과적으로 해석할 수 없다.

### 8. 도구변수의 3가지 조건

좋은 도구변수 $z$가 되려면 세 가지 조건을 동시에 만족해야 한다:

**(1) 관련성(Relevance)**
$$\text{Cov}(z_i, x_i) \neq 0$$
도구변수 $z$는 내생변수 $x$와 강한 상관관계를 가져야 한다. 상관이 너무 약하면 '약한 도구변수(weak instrument)' 문제가 발생하여 추정량이 불안정해진다.

**(2) 배제 조건(Exclusion Restriction)**
$$\text{Cov}(z_i, \epsilon_i) = 0$$
도구변수 $z$는 결과 변수 $y$에 대해 **오직 $x$를 통해서만** 영향을 미쳐야 한다. $z$가 $x$ 이외의 경로로 $y$에 영향을 주는 경우, 배제 조건이 위반되어 IV 추정이 편향된다. 이 조건은 직접 검증할 수 없으며, 이론적 논증에 의존해야 한다.

**(3) 외생성(Exogeneity)**
$z$는 잠재적 혼란 변수와 무관해야 한다. 즉, 도구변수 자체가 외생적으로(exogenously) 결정되어야 한다.

이 세 조건 중 하나라도 실패하면 IV 추정은 신뢰할 수 없게 된다.

### 9. 2SLS (Two-Stage Least Squares)

도구변수를 실제로 적용하는 대표적 방법이 **2단계 최소제곱(Two-Stage Least Squares, 2SLS)**이다:

**1단계 (First Stage)**: 내생변수 $x_i$를 도구변수 $z_i$와 통제변수 $W_i$로 회귀한다:

$$x_i = \gamma z_i + \theta W_i + \eta_i$$

이 단계에서 $\hat{x}_i$를 구한다. $\hat{x}_i$는 $z_i$의 외생적 변동만을 반영하므로, 내생성이 제거된 $x$의 대리변수가 된다.

**2단계 (Second Stage)**: 1단계에서 얻은 예측값 $\hat{x}_i$를 사용하여 $y_i$를 회귀한다:

$$y_i = \beta \hat{x}_i + \varphi W_i + \epsilon_i$$

$\hat{x}_i$는 $z_i$의 외생적 변동만 담고 있으므로, 이 단계에서 추정된 $\beta$는 **내생성이 제거된 순수 인과 효과**다.

2SLS의 핵심: 원래의 $x_i$가 아니라 외생적 변동 부분 $\hat{x}_i$만으로 $y$를 설명하기 때문에 내생성 문제를 해결한다.

### 10. 축약형 회귀 (Reduced Form)

2SLS에서 두 단계를 결합하면 **축약형(reduced form)** 방정식을 도출할 수 있다:

$$y_i = \beta \gamma z_i + (\beta \theta + \varphi) W_i + \text{error}$$

축약형은 도구변수 $z_i$가 결과 변수 $y_i$에 미치는 총효과(reduced-form effect)를 나타낸다. IV 추정량은 직관적으로 다음과 같이 표현된다:

$$\hat{\beta}_{IV} = \frac{\text{reduced-form coefficient}}{\text{first-stage coefficient}} = \frac{\partial y / \partial z}{\partial x / \partial z}$$

이는 도구변수가 결과에 미치는 효과를 도구변수가 내생변수에 미치는 효과로 나눈 것으로, 내생변수 한 단위 증가의 인과 효과를 추출한다.

### 11. 실패 사례: 바람 세기와 SNS 네트워크

IV의 배제 조건 실패 사례로 자주 언급되는 예시가 있다. 연구자가 SNS 친구 관계(X)가 정치 참여(Y)에 미치는 영향을 측정하고 싶다고 하자. 바람 세기(wind speed)를 도구변수로 제안할 수 있다 ( 바람이 강한 날 야외 활동이 줄어 온라인 활동(SNS)이 늘어 친구 관계가 형성될 수 있다는 논리다.

그러나 여기서 배제 조건이 실패할 수 있다. 바람이 강한 날 사람들이 집에 머물며 뉴스를 더 많이 보거나, 날씨 자체가 기분에 영향을 미쳐 정치 참여를 직접 바꿀 수 있기 때문이다. 즉, **바람 세기 → 정치 참여** 경로가 SNS 친구 수를 경유하지 않고도 존재할 수 있어 배제 조건이 성립하지 않는다.

이처럼 창의적인 도구변수를 찾더라도 배제 조건의 타당성을 이론적으로 엄밀하게 논증해야 한다.

### 12. 강건성 검사: 약한 도구변수 진단

**F-statistic (First-stage F-stat)**은 도구변수의 강도를 진단하는 핵심 지표다:

$$H_0: \gamma = 0 \quad (\text{도구변수가 내생변수와 무관})$$

관례적으로 **F-statistic > 10**이면 강한 도구변수(strong instrument)로 판단한다. Staiger & Stock(1997)이 제안한 이 기준보다 낮으면 '약한 도구변수(weak instrument)' 문제가 발생한다.

약한 도구변수의 문제:
- IV 추정량이 OLS 추정량 방향으로 편향됨
- 표준오차가 크게 증가하여 통계적 검정력 저하
- 2SLS가 아닌 LIML(Limited Information Maximum Likelihood) 사용을 고려해야 함

도구변수가 여러 개일 때는 **Sargan-Hansen J-test**(과잉 식별 검정)로 배제 조건의 일관성을 부분적으로 검증할 수 있다. 단, 모든 도구변수가 동시에 배제 조건을 위반하면 이 검정도 탐지하지 못한다.

### 13. Python 구현: statsmodels IV2SLS

```python
import numpy as np
import pandas as pd
from linearmodels.iv import IV2SLS
import statsmodels.api as sm

np.random.seed(42)
n = 1000

# 도구변수 (외생적)
z = np.random.randn(n)

# 내생변수 (도구변수 + 내생성 혼란)
endogeneity = np.random.randn(n)  # 공통 혼란 요인
x = 0.7 * z + 0.5 * endogeneity + np.random.randn(n) * 0.3

# 결과변수 (x를 통한 효과 + 내생성)
y = 2.0 * x + 0.8 * endogeneity + np.random.randn(n) * 0.5

df = pd.DataFrame({'y': y, 'x': x, 'z': z})
df['const'] = 1

# --- 1단계: First-Stage 회귀 및 F-stat 확인 ---
first_stage = sm.OLS(df['x'], df[['const', 'z']]).fit()
print("=== First-Stage F-statistic ===")
print(f"F-stat: {first_stage.fvalue:.2f}  (기준: > 10)")
print(first_stage.summary().tables[1])

# --- 2SLS 추정 ---
model = IV2SLS(
    dependent=df['y'],
    exog=df[['const']],
    endog=df[['x']],
    instruments=df[['z']]
)
result = model.fit(cov_type='robust')

print("\n=== 2SLS 추정 결과 ===")
print(result.summary)

# --- 비교: OLS (편향된 추정) ---
ols_result = sm.OLS(df['y'], df[['const', 'x']]).fit()
print("\n=== OLS 추정 (편향) ===")
print(f"OLS coefficient on x: {ols_result.params['x']:.3f}")
print(f"2SLS coefficient on x: {result.params['x']:.3f}")
print(f"실제 계수: 2.000")
```

<!-- Execution error: ModuleNotFoundError: No module named 'linearmodels' -->

**주요 해석 포인트**:
- OLS는 내생성으로 인해 2.0보다 높은 계수를 추정 (양의 내생성 편향)
- 2SLS는 도구변수를 통해 외생적 변동만 활용하여 2.0에 가까운 추정
- First-stage F-stat이 10 이상임을 반드시 보고해야 함

---

## RD와 IV의 비교 및 연결

| 항목 | RD | IV |
|------|----|----|  
| 핵심 아이디어 | 임계값 근처의 불연속성 활용 | 외생적 도구로 내생성 제거 |
| 추정 대상 | LATE (임계값 근처 집단) | LATE (준수자 집단) |
| 주요 가정 | 임계값 외생성, 비조작성 | 관련성, 배제 조건, 외생성 |
| 검증 방법 | McCrary Density Test | First-stage F-stat, J-test |
| Fuzzy RD | IV로 처리 가능 | RD를 IV의 특수 사례로 볼 수 있음 |

두 방법은 **국소 평균 처치 효과(LATE)**를 식별한다는 공통점이 있다. Fuzzy RD에서 임계값을 도구변수로 사용하는 것처럼, RD와 IV는 상호 보완적으로 활용될 수 있다.

---

## 마치며

RD와 IV는 현대 인과 추론의 핵심 도구다. RD는 임계값 근처라는 국소적 공간에서 자연 실험을 찾아내고, IV는 외생적 충격을 활용하여 내생성을 우회한다. 두 방법 모두 가정의 타당성 검증이 필수적이며, 가정이 무너지면 추정 결과의 인과적 해석도 무너진다.

Goldfarb, Tucker & Wang(2022)이 강조하듯, 디지털 마케팅 환경에서도 이 방법들은 강력하게 적용된다 ) 플랫폼 알고리즘 변경(임계값), 외생적 쇼크(도구변수) 등 다양한 준실험 상황이 존재하기 때문이다. 핵심은 *방법을 아는 것*이 아니라 *어떤 상황에서 어떤 가정이 정당화되는지 판단하는 것*이다.