<!-- infographic-hero -->
![Tree of Thoughts 핵심 요약](figures/infographic.svg)

*Figure: Tree of Thoughts 한 장 요약 인포그래픽*

# Tree of Thoughts: 트리 탐색 기반 의도적 추론

**Princeton** · **2023-05-17** · **Reasoning Technique** · **오픈**

## 개요

Tree of Thoughts(ToT)는 언어 모델의 추론 과정을 선형 체인이 아닌 트리 구조로 확장하여, 복잡한 문제 해결에 탐색 알고리즘(BFS/DFS)을 결합한 기법이다. Yao et al.(Princeton, 2023)이 논문 "Tree of Thoughts: Deliberate Problem Solving with Large Language Models"에서 발표한 이 프레임워크는, CoT의 단방향 추론 한계를 극복하여 **"계획적이고 의도적인(deliberate)"** 문제 해결을 가능하게 한다.

ToT의 핵심 비유는 인간의 문제 해결 과정이다. 인간은 어려운 문제를 풀 때 여러 가능한 접근 방식을 탐색하고, 유망하지 않은 경로는 포기하고 되돌아가며(backtracking), 가장 유망한 경로를 선택적으로 깊이 탐색한다. CoT가 **"한 줄기 생각"**이라면 ToT는 **"생각의 나무"**를 키우며, 각 가지의 유망성을 평가하여 최적의 경로를 찾는다. 이는 인지과학의 이중 프로세스 이론(System 1의 빠른 직관 vs System 2의 느린 숙고)에서 System 2에 해당하는 의도적 추론(deliberate reasoning)을 LLM에서 구현한 것이다.

기존 추론 기법과의 관계를 정리하면: CoT는 하나의 선형 경로, Self-Consistency는 여러 선형 경로의 병렬 샘플링, ToT는 트리 구조의 체계적 탐색이다. Self-Consistency가 "여러 번 풀어서 다수결"이라면, ToT는 "한 단계씩 유망한 방향을 선택하며 깊이 탐색"하는 것이다. 이 차이는 Game of 24에서 극적으로 드러난다: CoT 4%, Self-Consistency(k=100) 9%, ToT 74%. 다수 샘플링만으로는 해결할 수 없는 문제 유형이 존재하며, **구조화된 탐색이 본질적으로 필요한 과제**에서 ToT가 압도적 우위를 보인다.

![Tree of Thoughts 아키텍처 - 트리 구조 탐색과 단계별 평가·가지치기 기반 의도적 추론 구조](figures/architecture.svg)

*Figure 1: ToT 아키텍처 - 추론 과정을 트리로 확장하여 BFS/DFS 탐색 알고리즘으로 각 단계의 유망성을 평가하고 가지치기하며, CoT의 단방향 추론 한계를 극복한 계획적 문제 해결 프레임워크이다.*

아래 그림은 기존 추론 방식과 ToT의 차이를 시각적으로 비교한다. 입출력(IO), Chain-of-Thought, Self-Consistency, Tree of Thoughts의 구조적 차이를 확인할 수 있다.

![추론 방식 비교 - IO, CoT, CoT-SC, ToT의 구조적 차이](figures/fig_1.png)
*Figure 1: 추론 방식 비교 - (a) IO는 직접 입출력, (b) CoT는 단일 선형 경로, (c) Self-Consistency는 여러 경로의 병렬 샘플링, (d) ToT는 트리 구조의 체계적 탐색으로 각 단계에서 평가와 가지치기를 수행한다. (Source: arXiv 2305.10601)*

## 아키텍처 상세

ToT의 아키텍처는 네 가지 핵심 구성 요소로 이루어진다.

### 사고 분해(Thought Decomposition)

문제를 중간 사고 단위(thought step)로 분해한다. 분해의 세분화 수준은 문제 특성에 따라 결정된다.

| 문제 유형 | 사고 단위 | 세분화 수준 |
|----------|----------|----------|
| Game of 24 | 하나의 산술 연산 (예: $4 + 5 = 9$) | 세밀 |
| Creative Writing | 한 문단의 줄거리 계획 | 중간 |
| Crossword | 하나의 단어 채우기 | 세밀 |
| 코드 설계 | 하나의 모듈 설계 | 중간~거칠음 |

사고 단위가 너무 작으면 탐색 공간이 폭발하고, 너무 크면 중간 평가의 의미가 사라진다. 적절한 세분화 수준의 선택이 ToT 적용의 핵심 설계 결정이다.

### 사고 생성(Thought Generation)

각 상태에서 $k$개의 후보 사고를 생성한다. 두 가지 전략이 있다.

**Sample 전략**: LLM에서 독립적으로 $k$개를 샘플링한다. CoT의 temperature 기반 샘플링과 유사하지만, 전체 추론이 아닌 하나의 사고 단위만 샘플링한다.

**Propose 전략**: LLM에게 "$k$개의 서로 다른 접근법을 제안하라"고 프롬프팅한다. 이 전략은 더 다양하고 의도적인 후보를 생성하는 경향이 있다.

$$G(s) = \{z_1, z_2, ..., z_k\} \quad \text{where } z_i \sim \text{LLM}(\cdot | s) \text{ or } z_{1:k} = \text{LLM}(\text{propose}_k | s)$$

### 상태 평가(State Evaluation)

LLM이 각 중간 상태의 유망성을 평가한다. 이것이 ToT의 가장 독특한 요소로, **LLM을 동시에 생성기(generator)와 평가기(evaluator)로 사용**한다.

**Value 평가**: 각 상태에 대해 1~10점 스케일로 점수를 부여한다.

$$V(s) = \text{LLM}(\text{"이 상태의 유망성을 1-10점으로 평가하라"} | s)$$

**Vote 평가**: 여러 상태를 동시에 제시하고, 가장 유망한 것을 선택하도록 LLM에 투표를 요청한다.

$$\text{best} = \text{LLM}(\text{"가장 유망한 상태를 선택하라"} | s_1, s_2, ..., s_b)$$

### 탐색 알고리즘(Search Algorithm)

생성된 트리를 체계적으로 탐색한다.

**BFS (너비 우선 탐색)**: 각 레벨에서 상위 $b$개의 상태를 유지하며 확장한다. 탐색 공간이 넓지만 깊이가 제한적인 문제에 적합하다.

$$S_{t+1} = \text{top}_b\left(\{s' | s' = [s, z], \; s \in S_t, \; z \in G(s)\}, \; V\right)$$

**DFS (깊이 우선 탐색)**: 유망한 경로를 깊이 탐색하되, 평가 점수가 임계값 $\theta$ 이하이면 백트래킹한다. 해가 깊은 곳에 있는 문제에 적합하다.

$$\text{DFS}(s) = \begin{cases} s & \text{if terminal}(s) \\ \text{DFS}(\arg\max_{z \in G(s)} V([s,z])) & \text{if } V([s,z]) \geq \theta \\ \text{backtrack} & \text{otherwise} \end{cases}$$

### 실행 예시: Game of 24

다음은 Game of 24에서 ToT가 사고를 생성하고 평가하는 실제 프롬프트 예시이다.

![Game of 24에서의 ToT - 사고 생성 프롬프트와 상태 평가 프롬프트](figures/fig_3.png)
*Figure 2: Game of 24에서의 ToT - (a) Propose 전략으로 가능한 다음 연산을 생성하고, (b) Value 평가로 각 상태가 24에 도달할 가능성을 "sure/maybe/impossible"로 판단한다. (Source: arXiv 2305.10601)*

Game of 24는 4개의 숫자와 사칙연산으로 24를 만드는 문제다. 이 문제는 계획, 시행착오, 백트래킹이 필수적으로 요구되어 ToT의 강점이 극대화된다.

```
입력: 4, 5, 6, 10

                      [4, 5, 6, 10]
                    /       |        \
           4+5=9        5*6=30      10-4=6
          [9,6,10]    [4,30,10]    [5,6,6]
          V=7/10       V=5/10      V=6/10
           /    \         |           |
      9+6=15  9*6=54  30-10=20    5+6=11
     [15,10]  [54,10] [4,20]      [11,6]
      V=5/10  V=2/10   V=8/10     V=3/10
        |     (prune)    |
    15+10=25           20+4=24 ✓
    (backtrack)        (성공!)

최종 풀이: 5*6=30 → 30-10=20 → 20+4=24
```

이 예시에서 BFS($b=3$)는 각 레벨에서 상위 3개 상태를 유지하며, $V=2/10$인 $[54,10]$은 가지치기(pruning)된다. $V=8/10$인 $[4,20]$ 경로가 선택되어 최종적으로 $20+4=24$에 도달한다.

## 핵심 혁신

1. **탐색과 평가의 결합**: LLM의 생성 능력(사고 생성)과 판단 능력(상태 평가)을 조합하여, 기존 AI의 탐색 알고리즘(BFS/DFS)을 LLM 추론에 적용했다. 이는 기호적 AI(symbolic AI)의 탐색과 신경망의 생성을 결합한 것이다.

2. **백트래킹(Backtracking)**: CoT나 Self-Consistency에는 없는 되돌아가기 능력을 제공한다. 잘못된 경로를 인식하고 포기한 뒤 다른 경로를 탐색할 수 있다. 이는 계획이 필요한 문제에서 본질적인 이점을 제공한다.

3. **의도적 추론(Deliberate Reasoning)**: System 1(빠른 직관)이 아닌 System 2(느리고 의도적인 숙고)를 LLM에서 구현했다. 각 단계에서 여러 옵션을 명시적으로 생성, 평가, 선택하는 과정이 인간의 숙고적 사고를 모방한다.

4. **자기 평가(Self-Evaluation)**: LLM이 자신의 추론 과정을 평가하는 메타인지(metacognition) 능력을 활용한다. 이 자기 평가가 탐색의 가이드 역할을 하여, 무작위 탐색 대비 효율을 크게 높인다.

아래는 Creative Writing 태스크에서 ToT의 의도적 탐색 과정을 보여준다. 5개의 계획을 샘플링한 후 투표로 최선의 계획을 선택한다.

![Creative Writing에서의 ToT 의도적 탐색 - 5개 계획 샘플링과 투표 기반 선택](figures/fig_7.png)
*Figure 3: Creative Writing 의도적 탐색 - (a) 입력에서 (b) 5개의 서로 다른 글쓰기 계획을 생성하고, (c) LLM 투표로 가장 일관성 있는 계획(Plan 2)을 선택한다. (Source: arXiv 2305.10601)*

## 벤치마크/성능

| 과제 | CoT | Self-Consistency (k=100) | ToT (b=5) | 향상 (CoT 대비) |
|-----|-----|------------------------|-----------|--------------|
| Game of 24 | 4.0% | 9.0% | **74.0%** | +70.0%p |
| Creative Writing | 6.19 | 6.93 | **7.56** | +1.37 |
| Crossword (5x5) | 16% | - | **60%** | +44%p |

Game of 24에서 CoT 4% vs ToT 74%의 압도적 차이는 ToT의 위력을 극적으로 보여준다. 이 과제는 여러 숫자 조합을 시도하고, 잘못된 경로를 포기하는 백트래킹이 필수적인데, 이는 정확히 ToT가 제공하는 기능이다. Self-Consistency(k=100)도 9%에 불과하여, **"여러 번 풀어서 다수결"로는 해결할 수 없는 문제 유형**이 존재함을 실증한다. Crossword에서도 16% $\rightarrow$ 60%로 크게 향상되어, 제약 조건 만족(constraint satisfaction) 문제에서의 효과를 입증했다.

다음은 Mini Crosswords에서의 DFS 탐색과 가지치기 과정이다. 제약 조건을 만족하지 못하는 경로는 즉시 가지치기되어 백트래킹한다.

![Mini Crosswords에서의 ToT DFS - 사고 제안, 우선순위 큐, 상태 평가 및 가지치기](figures/fig_11.png)
*Figure 4: Mini Crosswords DFS 탐색 - (a) 단어 단서에 대한 사고를 제안하고 우선순위 큐로 관리하며, (b) 남은 단서의 충족 가능성을 평가하여 불가능한 상태는 가지치기하고 부모 상태로 백트래킹한다. (Source: arXiv 2305.10601)*

## 학습

ToT는 파인튜닝이 필요 없으며, 추론 시점에만 적용되는 순수 프롬프팅 기법이다. GPT-4를 기반으로 주로 실험되었으며, 주요 하이퍼파라미터는 탐색 너비 $b$(BFS에서 유지할 상태 수, 일반적으로 3~5), 후보 수 $k$(각 상태에서 생성할 사고 수, 5~10), 탐색 깊이, DFS 임계값 $\theta$이다. 비용은 트리의 크기에 비례하여 $O(d \times b \times k)$의 LLM 호출이 필요하다. Game of 24에서는 한 문제당 수십 번의 LLM 호출이 발생하여, 단순 CoT 대비 10~100배의 비용이 소요된다.

## 관련 모델

ToT는 CoT에서 발전하여, 선형 추론을 트리 탐색으로 확장한 기법이다. Self-Consistency가 "여러 경로의 다수결"이라면, ToT는 "각 단계에서의 평가 기반 탐색"으로 더 정교한 추론을 수행한다. ToT가 제시한 "구조화된 추론 탐색"과 "inference-time compute scaling" 개념은 이후 OpenAI의 o1/o3 시리즈가 채택한 내부 추론 메커니즘과 직접적으로 연결되며, 현대 추론 모델(reasoning model)의 이론적 선구 연구로 평가된다.

## 참고 자료

- Yao et al., "Tree of Thoughts: Deliberate Problem Solving with Large Language Models", NeurIPS 2023, arXiv:2305.10601
- [Tree of Thoughts GitHub Repository](https://github.com/princeton-nlp/tree-of-thought-llm)

## 관련 문서

- [[cot|Chain-of-Thought Prompting]] - 발전 기반
