---
title: "Phi: 오픈소스 대규모 언어 모델"
slug: phi
category: llm
tags: ["Microsoft", "Parameter Efficiency", "Phi", "Small Language Models", "Synthetic Data", "Textbook Quality Data"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.439317+00:00"
architecture_entry: phi
---

# Phi

**Microsoft** · **2023-06-20** · **Decoder-only** · **Dense** · **오픈소스**

## 개요

Phi는 Microsoft Research가 2023년 발표한 소형 언어 모델(SLM) 시리즈로, phi-1(1.3B)과 phi-1.5(1.3B), phi-2(2.7B)로 구성된다. 핵심 철학은 "교과서 수준의 고품질 데이터(Textbook Quality Data)"로, 수십억 파라미터 규모 모델에 필적하는 성능을 단 10억~30억 파라미터로 달성하였다. 코드 생성과 수학 추론 분야에서 특히 뛰어난 성능을 보이며, 모델 크기 대비 성능 효율(parameter efficiency)의 중요성을 강조한 연구이다. 이 시리즈는 소형 모델도 충분한 데이터 품질을 갖추면 대형 모델에 근접할 수 있다는 패러다임을 제시하였다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

Phi 시리즈는 GPT-4로 생성한 합성 교과서 데이터(약 1B 토큰)와 엄선된 고품질 웹 코드를 학습 데이터로 활용하는 것이 핵심이다. phi-1은 Python 코드 생성에 특화되어 HumanEval에서 50.6%를 달성하며, 당시 같은 크기 모델 대비 압도적인 성능을 보였다. phi-1.5는 상식 추론과 언어 이해로 범위를 확장하였고, phi-2(2.7B)는 오픈소스 7B·13B 모델들과 견줄 만한 성능을 발휘하였다. 이 연구는 스케일보다 데이터 품질이 성능에 더 결정적일 수 있다는 점을 실증하여 이후 소형 언어 모델 연구 붐을 이끌었다.

## 모델 사양

| 항목 | 값 |
|------|---|
| 파라미터 | 1.3B |
| 컨텍스트 길이 | 2048 |
| 어텐션 | Multi-Head Attention |
| 정규화 | LayerNorm |
| 활성화 | GeLU |
| 위치 인코딩 | Learned Absolute Position Embedding |
| 어휘 크기 | 50257 |
| 히든 차원 | 2048 |
| 레이어 수 | 24 |
| 어텐션 헤드 | 32 |

### 핵심 개념

- **Textbook Quality Data**
- **Small Language Models**
- **Synthetic Data**
- **Parameter Efficiency**

## 학습

phi-1은 약 7B 토큰의 교과서 품질 데이터(합성 데이터 1B + 웹 코드 6B)로 학습하였다. phi-2는 250B 토큰 규모로 확장하여 학습하였으며, 합성 NLP 데이터와 필터링된 웹 데이터를 혼합하였다. 학습에는 A100 GPU 96개가 사용되었고, phi-2 기준 약 14일의 학습 시간이 소요되었다.

### 관련 모델

- **gpt-3** — 영감

### 어텐션 메커니즘: MHA

Multi-Head Attention(MHA)은 Transformer의 핵심 메커니즘으로, 입력을 여러 헤드로 분할하여 병렬적으로 어텐션을 계산한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)W^O$$

각 헤드는 서로 다른 표현 부분공간(subspace)에서 정보를 추출하며, 결과를 결합하여 풍부한 표현을 학습한다. 추론 시에는 모든 Q 헤드에 대해 별도의 KV를 유지해야 하므로 KV 캐시 비용이 높다는 단점이 있다.
### 실무 코드 예시

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("microsoft/phi-2", torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2")

# Phi 추론 예시
messages = [{"role": "user", "content": "트랜스포머 아키텍처의 핵심 원리를 설명해줘"}]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=500, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 핵심 혁신

### 1. Textbook Quality Data

교과서 품질 데이터는 GPT-4 등 대형 모델로 생성한 구조화된 합성 데이터로, 개념 설명→예제→연습문제 형태의 체계적 구성을 갖추어 소형 모델의 학습 효율을 극대화한다. Microsoft Phi 시리즈가 이 접근법을 개척하여, 데이터 품질이 모델 크기보다 더 중요할 수 있음을 실증하였다.

### 2. Small Language Models

소형 언어 모델(SLM)은 수십억 파라미터 이하의 모델로, 엣지 배포, 프라이버시 보호, 비용 절감 등의 장점을 가진다. 교과서 품질 합성 데이터와 증류 기법으로 대형 모델에 근접하는 성능을 달성하며, 스마트폰이나 노트북 같은 로컬 디바이스에서 실행이 가능하다.

### 3. Synthetic Data

합성 데이터는 GPT-4 등 대형 모델을 활용하여 교과서 형태의 고품질 학습 데이터를 생성하는 기법이다. 데이터 부족 문제를 해결하고 학습 효율을 극대화하며, 특히 코드, 수학, 과학 추론 데이터에서 효과적이다. 합성 데이터의 다양성과 품질이 모델 성능에 직접적 영향을 미친다.

### 4. Parameter Efficiency

파라미터 효율은 적은 파라미터로 높은 성능을 달성하는 능력이다. 데이터 품질 최적화, 아키텍처 설계, 학습 전략의 조합이 핵심이며, Phi 시리즈가 1.3B 모델로 7B-13B 모델에 필적하는 성능을 보여 이 개념의 중요성을 입증하였다.


## 벤치마크/성능

Phi은 Textbook Quality Data, Small Language Models, Synthetic Data 분야에서 동급 모델 대비 경쟁력 있는 성능을 보인다.


## 실무 활용

### 1. 파인튜닝 베이스 모델
Phi은 오픈소스로 공개되어 LoRA, QLoRA 등의 PEFT 기법을 활용한 도메인 특화 파인튜닝이 가능하다. 의료, 법률, 금융 등 특정 도메인의 데이터로 미세조정하면 전문적인 AI 어시스턴트를 구축할 수 있다.

### 2. 추론 배포
Phi은 다양한 추론 프레임워크(vLLM, TGI, ONNX Runtime 등)에서 지원되며, 양자화(GPTQ, AWQ, GGUF)를 통해 효율적인 서버 배포가 가능하다.

### 3. 연구 베이스라인
Phi은 Textbook Quality Data, Small Language Models 연구의 표준 베이스라인으로 활용된다.

## 한계 및 전망

### 한계

1. **배포 인프라**: 1.3B 규모의 모델은 비교적 적은 하드웨어로 배포 가능하지만, 최적의 성능을 위해서는 적절한 인프라가 필요하다.
2. **학습 데이터 편향**: 사전 학습 데이터의 특성에 따라 특정 도메인이나 언어에서 편향이 존재할 수 있다.
3. **환각(Hallucination)**: 모든 언어 모델과 마찬가지로 사실이 아닌 정보를 자신 있게 생성할 수 있으며, 사실 검증 메커니즘이 필요하다.

### 전망

Phi은 Textbook Quality Data, Small Language Models, Synthetic Data 분야에서의 강점을 바탕으로, 향후 더 발전된 후속 모델이나 특화된 변형 모델로 진화할 것으로 예상된다. 데이터 품질 개선과 효율적 학습 기법의 발전이 핵심 연구 방향이다.
### 스케일링 법칙과의 관계

Chinchilla 스케일링 법칙에 따르면, 모델 파라미터 수 $N$과 학습 토큰 수 $D$의 최적 비율은 다음과 같이 결정된다:

$$L(N, D) = \frac{A}{N^\alpha} + \frac{B}{D^\beta} + E$$

여기서 $\alpha \approx 0.34$, $\beta \approx 0.28$이다. 이 법칙은 학습 예산이 주어졌을 때 모델 크기와 데이터 양의 최적 균형점을 결정하는 데 핵심적인 역할을 하며, 이 모델의 학습 전략에도 영향을 미쳤을 것으로 추정된다.

### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: Phi은 1.3B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: Phi은 1.3B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: Phi은 1.3B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: Phi은 1.3B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: Phi은 1.3B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.

## 참고 자료

- [논문](https://arxiv.org/abs/2306.11644)
- [코드](https://huggingface.co/microsoft/phi-2)

## 관련 문서

- [[phi-3|Phi-3 Technical Report: A Highly Capable Language Model Locally on Your Phone]] — 후속 모델
- [[gpt-3|Language Models are Few-Shot Learners (GPT-3)]] — 영감
