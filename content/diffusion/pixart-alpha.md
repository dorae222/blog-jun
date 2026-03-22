---
title: "PixArt-α: 확산 기반 이미지 생성 모델"
slug: "pixart-alpha"
category: diffusion
tags: ["AdaLN-Single", "Cross-Attention Text Conditioning", "Efficient DiT Training", "Huawei Noah's Ark Lab", "PixArt-α", "T5 Encoder", "Three-Stage Training"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.412795+00:00"
architecture_entry: "pixart-alpha"
---

# PixArt-α: 효율적 학습 기반 텍스트-이미지 확산 트랜스포머

**Huawei Noah's Ark Lab** · **2023-10-03** · **Diffusion** · **Apache 2.0**

## 개요

PixArt-α는 2023년 Huawei Noah's Ark Lab이 발표한 텍스트-이미지 DiT(Diffusion Transformer) 모델로, 학습 비용을 극단적으로 절감하면서도 상업 수준의 이미지 품질을 달성한 효율적 학습 전략이 핵심 기여이다. 대규모 텍스트-이미지 생성 모델의 학습은 막대한 컴퓨팅 자원을 요구한다. DALL-E 2는 수천만 달러, Stable Diffusion XL은 약 $320만 수준의 학습 비용이 소요되는 것으로 추정된다. 이러한 높은 비용 장벽은 소규모 연구 기관이나 개인 연구자가 대규모 생성 모델을 연구하는 것을 사실상 불가능하게 만들었다.

PixArt-α는 이 문제를 세 단계 분리 학습 전략(Three-Stage Training)으로 해결하였다. 전체 학습 비용은 약 2만 8000 A100 GPU 시간(약 $32만)으로, SDXL 학습 비용의 약 1/10 수준이다. 핵심 아이디어는 픽셀 수준의 구조 학습, 텍스트-이미지 정렬, 미적 품질 향상이라는 세 가지 과제를 분리하여 각 단계에서 효율적으로 학습하는 것이다. Stage 1에서 ImageNet 클래스 조건부 생성으로 기본적인 이미지 구조를 학습하고, Stage 2에서 소규모(~300만 장) 고품질 이미지-텍스트 쌍으로 텍스트 정렬을 학습하며, Stage 3에서 미적 품질을 미세조정한다. 이 전략은 각 단계에서 모델이 학습해야 할 과제를 명확히 분리함으로써 데이터 효율성을 극대화한다.

아키텍처적으로는 DiT에 Cross-Attention 블록을 추가하여 T5-XXL 텍스트 인코더와 연동하며, AdaLN-Single 기법으로 타임스텝 임베딩 파라미터를 약 30% 절감하였다. MS-COCO 기준 FID 7.32를 달성하며, 사용자 선호도 평가에서 SDXL과 경쟁력 있는 수준을 보였다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

### DiT 블록 구조

PixArt-α의 DiT 블록은 **Self-Attention → Cross-Attention → FFN** 순서로 구성된다. 입력 이미지는 VAE 인코더를 통해 잠재 공간으로 압축된 후, 고정 크기 패치로 분할되어 1D 토큰 시퀀스가 된다. Self-Attention은 이미지 토큰 간의 공간적 관계를 포착하고, Cross-Attention은 T5-XXL 텍스트 임베딩을 Key·Value로 활용하여 텍스트 조건을 주입한다. FFN(Feed-Forward Network)은 GELU 활성화 함수를 사용하며, 각 서브레이어에 residual connection이 적용된다.

전체 모델은 28개의 DiT 블록으로 구성되며, 히든 차원 1152, 16개의 어텐션 헤드를 사용한다. 총 파라미터 수는 약 600M으로, SDXL(2.6B)의 약 1/4 수준이다.

### AdaLN-Single: 효율적 조건 주입

기존 DiT의 Adaptive Layer Normalization(adaLN)은 각 블록마다 독립적인 선형 레이어를 사용하여 타임스텝 $t$에서 스케일 $\gamma$과 시프트 $\beta$를 생성한다:

$$\text{adaLN}(h, t) = \gamma_i(t) \odot \text{LN}(h) + \beta_i(t)$$

여기서 $i$는 블록 인덱스이며, 블록 수만큼 독립적인 MLP가 필요하다. PixArt-α의 **AdaLN-Single**은 타임스텝 임베딩에서 공유 임베딩 $c_{\text{shared}}$를 한 번만 계산하고, 각 블록의 스케일·시프트를 $c_{\text{shared}}$의 간단한 선형 변환으로 생성한다:

$$c_{\text{shared}} = \text{MLP}(t), \quad \gamma_i = W_i^\gamma c_{\text{shared}}, \quad \beta_i = W_i^\beta c_{\text{shared}}$$

이를 통해 약 30%의 파라미터 절감이 이루어지면서도, 성능 저하는 무시할 수 있는 수준이다.

### 텍스트 인코딩 및 위치 인코딩

텍스트 조건은 동결된 T5-XXL(11B 파라미터) 인코더에서 추출한 120 토큰 길이의 임베딩을 사용한다. 이미지 패치의 2D 위치 정보는 **NTK-aware RoPE**(Rotary Position Embedding)로 인코딩되며, 1024x1024 고해상도 생성 시에도 위치 정보가 안정적으로 외삽된다.

### 확산 과정의 수학적 정의

PixArt-α는 표준 DDPM 확산 과정을 사용한다. Forward 과정에서 노이즈 추가는 다음과 같다:

$$q(\mathbf{x}_t|\mathbf{x}_0) = \mathcal{N}(\sqrt{\bar{\alpha}_t}\mathbf{x}_0, (1-\bar{\alpha}_t)\mathbf{I})$$

학습 목표는 노이즈 예측이다:

$$\mathcal{L} = \mathbb{E}_{t, \mathbf{x}_0, \boldsymbol{\epsilon}}\left[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t, c_{\text{text}})\|^2\right]$$

추론 시에는 Classifier-Free Guidance(CFG)를 적용하여 텍스트 정렬도를 높인다:

$$\hat{\boldsymbol{\epsilon}}_\theta = \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t, \varnothing) + s \cdot (\boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t, c) - \boldsymbol{\epsilon}_\theta(\mathbf{x}_t, t, \varnothing))$$

## 핵심 혁신

PixArt-α의 핵심 혁신은 대규모 텍스트-이미지 모델의 학습 비용 장벽을 극적으로 낮춘 것이다. 세 단계 분리 학습은 각 과제를 독립적으로 최적화하여 데이터 효율성을 극대화한다. AdaLN-Single은 조건 주입의 파라미터 효율을 개선하면서 모델 크기를 줄인다. 고품질 캡션 데이터(LLaVA로 자동 생성)의 활용은 소규모 데이터셋으로도 높은 텍스트 정렬을 달성하는 핵심 요인이다. 이러한 효율적 설계 철학은 후속 모델인 PixArt-δ(LCM 증류), PixArt-Σ(4K 생성)로 계승되었으며, 학계와 산업계 모두에서 효율적 학습의 가능성을 입증한 사례로 평가받는다.

## 벤치마크/성능

| 모델 | FID (↓) | CLIP Score (↑) | 학습 비용 (A100일) | 파라미터 |
|------|---------|----------------|-------------------|--------|
| PixArt-α | 7.32 | 0.312 | 675 | 600M |
| SDXL | 6.63 | 0.310 | 6,250 | 2.6B |
| DALL-E 2 | 10.39 | 0.314 | ~41,000 | 6.5B |
| Imagen | 7.27 | - | ~10,000 | 3B+ |
| SD 1.5 | 9.62 | 0.305 | 6,250 | 860M |

PixArt-α는 SDXL 대비 약 1/10의 학습 비용으로 MS-COCO FID 7.32를 달성하며, Human Preference 평가에서도 경쟁력 있는 수준을 보인다. 학습 비용 대비 성능 효율 측면에서 당시 최고 수준이다.

## 학습

3단계 분리 학습: **Stage 1** -- ImageNet-1k 256x256 클래스 조건부 생성(200 에폭)으로 픽셀 구조 학습, **Stage 2** -- SAM(1100만 장) + JourneyDB(350만 장) 텍스트 조건부 학습(20 에폭)으로 텍스트-이미지 정렬 학습, **Stage 3** -- LAION-Aesthetics 고품질 데이터 미세조정(10 에폭)으로 미적 품질 향상. 총 학습 비용은 약 675 A100 GPU일(약 $32만). T5-XXL(11B) 텍스트 인코더는 동결 사용하며 별도 학습하지 않는다. 옵티마이저는 AdamW, 학습률은 2e-5이다.

## 관련 모델

PixArt-α는 DiT에서 직접 발전하였으며, Cross-Attention 기반 텍스트 조건부 생성을 DiT에 최초로 효과적으로 적용한 사례이다. 후속 모델로 PixArt-δ(LCM 증류 기반 4스텝 생성), PixArt-Σ(4K 해상도 지원)가 있다.

## 참고 자료

- [논문: PixArt-α: Fast Training of Diffusion Transformer for Photorealistic Text-to-Image Synthesis](https://arxiv.org/abs/2310.00426)
- [코드](https://github.com/PixArt-alpha/PixArt-alpha)

## 관련 문서

- [[dit|DiT (Diffusion Transformers)]] — 발전 기반