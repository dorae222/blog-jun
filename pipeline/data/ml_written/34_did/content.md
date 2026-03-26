# 이중차분법(DID): 정책 효과를 측정하는 가장 강력한 도구

## 1. 개요: 왜 DID인가

현실 세계에서 "이 정책이 효과가 있었나?"라는 질문에 답하는 것은 놀랍도록 어렵다. A/B 테스트처럼 완전한 랜덤 배정이 가능하면 이상적이지만, 실제로는 불가능한 경우가 많다. 이미 출시된 앱의 UI를 일부 사용자에게만 바꿨다. 특정 지역에만 보조금 정책을 도입했다. 이런 상황에서 단순히 사전-사후를 비교하거나, 처치집단-통제집단을 비교하면 다른 요인들이 섞여 들어온다.

**이중차분법(Difference-in-Differences, DID)**은 이 문제를 해결하는 준실험(quasi-experiment) 방법이다. 핵심 아이디어는 간단하다. 처치를 받은 집단과 받지 않은 집단 모두에서 사전-사후 변화를 측정하고, 그 변화의 차이를 취하는 것이다. 두 종류의 차분(Difference)을 다시 빼기 때문에 "이중차분"이라는 이름이 붙었다.

이 방법은 Goldfarb, Tucker & Wang(2022)이 정리한 디지털 마케팅 인과추론 프레임워크에서도 핵심으로 다루는 기법이며, 경제학, 정책 평가, 마케팅 분석, 의료 연구 등 광범위한 분야에서 사실상 표준적인 인과추론 도구로 자리잡았다.

---

## 2. 구조적 정의

### 기본 구성 요소

DID는 세 가지 요소로 구성된다.

- **처치집단(Treatment Group, TG)**: 처치(정책, UI 변경, 캠페인 등)를 받은 집단
- **통제집단(Control Group, CG)**: 처치를 받지 않은 비교 기준 집단
- **시점(Pre/Post)**: 처치 이전(Pre)과 이후(Post) 시점

이 두 축이 교차하면 2×2 셀 구조가 만들어진다.

| | Pre | Post |
|---|---|---|
| **처치집단(TG)** | $E[Y \mid \text{Pre}, TG]$ | $E[Y \mid \text{Post}, TG]$ |
| **통제집단(CG)** | $E[Y \mid \text{Pre}, CG]$ | $E[Y \mid \text{Post}, CG]$ |

### ATT 추정량

DID가 추정하는 핵심 양은 **처치집단에서의 평균처치효과(Average Treatment effect on the Treated, ATT)**이다:

$$\text{ATT} = (E[Y \mid \text{Post}, TG] - E[Y \mid \text{Pre}, TG]) - (E[Y \mid \text{Post}, CG] - E[Y \mid \text{Pre}, CG])$$

첫 번째 괄호는 처치집단의 사전-사후 변화이고, 두 번째 괄호는 통제집단의 사전-사후 변화이다. 통제집단의 변화는 처치가 없었더라도 시간이 흐르면서 자연적으로 발생했을 트렌드를 대표한다. 처치집단의 변화에서 이 자연적 트렌드를 빼주면 순수한 처치 효과만 남는다.

이것이 DID의 본질이다: **시간에 따른 공통 트렌드를 통제집단으로 제거하고 처치의 순수 효과를 분리한다.**

---

## 3. 직관적 예시: 모바일 커머스 앱

### 상황 설정

한 모바일 커머스 앱이 신규 UI를 도입하려 한다. 완전한 랜덤 배정 대신, 2030년 1월 1일을 기준으로 전체 사용자 중 30%에게는 신규 UI를 노출하고(처치집단), 나머지 70%는 기존 UI를 계속 사용하게 한다(통제집단). 측정 지표는 1인당 일일 구매 금액이다.

### 가상 데이터

| | 1월 이전(Pre) | 1월 이후(Post) | 변화(Δ) |
|---|---|---|---|
| **신규 UI(TG)** | 15,000원 | 19,500원 | +4,500원 |
| **기존 UI(CG)** | 14,500원 | 16,000원 | +1,500원 |

단순히 처치집단의 사전-사후 변화만 보면 +4,500원이다. 하지만 이 중 +1,500원은 연초 소비 증가 등 시장 전반의 자연스러운 트렌드다(통제집단도 +1,500원 증가했음을 확인).

**처치효과(ATT) = 4,500 - 1,500 = 3,000원**

신규 UI가 실제로 기여한 구매 증가는 3,000원이다. 단순 사전-사후 비교의 4,500원은 3,000원의 순수 효과와 1,500원의 공통 트렌드가 혼재된 결과였다.

이처럼 DID는 시장 전반의 트렌드, 계절성, 경기 변동 등 처치와 무관한 시간 효과를 통제집단을 통해 제거함으로써 처치의 순수 효과를 식별한다.

---

## 4. 회귀식으로 DID 추정

### 기본 회귀 모형

2×2 DID는 다음의 회귀식으로 추정할 수 있다:

$$Y_{it} = \beta_0 + \beta_1 (TG_i \times \text{Post}_t) + \beta_2 TG_i + \beta_3 \text{Post}_t + \epsilon_{it}$$

- $TG_i$: 개체 $i$가 처치집단이면 1, 아니면 0
- $\text{Post}_t$: 시점 $t$가 처치 이후이면 1, 아니면 0
- $TG_i \times \text{Post}_t$: 처치집단이면서 처치 이후인 **교차항(interaction term)**
- $\beta_1$: **DID 추정량 = ATT**

### 수학적 증명: 각 셀의 기댓값

각 셀의 기댓값을 회귀식에서 계산하면:

$$E[Y \mid \text{Pre}, CG] = \beta_0$$
$$E[Y \mid \text{Pre}, TG] = \beta_0 + \beta_2$$
$$E[Y \mid \text{Post}, CG] = \beta_0 + \beta_3$$
$$E[Y \mid \text{Post}, TG] = \beta_0 + \beta_1 + \beta_2 + \beta_3$$

ATT를 계산하면:

$$\text{ATT} = (E[Y \mid \text{Post}, TG] - E[Y \mid \text{Pre}, TG]) - (E[Y \mid \text{Post}, CG] - E[Y \mid \text{Pre}, CG])$$
$$= (\beta_0 + \beta_1 + \beta_2 + \beta_3 - \beta_0 - \beta_2) - (\beta_0 + \beta_3 - \beta_0)$$
$$= (\beta_1 + \beta_3) - \beta_3 = \beta_1$$

따라서 $\beta_1$, 즉 교차항의 계수가 곧 DID 추정량(ATT)임이 수학적으로 증명된다. 이 구조 덕분에 회귀 분석 소프트웨어로 DID를 손쉽게 추정하고 통계적 유의성을 검정할 수 있다.

---

## 5. 고정 효과 포함 확장

### 개체·시간 고정 효과 모형

실제 데이터는 단순한 2×2 구조를 넘어 여러 개체와 여러 시점으로 구성된 **패널 데이터(panel data)** 형태인 경우가 많다. 이때는 개체 고정 효과와 시간 고정 효과를 포함한 확장 모형을 사용한다:

$$Y_{it} = \beta_1 (TG_i \times \text{Post}_t) + X_{it}\beta + \mu_i + \tau_t + \epsilon_{it}$$

- $\mu_i$: **개체 고정 효과** — 시간에 따라 변하지 않는 개체별 이질성 제거 (예: 특정 사용자의 고유 구매 성향)
- $\tau_t$: **시간 고정 효과** — 모든 개체에 공통으로 작용하는 시간 트렌드 제거 (예: 연초 소비 증가)
- $X_{it}$: 시간에 따라 변하는 공변량(covariates)

개체 고정 효과는 관찰되지 않는 개체별 특성(시간 불변 혼란 변수)을 자동으로 제어한다. 시간 고정 효과는 전체적인 시간 추세를 흡수한다. 이 두 종류의 고정 효과를 함께 포함하는 것을 **Two-Way Fixed Effects(TWFE)** 모형이라 부른다.

### 다중 시점 DID

주차별·월별 데이터가 있을 때는 처치 더미 대신 처치 이후 각 시점별 효과를 별도로 추정하는 **이벤트 스터디(event study)** 형태로 확장할 수 있다:

$$Y_{it} = \sum_{k \neq -1} \delta_k \cdot \mathbf{1}[t - t_i^* = k] + \mu_i + \tau_t + \epsilon_{it}$$

여기서 $t_i^*$는 개체 $i$의 처치 시점이고, $k$는 처치 시점으로부터의 상대 시간이다. $k < 0$이면 처치 전, $k \geq 0$이면 처치 후이다. 이 추정량 $\delta_k$를 시각화하면 처치 전 평행 추세 여부와 처치 후 효과의 시간 경로를 동시에 확인할 수 있다.

---

## 6. 평행 추세 가정(Parallel Trends Assumption)

### 가정의 내용

DID의 타당성은 **평행 추세 가정(Parallel Trends Assumption)**에 달려 있다. 이 가정은 다음을 의미한다:

> "처치가 없었다면, 처치집단과 통제집단의 결과 변수는 같은 방향으로, 같은 크기로 변했을 것이다."

수식으로는:

$$E[Y_{it}(0) - Y_{i,t-1}(0) \mid TG_i = 1] = E[Y_{it}(0) - Y_{i,t-1}(0) \mid TG_i = 0]$$

여기서 $Y_{it}(0)$은 처치를 받지 않았을 때의 잠재 결과(potential outcome)이다. 평행 추세가 성립할 때, 통제집단의 추세가 처치집단의 반사실적(counterfactual) 추세를 대리하게 되어 ATT 식별이 가능해진다.

이 가정이 충족될 때 두 집단은 처치 배정이 랜덤에 가까운 상태라 볼 수 있다. 처치 이전에 이미 결과 변수의 궤적이 달랐다면, 처치 후 차이가 처치 효과인지 원래부터 달랐던 것인지 구분할 수 없다.

### 평행 추세 검증 방법

**1. 시각적 검증 (그래프)**: 처치 이전 여러 시점에서 두 집단의 결과 변수 추이를 겹쳐 그린다. 처치 전 구간에서 두 집단의 선이 평행하게 움직인다면 가정 충족에 우호적인 증거이다.

**2. Pre-trend 검정 (사전 추세 검정)**: 이벤트 스터디 형태에서 $k < 0$인 계수 $\delta_k$들이 0과 통계적으로 유의하게 다르지 않은지 검정한다. 처치 전 시점에서 처치집단과 통제집단 간 유의한 차이가 없다면 가정을 지지한다.

**3. 집단 비교**: 처치 배정의 근거가 되는 관찰 가능한 특성들이 처치 전 시점에서 두 집단 간에 균형 잡혀 있는지(balance check) 확인한다.

평행 추세 가정은 직접 검증할 수 없는 가정이다. 처치 후 반사실적 잠재 결과는 관측되지 않기 때문이다. 그러나 처치 이전 데이터를 이용해 가정의 그럴듯함을 뒷받침하는 간접 증거를 제시하는 것이 중요하다.

---

## 7. DID 강건성 검증 방법

DID 분석 결과의 신뢰성을 높이기 위해 여러 강건성 검증(robustness check)을 수행해야 한다.

### 다양한 통제변수 추가/제거

기본 모형에 다양한 공변량($X_{it}$)을 추가하거나 제거했을 때 $\beta_1$ 추정치가 크게 변하지 않는지 확인한다. 추정치가 안정적이라면 결과가 특정 통제변수 선택에 의존하지 않음을 의미한다. 주요 변수를 추가했을 때 추정치가 급격히 변한다면 평행 추세 가정 또는 모형 설정에 문제가 있을 수 있다.

### 대체 종속변수 사용

처치 효과가 나타날 것으로 예상되는 다른 종속변수로 분석을 반복한다. 예를 들어 신규 UI의 효과를 구매 금액으로 추정했다면, 클릭률이나 체류 시간으로도 추정해 결과의 일관성을 확인한다. 반면, 처치와 무관한 변수(예: 배송 시간)에서는 유의한 효과가 나타나면 안 된다.

### 플라시보 테스트 (Placebo Test)

플라시보 테스트는 실제 처치 시점이 아닌 다른 가상의 시점을 처치 시점으로 설정하여 DID를 추정하는 방법이다. 예를 들어 실제 처치가 2030년 1월이라면, 처치 전 데이터만 사용해 2029년 7월을 가상 처치 시점으로 설정한다. 이때 유의한 처치 효과가 나타난다면, 평행 추세 가정이 위반되었거나 분석에 문제가 있다는 신호다. 플라시보 테스트에서 유의한 효과가 없을 때 실제 분석 결과의 신뢰성이 높아진다.

---

## 8. 가설 검정

DID 분석의 귀무가설과 대립가설은 다음과 같다:

$$H_0: \text{ATT}(\beta_1) = 0 \quad \text{(처치 효과 없음)}$$
$$H_1: \text{ATT}(\beta_1) \neq 0 \quad \text{(처치 효과 존재)}$$

단측 검정을 원할 경우(예: 효과가 양의 방향이어야만 유의미하다고 볼 때):

$$H_1^+: \text{ATT}(\beta_1) > 0$$

표준 OLS 회귀 출력에서 $\beta_1$의 t-통계량과 p-값을 확인한다. 패널 데이터에서는 개체 내 오차의 자기상관을 반영하기 위해 개체 수준에서 **클러스터 표준오차(clustered standard errors)**를 사용하는 것이 표준 관행이다. 클러스터 표준오차 없이 계산된 표준오차는 과소 추정될 가능성이 높아, 1종 오류율이 높아질 수 있다.

---

## 9. Python 구현 예시

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
from statsmodels.stats.sandwich_covariance import cov_cluster

np.random.seed(42)

# ── 1. 가상 데이터 생성 ──────────────────────────────────────
n_users = 1000
n_periods = 6  # 처치 전 3주 + 처치 후 3주
treatment_week = 3  # week 3 이후가 Post

user_ids = np.repeat(np.arange(n_users), n_periods)
weeks = np.tile(np.arange(n_periods), n_users)

# 30%는 처치집단
treated = np.repeat((np.arange(n_users) < int(n_users * 0.3)).astype(int), n_periods)
post = (weeks >= treatment_week).astype(int)
treat_post = treated * post  # 교차항

# 잠재 결과 생성: 개체 고정 효과 + 시간 효과 + 처치 효과 + 노이즈
user_fe = np.repeat(np.random.normal(15000, 3000, n_users), n_periods)
time_fe = np.tile(np.linspace(0, 500, n_periods), n_users)  # 공통 상승 트렌드
att_true = 3000  # 실제 ATT
noise = np.random.normal(0, 1500, n_users * n_periods)

purchase = user_fe + time_fe + att_true * treat_post + noise

df = pd.DataFrame({
    'user_id': user_ids,
    'week': weeks,
    'treated': treated,
    'post': post,
    'treat_post': treat_post,
    'purchase': purchase
})

# ── 2. 기본 DID 회귀 (교차항 포함) ────────────────────────────
model_basic = smf.ols(
    'purchase ~ treat_post + treated + post',
    data=df
).fit(cov_type='cluster', cov_kwds={'groups': df['user_id']})

print("=== 기본 DID 회귀 결과 (클러스터 표준오차) ===")
print(model_basic.summary().tables[1])
print(f"\n추정된 ATT: {model_basic.params['treat_post']:.1f}원")
print(f"실제 ATT:   {att_true}원")

# ── 3. 개체·시간 고정 효과 포함 (Two-Way FE) ──────────────────
model_fe = smf.ols(
    'purchase ~ treat_post + C(user_id) + C(week)',
    data=df
).fit(cov_type='cluster', cov_kwds={'groups': df['user_id']})

att_fe = model_fe.params['treat_post']
se_fe = model_fe.bse['treat_post']
print(f"\n=== Two-Way FE DID 추정 ===")
print(f"ATT (β₁):   {att_fe:.1f}원  (SE = {se_fe:.1f}, p = {model_fe.pvalues['treat_post']:.4f})")

# ── 4. 평행 추세 시각화 ────────────────────────────────────────
df_agg = df.groupby(['week', 'treated'])['purchase'].mean().reset_index()
df_treat = df_agg[df_agg['treated'] == 1]
df_ctrl  = df_agg[df_agg['treated'] == 0]

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# 왼쪽: 평행 추세 확인
ax = axes[0]
ax.plot(df_treat['week'], df_treat['purchase'], 'o-', color='#E74C3C', label='처치집단 (신규 UI)', linewidth=2)
ax.plot(df_ctrl['week'],  df_ctrl['purchase'],  's-', color='#3498DB', label='통제집단 (기존 UI)', linewidth=2)
ax.axvline(x=treatment_week - 0.5, color='gray', linestyle='--', linewidth=1.5, label='처치 시점')
ax.fill_betweenx([df_agg['purchase'].min() - 500, df_agg['purchase'].max() + 500],
                 treatment_week - 0.5, n_periods, alpha=0.08, color='orange', label='Post 구간')
ax.set_xlabel('주차(Week)')
ax.set_ylabel('평균 구매금액 (원)')
ax.set_title('평행 추세 시각화')
ax.legend()
ax.grid(alpha=0.3)

# 오른쪽: DID 계수 및 신뢰구간
ax2 = axes[1]
coef = model_basic.params['treat_post']
ci_low, ci_high = model_basic.conf_int().loc['treat_post']
ax2.barh(['ATT (β₁)'], [coef], color='#2ECC71', alpha=0.8, xerr=[[coef - ci_low], [ci_high - coef]],
         capsize=8, error_kw={'linewidth': 2})
ax2.axvline(x=0, color='red', linestyle='--', linewidth=1.5)
ax2.set_xlabel('추정된 처치 효과 (원)')
ax2.set_title(f'DID 추정량: {coef:.0f}원\n(95% CI: [{ci_low:.0f}, {ci_high:.0f}])')
ax2.grid(alpha=0.3)

plt.suptitle('이중차분법(DID) 분석 결과', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.show()

# ── 5. 플라시보 테스트 ─────────────────────────────────────────
df_pre = df[df['week'] < treatment_week].copy()
df_pre['placebo_post'] = (df_pre['week'] >= 1).astype(int)  # 가상 처치: week 1 이후
df_pre['placebo_treat_post'] = df_pre['treated'] * df_pre['placebo_post']

model_placebo = smf.ols(
    'purchase ~ placebo_treat_post + treated + placebo_post',
    data=df_pre
).fit(cov_type='cluster', cov_kwds={'groups': df_pre['user_id']})

print("\n=== 플라시보 테스트 ===")
print(f"플라시보 ATT: {model_placebo.params['placebo_treat_post']:.1f}원")
print(f"p-value: {model_placebo.pvalues['placebo_treat_post']:.4f}")
print("→ p > 0.05이면 처치 전 평행 추세 가정 지지")
```

<!-- Execution error: ModuleNotFoundError: No module named 'statsmodels' -->

---

## 요약

| 항목 | 내용 |
|------|------|
| 핵심 아이디어 | 처치집단의 사전-사후 변화에서 통제집단의 변화를 차감 |
| 추정 대상 | ATT (처치집단에서의 평균처치효과) |
| 핵심 가정 | 평행 추세(Parallel Trends Assumption) |
| 회귀식 핵심 | 교차항 $TG_i \times \text{Post}_t$의 계수 $\beta_1 = \text{ATT}$ |
| 확장 모형 | Two-Way FE (개체·시간 고정 효과), 이벤트 스터디 |
| 표준오차 | 클러스터 표준오차 (개체 수준) |
| 강건성 검증 | 통제변수 변화, 대체 종속변수, 플라시보 테스트 |
| $H_0$ | $\beta_1 = 0$ (처치 효과 없음) |
| 활용 분야 | 정책 평가, 마케팅 효과, A/B 테스트 불가 상황 |

DID는 완전한 랜덤화 실험이 불가능한 현실에서 인과 효과를 추정하는 가장 강력하고 직관적인 도구다. 평행 추세 가정을 주의 깊게 점검하고 강건성 검증을 충실히 수행한다면, 이 방법은 앱 기능 변경, 가격 정책, 마케팅 캠페인의 실제 효과를 데이터로 증명하는 데 있어 신뢰할 수 있는 기반을 제공한다.