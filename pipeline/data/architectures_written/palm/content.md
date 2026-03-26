# PaLM: 5400억 파라미터와 Chain-of-Thought의 힘

## 개요

PaLM(Pathways Language Model)은 2022년 4월 Google이 발표한 **540B 파라미터**의 대형 언어 모델이다. PaLM의 역사적 의의는 세 가지 측면에서 두드러진다:

1. **최초의 Pathways 모델**: Google의 차세대 분산 학습 인프라인 Pathways 시스템을 활용해 6,144개 TPU v4에서 단일 모델을 효율적으로 학습한 최초의 사례
2. **추론 능력의 폭발**: Chain-of-Thought(CoT) 프롬프팅과 결합할 때 수학, 논리, 상식 추론에서 비약적인 성능 향상을 실증
3. **Google LLM 계보의 출발점**: PaLM 2, Gemini로 이어지는 Google의 LLM 시리즈의 기초

PaLM은 29개 NLP 태스크 중 28개에서 기존 SOTA를 능가하고, BIG-Bench의 65%에서 인간 평균을 초과하며 LLM의 가능성을 새로운 차원으로 끌어올렸다.

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

여기서 $\text{Swish}(x) = x \cdot \sigma(x)$. ReLU나 GELU 대비 **일관된 성능 향상**을 제공하며, 이후 LLaMA, Mistral 등이 채택했다.

**2. Multi-Query Attention (MQA)**

PaLM 540B에서 모든 Query 헤드가 **단일 Key-Value**를 공유한다. 이를 통해 KV 캐시를 48배 절감하고 추론 속도를 대폭 향상시켰다.

**3. RoPE (Rotary Position Embedding)**

상대적 위치를 회전 행렬로 인코딩하여 길이 외삽을 가능하게 했다.

**4. Parallel Transformer Block**

GPT-J에서 제안된 Attention+FFN 병렬 계산 구조를 채택하여, 대규모 분산 환경에서의 통신 효율을 개선했다:

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

- **6,144개 TPU v4** 칩에서 단일 모델 학습
- 이전 LLM 대비 **약 2배** 많은 칩 활용
- 통신 병목 최소화
- 57.8% MFU(Model FLOP Utilization) 달성

### Chain-of-Thought (CoT) 프롬프팅

PaLM은 CoT 프롬프팅과 결합했을 때 **비약적인 추론 능력 향상**을 보여주었다:

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
- 영어 웹 문서 50%
- 다국어 문서, GitHub 소스 코드
- Wikipedia, 뉴스, 도서

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
1. **비공개**: 모델 가중치가 공개되지 않아 외부 연구에 제한이 있다
2. **막대한 학습 비용**: 6,144 TPU v4라는 천문학적 자원이 필요하다
3. **컨텍스트 길이**: 2,048 토큰으로 제한적이다
4. **환각**: 대형 모델임에도 사실과 다른 내용을 생성할 수 있다

### 전망
PaLM은 **현대 LLM의 아키텍처 표준(SwiGLU + RoPE + MQA + Parallel Block)을 정립한 모델**이다. 이 조합은 이후 LLaMA, Mistral, Falcon 등 거의 모든 현대 LLM에서 (부분적으로) 채택되었다. PaLM 2로 진화하며 더 효율적인 학습과 다국어 능력을 강화했고, 최종적으로 Gemini 시리즈로 발전하며 Google의 핵심 AI 기반이 되었다.

---

**참고 문헌**
- Chowdhery, A., et al. (2022). "PaLM: Scaling Language Modeling with Pathways." arXiv:2204.02311
- Wei, J., et al. (2022). "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models."
- Anil, R., et al. (2023). "PaLM 2 Technical Report."

## 관련 문서

- [[gemini|Gemini]] — 후속 모델
- [[gpt-3|Language Models are Few-Shot Learners (GPT-3)]] — 영감
