<!-- infographic-hero -->
![MCP 스펙 분석: Tools, Resources, Prompts 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: MCP 스펙 분석: Tools, Resources, Prompts 한 장 요약. (Source: MCP/A2A/AG-UI 공식 문서 기반 자체 작성)*

# MCP 스펙 분석: Tools, Resources, Prompts

MCP 서버는 세 가지 기능을 제공한다. Tools는 모델이 실행할 수 있는 함수이고, Resources는 읽기 가능한 컨텍스트이며, Prompts는 재사용 가능한 작업 템플릿이다. 이 세 기능을 구분하지 않으면 모든 것을 Tool로 만들게 되고, 결과적으로 권한과 UX가 흐려진다.

![MCP 서버 기능 호출 흐름](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: MCP 서버 기능 호출 흐름. Client는 서버의 capability를 확인한 뒤 tools, resources, prompts 네임스페이스의 JSON-RPC 메서드를 호출한다. (Source: MCP server features docs 기반 자체 작성)*

:::info
MCP 서버의 세 primitive를 가르는 진짜 기준은 기능이 아니라 "누가 사용을 결정하는가"다. Tool은 모델이, Resource는 호스트 앱이, Prompt는 사용자가 사용 시점을 정한다. 이 제어 주체의 차이가 곧 권한 경계이자 UX 경계가 된다.
:::

이 글은 [[mcp-01-overview|MCP 개요]]에서 이어지는 서버 관점의 심층편이다. MCP를 처음 도입할 때 가장 흔한 실수는 노출하고 싶은 모든 것을 Tool 하나로 뭉치는 것이다. 그러면 스키마는 비대해지고, 무엇을 모델이 자율로 부르고 무엇을 사용자가 명시적으로 부르는지가 코드 어디에도 드러나지 않는다. 그래서 세 primitive를 제어 주체 기준으로 나눠 이해하는 것이 서버 설계의 출발점이다.

## Tools: 모델이 제어하는 실행 함수

Tool은 모델이 스스로 "지금 이걸 호출해야겠다"고 판단해 실행하는 함수다. 사용자가 직접 지시하지 않아도, 대화 맥락에서 필요하다고 판단하면 모델이 호출을 제안하고 호스트가 실행한다. 이 "모델이 제어한다(model-controlled)"는 점이 Tool의 정체성이다.

클라이언트는 `tools/list`로 서버가 노출한 도구 목록을 발견하고, 실제 실행은 `tools/call`로 한다. 각 Tool은 다음 필드로 정의된다.

- `name`: 도구 식별자. 모델이 호출 대상을 지정할 때 쓴다.
- `description`: 모델이 언제 이 도구를 써야 하는지 판단하는 근거. 자연어 설명이 곧 라우팅 힌트다.
- `inputSchema`: 입력 인자를 기술하는 JSON Schema. 모델이 인자를 채우고 호스트가 검증한다.
- `outputSchema`(선택): 구조화된 결과의 형태. 결과를 기계적으로 검증 가능하게 만든다.

예를 들어 고객 DB를 조회하는 도구는 다음처럼 정의한다.

```json
{
  "name": "query_customer_db",
  "description": "고객 데이터베이스에 읽기 전용 SQL을 실행하고 행을 반환한다",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sql": {
        "type": "string",
        "description": "실행할 SELECT 문 (읽기 전용)"
      },
      "limit": {
        "type": "integer",
        "description": "반환할 최대 행 수",
        "default": 100
      }
    },
    "required": ["sql"]
  }
}
```

`inputSchema`가 JSON Schema라는 점이 핵심이다. 모델은 이 스키마를 읽고 인자를 채우며, 호스트는 같은 스키마로 입력을 검증한 뒤에야 실제 함수를 실행한다. 스키마가 곧 계약이다.

Tool은 부작용(side effect)이 있는 액션에 쓴다. DB 쿼리, 파일 쓰기, 티켓 생성, 배포 트리거처럼 외부 상태를 바꾸거나 실행 비용이 드는 작업이 여기에 해당한다. 힘이 센 만큼 위험하다. 스펙은 Tool의 `annotations`(readOnlyHint, destructiveHint 같은 힌트)를 제공하지만, 동시에 이 annotation을 신뢰할 수 없는 정보로 취급하라고 명시한다. 즉 파괴적 작업에 대한 사용자 확인과 감사 로그는 annotation이 아니라 호스트가 강제해야 한다.

서버에서 Tool을 함수 데코레이터로 정의하고 스키마가 함수 시그니처에서 자동 생성되는 방식은 [[mcp-06-fastmcp-internal-api|FastMCP 내부 API]]에서 다룬다. 모델이 도구 호출을 어떻게 승인하고 표시하는지 클라이언트 쪽 흐름은 [[mcp-03-client-features|MCP Client Features]]를 참고한다.

## Resources: 앱이 제어하는 읽기 전용 컨텍스트

Resource는 모델에게 읽을거리를 제공하는 데이터다. Tool과 달리 부작용이 없고, 호출되어 무언가를 "실행"하지 않는다. 파일 내용, DB 스키마, API 응답 본문, 로그 조각처럼 맥락으로 넣을 정보를 담는다.

가장 큰 차이는 제어 주체다. Resource는 "앱이 제어한다(application-controlled)". 어떤 리소스를 실제로 모델의 컨텍스트에 넣을지는 모델이 아니라 호스트 애플리케이션(또는 그 뒤의 사용자)이 결정한다. 서버는 리소스를 제공하고, 앱은 그중 무엇을 언제 주입할지 고른다. 예를 들어 IDE형 클라이언트는 지금 열려 있는 파일만 컨텍스트에 넣고 나머지는 목록에만 노출할 수 있다.

각 Resource는 URI로 식별된다. `file://`, `https://`, `git://` 같은 표준 스킴을 쓰거나 `db://`, `log://` 같은 커스텀 스킴을 정의한다.

- `file:///repo/README.md` - 저장소 파일 내용
- `db://customers/schema` - 고객 테이블의 스키마 정의
- `https://internal.wiki/runbook/deploy` - 배포 런북 문서

클라이언트는 `resources/list`로 목록을, `resources/read`로 내용을 가져온다. 매번 전부 나열하기 어려운 동적 리소스는 `resources/templates/list`가 반환하는 URI 템플릿(예: `db://customers/{id}`)으로 표현한다. 데이터가 바뀌는 경우 `resources/subscribe`로 구독하면 서버가 변경 통지를 보낸다.

Resource 정의는 이렇게 생겼다.

```json
{
  "uri": "db://customers/schema",
  "name": "customer_schema",
  "title": "고객 테이블 스키마",
  "mimeType": "application/json"
}
```

Tool과 Resource의 경계가 헷갈릴 때는 부작용 여부로 가른다. 같은 데이터라도 "지금 조회를 실행"해야 하면 Tool이지만, 정적인 원문을 "맥락으로 첨부"하면 Resource다. Tool 결과가 `resource_link`를 반환해 "이 결과의 원문은 이 URI에 있다"고 가리킬 수도 있어, 둘은 종종 함께 쓰인다.

## Prompts: 사용자가 제어하는 재사용 템플릿

Prompt는 서버가 제공하는 재사용 가능한 프롬프트 템플릿이다. 세 primitive 중 유일하게 "사용자가 제어한다(user-controlled)". 모델이 알아서 부르지도, 앱이 배경에서 주입하지도 않는다. 사용자가 슬래시 커맨드나 메뉴에서 명시적으로 선택했을 때 실행된다.

클라이언트는 `prompts/list`로 사용 가능한 템플릿을, `prompts/get`으로 채워진 메시지를 받는다. 각 Prompt는 `arguments`로 파라미터화된다.

```json
{
  "name": "incident_report",
  "title": "장애 리포트 작성",
  "description": "로그와 영향 범위로 표준 장애 리포트를 생성한다",
  "arguments": [
    {
      "name": "service",
      "description": "장애가 발생한 서비스 이름",
      "required": true
    },
    {
      "name": "severity",
      "description": "심각도 (sev1~sev4)",
      "required": false
    }
  ]
}
```

사용자가 이 Prompt를 `/incident_report` 같은 슬래시 커맨드로 부르고 인자를 채우면, 서버는 `prompts/get`에 대한 응답으로 미리 설계된 메시지 묶음을 돌려준다. 이 메시지 안에 관련 Resource를 끼워 넣거나 특정 Tool 사용을 유도하는 지시를 담을 수 있다.

Prompt의 가치는 도메인 지식의 캡슐화에 있다. 고객 지원 요약, 코드 리뷰, 장애 리포트처럼 반복되는 작업에서 사용자가 매번 긴 지시문을 다시 쓰지 않게 한다. 서버가 "이 도구와 리소스를 이렇게 조합하라"는 업무 형식을 템플릿으로 배포하는 셈이라, MCP 서버는 단순 API 래퍼를 넘어 업무 패턴 라이브러리가 된다.

## 제어 주체가 다르다: 세 primitive의 핵심 대비

세 primitive는 기능이 아니라 "누가 사용을 결정하는가"로 갈린다. 이 축을 놓치면 세 기능이 전부 Tool로 수렴하고, 권한 경계와 UX 진입점이 한 덩어리로 뭉개진다.

| primitive | 제어 주체 | 사용 시점 결정 | 부작용 | 대표 예시 |
|-----------|-----------|----------------|--------|-----------|
| Tools | 모델 (model-controlled) | 모델이 맥락 보고 판단 | 있음 | DB 쓰기, 파일 생성, 배포 |
| Resources | 앱 (application-controlled) | 호스트 앱이 주입 결정 | 없음 (읽기) | 파일 내용, DB 스키마 |
| Prompts | 사용자 (user-controlled) | 사용자가 명시적 호출 | 템플릿 자체는 없음 | 슬래시 커맨드 템플릿 |

이 구분이 곧 권한 설계다. 모델이 자율적으로 부르는 Tool은 가장 엄격한 승인과 감사의 대상이고, 앱이 고르는 Resource는 컨텍스트 노출 정책의 대상이며, 사용자가 부르는 Prompt는 UX 진입점이다. 세 축을 섞으면 "누가 이걸 실행했는가"를 로그로 설명하기 어려워진다.

## 실무: 무엇을 Tool로 두고 무엇을 Resource로 노출할까

새 서버를 설계할 때 가장 먼저 답할 질문은 "이 기능이 상태를 바꾸는가"다. 아래 기준으로 primitive를 배치하면 대부분의 모호함이 사라진다.

| 질문 | 배치 |
|------|------|
| 모델이 외부 상태를 바꾸거나 실행해야 하는가 | Tool |
| 모델이 읽기만 할 맥락 데이터인가 | Resource |
| 사용자가 반복적으로 부르는 작업 형식인가 | Prompt |
| 결과가 구조화되어 검증되어야 하는가 | Tool + outputSchema |
| 데이터가 계속 바뀌는가 | Resource subscription 또는 listChanged 통지 |

몇 가지 실무 판단 기준을 덧붙인다.

- **읽기 조회는 기본적으로 Resource, 단 "실행"의 의미가 있으면 Tool**. 정적인 파일과 스키마는 Resource가 맞다. 그러나 "지금 이 파라미터로 검색을 수행"하는 것처럼 매번 계산이 필요하면 Tool이 낫다.
- **부작용이 있으면 무조건 Tool**. 쓰기, 삭제, 전송, 결제처럼 되돌리기 어려운 작업을 Resource로 위장하면 안 된다. 명시적 Tool로 두고 승인 플로우를 건다.
- **반복 업무 형식은 코드가 아니라 Prompt로**. 프롬프트 문자열을 클라이언트 코드에 하드코딩하면 재사용과 버전관리가 어렵다. 서버 Prompt로 올리면 여러 클라이언트가 같은 템플릿을 공유한다.
- **스키마에 실패 메시지와 권한 범위를 함께 설계**. `inputSchema`는 입력 검증만이 아니라 "이 도구가 무엇을 할 수 있는지"의 경계 문서이기도 하다.

흔한 실패 패턴은 대부분 경계가 흐린 데서 온다. 모든 것을 Tool 하나로 몰아 스키마가 비대해지거나, 같은 데이터를 Resource와 Tool이 서로 다르게 표현하거나, Prompt 템플릿이 코드 곳곳에 흩어져 재사용이 안 되는 경우다. 셋 다 기술 선택의 문제가 아니라 제어 주체를 먼저 정하지 않아 생긴다. 그래서 새 기능을 붙일 때마다 "이건 모델이 부를 것인가, 앱이 넣을 것인가, 사용자가 부를 것인가"를 먼저 답하는 습관이 서버 품질을 좌우한다.

서버의 세 primitive를 실제 함수와 데코레이터로 구현하는 방법은 [[mcp-06-fastmcp-internal-api|FastMCP 내부 API]]에서, 이 기능들을 소비하는 클라이언트 쪽(Roots, Sampling, Elicitation)은 [[mcp-03-client-features|MCP Client Features]]에서 이어진다. 전송 계층과 보안·운영은 각각 [[mcp-04-transports|MCP 전송 계층]]과 [[mcp-05-security-operations|MCP 보안과 운영]]을 참고한다. MCP가 담당하는 수직(도구) 통신과 A2A의 수평(에이전트) 통신이 어떻게 직교하는지는 [[a2a-03-vs-mcp|A2A vs MCP]]에서 다룬다.

## 참고 자료
- [MCP Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [MCP Resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources)
- [MCP Prompts](https://modelcontextprotocol.io/specification/2025-11-25/server/prompts)

## 관련 문서

- [[mcp-01-overview|MCP 개요]] - 시리즈 출발점, MCP가 푸는 문제
- [[mcp-03-client-features|MCP Client Features]] - 클라이언트가 노출하는 Roots·Sampling·Elicitation
- [[mcp-04-transports|MCP 전송 계층]] - stdio·HTTP·SSE 트랜스포트
- [[mcp-05-security-operations|MCP 보안과 운영]] - 권한·감사·프로덕션 운영
- [[mcp-06-fastmcp-internal-api|FastMCP 내부 API]] - 세 primitive 구현 방법
- [[a2a-03-vs-mcp|A2A vs MCP]] - 수직(도구)과 수평(에이전트) 통신의 직교성
- [[agent-protocol-stack|Agent Protocol Stack]] - MCP·A2A·AG-UI·AGNTCY 레이어 지도
- [[ai-agent-technology-guide|AI Agent 기술 지도]] - 에이전트 기술 전반 개관
