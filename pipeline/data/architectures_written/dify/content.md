<!-- infographic-hero -->
![Dify 핵심 요약](figures/infographic.svg)

*Figure: Dify 한 장 요약 인포그래픽*

# Dify: 노코드 워크플로와 RAG GUI를 결합한 오픈소스 LLMOps 1위 플랫폼

**LangGenius** · **2023-05-15** · **LLMOps Platform** · **Apache-2.0 (modified)**

## 개요

Dify는 LangGenius가 2023년 5월 출시한 오픈소스 LLMOps 플랫폼이다. 같은 시기에 등장한 LangChain, LlamaIndex, Flowise 등이 모두 코드 또는 노드 그래프 중심이었다면, Dify는 처음부터 통합 웹 콘솔로 비개발자도 직접 LLM 애플리케이션을 만들 수 있게 설계되었다. 시각적 워크플로 빌더, 프롬프트 IDE, 데이터셋 관리, RAG 파이프라인 GUI, 도구 마켓플레이스, API 노출, 사용량 모니터링이 한 화면에서 제공된다.

도입 배경에는 LLM 애플리케이션의 가치 사슬에서 PM과 도메인 전문가의 참여가 필수적이라는 인식이 있다. 코드 기반 프레임워크는 엔지니어가 모든 프롬프트, 도구, 평가를 작성해야 하지만 실제로는 의사, 변호사, 마케터, 운영자가 도메인 지식을 직접 입력해야 품질이 올라간다. Dify는 이들을 LLM 애플리케이션 빌더의 일급 사용자로 두기 위해 노코드 인터페이스를 우선했고, 이 결정이 폭발적인 성장의 원인이 되었다.

2024년부터 2025년에 걸쳐 GitHub 스타가 빠르게 증가해 약 13만 스타에 도달했고 AI 애플리케이션 빌더 카테고리에서 오픈소스 1위 위치를 차지했다. 라이선스는 Apache 2.0을 기반으로 하지만 멀티 테넌트 SaaS 형태로 재배포하는 것을 제한하는 추가 조항이 붙어 있어 완전한 OSI 호환은 아니다.

## 아키텍처

Dify는 풀스택 웹 애플리케이션이다. 백엔드는 Python(Flask + Celery + PostgreSQL + Redis)으로 구성되고 벡터 DB로는 Weaviate, Qdrant, Milvus, pgvector 중 선택할 수 있다. 프론트엔드는 Next.js로 구축된 SPA다. 모든 컴포넌트는 Docker Compose 한 번으로 띄울 수 있으며, 프로덕션은 공식 Kubernetes Helm 차트가 제공된다. SaaS 버전(dify.ai)도 운영되어 셀프호스트와 매니지드를 선택할 수 있다.

핵심은 다음 다섯 모듈이다. Studio(애플리케이션 빌더), Knowledge(데이터셋 관리), Tools(도구 마켓플레이스), Marketplace(플러그인 카탈로그), Monitoring(사용량과 로그). 각 모듈은 REST API로도 접근 가능해 자동화 스크립트나 CI/CD 파이프라인에 통합할 수 있다.

## 핵심 컴포넌트

### Studio: 애플리케이션 빌더

Studio는 네 가지 애플리케이션 타입을 지원한다.

| 타입 | 설명 | 사용 예 |
|------|------|---------|
| Chatbot | 단일 프롬프트 + 컨텍스트 변수 + 데이터셋 | 고객 지원 봇 |
| Agent | LLM이 도구를 자유롭게 호출 (Function Calling/ReAct) | 리서치 어시스턴트 |
| Workflow | 시각적 노드 그래프 (입출력 명시) | 결정적 데이터 처리 |
| Chatflow | Workflow + 대화 컨텍스트 | 복잡한 멀티턴 봇 |

### Workflow 노드 카탈로그

Workflow 빌더에는 다음 노드가 제공된다.

- Start / End: 워크플로의 진입과 종료
- LLM: 프롬프트와 모델을 지정하여 텍스트 생성
- Knowledge Retrieval: 데이터셋에서 의미 검색
- Code: Python 또는 JavaScript 스니펫 실행 (샌드박스)
- IF/ELSE: 조건 분기
- Iteration: 배열을 받아 sub-workflow를 반복 실행
- HTTP Request: 외부 REST API 호출
- Tool: Marketplace의 도구 호출
- Parameter Extractor: 자유 텍스트에서 구조화된 변수 추출
- Question Classifier: 사용자 입력을 정의된 카테고리로 분류
- Variable Aggregator: 여러 분기 결과를 단일 출력으로 병합

Workflow Variables는 노드 간 데이터를 명명된 변수로 전달한다. 예: `{{ #1721823045123.text #}}`처럼 특정 노드의 출력을 참조한다.

### Knowledge: RAG 파이프라인 GUI

데이터셋 모듈은 PDF, Word, Markdown, HTML, 웹페이지를 업로드하면 자동으로 청킹과 임베딩을 수행한다. 청킹은 General(고정 크기)과 Parent-Child(부모-자식 청크)를 선택할 수 있고, 검색은 keyword, semantic, full-text, hybrid의 네 가지 모드를 지원한다. 재순위화(rerank) 모델도 GUI에서 활성화하면 끝이다.

### Prompt IDE

system 메시지와 user 메시지를 분리해 작성하고 컨텍스트 변수를 `{{var}}` 문법으로 삽입한다. 출력 형식 검증(JSON Schema), 모델 매개변수(temperature, top_p, frequency_penalty), 모델 비교(같은 프롬프트를 GPT-4o, Claude, Gemini에 동시 실행) 같은 기능이 한 화면에 모여 있다.

### Tools / Marketplace

Marketplace에서 Google Search, Slack, Wikipedia, Stable Diffusion, Wolfram Alpha 등 100개 이상의 도구를 즉시 추가할 수 있다. 사용자 정의 도구는 OpenAPI 명세 또는 Python 코드로 등록 가능하다.

## 코드 예제

Workflow는 GUI에서 만들지만 결과는 REST API로 호출된다. 다음은 Python 클라이언트에서 Dify 워크플로를 호출하는 예다.

```python
import requests

DIFY_API = "https://api.dify.ai/v1"
API_KEY = "app-xxxxxxxxxxxx"

response = requests.post(
    f"{DIFY_API}/workflows/run",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "inputs": {
            "topic": "Agent 프레임워크 시장 동향",
            "depth": "deep",
        },
        "response_mode": "blocking",
        "user": "user-123",
    },
    timeout=120,
)

result = response.json()
print(result["data"]["outputs"]["report"])
```

스트리밍 모드는 `response_mode: "streaming"`으로 변경하면 SSE로 중간 결과를 받는다.

```python
with requests.post(
    f"{DIFY_API}/workflows/run",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"inputs": {...}, "response_mode": "streaming", "user": "u1"},
    stream=True,
) as r:
    for line in r.iter_lines():
        if line.startswith(b"data: "):
            print(line[6:].decode())
```

워크플로 정의 자체는 GUI에서 편집되지만 백업과 버전 관리를 위해 DSL(YAML) 형태로 export/import가 가능하다.

```yaml
version: "0.1.0"
kind: app
data:
  name: research-pipeline
  mode: workflow
  graph:
    nodes:
      - id: start
        type: start
        data:
          variables:
            - variable: topic
              type: text-input
              required: true
      - id: search
        type: knowledge-retrieval
        data:
          dataset_ids: ["ds-arxiv-papers"]
          retrieval_mode: hybrid
      - id: llm
        type: llm
        data:
          model:
            provider: openai
            name: gpt-4o
          prompt_template:
            - role: system
              text: "다음 자료로 1500자 리포트를 작성한다."
            - role: user
              text: "{{#search.result#}}"
    edges:
      - source: start
        target: search
      - source: search
        target: llm
```

## 사용 사례

### 사내 지식 챗봇

비개발자 PM이 Knowledge 모듈에 사내 문서를 업로드하고 Chatbot을 만들어 Slack에 임베드한다. 코드 한 줄 없이 RAG 챗봇이 완성된다.

### 콘텐츠 자동화

마케팅 팀이 Workflow를 만들어 키워드 입력 → 트렌드 검색 → 초안 생성 → 톤 조정 → CMS 업로드를 자동화한다. 도메인 전문가가 프롬프트를 직접 튜닝한다.

### 멀티 모델 비교 평가

같은 프롬프트를 GPT-4o, Claude Opus, Gemini 2.5 Pro에 동시 실행하여 출력을 나란히 비교한다. 모델 선택을 데이터 기반으로 결정한다.

### 엔터프라이즈 셀프호스트

데이터 주권이 중요한 금융, 의료, 정부 기관이 자체 인프라에 Dify를 배포해 외부 SaaS 의존을 제거한다.

## 비교

| 항목 | Dify | LangGraph | n8n + LangChain | LangSmith |
|------|------|-----------|------------------|-----------|
| 노코드 빌더 | 빌트인 | 미지원 | 노드 기반 | 미지원 |
| RAG GUI | 빌트인 | 미지원 | 별도 구성 | 미지원 |
| 프롬프트 IDE | 빌트인 | 미지원 | 미지원 | 빌트인 |
| 도구 마켓플레이스 | 100여 개 | LangChain 도구 | 400여 개 통합 | 미지원 |
| 셀프호스트 | 무료 | 무료 (라이브러리) | 무료 | 유료 |
| LLM 공급자 | 100여 개 | LangChain 통합 | LangChain 통합 | LangChain 통합 |
| 트레이싱 | 빌트인 | LangSmith 통합 | 제한적 | 핵심 기능 |
| 멀티테넌트 | 워크스페이스 | 없음 | 없음 | 워크스페이스 |
| GitHub 스타 | 약 13만 | 약 1.5만 | 약 7만 | 비공개 |

Dify는 노코드와 통합 콘솔 측면에서 압도적이다. 단, 정밀한 사이클 제어나 상태 관리가 필요한 복잡한 에이전트는 여전히 LangGraph 같은 코드 프레임워크가 더 강력하다.

## 한계

첫째, 라이선스 제약이 있다. 멀티 테넌트 SaaS 재배포 금지 조항 때문에 Dify를 wrapping해 자체 SaaS로 판매하기는 어렵다. 둘째, 노코드의 양면성이 있다. 비개발자 친화적이지만 정교한 분기, 재시도, 상태 관리는 여전히 코드가 더 표현력이 높다. 복잡한 에이전트는 LangGraph로 만들고 Dify는 빠른 프로토타입과 도메인 전문가 협업에 쓰는 분리 전략이 권장된다. 셋째, 셀프호스트 운영 비용이 있다. PostgreSQL, Redis, 벡터 DB, Celery worker, 웹 서버를 모두 관리해야 하며, 1인 개발자에게는 부담이 된다. 넷째, 워크플로 버전 관리가 git 기반이 아니라 GUI 내부 히스토리에 의존하므로 코드 리뷰 문화와 충돌할 수 있다.

## 관련 문서

- [[langgraph-deep-dive|LangGraph 심층 분석]] - 코드 기반 그래프 오케스트레이션 비교
- [[crewai-deep-dive|CrewAI 심층 분석]] - 역할 기반 멀티 에이전트 비교
- [[mcp|Model Context Protocol]] - 도구 통합 표준 프로토콜
