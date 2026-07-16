<!-- infographic-hero -->
![A2A Python SDK Tutorial: Building a Multi-Agent System 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure: A2A Python SDK Tutorial: Building a Multi-Agent System 한 장 요약 인포그래픽*

# A2A 실전: Python SDK로 멀티에이전트 구현

> 시리즈 안내: 본 글은 [[a2a|A2A Protocol]] 시리즈의 4편입니다. [[a2a-01-overview|1편]], [[a2a-02-specification|2편]], [[a2a-03-vs-mcp|3편]]에서 다룬 개념을 코드로 옮깁니다. 이후 [[a2a-05-adk-integration|5편]]에서 프로덕션 통합과 보안을 다룹니다.

![A2A Python SDK sequence](figures/researcher-writer-sequence.svg?v=layout-20260706-fix2)

*Figure 2: Client가 Writer를 호출하고 Writer가 Researcher를 다시 호출하는 2단계 A2A 흐름. (Source: A2A v1.0.0 specification 기반 자체 작성)*

:::info
2026-07 검증 기준: 본 시리즈는 A2A Protocol v1.0.0의 Agent Card, Task, Message/Part, Artifact, streaming event, push notification, JSON-RPC/gRPC/HTTP bindings를 기준으로 보강한다.
:::

## 도입: 두 에이전트로 협업 시스템 만들기

본 편의 목표는 다음과 같다. Python A2A SDK(`a2a-sdk`)를 사용해 두 에이전트가 협업하는 최소 시스템을 구현한다.

- **Researcher Agent**: 주제를 받아 웹 검색 결과를 정리한 noteset을 산출
- **Writer Agent**: noteset을 받아 1500자 이상의 블로그 포스트를 산출

Writer가 Researcher를 A2A로 호출하고, 클라이언트는 Writer를 A2A로 호출한다. 호출 체인이 두 단계가 되도록 의도적으로 설계했다. 실제 멀티에이전트 시스템의 패턴을 압축한 것이다.

## 1. 설치와 프로젝트 구조

```bash
pip install "a2a-sdk[server,client]>=1.0.0"
pip install "openai>=1.50.0" "uvicorn[standard]>=0.30.0"
```

프로젝트 구조는 다음과 같다.

```text
multi_agent/
├── researcher/
│   ├── __init__.py
│   ├── executor.py
│   └── main.py
├── writer/
│   ├── __init__.py
│   ├── executor.py
│   └── main.py
├── client.py
└── pyproject.toml
```

## 2. Researcher Agent: AgentExecutor 구현

서버 측 핵심은 `AgentExecutor` 추상 클래스를 상속해 `execute`와 `cancel`을 구현하는 것이다. SDK가 JSON-RPC 디스패치, SSE 스트리밍, Task 라이프사이클 관리를 모두 맡고, 우리는 비즈니스 로직만 작성하면 된다.

```python
# researcher/executor.py
import asyncio
from openai import AsyncOpenAI
from a2a.server import AgentExecutor
from a2a.server.events import EventQueue
from a2a.types import (
    Message,
    Part,
    TextPart,
    Artifact,
    TaskStatus,
    TaskState,
    RequestContext,
)

SYSTEM_PROMPT = """You are a research agent. Given a topic, produce
a structured noteset with 5 to 8 bullet points capturing key facts,
recent developments, and credible sources. Output JSON with fields
'topic' and 'notes' (list of {fact, source})."""

class ResearcherExecutor(AgentExecutor):
    def __init__(self, openai_api_key: str):
        self.llm = AsyncOpenAI(api_key=openai_api_key)

    async def execute(self, ctx: RequestContext, queue: EventQueue):
        topic = ctx.message.parts[0].text

        # 1. working 상태 통지
        await queue.enqueue_status(TaskStatus(state=TaskState.WORKING))

        # 2. LLM 호출 (실제로는 web search MCP를 추가하면 더 좋음)
        try:
            resp = await self.llm.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Topic: {topic}"},
                ],
            )
            notes_json = resp.choices[0].message.content
        except Exception as e:
            await queue.enqueue_status(
                TaskStatus(state=TaskState.FAILED, message=str(e))
            )
            return

        # 3. Artifact로 산출물 반환
        await queue.enqueue_artifact(
            Artifact(
                name="research_notes.json",
                parts=[TextPart(type="text", text=notes_json)],
            )
        )

        # 4. completed 통지
        await queue.enqueue_status(TaskStatus(state=TaskState.COMPLETED))

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        await queue.enqueue_status(TaskStatus(state=TaskState.CANCELLED))
```

핵심 패턴은 `EventQueue`에 이벤트를 enqueue하면 SDK가 자동으로 SSE 스트림이나 polling 응답에 반영한다는 점이다. 즉 우리는 동기 함수를 짜듯이 작성하지만 외부에는 스트리밍으로 보인다.

### main.py: 서버 부트스트랩

```python
# researcher/main.py
import os
import uvicorn
from a2a.server import A2AServer
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from researcher.executor import ResearcherExecutor

def build_agent_card() -> AgentCard:
    return AgentCard(
        name="researcher",
        description="Conducts research and produces structured notes",
        url="http://localhost:8001/a2a",
        version="1.0.0",
        protocol_version="1.0",
        capabilities=AgentCapabilities(
            streaming=True,
            push_notifications=False,
            state_transition_history=True,
        ),
        default_input_modes=["text/plain"],
        default_output_modes=["application/json"],
        skills=[
            AgentSkill(
                id="research",
                name="Research",
                description="Produce structured research notes on a topic",
                tags=["research", "notes"],
                examples=["Research recent advances in retrieval augmented generation"],
            )
        ],
    )

def main():
    executor = ResearcherExecutor(openai_api_key=os.environ["OPENAI_API_KEY"])
    server = A2AServer(
        agent_card=build_agent_card(),
        executor=executor,
        agent_card_path="/.well-known/agent-card.json",
        rpc_path="/a2a",
    )
    uvicorn.run(server.app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    main()
```

`A2AServer`가 ASGI 앱을 만들어 주고, `agent_card_path`에 GET 요청이 오면 Agent Card JSON을 반환한다. `rpc_path`로 들어오는 JSON-RPC 호출을 `executor.execute`로 라우팅한다.

## 3. Writer Agent: 다른 에이전트를 A2A로 호출

Writer Agent는 클라이언트인 동시에 서버다. 자신은 A2A 서버로 노출되고, 내부에서 Researcher를 A2A 클라이언트로 호출한다.

```python
# writer/executor.py
import os
from openai import AsyncOpenAI
from a2a.server import AgentExecutor
from a2a.server.events import EventQueue
from a2a.client import A2AClient
from a2a.types import (
    Message,
    TextPart,
    Artifact,
    TaskStatus,
    TaskState,
    RequestContext,
)

WRITE_SYSTEM = """You are a senior tech writer. Given a research noteset,
produce a 1500-word blog post in Korean with sections: introduction,
key insights, deep dive, conclusion. Use a professional tone."""

class WriterExecutor(AgentExecutor):
    def __init__(self, researcher_url: str, openai_api_key: str):
        self.researcher_url = researcher_url
        self.llm = AsyncOpenAI(api_key=openai_api_key)

    async def execute(self, ctx: RequestContext, queue: EventQueue):
        topic = ctx.message.parts[0].text
        await queue.enqueue_status(TaskStatus(state=TaskState.WORKING))

        # 1. A2A로 Researcher 호출 (horizontal)
        async with A2AClient(self.researcher_url) as client:
            await client.load_agent_card()
            task = await client.send_task_subscribe(
                message=Message(
                    role="user",
                    parts=[TextPart(type="text", text=topic)],
                )
            )

            notes_json: str | None = None
            async for ev in client.stream_events(task.id):
                if ev.artifact and ev.artifact.name == "research_notes.json":
                    notes_json = ev.artifact.parts[0].text
                if ev.status and ev.status.state in (
                    TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED
                ):
                    break

            if not notes_json:
                await queue.enqueue_status(
                    TaskStatus(state=TaskState.FAILED, message="No notes")
                )
                return

        # 2. LLM으로 본문 작성
        resp = await self.llm.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": WRITE_SYSTEM},
                {"role": "user", "content": f"Topic: {topic}\n\nNotes:\n{notes_json}"},
            ],
        )
        article = resp.choices[0].message.content

        # 3. Artifact 반환
        await queue.enqueue_artifact(
            Artifact(
                name="article.md",
                parts=[TextPart(type="text", text=article)],
            )
        )

        await queue.enqueue_status(TaskStatus(state=TaskState.COMPLETED))

    async def cancel(self, ctx: RequestContext, queue: EventQueue):
        await queue.enqueue_status(TaskStatus(state=TaskState.CANCELLED))
```

여기서 주목할 점은 Writer가 Researcher의 SSE 스트림을 받아 artifact가 도착하는 즉시 활용한다는 것이다. polling이 아니라 push 기반이라 latency가 낮다.

### Writer main.py

```python
# writer/main.py
import os
import uvicorn
from a2a.server import A2AServer
from a2a.types import AgentCard, AgentSkill, AgentCapabilities
from writer.executor import WriterExecutor

AGENT_CARD = AgentCard(
    name="writer",
    description="Produces blog posts from research notes",
    url="http://localhost:8002/a2a",
    version="1.0.0",
    protocol_version="1.0",
    capabilities=AgentCapabilities(streaming=True),
    default_input_modes=["text/plain"],
    default_output_modes=["text/markdown"],
    skills=[
        AgentSkill(
            id="write_blog",
            name="Write Blog",
            description="Write a 1500-word Korean blog post from a topic",
            tags=["writing", "blog"],
            examples=["Write a blog post about A2A protocol"],
        )
    ],
)

def main():
    executor = WriterExecutor(
        researcher_url="http://localhost:8001/a2a",
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )
    server = A2AServer(agent_card=AGENT_CARD, executor=executor, rpc_path="/a2a")
    uvicorn.run(server.app, host="0.0.0.0", port=8002)

if __name__ == "__main__":
    main()
```

## 4. 클라이언트: SSE 스트리밍과 멀티 호출

이제 외부 클라이언트가 Writer를 부르면 자동으로 두 단계 호출 체인이 실행된다.

```python
# client.py
import asyncio
from a2a.client import A2AClient
from a2a.types import Message, TextPart, TaskState

async def write_one(topic: str) -> str:
    async with A2AClient("http://localhost:8002/a2a") as client:
        await client.load_agent_card()
        task = await client.send_task_subscribe(
            message=Message(role="user", parts=[TextPart(type="text", text=topic)])
        )

        article: str | None = None
        async for ev in client.stream_events(task.id):
            if ev.status:
                print(f"[{topic}] state -> {ev.status.state}")
            if ev.artifact and ev.artifact.name == "article.md":
                article = ev.artifact.parts[0].text
            if ev.status and ev.status.state == TaskState.COMPLETED:
                break

        if not article:
            raise RuntimeError(f"No article for {topic}")
        return article

async def main():
    # 5개 주제를 동시 호출 (asyncio.gather)
    topics = [
        "Multi-agent collaboration patterns",
        "RAG evolution in 2025",
        "Cost-aware LLM routing",
        "Inference time scaling",
        "Tool calling reliability",
    ]
    articles = await asyncio.gather(*(write_one(t) for t in topics))
    for t, a in zip(topics, articles):
        print(f"=== {t} ({len(a)} chars) ===")

if __name__ == "__main__":
    asyncio.run(main())
```

이 클라이언트는 5개 주제를 동시에 호출한다. 각 호출은 Writer -> Researcher 체인을 거쳐 LLM을 두 번씩 사용하지만, asyncio.gather로 병렬화되어 실제 wall clock은 1개 처리 시간과 비슷하다. A2A의 SSE는 처음부터 비동기를 가정해 설계되었기 때문에 이런 패턴이 자연스럽다.

## 5. 실행과 디버깅

세 프로세스를 띄운다.

```bash
# 터미널 1
export OPENAI_API_KEY=sk-...
python -m researcher.main

# 터미널 2
python -m writer.main

# 터미널 3
python client.py
```

기대 출력은 다음과 같다.

```output
[Multi-agent collaboration patterns] state -> submitted
[Multi-agent collaboration patterns] state -> working
[RAG evolution in 2025] state -> submitted
[RAG evolution in 2025] state -> working
...
[Multi-agent collaboration patterns] state -> completed
=== Multi-agent collaboration patterns (1923 chars) ===
...
```

### a2a-cli로 디버깅

SDK 버전에 따라 제공되는 `a2a-cli`는 디버깅에 매우 유용하다.

```bash
# Agent Card 조회
a2a-cli card http://localhost:8001/.well-known/agent-card.json

# Task 직접 보내고 SSE 실시간 출력
a2a-cli send http://localhost:8001/a2a \
  --message "Research RAG evolution in 2025" \
  --stream

# 진행 중인 Task 상태 조회
a2a-cli get http://localhost:8001/a2a --task-id task-xxx

# Task 취소
a2a-cli cancel http://localhost:8001/a2a --task-id task-xxx
```

각 호출은 JSON-RPC 페이로드를 그대로 출력하므로 스펙과 실제 동작이 일치하는지 즉시 확인할 수 있다.

## 6. 패턴 정리

이 튜토리얼에서 사용한 핵심 패턴을 정리하면 다음과 같다.

### AgentExecutor 패턴

- `execute(ctx, queue)`에 비즈니스 로직만 작성
- `queue.enqueue_status`로 상태 전환을 알리고 `enqueue_artifact`로 산출물 반환
- 실패 시 `TaskState.FAILED`를 명시적으로 enqueue

### A2AClient 패턴

- `async with` 컨텍스트로 connection 관리
- `load_agent_card`로 능력 확인
- `send_task_subscribe`로 SSE 스트림 시작
- `stream_events`를 `async for`로 소비

### 합성 패턴

- 한 에이전트 안에서 `A2AClient`를 호출해 다른 에이전트와 협업
- artifact를 즉시 받아 후속 단계 시작 (low latency)
- asyncio.gather로 동시 호출 (high throughput)

## 정리 + 다음 편

a2a-sdk는 AgentExecutor와 A2AClient라는 두 추상화 위에 짜여 있어, JSON-RPC와 SSE 같은 트랜스포트 디테일을 신경 쓰지 않고 비즈니스 로직만 작성할 수 있다. 두 에이전트를 합성하는 것도 한 에이전트 안에서 `A2AClient`를 호출하면 끝이다.

본 편의 코드는 의도적으로 단순화되었다. 프로덕션에서는 다음이 추가되어야 한다.

- 인증(Bearer/OAuth/mTLS)
- Signed Agent Card 검증
- Retries와 timeout
- Task ID로 멱등성 보장
- 관찰성(logging, tracing)

이 모든 토픽이 다음 [[a2a-05-adk-integration|5편]]에서 다뤄진다. Google ADK가 reference implementation으로서 이 과제들을 어떻게 해결하는지, 그리고 Cloud Run + Vertex AI 위에 어떻게 배포하는지 본다.

## 튜토리얼 코드를 프로덕션으로 옮길 때

지금 만든 세 파일(`researcher/executor.py`, `writer/executor.py`, `client.py`)은 A2A의 흐름을 보여주려고 최소화했다. 실제 서비스로 승격할 때 코드가 어디서 바뀌는지를 짚으면 다음과 같다.

- **에러 처리 일관성**: `ResearcherExecutor`는 LLM 호출을 `try/except`로 감싸 실패 시 `TaskState.FAILED`를 enqueue하지만, `WriterExecutor`의 `self.llm.chat.completions.create` 호출과 Researcher를 부르는 `A2AClient` 블록에는 같은 방어가 없다. 원격 호출과 LLM 호출은 모두 실패를 가정하고 감싸서 원인을 담은 `FAILED` 상태로 내보내야, 클라이언트가 그 이유를 스트림에서 읽는다.
- **Task 상태 영속화**: 예제는 Task 상태를 프로세스 메모리에만 둔다. 서버를 재기동하거나 배포하면 진행 중이던 Task는 사라지고 `task_id`로 다시 조회할 수 없다. 프로덕션에서는 상태 저장을 외부(DB나 Redis)로 빼서 재기동 후에도 Task를 이어받게 한다.
- **인증 추가**: `build_agent_card`가 만드는 Agent Card에는 securityScheme가 없고, Writer가 Researcher를 부르는 `A2AClient(self.researcher_url)` 호출도 자격 증명을 싣지 않는다. localhost에서는 통하지만 에이전트가 네트워크를 넘는 순간, Agent Card에 보안 스킴을 선언하고 서버는 Bearer/OAuth를 검증해야 한다.
- **streaming과 재연결**: `client.py`와 Writer는 `stream_events`를 `async for`로 소비하다가 종료 상태에서 `break`한다. SSE 연결이 중간에 끊기면 이 루프는 그냥 끝나고 복구 경로가 없다. Researcher의 Agent Card는 `push_notifications=False`로 두었는데, 장시간 Task라면 이 값을 켜서 webhook으로 결과를 받는 경로를 함께 두어야 한다.
- **배포**: 지금은 세 프로세스를 로컬 포트 8001/8002로 띄우고 `researcher_url`을 `http://localhost:8001/a2a`로 하드코딩했다. 프로덕션에서는 각 에이전트를 컨테이너로 나누고, 하드코딩한 주소 대신 서비스 디스커버리와 TLS를 붙인다.

이 다섯 가지를 reference implementation 수준으로 채우는 과정은 [[a2a-05-adk-integration|5편 ADK 통합과 보안]]에서 이어진다.

## 처음 따라 할 때 자주 막히는 지점

- **Agent Card URL과 실제 포트의 불일치**: Agent Card의 `url` 필드(`http://localhost:8001/a2a`)는 RPC 엔드포인트를 가리키고, Card 문서 자체는 `agent_card_path`(`/.well-known/agent-card.json`)에서 받아온다. uvicorn이 여는 포트(8001), `rpc_path`(`/a2a`), Writer에 넣은 `researcher_url` 이 셋이 어긋나면 `load_agent_card()`나 RPC 호출이 곧바로 실패한다. 처음 붙일 때 가장 흔한 실수다.
- **모든 것이 async라는 점**: `execute`는 코루틴이고, `A2AClient`는 `async with`로 여는 비동기 컨텍스트이며, 이벤트는 `async for`로 소비한다. `enqueue_status`/`enqueue_artifact` 앞의 `await`를 빠뜨리거나 동기 코드에서 부르면 조용히 어긋난다. 진입점은 `asyncio.run(main())`이고, 5개 주제 동시 호출은 `asyncio.gather`가 담당한다.
- **두 서버 모두 OPENAI_API_KEY가 필요**: Researcher와 Writer executor는 부팅 시 `os.environ["OPENAI_API_KEY"]`를 읽는다. 키가 없으면 서버가 뜨면서 죽는다. 실행 블록은 터미널 1에만 `export`를 보였지만, 두 서버가 각자의 환경에서 키를 가져야 한다.
- **Researcher를 먼저 띄운다**: Writer는 실행 시점에 `A2AClient`로 Researcher를 부른다. 따라서 Writer에 첫 요청이 들어오기 전에 Researcher(:8001)가 올라와 있어야 한다. 순서가 꼬이면 Writer는 Researcher의 Card를 못 읽고 Task가 `FAILED`로 끝난다.

## 관련 문서

- [[a2a-05-adk-integration|ADK + A2A 통합]] - 이 튜토리얼이 생략한 인증·서명·재시도·배포를 프로덕션 레퍼런스로 채우는 바로 다음 편
- [[a2a-02-specification|A2A 스펙 분석]] - 코드로 다룬 Agent Card, Task 라이프사이클, SSE, JSON-RPC의 정확한 스키마 근거
- [[a2a-03-vs-mcp|A2A vs MCP]] - Researcher에 실제 web search를 붙일 때 MCP를 어느 층에 끼우는지
- [[a2a-01-overview|A2A 등장 배경]] - 두 에이전트를 굳이 A2A로 합성한 이유와 문제의식
- [[a2a|A2A Protocol]] - 5편 전체를 잇는 시리즈 아키텍처 엔트리
- [[mcp|MCP]] - Researcher의 도구 접근을 표준화하는 수직 통신 프로토콜, A2A와 보완 관계
- [[agent-protocol-stack|Agent Protocol Stack]] - A2A·MCP·AG-UI·AGNTCY가 각각 어느 레이어를 맡는지
- [[ai-agent-technology-guide|AI Agent 기술 지도]] - 멀티에이전트 프레임워크 전반 개관
