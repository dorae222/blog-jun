---
title: "ALBERT: 경량 BERT의 파라미터 효율화"
slug: albert
category: llm
tags: ["ALBERT", "Cross-Layer Parameter Sharing", "Efficient Model", "Factorized Embedding", "glue", "Google", "Lite BERT", "Memory Efficient", "Parameter Sharing", "SOP"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.771137+00:00"
architecture_entry: albert
---

# ALBERT: 경량 BERT를 위한 자기지도 학습 언어 표현

**Google Research / Toyota Technological Institute at Chicago** · **2019-09-26** · **Encoder-only** · **Apache 2.0**

## 개요

ALBERT(A Lite BERT)는 2019년 9월 Google Research와 Toyota Technological Institute at Chicago(TTIC)가 공동 발표한 사전 학습 언어 모델이다. 이 모델은 BERT의 두 가지 근본적인 **메모리 비효율 문제**를 정면으로 해결하여, 파라미터 수를 대폭 줄이면서도 오히려 성능을 향상시키는 놀라운 결과를 달성했다.

![Architecture](figures/architecture.svg)

2019년 당시 NLP 분야는 "모델을 키우면 성능이 올라간다"는 스케일링 사고에 지배되어 있었다. BERT-Large(340M), XLNet, RoBERTa 등이 파라미터를 늘리며 경쟁하고 있었으나, 이는 GPU 메모리 제약으로 인해 학습과 배포에 점점 더 큰 부담을 주고 있었다. ALBERT는 이 문제에 대해 구조적 해법을 제시했다. 임베딩 행렬 분해(Factorized Embedding Parameterization)로 어휘 임베딩 크기와 히든 차원을 분리하고, 레이어 간 파라미터 공유(Cross-Layer Parameter Sharing)로 중복 학습을 제거했으며, NSP를 SOP(Sentence Order Prediction)로 대체하여 문장 간 관계 모델링을 강화했다. 결과적으로 BERT-Large 대비 **18배 적은 파라미터**로 GLUE 89.4점, SQuAD 2.0 92.2 F1을 기록하며 당시 SOTA를 달성했다.

이 연구는 모델 크기와 성능 사이의 트레이드오프에 대한 근본적인 재고를 촉발했으며, 이후 PEFT(Parameter-Efficient Fine-Tuning) 연구의 선구적 사례로 자리매김했다.

## 아키텍처 상세

### 임베딩 행렬 분해 (Factorized Embedding Parameterization)

BERT에서 어휘 임베딩 행렬은 $V \times H$ 크기를 가진다. 여기서 $V$는 어휘 크기, $H$는 히든 차원이다. BERT-Large에서 $V = 30,000$, $H = 1,024$이면 약 **30.7M 파라미터**가 임베딩에만 소비된다. 이것이 비효율적인 이유는 어휘 임베딩이 **문맥에 독립적(context-independent)**인 표현을 학습하는 반면, 히든 레이어는 **문맥에 의존적(context-dependent)**인 표현을 학습하기 때문이다. 두 표현의 차원이 반드시 동일할 필요가 없다.

ALBERT는 이 행렬을 두 개의 작은 행렬로 분해한다:

$$E_{V \times H} \rightarrow E_{V \times E} \cdot W_{E \times H}$$

여기서 $E$는 임베딩 차원($E \ll H$)이다. ALBERT는 $E = 128$을 사용하여:

- **BERT-Large**: $V \times H = 30,000 \times 1,024 = 30.7M$
- **ALBERT**: $V \times E + E \times H = 30,000 \times 128 + 128 \times 1,024 = 3.97M$

임베딩 파라미터만 **약 87% 절감**된다. XXLarge($H=4,096$)에서는 절감 효과가 더 극적이다: BERT의 $30,000 \times 4,096 = 122.9M$에서 $30,000 \times 128 + 128 \times 4,096 = 4.37M$으로 **96.4% 절감**된다.

### 레이어 간 파라미터 공유 (Cross-Layer Parameter Sharing)

모든 Transformer 레이어가 **동일한 가중치 세트**를 공유한다. 이는 기하학적으로 동일한 함수를 반복 적용하는 것과 같다:

$$h^{(l+1)} = f_\theta(h^{(l)}), \quad l = 0, 1, \ldots, L-1$$

모든 레이어가 동일한 $\theta$를 사용하므로, 파라미터 수가 레이어 수에 **무관하게 고정**된다. 공유 방식에 대한 ablation 실험 결과:

| 공유 방식 | MNLI | SST-2 | 파라미터 절감 |
|----------|------|-------|------------|
| 공유 없음 (BERT) | 85.6 | 92.8 | 0% |
| Attention만 공유 | 84.4 | 92.3 | ~33% |
| FFN만 공유 | 84.0 | 91.2 | ~67% |
| **전체 공유 (ALBERT)** | **84.6** | **91.6** | **~90%** |

전체 공유 시 성능 하락이 1점 내외로 미미한 반면, 파라미터 절감 효과는 압도적이다. 이는 Transformer의 각 레이어가 유사한 변환을 수행하며, 깊이보다는 **표현 공간의 폭(width)**이 더 중요할 수 있음을 시사한다.

### SOP (Sentence Order Prediction)

BERT의 NSP(Next Sentence Prediction)를 **SOP(Sentence Order Prediction)**로 대체한다:

- **NSP**: "두 문장이 연속인가?" -- 주로 주제 유사성(topic overlap)만 학습
- **SOP**: "두 연속 문장의 순서가 맞는가/바뀌었는가?" -- 문장 간 일관성과 논리적 순서를 학습

SOP가 더 어려운 태스크인 이유는, 순서가 바뀐 두 문장도 주제는 동일하기 때문에 모델이 순수하게 **논리적 일관성**을 판단해야 하기 때문이다.

| 사전학습 태스크 | NSP 평가 성능 | SOP 평가 성능 |
|-------------|------------|------------|
| NSP | 89.3% | 53.2% (거의 랜덤) |
| **SOP** | **87.2%** | **86.5%** |

NSP로 학습한 모델은 SOP를 사실상 풀지 못하지만, SOP로 학습한 모델은 NSP도 합리적으로 수행한다. 이는 SOP가 NSP의 상위 태스크임을 의미한다.

### 모델 변형 사양

| 모델 | 레이어 | Hidden | E | 헤드 | 파라미터 | BERT 대비 |
|------|--------|--------|---|------|---------|----------|
| ALBERT-Base | 12 | 768 | 128 | 12 | **12M** | 9x 절감 |
| ALBERT-Large | 24 | 1024 | 128 | 16 | **18M** | 18x 절감 |
| ALBERT-XLarge | 24 | 2048 | 128 | 16 | **60M** | 6x 절감 |
| ALBERT-XXLarge | 12 | 4096 | 128 | 64 | **235M** | - |

주목할 점은 ALBERT-XXLarge가 12레이어만으로 24레이어 BERT-Large(340M)를 능가한다는 것이다.

### PyTorch 핵심 구현

```python
import torch
import torch.nn as nn

class ALBERTEmbedding(nn.Module):
    """Factorized Embedding: V x E -> E x H"""
    def __init__(self, vocab_size=30000, embed_dim=128, hidden_dim=4096):
        super().__init__()
        self.word_embed = nn.Embedding(vocab_size, embed_dim)  # V x E
        self.projection = nn.Linear(embed_dim, hidden_dim)      # E x H

    def forward(self, input_ids):
        return self.projection(self.word_embed(input_ids))

class ALBERTModel(nn.Module):
    """Cross-Layer Parameter Sharing"""
    def __init__(self, vocab_size=30000, embed_dim=128, hidden_dim=4096,
                 n_heads=64, n_layers=12):
        super().__init__()
        self.embedding = ALBERTEmbedding(vocab_size, embed_dim, hidden_dim)
        # 단 하나의 공유 레이어
        self.shared_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim, nhead=n_heads,
            dim_feedforward=hidden_dim * 4, activation='gelu', batch_first=True
        )
        self.n_layers = n_layers

    def forward(self, input_ids):
        h = self.embedding(input_ids)
        for _ in range(self.n_layers):
            h = self.shared_layer(h)
        return h
```

## 핵심 혁신

### 1. 파라미터 효율성의 극대화

ALBERT-XXLarge(235M)가 12레이어만으로 BERT-Large(340M, 24레이어)를 능가한다. 이는 **파라미터 수보다 표현 능력의 폭(hidden dimension)**이 더 중요할 수 있음을 시사하며, 레이어를 깊게 쌓는 것이 항상 최선은 아님을 보여준다.

### 2. 스케일링의 새로운 방향

레이어 수를 늘리지 않고도 히든 차원을 키워 성능을 향상할 수 있음을 보였다. 이는 전통적인 "더 깊게(deeper)" 스케일링과 다른 **"더 넓게(wider)"** 접근법으로, 이후 Universal Transformer 등 파라미터 공유 연구에 직접적 영향을 미쳤다.

### 3. SOP의 우수성과 추론 속도 한계

NSP 대비 SOP가 다운스트림 태스크에서 일관되게 더 나은 성능을 보이지만, 중요한 한계가 있다. ALBERT는 파라미터 수는 줄지만 **추론 속도는 BERT와 거의 동일**하다. 파라미터 공유는 메모리 절감에는 효과적이지만, 계산량(FLOPs)은 줄이지 않기 때문이다.

## 벤치마크/성능

| 벤치마크 | BERT-Large (340M) | ALBERT-XXLarge (235M) | RoBERTa (356M) | 비고 |
|---------|------------------|---------------------|---------------|-----|
| GLUE | 80.2 | **89.4** | 88.5 | +9.2 vs BERT |
| SQuAD 1.1 (F1) | 93.2 | **94.1** | 94.6 | 동등 수준 |
| SQuAD 2.0 (F1) | 89.1 | **92.2** | 89.8 | +3.1 vs BERT |
| RACE | 72.0 | **89.4** | 83.2 | +17.4 vs BERT |
| SuperGLUE | - | **87.7** | 84.6 | SOTA |

ALBERT-XXLarge는 BERT-Large 대비 **파라미터 약 31% 절감**하면서 모든 벤치마크에서 크게 앞서며, 특히 RACE(+17.4)에서 압도적 우위를 보인다.

## 학습

- **데이터**: BooksCorpus + English Wikipedia (16GB, BERT와 동일)
- **사전학습 태스크**: MLM + SOP
- **배치 크기**: 4,096
- **옵티마이저**: LAMB (lr=0.00176)
- **학습 스텝**: 1M
- **하드웨어**: 64~1,024 TPU v3 칩

## 관련 모델

ALBERT는 BERT를 직접 계승하면서, DistilBERT(지식 증류), ELECTRA(효율적 사전학습)와 함께 BERT 효율화 연구의 세 축을 형성한다. 특히 레이어 간 파라미터 공유 개념은 이후 LoRA, Adapter 등 PEFT 방법론의 이론적 선구자가 되었으며, DeBERTa의 분리 어텐션과 함께 인코더 모델의 구조적 혁신을 대표한다.

## 참고 자료

- [ALBERT: A Lite BERT for Self-supervised Learning of Language Representations](https://arxiv.org/abs/1909.11942) (Lan et al., 2019)
- [코드](https://github.com/google-research/albert)

## 관련 문서

- [[bert|BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding]] — 발전 기반
