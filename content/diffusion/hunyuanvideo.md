---
title: "HunyuanVideo: 확산 기반 비디오 생성 모델"
slug: hunyuanvideo
category: diffusion
tags: ["3D RoPE", "CausalVAE", "Dual-Stream Transformer", "Flow Matching", "HunyuanVideo", "MLLM Text Encoder", "Open-Source Video Generation", "Tencent"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.211140+00:00"
architecture_entry: hunyuanvideo
---

# HunyuanVideo: 오픈소스 대규모 비디오 생성 모델

## 개요

HunyuanVideo는 2024년 12월 Tencent가 발표한 오픈소스 텍스트-비디오 생성 모델로, 13B 파라미터 규모의 Dual-Stream Transformer 아키텍처를 통해 오픈소스 비디오 생성 모델 중 최고 수준의 시각 품질을 달성하였다.

- **논문**: [HunyuanVideo: A Systematic Framework For Large Video Generation Model](https://arxiv.org/abs/2412.03603)
- **코드**: [Tencent/HunyuanVideo](https://github.com/Tencent/HunyuanVideo)
- **발표**: 2024년 12월, Tencent
- **라이선스**: Apache 2.0

## 아키텍처 상세

### Dual-Stream Transformer

HunyuanVideo의 핵심은 FLUX.1의 Hybrid MMDiT에서 영감을 받은 Dual-Stream Transformer이다:

**Full Attention 레이어**: 비디오 시퀀스 $z^v$와 텍스트 시퀀스 $z^t$를 결합하여 상호 어텐션 계산:

$$\text{Attn}([z^v; z^t]) = \text{softmax}\left(\frac{Q_{[v;t]} K_{[v;t]}^T}{\sqrt{d}}\right) V_{[v;t]}$$

**독립 스트림 레이어**: 각 모달리티가 자체 파라미터로만 처리.

| 구성 요소 | 사양 |
|----------|------|
| 파라미터 | 13B |
| 텍스트 인코더 | LLaVA MLLM + CLIP |
| 텍스트 토큰 | 256 |
| 정규화 | RMSNorm |
| 활성화 | SiLU |
| 위치 인코딩 | 3D RoPE |
| 학습 기법 | Flow Matching |

### CausalVAE (3D Video VAE)

시간 방향 4배, 공간 방향 8배 압축을 수행하는 3D Causal VAE:

$$z = \text{CausalVAE}_{enc}(x) \in \mathbb{R}^{T/4 \times H/8 \times W/8 \times C}$$

인과 합성곱(Causal Conv3D)을 사용하여 현재 프레임은 이전 프레임에만 의존하도록 한다. 720p 129프레임 기준 잠재 크기는 $33 \times 45 \times 80 \times 16$이다.

이 인과 구조는 두 가지 장점을 제공한다:
- **스트리밍 생성**: 프레임을 순차적으로 인코딩/디코딩 가능
- **비디오 연장**: 기존 비디오의 끝 부분에서 자연스럽게 연장 가능

### 3D RoPE

프레임 인덱스($t$), 높이($h$), 너비($w$)에 각각 독립적인 주파수를 할당:

$$\text{RoPE}_{3D}(q, t, h, w) = \text{RoPE}(q^{(t)}, t) \oplus \text{RoPE}(q^{(h)}, h) \oplus \text{RoPE}(q^{(w)}, w)$$

### MLLM 텍스트 인코더

LLaVA 계열의 멀티모달 언어 모델을 텍스트 인코더로 활용하여 기존 CLIP이나 T5보다 풍부한 시각-언어 이해력을 제공한다. CLIP과 LLaVA를 함께 사용하는 이중 텍스트 인코딩 전략으로 저수준 시각 특성과 고수준 의미 정보를 모두 포착한다.

## 핵심 혁신

1. **13B 오픈소스 비디오 모델**: Apache 2.0으로 가중치, 추론 코드, VAE를 전면 공개한 최대 규모의 비디오 생성 모델이다.
2. **MLLM 텍스트 인코더**: CLIP/T5 대신 멀티모달 LLM을 텍스트 인코더로 활용하여 프롬프트 이해력을 향상시켰다.
3. **CausalVAE**: 인과 합성곱 기반 3D VAE로 스트리밍 생성과 비디오 연장이 가능하다.
4. **Full 3D Attention**: 모든 시공간 위치 간의 어텐션으로 높은 시간적 일관성을 달성한다.

## 벤치마크/성능

| 모델 | VBench 총점 | 해상도 | 길이 | 오픈소스 |
|------|-----------|--------|------|---------|
| HunyuanVideo | **최상위** | 720p | 5초 | Apache 2.0 |
| CogVideoX-5B | 81.6 | 480p/720p | 6초 | Apache 2.0 |
| Gen-3 Alpha | 높음 | 720p/1080p | 10초 | 비공개 |
| Kling 2.0 | 높음 | 1080p | 120초 | 비공개 |

VBench 벤치마크에서 오픈소스 모델 최상위 점수를 기록하였다.

## 관련 모델 비교

| 특성 | HunyuanVideo | CogVideoX | Sora | FLUX.1 |
|------|------------|-----------|------|--------|
| 도메인 | 비디오 | 비디오 | 비디오 | 이미지 |
| 파라미터 | 13B | 5B | 비공개 | 12B |
| 텍스트 인코더 | LLaVA+CLIP | T5-XXL | 비공개 | CLIP+T5 |
| VAE | CausalVAE 3D | 3D VAE | 비디오 VAE | 2D VAE |
| 어텐션 | Dual-Stream | Full 3D+ExpertAdaLN | Full 3D | Hybrid MMDiT |

## 학습 상세

- **데이터셋**: Tencent 내부 비디오 데이터 + 공개 데이터
- **학습 전략**: 저해상도 사전학습 → 고해상도 미세조정 다단계
- **학습 기법**: Flow Matching (직선 궤적)
- **분산 어텐션**: Ring Attention 등 메모리 효율화 기법 적용
- **공개 범위**: 모델 가중치, 추론 코드, VAE 모두 Apache 2.0

## 실무 활용

### 1. 오픈소스 비디오 생성 서비스

Apache 2.0 라이선스로 자체 비디오 생성 서비스 구축 가능. Diffusers, ComfyUI에서 지원.

### 2. 비디오 생성 연구

13B 규모의 사전학습된 비디오 생성 모델을 기반으로 다양한 후속 연구(비디오 편집, 스타일 전이 등)가 가능하다.

### 3. 이미지-비디오 변환

정적 이미지를 조건으로 자연스러운 동작의 비디오를 생성하는 I2V 파이프라인에 활용 가능하다. 제품 사진, 인물 사진 등을 동적인 비디오로 변환하여 마케팅, 소셜 미디어 콘텐츠 제작에 직접 활용할 수 있다.

## 한계 및 전망

### 한계

1. **짧은 생성 길이**: 5초(129프레임)로 상업 모델 대비 제한적이다.
2. **VRAM 요구량**: 13B 모델은 대규모 GPU 메모리가 필요하다.
3. **Full 3D Attention 비용**: 시공간 전체 어텐션의 이차 복잡도가 장시간 비디오 생성을 제한한다.

### 후속 발전

- **HunyuanVideo 1.5/2.0**: 더 긴 비디오, 더 높은 해상도 지원 예정
- **커뮤니티 양자화**: 소비자 GPU에서의 실행을 위한 양자화 연구
- **비디오 편집**: ControlNet, IP-Adapter의 비디오 확장

HunyuanVideo는 오픈소스 비디오 생성의 새로운 기준을 수립한 모델로, 비디오 생성 AI의 민주화에 크게 기여하였다.

### 기술적 의의

HunyuanVideo의 가장 큰 기여는 13B 규모의 비디오 생성 모델을 Apache 2.0으로 전면 공개한 것이다. 이는 비디오 생성 분야에서 사전학습 모델의 접근 장벽을 크게 낮추어, 연구자들이 비디오 편집, 스타일 전이, 비디오 이해 등 다양한 후속 연구를 수행할 수 있는 기반을 제공하였다. MLLM(멀티모달 언어 모델)을 텍스트 인코더로 활용한 것은 기존 CLIP이나 T5 중심의 텍스트 인코딩에서 벗어나 더 풍부한 시각-언어 이해를 가능하게 한 혁신적 선택이다. CausalVAE의 인과 구조는 비디오 연장(extension)과 스트리밍 생성이라는 실용적 기능을 가능하게 하며, 이는 단순 VAE 대비 비디오 생성에 특화된 설계이다. Dual-Stream Transformer와 Full 3D Attention의 결합은 FLUX.1의 이미지 생성 아키텍처를 비디오 영역으로 자연스럽게 확장한 사례로, 이미지-비디오 생성 아키텍처의 수렴 경향을 보여준다.

## 관련 문서

- [[dit|DiT (Diffusion Transformers)]] — 발전 기반
