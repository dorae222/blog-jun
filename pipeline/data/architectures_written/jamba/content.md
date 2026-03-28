# Jamba: Transformer-Mamba 하이브리드의 첫 상용 구현

## 개요

**Jamba**는 AI21 Labs가 2024년 3월 28일 공개한 최초의 상용급 **Transformer-Mamba 하이브리드** 아키텍처 모델이다. Transformer의 어텐션 메커니즘이 가진 $O(n^2)$ 메모리 복잡도와, 순수 SSM(State Space Model) 모델이 가진 전역 의존성 포착 한계를 동시에 극복하기 위해 두 구조를 하나의 모델에 결합했다.

52B 전체 파라미터 중 **12B만 활성화**하는 MoE(Mixture of Experts) 구조를 채용하여 파라미터 효율을 극대화했으며, 256K 토큰 컨텍스트를 **단일 A100 80GB GPU에서 처리**할 수 있는 실용적 효율성을 달성했다. Llama-2-7B 대비 3배 높은 처리량을 보이며, Attention과 SSM의 공존 가능성을 처음으로 대형 모델에서 실증한 이정표적 모델이다.

**참고 논문**: [Jamba: A Hybrid Transformer-Mamba Language Model](https://arxiv.org/abs/2403.19887)

다음 그림은 Jamba의 전체 블록 구조와 각 레이어 유형을 보여준다.

![Jamba 블록 구조와 레이어 유형 - Attention, Mamba, MoE 레이어의 교차 배치](figures/fig_1.png)
*Figure 1: Jamba 블록 구조 - (a) Mamba와 Attention 레이어의 교차 배치, (b) 각 레이어 유형의 내부 구성. Attention:Mamba = 1:7 비율로 MoE가 매 2번째 레이어에 적용된다. (Source: Lieber et al., 2024)*

## 아키텍처 상세

### Attention:Mamba 비율 설계

32개 레이어 중 **8개가 Attention, 24개가 Mamba**로, 1:7 비율(정확히는 1:3 반복 블록)로 교차 배치된다:

| 블록 구성 (반복 8회) | 레이어 유형 |
|---------------------|------------|
| 레이어 1-3 | Mamba + MoE |
| 레이어 4 | Attention + MoE |

### Mamba (Selective SSM)

Mamba는 Gu & Dao(2023)가 제안한 **선택적 상태 공간 모델(Selective State Space Model, S6)**이다. 핵심은 입력에 따라 SSM의 파라미터를 동적으로 조절하여 관련 정보를 선택적으로 기억하는 것이다:

$$h_t = \bar{A} h_{t-1} + \bar{B} x_t, \quad y_t = C h_t$$

여기서 $\bar{A}, \bar{B}$는 입력 $x_t$에 의존하는 이산화된 상태 전이 행렬이다. SSM의 핵심 장점은 시퀀스 길이에 대해 **선형 복잡도** $O(n)$를 가진다는 것으로, Attention의 $O(n^2)$ 대비 긴 시퀀스에서 극적인 효율 향상을 제공한다.

### MoE 통합

| 구성 요소 | 사양 |
|-----------|------|
| **전체 파라미터** | 52B |
| **활성 파라미터** | 12B |
| **전문가 수** | 16 |
| **활성 전문가** | 2 (토큰당) |
| **히든 차원** | 4,096 |
| **어텐션 헤드** | 32 |
| **컨텍스트** | 256,000 |
| **어휘** | 65,536 |

MoE는 주로 Mamba 레이어에 적용되며, 각 토큰은 16개 전문가 중 2개만 활성화하여 처리한다.

### 메모리 효율

Jamba의 하이브리드 설계가 제공하는 메모리 효율은 극적이다:

| 모델 | 256K 컨텍스트 시 GPU 요구 |
|------|-------------------------|
| Llama-2-70B | A100 80GB **8장** |
| Mixtral 8x7B | A100 80GB **4장** |
| **Jamba** | A100 80GB **1장** |

Mamba 레이어는 KV 캐시가 필요 없이 고정 크기의 상태 벡터만 유지하므로, 시퀀스 길이가 길어져도 메모리 사용량이 거의 증가하지 않는다.

아래 그래프는 단일 A100 80GB GPU에 적재 가능한 최대 컨텍스트 길이를 모델별로 비교한 것이다.

![단일 A100 80GB GPU에서의 최대 컨텍스트 길이 비교 - Jamba가 가장 긴 컨텍스트를 지원한다](figures/fig_2.png)
*Figure 2: 단일 A100 80GB GPU 기준 최대 컨텍스트 길이 비교 - Jamba는 Mixtral 대비 2배, Llama-2-70B 대비 7배 긴 컨텍스트를 처리할 수 있다. (Source: Lieber et al., 2024)*

## 핵심 혁신

### 1. Attention + SSM 하이브리드의 실용성 입증

이론적으로 제안된 Attention-SSM 결합을 52B 규모의 상용급 모델에서 처음으로 성공적으로 구현했다.

### 2. 선형 복잡도 장문 처리

Mamba 레이어가 24/32(75%)를 차지하므로, 전체 모델의 메모리 복잡도가 시퀀스 길이에 대해 거의 선형에 가깝다.

### 3. MoE + SSM의 삼중 하이브리드

Attention, Mamba(SSM), MoE라는 세 가지 효율화 기법을 동시에 결합한 최초의 모델이다.

다양한 배치 크기에서의 처리량 비교는 Jamba의 효율성을 명확히 보여준다.

![단일 GPU 환경에서 배치 크기별 처리량 비교 - Jamba가 Mixtral 대비 3배 높은 처리량을 달성](figures/fig_3_1.png)
*Figure 3: 단일 A100 GPU에서의 배치 크기별 처리량 비교 - Jamba는 대규모 배치 처리 시 Mixtral 대비 3배 이상의 처리량을 달성하며, Llama-2-70B는 큰 배치에서 메모리 한계에 도달한다. (Source: Lieber et al., 2024)*

## 벤치마크/성능

| 벤치마크 | Jamba (12B active) | Llama-2-7B | Mixtral 8x7B |
|---------|-------------------|-----------|-------------|
| **HellaSwag** | **87.1%** | 76.0% | 86.7% |
| **Arc-Challenge** | **59.4%** | 46.3% | 61.1% |
| **MMLU** | ~67% | 45.3% | 70.6% |
| **처리량** | **3x** | 1x (기준) | ~1.5x |
| **256K KV 캐시** | **~1GB** | ~8GB | ~4GB |

## 관련 모델 비교

| 특성 | Llama-2 | Mixtral | Mamba | Jamba |
|------|---------|---------|-------|-------|
| **아키텍처** | Transformer | MoE Transformer | Pure SSM | **Hybrid** |
| **어텐션** | MHA | GQA | 없음 | **MHA+SSM** |
| **장문 효율** | $O(n^2)$ | $O(n^2)$ | $O(n)$ | **~$O(n)$** |
| **KV 캐시** | 큼 | 중간 | 없음 | **최소** |
| **전역 의존성** | 강함 | 강함 | 약함 | **강함** |

다음은 256K 토큰 길이까지의 Needle-in-a-Haystack 평가 결과로, Jamba의 장문 검색 능력을 시각적으로 보여준다.

![Jamba의 Needle-in-a-Haystack 평가 결과 - 256K 토큰까지 안정적인 검색 성능](figures/fig_6.png)
*Figure 4: Needle-in-a-Haystack 평가 - Jamba는 256K 토큰 컨텍스트 내 임의 위치에 삽입된 정보를 안정적으로 검색하는 능력을 보여준다. (Source: Lieber et al., 2024)*

## 학습 상세

- **데이터**: 내부 데이터셋 (구체적 구성 미공개), 추정 1T 토큰 이상
- **정렬**: Jamba-Instruct는 SFT + DPO 적용
- **공개**: Hugging Face에 Apache 2.0 라이선스로 가중치 공개
- **컨텍스트**: Mamba의 SSM 상태로 256K 처리, 슬라이딩 윈도우 불필요

Attention-Mamba 하이브리드의 학습 효율성은 아래 학습 손실 곡선에서 확인할 수 있다.

![Attention-Mamba 비율별 학습 손실 곡선 비교 - 하이브리드가 순수 Attention과 순수 Mamba보다 낮은 손실을 달성](figures/fig_7.png)
*Figure 5: Attention-Mamba 비율별 학습 손실 비교 (1.3B 파라미터) - 하이브리드 구조(1:3, 1:7 비율)가 순수 Attention 및 순수 Mamba 대비 전 학습 과정에서 일관되게 낮은 손실을 달성한다. (Source: Lieber et al., 2024)*

## 실무 활용

### 1. 장문 문서 분석

256K 컨텍스트로 법률 계약서, 기술 사양서, 논문 전문을 한 번에 처리할 수 있다.

### 2. 단일 GPU 추론

12B 활성 파라미터로 A100 80GB 1장에서 256K 컨텍스트 처리가 가능하여, 온프레미스 배포 비용을 크게 절감한다.

### 3. 고처리량 서빙

Llama-2-7B 대비 3배의 처리량으로, 동시 요청이 많은 API 서비스에 적합하다.

## 한계 및 전망

### 한계

1. **순수 Attention 대비 정밀 검색 한계**: Mamba 레이어는 전역 어텐션이 없으므로, 특정 위치의 정확한 정보 검색에서 순수 Transformer 대비 약할 수 있다.
2. **학습 데이터 미공개**: 구체적 데이터 구성이 공개되지 않았다.
3. **Mamba 생태계 미성숙**: Mamba 커널의 하드웨어 최적화가 Attention 대비 아직 부족하다.

### 전망

Jamba는 하이브리드 SSM-Transformer 아키텍처의 실용성을 입증한 선구적 모델로, Jamba 1.6(398B)으로 진화하며 기업용 장문 처리에 특화되고 있다. Mamba2, RWKV v6 등 선형 복잡도 아키텍처와의 경쟁 속에서, 하이브리드 접근법은 유망한 방향으로 자리잡고 있다.

### 위치 인코딩: RoPE

RoPE(Rotary Position Embedding)는 위치 정보를 복소수 회전으로 인코딩하여 상대적 위치를 자연스럽게 포착한다:

$$f(x_m, m) = x_m e^{im\theta}, \quad \theta_j = 10000^{-2j/d}$$

이 방식은 절대 위치 임베딩의 한계를 극복하며, 학습 시 보지 못한 더 긴 시퀀스에 대한 외삽(extrapolation)이 가능하다는 핵심 장점이 있다. NTK-aware Scaling이나 YaRN 등의 확장 기법을 적용하면 학습 컨텍스트의 수십 배까지 외삽할 수 있다.
### 실무 코드 예시

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("jamba", torch_dtype=torch.bfloat16, device_map="auto")
tokenizer = AutoTokenizer.from_pretrained("jamba")

# Jamba 추론 예시
messages = [{"role": "user", "content": "트랜스포머 아키텍처의 핵심 원리를 설명해줘"}]
inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to(model.device)
outputs = model.generate(inputs, max_new_tokens=500, temperature=0.7)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```
### 스케일링 법칙과의 관계

Chinchilla 스케일링 법칙에 따르면, 모델 파라미터 수 $N$과 학습 토큰 수 $D$의 최적 비율은 다음과 같이 결정된다:

$$L(N, D) = \frac{A}{N^\alpha} + \frac{B}{D^\beta} + E$$

여기서 $\alpha \approx 0.34$, $\beta \approx 0.28$이다. 이 법칙은 학습 예산이 주어졌을 때 모델 크기와 데이터 양의 최적 균형점을 결정하는 데 핵심적인 역할을 하며, 이 모델의 학습 전략에도 영향을 미쳤을 것으로 추정된다.
### MoE 라우팅

Jamba은 16개의 전문가 중 2개를 활성화하는 희소 MoE(Sparse Mixture of Experts) 구조를 사용한다. 라우팅 메커니즘은 각 토큰을 가장 적합한 전문가에 할당한다:

$$g_i = \text{TopK}(\text{softmax}(W_r \cdot x), K=2)$$

$$y = \sum_{i \in \text{TopK}} g_i \cdot E_i(x)$$

각 토큰은 전체 16개 전문가 중 2개만 활성화하므로, 총 파라미터 수 대비 추론 비용이 크게 절감된다. 이를 통해 대규모 파라미터의 표현력과 소규모 활성 파라미터의 효율성을 동시에 달성한다. 전문가 간 부하 균형을 위해 보조 손실이나 동적 편향 조정이 사용된다.

### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다.

**모델 규모와 효율**: Jamba은 52B total / 12B active 규모의 파라미터를 가지며, 256000 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Jamba은 52B total / 12B active 규모의 파라미터를 가지며, 256000 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.


### 아키텍처 설계 분석

**정규화**: RMSNorm을 Pre-Norm 방식으로 적용하여 학습 안정성을 확보한다. RMSNorm은 LayerNorm 대비 평균 계산을 생략하여 연산 효율이 높으면서도 동등한 안정화 효과를 제공한다. $\text{RMSNorm}(x) = \frac{x}{\sqrt{\frac{1}{n}\sum x_i^2}} \cdot \gamma$ 형태로, 학습 가능한 스케일 파라미터 $\gamma$만 사용한다.

**활성화 함수**: SwiGLU 활성화 함수를 사용하여 FFN의 표현력을 높인다. $\text{SwiGLU}(x) = \text{SiLU}(xW_1) \otimes (xW_2)$ 형태로, 게이트 메커니즘이 정보 흐름을 선택적으로 제어한다. FFN 차원이 $\frac{2}{3} \times 4d$로 조정되어 게이트 프로젝션에 사용되는 추가 파라미터를 보상한다.


**모델 규모와 효율**: Jamba은 52B total / 12B active 규모의 파라미터를 가지며, 256000 토큰의 컨텍스트 윈도우를 지원한다. MoE 구조의 희소 활성화 덕분에 총 파라미터 대비 추론 비용이 크게 절감된다.

---

**참고 논문**: [Jamba: A Hybrid Transformer-Mamba Language Model](https://arxiv.org/abs/2403.19887)

## 관련 문서

- [[jamba-1-6|Jamba 1.6]] - 후속 모델
- [[mamba|Mamba: Linear-Time Sequence Modeling with Selective State Spaces]] - 영감
- [[mixtral|Mixtral of Experts]] - 영감
