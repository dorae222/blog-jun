# BERT: Bidirectional Encoder Representations from Transformers

## 개요

**BERT**(Bidirectional Encoder Representations from Transformers)는 2018년 10월 Google AI Language가 발표한 **양방향 사전 학습 언어 모델**이다. Transformer의 인코더 스택만을 활용해 문맥을 **양방향으로 동시에 처리**한다는 점에서, GPT 계열의 단방향(왼→오) 언어 모델과 근본적으로 차별화된다.

핵심 혁신은 **MLM(Masked Language Modeling)**이다. 문장 내 임의 15% 토큰을 마스킹하고 이를 예측하도록 학습함으로써, 왼쪽과 오른쪽 문맥을 **동시에** 활용하는 깊은 양방향 표현을 학습한다. GLUE 벤치마크 80.2점, SQuAD 1.1 F1 93.2점 등 **11개 NLP 태스크에서 SOTA**를 경신하며, 사전학습-미세조정 패러다임을 NLP의 표준으로 확립했다.

아래 그림은 BERT의 사전 학습과 미세조정 전체 흐름을 보여준다. 동일한 아키텍처가 사전 학습과 미세조정 모두에 사용되며, 출력 레이어만 태스크에 따라 교체된다.

![BERT 사전 학습 및 미세조정 전체 절차 - MLM/NSP 사전 학습에서 다운스트림 태스크 미세조정으로](figures/fig_1.png)
*Figure 1: BERT 사전 학습 및 미세조정 절차 - (좌) MLM과 NSP로 사전 학습하고, (우) 동일한 사전 학습 파라미터를 MNLI, NER, SQuAD 등 다양한 다운스트림 태스크의 초기화에 사용한다. 미세조정 시 모든 파라미터를 업데이트한다. (Source: Devlin et al., 2018)*

## 아키텍처 상세

### Transformer Encoder 기반

BERT는 Transformer의 **인코더 부분만** 사용한다. 디코더와 Cross-Attention이 없으므로, 모든 위치가 다른 모든 위치를 양방향으로 참조할 수 있다. 이는 GPT 계열이 사용하는 Transformer 디코더의 Causal Mask(미래 토큰 참조 차단)와 대조적으로, BERT는 입력 시퀀스의 모든 토큰이 다른 모든 토큰에 자유롭게 어텐션을 수행할 수 있다.

| 모델 | 레이어 | Hidden | 헤드 | FFN | 파라미터 |
|------|--------|--------|------|-----|----------|
| BERT-Base | 12 | 768 | 12 | 3072 | **110M** |
| BERT-Large | 24 | 1024 | 16 | 4096 | **340M** |

BERT-Base는 GPT-1과 동일한 모델 크기로 설계되어 공정한 비교를 가능하게 했으며, BERT-Large는 당시 기준으로 상당히 큰 규모의 모델이었다. 두 모델 모두 GELU 활성화 함수를 사용하며, 드롭아웃 비율은 0.1이다.

### 입력 표현

BERT의 입력은 세 가지 임베딩의 합이다:

$$E_{\text{input}} = E_{\text{token}} + E_{\text{segment}} + E_{\text{position}}$$

아래 그림은 이 세 가지 임베딩이 결합되는 과정을 구체적으로 보여준다.

![BERT 입력 표현 - Token, Segment, Position 임베딩의 합](figures/fig_2.png)
*Figure 2: BERT 입력 표현 구조 - Token Embedding, Segment Embedding(문장 A/B 구분), Position Embedding 세 가지를 합산하여 최종 입력 벡터를 구성한다. (Source: Devlin et al., 2018)*

- **Token Embedding**: WordPiece 토크나이저(30,522 vocab)
- **Segment Embedding**: 문장 A/B 구분 (`[SEP]` 토큰으로 분리)
- **Position Embedding**: Learned Absolute (최대 512)

특수 토큰:
- `[CLS]`: 시퀀스 시작, 분류 태스크의 대표 토큰
- `[SEP]`: 두 문장 구분자
- `[MASK]`: MLM에서 마스킹된 위치

### WordPiece 토크나이저

BERT는 **WordPiece** 서브워드 토크나이저를 사용한다. WordPiece는 BPE(Byte Pair Encoding)의 변형으로, 학습 코퍼스에서 빈도가 높은 문자 조합을 반복적으로 병합하여 30,522개의 어휘를 구축한다. 핵심 원리는 다음과 같다:

1. 초기에 모든 문자를 개별 토큰으로 시작한다.
2. 가장 빈번하게 인접하는 토큰 쌍을 찾아 하나의 새 토큰으로 병합한다.
3. 원하는 어휘 크기에 도달할 때까지 이 과정을 반복한다.

예를 들어 "embedding"이라는 단어는 어휘에 없을 경우 `["em", "##bed", "##ding"]`처럼 분리된다. `##` 접두사는 해당 토큰이 단어의 시작이 아님을 표시한다. 이 방식은 미등록 단어(OOV) 문제를 효과적으로 해결하면서도, 빈번한 단어는 하나의 토큰으로 유지하여 효율성을 확보한다. WordPiece 토크나이저는 대소문자를 구분하지 않는 `bert-base-uncased`와 구분하는 `bert-base-cased` 두 가지 버전으로 제공된다.

### 사전학습 목적함수

#### 1. MLM (Masked Language Modeling)

입력 토큰의 15%를 선택하여:
- **80%**: `[MASK]` 토큰으로 교체
- **10%**: 랜덤 토큰으로 교체
- **10%**: 원본 그대로 유지

$$\mathcal{L}_{\text{MLM}} = -\sum_{i \in \mathcal{M}} \log P(x_i | \tilde{x})$$

여기서 $\mathcal{M}$은 마스킹된 위치 집합, $\tilde{x}$는 마스킹된 입력이다.

**80/10/10 마스킹 전략의 설계 근거**: 만약 마스킹된 위치를 100% `[MASK]` 토큰으로만 대체하면, 모델은 `[MASK]`가 등장할 때만 예측을 수행하면 된다고 학습하게 된다. 그러나 미세조정 단계에서는 `[MASK]` 토큰이 전혀 등장하지 않으므로, 사전학습과 미세조정 사이의 분포 불일치(distribution mismatch)가 발생한다. 10%를 랜덤 토큰으로 교체하면 모델이 "이 위치의 토큰이 올바른 것인지"를 판단하는 능력을 갖추게 되고, 10%를 원본 그대로 유지하면 모델이 실제 입력 분포에서도 올바른 표현을 출력하도록 유도한다. 논문의 ablation 실험에서 이 비율이 최적임을 확인했으며, 80/20/0이나 100/0/0 대비 약 0.2~0.5%p의 성능 향상을 보였다.

또한, 15%라는 마스킹 비율 자체도 의미 있는 설계 결정이다. 비율이 너무 높으면 문맥 정보가 부족해져 예측이 어려워지고, 너무 낮으면 학습 신호가 부족하여 수렴이 느려진다. BERT 저자들은 실험을 통해 15%가 양방향 문맥 활용과 학습 효율 사이의 최적 균형점임을 확인했다.

#### 2. NSP (Next Sentence Prediction)

두 문장이 실제로 연속되는지 이진 분류:

$$P(\text{IsNext} | [\text{CLS}]) = \sigma(W \cdot h_{[\text{CLS}]}^L)$$

50%는 실제 연속 문장(IsNext), 50%는 랜덤 문장(NotNext)으로 구성한다. NSP의 설계 의도는 QA(질의응답)나 NLI(자연어 추론)처럼 두 문장 간의 관계를 이해해야 하는 다운스트림 태스크를 위한 것이었다.

**NSP에 대한 후속 비판**: 그러나 이후 연구들에서 NSP의 실질적 효용에 대한 논란이 제기되었다. RoBERTa(2019)는 NSP를 제거하고 더 많은 데이터와 긴 학습을 적용했을 때 오히려 성능이 향상됨을 보였다. 주요 비판은 다음과 같다:

1. **태스크 난이도 부족**: 랜덤으로 선택된 NotNext 문장은 대부분 완전히 다른 주제이므로, 모델이 단순히 토픽 일치 여부만으로도 높은 정확도를 달성할 수 있다. 실질적인 문장 간 논리적 관계를 학습한다고 보기 어렵다.
2. **MLM과의 간섭**: NSP 태스크가 MLM의 양방향 표현 학습을 오히려 방해할 수 있다는 분석이 있다.
3. **대안적 접근**: ALBERT는 SOP(Sentence Order Prediction)라는 대안을 제시하여, 같은 문서 내 두 문장의 순서를 맞추는 보다 어려운 태스크로 대체했다.

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

ELMo는 순방향과 역방향 LSTM을 **독립적으로** 학습한 뒤 결합했지만, BERT는 Self-Attention을 통해 **모든 위치가 동시에 양방향 문맥을 참조**한다. 아래 그림은 세 모델의 아키텍처 차이를 명확히 보여준다.

![BERT, OpenAI GPT, ELMo의 사전 학습 아키텍처 비교](figures/fig_3.png)
*Figure 3: 사전 학습 아키텍처 비교 - BERT는 양방향 Transformer로 모든 레이어에서 좌우 문맥을 동시에 참조한다. OpenAI GPT는 왼→오 단방향, ELMo는 독립적으로 학습된 양방향 LSTM의 결합이다. (Source: Devlin et al., 2018)*

이로 인해 "bank"의 의미가 "river bank"인지 "bank account"인지를 더 정확하게 구분할 수 있다.

### 2. MLM: 새로운 사전학습 목적함수

MLM은 자기회귀 LM(GPT)의 단방향 제약을 극복하는 핵심 아이디어다. 마스킹된 토큰을 예측하려면 좌우 문맥을 **모두** 활용해야 하므로, 진정한 양방향 표현이 학습된다.

### 3. 범용 미세조정

`[CLS]` 토큰 위에 단순한 분류 레이어만 추가하면 분류, NLI, QA 등 다양한 태스크를 수행할 수 있다. 아래 그림은 네 가지 대표적 다운스트림 태스크에서의 미세조정 방식을 보여준다.

![BERT의 다양한 다운스트림 태스크 미세조정 - 문장 쌍 분류, 단일 문장 분류, QA, 태깅](figures/fig_4.png)
*Figure 4: BERT 미세조정 태스크별 구성 - (좌상) 문장 쌍 분류, (우상) 단일 문장 분류, (좌하) 추출적 QA(Start/End 스팬 예측), (우하) 시퀀스 태깅(NER 등). 모든 태스크에서 동일한 BERT 구조를 사용하며 출력 레이어만 변경한다. (Source: Devlin et al., 2018)*

태스크별로 전체 모델을 미세조정하되, 아키텍처 변경은 최소화한다. 구체적으로 각 다운스트림 태스크의 미세조정 방식은 다음과 같다:

- **문장/문서 분류 (Sentiment, Topic)**: `[CLS]` 토큰의 최종 히든 벡터 $h_{[\text{CLS}]}$에 분류 레이어 $W \in \mathbb{R}^{K \times H}$를 곱하여 $K$개 클래스에 대한 확률을 출력한다. SST-2(감성 분석), CoLA(문법 판단) 등이 이 범주에 속한다.
- **문장 쌍 분류 (NLI, Paraphrase)**: 두 문장을 `[SEP]`로 연결한 뒤, 동일하게 `[CLS]`의 출력으로 관계를 분류한다. MNLI(자연어 추론), QQP(중복 질문 탐지) 등이 해당된다.
- **추출적 질의응답 (SQuAD)**: 질문과 문맥을 입력으로 넣고, 문맥 내 각 토큰이 답변의 시작(Start) 또는 끝(End)일 확률을 예측한다. Start와 End 각각에 별도의 선형 레이어를 사용하며, 가장 높은 확률의 스팬을 답변으로 추출한다.
- **시퀀스 태깅 (NER, POS)**: 각 토큰의 최종 히든 벡터에 태깅 분류 레이어를 적용하여, 토큰별로 B-PER, I-LOC 등의 태그를 예측한다. 이때 WordPiece로 분리된 서브워드는 첫 번째 서브워드의 예측만을 사용한다.

미세조정의 하이퍼파라미터는 대부분의 태스크에서 유사하다: 배치 크기 16 또는 32, 학습률 $2 \times 10^{-5}$ ~ $5 \times 10^{-5}$, 에폭 수 2~4. 이 좁은 범위 내에서도 안정적으로 수렴하는 것이 BERT 미세조정의 강점이다.

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

## 역사적 의의

BERT의 등장은 NLP 분야에서 **"ImageNet moment"**로 불릴 만큼 패러다임 전환적 사건이었다. BERT 이전의 NLP는 각 태스크마다 별도의 아키텍처를 설계하고, 작은 규모의 레이블 데이터로 처음부터 학습하는 방식이 일반적이었다. BERT는 이 관행을 완전히 뒤바꾸었다.

첫째, **사전학습-미세조정 패러다임의 대중화**이다. 대규모 비라벨 텍스트로 범용 언어 표현을 학습한 뒤, 소량의 라벨 데이터로 미세조정하는 전이 학습이 NLP의 기본 접근법으로 자리잡았다. 이는 컴퓨터 비전에서 ImageNet 사전학습 + 미세조정이 표준이 된 것과 같은 흐름이다.

둘째, **연구 커뮤니티의 폭발적 확장**이다. BERT 논문은 arXiv 공개 후 단기간에 수만 회 인용되었으며, "BERTology"라는 연구 분야가 형성될 정도로 BERT의 내부 표현을 분석하는 연구가 쏟아졌다. Probing 실험을 통해 BERT의 각 레이어가 구문론(syntax)에서 의미론(semantics)까지 계층적으로 언어 정보를 인코딩한다는 사실이 밝혀졌다.

셋째, **산업 적용의 가속화**이다. Google 검색 엔진은 2019년 BERT를 검색 랭킹에 도입하여, 전치사나 부정어의 의미를 더 정확하게 파악하는 등 검색 품질을 크게 개선했다. 이는 단일 모델이 상용 검색 엔진에 적용된 가장 영향력 있는 사례 중 하나이다.

## 한계 및 과제

### 구조적 한계

1. **양방향이지만 생성 불가**: BERT는 양방향 문맥을 활용하여 뛰어난 이해(understanding) 능력을 보이지만, 텍스트를 순차적으로 생성하는 태스크에는 구조적으로 적합하지 않다. 자기회귀적 디코딩이 불가능하므로, 요약, 번역, 대화 등 생성 태스크에서는 GPT 계열이나 T5 같은 Encoder-Decoder 모델에 비해 열세이다.
2. **고정된 컨텍스트 길이 (512 토큰)**: 학습된 포지션 임베딩이 512 위치까지만 존재하므로, 긴 문서나 다중 문서 처리에 한계가 있다. 법률 문서, 학술 논문, 책 등 긴 텍스트를 다루려면 Longformer나 BigBird 같은 후속 모델이 필요하다.
3. **사전학습-미세조정 불일치**: `[MASK]` 토큰이 미세조정에는 등장하지 않음
4. **토큰 독립 가정**: 마스킹된 토큰들 간의 상관관계를 무시. 예를 들어 "New York"에서 "New"와 "York"이 동시에 마스킹되면, 두 토큰의 예측이 독립적으로 수행되어 "New Delhi"처럼 비일관적인 예측이 가능하다. XLNet은 Permutation Language Modeling으로 이 문제를 해결한다.
5. **학습 비효율**: 전체 토큰의 15%만 학습 신호로 활용하므로, 동일한 데이터에서 자기회귀 모델 대비 더 많은 학습 스텝이 필요하다. ELECTRA는 Replaced Token Detection으로 100% 토큰을 학습에 활용하여 이 비효율성을 해결했다.

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

- [[transformer|Transformer]] - 발전 기반
- [[albert|ALBERT]] - 후속 모델
- [[deberta|DeBERTa]] - 후속 모델
- [[electra|ELECTRA]] - 후속 모델
- [[roberta|RoBERTa]] - 후속 모델
- [[bart|BART]] - 영감을 줌
- [[ernie|ERNIE]] - 영감을 줌
- [[mae|MAE]] - 영감을 줌
- [[xlnet|XLNet]] - 영감을 줌
- [[distilbert|DistilBERT]] - 변형 모델
