# Stable Diffusion 3: 멀티모달 확산 트랜스포머 기반 이미지 생성

**Stability AI** · **2024-03-05** · **Diffusion** · **Stability AI Community License**

## 개요

Stable Diffusion 3(SD3)는 2024년 Stability AI가 발표한 텍스트-이미지 생성 모델로, **Multimodal Diffusion Transformer(MMDiT)** 아키텍처와 **Flow Matching** 학습 기법을 결합한 혁신적인 설계를 채택하였다. SD3는 Stable Diffusion 시리즈의 세 번째 메이저 버전으로, 이전 세대(SD 1.x, SDXL)의 U-Net 기반 아키텍처에서 Transformer 기반 아키텍처로의 패러다임 전환을 이루었다.

기존 확산 모델은 이미지 토큰과 텍스트 토큰을 Cross-Attention으로 결합하였다. 이 구조에서 텍스트 정보는 이미지 표현에 영향을 주지만, 이미지 정보가 텍스트 표현에 영향을 주지는 못하는 일방향적 상호작용이었다. SD3의 MMDiT는 이미지 토큰과 텍스트 토큰을 별도의 스트림으로 유지하면서 **Full Self-Attention**으로 두 모달리티가 양방향으로 상호 어텐션을 계산하게 한다. 이 설계는 텍스트와 이미지 간의 풍부한 양방향 상호작용을 가능하게 하며, 각 모달리티가 자체 파라미터(선형 변환)를 유지하면서도 공유 어텐션 레이어에서 결합된다.

노이즈 스케줄로는 기존 선형 또는 코사인 스케줄 대신 Flow Matching의 직선 경로(Rectified Flow)를 채택하였고, 고노이즈 구간에 더 많은 학습 가중치를 부여하는 **로짓-정규 분포(logit-normal distribution)**로 타임스텝을 샘플링한다. 세 개의 텍스트 인코더(CLIP-L, CLIP-G, T5-XXL)를 병렬로 활용하여 텍스트 이해력을 최대화하였다. 텍스트 렌더링, 복잡한 구도, 다양한 종횡비 지원에서 SDXL 대비 크게 향상된 품질을 보이며, 특히 이미지 내 텍스트 생성 능력이 크게 개선되었다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

### MMDiT 블록: 이중 스트림 어텐션

MMDiT 블록의 핵심은 이미지 시퀀스 $z^x$와 텍스트 시퀀스 $z^y$를 채널 방향으로 연결하여 $[z^x; z^y]$를 구성하고, 이 결합 시퀀스에 Full Self-Attention을 적용하는 것이다. 각 모달리티는 독립적인 선형 변환을 사용한다:

$$Q = [W_Q^x z^x; W_Q^y z^y], \quad K = [W_K^x z^x; W_K^y z^y], \quad V = [W_V^x z^x; W_V^y z^y]$$

어텐션 계산:

$$\text{Attn}([z^x; z^y]) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

이 구조에서 이미지-이미지, 이미지-텍스트, 텍스트-이미지, 텍스트-텍스트의 네 가지 어텐션 상호작용이 모두 계산된다. 어텐션 출력은 다시 이미지 부분과 텍스트 부분으로 분리되어 각자의 독립적인 FFN을 통과한다. 이 "이중 스트림(dual-stream)" 설계는 두 모달리티가 공유 표현 공간에서 상호작용하면서도 각자의 특성을 유지할 수 있게 한다.

### Flow Matching 학습 기법

SD3는 DDPM의 이산 시간 확산 대신 Flow Matching의 연속 시간 흐름을 채택하였다. 학습 목표는 벡터 필드 예측이다:

$$\mathcal{L} = \mathbb{E}_{t, x_0, x_1}\left[\|v_\theta(z_t, t) - (x_1 - x_0)\|^2\right]$$

여기서 $z_t = (1-t)x_0 + tx_1$은 노이즈 $x_0$와 데이터 $x_1$ 사이의 선형 보간이다. 타임스텝 $t$의 샘플링은 로짓-정규 분포 $t \sim \text{logit-normal}(0, 1)$을 사용한다. 이 분포는 $t \approx 0.5$ 근처에 밀도를 집중시켜, 중간 노이즈 수준의 학습 가중치를 높인다. 이는 중간 노이즈 수준이 생성 품질에 가장 큰 영향을 미친다는 경험적 관찰에 기반한다.

### 트리플 텍스트 인코더

SD3는 세 개의 텍스트 인코더를 병렬로 활용한다: CLIP-L(텍스트-이미지 정렬 임베딩, 77 토큰), CLIP-G(대형 CLIP 임베딩, 77 토큰), T5-XXL(풍부한 의미 임베딩, 256 토큰). CLIP 임베딩은 풀링된 벡터로 AdaLN의 조건으로 주입되고, T5 임베딩은 시퀀스 형태로 MMDiT의 텍스트 스트림에 입력된다. 세 인코더의 조합은 짧은 프롬프트에서의 정확성(CLIP)과 긴 설명적 프롬프트에서의 이해력(T5)을 모두 확보한다.

### 위치 인코딩

이미지 패치에는 2D RoPE(Rotary Position Embedding)가 적용되며, 다양한 종횡비와 해상도를 지원한다. 텍스트 토큰에는 절대 위치 인코딩이 사용된다.

## 핵심 혁신

SD3의 핵심 혁신은 MMDiT의 이중 스트림 설계, Flow Matching 학습, 트리플 텍스트 인코더의 조합이다. MMDiT는 텍스트-이미지 간 양방향 어텐션으로 프롬프트 충실도를 크게 향상시켰으며, 특히 이미지 내 텍스트 렌더링에서 기존 모델 대비 현저한 개선을 보인다. Flow Matching과 로짓-정규 타임스텝 샘플링은 학습 효율과 생성 품질을 동시에 향상시켰다. 이 아키텍처는 후속 모델인 FLUX.1에서 더욱 발전되어, 단일 스트림 블록과 이중 스트림 블록을 혼합하는 하이브리드 구조로 진화하였다.

## 벤치마크/성능

| 모델 | 텍스트 정렬 승률 (↑) | 이미지 품질 승률 (↑) | 텍스트 렌더링 |
|------|-------------------|-------------------|------------|
| SD3 (8B) | DALL-E 3 대비 우위 | DALL-E 3 대비 우위 | 우수 |
| SD3 (2B) | Midjourney v6 대비 우위 | 경쟁적 | 양호 |
| SDXL | 기준선 | 기준선 | 불량 |
| DALL-E 3 | 높음 | 높음 | 양호 |
| Midjourney v6 | 높음 | 높음 | 양호 |

Human Preference 평가에서 SD3 8B는 DALL-E 3, Midjourney v6, SDXL 대비 텍스트 충실도와 이미지 품질 모두에서 우위를 기록하였다. 특히 텍스트 렌더링 능력은 이전 세대 대비 질적 도약이다.

## 학습

LAION-5B 등 대규모 이미지-텍스트 데이터셋으로 학습되었다. 세 텍스트 인코더 중 T5-XXL은 학습 중 동결하거나 낮은 학습률로 미세조정된다. 모델 크기에 따라 800M, 2B, 8B 세 가지 버전이 있으며, 중간 크기(2B Medium)가 커뮤니티 라이선스로 공개되었다. 학습 목표는 Flow Matching의 벡터 필드 예측이며, 추론 시 Classifier-Free Guidance를 적용한다.

## 관련 모델

SD3는 SDXL에서 발전하였으며, DiT와 Flow Matching 기법을 활용한다. 후속 모델인 FLUX.1(Black Forest Labs)은 SD3의 MMDiT 아키텍처를 개선한 하이브리드 구조를 채택하였다. SD3.5는 SD3의 개선 버전으로 Medium(2.5B) 크기가 공개되었다.

## 참고 자료

- [논문: Scaling Rectified Flow Transformers for High-Resolution Image Synthesis](https://arxiv.org/abs/2403.03206)
- [코드](https://github.com/Stability-AI/sd3-ref)

## 관련 문서

- [[sdxl|SDXL (Stable Diffusion XL)]] — 발전 기반
- [[flux|FLUX.1]] — 후속 모델
- [[dit|DiT (Diffusion Transformers)]] — 사용 기법