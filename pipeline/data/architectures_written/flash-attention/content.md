# FlashAttention: IO-Aware 정확한 어텐션 알고리즘

**Stanford University / HazyResearch** · **2022-06-23** · **오픈소스**

## 개요

FlashAttention은 Tri Dao 등이 2022년 스탠퍼드 HazyResearch에서 제안한 **IO-aware 정확한 어텐션 알고리즘**이다. Transformer 모델의 핵심인 Self-Attention 연산은 시퀀스 길이 N에 대해 O(N²)의 시간과 메모리 복잡도를 가지며, 이는 긴 시퀀스 처리의 주된 병목이었다. 기존의 근사 어텐션(Sparse Attention, Linear Attention 등)은 이 문제를 해결하려 했지만, 정확도 손실이 불가피했다.

FlashAttention은 완전히 다른 접근법을 취한다. **수학적으로 표준 어텐션과 완전히 동일한 결과를 내면서도**, GPU의 메모리 계층 구조(HBM과 SRAM)를 활용한 IO-aware 알고리즘 설계로 HBM 접근 횟수를 O(N²)에서 O(N²d²/M)으로 줄인다(여기서 d는 헤드 차원, M은 SRAM 크기). 결과적으로 표준 구현 대비 **2~4배 빠르고 5~20배 메모리 효율적**이며, 긴 시퀀스 학습의 병목을 획기적으로 해소했다.

![FlashAttention 아키텍처 — GPU HBM-SRAM 메모리 계층을 활용한 IO-aware 타일링 기반 정확한 어텐션](figures/architecture.svg)

*Figure 1: FlashAttention 아키텍처 — Q, K, V 행렬을 블록 단위로 분할하여 SRAM에서 계산하고, 온라인 소프트맥스로 N x N 어텐션 행렬의 HBM 실체화를 방지하는 IO-aware 알고리즘이다.*

FlashAttention의 타일링 전략과 속도 향상 효과를 아래 그림에서 확인할 수 있다.

![FlashAttention 타일링 전략 — HBM과 SRAM 사이의 블록 단위 데이터 이동과 GPT-2에서의 속도 향상](figures/fig_1.png)
*Figure 1: FlashAttention 타일링 전략 — (좌) K, V 블록을 외부 루프(빨간 화살표)로, Q 블록을 내부 루프(파란 화살표)로 순회하여 N x N 어텐션 행렬의 HBM 실체화를 방지한다. (우) GPT-2에서 표준 어텐션 대비 최대 7.6배 속도 향상. (Source: Dao et al., 2022)*

## 기법 상세

### GPU 메모리 계층 구조의 이해

FlashAttention을 이해하려면 먼저 GPU의 메모리 계층을 알아야 한다. NVIDIA A100 GPU를 기준으로:

| 메모리 종류 | 용량 | 대역폭 |
|------------|------|--------|
| SRAM (on-chip) | 20MB (108 SM × 192KB) | ~19TB/s |
| HBM (off-chip) | 40~80GB | ~2TB/s |

SRAM은 HBM보다 약 **10배 빠르지만 용량은 수천 배 작다**. 표준 어텐션 구현은 중간 행렬(S = QK^T, P = softmax(S))을 HBM에 반복적으로 읽고 쓰는데, 이 IO 비용이 실제 연산 시간보다 훨씬 크다. 어텐션 연산은 compute-bound가 아닌 **memory-bound** 연산인 것이다.

### 블록 타일링(Block Tiling)

FlashAttention의 핵심 전략은 Q, K, V 행렬을 SRAM에 들어갈 수 있는 크기의 **블록으로 분할(tiling)**하여 처리하는 것이다.

```
표준 어텐션:
1. S = QK^T ∈ R^{N×N}    → HBM에 저장 (O(N²) 메모리)
2. P = softmax(S)         → HBM에 저장 (O(N²) 메모리)
3. O = PV                 → HBM에 저장

FlashAttention (타일링):
1. Q를 블록 Q₁, Q₂, ... 로 분할
2. K, V를 블록 K₁, K₂, ... 로 분할
3. 각 블록 쌍을 SRAM에 로드하여 처리
4. 중간 행렬 S, P를 HBM에 저장하지 않음
```

외부 루프에서 K, V 블록을 순회하고, 내부 루프에서 Q 블록을 순회하며, 각 반복에서 부분 어텐션 출력을 계산한 뒤 누적한다. 이렇게 하면 N×N 크기의 어텐션 행렬을 HBM에 **절대로 실체화(materialize)하지 않는다**.

### 온라인 소프트맥스(Online Softmax)

타일링의 가장 큰 난제는 소프트맥스 정규화다. 소프트맥스는 전체 행에 대한 글로벌 연산이므로, 블록 단위로 나누어 처리하면 정규화 상수를 알 수 없다. FlashAttention은 **온라인 소프트맥스(Milakov & Gimelshein, 2018)** 기법을 활용하여 이를 해결한다.

```python
# 온라인 소프트맥스 의사코드
m_prev = -inf  # 이전까지의 최대값
l_prev = 0     # 이전까지의 지수합
o_prev = 0     # 이전까지의 출력

for j in range(num_kv_blocks):
    # 현재 블록의 어텐션 스코어
    S_ij = Q_i @ K_j.T / sqrt(d)
    
    # 현재 블록의 최대값과 지수합
    m_curr = max(m_prev, max(S_ij))
    l_curr = l_prev * exp(m_prev - m_curr) + sum(exp(S_ij - m_curr))
    
    # 이전 출력을 새 정규화 상수로 보정 + 현재 블록 기여 추가
    o_curr = o_prev * (l_prev * exp(m_prev - m_curr) / l_curr) \
           + exp(S_ij - m_curr) @ V_j / l_curr
    
    m_prev, l_prev, o_prev = m_curr, l_curr, o_curr
```

이 방법으로 각 블록을 처리할 때마다 정규화 통계(최대값 m, 지수합 l)를 **점진적으로 갱신**하여 최종적으로 정확한 소프트맥스 결과를 얻는다.

### 역전파와 재계산(Recomputation)

순전파에서 중간 어텐션 행렬(S, P)을 저장하지 않았으므로, 역전파 시 이들이 필요하다. FlashAttention은 **재계산(recomputation)** 전략을 사용한다: 역전파 시 Q, K, V와 출력 O, 그리고 소프트맥스 통계(m, l)만을 사용하여 S와 P를 다시 계산한다.

재계산에 의한 추가 FLOP은 있지만, HBM 접근을 크게 줄이므로 **총 wall-clock 시간은 오히려 감소**한다. 이는 현대 GPU에서 연산이 메모리 접근보다 훨씬 빠르기 때문이다. 메모리 복잡도는 O(N²)에서 **O(N)**으로 줄어든다.

HBM 접근 횟수와 블록 크기, 그리고 희소성에 따른 추가 속도 향상 효과를 아래 그래프에서 확인할 수 있다.

![블록 크기에 따른 HBM 접근 횟수와 실행 시간, 희소 FlashAttention의 속도 향상](figures/fig_2.png)
*Figure 2: (좌) 블록 크기 증가 시 HBM 접근 횟수가 줄어들며 실행 시간이 단축된다. (우) Block-Sparse FlashAttention은 희소성 비율에 비례하여 Dense FlashAttention보다 추가적인 속도 향상을 달성한다. (Source: Dao et al., 2022)*

## 핵심 혁신

| 혁신 | 설명 | 효과 |
|------|------|------|
| IO-Aware 설계 | HBM/SRAM 계층을 고려한 알고리즘 | HBM 접근 O(N²) → O(N²d²/M) |
| 블록 타일링 | Q, K, V를 SRAM 크기 블록으로 분할 | 중간 행렬 미실체화 |
| 온라인 소프트맥스 | 점진적 정규화 통계 갱신 | 블록 단위 정확한 소프트맥스 |
| 재계산 | 역전파 시 중간값 재계산 | 메모리 O(N²) → O(N) |
| 커스텀 CUDA 커널 | 하나의 퓨즈드 커널로 구현 | 커널 런칭 오버헤드 제거 |

## 벤치마크/성능

### 속도 비교

| 모델/설정 | 표준 어텐션 | FlashAttention | 속도 향상 |
|-----------|-----------|----------------|----------|
| GPT-2 (seq 1K) | 기준 | 3배 빠름 | 3.0× |
| GPT-2 (seq 4K) | 기준 | 4.2배 빠름 | 4.2× |
| BERT-large (seq 512) | 기준 | 2.4배 빠름 | 2.4× |
| Long Range Arena | 기준 | 2.8배 빠름 | 2.8× |

### 메모리 사용량

시퀀스 길이에 따른 메모리 스케일링:

| 시퀀스 길이 | 표준 어텐션 | FlashAttention |
|------------|-----------|----------------|
| 1K | 기준 | 5× 절감 |
| 4K | 기준 | 12× 절감 |
| 16K | OOM | 정상 동작 |

A100 GPU에서 이론 최대 TFLOPS의 **70~75%**를 달성하며, 이는 메모리 효율적 어텐션 구현체 중 가장 높은 하드웨어 활용률이다.

시퀀스 길이에 따른 실행 시간과 메모리 사용량 비교는 아래 그래프에서 확인할 수 있다.

![시퀀스 길이별 어텐션 실행 시간과 메모리 사용량 비교](figures/fig_5.png)
*Figure 3: (좌) 시퀀스 길이별 순전파+역전파 실행 시간 비교 — FlashAttention이 표준 어텐션과 PyTorch 구현 대비 일관되게 빠르다. (우) 메모리 사용량 비교 — FlashAttention은 시퀀스 길이 증가에 따라 선형적으로만 메모리가 증가한다. (Source: Dao et al., 2022)*

다양한 시퀀스 길이에서의 A100 GPU 속도 향상 배율은 다음과 같다.

![A100 GPU에서 시퀀스 길이별 FlashAttention 속도 향상 — 최대 4배 이상](figures/fig_7.jpg)
*Figure 4: A100 GPU에서의 FlashAttention 속도 향상 — Dropout+Masking 포함 시 최대 4.2배, 순수 어텐션에서도 2배 이상의 속도 향상을 시퀀스 길이 128~4096 범위에서 달성한다. (Source: Dao et al., 2022)*

## 관련 기법 비교

| 기법 | 정확도 | 속도 | 메모리 | IO-Aware |
|------|--------|------|--------|----------|
| 표준 어텐션 | 정확 | 기준 | O(N²) | X |
| Sparse Attention | 근사 | 빠름 | O(N√N) | X |
| Linear Attention | 근사 | 빠름 | O(N) | X |
| **FlashAttention** | **정확** | **2~4× 빠름** | **O(N)** | **O** |
| xFormers Memory Efficient | 정확 | 2× 빠름 | O(N) | 부분 |

FlashAttention의 가장 큰 차별점은 **정확도 손실 없이** 속도와 메모리를 모두 개선한다는 점이다.

## 실무 활용

### PyTorch 2.0+ 통합 (권장)

PyTorch 2.0 이후 `F.scaled_dot_product_attention`에 FlashAttention이 백엔드로 통합되어, 별도 설치 없이 바로 사용할 수 있다.

```python
import torch
import torch.nn.functional as F

# PyTorch 2.0+ SDPA (자동으로 FlashAttention 백엔드 선택)
query = torch.randn(batch, num_heads, seq_len, head_dim, 
                    device="cuda", dtype=torch.float16)
key = torch.randn_like(query)
value = torch.randn_like(query)

# FlashAttention이 자동 선택됨 (조건 충족 시)
with torch.backends.cuda.sdp_kernel(
    enable_flash=True,      # FlashAttention 활성화
    enable_math=False,       # 표준 구현 비활성화
    enable_mem_efficient=False
):
    output = F.scaled_dot_product_attention(
        query, key, value,
        attn_mask=None,
        dropout_p=0.0,
        is_causal=True  # causal mask 지원
    )
```

### flash-attn 라이브러리 직접 사용

```python
# pip install flash-attn --no-build-isolation
from flash_attn import flash_attn_func

# shape: (batch, seqlen, nheads, headdim)
q = torch.randn(2, 1024, 12, 64, device="cuda", dtype=torch.float16)
k = torch.randn(2, 1024, 12, 64, device="cuda", dtype=torch.float16)
v = torch.randn(2, 1024, 12, 64, device="cuda", dtype=torch.float16)

# FlashAttention 직접 호출
output = flash_attn_func(q, k, v, dropout_p=0.0, causal=True)
```

### HuggingFace Transformers 통합

```python
from transformers import AutoModelForCausalLM

# attn_implementation="flash_attention_2" 로 간단하게 활성화
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    torch_dtype=torch.float16,
    attn_implementation="flash_attention_2",
    device_map="auto"
)
```

## 한계 및 전망

### 현재 한계
- **CUDA 전용**: NVIDIA GPU에서만 동작하며, AMD나 Intel GPU 지원은 제한적이다
- **헤드 차원 제약**: 초기 버전에서는 head_dim ≤ 128만 지원 (FlashAttention-2에서 256까지 확장)
- **커스텀 마스크 제한**: 임의의 어텐션 마스크 패턴 지원이 제한적이다
- **컴파일 복잡성**: CUDA 커스텀 커널 빌드에 시간이 소요되고 GPU 아키텍처별 호환성 이슈가 존재한다

### 발전 방향
FlashAttention은 FlashAttention-2(2023)에서 워프 병렬화와 GQA 지원이 추가되어 2배 더 빨라졌고, FlashAttention-3(2024)에서는 H100의 TMA와 FP8 텐서 코어를 활용한다. 현재 PyTorch, vLLM, TGI, Megatron-LM 등 거의 모든 주요 LLM 프레임워크가 FlashAttention을 **기본 어텐션 구현**으로 채택하고 있으며, 현대 LLM 학습과 추론의 실질적 표준으로 자리 잡았다.

## 참고 자료

- [논문](https://arxiv.org/abs/2205.14135)
- [코드](https://github.com/Dao-AILab/flash-attention)

## 관련 문서

- [[flash-attention-2|FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning]] — 후속 모델
- [[falcon|Falcon]] — 적용 모델
