# DALL·E 2: CLIP 잠재 공간 기반 계층적 이미지 생성

## 개요

DALL·E 2(Hierarchical Text-Conditional Image Generation with CLIP Latents)는 2022년 OpenAI가 발표한 텍스트-이미지 생성 모델로, CLIP의 이미지 임베딩 공간을 활용하는 독창적인 two-stage 파이프라인을 도입하였다. 텍스트에서 이미지로 직접 생성하지 않고, CLIP 텍스트 임베딩 → CLIP 이미지 임베딩 → 실제 이미지의 계층적 생성 과정을 거친다.

- **논문**: [Hierarchical Text-Conditional Image Generation with CLIP Latents](https://arxiv.org/abs/2204.06125)
- **발표**: 2022년 4월, OpenAI
- **라이선스**: Proprietary

## 아키텍처 상세

### 3단계 계층적 파이프라인

DALL·E 2는 세 단계의 모델로 구성된다:

**Stage 1 — Diffusion Prior:**

텍스트 CLIP 임베딩 $z_t = \text{CLIP}_{\text{text}}(y)$에서 이미지 CLIP 임베딩 $z_i$를 생성하는 확산 모델:

$$p(z_i | y) = p(z_i | z_t)$$

Prior로 자기회귀(AR) 모델과 확산 모델 두 가지를 실험하였으며, 확산 Prior가 더 우수한 성능을 보였다.

**Stage 2 — Decoder (64×64):**

GLIDE 기반의 확산 U-Net이 CLIP 이미지 임베딩 $z_i$와 텍스트 캡션 $y$를 조건으로 64×64 이미지를 생성한다:

$$p(x_{64} | z_i, y)$$

**Stage 3 — Upsampler (64→256→1024):**

두 단계의 업샘플링 확산 모델이 고해상도 이미지를 완성한다:

$$p(x_{256} | x_{64}, z_i, y) \cdot p(x_{1024} | x_{256}, z_i, y)$$

| 구성 요소 | 파라미터 | 역할 |
|----------|---------|------|
| CLIP ViT-H/16 | 비공개 | 이미지/텍스트 임베딩 |
| Diffusion Prior | 3.5B | 텍스트→이미지 임베딩 |
| Decoder (64×64) | 3.5B | 이미지 임베딩→이미지 |
| Upsampler (256) | ~1B | 64→256 초해상도 |
| Upsampler (1024) | ~1B | 256→1024 초해상도 |

### CLIP 잠재 공간의 활용

DALL·E 2의 핵심 통찰은 CLIP 임베딩 공간이 시각-언어 정보를 구조적으로 잘 정렬하고 있다는 것이다:

- **보간**: 두 이미지의 CLIP 임베딩을 선형 보간 후 디코딩하면 의미 있는 시각적 변환이 이루어진다
- **이미지 Variations**: 실제 이미지의 CLIP 임베딩을 Prior를 건너뛰고 Decoder에 직접 입력하면 원본과 의미적으로 유사한 변형 이미지가 생성된다
- **텍스트-이미지 혼합**: 텍스트와 이미지 임베딩을 적절히 결합하여 창의적 생성이 가능하다

### CFG 적용

CFG는 텍스트 조건과 CLIP 임베딩 조건에 독립적으로 적용된다:

$$\tilde{\epsilon} = \epsilon_\theta(\mathbf{x}_t) + s_t \cdot (\epsilon_\theta(\mathbf{x}_t, z_t) - \epsilon_\theta(\mathbf{x}_t)) + s_i \cdot (\epsilon_\theta(\mathbf{x}_t, z_i) - \epsilon_\theta(\mathbf{x}_t))$$

## 핵심 혁신

1. **CLIP 임베딩 기반 2단계 생성**: 텍스트→이미지 직접 매핑 대신 CLIP 공간을 중간 표현으로 활용하여 더 풍부하고 유연한 생성이 가능하다.
2. **Diffusion Prior**: 텍스트 임베딩에서 이미지 임베딩을 생성하는 확산 모델로, 다양한 시각적 해석을 생성할 수 있다.
3. **이미지 Variations/편집**: CLIP 임베딩 조작을 통한 이미지 변형과 편집 기능 제공.
4. **상업 서비스 출시**: AI 이미지 생성의 상업화를 선도한 모델 중 하나이다.

## 벤치마크/성능

| 모델 | MS-COCO FID (↓) | CLIP Score (↑) | 해상도 |
|------|-----------------|----------------|--------|
| DALL·E 2 | 10.39 | - | 1024×1024 |
| DALL·E (원본) | 17.89 | - | 256×256 |
| GLIDE | 12.24 | - | 256×256 |
| Make-A-Scene | 11.84 | - | 512×512 |
| Imagen | **7.27** | 0.87 | 1024×1024 |

Imagen에 FID 기준으로 뒤처졌으나, 이미지 변형·편집 등 추가 기능에서 차별화를 보였다.

## 관련 모델 비교

| 특성 | DALL·E 2 | DALL·E | Imagen | GLIDE |
|------|---------|--------|--------|-------|
| 중간 표현 | CLIP 임베딩 | dVAE 토큰 | 없음 (직접) | 없음 (직접) |
| 텍스트 인코더 | CLIP | BPE | T5-XXL | Transformer |
| 해상도 | 1024 | 256 | 1024 | 256 |
| Variations | 가능 | 불가 | 불가 | 불가 |
| 파라미터 | ~7B (합계) | 12B | ~3B | 3.5B |

## 학습 상세

- **CLIP 인코더**: 250M 이미지-텍스트 쌍으로 사전학습된 CLIP ViT-H/16
- **Prior**: 텍스트-이미지 쌍으로 확산 Prior 학습
- **Decoder**: 이미지 CLIP 임베딩을 조건으로 이미지 재구성 학습
- **데이터셋**: DALL·E 학습 데이터 + LAION Aesthetics
- **CFG**: 텍스트와 CLIP 임베딩 양쪽에 독립 적용

## 실무 활용

### 1. 상업 이미지 생성 서비스

DALL·E 2는 OpenAI API를 통해 최초의 대규모 상업 AI 이미지 생성 서비스로 출시되었다.

### 2. 이미지 편집 (DALL·E Edits)

인페인팅 기반 이미지 편집 기능으로, 사용자가 마스크를 그리고 텍스트로 해당 영역의 내용을 지정할 수 있다.

### 3. 이미지 변형 (Variations)

원본 이미지와 의미적으로 유사하지만 다른 구성의 이미지를 생성하여 디자인 영감이나 컨셉 탐색에 활용된다.

## 한계 및 전망

### 한계

1. **텍스트 렌더링 부족**: CLIP의 텍스트 이해 한계로 이미지 내 텍스트 렌더링이 부정확하다.
2. **CLIP 병목**: CLIP 임베딩의 정보 손실로 인해 세밀한 디테일이 손실될 수 있다.
3. **복잡한 구성 이해 부족**: 여러 객체의 색상-속성 결합, 공간 관계 등에서 오류가 발생한다.

### 후속 발전

- **DALL·E 3 (2023)**: 합성 캡션을 통한 텍스트 충실도 혁신적 개선
- **unCLIP**: DALL·E 2의 오픈소스 구현체 (Karlo 등)
- **Imagen**: CLIP 대신 T5-XXL을 활용한 경쟁 접근법

DALL·E 2는 CLIP 잠재 공간을 생성 모델에 활용하는 독창적 아이디어와 상업화를 통해 AI 이미지 생성 시대를 본격적으로 열었다.

### 기술적 의의

DALL·E 2의 Prior + Decoder 2단계 파이프라인은 이후 Karlo(카카오브레인), Kandinsky 등 오픈소스 구현체에서 재현되었다. CLIP 임베딩 공간에서의 의미론적 조작(보간, 변형) 가능성은 생성 모델의 제어 가능성에 대한 새로운 관점을 제시하였다. 다만 CLIP 병목으로 인한 텍스트 렌더링 한계는 이후 DALL·E 3에서 합성 캡션 전략으로, Imagen에서 T5-XXL 텍스트 인코더로 각각 해결되는 방향으로 발전하였다. DALL·E 2의 상업 출시는 Midjourney, Stable Diffusion과 함께 2022년 "AI 이미지 생성 혁명"의 세 축을 형성하였으며, 이후 ChatGPT와의 통합을 통해 더 넓은 사용자층에 AI 이미지 생성을 보급하는 데 기여하였다.

## 관련 문서

- [[glide|GLIDE]] — 발전 기반
- [[dalle-3|DALL·E 3]] — 후속 모델
- [[clip|CLIP]] — 사용 기법
