<!-- infographic-hero -->
![A/B Testing and Statistical Significance 핵심 요약](figures/infographic.svg)

*Figure: A/B Testing and Statistical Significance 한 장 요약 인포그래픽*

## 개요: 왜 A/B 테스트인가

버튼 색상을 파란색에서 초록색으로 바꾸면 클릭률이 올라갈까? 새로운 추천 알고리즘이 기존 것보다 매출을 높일까? 이런 질문에 직관이나 경험만으로 답하는 것은 위험하다. 사람의 직관은 확증 편향(Confirmation Bias)에 취약하고, 시장 환경이나 계절적 요인이 결과에 혼재될 수 있기 때문이다.

**A/B 테스트(A/B Testing)**는 이러한 의사결정을 데이터로 뒷받침하는 무작위 대조 실험(Randomized Controlled Experiment)이다. 사용자를 무작위로 두 그룹(기존 버전(A, Control)과 새 버전(B, Treatment))으로 나누고, 두 그룹의 지표 차이가 통계적으로 유의미한지 검증한다. 넷플릭스, 아마존, 구글은 하루에도 수천 건의 A/B 테스트를 동시에 실행하며 제품을 개선한다.

그러나 A/B 테스트를 제대로 설계하고 해석하려면 통계적 가설 검정의 원리를 이해해야 한다. 잘못 이해된 p-value 하나가 잘못된 제품 결정으로 이어질 수 있다.

---

![A/B 테스트 가설 검정: 귀무가설과 대립가설의 분포 및 유의수준, 검정력 관계 시각화](figures/ab_test_hypothesis.png)
*A/B 테스트 가설 검정: 귀무가설(H0)과 대립가설(H1)의 분포가 겹치는 영역에서 1종 오류와 2종 오류의 트레이드오프를 보여준다.*

## 가설 검정의 기초

A/B 테스트는 통계적 가설 검정(Hypothesis Testing)의 틀 위에서 작동한다.

### 귀무가설과 대립가설

- **귀무가설 $H_0$**: 두 버전 간에 차이가 없다. 예: "A와 B의 클릭률 차이 $\delta = 0$"
- **대립가설 $H_1$**: 차이가 있다. 예: "$\delta \neq 0$" (양측 검정) 또는 "$\delta > 0$" (단측 검정)

검정의 목표는 $H_0$을 기각(Reject)할 충분한 증거가 있는지 판단하는 것이다. 과학에서는 "증거 부재가 부재의 증거는 아니다"는 원칙에 따라, $H_0$을 기각하지 못한다고 해서 $H_0$이 참임을 증명하는 것은 아니다.

### 두 가지 오류의 트레이드오프

가설 검정에서는 두 종류의 오류가 존재하며, 이 둘은 서로 트레이드오프 관계에 있다:

| | $H_0$ 참(실제로 차이 없음) | $H_0$ 거짓(실제로 차이 있음) |
|---|---|---|
| **$H_0$ 기각** | **1종 오류(Type I, $\alpha$)** ( False Positive | 올바른 결정 (Power) |
| **$H_0$ 채택** | 올바른 결정 | **2종 오류(Type II, $\beta$)** ) False Negative |

- **1종 오류($\alpha$, 유의수준)**: 차이가 없는데 있다고 잘못 판단하는 확률. 일반적으로 $\alpha = 0.05$로 설정한다. 이는 100번 실험 중 5번은 우연히 유의미한 결과가 나올 수 있음을 허용한다는 뜻이다.
- **2종 오류($\beta$)**: 실제로 차이가 있는데 탐지하지 못하는 확률. 일반적으로 $\beta = 0.20$으로 설정한다.

---

## p-value 이해하기

### p-value의 정확한 정의

 p-value는 다음과 같이 정의된다:

> **$H_0$이 사실일 때, 관측된 결과만큼 또는 그보다 더 극단적인 결과가 나올 확률**

수식으로는:
$$p = P(\text{관측값} \geq T_{\text{obs}} \mid H_0 \text{ 참})$$

여기서 $T_{\text{obs}}$는 관측된 검정 통계량이다. p-value가 작을수록 귀무가설 하에서 관측 데이터가 얼마나 "이상한지"를 나타낸다.

- $p < 0.05$: 5% 유의수준에서 $H_0$ 기각 → "통계적으로 유의미한 차이 있음"
- $p \geq 0.05$: $H_0$ 기각 실패 → "유의미한 차이를 탐지하지 못함"

### p-value에 대한 흔한 오해

p-value는 자주 잘못 해석된다. 절대 이렇게 해석하면 안 된다:

1. **잘못**: "p = 0.03이면 B가 A보다 좋을 확률이 97%다"
   - 올바름: p-value는 가설에 대한 확률이 아니라 데이터에 대한 확률이다.

2. **잘못**: "p < 0.05면 실용적으로 의미 있는 차이다"
   - 올바름: 통계적 유의성 ≠ 실용적 유의성. 표본이 충분히 크면 0.001% 차이도 유의미하게 나올 수 있다.

3. **잘못**: "p = 0.07이면 '거의' 유의미하다"
   - 올바름: 유의수준을 초과한 p-value에서 정도의 차이를 논하는 것은 의미 없다.

---

## 검정력(Statistical Power)

**검정력(Power)**은 실제 효과가 존재할 때 이를 탐지해낼 확률이다:

$$\text{Power} = 1 - \beta$$

일반적으로 검정력을 $1 - \beta = 0.80$ (80%) 이상으로 설정하는 것이 관례다. 즉, 실제 효과가 있을 때 80%의 확률로 탐지한다는 목표를 세운다.

검정력은 다음 네 가지 요소에 의해 결정된다:

$$\text{Power} \uparrow \iff \begin{cases} n \uparrow & \text{(표본 크기 증가)} \\ \delta \uparrow & \text{(효과 크기 증가)} \\ \sigma \downarrow & \text{(변동성 감소)} \\ \alpha \uparrow & \text{(유의수준 완화)} \end{cases}$$

여기서 $\delta$는 탐지하려는 최소 효과 크기(MDE)이고, $\sigma$는 지표의 표준편차다. 실무에서는 $\alpha$와 $\delta$를 비즈니스 맥락에 따라 먼저 고정하고, 목표 검정력을 달성하는 데 필요한 표본 크기 $n$을 역산한다.

---

## 표본 크기 설계

### 기본 공식

두 집단의 평균 비교(t-test 기준)에서 필요한 집단당 표본 크기는:

$$n \approx \frac{2(z_{\alpha/2} + z_{\beta})^2 \sigma^2}{\delta^2}$$

- $z_{\alpha/2}$: 유의수준 $\alpha$에 대한 임계값 ($\alpha = 0.05$ 양측 → $z_{0.025} = 1.96$)
- $z_{\beta}$: 검정력 $1 - \beta$에 대한 임계값 ($\beta = 0.20$ → $z_{0.20} = 0.84$)
- $\sigma$: 지표의 표준편차 (기존 데이터로 추정)
- $\delta$: 탐지하려는 최소 차이(MDE, Minimum Detectable Effect)

예를 들어, 기존 클릭률이 $p_0 = 0.10$이고 MDE를 $\delta = 0.01$ (1%p 개선)로 설정하면, 이항 분포에서 $\sigma^2 = p_0(1 - p_0) = 0.09$이므로:

$$n \approx \frac{2 \times (1.96 + 0.84)^2 \times 0.09}{0.01^2} \approx 14{,}112$$

각 그룹에 약 14,000명이 필요하다. **MDE를 작게 설정할수록 표본 크기는 제곱에 반비례하여 폭발적으로 증가한다**는 점을 주의해야 한다.

### 최소 탐지 효과(MDE) 설정

MDE는 비즈니스적으로 "의미 있는 최소 변화량"이어야 한다. 통계적으로 탐지 가능한 아주 작은 효과가 비즈니스적으로 의미 없을 수 있기 때문이다. MDE 설정 시 고려사항:

- 해당 지표 개선이 가져올 예상 수익 vs. 실험 비용
- 과거 유사 실험에서 관찰된 효과 크기의 분포
- 제품 변경의 난이도 대비 기대 효과

---

## 다중 비교 문제(Multiple Comparisons)

### 왜 문제가 되는가

실무에서는 하나의 지표만 보지 않는다. 클릭률, 전환율, 구매액, 이탈률 등 20개의 지표를 동시에 모니터링한다고 가정하자. 각 지표를 $\alpha = 0.05$로 독립적으로 검정하면, 모든 귀무가설이 참일 때 적어도 하나의 지표에서 우연히 유의미한 결과를 얻을 확률은:

$$P(\text{적어도 하나 유의}) = 1 - (1 - 0.05)^{20} \approx 0.64$$

무려 64%의 확률로 가짜 양성이 발생한다. 이를 **가족별 오류율(Family-Wise Error Rate, FWER)** 문제라 한다.

### 보정 방법

**Bonferroni 보정**: 가장 단순한 방법. 유의수준을 검정 횟수 $m$으로 나눈다:
$$\alpha_{\text{adjusted}} = \frac{\alpha}{m}$$
20개 지표라면 $\alpha_{\text{adjusted}} = 0.05 / 20 = 0.0025$. 매우 보수적이라 검정력이 크게 낮아진다.

**FDR(False Discovery Rate) 제어**: Benjamini-Hochberg 절차는 FWER 대신 "유의미하다고 선언한 것들 중 가짜 양성의 비율"을 제어한다. Bonferroni보다 덜 보수적이어서 검정력을 더 유지한다. 탐색적 분석에서 유용하다.

실무 조언: **사전에 핵심 지표(Primary Metric) 하나를 명확히 지정**하고, 나머지는 보조 지표(Guardrail Metric)로만 활용하면 다중 비교 문제를 상당 부분 피할 수 있다.

---

![A/B 테스트 결과 분석: 대조군과 실험군의 지표 분포 비교 및 통계적 유의성 시각화](figures/ab_test_results.png)
*A/B 테스트 결과 분석: 대조군과 실험군의 전환율 분포, 신뢰 구간, p-value를 종합적으로 시각화하여 의사결정을 지원한다.*

## Bayesian A/B 테스트

빈도주의(Frequentist) A/B 테스트의 p-value 접근은 직관적이지 않고 Peeking(중간 확인) 문제가 있다. **Bayesian A/B 테스트**는 이를 해결하는 대안이다.

### 핵심 아이디어

Bayes 정리를 적용한다:

$$P(\theta \mid \text{data}) \propto P(\text{data} \mid \theta) \cdot P(\theta)$$

- **사전 분포(Prior)** $P(\theta)$: 실험 전 전환율에 대한 믿음. 예: Beta 분포 $\text{Beta}(\alpha_0, \beta_0)$
- **우도(Likelihood)** $P(\text{data} \mid \theta)$: 관측 데이터의 확률. 이항 분포 $\text{Binomial}(n, \theta)$
- **사후 분포(Posterior)** $P(\theta \mid \text{data})$: 데이터를 본 후 갱신된 믿음

Beta-Binomial 켤레(Conjugate) 공식에 의해 사후 분포는 닫힌 형태로 계산된다:

$$\theta \mid \text{data} \sim \text{Beta}(\alpha_0 + \text{전환 수},\ \beta_0 + \text{비전환 수})$$

### Bayesian 접근의 장점

- **직접적인 확률 진술**: "B가 A보다 좋을 확률은 92%다"처럼 비즈니스 언어로 결과를 표현할 수 있다.
- **Peeking 허용**: 매일 사후 분포를 업데이트하며 모니터링해도 이론적으로 문제가 없다. 빈도주의 방식에서 중간에 결과를 들여다보면(Peeking) 1종 오류가 부풀려지는 문제가 있는데, Bayesian에서는 이런 제약이 없다.
- **정보 손실 없음**: 점 추정 대신 전체 분포를 활용하므로 불확실성을 더 풍부하게 표현한다.
- **사전 정보 활용**: 과거 실험 결과나 도메인 지식을 사전 분포에 반영할 수 있다.

단점으로는 사전 분포 선택이 주관적일 수 있다는 점과, 큰 표본에서는 빈도주의와 결과가 거의 같아진다는 점이 있다.

---

## 실전 함정들

### 1. 조기 종료(Early Stopping)

실험을 시작하고 며칠 후 $p = 0.04$가 나왔다고 바로 종료하면 안 된다. 반복 검정(Sequential Testing) 없이 중간에 p-value를 들여다보면 실제 1종 오류율이 크게 높아진다. 100번 확인하면 유의수준이 5%가 아닌 30% 이상으로 올라갈 수 있다. **사전에 설정한 표본 크기에 도달할 때까지 실험을 지속**해야 한다. 중간 모니터링이 필요하다면 Sequential Testing 또는 Bayesian 방법을 사용한다.

### 2. 네트워크 효과(Network Effects)

소셜 플랫폼처럼 사용자들이 서로 영향을 미치는 환경에서는 A 그룹과 B 그룹이 독립적이지 않을 수 있다. B 그룹 사용자가 A 그룹 사용자와 상호작용하면 실험이 오염된다. 이럴 때는 사용자 단위가 아닌 **클러스터(지역, 커뮤니티) 단위로 랜덤화**하는 Cluster Randomization을 고려해야 한다.

### 3. 참가자 오염(Contamination)

같은 사용자가 A, B 두 그룹 모두에 노출되는 경우다. 예를 들어, 쿠키 기반 랜덤화에서 사용자가 쿠키를 삭제하면 다른 그룹에 재배정될 수 있다. 또한 사용자가 여러 기기를 쓰는 경우 기기별로 다른 그룹에 배정될 수 있다. 이를 방지하려면 로그인 사용자 ID 기반의 랜덤화가 바람직하다.

### 4. 신규 사용자 효과(Novelty Effect)

새로운 UI가 처음에는 단지 새롭기 때문에 클릭률이 높아지지만 시간이 지나면 원래대로 돌아오는 현상이다. 실험 기간을 충분히 늘려 이 효과가 안정화된 후의 결과를 보거나, 신규 vs. 기존 사용자를 분리 분석해야 한다.

---

## Python 코드

```python
import numpy as np
from scipy import stats
from scipy.stats import beta as beta_dist

# ──────────────────────────────────────
# 1. 빈도주의 t-test / z-test
# ──────────────────────────────────────
def run_frequentist_ab_test(
    n_a: int, conv_a: int, n_b: int, conv_b: int,
    alpha: float = 0.05
) -> dict:
    """두 집단의 전환율 차이를 z-test로 검정한다."""
    p_a = conv_a / n_a
    p_b = conv_b / n_b
    p_pool = (conv_a + conv_b) / (n_a + n_b)

    # 합동 표준 오차
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n_a + 1/n_b))
    z = (p_b - p_a) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))  # 양측 검정

    return {
        "p_a": p_a, "p_b": p_b,
        "lift": (p_b - p_a) / p_a,
        "z_statistic": z,
        "p_value": p_value,
        "significant": p_value < alpha,
    }

# ──────────────────────────────────────
# 2. 표본 크기 계산
# ──────────────────────────────────────
def compute_sample_size(
    p_baseline: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.80
) -> int:
    """각 집단에 필요한 최소 표본 크기를 계산한다."""
    z_alpha = stats.norm.ppf(1 - alpha / 2)  # 1.96 (양측)
    z_beta  = stats.norm.ppf(power)           # 0.84

    p_b = p_baseline + mde
    sigma_sq = p_baseline * (1 - p_baseline) + p_b * (1 - p_b)
    n = (z_alpha + z_beta) ** 2 * sigma_sq / mde ** 2
    return int(np.ceil(n))

# ──────────────────────────────────────
# 3. Bayesian A/B 테스트
# ──────────────────────────────────────
def bayesian_ab_test(
    n_a: int, conv_a: int,
    n_b: int, conv_b: int,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    n_samples: int = 100_000
) -> dict:
    """Beta-Binomial 모델로 Bayesian A/B 테스트를 수행한다."""
    # 사후 분포 파라미터 (Beta-Binomial 켤레)
    post_alpha_a = prior_alpha + conv_a
    post_beta_a  = prior_beta  + (n_a - conv_a)
    post_alpha_b = prior_alpha + conv_b
    post_beta_b  = prior_beta  + (n_b - conv_b)

    # 몬테카를로 샘플링으로 "B > A" 확률 계산
    samples_a = beta_dist.rvs(post_alpha_a, post_beta_a, size=n_samples)
    samples_b = beta_dist.rvs(post_alpha_b, post_beta_b, size=n_samples)

    prob_b_better = np.mean(samples_b > samples_a)
    expected_lift = np.mean((samples_b - samples_a) / samples_a)

    return {
        "posterior_a": (post_alpha_a, post_beta_a),
        "posterior_b": (post_alpha_b, post_beta_b),
        "prob_b_better_than_a": prob_b_better,
        "expected_lift": expected_lift,
    }


# ──────────────────────────────────────
# 실행 예시
# ──────────────────────────────────────
if __name__ == "__main__":
    # 표본 크기 설계
    n_required = compute_sample_size(
        p_baseline=0.10, mde=0.01, alpha=0.05, power=0.80
    )
    print(f"[표본 크기] 집단당 최소 {n_required:,}명 필요")

    # 실험 결과 (가정)
    n_a, conv_a = 15_000, 1_500   # 전환율 10.0%
    n_b, conv_b = 15_000, 1_680   # 전환율 11.2%

    # 빈도주의 검정
    freq_result = run_frequentist_ab_test(n_a, conv_a, n_b, conv_b)
    print(f"\n[빈도주의] p-value={freq_result['p_value']:.4f}, "
          f"유의미={freq_result['significant']}, "
          f"lift={freq_result['lift']:.2%}")

    # Bayesian 검정
    bayes_result = bayesian_ab_test(n_a, conv_a, n_b, conv_b)
    print(f"[Bayesian] B가 A보다 나을 확률={bayes_result['prob_b_better_than_a']:.2%}, "
          f"기대 lift={bayes_result['expected_lift']:.2%}")
```

---

## 정리

A/B 테스트는 "직관 vs. 데이터"의 싸움에서 데이터의 손을 들어주는 도구다. 하지만 잘못 사용하면 오히려 잘못된 확신을 심어줄 수 있다. 핵심을 정리하면:

1. **가설 검정의 틀**: $H_0$, $H_1$, 1종/2종 오류를 명확히 이해하고 실험 전에 유의수준과 검정력을 정의한다.
2. **p-value는 확률이 아니다**: $H_0$ 하에서의 데이터 극단성 지표일 뿐, "차이가 있을 확률"이 아님을 명심한다.
3. **표본 크기 계산은 선행 작업이다**: MDE를 비즈니스 맥락에서 결정하고, 실험 시작 전에 필요 표본 수를 계산한다.
4. **다중 비교를 조심한다**: 핵심 지표를 하나로 사전 지정하고 Bonferroni 또는 FDR 보정을 적용한다.
5. **Bayesian은 강력한 대안이다**: 직관적 해석, Peeking 허용, 불확실성의 풍부한 표현이라는 장점이 있다.
6. **실전 함정을 피한다**: 조기 종료, 네트워크 효과, 참가자 오염은 실험의 타당성을 훼손하는 주요 위협이다.

> **다음 글 안내**: 관측 데이터에서 인과 효과를 추정하는 더 일반적인 방법론은 [[causal-inference-overview]]를 참고하고, 차분 인과추론(DiD) 방법은 [[did]]에서, 분류 모델 성능 평가는 [[classification-metrics]]에서 다룬다.

## 관련 문서

- [[causal-inference-overview|인과 추론 개요]]
- [[did|이중 차분법 (Difference-in-Differences)]]
- [[classification-metrics|분류 모델 성능 지표]]
- [[bayesian-ml|베이즈 머신러닝]]
- [[mlops-fundamentals|MLOps 기초]]