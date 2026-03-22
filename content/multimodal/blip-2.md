---
title: "BLIP-2: Q-Former를 이용한 효율적 멀티모달 사전학습"
slug: "blip-2"
category: multimodal
tags: ["BLIP-2", "Efficient Training", "Frozen LLM", "Frozen LLM Bridge", "Modular Multimodal Learning", "Q-Former", "Salesforce", "Visual Question Answering", "VQA"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.514100+00:00"
architecture_entry: "blip-2"
---

# BLIP-2: Q-Former를 이용한 효율적 멀티모달 사전학습

## 개요

BLIP-2(Bootstrapping Language-Image Pre-training 2)는 2023년 1월 Salesforce Research가 발표한 멀티모달 사전학습 모델이다. 핵심 혁신은 **Q-Former(Querying Transformer)**라는 경량 브릿지 모듈로 고정된(frozen) 비전 인코더와 고정된 LLM을 연결하는 접근 방식이다.

기존 멀티모달 학습은 수십억 파라미터의 모델 전체를 학습해야 했지만, BLIP-2는 Q-Former(약 188M 파라미터)만 학습하여 학습 비용을 대폭 절감하면서도 SOTA 성능을 달성했다. Flamingo 80B 대비 **54배 적은 학습 파라미터**로 제로샷 VQAv2에서 **8.7% 더 높은** 성능을 기록한 것이 대표적 성과이다. 이 연구는 "거대한 사전학습 모델을 고정한 채로 경량 모듈만 학습하여 연결한다"는 효율적 멀티모달 학습 패러다임의 초석을 놓았다.

논문: [BLIP-2: Bootstrapping Language-Image Pre-training with Frozen Image Encoders and Large Language Models](https://arxiv.org/abs/2301.12597)

## 아키텍처 상세

### 전체 구조

BLIP-2는 세 가지 핵심 컴포넌트로 구성된다:

1. **비전 인코더(Frozen)**: EVA-CLIP ViT-G/14 (1B params) — 이미지에서 패치 수준의 시각 특징을 추출
2. **Q-Former(Trainable)**: 쿼리 트랜스포머 (188M params) — 시각 특징을 LLM이 이해 가능한 토큰으로 변환
3. **LLM(Frozen)**: OPT-2.7B/6.7B 또는 FlanT5-XL/XXL — 텍스트 이해 및 생성

이 구조에서 실제로 학습되는 것은 Q-Former와 연결 레이어뿐이며, 수십억 파라미터의 비전 인코더와 LLM은 그대로 유지된다.

### Q-Former 구조

Q-Former는 BLIP-2의 핵심 모듈로, 두 개의 트랜스포머 서브모듈이 셀프 어텐션 레이어를 공유한다:

1. **이미지 트랜스포머**: 32개의 학습 가능한 쿼리 벡터($\mathbf{q} \in \mathbb{R}^{32 \times 768}$)가 비전 인코더 출력과 교차 어텐션(cross-attention)을 통해 시각 정보를 추출
2. **텍스트 트랜스포머**: BERT-base 구조를 공유하며, 셀프 어텐션 레이어를 통해 이미지 트랜스포머와 상호작용

쿼리 벡터가 추출하는 시각 정보는 LLM이 이해할 수 있는 **소프트 비주얼 프롬프트(soft visual prompt)**로 변환된다:

$$\text{Visual Tokens} = \text{Q-Former}(\text{Queries}, \text{ViT\_Output}) \in \mathbb{R}^{32 \times d_{LLM}}$$

여기서 $d_{LLM}$은 LLM의 임베딩 차원이며, FC 레이어로 Q-Former 출력을 LLM 입력 공간에 매핑한다. 이 32개의 시각 토큰이 텍스트 프롬프트 앞에 prepend되어 LLM에 입력된다.

### 2단계 학습 전략

**Stage 1: 비전-언어 표현 학습 (Vision-Language Representation Learning)**

Q-Former와 비전 인코더를 연결하여 세 가지 목표를 동시에 학습한다:

- **ITC (Image-Text Contrastive Learning)**: 이미지 쿼리 표현과 텍스트 CLS 표현 사이의 대조 학습. 유니모달 셀프 어텐션 마스크로 이미지/텍스트가 서로를 직접 보지 못하게 한다.
- **ITM (Image-Text Matching)**: 이미지-텍스트 매칭 이진 분류. 양방향 셀프 어텐션 마스크로 쿼리와 텍스트 간 상호작용 허용.
- **ITG (Image-grounded Text Generation)**: 이미지 기반 텍스트 생성. 인과적(causal) 셀프 어텐션 마스크 사용.

이 세 가지 손실의 핵심은 **셀프 어텐션 마스크 전략**이 다르다는 점이며, 이를 통해 하나의 Q-Former가 세 가지 다른 기능을 동시에 학습한다.

**Stage 2: 비전-언어 생성 학습 (Vision-to-Language Generative Learning)**

Q-Former 출력을 FC 레이어를 통해 LLM 입력 공간에 매핑하고, LLM이 시각 정보를 조건으로 텍스트를 생성하도록 학습한다. 디코더 기반 LLM(OPT)에는 language modeling 손실을, 인코더-디코더 기반 LLM(FlanT5)에는 prefix language modeling 손실을 사용한다.

| 구성 요소 | 사양 |
|-----------|------|
| Q-Former 레이어 | 12층, 768 히든 차원, 12 헤드 |
| 학습 가능 쿼리 | 32개 |
| 비전 인코더 | EVA-CLIP ViT-G/14 (1B, frozen) |
| LLM 옵션 | OPT-2.7B/6.7B, FlanT5-XL/XXL (frozen) |
| 학습 파라미터 | ~188M (Q-Former + FC 레이어) |

## 핵심 혁신

### 1. 정보 병목(Information Bottleneck)

Q-Former의 32개 쿼리는 비전 인코더의 수백 개 패치 토큰(ViT-G는 257개)에서 가장 관련 있는 시각 정보만 선택적으로 추출하는 **정보 병목** 역할을 한다. 이는 LLM에 불필요한 시각 노이즈가 전달되는 것을 방지하고, 핵심 시각 의미만 압축하여 효율적인 비전-언어 정렬을 가능하게 한다. 수백 개의 시각 토큰 대신 32개만 LLM에 전달하므로 추론 비용도 크게 절감된다.

### 2. 모듈형 설계(Modular Design)

OPT, FlanT5 등 다양한 LLM과 결합 가능한 모듈형 설계로, LLM을 교체하는 것만으로 새로운 능력을 추가할 수 있다. 더 강력한 LLM이 등장하면 Q-Former는 유지한 채 LLM만 교체하여 성능을 향상시킬 수 있으며, 이는 이후 LLaVA, InternVL 등 모듈형 VLM 연구의 기반이 되었다.

### 3. 셀프 어텐션 마스크를 통한 멀티태스크 학습

동일한 Q-Former 아키텍처에서 셀프 어텐션 마스크만 변경하여 대조 학습, 매칭, 생성 세 가지 목표를 동시에 학습하는 우아한 설계는 파라미터 공유를 극대화하면서도 다양한 비전-언어 능력을 갖추게 한다.

## 벤치마크/성능

| 모델 | VQAv2 (0-shot) | GQA | 학습 파라미터 |
|------|---------------|-----|-------------|
| BLIP-2 (FlanT5-XXL) | **65.0%** | 44.7% | 188M |
| Flamingo-80B | 56.3% | — | ~10B |
| Flamingo-9B | 51.8% | — | ~1.5B |
| BLIP-2 (OPT-6.7B) | 54.7% | 36.4% | 188M |
| Kosmos-1 | 51.0% | — | 1.6B |

학습 비용 비교:
- **Stage 1**: 16 A100 GPU, 6일 (AdamW, lr=1e-4, cosine schedule)
- **Stage 2**: 8 A100 GPU, 3일
- **Flamingo 80B**: 수천 TPU, 수주 소요

## 관련 모델 비교

| 특성 | BLIP-2 | Flamingo | LLaVA | CogVLM |
|------|--------|----------|-------|--------|
| 브릿지 모듈 | Q-Former | Perceiver Resampler | Linear/MLP | Visual Expert |
| LLM 학습 | Frozen | Frozen | Full Fine-tuning | Frozen (+ Expert) |
| 학습 파라미터 | 188M | ~10B | 7B+ | ~6B |
| 시각 토큰 수 | 32 (고정) | 64 (고정) | 256+ (가변) | 256+ (가변) |
| 설계 철학 | 효율적 브릿지 | 소수샷 학습 | 극도의 단순성 | 깊은 층별 융합 |

## 학습 상세

학습 데이터 구성:

| 데이터셋 | 규모 | 용도 |
|----------|------|------|
| COCO | 113K | 이미지-캡션 |
| CC3M | 3M | 웹 이미지-텍스트 |
| CC12M | 12M | 웹 이미지-텍스트 |
| SBU Captions | 1M | 이미지-캡션 |
| LAION-400M | 115M (부분) | 대규모 웹 |

옵티마이저: AdamW ($\beta_1=0.9, \beta_2=0.98$, weight decay 0.05)
학습률: 1e-4 (cosine decay, 2000 step warmup)
이미지 해상도: 224×224 (Stage 1), 224×224 (Stage 2)

## 실무 활용

```python
from transformers import Blip2Processor, Blip2ForConditionalGeneration
from PIL import Image
import torch

# 모델 로드
processor = Blip2Processor.from_pretrained("Salesforce/blip2-opt-2.7b")
model = Blip2ForConditionalGeneration.from_pretrained(
    "Salesforce/blip2-opt-2.7b", torch_dtype=torch.float16
).to("cuda")

# 이미지 캡셔닝
image = Image.open("photo.jpg")
inputs = processor(images=image, return_tensors="pt").to("cuda", torch.float16)
output = model.generate(**inputs, max_new_tokens=50)
print(processor.decode(output[0], skip_special_tokens=True))

# VQA (Visual Question Answering)
prompt = "Question: What is the main object in this image? Answer:"
inputs = processor(images=image, text=prompt, return_tensors="pt").to("cuda", torch.float16)
output = model.generate(**inputs, max_new_tokens=50)
print(processor.decode(output[0], skip_special_tokens=True))
```

### 주요 활용 분야

1. **이미지 캡셔닝**: 자동 이미지 설명 생성 (접근성, 검색 최적화)
2. **시각적 질의응답(VQA)**: 이미지에 대한 자연어 질문 응답
3. **이미지-텍스트 검색**: 멀티모달 유사도 기반 검색 시스템
4. **멀티모달 챗봇**: InstructBLIP로 확장된 대화형 AI

## 한계 및 전망

### 한계

1. **고정된 비전 인코더**: 비전 인코더 업데이트 불가로 세밀한 시각 이해(fine-grained recognition)에 제한이 있다
2. **쿼리 수 제한**: 32개 쿼리로 시각 정보를 압축하므로 복잡한 장면에서 정보 손실이 발생할 수 있다
3. **저해상도**: 224px 입력으로 OCR, 문서 이해 등 고해상도가 필요한 태스크에 한계가 있다
4. **단일 이미지**: 다중 이미지나 비디오 처리를 위한 설계가 부재하다

### 전망

BLIP-2의 Q-Former 개념은 InstructBLIP, mPLUG-Owl, MiniGPT-4 등으로 확장되었으며, "고정된 모델을 경량 모듈로 연결"하는 패러다임은 멀티모달 연구의 핵심 접근법으로 자리잡았다. 2024년 이후에는 LLaVA 방식의 단순한 MLP 프로젝터가 주류가 되면서 Q-Former의 직접적 사용은 줄었으나, 정보 병목 개념과 모듈형 설계 철학은 여전히 많은 연구에 영향을 미치고 있다. 특히 시각 토큰 수를 줄여 LLM 추론 비용을 절감하는 연구 방향에서 Q-Former의 아이디어가 재조명받고 있다.

## 관련 문서

- [[clip|CLIP]] — 발전 기반
