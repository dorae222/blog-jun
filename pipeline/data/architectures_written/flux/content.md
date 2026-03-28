# FLUX.1: 하이브리드 MMDiT 기반 텍스트-이미지 생성

## 개요

FLUX.1은 2024년 Black Forest Labs(Stable Diffusion 원작자 그룹)가 공개한 12B 파라미터 규모의 텍스트-이미지 생성 모델로, Flow Matching 학습과 Hybrid MMDiT 아키텍처를 통해 오픈소스 모델 중 최고 수준의 이미지 품질과 텍스트 충실도를 달성하였다.

- **코드**: [black-forest-labs/flux](https://github.com/black-forest-labs/flux)
- **발표**: 2024년 8월, Black Forest Labs
- **라이선스**: Apache 2.0 (schnell) / Non-Commercial (dev)

## 아키텍처 상세

![FLUX.1 하이브리드 MMDiT 아키텍처](figures/architecture.png)

*Figure 1: FLUX.1의 Double-Stream + Single-Stream 하이브리드 MMDiT 아키텍처. (Black Forest Labs, 2024)*

### Hybrid MMDiT: 이중 스트림 + 단일 스트림

FLUX.1의 핵심 혁신은 SD3의 MMDiT를 발전시킨 하이브리드 아키텍처이다:

**Phase 1 - Double-Stream 블록 (19개):**

이미지와 텍스트가 각자 독립적인 파라미터로 처리되면서 양방향 상호작용:

$$Q = [W_Q^x h^x; W_Q^y h^y], \quad K = [W_K^x h^x; W_K^y h^y], \quad V = [W_V^x h^x; W_V^y h^y]$$

$$\text{Attn}([h^x; h^y]) = \text{softmax}\left(\frac{QK^T}{\sqrt{d}}\right) V$$

출력을 다시 이미지/텍스트로 분리하여 각 스트림의 독립적 업데이트가 이루어진다.

**Phase 2 - Single-Stream 블록 (38개):**

이미지+텍스트를 하나의 시퀀스로 통합하여 공유 파라미터로 효율적 처리.

| 구성 요소 | 사양 |
|----------|------|
| 파라미터 | 12B |
| 이중 스트림 블록 | 19 |
| 단일 스트림 블록 | 38 |
| 히든 차원 | 3072 |
| 어텐션 헤드 | 24 |
| 텍스트 인코더 | CLIP-L (77 토큰) + T5-XXL (256 토큰) |
| 정규화 | AdaRMSNorm |
| 활성화 | GELU |
| 위치 인코딩 | RoPE (이미지) + Absolute (텍스트) |

### Parallel Attention

Self-Attention과 FFN을 순차적으로 실행하는 대신 병렬 실행:

$$h \leftarrow h + \text{Attn}(h) + \text{FFN}(h)$$

KV 캐시를 공유하여 연산 효율을 높이고, 추론 시 텐서 병렬화에 유리하다.

### RoPE for Images

2D 패치 좌표 $(h, w)$에 RoPE(Rotary Position Embedding)를 적용하여 임의 종횡비와 해상도 생성을 지원한다. 기존 Transformer 기반 이미지 모델들이 사용하던 고정 위치 인코딩(absolute positional encoding)은 학습 시 본 해상도에 강하게 묶여, 다른 해상도로 외삽(extrapolation)할 때 성능이 급격히 저하되는 문제가 있었다.

RoPE는 원래 NLP에서 시퀀스 위치를 인코딩하기 위해 제안된 기법으로, 쿼리와 키 벡터에 위치에 따른 회전 행렬을 곱하는 방식이다. FLUX.1은 이를 2D 이미지 패치로 확장하여, 각 패치의 $(h, w)$ 좌표를 독립적인 주파수 성분으로 인코딩한다:

$$\text{RoPE}(q, h, w) = R_h \cdot R_w \cdot q$$

여기서 $R_h$와 $R_w$는 각각 높이와 너비 좌표에 대한 회전 행렬이다. 이 방식은 상대적 위치 관계를 내재적으로 보존하므로, 학습 시 사용하지 않은 해상도나 종횡비에서도 안정적인 생성이 가능하다. 특히 1024x1024 정사각형뿐 아니라 768x1344, 1344x768 등 다양한 종횡비를 하나의 모델로 처리할 수 있어, 실무에서 매우 유용하다.

### T5-XXL 텍스트 인코더 통합

FLUX.1은 두 개의 텍스트 인코더를 동시에 활용한다. CLIP-L은 77토큰까지의 짧은 프롬프트에서 전역적 시각-언어 정렬 임베딩을 제공하며, T5-XXL(11B 파라미터)은 256토큰까지의 긴 프롬프트에서 세밀한 언어 의미를 포착한다.

T5-XXL은 인코더-디코더 구조의 대규모 언어 모델로, 그 인코더 부분만을 활용하여 텍스트의 풍부한 시맨틱 표현을 추출한다. CLIP이 이미지-텍스트 대조 학습으로 학습된 반면, T5는 순수 텍스트 태스크(span corruption)로 사전학습되어 복잡한 문장 구조, 수량, 공간 관계 등을 더 정확하게 표현할 수 있다. 두 인코더의 출력은 각각 독립적인 프로젝션을 통해 MMDiT의 텍스트 스트림에 입력된다.

이 이중 인코더 설계는 SD3에서 처음 도입되었으나(CLIP-L + CLIP-G + T5-XXL), FLUX.1은 CLIP-G를 제거하고 CLIP-L + T5-XXL만을 사용하여 더 간결하면서도 효과적인 구성을 달성하였다.

### 세 가지 버전

| 버전 | 특성 | 스텝 수 | 라이선스 |
|------|------|--------|---------|
| FLUX.1-pro | 최고 품질, API 전용 | ~28 | 상업용 |
| FLUX.1-dev | 가이던스 증류(CFG 내재화) | ~20 | Non-Commercial |
| FLUX.1-schnell | 일관성 증류 | 4~8 | Apache 2.0 |

### Rectified Flow Formulation

FLUX.1의 학습 기법인 Flow Matching은 기존 DDPM 기반 확산 모델과 근본적으로 다른 접근을 취한다. DDPM이 수백~수천 스텝의 마르코프 체인을 통해 노이즈를 점진적으로 제거하는 반면, Flow Matching은 노이즈 $x_0$에서 데이터 $x_1$로의 **직선 궤적(straight path)**을 직접 학습한다:

$$x_t = (1 - t) x_0 + t x_1, \quad t \in [0, 1]$$

$$\mathcal{L}_{\text{FM}} = \mathbb{E}_{t, x_0, x_1}\left[\|v_\theta(x_t, t) - (x_1 - x_0)\|^2\right]$$

여기서 $v_\theta$는 시간 $t$에서의 속도장(velocity field)을 예측하는 신경망이다. 직선 궤적의 핵심 장점은 곡선 궤적 대비 적은 함수 평가 횟수(NFE)로도 높은 품질의 샘플을 생성할 수 있다는 점이다. 이는 FLUX.1-schnell이 단 4~8스텝으로도 고품질 이미지를 생성할 수 있는 이론적 기반이 된다.

특히 Rectified Flow는 궤적의 "곧음(straightness)"을 극대화하는 방향으로 학습되므로, 오일러 적분기(Euler integrator)와 같은 단순한 샘플러로도 정확한 생성이 가능하다. 이는 DDPM 계열에서 고급 샘플러(DPM-Solver, UniPC 등)가 필요했던 것과 대비된다.

## 핵심 혁신

1. **Hybrid Double/Single-Stream**: 초반에는 이미지-텍스트 독립 처리로 풍부한 표현을 학습하고, 후반에는 통합 처리로 효율을 높이는 두 단계 설계이다.
2. **Parallel Attention**: Attn과 FFN을 병렬 실행하여 추론 효율을 향상시켰다.
3. **Guidance Distillation**: FLUX.1-dev는 CFG 효과를 모델에 내재화하여 단일 패스로 추론하므로 CFG의 2배 비용 문제를 해결하였다.
4. **Rectified Flow**: 직선 궤적 Flow Matching으로 적은 스텝에서도 높은 품질을 달성하며, 기존 DDPM 대비 샘플링 효율을 크게 향상시켰다.
5. **12B 스케일 오픈소스**: 당시 오픈소스 이미지 생성 모델 중 최대 규모의 파라미터를 공개하였다.

## 벤치마크/성능

| 모델 | ELO 점수 | 텍스트 렌더링 | 인체 표현 | 종횡비 다양성 |
|------|---------|------------|---------|------------|
| FLUX.1-pro | **1위권** | 우수 | 우수 | 임의 |
| Midjourney v6.0 | 상위 | 보통 | 우수 | 제한적 |
| DALL·E 3 | 상위 | 우수 | 보통 | 제한적 |
| SDXL | 중간 | 낮음 | 보통 | 제한적 |
| Ideogram 2.0 | 상위 | 우수 | 보통 | 임의 |

ELO 기반 이미지 생성 평가에서 Midjourney v6.0, DALL·E 3, Ideogram 2.0 대비 최상위 성능을 기록하였다.

## 관련 모델 비교

| 특성 | FLUX.1 | SD3 | SDXL | DALL·E 3 |
|------|--------|-----|------|---------|
| 백본 | Hybrid MMDiT | MMDiT | U-Net | 비공개 |
| 파라미터 | 12B | 2B/8B | 3.5B | 비공개 |
| 학습 기법 | Flow Matching | Flow Matching | DDPM | 비공개 |
| 텍스트 인코더 | CLIP-L + T5-XXL | CLIP-L + CLIP-G + T5-XXL | CLIP + OpenCLIP | 비공개 |
| 오픈소스 | 부분 (schnell) | 부분 (Medium) | 전체 | 아니오 |

### SDXL과의 비교

SDXL은 U-Net 기반의 3.5B 파라미터 모델로, Stable Diffusion 계열의 마지막 U-Net 아키텍처이다. FLUX.1은 SDXL 대비 세 가지 근본적 차이를 가진다. 첫째, U-Net의 인코더-디코더 구조를 완전히 버리고 Transformer 기반 MMDiT로 전환하여 스케일링이 더 자유롭다. 둘째, DDPM에서 Flow Matching으로 학습 기법을 변경하여 샘플링 효율이 향상되었다. 셋째, SDXL이 CLIP + OpenCLIP의 비교적 제한된 텍스트 이해에 의존하는 반면, FLUX.1은 T5-XXL을 통해 복잡한 프롬프트를 더 정확히 해석한다. 이러한 차이는 특히 텍스트 렌더링, 인체 해부학 정확도, 복잡한 다중 객체 장면에서 FLUX.1의 명확한 우위로 나타난다.

### DALL-E 3과의 비교

DALL-E 3는 합성 캡션(synthetic caption)을 통한 텍스트-이미지 정렬 향상이 핵심 혁신이었다. FLUX.1은 아키텍처 수준에서 이를 달성하여, 합성 캡션 없이도 높은 프롬프트 충실도를 보인다. DALL-E 3가 API 전용으로 폐쇄적인 반면, FLUX.1은 schnell 버전을 Apache 2.0으로 공개하여 커뮤니티 생태계를 활성화하였다. 다만, DALL-E 3가 ChatGPT 통합을 통해 프롬프트 리라이팅(prompt rewriting)을 자동으로 수행하는 사용자 경험 측면에서는 접근성이 더 높다.

### 모델 변형(Variants) 상세

**FLUX.1-schnell**은 일관성 증류(Consistency Distillation)를 통해 4~8스텝 생성을 달성한 경량 버전이다. Apache 2.0 라이선스로 상업적 활용이 완전히 자유로우며, 단일 A100에서 1024x1024 이미지를 약 2초 내에 생성할 수 있다. 품질은 pro/dev 대비 다소 낮지만, 실시간 미리보기나 대량 생성에 적합하다.

**FLUX.1-dev**는 가이던스 증류(Guidance Distillation)를 적용한 연구용 버전이다. 일반적으로 CFG(Classifier-Free Guidance)는 조건부/비조건부 추론을 각각 수행해야 하므로 추론 비용이 2배가 되지만, dev 버전은 CFG 효과를 모델 가중치에 내재화하여 단일 패스로 고품질 생성이 가능하다. Non-Commercial 라이선스이므로 연구 및 개인 프로젝트에 적합하다.

**FLUX.1-pro**는 최고 품질의 API 전용 버전으로, 약 28스텝의 전체 샘플링을 수행한다. 상업적 사용이 가능하며, BFL API를 통해 접근할 수 있다.

## 학습 상세

- **데이터셋**: 수억 장 규모 이미지-텍스트 쌍 (비공개)
- **텍스트 인코더**: T5-XXL (11B) + CLIP-L (동결)
- **학습 기법**: Flow Matching (직선 궤적)
- **NFE**: ~28 (pro), ~20 (dev), 4~8 (schnell)
- **FLUX.1-dev**: Guidance Distillation으로 CFG 효과 내재화
- **FLUX.1-schnell**: Consistency Distillation으로 4~8스텝 가속

## 실무 활용

### 1. 오픈소스 고품질 이미지 생성

FLUX.1-schnell (Apache 2.0)은 상업적으로 자유롭게 활용 가능하며, 4~8스텝으로 빠른 추론이 가능하다.

### 2. LoRA/ControlNet 생태계

ComfyUI, Diffusers 등에서 FLUX.1용 LoRA, ControlNet, IP-Adapter가 활발히 개발되고 있으며, 오픈소스 생태계가 빠르게 성장하고 있다.

### 3. 실시간 이미지 생성

FLUX.1-schnell의 4스텝 생성은 인터랙티브 이미지 편집, 실시간 시각화 등에 적합하다.

## 한계 및 전망

### 한계

1. **VRAM 요구량**: 12B 파라미터 모델은 FP16에서 약 24GB VRAM이 필요하여, 소비자 GPU에서의 실행에 양자화가 필요하다. NF4 양자화를 적용하면 8GB VRAM에서도 실행 가능하지만, 미세한 품질 저하가 발생한다.
2. **부분 오픈소스**: pro 모델은 API로만 접근 가능하며, dev 모델은 비상업 라이선스이다. 가장 높은 품질의 모델을 자유롭게 활용할 수 없다는 점에서 진정한 오픈소스라 하기 어렵다.
3. **공식 논문 부재**: 기술 보고서나 논문이 공개되지 않아 세부 아키텍처 정보가 제한적이다. 커뮤니티의 리버스 엔지니어링과 코드 분석에 의존해야 하는 상황이다.
4. **학습 데이터 불투명성**: 학습에 사용된 데이터셋이 완전히 비공개이며, 데이터 규모나 구성에 대한 정보도 제공되지 않는다. 이는 저작권 및 편향 관련 우려를 야기한다.
5. **긴 추론 시간**: 12B 규모로 인해 pro 버전 기준 28스텝 생성에 상당한 시간이 소요되며, 대화형 워크플로우에서는 schnell 버전 사용이 사실상 필수적이다.

### 후속 발전

- **FLUX.2 (2025)**: 텍스트 렌더링, 캐릭터 일관성 추가 개선
- **커뮤니티 양자화**: GGUF, NF4 등 다양한 양자화로 8GB VRAM에서도 실행 가능
- **FLUX Fill/Canny/Depth**: 인페인팅, ControlNet 변형 공식 공개

FLUX.1은 Stable Diffusion 원작자들이 SD3의 설계를 더욱 발전시켜 만든 모델로, 오픈소스 이미지 생성의 새로운 기준을 수립하였다.

### 기술적 의의

FLUX.1의 Hybrid Double/Single-Stream 설계는 "이미지와 텍스트를 어떻게 결합할 것인가"라는 근본적 질문에 대한 가장 정교한 답변 중 하나이다. 초반 이중 스트림에서 각 모달리티가 독립적으로 풍부한 표현을 구축한 뒤 후반 단일 스트림에서 효율적으로 통합하는 설계는, 단순한 Cross-Attention이나 일률적 결합보다 더 높은 품질과 효율을 동시에 달성한다. 12B 규모의 오픈소스 모델 공개는 이전까지 API로만 접근 가능하던 상업 모델 수준의 품질을 커뮤니티에 보급하여, LoRA, ControlNet, IP-Adapter 등 광범위한 생태계 구축을 촉진하였다.

## 관련 문서

- [[sd3|Stable Diffusion 3]] - 발전 기반
- [[flux-2|FLUX.2]] - 후속 모델
- [[flow-matching|Flow Matching]] - 사용 기법
