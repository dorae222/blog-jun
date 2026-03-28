# Model Context Protocol: AI 에이전트 생태계의 USB 표준

**Anthropic** · **2024-11-25** · **Agent Protocol** · **MIT**

## 개요

Model Context Protocol(MCP)은 LLM 애플리케이션과 외부 도구/리소스/프롬프트 간의 통신을 표준화하는 오픈 프로토콜이다. Anthropic이 2024년 11월 발표한 MCP는 AI 에이전트 생태계의 **"USB 표준"**을 지향한다. USB가 컴퓨터와 주변기기 간의 연결을 표준화한 것처럼, MCP는 LLM 애플리케이션과 외부 도구 간의 연결을 표준화한다.

MCP가 등장하기 전에는 각 LLM 애플리케이션이 도구와 데이터 소스와 통합하기 위해 독자적인 커스텀 연결을 구현해야 했다. $M$개의 LLM 클라이언트와 $N$개의 도구가 있으면 $M \times N$개의 커스텀 통합이 필요했다. MCP는 이 문제를 MCP 서버(도구 제공자)와 MCP 클라이언트(LLM 애플리케이션) 사이의 통신 규격을 정의함으로써 해결한다. 한 번 구현된 MCP 서버가 모든 호환 클라이언트에서 즉시 사용 가능하게 되어 $M + N$개의 구현만으로 충분하다.

$$\text{커스텀 통합: } O(M \times N) \xrightarrow{\text{MCP}} O(M + N)$$

MCP는 발표 후 1년도 되지 않아 사실상의 업계 표준(de facto standard)으로 자리잡았다. Claude Desktop, Claude Code, Cursor, Windsurf, Goose 등 주요 LLM 클라이언트가 MCP를 지원하며, OpenAI와 Google도 MCP 호환성을 지원하기 시작했다. 수천 개의 커뮤니티 MCP 서버가 개발되어 GitHub, Slack, PostgreSQL, Google Drive, Notion, Jira 등 다양한 서비스와의 통합이 가능하다.

![MCP 프로토콜 아키텍처 - Host, Client, Server 삼중 구조의 LLM-도구 통신 표준](figures/architecture.svg)

*Figure 1: MCP 아키텍처 - Host(LLM 애플리케이션)가 Client를 통해 MCP Server와 JSON-RPC 기반으로 통신하며, Tools·Resources·Prompts 세 가지 기능을 표준화하여 M+N 구현으로 모든 조합을 지원한다.*

## 아키텍처 상세

MCP 프로토콜은 세 가지 핵심 기능(Primitive)을 표준화한다.

### 1. Tools (도구)

LLM이 실행할 수 있는 함수를 정의한다. 각 Tool은 이름, 설명, JSON Schema로 정의된 입력 스키마를 가진다. LLM은 사용자의 요청을 분석한 후, 등록된 Tool 목록에서 적절한 도구를 선택하고 인자를 구성하여 호출한다. 도구 호출 결과는 다시 LLM에 전달되어 최종 응답 생성에 활용된다.

Tool은 **모델 제어(model-controlled)** 방식으로 동작한다. 즉, LLM이 어떤 도구를 언제 호출할지 자율적으로 결정한다. 이는 OpenAI의 function calling과 개념적으로 유사하지만, MCP에서는 도구의 발견(discovery)과 호출이 표준화된 프로토콜을 통해 이루어진다는 점이 다르다.

### 2. Resources (리소스)

파일, 데이터베이스 테이블, API 응답 등 LLM에 제공할 컨텍스트 데이터를 URI 기반으로 노출한다. `file://`, `db://`, `api://` 등의 URI 스킴을 통해 다양한 데이터 소스에 접근한다.

Resources는 **애플리케이션 제어(application-controlled)** 방식이다. LLM이 직접 리소스를 요청하는 것이 아니라, 호스트 애플리케이션이 어떤 리소스를 컨텍스트에 포함할지 결정한다. 이는 RAG(Retrieval-Augmented Generation)의 패턴과 유사하며, 서버가 리소스 변경을 실시간으로 알리는 구독(subscription) 메커니즘도 지원한다.

### 3. Prompts (프롬프트)

재사용 가능한 프롬프트 템플릿을 정의한다. 서버가 특정 도메인에 최적화된 프롬프트를 제공함으로써, 클라이언트가 도메인 지식 없이도 해당 도구를 효과적으로 활용할 수 있게 한다.

Prompts는 **사용자 제어(user-controlled)** 방식이다. 사용자가 명시적으로 프롬프트 템플릿을 선택하면, 해당 템플릿이 대화 컨텍스트에 주입된다. 이를 통해 도메인 전문 지식이 없는 사용자도 복잡한 도구 활용 패턴을 손쉽게 실행할 수 있다.

### 통신 프로토콜

MCP는 **JSON-RPC 2.0** 위에서 동작한다. JSON-RPC는 경량 원격 프로시저 호출 프로토콜로, 요청(request), 응답(response), 알림(notification) 세 가지 메시지 타입을 정의한다. MCP에서 클라이언트와 서버는 양방향 통신이 가능하며, 서버도 클라이언트에 알림을 보낼 수 있다(예: 리소스 변경 알림).

#### 도구 발견 및 호출 흐름

MCP의 핵심 통신 패턴은 다음과 같다:

1. **초기화(Initialize)**: 클라이언트가 서버에 연결하고, 프로토콜 버전과 지원 기능(capabilities)을 협상한다.
2. **도구 발견(Discovery)**: 클라이언트가 `tools/list` 메서드를 호출하여 서버가 제공하는 도구 목록을 조회한다. 각 도구의 이름, 설명, JSON Schema 형태의 입력 파라미터 정의가 반환된다.
3. **도구 호출(Invocation)**: LLM이 적절한 도구를 선택하면, 클라이언트가 `tools/call` 메서드로 서버에 실행을 요청한다.
4. **결과 반환**: 서버가 도구를 실행하고 결과를 JSON-RPC 응답으로 반환한다.

이 흐름에서 중요한 점은 **LLM은 MCP를 직접 인식하지 않는다**는 것이다. 호스트 애플리케이션이 MCP를 통해 도구 목록을 수집하고, 이를 LLM의 도구 정의(tool definitions)로 변환하여 전달한다. LLM은 기존 function calling 방식으로 도구를 선택하고, 호스트가 다시 MCP를 통해 실제 실행을 중개한다.

#### 전송 메커니즘

세 가지 전송(transport) 방식을 지원한다.

| 전송 방식 | 프로토콜 | 적합한 상황 | 예시 |
|----------|---------|-----------|------|
| stdio | 표준 입출력 | 로컬 프로세스 | 파일 시스템, 로컬 DB |
| SSE | HTTP 기반 | 원격 서버 | 클라우드 API, SaaS |
| Streamable HTTP | HTTP POST | 최신 원격 | 서버리스, 프로덕션 |

**stdio** 전송은 MCP 서버를 자식 프로세스로 실행하고, stdin/stdout을 통해 JSON-RPC 메시지를 교환한다. 가장 단순하며 로컬 도구에 적합하다. **SSE(Server-Sent Events)** 전송은 HTTP 기반으로 원격 서버와 통신하며, 서버→클라이언트 스트리밍을 SSE로, 클라이언트→서버 메시지를 HTTP POST로 처리한다. **Streamable HTTP**는 가장 최신 전송 방식으로, 단일 HTTP POST 엔드포인트에서 양방향 통신을 처리하며 서버리스 환경에 최적화되어 있다.

### 서버 구현 예시

```python
# MCP 서버 구현 (Python SDK)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather-server")

@mcp.tool()
async def get_weather(city: str) -> str:
    """지정 도시의 현재 날씨를 조회한다"""
    weather = await fetch_weather_api(city)
    return f"{city}: {weather.temp}°C, {weather.condition}"

@mcp.resource("weather://{city}/forecast")
async def get_forecast(city: str) -> str:
    """도시의 5일 예보를 반환한다"""
    forecast = await fetch_forecast_api(city)
    return format_forecast(forecast)

@mcp.prompt()
def weather_analysis_prompt(city: str) -> str:
    """날씨 분석 프롬프트 템플릿"""
    return f"""다음 도시의 날씨를 분석하세요: {city}
    1. 현재 날씨를 get_weather로 확인
    2. 5일 예보를 확인
    3. 외출 추천 여부를 판단"""
```

### 클라이언트 설정

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["weather_server.py"]
    },
    "github": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "ghp_..." }
    }
  }
}
```

### 보안 격리

각 MCP 서버는 독립 프로세스로 실행되므로, 하나의 도구가 다른 도구의 데이터에 접근할 수 없다. 이는 도구 사용의 안전성을 구조적으로 보장한다.

## 핵심 혁신

1. **$M \times N \rightarrow M + N$ 통합 문제 해결**: 표준 프로토콜을 통해 각 클라이언트와 서버가 한 번만 MCP를 구현하면, 모든 조합에서 상호운용이 가능하다.

2. **경량 서버 구현**: MCP 서버는 수십 줄의 코드로 구현할 수 있을 만큼 가볍다. 이 낮은 진입 장벽이 빠른 생태계 성장의 핵심 요인이다.

3. **보안 격리**: 각 MCP 서버가 독립 프로세스로 실행되어 도구 간 격리를 구조적으로 보장한다.

4. **생태계 확장성**: 개방형 표준이므로 누구나 MCP 서버를 구현하고 공유할 수 있다. npm, PyPI 등 기존 패키지 매니저를 통해 배포되어 설치가 간편하다.

## 벤치마크/성능

| 측면 | MCP | 직접 API 통합 | LangChain Tools | OpenAI Functions |
|------|-----|-------------|----------------|------------------|
| 표준화 | 오픈 표준 | 비표준 | LangChain 전용 | OpenAI 전용 |
| 클라이언트 호환 | 모든 MCP 클라이언트 | 특정 앱만 | LangChain만 | OpenAI API만 |
| 구현 비용 | 낮음 (SDK 제공) | 높음 (각각 구현) | 중간 | 중간 |
| 보안 격리 | 프로세스 분리 | 앱 종속 | 앱 종속 | 서버 측 |
| 생태계 크기 | 수천 개 서버 | 해당 없음 | 수백 개 | 수십 개 |

## 구현

**개발 환경 통합**: GitHub MCP 서버, PostgreSQL MCP 서버, Docker MCP 서버를 Claude Code에 연결하여, 코딩 에이전트가 이슈 관리, DB 쿼리, 컨테이너 관리까지 수행하는 통합 개발 환경을 구축한다.

**기업 데이터 접근**: 사내 CRM, ERP, 문서 관리 시스템에 대한 MCP 서버를 구축하면, LLM 클라이언트가 기업 데이터에 안전하게 접근하여 분석이나 보고서 생성을 수행할 수 있다.

**커스텀 도구 빌드**: 팀 특화 도구(내부 API, 사내 검색 엔진, 모니터링 시스템)를 MCP 서버로 래핑하여, 모든 팀원이 자신의 LLM 클라이언트에서 동일한 도구를 사용할 수 있게 한다.

## Function Calling / Plugin 방식과의 비교

MCP 이전에도 LLM에 외부 도구를 연결하는 방법은 존재했다. 대표적으로 OpenAI의 **Function Calling**, ChatGPT **Plugins**, LangChain의 **Tools** 등이 있다. MCP와 이들의 근본적 차이를 정리하면:

| 비교 항목 | MCP | OpenAI Function Calling | ChatGPT Plugins | LangChain Tools |
|-----------|-----|------------------------|----------------|-----------------|
| **표준화** | 오픈 프로토콜 (MIT) | OpenAI API 전용 | OpenAI 전용 (중단됨) | LangChain 프레임워크 전용 |
| **도구 실행 위치** | 클라이언트 측 (로컬) | 서버 측 (OpenAI) | 서버 측 | 클라이언트 측 |
| **도구 발견** | 동적 (`tools/list`) | 정적 (API 호출 시 정의) | 정적 (manifest) | 정적 (코드에 정의) |
| **데이터 프라이버시** | 데이터가 외부 전송 불필요 | OpenAI 서버 경유 | OpenAI 서버 경유 | 로컬 가능 |
| **상호운용성** | 모든 MCP 클라이언트 | OpenAI만 | OpenAI만 | LangChain만 |

MCP의 핵심 이점은 **도구가 실행되는 위치**에 있다. Function Calling에서는 도구 정의만 LLM에 전달하고 실제 실행은 개발자의 백엔드에서 이루어지지만, 이 방식은 각 LLM 공급자마다 별도 구현이 필요하다. MCP는 도구 제공자가 한 번 MCP 서버를 구현하면, 어떤 MCP 호환 클라이언트에서든 동일하게 동작한다.

## 채택 현황

2024년 11월 발표 이후, MCP는 놀라운 속도로 업계 표준으로 자리잡았다:

- **Anthropic**: Claude Desktop, Claude Code에서 네이티브 지원
- **OpenAI**: 2025년 3월 Agents SDK에서 MCP 지원 발표
- **Google**: Gemini 생태계에서 MCP 호환 도입
- **개발 도구**: Cursor, Windsurf, Cline, Goose 등 주요 AI 코딩 도구가 MCP 지원
- **커뮤니티**: GitHub에 수천 개의 MCP 서버가 공개되어, 사실상 모든 주요 SaaS(Slack, GitHub, Notion, Jira, Linear, PostgreSQL 등)에 대한 연결이 가능

이 빠른 채택의 배경에는 MCP의 **낮은 진입 장벽**이 있다. Python SDK(`mcp`)나 TypeScript SDK(`@modelcontextprotocol/sdk`)를 사용하면 수십 줄의 코드로 서버를 구현할 수 있으며, 기존 REST API 래퍼를 MCP 서버로 변환하는 것도 간단하다.

## 한계 및 과제

1. **인증/인가 표준 부재**: 현재 MCP 사양에는 통합된 인증 메커니즘이 포함되어 있지 않다. 각 서버가 환경 변수나 자체 방식으로 인증을 처리하므로, 엔터프라이즈 환경에서의 통합 관리(SSO, RBAC 등)가 어렵다. OAuth 2.0 기반 인증 확장이 논의 중이다.

2. **보안 위험**: MCP 서버는 로컬에서 실행되므로, 악의적인 MCP 서버가 시스템 리소스에 접근할 수 있는 위험이 있다. **프롬프트 인젝션(Prompt Injection)** 공격으로 LLM이 의도하지 않은 도구를 호출하도록 유도될 가능성도 존재한다. 신뢰할 수 없는 출처의 MCP 서버를 설치할 때 특히 주의가 필요하다.

3. **상태 관리의 복잡성**: MCP 세션은 stateful하여, 서버와 클라이언트 간 연결이 유지되어야 한다. 서버리스 환경이나 수평 확장이 필요한 프로덕션 배포에서 상태 관리가 복잡해질 수 있다. Streamable HTTP 전송이 이를 일부 해소하지만, 완전한 해결은 아니다.

4. **도구 품질 편차**: 커뮤니티 기반 생태계이므로 MCP 서버의 품질이 균일하지 않다. 일부 서버는 에러 처리가 미흡하거나, 문서가 부족하거나, 유지보수가 중단된 상태다.

5. **디버깅 어려움**: LLM의 도구 선택 과정은 비결정적(non-deterministic)이므로, MCP 기반 워크플로에서 문제가 발생했을 때 원인 파악이 어려울 수 있다. MCP Inspector 같은 디버깅 도구가 제공되지만, 복잡한 멀티 서버 환경에서는 한계가 있다.

## 관련 모델

MCP는 에이전트 통신 표준의 첫 번째 계층으로, A2A(에이전트-에이전트)와 AG-UI(에이전트-UI) 프로토콜과 함께 완전한 에이전트 통신 스택을 구성한다. Claude Code, Goose, Cursor 등의 핵심 도구 인터페이스로 채택되었으며, OpenAI와 Google도 호환 지원을 발표했다.

## 참고 자료

- [MCP GitHub Organization](https://github.com/modelcontextprotocol)
- [MCP Specification](https://spec.modelcontextprotocol.io)
- [Anthropic Blog: Introducing MCP](https://www.anthropic.com/news/model-context-protocol)

## 관련 문서

- [[a2a|Agent-to-Agent Protocol]] - 영감을 줌
- [[ag-ui|AG-UI Protocol]] - 영감을 줌
- [[claude-code|Claude Code]] - 적용 모델
- [[goose|Goose]] - 적용 모델
