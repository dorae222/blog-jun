<!-- infographic-hero -->
![AG-UI Protocol 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure: AG-UI Protocol 한 장 요약 인포그래픽*

# AG-UI Protocol: 에이전트와 사용자 인터페이스의 실시간 연결

**CopilotKit** · **2025-04-01** · **Agent Protocol** · **MIT**

## 개요

AG-UI는 에이전트와 사용자 인터페이스 사이의 이벤트 기반 통신을 표준화한다. MCP가 도구/데이터 접근을, A2A가 에이전트 간 Task 위임을 맡는다면, AG-UI는 사용자가 에이전트의 실행 과정을 보고 개입하는 마지막 인터랙션 계층이다.

![AG-UI 프로토콜 전체 아키텍처 - 에이전트 백엔드와 프론트엔드 UI 간 이벤트 기반 실시간 스트리밍 통신 구조](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 1: AG-UI 프로토콜 아키텍처 - 에이전트 상태 변화를 이벤트 스트림으로 프론트엔드에 전달한다. (Source: AG-UI docs 기반 자체 작성)*

![AG-UI 이벤트 타임라인](figures/event-timeline.svg?v=layout-20260706-fix2)

*Figure 2: AG-UI 이벤트 타임라인 - RUN_STARTED, TEXT_MESSAGE, TOOL_CALL, STATE_DELTA, INTERRUPT, RUN_FINISHED가 사용자 경험을 구성한다. (Source: AG-UI docs 기반 자체 작성)*

## 이벤트 중심으로 이해하기

AG-UI의 핵심은 텍스트 스트리밍만이 아니다. 에이전트의 tool call, reasoning, shared state update, human interrupt를 모두 이벤트로 표현한다. 따라서 UI는 단순 채팅창이 아니라 에이전트 작업 콘솔이 된다.

| 이벤트 축 | 의미 |
|-----------|------|
| Run lifecycle | 실행 시작/종료와 오류 |
| Messages | 텍스트 응답 스트리밍 |
| Tool calls | 도구 호출 시작, 인자, 결과 |
| State management | 상태 스냅샷과 delta |
| Interrupts | 사용자 승인, 추가 입력, 중단 요청 |

## MCP/A2A와의 조합

사용자는 AG-UI를 통해 Orchestrator의 상태를 본다. Orchestrator는 A2A로 전문 에이전트에게 Task를 보내고, 각 에이전트는 MCP로 도구와 데이터에 접근한다. AG-UI는 이 두 프로토콜의 내부 사건을 사용자에게 보여주는 표현 계층이다.

## 관련 문서

- [[agent-protocol-stack|에이전트 통신 표준 지도]]
- [[mcp|Model Context Protocol]]
- [[a2a|Agent-to-Agent Protocol]]

## 참고 자료

- [AG-UI docs](https://docs.ag-ui.com/)
