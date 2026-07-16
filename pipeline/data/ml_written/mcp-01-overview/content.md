<!-- infographic-hero -->
![MCP 개요: AI 앱을 위한 USB-C 표준 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: MCP 개요: AI 앱을 위한 USB-C 표준 한 장 요약. (Source: MCP/A2A/AG-UI 공식 문서 기반 자체 작성)*

# MCP 개요: AI 앱을 위한 USB-C 표준

MCP(Model Context Protocol)는 LLM 애플리케이션이 외부 도구와 데이터에 접근하는 방식을 표준화한다. 공식 스펙은 통신 주체를 Host, Client, Server로 나눈다. Host는 Claude Desktop, IDE, 에이전트 런타임처럼 연결을 시작하는 애플리케이션이고, Client는 Host 안에서 특정 MCP Server와 연결되는 커넥터이며, Server는 도구와 리소스를 제공하는 독립 프로세스다.

![MCP Host Client Server 구조](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: MCP Host/Client/Server 구조. Host는 사용자와 모델을 품고, Client는 서버별 세션을 관리하며, Server는 Tools·Resources·Prompts를 제공한다. (Source: MCP specification 기반 자체 작성)*

## 왜 MCP인가: M×N 통합 문제

MCP가 없던 시절, LLM 앱이 외부 세계와 연결되는 방식은 매번 손으로 짠 어댑터였다. GitHub를 붙이려면 GitHub 전용 통합 코드를, Slack을 붙이려면 Slack 전용 코드를, 사내 PostgreSQL을 붙이려면 또 다른 코드를 작성했다. 앱이 M개이고 붙일 도구가 N개라면 조합은 M x N으로 불어난다. 새 앱이 하나 등장할 때마다 기존 모든 도구에 대한 통합을 다시 작성해야 했고, 도구 하나가 인터페이스를 바꾸면 그 도구를 쓰던 모든 앱을 손봐야 했다.

MCP는 이 문제를 규격을 하나로 통일해서 푼다. 도구 쪽은 MCP Server를 한 번 구현해 능력을 노출하고, 앱 쪽은 MCP Client로 그 규격을 공통 해석한다. 그러면 통합 표면은 M x N에서 M + N에 가까워진다. 도구 제공자는 서버 하나만 관리하면 어떤 MCP 호환 앱과도 연결되고, 앱 개발자는 클라이언트 한 벌로 임의의 MCP 서버를 받아들인다.

이것이 "AI 앱을 위한 USB-C" 비유의 핵심이다. USB-C 이전에는 기기마다 전용 케이블과 포트가 있었지만, USB-C는 하나의 물리 규격으로 노트북, 모니터, 저장장치, 충전기를 임의로 연결한다. 케이블은 어느 쪽에 무엇이 붙었는지 신경 쓰지 않는다. MCP도 마찬가지로 임의의 Host와 임의의 Server를 같은 규격 위에서 연결한다. 중요한 점은 MCP가 "도구 호출 라이브러리"가 아니라 프로토콜이라는 것이다. 어떤 모델을 쓰는지, 서버가 어떤 언어로 작성됐는지는 MCP의 핵심 관심사가 아니다.

## 참여자 구조: Host, Client, Server

MCP 통신은 세 주체로 구성되고, 각자의 책임이 분명하게 나뉜다.

- **Host**: 사용자와 모델을 품는 LLM 애플리케이션이다. Claude Desktop, IDE 확장, 에이전트 런타임처럼 연결을 시작하고 사용자 경험을 책임지는 쪽이다. 여러 서버에 동시에 연결할 수 있다.
- **Client**: Host 안에서 하나의 Server와 1:1로 짝지어지는 커넥터다. Host가 세 개의 서버에 연결한다면 그 안에는 세 개의 Client 세션이 존재한다. Client는 자신이 담당하는 서버와의 메시지 교환, 상태, 권한 경계를 격리해서 관리한다.
- **Server**: 능력을 노출하는 독립 프로세스다. 파일 시스템 접근, 데이터베이스 조회, 외부 API 호출 같은 기능을 표준 인터페이스로 제공한다. 사용자 기기의 로컬 프로세스일 수도 있고 원격 서비스일 수도 있다.

세 주체는 JSON-RPC 2.0 메시지로 대화한다. 요청(request), 응답(response), 알림(notification)이라는 JSON-RPC의 기본 구조 위에서 `tools/list`, `tools/call`, `resources/read`, `prompts/get` 같은 메서드가 오간다. 덕분에 구현 언어와 무관하게 동일한 메시지 규약을 공유한다. 이 메시지가 실제로 어떤 트랜스포트를 타고 흐르는지는 [[mcp-04-transports|MCP Transport]]에서 다룬다.

## 무엇을 노출하나: 한눈에 보기

MCP에서 노출되는 능력은 서버가 제공하는 primitive와 클라이언트가 제공하는 기능으로 나뉜다. 서버 primitive는 세 가지이고, 각각 "누가 통제하는가"가 다르다.

| 서버 primitive | 통제 주체 | 목적 | 예시 |
|---------------|----------|------|------|
| Tools | 모델 | 모델이 호출하는 실행 함수 | `search_issue`, `query_db`, `render_pdf` |
| Resources | 애플리케이션 | 앱이 모델에 넣어 줄 컨텍스트 데이터 | 파일, DB row, API 응답, 문서 URI |
| Prompts | 사용자 | 사용자가 고르는 작업 템플릿 | 코드 리뷰, 보고서 작성, 장애 분석 프롬프트 |

Tools는 모델이 스스로 판단해 부르는 동작이고, Resources는 앱이 어떤 컨텍스트를 넣을지 통제하는 읽기 데이터이며, Prompts는 사용자가 명시적으로 선택하는 재사용 템플릿이다. 통제 주체를 구분해 두면 "모델이 임의로 실행해도 되는가", "앱이 넣기로 결정한 데이터인가", "사용자가 고른 흐름인가"라는 안전 경계가 자연스럽게 나뉜다. 세 primitive의 JSON-RPC 메시지 단위 동작은 [[mcp-02-server-features|MCP 스펙 분석: Tools, Resources, Prompts]]에서 분해한다.

반대 방향, 즉 클라이언트가 서버에 제공하는 기능도 있다.

- **Roots**: 클라이언트가 서버에 노출하는 파일 시스템 경계다. 서버가 접근해도 되는 디렉토리 범위를 알려 준다.
- **Sampling**: 서버가 클라이언트에게 LLM 추론을 요청하는 통로다. 서버가 자체 모델을 두지 않고도 Host의 모델을 빌려 쓸 수 있다.
- **Elicitation**: 서버가 작업 도중 사용자에게 추가 정보를 요청하는 통로다.

이 클라이언트 기능은 [[mcp-03-client-features|MCP 클라이언트 기능]]에서 자세히 다룬다. 핵심은 MCP가 서버에서 클라이언트로 향하는 단방향이 아니라, 양쪽이 서로의 능력을 노출하고 협상하는 구조라는 점이다.

## 연결 수명주기: initialize → operation → shutdown

Client와 Server의 연결은 정해진 수명주기를 따른다.

1. **initialize**: 연결을 열 때 가장 먼저 capability negotiation을 한다. 양쪽은 지원하는 프로토콜 버전과 각자 제공하는 기능(서버의 tools/resources/prompts, 클라이언트의 roots/sampling/elicitation)을 교환한다. 이 협상 결과가 이후 대화에서 무엇을 쓸 수 있는지를 정한다.
2. **operation**: 협상된 capability 범위 안에서 실제 메시지를 주고받는다. `tools/list`로 도구 목록을 받고 `tools/call`로 실행하며, `resources/read`로 컨텍스트를 읽는 식이다.
3. **shutdown**: 연결을 정리하고 종료한다.

capability negotiation을 먼저 하기 때문에, 서버가 새 기능을 추가해도 그 기능을 이해하지 못하는 구형 클라이언트와 안전하게 공존한다. 규격은 공유하되 버전과 기능은 연결 시점에 맞춰 협상하는 구조다.

## MCP가 하지 않는 것

MCP는 에이전트 간 협업 프로토콜이 아니다. 다른 에이전트에게 일을 위임하고 장시간 Task를 추적하려면 [[a2a|A2A]]가 더 적합하다. MCP는 UI 이벤트 프로토콜도 아니다. 사용자가 도구 호출 상태를 실시간으로 보려면 [[ag-ui-realtime-events|AG-UI]] 같은 이벤트 계층이 필요하다.

따라서 실전 구조는 MCP 단독이 아니라 조합이다. MCP는 에이전트가 도구를 쓰는 수직 통신을, A2A는 에이전트가 서로 협업하는 수평 통신을, AG-UI는 그 과정을 사용자에게 보여주는 통신을 담당한다. 세 프로토콜의 경계를 한눈에 보려면 [[agent-protocol-stack|Agent Protocol Stack]]을 함께 읽는 것이 좋고, MCP와 A2A의 직교성만 깊게 보려면 [[a2a-03-vs-mcp|A2A vs MCP]]가 있다.

## 실무로 옮기기 전: 도입 시 결정

MCP를 프로덕션에 넣을 때는 개념을 외우기보다 몇 가지 결정을 먼저 못박는 편이 낫다.

- **무엇을 서버로 뺄지**: 앱 안에 하드코딩된 통합 중 어떤 것을 MCP Server로 분리할지 정한다. 여러 앱이 공유하거나, 독립적으로 배포·버전관리하고 싶은 도구가 우선 후보다.
- **한 서버의 책임 범위**: 서버 하나가 어떤 tools/resources/prompts를 묶어 제공할지 정한다. 관련 없는 능력을 한 서버에 몰면 권한 경계가 흐려진다.
- **로컬 stdio vs 원격 HTTP**: 서버를 사용자 기기에서 로컬 프로세스(stdio)로 돌릴지, 원격 서비스(HTTP)로 둘지 정한다. 로컬은 파일이나 개인 데이터 접근에, 원격은 공유 서비스와 중앙 관리에 맞는다. 선택 기준은 [[mcp-04-transports|MCP Transport]]에서 다룬다.
- **동의와 권한 노출**: 모델이 도구를 실행하기 전 사용자 동의를 어떻게 UX에 드러낼지 정한다. 원격 서버라면 인증과 권한을 운영 표준에 맞춰야 한다. 이 관점은 [[mcp-05-security-operations|MCP 보안과 운영]]에서 구체화한다.

이 결정들을 먼저 적어 두면, 이후 서버가 늘어나도 "어느 레이어의 책임인가"를 기준으로 구조를 유지할 수 있다.

## 다음 글

다음 편 [[mcp-02-server-features|MCP 스펙 분석: Tools, Resources, Prompts]]에서는 서버가 노출하는 세 primitive를 실제 JSON-RPC 메시지 단위로 분해한다.

## 관련 문서

- [[mcp|MCP]] - 본 시리즈가 속한 아키텍처 엔트리
- [[mcp-02-server-features|MCP 서버 기능]] - Tools/Resources/Prompts 상세
- [[mcp-03-client-features|MCP 클라이언트 기능]] - Roots/Sampling/Elicitation
- [[mcp-04-transports|MCP Transport]] - 로컬 stdio와 원격 HTTP 트랜스포트
- [[mcp-05-security-operations|MCP 보안과 운영]] - 동의·인증·권한 경계
- [[mcp-06-fastmcp-internal-api|FastMCP 내부 API]] - 서버 구현 프레임워크
- [[a2a-03-vs-mcp|A2A vs MCP]] - 수직·수평 통신의 직교성
- [[agent-protocol-stack|Agent Protocol Stack]] - MCP·A2A·AG-UI·AGNTCY 레이어 지도
- [[ai-agent-technology-guide|AI Agent 기술 지도]] - 에이전트 기술 전반 개관

## 참고 자료
- [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP architecture](https://modelcontextprotocol.io/specification/2025-11-25)
