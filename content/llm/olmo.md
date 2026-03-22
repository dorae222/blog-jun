---
title: "OLMo: Accelerating the Science of Language Models"
slug: olmo
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.381083+00:00"
architecture_entry: olmo
---

## 논문 개요

OLMo(Open Language Model)는 Allen Institute for AI(AI2)가 2024년 ACL에서 발표한 대규모 언어 모델로, 그 이름처럼 "진정한 의미의 오픈" 모델이다. 기존의 오픈소스 LLM들이 모델 가중치만 공개하는 데 그쳤다면, OLMo는 **학습 코드, 사전학습 데이터, 모든 중간 체크포인트, 학습 로그, 평가 프레임워크**까지 모두 공개한다.

이 논문의 핵심 메시지는 "언어 모델의 과학을 가속화하자"는 것이다. LLM 연구가 소수의 기업에 집중되고 재현 불가능한 실험들이 난무하는 상황에서, OLMo는 완전한 투명성을 통해 모든 연구자가 LLM을 독립적으로 연구하고 발전시킬 수 있는 기반을 제공하고자 한다.

OLMo는 7B와 1B 두 가지 크기로 제공되며, 총 2T 토큰의 Dolma 데이터셋으로 학습되었다.

---

## 핵심 기여

### 1. 완전 오픈 생태계

OLMo의 가장 중요한 기여는 LLM 연구에 필요한 모든 요소를 완전히 공개한다는 점이다:

| 공개 요소 | 내용 | URL |
|---|---|---|
| 모델 가중치 | 7B, 1B (Apache 2.0) | HuggingFace |
| 학습 코드 | PyTorch + FSDP | GitHub |
| 사전학습 데이터 | Dolma 3T 토큰 | HuggingFace |
| 중간 체크포인트 | 2500+ 체크포인트 | S3 |
| 학습 로그 | WandB 학습 곡선 | WandB |
| 평가 프레임워크 | Catwalk, Paloma | GitHub |

이를 통해 연구자들은 다음이 가능해진다:
- 학습 과정의 재현 및 검증
- 특정 학습 단계의 모델 분석
- 데이터-성능 관계 연구
- 새로운 파인튜닝 방법 개발 및 공정 비교

### 2. Dolma 데이터셋

**Dolma**는 OLMo 학습을 위해 구축된 오픈소스 사전학습 데이터셋으로, 총 3T 토큰 규모다:

| 소스 | 토큰 수 | 비중 |
|---|---|---|
| Common Crawl | ~2.1T | 70% |
| C4 | ~0.2T | 7% |
| GitHub 코드 | ~0.2T | 7% |
| 학술 논문 | ~0.1T | 3% |
| Wikipedia | ~0.04T | 1% |
| OpenSubtitles | ~0.02T | 1% |
| 기타 | ~0.3T | 10% |

Dolma도 완전히 오픈소스로 공개되어, LLM 사전학습 데이터 연구에 귀중한 자원이 되었다.

### 3. 재현 가능한 평가 프레임워크

**Catwalk**: 다양한 다운스트림 태스크 평가를 위한 통합 프레임워크
**Paloma**: 언어 모델 성능을 표준화된 방식으로 측정하는 perplexity 벤치마크

---

## 방법론 상세

### 아키텍처

OLMo는 표준 decoder-only Transformer를 기반으로 하며 다음과 같은 설계 선택을 포함한다:

| 구성 요소 | OLMo-7B | OLMo-1B |
|---|---|---|
| 레이어 수 | 32 | 16 |
| 히든 차원 | 4096 | 2048 |
| FFN 차원 | 11008 | 8192 |
| 어텐션 헤드 | 32 | 16 |
| 컨텍스트 길이 | 2048 | 2048 |
| 어휘 크기 | 50,280 | 50,280 |
| 파라미터 | 6.89B | 1.18B |

**SwiGLU 피드포워드 네트워크**

OLMo는 SwiGLU(Swish-Gated Linear Unit)를 피드포워드 레이어에 채택한다:

$$\text{SwiGLU}(x) = \text{Swish}(xW_1 + b_1) \odot (xW_2 + b_2)$$

$$\text{Swish}(x) = x \cdot \sigma(x) = \frac{x}{1 + e^{-x}}$$

SwiGLU는 GLU의 변형으로, 게이팅 메커니즘이 불필요한 정보의 흐름을 제어하여 더 효율적인 표현 학습을 가능하게 한다. 동일 FLOPs 예산에서 표준 MLP 대비 성능이 우수함이 경험적으로 입증되어 있다.

**RoPE (Rotary Position Embedding)**

절대 Positional Embedding이나 ALiBi 대신 RoPE를 채택한다. RoPE의 핵심 수학은 복소수 공간에서의 회전으로 이해할 수 있다:

$$\mathbf{q}_m = \sum_{j=0}^{d/2-1} (q_{2j} + iq_{2j+1}) e^{im\theta_j} \mathbf{e}_{2j}$$

$$\text{Re}(\mathbf{q}_m^* \cdot \mathbf{k}_n) = \text{Re}\left(\sum_j (q_{2j} + iq_{2j+1})^*(k_{2j} + ik_{2j+1}) e^{i(n-m)\theta_j}\right)$$

이 수식은 어텐션 점수가 자연스럽게 상대 위치 $n - m$에 의존함을 보여준다.

각 주파수 성분은:
$$\theta_j = 10000^{-2j/d}, \quad j = 0, 1, \ldots, d/2 - 1$$

**No Biases**

OLMo는 attention projection과 feed-forward 레이어에서 편향 항(bias)을 사용하지 않는다. 이는 학습 안정성을 높이고 파라미터 효율을 개선하는 것으로 알려져 있다.

**Non-parametric Layer Norm**

어파인 변환(학습 가능한 스케일/시프트 파라미터)이 없는 단순화된 Layer Normalization을 사용한다:

$$\text{LayerNorm}(x) = \frac{x - \mu}{\sigma + \epsilon}$$

(RMSNorm과 달리 평균도 빼지만 학습 파라미터 없음)

### 학습 인프라

**하드웨어**: AMD MI250X GPU 클러스터 (LUMI 슈퍼컴퓨터), 총 448 GPU (A100 64GB 동급)

**분산 학습**: PyTorch FSDP(Fully Sharded Data Parallel) 사용

```python
# FSDP 설정 (개념적)
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp.wrap import transformer_auto_wrap_policy

model = FSDP(
    model,
    auto_wrap_policy=transformer_auto_wrap_policy,
    sharding_strategy=ShardingStrategy.FULL_SHARD,
    mixed_precision=MixedPrecision(
        param_dtype=torch.bfloat16,
        reduce_dtype=torch.float32,
        buffer_dtype=torch.bfloat16,
    ),
    device_id=local_rank,
)
```

**학습 안정화 기술:**
- Gradient clipping (max norm = 1.0)
- Z-loss: 출력 로짓의 분산 제어
  $$\mathcal{L}_{\text{z-loss}} = \alpha \cdot \mathbb{E}\left[\log^2 Z\right], \quad Z = \sum_i e^{z_i}$$
- 학습률 스케줄: 워밍업 후 코사인 감소

### 학습 설정

| 하이퍼파라미터 | OLMo-7B |
|---|---|
| 총 토큰 | 2.46T |
| 배치 크기 | 2048 × 2048 토큰 |
| 최대 학습률 | 3e-4 |
| 최소 학습률 | 3e-5 |
| 워밍업 | 5000 스텝 |
| 옵티마이저 | AdamW |
| β₁, β₂ | 0.9, 0.95 |
| 가중치 감쇠 | 0.1 |

---

## 실험 결과

### 종합 벤치마크

| 벤치마크 | OLMo-7B | Llama-2-7B | Falcon-7B | MPT-7B |
|---|---|---|---|---|
| ARC-Easy | **76.4** | 74.5 | 75.9 | 73.9 |
| ARC-Challenge | **44.2** | 40.0 | 39.5 | 39.9 |
| HellaSwag | **76.4** | 76.0 | 78.2 | 77.5 |
| PIQA | **79.4** | 79.1 | 80.3 | 80.6 |
| WinoGrande | **68.2** | 68.9 | 71.0 | 68.3 |

OLMo-7B는 동일 규모의 다른 오픈소스 모델들과 경쟁력 있는 성능을 보인다.

### Paloma 벤치마크

Paloma는 다양한 도메인과 언어 레지스터에서 perplexity를 측정하는 표준화된 벤치마크다:

$$\text{Perplexity} = \exp\left(-\frac{1}{N}\sum_{i=1}^N \log P(w_i | w_{<i})\right)$$

OLMo는 Paloma의 각 카테고리에서 Llama 2와 유사하거나 더 나은 perplexity를 달성한다.

### 학습 곡선 분석

공개된 WandB 로그를 통해 학습 과정을 상세히 분석할 수 있다:

```
학습 손실 추이 (개략적):
- 초기 (0-5B 토큰): 빠른 하강
- 중반 (5B-1T 토큰): 안정적 하강
- 후반 (1T-2.46T 토큰): 완만한 하강

관찰된 특이사항:
- 약 150B 토큰 시점에서 일시적 스파이크 발생
  → 데이터 품질 문제로 확인 및 수정
```

이처럼 학습 로그의 공개는 실험 재현성뿐 아니라 학습 안정성 연구에도 귀중한 자료가 된다.

---

## 의의 및 한계

### 의의

**완전 오픈의 표준 정립**: OLMo는 LLM 분야에서 진정한 오픈소스가 무엇인지 기준을 제시했다. 가중치만 공개하는 "오픈워싱(openwashing)"과 달리, 재현 가능한 과학을 위한 모든 요소를 공개했다.

**LLM 과학의 민주화**: 소수 빅테크 기업이 독점하던 LLM 연구를 모든 연구자에게 개방함으로써 학계와 소규모 기관의 참여를 가능하게 했다.

**데이터-모델 공동 연구**: 학습 데이터(Dolma)와 모델(OLMo)이 함께 공개됨으로써 데이터 선택이 모델 성능에 미치는 영향을 직접 연구할 수 있게 되었다.

**중간 체크포인트의 가치**: 2500개 이상의 중간 체크포인트는 지식 획득 과정, 능력 발현 시점, 잊어버림(forgetting) 현상 등을 연구하는 데 활용된다.

**공정한 비교 기반 마련**: 완전히 공개된 모델과 데이터를 기반으로 새로운 방법론을 공정하게 비교할 수 있는 환경이 조성되었다.

### 한계

**성능의 한계**: 완전 오픈에 집중하다 보니 동시대 최고 성능 모델(Llama 2 70B, Mixtral 등)에 비해 성능이 다소 낮다.

**컨텍스트 길이**: 기본 컨텍스트 길이가 2048 토큰으로 짧아 장문 처리 능력이 제한적이다.

**다국어 능력 부족**: 영어 중심 데이터로 학습되어 다국어 태스크에서 성능이 낮다.

**계산 자원 요구**: 완전한 재현을 위해서는 여전히 상당한 GPU 클러스터가 필요하다.

**이후 발전**: OLMo의 철학을 이어받아 OLMo 2(2024), OLMo-2-13B 등이 발표되었으며, AI2는 지속적으로 완전 오픈 LLM 생태계를 확장하고 있다. 특히 OLMo 2는 성능과 투명성 모두에서 크게 향상되었다.

OLMo는 단순히 하나의 LLM이 아니라, 오픈소스 AI 연구가 나아가야 할 방향을 제시한 중요한 이정표다.