# BART: 양방향 인코더와 자기회귀 디코더의 결합

## 개요

BART(Bidirectional and Auto-Regressive Transformers)는 2019년 10월 Meta AI(당시 Facebook AI Research, FAIR)가 발표한 시퀀스-투-시퀀스(Seq2Seq) 사전 학습 모델이다. 핵심 아이디어는 매우 단순하면서도 강력하다: **텍스트를 다양한 방식으로 손상(corrupt)시킨 후 원본을 복원하도록 학습**하는 노이즈 제거 오토인코더(Denoising Autoencoder) 구조를 채택한 것이다.

BART 이전에는 BERT(양방향 인코더)와 GPT(자기회귀 디코더)가 각각 이해(understanding)와 생성(generation) 태스크에서 강점을 보였지만, 두 능력을 동시에 갖춘 모델은 부재했다. BART는 이 두 패러다임을 인코더-디코더 구조로 통합하여, 이해와 생성 모두에서 뛰어난 성능을 달성했다.

- **논문**: [BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension](https://arxiv.org/abs/1910.13461)
- **코드**: [fairseq (GitHub)](https://github.com/facebookresearch/fairseq)
- **라이선스**: Apache 2.0

## 아키텍처 상세

### 전체 구조

BART는 표준 Transformer 인코더-디코더 구조를 따른다:

$$\text{BART} = \text{Bidirectional Encoder} + \text{Autoregressive Decoder}$$

| 구성 요소 | BART-Base | BART-Large |
|-----------|-----------|------------|
| 파라미터 수 | 139M | 406M |
| 인코더 레이어 | 6 | 12 |
| 디코더 레이어 | 6 | 12 |
| Hidden Dim | 768 | 1024 |
| Attention Heads | 12 | 16 |
| Vocab Size | 50,265 | 50,265 |
| Context Length | 1024 | 1024 |

### 인코더

인코더는 BERT와 동일한 **양방향(Bidirectional) Self-Attention**을 사용한다. 입력 시퀀스의 모든 위치가 다른 모든 위치를 참조할 수 있어, 문맥의 양방향 정보를 완전히 활용한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

### 디코더

디코더는 GPT와 동일한 **인과적(Causal) Self-Attention**을 사용하되, 추가로 인코더의 모든 레이어에 대해 **Cross-Attention**을 수행한다. 이를 통해 인코더가 포착한 풍부한 양방향 문맥을 디코더가 직접 활용할 수 있다.

### 위치 인코딩

BART는 **Learned Absolute Position Embedding**을 사용한다. 최대 1024개 위치에 대한 학습 가능한 벡터를 토큰 임베딩에 더한다.

## 핵심 혁신: 5가지 노이즈 함수

BART의 진정한 혁신은 사전 학습에 사용되는 **5가지 노이즈 함수(Noise Function)**에 있다:

### 1. Token Masking
BERT와 동일하게 임의 토큰을 `[MASK]`로 대체한다.

### 2. Token Deletion
임의 토큰을 완전히 삭제한다. 마스킹과 달리 모델이 **삭제된 위치까지 추론**해야 하므로 더 어려운 태스크이다.

### 3. Text Infilling
가장 혁신적인 노이즈 함수이다. 포아송 분포($\lambda = 3$)로 샘플링한 길이의 텍스트 범위(span)를 **단일 `[MASK]` 토큰**으로 대체한다:

$$\text{span length} \sim \text{Poisson}(\lambda = 3)$$

모델은 마스크 하나에서 **몇 개의 토큰이 빠졌는지(길이 예측)**까지 학습해야 한다.

### 4. Sentence Permutation
문서 내 문장들의 순서를 무작위로 뒤섞는다.

### 5. Document Rotation
문서의 임의 위치를 새로운 시작점으로 설정하여 회전시킨다.

실험 결과, **Text Infilling + Sentence Permutation** 조합이 가장 강력한 성능을 보였다.

```python
import torch
from transformers import BartForConditionalGeneration, BartTokenizer

# BART-Large-CNN 로드 (요약 파인튜닝 버전)
tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')

# 입력 텍스트
article = """BART is a denoising autoencoder for pretraining sequence-to-sequence models.
It is trained by corrupting text with an arbitrary noising function,
and learning a model to reconstruct the original text."""

# 요약 생성
inputs = tokenizer(article, return_tensors='pt', max_length=1024, truncation=True)
summary_ids = model.generate(
    inputs['input_ids'],
    num_beams=4,
    max_length=142,
    min_length=56,
    length_penalty=2.0
)
summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
print(summary)
```

## 벤치마크/성능

BART-Large는 발표 당시 여러 생성 태스크에서 SOTA를 달성했다:

| 벤치마크 | 메트릭 | BART-Large | 이전 SOTA |
|----------|--------|------------|----------|
| CNN/DailyMail | ROUGE-1 | **44.16** | 43.85 |
| CNN/DailyMail | ROUGE-2 | **21.28** | 20.43 |
| CNN/DailyMail | ROUGE-L | **40.90** | 40.67 |
| XSum | ROUGE-1 | **45.14** | 38.93 |
| XSum | ROUGE-2 | **22.27** | 16.33 |
| ELI5 (QA) | ROUGE-L | **30.6** | 28.9 |
| ConvAI2 (대화) | Perplexity | **10.7** | 11.1 |
| SQuAD 2.0 | F1 | **88.8** | - |
| MNLI | Accuracy | **89.9** | 90.2 (RoBERTa) |

특히 **요약(Summarization)** 태스크에서 압도적인 성능을 보였으며, XSum에서는 이전 SOTA 대비 ROUGE-1이 6.2포인트나 향상되었다.

## 관련 모델 비교

| 특성 | BERT | GPT-2 | T5 | BART |
|------|------|-------|-----|------|
| 구조 | Encoder-only | Decoder-only | Encoder-Decoder | Encoder-Decoder |
| 사전학습 | MLM | AR LM | Span Corruption | Denoising AE |
| 양방향 문맥 | O | X | O (인코더) | O (인코더) |
| 생성 능력 | 약함 | 강함 | 강함 | 강함 |
| 이해 능력 | 강함 | 약함 | 강함 | 강함 |
| 요약 성능 | - | 보통 | 우수 | **최우수** |
| 파라미터 (Large) | 340M | 774M | 770M | 406M |

BART는 BERT와 GPT의 장점을 결합하면서도 T5보다 더 유연한 노이즈 함수를 사용한다. T5가 span corruption이라는 단일 방식에 의존하는 반면, BART는 다양한 손상 방식을 실험할 수 있는 범용 프레임워크를 제공한다.

## 학습 상세

### 데이터셋
- BooksCorpus + Wikipedia + CC-News + OpenWebText + Stories
- 총 **160GB** (RoBERTa와 동일한 데이터)

### 학습 설정
- 배치 크기: 8,000 토큰
- Optimizer: Adam (lr = 1e-4)
- 학습 스텝: 500K
- 토크나이저: Byte-level BPE (50,265 vocab)
- GPU: 16 × NVIDIA V100
- 요약 파인튜닝 시 label smoothing 0.1 적용

## 실무 활용

### 1. 텍스트 요약
BART의 가장 대표적인 활용처이다. `facebook/bart-large-cnn`은 Hugging Face에서 가장 많이 다운로드되는 요약 모델 중 하나이다.

### 2. 기계 번역
mBART(Multilingual BART)로 확장하여 다국어 번역에도 활용된다.

### 3. 질의 응답
문서 기반 질의응답에서 답변을 생성하는 생성형 QA에 적합하다.

### 4. 데이터 증강
노이즈 제거 능력을 활용하여 패러프레이징(paraphrasing) 기반 데이터 증강에 사용할 수 있다.

### 5. 텍스트 교정
문법 오류 교정(Grammatical Error Correction)에도 BART의 노이즈 복원 능력이 유용하다.

## 한계 및 전망

### 한계
1. **컨텍스트 길이 제한**: 1024 토큰으로 제한되어 긴 문서 처리에 한계가 있다
2. **모델 크기**: 406M 파라미터로 현재 기준으로는 소형 모델에 속한다
3. **Encoder-Decoder 오버헤드**: Decoder-only 모델 대비 추론 시 인코더 연산이 추가된다
4. **단일 언어**: 영어 중심으로 학습되어 다국어 지원이 제한적이다 (mBART로 해결)

### 전망
BART는 현재 LLM 시대에서 직접적으로 사용되기보다는, Encoder-Decoder 구조의 사전 학습 패러다임을 정립한 **역사적 모델**로서 의미가 크다. 노이즈 제거 사전 학습의 개념은 이후 T5, UL2, mBART 등에 계승되었으며, 특히 요약·번역 등 조건부 생성(Conditional Generation) 태스크에서 Encoder-Decoder 구조의 유효성을 입증했다. Hugging Face에서 `facebook/bart-large-cnn`은 여전히 실무에서 널리 활용되는 요약 모델이다.

---

**참고 문헌**
- Lewis, M., et al. (2019). "BART: Denoising Sequence-to-Sequence Pre-training for Natural Language Generation, Translation, and Comprehension." arXiv:1910.13461
- Devlin, J., et al. (2018). "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding."
- Raffel, C., et al. (2019). "Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer." (T5)

## 관련 문서

- [[transformer|Transformer]] — 발전 기반
- [[bert|BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding]] — 영감
