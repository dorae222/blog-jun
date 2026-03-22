---
title: "Molmo: 멀티모달 AI 모델"
slug: molmo
category: multimodal
tags: ["AI2", "Coordinate Grounding", "Molmo", "PixMo Dataset", "Visual Pointing"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-22T10:37:37.256690+00:00"
architecture_entry: molmo
---

# Molmo: 시각적 포인팅 능력을 갖춘 멀티모달 모델

## 개요

Molmo는 2024년 9월 Allen AI Institute(AI2)가 발표한 멀티모달 모델이다. Molmo의 차별점은 **이미지 내 객체를 정확히 가리키는(pointing) 능력**과, 이를 위해 새롭게 구축한 **PixMo 데이터셋**이다.

기존 VLM들이 이미지에 대한 텍스트 설명을 생성하는 데 초점을 맞춘 반면, Molmo는 "이 이미지에서 고양이가 어디 있나요?"라는 질문에 **이미지 내 정확한 좌표**로 응답할 수 있다. 인간 주석자가 음성으로 이미지를 설명하면서 동시에 마우스로 객체를 가리키는 독특한 방식으로 수집한 PixMo 데이터셋으로 학습하여, 시각적 질의에 대한 응답으로 이미지 내 특정 위치를 좌표로 지시하는 포인팅(pointing) 능력을 갖추었다.

모든 모델 가중치, 학습 코드, 데이터셋을 공개하는 **완전 개방형(fully open) 연구**를 지향하며, 7B부터 72B까지 다양한 크기로 제공된다.

논문: [Molmo and PixMo: Open Weights and Open Data for State-of-the-Art Multimodal Models](https://arxiv.org/abs/2409.17146)

## 아키텍처 상세

### 전체 구조

Molmo는 표준적인 VLM 구조를 기반으로 한다:

1. **비전 인코더**: OpenAI CLIP ViT-L/14@336 (고정)
2. **MLP 프로젝터**: 2-layer MLP (비전 → 언어 공간 매핑)
3. **언어 모델**: Qwen2-7B / 72B 또는 OLMo-7B

아키텍처 자체는 LLaVA와 유사한 간결한 구조이며, **데이터(PixMo)가 핵심 차별점**이다.

### PixMo 데이터셋

PixMo는 두 가지 유형의 데이터로 구성된다:

**1. PixMo-Cap (음성 캡셔닝, 70만 이미지)**
인간 주석자가 이미지를 보면서 **음성으로** 설명한다. 음성 기반 주석의 장점:
- 타이핑보다 자연스럽고 상세한 설명
- 실시간 관찰 기반의 풍부한 디테일
- 주석 비용 절감 (음성이 타이핑보다 빠름)

**2. PixMo-Point (포인팅, 170만 이미지)**
주석자가 음성으로 설명하면서 동시에 마우스로 해당 객체를 **클릭**한다. 이 클릭 좌표가 포인팅 데이터로 수집된다.

### 포인팅 좌표 표현

Molmo의 포인팅 출력은 **텍스트 형식**으로 표현된다:

```
Q: Where is the cat in this image?
A: The cat is sitting on the windowsill <point x="0.65" y="0.42"/>
```

좌표는 이미지 크기에 대한 상대 좌표(0~1)로 표현되며, 특수 토큰 없이 일반 텍스트 시퀀스로 생성된다. 이는 기존 토크나이저를 수정하지 않아도 되는 실용적 장점이 있다.

| 구성 요소 | Molmo-72B | Molmo-7B |
|-----------|----------|---------|
| 비전 인코더 | CLIP ViT-L/14 | CLIP ViT-L/14 |
| LLM | Qwen2-72B | Qwen2-7B |
| 프로젝터 | 2-layer MLP | 2-layer MLP |
| 컨텍스트 | 4096 | 4096 |
| 포인팅 | 지원 | 지원 |

## 핵심 혁신

### 1. 시각적 포인팅(Visual Pointing)

"이미지 내 어디에 있는가?"에 대한 좌표 응답 능력은 단순한 텍스트 응답을 넘어선 것이다. 이 능력은:
- **로봇 조작**: "빨간 컵을 집어" → 빨간 컵의 좌표 출력
- **UI 자동화**: "로그인 버튼을 클릭해" → 버튼 좌표 지시
- **접근성**: 시각 장애인을 위한 객체 위치 안내
- **의료 영상**: "종양이 어디 있나요?" → 위치 지시

### 2. 음성 기반 데이터 수집

음성으로 이미지를 설명하게 하는 독특한 데이터 수집 방식은 기존 텍스트 기반 주석보다 더 자연스럽고 상세한 설명을 유도한다. 특히 공간 관계, 시각적 속성 등 타이핑으로는 번거로운 디테일이 음성으로는 쉽게 설명된다.

### 3. 완전 개방형 연구

모델 가중치뿐 아니라 학습 데이터(PixMo), 학습 코드까지 모두 공개하는 것은 재현성과 투명성 면에서 중요한 기여이다. 대부분의 VLM이 학습 데이터를 공개하지 않는 것과 대조적이다.

## 벤치마크/성능

| 벤치마크 | Molmo-72B | GPT-4V | Qwen2-VL-72B | InternVL2-76B |
|----------|----------|--------|-------------|-------------|
| 일반 VQA | 경쟁적 | 높음 | 높음 | 높음 |
| 포인팅 정확도 | **SOTA** | 미지원 | 제한적 | 미지원 |
| 캡셔닝 품질 | 높음 | 높음 | 높음 | 높음 |

Molmo는 특히 포인팅 정확도에서 다른 모델들을 크게 앞서며, 일반적인 VQA와 캡셔닝에서도 경쟁력 있는 성능을 보인다.

## 관련 모델 비교

| 특성 | Molmo | LLaVA-OV | Qwen2-VL | CogAgent |
|------|-------|---------|---------|----------|
| 포인팅 능력 | 강력 (PixMo) | 없음 | 제한적 | 있음 (UI) |
| 데이터 공개 | 전체 공개 | 부분 | 미공개 | 미공개 |
| 음성 캡셔닝 | 지원 (PixMo-Cap) | 미지원 | 미지원 | 미지원 |
| 모델 공개 | 전체 (가중치+코드) | 전체 | 가중치만 | 가중치만 |

## 학습 상세

**데이터 구성:**
- PixMo-Cap: 70만 이미지의 음성 캡셔닝 데이터
- PixMo-Point: 170만 이미지의 포인팅 데이터
- 기존 VQA 데이터: ShareGPT4V 등 보조 데이터 혼합

**학습 방법:**
- CLIP 비전 인코더: 고정
- MLP 프로젝터 + LLM: 파인튜닝
- 포인팅과 캡셔닝을 혼합한 멀티태스크 학습

**모델 크기 변형:**
- Molmo-7B-D: Qwen2-7B 기반 (밀집)
- Molmo-7B-O: OLMo-7B 기반 (완전 오픈)
- MolmoE-1B: 1B MoE (엣지 배포용)
- Molmo-72B: Qwen2-72B 기반 (최고 성능)

## 실무 활용

```python
from transformers import AutoModelForCausalLM, AutoProcessor
import torch

model = AutoModelForCausalLM.from_pretrained(
    "allenai/Molmo-7B-D-0924",
    torch_dtype=torch.bfloat16,
    trust_remote_code=True
).to("cuda")
processor = AutoProcessor.from_pretrained(
    "allenai/Molmo-7B-D-0924", trust_remote_code=True
)

# 포인팅 질의
image = Image.open("room.jpg")
inputs = processor(
    text="Point to the lamp in this image.",
    images=[image], return_tensors="pt"
).to("cuda")
output = model.generate(**inputs, max_new_tokens=200)
# 출력: "The lamp is on the left side of the desk <point x="0.23" y="0.35"/>"
```

## 한계 및 전망

### 한계

1. **포인팅 정밀도**: 복잡한 장면에서 작은 객체나 겹치는 객체의 포인팅 정확도가 떨어질 수 있다
2. **단일 이미지**: 다중 이미지나 비디오에서의 포인팅은 미지원
3. **생성 불가**: 이미지 이해/포인팅에 특화, 이미지 생성 능력 부재

### 전망

Molmo의 포인팅 능력은 AI 에이전트(computer use, 로봇 조작) 분야에서 핵심 기술이 될 수 있다. PixMo 데이터셋의 공개는 포인팅 연구의 접근성을 크게 높이며, 향후 3D 공간 포인팅, 비디오 내 시공간 포인팅 등으로 확장될 전망이다.

## 관련 문서

- [[llava|Visual Instruction Tuning]] — 영감
