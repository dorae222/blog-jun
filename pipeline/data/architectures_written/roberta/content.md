# RoBERTa: Robustly Optimized BERT Pretraining Approach

## 개요

**RoBERTa**(Robustly Optimized BERT Pretraining Approach)는 2019년 7월 Meta FAIR(Facebook AI Research)가 발표한 모델이다. 가장 놀라운 점은 **아키텍처를 전혀 변경하지 않고** BERT의 학습 방식과 데이터만을 대폭 개선하여, BERT를 훨씬 능가하는 성능을 달성했다는 것이다.

핵심 발견은 단순하지만 강력하다: **BERT는 심각하게 학습 부족(undertrained) 상태**였다. NSP 태스크 제거, 동적 마스킹, 더 큰 배치, 10배 더 많은 데이터라는 네 가지 변화만으로 GLUE 88.5점, SQuAD 2.0 89.4 F1을 기록하며, **학습 레시피의 중요성**을 NLP 커뮤니티에 각인시켰다.

## 아키텍처 상세

![RoBERTa 학습 최적화 아키텍처](figures/architecture.png)

*Figure 1: RoBERTa의 BERT-Large 동일 아키텍처와 4가지 핵심 학습 최적화 구조. (Liu et al., 2019)*

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

BERT의 WordPiece(30,522 vocab)를 GPT-2에서 도입된 **Byte-level BPE(50,265 vocab)**로 교체했다. 이를 통해 OOV(Out-of-Vocabulary) 문제를 완전히 제거했다.

WordPiece와 Byte-level BPE의 핵심 차이는 기본 단위에 있다. WordPiece는 유니코드 문자를 기본 단위로 사용하므로, 어휘에 없는 문자는 `[UNK]` 토큰으로 대체된다. 반면 Byte-level BPE는 **바이트(256개)**를 기본 단위로 사용하므로, 어떤 텍스트든 바이트 시퀀스로 분해할 수 있어 이론적으로 OOV가 발생하지 않는다.

어휘 크기의 증가(30,522 -> 50,265)는 임베딩 레이어의 파라미터 증가(약 15M)를 초래하여, 전체 파라미터가 340M에서 355M으로 약간 증가하였다. 그러나 이 차이는 모델 전체 규모 대비 미미하며, 더 풍부한 서브워드 표현이 가능해져 특히 코드, URL, 전문 용어 등 비정형 텍스트에서의 표현력이 향상되었다. 또한 Byte-level BPE는 사전 토큰화(pre-tokenization) 과정이 불필요하여, 전처리 파이프라인이 더 단순해진다는 실무적 장점도 있다.

### 학습 데이터 구성 상세

RoBERTa의 160GB 학습 데이터는 BERT의 16GB(BookCorpus + English Wikipedia) 대비 **10배** 규모이며, 네 가지 소스로 구성된다:

1. **BookCorpus + Wikipedia (16GB)**: BERT 원본과 동일한 기본 데이터셋. 정제된 문어체 텍스트로 기본 언어 능력의 토대를 제공한다.
2. **CC-News (76GB)**: CommonCrawl에서 추출한 영어 뉴스 기사 6,300만 건. 시사, 정치, 경제 등 다양한 도메인의 최신 텍스트를 포함하며, 사실 관계 추론과 지식 획득에 기여한다.
3. **OpenWebText (38GB)**: Reddit에서 3회 이상 추천받은 링크의 웹 페이지를 수집한 데이터셋. GPT-2의 학습 데이터(WebText)를 재현한 것으로, 다양한 주제와 문체를 포함한다.
4. **Stories (31GB)**: CommonCrawl에서 이야기체(narrative) 텍스트만을 필터링한 데이터셋. Winograd Schema Challenge 스타일의 상식 추론 능력 향상에 기여한다.

이 데이터 다양성은 모델이 단순히 더 많은 텍스트를 보는 것을 넘어, **다양한 도메인과 문체에 걸쳐 일반화된 언어 표현**을 학습하도록 한다. 이는 이후 GPT-3, LLaMA 등 대규모 모델의 데이터 큐레이션 전략에 영향을 미쳤다.

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

### GLUE 벤치마크 상세 분석

GLUE(General Language Understanding Evaluation)에서 RoBERTa의 88.5점은 발표 당시 단일 모델 기준 최고 성능이었다. 개별 태스크별로 분석하면:

- **MNLI (90.2)**: 자연어 추론에서 3.5점 향상. 전제와 가설 간의 논리적 관계를 판단하는 태스크로, 대규모 데이터에서 학습된 풍부한 문맥 이해가 기여하였다.
- **QQP (92.2)**: 질문 쌍의 의미적 동등성 판별에서 우수한 성능. Byte-level BPE의 유연한 서브워드 처리가 다양한 표현 방식을 포착하는 데 도움이 되었다.
- **QNLI (98.9)**: 질문-문단 관계 판별에서 거의 완벽에 가까운 성능. Full-Sentences 학습으로 긴 문맥에서의 정보 추출 능력이 강화되었다.
- **SST-2 (96.4)**: 감성 분류에서 1.5점 향상. 동적 마스킹이 감성 표현의 다양한 패턴을 학습하는 데 효과적이었다.

### SQuAD 벤치마크 분석

SQuAD(Stanford Question Answering Dataset)에서의 성능 향상은 벤치마크에 따라 차이를 보인다. SQuAD 1.1에서는 F1 기준 1.4점 향상(93.2 -> 94.6)으로 상당한 개선을 보인 반면, SQuAD 2.0에서는 0.3점(89.1 -> 89.4)의 소폭 향상에 그쳤다. SQuAD 2.0은 답이 없는 질문을 포함하므로, "답변 불가능" 판단에는 학습 레시피 변경만으로는 큰 향상이 어려웠음을 시사한다.

### RACE 벤치마크의 극적 향상

RACE(Reading Comprehension from Examinations)에서의 11.2점 향상(72.0 -> 83.2)은 RoBERTa의 모든 벤치마크 중 가장 극적인 개선이다. RACE는 중국 중고등학교 영어 시험의 독해 문제로 구성되며, 긴 지문에서의 추론과 다중 선택이 필요하다. 이 극적인 향상은 160GB의 다양한 텍스트 데이터가 장문 이해와 상식 추론 능력을 크게 강화했음을 보여준다.

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

## NLP 분야에 미친 영향

RoBERTa의 발표는 NLP 연구 방향에 중대한 전환점이 되었다.

### 학습 레시피 연구의 촉발

RoBERTa 이전에는 BERT의 성능을 넘기 위해 아키텍처 변경이 필수적이라는 암묵적 가정이 있었다. XLNet은 Permutation Language Modeling을, ALBERT는 파라미터 공유를 도입하는 등 구조적 혁신에 집중하였다. 그러나 RoBERTa가 **아키텍처 변경 없이** 이들 모델과 대등하거나 우수한 성능을 달성함으로써, "기존 아키텍처를 제대로 학습시키기만 해도 큰 성능 향상이 가능하다"는 사실이 입증되었다.

이 교훈은 이후 NLP를 넘어 컴퓨터 비전(DeiT: 데이터 효율적 ViT 학습), 음성 처리(wav2vec 2.0) 등 다양한 분야에서 "학습 레시피 최적화"라는 연구 트렌드를 형성하였다.

### 후속 모델에 대한 직접적 영향

RoBERTa의 학습 레시피는 후속 모델들에 직접 채택되었다:

- **XLM-RoBERTa**: RoBERTa의 학습 방법론을 100개 이상 언어의 CommonCrawl 데이터에 적용하여, 다국어 NLU의 새로운 기준을 수립하였다.
- **ELECTRA**: NSP 제거라는 RoBERTa의 발견을 계승하면서, MLM의 15% 비효율 문제를 Replaced Token Detection으로 해결하였다.
- **DeBERTa**: RoBERTa의 학습 레시피를 기반으로 disentangled attention을 추가하여 SuperGLUE에서 인간 성능을 초과하였다.
- **Chinchilla/LLaMA**: "데이터양과 학습 충분성이 핵심"이라는 RoBERTa의 통찰은, 스케일링 법칙 연구의 선구적 사례로 자주 인용된다.

## 한계 및 과제

### 한계

1. **학습 비용**: 160GB 데이터에 1024 V100 GPU를 사용하여 약 1일간 학습하였다. 당시 기준으로도 상당한 컴퓨팅 자원이며, 대부분의 연구 그룹이 이를 재현하기 어려운 규모였다. 이는 "더 많은 데이터, 더 큰 배치"라는 레시피 자체가 컴퓨팅 자원에 비례하는 접근법이라는 한계를 내포한다.
2. **Encoder-only 한계**: Transformer 인코더만을 사용하므로 텍스트 생성, 번역, 요약 등 시퀀스-투-시퀀스 태스크에는 직접 적용이 불가능하다. 이러한 태스크에는 T5, BART 등 인코더-디코더 구조나 GPT 계열의 디코더 모델이 필요하다.
3. **15% 학습 신호**: MLM은 입력 토큰의 15%만을 마스킹하여 예측하므로, 각 학습 스텝에서 전체 토큰의 85%는 학습 신호를 생성하지 않는다. 이는 ELECTRA의 Replaced Token Detection(모든 토큰에서 학습 신호 생성)과 비교하면 근본적으로 비효율적이다. ELECTRA는 RoBERTa의 1/4 컴퓨팅으로 유사한 성능을 달성하였다.
4. **컨텍스트 512**: 최대 512 토큰의 입력 길이 제한은 긴 문서(법률 문서, 논문, 소설 등)의 처리에 심각한 제약이 된다. Longformer, BigBird 등이 이 문제를 해결하기 위해 제안되었다.
5. **정적 임베딩 크기**: 모든 토큰에 동일한 1024차원 임베딩을 사용하므로, 빈출 토큰(the, is)과 희소 토큰(비전문 용어)에 동일한 표현력을 할당한다는 비효율이 있다.
6. **단일 언어 한계**: RoBERTa-Large는 영어 전용 모델로, 다국어 환경에서는 XLM-RoBERTa를 별도로 학습해야 한다.

### 전망

RoBERTa는 **"좋은 데이터와 충분한 학습이 아키텍처 혁신보다 중요할 수 있다"**는 교훈을 남겼다. 이 통찰은 이후 Chinchilla("데이터가 파라미터보다 중요"), LLaMA("작은 모델 + 더 많은 데이터") 등의 연구로 이어졌다. 2026년 현재, LLM 시대에서도 RoBERTa는 분류, NER, 감성 분석 등 NLU 특화 태스크에서 여전히 실무 베이스라인으로 널리 활용되고 있으며, 그 "학습 레시피 최적화"라는 철학은 AI 연구 전반에 깊이 각인되어 있다.

---

**참고 논문**: [RoBERTa: A Robustly Optimized BERT Pretraining Approach](https://arxiv.org/abs/1907.11692) (Liu et al., 2019)

## 관련 문서

- [[bert|BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding]] — 발전 기반
