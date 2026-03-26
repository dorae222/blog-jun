# CogVideoX: 오픈소스 텍스트-비디오 생성 모델

## 개요

CogVideoX는 2024년 8월 Tsinghua University와 Zhipu AI가 공동 개발한 오픈소스 텍스트-비디오 생성 모델로, 상업 수준의 비디오 생성 품질을 오픈소스로 제공한 최초의 대규모 모델 중 하나이다. 5B 파라미터 규모의 Expert Adaptive LayerNorm을 사용하는 Full 3D Attention DiT 아키텍처로, 모든 비디오 프레임을 시공간 통합 시퀀스로 처리한다.

- **논문**: [CogVideoX: Text-to-Video Diffusion Models](https://arxiv.org/abs/2408.06072)
- **코드**: [THUDM/CogVideo](https://github.com/THUDM/CogVideo)
- **발표**: 2024년 8월, Tsinghua/Zhipu AI
- **라이선스**: Apache 2.0

## 아키텍처 상세

### 전체 파이프라인

CogVideoX의 파이프라인은 세 가지 핵심 모듈로 구성된다:

1. **3D Video VAE**: 비디오를 잠재 공간으로 압축
2. **Expert AdaLN DiT**: 잠재 공간에서 노이즈 예측
3. **T5-XXL 텍스트 인코더**: 텍스트 조건 임베딩 생성

| 구성 요소 | 사양 |
|----------|------|
| 파라미터 수 | 5B / 2B |
| DiT 블록 수 | 42 |
| 텍스트 인코더 | T5-XXL (동결) |
| 텍스트 토큰 수 | 226 |
| 위치 인코딩 | 3D RoPE (시간+높이+너비) |
| 정규화 | RMSNorm |
| 활성화 함수 | GELU |

### 3D Video VAE

비디오 VAE는 시간 방향 4배, 공간 방향 8배 다운샘플링을 수행한다. 480p 6초 영상(49 프레임)을 $13 \times 60 \times 90 \times 16$ 크기의 잠재 텐서로 변환한다:

$$z = \text{Encoder}_{3D}(x) \in \mathbb{R}^{T/4 \times H/8 \times W/8 \times C}$$

### Expert Adaptive LayerNorm (Expert AdaLN)

CogVideoX의 핵심 혁신은 Expert AdaLN이다. 일반적인 AdaLN이 모든 토큰에 동일한 스케일·시프트를 적용하는 반면, Expert AdaLN은 텍스트 토큰과 비디오 토큰에 서로 다른 스케일·시프트 파라미터를 적용하는 모달리티 특화 정규화를 수행한다:

$$\text{ExpertAdaLN}(h^v, h^t, e) = \begin{cases} \gamma_v(e) \cdot \text{RMSNorm}(h^v) + \beta_v(e) & \text{(비디오 토큰)} \\ \gamma_t(e) \cdot \text{RMSNorm}(h^t) + \beta_t(e) & \text{(텍스트 토큰)} \end{cases}$$

### 텍스트-비디오 시퀀스 결합

Cross-Attention 없이 텍스트와 비디오 토큰을 시퀀스 방향으로 연결하여 단일 Full Self-Attention에서 함께 처리한다:

$$\text{Attention}([h^t; h^v]) = \text{softmax}\left(\frac{Q_{[t;v]} K_{[t;v]}^T}{\sqrt{d}}\right) V_{[t;v]}$$

이 설계는 텍스트↔비디오 양방향 상호작용을 자연스럽게 포착한다.

### 3D RoPE

각 비디오 패치 위치 $(t, h, w)$에 대해 시간·높이·너비 방향의 RoPE를 독립적으로 계산하여 연결한다. 이 설계로 임의 해상도·지속시간 비디오를 외삽 없이 생성 가능하다.

## 핵심 혁신

1. **Full 3D Attention**: 시공간 분리 어텐션 대신 모든 시공간 위치 간의 어텐션을 계산하여 높은 시간적 일관성을 달성한다.
2. **Expert AdaLN**: 모달리티별 독립적인 정규화로 텍스트와 비디오 토큰의 스케일 차이를 효과적으로 관리한다.
3. **Cross-Attention 제거**: 텍스트와 비디오를 시퀀스 결합하여 단일 어텐션으로 처리하는 단순하면서도 효과적인 설계이다.
4. **자동 데이터 파이프라인**: GPT-4V 기반 자동 비디오 캡션 생성과 품질 필터링 파이프라인을 통해 학습 데이터 품질을 체계적으로 향상시켰다.

## 벤치마크/성능

| 모델 | VBench 총점 | 시각 품질 | 시간 일관성 | 텍스트 정렬 |
|------|-----------|----------|-----------|-----------|
| CogVideoX-5B | **81.6** | 높음 | 높음 | 높음 |
| CogVideoX-2B | 79.8 | 중간 | 중간 | 중간 |
| Gen-2 (Runway) | 78.4 | 중간 | 중간 | 중간 |
| Pika 1.0 | 76.2 | 중간 | 낮음 | 중간 |

EvalCrafter, VBench 등 벤치마크에서 공개 시점 기준 오픈소스 모델 중 최상위 성능을 기록하였다.

## 관련 모델 비교

| 특성 | CogVideoX | Sora | HunyuanVideo | Kling |
|------|-----------|------|-------------|-------|
| 파라미터 | 5B | 비공개 | 13B | 비공개 |
| 오픈소스 | Apache 2.0 | 비공개 | Apache 2.0 | 비공개 |
| 해상도 | 480p/720p | 1080p | 720p | 1080p |
| 길이 | 6초 | 60초 | 5초 | 120초 |
| 어텐션 | Full 3D | Full 3D | Dual-Stream | Full 3D |

## 학습 상세

- **데이터셋**: 내부 수집 및 필터링된 비디오-텍스트 쌍
- **캡션 생성**: GPT-4V 기반 자동 캡션 파이프라인
- **학습 전략**: 저해상도→고해상도, 짧은 비디오→긴 비디오 순차 학습
- **텍스트 인코더**: T5-XXL (사전학습 가중치 동결)
- **후속 모델**: CogVideoX-5B-I2V (이미지→비디오), CogVideoX1.5 (고해상도)

## 실무 활용

### 1. 오픈소스 비디오 생성 파이프라인

Apache 2.0 라이선스로 가중치가 공개되어 있어, 자체 서비스 구축이나 미세조정이 가능하다. HuggingFace Diffusers에서 직접 활용 가능하다.

### 2. 이미지-비디오 변환

CogVideoX-5B-I2V 버전을 활용하면 정적 이미지를 입력으로 자연스러운 동작이 있는 비디오를 생성할 수 있다.

### 3. 커스텀 비디오 생성 서비스

LoRA 미세조정을 통해 특정 스타일이나 도메인에 특화된 비디오 생성 모델을 구축할 수 있다.

## 한계 및 전망

### 한계

1. **해상도 제한**: 480p/720p 수준으로 상업 모델(1080p/4K) 대비 해상도가 낮다.
2. **짧은 생성 길이**: 최대 6초로, Sora(60초)나 Kling(120초) 대비 짧다.
3. **Full 3D Attention의 메모리 비용**: 시공간 전체 어텐션은 $O(T \cdot H \cdot W)^2$ 복잡도를 가진다.

### 후속 발전

- **CogVideoX1.5**: 더 높은 해상도와 더 긴 비디오 지원
- **오픈소스 생태계 확장**: ComfyUI, Diffusers 통합으로 커뮤니티 활용 확대
- **비디오 편집**: I2V 기반 스타일 전이 및 비디오 편집 파이프라인 구축

CogVideoX는 오픈소스 비디오 생성 분야의 중요한 이정표로, 상업 수준의 품질을 연구 커뮤니티에 공개함으로써 비디오 생성 AI의 민주화에 기여하였다.

### 기술적 의의

CogVideoX가 제안한 Expert AdaLN과 텍스트-비디오 시퀀스 결합 방식은 이후 HunyuanVideo, Wan2.1 등 후속 오픈소스 비디오 모델들에도 영향을 미쳤다. Cross-Attention을 제거하고 단일 어텐션에서 두 모달리티를 처리하는 설계는 구현의 단순성과 효과의 양면에서 주목할 만하다. 특히 3D VAE의 시공간 압축 비율 설계는 비디오 잠재 확산 모델의 표준적 접근법으로 자리잡았으며, 시간 방향 4배 압축은 프레임 간 연속성을 보존하는 데 효과적인 비율로 평가된다. 데이터 품질 파이프라인 측면에서도 GPT-4V 기반 자동 캡셔닝은 DALL·E 3의 합성 캡션 접근법을 비디오 영역으로 확장한 의미가 있다.

## 관련 문서

- [[dit|DiT (Diffusion Transformers)]] — 발전 기반
