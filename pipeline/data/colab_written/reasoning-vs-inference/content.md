<!-- infographic-hero -->
![Reasoning vs Inference: Two Axes of AI Efficiency 핵심 요약](figures/infographic.svg)

*Figure: Reasoning vs Inference: Two Axes of AI Efficiency 한 장 요약 인포그래픽*

# Reasoning vs Inference: AI 효율성의 두 축

## 들어가며

:::info
이 글은 LLM의 **Reasoning(추론 품질)**과 **Inference(실행 효율)**를 체계적으로 비교하는 개론이다. 각 기법의 원리, 벤치마크, 비용 구조를 정리하고, 실전에서 어떤 전략을 선택해야 하는지 판단 기준을 제시한다.
:::

LLM 시대에 "효율성"이라는 단어는 두 가지 완전히 다른 의미로 사용된다.

하나는 **"어떻게 더 잘 생각하게 할 것인가"** -- Chain-of-Thought, 추론 모델, test-time compute scaling 등 모델의 **추론 품질**을 높이는 SW 관점의 효율성이다. 다른 하나는 **"어떻게 더 빠르게 실행할 것인가"** -- 양자화, KV-Cache, Multi-GPU 병렬 처리 등 같은 모델을 **더 적은 자원으로 실행**하는 HW 관점의 효율성이다.

이 두 축은 독립적이면서도 상호 보완적이다. 추론 모델([[deepseek-r1|DeepSeek-R1]], o1)은 더 많은 토큰을 생성하여 더 잘 "생각"하지만, 그만큼 Inference 비용도 증가한다. 반대로 양자화된 모델은 빠르게 실행되지만, 추론 품질이 저하될 수 있다. **두 축의 최적 균형점을 찾는 것**이 현대 LLM 배포의 핵심 과제다.

---

## Reasoning과 Inference 핵심 비교

| 구분 | SW Reasoning | HW Inference |
|------|-------------|-------------|
| **핵심 질문** | 어떻게 더 잘 생각하게 할까? | 어떻게 더 빠르게 실행할까? |
| **목표** | 정확도, 논리적 정합성 향상 | 레이턴시, 처리량, 비용 최적화 |
| **비용 구조** | 토큰 생성량 증가 (reasoning tokens) | 구현 복잡도, HW 투자 |
| **대표 기법** | CoT, Self-Consistency, ToT | 양자화, KV-Cache, Flash Attention |
| **대표 모델** | o1, o3, DeepSeek-R1, QwQ | vLLM, TensorRT-LLM, Ollama |
| **스케일링 방향** | Test-time compute 증가 | HW 활용률(MFU) 극대화 |
| **트레이드오프** | 더 나은 답 vs 더 많은 비용 | 속도 vs 정밀도 |

---

## System 1 vs System 2: 인간 사고와 LLM의 대응

Daniel Kahneman의 "Thinking, Fast and Slow"는 인간의 사고를 두 시스템으로 구분한다. 이 프레임워크는 LLM의 Reasoning vs Inference를 이해하는 데 매우 유용한 비유를 제공한다.

| 특성 | System 1 (빠른 사고) | System 2 (느린 사고) |
|------|---------------------|---------------------|
| **속도** | 즉각적, 자동적 | 느리고 의도적 |
| **에너지** | 적은 인지 부하 | 높은 인지 부하 |
| **정확도** | 직관적, 오류 가능 | 분석적, 높은 정확도 |
| **LLM 대응** | Standard inference (GPT-4o, Claude 3.5) | Reasoning model (o1, o3, DeepSeek-R1) |
| **토큰 사용** | 입력 대비 적은 출력 | 긴 reasoning chain 생성 |
| **적합 작업** | 번역, 요약, 간단한 QA | 수학, 코딩, 논리 추론 |

### 표준 모델의 System 1 동작

일반 LLM(GPT-4o, Claude 3.5 Sonnet)은 **System 1처럼 동작**한다. 프롬프트를 받으면 학습된 패턴에 기반하여 빠르게 응답을 생성한다. 대부분의 일상적 작업에서 충분한 품질을 제공하지만, 복잡한 다단계 추론에서는 중간 과정을 건너뛰어 오류가 발생할 수 있다.

### 추론 모델의 System 2 동작

추론 모델(o1, o3, DeepSeek-R1)은 **System 2처럼 동작**한다. 최종 답변 전에 긴 "생각의 사슬"을 생성하며, 여러 경로를 탐색하고 자체 검증을 수행한다. 정확도가 높지만, 더 많은 토큰(=시간과 비용)을 소비한다.

---

## SW 축: Reasoning 기법 상세

SW Reasoning은 모델 아키텍처나 하드웨어를 변경하지 않고, **모델이 문제를 푸는 방식**을 개선하는 접근법이다. 핵심 아이디어는 "더 많이 생각하면 더 나은 답을 얻는다"는 것이다.

## Chain-of-Thought (CoT)

CoT(Wei et al., 2022)는 모델이 최종 답변 전에 **중간 추론 과정을 명시적으로 생성**하도록 유도하는 기법이다. "Let's think step by step"이라는 단순한 프롬프트 추가만으로도 수학, 논리, 상식 추론에서 극적인 성능 향상을 달성했다.

CoT의 핵심 통찰:
- 모델은 이미 추론 능력을 보유하고 있지만, 중간 단계를 건너뛰면 오류가 누적된다
- 명시적 추론 체인이 "작업 메모리(working memory)" 역할을 수행
- 문제의 복잡도가 높을수록 CoT의 이점이 커진다

## Self-Consistency

[[self-consistency|Self-Consistency]](Wang et al., 2023)는 CoT를 확장한 기법이다. 동일한 문제에 대해 **여러 개의 CoT 경로를 샘플링**하고, 가장 빈번하게 등장하는 최종 답변을 선택한다(majority voting).

핵심 원리:
- Temperature를 높여 다양한 추론 경로를 생성
- 각 경로의 최종 답변에 대해 다수결 투표
- 단일 CoT 대비 GSM8K에서 **+17.9%** 정확도 향상 (GPT-3, 40개 경로)

## Tree of Thoughts (ToT)

[[tree-of-thoughts|Tree of Thoughts]](Yao et al., 2023)는 추론 과정을 **트리 구조로 탐색**하는 기법이다. 각 추론 단계를 "노드"로 보고, BFS 또는 DFS로 여러 분기를 탐색한다.

핵심 원리:
- 중간 사고(thought)를 생성하고 평가(evaluation)하는 과정을 분리
- 유망하지 않은 경로는 조기 종료(pruning)
- 24 Game 문제에서 CoT 대비 **4% → 74%** 정확도 향상

## Reasoning 기법 비교

| 기법 | 추론 경로 | 탐색 방식 | API 호출 수 | 정확도 향상 | 비용 |
|------|----------|----------|------------|-----------|------|
| Zero-shot | 1개 (직선) | 없음 | 1 | 기준선 | 최소 |
| CoT | 1개 (직선) | 순차적 | 1 | +10~30% | 토큰 2~3x |
| Self-Consistency | N개 (병렬) | 다수결 | N | +15~25% | 토큰 Nx |
| ToT | 트리 (분기) | BFS/DFS | 다수 | +30~70% | 토큰 10~50x |
| [[react\|ReAct]] | 행동 기반 | 관찰-행동 루프 | 다수 | 도구 활용 | 변동 |
| [[reflexion\|Reflexion]] | 반복 개선 | 자기 반성 | 다수 | 누적 개선 | 높음 |

---

## Test-Time Compute Scaling

[[test-time-compute-scaling|Test-Time Compute Scaling]]은 Snell et al.(2024)의 [[scaling-test-time-compute|"Scaling LLM Test-Time Compute"]]에서 제시된 핵심 관찰이다: **학습 시간(training-time)에 투입하는 연산을 추론 시간(test-time)으로 이동**시키면, 더 작은 모델로도 큰 모델의 성능에 도달할 수 있다.

### 핵심 전략

| 전략 | 설명 | 구현 예시 |
|------|------|----------|
| **Search** | 여러 후보 답변을 생성하고 최선을 선택 | Best-of-N, Beam Search |
| **Verification** | 각 추론 단계를 독립적으로 평가 | [[process-reward-models\|Process Reward Model (PRM)]] |
| **Adaptive Compute** | 문제 난이도에 따라 연산 할당 | 쉬운 문제: 1 경로, 어려운 문제: 64 경로 |

### PRM과 ORM 비교

추론 결과를 검증하는 보상 모델은 크게 두 가지 접근이 있다([[lets-verify|Let's Verify Step by Step]]):

| 항목 | ORM (Outcome RM) | PRM (Process RM) |
|------|------------------|------------------|
| **평가 단위** | 최종 답변만 | 각 추론 단계 |
| **피드백 세밀도** | 이진(맞다/틀리다) | 단계별 점수 |
| **학습 데이터** | 자동 생성 가능 | 인간 라벨링 or 자동화 필요 |
| **오류 탐지** | 최종 오류만 | 중간 오류 조기 발견 |
| **성능** | 기준선 | MATH에서 +7~15% 향상 |

이 패러다임의 실질적 함의는, 모델 크기를 키우는 것만이 성능 향상의 유일한 경로가 아니라는 점이다. 때로는 더 작은 모델에 더 많은 추론 시간을 투자하는 것이 비용 효율적이다.

---

## Reasoning 모델 비교

2024~2025년에 등장한 추론 모델들은 CoT와 test-time compute scaling을 **모델 자체에 내재화**한 사례다.

### 주요 Reasoning 모델

| 모델 | 개발사 | 학습 방식 | 추론 체인 | 오픈소스 | 특징 |
|------|--------|----------|----------|---------|------|
| **o1** | OpenAI | SFT + RL | 숨김 | X | 최초의 상용 reasoning 모델 |
| **o3** | OpenAI | SFT + RL | 숨김 | X | o1 대비 추론 능력 강화 |
| **o3-mini** | OpenAI | SFT + RL | 숨김 | X | 비용 효율 추론 모델 |
| **DeepSeek-R1** | DeepSeek | 순수 RL → SFT+RL | 공개 | O | RL만으로 CoT 자발적 학습 |
| **DeepSeek-R1-Zero** | DeepSeek | 순수 RL | 공개 | O | SFT 없이 RL만으로 추론 학습 |
| **QwQ-32B** | Alibaba | SFT + RL | 공개 | O | 크기 대비 효율적 추론 |
| **Claude 3.5 Sonnet** | Anthropic | RLHF | 내부 | X | 확장된 사고(extended thinking) 모드 |
| **Gemini 2.0 Flash Thinking** | Google | SFT + RL | 공개 | X | 빠른 추론 모델 |

### 벤치마크 비교

| 벤치마크 | GPT-4o | o1 | o3-mini(high) | DeepSeek-R1 | QwQ-32B |
|---------|--------|-----|--------------|-------------|---------|
| **MATH-500** | 76.6% | 94.8% | 97.0% | 97.3% | 90.6% |
| **AIME 2024** | 9.3% | 83.3% | 87.3% | 79.8% | 50.0% |
| **GPQA Diamond** | 53.6% | 78.0% | 79.7% | 71.5% | 65.2% |
| **Codeforces** | 23.0% | 89.0% | 93.4% | 96.3% | -- |
| **LiveCodeBench** | 33.4% | 63.4% | 72.1% | 65.9% | 63.4% |

:::warning
벤치마크 수치는 공개 시점과 평가 조건에 따라 차이가 있을 수 있다. 특히 reasoning 모델은 test-time compute budget(low/medium/high)에 따라 성능이 크게 달라지므로, 동일 조건 비교에 주의가 필요하다.
:::

### DeepSeek-R1의 핵심 발견

[[deepseek-r1|DeepSeek-R1]]은 reasoning 모델 연구에서 세 가지 중요한 발견을 제시했다:

1. **RL만으로 CoT 자발적 학습**: R1-Zero는 SFT 없이 순수 RL만으로 모델이 스스로 "생각하는 법"을 학습. 학습이 진행되면서 응답 길이가 자연스럽게 증가하고, self-verification과 backtracking이 자발적으로 출현
2. **Cold-start SFT의 효과**: R1-Zero의 가독성 문제를 해결하기 위해, 소량의 CoT 예시로 cold-start SFT 수행 후 RL 적용. 이 2단계 접근(SFT → RL)이 최적의 결과 달성
3. **증류의 효과**: R1의 추론 능력을 1.5B~70B 모델에 증류. 14B 증류 모델이 QwQ-32B-Preview를 능가하는 성능 달성

---

## Reasoning Token 비용 분석

Reasoning 모델의 가장 큰 특징은 **reasoning token**이다. 최종 답변 전에 "생각하는 과정"을 토큰으로 생성하며, 이 토큰이 전체 비용의 대부분을 차지한다.

## 토큰 사용량 비교

| 모델 | 입력 토큰 가격 ($/M) | 출력 토큰 가격 ($/M) | 평균 reasoning 토큰 | 총 비용 배수 |
|------|--------------------|--------------------|-------------------|------------|
| GPT-4o | $2.50 | $10.00 | 0 | 1x (기준) |
| o1-mini | $3.00 | $12.00 | ~3,000 | 5~10x |
| o1 | $15.00 | $60.00 | ~5,000 | 20~50x |
| o3-mini (low) | $1.10 | $4.40 | ~2,000 | 3~5x |
| o3-mini (high) | $1.10 | $4.40 | ~10,000 | 10~20x |
| DeepSeek-R1 (API) | $0.55 | $2.19 | ~5,000 | 3~8x |

## 비용 대비 정확도 트레이드오프

단순한 QA 작업에서 reasoning 모델을 사용하면 비용은 10배 이상 증가하지만 정확도 향상은 미미하다. 반면 수학/코딩 등 복잡한 추론 작업에서는 비용 증가 대비 정확도 향상이 극적이다.

| 작업 유형 | 표준 모델 정확도 | Reasoning 모델 정확도 | 비용 증가 | 비용 효율성 |
|----------|----------------|---------------------|----------|-----------|
| 단순 QA/분류 | 92% | 94% | 10x | 낮음 |
| 텍스트 요약 | 88% | 90% | 8x | 낮음 |
| 코드 생성 | 65% | 85% | 15x | 중간 |
| 수학 문제 | 60% | 95% | 20x | 높음 |
| 복잡한 논리 추론 | 45% | 80% | 25x | 높음 |
| 다단계 계획 수립 | 40% | 75% | 20x | 높음 |

---

## Reasoning 모델 프롬프팅 실전

Reasoning 모델은 기존 프롬프팅과 다른 접근이 필요하다. 불필요한 CoT 지시를 추가하면 오히려 성능이 저하될 수 있다.

### 표준 모델 vs Reasoning 모델 프롬프팅

```python
# 표준 모델 (GPT-4o) - CoT를 명시적으로 유도해야 함
standard_prompt = """
문제: 한 상점에서 사과 3개를 1200원에, 배 2개를 2000원에 판매한다.
사과 5개와 배 3개의 총 가격을 구하시오.

단계별로 생각하여 풀어주세요:
1. 먼저 사과 1개의 가격을 계산
2. 그 다음 배 1개의 가격을 계산
3. 최종 답을 구하세요
"""

# Reasoning 모델 (o1, DeepSeek-R1) - 간결하게 문제만 제시
reasoning_prompt = """
한 상점에서 사과 3개를 1200원에, 배 2개를 2000원에 판매한다.
사과 5개와 배 3개의 총 가격을 구하시오.
"""
# 모델이 자체적으로 최적의 추론 경로를 선택
```

### Reasoning 모델 프롬프팅 가이드

| 원칙 | 표준 모델 | Reasoning 모델 |
|------|---------|---------------|
| CoT 지시 | "단계별로 생각하세요" 추가 | 불필요 (자동 수행) |
| 구체적 단계 제시 | 효과적 | 오히려 방해될 수 있음 |
| 문제 설명 | 상세하게 | 핵심만 간결하게 |
| Few-shot 예시 | 3~5개 권장 | 1~2개 또는 불필요 |
| System prompt | 역할 부여 효과적 | 최소한으로 유지 |
| Temperature | 0.0~0.7 | 모델이 내부적으로 관리 |

### DeepSeek-R1 API 호출 예시

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-deepseek-api-key",
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-reasoner",
    messages=[
        {"role": "user", "content": "피보나치 수열의 100번째 항을 구하시오."}
    ],
    # temperature, top_p 등은 reasoning 모델에서 무시됨
)

# reasoning_content: 모델의 "생각 과정" (reasoning tokens)
print("=== Reasoning Process ===")
print(response.choices[0].message.reasoning_content)

# content: 최종 답변
print("=== Final Answer ===")
print(response.choices[0].message.content)

# 토큰 사용량 확인
print(f"Reasoning tokens: {response.usage.completion_tokens_details.reasoning_tokens}")
print(f"Output tokens: {response.usage.completion_tokens}")
```

---

## Reasoning vs Standard 모델 선택 가이드

### 의사결정 매트릭스

| 판단 기준 | 표준 모델 선택 | Reasoning 모델 선택 |
|----------|--------------|-------------------|
| **작업 복잡도** | 단순 (1~2단계) | 복잡 (3단계 이상) |
| **정확도 요구** | 90% 이상이면 충분 | 95%+ 필수 |
| **레이턴시 제약** | 2초 이내 응답 필요 | 30초+ 허용 |
| **비용 예산** | 제한적 | 정확도 우선 |
| **작업 유형** | 분류, 요약, 번역 | 수학, 코딩, 논리 |
| **사용 패턴** | 대량 배치 처리 | 소량 고품질 처리 |
| **사용자 기대** | 즉시 응답 | 정확한 결과 |

### 작업별 권장 모델

| 작업 | 권장 모델 유형 | 이유 |
|------|-------------|------|
| 고객 문의 응답 | 표준 (GPT-4o) | 빠른 응답, 패턴 매칭 충분 |
| 이메일 작성 | 표준 (Claude 3.5) | 창의성 + 속도 |
| 코드 리뷰 | Reasoning (o1) | 논리적 결함 탐지 필요 |
| 수학 과외 | Reasoning (DeepSeek-R1) | 단계별 풀이 과정 필수 |
| 법률 문서 분석 | Reasoning (o3) | 높은 정확도, 다단계 논리 |
| 데이터 분류 | 표준 (GPT-4o-mini) | 대량 처리, 비용 효율 |
| 연구 문제 풀이 | Reasoning (o3) | 최고 수준의 추론 필요 |
| 챗봇 | 표준 (GPT-4o) | 실시간 응답 필수 |
| 코드 생성 | 하이브리드 | 간단한 코드는 표준, 알고리즘은 reasoning |

---

## HW 축: Inference 최적화 개요

HW Inference 최적화는 모델의 추론 품질을 유지하면서, **같은 작업을 더 적은 시간과 자원으로 수행**하는 접근법이다. Reasoning 모델이 더 많은 토큰을 생성하기 때문에, Inference 최적화의 중요성은 더욱 커지고 있다.

### 핵심 Inference 최적화 기법

| 기법 | 최적화 대상 | 속도 향상 | 품질 영향 | 적용 난이도 |
|------|-----------|----------|----------|-----------|
| **양자화** (INT8/INT4) | 메모리, 연산 | 2~4x | 소폭 저하 | 낮음 |
| **KV-Cache** | 메모리 | 필수 기능 | 없음 | 낮음 |
| **PagedAttention** | 메모리 단편화 | 1.5~2x | 없음 | vLLM 사용 |
| **Flash Attention** | 어텐션 연산 | 2~4x | 없음 | 프레임워크 내장 |
| **Continuous Batching** | GPU 활용률 | 2~5x | 없음 | 서빙 프레임워크 |
| **Speculative Decoding** | 디코딩 속도 | 2~3x | 없음 (수학적 동일) | 중간 |
| **Tensor Parallelism** | 레이턴시 | ~N/GPU | 없음 | 높음 (NVLink 필요) |
| **Pipeline Parallelism** | 메모리 용량 | 처리량 증가 | 없음 | 중간 |

### 서빙 프레임워크 비교

| 프레임워크 | 핵심 특징 | 주요 최적화 | 추론 모델 지원 |
|-----------|----------|-----------|-------------|
| **vLLM** | PagedAttention, 높은 처리량 | Continuous batching, TP | O (긴 시퀀스 효율적) |
| **TGI** | HuggingFace 통합, 사용 편의성 | Flash Attention, Quantization | O |
| **TensorRT-LLM** | NVIDIA 최적화, 최고 성능 | FP8/INT4, Custom kernels | O |
| **Ollama** | 로컬 실행 특화, 간편 인터페이스 | GGUF 양자화, Metal (macOS) | O (R1 지원) |
| **SGLang** | 프로그래머블 서빙 | RadixAttention, 구조화 출력 | O |

---

## 두 축의 교차점

SW Reasoning과 HW Inference는 독립적 영역이 아니라, 여러 지점에서 교차한다.

### 추론 모델의 Inference 비용 문제

추론 모델은 긴 CoT를 생성하므로, 일반 LLM 대비 **토큰 생성량이 5~10배** 많다. 이는 곧:
- KV-Cache 메모리 사용량 급증 (수천~수만 토큰의 reasoning chain)
- 추론 시간(latency) 증가 (사용자 대기 시간 30초 이상)
- API 비용 상승 (reasoning token도 과금)

따라서 추론 모델일수록 HW Inference 최적화가 더 절실하다. [[deepseek-r1|DeepSeek-R1]]의 MoE 아키텍처 선택도 이 맥락에서 이해할 수 있다 -- 671B 파라미터 중 실제 활성화되는 것은 37B에 불과하여, Inference 비용을 크게 절감한다.

### 양자화된 추론 모델

4비트 양자화된 DeepSeek-R1이나 QwQ-32B는 소비자급 GPU(RTX 3090/4090)에서도 실행 가능하다. 최근 연구들은 **추론 과정(CoT)이 양자화에 상대적으로 견고(robust)**하다는 결과를 보여준다. 추론의 "논리 구조"는 가중치의 미세한 정밀도보다는 모델의 고수준 패턴에 의존하기 때문이다.

| 모델 | 양자화 | VRAM 요구량 | MATH-500 정확도 | 정확도 손실 |
|------|--------|-----------|---------------|-----------|
| DeepSeek-R1 (671B) | FP16 | ~1.3TB | 97.3% | 기준 |
| DeepSeek-R1 (671B) | INT4 | ~170GB | ~95% | ~2.3% |
| DeepSeek-R1-Distill-14B | FP16 | ~28GB | 93.9% | 3.4% |
| DeepSeek-R1-Distill-7B | FP16 | ~14GB | 92.8% | 4.5% |
| QwQ-32B | FP16 | ~64GB | 90.6% | 6.7% |
| QwQ-32B | INT4 | ~16GB | ~88% | ~9.3% |

### Speculative Decoding + Reasoning

작은 모델이 CoT 초안을 생성하고, 큰 모델이 검증하는 구조는 Speculative Decoding과 자연스럽게 결합된다. 초안 모델이 "빠르게 생각"하고, 검증 모델이 "깊게 검증"하는 구조는 CoT의 "생각 -> 검증" 패턴과 구조적으로 유사하다.

---

## 실전: 비용 최적화 전략

### 단계별 최적화 접근

| 단계 | 전략 | 설명 | 비용 절감 |
|------|------|------|----------|
| 1단계 | **라우팅** | 간단한 질문은 표준 모델, 복잡한 질문만 reasoning 모델로 분기 | 50~70% |
| 2단계 | **Compute budget 조절** | o3-mini의 low/medium/high 설정 활용 | 30~50% |
| 3단계 | **증류** | Reasoning 모델의 CoT를 작은 모델에 증류하여 배치 처리 | 80~90% |
| 4단계 | **캐싱** | 유사 질문에 대한 reasoning 결과 캐싱 | 변동 |
| 5단계 | **양자화 배포** | 증류된 모델을 INT4로 양자화하여 로컬 추론 | 95%+ |

### 하이브리드 파이프라인 설계

실전에서는 단일 모델만 사용하는 경우가 드물다. 복잡도에 따라 모델을 동적으로 선택하는 라우팅 전략이 효과적이다.

```python
def route_query(query: str, complexity_score: float) -> str:
    """질문 복잡도에 따라 적절한 모델을 선택하는 라우터"""
    if complexity_score < 0.3:
        # 단순 질문: 빠르고 저렴한 모델
        return "gpt-4o-mini"
    elif complexity_score < 0.7:
        # 중간 복잡도: 범용 모델
        return "gpt-4o"
    else:
        # 높은 복잡도: reasoning 모델
        return "o3-mini"  # budget: "high"

# 복잡도 판단 기준 예시
complexity_indicators = {
    "수학 수식 포함": +0.3,
    "다단계 논리 필요": +0.3,
    "코드 생성 요청": +0.2,
    "단순 분류/추출": -0.3,
    "번역/요약": -0.2,
}
```

---

## 시리즈 로드맵

이 글은 아래 후속 컨텐츠들의 "지도" 역할을 한다.

### SW Reasoning 경로
1. [[test-time-compute-scaling]]: Test-time compute scaling 원리와 실전
2. [[process-reward-models]]: 단계별 보상으로 추론 품질 향상
3. [[self-consistency]]: 다중 경로 샘플링과 다수결 투표
4. [[tree-of-thoughts]]: 트리 구조 추론 탐색
5. [[deepseek-r1]]: RL 기반 reasoning 모델의 핵심 발견

### HW Inference 경로
1. 양자화 심화: NVFP4와 현대 양자화 포맷 비교
2. 추론 최적화: Prefill vs Decode 파이프라인, KV-Cache, Speculative Decoding
3. Multi-GPU: DDP, FSDP, Tensor Parallelism 실전
4. NVLink: GPU 인터커넥트가 병렬 처리에 미치는 영향

---

## 정리

| 축 | 핵심 질문 | 대표 기술 | 비용 | 적합 상황 |
|-----|----------|----------|------|----------|
| **SW Reasoning** | 어떻게 더 잘 생각하게 할까? | CoT, Self-Consistency, ToT, PRM, 추론 모델 | 더 많은 토큰 생성 | 수학, 코딩, 논리 추론 |
| **HW Inference** | 어떻게 더 빠르게 실행할까? | 양자화, KV-Cache, Flash Attention, Multi-GPU | 구현 복잡도, HW 투자 | 실시간 서빙, 대량 처리 |
| **교차점** | 두 축의 균형은? | Speculative Decoding, 양자화된 추론 모델, MoE | 설계 트레이드오프 | 추론 모델의 프로덕션 배포 |

두 축은 경쟁 관계가 아니라 **보완 관계**다. SW Reasoning이 "생각의 품질"을 높이면, HW Inference가 "생각의 비용"을 낮추고, 그 결과 더 많은 사람이 더 나은 AI를 사용할 수 있게 된다. 실전에서의 핵심은 **작업 특성에 맞는 모델 선택과 비용 최적화 전략**이다. 단순 작업에 reasoning 모델을 사용하는 것은 낭비이고, 복잡한 추론 작업에 표준 모델을 사용하는 것은 품질 저하를 초래한다. 이 시리즈에서는 각 축의 핵심 기술을 하나씩 깊이 다루며, 최적의 균형점을 찾는 방법을 탐구한다.
