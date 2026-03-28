# Mamba-2: SSM과 어텐션의 수학적 동치성을 증명한 SSD 프레임워크

**Carnegie Mellon University / Princeton University** · **2024-05-31** · **SSM** · **Apache-2.0**

## 개요

Mamba-2는 2024년 Albert Gu와 Tri Dao가 발표한 후속 연구로, SSM과 Attention 간의 수학적 동치성을 발견한 SSD(Structured State Space Duality) 프레임워크를 기반으로 한다. 이 연구의 핵심 기여는 이론적 통찰에 있다. 선택적 SSM이 특정 조건하에서 구조화된 마스크 어텐션(Structured Masked Attention)과 수학적으로 동일한 연산임을 증명한 것이다.

Mamba-1의 선택적 SSM을 상태 확장 차원 $N$이 헤드 차원과 분리된 구조로 재설계하여, SSD 알고리즘으로 더 빠르고 효율적인 학습이 가능해졌다. FlashAttention 스타일의 타일링 알고리즘을 SSM에 적용할 수 있게 되었으며, 동일 규모 Mamba-1 대비 훈련 효율 2~8배 향상을 달성했다.

이 이중성(duality)의 발견은 SSM과 Transformer라는 두 패러다임이 근본적으로 같은 연산의 서로 다른 관점임을 보여준다. 이론적으로는 두 분야의 알고리즘과 최적화 기법을 자유롭게 상호 차용할 수 있는 기반을 마련했으며, 실용적으로는 SSM 모델의 학습 효율을 극적으로 개선했다.

![Mamba-2 아키텍처 — SSD 프레임워크 기반 SSM-어텐션 이중성을 활용한 구조화된 상태 공간 모델](figures/architecture.svg)

*Figure 1: Mamba-2 아키텍처 — SSM과 구조화된 마스크 어텐션의 수학적 동치성(SSD)을 기반으로 FlashAttention 스타일 타일링을 적용하여 Mamba-1 대비 2~8배 학습 효율을 향상시킨다.*

## 아키텍처 상세

SSD 프레임워크의 핵심은 선택적 SSM을 행렬 연산으로 재해석하는 것이다. 이를 통해 SSM과 어텐션이라는 두 가지 시퀀스 모델링 패러다임 간의 근본적 연결을 수학적으로 밝힌다.

### 1-세미분리 행렬(1-Semiseparable Matrix)

선택적 SSM의 입출력 관계를 행렬 형태로 전개하면, 출력 $y_t = \sum_{s \leq t} M_{ts} x_s$ 형태가 된다. 여기서 마스크 행렬 $M$의 원소는 다음과 같다.

$$M_{ts} = C_t^T \left(\prod_{r=s+1}^{t} \bar{A}_r\right) B_s$$

이 행렬 $M$은 **1-세미분리(1-semiseparable)** 구조를 가진다. 1-세미분리 행렬이란 하삼각(lower triangular) 부분의 모든 부분행렬의 rank가 최대 1인 행렬이다. 상태 차원 $N > 1$이면 rank-$N$ 세미분리 행렬이 된다.

세미분리 행렬의 중요한 성질은 이 행렬이 **인수분해 가능(factorizable)** 하다는 점이다. 즉, $M = L \odot (QK^T)$ 형태로 분해할 수 있으며, 여기서 $L$은 구조화된 마스크, $Q$와 $K$는 각각 SSM의 $C$와 $B$ 파라미터에 대응한다. 이 인수분해가 바로 SSM-어텐션 이중성의 수학적 근거가 된다.

구체적으로, 대각 SSM($A$가 대각 행렬)의 경우 마스크 행렬 $M$은 다음과 같이 분해된다:

$$M_{ts} = (C_t \odot a_{s+1:t})^T B_s = C_t^T \text{diag}(a_{s+1:t}) B_s$$

여기서 $a_{s+1:t} = \prod_{r=s+1}^{t} \bar{A}_r$는 시간 스텝 $s$에서 $t$까지의 누적 감쇠(cumulative decay)이다. 이 분해 구조가 세미분리 행렬의 핵심이며, 후술할 청크 단위 알고리즘의 효율성을 가능하게 한다.

### SSM-Attention 동치성

Transformer의 어텐션은 $Y = \text{softmax}(QK^T) V$ 형태이고, SSM의 출력은 $Y = M \cdot X$ 형태이다. softmax를 제거하고 구조화된 마스크를 적용하면, 두 연산이 수학적으로 동일해진다.

$$\underbrace{Y = M \cdot X}_{\text{SSM (recurrence)}} \quad \Longleftrightarrow \quad \underbrace{Y = (L \odot QK^T) \cdot V}_{\text{Structured Masked Attention}}$$

여기서 $L$은 구조화된 하삼각 마스크이다. 이 동치성은 SSM의 상태 전이를 어텐션의 마스크 패턴으로, 어텐션의 QKV를 SSM의 B, C, $x$로 대응시킨다.

이 동치성을 보다 상세히 살펴보면, 대응 관계는 다음과 같다:

| SSM 관점 | 어텐션 관점 |
|----------|------------|
| 상태 전이 행렬 $\bar{A}$ | 마스크 패턴 $L$ |
| 입력 사영 $B$ | Key 행렬 $K$ |
| 출력 사영 $C$ | Query 행렬 $Q$ |
| 입력 시퀀스 $x$ | Value 행렬 $V$ |

표준 softmax 어텐션은 $M$이 full-rank인 경우에 해당하며, 선택적 SSM은 $M$이 low-rank 세미분리 구조인 경우에 해당한다. 이러한 관점에서 보면, SSM은 구조적 제약이 추가된 선형 어텐션의 특수한 형태이다. 반대로, 선형 어텐션은 $A = I$(항등 행렬)인 SSM의 특수한 경우이다.

이 이중성은 단순한 수학적 호기심이 아니라 실질적인 알고리즘 설계에 직접적으로 활용된다. SSM의 순환(recurrence) 형태는 $O(1)$ 메모리로 추론에 유리하고, 어텐션의 행렬 곱셈 형태는 GPU의 텐서 코어를 활용한 병렬 학습에 유리하다. SSD는 이 두 관점을 상황에 따라 전환할 수 있게 해준다.

### 멀티-헤드 SSM 구조

Mamba-2 블록은 상태 차원 $N$을 헤드 수 $H$로 나누어 멀티-헤드 구조를 가진다. 각 헤드가 독립적인 SSM을 수행하며, Transformer의 Multi-Head Attention과 유사한 역할 분화가 일어난다. 이 설계로 텐서 병렬화(tensor parallelism)와 시퀀스 병렬화(sequence parallelism)가 Transformer처럼 자연스럽게 적용된다.

구체적으로, 전체 모델 차원 $D$를 $H$개의 헤드로 분할하면 각 헤드의 차원은 $P = D / H$가 된다. 각 헤드 $h$는 독립적인 SSM 파라미터 $A^{(h)}, B^{(h)}, C^{(h)}$를 가지며, 헤드별 입출력은 다음과 같다:

$$y_t^{(h)} = \sum_{s \leq t} \left(C_t^{(h)T} \prod_{r=s+1}^{t} \bar{A}_r^{(h)} B_s^{(h)}\right) x_s^{(h)}$$

Mamba-1에서는 상태 차원 $N$과 모델 차원 $D$가 결합되어 있었기 때문에, 상태 크기를 키우면 연산량이 $O(DN)$으로 증가하여 병목이 발생했다. Mamba-2에서는 $N$을 헤드 차원 $P$와 분리함으로써 이 제약을 해소했다. 헤드당 상태 크기 $N$을 독립적으로 확장할 수 있으며, 헤드 간 연산은 완전히 병렬화된다.

Transformer의 MHA, MQA, GQA에 대응하는 다양한 헤드 구조도 자연스럽게 정의된다. 예를 들어, 모든 헤드가 동일한 $B, C$를 공유하면 Multi-Query SSM이 되고, 그룹 단위로 공유하면 Grouped-Query SSM이 된다. 논문에서는 이러한 변형을 체계적으로 분류하고 실험적으로 비교하였다.

### SSD 타일링 알고리즘

FlashAttention의 핵심 아이디어인 블록 단위 연산을 SSM에 적용했다. 시퀀스를 청크 크기 $C$로 분할하고, 청크 내부에서는 행렬 곱셈으로 병렬 계산, 청크 간에서는 순환적 상태 전파를 수행한다.

$$\text{Intra-chunk: } Y_{\text{chunk}} = (L_{\text{chunk}} \odot Q_{\text{chunk}} K_{\text{chunk}}^T) V_{\text{chunk}}$$
$$\text{Inter-chunk: } S_{i+1} = \bar{A}_{\text{chunk}} S_i + B_{\text{chunk}}^T X_{\text{chunk}}$$

이 타일링은 GPU의 SRAM-HBM 메모리 계층을 최적화하여 실제 처리 속도를 크게 향상시킨다. 상태 크기를 Mamba-1 대비 8~16배 확장해도 효율적으로 동작한다.

#### 하드웨어 효율성: 텐서 코어 활용

SSD 알고리즘의 실질적 속도 향상은 GPU 텐서 코어(Tensor Core)의 활용에서 비롯된다. Mamba-1의 parallel scan 알고리즘은 원소별(element-wise) 연산에 의존하여 텐서 코어를 활용할 수 없었다. 반면, SSD는 청크 내부 연산을 행렬-행렬 곱셈(GEMM) 형태로 변환하므로, A100/H100 GPU의 텐서 코어가 제공하는 높은 연산 처리량을 직접 활용한다.

구체적으로, 청크 크기 $C = 256$ 기준으로 각 청크 내부는 $C \times C$ 크기의 행렬 곱셈으로 처리된다. 이는 $256 \times 256$ GEMM에 해당하며, 텐서 코어의 최적 워크로드에 적합하다. 청크 간 상태 전파만 순환적으로 수행하면 되므로, 전체 시퀀스 길이 $L$에 대해 순환 연산의 횟수는 $L/C$로 줄어든다.

메모리 접근 패턴도 FlashAttention과 동일한 원칙으로 최적화된다. 청크 단위 데이터를 SRAM에 로드한 후 모든 연산을 SRAM 내에서 수행하고, 결과만 HBM에 기록한다. 이로 인해 메모리 대역폭 병목이 해소되어 실제 wall-clock 시간이 크게 단축된다.

## 핵심 혁신

Mamba-2의 핵심 혁신은 세 가지이다.

첫째, **SSM-Attention 이중성 이론**이다. 선택적 SSM과 구조화된 마스크 어텐션이 수학적으로 동일함을 증명하여, 두 분야의 알고리즘을 상호 차용할 수 있는 이론적 기반을 제공한다.

둘째, **확장된 상태 크기**이다. Mamba-1의 $N=16$에서 $N=64\sim256$까지 확장할 수 있게 되었으며, 상태 크기 증가가 성능 향상으로 직접 이어짐을 확인했다.

셋째, **텐서/시퀀스 병렬화 지원**이다. 멀티-헤드 구조 덕분에 Transformer와 동일한 분산 학습 전략을 적용할 수 있다.

## 벤치마크/성능

| 모델 (2.7B) | Pile PPL↓ | 학습 속도 | 상태 크기 |
|------------|-----------|----------|----------|
| Mamba-2 | 6.18 | 1.5x Mamba-1 | 256 |
| Mamba-1 | 6.22 | 1x | 16 |
| Transformer++ | 6.10 | 0.8x | N/A |
| Mamba-2 (N=64) | 6.20 | 1.3x Mamba-1 | 64 |

| 모델 | 학습 알고리즘 | 멀티-헤드 | 상태 크기 | 이론적 기반 |
|------|-----------|---------|---------|------------|
| Mamba-2 | SSD 타일링 | 예 | 256 (8~16x) | SSM-Attn 이중성 |
| Mamba-1 | Parallel scan | 아니오 | 16 | 선택적 SSM |
| RetNet | 청크 순환 | 예 | 고정 | Retention |
| GLA | Chunkwise | 예 | 행렬 | 게이트 선형 어텐션 |

## 학습

Pile 데이터셋으로 학습하며, GPT-NeoX 토크나이저를 사용한다. A100 80GB GPU 클러스터에서 SSD CUDA 커널로 메모리 효율을 최적화했다. Mamba-1과 동일한 학습 설정에서 2.7B 기준 훈련 속도 약 50% 향상을 달성했다. 상태 확장 크기 $N=64$를 기본값으로 사용한다.

다음은 SSD의 청크 단위 이중 계산(dual computation)을 보여주는 의사 코드이다.

```python
import torch

def ssd_chunk_computation(Q, K, V, A_cumsum, chunk_size):
    """SSD 프레임워크의 intra-chunk 행렬 곱셈"""
    B, L, H, D = Q.shape
    n_chunks = L // chunk_size
    
    # 청크 단위로 분할
    Q_c = Q.reshape(B, n_chunks, chunk_size, H, D)
    K_c = K.reshape(B, n_chunks, chunk_size, H, D)
    V_c = V.reshape(B, n_chunks, chunk_size, H, D)
    
    # Intra-chunk: 행렬 곱셈 (어텐션 관점)
    attn = torch.einsum('bchd,bcjd->bchj', Q_c, K_c)  # QK^T
    
    # 구조화된 마스크 적용 (세미분리 행렬)
    mask = build_semiseparable_mask(A_cumsum, chunk_size)
    attn = attn * mask  # causal + decay mask
    
    # 출력 계산
    Y_intra = torch.einsum('bchj,bcjd->bchd', attn, V_c)
    
    # Inter-chunk: 순환 상태 전파
    states = compute_chunk_states(K_c, V_c, A_cumsum)
    Y_inter = apply_states(Q_c, states, A_cumsum)
    
    return Y_intra + Y_inter
```

## Mamba-1 vs Mamba-2 vs Transformer 비교

Mamba-2의 위치를 명확히 이해하기 위해, Mamba-1 및 Transformer와의 핵심 차이를 정리한다.

| 특성 | Mamba-1 | Mamba-2 | Transformer |
|------|---------|---------|-------------|
| **시퀀스 연산** | 선택적 SSM (scan) | SSD (타일링 + scan) | Self-Attention |
| **이론적 기반** | 선택적 상태 공간 | SSM-Attn 이중성 | 어텐션 메커니즘 |
| **학습 알고리즘** | Parallel scan | 청크 행렬곱 + 순환 | FlashAttention |
| **텐서 코어 활용** | 불가 | 가능 | 가능 |
| **상태 크기** | 16 (고정) | 64~256 (확장 가능) | N/A |
| **멀티-헤드** | 미지원 | 지원 | 지원 |
| **추론 복잡도** | $O(1)$ per step | $O(1)$ per step | $O(L)$ per step |
| **학습 복잡도** | $O(LDN)$ | $O(LD \cdot \min(N, C))$ | $O(L^2D)$ |
| **분산 학습** | 제한적 | TP/SP 지원 | TP/SP 지원 |

Mamba-2는 Mamba-1의 선형 시간 추론이라는 장점을 유지하면서, Transformer의 학습 효율성 기법(텐서 코어, 타일링, 분산 학습)을 차용할 수 있게 된 것이 핵심이다. 학습 시에는 어텐션 관점의 행렬 곱셈을 사용하고, 추론 시에는 SSM 관점의 순환 연산을 사용하는 "이중 모드" 전환이 가능하다.

## 한계 및 과제

SSD 프레임워크의 이론적 기여에도 불구하고, Mamba-2에는 여전히 몇 가지 중요한 한계가 존재한다.

**첫째, 정확한 정보 검색(in-context retrieval)의 한계이다.** SSM은 고정 크기 상태 벡터를 통해 시퀀스를 압축하므로, 수천 토큰 이전에 등장한 특정 정보를 정확히 검색하는 데 본질적 어려움이 있다. MQAR(Multi-Query Associative Recall) 벤치마크에서 Mamba-2는 상태 크기 확대로 Mamba-1 대비 개선을 보이지만, 동일 규모의 Transformer에는 여전히 미치지 못한다. 이는 상태 크기 $N$이 유한한 한 근본적으로 해소되기 어려운 문제이다.

**둘째, 대각 SSM 제약이다.** SSD 프레임워크의 효율적 알고리즘은 $A$ 행렬이 대각(diagonal)인 경우에만 적용 가능하다. 일반적인 밀집(dense) 상태 전이 행렬에 대해서는 세미분리 구조가 성립하지 않으며, 따라서 SSD 타일링을 적용할 수 없다. 이는 모델의 표현력에 제약을 줄 수 있으나, 실험적으로는 대각 SSM만으로도 충분한 성능을 달성하는 것으로 나타났다.

**셋째, 학습-추론 모드 전환의 복잡성이다.** SSD의 이중 모드는 학습 시 행렬 곱셈, 추론 시 순환 연산을 각각 별도로 구현해야 함을 의미한다. 이는 엔지니어링 복잡도를 증가시키며, 특히 커스텀 CUDA 커널의 구현과 유지보수에 상당한 노력이 필요하다.

**넷째, 순수 SSM의 성능 상한이다.** 2.7B 규모에서 Mamba-2의 Pile PPL은 6.18로, Transformer++(6.10)에 약간 미치지 못한다. 이는 순수 SSM 구조가 동일 규모에서 Transformer의 표현력을 완전히 대체하지 못함을 시사한다. 이 한계를 인식하여, 후속 연구인 Mamba-3에서는 소수의 어텐션 레이어를 혼합하는 하이브리드 접근법이 채택되었다.

## 관련 모델

Mamba-2는 state-spaces/mamba 저장소에서 Mamba-1과 동일한 인터페이스로 사용할 수 있다. SSD 프레임워크의 이론적 기여는 SSM과 어텐션을 통합하는 장기적 기반으로서 큰 영향을 미칠 것으로 예상된다. 순수 SSM의 in-context retrieval 한계는 여전히 존재하며, 이는 Mamba-3에서 소수의 어텐션 레이어를 추가하는 하이브리드 접근법으로 해결을 시도하고 있다.

## 참고 자료

- 논문: [Transformers are SSMs: Generalized Models and Efficient Algorithms Through Structured State Space Duality](https://arxiv.org/abs/2405.21060)
- 코드: [state-spaces/mamba](https://github.com/state-spaces/mamba)

## 관련 문서

- [[mamba|Mamba: Linear-Time Sequence Modeling with Selective State Spaces]] — 발전 기반
- [[mamba-3|Mamba-3]] — 후속 모델
