<!-- infographic-hero -->
![ADK + LiteLLM + Ollama: Local LLM Integration and Air-gapped Environments 핵심 요약](figures/infographic.svg)

*Figure: ADK + LiteLLM + Ollama: Local LLM Integration and Air-gapped Environments 한 장 요약 인포그래픽*

# ADK + LiteLLM + Ollama: 로컬 LLM 통합과 air-gapped 환경

> 본 글은 **ADK 로컬 개발 시리즈(adk-local-development)** 3편입니다.
>
> - [[adk-01-local-setup|1편: ADK 로컬 환경 셋업]]
> - [[adk-02-multi-agent-workflow|2편: ADK 멀티에이전트 워크플로우]]
> - 3편(현재 글): LiteLLM + Ollama 로컬 통합
> - [[adk-04-evaluation-tracing|4편: ADK 평가 / 트레이싱 / 디버깅]]
>
> 1, 2편은 Gemini를 가정했지만, 본 편은 외부 호출이 막힌 사내 환경, 의료/금융 같은 데이터 유출 금지 환경, 또는 단순히 비용을 0에 가깝게 만들고 싶은 개발자를 위한 가이드입니다.

## 개요

ADK가 등장 초기부터 가진 명확한 설계 결정이 있습니다: **모델은 교체 가능한 부품이다.** `LlmAgent(model=...)`에 들어가는 값은 문자열도 되고, 객체도 됩니다. Gemini 외의 모델을 쓰고 싶다면 `LiteLlm` 어댑터로 감싸면 됩니다.

```python
from google.adk.models.lite_llm import LiteLlm

agent = LlmAgent(
    name="local_agent",
    model=LiteLlm(model="ollama_chat/llama3.2"),
    tools=[...],
)
```

이 한 줄이 가능한 이유는 LiteLLM이 100여 개 LLM provider를 OpenAI Chat Completions 인터페이스로 통일했기 때문입니다. ADK는 LiteLLM 호출 결과를 자체 Event 객체로 변환하고, function calling은 OpenAI tool 스펙으로 통역합니다.

본 편은 다음을 다룹니다.

1. Ollama를 노트북에 설치하고 모델 받기
2. ADK에서 ollama 모델로 단일 에이전트 + 멀티에이전트 실행
3. air-gapped 환경에서 LiteLLM Proxy로 라우팅
4. Gemini vs Llama 3.2 비교(latency, tool calling 품질)
5. 트러블슈팅과 vLLM/TGI 대안
6. MCP 도구와의 결합

## 왜 LiteLLM인가

LiteLLM의 가치는 "OpenAI SDK 클라이언트 한 벌로 모든 모델"이 가능하다는 점입니다. ADK 입장에서는 다음 이득이 있습니다.

| 이득 | 설명 |
|------|------|
| Provider 추상화 | Gemini → Llama → Claude를 코드 한 줄 변경으로 교체 |
| Proxy 모드 | 사내 게이트웨이를 한 곳에 두고 모든 앱이 그곳만 바라봄 |
| 비용 추적 | 호출당 $0.000xx 단위로 자동 계산 |
| Fallback / Retry | 모델 A 실패 시 B로 자동 폴백 |
| Cache | redis/in-memory 응답 캐싱 |

## Ollama 설치와 모델 풀

Ollama는 로컬 LLM 서빙의 가장 쉬운 옵션입니다. macOS, Linux, Windows 모두 지원합니다.

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

설치 후 데몬을 띄웁니다.

```bash
ollama serve
# 기본 포트: http://localhost:11434
```

다른 터미널에서 모델을 받습니다. 도구 호출(function calling)을 지원하는 모델이 좋습니다.

```bash
# 일반 채팅 + tool calling 지원
ollama pull llama3.2          # 3B (~2GB), 가벼움
ollama pull llama3.1:8b       # 8B (~5GB)
ollama pull qwen2.5:7b        # 7B, tool calling 우수
ollama pull mistral:7b        # 7B, 안정적

# 임베딩
ollama pull nomic-embed-text
```

설치 확인:

```bash
ollama list
ollama run llama3.2 "Say hello in Korean"
```

## ADK에서 Ollama 호출

LiteLLM의 ollama 어댑터에는 두 가지 prefix가 있습니다.

| Prefix | 용도 | 권장 |
|--------|------|------|
| `ollama/` | text completion 스타일 | 비권장 |
| `ollama_chat/` | chat 스타일 + tool calling | **권장** |

ADK 에이전트는 항상 `ollama_chat/`을 사용해야 함수 호출이 정상 동작합니다.

설치 추가:

```bash
pip install google-adk litellm
```

에이전트 코드:

```python
# my_local_agent/agent.py
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm


def get_weather(city: str) -> dict:
    """Return current weather for a given city."""
    samples = {
        "seoul": "Seoul: 18C, partly cloudy",
        "paris": "Paris: 14C, light rain",
    }
    key = city.strip().lower()
    if key in samples:
        return {"status": "success", "report": samples[key]}
    return {
        "status": "error",
        "error_message": f"No weather data for {city}.",
    }


root_agent = LlmAgent(
    name="local_weather_agent",
    model=LiteLlm(model="ollama_chat/llama3.2"),
    description="Local weather assistant powered by Llama 3.2.",
    instruction=(
        "Use get_weather to answer weather questions. "
        "If unsupported, apologize politely in the user's language."
    ),
    tools=[get_weather],
)
```

`.env`는 사실상 비워둬도 동작합니다(API 키 불필요). Ollama 호스트를 변경하려면:

```bash
# .env
OLLAMA_API_BASE=http://localhost:11434
```

실행은 1편과 동일합니다.

```bash
adk web
# 또는
adk run my_local_agent
```

## 멀티에이전트에서 모델 혼합

2편의 워크플로우 패턴은 그대로 적용됩니다. 흥미로운 점은 **모델을 혼합**할 수 있다는 것입니다. 빠른 분류는 로컬, 긴 추론은 Gemini로 보내는 식입니다.

```python
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.lite_llm import LiteLlm

# 1단계: 로컬 모델로 빠른 분류
classifier = LlmAgent(
    name="classifier",
    model=LiteLlm(model="ollama_chat/llama3.2"),
    instruction="Classify the user's intent into one of: question, request, complaint.",
    output_key="intent",
)

# 2단계: 본격 추론은 Gemini
responder = LlmAgent(
    name="responder",
    model="gemini-2.5-flash",
    instruction=(
        "Intent: {intent}\n"
        "Respond appropriately to the user."
    ),
)

root_agent = SequentialAgent(
    name="hybrid_pipeline",
    sub_agents=[classifier, responder],
)
```

이 패턴은 비용을 크게 줄여줍니다. 입력의 80%가 단순 분류로 끝난다면 로컬에서 처리하고, 진짜 어려운 20%만 클라우드 모델에 보냅니다.

## air-gapped 환경: LiteLLM Proxy 토폴로지

사내 데이터센터, 의료/금융 격리망에서는 외부 인터넷 접근이 막혀있습니다. 이런 환경에서도 ADK를 쓸 수 있는 구조는 다음과 같습니다.

```text
┌─────────────────────────────────────────────────┐
│  Air-gapped network                              │
│                                                  │
│   [ADK Agent App] ──┐                            │
│                     │                            │
│   [ADK Agent App] ──┼─→ [LiteLLM Proxy] ──→ [Ollama / vLLM] │
│                     │       (router)             │
│   [ADK Agent App] ──┘                            │
│                                                  │
└─────────────────────────────────────────────────┘
```

LiteLLM Proxy는 별도 서버 프로세스로 동작하며, 다양한 백엔드 모델을 단일 OpenAI 호환 엔드포인트로 노출합니다.

`config.yaml`:

```yaml
model_list:
  - model_name: small-llm
    litellm_params:
      model: ollama_chat/llama3.2
      api_base: http://ollama-1:11434
  - model_name: large-llm
    litellm_params:
      model: ollama_chat/qwen2.5:32b
      api_base: http://ollama-2:11434
  - model_name: vllm-coder
    litellm_params:
      model: openai/Qwen2.5-Coder-32B
      api_base: http://vllm:8000/v1
      api_key: dummy

router_settings:
  fallbacks:
    - small-llm: ["large-llm"]
```

프록시 실행:

```bash
pip install 'litellm[proxy]'
litellm --config config.yaml --port 4000
```

ADK 측 설정:

```python
import os
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

os.environ["OPENAI_API_BASE"] = "http://litellm-proxy:4000"
os.environ["OPENAI_API_KEY"] = "internal-token"

root_agent = LlmAgent(
    name="agent",
    model=LiteLlm(model="openai/small-llm"),  # proxy의 model_name
    tools=[...],
)
```

이 구조의 장점:

- 모델 교체가 ADK 코드 변경 없이 proxy 설정만으로 가능
- 인증/감사 로깅을 proxy 한 곳에서 일괄 처리
- redis 기반 응답 캐시로 동일 질의 재사용
- `fallbacks`로 모델 장애 시 자동 우회

## Gemini vs Llama 3.2: 무엇을 언제 쓰나

선택은 결국 trade-off입니다.

| 항목 | Gemini 2.5 Flash | Llama 3.2 (3B local) | Qwen 2.5 7B (local) |
|------|------------------|----------------------|---------------------|
| 호스팅 | Google Cloud | 노트북/사내 GPU | 노트북/사내 GPU |
| 데이터 노출 | 외부 전송 | 로컬 보관 | 로컬 보관 |
| 첫 토큰 지연 | ~300ms | ~150ms (M-series Mac) | ~250ms |
| Tool calling 정확도 | 매우 높음 | 보통, 단순 도구만 | 높음, 복합 도구도 가능 |
| 한국어 품질 | 매우 높음 | 보통 | 높음 |
| 컨텍스트 윈도우 | 1M+ | 128K | 128K |
| 비용 | $/1M tokens | 전기료만 | 전기료만 |

권장:

- **데모, 스펙이 명확한 도구 호출**: Llama 3.2로 충분
- **한국어 긴 글, 복잡한 추론**: Gemini Flash 또는 Qwen 32B
- **PII/의료/금융 데이터**: 로컬 + LiteLLM Proxy 필수
- **실험 단계 비용 절감**: hybrid 파이프라인(로컬 분류 + 클라우드 추론)

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `function calling not supported` | `ollama/` prefix 사용 | `ollama_chat/` 로 변경 |
| 도구가 호출되지 않음 | 모델 자체가 tool calling 미지원 | llama3.2, qwen2.5, mistral 같은 지원 모델 사용 |
| `connection refused` | ollama 데몬 미실행 | `ollama serve` 또는 `OLLAMA_API_BASE` 설정 |
| 응답이 이상한 JSON | 모델이 schema 따라가지 못함 | 더 큰 모델로 교체 또는 instruction에 예시 포함 |
| 매우 느림 | CPU 추론 | Apple Silicon Metal 또는 GPU 사용 |
| Proxy 401 | api_key 미설정 | LiteLLM proxy의 master_key 와 클라이언트 토큰 일치 |

### Function calling vs JSON mode

작은 모델(3B 이하)은 function calling을 흉내만 내고 실제로는 free-form 텍스트를 뱉는 경우가 많습니다. 이 때는 두 가지 우회가 있습니다.

1. **JSON mode 강제**: instruction에 "Return ONLY a JSON object with keys ..."를 명시하고, 도구 호출 대신 결과 파싱
2. **모델 업그레이드**: 7B 이상(qwen2.5:7b, llama3.1:8b) 권장

ADK는 도구 호출 실패 이벤트를 그대로 trace에 남기므로, `adk web`의 trace 패널에서 어느 단계에서 모델이 실패하는지 즉시 확인할 수 있습니다.

## 다른 로컬 서빙: vLLM, TGI

Ollama는 가장 쉽지만, 성능을 더 짜내고 싶다면 다음 옵션이 있습니다.

| 옵션 | 강점 | 약점 |
|------|------|------|
| Ollama | 설치 5분, GGUF 자동 양자화 | 동시 요청 처리량 낮음 |
| vLLM | PagedAttention으로 throughput 매우 높음 | GPU 필수, 설치 복잡 |
| TGI | HuggingFace 생태계 통합 | Rust 의존, 운영 부담 |
| llama.cpp server | CPU 추론 최적화 | 기능 단순 |

ADK는 모두 LiteLLM의 OpenAI 호환 엔드포인트로 흡수합니다.

```python
# vLLM
LiteLlm(model="hosted_vllm/Qwen2.5-7B-Instruct", api_base="http://vllm:8000/v1")

# TGI
LiteLlm(model="huggingface/Qwen2.5-7B-Instruct", api_base="http://tgi:8080")
```

## MCP 도구와 결합

MCP(Model Context Protocol)는 도구를 표준 프로토콜로 노출합니다. ADK는 MCPToolset으로 MCP 서버의 도구를 그대로 흡수할 수 있습니다.

```python
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from mcp import StdioServerParameters

filesystem_tools = MCPToolset(
    connection_params=StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    )
)

agent = LlmAgent(
    name="local_coder",
    model=LiteLlm(model="ollama_chat/qwen2.5:7b"),
    tools=[filesystem_tools],
    instruction="Use filesystem tools to read/write code.",
)
```

이 조합은 air-gapped 환경에서 특히 강력합니다. **모델도 로컬, 도구도 로컬, 프로토콜도 표준**이므로 외부 의존성이 0에 수렴합니다.

## 정리 + 다음 편

이번 편 핵심:

- ADK의 model-agnostic 설계 → `LiteLlm` 한 줄로 100여 개 백엔드
- Ollama로 5분 만에 로컬 LLM 셋업, `ollama_chat/` prefix 필수
- air-gapped 환경은 LiteLLM Proxy + 사내 GPU 클러스터 토폴로지
- 비용/품질 trade-off에 따라 hybrid 파이프라인 권장
- MCP 도구까지 결합하면 완전한 오프라인 에이전트 시스템

다음 마지막 [[adk-04-evaluation-tracing|4편]]에서는 "에이전트가 잘 동작하는지 어떻게 측정하고 디버그하는가"를 다룹니다. EvalSet, AgentEvaluator, 자동 트레이싱, callback 기반 디버깅, 그리고 프로덕션 배포까지 한번에 정리합니다.

## 관련 문서

- [[adk-01-local-setup|ADK 로컬 환경 셋업]] - 시리즈 시작
- [[adk-02-multi-agent-workflow|ADK 멀티에이전트 워크플로우]] - 이전 편, 4가지 워크플로우 패턴
- [[adk-04-evaluation-tracing|ADK 평가 / 트레이싱 / 디버깅]] - 다음 편
- [[a2a-05-adk-integration|A2A + ADK 통합 패턴과 보안]] - 외부 노출과 프로덕션 보안
- [[a2a-03-vs-mcp|A2A vs MCP 비교]] - MCP 도구 결합 시 참고
