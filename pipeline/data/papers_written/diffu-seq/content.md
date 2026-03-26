## 개요

DiffuSeq(Gong et al., ICLR 2023)는 확산 모델(Diffusion Model)을 **조건부 Seq2Seq 텍스트 생성**에 직접 적용한 연구다. 기존 언어 모델이 자기회귀(autoregressive) 방식으로 토큰을 하나씩 순차적으로 생성하는 것과 달리, DiffuSeq는 목표 시퀀스 전체를 연속 임베딩 공간(continuous embedding space)에서 반복적으로 탈노이징(denoising)하며 **비자기회귀(non-autoregressive)** 방식으로 한 번에 생성한다.

핵심 기여는 세 가지로 요약된다:
1. 소스 시퀀스를 조건으로 활용하는 **부분 노이징(partial noising)** 전략
2. Classifier-Free Guidance의 Seq2Seq 확장
3. 최종 샘플 선택을 위한 **MBR(Minimum Bayes Risk) 디코딩**

## 배경 및 문제

확산 모델은 이미지 생성(DALL-E 2, Stable Diffusion 등)에서 탁월한 성능을 보였지만, 텍스트는 본질적으로 **이산(discrete) 공간**에 존재하기 때문에 연속 확산 과정을 직접 적용하기 어렵다. Diffusion-LM(Li et al., 2022)은 단어 임베딩 공간에서 연속 확산을 수행해 이 간극을 좁혔으나, 비조건부(unconditional) 또는 classifier-guided 생성에 한정되어 있어 입력 시퀀스가 주어졌을 때 출력 시퀀스를 생성하는 **Seq2Seq** 설정에는 적합하지 않았다.

아래 그림은 기존 확산 모델 접근법과 DiffuSeq의 차이를 직관적으로 보여준다.

![비조건부, Classifier-guided, Classifier-free 확산 모델 비교](figures/fig_1.png)
*Figure 1. 연속 공간에서의 확산 모델 비교. (a) 비조건부 가우시안 확산, (b) Diffusion-LM의 classifier-guided 방식, (c) DiffuSeq의 classifier-free 방식. DiffuSeq는 조건 신호(주황색 점)가 공간 내 점(파란색)으로 직접 가이드를 제공하여 별도의 classifier 없이도 조건부 생성을 수행한다.*

자기회귀 모델(T5, BART 등)은 Seq2Seq에서 강력한 성능을 보이지만, **노출 편향(exposure bias)** -- 학습 시에는 정답 토큰을 보지만 추론 시에는 자신의 예측에 의존하는 불일치 -- 과 좌-우 방향의 **순차적 의존성 가정**의 한계가 있다. DiffuSeq는 확산 모델의 반복적 정제(iterative refinement) 능력을 Seq2Seq 프레임워크에 결합해 이러한 문제를 우회하고자 한다.

다음 그림은 DiffuSeq를 포함한 다양한 생성 모델의 확률 그래프 모델(graphical model) 비교를 보여준다.

![AR, NAR, Iterative NAR, DiffuSeq 그래프 모델 비교](figures/fig_9.png)
*Figure 2. 자기회귀(AR), 완전 비자기회귀(Fully NAR), 반복적 비자기회귀(Iterative NAR), DiffuSeq 모델의 그래프 모델 비교. 회색 노드는 소스 시퀀스에 대한 의존성을 나타내고, 흰색 노드는 소스와 독립적인 노드를 의미한다. DiffuSeq는 반복적 정제를 통해 모든 목표 토큰이 소스에 의존하면서도 토큰 간 양방향 의존성을 포착한다.*

## 핵심 아이디어

**부분 노이징(Partial Noising)**이 DiffuSeq의 핵심이다. 소스 시퀀스 $\mathbf{w}^x$와 목표 시퀀스 $\mathbf{w}^y$를 각각 임베딩 함수 $\text{Emb}(\cdot)$을 통해 연속 벡터로 변환한 뒤, **목표 임베딩 $\mathbf{z}_0^y = \text{Emb}(\mathbf{w}^y)$에만 가우시안 노이즈를 추가**하고 소스 임베딩 $\mathbf{z}_0^x = \text{Emb}(\mathbf{w}^x)$는 깨끗한 상태로 유지한다. 두 표현을 연결(concatenate)하여 모델의 입력을 구성한다:

$$\mathbf{x}_t = \text{concat}(\text{Emb}(\mathbf{w}^x),\ \mathbf{z}_t^y)$$

여기서 $\mathbf{z}_t^y$는 시각 $t$에서 노이즈가 추가된 목표 임베딩이다. 이 구조 덕분에 소스 시퀀스가 Transformer의 self-attention 메커니즘 전반에 걸쳐 목표 시퀀스 탈노이징 과정에 **자연스럽게 개입**할 수 있다. 별도의 encoder-decoder 구조 없이도 소스 조건이 모든 attention layer에서 목표 토큰에 직접 영향을 미친다.

## 방법론

### 순방향 프로세스 (Forward Process)

DiffuSeq의 순방향 프로세스는 표준 DDPM의 가우시안 노이즈 스케줄을 **목표 임베딩에만** 적용한다. 시각 $t$에서의 노이즈 추가는 다음과 같이 정의된다:

$$q(\mathbf{z}_t^y \mid \mathbf{z}_0^y) = \mathcal{N}(\mathbf{z}_t^y;\ \sqrt{\bar{\alpha}_t}\, \mathbf{z}_0^y,\ (1-\bar{\alpha}_t)\mathbf{I})$$

여기서 $\bar{\alpha}_t = \prod_{s=1}^{t}(1-\beta_s)$는 누적 노이즈 스케줄이다. 핵심은 **소스 임베딩이 $t$에 관계없이 $\mathbf{z}_0^x$로 고정**된다는 점이다. 이를 통해 역방향 과정에서 소스 정보가 손실 없이 조건으로 활용된다.

아래 그림은 DiffuSeq의 전체 확산 과정을 시각적으로 보여준다.

![DiffuSeq 부분 노이징 확산 과정](figures/fig_2.png)
*Figure 3. DiffuSeq의 확산 과정. 소스 $\mathbf{w}^x$와 목표 $\mathbf{w}^y$를 연속 공간 $\mathbf{z}_0$로 변환한 뒤, 목표 영역에만 부분 가우시안 노이즈를 반복적으로 추가한다. 역방향 과정에서는 소스 임베딩을 깨끗한 조건으로 유지하면서 목표 임베딩만 탈노이징한다.*

### 역방향 프로세스 (Reverse Process)

역방향 프로세스에서는 Transformer 기반 노이즈 예측 네트워크 $\epsilon_\theta$가 연결된 입력 $(\mathbf{z}_0^x, \mathbf{z}_t^y, t)$를 받아 추가된 노이즈를 추정한다. 학습 목적 함수는 표준 DDPM의 단순화된 목적 함수와 동일한 형태를 따른다:

$$\mathcal{L}_{\text{simple}}(\theta) = \mathbb{E}_{q(\mathbf{z}_0^y|\mathbf{w}^y)}\,\mathbb{E}_{t,\,\epsilon}\left[\|\epsilon_\theta(\mathbf{z}_t^y,\ \mathbf{z}_0^x,\ t) - \epsilon\|^2\right]$$

추가로, 임베딩 공간과 이산 토큰 공간 사이의 정렬을 강화하기 위해 Diffusion-LM에서 도입된 **앵커 손실(anchor loss)**을 보조적으로 사용한다:

$$\mathcal{L}_{\text{anchor}} = \|\mathbf{z}_0 - \text{Emb}(\mathbf{w})\|^2$$

최종 손실은 두 항의 가중합으로 구성된다.

### Classifier-Free Guidance 적용

이미지 도메인에서 조건부 생성 품질을 크게 향상시킨 Classifier-Free Guidance(CFG)를 Seq2Seq 설정에 맞게 확장한다. 학습 시 일정 확률 $p_{\text{uncond}}$로 소스 임베딩을 **null 벡터** $\emptyset$로 대체해 조건 없는 예측을 함께 학습하고, 추론 시 두 예측을 선형 보간하여 조건 반영 강도를 조절한다:

$$\tilde{\epsilon}_\theta = \epsilon_\theta(\mathbf{z}_t^y, \emptyset, t) + s \cdot \big(\epsilon_\theta(\mathbf{z}_t^y, \mathbf{z}_0^x, t) - \epsilon_\theta(\mathbf{z}_t^y, \emptyset, t)\big)$$

가이던스 스케일 $s$가 핵심 하이퍼파라미터로, $s > 1$이면 소스 조건에 대한 의존도를 높여 **품질(fidelity)**이 향상되고, $s < 1$이면 조건 의존도를 낮춰 **다양성(diversity)**이 증가한다.

### MBR(Minimum Bayes Risk) 디코딩

확산 모델은 확률적 샘플링 특성상 한 번의 추론으로 **여러 다양한 후보 샘플**을 생성할 수 있다. MBR 디코딩은 $N$개 후보 샘플 집합 $\mathcal{S} = \{y_1, \ldots, y_N\}$ 중에서 전체 후보에 대해 평균적으로 가장 높은 유사도를 달성하는 샘플을 최종 출력으로 선택한다:

$$\hat{y} = \arg\max_{y_i \in \mathcal{S}} \frac{1}{N} \sum_{j=1}^{N} \text{BLEU}(y_i, y_j)$$

이를 통해 단순히 가장 그럴듯한 단일 샘플이 아닌, **집합 수준에서 대표성이 높은** 합의(consensus) 출력을 얻는다. 이 전략은 자기회귀 모델에서는 활용하기 어려운, 확산 모델의 고유한 장점이다.

## 실험 결과

네 가지 Seq2Seq 벤치마크에서 DiffuSeq의 성능을 평가했다.

- **텍스트 단순화(Text Simplification)**: Newsela 데이터셋에서 SARI 및 FKGL 지표를 측정. 자기회귀 베이스라인 대비 경쟁력 있는 성능을 달성.
- **패러프레이즈(Paraphrase)**: QQP 데이터셋에서 의미를 보존하면서 표현을 바꾸는 과제. 다양성(diversity) 지표에서 자기회귀 모델 대비 유의미하게 높은 점수.
- **질문 생성(Question Generation)**: SQuAD 기반 QG 태스크에서 ROUGE 및 BLEU 측정. ProphetNet, BART와 비슷하거나 우수한 성능.
- **기계번역(Machine Translation)**: IWSLT14 De→En에서 BLEU 기반 비교. 비자기회귀 모델 중 최상위권.

### 품질-다양성 트레이드오프

DiffuSeq의 가장 두드러진 특성 중 하나는 품질(quality)과 다양성(diversity) 사이의 트레이드오프를 명시적으로 제어할 수 있다는 점이다. 아래 그림은 질문 생성 태스크에서 이 트레이드오프를 시각화한 결과다.

![품질-다양성 트레이드오프 시각화](figures/fig_5.png)
*Figure 4. 질문 생성 태스크에서의 품질(BLEU)-다양성(div-4) 트레이드오프. DiffuSeq는 가이던스 스케일 $s$를 조절함으로써 품질-다양성 파레토 프론티어 위를 이동할 수 있다. GPT2 변형들은 고정된 단일 지점에 위치하는 반면, DiffuSeq는 유연한 제어가 가능하다.*

CFG 가이던스 스케일 $s$를 높이면 BLEU 점수(품질)가 올라가지만 다양성(div-4)은 감소하고, $s$를 낮추면 반대 경향을 보인다. GPT2-base, GPT2-large 같은 자기회귀 모델은 이러한 연속적인 제어가 불가능하여 그래프 상에서 고정된 점으로 나타난다.

MBR 디코딩을 적용했을 때 후보 수 $|\mathcal{S}|$가 증가할수록 일관된 BLEU 향상이 관찰되었으며, 이는 확산 모델이 생성하는 다양한 샘플들 사이에서 최적의 대표 샘플을 효과적으로 선별할 수 있음을 보여준다.

### 추론 속도와 품질

확산 모델의 실용적 한계 중 하나인 추론 속도에 대해서도 분석이 이루어졌다. 아래 그림은 샘플링 스텝 수에 따른 BLEU 점수와 생성 속도의 관계를 보여준다.

![샘플링 스텝에 따른 BLEU 점수와 추론 속도](figures/fig_6_2.png)
*Figure 5. 질문 생성 태스크에서 샘플링 스텝 수에 따른 DiffuSeq의 BLEU 점수(파란 선)와 생성 속도(주황 막대). 점선은 GPT2-large의 BLEU와 속도 기준선을 나타낸다. 스텝 수가 2000일 때 GPT2-large를 상회하는 BLEU를 달성하지만, 생성 속도는 상당히 느리다.*

샘플링 스텝 수를 줄이면 추론 속도는 빨라지지만 품질이 하락하는 트레이드오프가 존재한다. 2000 스텝에서 GPT2-large를 능가하는 BLEU를 달성하지만, 생성 속도(samples/sec)는 크게 뒤처진다. 이는 확산 기반 텍스트 생성의 실용화를 위해 효율적인 샘플링 기법(DDIM 등)의 적용이 필수적임을 시사한다.

## 의의 및 한계

### 의의

DiffuSeq는 확산 모델을 Seq2Seq 조건부 생성으로 확장한 **선구적 연구**다. 부분 노이징이라는 단순하지만 효과적인 설계로 소스 정보를 확산 과정 전반에 흘려 넣고, 비자기회귀 생성의 **출력 다양성**을 MBR 디코딩과 결합해 실용적인 성능을 확보했다. 특히 품질-다양성 트레이드오프를 연속적으로 제어할 수 있다는 점은 자기회귀 모델에서는 달성하기 어려운 고유한 장점이다. 이후 SeqDiffuSeq, GENIE, DiffuSeq-v2 등 다수의 후속 연구에 영향을 주었다.

### 한계

- **추론 속도**: 수백~수천 번의 탈노이징 스텝이 필요하며, 빠른 샘플링(DDIM 등)을 적용해도 T5/BART 대비 상당한 지연이 발생한다.
- **임베딩-토큰 정렬**: 긴 시퀀스에서 연속 임베딩 공간과 이산 토큰 공간 사이의 정렬(rounding)이 불완전해 생성 품질이 저하될 수 있다.
- **사전학습 부재**: GPT-4 등 대규모 사전학습 언어 모델과 달리, DiffuSeq는 태스크별로 처음부터 학습하므로 범용 언어 지식 활용에 한계가 있다.
- **길이 예측**: 비자기회귀 생성 특성상 목표 시퀀스의 길이를 사전에 결정하거나 예측해야 하는 추가적인 제약이 존재한다.

## 코드 예제

아래는 부분 노이징과 조건부 입력 구성을 PyTorch 스타일로 단순화한 예시다.

```python
import torch
import torch.nn as nn

class DiffuSeqForwardProcess:
    """DiffuSeq 순방향 프로세스: 목표 임베딩에만 노이즈 추가"""

    def __init__(self, num_timesteps: int = 2000, beta_start: float = 1e-4, beta_end: float = 0.02):
        betas = torch.linspace(beta_start, beta_end, num_timesteps)
        alphas = 1.0 - betas
        self.alphas_bar = torch.cumprod(alphas, dim=0)  # \bar{\alpha}_t

    def q_sample(self, z0_y: torch.Tensor, t: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """목표 임베딩 z0_y에 시각 t의 노이즈를 추가. 소스는 건드리지 않음."""
        alpha_bar_t = self.alphas_bar[t].view(-1, 1, 1)  # (B, 1, 1)
        eps = torch.randn_like(z0_y)
        zt_y = alpha_bar_t.sqrt() * z0_y + (1 - alpha_bar_t).sqrt() * eps
        return zt_y, eps


class DiffuSeqModel(nn.Module):
    """소스 임베딩을 조건으로 목표 노이즈를 예측하는 Transformer"""

    def __init__(self, embed_dim: int = 128, num_heads: int = 8, num_layers: int = 6):
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim, nhead=num_heads, batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.time_embed = nn.Embedding(2000, embed_dim)
        self.out_proj = nn.Linear(embed_dim, embed_dim)

    def forward(
        self,
        z0_x: torch.Tensor,   # 소스 임베딩 (B, src_len, D) — 노이즈 없음
        zt_y: torch.Tensor,   # 목표 노이즈 임베딩 (B, tgt_len, D)
        t: torch.Tensor,      # 타임스텝 (B,)
    ) -> torch.Tensor:
        # 타임스텝 임베딩을 목표 시퀀스의 각 위치에 더함
        t_emb = self.time_embed(t).unsqueeze(1)          # (B, 1, D)
        zt_y = zt_y + t_emb                              # 시간 조건 주입

        # 소스(조건)와 목표(노이즈)를 연결해 Transformer에 입력
        x = torch.cat([z0_x, zt_y], dim=1)              # (B, src+tgt, D)
        h = self.transformer(x)

        # 목표 시퀀스 위치만 추출해 노이즈 예측
        src_len = z0_x.size(1)
        eps_pred = self.out_proj(h[:, src_len:, :])      # (B, tgt_len, D)
        return eps_pred


def compute_diffu_seq_loss(
    model: DiffuSeqModel,
    forward_process: DiffuSeqForwardProcess,
    z0_x: torch.Tensor,
    z0_y: torch.Tensor,
    device: str = "cpu",
) -> torch.Tensor:
    """DiffuSeq 학습 손실: ||eps_theta(zt_y, z0_x, t) - eps||^2"""
    B = z0_y.size(0)
    t = torch.randint(0, len(forward_process.alphas_bar), (B,), device=device)
    zt_y, eps = forward_process.q_sample(z0_y, t)
    eps_pred = model(z0_x, zt_y, t)
    loss = ((eps_pred - eps) ** 2).mean()
    return loss
```

## 관련 문서

- Diffusion-LM (Li et al., 2022): 연속 임베딩 공간에서의 비조건부 텍스트 확산 기초
- DDPM (Ho et al., NeurIPS 2020): 가우시안 확산 모델 원형
- Classifier-Free Guidance (Ho & Salimans, 2022): 조건 강도 조절 기법
- GENIE (Lin et al., 2023): 확산 기반 Seq2Seq 후속 연구
- SeqDiffuSeq (Yuan et al., 2022): 토큰 단위 적응형 노이즈 스케줄
