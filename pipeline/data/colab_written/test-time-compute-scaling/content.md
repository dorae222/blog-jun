# Test-Time Compute Scaling: 추론 시간에 더 생각하기

## 들어가며

:::info
이 글은 [[reasoning-vs-inference|Reasoning vs Inference]] 시리즈의 **SW Reasoning** 축에 해당하며, [[process-reward-models|Process Reward Models]], [[67_scaling-test-time-compute|Scaling Test-Time Compute]] 글과 함께 읽으면 좋다.
:::

LLM의 성능을 높이는 전통적 방법은 **모델을 더 크게 만드는 것**이었다. GPT-3(175B)에서 GPT-4(~1.8T)까지, Kaplan et al.(2020)과 Hoffmann et al.(2022, Chinchilla)이 확립한 scaling law는 학습 시간(train-time)에 더 많은 연산을 투입하는 패러다임이다.

그러나 2024년, 근본적으로 다른 질문이 떠올랐다: **"학습 대신 추론 시간에 더 많은 연산을 투입하면 어떨까?"** Snell et al.(2024)의 "Scaling LLM Test-Time Compute Optimally Can be More Effective than Scaling Model Parameters"가 이 패러다임의 이론적 기반을 제시했고, OpenAI o1과 [[deepseek-r1|DeepSeek-R1]]이 이를 실제 제품으로 구현했다.

핵심 통찰: **같은 총 연산 예산이라면, 더 큰 모델을 한 번 실행하는 것보다 작은 모델을 여러 번 실행하고 최선을 선택하는 것이 더 효율적일 수 있다.**

---

## 두 가지 Scaling Law 비교

Train-time scaling과 test-time scaling은 연산 예산을 투입하는 시점이 다르다. 두 접근법의 핵심 차이를 먼저 정리한다.

| 비교 항목 | Train-Time Scaling | Test-Time Scaling |
|-----------|-------------------|------------------|
| **연산 투입 시점** | 학습 단계 (사전 학습) | 추론 단계 (배포 후) |
| **핵심 변수** | 모델 크기, 데이터 양, 학습 FLOPs | 샘플 수, 탐색 깊이, 검증 반복 |
| **대표 법칙** | Chinchilla Scaling Law | Snell et al. (2024) |
| **비용 구조** | 학습 1회 고정 비용 + 추론 비례 비용 | 학습 비용 낮음 + 추론 비례 비용 |
| **적응성** | 모든 질문에 동일한 연산 | 문제 난이도에 따라 적응적 조절 |
| **한계** | 추론 비용도 함께 증가 | 수확체감, 검증기 품질에 의존 |
| **대표 모델** | GPT-4, LLaMA 3, Gemini | OpenAI o1, DeepSeek-R1, QwQ |
| **성능 향상 곡선** | 로그-선형 (모델 크기 대비) | 로그-선형 (샘플 수 대비) |

---

## Train-Time Compute Scaling

Kaplan et al.(2020)과 Hoffmann et al.(2022, Chinchilla)이 확립한 법칙의 핵심:

- 모델 크기, 데이터 양, 학습 연산량이 증가하면 성능이 **예측 가능하게 향상**
- 최적의 모델 크기와 데이터 양은 연산 예산에 의해 결정 (Chinchilla optimal)
- 이 법칙은 GPT-4, LLaMA, Gemini 등 대규모 모델 개발의 이론적 근거

### Chinchilla Scaling Law 요약

Hoffmann et al.이 발견한 핵심 관계:

| 연산 예산 (FLOPs) | 최적 모델 크기 | 최적 토큰 수 | 예시 |
|-------------------|-------------|------------|------|
| $10^{21}$ | 400M | 8B | 소규모 실험 |
| $10^{23}$ | 10B | 200B | Chinchilla (70B는 과대) |
| $10^{24}$ | 67B | 1.4T | LLaMA 2 수준 |
| $10^{25}$ | 400B+ | 10T+ | GPT-4급 |

**한계**: 모델 크기를 키우는 것은 학습 비용뿐 아니라 **추론 비용도 증가**시킨다. 10배 큰 모델을 배포하면 매 요청마다 10배의 연산이 필요하며, 이 비용은 쉬운 질문이든 어려운 질문이든 동일하게 발생한다.

---

## Test-Time Compute Scaling

추론 시간에 투입하는 연산량을 늘려 성능을 향상시키는 새로운 패러다임이다. 핵심 장점은 **추론 연산을 필요할 때만 사용**할 수 있다는 것이다. 쉬운 질문에는 적은 연산을, 어려운 질문에는 많은 연산을 할당하여 평균 비용을 낮출 수 있다.

### 전략 개요

| 전략 | 핵심 메커니즘 | 추가 모델 필요 | 비용 스케일 | 구현 난이도 |
|------|------------|:----------:|-----------|:---------:|
| **Best-of-N (Majority Voting)** | 다수결 선택 | 없음 | O(N) 선형 | 낮음 |
| **Best-of-N + ORM** | 보상 모델 기반 선택 | ORM | O(N) 선형 | 중간 |
| **Best-of-N + PRM** | 단계별 보상 기반 선택 | PRM | O(N) 선형 | 중간 |
| **Beam Search + PRM** | 단계별 탐색 + 가지치기 | PRM | O(B x D) | 높음 |
| **MCTS (트리 탐색)** | 몬테카를로 트리 탐색 | PRM + Policy | O(시뮬레이션 수) | 높음 |
| **Iterative Refinement** | 자기 검토 + 수정 반복 | 없음 (선택적 PRM) | O(반복 횟수) | 낮음 |
| **내재화 (o1/R1)** | 긴 CoT 내부 탐색 | 없음 (내장) | O(출력 토큰 수) | N/A |

---

## Best-of-N Sampling

### 원리

가장 단순한 test-time compute 전략이다. 같은 질문에 대해 N개의 답변을 독립적으로 생성하고, 그 중 최선을 선택한다. 선택 방식에 따라 세 가지 변종이 있다.

| 변종 | 선택 기준 | 장점 | 한계 |
|------|---------|------|------|
| **Majority Voting** | 가장 많이 등장하는 답변 | 추가 모델 불필요 | 개방형 문제에 부적합 |
| **ORM Reranking** | ORM 점수 최고 답변 | 개방형 문제 가능 | ORM 품질에 의존 |
| **PRM Reranking** | PRM 단계별 점수 합산 최고 | 가장 정밀한 선택 | PRM 학습 비용 |

### Majority Voting 예시

[[self-consistency|Self-Consistency]](Wang et al., 2023)가 이 방법의 대표적 구현이다.

```python
import collections
from openai import OpenAI

client = OpenAI()

def best_of_n_majority_voting(question: str, n: int = 16, model: str = "gpt-4o-mini") -> str:
    """N개의 답변을 생성하고 다수결로 최선을 선택한다."""
    answers = []
    for _ in range(n):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "수학 문제를 풀어주세요. 최종 답을 \\boxed{} 안에 넣으세요."},
                {"role": "user", "content": question}
            ],
            temperature=0.7,  # 다양성을 위해 temperature > 0
        )
        # 최종 답변 추출 (\\boxed{} 파싱)
        answer = extract_boxed_answer(response.choices[0].message.content)
        answers.append(answer)

    # 다수결 투표
    counter = collections.Counter(answers)
    best_answer, count = counter.most_common(1)[0]
    confidence = count / n
    return best_answer, confidence

# 사용 예시
answer, conf = best_of_n_majority_voting("1부터 100까지의 합은?", n=16)
print(f"답: {answer}, 일치율: {conf:.1%}")
```

```output
답: 5050, 일치율: 81.2%
```

### Scaling 곡선: N에 따른 정확도 변화

N을 늘릴수록 정확도가 향상되지만, 수확체감(diminishing returns)이 발생한다.

| N (샘플 수) | MATH 정확도 (추정) | 비용 배수 | 정확도 향상폭 |
|:-----------:|:-----------------:|:---------:|:----------:|
| 1 | 50.0% | 1x | 기준 |
| 4 | 62.0% | 4x | +12.0%p |
| 8 | 68.0% | 8x | +6.0%p |
| 16 | 72.5% | 16x | +4.5%p |
| 32 | 75.0% | 32x | +2.5%p |
| 64 | 76.8% | 64x | +1.8%p |
| 128 | 77.5% | 128x | +0.7%p |
| 256 | 78.0% | 256x | +0.5%p |

핵심 관찰: N을 2배로 늘릴 때마다 정확도 향상폭이 대략 절반으로 줄어든다. 이는 **로그 스케일 수확체감**으로, N=64 이상에서는 비용 대비 효과가 급격히 감소한다.

---

## Reward Model 기반 선택

N개의 답변 중 다수결이 아니라, **보상 모델(Reward Model)**이 가장 좋다고 판단하는 답변을 선택한다. 보상 모델은 크게 두 가지 유형이 있다.

### PRM vs ORM 비교

| 비교 항목 | ORM (Outcome RM) | PRM (Process RM) |
|-----------|:----------------:|:----------------:|
| **평가 단위** | 최종 답변 전체 | 각 추론 단계 |
| **레이블 필요** | 정답/오답 이진 레이블 | 단계별 정확성 레이블 |
| **학습 비용** | 낮음 (자동 수집 가능) | 높음 (인간 or 자동 라벨링) |
| **검증 정밀도** | 낮음 (결과만 봄) | 높음 (과정까지 봄) |
| **오류 탐지** | 최종 답만 틀리면 탐지 | 중간 단계 오류도 탐지 |
| **탐색 결합** | Best-of-N만 가능 | Beam Search, MCTS와 결합 가능 |
| **대표 논문** | Cobbe et al. (2021) | [[66_lets-verify\|Lightman et al. (2023)]] |
| **OpenAI 사례** | GPT-4 RLHF의 RM | Math-Shepherd, PRM800K |

PRM이 ORM보다 우수한 이유: 최종 답이 맞더라도 **추론 과정에 오류가 있을 수 있다** (lucky guess). PRM은 이런 경우를 걸러내어, 올바른 과정으로 올바른 답에 도달한 풀이를 선택한다. 자세한 내용은 [[process-reward-models|Process Reward Models]] 글에서 다룬다.

---

## Beam Search + PRM

### 원리

Best-of-N이 완성된 답변을 비교하는 반면, Beam Search는 **추론 과정의 각 단계에서** 여러 후보를 유지하며 가장 유망한 경로만 확장한다.

작동 방식:
1. 추론의 각 단계에서 **B개의 후보 경로(beam)를 유지**
2. 각 beam에서 다음 단계를 생성
3. [[process-reward-models|PRM]]으로 각 경로의 단계별 점수를 평가
4. 상위 B개 경로만 유지하고, 나머지는 가지치기(pruning)
5. 최종적으로 가장 높은 누적 점수의 경로를 선택

### Best-of-N vs Beam Search 비교

| 비교 항목 | Best-of-N | Beam Search + PRM |
|-----------|:---------:|:-----------------:|
| **탐색 시점** | 완성 후 비교 | 단계마다 비교 |
| **탐색 효율** | 낮음 (전체 생성 후 평가) | 높음 (유망한 경로만 확장) |
| **PRM 활용** | 최종 선택용 | 탐색 가이드용 |
| **비용 구조** | N x 전체 생성 비용 | B x D x 단계 생성 비용 |
| **같은 예산 시 성능** | 중간 | 높음 |
| **구현 복잡도** | 매우 낮음 | 중간 |

같은 연산 예산에서 Beam Search가 Best-of-N보다 성능이 높은 이유: Best-of-N은 초기 단계에서 이미 잘못된 경로도 끝까지 생성하여 연산을 낭비하지만, Beam Search는 유망하지 않은 경로를 일찍 가지치기하여 **연산을 유망한 경로에 집중**한다.

---

## MCTS (Monte Carlo Tree Search)

### 원리

MCTS는 알파고(AlphaGo)에서 유명해진 탐색 알고리즘으로, LLM 추론에 적용하면 **추론 경로를 게임 트리로 구성**하고 최적 경로를 탐색한다.

네 단계 반복:
1. **Selection**: 트리 정책(UCB1 등)에 따라 확장할 노드를 선택
2. **Expansion**: 선택된 노드에서 새로운 추론 단계를 생성
3. **Simulation**: 해당 경로에서 끝까지 추론을 진행 (rollout)
4. **Backpropagation**: 결과를 트리 상위로 전파하여 노드 가치 업데이트

### AlphaGo vs LLM Reasoning 대응

| AlphaGo | LLM Reasoning |
|---------|--------------|
| 바둑판 상태 | 현재까지의 추론 텍스트 |
| 수를 두는 행동 | 다음 추론 단계 생성 |
| 승패 판정 | PRM 점수 또는 최종 정답 여부 |
| Policy Network | LLM 자체 (다음 단계 확률) |
| Value Network | PRM (현재 경로의 성공 확률) |

[[tree-of-thoughts|Tree of Thoughts]] (Yao et al., 2023)가 이 접근법의 초기 구현이며, 이후 rStar (Qi et al., 2024) 등이 MCTS를 LLM 추론에 본격 적용했다.

---

## Iterative Refinement (순차적 수정)

### 원리

하나의 답변을 생성한 후, **모델이 스스로 검토하고 수정**하는 과정을 반복한다. 다른 전략들이 "여러 답변 중 최선을 선택"하는 것이라면, 이 전략은 "하나의 답변을 점진적으로 개선"하는 것이다.

```
[초기 답변] -> [자기 검토: "2단계 계산에 오류가 있다"] -> [수정된 답변] -> [재검토: "논리적 오류 없음"] -> [최종 답변]
```

Reflexion(Shinn et al., 2023)이 대표적이며, 추론 모델의 `<think>` 태그 내에서 "Wait, let me reconsider..."와 같은 자기 수정 행동은 이 전략의 내재화된 형태로 볼 수 있다.

### 전략별 성능-비용 종합 비교

| 전략 | MATH 벤치마크 (추정) | 연산 비용 | 추가 인프라 | 병렬화 가능 |
|------|:------------------:|:---------:|:---------:|:---------:|
| Baseline (1회 추론) | 50.0% | 1x | 없음 | N/A |
| Majority Voting (N=16) | 72.5% | 16x | 없음 | 완전 병렬 |
| Best-of-N + ORM (N=16) | 74.0% | 16x + ORM | ORM 모델 | 완전 병렬 |
| Best-of-N + PRM (N=16) | 76.5% | 16x + PRM | PRM 모델 | 완전 병렬 |
| Beam Search + PRM (B=4, D=8) | 78.0% | ~32x + PRM | PRM 모델 | 부분 병렬 |
| MCTS + PRM (100 sims) | 80.0% | ~100x + PRM | PRM + 트리 관리 | 부분 병렬 |
| Iterative Refinement (3회) | 65.0% | 3x | 없음 (선택적) | 불가 |
| 내재화 (o1-preview) | 83.0% | ~10-50x (토큰) | 없음 (내장) | 불가 |

:::warning
위 수치는 여러 논문의 결과를 종합한 **추정치**이다. 실제 성능은 모델, PRM 품질, 구현 세부사항에 따라 크게 달라질 수 있다. 정확한 비교를 위해서는 동일 조건에서의 실험이 필요하다.
:::

---

## 적응적 연산 할당 (Adaptive Compute)

Test-time compute의 가장 강력한 아이디어는 **문제 난이도에 따라 연산량을 조절**하는 것이다.

### 문제 난이도별 최적 전략

Snell et al.(2024)의 핵심 발견:

| 문제 난이도 | Test-Time Compute 효과 | 최적 전략 | 연산 할당 |
|:----------:|:---------------------:|-----------|:---------:|
| 쉬운 문제 | 낮음 (이미 정답률 높음) | 1회 추론으로 충분 | 최소 |
| 중간 난이도 | **매우 높음** | Best-of-N 또는 Beam Search | 중간~높음 |
| 어려운 문제 | 높음 (개선 여지 큼) | MCTS + PRM | 높음 |
| 극히 어려운 문제 | 낮음 (모델 한계 초과) | 더 큰 모델 사용 권장 | 포기 또는 에스컬레이션 |

### Compute-Optimal Scaling

같은 총 연산 예산 $C$가 있을 때, 두 가지 선택지를 비교할 수 있다.

| 전략 | 구성 | MATH 정확도 (추정) | 장점 |
|------|------|:-----------------:|------|
| 큰 모델 1회 | 14B 모델 x 1회 | 65% | 단순, 낮은 레이턴시 |
| 작은 모델 N회 (Majority) | 1.5B 모델 x 64회 | 60% | 배포 비용 낮음 |
| 작은 모델 N회 + PRM | 1.5B 모델 x 64회 + PRM | 70% | 배포 비용 낮음 + 높은 정확도 |
| 작은 모델 Beam Search | 1.5B 모델 + PRM Beam | 72% | 연산 효율 최적 |

Snell et al.의 실험 결과, 적절한 test-time compute 전략을 사용하면 **1.5B 모델 + 다회 추론이 14B 모델 1회 추론을 능가**하는 영역이 존재한다. 이는 실무적으로 중요한 함의를 가진다:

- 작은 모델은 **배포 비용(GPU 메모리, 전력)이 낮음**
- 적응적 연산으로 **평균 비용을 관리** 가능
- 특히 **추론 품질이 중요한 소수의 어려운 질문**에서 비용 효율적

---

## 비용 효율 분석

### API 호출 기준 비용 비교

실제 서비스에서 각 전략의 비용을 API 가격 기준으로 비교한다 (GPT-4o-mini 기준, 입력 $0.15/1M tokens, 출력 $0.60/1M tokens).

| 전략 | 평균 출력 토큰 | API 비용 (1회 질의) | MATH 정확도 (추정) | 비용 대비 정확도 |
|------|:------------:|:------------------:|:-----------------:|:-----------:|
| 1회 추론 | 500 | $0.0004 | 50.0% | 기준 |
| Majority Voting (N=8) | 4,000 | $0.003 | 68.0% | 5.4x 비용, +18%p |
| Majority Voting (N=32) | 16,000 | $0.011 | 75.0% | 27.5x 비용, +25%p |
| Best-of-N + PRM (N=16) | 8,000 + PRM | $0.006 + PRM | 76.5% | ~15x 비용, +26.5%p |
| o1-mini | 10,000~50,000 | $0.03~0.15 | 83.0% | ~200x 비용, +33%p |

핵심 관찰:
- **비용 효율 최적점**은 대략 N=8~16 구간에 존재
- N=32 이상에서는 추가 비용 대비 향상폭이 급감
- 추론 모델(o1)은 정확도는 최고이지만, 비용도 가장 높음
- **"충분히 좋은" 성능**을 위한 비용 최적화가 실무에서 핵심

---

## 추론 모델과의 연결

### o1과 R1: Test-Time Compute의 제품화

OpenAI o1과 [[deepseek-r1|DeepSeek-R1]]은 test-time compute scaling을 **모델 내부에 내재화**한 것이다. 외부적 전략과 내재화된 전략의 차이를 비교한다.

| 비교 항목 | 외부적 (Best-of-N, Beam Search) | 내재화 (o1, R1) |
|-----------|:-----------------------------:|:--------------:|
| **실행 방식** | 모델 외부에서 여러 번 실행 + 선택 | 모델 내부에서 긴 CoT 생성 |
| **추가 인프라** | PRM, 탐색 알고리즘 필요 | 불필요 (모델에 내장) |
| **연산량 조절** | 사용자가 N, B 파라미터로 조절 | 모델이 자동 조절 (사용자 제한적) |
| **학습 방식** | 기존 LLM + 별도 PRM 학습 | RL로 탐색 전략 자체를 학습 |
| **관찰 가능성** | 중간 후보들을 모두 확인 가능 | `<think>` 출력으로만 관찰 |
| **병렬 처리** | 여러 샘플 동시 생성 가능 | 단일 시퀀스 순차 생성 |
| **비용 예측** | 정확 (N x 단일 비용) | 불확실 (출력 토큰 수 가변) |

### 두 접근법의 결합

흥미롭게도, 두 접근법은 **상호 배타적이 아니다**:

- R1을 여러 번 실행하고 Best-of-N 선택 -> 추가 성능 향상 가능
- R1의 추론 단계에 PRM을 적용 -> 더 정밀한 탐색 가능
- 내재화 모델 + 외부 검증의 **앙상블**이 현재 최고 성능을 달성

---

## 태스크별 선택 가이드

모든 전략이 모든 태스크에 적합한 것은 아니다. 태스크 특성에 따라 최적 전략이 달라진다.

### 태스크 특성별 추천 전략

| 태스크 유형 | 정답 명확성 | 검증 용이성 | 추천 전략 | 이유 |
|-----------|:---------:|:---------:|----------|------|
| **수학 문제 풀이** | 매우 높음 | 매우 높음 | Beam Search + PRM | 단계별 검증이 효과적 |
| **코드 생성** | 높음 | 높음 (실행 테스트) | Best-of-N + 테스트 실행 | 자동 검증 가능 |
| **논리 추론** | 높음 | 중간 | MCTS + PRM | 깊은 탐색이 필요 |
| **사실 확인 (QA)** | 높음 | 중간 | Majority Voting | 단순하고 효과적 |
| **번역** | 중간 | 낮음 | Best-of-N + ORM | 품질 판단 주관적 |
| **에세이/창작** | 낮음 | 매우 낮음 | Iterative Refinement | 검증 모델보다 자기 개선 효과적 |
| **전략 수립** | 낮음 | 매우 낮음 | 내재화 (o1/R1) | 긴 추론 체인이 효과적 |

### 의사결정 플로우

전략 선택을 위한 핵심 질문:

1. **정답이 명확한가?** -> Yes: 검증 기반 전략 (PRM, 다수결) / No: 자기 개선 전략
2. **단계별 검증이 가능한가?** -> Yes: Beam Search + PRM / No: Best-of-N + ORM
3. **레이턴시 제약이 있는가?** -> Yes: Best-of-N (병렬 처리) / No: MCTS (깊은 탐색)
4. **예산이 제한적인가?** -> Yes: Majority Voting (N=8~16) / No: Beam Search 또는 o1

---

## 코드 예시: Best-of-N + Reward Score 선택

Majority Voting 대신 점수 기반 선택을 구현하는 예시이다.

```python
import numpy as np
from openai import OpenAI

client = OpenAI()

def best_of_n_with_scoring(
    question: str,
    n: int = 16,
    model: str = "gpt-4o-mini",
    scorer_model: str = "gpt-4o-mini",
) -> dict:
    """N개의 답변을 생성하고, 스코어링 모델로 최선을 선택한다."""
    candidates = []
    for _ in range(n):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "수학 문제를 단계별로 풀어주세요."},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
        )
        candidates.append(response.choices[0].message.content)

    # 각 후보에 대해 스코어링
    scores = []
    for candidate in candidates:
        score_response = client.chat.completions.create(
            model=scorer_model,
            messages=[
                {"role": "system", "content": (
                    "다음 수학 풀이의 정확성을 0-10 점으로 평가하세요. "
                    "각 단계의 논리적 정확성, 계산 정확성, 최종 답의 정확성을 종합 평가합니다. "
                    "점수만 숫자로 답하세요."
                )},
                {"role": "user", "content": f"문제: {question}\n\n풀이: {candidate}"}
            ],
            temperature=0.0,
        )
        try:
            score = float(score_response.choices[0].message.content.strip())
        except ValueError:
            score = 0.0
        scores.append(score)

    best_idx = int(np.argmax(scores))
    return {
        "best_answer": candidates[best_idx],
        "best_score": scores[best_idx],
        "all_scores": scores,
        "score_mean": np.mean(scores),
        "score_std": np.std(scores),
    }
```

:::tip
실제 프로덕션에서는 별도의 **경량 PRM 모델**(예: Mistral-7B 파인튜닝)을 스코어러로 사용하는 것이 비용 효율적이다. LLM-as-a-judge 방식은 프로토타이핑에 유용하지만, 대규모 서비스에서는 PRM이 비용과 일관성 모두에서 우수하다.
:::

---

## 한계와 열린 질문

### 1. 수확체감의 경계

Test-time compute를 무한히 늘릴 수는 없다. 수확체감이 존재하며, 특정 시점 이후로는 더 큰 모델을 사용하는 것이 효율적이다. 이 **교차점(crossover point)**을 정확히 예측하는 것은 아직 어려운 문제다.

### 2. 검증기의 한계

PRM/ORM의 품질이 test-time compute의 효과를 결정한다. 검증기가 부정확하면 잘못된 답변을 선택하게 되며, 이는 test-time compute의 이점을 상쇄한다. 특히 **reward hacking** 문제가 발생할 수 있다.

### 3. 개방형 문제에서의 적용

수학/코드는 정답이 명확하여 검증이 용이하다. 그러나 에세이 작성, 창작, 전략 수립 같은 **개방형 문제**에서는 "더 좋은 답변"을 판단하는 것 자체가 어렵다. 이 영역에서의 test-time compute scaling은 아직 초기 단계다.

### 4. 레이턴시 트레이드오프

더 많은 연산은 더 긴 응답 시간을 의미한다. 실시간 대화에서 30초 이상 대기하는 것은 사용자 경험을 저하시킬 수 있다. 레이턴시와 품질 사이의 **최적 트레이드오프**를 찾는 것이 실무적 과제다.

---

## 향후 연구 방향

| 연구 방향 | 현재 상태 | 잠재적 영향 |
|----------|----------|-----------|
| **Test-time + Train-time 통합 Scaling Law** | 개별 연구 진행 중 | 연산 예산 최적 배분 이론 |
| **자동 PRM 학습** | Math-Shepherd 등 초기 연구 | PRM 구축 비용 대폭 절감 |
| **개방형 문제용 검증기** | LLM-as-a-judge 수준 | 적용 범위 확장 |
| **하드웨어 최적화** | 추론 최적화 활발 | 병렬 샘플링 비용 절감 |
| **내재화 + 외부 탐색 결합** | R1 + Best-of-N 수준 | 최고 성능 달성 |
| **적응적 예산 할당 알고리즘** | 난이도 분류 기반 | 평균 비용 최적화 |

---

## 정리

### 핵심 전략 요약

| 전략 | 핵심 메커니즘 | 비용 | 효과 | 적합 태스크 |
|------|------------|:----:|:----:|-----------|
| **Best-of-N (다수결)** | 다수결 선택 | N배 | 중간 | 정답이 명확한 문제 |
| **Best-of-N + PRM** | 보상 기반 선택 | N배 + PRM | 높음 | 수학, 코드 |
| **Beam Search + PRM** | 단계별 탐색 + 가지치기 | 가변 | 매우 높음 | 복잡한 추론 |
| **MCTS** | 트리 탐색 + 시뮬레이션 | 높음 | 매우 높음 | 깊은 논리 추론 |
| **Iterative Refinement** | 자기 검토 + 수정 반복 | 반복 수 | 중간 | 개방형 문제 |
| **내재화 (o1/R1)** | 긴 CoT 내부 탐색 | 토큰 수 | 최고 | 범용 |

### 핵심 메시지

Test-time compute scaling은 **"더 크게"에서 "더 오래 생각하게"**로의 패러다임 전환을 대표한다. 모델 크기를 키우는 것만이 성능 향상의 유일한 경로가 아니라, **같은 모델로 더 깊이 생각하는 것**이 또 다른 강력한 경로임을 보여준다.

실무적 가이드라인:
- **빠른 개선이 필요하면**: Majority Voting (N=8~16)부터 시작
- **정밀도가 중요하면**: PRM 기반 선택이나 Beam Search 도입
- **최고 성능이 필요하면**: o1/R1 같은 내재화 모델 사용
- **비용을 최적화하려면**: 적응적 연산 할당으로 쉬운 문제는 빠르게, 어려운 문제만 깊게
