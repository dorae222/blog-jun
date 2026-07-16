<!-- infographic-hero -->
![MCP 보안과 운영: OAuth, consent, DNS rebinding, registry 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: MCP 보안과 운영: OAuth, consent, DNS rebinding, registry 한 장 요약. (Source: MCP/A2A/AG-UI 공식 문서 기반 자체 작성)*

# MCP 보안과 운영: OAuth, consent, DNS rebinding, registry

> 시리즈 안내: 본 글은 [[mcp|MCP]] 시리즈의 5편입니다. 시리즈는 [[mcp-01-overview|1편 개요]], [[mcp-02-server-features|2편 서버 기능]], [[mcp-03-client-features|3편 클라이언트 기능]], [[mcp-04-transports|4편 전송 계층]], [[mcp-05-security-operations|5편 보안과 운영]], [[mcp-06-fastmcp-internal-api|6편 FastMCP 실전]]으로 구성됩니다.

:::info
2026-07 검증 기준: 본 글은 MCP 공식 스펙의 보안 원칙(User Consent, Data Privacy, Tool Safety, Sampling Controls)과 원격 전송의 OAuth 2.0 인가, Origin 검증 요구사항을 기준으로 정리한다. 특정 CVE나 개별 사고가 아니라 구조적으로 반복되는 위협 범주만 다룬다.
:::

MCP 서버는 단순한 플러그인이 아니다. 도구 호출, 데이터 접근, 프롬프트 제공, 경우에 따라 모델 샘플링 요청까지 가능하게 만드는 실행 경계다. 그래서 MCP 운영의 핵심은 "연결이 된다"가 아니라 "누가 무엇을 어떤 승인 아래 호출했는지 설명할 수 있다"이다.

![MCP 보안 레이어](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: MCP 보안 레이어. 사용자 동의 UI, 클라이언트 정책 게이트, transport 인증, 서버 최소 권한을 함께 설계해야 한다. (Source: MCP security guidance 및 MCPSecBench 논문 기반 자체 작성)*

## 왜 MCP 보안은 일반 API 보안과 다른가

일반 API 보안은 클라이언트가 무엇을 호출할지 코드로 미리 정해 둔다. MCP는 다르다. 어떤 도구를 언제 호출할지 결정하는 주체가 사람이 아니라 모델이고, 모델은 서버가 준 도구 설명과 리소스 내용을 읽고 판단한다. 즉 신뢰 경계 안으로 들어오는 데이터, 곧 도구 description과 resource 본문이 그대로 제어 흐름에 영향을 준다.

그래서 MCP 보안은 인증만으로 끝나지 않는다. 인증된 서버가 준 정직해 보이는 도구 설명이 사실은 모델을 조종하려는 지시일 수 있다. 이 글은 세 축으로 나눠 본다. 인증은 누가 접근하는가, 인가는 무엇을 할 수 있는가, 그리고 완화는 모델이 신뢰 경계 안 콘텐츠에 조종당하지 않게 하는 장치다. 이 세 축이 맞물려야 "누가 무엇을 어떤 승인 아래 호출했는지"를 사후에 설명할 수 있다.

## 공식 스펙의 네 가지 보안 원칙

MCP 공식 스펙은 User Consent and Control, Data Privacy, Tool Safety, LLM Sampling Controls를 핵심 원칙으로 둔다. 이를 운영 체크리스트로 바꾸면 다음과 같다.

| 원칙 | 운영 체크 |
|------|-----------|
| User Consent | 도구 이름, 인자, 대상 데이터, 예상 결과를 호출 전에 보여준다 |
| Data Privacy | Resource와 Tool 결과가 어떤 모델/서버로 전달되는지 제한한다 |
| Tool Safety | 입력 검증, rate limit, timeout, 출력 sanitization을 구현한다 |
| Sampling Controls | 서버가 요청한 모델 호출은 사용자와 클라이언트가 승인한다 |

이 네 원칙은 서로 독립된 항목이 아니라 하나의 흐름이다. 사용자가 동의한 범위 안에서, 데이터가 정해진 경계를 넘지 않게, 도구가 안전하게 실행되고, 모델 재호출까지 승인 아래 이뤄지는 것이다. 아래 절들은 이 흐름을 인증, 위협, 완화, 운영의 순서로 구체화한다.

## 인증과 인가: 원격은 OAuth, 로컬은 프로세스 경계

원격 MCP 서버는 대부분 외부 SaaS나 사내 API에 접근한다. 이 경우 서버가 모든 사용자의 장기 토큰을 한곳에 들고 있는 구조는 위험하다. 스펙은 원격 전송에 대해 OAuth 2.0 기반 인가를 권장한다. 사용자 단위로 access token을 발급하고, 짧은 수명과 refresh 정책을 두며, token scope로 도구가 실제로 필요로 하는 범위만 허용한다.

여기서 핵심은 사용자 동의(consent)다. 어떤 scope를 어떤 서버에 위임하는지 사용자가 명시적으로 승인해야 하고, 그 동의 내역은 나중에 조회하거나 취소하거나 감사할 수 있어야 한다. 동의가 한 번의 클릭으로 끝나고 흔적이 남지 않으면, 나중에 "이 서버가 왜 이 데이터에 접근했는가"에 답할 수 없다.

권한은 MCP 서버 단위가 아니라 Tool과 Resource 단위로 생각해야 한다. 같은 GitHub MCP 서버라도 issue read, pull request write, repository admin은 완전히 다른 권한이다. scope를 서버 전체에 뭉뚱그리면 최소 권한 원칙이 처음부터 무너진다.

로컬 stdio 서버는 네트워크 인가 대신 프로세스 경계가 보안 단위다. 클라이언트가 자식 프로세스로 서버를 띄우고 stdin/stdout으로만 통신하므로 네트워크에 노출되지 않는다. 대신 그 프로세스는 실행 사용자 권한으로 파일 시스템과 명령을 건드릴 수 있다는 점을 잊으면 안 된다. 로컬이라고 안전한 것이 아니라 경계의 종류가 다를 뿐이다. 원격 전송 자체의 보안 요구사항은 [[mcp-04-transports|4편 전송 계층]]에서 Origin 검증, TLS, 세션 관리와 함께 다룬다.

## 주요 위협 범주

MCP는 신뢰할 수 없는 서버와 신뢰할 수 없는 콘텐츠를 전제로 설계해야 한다. 일반적으로 알려진 위협 범주는 다음과 같다.

- **Prompt injection과 tool poisoning**: 악성 도구 설명(description)이나 리소스 내용이 모델에게 숨은 지시를 주입해 행동을 조종한다. 모델은 도구 메타데이터를 그대로 신뢰하기 쉬우므로, 도구 설명 자체가 공격 표면이 된다.
- **Confused deputy**: 서버가 자신에게 위임된 클라이언트 권한을 오용해, 사용자가 의도하지 않은 대상에 그 권한을 행사한다. 특히 여러 사용자의 토큰을 대리 보관하는 서버에서 나타나기 쉽다.
- **과도한 권한의 도구**: 한 번의 승인으로 광범위한 작업을 할 수 있는 도구는 prompt injection과 결합되면 피해 범위가 커진다. 삭제, 전송, 결제 같은 destructive 동작일수록 권한을 좁혀야 한다.
- **신뢰할 수 없는 리소스 내용**: 서버가 반환한 Resource나 Tool 결과에 악성 지시나 민감 데이터가 섞여 downstream 모델과 다른 도구로 전파된다.

이 범주들은 특정 사고나 버전에 묶인 것이 아니라 구조적으로 반복되는 패턴이다. 그래서 완화도 개별 버그 패치가 아니라 경계 설계로 접근한다.

## 완화 원칙

위협 범주를 뒤집으면 그대로 완화 원칙이 된다.

- **최소 권한(least privilege)**: 도구와 scope는 필요한 최소 범위만 부여한다. read와 write, 일반과 destructive를 분리한다.
- **사람이 개입하는 승인(human-in-the-loop)**: 민감 도구 실행과 서버가 요청한 Sampling은 사용자와 클라이언트가 승인한 뒤에만 진행한다. 이 승인 흐름의 설계는 [[mcp-03-client-features|3편 클라이언트 기능]]의 Sampling과 Elicitation에서 다룬다.
- **도구 출처 신뢰와 서명**: 서버 패키지의 출처를 확인하고, 가능하면 서명과 버전 고정으로 공급망을 통제한다. 신뢰할 수 없는 출처의 도구 설명은 그 자체로 실행하지 않는다.
- **목록 변경 감사**: 서버가 도구와 리소스 목록을 바꾸면(list_changed) 그 변경을 감사 로그로 남긴다. 조용히 바뀐 도구 설명이 새로운 injection 경로가 될 수 있기 때문이다.
- **입력 검증**: 도구 인자에 대한 schema 검증, rate limit, timeout, 출력 sanitization을 서버 쪽에서도 구현한다. 클라이언트 승인만 믿지 않는다.

이 다섯 원칙은 겹겹의 방어로 작동한다. 최소 권한으로 피해 범위를 줄이고, 사람 승인으로 마지막 방어선을 세우며, 출처 신뢰와 목록 감사로 도구 자체를 검증하고, 입력 검증으로 실행 시점을 지킨다. 어느 하나만으로는 충분하지 않다. injection처럼 여러 경계를 동시에 노리는 공격일수록 한 겹이 뚫려도 다음 겹이 남아 있어야 한다.

## DNS rebinding과 로컬 서버

Streamable HTTP 서버를 로컬에 띄울 때 가장 쉽게 놓치는 공격 표면은 DNS rebinding이다. 스펙은 Origin 헤더 검증, localhost bind, 적절한 인증을 요구한다. 로컬 MCP 서버는 "내 컴퓨터에서만 열려 있으니 안전하다"가 아니다. 브라우저와 로컬 네트워크 경계가 섞이면 외부 웹사이트가 로컬 포트를 건드릴 수 있다. 그래서 로컬 HTTP 서버라도 Origin 검증과 인증을 기본으로 켜 둔다.

:::warning
로컬 서버라고 인증과 Origin 검증을 생략하면 안 된다. 브라우저가 로드한 외부 페이지가 localhost 포트로 요청을 보낼 수 있고, 이때 서버가 요청을 무조건 신뢰하면 로컬 도구가 그대로 외부에 노출된다.
:::

## Registry와 공급망

MCP 서버가 npm, PyPI, 컨테이너 이미지로 배포되면 공급망 관리가 필요하다. 어떤 서버가 어떤 권한을 요구하는지, 누가 유지보수하는지, 업데이트가 신뢰 가능한지, 취약 버전을 어떻게 차단할지 관리해야 한다. 이는 앞의 "도구 출처 신뢰와 서명" 원칙을 배포 파이프라인 수준으로 끌어올린 것이다. registry에서 받은 서버를 그대로 신뢰하지 말고, 출처와 버전을 고정한 뒤 승인된 것만 프로덕션에 올린다.

## 운영과 관측성

보안 설계가 끝나면 그것을 운영 중에 확인할 수 있어야 한다. MCP 운영의 최소 관측 축은 "어떤 도구가 언제, 누구의 요청으로 호출됐는가"다. 구체적으로 tool name, arguments, 호출자(caller/session), 결과 상태를 함께 기록한다. 성공 로그만 남기면 공격 신호를 놓친다. 거부되거나 실패한 호출, 승인이 거절된 요청, scope를 벗어난 시도를 별도로 추적해야 이상 패턴이 보인다.

최소한 다음 축은 매 도구 호출마다 남긴다. 이름을 미리 고정해 두면 나중에 요청 하나를 끝까지 재구성할 수 있다.

- 호출 식별: `session_id`, `tool_name`, 요청 시각
- 인가 맥락: 사용된 scope와 token 주체
- 결과: 성공/실패/거부 상태와 소요 시간
- 데이터 흐름: 결과가 어느 모델이나 downstream 도구로 전달됐는지

토큰과 세션 수명도 관측 대상이다. access token이 언제 발급되고 만료되는지, 세션이 얼마나 오래 살아 있는지, refresh가 어디서 일어나는지를 보면 confused deputy나 토큰 탈취의 흔적을 잡을 수 있다. 핵심은 이 축들의 이름을 배포 전에 미리 정해 두는 것이다. 나중에 로그를 붙이면 필드가 제각각이 되어 상관 분석이 어렵다.

이 관점은 에이전트 사이 통신 보안과 대비하면 더 분명해진다. 에이전트가 서로를 호출하는 구조에서는 관측 축이 `agent_id`, `task_id`, `context_id`로 확장되는데, 그 설계는 [[a2a-05-adk-integration|A2A ADK 통합과 보안]]에서 서명과 mTLS와 함께 다룬다. MCP는 그보다 한 층 아래, 에이전트와 도구 사이의 경계에서 같은 원칙을 적용한다.

## 배포 전 보안 체크

프로덕션에 MCP 서버를 붙이기 전에 아래 항목을 각각 다른 신호로 확인한다. 표의 목적은 "다 했다"가 아니라 각 항목이 무엇으로 검증되는지를 분명히 하는 것이다.

| 점검 항목 | 확인 신호 |
|-----------|-----------|
| 원격 서버 인가 | access token이 사용자 단위로 발급되고 scope가 도구 범위와 일치하는가 |
| 민감 도구 승인 | destructive 도구와 Sampling 요청이 사람 승인 UI를 반드시 거치는가 |
| 도구 출처 신뢰 | 서버 패키지의 출처와 서명, 버전 고정이 배포 파이프라인에 기록되는가 |
| 목록 변경 감사 | list_changed 알림과 실제 도구/리소스 diff가 감사 로그에 남는가 |
| 로컬 전송 경계 | stdio 서버가 원격에 노출되지 않고 HTTP 서버는 Origin과 localhost bind를 검증하는가 |
| 관측 축 정의 | tool name, arguments, caller, 결과 상태가 trace 축으로 이미 정의되어 있는가 |

각 행의 확인 신호는 서로 다르다. 인가는 토큰과 scope로, 승인은 UI 흐름으로, 출처는 파이프라인 기록으로, 변경은 감사 로그로, 전송은 bind와 Origin으로, 관측은 미리 정의된 축으로 확인한다. 하나라도 "구현했으니 됐다"로 넘어가면 운영 중 그 지점부터 장애 위치를 설명하기 어려워진다.

## 다음 글

다음 [[mcp-06-fastmcp-internal-api|6편 FastMCP 실전]]에서는 FastMCP로 내부 API를 안전하게 감싸는 최소 예제를 만든다. 이 글의 인증, 최소 권한, 관측 축을 실제 코드 경계로 옮기는 단계다.

## 관련 문서

- [[mcp|MCP]] - 본 시리즈가 속한 아키텍처 엔트리
- [[mcp-03-client-features|MCP 클라이언트 기능]] - Sampling과 Elicitation 승인 흐름
- [[mcp-04-transports|MCP 전송 계층]] - 원격 전송의 Origin 검증과 세션 보안
- [[mcp-06-fastmcp-internal-api|MCP FastMCP 실전]] - 보안 원칙을 코드로 옮기는 최소 예제
- [[a2a-05-adk-integration|A2A ADK 통합과 보안]] - 에이전트 간 보안과의 대비
- [[agent-protocol-production-reference|Agent Protocol 종합 실전]] - 프로토콜 운영 관점 종합

## 참고 자료
- [MCP specification security section](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Transports security warning](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [MCPSecBench](https://arxiv.org/html/2508.13220v3)
