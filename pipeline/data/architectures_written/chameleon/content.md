<!-- infographic-hero -->
![Chameleon 핵심 요약](figures/infographic.svg)

*Figure: Chameleon 한 장 요약 인포그래픽*

# Chameleon: 조기 융합 기반 통합 멀티모달 모델

## 개요

Chameleon은 2024년 5월 Meta가 발표한 조기 융합(early-fusion) 방식의 멀티모달 모델이다. 기존 멀티모달 모델들이 별도의 비전 인코더(CLIP, SigLIP 등)를 사전학습한 뒤 LLM에 연결하는 **후기 융합(late-fusion)** 방식을 채택한 것과 달리, Chameleon은 이미지와 텍스트를 **모두 이산 토큰으로 변환하여 동일한 자기회귀 트랜스포머로 처리**하는 근본적으로 다른 접근을 취한다.

이미지를 VQ-VAE 토크나이저로 1024개의 이산 토큰으로 변환하고, BPE 텍스트 토큰과 합쳐 총 65,536개의 통합 어휘(vocabulary)로 모든 모달리티를 처리한다. 이 **all-token 방식**은 이미지 이해와 생성을 동일한 다음 토큰 예측(next-token prediction) 프레임워크로 통합하며, 인터리브된 이미지-텍스트 시퀀스를 자유롭게 생성할 수 있다. 7B와 34B 두 가지 크기로 제공되며, 텍스트 전용 벤치마크와 멀티모달 벤치마크 양쪽에서 경쟁력 있는 성능을 달성하였다.

논문: [Chameleon: Mixed-Modal Early-Fusion Foundation Models](https://arxiv.org/abs/2405.09818)

다음 다이어그램은 Chameleon의 조기 융합 아키텍처와 혼합 모달리티 생성 과정을 보여준다.

![Chameleon 아키텍처 - 혼합 모달리티 사전학습과 생성 과정](figures/fig_1.png)
*Figure 1: Chameleon 아키텍처 개요 - (a) 이미지와 텍스트를 모두 이산 토큰으로 변환하여 동일한 자기회귀 트랜스포머로 사전학습하고, (b) 텍스트와 이미지를 자유롭게 인터리브하여 생성한다. (Source: Team et al., 2024)*

## 아키텍처 상세

### 전체 구조

Chameleon의 아키텍처는 개념적으로 단순하다:

1. **이미지 토크나이저**: Make-A-Scene VQ-VAE 기반, 이미지를 512×512 → 1024개의 이산 토큰으로 변환 (8192개 코드북)
2. **텍스트 토크나이저**: BPE 기반, 57,344개 어휘
3. **통합 트랜스포머**: 텍스트 토큰 + 이미지 토큰을 동일한 자기회귀 모델로 처리

통합 어휘 구성:
$$V_{\text{total}} = V_{\text{text}} + V_{\text{image}} = 57,344 + 8,192 = 65,536$$

모든 토큰이 동일한 임베딩 공간에 매핑되므로, 이미지와 텍스트 사이에 별도의 프로젝션 레이어가 필요 없다.

### 이미지 토크나이제이션

이미지는 VQ-VAE(Vector Quantized Variational Autoencoder)를 통해 이산화된다:

$$I \in \mathbb{R}^{512 \times 512 \times 3} \xrightarrow{\text{VQ-VAE Encoder}} \mathbf{z} \in \{0, 1, ..., 8191\}^{1024}$$

1024개의 이산 코드는 각각 8192개 코드북 중 하나의 인덱스를 가리키며, 이는 텍스트 토큰과 완전히 동등하게 취급된다. 이미지 재구성 시에는 VQ-VAE 디코더가 이산 코드에서 원본 이미지를 복원한다.

### 학습 안정성 기법

대규모 혼합 모달리티 학습에서 발생하는 학습 불안정성을 해결하기 위해 세 가지 핵심 기법을 도입하였다:

1. **QK-Norm**: 쿼리와 키 벡터를 정규화하여 어텐션 로짓의 발산을 방지
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{\text{norm}(Q) \cdot \text{norm}(K)^T}{\sqrt{d_k}}\right)V$$

2. **재정렬된 레이어 정규화**: RMSNorm의 위치를 조정하여 그래디언트 흐름을 안정화

3. **Z-loss 정규화**: 로짓 크기가 지나치게 커지는 것을 방지하는 보조 손실

이 기법들이 없으면 이미지-텍스트 혼합 학습 시 학습 손실이 발산하는 현상이 빈번하게 발생한다. 아래 그래프는 QK-Norm과 dropout 적용 여부에 따른 출력 norm의 변화를 보여준다.

![QK-Norm과 dropout 적용에 따른 출력 norm 안정성 비교](figures/fig_5_1.png)
*Figure 2: 학습 안정성 분석 - QK-Norm과 dropout을 모두 적용했을 때만 출력 norm이 안정적으로 유지되며, 미적용 시 norm이 제어 불가능하게 증가하여 학습 발산의 전조가 된다. (Source: Team et al., 2024)*

Norm 재정렬 또한 학습 안정성에 결정적 역할을 한다.

![Norm 재정렬 적용 전후의 학습 손실 비교](figures/fig_12.png)
*Figure 3: Norm 재정렬 효과 - 정규화 순서를 재배치하면 학습 초기의 급격한 손실 스파이크가 완전히 제거되어 안정적인 수렴이 가능해진다. (Source: Team et al., 2024)*

### 모델 사양

| 항목 | Chameleon-7B | Chameleon-34B |
|------|-------------|--------------|
| 파라미터 | 7B | 34B |
| 히든 차원 | 4096 | 8192 |
| 레이어 | 32 | 48 |
| 어텐션 헤드 | 32 | 64 |
| 컨텍스트 길이 | 4096 | 4096 |
| 위치 인코딩 | RoPE | RoPE |
| 정규화 | RMSNorm + QK-Norm | RMSNorm + QK-Norm |
| 통합 어휘 | 65,536 | 65,536 |

## 핵심 혁신

### 1. 조기 융합(Early Fusion)

Chameleon은 처음부터 이미지와 텍스트를 동일한 토큰 공간에서 학습하므로, 후기 융합 모델처럼 비전 인코더와 LLM 사이의 표현 갭(representation gap)이 없다. 모델이 학습 초기부터 두 모달리티의 관계를 자연스럽게 학습하여, 인터리브된 이미지-텍스트 생성에서 더 자연스러운 결과를 산출한다.

### 2. 통합 생성 프레임워크

이미지 이해(텍스트 출력)와 이미지 생성(이미지 토큰 출력)이 동일한 다음 토큰 예측 메커니즘으로 작동한다. 이는 별도의 확산 모델이나 GAN 없이도 이미지를 생성할 수 있음을 의미하며, 아키텍처의 단순성을 극대화한다.

### 3. 자유로운 인터리브 생성

이미지와 텍스트 사이의 순서나 비율에 제약이 없어, "텍스트 → 이미지 → 텍스트 → 이미지"와 같은 자유로운 혼합 시퀀스 생성이 가능하다. 이는 블로그 포스트 자동 생성, 시각적 스토리텔링 등 실용적 응용에서 중요한 능력이다.

## 벤치마크/성능

| 벤치마크 | Chameleon-34B | Flamingo-80B | LLaVA-1.5-13B | GPT-4V |
|----------|-------------|-------------|--------------|--------|
| VQAv2 | 74.4% | 67.6% | 80.0% | - |
| MMMU | 38.4% | - | 36.4% | 56.8% |
| 텍스트 (MMLU) | 62.1% | - | - | 86.4% |
| 이미지 생성 (FID) | 경쟁적 | - | 불가 | 불가 |

텍스트 전용 벤치마크에서도 LLaMA-2-34B와 유사한 성능을 유지하며, 멀티모달 학습이 텍스트 능력을 심각하게 저하시키지 않음을 보여준다.

## 관련 모델 비교

| 특성 | Chameleon | Emu3 | Janus-Pro | LLaVA |
|------|-----------|------|-----------|-------|
| 융합 방식 | 조기 융합 | 조기 융합 | 디커플링 | 후기 융합 |
| 이미지 표현 | VQ 이산 토큰 | VQ 이산 토큰 | VQ + SigLIP | 연속 특징 |
| 이미지 생성 | 가능 | 가능 | 가능 | 불가 |
| 학습 안정성 | QK-Norm + Z-loss | - | - | 안정적 |
| 아키텍처 변경 | 최소 | 최소 | 듀얼 인코더 | 프로젝터 추가 |

## 학습 상세

학습은 두 단계로 진행된다:

1. **VQ-VAE 토크나이저 학습**: Make-A-Scene 기반의 이미지 토크나이저를 먼저 학습 (8192 코드북, 1024 토큰/이미지)
2. **통합 자기회귀 모델 학습**: 이미지 토큰과 텍스트 토큰을 혼합한 데이터로 사전학습

다음은 7B와 34B 모델의 학습 손실 곡선이다.

![Chameleon 7B와 34B의 학습 손실 곡선](figures/fig_10.png)
*Figure 4: 학습 손실 곡선 - 34B 모델이 7B 대비 일관되게 낮은 학습 손실을 달성하며, 약 600K 스텝에 걸쳐 안정적으로 수렴한다. (Source: Team et al., 2024)*

Chameleon은 다양한 유형의 인터리브 이미지-텍스트 생성을 지원한다.

![Chameleon의 인터리브 이미지-텍스트 생성 카테고리 분포](figures/fig_19.png)
*Figure 5: 인터리브 생성 태스크 분포 - Brainstorming(18.6%), Explanation(14.4%), How-to(12.5%) 등 다양한 카테고리에서 이미지와 텍스트를 혼합 생성하는 능력을 보여준다. (Source: Team et al., 2024)*

학습 데이터: 2조 토큰 이상의 텍스트와 수십억 장의 이미지를 이산 토큰으로 변환한 혼합 데이터
옵티마이저: AdamW
안정성: QK-Norm + Z-loss 정규화 필수 (미적용 시 학습 붕괴)

## 실무 활용

```python
# Chameleon 추론 예시 (개념적 코드)
from chameleon.inference import ChameleonModel

model = ChameleonModel.from_pretrained("facebook/chameleon-7b")

# 이미지 이해
response = model.generate(
    prompt="<image>이 이미지를 설명해주세요.",
    image="photo.jpg"
)

# 이미지 생성 (텍스트 → 이미지 토큰)
image_tokens = model.generate(
    prompt="A beautiful sunset over the ocean<image>",
    max_image_tokens=1024
)
image = model.decode_image(image_tokens)
```

## 한계 및 전망

### 한계

1. **이미지 생성 품질**: VQ 토크나이제이션의 정보 손실로 확산 모델(DALL-E 3, SD3) 대비 이미지 품질이 열등하다
2. **학습 불안정성**: 대규모 혼합 모달리티 학습에서 특별한 안정화 기법이 필수적이며, 하이퍼파라미터 민감성이 높다
3. **컴퓨팅 비용**: 이미지 1장당 1024개 토큰을 차지하여, 컨텍스트 윈도우 효율이 낮다
4. **비디오/오디오 미지원**: 이미지-텍스트 이외 모달리티 확장이 되지 않았다

### 전망

Chameleon이 제시한 조기 융합 방식은 이후 Emu3, Show-o2 등 통합 멀티모달 모델의 주요 설계 방향이 되었다. 특히 "모든 모달리티를 이산 토큰으로 통합"하는 철학은 GPT-4o와 같은 네이티브 멀티모달 모델의 이론적 기반이 되며, VQ-VAE의 품질 한계를 극복하기 위한 더 정교한 이미지 토크나이저 연구(Cosmos Tokenizer 등)와 함께 발전하고 있다.

## 관련 문서

- [[llama|LLaMA: Open and Efficient Foundation Language Models]] - 발전 기반
- [[emu3|Emu3]] - 영감을 줌
- [[show-o2|Show-o2]] - 영감을 줌
