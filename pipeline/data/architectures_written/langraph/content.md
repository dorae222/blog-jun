# LangGraph: 그래프 기반 에이전트 오케스트레이션

**LangChain** · **2024-01-17** · **Agent Orchestration** · **MIT**

## 개요

LangGraph는 LLM 기반 에이전트와 멀티 에이전트 워크플로를 상태 머신(state machine) 및 유향 그래프(directed graph)로 표현하는 오케스트레이션 라이브러리다. LangChain이 2024년 1월 공개한 이 프레임워크는, 기존 LangChain 체인의 단방향 DAG(Directed Acyclic Graph) 한계를 극복하여 사이클(cycle)을 포함한 복잡한 에이전트 워크플로를 선언적으로 구성할 수 있게 한다.

LangGraph의 핵심 통찰은 **"에이전트 워크플로는 본질적으로 상태 그래프"**라는 것이다. 에이전트가 도구를 호출하고, 결과를 평가하고, 필요시 재시도하는 과정은 노드(처리 로직)와 엣지(전이 조건)로 이루어진 그래프로 자연스럽게 표현된다. 이 추상화를 통해 조건부 분기, 루프, 되돌아가기 등 복잡한 제어 흐름을 코드로 명확하게 정의할 수 있다.

그래프 기반 접근의 수학적 기반은 **유한 상태 기계(Finite State Machine, FSM)**에 있다. 그래프 $G = (V, E, S)$에서 $V$는 노드(처리 함수), $E$는 엣지(전이 규칙), $S$는 공유 상태 객체다. 각 노드 $v_i \in V$는 현재 상태 $s$를 입력받아 업데이트된 상태 $s' = v_i(s)$를 반환하며, 조건부 엣지 $e_{ij}: S \rightarrow \{0, 1\}$은 전이 조건을 결정한다.

이 모델이 기존 체인(chain) 방식과 근본적으로 다른 점은 **사이클(cycle)**의 허용이다. DAG 기반 체인에서는 데이터가 한 방향으로만 흐르지만, LangGraph의 그래프에서는 노드 $v_j$에서 이전 노드 $v_i$로 되돌아가는 엣지가 허용된다. 이는 에이전트의 "시도→평가→재시도" 패턴을 수학적으로 표현하는 데 필수적이다. 그래프의 실행은 종료 조건(END 노드 도달 또는 최대 반복 횟수 초과)이 충족될 때까지 계속된다:

$$\text{Execute}(G, s_0) = s_n \text{ where } s_n \text{ reaches END or } n > \text{max\_iterations}$$

![LangGraph 아키텍처 - StateGraph 기반 노드-엣지 구조의 에이전트 워크플로 오케스트레이션](figures/architecture.svg)

*Figure 1: LangGraph 아키텍처 - 노드(처리 로직)와 엣지(전이 조건)로 구성된 유향 그래프에서 공유 상태 객체를 통해 조건부 분기, 루프, 되돌아가기 등 복잡한 에이전트 워크플로를 선언적으로 정의한다.*

## 아키텍처 상세

LangGraph의 핵심 추상화는 **StateGraph**로, TypedDict 또는 Pydantic 모델로 정의된 상태 스키마를 그래프 전체에서 공유한다.

### 기본 구성 요소

| 요소 | 역할 | 예시 |
|------|------|------|
| State | 그래프 전체 공유 상태 | 메시지 목록, 다음 행동 |
| Node | 상태를 변환하는 함수 | LLM 호출, 도구 실행 |
| Edge | 노드 간 전이 규칙 | 정적, 조건부 |
| Entry Point | 그래프 시작점 | 첫 번째 노드 |
| END | 그래프 종료점 | 최종 상태 |

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from operator import add

class AgentState(TypedDict):
    messages: Annotated[list, add]  # 리듀서: 새 메시지를 기존에 추가
    next_action: str

def agent_node(state: AgentState) -> AgentState:
    """LLM을 호출하여 다음 행동을 결정"""
    response = llm.invoke(state["messages"])
    return {"messages": [response], "next_action": parse_action(response)}

def tool_node(state: AgentState) -> AgentState:
    """도구를 실행하고 결과를 반환"""
    result = execute_tool(state["next_action"])
    return {"messages": [result]}

def should_continue(state: AgentState) -> str:
    """조건부 엣지: 계속할지 종료할지 결정"""
    if state["next_action"] == "finish":
        return "end"
    return "continue"

# 그래프 구성
graph = StateGraph(AgentState)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)

graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue, {
    "continue": "tools",
    "end": END
})
graph.add_edge("tools", "agent")  # 사이클: 도구 실행 후 에이전트로 복귀

app = graph.compile()
result = app.invoke({"messages": ["서울 날씨를 알려줘"]})
```

### 노드(Node), 엣지(Edge), 상태(State) 심층 분석

LangGraph의 세 가지 핵심 개념을 더 자세히 살펴보면:

**노드(Node)**는 상태를 입력받아 변환된 상태를 반환하는 순수 함수이다. 노드는 LLM 호출, 도구 실행, 데이터 변환, 외부 API 호출 등 어떤 연산이든 수행할 수 있다. 중요한 점은 노드가 전체 상태를 반환하는 것이 아니라, **변경할 부분만 반환**한다는 것이다. LangGraph의 상태 리듀서(reducer)가 이 부분 업데이트를 기존 상태에 병합한다.

**엣지(Edge)**는 정적 엣지와 조건부 엣지로 나뉜다. 정적 엣지(`add_edge`)는 항상 같은 노드로 전이하며, 조건부 엣지(`add_conditional_edges`)는 현재 상태를 평가하는 라우팅 함수에 의해 다음 노드가 결정된다. 조건부 엣지의 라우팅 함수는 상태를 입력받아 문자열(다음 노드 이름)을 반환하는 단순한 함수이다.

**상태(State)**는 TypedDict 또는 Pydantic 모델로 정의되며, Annotated 타입 힌트를 통해 각 필드의 리듀서 전략을 지정할 수 있다. 예를 들어 `Annotated[list, add]`는 새 값을 기존 리스트에 추가하는 리듀서를 의미하고, `Annotated[str, lambda old, new: new]`는 새 값으로 덮어쓰는 리듀서를 의미한다. 이 선언적 리듀서 패턴은 Redux(JavaScript 상태 관리 라이브러리)에서 영감을 받았다.

### 체크포인팅(Checkpointing)과 영속성

LangGraph의 강력한 기능 중 하나로, 그래프 실행의 모든 상태를 저장하고 복원할 수 있다.

```python
from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string(":memory:")
app = graph.compile(checkpointer=memory)

# 실행 중단 후 재개
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke(input, config=config)
# 나중에 동일 thread_id로 재개 가능
```

체크포인팅의 내부 동작은 다음과 같다: 각 노드 실행 전후에 현재 상태의 스냅샷이 저장소(SQLite, PostgreSQL 등)에 직렬화되어 저장된다. 이 스냅샷에는 상태 데이터뿐 아니라 실행 메타데이터(타임스탬프, 노드 이름, 스텝 번호)도 포함된다. 이를 통해:

- **중단-재개(Interrupt-Resume)**: 장시간 작업을 중간에 중단하고 나중에 재개. 서버 재시작이나 장애 상황에서도 마지막 체크포인트부터 실행을 이어갈 수 있다
- **Human-in-the-Loop**: 특정 노드에서 `interrupt_before` 또는 `interrupt_after` 설정으로 인간의 승인을 기다린 후 진행. 고위험 작업(결제, 이메일 발송 등)에서 안전장치로 활용
- **타임 트래블(Time Travel)**: 이전 상태로 되돌아가서 다른 경로를 탐색. 디버깅 시 특정 시점의 상태를 재현하거나, 다른 입력으로 분기 실행이 가능

프로덕션 환경에서는 `PostgresSaver`를 사용하여 다중 워커 간에 체크포인트를 공유하고, 수평 확장(horizontal scaling)을 달성할 수 있다.

### 서브그래프(Subgraph)

복잡한 멀티 에이전트 아키텍처를 계층적으로 구성할 수 있다. 각 서브그래프는 독립적인 상태와 로직을 가지며, 부모 그래프에 노드로 삽입된다. 서브그래프는 자체적인 상태 스키마를 가질 수 있으므로, 부모 그래프의 상태와 서브그래프의 상태 간 매핑을 정의해야 한다. 이 계층적 구조는 복잡한 멀티 에이전트 시스템을 모듈화하는 데 핵심적이다.

예를 들어, 코드 리뷰 시스템에서 "보안 분석" 서브그래프는 보안 취약점 목록을 상태로 관리하고, "성능 분석" 서브그래프는 성능 병목 목록을 관리하며, 오케스트레이터 그래프가 양쪽의 결과를 종합하는 구조를 만들 수 있다.

## 핵심 혁신

1. **사이클 허용 그래프**: 기존 LangChain 체인의 DAG 한계를 극복하여, 에이전트의 반복적 추론-행동 루프를 자연스럽게 표현한다. ReAct 패턴의 Thought $\rightarrow$ Action $\rightarrow$ Observation 사이클이 그래프의 사이클로 직접 매핑된다.

2. **상태 중심 설계**: 글로벌 상태 객체를 통해 모든 노드가 공유 컨텍스트에 접근할 수 있으며, Annotated 리듀서를 통해 상태 업데이트 로직을 선언적으로 정의한다.

3. **체크포인팅과 Human-in-the-Loop**: 그래프 실행의 모든 시점을 저장하고 복원할 수 있어, 프로덕션 환경에서 필수적인 안전장치와 감사 추적(audit trail)이 가능하다.

4. **스트리밍 우선 설계**: 노드 실행 결과를 실시간으로 스트리밍할 수 있어, 사용자에게 에이전트의 진행 상황을 즉시 전달할 수 있다.

## 프레임워크 비교

### LangGraph vs LangChain Agents

LangGraph와 LangChain의 기존 Agent 시스템은 같은 생태계에 속하지만 설계 철학이 근본적으로 다르다. LangChain Agent는 LLM이 다음 행동을 자유롭게 결정하는 **암묵적 제어 흐름**을 사용한다. 반면 LangGraph는 개발자가 가능한 모든 경로를 **명시적 그래프**로 정의하고, LLM은 조건부 엣지의 라우팅 로직 내에서만 결정을 내린다.

이 차이는 프로덕션 환경에서 결정적이다. LangChain Agent는 프로토타이핑에 빠르지만, LLM의 결정이 예측 불가능하여 에러 처리와 디버깅이 어렵다. LangGraph는 초기 설계에 더 많은 시간이 들지만, 실행 경로가 명시적이므로 예측 가능성과 디버깅 용이성이 높다.

### LangGraph vs CrewAI

CrewAI는 "역할 기반 에이전트 팀"이라는 직관적인 추상화를 제공한다. 각 에이전트에 역할(Role), 목표(Goal), 배경(Backstory)을 부여하고, 태스크를 할당하면 에이전트들이 협력하여 작업을 수행한다. 학습 곡선이 낮고 빠르게 시작할 수 있지만, 세밀한 제어 흐름 정의나 상태 관리에서 한계가 있다.

| 측면 | LangGraph | CrewAI | AutoGen | 직접 구현 |
|------|-----------|--------|---------|----------|
| 제어 흐름 | 명시적 그래프 | 암시적 프로세스 | 대화 기반 | 자유 |
| 사이클 지원 | 네이티브 | 제한적 | 대화 턴 | 수동 구현 |
| 상태 관리 | TypedDict/Pydantic | 텍스트 컨텍스트 | 메시지 히스토리 | 수동 |
| 체크포인팅 | 내장 (SQLite/Postgres) | 미지원 | 미지원 | 수동 구현 |
| Human-in-the-Loop | 네이티브 지원 | 제한적 | 제한적 | 수동 구현 |
| 스트리밍 | 네이티브 | 제한적 | 제한적 | 수동 |
| 학습 곡선 | 높음 | **낮음** | 중간 | 매우 높음 |
| 디버깅 | LangSmith 통합 | 제한적 | 로깅 | 수동 |
| 프로덕션 적합성 | 높음 | 중간 | 낮음 | 구현에 의존 |

## 한계 및 과제

1. **높은 학습 곡선**: 그래프 기반 프로그래밍 패러다임은 기존 체인/파이프라인 패턴에 익숙한 개발자에게 진입 장벽이 된다. 상태 스키마 설계, 리듀서 정의, 조건부 엣지 로직 등을 사전에 모두 설계해야 하므로 프로토타이핑 속도가 CrewAI 대비 느리다.

2. **LangChain 생태계 의존성**: LangGraph는 LangChain의 메시지 타입, 도구 인터페이스, 프롬프트 템플릿에 의존한다. LangChain을 사용하지 않는 프로젝트에서는 별도의 어댑터 레이어가 필요하며, LangChain의 빈번한 API 변경이 하위 호환성 문제를 야기할 수 있다.

3. **디버깅 복잡성**: 그래프가 복잡해질수록 실행 경로 추적이 어려워진다. LangSmith 연동으로 일부 완화되지만, 서브그래프 내부의 상태 변이나 조건부 엣지의 예상치 못한 분기를 진단하기 위해서는 상당한 로깅 설정이 필요하다.

4. **상태 크기 관리**: 모든 노드가 글로벌 상태를 공유하므로, 멀티 에이전트 시나리오에서 상태 객체가 비대해질 수 있다. 대화 히스토리, 도구 결과, 중간 추론 등이 누적되면서 LLM 컨텍스트 윈도우를 압박하게 되며, 이를 관리하기 위한 별도의 상태 정리(pruning) 전략이 필요하다.

5. **클라우드 배포 비용**: LangGraph Cloud(LangGraph Platform)는 편리한 배포 환경을 제공하지만, 자체 호스팅 대비 비용이 높다. 오픈소스 라이브러리 자체는 무료이나, 프로덕션 수준의 체크포인팅과 모니터링을 위해서는 LangSmith/LangGraph Cloud 유료 구독이 사실상 필수적이다.

## 구현

**RAG 에이전트**: 쿼리 분석 $\rightarrow$ 검색 $\rightarrow$ 평가 $\rightarrow$ (불충분시 재검색) $\rightarrow$ 답변 생성의 사이클을 그래프로 구현한다. 검색 결과의 품질에 따라 동적으로 재검색 여부를 결정하는 조건부 엣지를 활용한다.

**멀티 에이전트 코드 리뷰**: 코드 분석 에이전트, 보안 검토 에이전트, 성능 분석 에이전트를 서브그래프로 구성하고, 오케스트레이터가 결과를 종합하여 최종 리뷰를 생성한다.

**고객 지원 에스컬레이션**: 초기 분류 $\rightarrow$ 자동 응답 시도 $\rightarrow$ (실패 시) 전문가 에이전트 $\rightarrow$ (미해결 시) 인간 에스컬레이션의 다단계 워크플로를 그래프로 표현한다. 체크포인팅으로 각 단계를 기록하여 감사 추적이 가능하다.

## 관련 모델

LangGraph는 ReAct의 추론-행동 루프를 그래프 구조로 형식화한 프레임워크다. LangChain 생태계의 LLM, 도구, 메모리 컴포넌트와 호환되며, LangSmith를 통한 실행 추적 및 디버깅, LangGraph Cloud를 통한 클라우드 배포를 지원한다.

## 참고 자료

- [LangGraph GitHub Repository](https://github.com/langchain-ai/langgraph)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph)

## 관련 문서

- [[react|ReAct]] - 발전 기반
