---
title: "AutoGen: AI 에이전트 프레임워크"
slug: autogen
category: agent
tags: ["AutoGen", "Conversable Agent", "Microsoft", "Multi-Agent"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.418821+00:00"
architecture_entry: autogen
---

# AutoGen: 대화 기반 멀티 에이전트 프레임워크

**Microsoft** · **2023-08-16** · **Multi-Agent Framework** · **MIT**

## 개요

AutoGen은 여러 LLM 에이전트가 대화(conversation)를 통해 협력하여 복잡한 작업을 완수하는 멀티 에이전트 프레임워크다. Microsoft Research의 Wu et al.이 2023년 8월 논문 "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation"과 함께 공개한 이 오픈소스 프레임워크는, 단일 LLM의 한계를 다중 에이전트 협업으로 극복하는 패러다임을 대중화한 선구적 프로젝트다.

AutoGen의 핵심 철학은 **"대화가 곧 연산(conversation as computation)"**이다. 전통적 소프트웨어에서 함수 호출이 연산의 기본 단위라면, AutoGen에서는 에이전트 간의 메시지 교환 자체가 작업을 수행하는 프로세스가 된다. 각 에이전트는 LLM 호출, 코드 실행, 인간 입력 중 하나 이상을 조합하여 응답을 생성한다. 특히 코드 작성 $\rightarrow$ 실행(샌드박스) $\rightarrow$ 오류 반영 $\rightarrow$ 재시도의 자동 루프는 데이터 분석, 수학 문제 풀이, 소프트웨어 개발 등 광범위한 태스크에 적용된다.

멀티 에이전트 시스템의 핵심 도전 과제 중 하나는 에이전트 간 협업의 효율성이다. $N$개의 에이전트가 자유롭게 대화하면 통신 복잡도는 $O(N^2)$이 되며, 대화가 발산하거나 루프에 빠질 위험이 있다. AutoGen은 양자 대화(two-agent)와 GroupChat 패턴을 통해 이 복잡도를 관리하면서도, 유연한 에이전트 간 협업을 가능하게 한다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

AutoGen의 핵심 추상화는 **ConversableAgent** 클래스로, 모든 에이전트가 이를 상속하여 `send()`/`receive()` 인터페이스로 통신한다.

### 에이전트 유형

| 에이전트 타입 | 역할 | 핵심 기능 |
|-------------|------|----------|
| `AssistantAgent` | LLM 기반 추론 | 코드 생성, 분석, 대화 |
| `UserProxyAgent` | 인간/코드 대리인 | 코드 실행, 인간 입력 중계 |
| `GroupChatManager` | 그룹 대화 중재 | 발언 순서 결정, 메시지 라우팅 |
| `CompressibleAgent` | 컨텍스트 관리 | 대화 이력 압축 |

### 대화 패턴

AutoGen은 양자 대화(two-agent)와 그룹 대화(GroupChat) 두 가지 패턴을 지원한다.

```python
from autogen import AssistantAgent, UserProxyAgent

# 에이전트 정의
assistant = AssistantAgent(
    name="코딩_어시스턴트",
    llm_config={"model": "gpt-4"},
    system_message="Python 코드를 작성하는 전문가입니다."
)

user_proxy = UserProxyAgent(
    name="사용자",
    human_input_mode="NEVER",
    code_execution_config={"work_dir": "coding", "use_docker": True}
)

# 대화 시작 - 에이전트가 코드를 생성하고 실행
user_proxy.initiate_chat(
    assistant,
    message="피보나치 수열의 처음 20개 항을 계산하고 시각화해주세요."
)
```

그룹 대화에서는 GroupChatManager가 에이전트 목록과 발언 규칙을 관리한다.

```python
from autogen import GroupChat, GroupChatManager

group_chat = GroupChat(
    agents=[planner, coder, reviewer],
    messages=[],
    max_round=12,
    speaker_selection_method="auto"  # LLM이 다음 발언자 결정
)
manager = GroupChatManager(groupchat=group_chat, llm_config=llm_config)
```

### 코드 실행 루프

AutoGen의 가장 강력한 기능 중 하나는 자동 코드 실행 루프다. AssistantAgent가 코드를 생성하면 UserProxyAgent가 Docker 샌드박스에서 자동으로 실행하고, 오류 발생 시 에러 메시지를 다시 AssistantAgent에 전달하여 수정-재실행 루프를 자동화한다.

$$\text{Generate Code} \xrightarrow{\text{execute}} \text{Result/Error} \xrightarrow{\text{feedback}} \text{Fix Code} \xrightarrow{\text{execute}} \cdots$$

이 루프는 `max_consecutive_auto_reply` 파라미터로 최대 반복 횟수를 제한할 수 있으며, 일반적으로 3~5회의 반복으로 대부분의 코딩 작업을 성공적으로 완료한다.

### Human-in-the-Loop

`human_input_mode`를 통해 세 단계의 인간 개입 수준을 설정할 수 있다.
- `ALWAYS`: 매 턴마다 인간 확인 필요
- `TERMINATE`: 종료 조건 충족 시에만 인간 확인
- `NEVER`: 완전 자동 실행

## 핵심 혁신

1. **대화 기반 컴퓨테이션**: 에이전트 간 대화를 연산의 기본 단위로 정의함으로써, 복잡한 워크플로를 자연스러운 대화 흐름으로 구현할 수 있게 했다. 이는 전통적인 파이프라인/DAG 기반 워크플로 엔진과 근본적으로 다른 접근이다.

2. **자동 코드 실행 루프**: Generate $\rightarrow$ Execute $\rightarrow$ Debug의 사이클이 자동화되어, 데이터 분석이나 시각화 같은 코드 집약적 작업에서 강력한 효과를 발휘한다.

3. **유연한 인간 개입(Human-in-the-Loop)**: 작업의 중요도에 따라 인간 개입 수준을 3단계로 조절할 수 있어, 자동화와 안전성 사이의 균형을 유연하게 관리한다.

4. **이기종 LLM 지원**: `config_list`를 통해 GPT-4, Claude, Gemini, Ollama 로컬 모델 등 다양한 LLM 백엔드를 에이전트별로 독립적으로 설정할 수 있어, 비용과 성능을 유연하게 최적화한다.

## 벤치마크/성능

| 태스크 유형 | 단일 에이전트 | AutoGen (멀티) | 향상 |
|-----------|-------------|---------------|------|
| GSM8K (수학) | 56.9% | ~76%+ | +19%p |
| 데이터 분석 | 완성도 낮음 | 높은 완성도 | 유의미 |
| 코드 생성+실행 | 에러 시 중단 | 자동 디버깅 | 자동 복구 |
| 멀티파일 프로젝트 | 불가 | 역할 분담 | 가능 |

AutoGen의 멀티 에이전트 대화 접근법은 수학 문제 풀이(MATH 벤치마크)에서 코드 실행 피드백 루프를 통해 정답률이 약 20%p 향상되었고, 복잡한 데이터 분석 태스크에서는 에이전트 간 역할 분담을 통해 더 정확하고 완성도 높은 결과를 도출했다.

## 구현

**자동화된 데이터 분석 파이프라인**: 분석가 에이전트가 SQL 쿼리를 작성하고, 코드 실행 에이전트가 이를 실행하며, 시각화 에이전트가 차트를 생성하는 3-에이전트 파이프라인을 구성할 수 있다.

**소프트웨어 개발 팀 시뮬레이션**: 설계자, 개발자, 리뷰어 에이전트로 구성된 그룹 채팅에서, 요구사항 분석부터 코드 리뷰까지의 개발 프로세스를 자동화할 수 있다.

**리서치 어시스턴트**: 검색 에이전트가 최신 논문을 수집하고, 분석 에이전트가 핵심 내용을 추출하며, 작성 에이전트가 보고서를 생성하는 연구 보조 워크플로를 구축할 수 있다.

## 관련 모델

AutoGen은 ReAct의 추론-행동 루프에서 영감을 받아 멀티 에이전트로 확장했다. 이후 CrewAI(역할 기반 간소화), MetaGPT(SOP 기반 구조화), LangGraph(그래프 기반 제어) 등 후속 프레임워크에 직접적 영향을 미쳤다. Microsoft는 2024년 AutoGen 0.4에서 비동기 이벤트 기반 아키텍처로 재설계하여 분산 에이전트 실행을 지원한다.

## 참고 자료

- Wu et al., "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation", arXiv:2308.08155, 2023
- [AutoGen GitHub Repository](https://github.com/microsoft/autogen)
- [AutoGen Documentation](https://microsoft.github.io/autogen)

## 관련 문서

- [[react|ReAct]] — 영감
- [[crewai|CrewAI]] — 영감을 줌
- [[metagpt|MetaGPT]] — 영감을 줌
