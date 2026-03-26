# LLaMA: 오픈소스 LLM 혁명의 기폭제

## 개요

**LLaMA**(Large Language Model Meta AI)는 Meta AI가 2023년 2월 연구자 대상으로 공개한 오픈소스 LLM 시리즈로, **'공개 데이터만으로도 강력한 모델을 만들 수 있다'**는 명제를 입증했다. Chinchilla 스케일링 법칙을 따라 작은 파라미터로 더 많은 토큰을 학습하는 전략을 취해, 65B LLaMA가 GPT-3(175B)에 필적하고 **13B 모델이 GPT-3를 여러 벤치마크에서 능가**했다.

가중치 공개로 Alpaca, Vicuna, WizardLM 등 수백 개의 파생 모델이 탄생하며 오픈소스 LLM 생태계 폭발의 기폭제가 되었다. 이후 거의 모든 오픈 LLM(LLaMA 2, Mistral, Yi, Qwen 등)이 LLaMA 아키텍처를 기반으로 삼는다.

**참고 논문**: [LLaMA: Open and Efficient Foundation Language Models](https://arxiv.org/abs/2302.13971) (Touvron et al., 2023)

## 아키텍처 상세

### GPT 대비 3대 아키텍처 개선

LLaMA는 GPT-2/3의 Transformer Decoder 구조에서 3가지 핵심 개선을 적용했다:

#### 1. RMSNorm (Pre-Norm)

$$\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n} \sum_{i=1}^{n} x_i^2}} \cdot \gamma$$

LayerNorm에서 평균 계산을 생략한 RMSNorm을 어텐션 **전에** 적용한다. 이는 학습 안정성을 높이면서 연산량을 줄인다.

#### 2. SwiGLU 활성화

$$\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$$

GELU/ReLU 대비 동일 파라미터 수에서 더 나은 성능을 제공하는 게이팅 활성화 함수이다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 파라미터 수를 유지한다.

#### 3. RoPE (Rotary Position Embedding)

$$f(x_m, m) = x_m e^{im\theta}$$

어텐션 내 상대적 위치를 회전 행렬로 인코딩하여, 학습 시 보지 못한 더 긴 시퀀스에 대한 외삽이 가능하다.

### 모델 사양

| 모델 | 파라미터 | 레이어 | 히든 | 헤드 |
|------|---------|--------|------|------|
| LLaMA-7B | 7B | 32 | 4,096 | 32 |
| LLaMA-13B | 13B | 40 | 5,120 | 40 |
| LLaMA-33B | 33B | 60 | 6,656 | 52 |
| LLaMA-65B | 65B | 80 | 8,192 | 64 |

**토크나이저**: BPE SentencePiece (32K vocab)

## 핵심 혁신

### 1. 공개 데이터만으로 강력한 성능

모든 학습 데이터가 공개 출처이다: CommonCrawl(67%), C4(15%), GitHub(4.5%), Wikipedia(4.5%), Books(4.5%), ArXiv(2.5%), StackExchange(2%). 총 1.4T 토큰.

### 2. Chinchilla 스케일링 법칙 적용

파라미터를 줄이고 데이터를 늘리는 전략으로 GPT-3보다 훨씬 적은 파라미터로 동등한 성능을 달성했다.

### 3. 오픈소스 생태계 폭발

LLaMA의 가중치 공개(초기 유출 후 공식 공개)는 오픈소스 LLM 생태계의 폭발적 성장을 촉발했다:
- **Alpaca** (Stanford): 52K 인스트럭션으로 파인튜닝
- **Vicuna** (LMSYS): ShareGPT 데이터로 파인튜닝
- **WizardLM**: Evol-Instruct로 복잡한 인스트럭션 생성

## 벤치마크/성능

| 벤치마크 | GPT-3 (175B) | LLaMA-13B | LLaMA-65B |
|---------|-------------|----------|----------|
| **MMLU** | 43.9% | **46.9%** | **63.4%** |
| **HumanEval** | - | 15.8% | **23.7%** |
| **HellaSwag** | 78.9% | 76.2% | **84.2%** |
| **NQ (5-shot)** | - | 25.4% | **33.0%** |
| **ARC-C** | - | 47.6% | **56.0%** |

LLaMA-13B는 MMLU에서 GPT-3를 3%p 능가하며, 이는 1/13 파라미터로 달성한 것이다.

## 관련 모델 비교

| 특성 | GPT-3 | Chinchilla | LLaMA | Mistral 7B |
|------|-------|-----------|-------|-----------|
| **파라미터** | 175B | 70B | 65B | 7.3B |
| **학습 토큰** | 300B | 1.4T | **1.4T** | 미공개 |
| **컨텍스트** | 2,048 | 2,048 | 2,048 | 8,192 |
| **오픈소스** | 아니오 | 아니오 | **예** | **예** |
| **아키텍처 영향** | GPT 계열 | - | **LLaMA 계열** | LLaMA 계열 |

## 학습 상세

- **데이터**: CommonCrawl(67%) + C4(15%) + GitHub(4.5%) + Wikipedia(4.5%) + Books(4.5%) + ArXiv(2.5%) + StackExchange(2%), 총 1.4T 토큰
- **옵티마이저**: AdamW, $\beta$=(0.9, 0.95), lr cosine decay (최고 3e-4)
- **배치**: 4M 토큰
- **하드웨어**: 2,048개 A100 80GB (65B 모델: 약 21일)
- **Flash Attention**: 적용하여 학습 효율 향상

## 실무 활용

### 1. 파인튜닝 베이스 모델

```python
from transformers import LlamaForCausalLM, LlamaTokenizer

model = LlamaForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")
tokenizer = LlamaTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
# LoRA, QLoRA 등으로 효율적 파인튜닝 가능
```

### 2. 아키텍처 표준
RMSNorm + SwiGLU + RoPE 조합이 현대 LLM의 사실상 표준이 되었다.

### 3. 양자화 및 경량 추론
GPTQ, GGML 등으로 양자화하여 소비자 하드웨어에서도 실행 가능하다.

## 한계 및 전망

### 한계

1. **짧은 컨텍스트**: 2,048 토큰으로 장문 처리에 제한이 있다.
2. **GQA 미적용**: MHA를 사용하여 추론 시 KV 캐시 비용이 높다.
3. **초기 라이선스 혼란**: 연구 전용으로 시작하여 상업적 활용에 제약이 있었다.

### 전망

LLaMA는 오픈소스 LLM의 '리눅스 순간'을 만든 모델이다. LLaMA 2(상업 라이선스), LLaMA 3(128K 컨텍스트, GQA), LLaMA 4(MoE)로 이어지는 진화는 Meta의 오픈소스 전략의 핵심이며, 전체 AI 생태계의 방향을 바꾸었다.

### 어텐션 메커니즘: MHA

Multi-Head Attention(MHA)은 Transformer의 핵심 메커니즘으로, 입력을 여러 헤드로 분할하여 병렬적으로 어텐션을 계산한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

$$\text{MultiHead}(Q, K, V) = \text{Concat}(\text{head}_1, \ldots, \text{head}_h)W^O$$

각 헤드는 서로 다른 표현 부분공간(subspace)에서 정보를 추출하며, 결과를 결합하여 풍부한 표현을 학습한다. 추론 시에는 모든 Q 헤드에 대해 별도의 KV를 유지해야 하므로 KV 캐시 비용이 높다는 단점이 있다.

### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다.

**모델 규모와 효율**: LLaMA은 7B / 13B / 33B / 65B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: LLaMA은 7B / 13B / 33B / 65B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: LLaMA은 7B / 13B / 33B / 65B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: LLaMA은 7B / 13B / 33B / 65B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: LLaMA은 7B / 13B / 33B / 65B 규모의 파라미터를 가지며, 2048 토큰의 컨텍스트 윈도우를 지원한다. 효율적인 아키텍처 설계를 통해 동급 모델 대비 경쟁력 있는 성능을 달성한다.

---

**참고 논문**: [LLaMA: Open and Efficient Foundation Language Models](https://arxiv.org/abs/2302.13971) (Touvron et al., 2023)

## 관련 문서

- [[chameleon|Chameleon]] — 후속 모델
- [[llama-2|Llama 2: Open Foundation and Fine-Tuned Chat Models]] — 후속 모델
- [[chinchilla|Training Compute-Optimal Large Language Models (Chinchilla)]] — 영감
- [[llava|Visual Instruction Tuning]] — 영감을 줌
- [[mistral-7b|Mistral 7B]] — 영감을 줌
- [[olmo|OLMo: Accelerating the Science of Language Models]] — 영감을 줌
- [[transfusion|Transfusion]] — 영감을 줌
- [[yi|Yi: Open Foundation Models by 01.AI]] — 영감을 줌
