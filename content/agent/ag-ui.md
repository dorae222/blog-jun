---
title: "AG-UI Protocol: AI 에이전트 프레임워크"
slug: "ag-ui"
category: agent
tags: ["Agent-UI", "AG-UI Protocol", "CopilotKit", "Streaming Protocol"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.098372+00:00"
architecture_entry: "ag-ui"
---

# AG-UI Protocol: 에이전트와 사용자 인터페이스의 실시간 연결

**CopilotKit** · **2025-04-01** · **Agent Protocol** · **MIT**

## 개요

AG-UI(Agent-User Interface) 프로토콜은 AI 에이전트와 프론트엔드 UI 간의 실시간 스트리밍 통신을 표준화하는 오픈 프로토콜이다. CopilotKit이 2025년 4월 공개한 AG-UI는 에이전트 생태계에서 "마지막 1마일(last mile)"에 해당하는 에이전트-사용자 간 인터페이스 문제를 해결한다. MCP가 에이전트-도구 통신을, A2A가 에이전트 간 통신을 표준화한 것과 달리, AG-UI는 에이전트의 내부 동작을 사용자에게 투명하게 전달하는 프레젠테이션 레이어에 집중한다.

기존의 AI 챗봇 인터페이스는 에이전트가 작업을 수행하는 동안 "생각하는 중..."이라는 단순 메시지만 표시했다. 이는 사용자 입장에서 블랙박스나 다름없었다. AG-UI는 에이전트의 사고 과정, 도구 호출 상태, 중간 결과물을 실시간으로 스트리밍함으로써, 사용자가 에이전트의 작업 과정을 단계별로 관찰하고 필요한 시점에 개입할 수 있는 인터랙티브한 경험을 제공한다.

에이전트 투명성(agent transparency)은 단순한 UX 개선을 넘어 규제 요건과도 밀접하다. EU AI Act 등 AI 규제가 강화되면서, AI 시스템의 의사결정 과정을 설명할 수 있는 능력이 필수 요건이 되고 있다. AG-UI는 이러한 설명 가능성(explainability)을 프로토콜 수준에서 지원한다. MIT 라이선스로 공개되어 있으며, TypeScript와 Python SDK가 제공된다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

AG-UI는 이벤트 기반 스트리밍 프로토콜로 설계되었다. 에이전트 실행 중 발생하는 모든 상태 변화가 정형화된 이벤트(Event) 객체로 변환되어 프론트엔드에 전달된다.

### 이벤트 타입 체계

AG-UI는 다음과 같은 핵심 이벤트 타입을 정의한다.

| 이벤트 카테고리 | 이벤트 타입 | 설명 |
|---------------|-----------|------|
| 텍스트 메시지 | `TEXT_MESSAGE_START` | 텍스트 스트리밍 시작 |
| | `TEXT_MESSAGE_CONTENT` | 텍스트 청크 전송 |
| | `TEXT_MESSAGE_END` | 텍스트 스트리밍 완료 |
| 도구 호출 | `TOOL_CALL_START` | 도구 호출 시작 (도구명, ID) |
| | `TOOL_CALL_ARGS` | 도구 호출 인수 스트리밍 |
| | `TOOL_CALL_END` | 도구 호출 완료 |
| 상태 관리 | `STATE_SNAPSHOT` | 전체 상태 스냅샷 |
| | `STATE_DELTA` | 상태 변경분 (JSON Patch) |
| 워크플로 | `STEP_STARTED` | 다단계 작업의 단계 시작 |
| | `STEP_FINISHED` | 다단계 작업의 단계 완료 |
| 실행 제어 | `RUN_STARTED` | 에이전트 실행 시작 |
| | `RUN_FINISHED` | 에이전트 실행 완료 |
| 확장 | `CUSTOM` | 사용자 정의 이벤트 |

### 프로토콜 흐름

프론트엔드가 에이전트에 `/run` 엔드포인트로 요청을 보내면, 에이전트는 SSE(Server-Sent Events) 연결을 통해 이벤트 스트림을 반환한다.

```
사용자 UI (React)                        AG-UI 에이전트
    |                                        |
    |-- POST /run (메시지+상태) ------------→|
    |                                        |
    |←-- SSE: RUN_STARTED ------------------|
    |←-- SSE: TEXT_MESSAGE_START ------------|
    |←-- SSE: TEXT_MESSAGE_CONTENT ----------|
    |←-- SSE: TOOL_CALL_START (검색 도구) ---|
    |←-- SSE: TOOL_CALL_ARGS ----------------|
    |←-- SSE: TOOL_CALL_END -----------------|
    |←-- SSE: STATE_DELTA -------------------|
    |←-- SSE: TEXT_MESSAGE_CONTENT ----------|
    |←-- SSE: TEXT_MESSAGE_END --------------|
    |←-- SSE: RUN_FINISHED ------------------|
```

### 공유 상태(Shared State) 관리

AG-UI의 가장 강력한 기능 중 하나는 에이전트와 UI 간의 상태 동기화다. `STATE_SNAPSHOT` 이벤트는 에이전트의 전체 상태를 JSON으로 전달하고, `STATE_DELTA` 이벤트는 JSON Patch(RFC 6902) 형식으로 변경분만 전달한다.

```typescript
// React 컴포넌트에서 AG-UI 이벤트 처리
import { useAgentStream } from '@ag-ui/react';

function AgentDashboard() {
  const { messages, toolCalls, state, isRunning } = useAgentStream({
    agentUrl: 'https://agent.example.com',
    onStateChange: (delta) => {
      // 에이전트가 업데이트한 상태를 UI에 즉시 반영
      updateLocalState(delta);
    }
  });

  return (
    <div>
      {toolCalls.map(tc => (
        <ToolCallVisualization key={tc.id} call={tc} />
      ))}
      <StateInspector state={state} />
    </div>
  );
}
```

이를 통해 에이전트가 수정한 데이터(예: 스프레드시트 셀, 문서 내용)가 UI에 즉시 반영되는 양방향 상태 관리가 가능하다.

### Human-in-the-Loop 지원

AG-UI는 에이전트가 사용자의 확인이나 입력을 요청하는 Human Intervention Request 이벤트를 지원한다. 민감한 작업 전 사용자 승인을 받거나, 모호한 지시에 대한 명확화를 요청하는 등 안전한 에이전트 운영을 위한 메커니즘이다.

### 프레임워크 어댑터

LangGraph, CrewAI, AutoGen, Mastra 등 주요 에이전트 프레임워크와의 어댑터가 제공되어, 기존 에이전트 코드에 최소한의 변경으로 AG-UI 프로토콜을 적용할 수 있다.

## 핵심 혁신

1. **에이전트 투명성(Agent Transparency)**: 에이전트의 "블랙박스" 문제를 해결한다. 사용자는 에이전트가 어떤 도구를 호출하고, 어떤 데이터를 참조하며, 어떤 과정을 거쳐 결론에 도달했는지를 실시간으로 확인할 수 있다. 이는 AI 시스템에 대한 사용자 신뢰 구축의 핵심이다.

2. **공유 상태(Shared State) 관리**: `STATE_SNAPSHOT`과 `STATE_DELTA` 이벤트를 통해 에이전트와 UI가 동일한 상태를 공유하고 동기화한다. 상태 변경은 JSON Patch 형식으로 전달되어 대역폭 효율성을 유지한다.

3. **프레임워크 독립적 설계**: AG-UI는 특정 에이전트 프레임워크에 종속되지 않는 프로토콜 수준의 표준이다. 어떤 백엔드 프레임워크로 에이전트를 구축하든, AG-UI 이벤트를 생성하기만 하면 동일한 프론트엔드 컴포넌트를 사용할 수 있다.

4. **세 계층 표준 완성**: MCP(에이전트-도구), A2A(에이전트-에이전트), AG-UI(에이전트-사용자)가 함께 에이전트 생태계의 전체 통신 스택을 표준화한다. 이 세 프로토콜의 조합은 에이전트 시스템 구축의 표준 아키텍처가 되고 있다.

## 벤치마크/성능

| 측면 | AG-UI | Vercel AI SDK | Streamlit | Gradio |
|------|-------|---------------|-----------|--------|
| 통신 방식 | 이벤트 기반 SSE | 스트리밍 텍스트 | 위젯 렌더링 | 컴포넌트 |
| 에이전트 지원 | 다중 프레임워크 | Vercel 생태계 | 제한적 | 제한적 |
| 상태 관리 | 공유 상태 (JSON Patch) | 서버 상태 | 세션 상태 | 세션 상태 |
| 도구 호출 시각화 | 네이티브 지원 | 커스텀 필요 | 미지원 | 미지원 |
| Human-in-the-Loop | 프로토콜 내장 | 커스텀 필요 | 위젯 기반 | 콜백 |
| 실시간 스트리밍 | 세분화된 이벤트 | 텍스트 청크 | 전체 리렌더 | 전체 리렌더 |

## 구현

AG-UI의 에이전트 서버 구현 예시(Python):

```python
from ag_ui.server import AGUIServer
from ag_ui.events import (
    TextMessageStart, TextMessageContent, TextMessageEnd,
    ToolCallStart, ToolCallEnd, RunFinished
)

async def agent_handler(request):
    yield TextMessageStart(message_id="msg-1")
    yield TextMessageContent(message_id="msg-1", delta="분석을 시작합니다.")
    
    # 도구 호출 시각화
    yield ToolCallStart(tool_call_id="tc-1", tool_name="web_search")
    result = await search(request.query)
    yield ToolCallEnd(tool_call_id="tc-1", result=result)
    
    yield TextMessageContent(message_id="msg-1", delta=f"검색 결과: {result}")
    yield TextMessageEnd(message_id="msg-1")
    yield RunFinished()

server = AGUIServer(handler=agent_handler)
server.run(port=8000)
```

## 관련 모델

AG-UI는 MCP와 A2A에서 영감을 받아 에이전트 통신의 마지막 계층인 UI 통신을 표준화한다. CopilotKit의 React 컴포넌트 라이브러리와 긴밀하게 통합되어 있으며, 수 줄의 코드로 에이전트 기반 Copilot UI를 기존 React 애플리케이션에 임베딩할 수 있다.

## 참고 자료

- [AG-UI GitHub Repository](https://github.com/CopilotKit/ag-ui)
- [AG-UI Protocol Specification](https://docs.ag-ui.com)
- [CopilotKit Documentation](https://docs.copilotkit.ai)

## 관련 문서

- [[a2a|Agent-to-Agent Protocol]] — 영감
- [[mcp|Model Context Protocol]] — 영감
