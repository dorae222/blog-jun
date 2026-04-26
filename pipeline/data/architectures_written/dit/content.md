<!-- infographic-hero -->
![DiT (Diffusion Transformers) 핵심 요약](figures/infographic.svg)

*Figure: DiT (Diffusion Transformers) 한 장 요약 인포그래픽*

# DiT (Diffusion Transformers): 확산 트랜스포머

## 개요

Scalable Diffusion Models with Transformers(DiT)는 2022년 Meta AI와 UC Berkeley의 William Peebles, Saining Xie가 발표한 연구로, 확산 모델의 백본 네트워크를 기존 U-Net에서 Vision Transformer(ViT)로 대체한 선구적 아키텍처이다. 핵심 발견은 **Transformer 스케일링 법칙이 확산 모델에도 그대로 적용**된다는 것이다.

- **논문**: [Scalable Diffusion Models with Transformers](https://arxiv.org/abs/2212.09748)
- **코드**: [facebookresearch/DiT](https://github.com/facebookresearch/DiT)
- **발표**: 2022년 12월, Meta AI / UC Berkeley
- **라이선스**: CC BY-NC 4.0

## 아키텍처 상세

다음 다이어그램은 DiT의 전체 구조와 네 가지 조건 주입 블록 변형을 보여준다.

![DiT 아키텍처 - 전체 파이프라인과 DiT 블록 변형](figures/fig_3.png)
*Figure 1: DiT 아키텍처 - 왼쪽: 노이즈된 잠재 맵을 패치화하여 DiT 블록으로 처리하는 전체 파이프라인. 오른쪽: adaLN-Zero, Cross-Attention, In-Context 세 가지 조건 주입 블록 변형. adaLN-Zero가 가장 높은 성능을 달성한다. (Source: Peebles & Xie, 2022)*

### 전체 파이프라인: 패치 기반 잠재 공간 처리

DiT는 LDM(Latent Diffusion Models)과 동일하게 VAE 잠재 공간에서 동작한다. U-Net 기반 확산 모델이 잠재 맵을 2D 합성곱으로 처리하는 것과 달리, DiT는 잠재 맵을 **패치 시퀀스로 변환**하여 Transformer가 처리할 수 있는 형태로 만든다. 이 패치화 과정은 ViT(Vision Transformer)에서 직접 차용한 것이다.

구체적인 파이프라인은 다음과 같다:

1. **VAE 인코딩**: 입력 이미지 $x \in \mathbb{R}^{256 \times 256 \times 3}$를 Stable Diffusion VAE(KL-f8)로 인코딩하여 잠재 맵 $z \in \mathbb{R}^{32 \times 32 \times 4}$를 얻는다. 이 과정에서 공간 해상도는 8배 축소되고, 채널 수는 4가 된다.
2. **패치화(Patchify)**: 잠재 맵을 $p \times p$ 패치로 분할하여 $(I/p)^2$개의 토큰 시퀀스를 구성한다. 패치 크기 $p=2$일 때 $(32/2)^2 = 256$개의 토큰이 생성되며, $p=8$일 때는 $(32/8)^2 = 16$개의 토큰만 생성된다.
3. **선형 임베딩**: 각 패치를 선형 레이어로 히든 차원($d$)으로 투영하고, 학습 가능한 2D sinusoidal 위치 인코딩을 추가한다.
4. **DiT 블록 처리**: $N$개의 DiT 블록이 토큰 시퀀스를 처리하며, 각 블록에서 adaLN-Zero를 통해 타임스텝과 클래스 조건이 주입된다.
5. **디코딩**: 최종 DiT 블록의 출력을 선형 레이어로 노이즈 예측값과 공분산으로 디코딩한 후, unpatchify로 잠재 맵 형태로 복원하고 VAE 디코더로 최종 이미지를 생성한다.

패치 크기 $p$는 시퀀스 길이와 계산 비용을 직접 결정하는 핵심 하이퍼파라미터이다. $p=2$에서 시퀀스 길이는 256이며 Self-Attention의 비용은 $O(256^2) = O(65536)$이다. $p=8$에서는 16 토큰만 처리하므로 비용이 $O(256)$으로 대폭 감소하지만, 공간 정보 손실로 생성 품질이 크게 하락한다.

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
*Figure 2: 조건 주입 전략 비교 - adaLN-Zero가 모든 학습 단계에서 Cross-Attention, In-Context, adaLN보다 일관되게 낮은 FID를 달성한다. (Source: Peebles & Xie, 2022)*

### adaLN-Zero 블록 상세

adaLN-Zero는 DiT의 핵심 설계 선택으로, Adaptive Layer Normalization에 Zero 초기화 게이팅을 결합한 조건 주입 메커니즘이다. 이 설계가 왜 효과적인지를 단계별로 이해해보자.

**표준 Adaptive LN (adaLN)**: 타임스텝 $t$와 클래스 레이블 $y$를 결합한 임베딩으로부터 Layer Normalization의 스케일($\gamma$)과 시프트($\beta$) 파라미터를 동적으로 생성한다. 이는 StyleGAN의 Adaptive Instance Normalization(AdaIN)에서 영감을 받은 것으로, 정규화 레이어를 통해 조건 정보를 각 레이어에 주입하는 방식이다.

**adaLN-Zero의 핵심 확장**: adaLN에 **잔차 연결 게이트** $\alpha$를 추가하고, 이를 0으로 초기화한다. 조건 임베딩으로부터 총 6개의 파라미터를 생성한다:

$$\text{MLP}(\text{emb}_{time} + \text{emb}_{class}) \to (\alpha_1, \beta_1, \gamma_1, \alpha_2, \beta_2, \gamma_2)$$

각 DiT 블록의 연산은 다음과 같다:

$$h' = h + \alpha_1 \cdot \text{Attn}(\gamma_1 \cdot \text{LN}(h) + \beta_1)$$
$$\text{output} = h' + \alpha_2 \cdot \text{FFN}(\gamma_2 \cdot \text{LN}(h') + \beta_2)$$

여기서 $\gamma$는 스케일, $\beta$는 시프트, $\alpha$는 잔차 게이트이다. $\alpha_1$과 $\alpha_2$가 **0으로 초기화**되므로, 학습 초기에는 Self-Attention과 FFN의 출력이 잔차 연결에 더해지지 않는다. 결과적으로 학습 시작 시 각 DiT 블록이 항등 함수(identity function)로 동작하여, 전체 네트워크가 입력을 그대로 통과시킨다.

이 설계의 핵심적 이점은 **학습 초기 안정성**이다. 28개 레이어를 가진 DiT-XL에서 모든 블록이 초기에 항등 함수로 동작하므로, 그래디언트가 깊은 네트워크를 안정적으로 통과할 수 있다. 학습이 진행됨에 따라 $\alpha$ 값이 점진적으로 증가하면서, 각 블록이 점차 유의미한 변환을 수행하기 시작한다. 이는 ControlNet의 Zero Convolution과 유사한 철학으로, "처음에는 아무것도 하지 않고, 점진적으로 기능을 추가한다"는 원칙을 공유한다.

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
*Figure 3: DiT 스케일링 거동 - 상단: 패치 크기 고정 시 모델 크기에 따른 FID 변화. 하단: 모델 크기 고정 시 패치 크기에 따른 FID 변화. 두 축 모두에서 GFLOPs 증가가 성능 향상을 가져온다. (Source: Peebles & Xie, 2022)*

특히 Transformer GFLOPs와 FID 간에는 -0.93의 강한 음의 상관관계가 존재한다.

![Transformer GFLOPs와 FID-50K 간의 상관관계](figures/fig_8.png)
*Figure 4: GFLOPs-FID 상관관계 - 12개 DiT 변형에서 Transformer GFLOPs와 FID 사이에 -0.93의 강한 음의 상관관계가 관찰되어, 확산 모델에서도 스케일링 법칙이 성립함을 입증한다. (Source: Peebles & Xie, 2022)*

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
*Figure 5: DiT vs 기존 확산 모델 - 왼쪽: DiT 스케일링 곡선. 오른쪽: DiT-XL/2가 ADM, LDM 등 U-Net 기반 모델 대비 더 적은 GFLOPs로 더 낮은 FID를 달성하여 계산 효율성에서도 우위를 보인다. (Source: Peebles & Xie, 2022)*

## U-Net 기반 확산 모델과의 비교

DiT의 등장은 확산 모델의 백본 선택에 근본적인 전환을 가져왔다. U-Net과 Transformer 백본의 차이를 구조적으로 비교한다.

**U-Net의 귀납적 편향**: U-Net은 인코더-디코더 구조와 스킵 연결을 통해 멀티스케일 특성을 자연스럽게 활용한다. 합성곱 연산의 지역적(local) 특성과 다운/업샘플링을 통한 계층적 처리는 이미지 생성에 적합한 강력한 귀납적 편향을 제공한다. 그러나 이 고정된 구조는 모델 스케일링에 제약을 준다. 채널 수를 늘리면 합성곱 비용이 급격히 증가하고, 레이어 수를 늘리는 것은 인코더-디코더 균형을 깨트린다.

**Transformer의 유연성**: DiT는 동일한 구조의 블록을 반복 적재하는 균일한(isotropic) 아키텍처로, 레이어 수와 히든 차원을 자유롭게 조절하여 모델을 스케일링할 수 있다. Self-Attention은 모든 패치 간의 전역적(global) 관계를 캡처하며, 이는 장거리 의존성이 중요한 생성 작업에서 유리하다. 또한 NLP 분야에서 축적된 Transformer 스케일링 노하우와 최적화 기법(Flash Attention, 모델 병렬화 등)을 직접 활용할 수 있다.

**실질적 성능 차이**: DiT-XL/2는 675M 파라미터로 ADM(554M U-Net)보다 FID에서 크게 앞서면서도, GFLOPs 대비 효율성에서도 우위를 보였다. 이는 Transformer의 계산이 이미지 생성에 더 "효율적으로" 사용됨을 시사한다.

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

## 후속 모델에 대한 영향

DiT는 단일 논문을 넘어 확산 모델 분야 전체의 방향을 전환시킨 연구이다. 2024-2025년 등장한 거의 모든 주요 확산 모델이 DiT 아키텍처의 직접적 후손이다.

**Sora (OpenAI, 2024)**: DiT의 패치 기반 접근을 시공간(spatiotemporal) 3D 패치로 확장하여 비디오 생성에 적용했다. 2D 이미지 패치 $(p \times p)$를 3D 시공간 패치 $(p \times p \times t)$로 일반화한 것으로, DiT의 아키텍처가 이미지를 넘어 비디오, 나아가 임의 차원의 데이터로 확장 가능함을 보여주었다.

**Stable Diffusion 3 (Stability AI, 2024)**: DiT 블록을 이중 스트림(dual-stream) 구조인 MMDiT(Multi-Modal DiT)로 발전시켰다. 이미지 토큰과 텍스트 토큰이 별도의 스트림으로 처리되다가 Joint Attention에서 합류하는 구조로, adaLN-Zero 대신 이중 스트림 어텐션을 조건 주입에 활용한다.

**Flux (Black Forest Labs, 2024)**: 하이브리드 이중/단일 스트림 DiT 구조를 채택했다. 초기 블록은 MMDiT 스타일의 이중 스트림으로, 후기 블록은 단일 스트림으로 전환하여 계산 효율과 표현력의 균형을 맞추었다.

**PixArt-α (2023)**: DiT에 Cross-Attention을 추가하여 텍스트 조건부 생성을 가능하게 했으며, T5-XXL 텍스트 인코더와 결합하여 효율적인 학습을 달성했다.

## 한계 및 과제

### 아키텍처적 한계

1. **클래스 조건부만 실험**: 원논문은 ImageNet 1000 클래스 조건부 생성만을 다루었다. 실용적 텍스트-이미지 생성(자유 형식 프롬프트)으로의 확장은 후속 연구(PixArt-α, SD3)에서야 이루어졌으며, 텍스트 조건 주입 방법(Cross-Attention vs adaLN vs 이중 스트림)에 대한 최적 설계는 DiT 자체에서는 탐구되지 않았다.
2. **Self-Attention의 이차 비용**: 시퀀스 길이 $n$에 대해 $O(n^2)$의 어텐션 비용은 고해상도 생성의 근본적 병목이다. 512x512 이미지에서는 잠재 공간 기준 1024개의 패치가 생성되며, 1024x1024에서는 4096개로 증가하여 어텐션 비용이 16배 폭증한다. Flash Attention, 윈도우 어텐션 등의 최적화가 필수적이다.
3. **VAE 병목**: DiT는 잠재 공간에서 동작하므로 VAE의 재구성 품질에 의해 생성 품질의 상한이 결정된다. SD VAE(KL-f8)의 압축 비율은 세밀한 텍스처와 고주파 디테일에서 한계를 보인다.
4. **위치 인코딩의 제약**: 고정된 sinusoidal 2D 위치 인코딩은 학습 해상도와 다른 해상도에서의 외삽(extrapolation)이 제한적이다. 이후 모델들은 RoPE 등의 상대 위치 인코딩으로 전환하였다.
5. **학습 비용**: DiT-XL/2의 7M 스텝 학습은 8x A100에서 약 7일이 소요되며, 이는 클래스 조건부 ImageNet에 국한된 비용이다. 텍스트 조건부 대규모 학습으로 확장하면 비용이 수십~수백 배 증가한다.

### 후속 발전

- **PixArt-α (2023)**: DiT에 Cross-Attention을 추가한 효율적 텍스트-이미지 생성
- **SD3 (2024)**: MMDiT로 이미지-텍스트 이중 스트림 어텐션 도입
- **Sora (2024)**: 시공간 패치 DiT를 비디오 생성에 적용
- **Flux (2024)**: 하이브리드 이중/단일 스트림 DiT

DiT는 확산 모델의 Transformer 시대를 연 혁신적 연구로, "확산 + Transformer + 스케일링"이라는 현대 생성 AI의 핵심 공식을 확립하였다.

## 관련 문서

- [[ddpm|DDPM (Denoising Diffusion Probabilistic Models)]] - 발전 기반
- [[cogvideox|CogVideoX]] - 후속 모델
- [[hunyuanvideo|HunyuanVideo]] - 후속 모델
- [[pixart-alpha|PixArt-α]] - 후속 모델
- [[sora|Sora]] - 후속 모델
- [[kling|Kling]] - 영감을 줌
- [[runway-gen4|Runway Gen-4]] - 영감을 줌
- [[transfusion|Transfusion]] - 영감을 줌
- [[vit|An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale]] - 사용 기법
- [[sd3|Stable Diffusion 3]] - 적용 모델
