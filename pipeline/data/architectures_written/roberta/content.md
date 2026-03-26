# RoBERTa: Robustly Optimized BERT Pretraining Approach

## 개요

**RoBERTa**(Robustly Optimized BERT Pretraining Approach)는 2019년 7월 Meta FAIR(Facebook AI Research)가 발표한 모델이다. 가장 놀라운 점은 **아키텍처를 전혀 변경하지 않고** BERT의 학습 방식과 데이터만을 대폭 개선하여, BERT를 훨씬 능가하는 성능을 달성했다는 것이다.

핵심 발견은 단순하지만 강력하다: **BERT는 심각하게 학습 부족(undertrained) 상태**였다. NSP 태스크 제거, 동적 마스킹, 더 큰 배치, 10배 더 많은 데이터라는 네 가지 변화만으로 GLUE 88.5점, SQuAD 2.0 89.4 F1을 기록하며, **학습 레시피의 중요성**을 NLP 커뮤니티에 각인시켰다.

## 아키텍처 상세

### BERT와 동일한 아키텍처

RoBERTa는 BERT-Large와 **정확히 동일한 아키텍처**를 사용한다:

| 하이퍼파라미터 | BERT-Large | RoBERTa-Large |
|-------------|------------|---------------|
| 레이어 | 24 | 24 |
| Hidden | 1024 | 1024 |
| 어텐션 헤드 | 16 | 16 |
| FFN | 4096 | 4096 |
| 파라미터 | 340M | **355M** |

파라미터 차이(340M vs 355M)는 토크나이저 변경에 따른 임베딩 레이어 크기 차이뿐이다.

### 4가지 핵심 변경

#### 1. NSP(Next Sentence Prediction) 제거

BERT의 NSP 태스크가 실제로는 성능에 **해로울 수 있음**을 실험적으로 입증했다.

| 설정 | MNLI | SST-2 | SQuAD 1.1 |
|------|------|-------|----------|
| Segment-Pair + NSP (BERT 원본) | 84.0 | 92.4 | 90.4 |
| Sentence-Pair + NSP | 82.9 | 92.6 | 89.0 |
| Full-Sentences (NSP 제거) | **86.2** | **93.7** | **90.9** |
| Doc-Sentences (NSP 제거) | **86.2** | **93.3** | 90.8 |

**Full-Sentences** 방식(문서 경계를 넘어 연속된 문장으로 512 토큰을 채움)이 가장 우수했다.

#### 2. 동적 마스킹 (Dynamic Masking)

BERT는 사전학습 데이터 전처리 시 마스킹 패턴을 **한 번만 생성**한다. RoBERTa는 에포크마다 **새로운 마스킹 패턴을 동적으로 생성**하여, 동일한 데이터를 다양한 각도로 학습한다:

$$\tilde{x}^{(e)} = \text{DynamicMask}(x, p=0.15), \quad e = 1, 2, \ldots, E$$

에포크 $e$마다 서로 다른 마스크가 적용되므로, 모델이 특정 마스킹 패턴에 과적합되는 것을 방지한다.

#### 3. 더 큰 배치와 더 긴 학습

| 설정 | BERT | RoBERTa |
|------|------|---------|
| 배치 크기 | 256 | **8000** |
| 학습 스텝 | 1M (128+512) | **500K (512 전용)** |
| 총 토큰 | ~137B | **~2T** |

더 큰 배치는 더 안정적인 그래디언트 추정을 제공하며, 학습 효율도 향상시킨다.

#### 4. 더 많은 데이터 (160GB)

| 데이터셋 | 크기 | 비고 |
|---------|------|------|
| BooksCorpus + Wikipedia | 16GB | BERT 원본 |
| + CC-News | +76GB | 뉴스 기사 |
| + OpenWebText | +38GB | Reddit 링크 (GPT-2 재현) |
| + Stories | +31GB | CommonCrawl 이야기체 |
| **합계** | **~160GB** | BERT의 **10배** |

### Byte-level BPE 토크나이저

BERT의 WordPiece(30,522 vocab)를 GPT-2에서 도입된 **Byte-level BPE(50,265 vocab)**로 교체했다. 이를 통해 OOV 문제를 완전히 제거했다.

## 핵심 혁신

### 1. "학습 레시피가 전부다" 입증

RoBERTa의 가장 큰 기여는 **아키텍처 혁신 없이도 학습 방법론만으로 큰 성능 향상이 가능**하다는 것을 보여준 것이다. 이는 이후 Chinchilla 등 학습 효율성 연구의 선구적 사례다.

### 2. NSP의 무용성 증명

BERT의 NSP 태스크가 오히려 성능을 **저하**시킬 수 있음을 실험적으로 입증했다. 이후 ALBERT(SOP로 대체), XLNet(NSP 없음) 등 후속 모델들이 NSP를 제거하는 근거가 되었다.

### 3. 체계적 ablation 연구

각 요소(NSP, 마스킹, 배치, 데이터)의 기여를 하나씩 분리하여 측정하는 **체계적 ablation** 방법론은 NLP 연구의 실험 방법론 표준을 높였다.

## 벤치마크/성능

| 벤치마크 | BERT-Large | RoBERTa-Large | 개선폭 |
|---------|-----------|-------------|-------|
| GLUE | 80.2 | **88.5** | +8.3 |
| MNLI | 86.7 | **90.2** | +3.5 |
| SQuAD 1.1 (F1) | 93.2 | **94.6** | +1.4 |
| SQuAD 2.0 (F1) | 89.1 | **89.4** | +0.3 |
| RACE | 72.0 | **83.2** | +11.2 |
| SST-2 | 94.9 | **96.4** | +1.5 |

## 관련 모델 비교

| 특성 | BERT | RoBERTa | XLNet | ALBERT |
|------|------|---------|-------|--------|
| NSP | Yes | **No** | No | SOP |
| 마스킹 | Static | **Dynamic** | Permutation | Static |
| 배치 | 256 | **8000** | - | 4096 |
| 데이터 | 16GB | **160GB** | - | 16GB |
| Tokenizer | WordPiece | **Byte-level BPE** | SentencePiece | SentencePiece |
| GLUE | 80.2 | **88.5** | 90.5 | 89.4 |
| 아키텍처 변경 | - | **없음** | PLM | 파라미터 공유 |

## 실무 활용

### Hugging Face 사용

```python
from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch

tokenizer = RobertaTokenizer.from_pretrained('roberta-large')
model = RobertaForSequenceClassification.from_pretrained('roberta-large', num_labels=3)

inputs = tokenizer("Natural language processing is fascinating.", return_tensors="pt")
outputs = model(**inputs)
logits = outputs.logits
```

### 주요 활용

1. **범용 NLU 베이스라인**: 다양한 NLU 태스크의 강력한 기준 모델
2. **도메인 적응**: 추가 사전학습(continual pre-training) 후 도메인별 미세조정
3. **다국어 확장**: XLM-RoBERTa로 100개 이상 언어 지원
4. **Feature Extraction**: 문장/토큰 임베딩 추출

## 한계 및 전망

### 한계

1. **학습 비용**: 160GB 데이터에 1024 V100 GPU 사용
2. **Encoder-only 한계**: 생성 태스크에는 부적합
3. **15% 학습 신호**: MLM의 근본적 비효율은 해결하지 못함 (ELECTRA에서 해결)
4. **컨텍스트 512**: 긴 문서 처리 어려움

### 전망

RoBERTa는 **"좋은 데이터와 충분한 학습이 아키텍처 혁신보다 중요할 수 있다"**는 교훈을 남겼다. 이 통찰은 이후 Chinchilla("데이터가 파라미터보다 중요"), LLaMA("작은 모델 + 더 많은 데이터") 등의 연구로 이어졌다.

---

**참고 논문**: [RoBERTa: A Robustly Optimized BERT Pretraining Approach](https://arxiv.org/abs/1907.11692) (Liu et al., 2019)

## 관련 문서

- [[bert|BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding]] — 발전 기반
