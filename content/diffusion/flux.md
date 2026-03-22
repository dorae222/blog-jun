---
title: "FLUX.1: 확산 기반 이미지 생성 모델"
slug: flux
category: diffusion
tags: ["Black Forest Labs", "Double-Stream Attention", "Flow Matching", "FLUX.1", "Guidance Distillation", "Hybrid MMDiT", "Parallel Attention", "RoPE for Images", "Single-Stream Attention"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.286338+00:00"
architecture_entry: flux
---

# FLUX.1: 하이브리드 MMDiT 기반 텍스트-이미지 생성

## 개요

FLUX.1은 2024년 Black Forest Labs(Stable Diffusion 원작자 그룹)가 공개한 12B 파라미터 규모의 텍스트-이미지 생성 모델로, Flow Matching 학습과 Hybrid MMDiT 아키텍처를 통해 오픈소스 모델 중 최고 수준의 이미지 품질과 텍스트 충실도를 달성하였다.

- **코드**: [black-forest-labs/flux](https://github.com/black-forest-labs/flux)
- **발표**: 2024년 8월, Black Forest Labs
- **라이선스**: Apache 2.0 (schnell) / Non-Commercial (dev)

## 아키텍처 상세

### Hybrid MMDiT: 이중 스트림 + 단일 스트림

FLUX.1의 핵심 혁신은 SD3의 MMDiT를 발전시킨 하이브리드 아키텍처이다:

**Phase 1 — Double-Stream 블록 (19개):**

이미지와 텍스트가 각자 독립적인 파라미터로 처리되면서 양방향 상호작용:

$$Q = [W_Q^x h^x; W_Q^y h^y], \quad K = [W_K^x h^x; W_K^y h^y], \quad V = [W_V^x h^x; W_V^y h^y]$$

$$\text{Attn}([h^x; h^y]) = \text{softmax}\left(\frac{QK^T}{\sqrt{d}}\right) V$$

출력을 다시 이미지/텍스트로 분리하여 각 스트림의 독립적 업데이트가 이루어진다.

**Phase 2 — Single-Stream 블록 (38개):**

이미지+텍스트를 하나의 시퀀스로 통합하여 공유 파라미터로 효율적 처리.

| 구성 요소 | 사양 |
|----------|------|
| 파라미터 | 12B |
| 이중 스트림 블록 | 19 |
| 단일 스트림 블록 | 38 |
| 히든 차원 | 3072 |
| 어텐션 헤드 | 24 |
| 텍스트 인코더 | CLIP-L (77 토큰) + T5-XXL (256 토큰) |
| 정규화 | AdaRMSNorm |
| 활성화 | GELU |
| 위치 인코딩 | RoPE (이미지) + Absolute (텍스트) |

### Parallel Attention

Self-Attention과 FFN을 순차적으로 실행하는 대신 병렬 실행:

$$h \leftarrow h + \text{Attn}(h) + \text{FFN}(h)$$

KV 캐시를 공유하여 연산 효율을 높이고, 추론 시 텐서 병렬화에 유리하다.

### RoPE for Images

2D 패치 좌표 $(h, w)$에 RoPE를 적용하여 임의 종횡비와 해상도 생성을 지원한다. 이는 고정 위치 인코딩 대비 해상도 외삽 능력이 뛰어나다.

### 세 가지 버전

| 버전 | 특성 | 스텝 수 | 라이선스 |
|------|------|--------|---------|
| FLUX.1-pro | 최고 품질, API 전용 | ~28 | 상업용 |
| FLUX.1-dev | 가이던스 증류(CFG 내재화) | ~20 | Non-Commercial |
| FLUX.1-schnell | 일관성 증류 | 4~8 | Apache 2.0 |

## 핵심 혁신

1. **Hybrid Double/Single-Stream**: 초반에는 이미지-텍스트 독립 처리로 풍부한 표현을 학습하고, 후반에는 통합 처리로 효율을 높이는 두 단계 설계이다.
2. **Parallel Attention**: Attn과 FFN을 병렬 실행하여 추론 효율을 향상시켰다.
3. **Guidance Distillation**: FLUX.1-dev는 CFG 효과를 모델에 내재화하여 단일 패스로 추론하므로 CFG의 2배 비용 문제를 해결하였다.
4. **12B 스케일 오픈소스**: 당시 오픈소스 이미지 생성 모델 중 최대 규모의 파라미터를 공개하였다.

## 벤치마크/성능

| 모델 | ELO 점수 | 텍스트 렌더링 | 인체 표현 | 종횡비 다양성 |
|------|---------|------------|---------|------------|
| FLUX.1-pro | **1위권** | 우수 | 우수 | 임의 |
| Midjourney v6.0 | 상위 | 보통 | 우수 | 제한적 |
| DALL·E 3 | 상위 | 우수 | 보통 | 제한적 |
| SDXL | 중간 | 낮음 | 보통 | 제한적 |
| Ideogram 2.0 | 상위 | 우수 | 보통 | 임의 |

ELO 기반 이미지 생성 평가에서 Midjourney v6.0, DALL·E 3, Ideogram 2.0 대비 최상위 성능을 기록하였다.

## 관련 모델 비교

| 특성 | FLUX.1 | SD3 | SDXL | DALL·E 3 |
|------|--------|-----|------|---------|
| 백본 | Hybrid MMDiT | MMDiT | U-Net | 비공개 |
| 파라미터 | 12B | 2B/8B | 3.5B | 비공개 |
| 학습 기법 | Flow Matching | Flow Matching | DDPM | 비공개 |
| 텍스트 인코더 | CLIP-L + T5-XXL | CLIP-L + CLIP-G + T5-XXL | CLIP + OpenCLIP | 비공개 |
| 오픈소스 | 부분 (schnell) | 부분 (Medium) | 전체 | 아니오 |

## 학습 상세

- **데이터셋**: 수억 장 규모 이미지-텍스트 쌍 (비공개)
- **텍스트 인코더**: T5-XXL (11B) + CLIP-L (동결)
- **학습 기법**: Flow Matching (직선 궤적)
- **NFE**: ~28 (pro), ~20 (dev), 4~8 (schnell)
- **FLUX.1-dev**: Guidance Distillation으로 CFG 효과 내재화
- **FLUX.1-schnell**: Consistency Distillation으로 4~8스텝 가속

## 실무 활용

### 1. 오픈소스 고품질 이미지 생성

FLUX.1-schnell (Apache 2.0)은 상업적으로 자유롭게 활용 가능하며, 4~8스텝으로 빠른 추론이 가능하다.

### 2. LoRA/ControlNet 생태계

ComfyUI, Diffusers 등에서 FLUX.1용 LoRA, ControlNet, IP-Adapter가 활발히 개발되고 있으며, 오픈소스 생태계가 빠르게 성장하고 있다.

### 3. 실시간 이미지 생성

FLUX.1-schnell의 4스텝 생성은 인터랙티브 이미지 편집, 실시간 시각화 등에 적합하다.

## 한계 및 전망

### 한계

1. **VRAM 요구량**: 12B 파라미터 모델은 FP16에서 약 24GB VRAM이 필요하여, 소비자 GPU에서의 실행에 양자화가 필요하다.
2. **부분 오픈소스**: pro 모델은 API로만 접근 가능하며, dev 모델은 비상업 라이선스이다.
3. **공식 논문 부재**: 기술 보고서나 논문이 공개되지 않아 세부 아키텍처 정보가 제한적이다.

### 후속 발전

- **FLUX.2 (2025)**: 텍스트 렌더링, 캐릭터 일관성 추가 개선
- **커뮤니티 양자화**: GGUF, NF4 등 다양한 양자화로 8GB VRAM에서도 실행 가능
- **FLUX Fill/Canny/Depth**: 인페인팅, ControlNet 변형 공식 공개

FLUX.1은 Stable Diffusion 원작자들이 SD3의 설계를 더욱 발전시켜 만든 모델로, 오픈소스 이미지 생성의 새로운 기준을 수립하였다.

### 기술적 의의

FLUX.1의 Hybrid Double/Single-Stream 설계는 "이미지와 텍스트를 어떻게 결합할 것인가"라는 근본적 질문에 대한 가장 정교한 답변 중 하나이다. 초반 이중 스트림에서 각 모달리티가 독립적으로 풍부한 표현을 구축한 뒤 후반 단일 스트림에서 효율적으로 통합하는 설계는, 단순한 Cross-Attention이나 일률적 결합보다 더 높은 품질과 효율을 동시에 달성한다. 12B 규모의 오픈소스 모델 공개는 이전까지 API로만 접근 가능하던 상업 모델 수준의 품질을 커뮤니티에 보급하여, LoRA, ControlNet, IP-Adapter 등 광범위한 생태계 구축을 촉진하였다.

## 관련 문서

- [[sd3|Stable Diffusion 3]] — 발전 기반
- [[flux-2|FLUX.2]] — 후속 모델
- [[flow-matching|Flow Matching]] — 사용 기법
