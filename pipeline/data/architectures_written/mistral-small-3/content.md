<!-- infographic-hero -->
![Mistral Small 3 핵심 요약](figures/infographic.svg)

*Figure: Mistral Small 3 한 장 요약 인포그래픽*

# Mistral Small 3: 단일 GPU에서 GPT-4o-mini를 대체하는 24B 모델

## 개요

Mistral Small 3는 Mistral AI가 2025년 1월 30일 공개한 24B 파라미터 Dense 모델이다. Mistral의 라인업에서 "Small"이라는 이름을 가지지만 **24B로 절대 작지 않다**. Mistral 7B, Mixtral 8x7B와 비교하면 4배 가까운 규모이며, 일반적인 SLM(Small Language Model) 분류 기준(통상 8B 이하)에서도 한참 벗어난다.

이 "Small"이라는 명명은 Mistral 라인업 내 상대적 위치를 의미한다. Mistral Large 3(41B Dense / 675B MoE)와 대비되는 자체 호스팅 친화적 모델이라는 뜻이다. 정확히는 **단일 디바이스 추론 가능 최대 규모**를 의도적으로 겨냥한 설계이다. RTX 4090(24GB), RTX 5090(32GB), 32GB 메모리 MacBook(M-series)에서 4bit 양자화 또는 직접 bf16 추론이 가능한 한계점이 24B이며, Mistral은 이 지점을 sweet spot으로 선택하였다.

성능 측면에서는 Llama 3.3 70B Instruct에 근접한다. MMLU, HumanEval, MATH 등 주요 벤치마크에서 1/3 규모임에도 동등하거나 약간 낮은 점수를 보이며, 추론 속도는 약 3배 빠르다. GPT-4o-mini, Claude Haiku 3.5와 같은 클로즈드 소스 "small" 모델의 자체 호스팅 대체재로 평가된다.

## 아키텍처 상세

### 기본 구조

| 구성 요소 | 사양 |
|-----------|------|
| **아키텍처** | Dense Decoder-only Transformer |
| **파라미터 수** | 24B |
| **레이어 수** | 40 |
| **히든 차원** | 5,120 |
| **FFN 중간 차원** | 32,768 |
| **어텐션 헤드** | 32 (Q) / 8 (KV) |
| **어텐션** | Grouped Query Attention (GQA, 4:1) |
| **정규화** | RMSNorm |
| **활성화 함수** | SwiGLU |
| **위치 인코딩** | RoPE (theta=1,000,000) |
| **컨텍스트 길이** | 32K |
| **어휘 수** | 131,072 (Tekken 토크나이저) |

### 레이턴시 우선 Dense 설계

동급 모델들과 레이어/히든 비교는 다음과 같다.

| 모델 | 파라미터 | 레이어 | 히든 차원 | 직렬 깊이 |
|------|---------|--------|----------|----------|
| **Mistral Small 3** | 24B | **40** | 5,120 | 낮음 |
| Llama 3.3 70B | 70B | 80 | 8,192 | 높음 |
| Qwen2.5 32B | 32B | 64 | 5,120 | 중간 |
| Gemma 2 27B | 27B | 46 | 4,608 | 중간 |

레이어 수가 적을수록 토큰 생성 시 forward pass의 직렬 연산 단계가 줄어들어 **time-per-output-token(TPOT)**이 짧아진다. Mistral Small 3는 40 레이어로 의도적으로 깊이를 제한하면서 히든 차원(5,120)을 키워 표현력을 보전하였다. 이는 처리량(throughput)이 아닌 단일 요청 응답 속도를 우선시하는 설계 철학이다.

## 핵심 혁신

### 1. 단일 GPU 친화적 규모

24B Dense 모델은 다음과 같은 메모리 풋프린트를 가진다.

| 정밀도 | 메모리 (모델 가중치) | 추론 가능 디바이스 |
|--------|---------------------|---------------------|
| bf16 | 약 48GB | A100 80GB, H100 80GB |
| INT8 | 약 24GB | RTX 4090 24GB (간신히), RTX 5090 32GB |
| INT4 (GPTQ/AWQ) | 약 12-14GB | RTX 4090 24GB, RTX 4080 16GB |

특히 4bit 양자화 시 RTX 4090 단일 GPU와 32GB MacBook M-series에서 부드럽게 동작한다. 이는 Mistral이 "consumer-grade hardware에서 동작하는 가장 강력한 모델"을 명시적 목표로 삼은 결과이다.

### 2. Non-Reasoning 베이스 모델 전략

Mistral Small 3는 의도적으로 RLHF 정렬을 최소화한 "베이스에 가까운(near-base)" 인스트럭트 모델로 출시되었다. Mistral 공식 발표에 따르면, 이는 사용자가 자체 도메인에 맞춰 RL이나 reasoning SFT를 자유롭게 수행할 수 있도록 하기 위함이다.

실제로 출시 후 약 한 달 뒤인 2025년 3월 Mistral Small 3.1이 공개되었고, 이어 reasoning 특화 변형이 등장하였다. 즉 Mistral Small 3는 **커뮤니티 fine-tuning을 위한 베이스 플랫폼** 역할을 수행한다.

### 3. 빠른 추론 속도

bf16 기준 초당 약 150 토큰을 생성한다. 이는 동급 32B-70B 모델 대비 2-3배 빠른 수치이며, Llama 3.3 70B(약 50 토큰/초) 대비 명확한 우위이다.

$$\text{TPOT} \approx \frac{\text{layers} \times \text{params per layer}}{\text{memory bandwidth}}$$

Mistral Small 3는 레이어 수를 줄이고 GQA로 KV 캐시 메모리를 1/4로 압축하여 메모리 대역폭 병목을 완화하였다.

### 4. Tekken 토크나이저

Mistral Large 3 시리즈와 동일한 Tekken 토크나이저(어휘 131,072)를 사용한다. 이전 Mistral 7B의 32K 어휘 대비 4배 확장되어, 다국어 텍스트와 코드의 토큰 효율이 크게 개선되었다. 동일 영어 텍스트 기준 약 30% 적은 토큰 수로 동일 정보를 표현한다.

## 성능 비교

### 동급 SLM 및 클로즈드 소스 대비

| 벤치마크 | Mistral Small 3 24B | Llama 3.3 70B | Qwen2.5 32B | GPT-4o-mini | Claude Haiku 3.5 |
|----------|---------------------|---------------|--------------|-------------|-------------------|
| **MMLU** | 81.0 | 86.0 | 83.3 | 82.0 | 81.4 |
| **MMLU-Pro** | 66.3 | 68.9 | 65.1 | 65.0 | 65.0 |
| **GSM8K** | 91.0 | 95.1 | 92.9 | 91.4 | 91.3 |
| **MATH** | 70.6 | 71.4 | 67.2 | 72.0 | 69.4 |
| **HumanEval** | 84.8 | 88.4 | 89.0 | 87.2 | 88.4 |
| **GPQA Diamond** | 45.3 | 50.5 | 49.5 | 40.2 | 41.6 |
| **IFEval** | 82.1 | 84.7 | 83.5 | 87.2 | 85.7 |

24B 규모임에도 70B Llama 3.3에 평균 3-5점 차이로 근접하며, 클로즈드 소스 동급 모델인 GPT-4o-mini, Claude Haiku 3.5와 거의 동등한 성능을 보인다.

### 추론 속도 비교 (RTX 4090, INT4 양자화)

| 모델 | TPOT (ms) | 토큰/초 |
|------|-----------|---------|
| **Mistral Small 3 24B** | 6.7 | **150** |
| Qwen2.5 32B | 11.2 | 89 |
| Llama 3.3 70B (offload 필요) | N/A | 약 25 |
| Llama 3.1 8B | 3.5 | 285 |

Mistral Small 3는 24B 규모에서 동급 32B 모델 대비 약 1.7배, 70B 모델 대비 6배 빠른 토큰 생성을 보여준다.

## 사용 사례

### 1. 엣지 디바이스 / 온프레미스 챗봇

데이터 보안이 중요한 사내 환경, 의료, 법률, 금융 분야에서 외부 API 없이 자체 호스팅이 가능하다. 단일 RTX 4090 서버 하나로 회사 전체 챗봇 서비스를 운영할 수 있다.

### 2. 비용 효율 추론 워크로드

GPT-4o-mini나 Claude Haiku 3.5의 자체 호스팅 대체재로, 대량 분류·요약·번역 워크로드에서 토큰당 비용을 대폭 절감한다. 클라우드 GPU 시간당 비용 기준, 동일 처리량당 비용이 1/5-1/10 수준이다.

### 3. 코드 어시스턴트

HumanEval 84.8로 IDE 통합 코드 어시스턴트의 로컬 LLM 백엔드로 적합하다. Continue.dev, Tabby와 같은 self-hosted 코드 도우미와 호환된다.

### 4. RAG 시스템 백본

32K 컨텍스트와 Mistral 특유의 instruction-following 안정성으로 사내 문서 RAG에 적합하다. 응답 속도가 빠르고 한국어, 일본어, 유럽 주요 언어에서 일관된 품질을 보인다.

### 5. Fine-tuning 베이스

RLHF가 가볍게 적용된 점을 활용하여, 도메인 특화 RL이나 reasoning SFT의 베이스로 사용된다. 출시 후 의료, 법률, 코딩 등 다양한 도메인 fine-tuned 변형이 커뮤니티에서 등장하였다.

## 한계 및 의의

### 한계

1. **"Small"이라는 명명의 혼란**: 24B는 일반적 SLM 분류(8B 이하)에서 벗어나며, 진정한 엣지 디바이스(스마트폰, 라즈베리 파이)에서는 동작이 어렵다. 명명이 마케팅 의도와 사용자 기대 사이에 괴리를 만든다.
2. **컨텍스트 길이 제한**: 32K로 Llama 3.3 70B(128K), Qwen2.5 32B(128K), Claude(200K) 대비 짧다. 대규모 코드베이스 분석이나 장문 문서 처리에는 제약이 있다.
3. **Reasoning 능력 한계**: 베이스 모델 전략으로 RLHF가 제한적이라, GPQA Diamond 45.3 등 깊이 있는 추론 벤치마크에서 reasoning 특화 모델(o1-mini, DeepSeek-R1) 대비 명확히 뒤처진다.
4. **Vision 미지원**: 텍스트 전용 모델로, 멀티모달 입력은 별도 모델(Pixtral 12B)이 필요하다. Mistral Small 3.1에서 비전 지원이 추가되었다.
5. **메모리 절대량**: bf16 추론 시 48GB가 필요해 RTX 4090 단일로는 양자화가 사실상 필수이다. INT4 양자화 시 약 0.5-1.5점의 벤치마크 손실이 발생한다.

### 의의

Mistral Small 3는 **"단일 GPU에서 동작하는 가장 강력한 오픈 모델"**이라는 새로운 카테고리를 정립하였다. 이는 대규모 클라우드 GPU 없이도 GPT-4o-mini 수준의 AI를 자체 운영할 수 있는 가능성을 명확히 입증한 모델이며, 온프레미스 AI 인프라 구축의 표준이 되어가고 있다.

또한 베이스 모델로서의 포지셔닝은 흥미롭다. Mistral은 "정렬은 사용자가 직접 한다"는 철학을 통해 도메인 특화 fine-tuning 생태계를 활성화하였고, 이는 Mistral Small 3.1, 3.2, 그리고 reasoning 변형으로 이어졌다. Llama, Qwen이 이미 강하게 정렬된 모델을 제공하는 것과 차별화된 전략이다.

향후 Mistral Small 4가 등장한다면 32K 이상의 컨텍스트, 멀티모달 통합, reasoning 모드 내장 등이 핵심 개선 방향이 될 것이다. 24B Dense라는 규모 자체는 consumer-grade GPU 메모리가 32GB-48GB로 늘어남에 따라 더 매력적인 sweet spot이 될 전망이다.

## 관련 문서

- [[mistral-large-3|Mistral Large 3]] - Mistral 3 시리즈 플래그십
- [[mistral-7b|Mistral 7B]] - Mistral 라인업의 시초
- [[mixtral|Mixtral 8x7B]] - Mistral의 MoE 변형
- [[smollm3-3b|SmolLM3-3B]] - 진정한 의미의 SLM
- [[qwen3-8b|Qwen3-8B]] - 같은 efficiency 카테고리의 8B 모델
- [[phi-4-reasoning|Phi-4 Reasoning]] - Microsoft의 reasoning 특화 SLM
