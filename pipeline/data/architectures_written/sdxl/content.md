# SDXL (Stable Diffusion XL): 고해상도 오픈소스 이미지 생성의 표준

**Stability AI** · **2023-07-04** · **Diffusion** · **Diffusion UNet** · **오픈소스**

## 개요

Stable Diffusion XL(SDXL)은 2023년 Stability AI의 Dustin Podell 등이 발표한 고해상도 텍스트-이미지 생성 모델로, 기존 Stable Diffusion(SD) 1.x/2.x를 대폭 개선한 차세대 오픈소스 이미지 생성 모델이다. SDXL은 네 가지 핵심 개선을 통해 1024×1024 네이티브 해상도에서 상용 모델(Midjourney, DALL·E 3)에 필적하는 품질을 달성하였다.

첫째, U-Net 백본을 SD 1.5의 860M에서 3.5B 파라미터로 대폭 확장하였다. 특히 저해상도 특성 맵에 Transformer 블록을 집중 배치하여 의미적 표현 능력을 극대화하였다. 둘째, CLIP-ViT/L과 OpenCLIP-ViT/bigG 두 개의 텍스트 인코더를 병렬로 활용하여 텍스트 이해력을 획기적으로 향상시켰다. 셋째, 크기 조건화(Size Conditioning)와 자르기 조건화(Crop Conditioning)를 도입하여 학습 데이터 전처리로 인한 아티팩트를 제거하였다. 넷째, 선택적 Refiner 모델이 Base 모델의 출력을 고주파 디테일 위주로 개선한다.

SDXL은 출시 직후 오픈소스 이미지 생성의 새로운 표준이 되었으며, ComfyUI, Automatic1111 등 커뮤니티 도구와의 통합, LoRA/ControlNet 등 미세조정 생태계의 활성화에 크게 기여하였다.

- **논문**: [SDXL: Improving Latent Diffusion Models for High-Resolution Image Synthesis](https://arxiv.org/abs/2307.01952)
- **코드**: [Stability-AI/generative-models](https://github.com/Stability-AI/generative-models)
- **발표**: 2023년 7월, Stability AI
- **라이선스**: CreativeML Open RAIL+M

![SDXL과 이전 Stable Diffusion 버전의 인간 선호도 비교 — SDXL+Refiner가 48.44% 승률로 압도](figures/fig_2_1.jpg)
*Figure 1(좌): 사용자 선호도 비교 — SDXL+Refiner(48.44%)가 SDXL Base(36.93%)를 상회하며, SD 1.5(7.91%)와 SD 2.1(6.71%)을 크게 압도한다. Refiner 단계 추가만으로 선호도가 약 12%p 향상된다. (Source: Podell et al., 2023)*

![SDXL의 2단계 파이프라인 — Base 모델에서 Refiner를 거쳐 최종 이미지 생성까지](figures/fig_2_2.jpg)
*Figure 1(우): SDXL 2단계 파이프라인 — 노이즈로부터 Base 모델이 128x128 잠재 벡터를 생성하고, Refiner가 SDEdit 방식으로 디테일을 향상시킨 후, VAE 디코더가 1024x1024 최종 이미지를 출력한다. (Source: Podell et al., 2023)*

![Architecture](figures/architecture.svg)

## 아키텍처 상세

### 확장된 U-Net 백본

SDXL의 U-Net은 SD 1.5/2.x와 몇 가지 중요한 차이가 있다:

| 구성 요소 | SD 1.5 | SD 2.x | SDXL Base |
|----------|--------|--------|----------|
| 파라미터 | 860M | 865M | **3.5B** |
| 텍스트 인코더 | CLIP-L | OpenCLIP-H | **CLIP-L + OpenCLIP-bigG** |
| 네이티브 해상도 | 512×512 | 768×768 | **1024×1024** |
| Transformer 블록 배치 | 균등 | 균등 | **저해상도 집중** |
| 조건화 | 타임스텝 | 타임스텝 | **타임스텝+크기+크롭** |

SDXL U-Net의 핵심 설계 변경:

- **저해상도 집중 어텐션**: 가장 작은 해상도(8×8 특성 맵)에 4개, 32×32에 2개의 Transformer 블록을 집중 배치하고, 최고 해상도 레이어에서는 어텐션을 제거하여 메모리 효율과 의미적 표현 능력을 동시에 확보
- **최고 해상도 1블록 제거**: SD 1.5와 달리 128×128 해상도 레이어의 어텐션을 제거하여 계산 비용 절감

### 이중 텍스트 인코더 (Dual Text Encoder)

두 텍스트 인코더의 출력을 결합하여 풍부한 텍스트 표현을 구성한다:

**시퀀스 임베딩 (Cross-Attention용):**

$$h_{\text{text}} = \text{Concat}(h_{\text{CLIP-L}} \in \mathbb{R}^{77 \times 768}, \; h_{\text{OpenCLIP}} \in \mathbb{R}^{77 \times 1280}) \in \mathbb{R}^{77 \times 2048}$$

CLIP-L의 768차원 토큰 임베딩과 OpenCLIP-bigG의 1280차원 토큰 임베딩을 채널 방향으로 결합하여 2048차원 시퀀스를 만들고, Cross-Attention의 Key·Value로 사용한다.

**풀링 임베딩 (전역 조건용):**

OpenCLIP-bigG의 풀링된 텍스트 임베딩(1280차원)은 타임스텝 임베딩에 더해져 전역 조건으로 사용된다:

$$\text{emb}_{\text{global}} = \text{emb}_{\text{time}} + \text{emb}_{\text{size}} + \text{emb}_{\text{crop}} + \text{Pool}(h_{\text{OpenCLIP}})$$

### 마이크로 조건화 (Micro-Conditioning)

![학습 데이터셋의 높이-너비 해상도 분포 — Size Conditioning 없이는 39% 데이터가 폐기됨](figures/fig_3.jpg)
*Figure 2: 사전학습 데이터셋의 해상도 분포 — 점선(256px)으로 표시된 경계 아래의 저해상도 이미지가 전체의 39%를 차지한다. Size Conditioning을 통해 이 데이터를 모두 활용하면서도 추론 시 고해상도 조건으로 선명한 이미지를 생성할 수 있다. (Source: Podell et al., 2023)*

SDXL의 핵심 혁신 중 하나인 마이크로 조건화는 학습 데이터 전처리로 인한 아티팩트를 제거한다:

**Size Conditioning:**

학습 시 원본 이미지의 실제 해상도 $(h_{\text{orig}}, w_{\text{orig}})$를 시누소이달 임베딩으로 인코딩하여 U-Net에 주입한다. 이를 통해 모델은 저해상도 이미지와 고해상도 이미지를 구분할 수 있으며, 추론 시 높은 해상도를 지정하면 더 선명한 이미지를 생성한다.

$$\text{emb}_{\text{size}} = \text{SinEmb}(h_{\text{orig}}) + \text{SinEmb}(w_{\text{orig}})$$

**Crop Conditioning:**

학습 시 랜덤 크롭의 좌상단 좌표 $(c_{\text{top}}, c_{\text{left}})$를 조건으로 주입한다. 추론 시 $(0, 0)$을 지정하면 크롭 아티팩트(잘린 머리, 불완전한 객체)가 제거된다.

$$\text{emb}_{\text{crop}} = \text{SinEmb}(c_{\text{top}}) + \text{SinEmb}(c_{\text{left}})$$

| 조건화 유형 | 문제 해결 | 추론 시 설정 |
|-----------|---------|------------|
| Size Conditioning | 저해상도 학습 이미지의 영향 | 목표 해상도 지정 |
| Crop Conditioning | 크롭 아티팩트 | $(0, 0)$으로 설정 |

![Size Conditioning의 효과 — 동일 시드에서 크기 조건을 변경하면 이미지 품질이 크게 달라짐](figures/fig_4_1.jpg)
*Figure 3: Size Conditioning 효과 — 동일 프롬프트와 랜덤 시드에서 크기 조건을 64px에서 512px로 변경하면, 이미지 품질과 선명도가 극적으로 향상된다. 모델이 학습 데이터의 원본 해상도를 인식하고 이를 생성 품질에 반영한다. (Source: Podell et al., 2023)*

### Refiner 모델

SDXL은 선택적으로 사용할 수 있는 별도의 Refiner 모델(6.6B 파라미터)을 제공한다:

1. Base 모델이 전체 확산 과정을 수행하여 잠재 벡터 생성
2. Refiner가 고노이즈 구간($t \in [200, 1000]$)에서 img2img 방식으로 디테일 향상
3. 최종 VAE 디코딩으로 이미지 출력

Refiner는 같은 VAE 잠재 공간에서 동작하므로 Base 모델의 출력을 직접 입력으로 받을 수 있다. 주로 피부 질감, 머리카락, 배경 디테일 등 고주파 요소를 개선한다.

### 멀티스테이지 학습

SDXL은 두 단계 학습 전략을 사용한다:

1. **사전학습**: 512×512 해상도에서 대규모 학습
2. **미세조정**: 1024×1024 해상도에서 추가 학습

이 접근은 학습 효율을 높이면서도 고해상도 생성 능력을 확보한다.

## 핵심 혁신

1. **이중 텍스트 인코더**: CLIP-L과 OpenCLIP-bigG의 임베딩을 결합하여 텍스트 이해력을 크게 향상시켰다. 시퀀스 임베딩(Cross-Attention)과 풀링 임베딩(전역 조건)의 이중 경로 활용으로 로컬·글로벌 텍스트 정보를 모두 활용한다.

2. **마이크로 조건화**: Size Conditioning과 Crop Conditioning을 통해 학습 데이터의 다양한 해상도와 크롭을 모델이 인식하게 하여, 추론 시 아티팩트 없는 고품질 이미지를 생성할 수 있게 하였다.

3. **저해상도 집중 어텐션**: U-Net의 어텐션 블록을 저해상도 특성 맵에 집중 배치하는 설계로, 파라미터 대비 최대 효율을 달성하였다.

4. **Base + Refiner 파이프라인**: 2단계 파이프라인으로 생성과 세부 향상을 분리하여 품질을 극대화하였다.

## 벤치마크/성능

| 모델 | 해상도 | 인간 선호도 (↑) | CLIP Score (↑) |
|------|--------|----------------|----------------|
| **SDXL Base** | 1024² | 경쟁력 | **높음** |
| SDXL + Refiner | 1024² | **최고** | 높음 |
| SD 1.5 | 512² | 낮음 | 중간 |
| SD 2.1 | 768² | 중간 | 중간 |
| Midjourney 5.1 | - | 높음 | - |

Human Preference Study에서 SDXL + Refiner는 SD 1.5/2.x를 크게 능가하고, Midjourney 5.1과 경쟁력 있는 성능을 보였다.

## 관련 모델 비교

| 특성 | SDXL | SD 1.5 | SD 2.1 | SD3 |
|------|------|--------|--------|-----|
| 백본 | U-Net 3.5B | U-Net 860M | U-Net 865M | MMDiT 2B |
| 텍스트 인코더 | CLIP-L + OpenCLIP-bigG | CLIP-L | OpenCLIP-H | CLIP-L + G + T5 |
| 해상도 | 1024² | 512² | 768² | 1024² |
| 조건화 | Cross-Attn + 마이크로 | Cross-Attn | Cross-Attn | 이중 스트림 |
| Refiner | 선택적 | 없음 | 없음 | 없음 |
| VAE | SDXL VAE (f=8) | KL-f8 | KL-f8 | 16ch VAE |

## 학습 상세

- **데이터셋**: LAION-5B 등 수억 장의 이미지-텍스트 쌍
- **멀티스테이지**: 512×512 사전학습 → 1024×1024 미세조정
- **텍스트 인코더**: CLIP-ViT/L (OpenAI) + OpenCLIP-ViT/bigG (LAION), 학습 중 동결
- **VAE**: SDXL 전용 KL-f8 VAE (SD 1.5 VAE보다 개선)
- **Refiner**: 고노이즈 구간($t=200$~$1000$)에서 잘린 확산 과정으로 별도 학습
- **CFG**: 학습 시 10% 텍스트 드롭아웃, 추론 시 $s \approx 5$~$9$

## 실무 활용

### 1. 오픈소스 이미지 생성 생태계

SDXL은 ComfyUI, Automatic1111, InvokeAI 등 오픈소스 UI와의 통합으로 가장 널리 사용되는 이미지 생성 모델이 되었다. LoRA, ControlNet, IP-Adapter 등 다양한 커뮤니티 확장이 활발하다.

### 2. 다양한 종횡비 지원

마이크로 조건화 덕분에 1024×1024뿐 아니라 768×1344, 1344×768 등 다양한 종횡비를 지원한다.

### 3. Refiner를 활용한 품질 향상

Base 모델 단독 사용 대비, Refiner를 추가하면 피부, 머리카락, 질감 등 고주파 디테일이 크게 향상된다.

## 한계 및 전망

### 한계

1. **U-Net 스케일링 한계**: U-Net 구조의 비정형성으로 인해 DiT 대비 체계적 스케일링이 어렵다.
2. **텍스트 렌더링**: 이미지 내 텍스트 생성 능력이 여전히 제한적이다.
3. **구성적 이해**: 복잡한 공간 관계나 다수 객체 조합에서 여전히 한계가 있다.

### 후속 발전

- **SDXL Turbo (2023)**: Adversarial Diffusion Distillation으로 1~4 스텝 생성
- **SD3 (2024)**: U-Net을 MMDiT로 대체, T5-XXL 추가
- **SDXL Lightning (2024)**: Progressive Distillation으로 빠른 생성
- **Flux (2024)**: Hybrid DiT + Flow Matching

SDXL은 U-Net 기반 잠재 확산 모델의 정점으로, 오픈소스 이미지 생성 생태계를 형성한 가장 중요한 모델 중 하나이다. 이후 SD3와 Flux가 DiT 기반으로 전환하면서, SDXL은 U-Net 시대의 마지막 대표 모델로 자리매김하였다.

### 기술적 의의

SDXL의 기술적 의의는 "기존 아키텍처(U-Net + LDM)를 근본적으로 바꾸지 않으면서도 체계적 개선으로 상용 수준 품질을 달성할 수 있음"을 보인 것이다. 이중 텍스트 인코더는 Imagen의 "텍스트 인코더가 중요하다"는 발견을 오픈소스 환경에서 실현한 것이며, 마이크로 조건화는 학습 데이터의 메타데이터를 조건으로 활용하는 우아한 방법론이다. 특히 Crop Conditioning의 "학습 데이터의 결함을 모델이 인식하게 만들어 추론 시 결함을 제거"하는 접근은 데이터 증강의 관점에서 매우 혁신적이다. SDXL은 커뮤니티 생태계(LoRA 허브, ControlNet 확장, 커스텀 모델)의 폭발적 성장을 이끌며, 오픈소스 AI 이미지 생성의 민주화에 가장 큰 기여를 한 모델이다.

## 관련 문서

- [[ldm|LDM (Latent Diffusion Models)]] — 발전 기반
- [[sd3|Stable Diffusion 3]] — 후속 모델
