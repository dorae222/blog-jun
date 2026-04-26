<!-- infographic-hero -->
![HyperAgents: Self-Referential Agents for Open-Ended Self-Improvement 핵심 요약](figures/infographic.svg)

*Figure: HyperAgents: Self-Referential Agents for Open-Ended Self-Improvement 한 장 요약 인포그래픽*

# HyperAgents: 개방형 자기 개선을 위한 자기 참조적 에이전트

## 개요

:::info
**Paper:** HyperAgents: Self-Referential Agents for Open-Ended Self-Improvement (arXiv:2603.19461, 2026.03)
**저자:** Jenny Zhang, Bingchen Zhao, Wannan Yang, Jakob Foerster, Jeff Clune, Minqi Jiang, Sam Devlin, Tatiana Shavrina
**소속:** UBC / Vector Institute, University of Edinburgh, NYU, FAIR at Meta, Meta Superintelligence Labs
**코드:** [github.com/facebookresearch/Hyperagents](https://github.com/facebookresearch/Hyperagents)
:::

Self-improving AI는 인간 엔지니어링 의존도를 줄이면서 스스로 학습 및 문제 해결 프로세스를 개선하는 것을 목표로 한다. [[reflexion]], Self-Refine 등 기존 접근법들은 LLM이 자신의 출력을 반복적으로 개선하는 데 성공했지만, **"개선하는 방법" 자체는 인간이 설계한 고정된 메타 메커니즘에 의존**한다는 근본적 한계가 있었다. 이는 "더 좋은 도구를 만들 수 있지만, 도구를 만드는 공장 자체는 개선할 수 없는" 상황과 같다.

본 논문은 이 한계를 극복하기 위해 **hyperagent**를 제안한다. Hyperagent는 task agent(대상 태스크 수행)와 meta agent(자신과 task agent를 수정)를 **단일 편집 가능 프로그램**으로 통합한 자기 참조적(self-referential) 에이전트이다. 핵심 기여는 "개선하는 방법 자체를 개선하는" metacognitive self-modification 능력을 에이전트에 부여한 것이다. 4개 도메인(코딩, 논문 리뷰, 로보틱스, 수학)에서 기존 방법을 초과하는 성능을 달성했으며, 특히 meta-level 개선이 도메인 간 전이 가능하고 축적된다는 결과를 보여준다.

---

## 배경: Self-Improving AI의 두 갈래와 DGM

### Self-Improving AI 연구의 흐름

Self-improving AI 연구는 크게 두 갈래로 발전해왔다.

**Foundation Model 기반 자기 개선**: [[reflexion]], Self-Refine 등에서 LLM이 자신의 출력을 반복적으로 개선하는 방식이다. [[reflexion]]은 에이전트가 실패 경험으로부터 자연어 피드백을 생성하고 이를 메모리에 저장하여 다음 시도에 활용하는 구조를 제안했다. 그러나 이 접근법에서 "어떻게 반성할 것인가"를 결정하는 메커니즘 자체는 인간이 설계한 프롬프트에 고정되어 있다. 에이전트는 task-level에서는 개선되지만, 개선 전략 자체를 개선할 수는 없다.

**Open-ended exploration 기반**: MAP-Elites, Quality-Diversity 알고리즘 등에서 다양한 해를 탐색하는 방식이다. 이를 LLM 에이전트에 적용한 것이 Darwin Godel Machine(DGM)이다. DGM은 에이전트의 코드 자체를 에이전트가 편집할 수 있게 하여, Quality-Diversity 방식으로 다양한 변형체를 유지하면서 반복적 자기 개선을 달성했다.

| 접근법 | 핵심 메커니즘 | Task-level 개선 | Meta-level 개선 | 도메인 범용성 |
|--------|------------|:---:|:---:|:---:|
| [[reflexion]] / Self-Refine | 고정 프롬프트 기반 자기 반성 | O | X | 제한적 |
| [[react]] / [[swe-agent]] | 고정 TAO 루프 / 도구 사용 | O | X | 제한적 |
| DGM (Zhang et al., 2025b) | 자기 수정 + QD 아카이브 | O | X | 코딩 특화 |
| **DGM-H (본 논문)** | **Metacognitive self-modification** | **O** | **O** | **범용** |

### DGM의 성공과 근본적 한계

DGM(Zhang et al., 2025b)은 coding agent를 자기 수정 가능한 프로그램으로 구현하여, 코딩 벤치마크에서 반복적인 자기 개선을 달성한 선행 연구이다. 핵심 설계 요소는 다음과 같다:

- **자기 수정 가능한 에이전트**: 에이전트의 Python 코드 자체를 에이전트가 편집할 수 있음
- **아카이브 기반 탐색**: Quality-Diversity 방식으로 다양한 변형체를 유지하여 탐색 다양성 확보
- **경험적 평가**: 각 변형체를 실제 벤치마크에서 평가하여 아카이브에 추가할지 결정

그러나 DGM에는 **근본적 전제**가 존재한다. 코딩 도메인에서 coding agent가 task agent이자 meta agent 역할을 동시에 수행한다는 것이다. "코드를 잘 짜는 능력"이 곧 "자기 코드를 잘 수정하는 능력"이므로 이 가정이 성립한다. 하지만 이 task/meta alignment는 **코딩 도메인에서만 우연히 성립하는 특수한 조건**이다.

논문 리뷰를 생각해보자. 논문을 잘 리뷰하는 능력과 자기 코드를 수정하는 능력은 전혀 다른 역량이다. 로보틱스 보상 함수 설계도 마찬가지이다. DGM의 instruction-generation 메커니즘은 코딩 태스크에 특화되어 있어, 비코딩 도메인에서는 "어떻게 수정할지"에 대한 효과적인 지시를 생성하지 못한다. 결과적으로 DGM을 비코딩 도메인에 직접 적용하면 성능이 0.0으로 완전히 실패한다.

---

## 핵심 아이디어: Metacognitive Self-Modification

### Task-Level vs Meta-Level 개선의 구분

Hyperagent의 핵심 통찰은 간단하면서도 심오하다: **메타 레벨 수정 절차 자체가 편집 가능해야 한다**.

기존 self-improving 시스템에서 "개선"이라 함은 task-level improvement만을 의미했다. 즉, 에이전트가 더 나은 답을 내는 것이다. 그러나 hyperagent는 두 가지 수준의 개선을 동시에 수행한다:

| 수준 | 정의 | 예시 | 기존 방법 | DGM-H |
|------|------|------|---------|-------|
| **Task-level** | 대상 태스크의 성능을 개선 | 더 정확한 논문 리뷰 작성 | O | O |
| **Meta-level** | 개선 전략 자체를 개선 | 리뷰 개선 방법론을 발전시킴 | X | O |

이 구분이 중요한 이유는, "더 나은 해를 찾는 것"과 "더 나은 해를 찾는 *방법*을 찾는 것" 사이에 질적 차이가 있기 때문이다. 후자가 가능해지면 개선의 속도 자체가 가속화될 수 있다. 이는 인간 연구자가 연구 방법론 자체를 개선하면서 연구 생산성이 높아지는 것과 유사한 구조이다.

![DGM 변형들의 개념적 비교 - DGM에서 DGM-H까지의 진행](figures/fig_1.png)

*Figure 1: DGM 변형들의 개념적 비교. (1행) 원래 DGM은 코딩 도메인에서 task/meta alignment가 성립하여 자기 개선이 가능. (2행) 비코딩 도메인에서는 alignment가 깨져 개선 실패. (3행) DGM-custom은 수작업 도메인 적응으로 부분적 해결. (4행) DGM-H는 metacognitive self-modification으로 어떤 도메인에서든 자기 개선이 가능. (Zhang et al., 2026)*

### DGM vs DGM-H: 결정적 차이

DGM과 DGM-H의 아키텍처 차이를 정확히 이해하는 것이 본 논문의 핵심이다.

DGM에서 self-modification 과정은 다음과 같다:
1. 아카이브에서 부모 에이전트를 선택
2. **고정된(handcrafted) instruction-generation 메커니즘**이 수정 지시를 생성
3. Frozen Foundation Model(Claude 3.5 Sonnet)이 지시에 따라 에이전트 코드를 수정
4. 수정된 에이전트를 벤치마크에서 평가

여기서 2단계의 instruction-generation 메커니즘은 인간이 수작업으로 설계한 것이며, 실행 중에 변하지 않는다. DGM-custom은 이 메커니즘을 각 도메인에 맞게 수작업으로 재설계한 변형이다.

DGM-H의 결정적 혁신은, 이 instruction-generation 메커니즘을 **프로그램의 편집 가능한 일부**로 만든 것이다:
1. 아카이브에서 부모 hyperagent를 선택
2. **편집 가능한 metacognitive self-modification 모듈**이 수정 지시를 생성
3. Frozen FM이 지시에 따라 hyperagent 전체(task 코드 + meta 모듈)를 수정
4. 수정된 hyperagent를 벤치마크에서 평가

즉, 에이전트는 task 수행 코드뿐 아니라 **자기 개선을 위한 instruction 생성 로직 자체**를 수정할 수 있다. 이로 인해 에이전트가 도메인에 맞는 최적의 자기 개선 전략을 스스로 발견할 수 있다.

---

## 방법론: DGM-H 알고리즘 상세

### 알고리즘 구조

DGM-H 알고리즘의 전체 작동 방식을 단계별로 분석한다.

**초기화 단계**: Frozen Foundation Model(Claude 3.5 Sonnet) 기반 hyperagent 프로그램으로 시작한다. 이 프로그램은 Bash tool과 file editing tool을 보유하며, Python으로 구현된 Turing-complete 프로그램이다. 초기 hyperagent는 task 수행 코드와 metacognitive self-modification 모듈을 모두 포함한다.

**반복 루프** (총 50회 반복):

| 단계 | 설명 | 핵심 메커니즘 |
|------|------|------------|
| 부모 선택 | 아카이브에서 부모 hyperagent 선택 | 성능 비례 확률 + 자식 수 반비례 가중치 |
| 자기 수정 | 부모의 metacognitive 모듈이 수정 지시 생성 | 편집 가능한 instruction-generation |
| 코드 수정 | Frozen FM이 지시에 따라 hyperagent 전체 수정 | Task 코드 + Meta 모듈 동시 수정 가능 |
| 평가 | 새 hyperagent를 벤치마크에서 경험적 평가 | Training subset에서 평가 |
| 아카이브 | 평가 결과에 따라 아카이브에 추가 | Quality-Diversity 기준 |

**부모 선택 전략**이 특히 중요하다. 단순히 성능 최고의 에이전트만 부모로 선택하면 탐색 다양성이 급격히 줄어든다. DGM-H는 두 가지 가중치를 결합한다:

- **성능 비례 가중치**: 높은 성능의 에이전트가 더 자주 부모로 선택됨 (exploitation)
- **자식 수 반비례 가중치**: 이미 많은 자식을 생성한 에이전트는 선택 확률이 낮아짐 (exploration)

이 조합으로 모든 변형체가 고르게 부모가 될 기회를 가지면서도, 좋은 성능의 에이전트에 약간 더 많은 기회를 부여한다.

### Hyperagent가 자율적으로 발견한 Meta-Level 전략

실험에서 hyperagent들이 인간의 개입 없이 자율적으로 발견한 meta-level 개선 전략들이 있다. 이 전략들은 인간 연구자가 설계하지 않았음에도 불구하고, 소프트웨어 공학의 모범 사례와 유사한 패턴을 보인다.

**Persistent Memory 시스템**: 이전 실행에서의 성공/실패 패턴을 파일에 기록하고 다음 수정 시 참조하는 메커니즘을 자율적으로 개발했다. 이는 단순한 in-context 학습을 넘어, 실행 간(across-run) 지식 축적을 가능하게 한다. [[reflexion]]의 자기 반성 메모리가 단일 실행 내에서만 작동하는 것과 대조적으로, hyperagent의 persistent memory는 여러 세대에 걸쳐 축적된다.

**Performance Tracking 시스템**: 각 수정이 성능에 미치는 영향을 정량적으로 추적하는 로깅 체계를 구축했다. "어떤 수정이 성능을 올렸고, 어떤 수정이 내렸는지"를 데이터 기반으로 분석하여 다음 수정의 방향을 결정한다. 이는 인간 연구자의 실험 노트와 유사한 기능이다.

**적응적 탐색 전략**: 자기 개선 과정의 초기에는 에이전트 구조의 대규모 변경을 시도하고, 성능이 안정화되면 세부 파라미터 튜닝으로 전환하는 전략을 학습했다. 이는 simulated annealing의 cooling schedule과 개념적으로 유사하며, 탐색(exploration)과 활용(exploitation)의 균형을 동적으로 조절하는 것이다.

**도메인별 도구 활용 최적화**: Paper review에서는 구조화된 출력 포맷과 체크리스트를, 로보틱스에서는 보상 함수 시뮬레이션과 반복 테스트를 자동으로 도입했다. 도메인의 특성에 맞는 워크플로우를 에이전트 스스로 설계한 것이다.

:::warning
Hyperagent가 자율적으로 발견한 이 전략들은, 인간 소프트웨어 엔지니어가 일반적으로 사용하는 개발 패턴(version control, logging, A/B testing, progressive refinement)과 놀라울 정도로 유사하다. 이는 이러한 패턴들이 "좋은 자기 개선 전략"의 수렴적 해(convergent solution)일 가능성을 시사한다.
:::

---

## 실험 결과: 4개 도메인에서의 검증

### 실험 설계

저자들은 DGM-H의 일반화 능력을 검증하기 위해 4개의 도메인을 선택했다. 각 도메인은 task/meta alignment 정도가 다르며, 이를 통해 hyperagent의 범용성을 체계적으로 검증한다.

| 도메인 | 벤치마크 | Task/Meta Alignment | 핵심 평가 지표 |
|--------|---------|:---:|------------|
| Coding | Polyglot | 높음 (코드 수정 = 자기 수정) | Pass rate |
| Paper Review | AI-Scientist benchmark | 낮음 (리뷰 능력 != 코드 수정) | Quality score |
| Robotics | Reward design | 낮음 (보상 설계 != 코드 수정) | Task completion |
| Math Grading | IMO-GradingBench | 낮음 (채점 능력 != 코드 수정) | Accuracy |

모든 실험에서 DGM-H는 50회 반복(iteration)을 수행하며, 각 반복에서 하나의 새로운 hyperagent 변형체를 생성하고 평가한다. Frozen Foundation Model로는 Claude 3.5 Sonnet을 사용한다.

### 도메인별 결과 분석

#### 1. Coding (Polyglot)

| 지표 | 초기 에이전트 | DGM (코딩 특화) | DGM-H |
|------|------------|---------------|-------|
| Training subset | 0.140 | ~0.340 | **0.340** (CI: 0.300-0.380) |
| Full benchmark | 0.084 | ~0.267 | **0.267** (CI: 0.231-0.280) |

코딩 도메인에서 DGM-H는 원래 DGM(코딩에 특화된 수작업 메커니즘)과 **동등한 수준**의 개선을 달성했다. 이는 중요한 결과이다. 범용적 접근법(DGM-H)이 특화된 접근법(DGM)의 성능을 유지한다는 것은, 범용화에 따른 성능 저하가 없음을 의미한다. 코딩 도메인에서 task/meta alignment가 이미 존재하므로, metacognitive self-modification이 추가적 이점을 제공하지는 않지만 손해도 주지 않는다.

#### 2. Paper Review (핵심 결과)

| 방법 | 설명 | Test set 점수 |
|------|------|:---:|
| Initial agent | 초기 에이전트 | 0.000 |
| Original DGM | 코딩 특화 DGM 직접 적용 | 0.000 |
| DGM-custom | 수작업으로 도메인 적응 | 0.590 |
| AI-Scientist-v2 | 오픈소스 baseline | 0.630 |
| **DGM-H** | **Metacognitive self-modification** | **0.710** (CI: 0.590-0.750) |

논문 리뷰는 DGM-H의 핵심 성과를 가장 잘 보여주는 도메인이다. 원래 DGM은 코딩 특화 instruction-generation 메커니즘으로 인해 논문 리뷰에서 **완전히 실패(0.0)**했다. 코딩 에이전트가 "더 나은 코드를 작성하라"는 지시는 생성할 수 있지만, "더 나은 논문 리뷰를 작성하라"는 효과적인 지시를 생성할 수 없었기 때문이다.

DGM-custom은 인간이 수작업으로 논문 리뷰에 맞게 instruction-generation을 재설계하여 0.590을 달성했다. 그러나 DGM-H는 이 수작업 적응 없이도, **metacognitive self-modification을 통해 자동으로 논문 리뷰에 적합한 개선 전략을 발견**하여 0.710이라는 최고 성능에 도달했다. 이는 수작업 도메인 적응보다 자동 메타 학습이 더 효과적일 수 있음을 시사한다.

#### 3. Robotics Reward Design

| 방법 | 설명 | Test set 점수 |
|------|------|:---:|
| Initial agent | 초기 에이전트 | 0.060 |
| Default reward function | 기본 보상 함수 | 0.348 |
| DGM-custom | 수작업 도메인 적응 | 0.348 |
| **DGM-H** | **Metacognitive self-modification** | **0.372** (CI: 0.355-0.436) |

로보틱스에서의 개선폭(0.348 -> 0.372)은 상대적으로 작다. 그러나 핵심적으로 주목해야 할 점은, DGM-custom이 **기본 보상함수를 전혀 개선하지 못한 반면**(0.348 = default와 동일), DGM-H는 이를 초과했다는 것이다. 로보틱스 보상 설계는 코딩이나 논문 리뷰보다 탐색 공간이 까다로운 도메인이며, 수작업 도메인 적응조차 효과가 없었던 곳에서 metacognitive self-modification이 유의미한 개선을 달성한 것은 이 접근법의 범용성을 보여주는 강력한 증거이다.

#### 4. Olympiad-level Math Grading (IMO-GradingBench)

| 방법 | 설명 | Test set Accuracy |
|------|------|:---:|
| ProofAutoGrader baseline | 기존 전문 시스템 | 0.670 |
| DGM-H (초기 에이전트 시작) | 직접 학습 | 0.610 (CI: 0.510-0.680) |
| **DGM-H + transfer + ProofAutoGrader 초기화** | **전이 학습 적용** | **0.700** |

IMO-GradingBench는 올림피아드 수준의 수학 증명을 채점하는 극히 전문화된 태스크이다. DGM-H가 기존 전문 시스템(ProofAutoGrader)의 0.670을 초과하여 0.700을 달성한 것은, hyperagent가 **도메인 전문 도구를 활용하면서도 그 위에 추가적 개선을 쌓을 수 있음**을 보여준다. 이 결과에서 transfer learning의 기여가 특히 중요한데, 이에 대해서는 후속 섹션에서 상세히 다룬다.

![DGM-H의 실험 결과 - 도메인별 성능 향상 곡선](figures/fig_2.png)

*Figure 2: Metacognitive self-modification과 open-ended exploration이 지속적 성능 향상을 가능하게 함. (좌) Training tasks에서의 반복별 성능 개선. (우) Test tasks에서의 일반화 성능. Paper Review와 Robotics 두 도메인 모두에서 DGM-H가 baseline을 지속적으로 초과하며, DGM-custom 대비 더 높은 성능에 수렴. (Zhang et al., 2026)*

### Ablation Study: 핵심 구성 요소 분석

DGM-H의 두 가지 핵심 구성 요소의 필요성을 검증하는 ablation study 결과이다.

| 설정 | Paper Review | Robotics | 분석 |
|------|:---:|:---:|------|
| **DGM-H (full)** | **0.710** | **0.372** | 두 요소 모두 포함 |
| w/o self-improve (고정 meta agent) | 0.000 | 0.213 | Meta 고정 시 비코딩 도메인 실패 |
| w/o open-ended exploration (아카이브 없음) | 0.000 | 0.116 | 다양성 부족으로 탐색 실패 |

두 가지 핵심 요소가 모두 **필수 불가결**하다:

**Metacognitive self-modification의 필요성**: 고정된 meta agent로는 코딩 외 도메인에서 실패한다. Paper Review에서 이 요소를 제거하면 성능이 0.710에서 0.000으로 완전히 붕괴한다. Meta agent가 도메인에 맞게 스스로 적응해야만 task agent를 효과적으로 개선할 수 있다. 이는 "만능 개선 전략"은 존재하지 않으며, 각 도메인에 맞는 개선 전략이 필요하다는 것을 의미한다.

**Open-ended exploration의 필요성**: 아카이브 없이 순차적 교체(greedy replacement)만 하면 다양성 부족으로 실패한다. 하나의 "최선의 에이전트"만 유지하면 조기 수렴(premature convergence)에 빠지기 쉽다. 다양한 변형체를 아카이브에 유지해야 다양한 방향에서의 탐색이 가능하고, 예기치 않은 돌파구를 발견할 확률이 높아진다.

:::tip
Paper Review에서 두 요소 중 하나라도 제거하면 성능이 0.0으로 완전히 붕괴한다는 점은 핵심적인 발견이다. 이는 metacognitive self-modification과 open-ended exploration이 단순히 "있으면 좋은" 보조 요소가 아니라, **비코딩 도메인에서의 자기 개선을 가능하게 하는 필수 조건**임을 보여준다.
:::

---

## Transfer Learning과 Compounding Effects

### 도메인 간 Meta-Level 전이

본 논문의 가장 인상적인 결과 중 하나는 **meta-level 개선이 도메인 간 전이 가능하다**는 발견이다. Paper Review와 Robotics에서 학습된 meta agent를 Math Grading에 전이시킨 결과를 살펴본다.

| 전이 방법 | 전이 소스 | Math Grading imp@50 | 분석 |
|----------|---------|:---:|------|
| DGM-custom transfer | Paper Review + Robotics 수작업 적응 | 0.000 | 도메인 특화 전략은 전이 불가 |
| **DGM-H transfer** | **Paper Review + Robotics 자동 학습** | **0.630** | **범용 전략이므로 전이 가능** |

이 결과의 의미가 심원하다. DGM-custom의 수작업 도메인 적응은 **도메인에 종속적**이다. 논문 리뷰를 위해 설계한 instruction-generation 메커니즘은 로보틱스에 적용할 수 없고, 로보틱스용은 수학에 적용할 수 없다. 전이 시 성능이 0.0이라는 것이 이를 명확히 보여준다.

반면 DGM-H가 학습한 meta-level 전략들은 **도메인에 무관한 범용적 자기 개선 전략**이다:
- Persistent memory 시스템: 어떤 도메인에서든 이전 경험의 축적이 유용함
- Performance tracking: 어떤 도메인에서든 정량적 피드백이 유용함
- 적응적 탐색 전략: 어떤 도메인에서든 탐색-활용 균형이 필요함

이는 hyperagent의 meta-level 학습이 단순한 도메인 특화 최적화가 아니라, 보다 근본적인 **"자기 개선 능력" 자체의 향상**임을 시사한다. [[62_camel]]이나 [[multi-agent-comparison]]에서 다루는 멀티 에이전트 협업이 특정 태스크 구성에 최적화되는 것과 달리, hyperagent의 meta-level 학습은 태스크 유형을 초월하는 범용적 개선 능력을 구축한다.

### 축적적 자기 개선 (Compounding Self-Improvement)

Transfer된 hyperagent에서 다시 DGM-H를 실행하면, 이전 학습의 self-improvement가 축적(compound)된다.

| 시작점 | Math Grading test-set (최종) | 95% CI | 분석 |
|--------|:---:|:---:|------|
| 초기 에이전트에서 시작 | 0.610 | 0.510-0.680 | 처음부터 학습 |
| **Transfer hyperagent에서 시작** | **0.640** | **0.550-0.720** | 이전 학습 활용 |

주목할 점이 세 가지 있다:

**성능 향상**: Transfer hyperagent에서 시작하면 최종 성능이 더 높다 (0.640 > 0.610). 이전 도메인에서 학습한 meta-level 전략이 새로운 도메인에서의 학습을 가속화한다.

**빠른 수렴**: Transfer 시작점의 초기 성능이 이미 높아, 같은 50회 반복 내에서 더 높은 수준에 도달한다.

**신뢰 구간 안정성**: Transfer hyperagent의 신뢰 구간이 더 좁다는 점도 중요하다. 이전 학습이 탐색의 **안정성**을 높인다는 증거이다. 이는 단순한 초기화 이점이 아니라, meta-level 전략의 질적 개선이 탐색 과정 자체를 더 효율적으로 만드는 것이다.

![DGM-H의 축적적 자기 개선 - 도메인 간 전이 후 추가 개선](figures/fig_3.png)

*Figure 3: 자기 개선이 도메인과 실행(run) 간에 축적됨. (좌) Training tasks 성능. (우) Test tasks 성능. Transfer hyperagent에서 시작하면 초기 에이전트에서 시작하는 것보다 빠르게 높은 성능에 도달하며, ProofAutoGrader baseline을 초과. 이전 학습의 자기 개선이 새로운 도메인에서 보존되고 축적됨. (Zhang et al., 2026)*

이 결과는 self-improving AI의 핵심 가설인 **"개선이 축적되어 가속화될 수 있다"**를 경험적으로 지지하는 최초의 결과 중 하나이다. 다만, 현재 실험은 2개 도메인에서 1개 도메인으로의 1회 전이에 국한되어 있으므로, 더 많은 도메인과 반복 전이에서의 축적 효과는 향후 검증이 필요하다.

---

## 한계 및 의의

### 기술적 한계

**계산 비용**: 각 hyperagent 변형체를 벤치마크에서 평가해야 하므로, 50회 반복 실행 시 상당한 GPU/API 비용이 발생한다. Claude 3.5 Sonnet을 Foundation Model로 사용하며, 각 도메인에서 수백 회의 API 호출이 필요하다. 현재 시점에서 소규모 연구팀이 쉽게 재현하기 어려운 비용 구조이다. 더 효율적인 평가 방법(surrogate model, early stopping 등)의 개발이 필요하다.

**Frozen FM 의존성**: 기저 Foundation Model이 고정되어 있어, FM 자체의 한계를 넘어서는 개선에는 제약이 있다. Hyperagent는 FM의 능력을 더 효과적으로 활용하는 방법(prompting, workflow, tool use)을 학습하지만, FM이 근본적으로 할 수 없는 작업을 가능하게 만들지는 못한다. 향후 FM 자체의 파인튜닝과 결합하거나, 학습 가능한 소형 모델과의 하이브리드 접근법이 흥미로운 방향이 될 것이다.

**평가의 한계**: 현재 벤치마크 기반 평가는 과적합(overfitting)의 위험이 있다. Training subset에서의 성능이 test set으로 일반화되지만, 벤치마크 자체의 범위를 넘어서는 능력 향상은 측정되지 않는다. 또한 50회 반복이라는 제한된 예산 내에서의 결과이므로, 더 많은 반복에서의 스케일링 특성(수렴, 발산, 정체 등)은 아직 미검증이다.

### Safety 관련 논의

자기 수정 가능한 AI 시스템은 통제 가능성과 예측 가능성 면에서 본질적 위험을 내포한다. 저자들은 Section 6에서 이를 명시적으로 다루며, 다음과 같은 안전장치를 설명한다:

| 안전장치 | 설명 | 효과 |
|---------|------|------|
| 제한된 tool set | Bash + file editing만 허용 | 시스템 접근 범위 제한 |
| 샌드박스 환경 | 격리된 실행 환경 | 외부 영향 차단 |
| 감사 추적(audit trail) | 모든 수정 사항 기록 | 사후 분석 가능 |
| 인간 감독 | human oversight 유지 | 위험 개입 가능 |

그러나 시스템이 **"자기 개선 속도를 자기 개선할 수 있다"**는 점에서, 장기적으로는 인간의 감독 속도를 초과할 가능성에 대한 우려가 있다. 현재 실험에서 50회 반복은 관리 가능한 수준이지만, 반복 횟수가 수천, 수만 회로 증가할 경우 인간이 모든 수정을 추적하고 검증하는 것은 비현실적이다.

저자들은 "안전성을 절대적 보장이나 양적 지표로만 접근하기보다, 인간 감독과의 균형 속에서 점진적으로 신뢰를 구축해야 한다"고 주장한다. 이는 현실적인 접근이지만, 구체적인 safety threshold나 자동화된 안전 검증 메커니즘에 대한 논의는 부족하다.

### 학술적 의의

본 논문의 핵심 기여를 세 가지로 정리한다:

1. **메타 학습의 재귀적 확장**: 기존 self-improving AI가 task-level에 국한된 반면, DGM-H는 meta-level 개선을 가능하게 하여 자기 개선의 깊이를 한 단계 끌어올렸다.

2. **범용 자기 개선 프레임워크**: 도메인별 수작업 적응 없이도 다양한 도메인에서 자기 개선이 가능한 범용 프레임워크를 제시했다. 특히 DGM이 실패하는 비코딩 도메인에서 DGM-H가 성공한다는 것은 이 접근법의 실질적 가치를 보여준다.

3. **자기 개선의 전이 및 축적 가능성**: Meta-level 개선이 도메인 간 전이 가능하고 축적된다는 경험적 증거를 최초로 제시했다. 이는 self-improving AI의 장기적 비전인 "가속적 자기 개선"의 실현 가능성을 지지한다.

---

## 후속 연구 방향

### 단기적 확장 방향

**다중 Foundation Model 활용**: 현재 DGM-H는 단일 Frozen FM(Claude 3.5 Sonnet)에 의존한다. 다양한 FM을 상황에 따라 선택적으로 활용하는 hyperagent가 가능하다면, FM 개별의 한계를 넘어서는 개선이 가능할 것이다.

**계산 효율성 개선**: Surrogate model을 활용한 빠른 사전 평가, early stopping, 병렬 평가 등으로 50회 반복에 소요되는 비용을 줄이는 연구가 필요하다.

**더 넓은 도메인 검증**: 현재 4개 도메인에서의 검증은 고무적이지만, 자연어 처리, 컴퓨터 비전, 과학적 발견 등 더 다양한 도메인에서의 검증이 범용성 주장을 강화할 것이다.

### 장기적 연구 과제

**FM과의 공동 최적화**: Frozen FM의 제약을 넘어, FM의 파인튜닝과 hyperagent의 자기 수정을 동시에 최적화하는 연구가 흥미로운 방향이다. 이는 "도구를 더 잘 사용하는 법"(현재)을 넘어 "도구 자체를 개선하는 것"까지 확장하는 것이다.

**Safety-aware self-improvement**: 자기 개선 과정에 safety constraint를 명시적으로 통합하여, 성능 개선과 안전성을 동시에 최적화하는 방향이다. 현재의 사후적 안전장치를 넘어, 자기 개선 알고리즘 자체에 안전성 고려를 내재화하는 것이 필요하다.

**멀티 에이전트 자기 개선**: 단일 hyperagent가 아닌, 여러 hyperagent가 협력적으로 자기 개선하는 생태계를 구성하는 연구이다. [[multi-agent-comparison]]에서 다루는 멀티 에이전트 프레임워크와의 결합이 가능한 방향이다.

---

## 결론

HyperAgents는 self-improving AI의 핵심 병목인 **고정된 메타 메커니즘**을 해결하기 위해, task agent와 meta agent를 단일 편집 가능 프로그램으로 통합하는 접근법을 제시한다. "더 나은 해를 찾는 것"이 아니라 **"더 나은 해를 찾는 방법을 찾는 것"**이 가능한 시스템이다.

4개 도메인에서의 실험은 세 가지 핵심 결과를 보여준다:

1. **범용성**: 코딩 특화 DGM이 실패하는 논문 리뷰(0.0 -> 0.710), 로보틱스(0.348 -> 0.372)에서 DGM-H가 성공하며, 수작업 도메인 적응(DGM-custom)을 초과한다.
2. **전이 가능성**: Paper Review + Robotics에서 학습된 meta-level 전략이 Math Grading으로 성공적으로 전이된다 (imp@50 = 0.630). 수작업 적응은 전이에 완전히 실패한다 (0.0).
3. **축적성**: Transfer hyperagent에서 시작하면 더 높은 최종 성능(0.640 > 0.610)과 더 좁은 신뢰 구간을 보이며, 이전 학습의 자기 개선이 보존되고 축적된다.

이는 open-ended self-improving AI의 실현 가능성을 한 단계 끌어올린 결과이다. 동시에, 계산 비용의 현실적 제약과 자기 수정 가능 시스템의 안전성이라는 중요한 연구 과제를 남긴다. Metacognitive self-modification이 실용적인 수준으로 발전하기 위해서는, 효율성과 안전성 양 측면에서의 후속 연구가 필수적이다.

## Paper Summary

| 항목 | 내용 |
|------|------|
| 제목 | HyperAgents: Self-Referential Agents for Open-Ended Self-Improvement |
| 저자 | Jenny Zhang, Bingchen Zhao, Wannan Yang, Jakob Foerster, Jeff Clune, Minqi Jiang, Sam Devlin, Tatiana Shavrina |
| 소속 | UBC, Vector Institute, Edinburgh, NYU, FAIR at Meta, Meta Superintelligence Labs |
| 연도 | 2026 |
| 학회 | arXiv preprint |
| 원문 | [arXiv:2603.19461](https://arxiv.org/abs/2603.19461) |
| 코드 | [github.com/facebookresearch/Hyperagents](https://github.com/facebookresearch/Hyperagents) |
| 핵심 키워드 | Self-Improving AI, Metacognitive Self-Modification, Open-Ended AI, LLM Agent, Darwin Godel Machine |
