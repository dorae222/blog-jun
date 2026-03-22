---
title: "DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model"
slug: "deepseek-v2"
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.497131+00:00"
architecture_entry: "deepseek-v2"
---

## 개요

DeepSeek-V2는 DeepSeek AI가 2024년 5월 발표한 MoE(Mixture-of-Experts) 기반 대규모 언어 모델이다. 총 236B 파라미터를 가지지만 토큰당 21B만 활성화하는 희소 활성화 구조를 채택하여, 강력한 성능을 경제적으로 달성한다. 핵심 기여는 두 가지 혁신적인 아키텍처 구성 요소인 **Multi-head Latent Attention(MLA)**와 **DeepSeekMoE**이며, 이를 통해 DeepSeek 67B 대비 훈련 비용 42.5% 절감, KV 캐시 93.3% 절감, 추론 처리량 5.76배 향상을 달성했다.

## 배경 및 문제 정의

기존 대형 언어 모델들은 두 가지 주요 병목을 가진다. 첫째, 표준 Multi-Head Attention(MHA)은 추론 시 각 레이어마다 $2 \times n_{heads} \times d_{head}$ 크기의 KV 캐시를 유지해야 하므로 긴 시퀀스 처리 시 메모리 요구량이 급격히 증가한다. 둘째, Dense 모델은 모든 파라미터를 매 토큰마다 활성화하므로 계산 비용이 파라미터 수에 선형 비례한다.

Grouped Query Attention(GQA)이나 Multi-Query Attention(MQA) 같은 기존 KV 캐시 압축 기법들은 성능 저하를 감수해야 했으며, MoE 선행 연구들(GShard, Switch Transformer)은 전문가 활용 불균형 및 지식 분절 문제를 완전히 해결하지 못했다.

## 핵심 아이디어

### Multi-head Latent Attention (MLA)

MLA의 핵심은 KV 벡터를 저차원 잠재 공간으로 압축(down-projection)한 뒤, 실제 계산 시에만 복원(up-projection)하는 방식이다.

$$c_t^{KV} = W^{DKV} h_t$$

$$k_t^C = W^{UK} c_t^{KV}, \quad v_t^C = W^{UV} c_t^{KV}$$

여기서 $c_t^{KV} \in \mathbb{R}^{d_c}$는 압축된 잠재 벡터이며, $d_c \ll n_h \cdot d_h$이다. 캐시에는 전체 KV 대신 $c_t^{KV}$만 저장하므로, 메모리 사용량이 $O(d_c)$로 줄어든다. RoPE(Rotary Position Embedding)를 위한 위치 정보는 별도의 디커플링된 키 벡터 $k_t^R$에 보존한다.

$$q_t = [q_t^C; q_t^R], \quad k_t = [k_t^C; k_t^R]$$

최종 어텐션 출력:

$$o_{t,i} = \sum_{j \leq t} \text{softmax}\left(\frac{q_{t,i}^\top k_{j,i}}{\sqrt{d_h + d_h^R}}\right) v_{j,i}^C$$

이 설계로 MHA 대비 KV 캐시를 93.3% 절감하면서도 성능 저하 없이 풀 어텐션 표현력을 유지한다.

### DeepSeekMoE

DeepSeekMoE는 두 가지 전략을 결합한다.

**세분화된 전문가(Fine-grained Experts)**: 각 전문가의 FFN 차원을 줄이고 전문가 수를 늘려 더 정밀한 지식 분할이 가능하도록 한다. 전통적인 MoE가 $N$개의 전문가에서 $K$개를 활성화한다면, DeepSeekMoE는 $mN$개의 더 작은 전문가에서 $mK$개를 활성화한다.

**공유 전문가(Shared Experts)**: 일부 전문가를 항상 활성화되는 공유 전문가로 지정하여 범용 지식을 담당하게 하고, 나머지 라우팅 전문가들은 특수화된 지식에 집중한다.

전체 FFN 출력:

$$h_t' = \sum_{i=1}^{K_s} \text{FFN}_i^{(s)}(h_t) + \sum_{i=1}^{N_r} g_{i,t} \cdot \text{FFN}_i^{(r)}(h_t)$$

여기서 $K_s$는 공유 전문가 수, $N_r$은 라우팅 전문가 수이며, $g_{i,t}$는 게이팅 점수:

$$g_{i,t} = \frac{e^{s_{i,t}}}{\sum_{j \in \text{TopK}} e^{s_{j,t}}}, \quad s_{i,t} = \text{softmax}_i(W_g h_t)$$

부하 균형을 위해 보조 손실(auxiliary loss)을 추가하여 전문가 활용이 고르게 분포되도록 강제한다.

## 아키텍처 / 방법론

| 구성 요소 | 설정값 |
|---|---|
| 총 파라미터 | 236B |
| 활성화 파라미터 | 21B |
| Transformer 레이어 | 60 |
| 어텐션 헤드 수 | 128 |
| KV 압축 차원 $d_c$ | 512 |
| 라우팅 전문가 수 | 160 |
| 공유 전문가 수 | 2 |
| 활성화 전문가 수 | 6 |
| 최대 시퀀스 길이 | 128K |

훈련 데이터는 8.1T 토큰의 다국어 코퍼스(영어·중국어 중심)를 사용했으며, 이후 SFT(Supervised Fine-Tuning)와 RLHF(그룹 상대 정책 최적화, GRPO)를 통해 DeepSeek-V2-Chat 버전을 제공한다.

## 실험 결과

### 주요 벤치마크 (Base 모델)

| 벤치마크 | DeepSeek 67B | DeepSeek-V2 | Llama3 70B |
|---|---|---|---|
| MMLU | 71.3 | **78.5** | 79.5 |
| HumanEval | 45.1 | **48.8** | 81.7 |
| MATH | 18.7 | **43.6** | 30.0 |
| GSM8K | 63.4 | **79.2** | 83.0 |
| BBH | 68.7 | **78.9** | 81.0 |
| C-Eval | 66.1 | **81.7** | 67.7 |

DeepSeek-V2는 파라미터 대비 활성화 비율이 낮음에도 불구하고 DeepSeek 67B를 전반적으로 능가하며, 중국어 벤치마크(C-Eval)에서 특히 강점을 보인다.

### 경제성 비교

| 모델 | 활성화 파라미터 | 훈련 비용(GPU-Hours) | 상대 비용 |
|---|---|---|---|
| DeepSeek 67B | 67B | 기준 | 1.0x |
| DeepSeek-V2 | 21B | ~42.5% 절감 | 0.575x |

추론 처리량은 DeepSeek 67B 대비 5.76배 향상, 프리필 처리량 6.54배, KV 캐시 93.3% 절감을 달성했다.

## 의의 및 한계

DeepSeek-V2는 MoE 모델이 Dense 모델과 동등하거나 우수한 성능을 훨씬 낮은 비용으로 달성할 수 있음을 실증했다. MLA는 이후 DeepSeek-V3, DeepSeek-R1 등 후속 모델들의 표준 어텐션 메커니즘으로 채택될 만큼 강력한 기여를 했다. 특히 128K 컨텍스트를 KV 캐시 부담 없이 처리할 수 있다는 점은 실용적 배포 측면에서 큰 의미를 가진다.

한계로는 MoE 모델 특성상 전문가 병렬화를 위한 다수의 GPU가 필요하여 소규모 배포 환경에서 접근성이 제한된다. 또한 공유 전문가와 라우팅 전문가 사이의 최적 비율 결정이 여전히 경험적으로 이루어진다는 점, 그리고 전문가 부하 불균형 문제가 완전히 해결된 것은 아니라는 점이 후속 연구 과제로 남는다.

## 코드 예제

### MLA (Multi-head Latent Attention) 핵심 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import math

class MultiHeadLatentAttention(nn.Module):
    """DeepSeek-V2의 MLA: KV를 저차원 잠재 벡터로 압축.
    표준 MHA 대비 KV 캐시를 93% 줄임.
    """
    def __init__(self, d_model=5120, num_heads=128, kv_lora_rank=512, q_lora_rank=1536, head_dim=128, rope_head_dim=64):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = head_dim

        # KV 다운-업 프로젝션 (압축)
        self.kv_down = nn.Linear(d_model, kv_lora_rank, bias=False)  # 압축: d_model → kv_lora_rank
        self.k_up = nn.Linear(kv_lora_rank, num_heads * head_dim, bias=False)  # 복원
        self.v_up = nn.Linear(kv_lora_rank, num_heads * head_dim, bias=False)

        # Q 다운-업 프로젝션
        self.q_down = nn.Linear(d_model, q_lora_rank, bias=False)
        self.q_up = nn.Linear(q_lora_rank, num_heads * head_dim, bias=False)

        # RoPE용 분리 키 (decoupled RoPE)
        self.k_rope = nn.Linear(d_model, num_heads * rope_head_dim, bias=False)
        self.q_rope = nn.Linear(q_lora_rank, num_heads * rope_head_dim, bias=False)

        self.out_proj = nn.Linear(num_heads * head_dim, d_model, bias=False)

    def forward(self, x, use_cache=True):
        B, T, _ = x.shape

        # KV 압축 → 이것만 KV 캐시에 저장! (93% 절감)
        c_kv = self.kv_down(x)               # (B, T, kv_lora_rank) ← 캐시 저장
        K = self.k_up(c_kv).view(B, T, self.num_heads, self.head_dim)
        V = self.v_up(c_kv).view(B, T, self.num_heads, self.head_dim)

        # Q 계산 (캐시 불필요)
        c_q = self.q_down(x)
        Q = self.q_up(c_q).view(B, T, self.num_heads, self.head_dim)

        # Attention 계산
        scale = math.sqrt(self.head_dim)
        Q = Q.transpose(1, 2)  # (B, H, T, D)
        K = K.transpose(1, 2)
        V = V.transpose(1, 2)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / scale
        attn = torch.softmax(scores, dim=-1)
        out = torch.matmul(attn, V).transpose(1, 2).contiguous().view(B, T, -1)
        return self.out_proj(out)

# KV 캐시 크기 비교
d_model, num_heads, head_dim = 5120, 128, 128
kv_lora_rank = 512

# 표준 MHA KV 캐시: 레이어당 num_heads * head_dim * 2 (K+V)
mha_kv = num_heads * head_dim * 2
# MLA KV 캐시: kv_lora_rank만 저장
mla_kv = kv_lora_rank
print(f"MHA KV 캐시/토큰/레이어: {mha_kv:,} floats")
print(f"MLA KV 캐시/토큰/레이어: {mla_kv:,} floats")
print(f"절감률: {(1 - mla_kv/mha_kv)*100:.1f}%")  # ~97.5%
```