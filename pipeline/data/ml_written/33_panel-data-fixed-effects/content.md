<!-- infographic-hero -->
![Panel Data and Fixed Effects Model 핵심 요약](figures/infographic.svg)

*Figure: Panel Data and Fixed Effects Model 한 장 요약 인포그래픽*

## 개요: 횡단면 데이터의 한계

인과 추론의 목표는 단순한 상관관계를 넘어 **진짜 원인-결과 관계**를 추정하는 것입니다. 그런데 현실에서 수집한 데이터에는 종종 우리가 관측하지 못한 혼란 변수(Confounders)가 숨어 있어, 단순 회귀만으로는 인과 효과를 정확히 추정할 수 없습니다.

**횡단면 데이터(Cross-Sectional Data)**는 특정 시점에 여러 대상을 관측한 데이터입니다. 예를 들어 기업별 가격과 판매량을 한 해에만 수집했다면, 아래와 같은 모형을 세울 수 있습니다:

$$\text{Sales}_i = \beta_0 + \beta_1 \text{Price}_i + \beta_2 \text{Advertising}_i + \epsilon_i$$

여기서 $i$는 개별 기업을 나타냅니다. 이 모형에는 세 가지 근본적인 한계가 있습니다:

1. **특정 시점만 반영**: 해당 연도에 특수한 외부 환경(경기 침체, 팬데믹 등)이 있었다면 추정 계수가 그 영향을 받습니다. 다른 연도에 동일 계수를 적용할 수 없습니다.
2. **연도별 특수 여건에 의존**: 관측되지 않은 시점별 공통 요인이 $\epsilon_i$에 섞여 계수 추정을 왜곡합니다.
3. **개체 이질성 미통제**: 기업마다 고유한 브랜드 파워, 입지, 경영 역량 같은 관측 불가 특성이 $\epsilon_i$에 섞여 들어갑니다. 이 요소들이 $\text{Price}_i$와 상관되어 있으면 $\hat{\beta}_1$은 편향(Bias)됩니다.

이 한계를 극복하는 핵심 도구가 **패널 데이터**와 **고정 효과 모형**입니다.

---

## 패널 데이터(Panel Data)

**패널 데이터**는 동일한 개체 $i$를 여러 시점 $t$에 걸쳐 반복 관측한 데이터입니다. 개체 차원과 시간 차원을 동시에 갖기 때문에 **종단 데이터(Longitudinal Data)**라고도 불립니다.

패널 데이터 모형의 기본 형태는 다음과 같습니다:

$$\text{Sales}_{it} = \beta_0 + \beta_1 \text{Price}_{it} + \beta_2 \text{Advertising}_{it-1} + \epsilon_{it}$$

첨자 $i$는 개체(기업), $t$는 시점(연도)를 나타냅니다. 횡단면 모형과 비교해 두 가지 변화가 눈에 띕니다.

### 시차(Lag) 변수

$\text{Advertising}_{it-1}$은 $t-1$기의 광고비를 나타내는 **시차 변수(Lagged Variable)**입니다. 광고 효과는 집행 즉시 나타나기보다 다음 기에 판매로 이어지는 경우가 많기 때문에, 시차를 명시적으로 모형에 포함합니다. 이를 통해 광고비와 판매량 사이의 역인과(Reverse Causality) 문제도 일부 완화할 수 있습니다.

### 변수의 첨자 유형

패널 데이터에서 변수는 첨자 유형에 따라 세 종류로 구분됩니다:

| 유형 | 첨자 | 예시 | 의미 |
|------|------|------|------|
| 개체·시점 변동 | $i, t$ | $\text{Price}_{it}$, $\text{Sales}_{it}$ | 개체마다, 시점마다 달라짐 |
| 개체 고유 | $i$만 | $\text{Listed}_i$ (상장 여부) | 시점이 바뀌어도 고정 |
| 시점 공통 | $t$만 | $\text{CPI}_t$ (소비자물가지수) | 모든 개체에 공통 적용 |

상장 여부($\text{Listed}_i$)는 한 번 상장하면 쉽게 바뀌지 않으므로 $i$ 첨자만 갖습니다. 소비자물가지수($\text{CPI}_t$)는 특정 개체와 무관하게 경제 전반에 적용되므로 $t$ 첨자만 갖습니다.

---

## 개체 고정 효과(Individual Fixed Effects) $\mu_i$

### 개념

기업마다 **관측되지 않는 고유한 특성**이 존재합니다. 예를 들어 어떤 기업은 브랜드 파워가 높아 같은 가격이라도 판매량이 기본적으로 더 높고, 어떤 기업은 입지 조건이 좋아 광고 없이도 자연스럽게 고객이 유입됩니다. 이러한 **개체 수준의 이질성**을 포착하는 것이 개체 고정 효과 $\mu_i$입니다.

$$\text{Sales}_{it} = \beta_1 \text{Price}_{it} + \beta_2 \text{Advertising}_{it-1} + \mu_i + \epsilon_{it}$$

$\mu_i$는 기업 $i$의 Sales 기본 수준을 결정하는 모든 관측 불가 요인의 합입니다. 이 항이 모형에 들어오면 $\beta_0$이 $\mu_i$로 대체되므로 공통 상수항은 제외됩니다.

### 개체 고정 변수의 흡수

중요한 성질이 있습니다. **개체에만 의존하는 변수($i$ 첨자만 가진 변수)는 $\mu_i$에 완전히 흡수됩니다.** 상장 여부 $\text{Listed}_i$를 예로 들면:

$$\text{Sales}_{it} = \beta_1 \text{Price}_{it} + \beta_3 \text{Listed}_i + \mu_i + \epsilon_{it}$$

$\text{Listed}_i$는 $\mu_i$와 마찬가지로 $i$에만 의존하므로, 이 둘을 구분할 수 없습니다. 결국 $\beta_3 \text{Listed}_i$는 $\mu_i$에 흡수되어 **$\text{Listed}_i$의 개별 효과를 식별할 수 없게 됩니다.** 이는 개체 고정 효과 모형의 근본적인 한계입니다 ( 시간이 지나도 변하지 않는 개체 속성의 효과는 추정할 수 없습니다.

---

## 시점 고정 효과(Time Fixed Effects) $\tau_t$

개체 이질성 외에도 **시점별 공통 충격**이 존재합니다. 금리 변동, 경기 사이클, 법·규제 변화, 글로벌 공급망 이슈 등은 특정 시점에 모든 기업에 동일하게 영향을 미칩니다. 이러한 **시점 수준의 이질성**을 포착하는 것이 시점 고정 효과 $\tau_t$입니다.

$$\text{Sales}_{it} = \beta_1 \text{Price}_{it} + \beta_2 \text{Advertising}_{it-1} + \tau_t + \epsilon_{it}$$

$\tau_t$는 시점 $t$의 모든 개체에 공통으로 적용되는 효과입니다. 개체 고정 변수와 마찬가지로, **시점에만 의존하는 변수($t$ 첨자만 가진 변수)는 $\tau_t$에 흡수됩니다.** $\text{CPI}_t$를 명시적으로 포함시키면 $\tau_t$와 구분이 불가능합니다.

---

## 양방향 고정 효과 모형(Two-Way Fixed Effects)

개체 고정 효과와 시점 고정 효과를 모두 포함한 모형을 **양방향 고정 효과 모형(Two-Way Fixed Effects Model, TWFE)**이라 합니다:

$$\boxed{\text{Sales}_{it} = \beta_1 \text{Price}_{it} + \beta_2 \text{Advertising}_{it-1} + \mu_i + \tau_t + \epsilon_{it}}$$

이 모형은 다음 두 가지 혼란 변수를 동시에 제거합니다:

- $\mu_i$: 관측 불가능한 개체별 고정 특성 (예: 브랜드 파워, 입지)
- $\tau_t$: 관측 불가능한 시점별 공통 충격 (예: 경기 변동, 정책 변화)

남는 오차 $\epsilon_{it}$는 개체-시점 쌍에 고유한 무작위 충격으로, 독립성·등분산성 등의 표준 OLS 가정을 만족해야 합니다.

### 모형의 식별 조건

양방향 고정 효과 모형에서 $\beta_1$과 $\beta_2$를 식별하려면 핵심 설명변수($\text{Price}_{it}$, $\text{Advertising}_{it-1}$)가 **$i$와 $t$ 양쪽 모두에 걸쳐 변동**해야 합니다. 개체 내 시간 변동이 없거나, 모든 시점에 동일한 값이라면 계수를 식별할 수 없습니다.

---

## 모형 해석

양방향 고정 효과 모형에서 추정된 계수의 해석 방식은 일반 회귀와 중요한 차이가 있습니다.

예를 들어 추정 결과가 $\hat{\beta}_1 = -0.68$이라고 하면:

> **"동일한 기업에서 동일한 시점 환경 하에, 가격이 1단위 상승할 때 Sales는 평균 0.68단위 감소한다."**

일반 횡단면 회귀의 해석과 달리, 고정 효과 모형의 계수는 **개체 내(Within) 변동**에 기반합니다. 즉, 기업 A와 기업 B를 비교하는 것이 아니라, 기업 A의 어느 해 가격이 다른 해에 비해 높을 때 판매량이 어떻게 달라지는가를 추정합니다.

이 해석은 두 가지 강점을 갖습니다:
- **개체 간 비교 편향 제거**: 브랜드 파워가 다른 기업끼리 비교할 때 생기는 편향을 피합니다.
- **시점 간 비교 편향 제거**: 경기 호황기와 불황기를 단순 비교할 때 생기는 편향을 피합니다.

$\hat{\beta}_2 > 0$이라면 전기 광고비가 많을수록 이번 기 판매량이 증가하는 관계를 의미하며, 이 역시 동일 기업의 시간 내 변동으로 해석합니다.

---

## Within 추정량: 수학적 원리

고정 효과 모형은 **Within 추정량(Within Estimator)**으로 계수를 추정합니다. 핵심 아이디어는 **개체별 시간 평균을 차분(Demeaning)**하여 $\mu_i$를 제거하는 것입니다.

### 개체 내 차분(Within Transformation)

원래 모형:

$$\text{Sales}_{it} = \beta_1 \text{Price}_{it} + \beta_2 \text{Advertising}_{it-1} + \mu_i + \tau_t + \epsilon_{it}$$

기업 $i$의 시간 평균을 계산합니다:

$$\overline{\text{Sales}}_{i} = \beta_1 \overline{\text{Price}}_{i} + \beta_2 \overline{\text{Adv}}_{i} + \mu_i + \bar{\tau} + \bar{\epsilon}_{i}$$

원래 모형에서 시간 평균을 빼면:

$$(\text{Sales}_{it} - \overline{\text{Sales}}_i) = \beta_1 (\text{Price}_{it} - \overline{\text{Price}}_i) + \beta_2 (\text{Adv}_{it-1} - \overline{\text{Adv}}_i) + (\tau_t - \bar{\tau}) + (\epsilon_{it} - \bar{\epsilon}_i)$$

$\mu_i$는 상수이므로 차분 후 완전히 소거됩니다. 이렇게 변환된 데이터에 OLS를 적용하면 $\mu_i$의 영향을 받지 않은 $\beta_1$, $\beta_2$를 추정할 수 있습니다.

### 직관적 이해

Within 추정량은 각 기업의 "평균으로부터의 이탈량" 사이의 관계를 추정합니다. 특정 연도에 그 기업의 평균보다 가격이 얼마나 높았는지와, 그 연도의 판매량이 그 기업 평균보다 얼마나 높았는지의 관계입니다. 이 과정에서 기업 고유의 불변 특성($\mu_i$)은 모두 제거됩니다.

### Between 추정량과의 비교

| 구분 | Within 추정량 | Between 추정량 |
|------|--------------|---------------|
| 활용 변동 | 개체 내 시간 변동 | 개체 간 차이 |
| $\mu_i$ 통제 | 완전 제거 | 통제 불가 |
| 활용 정보 | 시계열 변화 | 횡단면 차이 |
| 인과 추론 | 더 신뢰 가능 | 혼란 변수 위험 |

---

## 확률 효과 모형과의 비교

고정 효과 모형 외에 **확률 효과 모형(Random Effects Model, RE)**도 패널 데이터 분석에 자주 사용됩니다.

$$\text{Sales}_{it} = \beta_1 \text{Price}_{it} + \beta_2 \text{Adv}_{it-1} + u_i + \epsilon_{it}$$

여기서 $u_i$는 확률 변수로, 설명 변수와 **무상관(uncorrelated)**임을 가정합니다. 이 가정이 성립하면 RE 추정량이 FE 추정량보다 효율적이지만, 가정이 위반되면 편향이 발생합니다.

**하우스만 검정(Hausman Test)**으로 두 모형 중 어느 것이 더 적절한지 판단합니다:

$$H_0: \text{Cov}(u_i, X_{it}) = 0 \quad \text{(RE가 더 효율적)}$$
$$H_1: \text{Cov}(u_i, X_{it}) \neq 0 \quad \text{(FE가 일치 추정량)}$$

$p$-value가 작아 $H_0$를 기각하면 고정 효과 모형을 선택합니다. 인과 추론이 목적인 경우 대부분 FE 모형이 선호됩니다.

---

## Python 코드: linearmodels로 패널 회귀

```python
import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS, RandomEffects, compare
from linearmodels.panel import BetweenOLS

# ── 1. 패널 데이터 생성 (예시) ────────────────────────────────────────────
np.random.seed(42)
n_firms = 100   # 기업 수
n_years = 5     # 관측 연도 수

firms = np.repeat(np.arange(n_firms), n_years)
years = np.tile(np.arange(2019, 2019 + n_years), n_firms)

# 개체 고정 효과: 기업마다 다른 기본 판매량
mu_i = np.repeat(np.random.normal(0, 2, n_firms), n_years)
# 시점 고정 효과: 연도별 공통 충격
tau_t = np.tile(np.random.normal(0, 1, n_years), n_firms)

# 설명 변수 생성
price = 10 + np.random.normal(0, 1, n_firms * n_years)
adv_lag = np.random.exponential(1, n_firms * n_years)  # 시차 광고비

# 종속 변수 (진짜 계수: price=-0.68, adv_lag=0.35)
sales = (-0.68 * price + 0.35 * adv_lag + mu_i + tau_t
         + np.random.normal(0, 0.5, n_firms * n_years))

df = pd.DataFrame({
    'firm': firms,
    'year': years,
    'sales': sales,
    'price': price,
    'adv_lag': adv_lag
})

# ── 2. MultiIndex 설정 (linearmodels 필수 형식) ──────────────────────────
df = df.set_index(['firm', 'year'])

print("데이터 형태:", df.shape)
print(df.head(10))

# ── 3. 양방향 고정 효과 모형 (TWFE) ─────────────────────────────────────
# time_effects=True → 시점 고정 효과($\tau_t$) 포함
twfe = PanelOLS(
    dependent=df['sales'],
    exog=df[['price', 'adv_lag']],
    entity_effects=True,   # 개체 고정 효과 ($\mu_i$)
    time_effects=True      # 시점 고정 효과 ($\tau_t$)
)
twfe_result = twfe.fit(cov_type='clustered', cluster_entity=True)  # 클러스터 표준오차

print("="*60)
print("[양방향 고정 효과 모형 결과]")
print(twfe_result.summary)

# ── 4. 개체 고정 효과만 포함한 모형 (One-Way FE) ─────────────────────────
one_way_fe = PanelOLS(
    dependent=df['sales'],
    exog=df[['price', 'adv_lag']],
    entity_effects=True,
    time_effects=False
)
one_way_result = one_way_fe.fit(cov_type='clustered', cluster_entity=True)

# ── 5. 확률 효과 모형 (Random Effects) ───────────────────────────────────
re = RandomEffects(
    dependent=df['sales'],
    exog=df[['price', 'adv_lag']]
)
re_result = re.fit()

# ── 6. 모형 비교 ──────────────────────────────────────────────────────────
comparison = compare({
    'TWFE': twfe_result,
    'One-Way FE': one_way_result,
    'RE': re_result
})
print("\n[모형 비교]")
print(comparison)

# ── 7. 하우스만 검정 (FE vs RE) ──────────────────────────────────────────
from linearmodels.panel import PooledOLS
import scipy.stats as stats

# 하우스만 검정: FE와 RE 계수 차이가 통계적으로 유의한지 확인
fe_coef  = one_way_result.params
re_coef  = re_result.params
fe_cov   = one_way_result.cov
re_cov   = re_result.cov

diff     = fe_coef - re_coef
diff_cov = fe_cov - re_cov

H_stat = float(diff.T @ np.linalg.inv(diff_cov) @ diff)
df_h   = len(diff)
p_val  = 1 - stats.chi2.cdf(H_stat, df_h)

print(f"\n[하우스만 검정]")
print(f"  H 통계량: {H_stat:.4f}")
print(f"  자유도  : {df_h}")
print(f"  p-value : {p_val:.4f}")
if p_val < 0.05:
    print("  → H0 기각: 고정 효과 모형(FE)이 적절합니다.")
else:
    print("  → H0 채택: 확률 효과 모형(RE)이 더 효율적입니다.")

# ── 8. 추정 계수 해석 ─────────────────────────────────────────────────────
print("\n[TWFE 계수 해석]")
params = twfe_result.params
pvalues = twfe_result.pvalues

for var in ['price', 'adv_lag']:
    coef = params[var]
    pval = pvalues[var]
    sig  = '***' if pval < 0.001 else ('**' if pval < 0.01 else ('*' if pval < 0.05 else ''))
    print(f"  {var:10s}: {coef:+.4f}  (p={pval:.4f}) {sig}")

print(f"\n  진짜 계수 ) price: -0.68,  adv_lag: +0.35")
print("  해석: 동일 기업에서 동일 연도 환경 하에,")
print("        가격 1단위 상승 시 Sales 평균 {:.2f}단위 감소.".format(abs(params['price'])))
```

<!-- Execution error: ModuleNotFoundError: No module named 'linearmodels' -->

### 클러스터 표준오차(Clustered Standard Error)

패널 데이터에서는 동일 개체의 관측값들이 시계열 상관을 가질 수 있습니다. 이를 무시하면 표준오차가 과소 추정되어 유의성이 부풀려집니다. `cov_type='clustered', cluster_entity=True` 옵션은 개체 내 임의의 상관을 허용하는 **클러스터 표준오차**를 계산하여 이 문제를 보정합니다.

---

## 정리

패널 데이터와 고정 효과 모형은 인과 추론에서 관측 연구(Observational Study)의 신뢰도를 높이는 핵심 도구입니다.

핵심 내용을 정리하면:

1. **횡단면 한계**: 관측 불가 개체·시점 이질성이 추정을 편향시킵니다.
2. **패널 데이터**: 동일 개체를 반복 관측하여 시간 차원을 확보합니다.
3. **개체 고정 효과 $\mu_i$**: 기업별 관측 불가 고정 특성을 흡수합니다. 개체에만 의존하는 변수($i$ 첨자)는 식별 불가합니다.
4. **시점 고정 효과 $\tau_t$**: 연도별 공통 충격을 흡수합니다. 시점에만 의존하는 변수($t$ 첨자)는 식별 불가합니다.
5. **Within 추정량**: 개체 내 시간 차분으로 $\mu_i$를 제거하고 계수를 추정합니다.
6. **해석**: 계수는 개체 내 변동에 기반한 인과 효과로 해석합니다.
7. **하우스만 검정**: FE와 RE 중 적절한 모형을 통계적으로 선택합니다.

고정 효과 모형은 처치 시점이 개체마다 다른 **이중차분법(DiD)**의 기반이 되며, 자연 실험 설계와 결합하면 강력한 인과 추론 도구로 발전합니다.

## 관련 문서

- [[causal-inference-overview|인과 추론 개요]]
- [[did|이중차분법 (Difference-in-Differences)]]
- [[rd-iv|회귀 불연속 & 도구 변수]]
- [[psm-synthetic-control|성향 점수 매칭 & 합성 통제]]
- [[linear-regression|선형 회귀 기초]]