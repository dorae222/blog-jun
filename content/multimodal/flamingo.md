---
title: "Flamingo: 소수샷 시각-언어 모델의 선구자"
slug: flamingo
category: multimodal
tags: ["DeepMind", "Few-Shot", "Few-Shot VLM", "Flamingo", "Gated Cross-Attention", "Interleaved Multimodal", "Perceiver Resampler", "VLM"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.608173+00:00"
architecture_entry: flamingo
---

# Flamingo: 소수샷 시각-언어 모델의 선구자

## 개요

Flamingo는 2022년 4월 DeepMind가 발표한 소수샷(few-shot) 시각-언어 모델(VLM)이다. 80B 파라미터 규모의 이 모델은 고정된 대규모 언어 모델(Chinchilla 70B)과 비전 인코더(NFNet-F6)를 **Perceiver Resampler**로 연결하고, **Gated Cross-Attention** 레이어를 LLM에 삽입하는 혁신적 구조를 제안했다.

Flamingo의 가장 중요한 기여는 **인터리브(interleaved) 이미지-텍스트 처리**이다. GPT-3이 텍스트 프롬프트에 예제를 제공하듯, Flamingo에 이미지-텍스트 쌍 예제를 제공하면 새로운 시각 태스크를 파인튜닝 없이 수행할 수 있다. 16개 멀티모달 벤치마크 중 6개에서 **32샷만으로 파인튜닝 모델을 능가**하는 놀라운 성과를 달성했으며, 이 연구는 LLaVA, BLIP-2 등 모든 후속 VLM의 이론적 토대가 되었다.

논문: [Flamingo: a Visual Language Model for Few-Shot Learning](https://arxiv.org/abs/2204.14198)

## 아키텍처 상세

### 전체 구조

Flamingo는 세 가지 핵심 컴포넌트로 구성된다:

1. **비전 인코더(Frozen)**: NFNet-F6 기반 (CLIP 방식으로 사전학습, ~400M params)
2. **Perceiver Resampler(Trainable)**: 시각 특징을 고정 크기 64개 토큰으로 압축
3. **LLM + Gated Cross-Attention(Partially Trainable)**: Chinchilla 70B

### Perceiver Resampler

Perceiver Resampler는 임의 크기의 이미지/비디오 특징을 **고정된 64개의 시각 토큰**으로 압축한다:

$$\text{Visual Tokens} = \text{PerceiverResampler}(\text{ViT\_features}) \in \mathbb{R}^{64 \times d}$$

64개의 학습 가능한 잠재 쿼리(latent query)가 교차 어텐션을 통해 비전 인코더 출력에서 필요한 정보를 추출한다. 이미지와 비디오 모두 동일한 차원의 고정 크기 토큰 시퀀스로 변환되므로, 모델이 다양한 시각 입력을 유연하게 처리할 수 있다. 이 설계는 이후 BLIP-2의 Q-Former에 직접적인 영감을 주었다.

### Gated Cross-Attention

LLM의 기존 셀프 어텐션 레이어 사이에 새로운 교차 어텐션 레이어를 삽입한다:

$$y = x + \alpha_{\text{xattn}} \cdot \tanh(\beta) \cdot \text{CrossAttn}(x, \text{visual\_tokens})$$
$$\text{output} = \text{FFN}(y)$$

여기서 $\alpha_{\text{xattn}}$은 **학습 가능한 게이팅 스칼라**로, **0으로 초기화**된다. 이를 통해:
- **학습 초기**: 게이팅 값 ≈ 0이므로 LLM의 원래 행동을 완벽히 보존
- **학습 진행**: 게이팅 값이 점진적으로 증가하며 시각 정보를 반영
- **결과**: LLM의 언어 능력을 손상시키지 않으면서 멀티모달 능력을 안정적으로 추가

모든 Gated Cross-Attention 레이어가 아닌, LLM 레이어 중 일부에만 삽입된다 (4개 레이어마다 1개).

### 인터리브 멀티모달 처리

```
[Image1] This is a photo of a golden retriever.
[Image2] This is a photo of a tabby cat.
[Image3] This is a photo of
```

이미지와 텍스트가 임의 순서로 인터리브된 시퀀스를 처리할 수 있어, ICL(In-Context Learning) 방식의 소수샷 학습이 자연스럽게 구현된다. 이는 이후 GPT-4V, Gemini 등 모든 멀티모달 대화 시스템의 기본 능력이 되었다.

| 구성 요소 | 사양 |
|-----------|------|
| LLM | Chinchilla 70B (Frozen) |
| 비전 인코더 | NFNet-F6 (Frozen) |
| Perceiver 쿼리 수 | 64 |
| 히든 차원 | 8192 |
| 레이어 수 | 80 |
| 어텐션 헤드 | 64 |
| 학습 파라미터 | ~10B (Perceiver + Gated XAttn) |

## 핵심 혁신

### 1. Perceiver Resampler

가변 크기의 시각 입력을 고정 크기(64개 토큰)로 압축하여 LLM의 컨텍스트 윈도우를 효율적으로 사용한다. 이미지든 비디오 프레임이든 동일한 64개 토큰으로 표현되므로, 다양한 시각 입력을 유연하게 처리할 수 있다.

### 2. Gated Cross-Attention with Zero Init

0으로 초기화된 게이팅으로 LLM의 사전학습된 능력을 보존하면서 멀티모달 능력을 추가하는 우아한 방법이다. 이 테크닉은 이후 LoRA의 zero-init, ControlNet의 zero convolution 등 다양한 연구에서 응용되었다.

### 3. 인터리브 멀티모달 소수샷 학습

이미지와 텍스트가 자유롭게 섞인 시퀀스를 처리하는 최초의 대규모 모델로, "프롬프트에 예제를 제공하면 새 태스크를 수행"하는 GPT-3의 ICL 패러다임을 멀티모달로 확장했다.

## 벤치마크/성능

| 벤치마크 | Flamingo-80B (32-shot) | 이전 SOTA (fine-tuned) | 비고 |
|----------|----------------------|----------------------|------|
| COCO Caption | 138.1 CIDEr | 131.1 (CoCa) | 파인튜닝 모델 능가 |
| VQAv2 | 67.6% | 80.0% (파인튜닝) | 32샷 기준 |
| OK-VQA | 57.8% | 54.4% (파인튜닝) | **파인튜닝 모델 능가** |
| TextVQA | 54.1% | 60.2% (파인튜닝) | 32샷 기준 |
| Hateful Memes | 70.7% | 64.7% | **파인튜닝 모델 능가** |

16개 벤치마크 중 6개에서 32샷만으로 파인튜닝 SOTA를 능가하였다. 나머지 벤치마크에서도 격차가 크지 않아, 소수샷 멀티모달 학습의 강력함을 입증하였다.

## 관련 모델 비교

| 특성 | Flamingo | LLaVA | BLIP-2 | GPT-4V |
|------|----------|-------|--------|--------|
| 발표 연도 | 2022 | 2023 | 2023 | 2023 |
| 소수샷 능력 | 우수 | 제한적 | 보통 | 우수 |
| 브릿지 방식 | Perceiver + XAttn | Linear/MLP | Q-Former | 네이티브 |
| LLM 학습 | Frozen | Full FT | Frozen | End-to-End |
| 오픈소스 | 비공개 | 공개 | 공개 | 비공개 |
| 비디오 지원 | 지원 | 미지원 (v1) | 미지원 | 지원 |

## 학습 상세

학습 데이터 구성:

| 데이터셋 | 유형 | 규모 |
|----------|------|------|
| M3W (MultiModal MassiveWeb) | 인터리브 이미지-텍스트 | 43M 웹페이지 |
| ALIGN | 이미지-텍스트 쌍 | 1.8B |
| LTIP | 긴 텍스트 이미지 쌍 | 312M |
| VTP | 비디오-텍스트 쌍 | 27M |

옵티마이저: AdaFactor (누적 그래디언트)
학습 인프라: TPU v4 Pod
학습 파라미터: ~10B (전체 80B 중 Perceiver + Gated XAttn만)

## 실무 활용

Flamingo 자체는 비공개 모델이지만, 충실한 오픈소스 재구현이 다수 존재한다:

```python
# OpenFlamingo (LAION 커뮤니티 재구현)
from open_flamingo import create_model_and_transforms

model, image_processor, tokenizer = create_model_and_transforms(
    clip_vision_encoder_path="ViT-L-14",
    clip_vision_encoder_pretrained="openai",
    lang_encoder_path="anas-awadalla/mpt-7b",
    tokenizer_path="anas-awadalla/mpt-7b",
)

# Few-shot VQA
demo_images = [Image.open(f"demo_{i}.jpg") for i in range(3)]
demo_texts = ["Q: What is this? A: A dog.", "Q: What is this? A: A cat."]
query_image = Image.open("query.jpg")
query_text = "Q: What is this? A:"
# ... generate response
```

주요 오픈소스 파생 모델:
- **OpenFlamingo** (LAION): 직접적 아키텍처 재구현
- **IDEFICS/IDEFICS2** (HuggingFace): Flamingo 아키텍처 기반 오픈 모델
- **Otter** (NTU): OpenFlamingo 기반 인스트럭션 튜닝

## 한계 및 전망

### 한계

1. **비공개 모델**: 가중치 미공개로 직접 사용 불가
2. **대규모 컴퓨팅**: 80B 파라미터로 추론 비용이 매우 높음
3. **이미지 생성 불가**: 이미지 이해에 특화, 생성 능력 부재
4. **시각 해상도**: NFNet 인코더의 해상도 제한으로 OCR 등 고해상도 태스크에 약함

### 전망

Flamingo는 "고정된 LLM에 멀티모달 능력을 추가"하는 패러다임을 정립한 선구적 연구이다. Perceiver Resampler → Q-Former(BLIP-2) → MLP Projector(LLaVA)로의 브릿지 모듈 진화, Gated Cross-Attention → 다양한 게이팅 기법으로의 발전, 인터리브 멀티모달 처리의 범용화 등 현대 VLM의 거의 모든 기본 개념이 Flamingo에서 출발했다. 2024-2025년의 GPT-4o, Gemini 등이 네이티브 멀티모달로 진화하면서 Flamingo 스타일의 "모듈 추가" 방식은 줄어들었지만, 효율적 파인튜닝과 모듈형 설계라는 핵심 철학은 여전히 유효하다.

## 관련 문서

- [[clip|CLIP]] — 영감
