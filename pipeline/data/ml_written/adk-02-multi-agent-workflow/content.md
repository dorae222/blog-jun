<!-- infographic-hero -->
![ADK Multi-Agent Workflow: Sequential / Parallel / Loop / Custom 핵심 요약](figures/infographic.svg)

*Figure: ADK Multi-Agent Workflow: Sequential / Parallel / Loop / Custom 한 장 요약 인포그래픽*

# ADK 멀티에이전트 워크플로우: Sequential / Parallel / Loop / Custom

> 본 글은 **ADK 로컬 개발 시리즈(adk-local-development)** 2편입니다.
>
> - [[adk-01-local-setup|1편: ADK 로컬 환경 셋업]]
> - 2편(현재 글): 멀티에이전트 워크플로우
> - [[adk-03-litellm-ollama|3편: ADK + LiteLLM + Ollama]]
> - [[adk-04-evaluation-tracing|4편: ADK 평가 / 트레이싱 / 디버깅]]
>
> 1편에서 단일 `LlmAgent`를 실행했다면, 이번 편은 "여러 에이전트를 어떻게 조합할지"를 다룹니다.

## 개요

LLM 한 개에 도구를 붙인 자율 에이전트는 데모로는 훌륭하지만, 실제 업무에 투입하면 두 가지 문제가 빠르게 드러납니다.

1. **결과 비결정성**: 같은 입력에 대해 매번 다른 경로로 동작
2. **관찰 불능**: 한 번의 LLM call 안에서 무엇이 결정됐는지 추적 어려움

ADK는 이 문제를 "명시적 워크플로우 에이전트"로 해결합니다. SequentialAgent, ParallelAgent, LoopAgent는 **LLM 추론 없이** 사전에 정의된 순서대로 자식 에이전트를 호출합니다. 즉, 큰 그림(orchestration)은 결정적, 잎(leaf) 노드만 LLM이 담당하는 하이브리드 구조입니다.

여기에 BaseAgent를 직접 상속해서 만드는 Custom Agent를 더하면, if-else 분기, 외부 시스템 폴링, 인간 결재 같은 임의 로직을 자유롭게 끼워 넣을 수 있습니다.

| 패턴 | 호출 방식 | 종료 조건 | 대표 use case |
|------|-----------|-----------|---------------|
| SequentialAgent | 순차 | 모든 자식 완료 | 단계별 파이프라인(연구→작성→검수) |
| ParallelAgent | 동시 | 모든 자식 완료 | 다중 소스 fan-out(웹+DB+벡터DB) |
| LoopAgent | 반복 | max_iterations 또는 exit_loop | 반복 개선, 검증 루프 |
| Custom(BaseAgent) | 임의 | 직접 정의 | if-else, 외부 폴링, 결재 |

## session.state: 에이전트 간 데이터 전달의 단일 진실원

ADK는 메시지 히스토리와 별도로 **세션 상태(`session.state`)**라는 dict를 제공합니다. 이것이 멀티에이전트 통신의 사실상 유일한 채널입니다.

상태에 값을 쓰는 방법은 두 가지입니다.

1. **`output_key`** 지정: `LlmAgent`가 마지막 응답 텍스트를 자동으로 `state[output_key]`에 저장
2. **Tool 내부에서 `tool_context.state`** 직접 변경

상태 값을 다음 에이전트의 instruction에 끼워 넣을 때는 중괄호 placeholder를 씁니다.

```python
LlmAgent(
    name="writer",
    instruction="Write an article based on this research:\n{research_result}",
    ...
)
```

ADK 런타임이 호출 직전에 `state["research_result"]`를 자동 치환합니다. 이 단순한 메커니즘이 4가지 패턴 모두의 기반입니다.

## SequentialAgent: 순차 파이프라인

가장 자주 쓰는 패턴입니다. 자식 에이전트를 정의된 순서대로 한 번씩 호출하고, 각 결과를 `output_key`로 state에 누적합니다.

```python
from google.adk.agents import LlmAgent, SequentialAgent

researcher = LlmAgent(
    name="researcher",
    model="gemini-2.5-flash",
    description="Gathers facts about a topic.",
    instruction=(
        "Research the user's topic. "
        "Return 5 bullet points of verified facts."
    ),
    output_key="research_result",
)

writer = LlmAgent(
    name="writer",
    model="gemini-2.5-flash",
    description="Writes a blog post.",
    instruction=(
        "Write a 300-word blog post in Korean based on:\n"
        "{research_result}\n\n"
        "Tone: friendly, technical."
    ),
    output_key="draft",
)

reviewer = LlmAgent(
    name="reviewer",
    model="gemini-2.5-flash",
    description="Reviews and polishes the draft.",
    instruction=(
        "Improve the following draft for clarity and grammar.\n\n"
        "{draft}"
    ),
    output_key="final_post",
)

root_agent = SequentialAgent(
    name="blog_pipeline",
    sub_agents=[researcher, writer, reviewer],
)
```

이 파이프라인을 `adk web`으로 실행하면 디버깅 패널에서 다음 흐름을 볼 수 있습니다.

```text
Event 1: researcher → state.research_result = "..."
Event 2: writer     → state.draft = "..."
Event 3: reviewer   → state.final_post = "..."
```

세 에이전트가 모델, 프롬프트, output_key까지 전부 분리되어 있어서, "writer만 gpt-4o로 교체", "reviewer 프롬프트만 영어로 변경" 같은 부분 교체가 즉시 가능합니다.

## ParallelAgent: 동시 fan-out

여러 소스를 동시에 조회하고 결과를 모아 다음 단계로 넘기고 싶을 때 사용합니다. 자식 에이전트들은 같은 시작 시점에 동시 실행되며, 모두 완료될 때까지 기다립니다.

```python
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

web_searcher = LlmAgent(
    name="web_searcher",
    model="gemini-2.5-flash",
    instruction="Search the web for the topic and summarize.",
    tools=[web_search_tool],
    output_key="web_summary",
)

doc_searcher = LlmAgent(
    name="doc_searcher",
    model="gemini-2.5-flash",
    instruction="Query internal docs for the topic and summarize.",
    tools=[doc_search_tool],
    output_key="doc_summary",
)

vector_searcher = LlmAgent(
    name="vector_searcher",
    model="gemini-2.5-flash",
    instruction="Query the vector DB for similar past cases.",
    tools=[vector_search_tool],
    output_key="vector_summary",
)

gather = ParallelAgent(
    name="gather_evidence",
    sub_agents=[web_searcher, doc_searcher, vector_searcher],
)

synthesizer = LlmAgent(
    name="synthesizer",
    model="gemini-2.5-flash",
    instruction=(
        "Combine the following sources into one answer:\n\n"
        "[Web]\n{web_summary}\n\n"
        "[Docs]\n{doc_summary}\n\n"
        "[Past cases]\n{vector_summary}"
    ),
)

root_agent = SequentialAgent(
    name="rag_pipeline",
    sub_agents=[gather, synthesizer],
)
```

:::warning
**ParallelAgent의 함정 - state race condition.**
모든 자식이 같은 `session.state`를 공유합니다. 두 자식이 같은 키에 쓰면 마지막 쓴 쪽이 이깁니다. 반드시 자식마다 **고유한 `output_key`**를 사용하세요. 예: `web_summary`, `doc_summary`, `vector_summary`처럼 prefix를 분리.
:::

ParallelAgent는 보통 `SequentialAgent` 안에 끼워서 "fan-out → fan-in" 패턴으로 씁니다. 위 예시도 ParallelAgent로 3소스를 모은 뒤 synthesizer에서 fan-in합니다.

## LoopAgent: 반복과 종료 제어

검증을 통과할 때까지 반복하거나, 점수가 임계치를 넘을 때까지 다듬는 패턴입니다. 두 가지 종료 조건을 가집니다.

1. `max_iterations` 도달
2. 자식 에이전트의 도구가 `tool_context.actions.escalate = True`를 설정 (또는 `exit_loop` 도구 호출)

대표 사례: SQL Query Generator + Validator.

```python
from google.adk.agents import LlmAgent, LoopAgent
from google.adk.tools import ToolContext


def validate_sql(query: str, tool_context: ToolContext) -> dict:
    """Validate a SQL query against the schema and return errors if any."""
    errors = run_dry_run(query)  # 사용자 정의: SQLAlchemy explain 등
    if not errors:
        # 통과 → 루프 종료 신호
        tool_context.actions.escalate = True
        return {"status": "ok", "query": query}
    return {"status": "invalid", "errors": errors}


generator = LlmAgent(
    name="sql_generator",
    model="gemini-2.5-flash",
    instruction=(
        "Generate a SQL query for the user's request. "
        "If state contains 'last_errors', fix those errors. "
        "Last errors: {last_errors?}"
    ),
    output_key="candidate_sql",
)

validator = LlmAgent(
    name="sql_validator",
    model="gemini-2.5-flash",
    instruction=(
        "Validate the SQL: {candidate_sql}. "
        "Call validate_sql tool. If invalid, write the errors to state."
    ),
    tools=[validate_sql],
    output_key="last_errors",
)

sql_loop = LoopAgent(
    name="sql_refiner",
    max_iterations=5,
    sub_agents=[generator, validator],
)
```

이 루프는 다음과 같이 동작합니다.

1. generator가 첫 시도 → `candidate_sql`에 저장
2. validator가 dry-run → 실패하면 `last_errors`에 저장, `escalate = False`
3. 루프 다시 generator로 → 이번엔 instruction 안의 `{last_errors?}`를 보고 수정
4. validator가 통과 → `escalate = True` → 루프 종료

`{last_errors?}`의 `?`는 "값이 없으면 빈 문자열로 치환"이라는 ADK의 optional placeholder 문법입니다. 첫 iteration에서 키가 없는 상태를 안전하게 처리합니다.

## Custom Agent: BaseAgent 상속으로 if-else 분기

Sequential / Parallel / Loop로 표현되지 않는 로직 - 예를 들어 "신뢰 점수가 낮으면 사람에게 결재 요청, 높으면 바로 실행" - 을 구현하려면 BaseAgent를 직접 상속합니다.

```python
from typing import AsyncGenerator
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event


class ConditionalRouter(BaseAgent):
    """Route to fast_agent or careful_agent based on confidence score."""

    fast_agent: LlmAgent
    careful_agent: LlmAgent

    def __init__(self, name: str, fast_agent: LlmAgent, careful_agent: LlmAgent):
        super().__init__(
            name=name,
            sub_agents=[fast_agent, careful_agent],
        )
        self.fast_agent = fast_agent
        self.careful_agent = careful_agent

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        score = ctx.session.state.get("confidence", 0.0)
        chosen = self.fast_agent if score >= 0.8 else self.careful_agent
        async for event in chosen.run_async(ctx):
            yield event


fast = LlmAgent(name="fast", model="gemini-2.5-flash", instruction="Answer briefly.")
careful = LlmAgent(
    name="careful",
    model="gemini-2.5-pro",
    instruction="Reason step by step before answering.",
)

router = ConditionalRouter(
    name="router",
    fast_agent=fast,
    careful_agent=careful,
)
```

`_run_async_impl`은 `Event`를 yield하는 async generator입니다. 외부 시스템 폴링, 휴먼 인 더 루프, A/B 테스트 같은 분기를 모두 이 안에서 처리할 수 있습니다.

## 패턴 결합 예시: 연구 → (병렬 검증) → 루프 개선

실전에서는 위 4가지를 자유롭게 중첩합니다.

```python
research_phase = SequentialAgent(
    name="research",
    sub_agents=[outline_agent, draft_agent],
)

verify_phase = ParallelAgent(
    name="verify",
    sub_agents=[fact_checker, style_checker, plagiarism_checker],
)

refine_loop = LoopAgent(
    name="refine",
    max_iterations=3,
    sub_agents=[reviewer, rewriter],
)

root_agent = SequentialAgent(
    name="full_pipeline",
    sub_agents=[research_phase, verify_phase, refine_loop],
)
```

이 구조는 LangGraph의 그래프 정의와 비슷한 표현력을 가지면서도, 노드/엣지 그래프 대신 **트리** 구조라서 디버그가 직관적입니다. `adk web`의 trace 패널에서 트리 자체가 그대로 보입니다.

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| placeholder가 그대로 출력됨 | state 키 누락 | `output_key` 또는 tool에서 state 쓰기 확인 |
| Parallel 결과 한 개만 보임 | 같은 output_key 충돌 | 자식마다 고유 키 사용 |
| Loop가 종료되지 않음 | escalate 미설정 | tool에서 `tool_context.actions.escalate = True` |
| Custom agent가 호출되지 않음 | sub_agents에 미등록 | `super().__init__(sub_agents=[...])` 누락 확인 |
| Sequential 도중 중단 | 자식이 예외 발생 | trace 패널의 빨간 이벤트 확인, try/except로 감싸기 |

## 정리 + 다음 편

이번 편에서 다룬 핵심:

- **결정적 orchestration + LLM leaf** 하이브리드가 ADK의 철학
- session.state + `output_key` + `{placeholder}`가 데이터 통신의 전부
- SequentialAgent(파이프라인) / ParallelAgent(fan-out) / LoopAgent(반복) / Custom(분기)
- 패턴은 자유롭게 중첩 가능

여기까지는 모델로 Gemini를 사용했습니다. 회사 내부 데이터를 다루거나 공중망 접속이 불가능한 환경에서는 로컬 LLM이 필요합니다. 다음 [[adk-03-litellm-ollama|3편]]에서는 LiteLLM 어댑터를 통해 Ollama, vLLM, TGI 같은 로컬 백엔드를 ADK에 연결하고 air-gapped 환경에서 운영하는 방법을 다룹니다.

## 관련 문서

- [[adk-01-local-setup|ADK 로컬 환경 셋업]] - 이전 편, 단일 에이전트와 실행 모드
- [[adk-03-litellm-ollama|ADK + LiteLLM + Ollama]] - 다음 편, 로컬 LLM 통합
- [[adk-04-evaluation-tracing|ADK 평가 / 트레이싱 / 디버깅]] - 워크플로우의 성능 측정
- [[a2a-05-adk-integration|A2A + ADK 통합 패턴과 보안]] - 워크플로우를 외부에 노출하는 방법
