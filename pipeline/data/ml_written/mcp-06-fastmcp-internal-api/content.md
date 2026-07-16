<!-- infographic-hero -->
![MCP 서버 실전: FastMCP로 내부 API 감싸기 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: MCP 서버 실전: FastMCP로 내부 API 감싸기 한 장 요약. (Source: MCP/A2A/AG-UI 공식 문서 기반 자체 작성)*

# MCP 서버 실전: FastMCP로 내부 API 감싸기

MCP 서버의 첫 번째 좋은 대상은 이미 존재하는 내부 API다. REST API를 LLM이 직접 호출하게 하는 대신, MCP 서버가 스키마, 권한, 오류 처리, 감사 로그를 담당하게 만든다. 이 편에서는 FastMCP 스타일의 최소 구조를 기준으로 설계를 정리한다.

![FastMCP 내부 API wrapper 구조](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: FastMCP 내부 API wrapper 구조. 기존 내부 API를 MCP Server가 감싸고, Client는 Tools/Resources/Prompts로 일관되게 노출된 기능만 본다. (Source: MCP SDK 패턴 기반 자체 작성)*

## 프로젝트 구조

```text
internal_mcp/
├── server.py
├── clients/
│   └── ticket_api.py
├── prompts/
│   └── incident_summary.md
└── pyproject.toml
```

## Tool: 티켓 조회

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("internal-support")

@mcp.tool()
async def get_ticket(ticket_id: str) -> dict:
    """사내 지원 티켓을 조회한다."""
    ticket = await ticket_api.fetch(ticket_id, timeout=5)
    return {
        "id": ticket.id,
        "title": ticket.title,
        "status": ticket.status,
        "summary": ticket.summary,
    }
```

Tool은 모델이 호출할 수 있는 행동이다. 따라서 입력 검증과 timeout이 반드시 필요하다. 내부 API 에러는 그대로 traceback으로 넘기지 말고, 모델이 재시도하거나 사용자에게 설명할 수 있는 오류 메시지로 바꿔야 한다.

## Resource: 티켓 원문

```python
@mcp.resource("ticket://{ticket_id}/raw")
async def ticket_raw(ticket_id: str) -> str:
    """티켓 원문을 읽기 전용 리소스로 제공한다."""
    return await ticket_api.fetch_raw_markdown(ticket_id)
```

읽기 전용 데이터는 Tool보다 Resource가 자연스럽다. 모델은 필요한 경우 Resource URI를 읽고, Tool은 상태 변경이나 계산이 필요한 경우에만 쓴다.

## Prompt: 장애 보고서 템플릿

```python
@mcp.prompt()
def incident_summary(ticket_id: str) -> str:
    return f"""ticket://{ticket_id}/raw 를 읽고 다음 형식으로 정리하세요.
1. 영향 범위
2. 원인 후보
3. 즉시 조치
4. 재발 방지
"""
```

Prompt는 도메인 업무 형식을 서버가 제공하는 방법이다. 사내 운영팀이 원하는 장애 보고서 형식을 프롬프트로 고정하면, 각 클라이언트가 같은 방식으로 결과를 만든다.

## 운영 전환 체크리스트

| 항목 | 로컬 stdio | 원격 Streamable HTTP |
|------|------------|----------------------|
| 인증 | 로컬 사용자 권한 | OAuth/mTLS/API Gateway |
| 네트워크 | subprocess | `/mcp` endpoint |
| 보안 | filesystem root 제한 | Origin 검증, session 보호 |
| 로그 | stderr 또는 파일 | 중앙 로그/감사 로그 |
| 배포 | 개발자 머신 | Kubernetes/Cloud Run |

## 시리즈 정리

MCP는 개요, 서버 기능, 클라이언트 기능, transport, 보안, 구현을 함께 봐야 실무에 쓸 수 있다. 단순히 "도구를 붙인다"에서 끝나면 운영 경계가 흐려진다. 다음 단계는 A2A로 에이전트 간 Task 위임을 묶고, AG-UI로 사용자에게 과정을 보여주는 것이다.

## 내부 API를 MCP로 감쌀 때 실전에서 챙길 것

이 글의 코드는 최소 구조지만, 사내 API를 실제로 감쌀 때는 몇 가지 결정을 먼저 못박아야 한다.

첫째, 무엇을 Tool로 두고 무엇을 Resource로 둘지 나눈다. 상태를 바꾸거나 외부를 호출하는 등 부작용이 있는 액션은 Tool로, 읽기 전용 데이터는 Resource로 노출한다. 위 예제의 `get_ticket`은 모델이 호출하는 행동이라 Tool로, `ticket://{ticket_id}/raw`는 원문을 그대로 읽는 데이터라 Resource로 나눈 것이 이 기준이다. Tool/Resource/Prompt 각 primitive의 책임 구분은 [[mcp-02-server-features|MCP 서버 기능]]에서 정리한다.

둘째, 내부 API를 감쌀 때 실무에서 걸리는 지점은 대개 코드가 아니라 경계에 있다.

- 인증 전달: MCP 서버가 내부 API 앞단에 서므로, 호출자 신원을 내부 API가 요구하는 토큰으로 주입하거나 교환하는 경로를 서버가 책임진다. 도구 함수 안에서 이 토큰을 어떻게 받아 넘길지 미리 정한다.
- 에러와 timeout 매핑: 내부 API의 traceback을 그대로 넘기지 말고, 모델이 재시도하거나 사용자에게 설명할 수 있는 오류로 바꾼다. 위 `get_ticket`이 `timeout=5`를 건 것처럼 모든 외부 호출에 timeout을 걸어 무한 대기를 막는다.
- description 품질: tool의 docstring은 모델이 어떤 도구를 언제 부를지 판단하는 근거다. "사내 지원 티켓을 조회한다"처럼 무엇을 하는 도구인지 한 줄로 분명해야 모델 사용성이 올라간다.
- 위험한 엔드포인트 승인: 삭제나 상태 변경처럼 되돌리기 어려운 액션은 모든 endpoint를 무차별로 공개하지 말고, 승인 게이트를 두거나 별도 권한으로 분리한다.

이 인증, 권한, 감사 로그를 서버가 어디서 책임질지는 [[mcp-05-security-operations|MCP 보안과 운영]]에서 다룬다.

셋째, 개발은 로컬 stdio로 하고 원격 배포에서 전송을 바꾼다. 로컬에서는 subprocess로 붙는 stdio가 편하고, 원격에서는 `/mcp` endpoint를 통한 Streamable HTTP로 전환하면서 위 "운영 전환 체크리스트"의 인증, 보안, 로그, 배포 항목이 함께 바뀐다. 전송 방식별 차이와 전환 기준은 [[mcp-04-transports|MCP 전송]]에서 정리한다.

## 관련 문서

- [[mcp|MCP]] - 이 서버가 구현하는 에이전트-도구 수직 통신 표준
- [[mcp-01-overview|MCP 개요]] - 프로토콜 전체 그림과 구성 요소
- [[mcp-02-server-features|MCP 서버 기능]] - Tools/Resources/Prompts primitive의 책임 구분
- [[mcp-03-client-features|MCP 클라이언트 기능]] - 이 서버를 소비하는 클라이언트 쪽 동작
- [[mcp-04-transports|MCP 전송]] - 로컬 stdio와 원격 Streamable HTTP 전환
- [[mcp-05-security-operations|MCP 보안과 운영]] - 인증 전달, 권한, 감사 로그의 책임 경계
- [[agent-protocol-production-reference|Agent Protocol 종합 실전]] - 프로덕션 배포 관점의 종합 참고
- [[agent-protocol-stack|Agent Protocol Stack]] - MCP·A2A·AG-UI·AGNTCY 레이어 지도

## 참고 자료
- [MCP SDKs](https://github.com/modelcontextprotocol)
- [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
