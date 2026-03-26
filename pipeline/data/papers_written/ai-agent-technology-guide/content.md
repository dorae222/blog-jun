# AI Agent 기술 지도: ReAct에서 멀티에이전트까지

## 개요

AI Agent는 LLM을 핵심 두뇌로 활용하여 도구를 사용하고, 계획을 수립하며, 환경과 상호작용하면서 자율적으로 작업을 수행하는 AI 시스템입니다. 단순한 텍스트 생성을 넘어, 코드 작성, 웹 브라우징, 데이터 분석, 시스템 운영 등 실제 작업을 수행할 수 있는 AI의 최전선입니다.

2022년 [ReAct](/post/react)의 등장으로 본격화된 AI Agent 연구는 단일 에이전트에서 멀티에이전트 시스템, 에이전트 간 통신 프로토콜, 프로덕션 에이전트 프레임워크까지 빠르게 발전하고 있습니다. 이 가이드는 AI Agent 기술의 **전체 지형도**를 체계적으로 정리합니다.

### 왜 AI Agent가 중요한가?

LLM은 지식과 추론 능력을 갖추고 있지만, 그 자체로는 텍스트를 생성하는 것이 전부입니다. Agent는 LLM에 **행동 능력(agency)**을 부여하여 실제 세계와 상호작용하게 합니다. 코드를 실행하고, API를 호출하고, 파일을 편집하고, 웹을 탐색하는 등 인간 개발자와 유사한 작업을 수행할 수 있습니다. 이는 AI의 실용적 가치를 결정짓는 핵심 요소이며, 현재 가장 빠르게 발전하는 분야 중 하나입니다.

---

## 핵심 흐름: AI Agent 기술 발전 타임라인

### Phase 1: 추론 프레임워크 (2022-2023)

LLM의 추론 능력을 강화하는 프롬프팅 기법과 행동 프레임워크가 등장한 시기입니다.

**추론 강화 기법**

- [Chain-of-Thought (CoT)](/post/cot) (2022): 단계별 추론을 유도하는 프롬프팅. "Let's think step by step"으로 복잡한 문제를 분해. LLM의 추론 능력을 극적으로 향상.

- [Self-Consistency](/post/self-consistency) (2022): 여러 추론 경로를 생성하고 다수결로 최종 답변 선택. CoT의 신뢰도를 높이는 앙상블 기법.

- [Tree of Thoughts (ToT)](/post/tree-of-thoughts) (2023): 추론을 트리 구조로 확장. 여러 경로를 탐색하고 평가하여 최적 경로 선택. BFS/DFS 탐색 전략.

**추론 + 행동 통합**

- [ReAct](/post/react) (2022): **Reasoning + Acting** 패러다임. LLM이 사고(Thought) → 행동(Action) → 관찰(Observation) 루프를 반복. 외부 도구(검색, 계산 등)를 호출하며 태스크 수행. AI Agent의 기본 프레임워크로 자리잡음.

- [Reflexion](/post/reflexion) (2023): 실패에서 학습하는 에이전트. 이전 시도의 결과를 반성(reflection)하여 다음 시도 개선. 에피소딕 메모리를 활용한 자기 개선. 인간의 경험 학습을 모방.

### Phase 2: 도구 활용과 코딩 에이전트 (2023-2024)

에이전트가 외부 도구를 효과적으로 활용하고, 코드를 자율적으로 작성하는 능력이 발전한 시기입니다.

**도구 활용**

- [Toolformer](/post/toolformer) (2023): LLM이 스스로 도구 사용법을 학습. 텍스트 내에 API 호출을 삽입하는 방식. 계산기, 검색 엔진, 번역기, 일정 관리 등 자율적 도구 호출.

- [Logic-LM](/post/logic-lm) (2023): 논리 추론에 형식 언어(formal language) 활용. LLM이 논리식을 생성하고 솔버로 검증.

**코딩 에이전트**

- [SWE-Agent](/post/swe-agent) (2024): GitHub 이슈를 자동으로 해결하는 코딩 에이전트. Agent-Computer Interface(ACI) 설계. SWE-bench에서 높은 이슈 해결률.

- [OpenHands](/post/openhands) (2024): 오픈소스 AI 소프트웨어 개발 에이전트. 코드 편집, 터미널 실행, 웹 브라우징을 통합. 사용자 친화적 인터페이스.

- [Claude Code](/post/claude-code) (2025): Anthropic의 프로덕션급 코딩 에이전트. 터미널에서 직접 코드 작성, 리팩토링, 디버깅. 실무에서의 AI 에이전트 활용 사례.

- [Devin](/post/devin) (2024): Cognition Labs의 AI 소프트웨어 엔지니어. 자율적으로 코딩 태스크 수행.

**컴퓨터 사용 에이전트**

- [Computer Use](/post/computer-use) (2024): Anthropic의 컴퓨터 사용 에이전트. 마우스, 키보드를 직접 조작하여 GUI 기반 태스크 수행. 웹 브라우저, 데스크톱 애플리케이션 조작 가능.

- [Operator](/post/operator) (2025): OpenAI의 웹 기반 에이전트. 웹 브라우저를 통한 태스크 자동화.

### Phase 3: 멀티에이전트 시스템 (2023-2024)

여러 에이전트가 협력하여 복잡한 작업을 수행하는 멀티에이전트 시스템이 등장했습니다.

- [AutoGen](/post/autogen) (2023): Microsoft의 멀티에이전트 대화 프레임워크. 여러 에이전트가 역할을 분담하여 대화를 통해 문제 해결. 인간-에이전트 협업 지원. 유연한 에이전트 구성.

- [MetaGPT](/post/metagpt) (2023): 소프트웨어 회사를 모방한 멀티에이전트 시스템. PM, 아키텍트, 엔지니어, QA 등 역할 분담. 구조화된 출력(SOP)으로 코드 품질 향상.

- [CrewAI](/post/crewai) (2024): 역할 기반 AI 에이전트 오케스트레이션 프레임워크. 에이전트에게 역할, 목표, 도구를 할당. 태스크 체인과 위임(delegation) 지원.

- [LangGraph](/post/langraph) (2024): LangChain 기반 그래프 워크플로우 프레임워크. 에이전트 상태 관리와 순환 그래프 지원. 복잡한 에이전트 로직의 시각화와 디버깅.

- [Manus](/post/manus) (2025): 범용 AI 에이전트. 웹 브라우징, 코딩, 데이터 분석 등 다양한 태스크 수행.

- [Goose](/post/goose) (2025): Block의 오픈소스 AI 에이전트. 개발자 워크플로우 자동화.

### Phase 4: 에이전트 통신 프로토콜 (2024-현재)

에이전트 간의 표준화된 통신 프로토콜과 도구 연결 규약이 등장했습니다.

- [MCP (Model Context Protocol)](/post/mcp) (2024): Anthropic이 제안한 모델-도구 연결 프로토콜. LLM이 외부 도구와 데이터 소스에 표준화된 방식으로 접근. 클라이언트-서버 구조로 도구 제공자와 소비자 분리.

- [A2A (Agent-to-Agent Protocol)](/post/a2a) (2025): Google이 제안한 에이전트 간 통신 프로토콜. 서로 다른 프레임워크로 만든 에이전트끼리 직접 통신. Agent Card로 능력 선언, Task로 작업 요청.

- [AG-UI (Agent-User Interaction Protocol)](/post/ag-ui) (2025): 에이전트-사용자 간 표준 상호작용 프로토콜. 스트리밍 이벤트 기반 실시간 소통. 프론트엔드 프레임워크와의 통합.

**에이전트 스케일링 연구**

- [Towards a Science of Scaling Agent Systems](/post/towards-a-science-of-scaling-agent-systems) (2025): 에이전트 시스템의 스케일링 법칙 연구. 에이전트 수 증가에 따른 성능 변화 분석.

### Phase 5: 추론 특화 에이전트 (2024-현재)

추론 능력을 극대화한 에이전트 모델이 등장했습니다.

- [O1](/post/o1) (2024): OpenAI의 추론 모델. 내부적으로 Chain-of-Thought를 수행하여 복잡한 문제 해결.
- [O3](/post/o3) (2025): 향상된 추론 능력. 과학, 수학, 코딩에서 전문가 수준.
- [O3-Pro](/post/o3-pro) (2025): 프로 수준의 추론 특화 모델.
- [O4-Mini](/post/o4-mini) (2025): 효율적인 추론 모델.
- [DeepSeek-R1](/post/deepseek-r1): RL 기반 추론 학습. 순수 강화학습으로 추론 능력 획득.

---

## 주요 Agent 기술 요약 테이블

### 추론 프레임워크

| 기법 | 연도 | 핵심 기여 | 특징 |
|------|------|----------|------|
| [CoT](/post/cot) | 2022 | 단계별 추론 | 프롬프팅 |
| [Self-Consistency](/post/self-consistency) | 2022 | 다중 경로 투표 | 앙상블 |
| [ReAct](/post/react) | 2022 | 추론 + 행동 통합 | Agent 기본 |
| [Tree of Thoughts](/post/tree-of-thoughts) | 2023 | 트리 탐색 추론 | 탐색 |
| [Reflexion](/post/reflexion) | 2023 | 자기 반성 학습 | 자기 개선 |

### 도구 활용 / 코딩 에이전트

| 모델/도구 | 연도 | 핵심 기여 | 특징 |
|----------|------|----------|------|
| [Toolformer](/post/toolformer) | 2023 | 자율 도구 학습 | Self-supervised |
| [SWE-Agent](/post/swe-agent) | 2024 | GitHub 이슈 해결 | ACI |
| [OpenHands](/post/openhands) | 2024 | 오픈소스 개발 에이전트 | 통합 환경 |
| [Claude Code](/post/claude-code) | 2025 | 프로덕션 코딩 에이전트 | CLI |
| [Devin](/post/devin) | 2024 | AI 소프트웨어 엔지니어 | 자율 코딩 |
| [Computer Use](/post/computer-use) | 2024 | GUI 조작 에이전트 | 스크린 기반 |
| [Operator](/post/operator) | 2025 | 웹 에이전트 | 브라우저 |

### 멀티에이전트 프레임워크

| 프레임워크 | 연도 | 핵심 기여 | 특징 |
|----------|------|----------|------|
| [AutoGen](/post/autogen) | 2023 | 멀티에이전트 대화 | Microsoft |
| [MetaGPT](/post/metagpt) | 2023 | SOP 기반 협업 | 역할 분담 |
| [CrewAI](/post/crewai) | 2024 | 역할 기반 오케스트레이션 | 위임 지원 |
| [LangGraph](/post/langraph) | 2024 | 그래프 워크플로우 | 상태 관리 |
| [Manus](/post/manus) | 2025 | 범용 에이전트 | 다목적 |
| [Goose](/post/goose) | 2025 | 개발자 에이전트 | 오픈소스 |

### 에이전트 프로토콜

| 프로토콜 | 연도 | 핵심 기여 | 제안자 |
|---------|------|----------|--------|
| [MCP](/post/mcp) | 2024 | 모델-도구 연결 | Anthropic |
| [A2A](/post/a2a) | 2025 | 에이전트 간 통신 | Google |
| [AG-UI](/post/ag-ui) | 2025 | 에이전트-사용자 상호작용 | CopilotKit |

---

## Agent의 핵심 구성 요소

### 1. LLM (두뇌)

에이전트의 추론과 의사결정을 담당합니다. 강력한 추론 능력과 도구 호출 능력을 갖춘 LLM이 필수적입니다.

- [GPT-4](/post/gpt-4), [Claude 4](/post/claude-4), [Gemini 2.5](/post/gemini-2-5) 등 프론티어 모델
- 추론 특화: [O3](/post/o3), [DeepSeek-R1](/post/deepseek-r1)

### 2. 도구 (행동 능력)

에이전트가 외부 세계와 상호작용하는 수단입니다.

- **코드 실행**: 터미널, 인터프리터
- **웹 접근**: 브라우저, API 호출
- **파일 시스템**: 파일 읽기/쓰기/편집
- **외부 서비스**: 데이터베이스, 검색 엔진

### 3. 메모리 (경험)

- **단기 메모리**: 현재 대화 컨텍스트
- **장기 메모리**: 과거 경험, 학습된 패턴
- **[RAG](/post/rag)**: 외부 지식 검색 및 활용

### 4. 계획 (전략)

- **순차 계획**: 단계별 작업 분해 ([ReAct](/post/react))
- **트리 탐색**: 여러 경로 탐색 ([ToT](/post/tree-of-thoughts))
- **자기 반성**: 실패에서 학습 ([Reflexion](/post/reflexion))

### 5. 통신 (협력)

- **도구 연결**: [MCP](/post/mcp) — 표준화된 도구 접근
- **에이전트 간**: [A2A](/post/a2a) — 에이전트 협력
- **사용자 소통**: [AG-UI](/post/ag-ui) — 인터페이스

---

## Agent 아키텍처 패턴

### Pattern 1: 단일 에이전트 (ReAct Loop)

가장 기본적인 에이전트 패턴입니다.

```
User → LLM → [Think → Act → Observe] → ... → Response
```

- [ReAct](/post/react): 사고-행동-관찰 루프
- [Claude Code](/post/claude-code): 프로덕션 코딩 에이전트
- [SWE-Agent](/post/swe-agent): GitHub 이슈 해결

### Pattern 2: 반성 에이전트 (Reflect & Retry)

실패를 분석하고 전략을 수정하여 재시도합니다.

```
User → Agent → [Try → Fail → Reflect → Retry] → Success
```

- [Reflexion](/post/reflexion): 에피소딕 메모리 기반 자기 개선

### Pattern 3: 멀티에이전트 대화

여러 에이전트가 대화를 통해 협업합니다.

```
User → Agent A ←→ Agent B ←→ Agent C → Result
```

- [AutoGen](/post/autogen): 유연한 에이전트 대화
- [CrewAI](/post/crewai): 역할 기반 오케스트레이션

### Pattern 4: 조직형 멀티에이전트

소프트웨어 조직을 모방한 구조적 협업입니다.

```
PM → Architect → Engineer → QA → Deploy
```

- [MetaGPT](/post/metagpt): SOP 기반 소프트웨어 개발

---

## 추천 학습 경로

### 초심자 (Agent 입문)

추론 프레임워크와 기본 에이전트를 이해합니다.

1. [CoT (Chain-of-Thought)](/post/cot) — 단계별 추론의 기본
2. [ReAct](/post/react) — Reasoning + Acting 프레임워크
3. [Toolformer](/post/toolformer) — 도구 활용의 원리
4. [Claude Code](/post/claude-code) — 프로덕션 에이전트 체험
5. [MCP](/post/mcp) — 도구 연결 프로토콜 이해

### 중급 (에이전트 구축)

실제 에이전트를 구축하고 멀티에이전트를 이해합니다.

1. [Reflexion](/post/reflexion) — 자기 개선 에이전트
2. [Tree of Thoughts](/post/tree-of-thoughts) — 고급 추론 전략
3. [SWE-Agent](/post/swe-agent) + [OpenHands](/post/openhands) — 코딩 에이전트
4. [AutoGen](/post/autogen) + [CrewAI](/post/crewai) — 멀티에이전트 프레임워크
5. [LangGraph](/post/langraph) — 에이전트 워크플로우 설계
6. [A2A](/post/a2a) + [AG-UI](/post/ag-ui) — 에이전트 통신

### 고급 (에이전트 시스템 설계)

프로덕션 에이전트 시스템을 설계하고 운영합니다.

1. [MetaGPT](/post/metagpt) — 조직형 멀티에이전트 설계
2. [Computer Use](/post/computer-use) + [Operator](/post/operator) — GUI 에이전트
3. [Towards a Science of Scaling Agent Systems](/post/towards-a-science-of-scaling-agent-systems) — 스케일링 연구
4. [DeepSeek-R1](/post/deepseek-r1) — RL 기반 추론 학습
5. 프로덕션 에이전트 안전성, 모니터링, 비용 최적화

---

## Agent 벤치마크

에이전트의 능력을 평가하는 주요 벤치마크입니다.

| 벤치마크 | 평가 영역 | 관련 포스트 |
|---------|----------|------------|
| SWE-bench | 코딩 (GitHub 이슈 해결) | [SWE-Agent](/post/swe-agent) |
| AgentBench | 범용 에이전트 능력 | [AgentBench](/post/agentbench) |
| WebArena | 웹 태스크 자동화 | [Computer Use](/post/computer-use) |
| GAIA | 일반 AI 능력 평가 | - |

---

## 관련 카테고리

- [AI/ML 아키텍처 로드맵](/post/ai-ml-architecture-roadmap) — 전체 AI/ML 지형도
- [LLM 핵심 논문 가이드](/post/llm-paper-guide) — Agent의 두뇌가 되는 LLM
- [AI 핵심 기법 총정리](/post/ai-core-techniques-guide) — RAG, CoT 등 Agent가 활용하는 기법
