# HyperAgents: 개방형 자기 개선을 위한 자기 참조적 에이전트

## 논문 개요

:::info
**Paper:** HyperAgents (arXiv:2603.19461, 2026.03)
**저자:** Jenny Zhang, Bingchen Zhao, Wannan Yang, Jakob Foerster, Jeff Clune, Minqi Jiang, Sam Devlin, Tatiana Shavrina
**소속:** UBC / Vector Institute, University of Edinburgh, NYU, FAIR at Meta, Meta Superintelligence Labs
**코드:** [github.com/facebookresearch/Hyperagents](https://github.com/facebookresearch/Hyperagents)
:::

Self-improving AI는 인간 엔지니어링 의존도를 줄이면서 스스로 학습 및 문제 해결 프로세스를 개선하는 것을 목표로 한다. 그러나 기존 접근법들은 **고정된 수작업 메타 레벨 메커니즘**에 의존하여, 개선 속도에 근본적 한계가 존재했다.

본 논문은 이 한계를 극복하기 위해 **hyperagent**를 제안한다 — task agent(대상 태스크 수행)와 meta agent(자신과 task agent를 수정)를 **단일 편집 가능 프로그램**으로 통합한 자기 참조적(self-referential) 에이전트이다. 4개 도메인(코딩, 논문 리뷰, 로보틱스, 수학)에서 기존 방법을 초과하는 성능을 달성했으며, 특히 meta-level 개선이 도메인 간 전이 가능하고 축적된다는 놀라운 결과를 보여준다.

---

## 배경: Darwin Gödel Machine의 한계

### Self-Improving AI의 흐름

Self-improving AI 연구는 크게 두 갈래로 발전해왔다:

1. **Foundation Model 기반 자기 개선**: Reflexion, Self-Refine 등에서 LLM이 자신의 출력을 반복적으로 개선하는 방식. 그러나 "개선하는 방법" 자체는 인간이 설계한 프롬프트에 고정되어 있다.
2. **Open-ended exploration 기반**: MAP-Elites, Quality-Diversity 알고리즘 등에서 다양한 해를 탐색하는 방식. 이를 LLM 에이전트에 적용한 것이 Darwin Gödel Machine(DGM)이다.

이 두 접근법의 공통적 한계는 **메타 레벨 메커니즘의 고정**이다. Reflexion의 자기 반성 프롬프트는 변하지 않고, DGM의 instruction-generation 절차도 수작업으로 설계된 채로 유지된다. 이는 마치 "더 좋은 도구를 만들 수 있지만, 도구를 만드는 공장 자체는 개선할 수 없는" 상황과 같다.

### DGM의 성공과 한계

DGM(Zhang et al., 2025b)은 coding agent를 자기 수정 가능한 프로그램으로 구현하여, 코딩 벤치마크에서 반복적인 자기 개선을 달성했다. 핵심 아이디어는:

- **자기 수정 가능한 에이전트**: 에이전트의 코드 자체를 에이전트가 편집
- **아카이브 기반 탐색**: Quality-Diversity 방식으로 다양한 변형체를 유지하여 탐색 다양성 확보
- **경험적 평가**: 각 변형체를 실제 벤치마크에서 평가하여 아카이브에 추가

하지만 DGM에는 **근본적 전제**가 있다: coding agent가 task agent이자 meta agent 역할을 동시에 수행한다는 것이다. 코딩 도메인에서는 "코드를 잘 짜는 능력"이 곧 "자기 코드를 잘 수정하는 능력"이므로 이 가정이 성립하지만, **논문 리뷰, 로보틱스, 수학** 등 다른 도메인에서는 이 정렬(alignment)이 깨진다. 논문 리뷰를 잘 하는 능력이 자기 코드를 수정하는 능력과 동일하지 않기 때문이다.

---

## 핵심 아이디어: Hyperagent

### Task Agent + Meta Agent의 통합

Hyperagent의 핵심 통찰은 간단하다: **메타 레벨 수정 절차 자체가 편집 가능해야 한다**.

기존 DGM에서 instruction-generation 메커니즘(어떻게 수정할지 결정하는 부분)은 고정되어 있었다. Hyperagent는 이를 프로그램의 일부로 포함시켜, 에이전트가 다음 두 가지를 모두 수행할 수 있게 한다:

1. **Task-level improvement**: 대상 태스크의 성능을 개선
2. **Meta-level improvement**: 개선 전략 자체를 개선 (metacognitive self-modification)

이 구분이 중요한 이유는, 기존 방법들이 task-level improvement만 가능했기 때문이다. "더 나은 해를 찾는 것"과 "더 나은 해를 찾는 *방법*을 찾는 것"의 차이다.

![DGM 변형들의 개념적 비교 — DGM에서 DGM-H까지의 진행](figures/fig_1.png)

*Figure 1: DGM 변형들의 개념적 비교. (1행) 원래 DGM은 코딩 도메인에서 task/meta alignment가 성립. (2행) 비코딩 도메인에서는 alignment가 깨져 실패. (3행) DGM-custom은 수작업 도메인 적응으로 부분 해결. (4행) DGM-H는 metacognitive self-modification으로 어떤 도메인에서든 자기 개선 가능. (Zhang et al., 2026)*

### DGM-Hyperagents (DGM-H) 알고리즘

DGM-H의 작동 방식:

1. **초기화**: Frozen Foundation Model(Claude 3.5 Sonnet) 기반 hyperagent로 시작. Bash tool + file editing tool을 보유하며, Python으로 구현된 Turing-complete 프로그램
2. **아카이브 구축**: Hyperagent 변형체들을 지속적으로 축적
3. **두 단계를 반복**:
   - **Metacognitive self-modification phase**: 부모 hyperagent를 **성능 비례 확률**로 선택. 부모 선택 시 **자식 수에 반비례하는 가중치**를 부여하여 탐색 다양성 유지 (모든 변형체가 고르게 부모가 될 기회를 가짐)
   - **Evaluation phase**: 생성된 hyperagent를 벤치마크에서 경험적으로 평가하여 아카이브에 추가

기존 DGM과의 결정적 차이는, DGM에서 고정되어 있던 "self-modification instruction을 생성하는 메커니즘"이 DGM-H에서는 **프로그램의 편집 가능한 일부**라는 점이다. 이로 인해 에이전트는 task 수행 코드뿐 아니라, **자기 개선을 위한 instruction 생성 로직 자체**를 수정할 수 있다.

### Hyperagent가 발견한 Meta-Level 전략들

실험에서 hyperagent들이 자율적으로 발견한 meta-level 개선의 구체적 예시들:

- **Persistent memory 시스템**: 이전 실행에서의 성공/실패 패턴을 파일에 기록하고 다음 수정 시 참조
- **Performance tracking**: 각 수정의 영향을 정량적으로 추적하여 개선 방향을 데이터 기반으로 결정
- **적응적 탐색 전략**: 초기에는 대규모 구조 변경을 시도하고, 성능이 안정화되면 세부 튜닝으로 전환
- **도메인별 도구 활용 최적화**: Paper review에서는 구조화된 출력 포맷을, 로보틱스에서는 보상 함수 시뮬레이션을 자동 도입

이러한 전략들은 인간 연구자가 수작업으로 설계하지 않고, hyperagent가 스스로 발견한 것이라는 점에서 의미가 크다.

---

## 실험 결과

### 4개 도메인에서의 검증

저자들은 코딩 외 도메인에서의 일반화를 입증하기 위해 4개의 다양한 도메인에서 실험을 수행했다. 각 실험에서 DGM-H는 50회 반복(iteration)을 수행하며, 각 반복에서 하나의 새로운 hyperagent 변형체를 생성하고 평가한다.

#### 1. Coding (Polyglot)

| 지표 | 초기 에이전트 | DGM-H |
|------|------------|-------|
| Training subset | 0.140 | **0.340** (CI: 0.300-0.380) |
| Full benchmark | 0.084 | **0.267** (CI: 0.231-0.280) |

코딩 도메인에서 DGM-H는 원래 DGM(코딩 특화)과 비슷한 수준의 개선을 달성했다. 이는 일반화된 접근법이 특화된 접근법의 성능을 유지함을 보여준다.

#### 2. Paper Review (핵심 결과)

| 방법 | Test set 점수 |
|------|-------------|
| Initial agent | 0.000 |
| Original DGM | 0.000 (코딩 특화라 실패) |
| DGM-custom (수작업 도메인 적응) | 0.590 |
| AI-Scientist-v2 (오픈소스 baseline) | 0.630 |
| **DGM-H** | **0.710** (CI: 0.590-0.750) |

논문 리뷰 도메인에서 DGM-H는 수작업으로 도메인 적응한 DGM-custom과 오픈소스 AI-Scientist-v2를 모두 초과했다. 원래 DGM은 코딩 특화 메커니즘으로 인해 논문 리뷰에서 완전히 실패(0.0)했다는 점에서 hyperagent의 일반화 능력이 명확히 드러난다.

#### 3. Robotics Reward Design

| 방법 | Test set 점수 |
|------|-------------|
| Initial agent | 0.060 |
| Default reward function | 0.348 |
| DGM-custom | 0.348 |
| **DGM-H** | **0.372** (CI: 0.355-0.436) |

로보틱스에서의 개선폭은 상대적으로 작지만, DGM-custom이 기본 보상함수를 전혀 개선하지 못한 반면(0.348 = default와 동일) DGM-H는 이를 초과했다는 점이 중요하다.

#### 4. Olympiad-level Math Grading (IMO-GradingBench)

| 방법 | Test set Accuracy |
|------|------------------|
| ProofAutoGrader baseline | 0.670 |
| **DGM-H + transfer + ProofAutoGrader 초기화** | **0.700** |

IMO-GradingBench에서 기존 전문 시스템(ProofAutoGrader)의 성능을 초과한 것은, hyperagent가 도메인 전문 도구를 활용하면서도 그 위에 추가적 개선을 달성할 수 있음을 보여준다.

![DGM-H의 실험 결과 — 도메인별 성능 향상 곡선](figures/fig_2.png)

*Figure 2: Metacognitive self-modification과 open-ended exploration이 지속적 성능 향상을 가능하게 함. (좌) Training tasks에서의 반복별 성능 개선. (우) Test tasks에서의 일반화 성능. Paper Review와 Robotics 두 도메인 모두에서 DGM-H가 baseline을 지속적으로 초과. (Zhang et al., 2026)*

### Ablation Study: 무엇이 핵심인가?

| 설정 | Paper Review | Robotics |
|------|-------------|----------|
| DGM-H (full) | 0.710 | 0.372 |
| w/o self-improve (고정 meta agent) | 0.000 | 0.213 |
| w/o open-ended exploration (아카이브 없음) | 0.000 | 0.116 |

두 가지 핵심 요소가 모두 필수적이다:

1. **Metacognitive self-modification**: 고정된 meta agent로는 코딩 외 도메인에서 실패. Meta agent가 도메인에 맞게 스스로 적응해야만 task agent를 효과적으로 개선할 수 있다.
2. **Open-ended exploration**: 아카이브 없이 순차적 교체만 하면 다양성 부족으로 실패. 다양한 변형체를 유지해야 좋은 해를 발견할 확률이 높아진다.

특히 Paper Review에서 두 요소 중 하나라도 제거하면 성능이 0.0으로 완전히 붕괴한다는 점은, 이 두 메커니즘이 단순히 "있으면 좋은" 것이 아니라 **비코딩 도메인에서 필수 불가결**한 요소임을 보여준다.

---

## Transfer와 Compounding

### 도메인 간 전이

논문의 가장 인상적인 결과 중 하나는 **meta-level 개선이 도메인 간 전이 가능하다**는 발견이다.

Paper Review와 Robotics에서 학습된 meta agent를 Math Grading에 전이시킨 결과:

- **DGM-custom transfer**: imp@50 = 0.0 (전이 실패)
- **DGM-H transfer**: imp@50 = **0.630** (성공적 전이)

DGM-custom의 수작업 도메인 적응은 특정 도메인에 종속적이어서 전이가 불가능한 반면, DGM-H가 학습한 meta-level 개선(persistent memory 관리, performance tracking, 적응적 탐색 전략 등)은 도메인에 무관한 **범용적 자기 개선 전략**이다. 이는 hyperagent의 meta-level 학습이 단순한 도메인 특화 최적화가 아니라, 보다 근본적인 "자기 개선 능력"의 향상임을 시사한다.

### 축적적 자기 개선 (Compounding)

Transfer된 hyperagent에서 다시 DGM-H를 실행하면, 이전 학습의 self-improvement가 축적된다:

- Transfer hyperagent 시작: test-set **0.640** (CI: 0.550-0.720)
- 초기 에이전트 시작: 0.610 (CI: 0.510-0.680)

성능 향상뿐 아니라 **신뢰 구간이 더 좁아진다**는 점도 주목할 만하다 — 이전 학습이 탐색의 안정성을 높인다는 증거이다. 이는 self-improving AI의 핵심 가설인 "개선이 축적되어 가속화될 수 있다"를 경험적으로 지지하는 결과이다.

![DGM-H의 축적적 자기 개선 — 도메인 간 전이 후 추가 개선](figures/fig_3.png)

*Figure 3: 자기 개선이 도메인과 실행(run) 간에 축적됨. (좌) Training tasks 성능. (우) Test tasks 성능. Transfer hyperagent에서 시작하면 초기 에이전트에서 시작하는 것보다 빠르게 높은 성능에 도달하며, 이전 학습의 자기 개선이 새로운 도메인에서 보존되고 축적됨. (Zhang et al., 2026)*

---

## 한계와 논의

### 1. 계산 비용

각 hyperagent 변형체를 벤치마크에서 평가해야 하므로, 50회 반복 실행 시 상당한 GPU/API 비용이 발생한다. 논문에서는 Claude 3.5 Sonnet을 Foundation Model로 사용하며, 각 도메인에서 수백 회의 API 호출이 필요하다. 이는 현재 시점에서 소규모 연구팀이 쉽게 재현하기 어려운 비용 구조다.

### 2. Safety 우려

자기 수정 가능한 AI 시스템은 통제 가능성과 예측 가능성 면에서 본질적 위험을 내포한다. 저자들은 이를 인지하고 다음과 같은 안전장치를 두고 있다:
- 제한된 tool set (Bash + file editing만 허용)
- 샌드박스 환경에서 실행
- 모든 수정 사항에 대한 감사 추적(audit trail)
- 인간 감독(human oversight) 유지

그러나 시스템이 **자기 개선 속도를 자기 개선할 수 있다**는 점에서, 장기적으로는 인간의 감독 속도를 초과할 가능성에 대한 우려가 있다. 저자들도 Section 6에서 이 문제를 명시적으로 논의하며, "안전성을 절대적 보장이나 양적 지표로만 접근하기보다, 인간 감독과의 균형 속에서 점진적으로 신뢰를 구축해야 한다"고 주장한다.

### 3. 평가의 한계

현재 벤치마크 기반 평가는 과적합(overfitting)의 위험이 있으며, 실제 open-ended 환경에서의 검증이 추가로 필요하다. 또한 50회 반복이라는 제한된 예산 내에서의 결과이므로, 더 많은 반복에서의 스케일링 특성은 아직 미검증이다.

### 4. Frozen FM 의존성

기저 Foundation Model이 고정되어 있어, FM 자체의 한계를 넘어서는 개선에는 제약이 있다. Hyperagent는 FM의 능력을 더 효과적으로 활용하는 방법을 학습하지만, FM이 근본적으로 할 수 없는 작업을 가능하게 만들지는 못한다. 향후 FM 자체의 파인튜닝과 결합하는 연구가 흥미로운 방향이 될 것이다.

---

## 결론

HyperAgents는 self-improving AI의 핵심 병목인 **고정된 메타 메커니즘**을 해결하기 위해, task agent와 meta agent를 단일 편집 가능 프로그램으로 통합하는 접근법을 제시한다. "더 나은 해를 찾는 것"이 아니라 **"더 나은 해를 찾는 방법을 찾는 것"**이 가능한 시스템이다.

4개 도메인에서의 실험은 이 접근법의 일반성을 입증하며, 특히 세 가지 결과가 핵심적이다:

1. **범용성**: 코딩 특화 DGM이 실패하는 논문 리뷰, 로보틱스에서 DGM-H가 성공
2. **전이 가능성**: meta-level 개선이 훈련하지 않은 새로운 도메인(수학)으로 전이
3. **축적성**: 이전 학습의 자기 개선이 보존되고 새로운 학습 위에 축적

이는 open-ended self-improving AI의 실현 가능성을 한 단계 끌어올린 결과이며, 동시에 계산 비용과 안전성 문제라는 중요한 연구 과제를 남긴다.

## Paper Summary

| 항목 | 내용 |
|------|------|
| 제목 | HyperAgents |
| 저자 | Jenny Zhang, Bingchen Zhao, Wannan Yang, Jakob Foerster, Jeff Clune, Minqi Jiang, Sam Devlin, Tatiana Shavrina |
| 소속 | UBC, Vector Institute, Edinburgh, NYU, FAIR at Meta |
| 연도 | 2026 |
| 학회 | arXiv preprint |
| 원문 | [arXiv:2603.19461](https://arxiv.org/abs/2603.19461) |
| 코드 | [github.com/facebookresearch/Hyperagents](https://github.com/facebookresearch/Hyperagents) |
| 핵심 키워드 | Self-Improving AI, Metacognitive Self-Modification, Open-Ended AI, LLM Agent |
