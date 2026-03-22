---
title: "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale"
slug: vit
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.413721+00:00"
architecture_entry: vit
---

## 논문 개요

Transformer 아키텍처는 NLP 분야에서 BERT, GPT 등을 통해 압도적인 성과를 거두었습니다. 그러나 컴퓨터 비전 분야는 2020년까지 CNN(Convolutional Neural Network)이 지배하고 있었습니다. Dosovitskiy 등(Google Brain, 2020)은 ICLR 2021에 발표한 **ViT(Vision Transformer)**를 통해 순수 Transformer를 이미지 분류에 직접 적용할 수 있음을 보여주었습니다.

핵심 아이디어는 NLP에서 단어를 토큰으로 처리하듯, 이미지를 고정 크기의 **패치(patch)** 시퀀스로 분할하여 Transformer에 입력하는 것입니다. 이때 각 패치는 하나의 "단어"에 해당하며, 16×16 픽셀 패치를 사용할 경우 224×224 이미지는 $\left(\frac{224}{16}\right)^2 = 196$개의 토큰이 됩니다.

---

## 핵심 기여

1. **순수 Transformer를 이미지 분류에 직접 적용**: CNN 없이 Self-Attention만으로 이미지 이해 가능함을 증명
2. **대규모 사전학습의 중요성 입증**: JFT-300M(3억 장)으로 사전학습 시 CNN 모델 능가
3. **이미지 패치 기반 토큰화**: 이미지를 16×16 패치로 분할하는 단순하지만 효과적인 방법
4. **비전-언어 통합 가능성 제시**: NLP와 동일한 아키텍처 사용으로 멀티모달 연구의 기반 마련

---

## 방법론 상세

### 이미지 패치 임베딩 (Patch Embedding)

입력 이미지 $\mathbf{x} \in \mathbb{R}^{H \times W \times C}$를 $N$개의 패치로 분할합니다:

$$N = \frac{H \times W}{P^2}, \quad \mathbf{x}_p \in \mathbb{R}^{N \times (P^2 \cdot C)}$$

여기서 $P$는 패치 크기(보통 16 또는 32), $C$는 채널 수입니다. 각 패치는 선형 투영으로 $D$차원 임베딩으로 변환됩니다:

$$\mathbf{z}_0^i = \mathbf{E} \cdot \mathbf{x}_p^i + \mathbf{e}_i^{pos}, \quad \mathbf{E} \in \mathbb{R}^{(P^2 \cdot C) \times D}$$

### CLS 토큰

BERT와 동일하게 학습 가능한 **[CLS] 토큰**을 패치 임베딩 시퀀스 앞에 추가합니다:

$$\mathbf{z}_0 = \left[\mathbf{x}_{\mathrm{class}};\, \mathbf{z}_0^1;\, \mathbf{z}_0^2;\, \cdots;\, \mathbf{z}_0^N\right] + \mathbf{E}_{\mathrm{pos}}$$

Transformer를 통과한 후 [CLS] 토큰의 출력 표현이 이미지 전체를 대표하는 벡터로 사용됩니다.

### Positional Embedding (Positional Embedding)

ViT는 1D 학습 가능한 Positional Embedding을 사용합니다. 논문에서는 1D, 2D, 상대적 Positional Embedding을 비교했지만 성능 차이가 미미하여 단순한 1D 임베딩을 채택했습니다.

```
시퀀스: [CLS, Patch_1, Patch_2, ..., Patch_196]
위치:   [  0,      1,      2, ...,       196]
```

### Transformer 인코더

표준 Transformer 인코더 블록을 $L$번 반복합니다:

$$\mathbf{z}'_\ell = \mathrm{MSA}(\mathrm{LN}(\mathbf{z}_{\ell-1})) + \mathbf{z}_{\ell-1}$$
$$\mathbf{z}_\ell = \mathrm{MLP}(\mathrm{LN}(\mathbf{z}'_\ell)) + \mathbf{z}'_\ell$$

Multi-Head Self-Attention:

$$\mathrm{Attention}(Q, K, V) = \mathrm{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

### 분류 헤드

마지막 레이어의 [CLS] 토큰 표현에 MLP 헤드를 붙여 분류:

$$y = \mathrm{MLP}(\mathbf{z}_L^0)$$

사전학습 시에는 1개의 은닉층을 가진 MLP, 파인튜닝 시에는 단일 선형 레이어를 사용합니다.

### ViT 모델 변형

| 모델 | 레이어 수 | 은닉 크기 $D$ | MLP 크기 | 헤드 수 | 파라미터 수 |
|------|----------|-------------|---------|---------|----------|
| ViT-B/16 | 12 | 768 | 3072 | 12 | 86M |
| ViT-L/16 | 24 | 1024 | 4096 | 16 | 307M |
| ViT-H/14 | 32 | 1280 | 5120 | 16 | 632M |

표기법: `/16`은 패치 크기 16×16을 의미합니다.

### 구현 예시

```python
import torch
import torch.nn as nn

class PatchEmbedding(nn.Module):
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

class ViT(nn.Module):
    def __init__(self, img_size=224, patch_size=16, num_classes=1000,
                 embed_dim=768, depth=12, num_heads=12):
        super().__init__()
        self.patch_embed = PatchEmbedding(img_size, patch_size, embed_dim=embed_dim)
        num_patches = self.patch_embed.num_patches
        
        # CLS 토큰과 위치 임베딩
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        self.pos_embed = nn.Parameter(torch.zeros(1, num_patches + 1, embed_dim))
        
        # Transformer 인코더
        self.encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(embed_dim, num_heads, embed_dim * 4),
            num_layers=depth
        )
        self.norm = nn.LayerNorm(embed_dim)
        self.head = nn.Linear(embed_dim, num_classes)
    
    def forward(self, x):
        B = x.shape[0]
        x = self.patch_embed(x)  # (B, N, D)
        
        cls_tokens = self.cls_token.expand(B, -1, -1)  # (B, 1, D)
        x = torch.cat([cls_tokens, x], dim=1)  # (B, N+1, D)
        x = x + self.pos_embed
        
        x = self.encoder(x)
        x = self.norm(x)
        return self.head(x[:, 0])  # CLS 토큰만 사용
```

---

## 실험 결과

### 데이터셋 규모에 따른 성능 변화

| 사전학습 데이터 | 모델 | ImageNet Top-1 |
|--------------|------|---------------|
| ImageNet (1.2M) | ViT-L/16 | 76.5% |
| ImageNet-21K (14M) | ViT-L/16 | 85.3% |
| JFT-300M (300M) | ViT-L/16 | **87.7%** |
| JFT-300M (300M) | ViT-H/14 | **88.5%** |
| - | BiT-L (ResNet) | 87.5% |

소규모 데이터에서는 CNN 기반 BiT-L보다 성능이 낮지만, 대규모 데이터에서는 능가합니다.

### 주목할 점: 귀납적 편향(Inductive Bias)

CNN은 **지역성(locality)**과 **이동 불변성(translation invariance)**이라는 강한 귀납적 편향을 가집니다. ViT는 이러한 편향이 없어 소규모 데이터에서는 CNN보다 불리하지만, 대규모 데이터에서는 이 편향 없이도 패턴을 학습할 수 있습니다.

---

## 후속 연구

### DeiT (Data-efficient Image Transformers)

Facebook AI(2021)에서 발표. ImageNet만으로도 ViT를 효과적으로 학습하는 방법 제안. 지식 증류(knowledge distillation)와 강력한 데이터 증강 기법 활용.

### Swin Transformer

계층적(hierarchical) 구조와 이동 윈도우(shifted window) Self-Attention으로 CNN과 유사한 특성 추출 가능. 객체 탐지, 세그멘테이션 등 다운스트림 태스크에서 강력한 성능.

### MAE (Masked Autoencoders)

ViT 기반의 자기지도 학습 방법. 이미지 패치의 75%를 마스킹하고 복원하는 방식으로 사전학습.

### CLIP

ViT 비전 인코더와 텍스트 인코더를 대조 학습으로 연결. 제로샷 이미지 분류와 멀티모달 이해의 기반.

---

## 의의 및 한계

### 의의

- **패러다임 전환**: 비전 분야의 CNN 독점에 도전하여 Transformer 기반 모델의 가능성을 입증
- **통합 아키텍처**: NLP와 비전에서 동일한 아키텍처 사용으로 멀티모달 모델의 설계 단순화
- **확장성**: 데이터와 모델 크기에 따른 명확한 성능 향상(스케일링 법칙) 확인
- **학문적 영향**: 2022년 가장 많이 인용된 논문 중 하나

### 한계

- **대규모 데이터 의존성**: JFT-300M 같은 대규모 사전학습 데이터 없이는 CNN 대비 성능 열위
- **이차 복잡도**: Self-Attention의 시퀀스 길이 $N$에 대한 $O(N^2)$ 복잡도 (고해상도 이미지에서 비효율)
- **위치 정보 처리**: 2D 구조를 1D 시퀀스로 평탄화하여 공간 관계 정보 손실
- **귀납적 편향 부재**: 작은 데이터셋에서 과적합 위험

---

## 결론

ViT는 "이미지를 단어처럼 처리할 수 있다"는 단순하지만 강력한 아이디어로 컴퓨터 비전의 역사를 바꾸었습니다. 충분한 데이터와 모델 크기를 주면 CNN의 귀납적 편향 없이도 더 나은 표현을 학습할 수 있음을 증명했습니다. 이후 CLIP, DALL-E, LLaVA 등 대부분의 최신 멀티모달 모델이 ViT 기반 비전 인코더를 채택하고 있어, 비전-언어 통합의 핵심 구성요소가 되었습니다.