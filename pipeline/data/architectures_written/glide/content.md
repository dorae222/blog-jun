# GLIDE: 텍스트 가이드 확산 이미지 생성

## 개요

GLIDE(Guided Language to Image Diffusion for Generation and Editing)는 2021년 OpenAI가 발표한 텍스트 조건부 이미지 생성 모델로, Classifier Guidance와 Classifier-Free Guidance(CFG)를 동일한 모델에서 비교하고 **CFG가 더 우월함을 최초로 실증**한 중요한 연구이다. 35억 파라미터 규모의 ADM U-Net에 텍스트 인코더를 결합하였다.

- **논문**: [GLIDE: Towards Photorealistic Image Generation and Editing with Text-Guided Diffusion Models](https://arxiv.org/abs/2112.10741)
- **코드**: [openai/glide-text2im](https://github.com/openai/glide-text2im)
- **발표**: 2021년 12월, OpenAI
- **라이선스**: MIT (필터링 버전)

![GLIDE 전체 아키텍처 - U-Net Denoiser, Text Conditioning, CFG 구조](figures/architecture.png)
*Figure 1: GLIDE 전체 아키텍처 - 3.5B 파라미터 ADM U-Net에 Transformer 텍스트 인코더를 결합하고, Cross-Attention과 AdaGN의 이중 경로로 텍스트 조건을 주입한다. Classifier-Free Guidance(CFG) 수식과 핵심 사양을 함께 보여준다. (Source: Nichol et al., 2021)*

## 아키텍처 상세

### 텍스트 인코딩

GLIDE는 Transformer 기반 언어 모델로 텍스트를 처리하며, $K$개 토큰의 임베딩 시퀀스를 생성한다. 이 임베딩은 두 경로로 활용된다:

**경로 1 - Cross-Attention:**

U-Net의 각 어텐션 레이어에서 텍스트 임베딩을 Key·Value로 사용:

$$\text{Attn}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d}}\right) V$$
$$Q = W_Q \cdot h_{\text{image}}, \quad K = W_K \cdot h_{\text{text}}, \quad V = W_V \cdot h_{\text{text}}$$

**경로 2 - AdaGN:**

최종 토큰 임베딩을 타임스텝 임베딩에 더하여 AdaGN으로 각 레이어에 전역 조건 주입:

$$y = \text{MLP}(\text{emb}_t + \text{emb}_{\text{text}})$$

| 구성 요소 | 사양 |
|----------|------|
| 파라미터 수 | 3.5B (full) / 300M (공개) |
| 텍스트 토큰 수 | 128 |
| 생성 해상도 | 64×64 → 256×256 (업샘플러) |
| 어텐션 | Self-Attention + Cross-Attention |
| 정규화 | Group Norm + AdaGN |
| 활성화 | SiLU |

### CLIP Guidance vs. Classifier-Free Guidance 비교

GLIDE는 동일한 모델에서 두 가이던스 방법을 직접 비교하였다:

**CLIP Guidance:**
$$\tilde{\epsilon} = \epsilon_\theta(\mathbf{x}_t) + s \cdot \nabla_{\mathbf{x}_t} (\text{CLIP}_{\text{image}}(\hat{\mathbf{x}}_0) \cdot \text{CLIP}_{\text{text}}(c))$$

**Classifier-Free Guidance:**
$$\tilde{\epsilon} = \epsilon_\theta(\mathbf{x}_t, \varnothing) + s \cdot (\epsilon_\theta(\mathbf{x}_t, c) - \epsilon_\theta(\mathbf{x}_t, \varnothing))$$

실험 결과: 인간 평가자들이 CFG를 2:1 비율로 선호. 이는 CLIP 공간의 방향이 지각적 품질 방향과 반드시 일치하지 않으며, 내부 조건부 정보만으로 가이던스를 수행하는 CFG가 더 효과적임을 의미한다.

### 인페인팅 (Inpainting)

![GLIDE 텍스트 기반 인페인팅 - 마스크 영역을 텍스트 프롬프트에 따라 채우는 예시](figures/fig_2_1.jpg)
*Figure 2: 텍스트 조건부 인페인팅 - 녹색 영역이 지워진 후, 텍스트 프롬프트에 따라 모델이 주변 맥락의 스타일과 조명에 맞춰 사실적으로 채워 넣는다. (Source: Nichol et al., 2021)*

GLIDE는 인페인팅 기능도 제공한다:

1. 원본 이미지에 마스크 적용
2. 마스크된 이미지를 노이즈와 결합하여 U-Net에 입력
3. 텍스트 프롬프트에 따라 마스크 영역 새롭게 생성
4. 업샘플러로 고해상도 완성

### 업샘플러

별도의 확산 업샘플러 모델이 64×64 출력을 256×256으로 향상시킨다. 이 접근법은 이후 Imagen의 Cascaded Diffusion으로 발전하였다.

## 핵심 혁신

1. **CFG의 우월성 실증**: 동일 조건에서 CLIP Guidance와 CFG를 비교하여 CFG의 우월성을 최초로 정량적/정성적으로 증명하였다.
2. **텍스트-확산 통합 아키텍처**: Cross-Attention + AdaGN의 이중 경로로 텍스트 정보를 풍부하게 활용하는 설계를 제시하였다.
3. **텍스트 기반 인페인팅**: 마스크 영역을 텍스트로 지정하여 편집하는 실용적 파이프라인을 시연하였다.
4. **안전 필터링 공개**: 안전 필터를 적용한 축소 모델을 공개하여 연구 접근성을 높였다.

![GLIDE CFG 생성 샘플 - 포토리얼리스틱한 이미지 생성 결과](figures/fig_1_1.png)
*Figure 4: GLIDE의 Classifier-Free Guidance 생성 샘플 - 그림자와 반사를 포함한 사실적 이미지를 생성하며, 여러 개념을 올바르게 조합하고 새로운 개념의 예술적 렌더링도 가능하다. (Source: Nichol et al., 2021)*

## 벤치마크/성능

| 가이던스 방법 | FID (↓) | CLIP Score (↑) | 인간 선호도 |
|-------------|---------|----------------|-----------|
| GLIDE + CLIP Guidance | ~12.0 | 높음 | 33% |
| GLIDE + CFG | ~12.24 | 높음 | **67%** |
| DALL·E (2021) | 17.89 | 중간 | - |

인간 평가자들이 CFG 버전을 CLIP Guidance 대비 약 2:1로 선호하였다.

## 관련 모델 비교

| 특성 | GLIDE | DALL·E | ADM | DALL·E 2 |
|------|-------|--------|-----|---------|
| 텍스트 인코더 | Transformer | BPE | 없음 (클래스) | CLIP |
| 가이던스 | CFG | 자기회귀 | Classifier | CFG |
| 해상도 | 256×256 | 256×256 | 256×256 | 1024×1024 |
| 인페인팅 | 가능 | 불가 | 불가 | 가능 |
| 발표 연도 | 2021.12 | 2021.01 | 2021.05 | 2022.04 |

## 학습 상세

- **데이터셋**: 대규모 인터넷 이미지-텍스트 쌍 (내부 데이터, 규모 비공개)
- **CLIP Guidance**: 별도 학습된 noisy CLIP 모델 활용
- **CFG**: 학습 시 20% 확률로 텍스트를 빈 시퀀스로 대체
- **공개 버전**: 300M 파라미터, 안전 필터 적용 데이터로 재학습

## 실무 활용

### 1. CFG 기반 텍스트-이미지 생성의 프로토타입

GLIDE는 이후 DALL·E 2, Imagen, Stable Diffusion 등 모든 텍스트-이미지 확산 모델의 CFG + Cross-Attention 설계의 원형이 되었다.

![반복적 인페인팅으로 복잡한 장면을 생성하는 과정](figures/fig_3_1.jpg)
*Figure 3: 반복 인페인팅 - "a cozy living room"으로 이미지를 생성한 후, 인페인팅 마스크와 후속 텍스트 프롬프트를 사용하여 벽에 그림, 커피 테이블, 꽃병을 순차적으로 추가하는 과정. (Source: Nichol et al., 2021)*

### 2. 텍스트 기반 이미지 편집

인페인팅 파이프라인은 사용자가 원하는 영역을 텍스트로 수정하는 워크플로우의 초기 형태로, 이후 DALL·E 2 Edits, Stable Diffusion Inpainting으로 발전하였다.

### 3. 연구 베이스라인

공개된 300M 필터링 모델은 텍스트-이미지 생성 연구의 베이스라인으로 활용되었다.

## 한계 및 전망

### 한계

1. **낮은 해상도**: 기본 64×64 생성 후 업샘플링으로 256×256를 달성하는 구조는 이후 더 높은 네이티브 해상도 모델로 대체되었다.
2. **비공개 전체 모델**: 3.5B 전체 모델은 공개되지 않았다.
3. **텍스트 이해 한계**: Transformer 기반 텍스트 인코더의 규모가 제한적이어서 복잡한 프롬프트 이해에 한계가 있었다.

### 후속 발전

- **DALL·E 2 (2022)**: CLIP 잠재 공간 기반으로 확장
- **Imagen (2022)**: T5-XXL 텍스트 인코더로 텍스트 이해력 혁신
- **Stable Diffusion (2022)**: 잠재 공간 확산으로 효율성 향상

GLIDE는 CFG의 우월성을 실증하고 텍스트-확산 모델의 기본 설계를 확립한 선구적 연구로, 이후 텍스트-이미지 생성 혁명의 직접적 전신이다.

### 기술적 의의

GLIDE가 증명한 "CFG가 CLIP Guidance보다 우수하다"는 결론은 이후 확산 모델 연구 전체의 방향을 결정지었다. CLIP Guidance는 외부 모델의 그래디언트에 의존하므로 분포 외 영역(out-of-distribution)으로 밀려나는 문제가 있었으나, CFG는 확산 모델 자체의 내부 표현을 활용하므로 더 자연스러운 이미지를 생성한다. GLIDE의 Cross-Attention + AdaGN 이중 경로 텍스트 주입 방식은 이후 사실상 모든 텍스트-이미지 확산 모델의 표준 설계가 되었다. 또한 인페인팅 기능의 시연은 확산 모델이 단순한 생성을 넘어 이미지 편집 도구로 활용될 수 있음을 보여주었으며, 이는 Stable Diffusion Inpainting, DALL·E 2 Edits로 직접 이어졌다. GLIDE는 DALL·E 2의 직접적 선행 모델로서, OpenAI의 텍스트-이미지 생성 연구 계보에서 핵심적인 위치를 차지한다.

## 관련 문서

- [[classifier-guidance|Classifier Guidance (ADM)]] - 발전 기반
- [[dalle-2|DALL·E 2]] - 후속 모델
