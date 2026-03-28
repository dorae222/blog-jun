# ControlNet: 공간 조건 제어 확산 모델

## 개요

ControlNet은 2023년 Stanford University의 Lvmin Zhang 등이 발표한 연구로, 사전학습된 확산 모델에 엣지 맵, 깊이 맵, 포즈 스켈레톤, 세그멘테이션 맵 등 다양한 공간적 조건(spatial condition)을 추가하는 경량 어댑터 아키텍처이다. 텍스트 프롬프트만으로는 구체적인 구도, 자세, 레이아웃을 정밀하게 제어하기 어렵다는 한계를 해결하였다.

- **논문**: [Adding Conditional Control to Text-to-Image Diffusion Models](https://arxiv.org/abs/2302.05543)
- **코드**: [lllyasviel/ControlNet](https://github.com/lllyasviel/ControlNet)
- **발표**: 2023년 2월, Stanford University
- **라이선스**: Apache 2.0

## 아키텍처 상세

다음 다이어그램은 ControlNet의 전체 아키텍처를 상세히 보여준다. Frozen SD U-Net과 Trainable Copy의 연결, Zero Convolution의 원리, 지원되는 조건 유형을 확인할 수 있다.

![ControlNet 전체 아키텍처 다이어그램 - Frozen U-Net, Trainable Copy, Zero Convolution 구조](figures/architecture.png)
*Figure 1: ControlNet 아키텍처 개요 - 사전학습된 SD U-Net(동결)과 학습 가능한 인코더 복사본이 Zero Convolution으로 연결된다. Canny Edge, Depth Map, OpenPose 등 다양한 공간 조건을 지원한다. (Source: Stanford University)*

### 핵심 설계: Trainable Copy + Zero Convolution

아래 그림은 ControlNet의 핵심 설계를 보여준다. 원본 네트워크 블록을 잠그고, 학습 가능한 복사본을 Zero Convolution으로 연결하는 구조이다.

![ControlNet 블록 구조 - 원본 블록 동결, Trainable Copy와 Zero Convolution 연결](figures/fig_2.png)
*Figure 2: ControlNet 블록 설계 - (a) 원본 네트워크 블록을 (b) 동결(locked)하고, 학습 가능한 복사본(trainable copy)을 생성하여 Zero Convolution으로 조건 $c$를 입력하고 출력을 원본에 더한다. (Source: arXiv 2302.05543)*

ControlNet의 아키텍처는 우아하면서도 효과적이다:

1. **원본 U-Net**: 사전학습된 가중치를 완전히 고정(lock)
2. **학습 가능한 복사본**: 인코더 부분만 복사하여 새로운 조건 정보를 처리
3. **Zero Convolution**: 복사본 출력을 원본에 연결하는 1×1 합성곱 (초기 가중치 = 0)

수식으로 표현하면:

$$y_c = \mathcal{F}(x; \Theta) + \mathcal{Z}\left(\mathcal{F}(x + \mathcal{Z}(c; \Theta_{z1}); \Theta_c); \Theta_{z2}\right)$$

여기서:
- $\mathcal{F}(\cdot; \Theta)$: 원본 U-Net 블록 (동결)
- $\mathcal{F}(\cdot; \Theta_c)$: 학습 가능한 복사본 블록
- $\mathcal{Z}(\cdot; \Theta_{z})$: Zero Convolution (1×1 Conv, 초기값 0)
- $c$: 조건 이미지 (엣지 맵, 깊이 맵 등)

| 구성 요소 | 사양 |
|----------|------|
| 기반 모델 | Stable Diffusion 1.5 (860M) |
| ControlNet 추가 파라미터 | ~860M (인코더 복사본) |
| 텍스트 인코더 | CLIP (77 토큰) |
| 어텐션 | Self-Attention + Cross-Attention |
| 정규화 | Group Normalization |
| 조건 입력 해상도 | 512×512 (기본) |

다음은 Stable Diffusion의 U-Net 전체 구조와 ControlNet의 연결 방식을 보여주는 상세도이다. 인코더 블록과 미들 블록의 Trainable Copy가 Zero Convolution을 통해 디코더에 연결된다.

![Stable Diffusion U-Net과 ControlNet 연결 구조 - 인코더 복사본이 Zero Convolution으로 디코더에 연결](figures/fig_3.png)
*Figure 3: SD U-Net + ControlNet 구조 - 좌측이 동결된 원본 SD U-Net(인코더+디코더), 우측이 학습 가능한 인코더 복사본이다. 각 해상도 레벨(64/32/16/8)에서 Zero Convolution으로 연결된다. (Source: arXiv 2302.05543)*

### Zero Convolution의 원리

Zero Convolution은 ControlNet의 가장 핵심적인 설계 요소이다. 일반적으로 사전학습된 모델에 새로운 모듈을 추가하면, 초기 랜덤 가중치로 인해 기존 모델의 출력이 즉시 왜곡된다. ControlNet은 이 문제를 Zero Convolution으로 근본적으로 해결한다.

Zero Convolution은 1x1 합성곱 레이어로, 가중치 $W_z$와 바이어스 $b_z$를 모두 0으로 초기화한다:

$$\mathcal{Z}(x; \{W_z = 0, b_z = 0\}) = 0 \quad \text{(초기)}$$

이 초기화의 수학적 의미를 살펴보면, 학습 초기에 Trainable Copy의 출력이 어떤 값이든 상관없이 Zero Convolution을 통과하면 정확히 0이 된다. 따라서 전체 출력은 원본 모델의 출력과 동일하다:

$$y_c = \mathcal{F}(x; \Theta) + 0 = \mathcal{F}(x; \Theta) \quad \text{(학습 초기)}$$

역전파 과정에서 Zero Convolution의 그래디언트는 다음과 같이 계산된다:

$$\frac{\partial \mathcal{Z}}{\partial W_z} = x, \quad \frac{\partial \mathcal{Z}}{\partial b_z} = 1$$

따라서 입력 $x$가 0이 아닌 한 그래디언트가 존재하며, 학습이 진행됨에 따라 $W_z$와 $b_z$가 점진적으로 업데이트된다. 이 과정에서 조건 정보가 원본 모델에 "서서히 스며드는" 방식으로 통합된다. 이 설계 덕분에 학습이 매우 안정적이며, 학습 초기부터 생성 품질이 유지된다.

ControlNet 논문에서는 이 현상을 **"급격한 수렴(sudden convergence)"**이라고 명명했다. 학습 전체 기간 동안 생성 이미지의 품질이 유지되다가, 특정 시점에서 모델이 갑자기 입력 조건을 따르기 시작한다. 아래 그림이 이 현상을 보여준다.

![ControlNet 급격한 수렴 현상 - 학습 중 특정 시점에서 조건 따르기를 갑자기 학습](figures/fig_4.png)
*Figure 4: 급격한 수렴 현상 - Zero Convolution 덕분에 학습 전체 기간 동안 고품질 이미지를 생성하다가, 특정 시점(6133 스텝)에서 입력 조건을 갑자기 따르기 시작한다. (Source: arXiv 2302.05543)*

### 조건 신호의 주입 경로

ControlNet이 지원하는 공간 조건(Canny Edge, Depth Map, OpenPose 등)은 각각 고유한 전처리 파이프라인을 거쳐 모델에 주입된다. 각 조건 유형별 주입 경로를 상세히 살펴보면:

**Canny Edge**: OpenCV의 Canny 에지 검출기로 원본 이미지에서 에지 맵을 추출한다. 이진 에지 맵(0/255)이 모델에 직접 입력되며, 가장 정밀한 구조 제어를 제공한다. 임계값 조절로 에지 밀도를 제어할 수 있다.

**Depth Map**: MiDaS 또는 Zoe-Depth 모델로 단안 깊이 추정을 수행한다. 연속적인 깊이 값을 가진 그레이스케일 맵으로, 3D 공간감을 제어하는 데 효과적이다.

**OpenPose**: 인체 키포인트(17개 관절)를 검출하여 스켈레톤 맵으로 변환한다. 얼굴과 손 키포인트를 추가로 포함할 수 있으며, 인물 포즈를 직접 지정할 수 있다.

**Segmentation Map**: ADE20K 또는 COCO 세그멘테이션 모델로 의미적 영역을 분할하며, 각 영역에 고유 색상을 할당하여 장면 레이아웃을 제어한다.

### 조건 이미지 전처리

조건 이미지 $c$는 소형 합성곱 네트워크(4개의 Conv+ReLU 레이어, 채널 수 16→32→64→128)를 거쳐 U-Net의 특성 맵 차원(320채널)으로 투영된다. 이 전처리 네트워크는 ControlNet과 함께 학습되며, 조건 유형에 따라 서로 다른 가중치를 학습한다. 전처리 네트워크의 역할은 다양한 형태의 조건 입력(이진 에지, 연속 깊이값, 스켈레톤 좌표 등)을 통일된 특성 공간으로 매핑하는 것이다.

### 다중 ControlNet 합산

여러 ControlNet을 동시에 적용할 수 있다. 예를 들어 Canny Edge ControlNet과 Depth ControlNet을 합산하면 엣지와 깊이를 동시에 제어할 수 있다:

$$y_c = \mathcal{F}(x; \Theta) + \sum_i w_i \cdot \mathcal{Z}_i(\cdot)$$

## 핵심 혁신

1. **사전학습 보존**: Zero Convolution으로 원본 확산 모델의 품질을 훼손 없이 조건을 추가한다.
2. **소규모 데이터 학습**: 수만 장의 조건-이미지 쌍만으로도 효과적인 ControlNet을 학습할 수 있다.
3. **범용 어댑터 구조**: Canny Edge, HED, Depth, OpenPose, Scribble, Normal Map, Segmentation 등 거의 모든 공간 조건에 적용 가능하다. 아래 결과는 프롬프트 없이 다양한 조건만으로 생성한 이미지들이다.

![ControlNet 다양한 조건별 생성 결과 - Canny, Depth, Sketch, HED, Segmentation, Pose 조건으로 프롬프트 없이 생성](figures/fig_7.jpg)
*Figure 5: 다양한 조건별 생성 결과 - Canny Edge, Depth, Sketch, HED, Segmentation, OpenPose 등 7가지 조건으로 텍스트 프롬프트 없이도 의미적으로 일관된 이미지를 생성한다. (Source: arXiv 2302.05543)*
4. **플러그-앤-플레이**: 기존 확산 모델 생태계(LoRA, 커스텀 모델 등)와 자유롭게 조합 가능하다.

## 벤치마크/성능

| 조건 유형 | 정밀도 | 사용자 선호도 | 학습 데이터 규모 |
|----------|--------|------------|--------------|
| Canny Edge | 높음 | 매우 높음 | ~300K |
| Depth (MiDaS) | 높음 | 높음 | ~300K |
| OpenPose | 중간 | 높음 | ~200K |
| Scribble | 중간 | 높음 | ~300K |
| Normal Map | 높음 | 중간 | ~300K |
| Segmentation | 높음 | 중간 | ~300K |

인간 평가에서 ControlNet이 PITI, Sketch-Guided Diffusion 등 기존 조건부 생성 방법 대비 압도적으로 선호되었다.

## 관련 모델 비교

### 조건부 생성 접근법 상세 비교

ControlNet 이후 다양한 조건부 생성 어댑터가 등장했다. 각 접근법의 철학과 트레이드오프를 상세히 비교한다.

**T2I-Adapter** (Tencent ARC, 2023): ControlNet과 동일하게 공간 조건 맵을 처리하지만, 원본 모델을 복사하지 않고 경량 어댑터 모듈(~80M)만 추가한다. 각 해상도 레벨에서 특성 맵을 추출하여 U-Net의 중간 특성에 더하는 방식이다. 파라미터 효율성은 높지만, ControlNet 대비 조건 따르기 정밀도가 다소 낮다. 특히 복잡한 구조를 가진 조건(세밀한 에지, 복잡한 포즈)에서 차이가 두드러진다.

**IP-Adapter** (Tencent AI Lab, 2023): 공간 조건이 아닌 **참조 이미지** 기반 스타일/콘텐츠 전이를 수행한다. CLIP 이미지 인코더로 참조 이미지의 특성을 추출한 후, 분리된 Cross-Attention 레이어를 통해 U-Net에 주입한다. ~22M의 매우 적은 추가 파라미터만 필요하며, ControlNet과 결합하면 "참조 이미지 스타일 + 공간 구조 제어"를 동시에 달성할 수 있다.

**LoRA (Low-Rank Adaptation)**: 엄밀히는 조건부 생성 방법이 아닌 파인튜닝 기법이지만, 특정 스타일이나 주제를 학습시키는 데 널리 사용된다. ~4M의 극소 파라미터로 모델의 어텐션 가중치를 미세 조정하며, ControlNet과 함께 사용하여 "구조 제어 + 스타일 적용"을 달성하는 것이 일반적이다.

| 특성 | ControlNet | T2I-Adapter | IP-Adapter | LoRA |
|------|-----------|-------------|------------|------|
| 조건 유형 | 공간 맵 | 공간 맵 | 이미지 참조 | 스타일/주제 |
| 추가 파라미터 | ~860M | ~80M | ~22M | ~4M |
| 사전학습 보존 | Zero Conv | 경량 연결 | Cross-Attn | 저랭크 분해 |
| 학습 비용 | 중간 | 낮음 | 낮음 | 낮음 |
| 정밀도 | 매우 높음 | 높음 | 중간 | N/A |
| 조합 가능성 | 다른 CN과 합산 | CN과 호환 | CN/LoRA 결합 | CN/IP와 결합 |

## 학습 상세

ControlNet의 학습 방법론은 사전학습된 모델의 지식을 최대한 보존하면서 새로운 조건 제어 능력을 추가하는 것이 핵심이다.

### 학습 전략: Locked Copy + Trainable Copy

학습 과정에서 원본 Stable Diffusion U-Net은 완전히 고정(locked)된다. 인코더 블록과 미들 블록만 복사하여 Trainable Copy를 생성하며, 이 복사본과 Zero Convolution 레이어만 학습 대상이다. 디코더는 복사하지 않으므로 메모리 비용이 전체 모델 복사 대비 약 50% 절감된다.

학습 목표 함수는 표준 확산 모델의 노이즈 예측 손실에 조건 $c$를 추가한 형태이다:

$$\mathcal{L} = \mathbb{E}_{z_0, t, c_t, c, \epsilon \sim \mathcal{N}(0,1)} \left[ \| \epsilon - \epsilon_\theta(z_t, t, c_t, c) \|_2^2 \right]$$

여기서 $c_t$는 텍스트 조건, $c$는 공간 조건이다. 학습 시 50%의 확률로 텍스트 프롬프트를 빈 문자열로 대체하여, 조건 이미지만으로도 의미적으로 일관된 생성이 가능하도록 한다.

- **기반 모델**: SD 1.5 (860M) 또는 SD 2.1 (865M)
- **학습 데이터**: 조건별 독립 구축 (Canny: OpenCV, Depth: MiDaS, Pose: OpenPose)
- **데이터 규모**: 수만 ~ 수십만 쌍
- **하드웨어**: 단일 NVIDIA RTX 3090에서 수일 내 학습 완료
- **CFG 적용**: 조건부·비조건부 예측 모두에 ControlNet 적용
- **학습률**: 기본값 1e-5, 조건별 미세 조정
- **배치 크기**: 4 (그래디언트 누적 사용)

## 실무 활용

### 1. 정밀 구도 제어 이미지 생성

건축 렌더링, 제품 디자인, 패션 디자인 등에서 정확한 구도와 레이아웃을 지정하여 이미지를 생성한다. Depth ControlNet으로 3D 공간감을, Canny Edge로 외곽선을 제어한다.

### 2. 포즈 기반 캐릭터 생성

OpenPose ControlNet을 활용하면 특정 자세의 인물 이미지를 텍스트 프롬프트와 함께 생성할 수 있다. 게임 캐릭터, 일러스트, 광고 이미지 제작에 활용된다.

### 3. 스케치→이미지 변환

Scribble ControlNet으로 간단한 손그림을 고품질 이미지로 변환하는 워크플로우를 구성할 수 있다. 아이디어 시각화, 컨셉 아트 제작에 유용하다.

## 커뮤니티 영향과 채택

ControlNet은 학술적 기여를 넘어 생성 AI 커뮤니티에 가장 큰 실질적 영향을 미친 연구 중 하나이다.

**도구 생태계 통합**: 발표 수주 내에 Automatic1111 WebUI와 ComfyUI에 통합되었으며, 이후 모든 주요 Stable Diffusion UI가 ControlNet을 기본 지원하게 되었다. ComfyUI에서는 ControlNet 노드를 자유롭게 조합하여 복잡한 생성 파이프라인을 구성할 수 있다.

**커스텀 모델 폭발적 증가**: Civitai, Hugging Face 등에서 수백 종의 커스텀 ControlNet이 커뮤니티에 의해 학습되고 공유되었다. QR Code ControlNet, Tile ControlNet, Inpaint ControlNet 등 원논문에 없던 새로운 조건 유형이 커뮤니티 주도로 개발되었다.

**산업 채택**: 건축 시각화, 패션 디자인, 게임 컨셉 아트, 광고 이미지 제작 등 전문 영역에서 ControlNet이 표준 워크플로우에 편입되었다. Midjourney, DALL-E 등 폐쇄형 서비스 대비 정밀한 구조 제어가 가능하다는 점이 전문가들에게 높이 평가되었다.

## 한계 및 과제

### 구조적 한계

1. **추가 파라미터 부담**: 인코더 전체를 복사하므로 약 860M의 추가 파라미터가 필요하다. SDXL에서는 이 비용이 더욱 증가하여 약 2.5B의 추가 파라미터가 필요하며, 추론 시 메모리와 속도에 상당한 부담을 준다.
2. **모델별 재학습 필수**: 기반 모델이 바뀌면(SD 1.5 → SDXL → SD3) ControlNet도 전면 재학습이 필요하다. 아키텍처 호환성이 없으므로, 새로운 기반 모델이 등장할 때마다 커뮤니티가 처음부터 ControlNet을 다시 학습해야 한다.
3. **조건 정확도의 근본적 한계**: ControlNet이 제어하는 것은 "구조적 가이드"이지 "픽셀 단위 정밀 제어"가 아니다. 매우 세밀한 구조(정확한 손가락 수, 텍스트 렌더링, 대칭 패턴 등)는 여전히 완벽하지 않다.
4. **조건 간 충돌**: 여러 ControlNet을 동시에 사용할 때, 서로 모순되는 조건이 입력되면 결과가 불안정하다. 가중치 밸런싱이 필요하며, 이는 경험적 조정에 의존한다.
5. **추론 속도 저하**: Trainable Copy의 추가 연산으로 인해 추론 시간이 약 1.5~2배 증가한다. 실시간 응용에는 T2I-Adapter 같은 경량 대안이 더 적합할 수 있다.

### 후속 발전

- **ControlNet-XS**: 파라미터 효율을 높인 경량 ControlNet
- **Multi-ControlNet**: 여러 조건의 동시 제어
- **ControlNet for SDXL/SD3**: 최신 모델에 대한 ControlNet 확장
- **IP-Adapter + ControlNet**: 참조 이미지 + 공간 조건의 결합

ControlNet은 생성 AI 이미지의 제어 가능성을 크게 향상시킨 핵심 어댑터 아키텍처로, Stable Diffusion 생태계의 필수 구성 요소로 자리잡았다.

### 기술적 의의

ControlNet의 Zero Convolution 아이디어는 사전학습된 모델에 새로운 기능을 안전하게 추가하는 범용적 패턴으로, 이후 IP-Adapter, T2I-Adapter, AnimateDiff 등 다양한 어댑터 아키텍처에 영감을 주었다. 특히 '원본 모델을 건드리지 않으면서 기능을 확장한다'는 설계 철학은 대규모 사전학습 모델 시대에 매우 실용적인 접근법이다. 커뮤니티에서 수백 종의 커스텀 ControlNet이 학습·공유되면서 생성 AI 생태계의 핵심 인프라가 되었으며, ComfyUI와 Automatic1111 WebUI에서의 지원으로 비전문가도 쉽게 활용할 수 있게 되었다.

## 관련 문서

- [[ldm|LDM (Latent Diffusion Models)]] - 발전 기반
