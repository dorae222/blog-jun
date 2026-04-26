<!-- infographic-hero -->
![OpenAI Agents SDK 핵심 요약](figures/infographic.svg)

*Figure: OpenAI Agents SDK 한 장 요약 인포그래픽*

# OpenAI Agents SDK: 핸드오프와 가드레일을 일급 개념으로 만든 OpenAI 네이티브 에이전트 프레임워크

**OpenAI** · **2025-03-11** · **Agent Framework** · **MIT**

## 개요

OpenAI Agents SDK는 OpenAI가 2025년 3월 11일 공개한 경량 멀티 에이전트 프레임워크다. 이전까지 OpenAI는 두 갈래의 추상화를 제공해왔다. 하나는 서버 측에서 스레드(thread)와 런(run)을 관리하는 Assistants API였고, 다른 하나는 2024년 10월 실험용으로 공개된 클라이언트 라이브러리 Swarm이었다. Assistants API는 추상화 수준이 너무 높아 디버깅이 어려웠고, Swarm은 단순했지만 프로덕션 사용을 권장하지 않는 교육용 프로젝트였다. Agents SDK는 이 두 갈래의 장단점을 종합하여 명시적이면서도 프로덕션 수준의 안정성을 갖춘 클라이언트 측 라이브러리로 재설계되었다.

설계 철학은 최소 추상화(minimal abstraction)다. 에이전트, 도구, 핸드오프, 가드레일이라는 네 개의 일급 개념(first-class primitive)만 노출하고, 나머지 동작은 모두 코드로 명시되도록 만들었다. 이는 LangChain이나 LangGraph가 수십 개의 데코레이터와 클래스를 도입하는 것과 정반대 방향이다. OpenAI는 개발자들이 "마법(magic)이 적은" 라이브러리를 선호한다는 피드백을 반영해, SDK 전체를 5천 줄 미만의 Python 코드로 구현하고 모든 내부 동작을 추적 가능하게 했다.

핵심 차별점은 세 가지다. 첫째, 핸드오프(handoff)를 함수 호출처럼 명시적인 제어 전환으로 정의해 멀티 에이전트 시나리오의 비용과 지연을 줄였다. 둘째, 가드레일이 입력과 출력 양쪽에서 비동기로 실행되어 메인 추론을 차단하지 않는다. 셋째, 트레이싱이 SDK에 빌트인되어 별도 LangSmith 같은 외부 도구 없이도 OpenAI 대시보드에서 모든 에이전트 실행을 시각화할 수 있다.

## 아키텍처

Agents SDK의 실행 모델은 단순하다. Runner가 Agent를 호출하면, Agent는 LLM에 요청을 보내고 응답에서 도구 호출 또는 핸드오프 의도를 파싱한다. 도구 호출이면 도구를 실행하고 결과를 다시 LLM에 전달하며, 핸드오프면 새로운 Agent로 제어를 넘긴다. 출력 스키마(Pydantic 모델)가 정의되어 있다면 마지막 응답을 파싱하여 구조화된 객체로 반환한다.

이 루프는 LangGraph의 StateGraph와 비슷하지만 노드와 엣지를 명시적으로 정의할 필요가 없다. 핸드오프와 도구 호출이 자연스럽게 그래프의 엣지 역할을 하기 때문에, 개발자는 Agent들과 그들의 도구 목록만 선언하면 된다. 대신 LangGraph의 명시적 분기와 사이클 제어 같은 정밀한 제어는 어렵다. OpenAI는 이를 의도적인 트레이드오프로 두었으며, 정밀 제어가 필요한 워크플로는 직접 코드로 구성하라고 권장한다.

## 핵심 컴포넌트

### Agent

Agent는 모델, 지시문(instructions), 도구 목록, 출력 타입, 핸드오프 가능 에이전트 목록을 묶은 단위다.

```python
from agents import Agent

triage_agent = Agent(
    name="Triage",
    instructions="사용자의 질문을 분류하고 적절한 전문가에게 위임한다.",
    handoffs=[support_agent, billing_agent],
)
```

### Tool

도구는 Python 함수에 `@function_tool` 데코레이터를 붙이면 자동으로 OpenAI function calling 스키마로 변환된다. Pydantic 타입 힌트가 그대로 JSON Schema로 변환되며, docstring이 도구 설명으로 사용된다.

```python
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """도시의 현재 날씨를 조회한다."""
    return fetch_weather_api(city)
```

### Handoff

핸드오프는 한 에이전트가 다른 에이전트에 작업을 넘기는 메커니즘이다. 내부적으로 도구 호출 형태로 구현되지만, OpenAI는 이를 별도 추상화로 분리해 LLM이 위임 의도를 명시적으로 표현하도록 만들었다. 핸드오프 시 컨텍스트는 자동으로 전달되며, 필요하면 입력 필터(input filter)를 사용해 메시지 일부를 제거하거나 변환할 수 있다.

### Guardrail

가드레일은 입력 가드레일과 출력 가드레일로 나뉜다. 입력 가드레일은 사용자 입력이 정책에 부합하는지 검증하고, 위반 시 에이전트 실행을 즉시 중단한다. 출력 가드레일은 최종 응답이 안전한지 검증한다. 두 가드레일 모두 비동기로 실행되어 메인 추론과 병렬화된다.

```python
from agents import Agent, GuardrailFunctionOutput, input_guardrail
from pydantic import BaseModel

class SafetyCheck(BaseModel):
    is_unsafe: bool
    reason: str

@input_guardrail
async def safety_guardrail(ctx, agent, input_text):
    result = await safety_classifier.run(input_text)
    return GuardrailFunctionOutput(
        output_info=result,
        tripwire_triggered=result.is_unsafe,
    )
```

### Tracing

모든 에이전트 실행, LLM 호출, 도구 호출, 핸드오프, 가드레일 평가가 자동으로 트레이스에 기록된다. 트레이스는 OpenAI 대시보드(platform.openai.com/traces)에서 시각화되며, 외부 백엔드(Logfire, AgentOps, Braintrust 등)로 익스포트할 수도 있다.

## 코드 예제

다음은 트리아지 에이전트가 사용자의 문의를 분류하고 전문 에이전트로 위임하는 전형적인 패턴이다.

```python
from agents import Agent, Runner, function_tool
from pydantic import BaseModel

class RefundResult(BaseModel):
    approved: bool
    amount: float
    reason: str

@function_tool
def lookup_order(order_id: str) -> dict:
    """주문 정보를 조회한다."""
    return {"order_id": order_id, "total": 89.0, "status": "delivered"}

billing_agent = Agent(
    name="Billing",
    instructions="환불 요청을 검토하고 정책에 따라 승인 또는 거절한다.",
    tools=[lookup_order],
    output_type=RefundResult,
)

support_agent = Agent(
    name="Support",
    instructions="기술 지원 질문에 답변한다.",
)

triage_agent = Agent(
    name="Triage",
    instructions="사용자 메시지를 보고 결제 문의는 Billing, 기술 문의는 Support로 위임한다.",
    handoffs=[billing_agent, support_agent],
)

result = Runner.run_sync(
    triage_agent,
    input="주문 12345 환불해주세요. 배송된 상품이 망가져 있어요.",
)
print(result.final_output)
```

음성 에이전트는 동일한 Agent 정의를 그대로 재사용하면서 Realtime API와 결합한다.

```python
from agents.voice import VoicePipeline, SingleAgentVoiceWorkflow

pipeline = VoicePipeline(
    workflow=SingleAgentVoiceWorkflow(triage_agent),
)
result = await pipeline.run(audio_input)
```

## 사용 사례

### 고객 지원 자동화

OpenAI 자체가 dotcom 고객 지원 봇에 Agents SDK를 사용하고 있다. 트리아지 에이전트가 문의를 분류하고 결제, 기술, 계정 등 전문 에이전트로 위임하며, 가드레일이 결제 환불 한도와 같은 정책을 강제한다.

### 음성 어시스턴트

Realtime API와 결합한 음성 에이전트가 콜센터 자동화, 차량 음성 어시스턴트, 헬스케어 트리아지 등에 적용된다. 동일한 Agent 정의가 텍스트 채팅과 음성 통화 양쪽에서 재사용된다.

### 리서치 자동화

Deep Research 워크플로에서 검색 에이전트, 요약 에이전트, 검증 에이전트가 핸드오프로 협업하여 장문 리포트를 생성한다.

## 비교

| 항목 | OpenAI Agents SDK | LangGraph | CrewAI | AutoGen |
|------|-------------------|-----------|--------|---------|
| 핵심 추상화 | Agent, Handoff, Guardrail | StateGraph, Node, Edge | Crew, Agent, Task | ConversableAgent, GroupChat |
| 제어 흐름 | 핸드오프 기반 | 명시적 그래프 | 순차/계층 프로세스 | 대화 기반 |
| 트레이싱 | 빌트인 (OpenAI 대시보드) | LangSmith 통합 | 제한적 | 로깅 |
| 음성 지원 | 네이티브 (Realtime API) | 미지원 | 미지원 | 미지원 |
| 비OpenAI 모델 | LiteLLM 어댑터 | 네이티브 | 네이티브 | 네이티브 |
| 학습 곡선 | 낮음 | 높음 | 낮음 | 중간 |
| 코드 라인 | 약 5천 줄 | 약 5만 줄 | 약 2만 줄 | 약 3만 줄 |

OpenAI Agents SDK는 가장 경량이며 OpenAI 모델과의 통합이 가장 매끄럽다. 반면 명시적 사이클 제어나 체크포인팅 같은 고급 기능이 필요하면 LangGraph가 더 적합하다.

## 한계

첫째, OpenAI 생태계 우선 설계다. LiteLLM으로 다른 모델을 호출할 수 있지만 structured output, function calling, Realtime API의 모든 기능이 OpenAI 모델에서 가장 잘 동작한다. 둘째, LangGraph 같은 명시적 그래프 제어가 어렵다. 복잡한 분기와 루프가 필요한 워크플로는 직접 코드로 구성해야 한다. 셋째, 체크포인팅과 영속성이 빌트인되지 않았다. 장시간 작업이나 인간 개입이 필요한 워크플로는 외부 저장소를 사용자가 직접 통합해야 한다. 넷째, 멀티 에이전트 협상(negotiation)이나 토론(debate) 같은 대화 중심 시나리오는 AutoGen이 더 적합하다.

## 관련 문서

- [[langgraph-deep-dive|LangGraph 심층 분석]] - 그래프 기반 에이전트 오케스트레이션 비교
- [[autogen-deep-dive|AutoGen 심층 분석]] - 대화 기반 멀티 에이전트 프레임워크 비교
- [[mcp|Model Context Protocol]] - 도구 통합 표준 프로토콜
- [[a2a|Agent-to-Agent Protocol]] - 에이전트 간 통신 표준
