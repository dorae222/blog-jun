# DiT (Diffusion Transformers): 확산 트랜스포머

## 개요

Scalable Diffusion Models with Transformers(DiT)는 2022년 Meta AI와 UC Berkeley의 William Peebles, Saining Xie가 발표한 연구로, 확산 모델의 백본 네트워크를 기존 U-Net에서 Vision Transformer(ViT)로 대체한 선구적 아키텍처이다. 핵심 발견은 **Transformer 스케일링 법칙이 확산 모델에도 그대로 적용**된다는 것이다.

- **논문**: [Scalable Diffusion Models with Transformers](https://arxiv.org/abs/2212.09748)
- **코드**: [facebookresearch/DiT](https://github.com/facebookresearch/DiT)
- **발표**: 2022년 12월, Meta AI / UC Berkeley
- **라이선스**: CC BY-NC 4.0

## 아키텍처 상세

다음 다이어그램은 DiT의 전체 구조와 네 가지 조건 주입 블록 변형을 보여준다.

![DiT 아키텍처 — 전체 파이프라인과 DiT 블록 변형](figures/fig_3.png)
*Figure 1: DiT 아키텍처 — 왼쪽: 노이즈된 잠재 맵을 패치화하여 DiT 블록으로 처리하는 전체 파이프라인. 오른쪽: adaLN-Zero, Cross-Attention, In-Context 세 가지 조건 주입 블록 변형. adaLN-Zero가 가장 높은 성능을 달성한다. (Source: Peebles & Xie, 2022)*

### 전체 파이프라인

DiT는 LDM과 동일하게 VAE 잠재 공간에서 동작한다:

1. VAE 인코더로 이미지를 잠재 맵 $z \in \mathbb{R}^{I \times I \times C}$로 인코딩
2. 잠재 맵을 $p \times p$ 패치로 분할하여 $(I/p)^2$개의 토큰 시퀀스 구성
3. 선형 임베딩 후 2D 위치 인코딩 추가
4. $N$개의 DiT 블록으로 노이즈 예측
5. VAE 디코더로 이미지 복원

| 구성 요소 | DiT-XL/2 사양 |
|----------|-------------|
| 파라미터 수 | 675M |
| 히든 차원 | 1152 |
| 레이어 수 | 28 |
| 어텐션 헤드 | 16 |
| 패치 크기 | 2 |
| VAE | Stable Diffusion VAE (KL-f8) |
| 잠재 공간 | $4 \times 32 \times 32$ |
| 위치 인코딩 | Sinusoidal 2D |
| 정규화 | AdaLN-Zero |
| 활성화 | GELU |

### 네 가지 조건 주입 방법 비교

논문은 타임스텝과 클래스 레이블을 DiT 블록에 주입하는 네 가지 방법을 체계적으로 비교하였다:

| 방법 | 설명 | FID (XL/2) |
|------|------|-----------|
| In-Context | 조건 토큰을 시퀀스에 추가 | 5.11 |
| Cross-Attention | 조건을 별도 KV로 어텐션 | 3.75 |
| Adaptive LN (adaLN) | 조건으로 LN 스케일·시프트 생성 | 2.85 |
| **adaLN-Zero** | adaLN + 게이트 0 초기화 | **2.27** |

다음 그래프는 네 가지 조건 주입 방법의 학습 전 과정에서의 FID 비교이다.

![네 가지 조건 주입 전략의 FID 비교](figures/fig_5.png)
*Figure 2: 조건 주입 전략 비교 — adaLN-Zero가 모든 학습 단계에서 Cross-Attention, In-Context, adaLN보다 일관되게 낮은 FID를 달성한다. (Source: Peebles & Xie, 2022)*

### adaLN-Zero 블록

adaLN-Zero는 DiT의 핵심 설계 선택이다:

$$\text{MLP}(\text{emb}_{time} + \text{emb}_{class}) \to (\alpha_1, \beta_1, \gamma_1, \alpha_2, \beta_2, \gamma_2)$$

$$h' = h + \alpha_1 \cdot \text{Attn}(\gamma_1 \cdot \text{LN}(h) + \beta_1)$$
$$\text{output} = h' + \alpha_2 \cdot \text{FFN}(\gamma_2 \cdot \text{LN}(h') + \beta_2)$$

$\alpha$ (잔차 게이트)는 **0으로 초기화**되어 학습 초기 DiT 블록이 항등 함수(identity function)로 동작한다. 이는 학습 초기 안정성을 크게 향상시킨다.

### 스케일링 법칙

DiT는 네 가지 크기(S/B/L/XL)와 세 가지 패치 크기(2/4/8) 조합을 실험하였다:

| 모델 | 파라미터 | GFLOPs | FID (↓) |
|------|---------|--------|---------|
| DiT-S/2 | 33M | 6.06 | 68.40 |
| DiT-B/2 | 130M | 23.01 | 43.47 |
| DiT-L/2 | 458M | 80.71 | 9.62 |
| DiT-XL/2 | 675M | 118.64 | **2.27** |
| DiT-XL/4 | 675M | 29.66 | 9.07 |
| DiT-XL/8 | 675M | 7.42 | 31.04 |

핵심 발견: **GFLOPs가 증가할수록 FID가 체계적으로 감소**한다. 패치 크기를 줄이는 것(시퀀스 길이 증가)이 모델 크기를 키우는 것만큼이나 효과적이다.

아래 그래프는 모델 크기와 패치 크기의 12가지 조합에서 학습에 따른 FID 변화를 보여준다.

![12가지 DiT 변형의 학습에 따른 FID 스케일링 거동](figures/fig_6.png)
*Figure 3: DiT 스케일링 거동 — 상단: 패치 크기 고정 시 모델 크기에 따른 FID 변화. 하단: 모델 크기 고정 시 패치 크기에 따른 FID 변화. 두 축 모두에서 GFLOPs 증가가 성능 향상을 가져온다. (Source: Peebles & Xie, 2022)*

특히 Transformer GFLOPs와 FID 간에는 -0.93의 강한 음의 상관관계가 존재한다.

![Transformer GFLOPs와 FID-50K 간의 상관관계](figures/fig_8.png)
*Figure 4: GFLOPs-FID 상관관계 — 12개 DiT 변형에서 Transformer GFLOPs와 FID 사이에 -0.93의 강한 음의 상관관계가 관찰되어, 확산 모델에서도 스케일링 법칙이 성립함을 입증한다. (Source: Peebles & Xie, 2022)*

## 핵심 혁신

1. **U-Net → Transformer 전환**: 확산 모델의 백본을 Transformer로 대체할 수 있음을 증명하여, 이후 Sora, SD3, Flux 등의 방향을 제시하였다.
2. **adaLN-Zero**: 0 초기화 게이트를 통한 안정적이고 효과적인 조건 주입 방법으로, 이후 표준 기법이 되었다.
3. **스케일링 법칙 증명**: LLM에서 관찰된 스케일링 법칙이 확산 이미지 생성에도 적용됨을 실증하였다.
4. **패치 크기의 중요성**: 작은 패치 크기(더 긴 시퀀스)가 더 높은 품질을 가져오며, 이는 해상도 확장에 핵심 설계 변수임을 보였다.

## 벤치마크/성능

| 모델 | FID (↓) | IS (↑) | 데이터셋 |
|------|---------|--------|---------|
| DiT-XL/2 (w/o CFG) | 9.62 | 121.5 | ImageNet 256 |
| DiT-XL/2 (CFG $s=1.5$) | **2.27** | 278.2 | ImageNet 256 |
| LDM-4 (CFG) | 3.60 | - | ImageNet 256 |
| ADM (CFG) | 4.59 | 186.7 | ImageNet 256 |
| BigGAN-deep | 6.95 | 198.2 | ImageNet 256 |

DiT-XL/2는 CFG 적용 시 FID 2.27로 기존 모든 클래스 조건부 모델을 능가하였다. 다음은 기존 확산 모델과의 FID-GFLOPs 비교이다.

![DiT와 기존 확산 모델의 FID-GFLOPs 비교](figures/fig_2.png)
*Figure 5: DiT vs 기존 확산 모델 — 왼쪽: DiT 스케일링 곡선. 오른쪽: DiT-XL/2가 ADM, LDM 등 U-Net 기반 모델 대비 더 적은 GFLOPs로 더 낮은 FID를 달성하여 계산 효율성에서도 우위를 보인다. (Source: Peebles & Xie, 2022)*

## 관련 모델 비교

| 특성 | DiT | LDM (U-Net) | PixArt-α | SD3 (MMDiT) |
|------|-----|------------|----------|------------|
| 백본 | ViT | U-Net | DiT + Cross-Attn | MMDiT |
| 조건 주입 | adaLN-Zero | Cross-Attn | adaLN-Single | Dual-Stream |
| 스케일링 | 입증 | 제한적 | 효율적 | 대규모 |
| 텍스트 조건 | 클래스만 | CLIP | T5-XXL | CLIP + T5 |
| 패치 기반 | 예 | 아니오 | 예 | 예 |

## 학습 상세

- **데이터셋**: ImageNet 1000 클래스, 256×256 / 512×512
- **VAE**: Stable Diffusion VAE (KL-f8, 동결)
- **학습률**: 1e-4, Adam optimizer
- **EMA**: 0.9999
- **학습 스텝**: 7M (약 7일, 8× A100)
- **CFG**: 학습 시 10% 클래스 드롭아웃

## 실무 활용

### 1. 대규모 확산 모델의 백본

DiT 아키텍처는 Sora(비디오), SD3/Flux(이미지), PixArt-α(효율적 학습) 등 현대 대규모 확산 모델의 표준 백본이 되었다.

### 2. 스케일링 법칙 기반 모델 설계

Compute-optimal 모델 크기 선택 시 DiT의 스케일링 결과를 참조하여 파라미터 수, 패치 크기, GFLOPs 예산을 결정할 수 있다.

### 3. 비디오·3D 생성으로의 확장

패치 기반 토큰화 방식은 2D 이미지에서 3D 시공간 패치로 자연스럽게 확장되어, 비디오 생성(Sora)과 3D 생성에 적용 가능하다.

## 한계 및 전망

### 한계

1. **클래스 조건부만 실험**: 원논문은 텍스트 조건부 생성을 다루지 않아, 실용적 텍스트-이미지 생성으로의 확장이 후속 연구에 맡겨졌다.
2. **Self-Attention 비용**: 시퀀스 길이의 제곱에 비례하는 어텐션 비용이 고해상도 확장에 병목이 된다.

### 후속 발전

- **PixArt-α (2023)**: DiT에 Cross-Attention을 추가한 효율적 텍스트-이미지 생성
- **SD3 (2024)**: MMDiT로 이미지-텍스트 이중 스트림 어텐션 도입
- **Sora (2024)**: 시공간 패치 DiT를 비디오 생성에 적용
- **Flux (2024)**: 하이브리드 이중/단일 스트림 DiT

DiT는 확산 모델의 Transformer 시대를 연 혁신적 연구로, "확산 + Transformer + 스케일링"이라는 현대 생성 AI의 핵심 공식을 확립하였다.

## 관련 문서

- [[ddpm|DDPM (Denoising Diffusion Probabilistic Models)]] — 발전 기반
- [[cogvideox|CogVideoX]] — 후속 모델
- [[hunyuanvideo|HunyuanVideo]] — 후속 모델
- [[pixart-alpha|PixArt-α]] — 후속 모델
- [[sora|Sora]] — 후속 모델
- [[kling|Kling]] — 영감을 줌
- [[runway-gen4|Runway Gen-4]] — 영감을 줌
- [[transfusion|Transfusion]] — 영감을 줌
- [[vit|An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale]] — 사용 기법
- [[sd3|Stable Diffusion 3]] — 적용 모델
