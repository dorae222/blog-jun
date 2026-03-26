# OLMo

**Allen Institute for AI (AI2)** · **2024-02-01** · **Decoder-only** · **Dense** · **오픈소스**

## 개요

Allen Institute for AI(AI2)가 2024년 2월 공개한 완전 개방형 언어 모델로, 'Open'의 의미를 모델 가중치 공개에서 훨씬 더 나아가 학습 데이터·코드·평가 코드·학습 로그·중간 체크포인트까지 모두 공개한다. 대부분의 '오픈' LLM이 가중치만 공개하는 데 반해, OLMo는 LLM 연구의 완전한 재현성(reproducibility)을 목표로 한다. 학습 데이터셋 Dolma(3T 토큰)도 함께 공개해 학계가 처음부터 끝까지 동일한 결과를 재현할 수 있게 했다. 영리 목적이 아닌 과학적 투명성 중심의 LLM 연구 인프라로서, AI 연구 접근성 민주화에 기여했다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

완전 개방성(Full Openness): 가중치·Dolma 학습 데이터(3T 토큰)·학습 코드(OLMo Python 패키지)·평가 코드(Catwalk)·텐서보드 로그·2000개 이상 중간 체크포인트 모두 Apache 2.0으로 공개. 아키텍처 특이점: 비파라메트릭 LayerNorm(bias=False, affine=False)과 QK-norm으로 학습 안정성 강화. Rotary Position Embedding(RoPE). OLMo-7B: MMLU 52.0%, HellaSwag 78.4%(LLaMA-7B: 76.1%). ALLMo 평가 프레임워크로 재현 가능한 벤치마크 제공.

## 모델 사양

| 항목 | 값 |
|------|---|
| 파라미터 | 1B / 7B / 65B |
| 컨텍스트 길이 | 2048 |
| 어텐션 | MHA |
| 정규화 | LayerNorm (non-parametric) |
| 활성화 | SiLU (SwiGLU) |
| 위치 인코딩 | RoPE |
| 어휘 크기 | 50280 |
| 히든 차원 | 2048 (1B) / 4096 (7B) |
| 레이어 수 | 16 (1B) / 32 (7B) |
| 어텐션 헤드 | 16 (1B) / 32 (7B) |

### 핵심 개념

- **Open Science**
- **Dolma Dataset**
- **RoPE**
- **SwiGLU**
- **Full Transparency**
- **Reproducibility**

## 학습

Dolma v1.6—C4, Pile, Reddit, StackExchange, Wikipedia, Common Crawl 등 조합, 총 3T 토큰. BPE 50,280 vocab(GPT-NeoX 토크나이저 기반). AdamW lr=4e-4, cosine decay to 1e-5, warmup 5000 스텝. 7B: A100 80GB 4096개, 학습 시간 약 25일. 배치 2M 토큰.

### 관련 모델

- **llama** — 영감

### 어텐션 메커니즘: MHA

Multi-Head Attention(MHA)은 Transformer의 핵심 메커니즘으로, 입력을 여러 헤드로 분할하여 병렬적으로 어텐션을 계산한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)W^O$$

각 헤드는 서로 다른 표현 부분공간(subspace)에서 정보를 추출하며, 결과를 결합하여 풍부한 표현을 학습한다. 추론 시에는 모든 Q 헤드에 대해 별도의 KV를 유지해야 하므로 KV 캐시 비용이 높다는 단점이 있다.
### 실무 코드 예시

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("olmo", torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("olmo")

# OLMo 추론 예시
messages = [{"role": "user", "content": "트랜스포머 아키텍처의 핵심 원리를 설명해줘"}]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=500, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 핵심 혁신

### 1. Open Science

오픈 사이언스는 모델 가중치뿐 아니라 학습 데이터, 코드, 로그, 중간 체크포인트까지 모두 공개하여 연구의 완전한 재현성을 보장하는 접근법이다. 대부분의 '오픈' LLM이 가중치만 공개하는 것과 달리, 학습의 모든 단계를 투명하게 공유하여 외부 검증과 협력적 연구를 가능하게 한다.

### 2. Dolma Dataset

Dolma는 AI2가 구축한 3T 토큰 규모의 공개 학습 데이터셋으로, C4, Pile, Reddit, StackExchange, Wikipedia, Common Crawl 등을 조합하였다. LLM 연구의 완전한 재현성을 지원하기 위해 Apache 2.0 라이선스로 공개되었으며, 데이터 수집·필터링·중복 제거 파이프라인도 함께 제공된다.

### 3. RoPE

RoPE(Rotary Position Embedding)는 위치 정보를 회전 행렬로 인코딩하여 상대적 위치를 자연스럽게 포착하며, 시퀀스 길이 외삽이 가능하다. NTK-aware Scaling이나 YaRN 확장으로 학습 컨텍스트의 수십 배 길이까지 외삽할 수 있어, 현대 LLM의 사실상 표준 위치 인코딩이다.

### 4. SwiGLU

SwiGLU는 SiLU 활성화와 게이트 메커니즘을 결합한 FFN 활성화 함수이다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, GELU/ReLU 대비 동일 파라미터에서 더 나은 성능을 제공한다. FFN 차원을 $\frac{2}{3} \times 4d$로 조정하여 파라미터 수를 유지한다.


## 벤치마크/성능

| 벤치마크 | OLMo | 비교 모델 |
|---------|--------|---------|
| **MMLU** | **52.0%** | - |
| **HellaSwag** | **78.4%** | - |


## 실무 활용

### 1. 파인튜닝 베이스 모델
OLMo은 오픈소스로 공개되어 LoRA, QLoRA 등의 PEFT 기법을 활용한 도메인 특화 파인튜닝이 가능하다. 의료, 법률, 금융 등 특정 도메인의 데이터로 미세조정하면 전문적인 AI 어시스턴트를 구축할 수 있다.

### 2. 추론 배포
OLMo은 다양한 추론 프레임워크(vLLM, TGI, ONNX Runtime 등)에서 지원되며, 양자화(GPTQ, AWQ, GGUF)를 통해 효율적인 서버 배포가 가능하다.

### 3. 연구 베이스라인
모든 학습 아티팩트가 공개되어 있어 연구의 완전한 재현이 가능하며, OLMo은 Open Science, Dolma Dataset 연구의 표준 베이스라인으로 활용된다.

## 한계 및 전망

### 한계

1. **배포 인프라**: 1B / 7B / 65B 규모의 모델은 비교적 적은 하드웨어로 배포 가능하지만, 최적의 성능을 위해서는 적절한 인프라가 필요하다.
2. **학습 데이터 편향**: 사전 학습 데이터의 특성에 따라 특정 도메인이나 언어에서 편향이 존재할 수 있다.
3. **환각(Hallucination)**: 모든 언어 모델과 마찬가지로 사실이 아닌 정보를 자신 있게 생성할 수 있으며, 사실 검증 메커니즘이 필요하다.

### 전망

OLMo은 Open Science, Dolma Dataset, RoPE 분야에서의 강점을 바탕으로, 향후 더 발전된 후속 모델이나 특화된 변형 모델로 진화할 것으로 예상된다. 데이터 품질 개선과 효율적 학습 기법의 발전이 핵심 연구 방향이다.
### 위치 인코딩: RoPE

RoPE(Rotary Position Embedding)는 위치 정보를 복소수 회전으로 인코딩하여 상대적 위치를 자연스럽게 포착한다:

$$f(x_m, m) = x_m e^{im\theta}, \quad \theta_j = 10000^{-2j/d}$$

이 방식은 절대 위치 임베딩의 한계를 극복하며, 학습 시 보지 못한 더 긴 시퀀스에 대한 외삽(extrapolation)이 가능하다는 핵심 장점이 있다. NTK-aware Scaling이나 YaRN 등의 확장 기법을 적용하면 학습 컨텍스트의 수십 배까지 외삽할 수 있다.

### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: OLMo은 1B / 7B / 65B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: OLMo은 1B / 7B / 65B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: OLMo은 1B / 7B / 65B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: OLMo은 1B / 7B / 65B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: OLMo은 1B / 7B / 65B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.

## 참고 자료

- [논문](https://arxiv.org/abs/2402.00838)

## 관련 문서

- [[llama|LLaMA: Open and Efficient Foundation Language Models]] — 영감
