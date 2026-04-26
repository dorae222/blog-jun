<!-- infographic-hero -->
![Reflexion 핵심 요약](figures/infographic.svg)

*Figure: Reflexion 한 장 요약 인포그래픽*

# Reflexion: 언어적 자기 반성을 통한 에이전트 강화 학습

**Northeastern/MIT** · **2023-03-20** · **Agent Technique** · **오픈**

## 개요

Reflexion은 언어 에이전트가 과거 시행착오를 언어적 반성(verbal reflection)으로 전환해 컨텍스트에 저장하고, 다음 시도에서 이를 활용해 자기 개선하는 프레임워크다. Shinn et al.(Northeastern University/MIT, 2023)이 논문 "Reflexion: Language Agents with Verbal Reinforcement Learning"에서 발표한 이 기법은, 기울기 기반 학습(gradient update) 없이도 에이전트가 실패로부터 학습하는 메커니즘을 제공한다.

Reflexion의 핵심 통찰은 **"인간은 실패에서 배우며, 언어가 그 학습의 매개"**라는 것이다. 인간은 실패 후 "왜 실패했는가", "다음에는 어떻게 해야 하는가"를 언어로 반성하고, 그 교훈을 기억하여 다음 시도에 적용한다. Reflexion은 이 자연스러운 자기 개선 과정을 LLM으로 자동화한다. 전통적 강화 학습이 스칼라 보상 신호 $r \in \mathbb{R}$를 사용하는 반면, Reflexion은 자연어 반성 텍스트를 피드백으로 활용하여 **"언어적 강화 학습(Verbal Reinforcement Learning)"**이라는 새로운 패러다임을 제시한다.

ReAct는 Thought-Action-Observation의 단일 시도에서 최선의 답을 구하지만, 복잡한 문제에서는 한 번의 시도로 최적의 답을 찾지 못하는 경우가 빈번하다. Reflexion은 이 한계를 극복하여, 실패한 시도의 궤적(trajectory)과 평가 결과를 분석하고, 구체적인 개선 방향을 자연어로 생성하여 다음 시도의 컨텍스트에 주입한다. 이를 통해 동일한 기반 모델 위에서 별도의 가중치 업데이트 없이도 **반복 시도를 통한 지속적 성능 향상**을 실현한다. HotpotQA에서 17.6%p, HumanEval(코드 생성)에서 24.0%p의 향상은 이 접근법의 효과를 실증한다.

![Reflexion 아키텍처 - Actor, Evaluator, Self-Reflection과 언어적 메모리 기반 자기 개선 에이전트 구조](figures/architecture.svg)

*Figure 1: Reflexion 아키텍처 - Actor가 환경과 상호작용하고 Evaluator가 피드백을 생성하며, Self-Reflection이 실패 원인을 언어로 분석하여 장기 메모리에 저장하고 다음 시도에 활용하는 언어적 강화 학습 프레임워크이다.*

![Reflexion 개요 - 의사결정, 프로그래밍, 추론 태스크에서의 적용](figures/fig_1.png)
*Figure 1: Reflexion 작동 과정 - (a) 태스크 수행, (b) 궤적 기록, (c) 평가, (d) 자기 반성, (e) 개선된 다음 시도. 의사결정, 코드 생성, 추론 세 도메인에서 동일 프레임워크 적용. (Source: arXiv 2303.11366)*

## 아키텍처 상세

Reflexion의 아키텍처는 세 개의 핵심 컴포넌트와 하나의 메모리 시스템으로 구성된다.

![Reflexion 에이전트 아키텍처 - Actor, Evaluator, Self-Reflection, 메모리 구조](figures/fig_2.png)
*Figure 2: Reflexion 에이전트 구조 - Actor가 환경과 상호작용하고, Evaluator가 내부/외부 피드백을 생성하며, Self-Reflection이 반성 텍스트를 장기 메모리에 저장하여 다음 시도에 활용. (Source: arXiv 2303.11366)*

### Actor-Evaluator-Self-Reflection 삼중 구조

**Actor (행위자)**: ReAct 루프를 실행하여 환경과 상호작용하는 에이전트다. Thought $\rightarrow$ Action $\rightarrow$ Observation 사이클을 반복하며 태스크를 수행한다. 에피소드 메모리에 저장된 이전 반성 텍스트를 컨텍스트에 포함하여, 과거 실패의 교훈을 참조하면서 행동한다.

**Evaluator (평가자)**: Actor의 시도 결과를 평가하여 성공/실패 신호를 생성한다. 태스크에 따라 다양한 평가 기준을 사용한다.

| 태스크 도메인 | 평가 방식 | 피드백 형태 |
|-------------|----------|----------|
| 질의응답 (HotpotQA) | 정확 매칭 (Exact Match) | 정답/오답 |
| 코드 생성 (HumanEval) | 단위 테스트 실행 | 통과/실패 + 에러 메시지 |
| 시퀀셜 의사결정 (ALFWorld) | 환경 보상 함수 | 성공/실패 |
| 사실 검증 (Fever) | 레이블 매칭 | 정답/오답 |

**Self-Reflection (자기 반성)**: 실패한 경우 LLM이 실패 궤적과 평가 결과를 분석하여, 구체적인 실패 원인과 개선 전략을 자연어로 생성하는 핵심 모듈이다. 이 모듈이 생성하는 반성 텍스트는 단순한 "실패했다"가 아니라, "왜 실패했으며 구체적으로 무엇을 변경해야 하는가"를 상세히 기술한다.

### 수학적 정의

Reflexion의 프로세스를 형식적으로 정의하면:

$$\tau_t = \text{Actor}(\text{task}, \text{mem}_t) \quad \text{(시도 실행)}$$
$$e_t = \text{Evaluator}(\tau_t) \quad \text{(결과 평가)}$$
$$r_t = \text{Reflect}(\tau_t, e_t) \quad \text{(반성 생성)}$$
$$\text{mem}_{t+1} = \text{mem}_t \cup \{r_t\} \quad \text{(메모리 업데이트)}$$

여기서 $\tau_t$는 $t$번째 시도의 궤적(trajectory), $e_t$는 평가 결과, $r_t$는 반성 텍스트, $\text{mem}_t$는 에피소드 메모리다. 이 루프를 성공할 때까지 또는 최대 시도 횟수 $K$에 도달할 때까지 반복한다.

전통적 RL과의 핵심 차이를 비교하면:

$$\text{기존 RL: } \theta_{t+1} = \theta_t + \alpha \nabla_\theta J(\theta) \quad \text{(가중치 업데이트)}$$
$$\text{Reflexion: } \text{mem}_{t+1} = \text{mem}_t \cup \{r_t\} \quad \text{(컨텍스트 업데이트)}$$

기존 RL은 모델 가중치 $\theta$를 업데이트하지만, Reflexion은 가중치는 고정한 채 컨텍스트(메모리)만 업데이트한다. 이를 통해 파인튜닝 없이도 행동 개선이 가능하다.

### 에피소드 메모리(Episodic Memory)

반성 텍스트를 저장하는 메모리 시스템이다. 컨텍스트 길이 제한을 관리하기 위해 슬라이딩 윈도우 방식으로 최근 $K$개의 반성만 유지한다.

```
시도 #1:
  Actor: ReAct 루프 실행 → 답변 생성
  Evaluator: 오답 판정
  Self-Reflection: "검색 결과를 충분히 확인하지 않고
    첫 번째 결과만으로 판단했다. 다음에는 여러 소스를
    교차 검증해야 한다."
  → mem = [반성 #1]

시도 #2 (반성 텍스트가 컨텍스트에 추가됨):
  Actor: ReAct 루프 실행 (이전 반성을 참고하여 더 신중하게 검색)
  Evaluator: 오답 판정
  Self-Reflection: "교차 검증은 했으나, 질문의 핵심 키워드
    '최초'를 놓쳤다. 다음에는 질문을 더 신중히 분석해야 한다."
  → mem = [반성 #1, 반성 #2]

시도 #3 (두 개의 반성이 컨텍스트에 포함):
  Actor: 질문을 면밀히 분석 → 핵심 키워드 포착 → 교차 검증
  Evaluator: 정답 판정 ✓
```

### 코드 생성 특화: 테스트 기반 반성

코드 생성에서 Reflexion은 특히 강력한 성능을 보인다. 테스트 실패 메시지가 구체적인 피드백을 제공하므로, 반성의 품질이 자연스럽게 높아진다.

```python
# 시도 #1: 생성된 코드
def is_palindrome(s: str) -> bool:
    return s == s[::-1]

# 테스트 실패: assert is_palindrome("Race Car") == True  # False 반환

# Self-Reflection: "대소문자를 구분하지 않고 공백을 무시해야 한다.
#   다음 시도에서 입력을 정규화하는 전처리를 추가해야 한다."

# 시도 #2: 반성을 반영한 수정 코드
def is_palindrome(s: str) -> bool:
    cleaned = ''.join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]

# 테스트 통과 ✓
```

## 핵심 혁신

1. **언어적 강화 학습(Verbal RL)**: 전통적 RL의 스칼라 보상 $r \in \mathbb{R}$ 대신 자연어 반성을 피드백으로 사용한다. 스칼라 보상이 "얼마나 잘했는가"만 알려주는 반면, 언어적 반성은 "왜 실패했고 어떻게 고쳐야 하는가"까지 전달하여 정보량이 크게 풍부하다.

2. **무기울기 자기 개선(Gradient-Free Self-Improvement)**: 모델 가중치를 업데이트하지 않고 컨텍스트만 변경하여 행동을 개선한다. 이는 대형 모델의 파인튜닝 비용을 피하면서도 태스크별 적응이 가능하게 한다.

3. **에피소드 메모리**: 과거 시행착오의 교훈을 자연어로 요약하여 저장하고, 이후 시도에서 참조하는 구조. 이는 인간의 경험적 학습(experiential learning)을 모방한 것이다.

4. **범용적 적용**: 질의응답, 코드 생성, 시퀀셜 의사결정, 사실 검증 등 다양한 태스크에 동일한 프레임워크가 적용 가능하며, Evaluator만 교체하면 된다.

## 벤치마크/성능

| 벤치마크 | 태스크 유형 | ReAct (1시도) | Reflexion (최대 5시도) | 향상 |
|---------|-----------|-------------|---------------------|------|
| HotpotQA | 질의응답 | 34.2% | **51.8%** | +17.6%p |
| ALFWorld | 의사결정 | 71% | **90%** | +19.0%p |
| HumanEval | 코드 생성 | 67.0% | **91.0%** | +24.0%p |
| Fever | 사실 검증 | 64.6% | **77.3%** | +12.7%p |

![ALFWorld에서의 반복 시도에 따른 성공률 향상](figures/fig_4.png)
*Figure 3: ALFWorld 성공률 - ReAct + Reflexion(파란색)이 시도 횟수 증가에 따라 ReAct 단독(회색) 대비 약 20%p 이상 성공률 향상. 반복 반성의 누적 효과를 시각적으로 확인. (Source: arXiv 2303.11366)*

![HotpotQA에서의 Reflexion 성능 향상](figures/fig_6_1.png)
*Figure 4: HotpotQA 성공률 - ReAct + Reflexion(파란색)이 6회 시도 시 55%로, ReAct 단독(회색, 34%) 대비 21%p 향상. CoT + Reflexion(빨간색)도 일관된 향상을 보임. (Source: arXiv 2303.11366)*

특히 HumanEval에서 91%의 성공률은 Reflexion의 자기 수정 루프가 코드 생성에서 매우 효과적임을 보여준다. 테스트 실패 메시지가 명확한 오류 정보를 제공하므로, Self-Reflection 모듈이 구체적이고 실행 가능한 개선 방향을 생성할 수 있기 때문이다. ALFWorld에서의 19%p 향상은 시퀀셜 의사결정에서도 반복 시도와 반성이 효과적임을 입증한다.

## 학습

Reflexion은 파인튜닝 없이 GPT-3.5, GPT-4, Claude 등 강력한 기반 모델 위에서 프롬프팅으로 구현된다. Actor는 ReAct 프롬프트를, Self-Reflection 모듈은 반성 생성 전용 프롬프트를 사용한다. 주요 하이퍼파라미터는 최대 반성 횟수(보통 3~5회)와 메모리 저장 방식(슬라이딩 윈도우, 일반적으로 최근 3개)이다. 반성 횟수가 증가할수록 성능이 향상되지만, 3~5회를 넘으면 수확 체감(diminishing returns)이 관찰된다. 컨텍스트 길이 제한으로 인해 무한한 반성 누적은 불가능하며, 이는 Reflexion의 구조적 한계다.

## 관련 모델

Reflexion은 ReAct의 단일 시도 한계를 자기 반성 메커니즘으로 극복한 프레임워크다. CoT의 내부 추론, ReAct의 외부 행동에 이어 "자기 반성과 반복 학습"이라는 세 번째 축을 추가했다. 이후 코드 에이전트(OpenHands, SWE-agent)의 자동 디버깅 루프, LangGraph의 조건부 반복 패턴, Claude Code의 자기 수정 메커니즘 등에 직접적 영향을 미쳤다.

## 참고 자료

- Shinn et al., "Reflexion: Language Agents with Verbal Reinforcement Learning", NeurIPS 2023, arXiv:2303.11366
- [Reflexion GitHub Repository](https://github.com/noahshinn/reflexion)

## 관련 문서

- [[react|ReAct]] - 발전 기반
