<!-- infographic-hero -->
![PaLM 핵심 요약](figures/infographic.svg)

*Figure: PaLM 한 장 요약 인포그래픽*

# PaLM: 5400억 파라미터와 Chain-of-Thought의 힘

## 개요

PaLM(Pathways Language Model)은 2022년 4월 Google이 발표한 **540B 파라미터**의 대형 언어 모델이다. PaLM의 역사적 의의는 세 가지 측면에서 두드러진다:

1. **최초의 Pathways 모델**: Google의 차세대 분산 학습 인프라인 Pathways 시스템을 활용해 6,144개 TPU v4에서 단일 모델을 효율적으로 학습한 최초의 사례
2. **추론 능력의 폭발**: Chain-of-Thought(CoT) 프롬프팅과 결합할 때 수학, 논리, 상식 추론에서 비약적인 성능 향상을 실증
3. **Google LLM 계보의 출발점**: PaLM 2, Gemini로 이어지는 Google의 LLM 시리즈의 기초

PaLM은 29개 NLP 태스크 중 28개에서 기존 SOTA를 능가하고, BIG-Bench의 65%에서 인간 평균을 초과하며 LLM의 가능성을 새로운 차원으로 끌어올렸다.

다음은 PaLM이 Chain-of-Thought 프롬프팅을 통해 농담 설명과 논리적 추론을 수행하는 예시이다.

![PaLM의 Chain-of-Thought 프롬프팅 예시 - 농담 설명과 논리적 추론](figures/fig_1.png)
*Figure 1: PaLM 540B의 Chain-of-Thought 프롬프팅 예시 - 2-shot 프롬프트로 농담 설명과 논리적 추론을 수행한다. (Source: Chowdhery et al., 2022)*

- **논문**: [PaLM: Scaling Language Modeling with Pathways](https://arxiv.org/abs/2204.02311)
- **라이선스**: Proprietary (비공개)

## 아키텍처 상세

| 구성 요소 | PaLM 8B | PaLM 62B | PaLM 540B |
|-----------|---------|---------|----------|
| 파라미터 수 | 8B | 62B | 540B |
| 레이어 수 | 32 | 64 | **118** |
| Hidden Dim | 4,096 | 8,192 | **18,432** |
| Attention Heads | 16 | 32 | **48** |
| KV Heads | 16 | 32 | **1 (MQA)** |
| Vocab Size | 256,000 | 256,000 | **256,000** |
| Context Length | 2,048 | 2,048 | 2,048 |

### 핵심 아키텍처 선택

PaLM은 당시 개별적으로 연구되던 여러 최적화 기법을 **하나의 모델에 통합**했다:

**1. SwiGLU 활성화 함수**

$$\text{SwiGLU}(x) = \text{Swish}(xW_1) \otimes (xV)$$

여기서 $\text{Swish}(x) = x \cdot \sigma(x)$. ReLU나 GELU 대비 **일관된 성능 향상**을 제공하며, 이후 LLaMA, Mistral 등이 채택했다. SwiGLU는 Gated Linear Unit(GLU) 계열의 활성화 함수로, 입력에 대해 두 개의 선형 변환을 수행한 뒤 하나를 게이트로 사용한다. 이 게이트 메커니즘이 정보 흐름을 선택적으로 제어하여, 단순 활성화 함수 대비 표현력이 높다. 다만 파라미터가 약 50% 증가하므로, FFN 히든 차원을 $\frac{8}{3}d$ 수준으로 조정하여 전체 파라미터 수를 맞추는 것이 일반적이다.

**2. Multi-Query Attention (MQA)**

PaLM 540B에서 모든 Query 헤드가 **단일 Key-Value**를 공유한다. 이를 통해 KV 캐시를 48배 절감하고 추론 속도를 대폭 향상시켰다. 기존 Multi-Head Attention(MHA)에서는 Q, K, V 각각이 $h$개의 헤드를 가지지만, MQA에서는 K와 V가 단 1개의 헤드만 가지고 모든 Q 헤드가 이를 공유한다. 이는 학습 시에는 품질 저하가 거의 없으면서, 추론 시 autoregressive 디코딩의 메모리 대역폭 병목을 극적으로 완화한다. 이후 GQA(Grouped-Query Attention)가 MHA와 MQA의 절충안으로 제안되어 LLaMA 2 등에서 채택되었다.

**3. RoPE (Rotary Position Embedding)**

상대적 위치를 회전 행렬로 인코딩하여 길이 외삽을 가능하게 했다.

**4. Parallel Transformer Block**

GPT-J에서 제안된 Attention+FFN 병렬 계산 구조를 채택하여, 대규모 분산 환경에서의 통신 효율을 개선했다. 기존 Sequential Transformer에서는 Attention 출력이 나온 후 FFN에 입력하는 직렬 구조를 사용하지만, Parallel 방식에서는 동일한 LayerNorm 출력을 Attention과 FFN에 동시에 입력한다. 이를 통해 두 연산의 all-reduce 통신을 하나로 합칠 수 있어 분산 학습에서 통신 오버헤드가 줄어든다. 8B 이상의 대규모 모델에서는 품질 저하 없이 약 15%의 학습 속도 향상을 달성했다:

$$y = x + \text{Attention}(\text{LN}(x)) + \text{FFN}(\text{LN}(x))$$

```python
import torch
import torch.nn as nn

class PaLMBlock(nn.Module):
    """PaLM의 Parallel Transformer Block + SwiGLU 개념적 구현"""
    def __init__(self, d_model, n_heads, d_ff):
        super().__init__()
        self.ln = nn.RMSNorm(d_model)
        self.attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        # SwiGLU FFN
        self.w1 = nn.Linear(d_model, d_ff, bias=False)
        self.v = nn.Linear(d_model, d_ff, bias=False)
        self.w2 = nn.Linear(d_ff, d_model, bias=False)
    
    def swiglu(self, x):
        return nn.functional.silu(self.w1(x)) * self.v(x)
    
    def forward(self, x):
        normed = self.ln(x)
        # Parallel: Attention + SwiGLU FFN 동시 계산
        attn_out, _ = self.attn(normed, normed, normed)
        ffn_out = self.w2(self.swiglu(normed))
        return x + attn_out + ffn_out
```

## 핵심 혁신: Pathways 시스템과 Chain-of-Thought

### Pathways 시스템

기존 LLM은 데이터 병렬화 + 모델 병렬화의 조합으로 학습했지만, Pathways는 **이기종 하드웨어에서 단일 모델을 효율적으로 학습**하는 새로운 패러다임이다:

아래 다이어그램은 Pathways 시스템이 두 개의 TPU v4 Pod에서 교차 그래디언트 전송을 통해 분산 학습을 수행하는 구조를 보여준다.

![Pathways 시스템 분산 학습 구조 다이어그램](figures/fig_2_1.png)
*Figure 2: Pathways 시스템의 2-way 데이터 병렬화 - 두 TPU v4 Pod 간 교차 그래디언트 전송으로 6,144개 칩에서 효율적 분산 학습을 수행한다. (Source: Chowdhery et al., 2022)*

- **6,144개 TPU v4** 칩에서 단일 모델 학습 (2개 TPU v4 Pod, 각 3,072 칩)
- 이전 LLM 대비 **약 2배** 많은 칩 활용
- 통신 병목 최소화: Pod 내 ICI(Inter-Chip Interconnect), Pod 간 DCN(Data Center Network) 활용
- **57.8% MFU(Model FLOP Utilization)** 달성 - 이전 최고 기록인 Megatron-Turing NLG의 약 30%를 크게 상회

Pathways의 핵심 혁신은 SPMD(Single Program Multiple Data) 기반의 유연한 파이프라인 스케줄링이다. 기존 시스템들이 고정된 파이프라인 병렬화를 사용한 반면, Pathways는 각 TPU Pod에서 독립적으로 forward/backward를 실행하고, Pod 간에는 비동기 그래디언트 전송으로 버블(bubble)을 최소화했다. 이러한 설계 덕분에 학습 중 하드웨어 장애 발생 시에도 빠른 복구가 가능했으며, 수주에 걸친 대규모 학습의 안정성을 확보할 수 있었다.

### Chain-of-Thought (CoT) 프롬프팅

PaLM은 CoT 프롬프팅과 결합했을 때 **비약적인 추론 능력 향상**을 보여주었다. 아래 그림은 표준 프롬프팅과 CoT 프롬프팅의 차이를 명확히 보여준다.

![표준 프롬프팅과 Chain-of-Thought 프롬프팅 비교](figures/fig_10.png)
*Figure 3: 표준 프롬프팅 vs Chain-of-Thought 프롬프팅 - CoT는 중간 추론 단계를 명시적으로 생성하여 수학 문제 같은 다단계 추론 정확도를 크게 향상시킨다. (Source: Chowdhery et al., 2022)*

$$P(\text{answer} | \text{question}) \rightarrow P(\text{answer} | \text{question}, \text{reasoning steps})$$

## 벤치마크/성능

| 벤치마크 | PaLM 540B | GPT-3 175B | Gopher 280B | Chinchilla 70B |
|----------|----------|-----------|------------|---------------|
| 29개 NLP 태스크 | **28/29 SOTA** | baseline | - | - |
| BIG-Bench (인간 초과) | **65%** | - | - | - |
| GSM8K (CoT, 8-shot) | **58%** | 55% (ft) | - | - |
| MMLU (5-shot) | **69.3%** | 43.9% | 60.0% | 67.5% |
| HellaSwag | **83.6%** | ~79% | ~80% | - |
| WinoGrande | **85.1%** | ~77% | - | - |

다음은 BIG-bench 58개 공통 태스크에서 PaLM과 기존 모델들의 성능 비교이다.

![BIG-bench 58개 태스크에서의 모델 스케일별 성능 비교](figures/fig_3_1.png)
*Figure 4: BIG-bench 58개 공통 태스크 성능 비교 - PaLM 540B가 GPT-3, Gopher, Chinchilla를 모든 스케일에서 압도하며, 파라미터 수 증가에 따른 명확한 성능 향상을 보인다. (Source: Chowdhery et al., 2022)*

CoT 프롬프팅을 적용한 추론 태스크에서도 PaLM은 광범위한 벤치마크에서 새로운 SOTA를 달성했다.

![CoT 프롬프팅 기반 산술 및 상식 추론 태스크 성능](figures/fig_12.png)
*Figure 5: Chain-of-Thought 프롬프팅 기반 추론 성능 - GSM8K, SVAMP, StrategyQA 등에서 새로운 SOTA를 기록하며, 모델 스케일 증가에 따라 추론 능력이 비약적으로 향상됨을 보여준다. (Source: Chowdhery et al., 2022)*

### 핵심 결과
- 29개 NLP 태스크 중 **28개에서 SOTA**
- BIG-Bench **65%**에서 인간 평균 초과
- GSM8K 수학 문제: CoT 8-shot으로 **58%** (이전 SOTA 55%)
- MMLU **69.3%**로 Chinchilla(67.5%) 능가

## 관련 모델 비교

| 특성 | GPT-3 | Gopher | Chinchilla | PaLM |
|------|-------|--------|-----------|------|
| 파라미터 | 175B | 280B | 70B | **540B** |
| 학습 토큰 | 300B | 300B | 1.4T | **780B** |
| 어텐션 | MHA | MHA | MHA | **MQA** |
| 활성화 | GeLU | GeLU | GeLU | **SwiGLU** |
| 위치 인코딩 | Learned | Relative | Learned | **RoPE** |
| 인프라 | GPU | TPU v3 | TPU v3/v4 | **TPU v4 (6144)** |
| CoT 추론 | 약함 | 보통 | 보통 | **강함** |

## 학습 상세

### 데이터셋
- **780B 토큰** 규모의 다국어 학습 코퍼스
- 영어 웹 문서(웹페이지 27%, Books 13%, Wikipedia 4%) - 전체의 약 50%
- 다국어 웹 문서 - 100개 이상 언어 포함
- **GitHub 소스 코드** - 전체의 약 5%, 코드 생성 능력의 핵심 소스
- 대화 데이터(소셜 미디어) - 대화 능력 강화 목적
- SentencePiece 토크나이저(256K 어휘) 사용 - 다국어 커버리지를 위해 대형 어휘 채택

### 스케일링 분석과 Breakthrough 능력

PaLM의 가장 주목할 만한 발견 중 하나는 **불연속적 능력 출현(discontinuous emergence)**이다. 8B, 62B, 540B 세 스케일에서 실험한 결과, 일부 태스크는 62B까지 무작위 수준이다가 540B에서 갑자기 높은 성능을 보이는 "능력 출현(emergent ability)" 패턴을 보였다. 이는 BIG-Bench의 여러 태스크에서 관찰되었으며, 스케일링에 따른 LLM 능력이 단순한 선형 외삽이 아닌 질적 전환을 포함한다는 중요한 증거가 되었다.

### 학습 인프라
- **TPU v4 Pod 2개 (총 6,144 칩)**
- Pathways 시스템으로 분산 학습
- 파이프라인 병렬화 + 데이터 병렬화 조합
- MFU: **57.8%**

## 실무 활용

### 1. Google 제품 통합
PaLM은 Google의 Bard(현 Gemini)와 다양한 Google Cloud AI 서비스의 기반이 되었다.

### 2. Med-PaLM (의료)
PaLM을 의료 도메인에 파인튜닝한 Med-PaLM은 USMLE(미국 의사 시험) 수준의 성능을 달성했다.

### 3. Sec-PaLM (보안)
사이버 보안 분야에 특화된 버전으로 Google Cloud에서 활용된다.

### 4. Codey (코드)
PaLM을 코드 생성에 특화한 버전으로 Google의 코딩 어시스턴트에 활용된다.

## 한계 및 전망

### 한계
1. **비공개**: 모델 가중치가 공개되지 않아 외부 연구에 제한이 있다. 이는 오픈소스 LLM 생태계(LLaMA, Falcon 등)의 급부상에 비해 PaLM의 학술적 영향력을 제한하는 요인이 되었다
2. **막대한 학습 비용**: 6,144 TPU v4라는 천문학적 자원이 필요하다. 추정 학습 비용은 수백만 달러에 달하며, 이는 소수의 대기업만 접근 가능한 수준이다
3. **컨텍스트 길이**: 2,048 토큰으로 제한적이다. 동시기 GPT-3도 동일한 제약을 가졌으나, 이후 GPT-4(128K), Claude(100K) 등이 컨텍스트를 대폭 확장하면서 이 한계가 더 부각되었다
4. **환각**: 대형 모델임에도 사실과 다른 내용을 생성할 수 있다. 특히 CoT 추론에서 각 단계가 그럴듯하지만 논리적으로 오류가 있는 "faithful but wrong" 추론이 관찰되었다
5. **Chinchilla 비최적**: 780B 토큰은 540B 파라미터에 대한 Chinchilla 최적(약 10.8T)에 크게 못 미치며, 동일 컴퓨트로 더 작은 모델에 더 많은 데이터를 학습했다면 더 나은 성능이 가능했을 수 있다

### 전망
PaLM은 **현대 LLM의 아키텍처 표준(SwiGLU + RoPE + MQA + Parallel Block)을 정립한 모델**이다. 이 조합은 이후 LLaMA, Mistral, Falcon 등 거의 모든 현대 LLM에서 (부분적으로) 채택되었다. PaLM 2로 진화하며 더 효율적인 학습과 다국어 능력을 강화했고, 최종적으로 Gemini 시리즈로 발전하며 Google의 핵심 AI 기반이 되었다.

---

**참고 문헌**
- Chowdhery, A., et al. (2022). "PaLM: Scaling Language Modeling with Pathways." arXiv:2204.02311
- Wei, J., et al. (2022). "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models."
- Anil, R., et al. (2023). "PaLM 2 Technical Report."

## 관련 문서

- [[gemini|Gemini]] - 후속 모델
- [[gpt-3|Language Models are Few-Shot Learners (GPT-3)]] - 영감
