## 개요

Gemma는 Google DeepMind가 2024년 2월에 공개한 경량 오픈소스 언어 모델 시리즈입니다. 이름은 라틴어로 "보석(gemstone)"을 의미하며, 대형 상용 모델인 Gemini의 연구 결과와 핵심 기술을 소형 모델에 이식하는 것을 목표로 합니다. Gemma는 단순히 Gemini를 축소한 것이 아니라, 소형 모델에 최적화된 아키텍처와 학습 전략을 독립적으로 설계한 결과물입니다.

Gemma는 **2B(20억 파라미터)**와 **7B(70억 파라미터)** 두 가지 크기로 제공되며, 각각 사전학습 버전(Gemma 2B/7B)과 지시 학습 버전(Gemma 2B-IT/7B-IT)이 존재합니다. 특히 책임감 있는 AI(Responsible AI)를 핵심 설계 원칙으로 채택하여 안전성과 유용성을 동시에 추구합니다.

사전학습에는 주로 영어 웹 문서, 수학, 코드 데이터가 포함된 **6T(6조) 토큰**이 사용되었으며, SentencePiece 기반의 256K 어휘 토크나이저를 사용합니다. 이 데이터 규모는 모델 크기 대비 매우 큰 것으로, Chinchilla의 compute-optimal 법칙을 넘어서는 "over-training" 전략을 의도적으로 채택한 것입니다.

Gemma의 공개는 오픈소스 LLM 생태계에서 중요한 전환점이 되었습니다. 기존에 Meta의 Llama 시리즈, Mistral AI의 Mistral 시리즈가 주도하던 오픈소스 LLM 시장에 Google이 본격적으로 진입하면서, 대형 기술 기업 간의 오픈소스 경쟁이 본격화되었기 때문입니다.

---

## 배경 및 문제

### 대형 언어 모델의 폐쇄성 문제

2023년부터 2024년 초까지 대형 언어 모델 분야는 두 가지 상반된 흐름이 공존하고 있었습니다. 한편으로는 GPT-4, Gemini, Claude 등 상용 모델의 성능이 급격히 향상되었지만, 이들 모델은 API 접근만 가능하고 가중치가 비공개였습니다. 다른 한편으로는 Llama 2, Mistral, Falcon 등 오픈소스 모델이 등장하여 연구자와 개발자들에게 자유로운 실험 환경을 제공했습니다.

그러나 오픈소스 모델과 상용 모델 사이에는 여전히 상당한 성능 격차가 존재했습니다. 특히 소형 모델(10B 이하)의 성능은 실용적 활용에 한계가 있었으며, 다음과 같은 문제들이 지적되었습니다.

- **학습 데이터 품질**: 오픈소스 모델 대부분이 공개 데이터셋에 의존하여 데이터 품질 관리에 한계가 있었습니다.
- **안전성 미비**: 안전성 평가와 정렬(alignment)이 체계적으로 이루어지지 않는 경우가 많았습니다.
- **엣지 배포 어려움**: 모바일, IoT 등 자원 제한 환경에서 동작할 수 있는 고성능 소형 모델이 부족했습니다.
- **재현성 부족**: 학습 과정, 데이터 구성, 하이퍼파라미터 등이 충분히 공개되지 않아 연구 재현이 어려웠습니다.

### Scaling Law와 Over-Training

전통적인 Chinchilla Scaling Law는 compute-optimal 학습을 위해 모델 파라미터 수와 학습 토큰 수의 비율을 약 $1:20$으로 제안합니다. 즉, 7B 모델이라면 약 140B 토큰이 최적입니다.

$$N_{\text{tokens}}^{\text{optimal}} \approx 20 \times N_{\text{params}}$$

그러나 최근 연구들은 추론 비용(inference cost)을 고려하면 더 작은 모델을 더 많은 데이터로 학습하는 것이 전체 비용 측면에서 유리할 수 있음을 보여주었습니다. Gemma는 이 원칙을 적극적으로 활용하여, Chinchilla 최적 비율을 수십 배 이상 초과하는 공격적인 over-training을 수행합니다.

| 모델 | 파라미터 | 학습 토큰 | 토큰/파라미터 비율 |
|---|---|---|---|
| Chinchilla 최적 (7B) | 7B | 140B | 20x |
| Llama 2 7B | 7B | 2T | 286x |
| Gemma 7B | 7B | 6T | **857x** |
| Gemma 2B | 2B | 2T | 1000x |

Gemma 7B는 Chinchilla 최적 대비 약 **43배** 많은 토큰으로 학습되었습니다. 이러한 over-training 전략은 학습 비용은 증가하지만, 배포 후 추론 비용 절감과 소형 모델의 성능 극대화라는 이점을 제공합니다.

### Google의 오픈소스 전략

Google은 Gemini 시리즈를 통해 상용 LLM 시장에서 경쟁하는 동시에, Gemma를 통해 오픈소스 생태계에서의 영향력을 확보하려는 이중 전략을 구사했습니다. 이는 다음과 같은 전략적 의미를 가집니다.

- **개발자 생태계 확보**: Keras, JAX, PyTorch, Hugging Face 등 다양한 프레임워크 지원을 통해 개발자 유입을 유도합니다.
- **GCP(Google Cloud Platform) 시너지**: Gemma를 GCP에서 쉽게 배포할 수 있는 환경을 제공하여 클라우드 서비스와의 시너지를 창출합니다.
- **연구 커뮤니티 기여**: Gemini의 핵심 기술을 공개하여 학술 연구에 기여하고, 후속 연구를 통한 기술 발전을 촉진합니다.

---

## 핵심 아이디어

Gemma의 핵심 아이디어는 크게 세 가지로 요약할 수 있습니다.

### 1. Gemini 기술의 소형 모델 이전

Gemma는 Gemini Ultra/Pro/Nano의 개발 과정에서 축적된 핵심 인사이트와 기술을 소형 모델에 적용한 것입니다. 이는 대규모 상용 모델의 연구 성과가 오픈소스 커뮤니티로 이전되는 중요한 사례입니다.

주요 이전 기술은 다음과 같습니다.

- **Multi-Query Attention (MQA)**: 추론 시 KV 캐시 메모리를 대폭 절감하여 배치 추론 효율성을 극대화합니다.
- **GeGLU 활성화 함수**: 게이팅 메커니즘을 통해 피드포워드 네트워크의 표현력을 향상시킵니다.
- **고품질 사전학습 데이터 큐레이션 방법론**: Google 내부의 데이터 필터링 파이프라인을 활용하여 높은 품질의 학습 데이터를 확보합니다.
- **RLHF 정렬 기법**: 인간 선호도에 기반한 강화학습으로 모델의 유용성과 안전성을 동시에 향상시킵니다.

### 2. 크기별 최적화된 아키텍처 설계

흥미로운 점은 2B와 7B 모델이 동일한 아키텍처를 사용하지 않는다는 것입니다. 2B 모델은 Multi-Query Attention(MQA)을, 7B 모델은 Multi-Head Attention(MHA)을 사용합니다. 이는 모델 크기에 따른 효율성과 성능 간의 트레이드오프를 세밀하게 고려한 설계 결정입니다.

소형 모델(2B)에서는 추론 효율성이 더 중요하므로 MQA를 채택하여 KV 캐시를 최소화하고, 대형 모델(7B)에서는 충분한 파라미터 예산이 있으므로 MHA의 더 높은 표현력을 활용합니다.

### 3. 책임감 있는 AI의 설계 단계 통합

Gemma는 모델 개발의 모든 단계에서 안전성을 고려합니다. 이는 사후적으로 안전성 레이어를 추가하는 것이 아니라, 데이터 수집부터 학습, 평가, 배포까지 전 과정에 걸쳐 안전성을 내재화하는 접근법입니다.

- **사전학습 데이터 필터링**: 개인정보(PII), 유해 콘텐츠, CSAM(아동 성 착취물) 등 제거합니다.
- **SFT 데이터 품질 관리**: 독성, 편견, 사실 오류를 최소화합니다.
- **안전성 평가**: 다양한 해로움 범주에 대한 체계적 레드팀 평가를 수행합니다.
- **모델 카드**: 투명한 사용 가이드라인과 제한 사항을 공개합니다.

---

## 방법론

### 아키텍처 상세

Gemma는 표준 Transformer decoder-only 아키텍처를 기반으로 하되, Gemini에서 검증된 여러 현대적인 기법을 통합합니다. 아래 다이어그램은 Gemma의 전체 아키텍처 구조와 핵심 설계 선택을 보여줍니다.

![Gemma 아키텍처 다이어그램: Transformer decoder-only 구조와 핵심 설계 요소](figures/architecture.png)
*Gemma의 전체 아키텍처 구조. Input Embedding에 RoPE가 적용되고, Pre-RMSNorm을 거친 후 Multi-Query/Multi-Head Attention과 GeGLU FFN이 잔차 연결과 함께 18/28개 레이어로 반복된다. 2B 모델은 MQA, 7B 모델은 MHA를 사용하는 크기별 차별화 설계가 특징이다.*

**모델 사양 비교표:**

| 구성 요소 | Gemma 2B | Gemma 7B |
|---|---|---|
| 파라미터 수 | 2.51B | 8.54B |
| 레이어 수 ($L$) | 18 | 28 |
| 히든 차원 ($d_{\text{model}}$) | 2048 | 3072 |
| FFN 차원 ($d_{\text{ff}}$) | 16384 | 24576 |
| 어텐션 헤드 수 ($n_h$) | 8 | 16 |
| KV 헤드 수 ($n_{kv}$) | 1 (MQA) | 16 (MHA) |
| 헤드 차원 ($d_k$) | 256 | 256 |
| 컨텍스트 길이 | 8192 | 8192 |
| 어휘 크기 ($V$) | 256,000 | 256,000 |
| 학습 토큰 수 | 2T | 6T |
| 활성화 함수 | GeGLU | GeGLU |
| 위치 인코딩 | RoPE | RoPE |
| 정규화 | RMSNorm | RMSNorm |

주목할 점은 히든 차원 대비 FFN 차원의 비율이 $d_{\text{ff}} / d_{\text{model}} = 8$로, 일반적인 Transformer의 4배 비율보다 큰 값을 사용한다는 것입니다. 이는 GeGLU의 게이팅 메커니즘이 실질적으로 FFN 차원을 절반으로 줄이는 효과가 있기 때문입니다.

$$d_{\text{ff}}^{\text{effective}} = \frac{d_{\text{ff}}}{2} = \frac{16384}{2} = 8192 = 4 \times d_{\text{model}}$$

따라서 실질적인 FFN 차원 비율은 표준 Transformer와 동일한 4배가 됩니다.

#### Multi-Query Attention (MQA)

MQA는 Shazeer(2019)가 제안한 효율적인 어텐션 메커니즘으로, 모든 쿼리 헤드가 단 하나의 Key-Value 헤드를 공유합니다. Gemma 2B에서 채택되었습니다.

표준 Multi-Head Attention에서 각 헤드 $i$의 어텐션은 다음과 같이 계산됩니다.

$$\text{head}_i = \text{softmax}\left(\frac{Q_i K_i^T}{\sqrt{d_k}}\right) V_i$$

여기서 $Q_i = X W_i^Q$, $K_i = X W_i^K$, $V_i = X W_i^V$이고, 각 헤드마다 독립적인 $K$, $V$ 프로젝션을 가집니다.

MQA에서는 모든 헤드가 하나의 $K$, $V$를 공유합니다.

$$\text{head}_i = \text{softmax}\left(\frac{Q_i K^T}{\sqrt{d_k}}\right) V$$

$$Q_i = X W_i^Q \in \mathbb{R}^{T \times d_k}, \quad K = X W^K \in \mathbb{R}^{T \times d_k}, \quad V = X W^V \in \mathbb{R}^{T \times d_k}$$

이때 KV 캐시의 메모리 사용량은 다음과 같이 계산됩니다.

$$\text{KV cache} = 2 \times L \times T \times d_k \times n_{kv} \times \text{sizeof(dtype)}$$

MHA($n_{kv} = n_h = 16$)에서 MQA($n_{kv} = 1$)로 전환하면 KV 캐시가 **16배 절감**됩니다. Gemma 2B의 경우 구체적으로 계산하면 다음과 같습니다.

$$\text{KV cache (MQA)} = 2 \times 18 \times 8192 \times 256 \times 1 \times 2 \text{ bytes} \approx 151 \text{ MB}$$

만약 MHA를 사용했다면 $8 \times 151 = 1,208$ MB가 필요했을 것입니다. 이 차이는 배치 크기를 키울수록 더욱 중요해집니다.

#### GeGLU 활성화 함수

피드포워드 네트워크에 GeGLU(Gated Linear Unit with GELU)를 사용합니다. Dauphin et al.(2017)이 제안한 GLU 변형으로, 게이팅 메커니즘을 통해 정보 흐름을 선택적으로 제어합니다.

$$\text{FFN}_{\text{GeGLU}}(x) = (\text{GELU}(x W_1 + b_1) \odot (x W_2 + b_2)) W_3 + b_3$$

여기서 $W_1, W_2 \in \mathbb{R}^{d_{\text{model}} \times d_{\text{ff}}}$, $W_3 \in \mathbb{R}^{d_{\text{ff}} \times d_{\text{model}}}$이고, $\odot$는 요소별 곱셈(Hadamard product)입니다.

GELU 활성화 함수는 다음과 같이 정의됩니다.

$$\text{GELU}(x) = x \cdot \Phi(x) = x \cdot \frac{1}{2}\left[1 + \text{erf}\left(\frac{x}{\sqrt{2}}\right)\right]$$

여기서 $\Phi(x)$는 표준 정규분포의 누적분포함수(CDF)입니다. GELU는 ReLU와 달리 부드러운 비선형성을 제공하며, 입력값이 음수일 때도 완전히 0이 되지 않아 gradient 흐름을 유지합니다.

GeGLU의 핵심은 $\text{GELU}(x W_1)$이 게이트 역할을 하여 $x W_2$의 어떤 차원을 통과시킬지 결정한다는 점입니다. 이를 통해 피드포워드 네트워크가 조건부로 정보를 처리할 수 있게 됩니다. SwiGLU와 유사하지만 Swish 대신 GELU를 게이트 활성화로 사용한다는 차이가 있습니다.

#### RoPE (Rotary Position Embedding)

Gemma는 위치 정보를 인코딩하기 위해 Su et al.(2021)이 제안한 RoPE를 채택합니다. RoPE는 절대 위치 인코딩과 상대 위치 인코딩의 장점을 결합합니다.

위치 $m$에 있는 쿼리 벡터 $q_m$과 위치 $n$에 있는 키 벡터 $k_n$에 대해, RoPE는 회전 행렬 $R$을 적용합니다.

$$q_m' = R(m, \theta) q_m, \quad k_n' = R(n, \theta) k_n$$

2차원 부분 공간에서의 회전 행렬은 다음과 같습니다.

$$R(m, \theta_i) = \begin{pmatrix} \cos(m\theta_i) & -\sin(m\theta_i) \\ \sin(m\theta_i) & \cos(m\theta_i) \end{pmatrix}$$

여기서 $\theta_i = 10000^{-2i/d_k}$이고, $i$는 차원 인덱스입니다.

핵심적인 성질은 내적이 상대적 위치 차이 $(m - n)$에만 의존한다는 것입니다.

$$\text{score}(q_m, k_n) = (q_m')^T k_n' = q_m^T R(m-n, \theta)^T k_n$$

이를 통해 절대 위치를 인코딩하면서도 어텐션 점수는 상대 위치에 의존하게 되어, 길이 일반화(length generalization) 능력이 향상됩니다.

#### RMSNorm (Pre-Normalization)

Gemma는 LayerNorm 대신 Zhang & Sennrich(2019)가 제안한 RMSNorm을 사용하며, 어텐션과 피드포워드 레이어 이전에 적용하는 Pre-Normalization 방식을 채택합니다.

$$\text{RMSNorm}(x) = \frac{x}{\text{RMS}(x)} \cdot \gamma, \quad \text{RMS}(x) = \sqrt{\frac{1}{d} \sum_{i=1}^{d} x_i^2}$$

RMSNorm은 LayerNorm에서 평균 빼기(mean centering) 연산을 제거하여 약 7-64%의 계산 비용을 절감하면서도 유사한 성능을 유지합니다.

Pre-Normalization을 적용한 Transformer 블록의 전체 구조는 다음과 같습니다.

$$h_l = h_{l-1} + \text{Attention}(\text{RMSNorm}(h_{l-1}))$$
$$h_l' = h_l + \text{FFN}_{\text{GeGLU}}(\text{RMSNorm}(h_l))$$

Pre-Normalization은 Post-Normalization 대비 학습 안정성이 높으며, 학습률 워밍업(warm-up) 의존도가 낮다는 장점이 있습니다.

#### Normalizer Location 특이점

Gemma는 한 가지 독특한 설계를 가지고 있습니다. 일반적인 Transformer와 달리 **임베딩 레이어의 출력에 $\sqrt{d_{\text{model}}}$을 곱합니다**.

$$h_0 = \text{Embed}(x) \times \sqrt{d_{\text{model}}}$$

이는 임베딩 가중치가 일반적으로 작은 값으로 초기화되기 때문에, hidden dimension에 비례한 스케일링을 통해 후속 레이어들과의 크기 균형을 맞추기 위한 것입니다.

### 토크나이저

Gemma는 SentencePiece 기반의 토크나이저를 사용하며, 어휘 크기는 **256,000**으로 매우 큽니다. 이는 Llama 2의 32,000이나 Mistral의 32,768과 비교하면 약 8배 큰 규모입니다.

| 모델 | 토크나이저 | 어휘 크기 |
|---|---|---|
| Gemma | SentencePiece | 256,000 |
| Llama 2 | SentencePiece | 32,000 |
| Mistral | SentencePiece | 32,768 |
| GPT-4 | BPE (tiktoken) | ~100,000 |

큰 어휘 크기의 장점은 다음과 같습니다.

- **토큰 효율성**: 동일한 텍스트를 더 적은 토큰으로 표현할 수 있어 컨텍스트 길이를 효율적으로 활용합니다.
- **다국어 지원**: 더 많은 문자와 서브워드를 직접 표현할 수 있어 비영어권 언어 처리에 유리합니다.
- **코드 처리**: 프로그래밍 언어의 키워드, 연산자 등을 개별 토큰으로 표현할 수 있습니다.

단점으로는 임베딩 레이어와 출력 레이어의 파라미터 수가 증가한다는 점이 있습니다. $V \times d_{\text{model}} = 256000 \times 3072 \approx 786M$ 파라미터가 임베딩에만 사용되며, 이는 Gemma 7B 전체 파라미터의 약 9%에 해당합니다.

### 사전학습 데이터 및 인프라

#### 데이터 구성

총 **6T 토큰**의 학습 데이터는 다음과 같이 구성됩니다.

- **웹 문서**: 주로 영어, Common Crawl에서 품질 필터링을 거쳐 수집됩니다.
- **코드**: 다양한 프로그래밍 언어의 오픈소스 코드를 포함합니다.
- **수학**: 수학적 추론 능력 향상을 위한 전문 데이터입니다.
- **과학**: 학술 논문, 기술 문서 등 전문 지식 데이터입니다.

데이터 품질 보장을 위한 필터링 파이프라인은 다단계로 구성됩니다.

```python
# 데이터 필터링 파이프라인 (개념적 구현)
def filter_data_pipeline(raw_data):
    # 1단계: 언어 감지 및 필터링
    data = language_detection(raw_data, target_lang='en')

    # 2단계: 규칙 기반 품질 필터링
    data = rule_based_filter(data,
        min_length=100,
        max_repetition_ratio=0.3,
        min_alphanumeric_ratio=0.7
    )

    # 3단계: 모델 기반 품질 점수 필터링
    data = quality_classifier_filter(data, min_score=0.7)

    # 4단계: 안전성 필터
    data = safety_filter(data)  # 유해 콘텐츠 제거

    # 5단계: 개인정보(PII) 필터
    data = pii_filter(data)  # 이메일, 전화번호, 주소 등 제거

    # 6단계: CSAM 필터
    data = csam_filter(data)  # 아동 성 착취물 관련 콘텐츠 제거

    # 7단계: 문서 수준 중복 제거
    data = deduplication(data, method='minhash_lsh')

    # 8단계: 문장 수준 중복 제거
    data = sentence_dedup(data)

    return data
```

#### 학습 인프라

Gemma는 Google의 TPU(Tensor Processing Unit)를 사용하여 학습되었습니다. 구체적으로 TPUv5e를 사용하며, 각 모델의 학습 설정은 다음과 같습니다.

| 설정 | Gemma 2B | Gemma 7B |
|---|---|---|
| 하드웨어 | TPUv5e | TPUv5e |
| 학습 토큰 | 2T | 6T |
| 시퀀스 길이 | 8192 | 8192 |
| 옵티마이저 | AdamW | AdamW |
| 학습률 스케줄 | 코사인 감쇠 | 코사인 감쇠 |
| 최대 학습률 | $1 \times 10^{-3}$ | $5 \times 10^{-4}$ |

학습률 스케줄은 코사인 감쇠(cosine decay)를 따릅니다.

$$\eta_t = \eta_{\min} + \frac{1}{2}(\eta_{\max} - \eta_{\min})\left(1 + \cos\left(\frac{t}{T}\pi\right)\right)$$

여기서 $\eta_{\max}$는 최대 학습률, $\eta_{\min}$은 최소 학습률, $t$는 현재 스텝, $T$는 전체 학습 스텝 수입니다.

### 지시 학습 (Gemma-IT)

Gemma-IT 모델은 사전학습된 기반 모델 위에 다음 단계를 거쳐 만들어집니다.

**1단계: 지도 미세조정 (Supervised Fine-Tuning, SFT)**

다양한 지시-응답 쌍으로 학습합니다. 데이터 구성은 다음과 같습니다.

- 수학 문제 풀이 (chain-of-thought 포함)
- 코드 생성 및 디버깅
- 요약, 번역, QA
- 창의적 글쓰기
- 안전성 관련 거부 응답

**2단계: 강화학습 (RLHF)**

인간 선호도 데이터를 기반으로 보상 모델을 학습하고, 이를 활용하여 정책 최적화를 수행합니다.

$$\mathcal{L}_{\text{RLHF}} = -\mathbb{E}_{x \sim \mathcal{D}, y \sim \pi_\theta(\cdot|x)} \left[ R(x, y) - \beta \cdot D_{\text{KL}}(\pi_\theta(\cdot|x) \| \pi_{\text{ref}}(\cdot|x)) \right]$$

여기서 $R(x, y)$는 보상 모델의 점수, $\pi_\theta$는 현재 정책, $\pi_{\text{ref}}$는 SFT 모델(참조 정책), $\beta$는 KL 발산 패널티 계수입니다.

**채팅 템플릿:**

```
<start_of_turn>user
{사용자 메시지}<end_of_turn>
<start_of_turn>model
{모델 응답}<end_of_turn>
```

이 형식은 다중 턴 대화에서도 동일하게 적용됩니다. 시스템 프롬프트를 위한 별도의 태그는 제공되지 않으며, 필요한 경우 사용자 턴에 포함시킵니다.

---

## 실험 결과

### 종합 벤치마크 비교 (사전학습 모델)

Gemma의 사전학습 모델 성능을 동일 규모의 경쟁 모델들과 비교합니다. 아래 그래프는 4개 핵심 영역(Question Answering, Reasoning, Math/Science, Coding)에서 Gemma 7B와 경쟁 모델들의 성능을 시각적으로 비교한 것입니다.

![Gemma 7B와 경쟁 모델의 영역별 벤치마크 성능 비교](figures/fig_1.png)
*Gemma 7B, LLaMA 2 7B/13B, Mistral 7B의 4개 핵심 영역 성능 비교. Question Answering과 Reasoning에서는 모든 모델이 유사한 수준을 보이지만, Math/Science와 Coding 영역에서 Gemma 7B가 동급 및 상위 모델을 뚜렷하게 앞서는 것을 확인할 수 있다.*

특히 수학/과학 및 코딩 영역에서의 우위는 Gemma의 6T 토큰 over-training 전략과 수학/코드 데이터의 적극적 포함이 효과적이었음을 보여줍니다. 세부 벤치마크별 성능은 다음과 같습니다.

| 벤치마크 | 평가 방법 | Gemma 7B | Llama 2 7B | Mistral 7B | Llama 2 13B |
|---|---|---|---|---|---|
| MMLU (5-shot) | 지식 | **64.3** | 45.3 | 60.1 | 54.8 |
| HellaSwag (0-shot) | 상식 추론 | **81.2** | 77.2 | 81.3 | 80.7 |
| PIQA (0-shot) | 물리 상식 | **81.2** | 78.8 | 82.1 | 80.5 |
| SocialIQA (0-shot) | 사회 상식 | 51.8 | 48.3 | **52.3** | 50.6 |
| BoolQ (0-shot) | 독해 | **83.2** | 71.5 | 83.0 | 81.4 |
| WinoGrande (partial) | 상식 | **78.4** | 69.2 | 78.0 | 72.2 |
| ARC-easy (0-shot) | 과학 | **81.5** | 75.2 | 80.5 | 78.8 |
| ARC-Challenge (25-shot) | 과학 | 53.2 | 53.7 | **60.0** | 59.4 |
| TriviaQA (5-shot) | 지식 | **63.4** | 63.1 | 62.5 | 63.0 |
| NaturalQuestions (5-shot) | 지식 | **23.0** | 17.8 | 21.5 | 20.1 |
| GSM8K (5-shot, maj@1) | 수학 | **46.4** | 14.6 | 34.5 | 28.7 |
| MATH (4-shot) | 수학 | **24.3** | 3.2 | 11.3 | 6.0 |
| HumanEval (pass@1) | 코딩 | **32.3** | 12.8 | 26.2 | 18.3 |
| MBPP (3-shot) | 코딩 | **44.4** | 20.8 | 40.2 | 28.4 |
| AGIEval | 종합 | **41.7** | 29.7 | 38.2 | 33.5 |

핵심 관찰 사항은 다음과 같습니다.

- **MMLU**: Gemma 7B(64.3)가 Llama 2 13B(54.8)보다 약 10점 높으며, Mistral 7B(60.1)보다도 4점 이상 우수합니다. 이는 6T 토큰의 대규모 학습과 데이터 품질의 효과를 보여줍니다.
- **GSM8K**: Gemma 7B(46.4)가 Llama 2 7B(14.6)를 약 3배 이상 압도합니다. 수학 데이터를 학습 데이터에 적극적으로 포함한 효과입니다.
- **HumanEval**: 코드 생성 능력에서도 32.3%로 다른 모델들을 크게 앞서며, 코드 데이터의 품질이 높았음을 시사합니다.
- **MATH**: 24.3%로 Llama 2 7B(3.2%)와 Mistral 7B(11.3%)를 큰 폭으로 앞섭니다.

### Gemma 2B 소형 모델 성능

| 벤치마크 | Gemma 2B | Phi-2 (2.7B) | Llama 2 7B |
|---|---|---|---|
| MMLU (5-shot) | 42.3 | **56.7** | 45.3 |
| HellaSwag (0-shot) | 71.4 | **73.1** | 77.2 |
| GSM8K (5-shot) | 17.7 | **57.2** | 14.6 |
| HumanEval (pass@1) | **32.3** | 29.3 | 12.8 |
| MBPP (3-shot) | **36.6** | 35.7 | 20.8 |

Gemma 2B는 자신보다 3.5배 큰 Llama 2 7B와 비교할 만한 수준이며, 코딩 벤치마크에서는 더 큰 모델을 능가합니다. 다만 Phi-2와 비교하면 MMLU, GSM8K 등에서 열세를 보이는데, 이는 Phi-2가 "교과서 품질" 합성 데이터를 적극적으로 활용했기 때문입니다.

### 지시 학습 모델(IT) 성능

| 벤치마크 | Gemma 7B-IT | Mistral 7B-Instruct | Llama 2 7B-Chat |
|---|---|---|---|
| MMLU (5-shot) | **62.0** | 54.4 | 48.1 |
| GSM8K (maj@1) | **42.1** | 33.0 | 12.0 |
| HumanEval | **33.5** | 25.0 | 12.2 |
| ARC-Challenge | **55.8** | 53.4 | 52.1 |

지시 학습 모델에서도 Gemma 7B-IT는 동일 규모의 경쟁 모델들을 전반적으로 능가합니다.

### 안전성 평가

Gemma는 책임감 있는 AI 원칙에 따라 다양한 안전성 평가를 수행합니다.

| 평가 항목 | Gemma 7B | Gemma 7B-IT | 설명 |
|---|---|---|---|
| 독성 생성률 | 1.2% | 0.4% | RealToxicityPrompts |
| 편향 점수 | 중간 | 낮음 | BBQ 벤치마크 |
| 사실 정확도 | 높음 | 높음 | TruthfulQA |
| 거부 정확도 | N/A | 92.3% | 유해 요청 거부율 |

지시 학습 모델(IT)은 기반 모델 대비 독성 생성률이 크게 감소하며, 유해한 요청에 대한 거부 능력이 추가됩니다. 이는 RLHF 정렬 과정의 효과를 보여줍니다.

안전성과 밀접하게 관련된 지표로, Gemma는 학습 데이터의 기억화(memorization) 비율에서도 기존 모델 대비 우수한 결과를 보입니다. 아래 그래프는 Gemma 모델들이 PaLM 2 Small과 비교하여 현저히 낮은 기억화 비율을 달성했음을 보여줍니다.

![Gemma와 PaLM 2 Small의 기억화 비율 비교](figures/fig_2.png)
*Gemma 2B, Gemma 7B, PaLM 2 Small의 영어 웹 콘텐츠(왼쪽)와 전체 콘텐츠(오른쪽)에 대한 정확 기억화(exact memorization) 비율 비교. Gemma 모델들이 PaLM 2 Small 대비 현저히 낮은 기억화 비율을 보여, 데이터 프라이버시 측면에서 우수함을 나타낸다.*

이러한 낮은 기억화 비율은 Gemma의 다단계 데이터 필터링 파이프라인과 중복 제거 전략의 효과를 실증적으로 보여줍니다. 더 세부적으로 데이터 소스별 기억화 특성을 분석하면, 코드와 위키 데이터는 상대적으로 높은 기억화율을, 웹과 다국어 데이터는 낮은 기억화율을 보이는 패턴이 관찰됩니다.

![데이터 소스별 기억화 비율과 개인정보 포함 여부에 따른 차이](figures/fig_3.png)
*Gemma 2B(왼쪽)와 7B(오른쪽) 모델의 데이터 소스(Code, Wiki, Science, Web, Multilingual)별 기억화 비율. 개인정보(Personal Data)가 포함된 경우(짙은 색)가 그렇지 않은 경우(연한 색)보다 높은 기억화율을 보이며, 이는 개인정보 필터링의 중요성을 뒷받침한다.*

개인정보가 포함된 데이터에서 기억화율이 더 높다는 관찰은, 사전학습 단계에서의 PII 필터링이 단순한 규정 준수를 넘어 모델의 프라이버시 안전성을 실질적으로 향상시키는 핵심 요소임을 시사합니다.

기억화 유형을 더 세밀하게 분석하면, 정확 기억화(exact memorization)와 근사 기억화(approximate memorization) 간의 차이도 데이터 소스에 따라 다른 양상을 보입니다. 다음 그림은 이 두 유형의 기억화 비율을 데이터 소스별로 비교한 결과입니다.

![Gemma 2B/7B 모델의 데이터 소스별 정확 기억화와 근사 기억화 비율 비교](figures/fig_4.png)
*Figure 5: 2B 모델(왼쪽)과 7B 모델(오른쪽)의 데이터 소스별 정확 기억화(Exact)와 근사 기억화(Approximate) 비율 비교 — 코드와 위키 데이터에서 두 유형 모두 상대적으로 높은 기억화율을 보이며, 특히 7B 모델에서 근사 기억화 비율이 정확 기억화보다 일관되게 높은 경향이 관찰된다. 이는 모델 크기가 커질수록 학습 데이터의 패턴을 더 세밀하게 포착함을 시사한다. (Google DeepMind, 2024)*

---

## 의의 및 한계

### 학술적/산업적 의의

**1. Gemini 기술의 민주화**

대형 상용 모델의 핵심 기술을 오픈소스로 이전한 중요한 사례입니다. 연구자와 개발자들이 Google의 최신 LLM 연구 성과를 자유롭게 활용할 수 있게 되었으며, 이는 오픈소스 LLM 생태계의 발전을 가속화했습니다.

**2. 효율적 아키텍처 설계의 실용적 가이드라인**

MQA(2B)와 MHA(7B)를 크기에 따라 선택적으로 적용하는 실용적 설계는, 모델 크기에 따른 아키텍처 최적화 방법론에 대한 구체적인 사례를 제시합니다. 이는 후속 모델들의 설계에 영향을 미쳤습니다.

**3. 책임감 있는 AI의 실천적 모범**

안전성을 사후적으로 추가하는 것이 아니라 설계 단계부터 통합하는 접근법은, AI 안전성 분야에서 실천적 모범 사례가 되었습니다. 특히 상세한 모델 카드를 함께 공개하여 투명성을 확보한 점은 주목할 만합니다.

**4. Over-Training 전략의 검증**

Chinchilla scaling law를 넘어서는 대규모 over-training이 소형 모델의 성능을 크게 향상시킬 수 있음을 실증적으로 보여주었습니다. 이는 이후 Llama 3, Phi-3 등에서도 유사하게 채택된 전략입니다.

**5. 생태계 확장**

Keras, JAX, PyTorch, Hugging Face Transformers 등 다양한 프레임워크 지원으로 폭넓은 활용 가능성을 열었습니다. 특히 Google의 Keras 3.0과의 긴밀한 통합은 멀티 백엔드 학습을 가능하게 합니다.

### 한계

**1. 영어 중심성**

주로 영어 데이터로 학습되어 다국어 능력이 제한적입니다. 한국어, 중국어, 일본어 등 비영어권 언어에서는 성능이 상당히 저하됩니다. 256K 어휘의 토크나이저가 다국어 토큰을 포함하고 있지만, 학습 데이터의 영어 편중으로 인해 실질적인 다국어 능력은 미흡합니다.

**2. 제한된 컨텍스트 길이**

8192 토큰의 컨텍스트 길이는 2024년 기준으로 경쟁 모델들(Yi-200K, Claude-200K, Mistral-32K)에 비해 짧습니다. 장문 문서 처리, 복잡한 코드 분석 등의 작업에서 제약이 됩니다.

**3. 추론 능력의 한계**

복잡한 다단계 수학 추론이나 논리 추론에서 여전히 한계를 보입니다. GSM8K에서 46.4%의 성능은 상당한 개선이지만, GPT-4 수준의 추론 능력과는 거리가 있습니다.

**4. 모델 크기 간극**

2B와 7B 사이의 중간 크기 모델이 없어 특정 사용 사례에서 선택의 어려움이 있습니다. 2B는 성능이 부족하고 7B는 리소스가 과다한 시나리오에서 적절한 대안이 없습니다. 이 문제는 이후 Gemma 2에서 9B, 27B 등의 크기로 보완되었습니다.

**5. 멀티모달 미지원**

텍스트 전용 모델로, 이미지나 오디오 등 멀티모달 입력을 지원하지 않습니다. 이는 이후 PaliGemma 시리즈를 통해 보완되었습니다.

---

## 코드 예제

### Hugging Face Transformers를 활용한 텍스트 생성

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# 모델 및 토크나이저 로드
model_id = "google/gemma-7b-it"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)

# 채팅 템플릿을 활용한 프롬프트 구성
chat = [
    {"role": "user", "content": "Transformer의 self-attention 메커니즘을 설명해주세요."},
]
prompt = tokenizer.apply_chat_template(
    chat, tokenize=False, add_generation_prompt=True
)

# 텍스트 생성
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
outputs = model.generate(
    **inputs,
    max_new_tokens=512,
    do_sample=True,
    temperature=0.7,
    top_p=0.9,
    top_k=50,
)
response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[-1]:], skip_special_tokens=True)
print(response)
```

### LoRA를 활용한 파인튜닝

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

# 기반 모델 로드
model_id = "google/gemma-7b"
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
tokenizer = AutoTokenizer.from_pretrained(model_id)

# LoRA 설정
lora_config = LoraConfig(
    r=16,                          # LoRA rank
    lora_alpha=32,                 # 스케일링 계수
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

# LoRA 적용
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# 학습 가능한 파라미터: ~16M / 전체: ~8.5B (0.19%)

# 학습 설정
training_args = TrainingArguments(
    output_dir="./gemma-7b-lora",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    bf16=True,
    logging_steps=10,
    save_strategy="epoch",
)

# SFTTrainer로 학습
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    tokenizer=tokenizer,
    max_seq_length=2048,
)
trainer.train()
```

### GGUF 양자화 및 llama.cpp 추론

```bash
# llama.cpp를 활용한 양자화 및 추론
# 1. GGUF 변환
python convert_hf_to_gguf.py google/gemma-7b --outtype f16 --outfile gemma-7b-f16.gguf

# 2. 4비트 양자화 (Q4_K_M)
./llama-quantize gemma-7b-f16.gguf gemma-7b-Q4_K_M.gguf Q4_K_M

# 3. 추론 실행
./llama-cli -m gemma-7b-Q4_K_M.gguf \
    -p "<start_of_turn>user\nExplain gradient descent in simple terms.<end_of_turn>\n<start_of_turn>model\n" \
    -n 256 --temp 0.7 --top-p 0.9
```

4비트 양자화 시 모델 크기와 메모리 사용량이 크게 줄어듭니다.

| 양자화 | 모델 크기 | VRAM 사용량 | MMLU 성능 변화 |
|---|---|---|---|
| FP16 | ~16 GB | ~18 GB | 기준 (64.3) |
| Q8_0 | ~8.5 GB | ~10 GB | -0.5 |
| Q4_K_M | ~4.5 GB | ~6 GB | -1.5 |
| Q4_0 | ~4.0 GB | ~5.5 GB | -2.5 |

---

Gemma는 오픈소스 LLM 분야에서 "소형이지만 강력한" 모델의 기준을 높이는 데 크게 기여했습니다. Gemini의 핵심 기술을 오픈소스로 이전하면서도 책임감 있는 AI 원칙을 일관되게 적용한 점은 높이 평가할 만합니다. 이후 Gemma 1.1, [[gemma-3|Gemma 3]], [[paligemma-2|PaliGemma 2]] 등의 개선 및 확장 버전으로 발전되었으며, [[gemini|Gemini]] 시리즈와 함께 Google의 AI 생태계를 구성하는 핵심 축이 되고 있습니다.

## 관련 문서

- [[gemma-3|Gemma 3]] -- 후속 모델
- [[paligemma-2|PaliGemma 2]] -- 후속 모델
- [[gemini|Gemini]] -- 영감
