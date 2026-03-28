# Swin Transformer: 계층적 비전 트랜스포머

**Microsoft** · **2021-03-01** · **Vision** · **오픈소스**

## 개요

Swin Transformer는 2021년 Microsoft Research Asia의 Ze Liu 등이 발표한 계층적(hierarchical) 비전 트랜스포머로, 컴퓨터 비전의 범용 백본으로 설계된 모델이다. ViT가 비전에 트랜스포머를 성공적으로 도입했지만, 전역 셀프 어텐션의 $O(N^2)$ 복잡도와 단일 해상도 특징 맵이라는 한계가 있었다. Swin Transformer는 **이동 윈도우(Shifted Window)** 기반 지역 어텐션과 **계층적 특징 맵** 구조로 이 두 문제를 동시에 해결하여, 분류·탐지·세그멘테이션 등 광범위한 비전 태스크에서 SOTA를 달성하였다.

Swin Transformer는 ICCV 2021 Best Paper Award를 수상하였으며, 2024년 기준 10,000회 이상의 인용으로 비전 트랜스포머 분야에서 가장 영향력 있는 연구 중 하나이다.

![Swin Transformer 아키텍처 - 이동 윈도우 기반 지역 어텐션과 계층적 특징 맵 구조](figures/architecture.svg)

*Figure 1: Swin Transformer 아키텍처 - 이동 윈도우(Shifted Window)로 선형 복잡도의 지역 어텐션을 수행하고, 패치 병합으로 계층적 특징 맵을 생성하여 분류, 탐지, 세그멘테이션을 통합 지원한다.*

## 아키텍처 상세

아래 그림은 Swin Transformer와 기존 ViT의 구조적 차이를 보여준다. Swin Transformer는 계층적 특징 맵을 생성하여 분류뿐 아니라 탐지·세그멘테이션에도 활용 가능한 반면, ViT는 단일 해상도의 특징 맵만 생성한다.

![Swin Transformer와 ViT의 구조 비교 - 계층적 특징 맵 vs 단일 해상도](figures/fig_1.png)
*Figure 1: Swin Transformer vs ViT 구조 비교 - (a) Swin Transformer는 패치 병합으로 계층적 특징 맵(4x, 8x, 16x)을 생성하며 선형 복잡도를 가진다. (b) ViT는 전역 어텐션으로 단일 저해상도(16x) 특징 맵만 생성하며 이차 복잡도를 가진다. (Source: Liu et al., 2021)*

### 계층적 구조(Hierarchical Structure)

Swin Transformer는 CNN과 유사한 4단계 계층적 구조를 갖는다. 각 단계에서 특징 맵의 공간 해상도는 줄어들고 채널 수는 증가한다:

| 단계 | 해상도 (224 입력) | 채널 수 | 트랜스포머 블록 수 |
|------|-----------------|--------|-----------------|
| Stage 1 | 56×56 | C (96) | 2 |
| Stage 2 | 28×28 | 2C (192) | 2 |
| Stage 3 | 14×14 | 4C (384) | 6 |
| Stage 4 | 7×7 | 8C (768) | 2 |

단계 간에는 **패치 병합(Patch Merging)** 레이어가 인접한 2×2 패치를 결합하여 공간 해상도를 절반으로 줄이고 채널 수를 2배로 늘린다. 이 구조는 CNN의 풀링과 유사한 역할을 하며, FPN(Feature Pyramid Network)과 자연스럽게 호환된다.

### 윈도우 기반 어텐션(Window-based Attention)

전역 셀프 어텐션 대신, 이미지를 $M \times M$ (기본 7×7) 크기의 윈도우로 분할하고 각 윈도우 내부에서만 어텐션을 계산한다:

$$\text{W-MSA}: \Omega(\text{global}) = O(N^2) \rightarrow \Omega(\text{window}) = O(M^2 \cdot N)$$

$M$은 윈도우 크기(7)로 고정이고 $N$은 전체 토큰 수이므로, 연산 복잡도가 $N$에 대해 **선형**이 된다.

### 이동 윈도우(Shifted Window) 어텐션

윈도우 내부 어텐션만으로는 인접 윈도우 간 정보 교류가 불가능하다. 아래 그림은 이동 윈도우 메커니즘의 핵심 아이디어를 시각적으로 보여준다.

![이동 윈도우 방식의 셀프 어텐션 계산 - Layer l과 l+1에서의 윈도우 위치 변화](figures/fig_2.png)
*Figure 2: 이동 윈도우(Shifted Window) 어텐션 - Layer l에서 표준 윈도우 분할로 어텐션을 계산한 후, Layer l+1에서 윈도우를 이동시켜 이전 윈도우 경계를 넘는 연결을 생성한다. (Source: Liu et al., 2021)*

Swin Transformer는 연속된 두 트랜스포머 블록에서 **윈도우 위치를 번갈아 이동**시켜 이 문제를 해결한다:

- **홀수 블록 (W-MSA)**: 표준 윈도우 분할 → 윈도우 내 어텐션
- **짝수 블록 (SW-MSA)**: 윈도우를 $(M/2, M/2)$만큼 이동 → 이동된 윈도우 내 어텐션

$$\hat{z}^l = \text{W-MSA}(\text{LN}(z^{l-1})) + z^{l-1}$$
$$z^l = \text{FFN}(\text{LN}(\hat{z}^l)) + \hat{z}^l$$
$$\hat{z}^{l+1} = \text{SW-MSA}(\text{LN}(z^l)) + z^l$$
$$z^{l+1} = \text{FFN}(\text{LN}(\hat{z}^{l+1})) + \hat{z}^{l+1}$$

이동 시 가장자리에서 발생하는 불완전한 윈도우는 **순환 이동(cyclic shift) + 마스킹**으로 효율적으로 처리한다. 다음 그림은 이 순환 이동 기법의 배치 계산 방식을 보여준다.

![이동 윈도우에서의 효율적 배치 계산 - 순환 이동과 마스킹 방식](figures/fig_4.png)
*Figure 3: 순환 이동(Cyclic Shift) 기반 효율적 배치 계산 - 윈도우 분할 후 순환 이동을 적용하고, 마스킹된 MSA를 수행한 뒤 역순환 이동으로 원래 위치를 복원한다. 이를 통해 추가 연산 없이 이동 윈도우를 효율적으로 구현한다. (Source: Liu et al., 2021)*

### 상대적 위치 편향(Relative Position Bias)

ViT의 절대적 위치 임베딩 대신, 각 어텐션 헤드에 상대적 위치 편향을 추가한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d}} + B\right)V$$

여기서 $B$는 학습 가능한 상대적 위치 편향 행렬이다. 이 방식은 다양한 입력 크기에 대한 유연성을 제공한다.

다음 그림은 Swin Transformer(Swin-T)의 전체 아키텍처와 트랜스포머 블록 내부 구조를 상세히 보여준다.

![Swin-T 전체 아키텍처와 연속된 두 트랜스포머 블록의 내부 구조](figures/fig_3.png)
*Figure 4: Swin-T 아키텍처 상세 - (a) 4단계 계층적 구조에서 패치 병합과 트랜스포머 블록의 배치, (b) W-MSA와 SW-MSA를 교대로 적용하는 연속된 두 트랜스포머 블록의 내부 구조. (Source: Liu et al., 2021)*

## 핵심 혁신

1. **선형 복잡도 어텐션**: 윈도우 어텐션으로 $O(N)$ 복잡도를 달성하여, 고해상도 이미지에서도 효율적으로 동작한다.
2. **계층적 멀티스케일 특징**: FPN과 호환되는 피라미드 특징을 생성하여, 객체 탐지와 세그멘테이션에 직접 활용 가능하다.
3. **범용 백본**: 분류, 탐지, 세그멘테이션 등 다양한 비전 태스크의 백본으로 교체 가능하다.

## 벤치마크/성능

| 모델 | ImageNet top-1 | COCO mAP (Mask R-CNN) | ADE20K mIoU (UperNet) | 파라미터 |
|------|---------------|----------------------|----------------------|---------|
| Swin-T | 81.3% | 46.0 | 44.5 | 29M |
| Swin-S | 83.0% | 48.5 | 47.6 | 50M |
| Swin-B | 83.5% | 48.5 | 48.1 | 88M |
| Swin-L | 87.3% | 51.9 | 53.5 | 197M |
| ViT-B/16 | 77.9% | - | - | 86M |
| DeiT-B | 81.8% | - | - | 86M |

Swin Transformer는 ImageNet 분류에서 ViT/DeiT를 능가하며, COCO 탐지와 ADE20K 세그멘테이션에서도 당시 SOTA를 달성하였다.

## 관련 모델 비교

| 모델 | 어텐션 | 복잡도 | 계층적 | 멀티스케일 |
|------|--------|--------|--------|----------|
| ViT | 전역 | $O(N^2)$ | 없음 | 단일 |
| Swin | 이동 윈도우 | $O(N)$ | 4단계 | 피라미드 |
| PVT | 공간 축소 | $O(N^{1.5})$ | 4단계 | 피라미드 |
| Twins | 지역+전역 교대 | $O(N)$ | 4단계 | 피라미드 |

## 학습 상세

- **ImageNet-1K 학습**: 300 에폭, AdamW, cosine 스케줄, 배치 크기 1024
- **ImageNet-22K 사전학습**: 90 에폭 후 ImageNet-1K 파인튜닝 30 에폭
- **데이터 증강**: Rand-Augment, Mixup(α=0.8), CutMix(α=1.0), Label Smoothing(0.1)
- **정규화**: Stochastic depth(최대 0.5), Weight decay 0.05
- **GPU**: 8×V100 또는 A100

```python
import torch
from transformers import SwinForImageClassification, AutoImageProcessor

# Swin-Base 모델 로드
processor = AutoImageProcessor.from_pretrained("microsoft/swin-base-patch4-window7-224")
model = SwinForImageClassification.from_pretrained("microsoft/swin-base-patch4-window7-224")

# 이미지 분류
inputs = processor(images=image, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)
    predicted_class = outputs.logits.argmax(-1).item()
```

## 실무 활용

Swin Transformer는 비전 태스크의 범용 백본으로 가장 널리 채택된 모델 중 하나이다:

- **객체 탐지**: Mask R-CNN, Cascade R-CNN, DINO-DETR 등의 백본으로 사용
- **세그멘테이션**: UperNet, Mask2Former 등의 백본으로 사용
- **비디오 이해**: Video Swin Transformer로 확장되어 비디오 분류/액션 인식에 활용
- **멀티모달**: Grounding DINO의 이미지 인코더로 채택

`timm` 라이브러리와 `transformers` 라이브러리 모두에서 다양한 Swin 변형이 제공되어, 실무 적용이 용이하다.

## 한계 및 전망

1. **윈도우 경계 아티팩트**: 이동 윈도우로 완화되지만, 윈도우 경계에서의 불연속성이 완전히 해결되지는 않는다.
2. **구현 복잡성**: 이동 윈도우, 순환 이동, 마스킹 등의 구현이 ViT 대비 복잡하다.
3. **자기지도 학습 호환성**: MAE 등 마스킹 기반 자기지도 학습과의 결합이 ViT보다 까다롭다(SimMIM이 이를 해결).

Swin Transformer V2(2022)에서 스케일링과 해상도 전이 기법이 개선되었으며, 2025년 현재에도 실무에서 가장 많이 사용되는 비전 백본 중 하나로 자리잡고 있다.

## 관련 문서

- [[vit|An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale]] - 발전 기반
