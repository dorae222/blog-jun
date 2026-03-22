---
title: "DeepSeek-V3 Technical Report"
slug: "deepseek-v3"
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.365625+00:00"
architecture_entry: "deepseek-v3"
---

## 개요

DeepSeek-V3는 2024년 12월 DeepSeek AI가 공개한 671B 파라미터 MoE 언어 모델로, 토큰당 37B 파라미터만 활성화한다. 전작 DeepSeek-V2의 MLA와 DeepSeekMoE 아키텍처를 계승하면서, 세 가지 핵심 혁신을 추가했다: (1) 보조 손실 없는 부하 균형 전략, (2) Multi-Token Prediction(MTP) 훈련 목표, (3) FP8 혼합 정밀도 훈련 프레임워크. 단 2.788M H800 GPU-시간(약 557만 달러)으로 14.8T 토큰 훈련을 완료하여, 유사 규모 Dense 모델 대비 압도적인 비용 효율성을 입증했다.

## 배경 및 문제 정의

DeepSeek-V2 이후의 핵심 과제는 세 가지였다. 첫째, MoE 모델의 전문가 부하 균형을 위해 사용하는 보조 손실(auxiliary loss)이 모델 성능을 저하시키는 문제가 있었다. 부하 균형 계수 $\alpha$를 키우면 균형은 잡히지만 손실 함수의 목표가 분산되어 주요 언어 모델링 성능이 떨어진다. 둘째, 표준 다음 토큰 예측(NTP)만으로는 훈련 신호가 충분히 풍부하지 않다. 셋째, BF16/FP32 훈련은 계산 및 메모리 비용이 높아 초대형 모델의 훈련 효율성을 제한한다.

## 핵심 아이디어

### 보조 손실 없는 부하 균형 (Auxiliary-Loss-Free Load Balancing)

기존 방식은 전문가 활용도를 균등하게 하기 위해 보조 손실 $\mathcal{L}_{aux}$를 메인 손실에 더했다:

$$\mathcal{L}_{total} = \mathcal{L}_{LM} + \alpha \cdot \mathcal{L}_{aux}$$

DeepSeek-V3는 대신 각 전문가에 대한 편향 항(bias term) $b_i$를 라우팅 점수에 추가한다:

$$g'_{i,t} = \begin{cases} s_{i,t} & \text{if } s_{i,t} + b_i \in \text{TopK}(\{s_{j,t}+b_j\}_{j=1}^{N_r}, K_r) \\ 0 & \text{otherwise} \end{cases}$$

실제 게이팅 값은 편향 없이 $s_{i,t}$를 사용하고, 토큰 선택에만 $b_i$를 활용한다. 각 훈련 스텝에서 과부하 전문가의 $b_i$는 감소시키고 과소부하 전문가의 $b_i$는 증가시키는 동적 업데이트를 수행한다:

$$b_i \leftarrow b_i - \gamma \cdot \mathbf{1}[\text{expert } i \text{ is overloaded}] + \gamma \cdot \mathbf{1}[\text{expert } i \text{ is underloaded}]$$

이를 통해 메인 손실에 간섭 없이 전문가 부하를 균등하게 유지한다.

### Multi-Token Prediction (MTP)

MTP는 각 위치에서 다음 1개 토큰이 아닌 $D$개의 연속 토큰을 동시에 예측하도록 한다. 각 추가 예측 헤드 $k = 1, \ldots, D$는 독립적인 Transformer 레이어와 출력 임베딩을 가진다:

$$\mathcal{L}_{MTP}^k = -\sum_{t} \log P(x_{t+k+1} | h_t^{(k)})$$

전체 MTP 훈련 목표:

$$\mathcal{L}_{total} = \mathcal{L}_{LM} + \lambda \sum_{k=1}^{D} \mathcal{L}_{MTP}^k$$

DeepSeek-V3에서는 $D=1$ (1개의 추가 토큰 예측 모듈)을 사용하며, $\lambda = 0.3$으로 설정했다. MTP는 훈련 시 주 모델의 표현을 풍부하게 하는 동시에, 추론 시 투기적 디코딩(speculative decoding)에 활용하여 처리량을 향상시킨다.

### FP8 혼합 정밀도 훈련

H800 GPU의 FP8 텐서 코어를 활용하여 선형 레이어 계산을 FP8로 수행하고, 누적과 민감한 연산(어텐션, 정규화)은 BF16/FP32로 유지하는 혼합 정밀도 전략을 채택했다. 세밀한 양자화(tile-wise, block-wise quantization)를 통해 FP8 수치 안정성을 확보했다.

## 아키텍처 / 방법론

| 구성 요소 | 설정값 |
|---|---|
| 총 파라미터 | 671B |
| 활성화 파라미터 | 37B |
| Transformer 레이어 | 61 |
| 어텐션 헤드 수 | 128 |
| KV 압축 차원 | 512 |
| 라우팅 전문가 수 | 256 |
| 공유 전문가 수 | 1 |
| 활성화 전문가 수 | 8 |
| 최대 시퀀스 길이 | 128K |
| 훈련 토큰 수 | 14.8T |
| 훈련 비용 | 2.788M H800 GPU-hours |

파이프라인 병렬화, 전문가 병렬화, 데이터 병렬화를 결합한 DualPipe 알고리즘으로 크로스-노드 통신 오버헤드를 최소화했다.

## 실험 결과

### 주요 벤치마크 비교

| 벤치마크 | GPT-4o | Claude-3.5-Sonnet | DeepSeek-V3 | Llama-3.1-405B |
|---|---|---|---|---|
| MMLU | 88.0 | 88.3 | **88.5** | 87.3 |
| MATH-500 | 76.6 | 78.3 | **90.2** | 73.8 |
| HumanEval | 90.2 | **92.0** | 89.0 | 89.0 |
| GPQA Diamond | 53.6 | **65.0** | 59.1 | 51.1 |
| LiveCodeBench | 33.4 | 36.3 | **43.4** | 27.4 |
| AIME 2024 | 9.3 | 16.0 | **39.2** | 23.3 |

DeepSeek-V3는 특히 수학(MATH-500: 90.2%)과 코딩(LiveCodeBench: 43.4%) 분야에서 최강 클로즈드 모델들을 능가한다.

### 훈련 안정성

14.8T 토큰 훈련 전반에 걸쳐 손실 스파이크(loss spike) 없이 안정적인 수렴을 달성했으며, FP8 훈련이 BF16 대비 동등한 성능을 유지함을 확인했다.

## 의의 및 한계

DeepSeek-V3는 오픈소스 LLM의 새로운 기준점을 제시했다. 특히 보조 손실 없는 부하 균형 전략은 MoE 훈련의 오랜 딜레마를 해결한 중요한 기여이며, MTP는 훈련과 추론 양쪽에서 실질적인 이점을 제공하는 우아한 설계다. 약 557만 달러의 훈련 비용은 동급 성능 대비 전례 없이 낮은 수준으로, AI 접근성 민주화에 기여한다.

한계로는 671B 전체 모델 배포에 여전히 상당한 GPU 메모리(최소 80GB × 8개 이상)가 필요하다. 또한 MTP의 추가 예측 헤드 설계에서 최적의 $D$ 값과 $\lambda$ 계수 결정이 여전히 경험적이며, 다양한 도메인에서의 MTP 효과가 균일하지 않을 수 있다.

## 코드 예제

### Multi-Token Prediction (MTP) 구현 (PyTorch)

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class MultiTokenPrediction(nn.Module):
    """DeepSeek-V3의 MTP: 다음 1개 토큰 외 추가 토큰들도 동시에 예측.
    학습 신호를 강화하고 추론 시 speculative decoding에 활용 가능.
    """
    def __init__(self, d_model=7168, vocab_size=129280, num_extra_tokens=1):
        super().__init__()
        self.num_extra_tokens = num_extra_tokens
        # 추가 예측 헤드: 각 추가 토큰마다 별도 MTP 모듈
        self.mtp_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(d_model * 2, d_model),  # h_i + embed_{t+k} 결합
                nn.SiLU(),
                nn.Linear(d_model, vocab_size)
            ) for _ in range(num_extra_tokens)
        ])
        self.embed = nn.Embedding(vocab_size, d_model)
        self.main_head = nn.Linear(d_model, vocab_size)  # 기본 다음 토큰 예측

    def forward(self, hidden_states, input_ids, targets=None):
        """hidden_states: (B, T, d_model)"""
        B, T, D = hidden_states.shape
        # 기본 언어 모델 손실 (다음 토큰 예측)
        main_logits = self.main_head(hidden_states)   # (B, T, V)
        loss = 0.0
        if targets is not None:
            loss = F.cross_entropy(main_logits[:, :-1].reshape(-1, main_logits.size(-1)),
                                   targets[:, 1:].reshape(-1))
        # 추가 토큰 예측 (MTP)
        for k, mtp_head in enumerate(self.mtp_heads, start=2):
            if T > k:
                # h_i 와 embed(t+k-1) 결합해서 t+k 예측
                future_embed = self.embed(input_ids[:, k-1:T])  # (B, T-k+1, D)
                combined = torch.cat([hidden_states[:, :T-k+1], future_embed], dim=-1)
                extra_logits = mtp_head(combined)  # (B, T-k+1, V)
                if targets is not None:
                    mtp_loss = F.cross_entropy(
                        extra_logits.reshape(-1, extra_logits.size(-1)),
                        targets[:, k:T+1].reshape(-1)
                    )
                    loss = loss + 0.3 * mtp_loss  # MTP 가중치 λ=0.3
        return main_logits, loss

# Auxiliary-loss-free 부하 균형: 편향 조정 방식
class AuxLossFreeMoERouter(nn.Module):
    """DeepSeek-V3의 보조 손실 없는 부하 균형 라우터."""
    def __init__(self, d_model, num_experts, top_k):
        super().__init__()
        self.router = nn.Linear(d_model, num_experts, bias=False)
        self.bias = nn.Parameter(torch.zeros(num_experts))  # 동적 편향
        self.top_k = top_k
        self.alpha = 0.001  # 편향 업데이트 속도

    def forward(self, x):
        logits = self.router(x) + self.bias  # 편향 추가
        _, selected = torch.topk(logits, self.top_k, dim=-1)
        return selected

    def update_bias(self, load_counts, target_load):
        """과부하 전문가 편향 감소, 과소 전문가 편향 증가."""
        with torch.no_grad():
            self.bias.data -= self.alpha * torch.sign(load_counts - target_load)

# 테스트
mtp = MultiTokenPrediction(d_model=256, vocab_size=1000, num_extra_tokens=1)
hidden = torch.randn(2, 20, 256)
input_ids = torch.randint(0, 1000, (2, 20))
targets = torch.randint(0, 1000, (2, 20))
logits, loss = mtp(hidden, input_ids, targets)
print(f"logits: {logits.shape}, loss: {loss.item():.4f}")
```