<!-- infographic-hero -->
![T5 핵심 요약](figures/infographic.svg)

*Figure: T5 한 장 요약 인포그래픽*

# T5: 텍스트-투-텍스트 통합 프레임워크의 정립

## 개요

**T5**(Text-to-Text Transfer Transformer)는 2019년 10월 Google Research가 발표한 인코더-디코더 모델로, **모든 NLP 태스크를 텍스트 입력 → 텍스트 출력**으로 통일하는 '텍스트-투-텍스트' 프레임워크를 제안하여 전이 학습 패러다임을 재정립했다. 분류, 요약, 번역, 질의응답, 추론 등 이질적인 태스크를 **단일 모델과 동일한 손실 함수**로 학습할 수 있다는 점에서 진정한 범용 언어 모델의 가능성을 입증했다.

750GB에 달하는 **C4(Colossal Clean Crawled Corpus)** 데이터셋을 구축·공개했으며, 11B 모델로 GLUE, SuperGLUE, CNN/DM, SQuAD 등 다수 벤치마크에서 당시 SOTA를 달성했다.

**참고 논문**: [Exploring the Limits of Transfer Learning with a Unified Text-to-Text Transformer](https://arxiv.org/abs/1910.10683) (Raffel et al., 2019)

아래 다이어그램은 T5의 텍스트-투-텍스트 프레임워크 핵심 개념을 보여준다. 번역, 질의응답, 분류 등 모든 태스크가 동일한 입출력 형식으로 처리된다.

![T5 텍스트-투-텍스트 프레임워크 다이어그램 - 모든 NLP 태스크를 텍스트 입력-출력으로 통일](figures/fig_1.png)
*Figure 1: T5 텍스트-투-텍스트 프레임워크 - 번역, 질의응답, 분류 등 모든 태스크를 텍스트 입력→텍스트 출력으로 통합하여 동일한 모델, 손실 함수, 하이퍼파라미터로 학습한다. (Source: Raffel et al., 2019)*

## 아키텍처 상세

### 텍스트-투-텍스트 프레임워크

모든 태스크를 접두사(prefix)로 표현하여 통일된 형식으로 처리한다:

- **번역**: `"translate English to German: The house is wonderful."` → `"Das Haus ist wunderbar."`
- **분류**: `"sentiment: This movie was great."` → `"positive"`
- **요약**: `"summarize: Long article text..."` → `"Summary text"`

이 방식으로 멀티태스크 학습이 단순 배치 샘플링 문제가 된다.

T5는 인코더-디코더, Language Model, Prefix LM 세 가지 아키텍처 변형을 비교 실험하여 최적 구조를 선택했다.

![인코더-디코더, Language Model, Prefix LM 세 가지 Transformer 아키텍처 변형 비교](figures/fig_4.png)
*Figure 2: Transformer 아키텍처 변형 비교 - (좌) 인코더-디코더는 인코더에서 양방향, 디코더에서 인과적 마스킹을 사용한다. (중) Language Model은 단일 스택에 인과적 마스킹을 적용한다. (우) Prefix LM은 입력 부분에 양방향 마스킹을 허용한다. (Source: Raffel et al., 2019)*

### 인코더-디코더 구조

| 구성 요소 | Small | Base | Large | 3B | 11B |
|-----------|-------|------|-------|----|-----|
| **파라미터** | 60M | 220M | 770M | 3B | 11B |
| **레이어 (각)** | 6 | 12 | 24 | 24 | 24 |
| **히든** | 512 | 768 | 1,024 | 1,024 | 1,024 |
| **어텐션 헤드** | 8 | 12 | 16 | 32 | 128 |

### Relative Attention Bias

T5는 절대 위치 임베딩을 제거하고 **상대 위치 편향(Relative Attention Bias)**만 사용한다:

$$A_{ij} = \frac{Q_i K_j^T}{\sqrt{d}} + b(i-j)$$

여기서 $b(i-j)$는 상대 위치 $i-j$에 따른 학습 가능한 편향 값이다. 버킷 기반으로 이산화하여 먼 거리의 위치 정보를 효율적으로 처리한다.

### Span Corruption 사전 학습

입력의 15%를 다양한 길이(평균 3토큰)의 **스팬(span)으로 마스킹**하고, 단일 sentinel 토큰으로 대체한다:

```
입력: Thank you [X] me to your party [Y] week
출력: [X] for inviting [Y] last [Z]
```

아래 그림은 이 Span Corruption 과정을 구체적으로 보여준다.

![Span Corruption 사전 학습 목표의 동작 과정 - 연속 토큰을 sentinel로 대체하고 디코더가 복원](figures/fig_2.png)
*Figure 3: Span Corruption 사전 학습 목표 - 입력 문장에서 무작위로 선택된 토큰을 sentinel 토큰(`<X>`, `<Y>`)으로 대체하고, 출력은 대체된 스팬을 sentinel 구분자로 연결하여 생성한다. (Source: Raffel et al., 2019)*

BERT의 토큰 단위 마스킹보다 효율적이며, 디코더가 연속된 텍스트를 생성하도록 학습된다.

## 핵심 혁신

### 1. 통합 프레임워크

분류, 생성, 변환, 추론 등 모든 NLP 태스크를 하나의 프레임워크로 통합한 것은 이후 GPT-3의 인컨텍스트 러닝과 LLM의 범용 태스크 수행에 직접적 영감을 제공했다.

### 2. C4 데이터셋

Common Crawl에서 중복 제거, 저품질 필터링을 거쳐 구축한 **750GB 규모의 정제된 영어 코퍼스**를 공개했다. 이는 이후 mC4, RefinedWeb 등 대규모 데이터셋 구축의 기준이 되었다.

### 3. 체계적 비교 연구

논문은 아키텍처(인코더-디코더 vs 디코더-only), 사전 학습 목표(MLM vs Span Corruption vs LM), 학습 전략 등을 체계적으로 비교하여 최적 구성을 도출했다. 아래 플로우차트는 비지도 학습 목표 탐색 과정의 전체 흐름을 보여준다.

![비지도 학습 목표 탐색 플로우차트 - BERT 스타일에서 Span Corruption까지의 실험 경로](figures/fig_5.png)
*Figure 4: 비지도 학습 목표 탐색 플로우차트 - BERT 스타일 디노이징에서 출발하여 타겟 시퀀스 단축, 코럽션 비율, 연속 스팬 코럽션까지 단계적으로 실험하여 최적 설정을 도출하는 과정. (Source: Raffel et al., 2019)*

## 벤치마크/성능

| 벤치마크 | BERT-Large | T5-Base | T5-11B |
|---------|----------|--------|--------|
| **GLUE** | 84.6 | 83.3 | **90.3** |
| **SuperGLUE** | ~69 | 79.3 | **88.9** |
| **SQuAD (EM)** | 80.8 | 82.1 | **86.3** |
| **CNN/DM (R-L)** | - | 38.2 | **43.5** |

## 관련 모델 비교

| 특성 | BERT | GPT-2 | T5 | mT5 |
|------|------|-------|-----|------|
| **아키텍처** | Encoder | Decoder | **Enc-Dec** | Enc-Dec |
| **사전 학습** | MLM+NSP | LM | **Span Corruption** | Span Corruption |
| **다국어** | 제한적 | 영어 | 영어 | **101개 언어** |
| **출력 형식** | 분류 | 생성 | **텍스트 통합** | 텍스트 통합 |
| **데이터셋** | 16GB | 40GB | **750GB (C4)** | 6.4TB (mC4) |

## 학습 상세

- **데이터**: C4 (Colossal Clean Crawled Corpus, 750GB)
- **토크나이저**: SentencePiece unigram LM, 32,100 vocab
- **옵티마이저**: Adafactor (메모리 효율화)
- **배치**: 128 (Small) ~ 2,048 (11B)
- **학습률**: 역제곱근(inverse square root) 스케줄
- **스텝**: 1M
- **하드웨어**: TPU v3, 11B는 1,024 코어

## 실무 활용

### 1. 요약 및 번역

```python
from transformers import T5ForConditionalGeneration, T5Tokenizer

model = T5ForConditionalGeneration.from_pretrained("t5-base")
tokenizer = T5Tokenizer.from_pretrained("t5-base")

input_text = "summarize: Long article about AI research..."
inputs = tokenizer(input_text, return_tensors="pt")
outputs = model.generate(**inputs, max_length=100)
print(tokenizer.decode(outputs[0]))
```

### 2. 멀티태스크 학습
하나의 모델로 번역, 요약, 분류, QA를 동시에 수행할 수 있다.

### 3. 연구 베이스라인
인코더-디코더 아키텍처 연구의 표준 베이스라인으로 널리 사용된다.

## 한계 및 전망

### 한계

1. **인코더-디코더 비효율**: 디코더-only 모델 대비 대화형 생성에서 비효율적이다.
2. **짧은 컨텍스트**: 512 토큰 입력으로 장문 처리에 한계가 있다.
3. **대규모 확장 한계**: 11B 이후 더 큰 T5 모델은 공개되지 않았다.

### 전망

T5의 텍스트-투-텍스트 철학은 GPT-3, ChatGPT의 "모든 것을 대화로" 접근법의 이론적 선구자이다. mT5, Switch Transformer, Flan-T5 등으로 확장되었으며, 인코더-디코더 구조는 요약, 번역 등 특정 생성 태스크에서 여전히 디코더-only 대비 장점을 가진다.

### 어텐션 메커니즘: MHA

Multi-Head Attention(MHA)은 Transformer의 핵심 메커니즘으로, 입력을 여러 헤드로 분할하여 병렬적으로 어텐션을 계산한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)W^O$$

각 헤드는 서로 다른 표현 부분공간(subspace)에서 정보를 추출하며, 결과를 결합하여 풍부한 표현을 학습한다. 추론 시에는 모든 Q 헤드에 대해 별도의 KV를 유지해야 하므로 KV 캐시 비용이 높다는 단점이 있다.
### 스케일링 법칙과의 관계

Chinchilla 스케일링 법칙에 따르면, 모델 파라미터 수 $N$과 학습 토큰 수 $D$의 최적 비율은 다음과 같이 결정된다:

$$L(N, D) = \frac{A}{N^\alpha} + \frac{B}{D^\beta} + E$$

여기서 $\alpha \approx 0.34$, $\beta \approx 0.28$이다. 이 법칙은 학습 예산이 주어졌을 때 모델 크기와 데이터 양의 최적 균형점을 결정하는 데 핵심적인 역할을 하며, 이 모델의 학습 전략에도 영향을 미쳤을 것으로 추정된다.

### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다.

**모델 규모와 효율**: T5은 60M (Small) / 220M (Base) / 770M (Large) / 3B / 11B 규모의 파라미터를 가지며, 512 (input) / 128 (output default) 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: ReLU 활성화 함수를 FFN에 사용한다. $\text{ReLU}(x) = \max(0, x)$로, 계산이 단순하고 효율적이며 Transformer 초기 설계에서 널리 사용되었다. 이후 모델들은 GELU나 SwiGLU로 전환하여 더 나은 성능을 달성하였다.


**모델 규모와 효율**: T5은 60M (Small) / 220M (Base) / 770M (Large) / 3B / 11B 규모의 파라미터를 가지며, 512 (input) / 128 (output default) 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: ReLU 활성화 함수를 FFN에 사용한다. $\text{ReLU}(x) = \max(0, x)$로, 계산이 단순하고 효율적이며 Transformer 초기 설계에서 널리 사용되었다. 이후 모델들은 GELU나 SwiGLU로 전환하여 더 나은 성능을 달성하였다.


**모델 규모와 효율**: T5은 60M (Small) / 220M (Base) / 770M (Large) / 3B / 11B 규모의 파라미터를 가지며, 512 (input) / 128 (output default) 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: ReLU 활성화 함수를 FFN에 사용한다. $\text{ReLU}(x) = \max(0, x)$로, 계산이 단순하고 효율적이며 Transformer 초기 설계에서 널리 사용되었다. 이후 모델들은 GELU나 SwiGLU로 전환하여 더 나은 성능을 달성하였다.


**모델 규모와 효율**: T5은 60M (Small) / 220M (Base) / 770M (Large) / 3B / 11B 규모의 파라미터를 가지며, 512 (input) / 128 (output default) 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.

---

**참고 논문**: [Exploring the Limits of Transfer Learning](https://arxiv.org/abs/1910.10683) (Raffel et al., 2019)

## 관련 문서

- [[transformer|Transformer]] - 발전 기반
- [[flan-t5|Flan-T5]] - 후속 모델
- [[switch-transformer|Switch Transformer]] - 후속 모델
- [[ul2|UL2]] - 후속 모델
- [[mt5|mT5]] - 변형 모델
- [[imagen|Imagen]] - 적용 모델
