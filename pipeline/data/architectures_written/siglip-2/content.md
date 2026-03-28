# SigLIP 2: 시그모이드 대조 학습 기반 시각-언어 모델

**Google** · **2025-02-01** · **Vision** · **오픈소스**

## 개요

SigLIP 2는 2025년 2월 Google DeepMind가 발표한 차세대 시그모이드 손실 기반 시각-언어 사전학습 모델이다. CLIP(OpenAI, 2021)이 소프트맥스 기반 InfoNCE 대조 손실로 이미지-텍스트 쌍을 정렬하는 것과 달리, SigLIP 2는 **시그모이드 이진 분류 손실**을 사용하여 각 이미지-텍스트 쌍을 독립적으로 매칭/비매칭 판별한다. 이 설계 선택은 배치 크기에 대한 의존성을 제거하고 분산 학습 효율을 크게 향상시킨다.

기존 SigLIP(2023)의 핵심 아이디어를 계승하면서, SigLIP 2는 다국어 확장(109개 언어), 학습 레시피 개선(MIM 보조 손실), NaViT 스타일 가변 해상도 처리를 통합하였다. PaLI-3, Gemma 등 Google의 멀티모달 LLM에서 비전 인코더로 채택되어, 시각적 질의응답, 문서 이해, OCR 등 다운스트림 태스크 전반에서 CLIP·OpenCLIP 대비 일관되게 우수한 성능을 보인다.

![SigLIP 2 아키텍처 - 다국어 확장, MIM 보조 손실, NaViT 가변 해상도를 통합한 시각-언어 모델 구조](figures/architecture.svg)

*Figure 1: SigLIP 2 아키텍처 - SigLIP의 시그모이드 대조 손실을 계승하면서 109개 언어 지원, MIM 보조 학습, NaViT 스타일 가변 해상도 처리를 통합한 차세대 비전 인코더이다.*

## 아키텍처 상세

### 시그모이드 대조 손실

CLIP의 소프트맥스 InfoNCE 손실은 배치 내 모든 이미지-텍스트 쌍의 유사도를 계산하고 행/열별 소프트맥스 정규화를 수행한다. 이는 큰 배치가 더 많은 네거티브 샘플을 제공하여 성능에 직결되므로, 매우 큰 배치 크기(32K~65K)가 필요하다.

SigLIP 2의 시그모이드 손실은 각 쌍을 독립적으로 처리한다:

$$\mathcal{L} = -\frac{1}{B^2} \sum_{i,j} \left[ y_{ij} \log \sigma(z_{ij}) + (1-y_{ij}) \log (1-\sigma(z_{ij})) \right]$$

여기서 $z_{ij} = t \cdot (\mathbf{v}_i \cdot \mathbf{l}_j) + b$이며, $y_{ij} = \mathbb{1}[i=j]$는 매칭 레이블, $t$와 $b$는 학습 가능한 온도와 바이어스이다. 이 방식은 소프트맥스 정규화가 없으므로 배치 크기에 대한 민감도가 크게 감소하고, 분산 학습에서 GPU 간 통신 오버헤드도 줄어든다.

### NaViT 기반 가변 해상도 패치 처리

SigLIP 2는 NaViT(Native Resolution ViT) 스타일의 가변 해상도 처리를 채택한다:

1. 이미지를 고정 크기로 리사이즈하지 않고, 원본 종횡비를 유지한 채 14×14 패치로 분할
2. **시퀀스 패킹**: 서로 다른 해상도의 이미지를 하나의 배치에 효율적으로 묶어 GPU 활용률 극대화
3. 2D 학습 위치 임베딩은 학습 시 보지 못한 해상도에도 보간으로 일반화

이를 통해 정사각형이 아닌 문서 이미지, 파노라마 사진 등 다양한 종횡비의 이미지를 정보 손실 없이 처리할 수 있다.

### SO400M 아키텍처

SigLIP 2는 SO400M(Shape Optimized 400M) 아키텍처를 사용한다. 전통적인 ViT-L(304M)이나 ViT-H(632M) 대신, 레이어 수(27)와 히든 차원(1152), 헤드 수(16)의 비율을 최적화하여 동일 파라미터 수(400M)에서 더 나은 성능-효율 트레이드오프를 달성한다.

### MIM 보조 손실

대조 학습만으로는 이미지의 지역적(local) 세부 패턴을 충분히 학습하지 못하는 한계가 있다. SigLIP 2는 마스킹 이미지 모델링(MIM) 보조 손실을 추가하여, 입력 패치의 약 75%를 마스킹하고 인코더 출력에서 마스킹된 패치를 복원하도록 학습한다:

$$\mathcal{L}_\text{total} = \mathcal{L}_\text{sigmoid} + \alpha \cdot \mathcal{L}_\text{MIM}$$

이 조합은 전역적 시각-언어 정렬(대조 학습)과 지역적 시각 패턴 학습(MIM)을 동시에 달성한다.

다음 그림은 SigLIP 2의 4가지 핵심 혁신 - 시그모이드 손실, NaViT 가변 해상도, MIM 보조 손실, SO400M 아키텍처 - 을 상세히 보여준다.

![SigLIP 2의 핵심 혁신 상세도](figures/detail.png)
*Figure 2: SigLIP 2 핵심 혁신 - Sigmoid vs Softmax 손실 비교(좌상), NaViT 가변 해상도 패치 처리(상단 중앙), 다국어 및 다운스트림 성능(우상), MIM 보조 손실(하단 중앙), SO400M 최적화 아키텍처(우하). (Source: Tschannen et al., 2025)*

## 핵심 혁신

1. **배치 크기 독립성**: 시그모이드 손실로 배치 크기에 대한 민감도를 제거하여, 소규모 배치에서도 안정적 학습이 가능하다.
2. **다국어 지원(109개 언어)**: SentencePiece(250K vocab) 텍스트 인코더로 109개 언어를 지원하며, 한국어를 포함한 비영어권 이미지-텍스트 매칭에서도 강력한 성능을 보인다.
3. **대조 학습 + MIM 결합**: 전역적 의미 정렬과 지역적 패턴 학습을 통합하여, 특히 세밀한 시각 이해(fine-grained recognition)에서 2-3% 정확도 향상을 달성하였다.

## 벤치마크/성능

| 모델 | ImageNet 제로샷 | COCO 검색 (R@1) | 다국어 검색 | 문서 이해 |
|------|---------------|-----------------|-----------|----------|
| SigLIP 2 SO400M | 84.1% | 69.7 | 우수 | 우수 |
| SigLIP SO400M | 81.4% | 66.3 | 양호 | 양호 |
| CLIP ViT-L/14 | 75.5% | 58.4 | 제한적 | 제한적 |
| OpenCLIP ViT-H/14 | 78.0% | 63.2 | 양호 | 양호 |

SigLIP 2는 제로샷 분류, 이미지-텍스트 검색, 다국어 처리, 문서 이해 등 전 영역에서 기존 모델들을 일관되게 능가한다.

## 관련 모델 비교

| 모델 | 손실 함수 | 배치 의존 | 다국어 | 해상도 | MIM |
|------|----------|---------|--------|--------|-----|
| CLIP | 소프트맥스 InfoNCE | 높음 | 영어 중심 | 고정 | 없음 |
| SigLIP | 시그모이드 | 낮음 | 영어 중심 | 고정 | 없음 |
| SigLIP 2 | 시그모이드 | 낮음 | 109개 | 가변(NaViT) | 있음 |
| EVA-CLIP | 소프트맥스 | 높음 | 영어 중심 | 고정 | 있음 |

## 학습 상세

- **데이터셋**: WebLI (약 100억 이미지-텍스트 쌍, 109개 언어)
- **다단계 학습**:
  1. 저해상도(224px) 대규모 사전학습
  2. 고해상도(384px) 미세조정
  3. NaViT 패킹으로 가변 해상도 혼합 학습
- **텍스트 인코더**: SentencePiece 250K vocab
- **GPU**: Google TPU v4/v5e 클러스터
- **데이터 큐레이션**: De-duplication + 품질 필터링 강화

## 실무 활용

```python
from transformers import AutoProcessor, AutoModel
import torch

# SigLIP 2 모델 로드
processor = AutoProcessor.from_pretrained("google/siglip2-so400m-patch14-384")
model = AutoModel.from_pretrained("google/siglip2-so400m-patch14-384")

# 제로샷 이미지 분류
texts = ["a photo of a cat", "a photo of a dog", "고양이 사진"]
inputs = processor(text=texts, images=image, return_tensors="pt", padding=True)

with torch.no_grad():
    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image  # 이미지-텍스트 유사도
    probs = torch.sigmoid(logits_per_image)  # 시그모이드로 확률 변환
```

SigLIP 2는 멀티모달 LLM의 비전 인코더로서 가장 많이 활용되며, Gemma, PaLI 등의 시각 백본으로 채택되어 있다. 다국어 지원 덕분에 한국어 이미지-텍스트 매칭에서도 별도 학습 없이 우수한 성능을 보인다.

## 한계 및 전망

1. **생성 능력 부재**: CLIP과 마찬가지로 판별 모델이므로 이미지 생성이 불가능하다.
2. **세밀한 공간 이해**: 전역적 이미지-텍스트 정렬은 강력하지만, "왼쪽 위의 빨간 공" 같은 세밀한 공간적 관계 이해에는 한계가 있다.
3. **폐쇄형 데이터**: WebLI 데이터셋이 비공개이므로 재현이 어렵다.

SigLIP 2는 시각-언어 사전학습의 최전선에 서 있으며, 다국어·가변 해상도·보조 손실이라는 세 축의 혁신으로 CLIP 패러다임을 한 단계 진화시켰다.

## 관련 문서

- [[siglip|SigLIP]] - 발전 기반
