---
title: "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"
slug: "chain-of-thought"
category: technique
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.483493+00:00"
---

## 논문 개요

"Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"(2022, NeurIPS)는 Google Research의 Jason Wei 등이 발표한 연구로, LLM 프롬프팅 분야에서 가장 영향력 있는 연구 중 하나다. 핵심 아이디어는 매우 단순하다: few-shot 예시에 **중간 추론 단계(chain of thought)**를 포함시키면, LLM이 복잡한 추론 문제를 해결하는 능력이 극적으로 향상된다.

기존 few-shot 프롬프팅은 입력-출력 쌍만 제공했다. CoT는 "입력 → 중간 추론 단계 → 출력"의 형태로 예시를 구성하여, 모델이 출력을 생성하기 전에 문제를 단계별로 풀어나가도록 유도한다. 이는 인간이 어려운 문제를 풀 때 "먼저 생각하고 답을 쓰는" 인지 과정을 모방한 것이다.

## 핵심 기여

1. **CoT 프롬프팅 방법 제안**: 중간 추론 단계를 포함한 few-shot 예시 구성 방법을 체계화.
2. **창발적 능력 확인**: CoT의 효과가 ~100B 파라미터 이상에서만 나타나는 스케일 의존적 현상임을 발견.
3. **다양한 추론 태스크 일반화**: 산술(arithmetic), 상식(commonsense), 기호(symbolic) 추론 세 영역에서 모두 유효함 검증.
4. **Zero-shot CoT 가능성 제시**: "Let's think step by step"이라는 단 한 문장으로도 CoT 효과가 나타남을 부록에서 언급(이후 Kojima et al.에서 정식화).

## 방법론 상세

### 1. 표준 Few-Shot vs Chain-of-Thought

**표준 few-shot 예시**:
```
Q: 로저는 테니스공 5개를 가지고 있다. 그는 2캔을 더 샀다.
   캔마다 3개의 공이 들어 있다. 지금 몇 개의 공이 있는가?
A: 11개
```

**CoT 프롬프팅 예시**:
```
Q: 로저는 테니스공 5개를 가지고 있다. 그는 2캔을 더 샀다.
   캔마다 3개의 공이 들어 있다. 지금 몇 개의 공이 있는가?
A: 로저는 처음에 5개의 공을 가지고 있었다.
   테니스공 2캔은 각 3개씩이므로 2 × 3 = 6개다.
   5 + 6 = 11개. 정답은 11개다.
```

차이는 단순하다. 답 이전에 **자연어로 추론 과정을 서술**하는 것이다.

### 2. 수식적 관점에서의 CoT

표준 프롬프팅에서 모델이 생성하는 확률:

$$P(\text{answer} | \text{input}, \text{examples})$$

CoT 프롬프팅에서는:

$$P(\text{answer} | \text{input}, \text{examples}) = \sum_{\text{rationale}} P(\text{answer} | \text{rationale}, \text{input}) \cdot P(\text{rationale} | \text{input}, \text{examples})$$

즉, CoT는 **중간 추론 경로(rationale)를 잠재 변수**로 하여 최종 답의 확률을 높이는 것으로 볼 수 있다. 올바른 reasoning path가 올바른 answer로 이어지므로, 모델이 단계별로 올바르게 추론하도록 유도하면 전체 정확도가 올라간다.

### 3. 프롬프트 구성 상세

**예시 수**: 논문에서는 8개의 few-shot 예시 사용

**추론 체인 길이**: 태스크에 따라 다르며, 산술 문제는 평균 3-5 문장, 기호 추론은 더 길어질 수 있음

**자유 형식**: 추론 체인의 형식을 엄격히 지정하지 않고, 자연스러운 설명 형태로 작성

### 4. 평가 벤치마크

**산술 추론**:
- GSM8K (초등 수준 수학 서술형)
- SVAMP (다양한 구조의 수학 문제)
- ASDiv (다양성이 높은 수학 문제)
- MAWPS (수학 서술형 문제)
- AQuA (대수 문제)

**상식 추론**:
- CommonsenseQA
- StrategyQA
- ARC (과학 문제)
- OpenBookQA

**기호 추론**:
- Last Letter Concatenation (단어들의 마지막 글자 연결)
- Coin Flip (동전 뒤집기 상태 추적)

## 실험 결과

### 스케일별 CoT 효과 (GSM8K)

| 모델 크기 | 표준 few-shot | CoT few-shot |
|----------|---------------|---------------|
| GPT-3 350M | 0.2% | 0.3% |
| GPT-3 6.7B | 2.4% | 3.1% |
| GPT-3 13B | 4.2% | 6.5% |
| GPT-3 175B | 14.0% | **56.9%** |
| PaLM 540B | 17.9% | **58.1%** |

**핵심 발견**: 100B 이하에서는 CoT가 거의 효과가 없거나 오히려 해롭다. 100B 이상에서 갑자기 극적인 효과가 나타나는 **창발(emergence)** 현상이 관찰된다.

이 창발 임계값은 대략:

$$N_{\text{threshold}} \approx 100\text{B parameters}$$

### 상식 추론 (StrategyQA)

| 방법 | 정확도 |
|------|-------|
| Few-shot | 65.4% |
| CoT Few-shot | **73.0%** |
| SOTA (파인튜닝) | 69.4% |

CoT few-shot이 전용 파인튜닝 모델을 초과.

### 기호 추론 (Last Letter Concatenation, OOD)

| 방법 | 4단어 | 8단어 (OOD) |
|------|-------|-------------|
| Few-shot | 4.0% | 0.4% |
| CoT | **93.3%** | **81.0%** |

학습에서 보지 않은 더 긴 시퀀스(OOD)에서도 CoT는 일반화 능력을 보인다.

## 의의 및 한계

### 의의

- **프롬프팅 패러다임 변화**: "입출력 예시" 패러다임에서 "추론 과정 예시" 패러다임으로 전환.
- **파인튜닝 없는 추론 향상**: 모델 가중치를 수정하지 않고도 강력한 추론 능력을 이끌어냄.
- **창발적 능력 발견**: 특정 모델 크기에서 갑자기 능력이 나타나는 창발 현상에 관한 초기 증거 제공.
- **후속 연구 폭발**: Zero-shot CoT, Self-Consistency, Tree of Thoughts, Program-of-Thought 등 수백 편의 후속 연구를 촉발.

### 한계

- **수동 예시 구성**: 고품질 추론 체인 예시를 인간이 직접 작성해야 해, 새로운 태스크마다 노력이 필요.
- **소형 모델 비효과적**: 100B 미만 모델에서는 CoT가 오히려 해가 될 수 있어, 자원 제약 환경에서는 사용하기 어렵다.
- **추론 체인 오류 전파**: 중간 단계에 오류가 있으면 최종 답도 틀릴 가능성이 높다.
- **자기 일관성(Self-Consistency) 미활용**: 단일 greedy decoding만 사용하여, 이후 Self-Consistency(Wang et al., 2022)로 보완될 여지를 남김.
- **환각(Hallucination) 위험**: 그럴듯해 보이지만 사실적으로 틀린 추론 체인을 생성할 수 있다.