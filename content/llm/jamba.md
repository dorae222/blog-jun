---
title: "Jamba: A Hybrid Transformer-Mamba Language Model"
slug: jamba
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.424513+00:00"
architecture_entry: jamba
---

## 논문 개요

AI21 Labs(2024)가 발표한 **Jamba**는 Transformer, Mamba SSM, Mixture-of-Experts(MoE)라는 세 가지 현대 언어 모델 기술을 하나의 아키텍처에 결합한 하이브리드 언어 모델입니다.

기존 언어 모델의 두 가지 주요 접근법:
- **Transformer**: 강력한 In-Context Learning, 유연한 어텐션 메커니즘, 하지만 KV 캐시로 인한 메모리 폭발과 $O(N^2)$ 복잡도
- **Mamba (순수 SSM)**: 선형 시간 복잡도, 고정 크기 상태로 메모리 효율적, 하지만 긴 시퀀스 재현(recall) 능력 한계

Jamba는 두 접근법을 혼합하여 각각의 장점을 활용하고 단점을 보완합니다. 총 52B 파라미터 중 활성화되는 파라미터는 12B에 불과하여, 작은 메모리와 빠른 추론 속도를 유지합니다.

---

## 핵심 기여

1. **3-way 하이브리드 아키텍처**: Transformer + Mamba + MoE의 결합 방식 정립
2. **256K 컨텍스트 지원**: 단일 A100 80GB GPU에서 처리 가능한 최장 컨텍스트
3. **KV 캐시 대폭 절감**: 동일 규모 순수 Transformer 대비 약 8배 감소
4. **오픈소스 대형 하이브리드 모델**: 7B 이상 규모의 Mamba 기반 모델 중 최초 공개

---

## 방법론 상세

### 아키텍처 설계 원칙

Jamba의 핵심 설계 결정은 **Transformer와 Mamba 레이어의 비율**입니다. 논문에서는 다양한 비율을 실험하여 최적 구성을 도출했습니다.

전체 아키텍처는 여러 **Jamba 블록**의 스택으로 구성됩니다:

```
Jamba 블록 구조 (예: Transformer:Mamba = 1:3 비율)
┌─────────────────────────────────────┐
│  Mamba 레이어                        │
│  Mamba 레이어                        │
│  Mamba 레이어                        │
│  Transformer (Attention) 레이어      │
└─────────────────────────────────────┘
        × 여러 블록 반복
```

### Transformer 레이어

표준 Multi-Head Attention(MHA) 사용:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

GQA(Grouped Query Attention)를 적용하여 KV 헤드 수를 줄여 KV 캐시 크기를 추가로 절감합니다:
- Q 헤드 수: 32
- KV 헤드 수: 8 (GQA 적용)

### Mamba 레이어

선택적 상태 공간 모델(S6):  

$$h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t, \quad y_t = C_t h_t$$

파라미터가 입력에 의존:

$$\bar{B}_t, C_t, \Delta_t = f(x_t)$$

Jamba에서 Mamba 레이어는:
- 상태 크기(state size): $d_{\text{state}} = 16$
- 확장 비율(expansion factor): 2
- 학습 불안정을 줄이기 위한 RMSNorm 적용

### Mixture-of-Experts (MoE)

MoE는 각 토큰에 대해 전체 전문가(expert) 중 일부만 활성화합니다. Jamba에서 MoE는 FFN(Feed-Forward Network) 레이어에 적용됩니다:

$$\text{MoE}(x) = \sum_{i=1}^K G_i(x) \cdot E_i(x)$$

$$G(x) = \text{Top-K}(\text{softmax}(W_g x))$$

- 전체 전문가 수: 16
- 활성화 전문가 수: 2 (Top-2 라우팅)
- MoE 레이어는 일부 Transformer/Mamba 레이어에만 적용

**파라미터 분포:**

| 구성 요소 | 총 파라미터 | 활성 파라미터 |
|---------|-----------|-------------|
| 임베딩 | - | - |
| Transformer 레이어 (MoE) | 다수 | 1/8 |
| Mamba 레이어 | - | 100% |
| **전체** | **52B** | **~12B** |

### 레이어 구성 상세

```
Jamba 전체 구조:
- 총 레이어: 32개
- Transformer 레이어: 7개 (약 1:3 비율)
- Mamba 레이어: 25개
- MoE 레이어: 일부 Transformer + 일부 Mamba
- 히든 차원: 4096
- Attention 헤드: 32 (Q), 8 (KV)
- 중간 차원: 14336
```

### KV 캐시 효율 분석

시퀀스 길이 $L$에서 KV 캐시 메모리:

$$M_{\text{KV}} = 2 \times L \times d_{\text{model}} \times n_{\text{KV\_heads}} \times n_{\text{layers}} \times \text{dtype\_size}$$

Mamba 레이어는 고정 크기 상태 $h \in \mathbb{R}^{D \times N}$만 유지하므로 시퀀스 길이와 무관:

$$M_{\text{Mamba}} = D \times N \times \text{dtype\_size} \quad (\text{L에 독립})$$

**256K 시퀀스에서의 비교 (bf16 기준):**

| 모델 | KV/상태 캐시 크기 |
|------|----------------|
| Llama-2-7B (순수 Transformer, 256K) | ~128 GB |
| Jamba-7B (하이브리드, 256K) | ~16 GB |
| **절감 비율** | **~8배** |

---

## 실험 결과

### 언어 모델링 벤치마크

| 모델 | MMLU | HellaSwag | WinoGrande | ARC-C | Avg |
|------|------|-----------|-----------|-------|-----|
| Llama-2-7B | 45.3 | 77.2 | 69.2 | 46.3 | 59.5 |
| Llama-2-13B | 54.8 | 80.7 | 72.8 | 49.4 | 64.4 |
| Mixtral-8×7B | **70.6** | **86.7** | **81.2** | **66.0** | **76.1** |
| **Jamba** | **67.4** | **87.1** | **78.5** | **64.4** | **74.4** |
| Mamba-2.8B | 25.8 | 66.2 | 63.6 | 29.6 | 46.3 |

Jamba(활성 12B)는 Mixtral-8×7B(활성 13B)와 경쟁적인 성능을 보이며, 순수 Mamba 모델보다 크게 앞섭니다.

### 긴 컨텍스트 처리 (SCROLLS 벤치마크)

| 모델 | 지원 컨텍스트 | SCROLLS 점수 |
|------|------------|-------------|
| Llama-2-7B | 4K | 17.4 |
| Mistral-7B | 32K | 23.1 |
| **Jamba** | **256K** | **24.2** |

256K 컨텍스트 지원으로 장문 문서 이해에서 우수한 성능을 보입니다.

### 처리량 (Throughput)

긴 시퀀스에서 Jamba의 추론 처리량 이점:

| 시퀀스 길이 | Jamba vs Llama-2-7B |
|-----------|--------------------|
| 16K | 1.5× 빠름 |
| 64K | 3.0× 빠름 |
| 128K | 5.2× 빠름 |

---

## 아키텍처 설계 실험

### Transformer:Mamba 비율의 영향

| 비율 (T:M) | Perplexity | KV 캐시 크기 |
|-----------|-----------|-------------|
| 1:1 | 8.23 | 중간 |
| 1:3 | **8.14** | 작음 |
| 1:7 | 8.31 | 매우 작음 |
| 0:1 (순수 Mamba) | 8.72 | 최소 |

1:3 비율이 성능과 효율의 최적 균형점임을 발견했습니다.

### MoE 적용 레이어의 영향

MoE를 Transformer 레이어에만, Mamba 레이어에만, 또는 모두에 적용했을 때:
- **모든 레이어에 MoE 적용** 시 최적 성능-효율 트레이드오프
- MoE 없이 Dense 모델만 사용 시 파라미터 효율 감소

---

## Jamba-1.5 (후속 모델)

AI21 Labs는 2024년 후반에 Jamba-1.5를 발표했습니다:

- **Jamba-1.5-Mini**: 12B 활성 파라미터
- **Jamba-1.5-Large**: 94B 총 파라미터, 52B 활성
- 지시 튜닝 버전 포함 (Jamba-1.5-Mini-Instruct)
- 256K 컨텍스트 유지, 개선된 품질

```
Jamba-1.5 개선 사항:
- 더 강력한 지시 튜닝 데이터
- 향상된 코드 및 수학 능력
- 다국어 지원 강화
- 함수 호출(function calling) 지원
```

---

## 의의 및 한계

### 의의

- **하이브리드 아키텍처의 실용성 입증**: 대규모 모델에서 Transformer+Mamba 혼합이 효과적임을 보여줌
- **극한의 컨텍스트 효율**: 256K 컨텍스트를 단일 GPU에서 처리, 실용적 장문 처리 가능
- **산업 수준의 오픈소스**: AI21 Labs의 상용 경험이 반영된 최초의 대규모 하이브리드 모델 공개
- **설계 가이드라인 제시**: T:M 비율, MoE 구성 등 하이브리드 모델 설계를 위한 실증적 지침

### 한계

- **복잡한 구현**: 세 가지 다른 구성 요소의 결합으로 구현 및 최적화 난이도 증가
- **재현 능력**: Mamba 레이어가 다수를 차지하여 정확한 긴 시퀀스 재현(exact recall)에 한계
- **학습 비용**: MoE + Mamba 혼합으로 인한 학습 불안정성 및 최적화 어려움
- **커뮤니티 생태계 부족**: Transformer 기반 모델에 비해 파인튜닝 툴, 양자화 등 지원 미비

### 성능-효율 트레이드오프 요약

$$\text{Efficiency Score} = \frac{\text{Performance}}{\text{KV Cache Memory} \times \text{Latency}}$$

| 모델 유형 | 성능 | KV 캐시 | 추론 속도 (긴 시퀀스) |
|---------|------|---------|--------------------|
| 순수 Transformer | 높음 | 매우 큼 | 느림 |
| 순수 Mamba | 중간 | 최소 | 매우 빠름 |
| **Jamba (하이브리드)** | **높음** | **작음** | **빠름** |

---

## 결론

Jamba는 Transformer의 강력한 표현 능력과 Mamba의 선형 시간 효율성을 결합함으로써, 두 접근법의 상호보완적 특성을 성공적으로 활용했습니다. 256K 컨텍스트를 단일 GPU에서 처리할 수 있다는 점은 RAG 없이 긴 문서를 직접 처리하는 응용에서 특히 가치 있습니다. Jamba의 성공은 순수 Transformer 이외의 아키텍처가 대규모 언어 모델에서 경쟁력 있는 대안이 될 수 있음을 보여주며, 이후 Zamba, RWKV-7 등 다양한 하이브리드 아키텍처 연구의 선도적 사례가 되었습니다.