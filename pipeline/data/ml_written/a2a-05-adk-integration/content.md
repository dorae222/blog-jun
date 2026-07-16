<!-- infographic-hero -->
![Google ADK + A2A Integration and Security 핵심 요약](figures/infographic.svg?v=layout-20260706-fix2)

*Figure: Google ADK + A2A Integration and Security 한 장 요약 인포그래픽*

# Google ADK + A2A 통합 패턴과 보안

> 시리즈 안내: 본 글은 [[a2a|A2A Protocol]] 시리즈의 5편이자 마지막 편입니다. [[a2a-01-overview|1편]]부터 [[a2a-04-python-sdk-tutorial|4편]]까지의 개념과 코드를 프로덕션 환경으로 옮깁니다. 다음 단계로는 ADK 자체를 깊게 다루는 별도 시리즈([[adk-01-local-setup|ADK 로컬 시리즈 1편]])로 연결됩니다.

![A2A ADK security layers](figures/security-four-layers.svg?v=layout-20260706-fix2)

*Figure 2: Signed Agent Card, mTLS, OIDC, sandbox를 나눈 A2A 운영 보안 4계층. (Source: A2A v1.0.0 specification 기반 자체 작성)*

:::info
2026-07 검증 기준: 본 시리즈는 A2A Protocol v1.0.0의 Agent Card, Task, Message/Part, Artifact, streaming event, push notification, JSON-RPC/gRPC/HTTP bindings를 기준으로 보강한다.
:::

## 도입: ADK는 A2A의 reference implementation

Google이 A2A를 발표한 2025년 4월, 같은 날 ADK(Agent Development Kit)도 함께 공개되었다. ADK는 단순한 SDK가 아니라 A2A 프로토콜의 reference implementation이다. 즉 ADK로 만든 에이전트는 별도 변환 없이 A2A 엔드포인트를 노출할 수 있고, 다른 ADK 또는 비-ADK 에이전트와 즉시 통신 가능하다.

본 편에서는 다음 세 가지를 다룬다.

1. ADK 에이전트를 A2A로 노출하는 패턴(`to_a2a_server`)
2. ADK-to-ADK A2A 통신 시퀀스
3. 프로덕션 보안의 4축: Signed Agent Card, mTLS, OIDC, Sandbox

## 1. ADK Agent를 A2A로 expose하기

ADK의 핵심 추상화는 `LlmAgent`다. 이를 A2A 서버로 노출하는 것은 한 줄이다.

```python
# product_agent_a2a.py
import os
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from a2a.adk import to_a2a_server

def get_product(sku: str) -> dict:
    """Fetch product information from internal catalog."""
    # 실제로는 DB나 MCP 호출
    return {"sku": sku, "name": "Sample", "price": 19.99}

product_tool = FunctionTool(get_product)

agent = LlmAgent(
    name="product_agent",
    model="gemini-2.5-pro",
    instruction=(
        "You are a product information assistant. Use get_product to fetch "
        "details by SKU and respond with structured information."
    ),
    tools=[product_tool],
)

# ADK Agent를 A2A 서버로 변환
app = to_a2a_server(
    agent=agent,
    agent_card_overrides={
        "name": "product_agent",
        "description": "Provides structured product information by SKU",
        "url": os.environ["AGENT_PUBLIC_URL"],
        "version": "1.0.0",
    },
)

# 이제 app은 ASGI 앱. uvicorn으로 띄우거나 Cloud Run에 배포
```

`to_a2a_server`가 자동으로 처리하는 것은 다음과 같다.

- Agent Card JSON 생성: tool과 instruction에서 skill 자동 추출
- Task 라이프사이클 매핑: ADK의 `Runner` 출력 이벤트를 A2A 상태/artifact로 변환
- SSE 스트리밍: ADK가 yield하는 partial response를 SSE 이벤트로 변환
- 보안 미들웨어: 환경 설정에 따라 Bearer/OIDC 토큰 검증을 자동 끼워 넣음

ADK 사용자 입장에서는 LlmAgent만 만들면 A2A 노출은 부수 효과다. 기존 ADK 코드를 거의 수정하지 않아도 멀티에이전트 시스템에 합류할 수 있다.

## 2. ADK-to-ADK A2A 통신 패턴

ADK 안에서 다른 A2A 에이전트를 호출하는 것은 도구 호출처럼 다뤄진다.

```python
# orchestrator_agent.py
from google.adk.agents import LlmAgent
from a2a.adk import A2ATool

# 다른 A2A 에이전트를 도구로 등록
research_tool = A2ATool(
    name="researcher",
    agent_url="https://researcher.example.com/a2a",
    description="Conducts research on a topic and returns structured notes",
    auth={"type": "oidc", "audience": "researcher.example.com"},
)

write_tool = A2ATool(
    name="writer",
    agent_url="https://writer.example.com/a2a",
    description="Writes a blog post from research notes",
    auth={"type": "oidc", "audience": "writer.example.com"},
)

orchestrator = LlmAgent(
    name="orchestrator",
    model="gemini-2.5-pro",
    instruction=(
        "Given a topic, first call 'researcher' to get notes, "
        "then call 'writer' with those notes to produce a blog post."
    ),
    tools=[research_tool, write_tool],
)
```

ADK 입장에서 A2A 에이전트는 그냥 `tool`이다. LlmAgent의 router(LLM)가 어느 도구를 부를지 결정하고, `A2ATool`이 내부적으로 A2A JSON-RPC 호출과 SSE 구독을 처리한다.

이 패턴의 장점은 다음과 같다.

- 동일한 ADK 멘탈 모델 안에서 local tool과 remote agent를 동등하게 다룸
- LLM이 라우팅 결정을 내리므로 새 에이전트 추가 시 코드 변경 최소
- A2A의 SSE 스트림이 ADK의 partial response stream과 자동 연결되어 end-to-end streaming 가능

### 호출 시퀀스

```text
User -> Orchestrator(ADK)         Researcher(ADK)        Writer(ADK)
  │           │                          │                     │
  │  topic    │                          │                     │
  │ ────────> │                          │                     │
  │           │  A2A: SendStreamingMessage                       │
  │           │ ───────────────────────> │                     │
  │           │ <─── SSE: working ────── │                     │
  │           │ <─── SSE: artifact ───── │                     │
  │           │ <─── SSE: completed ─── │                     │
  │           │                          │                     │
  │           │  A2A: SendStreamingMessage (notes as input)     │
  │           │ ────────────────────────────────────────────> │
  │           │ <─── SSE: working ───────────────────────── │
  │           │ <─── SSE: artifact (article.md) ──────────── │
  │           │ <─── SSE: completed ────────────────────── │
  │ <─── article ─                                              │
```

end-to-end가 모두 streaming이라 사용자는 작업 진행을 실시간으로 본다.

## 3. 프로덕션 보안의 4축

A2A로 횡단하는 호출은 신뢰 경계를 넘는다. 따라서 보안은 옵션이 아니다. 프로덕션에서 ADK + A2A는 다음 4축을 모두 채운다.

### 3-1. Signed Agent Card (JWS)

기본 Agent Card는 누구나 만들 수 있는 JSON이다. 따라서 누군가 fake URL로 가짜 능력을 광고할 수 있다. v1.0.0의 AgentCardSignature는 이 공격을 막는다.

```python
from a2a.adk import to_a2a_server
from a2a.security import SigningConfig

app = to_a2a_server(
    agent=agent,
    agent_card_overrides={...},
    signing=SigningConfig(
        # JWS 서명용 키. KMS에 두는 것이 권장
        private_key_path="/secrets/agent-signing.key",
        certificate_path="/secrets/agent-signing.crt",
        algorithm="RS256",
    ),
)
```

서명된 카드는 다음 형식을 갖는다.

```json
{
  "card": {"name": "product_agent", "url": "...", "skills": [...]},
  "signature": {
    "alg": "RS256",
    "x5c": ["<base64 cert>"],
    "value": "<base64 sig>"
  }
}
```

호출자는 서명을 검증하고 발급자(`x5c`의 issuer DN)가 신뢰 목록에 있는지 확인한다. 통과하지 못하면 호출 자체를 거부한다.

### 3-2. mTLS for Transport

mTLS는 TLS 핸드셰이크 단계에서 양쪽이 인증서를 교환한다. 인프라 layer에서 처리되므로 application 코드는 그대로 둔다. Cloud Run 배포 시 다음 설정으로 활성화한다.

```yaml
# cloud-run-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: product-agent
  annotations:
    run.googleapis.com/ingress: internal-and-cloud-load-balancing
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/client-cert-mode: "required"
    spec:
      containers:
        - image: gcr.io/proj/product-agent:v1
          env:
            - name: A2A_REQUIRE_MTLS
              value: "true"
            - name: A2A_TRUSTED_CA_BUNDLE
              value: /etc/ssl/internal-ca.pem
```

`client-cert-mode: required`는 클라이언트 인증서가 없으면 TLS 핸드셰이크 자체를 실패시킨다. application은 이미 검증된 connection만 본다.

### 3-3. OIDC for Principal Propagation

A2A 호출 체인이 깊어지면 끝단 에이전트가 "이 요청을 누가 시작했나?"를 알아야 한다. 사용자 권한 검증, 감사 로그, 데이터 격리 모두 principal에 의존한다.

OIDC ID 토큰을 A2A 호출에 첨부하면 propagation이 가능하다.

```python
# A2ATool에 OIDC 자동 첨부
from a2a.adk import A2ATool
from a2a.security import OIDCAuth

writer_tool = A2ATool(
    name="writer",
    agent_url="https://writer.example.com/a2a",
    auth=OIDCAuth(
        # 받은 토큰을 그대로 forward (downstream이 같은 trust)
        propagate_caller_token=True,
        # 또는 새 토큰을 발급해 chain claim에 caller 추가
        delegate_with_chain_claim=False,
        audience="writer.example.com",
    ),
)
```

서버 측은 토큰을 검증하고 `RequestContext.principal`에 사용자 정보를 채워 준다.

```python
async def execute(self, ctx: RequestContext, queue: EventQueue):
    user_id = ctx.principal.subject
    if not has_permission(user_id, "blog:write"):
        await queue.enqueue_status(
            TaskStatus(state=TaskState.FAILED, message="Permission denied")
        )
        return
    # ... 정상 흐름
```

### 3-4. Sandbox for External Agent Calls

내부 에이전트끼리는 신뢰 가능하지만, 외부 SaaS 에이전트(Salesforce Agentforce 등)를 호출할 때는 격리가 필요하다. ADK는 외부 호출을 sandbox role로 격리하는 기능을 제공한다.

```python
from a2a.adk import A2ATool
from a2a.security import SandboxConfig

external_tool = A2ATool(
    name="salesforce_agentforce",
    agent_url="https://agentforce.salesforce.com/a2a",
    sandbox=SandboxConfig(
        # 외부 에이전트가 새 도구를 광고해도 실행 거부
        allow_dynamic_skills=False,
        # 출력 데이터 마스킹
        redact_pii=True,
        # 호출당 최대 처리 시간
        max_duration_seconds=60,
        # 결과를 caller에게 반환하기 전 검증
        output_validator=validate_external_output,
    ),
)
```

sandbox는 외부 에이전트의 응답을 무조건 신뢰하지 않고, allowlist 기반으로 필터링한다. prompt injection을 통한 권한 상승을 막는 핵심 layer다.

## 4. 프로덕션 배포 토폴로지

GCP에서 권장되는 배포 토폴로지는 다음과 같다.

```text
                  ┌──────────────────┐
                  │  External Users  │
                  └────────┬─────────┘
                           │
                  ┌────────v─────────┐
                  │  Cloud Load      │  (mTLS termination at edge for B2B)
                  │  Balancing       │
                  └────────┬─────────┘
                           │
        ┌──────────────────┼──────────────────┐
        v                  v                  v
   ┌─────────┐       ┌─────────┐       ┌─────────┐
   │ Cloud   │       │ Cloud   │       │ Vertex  │
   │ Run     │       │ Run     │       │ AI      │
   │ Orches- │       │Reseacher│       │ Agent   │
   │ trator  │       │         │       │ Engine  │
   └────┬────┘       └────┬────┘       └────┬────┘
        │                 │                 │
        └────────┬────────┴────────┬────────┘
                 v                 v
           ┌──────────┐      ┌──────────┐
           │ Cloud    │      │ Secret   │
           │ Tasks    │      │ Manager  │
           │ (long-   │      │ (signing │
           │  running)│      │  keys)   │
           └──────────┘      └──────────┘
```

핵심 결정사항은 다음과 같다.

- **Cloud Run**: stateless 에이전트(Researcher, Orchestrator)에 최적. concurrent invocation 자동 스케일링
- **Vertex AI Agent Engine**: 장기 실행 에이전트, GPU/TPU 필요한 에이전트. 매니지드 라이프사이클 관리
- **Cloud Tasks**: long-running A2A Task의 webhook callback 큐
- **Secret Manager**: signing key, OIDC client secret 등을 Cloud Run에서 mount
- **Cloud Load Balancing**: edge에서 mTLS terminate 후 internal로 plaintext (또는 Cloud Run 내부 mTLS 유지)

장기 실행 작업은 Cloud Run의 60분 timeout을 넘을 수 있다. 이 경우 webhook 패턴으로 전환한다. Task 시작 시 작업을 Cloud Tasks 큐에 넣고, worker가 처리한 뒤 webhook으로 진행 상태를 알린다.

## 5. 관찰성과 비용 통제

A2A 호출 체인이 깊어지면 한 사용자 요청이 수십 번의 LLM 호출과 도구 호출을 거친다. 관찰성 없이는 디버깅이 불가능하다.

ADK는 OpenTelemetry를 1급 시민으로 지원하고, A2A 호출에 trace context(W3C `traceparent` header)를 자동 propagation한다.

```python
# 모든 ADK + A2A 호출이 같은 trace에 묶임
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(CloudTraceSpanExporter()))
trace.set_tracer_provider(provider)

# ADK + A2A 자동 instrumentation
from a2a.adk.observability import auto_instrument
auto_instrument()
```

Cloud Trace에서 한 사용자 요청의 전체 호출 트리(orchestrator -> researcher -> writer -> ...)를 한 화면에서 본다. 토큰 사용량과 latency가 span attribute로 자동 부착되어 비용 분석에도 활용된다.

## 6. 다음 단계

본 시리즈는 A2A 프로토콜에 집중했다. 같은 무대의 또 다른 주인공인 ADK 자체는 별도 시리즈에서 다룬다.

- [[adk-01-local-setup|ADK 로컬 시리즈 1편]]: 로컬 환경 셋업
- ADK 시리즈에서는 LlmAgent의 내부 동작, multi-agent orchestration, evaluation framework, 그리고 ADK Studio 같은 개발 도구까지 다룬다.

A2A는 통신 표준이고, ADK는 그 표준을 가장 잘 구현한 framework 중 하나다. 두 시리즈를 함께 읽으면 멀티에이전트 시스템을 처음부터 끝까지 설계할 수 있다.

## 정리

ADK + A2A의 통합은 두 가지 한 줄 결정으로 압축된다.

- 노출: `to_a2a_server(agent)` 한 줄로 ADK Agent를 A2A 서버로 변환
- 호출: `A2ATool(...)`을 도구로 등록하면 LlmAgent가 다른 A2A 에이전트를 자동 라우팅

프로덕션 보안은 4축으로 구성된다.

1. Signed Agent Card (JWS): fake card 공격 방어
2. mTLS: 트랜스포트 layer에서 양방향 인증
3. OIDC principal propagation: 사용자 권한이 chain 끝까지 유지
4. Sandbox: 외부 에이전트 호출 시 격리와 출력 검증

배포는 Cloud Run + Vertex AI Agent Engine + Cloud Tasks의 조합이 권장 토폴로지다. OpenTelemetry로 end-to-end trace를 자동 수집해 디버깅과 비용 분석을 단일 화면에서 한다.

5편 시리즈는 여기서 마무리된다. 표준의 등장 배경에서 시작해, 스펙을 분해하고, [[mcp|MCP]]와의 직교성을 확인했고, Python SDK로 구현했고, 프로덕션 보안과 배포까지 살폈다. 다음 단계는 [[adk-01-local-setup|ADK 로컬 시리즈]]에서 framework 자체를 깊이 다루는 것이다.

## 배포 전 보안 체크

시리즈를 닫기 전에, 본문의 4축을 "배포 직전 확정해야 하는 결정"으로 다시 세운다. 4축은 서로 다른 계층을 막기 때문에 하나를 통과했다고 나머지가 자동으로 채워지지 않는다. 그래서 확인하는 신호도 항목마다 다르다.

| 결정 | 확정할 것 | 통과 신호 |
|------|-----------|-----------|
| Agent Card 서명 검증 (JWS) | 호출 전에 카드 서명을 검증하고 발급자를 신뢰 목록과 대조할지 | 서명이 없거나 `x5c`의 issuer DN이 목록 밖인 카드에 대해 호출 자체가 거부되고, 그 거부가 로그에 남는가 |
| 전송 보안 (mTLS/TLS) | edge와 내부 홉 중 어디까지 클라이언트 인증서를 강제할지 | `client-cert-mode: required` 상태에서 인증서 없는 연결이 애플리케이션에 닿기 전 TLS 핸드셰이크 단계에서 끊기는가 |
| 인증 (OAuth2/OIDC) | caller 토큰을 그대로 forward할지 chain claim으로 재발급할지 | 끝단 에이전트의 `RequestContext.principal.subject`가 실제 요청자로 채워지고, 권한 없는 subject의 Task가 FAILED로 떨어지는가 |
| 권한 경계 (sandbox) | 외부 에이전트 호출을 어떤 격리 role로 감쌀지 | 외부 응답이 `output_validator`와 `redact_pii`를 거치고, 응답에 광고된 동적 skill이 실행 거부되는가 |

통과 신호는 문서상 설정 존재 여부가 아니라 실제 런타임 동작으로 확인한다. 예를 들어 서명 검증은 config에 키 경로가 적혀 있는지가 아니라, 위조 카드를 넣었을 때 요청이 시작조차 못 하는지로 판단한다.

## 흔한 보안 실패

본문에서 짚은 실패는 대부분 기술 선택이 아니라 신뢰 경계를 흐린 데서 시작한다.

- **서명되지 않은 Agent Card를 그대로 신뢰한다.** 카드는 누구나 만들 수 있는 JSON이므로, 검증 없이 URL이 광고하는 능력을 믿으면 fake card가 신뢰 경계 안으로 들어온다. JWS 검증을 호출 직전 게이트로 둔다.
- **내부 에이전트를 신뢰 경계 밖에 그대로 노출한다.** 내부용 stateless 에이전트를 external ingress로 열면 mTLS와 OIDC를 건너뛴 호출이 도달한다. Cloud Run ingress 설정과 `client-cert-mode`로 경계를 먼저 못박는다.
- **외부 에이전트를 sandbox 없이 호출한다.** 외부 SaaS 에이전트의 응답을 무조건 신뢰하면 prompt injection을 통한 권한 상승이나 PII 유출로 이어진다. `SandboxConfig`의 allowlist와 출력 검증을 통과한 결과만 caller에게 돌려준다.
- **호출 체인이 깊어지며 principal이 사라진다.** OIDC propagation 없이 홉을 넘으면 끝단에서 "누가 이 요청을 시작했나"를 잃어, 사용자 권한 검증과 감사 로그가 함께 무너진다.

이 4축과 실패 패턴을 배포 직전 체크리스트로 고정하면, 시리즈 내내 쌓은 개념이 코드가 아니라 신뢰 경계의 언어로 정리된다. A2A 시리즈는 여기서 마친다. 표준의 등장 배경에서 프로덕션 보안까지, 다섯 편을 관통한 질문은 결국 "어느 홉에서 무엇을 신뢰하는가"였다.

## 관련 문서

- [[a2a|A2A Protocol]] - 시리즈 메인 엔트리
- [[a2a-01-overview|A2A 등장 배경]] - 1편, 표준이 필요한 이유
- [[a2a-02-specification|A2A 스펙 분석]] - 2편, AgentCardSignature와 SecurityScheme 원본 정의
- [[a2a-03-vs-mcp|A2A vs MCP]] - 3편, 수평·수직 통신의 경계
- [[a2a-04-python-sdk-tutorial|A2A Python SDK 실전]] - 4편, 이 글이 프로덕션으로 옮긴 구현
- [[mcp-05-security-operations|MCP 보안과 운영]] - 도구 계층의 서명·권한·운영, 같은 관점을 수직 통신에 적용
- [[agent-protocol-production-reference|Agent Protocol 프로덕션 레퍼런스]] - 배포·관찰성·보안 체크의 통합 참조
- [[agent-protocol-stack|Agent Protocol Stack]] - MCP·A2A·AG-UI·AGNTCY 레이어 지도
