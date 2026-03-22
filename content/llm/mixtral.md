---
title: Mixtral of Experts
slug: mixtral
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.494696+00:00"
architecture_entry: mixtral
---

## 개요

Mixtral 8x7B는 Mistral AI가 2024년 1월 발표한 **희소 혼합 전문가(Sparse Mixture of Experts, SMoE)** 언어 모델이다. 모델 이름처럼 8개의 "전문가(expert)" FFN 레이어가 있으며, 각 토큰은 그 중 2개만 선택하여 처리된다. 이를 통해 전체 파라미터는 46.7B이지만, 실제 추론 시에는 12.9B만 활성화되어 **더 적은 연산으로 더 큰 모델의 성능**을 달성한다.

Mixtral은 오픈 가중치(Apache 2.0)로 공개되었으며, Llama 2 70B보다 대부분 벤치마크에서 우수하고, 추론 속도는 약 6배 빠르다. 명령 파인튜닝 버전인 Mixtral 8x7B Instruct는 GPT-3.5 Turbo와 동등하거나 우수한 성능을 보인다.

## 배경 및 문제

### 스케일링의 계산 비용 문제

더 좋은 성능을 위해 모델을 키우면 추론 비용이 선형적으로 증가한다. 70B 모델은 7B 모델보다 10배 많은 GPU 메모리와 연산을 필요로 한다. 실용적인 배포를 위해서는 **파라미터는 많지만 연산은 적은** 방법이 필요하다.

### 혼합 전문가(MoE)의 역사

MoE 아키텍처는 1991년 Jacobs et al.이 제안하였고, Shazeer et al.(2017)이 LSTM에 희소 MoE를 적용했으며, Switch Transformer(2022)가 Transformer에 MoE를 성공적으로 적용했다. Mixtral은 이를 오픈소스 대형 모델에 실용적으로 구현한 사례다.

## 핵심 아이디어

### 희소 MoE 레이어

Mixtral은 Mistral 7B의 아키텍처를 기반으로, 각 Transformer 레이어의 **FFN(Feed-Forward Network) 서브레이어를 8개의 전문가 FFN으로 교체**한다. 어텐션 레이어는 그대로 유지한다.

각 토큰 $x$에 대해 게이팅 네트워크(router)가 8개 전문가 중 상위 2개를 선택한다:

$$\text{MoE}(x) = \sum_{i \in \text{Top2}} G_i(x) \cdot E_i(x)$$

$$G(x) = \text{Softmax}(\text{TopK}(x \cdot W_g, 2))$$

여기서 $W_g$는 게이팅 가중치 행렬, $E_i$는 $i$번째 전문가 FFN, $G_i(x)$는 해당 전문가의 소프트맥스 가중치다. TopK는 상위 2개 외 나머지를 $-\infty$로 마스킹한다.

### 파라미터 효율

- **전체 파라미터**: 46.7B
- **추론 시 활성 파라미터**: 12.9B (전체의 약 27.6%)
- **어텐션 레이어**: 전체 공유 (MoE 적용 안 됨)
- **전문가 FFN**: 각 레이어마다 8개

토큰당 2개의 전문가를 사용하므로, 연산량은 약 13B 모델과 동일하지만 전체 파라미터 용량은 47B에 달한다.

### 아키텍처 세부 사항

Mixtral은 Mistral 7B의 다음 설정을 공유한다:
- **SWA (Sliding Window Attention)**: 윈도우 크기 4096
- **GQA (Grouped Query Attention)**: 8개 KV 헤드
- **RoPE Positional Embedding**
- **RMSNorm**
- **SwiGLU 활성화 함수**
- **컨텍스트 길이**: 32K 토큰

## 방법론

### 모델 구성

| 항목 | 값 |
|------|----|
| 전체 파라미터 | 46.7B |
| 활성 파라미터 | 12.9B |
| 레이어 수 | 32 |
| 전문가 수/레이어 | 8 |
| 활성 전문가/토큰 | 2 |
| 쿼리 헤드 수 | 32 |
| KV 헤드 수 | 8 |
| 히든 차원 | 4096 |
| 전문가 FFN 차원 | 14336 |
| 컨텍스트 길이 | 32768 |

### 분산 훈련과 전문가 병렬화

MoE 모델의 학습에는 **전문가 병렬화(Expert Parallelism)**가 핵심이다. 각 전문가를 다른 GPU에 배치하여 병렬로 계산한다. All-to-all 통신이 필요하여 분산 환경 설계가 복잡하지만, Mixtral은 이를 효율적으로 구현한다.

## 실험 결과

### 주요 벤치마크 비교

| 모델 | MMLU | HellaSwag | WinoGrande | ARC-c | HumanEval | MBPP | GSM8K |
|------|------|-----------|------------|-------|-----------|------|-------|
| Llama 2-13B | 54.8 | 81.9 | 72.0 | 48.8 | 18.3 | 30.2 | 29.6 |
| Llama 2-70B | 69.8 | 87.1 | 80.0 | 57.4 | 29.9 | 49.8 | 59.4 |
| GPT-3.5 | 70.0 | 85.5 | 81.6 | 61.5 | 48.1 | - | 57.1 |
| **Mixtral 8x7B** | **70.6** | **86.7** | **81.2** | **60.7** | **40.2** | **52.2** | **74.4** |

Mixtral은 Llama 2 70B를 대부분 태스크에서 능가하고, GSM8K(수학)에서는 GPT-3.5를 크게 앞선다.

### 추론 속도 비교

| 모델 | 활성 파라미터 | 상대적 처리량 |
|------|-------------|-------------|
| Llama 2-70B | 70B | 1x |
| Mixtral 8x7B | 12.9B | ~6x |

동일한 하드웨어에서 Mixtral은 Llama 2 70B보다 약 6배 빠른 처리량을 제공한다.

### 다국어 성능

| 모델 | DE | FR | IT | ES |
|------|----|----|----|----|  
| Llama 2-70B | 52.4 | 54.0 | 48.6 | 63.9 |
| Mixtral 8x7B | **59.4** | **62.0** | **57.0** | **70.1** |

영어 외에도 독일어, 프랑스어, 이탈리아어, 스페인어에서 Llama 2 70B를 능가한다.

### Mixtral 8x7B Instruct

- MT-Bench: 8.3 (GPT-3.5 Turbo의 8.32와 동등)
- 인간 선호도 평가에서 GPT-3.5 대비 동등하거나 우위

## 의의 및 한계

### 의의

- **MoE의 오픈소스 실용화**: 대규모 희소 MoE를 오픈 가중치로 공개한 선구적 사례
- **효율성 패러다임 전환**: "더 큰 모델 = 더 느린 추론" 공식을 깨뜨림
- **수학/코드 강점**: 전문가 특화로 도메인별 능력이 자연스럽게 향상
- **32K 컨텍스트**: 긴 문서 처리 능력 내재화

### 한계

- **높은 메모리 요구**: 추론 연산은 13B 수준이지만 전체 가중치를 메모리에 올려야 해 46.7B 분량의 VRAM 필요
- **전문가 불균형(Load Imbalance)**: 특정 전문가에 토큰이 쏠리는 현상 발생 가능
- **학습 복잡성**: All-to-all 통신으로 인한 분산 학습의 복잡성
- **해석 가능성**: 어떤 전문가가 어떤 능력을 담당하는지 분석이 어려움

Mixtral은 희소 MoE 아키텍처를 오픈소스 LLM 세계에 본격적으로 도입한 모델로, 이후 DeepSeek-MoE, Qwen-MoE 등 다양한 MoE 모델 연구의 기폭제가 되었다.

## 코드 예제

### Sparse Mixture of Experts (MoE) FFN 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class MoEFeedForward(nn.Module):
    """Mixtral 방식 Sparse MoE FFN.
    각 토큰마다 top-k 전문가만 활성화.
    """
    def __init__(self, d_model=4096, d_ff=14336, num_experts=8, top_k=2):
        super().__init__()
        self.num_experts = num_experts
        self.top_k = top_k
        # 라우터 (게이팅 네트워크)
        self.router = nn.Linear(d_model, num_experts, bias=False)
        # 전문가 네트워크 (SwiGLU FFN)
        self.experts_w1 = nn.ModuleList([nn.Linear(d_model, d_ff, bias=False) for _ in range(num_experts)])
        self.experts_w2 = nn.ModuleList([nn.Linear(d_ff, d_model, bias=False) for _ in range(num_experts)])
        self.experts_w3 = nn.ModuleList([nn.Linear(d_model, d_ff, bias=False) for _ in range(num_experts)])

    def forward(self, x):
        """x: (batch, seq_len, d_model)"""
        B, T, D = x.shape
        x_flat = x.view(-1, D)  # (B*T, D)

        # 라우팅: 각 토큰마다 top_k 전문가 선택
        router_logits = self.router(x_flat)               # (B*T, num_experts)
        router_weights, selected_experts = torch.topk(
            router_logits, self.top_k, dim=-1
        )                                                  # (B*T, top_k)
        router_weights = F.softmax(router_weights, dim=-1) # 선택된 전문가 가중치 정규화

        output = torch.zeros_like(x_flat)
        # 각 전문가 처리
        for expert_idx in range(self.num_experts):
            # 이 전문가를 선택한 토큰 마스크
            mask = (selected_experts == expert_idx).any(dim=-1)  # (B*T,)
            if not mask.any():
                continue
            expert_input = x_flat[mask]
            # SwiGLU FFN
            w1 = self.experts_w1[expert_idx]
            w2 = self.experts_w2[expert_idx]
            w3 = self.experts_w3[expert_idx]
            expert_out = w2(F.silu(w1(expert_input)) * w3(expert_input))
            # 해당 전문가의 가중치 찾기
            expert_weights = router_weights[mask][
                (selected_experts[mask] == expert_idx).nonzero(as_tuple=True)
            ]
            output[mask] += expert_weights.unsqueeze(-1) * expert_out

        return output.view(B, T, D)

# 테스트
moe = MoEFeedForward(d_model=512, d_ff=1024, num_experts=8, top_k=2)
x = torch.randn(2, 10, 512)
out = moe(x)
print(f"MoE output: {out.shape}")  # (2, 10, 512)

# 전문가 선택 분포 확인
with torch.no_grad():
    router_logits = moe.router(x.view(-1, 512))
    _, selected = torch.topk(router_logits, 2, dim=-1)
    counts = torch.bincount(selected.view(-1), minlength=8)
print(f"전문가별 활성화 횟수: {counts.tolist()}")
# 이상적으로는 균등 분포되어야 함 (부하 균형 중요)
```