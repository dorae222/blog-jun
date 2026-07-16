<!-- infographic-hero -->
![A2A vs MCP: Horizontal Agent Communication and Vertical Tool Access 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure: A2A vs MCP: Horizontal Agent Communication and Vertical Tool Access 한 장 요약 인포그래픽*

# A2A vs MCP: 수직(tool)과 수평(agent) 통신의 차이

> 시리즈 안내: 본 글은 [[a2a|A2A Protocol]] 시리즈의 3편입니다. [[a2a-01-overview|1편 등장 배경]]과 [[a2a-02-specification|2편 스펙 분석]]에 이어, A2A와 [[mcp|MCP]]의 관계를 정리합니다. 이후 [[a2a-04-python-sdk-tutorial|4편]], [[a2a-05-adk-integration|5편]]으로 이어집니다.

![A2A MCP cross stack](figures/a2a-mcp-cross-stack.svg?v=layout-20260706-fix2)

*Figure 2: A2A의 수평 통신과 MCP의 수직 도구 접근이 결합되는 구조. (Source: A2A v1.0.0 specification 기반 자체 작성)*

:::info
2026-07 검증 기준: 본 시리즈는 A2A Protocol v1.0.0의 Agent Card, Task, Message/Part, Artifact, streaming event, push notification, JSON-RPC/gRPC/HTTP bindings를 기준으로 보강한다.
:::

## 도입: 두 프로토콜은 경쟁이 아니다

A2A와 MCP는 자주 혼동된다. 둘 다 LLM 시대의 통신 표준이고, 둘 다 JSON-RPC 위에 올라가며, 둘 다 1년 사이에 표준의 위치에 올랐기 때문이다. 하지만 두 프로토콜은 직교한다. 다른 층을 담당하고, 함께 쓰이도록 설계되었다.

핵심 명제는 한 줄로 압축된다.

- **A2A는 horizontal**: 에이전트와 에이전트 사이 통신
- **MCP는 vertical**: 에이전트와 도구/리소스 사이 통신

이 한 줄을 받아들이면 나머지는 따라온다. 본 편은 두 프로토콜의 차이를 표로 정리하고, 보완 패턴을 코드 예제로 보여 준다.

## 차원별 비교

### 1. 통신 대상

```text
       A2A (horizontal)
   ┌───────────┐         ┌───────────┐
   │  Agent A  │ <─────> │  Agent B  │
   └─────┬─────┘         └─────┬─────┘
         │                     │
         │ MCP                 │ MCP
         │ (vertical)          │ (vertical)
         v                     v
    ┌─────────┐           ┌─────────┐
    │ Tool 1  │           │ Tool 2  │
    │ (DB)    │           │ (CRM)   │
    └─────────┘           └─────────┘
```

A2A는 항상 두 자율 주체(에이전트) 사이의 통신이다. 양쪽 모두 LLM이 의사결정하고 도구를 사용할 수 있다. MCP는 에이전트가 외부 도구나 리소스(데이터베이스, 파일시스템, API)에 접근하는 통로다. 도구는 자율 의사결정을 하지 않는다.

### 2. 추상화 단위

| 항목 | A2A | MCP |
|------|-----|-----|
| 호출 단위 | Task | Tool call |
| 응답 모델 | 장기 라이프사이클(submitted -> working -> ...) | 즉시 응답(stateless) |
| 모달리티 | text, file, structured data 모두 1급 | 주로 text/structured data |
| 산출물 | Artifact 객체 | tool result(JSON) |

A2A의 단위는 Task로, "보고서 한 편 작성"같은 큰 일을 표현한다. MCP의 단위는 Tool call로, "이 SQL을 실행해 결과를 반환"같은 단일 행위다.

### 3. 상태 모델

A2A는 stateful이다. Task는 ID로 식별되며, 시간이 흘러가는 동안 history가 누적되고 input-required 상태에서 사람을 기다릴 수 있다. 며칠짜리 작업이 자연스럽게 표현된다.

MCP는 기본적으로 stateless다. 한 도구 호출은 자기 자신으로 완결된다. session이라는 개념이 있지만 주로 connection 관리용이다. resource subscription처럼 stateful한 기능도 있지만 부수적이다.

### 4. 동기 vs 비동기

A2A는 동기와 비동기 모두 1급. SSE 스트리밍, webhook, polling을 모두 지원한다. 5초 안에 끝나는 작업도, 5일 걸리는 작업도 같은 모델로 표현된다.

MCP는 주로 동기. 도구를 호출하면 곧장 결과를 받는다. 예외는 sampling 기능으로, 서버가 클라이언트(LLM)에게 추론을 역으로 요청하는 비동기 흐름이다.

### 5. 보안 모델

A2A는 신뢰할 수 없는 두 주체 사이의 통신을 가정한다. mTLS, Signed Agent Card, OIDC principal propagation 등 다층 보안이 기본이다.

MCP는 한 사용자의 LLM과 그 사용자가 신뢰하는 도구 사이의 통신을 가정한다. 보통 같은 신뢰 영역 안이거나, 사용자가 직접 도구 권한을 부여한다. 인증은 보통 OAuth, 단순한 token, 또는 stdio 트랜스포트(local)로 처리한다.

### 종합 비교 표

| 차원 | A2A | MCP |
|------|-----|-----|
| 통신 대상 | Agent <-> Agent | Agent <-> Tool/Resource |
| 추상화 | Task | Tool/Resource/Prompt |
| 상태 | Long-running stateful | Mostly stateless |
| 응답 시간 | 초~일 단위 | 즉시 |
| 모달리티 | text, file, structured 1급 | 주로 structured |
| 비동기 | streaming + webhook 1급 | 주로 동기 (sampling 예외) |
| 보안 가정 | 신뢰 경계 횡단 | 보통 한 신뢰 영역 |
| 발표 | 2025-04 (Google) | 2024-11 (Anthropic) |
| 거버넌스 | Linux Foundation | Anthropic + 커뮤니티 |

## 보완 패턴: 한 시스템에서 함께 쓰기

실제 시스템에서는 A2A와 MCP가 함께 쓰이는 경우가 절대 다수다. 두 프로토콜은 다른 층이라 합성된다.

### 시나리오: Sales Agent가 Marketing Agent를 호출

회사에 두 에이전트가 있다.

- Sales Agent: 영업팀 소유, CRM(예: Salesforce)에 MCP로 접근
- Marketing Agent: 마케팅팀 소유, CMS(예: Contentful)에 MCP로 접근

영업 담당자가 Sales Agent에게 "이 잠재 고객에게 보낼 맞춤 자료를 준비해 줘"라고 요청하면, Sales Agent는 다음 단계를 수행한다.

```text
1. MCP로 Salesforce에서 고객 정보 조회
2. A2A로 Marketing Agent에게 "고객 X에 맞춘 자료 생성" 요청
3. Marketing Agent가 MCP로 CMS에서 템플릿 조회
4. Marketing Agent가 LLM으로 콘텐츠 생성
5. Marketing Agent가 Artifact로 PDF 반환
6. Sales Agent가 받은 Artifact를 다시 MCP로 CRM에 첨부
```

각 에이전트는 내부 도구를 MCP로 호출하고, 에이전트 사이 협업은 A2A로 한다. 깔끔히 분리된다.

### 코드 예제: MCP 도구를 사용하는 A2A 에이전트

다음은 Marketing Agent가 받은 Task를 처리하는 의사코드다. A2A로 Task를 받고, 내부에서 MCP 도구를 호출한 뒤 Artifact를 반환한다.

```python
from a2a.server import AgentExecutor, EventQueue
from a2a.types import TaskStatus, TaskState, Artifact, Part
from mcp.client import MCPClient
import asyncio

class MarketingAgentExecutor(AgentExecutor):
    """A2A로 들어온 Task를 받아 MCP로 도구를 사용해 처리한다."""

    def __init__(self, llm, cms_mcp_url: str):
        self.llm = llm
        # MCP는 vertical: 에이전트가 도구에 접근
        self.cms = MCPClient(cms_mcp_url)

    async def execute(self, context, event_queue: EventQueue):
        task = context.current_task
        user_msg = context.message.parts[0].text

        # 1. 진행 상태 업데이트
        await event_queue.enqueue_status(
            TaskStatus(state=TaskState.WORKING)
        )

        # 2. MCP로 CMS 템플릿 조회 (vertical 호출)
        async with self.cms.session() as session:
            templates = await session.call_tool(
                "list_templates",
                arguments={"category": "personalized_pitch"}
            )
            template = templates.content[0].text

        # 3. LLM으로 콘텐츠 생성
        prompt = f"Use template:\n{template}\n\nFor request:\n{user_msg}"
        content = await self.llm.complete(prompt)

        # 4. MCP로 PDF 변환 도구 호출
        async with self.cms.session() as session:
            pdf_result = await session.call_tool(
                "render_pdf",
                arguments={"markdown": content}
            )
            pdf_uri = pdf_result.content[0].text

        # 5. A2A Artifact로 결과 반환 (horizontal 응답)
        await event_queue.enqueue_artifact(
            Artifact(
                name="pitch.pdf",
                parts=[Part(type="file", file={
                    "name": "pitch.pdf",
                    "mime_type": "application/pdf",
                    "uri": pdf_uri,
                })]
            )
        )

        # 6. 완료 상태
        await event_queue.enqueue_status(
            TaskStatus(state=TaskState.COMPLETED)
        )

    async def cancel(self, context, event_queue):
        await event_queue.enqueue_status(
            TaskStatus(state=TaskState.CANCELLED)
        )
```

이 코드에서 두 프로토콜의 책임이 명확히 갈린다.

- A2A 부분: `context.current_task`로 Task를 받음, `event_queue.enqueue_status`/`enqueue_artifact`로 진행 상황과 산출물 반환
- MCP 부분: `self.cms.session()`으로 CMS에 연결, `call_tool`로 템플릿 조회와 PDF 렌더링

A2A 입장에서 MCP 호출은 그저 "에이전트가 일을 처리하기 위해 사용하는 내부 도구"다. 외부에서 보면 Task의 시작과 끝만 보인다. MCP 입장에서 호출자가 LLM 직속이든, A2A를 받은 에이전트든 차이가 없다.

### Sales Agent 쪽 호출 코드

반대편 Sales Agent가 Marketing Agent를 부르는 부분은 다음과 같다.

```python
from a2a.client import A2AClient
from a2a.types import Message, Part

async def request_pitch(customer_info: dict, marketing_url: str) -> str:
    """A2A로 Marketing Agent를 호출해 PDF artifact를 받는다."""
    async with A2AClient(marketing_url) as client:
        # Agent Card 자동 fetch
        await client.load_agent_card()

        # Task 전송 + SSE 구독
        task = await client.send_task_subscribe(
            message=Message(
                role="user",
                parts=[Part(type="text", text=f"Pitch for {customer_info}")]
            )
        )

        # 스트림에서 완료 대기
        async for event in client.stream_events(task.id):
            if event.type == "artifact":
                return event.artifact.parts[0].file["uri"]
            if event.status and event.status.state == "completed":
                break

    raise RuntimeError("No artifact returned")
```

Sales Agent는 `A2AClient`로 다른 에이전트를 호출한다. 이때 자신의 내부에서는 별도로 Salesforce MCP를 사용해 고객 정보를 가져왔을 것이다. 두 호출은 서로 독립이다.

## 어느 경우에 어느 프로토콜인가

설계 시 결정 트리는 단순하다.

```text
   Q: 통신 대상이 자율적 의사결정 주체인가?
        │
   ┌────┴────┐
  Yes        No
   │          │
  A2A        MCP
   │          │
   │     Q: 도구의 결과가 stateless인가?
   │          │
   │      ┌───┴───┐
   │     Yes      No (resource subscription, etc.)
   │      │       │
   │     MCP     MCP (with subscriptions)
   │
  Q: long-running인가?
        │
    ┌───┴───┐
   Yes      No
    │       │
   A2A     A2A (still A2A; 단지 SSE 끝이 빠름)
```

요약하면 "상대가 LLM을 가진 자율 에이전트면 A2A, 단순 도구나 데이터 소스면 MCP"다.

## 스펙상 보완 관계

A2A와 MCP의 관계는 한쪽이 다른 쪽을 대체하는 구조가 아니다. A2A v1.0.0 스펙은 장시간 실행되는 agent task, message/artifact 교환, streaming/push notification을 다룬다. MCP 2025-11-25 스펙은 Host/Client/Server 구조에서 Tools, Resources, Prompts와 client feature를 다룬다.

따라서 실제 시스템에서는 Orchestrator가 A2A로 전문 에이전트에게 Task를 위임하고, 각 전문 에이전트가 MCP로 도구와 데이터에 접근하는 조합이 자연스럽다. 이 글의 비교 표와 예시는 이 직교성을 설명하기 위한 reference architecture로 보면 된다.

## 정리 + 다음 편

A2A와 MCP는 경쟁이 아니라 직교다. A2A는 에이전트 사이 수평 통신, MCP는 에이전트와 도구 사이 수직 통신을 담당한다. 이 차이는 다음 다섯 차원으로 정리된다.

- 통신 대상(자율 주체 vs 도구), 추상화(Task vs Tool call), 상태(stateful vs stateless), 응답 시간(long-running vs immediate), 보안 가정(횡단 vs 동일 신뢰 영역)

실제 시스템에서는 두 프로토콜이 함께 쓰인다. 한 에이전트가 A2A로 다른 에이전트를 부르고, 내부에서는 MCP로 도구를 사용한다. 코드는 두 호출을 명확히 분리한다.

다음 [[a2a-04-python-sdk-tutorial|4편]]에서는 a2a-sdk를 직접 사용해 Researcher와 Writer 두 에이전트가 협업하는 시스템을 처음부터 끝까지 구현한다. AgentExecutor와 A2AClient의 실제 코드, SSE 스트리밍 처리, asyncio 병렬 호출까지 다룬다.

## 설계에서 A2A와 MCP를 가르는 기준

앞의 비교를 실제 설계 판단으로 옮기면, 대부분의 경계는 네 가지 질문으로 갈린다. 새 연결을 놓을 때마다 아래를 순서대로 물으면 "이건 A2A로, 저건 MCP로"가 자연스럽게 정해진다.

| 구분 질문 | 이렇다면 A2A (수평) | 이렇다면 MCP (수직) |
|-----------|--------------------|--------------------|
| 상대가 스스로 판단하고 도구를 쓰는 주체인가 | 자율적으로 의사결정하는 다른 에이전트 | 판단 없이 결과만 돌려주는 도구·데이터 소스 |
| 맡기는 단위가 무엇인가 | "보고서 한 편 작성" 같은 Task | "이 SQL 실행" 같은 단일 tool call |
| 상태 수명이 어떤가 | ID로 며칠간 history를 쌓고 input-required로 사람을 기다림 | 한 호출로 완결되는 stateless 즉시 응답 |
| 호출자와 상대가 어느 신뢰 경계에 있는가 | 신뢰 경계를 횡단 (mTLS, Signed Agent Card, OIDC) | 대개 같은 신뢰 영역 (OAuth, token, stdio local) |

한 문장으로 줄이면 본문의 결론과 같다. 상대가 LLM을 가진 자율 에이전트면 A2A, 단순 도구나 데이터 소스면 MCP다. 응답 시간, 비동기 방식, 모달리티 같은 나머지 축은 이 첫 판단을 따라온다.

## A2A와 MCP를 함께 쓸 때 흔한 혼동

두 프로토콜은 직교하지만, 경계가 흐려지면 한쪽을 다른 쪽으로 억지로 표현하게 된다. 본문에서 다룬 실패 패턴을 판단 기준과 함께 정리한다.

- **도구 접근을 A2A로 감싼다** - 단일 tool call을 Task 라이프사이클로 표현하면, stateless 호출에 불필요한 상태 관리와 스트리밍이 붙는다. 즉시 끝나는 도구는 MCP로 두는 편이 맞다.
- **에이전트 간 위임을 MCP로 밀어 넣는다** - 상대가 자율 주체인데 tool call로 감싸면 Agent Card 발견, Artifact 반환, 신뢰 경계 보안 (mTLS/OIDC)이 사라진다. 상대가 판단하는 주체면 A2A다.
- **MCP tool을 remote agent처럼 장시간 돌린다** - MCP는 즉시 응답 모델이라 며칠짜리 흐름을 이어받을 Task state나 push notification이 없다. long-running 위임은 A2A로 표현한다.
- **두 계층의 실패를 같은 retry 정책으로 묶는다** - long-running한 A2A Task 실패와 즉시성인 MCP tool call 실패는 성질이 달라, 한 정책으로 재시도하면 복구가 무너진다. orchestrator에서 계층별로 나눈다.

이 혼동은 대부분 기술 선택이 아니라 경계가 흐린 데서 시작한다. 새 화살표를 그을 때 "상대가 주체인가 도구인가", "단위가 Task인가 tool call인가"만 먼저 확정해도 대부분 갈린다.

## 관련 문서

- [[a2a|A2A Protocol]] - 본 시리즈가 속한 아키텍처 엔트리, 수평 통신의 전체 그림
- [[mcp|MCP]] - 이 글이 대비한 수직 도구 접근 프로토콜, 보완 관계의 반대 축
- [[a2a-01-overview|A2A 등장 배경]] - 왜 수평 통신 표준이 필요했는지, framework 사일로 문제
- [[a2a-02-specification|A2A 스펙 분석]] - 이 글의 Task·Artifact·보안 대비가 기대는 스펙 근거
- [[a2a-04-python-sdk-tutorial|A2A Python SDK 실전]] - 다음 편, 이 글의 의사코드를 실제 a2a-sdk로 구현
- [[a2a-05-adk-integration|ADK + A2A 통합]] - A2A 쪽 신뢰 경계 보안 (mTLS·JWS·OIDC) 심화
- [[mcp-05-security-operations|MCP 보안과 운영]] - MCP 쪽 동일 신뢰 영역 가정과 보안 대비축
- [[agent-protocol-stack|Agent Protocol Stack]] - A2A·MCP·AG-UI·AGNTCY 레이어 지도로 보는 직교성
