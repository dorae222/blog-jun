## 개요

**MDLM(Masked Diffusion Language Model)**은 Sahoo et al.이 NeurIPS 2024에서 발표한 이산 확산 언어 모델이다. 핵심 기여는 마스크(흡수) 확산 과정에 대한 엄밀하고 깔끔한 ELBO(Evidence Lower Bound)를 유도하고, 이를 단순한 가중 교차 엔트로피 목표로 환원하는 것이다.

아래 Figure 1은 MDLM의 전체 구조와 핵심 아이디어를 요약한다. 왼쪽은 다양한 마스킹 비율에서의 가중 교차 엔트로피 손실 평균으로 훈련하는 과정을, 오른쪽 상단은 기존 MLM과의 차이점(원리적 변분 하한 + 조상 샘플링 지원)을, 오른쪽 하단은 One Billion Words 벤치마크에서의 퍼플렉시티 비교를 보여준다.

![MDLM 구조 및 MLM 대비 특성 요약](figures/fig_1.png)
*Figure 1: (왼쪽) MDLM은 다양한 마스킹 비율에서의 마스크 교차 엔트로피 손실의 가중 평균으로 훈련된다. (오른쪽 상단) MLM과 달리 MDLM의 목표는 원리적인 변분 하한에 대응하며, 조상 샘플링을 통한 생성을 지원한다. (오른쪽 하단) One Billion Words 벤치마크에서 AR(20.8) 대비 MDLM(23.3)은 이산 확산 모델 중 가장 낮은 퍼플렉시티를 달성한다.*

기존 이산 확산 모델(D3PM, SEDD 등)은 수식이 복잡하거나 훈련이 불안정한 문제가 있었다. MDLM은 흡수(absorbing) 확산만을 사용하되, 연속 시간 변분 목표를 엄밀히 유도하여 구현의 단순성과 성능을 동시에 달성한다. 이후 LLaDA(8B 규모)와 같은 대규모 마스크 확산 LLM 연구가 MDLM의 훈련 목표를 그대로 계승하면서, 이 접근법의 확장 가능성이 입증되었다.

## 배경 및 문제

이산 확산 모델은 연속 확산(DDPM 등)을 텍스트와 같은 범주형 데이터에 적용하는 시도에서 출발한다. 대표적인 선행 연구는 다음과 같다.

- **D3PM**: 마스킹, 균등, 흡수 등 다양한 전이 행렬을 통합하는 일반 프레임워크. 수식이 복잡하고 훈련 목표가 tight하지 않다.
- **SEDD(Score Entropy Discrete Diffusion)**: 스코어 엔트로피 기반 목표를 사용해 좋은 성능을 보이지만, 목표 함수 유도가 복잡하고 구현 비용이 크다.

이 논문이 지적하는 핵심 문제는 두 가지다. 첫째, 텍스트에 균등(uniform) 전이를 사용하는 것은 흡수(absorbing) 전이에 비해 불필요하게 복잡하다. 균등 전이에서는 노이즈 토큰이 어휘 내 임의의 단어로 치환되므로, 모델이 "이것이 원본인가, 노이즈인가"를 먼저 구분해야 한다. 반면 흡수 전이에서는 [MASK] 토큰이 명시적 신호 역할을 하므로 즉시 복원에 집중할 수 있다. 둘째, 기존 ELBO 유도는 tight하지 않거나 연속 시간으로 자연스럽게 확장되지 않는다.

## 핵심 아이디어

MDLM의 핵심 통찰은 **흡수(마스킹) 확산이 텍스트에 대해 균등 확산보다 근본적으로 더 단순하고 더 나은 귀납 편향을 제공한다**는 것이다.

흡수 확산에서 각 토큰은 독립적으로 마스크 토큰 $m$으로 대체될 수 있다. "HELLO WORLD" → "HELLO [MASK]" → "[MASK] [MASK]"처럼 진행된다. 이 과정은 다음의 특성을 가진다.

- 각 차원이 독립적으로 작동하므로 전이 행렬의 텐서 분해가 가능하다.
- 조건부 독립 구조 덕분에 ELBO가 닫힌 형태로 계산된다.
- 균등 확산에서 필요한 복잡한 분모 계산이 필요 없다.

이러한 구조적 단순성이 바로 MDLM이 복잡한 스코어 매칭(SEDD)이나 다중 KL 발산 합(D3PM) 없이도 경쟁력 있는 성능을 달성하는 핵심 요인이다.

## 방법론

### 순전파 과정 (Forward Process)

흡수 확산의 순전파는 각 토큰 차원에 대해 독립적으로 정의된다.

$$q_{t|0}(x_t|x_0) = \prod_{d=1}^D \text{Cat}\!\left(x_t^d;\, (1-\alpha_t)\, x_0^d + \alpha_t\, m\right)$$

여기서 $\alpha_t \in [0, 1]$은 시각 $t$에서의 마스킹 비율이고, $m$은 [MASK] 토큰의 원-핫 벡터다. $t=0$에서는 원본 토큰, $t=1$에서는 완전 마스킹이 된다. 이 정의가 핵심적으로 중요한 이유는 각 차원의 독립성 덕분에 역전파 $q_{t-1|t,0}$도 닫힌 형태를 갖게 되어, ELBO를 정확히 분해할 수 있기 때문이다.

### 이산 시간 ELBO 유도

순전파의 마르코프 구조를 이용하면, 역과정 ELBO는 모든 오염 레벨에 대한 합으로 정확히 분해된다.

$$\text{ELBO} = \mathbb{E}_{q}\!\left[\sum_{t=1}^T \text{CE}(x_0 \mid x_t) \cdot w_t\right]$$

각 $w_t$는 마스킹 비율의 차이 $\alpha_t - \alpha_{t-1}$에 비례하는 가중치다. 이 분해가 성립하는 이유는 흡수 확산의 역전파 $q_{t-1|t,0}$가 닫힌 형태를 갖기 때문이다. 마스크된 위치에서만 예측 오류가 발생하므로, 목표는 실질적으로 마스크 위치에 대한 가중 교차 엔트로피가 된다. 이 표현은 D3PM의 복잡한 KL 합계와 달리 추가적인 근사 없이 정확히 성립한다는 점에서, MDLM의 이론적 기여가 크다.

### 연속 시간 MDLM 목표

이산 시간 ELBO를 연속 시간 극한으로 확장하면 MDLM의 최종 훈련 목표가 된다.

$$\mathcal{L}_{\text{MDLM}} = \mathbb{E}_t\, \mathbb{E}_{q_{t|0}(x_t|x_0)}\!\left[\frac{\alpha'_t}{1-\alpha_t}\, \|x_0 - p_\theta(x_0 \mid x_t)\|^2_{\text{mask}}\right]$$

여기서 $\alpha'_t = d\alpha_t/dt$이고, $\|\cdot\|^2_{\text{mask}}$는 마스크된 위치에서만 손실을 계산하는 마스크 제곱 오차다. 가중치 $\alpha'_t/(1-\alpha_t)$는 시각 $t$에서 마스크 위치에 대한 예측의 중요도를 나타낸다.

실용적으로는 **균일 가중치**($w_t = 1$)가 이론적 가중치보다 더 나은 성능을 보이며, 구현도 단순해진다. 이는 최적화 관점에서 균형 잡힌 그래디언트가 편향된 가중치보다 효과적이기 때문으로 해석된다. 실제 구현에서는 $\alpha_t = 1 - \cos^2(\pi t / 2)$와 같은 코사인 스케줄을 사용한다.

### MDLM vs 선행 모델 비교

| 항목 | D3PM-Absorb | SEDD | MDLM |
|------|------------|------|------|
| 전이 유형 | 흡수 | 균등/흡수 | 흡수 |
| ELBO tight 여부 | 아니오 | 해당 없음 | 예 |
| 손실 함수 | 복잡한 KL 합 | 스코어 엔트로피 | 단순 가중 CE |
| 훈련 안정성 | 낮음 | 중간 | 높음 |
| 구현 난이도 | 중간 | 높음 | 낮음 |

흡수 확산은 균등 확산에 비해 훈련 신호가 명확하다. 균등 확산에서는 노이즈 토큰이 어휘 내 임의의 다른 단어이므로, 모델이 "이것이 진짜 문맥인가, 노이즈인가"를 학습해야 한다. 흡수 확산에서는 [MASK] 토큰이 명시적 신호 역할을 하므로, 모델이 오염 여부를 즉시 파악하고 복원에 집중할 수 있다.

### 추론 (Ancestral Sampling)

추론은 완전 마스킹 상태 $x_1 = [M, M, \ldots, M]$에서 시작해 역방향으로 순차 복원한다. 각 스텝에서 $p_\theta(x_0|x_t)$를 계산하고, 후방 분포 $q(x_{t-1}|x_t, x_0)$를 이용해 아직 복원되지 않은 마스크 위치를 확률적으로 복원한다. 트랜스포머 백본을 사용하는 경우 KV 캐시를 활용해 추론 효율을 높일 수 있다. 50 스텝 이후에는 성능 향상이 미미하므로 50 스텝이 최적의 균형점이다.

## 실험 결과

GPT-2 규모 모델(약 110M-168M 파라미터)을 동일한 훈련 토큰으로 학습한 뒤 언어 모델 퍼플렉시티(PPL)를 비교했다.

| 모델 | 방식 | WikiText-103 PPL | 비고 |
|------|------|-----------------|------|
| GPT-2 (124M) | AR | 29.4 | 자기회귀 기준선 |
| D3PM-Absorb | 이산 확산 | 76.4 | tight하지 않은 ELBO |
| SEDD-Absorb | 이산 확산 | ~44 | 스코어 엔트로피 |
| **MDLM (168M)** | **마스크 확산** | **26.2** | tight ELBO + 균일 가중치 |

핵심 비교 결과는 세 가지다. (1) MDLM은 SEDD보다 단순한 공식을 사용하면서 동등하거나 더 나은 퍼플렉시티를 달성한다. (2) D3PM-Absorb 대비 tight한 ELBO 유도만으로도 큰 성능 향상이 가능함을 보인다. (3) 균등 확산 변형(D3PM-Uniform, SEDD-Uniform)은 흡수 변형보다 일관되게 성능이 낮아, 흡수 전이가 텍스트에 적합한 귀납 편향임을 확인한다.

가중치 ablation에서는 이론적 가중치 $\alpha'_t/(1-\alpha_t)$보다 균일 가중치가 PPL 26.2를 달성하며 더 좋은 결과를 낸다. 노이즈 스케줄 ablation에서는 코사인 스케줄이 선형 스케줄(PPL 28.9)보다 우수하다. 생성 품질(Mauve 점수) 기준으로도 MDLM은 50 스텝에서 GPT-2(0.942) 수준에 근접한 0.921을 달성한다.

아래 Figure 2는 OpenWebText에서 64개 샘플을 생성할 때의 벽시계 시간(wall clock time) 대비 생성 퍼플렉시티를 비교한 결과다. 역방향 확산 스텝 수 $T$를 100에서 10,000까지 변화시키며 AR, SEDD, MDLM(캐싱 유/무)을 비교하였다. MDLM은 KV 캐시 활용 시 AR 모델과 유사한 시간 내에 경쟁력 있는 퍼플렉시티를 달성하며, 캐싱 없이도 SEDD 대비 효율적인 생성이 가능함을 보여준다.

![OpenWebText에서 모델별 생성 퍼플렉시티 vs 벽시계 시간 비교](figures/fig_2.png)
*Figure 2: 32GB A5000 GPU 단일 장치에서 OWT 64개 샘플 생성 시, 역방향 스텝 수 $T \in \{100, 500, 1000, 5000, 10000\}$에 따른 벽시계 시간 대비 생성 퍼플렉시티 비교. MDLM(캐싱 적용)은 AR 모델과 유사한 효율을 보이며, 스텝 수가 적을수록 속도 이점이 두드러진다.*

아래 Figure 3은 OpenWebText에서 1M 그래디언트 스텝(약 524B 토큰)에 걸친 훈련 NLL(음의 로그 가능도) 곡선을 보여준다. MDLM은 학습 초반부터 빠르게 수렴하여 최종적으로 SEDD 및 기존 방법들과 동등하거나 더 낮은 NLL에 도달한다. 이는 tight한 ELBO 유도와 균일 가중치 전략이 안정적인 훈련 동역학을 제공함을 실증적으로 뒷받침한다.

![OpenWebText에서의 훈련 NLL 수렴 곡선](figures/fig_3.png)
*Figure 3: OpenWebText에서 1M 그래디언트 스텝에 걸친 훈련 NLL 곡선. 1K 스텝마다 기록하였으며 값 스무딩은 적용하지 않았다. MDLM은 안정적으로 수렴하여 경쟁 모델들과 동등한 NLL에 도달한다.*

## 의의 및 한계

**의의**는 세 가지다. 첫째, 흡수 확산의 ELBO를 엄밀하게 유도하여 이후 이산 확산 연구의 이론적 토대가 된다. 특히 LLaDA(8B 규모 마스크 확산 LLM)와 같은 대규모 후속 연구는 MDLM의 훈련 목표를 그대로 계승한다. 둘째, 단순한 구현(표준 트랜스포머 + 마스크 CE 손실)으로 경쟁력 있는 성능을 달성해 실용적 접근성이 높다. 셋째, 흡수 vs 균등 확산에 대한 체계적 비교를 통해 설계 공간을 명확히 한다.

**한계**는 두 가지다. 첫째, 자기회귀 모델(GPT 계열) 대비 여전히 퍼플렉시티 격차가 존재한다. 다만 Figure 1의 오른쪽 하단에서 확인할 수 있듯이, One Billion Words 벤치마크에서 AR(20.8) 대비 MDLM(23.3)으로 격차가 상당히 줄어들었다. 둘째, 고품질 생성을 위해 많은 디노이징 스텝이 필요하며, 병렬 디코딩의 이점을 충분히 활용하려면 스텝 수-품질 트레이드오프를 신중히 조정해야 한다. Figure 2에서 볼 수 있듯이, 스텝 수가 적을 때 캐싱의 효과가 가장 크며 실용적 배포 시 이 균형점을 찾는 것이 중요하다.

## 코드 예제

MDLM 훈련 루프의 핵심 부분을 PyTorch로 나타내면 다음과 같다.

```python
import math
import torch
import torch.nn.functional as F


def cosine_schedule(t: torch.Tensor) -> torch.Tensor:
    """코사인 노이즈 스케줄: alpha_t = 1 - cos^2(pi*t/2)"""
    return 1.0 - torch.cos(t * math.pi / 2) ** 2


def mdlm_loss(
    model,
    x0: torch.Tensor,
    mask_token_id: int = 103,
) -> torch.Tensor:
    """
    MDLM 훈련 손실 (균일 가중치 버전).

    x0: (B, L) 원본 토큰 시퀀스
    반환: 스칼라 손실값
    """
    B, L = x0.shape
    device = x0.device

    # 1) 연속 시간 t ~ Uniform(0, 1) 샘플링
    t = torch.rand(B, device=device) * (1.0 - 1e-4) + 1e-4
    alpha_t = cosine_schedule(t).unsqueeze(1)  # (B, 1)

    # 2) 순전파: 흡수 확산 q_{t|0}(x_t|x_0)
    #    각 토큰을 alpha_t 확률로 독립적으로 [MASK]로 대체
    is_masked = torch.bernoulli(alpha_t.expand(B, L)).bool()  # (B, L)
    x_t = x0.clone()
    x_t[is_masked] = mask_token_id

    # 3) 역방향 예측: p_theta(x_0 | x_t, t)
    logits = model(x_t, t)  # (B, L, V)

    # 4) 마스크된 위치에서만 교차 엔트로피 계산 (균일 가중치)
    if not is_masked.any():
        return torch.tensor(0.0, device=device, requires_grad=True)

    loss = F.cross_entropy(
        logits[is_masked],  # (N_masked, V)
        x0[is_masked],      # (N_masked,)
        reduction="mean",
    )
    return loss


def mdlm_generate(
    model,
    seq_len: int,
    num_steps: int = 50,
    mask_token_id: int = 103,
    device: str = "cuda",
) -> torch.Tensor:
    """
    MDLM 생성: 완전 마스크에서 시작해 점진적으로 언마스킹.
    q(x_{t-1} | x_t, x_0_hat) 후방 분포 사용.
    """
    x = torch.full((1, seq_len), mask_token_id, dtype=torch.long, device=device)
    timesteps = torch.linspace(1.0, 0.0, num_steps + 1, device=device)

    with torch.no_grad():
        for i in range(num_steps):
            t_curr = timesteps[i].unsqueeze(0)   # (1,)
            t_prev = timesteps[i + 1]

            # 현재 노이즈 수준에서 원본 분포 예측
            logits = model(x, t_curr)              # (1, L, V)
            x0_hat = logits.argmax(dim=-1)         # greedy 언마스킹

            # 후방: t-1에서도 마스크일 확률 계산
            alpha_curr = cosine_schedule(t_curr).item()
            alpha_prev = cosine_schedule(t_prev.unsqueeze(0)).item()
            prob_remain_masked = alpha_prev / alpha_curr if alpha_curr > 0 else 0.0

            # 마스크된 위치 중 일부를 확률적으로 복원
            currently_masked = (x.squeeze(0) == mask_token_id)  # (L,)
            do_unmask = currently_masked & (
                torch.rand(seq_len, device=device) > prob_remain_masked
            )
            x = x.squeeze(0)
            x[do_unmask] = x0_hat.squeeze(0)[do_unmask]
            x = x.unsqueeze(0)

    # 잔여 마스크 최종 처리
    remaining = (x == mask_token_id).squeeze(0)
    if remaining.any():
        t_final = torch.tensor([1e-5], device=device)
        x[0, remaining] = model(x, t_final).argmax(-1).squeeze(0)[remaining]

    return x.squeeze(0)
```

주요 구현 포인트는 다음과 같다. (1) `is_masked`를 통해 손실을 마스크 위치에만 집중시킨다. (2) 균일 가중치를 사용하므로 이론적 가중치 $\alpha'_t/(1-\alpha_t)$ 계산이 불필요하다. (3) 생성 시 후방 분포 $q(x_{t-1}|x_t, x_0)$의 닫힌 형태를 이용해 점진적으로 복원한다.

## 관련 문서

- [D3PM: Structured Denoising Diffusion Models in Discrete State-Spaces](https://arxiv.org/abs/2107.03006) -- MDLM의 전작이자 이론적 기반
- [SEDD: Discrete Diffusion Modeling by Estimating the Ratios of the Data Distribution](https://arxiv.org/abs/2310.16834) -- 같은 시기의 경쟁 방법으로 MDLM과 직접 비교
- [LLaDA: Large Language Diffusion with mAsking](https://arxiv.org/abs/2502.09992) -- MDLM 훈련 목표를 8B 규모로 확장한 후속 연구
- [Multinomial Diffusion](https://arxiv.org/abs/2102.05379) -- 균등 전이 기반 이산 확산의 초기 연구
- [BERT: Pre-training of Deep Bidirectional Transformers](https://arxiv.org/abs/1810.04805) -- 마스크 언어 모델의 원형으로 MDLM 순전파와 개념적 연결
