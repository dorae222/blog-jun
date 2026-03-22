---
title: Mistral 7B
slug: "mistral-7b"
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.492629+00:00"
architecture_entry: "mistral-7b"
---

## 개요

Mistral 7B는 Mistral AI가 2023년 10월 발표한 7B 파라미터 언어 모델이다. 핵심 혁신은 **SWA (Sliding Window Attention)**과 **롤링 버퍼 KV 캐시(Rolling Buffer KV Cache)**로, 긴 시퀀스를 선형 메모리로 처리할 수 있다. 이에 더해 **GQA (Grouped Query Attention)**을 결합하여 추론 속도를 크게 향상시켰다.

결과적으로 Mistral 7B는 대부분의 평가 벤치마크에서 Llama 2 13B를 능가하는 성능을 7B라는 작은 크기에서 달성했다. 효율적인 어텐션 메커니즘 덕분에 실제 배포 환경에서의 처리량(throughput)도 뛰어나다.

## 배경 및 문제

### 표준 어텐션의 문제

Transformer의 표준 Self-Attention은 시퀀스 길이 $n$에 대해 $O(n^2)$의 시간 및 메모리 복잡도를 가진다. KV 캐시를 사용하는 자기회귀 생성에서 모든 이전 토큰의 Key-Value를 저장해야 하므로, 긴 시퀀스에서 메모리 소비가 폭발적으로 증가한다.

### 작은 모델의 성능 한계

이전까지 7B 규모 모델은 13B 이상 모델에 비해 성능이 뚜렷하게 낮았다. 아키텍처 혁신을 통해 이 격차를 좁힐 수 있는지가 과제였다.

## 핵심 아이디어

### 슬라이딩 윈도우 어텐션 (SWA)

SWA는 각 토큰이 전체 시퀀스가 아닌 **최근 $W$개의 토큰**에만 어텐션을 수행하도록 제한한다.

$$\text{Attention}(q_i, K_{i-W:i}, V_{i-W:i}) = \text{softmax}\left(\frac{q_i K_{i-W:i}^\top}{\sqrt{d_k}}\right) V_{i-W:i}$$

Mistral 7B에서 $W = 4096$을 사용한다. 단일 레이어에서는 $W$ 범위만 보지만, 레이어를 거듭하면서 정보가 **이론적으로 $W \times \text{layers}$까지** 전파된다. 32개 레이어에서 $W=4096$이면 최대 131,072 토큰의 정보에 접근할 수 있다.

### 롤링 버퍼 KV 캐시

표준 KV 캐시는 모든 이전 토큰을 저장하지만, SWA에서는 최근 $W$개만 필요하다. **롤링 버퍼(Rolling Buffer)**는 크기 $W$의 고정 메모리에 위치 인덱스를 순환 방식으로 덮어쓴다.

$$\text{cache}[i \% W] = (k_i, v_i)$$

이를 통해 시퀀스 길이에 무관하게 **KV 캐시 메모리가 일정**하게 유지된다. 8192 토큰 시퀀스에서 표준 캐시 대비 메모리를 8배 절감한다.

### 프리필 청킹 (Chunked Prefill)

Prompt를 한 번에 처리하는 대신 크기 $W$의 청크로 나누어 처리한다. 각 청크는 자신의 토큰과 슬라이딩 윈도우에 있는 이전 청크 토큰에 어텐션한다. 이를 통해 메모리 사용량을 줄이고 GPU 활용률을 높인다.

### Grouped Query Attention (GQA)

SWA와 함께 GQA를 적용한다. Mistral 7B는 32개의 쿼리 헤드를 8개의 KV 헤드 그룹으로 나눈다. 이는 KV 캐시 크기를 추가로 줄이고 추론 속도를 향상시킨다.

## 방법론

### 모델 구성

| 항목 | 값 |
|------|----|
| 파라미터 수 | 7.3B |
| 레이어 수 | 32 |
| 쿼리 헤드 수 | 32 |
| KV 헤드 수 | 8 (GQA) |
| 히든 차원 | 4096 |
| FFN 차원 | 14336 |
| 슬라이딩 윈도우 | 4096 |
| 어휘 크기 | 32000 |
| 활성화 함수 | SwiGLU |
| Positional Embedding | RoPE |
| 정규화 | RMSNorm |

### 파인튜닝 변형

- **Mistral 7B Instruct**: 공개 데이터셋으로 지도 파인튜닝된 명령 따르기 버전

## 실험 결과

### 성능 비교 (다양한 벤치마크)

| 모델 | MMLU | HellaSwag | WinoGrande | ARC-e | ARC-c | MBPP |
|------|------|-----------|------------|-------|-------|------|
| Llama 2-7B | 45.3 | 77.2 | 69.2 | 76.1 | 46.2 | 20.8 |
| Llama 2-13B | 54.8 | 81.9 | 72.0 | 79.4 | 48.8 | 30.2 |
| Llama 1-34B | 55.8 | 82.6 | 76.0 | 79.0 | 50.9 | 37.4 |
| **Mistral 7B** | **60.1** | **81.3** | **75.3** | **80.0** | **55.5** | **40.2** |

Mistral 7B는 MMLU에서 Llama 2 13B를 5.3점 차이로 능가하며, 코드(MBPP)에서는 Llama 1 34B보다 높다.

### 추론 효율

슬라이딩 윈도우 어텐션과 롤링 버퍼 덕분에:
- **4096 토큰 이상 시퀀스에서 표준 어텐션 대비 최대 2배 빠른 추론**
- KV 캐시 메모리 사용량이 시퀀스 길이에 무관하게 일정

### Mistral 7B Instruct 성능

| 비교 대상 | Mistral 7B Instruct 결과 |
|---------|------------------------|
| Llama 2 13B Chat | 대부분 벤치마크에서 우위 |
| Llama 1 34B | 코드/추론에서 동등 이상 |

## 의의 및 한계

### 의의

- **SWA 실용화**: 슬라이딩 윈도우 어텐션을 대형 모델에 성공적으로 적용
- **소형 모델의 성능 한계 돌파**: 7B 모델이 13B를 능가하는 새 기준 수립
- **효율성과 성능의 균형**: 실제 배포 환경에서 뛰어난 처리량 제공
- **Mixtral 기반 마련**: 이후 MoE 기반 Mixtral 8x7B로 발전

### 한계

- **긴 범위 의존성**: 이론적으로 긴 컨텍스트를 지원하지만, SWA로 인해 매우 먼 토큰 간 의존성이 약화될 수 있음
- **정렬 부족**: Mistral 7B 베이스는 SFT만 적용되어 RLHF 기반 모델 대비 안전성 정렬이 제한적
- **학습 데이터 비공개**: 사전학습 데이터 세부 사항이 공개되지 않음

Mistral 7B는 효율적인 어텐션 메커니즘을 통해 소형 LLM의 성능 한계를 새로 정의했으며, 이후 Mixtral, Mistral NeMo 등으로 이어지는 Mistral AI 모델 라인업의 출발점이 되었다.

## 코드 예제

### Sliding Window Attention (SWA) 구현 (PyTorch)

```python
import torch
import torch.nn.functional as F
import math

def sliding_window_attention(Q, K, V, window_size=4096):
    """Sliding Window Attention (Mistral-7B 방식).
    각 토큰은 이전 window_size개의 토큰만 참조.
    긴 시퀀스에서 O(n*w) 복잡도로 O(n^2) 대비 효율적.
    Args:
        Q, K, V: (batch, heads, seq_len, head_dim)
        window_size: 각 토큰이 볼 수 있는 이전 토큰 수
    """
    B, H, T, D = Q.shape
    scale = math.sqrt(D)
    output = torch.zeros_like(Q)

    for t in range(T):
        # 각 위치에서 [t-window_size, t] 범위만 참조
        start = max(0, t - window_size + 1)
        k_window = K[:, :, start:t+1, :]   # (B, H, w, D)
        v_window = V[:, :, start:t+1, :]
        q_t = Q[:, :, t:t+1, :]            # (B, H, 1, D)

        scores = torch.matmul(q_t, k_window.transpose(-2, -1)) / scale
        attn = F.softmax(scores, dim=-1)
        output[:, :, t:t+1, :] = torch.matmul(attn, v_window)

    return output

# Rolling Buffer KV Cache: 실제 Mistral 구현에서 O(w) 메모리 사용
class RollingBufferKVCache:
    """윈도우 크기만큼만 KV 캐시 유지."""
    def __init__(self, window_size, num_heads, head_dim):
        self.window_size = window_size
        self.cache_k = torch.zeros(1, num_heads, window_size, head_dim)
        self.cache_v = torch.zeros(1, num_heads, window_size, head_dim)
        self.pos = 0

    def update(self, k, v):
        """새 KV를 Rolling Buffer에 추가 (오래된 것은 덮어쓰기)."""
        idx = self.pos % self.window_size  # 원형 버퍼 인덱스
        self.cache_k[:, :, idx:idx+1, :] = k
        self.cache_v[:, :, idx:idx+1, :] = v
        self.pos += 1
        # 현재까지 채워진 윈도우 반환
        if self.pos < self.window_size:
            return self.cache_k[:, :, :self.pos, :], self.cache_v[:, :, :self.pos, :]
        return self.cache_k, self.cache_v

# 테스트: 긴 시퀀스에서 메모리 효율 확인
B, H, T, D = 1, 8, 100, 64
Q = torch.randn(B, H, T, D)
K = torch.randn(B, H, T, D)
V = torch.randn(B, H, T, D)

out = sliding_window_attention(Q, K, V, window_size=16)
print(f"SWA output shape: {out.shape}")  # (1, 8, 100, 64)
print(f"각 토큰은 최대 16개의 이전 토큰만 참조")
```