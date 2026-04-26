<!-- infographic-hero -->
![LangGraph Deep Dive 핵심 요약](figures/infographic.svg)

*Figure: LangGraph Deep Dive 한 장 요약 인포그래픽*

# LangGraph 심층 분석: 그래프 기반 에이전트 오케스트레이션

## 개요

LangGraph는 LangChain이 2024년 1월 공개한 LLM 에이전트 오케스트레이션 라이브러리로, 월 3,450만 다운로드를 기록하며 엔터프라이즈 에이전트 프레임워크 카테고리에서 사실상 1위 자리를 차지하고 있다. LinkedIn, Klarna, Replit, Uber, Elastic 같은 회사들이 프로덕션 에이전트의 기반 라이브러리로 채택했고, LangChain v0.3 이후로는 LangChain 자체의 표준 에이전트 구현체도 모두 LangGraph 위에서 동작한다.

LangGraph가 다른 에이전트 프레임워크와 차별화되는 지점은 추상화 수준이다. CrewAI, AutoGen, OpenAI Agents SDK가 high-level 추상화(역할, 대화, 핸드오프)를 제공한다면 LangGraph는 그래프, 노드, 엣지, 상태라는 low-level primitive를 노출한다. 이 low-level 접근은 학습 곡선이 가파르지만 프로덕션에 필요한 정밀한 제어, 영속성, 디버깅 가능성을 보장한다. LangGraph가 "에이전트의 PyTorch"라고 불리는 이유다.

핵심 통찰은 "에이전트 워크플로는 본질적으로 상태 그래프"라는 것이다. 에이전트가 도구를 호출하고, 결과를 평가하고, 필요시 재시도하고, 사용자 승인을 기다리고, 다른 에이전트에 위임하는 모든 흐름은 노드(처리 로직)와 엣지(전이 조건)로 이루어진 그래프로 자연스럽게 표현된다. 이 추상화를 통해 조건부 분기, 사이클, 인터럽트, 체크포인팅 같은 복잡한 제어 흐름이 단일 일관된 모델로 표현된다.

## 아키텍처

LangGraph의 핵심 아키텍처는 세 계층으로 구성된다. 최하단의 Pregel 실행 엔진은 그래프의 동시성과 상태 동기화를 담당하고, 그 위의 StateGraph API는 사용자가 그래프를 정의하는 인터페이스를 제공하며, 최상단의 Prebuilt 모듈은 ReAct 에이전트, ToolNode 같은 자주 쓰이는 패턴을 미리 구현해 둔 헬퍼다. 또한 Checkpointer 인터페이스가 모든 계층을 가로질러 상태 영속성을 제공한다.

Pregel 엔진은 Google의 Pregel 논문(2010)에서 영감을 받은 메시지 패싱 모델을 사용한다. 각 super-step에서 활성 노드들이 병렬로 실행되고, 노드들이 반환하는 상태 업데이트가 리듀서를 통해 글로벌 상태에 병합되며, 다음 super-step에서 활성화될 노드가 결정된다. 이 모델 덕분에 ParallelAgent 같은 별도 추상화 없이도 동시 실행이 자연스럽게 표현된다.

상태(State)는 TypedDict 또는 Pydantic 모델로 정의되며 Annotated 타입 힌트로 각 필드의 리듀서 전략을 지정한다. `Annotated[list, add]`는 리스트에 새 값을 append하는 리듀서이고, `Annotated[str, lambda old, new: new]`는 덮어쓰기 리듀서다. 이 선언적 리듀서 패턴은 Redux와 Elm Architecture에서 영감을 받았으며, 멀티 노드 동시 업데이트 시 일관성을 보장하는 핵심 메커니즘이다.

## 핵심 컴포넌트

### StateGraph

```python
from typing import TypedDict, Annotated, Sequence
from operator import add
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add]
    next_step: str
    iteration: int

graph = StateGraph(AgentState)
```

상태 스키마는 그래프 전체에서 공유되는 데이터의 형태를 정의한다. 모든 노드는 이 타입의 부분 업데이트를 반환한다.

### Node와 Edge

노드는 상태를 입력받아 부분 업데이트를 반환하는 함수다.

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")

def planner(state: AgentState) -> dict:
    response = llm.invoke([
        {"role": "system", "content": "다음 단계를 결정한다."},
        *state["messages"],
    ])
    return {
        "messages": [response],
        "next_step": parse_next(response.content),
        "iteration": state["iteration"] + 1,
    }

def executor(state: AgentState) -> dict:
    result = run_tool(state["next_step"])
    return {"messages": [result]}

graph.add_node("planner", planner)
graph.add_node("executor", executor)
graph.add_edge(START, "planner")
graph.add_edge("executor", "planner")
```

### 조건부 라우팅

```python
def route_after_planner(state: AgentState) -> str:
    if state["next_step"] == "FINISH":
        return "end"
    if state["iteration"] >= 10:
        return "end"
    return "execute"

graph.add_conditional_edges(
    "planner",
    route_after_planner,
    {"execute": "executor", "end": END},
)

app = graph.compile()
```

조건부 엣지는 현재 상태를 평가하는 라우팅 함수와 결과 매핑으로 구성된다. 이 패턴이 ReAct의 추론-행동 루프와 종료 조건을 자연스럽게 표현한다.

### 체크포인트와 영속성

```python
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string("postgresql://...") as checkpointer:
    checkpointer.setup()
    app = graph.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": "user-123-session-456"}}
    result = app.invoke(
        {"messages": [{"role": "user", "content": "리포트 작성해줘"}]},
        config=config,
    )
```

체크포인트는 각 super-step 전후에 상태 스냅샷을 저장한다. 이로 인해 서버 재시작, 중단된 작업 재개, 멀티 워커 분산 처리가 모두 가능하다. 프로덕션에서는 PostgresSaver 또는 사용자 정의 Saver(Redis, DynamoDB 등)를 사용한다.

### Time-Travel

체크포인트가 있으면 임의의 과거 상태로 되돌아가서 다른 경로를 탐색할 수 있다.

```python
history = list(app.get_state_history(config))
# 5번째 step의 상태로 되돌아가서 다른 입력으로 분기
checkpoint_id = history[5].config["configurable"]["checkpoint_id"]
fork_config = {
    "configurable": {
        "thread_id": "user-123-session-456",
        "checkpoint_id": checkpoint_id,
    }
}
new_result = app.invoke(
    {"messages": [{"role": "user", "content": "다른 방향으로 가보자"}]},
    config=fork_config,
)
```

Time-travel은 디버깅뿐 아니라 A/B 테스트, 시뮬레이션, 인간 개입 후 분기 같은 시나리오에 활용된다.

### Subgraph

복잡한 멀티 에이전트는 서브그래프로 계층화한다. 각 서브그래프는 독립적인 상태 스키마를 가질 수 있고 부모 그래프와 매핑 함수로 연결된다.

```python
class SecuritySubState(TypedDict):
    code: str
    vulnerabilities: list[dict]

security_graph = StateGraph(SecuritySubState)
# ... 보안 분석 노드들 ...
security_app = security_graph.compile()

class ReviewState(TypedDict):
    code: str
    security_report: dict
    perf_report: dict

review_graph = StateGraph(ReviewState)
review_graph.add_node("security", security_app)
review_graph.add_node("perf", perf_app)
```

## 고급 기능

### Human-in-the-Loop (HITL)

LangGraph가 가장 차별화되는 기능은 인간 개입을 그래프에 일급 개념으로 통합한 점이다. interrupt 함수를 호출하면 그래프 실행이 일시 중단되고 외부에서 입력을 주입할 때까지 대기한다.

```python
from langgraph.types import interrupt, Command

def approval_node(state: AgentState) -> dict:
    decision = interrupt({
        "question": "이 환불을 승인하시겠습니까?",
        "amount": state["refund_amount"],
        "reason": state["refund_reason"],
    })
    return {"approved": decision["approved"]}

graph.add_node("approval", approval_node)

# 실행
result = app.invoke({"refund_amount": 89.0, "refund_reason": "..."}, config=config)
# result는 interrupt 정보를 담은 응답을 반환

# 사용자 승인 후 재개
final = app.invoke(
    Command(resume={"approved": True}),
    config=config,
)
```

interrupt는 체크포인트와 결합되어 동작한다. 그래프가 중단되는 순간 상태가 저장되고, 임의의 시간 후 재개해도 정확히 그 지점부터 이어진다. 며칠 후 모바일 앱에서 승인이 들어와도 동일하게 처리된다.

### Streaming

LangGraph는 네 가지 스트리밍 모드를 지원한다. values는 매 super-step의 전체 상태를, updates는 부분 업데이트만, messages는 LLM 토큰을, debug는 모든 내부 이벤트를 스트리밍한다.

```python
async for event in app.astream(input, config, stream_mode="messages"):
    chunk, metadata = event
    print(chunk.content, end="", flush=True)
```

여러 모드를 동시에 구독하려면 `stream_mode=["values", "updates", "messages"]`처럼 리스트로 지정한다.

### LangSmith 통합

LangGraph는 LangSmith와 원활히 통합되어 모든 노드 실행, LLM 호출, 도구 호출, 상태 변이가 자동으로 트레이스에 기록된다. LangSmith UI에서 실행 그래프를 시각화하고 토큰 사용량, 지연, 비용을 분석할 수 있다.

```python
import os
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = "ls__..."
os.environ["LANGSMITH_PROJECT"] = "my-agent"
```

설정만 하면 추가 코드 없이 모든 실행이 LangSmith로 송출된다.

### Prebuilt: ReAct Agent

자주 쓰이는 ReAct 패턴은 한 줄로 만들 수 있다.

```python
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model=llm,
    tools=[search_tool, calculator],
    checkpointer=checkpointer,
)

result = agent.invoke({"messages": [("user", "도쿄 인구 곱하기 12는?")]}, config)
```

내부적으로 동일한 StateGraph를 사용하므로 필요시 직접 그래프로 풀어 커스터마이즈 가능하다.

## 다른 프레임워크와 비교

| 항목 | LangGraph | CrewAI | AutoGen | OpenAI Agents SDK |
|------|-----------|--------|---------|--------------------|
| 추상화 수준 | low-level (그래프) | high-level (역할) | mid-level (대화) | mid-level (핸드오프) |
| 사이클 지원 | 네이티브 (Pregel) | 제한적 | 대화 턴 | 도구 호출 루프 |
| 체크포인트 | 빌트인 (Postgres/SQLite) | 미지원 | 미지원 | 미지원 |
| HITL | interrupt + Command | 제한적 | 제한적 | 미지원 |
| Time-travel | 빌트인 | 미지원 | 미지원 | 미지원 |
| Subgraph | 네이티브 | 미지원 | nested chat | 미지원 |
| 트레이싱 | LangSmith | 제한적 | 로깅 | OpenAI 대시보드 |
| 학습 곡선 | 높음 | 매우 낮음 | 중간 | 낮음 |
| 월 다운로드 | 약 3,450만 | 수백만 | 수백만 | 수십만 |
| 엔터프라이즈 채택 | 매우 많음 | 많음 | 중간 | 증가 중 |

LangGraph의 강점은 정밀한 제어와 영속성이다. 약점은 학습 곡선과 LangChain 생태계 의존이다. 빠른 프로토타입은 CrewAI가 적합하고, 음성과 OpenAI 통합은 OpenAI Agents SDK가 적합하다. 그러나 프로덕션 에이전트의 영속성, HITL, 디버깅이 필요하면 LangGraph가 사실상 표준이다.

## 사용 사례

### LinkedIn AI 채용 어시스턴트

LinkedIn은 채용 담당자용 AI 어시스턴트의 멀티 에이전트 오케스트레이션을 LangGraph로 구축했다. 후보 검색, 프로필 분석, 메시지 초안 작성 에이전트가 협업하며, HITL로 채용 담당자의 승인을 받아 메시지를 발송한다.

### Klarna 고객 지원

Klarna는 8천 5백만 사용자에게 LangGraph 기반 AI 어시스턴트를 제공한다. 도입 후 첫 한 달간 230만 건의 대화를 처리했고 평균 해결 시간이 11분에서 2분으로 줄었다고 발표했다.

### Replit Agent

Replit Agent는 자연어 명령으로 풀스택 앱을 빌드하는 코딩 에이전트로 LangGraph를 기반으로 동작한다. 계획, 코드 생성, 실행, 디버깅 노드가 사이클로 연결되며 사용자 피드백이 interrupt로 주입된다.

### Uber 코드 마이그레이션

Uber는 대규모 코드베이스의 Java 17 마이그레이션을 LangGraph 멀티 에이전트로 자동화했다. 분석, 변환, 테스트, 검증 에이전트가 서브그래프로 협업하며 수만 개 파일을 일괄 처리했다.

## 한계

첫째, 학습 곡선이 가파르다. 상태 스키마 설계, 리듀서 정의, 조건부 엣지, 체크포인트 설정을 모두 사전에 결정해야 한다. CrewAI는 30분이면 멀티 에이전트를 띄우지만 LangGraph는 며칠이 필요할 수 있다.

둘째, LangChain 생태계 의존이다. LangGraph는 LangChain의 메시지 타입, 도구 인터페이스, 프롬프트 템플릿을 사용한다. LangChain의 잦은 API 변경이 하위 호환성 문제를 야기할 수 있고, LangChain을 쓰지 않는 팀은 어댑터를 작성해야 한다.

셋째, 디버깅 복잡성이다. 그래프가 커지면 실행 경로 추적이 어려워진다. LangSmith가 있어도 서브그래프 내부 상태 변이나 조건부 엣지의 예상치 못한 분기를 진단하려면 상당한 로깅 설정이 필요하다.

넷째, 상태 크기 관리다. 모든 노드가 글로벌 상태를 공유하므로 메시지 히스토리, 도구 결과, 중간 추론이 누적되어 LLM 컨텍스트 윈도우를 압박한다. 별도의 상태 정리(pruning) 전략이 필요하다.

다섯째, 클라우드 배포 비용이다. LangGraph 자체는 무료지만 LangGraph Platform, LangSmith 유료 구독이 사실상 필수다.

## 관련 문서

- [[langraph|LangGraph]] - 모델 카드 (entry)
- [[crewai-deep-dive|CrewAI 심층 분석]] - 역할 기반 멀티 에이전트 비교
- [[autogen-deep-dive|AutoGen 심층 분석]] - 대화 기반 멀티 에이전트 비교
- [[openai-agents-sdk|OpenAI Agents SDK]] - 핸드오프 중심 프레임워크
- [[google-adk|Google ADK]] - Workflow Agent 기반 프레임워크
