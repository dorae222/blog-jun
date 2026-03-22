---
title: "RWKV: 상태 공간 기반 시퀀스 모델"
slug: rwkv
category: ssm
tags: ["Channel Mixing", "Linear Attention", "Parallel Training", "Recurrence", "rnn", "RWKV", "RWKV Foundation", "Time Mixing", "Token Shift", "WKV Operator"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.450062+00:00"
architecture_entry: rwkv
---

# RWKV: Transformer의 병렬 학습과 RNN의 효율적 추론을 결합한 커뮤니티 주도 모델

**RWKV Foundation / EleutherAI** · **2023-05-22** · **SSM** · **Apache-2.0**

## 개요

RWKV(Receptance Weighted Key Value)는 2023년 Bo Peng이 제안하고 RWKV Foundation과 EleutherAI가 함께 발전시킨 모델로, Transformer의 병렬 학습 능력과 RNN의 효율적 추론을 동시에 달성한 혁신적 아키텍처이다. RWKV라는 이름은 네 가지 핵심 요소 -- R(Receptance), W(Weight/Decay), K(Key), V(Value) -- 에서 유래한다.

WKV(Weighted Key-Value) 연산자를 통해 어텐션의 $O(N^2)$ 복잡도 없이 시퀀스 의존성을 포착한다. 학습 시에는 병렬 계산(Transformer처럼), 추론 시에는 순환 계산(RNN처럼) 동작하는 이중성이 핵심이다. 14B 파라미터 버전까지 Apache-2.0 라이선스로 공개되어 대형 언어 모델 오픈소스 생태계에 큰 기여를 했다.

RWKV는 학술 연구실이 아닌 오픈소스 커뮤니티에서 시작하여 대규모 모델까지 발전시킨 독특한 사례이다. World Tokenizer를 통한 100개 이상 언어 지원이 특히 강점이며, 한국어를 포함한 비영어 언어에서도 효율적인 토크나이제이션을 제공한다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

RWKV 블록은 두 가지 핵심 모듈로 구성된다.

### Time Mixing (시퀀스 방향 정보 혼합)

시간축을 따라 토큰 간 정보를 혼합하는 모듈이다. 먼저 Token Shift 연산으로 현재 토큰과 이전 토큰의 정보를 선형 보간한다.

$$r_t = W_r \cdot (\mu_r \odot x_t + (1-\mu_r) \odot x_{t-1})$$
$$k_t = W_k \cdot (\mu_k \odot x_t + (1-\mu_k) \odot x_{t-1})$$
$$v_t = W_v \cdot (\mu_v \odot x_t + (1-\mu_v) \odot x_{t-1})$$

여기서 $\mu$는 학습 가능한 보간 비율이다. 이 Token Shift는 인접 토큰 정보를 자연스럽게 결합하여 bigram 수준의 국소 패턴을 포착하며, H3의 Shift SSM과 유사한 역할을 한다.

WKV 연산자의 핵심 수식은 다음과 같다.

$$\text{wkv}_t = \frac{\sum_{i=1}^{t-1} e^{-(t-1-i)w + k_i} v_i + e^{u+k_t} v_t}{\sum_{i=1}^{t-1} e^{-(t-1-i)w + k_i} + e^{u+k_t}}$$

여기서 $w$는 시간 감쇠(time decay) 파라미터로, 과거 토큰의 영향이 시간이 지남에 따라 지수적으로 감소한다. $u$는 현재 토큰에 대한 보너스 가중치이다. 이 연산은 어텐션의 softmax-weighted sum과 기능적으로 유사하지만, 순환적으로 계산할 수 있어 $O(N)$ 복잡도를 달성한다.

SSM과의 연결을 보면, WKV 연산의 순환 형태는 다음과 같다.

$$a_t = e^{-w} a_{t-1} + e^{k_t} v_t, \quad b_t = e^{-w} b_{t-1} + e^{k_t}$$
$$\text{wkv}_t = \frac{a_t}{b_t}$$

이는 RetNet의 상태 업데이트 $s_t = \gamma s_{t-1} + k_t^T v_t$와 구조적으로 유사하며, $e^{-w}$가 감쇠율 $\gamma$에 해당한다.

최종 출력은 R(Receptance) 게이트로 조절된다.

$$o_t = \sigma(r_t) \odot \text{wkv}_t$$

### Channel Mixing (채널 방향 정보 변환)

Transformer의 FFN에 해당하는 모듈이다. Token Shift를 적용한 뒤, SiLU 활성화 함수와 sigmoid 게이트를 결합한다.

$$o_t = \sigma(r'_t) \odot (W_v' \cdot \max(k'_t, 0)^2)$$

## 핵심 혁신

RWKV의 핵심 혁신은 세 가지이다.

첫째, **WKV 연산자**이다. softmax 어텐션을 지수 감쇠 가중합으로 대체하면서도 Transformer와 유사한 표현력을 유지한다. 순환 형태로 변환 가능하여 추론 시 $O(1)$ 메모리를 달성한다.

둘째, **Token Shift**이다. 인접 토큰 정보를 선형 보간하여 bigram 수준의 국소 패턴을 효과적으로 포착한다.

셋째, **커뮤니티 기반 발전**이다. 오픈소스 커뮤니티에서 시작하여 14B까지 성장한 독특한 사례이며, World Tokenizer를 통한 다국어 지원이 강점이다.

## 벤치마크/성능

| 모델 | 파라미터 | Pile PPL↓ | LAMBADA | HellaSwag | ARC-E |
|------|---------|-----------|---------|-----------|-------|
| RWKV-4 | 14B | 5.63 | 77.2 | 72.5 | 70.3 |
| RWKV-4 | 7B | 6.31 | 73.8 | 66.7 | 65.1 |
| RWKV-4 | 3B | 6.85 | 68.5 | 58.8 | 57.2 |
| Pythia | 12B | 5.51 | 78.1 | 73.2 | 71.5 |

| 모델 | 토큰 믹싱 | 학습 병렬화 | 추론 복잡도 | 다국어 지원 |
|------|---------|-----------|-----------|------------|
| RWKV | WKV + Token Shift | 시간축 병렬 | $O(1)$ 메모리 | World Tokenizer |
| Mamba | 선택적 SSM | Parallel scan | $O(1)$ 메모리 | GPT-NeoX |
| RetNet | Retention | 완전 병렬 | $O(1)$ 메모리 | SentencePiece |
| Transformer | Self-Attention | 완전 병렬 | $O(N)$ KV cache | 다양 |

## 학습

Pile 데이터셋 등 대규모 텍스트로 학습하며, A100 GPU를 사용한다. RWKV 전용 World Tokenizer는 65,536 vocab 크기로 100개 이상 언어를 효율적으로 토크나이즈한다. EleutherAI와 협력으로 재현 가능한 학습 파이프라인이 공개되어 있다.

다음은 RWKV의 WKV 연산자를 순환 모드로 구현한 예시이다.

```python
import torch
import torch.nn as nn

class RWKVTimeMixing(nn.Module):
    def __init__(self, d_model):
        super().__init__()
        self.w = nn.Parameter(torch.randn(d_model))  # 시간 감쇠
        self.u = nn.Parameter(torch.randn(d_model))  # 현재 보너스
        self.mu_r = nn.Parameter(torch.ones(d_model) * 0.5)
        self.mu_k = nn.Parameter(torch.ones(d_model) * 0.5)
        self.mu_v = nn.Parameter(torch.ones(d_model) * 0.5)
        self.W_r = nn.Linear(d_model, d_model, bias=False)
        self.W_k = nn.Linear(d_model, d_model, bias=False)
        self.W_v = nn.Linear(d_model, d_model, bias=False)
        self.W_o = nn.Linear(d_model, d_model, bias=False)

    def forward_recurrent(self, x_t, x_prev, state_a, state_b):
        """순환 모드 추론 - O(1) 메모리"""
        # Token Shift: 현재/이전 토큰 보간
        r = self.W_r(self.mu_r * x_t + (1 - self.mu_r) * x_prev)
        k = self.W_k(self.mu_k * x_t + (1 - self.mu_k) * x_prev)
        v = self.W_v(self.mu_v * x_t + (1 - self.mu_v) * x_prev)
        
        # WKV 순환 계산
        wkv = (state_a + torch.exp(self.u + k) * v) / \
              (state_b + torch.exp(self.u + k))
        
        # 상태 업데이트
        new_a = torch.exp(-self.w) * state_a + torch.exp(k) * v
        new_b = torch.exp(-self.w) * state_b + torch.exp(k)
        
        # Receptance 게이트
        out = torch.sigmoid(r) * wkv
        return self.W_o(out), new_a, new_b
```

## 관련 모델

RWKV는 GitHub(BlinkDL/RWKV-LM)에서 직접 사용할 수 있으며, Hugging Face에서도 다양한 크기의 모델이 공개되어 있다. WKV 연산자에서 감쇠 가중치 $w$가 채널별로 고정되어 있어 입력에 따라 동적으로 감쇠율을 조절하지 못하는 한계는 RWKV-5, RWKV-6에서 데이터 의존적 게이팅을 도입하여 점진적으로 개선되었고, RWKV-7(Goose)에서 Delta Rule 기반으로 전면 재설계되었다.

## 참고 자료

- 논문: [RWKV: Reinventing RNNs for the Transformer Era](https://arxiv.org/abs/2305.13048)
- 코드: [BlinkDL/RWKV-LM](https://github.com/BlinkDL/RWKV-LM)

## 관련 문서

- [[rwkv-7|RWKV-7 (Goose)]] — 후속 모델
- [[transformer|Transformer]] — 영감
