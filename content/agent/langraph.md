---
title: "LangGraph: AI 에이전트 프레임워크"
slug: langraph
category: agent
tags: ["Agent Orchestration", "Cycles", "LangChain", "LangGraph", "State Graph"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.370472+00:00"
architecture_entry: langraph
---

# LangGraph: 그래프 기반 에이전트 오케스트레이션

**LangChain** · **2024-01-17** · **Agent Orchestration** · **MIT**

## 개요

LangGraph는 LLM 기반 에이전트와 멀티 에이전트 워크플로를 상태 머신(state machine) 및 유향 그래프(directed graph)로 표현하는 오케스트레이션 라이브러리다. LangChain이 2024년 1월 공개한 이 프레임워크는, 기존 LangChain 체인의 단방향 DAG(Directed Acyclic Graph) 한계를 극복하여 사이클(cycle)을 포함한 복잡한 에이전트 워크플로를 선언적으로 구성할 수 있게 한다.

LangGraph의 핵심 통찰은 **"에이전트 워크플로는 본질적으로 상태 그래프"**라는 것이다. 에이전트가 도구를 호출하고, 결과를 평가하고, 필요시 재시도하는 과정은 노드(처리 로직)와 엣지(전이 조건)로 이루어진 그래프로 자연스럽게 표현된다. 이 추상화를 통해 조건부 분기, 루프, 되돌아가기 등 복잡한 제어 흐름을 코드로 명확하게 정의할 수 있다.

그래프 기반 접근의 수학적 기반은 **유한 상태 기계(Finite State Machine, FSM)**에 있다. 그래프 $G = (V, E, S)$에서 $V$는 노드(처리 함수), $E$는 엣지(전이 규칙), $S$는 공유 상태 객체다. 각 노드 $v_i \in V$는 현재 상태 $s$를 입력받아 업데이트된 상태 $s' = v_i(s)$를 반환하며, 조건부 엣지 $e_{ij}: S \rightarrow \{0, 1\}$은 전이 조건을 결정한다.

![Architecture](figures/architecture.svg)

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

### 체크포인팅(Checkpointing)

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

체크포인팅을 통해:
- **중단-재개**: 장시간 작업을 중간에 중단하고 나중에 재개
- **Human-in-the-Loop**: 특정 노드에서 인간의 승인을 기다린 후 진행
- **타임 트래블**: 이전 상태로 되돌아가서 다른 경로를 탐색

### 서브그래프(Subgraph)

복잡한 멀티 에이전트 아키텍처를 계층적으로 구성할 수 있다. 각 서브그래프는 독립적인 상태와 로직을 가지며, 부모 그래프에 노드로 삽입된다.

## 핵심 혁신

1. **사이클 허용 그래프**: 기존 LangChain 체인의 DAG 한계를 극복하여, 에이전트의 반복적 추론-행동 루프를 자연스럽게 표현한다. ReAct 패턴의 Thought $\rightarrow$ Action $\rightarrow$ Observation 사이클이 그래프의 사이클로 직접 매핑된다.

2. **상태 중심 설계**: 글로벌 상태 객체를 통해 모든 노드가 공유 컨텍스트에 접근할 수 있으며, Annotated 리듀서를 통해 상태 업데이트 로직을 선언적으로 정의한다.

3. **체크포인팅과 Human-in-the-Loop**: 그래프 실행의 모든 시점을 저장하고 복원할 수 있어, 프로덕션 환경에서 필수적인 안전장치와 감사 추적(audit trail)이 가능하다.

4. **스트리밍 우선 설계**: 노드 실행 결과를 실시간으로 스트리밍할 수 있어, 사용자에게 에이전트의 진행 상황을 즉시 전달할 수 있다.

## 벤치마크/성능

| 측면 | LangGraph | CrewAI | AutoGen | 직접 구현 |
|------|-----------|--------|---------|----------|
| 제어 흐름 | 명시적 그래프 | 암시적 프로세스 | 대화 기반 | 자유 |
| 사이클 지원 | 네이티브 | 제한적 | 대화 턴 | 수동 구현 |
| 상태 관리 | TypedDict/Pydantic | 텍스트 컨텍스트 | 메시지 히스토리 | 수동 |
| 체크포인팅 | 내장 (SQLite/Postgres) | 미지원 | 미지원 | 수동 구현 |
| 학습 곡선 | 높음 | **낮음** | 중간 | 매우 높음 |
| 디버깅 | LangSmith 통합 | 제한적 | 로깅 | 수동 |

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

- [[react|ReAct]] — 발전 기반
