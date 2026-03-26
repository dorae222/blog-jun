## 개요

트랜스포머 아키텍처의 핵심 연산인 셀프 어텐션(self-attention)은 시퀀스 길이 $N$에 대해 $O(N^2)$의 시간 및 메모리 복잡도를 가진다. 이 이차적 복잡도는 긴 시퀀스를 처리하는 대규모 언어 모델(LLM)에서 심각한 병목이 되어 왔다. FlashAttention-1은 IO 인식(IO-aware) 타일링 기법을 도입하여 메모리 효율성을 혁신적으로 개선했지만, GPU의 이론적 최대 처리량(theoretical peak throughput) 대비 실제 달성률은 25~35% 수준에 머물렀다. 이는 GPU 하드웨어의 계산 자원을 충분히 활용하지 못하고 있음을 의미한다.

FlashAttention-2는 GPU 하드웨어의 계산 모델, 메모리 계층 구조, 병렬화 메커니즘을 더욱 깊이 분석하여, FlashAttention-1의 알고리즘적 구조를 근본적으로 재설계한다. 세 가지 핵심 개선 -- 비행렬곱 FLOPs 감소, 시퀀스 길이 차원 병렬화, 워프 간 작업 분배 최적화 -- 을 통해 A100 GPU에서 최대 이론 처리량의 50~73%를 달성하며, FlashAttention-1 대비 약 2배의 추가 속도 향상을 실현한다. 이 논문은 알고리즘 설계에서 하드웨어 특성을 얼마나 정밀하게 반영하느냐가 실제 성능에 결정적인 영향을 미친다는 점을 명확히 보여준다.

## 배경 및 문제

### GPU 메모리 계층 구조

현대 GPU의 메모리 시스템은 여러 계층으로 구성되어 있으며, 각 계층은 용량과 대역폭 사이에 근본적인 트레이드오프를 가진다. NVIDIA A100 GPU를 기준으로 살펴보면 다음과 같다.

**HBM (High Bandwidth Memory)**: GPU의 주 메모리로, 용량은 40GB 또는 80GB이며 대역폭은 약 2TB/s이다. 일반적으로 텐서(tensor)가 저장되는 공간이지만, 온칩(on-chip) 메모리에 비하면 접근 속도가 상대적으로 느리다.

**SRAM (Shared Memory / L1 Cache)**: 각 SM(Streaming Multiprocessor) 내에 위치하는 온칩 메모리로, A100에서는 SM당 최대 192KB를 제공한다. 전체 108개 SM을 합산하면 약 20MB에 불과하지만, 대역폭은 약 19TB/s로 HBM보다 약 10배 빠르다.

**레지스터(Registers)**: 각 스레드가 직접 접근하는 가장 빠른 저장소이다. 용량이 매우 제한적이지만 접근 지연 시간이 사실상 0에 가깝다.

이러한 메모리 계층 구조에서 핵심적인 최적화 원칙은 명확하다. 느린 메모리(HBM)에 대한 접근 횟수를 최소화하고, 가능한 한 많은 연산을 빠른 온칩 메모리(SRAM, 레지스터)에서 수행해야 한다. FlashAttention-1은 이 원칙을 타일링(tiling)으로 실현했지만, SRAM 내에서의 연산 효율성까지는 최적화하지 못했다.

### 어텐션 연산의 수학적 정의

표준 멀티 헤드 어텐션(Multi-Head Attention)의 연산은 다음과 같이 정의된다. 입력 시퀀스 $\mathbf{Q}, \mathbf{K}, \mathbf{V} \in \mathbb{R}^{N \times d}$ 에 대해:

$$\mathbf{S} = \mathbf{Q}\mathbf{K}^\top \in \mathbb{R}^{N \times N}$$

$$\mathbf{P} = \text{softmax}(\mathbf{S} / \sqrt{d}) \in \mathbb{R}^{N \times N}$$

$$\mathbf{O} = \mathbf{P}\mathbf{V} \in \mathbb{R}^{N \times d}$$

여기서 $N$은 시퀀스 길이, $d$는 헤드 차원이다. 이 연산의 총 FLOPs는 $O(N^2 d)$이며, 중간 행렬 $\mathbf{S}$와 $\mathbf{P}$를 HBM에 저장하면 $O(N^2)$의 추가 메모리가 필요하다.

FlashAttention-1은 온라인 소프트맥스(online softmax) 기법을 활용하여, 중간 행렬을 HBM에 저장하지 않고 타일 단위로 어텐션을 계산한다. 이를 통해 HBM 접근 횟수를 $O(N^2 d^2 M^{-1})$로 줄였다(여기서 $M$은 SRAM 크기). 하지만 이 과정에서 발생하는 비행렬곱 연산(스케일링, 소프트맥스 정규화, 재스케일링 등)의 오버헤드와 병렬화 비효율성은 해결하지 못했다.

### FlashAttention-1의 세 가지 한계

FlashAttention-2 논문에서는 FlashAttention-1의 구체적인 성능 병목을 세 가지로 분석한다.

**한계 1 -- 비행렬곱 연산 과다**: A100 GPU의 Tensor Core는 FP16/BF16 행렬곱에 대해 312 TFLOPS의 처리량을 제공하지만, 비행렬곱 연산(원소별 덧셈, 곱셈, 소프트맥스의 지수/합산 등)의 처리량은 약 19.5 TFLOPS에 불과하다. 즉, 행렬곱 유닛은 비행렬곱 유닛보다 약 16배 빠르다. FlashAttention-1의 내부 루프에서는 매 반복마다 누적 출력값 $\mathbf{O}$를 재스케일링하는 연산이 발생하며, 이러한 비행렬곱 연산이 전체 실행 시간의 상당 부분을 차지한다.

**한계 2 -- 시퀀스 차원 병렬화 부재**: FlashAttention-1은 배치 크기 $B$와 헤드 수 $H$ 차원으로만 스레드 블록을 병렬화한다. 따라서 병렬 작업의 총 수는 $B \times H$이다. A100에는 108개의 SM이 있으므로, $B \times H < 108$이면 일부 SM이 유휴(idle) 상태가 된다. 예를 들어 배치 크기 1, 헤드 수 32인 경우 GPU의 약 30%만 활용된다. 이는 긴 시퀀스 추론(long-context inference)이나 GQA(Grouped Query Attention) 환경에서 심각한 성능 저하를 초래한다.

**한계 3 -- 워프 간 비효율적 작업 분배**: GPU의 SM 내에서 실행되는 워프(warp, 32개 스레드의 묶음) 간 작업 분배 방식이 비효율적이다. FlashAttention-1에서는 $\mathbf{K}$와 $\mathbf{V}$ 블록을 4개 워프에 분배하여 각 워프가 어텐션의 부분 결과를 계산한 뒤, 공유 메모리(shared memory)를 통해 결과를 합산한다. 이 과정에서 워프 간 동기화(synchronization)와 공유 메모리 읽기/쓰기가 필수적으로 발생하며, 이것이 상당한 오버헤드를 유발한다.

## 핵심 아이디어

FlashAttention-2의 핵심 통찰은 다음과 같다. 동일한 IO 복잡도를 유지하면서도, GPU 하드웨어의 계산 특성에 맞게 알고리즘의 내부 구조를 재설계하면 실질적인 성능을 크게 향상시킬 수 있다는 것이다. 구체적으로 세 가지 개선을 도입한다.

### 개선 1: 비행렬곱 FLOPs 감소

FlashAttention-1의 순전파 알고리즘에서는 외부 루프가 $\mathbf{K}, \mathbf{V}$ 블록을 순회하고, 내부 루프에서 $\mathbf{Q}$ 블록을 처리한다. 이 구조에서는 매 내부 반복마다 출력 $\mathbf{O}$에 대해 다이아그래밍 행렬 $\text{diag}(l_i^{\text{new}})^{-1} \text{diag}(l_i)$를 곱하는 재스케일링 연산이 필요하다.

FlashAttention-2는 루프 순서를 뒤집어, 외부 루프에서 $\mathbf{Q}$ 블록을 고정하고 내부 루프에서 $\mathbf{K}, \mathbf{V}$ 블록을 순회한다. 다음 그림은 이 변경된 타일링 구조를 보여준다. Q 블록을 SRAM에 고정한 채 K/V 블록을 순차적으로 로드하며, 온라인 소프트맥스를 통해 출력을 점진적으로 누적하는 과정이 핵심이다.

![FlashAttention-2 순전파 타일링 구조: Q 블록을 SRAM에 고정하고 K/V 블록을 순회하며 온라인 소프트맥스로 누적 계산](figures/fig_1.png)
*FlashAttention-2의 순전파 타일링 구조. Q 블록을 고정한 상태에서 K/V 블록을 순차적으로 로드하여, SRAM 내에서 어텐션 스코어와 출력을 점진적으로 계산한다. 중간 행렬 $\mathbf{S}$, $\mathbf{P}$는 HBM에 저장되지 않으며(주황색 점선), 최종 정규화는 모든 K/V 블록 처리 후 한 번만 수행된다.*

이 구조 변경의 핵심적 이점은 다음과 같다.

- 하나의 $\mathbf{Q}$ 블록에 대한 출력을 계산하는 동안 누적 변수 $\mathbf{O}_i$, 로그-합 $l_i$, 최대값 $m_i$를 SRAM의 레지스터에 유지할 수 있다.
- 최종 정규화($\mathbf{O}_i / l_i$)를 내부 루프가 완료된 후 한 번만 수행하면 된다.
- 내부 루프에서의 재스케일링은 $\exp(m_i^{\text{old}} - m_i^{\text{new}})$를 곱하는 것으로 충분하며, 이 연산의 횟수가 FlashAttention-1 대비 절반으로 줄어든다.

수학적으로, 내부 루프의 $j$번째 반복에서의 업데이트 규칙은 다음과 같다:

$$m_i^{(j)} = \max(m_i^{(j-1)}, \text{rowmax}(\mathbf{S}_i^{(j)}))$$

$$\tilde{\mathbf{P}}_i^{(j)} = \exp(\mathbf{S}_i^{(j)} - m_i^{(j)})$$

$$l_i^{(j)} = e^{m_i^{(j-1)} - m_i^{(j)}} l_i^{(j-1)} + \text{rowsum}(\tilde{\mathbf{P}}_i^{(j)})$$

$$\mathbf{O}_i^{(j)} = e^{m_i^{(j-1)} - m_i^{(j)}} \mathbf{O}_i^{(j-1)} + \tilde{\mathbf{P}}_i^{(j)} \mathbf{V}_j$$

내부 루프 종료 후 최종 출력은 $\mathbf{O}_i = \mathbf{O}_i^{(T_c)} / l_i^{(T_c)}$로 한 번만 정규화한다. 여기서 $T_c = \lceil N / B_c \rceil$은 $\mathbf{K}, \mathbf{V}$의 블록 수이다.

이 구조 변경으로 비행렬곱 FLOPs가 약 2배 감소하여, Tensor Core의 행렬곱 연산이 전체 실행 시간에서 차지하는 비율이 크게 높아진다.

### 개선 2: 시퀀스 길이 차원 병렬화

FlashAttention-1은 병렬 작업 수가 $B \times H$로 제한되어 있어, SM 수(A100에서 108개)보다 적을 경우 GPU 활용률이 떨어진다. FlashAttention-2는 외부 루프의 $\mathbf{Q}$ 블록을 독립적인 스레드 블록으로 처리할 수 있다는 점을 활용하여, 시퀀스 길이 차원에 걸친 병렬화를 추가한다.

새로운 병렬 작업 수는 다음과 같다:

$$\text{총 스레드 블록 수} = B \times H \times \lceil N / B_r \rceil$$

여기서 $B_r$은 $\mathbf{Q}$ 블록의 행 수이다. 예를 들어 $B=1$, $H=32$, $N=8192$, $B_r=64$인 경우, FlashAttention-1의 병렬 작업 수는 32인 반면 FlashAttention-2는 $32 \times 128 = 4096$개의 스레드 블록을 생성한다. 이를 통해 108개의 SM을 모두 활용할 수 있게 된다.

이 병렬화가 가능한 이유는 루프 순서 변경 덕분이다. 외부 루프가 $\mathbf{Q}$ 블록을 순회하므로, 각 $\mathbf{Q}$ 블록의 출력은 독립적으로 계산된다. $\mathbf{K}, \mathbf{V}$는 읽기 전용(read-only)이므로 모든 스레드 블록이 동시에 접근해도 충돌이 발생하지 않는다.

다음 그림은 이러한 시퀀스 차원 병렬화가 순전파와 역전파에서 각각 어떻게 적용되는지를 보여준다. 순전파에서는 어텐션 행렬의 행(Q 블록)을 워커에 분배하고, 역전파에서는 열(K/V 블록)을 분배하여, 인과적 마스킹 하에서도 워커 간 작업량의 균형을 맞춘다.

![FlashAttention-2 시퀀스 병렬화 -- 순전파에서는 행 방향, 역전파에서는 열 방향으로 워커에 타일을 분배](figures/fig_2.png)
*순전파(왼쪽)에서는 Q 블록을 행 방향으로 워커에 분배하고, 역전파(오른쪽)에서는 K/V 블록을 열 방향으로 분배한다. 인과적 마스킹(하삼각 영역)에서 각 워커의 유효 연산량(색칠된 영역)이 대략 균등해지도록 설계되었다.*

**인과적(causal) 어텐션에서의 부하 균형**: 인과적 마스킹을 적용하면 $\mathbf{Q}$ 블록의 위치에 따라 유효한 $\mathbf{K}, \mathbf{V}$ 블록의 수가 달라진다. 시퀀스 초반의 $\mathbf{Q}$ 블록은 소수의 $\mathbf{K}, \mathbf{V}$ 블록만 참조하고, 후반의 $\mathbf{Q}$ 블록은 거의 모든 블록을 참조한다. 이로 인해 스레드 블록 간 작업량 불균형이 발생할 수 있다. FlashAttention-2는 완전히 마스킹된 블록(모든 원소가 $-\infty$인 블록)을 아예 건너뛰는 최적화를 적용하여, 인과적 어텐션의 실질적 연산량을 비인과적 어텐션의 약 절반으로 줄인다.

### 개선 3: 워프 간 작업 분배 개선

GPU의 SM 내에서는 일반적으로 4~8개의 워프가 하나의 스레드 블록을 구성한다. FlashAttention-2에서는 4개의 워프를 사용하며, 이들 간의 작업 분배 방식을 근본적으로 재설계한다. 다음 두 그림은 FlashAttention-1과 FlashAttention-2의 워프 분배 방식의 차이를 직관적으로 보여준다.

**FlashAttention-1의 방식 (split-K)**: $\mathbf{K}$와 $\mathbf{V}$ 블록을 4개 워프에 분배한다. 각 워프는 $\mathbf{Q} \mathbf{K}_j^\top$을 계산하여 부분 어텐션 스코어를 얻고, 소프트맥스와 $\mathbf{P}_j \mathbf{V}_j$를 계산한다. 이후 4개 워프의 결과를 합산하기 위해 공유 메모리에 쓰고, 동기화 배리어(sync barrier)를 거친 뒤, 하나의 워프가 결과를 읽어서 합산한다. 이 과정에서 공유 메모리 접근과 워프 동기화가 병목이 된다.

![FlashAttention-1의 split-K 워프 분배: K/V를 4개 워프에 분배하고 Q는 모든 워프가 공유](figures/fig_3_1.png)
*FlashAttention-1의 split-K 방식. $\mathbf{K}^T$와 $\mathbf{V}$를 4개 워프에 분할하고 $\mathbf{Q}$는 전체 워프가 공유한다. 각 워프가 부분 결과를 독립적으로 계산한 뒤, 공유 메모리(shared memory)를 통해 합산해야 하므로 워프 간 동기화 오버헤드가 발생한다.*

**FlashAttention-2의 방식 (split-Q)**: 반대로 $\mathbf{Q}$ 블록을 4개 워프에 분배한다. 모든 워프가 동일한 $\mathbf{K}$, $\mathbf{V}$ 블록에 접근하지만, 각 워프는 서로 다른 $\mathbf{Q}$ 행들의 출력을 독립적으로 계산한다. 각 워프의 결과가 완전히 독립적이므로, 워프 간에 결과를 합산하거나 동기화할 필요가 없다. $\mathbf{K}$, $\mathbf{V}$는 공유 메모리에서 읽기만 하면 되므로, 공유 메모리 쓰기 연산도 최소화된다.

![FlashAttention-2의 split-Q 워프 분배: Q를 4개 워프에 분배하고 K/V는 모든 워프가 읽기 전용으로 공유](figures/fig_3_2.png)
*FlashAttention-2의 split-Q 방식. $\mathbf{Q}$를 4개 워프에 분할하고, $\mathbf{K}^T$와 $\mathbf{V}$는 전체 워프가 읽기 전용으로 공유한다. 각 워프의 출력이 완전히 독립적이므로 워프 간 동기화가 불필요하고, 공유 메모리 쓰기가 최소화된다.*

이 변경으로 워프 간 동기화 오버헤드가 사실상 제거되며, 공유 메모리 대역폭도 더 효율적으로 활용된다. split-K에서 split-Q로의 전환은 단순한 분배 방향의 변경처럼 보이지만, 이것이 가능한 이유는 개선 1의 루프 순서 변경과 밀접하게 연결되어 있다. 외부 루프가 Q 블록을 순회하는 구조이기 때문에, Q를 워프 간에 분할하는 것이 자연스럽게 독립적인 출력을 보장하는 것이다.

## 방법론

### Forward Pass 알고리즘

FlashAttention-2의 순전파 알고리즘을 상세히 기술하면 다음과 같다.

**입력**: $\mathbf{Q}, \mathbf{K}, \mathbf{V} \in \mathbb{R}^{N \times d}$, 블록 크기 $B_r$(Q 블록), $B_c$(KV 블록)

**출력**: $\mathbf{O} \in \mathbb{R}^{N \times d}$

```
Algorithm: FlashAttention-2 Forward Pass
1. Q, K, V를 HBM에서 블록 단위로 분할
   T_r = ceil(N / B_r), T_c = ceil(N / B_c)
2. for i = 1 to T_r (병렬 실행, 각 블록은 별도 스레드 블록):
   (a) Q_i를 HBM에서 SRAM으로 로드 (크기: B_r x d)
   (b) O_i = 0, l_i = 0, m_i = (-inf)   (레지스터에 초기화)
   (c) for j = 1 to T_c (순차 실행):
       i.   K_j, V_j를 HBM에서 SRAM으로 로드
       ii.  S_ij = Q_i @ K_j^T / sqrt(d)   (Tensor Core 행렬곱)
       iii. m_i_new = max(m_i, rowmax(S_ij))
       iv.  P_ij = exp(S_ij - m_i_new)
       v.   l_i = exp(m_i - m_i_new) * l_i + rowsum(P_ij)
       vi.  O_i = exp(m_i - m_i_new) * O_i + P_ij @ V_j  (Tensor Core 행렬곱)
       vii. m_i = m_i_new
   (d) O_i = O_i / l_i                    (최종 정규화, 1회)
   (e) O_i를 SRAM에서 HBM으로 저장
   (f) l_i, m_i를 HBM에 저장 (역전파용)
```

핵심 포인트는 단계 2(c)vi에서 $\mathbf{O}_i$의 재스케일링이 $\exp(m_i - m_i^{\text{new}})$를 곱하는 것으로 이루어지며, 최종 $1/l_i$ 정규화는 루프 밖에서 한 번만 수행된다는 점이다. FlashAttention-1에서는 이 정규화가 매 반복마다 $\text{diag}(l_i)$ 역행렬을 곱하는 형태로 이루어졌으므로, 비행렬곱 연산의 비중이 훨씬 높았다.

### Backward Pass 알고리즘

역전파에서는 순전파 때 저장한 $\mathbf{O}$, $l$, $m$ 값을 활용하여 그래디언트를 계산한다. 역전파에서도 루프 순서 최적화와 워프 분배 개선이 동일하게 적용된다.

역전파의 핵심 연산은 $d\mathbf{Q}$, $d\mathbf{K}$, $d\mathbf{V}$를 계산하는 것이다:

$$d\mathbf{V} = \mathbf{P}^\top d\mathbf{O}$$

$$d\mathbf{P} = d\mathbf{O} \mathbf{V}^\top$$

$$d\mathbf{S} = d\mathbf{P} \odot \mathbf{P} - \mathbf{P} \odot (d\mathbf{P} \cdot \mathbf{P})^\top \mathbf{1}$$

$$d\mathbf{Q} = d\mathbf{S} \mathbf{K} / \sqrt{d}, \quad d\mathbf{K} = d\mathbf{S}^\top \mathbf{Q} / \sqrt{d}$$

역전파에서는 $d\mathbf{K}$와 $d\mathbf{V}$가 모든 $\mathbf{Q}$ 블록으로부터의 기여를 합산해야 하므로, 순전파처럼 단순히 외부 루프를 $\mathbf{Q}$ 블록으로 설정할 수 없다. 대신 FlashAttention-2는 역전파에서 외부 루프를 $\mathbf{K}, \mathbf{V}$ 블록으로, 내부 루프를 $\mathbf{Q}$ 블록으로 설정하되, 워프 분배와 비행렬곱 연산 최적화는 동일하게 적용한다. 시퀀스 차원 병렬화는 $\mathbf{K}, \mathbf{V}$ 블록의 외부 루프에 적용된다.

### IO 복잡도 분석

FlashAttention-2의 HBM 접근 횟수는 FlashAttention-1과 동일하다:

$$\Theta\left(\frac{N^2 d^2}{M}\right)$$

여기서 $M$은 SRAM의 크기이다. 이는 $d \leq M$ 조건 하에서 최적(optimal)임이 증명되어 있다. 즉, FlashAttention-2는 IO 복잡도를 변경하지 않으면서, 같은 IO 접근 패턴 내에서의 연산 효율성만을 개선한다.

하지만 실질적인 HBM 접근 횟수는 인과적 마스킹 최적화를 통해 감소한다. 인과적 어텐션에서 완전히 마스킹된 블록을 건너뛰면, 실제 로드되는 $\mathbf{K}, \mathbf{V}$ 블록의 수가 평균적으로 절반으로 줄어들기 때문이다.

### GQA/MQA 지원

FlashAttention-2는 GQA(Grouped Query Attention)와 MQA(Multi-Query Attention)를 네이티브로 지원한다. GQA에서는 $\mathbf{Q}$의 헤드 수($H_q$)가 $\mathbf{K}, \mathbf{V}$의 헤드 수($H_{kv}$)보다 크며, $H_q / H_{kv}$개의 쿼리 헤드가 하나의 키-값 헤드를 공유한다. FlashAttention-2는 $\mathbf{K}, \mathbf{V}$ 텐서를 복제하지 않고 인덱싱만으로 처리하여 메모리 효율성을 유지한다.

## 실험 결과

### FLOPS 달성률 비교 (A100 80GB, 헤드 차원 128)

다음 표는 다양한 시퀀스 길이에서의 어텐션 순전파 처리량을 비교한다. A100의 이론적 최대 FP16/BF16 행렬곱 처리량은 312 TFLOPS이다.

| 시퀀스 길이 | PyTorch Naive | FlashAttention-1 | FlashAttention-2 | FA2 이론 대비 |
|-----------|-------------|-----------------|-----------------|------------|
| 512       | ~55 TFLOPS  | ~115 TFLOPS     | ~180 TFLOPS     | ~58%       |
| 1k        | ~45 TFLOPS  | ~130 TFLOPS     | ~195 TFLOPS     | ~63%       |
| 2k        | ~38 TFLOPS  | ~140 TFLOPS     | ~205 TFLOPS     | ~66%       |
| 4k        | ~30 TFLOPS  | ~145 TFLOPS     | ~215 TFLOPS     | ~69%       |
| 8k        | OOM         | ~148 TFLOPS     | ~220 TFLOPS     | ~71%       |
| 16k       | OOM         | ~150 TFLOPS     | ~230 TFLOPS     | ~73%       |

FlashAttention-2는 시퀀스 길이가 길어질수록 이론 대비 달성률이 높아지며, 16k 시퀀스에서 73%에 도달한다. 이는 시퀀스가 길수록 타일링의 오버헤드가 전체 연산량 대비 상대적으로 줄어들고, 시퀀스 차원 병렬화를 통한 SM 활용률이 높아지기 때문이다.

아래 그림은 다양한 시퀀스 길이에서 FlashAttention-2가 기존 방법들을 압도하는 성능을 달성하는 것을 보여준다. 특히 PyTorch 표준 어텐션은 8k 이상에서 OOM이 발생하는 반면, FlashAttention-2는 16k까지 안정적으로 동작하며 176 TFLOPs/s를 달성한다.

![A100 80GB에서 어텐션 순전파+역전파 속도 비교 -- 비인과적 어텐션, 헤드 차원 128](figures/fig_6_1.png)
*A100 80GB SXM4에서 비인과적(causal=False) 어텐션의 순전파+역전파 처리량 비교. FlashAttention-2(보라)가 모든 시퀀스 길이에서 FlashAttention-1(주황), xformers(초록), Triton(빨강), PyTorch(파랑)를 상회하며, 시퀀스 길이 16k에서 176 TFLOPs/s를 달성한다. PyTorch 표준 어텐션은 8k 이상에서 메모리 부족(OOM)이 발생한다.*

### FlashAttention-1 대비 속도 향상 (end-to-end)

| 설정                        | 속도 향상 | 비고                     |
|---------------------------|---------|------------------------|
| 순전파 (causal=False)       | ~2.0x   | 비행렬곱 감소 + 워프 분배    |
| 순전파 (causal=True)        | ~2.0x   | 마스킹 블록 스킵 포함       |
| 순전파+역전파 (causal=False) | ~1.7x   | 역전파 최적화 여지 존재      |
| 순전파+역전파 (causal=True)  | ~2.0x   | 인과적 마스킹 최적화 효과     |

역전파에서의 속도 향상이 순전파보다 다소 낮은 이유는, 역전파에서는 $d\mathbf{Q}$, $d\mathbf{K}$, $d\mathbf{V}$ 세 개의 그래디언트를 모두 계산해야 하므로 루프 구조의 유연성이 제한되기 때문이다. 그러나 인과적 마스킹을 적용하면 마스킹된 블록 스킵 최적화가 순전파와 역전파 모두에 적용되어, 종합 속도 향상이 ~2.0x로 회복된다.

### GPT 모델 학습 처리량 (8xA100 80GB, Megatron-LM)

실제 LLM 학습 환경에서의 end-to-end 성능을 GPT 스타일 모델로 측정한 결과이다. 어텐션이 전체 학습 시간에서 차지하는 비율은 모델 크기와 시퀀스 길이에 따라 다르지만, 어텐션 부분만의 속도 향상(~2x)이 전체 학습 속도 향상(~1.2-1.3x)으로 반영된다.

| 모델 크기     | 시퀀스 길이 | 기존 (Megatron) | FA1 적용    | FA2 적용     | FA2 속도 향상 |
|------------|---------|---------------|-----------|------------|------------|
| 1.3B       | 2k      | 142 TFLOPS    | 170 TFLOPS | 189 TFLOPS | 1.33x      |
| 2.7B       | 2k      | 149 TFLOPS    | 176 TFLOPS | 196 TFLOPS | 1.32x      |
| GPT-3 175B | 2k      | 143 TFLOPS    | 163 TFLOPS | 190 TFLOPS | 1.33x      |
| 1.3B       | 8k      | OOM           | 139 TFLOPS | 168 TFLOPS | 1.21x      |
| 2.7B       | 8k      | OOM           | 148 TFLOPS | 175 TFLOPS | 1.18x      |

특히 GPT-3 175B 규모에서도 기존 Megatron-LM 대비 1.33배의 학습 속도 향상이 확인되며, 시퀀스 길이 8k에서는 기존 방법이 OOM으로 학습 자체가 불가능한 반면 FlashAttention-2는 안정적으로 동작한다. 8k 시퀀스에서 속도 향상 비율이 다소 낮은 것은, 긴 시퀀스에서 어텐션 외 연산(FFN, 통신 등)의 비중이 상대적으로 줄어들어 어텐션 최적화의 전체 효과가 더 직접적으로 반영되기 때문이다.

### 헤드 차원별 성능

| 헤드 차원 ($d$) | FA1 TFLOPS | FA2 TFLOPS | 속도 향상 |
|--------------|----------|----------|--------|
| 64           | ~100     | ~160     | ~1.6x  |
| 128          | ~140     | ~220     | ~1.6x  |
| 256          | ~120     | ~200     | ~1.7x  |

헤드 차원이 128일 때 가장 높은 절대 처리량을 달성한다. 이는 $d=128$이 Tensor Core의 타일 크기(16x16 또는 8x32)와 정렬이 잘 맞아 레지스터 활용과 메모리 접근 패턴이 최적화되기 때문이다. $d=256$에서 절대 처리량이 다소 감소하는 것은, 블록 크기가 커져 SRAM 용량 제약으로 동시에 처리할 수 있는 블록 수가 줄어들기 때문이다.

## 의의 및 한계

### 의의

**사실상의 업계 표준**: FlashAttention-2는 발표 이후 거의 모든 주요 LLM 학습 및 추론 프레임워크에 채택되었다. PyTorch 2.0+의 `torch.nn.functional.scaled_dot_product_attention`, vLLM, TGI(Text Generation Inference), Megatron-LM, DeepSpeed, nanoGPT, LLaMA 학습 코드 등에서 기본 어텐션 구현으로 사용된다.

**하드웨어 인식 알고리즘 설계의 모범 사례**: 이 논문은 동일한 알고리즘적 아이디어(IO 인식 타일링)를 유지하면서도, 하드웨어 특성에 맞춘 구현 수준의 최적화가 2배의 성능 향상을 가져올 수 있음을 보여준다. 이는 시스템 연구와 알고리즘 연구의 교차점에서 중요한 시사점을 제공한다.

**GQA/MQA와의 시너지**: FlashAttention-2의 GQA 네이티브 지원은 LLaMA-2 70B, Mistral, Mixtral 등 GQA를 채택한 모델들의 추론 속도를 크게 향상시켰다. 특히 긴 시퀀스 추론에서 KV 캐시 메모리 절약과 어텐션 계산 효율성이 동시에 달성된다.

**긴 컨텍스트 처리의 실용화**: 시퀀스 길이 차원 병렬화 덕분에 소규모 배치에서도 높은 GPU 활용률을 유지할 수 있어, 100K+ 토큰의 긴 컨텍스트를 처리하는 모델(Claude, GPT-4 Turbo 등)의 실용화에 기여했다.

**후속 연구의 기반**: FlashAttention-3(H100의 TMA, wgmma, 비동기 실행 활용), FlashDecoding(추론 시 KV 차원 병렬화), Ring Attention(다중 GPU 시퀀스 병렬화) 등 후속 최적화 연구의 기반이 되었다.

### 한계

**하드웨어 종속성**: CUDA 커스텀 커널로 구현되어 있어 NVIDIA GPU(A100, H100, RTX 3090/4090 등)에 최적화되어 있다. AMD GPU(ROCm), Intel GPU, Apple Silicon 등 다른 하드웨어에서는 별도의 구현이 필요하며, 동일한 성능 향상을 보장하기 어렵다. 다만 Triton 기반 구현이 제공되어 이식성이 일부 개선되었다.

**짧은 시퀀스에서의 제한적 이점**: 시퀀스 길이가 256 이하인 경우, 타일링과 온라인 소프트맥스의 오버헤드가 실제 연산 절감보다 클 수 있어 이점이 줄어든다. 이런 경우 cuBLAS의 배치 행렬곱이 더 효율적일 수 있다.

**커널 수정의 어려움**: 어텐션 패턴의 변형(sliding window, dilated, sparse 등)을 지원하려면 CUDA/Triton 커널을 직접 수정해야 한다. 이는 높은 수준의 GPU 프로그래밍 전문 지식을 요구하며, 디버깅이 매우 어렵다.

**역전파 최적화의 여지**: 순전파에서의 속도 향상(~2x)에 비해 순전파+역전파 통합 속도 향상(~1.7x)이 다소 낮다. 역전파 알고리즘의 구조적 제약으로 인해 루프 순서 최적화가 순전파만큼 자유롭지 않기 때문이다.

**수치 정밀도**: FP16/BF16 연산에서 온라인 소프트맥스의 재스케일링 과정에서 미세한 수치적 차이가 발생할 수 있다. 대부분의 실용적 상황에서 문제가 되지 않지만, 정밀한 수치 재현성(numerical reproducibility)이 요구되는 경우 주의가 필요하다.

## 코드 예제

### FlashAttention-2의 핵심 알고리즘 구현 (PyTorch)

다음 코드는 FlashAttention-2의 핵심 알고리즘을 PyTorch로 구현한 참조 코드이다. 실제 CUDA 커널의 동작을 이해하기 위한 용도이며, 프로덕션에서는 `torch.nn.functional.scaled_dot_product_attention`을 사용하는 것을 권장한다.

```python
import torch
import torch.nn.functional as F
import math
import time
from typing import Optional


def flash_attention_2_reference(
    Q: torch.Tensor,       # (B, H, N, d)
    K: torch.Tensor,       # (B, H, N, d)
    V: torch.Tensor,       # (B, H, N, d)
    block_size_q: int = 64,
    block_size_kv: int = 64,
    causal: bool = False,
) -> torch.Tensor:
    """FlashAttention-2 순전파 참조 구현.

    핵심 변경점:
    1. 외부 루프: Q 블록 (병렬화 가능)
    2. 내부 루프: K,V 블록 (순차 처리)
    3. 최종 정규화를 루프 밖에서 1회 수행
    """
    B, H, N, d = Q.shape
    scale = 1.0 / math.sqrt(d)
    O = torch.zeros_like(Q)

    num_blocks_q = math.ceil(N / block_size_q)
    num_blocks_kv = math.ceil(N / block_size_kv)

    # 외부 루프: Q 블록 순회 (실제 GPU에서는 병렬 실행)
    for i in range(num_blocks_q):
        q_start = i * block_size_q
        q_end = min(q_start + block_size_q, N)
        Q_block = Q[:, :, q_start:q_end, :]  # (B, H, Br, d)

        # 레지스터에 유지되는 누적 변수
        O_block = torch.zeros_like(Q_block)
        l_block = torch.zeros(B, H, q_end - q_start, 1,
                              device=Q.device, dtype=Q.dtype)
        m_block = torch.full((B, H, q_end - q_start, 1),
                             float('-inf'), device=Q.device, dtype=Q.dtype)

        # 내부 루프: K,V 블록 순회 (순차 처리)
        kv_end_idx = num_blocks_kv
        if causal:
            # 인과적 마스킹: q_start 이후의 K 블록은 건너뜀
            kv_end_idx = min(num_blocks_kv, i + 1 + 1)  # 여유분 포함

        for j in range(kv_end_idx):
            kv_start = j * block_size_kv
            kv_end = min(kv_start + block_size_kv, N)
            K_block = K[:, :, kv_start:kv_end, :]  # (B, H, Bc, d)
            V_block = V[:, :, kv_start:kv_end, :]  # (B, H, Bc, d)

            # 어텐션 스코어 계산 (Tensor Core 행렬곱)
            S_block = torch.matmul(Q_block, K_block.transpose(-2, -1)) * scale

            # 인과적 마스킹 적용
            if causal:
                q_indices = torch.arange(q_start, q_end, device=Q.device)
                k_indices = torch.arange(kv_start, kv_end, device=Q.device)
                mask = q_indices.unsqueeze(-1) >= k_indices.unsqueeze(0)
                S_block = S_block.masked_fill(~mask.unsqueeze(0).unsqueeze(0),
                                              float('-inf'))

            # 온라인 소프트맥스 업데이트
            m_block_new = torch.maximum(m_block, S_block.max(dim=-1, keepdim=True).values)
            P_block = torch.exp(S_block - m_block_new)

            # 누적값 재스케일링 (비행렬곱 연산, 최소화된 횟수)
            alpha = torch.exp(m_block - m_block_new)
            l_block = alpha * l_block + P_block.sum(dim=-1, keepdim=True)
            O_block = alpha * O_block + torch.matmul(P_block, V_block)

            m_block = m_block_new

        # 최종 정규화 (루프 밖에서 1회)
        O[:, :, q_start:q_end, :] = O_block / l_block

    return O


def benchmark_attention(
    batch: int = 2,
    heads: int = 32,
    seq_len: int = 2048,
    head_dim: int = 128,
    device: str = 'cuda',
    num_runs: int = 10,
) -> None:
    """표준 Attention vs Flash Attention 2 속도/메모리 비교."""
    Q = torch.randn(batch, heads, seq_len, head_dim,
                    device=device, dtype=torch.float16)
    K = torch.randn(batch, heads, seq_len, head_dim,
                    device=device, dtype=torch.float16)
    V = torch.randn(batch, heads, seq_len, head_dim,
                    device=device, dtype=torch.float16)

    # 표준 Attention: O(N^2) 메모리 사용
    def standard_attention(Q, K, V):
        scale = math.sqrt(head_dim)
        # (B, H, N, N) 크기의 전체 어텐션 행렬 생성
        scores = torch.matmul(Q, K.transpose(-2, -1)) / scale
        mask = torch.tril(torch.ones(seq_len, seq_len, device=device))
        scores = scores.masked_fill(mask == 0, float('-inf'))
        attn = F.softmax(scores.float(), dim=-1).half()
        return torch.matmul(attn, V)

    # Flash Attention 2: PyTorch의 SDPA 인터페이스
    def flash_attention_2(Q, K, V):
        return F.scaled_dot_product_attention(Q, K, V, is_causal=True)

    if device == 'cuda' and torch.cuda.is_available():
        # Warmup
        for _ in range(3):
            _ = flash_attention_2(Q, K, V)
        torch.cuda.synchronize()

        # 표준 Attention 벤치마크
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        t0 = time.time()
        for _ in range(num_runs):
            out_std = standard_attention(Q, K, V)
        torch.cuda.synchronize()
        std_time = (time.time() - t0) / num_runs * 1000
        std_mem = torch.cuda.max_memory_allocated() / 1024**3

        # Flash Attention 2 벤치마크
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        t0 = time.time()
        for _ in range(num_runs):
            out_fa2 = flash_attention_2(Q, K, V)
        torch.cuda.synchronize()
        fa2_time = (time.time() - t0) / num_runs * 1000
        fa2_mem = torch.cuda.max_memory_allocated() / 1024**3

        print(f"=== Benchmark (B={batch}, H={heads}, N={seq_len}, d={head_dim}) ===")
        print(f"Standard Attention: {std_time:.2f}ms, {std_mem:.3f}GB")
        print(f"Flash Attention 2:  {fa2_time:.2f}ms, {fa2_mem:.3f}GB")
        print(f"속도 향상: {std_time / fa2_time:.1f}x")
        print(f"메모리 절감: {std_mem / fa2_mem:.1f}x")
    else:
        print("CUDA 없음: CPU 실행 (실제 FA2는 GPU 전용)")
        out = flash_attention_2(Q.float(), K.float(), V.float())
        print(f"출력 shape: {out.shape}")


# GQA(Grouped Query Attention) 지원 예제
def fa2_with_gqa(
    Q: torch.Tensor,   # (B, num_q_heads, N, d)
    K: torch.Tensor,   # (B, num_kv_heads, N, d)
    V: torch.Tensor,   # (B, num_kv_heads, N, d)
) -> torch.Tensor:
    """GQA: Q 헤드 수 > KV 헤드 수일 때 FA2가 효율적으로 처리.

    예: LLaMA-2 70B는 num_q_heads=64, num_kv_heads=8 (GQA 8그룹)
    FA2는 KV를 복제하지 않고 인덱싱으로 처리하여 메모리 효율적.
    """
    B, Hq, N, d = Q.shape
    Hkv = K.shape[1]
    assert Hq % Hkv == 0, "Q 헤드 수는 KV 헤드 수의 배수여야 합니다"

    # KV를 Q 헤드 수에 맞게 확장 (repeat_interleave)
    # FA2 커널 내부에서는 이 복제 없이 인덱싱으로 처리
    num_groups = Hq // Hkv
    K_expanded = K.repeat_interleave(num_groups, dim=1)
    V_expanded = V.repeat_interleave(num_groups, dim=1)

    return F.scaled_dot_product_attention(
        Q, K_expanded, V_expanded, is_causal=True
    )


if __name__ == '__main__':
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    benchmark_attention(batch=2, heads=32, seq_len=2048, head_dim=128,
                        device=device)

    # GQA 테스트
    B, N, d = 1, 1024, 128
    Q = torch.randn(B, 32, N, d, device=device, dtype=torch.float16)
    K = torch.randn(B, 8, N, d, device=device, dtype=torch.float16)   # GQA 4그룹
    V = torch.randn(B, 8, N, d, device=device, dtype=torch.float16)
    out = fa2_with_gqa(Q, K, V)
    print(f"GQA 출력 shape: {out.shape}")
```

위 코드에서 `flash_attention_2_reference` 함수는 FlashAttention-2의 핵심 알고리즘을 Python 수준에서 충실히 재현한다. 외부 루프가 Q 블록을 순회하고, 내부 루프에서 K/V 블록을 순차 처리하며, 최종 정규화를 루프 밖에서 한 번만 수행하는 구조를 확인할 수 있다.

## 관련 문서

- [[flash-attention|FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness]] -- 발전 기반
