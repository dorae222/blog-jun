# CAMEL: LLM 멀티에이전트 협력의 선구자

## 논문 개요

:::info
**Paper:** CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society (arXiv:2303.17760, NeurIPS 2023)
**저자:** Guohao Li, Hasan Abed Al Kader Hammoud et al.
**소속:** King Abdullah University of Science and Technology (KAUST)
**코드:** [GitHub: camel-ai/camel](https://github.com/camel-ai/camel)
:::

LLM 하나가 강력하다면, **두 개의 LLM이 협력하면 어떨까?** CAMEL은 이 질문에 대한 최초의 체계적 연구다.

CAMEL(Communicative Agents for "Mind" Exploration)은 두 LLM 에이전트에게 **서로 다른 역할**(예: "Python 프로그래머"와 "주식 트레이더")을 부여하고, 주어진 과제를 **자율적으로 협력**하여 해결하도록 하는 프레임워크다.

---

## 핵심 아이디어

### Role-Playing Framework

CAMEL의 설계는 단순하면서도 효과적이다:

1. **AI User**: 지시를 내리는 역할 (예: "주식 트레이더")
2. **AI Assistant**: 지시를 수행하는 역할 (예: "Python 프로그래머")
3. **Task**: 두 에이전트가 함께 해결할 과제

```
Task: "주식 포트폴리오 최적화 프로그램 개발"

AI User (주식 트레이더):
  "과거 5년 주가 데이터를 가져오는 함수를 먼저 만들어주세요."

AI Assistant (Python 프로그래머):
  "yfinance 라이브러리를 사용하여 다음과 같이 구현합니다..."

AI User:
  "좋습니다. 이제 Markowitz 평균-분산 최적화를 구현해주세요."

AI Assistant:
  "scipy.optimize를 활용하여..."
```

### Inception Prompting

CAMEL의 핵심 기술은 **Inception Prompting**이다. 각 에이전트에게 역할, 과제, 행동 규칙을 상세히 기술한 **시스템 프롬프트**를 제공하여, 인간 개입 없이 자율적으로 대화를 진행하도록 한다.

시스템 프롬프트에 포함되는 규칙:
- 항상 역할에 충실할 것
- 구체적인 지시를 제공할 것 (AI User)
- 지시를 정확히 이행할 것 (AI Assistant)
- 과제가 완료되면 `<CAMEL_TASK_DONE>` 토큰을 출력할 것

이 규칙들은 대화가 **목표 지향적**으로 진행되도록 하며, 무한 루프나 주제 이탈을 방지한다.

---

## 실험: AI Society와 Code

### AI Society 시나리오

50개의 다양한 역할 쌍 × 다양한 과제로 대규모 대화를 생성:

역할 예시:
- 의사 + 환자 → 건강 상담
- 교수 + 학생 → 연구 논문 작성
- CEO + 엔지니어 → 제품 설계

관찰된 행동:
- 에이전트들이 **자연스럽게 하위 과제를 분해**하고 순차적으로 해결
- 역할에 따른 **전문 용어와 관점** 차이가 나타남
- 대부분의 과제가 10-30 턴 내에 종료 신호 도달

### Code Generation 시나리오

프로그래밍 과제에서 두 에이전트가 협력:
- AI User가 요구사항을 명세
- AI Assistant가 코드를 작성하고 설명
- AI User가 피드백하고 추가 요구사항 제시

단일 에이전트 대비 장점:
- **요구사항의 점진적 정교화**: 한 번에 완벽한 프롬프트를 작성할 필요 없음
- **자연스러운 디버깅**: AI User가 출력을 검토하고 수정 요청
- **구조화된 개발**: 기능을 단계별로 구현

---

## 대화 데이터셋: 규모의 힘

CAMEL의 또 다른 기여는 **대규모 멀티에이전트 대화 데이터셋** 생성이다:

| 시나리오 | 역할 쌍 | 대화 수 | 메시지 수 |
|---------|--------|--------|----------|
| AI Society | 50×50 | ~25,000 | ~500,000 |
| Code | 50×50 | ~25,000 | ~500,000 |

이 데이터셋은 멀티에이전트 연구의 벤치마크로 활용되며, 에이전트 행동 분석의 기반 자료가 된다.

---

## 발견과 통찰

### 1. 역할의 힘

같은 GPT-4 모델이라도 **부여된 역할에 따라 행동이 크게 달라진다**. "Python 전문가" 역할의 에이전트는 "초보 프로그래머" 역할보다 더 정교하고 효율적인 코드를 생성했다.

### 2. 협력의 효과

두 에이전트의 대화는 단일 에이전트의 일방적 생성보다 **더 구조화되고 완결적인 결과물**을 생산하는 경향이 있다. AI User의 피드백이 AI Assistant의 출력 품질을 높이는 역할을 한다.

### 3. Flattening 문제

장기 대화에서 에이전트들이 점차 **역할에서 벗어나는(role-flattening)** 현상이 관찰되었다. 초반에는 역할에 충실하지만, 대화가 길어질수록 일반적인 LLM 응답 패턴으로 수렴한다.

### 4. 환각의 전파

한 에이전트가 생성한 잘못된 정보가 다른 에이전트에 의해 **검증 없이 수용**되는 경우가 발생했다. 멀티에이전트 시스템에서 환각은 단일 에이전트보다 더 위험할 수 있다.

---

## 후속 연구에의 영향

CAMEL은 멀티에이전트 LLM 시스템의 **선구적 연구**로, 이후 다양한 프레임워크에 영향을 미쳤다:

| 프레임워크 | 연도 | CAMEL과의 관계 |
|----------|------|--------------|
| AutoGen (Microsoft) | 2023 | 역할 기반 대화 구조 확장, 인간 참여 추가 |
| CrewAI | 2024 | 역할/도구/프로세스의 3축 설계 |
| LangGraph | 2024 | 그래프 기반 에이전트 워크플로우 |
| MetaGPT | 2023 | 소프트웨어 개발 팀 시뮬레이션 |

---

## 한계

### 1. 비용

두 에이전트가 10-30 턴 대화 → 단일 에이전트의 **10-30배 API 호출**. 복잡한 과제에서는 비용이 급격히 증가한다.

### 2. 수렴 보장 없음

에이전트 간 대화가 항상 목표에 수렴하지는 않는다. 무한 루프, 반복적 동의, 주제 이탈 등의 failure mode가 존재한다.

### 3. 검증 메커니즘 부재

AI User가 AI Assistant의 출력을 "검증"하지만, 이 검증 자체가 LLM에 의존하므로 **진정한 검증이 아니다**. 외부 실행 환경(코드 실행, 테스트 등)과의 연동이 필요하다.

## Paper Summary

| 항목 | 내용 |
|------|------|
| 제목 | CAMEL: Communicative Agents for "Mind" Exploration of Large Language Model Society |
| 저자 | Guohao Li et al. |
| 소속 | KAUST |
| 연도 | 2023 |
| 학회 | NeurIPS 2023 |
| 원문 | [arXiv:2303.17760](https://arxiv.org/abs/2303.17760) |
| 코드 | [GitHub: camel-ai/camel](https://github.com/camel-ai/camel) |
| 핵심 키워드 | Multi-Agent, Role-Playing, Cooperative AI, Inception Prompting, LLM Society |
