## 개요

"Chain-of-Thought Prompting Elicits Reasoning in Large Language Models"(Wei et al., 2022)는 Google Research의 Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter, Fei Xia, Ed Chi, Quoc Le, Denny Zhou가 NeurIPS 2022에서 발표한 논문입니다. 이 연구는 대규모 언어 모델(LLM)의 추론 능력을 끌어내는 가장 간단하면서도 강력한 방법 중 하나인 **Chain-of-Thought(CoT) 프롬프팅**을 제안했습니다.

핵심 아이디어는 놀라울 정도로 단순합니다. Few-shot 프롬프트의 예시에 최종 답변만 제공하는 것이 아니라, **답에 이르는 중간 추론 단계(chain of thought)를 자연어로 함께 서술**하면, 모델이 새로운 문제에 대해서도 비슷한 단계적 추론을 수행하게 되어 정확도가 극적으로 향상됩니다.

![표준 프롬프팅과 CoT 프롬프팅의 비교](figures/fig_1.png)
*표준 Few-shot 프롬프팅(왼쪽)은 입력-출력 쌍만 제시하여 모델이 바로 답을 출력하도록 유도하는 반면, CoT 프롬프팅(오른쪽)은 중간 추론 과정을 자연어로 서술하여 모델이 단계적으로 사고한 후 정답에 도달하도록 유도한다. 파란색 하이라이트가 추론 체인(chain of thought)에 해당한다.*

이 논문은 프롬프트 엔지니어링의 패러다임을 근본적으로 바꾸었습니다. 발표 이후 Google Scholar 기준 10,000회 이상 인용되었으며, Zero-shot CoT, [[self-consistency]], [[tree-of-thoughts]], [[program-of-thought]], [[react-agent]] 등 수백 편의 후속 연구를 촉발했습니다. 현대 LLM 응용에서 CoT는 사실상 표준적인 프롬프팅 기법이 되었습니다.

## 배경 및 문제

### LLM의 추론 능력 한계

2020년대 초반, GPT-3(175B), PaLM(540B) 등의 대규모 언어 모델은 번역, 요약, 질의응답 등 다양한 자연어 처리 태스크에서 놀라운 성능을 보여주었습니다. 하지만 **다단계 추론(multi-step reasoning)**이 필요한 문제에서는 여전히 취약했습니다.

특히 다음과 같은 유형의 문제들이 어려웠습니다.

- **산술 추론**: "사과 5개를 가진 철수가 3명의 친구에게 각각 2개씩 나눠주면 남는 사과는?"과 같이 여러 연산을 순차적으로 수행해야 하는 문제
- **상식 추론**: "빗자루로 무엇을 할 수 있는가?"와 같이 여러 상식 지식을 결합해야 하는 문제
- **기호 추론**: 특정 규칙을 여러 단계에 걸쳐 적용하는 문제

이런 문제의 공통점은 답에 도달하기 위해 **여러 개의 논리적 단계를 순차적으로 수행**해야 한다는 것입니다. 인간은 이런 문제를 풀 때 종이에 중간 과정을 적으면서 생각을 정리하지만, 기존 LLM은 입력을 받으면 바로 최종 답을 출력하도록 학습되어 있어 이런 단계적 추론이 어려웠습니다.

### 기존 접근법의 한계

이 문제를 해결하기 위한 기존 접근법들에는 다음과 같은 한계가 있었습니다.

**1. 태스크별 파인튜닝**: Cobbe et al.(2021)의 GSM8K 연구처럼, 수만 개의 (문제, 풀이과정, 답) 삼중쌍을 수작업으로 레이블링하여 모델을 파인튜닝하는 방법입니다. 효과적이지만, 태스크마다 대규모 레이블 데이터를 수집해야 하며 대규모 모델의 파인튜닝에는 막대한 컴퓨팅 비용이 듭니다.

**2. Scratchpad 방법(Nye et al., 2021)**: 모델이 중간 계산 과정을 "연습장(scratchpad)"에 적도록 학습시키는 방법입니다. 효과적이지만 역시 파인튜닝이 필요합니다.

**3. 형식적 언어로의 변환**: 자연어 문제를 수학 공식이나 프로그래밍 코드로 변환한 뒤, 외부 실행기(solver/interpreter)로 풀어내는 방법입니다. 정확하지만, 자연어에서 형식 언어로의 변환 자체가 어렵고, 상식 추론처럼 형식화가 어려운 문제에는 적용하기 힘듭니다.

**4. 표준 Few-shot 프롬프팅**: Brown et al.(2020)의 GPT-3 논문 이후 주류가 된 방법으로, 입력-출력 쌍의 예시를 제공합니다. 파인튜닝이 필요 없지만, 복잡한 추론 문제에서는 성능이 낮았습니다.

CoT 프롬프팅은 이러한 한계를 동시에 극복합니다. 파인튜닝 없이, 단지 프롬프트 예시의 형식을 바꾸는 것만으로 추론 성능을 대폭 향상시킬 수 있기 때문입니다.

### 핵심 관찰

이 논문의 출발점은 간단한 관찰에서 비롯됩니다. 인간은 복잡한 문제를 풀 때 한 번에 답을 내지 않습니다. 중간 단계를 거치며 사고를 전개합니다. 이 과정을 few-shot 예시에 명시적으로 포함시키면, LLM도 유사한 방식으로 추론을 전개하지 않을까 하는 것입니다.

이 관찰은 두 가지 가설에 기반합니다.

1. **사전학습 코퍼스의 추론 패턴 내재화**: LLM은 사전학습 과정에서 이미 단계별 추론의 패턴을 학습했을 가능성이 있습니다. 웹 텍스트에는 수학 풀이, 논증, 설명 등 단계적 사고가 포함된 텍스트가 다수 존재합니다.
2. **Few-shot 예시의 출력 형식 유도 효과**: Few-shot 예시가 모델의 출력 형식을 결정한다면, 추론 과정을 포함한 예시는 모델이 추론 과정을 포함한 출력을 생성하도록 유도할 것입니다.

## 핵심 아이디어

### Chain-of-Thought의 정의

Chain-of-Thought(연쇄적 사고)란 **최종 답에 이르기까지의 일련의 중간 자연어 추론 단계**를 말합니다. CoT 프롬프팅은 few-shot 예시에 이러한 추론 체인을 포함시켜, 모델이 새로운 문제에서도 유사한 추론 체인을 생성하도록 유도하는 방법입니다.

구체적으로, 표준 few-shot과 CoT few-shot의 차이를 비교하면 다음과 같습니다.

**표준 few-shot 예시:**

```
Q: 로저는 테니스공 5개를 가지고 있다. 그는 2캔을 더 샀다.
   캔마다 3개의 공이 들어 있다. 지금 몇 개의 공이 있는가?
A: 11개
```

**CoT few-shot 예시:**

```
Q: 로저는 테니스공 5개를 가지고 있다. 그는 2캔을 더 샀다.
   캔마다 3개의 공이 들어 있다. 지금 몇 개의 공이 있는가?
A: 로저는 처음에 5개의 공을 가지고 있었다.
   테니스공 2캔은 각 3개씩이므로 2 x 3 = 6개다.
   5 + 6 = 11. 정답은 11개다.
```

차이는 답 이전에 **자연어로 된 추론 과정을 서술**하는 것뿐입니다. 이 간단한 변경이 모델의 추론 성능을 극적으로 바꿔놓습니다.

### CoT의 세 가지 핵심 특성

논문에서는 CoT 프롬프팅의 세 가지 매력적인 특성을 강조합니다.

**1. 분해(Decomposition)**: 복잡한 다단계 문제를 중간 단계들로 분해하여, 각 단계에서 더 많은 연산 자원(토큰)을 할당할 수 있습니다. 이는 사실상 모델의 "thinking time"을 확장하는 효과가 있습니다. Transformer 아키텍처에서 단일 forward pass의 depth는 고정되어 있지만, 추론 체인을 통해 **sequential depth를 동적으로 확장**하는 셈입니다.

**2. 해석 가능성(Interpretability)**: 모델의 추론 과정이 자연어로 서술되므로, 모델이 어디에서 틀렸는지 디버깅할 수 있습니다. 이는 블랙박스 문제를 부분적으로 완화합니다. 다만 모델의 내부 계산이 실제로 생성된 추론 체인을 "따르는지"는 별개의 문제이며, 이는 이후 faithfulness 연구의 주제가 됩니다.

**3. 범용성(Generality)**: 산술, 상식, 기호 추론 등 다양한 추론 유형에 동일한 접근법을 적용할 수 있으며, 인간이 언어로 풀 수 있는 모든 종류의 문제에 원칙적으로 적용 가능합니다.

## 방법론

### 프롬프트 구조와 수식적 해석

표준 프롬프팅에서 모델은 다음 확률을 직접 모델링합니다.

$$P(a \mid q, E)$$

여기서 $q$는 질문, $a$는 답변, $E = \{(q_1, a_1), \ldots, (q_k, a_k)\}$는 $k$개의 few-shot 예시 집합입니다.

CoT 프롬프팅에서는 중간 추론 경로 $r$(rationale)을 잠재 변수로 도입합니다.

$$P(a \mid q, E_{\text{CoT}}) = \sum_{r} P(a \mid r, q) \cdot P(r \mid q, E_{\text{CoT}})$$

여기서 $E_{\text{CoT}} = \{(q_1, r_1, a_1), \ldots, (q_k, r_k, a_k)\}$입니다. 실제로는 greedy decoding으로 하나의 $r$만 생성하므로, 모델은 가장 가능성 높은 추론 경로 $r^*$를 먼저 생성한 뒤 그로부터 답 $a$를 도출하는 2단계 구조가 됩니다.

$$r^* = \arg\max_{r} P(r \mid q, E_{\text{CoT}})$$
$$a^* = \arg\max_{a} P(a \mid r^*, q)$$

이 구조의 핵심적 의미는, 추론 문제를 여러 개의 쉬운 하위 문제로 분해하는 효과를 낸다는 점입니다. 각 추론 단계가 다음 단계의 컨텍스트가 되므로, 모델은 전체 문제를 한 번에 풀지 않고 순차적으로 접근할 수 있습니다.

### 정보 이론적 관점: 연산 예산의 확장

정보 이론적으로 CoT의 효과를 이해할 수도 있습니다. 표준 프롬프팅에서 모델은 질문에서 답으로의 직접적인 매핑을 수행합니다. 이때 다단계 추론이 필요한 문제에서는 **정보 병목(information bottleneck)**이 발생합니다. 즉, 단일 forward pass의 연산량으로는 복잡한 추론 체인을 내부적으로 처리하기 어렵습니다.

CoT는 중간 단계를 **명시적으로 생성**함으로써 이 병목을 완화합니다. 각 토큰 생성 단계에서 Transformer의 전체 계산 능력이 활용되므로, 추론 체인이 길어질수록 더 많은 연산 자원이 문제 해결에 투입됩니다.

$$\text{Computation}_{\text{CoT}} = O(L_{\text{chain}} \cdot C_{\text{step}})$$

여기서 $L_{\text{chain}}$은 추론 체인의 토큰 수, $C_{\text{step}}$은 각 토큰 생성 시 Transformer가 수행하는 연산량입니다. 표준 프롬프팅에서는 $L_{\text{chain}} \approx 0$이므로, CoT는 본질적으로 **추론에 할당되는 연산 예산을 확장**하는 기법으로 볼 수 있습니다. 이 관점은 이후 "test-time compute scaling"이라는 연구 방향의 이론적 기반이 됩니다.

### 프롬프트 구성 상세

**예시 수**: 각 벤치마크에 대해 **8개의 few-shot 예시**를 사용했습니다. 각 예시는 (질문, 추론 체인, 최종 답)의 삼중 구조로 되어 있습니다.

**추론 체인 작성**: 추론 체인은 논문 저자들이 직접 수작업으로 작성했습니다. 형식적 제약 없이 자연스러운 문장으로 서술하되, 각 단계가 논리적으로 연결되도록 했습니다. 추론 체인의 길이는 태스크에 따라 다르며, 산술 문제는 평균 3-5문장, 기호 추론은 더 길어질 수 있습니다.

**자유 형식**: CoT의 핵심 특징 중 하나는 추론 체인의 형식을 엄격하게 규정하지 않는다는 것입니다. "먼저 ... 하면 ... 이므로 ... 따라서"와 같은 자연스러운 흐름이면 충분합니다. 이는 형식적 언어로의 변환이 필요한 기존 방법들과의 중요한 차별점입니다.

### 사용된 모델

논문에서는 다섯 개의 LLM 패밀리에 걸쳐 실험을 수행했습니다.

| 모델 | 파라미터 수 | 제공자 |
|------|-----------|-------|
| GPT-3 | 350M, 1.3B, 6.7B, 175B | OpenAI |
| LaMDA | 422M, 2B, 8B, 68B, 137B | Google |
| PaLM | 8B, 62B, 540B | Google |
| Codex | code-davinci-002 | OpenAI |
| UL2 | 20B | Google |

이렇게 다양한 모델 계열에서의 평가는 CoT의 효과가 특정 모델에 한정되지 않는 **일반적 현상**임을 보여주기 위한 핵심 실험 설계입니다.

### 디코딩 전략

논문에서는 기본적으로 **greedy decoding**(temperature = 0)을 사용했습니다. 이는 CoT의 효과를 가장 보수적으로 측정하기 위함입니다. Greedy decoding은 가장 확률이 높은 단일 경로만 탐색하므로, 이 조건에서의 성능 향상은 CoT의 효과에 대한 하한(lower bound)으로 볼 수 있습니다. 이후 Wang et al.(2022)의 [[self-consistency]] 연구에서는 다중 샘플링 후 다수결 투표(majority voting) 방식으로 CoT의 성능을 더욱 향상시켰습니다.

### 평가 벤치마크

논문은 세 영역, 총 12개의 벤치마크에서 CoT를 평가했습니다.

**산술 추론(Arithmetic Reasoning)** -- 5개 벤치마크:
- **GSM8K**: 초등학교 수준 수학 서술형 문제 (8.5K 문제, 2-8 추론 단계)
- **SVAMP**: 구조 변환이 적용된 다양한 수학 문제
- **ASDiv**: 다양성이 높은 수학 문제
- **AQuA**: 대수학 객관식 문제
- **MAWPS**: 수학 서술형 문제 (SingleOp, MultiArith 포함)

**상식 추론(Commonsense Reasoning)** -- 5개 벤치마크:
- **CSQA (CommonsenseQA)**: 일상적 상식에 기반한 5지선다 질의응답
- **StrategyQA**: 다단계 상식 추론이 필요한 예/아니오 질문
- **Date Understanding**: 날짜 관련 추론
- **Sports Understanding**: 스포츠 규칙 관련 추론
- **SayCan**: 로봇 행동 계획 관련 추론

**기호 추론(Symbolic Reasoning)** -- 2개 벤치마크:
- **Last Letter Concatenation**: 주어진 단어들의 마지막 글자를 순서대로 연결 (예: "Amy Brown" -> "yn")
- **Coin Flip**: 동전을 여러 번 뒤집거나 뒤집지 않은 후의 상태 추적

## 실험 결과

### 산술 추론: 스케일에 따른 CoT의 창발적 효과

CoT의 가장 인상적인 결과는 산술 추론에서 나타났습니다. GSM8K 벤치마크에서의 모델 크기별 결과는 다음과 같습니다.

| 모델 | 파라미터 | 표준 Few-shot | CoT Few-shot | 향상폭 |
|------|---------|--------------|-------------|-------|
| GPT-3 | 350M | 2.0% | 2.1% | +0.1%p |
| GPT-3 | 1.3B | 2.6% | 2.4% | -0.2%p |
| GPT-3 | 6.7B | 4.9% | 5.4% | +0.5%p |
| GPT-3 | 175B | 14.0% | **46.9%** | **+32.9%p** |
| LaMDA | 137B | 14.3% | **27.7%** | +13.4%p |
| PaLM | 8B | 4.1% | 3.2% | -0.9%p |
| PaLM | 62B | 18.1% | **33.0%** | +14.9%p |
| PaLM | 540B | 17.9% | **58.1%** | **+40.2%p** |

이 표에서 가장 주목할 점은 **스케일 의존성(scale dependence)**입니다. 350M-8B 범위의 소형 모델에서는 CoT가 거의 효과가 없거나 오히려 성능이 하락합니다. 반면 약 100B 파라미터를 넘어서면 CoT의 효과가 급격히 나타나며, PaLM 540B에서 40.2%p라는 극적인 향상을 보여줍니다.

이러한 **창발(emergence) 임계값**은 다음과 같이 추정됩니다.

$$N_{\text{threshold}} \approx 10^{11} \text{ parameters}$$

이 임계값 아래에서 CoT가 비효과적인 이유에 대해, 논문은 소형 모델이 유창하면서도 논리적인 추론 체인을 생성할 능력이 부족하기 때문이라고 설명합니다. 소형 모델은 추론 체인을 생성하긴 하지만, 그 내용이 비논리적이거나 문제와 무관한 경우가 많아 오히려 오답으로 이끕니다. 이는 CoT가 모델에 새로운 능력을 "부여"하는 것이 아니라, 이미 내재된 추론 능력을 "끌어내는(elicit)" 것임을 시사합니다 -- 논문 제목의 "elicits"가 이 점을 정확히 반영합니다.

PaLM 540B + CoT의 GSM8K 58.1% 정확도는 당시 파인튜닝 기반 SOTA인 GPT-3 175B + verifier(55%)를 초과하는 수치였습니다. **프롬프트 변경만으로 파인튜닝 모델을 능가**한 것입니다.

### 전체 산술 벤치마크 종합 (PaLM 540B 기준)

| 벤치마크 | 문제 유형 | 표준 Few-shot | CoT Few-shot | 이전 SOTA (파인튜닝) |
|---------|----------|--------------|-------------|-------------------|
| GSM8K | 초등 수학 | 17.9% | **58.1%** | 55.0% |
| SVAMP | 구조 변환 수학 | 79.0% | **86.6%** | 57.4% |
| ASDiv | 다양한 수학 | 74.0% | **81.2%** | 75.3% |
| AQuA | 대수 선다형 | 25.2% | **35.8%** | 37.9% |
| MAWPS (MultiArith) | 다중 연산 | 33.8% | **94.7%** | 60.5% |

GSM8K, SVAMP, MultiArith에서 CoT + PaLM 540B가 기존 파인튜닝 기반 SOTA를 넘어섰습니다. 특히 MultiArith에서의 33.8%에서 94.7%로의 향상은 CoT가 **다중 연산 문제에서 특히 효과적**임을 보여줍니다. 이는 여러 연산을 순차적으로 수행해야 하는 문제에서 단계별 추론의 이점이 극대화되기 때문입니다.

반면 AQuA(35.8%)에서는 파인튜닝 SOTA(37.9%)에 미치지 못한 점도 주목할 필요가 있습니다. AQuA는 대수학 객관식 문제로, 복잡한 대수적 변환이 필요하여 자연어 추론만으로는 한계가 있습니다. 이는 이후 [[program-of-thought]]에서 코드 생성 기반 추론으로 극복하려는 동기가 됩니다.

### 상식 추론 결과

![다양한 추론 유형에서의 CoT 프롬프트 예시](figures/fig_3.png)
*산술(Math Word Problems), 상식(CSQA, StrategyQA), 날짜 이해(Date Understanding), 기호 추론(Last Letter Concatenation, Coin Flip) 등 다양한 벤치마크에서의 CoT 프롬프트 입출력 예시. 각 태스크마다 추론 체인의 형태가 다르지만, 공통적으로 중간 추론 단계(색상 하이라이트)를 거쳐 정답에 도달하는 구조를 보인다.*

상식 추론은 세계에 대한 배경 지식을 기반으로 논리적 판단을 내리는 능력을 평가합니다.

| 벤치마크 | PaLM 540B (표준) | PaLM 540B (CoT) | 이전 SOTA (파인튜닝) |
|---------|-----------------|----------------|-------------------|
| CSQA | 72.1% | **79.9%** | 79.0% |
| StrategyQA | 65.4% | **73.0%** | 69.4% |
| Date Understanding | 62.3% | **77.1%** | -- |
| Sports Understanding | 92.0% | **95.4%** | -- |

StrategyQA에서 CoT 프롬프팅(73.0%)이 전용 파인튜닝 모델(69.4%)을 3.6%p 초과한 것은 특히 주목할 만합니다. StrategyQA는 "아리스토텔레스는 이메일을 사용했는가?"처럼 여러 사실을 조합하는 다단계 상식 추론이 필요한 벤치마크인데, CoT가 이런 유형의 문제에서도 효과적임을 보여줍니다.

상식 추론에서의 성능 향상폭(약 5-15%p)은 산술 추론(약 15-40%p)보다 상대적으로 작습니다. 이는 상식 추론이 지식(knowledge)과 추론(reasoning)이 혼합된 태스크이기 때문입니다. CoT가 추론 단계를 개선하더라도, 모델이 필요한 배경 지식 자체를 갖추지 못한 경우에는 효과가 제한됩니다.

### 기호 추론 결과: OOD 일반화

기호 추론은 CoT의 **일반화 능력**을 검증하는 데 특히 유용합니다. 학습 예시에서 보지 않은 조건(Out-of-Distribution)에서의 성능을 측정할 수 있기 때문입니다.

#### Last Letter Concatenation

단어들의 마지막 글자를 순서대로 이어 붙이는 태스크입니다. 예를 들어 "Jason Wei"의 답은 "ni"입니다. Few-shot 예시는 2단어로 구성했으나, 테스트 시에는 4단어(OOD)로도 평가했습니다.

| 조건 | 표준 Few-shot | CoT Few-shot |
|------|--------------|-------------|
| 2단어 (In-Domain) | 6.8% | **93.3%** |
| 4단어 (OOD) | 0.4% | **81.0%** |

#### Coin Flip

동전의 앞뒤를 추적하는 태스크입니다. 여러 사람이 동전을 뒤집거나 뒤집지 않은 후 최종 상태를 맞추는 문제입니다.

| 조건 | 표준 Few-shot | CoT Few-shot |
|------|--------------|-------------|
| 4번 (In-Domain) | 50.0% | **99.6%** |
| 8번 (OOD) | 50.0% | **97.5%** |

기호 추론에서 특히 중요한 발견은 **OOD(Out-of-Distribution) 일반화**입니다. 표준 few-shot은 OOD에서 거의 랜덤 수준으로 떨어지는 반면, CoT는 단계별 추론이 가능하므로 길이가 늘어나도 체계적으로 문제를 풀 수 있습니다. 이는 CoT가 단순한 패턴 매칭이 아니라, **알고리즘적 절차를 일반화하는 능력**을 LLM에 부여함을 시사합니다.

Last Letter Concatenation에서 표준 few-shot의 In-Domain 정확도가 6.8%에 불과한 점도 의미심장합니다. 이 태스크는 알고리즘적으로는 매우 단순하지만(각 단어의 마지막 글자를 추출하여 연결), 모델이 이 절차를 internal representation만으로 수행하기는 어렵습니다. CoT는 이 절차를 외부화(externalize)하여 각 단계를 명시적으로 수행하게 함으로써 93.3%의 정확도를 달성합니다.

### Ablation Study: CoT의 효과는 어디서 오는가?

논문에서는 CoT의 효과가 단순히 추가 토큰에 의한 것인지, 추론 구조 자체에 의한 것인지를 검증하기 위해 여러 ablation 실험을 수행했습니다.

| 변형 | GSM8K 정확도 | 분석 |
|------|------------|------|
| 표준 few-shot | 17.9% | 추론 체인 없음 |
| CoT (정상) | **58.1%** | 전체 추론 체인 포함 |
| 수식만 포함 | 43.2% | 자연어 설명 없이 수식만 |
| 답 뒤에 추론 배치 | 18.5% | 추론이 답 생성에 영향 못 줌 |
| 무관한 추론 체인 | 15.3% | 관련 없는 추론은 효과 없음 |

이 결과에서 얻을 수 있는 핵심 통찰은 다음과 같습니다.

- **자연어 설명의 기여**: 수식만(43.2%)으로는 CoT 전체 효과(58.1%)를 얻을 수 없습니다. 자연어 추론 서술이 약 14.9%p의 추가적 기여를 합니다. 자연어는 수식으로 표현하기 어려운 의미론적 추론(예: "2캔은 각 3개이므로"에서 "캔"과 "공"의 관계 파악)을 가능하게 합니다.
- **추론 순서의 인과적 효과**: 답을 먼저 생성하고 추론을 뒤에 붙이면(18.5%) 효과가 거의 사라집니다. 이는 추론 체인이 답 생성 과정에 **인과적으로** 영향을 미쳐야 한다는 것을 증명합니다. Autoregressive 모델에서 이전 토큰이 이후 토큰의 생성을 조건화하므로, 추론이 답 앞에 위치해야 합니다.
- **논리적 일관성의 필수성**: 무관한 체인을 넣으면 오히려 표준 few-shot(17.9%)보다 성능이 하락합니다(15.3%). CoT의 효과는 단순히 출력 길이를 늘리는 것이 아니라 **올바른 추론 경로를 유도**하는 것에서 옵니다.

### 추론 체인의 정확성 분석 및 오류 유형

PaLM 540B가 GSM8K에서 생성한 CoT를 인간이 수동 검증한 결과, 정답 50문제 중 **46문제(92%)**에서 추론 체인이 완전히 올바르다는 것이 확인되었습니다. 이는 CoT가 "우연히 맞는 답"을 내는 것이 아니라, 올바른 추론을 통해 올바른 답에 도달하는 메커니즘임을 지지합니다.

반면 오답 50문제를 분석한 결과, 오류 유형은 크게 세 가지로 분류됩니다.

- **의미론적 이해 오류(Semantic understanding)**: 문제의 의미를 잘못 해석하는 경우. 예를 들어 "각 사과의 절반"을 "사과 전체의 절반"으로 해석하는 오류.
- **한 단계 누락(One step missing)**: 추론 체인에서 필요한 단계 하나를 건너뛰는 경우. 논리 자체는 맞지만 특정 조건을 반영하지 않음.
- **기타 오류**: 환각(hallucination), 반복 출력, 기호 매핑 오류 등.

![모델 스케일 업에 따른 오류 수정 사례](figures/fig_10.png)
*PaLM 62B에서 540B로 스케일 업할 때 수정되는 오류의 구체적 사례. 62B 모델은 의미론적 이해 오류(배달 수수료 계산 누락, 속도 계산 실수)와 한 단계 누락 오류(최종 합산 단계 생략)를 보이지만, 540B 모델은 동일한 문제에서 올바른 추론 체인을 생성하여 정답에 도달한다. 이는 모델 크기 증가가 단순한 유창성이 아닌 추론의 정확성 자체를 향상시킴을 보여준다.*

주목할 점은 PaLM을 62B에서 540B로 스케일 업했을 때, **세 가지 오류 유형 모두에서 상당 부분이 수정**된다는 것입니다. 위 그림의 구체적 사례들을 살펴보면, 62B 모델이 "배달 수수료 25%를 가격에 적용"하는 과정에서 계산을 잘못하거나 속도-시간-거리 관계를 혼동하는 반면, 540B 모델은 동일한 문제에서 정확한 추론을 수행합니다. 이는 모델 크기의 증가가 단순히 언어 유창성뿐 아니라, 의미론적 이해와 추론의 완전성까지 향상시킨다는 것을 시사합니다.

## 의의 및 한계

### 의의

**1. 프롬프팅 패러다임의 전환**

CoT는 few-shot 프롬프팅의 패러다임을 근본적으로 바꾸었습니다. "입출력 예시"만 제공하던 방식에서 "추론 과정 예시"를 제공하는 방식으로의 전환은, 이후 모든 프롬프팅 연구의 기준점이 되었습니다.

**2. 파인튜닝 없는 추론 능력 강화**

모델 가중치를 수정하지 않고도, 프롬프트 구성만으로 파인튜닝 모델에 필적하는 추론 성능을 달성할 수 있음을 보여주었습니다. 이는 LLM 활용의 접근성을 크게 높인 발견입니다.

**3. 창발적 능력(Emergent Abilities)의 초기 증거**

특정 스케일 이상에서만 나타나는 CoT의 효과는 LLM의 창발적 능력에 대한 초기 실증 증거 중 하나입니다. 이 발견은 이후 Wei et al.(2022)의 "Emergent Abilities of Large Language Models" 논문으로 확장되어, 스케일링 연구의 주요 주제가 되었습니다.

**4. 후속 연구의 폭발적 촉발**

CoT는 이후 프롬프팅 및 추론 연구의 토대가 되었습니다.

| 후속 연구 | 핵심 아이디어 | 연도 |
|----------|------------|-----|
| Zero-shot CoT (Kojima et al.) | "Let's think step by step" 한 문장으로 CoT 유도 | 2022 |
| [[self-consistency]] (Wang et al.) | 다수의 추론 경로 생성 후 다수결 투표 | 2022 |
| Least-to-Most (Zhou et al.) | 문제를 하위 문제로 분해 후 순차 해결 | 2022 |
| Auto-CoT (Zhang et al.) | CoT 예시의 자동 생성 | 2022 |
| [[tree-of-thoughts]] (Yao et al.) | 추론 경로를 트리 구조로 탐색 | 2023 |
| [[program-of-thought]] (Chen et al.) | 추론 체인을 코드로 생성하여 실행 | 2023 |

특히 [[self-consistency]]는 CoT의 단일 greedy decoding 한계를 극복하여, 같은 문제에 대해 여러 추론 경로를 샘플링한 뒤 가장 빈번한 답을 선택하는 방법으로 GSM8K에서 추가 약 17%p의 성능 향상을 달성했습니다.

**5. 추론 시간 확장(Test-time Compute Scaling)의 시초**

CoT의 핵심 통찰 -- 모델이 답을 내기 전에 더 많이 "생각"하게 하면 성능이 올라간다 -- 은 이후 OpenAI의 o1 모델(2024)에서 극대화되었습니다. o1은 모델이 응답하기 전에 내부적으로 긴 추론 체인을 생성하도록 학습시킨 것으로, CoT의 아이디어가 프롬프팅 기법을 넘어 모델 학습 자체에 통합된 사례입니다. 이후 DeepSeek-R1(2025) 등 다양한 추론 특화 모델들이 이 방향을 계승하고 있습니다.

### 한계

**1. 대형 모델 의존성**: 약 100B 이상의 모델에서만 효과적이므로, 자원 제약 환경에서는 활용이 어렵습니다. 이후 모델 증류(distillation)를 통해 소형 모델에 CoT 능력을 전이하려는 연구들이 진행되었습니다(예: Fu et al., 2023의 Specializing Smaller Language Models).

**2. 수동 예시 작성의 비용**: 각 태스크에 적합한 CoT 예시를 인간이 직접 작성해야 합니다. 새로운 태스크마다 전문가가 예시를 작성해야 하므로, 완전한 자동화가 이루어지지 않았습니다. 이 한계는 이후 Zero-shot CoT(Kojima et al., 2022)의 "Let's think step by step"과 Auto-CoT(Zhang et al., 2022)에서 부분적으로 해결되었습니다.

**3. 추론 체인의 정확성 미보장(Unfaithful Reasoning)**: 모델이 생성하는 추론 체인이 항상 논리적으로 올바르다는 보장이 없습니다. 그럴듯하지만 잘못된 추론이 발생할 수 있으며, 이는 환각(hallucination)의 한 형태입니다. 더 근본적으로, 모델의 내부 연산 과정이 실제로 생성된 추론 체인을 "따르는지"도 불분명합니다(faithfulness 문제).

**4. 오류 전파(Error Cascading)**: 다단계 추론에서 앞선 단계의 오류가 후속 단계로 전파되어 최종 답이 틀릴 수 있습니다. 추론 체인이 길어질수록 이 위험은 누적됩니다. [[self-consistency]]에서 다중 샘플링으로, Process Reward Model(Lightman et al., 2023)에서 각 단계의 검증으로 완화를 시도했습니다.

**5. 추론 비용 증가**: CoT는 추가적인 토큰을 생성하므로, 표준 프롬프팅 대비 추론 시간과 API 비용이 증가합니다. 간단한 질문에도 긴 추론 체인을 생성하는 것은 비효율적이므로, 문제 난이도에 따라 CoT 적용 여부를 동적으로 결정하는 연구도 후속으로 등장했습니다.

**6. Greedy Decoding의 한계**: 논문에서는 단일 greedy decoding만 사용했습니다. 하나의 추론 경로만 생성하므로, 그 경로가 잘못되면 복구할 방법이 없습니다. 이는 [[self-consistency]]와 [[tree-of-thoughts]]에서 다중 경로 탐색으로 해결되었습니다.

## 코드 예제

### CoT 프롬프팅 파이프라인 구현 (Python)

다음은 CoT 프롬프팅의 핵심 메커니즘을 보여주는 구현입니다. 표준 few-shot과 CoT few-shot의 차이, 그리고 Self-Consistency 확장까지 포함합니다.

```python
import re
from dataclasses import dataclass


@dataclass
class FewShotExample:
    """Few-shot 예시 구조."""
    question: str
    rationale: str  # CoT에서만 사용
    answer: str


def build_standard_prompt(examples: list[FewShotExample], query: str) -> str:
    """표준 few-shot 프롬프트 구성.

    입력-출력 쌍만 포함하며, 중간 추론 과정은 제외합니다.
    """
    prompt_parts = []
    for ex in examples:
        prompt_parts.append(f"Q: {ex.question}\nA: {ex.answer}")
    prompt_parts.append(f"Q: {query}\nA:")
    return "\n\n".join(prompt_parts)


def build_cot_prompt(examples: list[FewShotExample], query: str) -> str:
    """CoT few-shot 프롬프트 구성.

    각 예시에 중간 추론 단계(rationale)를 포함하여,
    모델이 추론 과정을 생성한 뒤 답을 도출하도록 유도합니다.
    """
    prompt_parts = []
    for ex in examples:
        # 핵심: 답 이전에 추론 과정을 삽입
        prompt_parts.append(
            f"Q: {ex.question}\n"
            f"A: {ex.rationale} "
            f"따라서 정답은 {ex.answer}입니다."
        )
    prompt_parts.append(f"Q: {query}\nA:")
    return "\n\n".join(prompt_parts)


def extract_answer(response: str) -> str:
    """모델 응답에서 최종 답을 추출합니다."""
    match = re.search(r"정답은\s+(.+?)입니다", response)
    if match:
        return match.group(1).strip()
    numbers = re.findall(r"\d+", response)
    return numbers[-1] if numbers else response.strip()


def self_consistency(
    prompt: str,
    generate_fn,
    n_samples: int = 10,
    temperature: float = 0.7
) -> tuple:
    """Self-Consistency: 다중 추론 경로 샘플링 후 다수결 투표.

    Wang et al. (2022)의 방법으로,
    CoT의 greedy decoding 한계를 극복합니다.
    """
    from collections import Counter

    answers = []
    for _ in range(n_samples):
        response = generate_fn(prompt, temperature=temperature)
        answer = extract_answer(response)
        answers.append(answer)

    # 다수결 투표: 가장 빈번한 답 선택
    vote_counts = Counter(answers)
    majority_answer, count = vote_counts.most_common(1)[0]
    confidence = count / n_samples

    return majority_answer, confidence, vote_counts


# --- 사용 예시 ---

cot_examples = [
    FewShotExample(
        question="식당에 23명이 있었습니다. 5명이 나가고 8명이 들어왔습니다. 지금 몇 명인가요?",
        rationale="처음 23명에서 5명이 나가면 23 - 5 = 18명입니다. "
                  "8명이 새로 들어오면 18 + 8 = 26명입니다.",
        answer="26명"
    ),
    FewShotExample(
        question="사과 7개가 있습니다. 3봉지를 더 샀는데 봉지마다 4개씩 들어있습니다. 총 몇 개인가요?",
        rationale="처음 사과는 7개입니다. "
                  "3봉지에 각 4개이므로 3 x 4 = 12개를 추가로 얻었습니다. "
                  "7 + 12 = 19개입니다.",
        answer="19개"
    ),
]

query = "연필 15자루가 있습니다. 2다스를 더 샀습니다. 한 다스는 12자루입니다. 총 몇 자루인가요?"

# 표준 vs CoT 프롬프트 비교
standard_prompt = build_standard_prompt(cot_examples, query)
cot_prompt = build_cot_prompt(cot_examples, query)

print("=== 표준 Few-Shot ===")
print(standard_prompt)
print()
print("=== CoT Few-Shot ===")
print(cot_prompt)
```

### OpenAI API를 활용한 CoT 호출

```python
from openai import OpenAI

client = OpenAI()


def solve_with_cot(question: str, model: str = "gpt-4") -> dict:
    """Chain-of-Thought 프롬프팅으로 수학 문제를 해결합니다."""
    cot_system = (
        "당신은 수학 문제를 단계별로 풀어주는 도우미입니다. "
        "반드시 풀이 과정을 자세히 서술한 후 답을 제시하세요."
    )

    cot_user = f"""다음은 수학 문제를 단계별로 풀어가는 예시입니다.

Q: 주차장에 자동차가 3대 있었습니다. 2대가 더 왔습니다.
   주차장에 자동차가 총 몇 대인가요?
A: 처음에 주차장에 3대가 있었습니다.
   2대가 더 왔으므로 3 + 2 = 5대입니다.
   따라서 정답은 5대입니다.

Q: 레아는 초콜릿 32개를 가지고 있고, 언니는 레아보다 42개
   더 많이 가지고 있습니다. 둘을 합치면 총 몇 개인가요?
A: 레아는 32개를 가지고 있습니다.
   언니는 레아보다 42개 더 많으므로 32 + 42 = 74개입니다.
   둘을 합치면 32 + 74 = 106개입니다.
   따라서 정답은 106개입니다.

Q: {question}
A:"""

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": cot_system},
            {"role": "user", "content": cot_user}
        ],
        temperature=0,
        max_tokens=512
    )

    return {
        "question": question,
        "reasoning_chain": response.choices[0].message.content,
        "model": model
    }


def solve_with_zero_shot_cot(question: str, model: str = "gpt-4") -> str:
    """Zero-shot CoT: 예시 없이 한 문장으로 추론을 유도합니다."""
    response = client.chat.completions.create(
        model=model,
        messages=[{
            "role": "user",
            "content": f"{question}\n\n단계별로 생각해 봅시다."
        }],
        temperature=0,
        max_tokens=1024
    )
    return response.choices[0].message.content
```

위 코드 예제들은 CoT 프롬프팅의 기본 구현부터 Self-Consistency를 결합한 향상된 버전, 그리고 가장 간단한 Zero-shot CoT까지를 보여줍니다. 실제 프로덕션 환경에서는 프롬프트 캐싱, 에러 핸들링, 비용 모니터링 등을 추가로 고려해야 합니다.

CoT는 단순한 프롬프팅 기법을 넘어, LLM이 "생각하는" 방식 자체를 변화시킨 패러다임입니다. 현대 LLM 응용에서 CoT는 선택이 아닌 필수가 되었으며, 앞으로도 추론 능력 향상의 핵심 축으로 남을 것입니다.
