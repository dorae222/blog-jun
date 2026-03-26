# Yi

**01.AI** · **2023-11-02** · **Decoder-only** · **Dense** · **오픈소스**

## 개요

전 구글 브레인 리더 이카이푸(李開複)가 설립한 01.AI가 2023년 11월 공개한 이중 언어(한중영) 고성능 LLM이다. LLaMA-2 아키텍처를 기반으로 하되 어휘를 64K로 확장해 중국어 토큰화 효율을 대폭 높이고, GQA를 도입해 추론 속도를 개선했다. 특히 Yi-34B-200K 버전은 200K 토큰이라는 당시 오픈 모델 중 최장 컨텍스트를 YARN·LongRoPE 기법으로 달성했다. 34B 모델이 Llama-2-70B에 필적하는 성능을 절반 파라미터로 달성해, LLaMA 아키텍처의 중국어 적용 가능성을 보여준 대표 사례가 되었다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

LLaMA-2 구조에서 3가지 변화: (1) 64K vocab—한자·한글 등 CJK 문자에 최적화된 토큰 추가로 중국어 텍스트 처리 효율 대폭 향상(LLaMA-2 32K 대비), (2) GQA 도입—KV 헤드 수 감소로 추론 KV 캐시 절감 및 처리량 향상, (3) 200K 컨텍스트—YARN(YetAnotherRoPE ExtensioN)으로 기본 4K RoPE를 200K까지 외삽. Yi-34B: MMLU 76.3%(Llama-2-70B: 68.9%), HumanEval 23.1%. Yi-6B: MMLU 61.4%(Llama-2-13B: 54.8%).

## 모델 사양

| 항목 | 값 |
|------|---|
| 파라미터 | 6B / 34B |
| 컨텍스트 길이 | 200000 |
| 어텐션 | GQA |
| 정규화 | RMSNorm |
| 활성화 | SiLU (SwiGLU) |
| 위치 인코딩 | RoPE |
| 어휘 크기 | 64000 |
| 히든 차원 | 4096 (6B) / 7168 (34B) |
| 레이어 수 | 32 (6B) / 60 (34B) |
| 어텐션 헤드 | 32 (6B) / 56 (34B) |

### 핵심 개념

- **GQA**
- **RoPE**
- **RMSNorm**
- **SwiGLU**
- **Multilingual**
- **Long Context**

## 학습

3T 토큰 이상(영어 약 60%, 중국어 약 40%). BPE 64K vocab(SentencePiece). AdamW, cosine lr schedule, gradient clipping. Flash Attention 2 적용. Yi-34B-200K은 YARN 방식으로 컨텍스트 외삽 후 장문 데이터로 추가 파인튜닝.

### 관련 모델

- **llama** — 영감

### 어텐션 메커니즘: GQA

GQA(Grouped Query Attention)는 Query 헤드를 여러 그룹으로 나누어 각 그룹이 하나의 KV 헤드를 공유하는 어텐션 변형이다:

$$\text{GQA}: Q \in \mathbb{R}^{n_h \times d_h}, \quad K, V \in \mathbb{R}^{n_g \times d_h}, \quad n_g \ll n_h$$

이를 통해 MHA 대비 KV 캐시 메모리를 $n_h / n_g$배 절감하면서도 MHA에 근접하는 성능을 유지한다. MQA(Multi-Query Attention)가 단일 KV 헤드로 인해 품질 저하가 발생할 수 있는 반면, GQA는 적절한 수의 KV 그룹을 사용하여 성능과 효율의 균형을 맞춘다.
### 실무 코드 예시

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("yi", torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("yi")

# Yi 추론 예시
messages = [{"role": "user", "content": "트랜스포머 아키텍처의 핵심 원리를 설명해줘"}]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=500, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 핵심 혁신

### 1. GQA

GQA(Grouped Query Attention)는 KV 헤드를 Q 헤드보다 적게 사용하여 KV 캐시 메모리를 절감하는 어텐션 변형이다. MHA의 성능을 유지하면서 MQA보다 안정적인 성능을 제공하며, LLaMA 2(34B/70B) 이후 대부분의 현대 LLM에서 표준으로 채택되고 있다.

### 2. RoPE

RoPE(Rotary Position Embedding)는 위치 정보를 회전 행렬로 인코딩하여 상대적 위치를 자연스럽게 포착하며, 시퀀스 길이 외삽이 가능하다. NTK-aware Scaling이나 YaRN 확장으로 학습 컨텍스트의 수십 배 길이까지 외삽할 수 있어, 현대 LLM의 사실상 표준 위치 인코딩이다.

### 3. RMSNorm

RMSNorm은 LayerNorm에서 평균 계산을 생략한 정규화 기법으로, $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태이다. 동일한 안정화 효과를 더 적은 연산으로 달성하며, LLaMA 이후 대부분의 현대 LLM에서 Pre-Norm 방식과 함께 표준으로 사용된다.

### 4. SwiGLU

SwiGLU는 SiLU 활성화와 게이트 메커니즘을 결합한 FFN 활성화 함수이다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, GELU/ReLU 대비 동일 파라미터에서 더 나은 성능을 제공한다. FFN 차원을 $\frac{2}{3} \times 4d$로 조정하여 파라미터 수를 유지한다.


## 벤치마크/성능

| 벤치마크 | Yi | 비교 모델 |
|---------|--------|---------|
| **MMLU** | **76.3%** | - |
| **HumanEval** | **23.1%** | - |


## 실무 활용

### 1. 파인튜닝 베이스 모델
Yi은 오픈소스로 공개되어 LoRA, QLoRA 등의 PEFT 기법을 활용한 도메인 특화 파인튜닝이 가능하다. 의료, 법률, 금융 등 특정 도메인의 데이터로 미세조정하면 전문적인 AI 어시스턴트를 구축할 수 있다.

### 2. 추론 배포
Yi은 다양한 추론 프레임워크(vLLM, TGI, ONNX Runtime 등)에서 지원되며, 양자화(GPTQ, AWQ, GGUF)를 통해 효율적인 서버 배포가 가능하다.

### 3. 연구 베이스라인
Yi은 GQA, RoPE 연구의 표준 베이스라인으로 활용된다.

## 한계 및 전망

### 한계

1. **배포 인프라**: 6B / 34B 규모의 모델은 충분한 GPU 인프라가 필요하다.
2. **학습 데이터 편향**: 사전 학습 데이터의 특성에 따라 특정 도메인이나 언어에서 편향이 존재할 수 있다.
3. **환각(Hallucination)**: 모든 언어 모델과 마찬가지로 사실이 아닌 정보를 자신 있게 생성할 수 있으며, 사실 검증 메커니즘이 필요하다.

### 전망

Yi은 GQA, RoPE, RMSNorm 분야에서의 강점을 바탕으로, 향후 더 발전된 후속 모델이나 특화된 변형 모델로 진화할 것으로 예상된다. 데이터 품질 개선과 효율적 학습 기법의 발전이 핵심 연구 방향이다.
### 위치 인코딩: RoPE

RoPE(Rotary Position Embedding)는 위치 정보를 복소수 회전으로 인코딩하여 상대적 위치를 자연스럽게 포착한다:

$$f(x_m, m) = x_m e^{im\theta}, \quad \theta_j = 10000^{-2j/d}$$

이 방식은 절대 위치 임베딩의 한계를 극복하며, 학습 시 보지 못한 더 긴 시퀀스에 대한 외삽(extrapolation)이 가능하다는 핵심 장점이 있다. NTK-aware Scaling이나 YaRN 등의 확장 기법을 적용하면 학습 컨텍스트의 수십 배까지 외삽할 수 있다.

### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Yi은 6B / 34B 규모의 파라미터를 가지며, 200000 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Yi은 6B / 34B 규모의 파라미터를 가지며, 200000 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Yi은 6B / 34B 규모의 파라미터를 가지며, 200000 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Yi은 6B / 34B 규모의 파라미터를 가지며, 200000 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Yi은 6B / 34B 규모의 파라미터를 가지며, 200000 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.

## 참고 자료

- [논문](https://arxiv.org/abs/2403.04652)

## 관련 문서

- [[llama|LLaMA: Open and Efficient Foundation Language Models]] — 영감
