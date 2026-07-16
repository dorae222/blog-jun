---
title: "Model Context Protocol: AI 에이전트 프레임워크"
slug: mcp
category: agent
tags: ["Anthropic", "Model Context Protocol", "Protocol", "Standardization", "Tool Interface"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.000000+00:00"
architecture_entry: mcp
---

<!-- infographic-hero -->
![Model Context Protocol 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure: Model Context Protocol 한 장 요약 인포그래픽*

# Model Context Protocol: AI 에이전트 생태계의 USB-C 표준

**Anthropic** · **2024-11-25** · **Agent Protocol** · **MIT** · **Spec 2025-11-25 기준**

## 개요

Model Context Protocol(MCP)은 LLM 애플리케이션이 외부 도구, 리소스, 프롬프트와 통신하는 방식을 표준화한다. 2025-11-25 최신 스펙 기준 MCP는 Host, Client, Server의 삼중 구조와 JSON-RPC 2.0 메시지, 상태 있는 연결, capability negotiation을 핵심으로 둔다.

![MCP 프로토콜 아키텍처 - Host, Client, Server 삼중 구조의 LLM-도구 통신 표준](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 1: MCP 아키텍처 - Host가 Client를 통해 MCP Server와 JSON-RPC 기반으로 통신하며, Tools·Resources·Prompts를 표준화한다. (Source: MCP specification 기반 자체 작성)*

## 스펙 기준으로 다시 보기

| 축 | 내용 |
|----|------|
| Base protocol | JSON-RPC 2.0, stateful connection, capability negotiation |
| Server features | Tools, Resources, Prompts |
| Client features | Roots, Sampling, Elicitation |
| Transport | stdio, Streamable HTTP |
| Security | user consent, data privacy, tool safety, sampling controls |

기존 MCP 설명은 Tools 중심으로 단순화되기 쉽다. 하지만 최신 스펙에서 중요한 변화는 클라이언트 기능과 transport 보안까지 함께 봐야 한다는 점이다. 서버는 Tools를 제공할 뿐 아니라, 클라이언트에 Roots, Sampling, Elicitation을 요청할 수 있다. 또한 원격 서버는 Streamable HTTP endpoint에서 Origin 검증, 인증, 세션 관리를 갖춰야 한다.

## MCP 시리즈

- [[mcp-01-overview|MCP 개요: AI 앱을 위한 USB-C 표준]]
- [[mcp-02-server-features|MCP 스펙 분석: Tools, Resources, Prompts]]
- [[mcp-03-client-features|MCP Client Features: Roots, Sampling, Elicitation]]
- [[mcp-04-transports|MCP Transport: stdio vs Streamable HTTP]]
- [[mcp-05-security-operations|MCP 보안과 운영]]
- [[mcp-06-fastmcp-internal-api|MCP 서버 실전: FastMCP로 내부 API 감싸기]]

## 관련 문서

- [[agent-protocol-stack|에이전트 통신 표준 지도]]
- [[a2a|Agent-to-Agent Protocol]]
- [[ag-ui|AG-UI Protocol]]

## 참고 자료

- [MCP specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
