# 멀티에이전트 시스템 비교: CrewAI vs AutoGen vs LangGraph

## 들어가며

:::info
이 글은 [[camel|CAMEL 논문 리뷰]]에서 다룬 멀티에이전트 개념의 실전 적용 편이다. [[llm-tool-use-patterns|Tool Use 패턴]]과 함께 읽으면 좋다.
:::

단일 LLM 에이전트로 해결하기 어려운 복잡한 작업 ( 예를 들어 "시장 조사 → 보고서 작성 → 코드 구현 → 테스트" ) 은 **여러 에이전트가 역할을 분담**하여 처리하는 것이 효과적이다.

2024년 기준 주요 멀티에이전트 프레임워크 3종을 비교한다: **CrewAI, AutoGen, LangGraph**.

---

## 프레임워크 개요

| | CrewAI | AutoGen | LangGraph |
|--|--------|---------|-----------|
| 개발사 | CrewAI Inc. | Microsoft | LangChain |
| 출시 | 2024.01 | 2023.10 | 2024.01 |
| 설계 철학 | 역할 기반 팀 | 대화 기반 협력 | 그래프 기반 워크플로우 |
| 추상화 수준 | 높음 (선언적) | 중간 | 낮음 (세밀한 제어) |
| 학습 곡선 | 낮음 | 중간 | 높음 |

---

## CrewAI: 역할 기반 팀

### 설계 철학

CrewAI는 **실제 팀의 비유**로 설계되었다. Agent(팀원), Task(업무), Crew(팀), Process(프로세스)의 4가지 개념으로 구성된다.

### 코드 예제

```python
from crewai import Agent, Task, Crew, Process

# 에이전트 정의
researcher = Agent(
    role="시장 조사 분석가",
    goal="최신 AI 시장 트렌드를 분석하여 인사이트를 제공한다",
    backstory="10년 경력의 테크 시장 분석가로, 데이터 기반 의사결정을 중시한다",
    tools=[web_search, data_analyzer],
    llm="gpt-4o",
)

writer = Agent(
    role="기술 문서 작성자",
    goal="분석 결과를 명확하고 구조화된 보고서로 작성한다",
    backstory="기술 블로그와 백서를 전문적으로 작성하는 테크니컬 라이터",
    llm="gpt-4o",
)

# 태스크 정의
research_task = Task(
    description="2024년 AI 에이전트 시장 현황을 조사하고 핵심 트렌드 5가지를 정리하라",
    expected_output="핵심 트렌드 5가지와 각각의 근거 데이터",
    agent=researcher,
)

report_task = Task(
    description="조사 결과를 바탕으로 경영진용 보고서를 작성하라",
    expected_output="구조화된 보고서 (요약, 트렌드 분석, 권장 사항 포함)",
    agent=writer,
    context=[research_task],    # 이전 태스크 결과 참조
)

# 팀 구성 및 실행
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, report_task],
    process=Process.sequential,   # 순차 실행
)
result = crew.kickoff()
```

### 장점
- **직관적인 API** ( 역할/목표/배경 설정이 자연어
- **빠른 프로토타이핑** ) 몇 줄로 멀티에이전트 시스템 구축
- **Process 패턴** ( sequential, hierarchical 등 사전 정의된 협력 패턴

### 단점
- 세밀한 에이전트 간 통신 제어가 어려움
- 복잡한 조건 분기 처리가 제한적
- 에러 복구 전략이 제한적

---

## AutoGen: 대화 기반 협력

### 설계 철학

AutoGen은 [[camel|CAMEL]]의 아이디어를 발전시켜, **에이전트 간 대화**로 문제를 해결한다. 인간 참여(Human-in-the-Loop)를 자연스럽게 지원한다.

### 코드 예제

```python
from autogen import ConversableAgent

# 에이전트 정의
coder = ConversableAgent(
    name="Coder",
    system_message="Python 코드를 작성하는 전문 개발자. 코드만 작성하고 실행하지 않는다.",
    llm_config={"model": "gpt-4o"},
)

reviewer = ConversableAgent(
    name="Reviewer",
    system_message="코드를 리뷰하고 개선점을 제안하는 시니어 개발자.",
    llm_config={"model": "gpt-4o"},
)

executor = ConversableAgent(
    name="Executor",
    system_message="코드를 실행하고 결과를 보고한다.",
    code_execution_config={"work_dir": "workspace"},
    human_input_mode="NEVER",
)

# 그룹 채팅
from autogen import GroupChat, GroupChatManager

group_chat = GroupChat(
    agents=[coder, reviewer, executor],
    messages=[],
    max_round=10,
)
manager = GroupChatManager(groupchat=group_chat)

# 실행
coder.initiate_chat(
    manager,
    message="피보나치 수열을 계산하는 함수를 작성하고 테스트해줘"
)
```

### 장점
- **유연한 대화 패턴** ) 에이전트 간 자유로운 대화
- **코드 실행** ( 내장 코드 실행 환경
- **Human-in-the-Loop** ) 인간 승인 단계 삽입 용이

### 단점
- 대화 방향 제어가 어려움 (발산 가능)
- 비용 예측이 어려움 (대화 길이가 가변적)
- 디버깅이 복잡함

---

## LangGraph: 그래프 기반 워크플로우

### 설계 철학

LangGraph는 에이전트 워크플로우를 **상태 머신(State Machine)**으로 모델링한다. 각 노드가 에이전트 액션이고, 엣지가 전환 조건이다. 가장 세밀한 제어를 제공한다.

### 코드 예제

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    research_data: str
    report: str
    approved: bool

# 노드 함수 정의
def research_node(state: AgentState) -> AgentState:
    # 조사 수행
    result = llm.invoke("시장 조사를 수행하라: " + state["messages"][-1])
    return {"research_data": result.content}

def write_node(state: AgentState) -> AgentState:
    # 보고서 작성
    result = llm.invoke(f"다음 데이터로 보고서 작성: {state['research_data']}")
    return {"report": result.content}

def review_node(state: AgentState) -> AgentState:
    # 품질 검토
    result = llm.invoke(f"이 보고서를 검토하라: {state['report']}")
    approved = "승인" in result.content
    return {"approved": approved}

# 조건 분기
def should_revise(state: AgentState) -> str:
    return "end" if state["approved"] else "write"

# 그래프 구성
graph = StateGraph(AgentState)
graph.add_node("research", research_node)
graph.add_node("write", write_node)
graph.add_node("review", review_node)

graph.set_entry_point("research")
graph.add_edge("research", "write")
graph.add_edge("write", "review")
graph.add_conditional_edges("review", should_revise, {"end": END, "write": "write"})

app = graph.compile()
result = app.invoke({"messages": ["AI 에이전트 시장 보고서 작성"]})
```

### 장점
- **세밀한 제어** ( 조건 분기, 루프, 에러 처리를 명시적으로 정의
- **상태 관리** ) 워크플로우 상태를 체계적으로 추적
- **디버깅** ( 그래프 시각화로 흐름 파악 용이
- **체크포인팅** ) 중간 상태 저장/복원 지원

### 단점
- 학습 곡선이 가장 높음
- 보일러플레이트 코드가 많음
- 단순한 파이프라인에는 과도한 복잡도

---

## 선택 가이드

| 요구사항 | 추천 프레임워크 |
|----------|---------------|
| 빠른 프로토타이핑 | **CrewAI** |
| 코드 생성 + 실행 | **AutoGen** |
| 복잡한 조건 분기 | **LangGraph** |
| 인간 참여 필요 | AutoGen 또는 LangGraph |
| 프로덕션 배포 | **LangGraph** (상태 관리, 체크포인팅) |
| 간단한 순차 파이프라인 | **CrewAI** |

### 프로젝트 복잡도별

| 복잡도 | 설명 | 추천 |
|--------|------|------|
| 낮음 | 2-3 에이전트, 순차 실행 | CrewAI |
| 중간 | 4-5 에이전트, 대화 기반 | AutoGen |
| 높음 | 조건 분기, 루프, 에러 복구 | LangGraph |

---

## 정리

| | CrewAI | AutoGen | LangGraph |
|--|--------|---------|-----------|
| 핵심 비유 | 팀 | 대화방 | 상태 머신 |
| 추상화 | 높음 | 중간 | 낮음 |
| 유연성 | 낮음 | 중간 | 높음 |
| 학습 곡선 | 낮음 | 중간 | 높음 |
| 프로덕션 | 중간 | 중간 | 높음 |

멀티에이전트 시스템은 아직 빠르게 발전 중인 분야다. 현재 시점에서는 **프로토타이핑에 CrewAI, 프로덕션에 LangGraph**가 가장 실용적인 선택이다. 핵심은 프레임워크 자체보다 **좋은 에이전트 설계(역할, 도구, 협력 패턴)**에 있다.
