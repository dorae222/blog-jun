# Phi-3

**Microsoft** · **2024-04-23** · **Decoder-only** · **Dense** · **오픈소스**

## 개요

Microsoft가 2024년 4월 공개한 소형 언어 모델(SLM) 시리즈로, '아키텍처 혁신보다 데이터 품질이 더 중요하다'는 명제를 실증한 모델이다. GPT-4를 활용해 생성한 교과서 수준의 합성 데이터를 핵심 학습 자원으로 삼아, 3.8B(Phi-3-mini) 파라미터로 GPT-3.5 수준의 추론 능력을 달성했다. 128K 컨텍스트(LongRoPE로 확장)와 ONNX/DirectML 지원으로 스마트폰·엣지 디바이스에서 로컬 실행이 가능하여, 프라이버시 중시 엣지 AI 응용에 새로운 가능성을 열었다.

![Phi-3 아키텍처 - LongRoPE 128K 컨텍스트와 교과서 품질 합성 데이터 기반 3.8B 소형 언어 모델 구조](figures/architecture.svg)

*Figure 1: Phi-3 아키텍처 - LLaMA-2 유사 Decoder-only Transformer에 LongRoPE로 128K 컨텍스트를 확장하고, 교과서 수준 합성 데이터 3.3T 토큰으로 학습한 엣지 AI 최적화 모델이다.*

다음은 4비트 양자화된 Phi-3-mini가 iPhone A16 Bionic 칩에서 네이티브로 실행되는 모습으로, 초당 12토큰 이상을 생성하며 엣지 AI의 가능성을 보여준다.

![Phi-3-mini iPhone 네이티브 실행 - 4비트 양자화로 초당 12토큰 이상 생성](figures/fig_1_1.png)
*Figure 1: Phi-3-mini 모바일 실행 - 4비트 양자화된 Phi-3-mini가 iPhone A16 Bionic에서 네이티브로 실행되어, 시 생성 태스크를 처리하는 모습. (Source: Abdin et al., 2024)*

## 아키텍처 상세

핵심 혁신은 아키텍처가 아니라 데이터 큐레이션이다. Phi-1에서 시작된 '교과서 품질(textbook quality)' 합성 데이터 전략을 Phi-3에서 완성: (1) GPT-4로 생성한 교과서·문제집 형태 합성 데이터, (2) 고품질 필터링된 웹 데이터, (3) 코드 데이터 강화. 3.3T 토큰 학습. 아키텍처는 LLaMA-2와 유사한 Decoder-only Transformer에 LongRoPE(위치 인코딩을 점진적으로 외삽)로 128K 컨텍스트 달성. Phi-3-mini: MMLU 68.8%(Mistral-7B: 61.7%), GSM8K 82.0%.

## 모델 사양

| 항목 | 값 |
|------|---|
| 파라미터 | 3.8B (mini) / 7B (small) / 14B (medium) |
| 컨텍스트 길이 | 128000 |
| 어텐션 | MHA / GQA |
| 정규화 | LayerNorm |
| 활성화 | GELU |
| 위치 인코딩 | RoPE |
| 어휘 크기 | 32064 |
| 히든 차원 | 3072 (mini) / 4096 (small) / 5120 (medium) |
| 레이어 수 | 32 (mini) / 32 (small) / 40 (medium) |
| 어텐션 헤드 | 32 (mini) / 32 (small) / 40 (medium) |

### 핵심 개념

- **Data Quality**
- **Synthetic Data**
- **SLM**
- **RoPE**
- **LongRoPE**
- **Edge AI**

## 학습

3.3T 토큰(합성 교과서 데이터 + 필터링된 웹 + 코드). Flash Attention 2 + 모델 병렬화. 사전 학습 후 Chat 버전은 SFT + DPO 정렬. A100 80GB GPU 클러스터. LongRoPE: 짧은 컨텍스트(4K)로 학습 후 점진적 컨텍스트 길이 연장 파인튜닝으로 128K 달성.

### 관련 모델

- **phi** - 발전 기반

### 어텐션 메커니즘: GQA

GQA(Grouped Query Attention)는 Query 헤드를 여러 그룹으로 나누어 각 그룹이 하나의 KV 헤드를 공유하는 어텐션 변형이다:

$$\text{GQA}: Q \in \mathbb{R}^{n_h \times d_h}, \quad K, V \in \mathbb{R}^{n_g \times d_h}, \quad n_g \ll n_h$$

이를 통해 MHA 대비 KV 캐시 메모리를 $n_h / n_g$배 절감하면서도 MHA에 근접하는 성능을 유지한다. MQA(Multi-Query Attention)가 단일 KV 헤드로 인해 품질 저하가 발생할 수 있는 반면, GQA는 적절한 수의 KV 그룹을 사용하여 성능과 효율의 균형을 맞춘다.
### 실무 코드 예시

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("phi-3", torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("phi-3")

# Phi-3 추론 예시
messages = [{"role": "user", "content": "트랜스포머 아키텍처의 핵심 원리를 설명해줘"}]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=500, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 핵심 혁신

아래 그래프는 Phi 시리즈와 LLaMA-2 시리즈의 스케일링 법칙을 비교한 것으로, 동일 데이터에서 학습된 LLaMA-2 대비 데이터 최적 체제(Data Optimal Regime)에서 Phi 시리즈가 훨씬 낮은 MMLU 오류율을 달성함을 보여준다.

![데이터 최적 스케일링 법칙 - Phi vs LLaMA-2 모델 크기 대비 MMLU 오류율](figures/fig_2.png)
*Figure 2: 데이터 최적 스케일링 법칙 - Phi 시리즈(파란색/빨간색)가 동일 데이터의 LLaMA-2(보라색/초록색) 대비 모든 규모에서 낮은 MMLU 오류율을 달성하여, 데이터 품질의 중요성을 입증한다. (Source: Abdin et al., 2024)*

### 1. Data Quality

데이터 품질은 모델 성능에 있어 데이터 양이나 모델 크기보다 더 결정적인 요소임이 Phi 시리즈를 통해 실증되었다. 고품질 합성 데이터, 체계적 필터링, 도메인별 데이터 믹싱 비율 조정이 핵심이며, 'Textbooks Are All You Need'라는 슬로건이 이 철학을 대표한다.

### 2. Synthetic Data

합성 데이터는 GPT-4 등 대형 모델을 활용하여 교과서 형태의 고품질 학습 데이터를 생성하는 기법이다. 데이터 부족 문제를 해결하고 학습 효율을 극대화하며, 특히 코드, 수학, 과학 추론 데이터에서 효과적이다. 합성 데이터의 다양성과 품질이 모델 성능에 직접적 영향을 미친다.

### 3. SLM

SLM(Small Language Model)은 수십억 파라미터 이하의 경량 모델로, Phi-3-mini(3.8B)가 GPT-3.5 수준의 성능을 달성하여 대표적 사례가 되었다. ONNX/DirectML을 통한 엣지 배포와 양자화(INT4)를 통한 스마트폰 실행이 가능하다.

### 4. RoPE

RoPE(Rotary Position Embedding)는 위치 정보를 회전 행렬로 인코딩하여 상대적 위치를 자연스럽게 포착하며, 시퀀스 길이 외삽이 가능하다. NTK-aware Scaling이나 YaRN 확장으로 학습 컨텍스트의 수십 배 길이까지 외삽할 수 있어, 현대 LLM의 사실상 표준 위치 인코딩이다.


## 벤치마크/성능

| 벤치마크 | Phi-3 | 비교 모델 |
|---------|--------|---------|
| **MMLU** | **68.8%** | - |
| **GSM8K** | **82.0%** | - |


## 실무 활용

### 1. 파인튜닝 베이스 모델
Phi-3은 오픈소스로 공개되어 LoRA, QLoRA 등의 PEFT 기법을 활용한 도메인 특화 파인튜닝이 가능하다. 의료, 법률, 금융 등 특정 도메인의 데이터로 미세조정하면 전문적인 AI 어시스턴트를 구축할 수 있다.

### 2. 추론 배포
Phi-3은 다양한 추론 프레임워크(vLLM, TGI, ONNX Runtime 등)에서 지원되며, 양자화(GPTQ, AWQ, GGUF)를 통해 엣지 디바이스에서도 실행할 수 있다.

### 3. 연구 베이스라인
Phi-3은 Data Quality, Synthetic Data 연구의 표준 베이스라인으로 활용된다.

아래는 Phi-3-mini가 검색 없이 사용자의 질문에 직접 응답하는 모습으로, 3.8B 소형 모델임에도 상세한 일정 계획 등 실용적인 태스크를 처리하는 능력을 보여준다.

![Phi-3-mini 응답 예시 - 검색 없이 상세한 여행 일정 생성](figures/fig_4_1.png)
*Figure 4: Phi-3-mini 응답 품질 - 3.8B 파라미터의 소형 모델이 검색 없이도 Alaska Skagway 일일 여행 일정을 상세하게 생성하는 모습. (Source: Abdin et al., 2024)*

다음 그래프는 안전성 정렬(safety alignment) 전후의 유해 응답 비율을 비교한 것으로, 안전성 학습이 다양한 유해 카테고리에서 효과적으로 작동함을 보여준다.

![안전성 정렬 전후 유해 응답 비율 비교 - 카테고리별 개선](figures/fig_3.png)
*Figure 3: 안전성 정렬 효과 - 안전성 학습 전(파란색) 대비 후(주황색)로 모든 유해 카테고리에서 유해 응답 비율이 크게 감소한다. (Source: Abdin et al., 2024)*

## 한계 및 전망

### 한계

1. **배포 인프라**: 3.8B (mini) / 7B (small) / 14B (medium) 규모의 모델은 충분한 GPU 인프라가 필요하다.
2. **학습 데이터 편향**: 사전 학습 데이터의 특성에 따라 특정 도메인이나 언어에서 편향이 존재할 수 있다.
3. **환각(Hallucination)**: 모든 언어 모델과 마찬가지로 사실이 아닌 정보를 자신 있게 생성할 수 있으며, 사실 검증 메커니즘이 필요하다.

### 전망

Phi-3은 Data Quality, Synthetic Data, SLM 분야에서의 강점을 바탕으로, 향후 더 발전된 후속 모델이나 특화된 변형 모델로 진화할 것으로 예상된다. 데이터 품질 개선과 효율적 학습 기법의 발전이 핵심 연구 방향이다.
### 위치 인코딩: RoPE

RoPE(Rotary Position Embedding)는 위치 정보를 복소수 회전으로 인코딩하여 상대적 위치를 자연스럽게 포착한다:

$$f(x_m, m) = x_m e^{im\theta}, \quad \theta_j = 10000^{-2j/d}$$

이 방식은 절대 위치 임베딩의 한계를 극복하며, 학습 시 보지 못한 더 긴 시퀀스에 대한 외삽(extrapolation)이 가능하다는 핵심 장점이 있다. NTK-aware Scaling이나 YaRN 등의 확장 기법을 적용하면 학습 컨텍스트의 수십 배까지 외삽할 수 있다.

### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: Phi-3은 3.8B (mini) / 7B (small) / 14B (medium) 규모의 파라미터를 가지며, 128000 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: Phi-3은 3.8B (mini) / 7B (small) / 14B (medium) 규모의 파라미터를 가지며, 128000 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: Phi-3은 3.8B (mini) / 7B (small) / 14B (medium) 규모의 파라미터를 가지며, 128000 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: LayerNorm을 사용하여 각 레이어의 입력을 정규화한다. $\text{LayerNorm}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$ 형태로, 평균과 분산을 사용하여 입력을 정규화한다. 이는 깊은 네트워크에서의 학습 안정성을 보장하는 핵심 기법이다.

**활성화 함수**: GELU 활성화 함수를 사용한다. $\text{GELU}(x) = x \cdot \Phi(x)$로, 가우시안 누적 분포 함수를 통해 입력에 따라 확률적 게이팅 효과를 제공한다. ReLU의 hard threshold와 달리 부드러운 비선형성을 제공하여 학습 안정성이 향상된다.


**모델 규모와 효율**: Phi-3은 3.8B (mini) / 7B (small) / 14B (medium) 규모의 파라미터를 가지며, 128000 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.

## 참고 자료

- [논문](https://arxiv.org/abs/2404.14219)

## 관련 문서

- [[phi|Phi]] - 발전 기반
- [[phi-4-multimodal|Phi-4-Multimodal]] - 후속 모델
- [[phi-4-reasoning|Phi-4 Reasoning]] - 후속 모델
