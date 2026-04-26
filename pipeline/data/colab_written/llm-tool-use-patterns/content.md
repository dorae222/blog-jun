<!-- infographic-hero -->
![LLM Tool Use Patterns: From Function Calling to Agents 핵심 요약](figures/infographic.svg)

*Figure: LLM Tool Use Patterns: From Function Calling to Agents 한 장 요약 인포그래픽*

# LLM Tool Use 패턴: Function Calling부터 Agent까지

## 들어가며

:::info
이 글은 LLM이 외부 도구를 활용하는 핵심 패턴을 체계적으로 비교한다. 단순 Function Calling에서 [[react|ReAct]], MRKL, Toolformer, TaskWeaver까지의 기법과, OpenAI/Anthropic/Google 각 API의 Tool Calling 구현 차이를 다룬다. [[multi-agent-comparison|멀티 에이전트 비교]]와 함께 읽으면 에이전트 설계의 전체 그림을 파악할 수 있다.
:::

LLM은 텍스트 생성에 뛰어나지만, 실시간 데이터 조회, 수학 계산, 파일 조작, 외부 API 호출 등 **현실 세계와의 상호작용**에는 근본적 한계가 있다. 학습 데이터의 컷오프 이후 정보는 알 수 없고, 부동소수점 연산은 불안정하며, 외부 시스템에 직접 접근할 수 없다.

**Tool Use**는 이 한계를 극복하는 패러다임이다. LLM에게 사용 가능한 "도구 목록"을 제공하고, 모델이 적절한 도구를 선택하여 호출하도록 하는 방식이다. 이 글에서는 Tool Use의 핵심 기법들을 비교하고, 주요 API 제공자별 구현 방식, 실전 설계 패턴, 그리고 용도별 선택 가이드를 정리한다.

---

## Tool Use 기법 총괄 비교

| 기법 | 제안 시점 | 핵심 아이디어 | 도구 선택 주체 | 학습 필요 | 추론 루프 | 주요 장점 |
|------|---------|------------|-------------|---------|---------|---------|
| **Function Calling** | 2023 (OpenAI) | API 레벨에서 함수 스키마 제공 | LLM (프롬프트) | 불필요 | 없음 | 구현 단순, 즉시 적용 |
| **ReAct** | 2023 (Yao et al.) | Thought-Action-Observation 루프 | LLM (프롬프트) | 불필요 | 반복 | 추론 과정 투명 |
| **Toolformer** | 2023 (Schick et al.) | 모델 자체가 도구 호출을 학습 | LLM (파인튜닝) | 필수 | 없음 | 추가 프롬프트 불필요 |
| **MRKL** | 2022 (Karpas et al.) | 전문가 모듈 라우팅 | 라우터 모듈 | 라우터만 | 없음 | 전문 도구 정밀 활용 |
| **TaskWeaver** | 2023 (Microsoft) | 코드 생성 기반 계획 | 코드 생성기 | 불필요 | 반복 | 데이터 분석 특화 |
| **자율 에이전트** | 2023 (AutoGPT 등) | 목표 기반 자율 계획+실행 | LLM (프롬프트) | 불필요 | 반복 | 복잡한 목표 자율 수행 |

---

## Function Calling: API 레벨 도구 호출

### 개념

Function Calling은 가장 기본적이면서 가장 널리 사용되는 Tool Use 패턴이다. LLM API에 **함수 스키마(이름, 설명, 파라미터)**를 전달하면, 모델이 사용자 요청에 따라 적절한 함수를 선택하고 인자를 생성한다.

핵심 흐름은 다음과 같다:

1. 개발자가 사용 가능한 도구(함수)의 스키마를 API에 전달
2. 사용자 메시지를 LLM에 전송
3. LLM이 도구 호출이 필요하다고 판단하면 함수명 + 인자를 JSON으로 반환
4. 개발자가 해당 함수를 실행하고 결과를 다시 LLM에 전달
5. LLM이 결과를 종합하여 최종 응답 생성

### OpenAI Function Calling

```python
import openai

client = openai.OpenAI()

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "지정된 도시의 현재 날씨를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "도시명 (예: Seoul, Tokyo)"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "온도 단위"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "서울 날씨 알려줘"}],
    tools=tools,
    tool_choice="auto"
)

# 도구 호출 결과 처리
tool_call = response.choices[0].message.tool_calls[0]
# tool_call.function.name: "get_weather"
# tool_call.function.arguments: '{"location": "Seoul", "unit": "celsius"}'
```

### Anthropic Tool Use

Anthropic은 `tools` 파라미터에 `input_schema`를 사용하며, 응답에서 `tool_use` content block을 반환한다.

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=[
        {
            "name": "get_weather",
            "description": "지정된 도시의 현재 날씨를 조회합니다.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "도시명"
                    }
                },
                "required": ["location"]
            }
        }
    ],
    messages=[{"role": "user", "content": "서울 날씨 알려줘"}]
)

# response.content[0].type == "tool_use"
# response.content[0].name == "get_weather"
# response.content[0].input == {"location": "Seoul"}
```

### Google Gemini Function Calling

Google은 `google.genai` SDK에서 Python 함수를 직접 도구로 전달할 수 있다.

```python
from google import genai

client = genai.Client()

def get_weather(location: str) -> dict:
    """지정된 도시의 현재 날씨를 조회합니다."""
    return {"temperature": 22, "condition": "맑음"}

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="서울 날씨 알려줘",
    config=genai.types.GenerateContentConfig(
        tools=[get_weather]
    )
)
```

---

## API 제공자별 Tool Calling 비교

| 항목 | OpenAI | Anthropic | Google Gemini |
|------|--------|-----------|---------------|
| **스키마 키** | `parameters` (JSON Schema) | `input_schema` (JSON Schema) | Python 함수 / `FunctionDeclaration` |
| **응답 형태** | `tool_calls` 배열 | `tool_use` content block | `function_call` Part |
| **병렬 호출** | `parallel_tool_calls=True` | 자동 (여러 tool_use block) | 자동 |
| **강제 호출** | `tool_choice={"type":"function","function":{"name":"X"}}` | `tool_choice={"type":"tool","name":"X"}` | `tool_config` mode 설정 |
| **자동 선택** | `tool_choice="auto"` | `tool_choice={"type":"auto"}` | `ANY` mode |
| **호출 금지** | `tool_choice="none"` | 도구 미전달 | `NONE` mode |
| **스트리밍** | 지원 (SSE) | 지원 (SSE) | 지원 |
| **결과 반환 형식** | `tool` role 메시지 | `tool_result` content block | `function_response` Part |
| **최대 도구 수** | 128개 | 제한 없음 (권장 ~20) | 128개 |

---

## ReAct: 추론과 행동의 결합

### 개념

[[react|ReAct]](Yao et al., 2023)는 LLM이 **Thought(추론) - Action(행동) - Observation(관찰)** 루프를 반복하는 패턴이다. 단순 Function Calling과 달리, 모델이 각 도구 호출 전에 **왜 그 도구를 호출하는지 명시적으로 추론**하고, 결과를 관찰한 뒤 다음 행동을 결정한다.

### 동작 예시

```
질문: "오늘 서울과 도쿄의 기온 차이는?"

Thought 1: 서울과 도쿄의 현재 기온을 각각 조회해야 한다. 먼저 서울부터 조회하자.
Action 1: get_weather(location="서울")
Observation 1: {"temperature": 22, "unit": "celsius"}

Thought 2: 서울은 22도이다. 이제 도쿄를 조회한다.
Action 2: get_weather(location="도쿄")
Observation 2: {"temperature": 18, "unit": "celsius"}

Thought 3: 서울 22도 - 도쿄 18도 = 4도 차이. 최종 답변을 작성한다.
Answer: 서울이 도쿄보다 4도 높습니다. (서울 22도, 도쿄 18도)
```

### Function Calling과의 차이

| 비교 항목 | Function Calling | ReAct |
|----------|-----------------|-------|
| 추론 과정 | 암묵적 (블랙박스) | 명시적 (Thought 기록) |
| 루프 | 단일 또는 수동 반복 | 자동 반복 |
| 디버깅 | 어려움 | 추론 과정 추적 가능 |
| 복잡한 작업 | 제한적 | 다단계 추론 가능 |
| 구현 복잡도 | 낮음 | 중간 |
| 토큰 소비 | 적음 | 많음 (Thought 포함) |

---

## Toolformer: 모델 내재화 도구 호출

### 개념

Toolformer(Schick et al., 2023)는 프롬프트 엔지니어링이 아닌 **파인튜닝을 통해 모델 자체가 도구 호출 능력을 학습**하는 접근법이다. 모델이 텍스트 생성 중간에 `[Calculator(3.14 * 12^2)]` 같은 특수 토큰을 삽입하여 도구를 호출하고, 결과를 텍스트에 통합한다.

### 학습 과정

1. 기존 학습 데이터에서 도구 호출이 유용한 위치를 자동 탐색
2. 각 위치에 API 호출 토큰을 삽입한 후보 데이터 생성
3. 도구 호출이 **perplexity를 낮추는 경우**만 학습 데이터로 채택
4. 이 데이터로 모델을 파인튜닝

### 장점과 한계

| 항목 | 설명 |
|------|------|
| 장점 | 추가 프롬프트 없이 자연스럽게 도구 사용 |
| 장점 | 도구 호출 시점을 모델이 스스로 판단 |
| 장점 | 추론 비용 증가 없음 (프롬프트에 도구 정의 불필요) |
| 한계 | 파인튜닝 필요 (API 모델에 직접 적용 불가) |
| 한계 | 새 도구 추가 시 재학습 필요 |
| 한계 | 현재 상용 API에서는 사용 불가 |

---

## MRKL: 전문가 라우팅 시스템

### 개념

MRKL(Modular Reasoning, Knowledge and Language, Karpas et al., 2022)은 LLM을 **중앙 라우터**로 사용하고, 전문화된 모듈(계산기, 검색 엔진, 데이터베이스 등)로 쿼리를 분배하는 아키텍처이다. LangChain의 Agent 프레임워크가 이 구조에 영향을 받았다.

### 아키텍처 구성

MRKL 시스템은 세 가지 핵심 구성 요소로 이루어진다:

1. **라우터 (LLM)**: 사용자 쿼리를 분석하여 적절한 전문가 모듈을 선택
2. **전문가 모듈**: 각 도메인에 특화된 실행 엔진 (계산기, SQL 엔진, 검색 API 등)
3. **통합기 (LLM)**: 전문가 모듈의 결과를 종합하여 최종 응답 생성

### ReAct와의 차이

| 비교 항목 | ReAct | MRKL |
|----------|-------|------|
| 도구 선택 | 추론 루프 내에서 동적 | 라우터가 사전 분류 |
| 실행 방식 | 순차적 | 병렬 가능 |
| 확장성 | 도구 수 증가 시 프롬프트 비대 | 라우터만 업데이트 |
| 적합 시나리오 | 다단계 추론 | 독립적 전문가 활용 |

---

## TaskWeaver: 코드 기반 도구 오케스트레이션

### 개념

TaskWeaver(Microsoft, 2023)는 사용자의 요청을 **Python 코드로 변환**하여 실행하는 프레임워크이다. 도구를 함수로 정의하면, LLM이 해당 함수들을 조합하는 코드를 생성하고 실행한다. 특히 데이터 분석 작업에 강점을 보인다.

### 동작 흐름

1. 사용자가 자연어로 요청 ("매출 데이터에서 상위 5개 제품을 찾아 차트로 그려줘")
2. Planner가 요청을 하위 작업으로 분해
3. Code Generator가 각 하위 작업에 대한 Python 코드 생성
4. 코드 실행기가 안전한 환경에서 코드 실행
5. 결과를 사용자에게 반환

### 다른 기법과의 차이

TaskWeaver는 **도구 간 데이터 흐름을 코드로 표현**하기 때문에, ReAct의 자연어 기반 체이닝보다 정밀하다. Pandas DataFrame 조작, 통계 분석, 시각화 등 데이터 파이프라인 작업에서 높은 정확도를 보인다.

---

## 다중 도구 호출 패턴

### 순차 체이닝 (Sequential Chaining)

이전 도구의 출력이 다음 도구의 입력이 되는 패턴이다. LLM이 전체 워크플로우를 계획하고 단계별로 실행한다.

```
질문: "삼성전자 최신 실적을 분석하고 요약해줘"

Step 1: web_search("삼성전자 2025 Q4 실적") -> 검색 결과 URL
Step 2: web_scrape(url) -> 실적 데이터 텍스트
Step 3: analyze_data(text) -> 핵심 수치 추출
Step 4: summarize(analysis) -> 요약 보고서
```

### 병렬 호출 (Parallel Calling)

독립적인 도구 호출을 동시에 실행하여 지연시간을 줄이는 패턴이다. OpenAI, Anthropic 모두 병렬 호출을 지원한다.

```python
# OpenAI 병렬 Function Calling 예시
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "서울, 도쿄, 뉴욕 날씨를 알려줘"}],
    tools=weather_tools,
    parallel_tool_calls=True,
)

# response.choices[0].message.tool_calls에 3개의 호출이 동시 포함:
# [get_weather("Seoul"), get_weather("Tokyo"), get_weather("New York")]
```

### 조건부 분기 (Conditional Branching)

도구 실행 결과에 따라 다음 행동이 달라지는 패턴이다.

```
질문: "이 이미지에 텍스트가 있으면 번역하고, 없으면 내용을 설명해줘"

Step 1: detect_text(image) -> {"has_text": true, "text": "Hello World"}
Step 2a (텍스트 있음): translate(text, target="ko") -> "안녕하세요 세계"
Step 2b (텍스트 없음): describe_image(image) -> "풍경 사진..."
```

### 다중 도구 호출 패턴 비교

| 패턴 | 실행 방식 | 적합 시나리오 | 레이턴시 | 구현 복잡도 |
|------|---------|------------|---------|----------|
| 순차 체이닝 | 직렬 | 이전 결과가 다음 입력인 경우 | 높음 | 낮음 |
| 병렬 호출 | 동시 | 독립적 다중 조회 | 낮음 | 중간 |
| 조건부 분기 | 동적 | 결과에 따라 분기가 필요한 경우 | 가변 | 높음 |
| 혼합 (Fan-out/Fan-in) | 병렬 후 합산 | 여러 소스에서 수집 후 통합 | 중간 | 높음 |

---

## 자율적 에이전트

LLM이 **목표를 받고 스스로 계획-실행-검증**을 반복하는 패턴이다. 인간의 개입 없이 복잡한 작업을 완수한다.

```
목표: "블로그 포스트를 작성하고 배포하라"

Plan:
1. 주제 리서치 (web_search)
2. 개요 작성 (generate_outline)
3. 본문 작성 (generate_content)
4. 이미지 생성 (generate_image)
5. CMS에 업로드 (api_call)
6. SNS 공유 (social_post)

-> 각 단계를 자율적으로 실행, 실패 시 재시도 또는 대안 탐색
```

### 대표적 에이전트 구현체

| 에이전트 | 특화 분야 | 도구 사용 방식 | 자율성 수준 |
|---------|---------|-------------|----------|
| AutoGPT | 범용 자율 에이전트 | ReAct + 메모리 | 매우 높음 |
| Claude Code | 소프트웨어 개발 | Function Calling + 파일 시스템 | 높음 |
| SWE-Agent | GitHub 이슈 해결 | 코드 편집 + 터미널 | 높음 |
| OpenAI Codex | 소프트웨어 개발 | 코드 생성 + 실행 | 높음 |
| Devin | 소프트웨어 개발 | 브라우저 + 터미널 + 에디터 | 매우 높음 |

---

## MCP (Model Context Protocol)

### 개념

Anthropic이 제안한 **Tool Use 표준화 프로토콜**이다. 도구를 제공하는 서버와 LLM 클라이언트 사이의 통신을 표준화하여, 한 번 구현한 도구를 여러 LLM 클라이언트에서 재사용할 수 있게 한다.

### 핵심 구조

MCP는 클라이언트-서버 아키텍처를 따르며, JSON-RPC 2.0 프로토콜로 통신한다:

- **MCP Client**: LLM 앱 (Claude Desktop, Cursor, Claude Code 등)
- **MCP Server**: 도구/리소스 제공자 (GitHub, Slack, DB 등)
- **Transport**: stdio 또는 HTTP(SSE) 기반 통신

### 기존 방식과의 비교

| 항목 | 기존 Tool Use | MCP |
|------|-------------|-----|
| 도구 정의 | 각 앱마다 개별 구현 | 표준 프로토콜로 통일 |
| 재사용성 | 앱 간 공유 불가 | 서버 하나로 여러 클라이언트 지원 |
| 생태계 | 폐쇄적 | 오픈 표준 |
| 도구 검색 | 수동 | 서버가 도구 목록 자동 제공 |
| 인증/보안 | 앱마다 다름 | OAuth 2.1 표준 |

MCP 서버는 이미 Slack, GitHub, Google Drive, PostgreSQL 등 주요 서비스에 대해 다수 존재하며, 빠르게 생태계가 확장되고 있다.

---

## 도구 설명 설계 원칙

### 좋은 도구 설명 vs 나쁜 도구 설명

LLM이 도구를 정확하게 선택하고 올바른 인자를 전달하려면, **명확하고 구체적인 도구 설명**이 핵심이다.

```python
# 나쁜 예: 모호한 설명
{
    "name": "search",
    "description": "검색"
}

# 좋은 예: 구체적이고 사용 조건을 명시
{
    "name": "web_search",
    "description": "인터넷에서 최신 정보를 검색합니다. "
                   "실시간 데이터(날씨, 주가, 뉴스)나 "
                   "학습 데이터에 없는 최신 정보가 필요할 때 사용합니다. "
                   "일반 지식 질문에는 사용하지 마세요."
}
```

### 도구 설명 체크리스트

| 항목 | 설명 | 예시 |
|------|------|------|
| 기능 명시 | 도구가 **무엇을 하는지** 명확히 | "지정 도시의 현재 기상 데이터를 반환" |
| 사용 조건 | **언제** 사용해야 하는지 | "실시간 날씨가 필요할 때 사용" |
| 제한 사항 | **언제 사용하지 말아야** 하는지 | "과거 날씨 이력 조회에는 사용 불가" |
| 파라미터 설명 | 각 파라미터의 의미와 형식 | "location: 도시명 (영문, 예: Seoul)" |
| 반환값 설명 | 어떤 데이터가 반환되는지 | "temperature(숫자), condition(문자열)" |

---

## 도구 수 관리와 라우팅

### 도구 수에 따른 전략

| 도구 수 | LLM 정확도 | 권장 전략 |
|---------|----------|---------|
| 1~5개 | 매우 높음 | 단순 Function Calling |
| 5~10개 | 높음 | 그룹별 설명 보강 |
| 10~20개 | 중간 | 카테고리별 그룹화 + 상세 설명 |
| 20~50개 | 낮음 | 2단계 라우팅 (카테고리 선택 -> 도구 선택) |
| 50개 이상 | 매우 낮음 | RAG 기반 도구 검색 + 동적 도구 주입 |

### 2단계 라우팅 패턴

도구가 20개 이상일 때는 **카테고리 선택 -> 도구 선택**의 2단계 라우팅이 효과적이다:

1. 1단계: LLM이 요청을 분석하여 도구 카테고리를 선택 (예: "날씨", "금융", "파일 관리")
2. 2단계: 선택된 카테고리의 도구만 LLM에 전달하여 구체적 도구 선택

---

## 오류 처리와 재시도 패턴

### 오류 메시지 설계

도구 실행 실패 시 LLM에게 **의미 있는 에러 메시지**를 반환해야 모델이 적절히 대처할 수 있다.

```python
# 나쁜 예: 디버깅 불가능한 에러
return {"error": "500"}

# 좋은 예: LLM이 대처 가능한 에러
return {
    "error": "API_RATE_LIMIT",
    "message": "API 할당량 초과. 1분 후 재시도하거나 "
               "cached_weather 도구를 대안으로 사용하세요.",
    "retry_after_seconds": 60,
    "alternative_tool": "cached_weather"
}
```

### 재시도 전략

| 전략 | 설명 | 적합 상황 |
|------|------|---------|
| 단순 재시도 | 동일 요청 재실행 | 일시적 네트워크 오류 |
| 백오프 재시도 | 대기 시간 증가하며 재시도 | Rate limit |
| 대안 도구 | 다른 도구로 대체 실행 | 특정 API 장애 |
| 파라미터 수정 | 인자를 변경하여 재시도 | 입력 형식 오류 |
| 사용자 확인 | 사용자에게 판단 위임 | 모호한 요청 |

### 오류 처리 흐름

```python
def execute_tool_with_retry(tool_name, args, max_retries=3):
    for attempt in range(max_retries):
        result = execute_tool(tool_name, args)

        if result.get("success"):
            return result

        error_type = result.get("error_type")

        if error_type == "RATE_LIMIT":
            wait = result.get("retry_after_seconds", 60)
            time.sleep(wait)
            continue
        elif error_type == "INVALID_INPUT":
            # LLM에게 에러를 반환하여 파라미터 수정 유도
            return result
        elif error_type == "SERVICE_DOWN":
            # 대안 도구 시도
            alt = result.get("alternative_tool")
            if alt:
                return execute_tool(alt, args)
            return result
        else:
            return result

    return {"error": "MAX_RETRIES_EXCEEDED"}
```

---

## [[structured-output-guide|Structured Output]]과의 관계

Tool Use와 Structured Output은 밀접하게 연관되어 있다. Function Calling의 **인자 생성**이 곧 구조화된 출력이기 때문이다.

| 항목 | Tool Use | Structured Output |
|------|----------|------------------|
| 목적 | 외부 도구 호출 | 특정 형식의 데이터 출력 |
| 스키마 | 함수 파라미터 정의 | 출력 형식 정의 |
| 검증 | 런타임 실행 결과 | 스키마 유효성 검사 |
| 활용 | 외부 시스템 연동 | 파싱, 데이터 추출 |

실무에서는 둘을 결합하여 사용하는 경우가 많다. 예를 들어, 도구 호출 결과를 받은 후 특정 구조로 출력하도록 강제하는 패턴이다.

---

## Tool Use 벤치마크

### 주요 벤치마크 결과

| 벤치마크 | 평가 내용 | GPT-4o | Claude 3.5 Sonnet | Gemini 1.5 Pro |
|---------|---------|--------|-------------------|----------------|
| **Berkeley Function Calling (BFCL)** | 함수 호출 정확도 | 88.0% | 90.0% | 84.3% |
| **ToolBench** | 다중 도구 체이닝 | 높음 | 높음 | 중간 |
| **API-Bank** | API 호출 정확도 | 높음 | 높음 | 높음 |
| **Nexus Raven** | 복잡한 함수 호출 | 높음 | 매우 높음 | 중간 |

:::warning
벤치마크 점수는 모델 버전, 평가 시점, 프롬프트 설계에 따라 크게 달라질 수 있다. 위 수치는 참고용이며, 실제 프로덕션 환경에서는 자체 평가 셋으로 테스트하는 것이 필수적이다.
:::

### 실패 유형 분석

| 실패 유형 | 빈도 | 원인 | 해결 방법 |
|----------|------|------|---------|
| 잘못된 도구 선택 | 높음 | 도구 설명 모호 | 설명 보강 + 예시 추가 |
| 파라미터 누락 | 중간 | required 미지정 | 스키마에 required 명시 |
| 타입 불일치 | 중간 | enum 미정의 | enum/format 명시 |
| 불필요한 도구 호출 | 낮음 | 사용 조건 미명시 | "사용하지 않을 조건" 추가 |
| 환각 도구 호출 | 낮음 | 존재하지 않는 함수 호출 | strict mode 활성화 |

---

## 용도별 선택 가이드

### 챗봇 (고객 응대)

- **권장 패턴**: Function Calling + 병렬 호출
- **도구 예시**: FAQ 검색, 주문 조회, 상담원 연결
- **핵심 포인트**: 응답 속도가 중요하므로 병렬 호출 활용, 도구 수는 10개 이하로 유지

### 데이터 분석 에이전트

- **권장 패턴**: TaskWeaver 또는 ReAct + 코드 실행
- **도구 예시**: SQL 쿼리, Pandas 조작, 차트 생성
- **핵심 포인트**: 코드 생성 기반이 자연어 체이닝보다 정확, 실행 환경 격리 필수

### 소프트웨어 개발 에이전트

- **권장 패턴**: 자율 에이전트 (ReAct 기반)
- **도구 예시**: 파일 읽기/쓰기, 터미널 실행, 웹 검색, 코드 분석
- **핵심 포인트**: 긴 컨텍스트 유지, 실행 결과 검증 루프 필수

### RAG 보강 시스템

- **권장 패턴**: Function Calling + 조건부 분기
- **도구 예시**: 벡터 검색, 키워드 검색, 문서 요약
- **핵심 포인트**: 검색 결과 품질에 따라 재검색 또는 요약 분기

### API 통합 플랫폼

- **권장 패턴**: MRKL + MCP
- **도구 예시**: 외부 SaaS API 연동 (CRM, ERP, 메신저)
- **핵심 포인트**: MCP 서버로 도구 표준화, 2단계 라우팅으로 도구 선택 정확도 확보

---

## 용도별 패턴 매칭 매트릭스

| 용도 | Function Calling | ReAct | Toolformer | MRKL | TaskWeaver | 자율 에이전트 |
|------|:---------------:|:-----:|:----------:|:----:|:----------:|:----------:|
| 고객 응대 챗봇 | **최적** | 적합 | 부적합 | 적합 | 부적합 | 과도 |
| 데이터 분석 | 적합 | 적합 | 부적합 | 적합 | **최적** | 적합 |
| 소프트웨어 개발 | 적합 | **최적** | 부적합 | 부적합 | 적합 | **최적** |
| RAG 시스템 | **최적** | 적합 | 부적합 | 적합 | 부적합 | 과도 |
| API 통합 | 적합 | 적합 | 부적합 | **최적** | 부적합 | 적합 |
| 연구/실험 | 적합 | 적합 | **최적** | 적합 | 적합 | 적합 |

---

## 실전 구현 체크리스트

| 단계 | 체크 항목 | 설명 |
|------|---------|------|
| 1. 도구 설계 | 도구 설명이 구체적인가 | 기능, 사용 조건, 제한 사항 포함 |
| 2. 스키마 정의 | required 필드가 명시되었는가 | 필수/선택 파라미터 구분 |
| 3. 타입 정의 | enum, format이 지정되었는가 | 파라미터 유효 범위 제한 |
| 4. 오류 처리 | 에러 메시지가 LLM 친화적인가 | 대안 행동을 제안하는 메시지 |
| 5. 재시도 로직 | 실패 시 재시도 전략이 있는가 | 백오프, 대안 도구 |
| 6. 보안 | 도구 실행 환경이 격리되었는가 | 샌드박스, 권한 제한 |
| 7. 로깅 | 도구 호출 로그가 기록되는가 | 디버깅, 모니터링 |
| 8. 테스트 | 엣지 케이스 테스트가 있는가 | 잘못된 입력, 타임아웃 |

---

## 정리

Tool Use는 LLM을 **텍스트 생성기에서 행동 주체로** 전환시키는 핵심 패러다임이다. 각 기법의 특성을 요약하면 다음과 같다:

| 기법 | 핵심 가치 | 적합 규모 | 도입 난이도 |
|------|---------|---------|----------|
| Function Calling | 즉시 적용 가능한 범용 도구 호출 | 소~중 | 쉬움 |
| ReAct | 투명한 추론 과정 + 도구 사용 | 중 | 중간 |
| Toolformer | 모델 내재화, 추가 프롬프트 불필요 | 연구용 | 높음 |
| MRKL | 전문가 모듈 조합의 확장성 | 대 | 중간 |
| TaskWeaver | 데이터 분석 파이프라인 정밀도 | 중 | 중간 |
| 자율 에이전트 | 복잡한 목표의 자율적 달성 | 대 | 높음 |

대부분의 프로덕션 환경에서는 **Function Calling으로 시작**하여, 복잡도가 증가하면 ReAct나 다중 도구 체이닝으로 확장하는 것이 실용적이다. MCP의 등장으로 도구 생태계가 표준화되면서, 에이전트 시스템의 실용화가 가속되고 있다. 목적과 규모에 맞는 패턴을 선택하고, 도구 설명 품질과 오류 처리에 집중하는 것이 성공적인 Tool Use 구현의 핵심이다.
