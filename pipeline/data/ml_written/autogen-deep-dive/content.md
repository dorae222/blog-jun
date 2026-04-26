<!-- infographic-hero -->
![AutoGen Deep Dive 핵심 요약](figures/infographic.svg)

*Figure: AutoGen Deep Dive 한 장 요약 인포그래픽*

# AutoGen 심층 분석: Microsoft의 대화형 멀티에이전트

## 개요

AutoGen은 Microsoft Research의 Wu et al.이 2023년 8월 공개한 대화 기반 멀티 에이전트 프레임워크로, 멀티 에이전트 영역의 대표적인 학술-산업 가교 프로젝트다. arXiv 논문(2308.08155)과 함께 오픈소스로 공개된 이후 학계에서는 멀티 에이전트 협업의 baseline 구현으로, 산업에서는 데이터 분석과 코드 자동화의 실험 플랫폼으로 빠르게 확산되었다. Microsoft 내부에서는 Office Copilot, Microsoft 365 Copilot의 일부 멀티 에이전트 시나리오 프로토타입에 사용되었다고 알려져 있다.

AutoGen의 핵심 통찰은 "에이전트 간 협업을 자연어 대화로 표현하자"는 것이다. CrewAI의 역할 기반 추상화나 LangGraph의 그래프 기반 추상화와 달리, AutoGen은 모든 에이전트가 메시지를 주고받는 채팅방의 참가자로 모델링된다. 이 메타포 덕분에 협상, 토론, 비평, 합의 같은 복잡한 사회적 상호작용 패턴이 자연스럽게 표현된다. 멀티 에이전트가 답을 두고 토론하면서 품질을 끌어올리는 시나리오는 AutoGen이 가장 강한 영역이다.

또 하나의 차별점은 코드 실행 에이전트(code execution agent)다. UserProxyAgent는 LLM이 생성한 코드를 자동으로 추출하여 Docker 샌드박스 또는 로컬 환경에서 실행하고 결과를 다시 LLM에 피드백한다. 이 자동화된 코드 생성→실행→오류 반영→재시도 루프는 데이터 분석, 수학 풀이, 자동화 스크립트 작성 같은 태스크에서 강력한 성능을 보인다.

2024년 후반 AutoGen은 v0.4로 메이저 리팩토링을 거쳤다. v0.2까지의 동기 메시지 패싱 모델이 비동기 액터 모델(asyncio 기반)로 전환되었고 분산 실행이 가능해졌다. 동시에 AutoGen Studio라는 노코드 UI가 정식 출시되어 비개발자도 멀티 에이전트 시스템을 GUI로 구성할 수 있게 되었다. v0.4부터는 Microsoft Research와 별개로 Magentic이라는 후속 프레임워크가 등장하면서 진영이 분화되는 양상이 있지만 AutoGen 자체는 여전히 활발히 유지보수되고 있다.

## 아키텍처

AutoGen v0.4의 아키텍처는 세 계층으로 구성된다. 최하단의 autogen-core는 비동기 액터 런타임으로 메시지 패싱과 분산 실행을 담당하고, 중간의 autogen-agentchat는 ConversableAgent와 GroupChat 같은 채팅 추상화를 제공하며, 최상단의 autogen-ext는 Docker 코드 실행기, OpenAI/Anthropic 클라이언트, MCP 통합 같은 확장 모듈을 모은다.

ConversableAgent는 모든 에이전트의 기본 클래스로 send/receive 인터페이스를 가진다. 메시지를 받으면 generate_reply가 호출되어 응답을 만들고, 그 응답이 다시 다른 에이전트에 전달된다. 응답 생성 로직은 LLM 호출, 코드 실행, 도구 호출, 인간 입력 중 하나 이상을 조합할 수 있다.

GroupChat은 여러 에이전트가 참여하는 채팅방이고 GroupChatManager가 발언 순서를 중재한다. Speaker selection 정책은 round_robin(순환), random(무작위), auto(LLM이 다음 발언자를 결정), manual(사람이 선택), 사용자 정의 함수 중에서 선택할 수 있다. auto 모드가 가장 흥미로운데 발언자 선택을 LLM에 위임함으로써 동적 협업이 가능해진다.

## 핵심 컴포넌트

### ConversableAgent

```python
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(model="gpt-4o")

assistant = AssistantAgent(
    name="Coder",
    model_client=model_client,
    system_message=(
        "당신은 시니어 Python 개발자다. "
        "사용자의 요구를 받아 작동하는 코드를 작성한다. "
        "코드는 ```python ... ``` 형태로 출력한다."
    ),
)
```

AssistantAgent는 LLM 기반 응답 생성을 담당하고, UserProxyAgent는 사용자(또는 코드 실행) 대리 역할이다. 두 에이전트가 짝을 이뤄 양자 대화를 구성하는 것이 가장 단순한 패턴이다.

### Code Execution

UserProxyAgent에 코드 실행기를 연결하면 LLM이 생성한 코드를 자동으로 실행한다.

```python
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor

executor = DockerCommandLineCodeExecutor(
    work_dir="./coding",
    image="python:3.12-slim",
    timeout=60,
)

user = UserProxyAgent(
    name="Executor",
    code_execution_config={"executor": executor},
    human_input_mode="NEVER",
)
```

Docker 샌드박스에서 격리 실행되므로 호스트 시스템에 영향을 주지 않는다. 실행 결과(stdout, stderr, exit code)가 메시지로 변환되어 다음 발언자에게 전달된다.

### GroupChat

```python
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination, MaxMessageTermination

team = SelectorGroupChat(
    participants=[coder, reviewer, executor],
    model_client=model_client,
    termination_condition=TextMentionTermination("APPROVED")
    | MaxMessageTermination(20),
)
```

SelectorGroupChat은 LLM이 다음 발언자를 동적으로 선택한다. RoundRobinGroupChat은 정해진 순서로 순환한다. termination_condition으로 종료 조건을 명시한다(특정 텍스트 등장, 최대 메시지 수 등).

### Tool 호출

```python
from autogen_core.tools import FunctionTool

def calculate(expression: str) -> str:
    """수식을 계산한다."""
    return str(eval(expression))

calc_tool = FunctionTool(calculate, description="안전한 수식 계산")

assistant = AssistantAgent(
    name="MathSolver",
    model_client=model_client,
    tools=[calc_tool],
    system_message="수학 문제를 도구를 사용해 정확히 계산하라.",
)
```

OpenAI function calling 형식으로 자동 변환된다. 도구 호출 결과는 메시지로 전달되어 LLM이 다음 응답을 생성한다.

### Termination

여러 종료 조건을 조합할 수 있다.

```python
from autogen_agentchat.conditions import (
    TextMentionTermination,
    MaxMessageTermination,
    TokenUsageTermination,
)

termination = (
    TextMentionTermination("APPROVED")
    | MaxMessageTermination(30)
    | TokenUsageTermination(max_total_token=20000)
)
```

OR 연산자로 조건들을 결합한다. 어느 하나라도 충족되면 그룹챗이 종료된다.

## 코드 예제: Coder + Reviewer + Executor GroupChat

다음은 Coder가 코드를 작성하고 Reviewer가 검토하며 Executor가 실행하는 전형적인 자동 코드 생성 패턴이다.

```python
import asyncio
from autogen_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import (
    TextMentionTermination,
    MaxMessageTermination,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor

async def main():
    model_client = OpenAIChatCompletionClient(model="gpt-4o")

    coder = AssistantAgent(
        name="Coder",
        model_client=model_client,
        system_message=(
            "당신은 시니어 Python 개발자. "
            "사용자 요구사항을 받아 코드를 작성한다. "
            "코드는 ```python ... ``` 블록으로 출력한다."
        ),
    )

    reviewer = AssistantAgent(
        name="Reviewer",
        model_client=model_client,
        system_message=(
            "당신은 시니어 코드 리뷰어. "
            "Coder가 작성한 코드를 검토하여 버그나 개선점을 지적한다. "
            "코드 품질이 만족스러우면 'APPROVED'라고 답한다."
        ),
    )

    executor_runtime = DockerCommandLineCodeExecutor(
        work_dir="./coding",
        image="python:3.12-slim",
        timeout=60,
    )
    await executor_runtime.start()

    executor = CodeExecutorAgent(
        name="Executor",
        code_executor=executor_runtime,
    )

    termination = (
        TextMentionTermination("APPROVED")
        & MaxMessageTermination(2)  # APPROVED 이후 추가 응답 최소화
    ) | MaxMessageTermination(20)

    team = SelectorGroupChat(
        participants=[coder, reviewer, executor],
        model_client=model_client,
        termination_condition=termination,
        selector_prompt=(
            "다음 발언자를 선택하라. "
            "Coder가 코드를 작성하면 Executor가 실행하고, "
            "결과가 나오면 Reviewer가 리뷰하라. "
            "Reviewer가 APPROVED를 말하면 종료다."
        ),
    )

    task = (
        "피보나치 수열의 처음 20개 항을 계산하고 시각화하는 Python 스크립트를 작성하라. "
        "matplotlib을 사용한다."
    )

    async for message in team.run_stream(task=task):
        print(f"[{message.source}] {message.content}")

    await executor_runtime.stop()

asyncio.run(main())
```

이 패턴이 흥미로운 점은 명시적 그래프 정의 없이도 협업이 일어난다는 것이다. selector_prompt에 "어떤 상황에서 누구를 호출할지"를 자연어로 적어두면 SelectorGroupChat이 그 지침을 따른다. LangGraph가 모든 흐름을 코드로 표현해야 하는 것과 정반대 접근이다.

## 고급 기능

### Nested Chat

에이전트가 다른 에이전트와 nested 대화를 시작할 수 있다.

```python
from autogen_agentchat.agents import AssistantAgent

class ResearcherWithSubChat(AssistantAgent):
    async def on_messages(self, messages, ctx):
        # 메인 대화에서 하위 대화 시작
        sub_team = RoundRobinGroupChat([searcher, summarizer])
        sub_result = await sub_team.run(task=messages[-1].content)
        return await super().on_messages(
            [TextMessage(content=sub_result.messages[-1].content, source="sub")],
            ctx,
        )
```

이 패턴이 멀티 에이전트의 계층화를 가능하게 한다.

### AutoGen Studio

AutoGen Studio는 v0.4에서 정식 출시된 노코드 UI다.

```bash
pip install autogenstudio
autogenstudio ui --port 8081
```

브라우저에서 에이전트, 도구, 워크플로를 GUI로 구성하고 실시간으로 실행 결과를 확인할 수 있다. 비개발자가 멀티 에이전트 시스템을 직접 만들 수 있게 해주는 것이 목표다.

### 분산 실행

v0.4의 비동기 액터 모델은 분산 실행을 지원한다. 에이전트를 별도 프로세스 또는 별도 머신에 배치하고 gRPC로 통신할 수 있다. 대규모 멀티 에이전트 시스템에서 단일 프로세스의 GIL 제약을 우회한다.

### Magentic-One

Microsoft Research가 AutoGen 위에 구축한 일반 목적 에이전트 시스템 Magentic-One은 Orchestrator + WebSurfer + FileSurfer + Coder + ComputerTerminal의 5명 팀으로 GAIA, AssistantBench 같은 벤치마크에서 SOTA에 근접한 성능을 보였다. 이 패턴은 AutoGen의 GroupChat을 활용한 대표적 예다.

## 다른 프레임워크와 비교

| 항목 | AutoGen | LangGraph | CrewAI | OpenAI Agents SDK |
|------|---------|-----------|--------|--------------------|
| 추상화 모델 | 대화 (메시지) | 그래프 (노드/엣지) | 팀 (역할/태스크) | 핸드오프 |
| Speaker Selection | LLM auto / 사용자 정의 | 명시적 라우팅 | Sequential/Hierarchical | 핸드오프 결정 |
| Code Execution | 빌트인 (Docker) | LangChain Tools | crewai_tools | 사용자 정의 |
| 노코드 UI | AutoGen Studio | LangGraph Studio | 미지원 | 미지원 |
| 분산 실행 | v0.4 비동기 액터 | 멀티 워커 | 미지원 | 미지원 |
| 체크포인트 | 미지원 | 빌트인 | 미지원 | 미지원 |
| HITL | 제한적 | 네이티브 | 제한적 | 미지원 |
| 학술 인용 | 다수 (논문 baseline) | 증가 중 | 적음 | 적음 |
| 적합 시나리오 | 토론/협상/코드 자동화 | 프로덕션 정밀 제어 | 빠른 프로토타입 | OpenAI 생태계 |

AutoGen은 대화 기반 협업과 코드 실행 자동화에서 가장 강하다. 토론, 협상, 비평, 합의 같은 복잡한 사회적 상호작용은 AutoGen의 자연스러운 영역이다. 반면 결정적 워크플로나 영속성이 필요한 시나리오는 LangGraph가 더 적합하다.

## 사용 사례

### 자동 데이터 분석

데이터 사이언티스트 에이전트와 코드 실행 에이전트가 짝을 이뤄 사용자가 자연어로 데이터셋 질문을 하면 SQL/pandas 코드가 생성-실행-요약되는 시스템. AutoGen의 코드 실행 자동화가 핵심 가치를 보인다.

### 학술 토론 시뮬레이션

찬성/반대/중립 에이전트가 GroupChat에서 주제를 토론하며 합의에 이르는 시뮬레이션. 학계 연구에서 LLM의 추론 다양성과 합의 동학을 측정하는 도구로 사용된다.

### 자동 소프트웨어 개발

PM, Coder, Reviewer, Tester 에이전트가 협업해 요구사항부터 테스트까지 완성하는 시스템. MetaGPT 같은 프로젝트가 비슷한 패턴이지만 AutoGen은 일반 목적 빌딩 블록을 제공한다.

### Magentic-One 일반 목적 에이전트

WebSurfer가 브라우저를 조작하고 FileSurfer가 파일을 읽고 Coder가 스크립트를 작성하고 ComputerTerminal이 실행하는 5명 팀이 일반 컴퓨터 작업 자동화 벤치마크에서 SOTA에 근접한다.

## 한계

첫째, 토큰 비용이 높다. 모든 에이전트가 같은 메시지 히스토리를 보면서 응답하므로 협업이 길어질수록 컨텍스트가 누적된다. 특히 SelectorGroupChat은 다음 발언자를 LLM에 위임하므로 추가 LLM 호출이 매 턴마다 발생한다.

둘째, 결정성이 낮다. LLM이 발언자 선택을 좌우하므로 동일 입력에 대해 매번 다른 흐름이 나타날 수 있다. 재현성이 중요한 시나리오에서는 RoundRobin이나 사용자 정의 함수를 사용해야 한다.

셋째, 영속성이 약하다. v0.4 시점에서도 LangGraph 같은 빌트인 체크포인터가 부재하여 장시간 작업, 인터럽트, 재개 시나리오는 사용자가 직접 구현해야 한다.

넷째, v0.2와 v0.4 사이 큰 API 변화가 있다. 인터넷 자료가 v0.2 기준인 경우가 많아 최신 코드와 호환되지 않는다. 학습 시 버전 확인이 필수다.

다섯째, AutoGen Studio가 LangGraph Studio나 Dify에 비해 기능이 제한적이다. 노코드로 시작은 가능하지만 복잡한 시나리오는 결국 코드로 돌아와야 한다.

## 관련 문서

- [[autogen|AutoGen]] - 모델 카드 (entry)
- [[langgraph-deep-dive|LangGraph 심층 분석]] - 그래프 기반 오케스트레이션 비교
- [[crewai-deep-dive|CrewAI 심층 분석]] - 역할 기반 협업 비교
- [[openai-agents-sdk|OpenAI Agents SDK]] - 핸드오프 중심 프레임워크
- [[metagpt|MetaGPT]] - 소프트웨어 회사 시뮬레이션 멀티 에이전트
