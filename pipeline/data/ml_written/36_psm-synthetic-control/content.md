# PSM, Synthetic Control, Heckman Selection: 선택 편향 보정 3종 세트

## 0. 왜 3가지 방법이 필요한가

인과추론의 이상적인 상황은 완벽한 외생적 변이(Exogenous Variation)를 가진 자연실험이나 RD, IV가 존재하는 경우다. 그러나 현실에서는 이런 조건을 충족하는 상황이 드물다. 처치(Treatment)를 받은 집단과 받지 않은 집단이 처음부터 다를 때, 즉 **선택 편향(Selection Bias)**이 존재할 때 단순 비교는 인과효과를 왜곡한다.

이 포스트에서는 외생적 변이가 불완전하거나 없을 때 선택 편향을 보정하는 3가지 방법을 체계적으로 비교한다:

- **Part A**: Propensity Score Matching (PSM) ( 관찰 가능한 변수 기반 매칭
- **Part B**: Synthetic Control Method (SCM) ) 가상의 합성 통제군 구성
- **Part C**: Heckman Selection Model ( Inverse Mills Ratio로 자기선택 편향 보정

---

## Part A: Propensity Score Matching (PSM)

### 1. 개념과 직관

**PSM(Propensity Score Matching)**의 핵심 아이디어는 단순하다. 처치집단(Treated)과 통제집단(Control)이 처음부터 서로 다른 특성을 가지고 있다면, **처치 여부만 다르고 나머지 특성은 최대한 유사한 쌍**을 만들어 비교하자는 것이다.

예를 들어 온라인 광고 캠페인의 효과를 측정한다고 하자. 광고를 본 사람(처치집단)과 보지 않은 사람(통제집단)은 연령, 소득, 인터넷 사용 패턴 등에서 체계적으로 다를 수 있다. 이때 단순히 두 집단의 구매율을 비교하면 광고 효과가 아니라 이러한 배경 차이가 반영된다.

PSM은 이 문제를 **성향 점수(Propensity Score)**라는 단일 스칼라값으로 요약해 해결한다. 수많은 공변량(Covariates)의 차원을 하나의 숫자로 압축함으로써 매칭이 실용적이 된다.

### 2. Propensity Score 계산

Propensity Score는 관찰된 공변량 $X_i$가 주어졌을 때 처치를 받을 조건부 확률이다:

$$\text{Propensity Score} = e(X_i) = \Pr[D_i = 1 \mid X_i]$$

여기서 $D_i$는 처치 여부(1=처치, 0=통제)이다. 이 확률은 일반적으로 **로지스틱 회귀(Logistic Regression)**로 추정한다:

$$e(X_i) = F(\beta_0 + X_i\beta) = \frac{1}{1 + e^{-(\beta_0 + X_i\beta)}}$$

로지스틱 회귀 외에도 Probit, 랜덤 포레스트, 부스팅 등의 모델로 Propensity Score를 추정할 수 있다. 다만 추정 모델 자체는 인과 추론의 목적이 아니므로, 예측 성능보다는 공변량을 충분히 포함하는지가 더 중요하다.

### 3. 매칭 과정

Propensity Score를 추정한 후 매칭 알고리즘을 적용한다. 가장 흔한 방식은 **1:1 Nearest Neighbor Matching**이다:

1. 처치집단의 각 대상 $i$에 대해 Propensity Score $\hat{e}(X_i)$를 계산한다.
2. 통제집단에서 $|\hat{e}(X_i) - \hat{e}(X_j)|$가 가장 작은 대상 $j$를 찾아 쌍으로 묶는다.
3. 허용 오차(Caliper)를 설정해 Propensity Score 차이가 너무 크면 매칭을 거부하기도 한다.

매칭 방식에는 이 외에도 다양한 변형이 있다:
- **k:1 Matching**: 처치 1명에 통제 k명을 매칭 (분산 감소)
- **Kernel Matching**: 모든 통제 대상을 가중 평균으로 활용
- **Stratification**: Propensity Score 구간별로 층화(Stratification) 후 집단 내 비교
- **Inverse Probability Weighting (IPW)**: 매칭 대신 가중치 $1/e(X_i)$ 또는 $1/(1-e(X_i))$를 부여

### 4. 균형 검증 (Balance Check)

매칭 후 반드시 두 집단이 실제로 균형을 이루었는지 확인해야 한다. **Standardized Mean Difference (SMD)**가 일반적인 기준이다:

$$\text{SMD} = \frac{\bar{X}_{\text{treated}} - \bar{X}_{\text{control}}}{\sqrt{(s^2_{\text{treated}} + s^2_{\text{control}})/2}}$$

$|\text{SMD}| < 0.1$ (일부 기준에서는 0.2)이면 두 집단이 균형을 이루었다고 본다. Love Plot으로 매칭 전후 SMD를 시각화하는 것이 표준 관행이다.

### 5. PSM의 핵심 가정과 한계

PSM은 **조건부 독립 가정(Conditional Independence Assumption, CIA)** 또는 **무시 가능성(Ignorability)**에 의존한다:

$$\{Y_i(0), Y_i(1)\} \perp D_i \mid X_i$$

이는 관찰된 공변량 $X_i$를 조건으로 하면 처치 배정이 잠재적 결과(Potential Outcomes)와 독립이라는 가정이다. **핵심 한계**: 관찰되지 않은 교란변수(Unobserved Confounders)가 존재하면 이 가정이 깨진다. PSM은 **관찰 가능한 차이만** 통제할 수 있다.

---

## Part B: Synthetic Control Method (SCM)

### 5. 개념과 적용 상황

**Synthetic Control Method(SCM)**는 Abadie & Gardeazabal(2003)이 바스크 지방 테러리즘의 경제적 비용을 분석하며 제안한 방법이다. PSM이 개인 수준에서 매칭을 수행한다면, SCM은 **집합 단위(국가, 지역, 기업 등)**를 대상으로 한다.

**적용 상황**: 처치 단위가 소수일 때(예: 특정 국가 1개가 정책을 도입), 유사한 통제 단위가 여럿 있을 때, 처치 이전 기간의 데이터가 충분할 때. 예를 들어 캘리포니아가 담배세를 올린 효과를 측정할 때, 담배세를 올리지 않은 다른 주들을 조합해 "담배세가 없었더라면의 캘리포니아"를 만들 수 있다.

### 6. 합성 통제군 구성

SCM의 핵심은 **처치 이전 기간(Pre-treatment Period)** 동안의 결과 변수를 가장 잘 재현하는 통제 단위들의 가중 평균을 찾는 것이다.

처치 단위를 $j=1$, $J$개의 통제 단위를 $j=2, \ldots, J+1$이라 하자. 합성 통제군은 가중치 벡터 $W = (w_2, \ldots, w_{J+1})^T$로 정의된다. 최적 가중치는 다음 최적화 문제로 구한다:

$$\min_{W} \sum_{t=1}^{T_0} \left(Y_{1t} - \sum_{j=2}^{J+1} w_j Y_{jt}\right)^2$$

제약 조건: $w_j \geq 0$, $\sum_{j=2}^{J+1} w_j = 1$

여기서 $T_0$는 처치 이전 기간의 수, $Y_{1t}$는 처치 단위의 $t$기 결과 변수다. 결과 변수뿐 아니라 다른 공변량도 함께 매칭하도록 확장할 수 있다.

최적 가중치 $\hat{W}^*$로 구성된 합성 통제군의 처치 후 결과:

$$\hat{Y}_{1t}^{\text{synth}} = \sum_{j=2}^{J+1} \hat{w}_j^* Y_{jt}, \quad t > T_0$$

처치 효과 추정치는 실제 처치 단위와 합성 통제군의 차이다:

$$\hat{\tau}_t = Y_{1t} - \hat{Y}_{1t}^{\text{synth}}, \quad t > T_0$$

### 7. 통계적 유의성: Permutation Test

SCM은 표본 수가 적어 전통적인 표준 오차를 계산하기 어렵다. 대신 **Placebo Test(순열 검정)**을 사용한다:

1. 처치를 받지 않은 각 통제 단위에 대해서도 마치 그 단위가 처치를 받은 것처럼 SCM을 적용한다.
2. 처치 단위의 사후 추정 오차가 통제 단위들의 사후 오차 분포에서 얼마나 극단적인지를 본다.
3. 이를 통해 처치 효과의 유의성을 비모수적으로 평가한다.

**SCM의 장점**: 처치 이전 기간의 추세가 잘 맞으면 처치 이후의 반사실(Counterfactual)을 신뢰성 있게 구성한다. 합성 가중치가 투명하게 공개되므로 해석이 용이하다.

**SCM의 한계**: 처치 이전 기간이 충분히 길어야 한다. 통제 풀(Donor Pool)에 적합한 단위가 없으면 매칭이 어렵다. 처치 효과가 시간에 따라 변하는 것은 추적 가능하지만, 처치 이전 기간 균형이 맞지 않으면 결과를 신뢰하기 어렵다.

---

## Part C: Selection Bias Correction ) Heckman Selection Model

### 8. 자기선택 편향 문제

PSM과 SCM은 처치 배정이 관찰 가능한 변수에 의해서만 결정된다고 가정한다. 그러나 현실에는 대상이 **스스로 처치를 선택(Self-selection)**하는 경우가 많다. 이때 관찰되지 않은 요인이 처치 선택과 결과 변수 모두에 영향을 미치면, 단순 회귀분석은 편향된 추정치를 낳는다.

**OTT 서비스 예시**: OTT 플랫폼에서 유료 멤버십 구독자만 콘텐츠를 다운로드할 수 있다고 하자. 다운로드가 재구독에 미치는 효과를 측정하려면 다운로드를 하지 않은 비구독자(통제집단)가 필요하다. 그러나 비구독자는 다운로드 기회 자체가 없으므로 관찰된 데이터가 없다. 이를 **표본 선택 편향(Sample Selection Bias)**이라 한다.

또 다른 예: 대학 진학이 임금에 미치는 효과. 대학에 진학하는 사람들은 그렇지 않은 사람들과 관찰되지 않는 동기, 능력, 가정 환경에서 체계적으로 다를 수 있다.

### 9. Heckman의 2단계 추정법 (Tobit-2 Model)

**James Heckman(1979)**은 이 문제를 두 방정식 체계로 모형화했다.

**선택 방정식 (Selection Equation)**:

$$Y_i^{S*} = \beta_0 + X_i^S \beta + \epsilon_i^S$$

$$D_i = \begin{cases} 1 & \text{if } Y_i^{S*} > 0 \\ 0 & \text{if } Y_i^{S*} \leq 0 \end{cases}$$

$Y_i^{S*}$는 처치를 선택하려는 잠재적 성향이고, $D_i$는 실제 처치 여부다. $X_i^S$는 처치 선택에 영향을 미치는 변수들이다. 이 방정식은 Probit으로 추정한다.

**결과 방정식 (Outcome Equation)**:

$$Y_i^{O*} = \gamma_0 + X_i^O \gamma + \epsilon_i^O$$

$Y_i^O$는 처치집단에서만 관찰된다. 만약 $\epsilon_i^S$와 $\epsilon_i^O$가 상관되어 있다면($\text{Cov}(\epsilon^S, \epsilon^O) = \sigma_{SO} \neq 0$), OLS로 결과 방정식만 추정하면 편향이 발생한다.

**핵심 통찰**: 처치집단에서만 결과를 관찰한다는 것은, $D_i = 1$, 즉 $Y_i^{S*} > 0$인 조건 하에서 결과를 보는 것이다. 이때:

$$E[Y_i^O \mid D_i = 1, X_i^O] = \gamma_0 + X_i^O \gamma + E[\epsilon_i^O \mid \epsilon_i^S > -\beta_0 - X_i^S\beta]$$

마지막 항이 바로 선택 편향을 만드는 부분이다. 이중 정규 분포 가정 하에서 이 조건부 기댓값은 **Inverse Mills Ratio(역 밀스 비율)**로 표현된다.

### 10. Inverse Mills Ratio (IMR)

$z_i = \beta_0 + X_i^S\hat{\beta}$로 정의하면, IMR은:

$$\text{IMR}(z_i) = \lambda(z_i) = \frac{\phi(z_i)}{\Phi(z_i)}$$

여기서 $\phi(\cdot)$는 표준 정규 분포의 밀도함수(PDF), $\Phi(\cdot)$는 누적분포함수(CDF)다.

**보정된 결과 방정식**은 IMR을 추가적인 설명변수로 포함한다:

$$Y_i^O = \gamma_0 + X_i^O \gamma + \delta \cdot \text{IMR}(z_i) + \eta_i$$

여기서 $\delta = \sigma_{SO}/\sigma_O$는 선택 편향의 크기를 나타내는 계수다. $\delta$가 유의하면 선택 편향이 존재한다는 증거이며, IMR을 포함한 추정치 $\hat{\gamma}$는 편향이 보정된 인과 효과다.

**2단계 추정 절차**:
1. **1단계**: Probit으로 선택 방정식 추정 → $\hat{\beta}$ 획득 → $\text{IMR}(z_i)$ 계산
2. **2단계**: 처치집단($D_i = 1$)에 대해 IMR을 포함한 결과 방정식을 OLS로 추정

2단계 표준 오차는 1단계 추정의 불확실성을 반영하지 않으므로, 부트스트랩 표준 오차를 사용하는 것이 권장된다.

### 11. Tobit-5 Model: 통제집단도 결과를 관찰하는 경우

**Tobit-2**는 처치집단에서만 결과를 관찰하는 경우다. 반면 **Tobit-5(Switching Regression)**는 처치집단과 통제집단 모두 결과를 관찰하지만, 두 집단의 결과 방정식이 다를 수 있는 경우다.

$$Y_i = D_i \cdot Y_i^{O,1} + (1 - D_i) \cdot Y_i^{O,0}$$

$$Y_i^{O,1} = \gamma_0^1 + X_i^O \gamma^1 + \delta^1 \cdot \lambda(z_i) + \eta_i^1 \quad (D_i = 1)$$
$$Y_i^{O,0} = \gamma_0^0 + X_i^O \gamma^0 - \delta^0 \cdot \frac{\phi(z_i)}{1 - \Phi(z_i)} + \eta_i^0 \quad (D_i = 0)$$

통제집단의 IMR은 $\phi(z_i)/(1-\Phi(z_i))$임에 주의하라. 두 집단 모두에서 결과를 추정하므로 처치 효과의 이질성도 파악할 수 있다.

### 12. 배제 조건 (Exclusion Restriction)

Heckman 모델이 잘 작동하려면 **배제 조건(Exclusion Restriction)**을 만족하는 변수가 필요하다. 배제 조건을 만족하는 변수 $Z_i$는:
- 선택 방정식 $X_i^S$에 포함 (처치 선택에 영향)
- 결과 방정식 $X_i^O$에서는 제외 (결과 변수에 직접 영향 없음)

예를 들어 대학 진학의 임금 효과를 분석할 때, 거주지에서 대학까지의 거리는 진학 여부에는 영향을 주지만 임금에는 직접 영향을 주지 않는다고 볼 수 있다. 적절한 배제 변수가 없으면 모델 식별이 함수 형태(Functional Form)에만 의존하게 되어 추정이 불안정해진다.

---

## 3가지 방법 비교

| 항목 | PSM | Synthetic Control | Heckman Selection |
|------|-----|-------------------|-------------------|
| **핵심 가정** | 조건부 독립(CIA) | 처치 전 추세 재현 가능 | 이중 정규 분포, 배제 조건 |
| **식별 전략** | 관찰 변수 기반 매칭 | 가중 평균 합성 통제군 | Inverse Mills Ratio 추가 |
| **처치 단위** | 개인/관측치 수준 | 집합 단위(국가/지역/기업) | 개인/관측치 수준 |
| **데이터 요건** | 다양한 공변량, 겹침(Overlap) | 충분한 처치 전 기간 데이터 | 선택 방정식 추정 가능 |
| **주요 한계** | 비관찰 교란변수 통제 불가 | 도너 풀 품질에 민감 | 배제 변수 확보 어려움 |
| **활용 상황** | 관찰 연구, 마케팅 분석 | 정책 평가(지역/국가 단위) | 자기선택, 표본 절단 문제 |
| **유의성 검정** | 표준 통계 검정 | Placebo(순열) 검정 | 부트스트랩 표준 오차 |

---

## Python 구현 예시

### PSM 구현

```python
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

np.random.seed(42)
n = 1000

# 공변량 생성
age = np.random.normal(35, 10, n)
income = np.random.normal(50000, 15000, n)
online_hours = np.random.normal(4, 2, n).clip(0)

# 처치 배정: 공변량에 의존 (선택 편향 의도적 생성)
logit = -3 + 0.03 * age + 0.00002 * income + 0.2 * online_hours
treat_prob = 1 / (1 + np.exp(-logit))
treatment = np.random.binomial(1, treat_prob)

# 잠재적 결과
Y0 = 10 + 0.5 * age + 0.00005 * income + np.random.normal(0, 2, n)
Y1 = Y0 + 3  # 진짜 처치 효과 = 3
Y = np.where(treatment == 1, Y1, Y0)

df = pd.DataFrame({
    'age': age, 'income': income, 'online_hours': online_hours,
    'treatment': treatment, 'outcome': Y
})

# 1단계: Propensity Score 추정
X_covs = ['age', 'income', 'online_hours']
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[X_covs])

ps_model = LogisticRegression()
ps_model.fit(X_scaled, df['treatment'])
df['ps'] = ps_model.predict_proba(X_scaled)[:, 1]

print(f"처치집단 평균 PS: {df.loc[df.treatment==1, 'ps'].mean():.3f}")
print(f"통제집단 평균 PS: {df.loc[df.treatment==0, 'ps'].mean():.3f}")

# 2단계: 1:1 Nearest Neighbor Matching
treated = df[df.treatment == 1].copy()
control = df[df.treatment == 0].copy()

nn = NearestNeighbors(n_neighbors=1, metric='euclidean')
nn.fit(control[['ps']])
distances, indices = nn.kneighbors(treated[['ps']])

matched_control = control.iloc[indices.flatten()].copy()

# 3단계: ATT 추정 (Average Treatment Effect on the Treated)
att = (treated['outcome'].values - matched_control['outcome'].values).mean()
print(f"\nPSM 추정 ATT: {att:.3f} (진짜 효과: 3.000)")

# 균형 검증: SMD
for col in X_covs:
    mean_t = treated[col].mean()
    mean_c = matched_control[col].mean()
    std_pool = np.sqrt((treated[col].std()**2 + matched_control[col].std()**2) / 2)
    smd = abs(mean_t - mean_c) / std_pool
    print(f"  {col} SMD: {smd:.3f} {'(OK)' if smd < 0.1 else '(주의)'}")
```

```output
처치집단 평균 PS: 0.521
통제집단 평균 PS: 0.438

PSM 추정 ATT: 3.095 (진짜 효과: 3.000)
  age SMD: 0.014 (OK)
  income SMD: 0.007 (OK)
  online_hours SMD: 0.004 (OK)
```

### Heckman Selection Model 구현

```python
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

np.random.seed(42)
n = 2000

# 공변량
X_outcome = np.random.normal(0, 1, n)   # 결과 방정식 변수
Z_exclusion = np.random.normal(0, 1, n) # 배제 변수 (선택에만 영향)

# 오차항: 선택-결과 간 상관 (rho = 0.7)
rho = 0.7
errors = np.random.multivariate_normal(
    mean=[0, 0],
    cov=[[1, rho], [rho, 1]],
    size=n
)
eps_selection = errors[:, 0]
eps_outcome = errors[:, 1]

# 선택 방정식: D=1이면 처치 관찰
latent_selection = 0.5 * X_outcome + 0.8 * Z_exclusion + eps_selection
D = (latent_selection > 0).astype(int)

# 결과 방정식 (처치집단에서만 관찰)
Y_star = 2.0 + 1.5 * X_outcome + eps_outcome
Y = np.where(D == 1, Y_star, np.nan)

df = pd.DataFrame({'X': X_outcome, 'Z': Z_exclusion, 'D': D, 'Y': Y})
print(f"처치집단 비율: {D.mean():.3f} ({D.sum()}명 관찰)")

# 편향된 추정 (OLS만 사용, 선택 편향 무시)
df_treated = df[df.D == 1].copy()
X_ols = sm.add_constant(df_treated['X'])
ols_model = sm.OLS(df_treated['Y'], X_ols).fit()
print(f"\n편향된 OLS 추정 (X 계수): {ols_model.params['X']:.4f} (진짜값: 1.5)")

# 1단계: Probit으로 선택 방정식 추정
X_probit = sm.add_constant(df[['X', 'Z']])
probit_model = sm.Probit(df['D'], X_probit).fit(disp=0)

# IMR 계산
z_hat = probit_model.predict(X_probit, linear=True)  # 선형 지수
imr = stats.norm.pdf(z_hat) / stats.norm.cdf(z_hat)   # phi(z) / Phi(z)
df['IMR'] = imr

# 2단계: IMR을 포함한 결과 방정식 OLS
df_treated = df[df.D == 1].copy()
X_heckman = sm.add_constant(df_treated[['X', 'IMR']])
heckman_model = sm.OLS(df_treated['Y'], X_heckman).fit()

print(f"Heckman 보정 추정 (X 계수): {heckman_model.params['X']:.4f} (진짜값: 1.5)")
print(f"IMR 계수 (delta): {heckman_model.params['IMR']:.4f}")
print(f"IMR 계수 유의성 p-value: {heckman_model.pvalues['IMR']:.4f}")
if heckman_model.pvalues['IMR'] < 0.05:
    print("  → 선택 편향이 유의하게 존재함. Heckman 보정 필요.")
```

<!-- Execution error: ModuleNotFoundError: No module named 'statsmodels' -->

---

## 요약

외생적 변이가 불완전한 상황에서 인과효과를 추정하는 3가지 접근법은 각기 다른 가정과 적용 상황을 가진다.

**PSM**은 관찰 가능한 공변량으로 처치집단과 통제집단을 매칭하는 방법으로, 개인 수준 데이터가 풍부하고 교란변수를 대부분 관찰할 수 있을 때 유용하다. 그러나 비관찰 교란변수에는 무력하며, 사전에 균형 검증을 반드시 수행해야 한다.

**Synthetic Control**은 집합 단위(국가, 지역)의 정책 평가에 특화된 방법으로, 가중 평균으로 합성 통제군을 구성해 처치 이전 추세를 재현한다. 처치 단위가 소수일 때 효과적이며, Placebo Test로 유의성을 비모수적으로 평가한다.

**Heckman Selection Model**은 자기선택 또는 표본 절단 문제에 대응하는 방법으로, 선택 방정식과 결과 방정식을 분리해 IMR을 통해 선택 편향을 명시적으로 보정한다. 배제 조건을 만족하는 변수 확보가 핵심이며, IMR 계수의 유의성이 선택 편향 존재 여부를 알려준다.

세 방법 모두 관찰 연구의 근본적 한계인 비관찰 교란변수 문제를 완전히 해결하지는 못한다. 연구 설계 단계에서 어떤 가정이 가장 현실적으로 성립하는지를 먼저 판단하고, 그에 맞는 방법을 선택하는 것이 중요하다.