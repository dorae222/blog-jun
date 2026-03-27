## 개요

Transformer 아키텍처는 NLP 분야에서 BERT, GPT 등을 통해 압도적인 성과를 거두었습니다. 그러나 컴퓨터 비전 분야는 2020년까지 CNN(Convolutional Neural Network)이 지배하고 있었습니다. Dosovitskiy 등(Google Brain, 2020)은 ICLR 2021에 발표한 **ViT(Vision Transformer)**를 통해 순수 Transformer를 이미지 분류에 직접 적용할 수 있음을 보여주었습니다. 이 논문은 발표 이후 약 5만 회 이상의 인용을 기록하며 컴퓨터 비전 역사상 가장 영향력 있는 논문 중 하나로 자리잡았습니다.

핵심 아이디어는 NLP에서 단어를 토큰으로 처리하듯, 이미지를 고정 크기의 **패치(patch)** 시퀀스로 분할하여 Transformer에 입력하는 것입니다. 이때 각 패치는 하나의 "단어"에 해당하며, 16x16 픽셀 패치를 사용할 경우 224x224 이미지는 $\left(\frac{224}{16}\right)^2 = 196$개의 토큰이 됩니다. 이 단순한 아이디어가 비전 분야의 패러다임을 근본적으로 변화시켰습니다.

---

## 배경

### CNN의 지배와 한계

AlexNet(2012) 이후 컴퓨터 비전은 CNN이 지배해왔습니다. VGGNet, ResNet, EfficientNet 등으로 이어지는 계보는 모두 **합성곱(convolution)** 연산을 기반으로 합니다. CNN은 두 가지 강력한 귀납적 편향(inductive bias)을 내장하고 있습니다:

1. **지역성(Locality)**: 필터가 인접 픽셀만 처리하여 지역적 패턴을 효율적으로 학습
2. **이동 불변성(Translation Invariance/Equivariance)**: 동일 필터가 이미지 전체에 적용되어 위치와 무관한 특징 추출

이러한 편향은 작은 데이터셋에서도 효과적인 학습을 가능하게 하지만, 동시에 전역적(global) 관계를 모델링하는 데 한계가 있습니다. 먼 거리의 픽셀 간 관계를 파악하려면 매우 깊은 네트워크가 필요합니다.

### Self-Attention의 비전 적용 시도

Transformer 이전에도 Self-Attention을 비전에 적용하려는 시도가 있었습니다. Non-local Neural Networks(Wang et al., 2018)는 CNN에 self-attention 블록을 삽입했고, Stand-Alone Self-Attention(Ramachandran et al., 2019)은 합성곱을 self-attention으로 대체하려 했습니다. 그러나 이들은 모두 CNN과 결합하거나 지역적 self-attention만 사용하여, 순수 Transformer 아키텍처로의 완전한 전환을 이루지 못했습니다.

ViT는 이러한 타협 없이 **NLP용 Transformer를 거의 수정 없이** 이미지에 적용함으로써 패러다임 전환을 이끌었습니다.

---

## 핵심 아이디어

ViT의 핵심 아이디어는 세 가지로 요약됩니다:

1. **이미지 패치를 토큰으로 변환**: 이미지를 고정 크기 패치로 분할하고, 각 패치를 선형 투영하여 Transformer 입력으로 사용
2. **표준 Transformer 인코더 그대로 사용**: NLP의 BERT와 동일한 아키텍처를 거의 수정 없이 적용
3. **대규모 사전학습으로 귀납적 편향 대체**: CNN의 지역성, 이동 불변성 편향 없이도 충분한 데이터로 학습하면 이들 패턴을 자연스럽게 학습

특히 세 번째 포인트가 논문의 가장 중요한 발견입니다. ViT는 ImageNet(1.2M 이미지)만으로는 CNN 대비 열위이지만, JFT-300M(3억 장) 수준의 대규모 데이터셋으로 사전학습하면 CNN을 능가합니다. 이는 **귀납적 편향이 데이터의 부족을 보상하는 것**이며, 데이터가 충분하면 편향이 오히려 성능의 천장이 될 수 있음을 의미합니다.

실제로 VTAB 벤치마크에서 ViT-H/14는 Natural, Specialized, Structured 세 범주 모두에서 CNN 기반 모델들을 압도하며, 단일 아키텍처의 범용성을 입증합니다.

![VTAB 벤치마크에서 ViT-H/14와 CNN 기반 모델들의 정확도 비교: 19개 태스크 전체에서 최고 성능](figures/fig_2.png)
*Figure 2: VTAB 벤치마크 결과. ViT-H/14(파란색)가 BiT-L, VIVI-Ex, S4L 대비 Natural(7개), Specialized(4개), Structured(8개) 전 범주에서 최고 정확도를 달성한다. 특히 Structured 태스크에서의 우위는 ViT가 공간적 추론 능력까지 갖추고 있음을 시사한다. (Dosovitskiy et al., 2021)*

---

## 방법론

### 이미지 패치 임베딩 (Patch Embedding)

아래 그림은 ViT의 전체 아키텍처를 보여줍니다. 이미지를 고정 크기 패치로 분할한 뒤 선형 투영하고, 위치 임베딩을 더해 Transformer 인코더에 입력하는 구조입니다.

![ViT 전체 아키텍처: 이미지를 패치로 분할하고 선형 투영하여 Transformer Encoder에 입력하는 구조](figures/fig_1.png)
*Figure 1: ViT 아키텍처 개요. 입력 이미지를 고정 크기 패치(16x16)로 분할하고, 각 패치를 선형 투영(Patch Embedding)한 뒤 위치 임베딩을 더하여 표준 Transformer Encoder에 입력한다. 시퀀스 앞에 추가된 [CLS] 토큰의 최종 출력이 분류에 사용된다.*

입력 이미지 $\mathbf{x} \in \mathbb{R}^{H \times W \times C}$를 $N$개의 패치로 분할합니다:

$$N = \frac{H \times W}{P^2}, \quad \mathbf{x}_p \in \mathbb{R}^{N \times (P^2 \cdot C)}$$

여기서 $P$는 패치 크기(보통 16 또는 32), $C$는 채널 수입니다. 각 패치는 선형 투영으로 $D$차원 임베딩으로 변환됩니다:

$$\mathbf{z}_0^i = \mathbf{E} \cdot \mathbf{x}_p^i + \mathbf{e}_i^{pos}, \quad \mathbf{E} \in \mathbb{R}^{(P^2 \cdot C) \times D}$$

실제 구현에서는 이 선형 투영을 stride가 패치 크기와 같은 2D 합성곱으로 효율적으로 수행합니다. 패치 크기 16, 입력 채널 3, 임베딩 차원 768이라면 `nn.Conv2d(3, 768, kernel_size=16, stride=16)`으로 구현됩니다.

학습된 패치 임베딩 필터를 시각화하면, CNN의 초기 레이어에서 나타나는 Gabor 필터와 유사한 구조적 패턴이 자연스럽게 형성되는 것을 확인할 수 있습니다.

![ViT 패치 임베딩 레이어의 학습된 RGB 필터: 주성분 28개 시각화](figures/fig_8_1.png)
*Figure 8 (상단): 패치 임베딩 레이어의 처음 28개 주성분 RGB 필터. 명시적인 합성곱 구조 없이도 방향성 에지 검출기, 색상 필터 등 CNN의 Gabor 필터와 유사한 저수준 특징 추출 패턴이 자연스럽게 학습된다. (Dosovitskiy et al., 2021)*

이는 ViT가 귀납적 편향 없이도 데이터로부터 CNN과 유사한 저수준 특징 추출 전략을 독립적으로 발견한다는 점에서 주목할 만합니다.

### CLS 토큰과 위치 임베딩

BERT와 동일하게 학습 가능한 **[CLS] 토큰**을 패치 임베딩 시퀀스 앞에 추가합니다:

$$\mathbf{z}_0 = \left[\mathbf{x}_{\mathrm{class}};\, \mathbf{z}_0^1;\, \mathbf{z}_0^2;\, \cdots;\, \mathbf{z}_0^N\right] + \mathbf{E}_{\mathrm{pos}}$$

Transformer를 통과한 후 [CLS] 토큰의 출력 표현이 이미지 전체를 대표하는 벡터로 사용됩니다. 위치 임베딩은 1D 학습 가능한 벡터를 사용합니다. 논문에서는 1D, 2D, 상대적 위치 임베딩을 비교했지만 성능 차이가 미미하여 단순한 1D 임베딩을 채택했습니다.

흥미로운 점은 1D 위치 임베딩만으로도 모델이 2D 공간 구조를 자연스럽게 학습한다는 것입니다. 아래 그림에서 위치 임베딩 간의 코사인 유사도를 시각화하면, 공간적으로 인접한 패치의 임베딩이 높은 유사도를 보이는 격자 패턴이 명확하게 나타납니다.

![위치 임베딩 간 코사인 유사도 행렬: 1D 위치 임베딩에서 2D 공간 구조가 자연스럽게 학습됨](figures/fig_8_2.png)
*Figure 7 (원논문 Figure 8 중간): 위치 임베딩 유사도 행렬. 각 패치 위치의 임베딩과 나머지 모든 위치 임베딩 간의 코사인 유사도를 시각화한 것이다. 같은 행/열에 위치한 패치끼리 높은 유사도를 보여, 1D 임베딩만으로도 2D 격자 구조를 학습함을 확인할 수 있다.*

### Transformer 인코더

표준 Transformer 인코더 블록을 $L$번 반복합니다:

$$\mathbf{z}'_\ell = \mathrm{MSA}(\mathrm{LN}(\mathbf{z}_{\ell-1})) + \mathbf{z}_{\ell-1}$$
$$\mathbf{z}_\ell = \mathrm{MLP}(\mathrm{LN}(\mathbf{z}'_\ell)) + \mathbf{z}'_\ell$$

여기서 MSA는 Multi-Head Self-Attention, LN은 Layer Normalization입니다. ViT는 Pre-Norm 구조를 사용하여 LN을 attention/MLP 전에 적용합니다. Multi-Head Self-Attention의 핵심 수식은:

$$\mathrm{Attention}(Q, K, V) = \mathrm{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

Self-Attention의 시간 복잡도는 $O(N^2 \cdot D)$이므로, 패치 수 $N = 196$일 때 약 $196^2 = 38,416$개의 쌍을 처리합니다. 이는 모든 패치가 다른 모든 패치와 직접 상호작용할 수 있음을 의미하며, CNN의 지역적 수용 영역(receptive field)과 대조됩니다.

### 분류 헤드

마지막 레이어의 [CLS] 토큰 표현에 MLP 헤드를 붙여 분류합니다:

$$y = \mathrm{MLP}(\mathbf{z}_L^0)$$

사전학습 시에는 1개의 은닉층(GELU 활성화)을 가진 MLP, 파인튜닝 시에는 단일 선형 레이어를 사용합니다.

### ViT 모델 변형

| 모델 | 레이어 수 $L$ | 은닉 크기 $D$ | MLP 크기 | 헤드 수 | 파라미터 수 |
|------|----------|-------------|---------|---------|----------|
| ViT-B/16 | 12 | 768 | 3072 | 12 | 86M |
| ViT-L/16 | 24 | 1024 | 4096 | 16 | 307M |
| ViT-H/14 | 32 | 1280 | 5120 | 16 | 632M |

표기법에서 `/16`은 패치 크기 16x16을, `/14`는 패치 크기 14x14를 의미합니다. 패치가 작을수록 시퀀스 길이가 길어져 더 세밀한 정보를 처리할 수 있지만, 계산 비용이 $O(N^2)$로 증가합니다.

---

## 코드 예제

### 패치 임베딩 (Patch Embedding)

이미지를 고정 크기 패치로 분할하고 선형 투영하여 Transformer 입력 임베딩으로 변환한다.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class PatchEmbedding(nn.Module):
    """이미지를 패치 임베딩으로 변환하는 모듈"""
    def __init__(self, img_size=224, patch_size=16, in_channels=3, embed_dim=768):
        super().__init__()
        self.num_patches = (img_size // patch_size) ** 2  # 196
        # 패치를 임베딩으로 변환하는 Conv2d (stride=patch_size로 패치 분할)
        self.proj = nn.Conv2d(
            in_channels, embed_dim,
            kernel_size=patch_size, stride=patch_size
        )

    def forward(self, x):
        # x: (B, C, H, W) -> (B, embed_dim, H/P, W/P)
        x = self.proj(x)
        # (B, embed_dim, N^0.5, N^0.5) -> (B, N, embed_dim)
        x = x.flatten(2).transpose(1, 2)
        return x

```

### Multi-Head Self-Attention

QKV를 동시에 계산하여 Scaled Dot-Product Attention을 수행하는 ViT 어텐션 모듈이다.

```python
class MultiHeadSelfAttention(nn.Module):
    """Multi-Head Self-Attention 모듈"""
    def __init__(self, embed_dim=768, num_heads=12, dropout=0.0):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads
        self.scale = self.head_dim ** -0.5

        self.qkv = nn.Linear(embed_dim, embed_dim * 3)
        self.proj = nn.Linear(embed_dim, embed_dim)
        self.attn_drop = nn.Dropout(dropout)

    def forward(self, x):
        B, N, C = x.shape
        # Q, K, V 동시 계산
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # (3, B, heads, N, head_dim)
        q, k, v = qkv.unbind(0)

        # Scaled Dot-Product Attention
        attn = (q @ k.transpose(-2, -1)) * self.scale  # (B, heads, N, N)
        attn = attn.softmax(dim=-1)
        attn = self.attn_drop(attn)

        x = (attn @ v).transpose(1, 2).reshape(B, N, C)
        return self.proj(x)

```

### Transformer 인코더 블록

Pre-LN 방식의 ViT Transformer 블록으로, 멀티헤드 어텐션과 MLP를 Residual Connection으로 결합한다.

```python
class TransformerBlock(nn.Module):
    """ViT Transformer 인코더 블록 (Pre-Norm)"""
    def __init__(self, embed_dim=768, num_heads=12, mlp_ratio=4.0, dropout=0.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = MultiHeadSelfAttention(embed_dim, num_heads, dropout)
        self.norm2 = nn.LayerNorm(embed_dim)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, int(embed_dim * mlp_ratio)),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(int(embed_dim * mlp_ratio), embed_dim),
            nn.Dropout(dropout),
        )

    def forward(self, x):
        x = x + self.attn(self.norm1(x))   # Pre-Norm + Residual
        x = x + self.mlp(self.norm2(x))     # Pre-Norm + Residual
        return x

```

### ViT 전체 모델

패치 임베딩, CLS 토큰, 위치 임베딩, Transformer 블록 스택을 결합한 ViT 전체 구조와 추론 예시이다.

```python
class ViT(nn.Module):
    """Vision Transformer 전체 모델"""
    def __init__(self, img_size=224, patch_size=16, num_classes=1000,
                 embed_dim=768, depth=12, num_heads=12):
        super().__init__()
        self.patch_embed = PatchEmbedding(img_size, patch_size, embed_dim=embed_dim)
        num_patches = self.patch_embed.num_patches

        # 학습 가능한 CLS 토큰과 위치 임베딩
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + 1, embed_dim))

        # Transformer 인코더 블록 스택
        self.blocks = nn.Sequential(*[
            TransformerBlock(embed_dim, num_heads)
            for _ in range(depth)
        ])
        self.norm = nn.LayerNorm(embed_dim)
        self.head = nn.Linear(embed_dim, num_classes)

        # 가중치 초기화
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        nn.init.trunc_normal_(self.cls_token, std=0.02)

    def forward(self, x):
        B = x.shape[0]
        x = self.patch_embed(x)                          # (B, N, D)
        cls_tokens = self.cls_token.expand(B, -1, -1)    # (B, 1, D)
        x = torch.cat([cls_tokens, x], dim=1)            # (B, N+1, D)
        x = x + self.pos_embed                           # 위치 정보 추가

        x = self.blocks(x)                               # Transformer 인코딩
        x = self.norm(x)
        return self.head(x[:, 0])                        # CLS 토큰만 사용


# 모델 생성 및 추론 예시
model = ViT(img_size=224, patch_size=16, num_classes=1000,
            embed_dim=768, depth=12, num_heads=12)  # ViT-B/16
img = torch.randn(1, 3, 224, 224)  # 배치 1, RGB, 224x224
logits = model(img)  # (1, 1000)
print(f"파라미터 수: {sum(p.numel() for p in model.parameters()) / 1e6:.1f}M")
print(f"출력 shape: {logits.shape}")  # torch.Size([1, 1000])
```

---

## 실험 결과

### 데이터셋 규모에 따른 성능 변화

논문의 가장 핵심적인 실험 결과는 사전학습 데이터 규모에 따른 성능 변화입니다. 아래 그림은 ImageNet, ImageNet-21K, JFT-300M 세 가지 사전학습 데이터셋에서 ViT 변형들과 BiT(ResNet) 모델의 ImageNet Top-1 정확도를 비교합니다.

![사전학습 데이터 규모에 따른 ImageNet Top-1 정확도 비교: ImageNet, ImageNet-21K, JFT-300M](figures/fig_3_1.png)
*Figure 3: 사전학습 데이터셋 규모별 ImageNet Top-1 정확도. ImageNet(1.2M)에서는 BiT(회색)가 모든 ViT 변형을 앞서지만, ImageNet-21K(14M)에서 격차가 줄어들고, JFT-300M(300M)에서는 ViT-H/14(주황)가 88.55%로 BiT를 역전한다. 데이터 규모가 커질수록 ViT의 이점이 뚜렷해지는 스케일링 특성이 핵심이다.*

| 사전학습 데이터 | 모델 | ImageNet Top-1 Accuracy |
|--------------|------|-------------------------|
| ImageNet (1.2M) | ViT-L/16 | 76.5% |
| ImageNet-21K (14M) | ViT-L/16 | 85.3% |
| JFT-300M (300M) | ViT-L/16 | **87.7%** |
| JFT-300M (300M) | ViT-H/14 | **88.55%** |
| ImageNet (1.2M) | BiT-L (ResNet152x4) | 87.5% |
| JFT-300M (300M) | BiT-L (ResNet152x4) | 87.5% |

소규모 데이터(ImageNet 1.2M)에서는 ViT-L이 76.5%로 CNN 기반 BiT-L(87.5%)보다 크게 뒤처집니다. 그러나 JFT-300M으로 사전학습하면 ViT-H/14가 88.55%를 달성하여 BiT-L을 능가합니다. 이는 **대규모 데이터가 귀납적 편향을 대체할 수 있음**을 보여주는 결정적 증거입니다.

이 현상을 보다 세밀하게 분석하기 위해, 논문에서는 JFT-300M의 부분집합을 다양한 크기로 샘플링하여 학습 데이터 수에 따른 성능 곡선을 비교합니다.

![학습 샘플 수에 따른 ImageNet 5-shot 정확도: 소규모 데이터에서 ResNet 우위, 대규모에서 ViT 역전](figures/fig_5.png)
*Figure 5: 학습 샘플 수 증가에 따른 ImageNet 5-shot 정확도. 소규모(9M)에서는 ResNet(R152x2, 빨간 X)이 모든 ViT 변형보다 높은 성능을 보이지만, 데이터가 약 100M을 넘어가면 ViT-L/32(파란 원)가 ResNet을 추월하기 시작한다. 이 교차점이 바로 귀납적 편향과 데이터 규모 간의 트레이드오프를 상징한다.*

### 사전학습 계산 효율성

동일한 계산 비용(FLOPs)에서 ViT는 ResNet보다 더 높은 성능을 달성합니다. 아래 그림은 총 사전학습 계산량(TPUv3-core-days) 대비 전이 학습 정확도를 비교한 것으로, ViT의 우월한 계산 효율성을 명확히 보여줍니다.

![사전학습 계산량 대비 전이 정확도: ViT가 동일 계산 예산에서 ResNet BiT를 능가](figures/fig_6.png)
*Figure 4 (원논문 Figure 5): 총 사전학습 계산량 대비 전이 학습 정확도. 동일한 계산 예산에서 ViT(원형 마커)가 ResNet 기반 BiT(사각형 마커)보다 일관되게 더 높은 정확도를 달성한다. 특히 ViT-H/14는 BiT-L 대비 약 4배 적은 사전학습 계산으로 유사한 성능에 도달하며, Transformer의 표현 학습 효율성을 입증한다. (Dosovitskiy et al., 2021)*

이는 Transformer의 자기 주의(self-attention) 메커니즘이 CNN의 합성곱보다 이미지 표현 학습에 본질적으로 더 효율적임을 시사합니다. 같은 계산 자원으로 더 좋은 성능을 얻을 수 있다는 점은 실용적 관점에서 ViT의 큰 장점입니다.

### Attention 패턴 분석

논문은 학습된 어텐션 패턴을 시각화하여 ViT가 이미지를 어떻게 이해하는지 분석합니다. 아래 그림은 다양한 입력 이미지에 대해 ViT가 어떤 영역에 주목하는지를 보여줍니다.

![ViT의 어텐션 맵 시각화: 입력 이미지와 대응하는 Self-Attention 히트맵](figures/fig_7.png)
*Figure 7 (원논문 Figure 6): ViT가 학습한 어텐션 패턴 시각화. 별도의 지도 학습 없이도 모델이 의미적으로 중요한 객체 영역(개, 새, 곤충 등)에 집중하는 어텐션을 자연스럽게 학습한다. 이는 ViT가 전역적 self-attention을 통해 이미지의 의미 구조를 효과적으로 파악함을 보여준다.*

레이어 깊이에 따른 어텐션 패턴도 흥미로운 계층 구조를 보입니다. 아래 그림은 각 레이어에서 어텐션 헤드별 평균 어텐션 거리를 시각화한 것입니다.

![ViT-L/16 레이어 깊이에 따른 헤드별 평균 어텐션 거리: 하위 레이어 지역적, 상위 레이어 전역적 패턴](figures/fig_8_3.png)
*Figure 8 (하단): ViT-L/16의 레이어 깊이별 헤드별 평균 어텐션 거리. 하위 레이어(0-5)에서는 일부 헤드가 매우 짧은 거리(지역적 패턴)에 집중하지만, 상위 레이어로 갈수록 대부분의 헤드가 긴 거리(전역적 패턴)로 어텐션을 확장한다. 특히 하위 레이어에서도 전역적 어텐션을 수행하는 헤드가 존재하여, CNN과 달리 첫 레이어부터 장거리 의존성을 모델링할 수 있음을 보여준다. (Dosovitskiy et al., 2021)*

이 결과에서 주목할 점은 다음과 같습니다:

- **하위 레이어**: 인접 패치에 집중하는 지역적(local) 어텐션 패턴이 자연스럽게 학습됨 (CNN의 합성곱과 유사)
- **상위 레이어**: 의미적으로 관련된 먼 거리 패치에도 어텐션을 할당하는 전역적(global) 패턴
- **혼합 전략**: 같은 레이어 내에서도 지역적 헤드와 전역적 헤드가 공존하여 다양한 스케일의 정보를 동시에 처리

이는 CNN이 깊은 네트워크 구조를 통해 점진적으로 수용 영역(receptive field)을 넓히는 것과 유사하지만, ViT는 첫 번째 레이어부터 이미 전역적 연결 능력을 갖추고 있다는 점에서 근본적으로 다릅니다.

### 파인튜닝 성능

다양한 다운스트림 태스크에서의 파인튜닝 결과:

| 데이터셋 | ViT-H/14 | BiT-L |
|---------|----------|-------|
| ImageNet | 88.55 | 87.54 |
| CIFAR-10 | 99.50 | 99.37 |
| CIFAR-100 | 94.55 | 93.51 |
| Oxford Pets | 97.56 | 96.62 |
| Oxford Flowers | 99.68 | 99.63 |

---

## 의의 및 한계

### 의의

- **패러다임 전환**: 비전 분야의 CNN 독점에 도전하여 Transformer 기반 모델의 가능성을 입증했습니다. 발표 이후 약 5만 회 이상 인용되며 2022년 가장 많이 인용된 논문 중 하나로 기록되었습니다.
- **통합 아키텍처의 시작**: NLP와 비전에서 동일한 아키텍처를 사용할 수 있게 되어, CLIP, DALL-E, LLaVA 등 멀티모달 모델 설계의 기반이 되었습니다.
- **스케일링 법칙 확인**: 데이터와 모델 크기에 따른 명확한 성능 향상 패턴을 비전에서도 확인하여, 비전 모델의 스케일링 방향을 제시했습니다.
- **연구 생태계 변화**: DeiT, Swin Transformer, BEiT, MAE 등 수백 편의 후속 연구를 촉발하여 비전 트랜스포머(Vision Transformer) 분야 자체를 새로 형성했습니다.

### 한계

- **대규모 데이터 의존성**: JFT-300M 같은 대규모 사전학습 데이터 없이는 CNN 대비 성능이 열위합니다. 이는 자원이 제한된 연구 환경에서의 활용을 제약합니다.
- **이차 복잡도**: Self-Attention의 시퀀스 길이 $N$에 대한 $O(N^2)$ 복잡도는 고해상도 이미지(예: 1024x1024)에서 비효율적입니다. 패치 수가 $4096$개로 증가하면 어텐션 행렬 크기가 $4096^2 \approx 16.8M$이 됩니다.
- **위치 정보 처리의 한계**: 2D 구조를 1D 시퀀스로 평탄화하여 공간 관계 정보가 일부 손실됩니다. 이는 이후 Swin Transformer의 윈도우 기반 어텐션으로 보완되었습니다.
- **밀집 예측 태스크 한계**: 분류에는 강하지만, 객체 탐지나 세그멘테이션 같은 밀집 예측 태스크에는 추가 설계가 필요합니다.
- **귀납적 편향 부재**: 작은 데이터셋에서 과적합 위험이 높으며, 데이터 효율성이 CNN보다 낮습니다.

---

## 후속 연구

### DeiT (Data-efficient Image Transformers, 2021)

Facebook AI에서 발표한 DeiT는 ImageNet만으로도 ViT를 효과적으로 학습하는 방법을 제안했습니다. 지식 증류(knowledge distillation)와 강력한 데이터 증강 기법(RandAugment, Mixup, CutMix, Random Erasing)을 활용하여 ViT의 데이터 의존성 문제를 크게 완화했습니다.

### Swin Transformer (2021)

계층적(hierarchical) 구조와 이동 윈도우(shifted window) Self-Attention을 도입하여 CNN과 유사한 다중 스케일 특징 추출을 가능하게 했습니다. 복잡도를 $O(N^2)$에서 $O(N)$으로 줄여 고해상도 이미지 처리에 효율적이며, 객체 탐지, 세그멘테이션 등 다운스트림 태스크에서 강력한 성능을 보여 실용적 비전 트랜스포머의 기준이 되었습니다.

### MAE (Masked Autoencoders, 2022)

ViT 기반의 자기지도 학습 방법으로, 이미지 패치의 75%를 마스킹하고 복원하는 방식으로 사전학습합니다. BERT의 마스크드 언어 모델링을 비전에 적용한 것으로, 레이블이 없는 대규모 이미지 데이터에서 효과적인 표현 학습이 가능합니다.

### CLIP (2021)

OpenAI가 발표한 CLIP은 ViT 비전 인코더와 텍스트 인코더를 대조 학습(contrastive learning)으로 연결합니다. 4억 개의 이미지-텍스트 쌍으로 학습하여 제로샷 이미지 분류와 멀티모달 이해의 기반을 마련했으며, 이후 DALL-E, Stable Diffusion, LLaVA 등 거의 모든 멀티모달 모델에 영향을 미쳤습니다.

### Vision Mamba, FlashAttention 등

최근에는 ViT의 이차 복잡도를 해결하기 위해 Mamba 기반의 선형 복잡도 비전 모델(Vision Mamba, VMamba)과 FlashAttention을 활용한 효율적 ViT 구현이 활발히 연구되고 있습니다.

---

## 결론

ViT는 "이미지를 단어처럼 처리할 수 있다"는 단순하지만 강력한 아이디어로 컴퓨터 비전의 역사를 바꾸었습니다. 충분한 데이터와 모델 크기를 주면 CNN의 귀납적 편향 없이도 더 나은 표현을 학습할 수 있음을 증명했습니다. 이 발견은 단순히 이미지 분류의 새로운 방법을 제시한 것을 넘어, NLP와 비전의 아키텍처 통합이라는 더 큰 비전을 실현하는 첫 걸음이었습니다. 이후 CLIP, DALL-E, LLaVA, GPT-4V 등 대부분의 최신 멀티모달 모델이 ViT 기반 비전 인코더를 채택하고 있어, ViT는 현대 AI의 핵심 구성요소로 확고히 자리잡았습니다.

## 관련 문서

- [[transformer|Transformer]] ( 발전 기반
- [[deit|DeiT]] ) 후속 모델
- [[dinov2|DINOv2]] ( 후속 모델
- [[mae|MAE]] ) 후속 모델
- [[sam|SAM]] ( 후속 모델
- [[swin-transformer|Swin Transformer]] ) 후속 모델
- [[llava|Visual Instruction Tuning]] ( 영감을 줌
- [[clip|CLIP]] ) 적용 모델
- [[dit|DiT (Diffusion Transformers)]] ( 적용 모델
- [[pixtral|Pixtral]] ) 적용 모델
