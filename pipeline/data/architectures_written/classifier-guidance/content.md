<!-- infographic-hero -->
![Classifier Guidance (ADM) 핵심 요약](figures/infographic.svg)

*Figure: Classifier Guidance (ADM) 한 장 요약 인포그래픽*

# Classifier Guidance (ADM): 분류기 가이던스 기반 확산 모델

## 개요

"Diffusion Models Beat GANs on Image Synthesis"는 2021년 OpenAI의 Prafulla Dhariwal과 Alex Nichol이 발표한 논문으로, Ablated Diffusion Model(ADM)과 Classifier Guidance 기법을 통해 확산 모델이 FID 기준으로 GAN을 최초로 능가함을 보인 역사적 연구이다. 이 논문은 U-Net 아키텍처 개선(ADM)과 외부 분류기를 활용한 조건부 생성(Classifier Guidance) 두 가지 핵심 기여를 제시하였다.

- **논문**: [Diffusion Models Beat GANs on Image Synthesis](https://arxiv.org/abs/2105.05233)
- **코드**: [openai/guided-diffusion](https://github.com/openai/guided-diffusion)
- **발표**: 2021년 5월, OpenAI
- **라이선스**: MIT

![Classifier Guidance(ADM) 아키텍처 개요 - U-Net과 분류기 가이던스 메커니즘](figures/architecture.png)
*Figure 1: ADM 아키텍처 전체 구조 - 순전파/역전파 확산 과정, ADM U-Net(554M), 그리고 별도 학습된 분류기의 그래디언트를 score에 결합하는 Classifier Guidance 메커니즘. (Source: arXiv 2105.05233)*

## 아키텍처 상세

### ADM U-Net 개선 사항

ADM은 기존 DDPM U-Net에 체계적인 절제 연구(ablation study)를 통해 최적의 설계를 도출하였다:

| 구성 요소 | DDPM (기존) | ADM (개선) |
|----------|-----------|----------|
| 파라미터 수 | ~114M | 554M (256×256) |
| 어텐션 해상도 | 16×16만 | 8, 16, 32 픽셀 |
| 헤드당 채널 수 | 가변 | 64 고정 |
| 정규화 | Group Norm | Adaptive Group Norm (AdaGN) |
| 잔차 블록 | 일반 ResBlock | BigGAN 스타일 ResBlock |
| 업/다운샘플링 | Stride Conv | 학습된 업/다운샘플 |

![U-Net 아키텍처 절제 연구 - 각 개선 사항의 FID 기여도](figures/fig_2_1.png)
*Figure 2: 아키텍처 절제 연구 - 채널 수 증가, 해상도 변경, 멀티해상도 어텐션, BigGAN 업/다운샘플링 등 각 개선의 FID 기여도를 학습 시간 대비 비교. 모든 개선을 조합한 모델(분홍색)이 최저 FID 달성. (Source: arXiv 2105.05233)*

### Adaptive Group Normalization (AdaGN)

AdaGN은 타임스텝과 클래스 임베딩 정보를 모든 레이어에 효과적으로 주입하는 핵심 기법이다:

$$\text{AdaGN}(h, y) = y_s \cdot \text{GroupNorm}(h) + y_b$$

여기서 $y_s$와 $y_b$는 타임스텝 임베딩과 클래스 임베딩의 결합으로부터 선형 변환으로 생성된다.

### Classifier Guidance 수학적 정의

Classifier Guidance는 베이즈 정리를 활용하여 조건부 score를 분해한다:

$$\nabla_{\mathbf{x}_t} \log p(\mathbf{x}_t | y) = \nabla_{\mathbf{x}_t} \log p(\mathbf{x}_t) + \nabla_{\mathbf{x}_t} \log p_\phi(y | \mathbf{x}_t)$$

가이던스 스케일 $s$를 도입하면:

$$\nabla_{\mathbf{x}_t} \log p_s(\mathbf{x}_t | y) = \nabla_{\mathbf{x}_t} \log p(\mathbf{x}_t) + s \cdot \nabla_{\mathbf{x}_t} \log p_\phi(y | \mathbf{x}_t)$$

$s > 1$로 설정하면 분류기 그래디언트를 증폭하여 특정 클래스에 대한 샘플 품질(IS)을 높이는 대신 다양성(FID)을 희생한다. 이 트레이드오프를 추론 시간에 자유롭게 조절할 수 있다.

![분류기 스케일 변화에 따른 생성 이미지 변화](figures/fig_20.jpg)
*Figure 3: 분류기 스케일 효과 - 스케일 0.0(좌)에서 5.5(우)로 증가시킬 때 생성 이미지의 변화. 스케일이 커질수록 클래스 충실도가 높아지지만 다양성이 감소하는 트레이드오프를 시각적으로 확인. (Source: arXiv 2105.05233)*

### 노이즈 분류기 (Noisy Classifier)

별도로 학습된 분류기 $p_\phi(y | \mathbf{x}_t)$는 각 타임스텝 $t$에서의 노이즈가 추가된 이미지에 대해 분류 정확도를 유지하도록 학습된다. 이 분류기는 U-Net의 다운샘플링 경로와 유사한 아키텍처를 사용하며, 어텐션 풀링으로 최종 분류를 수행한다.

## 핵심 혁신

1. **GAN 능가의 역사적 증명**: 확산 모델이 ImageNet 생성에서 FID 기준으로 BigGAN-deep을 최초로 능가하였다. 이는 확산 모델 연구의 방향을 결정적으로 전환시킨 사건이다.
2. **Adaptive Group Normalization**: 조건부 정보를 모든 레이어에 효과적으로 주입하는 범용적 기법으로, 이후 DiT, SD3 등에서 AdaLN-Zero로 발전하였다.
3. **FID-IS 트레이드오프 제어**: 가이던스 스케일 $s$ 하나로 품질과 다양성의 균형을 추론 시간에 조절할 수 있음을 증명하였다.
4. **체계적 설계 공간 탐색**: U-Net 아키텍처의 각 구성 요소를 독립적으로 분석하여 최적 설계를 도출하는 방법론을 제시하였다.

## 벤치마크/성능

| 모델 | 해상도 | FID (↓) | IS (↑) | Precision | Recall |
|------|-------|---------|--------|-----------|--------|
| BigGAN-deep | 256×256 | 6.95 | 198.2 | 0.87 | 0.28 |
| ADM (Classifier Guidance 없이) | 256×256 | 10.94 | 100.98 | 0.69 | 0.63 |
| ADM + CG ($s=1.0$) | 256×256 | 4.59 | 186.70 | 0.82 | 0.52 |
| ADM + CG | 512×512 | 7.72 | 172.71 | - | - |
| ADM + CG + Upsampler | 256×256 | **3.94** | **215.84** | - | - |

ADM + Classifier Guidance가 BigGAN-deep의 FID 6.95를 4.59로 크게 능가하며, 업샘플러를 추가하면 3.94까지 낮아진다. Recall(다양성)은 GAN 대비 월등히 높아 모드 커버리지가 우수하다.

![Precision-Recall 트레이드오프 - BigGAN-deep vs Classifier Guidance](figures/fig_12_1.png)
*Figure 4: Precision-Recall 트레이드오프 - BigGAN-deep(주황색)은 truncation 조절 시 Precision-Recall 곡선이 제한적인 반면, Classifier Guidance(파란색)는 더 넓은 범위에서 우월한 트레이드오프를 달성. (Source: arXiv 2105.05233)*

## 관련 모델 비교

| 특성 | ADM + CG | BigGAN-deep | DDPM | CFG |
|------|---------|------------|------|-----|
| 생성 방식 | 확산 + 분류기 | GAN | 확산 (무조건부) | 확산 (내재적) |
| 외부 모델 필요 | 분류기 필요 | 불필요 | 불필요 | 불필요 |
| FID (256×256) | 4.59 | 6.95 | 10.94 | **2.43** (128) |
| 학습 안정성 | 높음 | 불안정 | 높음 | 높음 |
| 발표 연도 | 2021 | 2019 | 2020 | 2022 |

## 학습 상세

- **데이터셋**: ImageNet (1,281,167 이미지, 1000 클래스)
- **해상도**: 128×128, 256×256, 512×512
- **학습 스텝**: 100만 ~ 150만 스텝
- **샘플링 스텝**: 250 스텝 (기본)
- **분류기**: 별도로 동일 노이즈 수준에서 사전학습
- **하드웨어**: 대규모 GPU 클러스터 (V100/A100)

## 실무 활용

### 1. 고품질 클래스 조건부 생성

ImageNet 클래스 조건부 이미지 생성에서 가이던스 스케일을 조절하여 사실성과 다양성의 균형을 맞출 수 있다.

### 2. 확산 모델 아키텍처 설계 가이드

ADM의 절제 연구 결과는 새로운 확산 모델을 설계할 때 참고하는 표준 가이드라인이 되었다. 어텐션 해상도 확장, AdaGN, 잔차 블록 설계 등이 이후 모델들에 직접 활용되었다.

### 3. Score 기반 조건부 생성의 프레임워크

Classifier Guidance의 score 분해 개념은 이후 CFG, DPS(Diffusion Posterior Sampling), 이미지 복원 등 다양한 분야에서 확산 모델의 조건부 생성 이론의 기초가 되었다.

## 한계 및 전망

### 한계

1. **별도 분류기 학습 필요**: 노이즈 환경에서 동작하는 분류기를 별도로 학습·유지해야 하며, 새로운 조건 유형마다 새로운 분류기가 필요하다.
2. **클래스 라벨 한정**: 텍스트나 연속적 조건에는 직접 적용이 어렵다.
3. **그래디언트 불일치**: 분류기의 그래디언트 방향이 지각적 품질 향상 방향과 완전히 일치하지 않을 수 있다.

### 후속 발전

- **Classifier-Free Guidance (2022)**: 분류기 없이 동일 효과를 달성하여 ADM+CG를 대체
- **GLIDE (2021)**: CFG를 텍스트-이미지 생성에 최초 적용
- **DiT (2022)**: ADM의 U-Net을 Transformer로 대체하여 스케일링 법칙 발견

![ImageNet 512x512에서의 최고 품질 생성 샘플 (FID 3.85)](figures/fig_1.jpg)
*Figure 5: 최고 품질 생성 결과 - ADM + Classifier Guidance + Upsampler로 생성한 ImageNet 512x512 샘플(FID 3.85). 확산 모델이 GAN을 최초로 능가한 역사적 결과물. (Source: arXiv 2105.05233)*

ADM과 Classifier Guidance는 확산 모델이 GAN을 능가할 수 있음을 최초로 증명한 역사적 연구로, 이후 텍스트-이미지 생성 혁명의 이론적 토대를 마련하였다.

## 관련 문서

- [[ddpm|DDPM (Denoising Diffusion Probabilistic Models)]] - 발전 기반
- [[cfg|Classifier-Free Guidance (CFG)]] - 후속 모델
- [[glide|GLIDE]] - 후속 모델
