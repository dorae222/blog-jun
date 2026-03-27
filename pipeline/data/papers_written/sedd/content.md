## 개요

SEDD(Score Entropy Discrete Diffusion)는 Lou et al.이 ICML 2024에서 발표한 논문으로, 연속 공간에서 큰 성공을 거둔 확산 모델(diffusion model)의 핵심 원리를 이산(discrete) 공간으로 이전하는 문제를 다룬다. 텍스트는 본질적으로 이산적인 토큰 시퀀스이므로, 연속 확산 모델을 직접 적용하기 어렵다는 문제가 오랫동안 존재했다. SEDD는 스코어 함수(score function) 대신 **확률 비율(probability ratio)**을 학습 대상으로 삼는 스코어 엔트로피(score entropy) 손실을 제안하며, 이를 통해 GPT-2 수준의 언어 모델링 성능을 달성한 최초의 이산 확산 모델이다.

## 배경 및 문제

연속 확산 모델의 역방향 샘플링은 스코어 함수 $s(\mathbf{x}) = \nabla_{\mathbf{x}} \log p(\mathbf{x})$를 학습하는 데 의존한다. 그러나 이산 공간에서는 $\nabla$가 정의되지 않으므로 이 접근이 불가능하다. 기존 이산 확산 모델(D3PM 등)은 분포를 직접 예측하는 방식을 사용했지만, 연속 시간 프레임워크와의 연결성이 부족하고 샘플링 품질도 자기회귀 모델(AR)에 크게 뒤쳐졌다.

이산 확산의 순방향 과정은 **CTMC(Continuous-Time Markov Chain)**로 기술된다. 토큰 $x$의 시간 $t$에서의 확률 $p_t(x)$는 다음 마스터 방정식을 따른다:

$$\partial_t p_t(x) = \int \left[p_t(y)R_t(y \to x) - p_t(x)R_t(x \to y)\right] dy$$

여기서 $R_t(x \to y)$는 전이 속도 행렬(rate matrix)이다. 충분한 시간이 지나면 $p_t$는 다루기 쉬운 사전 분포(예: 균등 분포 또는 마스크 토큰 분포)에 수렴한다. 역방향 과정을 구동하기 위해서는 이 CTMC의 시간 역전(time reversal)이 필요하며, 이때 필요한 핵심 정보가 바로 확률 비율이다.

## 핵심 아이디어

### 콘크리트 스코어 (Concrete Score)

SEDD의 출발점은 이산 공간에서의 **콘크리트 스코어(concrete score)**를 정의하는 것이다:

$$s_t(x, y) := \frac{p_t(y)}{p_t(x)}$$

연속 공간의 스코어 $\nabla \log p(x)$가 로그 확률의 기울기인 데 비해, 콘크리트 스코어는 두 이산 상태 $x$와 $y$ 사이의 **확률 비율**이다. 이 비율을 알면 역방향 CTMC의 전이 속도를 계산할 수 있으며, 순방향 과정의 역전(reversal)이 가능해진다.

:::info
연속 공간에서 스코어 $\nabla \log p(x)$는 분포의 "기울기 방향"을 알려준다. 이산 공간에서는 미분이 불가능하므로, 대신 두 상태 간의 확률 비율로 "어느 상태가 더 가능성이 높은지"를 나타낸다. 이 비율이 역방향 CTMC의 전이 속도를 결정하는 핵심 정보가 된다.
:::

역방향 CTMC의 전이 속도는 콘크리트 스코어를 통해 다음과 같이 표현된다:

$$\bar{R}_t(x \to y) = R_t(y \to x) \cdot s_t(x, y) = R_t(y \to x) \cdot \frac{p_t(y)}{p_t(x)}$$

이 관계식은 연속 시간 역전(time reversal) 정리에서 직접 유도되며, 콘크리트 스코어를 정확히 알면 순방향 과정의 역전이 정확히 수행됨을 의미한다.

### 스코어 엔트로피 손실

문제는 $p_t(x)$를 직접 계산하기 어렵다는 점이다. SEDD는 이 비율을 신경망 $s_\theta(x_t, y)$로 추정하기 위해 **스코어 엔트로피(score entropy)** 손실을 제안한다:

$$\mathcal{L}_{SE} = \mathbb{E}_{t, x_t}\left[\sum_{y \neq x_t} \hat{R}_t(x_t, y)\left(s_t(x_t, y)\log\frac{s_t(x_t, y)}{s_\theta(x_t, y)} - s_t(x_t, y) + s_\theta(x_t, y)\right)\right]$$

괄호 안의 수식은 $u \log(u/v) - u + v$ 형태로, $u = v$일 때 최솟값 0을 가지는 **변형 KL 발산(modified KL divergence)**이다. 이를 통해 $s_\theta$가 실제 비율 $s_t$로 수렴하도록 유도된다. 중요한 점은 이 손실이 intractable한 $p_t(x)$ 자체를 명시적으로 알 필요 없이 최적화 가능하다는 것이다.

아래 그래프는 기존 Concrete Score Matching (CSM) 손실과 제안된 Score Entropy 손실의 형태를 비교한 것이다.

![Score Entropy와 Concrete Score Matching 손실 함수 비교](figures/fig_1.png)
*Figure 1: Score Entropy 손실(주황)은 CSM 손실(파랑)에 비해 음수 영역에서 발산하지 않고 완만하게 증가하며, 양수 영역에서도 기울기가 상대적으로 완만하여 학습이 안정적이다. 최솟값은 동일하게 $s_\theta = s_t$에서 달성된다. (Lou et al., 2024)*

### ELBO와의 관계

스코어 엔트로피 손실이 유효한 학습 목적 함수인 이유를 이해하려면 ELBO(Evidence Lower BOund)와의 관계를 살펴볼 필요가 있다. CTMC 기반 확산 모델의 ELBO는 다음과 같이 분해된다:

$$\log p_\theta(x_0) \geq \underbrace{\mathbb{E}_{q(x_T)} [\log p_\theta(x_T)]}_{\text{prior term}} - \underbrace{\int_0^T \mathbb{E}_{q(x_t)} \left[\sum_{y \neq x_t} R_t(x_t, y) \log \frac{s_t(x_t, y)}{s_\theta(x_t, y)}\right] dt}_{\text{denoising KL term}}$$

디노이징 KL 항은 실제 콘크리트 스코어 $s_t$와 모델 예측 $s_\theta$ 사이의 가중 KL 발산이다. 그러나 이 ELBO를 직접 최적화하면 $s_t(x_t, y)$를 정확히 계산해야 하는 문제가 있다.

SEDD의 핵심 기여는 이 ELBO의 디노이징 항을 **tractable한 형태로 변환**한 것이다. 구체적으로, 순방향 과정의 전이 확률 $q(x_t | x_0)$를 알고 있으므로:

$$s_t(x_t, y) = \frac{p_t(y)}{p_t(x_t)} = \frac{\sum_{x_0'} q(x_t = y | x_0') p(x_0')}{\sum_{x_0'} q(x_t | x_0') p(x_0')}$$

이 비율은 일반적으로 intractable하지만, **Absorbing 커널**의 경우 $x_t = \text{MASK}$일 때 비율이 해석적으로 계산 가능해진다:

$$s_t(\text{MASK}, y) = \frac{q(x_t = y | x_0 = y) \cdot p(x_0 = y)}{q(x_t = \text{MASK} | x_0 = y) \cdot p(x_0 = y)} = \frac{e^{-\sigma(t)}}{\sigma(t) \cdot (1 - e^{-\sigma(t)}) / \sigma(t)} $$

스코어 엔트로피 손실은 이 ELBO의 디노이징 항과 상수 차이만 있는 대리 손실(surrogate loss)이며, $s_\theta \to s_t$에서 동일한 최솟값을 가진다. 따라서 스코어 엔트로피를 최소화하면 ELBO를 최대화하는 것과 동치이다.

:::tip
스코어 엔트로피 손실의 핵심 장점은 기존 Concrete Score Matching(CSM) 손실과 달리 **비음수성(non-negativity)**을 보장한다는 점이다. CSM은 $s_\theta$가 음수 영역에 들어갈 때 손실이 발산하여 학습이 불안정해질 수 있지만, 스코어 엔트로피는 모든 영역에서 유한한 값을 가진다.
:::

## 방법론

**전이 커널의 선택.** SEDD는 두 가지 순방향 커널을 비교한다. *Absorbing SEDD*는 각 토큰을 독립적으로 특수 `[MASK]` 토큰으로 흡수시키는 방식으로, BERT의 마스킹과 유사하다. 전이 속도는 $R_t(x \to \text{MASK}) = \sigma(t)$로 단순하다. *Uniform SEDD*는 각 토큰이 어휘 전체에 균등하게 전이될 수 있도록 설정한다. Absorbing SEDD가 실험에서 일관되게 더 나은 성능을 보였으며, 이는 마스킹이 이산 데이터에 자연스럽게 적합한 구조임을 시사한다.

**스코어 매개변수화.** 신경망 $s_\theta(x_t, y)$는 $x_t$를 입력받아 각 가능한 상태 $y$에 대한 비율을 출력한다. Transformer 아키텍처를 사용하며, 출력 헤드를 어휘 크기로 확장하여 모든 $y$에 대한 비율을 한 번에 계산한다.

다음 그래프는 score parameterization과 mean parameterization의 학습 수렴 속도를 비교한 것으로, score parameterization의 우수성을 보여준다.

![Score Parameterization과 Mean Parameterization의 학습 손실 비교](figures/fig_5.png)
*Score parameterization(분홍)이 mean parameterization(하늘)에 비해 훈련 전반에 걸쳐 일관되게 낮은 평가 손실을 달성한다. 학습 후반부에서 약 700의 차이가 유지되며, 이는 확률 비율을 직접 출력하는 방식이 분포 평균을 예측하는 방식보다 표현력이 높음을 의미한다.*

**Tau-leaping 샘플러.** 역방향 샘플링에는 SDE 적분기 대신 **tau-leaping** 기법을 사용한다. 작은 시간 간격 $\tau$ 동안 전이 속도가 일정하다고 가정하고, 포아송 분포에서 전이 횟수를 샘플링한다. 이 방법은 각 토큰의 전이를 병렬로 처리할 수 있어 자기회귀 모델 대비 샘플링 효율이 높다.

## 실험 결과

SEDD는 text8(문자 수준)과 OpenWebText(토큰 수준) 벤치마크에서 평가되었다.

text8에서 SEDD-Absorb는 약 **33 BPD(bits per dimension)**를 달성하였으며, 이는 GPT-2의 약 32 BPD에 근접한 수준이다. 이전 최고 이산 확산 모델들이 40 BPD 이상이었음을 감안하면 커다란 도약이다. OpenWebText에서는 GPT-2(124M)와 동등한 퍼플렉시티 수준에 도달하였으며, 비슷한 파라미터 수 조건에서 이전 이산 확산 모델들을 크게 앞섰다.

다음 그래프는 SEDD-Absorbing 모델의 네트워크 평가 횟수에 따른 생성 퍼플렉시티를 GPT-2와 비교한 것이다.

![SEDD-Absorbing의 샘플링 반복 횟수에 따른 생성 퍼플렉시티](figures/fig_2.png)
*네트워크 평가 횟수가 증가할수록 SEDD-A의 생성 퍼플렉시티가 꾸준히 감소하며, 약 1000회 이상의 평가에서 GPT-2 Small/Medium과 동등하거나 더 낮은 퍼플렉시티를 달성한다. 이산 확산 모델이 자기회귀 모델에 필적하는 생성 품질을 보인 최초의 결과이다.*

모델 크기에 따른 SEDD의 스케일링 특성도 중요한 결과이다. 아래 그래프에서 SEDD-A Medium 모델은 충분한 샘플링 스텝에서 GPT-2 Small/Medium 수준을 뛰어넘는 퍼플렉시티를 달성하며, 모델 크기 증가에 따른 일관된 성능 개선을 보여준다.

![SEDD-A Small/Medium 모델의 네트워크 평가 횟수별 생성 퍼플렉시티](figures/fig_3.png)
*SEDD-A Small(파랑)과 Medium(주황) 모델의 생성 퍼플렉시티 -- 네트워크 평가 횟수가 증가할수록 퍼플렉시티가 지속적으로 감소하며, Medium 모델은 약 1000회 평가에서 GPT-2 Small/Medium(별 마커)보다 낮은 퍼플렉시티를 달성한다. (Lou et al., 2024)*

아래 그래프는 absorbing 커널에서 다양한 샘플러(analytic, euler)와 모델 크기(small, medium)에 따른 퍼플렉시티 변화를 종합적으로 보여준다.

![SEDD Absorbing의 샘플러별, 모델 크기별 생성 퍼플렉시티 비교](figures/fig_6.png)
*Analytic 샘플러(원형 마커)가 Euler 샘플러(삼각 마커)보다 전반적으로 낮은 퍼플렉시티를 달성한다. Medium 모델(주황)은 Small 모델(파랑)보다 일관되게 우수하며, 충분한 샘플링 스텝에서 GPT-2(별 마커) 대비 동등 이상의 성능을 보인다. Uniform 커널(점선)은 absorb 커널(실선)에 비해 성능이 떨어지는 것도 확인할 수 있다.*

### 기존 모델과의 정량적 비교

아래 표는 SEDD와 기존 이산 확산 모델들의 OpenWebText 퍼플렉시티를 종합 비교한 것이다:

| 모델 | 파라미터 수 | 유형 | OWT PPL | 비고 |
|------|------------|------|---------|------|
| D3PM (Uniform) | 124M | 이산 확산 | ~150+ | 균등 전이, 성능 제한 |
| D3PM (Absorb) | 124M | 이산 확산 | ~120+ | 흡수 커널 |
| MDLM | 124M | 마스크 확산 | ~74 | SEDD와 동시기 연구 |
| SEDD-Uniform Small | 124M | 스코어 엔트로피 | ~85 | 균등 커널 |
| SEDD-Absorb Small | 124M | 스코어 엔트로피 | ~78 | 흡수 커널 |
| SEDD-Absorb Medium | 350M | 스코어 엔트로피 | ~55 | 스케일 업 |
| GPT-2 Small | 124M | 자기회귀 | ~30 | 참고용 하한 |
| GPT-2 Medium | 350M | 자기회귀 | ~26 | 참고용 하한 |

SEDD-Absorb Medium은 350M 파라미터에서 GPT-2 Small(124M)의 퍼플렉시티에 근접하는 수준을 달성했으며, 이는 이산 확산 모델 계열에서 전례 없는 성과다.

### Analytic 샘플러의 효과

논문은 tau-leaping 외에도 CTMC의 전이 확률을 해석적으로 계산하는 **Analytic 샘플러**를 제안한다. Analytic 샘플러는 이산 시간 간격에서의 전이 확률을 행렬 지수(matrix exponential)로 정확히 계산하며, tau-leaping보다 적은 스텝에서 더 나은 생성 품질을 보인다. 위 Figure 4에서 원형 마커(Analytic)가 삼각 마커(Euler/tau-leaping)보다 일관되게 낮은 퍼플렉시티를 달성하는 것이 이를 확인시켜준다.

샘플링 측면에서도 tau-leaping 샘플러는 자기회귀 디코딩보다 병렬 처리가 가능하여, 특히 배치 생성 시나리오에서 처리량(throughput) 우위를 가진다.

Uniform 커널의 경우에도 유사한 경향이 관찰되지만, Absorbing 커널에 비해 전반적으로 높은 퍼플렉시티를 보인다. 아래 그래프는 이 차이를 명확히 보여준다.

![SEDD Uniform 커널의 샘플러별, 모델 크기별 생성 퍼플렉시티](figures/fig_7.png)
*SEDD Uniform 커널의 생성 퍼플렉시티 -- Absorbing 커널(Figure 4)과 동일한 설정에서 Uniform 커널은 전반적으로 더 높은 퍼플렉시티를 보인다. 이는 마스킹 기반 흡수 전이가 균등 전이보다 이산 텍스트 데이터에 더 적합한 구조임을 뒷받침한다. (Lou et al., 2024)*

## 의의 및 한계

**의의.** SEDD는 이산 확산 모델링을 자기회귀 모델과 경쟁 가능한 수준으로 끌어올린 첫 번째 연구다. 스코어 엔트로피라는 이론적으로 탄탄한 손실 함수를 도입함으로써 연속 확산 이론과 이산 확산을 통일적인 프레임워크로 연결했다. 또한 인필링(infilling), 조건부 생성 등 확산 모델 특유의 유연성을 텍스트에 적용할 수 있는 발판을 마련했다.

**한계.** SEDD의 한계는 다음과 같이 정리된다:

1. **AR과의 성능 격차**: SEDD는 여전히 잘 조정된 대형 자기회귀 모델(GPT-4 계열)에 비해 생성 품질이 떨어진다. 동일 파라미터(124M)에서 GPT-2 대비 약 2.5배 높은 퍼플렉시티를 보인다.

2. **샘플링 정밀도**: tau-leaping 샘플러는 이산성 때문에 연속 SDE 솔버만큼 정밀하지 않으며, 스텝 수가 충분하지 않으면 품질 저하가 발생한다. Analytic 샘플러가 이를 완화하지만 계산 비용이 더 높다.

3. **어휘 크기 확장성**: 어휘 크기가 클수록 비율 추정의 차원이 높아져 학습이 어려워지는 확장성 문제가 존재한다. GPT-2의 50,257 어휘에서도 각 토큰 위치마다 50,256개의 비율을 추정해야 한다.

4. **추론 비용**: 생성 품질을 GPT-2 수준으로 끌어올리려면 약 1000회 이상의 네트워크 평가가 필요하며, 이는 자기회귀 모델의 시퀀스 길이(보통 수백 토큰)보다 많은 계산을 요구한다.

5. **조건부 생성 제한**: 논문에서는 비조건부 언어 모델링에 집중하며, Seq2Seq이나 instruction-following 같은 조건부 설정에서의 성능은 별도 연구가 필요하다.

## 구현 고려사항

### 아키텍처 선택

SEDD는 GPT-2 아키텍처를 기반으로 하되 양방향 어텐션을 사용한다. 구체적 설정은 다음과 같다:

- **Small 모델**: 12 레이어, 768 hidden dim, 12 헤드 (124M 파라미터)
- **Medium 모델**: 24 레이어, 1024 hidden dim, 16 헤드 (350M 파라미터)
- **어텐션**: 양방향 (비인과적), 순수 확산 모델이므로 전체 시퀀스에 접근 가능
- **위치 인코딩**: 학습 가능한 절대 위치 임베딩 + RoPE 변형 실험

### Score 출력 구조

$s_\theta(x_t, y)$의 출력 구조에 대해 두 가지 매개변수화를 비교한다:

1. **Score Parameterization**: 비율 $p_t(y)/p_t(x_t)$를 직접 출력. softplus 활성화로 양수 보장.
2. **Mean Parameterization**: $x_0$의 분포를 예측하고 이로부터 비율을 간접 계산.

Figure 2에서 확인되듯이 Score Parameterization이 Mean Parameterization보다 약 65% 낮은 퍼플렉시티를 달성하며, 이는 비율을 직접 학습하는 것이 간접 예측보다 표현력이 높음을 보여준다.

### 노이즈 스케줄

Absorbing 커널의 전이 속도 $\sigma(t)$는 다음 로그-리니어 스케줄을 따른다:

$$\sigma(t) = -\log(1 - t(1 - e^{-\sigma_{\max}}))$$

$\sigma_{\max}$은 최종 시점에서의 최대 흡수 확률을 결정하며, 논문에서는 $\sigma_{\max} = 10$을 사용한다. 이 스케줄은 초기에는 느리게, 후반부에는 빠르게 마스킹이 진행되어 학습 안정성을 확보한다.

### 학습 설정

| 하이퍼파라미터 | 값 |
|---------------|-----|
| 옵티마이저 | AdamW ($\beta_1 = 0.9$, $\beta_2 = 0.999$) |
| 학습률 | $3 \times 10^{-4}$ |
| 웜업 스텝 | 2,500 |
| 배치 크기 | 512 |
| 시퀀스 길이 | 1024 |
| Weight Decay | 0.01 |
| 학습 토큰 수 | ~33B (Small), ~50B (Medium) |

:::warning
SEDD의 학습 비용은 GPT-2 학습과 유사한 수준이다. 그러나 추론 시 다수의 네트워크 평가가 필요하므로, 총 연산 비용은 AR 모델보다 높다. 생성 품질과 추론 비용 사이의 트레이드오프를 태스크 요구사항에 맞게 설정해야 한다.
:::

## 코드 예제

아래는 Absorbing SEDD의 순방향 가우시안 커널과 스코어 엔트로피 손실의 핵심 로직을 PyTorch 스타일의 의사 코드로 나타낸 것이다.

```python
import torch
import torch.nn.functional as F

def absorbing_forward(x0, t, mask_id):
    """시간 t에서 토큰을 독립적으로 MASK 토큰으로 흡수"""
    # sigma(t): 흡수 확률 스케줄 (예: 1 - exp(-t))
    sigma_t = 1.0 - torch.exp(-t)  # (B,)
    mask_prob = sigma_t[:, None].expand_as(x0)  # (B, L)
    # 베르누이 샘플링으로 마스킹 여부 결정
    masked = torch.bernoulli(mask_prob).bool()
    xt = x0.clone()
    xt[masked] = mask_id
    return xt

def score_entropy_loss(s_theta, s_true, R_hat):
    """
    score entropy loss 계산
    s_theta: 모델 예측 비율 (B, L, V)
    s_true : 실제 비율 p_t(y)/p_t(x) (B, L, V)
    R_hat  : 전이 속도 가중치 (B, L, V)
    """
    # u*log(u/v) - u + v, u=s_true, v=s_theta
    loss = s_true * (torch.log(s_true + 1e-8) - torch.log(s_theta + 1e-8))
    loss = loss - s_true + s_theta  # (B, L, V)
    loss = (R_hat * loss).sum(dim=-1)  # y != x 방향만 합산
    return loss.mean()
```

Absorbing 커널에서 $x_t$가 `[MASK]`인 경우 진짜 토큰 $y = x_0$에 대한 비율 $p_t(y)/p_t(x_t)$은 해석적으로 계산 가능하므로, `s_true`를 레이블로 직접 사용할 수 있다. 이 점이 학습을 안정적으로 만드는 핵심이다.

아래는 tau-leaping 샘플러를 이용한 역방향 샘플링의 의사 코드다:

```python
def tau_leaping_sample(
    model,
    seq_len: int,
    vocab_size: int,
    num_steps: int = 1000,
    mask_id: int = None,
) -> torch.Tensor:
    """
    SEDD Absorbing 커널의 tau-leaping 역방향 샘플링.
    모든 토큰을 MASK에서 시작하여 점진적으로 복원.
    """
    device = next(model.parameters()).device
    batch = 1
    mask_id = mask_id or (vocab_size - 1)

    # 초기 상태: 모든 토큰이 MASK
    x_t = torch.full((batch, seq_len), mask_id, device=device)

    dt = 1.0 / num_steps  # 시간 간격

    for step in range(num_steps):
        t = 1.0 - step * dt  # t: 1 → 0으로 감소

        # 모델로부터 콘크리트 스코어 예측
        # s_theta[i, j, v] = p_t(v) / p_t(x_t[i, j])
        s_theta = model(x_t, t)  # (batch, seq_len, vocab_size)

        # 역방향 전이 속도 계산
        # R_bar(x -> y) = R(y -> x) * s_theta(x, y)
        # Absorbing: R(y -> MASK) = sigma'(t), R(MASK -> y) = 0
        # 따라서 MASK -> y 전이만 발생
        is_masked = (x_t == mask_id)  # (batch, seq_len)

        if is_masked.any():
            # 마스크된 위치에서의 전이 확률 계산
            rates = s_theta[is_masked]  # (num_masked, vocab_size)
            rates[:, mask_id] = 0  # MASK -> MASK 전이 제거

            # 포아송 근사: 전이 수 = rate * dt
            probs = rates * dt
            probs = probs.clamp(max=1.0)  # 확률 상한

            # 가장 높은 확률의 토큰으로 전이 (greedy)
            # 또는 카테고리컬 샘플링 (stochastic)
            new_tokens = torch.distributions.Categorical(
                probs=probs + 1e-8
            ).sample()

            # 전이 여부 결정 (전체 전이 확률에 따라)
            total_rate = probs.sum(dim=-1)
            do_transition = torch.bernoulli(total_rate.clamp(max=1.0)).bool()

            # 전이 적용
            x_t_flat = x_t[is_masked]
            x_t_flat[do_transition] = new_tokens[do_transition]
            x_t[is_masked] = x_t_flat

    return x_t
```

:::info
tau-leaping의 핵심은 작은 시간 간격 $\Delta t$ 동안 전이 속도가 일정하다고 가정하는 것이다. 이 근사가 유효하려면 $\Delta t$가 충분히 작아야 하며, 스텝 수가 많을수록 생성 품질이 향상된다. Analytic 샘플러는 이 근사를 사용하지 않고 정확한 전이 확률을 계산하므로 적은 스텝에서도 더 나은 품질을 보인다.
:::

## 후속 연구와 영향

SEDD는 이산 확산 모델 연구에 큰 영향을 미쳤다. 주요 후속 연구와의 관계는 다음과 같다:

| 후속 모델 | SEDD와의 관계 | 개선점 |
|-----------|-------------|--------|
| MDLM | 동시기 독립 연구 | 마스크 예측 기반, 더 단순한 학습 목적 |
| BD3LM | SEDD/MDLM 기반 | 블록 단위 AR + 확산 하이브리드, KV-캐시 |
| LLaDA | 마스크 확산 확장 | 대규모 학습 (7B+) |
| DLLM | 잠재 공간 확산 | 이산 잠재 변수에서 확산 수행 |

SEDD가 제시한 콘크리트 스코어와 스코어 엔트로피의 이론적 프레임워크는, 이후 이산 확산 모델 연구의 공통 언어가 되었다.

## 관련 문서

- [D3PM: Structured Denoising Diffusion Models in Discrete State Spaces](https://arxiv.org/abs/2107.03006)
- [Score-Based Generative Modeling through SDEs](https://arxiv.org/abs/2011.13456)
- [MDLM: Masked Diffusion Language Model](https://arxiv.org/abs/2406.07524)
- [Continuous Diffusion for Categorical Data (CDCD)](https://arxiv.org/abs/2211.15089)