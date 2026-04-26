<!-- infographic-hero -->
![ReAct 핵심 요약](figures/infographic.svg)

*Figure: ReAct 한 장 요약 인포그래픽*

# ReAct: 추론과 행동의 결합

**Princeton/Google** · **2022-10-06** · **Agent Technique** · **오픈**

## 개요

ReAct(Reasoning + Acting)는 언어 모델이 추론(Reasoning)과 행동(Acting)을 교차 반복하는 패러다임으로, AI 에이전트 분야의 핵심 기반 기법이다. Yao et al.(Princeton/Google, 2022)이 논문 "ReAct: Synergizing Reasoning and Acting in Language Models"에서 제안한 이 프레임워크는, CoT(Chain-of-Thought)의 내부 추론 능력과 외부 도구 활용을 결합하여 **AI 에이전트의 기초를 확립**했다.

ReAct의 핵심 통찰은 **"추론만으로는 불완전하고, 행동만으로는 비효율적"**이라는 것이다. 순수 CoT는 모델 내부 지식에만 의존하므로 사실 환각(hallucination)에 취약하다. 반대로 행동만 반복하는 에이전트는 전략 없이 무작위 탐색에 가깝다. ReAct는 Thought(생각) $\rightarrow$ Action(행동) $\rightarrow$ Observation(관찰) 사이클을 반복함으로써, 추론이 행동을 안내하고 행동의 결과가 추론을 보강하는 시너지를 실현한다.

ReAct가 AI 에이전트 분야에 미친 영향은 절대적이다. 이후 LangChain의 AgentExecutor, AutoGen의 ConversableAgent, Claude의 tool use, LangGraph의 에이전트 노드 등 **사실상 모든 에이전트 시스템이 ReAct 패턴을 기본 추론 루프로 채택**했다. ReAct는 현대 AI 에이전트의 "hello world"에 해당하는 기초 패러다임이다.

아래 그림은 Standard, CoT, Act-only, ReAct 네 가지 프롬프팅 방법을 HotpotQA와 ALFWorld 태스크에서 비교한 것이다.

![네 가지 프롬프팅 방법(Standard, CoT, Act-only, ReAct) 비교 - HotpotQA 및 ALFWorld 태스크](figures/fig_1.png)
*Figure 1: 네 가지 프롬프팅 방법 비교 - (1a) Standard, (1b) CoT(추론만), (1c) Act-only, (1d) ReAct(추론+행동)로 HotpotQA 문제를 해결하는 과정과, ALFWorld 게임에서의 Act-only vs ReAct 비교. (Source: Yao et al., 2022)*

![ReAct 아키텍처 - Thought-Action-Observation 사이클 기반 추론과 행동 결합 에이전트 구조](figures/architecture.svg)

*Figure 2: ReAct 아키텍처 - Thought(추론)로 전략을 수립하고 Action(행동)으로 외부 도구를 호출한 뒤 Observation(관찰)으로 결과를 반영하는 에이전틱 루프를 반복하여 추론과 행동의 시너지를 실현한다.*

## 아키텍처 상세

ReAct의 에이전틱 루프는 세 가지 요소로 구성된다.

### Thought-Action-Observation 사이클

**Thought (생각)**: 현재 상황을 분석하고 다음 행동을 계획하는 언어적 추론 단계. CoT의 단계별 사고를 에이전트 루프에 통합한 것이다.

**Action (행동)**: 외부 도구(검색 엔진, API, 계산기 등)를 실행하는 구체적 행동. 미리 정의된 행동 공간(action space)에서 선택한다.

**Observation (관찰)**: 행동 결과를 환경으로부터 수신. 이 결과가 다음 Thought의 입력이 된다.

```
질문: "Apple의 CEO는 누구이며, 그 사람의 나이는?"

Thought 1: Apple의 CEO를 먼저 찾아야 한다.
Action 1: Search["Apple CEO 2024"]
Observation 1: Tim Cook은 Apple의 CEO이다.
              1960년 11월 1일 출생.

Thought 2: Tim Cook이 CEO이고, 1960년생이다.
           현재 나이를 계산해야 한다.
Action 2: Calculator["2024 - 1960"]
Observation 2: 64

Thought 3: Tim Cook은 Apple의 CEO이며, 63-64세이다.
           충분한 정보가 모였으므로 답변을 생성한다.
Action 3: Finish["Apple의 CEO는 Tim Cook이며, 63-64세이다."]
```

### 수학적 정의

ReAct의 정책(policy)을 수학적으로 표현하면:

$$\pi_{\text{ReAct}}(a_t | o_t, c_t) = \text{LLM}(\text{thought}_t, \text{action}_t | o_{1:t}, a_{1:t-1}, c_t)$$

여기서 $o_t$는 관찰, $c_t$는 컨텍스트, $a_t$는 행동이며, LLM이 사고(thought)와 행동(action)을 동시에 생성한다. 기존 행동 전용 에이전트가 $\pi(a_t | o_t)$만 모델링하는 것과 대조적으로, ReAct는 명시적 추론을 통해 행동 선택의 근거를 제공한다.

이를 그래프 구조로 표현하면, ReAct는 세 노드(Thought, Action, Observation)의 사이클 그래프다.

$$G = (\{T, A, O\}, \{T \rightarrow A, A \rightarrow O, O \rightarrow T\})$$

이 사이클 구조가 바로 LangGraph가 "사이클을 허용하는 그래프"로 에이전트를 모델링하게 된 직접적 근거다.

### 행동 공간(Action Space)

ReAct의 행동 공간은 태스크에 따라 정의된다.

| 태스크 도메인 | 행동 공간 | 예시 |
|-------------|----------|------|
| 지식 추론 | Search, Lookup, Finish | HotpotQA, Fever |
| 수학 | Calculator, Finish | GSM8K |
| 가상 환경 | go, take, open, put, use | ALFWorld |
| 웹 탐색 | click, type, scroll | WebShop |

### Few-Shot 프롬프팅

ReAct는 CoT와 동일하게 few-shot 예시를 통해 구현된다. Thought-Action-Observation 트리플을 few-shot 예시로 제공하면, 모델이 이 패턴을 따라 새로운 문제를 해결한다. 별도의 파인튜닝 없이 프롬프트 엔지니어링만으로 구현 가능하다.

## 핵심 혁신

1. **추론-행동 시너지**: 추론은 행동 계획을 안내하고, 행동 결과는 추론을 보강하는 선순환 구조를 확립했다. 이는 이후 모든 에이전트 프레임워크의 기본 추론 루프가 되었다.

2. **외부 지식 접근**: 모델 내부 지식에만 의존하는 CoT의 환각 문제를 외부 도구 활용으로 해결했다. 검색 엔진으로 최신 정보를 확인하고, 계산기로 정확한 연산을 수행할 수 있다.

3. **해석 가능한 에이전트 행동**: Thought 단계가 에이전트의 추론 과정을 명시적으로 드러내므로, 왜 특정 행동을 선택했는지 이해하고 디버깅할 수 있다. 아래 예시는 ReAct가 외부 검색을 통해 오래된 정답 라벨을 극복하고 최신 정보를 얻는 과정을 보여준다.

![ReAct가 외부 검색으로 최신 정보를 획득하여 오래된 라벨을 극복하는 예시](figures/fig_8.png)
*Figure 5: 외부 지식 접근의 강점 - HotpotQA에서 정답 라벨이 구식(outdated)인 경우, ReAct만이 실시간 웹 검색과 추론을 결합하여 최신 정보를 획득한다. (Source: Yao et al., 2022)*

4. **범용 에이전트 패러다임**: 지식 추론(HotpotQA), 사실 검증(Fever), 대화형 게임(ALFWorld), 웹 탐색(WebShop) 등 다양한 도메인에 동일한 패러다임이 적용 가능함을 입증했다.

## 벤치마크/성능

| 벤치마크 | 메트릭 | CoT 단독 | 행동 단독 | ReAct | 향상 |
|---------|--------|---------|---------|-------|------|
| HotpotQA | EM | 29.4% | 25.7% | **34.2%** | +4.8%p |
| Fever | Accuracy | 56.3% | 58.2% | **64.6%** | +6.4%p |
| ALFWorld | Success | - | 45% | **71%** | +26%p |
| WebShop | Score | - | 62.4% | **66.6%** | +4.2%p |

특히 ALFWorld에서 26%p의 향상은 추론이 행동 기반 에이전트의 효율을 크게 높일 수 있음을 보여준다.

CoT-SC(Self-Consistency) 샘플 수에 따른 성능 변화를 살펴보면, ReAct와 CoT-SC를 결합했을 때 각각 단독 사용 대비 더 높은 성능을 달성한다.

![HotpotQA에서 CoT-SC 샘플 수에 따른 성능 비교 그래프](figures/fig_3_1.png)
*Figure 2: HotpotQA에서 CoT-SC 샘플 수에 따른 PaLM-540B 프롬프팅 성능 - CoT-SC→ReAct 결합이 가장 높은 EM 점수를 달성한다. (Source: Yao et al., 2022)*

![Fever에서 CoT-SC 샘플 수에 따른 성능 비교 그래프](figures/fig_3_2.png)
*Figure 3: Fever에서 CoT-SC 샘플 수에 따른 PaLM-540B 프롬프팅 성능 - CoT-SC→ReAct 결합이 최고 정확도를 달성하며, ReAct→CoT-SC도 강력한 성능을 보인다. (Source: Yao et al., 2022)*

모델 스케일 측면에서도 ReAct의 우위가 확인된다. 아래 그래프는 모델 크기(8B→62B→540B)에 따른 프롬프팅과 파인튜닝 결과를 보여준다.

![HotpotQA에서 모델 크기별 프롬프팅 및 파인튜닝 성능 비교](figures/fig_5.png)
*Figure 4: HotpotQA 스케일링 실험 결과 - 프롬프팅(좌)과 파인튜닝(우) 모두에서 ReAct가 모델 크기 증가에 따라 일관된 성능 향상을 보인다. (Source: Yao et al., 2022)*

## 학습

ReAct는 few-shot CoT 예시와 동일한 방식으로 Thought-Action-Observation 트리플을 few-shot 예시로 제공한다. PaLM-540B, GPT-3 등을 기반으로 실험되었으며, 별도 파인튜닝 없이 프롬프트 엔지니어링만으로 구현 가능하다.

## 관련 모델

ReAct는 CoT에서 발전하여 외부 도구 사용을 추가한 프레임워크다. 이후 Reflexion(자기 반성), Toolformer(도구 내재화), LangGraph(그래프 기반 오케스트레이션), AutoGen(멀티 에이전트 대화), SWE-agent(소프트웨어 엔지니어링) 등 거의 모든 에이전트 기법에 직접적 영향을 미쳤다.

## 참고 자료

- Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models", ICLR 2023, arXiv:2210.03629
- [ReAct Project Page](https://react-lm.github.io)

## 관련 문서

- [[cot|Chain-of-Thought Prompting]] - 발전 기반
- [[langraph|LangGraph]] - 후속 모델
- [[reflexion|Reflexion]] - 후속 모델
- [[swe-agent|SWE-agent]] - 후속 모델
- [[autogen|AutoGen]] - 영감을 줌
- [[toolformer|Toolformer: Language Models Can Teach Themselves to Use Tools]] - 영감을 줌
