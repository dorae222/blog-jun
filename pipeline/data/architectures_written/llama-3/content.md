# LLaMA 3: 오픈소스 LLM의 GPT-4 도전

## 개요

**LLaMA 3**는 Meta가 2024년 4월 18일 공개한 오픈소스 대규모 언어 모델 시리즈로, **8B, 70B, 405B** 세 가지 규모로 제공된다. LLaMA 2 대비 훈련 데이터를 **7.5배(2T→15T 토큰)** 확대하고, 128K 토큰 컨텍스트와 GQA를 전 모델에 도입하여 성능과 효율 모두를 대폭 향상시켰다.

특히 **405B 모델은 오픈소스 모델 중 최초로 GPT-4 수준에 근접**하는 성능을 달성하여 오픈소스 LLM 생태계의 이정표가 되었다. 8B 모델조차 LLaMA 2-70B에 필적하는 성능을 보이며, 데이터 스케일링의 위력을 극적으로 보여주었다.

**참고 논문**: [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783)

## 아키텍처 상세

다음 다이어그램은 LLaMA 3의 전체 아키텍처와 GQA 구조, 핵심 혁신을 보여준다.

![LLaMA 3 전체 아키텍처 — 8B/70B/405B Dense Decoder-Only Transformer with GQA](figures/architecture.png)
*Figure 1: LLaMA 3 아키텍처 — GQA를 전 모델에 적용하고, 128K 어휘, 128K 컨텍스트, SwiGLU 활성화, RoPE 위치 인코딩을 사용하는 Dense Decoder-Only 구조. (Source: LLaMA 3 논문)*

아래 그림은 논문에서 제시한 LLaMA 3의 전체 학습 파이프라인을 보여준다. 텍스트 토큰 입력부터 Self-Attention과 FFN을 반복하여 다음 토큰을 예측하는 자기회귀 디코딩 과정이다.

![LLaMA 3 전체 학습 파이프라인 — 텍스트 토큰 입력부터 자기회귀 디코딩까지](figures/fig_1.png)
*Figure 2: LLaMA 3 학습 파이프라인 — Token Embedding, Self-Attention, FFN 블록이 반복되는 표준 Transformer 구조. 자기회귀 방식으로 다음 토큰을 예측한다. (Source: LLaMA 3 논문)*

### LLaMA 2 대비 핵심 변화

#### 1. GQA 전면 도입

LLaMA 2에서 34B/70B에만 적용했던 GQA를 **전 모델(8B 포함)에 적용**했다:

$$\text{GQA}: Q \in \mathbb{R}^{n_h \times d_h}, \quad K, V \in \mathbb{R}^{n_g \times d_h}$$

8B 모델: Q 32헤드, KV 8헤드. 70B: Q 64헤드, KV 8헤드. 405B: Q 128헤드, KV 8헤드. GQA를 통해 KV 캐시 메모리가 대폭 감소하면서도 MHA 수준의 표현력을 유지한다.

#### 2. 어휘 크기 4배 확장 (32K → 128K)

토크나이저를 **128,256 어휘**로 확장했다. 이는 LLaMA 2의 32K 대비 4배 증가로, 다국어 텍스트의 토큰화 효율이 크게 향상된다. 동일한 텍스트를 더 적은 토큰으로 표현할 수 있어, 실질적인 컨텍스트 길이가 확대되는 효과가 있다.

#### 3. 128K 컨텍스트

LLaMA 2의 4K에서 **32배 확장**했다. RoPE의 기본 주파수를 500,000으로 조정하여 장거리 위치 인코딩 성능을 확보했다.

### 모델 사양

| 모델 | 파라미터 | 레이어 | 히든 | Q 헤드 | KV 헤드 |
|------|---------|--------|------|--------|--------|
| 8B | 8B | 32 | 4,096 | 32 | 8 |
| 70B | 70B | 80 | 8,192 | 64 | 8 |
| 405B | 405B | 126 | 16,384 | 128 | 8 |

### 데이터 스케일링의 위력

LLaMA 3의 가장 중요한 혁신은 아키텍처가 아니라 **데이터 규모**에 있다. 15T 토큰은 Chinchilla 최적 비율($D \approx 20N$)을 크게 초과하는 의도적 과학습(overtraining)이다:

| 모델 | 파라미터 | Chinchilla 최적 | 실제 학습 | 과학습 비율 |
|------|---------|----------------|----------|----------|
| 8B | 8B | 160B | **15T** | **94x** |
| 70B | 70B | 1.4T | **15T** | **11x** |
| 405B | 405B | 8.1T | **15T** | **1.9x** |

이 전략은 추론 시 더 작은 모델을 사용할 수 있게 해, 추론 비용 최적화에 유리하다.

다음 그래프는 LLaMA 3 학습에 활용된 IsoFLOPs 스케일링 법칙 곡선이다. 각 컴퓨트 예산에서 최적의 학습 토큰 수를 결정하는 데 사용되었다.

![IsoFLOPs 스케일링 법칙 곡선 — 컴퓨트 예산별 학습 토큰 수와 검증 손실의 관계](figures/fig_3.png)
*Figure 3: IsoFLOPs 스케일링 법칙 — 각 곡선은 고정된 컴퓨트 예산(6e18~1e22 FLOPs)에서 학습 토큰 수에 따른 검증 손실을 보여준다. 곡선의 최소점(분홍 다이아몬드)이 해당 컴퓨트에서의 최적 토큰 수이다. (Source: LLaMA 3 논문)*

## 핵심 혁신

### 1. 405B: 오픈소스 최초의 Frontier급 모델

405B는 MMLU 88.6%, HumanEval 61.0%를 달성하며 GPT-4(초기)에 근접했다. 오픈소스 모델이 독점 모델의 성능 영역에 진입한 최초의 사례이다.

### 2. 데이터 품질 파이프라인

Meta는 15T 토큰 수집을 위해 정교한 데이터 품질 필터링 파이프라인을 구축했다. Heuristic 필터링, 중복 제거(deduplication), 분류 모델 기반 품질 점수 부여, PII 제거 등 다단계 파이프라인이 적용되었다.

### 3. 의도적 과학습 전략

Chinchilla 법칙을 의도적으로 초과하여 학습함으로써, 8B 같은 소형 모델에서도 이전 세대 대형 모델에 필적하는 성능을 달성했다. 이는 배포 시 추론 비용을 절감하는 실용적 전략이다.

## 벤치마크/성능

| 벤치마크 | LLaMA 3-8B | LLaMA 2-70B | LLaMA 3-70B | LLaMA 3-405B | GPT-4 |
|---------|-----------|------------|------------|-------------|-------|
| **MMLU** | 68.4% | 68.9% | **82.0%** | **88.6%** | ~86% |
| **HumanEval** | 33.5% | 29.9% | **48.2%** | **61.0%** | ~67% |
| **GSM8K** | 79.6% | 56.8% | **93.0%** | **96.8%** | ~95% |
| **ARC-C** | 61.1% | 57.4% | **68.8%** | **71.2%** | - |
| **MATH** | 30.0% | - | **50.4%** | **73.8%** | ~68% |

8B 모델이 LLaMA 2-70B를 MMLU에서 비슷하게 따라잡고, GSM8K에서는 크게 능가한다.

아래 그래프는 LLaMA 3 8B가 유사 규모 경쟁 모델들과 비교했을 때 카테고리별 성능을 보여준다.

![LLaMA 3 8B vs LLaMA 2 7B, Mistral 7B, Gemma 7B 카테고리별 성능 비교](figures/fig_13_1.png)
*Figure 5: 사전 학습 벤치마크 성능 — LLaMA 3 8B(파란색)가 General, Knowledge, Math & Reasoning, Code 등 대부분 카테고리에서 LLaMA 2 7B를 크게 앞서며, Mistral 7B와 Gemma 7B와도 경쟁력 있는 성능을 보인다. (Source: LLaMA 3 논문)*

## 관련 모델 비교

| 특성 | LLaMA 2 | LLaMA 3 | Mistral 7B | GPT-4 |
|------|---------|---------|-----------|-------|
| **최대 모델** | 70B | **405B** | 7.3B | ~1.8T |
| **학습 토큰** | 2T | **15T** | 미공개 | 미공개 |
| **컨텍스트** | 4,096 | **128K** | 8,192 | 128K |
| **GQA** | 34B/70B만 | **전 모델** | 전 모델 | - |
| **어휘** | 32K | **128K** | 32K | ~100K |
| **오픈소스** | 예 | **예** | 예 | 아니오 |

## 학습 상세

- **데이터**: 15T 토큰 (영어 비중 감소, 코드·수학·다국어 비중 대폭 증가)
- **토크나이저**: BPE 128,256 vocab (tiktoken 기반)
- **옵티마이저**: AdamW, lr cosine decay
- **배치**: 8B: 4M 토큰, 405B: 16M 토큰
- **하드웨어**: 16,384개 H100 GPU (405B 기준)
- **정렬**: SFT + RLHF (DPO 포함) + Rejection Sampling

다음 그림은 LLaMA 3의 사후 학습(post-training) 접근법을 보여준다. Rejection Sampling, SFT, DPO를 조합한 정렬 파이프라인이다.

![LLaMA 3 사후 학습 파이프라인 — Rejection Sampling, SFT, DPO의 조합](figures/fig_8.png)
*Figure 4: LLaMA 3 Post-Training — 사전 학습된 모델에 Rejection Sampling, SFT, DPO를 순차적으로 적용하여 정렬을 수행한다. (Source: LLaMA 3 논문)*
- **멀티모달**: LLaMA 3.2에서 비전·음성 확장

## 실무 활용

### 1. 범용 기반 모델

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Meta-Llama-3-8B-Instruct")
```

### 2. 128K 컨텍스트 활용

장문 문서 분석, 다중 문서 RAG, 대규모 코드베이스 분석 등에 활용할 수 있다.

### 3. 8B 모델의 실용성

8B 모델은 4-bit 양자화 시 약 5GB 메모리로 소비자 GPU에서 실행 가능하며, 이전 세대 70B 수준의 성능을 제공한다.

## 한계 및 전망

### 한계

1. **Dense 구조의 비효율**: 405B 전체 파라미터가 활성화되어 추론 비용이 높다.
2. **커스텀 라이선스**: Apache 2.0이 아닌 Meta 커스텀 라이선스로, 7억 MAU 이상 서비스에 제한이 있다.
3. **멀티모달 한계**: 기본 모델은 텍스트 전용이며, LLaMA 3.2에서야 멀티모달 확장이 이루어졌다.

### 전망

LLaMA 3는 오픈소스 LLM이 독점 모델의 성능 영역에 진입한 이정표이다. 405B의 Dense 구조 비효율은 LLaMA 4에서 MoE로 전환하여 해결되었으며, 15T 토큰 데이터 스케일링 전략은 이후 Qwen, DeepSeek 등 경쟁 모델들의 데이터 투자를 촉진했다.

---

**참고 논문**: [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783)

## 관련 문서

- [[llama-2|Llama 2: Open Foundation and Fine-Tuned Chat Models]] — 발전 기반
- [[llama-4|LLaMA 4 (Scout / Maverick / Behemoth)]] — 후속 모델
