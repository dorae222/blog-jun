<!-- infographic-hero -->
![A2A Specification Deep Dive 핵심 요약](figures/infographic.svg)

*Figure: A2A Specification Deep Dive 한 장 요약 인포그래픽*

# A2A 스펙 분석: Agent Card / Task / JSON-RPC 2.0 / gRPC

> 시리즈 안내: 본 글은 [[a2a|A2A Protocol]] 시리즈의 2편입니다. [[a2a-01-overview|1편 등장 배경]]에서 표준의 필요성을 다뤘다면, 본 편은 스펙 자체를 분해합니다. [[a2a-03-vs-mcp|3편]], [[a2a-04-python-sdk-tutorial|4편]], [[a2a-05-adk-integration|5편]]으로 이어집니다.

## 도입: 스펙을 세 축으로 보기

A2A 스펙은 분량이 크지만 핵심은 세 축이다.

1. **Agent Discovery**: 에이전트가 자신의 능력을 어떻게 광고하는가 -> Agent Card
2. **Task Management**: 에이전트가 받은 일을 어떻게 추적하는가 -> Task 라이프사이클
3. **Transport**: 메시지를 어떻게 전송하는가 -> JSON-RPC 2.0, gRPC, SSE

이 세 축을 차례로 보면 스펙 전체가 보인다. 본 편에서는 각 축을 실제 페이로드 예시와 함께 분해한다.

## 1. Agent Card: 능력의 자기 서술

Agent Card는 에이전트가 "나는 누구이고 무엇을 할 수 있다"를 선언하는 JSON 문서다. 관례적으로 `https://agent.example.com/.well-known/agent.json` 경로에서 GET으로 가져올 수 있다. RFC 8615의 well-known URI 패턴을 따른다.

### 최소 필드

```json
{
  "name": "research_agent",
  "description": "Conducts deep web research and produces structured reports",
  "url": "https://research.example.com/a2a",
  "version": "1.4.0",
  "protocol_version": "1.1",
  "capabilities": {
    "streaming": true,
    "push_notifications": true,
    "state_transition_history": true
  },
  "default_input_modes": ["text/plain", "application/json"],
  "default_output_modes": ["text/plain", "application/json", "text/markdown"],
  "skills": [
    {
      "id": "web_research",
      "name": "Web Research",
      "description": "Search and synthesize information from the web",
      "tags": ["research", "web", "synthesis"],
      "examples": [
        "Find the top 5 papers on test-time compute scaling published in 2025"
      ]
    }
  ],
  "security_schemes": {
    "bearer": {
      "type": "http",
      "scheme": "bearer",
      "bearer_format": "JWT"
    }
  },
  "security": [{"bearer": []}]
}
```

각 필드의 의미는 다음과 같다.

- `name`, `description`: 사람과 LLM이 읽을 식별자. LLM 라우팅이 description을 본다
- `url`: A2A 엔드포인트의 base URL. 모든 RPC 호출이 여기로 향함
- `protocol_version`: A2A 스펙 자체의 버전. 1.0은 2025-12, 1.1은 2026-03
- `capabilities`: 옵션 기능 선언. streaming(SSE 지원), push_notifications(webhook 지원)
- `skills`: 사람이 부를 수 있는 능력 목록. tag와 example로 검색 가능
- `security_schemes`, `security`: OpenAPI 3.0과 동일한 보안 정의 형식 채택

### Signed Agent Card (2026)

2026-03 v1.1에서 도입된 Signed Agent Card는 Agent Card 자체에 X.509 서명을 첨부한다. 형식은 JWS(JSON Web Signature)를 따르고, 검증자는 서명을 통해 발급자(에이전트 운영자)와 무결성을 모두 확인한다. 외부 에이전트 호출 시 fake Agent Card 공격을 막는 핵심 메커니즘이다. 자세한 보안 토픽은 [[a2a-05-adk-integration|5편]]에서 다룬다.

## 2. Task: 일의 단위와 라이프사이클

A2A에서 일의 단위는 단순한 RPC 응답이 아니라 Task 객체다. Task는 ID를 가지며, 시간이 흘러가는 동안 상태가 바뀐다.

### 상태 머신

```text
                    ┌──────────────┐
                    │   submitted  │  (초기 상태)
                    └──────┬───────┘
                           v
                    ┌──────────────┐
        ┌──────────>│   working    │
        │           └──┬─────────┬─┘
        │              v         v
        │   ┌─────────────┐   ┌──────────────┐
        │   │input-required│  │   completed  │
        │   └──────┬──────┘   └──────────────┘
        │          │
        └──────────┘
                           
        any state ──> failed | cancelled
```

상태는 6가지다.

- `submitted`: 클라이언트가 Task를 보냈고 서버가 수신함
- `working`: 에이전트가 처리 중
- `input-required`: 추가 입력이 필요함. 사용자나 다른 에이전트의 응답을 기다림
- `completed`: 정상 종료
- `failed`: 에러로 종료
- `cancelled`: 외부에서 취소됨

`input-required`는 long-running 시나리오에서 핵심이다. 예를 들어 에이전트가 "이 견적을 승인할까요?"라고 사람에게 묻고 며칠을 대기할 수 있다. 그동안 Task는 메모리에서 사라지지 않고 같은 ID로 다시 깨어난다.

### Task 페이로드 구조

```json
{
  "id": "task-7f3c2a91",
  "session_id": "sess-9d4e",
  "status": {
    "state": "working",
    "timestamp": "2026-04-15T10:23:11Z"
  },
  "history": [
    {
      "role": "user",
      "parts": [
        {"type": "text", "text": "Summarize the attached PDF"},
        {"type": "file", "file": {"name": "report.pdf", "mime_type": "application/pdf", "uri": "s3://bucket/report.pdf"}}
      ]
    },
    {
      "role": "agent",
      "parts": [
        {"type": "text", "text": "I will read the file and produce a summary in 5 bullets."}
      ]
    }
  ],
  "artifacts": [
    {
      "name": "summary.md",
      "parts": [{"type": "text", "text": "# Summary\n- ..."}]
    }
  ],
  "metadata": {"priority": "normal"}
}
```

핵심 구조는 다음과 같다.

- **Multipart message**: 한 메시지에 여러 part(text, file, structured data)를 동시 첨부 가능
- **History**: 사용자와 에이전트의 모든 turn을 누적. 클라이언트가 polling 시 전체 history를 받음
- **Artifacts**: 에이전트가 생성한 산출물. 단순 텍스트 응답이 아닌 파일, 보고서, 차트 데이터 등을 명시적으로 분리
- **Session**: 여러 Task를 묶는 상위 개념. 같은 사용자의 연속 요청을 같은 session 안에 둠

이 구조 덕에 "수업 계획서 PDF를 받아 요약하고 슬라이드 PNG로 변환해 줘"같은 다중 모달 요청도 자연스럽게 표현된다.

## 3. Transport: JSON-RPC 2.0과 gRPC

### JSON-RPC 2.0 (1차 트랜스포트)

A2A의 1차 트랜스포트는 HTTPS + JSON-RPC 2.0이다. 모든 메서드는 단일 엔드포인트(POST /a2a)에 JSON-RPC 호출을 보내는 형식이다.

```json
POST /a2a HTTP/1.1
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tasks/send",
  "params": {
    "id": "task-7f3c2a91",
    "session_id": "sess-9d4e",
    "message": {
      "role": "user",
      "parts": [{"type": "text", "text": "Find papers on RAG"}]
    }
  }
}
```

응답은 일반적인 JSON-RPC 2.0 응답이다.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "task-7f3c2a91",
    "status": {"state": "submitted", "timestamp": "2026-04-15T10:00:00Z"}
  }
}
```

표준 메서드는 다음과 같다.

| 메서드 | 역할 |
|--------|------|
| `tasks/send` | Task 생성 또는 메시지 추가 |
| `tasks/get` | 현재 상태와 history 조회 |
| `tasks/cancel` | Task 취소 |
| `tasks/sendSubscribe` | Task 생성 + SSE 스트림 구독 |
| `tasks/pushNotification/set` | webhook 등록 |
| `tasks/pushNotification/get` | 등록된 webhook 조회 |

### gRPC (확장 트랜스포트)

JSON-RPC가 텍스트 기반이라 페이로드 크기와 latency에 민감한 환경에서는 gRPC 트랜스포트를 선택할 수 있다. v1.1부터 공식 지원되며, proto 정의는 다음과 같다.

```proto
service A2AService {
  rpc SendTask(SendTaskRequest) returns (Task);
  rpc GetTask(GetTaskRequest) returns (Task);
  rpc CancelTask(CancelTaskRequest) returns (Task);
  rpc StreamTask(SendTaskRequest) returns (stream TaskUpdate);
}
```

JSON-RPC와 gRPC는 의미적으로 동일한 메서드를 노출한다. Agent Card의 `transport` 필드(또는 별도 endpoint URL)로 어느 트랜스포트를 지원하는지 광고한다.

## 4. Streaming과 Push Notification

장시간 실행 작업은 두 가지 방식으로 진행 상황을 전달한다.

### SSE (Server-Sent Events)

`tasks/sendSubscribe` 메서드는 단일 HTTP 응답으로 SSE 스트림을 연다. 서버는 상태 변경마다 이벤트를 푸시한다.

```text
HTTP/1.1 200 OK
Content-Type: text/event-stream

event: status
data: {"id":"task-7f3c2a91","status":{"state":"working","timestamp":"..."}}

event: artifact
data: {"id":"task-7f3c2a91","artifact":{"name":"draft.md","parts":[...]}}

event: status
data: {"id":"task-7f3c2a91","status":{"state":"completed","timestamp":"..."}}
```

클라이언트는 EventSource(웹) 또는 SSE 라이브러리(Python `httpx-sse`)로 받는다. 짧은 작업과 실시간 표시에 적합하다.

### Push Notification (Webhook)

며칠짜리 작업은 SSE 연결을 유지하기 어렵다. `tasks/pushNotification/set`으로 webhook URL을 등록하면, 서버는 상태 변경 시 그 URL로 POST를 보낸다.

```json
{
  "method": "tasks/pushNotification/set",
  "params": {
    "id": "task-7f3c2a91",
    "push_notification_config": {
      "url": "https://client.example.com/webhooks/a2a",
      "token": "wh_secret_xxx",
      "authentication": {"schemes": ["bearer"]}
    }
  }
}
```

webhook 인증을 위해 token을 미리 교환한다. 클라이언트는 들어오는 알림이 올바른 토큰을 가졌는지 검증한다.

## 5. Authentication: 다층 보안

A2A는 인증을 옵션이 아니라 기본으로 한다. 지원하는 방식은 OpenAPI 3.0의 보안 스키마와 호환된다.

### Bearer Token

가장 단순. JWT나 opaque token을 `Authorization: Bearer <token>`으로 전달.

```yaml
security_schemes:
  bearer:
    type: http
    scheme: bearer
    bearer_format: JWT
```

### OAuth 2.0

Authorization Code, Client Credentials 등 표준 grant 흐름 모두 지원. 외부 SaaS와 통합 시 주류.

```yaml
security_schemes:
  oauth:
    type: oauth2
    flows:
      client_credentials:
        token_url: https://auth.example.com/token
        scopes:
          read:tasks: View task status
          write:tasks: Create tasks
```

### mTLS (Mutual TLS)

엔터프라이즈 내부 통신에서는 mTLS를 사용해 양방향 인증서 검증. 인프라 layer에서 처리되어 application 코드는 단순함.

### Signed Agent Card + OIDC Principal

v1.1에서 추가된 패턴. Agent Card 자체에 X.509 서명을 붙여 발급자를 확인하고, 호출 시 OIDC ID 토큰으로 사용자 principal을 propagation한다. 다단계 호출에서 사용자 권한이 끝까지 유지된다. 자세한 내용은 [[a2a-05-adk-integration|5편]]에서 다룬다.

## 6. 페이로드 한 번에 보기: 호출 시퀀스

전체 흐름을 한 번에 보면 다음과 같다.

```text
Client                                  Agent
  │                                       │
  │  GET /.well-known/agent.json          │
  │ ────────────────────────────────────> │
  │ <──────────────── Agent Card ──────── │
  │                                       │
  │  POST /a2a (tasks/sendSubscribe)      │
  │ ────────────────────────────────────> │
  │ <──── 200 SSE: state=submitted ────── │
  │ <──── SSE: state=working ──────────── │
  │ <──── SSE: artifact updated ───────── │
  │ <──── SSE: state=input-required ───── │
  │                                       │
  │  POST /a2a (tasks/send, same id)      │
  │  with user response                   │
  │ ────────────────────────────────────> │
  │ <──── SSE: state=working ──────────── │
  │ <──── SSE: state=completed ────────── │
  │ <──── stream closed ───────────────── │
```

이 흐름은 4편 Python SDK 튜토리얼에서 코드로 구현한다.

## 정리 + 다음 편

A2A 스펙은 세 축으로 압축된다.

- **Agent Card**: well-known URI에 놓인 JSON 문서로 능력을 자기 서술. v1.1부터 X.509 서명 가능
- **Task**: 6단계 상태 머신과 multipart message + artifact 구조로 long-running 작업 모델링
- **Transport**: HTTPS + JSON-RPC 2.0 1차, gRPC 확장. SSE와 webhook으로 진행 상황 전달

이 세 축이 OpenAPI, JSON-RPC 2.0, OAuth 2.0 같은 검증된 웹 표준 위에 합성되어 있다. 새로 발명한 부분이 거의 없다.

다음 [[a2a-03-vs-mcp|3편]]에서는 A2A와 [[mcp|MCP]]의 직교성을 코드 예제로 비교한다. 두 프로토콜이 어떻게 한 시스템 안에서 함께 쓰이는지, 어느 경우에 어느 프로토콜을 선택해야 하는지 정리한다.

## 관련 문서

- [[a2a|A2A Protocol]] - 메인 엔트리
- [[a2a-01-overview|A2A 등장 배경]] - 이전 편
- [[a2a-03-vs-mcp|A2A vs MCP]] - 다음 편
- [[mcp|MCP]] - 도구 통신 프로토콜
- [[a2a-04-python-sdk-tutorial|A2A Python SDK 실전]] - 구현 튜토리얼
- [[a2a-05-adk-integration|ADK + A2A]] - 보안과 프로덕션 배포
