<!-- infographic-hero -->
![ADK Local Setup: adk web / adk run / API Server 핵심 요약](figures/infographic.svg)

*Figure: ADK Local Setup: adk web / adk run / API Server 한 장 요약 인포그래픽*

# ADK 로컬 환경 셋업: adk web / adk run / API Server

> 본 글은 **ADK 로컬 개발 시리즈(adk-local-development)** 1편입니다. 시리즈 전체:
>
> - 1편(현재 글): 로컬 환경 셋업
> - [[adk-02-multi-agent-workflow|2편: 멀티에이전트 워크플로우 - Sequential / Parallel / Loop / Custom]]
> - [[adk-03-litellm-ollama|3편: ADK + LiteLLM + Ollama - 로컬 LLM 통합과 air-gapped 환경]]
> - [[adk-04-evaluation-tracing|4편: ADK 평가 / 트레이싱 / 디버깅]]
>
> 그리고 A2A 시리즈의 마지막 편 [[a2a-05-adk-integration|A2A + ADK 통합 패턴과 보안]]과 짝을 이룹니다. A2A는 "에이전트 간 통신 프로토콜", ADK는 "그 에이전트를 만드는 SDK"의 관점으로 함께 읽으면 가장 효과적입니다.

## 개요

Google ADK(Agent Development Kit)는 2025년에 오픈소스로 공개된 에이전트 개발 프레임워크입니다. Vertex AI Agent Builder, Gemini, A2A 프로토콜 같은 Google 생태계와 일급으로 통합되지만, 동시에 LiteLLM 어댑터를 통해 OpenAI, Anthropic, Ollama 등 거의 모든 LLM 백엔드를 받아들이는 model-agnostic 구조를 가집니다.

기존의 LangChain, LlamaIndex, CrewAI 같은 프레임워크가 "체인 / 워크플로우 / 멀티에이전트" 중 하나에 강점을 가졌다면, ADK는 처음부터 production 멀티에이전트 시스템을 염두에 두고 설계되었습니다. 즉, 단일 에이전트 데모가 아니라 다음과 같은 요구를 수렴합니다.

- 결정적 워크플로우(Sequential / Parallel / Loop)와 LLM 기반 자율 에이전트의 혼합
- session.state 기반의 명시적 상태 공유
- 모든 LLM call, tool call, sub-agent invocation에 대한 자동 트레이싱
- `adk eval`을 통한 회귀 평가
- A2A 프로토콜로 외부 노출, MCP로 외부 도구 흡수

이번 1편의 목표는 ADK를 "내 노트북에서 동작하는 첫 에이전트"까지 끌어내는 것입니다. Python 3.10 이상만 있으면 5분 안에 끝납니다.

## 핵심 개념: ADK가 바라보는 "에이전트"

ADK에서 에이전트는 단순히 "LLM에 도구를 붙인 것"이 아니라 다음 4가지 축으로 정의됩니다.

| 축 | 의미 | 예시 |
|----|------|------|
| Identity | 이름, 설명, 역할 | `name="weather_agent"` |
| Brain | 모델 + 시스템 프롬프트 | `model="gemini-2.5-flash"` |
| Tools | 호출 가능한 함수/외부 시스템 | `[get_weather, get_time]` |
| Sub-agents | 위임 가능한 자식 에이전트 | `[research_agent, writer_agent]` |

이 구조 덕분에 같은 코드 베이스에서 "단일 도구 에이전트"부터 "다층 위임 에이전트"까지 점진적으로 키울 수 있습니다.

## 설치

ADK는 PyPI에 `google-adk`로 등록되어 있습니다.

```bash
# Python 3.10 이상 필수
python3 --version

# 가상환경 (권장)
python3 -m venv .venv
source .venv/bin/activate

# 설치
pip install --upgrade pip
pip install google-adk
```

설치 확인:

```bash
adk --version
adk --help
```

`adk` CLI는 다음 서브커맨드를 제공합니다.

| 명령 | 용도 |
|------|------|
| `adk create <name>` | 프로젝트 스캐폴딩 |
| `adk run <agent_dir>` | CLI 대화 모드 |
| `adk web` | 개발용 웹 UI |
| `adk api_server` | REST API 서버 |
| `adk eval <agent_dir> <eval_set>` | 평가 실행 |
| `adk deploy` | Cloud Run / Agent Engine 배포 |

## 프로젝트 구조

ADK는 "에이전트 = 디렉토리"라는 컨벤션을 강제합니다. 가장 간단한 형태는 다음과 같습니다.

```text
my_agent/
├── __init__.py        # from . import agent
├── agent.py           # root_agent 정의
└── .env               # API 키, 모델 설정
```

`__init__.py`는 단 한 줄이면 됩니다.

```python
from . import agent
```

`.env`는 다음과 같이 구성합니다.

```bash
# Google AI Studio (개발용)
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your-api-key-here

# 또는 Vertex AI (프로덕션)
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_CLOUD_LOCATION=us-central1

# 기본 모델 (선택)
MODEL=gemini-2.5-flash
```

ADK는 `adk web`, `adk run`, `adk api_server` 실행 시 해당 디렉토리의 `.env`를 자동으로 로드합니다. `python-dotenv`를 명시적으로 호출할 필요가 없습니다.

## 첫 에이전트: weather + time multi-tool

ADK의 hello world에 해당하는 multi-tool 에이전트를 작성합니다. 두 개의 함수형 도구를 정의하고, `LlmAgent`에 등록합니다.

```python
# my_agent/agent.py
from google.adk.agents import LlmAgent


def get_weather(city: str) -> dict:
    """Return current weather for a given city.

    Args:
        city: City name in English, e.g. "Seoul" or "Paris".

    Returns:
        dict with keys: status, report (or error_message).
    """
    samples = {
        "seoul": "Seoul: 18C, partly cloudy",
        "paris": "Paris: 14C, light rain",
        "tokyo": "Tokyo: 21C, clear",
    }
    key = city.strip().lower()
    if key in samples:
        return {"status": "success", "report": samples[key]}
    return {
        "status": "error",
        "error_message": f"Weather data not available for {city}.",
    }


def get_time(city: str) -> dict:
    """Return current local time for a given city."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    tz_map = {
        "seoul": "Asia/Seoul",
        "paris": "Europe/Paris",
        "tokyo": "Asia/Tokyo",
    }
    key = city.strip().lower()
    if key not in tz_map:
        return {"status": "error", "error_message": f"No timezone for {city}."}
    now = datetime.now(ZoneInfo(tz_map[key]))
    return {
        "status": "success",
        "report": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }


root_agent = LlmAgent(
    name="weather_time_agent",
    model="gemini-2.5-flash",
    description="Answers weather and time questions for supported cities.",
    instruction=(
        "You are a helpful assistant. "
        "Use get_weather for weather questions and get_time for time questions. "
        "If the city is not supported, apologize politely."
    ),
    tools=[get_weather, get_time],
)
```

핵심 포인트:

- **함수의 docstring이 곧 tool schema**가 됩니다. ADK는 docstring과 type hint로부터 JSON Schema를 자동 생성합니다.
- 반환은 가급적 `{"status": ..., "report"|"error_message": ...}` 형태로 통일하면 모델이 결과를 일관되게 해석합니다.
- 변수명은 반드시 **`root_agent`**여야 합니다. ADK 런타임이 이 이름으로 진입점을 찾습니다.

## 실행 1: adk web (개발 UI)

가장 자주 쓰는 모드입니다. 프로젝트 루트(즉 `my_agent/`의 부모)에서 다음을 실행합니다.

```bash
adk web
```

기본 포트는 8000입니다. 브라우저에서 `http://localhost:8000`을 열면 좌측에 에이전트 목록, 가운데에 채팅창, 우측에 디버깅 패널이 나타납니다. 디버깅 패널은 다음을 실시간으로 보여줍니다.

- **Events**: 사용자 입력, 모델 출력, tool call, tool response의 시간순 흐름
- **State**: 현재 session.state 스냅샷
- **Trace**: 한 turn의 LLM call/tool call이 트리 형태로 시각화
- **Token usage**: prompt / completion token 카운트

이 디버깅 패널은 ADK의 가장 큰 강점 중 하나입니다. LangSmith나 Phoenix를 별도로 띄우지 않아도 로컬에서 즉시 트레이스를 볼 수 있습니다. adk-web의 소스는 GitHub(`google/adk-web`)에 공개되어 있어, 자체 변형도 가능합니다.

```bash
# 포트 변경, host 노출 예시
adk web --host 0.0.0.0 --port 8080
```

:::warning
`adk web`은 **개발 전용**입니다. 인증/인가가 없고, 임의 코드 실행 도구가 노출될 수 있습니다. 외부에 그대로 열지 말고, 프로덕션은 `adk api_server` + 인증 게이트웨이 또는 Agent Engine 배포를 사용하세요.
:::

## 실행 2: adk run (CLI)

UI 없이 바로 터미널에서 대화하고 싶다면:

```bash
adk run my_agent
```

다음과 같이 동작합니다.

```text
Loading agent from my_agent...
[user]: What's the weather in Seoul?
[weather_time_agent]: It is 18C and partly cloudy in Seoul.
[user]: And the time?
[weather_time_agent]: Current time in Seoul is 2026-04-26 10:42:15 KST.
[user]: exit
```

CI 파이프라인이나 SSH 환경에서 빠르게 sanity check할 때 유용합니다. `--save_session` 플래그를 주면 대화 기록을 JSON으로 저장할 수 있어, 그 자체로 평가용 trace 자료가 됩니다.

## 실행 3: adk api_server (REST)

다른 서비스(예: Django 백엔드, React 프론트엔드)에서 ADK 에이전트를 호출하고 싶다면 REST 모드를 씁니다.

```bash
adk api_server --port 8000
```

주요 엔드포인트:

| Method | Path | 역할 |
|--------|------|------|
| POST | `/apps/{app}/users/{user}/sessions` | 세션 생성 |
| POST | `/run` | 동기 실행 |
| POST | `/run_sse` | SSE 스트리밍 실행 |
| GET | `/list-apps` | 등록된 에이전트 목록 |

curl 예시:

```bash
# 1) 세션 생성
curl -X POST \
  http://localhost:8000/apps/my_agent/users/u1/sessions/s1

# 2) 메시지 전송 (SSE 스트리밍)
curl -N -X POST http://localhost:8000/run_sse \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "my_agent",
    "user_id": "u1",
    "session_id": "s1",
    "new_message": {
      "role": "user",
      "parts": [{"text": "What is the weather in Tokyo?"}]
    }
  }'
```

응답은 `data: {...}\n\n` 형태의 SSE 스트림으로 도착합니다. blog-jun의 chatbot처럼 React 프론트엔드에서 이 스트림을 받아 토큰 단위로 렌더링하면 ChatGPT 스타일 UX를 그대로 구현할 수 있습니다.

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `ModuleNotFoundError: my_agent` | 부모 디렉토리에서 실행하지 않음 | `cd <parent>` 후 `adk web` 실행 |
| `root_agent not found` | 변수명이 다름 | 반드시 `root_agent`로 export |
| 401 / API key invalid | `.env` 미적용 | `.env` 위치가 `agent.py`와 같은 폴더인지 확인 |
| `gemini-2.5-flash` 미인식 | SDK 버전 오래됨 | `pip install -U google-adk` |
| 도구가 호출되지 않음 | docstring 누락 | 모든 인자에 type hint와 description |

## 정리 + 다음 편

이번 편에서 다음을 갖췄습니다.

- `pip install google-adk`로 5분 만에 환경 구성
- `agent.py` + `__init__.py` + `.env` 컨벤션
- `LlmAgent` + 함수 도구로 첫 에이전트
- `adk web` / `adk run` / `adk api_server` 3가지 실행 모드

여기까지는 단일 에이전트입니다. 실전에서는 보통 "검색 → 작성 → 검수"처럼 여러 단계가 필요하고, 이때 등장하는 것이 ADK의 워크플로우 에이전트입니다. 다음 [[adk-02-multi-agent-workflow|2편]]에서는 SequentialAgent, ParallelAgent, LoopAgent, 그리고 BaseAgent 상속을 통한 Custom Agent까지, 멀티에이전트 패턴을 코드와 함께 다룹니다.

## 관련 문서

- [[adk-02-multi-agent-workflow|ADK 멀티에이전트 워크플로우]] - 다음 편, Sequential/Parallel/Loop/Custom 패턴
- [[adk-03-litellm-ollama|ADK + LiteLLM + Ollama]] - 로컬 LLM과 air-gapped 환경
- [[adk-04-evaluation-tracing|ADK 평가 / 트레이싱 / 디버깅]] - 시리즈 마지막
- [[a2a-05-adk-integration|A2A + ADK 통합 패턴과 보안]] - A2A 프로토콜로 ADK 에이전트 노출
- [[a2a-01-overview|A2A 프로토콜 개요]] - 에이전트 간 통신 프로토콜
