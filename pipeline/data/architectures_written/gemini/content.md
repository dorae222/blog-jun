# Gemini 1.0: Google DeepMind의 네이티브 멀티모달 AI 모델

## 개요

Gemini 1.0은 Google DeepMind가 2023년 12월 6일 발표한 멀티모달 대형 언어 모델 패밀리로, Ultra, Pro, Nano 세 가지 크기로 제공된다. "Gemini"라는 이름은 쌍둥이자리를 의미하며, Google Brain과 DeepMind의 합병 후 통합된 역량을 상징한다.

Gemini의 가장 근본적인 차별점은 '네이티브 멀티모달(natively multimodal)' 아키텍처이다. 기존의 멀티모달 모델들이 각 모달리티(텍스트, 이미지, 오디오 등)를 별도의 인코더로 처리한 후 결합하는 방식인 데 반해, Gemini는 처음부터 모든 모달리티를 단일 Transformer 모델에서 통합 처리하도록 설계되었다. 이를 통해 모달리티 간의 더 깊은 상호작용과 이해가 가능하다.

## 아키텍처 상세

### 모델 규모

| 구성 요소 | Nano-1 | Nano-2 | Pro | Ultra |
|---|---|---|---|---|
| 파라미터 | 1.8B | 3.25B | 미공개 | 미공개 |
| 컨텍스트 | 32K | 32K | 32K | 32K |
| 타겟 환경 | 온디바이스 | 온디바이스 | 범용 | 최고 성능 |

### 핵심 구성 요소

| 요소 | 사양 |
|---|---|
| Attention | Multi-Query Attention |
| 정규화 | RMSNorm |
| 활성화 함수 | GeGLU |
| 위치 인코딩 | RoPE |
| 어휘 크기 | ~256,000 |
| 학습 인프라 | TPU v5e / v5p |

### 네이티브 멀티모달 처리

Gemini의 멀티모달 처리 파이프라인은 다음과 같다:

1. **입력 토큰화**: 각 모달리티가 동일한 토큰 공간으로 변환
   - 텍스트: SentencePiece BPE
   - 이미지: 비전 인코더로 패치 토큰 생성
   - 오디오: Universal Speech Model(USM) 기반 토큰화
   - 비디오: 프레임별 이미지 토큰 + 시간적 인코딩

2. **통합 Transformer 처리**: 모든 모달리티의 토큰이 단일 시퀀스로 결합되어 Transformer에 입력

$$\text{Output} = \text{Transformer}([t_1^{\text{text}}, t_2^{\text{img}}, ..., t_n^{\text{audio}}])$$

3. **교차 모달 추론**: Self-attention을 통해 서로 다른 모달리티 간의 상호 참조가 자연스럽게 발생

### Multi-Query Attention (MQA)

추론 효율성을 위해 MQA를 채택했다. MQA는 Key와 Value 헤드를 단일 헤드로 공유하여:

$$\text{KV Cache 크기} \propto \frac{1}{h} \times \text{MHA의 KV Cache}$$

여기서 $h$는 Query 헤드 수이다. 이를 통해 긴 멀티모달 시퀀스에서의 추론 효율을 확보한다.

## 핵심 혁신

### 1. MMLU에서 인간 전문가 초과

Gemini Ultra는 MMLU 벤치마크에서 90.0%를 달성하여 인간 전문가의 89.8%를 처음으로 넘어섰다. 이 결과는 5-shot CoT(Chain-of-Thought) 프롬프팅이 아닌 새로운 평가 방식으로 달성되었다.

### 2. 32개 벤치마크 중 30개에서 SOTA

Gemini Ultra는 당시 평가된 32개 벤치마크 중 30개에서 최고 성능을 달성했으며, 특히 20개 멀티모달 벤치마크에서 새로운 기록을 세웠다.

### 3. 온디바이스 AI의 시작

Gemini Nano는 4-bit 양자화를 통해 Pixel 8 Pro 스마트폰에 탑재되었다. 이는 대형 멀티모달 모델이 온디바이스에서 실행된 최초의 상용 사례 중 하나이다.

## 벤치마크/성능

| 벤치마크 | Gemini Ultra | GPT-4 | Claude 2 | PaLM 2-L |
|---|---|---|---|---|
| MMLU | 90.0% | 86.4% | 78.5% | 81.2% |
| MMMU | 62.4% | 56.8% | - | - |
| HumanEval | 74.4% | 67.0% | 70.0% | - |
| GSM8K | 94.4% | 92.0% | 88.0% | 80.7% |
| HellaSwag | 87.8% | 95.3% | - | 86.8% |
| MATH | 53.2% | 42.2% | - | 34.4% |
| Natural2Code | 74.9% | 73.9% | - | - |

## 관련 모델 비교

### Google AI 모델 계보

| 모델 | 연도 | 유형 | 핵심 특징 |
|---|---|---|---|
| BERT | 2018 | Encoder | 양방향 사전 학습 |
| T5 | 2019 | Encoder-Decoder | Text-to-Text 통합 |
| PaLM | 2022 | Decoder-only | 540B 대규모 모델 |
| PaLM 2 | 2023 | Decoder-only | 효율적 스케일링 |
| Gemini 1.0 | 2023 | Decoder-only | 네이티브 멀티모달 |
| Gemini 1.5 | 2024 | Decoder-only + MoE | 100만 토큰 컨텍스트 |
| Gemini 2.5 | 2025 | Decoder-only + MoE | 내장 사고 기능 |

### 멀티모달 모델 비교

| 모델 | 멀티모달 방식 | 지원 모달리티 |
|---|---|---|
| GPT-4V | 별도 비전 인코더 결합 | 텍스트+이미지 |
| Gemini 1.0 | 네이티브 통합 | 텍스트+이미지+오디오+비디오 |
| Claude 3 | 별도 비전 인코더 | 텍스트+이미지 |
| LLaVA | CLIP+LLM 결합 | 텍스트+이미지 |

## 실무 활용

### API 활용

Gemini 1.0 Pro는 Google AI Studio와 Vertex AI를 통해 API로 제공된다:

1. **텍스트 생성**: 일반적인 LLM 사용 사례 (요약, 번역, QA 등)
2. **멀티모달 이해**: 이미지 설명, 비디오 분석, 오디오 전사
3. **코드 생성**: HumanEval 74.4% 수준의 코드 생성 능력
4. **수학/과학**: GSM8K 94.4%로 수학 문제 풀이에 강점

### 온디바이스 배포

Gemini Nano는 Android AICore를 통해 다음과 같은 온디바이스 기능을 제공한다:
- 키보드 자동완성 (Smart Reply)
- 녹음 요약 (Summarize in Recorder)
- 오프라인 번역

## 한계 및 전망

### 한계

1. **비공개 구조**: 파라미터 수, 학습 데이터 상세 등이 공개되지 않아 학술적 재현 불가
2. **32K 컨텍스트 제한**: 이후 Gemini 1.5에서 100만 토큰으로 대폭 확장
3. **환각(Hallucination)**: 멀티모달 추론에서 시각적 환각 현상이 보고됨
4. **독점 모델**: 오픈소스가 아니어서 커스터마이징이 제한적

### 전망

Gemini 1.0은 Google DeepMind의 통합 AI 플랫폼의 기반을 닦은 모델이다. 네이티브 멀티모달 아키텍처라는 설계 철학은 Gemini 1.5(100만 토큰 MoE), Gemini 2.5(내장 사고 기능), Gemini 3(에이전틱 AI)로 이어지며 계속 발전하고 있다. MMLU 90.0%이라는 이정표는 AI가 특정 벤치마크에서 인간 전문가를 넘어선 상징적 순간으로, 이후 AI 연구의 방향을 벤치마크 성능에서 실질적 유용성으로 전환시키는 데 기여했다.

## 관련 문서

- [[palm|PaLM]] — 발전 기반
- [[gemini-1-5|Gemini 1.5]] — 후속 모델
- [[gemma|Gemma: Open Models Based on Gemini Research and Technology]] — 영감을 줌
