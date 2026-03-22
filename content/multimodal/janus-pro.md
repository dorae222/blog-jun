---
title: "Janus-Pro: 멀티모달 AI 모델"
slug: "janus-pro"
category: multimodal
tags: ["Decoupled Vision Encoder", "DeepSeek", "Discrete Image Tokenization", "Janus-Pro", "Unified Understanding-Generation"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.185271+00:00"
architecture_entry: "janus-pro"
---

# Janus-Pro: 이해와 생성을 위한 디커플링 비전 인코더

## 개요

Janus-Pro는 2025년 1월 DeepSeek이 발표한 통합 멀티모달 이해 및 생성 모델이다. 모델명의 유래인 로마 신화의 야누스(Janus, 두 개의 얼굴을 가진 신)처럼, **시각 이해와 이미지 생성이라는 두 가지 얼굴**을 하나의 모델에서 구현한다.

Janus-Pro의 핵심 통찰은 이해와 생성이 **근본적으로 다른 시각 표현을 필요로 한다**는 것이다. 시각 이해는 의미론적으로 풍부한 고수준(high-level) 표현이 중요하고, 이미지 생성은 픽셀 수준의 정밀한 저수준(low-level) 표현이 중요하다. 기존 통합 모델(Chameleon, Emu3 등)이 하나의 비전 인코더로 두 태스크를 모두 처리하려다 양쪽 모두에서 타협한 것과 달리, Janus-Pro는 **이해용 인코더(SigLIP)**와 **생성용 인코더(VQVAE)**를 독립적으로 운영하는 디커플링 아키텍처를 제안하였다. 이 설계로 7B 파라미터의 소형 모델에서도 DALL-E 3, SD3 수준의 생성 품질과 LLaVA-1.5급 이해 성능을 동시에 달성하였다.

논문: [Janus-Pro: Unified Multimodal Understanding and Generation with Data and Model Scaling](https://arxiv.org/abs/2501.17811)

## 아키텍처 상세

### 전체 구조

Janus-Pro는 네 가지 핵심 컴포넌트로 구성된다:

1. **이해용 비전 인코더**: SigLIP-L (400M params) — 의미론적 시각 표현 추출
2. **생성용 비전 인코더/디코더**: VQVAE (16,384 코드북) — 이미지를 이산 토큰으로 변환/복원
3. **MLP 어댑터 (2개)**: 각 인코더 출력을 LLM 공간에 매핑하는 독립적 프로젝터
4. **DeepSeek-LLM (7B)**: 통합 언어 모델 (이해 + 생성 모두 처리)

### 디커플링 아키텍처

이해 경로 (이미지 → 텍스트):
$$I \xrightarrow{\text{SigLIP}} h_{\text{semantic}} \xrightarrow{\text{MLP}_u} \text{LLM} \rightarrow \text{텍스트 응답}$$

생성 경로 (텍스트 → 이미지):
$$\text{텍스트 프롬프트} \rightarrow \text{LLM} \rightarrow \text{이미지 토큰} \xrightarrow{\text{VQVAE Decoder}} I$$

두 경로가 **동일한 LLM을 공유**하지만, 시각 인코딩은 완전히 독립적이다.

### 왜 디커플링인가?

| 요구사항 | 이해(Understanding) | 생성(Generation) |
|---------|-------------------|-----------------|
| 필요한 표현 | 의미론적, 추상적 | 픽셀 수준, 구체적 |
| 최적 인코더 | CLIP/SigLIP (대조 학습) | VQVAE (재구성 학습) |
| 정보 초점 | "무엇이 있는가?" | "어떻게 생겼는가?" |

SigLIP은 이미지의 의미(고양이, 개, 풍경 등)를 잘 포착하지만 픽셀 세부사항은 버린다. VQVAE는 픽셀 재구성을 위한 상세 정보를 보존하지만 고수준 의미 추출에는 약하다. 하나의 인코더로 두 가지를 모두 만족시키는 것은 근본적으로 어렵다.

| 구성 요소 | 사양 |
|-----------|------|
| LLM | DeepSeek-LLM-7B |
| 이해용 인코더 | SigLIP-L (400M) |
| 생성용 인코더 | VQVAE (16,384 코드북) |
| 이미지 해상도 | 384×384 (이해), 384×384 (생성) |
| 이미지 토큰 수 | 576 (이해), 576 (생성) |
| 컨텍스트 길이 | 4096 |

## 핵심 혁신

### 1. 이해-생성 디커플링

통합 멀티모달 모델에서 이해와 생성의 시각 인코더를 분리하는 것이 더 효과적이라는 핵심 통찰을 실험적으로 검증하였다. 커플링 vs 디커플링 실험에서 디커플링이 양쪽 태스크 모두에서 우수한 성능을 보였다.

### 2. 소형 모델에서의 고품질 생성

7B 파라미터만으로 DALL-E 3 수준의 이미지 생성 품질을 달성한 것은, 적절한 아키텍처 설계가 모델 규모를 보완할 수 있음을 보여준다.

### 3. 확장 가능한 데이터 전략

이해 데이터와 생성 데이터를 독립적으로 확장하여 각 태스크의 성능을 독립적으로 향상시킬 수 있다. Janus-Pro는 기존 Janus 대비 학습 데이터를 크게 확장하여 성능을 높였다.

## 벤치마크/성능

### 이해 성능

| 벤치마크 | Janus-Pro-7B | LLaVA-v1.5-7B | Chameleon-7B |
|----------|-------------|--------------|-------------|
| MMBench | **69.4** | 67.4 | — |
| MMMU | **36.3** | 35.8 | — |
| GQA | **60.3** | 62.0 | — |

### 생성 성능

| 벤치마크 | Janus-Pro-7B | SDXL | DALL-E 3 |
|----------|-------------|------|----------|
| GenEval (Overall) | **0.80** | 0.55 | 0.67 |
| DPG-Bench | **84.2** | 74.7 | 83.5 |

## 관련 모델 비교

| 특성 | Janus-Pro | Chameleon | Emu3 | Show-o2 |
|------|-----------|-----------|------|---------|
| 이해/생성 인코더 | **분리** | 공유 | 공유 | 공유 |
| 이해 인코더 | SigLIP | VQ-VAE | VQ-VAE | VQ-VAE |
| 생성 인코더 | VQVAE | VQ-VAE | VQ-VAE | VQ-VAE |
| 이해 성능 | 높음 | 보통 | 보통 | 보통 |
| 생성 품질 | 높음 | 보통 | 높음 | 보통 |
| 모델 크기 | 7B | 34B | 8B | 7B |

## 학습 상세

3단계 학습을 수행한다:

**Stage 1: 인코더 정렬**
- 이해용 MLP 어댑터: SigLIP 출력 → LLM 공간 매핑
- 생성용 MLP 어댑터: LLM 출력 → VQVAE 코드 예측을 위한 매핑
- LLM과 인코더는 고정

**Stage 2: 통합 SFT (Supervised Fine-Tuning)**
- 이해 데이터: LLaVA 스타일의 인스트럭션 튜닝 데이터
- 생성 데이터: 고품질 텍스트-이미지 쌍
- 두 태스크를 균형 있게 배합하여 멀티태스크 학습

**Stage 3: 생성 품질 향상**
- DPO 등을 통한 생성 품질 최적화
- 이해 성능 유지를 위한 정규화

## 실무 활용

```python
import torch
from janus.models import MultiModalModel

model = MultiModalModel.from_pretrained(
    "deepseek-ai/Janus-Pro-7B",
    torch_dtype=torch.bfloat16
).to("cuda")

# 이미지 이해
response = model.understand(
    image="photo.jpg",
    prompt="이 이미지의 내용을 자세히 설명해주세요."
)

# 이미지 생성
image = model.generate(
    prompt="A futuristic city with flying cars at sunset",
    num_images=1
)
image.save("generated.png")
```

## 한계 및 전망

### 한계

1. **단일 이미지 처리**: 다중 이미지나 비디오 처리를 위한 설계가 부재
2. **해상도 제한**: 384px로 고해상도 생성/이해에 한계가 있다
3. **생성 속도**: 자기회귀 방식으로 토큰을 하나씩 생성하므로 확산 모델 대비 느리다
4. **듀얼 인코더 메모리**: 두 개의 비전 인코더를 로드해야 하므로 메모리 사용량이 증가한다

### 전망

Janus-Pro의 디커플링 철학은 "만능 인코더는 존재하지 않는다"는 실용적 통찰에 기반하며, 향후 더 정교한 태스크별 전문 인코더 조합과 더 큰 LLM 백본으로의 확장이 기대된다. DeepSeek의 MoE 기술(DeepSeek-V3)과 결합하면 파라미터 효율성도 크게 높일 수 있을 것이다.

## 관련 문서

- [[deepseek-vl2|DeepSeek-VL2]] — 발전 기반
