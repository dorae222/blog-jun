<!-- infographic-hero -->
![DeiT 핵심 요약](figures/infographic.svg)

*Figure: DeiT 한 장 요약 인포그래픽*

# DeiT: 데이터 효율적 비전 트랜스포머

**Meta/FAIR** · **2021-01-01** · **Vision** · **Apache-2.0**

## 개요

DeiT(Data-efficient Image Transformers)는 2021년 Meta/FAIR의 Hugo Touvron 등이 발표한 비전 트랜스포머 모델로, 대규모 데이터셋 없이도 ViT를 효율적으로 학습할 수 있음을 보여준 획기적인 연구이다. 기존 ViT(Vision Transformer)는 Google이 보유한 JFT-300M(3억 장) 같은 초대규모 비공개 데이터셋에 의존해야만 CNN과 경쟁력 있는 성능을 달성할 수 있었다. ImageNet-1K(128만 장)만으로 ViT를 학습하면 동일 크기의 CNN(예: EfficientNet, RegNet)보다 크게 뒤처지는 한계가 있었으며, 이는 트랜스포머가 CNN의 귀납적 편향(지역성, 평행이동 불변성)을 갖추지 못해 소규모 데이터에서 과적합에 취약하기 때문이었다.

DeiT는 이 문제를 두 가지 핵심 전략으로 해결한다. 첫째, 지식 증류(Knowledge Distillation) 토큰을 트랜스포머 아키텍처에 직접 통합하여, CNN 교사 모델의 귀납적 편향(inductive bias)을 학생 트랜스포머 모델에 전달한다. 둘째, Rand-Augment, Mixup, CutMix, Random Erasing, Repeated Augmentation, Stochastic Depth 등 강력한 데이터 증강과 정규화 기법을 체계적으로 조합하여 소규모 데이터에서의 과적합을 효과적으로 방지한다. 이 전략의 결합으로 DeiT-B는 ImageNet-1K에서 top-1 정확도 83.1%를 달성하였으며, 증류 버전(DeiT-B⚗↑384)은 85.2%라는 인상적인 성능을 기록하여 동일 데이터 조건에서 ViT-B(77.9%)를 5%p 이상 앞서고, 훨씬 큰 ViT-L(307M, 76.5%)마저 능가하였다. DeiT의 학습 레시피는 이후 비전 트랜스포머 학습의 사실상 표준이 되었으며, Swin Transformer, DINOv2, BEiT 등 후속 모델들도 이 레시피를 기반으로 발전하였다.

![DeiT 아키텍처 - ViT에 증류 토큰을 추가하여 CNN 교사 모델의 귀납적 편향을 전달하는 구조](figures/architecture.svg)

*Figure 1: DeiT 아키텍처 - ViT 구조에 증류 토큰(distillation token)을 추가하여 CNN 교사 모델의 지식을 전달하고, 강력한 데이터 증강으로 ImageNet-1K만으로도 경쟁력 있는 성능을 달성한다.*

아래 그림은 ImageNet에서의 처리량(이미지/초) 대비 정확도를 비교한 것으로, DeiT가 EfficientNet과 동등한 성능을 적은 데이터로 달성함을 보여준다.

![ImageNet에서 DeiT vs EfficientNet vs ViT 처리량-정확도 비교](figures/fig_1_1.png)
*Figure 1: ImageNet 처리량-정확도 비교 - DeiT-B는 ViT-B와 동일한 아키텍처이지만 데이터 부족 환경에 맞는 학습 전략으로 성능을 크게 향상시켰다. 증류 버전(기호 표시)은 EfficientNet과 경쟁하는 정확도를 달성한다. (Source: Touvron et al., 2021)*

## 아키텍처 상세

DeiT의 아키텍처는 ViT와 거의 동일하되, 하나의 결정적 차이점이 존재한다: **증류 토큰(distillation token)**의 도입이다. 이 작은 변경이 데이터 효율성에 큰 영향을 미친다.

### 패치 임베딩과 토큰 구조

입력 이미지 $x \in \mathbb{R}^{H \times W \times 3}$를 $16 \times 16$ 크기의 패치로 분할하고, 각 패치를 선형 투영 행렬 $\mathbf{E} \in \mathbb{R}^{(P^2 \cdot C) \times D}$를 통해 768차원 임베딩 벡터로 변환한다. $224 \times 224$ 입력의 경우 $N = (224/16)^2 = 196$개의 패치가 생성된다. 기존 ViT의 학습 가능한 [CLS] 토큰 외에 **학습 가능한 증류 토큰**을 시퀀스에 추가하여, 총 $N + 2 = 198$개의 토큰으로 시퀀스를 구성한다:

$$\mathbf{z}_0 = [\mathbf{x}_\text{cls};\; \mathbf{x}_\text{distill};\; \mathbf{x}_1\mathbf{E};\; \cdots;\; \mathbf{x}_N\mathbf{E}] + \mathbf{E}_\text{pos}$$

[CLS] 토큰은 기존처럼 분류 손실(ground truth label)을 학습하고, 증류 토큰은 CNN 교사 모델의 출력을 학습 목표로 삼는다. 12개의 트랜스포머 인코더 레이어(각각 12-head Multi-Head Self-Attention, GELU 활성화, LayerNorm 정규화)를 거치면서 셀프 어텐션을 통해 두 토큰이 상호작용하며, 모델은 교사의 귀납적 편향과 실제 레이블 정보를 동시에 학습한다. 추론 시에는 [CLS] 토큰과 증류 토큰의 출력을 평균내어 최종 예측을 생성한다.

| 사양 | DeiT-Ti | DeiT-S | DeiT-B |
|------|---------|--------|--------|
| 히든 차원 $D$ | 192 | 384 | 768 |
| 레이어 수 $L$ | 12 | 12 | 12 |
| 어텐션 헤드 $h$ | 3 | 6 | 12 |
| MLP 비율 | 4× | 4× | 4× |
| 파라미터 | 5M | 22M | 86M |
| 패치 크기 | 16×16 | 16×16 | 16×16 |
| 시퀀스 길이 | 198 | 198 | 198 |

아래 그림은 증류 토큰이 아키텍처에 통합되는 과정을 보여준다. class 토큰과 별도로 distillation 토큰이 셀프 어텐션을 통해 패치 토큰들과 상호작용한다.

![DeiT 증류 절차 - class 토큰과 distillation 토큰이 셀프 어텐션으로 상호작용](figures/fig_2.png)
*Figure 2: DeiT 증류 절차 - class 토큰(좌)은 실제 레이블을, distillation 토큰(우)은 교사 모델의 예측을 학습 목표로 삼는다. 두 토큰 모두 셀프 어텐션 레이어를 통해 패치 토큰과 상호작용하며 역전파로 학습된다. (Source: Touvron et al., 2021)*

### 지식 증류 방식

DeiT는 두 가지 증류 방식을 실험하였다:

**소프트 증류(Soft Distillation)**: 교사 모델의 소프트맥스 출력 분포와 학생 모델의 출력 분포 간 KL 발산(Kullback-Leibler Divergence)을 최소화한다. 온도 파라미터 $\tau$를 통해 확률 분포를 부드럽게 만들어 교사의 불확실성 정보까지 전달한다:

$$\mathcal{L}_\text{soft} = (1-\lambda)\mathcal{L}_\text{CE}(y, \psi(Z_s)) + \lambda \tau^2 \text{KL}\!\left(\psi\!\left(\frac{Z_t}{\tau}\right),\; \psi\!\left(\frac{Z_s}{\tau}\right)\right)$$

**하드 증류(Hard Distillation)**: 교사 모델의 예측 클래스(argmax)를 하드 레이블로 사용하여, 증류 토큰의 손실을 별도의 교차 엔트로피로 계산한다. [CLS] 토큰은 ground truth를, 증류 토큰은 교사의 하드 예측을 각각 학습한다:

$$\mathcal{L}_\text{hard} = \frac{1}{2}\mathcal{L}_\text{CE}(y, \psi(Z_s^\text{cls})) + \frac{1}{2}\mathcal{L}_\text{CE}(y_t, \psi(Z_s^\text{distill}))$$

여기서 $y_t = \arg\max_c Z_t(c)$는 교사의 하드 예측이다. 실험 결과, 하드 증류가 소프트 증류보다 일관되게 우수한 성능을 보였다. 이는 하드 레이블이 label smoothing과 유사한 정규화 효과를 제공하며, 데이터 증강과 결합할 때 교사의 예측이 증강된 이미지에 대한 추가적인 감독 신호로 작용하기 때문으로 분석된다.

### 셀프 어텐션 메커니즘

DeiT는 표준 Multi-Head Self-Attention을 사용한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\!\left(\frac{QK^\top}{\sqrt{d_k}}\right)V$$

각 헤드에서 $Q = XW_Q$, $K = XW_K$, $V = XW_V$로 투영하며, 헤드 차원은 $d_k = D/h$이다. 흥미로운 관찰 결과, 학습이 진행됨에 따라 [CLS] 토큰과 증류 토큰이 서로 다른 어텐션 패턴을 발전시키며, 이 둘의 코사인 유사도가 낮아 각각 보완적인 표현을 학습하는 것으로 확인되었다. 이는 두 토큰의 평균이 앙상블 효과를 제공하는 이유를 설명한다.

## 핵심 혁신

1. **증류 토큰 아키텍처**: 기존의 지식 증류가 손실 함수 수준에서만 적용되는 것과 달리, DeiT는 토큰 수준에서 증류를 아키텍처에 직접 통합하였다. 증류 토큰과 [CLS] 토큰이 셀프 어텐션을 통해 상호작용하면서도 서로 다른 표현을 학습하게 되어, 추론 시 두 토큰의 출력을 평균내면 앙상블 효과를 얻을 수 있다. 이 접근법은 토큰 기반 증류라는 새로운 방법론을 제시하였다.

2. **CNN → Transformer 교차 아키텍처 지식 전달**: RegNetY-16GF(ImageNet top-1 82.9%)를 교사 모델로 사용하여 CNN의 지역적 특징 추출 능력을 트랜스포머에 전달한다. 흥미롭게도 DeiT 교사보다 CNN 교사가 더 효과적인 것으로 밝혀졌는데, 이는 서로 다른 귀납적 편향(CNN의 지역성과 평행이동 불변성 vs Transformer의 전역 어텐션)이 상호 보완적이기 때문이다. 동일 아키텍처 교사 사용 시에는 이미 학생이 가진 편향과 중복되어 효과가 감소한다.

3. **체계적 데이터 증강 레시피**: Rand-Augment, Mixup($\alpha$=0.8), CutMix($\alpha$=1.0), Random Erasing($p$=0.25), Repeated Augmentation, Stochastic Depth($p$=0.1), Label Smoothing($\epsilon$=0.1) 등을 체계적으로 조합한 학습 레시피를 제시하였다. 각 기법의 독립적 기여도를 ablation study로 철저히 검증하여, 비전 트랜스포머 학습의 표준 방법론을 확립하였다. 특히 Repeated Augmentation이 가장 큰 개별 기여(+1.2%p)를 하는 것으로 밝혀졌다.

4. **모델 크기 효율성**: DeiT-B(86M)가 ViT-L(307M)보다 ImageNet-1K에서 더 높은 정확도를 달성하며, 파라미터 효율성 측면에서 매우 뛰어남을 보였다. 이는 적절한 학습 전략이 모델 크기 증가보다 더 효과적일 수 있음을 시사한다.

## 벤치마크/성능

| 모델 | ImageNet top-1 | 사전학습 데이터 | 파라미터 | 해상도 | GPU 학습 시간 |
|------|---------------|----------------|---------|--------|-------------|
| DeiT-Ti | 72.2% | ImageNet-1K | 5M | 224 | ~10h |
| DeiT-S | 79.8% | ImageNet-1K | 22M | 224 | ~20h |
| DeiT-B | 81.8% | ImageNet-1K | 86M | 224 | ~53h |
| DeiT-B⚗ (하드 증류) | 83.4% | ImageNet-1K | 86M | 224 | ~53h |
| DeiT-B⚗↑384 | 85.2% | ImageNet-1K | 86M | 384 | ~53h+FT |
| ViT-B/16 | 77.9% | ImageNet-1K | 86M | 224 | - |
| ViT-L/16 | 76.5% | ImageNet-1K | 307M | 224 | - |
| ViT-B/16 | 84.2% | JFT-300M | 86M | 384 | TPU-v3 |
| EfficientNet-B7 | 84.3% | ImageNet-1K | 66M | 600 | - |
| RegNetY-16GF (교사) | 82.9% | ImageNet-1K | 84M | 224 | - |

증류 방식별 학습 곡선을 비교하면, 하드 증류 토큰 방식이 가장 높은 성능을 달성하며 학습 에폭이 증가할수록 지속적으로 개선된다.

![DeiT-B 증류 방식별 학습 에폭에 따른 ImageNet 성능 비교](figures/fig_3.png)
*Figure 3: 증류 방식별 학습 곡선 - 증류 토큰+하드 증류 방식(빨간 실선)이 에폭 증가에 따라 지속적으로 성능이 향상되며, 증류 없는 기본 모델(점선)은 400 에폭 이후 포화된다. 384 해상도 파인튜닝(빨간 점선)은 추가 성능 향상을 달성한다. (Source: Touvron et al., 2021)*

DeiT-B는 동일한 ImageNet-1K 데이터만으로 ViT-B 대비 약 4%p 높은 정확도를 달성하며, 훨씬 큰 ViT-L(307M)보다도 우수한 결과를 보인다. 증류+고해상도 파인튜닝 버전(DeiT-B⚗↑384)은 JFT-300M으로 사전학습한 ViT-B/16(84.2%)을 능가하여, 데이터 효율적 학습의 가능성을 극대화하였다.

## 학습

ImageNet-1K(128만 이미지, 1000 클래스)만을 사용하여 300 에폭 학습한다. 외부 데이터나 추가적인 사전학습 없이 순수하게 ImageNet-1K만으로 경쟁력 있는 성능을 달성한다는 점이 핵심이다. 주요 하이퍼파라미터는 다음과 같다:

- **옵티마이저**: AdamW ($\beta_1$=0.9, $\beta_2$=0.999)
- **학습률**: 5e-4 (cosine annealing 스케줄, 5 에폭 linear warmup)
- **배치 크기**: 1024
- **Weight decay**: 0.05
- **Stochastic depth**: 0.1 (DeiT-B 기준)
- **Label smoothing**: $\epsilon$ = 0.1
- **교사 모델**: RegNetY-16GF (ImageNet top-1 82.9%, 별도 학습)
- **증류 방식**: Hard distillation (기본)
- **데이터 증강**: Rand-Augment(9, 0.5), Mixup($\alpha$=0.8), CutMix($\alpha$=1.0), Random Erasing($p$=0.25), Repeated Augmentation
- **GPU**: 4×V100 32GB, 약 53시간 (DeiT-B 기준)

파인튜닝 시 384×384 해상도로 업스케일하며, 위치 임베딩은 바이큐빅 보간(bicubic interpolation)으로 $\sqrt{196}=14 \to \sqrt{576}=24$로 적응한다. 고해상도 파인튜닝은 10-30 에폭만으로 충분하다.

## 관련 모델

DeiT는 ViT의 데이터 효율성 문제를 지식 증류와 데이터 증강으로 해결한 선구적 모델이다. 이후 Swin Transformer(윈도우 기반 어텐션으로 계산 효율 개선), DINOv2(자기지도 학습으로 레이블 의존 제거), BEiT(시각 토큰 마스킹으로 사전학습), MAE(마스킹 오토인코더) 등 다양한 비전 트랜스포머 후속 연구에 학습 레시피와 증류 기법 측면에서 직접적인 영향을 주었다. DeiT의 증강 레시피는 비전 트랜스포머 학습의 "표준 레시피"로 자리잡았다.

## 참고 자료

- 논문: [Training data-efficient image transformers & distillation through attention](https://arxiv.org/abs/2012.12877)
- 코드: [github.com/facebookresearch/deit](https://github.com/facebookresearch/deit)

## 관련 문서

- [[vit|An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale]] - 발전 기반