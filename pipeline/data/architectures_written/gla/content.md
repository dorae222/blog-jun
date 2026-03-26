# GLA: 데이터 의존적 게이팅으로 선형 어텐션의 표현력을 향상시킨 모델

**Tsinghua University / Shanghai AI Lab** · **2023-12-15** · **SSM** · **MIT**

## 개요

GLA(Gated Linear Attention)는 2023년 청화대학교와 상하이 AI Lab이 발표한 모델로, 선형 어텐션에 데이터 의존적 게이팅(data-dependent gating)을 추가하여 표현력을 향상시킨 아키텍처이다. 기존 선형 어텐션은 softmax를 제거하여 $O(N)$ 복잡도를 달성하지만, 이로 인해 Transformer 대비 심각한 성능 저하가 발생하는 것이 고질적인 문제였다.

GLA는 이 문제의 근본 원인이 "모든 과거 정보를 동등하게 누적하는 것"에 있다고 진단했다. 일반 선형 어텐션의 상태 업데이트는 $S_t = S_{t-1} + k_t^T v_t$로, 모든 키-값 쌍이 동등하게 누적된다. 과거의 불필요한 정보가 계속 쌓이면서 상태가 오염되고, 관련 정보의 검색이 어려워진다.

GLA는 각 타임스텝에서 게이트 $G_t$를 입력에 따라 동적으로 계산하여 KV 상태의 망각(forget)과 기억(remember)을 선택적으로 조절한다. 이 구조는 Mamba의 선택적 메커니즘과 유사한 역할을 하지만, 행렬 값의 KV 상태를 유지한다는 점에서 차별화된다. RetNet 대비 일관되게 더 낮은 perplexity를 기록하며 선형 어텐션의 발전 방향을 제시했다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

GLA의 핵심은 KV 상태 업데이트 시 forget gate $G_t$를 적용하는 것이다.

### 게이트 선형 어텐션 상태 업데이트

$$S_t = G_t \odot S_{t-1} + k_t^T v_t$$

여기서 $G_t \in \mathbb{R}^{d_k \times d_v}$는 입력에 의존적으로 계산되는 행렬 게이트이다. $G_t$의 각 원소는 0과 1 사이의 값으로, 이전 상태 $S_{t-1}$의 어떤 부분을 유지하고 어떤 부분을 망각할지를 결정한다. 새로운 정보 $k_t^T v_t$는 외적(outer product) 형태로 상태에 추가된다.

출력은 쿼리 벡터로 상태에서 정보를 검색한다.

$$o_t = S_t q_t$$

SSM과의 연결을 명확히 하면, GLA의 상태 업데이트는 선택적 SSM과 구조적으로 동일하다.

$$\underbrace{S_t = G_t \odot S_{t-1} + k_t^T v_t}_{\text{GLA}} \quad \leftrightarrow \quad \underbrace{h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t}_{\text{Selective SSM}}$$

GLA의 $G_t$는 Mamba의 $\bar{A}_t$에, $k_t^T v_t$는 $\bar{B}_t x_t$에 대응한다.

### 행렬 수준 게이팅의 차별점

GLA의 핵심 차별점은 **행렬 수준의 게이팅**이다. Mamba의 선택적 메커니즘은 상태 벡터의 각 차원에 스칼라 게이트를 적용하지만, GLA는 KV 상태 행렬의 각 원소에 독립적인 게이트를 적용한다.

| 모델 | 게이트 차원 | 상태 형태 | 게이트 파라미터 수 |
|------|-----------|---------|------------------|
| GLA | $(d_k \times d_v)$ 행렬 | $(d_k \times d_v)$ 행렬 | $d_k \times d_v$ |
| Mamba | $D$ 스칼라 | $(D \times N)$ 행렬 | $D$ |
| RetNet | 스칼라 $\gamma$ | $(d_k \times d_v)$ 행렬 | 1 (고정) |

### GLA Transformer

GLA Transformer는 표준 Transformer 레이어에서 MHA를 GLA로 교체한 구조이다. FFN은 SwiGLU를 사용하며, 정규화는 RMSNorm을 적용한다. 각 GLA 헤드는 독립적인 KV 상태를 유지하며, 멀티-헤드 구조로 다양한 패턴을 동시에 포착한다.

### 청크 단위 효율적 구현

순환 연산을 직접 GPU에서 수행하면 메모리 대역폭에 병목이 발생한다. GLA는 시퀀스를 청크(chunk) 단위로 분할하여, 청크 내부에서는 행렬 곱셈(BLAS 연산)을 활용한 병렬 계산을 수행하고, 청크 간에서는 순환적으로 상태를 전파한다.

$$Y_{\text{chunk}} = \underbrace{(G_{\text{intra}} \odot Q_c K_c^T) V_c}_{\text{intra-chunk (BLAS)}} + \underbrace{Q_c \cdot G_{\text{inter}} \cdot S_{\text{prev}}}_{\text{inter-chunk (recurrence)}}$$

이 chunkwise recurrence 전략으로 FlashAttention과 유사한 처리 속도를 달성했다.

## 핵심 혁신

GLA의 핵심 혁신은 두 가지이다.

첫째, **데이터 의존적 망각**이다. RetNet의 고정 감쇠율 $\gamma$와 달리, GLA의 게이트는 입력에 따라 동적으로 결정된다. 모델이 문맥에 따라 "이 정보는 오래 기억하고, 저 정보는 빨리 잊어라"라는 판단을 할 수 있게 해준다.

둘째, **행렬 수준 게이팅의 세밀한 제어**이다. 스칼라 게이트(Mamba)나 고정 감쇠(RetNet)보다 더 세밀한 키-값 쌍 간 상호작용 제어가 가능하다.

## 벤치마크/성능

| 모델 (1.3B) | Pile PPL↓ | ARC-C | HellaSwag | WinoGrande |
|------------|-----------|-------|-----------|------------|
| GLA | 8.32 | 35.2 | 64.3 | 60.1 |
| RetNet | 8.67 | 33.8 | 62.1 | 58.7 |
| RWKV-4 | 8.54 | 34.1 | 63.0 | 59.2 |
| Transformer++ | 8.15 | 36.5 | 66.1 | 61.3 |
| Mamba | 8.28 | 35.8 | 65.2 | 60.8 |

| 모델 | 게이트 유형 | KV 상태 | 추론 메모리 | 학습 방식 |
|------|-----------|---------|-----------|----------|
| GLA | 행렬 게이트(입력 의존) | 행렬 | $O(1)$ | Chunkwise |
| RetNet | 스칼라 감쇠(고정) | 행렬 | $O(1)$ | 병렬/순환 |
| Mamba | 스칼라 게이트(입력 의존) | 벡터 | $O(1)$ | Parallel scan |
| Transformer | Softmax attention | KV cache | $O(N)$ | 완전 병렬 |

## 학습

RedPajama, SlimPajama 등 공개 데이터셋으로 학습하며, A100 GPU를 사용한다. 청크 크기 256으로 chunkwise 학습을 수행한다. LLaMA 학습 설정을 준수하여 공정한 비교를 보장하며, 1.3B 모델 기준 약 100B 토큰으로 학습한다.

다음은 GLA의 게이트 선형 어텐션을 구현한 예시이다.

```python
import torch
import torch.nn as nn

class GatedLinearAttention(nn.Module):
    def __init__(self, d_model, d_key, d_value, n_heads):
        super().__init__()
        self.d_key = d_key
        self.d_value = d_value
        self.n_heads = n_heads
        self.W_q = nn.Linear(d_model, n_heads * d_key)
        self.W_k = nn.Linear(d_model, n_heads * d_key)
        self.W_v = nn.Linear(d_model, n_heads * d_value)
        self.W_g = nn.Linear(d_model, n_heads * d_key * d_value)
        self.W_o = nn.Linear(n_heads * d_value, d_model)

    def forward_recurrent(self, x_t, S_prev):
        """순환 모드: O(1) 메모리 추론"""
        q = self.W_q(x_t).view(-1, self.n_heads, self.d_key)
        k = self.W_k(x_t).view(-1, self.n_heads, self.d_key)
        v = self.W_v(x_t).view(-1, self.n_heads, self.d_value)
        
        # 행렬 게이트 계산 (데이터 의존적)
        G = torch.sigmoid(self.W_g(x_t)).view(
            -1, self.n_heads, self.d_key, self.d_value
        )
        
        # 게이트 선형 어텐션 상태 업데이트
        # S_t = G_t * S_{t-1} + k_t^T @ v_t
        S_t = G * S_prev + torch.einsum('bhk,bhv->bhkv', k, v)
        
        # 출력: o_t = S_t @ q_t
        o_t = torch.einsum('bhkv,bhk->bhv', S_t, q)
        return self.W_o(o_t.reshape(-1, self.n_heads * self.d_value)), S_t
```

## 관련 모델

GLA는 flash-linear-attention 라이브러리를 통해 PyTorch 환경에서 쉽게 사용할 수 있다. Transformer의 MHA를 GLA로 교체하는 것만으로 추론 시 $O(1)$ 메모리를 달성할 수 있다. GLA의 주요 한계인 in-context retrieval 성능은 후속 연구인 Gated DeltaNet에서 delta rule을 결합하는 방향으로 발전했다. GLA는 선형 어텐션 연구에서 "데이터 의존적 게이팅"이라는 핵심 원칙을 확립한 중요한 모델이다.

## 참고 자료

- 논문: [Gated Linear Attention Transformers with Hardware-Efficient Training](https://arxiv.org/abs/2312.06635)
- 코드: [fla-org/flash-linear-attention](https://github.com/fla-org/flash-linear-attention)

## 관련 문서

- [[retnet|RetNet]] — 영감
