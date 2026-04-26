<!-- infographic-hero -->
![Agentic RAG: LLM-Driven Retrieval Control 핵심 요약](figures/infographic.svg)

*Figure: Agentic RAG: LLM-Driven Retrieval Control 한 장 요약 인포그래픽*

# Agentic RAG: LLM이 retrieval을 제어하는 패러다임

> 시리즈 안내: 5편 중 4편 - retrieval을 도구로 보는 에이전트 기반 RAG

## 개요

[[rag-03-self-rag|3편]]의 Self-RAG는 모델이 학습된 reflection token으로 검색을 평가했습니다. 그러나 이 reflection은 단일 호출 안에서 일어나는 정적 판단이었습니다. 사용자의 질문이 "지난 분기 보고서에서 시장 점유율 1위 기업을 찾고, 그 기업의 최근 실적 발표 요약과 우리 회사 대응 전략을 정리해줘" 같은 복합 작업이라면 단일 retrieval-generate 흐름으로는 풀리지 않습니다.

Agentic RAG는 이 문제를 풉니다. retrieval을 LLM의 도구(tool) 중 하나로 격상시키고, LLM이 plan-execute-observe-replan 루프를 돌면서 필요할 때마다 retrieval을 호출합니다. 이 편에서는 Single-Agent, Multi-Agent, Hierarchical 세 가지 패턴을 비교하고, LangGraph로 실제 코드를 보여드립니다.

## 배경: Agent의 부상

2023년 ReAct(Yao et al.)와 Toolformer(Schick et al.) 이후 LLM이 외부 도구를 호출한다는 발상이 빠르게 퍼졌습니다. 2024년에는 LangGraph, LlamaIndex Workflows, OpenAI Assistants API 같은 프레임워크가 자리 잡으면서 production-grade agent를 빌드할 수 있게 됐습니다.

이 흐름이 RAG와 만나면 자연스러운 결합이 일어납니다. retriever를 도구로 등록하면 LLM이 알아서 호출 시점, 횟수, 쿼리 형태를 결정합니다. 추가로 query rewrite, web search, calculator 같은 도구들과 조합되면 RAG는 더 이상 정적 파이프라인이 아닙니다.

## 핵심 개념: 3가지 패턴

### Pattern 1: Single-Agent (Reflection + Tool Use)

가장 단순한 형태입니다. 하나의 LLM이 ReAct 루프를 돌며 retrieval을 호출하고, 결과를 보고 다시 결정합니다.

```text
[User Query]
   ↓
[Thought] "관련 문서가 필요한가?"
[Action] retrieve("query")
[Observation] "..."
[Thought] "정보가 부족, 다른 키워드로 재검색"
[Action] retrieve("alt query")
[Observation] "..."
[Thought] "충분, 답변 생성"
[Final Answer]
```

### Pattern 2: Multi-Agent (Router + Specialists)

복잡한 워크플로우를 역할별 에이전트로 분리합니다.

| Agent | 역할 |
|-------|------|
| Router | 쿼리 분류, 적절한 specialist에게 전달 |
| Retrieval Agent | 도구 호출과 검색 결과 수집 |
| Generation Agent | 컨텍스트 기반 답안 생성 |
| Critic Agent | 답안 품질 검증, 부족하면 재요청 |

각 에이전트는 다른 모델을 쓸 수도 있습니다. Router는 빠른 Haiku, Generation은 정확한 Sonnet, Critic은 비용 절감용 Llama처럼 mix-and-match가 가능합니다.

### Pattern 3: Hierarchical

상위 에이전트가 작업을 sub-task로 분해해 하위 에이전트에 위임합니다. 보고서 작성처럼 단계가 많은 작업에 적합합니다.

```text
[Top Agent]
   ↓ decompose
[Sub-Agent A] → 자료 수집 (RAG)
[Sub-Agent B] → 분석 (RAG + 계산 도구)
[Sub-Agent C] → 작성 (LLM)
   ↓ aggregate
[Top Agent] → 통합 보고서
```

## 동작 원리: ReAct 루프와 State Graph

LangGraph에서 agentic RAG는 state graph로 표현됩니다. 노드는 에이전트 또는 도구, 엣지는 조건부 전환입니다.

```text
        ┌─────────┐
        │  Agent  │
        └────┬────┘
             │
      ┌──────┴──────┐
      ↓             ↓
[tool: retrieve]  [final_answer]
      │
      └───→ back to Agent
```

상태는 dict로 관리됩니다. 매 노드는 상태를 받고, 갱신해서 반환합니다.

```python
class AgentState(TypedDict):
    messages: List[BaseMessage]
    retrieved_docs: List[str]
    iteration: int
```

Router가 들어가면 상태에 `query_type` 같은 필드가 추가되고, 분기가 늘어납니다.

## 코드 예제: LangGraph Agentic RAG

ReAct 스타일의 single-agent RAG를 LangGraph로 구현합니다.

```python
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from typing import TypedDict, List, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

@tool
def retrieve_docs(query: str) -> str:
    """벡터 DB에서 query에 관련된 문서를 검색합니다."""
    docs = vectorstore.similarity_search(query, k=4)
    return "\n\n".join(d.page_content for d in docs)

@tool
def web_search(query: str) -> str:
    """최신 정보가 필요할 때 웹을 검색합니다."""
    return tavily_client.search(query)["results"]

tools = [retrieve_docs, web_search]
llm_with_tools = llm.bind_tools(tools)

class State(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]

def agent_node(state: State) -> State:
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

def tool_node(state: State) -> State:
    last = state["messages"][-1]
    outputs = []
    for call in last.tool_calls:
        tool_fn = {t.name: t for t in tools}[call["name"]]
        result = tool_fn.invoke(call["args"])
        outputs.append(
            AIMessage(content=str(result), name=call["name"])
        )
    return {"messages": outputs}

def should_continue(state: State) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END

graph = StateGraph(State)
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.set_entry_point("agent")
graph.add_conditional_edges("agent", should_continue)
graph.add_edge("tools", "agent")
app = graph.compile()

result = app.invoke({
    "messages": [
        HumanMessage(
            content="삼성전자 작년 매출과 올해 1분기 실적 차이를 분석해줘"
        )
    ]
})
print(result["messages"][-1].content)
```

이 에이전트는 자체적으로 두 번의 retrieve를 호출(작년 데이터, 올해 데이터)하고, 부족하면 web_search로 보강합니다.

## Multi-Agent 패턴 예제

Critic을 추가한 multi-agent 형태입니다.

```python
def critic_node(state: State) -> State:
    last_answer = state["messages"][-1].content
    critique = llm.invoke(
        f"답안:\n{last_answer}\n\n"
        f"이 답이 충분하면 'OK', 부족하면 부족한 부분을 명시"
    ).content
    if "OK" in critique:
        return {"messages": [AIMessage(content="approved")]}
    return {
        "messages": [
            HumanMessage(content=f"보완 필요: {critique}")
        ]
    }

def router(state: State) -> str:
    last = state["messages"][-1]
    if "approved" in last.content:
        return END
    return "agent"

graph.add_node("critic", critic_node)
graph.add_edge("agent", "critic")
graph.add_conditional_edges("critic", router)
```

이 구조에서는 답이 critic의 검증을 통과할 때까지 agent → tools → critic 루프가 반복됩니다.

## vs Self-RAG

| 항목 | Self-RAG | Agentic RAG |
|------|----------|-------------|
| Reflection 메커니즘 | 학습된 token | 프롬프트 + tool calling |
| 학습 필요성 | 필요 | 불필요(closed-source 가능) |
| 도구 확장 | 어려움 | 쉬움(retriever, web, calc 등) |
| 추론 비용 | 단일 LM call | multiple LLM call |
| Latency | 낮음-중간 | 중간-높음 |
| 디버깅 | 어려움 | 상태 그래프로 추적 가능 |

요약하면, Self-RAG는 학습 기반 closed loop, Agentic RAG는 프롬프트 기반 open loop입니다. 실무에서는 Self-RAG의 reflection 신호를 agent의 평가 도구로 결합하는 하이브리드도 등장하고 있습니다.

## 실제 케이스

### LlamaIndex Workflows

LlamaIndex가 2024년 발표한 Workflows는 이벤트 기반 agent 프레임워크입니다. 각 step이 이벤트를 발행하고 다른 step이 구독하는 구조라, RAG의 다양한 패턴(self-correction, multi-agent, parallel retrieval)을 표현하기 좋습니다.

### LangGraph in production

Klarna, Replit, Elastic 등 다수 기업이 LangGraph 기반 agentic RAG를 production에서 쓰고 있다고 공개했습니다. 공통 패턴은 다음과 같습니다.

1. Router가 쿼리를 카테고리(FAQ, 분석, 작업 요청)로 분류
2. 카테고리별 specialist agent가 처리
3. Critic이 답안을 검증하고 metric을 logging
4. 미해결 케이스는 human-in-the-loop으로 escalate

## 한계 및 trade-off

- 비용: 매 step마다 LLM call이 발생합니다. 5-step agent는 단일 RAG의 5배 이상 비용이 듭니다.
- Latency: tool call의 직렬 실행이 누적되면 사용자 체감 응답 시간이 5초를 넘기 쉽습니다. 병렬화 설계가 중요합니다.
- 무한 루프: 잘못 설계된 agent는 같은 도구를 반복 호출합니다. iteration limit과 critic이 필수입니다.
- 디버깅: state가 복잡해지면 어디서 잘못됐는지 추적이 어려워집니다. LangSmith, Langfuse 같은 tracing 도구가 사실상 필수입니다.
- Prompt 민감도: agent의 행동은 system prompt 문구에 크게 좌우됩니다. 작은 변경이 전체 흐름을 바꿉니다.

## 정리 + 다음 편 예고

Agentic RAG는 retrieval을 도구로 격상시켜 복잡한 작업을 풀 수 있게 합니다. Single-Agent, Multi-Agent, Hierarchical 패턴은 작업 복잡도에 따라 선택합니다. 다만 비용과 latency는 선형 이상으로 증가합니다. 다음 편이자 마지막 편에서는 두 가지 보완 기법인 Late Chunking과 Adaptive RAG Routing을 다룹니다. 청크 단위에서 컨텍스트 손실을 줄이는 임베딩 트릭과, 쿼리별로 어떤 RAG를 쓸지 동적으로 결정하는 라우팅을 살펴본 뒤 시리즈를 종합합니다.

## 관련 문서

- [[rag-01-evolution-overview|RAG 진화 개요]] - 1편: 시리즈 출발점
- [[rag-02-graphrag-lazygraphrag|GraphRAG와 LazyGraphRAG]] - 2편: 지식그래프 기반 검색
- [[rag-03-self-rag|Self-RAG]] - 3편: 자기 검토 RAG
- [[rag-05-late-chunking-adaptive-routing|Late Chunking과 Adaptive Routing]] - 5편: 청킹 혁신과 동적 라우팅
