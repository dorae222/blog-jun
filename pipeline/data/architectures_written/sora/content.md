# Sora: 시공간 패치 기반 비디오 생성 확산 트랜스포머

**OpenAI** · **2024-02-15** · **Diffusion** · **Proprietary**

## 개요

Sora는 2024년 2월 OpenAI가 발표한 텍스트-비디오 생성 모델로, DiT(Diffusion Transformer) 아키텍처를 영상 생성에 최초로 대규모 적용하여 최대 60초의 1080p 고해상도 비디오를 생성할 수 있음을 시연한 혁신적 연구이다. Sora의 등장은 비디오 생성 AI 분야의 분수령이 되었다. 기존의 비디오 생성 모델들(Make-A-Video, Imagen Video 등)은 짧은 클립(수 초)에서 제한된 해상도의 영상만 생성할 수 있었으나, Sora는 장편, 고해상도, 물리적으로 그럴듯한 비디오 생성이 가능함을 보여주었다.

Sora의 핵심 기술적 기여는 비디오를 **시공간 패치(spacetime patch)**로 분할하여 처리하는 방식이다. ViT(Vision Transformer)가 이미지를 2D 패치로 분할하여 처리하듯, Sora는 비디오를 3D 패치(시간 x 높이 x 너비)로 분할하여 1D 토큰 시퀀스로 전개한다. 비디오 프레임 시퀀스를 Video VAE로 잠재 공간에 인코딩한 뒤, 시간 축과 공간 축을 함께 묶은 3D 패치(예: 시간 2프레임 x 공간 16x16 픽셀)로 분할한다. 이 토큰 시퀀스에 DiT의 Full Self-Attention을 적용하면 장거리 시공간 의존성을 직접 포착할 수 있다.

이 접근법의 핵심 장점은 임의의 해상도, 종횡비, 지속 시간의 비디오를 동일한 모델로 처리 가능하다는 것이다. 패치 크기와 시간 스트라이드를 조절하여 다양한 형식의 비디오를 유연하게 다룰 수 있다. OpenAI는 기술 보고서에서 Sora를 "세계 시뮬레이터(world simulator)"로 포지셔닝하며, 비디오 생성 분야에 Transformer 스케일링 법칙이 적용됨을 시사하였다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

### 시공간 패치 토큰화

Sora의 파이프라인은 5단계로 구성된다:

1. **Video VAE 압축**: 입력 비디오를 시공간 VAE로 잠재 공간에 압축. 공간적으로 8x, 시간적으로 약 4x 다운샘플링
2. **3D 패치 분할**: 잠재 비디오를 $p \times p \times f$ 크기의 시공간 패치로 분할하여 1D 시퀀스 구성
3. **선형 임베딩 + 위치 인코딩**: 각 패치를 선형 변환으로 $d$-차원 토큰으로 변환하고 시공간 위치 인코딩 적용
4. **DiT 블록 처리**: Multi-Head Self-Attention + FFN + adaLN-Zero 블록으로 노이즈 예측
5. **VAE 디코딩**: VAE 디코더로 잠재 공간에서 픽셀 공간으로 복원

### DiT 블록과 조건부 생성

각 DiT 블록은 다음과 같이 구성된다:

$$h' = h + \gamma_1(c) \odot \text{Attn}(\alpha_1(c) \odot \text{LN}(h) + \beta_1(c))$$
$$\text{out} = h' + \gamma_2(c) \odot \text{FFN}(\alpha_2(c) \odot \text{LN}(h') + \beta_2(c))$$

여기서 $\alpha, \beta, \gamma$는 adaLN-Zero 파라미터로 조건 $c$에서 생성된다. 타임스텝 임베딩이 이 조건 벡터의 핵심 구성요소이며, 텍스트 조건은 T5 또는 GPT-4 기반 텍스트 인코더를 통해 Cross-Attention 또는 AdaLN으로 주입된다.

확산 과정의 학습 목표는 표준적인 노이즈 예측이다:

$$\mathcal{L} = \mathbb{E}_{t, \mathbf{z}_0, \boldsymbol{\epsilon}}\left[\|\boldsymbol{\epsilon} - \boldsymbol{\epsilon}_\theta(\mathbf{z}_t, t, c_{\text{text}})\|^2\right]$$

### 프롬프트 확장

GPT-4를 활용한 프롬프트 확장은 Sora의 중요한 구성요소이다. 사용자가 짧은 텍스트 프롬프트를 제공하면, GPT-4가 이를 비디오 설명에 적합한 상세한 프롬프트로 변환한다. 이 과정은 카메라 동작, 조명, 물체 배치, 동작 시퀀스 등 비디오 생성에 필요한 세부 정보를 자동으로 추가한다.

### 세계 시뮬레이터로서의 역할

기술 보고서에 따르면, 대규모 비디오 데이터로 학습된 Sora는 물리 법칙에 부합하는 움직임(중력, 충돌, 유체 역학)과 카메라 동작, 복잡한 장면 전환을 구현한다. 이는 모델이 단순히 통계적 패턴을 학습하는 것을 넘어, 물리적 세계의 인과적 구조를 어느 정도 내재화하고 있음을 시사한다.

## 핵심 혁신

Sora의 핵심 혁신은 세 가지이다. 첫째, 시공간 패치 토큰화를 통해 비디오를 NLP의 토큰 시퀀스처럼 처리함으로써 Transformer의 스케일링 법칙을 비디오 생성에 적용할 수 있게 하였다. 둘째, 임의의 해상도, 종횡비, 지속 시간을 하나의 모델로 처리하는 유연한 아키텍처를 제시하였다. 셋째, 대규모 비디오 데이터 학습이 물리적 세계 모델링으로 이어질 수 있음을 경험적으로 보여주었다. 이러한 혁신은 CogVideoX, HunyuanVideo, Runway Gen-4 등 수많은 후속 모델들의 방향을 제시하였다.

## 벤치마크/성능

| 모델 | 해상도 | 최대 길이 | 물리 사실성 | 텍스트 정렬 |
|------|--------|---------|-----------|----------|
| Sora | 1080p | 60초 | 높음 | 높음 |
| Runway Gen-2 | 720p | ~4초 | 중간 | 중간 |
| Pika 1.0 | 720p | ~3초 | 중간 | 중간 |
| Make-A-Video | 768p | ~5초 | 낮음 | 중간 |
| Imagen Video | 1280x768 | ~5초 | 중간 | 높음 |

Sora는 2024년 2월 발표 시점에서 해상도, 길이, 물리적 사실성 모든 측면에서 기존 모델들을 크게 능가하였다. 특히 60초 길이의 1080p 비디오 생성은 당시 다른 어떤 모델도 달성하지 못한 수준이었다.

## 학습

학습 데이터, 모델 파라미터 수, 학습 비용 등은 공개되지 않았다. 기술 보고서(Technical Report)만 공개되었으며 학술 논문은 발표되지 않았다. OpenAI ChatGPT Plus/Pro 구독자에게 API 접근이 제공되었다. 2024년 2월 데모 영상으로 공개되었고 동년 12월 일반 서비스가 시작되었다. 학습에는 대규모 인터넷 비디오 데이터와 함께 합성 데이터도 활용된 것으로 추정된다.

## 관련 모델

Sora는 DiT에서 직접 발전하였으며, OpenAI의 후속 모델인 Sora 2(2025)로 이어졌다. 경쟁 모델로 Veo 2/3(Google DeepMind), Runway Gen-4, Kling 2.6(Kuaishou), HunyuanVideo(Tencent) 등이 있다.

## 참고 자료

- [기술 보고서: Video generation models as world simulators](https://openai.com/research/video-generation-models-as-world-simulators)

## 관련 문서

- [[dit|DiT (Diffusion Transformers)]] — 발전 기반
- [[sora-2|Sora 2]] — 후속 모델