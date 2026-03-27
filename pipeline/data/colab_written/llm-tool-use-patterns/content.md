# LLM Tool Use 패턴: Function Calling부터 Agent까지

## 들어가며

LLM은 텍스트를 생성하는 데 뛰어나지만, **현실 세계와 상호작용**하는 데는 한계가 있다. 실시간 데이터 조회, 계산, 파일 조작, API 호출 — 이런 작업은 LLM 혼자 할 수 없다.

**Tool Use**는 LLM에게 "도구"를 제공하여 이 한계를 극복하는 패러다임이다. 단순한 함수 호출에서 시작하여, 다중 도구 체이닝, 그리고 자율적 에이전트까지 — Tool Use의 발전 과정을 단계별로 살펴본다.

---

## 패턴 1: 단일 도구 호출

가장 기본적인 패턴. LLM이 하나의 외부 함수를 호출하고 결과를 응답에 통합한다.

```
사용자: "현재 비트코인 가격은?"
LLM: → get_crypto_price(symbol="BTC") 호출
     → 결과: {"price": 67234.50, "change_24h": "+2.3%"}
     → "현재 비트코인 가격은 $67,234.50이며, 24시간 동안 2.3% 상승했습니다."
```

적용 시나리오:
- 실시간 데이터 조회 (날씨, 주가, 환율)
- 간단한 계산 (수학, 단위 변환)
- 단일 API 호출 (이메일 발송, 캘린더 등록)

---

## 패턴 2: ReAct (Reasoning + Acting)

Yao et al.(2023)이 제안한 패턴. LLM이 **추론(Thought) → 행동(Action) → 관찰(Observation)** 루프를 반복한다.

```
질문: "오늘 서울과 도쿄의 기온 차이는?"

Thought: 서울과 도쿄의 현재 기온을 각각 조회해야 한다.
Action: get_weather(location="서울")
Observation: {"temperature": 22}

Thought: 서울은 22°C다. 이제 도쿄를 조회한다.
Action: get_weather(location="도쿄")
Observation: {"temperature": 18}

Thought: 서울 22°C - 도쿄 18°C = 4°C 차이.
Answer: 서울이 도쿄보다 4°C 높습니다. (서울 22°C, 도쿄 18°C)
```

ReAct의 핵심: **각 행동 전에 추론을 명시**함으로써, LLM이 왜 그 도구를 호출하는지 설명하고 결과를 논리적으로 통합한다.

---

## 패턴 3: 다중 도구 체이닝

여러 도구의 출력을 **파이프라인처럼 연결**하는 패턴.

```
질문: "삼성전자 최신 실적 보고서를 분석하고, 주요 수치를 차트로 만들어줘"

Step 1: web_search("삼성전자 2024 Q3 실적") → 검색 결과
Step 2: web_scrape(url) → 실적 데이터 추출
Step 3: analyze_data(data) → 핵심 수치 분석
Step 4: create_chart(data, type="bar") → 차트 이미지 생성
```

이전 도구의 출력이 다음 도구의 입력이 된다. LLM은 **전체 워크플로우를 계획하고 조율**하는 역할을 한다.

---

## 패턴 4: 병렬 도구 호출

독립적인 도구 호출을 **동시에 실행**하여 지연시간을 줄이는 패턴.

```python
# OpenAI의 parallel function calling
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "서울, 도쿄, 뉴욕의 날씨를 알려줘"}],
    tools=weather_tools,
    parallel_tool_calls=True,
)

# response.choices[0].message.tool_calls에 3개의 호출이 동시에 포함
```

---

## 패턴 5: 자율적 에이전트

LLM이 **목표를 받고 스스로 계획-실행-검증**을 반복하는 패턴. 인간의 개입 없이 복잡한 작업을 완수한다.

```
목표: "블로그 포스트를 작성하고 배포하라"

Plan:
1. 주제 리서치 (web_search)
2. 개요 작성 (generate_outline)
3. 본문 작성 (generate_content)
4. 이미지 생성 (generate_image)
5. CMS에 업로드 (api_call)
6. SNS 공유 (social_post)

→ 각 단계를 자율적으로 실행, 실패 시 재시도 또는 대안 탐색
```

대표적 구현:
- **AutoGPT**: 완전 자율형 (목표만 제공)
- **Claude Code**: 소프트웨어 개발 특화
- **SWE-Agent**: GitHub 이슈 자동 해결

---

## MCP (Model Context Protocol)

Anthropic이 제안한 **Tool Use 표준화 프로토콜**. 도구를 제공하는 서버와 LLM 클라이언트 사이의 통신을 표준화한다.

```
┌─────────────┐     MCP      ┌──────────────┐
│  LLM Client │ ◄──────────► │  MCP Server  │
│  (Claude)   │   JSON-RPC   │  (도구 제공)  │
└─────────────┘              └──────────────┘
```

MCP의 장점:
- **상호 운용성**: 한 번 구현한 도구를 여러 LLM 클라이언트에서 사용
- **표준화**: 도구 정의, 호출, 결과 반환의 통일된 형식
- **생태계**: Slack, GitHub, Google Drive 등의 MCP 서버가 이미 다수 존재

---

## Tool Use 설계 원칙

### 1. 도구 설명이 핵심

LLM이 도구를 올바르게 사용하려면 **명확한 설명**이 필요하다:

```python
# 나쁜 예
{"name": "search", "description": "검색"}

# 좋은 예
{"name": "web_search",
 "description": "인터넷에서 최신 정보를 검색합니다. "
                "실시간 데이터(날씨, 주가, 뉴스)나 "
                "학습 데이터에 없는 최신 정보가 필요할 때 사용합니다. "
                "일반 지식 질문에는 사용하지 마세요."}
```

### 2. 도구 수 관리

도구가 너무 많으면 LLM이 올바른 도구를 선택하기 어려워진다:
- **5~10개**: 대부분의 LLM이 잘 처리
- **10~20개**: 정밀한 설명 필요
- **20개 이상**: 도구 그룹화 또는 라우팅 필요

### 3. 오류 처리

도구 실행 실패 시 LLM에게 **의미 있는 에러 메시지**를 반환해야 한다:

```python
# 나쁜 예
return {"error": "500"}

# 좋은 예
return {"error": "API 할당량 초과. 1분 후 재시도하거나 대안 도구를 사용하세요."}
```

---

## 패턴 비교

| 패턴 | 복잡도 | 자율성 | 적용 시나리오 |
|------|--------|--------|-------------|
| 단일 도구 | 낮음 | 없음 | 간단한 데이터 조회 |
| ReAct | 중간 | 낮음 | 다단계 추론 + 도구 |
| 체이닝 | 중간 | 중간 | 순차적 워크플로우 |
| 병렬 호출 | 중간 | 낮음 | 독립적 다중 조회 |
| 자율 에이전트 | 높음 | 높음 | 복잡한 목표 달성 |

---

## 정리

Tool Use는 LLM을 **"텍스트 생성기"에서 "행동 주체"**로 전환시키는 핵심 패러다임이다. 단순한 Function Calling에서 시작하여, ReAct, 체이닝, 병렬 호출, 자율 에이전트까지 — 복잡도와 자율성의 스펙트럼 위에서 과제에 맞는 패턴을 선택하는 것이 핵심이다.

MCP의 등장으로 도구 생태계가 표준화되고 있으며, 이는 에이전트 시스템의 실용화를 가속화할 것이다.
