<!-- infographic-hero -->
![ViT 핵심 요약](figures/infographic.svg)

*Figure: ViT 한 장 요약 인포그래픽*

# ViT: 비전 트랜스포머의 시작

**Google Brain** · **2020-10-22** · **Vision** · **오픈소스**

## 개요

ViT(Vision Transformer)는 2020년 Google Brain의 Alexey Dosovitskiy 등이 발표한 최초의 순수 트랜스포머 기반 이미지 분류 모델이다. "An Image is Worth 16x16 Words"라는 제목이 핵심 아이디어를 함축하고 있듯이, 이미지를 고정 크기의 패치로 분할하여 NLP의 토큰처럼 취급한 뒤 표준 Transformer 인코더를 그대로 적용한다. CNN이 지배해 온 컴퓨터 비전 분야에 트랜스포머를 도입한 패러다임 전환적 연구로, 이후 DeiT, Swin Transformer, DINOv2, SAM 등 수많은 비전 모델의 기반이 되었다.

ViT 이전에도 이미지에 어텐션 메커니즘을 적용하려는 시도는 있었지만, 대부분 CNN과 결합하거나 지역적 어텐션에 한정되었다. ViT는 컨볼루션 연산 없이 순수 트랜스포머만으로 이미지를 처리하여, 대규모 데이터로 사전학습하면 CNN의 귀납적 편향(translation equivariance, locality) 없이도 동등하거나 우수한 성능을 달성할 수 있음을 입증하였다.

![ViT 아키텍처 - 이미지를 16x16 패치로 분할하여 표준 Transformer 인코더로 처리하는 구조](figures/architecture.svg)

*Figure 1: ViT 아키텍처 - 이미지를 고정 크기 패치로 분할하고 선형 임베딩과 위치 인코딩을 추가한 뒤 표준 Transformer 인코더에 입력하여, CNN 없이 순수 트랜스포머만으로 이미지를 분류한다.*

## 아키텍처 상세

다음 다이어그램은 ViT의 전체 구조를 보여준다.

![ViT 모델 개요 - 이미지를 패치로 분할, 선형 임베딩, 트랜스포머 인코더 처리](figures/fig_1.png)
*Figure 1: ViT 아키텍처 - 이미지를 고정 크기 패치로 분할하여 선형 임베딩한 뒤 위치 인코딩을 추가하고, 표준 Transformer 인코더로 처리한다. [CLS] 토큰의 출력으로 분류를 수행한다. (Source: Dosovitskiy et al., 2020)*

ViT의 아키텍처는 세 단계로 구성된다: 패치 임베딩, 트랜스포머 인코더, 분류 헤드이다.

### 패치 임베딩(Patch Embedding)

입력 이미지 $H \times W \times C$를 $P \times P$ 크기의 패치로 분할한다. 예를 들어, 224×224 이미지를 16×16 패치로 나누면 $N = (224/16)^2 = 196$개의 패치가 생성된다. 각 패치를 펼쳐(flatten) $P^2 \cdot C$ 차원의 벡터로 만든 뒤, 학습 가능한 선형 투영 $\mathbf{E} \in \mathbb{R}^{(P^2 \cdot C) \times D}$를 통해 D차원 임베딩으로 변환한다.

구체적으로, 16x16 패치 하나는 RGB 3채널 기준 $16 \times 16 \times 3 = 768$ 차원의 벡터가 되며, 이 벡터에 선형 투영을 적용하면 모델의 히든 차원 $D$로 매핑된다. 실제 구현에서는 커널 크기와 스트라이드가 모두 $P$인 합성곱(Conv2d)으로 패치 분할과 선형 투영을 단일 연산으로 수행한다. 이 방식은 flatten + linear와 수학적으로 동일하지만, GPU에서 더 효율적이다.

### CLS 토큰과 포지션 임베딩

시퀀스 앞에 학습 가능한 **[CLS] 토큰**을 추가하고, 각 위치에 학습 가능한 1D 포지션 임베딩을 더한다:

$$\mathbf{z}_0 = [\mathbf{x}_\text{cls}; \mathbf{x}_1\mathbf{E}; \mathbf{x}_2\mathbf{E}; \cdots; \mathbf{x}_N\mathbf{E}] + \mathbf{E}_\text{pos}$$

**[CLS] 토큰의 역할**: BERT에서 차용한 설계로, 이 특수 토큰은 이미지의 전체적인 표현을 집약하는 역할을 한다. 트랜스포머의 모든 레이어를 거치면서 셀프 어텐션을 통해 모든 패치 토큰의 정보를 수집하고, 최종 레이어에서 이 토큰의 출력 벡터가 분류 헤드에 입력된다. 다만 논문에서는 [CLS] 토큰 대신 모든 패치 토큰의 출력을 Global Average Pooling(GAP)으로 집약해도 유사한 성능을 달성함을 보였으며, DeiT 등 후속 모델에서는 GAP이 더 자주 사용되는 경향이 있다.

**포지션 임베딩**: ViT는 **학습 가능한(learnable) 1D 포지션 임베딩**을 사용한다. 이는 Transformer 원본 논문의 사인/코사인(sinusoidal) 고정 포지션 인코딩과 대조적인 선택이다. 논문의 ablation에서 흥미로운 결과가 보고되었다:

- 포지션 임베딩 없음 vs. 1D learnable vs. 2D learnable vs. 상대적 포지션 인코딩을 비교한 결과, **성능 차이가 미미**했다.
- 2D 포지션 임베딩이 직관적으로 이미지의 공간 구조를 더 잘 반영할 것 같지만, 실제로는 1D 임베딩만으로 충분했다.
- 이는 트랜스포머가 1D 포지션 정보만으로도 2D 공간 관계를 내부적으로 학습할 수 있음을 시사한다. 실제로 학습된 포지션 임베딩의 유사도를 시각화하면, 같은 행/열에 있는 패치들의 포지션 임베딩이 높은 유사도를 보여, 모델이 자연스럽게 2D 구조를 파악하고 있음을 확인할 수 있다.

### 트랜스포머 인코더

각 트랜스포머 블록은 Pre-Norm 구조로, LayerNorm → Multi-Head Self-Attention → 잔차 연결 → LayerNorm → FFN → 잔차 연결 순서로 처리된다:

$$\mathbf{z}'_l = \text{MSA}(\text{LN}(\mathbf{z}_{l-1})) + \mathbf{z}_{l-1}$$
$$\mathbf{z}_l = \text{FFN}(\text{LN}(\mathbf{z}'_l)) + \mathbf{z}'_l$$

FFN은 GELU 활성화 함수를 사용하며, 중간 차원은 히든 차원의 4배이다. 모든 패치 토큰 간에 전역 셀프 어텐션이 계산되므로, 이미지의 어떤 위치든 다른 모든 위치와 직접 상호작용할 수 있다.

### 모델 변형

| 모델 | 레이어 | 히든 차원 | 헤드 수 | 파라미터 | 패치 크기 |
|------|--------|----------|--------|---------|----------|
| ViT-B/16 | 12 | 768 | 12 | 86M | 16×16 |
| ViT-L/16 | 24 | 1024 | 16 | 307M | 16×16 |
| ViT-H/14 | 32 | 1280 | 16 | 632M | 14×14 |

패치 크기가 작을수록 시퀀스 길이가 길어져 표현력은 향상되지만, 어텐션의 $O(N^2)$ 복잡도로 인해 연산량이 급격히 증가한다.

## CNN과의 비교: 귀납적 편향의 부재

ViT를 이해하는 핵심은 CNN과의 차이, 특히 **귀납적 편향(inductive bias)**의 부재를 이해하는 것이다. CNN은 두 가지 강력한 귀납적 편향을 내장하고 있다:

1. **지역성(Locality)**: 합성곱 커널은 인접한 픽셀만을 참조하므로, 가까운 픽셀 간의 관계가 먼 픽셀 간의 관계보다 중요하다는 가정을 내포한다.
2. **이동 등변성(Translation Equivariance)**: 동일한 커널이 이미지의 모든 위치에 적용되므로, 물체가 이미지의 어디에 위치하든 동일한 특징을 추출한다.

ViT는 이러한 귀납적 편향을 의도적으로 배제한다. 셀프 어텐션은 첫 번째 레이어에서부터 이미지의 모든 패치 간 관계를 계산하므로, 지역성 가정이 없다. 포지션 임베딩은 학습을 통해 결정되므로, 이동 등변성도 내장되어 있지 않다.

이 차이는 두 가지 실질적 결과를 낳는다. 소규모 데이터(ImageNet-1K, 130만 장)에서는 CNN의 귀납적 편향이 유리하여 ResNet이 ViT를 능가한다. 그러나 대규모 데이터(JFT-300M, 3억 장)에서는 ViT가 데이터로부터 직접 이러한 패턴을 학습하고, 귀납적 편향의 제약 없이 더 유연한 표현을 학습할 수 있어 CNN을 능가한다. EfficientNet이 ImageNet에서 달성한 84.7%를 ViT-H/14가 88.6%로 크게 앞서는 것이 이를 증명한다.

## 핵심 혁신

ViT의 가장 중요한 기여는 **컨볼루션 없는 순수 트랜스포머가 비전 태스크에서 작동한다**는 것을 입증한 점이다.

1. **패치 토큰화**: 이미지를 패치 단위로 토큰화하는 간단하면서도 효과적인 방법론을 제시하였다. 이후 거의 모든 비전 트랜스포머가 이 방식을 채택한다.
2. **스케일링 법칙**: 모델 크기와 데이터 크기를 함께 키울수록 성능이 로그-선형으로 향상되는 스케일링 법칙이 비전에서도 성립함을 확인하였다.
3. **범용 비전 인코더**: ViT 아키텍처는 CLIP, LLaVA, BLIP-2 등 멀티모달 모델의 비전 백본으로 폭넓게 활용된다.

## 벤치마크/성능

| 모델 | ImageNet top-1 | 사전학습 데이터 |
|------|---------------|--------------|
| ViT-B/16 | 77.9% | ImageNet-1K only |
| ViT-L/16 | 85.3% | ImageNet-21K |
| ViT-H/14 | 88.6% | JFT-300M |
| ResNet-152x4 (BiT) | 87.5% | JFT-300M |

ImageNet-1K만으로 학습하면 CNN 대비 성능이 낮지만, JFT-300M(3억 장) 규모의 데이터로 사전학습하면 CNN을 능가한다. 이는 트랜스포머가 CNN의 귀납적 편향 없이 데이터에서 직접 패턴을 학습하기 때문이다. 아래 그래프는 이 관계를 명확히 보여준다.

![사전학습 데이터셋 크기에 따른 ImageNet 전이 성능](figures/fig_4.png)
*Figure 2: 데이터 규모와 성능 관계 - 소규모 데이터(ImageNet-1K)에서는 BiT(ResNet)가 우세하지만, 대규모 데이터(JFT-300M)로 갈수록 ViT가 ResNet을 능가한다. 큰 ViT 변형일수록 데이터 증가에 따른 성능 향상 폭이 크다. (Source: Dosovitskiy et al., 2020)*

Few-shot 학습에서도 동일한 패턴이 관찰된다.

![학습 샘플 수에 따른 ViT와 ResNet의 Few-shot 성능 비교](figures/fig_5.png)
*Figure 3: Few-shot 평가 - ResNet은 소규모 사전학습에서 더 우수하지만 빠르게 포화하는 반면, ViT는 사전학습 데이터가 증가할수록 계속 성능이 향상되어 궁극적으로 ResNet을 추월한다. (Source: Dosovitskiy et al., 2020)*

## 관련 모델 비교

| 모델 | 핵심 차이 | 패치 크기 | 어텐션 방식 |
|------|----------|----------|-----------|
| ViT | 전역 셀프 어텐션 | 16×16 / 14×14 | 전역 |
| DeiT | 증류 토큰으로 데이터 효율 향상 | 16×16 | 전역 |
| Swin | 이동 윈도우 지역 어텐션 | 4×4 → 계층적 | 지역 → 전역 |
| DINOv2 | 자기지도 학습으로 범용 특징 | 14×14 | 전역 |

동일한 계산 예산(compute budget)에서 ViT가 ResNet과 하이브리드 모델을 비교한 결과도 의미 있다.

![사전학습 계산량 대비 ViT, ResNet, 하이브리드 모델의 성능 비교](figures/fig_6.png)
*Figure 4: 계산 효율성 비교 - 동일 계산 예산에서 ViT가 ResNet보다 일반적으로 우수하며, 하이브리드 모델은 소규모에서 이점이 있지만 대규모에서는 격차가 사라진다. (Source: Dosovitskiy et al., 2020)*

ViT의 어텐션 메커니즘은 이미지의 의미적으로 중요한 영역에 자연스럽게 집중한다.

![ViT 출력 토큰에서 입력 공간으로의 어텐션 시각화](figures/fig_7.png)
*Figure 5: 어텐션 시각화 - ViT의 [CLS] 토큰이 입력 이미지의 의미적으로 관련 있는 영역(동물의 형태, 물체의 윤곽 등)에 집중하는 것을 보여준다. (Source: Dosovitskiy et al., 2020)*

## 학습 상세

### 데이터 요구사항과 전이 학습

ViT의 학습 전략에서 가장 중요한 요소는 **대규모 사전학습 데이터**이다. 논문에서 사용한 데이터셋은 세 가지이다:

| 데이터셋 | 규모 | 접근성 |
|---------|------|--------|
| ImageNet-1K | 130만 장 | 공개 |
| ImageNet-21K | 1,400만 장 | 공개 |
| JFT-300M | 3억 장 | Google 내부 |

JFT-300M은 Google 내부에서 자동 레이블링으로 구축한 3억 장 규모의 데이터셋으로, 약 18,000개 클래스를 포함한다. 이 데이터셋은 공개되지 않았기 때문에, ViT 논문의 핵심 결과를 외부에서 재현하기 어렵다는 비판이 있었다. 이후 DeiT(Data-efficient Image Transformers)가 ImageNet-1K만으로도 지식 증류와 강력한 데이터 증강을 통해 경쟁력 있는 성능을 달성하면서, 이 문제가 상당 부분 해소되었다.

사전학습 시 TPU v3-512를 활용하며, 학습률은 cosine 스케줄을 따른다. 파인튜닝 시에는 해상도를 224에서 384 또는 512로 높이며, 이때 포지션 임베딩을 **2D 바이큐빅 보간(bicubic interpolation)**하여 더 긴 시퀀스에 적응시킨다. 예를 들어, 224 해상도에서 196개 패치에 대해 학습된 포지션 임베딩을 384 해상도의 576개 패치에 맞게 보간한다. 이 기법은 간단하면서도 효과적이며, 이후 대부분의 비전 트랜스포머에서 표준 관행이 되었다.

```python
import torch
from transformers import ViTForImageClassification, ViTImageProcessor

# ViT-Base/16 모델 로드
processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")
model = ViTForImageClassification.from_pretrained("google/vit-base-patch16-224")

# 이미지 전처리 및 추론
inputs = processor(images=image, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)
    predicted_class = outputs.logits.argmax(-1).item()
```

## 실무 활용

ViT는 단독 이미지 분류기 외에도 다양한 역할로 활용된다:

- **멀티모달 비전 인코더**: CLIP, SigLIP 등 대조 학습 모델의 이미지 인코더로 사용되며, 이를 통해 LLaVA, BLIP-2, PaLI 등 비전-언어 모델의 시각 백본이 된다.
- **세그멘테이션 백본**: SAM(Segment Anything Model)의 이미지 인코더로 채택되어 범용 세그멘테이션을 가능하게 한다.
- **생성 모델 백본**: DiT(Diffusion Transformer)에서 U-Net을 대체하여 이미지 생성에도 활용된다.
- **자기지도 학습**: MAE, DINO 등의 사전학습 프레임워크와 결합하여 레이블 없이 강력한 시각 표현을 학습한다.

실무에서는 Hugging Face `transformers` 라이브러리를 통해 사전학습된 다양한 ViT 변형을 즉시 활용할 수 있으며, `timm` 라이브러리에서도 수백 가지 ViT 변형을 제공한다.

## 한계 및 과제

ViT의 주요 한계는 다음과 같다:

1. **대규모 데이터 의존성**: ViT의 가장 근본적인 한계이다. CNN의 귀납적 편향(지역성, 이동 등변성) 없이 순수하게 데이터에서 시각적 패턴을 학습해야 하므로, 소규모 데이터에서는 과적합이 발생하고 CNN 대비 성능이 크게 떨어진다. ImageNet-1K만으로 학습한 ViT-B/16은 77.9%에 불과하여, 같은 크기의 ResNet50(76.1%)과 비슷한 수준이다. 이 문제를 해결하기 위해 DeiT(2021)는 CNN 교사 모델의 지식 증류와 강력한 데이터 증강(RandAugment, Mixup, CutMix)을 결합하여, ImageNet-1K만으로 81.8%를 달성했다.
2. **연산 복잡도**: 전역 셀프 어텐션의 $O(N^2)$ 복잡도로 인해 고해상도 이미지 처리에 비용이 크다. 224px 이미지의 16x16 패치는 196개이므로 관리 가능하지만, 512px 이미지의 16x16 패치는 1,024개로 어텐션 행렬이 100만 원소를 넘는다. Swin Transformer가 윈도우 기반 지역 어텐션으로, FlashAttention이 하드웨어 최적화로 이 문제를 완화하였다.
3. **멀티스케일 특징 부재**: ViT는 모든 레이어에서 동일한 해상도의 특징 맵을 출력한다. CNN(ResNet 등)은 점진적으로 해상도를 줄이며 멀티스케일 피라미드를 구성하여 객체 탐지와 세그멘테이션에 적합한 반면, ViT의 단일 해상도 출력은 이러한 태스크에 직접 사용하기 어렵다. Swin Transformer의 계층적 구조와 ViTDet의 Simple Feature Pyramid가 이 한계를 극복한다.
4. **패치 경계 아티팩트**: 고정 크기 패치로 이미지를 분할하면, 물체가 패치 경계에 걸쳐 분리될 수 있다. 이는 특히 미세한 지역적 패턴이 중요한 태스크(의료 영상, 위성 이미지 등)에서 문제가 될 수 있다.

그럼에도 ViT는 비전 AI의 트랜스포머 시대를 열었으며, 이후 모든 비전 트랜스포머 연구의 출발점이 되었다. 2025년 현재에도 ViT 기반 아키텍처는 DINOv3(7B), SigLIP 2 등으로 계속 진화하며 비전 분야의 주류 아키텍처로 자리잡고 있다.

## 관련 문서

- [[transformer|Transformer]] - 발전 기반
- [[deit|DeiT]] - 후속 모델
- [[dinov2|DINOv2]] - 후속 모델
- [[mae|MAE]] - 후속 모델
- [[sam|SAM]] - 후속 모델
- [[swin-transformer|Swin Transformer]] - 후속 모델
- [[llava|Visual Instruction Tuning]] - 영감을 줌
- [[clip|CLIP]] - 적용 모델
- [[dit|DiT (Diffusion Transformers)]] - 적용 모델
- [[pixtral|Pixtral]] - 적용 모델
