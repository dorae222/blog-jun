# LLaMA 2: 오픈소스 Chat 모델의 기준을 세운 모델

## 개요

**LLaMA 2**는 Meta AI와 Microsoft가 2023년 7월 18일 연구 및 **상업적 이용이 모두 가능한 라이선스**로 공개한 LLaMA의 후속 모델이다. 단순한 성능 개선을 넘어, 오픈소스 커뮤니티가 전체 RLHF 파이프라인의 결과물을 직접 활용할 수 있게 한 **LLaMA-2-Chat**을 함께 제공했다.

컨텍스트 길이를 2배(2,048→4,096) 확장하고, 대형 모델(34B/70B)에 GQA를 도입해 추론 효율을 대폭 개선했다. 또한 **Ghost Attention(GAtt)** 기법으로 멀티턴 대화에서 초기 시스템 프롬프트 지시를 일관되게 유지하는 문제를 해결했다.

**참고 논문**: [Llama 2: Open Foundation and Fine-Tuned Chat Models](https://arxiv.org/abs/2307.09288) (Touvron et al., 2023)

![LLaMA 2-Chat 학습 파이프라인 — 사전학습에서 SFT, RLHF(Rejection Sampling + PPO)까지의 전체 과정](figures/fig_5.jpg)
*Figure 1: LLaMA 2-Chat 학습 파이프라인 — 사전학습 데이터로 Llama 2를 학습한 후, SFT와 RLHF(Rejection Sampling + PPO)를 반복 적용하여 Chat 모델을 완성한다. Safety/Helpful 보상 모델이 병렬로 활용된다. (Source: Touvron et al., 2023)*

## 아키텍처 상세

### LLaMA 대비 3대 변화

#### 1. 컨텍스트 확장 (2K → 4K)

학습 데이터를 1.4T에서 **2T 토큰**으로 40% 확대하면서, 컨텍스트 길이를 4,096으로 확장했다.

#### 2. GQA (Grouped Query Attention)

34B와 70B 모델에 GQA를 도입했다:

$$\text{GQA}: Q \in \mathbb{R}^{n_h \times d_h}, \quad K, V \in \mathbb{R}^{n_g \times d_h}$$

70B 기준: Q 64헤드, KV 8헤드 → KV 캐시 **8배 감소**, 추론 처리량 크게 향상.

#### 3. Ghost Attention (GAtt)

멀티턴 대화에서 시스템 프롬프트를 일관되게 유지하기 위한 기법이다. SFT 데이터 구성 시 시스템 메시지를 **모든 대화 턴에 가상으로 삽입**하여, 모델이 장기 대화에서도 초기 지시를 잊지 않도록 한다.

![Ghost Attention 적용 전후 비교 — GAtt 없이 시스템 지시를 잊는 문제가 해결됨](figures/fig_10_1.png)
*Figure 2: Ghost Attention 효과 — GAtt 적용 전(좌)에는 멀티턴 대화에서 시스템 프롬프트 지시(이모지로 답변)를 잊지만, GAtt 적용 후(우)에는 일관되게 유지한다. (Source: Touvron et al., 2023)*

![GAtt 적용 전후 어텐션 패턴 시각화 — 시스템 프롬프트에 대한 어텐션이 유지됨](figures/fig_11.png)
*Figure 3: GAtt 어텐션 시각화 — GAtt 적용 전(좌)에는 후반 턴에서 시스템 메시지 어텐션이 약화되지만, 적용 후(우)에는 전체 대화에 걸쳐 시스템 메시지에 대한 강한 어텐션이 유지된다. (Source: Touvron et al., 2023)*

### 모델 사양

| 모델 | 파라미터 | 레이어 | 히든 | 어텐션 |
|------|---------|--------|------|--------|
| 7B | 7B | 32 | 4,096 | MHA (32 헤드) |
| 13B | 13B | 40 | 5,120 | MHA (40 헤드) |
| 34B | 34B | 48 | 8,192 | **GQA** (48Q/6KV) |
| 70B | 70B | 80 | 8,192 | **GQA** (64Q/8KV) |

## 핵심 혁신

### 1. 상업적 오픈소스 Chat 모델

LLaMA-2-Chat은 RLHF(Rejection Sampling + PPO)가 적용된 완성된 Chat 모델을 상업 라이선스로 제공한 최초의 대규모 오픈소스 모델이다.

### 2. Rejection Sampling + PPO

![LLaMA 2-Chat의 RLHF 반복 학습에 따른 유용성-무해성 진화 — SFT에서 RLHF-v5까지](figures/fig_12_1.png)
*Figure 5: LLaMA 2-Chat의 반복 정렬 진화 — SFT-v1에서 RLHF-v5(with PPO)까지 반복 학습을 거치며 유용성(Helpfulness)과 무해성(Harmlessness)이 동시에 향상되는 과정. (Source: Touvron et al., 2023)*

InstructGPT의 PPO만 사용하는 방식에서 한 단계 진화하여, 여러 응답을 생성한 후 보상 모델로 최상위 응답을 선택하는 **Rejection Sampling**을 PPO 전에 적용했다.

### 3. Safety RLHF

안전성을 별도 축으로 최적화하여, 유용성과 안전성을 동시에 달성하는 멀티-목표 정렬을 구현했다.

## 벤치마크/성능

![LLaMA 2-Chat 유용성 인간 평가 결과 — 다양한 오픈소스 및 상업 모델 대비 Win Rate 비교](figures/fig_1_1.png)
*Figure 4: 유용성 인간 평가 — LLaMA 2-Chat이 PaLM-Bison, Falcon, Vicuna, MPT 등 오픈소스 모델 대비 높은 Win Rate를 기록하고, ChatGPT와도 경쟁력 있는 수준을 달성하였다. (Source: Touvron et al., 2023)*

| 벤치마크 | LLaMA-2-7B | LLaMA-2-70B | LLaMA-1-65B |
|---------|-----------|------------|------------|
| **MMLU** | 45.3% | **68.9%** | 63.4% |
| **GSM8K** | 14.6% | **56.8%** | - |
| **HumanEval** | 12.8% | **29.9%** | 23.7% |
| **MT-Bench (Chat)** | 6.27 | **6.86** | - |

## 관련 모델 비교

| 특성 | LLaMA | LLaMA 2 | ChatGPT | Mistral 7B |
|------|-------|---------|---------|-----------|
| **파라미터** | 65B | 70B | 미공개 | 7.3B |
| **컨텍스트** | 2,048 | **4,096** | 4,096 | **8,192** |
| **GQA** | 없음 | **있음** (34B/70B) | - | **있음** |
| **Chat 모델** | 없음 | **있음** | 있음 | Instruct |
| **상업 라이선스** | 없음 | **있음** | API 전용 | Apache 2.0 |

## 학습 상세

- **사전 학습**: 2T 토큰 (LLaMA 대비 40% 증가, 공개 데이터)
- **Chat SFT**: 27,540개 어노테이션 (Meta 내부 품질 선별)
- **RLHF**: Rejection Sampling + PPO
- **Reward Model**: 70B 기반 별도 학습
- **하드웨어**: A100 80GB 2,000개
- **배치**: 4M 토큰

## 실무 활용

### 1. 상업용 Chat 서비스
상업 라이선스로 고객 서비스 챗봇, 내부 지식 어시스턴트 등을 구축할 수 있다.

### 2. RLHF 연구 베이스라인
Chat 모델과 기반 모델을 모두 공개하여, RLHF 연구의 표준 베이스라인으로 활용된다.

### 3. 파인튜닝 출발점
LoRA/QLoRA를 활용한 도메인 특화 파인튜닝의 출발점으로 널리 사용된다.

## 한계 및 전망

### 한계

1. **컨텍스트 제한**: 4,096은 현대 기준으로 짧다.
2. **소형 모델의 GQA 미적용**: 7B/13B에는 GQA가 적용되지 않았다.
3. **RLHF 파이프라인 미공개**: Chat 모델의 가중치는 공개되었으나 RLHF 학습 코드는 비공개이다.

### 전망

LLaMA 2는 오픈소스 Chat 모델의 기준을 세웠으며, LLaMA 3에서 128K 컨텍스트와 15T 토큰으로 대폭 확장되었다. GQA와 Ghost Attention은 이후 모델들의 표준 기법이 되었다.

### 위치 인코딩: RoPE

RoPE(Rotary Position Embedding)는 위치 정보를 복소수 회전으로 인코딩하여 상대적 위치를 자연스럽게 포착한다:

$$f(x_m, m) = x_m e^{im\theta}, \quad \theta_j = 10000^{-2j/d}$$

이 방식은 절대 위치 임베딩의 한계를 극복하며, 학습 시 보지 못한 더 긴 시퀀스에 대한 외삽(extrapolation)이 가능하다는 핵심 장점이 있다. NTK-aware Scaling이나 YaRN 등의 확장 기법을 적용하면 학습 컨텍스트의 수십 배까지 외삽할 수 있다.
### 실무 코드 예시

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("llama-2", torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("llama-2")

# LLaMA 2 추론 예시
messages = [{"role": "user", "content": "트랜스포머 아키텍처의 핵심 원리를 설명해줘"}]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=500, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```
### 스케일링 법칙과의 관계

Chinchilla 스케일링 법칙에 따르면, 모델 파라미터 수 $N$과 학습 토큰 수 $D$의 최적 비율은 다음과 같이 결정된다:

$$L(N, D) = \frac{A}{N^\alpha} + \frac{B}{D^\beta} + E$$

여기서 $\alpha \approx 0.34$, $\beta \approx 0.28$이다. 이 법칙은 학습 예산이 주어졌을 때 모델 크기와 데이터 양의 최적 균형점을 결정하는 데 핵심적인 역할을 하며, 이 모델의 학습 전략에도 영향을 미쳤을 것으로 추정된다.

### RMSNorm에 관하여

RMSNorm은 LayerNorm에서 평균 계산을 생략한 정규화 기법으로, $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태이다. 동일한 안정화 효과를 더 적은 연산으로 달성하며, LLaMA 이후 대부분의 현대 LLM에서 Pre-Norm 방식과 함께 표준으로 사용된다.

### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다.

**모델 규모와 효율**: LLaMA 2은 7B / 13B / 34B / 70B 규모의 파라미터를 가지며, 4096 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: LLaMA 2은 7B / 13B / 34B / 70B 규모의 파라미터를 가지며, 4096 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: LLaMA 2은 7B / 13B / 34B / 70B 규모의 파라미터를 가지며, 4096 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: LLaMA 2은 7B / 13B / 34B / 70B 규모의 파라미터를 가지며, 4096 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.

---

**참고 논문**: [Llama 2: Open Foundation and Fine-Tuned Chat Models](https://arxiv.org/abs/2307.09288) (Touvron et al., 2023)

## 관련 문서

- [[llama|LLaMA: Open and Efficient Foundation Language Models]] — 발전 기반
- [[llama-3|LLaMA 3]] — 후속 모델
- [[qwen2|Qwen2 Technical Report]] — 영감을 줌
