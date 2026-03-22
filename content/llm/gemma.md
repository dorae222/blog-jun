---
title: "Gemma: Open Models Based on Gemini Research and Technology"
slug: gemma
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.376429+00:00"
architecture_entry: gemma
---

## 논문 개요

Gemma는 Google DeepMind가 2024년 2월에 공개한 경량 오픈소스 언어 모델 시리즈다. 이름은 라틴어로 "보석(gemstone)"을 의미하며, 대형 상용 모델인 Gemini의 연구 결과와 핵심 기술을 소형 모델에 이식하는 것을 목표로 한다.

Gemma는 **2B(2억 파라미터)**와 **7B(70억 파라미터)** 두 가지 크기로 제공되며, 각각 사전학습 버전(Gemma 2B/7B)과 지시 학습 버전(Gemma 2B-IT/7B-IT)이 존재한다. 특히 책임감 있는 AI(Responsible AI)를 핵심 설계 원칙으로 채택하여 안전성과 유용성을 동시에 추구한다.

사전학습에는 주로 영어 웹 문서, 수학, 코드 데이터가 포함된 **6T 토큰**이 사용되었으며, SentencePiece 기반의 256K 어휘 토크나이저를 사용한다.

---

## 핵심 기여

### 1. Gemini 기술의 소형 모델 이전

Gemma는 Gemini Ultra/Pro/Nano의 개발 과정에서 축적된 핵심 인사이트와 기술을 소형 모델에 적용한 것이다. 이는 대규모 상용 모델의 연구 성과가 오픈소스 커뮤니티로 흘러들어오는 중요한 사례다.

주요 이전 기술:
- **Multi-Query Attention (MQA)**: 추론 효율 최적화
- **GeGLU 활성화 함수**: 표현력 향상
- **고품질 사전학습 데이터 큐레이션 방법론**
- **RLHF 정렬 기법**

### 2. 책임감 있는 AI 통합

Gemma는 모델 개발의 모든 단계에서 안전성을 고려한다:

- **사전학습 데이터 필터링**: 개인정보, 유해 콘텐츠, CSAM 등 제거
- **SFT 데이터 품질 관리**: 독성, 편견, 사실 오류 최소화
- **안전성 평가**: 다양한 해로움 범주에 대한 체계적 평가
- **모델 카드**: 투명한 사용 가이드라인과 제한 사항 공개

### 3. 소형 모델의 성능 한계 돌파

동일 파라미터 크기 대비 Llama 2, Mistral 등 경쟁 모델을 능가하는 성능을 달성했다.

---

## 방법론 상세

### 아키텍처

**전체 구성:**

| 구성 요소 | Gemma 2B | Gemma 7B |
|---|---|---|
| 레이어 수 | 18 | 28 |
| 히든 차원 | 2048 | 3072 |
| FFN 차원 | 16384 | 24576 |
| 어텐션 헤드 (Q) | 8 | 16 |
| KV 헤드 | 1 (MQA) | 16 (MHA) |
| 컨텍스트 길이 | 8192 | 8192 |
| 어휘 크기 | 256,000 | 256,000 |

흥미롭게도 **2B 모델은 MQA(Multi-Query Attention)**를, **7B 모델은 MHA(Multi-Head Attention)**를 사용한다. 이는 모델 크기에 따른 효율성 트레이드오프를 고려한 설계다.

**Multi-Query Attention (MQA)**

MQA는 모든 쿼리 헤드가 단 하나의 KV 헤드를 공유하는 방식이다:

$$\text{MQA}: Q \in \mathbb{R}^{n_h \times d_k}, \; K, V \in \mathbb{R}^{1 \times d_k}$$

표준 MHA 대비 KV 캐시 메모리를 $n_h$배 절감할 수 있다:

$$\text{KV 캐시 크기} = 2 \times L \times T \times d_k \times n_{kv}$$

여기서 $L$은 레이어 수, $T$는 시퀀스 길이, $n_{kv}$는 KV 헤드 수다. MQA에서 $n_{kv} = 1$이므로 메모리가 대폭 절감된다.

**GeGLU 활성화 함수**

피드포워드 네트워크에 GeGLU(Gated Linear Unit with GELU)를 사용한다:

$$\text{GeGLU}(x, W, V, b, c) = \text{GELU}(xW + b) \odot (xV + c)$$

$$\text{GELU}(x) = x \cdot \Phi(x) = x \cdot \frac{1}{2}\left[1 + \text{erf}\left(\frac{x}{\sqrt{2}}\right)\right]$$

GeGLU는 게이팅 메커니즘을 통해 불필요한 활성화를 억제하고, GELU의 부드러운 비선형성을 결합하여 표현력을 높인다. SwiGLU와 유사하지만 Swish 대신 GELU를 사용한다는 차이가 있다.

**RoPE Positional Embedding**

Gemma도 RoPE를 채택한다:

$$q_m' = R(m, \theta) q_m, \quad k_n' = R(n, \theta) k_n$$

$$\text{score}(q_m, k_n) = (q_m')^T k_n' = q_m^T R(m-n, \theta) k_n$$

**RMSNorm (Pre-Normalization)**

Post-normalization이 아닌 Pre-normalization을 사용하여 학습 안정성을 높인다:

$$h_l = h_{l-1} + \text{Attention}(\text{RMSNorm}(h_{l-1}))$$
$$h_l' = h_l + \text{FFN}(\text{RMSNorm}(h_l))$$

### 사전학습 데이터

총 **6T 토큰**으로 구성되며, 데이터 구성은 다음과 같다:

- **웹 문서**: 주로 영어, Common Crawl에서 품질 필터링
- **코드**: 다양한 프로그래밍 언어
- **수학**: 수학적 추론 데이터
- **과학**: 학술 논문, 기술 문서

데이터 품질 보장을 위한 필터링 파이프라인:

```python
# 데이터 필터링 단계 (개념적 구현)
def filter_data_pipeline(raw_data):
    # 1. 언어 감지
    data = language_detection(raw_data, target_lang='en')
    
    # 2. 품질 점수 기반 필터링
    data = quality_filter(data, min_score=0.7)
    
    # 3. 안전성 필터
    data = safety_filter(data)  # 유해 콘텐츠 제거
    
    # 4. 개인정보 필터
    data = pii_filter(data)  # 개인정보 제거
    
    # 5. 중복 제거 (문서 레벨 + 문장 레벨)
    data = deduplication(data, method='minhash_lsh')
    
    return data
```

### 지시 학습 (Gemma-IT)

Gemma-IT는 사전학습 후 다음 단계를 거친다:

1. **지도 미세조정 (SFT)**: 다양한 지시-응답 쌍 학습
   - 수학 문제 풀이
   - 코드 생성 및 설명
   - 요약, 번역, QA 등

2. **강화학습 (RLHF)**: 인간 선호도 기반 정렬
   - 보상 모델 학습
   - PPO(Proximal Policy Optimization) 적용

**채팅 템플릿:**

```
<start_of_turn>user
{사용자 메시지}<end_of_turn>
<start_of_turn>model
{모델 응답}<end_of_turn>
```

---

## 실험 결과

### 종합 벤치마크

| 벤치마크 | Gemma 7B | Llama 2 7B | Mistral 7B | Llama 2 13B |
|---|---|---|---|---|
| MMLU | **64.3** | 45.3 | 60.1 | 54.8 |
| HellaSwag | **81.2** | 77.2 | 81.3 | 80.7 |
| ARC-Challenge | **53.2** | 53.7 | 60.0 | 59.4 |
| GSM8K | **46.4** | 14.6 | 34.5 | 28.7 |
| HumanEval | **32.3** | 12.8 | 26.2 | 18.3 |

Gemma 7B는 동일 크기의 Llama 2 7B와 Mistral 7B 대비 대부분의 벤치마크에서 우수한 성능을 보이며, 심지어 더 큰 Llama 2 13B도 여러 항목에서 능가한다.

### Gemma 2B 성능

| 벤치마크 | Gemma 2B | Llama 2 7B | Mistral 7B |
|---|---|---|---|
| MMLU | 42.3 | 45.3 | 60.1 |
| HellaSwag | 71.4 | 77.2 | 81.3 |
| ARC-C | 42.1 | 53.7 | 60.0 |
| GSM8K | 17.7 | 14.6 | 34.5 |

Gemma 2B는 자신보다 3배 이상 큰 Llama 2 7B와 비교할 만한 수준이며, 소형 디바이스 배포에 적합하다.

### 안전성 평가

| 평가 항목 | Gemma 7B-IT | GPT-3.5 |
|---|---|---|
| 독성 생성률 | 0.4% | 0.6% |
| 편향 점수 | 낮음 | 낮음 |
| 사실 정확도 | 높음 | 높음 |

---

## 의의 및 한계

### 의의

**Gemini 기술의 민주화**: 대형 상용 모델의 핵심 기술을 오픈소스로 이전한 중요한 사례다. 연구자와 개발자들이 Google의 최신 LLM 연구 성과를 자유롭게 활용할 수 있게 되었다.

**효율적 아키텍처 설계**: MQA(2B)와 MHA(7B)를 크기에 따라 선택적으로 적용하는 실용적 설계는 배포 환경에 맞는 최적화 방법론을 제시한다.

**책임감 있는 AI의 실천**: 안전성을 사후적으로 추가하는 것이 아니라 설계 단계부터 통합하는 접근법은 향후 AI 개발의 모범 사례가 되고 있다.

**모델 카드와 투명성**: 상세한 모델 카드를 제공하여 사용자가 모델의 능력과 한계를 명확히 이해할 수 있도록 했다.

**생태계 확장**: Keras, JAX, PyTorch, Hugging Face Transformers 등 다양한 프레임워크 지원으로 폭넓은 활용 가능성을 열었다.

### 한계

**영어 중심성**: 주로 영어 데이터로 학습되어 다국어 능력이 제한적이다. 한국어, 중국어 등 비영어권 언어에서 성능이 저하될 수 있다.

**컨텍스트 길이**: 8192 토큰으로 장문 처리 능력이 일부 경쟁 모델(Yi-200K, Mistral-32K)에 뒤처진다.

**추론 능력의 한계**: 복잡한 다단계 수학 추론이나 논리 추론에서 여전히 한계를 보인다.

**모델 크기 간극**: 2B와 7B 사이의 중간 크기 모델이 없어 특정 사용 사례에서 선택의 어려움이 있다. (이는 이후 Gemma 2에서 9B, 27B로 보완됨)

Gemma는 오픈소스 LLM 분야에서 "소형이지만 강력한" 모델의 기준을 높이는 데 기여했으며, 이후 Gemma 1.1, Gemma 2 등의 개선 버전으로 발전되었다.