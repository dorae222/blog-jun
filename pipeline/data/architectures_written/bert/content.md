# BERT: Bidirectional Encoder Representations from Transformers

## 개요

**BERT**(Bidirectional Encoder Representations from Transformers)는 2018년 10월 Google AI Language가 발표한 **양방향 사전 학습 언어 모델**이다. Transformer의 인코더 스택만을 활용해 문맥을 **양방향으로 동시에 처리**한다는 점에서, GPT 계열의 단방향(왼→오) 언어 모델과 근본적으로 차별화된다.

핵심 혁신은 **MLM(Masked Language Modeling)**이다. 문장 내 임의 15% 토큰을 마스킹하고 이를 예측하도록 학습함으로써, 왼쪽과 오른쪽 문맥을 **동시에** 활용하는 깊은 양방향 표현을 학습한다. GLUE 벤치마크 80.2점, SQuAD 1.1 F1 93.2점 등 **11개 NLP 태스크에서 SOTA**를 경신하며, 사전학습-미세조정 패러다임을 NLP의 표준으로 확립했다.

## 아키텍처 상세

### Transformer Encoder 기반

BERT는 Transformer의 **인코더 부분만** 사용한다. 디코더와 Cross-Attention이 없으므로, 모든 위치가 다른 모든 위치를 양방향으로 참조할 수 있다.

| 모델 | 레이어 | Hidden | 헤드 | FFN | 파라미터 |
|------|--------|--------|------|-----|----------|
| BERT-Base | 12 | 768 | 12 | 3072 | **110M** |
| BERT-Large | 24 | 1024 | 16 | 4096 | **340M** |

### 입력 표현

BERT의 입력은 세 가지 임베딩의 합이다:

$$E_{\text{input}} = E_{\text{token}} + E_{\text{segment}} + E_{\text{position}}$$

- **Token Embedding**: WordPiece 토크나이저(30,522 vocab)
- **Segment Embedding**: 문장 A/B 구분 (`[SEP]` 토큰으로 분리)
- **Position Embedding**: Learned Absolute (최대 512)

특수 토큰:
- `[CLS]`: 시퀀스 시작, 분류 태스크의 대표 토큰
- `[SEP]`: 두 문장 구분자
- `[MASK]`: MLM에서 마스킹된 위치

### 사전학습 목적함수

#### 1. MLM (Masked Language Modeling)

입력 토큰의 15%를 선택하여:
- **80%**: `[MASK]` 토큰으로 교체
- **10%**: 랜덤 토큰으로 교체
- **10%**: 원본 그대로 유지

$$\mathcal{L}_{\text{MLM}} = -\sum_{i \in \mathcal{M}} \log P(x_i | \tilde{x})$$

여기서 $\mathcal{M}$은 마스킹된 위치 집합, $\tilde{x}$는 마스킹된 입력이다. 80/10/10 비율은 사전학습과 미세조정 사이의 불일치(mismatch)를 줄이기 위한 것이다.

#### 2. NSP (Next Sentence Prediction)

두 문장이 실제로 연속되는지 이진 분류:

$$P(\text{IsNext} | [\text{CLS}]) = \sigma(W \cdot h_{[\text{CLS}]}^L)$$

50%는 실제 연속 문장(IsNext), 50%는 랜덤 문장(NotNext)으로 구성한다.

### PyTorch 구현 예시

```python
import torch
import torch.nn as nn

class BERTEmbedding(nn.Module):
    def __init__(self, vocab_size=30522, hidden=768, max_len=512, n_segments=2):
        super().__init__()
        self.token = nn.Embedding(vocab_size, hidden)
        self.position = nn.Embedding(max_len, hidden)
        self.segment = nn.Embedding(n_segments, hidden)
        self.norm = nn.LayerNorm(hidden)
        self.dropout = nn.Dropout(0.1)

    def forward(self, token_ids, segment_ids):
        pos = torch.arange(token_ids.size(1), device=token_ids.device)
        x = self.token(token_ids) + self.position(pos) + self.segment(segment_ids)
        return self.dropout(self.norm(x))

class BERTModel(nn.Module):
    def __init__(self, vocab_size=30522, hidden=768, n_layers=12, n_heads=12):
        super().__init__()
        self.embedding = BERTEmbedding(vocab_size, hidden)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden, nhead=n_heads, dim_feedforward=hidden*4,
            activation='gelu', batch_first=True, dropout=0.1
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        # MLM Head
        self.mlm_head = nn.Linear(hidden, vocab_size)
        # NSP Head
        self.nsp_head = nn.Linear(hidden, 2)

    def forward(self, token_ids, segment_ids):
        x = self.embedding(token_ids, segment_ids)
        h = self.encoder(x)
        mlm_logits = self.mlm_head(h)  # 모든 위치
        nsp_logits = self.nsp_head(h[:, 0])  # [CLS] 토큰만
        return mlm_logits, nsp_logits
```

## 핵심 혁신

### 1. 깊은 양방향 표현

ELMo는 순방향과 역방향 LSTM을 **독립적으로** 학습한 뒤 결합했지만, BERT는 Self-Attention을 통해 **모든 위치가 동시에 양방향 문맥을 참조**한다. 이로 인해 "bank"의 의미가 "river bank"인지 "bank account"인지를 더 정확하게 구분할 수 있다.

### 2. MLM: 새로운 사전학습 목적함수

MLM은 자기회귀 LM(GPT)의 단방향 제약을 극복하는 핵심 아이디어다. 마스킹된 토큰을 예측하려면 좌우 문맥을 **모두** 활용해야 하므로, 진정한 양방향 표현이 학습된다.

### 3. 범용 미세조정

`[CLS]` 토큰 위에 단순한 분류 레이어만 추가하면 분류, NLI, QA 등 다양한 태스크를 수행할 수 있다. 태스크별로 전체 모델을 미세조정하되, 아키텍처 변경은 최소화한다.

## 벤치마크/성능

| 벤치마크 | BERT-Base | BERT-Large | 이전 SOTA |
|---------|-----------|-----------|----------|
| GLUE 전체 | 79.6 | **80.2** | 72.8 (GPT-1) |
| MNLI | 84.6 | **86.7** | 82.1 |
| SQuAD 1.1 (F1) | 88.5 | **93.2** | 91.6 |
| SQuAD 2.0 (F1) | 76.3 | **89.1** | 66.3 |
| MRPC | 87.4 | **89.3** | 86.0 |
| SST-2 | 93.5 | **94.9** | 93.2 |

11개 태스크 전체에서 SOTA를 달성했다.

## 관련 모델 비교

| 특성 | ELMo | GPT-1 | BERT | RoBERTa |
|------|------|-------|------|----------|
| 출시 | 2018.02 | 2018.06 | 2018.10 | 2019.07 |
| 구조 | BiLSTM | Transformer Dec | **Transformer Enc** | Transformer Enc |
| 방향성 | 양방향 (독립) | 단방향 | **양방향 (동시)** | 양방향 (동시) |
| 사전학습 | LM | LM | **MLM + NSP** | MLM만 |
| 전이 방식 | Feature-based | Fine-tuning | **Fine-tuning** | Fine-tuning |
| 데이터 | 1B 단어 | 5GB | **16GB** | 160GB |
| GLUE | 66.5 | 72.8 | **80.2** | 88.5 |

## 실무 활용

### Hugging Face로 바로 사용하기

```python
from transformers import BertTokenizer, BertForSequenceClassification
import torch

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertForSequenceClassification.from_pretrained('bert-base-uncased', num_labels=2)

inputs = tokenizer("이 영화는 정말 재미있었다!", return_tensors="pt", padding=True)
outputs = model(**inputs)
predicted = torch.argmax(outputs.logits, dim=-1)
```

### 주요 활용 분야

1. **텍스트 분류**: 감성 분석, 스팸 탐지, 주제 분류
2. **개체명 인식 (NER)**: 인명, 지명, 기관명 추출
3. **질의응답 (QA)**: SQuAD 스타일의 추출적 QA
4. **문장 유사도**: 의미적 유사도 계산
5. **검색 랭킹**: 문서 관련도 평가

## 한계 및 전망

### 한계

1. **사전학습-미세조정 불일치**: `[MASK]` 토큰이 미세조정에는 등장하지 않음
2. **NSP 효용 논란**: RoBERTa에서 NSP 제거 시 성능 향상 확인
3. **토큰 독립 가정**: 마스킹된 토큰들 간의 상관관계를 무시
4. **학습 비효율**: 전체 토큰의 15%만 학습 신호로 활용 (ELECTRA에서 해결)
5. **컨텍스트 512**: 긴 문서 처리 어려움

### 후속 모델과 발전

- **RoBERTa**: NSP 제거 + 더 많은 데이터/학습으로 성능 대폭 향상
- **ALBERT**: 파라미터 공유로 경량화
- **DeBERTa**: Disentangled Attention으로 위치 인코딩 개선
- **ELECTRA**: 100% 토큰 학습으로 효율 극대화
- **DistilBERT**: 지식 증류로 경량 모델 생성

BERT는 NLP의 **"ImageNet moment"**로 불리며, 사전학습-미세조정 패러다임의 폭발적 확산을 이끌었다. 2018년 이후 BERT 기반 변형 모델이 수백 개 등장했으며, 그 영향력은 현재까지 지속되고 있다.

---

**참고 논문**: [BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding](https://arxiv.org/abs/1810.04805) (Devlin et al., 2018)

## 관련 문서

- [[transformer|Transformer]] — 발전 기반
- [[albert|ALBERT]] — 후속 모델
- [[deberta|DeBERTa]] — 후속 모델
- [[electra|ELECTRA]] — 후속 모델
- [[roberta|RoBERTa]] — 후속 모델
- [[bart|BART]] — 영감을 줌
- [[ernie|ERNIE]] — 영감을 줌
- [[mae|MAE]] — 영감을 줌
- [[xlnet|XLNet]] — 영감을 줌
- [[distilbert|DistilBERT]] — 변형 모델
