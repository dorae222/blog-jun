# ControlNet: 공간 조건 제어 확산 모델

## 개요

ControlNet은 2023년 Stanford University의 Lvmin Zhang 등이 발표한 연구로, 사전학습된 확산 모델에 엣지 맵, 깊이 맵, 포즈 스켈레톤, 세그멘테이션 맵 등 다양한 공간적 조건(spatial condition)을 추가하는 경량 어댑터 아키텍처이다. 텍스트 프롬프트만으로는 구체적인 구도, 자세, 레이아웃을 정밀하게 제어하기 어렵다는 한계를 해결하였다.

- **논문**: [Adding Conditional Control to Text-to-Image Diffusion Models](https://arxiv.org/abs/2302.05543)
- **코드**: [lllyasviel/ControlNet](https://github.com/lllyasviel/ControlNet)
- **발표**: 2023년 2월, Stanford University
- **라이선스**: Apache 2.0

## 아키텍처 상세

### 핵심 설계: Trainable Copy + Zero Convolution

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

### Zero Convolution의 원리

Zero Convolution은 학습 초기 ControlNet의 출력이 정확히 0이 되게 하여 원본 확산 모델의 사전학습된 표현을 완전히 보존한다:

$$\mathcal{Z}(x; \{W_z = 0, b_z = 0\}) = 0 \quad \text{(초기)}$$

학습이 진행되면 역전파를 통해 $W_z$와 $b_z$가 점진적으로 업데이트되며, 조건 정보가 원본 모델에 점차 통합된다. 이 설계 덕분에 학습이 매우 안정적이며, 학습 초기부터 생성 품질이 유지된다.

### 조건 이미지 전처리

조건 이미지 $c$는 소형 합성곱 네트워크(4개의 Conv+ReLU 레이어)를 거쳐 U-Net의 특성 맵 차원으로 투영된다. 이 전처리 네트워크는 ControlNet과 함께 학습된다.

### 다중 ControlNet 합산

여러 ControlNet을 동시에 적용할 수 있다. 예를 들어 Canny Edge ControlNet과 Depth ControlNet을 합산하면 엣지와 깊이를 동시에 제어할 수 있다:

$$y_c = \mathcal{F}(x; \Theta) + \sum_i w_i \cdot \mathcal{Z}_i(\cdot)$$

## 핵심 혁신

1. **사전학습 보존**: Zero Convolution으로 원본 확산 모델의 품질을 훼손 없이 조건을 추가한다.
2. **소규모 데이터 학습**: 수만 장의 조건-이미지 쌍만으로도 효과적인 ControlNet을 학습할 수 있다.
3. **범용 어댑터 구조**: Canny Edge, HED, Depth, OpenPose, Scribble, Normal Map, Segmentation 등 거의 모든 공간 조건에 적용 가능하다.
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

| 특성 | ControlNet | T2I-Adapter | IP-Adapter | LoRA |
|------|-----------|-------------|------------|------|
| 조건 유형 | 공간 맵 | 공간 맵 | 이미지 참조 | 스타일/주제 |
| 추가 파라미터 | ~860M | ~80M | ~22M | ~4M |
| 사전학습 보존 | Zero Conv | 경량 연결 | Cross-Attn | 저랭크 분해 |
| 학습 비용 | 중간 | 낮음 | 낮음 | 낮음 |
| 정밀도 | 매우 높음 | 높음 | 중간 | N/A |

## 학습 상세

- **기반 모델**: SD 1.5 (860M) 또는 SD 2.1 (865M)
- **학습 데이터**: 조건별 독립 구축 (Canny: OpenCV, Depth: MiDaS, Pose: OpenPose)
- **데이터 규모**: 수만 ~ 수십만 쌍
- **하드웨어**: 단일 NVIDIA RTX 3090에서 수일 내 학습 완료
- **CFG 적용**: 조건부·비조건부 예측 모두에 ControlNet 적용

## 실무 활용

### 1. 정밀 구도 제어 이미지 생성

건축 렌더링, 제품 디자인, 패션 디자인 등에서 정확한 구도와 레이아웃을 지정하여 이미지를 생성한다. Depth ControlNet으로 3D 공간감을, Canny Edge로 외곽선을 제어한다.

### 2. 포즈 기반 캐릭터 생성

OpenPose ControlNet을 활용하면 특정 자세의 인물 이미지를 텍스트 프롬프트와 함께 생성할 수 있다. 게임 캐릭터, 일러스트, 광고 이미지 제작에 활용된다.

### 3. 스케치→이미지 변환

Scribble ControlNet으로 간단한 손그림을 고품질 이미지로 변환하는 워크플로우를 구성할 수 있다. 아이디어 시각화, 컨셉 아트 제작에 유용하다.

## 한계 및 전망

### 한계

1. **추가 파라미터 부담**: 인코더 전체를 복사하므로 약 860M의 추가 파라미터가 필요하다.
2. **모델별 재학습**: 기반 모델이 바뀌면 ControlNet도 재학습이 필요하다.
3. **조건 정확도 한계**: 매우 복잡한 조건(예: 정확한 손가락 수)은 여전히 완벽하지 않다.

### 후속 발전

- **ControlNet-XS**: 파라미터 효율을 높인 경량 ControlNet
- **Multi-ControlNet**: 여러 조건의 동시 제어
- **ControlNet for SDXL/SD3**: 최신 모델에 대한 ControlNet 확장
- **IP-Adapter + ControlNet**: 참조 이미지 + 공간 조건의 결합

ControlNet은 생성 AI 이미지의 제어 가능성을 크게 향상시킨 핵심 어댑터 아키텍처로, Stable Diffusion 생태계의 필수 구성 요소로 자리잡았다.

### 기술적 의의

ControlNet의 Zero Convolution 아이디어는 사전학습된 모델에 새로운 기능을 안전하게 추가하는 범용적 패턴으로, 이후 IP-Adapter, T2I-Adapter, AnimateDiff 등 다양한 어댑터 아키텍처에 영감을 주었다. 특히 '원본 모델을 건드리지 않으면서 기능을 확장한다'는 설계 철학은 대규모 사전학습 모델 시대에 매우 실용적인 접근법이다. 커뮤니티에서 수백 종의 커스텀 ControlNet이 학습·공유되면서 생성 AI 생태계의 핵심 인프라가 되었으며, ComfyUI와 Automatic1111 WebUI에서의 지원으로 비전문가도 쉽게 활용할 수 있게 되었다.

## 관련 문서

- [[ldm|LDM (Latent Diffusion Models)]] — 발전 기반
