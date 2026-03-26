# CrewAI: 역할 기반 AI 에이전트 오케스트레이션

**CrewAI Inc.** · **2024-01-01** · **Multi-Agent Framework** · **MIT**

## 개요

CrewAI는 역할 기반 멀티 에이전트 오케스트레이션 프레임워크로, AI 에이전트를 '크루(crew)' 단위로 조직하여 복잡한 작업을 분업 처리하도록 설계되었다. 2024년 초 CrewAI Inc.가 공개한 이 오픈소스 프레임워크는, AutoGen의 대화 중심 접근 방식과 달리 선언적 API를 통해 에이전트 역할과 태스크를 명확히 분리하여 직관적인 워크플로 구성을 가능하게 한다.

CrewAI의 핵심 비유는 **실제 회사 조직**이다. 리서처, 작가, 편집자처럼 각 에이전트에 명확한 역할(role), 목표(goal), 배경(backstory)을 부여하고, 이들이 정해진 태스크를 순차적 또는 계층적으로 처리한다. 이 직관적인 추상화 덕분에 프로그래밍 경험이 적은 사용자도 쉽게 멀티 에이전트 시스템을 구축할 수 있어, 빠른 속도로 커뮤니티가 성장했다.

멀티 에이전트 프레임워크 선택에서 핵심 트레이드오프는 **사용 편의성 vs 유연성**이다. AutoGen은 자유로운 대화를 통해 높은 유연성을 제공하지만 학습 곡선이 가파르고, LangGraph는 그래프 기반으로 정밀한 제어가 가능하지만 보일러플레이트가 많다. CrewAI는 이 스펙트럼에서 "사용 편의성" 측에 위치하며, 가장 적은 코드로 프로덕션 수준의 멀티 에이전트 시스템을 구축할 수 있다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

CrewAI의 아키텍처는 세 가지 핵심 추상화를 중심으로 구성된다.

### Agent

역할, 목표, 배경 스토리를 가진 자율적 단위다. 각 에이전트는 독립적인 LLM 설정과 도구 목록을 보유한다.

### Task

에이전트가 수행할 구체적 작업 명세다. 설명, 기대 출력, 담당 에이전트를 정의하며, `context` 파라미터로 이전 태스크의 결과를 참조할 수 있다.

### Crew

에이전트와 태스크의 조합으로, 실행 프로세스 타입과 전체 설정을 정의한다.

```python
from crewai import Agent, Task, Crew, Process

# 에이전트 정의
researcher = Agent(
    role="시니어 리서처",
    goal="최신 AI 트렌드에 대한 심층 분석 제공",
    backstory="10년 경력의 AI 연구원으로 논문 분석에 전문성이 있다",
    tools=[search_tool, arxiv_tool],
    llm="gpt-4"
)

writer = Agent(
    role="기술 블로거",
    goal="복잡한 기술 주제를 일반 독자가 이해하기 쉬운 글로 변환",
    backstory="기술 매거진에서 5년간 기고한 프리랜서 작가",
    llm="claude-3-5-sonnet"
)

editor = Agent(
    role="편집장",
    goal="글의 정확성, 가독성, SEO 최적화를 검증",
    backstory="미디어 업계 15년 경력의 편집 전문가",
    llm="gpt-4o"
)

# 태스크 정의
research_task = Task(
    description="2025년 AI 에이전트 프레임워크 동향을 조사하라",
    expected_output="핵심 트렌드 5가지와 각각의 상세 분석",
    agent=researcher
)

writing_task = Task(
    description="조사 결과를 바탕으로 블로그 포스트를 작성하라",
    expected_output="2000자 이상의 기술 블로그 글",
    agent=writer,
    context=[research_task]
)

editing_task = Task(
    description="블로그 포스트의 품질을 검토하고 최종 수정하라",
    expected_output="발행 가능한 최종 원고",
    agent=editor,
    context=[writing_task]
)

# 크루 실행
crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research_task, writing_task, editing_task],
    process=Process.sequential
)

result = crew.kickoff()
```

### 프로세스 타입

| 프로세스 | 실행 방식 | 적합한 상황 |
|---------|----------|------------|
| Sequential | 태스크가 정의된 순서대로 실행 | 의존성이 명확한 파이프라인 |
| Hierarchical | 매니저 에이전트가 위임 | 동적 의사결정이 필요한 작업 |
| Consensual | 에이전트 간 합의 (실험적) | 품질 검증이 중요한 작업 |

### 도구 생태계

CrewAI는 LangChain 도구와 완벽히 호환되며, 자체 도구 데코레이터(`@tool`)를 통해 커스텀 도구를 쉽게 정의할 수 있다.

```python
from crewai_tools import tool

@tool("데이터베이스 조회")
def query_database(query: str) -> str:
    """SQL 쿼리를 실행하여 결과를 반환한다"""
    result = db.execute(query)
    return str(result)
```

## 핵심 혁신

1. **선언적 에이전트 정의**: Agent, Task, Crew의 세 가지 추상화만으로 복잡한 멀티 에이전트 시스템을 구축할 수 있다. AutoGen의 명시적 대화 관리에 비해 코드량이 $\frac{1}{3}$ 이하로 줄어든다.

2. **역할 기반 전문화**: 각 에이전트에 역할과 배경을 부여함으로써, LLM이 해당 전문가의 관점에서 사고하도록 유도한다. 이는 프롬프트 엔지니어링의 페르소나 기법을 구조화한 것이다.

3. **에이전트별 LLM 독립 설정**: 비용이 많이 드는 분석 작업에는 GPT-4를, 단순 요약에는 GPT-4o-mini를 사용하는 등 태스크 특성에 맞는 모델 배분이 가능하다.

4. **계층적 프로세스**: 매니저 에이전트가 자동으로 작업을 분배하고 결과를 검증하는 계층적 구조를 프레임워크 수준에서 지원한다.

## 벤치마크/성능

| 측면 | CrewAI | AutoGen | MetaGPT | LangGraph |
|------|--------|---------|---------|-----------|
| 핵심 패러다임 | 역할 기반 크루 | 대화 기반 | SOP 기반 | 그래프 기반 |
| 학습 곡선 | **낮음** | 중간 | 중간 | 높음 |
| 유연성 | 중간 | 높음 | 낮음 | **매우 높음** |
| 코드 실행 | 도구 기반 | Docker 샌드박스 | 내장 | 노드 함수 |
| 프로덕션 지원 | CrewAI Enterprise | 커뮤니티 | 커뮤니티 | LangGraph Cloud |
| 최소 코드 라인 | **~30줄** | ~60줄 | ~50줄 | ~80줄 |

## 구현

**콘텐츠 제작 파이프라인**: 리서처 $\rightarrow$ 작가 $\rightarrow$ 편집자 크루를 구성하여, 주제 조사부터 초안 작성, 교정까지의 콘텐츠 제작 프로세스를 자동화한다.

**고객 지원 에스컬레이션**: 1차 상담 에이전트, 기술 전문가 에이전트, 매니저 에이전트로 구성된 크루가 고객 문의를 분류하고 적절한 수준에서 처리한다.

**시장 분석 보고서**: 데이터 수집 에이전트, 분석 에이전트, 시각화 에이전트, 보고서 작성 에이전트가 협업하여 포괄적인 시장 분석 보고서를 생성한다.

## 관련 모델

CrewAI는 AutoGen의 멀티 에이전트 협업 아이디어에서 영감을 받아, 선언적 API와 역할 기반 추상화로 사용 편의성을 극대화했다. LangChain 도구 생태계와의 호환성이 높으며, CrewAI Enterprise를 통해 에이전트 모니터링, 배포, 비용 추적 기능을 제공한다.

## 참고 자료

- [CrewAI GitHub Repository](https://github.com/crewAIInc/crewAI)
- [CrewAI Documentation](https://docs.crewai.com)

## 관련 문서

- [[autogen|AutoGen]] — 영감
