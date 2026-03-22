---
title: Qwen2.5 Technical Report
slug: "qwen2-5"
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.371752+00:00"
architecture_entry: "qwen2-5"
---

## 논문 개요

Qwen2.5는 Alibaba Qwen 팀이 2025년 초 발표한 대규모 언어 모델(LLM) 시리즈로, 이전 버전인 Qwen2 대비 대폭 향상된 성능과 기능을 제공한다. 이 기술 보고서는 사전학습 데이터, 모델 아키텍처, 학습 방법론, 평가 결과 등을 상세하게 기술하고 있다.

모델 크기는 **0.5B, 1.5B, 3B, 7B, 14B, 32B, 72B**의 7가지로 제공되며, 각기 다른 배포 환경과 요구사항에 대응할 수 있도록 설계되었다. 특히 코딩 전용 모델인 **Qwen2.5-Coder**와 수학 전용 모델인 **Qwen2.5-Math**도 함께 공개되어 도메인 특화 활용도를 크게 높였다.

---

## 핵심 기여

### 1. 대규모 사전학습 데이터

Qwen2.5는 총 **18조(18T) 토큰**의 고품질 데이터로 사전학습되었다. 이는 Qwen2의 약 7T 토큰 대비 2.5배 이상 증가한 규모다. 데이터 구성은 다음과 같다:

| 데이터 유형 | 비중 | 특징 |
|---|---|---|
| 일반 웹 텍스트 | ~50% | 다국어 지원, 품질 필터링 |
| 코드 | ~15% | 코딩 능력 강화 |
| 수학 | ~10% | 수학적 추론 강화 |
| 합성 데이터 | ~25% | GPT-4 기반 생성 |

특히 수학과 코딩 데이터를 대폭 증가시켜 해당 도메인에서 두드러진 성능 향상을 달성했다.

### 2. 확장된 컨텍스트 윈도우

기본 모델은 **128K 토큰** 컨텍스트를 지원하며, 특수 처리를 통해 **1M 토큰**까지 확장할 수 있다. 이는 긴 문서 처리, 코드베이스 분석, 장문 대화 등에서 실질적인 이점을 제공한다.

긴 컨텍스트를 효율적으로 처리하기 위해 **YaRN(Yet another RoPE extensioN)** 기법을 채택하였다:

$$\text{RoPE scale factor} = \frac{\log(L_{\text{target}} / L_{\text{base}})}{\log(L_{\text{train}} / L_{\text{base}})}$$

### 3. 향상된 지시 따르기 능력

Qwen2.5는 구조화된 출력(JSON 모드), 다중 에이전트 협업, 도구 호출 등의 기능이 크게 강화되었다. 이를 위해 **RLHF(Reinforcement Learning from Human Feedback)** 및 **DPO(Direct Preference Optimization)** 를 체계적으로 적용하였다.

---

## 방법론 상세

### 아키텍처

Qwen2.5는 Transformer 디코더 기반 아키텍처를 채택하며, 다음과 같은 핵심 설계 선택을 포함한다:

**GQA (Grouped Query Attention)**

표준 Multi-Head Attention (MHA)의 KV 캐시 메모리 문제를 해결하기 위해 GQA를 사용한다:

$$\text{GQA}: Q \in \mathbb{R}^{n_h \times d}, \; K, V \in \mathbb{R}^{n_{kv} \times d}, \; n_{kv} \ll n_h$$

72B 모델의 경우 쿼리 헤드 수($n_h = 64$)에 비해 KV 헤드 수($n_{kv} = 8$)를 8배 줄여 추론 효율을 크게 개선했다.

**RoPE(Rotary Position Embedding)**

위치 정보를 쿼리-키 행렬에 회전 변환으로 인코딩한다:

$$f_q(x_m) = W_q x_m \cdot e^{im\theta}, \quad f_k(x_n) = W_k x_n \cdot e^{in\theta}$$

내적 결과는 $m - n$의 상대 위치에만 의존하므로 자연스럽게 상대 위치 정보를 캡처한다.

**SwiGLU 활성화 함수**

피드포워드 네트워크에 SwiGLU를 사용하여 기존 ReLU나 GELU 대비 향상된 학습 효율을 달성한다:

$$\text{SwiGLU}(x, W, V, b, c) = \text{Swish}_1(xW + b) \odot (xV + c)$$

$$\text{Swish}_1(x) = x \cdot \sigma(x)$$

**RMSNorm**

Layer Normalization로 RMSNorm을 사용하여 계산 효율을 높인다:

$$\text{RMSNorm}(x) = \frac{x}{\text{RMS}(x)} \cdot \gamma, \quad \text{RMS}(x) = \sqrt{\frac{1}{n}\sum_{i=1}^n x_i^2}$$

### 학습 파이프라인

학습은 크게 세 단계로 구성된다:

1. **사전학습(Pretraining)**: 18T 토큰의 대규모 코퍼스로 언어 모델링 목표 $\mathcal{L} = -\sum_t \log P(x_t | x_{<t})$ 최소화
2. **지시 학습(SFT)**: 고품질 지시-응답 쌍으로 미세조정, 다양한 태스크 커버리지 확보
3. **RLHF/DPO**: 인간 선호도 데이터를 활용한 보상 모델 학습 후 강화학습 적용

```python
# Qwen2.5 모델 로딩 예시
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen2.5-72B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto"
)

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the integral of x^2?"}
]
text = tokenizer.apply_chat_template(messages, tokenize=False)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
outputs = model.generate(**model_inputs, max_new_tokens=512)
```

### Qwen2.5-Coder

코딩 특화 변형으로, **5.5T 토큰의 코드 관련 데이터**로 추가 학습되었다. 지원 언어는 92종 이상이며, 코드 생성, 디버깅, 설명 등에서 최고 수준의 성능을 보인다.

### Qwen2.5-Math

수학 특화 변형으로, **Process Reward Model(PRM)**을 도입하여 중간 추론 단계의 정확성을 검증한다. Chain-of-Thought 방식으로 복잡한 수학 문제를 단계적으로 해결한다.

---

## 실험 결과

### 종합 벤치마크

| 모델 | MMLU | HumanEval | MATH | GSM8K |
|---|---|---|---|---|
| Qwen2.5-72B-Instruct | **86.1** | **92.7** | **83.1** | **95.9** |
| GPT-4o | 85.7 | 90.2 | 76.6 | 94.8 |
| Llama-3.1-70B | 83.6 | 80.5 | 64.7 | 92.1 |
| Mistral-Large-2 | 84.0 | 92.1 | 74.1 | 93.8 |

Qwen2.5-72B-Instruct는 MMLU, HumanEval, MATH, GSM8K 등 주요 벤치마크에서 GPT-4o와 동등하거나 이를 능가하는 성능을 보인다.

### 코딩 성능

| 모델 | HumanEval | MBPP | LiveCodeBench |
|---|---|---|---|
| Qwen2.5-Coder-32B | **92.7** | **90.9** | **67.3** |
| GPT-4o | 90.2 | 87.0 | 62.4 |
| Claude 3.5 Sonnet | 92.0 | 91.0 | 65.9 |

### 소형 모델 성능

Qwen2.5-7B-Instruct는 이전 세대 Qwen2-72B-Instruct와 유사한 성능을 보이며, 소형 모델의 효율성이 크게 향상되었음을 보여준다.

---

## 의의 및 한계

### 의의

**오픈소스 생태계 기여**: Qwen2.5는 상업적 이용 가능한 라이선스로 공개되어 연구 및 산업 응용에서 폭넓게 활용될 수 있다. 특히 72B 오픈소스 모델이 GPT-4 수준의 성능을 달성한 것은 LLM 민주화 측면에서 중요한 이정표다.

**다국어 지원 강화**: 한국어, 일본어, 아랍어 등 비영어권 언어에서도 개선된 성능을 보이며, 29개 이상의 언어를 지원한다.

**실용적 기능 강화**: JSON 모드, 함수 호출, 에이전트 프레임워크 통합 등 실제 응용에 필요한 기능들이 강화되었다.

**효율적 스케일링**: 소형 모델(0.5B~7B)도 이전 세대의 훨씬 큰 모델과 경쟁할 수 있는 성능을 보이며, 엣지 배포 가능성을 높였다.

### 한계

**추론 비용**: 72B 모델은 여전히 상당한 GPU 메모리(최소 A100 80GB x 2)를 요구하여 일반 사용자의 로컬 배포에 제약이 있다.

**환각(Hallucination)**: 사실 오류나 근거 없는 정보 생성 문제는 완전히 해결되지 않았다.

**멀티모달 한계**: 텍스트 전용 모델로, 이미지/오디오 처리는 별도의 Qwen-VL 시리즈에서 다룬다.

**평가 데이터 오염**: 18T 토큰의 대규모 학습 데이터에 벤치마크 문제가 포함될 가능성이 있어 성능 수치 해석에 주의가 필요하다.

### 향후 방향

Qwen2.5의 등장은 오픈소스 LLM이 상용 모델과의 격차를 빠르게 좁히고 있음을 보여준다. 특히 코딩과 수학 도메인 특화 모델의 성공은 범용 LLM보다 도메인 특화 접근법의 실효성을 입증한다. 향후에는 더 효율적인 아키텍처, 더 나은 데이터 큐레이션, 그리고 멀티모달 통합 방향으로 발전이 예상된다.