<!-- infographic-hero -->
![CrewAI Deep Dive 핵심 요약](figures/infographic.svg)

*Figure: CrewAI Deep Dive 한 장 요약 인포그래픽*

# CrewAI 심층 분석: 역할 기반 멀티에이전트 협업

## 개요

CrewAI는 João Moura가 2024년 1월 공개한 역할 기반 멀티 에이전트 오케스트레이션 프레임워크다. AutoGen이 같은 시기 멀티 에이전트의 가능성을 보여줬다면 CrewAI는 그것을 가장 직관적으로 사용 가능한 형태로 다듬었다. 핵심 통찰은 단순하다. 사람의 협업이 직장의 "팀"으로 비유될 때 자연스러우니, 에이전트도 "팀(crew)"의 구성원으로 모델링하자는 것이다.

CrewAI의 추상화는 인간 조직의 은유를 그대로 따른다. Agent는 직원, Task는 업무 지시서, Crew는 팀 그 자체, Process는 팀의 운영 방식(순차 또는 위계)이다. 각 Agent는 role(직책), goal(목표), backstory(배경 이야기)를 가지며 이 세 텍스트가 시스템 프롬프트로 합성된다. 이 단순한 메타포 덕분에 비개발자도 코드를 읽을 수 있고 도메인 전문가가 프롬프트를 직접 튜닝할 수 있다.

빠른 프로토타이핑이 가능한 것이 가장 큰 강점이다. 잘 만들어진 멀티 에이전트 시스템을 LangGraph로 만들면 수백 줄이 필요하지만 CrewAI는 20-30줄로 충분하다. 단점은 정밀한 제어가 어렵다는 점인데, CrewAI 진영도 이를 인지하고 2024년 후반부터 Flows라는 결정적 워크플로 추상화를 추가해 두 추상화 레벨을 함께 제공하는 방향으로 진화했다.

CrewAI는 LangChain과 독립적으로 시작했지만 LangChain Tools 생태계와 호환된다. 라이선스는 MIT이며 GitHub 스타가 빠르게 늘어 약 3.5만 스타에 도달했고 엔터프라이즈 도입도 가속화되고 있다. 2024년 시리즈 A로 1,800만 달러를 조달하면서 매니지드 플랫폼 CrewAI Enterprise도 출시했다.

## 아키텍처

CrewAI 실행 모델은 다음 단계로 구성된다. Crew를 kickoff하면 Process에 따라 Task를 정렬한다. Sequential은 정의된 순서대로, Hierarchical은 매니저 에이전트가 위임 결정을 내린다. 각 Task는 할당된 Agent에 의해 실행되며 Agent는 자신의 도구 목록과 메모리를 사용해 작업을 완수한다. 이전 Task의 출력이 컨텍스트로 다음 Task에 전달되며 모든 결과가 Crew의 최종 출력으로 합성된다.

Agent 내부의 추론 엔진은 LangChain의 ReAct 에이전트와 유사한 Thought-Action-Observation 루프를 따른다. CrewAI 0.x 초기 버전은 LangChain ReAct를 그대로 사용했지만 1.0 이후 자체 구현으로 전환되어 의존성이 줄었다. Memory는 단기(short-term, 최근 대화), 장기(long-term, RAG로 누적된 학습), 엔터티(entity, 등장 객체 추적), 컨텍스츄얼(contextual, Task 간 컨텍스트)의 네 계층으로 구성된다.

CrewAI는 두 가지 추상화 레벨을 제공한다. Crews는 자율적 협업 모델로 비결정적이고, Flows는 결정적 이벤트 기반 워크플로다. 이 둘을 결합해 Flow 안에서 특정 step이 Crew를 호출하거나 Crew의 한 도구가 Flow를 호출하는 구조도 가능하다.

## 핵심 컴포넌트

### Agent

```python
from crewai import Agent
from crewai_tools import SerperDevTool, WebsiteSearchTool

researcher = Agent(
    role="시장 리서처",
    goal="에이전트 프레임워크 시장의 최신 동향을 정확히 파악한다",
    backstory=(
        "당신은 10년 경력의 IT 시장 분석가로, "
        "특히 오픈소스 개발자 도구의 채택 패턴 분석에 강하다. "
        "정량 데이터와 정성 인사이트를 균형 있게 제시한다."
    ),
    tools=[SerperDevTool(), WebsiteSearchTool()],
    verbose=True,
    allow_delegation=False,
)
```

role/goal/backstory 세 필드가 시스템 프롬프트로 결합된다. 이 메타포가 CrewAI 사용성의 핵심이다. 도메인 전문가가 코드를 거의 모르더라도 텍스트를 보고 의도를 이해하고 수정할 수 있다.

### Task

```python
from crewai import Task

research_task = Task(
    description=(
        "2025년 에이전트 프레임워크 시장의 최신 동향을 조사한다.\n"
        "- 주요 프레임워크 (LangGraph, CrewAI, AutoGen, OpenAI Agents SDK)의 채택률\n"
        "- 엔터프라이즈 도입 사례\n"
        "- 핵심 기술 트렌드 (HITL, A2A, MCP)"
    ),
    expected_output="마크다운 형식의 5개 섹션 조사 보고서",
    agent=researcher,
)
```

Task는 description(작업 지시), expected_output(원하는 출력 형태), agent(담당자)로 구성된다. expected_output을 명시하면 LLM이 형식을 더 정확히 따른다. async_execution=True로 설정하면 다른 Task와 병렬 실행된다.

### Crew와 Process

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, writer, reviewer],
    tasks=[research_task, writing_task, review_task],
    process=Process.sequential,
    verbose=True,
    memory=True,
)

result = crew.kickoff(inputs={"topic": "에이전트 프레임워크 2025"})
print(result.raw)
```

Sequential 프로세스는 Task 순서대로 실행한다. Hierarchical 프로세스를 쓰면 manager_llm을 추가로 지정해야 하며, 매니저 에이전트가 자율적으로 Task를 적절한 Agent에 위임한다.

### Tools

CrewAI는 자체 도구 카탈로그(crewai_tools)를 제공하며 LangChain Tools와도 호환된다.

```python
from crewai_tools import (
    SerperDevTool,        # 웹 검색
    WebsiteSearchTool,    # 사이트 내 RAG 검색
    PDFSearchTool,        # PDF RAG
    GithubSearchTool,     # GitHub 코드 검색
    DallETool,            # 이미지 생성
    CodeInterpreterTool,  # 코드 실행 (Docker 샌드박스)
)
```

사용자 정의 도구는 BaseTool을 상속하거나 데코레이터로 만든다.

```python
from crewai.tools import tool

@tool("Database Query")
def query_database(sql: str) -> str:
    """SQL 쿼리를 실행하고 결과를 JSON으로 반환한다."""
    return execute_sql(sql)
```

### Memory

```python
crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,
    embedder={
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"},
    },
)
```

memory=True를 설정하면 단기, 장기, 엔터티 메모리가 모두 활성화된다. 장기 메모리는 SQLite에 저장되어 다음 kickoff에서 재사용된다.

## 코드 예제: 시장 조사 → 보고서 작성 Crew

다음은 세 명의 에이전트가 협업해 시장 조사 보고서를 작성하는 완전한 예제다.

```python
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, WebsiteSearchTool

search_tool = SerperDevTool()
web_search = WebsiteSearchTool()

researcher = Agent(
    role="시장 리서처",
    goal="에이전트 프레임워크 2025 시장의 핵심 데이터를 수집한다",
    backstory="10년 경력의 IT 시장 분석가. 정량과 정성 분석에 모두 능하다.",
    tools=[search_tool, web_search],
    allow_delegation=False,
    verbose=True,
)

analyst = Agent(
    role="기술 애널리스트",
    goal="수집된 데이터에서 핵심 트렌드 3가지를 도출한다",
    backstory="MIT 출신 테크 애널리스트. 경쟁 구도 분석에 특화되어 있다.",
    allow_delegation=False,
    verbose=True,
)

writer = Agent(
    role="테크 블로그 에디터",
    goal="분석 결과를 한국어 1500자 블로그 포스트로 작성한다",
    backstory="20년 경력의 IT 매체 수석 에디터. 가독성과 정확성을 모두 잡는다.",
    allow_delegation=False,
    verbose=True,
)

research = Task(
    description=(
        "에이전트 프레임워크 2025 시장 동향 조사:\n"
        "- LangGraph, CrewAI, AutoGen, OpenAI Agents SDK 4종의 채택률\n"
        "- 엔터프라이즈 사례 5건\n"
        "- 핵심 기술 트렌드 5가지"
    ),
    expected_output="섹션별 정리된 조사 노트 (마크다운)",
    agent=researcher,
)

analysis = Task(
    description="조사 노트를 분석해 시장 트렌드 핵심 3가지를 도출한다.",
    expected_output="각 트렌드별 제목, 근거, 시사점이 정리된 분석 (마크다운)",
    agent=analyst,
    context=[research],
)

article = Task(
    description=(
        "분석 결과를 한국어 1500자 블로그 포스트로 작성한다. "
        "독자는 시니어 개발자이며 em-dash를 쓰지 않는다."
    ),
    expected_output="제목, 본문, 결론이 포함된 마크다운 포스트",
    agent=writer,
    context=[analysis],
    output_file="agent_market_2025.md",
)

crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research, analysis, article],
    process=Process.sequential,
    memory=True,
    verbose=True,
)

result = crew.kickoff(inputs={"topic": "에이전트 프레임워크 2025"})
print(result.raw)
```

20-30줄로 멀티 에이전트 시스템이 동작한다. 동일한 워크플로를 LangGraph로 만들면 100줄 이상이 필요하다. 이 차이가 CrewAI를 빠른 프로토타입의 표준으로 만든 이유다.

## 고급 기능

### Hierarchical Process

```python
crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[main_task],
    process=Process.hierarchical,
    manager_llm="gpt-4o",
    verbose=True,
)
```

Hierarchical 프로세스에서는 매니저 에이전트가 자동 생성되며 Task를 어떤 Agent에 위임할지 동적으로 결정한다. allow_delegation=True인 Agent는 다른 Agent에게 추가 위임도 가능하다.

### Flows: 결정적 워크플로

```python
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

class ResearchState(BaseModel):
    topic: str = ""
    research_notes: str = ""
    final_article: str = ""

class ResearchFlow(Flow[ResearchState]):
    @start()
    def begin(self):
        self.state.topic = "에이전트 프레임워크 2025"

    @listen(begin)
    def do_research(self):
        result = research_crew.kickoff(inputs={"topic": self.state.topic})
        self.state.research_notes = result.raw

    @listen(do_research)
    def write_article(self):
        result = writing_crew.kickoff(inputs={"notes": self.state.research_notes})
        self.state.final_article = result.raw

flow = ResearchFlow()
flow.kickoff()
```

Flows는 LangGraph와 비슷한 결정적 워크플로 추상화를 제공한다. @start, @listen, @router 데코레이터로 노드와 엣지를 정의한다. Flows 안에서 Crew를 호출하는 패턴이 권장된다.

### Training과 Replay

CrewAI는 인간 피드백 기반 학습을 지원한다.

```bash
crewai train -n 5 -f training_data.pkl
```

5번의 실행 동안 인간이 각 Task의 출력을 평가하면 그 피드백이 시스템 프롬프트에 통합되어 다음 실행부터 품질이 개선된다. crewai replay로 특정 Task부터 재실행도 가능하다.

## 다른 프레임워크와 비교

| 항목 | CrewAI | LangGraph | AutoGen | OpenAI Agents SDK |
|------|--------|-----------|---------|--------------------|
| 추상화 수준 | high-level (역할/팀) | low-level (그래프) | mid-level (대화) | mid-level (핸드오프) |
| 학습 곡선 | 매우 낮음 | 높음 | 중간 | 낮음 |
| 코드 분량 (3 에이전트) | 약 25줄 | 약 100줄 | 약 60줄 | 약 40줄 |
| 결정적 워크플로 | Flows (별도) | StateGraph | 미지원 | 미지원 |
| 사이클 제어 | 제한적 | 네이티브 | 대화 턴 | 도구 루프 |
| 체크포인트 | 미지원 | 빌트인 | 미지원 | 미지원 |
| HITL | 제한적 | 네이티브 | 제한적 | 미지원 |
| Memory 계층 | 4종 (자동) | 사용자 정의 | 메시지 히스토리 | 단순 컨텍스트 |
| LangChain Tools | 호환 | 네이티브 | 호환 | 호환 |
| Training/Replay | 빌트인 | 미지원 | 미지원 | 미지원 |
| 적합 시나리오 | 빠른 프로토타입, 도메인 전문가 협업 | 프로덕션 정밀 제어 | 협상/토론 시나리오 | OpenAI 생태계 |

CrewAI vs LangGraph는 추상화 레벨의 양극단을 차지한다. CrewAI는 high-level "팀" 추상화로 빠르게 시작하고, LangGraph는 low-level "그래프"로 정밀하게 제어한다. 두 프레임워크 모두 자기 자리를 갖고 있어 경쟁이 아닌 보완 관계로 보는 시각이 정착되었다. 실제로 CrewAI Flows는 LangGraph와 비슷한 결정적 모델을 도입하면서 추상화 격차를 줄이고 있다.

## 사용 사례

### 콘텐츠 자동화 파이프라인

마케팅 팀이 키워드 → 시장 조사 → 분석 → 초안 작성 → 톤 조정 Crew를 구성해 매일 5-10개 블로그 포스트를 자동 생성한다. role/goal/backstory가 도메인 전문가에게 직관적이라 마케터가 직접 튜닝한다.

### 사내 RAG 챗봇

CrewAI Crew가 사용자 질문을 받아 검색 에이전트, 답변 생성 에이전트, 검증 에이전트로 분업한다. 빠른 구현 속도 덕에 4시간 만에 PoC가 가능하다.

### 멀티스텝 영업 자동화

리드 발굴, 회사 조사, 메시지 초안, 후속 질문 생성을 Hierarchical 프로세스로 묶어 영업 팀의 반복 업무를 자동화한다.

### 학술 논문 작성 보조

리서치, 인용 정리, 요약, 영문 첨삭 에이전트가 협업하는 Crew로 논문 초안 작성을 보조한다.

## 한계

첫째, 정밀 제어가 어렵다. role/goal/backstory 메타포는 직관적이지만 LLM의 자율 의사결정에 많은 부분을 의존하므로 출력 일관성이 LangGraph 대비 낮다.

둘째, 사이클 제어가 제한적이다. Sequential과 Hierarchical 프로세스 외에 명시적 사이클이나 조건부 분기를 표현하기 어렵다. Flows로 일부 보완되지만 LangGraph만큼 정교하지 않다.

셋째, 체크포인트와 HITL이 약하다. 장시간 작업, 인간 승인 워크플로, 멀티 워커 분산 처리는 LangGraph가 우월하다.

넷째, 토큰 비용이 높을 수 있다. role/goal/backstory가 매 요청마다 시스템 프롬프트로 들어가고 multi-agent 협업이 메시지 히스토리를 누적시켜 토큰 소비가 빠르게 증가한다. 비용 모니터링이 필수다.

다섯째, 디버깅이 verbose 로그에 의존한다. LangSmith 같은 통합 트레이싱 플랫폼이 부재하여 verbose=True 출력을 직접 분석해야 한다. CrewAI Plus는 트레이싱 기능을 제공하지만 유료다.

## 관련 문서

- [[crewai|CrewAI]] - 모델 카드 (entry)
- [[langgraph-deep-dive|LangGraph 심층 분석]] - 그래프 기반 오케스트레이션 비교
- [[autogen-deep-dive|AutoGen 심층 분석]] - 대화 기반 협업 비교
- [[openai-agents-sdk|OpenAI Agents SDK]] - 핸드오프 중심 프레임워크
- [[mastra|Mastra]] - TypeScript 우선 풀스택 프레임워크
