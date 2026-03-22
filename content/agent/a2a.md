---
title: "Agent-to-Agent Protocol: AI 에이전트 프레임워크"
slug: a2a
category: agent
tags: ["Agent Communication", "Agent-to-Agent Protocol", "Google", "Interoperability", "Protocol"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.088357+00:00"
architecture_entry: a2a
---

# Agent-to-Agent Protocol: AI 에이전트 간 통신의 표준

**Google** · **2025-04-09** · **Agent Protocol** · **Apache-2.0**

## 개요

Agent-to-Agent(A2A) 프로토콜은 서로 다른 프레임워크나 벤더로 구축된 AI 에이전트들이 직접 통신하고 협업할 수 있게 하는 오픈 표준이다. Google이 2025년 4월 발표한 A2A는 AI 에이전트 생태계에서 에이전트 간 상호운용성(interoperability)이라는 핵심 과제를 해결하기 위해 설계되었다. Anthropic의 MCP(Model Context Protocol)가 에이전트와 도구 간의 통신을 표준화했다면, A2A는 에이전트와 에이전트 사이의 통신을 표준화하는 상호 보완적 프로토콜이다.

A2A의 핵심 가치는 벤더 종속성 탈피에 있다. 기존에는 LangChain으로 구축된 에이전트가 AutoGen 에이전트와 협업하려면 커스텀 통합 코드를 작성해야 했다. $M$개의 에이전트 프레임워크와 $N$개의 에이전트가 있을 때, 모든 조합을 연결하려면 $M \times N$개의 커스텀 통합이 필요했다. A2A는 이 문제를 표준 프로토콜로 해결하여 $M + N$개의 구현만으로 모든 조합의 통신을 가능하게 한다. Google, Atlassian, Salesforce, SAP, ServiceNow 등 50개 이상의 기업이 초기 파트너로 참여했으며, 이는 업계 전반의 표준화 요구를 반영한다.

에이전트 생태계는 세 가지 통신 계층으로 구성된다. 에이전트-도구(MCP), 에이전트-에이전트(A2A), 에이전트-사용자(AG-UI)가 그것이다. A2A는 이 중 가장 복잡한 에이전트 간 협업 문제를 다루며, 이기종 에이전트 시스템의 통합이라는 엔터프라이즈 핵심 과제를 해결한다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

A2A 프로토콜의 아키텍처는 네 가지 핵심 개념을 중심으로 설계되었다.

### Agent Card

각 에이전트는 자신의 역량, 입출력 스키마, 엔드포인트 URL을 JSON 형태의 Agent Card로 광고(advertise)한다. Agent Card는 `/.well-known/agent.json` 경로에 호스팅되며, 다음과 같은 정보를 포함한다.

```json
{
  "name": "research-agent",
  "description": "학술 논문 검색 및 요약 에이전트",
  "url": "https://research-agent.example.com",
  "capabilities": {
    "input": ["text/plain", "application/json"],
    "output": ["text/plain", "application/pdf"],
    "streaming": true
  },
  "authentication": {
    "type": "oauth2",
    "token_url": "https://auth.example.com/token"
  },
  "skills": [
    {"name": "paper_search", "description": "arXiv/Semantic Scholar 논문 검색"},
    {"name": "summarize", "description": "논문 핵심 요약 생성"}
  ]
}
```

이는 웹의 `robots.txt`나 `/.well-known/openid-configuration`과 유사한 발견(discovery) 메커니즘을 제공하여, DNS나 별도의 서비스 레지스트리 없이도 에이전트를 발견할 수 있다.

### Task

A2A에서 모든 작업의 기본 단위다. 클라이언트 에이전트가 원격 에이전트에 Task를 생성하면, 해당 Task는 상태 전이 머신으로 관리된다.

$$\text{submitted} \rightarrow \text{working} \rightarrow \begin{cases} \text{completed} \\ \text{failed} \\ \text{canceled} \\ \text{input-required} \end{cases}$$

Task ID를 통해 비동기적으로 진행 상황을 추적할 수 있으며, `input-required` 상태는 원격 에이전트가 추가 정보를 요청할 때 사용된다.

### Message와 Part

Task 내의 통신은 Message 객체로 이루어지며, 각 Message는 하나 이상의 Part를 포함한다.

| Part 타입 | 설명 | 예시 |
|----------|------|------|
| `TextPart` | 일반 텍스트 | 분석 요청, 질의 |
| `FilePart` | 파일 (인라인 또는 URI) | PDF 보고서, 이미지 |
| `DataPart` | 구조화된 JSON 데이터 | API 응답, 메타데이터 |

이를 통해 텍스트뿐 아니라 파일, 구조화된 데이터 등 다양한 형태의 정보를 교환할 수 있다.

### Artifact

에이전트가 작업 결과로 생성한 산출물을 나타낸다. 보고서, 코드 파일, 이미지 등 최종 결과물이 Artifact로 반환되며, 각 Artifact는 MIME 타입과 메타데이터를 포함한다.

### 통신 프로토콜

통신은 HTTP 위에서 JSON-RPC 2.0 프로토콜을 사용하며, 실시간 스트리밍이 필요한 경우 SSE(Server-Sent Events)를 통해 중간 결과를 전송한다.

```
클라이언트 에이전트                       원격 에이전트
     |                                      |
     |-- GET /.well-known/agent.json ------→|
     |←-- Agent Card (역량·스키마) ---------|
     |                                      |
     |-- POST /tasks (JSON-RPC) ----------→|
     |←-- Task ID + status: working -------|
     |←-- SSE: 중간 결과 스트리밍 ---------|
     |←-- SSE: status: completed ----------|
     |←-- Artifact (결과물) ---------------|
```

이 설계를 통해 기존 웹 인프라(로드 밸런서, API 게이트웨이, 인증 시스템, 방화벽)를 그대로 활용할 수 있다. 새로운 전송 프로토콜을 도입하지 않고 HTTP/JSON이라는 검증된 기술 위에 구축했다는 점이 실무 도입 장벽을 크게 낮춘다.

## 핵심 혁신

1. **Agent Card 기반 발견 메커니즘**: DNS나 서비스 레지스트리 없이도 에이전트를 발견할 수 있는 경량 메커니즘을 제공한다. 웹 표준(`.well-known`)을 활용하여 기존 인프라와의 호환성을 극대화했다. 에이전트 마켓플레이스나 디렉토리 서비스 구축의 기반이 된다.

2. **비동기 우선 설계**: 에이전트 작업은 수초에서 수시간까지 소요될 수 있으므로, 비동기 Task 관리를 기본으로 설계했다. 폴링(polling), 웹훅(webhook), SSE(Server-Sent Events) 등 다양한 비동기 패턴을 지원하여 작업 특성에 맞는 최적의 방식을 선택할 수 있다.

3. **MCP와의 상호 보완성**: A2A는 에이전트 간 통신을, MCP는 에이전트와 도구 간 통신을 각각 담당한다. 하나의 에이전트 시스템 내에서 두 프로토콜이 함께 동작하는 아키텍처가 표준 패턴으로 권장된다. 예를 들어, 오케스트레이터 에이전트가 A2A로 전문 에이전트에 작업을 위임하고, 각 전문 에이전트는 MCP로 도구에 접근한다.

4. **이기종 에이전트 생태계 지원**: Python, JavaScript, Java 등 다양한 언어와 프레임워크로 구축된 에이전트가 동일한 프로토콜로 통신할 수 있어, 기업 환경에서 점진적 에이전트 도입이 가능하다. LangChain 에이전트, AutoGen 에이전트, CrewAI 크루가 A2A를 통해 단일 워크플로에서 협업할 수 있다.

## 벤치마크/성능

| 프로토콜 | 통신 대상 | 제공자 | 발표 시기 | 전송 계층 | 상태 관리 |
|---------|----------|--------|----------|----------|----------|
| **A2A** | 에이전트 ↔ 에이전트 | Google | 2025.04 | HTTP + JSON-RPC | Task 상태 머신 |
| **MCP** | 에이전트 ↔ 도구 | Anthropic | 2024.11 | stdio / SSE | 세션 기반 |
| **AG-UI** | 에이전트 ↔ UI | CopilotKit | 2025.04 | 이벤트 스트림 | 공유 상태 |

A2A, MCP, AG-UI는 각각 에이전트 생태계의 서로 다른 통신 계층을 표준화한다. 세 프로토콜을 함께 사용하면 에이전트가 도구에 접근하고(MCP), 다른 에이전트와 협업하며(A2A), 사용자에게 결과를 실시간으로 표시하는(AG-UI) 전체 스택을 표준화된 인터페이스로 구성할 수 있다.

## 구현

A2A의 레퍼런스 구현은 Python과 JavaScript SDK로 제공된다. 최소한의 서버 구현 예시는 다음과 같다.

```python
from a2a.server import A2AServer
from a2a.types import AgentCard, Skill

# Agent Card 정의
card = AgentCard(
    name="data-analyst",
    description="데이터 분석 및 시각화 에이전트",
    skills=[
        Skill(name="analyze", description="CSV 데이터 분석"),
        Skill(name="visualize", description="차트 생성")
    ]
)

# 태스크 핸들러
async def handle_task(task):
    # 작업 처리 로직
    result = await analyze_data(task.messages[-1])
    return task.complete(artifacts=[result])

server = A2AServer(card=card, handler=handle_task)
server.run(port=8080)
```

클라이언트 측에서 원격 에이전트를 호출하는 코드도 간결하다.

```python
from a2a.client import A2AClient

client = A2AClient("https://data-analyst.example.com")
card = await client.get_agent_card()
task = await client.create_task(
    message="2024년 매출 데이터를 분석해주세요",
    files=["sales_2024.csv"]
)

async for event in client.stream_task(task.id):
    print(f"상태: {event.status}, 결과: {event.data}")
```

## 관련 모델

A2A는 MCP(에이전트-도구 표준)에서 영감을 받아 에이전트-에이전트 계층으로 확장한 프로토콜이다. AG-UI(에이전트-사용자 표준)와 함께 에이전트 통신의 세 축을 구성한다. 기존의 독자적 에이전트 간 통신 방식(LangChain의 Agent Protocol, AutoGen의 메시지 패싱)을 표준화된 단일 프로토콜로 통합하려는 시도다.

## 참고 자료

- [A2A GitHub Repository](https://github.com/google/A2A)
- [Google Cloud Blog: A2A Protocol Announcement](https://cloud.google.com/blog/products/ai-machine-learning/a2a-a-new-era-of-agent-interoperability)

## 관련 문서

- [[mcp|Model Context Protocol]] — 영감
- [[ag-ui|AG-UI Protocol]] — 영감을 줌
