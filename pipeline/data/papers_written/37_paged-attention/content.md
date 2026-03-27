## 개요

LLM(대규모 언어 모델)을 프로덕션 환경에서 서빙할 때, GPU 메모리 관리는 가장 핵심적인 병목 요소 중 하나입니다. [[Transformer]] 아키텍처의 자기회귀적(autoregressive) 생성 방식은 모든 이전 토큰의 키(Key)와 값(Value) 벡터를 캐시에 저장해야 하며, 이 KV 캐시(KV cache)는 생성 길이와 동시 요청(배치) 수에 비례하여 선형적으로 증가합니다. 예를 들어, 13B 파라미터 모델에서 단일 요청의 KV 캐시는 최대 1.7GB에 달할 수 있으며, 이는 전체 GPU 메모리의 상당 부분을 차지합니다.

Kwon et al.(2023)이 SOSP 2023(운영체제 분야의 최고 권위 학술대회)에서 발표한 이 논문은 LLM 서빙의 메모리 비효율 문제를 운영체제(OS)의 가상 메모리(virtual memory) 관점에서 근본적으로 재접근합니다. 핵심 아이디어는 단순하면서도 강력합니다. OS가 물리 메모리를 고정 크기 페이지(page) 단위로 관리하여 단편화를 해결하는 것처럼, KV 캐시도 고정 크기 블록(block) 단위로 분할하고 비연속적으로 저장하자는 것입니다.

이 아이디어를 구현한 PagedAttention 알고리즘과 vLLM 시스템은 발표 이후 폭발적인 채택률을 보이며, 현재 LLM 서빙 인프라의 사실상 표준(de facto standard)으로 자리 잡았습니다. GitHub에서 40,000개 이상의 스타를 받았으며, Hugging Face TGI, Anyscale, Modal, RunPod 등 주요 서빙 플랫폼에 통합되어 있습니다.

아래 그림은 이 논문의 핵심 기여를 직관적으로 보여줍니다. 기존 시스템은 KV 캐시 메모리 사용량이 배치 크기에 따라 급격히 증가하여 배치 크기 약 8에서 OOM(Out-of-Memory)이 발생하지만, vLLM은 동일 메모리 예산으로 배치 크기 40까지 선형적으로 확장하며 처리량을 3배 이상 높입니다.

![기존 시스템과 vLLM의 배치 크기에 따른 메모리 사용량 및 처리량 비교](figures/fig_1_2.png)
*Figure 1: LLM 서빙 시 메모리 레이아웃과 성능 비교. 위: 배치 크기 증가에 따른 GPU 메모리 사용량 ( 기존 시스템(주황)은 급격한 증가로 조기 OOM이 발생하지만 vLLM(파랑)은 완만하게 증가한다. 아래: 처리량(token/s) 비교 ) vLLM이 동일 메모리에서 훨씬 높은 처리량을 달성한다. (Kwon et al., 2023)*

---

## 배경 및 문제

### KV 캐시의 메모리 소비 구조

[[Transformer]]의 자기회귀 생성에서, 각 디코딩 단계마다 모델은 이전에 생성된 모든 토큰의 키-값(Key-Value) 벡터에 접근해야 합니다. 이를 매번 재계산하는 것은 비효율적이므로, 한 번 계산된 KV 벡터를 캐시에 저장하고 재사용합니다. 이것이 바로 KV 캐시입니다.

단일 요청에 대한 KV 캐시의 총 메모리 소비량은 다음과 같이 계산됩니다:

$$M_{\text{KV}} = 2 \times n_{\text{layers}} \times n_{\text{heads}} \times d_{\text{head}} \times L \times \text{sizeof(dtype)}$$

여기서 $n_{\text{layers}}$는 트랜스포머 레이어 수, $n_{\text{heads}}$는 어텐션 헤드 수, $d_{\text{head}}$는 각 헤드의 차원, $L$은 시퀀스 길이, 그리고 계수 2는 Key와 Value 두 가지를 저장하기 때문입니다. 구체적으로 OPT-13B 모델의 경우:

$$M_{\text{KV}} = 2 \times 40 \times 40 \times 128 \times 2048 \times 2 \text{ bytes} \approx 1.6 \text{ GB}$$

A100 80GB GPU에서 모델 가중치가 약 26GB를 차지하므로, 나머지 54GB를 KV 캐시에 사용할 수 있습니다. 이론적으로는 약 33개의 동시 요청을 처리할 수 있어야 하지만, 기존 시스템에서는 메모리 낭비로 인해 실제로 10~15개 정도만 처리할 수 있었습니다.

### 기존 시스템의 세 가지 메모리 낭비

기존 LLM 서빙 시스템(FasterTransformer, Orca 등)은 각 요청에 대해 KV 캐시를 연속된(contiguous) 메모리 공간에 사전 할당합니다. 이 방식은 다음 세 가지 유형의 메모리 낭비를 유발합니다.

**1. 예약 낭비(Reserved Waste)**

자기회귀 생성에서는 최종 출력 길이를 미리 알 수 없습니다. 따라서 시스템은 가능한 최대 생성 길이 $L_{\max}$만큼의 메모리를 미리 예약합니다. 그러나 실제 생성 길이 $l_i$가 $L_{\max}$보다 짧은 경우가 대부분이므로, $(L_{\max} - l_i)$만큼의 메모리가 사용되지 않은 채 점유됩니다.

$$W_{\text{reserved}} = \sum_{i=1}^{N} (L_{\max} - l_i) \times m_{\text{per\_token}}$$

여기서 $N$은 동시 처리 요청 수, $m_{\text{per\_token}}$은 토큰당 KV 캐시 메모리입니다.

**2. 내부 단편화(Internal Fragmentation)**

연속 할당 방식에서는 메모리를 고정 단위로 할당하므로, 실제 사용량이 할당 단위와 정확히 일치하지 않으면 블록 내부에 사용되지 않는 공간이 남습니다. 이 문제는 OS의 메모리 내부 단편화와 동일한 현상입니다.

**3. 외부 단편화(External Fragmentation)**

다양한 길이의 요청이 도착하고 완료되면서, 해제된 메모리 블록이 비연속적으로 흩어집니다. 전체적으로는 충분한 여유 메모리가 있더라도, 연속된 큰 블록을 확보할 수 없어 새로운 요청을 처리하지 못하는 상황이 발생합니다.

논문의 분석에 따르면, 기존 시스템에서 KV 캐시 메모리의 **60~80%가 이 세 가지 낭비**로 인해 실효적으로 사용되지 못하고 있었습니다. 이는 GPU라는 고가의 자원이 극심하게 낭비되고 있음을 의미합니다.

---

## 핵심 아이디어


아래 그림은 기존 시스템에서 KV 캐시 메모리가 어떻게 낭비되는지를 직관적으로 보여줍니다. 예약 낭비, 내부 단편화, 외부 단편화가 복합적으로 작용하여 실제 유효하게 사용되는 메모리 비율이 극히 낮아지는 구조입니다.

![기존 시스템의 KV 캐시 메모리 낭비 구조](figures/fig_5.png)
*Figure 3: 기존 LLM 서빙 시스템의 KV 캐시 메모리 레이아웃. 예약 낭비(reserved), 내부 단편화(internal fragmentation), 외부 단편화(external fragmentation) 세 가지 유형의 낭비가 동시에 발생하여, 다른 요청의 KV 캐시를 적재할 수 있는 유효 공간이 크게 줄어든다. (Kwon et al., 2023)*

이러한 낭비를 정량적으로 측정한 결과, 기존 시스템들의 KV 캐시 메모리 중 60~80%가 실효적으로 사용되지 못하고 있었습니다. 반면 PagedAttention을 적용한 vLLM은 이 낭비를 5% 이하로 줄여, 동일한 GPU에서 처리할 수 있는 동시 요청 수를 크게 늘립니다.

![LLM 서빙 시스템별 KV 캐시 메모리 낭비 비율 비교](figures/fig_4.png)
*Figure 2: 다양한 LLM 서빙 시스템의 평균 KV 캐시 메모리 낭비 비율. Orca 변형들과 비교하여 vLLM은 토큰 상태(token states) 외의 낭비를 거의 제거하여, 전체 메모리 활용 효율을 극대화한다. (Kwon et al., 2023)*

### 가상 메모리 개념의 KV 캐시 적용

PagedAttention의 핵심 통찰은 KV 캐시 메모리 관리 문제가 OS의 메모리 관리 문제와 본질적으로 동일하다는 점입니다. OS는 이 문제를 수십 년 전에 **가상 메모리(virtual memory)**와 **페이징(paging)** 기법으로 해결했습니다.

OS의 페이징 시스템에서는 다음과 같은 추상화를 사용합니다:

- **물리 메모리**를 고정 크기의 **프레임(frame)**으로 분할합니다.
- 프로세스에게는 **연속적인 가상 주소 공간**을 제공합니다.
- **페이지 테이블(page table)**이 가상 페이지 번호를 물리 프레임 번호로 매핑합니다.
- 물리 프레임이 비연속적이어도 프로세스는 연속적인 메모리로 인식합니다.

PagedAttention은 이 개념을 KV 캐시에 그대로 적용합니다:

| OS 개념 | PagedAttention 대응 개념 |
|---------|------------------------|
| 프로세스 | 요청(Request) / 시퀀스 |
| 가상 페이지 | 논리 블록(Logical Block) |
| 물리 프레임 | 물리 블록(Physical Block) |
| 페이지 테이블 | 블록 테이블(Block Table) |
| 페이지 크기 | 블록 크기 $B$ (토큰 수) |
| 스왑 영역 | CPU 메모리 (스왑 공간) |
| Copy-on-Write | KV 캐시 Copy-on-Write |

이 매핑이 가능한 이유는, 어텐션 연산에서 KV 벡터가 반드시 물리적으로 연속된 메모리에 있을 필요가 없기 때문입니다. 각 블록 내에서의 연산만 올바르게 수행되면, 블록 간의 물리적 위치는 무관합니다.

---

## 방법론

vLLM은 중앙화된 스케줄러, KV 캐시 관리자, 그리고 여러 GPU 워커로 구성된 시스템입니다. 스케줄러가 블록 테이블을 관리하고 요청 스케줄링을 담당하며, 각 워커가 PagedAttention 커널을 실행합니다. GPU 메모리가 부족할 경우 CPU 스왑 공간을 활용하여 KV 캐시를 임시로 저장합니다.

![vLLM 시스템 전체 아키텍처: 스케줄러, KV 캐시 관리자, GPU/CPU 워커](figures/fig_6.png)
*Figure 4: vLLM 시스템 개요. 중앙 스케줄러가 블록 테이블을 통해 KV 캐시 메모리를 관리하고, CPU/GPU 블록 할당자가 물리 블록을 관리하며, 다수의 GPU 워커가 모델 샤드와 캐시 엔진을 병렬로 실행한다. (Kwon et al., 2023)*

### PagedAttention 알고리즘

아래 그림은 PagedAttention의 핵심 메커니즘을 보여줍니다. 기존의 연속 메모리 할당과 달리, KV 캐시를 고정 크기 블록 단위로 분산 저장하고 블록 테이블을 통해 논리 주소를 물리 주소로 매핑합니다.

![PagedAttention의 핵심 메커니즘: 비연속 블록 기반 KV 캐시 저장과 어텐션 계산](figures/fig_7.png)
*Figure 5: PagedAttention 알고리즘의 동작 원리. 쿼리 벡터가 비연속적인 물리 블록에 분산 저장된 키-값 벡터에 접근하여 어텐션을 계산한다. 각 블록은 고정 개수의 토큰 KV 벡터를 담고 있으며, 블록 테이블이 논리 블록 번호를 물리 블록 번호로 변환한다. (Kwon et al., 2023)*

PagedAttention은 KV 캐시를 고정 크기 $B$ 토큰 단위의 블록으로 분할합니다. 각 블록은 $B$개 토큰에 해당하는 키와 값 벡터를 저장합니다. 블록의 물리적 메모리 크기는 다음과 같습니다:

$$S_{\text{block}} = 2 \times n_{\text{heads}} \times d_{\text{head}} \times B \times \text{sizeof(dtype)}$$

어텐션 계산은 블록 단위로 분할되어 수행됩니다. 쿼리 벡터 $q$와 시퀀스 길이 $T$의 KV 캐시에 대해, 전체 블록 수는 $N_B = \lceil T / B \rceil$이 됩니다. 각 블록 $k$에 대해 부분 어텐션 스코어를 계산한 후, 이를 합산합니다:

$$a_{k,j} = \frac{\exp(q \cdot K_{k,j}^T / \sqrt{d_{\text{head}}})}{\sum_{k'=0}^{N_B-1}\sum_{j'=0}^{B-1} \exp(q \cdot K_{k',j'}^T / \sqrt{d_{\text{head}}})}$$

$$\text{output} = \sum_{k=0}^{N_B-1} \sum_{j=0}^{B-1} a_{k,j} \cdot V_{k,j}$$

여기서 $K_{k,j}$와 $V_{k,j}$는 $k$번째 논리 블록의 $j$번째 위치에 저장된 키 및 값 벡터이며, 실제 GPU 메모리에서의 접근은 블록 테이블을 통해 이루어집니다.

실제 구현에서는 수치 안정성을 위해 블록별 softmax 값을 log-sum-exp 트릭으로 결합합니다:

$$m = \max_k(m_k), \quad \text{output} = \frac{\sum_k \exp(m_k - m) \cdot o_k}{\sum_k \exp(m_k - m) \cdot l_k}$$

여기서 $m_k$는 블록 $k$의 최대 어텐션 로짓, $o_k$는 블록 $k$의 가중합, $l_k$는 블록 $k$의 softmax 분모입니다.

### 블록 테이블과 메모리 관리

블록 테이블은 각 요청의 논리 블록 번호를 물리 블록 번호로 매핑하는 간단한 배열입니다. 아래 그림은 이 변환 과정을 구체적으로 보여줍니다. "Four score and seven years ago our fathers brought ..." 라는 시퀀스에서 논리 블록이 블록 테이블을 통해 비연속적인 물리 블록으로 매핑되는 과정을 확인할 수 있습니다.

![vLLM의 블록 테이블 변환: 논리 블록에서 물리 블록으로의 주소 매핑 과정](figures/fig_8.png)
*Figure 6: 블록 테이블 변환 예시. 요청 A의 논리 블록 0~2가 각각 물리 블록 7, 1, 3으로 매핑된다. 각 물리 블록은 GPU DRAM의 비연속적 위치에 저장되지만, 블록 테이블을 통해 논리적으로 연속된 접근이 가능하다. (Kwon et al., 2023)*

요청의 $t$번째 토큰에 접근하려면:

$$\text{physical\_block} = \text{BlockTable}[\text{seq\_id}][\lfloor t / B \rfloor]$$
$$\text{offset} = t \mod B$$
$$K[t] = \text{GPU\_Memory}[\text{physical\_block}][\text{offset}]$$

vLLM의 메모리 관리자(Block Manager)는 다음 연산을 수행합니다:

- **Allocate**: 새 토큰 생성 시 현재 마지막 블록에 여유가 있으면 해당 블록에 추가하고, 여유가 없으면 빈 물리 블록을 할당하여 블록 테이블에 추가합니다.
- **Free**: 요청 완료 시 해당 요청의 모든 물리 블록을 반환하여 즉시 재사용 가능하게 합니다.
- **Fork**: 병렬 샘플링 시 기존 요청의 블록 테이블을 복제하여 새 시퀀스가 동일한 물리 블록을 참조하도록 합니다 (참조 카운트 증가).
- **Swap Out/In**: GPU 메모리 부족 시 물리 블록의 내용을 CPU 메모리로 이동하고, 나중에 다시 GPU로 복원합니다.

이 설계의 핵심 장점은 메모리 할당이 토큰 단위가 아닌 블록 단위로 이루어지기 때문에, 내부 단편화가 마지막 블록에서만 최대 $(B-1)$ 토큰만큼 발생하고, 외부 단편화는 원천적으로 제거된다는 것입니다.

### Copy-on-Write 메모리 공유

병렬 샘플링(parallel sampling)에서 동일한 프롬프트로 $n$개의 서로 다른 응답을 생성할 때, 프롬프트에 해당하는 KV 캐시는 $n$개의 시퀀스에서 동일합니다. PagedAttention은 OS의 Copy-on-Write(CoW) 기법을 적용하여 이 공통 데이터를 물리적으로 한 번만 저장합니다.

동작 과정은 다음과 같습니다:

1. 프롬프트 처리 후, $n$개의 시퀀스가 동일한 물리 블록들을 참조하는 블록 테이블을 갖습니다. 각 물리 블록의 참조 카운트(reference count)가 $n$으로 설정됩니다.
2. 시퀀스 $i$가 새 토큰을 생성하여 블록 $k$를 수정해야 할 때, 참조 카운트가 1보다 크면 해당 블록을 새로운 물리 블록으로 복사합니다.
3. 복사된 블록에 새 토큰의 KV 벡터를 기록하고, 원본 블록의 참조 카운트를 감소시킵니다.

이를 통해 프롬프트 부분의 메모리 사용량이 $n$배 절감됩니다:

$$M_{\text{prompt}} : O(n \times L_p) \rightarrow O(L_p)$$

아래 그림은 병렬 샘플링에서 Copy-on-Write가 동작하는 구체적인 예시를 보여줍니다. 두 시퀀스가 동일한 프롬프트의 물리 블록을 공유하다가, 분기 시점에서만 새로운 블록이 할당됩니다.

![병렬 샘플링에서 Copy-on-Write를 통한 KV 캐시 공유](figures/fig_10.png)
*Figure 8: 병렬 샘플링 예시. 동일 프롬프트에서 여러 시퀀스를 생성할 때, 공유 접두사의 물리 블록은 참조 카운트(ref count)로 관리되며, 분기 시점에서 Copy-on-Write로 새 블록이 할당되어 메모리 중복을 제거한다. (Kwon et al., 2023)*

빔 서치(beam search)에서도 유사하게 적용됩니다. 각 빔은 이전 단계의 빔에서 분기(fork)되므로, 공유되는 접두사(prefix) 부분의 KV 캐시를 CoW로 공유할 수 있습니다. 아래 그림에서 볼 수 있듯이, 각 빔 후보가 이전 단계의 블록을 공유하면서 새로운 토큰에 대해서만 추가 블록을 할당하므로, 빔 크기가 증가해도 메모리 사용량이 선형 이하로 증가합니다.

![빔 서치에서 Copy-on-Write를 통한 KV 캐시 공유](figures/fig_11.png)
*Figure 9: 빔 서치 예시. 4개의 빔 후보가 이전 단계에서 분기할 때, 공유 접두사의 물리 블록을 CoW로 공유한다. 빔 크기가 커져도 메모리 사용량이 선형 이하로 증가하여 대규모 빔 서치가 가능해진다. (Kwon et al., 2023)*

### 프리엠션(Preemption) 정책

GPU 메모리가 부족할 때, vLLM은 처리 중인 요청의 우선순위를 판단하여 낮은 우선순위의 요청을 일시 중단합니다. 중단된 요청의 KV 캐시 블록은 두 가지 방식으로 처리될 수 있습니다:

- **Swap**: 물리 블록의 내용을 CPU 메모리로 복사한 후 GPU 블록을 해제합니다. 나중에 요청을 재개할 때 CPU에서 GPU로 다시 복사합니다.
- **Recompute**: KV 캐시를 완전히 버리고, 나중에 프롬프트를 다시 처리하여 KV 캐시를 재생성합니다.

두 전략의 실제 성능 차이는 블록 크기에 따라 달라지며, 블록 크기가 작을 때(1~4)는 Swap의 오버헤드가 Recompute보다 크지만, 블록 크기 16 이상에서는 Swap이 더 효율적입니다.

논문에서는 First-Come-First-Served(FCFS) 정책을 기본으로 사용합니다. 즉, 나중에 도착한 요청이 먼저 중단 대상이 됩니다. 이는 OS의 스왑 파티션(swap partition) 및 프로세스 스케줄링과 유사한 개념입니다.

### 분산 실행 지원

텐서 병렬(tensor parallelism) 환경에서는 여러 GPU에 걸쳐 어텐션 연산이 분할됩니다. PagedAttention은 중앙화된 스케줄러가 블록 테이블을 관리하고, 각 GPU 워커가 동일한 논리-물리 매핑을 유지하도록 합니다. 모든 GPU에서 동일한 물리 블록 번호에 해당 GPU가 담당하는 어텐션 헤드의 KV 캐시를 저장합니다.

---

## 실험 결과

### 실험 설정

저자들은 다음 환경에서 실험을 수행했습니다:

- **GPU**: NVIDIA A100 80GB
- **모델**: OPT-13B, OPT-66B, OPT-175B, LLaMA-13B
- **비교 대상**: FasterTransformer (NVIDIA), Orca (Microsoft), Hugging Face TGI
- **워크로드**: ShareGPT 데이터셋(실제 ChatGPT 대화), Alpaca 데이터셋
- **메트릭**: 처리량(throughput, requests/second), 지연시간(latency)

실험에 사용된 두 데이터셋은 입출력 길이 분포에서 뚜렷한 차이를 보입니다. ShareGPT는 입력 평균 161토큰, 출력 평균 338토큰으로 긴 대화 시퀀스를 포함하여 예약 낭비가 심화되는 조건이고, Alpaca는 입력 평균 19토큰, 출력 평균 58토큰으로 짧은 시퀀스 위주입니다. 이 대조적인 워크로드 특성을 통해 메모리 관리 효율성의 영향을 다각도로 검증합니다.

### 처리량 비교 (OPT-13B, A100 80GB, ShareGPT 데이터셋)

| 시스템 | 처리량 (req/s) | 정규화 처리량 | vLLM 대비 |
|--------|--------------|-------------|----------|
| Hugging Face TGI | 1.0 | 1.0x | 0.12x |
| FasterTransformer | 2.2 | 2.2x | 0.26x |
| Orca (iteration-level) | 4.1 | 4.1x | 0.48x |
| vLLM (PagedAttention) | **8.5** | **8.5x** | **1.0x** |

vLLM은 Hugging Face TGI 대비 약 8.5배, FasterTransformer 대비 약 3.9배, Orca 대비 약 2.1배의 처리량 향상을 달성했습니다. 아래 그래프는 다양한 모델 크기와 데이터셋에서 이 성능 차이를 보여줍니다.

![다양한 모델과 데이터셋에서의 단일 시퀀스 생성 처리량 비교](figures/fig_16_1.png)
*Figure 12: ShareGPT와 Alpaca 데이터셋에서 OPT-13B/66B/175B 모델의 처리량 비교. 요청 빈도(request rate)가 증가할수록 기존 시스템(FasterTransformer, Orca 등)은 메모리 한계로 처리량이 포화되는 반면, vLLM은 PagedAttention의 효율적 메모리 관리를 통해 일관되게 높은 처리량을 유지한다. (Kwon et al., 2023)*

이러한 처리량 차이의 근본 원인은 동시에 배치할 수 있는 요청 수의 격차에 있습니다. ShareGPT 데이터셋에서 vLLM은 평균 30.42개의 요청을 동시에 처리하며, 이는 Orca Max(7.00) 대비 4.3배에 달합니다. 짧은 시퀀스 위주의 Alpaca 데이터셋에서는 그 차이가 더욱 극대화되어, vLLM(132.44)이 Orca Max 대비 약 19배 많은 요청을 동시에 배치합니다.

### LLaMA-13B 모델에서의 처리량 비교

| 시스템 | 처리량 (req/s) | vLLM 대비 |
|--------|--------------|----------|
| Hugging Face TGI | 1.4 | 0.15x |
| FasterTransformer | 3.1 | 0.33x |
| Orca | 5.4 | 0.57x |
| vLLM | **9.4** | **1.0x** |

### 메모리 활용률 분석

| 항목 | 기존 시스템 | vLLM |
|------|-----------|------|
| KV 캐시 메모리 활용률 | 20~40% | **80~95%** |
| 예약 낭비 | 최대 60% | **< 4%** (마지막 블록만) |
| 외부 단편화 | 있음 | **없음** |
| 내부 단편화 | 있음 | **< $(B-1)$ 토큰/요청** |

### 다양한 서빙 시나리오에서의 성능 향상

| 시나리오 | 설명 | 처리량 향상 |
|---------|------|----------|
| 단일 시퀀스 생성 | 기본 텍스트 생성 | 2.1x |
| 병렬 샘플링 (n=4) | 동일 프롬프트, 4개 응답 생성 | **4.1x** |
| 빔 서치 (beam=4) | 빔 크기 4로 탐색 | **3.7x** |
| 긴 문맥 (2048 토큰) | 긴 입력/출력 시퀀스 | 3.3x |
| 혼합 워크로드 | 다양한 길이의 요청 혼합 | 2.8x |

병렬 샘플링과 빔 서치에서 특히 큰 향상을 보이는 이유는 Copy-on-Write 메커니즘 덕분입니다. 기존 시스템에서는 동일한 프롬프트의 KV 캐시를 $n$개 복제해야 했지만, vLLM은 하나의 사본만 유지합니다. 아래 그래프는 이러한 CoW 효과를 실험적으로 검증한 결과입니다.

![OPT-13B에서 병렬 생성과 빔 서치의 처리량 비교](figures/fig_20_1.png)
*Figure 14: OPT-13B의 Alpaca 데이터셋에서 병렬 생성(n=3)과 빔 서치(beam=6) 처리량 비교. CoW 메커니즘이 적용된 vLLM이 기존 시스템(Orca 변형) 대비 병렬 샘플링에서 최대 4.1배, 빔 서치에서 최대 3.7배의 처리량 향상을 달성한다. (Kwon et al., 2023)*

이 결과는 CoW가 단순한 메모리 절감을 넘어, 동시 처리 가능한 시퀀스 수를 증가시켜 GPU 연산 자원의 활용률까지 높인다는 점을 보여줍니다.

### 블록 크기에 따른 영향

| 블록 크기 $B$ | 처리량 (req/s) | 메모리 낭비율 |
|-------------|--------------|-------------|
| 1 | 7.2 | 0% (블록 테이블 오버헤드 큼) |
| 8 | 8.1 | < 1% |
| **16** | **8.5** | **< 2%** |
| 32 | 8.3 | < 4% |
| 64 | 7.8 | < 8% |

블록 크기가 너무 작으면 블록 테이블 관리 오버헤드가 커지고, 너무 크면 내부 단편화가 증가합니다. 실험 결과에 따르면 블록 크기 1~4에서는 관리 오버헤드로 인해 지연시간이 높고, 64 이상에서는 내부 단편화로 다시 증가하여, 논문에서는 $B=16$이 최적의 균형점임을 실험적으로 확인했습니다.

### 대규모 모델에서의 확장성 (OPT-175B, 8x A100)

vLLM은 텐서 병렬 환경에서도 효과적으로 동작합니다. OPT-175B 모델을 8개 A100에서 실행한 결과, FasterTransformer 대비 약 2.2배의 처리량 향상을 달성했습니다. 이는 중앙화된 스케줄러와 일관된 블록 테이블 관리가 분산 환경에서도 잘 동작함을 보여줍니다.

---

## 의의 및 한계

### 학술적 의의

**1. OS와 ML 시스템의 학제적 융합**

PagedAttention은 운영체제 분야에서 수십 년간 발전시킨 가상 메모리 기법을 ML 시스템에 창의적으로 적용한 대표적 사례입니다. 이 연구는 시스템 분야의 성숙한 기법이 ML 서빙 문제에도 직접적으로 적용될 수 있음을 보여주었으며, 후속 연구에서도 OS 개념을 ML 시스템에 활용하는 흐름을 촉발했습니다.

**2. 메모리 바운드 문제의 근본적 해결**

LLM 서빙에서 처리량이 제한되는 주된 이유가 연산 능력이 아닌 메모리 관리의 비효율이었음을 명확히 보여주고, 이를 거의 최적에 가깝게 해결했습니다. KV 캐시 메모리 낭비를 95% 이상 제거함으로써, GPU의 실효적 활용률을 크게 높였습니다.

**3. 실질적인 업계 표준 정립**

vLLM은 단순한 학술 논문을 넘어 실질적인 오픈소스 소프트웨어로서 업계에 깊이 침투했습니다. 현재 대부분의 LLM 서빙 프레임워크가 PagedAttention 또는 유사한 메커니즘을 채택하고 있습니다.

### 실용적 영향

- **비용 절감**: 동일한 GPU로 2~4배 많은 요청을 처리할 수 있어, LLM API 서비스의 운영 비용을 크게 절감합니다.
- **생태계 확산**: vLLM은 Hugging Face, Anyscale, Modal, BentoML, SkyPilot 등 주요 플랫폼에 통합되어 LLM 서빙의 표준 엔진이 되었습니다.
- **후속 최적화의 기반**: [[FlashAttention]], [[Speculative Decoding]], Continuous Batching 등 다른 최적화 기법과 함께 사용될 수 있어, 전체 서빙 스택의 효율성을 극대화합니다.

### 한계

**1. 블록 크기 선택의 하이퍼파라미터 문제**

블록 크기 $B$는 모델 아키텍처, 워크로드 패턴, GPU 종류에 따라 최적값이 달라질 수 있습니다. 현재는 고정된 블록 크기를 사용하며, 동적으로 적응하는 메커니즘은 제공되지 않습니다.

**2. CPU-GPU 스왑 오버헤드**

프리엠션 시 CPU-GPU 간 데이터 전송의 대역폭 한계로 인해 지연이 발생할 수 있습니다. PCIe 대역폭(약 32 GB/s)이 병목이 되며, 특히 대규모 모델에서는 스왑 비용이 상당합니다.

**3. 멀티모달 모델 확장**

이미지, 오디오 등 가변 크기의 토큰을 처리하는 멀티모달 모델에서는 고정 크기 블록 방식이 비효율적일 수 있으며, 추가적인 설계가 필요합니다.

**4. 접두사 캐싱의 한계**

서로 다른 요청 간에 공통 접두사(system prompt 등)의 KV 캐시를 공유하는 기능은 원 논문에서 제한적으로만 다루고 있습니다. 이후 vLLM에서 Prefix Caching 기능이 추가되었으나, 최적의 캐시 교체 정책(eviction policy)은 여전히 연구 과제입니다.

**5. 커널 오버헤드**

PagedAttention은 비연속 메모리 접근 패턴으로 인해, 연속 메모리를 전제로 최적화된 [[FlashAttention]] 등의 커스텀 커널보다 단일 연산 수준에서는 약간 느릴 수 있습니다. 그러나 이 오버헤드는 동시 처리 요청 수의 증가로 상쇄됩니다.

---

## 코드 예제

vLLM을 사용한 LLM 서빙 예제를 살펴보겠습니다. vLLM은 PagedAttention을 자동으로 적용하므로, 사용자는 메모리 관리를 신경 쓸 필요 없이 간단한 API로 고성능 서빙을 구현할 수 있습니다.

### 기본 오프라인 추론

```python
from vllm import LLM, SamplingParams

# 모델 로드 (PagedAttention 자동 적용)
llm = LLM(
    model="meta-llama/Llama-2-13b-chat-hf",
    tensor_parallel_size=1,       # GPU 수
    gpu_memory_utilization=0.90,  # GPU 메모리 활용률 (기본 90%)
    block_size=16,                # 블록 크기 B (기본값 16)
    swap_space=4,                 # CPU 스왑 공간 (GB)
)

# 샘플링 파라미터 설정
sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=512,
    n=1,  # 시퀀스당 생성 수
)

# 배치 추론 실행
prompts = [
    "Explain the concept of virtual memory in operating systems.",
    "What is the difference between paging and segmentation?",
    "Describe how TLB (Translation Lookaside Buffer) works.",
]

outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    prompt = output.prompt
    generated = output.outputs[0].text
    print(f"Prompt: {prompt[:50]}...")
    print(f"Output: {generated[:200]}...\n")
```

### OpenAI 호환 API 서버

```bash
# vLLM OpenAI 호환 서버 시작
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-13b-chat-hf \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 2 \
    --gpu-memory-utilization 0.90 \
    --max-model-len 4096 \
    --block-size 16
```

```python
# 클라이언트 코드 (OpenAI SDK 호환)
import openai

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed",  # vLLM은 API 키 불필요
)

# 스트리밍 응답
response = client.chat.completions.create(
    model="meta-llama/Llama-2-13b-chat-hf",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain PagedAttention briefly."},
    ],
    stream=True,
    max_tokens=256,
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

### 병렬 샘플링 (Copy-on-Write 활용)

```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-2-7b-chat-hf")

# 동일 프롬프트에서 4개의 다른 응답 생성
# Copy-on-Write로 프롬프트 KV 캐시가 공유됨
sampling_params = SamplingParams(
    temperature=0.8,
    top_p=0.95,
    max_tokens=256,
    n=4,  # 4개의 병렬 시퀀스 (CoW 자동 적용)
    best_of=4,
)

prompt = "Write a creative story about a robot learning to paint:"
outputs = llm.generate([prompt], sampling_params)

for i, output in enumerate(outputs[0].outputs):
    print(f"--- Response {i+1} ---")
    print(output.text[:300])
    print()
```

### Docker를 이용한 배포

```yaml
# docker-compose.yml
services:
  vllm:
    image: vllm/vllm-openai:latest
    runtime: nvidia
    ports:
      - "8000:8000"
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    environment:
      - HUGGING_FACE_HUB_TOKEN=${HF_TOKEN}
    command: >
      --model meta-llama/Llama-2-13b-chat-hf
      --tensor-parallel-size 2
      --gpu-memory-utilization 0.90
      --max-model-len 4096
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 2
              capabilities: [gpu]
```

이러한 간결한 인터페이스 뒤에서 vLLM은 PagedAttention, Continuous Batching, 동적 메모리 할당 등 복잡한 최적화를 자동으로 수행합니다. 사용자는 메모리 관리의 세부사항을 신경 쓸 필요 없이, 높은 처리량과 낮은 지연시간의 LLM 서빙을 구현할 수 있습니다.