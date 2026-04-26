<!-- infographic-hero -->
![Gemma 핵심 요약](figures/infographic.svg)

*Figure: Gemma 한 장 요약 인포그래픽*

# Gemma: Google DeepMind의 경량 오픈 언어 모델

## 개요

Gemma는 Google DeepMind가 2024년 2월 공개한 경량 오픈 언어 모델 시리즈로, 2B와 7B 두 가지 크기로 제공된다. "Gemma"라는 이름은 라틴어로 "보석"을 의미하며, Google의 플래그십 모델인 Gemini 개발 과정에서 축적된 기술과 노하우를 소형 모델에 이식한 것이 핵심 특징이다.

Gemma의 가장 눈에 띄는 기술적 특징은 256,128개라는 방대한 어휘 크기(vocabulary size)이다. 이는 GPT 계열의 50K, LLaMA 계열의 32K와 비교하면 약 5~8배에 달하는 규모로, 다국어 토큰화 효율을 극대화한다. 또한 7B 모델에 MQA(Multi-Query Attention)를 적용하여 추론 속도를 개선했다.

아래 그림은 Gemma 7B가 동급 오픈 모델들과 비교했을 때 각 능력별 성능을 보여준다. 특히 수학/과학과 코딩 영역에서 큰 강점을 보인다.

![Gemma 7B vs LLaMA-2/Mistral 능력별 성능 비교 - QA, 추론, 수학/과학, 코딩](figures/fig_1.png)
*Figure 1: Gemma 7B 능력별 성능 비교 - 질의응답(QA), 추론(Reasoning), 수학/과학(Math/Science), 코딩(Coding) 4개 영역에서 LLaMA-2 7B/13B, Mistral 7B와 비교. Gemma 7B는 특히 수학/과학과 코딩에서 동급 대비 뛰어난 성능을 달성한다. (Source: Gemma Team, 2024)*

## 아키텍처 상세

### 기본 구조

Gemma는 Decoder-only Transformer 아키텍처를 기반으로 하며, Gemini에서 검증된 여러 기술을 채택했다.

| 구성 요소 | Gemma 2B | Gemma 7B |
|---|---|---|
| 파라미터 수 | 2B | 7B |
| Hidden Dimension | 2048 | 3072 |
| 레이어 수 | 18 | 28 |
| Attention Head | 8 | 16 |
| Attention 방식 | MHA | MQA |
| 컨텍스트 길이 | 8,192 | 8,192 |
| 어휘 크기 | 256,128 | 256,128 |
| 위치 인코딩 | RoPE | RoPE |
| 정규화 | RMSNorm (Pre-Norm) | RMSNorm (Pre-Norm) |
| 활성화 함수 | GeGLU | GeGLU |

### 256K 초대형 어휘(Vocabulary)

Gemma의 가장 독특한 설계 결정은 256,128개의 SentencePiece BPE 어휘이다. 이 거대한 어휘 크기의 효과는 다음과 같다:

$$\text{토큰화 효율} = \frac{\text{원문 길이}}{\text{토큰 수}}$$

어휘 크기가 클수록 하나의 토큰이 더 많은 텍스트를 커버하므로, 동일 텍스트에 대해 더 적은 토큰이 필요하다. 이는 특히 한국어, 중국어, 일본어 등 CJK 문자에서 큰 효과를 발휘한다:

| 모델 | 어휘 크기 | 한국어 토큰화 효율 |
|---|---|---|
| LLaMA-2 | 32,000 | 낮음 (바이트 단위 분해) |
| Mistral | 32,000 | 낮음 |
| Qwen2 | 151,936 | 높음 |
| Gemma | 256,128 | 매우 높음 |

### Multi-Query Attention (MQA)

7B 모델에 적용된 MQA는 KV 헤드를 단 1개로 줄이는 방식이다:

$$\text{MQA: } Q \in \mathbb{R}^{n \times d_k}, K \in \mathbb{R}^{1 \times d_k}, V \in \mathbb{R}^{1 \times d_v}$$

이를 통해 KV 캐시 메모리를 헤드 수에 비례하여 절감할 수 있다. 16개 Query 헤드 대비 1개 KV 헤드이므로, KV 캐시가 약 1/16로 감소한다.

### GeGLU 활성화 함수

Gemma는 GELU 기반 Gated Linear Unit인 GeGLU를 사용한다:

$$\text{GeGLU}(x, W, V, b, c) = \text{GELU}(xW + b) \odot (xV + c)$$

이 게이트 메커니즘은 정보 흐름을 선택적으로 제어하여 모델의 표현력을 높인다.

## 핵심 혁신

### 1. Gemini 기술의 민주화

Gemma는 Google의 가장 강력한 모델인 Gemini의 학습 인프라와 데이터 전처리 파이프라인을 소형 모델에 적용한 최초의 공개 모델이다. TPU v5p 대규모 클러스터에서의 효율적인 분산 학습 기법이 적용되었다.

### 2. 책임감 있는 AI 설계

Gemma는 사전 학습 단계부터 Responsible AI 원칙을 반영했다:
- 독성(toxicity) 데이터 필터링
- 편향(bias) 평가 및 완화
- 안전성 벤치마크(RealToxicityPrompts, BOLD 등) 통과

아래 그림들은 Gemma의 메모리제이션(학습 데이터 암기) 비율이 동급 모델 대비 낮은 수준임을 보여준다.

![Gemma vs PaLM 모델 계열 간 메모리제이션 비율 비교](figures/fig_2.png)
*Figure 2: 모델 계열별 메모리제이션 비율 비교 - Gemma 2B/7B는 PaLM, PaLM 2 등 유사 규모 모델과 비교하여 동등하게 낮은 영어 웹 콘텐츠 암기율을 보인다. (Source: Gemma Team, 2024)*

![Gemma 2B/7B의 데이터 소스별 개인 정보 메모리제이션 비율](figures/fig_3.png)
*Figure 3: 개인 및 민감 데이터 메모리제이션 측정 - Gemma 2B/7B 모두 민감 데이터의 메모리제이션이 발견되지 않았으며, 개인 데이터 암기율도 매우 낮은 수준이다. (Source: Gemma Team, 2024)*

### 3. 6T 토큰 학습

2B/7B급 소형 모델임에도 6T 토큰이라는 대규모 학습 데이터를 사용했다. 이는 Chinchilla 스케일링 법칙이 제안하는 최적 비율(파라미터 수 x 20)을 크게 초과하는 수준으로, 소형 모델에서의 과잉 학습(over-training)이 실제 성능 향상에 기여함을 보여준다.

## 벤치마크/성능

| 벤치마크 | Gemma 7B | Mistral 7B | LLaMA-2 7B | LLaMA-2 13B |
|---|---|---|---|---|
| MMLU (5-shot) | 64.6% | 60.1% | 45.3% | 54.8% |
| HumanEval | 32.3% | 26.2% | 12.8% | 18.3% |
| GSM8K | 46.4% | 37.8% | 14.6% | 28.7% |
| HellaSwag | 81.2% | 81.3% | 77.2% | 80.7% |
| ARC Challenge | 53.2% | 55.5% | 48.5% | 49.4% |

Gemma 7B는 MMLU에서 64.6%, HumanEval에서 32.3%를 달성하여 동급 모델을 대부분 능가했다.

## 관련 모델 비교

### Gemma 시리즈 발전 과정

| 모델 | 출시일 | 파라미터 | 컨텍스트 | 어휘 | 주요 변화 |
|---|---|---|---|---|---|
| Gemma 1 | 2024.02 | 2B/7B | 8K | 256K | 초대형 어휘, MQA |
| CodeGemma | 2024.04 | 2B/7B | 8K | 256K | 코드 특화 파인튜닝 |
| Gemma 2 | 2024.06 | 2B/9B/27B | 8K | 256K | 27B 추가, 성능 향상 |
| Gemma 3 | 2025.03 | 1B-27B | 128K | 262K | 멀티모달, 128K 컨텍스트 |

### 동급 경쟁 모델 비교

| 특성 | Gemma 7B | Mistral 7B | Phi-2 2.7B |
|---|---|---|---|
| 어휘 크기 | 256K | 32K | 50K |
| 학습 데이터 | 6T 토큰 | 미공개 | 1.4T 토큰 |
| Attention | MQA | GQA | MHA |
| 강점 | 다국어, 안전성 | 코드, 추론 | 소형 고성능 |

## 실무 활용

### 배포 시나리오

1. **엣지/모바일 배포**: 2B 모델은 양자화 시 2GB 이하로 모바일 디바이스에서 실행 가능
2. **다국어 서비스**: 256K 어휘로 CJK 언어에서의 토큰화 효율이 뛰어남
3. **파인튜닝 베이스**: LoRA/QLoRA로 도메인 특화 모델 구축에 적합한 기반 모델
4. **교육/연구**: 연구·교육용 라이선스로 학술 목적에 적합

### 프레임워크 지원

Gemma는 Keras 3.0, JAX, PyTorch를 공식 지원하며, Hugging Face Transformers에서도 바로 사용할 수 있다. Google Colab T4 GPU에서도 2B 모델 실행이 가능하다.

## 한계 및 전망

### 한계

1. **컨텍스트 제한**: 8,192 토큰의 컨텍스트는 2024년 기준으로 짧은 편
2. **MQA의 품질 트레이드오프**: KV 헤드가 1개로 줄어 추론 속도는 빠르지만, GQA 대비 품질 저하 가능성
3. **초대형 어휘의 임베딩 비용**: 256K 어휘의 임베딩 레이어가 전체 파라미터에서 차지하는 비중이 큼
4. **제한적 라이선스**: 초기 버전은 상업적 사용에 일부 제한

### 전망

Gemma는 Google의 오픈소스 LLM 전략의 시작점이었다. 이후 Gemma 2에서 27B까지 확장하고, Gemma 3에서 멀티모달과 128K 컨텍스트를 추가하며 빠르게 발전했다. 특히 256K 어휘라는 설계 결정은 이후 다국어 LLM의 트렌드를 선도하며, Qwen, Yi 등 다른 모델들도 대형 어휘를 채택하는 데 영향을 미쳤다.

Gemma 시리즈는 "대형 모델의 기술을 소형 모델로 이전한다"는 Google의 철학을 구현하며, 오픈소스 AI 생태계에서 점점 더 중요한 위치를 차지하고 있다.

## 관련 문서

- [[gemma-3|Gemma 3]] - 후속 모델
- [[paligemma-2|PaliGemma 2]] - 후속 모델
- [[gemini|Gemini]] - 영감
