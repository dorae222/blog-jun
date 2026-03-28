# Phi-4 Reasoning

**Microsoft** · **2025-04-30** · **Decoder-only** · **Dense** · **오픈소스**

## 개요

Phi-4 Reasoning은 Microsoft Research가 arXiv:2504.21318을 통해 발표한 14B 파라미터 소형 추론 특화 언어 모델이다. Microsoft의 '소형·고성능' 철학을 계승하면서, 합성 데이터(synthetic data) 기반 훈련과 RL을 결합하여 훨씬 큰 모델에 필적하는 수학·과학·논리 추론 능력을 달성하였다. 특히 경쟁 수학(AIME 2025) 및 과학 추론 벤치마크에서 GPT-4o와 동등 수준의 성능을 보이며 소형 추론 모델의 가능성을 입증하였다.

![Phi-4 Reasoning 아키텍처 — 합성 CoT 데이터와 GRPO 기반 RL을 결합한 14B 추론 특화 모델 구조](figures/architecture.svg)

*Figure 1: Phi-4 Reasoning 아키텍처 — GPT-4o 교사 모델로 생성한 합성 Chain-of-Thought 데이터로 SFT 후 GRPO 기반 RL로 추론 정확도를 강화하여, 14B로 DeepSeek-R1급 성능을 달성한다.*

## 아키텍처 상세

Phi-4 Reasoning의 핵심은 고품질 합성 Chain-of-Thought 데이터와 결과 보상 기반 RL의 결합이다. Microsoft는 GPT-4o를 교사 모델로 활용하여 복잡한 수학·과학 문제의 단계별 풀이 과정을 합성 데이터로 생성하고, 이를 SFT에 활용한다. 이후 GRPO 기반 RL로 추론 정확도를 추가 향상시킨다. 14B라는 비교적 소형 파라미터로 DeepSeek-R1-671B와 경쟁하는 성능을 달성하여 데이터 효율성과 스케일링 효율성의 새로운 기준을 제시하였다.

## 모델 사양

| 항목 | 값 |
|------|---|
| 파라미터 | 14B |
| 컨텍스트 길이 | 16K |
| 어텐션 | Grouped Query Attention (GQA) |
| 정규화 | RMSNorm |
| 활성화 | SwiGLU |
| 위치 인코딩 | RoPE |
| 어휘 크기 | 100,352 |
| 히든 차원 | 5120 |
| 레이어 수 | 40 |
| 어텐션 헤드 | 40 |

### 핵심 개념

- **Reasoning**
- **Chain-of-Thought**
- **Synthetic Data**
- **GRPO**
- **Small Language Model**

## 학습

고품질 합성 추론 데이터(GPT-4o 생성 CoT 데이터) 기반 SFT를 먼저 수행한 뒤, GRPO 알고리즘으로 RL 훈련을 진행한다. 수학·과학·코딩·논리 추론 중심의 데이터 믹스를 사용하며, 특히 경쟁 수학(AIME, AMC, Olympiad) 문제를 대량 포함한다. Apache 2.0 라이선스로 가중치와 훈련 세부 사항이 공개되었다.

### 관련 모델

- **phi-3** — 발전 기반

### 어텐션 메커니즘: GQA

GQA(Grouped Query Attention)는 Query 헤드를 여러 그룹으로 나누어 각 그룹이 하나의 KV 헤드를 공유하는 어텐션 변형이다:

$$\text{GQA}: Q \in \mathbb{R}^{n_h \times d_h}, \quad K, V \in \mathbb{R}^{n_g \times d_h}, \quad n_g \ll n_h$$

이를 통해 MHA 대비 KV 캐시 메모리를 $n_h / n_g$배 절감하면서도 MHA에 근접하는 성능을 유지한다. MQA(Multi-Query Attention)가 단일 KV 헤드로 인해 품질 저하가 발생할 수 있는 반면, GQA는 적절한 수의 KV 그룹을 사용하여 성능과 효율의 균형을 맞춘다.
### 실무 코드 예시

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("microsoft/Phi-4-reasoning", torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-4-reasoning")

# Phi-4 Reasoning 추론 예시
messages = [{"role": "user", "content": "트랜스포머 아키텍처의 핵심 원리를 설명해줘"}]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=500, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 핵심 혁신

### 1. Reasoning

추론 능력은 논리적 사고, 수학적 증명, 다단계 분석, 추상적 패턴 인식 등 복잡한 인지 과정을 수행하는 능력이다. 강화 학습 기반 추론 훈련과 Chain-of-Thought 기법이 핵심이며, 검증 가능한 태스크(수학, 코딩)에서의 보상 신호를 통해 추론 전략이 최적화된다.

### 2. Chain-of-Thought

Chain-of-Thought(CoT)는 복잡한 문제를 중간 추론 단계를 명시적으로 생성하며 해결하는 기법이다. 최종 답만 생성하는 것보다 추론 과정을 포함할 때 수학, 코딩, 논리 추론 정확도가 크게 향상된다. 내부 CoT는 사용자에게 보이지 않는 추론 토큰을 생성한 후 최종 답변만 반환한다.

### 3. Synthetic Data

합성 데이터는 GPT-4 등 대형 모델을 활용하여 교과서 형태의 고품질 학습 데이터를 생성하는 기법이다. 데이터 부족 문제를 해결하고 학습 효율을 극대화하며, 특히 코드, 수학, 과학 추론 데이터에서 효과적이다. 합성 데이터의 다양성과 품질이 모델 성능에 직접적 영향을 미친다.

### 4. GRPO

GRPO(Group Relative Policy Optimization)는 PPO의 변형으로, 그룹 내 상대적 보상을 사용하여 안정적인 정책 최적화를 달성한다. 별도의 critic 모델 없이 그룹 내 보상의 상대적 순위를 활용하여, 수학·코딩 등 검증 가능한 태스크에서 추론 능력을 효과적으로 강화한다.


## 벤치마크/성능

Phi-4 Reasoning은 Reasoning, Chain-of-Thought, Synthetic Data 분야에서 동급 모델 대비 경쟁력 있는 성능을 보인다.


## 실무 활용

### 1. 파인튜닝 베이스 모델
Phi-4 Reasoning은 오픈소스로 공개되어 LoRA, QLoRA 등의 PEFT 기법을 활용한 도메인 특화 파인튜닝이 가능하다. 의료, 법률, 금융 등 특정 도메인의 데이터로 미세조정하면 전문적인 AI 어시스턴트를 구축할 수 있다.

### 2. 추론 배포
Phi-4 Reasoning은 다양한 추론 프레임워크(vLLM, TGI, ONNX Runtime 등)에서 지원되며, 양자화(GPTQ, AWQ, GGUF)를 통해 효율적인 서버 배포가 가능하다.

### 3. 연구 베이스라인
Phi-4 Reasoning은 Reasoning, Chain-of-Thought 연구의 표준 베이스라인으로 활용된다.

## 한계 및 전망

### 한계

1. **배포 인프라**: 14B 규모의 모델은 비교적 적은 하드웨어로 배포 가능하지만, 최적의 성능을 위해서는 적절한 인프라가 필요하다.
2. **학습 데이터 편향**: 사전 학습 데이터의 특성에 따라 특정 도메인이나 언어에서 편향이 존재할 수 있다.
3. **환각(Hallucination)**: 모든 언어 모델과 마찬가지로 사실이 아닌 정보를 자신 있게 생성할 수 있으며, 사실 검증 메커니즘이 필요하다.

### 전망

Phi-4 Reasoning은 Reasoning, Chain-of-Thought, Synthetic Data 분야에서의 강점을 바탕으로, 향후 더 발전된 후속 모델이나 특화된 변형 모델로 진화할 것으로 예상된다. 데이터 품질 개선과 효율적 학습 기법의 발전이 핵심 연구 방향이다.
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


**모델 규모와 효율**: Phi-4 Reasoning은 14B 규모의 파라미터를 가지며, 16K 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Phi-4 Reasoning은 14B 규모의 파라미터를 가지며, 16K 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Phi-4 Reasoning은 14B 규모의 파라미터를 가지며, 16K 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Phi-4 Reasoning은 14B 규모의 파라미터를 가지며, 16K 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.

## 참고 자료

- [논문](https://arxiv.org/abs/2504.21318)
- [코드](https://huggingface.co/microsoft/Phi-4-reasoning)

## 관련 문서

- [[phi-3|Phi-3 Technical Report: A Highly Capable Language Model Locally on Your Phone]] — 발전 기반
