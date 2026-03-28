# MetaGPT: SOP 기반 멀티 에이전트 소프트웨어 개발

**DeepWisdom** · **2023-08-01** · **Multi-Agent Framework** · **MIT**

## 개요

MetaGPT는 소프트웨어 개발 조직의 표준 운영 절차(SOP, Standard Operating Procedures)를 멀티 에이전트 시스템에 적용한 프레임워크다. Hong et al.(DeepWisdom, 2023)이 논문 "MetaGPT: Meta Programming for Multi-Agent Collaborative Framework"에서 발표한 이 시스템은, 실제 소프트웨어 회사의 조직 구조와 업무 프로세스를 AI 에이전트 시스템으로 재현한다.

MetaGPT의 핵심 통찰은 **"비구조적 대화는 멀티 에이전트 시스템의 효율을 떨어뜨린다"**는 것이다. AutoGen에서 에이전트들이 자유롭게 대화하면, 대화가 발산하거나 중복 작업이 발생하는 문제가 있었다. MetaGPT는 각 에이전트(역할)에 명확한 입력/출력 산출물을 정의하고, SOP에 따라 순차적으로 작업을 진행하게 함으로써 이 문제를 해결한다.

이 접근의 이론적 배경은 소프트웨어 공학의 **폭포수(Waterfall) 모델**과 유사하다. 요구사항 분석 $\rightarrow$ 시스템 설계 $\rightarrow$ 구현 $\rightarrow$ 테스트의 순차적 절차를 따르되, 각 단계의 산출물이 다음 단계의 입력이 되는 구조화된 파이프라인을 에이전트 시스템으로 자동화한다. 이는 에이전트 간 불필요한 대화를 제거하고, 구조화된 산출물을 통해 환각(hallucination)을 줄이는 효과가 있다.

![MetaGPT 아키텍처 — SOP 기반 역할 분담과 구조화된 산출물 흐름의 멀티 에이전트 소프트웨어 개발 구조](figures/architecture.svg)

*Figure 1: MetaGPT 아키텍처 — Product Manager, Architect, Engineer, QA Engineer 역할을 SOP에 따라 배치하고, 구조화된 산출물(PRD, 시스템 설계, 코드, 테스트)이 순차적으로 전달되는 폭포수 프로세스이다.*

아래 그림은 MetaGPT의 SOP 기반 에이전트 협업 구조를 보여준다. 실제 소프트웨어 개발 팀의 폭포수 프로세스와 MetaGPT 에이전트의 역할별 산출물 흐름을 비교할 수 있다.

![MetaGPT SOP 기반 협업 구조 — 실제 개발팀과 동일한 역할 분담과 산출물 흐름](figures/fig_1.png)
*Figure 1: MetaGPT 에이전트 협업과 SOP — Product Manager, Architect, Engineer, QA Engineer가 순차적으로 산출물을 생성하며, 인간 상호작용은 요구사항 입력과 최종 검수로 최소화된다. (Source: arXiv 2308.00352)*

## 아키텍처 상세

MetaGPT의 아키텍처는 역할(Role), 액션(Action), 메시지 풀(Message Pool)의 세 핵심 개념으로 구성된다.

### 역할(Role) 시스템

| 역할 | 입력 | 산출물 | 형식 |
|------|------|--------|------|
| Product Manager | 사용자 요구사항 | PRD (Product Requirements Document) | 마크다운 |
| Architect | PRD | 시스템 설계서 (클래스 다이어그램, API 명세) | Mermaid/JSON |
| Engineer | 설계서 | 소스 코드 | Python/JS |
| QA Engineer | 코드 | 테스트 케이스 + 실행 결과 | pytest |

### 메시지 풀(Message Pool)

다음 그림은 메시지 풀의 발행-구독 패턴과 반복적 프로그래밍의 실행 피드백 루프를 보여준다.

![MetaGPT 메시지 풀과 반복적 프로그래밍 — 발행-구독 패턴과 실행 피드백 루프](figures/fig_2.jpg)
*Figure 2: 메시지 풀과 반복적 프로그래밍 — (좌) 에이전트들이 공유 메시지 풀에 구조화된 메시지를 발행하고 필요한 것만 구독한다. (우) Engineer 에이전트가 코드 실행 피드백을 받아 반복적으로 수정하는 루프. (Source: arXiv 2308.00352)*

MetaGPT의 가장 독특한 설계 요소다. 모든 에이전트의 산출물은 공유 메시지 풀에 발행(publish)되며, 각 에이전트는 자신에게 필요한 메시지 타입만 구독(subscribe)한다.

$$\text{Agent}_i \xrightarrow{\text{publish}} \text{Message Pool} \xrightarrow{\text{subscribe}} \text{Agent}_j$$

이 발행-구독(pub-sub) 패턴은 에이전트 간 직접적인 대화를 제거하고, 각 에이전트가 정확히 필요한 정보만 소비하도록 보장한다. 이는 토큰 비용 절감과 정보 오염 방지에 효과적이다.

```python
# MetaGPT 역할 정의 예시
from metagpt.roles import Role
from metagpt.actions import WritePRD, WriteDesign, WriteCode

class ProductManager(Role):
    name: str = "Alice"
    profile: str = "Product Manager"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WritePRD])
        self._watch([UserRequirement])  # 구독: 사용자 요구사항

class Architect(Role):
    name: str = "Bob"
    profile: str = "Architect"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteDesign])
        self._watch([WritePRD])  # 구독: PRD 문서

class Engineer(Role):
    name: str = "Charlie"
    profile: str = "Engineer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([WriteCode])
        self._watch([WriteDesign])  # 구독: 설계서
```

### SOP 기반 워크플로

```
사용자 요구사항: "온라인 서점 웹 애플리케이션을 만들어줘"
    |
    v
Product Manager → PRD 생성
    - 사용자 스토리, 기능 요구사항, 비기능 요구사항
    - 유스케이스 다이어그램 (Mermaid)
    |
    v
Architect → 시스템 설계서
    - 클래스 다이어그램 (Mermaid)
    - 시퀀스 다이어그램
    - API 엔드포인트 명세 (JSON)
    - 데이터 모델 정의
    |
    v
Engineer → 코드 구현
    - 파일별 분리된 소스 코드
    - 의존성 관리 (requirements.txt)
    - 모듈 간 인터페이스 준수
    |
    v
QA Engineer → 테스트
    - 단위 테스트 작성 (pytest)
    - 테스트 실행 및 결과 보고
    - 실패 시 Engineer에 피드백 → 수정 루프
```

### 구조화된 산출물

아래는 MetaGPT의 전체 개발 프로세스 상세도이다. "2048 퍼즐 게임"이라는 한 줄 요구사항에서 각 역할이 생성하는 실제 산출물(PRD, 설계서, 코드, 테스트)을 확인할 수 있다.

![MetaGPT 전체 개발 프로세스 — 한 줄 요구사항에서 완성된 소프트웨어까지의 상세 흐름](figures/fig_3.jpg)
*Figure 3: MetaGPT 개발 프로세스 상세 — Product Manager의 PRD, Architect의 시스템 설계, Engineer의 코드 구현, QA Engineer의 테스트까지 각 단계의 실제 산출물을 보여준다. (Source: arXiv 2308.00352)*

각 역할은 자유 텍스트가 아닌 구조화된 형식(JSON, 마크다운, Mermaid 다이어그램)으로 산출물을 생성한다. 이는 하위 역할이 상위 산출물을 파싱하고 활용하는 데 있어 정확도를 높인다.

## 핵심 혁신

1. **SOP 기반 에이전트 협업**: 자유 대화 대신 구조화된 절차를 따르게 함으로써, 멀티 에이전트 시스템의 일관성과 효율성을 크게 향상시켰다. AutoGen 대비 불필요한 대화가 $\frac{1}{5}$ 이하로 줄어든다.

2. **발행-구독 메시지 패턴**: 에이전트 간 불필요한 통신을 제거하고, 각 에이전트가 정확히 필요한 정보만 소비하도록 하여 토큰 비용을 절감한다.

3. **구조화된 중간 산출물**: 비정형 텍스트 대신 JSON, Mermaid 다이어그램 등 구조화된 형식을 강제하여, 다음 단계 에이전트의 파싱 오류와 환각을 줄인다.

4. **코드 리뷰 루프**: QA 엔지니어의 테스트 결과가 실패하면, 엔지니어에게 피드백이 전달되어 수정-재테스트 루프가 작동한다.

## 벤치마크/성능

다음 그래프는 MBPP와 HumanEval 코드 생성 벤치마크에서 MetaGPT와 다른 접근법들의 Pass@1 비율을 비교한 것이다.

![MetaGPT vs 다른 접근법 MBPP/HumanEval Pass@1 비교](figures/fig_4.png)
*Figure 4: MBPP 및 HumanEval Pass@1 비교 — MetaGPT가 단일 에이전트와 ChatDev 대비 높은 코드 실행 성공률을 달성한다. (Source: arXiv 2308.00352)*

| 지표 | 단일 에이전트 | AutoGen | MetaGPT | 향상 |
|-----|-----------|---------|---------|------|
| 코드 실행률 | 50-60% | 65-70% | **82%** | +12%p |
| 테스트 통과율 | 낮음 | 중간 | **높음** | 유의미 |
| 토큰 효율성 | 1x | 2-3x | **1.5x** | 절감 |
| 프로젝트 완성도 | 낮음 | 중간 | **높음** | 유의미 |

다중 파일, 모듈 간 의존성이 있는 복잡한 소프트웨어 프로젝트에서 SOP 기반 접근의 강점이 두드러진다.

## 구현

**MVP 자동 생성**: "SNS 앱을 만들어줘"라는 한 줄의 지시로, PRD부터 실행 가능한 코드까지 전체 소프트웨어를 자동 생성할 수 있다.

**기술 문서 자동화**: 기존 코드베이스에 대한 API 문서, 아키텍처 설명서, 사용자 가이드를 역할별 에이전트가 분업하여 생성한다.

**프로토타이핑 가속화**: 아이디어 단계에서 빠르게 작동하는 프로토타입을 생성하여 피드백을 받고, 이를 바탕으로 실제 개발 방향을 결정하는 데 활용한다.

## 관련 모델

MetaGPT는 AutoGen의 멀티 에이전트 아이디어에서 영감을 받되, 구조화된 SOP와 발행-구독 패턴으로 차별화했다. 이후 CrewAI, ChatDev 등 역할 기반 멀티 에이전트 프레임워크에 직접적 영향을 미쳤다. GPT-4를 주 백엔드로 사용하며 별도 파인튜닝 없이 동작한다.

## 참고 자료

- Hong et al., "MetaGPT: Meta Programming for Multi-Agent Collaborative Framework", ICLR 2024, arXiv:2308.00352
- [MetaGPT GitHub Repository](https://github.com/geekan/MetaGPT)

## 관련 문서

- [[autogen|AutoGen]] — 영감
