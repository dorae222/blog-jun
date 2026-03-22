---
title: "DeepSeek-VL2: 멀티모달 AI 모델"
slug: "deepseek-vl2"
category: multimodal
tags: ["DeepSeek", "DeepSeek-VL2", "Dynamic Tiling", "MoE VLM", "Parameter Efficiency"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.222172+00:00"
architecture_entry: "deepseek-vl2"
---

# DeepSeek-VL2: MoE 기반 효율적 멀티모달 모델

## 개요

DeepSeek-VL2는 2024년 12월 DeepSeek이 발표한 MoE(Mixture of Experts) 기반 멀티모달 모델이다. **동적 타일링(Dynamic Tiling)** 방식의 고해상도 이미지 처리와 **DeepSeekMoE 아키텍처**를 결합하여, 전체 파라미터 대비 훨씬 적은 활성화 파라미터로 경쟁력 있는 성능을 달성한다. 3B(소형), 16B(중형), 27B(대형) 세 가지 크기로 제공되며, OCR, 문서 이해, 시각적 추론, 수학 문제 해결 등 다양한 멀티모달 태스크에서 오픈소스 SOTA 수준을 기록하였다.

DeepSeek-VL2의 핵심 가치는 **파라미터 효율성**이다. 27B 모델의 경우 전체 27B 파라미터 중 추론 시 약 4.5B만 활성화되어, 유사 크기의 밀집(dense) 모델 대비 3~6배 적은 연산량으로 동등하거나 더 높은 성능을 달성한다.

논문: [DeepSeek-VL2: Mixture-of-Experts Vision-Language Models for Advanced Multimodal Understanding](https://arxiv.org/abs/2412.10302)

## 아키텍처 상세

### 전체 구조

DeepSeek-VL2는 세 가지 핵심 컴포넌트로 구성된다:

1. **비전 인코더**: SigLIP-L (400M params) — 이미지 패치 특징 추출
2. **동적 타일링 + MLP 프로젝터**: 고해상도 이미지를 448×448 타일로 분할 후 LLM 공간에 매핑
3. **DeepSeekMoE LLM**: MoE 기반 언어 모델, MLA(Multi-head Latent Attention) 적용

### 동적 타일링(Dynamic Tiling)

고해상도 이미지를 효율적으로 처리하기 위해 이미지를 내용과 해상도에 따라 최적 개수의 448×448 타일로 분할한다:

$$I \in \mathbb{R}^{H \times W \times 3} \rightarrow \{T_1, T_2, ..., T_n, T_{\text{global}}\}$$

각 타일 $T_i$는 SigLIP으로 개별 인코딩되고, 전체 이미지의 축소 버전인 글로벌 타일 $T_{\text{global}}$도 함께 제공한다. 이 방식은:
- 저해상도 이미지: 1~2개 타일 → 적은 토큰
- 고해상도 이미지: 최대 12개 타일 → 많은 토큰 (세밀한 정보 보존)

이미지 본래의 종횡비를 유지하면서 해상도에 비례한 토큰 수를 사용하므로, 고해상도 OCR이나 문서 이해에서 탁월한 성능을 보인다.

### DeepSeekMoE 아키텍처

각 트랜스포머 레이어의 FFN이 MoE 블록으로 대체된다:

$$\text{MoE}(x) = \sum_{i=1}^{K} g_i(x) \cdot E_i(x) + E_{\text{shared}}(x)$$

여기서 $g_i(x)$는 라우터가 결정하는 게이팅 가중치, $E_i$는 개별 전문가, $E_{\text{shared}}$는 공유 전문가이다.

| 항목 | DeepSeek-VL2-3B | DeepSeek-VL2-16B | DeepSeek-VL2-27B |
|------|----------------|-----------------|-----------------|
| 전체 파라미터 | 3B | 16B | 27B |
| 활성 파라미터 | ~1B | ~2.8B | ~4.5B |
| 전문가 수 | 16 | 64 | 64 |
| 활성 전문가 | 4 | 6 | 6 |
| 공유 전문가 | 1 | 2 | 2 |
| 레이어 수 | 28 | 60 | 60 |

### MLA(Multi-head Latent Attention)

KV 캐시를 압축하여 추론 메모리를 절감하는 기법이다:

$$c_{kv} = W_{DKV} \cdot x, \quad k = W_{UK} \cdot c_{kv}, \quad v = W_{UV} \cdot c_{kv}$$

저차원 잠재 벡터 $c_{kv}$만 캐싱하면 되므로, 기존 MHA 대비 KV 캐시 크기가 크게 줄어든다.

## 핵심 혁신

### 1. MoE + VLM 결합

VLM에 MoE를 적용한 선구적 연구로, 소수의 전문가만 활성화하여 추론 효율성을 극대화하면서도 전체 모델 크기의 이점(다양한 지식 저장)을 유지한다.

### 2. 로컬-글로벌 시각 특징 결합

동적 타일링의 로컬 타일과 글로벌 타일을 동시에 제공하여, 세밀한 디테일(OCR 문자, 수식 기호)과 전체 맥락(레이아웃, 구조)을 모두 파악한다.

### 3. 세밀한 전문가 분리(Fine-grained Expert Segmentation)

DeepSeekMoE의 핵심으로, 기존 MoE 대비 전문가를 더 작고 많은 수로 분리하여 조합의 유연성을 높이고 라우팅 정확도를 개선한다.

## 벤치마크/성능

| 벤치마크 | VL2-27B | Qwen2-VL-72B | InternVL2-76B | GPT-4V |
|----------|---------|-------------|--------------|--------|
| OCRBench | **83.4** | 85.5 | 83.9 | 78.0 |
| DocVQA | **92.2** | 93.1 | 91.6 | 87.2 |
| MathVista | **68.2** | 70.5 | 65.5 | 58.1 |
| MMMU | **49.3** | 54.1 | 51.2 | 56.8 |
| TextVQA | **84.1** | 84.3 | 82.0 | 78.0 |

활성 파라미터 ~4.5B로 72B급 밀집 모델과 경쟁하는 성능을 달성한다.

## 관련 모델 비교

| 특성 | DeepSeek-VL2 | Qwen2-VL | InternVL 2 | LLaVA-OV |
|------|-------------|---------|-----------|----------|
| LLM 타입 | MoE | Dense | Dense | Dense |
| 활성 파라미터 | 4.5B (27B 중) | 72B | 76B | 72B |
| 이미지 처리 | 동적 타일링 | 동적 해상도 | 동적 해상도 | AnyRes |
| KV 캐시 | MLA 압축 | GQA | GQA | MHA |
| 추론 효율 | 매우 높음 | 보통 | 보통 | 보통 |

## 학습 상세

2단계 학습을 수행한다:

**Stage 1: 비전-언어 정렬**
- MLP 프로젝터를 학습하여 SigLIP 출력과 LLM 입력 공간 정렬
- LLM과 비전 인코더는 고정

**Stage 2: 통합 파인튜닝**
- 전체 모델(비전 인코더 + 프로젝터 + LLM) 통합 파인튜닝
- 웹 이미지-텍스트, OCR, 수학, 과학 도메인 데이터 혼합

MoE 학습 시 로드 밸런싱 손실로 전문가 활용 균등화:
$$\mathcal{L}_{\text{balance}} = N \sum_{i=1}^{N} f_i \cdot p_i$$

## 실무 활용

```python
from transformers import AutoModelForCausalLM, AutoProcessor
import torch

model = AutoModelForCausalLM.from_pretrained(
    "deepseek-ai/deepseek-vl2-small",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
).to("cuda")
processor = AutoProcessor.from_pretrained(
    "deepseek-ai/deepseek-vl2-small",
    trust_remote_code=True
)

# OCR + 문서 이해
image = processor.image_processor("document.pdf")
inputs = processor(
    text="이 문서의 핵심 내용을 요약해주세요.",
    images=image, return_tensors="pt"
).to("cuda")
output = model.generate(**inputs, max_new_tokens=512)
```

## 한계 및 전망

### 한계

1. **MoE 메모리**: 전체 파라미터가 메모리에 로드되어야 하므로, 활성 파라미터는 적지만 GPU 메모리 요구량은 밀집 모델과 유사하다
2. **라우팅 불균형**: 특정 전문가에 토큰이 집중되는 문제가 발생할 수 있다
3. **커뮤니티 생태계**: Qwen2-VL, LLaVA 대비 서드파티 도구 및 파인튜닝 생태계가 상대적으로 작다

### 전망

DeepSeek-VL2는 MoE와 VLM의 결합이 파라미터 효율성 측면에서 매우 유망함을 입증하였다. 이후 Janus-Pro에서 이해와 생성을 통합하는 방향으로 발전하였으며, DeepSeek-V3/R1의 MoE 기술이 VLM으로 확산되면서 향후 더욱 효율적인 멀티모달 모델이 등장할 것으로 기대된다.

## 관련 문서

- [[deepseek-v2|DeepSeek-V2: A Strong, Economical, and Efficient Mixture-of-Experts Language Model]] — 발전 기반
- [[janus-pro|Janus-Pro]] — 후속 모델
