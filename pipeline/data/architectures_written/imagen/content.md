# Imagen: T5 텍스트 인코더 기반 고품질 이미지 생성

## 개요

Imagen은 2022년 Google Brain이 발표한 텍스트-이미지 생성 모델로, 사전학습된 대형 언어 모델(T5-XXL)의 텍스트 인코더를 이미지 생성에 그대로 활용하면 CLIP보다 훨씬 우수한 텍스트 정렬을 달성할 수 있다는 핵심 발견을 제시하였다. MS-COCO FID 7.27로 DALL·E 2를 능가하였다.

- **논문**: [Photorealistic Text-to-Image Diffusion Models with Deep Language Understanding](https://arxiv.org/abs/2205.11487)
- **발표**: 2022년 5월, Google Brain
- **라이선스**: Proprietary

## 아키텍처 상세

### Cascaded Diffusion Pipeline

Imagen은 세 단계의 확산 모델로 구성된다:

| 단계 | 해상도 | 모델 | 역할 |
|------|--------|------|------|
| Stage 1 | 64×64 | Efficient U-Net | 텍스트→이미지 기본 생성 |
| Stage 2 | 64→256 | SR U-Net | 초해상도 |
| Stage 3 | 256→1024 | SR U-Net | 최종 초해상도 |

### T5-XXL 텍스트 인코더

Imagen의 핵심 발견은 이미지-텍스트 쌍으로 학습된 CLIP 인코더보다, 순수 텍스트 코퍼스로 학습된 T5-XXL(11B 파라미터)이 의미론적으로 훨씬 풍부한 텍스트 표현을 제공한다는 것이다.

**규모별 절제 실험 결과:**

| T5 버전 | 파라미터 | FID (↓) | CLIP Score (↑) |
|---------|---------|---------|----------------|
| T5-Small | 60M | 12.3 | 0.82 |
| T5-Base | 220M | 10.5 | 0.84 |
| T5-Large | 770M | 9.1 | 0.85 |
| T5-XL | 3B | 8.2 | 0.86 |
| T5-XXL | 11B | **7.27** | **0.87** |

텍스트 인코더 규모가 커질수록 FID와 CLIP Score가 모두 향상된다. T5-XXL은 학습 중 **완전히 동결**되므로 이미지 생성 모델만 업데이트된다.

텍스트 임베딩은 U-Net의 Cross-Attention으로 주입된다:

$$\text{Attn}(Q, K, V): \quad Q = W_Q h_{\text{image}}, \quad K = W_K h_{\text{T5}}, \quad V = W_V h_{\text{T5}}$$

### Noise Conditioning Augmentation

SR 모델의 핵심 기법으로, 저해상도 조건 이미지에 노이즈를 추가하여 SR 모델이 다양한 품질의 입력에 강건하게 동작하도록 한다:

$$x_{low}^{aug} = \sqrt{\bar{\alpha}_s} x_{low} + \sqrt{1 - \bar{\alpha}_s} \epsilon, \quad \epsilon \sim \mathcal{N}(0, I)$$

노이즈 수준 $s$도 조건으로 함께 입력된다. 이 기법 없이는 SR 모델이 Stage 1의 특정 오류 패턴에 과적합되어 아티팩트가 발생한다.

### Efficient U-Net

메모리 효율을 위해 저해상도 블록에 더 많은 파라미터를 할당하고, 고해상도 블록은 경량화한 U-Net 변형:

- 저해상도 특성 맵: 많은 잔차 블록 + 어텐션
- 고해상도 특성 맵: 적은 잔차 블록 + 어텐션 없음

### DrawBench 벤치마크

Imagen은 기존 FID/CLIP Score 외에 DrawBench라는 새로운 평가 벤치마크를 도입하였다. DrawBench는 11개 카테고리(색상, 개수, 공간 관계, 텍스트 렌더링 등)의 200개 프롬프트로 구성되며, 인간 평가자가 텍스트 충실도와 이미지 품질을 판정한다.

## 핵심 혁신

1. **동결 T5-XXL 활용**: LLM의 텍스트 이해 능력이 이미지 생성 조건으로 효과적임을 증명하였다. 이 발견은 이후 SD3, Flux 등에서 T5를 채택하는 데 직접적 근거가 되었다.
2. **Noise Conditioning Augmentation**: Cascaded Diffusion의 단계 간 품질 불일치 문제를 해결하는 실용적 기법이다.
3. **DrawBench**: 텍스트-이미지 정렬의 세밀한 측면을 평가하는 표준 벤치마크를 제시하였다.
4. **Cascaded Diffusion**: 저해상도→고해상도 단계적 생성으로 계산 효율과 품질을 동시에 달성하였다.

## 벤치마크/성능

| 모델 | MS-COCO FID (↓) | DrawBench 선호도 |
|------|-----------------|----------------|
| Imagen | **7.27** | **최상위** |
| DALL·E 2 | 10.39 | 중간 |
| GLIDE | 12.24 | 중간 |
| Make-A-Scene | 11.84 | - |
| VQ-Diffusion | 13.86 | 낮음 |

## 관련 모델 비교

| 특성 | Imagen | DALL·E 2 | GLIDE | Stable Diffusion |
|------|--------|---------|-------|-----------------|
| 텍스트 인코더 | T5-XXL (11B) | CLIP | Transformer | CLIP |
| 중간 표현 | 없음 (직접) | CLIP 임베딩 | 없음 | 잠재 공간 |
| 해상도 | 1024 | 1024 | 256 | 512 |
| Cascaded | 3단계 | Prior+Decoder+SR | 2단계 | 없음 |
| 오픈소스 | 아니오 | 아니오 | 부분 | 전체 |

## 학습 상세

- **데이터셋**: LAION-400M, COCO, CC3M, CC12M, WebLI 등 860M 이미지-텍스트 쌍
- **T5-XXL**: 동결 (학습 중 업데이트하지 않음)
- **이미지 생성 모델**: ~2B 파라미터 (업데이트 대상)
- **CFG**: 각 단계에 독립적으로 적용
- **하드웨어**: 16× TPUv4

## 실무 활용

### 1. T5 기반 텍스트 인코더의 표준화

Imagen의 발견 이후 SD3, Flux, PixArt-α 등이 T5-XXL을 텍스트 인코더로 채택하여 업계 표준이 되었다.

### 2. Cascaded Diffusion 설계 패턴

저해상도 생성 + SR 파이프라인은 Imagen 이후 고해상도 이미지·비디오 생성의 표준 접근법이 되었다.

### 3. Google 제품 통합

Imagen의 기술은 Google의 ImageFX, Vertex AI 등 상업 서비스에 통합되었다.

## 한계 및 전망

### 한계

1. **비공개 모델**: 코드와 가중치가 공개되지 않아 직접 활용이 불가능하다.
2. **Cascaded 구조의 복잡성**: 세 단계 모델을 관리하는 것이 단일 모델 대비 복잡하다.
3. **CLIP Score 한계**: 텍스트-이미지 정렬 평가에 CLIP Score가 완벽하지 않음을 지적하고 DrawBench를 제안하였으나, DrawBench도 인간 평가에 의존한다.

### 후속 발전

- **Imagen 2/3 (2024~)**: Google의 후속 이미지 생성 모델
- **Veo (2024)**: Imagen 기술을 비디오 생성으로 확장
- **Parti**: T5 기반 자기회귀 이미지 생성 모델

Imagen은 "텍스트 인코더의 규모와 품질이 이미지 생성의 핵심"이라는 패러다임 전환을 이끈 연구로, 현대 텍스트-이미지 생성 모델의 설계 철학에 근본적 영향을 미쳤다. 특히 T5-XXL의 성공은 이후 PixArt-alpha, SD3, Flux 등이 T5를 표준 텍스트 인코더로 채택하는 직접적 근거가 되었다. Noise Conditioning Augmentation은 Cascaded Diffusion의 핵심 기법으로 이후 업샘플링 파이프라인에서 널리 채택되었다.

## 관련 문서

- [[ddpm|DDPM (Denoising Diffusion Probabilistic Models)]] — 발전 기반
- [[veo|Veo 2]] — 후속 모델
- [[t5|T5]] — 사용 기법
