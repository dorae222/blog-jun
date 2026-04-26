<!-- infographic-hero -->
![Google ADK 핵심 요약](figures/infographic.svg)

*Figure: Google ADK 한 장 요약 인포그래픽*

# Google ADK: 워크플로 에이전트와 A2A를 표준으로 만든 Google의 오픈소스 에이전트 키트

**Google** · **2025-04-09** · **Agent Framework** · **Apache-2.0**

## 개요

Google Agent Development Kit(ADK)는 Google이 2025년 4월 9일 Google Cloud Next에서 공개한 오픈소스 멀티 에이전트 프레임워크다. 같은 키노트에서 발표된 Agent-to-Agent(A2A) 프로토콜의 reference implementation이자, Google Cloud의 Vertex AI Agent Builder, Agentspace의 기반 SDK이기도 하다. Google이 자체 사내 시스템(Customer Engineering Suite, Search Generative Experience 등)에 사용 중인 패턴을 외부에 공개한 것이라 해석되며, 출시 직후 Vertex AI Agent Engine과의 즉시 배포 통합이 가능했던 점이 그 증거다.

ADK의 가장 큰 차별점은 워크플로 에이전트(Workflow Agent)라는 결정적 오케스트레이션 컴포넌트를 일급 추상화로 도입한 점이다. Sequential, Parallel, Loop, Custom의 네 가지 패턴이 LLM Agent와 동일한 인터페이스를 따르므로, 결정적 단계 내부에 비결정적 LLM 의사결정을 자연스럽게 임베드할 수 있다. 이는 LangGraph가 모든 흐름을 단일 StateGraph로 표현하는 방식과 다르고, CrewAI의 sequential/hierarchical 프로세스보다 훨씬 정교하다.

ADK는 Python과 Java를 동시 지원하며, model agnostic 설계로 Gemini가 1순위지만 LiteLLM 어댑터를 통해 GPT, Claude, Mistral, Ollama 등도 호출할 수 있다. MCP 통합이 빌트인이며 A2A 프로토콜로 다른 프레임워크에서 만든 에이전트와 통신할 수 있어 멀티 벤더 에이전트 생태계의 표준 빌딩 블록 역할을 노린다.

## 아키텍처

ADK 실행은 Runner가 root_agent를 호출하면서 시작된다. root_agent는 일반적으로 Workflow Agent로 구성되며, 그 sub_agent로 LLM Agent와 다른 Workflow Agent를 임의의 깊이로 중첩할 수 있다. 모든 에이전트는 동일한 invoke 인터페이스를 가지므로 호출자 입장에서 LLM Agent인지 Workflow Agent인지 구분할 필요가 없다. 이 다형성(polymorphism)은 트리 구조의 멀티 에이전트 시스템을 매끄럽게 구성하는 핵심이다.

세션 상태는 Session 객체에 저장되며 Vertex AI 또는 사용자 정의 SessionService를 통해 영속화된다. 모든 에이전트 호출, 도구 실행, 모델 응답이 Event 스트림으로 기록되어 트레이싱과 디버깅에 사용된다.

## 핵심 컴포넌트

### LLM Agent

```python
from google.adk.agents import LlmAgent
from google.adk.tools import google_search

researcher = LlmAgent(
    name="Researcher",
    model="gemini-2.5-flash",
    instruction="주어진 주제를 검색하여 핵심 사실 5가지를 요약한다.",
    tools=[google_search],
)
```

### Workflow Agent

SequentialAgent는 sub_agent를 순서대로 실행하고, ParallelAgent는 동시에 실행한다. LoopAgent는 종료 조건이 충족될 때까지 sub_agent를 반복하며, CustomAgent는 사용자가 직접 제어 흐름을 구현한다.

```python
from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent

research_pipeline = SequentialAgent(
    name="ResearchPipeline",
    sub_agents=[researcher, summarizer, writer],
)

parallel_search = ParallelAgent(
    name="ParallelSearch",
    sub_agents=[arxiv_searcher, github_searcher, news_searcher],
)
```

### MCP 통합

```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

filesystem_tools = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/data"],
    ),
)

agent = LlmAgent(
    name="FileAnalyst",
    model="gemini-2.5-pro",
    tools=[filesystem_tools],
)
```

### A2A 통합

원격 에이전트를 표준 A2A 프로토콜로 호출할 수 있다.

```python
from google.adk.agents import RemoteA2aAgent

remote_billing = RemoteA2aAgent(
    name="RemoteBilling",
    agent_card_url="https://billing.example.com/agent-card.json",
)
```

### CLI

세 가지 CLI가 제공된다. `adk web`은 로컬 채팅 UI를, `adk run`은 터미널 실행을, `adk api_server`는 REST 서버를 띄운다. 모두 동일한 에이전트 정의를 그대로 사용한다.

```bash
adk web              # localhost:8000에 채팅 UI
adk run my_agent     # 터미널에서 대화
adk api_server       # REST 엔드포인트 노출
```

## 코드 예제

다음은 검색, 분석, 리포팅 에이전트를 SequentialAgent로 묶고 검색 단계에서 여러 출처를 ParallelAgent로 병렬 처리하는 멀티 에이전트 시스템이다.

```python
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent
from google.adk.tools import google_search
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

arxiv_searcher = LlmAgent(
    name="ArxivSearcher",
    model="gemini-2.5-flash",
    instruction="주제와 관련된 arXiv 논문 5편을 검색해 제목과 요약을 반환한다.",
    tools=[google_search],
    output_key="arxiv_results",
)

news_searcher = LlmAgent(
    name="NewsSearcher",
    model="gemini-2.5-flash",
    instruction="주제 관련 최신 뉴스 5건을 검색해 헤드라인과 요약을 반환한다.",
    tools=[google_search],
    output_key="news_results",
)

parallel_search = ParallelAgent(
    name="ParallelSearch",
    sub_agents=[arxiv_searcher, news_searcher],
)

analyst = LlmAgent(
    name="Analyst",
    model="gemini-2.5-pro",
    instruction=(
        "다음 데이터를 종합 분석한다.\n"
        "arxiv: {arxiv_results}\n"
        "news: {news_results}\n"
        "핵심 트렌드 3가지를 도출한다."
    ),
    output_key="analysis",
)

reporter = LlmAgent(
    name="Reporter",
    model="gemini-2.5-pro",
    instruction="분석 결과({analysis})를 한국어 1500자 리포트로 작성한다.",
)

research_pipeline = SequentialAgent(
    name="ResearchPipeline",
    sub_agents=[parallel_search, analyst, reporter],
)

session_service = InMemorySessionService()
runner = Runner(
    agent=research_pipeline,
    app_name="research_app",
    session_service=session_service,
)

session = session_service.create_session(app_name="research_app", user_id="u1")
for event in runner.run(
    user_id="u1",
    session_id=session.id,
    new_message="에이전트 프레임워크 시장 동향을 조사해줘.",
):
    print(event)
```

## 사용 사례

### Vertex AI Agent Builder

Google Cloud의 매니지드 에이전트 빌더 서비스가 ADK를 기반으로 한다. ADK로 정의된 에이전트는 추가 코드 없이 Vertex AI Agent Engine으로 배포된다.

### Agentspace

Google의 사내/기업용 AI 워크스페이스 Agentspace에서 사용자 정의 에이전트를 추가할 때 ADK를 사용한다.

### 멀티 벤더 에이전트 협업

A2A reference 구현이라는 위치 덕에 다른 프레임워크(LangGraph, CrewAI 등)에서 만든 에이전트와 표준 인터페이스로 협업할 수 있다.

## 비교

| 항목 | Google ADK | LangGraph | OpenAI Agents SDK | Mastra |
|------|------------|-----------|--------------------|--------|
| 결정적 워크플로 | Workflow Agent (4종) | StateGraph | 미지원 | 일급 추상화 |
| LLM 비종속 | LiteLLM | 네이티브 | LiteLLM | Vercel AI SDK |
| MCP 통합 | 빌트인 | 어댑터 | 어댑터 | 어댑터 |
| A2A 지원 | reference 구현 | 미지원 | 미지원 | 미지원 |
| 언어 | Python, Java | Python, JS | Python | TypeScript |
| 로컬 UI | adk web | LangGraph Studio | 미지원 | mastra dev |
| 클라우드 배포 | Vertex AI Agent Engine | LangGraph Cloud | OpenAI Platform | Vercel |

ADK는 Workflow Agent의 정교함과 A2A 표준 준수가 가장 큰 강점이다. 단점은 Gemini 외 모델에서 일부 기능이 제한될 수 있다는 점과 Vertex AI 생태계와 묶일수록 가치가 커진다는 종속성이다.

## 한계

첫째, Gemini 우선 설계다. LiteLLM으로 다른 모델을 호출할 수 있지만 도구 호출 신뢰성과 비용 효율은 Gemini 2.5 Flash/Pro에서 가장 좋다. 둘째, Workflow Agent의 학습 곡선이 있다. Sequential, Parallel, Loop, Custom 중 어느 패턴을 선택할지, sub_agent 사이의 데이터 전달은 어떻게 할지가 명시적 설계 결정이 된다. 셋째, 출시 초기라 통합 도구와 MCP 서버 카탈로그가 LangChain만큼 풍부하지 않다. 넷째, A2A는 표준이지만 다른 벤더가 아직 채택을 시작하는 단계라 실제 멀티 벤더 협업 사례가 제한적이다.

## 관련 문서

- [[a2a|Agent-to-Agent Protocol]] - ADK가 reference implementation으로 구현하는 표준
- [[mcp|Model Context Protocol]] - 도구 통합 표준 프로토콜
- [[langgraph-deep-dive|LangGraph 심층 분석]] - 그래프 기반 에이전트 오케스트레이션 비교
- [[openai-agents-sdk|OpenAI Agents SDK]] - 핸드오프 중심 멀티 에이전트 프레임워크
