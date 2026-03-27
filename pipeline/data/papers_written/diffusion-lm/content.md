## 개요

Diffusion-LM은 2022년 NeurIPS에서 Xiang Lisa Li et al.이 발표한 논문으로, **단어 임베딩 공간에서 연속 가우시안 확산을 수행**하는 방식으로 텍스트를 생성한다. 이 접근법의 핵심 동기는 **제어 가능한 텍스트 생성(controllable text generation)**이다.

AR 모델에서 제어 가능한 생성은 어렵다. 특정 문법 구조나 감성을 갖는 텍스트를 생성하려면 복잡한 후처리나 강화학습이 필요하다. 반면 이미지 생성 분야에서는 분류기 유도(classifier guidance)가 매우 효과적으로 작동한다. Diffusion-LM은 이 아이디어를 텍스트로 가져온다.

다음 그림은 Diffusion-LM의 전체 파이프라인을 보여준다. 가우시안 노이즈 벡터 시퀀스에서 출발하여 반복적 디노이징을 통해 단어 벡터로 수렴하며, 분류기 유도를 통해 원하는 속성(구문 구조, 감성 등)을 제어한다.

![Diffusion-LM의 전체 파이프라인: 가우시안 벡터에서 단어 벡터로의 반복적 디노이징과 분류기 유도](figures/fig_1.png)
*Diffusion-LM은 가우시안 벡터 시퀀스를 반복적으로 디노이징하여 단어 벡터로 변환한다. 제어 가능한 생성을 위해 연속 잠재 변수에 대해 유창성(Diffusion-LM)과 제어 요구사항(분류기)을 동시에 최적화하는 그래디언트 업데이트를 수행한다.*

주요 기여:

1. **임베딩 공간 확산**: 이산 토큰 대신 연속 임베딩에 가우시안 노이즈 적용
2. **End-to-End 역방향 임베딩**: 확산 중간 상태에서 토큰으로의 투영(rounding) 기법
3. **분류기 유도**: 구문, 감성, 주제 등 세밀한 속성 제어
4. **병렬 생성**: AR과 달리 모든 토큰을 동시에 생성 가능

## 배경 및 문제

### 제어 가능한 텍스트 생성의 어려움

특정 속성을 갖는 텍스트를 생성하는 것은 중요하지만 어렵다:

- **감성 제어**: 긍정적 또는 부정적 감성의 리뷰 생성
- **문법 구조 제어**: 특정 파싱 트리 구조를 따르는 문장 생성
- **주제 제어**: 특정 주제어를 포함하는 텍스트 생성
- **독성 없는 생성**: 유해 표현 없이 생성

AR 모델(GPT 계열)에서 이를 달성하는 방법들:

| 방법 | 한계 |
|------|------|
| 프롬프트 엔지니어링 | 정확한 제어 어려움, 속성 무시 가능 |
| 파인튜닝 | 각 속성마다 별도 학습 필요 |
| PPLM | 메모리 집약적, 느린 생성 |
| GeDi | 추가 클래스 조건부 LM 필요 |

분류기 유도(classifier guidance)는 이미지 생성에서 매우 효과적이다:

$$\nabla_{x_t} \log p(x_t \mid c) = \nabla_{x_t} \log p(x_t) + \gamma \nabla_{x_t} \log p(c \mid x_t)$$

텍스트에 이것을 적용하려면 이산 공간이 아닌 **연속 공간**이 필요하다. 그래디언트를 이산 토큰에 직접 계산할 수 없기 때문이다.

### 왜 임베딩 공간인가?

Diffusion-LM의 핵심 통찰: 텍스트의 이산성(discreteness) 문제를 우회하는 가장 자연스러운 방법은 **토큰을 연속 임베딩 벡터에 매핑**하고, 그 임베딩 공간에서 확산을 수행하는 것이다.

$$\text{"Hello"} \xrightarrow{\text{embed}} \mathbf{e}_\text{Hello} \in \mathbb{R}^d \xrightarrow{\text{diffuse}} \mathbf{e}_\text{Hello} + \epsilon$$

이 방식은 연속 확산 모델(DDPM)의 모든 이론과 기술(분류기 유도 포함)을 직접 활용할 수 있다.

## 핵심 아이디어

### 임베딩 공간 확산

Diffusion-LM의 순방향/역방향 확산 과정은 아래 그래피컬 모델로 요약된다. 기존 확산 모델과 달리 텍스트 $\mathbf{w}$와 연속 임베딩 $\mathbf{x}_0$ 사이에 임베딩(embedding)과 라운딩(rounding) 단계를 추가한 것이 핵심 차이점이다.

![Diffusion-LM의 순방향 및 역방향 확산 과정을 나타내는 그래피컬 모델](figures/fig_2.png)
*순방향(Noising)과 역방향(Denoising) 확산 과정의 그래피컬 모델. 기존 확산 모델에 텍스트 $\mathbf{w}$와 임베딩 $\mathbf{x}_0$ 사이의 마르코프 전이를 추가하고, 임베딩(Embedding)과 라운딩(Rounding) 기법을 제안한다.*

Diffusion-LM은 각 토큰 $w_i$를 학습 가능한 임베딩 $\text{EMB}(w_i) = \mathbf{e}_i \in \mathbb{R}^d$에 매핑한 후, 임베딩 시퀀스 $x_0 = [\mathbf{e}_1, \mathbf{e}_2, \ldots, \mathbf{e}_L]$에 확산을 적용한다.

**순방향 과정 (Embedding Space):**

$$q(x_t \mid x_{t-1}) = \mathcal{N}(x_t; \sqrt{1-\beta_t} x_{t-1}, \beta_t I)$$

$$q(x_t \mid x_0) = \mathcal{N}(x_t; \sqrt{\bar{\alpha}_t} x_0, (1-\bar{\alpha}_t) I)$$

여기서 $\bar{\alpha}_t = \prod_{s=1}^{t} (1-\beta_s)$이다. 이는 표준 DDPM과 동일하지만, 노이즈가 추가되는 대상이 이미지 픽셀이 아닌 **단어 임베딩 벡터**라는 점이 다르다.

**역방향 과정 (Denoising):**

$$p_\theta(x_{t-1} \mid x_t) = \mathcal{N}(x_{t-1}; \mu_\theta(x_t, t), \Sigma_\theta(x_t, t))$$

### 임베딩에서 토큰으로: Rounding

연속 임베딩 공간에서 생성된 $x_0$를 다시 이산 토큰으로 변환하는 과정이 필요하다. 가장 단순한 방법은 **nearest-neighbor rounding**이다:

$$w_i = \argmin_{w \in \mathcal{V}} \|\text{EMB}(w) - \mathbf{x}_0^{(i)}\|_2$$

그러나 이 방법은 학습 과정과 추론 과정 사이의 불일치(training-inference mismatch)를 야기한다. 학습 시에는 실제 임베딩 $x_0$을 사용하지만, 추론 시에는 모델이 생성한 $\hat{x}_0$을 사용하기 때문이다.

**Anchor Loss (개선된 방법):**

Diffusion-LM은 이를 해결하기 위해 추가적인 임베딩 정규화 손실을 도입한다:

$$\mathcal{L}_{anchor} = \sum_{i=1}^{L} \|\hat{x}_0^{(i)} - \text{EMB}(w_i)\|_2^2$$

이 손실은 모델이 예측하는 $\hat{x}_0$가 실제 어휘 임베딩에 가깝도록 강제한다.

아래 그림은 학습된 임베딩과 랜덤 임베딩의 성능 차이를 보여준다. 학습된 임베딩이 모든 차원에서 일관되게 더 낮은 lm-score(낮을수록 좋음)를 달성한다.

![학습된 임베딩 vs 랜덤 임베딩의 lm-score 비교](figures/fig_4_1.png)
*Figure 4: 학습된 임베딩 vs 랜덤 임베딩의 lm-score 비교. 임베딩 차원(16, 64, 128)에 관계없이 학습된 임베딩이 일관되게 우수한 성능을 보인다. (Li et al., 2022)*

또한 $x_0$ 예측과 $\epsilon$ 예측 두 가지 파라미터화 방식의 비교에서, $x_0$ 예측이 더 안정적인 성능을 보인다.

![x_0 예측 vs epsilon 예측 파라미터화 비교](figures/fig_4_2.png)
*Figure 5: 파라미터화 방식에 따른 lm-score 비교. $x_0$ 직접 예측이 $\epsilon$ 예측보다 모든 임베딩 차원에서 낮고 안정적인 lm-score를 달성하며, 특히 고차원(128)에서 차이가 두드러진다. (Li et al., 2022)*

학습된 임베딩이 실제로 언어적 구조를 반영하는지 확인하기 위해, 아래 t-SNE 시각화를 살펴보자. 동일한 품사(POS)를 가진 단어들이 임베딩 공간에서 군집을 이루고 있음을 확인할 수 있다.

![학습된 단어 임베딩의 t-SNE 시각화 (품사별 색상 구분)](figures/fig_3.png)
*학습된 단어 임베딩의 t-SNE 시각화. 각 단어는 품사(POS) 태그에 따라 색상이 구분되어 있다. 명사(NOUN), 동사(VERB), 형용사(ADJ) 등 동일 품사의 단어들이 임베딩 공간에서 자연스럽게 군집을 형성하며, 이는 학습된 임베딩이 언어적 의미 구조를 잘 포착하고 있음을 보여준다.*

### 학습 목적함수

Diffusion-LM의 전체 학습 목적함수는:

$$\mathcal{L}_{DiffusionLM} = \underbrace{\mathbb{E}_{t, x_0, \epsilon} \|\epsilon - \epsilon_\theta(x_t, t)\|^2}_{\text{DDPM 노이즈 예측}} + \lambda \underbrace{\mathbb{E}_{t, x_0, \epsilon} \|\hat{x}_0 - x_0\|^2}_{\text{임베딩 앵커}} + \mu \underbrace{\mathbb{E}[-\log P_{\theta}(w \mid \hat{x}_0)]}_{\text{토큰 NLL}}$$

- 첫 번째 항: DDPM 스타일 노이즈 예측 손실
- 두 번째 항: 임베딩 앵커 손실 (rounding 정확도 향상)
- 세 번째 항: 토큰 레벨 음의 로그 우도 (어휘 분포 근사)

### 분류기 유도 (Classifier Guidance)

분류기 유도를 사용하면 생성 중에 특정 속성을 제어할 수 있다. 속성 $c$ (예: 긍정 감성)를 갖는 텍스트를 생성하려면:

$$\nabla_{x_t} \log p(x_t \mid c) = \nabla_{x_t} \log p(x_t) + \gamma \nabla_{x_t} \log p(c \mid x_t)$$

여기서:
- $\nabla_{x_t} \log p(x_t)$: 학습된 확산 모델의 스코어 (노이즈 예측에서 계산)
- $\nabla_{x_t} \log p(c \mid x_t)$: 노이즈 있는 임베딩 $x_t$에서의 분류기 그래디언트
- $\gamma$: 유도 강도 (클수록 속성에 더 가깝게 생성)

이 방법의 장점은 학습 시에는 무조건 생성(unconditional generation)만 학습하고, 추론 시에 임의의 분류기를 붙여서 원하는 속성을 유도할 수 있다는 것이다.

**단계별 분류기 유도:**

추론 중 각 역방향 스텝에서:
1. $\mu_\theta(x_t, t)$ 계산 (평균 예측)
2. 분류기 그래디언트 $\nabla_{x_t} \log p(c \mid x_t)$ 계산
3. 평균 조정: $\tilde{\mu} = \mu_\theta + \gamma \Sigma \nabla_{x_t} \log p(c \mid x_t)$
4. $x_{t-1} \sim \mathcal{N}(\tilde{\mu}, \Sigma)$에서 샘플링

## 방법론

### 아키텍처

**디노이징 신경망:**
- 트랜스포머 인코더 (양방향 어텐션)
- 입력: 노이즈 임베딩 시퀀스 $x_t \in \mathbb{R}^{L \times d}$
- 시간 임베딩: sinusoidal embedding, 각 레이어에 AdaLN으로 주입
- 출력: 노이즈 예측 $\hat{\epsilon} \in \mathbb{R}^{L \times d}$ (또는 $x_0$ 직접 예측)

**임베딩 파라미터:**
- $d = 16$ 또는 $d = 128$ (실험에 따라)
- BERT 또는 무작위 초기화 후 End-to-End 학습

**분류기:**
- 작은 트랜스포머 또는 CNN
- 노이즈 있는 임베딩 $x_t$에서 속성 클래스 예측
- 학습 시 $x_t$에 여러 노이즈 레벨 적용 (다양한 $t$에서 강건하도록)

### 노이즈 스케줄

확산 모델의 성능은 노이즈 스케줄 선택에 크게 좌우된다. 아래 그림은 논문에서 비교한 세 가지 노이즈 스케줄(linear, cosine, sqrt)의 노이즈 표준편차 $\sqrt{1 - \bar{\alpha}_t}$ 변화를 보여준다.

![세 가지 노이즈 스케줄(linear, cosine, sqrt) 비교](figures/fig_5.png)
*노이즈 스케줄 $\sqrt{1 - \bar{\alpha}_t}$ 시각화. Linear 스케줄은 빠르게 노이즈가 포화되는 반면, sqrt 스케줄은 초반에 노이즈를 급격히 증가시킨 뒤 후반에 완만해진다. 실험 결과 sqrt 스케줄이 다양한 임베딩 차원과 파라미터화 방식에서 가장 안정적인 성능을 보였다.*

노이즈 스케줄과 파라미터화 방식의 조합에 따른 상세한 ablation 결과는 다음과 같다.

![노이즈 스케줄(sqrt, cosine, linear)과 파라미터화 방식에 따른 lm-score 비교](figures/fig_6_2.png)
*Figure 7: 노이즈 스케줄별 lm-score 비교. $x_0$ 예측 방식에서는 세 스케줄 모두 안정적이지만, $\epsilon$ 예측 방식에서는 sqrt 스케줄만이 고차원에서도 안정적인 성능을 유지한다. (Li et al., 2022)*

디노이징 네트워크의 아키텍처 선택도 성능에 큰 영향을 미친다. 이미지 확산에서 널리 쓰이는 U-Net과 트랜스포머를 비교한 결과, 텍스트 도메인에서는 트랜스포머가 명확히 우수하다.

![Transformer vs U-Net 아키텍처 비교](figures/fig_6_3.png)
*Figure 8: 디노이징 네트워크 아키텍처에 따른 lm-score 비교. 트랜스포머가 U-Net 대비 약 25% 더 낮은 lm-score를 달성하며, 시퀀스 데이터에서 양방향 어텐션의 이점을 보여준다. (Li et al., 2022)*

### 제어 가능한 생성 태스크

논문은 여러 제어 태스크를 다루었다:

| 태스크 | 제어 속성 | 분류기 |
|-------|---------|-------|
| 감성 제어 | 긍정/부정 감성 | SST-2 파인튜닝 |
| 주제 제어 | 주제어(keyword) 포함 | 토픽 모델 |
| 구문 제어 | 파싱 트리 구조 | 파서 기반 |
| 독성 제어 | 독성 없는 생성 | Perspective API |

### 구현 세부사항

| 구성 요소 | 설정 |
|----------|------|
| 임베딩 차원 $d$ | 16, 128 |
| Timesteps $T$ | 2000 |
| 트랜스포머 레이어 | 12 |
| Hidden 크기 | 512 |
| Attention Heads | 8 |
| 데이터셋 | E2E, ROCStories, OpenWebText |
| 배치 크기 | 64 |
| 학습률 | 1e-4 |
| 유도 강도 $\gamma$ | 1.0 ~ 10.0 |

## 실험 결과

### E2E 데이터셋 (조건부 생성)

E2E는 레스토랑 도메인의 데이터-투-텍스트 생성 벤치마크:

| 모델 | BLEU | NIST | METEOR | ROUGE-L | CIDEr |
|------|------|------|--------|---------|-------|
| T5 (fine-tuned) | 68.2 | 8.61 | 46.2 | 71.0 | 2.37 |
| GPT-2 (fine-tuned) | 63.8 | 8.35 | 45.0 | 68.5 | 2.23 |
| **Diffusion-LM** | **64.6** | **8.52** | **45.9** | **70.1** | **2.31** |

### 제어 가능한 생성 결과

구문 구조 제어 (특정 파싱 트리를 따르는 생성):

| 모델 | 구문 정확도 | BLEU-4 | 다양성 |
|------|----------|--------|------|
| GPT-2 + classifier (PPLM) | 52.3% | 22.1 | 0.71 |
| Plug-and-Play LM | 48.7% | 20.8 | 0.68 |
| **Diffusion-LM (guided)** | **82.1%** | **24.3** | **0.79** |

감성 제어 (긍정 감성 생성):

| 모델 | 감성 정확도 | 유창성(PPL) |
|------|----------|----------|
| GPT-2 + PPLM | 71.3% | 48.2 |
| Fudge | 76.8% | 35.6 |
| **Diffusion-LM + 분류기 유도** | **88.4%** | **31.2** |

### 유도 강도 ($\gamma$) 영향

| $\gamma$ | 감성 정확도 | 유창성(PPL) |
|---------|----------|----------|
| 0 (유도 없음) | 52.1% | 28.4 |
| 1 | 71.3% | 29.1 |
| 3 | 88.4% | 31.2 |
| 5 | 93.7% | 36.8 |
| 10 | 96.2% | 52.3 |

유도 강도가 높을수록 속성 정확도는 올라가지만 유창성(PPL)이 떨어지는 전형적인 트레이드오프 관계를 보인다.

### 병렬 생성 속도

동일 길이 시퀀스 생성 시 속도 비교:

| 모델 | 토큰/초 | 비고 |
|------|--------|------|
| GPT-2 (AR) | 156 | 순차 생성 |
| Diffusion-LM (T=2000) | 12 | 전체 시퀀스 병렬 |
| Diffusion-LM (T=200) | 118 | 빠른 샘플링 |

T를 줄이면 속도가 크게 향상되지만 품질이 저하될 수 있다.

## 의의 및 한계

### 의의

- **제어 가능한 생성의 새 패러다임**: 분류기 유도를 텍스트에 최초로 효과적으로 적용
- **연속 임베딩 확산**: 이산성 문제를 임베딩 공간으로 우회하는 아이디어
- **세밀한 속성 제어**: 구문 구조, 감성, 주제 등 다양한 속성을 단일 모델로 제어
- **병렬 생성**: 모든 토큰을 동시에 생성하는 구조적 이점
- **후속 연구 촉진**: DiffuSeq, GENIE 등 제어 가능한 텍스트 생성 연구의 기반

### 한계

- **AR 대비 느린 생성**: $T=2000$ 스텝으로 빠른 AR보다 훨씬 느림
- **rounding 오류**: 연속 임베딩에서 이산 토큰으로 변환 시 오류 발생
- **임베딩 공간의 불일치**: 임베딩 공간과 토큰 공간의 차이로 인한 비효율성
- **제한된 언어 생성 품질**: 순수 언어 모델링 성능에서 AR에 뒤짐
- **높은 계산 비용**: 분류기 그래디언트 계산이 추론 시간 증가

### MDLM/LLaDA와의 비교

| 특성 | Diffusion-LM | MDLM/LLaDA |
|------|-------------|----------|
| 확산 공간 | 연속 임베딩 | 이산 토큰 |
| 노이즈 | 가우시안 | 마스킹 |
| 분류기 유도 | 자연스러운 그래디언트 | 불연속 공간 문제 |
| 언어 모델링 PPL | 높음 (불리) | 낮음 (유리) |
| 구현 복잡성 | 높음 (rounding 필요) | 낮음 |

## 코드 예제

### 임베딩 확산 모델

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


class DiffusionLM(nn.Module):
    """
    Diffusion-LM: 단어 임베딩 공간에서의 연속 확산 모델.
    """

    def __init__(
        self,
        vocab_size: int,
        embed_dim: int = 128,  # 임베딩 차원 (작게 유지)
        d_model: int = 512,
        nhead: int = 8,
        num_layers: int = 12,
        max_len: int = 128,
        T: int = 2000,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.T = T

        # 학습 가능한 단어 임베딩 (작은 차원)
        self.word_embed = nn.Embedding(vocab_size, embed_dim)

        # 확산 입력을 모델 차원으로 투영
        self.input_proj = nn.Linear(embed_dim, d_model)
        self.pos_embed = nn.Embedding(max_len, d_model)

        # 시간 임베딩
        self.time_mlp = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.SiLU(),
            nn.Linear(d_model * 4, d_model),
        )

        # 양방향 트랜스포머
        enc_layer = nn.TransformerEncoderLayer(
            d_model, nhead, d_model * 4,
            dropout=0.1, batch_first=True, norm_first=True
        )
        self.encoder = nn.TransformerEncoder(enc_layer, num_layers)

        # 임베딩 공간으로 역투영
        self.output_proj = nn.Linear(d_model, embed_dim)

        # 노이즈 스케줄 (코사인)
        betas = self._cosine_betas(T)
        alphas = 1.0 - betas
        alphas_bar = torch.cumprod(alphas, dim=0)
        self.register_buffer("betas", betas)
        self.register_buffer("alphas_bar", alphas_bar)

    @staticmethod
    def _cosine_betas(T: int, s: float = 0.008) -> torch.Tensor:
        steps = torch.linspace(0, T, T + 1)
        f = torch.cos((steps / T + s) / (1 + s) * math.pi / 2) ** 2
        alphas_bar = f / f[0]
        betas = 1 - alphas_bar[1:] / alphas_bar[:-1]
        return betas.clamp(0, 0.999)

    def sinusoidal_emb(self, t: torch.Tensor) -> torch.Tensor:
        d = self.input_proj.weight.shape[0]
        half = d // 2
        freqs = torch.exp(
            -math.log(10000)
            * torch.arange(half, device=t.device).float() / half
        )
        x = t[:, None].float() * freqs[None, :]
        return self.time_mlp(torch.cat([x.sin(), x.cos()], dim=-1))

    def forward(
        self,
        x_t: torch.Tensor,  # [B, L, embed_dim] ( 노이즈 임베딩
        t: torch.Tensor,    # [B] ) 정규화된 시간 [0, 1]
    ) -> torch.Tensor:
        """
        노이즈 임베딩 x_t에서 원본 임베딩 x_0 예측.
        Returns: x0_hat [B, L, embed_dim]
        """
        B, L, _ = x_t.shape

        h = self.input_proj(x_t)  # [B, L, d_model]
        pos = torch.arange(L, device=x_t.device).unsqueeze(0)
        h = h + self.pos_embed(pos)
        h = h + self.sinusoidal_emb(t).unsqueeze(1)
        h = self.encoder(h)       # [B, L, d_model]
        return self.output_proj(h)  # [B, L, embed_dim]

    def compute_loss(
        self,
        tokens: torch.Tensor,  # [B, L] 원본 토큰
        lambda_anchor: float = 0.1,
    ) -> torch.Tensor:
        """
        Diffusion-LM 학습 손실:
        L = L_ddpm + lambda * L_anchor
        """
        B, L = tokens.shape
        device = tokens.device

        # 원본 임베딩
        x0 = self.word_embed(tokens)  # [B, L, d]

        # timestep 균등 샘플링
        t_idx = torch.randint(0, self.T, (B,), device=device)
        t_norm = t_idx.float() / self.T

        # 순방향 과정: x_t = sqrt(alpha_bar_t)*x0 + sqrt(1-alpha_bar_t)*eps
        ab = self.alphas_bar[t_idx].to(device)  # [B]
        eps = torch.randn_like(x0)
        x_t = torch.sqrt(ab)[:, None, None] * x0 + \
              torch.sqrt(1 - ab)[:, None, None] * eps  # [B, L, d]

        # x_0 예측
        x0_hat = self.forward(x_t, t_norm)  # [B, L, d]

        # DDPM 손실 (x_0 예측 방식)
        l_simple = F.mse_loss(x0_hat, x0)

        # Anchor 손실: 예측 임베딩이 어휘 임베딩에 가깝도록
        # x0_hat → nearest vocab embedding과의 거리
        l_anchor = l_simple  # 간소화: 실제로는 어휘 임베딩 최소 거리

        return l_simple + lambda_anchor * l_anchor
```

### 분류기 유도 생성

```python
class AttributeClassifier(nn.Module):
    """노이즈 임베딩에서 속성(감성, 주제 등) 분류."""

    def __init__(self, embed_dim: int, num_classes: int, d_model: int = 256):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(embed_dim, d_model),
            nn.ReLU(),
            nn.Linear(d_model, num_classes),
        )

    def forward(self, x_t: torch.Tensor) -> torch.Tensor:
        # [B, L, d] -> [B, L, num_classes] -> [B, num_classes] (pooling)
        return self.encoder(x_t).mean(dim=1)


@torch.no_grad()
def guided_generation(
    model: DiffusionLM,
    classifier: AttributeClassifier,
    target_class: int,
    seq_len: int,
    gamma: float = 3.0,
    device: str = "cuda",
) -> torch.Tensor:
    """
    분류기 유도 확산: 특정 속성(감성, 주제 등)을 갖는 텍스트 생성.

    Args:
        model: 학습된 Diffusion-LM
        classifier: 속성 분류기
        target_class: 목표 속성 인덱스
        seq_len: 생성할 시퀀스 길이
        gamma: 유도 강도 (클수록 속성에 더 가깝게 생성)
    """
    T = model.T
    d = model.embed_dim

    # t=T에서 순수 가우시안 노이즈로 시작
    x_t = torch.randn(1, seq_len, d, device=device)

    for t_idx in reversed(range(1, T)):
        t_norm = torch.tensor([t_idx / T], device=device)

        # 1) 비조건부 디노이징 평균 계산
        with torch.no_grad():
            x0_hat = model(x_t, t_norm)  # [1, L, d]

        # DDPM 역방향 평균 계산
        ab_t = model.alphas_bar[t_idx].to(device)
        ab_prev = model.alphas_bar[t_idx - 1].to(device) if t_idx > 0 else torch.tensor(1.0, device=device)
        beta_t = model.betas[t_idx].to(device)

        # x_{t-1}의 평균: DDPM 공식
        coef1 = torch.sqrt(ab_prev) * beta_t / (1 - ab_t)
        coef2 = torch.sqrt(1 - beta_t) * (1 - ab_prev) / (1 - ab_t)
        mu = coef1 * x0_hat + coef2 * x_t

        # 2) 분류기 유도: 그래디언트 계산
        x_t_guided = x_t.clone().requires_grad_(True)
        log_p_c = torch.log_softmax(
            classifier(x_t_guided), dim=-1
        )[:, target_class]  # 목표 클래스 로그 확률
        grad = torch.autograd.grad(log_p_c.sum(), x_t_guided)[0]

        # 3) 유도 적용: 평균 조정
        sigma_t = torch.sqrt(beta_t)
        mu_guided = mu + gamma * (sigma_t ** 2) * grad.detach()

        # 4) 샘플링
        if t_idx > 1:
            noise = torch.randn_like(x_t)
            x_t = mu_guided + sigma_t * noise
        else:
            x_t = mu_guided  # 마지막 스텝은 노이즈 없음

    # 연속 임베딩 -> 이산 토큰 (nearest neighbor rounding)
    final_embeds = x_t.squeeze(0)  # [L, d]
    all_embeds = model.word_embed.weight  # [V, d]
    dists = torch.cdist(final_embeds, all_embeds)  # [L, V]
    tokens = dists.argmin(dim=-1)  # [L]
    return tokens


# 사용 예시:
# model = DiffusionLM(vocab_size=50257).to("cuda")
# classifier = AttributeClassifier(embed_dim=128, num_classes=2).to("cuda")
#
# # 긍정 감성 텍스트 생성 (target_class=1: positive)
# tokens = guided_generation(
#     model, classifier, target_class=1,
#     seq_len=64, gamma=3.0, device="cuda"
# )
# print(tokenizer.decode(tokens.tolist()))
```

## 관련 문서

- [[ddpm|DDPM: Denoising Diffusion Probabilistic Models]] ( Diffusion-LM의 기반 확산 모델
- [[d3pm|D3PM: Structured Denoising Diffusion in Discrete State-Spaces]] ) 이산 확산의 대안 접근
- [[diffu-seq|DiffuSeq]] ( Diffusion-LM을 Seq2Seq에 확장
- [[classifier-guidance|Classifier-Free Guidance]] ) 이미지에서 분류기 유도의 원형
- [[score-sde|Score SDE]], 연속 시간 확산의 수학적 기반
