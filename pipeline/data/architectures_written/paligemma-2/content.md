# PaliGemma 2: SigLIP과 Gemma 2의 결합으로 탄생한 범용 시각-언어 모델

## 개요

PaliGemma 2는 2024년 12월 Google이 발표한 멀티모달 모델로, **SigLIP-SO400M 비전 인코더**와 **Gemma 2 언어 모델**을 결합한 구조이다. PaliGemma의 후속작으로, Gemma 2의 향상된 언어 모델 능력과 SigLIP의 강력한 시각 인코더를 결합하여 이미지 이해, 문서 분석, OCR, 시각적 질의응답 등에서 전작 대비 크게 향상된 성능을 달성한다.

PaliGemma 2의 설계 철학은 **범용 파인튜닝 기반 모델(fine-tuning base model)**이다. 사전학습된 모델을 그대로 사용하기보다는, 사용자가 특정 태스크에 맞게 파인튜닝하여 최적의 성능을 달성하도록 설계되었다. 3B, 10B, 28B 세 가지 크기와 224, 448, 896px 세 가지 해상도를 지원하여, 다양한 연구 및 산업 요구에 맞는 최적의 조합을 선택할 수 있다. 모든 모델 가중치가 공개되어 학술 연구와 상용 파인튜닝에 널리 활용된다.

논문: [PaliGemma 2: A Family of Versatile VLMs for Transfer](https://arxiv.org/abs/2412.03555)

## 아키텍처 상세

### 전체 구조

PaliGemma 2는 간결한 2-컴포넌트 구조이다:

1. **비전 인코더**: SigLIP-SO400M/14 (400M params, 고정)
2. **언어 모델**: Gemma 2 (3B / 10B / 28B)
3. **연결**: 선형 프로젝터 (비전 토큰 → 언어 임베딩 공간)

### 이미지 처리 파이프라인

SigLIP이 이미지를 14×14 패치로 분할하고, 각 패치에서 시각 토큰을 추출한다:

| 해상도 | 패치 그리드 | 시각 토큰 수 | 적합한 태스크 |
|--------|-----------|------------|-------------|
| 224px | 16×16 | 256 | 분류, 간단한 VQA |
| 448px | 32×32 | 1024 | 일반 VQA, 캡셔닝 |
| 896px | 64×64 | 4096 | OCR, 문서, 세밀한 분석 |

시각 토큰은 선형 프로젝터를 통해 Gemma 2의 임베딩 공간으로 매핑된 후, 텍스트 토큰 앞에 prefix로 추가된다:

$$[\text{visual tokens}] \oplus [\text{text tokens}] \rightarrow \text{Gemma 2} \rightarrow \text{output}$$

### Gemma 2의 아키텍처적 장점

Gemma 2는 두 가지 핵심 기법으로 긴 시퀀스 처리 효율을 높인다:

1. **슬라이딩 윈도우 어텐션**: 짝수 레이어에서 로컬 윈도우 내 어텐션 적용
2. **글로벌-로컬 교차**: 홀수 레이어에서 전체 시퀀스 어텐션, 짝수 레이어에서 로컬 어텐션 교차

896px 해상도에서 4096개 시각 토큰이 생성되므로, 이 효율적인 어텐션 메커니즘이 특히 중요하다.

| 모델 변형 | 파라미터 | 히든 차원 | 레이어 수 | 헤드 수 |
|----------|---------|---------|---------|--------|
| PaliGemma2-3B | 3B | 2304 | 26 | 8 |
| PaliGemma2-10B | 10B | 3584 | 42 | 16 |
| PaliGemma2-28B | 28B | 4608 | 46 | 32 |

## 핵심 혁신

### 1. 파인튜닝 기반 설계 철학

대부분의 VLM이 제로샷/소수샷 성능을 강조하는 반면, PaliGemma 2는 **파인튜닝 후 성능**에 초점을 맞춘다. 사전학습 모델은 범용적인 시각-언어 표현을 학습하고, 사용자가 특정 태스크(의료 영상, 위성 이미지, 산업 검사 등)에 맞게 파인튜닝하여 최적의 성능을 달성한다.

### 2. 다양한 크기-해상도 조합

3가지 모델 크기 × 3가지 해상도 = 9가지 조합을 제공하여, 배포 환경(엣지 vs 클라우드)과 태스크 특성(분류 vs OCR)에 최적화된 선택이 가능하다.

### 3. SigLIP + Gemma 2 시너지

SigLIP의 효율적인 시그모이드 손실과 Gemma 2의 효율적인 어텐션 메커니즘이 결합되어, 고해상도 이미지를 처리하면서도 합리적인 추론 비용을 유지한다.

## 벤치마크/성능

파인튜닝 후 성능 (태스크별):

| 태스크 | PG2-28B-896 | PG2-10B-448 | PG1-3B-224 |
|--------|-----------|-----------|-----------|
| COCO Cap (CIDEr) | **152.8** | 148.3 | 140.1 |
| TextVQA | **85.1** | 80.4 | 72.3 |
| DocVQA | **89.3** | 83.7 | 70.2 |
| AI2D | **82.1** | 78.5 | 72.8 |
| 공간 추론 | **78.2** | 73.4 | 65.1 |

## 관련 모델 비교

| 특성 | PaliGemma 2 | LLaVA-OV | Qwen2-VL | InternVL 2 |
|------|-----------|---------|---------|-----------|
| 설계 목적 | 파인튜닝 기반 | 범용 대화 | 범용 대화 | 범용 대화 |
| 비전 인코더 | SigLIP-400M | SigLIP-400M | ViT-675M | InternViT-6B |
| 해상도 옵션 | 224/448/896 | AnyRes | 동적 | 동적 |
| 모델 크기 | 3B/10B/28B | 0.5B~72B | 2B~72B | 2B~76B |
| 오픈 가중치 | 공개 | 공개 | 공개 | 공개 |

## 학습 상세

2단계 학습:

**Stage 1: 비전-언어 정렬**
- SigLIP 비전 인코더와 Gemma 2 LLM을 선형 프로젝터로 연결
- 대규모 이미지-텍스트 데이터로 정렬 학습
- TPU v5 클러스터 사용

**Stage 2: 멀티태스크 파인튜닝**
- 문서, OCR, 과학 이미지, 캡셔닝, VQA 등 다양한 태스크 혼합
- 고해상도(448, 896) 이미지 포함

## 실무 활용

```python
from transformers import PaliGemmaProcessor, PaliGemmaForConditionalGeneration
import torch

model = PaliGemmaForConditionalGeneration.from_pretrained(
    "google/paligemma2-10b-ft-docci-448",
    torch_dtype=torch.bfloat16
).to("cuda")
processor = PaliGemmaProcessor.from_pretrained(
    "google/paligemma2-10b-ft-docci-448"
)

image = Image.open("document.png")
inputs = processor(text="Describe this image in detail.", images=image, return_tensors="pt").to("cuda")
output = model.generate(**inputs, max_new_tokens=256)
print(processor.decode(output[0], skip_special_tokens=True))
```

## 한계 및 전망

### 한계

1. **파인튜닝 필요**: 제로샷 성능이 대화형 VLM 대비 약하며, 최적 성능을 위해 태스크별 파인튜닝이 필수적이다
2. **비디오 미지원**: 이미지 이해에 특화, 비디오 처리 능력 부재
3. **대화형 AI 한계**: 멀티턴 대화보다는 단일 질의-응답에 최적화

### 전망

PaliGemma 2의 파인튜닝 기반 접근은 특정 도메인(의료, 산업, 과학)에서 최고 수준의 성능을 달성하는 데 유리하며, 범용 대화형 VLM과 상호 보완적인 역할을 한다. Google의 Gemma 생태계가 확장되면서 더 큰 LLM과의 결합이 기대된다.

PaliGemma 2의 파인튜닝 중심 설계는 특히 **특수 도메인**에서 큰 가치를 발휘한다. 의료 영상에서 병변을 탐지하거나, 위성 이미지에서 건물을 분류하거나, 제조 라인에서 불량품을 검출하는 등의 태스크에서, 범용 대화형 VLM보다 파인튜닝된 PaliGemma 2가 더 높은 정확도를 달성할 수 있다. 9가지 크기-해상도 조합은 배포 환경의 제약(GPU 메모리, 처리 속도)과 태스크 요구(OCR 정밀도, 분류 정확도) 사이의 최적 균형을 찾는 데 유연성을 제공한다. Google의 TPU 생태계와의 긴밀한 통합도 실무 배포에서 중요한 이점이며, JAX/Flax 기반 학습 파이프라인이 공식 지원된다.

## 관련 문서

- [[gemma|Gemma: Open Models Based on Gemini Research and Technology]] — 발전 기반
- [[siglip|SigLIP]] — 사용 기법
