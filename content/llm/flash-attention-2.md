---
title: "FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning"
slug: "flash-attention-2"
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.397726+00:00"
architecture_entry: "flash-attention-2"
---

## 개요

FlashAttention-1이 IO 인식 타일링으로 혁신적인 메모리 효율을 달성했지만, GPU의 이론적 최대 처리량 대비 실제 달성률은 25~35% 수준에 머물렀습니다. FlashAttention-2는 GPU 하드웨어의 병렬화 특성을 더 깊이 분석하여 세 가지 핵심 개선을 통해 A100 기준 50~73% 처리량 달성률을 실현합니다.

## 배경 및 문제

### FlashAttention-1의 한계

FlashAttention-1의 주요 병목:

1. **비행렬곱 연산 과다**: 소프트맥스 정규화, 스케일링, 마스킹 등 비행렬곱 연산이 전체 실행 시간의 상당 부분을 차지. GPU의 행렬곱 유닛(Tensor Core)은 비행렬곱 연산보다 훨씬 높은 처리량을 가지므로, 비행렬곱 연산이 병목이 됨
2. **시퀀스 차원 병렬화 부재**: FlashAttention-1은 배치와 헤드 차원으로만 병렬화하여 배치 크기가 작거나 헤드 수가 적을 때 GPU를 충분히 활용하지 못함
3. **워프 간 비효율적 작업 분배**: 같은 SM(Streaming Multiprocessor) 내 워프들 사이에서 불필요한 동기화와 통신이 발생

### 행렬곱 vs 비행렬곱 처리량

A100 GPU 기준:
- **행렬곱(FP16/BF16)**: 312 TFLOPS
- **비행렬곱 연산**: ~20 TFLOPS

비행렬곱 연산이 전체의 1%만 차지해도 실질적 처리량을 크게 저해할 수 있습니다.

## 핵심 아이디어

### 개선 1: 비행렬곱 FLOPs 감소

FlashAttention-1의 루프 구조를 재구성하여 스케일링과 정규화 연산을 최소화합니다. 구체적으로:

- 로우스케일(rowscale) 연산의 수를 줄이기 위해 내부 루프에서 $Q$ 블록을 고정하고 $K$, $V$ 블록을 순회하는 방식으로 루프 순서 변경
- 누적값 재스케일링 횟수를 FlashAttention-1 대비 절반으로 감소

결과적으로 비행렬곱 FLOPs가 약 2배 감소하여 Tensor Core 활용률이 높아집니다.

### 개선 2: 시퀀스 길이 차원 병렬화

FlashAttention-1은 배치 크기 $B$와 헤드 수 $H$만으로 병렬화합니다. SM 수가 108개인 A100에서 $B \times H < 108$이면 일부 SM이 유휴 상태가 됩니다.

FlashAttention-2는 시퀀스 길이 $N$을 추가 병렬화 차원으로 활용합니다:

$$\text{병렬 작업 수} = B \times H \times \lceil N / B_c \rceil$$

긴 시퀀스 추론 시(배치=1, 헤드=소수) 특히 효과적이며, 멀티 헤드 GQA 환경에서도 유리합니다.

**주의**: 인과적(causal) 어텐션의 경우 타일마다 처리하는 유효 토큰 수가 달라 단순 병렬화는 부하 불균형을 유발합니다. FlashAttention-2는 이를 위해 인과적 마스킹에서의 작업 분배도 최적화합니다.

### 개선 3: 워프 간 작업 분배 개선

하나의 어텐션 블록 계산을 SM 내 워프들에게 효율적으로 분배합니다.

**FlashAttention-1 방식**: $K$, $V$ 블록을 워프에 분배 → 워프가 부분 결과를 공유 메모리를 통해 합산 → 동기화 오버헤드 발생

**FlashAttention-2 방식**: $Q$ 블록을 워프에 분배 → 각 워프가 독립적으로 결과를 누적 → 공유 메모리 통신 최소화

이를 통해 워프 간 동기화로 인한 스톨(stall)이 크게 감소합니다.

## 방법론

### 알고리즘 개요

순전파에서의 핵심 루프 구조 변경:

```
# FlashAttention-2 순전파 (의사 코드)
for each Q 블록 q_i:          # 외부 루프: SM에 병렬 분배
    O_i = 0, l_i = 0, m_i = -∞
    for each K,V 블록 k_j, v_j:  # 내부 루프: 순차 처리
        S_ij = q_i @ k_j^T / √d
        m_i_new = max(m_i, rowmax(S_ij))
        P_ij = exp(S_ij - m_i_new)
        l_i = exp(m_i - m_i_new) * l_i + rowsum(P_ij)
        O_i = exp(m_i - m_i_new) * O_i + P_ij @ v_j
        m_i = m_i_new
    O_i = O_i / l_i  # 최종 정규화 1회
```

정규화를 루프 밖으로 이동하여 재스케일링 연산을 최소화합니다.

### 인과적 마스킹 최적화

인과적 어텐션에서 하삼각(lower-triangular) 블록은 완전 계산, 대각선 블록은 마스킹 적용이 필요합니다. FlashAttention-2는 완전 마스킹된 블록을 건너뛰어 실질적 연산량을 절반 수준으로 줄입니다.

## 실험 결과

### 처리량 비교 (A100 80GB, 헤드 차원 128)

| 시퀀스 길이 | PyTorch Attention | FlashAttention-1 | FlashAttention-2 |
|-----------|-----------------|-----------------|------------------|
| 512 | ~55 TFLOPS | ~115 TFLOPS | ~180 TFLOPS |
| 1024 | ~45 TFLOPS | ~130 TFLOPS | ~195 TFLOPS |
| 2048 | ~38 TFLOPS | ~140 TFLOPS | ~205 TFLOPS |
| 4096 | ~30 TFLOPS | ~145 TFLOPS | ~215 TFLOPS |

A100 이론 최대(312 TFLOPS 대비): FlashAttention-2는 약 50~73% 달성

### FlashAttention-1 대비 속도 향상

| 설정 | 속도 향상 |
|------|-------|
| 순전파 (causal=False) | ~2.0x |
| 순전파 (causal=True) | ~2.0x |
| 순역전파 (causal=False) | ~1.7x |
| 순역전파 (causal=True) | ~2.0x |

### GPT 학습 처리량 (8xA100)

| 모델 | 기존 구현 | FlashAttention-2 |
|------|---------|------------------|
| GPT-3 175B | 143 TFLOPS/GPU | 190 TFLOPS/GPU |

## 의의 및 한계

### 의의

- **사실상 표준**: 거의 모든 최신 LLM 학습 및 추론 프레임워크(vLLM, TGI, Megatron-LM, nanoGPT 등)에 채택
- **멀티 헤드 GQA 지원**: GQA와 결합하여 긴 시퀀스 추론에서 시너지 효과
- **확장성**: 시퀀스 길이 병렬화로 소규모 배치에서도 높은 GPU 활용률 유지
- **FlashAttention-3**: H100의 새 하드웨어 특성(TMA, 비동기 실행)을 활용하는 후속 연구의 기반

### 한계

- A100/H100 등 NVIDIA GPU에 최적화되어 있으며 다른 하드웨어에서는 별도 구현 필요
- 매우 짧은 시퀀스(256 토큰 이하)에서는 오버헤드 대비 이익이 줄어듦
- Triton/CUDA 커스텀 커널로 구현되어 있어 커널 수정 및 디버깅이 어려움

## 코드 예제

### Flash Attention 2 개선점 실습 (PyTorch)

```python
import torch
import torch.nn.functional as F
import time

def benchmark_attention(batch, heads, seq_len, head_dim, device='cuda', num_runs=10):
    """표준 Attention vs Flash Attention 2 속도/메모리 비교."""
    Q = torch.randn(batch, heads, seq_len, head_dim, device=device, dtype=torch.float16)
    K = torch.randn(batch, heads, seq_len, head_dim, device=device, dtype=torch.float16)
    V = torch.randn(batch, heads, seq_len, head_dim, device=device, dtype=torch.float16)

    # 방법 1: 표준 Attention (O(N^2) 메모리)
    def standard_attention(Q, K, V):
        import math
        scale = math.sqrt(head_dim)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / scale  # (B,H,N,N) 행렬 생성!
        mask = torch.tril(torch.ones(seq_len, seq_len, device=device))
        scores = scores.masked_fill(mask == 0, float('-inf'))
        attn = F.softmax(scores.float(), dim=-1).half()
        return torch.matmul(attn, V)

    # 방법 2: Flash Attention 2 (torch.nn.functional.scaled_dot_product_attention)
    def flash_attention2(Q, K, V):
        # FA2가 내부적으로 사용됨 (CUDA 가속)
        return F.scaled_dot_product_attention(Q, K, V, is_causal=True)

    if device == 'cuda':
        torch.cuda.reset_peak_memory_stats()
        # Standard
        torch.cuda.synchronize()
        t0 = time.time()
        for _ in range(num_runs):
            out_std = standard_attention(Q, K, V)
        torch.cuda.synchronize()
        std_time = (time.time() - t0) / num_runs * 1000
        std_mem = torch.cuda.max_memory_allocated() / 1024**3

        torch.cuda.reset_peak_memory_stats()
        # Flash Attention 2
        t0 = time.time()
        for _ in range(num_runs):
            out_fa2 = flash_attention2(Q, K, V)
        torch.cuda.synchronize()
        fa2_time = (time.time() - t0) / num_runs * 1000
        fa2_mem = torch.cuda.max_memory_allocated() / 1024**3

        print(f"Standard Attention: {std_time:.2f}ms, {std_mem:.3f}GB")
        print(f"Flash Attention 2:  {fa2_time:.2f}ms, {fa2_mem:.3f}GB")
        print(f"속도 향상: {std_time/fa2_time:.1f}x, 메모리 절감: {std_mem/fa2_mem:.1f}x")
    else:
        print("CUDA 없음: CPU 실행 (실제 FA2는 GPU 전용)")
        out_fa2 = flash_attention2(Q.cpu(), K.cpu(), V.cpu())
        print(f"출력 shape: {out_fa2.shape}")

# FA2의 GQA 지원 (Mistral, LLaMA-2-70B 등)
def fa2_with_gqa(Q, K, V):
    """GQA: Q 헤드 > KV 헤드일 때 FA2가 자동으로 처리."""
    # Q: (B, num_heads, T, D), K/V: (B, num_kv_heads, T, D)
    # FA2는 내부적으로 KV를 확장 없이 브로드캐스팅으로 처리
    return F.scaled_dot_product_attention(Q, K, V, is_causal=True)
    # FA1은 GQA를 직접 지원하지 않아 수동 확장 필요

# 사용 예시 (CUDA 없으면 CPU로 대체)
device = 'cuda' if torch.cuda.is_available() else 'cpu'
benchmark_attention(batch=2, heads=8, seq_len=1024, head_dim=64, device=device)
```