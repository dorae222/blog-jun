<!-- infographic-hero -->
![MCP Transport: stdio vs Streamable HTTP 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: MCP Transport: stdio vs Streamable HTTP 한 장 요약. (Source: MCP/A2A/AG-UI 공식 문서 기반 자체 작성)*

# MCP Transport: stdio vs Streamable HTTP

MCP는 클라이언트와 서버가 주고받는 모든 메시지를 JSON-RPC 2.0으로 인코딩한다. 그런데 이 메시지를 실제로 어떤 통로로 실어 나를지는 별개의 문제다. 같은 JSON-RPC 메시지라도 로컬 프로세스의 stdin/stdout을 타고 흐를 수 있고, 네트워크 위의 HTTP 요청과 SSE 스트림을 타고 흐를 수도 있다. MCP 스펙은 이 통로를 transport라고 부르고, 표준으로 두 가지를 정의한다. 로컬 서버를 위한 stdio, 원격 서버를 위한 Streamable HTTP다.

![MCP transport 선택 기준](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: MCP transport 선택 기준. 로컬 subprocess 통합은 stdio, 원격/프로덕션 서버는 Streamable HTTP와 SSE를 사용한다. (Source: MCP transports docs 기반 자체 작성)*

## 공통층: JSON-RPC 2.0 메시지

transport를 이해하려면 먼저 그 위에 얹히는 메시지 계층을 분리해서 봐야 한다. MCP의 모든 상호작용은 세 종류의 JSON-RPC 2.0 메시지로 환원된다.

- request: 응답을 기대하는 호출. `id`를 가지며, 상대가 반드시 result나 error로 답해야 한다.
- response: request에 대한 답. 같은 `id`로 result 또는 error를 돌려준다.
- notification: 응답이 필요 없는 단방향 통지. `id`가 없다.

tool 호출, resource 조회, prompt 요청, 초기화 handshake까지 모두 이 세 형태의 조합이다. 이 계층은 transport가 무엇이든 동일하다. 즉 [[mcp-02-server-features|MCP 서버 기능]]이 노출하는 도구와 [[mcp-03-client-features|MCP 클라이언트 기능]]이 제공하는 기능은 stdio든 HTTP든 똑같은 메시지로 표현된다. transport가 결정하는 것은 오직 "이 메시지를 어떤 물리 통로로, 어떤 수명과 신뢰 경계 안에서 나르는가"다.

연결이 열리면 가장 먼저 `initialize` 요청과 응답으로 handshake를 주고받으며, 이때 양쪽이 지원하는 기능(capabilities)과 프로토콜 버전을 협상한다. 이 handshake 역시 JSON-RPC 메시지이므로 transport와 무관하게 동일한 절차로 진행된다. 다시 말해 transport는 세션의 물리적 시작과 끝, 그리고 메시지를 실어 나르는 방식만 책임질 뿐, 그 안에서 오가는 대화의 문법은 건드리지 않는다. 이 분리 덕분에 서버 구현은 도구 로직에 집중하고, transport는 배포 환경에 맞춰 갈아 끼우는 대상이 된다.

예를 들어 클라이언트가 `tools/call` request를 보낼 때, stdio에서는 이 JSON 한 줄이 서버의 stdin으로 들어가고 결과가 stdout으로 나온다. 같은 request가 Streamable HTTP에서는 `/mcp`로의 POST 본문이 되고, 서버가 오래 걸리는 작업이면 응답이 SSE 이벤트로 조각조각 흘러나온다. 메시지의 내용(`method`, `params`, `id`)은 두 경우가 완전히 동일하고, 달라지는 것은 그 바이트가 지나는 통로와 응답이 도착하는 방식뿐이다.

## stdio 전송

stdio transport에서는 클라이언트가 MCP 서버를 하위 프로세스(subprocess)로 직접 띄운다. 서버는 stdin에서 JSON-RPC 메시지를 읽고 stdout으로 응답을 쓴다. 로그나 진단 출력은 stderr로 흘려보내되, stdout에는 반드시 유효한 MCP 메시지만 써야 한다. stdout에 디버그 문자열이 섞이면 프레이밍이 깨져 클라이언트가 파싱에 실패한다.

메시지는 개행으로 구분되는 JSON 텍스트로 오간다. 그래서 서버 코드가 실수로 stdout에 한 줄을 남기면 그 줄이 메시지로 오인되어 세션 전체가 무너질 수 있다. 라이브러리 로그, 진행 표시, 예외 스택은 모두 stderr로 보내는 것이 기본 규율이다.

이 구조에서 연결 수명은 곧 프로세스 수명이다. 클라이언트가 서버 프로세스를 spawn하면 세션이 시작되고, 프로세스를 종료하면 연결도 끝난다. 별도의 세션 ID나 재연결 개념이 필요 없다. 네트워크 포트를 열지 않으므로 지연이 가장 낮고, 방화벽이나 TLS 설정도 필요 없다.

보안 경계는 로컬 프로세스 경계 그 자체다. 서버는 자신을 실행한 사용자의 권한으로 로컬 파일 시스템, 로컬 데이터베이스, 개발자 도구에 접근한다. 인증 프로토콜이 개입하지 않는 대신 "누가 이 프로세스를 띄울 수 있는가"가 곧 접근 통제가 된다. 그래서 stdio는 로컬 단일 사용자 도구에 자연스럽게 맞는다.

## Streamable HTTP 전송

Streamable HTTP는 서버가 독립적으로 떠 있고 클라이언트가 네트워크 너머로 접속하는 방식이다. 서버는 보통 `/mcp` 같은 단일 HTTP endpoint 하나를 노출한다. 클라이언트는 이 endpoint에 POST로 JSON-RPC 메시지를 보내고, 서버는 상황에 따라 두 가지로 답한다. 단발 응답이면 그냥 JSON 본문을 돌려주고, 진행 상황을 나눠 보내야 하면 같은 응답을 Server-Sent Events(SSE) 스트림으로 연다. 클라이언트가 서버발 메시지를 받기 위해 GET으로 SSE 스트림을 별도로 열 수도 있다.

원격 서버이므로 stdio에 없던 두 가지가 생긴다. 첫째는 세션이다. 서버는 초기화 응답에서 `Mcp-Session-Id`를 발급할 수 있고, 클라이언트는 이후 요청마다 이 헤더를 실어 자신이 같은 세션임을 밝힌다. 둘째는 재연결이다. 네트워크가 끊겨 SSE 스트림이 닫히면 클라이언트는 다시 접속해 스트림을 이어야 한다. 또한 각 HTTP 요청에는 협상된 `MCP-Protocol-Version` 헤더를 함께 싣는 것이 권장된다.

세션이 항상 필수인 것은 아니다. 서버가 상태를 들고 있지 않아도 되는 단순 도구라면 세션 없이 요청마다 독립적으로 처리하도록 구현할 수도 있다. 이 경우 서버는 `Mcp-Session-Id`를 발급하지 않고 각 요청이 그 자체로 완결되며, 서버리스처럼 인스턴스가 요청 단위로 뜨고 사라지는 배포와 잘 맞는다. 반대로 도구가 진행 상태나 대화 맥락을 이어가야 하면 세션을 두고 재연결까지 설계해야 한다.

과거 MCP는 HTTP 계열 transport로 요청용 POST endpoint와 수신용 SSE endpoint를 나눠 쓰는 HTTP+SSE 방식을 두었다. Streamable HTTP는 이를 단일 endpoint로 통합해 세션과 재연결을 다루기 쉽게 만든 흐름으로 이해하면 충분하다. 구형 방식의 세부는 스펙 버전마다 다르므로, 실제 구현 대상 버전을 직접 확인하는 편이 안전하다.

## DNS rebinding 방어

Streamable HTTP를 로컬에서 띄우면 DNS rebinding 공격 표면이 생긴다. 공식 스펙은 Streamable HTTP 서버가 Origin 헤더를 검증하고, 로컬 실행 시 127.0.0.1에만 bind하며, 적절한 인증을 구현할 것을 요구한다.

운영 관점에서 이 부분은 선택 사항이 아니다. MCP 서버는 도구 호출과 데이터 접근을 제공하므로, 브라우저에서 접근 가능한 로컬 포트가 열려 있으면 외부 사이트가 내부 도구를 호출하는 경로가 될 수 있다. transport가 로컬 프로세스 경계를 벗어나 네트워크 소켓으로 바뀌는 순간 방어 책임도 함께 옮겨 온다.

## 언제 무엇을 쓰나

선택의 축은 성능보다 "서버가 어디서 누구를 위해 도는가"다.

- 로컬에서, 단일 사용자를 위해, 사용자 컴퓨터 안의 자원에 접근한다면 stdio. IDE 확장, 데스크톱 앱에 붙는 파일 시스템 도구, 개인 개발 도구가 여기 해당한다.
- 원격에서, 여러 사용자를 위해, 네트워크를 경유해 접근한다면 Streamable HTTP. 팀 공용 SaaS 통합, 서버리스로 배포한 도구 서버, 사내 마이크로서비스로 뜬 MCP가 여기 해당한다.

경계는 인증과 네트워크 보안이 필요한지에서 갈린다. stdio는 프로세스 경계가 곧 보안이라 인증이 개입하지 않지만, HTTP는 네트워크에 노출되는 순간 인증, 권한, consent가 필수가 된다. 이 주제는 [[mcp-05-security-operations|MCP 보안과 운영]]에서 OAuth와 위협 모델까지 이어서 다룬다.

## 전송 선택 기준

두 transport를 네 축으로 나눠 보면 각 축마다 결정을 좌우하는 근거가 다르다.

| 기준 | stdio | Streamable HTTP | 결정을 가르는 근거 |
|------|-------|-----------------|---------------------|
| 지연 | 프로세스 간 파이프 왕복이라 짧다 | 네트워크와 TLS를 거쳐 상대적으로 길다 | 로컬 자원에 붙는 대화형 도구는 지연이 곧 체감 품질 |
| 배포 | 클라이언트가 서버 바이너리를 직접 spawn | 서버를 따로 띄우고 URL로 접속 | 기기마다 설치할지, 한 곳에 두고 공유할지 |
| 인증 | 프로세스 경계가 곧 접근 통제 | OAuth 등 명시적 인증이 필요 | 신뢰할 수 없는 호출자에게 노출되는가 |
| 확장 | 사용자당 프로세스 하나, 수평 확장 개념 없음 | 세션 기반으로 다수 클라이언트 수용 | 동시 사용자 수와 상태 공유 요구 |

이 표의 요점은 "무엇이 더 빠른가"가 아니라 각 행이 서로 다른 질문에 답한다는 것이다. 지연이 문제라면 로컬성이, 배포가 문제라면 설치 부담이, 인증이 문제라면 노출 범위가, 확장이 문제라면 동시성이 판단 기준이 된다.

상황별로 정리하면 다음과 같다.

| 상황 | 권장 transport |
|------|----------------|
| 개인 개발자가 로컬 도구를 연결 | stdio |
| 데스크톱 앱이 파일 시스템 도구를 실행 | stdio |
| 팀 공용 SaaS 통합 서버 | Streamable HTTP |
| Kubernetes 내부 MCP 서비스 | Streamable HTTP + 인증 + mTLS |
| 서버리스 MCP 서버 | Streamable HTTP |

## A2A 전송과의 유사성

transport와 메시지 계층을 분리하는 이 발상은 MCP만의 것이 아니다. [[a2a|A2A]]도 같은 JSON-RPC 2.0 메시지를 여러 binding으로 나르며, 스펙은 JSON-RPC, gRPC, HTTP+JSON/REST와 SSE streaming을 함께 정의한다. "메시지 모델은 하나, 운반 방식은 여럿"이라는 구조가 두 프로토콜에 공통이다. A2A의 transport binding 구성은 [[a2a-02-specification|A2A 스펙 분석]]에서, MCP와 A2A의 역할 차이는 [[a2a-03-vs-mcp|A2A vs MCP]]에서 다룬다.

## 실무 관점

실무에서 transport 선택은 대개 한 번의 결정으로 끝나지 않는다. 로컬 개발 단계에서 stdio로 시작한 서버를 팀에 공유하려면 Streamable HTTP로 다시 감싸야 하는데, 이때 메시지 계층(도구, resource, prompt 정의)은 그대로 두고 transport만 교체하면 된다는 점이 설계의 이점이다. 서버 로직을 transport에 의존하지 않게 짜 두면 이 전환 비용이 작아진다.

반대로 흔한 실수는 stdio 시절의 전제를 원격 서버에 그대로 끌고 가는 것이다. 로컬에서는 인증이 없어도 됐으니 HTTP로 옮긴 뒤에도 endpoint를 열어만 두는 식이다. 네트워크에 노출된 MCP 서버는 도구 호출과 데이터 접근을 제공하므로, 인증과 Origin 검증이 빠지면 그 자체가 공격 표면이 된다. transport를 바꾸는 순간 신뢰 경계도 함께 바뀐다는 것을 결정 시점에 적어 두는 편이 좋다.

프로덕션에서는 transport 계층 자체가 관측 대상이 된다. stdio 서버는 프로세스 생존과 재시작 로그를 남겨야 하고, HTTP 서버는 endpoint별 요청 수, SSE 스트림 지속 시간, 세션 재연결 빈도를 지표로 남겨야 장애를 재현할 수 있다. 같은 도구 서버라도 transport에 따라 감시해야 할 신호가 달라진다는 뜻이다. 이런 운영 관점을 프로토콜 스택 전체로 넓혀 보려면 [[agent-protocol-production-reference|Agent Protocol 프로덕션 레퍼런스]]가 참고가 된다.

FastMCP처럼 하나의 서버 정의로 stdio와 HTTP를 모두 서빙하는 구현도 이 분리를 전제로 한다. 서버 내부 동작은 [[mcp-06-fastmcp-internal-api|FastMCP 내부 API]]에서 더 파고든다.

## 다음 글

다음 [[mcp-05-security-operations|MCP 보안과 운영]]에서는 원격 transport가 필연적으로 요구하는 인증을 중심으로 OAuth, consent, registry, 위협 모델을 정리한다.

## 관련 문서

- [[mcp|MCP]] - 본 시리즈가 속한 아키텍처 엔트리
- [[mcp-01-overview|MCP 개요]] - 프로토콜 전체 그림과 시리즈 출발점
- [[mcp-02-server-features|MCP 서버 기능]] - transport 위에 얹히는 tool·resource·prompt
- [[mcp-03-client-features|MCP 클라이언트 기능]] - sampling·roots 등 클라이언트 측 메시지
- [[mcp-05-security-operations|MCP 보안과 운영]] - 원격 transport의 인증과 위협 모델
- [[mcp-06-fastmcp-internal-api|FastMCP 내부 API]] - 하나의 정의로 stdio·HTTP 서빙
- [[a2a-02-specification|A2A 스펙 분석]] - JSON-RPC/gRPC/SSE binding 비교
- [[a2a-03-vs-mcp|A2A vs MCP]] - 수평·수직 통신의 역할 차이
- [[agent-protocol-stack|Agent Protocol Stack]] - MCP·A2A·AG-UI·AGNTCY 레이어 지도
- [[agent-protocol-production-reference|Agent Protocol 프로덕션 레퍼런스]] - 스택 전반의 운영·관측 관점
- [[ai-agent-technology-guide|AI Agent 기술 지도]] - 에이전트 기술 전반 개관

## 참고 자료
- [MCP Transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
