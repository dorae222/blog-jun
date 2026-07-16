<!-- infographic-hero -->
![Agent Protocol 종합 실전: MCP, A2A, AG-UI 레퍼런스 아키텍처 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure 1: Agent Protocol 종합 실전: MCP, A2A, AG-UI 레퍼런스 아키텍처 한 장 요약. (Source: MCP/A2A/AG-UI 공식 문서 기반 자체 작성)*

# Agent Protocol 종합 실전: MCP, A2A, AG-UI 레퍼런스 아키텍처

이 글은 MCP, A2A, AG-UI를 따로 이해한 뒤 실제 시스템으로 묶는 최종 그림이다. 목표는 "에이전트가 도구를 쓰고, 다른 에이전트와 협업하며, 사용자는 그 과정을 볼 수 있는 구조"를 만드는 것이다. 각 프로토콜을 개념 단위로 먼저 정리하고 싶다면 [[agent-protocol-stack|Agent Protocol Stack]]에서 레이어 지도를 확인하고 돌아오는 편이 이해가 빠르다. 이 글은 그 지도를 실제 프로덕션 시스템의 경계로 옮긴다.

![Agent Protocol 종합 레퍼런스 아키텍처](figures/architecture.svg?v=layout-20260706-fix2)

*Figure 2: Agent Protocol end-to-end 레퍼런스 아키텍처. UI는 AG-UI 이벤트를 받고, Orchestrator는 A2A로 전문 에이전트를 호출하며, 각 에이전트는 MCP로 도구와 데이터에 접근한다. (Source: MCP/A2A/AG-UI 공식 문서 기반 자체 작성)*

## 구성 요소

| 구성 요소 | 책임 |
|-----------|------|
| User UI | 사용자 입력, 진행 상태, tool call, 승인/거절 인터럽트 표시 |
| Orchestrator Agent | 목표 분해, 전문 에이전트 선택, Task 상태 통합 |
| Remote Agents | 특정 업무 수행, Artifact 생성, 장시간 작업 처리 |
| MCP Servers | 사내 API, DB, 문서, 파일, 배포 시스템을 도구/리소스로 노출 |
| Policy Gate | 사용자 동의, 권한, 데이터 반출, 비용 통제 |
| Observability | 모델 호출, 도구 호출, Task 이벤트, UI 이벤트 trace 연결 |

## 참조 토폴로지

프로덕션에서 네 프로토콜은 각각 하나의 경계(boundary)를 맡는다. 경쟁하는 표준이 아니라 서로 다른 층을 담당하므로, 설계의 핵심은 "어느 경계가 어떤 책임을 지는가"를 흐리지 않는 것이다. 위에서 아래로 요청이 흐르는 순서대로 정리한다.

- **UI 경계 - AG-UI**: 사용자 화면은 [[ag-ui-realtime-events|AG-UI 실시간 이벤트]]로 Orchestrator에 붙는다. 사용자의 목표를 run으로 시작하고, 에이전트가 만드는 중간 상태(진행률, tool call, 승인 요청)를 이벤트 스트림으로 되받아 표시한다. 이 경계의 책임은 "사람이 개입하는 지점"을 표준화하는 것이다. 무엇을 보여줄지, 어디서 승인을 받을지가 여기서 정해진다.
- **에이전트 간 경계 - A2A**: Orchestrator는 [[a2a-02-specification|A2A 스펙]]의 Task로 전문 에이전트에 작업을 위임한다. 이 경계의 책임은 원격 에이전트를 자율적이고 장시간 실행되는 주체로 다루는 것이다. 위임한 작업은 즉시 끝나지 않을 수 있으므로 Task를 일급 객체로 두고 상태 전이를 추적한다. 결과물은 대화가 아니라 Artifact로 분리해 되돌려 받는다.
- **도구 경계 - MCP**: 각 에이전트는 [[mcp-02-server-features|MCP 서버 기능]]으로 사내 API, DB, 문서, 배포 시스템 같은 도구와 리소스에 접근한다. 이 경계의 책임은 "에이전트가 외부 세계에 무엇을 할 수 있는가"를 tool과 resource 단위로 노출하고 통제하는 것이다. 전송 계층의 선택지는 [[mcp-04-transports|MCP 전송 방식]]에서 다룬다.
- **발견 경계 - AGNTCY**: 어떤 원격 에이전트가 어떤 능력을 갖고 있는지는 [[agntcy-agent-discovery-trust|AGNTCY 에이전트 발견과 신뢰]]의 registry와 신뢰 그래프로 찾는다. 이 경계의 책임은 에이전트를 코드에 하드코딩하지 않고 등록·발견·검증하는 것이다. 새 에이전트가 추가되거나 해지될 때 Orchestrator 코드를 재배포하지 않아도 되도록 만든다.

수평 통신(A2A)과 수직 통신(MCP)이 직교한다는 점이 이 토폴로지의 뼈대다. 두 축이 어떻게 나뉘는지는 [[a2a-03-vs-mcp|A2A vs MCP]]에서 코드 예제로 확인할 수 있다.

## 실행 시나리오

예를 들어 "지난주 장애 티켓을 분석해서 고객 공지 초안을 만들어줘"라는 요청을 보자.

1. 사용자가 UI에서 요청한다.
2. UI는 AG-UI run을 시작하고 Orchestrator에 목표를 전달한다.
3. Orchestrator는 A2A로 Incident Analyst Agent에 분석 Task를 보낸다.
4. Incident Analyst는 MCP로 ticket system, log search, runbook resource를 조회한다.
5. 분석 결과는 A2A Artifact로 돌아온다.
6. Orchestrator는 Writer Agent에 공지 초안 작성 Task를 보낸다.
7. Writer Agent는 MCP prompt와 document renderer를 사용한다.
8. 모든 중간 상태는 AG-UI event로 UI에 표시된다.

이 흐름에서 눈여겨볼 점은 하나의 사용자 요청이 서로 다른 세 경계를 차례로 지난다는 것이다. UI 경계에서 시작해 에이전트 간 경계로 위임되고, 각 에이전트 안에서 도구 경계로 내려간다. 다음 세 절은 이 경계들을 가로지르는 관심사, 즉 어느 한 층에 속하지 않고 전체를 관통하는 문제를 다룬다.

## 횡단 관심사

인증, 관측성, 상태 영속화, 실패 격리는 특정 프로토콜 하나가 책임지지 않는다. 각 경계에서 조금씩 다르게 나타나므로, 공통 미들웨어로 끌어올려 일관되게 다루는 편이 관리하기 쉽다.

### 인증과 인가

세 프로토콜은 신뢰 모델이 다르다. MCP에서는 tool 호출과 resource 접근 권한이 중요하고, A2A에서는 원격 에이전트의 신원과 Task 권한 위임이 중요하며, AG-UI에서는 사용자 승인과 민감 정보 표시가 중요하다. 이 셋을 따로 두면 "누가 무엇을 할 권한이 있는가"가 경계마다 다른 규칙으로 갈라진다.

A2A 쪽 인증과 서명, mTLS, OIDC는 [[a2a-05-adk-integration|ADK 통합과 보안]]에서, MCP 서버의 권한·시크릿·감사 운영은 [[mcp-05-security-operations|MCP 보안과 운영]]에서 각각 구체화된다. 프로덕션에서는 사용자 신원을 UI 경계에서 확인한 뒤, 그 컨텍스트를 A2A 위임과 MCP 도구 호출까지 전파해 각 경계가 같은 주체를 기준으로 인가를 판단하도록 만든다.

### 관측성과 상관관계 ID

관측성의 핵심은 하나의 요청을 끝까지 이을 수 있는 상관관계 ID(correlation ID) 체인이다. 요청에서 Task, tool call까지 이어지는 식별자가 끊기지 않아야 한다.

```text
user_id -> session_id -> run_id -> task_id -> agent_id -> tool_call_id -> resource_uri
```

이 체인이 끊기면 사고 발생 시 "어떤 사용자의 요청 때문에 어떤 도구가 어떤 데이터에 접근했는지"를 설명하기 어렵다. UI 이벤트, 원격 에이전트 로그, 도구 호출 로그가 서로 다른 시스템에 흩어져 있어도, 이 식별자만 공유하면 하나의 감사 관점으로 묶을 수 있다.

### 상태와 Task 영속화

A2A Task는 즉시 끝나지 않을 수 있고, AG-UI run은 사용자 승인을 기다리며 멈출 수 있다. 따라서 진행 중 상태를 메모리에만 두면 백엔드 재기동이나 연결 끊김에서 작업이 사라진다. TaskState를 영속 저장소에 기록하고 task_id로 다시 조회할 수 있어야, 장시간 작업을 이어받고 push 방식으로 결과를 복구할 수 있다. run 상태도 마찬가지로 저장해, 사용자가 브라우저를 닫았다 돌아와도 진행 중인 작업을 다시 볼 수 있어야 한다.

### 실패 격리

경계가 나뉘면 실패도 나뉜다. 원격 에이전트 하나가 응답하지 않는 것, MCP 서버 하나가 오류를 반환하는 것, 사용자가 승인을 거절하는 것은 서로 다른 실패이며 서로 다른 복구가 필요하다. tool call 실패와 task 실패를 같은 에러로 뭉개면 어느 층을 재시도해야 할지 판단할 수 없다. 한 원격 에이전트나 한 MCP 서버의 장애가 Orchestrator 전체를 멈추지 않도록, 경계마다 timeout과 재시도, 대체 경로를 따로 둔다.

## 운영 신호

관측성은 대시보드 하나로 끝나지 않는다. 각 경계는 서로 다른 식별자를 남기고, 그 식별자가 이어져야 사용자 요청 하나를 끝까지 재구성할 수 있다. 경계별로 무엇을 로깅하고 무엇을 모니터링할지 미리 정한다.

| 경계 | 핵심 식별자 | 로깅 대상 | 모니터링 신호 |
|------|-------------|-----------|----------------|
| UI <-> Orchestrator (AG-UI) | session_id, run_id | run 시작/종료, 사용자 승인·거절, 표시된 tool call | run 실패율, 승인 대기 시간 |
| Orchestrator <-> Remote Agent (A2A) | task_id, agent_id | Task 생성·상태 전이, Artifact 참조 | Task 실패율, 상태별 체류 시간 |
| Agent <-> MCP Server | tool_call_id, resource_uri | tool 호출 인자·결과 크기, resource 접근 | tool 오류율, 지연, 권한 거부 수 |
| Discovery (AGNTCY / Agent Card) | agent_id | Agent Card 조회·검증, registry 변경 | 발견 실패, 서명 검증 실패 |

이 표의 원칙은 "성공/실패"만으로는 부족하다는 것이다. 최소한 session_id, run_id, task_id, agent_id, tool_call_id를 하나의 trace에 실어야, 장애가 났을 때 어느 사용자 요청이 어느 원격 에이전트의 어느 Task를 거쳐 어떤 도구를 호출했는지 되짚을 수 있다. 대시보드와 로그 축의 이름을 경계마다 통일해 두면, 장애 재현과 비용 분석이 훨씬 빨라진다.

## 구현 순서

1. 내부 API를 MCP 서버로 감싼다.
2. 단일 Orchestrator Agent가 MCP 도구를 직접 쓰는 구조로 시작한다.
3. 업무가 분리되면 전문 에이전트를 A2A로 노출한다.
4. 사용자에게 보여줄 필요가 있는 상태를 AG-UI 이벤트로 변환한다.
5. 권한/감사/관측성을 공통 middleware로 올린다.

이 순서가 중요한 이유는 처음부터 모든 표준을 도입하면 추상화가 과하기 때문이다. 먼저 도구 경계를 안정화하고, 다음 에이전트 간 경계, 마지막 사용자 경험 경계를 분리하는 편이 관리하기 쉽다. MCP 단일 에이전트부터 시작하려면 [[mcp-01-overview|MCP 개요]]와 A2A 단독 시스템 구현은 [[a2a-04-python-sdk-tutorial|A2A Python SDK 실전]]을 각각 출발점으로 삼을 수 있다.

## 배포 전 체크

프로덕션으로 옮기기 전에 각 경계가 제 책임을 다하는지 확인한다. 아래 항목은 서로 다른 신호를 본다. 한 항목이 통과해도 다른 항목이 실패할 수 있으므로 개별적으로 점검한다.

| 확인 항목 | 통과 신호 |
|-----------|-----------|
| MCP 도구 경계 | 내부 API가 MCP 서버 뒤에 있고, tool call마다 tool_call_id와 resource_uri가 로그에 남는가 |
| A2A 위임 | 원격 에이전트가 Agent Card로 능력을 노출하고, Task 상태 전이(submitted -> working -> completed/failed)가 task_id별로 조회되는가 |
| AG-UI run | 사용자 승인·인터럽트가 run 이벤트로 전달되고, 민감 정보 표시가 Policy Gate를 거치는가 |
| 상관관계 ID | user/session에서 resource_uri까지 하나의 trace로 이어져 임의 요청을 역추적할 수 있는가 |
| 상태 영속화 | 백엔드 재기동 후에도 진행 중 Task를 task_id로 이어받는가 |
| 실패 격리 | 한 원격 에이전트나 MCP 서버 장애가 Orchestrator 전체를 멈추지 않는가 |
| 에이전트 발견 | 새 에이전트 등록·해지가 코드 재배포 없이 registry 갱신으로 반영되는가 |

이 표의 목적은 "언제 완성인가"가 아니라 "무엇이 흐릿한가"를 드러내는 것이다. 다이어그램의 박스 이름보다 화살표를 본다. 어떤 요청이 어느 경계를 지나고, 그 사이에서 인증, 권한, 상태 전이, 실패가 어디에 기록되는지 확인하면 실제 운영 구조가 더 빨리 보인다.

## 참고 자료

- [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [A2A Protocol](https://a2a-protocol.org/v1.0.0/specification/)
- [AG-UI docs](https://docs.ag-ui.com/)

## 관련 문서

- [[agent-protocol-stack|Agent Protocol Stack]] - MCP·A2A·AG-UI·AGNTCY 레이어 지도, 이 글의 개념적 출발점
- [[ag-ui-realtime-events|AG-UI 실시간 이벤트]] - UI 경계, run 이벤트와 사용자 인터럽트
- [[a2a-02-specification|A2A 스펙 분석]] - 에이전트 간 경계, Task 라이프사이클과 Artifact
- [[mcp-02-server-features|MCP 서버 기능]] - 도구 경계, tool과 resource 노출
- [[agntcy-agent-discovery-trust|AGNTCY 에이전트 발견과 신뢰]] - 발견 경계, registry와 신뢰 그래프
- [[a2a-05-adk-integration|ADK 통합과 보안]] - A2A 인증·JWS 서명·mTLS·OIDC
- [[mcp-05-security-operations|MCP 보안과 운영]] - MCP 권한·시크릿·감사 운영
- [[a2a-03-vs-mcp|A2A vs MCP]] - 수평·수직 통신의 직교성
- [[a2a-04-python-sdk-tutorial|A2A Python SDK 실전]] - 단일 에이전트 협업 시스템 구현
- [[ai-agent-technology-guide|AI Agent 기술 지도]] - 에이전트 프레임워크 전반 개관
