---
title: "Qwen3: MoE 기반 대규모 언어 모델"
slug: qwen3
category: llm
tags: ["Alibaba", "Chain-of-Thought", "Hybrid Reasoning", "MoE", "Multilingual", "Qwen3", "Thinking Mode"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.067070+00:00"
architecture_entry: qwen3
---

# Qwen3

**Alibaba** · **2025-04-29** · **Decoder-only** · **Sparse MoE** · **오픈소스**

## 개요

Qwen3는 Alibaba Cloud가 2025년 공개한 대규모 언어 모델 시리즈로, 0.6B부터 235B까지 Dense 및 MoE 두 계열을 포함한다. arXiv:2505.09388에 기술 보고서가 공개되었으며, 단일 모델 내에서 '생각 모드(thinking mode)'와 '비생각 모드(non-thinking mode)'를 동적으로 전환할 수 있는 하이브리드 추론 기능이 가장 큰 혁신이다. GPT-4o, Claude 3.5 Sonnet, DeepSeek-R1을 포함한 다양한 벤치마크에서 경쟁력 있는 성능을 달성하며, Apache 2.0 라이선스로 완전 오픈소스 공개되었다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

Qwen3의 핵심 혁신은 생각/비생각 이중 모드(Thinking/Non-Thinking Mode)이다. 생각 모드에서는 내부 Chain-of-Thought 추론 과정을 수행하여 복잡한 수학·코딩·논리 문제를 해결하고, 비생각 모드에서는 빠른 응답을 위해 직접 출력을 생성한다. 이 전환은 특수 토큰(enable_thinking=True/False)으로 제어된다. 235B MoE 모델은 토큰당 22B 파라미터만 활성화하여 효율적인 추론을 실현하며, 119개 언어를 지원하는 광범위한 다국어 능력을 갖추고 있다.

## 모델 사양

| 항목 | 값 |
|------|---|
| 파라미터 | 0.6B / 1.7B / 4B / 8B / 14B / 32B (Dense) / 30B-A3B / 235B-A22B (MoE) |
| 컨텍스트 길이 | 128K |
| 어텐션 | Grouped Query Attention (GQA) |
| 정규화 | RMSNorm |
| 활성화 | SwiGLU |
| 위치 인코딩 | RoPE |
| 어휘 크기 | 151,936 |
| 히든 차원 | 4096 (8B 기준) |
| 레이어 수 | 36 (8B 기준) |
| 어텐션 헤드 | 32 (8B 기준) |
| 전문가 수 | 128 (활성: 8) |

### 핵심 개념

- **Thinking Mode**
- **Chain-of-Thought**
- **MoE**
- **Hybrid Reasoning**
- **Multilingual**

## 학습

36조 토큰의 고품질 다국어 데이터로 사전 학습하였으며, 두 단계의 훈련 과정을 거친다. 1단계: 일반 언어 모델링; 2단계: 장문 컨텍스트 확장 및 추론 특화 데이터 강화. 이후 SFT → 생각 모드 RL(GRPO) → 융합 훈련(생각+비생각 통합) 순서로 정렬(alignment) 과정을 진행한다.

### 관련 모델

- **qwen2-5** — 발전 기반

### 어텐션 메커니즘: GQA

GQA(Grouped Query Attention)는 Query 헤드를 여러 그룹으로 나누어 각 그룹이 하나의 KV 헤드를 공유하는 어텐션 변형이다:

$$\text{GQA}: Q \in \mathbb{R}^{n_h \times d_h}, \quad K, V \in \mathbb{R}^{n_g \times d_h}, \quad n_g \ll n_h$$

이를 통해 MHA 대비 KV 캐시 메모리를 $n_h / n_g$배 절감하면서도 MHA에 근접하는 성능을 유지한다. MQA(Multi-Query Attention)가 단일 KV 헤드로 인해 품질 저하가 발생할 수 있는 반면, GQA는 적절한 수의 KV 그룹을 사용하여 성능과 효율의 균형을 맞춘다.
### MoE 라우팅

Qwen3은 128개의 전문가 중 8개를 활성화하는 희소 MoE(Sparse Mixture of Experts) 구조를 사용한다. 라우팅 메커니즘은 각 토큰을 가장 적합한 전문가에 할당한다:

$$g_i = \text{TopK}(\text{softmax}(W_r \cdot x), K=8)$$

$$y = \sum_{i \in \text{TopK}} g_i \cdot E_i(x)$$

각 토큰은 전체 128개 전문가 중 8개만 활성화하므로, 총 파라미터 수 대비 추론 비용이 크게 절감된다. 이를 통해 대규모 파라미터의 표현력과 소규모 활성 파라미터의 효율성을 동시에 달성한다. 전문가 간 부하 균형을 위해 보조 손실이나 동적 편향 조정이 사용된다.
### 실무 코드 예시

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("qwen3", torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("qwen3")

# Qwen3 추론 예시
messages = [{"role": "user", "content": "트랜스포머 아키텍처의 핵심 원리를 설명해줘"}]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=500, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 핵심 혁신

### 1. Thinking Mode

생각 모드(Thinking Mode)는 모델이 내부 Chain-of-Thought 추론 과정을 수행하여 복잡한 문제를 단계적으로 해결하는 기능이다. enable_thinking=True/False 파라미터로 생각 모드와 비생각 모드를 동적으로 전환할 수 있어, 문제 복잡도에 따른 적응적 추론이 가능하다.

### 2. Chain-of-Thought

Chain-of-Thought(CoT)는 복잡한 문제를 중간 추론 단계를 명시적으로 생성하며 해결하는 기법이다. 최종 답만 생성하는 것보다 추론 과정을 포함할 때 수학, 코딩, 논리 추론 정확도가 크게 향상된다. 내부 CoT는 사용자에게 보이지 않는 추론 토큰을 생성한 후 최종 답변만 반환한다.

### 3. MoE

Mixture of Experts(MoE)는 입력 토큰에 따라 일부 전문가만 활성화하여, 전체 파라미터의 표현력을 유지하면서 추론 비용을 절감하는 아키텍처이다. 전문가 간 부하 균형과 라우팅 효율성이 핵심 과제이며, 보조 손실이나 동적 편향 조정으로 균형을 유지한다.

### 4. Hybrid Reasoning

하이브리드 추론은 빠른 직관적 응답(비생각 모드)과 깊은 단계적 추론(생각 모드)을 단일 모델에서 동적으로 전환하는 기능이다. 간단한 질문에는 즉시 응답하고, 복잡한 수학이나 코딩 문제에는 내부 추론 과정을 거쳐 정확한 답변을 제공한다.


## 벤치마크/성능

Qwen3은 Thinking Mode, Chain-of-Thought, MoE 분야에서 동급 모델 대비 경쟁력 있는 성능을 보인다.


## 실무 활용

### 1. 파인튜닝 베이스 모델
Qwen3은 오픈소스로 공개되어 LoRA, QLoRA 등의 PEFT 기법을 활용한 도메인 특화 파인튜닝이 가능하다. 의료, 법률, 금융 등 특정 도메인의 데이터로 미세조정하면 전문적인 AI 어시스턴트를 구축할 수 있다.

### 2. 추론 배포
Qwen3은 다양한 추론 프레임워크(vLLM, TGI, ONNX Runtime 등)에서 지원되며, 양자화(GPTQ, AWQ, GGUF)를 통해 효율적인 서버 배포가 가능하다.

### 3. 연구 베이스라인
Qwen3은 Thinking Mode, Chain-of-Thought 연구의 표준 베이스라인으로 활용된다.

## 한계 및 전망

### 한계

1. **배포 인프라**: 0.6B / 1.7B / 4B / 8B / 14B / 32B (Dense) / 30B-A3B / 235B-A22B (MoE) 규모의 모델은 충분한 GPU 인프라가 필요하다.
2. **학습 데이터 편향**: 사전 학습 데이터의 특성에 따라 특정 도메인이나 언어에서 편향이 존재할 수 있다.
3. **환각(Hallucination)**: 모든 언어 모델과 마찬가지로 사실이 아닌 정보를 자신 있게 생성할 수 있으며, 사실 검증 메커니즘이 필요하다.

### 전망

Qwen3은 Thinking Mode, Chain-of-Thought, MoE 분야에서의 강점을 바탕으로, 향후 더 발전된 후속 모델이나 특화된 변형 모델로 진화할 것으로 예상된다. 데이터 품질 개선과 효율적 학습 기법의 발전이 핵심 연구 방향이다.
### 위치 인코딩: RoPE

RoPE(Rotary Position Embedding)는 위치 정보를 복소수 회전으로 인코딩하여 상대적 위치를 자연스럽게 포착한다:

$$f(x_m, m) = x_m e^{im\theta}, \quad \theta_j = 10000^{-2j/d}$$

이 방식은 절대 위치 임베딩의 한계를 극복하며, 학습 시 보지 못한 더 긴 시퀀스에 대한 외삽(extrapolation)이 가능하다는 핵심 장점이 있다. NTK-aware Scaling이나 YaRN 등의 확장 기법을 적용하면 학습 컨텍스트의 수십 배까지 외삽할 수 있다.
### 스케일링 법칙과의 관계

Chinchilla 스케일링 법칙에 따르면, 모델 파라미터 수 $N$과 학습 토큰 수 $D$의 최적 비율은 다음과 같이 결정된다:

$$L(N, D) = \frac{A}{N^\alpha} + \frac{B}{D^\beta} + E$$

여기서 $\alpha \approx 0.34$, $\beta \approx 0.28$이다. 이 법칙은 학습 예산이 주어졌을 때 모델 크기와 데이터 양의 최적 균형점을 결정하는 데 핵심적인 역할을 하며, 이 모델의 학습 전략에도 영향을 미쳤을 것으로 추정된다.

### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Qwen3은 0.6B / 1.7B / 4B / 8B / 14B / 32B (Dense) / 30B-A3B / 235B-A22B (MoE) 규모의 파라미터를 가지며, 128K 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Qwen3은 0.6B / 1.7B / 4B / 8B / 14B / 32B (Dense) / 30B-A3B / 235B-A22B (MoE) 규모의 파라미터를 가지며, 128K 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Qwen3은 0.6B / 1.7B / 4B / 8B / 14B / 32B (Dense) / 30B-A3B / 235B-A22B (MoE) 규모의 파라미터를 가지며, 128K 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.

## 참고 자료

- [논문](https://arxiv.org/abs/2505.09388)
- [코드](https://github.com/QwenLM/Qwen3)

## 관련 문서

- [[qwen2-5|Qwen2.5 Technical Report]] — 발전 기반
- [[qwen3-5|Qwen3.5]] — 후속 모델
- [[qwen3-omni|Qwen3-Omni]] — 후속 모델
