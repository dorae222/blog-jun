# Transformer: Attention Is All You Need

## 개요

2017년 6월, Google Brain과 Google Research의 Ashish Vaswani 등이 발표한 **"Attention Is All You Need"** 논문은 딥러닝 역사의 분기점이 된 작업이다. 이 논문에서 제안된 **Transformer** 아키텍처는 당시 NLP 시퀀스 모델링의 주류였던 RNN(Recurrent Neural Network)과 LSTM(Long Short-Term Memory)의 근본적 한계—순차 처리로 인한 병렬화 불가, 장거리 의존성 소실—를 **Self-Attention 메커니즘 하나만으로 완전히 해결**했다.

Transformer 이전에는 시퀀스를 처리하려면 반드시 시간 축을 따라 순차적으로 계산해야 했다. 이는 GPU의 병렬 연산 능력을 충분히 활용할 수 없게 만들었고, 수백 토큰 이상의 장거리 의존성을 포착하기 어려웠다. Transformer는 이 모든 제약을 제거하고, 입력 시퀀스의 **모든 위치 쌍 간의 관계를 동시에 계산**할 수 있는 구조를 제시했다.

## 아키텍처 상세

### 전체 구조: Encoder-Decoder

아래 그림은 Transformer의 전체 아키텍처로, 왼쪽의 인코더와 오른쪽의 디코더로 구성된 구조를 보여준다.

![Transformer 전체 아키텍처 — 인코더-디코더 구조와 각 서브레이어 구성](figures/fig_1.png)
*Figure 1: Transformer 모델 아키텍처 — 인코더(왼쪽)와 디코더(오른쪽) 각 N개 레이어로 구성되며, Multi-Head Attention, Feed Forward, Add & Norm 서브레이어가 반복된다. (Source: Vaswani et al., 2017)*

Transformer는 **인코더(Encoder)**와 **디코더(Decoder)** 각각 6개의 동일한 레이어를 쌓은 구조다.

- **인코더**: Self-Attention + Feed-Forward Network (FFN)
- **디코더**: Masked Self-Attention + Cross-Attention + FFN

각 서브레이어에는 **Residual Connection**과 **Post-LayerNorm**이 적용된다:

$$\text{output} = \text{LayerNorm}(x + \text{SubLayer}(x))$$

### Scaled Dot-Product Attention

Transformer의 핵심 연산은 **Scaled Dot-Product Attention**이다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

여기서 $Q$(Query), $K$(Key), $V$(Value)는 입력 시퀀스의 선형 변환이며, $d_k$는 Key의 차원이다. $\sqrt{d_k}$로 스케일링하는 이유는 $d_k$가 커질수록 내적값의 분산이 커져 softmax가 극단적으로 편향되는 것을 방지하기 위함이다.

다음 두 그림은 Scaled Dot-Product Attention의 연산 흐름과 Multi-Head Attention의 병렬 구조를 각각 보여준다.

![Scaled Dot-Product Attention 연산 흐름 — Q, K, V 입력부터 출력까지의 단계](figures/fig_2_1.png)
*Figure 2a: Scaled Dot-Product Attention — Q와 K의 행렬 곱 후 스케일링, 선택적 마스킹, Softmax를 거쳐 V와 곱하는 과정. (Source: Vaswani et al., 2017)*

![Multi-Head Attention 구조 — 여러 어텐션 헤드의 병렬 실행과 결합](figures/fig_2_2.png)
*Figure 2b: Multi-Head Attention — 입력을 h개 헤드로 분리하여 병렬 어텐션을 수행한 뒤 Concat하고 선형 변환하는 구조. (Source: Vaswani et al., 2017)*

### Multi-Head Attention (MHA)

단일 어텐션 대신 **여러 개의 헤드**로 병렬 어텐션을 수행한다:

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, ..., \text{head}_h)W^O$$
$$\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$$

Base 모델은 8개 헤드($h=8$), 각 헤드의 차원 $d_k = d_v = d_{\text{model}}/h = 64$이다. 이를 통해 서로 다른 표현 부분 공간(representation subspace)에서 다양한 관계 패턴을 동시에 학습할 수 있다.

### Position-wise Feed-Forward Network

각 어텐션 레이어 뒤에는 두 개의 선형 변환과 ReLU 활성화로 구성된 FFN이 위치한다:

$$\text{FFN}(x) = \max(0, xW_1 + b_1)W_2 + b_2$$

FFN의 내부 차원은 $d_{ff} = 2048$로, 어텐션 차원($d_{\text{model}} = 512$)의 4배다. 이 4배 비율은 이후 거의 모든 Transformer 변형에서 표준이 되었다.

### Sinusoidal Positional Encoding

Self-Attention은 순서 정보를 포함하지 않으므로, **위치 인코딩**을 명시적으로 주입해야 한다. Transformer는 학습 없이 사인·코사인 함수를 사용한다:

$$PE_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$
$$PE_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

이 방식의 장점은 학습 데이터에서 보지 못한 더 긴 시퀀스에도 외삽(extrapolation)이 가능하다는 점이다.

### PyTorch 구현 예시

```python
import torch
import torch.nn as nn
import math

class ScaledDotProductAttention(nn.Module):
    def forward(self, Q, K, V, mask=None):
        d_k = Q.size(-1)
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(d_k)
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        attn = torch.softmax(scores, dim=-1)
        return torch.matmul(attn, V), attn

class MultiHeadAttention(nn.Module):
    def __init__(self, d_model=512, n_heads=8):
        super().__init__()
        self.d_k = d_model // n_heads
        self.n_heads = n_heads
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)
        self.W_o = nn.Linear(d_model, d_model)
        self.attention = ScaledDotProductAttention()

    def forward(self, Q, K, V, mask=None):
        B = Q.size(0)
        Q = self.W_q(Q).view(B, -1, self.n_heads, self.d_k).transpose(1, 2)
        K = self.W_k(K).view(B, -1, self.n_heads, self.d_k).transpose(1, 2)
        V = self.W_v(V).view(B, -1, self.n_heads, self.d_k).transpose(1, 2)
        out, attn = self.attention(Q, K, V, mask)
        out = out.transpose(1, 2).contiguous().view(B, -1, self.n_heads * self.d_k)
        return self.W_o(out)
```

## 핵심 혁신

### 1. Self-Attention: O(1) 깊이의 장거리 의존성

다음 시각화는 인코더 Self-Attention(레이어 5)에서 장거리 의존성을 포착하는 과정을 보여준다. 단어 "making"에 대한 어텐션이 먼 거리에 위치한 "more difficult"를 정확히 연결하고 있다.

![Self-Attention의 장거리 의존성 포착 — 'making...more difficult' 구문 연결](figures/fig_3.png)
*Figure 3: 장거리 의존성 어텐션 시각화 — 인코더 레이어 5에서 "making"이 멀리 떨어진 "more difficult"에 어텐션을 집중하여 구문적 의존성을 포착한다. 색상은 서로 다른 헤드를 나타낸다. (Source: Vaswani et al., 2017)*

RNN에서 거리 $n$만큼 떨어진 두 위치를 연결하려면 $O(n)$ 단계가 필요하지만, Self-Attention은 **$O(1)$** 단계로 임의의 두 위치를 직접 연결한다. 다만 계산 복잡도는 시퀀스 길이 $n$에 대해 $O(n^2)$으로, 이는 이후 Efficient Transformer 연구의 주요 동기가 되었다.

### 2. 완전한 병렬화

모든 위치의 어텐션을 동시에 계산할 수 있으므로 GPU 활용도가 극대화된다. P100 GPU 8개로 Base 모델은 12시간, Large 모델은 3.5일 만에 학습이 완료되었다.

### 3. 모듈형 설계의 범용성

Encoder-Decoder 구조는 번역뿐 아니라 다양한 시퀀스-투-시퀀스 태스크에 적용 가능하다. 이후 BERT는 Encoder만, GPT는 Decoder만 사용하는 변형이 등장했다.

아래 시각화는 서로 다른 어텐션 헤드가 문장의 구조적 관계를 학습하는 모습을 보여준다. 각 헤드가 구문 분석, 수식어 관계 등 서로 다른 언어적 패턴에 특화됨을 확인할 수 있다.

![어텐션 헤드별 문장 구조 학습 — 서로 다른 구문적 패턴을 포착하는 헤드들](figures/fig_5_1.png)
*Figure 5: 어텐션 헤드의 구조적 학습 — 인코더 레이어 5의 서로 다른 헤드가 문장 구조와 관련된 다양한 패턴을 학습하는 모습. 각 헤드가 명확히 다른 역할을 수행한다. (Source: Vaswani et al., 2017)*

## 벤치마크/성능

WMT 2014 기계 번역 벤치마크 결과:

| 모델 | EN-DE BLEU | EN-FR BLEU | 학습 비용 (FLOPs) |
|------|-----------|-----------|------------------|
| GNMT+RL (2016) | 24.6 | 39.92 | $2.3 \times 10^{19}$ |
| ConvS2S (2017) | 25.16 | 40.46 | $1.5 \times 10^{20}$ |
| **Transformer Base** | **27.3** | **38.1** | $3.3 \times 10^{18}$ |
| **Transformer Large** | **28.4** | **41.8** | $2.3 \times 10^{19}$ |

Transformer Large는 EN-DE에서 기존 앙상블 모델을 포함한 모든 결과를 **2 BLEU 이상** 앞질렀으며, EN-FR에서는 단일 모델로 **41.8 BLEU** SOTA를 달성했다. 특히 학습 비용은 기존 최고 모델의 1/4 수준이었다.

## 관련 모델 비교

| 특성 | RNN/LSTM | CNN (ConvS2S) | Transformer |
|------|----------|---------------|-------------|
| 시퀀스 병렬화 | 불가 | 부분 가능 | **완전 가능** |
| 장거리 의존성 | $O(n)$ | $O(\log n)$ | **$O(1)$** |
| 레이어당 복잡도 | $O(n \cdot d^2)$ | $O(k \cdot n \cdot d^2)$ | $O(n^2 \cdot d)$ |
| 학습 속도 | 느림 | 보통 | **빠름** |
| 이후 영향력 | 감소 | 제한적 | **GPT, BERT, T5 등 전체** |

## 실무 활용

Transformer는 현재 NLP뿐 아니라 다양한 분야에서 핵심 아키텍처로 사용된다:

- **기계 번역**: Google Translate, DeepL 등 상용 번역 시스템의 기반
- **언어 모델**: GPT 시리즈, BERT, T5 등 모든 현대 LLM
- **컴퓨터 비전**: Vision Transformer(ViT), DETR 등
- **음성 처리**: Whisper, wav2vec 2.0
- **단백질 구조 예측**: AlphaFold 2
- **코드 생성**: Codex, GitHub Copilot

Hugging Face Transformers 라이브러리를 통해 수천 개의 사전 학습 모델을 즉시 활용할 수 있다.

## 한계 및 전망

### 한계

1. **$O(n^2)$ 메모리/연산 복잡도**: 시퀀스 길이의 제곱에 비례하는 어텐션 행렬 계산은 긴 시퀀스 처리의 병목이다
2. **위치 외삽 한계**: Sinusoidal Encoding은 이론적으로 외삽 가능하지만, 실제로는 학습 길이를 크게 벗어나면 성능이 저하된다
3. **Post-Norm 불안정성**: 깊은 네트워크에서 Post-Norm은 학습 초기 불안정을 초래할 수 있다 (이후 Pre-Norm이 표준이 됨)

### 전망 및 후속 연구

- **Efficient Attention**: Linear Attention, Flash Attention 등 $O(n)$ 복잡도 근사 기법
- **위치 인코딩 발전**: RoPE(Rotary Position Embedding), ALiBi 등 외삽 성능 개선
- **Pre-Norm 채택**: GPT-2 이후 거의 모든 대형 모델이 Pre-Norm으로 전환
- **Mixture of Experts**: 파라미터 효율성을 위한 조건부 계산

Transformer는 단순히 하나의 모델이 아니라, 현대 AI의 **공통 언어**이자 **설계 철학**이다. 2017년 이후 등장한 거의 모든 주요 AI 모델은 Transformer의 변형이거나 Transformer에서 영감을 받은 구조다.

---

**참고 논문**: [Attention Is All You Need](https://arxiv.org/abs/1706.03762) (Vaswani et al., 2017)

## 관련 문서

- [[bart|BART]] — 후속 모델
- [[bert|BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding]] — 후속 모델
- [[clip|CLIP]] — 후속 모델
- [[cohere-command-a|Cohere Command A]] — 후속 모델
- [[detr|DETR]] — 후속 모델
- [[gpt-1|GPT-1]] — 후속 모델
- [[t5|T5]] — 후속 모델
- [[vit|An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale]] — 후속 모델
- [[whisper|Whisper]] — 후속 모델
- [[xlnet|XLNet]] — 후속 모델
- [[fnet|FNet]] — 영감을 줌
- [[retnet|RetNet]] — 영감을 줌
- [[rwkv|RWKV]] — 영감을 줌
