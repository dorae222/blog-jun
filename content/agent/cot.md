---
title: "Chain-of-Thought Prompting: AI 에이전트 프레임워크"
slug: cot
category: agent
tags: ["Chain-of-Thought", "Chain-of-Thought Prompting", "Emergent Ability", "Few-Shot Reasoning", "Google"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.618814+00:00"
architecture_entry: cot
---

# Chain-of-Thought Prompting: 단계별 추론의 시작

**Google** · **2022-01-28** · **Prompting Technique** · **오픈**

## 개요

Chain-of-Thought(CoT) 프롬프팅은 대형 언어 모델이 복잡한 추론 문제를 단계별 중간 사고 과정을 명시적으로 생성하며 풀도록 유도하는 기법이다. Google Brain의 Wei et al.이 2022년 1월 논문 "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"에서 발표한 이 기법은, 이후 모든 에이전트 추론 기법의 이론적 근간이 되었다.

CoT의 핵심 통찰은 단순하지만 혁명적이다. 기존 few-shot 프롬프팅이 입력-출력 쌍만 제공했다면, CoT는 중간 추론 단계를 예시에 포함시켜 모델이 "생각의 과정"을 모방하도록 유도한다. 이 간단한 변경만으로 수학, 상식 추론, 기호 조작 등 다양한 벤치마크에서 획기적인 성능 향상을 달성했다.

특히 주목할 점은 CoT가 100B(1000억) 파라미터 이상의 대규모 모델에서만 창발적(emergent)으로 나타나는 능력이라는 점이다. 이는 LLM 스케일링의 중요성을 재확인시켰으며, "모델이 충분히 크면 새로운 능력이 나타난다"는 스케일링 법칙의 핵심 사례가 되었다. CoT는 현재 GPT-4, Claude, Gemini 등 모든 주요 LLM이 내재적으로 활용하는 기본 추론 전략으로 자리잡았다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

CoT 프롬프팅의 핵심 메커니즘은 입력 $\rightarrow$ 중간 추론 단계 $\rightarrow$ 출력의 삼중 구조 예시를 제공하는 것이다.

### 표준 프롬프팅 vs CoT 프롬프팅

```
[표준 Few-Shot]
Q: 로저는 테니스 공 5개를 가지고 있다. 2캔을 더 샀고
   캔마다 3개씩 들어있다. 총 몇 개?
A: 11

[CoT Few-Shot]
Q: 로저는 테니스 공 5개를 가지고 있다. 2캔을 더 샀고
   캔마다 3개씩 들어있다. 총 몇 개?
A: 로저는 처음에 5개를 가지고 있었다.
   2캔을 샀고 각 캔에 3개가 있으므로 2 * 3 = 6개를
   추가로 얻었다. 따라서 총 5 + 6 = 11개다.
   정답은 11이다.
```

### 수학적 분석

복잡한 함수 $f: X \rightarrow Y$를 직접 근사하는 대신, 중간 변수 $z_1, z_2, ..., z_n$을 통해 합성 함수로 분해한다.

$$f = g_n \circ g_{n-1} \circ \cdots \circ g_1$$

각 $g_i$는 원래 $f$보다 단순한 함수이므로, 모델이 정확하게 근사할 확률이 높아진다. 확률적으로:

$$P(y|x) = \sum_{z_1,...,z_n} P(z_1|x) \cdot P(z_2|z_1,x) \cdot \ldots \cdot P(y|z_n,...,z_1,x)$$

이 분해를 통해 각 단계의 난이도가 낮아지므로, 모델이 정확한 답을 생성할 확률이 높아진다. 직관적으로, 복잡한 수학 문제를 한 번에 풀기보다 단계별로 풀면 실수할 확률이 줄어드는 것과 같다.

### Zero-Shot CoT

Kojima et al.(2022)은 "Let's think step by step"이라는 단순한 문장만 추가해도 CoT 효과를 얻을 수 있음을 발견했다. 이는 대규모 모델이 학습 데이터에서 단계적 추론 패턴을 이미 내재화하고 있으며, 적절한 트리거만 있으면 이를 활성화할 수 있음을 시사한다.

```
[Zero-Shot CoT]
Q: 카페에서 커피 3잔(각 4,500원)과 케이크 2개(각 6,000원)를
   주문했다. 할인 쿠폰으로 10% 할인을 받으면 총 얼마?
A: Let's think step by step.
   커피 3잔: 3 * 4,500 = 13,500원
   케이크 2개: 2 * 6,000 = 12,000원
   합계: 13,500 + 12,000 = 25,500원
   10% 할인: 25,500 * 0.1 = 2,550원
   최종 금액: 25,500 - 2,550 = 22,950원
```

### 스케일링 특성

CoT의 효과는 모델 크기에 강하게 의존한다. PaLM 8B에서는 CoT의 효과가 미미하거나 오히려 성능이 하락하지만, PaLM 62B에서 효과가 나타나기 시작하고, PaLM 540B에서 극적인 성능 향상을 보인다. 이는 특정 임계점을 넘어야 창발하는 능력(emergent ability)의 대표적 사례다.

## 핵심 혁신

1. **프롬프트 엔지니어링의 패러다임 전환**: 모델 가중치를 변경하지 않고도 추론 능력을 극적으로 향상시킬 수 있음을 실증했다. 파인튜닝 비용 없이 기존 모델의 잠재된 능력을 끌어내는 실용적 접근이다.

2. **추론 과정의 해석 가능성**: 모델이 생성한 중간 사고 과정을 통해 답에 도달한 논리를 확인할 수 있다. 이는 모델의 실수를 진단하고 프롬프트를 개선하는 데 유용하다.

3. **창발적 능력(Emergent Ability)의 발견**: 일정 규모 이상의 모델에서만 나타나는 능력의 존재를 입증하여, LLM 스케일링 연구의 방향을 제시했다.

4. **후속 기법의 이론적 기반**: Self-Consistency(다중 경로), Tree of Thoughts(트리 탐색), Reflexion(자기 반성) 등 모든 후속 추론 기법이 CoT를 기반으로 확장되었다.

## 벤치마크/성능

| 벤치마크 | 모델 | 표준 프롬프팅 | CoT 프롬프팅 | 향상 |
|---------|------|-------------|-------------|------|
| GSM8K | PaLM 540B | 17.9% | 56.9% | +39.0%p |
| AQuA | PaLM 540B | 25.2% | 35.8% | +10.6%p |
| SVAMP | PaLM 540B | 79.0% | 89.3% | +10.3%p |
| StrategyQA | PaLM 540B | 73.9% | 77.8% | +3.9%p |
| GSM8K | GPT-3 175B | 15.6% | 46.9% | +31.3%p |

특히 GSM8K(초등 수학)에서의 39%p 향상은 CoT의 위력을 극적으로 보여주는 결과다.

## 학습

CoT는 별도의 파인튜닝 없이 추론(inference) 시점에 프롬프트 엔지니어링만으로 적용된다. PaLM 540B, GPT-3 175B 등 대규모 모델을 대상으로 평가되었으며, 모델 가중치 변경 없이 프롬프트 구성만으로 성능을 끌어올린다는 점이 실용적 강점이다. 학습 데이터나 파인튜닝 비용 없이 즉시 활용 가능하다.

## 관련 모델

CoT는 이후 등장한 거의 모든 에이전트 추론 기법의 근간이다. Self-Consistency가 다중 CoT 경로의 앙상블을 도입했고, Tree of Thoughts가 트리 탐색으로 확장했으며, ReAct가 추론과 외부 도구 사용을 결합했다. 현재 OpenAI o1, o3 시리즈가 채택한 "내부 추론(internal reasoning)" 메커니즘도 CoT의 연장선에 있다.

## 참고 자료

- Wei et al., "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models", NeurIPS 2022, arXiv:2201.11903
- Kojima et al., "Large Language Models are Zero-Shot Reasoners", NeurIPS 2022, arXiv:2205.11916

## 관련 문서

- [[react|ReAct]] — 후속 모델
- [[self-consistency|Self-Consistency]] — 후속 모델
- [[tree-of-thoughts|Tree of Thoughts]] — 후속 모델
