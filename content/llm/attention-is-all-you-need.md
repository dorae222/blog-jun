---
title: Attention Is All You Need
slug: "attention-is-all-you-need"
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.390758+00:00"
architecture_entry: transformer
---

## 개요

"Attention Is All You Need"(Vaswani et al., 2017)는 자연어 처리 분야에서 가장 혁신적인 논문 중 하나로, **Transformer** 아키텍처를 처음으로 제안했습니다. 기존의 RNN이나 CNN을 완전히 제거하고, 오직 Self-Attention 메커니즘만을 사용하여 시퀀스-투-시퀀스 학습을 수행합니다. 영어-독일어 번역에서 28.4 BLEU, 영어-프랑스어 번역에서 41.0 BLEU라는 당시 SOTA 성능을 달성했습니다.

## 배경 및 문제 정의

2017년 이전까지 시퀀스 모델링의 주류는 LSTM, GRU 같은 RNN이었습니다. RNN 계열 모델은 다음과 같은 근본적인 한계를 가지고 있었습니다:

- **순차 계산(Sequential computation)**: 시퀀스를 순서대로 처리해야 하므로 병렬화가 불가능
- **장기 의존성 문제(Long-range dependency)**: 시퀀스가 길어질수록 먼 위치의 정보를 유지하기 어려움
- **기울기 소실(Vanishing gradient)**: 역전파 시 오랜 시간 단계를 거치면 기울기가 사라짐

Attention 메커니즘은 이미 RNN과 함께 사용되고 있었지만, Vaswani et al.은 RNN 자체를 제거하고 Attention만으로 모든 것을 처리할 수 있다는 대담한 가설을 제시했습니다.

## 핵심 아이디어

### Scaled Dot-Product Attention

Transformer의 핵심은 **Scaled Dot-Product Attention**입니다. Query $Q$, Key $K$, Value $V$ 행렬이 주어지면:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

여기서 $d_k$는 키 벡터의 차원입니다. $\sqrt{d_k}$로 나누는 스케일링은 내적값이 너무 커져 softmax 기울기가 소실되는 것을 방지합니다.

### Multi-Head Attention

단일 Attention 대신 여러 Attention을 병렬로 수행하는 **Multi-Head Attention**을 사용합니다:

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)W^O$$

$$\text{head}_i = \text{Attention}(QW_i^Q, KW_i^K, VW_i^V)$$

각 헤드는 서로 다른 표현 부분 공간(representation subspace)에서 정보를 독립적으로 학습합니다. 논문에서는 $h=8$개의 헤드를 사용하며, $d_k = d_v = d_{\text{model}}/h = 64$로 설정합니다.

### Positional Encoding

Attention은 위치 정보가 없으므로, 다음과 같은 **Positional Encoding (Sinusoidal)**을 임베딩에 더합니다:

$$PE_{(pos, 2i)} = \sin\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

$$PE_{(pos, 2i+1)} = \cos\left(\frac{pos}{10000^{2i/d_{\text{model}}}}\right)$$

이 설계는 모델이 상대적 위치를 쉽게 학습할 수 있도록 해줍니다.

## 아키텍처 / 방법론

Transformer는 **Encoder-Decoder** 구조로 이루어져 있습니다.

### Encoder

인코더는 $N=6$개의 동일한 레이어로 구성되며, 각 레이어는:
1. **Multi-Head Self-Attention** 서브레이어
2. **Position-wise Feed-Forward Network** 서브레이어

각 서브레이어에는 Residual Connection과 Layer Normalization가 적용됩니다:

$$\text{LayerOutput} = \text{LayerNorm}(x + \text{Sublayer}(x))$$

### Decoder

디코더도 $N=6$개의 레이어로 구성되며, 인코더와 달리 세 번째 서브레이어로 **Cross-Attention**(인코더 출력에 대한 Multi-Head Attention)이 추가됩니다. 또한 Self-Attention에는 미래 위치를 보지 못하도록 **마스킹(Masking)**이 적용됩니다.

### Feed-Forward Network

각 레이어의 FFN은 두 선형 변환 사이에 ReLU를 적용합니다:

$$\text{FFN}(x) = \max(0, xW_1 + b_1)W_2 + b_2$$

$d_{\text{model}} = 512$, $d_{\text{ff}} = 2048$을 사용합니다.

## 실험 결과

### Machine Translation (WMT 2014)

| 모델 | EN-DE BLEU | EN-FR BLEU | Training Cost (FLOPs) |
|------|-----------|-----------|------------------|
| ByteNet | 23.75 | - | - |
| ConvS2S | 25.16 | 40.46 | 9.6×10¹⁸ |
| MoE | 26.03 | 40.56 | 2.0×10¹⁹ |
| Transformer (base) | 27.3 | 38.1 | 3.3×10¹⁸ |
| **Transformer (big)** | **28.4** | **41.0** | **2.3×10¹⁹** |

Transformer(big)는 앙상블 모델 대비 2 BLEU 이상 개선되었으며, 학습 비용은 경쟁 모델 대비 훨씬 낮습니다.

### Ablation Study

| 모델 변형 | EN-DE BLEU |
|----------|----------|
| heads = 1 | 25.9 |
| 헤드 수 = 8 (기본) | 27.3 |
| $d_k$ 축소 | 26.9 |
| Dropout 제거 | 26.9 |

## 의의 및 한계

### 의의

- **병렬 처리**: 모든 위치를 동시에 처리할 수 있어 GPU 활용도가 극적으로 향상
- **장거리 의존성**: 두 위치 사이의 경로 길이가 $O(1)$로, RNN의 $O(n)$에 비해 훨씬 효율적
- **확장성**: 모델 크기를 쉽게 늘릴 수 있어 이후 BERT, GPT, T5 등 수많은 모델의 기반이 됨
- **범용성**: 번역 외 텍스트 요약, 질의응답, 이미지 처리(ViT) 등 다양한 도메인으로 확장

### 한계

- **2차 복잡도**: Self-Attention의 계산 복잡도가 시퀀스 길이 $n$에 대해 $O(n^2)$이므로 매우 긴 시퀀스 처리에 제약이 있음
- **Positional Encoding의 한계**: 사인·코사인 인코딩은 학습되지 않으며, 훈련 시 보지 못한 길이의 시퀀스에 일반화하기 어려울 수 있음
- **데이터 효율성**: RNN에 비해 학습에 더 많은 데이터가 필요한 경향이 있음

이후 연구들은 Sparse Attention(Longformer, BigBird), 상대적 Positional Encoding(RoPE, ALiBi), Flash Attention 등으로 이러한 한계를 극복해 나가고 있습니다.\n\n## 코드 예제\n\n### Scaled Dot-Product Attention (PyTorch)\n\n```python\nimport torch\nimport torch.nn as nn\nimport torch.nn.functional as F\nimport math\n\ndef scaled_dot_product_attention(Q, K, V, mask=None):\n    \"\"\"Scaled Dot-Product Attention 구현.\n    Args:\n        Q: Query (batch, heads, seq_len, d_k)\n        K: Key   (batch, heads, seq_len, d_k)\n        V: Value (batch, heads, seq_len, d_v)\n        mask: 마스킹 텐서 (선택적)\n    \"\"\"\n    d_k = Q.size(-1)\n    # 어텐션 스코어 계산: QK^T / sqrt(d_k)\n    scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(d_k)\n    if mask is not None:\n        scores = scores.masked_fill(mask == 0, float('-inf'))\n    attn_weights = F.softmax(scores, dim=-1)\n    return torch.matmul(attn_weights, V), attn_weights\n\nclass MultiHeadAttention(nn.Module):\n    def __init__(self, d_model=512, num_heads=8):\n        super().__init__()\n        assert d_model % num_heads == 0\n        self.d_k = d_model // num_heads\n        self.num_heads = num_heads\n        self.W_q = nn.Linear(d_model, d_model)\n        self.W_k = nn.Linear(d_model, d_model)\n        self.W_v = nn.Linear(d_model, d_model)\n        self.W_o = nn.Linear(d_model, d_model)\n\n    def forward(self, Q, K, V, mask=None):\n        batch = Q.size(0)\n        # 선형 변환 후 헤드로 분리\n        Q = self.W_q(Q).view(batch, -1, self.num_heads, self.d_k).transpose(1, 2)\n        K = self.W_k(K).view(batch, -1, self.num_heads, self.d_k).transpose(1, 2)\n        V = self.W_v(V).view(batch, -1, self.num_heads, self.d_k).transpose(1, 2)\n        x, _ = scaled_dot_product_attention(Q, K, V, mask)\n        # 헤드 합치기\n        x = x.transpose(1, 2).contiguous().view(batch, -1, self.num_heads * self.d_k)\n        return self.W_o(x)\n\nclass PositionalEncoding(nn.Module):\n    def __init__(self, d_model=512, max_len=5000):\n        super().__init__()\n        pe = torch.zeros(max_len, d_model)\n        position = torch.arange(0, max_len).unsqueeze(1).float()\n        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))\n        pe[:, 0::2] = torch.sin(position * div_term)  # 짝수 인덱스: sin\n        pe[:, 1::2] = torch.cos(position * div_term)  # 홀수 인덱스: cos\n        self.register_buffer('pe', pe.unsqueeze(0))  # (1, max_len, d_model)\n\n    def forward(self, x):\n        return x + self.pe[:, :x.size(1)]\n\n# 사용 예시\nd_model, num_heads, seq_len, batch = 512, 8, 10, 4\nmha = MultiHeadAttention(d_model, num_heads)\npe = PositionalEncoding(d_model)\nx = torch.randn(batch, seq_len, d_model)\nx_pos = pe(x)              # positional encoding 추가\nout = mha(x_pos, x_pos, x_pos)  # self-attention (Q=K=V)\nprint(out.shape)           # (4, 10, 512)\n```