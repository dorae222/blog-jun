# Structured Output + Function Calling 완전 가이드

## 들어가며

LLM의 출력은 기본적으로 **자유형 텍스트**다. 그러나 실제 애플리케이션에서는 JSON, 함수 호출, 데이터베이스 쿼리 등 **구조화된 형식**이 필요하다.

이 가이드는 LLM 출력을 안정적으로 구조화하는 세 가지 접근법을 다룬다:
1. **Structured Output**: JSON Schema로 출력 형식 강제
2. **Function Calling / Tool Use**: 외부 함수를 호출하는 구조화된 인터페이스
3. **오픈소스 대안**: Outlines, Instructor 등

---

## Structured Output

### OpenAI Structured Outputs

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

핵심: `response_format`에 Pydantic 모델을 전달하면, **100% 스키마 준수가 보장**된다. 내부적으로 constrained decoding을 사용하여 유효하지 않은 토큰을 원천 차단한다.

### Anthropic Tool Use (Structured Output)

Anthropic API에서는 Tool Use를 Structured Output으로 활용할 수 있다:

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
```

---

## Function Calling / Tool Use

### 개념

LLM이 직접 작업을 수행하는 대신, **외부 함수를 호출하여 결과를 받아오는** 패턴이다.

```
사용자: "서울의 현재 날씨는?"

LLM 판단: get_weather(location="서울") 함수 호출 필요

→ 함수 실행: {"temperature": 22, "condition": "맑음"}

LLM 응답: "서울의 현재 날씨는 22°C이며 맑은 상태입니다."
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

### Tool Use 패턴

실제 에이전트 시스템에서의 Tool Use 루프:

```python
def agent_loop(user_message, tools, max_iterations=5):
    messages = [{"role": "user", "content": user_message}]

    for _ in range(max_iterations):
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

## 오픈소스 대안

### Instructor

[Instructor](https://github.com/jxnl/instructor)는 Pydantic 모델을 사용하여 **모든 LLM에서** Structured Output을 지원한다:

```python
import instructor
from openai import OpenAI
from pydantic import BaseModel

client = instructor.from_openai(OpenAI())

class UserInfo(BaseModel):
    name: str
    age: int
    interests: list[str]

user = client.chat.completions.create(
    model="gpt-4o-mini",
    response_model=UserInfo,
    messages=[{"role": "user", "content": "김철수, 28세, AI와 요리에 관심이 많습니다"}]
)
# user.name == "김철수", user.age == 28
```

Instructor는 OpenAI, Anthropic, Ollama, LiteLLM 등 **다양한 백엔드**를 지원한다.

### Outlines

[Outlines](https://github.com/dottxt-ai/outlines)는 **로컬 모델에서 constrained generation**을 제공한다:

```python
import outlines

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# JSON Schema 기반 생성
generator = outlines.generate.json(model, UserInfo)
result = generator("김철수에 대한 정보를 JSON으로 작성해줘")
```

Outlines는 토큰 레벨에서 유효한 출력만 생성하도록 **마스킹**하므로, 재시도 없이 100% 유효한 출력을 보장한다.

---

## 선택 가이드

| 상황 | 권장 도구 |
|------|----------|
| OpenAI API + Pydantic | `response_format=Model` (네이티브) |
| Anthropic API | Tool Use with `tool_choice` |
| 다양한 LLM 백엔드 | Instructor |
| 로컬 모델 (vLLM/Ollama) | Outlines 또는 Instructor |
| 복잡한 에이전트 | Function Calling + 실행 루프 |

---

## 정리

| 접근법 | 핵심 용도 | 신뢰성 |
|--------|---------|--------|
| Structured Output | JSON 형식 출력 강제 | 100% (constrained decoding) |
| Function Calling | 외부 도구 연동 | 높음 (스키마 강제) |
| Instructor | 크로스 플랫폼 구조화 | 높음 (재시도 로직) |
| Outlines | 로컬 모델 구조화 | 100% (토큰 마스킹) |

Structured Output은 LLM을 **"텍스트 생성기"에서 "구조화된 데이터 생성기"**로 전환시킨다. 이는 RAG, 에이전트, 데이터 파이프라인 등 모든 LLM 애플리케이션의 기반이 된다.
