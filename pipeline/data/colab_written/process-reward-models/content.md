# Process Reward Models: 단계별 검증으로 추론 향상하기

## 들어가며

:::info
이 글은 [[reasoning-vs-inference|Reasoning vs Inference]] 시리즈의 **SW Reasoning** 축에 해당하며, [[test-time-compute-scaling|Test-Time Compute Scaling]], [[66_lets-verify|Let's Verify Step by Step]] 글과 함께 읽으면 좋다.
:::

LLM이 수학 문제를 풀 때, 최종 답만 맞으면 되는가, 아니면 **풀이 과정도 올바른지** 확인해야 하는가?

이 질문에 대한 답이 **Process Reward Model(PRM)**과 **Outcome Reward Model(ORM)**의 차이를 결정한다. OpenAI의 "Let's Verify Step by Step"(Lightman et al., 2023)은 이 문제에 대한 체계적 실험을 통해, **과정을 검증하는 것이 결과만 검증하는 것보다 우월**함을 증명했다.

이 글에서는 PRM과 ORM의 원리를 비교하고, 핵심 데이터셋과 벤치마크 결과를 분석하며, 코드 수준에서 PRM 추론을 구현하는 방법까지 정리한다.

---

## 검증 전략 전체 비교

추론 결과를 검증하는 전략은 크게 네 가지로 나뉜다. 각 방법의 핵심 차이를 먼저 파악하자.

| 검증 전략 | 평가 대상 | 레이블 필요 | 자동화 가능 | 정밀도 | 확장성 |
|-----------|----------|:---------:|:---------:|:-----:|:-----:|
| **Majority Voting** | 최빈 답변 | 불필요 | 완전 자동 | 낮음 | 높음 |
| **ORM** | 최종 답변 정오 | 정답만 | 완전 자동 | 중간 | 높음 |
| **PRM (인간 감독)** | 각 추론 단계 | 단계별 | 수동 | 높음 | 낮음 |
| **PRM (자동 감독)** | 각 추론 단계 | Monte Carlo | 반자동 | 높음 | 중간 |
| **Self-Consistency** | 다수 경로 일관성 | 불필요 | 완전 자동 | 중간 | 높음 |

핵심 트레이드오프는 **정밀도 vs 확장성**이다. ORM은 대규모 데이터로 쉽게 학습할 수 있지만, 잘못된 추론으로 우연히 정답에 도달한 경우를 구별하지 못한다. PRM은 이를 정확히 포착하지만, 학습 데이터 구축 비용이 높다.

---

## ORM: 결과 기반 검증

### 작동 원리

ORM(Outcome Reward Model)은 풀이의 **최종 답변만** 평가한다. 정답이면 보상 +1, 오답이면 보상 0을 부여하는 단순한 구조다.

```
풀이: "x + 3 = 7이므로 x = 4"
ORM 평가: 정답(4) 맞음 → 보상 +1
```

### ORM의 장점

- **학습 데이터 자동 생성**: 정답 여부만 알면 되므로, 수만 개의 풀이를 자동으로 레이블링할 수 있다
- **구현 단순성**: 시퀀스 분류 모델 하나로 충분하다
- **도메인 독립성**: 수학뿐 아니라 코드 실행, 사실 확인 등 정답 검증이 가능한 모든 영역에 적용 가능

### ORM의 치명적 한계

ORM은 **결과가 같으면 과정을 무시**한다. 이는 근본적인 문제를 야기한다.

```
풀이: "x + 3 = 7. 양변에서 3을 빼면 x = 5.
       아, 잠깐, 다시 계산하면 x = 4."   ← 중간 과정이 틀림
ORM 평가: 정답(4) 맞음 → 보상 +1        ← 그래도 보상
```

이런 풀이가 높은 보상을 받으면, 모델은 **올바른 추론 패턴이 아니라 정답을 우연히 맞추는 패턴**을 학습하게 된다. 이를 "reward hacking"이라 부르며, 문제가 복잡해질수록 심화된다.

---

## PRM: 과정 기반 검증

### 작동 원리

PRM(Process Reward Model)은 **추론의 각 단계를 독립적으로 평가**한다. 각 단계가 이전 단계로부터 논리적으로 올바르게 도출되었는지를 검증한다.

```
풀이 단계 1: "x + 3 = 7"           → PRM: 올바른 설정 (0.97)
풀이 단계 2: "양변에서 3을 빼면"     → PRM: 올바른 연산 (0.95)
풀이 단계 3: "x = 4"               → PRM: 올바른 결론 (0.98)
전체 점수: min(0.97, 0.95, 0.98) = 0.95
```

잘못된 단계가 있으면 **그 이후의 모든 경로를 차단**할 수 있다. 이 특성이 트리 탐색과 결합될 때 특히 강력해진다.

### PRM의 장점

- **오류 조기 감지**: 중간 단계에서 논리적 오류를 즉시 포착
- **해석 가능성**: 어떤 단계에서 추론이 잘못되었는지 정확히 파악 가능
- **탐색 효율성**: 잘못된 경로를 조기에 가지치기하여 연산 자원 절약
- **Reward Hacking 방지**: 우연히 정답에 도달한 풀이를 낮게 평가

---

## PRM vs ORM 상세 비교

| 비교 항목 | ORM | PRM |
|----------|-----|-----|
| **평가 대상** | 최종 답변만 | 각 추론 단계 |
| **평가 단위** | 풀이 전체 1개 점수 | 단계별 N개 점수 |
| **학습 데이터** | 정답/오답 자동 레이블 | 단계별 인간 레이블 필요 |
| **데이터 구축 비용** | 매우 낮음 | 매우 높음 (10배 이상) |
| **오류 검출 범위** | 최종 결과가 맞으면 무시 | 중간 단계 오류 포착 |
| **Reward Hacking** | 취약 | 강건 |
| **해석 가능성** | 낮음 (블랙박스) | 높음 (단계별 진단) |
| **Best-of-N 성능** | 기본 | **6%p+ 향상** (MATH 기준) |
| **트리 탐색 적합성** | 부적합 (전체 풀이만 평가) | 최적 (단계별 가지치기 가능) |
| **연산 비용 (추론)** | 낮음 (1회 평가) | 높음 (단계 수만큼 평가) |
| **확장 도메인** | 정답 있는 모든 영역 | 단계 분할 가능한 영역 |
| **대표 모델** | Cobbe et al. (2021) | Lightman et al. (2023) |

---

## Let's Verify Step by Step: 핵심 실험

### 실험 설계

Lightman et al.(2023)은 MATH 데이터셋에서 ORM과 PRM의 효과를 체계적으로 비교했다. [[66_lets-verify|원 논문]]의 핵심 실험 구조는 다음과 같다.

**핵심 질문**: Best-of-N 선택에서 어떤 검증기가 더 좋은 답변을 골라내는가?

- 동일한 생성 모델(GPT-4 계열)로 N개의 풀이를 생성
- ORM으로 최고 풀이를 선택 vs PRM으로 최고 풀이를 선택
- N = 1, 10, 100, 1000까지 변화시키며 정답률 비교

### MATH 벤치마크 결과

PRM이 **모든 N에서 ORM을 능가**했다. 특히 N이 커질수록(test-time compute가 증가할수록) 격차가 벌어졌다.

| 검증 방식 | N=1 | N=10 | N=100 | N=1000 |
|----------|:---:|:----:|:-----:|:------:|
| **Majority Voting** | ~50% | ~63% | ~69% | ~71% |
| **ORM (Best-of-N)** | ~50% | ~66% | ~72% | ~73% |
| **PRM (Best-of-N)** | ~50% | ~69% | **~78%** | **~80%** |
| **PRM 우위 (vs ORM)** | 0%p | +3%p | **+6%p** | **+7%p** |

이 결과가 중요한 이유는 [[test-time-compute-scaling|test-time compute scaling]]에서 **검증기의 품질이 scaling의 효율을 결정**한다는 것을 보여주기 때문이다. 같은 연산 예산을 투입해도, 좋은 검증기가 있으면 더 큰 성능 향상을 얻을 수 있다.

### 핵심 발견 정리

| 발견 | 의미 |
|------|------|
| PRM이 모든 N에서 ORM 능가 | 과정 감독이 결과 감독보다 일관되게 우수 |
| N 증가에 따라 격차 확대 | Test-time compute 투자 시 PRM의 ROI가 더 높음 |
| Majority Voting 대비 PRM이 9%p+ 우위 | 단순 다수결보다 모델 기반 검증이 훨씬 효과적 |
| 최솟값 집계가 최선 | 가장 약한 단계가 풀이 품질을 결정 |

---

## PRM800K 데이터셋

### 데이터셋 구성

이 논문의 또 다른 핵심 기여는 **PRM800K** 데이터셋이다. 이전까지 이 규모의 프로세스 감독 데이터는 존재하지 않았다.

| 항목 | 수치 |
|------|------|
| 총 풀이 수 | 75,000개 |
| 총 단계 레이블 수 | 800,000개 |
| 레이블 유형 | positive / negative / neutral |
| 대상 데이터셋 | MATH (경시대회 수준 수학) |
| 레이블 생성 방식 | 인간 검증자 (전문 수학 지식 보유) |
| 풀이당 평균 단계 수 | ~10.7개 |

### 레이블 분포

| 레이블 | 비율 | 의미 |
|--------|:----:|------|
| **Positive** | ~75% | 해당 단계의 논리가 올바름 |
| **Negative** | ~16% | 해당 단계에 논리적 오류 존재 |
| **Neutral** | ~9% | 판단 불가 (모호하거나 불필요한 단계) |

PRM800K는 후속 연구(Math-Shepherd, [[deepseek-r1|DeepSeek-R1]]의 보상 설계 등)의 기반이 되었다.

---

## PRM의 작동 메커니즘

### 단계 분할 (Step Segmentation)

PRM을 학습시키려면 먼저 **추론을 단계로 분할**해야 한다. 일반적인 방법 세 가지가 있다.

| 분할 방식 | 기준 | 장점 | 단점 |
|----------|------|------|------|
| **줄바꿈 기반** | 각 줄을 하나의 단계로 취급 | 구현 가장 단순 | 불균일한 단계 크기 |
| **문장 기반** | 완결된 문장 단위로 분할 | 의미적으로 일관 | 수식에 부적합 |
| **논리적 분할** | 수학적 변환/추론 전환점 기준 | 가장 정밀 | 구현 복잡, 도메인 의존 |

실제로 대부분의 연구는 **줄바꿈 기반**을 사용한다. 추론 모델(o1, R1)의 `<think>` 블록은 자연스러운 단계 분할을 제공하므로 PRM 적용이 용이하다.

### 단계별 점수 계산

PRM은 각 단계 $s_i$에 대해 점수 $r(s_i | s_1, ..., s_{i-1}, q)$를 할당한다. 여기서 $q$는 원래 질문이다.

전체 풀이의 점수는 보통 다음 중 하나로 집계된다.

| 집계 방식 | 수식 | 특성 | 성능 |
|----------|------|------|:----:|
| **최솟값** | $R = \min_i r(s_i)$ | 가장 약한 고리가 전체 품질 결정 | 최선 |
| **곱** | $R = \prod_i r(s_i)$ | 모든 단계가 올바를 확률 | 양호 |
| **마지막 단계** | $R = r(s_n)$ | 최종 단계의 누적 평가 | 보통 |
| **평균** | $R = \frac{1}{n}\sum_i r(s_i)$ | 전체 단계의 평균 품질 | 보통 |

"Let's Verify Step by Step"에서는 **최솟값** 방식이 가장 효과적이었다. 이는 직관적으로도 타당하다: 풀이의 품질은 **가장 취약한 추론 단계**에 의해 결정되기 때문이다.

---

## PRM 추론 코드 구현

### Hugging Face PRM 모델 로드

실제로 PRM을 사용하여 풀이의 품질을 평가하는 코드를 살펴보자. 아래는 Hugging Face에 공개된 PRM 모델을 활용하는 예시다.

```python
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# PRM 모델 로드 (예: peiyi9979/math-shepherd-mistral-7b-prm)
model_name = "peiyi9979/math-shepherd-mistral-7b-prm"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)

def score_solution(question: str, solution_steps: list[str]) -> dict:
    """
    풀이의 각 단계를 PRM으로 평가한다.

    Args:
        question: 원래 질문
        solution_steps: 풀이 단계 리스트

    Returns:
        각 단계의 점수와 전체 점수
    """
    step_scores = []

    for i, step in enumerate(solution_steps):
        # 질문 + 지금까지의 단계를 결합
        context = question + "\n" + "\n".join(solution_steps[:i+1])
        inputs = tokenizer(context, return_tensors="pt", truncation=True)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = model(**inputs).logits
            # softmax로 positive 확률 추출
            score = torch.softmax(logits, dim=-1)[0, 1].item()

        step_scores.append({
            "step": i + 1,
            "content": step,
            "score": round(score, 4),
        })

    # 최솟값 집계 (가장 약한 단계가 전체 품질 결정)
    min_score = min(s["score"] for s in step_scores)

    return {
        "step_scores": step_scores,
        "overall_score": round(min_score, 4),
    }

# 사용 예시
question = "삼각형의 넓이가 24이고 밑변이 8일 때, 높이를 구하라."
steps = [
    "삼각형의 넓이 공식: A = (1/2) * b * h",
    "24 = (1/2) * 8 * h",
    "24 = 4h",
    "h = 6",
]
result = score_solution(question, steps)
for s in result["step_scores"]:
    print(f"  Step {s['step']}: {s['score']:.4f} - {s['content']}")
print(f"  Overall: {result['overall_score']:.4f}")
```

### Best-of-N 선택 구현

PRM의 가장 기본적인 활용은 N개의 풀이 중 최선을 선택하는 것이다.

```python
def best_of_n_with_prm(
    question: str,
    solutions: list[list[str]],
    score_fn=score_solution,
) -> dict:
    """
    N개의 풀이를 PRM으로 평가하여 최고 점수의 풀이를 선택한다.

    Args:
        question: 원래 질문
        solutions: N개의 풀이 (각 풀이는 단계 리스트)
        score_fn: 점수 산출 함수

    Returns:
        최고 점수 풀이와 전체 결과
    """
    scored = []
    for i, sol_steps in enumerate(solutions):
        result = score_fn(question, sol_steps)
        scored.append({
            "solution_idx": i,
            "steps": sol_steps,
            "overall_score": result["overall_score"],
            "step_scores": result["step_scores"],
        })

    # 전체 점수 기준 내림차순 정렬
    scored.sort(key=lambda x: x["overall_score"], reverse=True)

    return {
        "best": scored[0],
        "all_scores": [(s["solution_idx"], s["overall_score"]) for s in scored],
    }

# 사용 예시: 3개의 풀이 비교
solutions = [
    # 풀이 1: 올바른 과정
    ["A = (1/2) * b * h", "24 = (1/2)*8*h", "24 = 4h", "h = 6"],
    # 풀이 2: 공식 오류
    ["A = b * h", "24 = 8*h", "h = 3"],
    # 풀이 3: 과정 불명확하나 정답
    ["24/8 = 3", "3 * 2 = 6"],
]

result = best_of_n_with_prm(question, solutions)
print(f"Best solution: #{result['best']['solution_idx']}")
print(f"Score: {result['best']['overall_score']:.4f}")
```

풀이 2는 공식 오류로 PRM 점수가 낮고, 풀이 3은 정답이지만 중간 과정이 불명확하여 PRM 점수가 낮다. PRM은 **올바른 결과뿐 아니라 올바른 과정**을 가진 풀이를 선호한다.

---

## Math-Shepherd: 자동 프로세스 감독

### PRM의 비용 문제

PRM800K처럼 인간이 80만 개 단계를 수동 레이블링하는 것은 현실적으로 확장하기 어렵다. Math-Shepherd(Wang et al., 2024)는 이 문제를 **Monte Carlo 추정**으로 해결했다.

### Monte Carlo 단계 평가

핵심 아이디어: 각 단계에서 나머지를 여러 번 완성시키고, **정답 도달 비율**로 단계의 품질을 추정한다.

1. 풀이의 k번째 단계까지를 취한다
2. 그 이후를 M번 독립적으로 완성시킨다 (rollout)
3. M개 완성 중 정답 도달 비율 $\hat{r}_k = \frac{\text{정답 횟수}}{M}$을 해당 단계의 점수로 사용

| 항목 | PRM800K (인간) | Math-Shepherd (자동) |
|------|:-------------:|:------------------:|
| 레이블 방식 | 전문가 수동 평가 | Monte Carlo rollout |
| 단계당 비용 | $0.5~2.0 | $0.01~0.05 (API 비용) |
| 확장성 | 수만 풀이 한계 | 수백만 풀이 가능 |
| 레이블 품질 | 최고 (인간 판단) | 양호 (통계적 추정) |
| 도메인 확장 | 도메인별 전문가 필요 | 정답 검증만 가능하면 적용 |
| MATH 정답률 (BoN) | ~78% | ~76% |

Math-Shepherd가 보여준 핵심: 인간 레이블 없이도 PRM800K에 **근접한 성능**을 달성할 수 있다. 비용은 수십 배 절감된다.

---

## PRM + Test-Time Compute 전략

PRM은 [[test-time-compute-scaling|test-time compute scaling]]의 핵심 구성 요소다. 활용 방식에 따라 연산 효율이 크게 달라진다.

### Best-of-N + PRM vs Majority Voting

가장 직접적인 비교 대상은 Majority Voting이다. [[self-consistency|Self-Consistency]]에서 제안된 Majority Voting은 구현이 단순하지만, PRM 기반 선택이 일관되게 우수하다.

| 방법 | 원리 | MATH (N=100) | GSM8K (N=100) | 추가 모델 필요 |
|------|------|:-----------:|:------------:|:------------:|
| **Majority Voting** | 최빈 답변 선택 | ~69% | ~87% | 불필요 |
| **ORM Best-of-N** | ORM 최고 점수 선택 | ~72% | ~89% | ORM 1개 |
| **PRM Best-of-N** | PRM 최고 점수 선택 | **~78%** | **~92%** | PRM 1개 |
| **Weighted Voting** | PRM 점수로 가중 투표 | ~76% | ~91% | PRM 1개 |

### Beam Search + PRM

더 정교한 활용법은 **Beam Search**다. 추론 과정을 트리로 구성하고, PRM으로 각 분기의 품질을 평가하며 탐색한다.

1. 1단계에서 K개의 후보 생성 -> PRM으로 상위 B개 선택
2. 선택된 B개에서 각각 K개의 2단계 생성 -> 다시 상위 B개 선택
3. 반복하여 최종 풀이에 도달

이 방식은 **단순 Best-of-N보다 같은 연산으로 더 높은 정답률**을 달성한다. [[67_scaling-test-time-compute|Snell et al.(2024)]]의 연구에서 beam search + PRM이 test-time compute의 가장 효율적인 활용법임을 보여줬다.

### MCTS + PRM 통합

Monte Carlo Tree Search(MCTS)와 PRM을 결합하면 더욱 강력한 탐색이 가능하다. [[tree-of-thoughts|Tree of Thoughts]]의 확장으로 볼 수 있다.

| 탐색 전략 | 연산 비용 | 정답률 향상 | 구현 복잡도 |
|----------|:--------:|:---------:|:---------:|
| Best-of-N | 낮음 (N회 생성) | 기본 | 낮음 |
| Beam Search | 중간 (B*K*D) | +3~5%p | 중간 |
| MCTS | 높음 (반복 시뮬레이션) | +5~8%p | 높음 |

MCTS의 핵심은 **탐색(exploration)과 활용(exploitation)의 균형**이다.

1. **Selection**: UCB 점수로 확장할 노드 선택 (PRM 점수가 value 역할)
2. **Expansion**: 선택된 노드에서 다음 단계 생성
3. **Simulation**: 나머지를 rollout으로 완성
4. **Backpropagation**: 결과를 트리 상위로 전파

PRM은 이 과정에서 **value function** 역할을 하며, MCTS의 탐색 방향을 안내한다. 다만, MCTS는 연산 비용이 크기 때문에 실시간 서빙보다는 고품질 데이터 생성에 주로 사용된다.

---

## 프로세스 감독의 어려움과 대안

### 레이블링 비용

PRM의 가장 큰 장벽은 **학습 데이터 구축 비용**이다. 아래 표에서 ORM과 PRM의 데이터 구축 비용을 비교한다.

| 항목 | ORM | PRM (인간) | PRM (자동) |
|------|:---:|:---------:|:---------:|
| 레이블 단위 | 풀이 1개 | 단계 ~10개/풀이 | 단계 ~10개/풀이 |
| 레이블 비용/풀이 | ~$0.01 | ~$5~15 | ~$0.1~0.5 |
| 10만 풀이 총비용 | ~$1,000 | ~$500K~1.5M | ~$10K~50K |
| 전문 인력 필요 | 불필요 | 필요 (수학 전공) | 불필요 |
| 품질 편차 | 낮음 | 평가자 간 편차 있음 | 통계적 안정 |

### 자동 프로세스 감독 연구 방향

| 방법 | 핵심 아이디어 | 대표 연구 |
|------|------------|----------|
| **Monte Carlo 추정** | 각 단계에서 rollout, 정답 비율로 점수 추정 | Math-Shepherd (2024) |
| **Self-taught** | 모델 자체가 각 단계를 평가하도록 학습 | ReST-MCTS (2024) |
| **합성 데이터** | 의도적으로 특정 단계에 오류를 주입 | PRM training with corrupted steps |
| **토큰 수준 감독** | 단계가 아닌 토큰 단위로 보상 학습 | Token-level reward models |

:::warning
[[deepseek-r1|DeepSeek-R1]]은 흥미롭게도 PRM을 **사용하지 않았다**. 대신 최종 정답 여부만으로 GRPO를 학습시켜, 모델 내부에서 자연스럽게 프로세스 검증 능력이 **창발**하도록 했다. 이는 외부 PRM 없이도 일부 프로세스 감독의 효과를 얻을 수 있음을 시사하지만, 전용 PRM 대비 검증 정밀도는 낮을 수 있다.
:::

---

## 벤치마크 종합 비교

다양한 검증 방법이 주요 수학 벤치마크에서 어떤 성능을 보이는지 종합 비교한다.

| 방법 | MATH | GSM8K | SVAMP | 비고 |
|------|:----:|:-----:|:-----:|------|
| Greedy Decoding (1회) | ~50% | ~80% | ~82% | 기본 |
| Majority Voting (N=64) | ~69% | ~87% | ~89% | 추가 모델 없음 |
| ORM Best-of-N (N=64) | ~72% | ~89% | ~90% | ORM 필요 |
| PRM Best-of-N (N=64) | ~78% | ~92% | ~93% | PRM 필요 |
| Beam Search + PRM (B=5, K=8) | ~80% | ~93% | ~94% | 단계별 탐색 |
| MCTS + PRM | ~83% | ~94% | ~95% | 높은 연산 비용 |

**핵심 관찰**: 동일한 생성 모델에서 검증 방식만 바꿔도 **MATH에서 50%에서 83%**까지 향상이 가능하다. 이는 test-time compute 투자의 ROI가 매우 높다는 것을 의미한다.

---

## 수학을 넘어: PRM의 확장

### 코드 생성

코드는 수학과 유사하게 **실행 결과로 자동 검증**이 가능하다. 각 코딩 단계(함수 설계, 구현, 테스트)에 PRM을 적용하여 코드 품질을 개선할 수 있다.

| 도메인 | 단계 정의 | 자동 검증 | PRM 적합도 |
|--------|----------|:---------:|:---------:|
| 수학 | 수식 변환 | 정답 비교 | 최적 |
| 코드 생성 | 함수/블록 | 테스트 통과 | 높음 |
| 논리 추론 | 전제 -> 결론 | 형식 검증 | 높음 |
| 과학 문제 | 가설 -> 실험 -> 결론 | 부분 자동화 | 중간 |
| 에세이 작성 | 문단 | 불가 | 낮음 |
| 창작 | 장면/절 | 불가 | 낮음 |

### 개방형 문제의 한계

에세이 작성, 전략 수립, 창작 등 **정답이 명확하지 않은 문제**에서는 PRM 적용이 어렵다. "이 문단이 논리적으로 올바른가?"를 판단하는 것은 "이 수학 단계가 맞는가?"보다 훨씬 주관적이다.

이 한계는 test-time compute scaling 전체의 한계이기도 하다. 검증 가능한 문제에서 가장 효과적이고, 검증이 어려운 문제에서는 효과가 제한적이다.

---

## 검증 전략 선택 가이드

상황에 따라 어떤 검증 전략을 선택해야 하는지 정리한다.

| 조건 | 추천 전략 | 이유 |
|------|----------|------|
| 추가 모델 학습 불가 | Majority Voting / [[self-consistency|Self-Consistency]] | 별도 검증 모델 없이 적용 |
| 빠른 구현 필요 | ORM | 정답 데이터만으로 학습 가능 |
| 최고 정답률 필요 (수학) | PRM + Beam Search | 단계별 가지치기로 최고 성능 |
| 대규모 PRM 데이터 구축 | Math-Shepherd (Monte Carlo) | 자동화로 비용 절감 |
| 실시간 서빙 | PRM + Best-of-N (N 작게) | 레이턴시와 정확도 균형 |
| 고품질 학습 데이터 생성 | MCTS + PRM | 오프라인에서 최고 품질 풀이 생성 |
| 추론 모델(o1, R1) 사용 중 | PRM과 호환 용이 | `<think>` 블록이 자연스러운 단계 분할 제공 |
| 검증 불가 도메인 (에세이 등) | Majority Voting 또는 LLM-as-Judge | PRM/ORM 적용 어려움 |

---

## 핵심 논문 및 데이터셋

| 논문/데이터셋 | 연도 | 핵심 기여 |
|-------------|:----:|----------|
| Training Verifiers to Solve Math (Cobbe et al.) | 2021 | ORM 개념 정립, GSM8K 데이터셋 |
| [[66_lets-verify\|Let's Verify Step by Step]] (Lightman et al.) | 2023 | PRM > ORM 체계적 증명, PRM800K |
| Math-Shepherd (Wang et al.) | 2024 | Monte Carlo 자동 프로세스 감독 |
| [[67_scaling-test-time-compute\|Scaling LLM Test-Time Compute]] (Snell et al.) | 2024 | PRM + Beam Search 효율성 분석 |
| [[deepseek-r1\|DeepSeek-R1]] (DeepSeek) | 2025 | PRM 없이 RL로 프로세스 검증 창발 |
| ReST-MCTS (Zhang et al.) | 2024 | Self-taught 프로세스 감독 |

---

## 정리

| 비교 항목 | ORM | PRM | Majority Voting |
|----------|:---:|:---:|:---------------:|
| 평가 대상 | 최종 답변 | 각 추론 단계 | 최빈 답변 |
| 학습 데이터 | 자동 생성 | 인간/자동 레이블 | 불필요 |
| MATH 정답률 (N=100) | ~72% | **~78%** | ~69% |
| 오류 검출 | 최종 오류만 | 중간 단계 포착 | 다수가 틀리면 실패 |
| 트리 탐색 적합성 | 부적합 | 최적 | 부적합 |
| 활용 | 단순 선택 | Beam Search, MCTS | 앙상블 |
| 비용 | 낮음 | 높음 (자동화로 절감 가능) | 생성 비용만 |

PRM은 **"정답을 맞추는 것"에서 "올바르게 추론하는 것"**으로의 전환을 대표한다. 이 전환이 중요한 이유는, 올바른 추론 과정을 가진 모델이 **새로운 문제에서도 일관되게 높은 성능**을 보이기 때문이다. 우연히 정답을 맞추는 모델은 문제가 약간만 변형되면 틀리지만, 올바르게 추론하는 모델은 변형에도 강건하다.

향후 자동 프로세스 감독 기술이 성숙하면, PRM의 비용 장벽은 크게 낮아질 것이다. Math-Shepherd가 그 가능성을 보여줬고, 추론 모델의 `<think>` 블록은 PRM 적용의 자연스러운 인프라를 제공한다. PRM은 test-time compute 시대의 **핵심 인프라**로 자리잡고 있다.
