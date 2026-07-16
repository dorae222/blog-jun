<!-- infographic-hero -->
![A2A Protocol Overview: Why Agents Need a Standard 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure: A2A Protocol Overview: Why Agents Need a Standard 한 장 요약 인포그래픽*

# A2A 프로토콜 등장 배경: 멀티에이전트의 표준 필요성

> 시리즈 안내: 본 글은 A2A(Agent-to-Agent) 프로토콜 시리즈의 1편입니다. 시리즈는 [[a2a-01-overview|1편 등장 배경]], [[a2a-02-specification|2편 스펙 분석]], [[a2a-03-vs-mcp|3편 A2A vs MCP]], [[a2a-04-python-sdk-tutorial|4편 Python SDK 실전]], [[a2a-05-adk-integration|5편 ADK 통합과 보안]]으로 구성됩니다.

![A2A agent web map](figures/agent-web-map.svg?v=layout-20260706-fix2)

*Figure 2: Agent Card 기반 발견에서 Task/Artifact 교환까지 이어지는 A2A agent web 흐름. (Source: A2A v1.0.0 specification 기반 자체 작성)*

:::info
2026-07 검증 기준: 본 시리즈는 A2A Protocol v1.0.0의 Agent Card, Task, Message/Part, Artifact, streaming event, push notification, JSON-RPC/gRPC/HTTP bindings를 기준으로 보강한다.
:::

## 도입: 왜 또 다른 프로토콜인가

2024년부터 2025년 초까지 LLM 기반 에이전트 프레임워크는 폭발적으로 늘어났다. LangGraph, CrewAI, AutoGen, LlamaIndex Workflow, Semantic Kernel, Google ADK, Mastra, Pydantic AI 등 메이저 프레임워크만 헤아려도 두 자릿수다. 각 프레임워크는 자신만의 메시지 포맷, 상태 모델, 도구 호출 규약을 가졌고, 생태계는 빠르게 사일로화되었다.

같은 회사 안에서도 마케팅팀은 CrewAI로 캠페인 에이전트를 짜고, 영업팀은 LangGraph로 리드 분류 에이전트를 짜며, 데이터팀은 ADK로 분석 에이전트를 만들었다. 이 셋이 서로 호출해야 할 때 어떻게 통신할 것인가. HTTP REST API를 부서마다 따로 정의하고, payload 스키마를 회의로 합의하고, 인증을 일일이 협상해야 했다.

[[a2a|A2A Protocol]](Agent-to-Agent Protocol)은 바로 이 문제를 표준화하려는 시도다. 2025년 4월 Google Cloud Next에서 공개됐고, 이후 a2aproject/A2A와 공식 프로토콜 사이트를 중심으로 스펙과 SDK 문서가 정리되고 있다. 이 시리즈는 2026-07-06 확인 기준 A2A Protocol v1.0.0 공개 스펙을 기준으로 Agent Card, Task, Message/Part, Artifact, streaming, push notification, JSON-RPC/gRPC/HTTP bindings를 설명한다.

## 에이전트 생태계 폭증과 사일로 문제

### 프레임워크 난립

2025년 한 해 동안 GitHub에서 "agent framework"를 표방하며 1k+ star를 받은 프로젝트만 30개가 넘는다. 각 프레임워크는 다음과 같은 자신만의 결정을 내렸다.

- 메시지 포맷: ChatML 변형, OpenAI function calling, Anthropic XML, 자체 JSON
- 상태 모델: stateless turn 기반, persistent conversation, graph state, blackboard
- 도구 호출: function calling, MCP, REST proxy, plugin
- 멀티 에이전트 통신: message passing, shared state, event bus, pub/sub

각자의 결정은 합리적이지만, 결과적으로 에이전트 A를 에이전트 B에 연결하려면 항상 어댑터 코드를 새로 작성해야 했다. n개 프레임워크가 있으면 n^2개의 어댑터가 필요한 고전적 통합 지옥이다.

### 기업 환경의 현실

대기업에서 에이전트를 도입할 때 마주치는 시나리오는 거의 비슷하다.

1. 부서마다 선호하는 framework가 다름. 영업은 CRM 통합이 강한 도구를, 데이터는 SQL 도구가 풍부한 도구를 선택
2. 외주/SI 업체가 각각 다른 stack으로 구축한 에이전트를 인수
3. M&A 후 자회사 에이전트와 통합 필요
4. SaaS 벤더가 제공하는 외부 에이전트(Salesforce Agentforce, ServiceNow Now Assist 등)와 사내 에이전트가 협업해야 함

이 모든 상황에서 "어떻게 통신할 것인가"가 매번 새로운 문제로 등장한다. REST API를 일일이 정의하고, OpenAPI 스펙을 합의하고, 인증을 협상하고, 변경 시마다 양쪽을 동시 배포해야 한다.

## A2A의 비전: HTTP가 웹을 만든 것처럼

A2A의 디자인 문서는 첫 페이지에서 명시적으로 비유한다. "HTTP가 웹을 가능하게 했듯, A2A는 에이전트 웹(Agent Web)을 가능하게 한다."

이 비유의 핵심은 두 가지다.

첫째, 트랜스포트 표준화. HTTP는 어떤 언어로 작성된 서버든 어떤 클라이언트든 메시지를 주고받을 수 있게 했다. A2A는 어떤 framework로 작성된 에이전트든 다른 에이전트를 호출할 수 있게 한다.

둘째, 디스커버리 표준화. 웹은 URL로 자원을 식별하고 robots.txt와 sitemap.xml로 자기 자신을 광고한다. A2A는 Agent Card라는 JSON 문서로 에이전트가 무엇을 할 수 있는지를 광고한다. URL을 알면 능력을 알 수 있다.

```text
┌─────────────────┐        A2A         ┌─────────────────┐
│  Sales Agent    │ ─────────────────> │ Marketing Agent │
│  (LangGraph)    │ <───── Task ─────  │   (CrewAI)      │
└─────────────────┘                    └─────────────────┘
        │                                       │
        │ MCP                                   │ MCP
        v                                       v
   CRM Server                              CMS Server
```

Sales Agent와 Marketing Agent는 서로 다른 framework이지만 A2A로 통신한다. 각자는 [[mcp|MCP]]로 자신의 도구(CRM, CMS)에 접근한다. 수평 통신과 수직 통신이 분리되어 깔끔하게 합성된다. 이 보완 관계는 [[a2a-03-vs-mcp|3편 A2A vs MCP]]에서 상세히 다룬다.

## 핵심 원칙

A2A는 다섯 가지 디자인 원칙을 명시한다.

1. **Embrace agentic capabilities**. 에이전트를 단순 RPC 엔드포인트로 다루지 않는다. 자율적이고, 비결정적이며, 장시간 실행될 수 있는 주체로 모델링한다.
2. **Build on existing standards**. HTTPS, JSON-RPC 2.0, Server-Sent Events, OAuth 2.0, OpenID Connect 등 검증된 웹 표준 위에 구축한다. 새 트랜스포트를 발명하지 않는다.
3. **Secure by default**. 인증과 권한이 옵션이 아니라 기본이다. 신뢰할 수 없는 에이전트 간 통신을 가정한다.
4. **Support long-running tasks**. 사람이 개입하거나 며칠 걸리는 작업도 자연스럽게 표현한다. polling, webhook, streaming을 모두 지원한다.
5. **Modality agnostic**. 텍스트뿐 아니라 파일, 구조화 데이터, 오디오, 비디오를 동등하게 다룬다.

이 원칙은 단순한 RPC 프로토콜과 차별화되는 지점이다. gRPC나 GraphQL은 1번을 직접 다루지 않고, OpenAPI는 4번을 자연스럽게 표현하지 못한다.

## 다른 에이전트 프로토콜과의 비교

A2A 외에도 에이전트 통신을 표준화하려는 시도가 있다.

### AGNTCY (Cisco, 2025)

Cisco가 주도하는 이니셔티브로, 에이전트 디렉토리(Agent Directory) 중심이다. 분산된 디렉토리에서 에이전트 메타데이터를 발견하고, 신뢰 그래프로 평판을 관리한다. 통신 자체보다 디스커버리에 무게를 둔다. A2A의 Agent Card 디스커버리와 일부 겹치지만, 분산 신뢰 모델이 차별점이다. 2026년 시점에는 A2A와 메타데이터 호환을 추진 중이다.

### AG-UI Protocol (CopilotKit, 2025)

이름이 비슷하지만 영역이 다르다. AG-UI는 에이전트와 사용자 인터페이스(UI) 사이의 통신 프로토콜이다. 즉 에이전트가 화면을 어떻게 갱신하고 사용자 입력을 어떻게 받을지 표준화한다. A2A가 백엔드 간 통신이라면 AG-UI는 에이전트와 프론트엔드 사이 통신이다. 보완 관계다.

### MCP (Anthropic, 2024)

Anthropic이 발표한 [[mcp|MCP]]는 에이전트와 도구/리소스 사이 통신을 표준화한다. A2A와는 직교한다. 한 에이전트 안에서는 MCP로 도구를 호출하고, 에이전트 사이에서는 A2A로 통신한다. 두 프로토콜은 함께 쓰이도록 설계되었다. 자세한 비교는 [[a2a-03-vs-mcp|3편]]에서 다룬다.

### 비교 표

| 프로토콜 | 영역 | 출시 | 거버넌스 | 위치 |
|----------|------|------|----------|------|
| A2A | 에이전트 간 통신 | 2025-04 | Linux Foundation | 수평 |
| MCP | 에이전트-도구 | 2024-11 | Anthropic | 수직 |
| AG-UI | 에이전트-UI | 2025 | CopilotKit | 프론트엔드 |
| AGNTCY | 디스커버리 | 2025 | Cisco 주도 | 디렉토리 |

이 네 프로토콜은 경쟁이 아니라 스택의 다른 층을 담당한다. 이 글에서는 공식 문서로 확인 가능한 책임 경계만 기준으로 삼는다.

## 공식 문서 기준 확인 항목

최신성 검증은 도입 기업 수나 특정 클라우드 지원 목록보다 공식 스펙의 객체와 binding을 우선한다.

- **Discovery**: `/.well-known/agent-card.json`와 AgentCard/Extended Agent Card
- **작업 모델**: Task, TaskStatus, TaskState, Message, Part, Artifact
- **전송 방식**: JSON-RPC, gRPC, HTTP+JSON/REST, SSE streaming
- **비동기 운영**: Task subscribe와 push notification configuration
- **보안**: SecurityScheme, OAuth2, OpenID Connect, mTLS, AgentCardSignature

## 시리즈 로드맵

이 시리즈는 5편으로 구성된다.

1. **본 편 - 등장 배경**: 왜 표준이 필요한가, A2A의 비전과 다른 프로토콜과의 관계
2. [[a2a-02-specification|2편 - 스펙 분석]]: Agent Card, Task 라이프사이클, JSON-RPC 2.0, gRPC, SSE, 인증
3. [[a2a-03-vs-mcp|3편 - A2A vs MCP]]: 수직과 수평 통신의 직교성, 보완 패턴 코드 예제
4. [[a2a-04-python-sdk-tutorial|4편 - Python SDK 실전]]: a2a-sdk로 Researcher + Writer 협업 시스템 구현
5. [[a2a-05-adk-integration|5편 - ADK 통합과 보안]]: Google ADK 통합 패턴, JWS 서명, mTLS, OIDC, 프로덕션 배포

각 편은 독립적으로 읽을 수 있지만, 처음 보는 독자라면 순서대로 따라가는 것을 권장한다.

## 정리 + 다음 편

에이전트 framework 폭증은 통신 표준의 부재를 드러냈고, A2A는 HTTP가 웹을 만든 방식과 같은 비유로 이 문제를 풀려 한다. 핵심은 두 가지다.

- **트랜스포트 표준화**: 어떤 framework든 A2A 엔드포인트를 노출하면 다른 에이전트가 호출 가능
- **디스커버리 표준화**: Agent Card라는 JSON 문서로 능력을 광고

A2A는 MCP, AG-UI, AGNTCY와 경쟁하지 않고 스택의 다른 층을 담당한다. 이 시리즈에서는 채택 현황보다 v1.0.0 스펙 객체와 실제 조합 패턴을 중심으로 다룬다.

다음 [[a2a-02-specification|2편]]에서는 스펙 자체로 들어가 Agent Card의 JSON 스키마, Task 라이프사이클, JSON-RPC 2.0과 gRPC 트랜스포트, SSE 스트리밍, 인증 방식을 실제 페이로드 예시와 함께 분해한다.

## 실무로 옮기기 전: A2A 특유의 결정

A2A를 "또 하나의 RPC"로 도입하면 대부분 실패한다. 이 프로토콜의 값어치는 원격 에이전트를 자율적이고 장시간 실행되는 주체로 다루는 데 있고, 그러려면 설계 단계에서 네 가지를 먼저 못박아야 한다. 각 결정은 나중에 무엇으로 검증하는지가 서로 다르다.

| 결정 | 무엇을 정하나 | 검증 신호 |
|------|--------------|-----------|
| 능력 노출 | 어떤 skill을 Agent Card로 공개하고 무엇을 숨길지 | `/.well-known/agent-card.json` 응답에 skill과 securityScheme가 의도대로 나오는가 |
| 작업 추적 | Task를 어느 지점에서 생성하고 상태 전이를 어디에 기록할지 | `task_id`별 상태 전이(submitted → working → completed/failed)가 로그에 남는가 |
| 산출물 분리 | 대화(Message)와 결과물(Artifact)을 어떻게 나눌지 | Artifact가 message body가 아니라 별도 참조로 감사·재사용되는가 |
| 비동기 방식 | streaming(SSE)과 push notification 중 무엇을 언제 쓸지 | 연결이 끊긴 장시간 Task가 push webhook으로 복구되는가 |

이 표의 목적은 선택지를 줄이는 것이다. 도구 호출은 [[mcp|MCP]], 작업 위임은 A2A, UI 이벤트는 [[ag-ui-realtime-events|AG-UI 실시간 이벤트]], 에이전트 발견은 [[agntcy-agent-discovery-trust|AGNTCY]]가 맡는다. 이 책임들이 한 레이어에 섞이면 구현은 빨리 끝나도 장애 위치를 설명하기 어렵다. 네 프로토콜의 경계를 한눈에 보려면 [[agent-protocol-stack|Agent Protocol Stack]]을 함께 읽는 것이 좋다.

## 자주 나오는 실패 패턴

- **remote agent를 단순 HTTP RPC로만 취급한다** - 자율성·장시간 실행·비결정성을 흡수할 상태 모델이 없어 재시도와 복구가 무너진다. Task를 일급 객체로 두는 것이 출발점이다.
- **Task 상태가 사라진다** - 서버 재기동이나 연결 끊김에서 진행 중 작업을 이어받지 못한다. TaskState를 영속화하고 `task_id`로 다시 조회할 수 있어야 한다.
- **Artifact가 message body에 섞인다** - 결과물을 재사용·감사·버전관리하기 어렵다. Artifact는 참조로 분리한다.

관측성 축은 미리 이름을 정해 둔다. 성공/실패만으로는 부족하고, 최소한 `agent_id`, `task_id`, `context_id`, `tool_call_id`를 trace에 실어야 사용자 요청 하나가 어느 원격 에이전트의 어느 Task로 흘렀는지 재구성할 수 있다. 이 관점은 [[a2a-05-adk-integration|5편 ADK 통합과 보안]]에서 인증·서명과 함께 구체화한다.

## 관련 문서

- [[a2a|A2A Protocol]] - 본 시리즈가 속한 아키텍처 엔트리
- [[a2a-02-specification|A2A 스펙 분석]] - 바로 다음 편, Agent Card와 Task 라이프사이클
- [[a2a-03-vs-mcp|A2A vs MCP]] - 수직·수평 통신의 직교성
- [[a2a-04-python-sdk-tutorial|A2A Python SDK 실전]] - Researcher + Writer 협업 구현
- [[a2a-05-adk-integration|ADK + A2A 통합]] - JWS 서명·mTLS·프로덕션 배포
- [[mcp|MCP]] - 에이전트-도구 수직 통신, A2A와 보완 관계
- [[agent-protocol-stack|Agent Protocol Stack]] - MCP·A2A·AG-UI·AGNTCY 레이어 지도
- [[ai-agent-technology-guide|AI Agent 기술 지도]] - 에이전트 프레임워크 전반 개관
