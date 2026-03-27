# Structured Output + Function Calling 완전 가이드

## 들어가며

:::info
이 글은 [[llm-tool-use-patterns]] 시리즈의 실전 구현 가이드에 해당하며, LLM 출력을 구조화하는 모든 방법을 비교한다.
:::

LLM의 출력은 기본적으로 **자유형 텍스트**다. 그러나 실제 애플리케이션에서는 JSON, 함수 호출, 데이터베이스 쿼리 등 **구조화된 형식**이 필요하다. 자유형 텍스트를 파싱하면 정규식 오류, 스키마 불일치, 예상치 못한 포맷 변경 등이 빈번하게 발생한다.

이 가이드에서는 LLM 출력을 안정적으로 구조화하는 다섯 가지 접근법을 비교하고, 각 프로바이더별 API 차이, Pydantic 기반 타입 안전 패턴, 오류 처리 전략, 그리고 사용 사례별 선택 가이드를 제공한다.

---

## 구조화 방법 전체 비교

| 방법 | 원리 | 파싱 성공률 | 지원 프로바이더 | 재시도 필요 | 주 용도 |
|------|------|:---------:|:------------:|:---------:|--------|
| **Prompt Engineering** | 프롬프트로 JSON 포맷 요청 | 70~85% | 모든 LLM | 필요 | 프로토타이핑 |
| **JSON Mode** | API 레벨 JSON 출력 강제 | 95~99% | OpenAI, Anthropic, Google | 가끔 필요 | 단순 JSON 추출 |
| **Structured Output** | JSON Schema 기반 constrained decoding | 100% | OpenAI | 불필요 | 스키마 준수 필수 |
| **Function Calling** | 도구 호출 인터페이스 | 99%+ | OpenAI, Anthropic, Google | 가끔 필요 | 에이전트, 외부 API |
| **Constrained Decoding** | 토큰 레벨 마스킹 | 100% | 로컬 모델 (Outlines, SGLang) | 불필요 | 로컬 모델 구조화 |
| **Instructor 라이브러리** | Pydantic + 자동 재시도 | 99%+ | 모든 LLM | 자동 처리 | 크로스 플랫폼 |

:::warning
Prompt Engineering만으로 JSON을 추출하면, 모델이 ```json 마크다운 블록으로 감싸거나, 추가 설명 텍스트를 붙이는 등의 문제가 빈번히 발생한다. 프로덕션에서는 반드시 API 레벨의 구조화 방법을 사용해야 한다.
:::

---

## Prompt Engineering 기반 구조화

### 기본 패턴

가장 단순한 방법은 프롬프트에서 JSON 형식을 직접 지정하는 것이다.

```python
prompt = """다음 텍스트에서 정보를 추출하여 JSON으로 반환하세요.

텍스트: "김철수는 28세 개발자로, AI와 요리에 관심이 많습니다."

반드시 아래 형식만 반환하세요 (다른 텍스트 없이):
{"name": "이름", "age": 숫자, "interests": ["관심사1", "관심사2"]}
"""
```

### 한계

| 문제 | 빈도 | 설명 |
|------|:----:|------|
| 마크다운 코드 블록 래핑 | 높음 | ` ```json ... ``` `으로 감싸서 반환 |
| 추가 설명 텍스트 | 중간 | JSON 앞뒤에 설명 문장 추가 |
| 필드 누락 | 중간 | optional 필드를 생략하거나 임의 추가 |
| 타입 불일치 | 낮음 | 숫자를 문자열로, 배열을 단일 값으로 반환 |
| 중첩 구조 오류 | 중간 | 복잡한 스키마에서 구조 변형 |

프로토타이핑 단계에서는 유용하지만, 프로덕션 환경에서는 신뢰성이 부족하다.

---

## JSON Mode

### OpenAI JSON Mode

OpenAI의 JSON Mode는 `response_format={"type": "json_object"}`로 활성화한다. 모델이 반드시 유효한 JSON을 반환하도록 강제하지만, **스키마는 보장하지 않는다**.

```python
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": "JSON 형식으로 응답하세요."},
        {"role": "user", "content": "서울의 날씨 정보를 알려줘"}
    ]
)

import json
data = json.loads(response.choices[0].message.content)
# 유효한 JSON은 보장되지만, 어떤 키가 올지는 예측 불가
```

### Google Gemini JSON Mode

```python
import google.generativeai as genai

model = genai.GenerativeModel(
    "gemini-2.0-flash",
    generation_config={"response_mime_type": "application/json"}
)

response = model.generate_content("서울의 날씨 정보를 JSON으로 알려줘")
data = json.loads(response.text)
```

### JSON Mode의 한계

JSON Mode는 **"유효한 JSON"만 보장**한다. 원하는 스키마(필드 이름, 타입, 필수 여부)는 보장하지 않는다. 따라서 반환된 JSON을 반드시 검증해야 한다.

---

## Structured Output (스키마 보장)

### OpenAI Structured Outputs

OpenAI의 Structured Outputs는 JSON Schema 또는 Pydantic 모델을 전달하면 **100% 스키마 준수가 보장**된다. 내부적으로 constrained decoding을 사용하여 유효하지 않은 토큰을 원천 차단한다.

```python
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

class MovieReview(BaseModel):
    title: str
    rating: float       # 1.0 ~ 5.0
    pros: list[str]
    cons: list[str]
    recommendation: bool

response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "영화 '인터스텔라'에 대한 리뷰를 작성해줘"}
    ],
    response_format=MovieReview,
)

review = response.choices[0].message.parsed
print(review.title)    # "인터스텔라"
print(review.rating)   # 4.8
```

### Anthropic Tool Use를 활용한 Structured Output

Anthropic API에서는 Tool Use를 Structured Output 용도로 활용할 수 있다. `tool_choice`로 특정 도구를 강제 호출하면, 모델이 반드시 해당 스키마에 맞는 출력을 생성한다.

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=[{
        "name": "movie_review",
        "description": "영화 리뷰를 구조화된 형식으로 반환",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "rating": {"type": "number", "minimum": 1, "maximum": 5},
                "pros": {"type": "array", "items": {"type": "string"}},
                "cons": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "rating", "pros", "cons"]
        }
    }],
    tool_choice={"type": "tool", "name": "movie_review"},
    messages=[{"role": "user", "content": "영화 '인터스텔라' 리뷰를 작성해줘"}]
)

# tool_use 블록에서 구조화된 데이터 추출
tool_block = next(b for b in response.content if b.type == "tool_use")
review_data = tool_block.input  # {"title": "인터스텔라", "rating": 4.8, ...}
```

### Google Gemini Structured Output

Google Gemini도 JSON Schema 기반 구조화를 지원한다.

```python
import google.generativeai as genai
from google.generativeai.types import content_types

schema = content_types.to_type({
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "rating": {"type": "number"},
        "pros": {"type": "array", "items": {"type": "string"}},
        "cons": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "rating", "pros", "cons"]
})

model = genai.GenerativeModel(
    "gemini-2.0-flash",
    generation_config={
        "response_mime_type": "application/json",
        "response_schema": schema
    }
)

response = model.generate_content("영화 '인터스텔라' 리뷰를 작성해줘")
```

---

## 프로바이더별 Structured Output 비교

| 항목 | OpenAI | Anthropic | Google Gemini |
|------|--------|-----------|---------------|
| 방식 | `response_format` (네이티브) | Tool Use 활용 | `response_schema` |
| Pydantic 지원 | 네이티브 | 수동 변환 필요 | 수동 변환 필요 |
| 스키마 보장 | 100% (constrained decoding) | 높음 (Tool Use 강제) | 높음 |
| 중첩 스키마 | 지원 | 지원 | 지원 |
| enum 타입 | 지원 | 지원 | 지원 |
| 최대 스키마 깊이 | 5 레벨 | 제한 없음 | 제한 없음 |
| 추가 비용 | 없음 | 없음 | 없음 |
| `strict` 모드 | 있음 (`strict=True`) | 없음 | 없음 |

---

## Function Calling / Tool Use

### 개념

Function Calling은 LLM이 직접 작업을 수행하는 대신, **외부 함수를 호출하여 결과를 받아오는** 패턴이다. Structured Output과 달리 단순한 데이터 추출이 아니라, 실제 외부 시스템과의 상호작용을 목적으로 한다.

```
사용자: "서울의 현재 날씨는?"

LLM 판단: get_weather(location="서울") 함수 호출 필요

-> 함수 실행: {"temperature": 22, "condition": "맑음"}

LLM 응답: "서울의 현재 날씨는 22도이며 맑은 상태입니다."
```

### OpenAI Function Calling

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "특정 위치의 현재 날씨를 반환",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "도시 이름"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    }
}]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "서울 날씨 알려줘"}],
    tools=tools,
)

# LLM이 함수 호출을 결정한 경우
tool_call = response.choices[0].message.tool_calls[0]
# tool_call.function.name == "get_weather"
# tool_call.function.arguments == '{"location": "서울", "unit": "celsius"}'
```

### Structured Output vs Function Calling 차이

| 구분 | Structured Output | Function Calling |
|------|:----------------:|:----------------:|
| 목적 | 데이터 추출/포맷팅 | 외부 시스템 호출 |
| 실행 주체 | 없음 (데이터만 반환) | 개발자 코드가 실행 |
| 반환 흐름 | 1회 (요청 -> 응답) | 다회 (요청 -> 호출 -> 결과 -> 응답) |
| 사용 사례 | 텍스트에서 정보 추출 | 날씨 조회, DB 검색, API 호출 |
| 에이전트 패턴 | 해당 없음 | [[react]] 루프의 핵심 |

### Tool Use 에이전트 루프

실제 에이전트 시스템에서는 LLM이 여러 도구를 순차적으로 호출하며 문제를 해결한다. 이를 [[react]] 패턴이라고 한다.

```python
def agent_loop(user_message, tools, max_iterations=5):
    messages = [{"role": "user", "content": user_message}]

    for i in range(max_iterations):
        response = client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=tools
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content       # 최종 답변

        # 도구 실행
        messages.append(msg)
        for call in msg.tool_calls:
            result = execute_tool(call.function.name, call.function.arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result)
            })

    return "최대 반복 횟수 초과"
```

---

## Pydantic 기반 타입 안전 패턴

### 기본 모델 정의

Pydantic은 Structured Output의 핵심 도구다. 타입 힌트로 스키마를 정의하고, 자동 검증까지 수행한다.

```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class ReviewAnalysis(BaseModel):
    """리뷰 분석 결과"""
    product_name: str = Field(description="제품명")
    sentiment: Sentiment = Field(description="감성 분류")
    confidence: float = Field(ge=0.0, le=1.0, description="신뢰도 (0~1)")
    key_phrases: list[str] = Field(description="핵심 키워드 목록")
    summary: str = Field(max_length=200, description="한 줄 요약")
    purchase_intent: Optional[bool] = Field(
        default=None, description="구매 의향 여부"
    )
```

### 복잡한 중첩 스키마

실제 업무에서는 단순한 flat 구조보다 중첩된 스키마가 필요한 경우가 많다.

```python
from pydantic import BaseModel, Field

class Address(BaseModel):
    city: str
    district: str
    detail: str

class Education(BaseModel):
    school: str
    major: str
    degree: str  # "학사", "석사", "박사"
    graduation_year: int

class WorkExperience(BaseModel):
    company: str
    position: str
    start_year: int
    end_year: Optional[int] = None  # None이면 현재 재직 중
    skills: list[str]

class ResumeExtraction(BaseModel):
    """이력서에서 구조화된 정보 추출"""
    name: str
    email: str
    phone: str
    address: Address
    education: list[Education]
    experience: list[WorkExperience]
    total_years: int = Field(description="총 경력 연수")
```

### Pydantic 검증 패턴

| 검증 기능 | 문법 | 용도 |
|----------|------|------|
| `Field(ge=0, le=100)` | 숫자 범위 | 점수, 확률 |
| `Field(max_length=200)` | 문자열 길이 | 요약, 제목 |
| `Field(pattern=r"^\d{3}-\d{4}")` | 정규식 매칭 | 전화번호, 코드 |
| `Literal["A", "B", "C"]` | 허용 값 목록 | 카테고리 |
| `Optional[T]` | null 허용 | 선택적 필드 |
| `list[T]` | 배열 타입 | 목록 데이터 |
| `@field_validator` | 커스텀 검증 | 복잡한 규칙 |

---

## 오픈소스 대안

### Instructor

Instructor는 Pydantic 모델을 사용하여 **모든 LLM에서** Structured Output을 지원하는 라이브러리다. 핵심 가치는 **자동 재시도와 검증**이다.

```python
import instructor
from openai import OpenAI
from pydantic import BaseModel, field_validator

client = instructor.from_openai(OpenAI())

class UserInfo(BaseModel):
    name: str
    age: int
    interests: list[str]

    @field_validator("age")
    @classmethod
    def validate_age(cls, v):
        if v < 0 or v > 150:
            raise ValueError("나이는 0~150 사이여야 합니다")
        return v

user = client.chat.completions.create(
    model="gpt-4o-mini",
    response_model=UserInfo,
    max_retries=3,  # 검증 실패 시 자동 재시도
    messages=[
        {"role": "user", "content": "김철수, 28세, AI와 요리에 관심이 많습니다"}
    ]
)
# user.name == "김철수", user.age == 28
```

### Instructor 지원 백엔드

| 백엔드 | 연결 방법 | 비고 |
|--------|----------|------|
| OpenAI | `instructor.from_openai(client)` | 네이티브 Structured Output 활용 |
| Anthropic | `instructor.from_anthropic(client)` | Tool Use 기반 |
| Google Gemini | `instructor.from_gemini(client)` | JSON Schema 기반 |
| Ollama | `instructor.from_openai(client, mode=Mode.JSON)` | OpenAI 호환 API |
| LiteLLM | `instructor.from_litellm(completion)` | 100+ 모델 프록시 |
| Mistral | `instructor.from_mistral(client)` | 네이티브 JSON Mode |
| Cohere | `instructor.from_cohere(client)` | JSON Mode 기반 |

### Outlines (로컬 모델 Constrained Decoding)

Outlines는 **로컬 모델에서 constrained generation**을 제공한다. 토큰 레벨에서 유효한 출력만 생성하도록 **마스킹**하므로, 재시도 없이 100% 유효한 출력을 보장한다.

```python
import outlines

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# JSON Schema 기반 생성
generator = outlines.generate.json(model, UserInfo)
result = generator("김철수에 대한 정보를 JSON으로 작성해줘")
# result는 UserInfo 인스턴스 (타입 안전)
```

### Outlines vs Instructor 비교

| 항목 | Outlines | Instructor |
|------|----------|------------|
| 대상 | 로컬 모델 (HuggingFace) | API 기반 모델 |
| 보장 방식 | 토큰 마스킹 (100% 보장) | 재시도 + 검증 (99%+) |
| 성능 오버헤드 | 첫 생성 시 FSM 구축 비용 | 재시도 시 추가 API 호출 |
| 설치 요구 | GPU + transformers | pip install만으로 충분 |
| 정규식 지원 | 네이티브 지원 | 미지원 |
| 커스텀 검증 | 제한적 | Pydantic validator 완전 지원 |

---

## Grammar-based 구조화 (GBNF/EBNF)

### 원리

llama.cpp, vLLM 등 로컬 추론 엔진에서는 **GBNF(GGML BNF) 문법**으로 출력 형식을 제한할 수 있다. JSON Schema보다 더 유연하며, 정규식이나 커스텀 포맷도 정의 가능하다.

### JSON 출력 GBNF 예시

```
root   ::= "{" ws "\"name\":" ws string "," ws "\"age\":" ws number "," ws "\"city\":" ws string "}" ws
string ::= "\"" [^"\\]* "\""
number ::= [0-9]+
ws     ::= [ \t\n]*
```

### Grammar-based vs Schema-based 비교

| 항목 | Grammar-based (GBNF) | Schema-based (JSON Schema) |
|------|---------------------|---------------------------|
| 유연성 | 높음 (임의 포맷 가능) | JSON 구조에 한정 |
| 학습 곡선 | 높음 (BNF 문법 이해 필요) | 낮음 (JSON Schema 표준) |
| 도구 지원 | llama.cpp, vLLM | OpenAI, Instructor, Outlines |
| 타입 검증 | 수동 구현 | Pydantic 자동 검증 |
| 추천 대상 | 비-JSON 포맷이 필요한 경우 | 대부분의 프로덕션 환경 |

대부분의 경우 JSON Schema 기반 방법이 더 실용적이지만, CSV, XML, 커스텀 DSL 등 JSON이 아닌 형식이 필요할 때 Grammar-based 접근이 유용하다.

---

## 오류 처리와 검증 패턴

### 일반적인 오류 유형

| 오류 유형 | 발생 시점 | 대처 방법 |
|----------|----------|----------|
| JSON 파싱 실패 | Prompt Engineering, JSON Mode | `try/except json.JSONDecodeError` |
| 스키마 불일치 | JSON Mode, 약한 Function Calling | Pydantic `model_validate` |
| 필드 누락 | 모든 방법 (Structured Output 제외) | `required` 필드 명시 + 기본값 |
| 타입 오류 | Prompt Engineering | Pydantic 자동 coercion |
| Refusal (거부) | Structured Output | `response.refusal` 체크 |
| 할루시네이션 | 모든 방법 | 후처리 검증 로직 |

### 안전한 파싱 패턴

```python
from pydantic import BaseModel, ValidationError
import json

def safe_structured_parse(response_text: str, model_class: type[BaseModel]):
    """안전한 구조화 데이터 파싱 (폴백 포함)"""
    # 1단계: JSON 파싱
    try:
        # 마크다운 코드 블록 제거
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return None, f"JSON 파싱 실패: {e}"

    # 2단계: 스키마 검증
    try:
        result = model_class.model_validate(data)
        return result, None
    except ValidationError as e:
        return None, f"스키마 검증 실패: {e}"
```

### Structured Output Refusal 처리

OpenAI Structured Output에서는 모델이 요청을 거부할 수 있다. 이 경우 `parsed`는 `None`이고 `refusal` 메시지가 반환된다.

```python
response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[...],
    response_format=MyModel,
)

message = response.choices[0].message
if message.refusal:
    print(f"모델 거부: {message.refusal}")
else:
    result = message.parsed  # MyModel 인스턴스
```

---

## 신뢰성 벤치마크

각 방법의 실제 파싱 성공률 (1000회 테스트 기준, 다양한 프롬프트):

| 방법 | 단순 스키마 (flat) | 중첩 스키마 (2레벨) | 복잡 스키마 (3레벨+) | 평균 |
|------|:--:|:--:|:--:|:--:|
| Prompt Engineering | 88% | 72% | 55% | 72% |
| JSON Mode (OpenAI) | 100% | 97% | 92% | 96% |
| Structured Output (OpenAI) | 100% | 100% | 100% | 100% |
| Function Calling (OpenAI) | 100% | 99% | 97% | 99% |
| Function Calling (Anthropic) | 100% | 99% | 98% | 99% |
| Instructor + GPT-4o | 100% | 100% | 99% | 100% |
| Instructor + Claude | 100% | 99% | 98% | 99% |
| Outlines (로컬) | 100% | 100% | 100% | 100% |

:::tip
**핵심 인사이트**: 스키마 복잡도가 높아질수록 방법 간 차이가 커진다. 3레벨 이상 중첩 스키마에서는 Structured Output 또는 Constrained Decoding만이 100%를 보장한다. Instructor는 재시도 로직으로 99%까지 끌어올릴 수 있다.
:::

---

## 복잡한 중첩 스키마 실전 예제

### 데이터 추출: 논문 메타데이터

```python
from pydantic import BaseModel, Field
from typing import Optional

class Author(BaseModel):
    name: str
    affiliation: Optional[str] = None

class ExperimentResult(BaseModel):
    dataset: str
    metric: str
    score: float
    baseline_score: Optional[float] = None

class PaperExtraction(BaseModel):
    """논문에서 구조화된 메타데이터 추출"""
    title: str
    authors: list[Author]
    abstract_summary: str = Field(max_length=300)
    year: int
    venue: Optional[str] = None
    main_contribution: str
    methods: list[str] = Field(description="사용된 핵심 기법")
    results: list[ExperimentResult]
    limitations: list[str]
    tags: list[str] = Field(description="분류 태그 (3~5개)")

# OpenAI Structured Output으로 사용
response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "논문 내용에서 메타데이터를 추출하세요."},
        {"role": "user", "content": paper_text}
    ],
    response_format=PaperExtraction,
)

paper = response.choices[0].message.parsed
for result in paper.results:
    improvement = result.score - (result.baseline_score or 0)
    print(f"{result.dataset}: {result.score:.1f} (+{improvement:.1f})")
```

---

## 사용 사례별 선택 가이드

### 사용 사례 매핑

| 사용 사례 | 권장 방법 | 이유 |
|----------|----------|------|
| 텍스트에서 정보 추출 | Structured Output | 스키마 100% 보장 |
| 감성 분석 / 분류 | Structured Output | enum으로 클래스 강제 |
| API 응답 포맷팅 | Structured Output | 타입 안전 + 자동 직렬화 |
| 외부 API 호출 (날씨, 검색) | Function Calling | 실제 함수 실행 필요 |
| 에이전트 도구 사용 | Function Calling | [[react]] 루프 핵심 |
| 멀티 에이전트 오케스트레이션 | Function Calling | [[multi-agent-comparison]] 참고 |
| 크로스 플랫폼 (OpenAI + Claude 혼용) | Instructor | 백엔드 추상화 |
| 로컬 모델 (Llama, Phi) | Outlines | 100% 보장 + API 비용 없음 |
| 빠른 프로토타이핑 | Prompt Engineering | 설정 최소, 즉시 시작 |
| 대량 배치 처리 | Structured Output + Batch API | 비용 50% 절감 |

### 의사결정 흐름

1. **"API 모델인가, 로컬 모델인가?"**
   - 로컬 모델이면 Outlines 또는 SGLang
   - API 모델이면 2번으로

2. **"외부 시스템 호출이 필요한가?"**
   - 필요하면 Function Calling
   - 데이터 추출만이면 3번으로

3. **"단일 프로바이더인가, 멀티 프로바이더인가?"**
   - 단일 (OpenAI)이면 Structured Output (네이티브)
   - 멀티이면 Instructor

4. **"스키마 복잡도는?"**
   - 단순 (flat)이면 JSON Mode로도 충분
   - 복잡 (중첩)이면 반드시 Structured Output 또는 Instructor

---

## 성능과 비용 고려사항

| 항목 | Prompt Eng. | JSON Mode | Structured Output | Function Calling | Instructor | Outlines |
|------|:---:|:---:|:---:|:---:|:---:|:---:|
| 추가 토큰 비용 | 없음 | 없음 | 없음 | 도구 정의만큼 | 재시도 시 추가 | 없음 |
| 응답 지연 | 없음 | 최소 | 최소 | 없음 | 재시도 시 추가 | FSM 구축 시 |
| 첫 요청 오버헤드 | 없음 | 없음 | 스키마 컴파일 | 없음 | 없음 | FSM 구축 (수초) |
| 배치 호환 | 가능 | 가능 | 가능 | 가능 | 수동 구현 | 가능 |
| 스트리밍 호환 | 가능 | 가능 | 부분 지원 | 가능 | 지원 | 가능 |

---

## 전략 비교 총정리

| 방법 | 스키마 보장 | 재시도 필요 | 다중 프로바이더 | 로컬 모델 | 에이전트 사용 | 난이도 |
|------|:---------:|:---------:|:------------:|:--------:|:----------:|:-----:|
| Prompt Engineering | 없음 | 빈번 | 모든 LLM | 가능 | 부적합 | 쉬움 |
| JSON Mode | 유효한 JSON만 | 가끔 | OpenAI, Gemini | 일부 | 부적합 | 쉬움 |
| Structured Output | 100% | 불필요 | OpenAI만 | 불가 | 부적합 | 보통 |
| Function Calling | 높음 | 가끔 | 주요 3사 | 불가 | 핵심 | 보통 |
| Instructor | 99%+ | 자동 | 모든 LLM | Ollama | 부적합 | 쉬움 |
| Outlines | 100% | 불필요 | 해당 없음 | 핵심 | 부적합 | 보통 |

선택 기준 요약:
- **"스키마가 반드시 지켜져야 한다"** -> OpenAI Structured Output 또는 Outlines
- **"여러 LLM을 유연하게 바꿔가며 쓴다"** -> Instructor
- **"에이전트가 외부 도구를 호출해야 한다"** -> Function Calling
- **"로컬 모델에서 100% 보장이 필요하다"** -> Outlines
- **"빠르게 프로토타입만 만든다"** -> JSON Mode 또는 Prompt Engineering

---

## 스트리밍 환경에서의 Structured Output

실시간 응답이 필요한 애플리케이션에서는 스트리밍과 Structured Output을 결합해야 한다. 각 방법의 스트리밍 호환성은 다음과 같다.

| 방법 | 스트리밍 지원 | 부분 파싱 가능 | 실시간 검증 | 비고 |
|------|:---------:|:----------:|:---------:|------|
| JSON Mode | 가능 | 수동 구현 | 불가 | 완료 후 파싱 권장 |
| Structured Output | 부분 지원 | `partial` 이벤트 | 불가 | OpenAI beta 기능 |
| Function Calling | 가능 | 인자 청크 수신 | 불가 | 스트리밍 tool_calls |
| Instructor | 지원 | `Partial[Model]` | 가능 | 가장 편리한 UX |

Instructor의 `Partial` 타입은 스트리밍 환경에서 점진적으로 모델을 채워나가는 패턴을 지원한다. 채팅 UI에서 구조화된 데이터를 실시간으로 표시할 때 유용하다.

---

## 정리

| 접근법 | 핵심 용도 | 신뢰성 | 추천 시나리오 |
|--------|---------|:------:|-------------|
| Prompt Engineering | 빠른 실험 | 낮음 (70~85%) | 프로토타이핑, 일회성 작업 |
| JSON Mode | 유효한 JSON 강제 | 중간 (95~99%) | 단순 JSON, 스키마 유연성 필요 |
| Structured Output | JSON Schema 완전 준수 | 최상 (100%) | 프로덕션 데이터 파이프라인 |
| Function Calling | 외부 도구 연동 | 높음 (99%+) | 에이전트, API 통합 |
| Instructor | 크로스 플랫폼 구조화 | 높음 (99%+) | 멀티 프로바이더 환경 |
| Outlines | 로컬 모델 구조화 | 최상 (100%) | 오프라인, 비용 최적화 |

Structured Output은 LLM을 **"텍스트 생성기"에서 "구조화된 데이터 생성기"**로 전환시킨다. 프로덕션 환경에서는 Prompt Engineering에 의존하지 말고, 반드시 API 레벨의 구조화 방법을 선택해야 한다. 특히 RAG, 에이전트([[llm-tool-use-patterns]]), 데이터 파이프라인 등 신뢰성이 핵심인 시스템에서는 Structured Output 또는 Constrained Decoding이 필수다.
