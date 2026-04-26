<!-- infographic-hero -->
![ADK Evaluation, Tracing, and Debugging 핵심 요약](figures/infographic.svg)

*Figure: ADK Evaluation, Tracing, and Debugging 한 장 요약 인포그래픽*

# ADK 평가 / 트레이싱 / 디버깅

> 본 글은 **ADK 로컬 개발 시리즈(adk-local-development)** 마지막 4편입니다.
>
> - [[adk-01-local-setup|1편: ADK 로컬 환경 셋업]]
> - [[adk-02-multi-agent-workflow|2편: ADK 멀티에이전트 워크플로우]]
> - [[adk-03-litellm-ollama|3편: ADK + LiteLLM + Ollama]]
> - 4편(현재 글): 평가 / 트레이싱 / 디버깅
>
> 1-3편이 "어떻게 만드는가"였다면 이번 편은 "어떻게 신뢰할 수 있게 운영하는가"입니다.

## 개요

LLM 에이전트는 두 가지 측면에서 전통적인 소프트웨어와 다릅니다.

1. **비결정성**: 같은 입력에 대해 같은 출력을 보장하지 않음
2. **다단계 의사결정**: 한 turn 안에서 LLM이 여러 도구를 부르고 sub-agent에 위임

이 두 특성 때문에 단위 테스트(`assert output == expected`)만으로는 회귀를 잡기 어렵고, 한 번의 print 디버깅으로 원인을 찾기도 어렵습니다. ADK는 이 문제를 다음 4축으로 해결합니다.

| 축 | 도구 | 목적 |
|----|------|------|
| Trace | 자동 OpenTelemetry 기록 | 무엇이, 언제, 얼마나 걸렸나 |
| Eval | EvalSet + AgentEvaluator + `adk eval` | 회귀 방지 |
| Debug | before_model / after_tool callbacks | step-by-step 검증 |
| Deploy | `adk deploy` → Cloud Run / Agent Engine | 프로덕션 운영 |

## 자동 트레이싱: ADK의 첫 번째 선물

ADK는 모든 실행을 자동으로 트레이싱합니다. 별도 설정 없이 다음이 기록됩니다.

- **LLM call**: 모델, 입력 토큰, 출력 토큰, 지연 시간, 시스템 프롬프트
- **Tool call**: 도구명, 인자, 반환값, 예외, 지연 시간
- **Sub-agent invocation**: 부모 → 자식 위임 관계, state delta
- **Event log**: 사용자 메시지부터 모델 응답까지 시간순 흐름

`adk web`으로 실행하면 이 모든 정보가 우측 trace 패널에 트리 형태로 표시됩니다. 한 turn을 클릭하면 해당 turn에서 호출된 LLM/tool/sub-agent가 들여쓰기 트리로 보입니다.

### OpenTelemetry export

로컬 trace로는 부족할 때 OTLP로 외부 컬렉터에 보낼 수 있습니다.

```python
# bootstrap.py - 에이전트 실행 전에 import
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
exporter = OTLPSpanExporter(endpoint="http://otel-collector:4317", insecure=True)
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)
```

이 설정만 있으면 모든 ADK 이벤트가 자동으로 Cloud Trace, Jaeger, Tempo, Grafana, LangSmith, Phoenix 등으로 송출됩니다. ADK 내부에서 별도 trace 코드를 추가할 필요가 없습니다.

### Cloud Trace 통합 (Vertex AI 환경)

Vertex AI Agent Engine으로 배포하면 Cloud Trace가 기본 활성화됩니다.

```bash
# 환경 변수만 설정하면 됨
export GOOGLE_CLOUD_PROJECT=your-project
export GOOGLE_GENAI_USE_VERTEXAI=TRUE

adk deploy agent_engine ./my_agent
```

GCP 콘솔의 Trace 페이지에서 turn별 latency 분포, error rate, p50/p95/p99를 즉시 확인할 수 있습니다.

## EvalSet과 회귀 평가

에이전트 회귀 테스트의 본질은 "원래 잘 풀던 케이스를 여전히 풀 수 있는가?"입니다. ADK는 이를 위해 EvalSet 포맷과 `adk eval` CLI를 제공합니다.

### EvalSet 정의

EvalSet은 JSON 파일로 작성합니다. 각 케이스는 사용자 입력, 기대 출력, 기대 도구 호출 trajectory를 가집니다.

```json
{
  "eval_set_id": "weather_basic",
  "name": "weather_basic",
  "eval_cases": [
    {
      "eval_id": "case_seoul",
      "conversation": [
        {
          "user_content": {
            "parts": [{"text": "서울 날씨 알려줘"}]
          },
          "final_response": {
            "parts": [{"text": "서울은 18도, 부분적으로 흐림입니다."}]
          },
          "intermediate_data": {
            "tool_uses": [
              {
                "name": "get_weather",
                "args": {"city": "Seoul"}
              }
            ]
          }
        }
      ]
    }
  ]
}
```

평가 기준은 두 가지입니다.

1. **Trajectory match**: 기대한 도구가 기대한 인자로 호출됐는가
2. **Response match**: 최종 응답이 기대 응답과 충분히 유사한가(LLM-as-judge)

### CLI로 실행

```bash
adk eval ./my_agent ./evals/weather_basic.evalset.json
```

출력 예:

```text
Running 1 eval case(s)...

case_seoul: PASS
  trajectory_score: 1.00
  response_score:   0.92

Summary: 1/1 passed (100%)
Avg trajectory: 1.00
Avg response:   0.92
```

### 프로그래매틱 사용

CI 통합용으로 Python에서 직접 호출합니다.

```python
# tests/test_agent_eval.py
import pytest
from google.adk.evaluation import AgentEvaluator


@pytest.mark.asyncio
async def test_weather_basic():
    await AgentEvaluator.evaluate(
        agent_module="my_agent",
        eval_dataset_file_path_or_dir="./evals/weather_basic.evalset.json",
        num_runs=3,  # 비결정성 흡수를 위해 여러 번 실행 후 평균
    )
```

GitHub Actions 같은 CI에 `pytest tests/`만 추가하면, PR이 들어올 때마다 회귀가 자동 감지됩니다.

### LLM-as-judge

응답 매칭은 단순 string 비교가 아닙니다. ADK는 내부적으로 judge LLM을 띄워 "기대 응답과 실제 응답이 의미적으로 일치하는가"를 0-1 점수로 매깁니다. 기본 judge는 Gemini이고, 임계치는 EvalSet의 `criteria`로 조절합니다.

```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0,
    "response_match_score": 0.8
  }
}
```

이 임계치를 통과하지 못하면 case는 FAIL로 표시됩니다.

## Callback 기반 디버깅

trace는 사후 분석에 좋지만, "이 turn에서 모델 입력을 가로채서 수정"이나 "이 도구 호출 결과를 검증"이 필요할 때는 callback을 씁니다. ADK는 5가지 hook 포인트를 제공합니다.

| Callback | 시점 | 활용 |
|----------|------|------|
| `before_model_callback` | LLM 호출 직전 | 프롬프트 검열, 토큰 절약 |
| `after_model_callback` | LLM 응답 직후 | 출력 후처리, PII 마스킹 |
| `before_tool_callback` | 도구 호출 직전 | 인자 검증, rate limiting |
| `after_tool_callback` | 도구 응답 직후 | 결과 변환, 캐싱 |
| `before_agent_callback` | 에이전트 진입 시 | 인증, 사용자 컨텍스트 주입 |

예시: 위험한 SQL을 실행 전에 차단.

```python
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext


def block_destructive_sql(callback_context: CallbackContext, tool, args, tool_context):
    if tool.name != "execute_sql":
        return None
    sql = args.get("query", "").lower()
    if any(kw in sql for kw in ["drop ", "delete ", "truncate "]):
        return {
            "status": "blocked",
            "reason": "Destructive SQL is not allowed.",
        }
    return None  # None = 정상 진행


agent = LlmAgent(
    name="db_agent",
    model="gemini-2.5-flash",
    tools=[execute_sql],
    before_tool_callback=block_destructive_sql,
)
```

callback이 `None`이 아닌 값을 반환하면 ADK는 그 값을 도구의 응답으로 사용하고 실제 도구는 호출하지 않습니다. 이 메커니즘으로 가드레일, A/B 테스트, mocking을 모두 구현할 수 있습니다.

### State inspection

각 step에서 session.state 스냅샷을 직접 들여다보고 싶다면:

```python
def log_state(callback_context: CallbackContext) -> None:
    print("[BEFORE]", dict(callback_context.state.to_dict()))
    return None


agent = LlmAgent(
    name="researcher",
    model="gemini-2.5-flash",
    before_agent_callback=log_state,
    ...
)
```

state는 모든 멀티에이전트 패턴의 데이터 통신 채널이므로, "왜 다음 에이전트가 빈 값을 받지?"를 추적하는 가장 빠른 방법은 step별 state를 찍어보는 것입니다.

## 디버깅 워크플로우 권장 순서

장애가 났을 때 권장 순서는 다음과 같습니다.

1. **`adk web` trace 패널** 열기, 실패 turn의 트리 구조 확인
2. 빨간 이벤트(예외, 도구 실패) 찾기
3. 해당 LLM call의 입력 프롬프트 그대로 복사 → Gemini Studio/플레이그라운드에서 재현
4. 모델 출력에 문제 → instruction 또는 모델 변경
5. 도구 출력에 문제 → callback으로 가로채기 또는 단위 테스트
6. state 누락 → before/after callback으로 step별 state 출력
7. 한 케이스로 EvalSet에 추가 → 다음 회귀 차단

## 프로덕션 배포

로컬 `adk web`은 개발 전용입니다. 운영 옵션은 다음과 같습니다.

### 1. Cloud Run

가장 가벼운 옵션. ADK가 Dockerfile과 FastAPI 래퍼를 자동 생성합니다.

```bash
adk deploy cloud_run \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=us-central1 \
  --service_name=my-agent \
  ./my_agent
```

자동으로 다음을 처리합니다.

- Dockerfile 생성 (`adk api_server` 진입점)
- Artifact Registry 이미지 빌드
- Cloud Run 서비스 생성
- IAM 인증 옵션

### 2. GKE / Kubernetes

자체 클러스터를 가진 조직에서는 위 Dockerfile을 받아 Helm 차트나 Kustomize로 배포합니다. ADK 컨테이너는 stateless이므로 HPA로 수평 확장 가능합니다.

### 3. Vertex AI Agent Engine (Reasoning Engine)

Vertex AI에 통합되어 다음을 자동 제공합니다.

- 세션 영속화 (Cloud Storage / Firestore)
- 자동 trace → Cloud Trace
- IAM 통합 인증
- A2A 엔드포인트 자동 노출

```bash
adk deploy agent_engine \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=us-central1 \
  ./my_agent
```

배포 후 reasoning_engine_id를 받으면, 다른 ADK 에이전트가 RemoteAgent로 호출할 수 있습니다.

### 비교

| 항목 | Cloud Run | GKE | Agent Engine |
|------|-----------|-----|--------------|
| 셋업 난이도 | 낮음 | 높음 | 매우 낮음 |
| 비용 | 사용량 기반 | 노드 비용 고정 | 사용량 기반 |
| 세션 영속화 | 직접 구현 | 직접 구현 | 자동 |
| 트레이스 | OTLP 직접 설정 | OTLP 직접 설정 | Cloud Trace 자동 |
| A2A 노출 | 직접 구현 | 직접 구현 | 자동 |
| 권장 사용처 | MVP, 단일 서비스 | 멀티 테넌트 | 프로덕션 멀티에이전트 |

## A2A 통합으로 가는 길

ADK 에이전트를 외부 시스템이 호출하게 하려면 A2A 프로토콜로 노출합니다. ADK는 이를 위한 `to_a2a_server` 헬퍼를 제공해 단 한 줄로 LlmAgent를 A2A 서버로 변환합니다.

```python
from google.adk.a2a import to_a2a_server

a2a_app = to_a2a_server(root_agent)
# 이제 uvicorn으로 실행하면 표준 A2A 엔드포인트 노출
```

자세한 통합 패턴, Agent Card 서명, mTLS, OIDC 전파 같은 보안 토픽은 [[a2a-05-adk-integration|A2A + ADK 통합 패턴과 보안]] 편에서 다룹니다. ADK 시리즈와 A2A 시리즈는 다음 관계로 보면 명확합니다.

- ADK 시리즈: "**개별 에이전트 시스템**을 어떻게 만들고 운영하는가"
- A2A 시리즈: "**여러 에이전트 시스템 사이의 통신**을 어떻게 표준화하는가"

## 시리즈 종합 정리

본 ADK 로컬 개발 시리즈에서 다룬 내용을 한 표로 압축합니다.

| 편 | 핵심 토픽 | 결론 |
|----|-----------|------|
| 1편 | 설치, 첫 에이전트, 3가지 실행 모드 | `pip install google-adk`로 5분 만에 시작 |
| 2편 | Sequential / Parallel / Loop / Custom | 결정적 orchestration + LLM leaf 하이브리드 |
| 3편 | LiteLLM + Ollama, air-gapped | 모델은 교체 가능한 부품, 100여 개 백엔드 지원 |
| 4편 | Trace, Eval, Callback, Deploy | 비결정 시스템도 회귀 테스트 가능 |

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| 평가 점수가 매번 다름 | 비결정성 | `num_runs` 늘리기, 임계치 완화 |
| trace 누락 | OTLP exporter 미설정 | bootstrap에서 TracerProvider 등록 |
| callback이 호출되지 않음 | 잘못된 hook 위치 | tool callback은 LlmAgent에만 등록 |
| Cloud Run 배포 실패 | 권한 부족 | run.admin, artifactregistry.writer 권한 확인 |
| Agent Engine 세션 분실 | 세션 ID 미일치 | 클라이언트 측에서 동일 session_id 재사용 |

## 정리

ADK는 단순한 "LLM 래퍼"가 아니라 **에이전트 시스템 운영 프레임워크**입니다. trace, eval, callback, deploy의 4축이 처음부터 통합되어 있어, 데모를 만든 그날부터 프로덕션 readiness를 향한 점진적 개선이 가능합니다.

다음에 무엇을 할 것인가:

- [[a2a-05-adk-integration|A2A + ADK 통합]]으로 외부 시스템에 노출
- [[a2a-04-python-sdk-tutorial|A2A Python SDK 튜토리얼]]로 클라이언트 작성
- 자체 에이전트에 EvalSet 100개 채워보기 → CI에 통합
- LiteLLM Proxy로 멀티 모델 라우팅 운영

ADK는 빠르게 진화 중입니다. GitHub `google/adk-python` 저장소의 릴리즈 노트와 `google/adk-web` UI 변경사항을 주기적으로 확인하시기를 권장합니다.

## 관련 문서

- [[adk-01-local-setup|ADK 로컬 환경 셋업]] - 시리즈 1편
- [[adk-02-multi-agent-workflow|ADK 멀티에이전트 워크플로우]] - 시리즈 2편
- [[adk-03-litellm-ollama|ADK + LiteLLM + Ollama]] - 시리즈 3편, 로컬 LLM
- [[a2a-01-overview|A2A 프로토콜 개요]] - 에이전트 간 통신 표준
- [[a2a-04-python-sdk-tutorial|A2A Python SDK 튜토리얼]] - A2A 클라이언트 작성
- [[a2a-05-adk-integration|A2A + ADK 통합 패턴과 보안]] - 짝을 이루는 통합 가이드
