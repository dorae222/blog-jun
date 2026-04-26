<!-- infographic-hero -->
![A2A Protocol Overview: Why Agents Need a Standard 핵심 요약](figures/infographic.svg)

*Figure: A2A Protocol Overview: Why Agents Need a Standard 한 장 요약 인포그래픽*

# A2A 프로토콜 등장 배경: 멀티에이전트의 표준 필요성

> 시리즈 안내: 본 글은 A2A(Agent-to-Agent) 프로토콜 시리즈의 1편입니다. 시리즈는 [[a2a-01-overview|1편 등장 배경]], [[a2a-02-specification|2편 스펙 분석]], [[a2a-03-vs-mcp|3편 A2A vs MCP]], [[a2a-04-python-sdk-tutorial|4편 Python SDK 실전]], [[a2a-05-adk-integration|5편 ADK 통합과 보안]]으로 구성됩니다.

## 도입: 왜 또 다른 프로토콜인가

2024년부터 2025년 초까지 LLM 기반 에이전트 프레임워크는 폭발적으로 늘어났다. LangGraph, CrewAI, AutoGen, LlamaIndex Workflow, Semantic Kernel, Google ADK, Mastra, Pydantic AI 등 메이저 프레임워크만 헤아려도 두 자릿수다. 각 프레임워크는 자신만의 메시지 포맷, 상태 모델, 도구 호출 규약을 가졌고, 생태계는 빠르게 사일로화되었다.

같은 회사 안에서도 마케팅팀은 CrewAI로 캠페인 에이전트를 짜고, 영업팀은 LangGraph로 리드 분류 에이전트를 짜며, 데이터팀은 ADK로 분석 에이전트를 만들었다. 이 셋이 서로 호출해야 할 때 어떻게 통신할 것인가. HTTP REST API를 부서마다 따로 정의하고, payload 스키마를 회의로 합의하고, 인증을 일일이 협상해야 했다.

[[a2a|A2A Protocol]](Agent-to-Agent Protocol)은 바로 이 문제를 표준화하려는 시도다. 2025년 4월 Google Cloud Next에서 Google이 50여 개 파트너와 함께 발표했고, 2025년 6월 Linux Foundation에 기증되면서 벤더 중립 거버넌스로 전환되었다. 2026년 4월 시점, 전 세계 150여 개 조직이 프로덕션에 도입했고, 주요 클라우드(AWS Bedrock AgentCore, Azure AI Foundry, GCP Vertex AI Agent Engine)가 모두 native 지원을 제공한다.

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

이 네 프로토콜은 경쟁이 아니라 스택의 다른 층을 담당한다. 2026년 시점에는 네 표준이 모두 상호운용성 작업을 진행 중이다.

## 2026년 4월 도입 현황

발표 1년 후 시점의 도입 현황은 다음과 같다.

- **클라우드 hyperscaler**: AWS, Azure, GCP 모두 native 지원. AWS Bedrock AgentCore Runtime은 A2A 게이트웨이를 기본 제공
- **엔터프라이즈 SaaS**: Salesforce Agentforce, ServiceNow Now Assist, SAP Joule, Workday Illuminate가 A2A 엔드포인트를 노출
- **오픈소스 framework**: LangGraph, CrewAI, AutoGen, ADK, Mastra, Pydantic AI가 A2A 어댑터를 1급 시민으로 제공
- **표준화**: Linux Foundation A2A Working Group이 격주 회의로 스펙을 진화. 2025-12에 v1.0, 2026-03에 v1.1(Signed Agent Card 강화) 릴리스

생태계 채택의 가속도는 MCP와 비슷하다. 2024-11 발표 후 1년 만에 표준이 된 MCP의 궤적을 A2A도 따르고 있다.

## 시리즈 로드맵

이 시리즈는 5편으로 구성된다.

1. **본 편 - 등장 배경**: 왜 표준이 필요한가, A2A의 비전과 다른 프로토콜과의 관계
2. [[a2a-02-specification|2편 - 스펙 분석]]: Agent Card, Task 라이프사이클, JSON-RPC 2.0, gRPC, SSE, 인증
3. [[a2a-03-vs-mcp|3편 - A2A vs MCP]]: 수직과 수평 통신의 직교성, 보완 패턴 코드 예제
4. [[a2a-04-python-sdk-tutorial|4편 - Python SDK 실전]]: a2a-sdk로 Researcher + Writer 협업 시스템 구현
5. [[a2a-05-adk-integration|5편 - ADK 통합과 보안]]: Google ADK 통합 패턴, X.509 서명, mTLS, OIDC, 프로덕션 배포

각 편은 독립적으로 읽을 수 있지만, 처음 보는 독자라면 순서대로 따라가는 것을 권장한다.

## 정리 + 다음 편

에이전트 framework 폭증은 통신 표준의 부재를 드러냈고, A2A는 HTTP가 웹을 만든 방식과 같은 비유로 이 문제를 풀려 한다. 핵심은 두 가지다.

- **트랜스포트 표준화**: 어떤 framework든 A2A 엔드포인트를 노출하면 다른 에이전트가 호출 가능
- **디스커버리 표준화**: Agent Card라는 JSON 문서로 능력을 광고

A2A는 MCP, AG-UI, AGNTCY와 경쟁하지 않고 스택의 다른 층을 담당한다. 2026년 시점 150+ 조직 프로덕션 도입과 hyperscaler 전면 지원으로 사실상 표준의 위치에 올랐다.

다음 [[a2a-02-specification|2편]]에서는 스펙 자체로 들어가 Agent Card의 JSON 스키마, Task 라이프사이클, JSON-RPC 2.0과 gRPC 트랜스포트, SSE 스트리밍, 인증 방식을 실제 페이로드 예시와 함께 분해한다.

## 관련 문서

- [[a2a|A2A Protocol]] - 본 시리즈가 속한 메인 엔트리
- [[mcp|MCP]] - Model Context Protocol, A2A와 보완 관계
- [[a2a-02-specification|A2A 스펙 분석]] - 다음 편
- [[a2a-03-vs-mcp|A2A vs MCP]] - 직교성 분석
- [[a2a-04-python-sdk-tutorial|A2A Python SDK 실전]] - 구현 튜토리얼
- [[a2a-05-adk-integration|ADK + A2A 통합]] - 프로덕션 배포
