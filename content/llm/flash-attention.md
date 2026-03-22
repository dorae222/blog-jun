---
title: "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness"
slug: "flash-attention"
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.395713+00:00"
architecture_entry: "flash-attention"
---

## 개요

트랜스포머의 셀프 어텐션은 시퀀스 길이 $N$에 대해 $O(N^2)$의 시간 및 공간 복잡도를 가집니다. 이는 긴 시퀀스 처리를 어렵게 만드는 근본적 제약이지만, FlashAttention은 알고리즘의 계산 복잡도를 바꾸지 않고도 GPU 메모리 계층 구조를 활용하여 실질적인 속도와 메모리 효율을 크게 향상시킵니다.

핵심 통찰은 GPU의 연산 속도가 메모리 대역폭보다 훨씬 빠르기 때문에, 실제 병목은 계산량이 아니라 HBM(High Bandwidth Memory)과 SRAM(온칩 캐시) 간의 데이터 이동량이라는 점입니다.

## 배경 및 문제

### GPU 메모리 계층

A100 GPU 기준:
- **SRAM (온칩 캐시)**: 192KB per SM, 대역폭 ~19 TB/s
- **HBM (GPU DRAM)**: 40-80GB, 대역폭 ~2 TB/s
- **DRAM (호스트 메모리)**: 수백 GB, 대역폭 ~12.8 GB/s

SRAM은 HBM보다 10배 이상 빠르지만 용량이 극히 작습니다. 표준 어텐션은 $N \times N$ 크기의 어텐션 행렬을 HBM에 저장하고 반복적으로 읽어야 하므로, 이 HBM 접근이 주요 병목이 됩니다.

### 표준 어텐션의 IO 비용

시퀀스 길이 $N$, 헤드 차원 $d$일 때 표준 어텐션의 HBM 접근량:

$$\text{IO}_{\text{standard}} = O(Nd + N^2)$$

$N$이 커질수록 $N^2$ 항이 지배적이 됩니다. GPT-2(1024 토큰) 수준에서도 어텐션 연산의 75% 이상이 메모리 접근 대기에 소모됩니다.

## 핵심 아이디어

### 타일링 (Tiling)

FlashAttention은 $Q$, $K$, $V$ 행렬을 블록(타일)으로 나누어 SRAM에 순차적으로 로드하고, 어텐션 결과를 점진적으로 누적합니다. 핵심은 온라인 소프트맥스(online softmax) 트릭으로, 전체 어텐션 행렬을 구체화하지 않고도 정확한 소프트맥스 값을 타일 단위로 계산할 수 있습니다.

온라인 소프트맥스는 수치 안정성을 위해 최대값을 빼는 방식으로 작동합니다:

$$\text{softmax}(x_i) = \frac{e^{x_i - m}}{\sum_j e^{x_j - m}}, \quad m = \max_j x_j$$

타일을 순차적으로 처리할 때 이전 타일에서 계산한 최대값 $m$과 지수합 $\ell$을 업데이트하면서 최종적으로 정확한 결과를 얻습니다:

$$m^{\text{new}} = \max(m^{\text{old}}, m_j), \quad \ell^{\text{new}} = e^{m^{\text{old}} - m^{\text{new}}} \ell^{\text{old}} + e^{m_j - m^{\text{new}}} \ell_j$$

### FlashAttention의 IO 비용

$$\text{IO}_{\text{flash}} = O\left(\frac{N^2 d}{M}\right)$$

여기서 $M$은 SRAM 크기입니다. $d \ll M \ll N^2$인 일반적인 조건에서 표준 어텐션보다 IO 비용이 크게 줄어듭니다.

## 방법론

### 순전파 (Forward Pass)

1. $Q$, $K$, $V$를 블록 크기 $B_c = \lceil M / 4d \rceil$로 분할
2. 각 $Q$ 블록에 대해 모든 $K$, $V$ 블록을 순회
3. SRAM 내에서 부분 어텐션 스코어 계산, 온라인 소프트맥스로 누적
4. 최종 출력만 HBM에 기록

HBM 접근 횟수: 블록 수 × 블록 크기 = $O(N^2 d / M)$

### 역전파 (Backward Pass)

일반적인 어텐션 역전파는 $N \times N$ 어텐션 행렬을 저장해야 합니다. FlashAttention은 역전파 시 필요한 어텐션 행렬을 저장하지 않고, 순전파에서 기록해 둔 소프트맥스 통계값 ($m$, $\ell$)만 이용하여 역전파 중 어텐션 행렬을 **재계산(recomputation)**합니다.

- 추가 메모리 비용: $O(N)$ (소프트맥스 통계값 저장)
- 추가 계산 비용: 어텐션 행렬 재계산 1회
- 절약: HBM에 $O(N^2)$ 어텐션 행렬 저장 불필요

이 트레이드오프로 메모리 복잡도가 $O(N^2) \to O(N)$으로 감소합니다.

### 블록 희소 어텐션

FlashAttention은 사전 정의된 희소 마스크와 결합하여 블록 희소 어텐션으로도 확장 가능합니다. 이 경우 IO 비용이 추가로 감소합니다.

## 실험 결과

### 학습 속도

| 모델 | 시퀀스 길이 | 표준 어텐션 | FlashAttention | 속도 향상 |
|------|-----------|-----------|--------------|--------|
| BERT-large | 512 | 기준 | 1.0x | - |
| GPT-2 | 1024 | 기준 | 2.4x | 2.4x |
| GPT-2 | 4096 | OOM | 가능 | - |
| Long-range Arena | 1024~16384 | 기준 | 2~4x | 2~4x |

### 메모리 복잡도

| 어텐션 종류 | 메모리 | 비고 |
|-----------|-------|----|
| 표준 어텐션 | $O(N^2)$ | 어텐션 행렬 저장 |
| FlashAttention | $O(N)$ | 통계값만 저장 |

### 긴 시퀀스 지원

A100 80GB GPU에서 FlashAttention은 최대 64K 토큰까지 처리 가능하며, 표준 어텐션의 OOM 한계(16K 전후)를 크게 넘어섭니다.

## 의의 및 한계

### 의의

- **정확성**: 근사 없이 표준 어텐션과 수치적으로 동일한 결과 보장
- **범용성**: 인과적(causal) 마스킹, 드롭아웃 등 표준 어텐션 기능 모두 지원
- **실용성**: PyTorch, JAX, Triton 등 다양한 구현이 공개되어 즉시 적용 가능
- **긴 컨텍스트**: 이전에 불가능했던 긴 시퀀스 학습 가능 → GPT-4, Claude 등 긴 컨텍스트 모델의 기반 기술
- **후속 연구**: FlashAttention-2, FlashAttention-3, PagedAttention 등 후속 연구의 토대

### 한계

- Triton/CUDA 커널 수준의 하드웨어 특화 구현이 필요하여 다른 하드웨어(TPU, AMD GPU 등)로의 이식이 복잡
- 타일 크기가 SRAM 용량에 맞춰 조정되어야 하므로 GPU 아키텍처별 최적화가 필요
- 역전파에서 재계산으로 인한 추가 연산 비용이 일부 발생

## 코드 예제

### Flash Attention 핵심 알고리즘 (Triton)

```python
import torch
import triton
import triton.language as tl

# Flash Attention의 핵심: 블록 타일링으로 SRAM 내에서 처리
@triton.jit
def _flash_attn_fwd_kernel(
    Q, K, V, Out,
    stride_qb, stride_qh, stride_qm, stride_qd,
    stride_kb, stride_kh, stride_kn, stride_kd,
    stride_vb, stride_vh, stride_vn, stride_vd,
    stride_ob, stride_oh, stride_om, stride_od,
    Z, H, N_CTX, BLOCK_M: tl.constexpr, BLOCK_N: tl.constexpr, BLOCK_DMODEL: tl.constexpr,
):
    """Flash Attention Forward Kernel (단순화 버전).
    핵심 아이디어: Q 블록에 대해 K,V 블록을 순회하며 온라인 소프트맥스 계산.
    """
    start_m = tl.program_id(0)
    off_hz = tl.program_id(1)
    off_b = off_hz // H
    off_h = off_hz % H

    # 포인터 계산
    Q_ptr = Q + off_b * stride_qb + off_h * stride_qh + start_m * BLOCK_M * stride_qm
    K_ptr = K + off_b * stride_kb + off_h * stride_kh
    V_ptr = V + off_b * stride_vb + off_h * stride_vh

    offs_m = tl.arange(0, BLOCK_M) + start_m * BLOCK_M
    offs_d = tl.arange(0, BLOCK_DMODEL)

    # Q 블록 로드
    q = tl.load(Q_ptr + offs_m[:, None] * stride_qm + offs_d[None, :] * stride_qd)

    # 온라인 소프트맥스 상태 초기화
    m_i = tl.full([BLOCK_M], float('-inf'), dtype=tl.float32)  # running max
    l_i = tl.zeros([BLOCK_M], dtype=tl.float32)               # running sum
    acc = tl.zeros([BLOCK_M, BLOCK_DMODEL], dtype=tl.float32) # 누적 출력

    # K,V 블록 순회 (HBM → SRAM 로딩 최소화)
    for start_n in range(0, N_CTX, BLOCK_N):
        offs_n = tl.arange(0, BLOCK_N) + start_n
        k = tl.load(K_ptr + offs_n[None, :] * stride_kn + offs_d[:, None] * stride_kd)
        v = tl.load(V_ptr + offs_n[:, None] * stride_vn + offs_d[None, :] * stride_vd)

        # 어텐션 스코어 계산 (SRAM 내에서!)
        qk = tl.dot(q, k)  # (BLOCK_M, BLOCK_N)

        # 온라인 소프트맥스 업데이트
        m_ij = tl.max(qk, 1)           # 새 블록의 최댓값
        p = tl.exp(qk - m_ij[:, None]) # 정규화된 어텐션
        l_ij = tl.sum(p, 1)            # 합계

        # 이전 상태와 합산 (수치 안정성 유지)
        m_i_new = tl.maximum(m_i, m_ij)
        alpha = tl.exp(m_i - m_i_new)
        beta = tl.exp(m_ij - m_i_new)
        l_i_new = alpha * l_i + beta * l_ij

        # 누적 출력 업데이트
        acc = acc * (alpha[:, None]) + tl.dot(p.to(tl.float16), v) * beta[:, None]
        m_i = m_i_new
        l_i = l_i_new

    # 최종 정규화 및 출력 저장
    acc = acc / l_i[:, None]
    Out_ptr = Out + off_b * stride_ob + off_h * stride_oh + start_m * BLOCK_M * stride_om
    tl.store(Out_ptr + offs_m[:, None] * stride_om + offs_d[None, :] * stride_od, acc)

# PyTorch에서 Flash Attention 사용 (torch.nn.functional)
def flash_attention_pytorch(Q, K, V):
    """PyTorch 2.0+ 내장 Flash Attention 사용."""
    # F.scaled_dot_product_attention이 내부적으로 Flash Attention 사용
    import torch.nn.functional as F
    return F.scaled_dot_product_attention(Q, K, V, is_causal=True)

# 메모리 사용량 비교
seq_len = 4096
head_dim = 64
print(f"표준 Attention S 행렬: {seq_len}×{seq_len} = {seq_len**2 * 4 / 1024**2:.1f} MB (fp32)")
print(f"Flash Attention: O(N) 메모리 — S 행렬 저장 불필요")
print(f"seq=4096, Flash Attention 메모리 절감: ~{seq_len**2 * 4 / 1024**2:.0f} MB")
```