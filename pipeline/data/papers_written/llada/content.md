## 개요

LLaDA(Large Language Diffusion with mAsking)는 2025년 Nie et al.이 발표한 논문으로, **마스크 확산(masked diffusion) 방식을 언어 모델에 8B 파라미터 규모로 적용한 최초의 시도**다. 자기회귀(autoregressive, AR) 방식이 지배해 온 대규모 언어 모델 분야에서, 확산 기반 비자기회귀 모델이 동일한 스케일에서도 경쟁력 있는 성능을 낼 수 있음을 처음으로 실증했다.

모델은 표준 Transformer 구조에 $[\text{MASK}]$ 토큰 하나만 추가하여 설계 단순성을 유지하면서도, 2.3T 토큰 사전학습과 instruction fine-tuning을 통해 MT-Bench, GSM8K, HumanEval 등에서 LLaMA 3 8B와 비교 가능한 수준의 성능을 달성했다. 특히 추론 시 병렬 토큰 생성이 가능하여 AR 모델 대비 최대 3배 이상의 생성 속도 향상을 보여준다.

## 배경 및 문제

기존 대규모 언어 모델은 거의 모두 자기회귀(AR) 방식으로, 토큰을 왼쪽에서 오른쪽으로 하나씩 생성한다. 이 접근법은 강력하지만 근본적인 제약이 있다:

- **단방향 컨텍스트**: AR 모델은 앞 토큰에만 조건부로 다음 토큰을 예측하므로, 생성 과정에서 전체 시퀀스의 양방향 맥락을 동시에 고려하기 어렵다.
- **순차적 생성 비용**: 길이 $L$인 시퀀스를 생성하려면 정확히 $L$번의 순차적 forward pass가 필요하여, 긴 시퀀스일수록 지연 시간이 선형으로 증가한다.

반면 이미지 도메인에서는 확산 모델(DDPM, Stable Diffusion 등)이 생성 모델의 주류로 자리잡았다. 언어에도 확산을 적용하려는 시도가 있었지만, 연속 공간 확산을 이산적 텍스트에 적용하는 것은 본질적으로 어색하고, 기존 연구들은 소규모 실험에 머물러 있었다. LLaDA는 **이산 마스크 확산(discrete masked diffusion)**을 채택하여 언어의 이산적 특성과 확산 프레임워크를 자연스럽게 결합하고, 이를 처음으로 8B 스케일로 확장했다.

### BERT와의 차이

BERT도 마스크 언어 모델링(MLM)을 사용하지만, LLaDA와는 근본적으로 다른 목적과 구조를 가진다:

| | BERT | LLaDA |
|---|---|---|
| 마스킹 비율 | 고정 15% | $t \sim U[0,1]$ (시간에 따라 연속 변화) |
| 학습 목표 | 마스크 복원 (인코더 사전학습) | 확산 ELBO (생성 모델 학습) |
| 추론 방식 | 단일 패스 복원 | 반복적 디노이징 ($t=1 \to 0$) |
| 용도 | 분류/이해 태스크 | 텍스트 생성 |

## 핵심 아이디어

LLaDA의 핵심은 **시간 연속 마스크 확산(continuous-time masked diffusion)**이다. 아이디어는 직관적이다: 학습 시에는 토큰을 점진적으로 마스킹하는 전진 과정(forward process)을 정의하고, 모델은 마스킹된 토큰을 복원하는 역과정(reverse process)을 학습한다. 추론 시에는 완전히 마스킹된 시퀀스 $x_1 = [\text{MASK}]^L$에서 시작해 반복적으로 마스크를 해제하며 텍스트를 생성한다.

다음 그림은 LLaDA의 전체 파이프라인을 보여준다. 사전학습, SFT, 샘플링의 세 단계가 모두 마스크 확산이라는 하나의 프레임워크 위에서 동작한다.

![LLaDA의 사전학습, SFT, 샘플링 과정 개요](figures/fig_2.png)
*LLaDA의 개념적 개요. (a) 사전학습: 모든 토큰에 동일한 비율 $t \sim U[0,1]$로 독립적 마스킹 적용. (b) SFT: 응답 토큰만 마스킹 대상. (c) 샘플링: $t=1$(완전 마스킹)에서 $t=0$(언마스킹)으로 확산 과정을 시뮬레이션하며, 각 스텝에서 모든 마스크를 동시에 예측한다.*

특히 각 스텝에서 **병렬로 여러 토큰을 동시에 복원**할 수 있어, AR 모델의 $L$번 순차 호출 대비 훨씬 적은 forward pass로 생성이 가능하다. 예를 들어, 256 토큰 시퀀스를 25 스텝만에 생성할 수 있다.

## 방법론

### 전진 과정 (Forward Masking Process)

시간 $t \in [0, 1]$에서 각 토큰 $x_0^i$에 독립적으로 마스킹을 적용한다. 전체 시퀀스에 대한 전진 분포는 각 토큰의 분포의 곱으로 인수분해된다:

$$q(x_t|x_0) = \prod_i q(x_t^i|x_0^i)$$

각 토큰의 마스킹 분포는 선형 스케줄을 따른다:

$$q(x_t^i|x_0^i) = (1-t)\delta_{x_0^i} + t\delta_{[\text{MASK}]}$$

$t=0$이면 원본 토큰이 그대로 유지되고($x_0^i$), $t=1$이면 모든 토큰이 $[\text{MASK}]$로 대체된다. 마스킹은 토큰 간 독립적으로 수행되므로, 시간 $t$에서 각 토큰은 확률 $t$로 마스킹되어 부분적으로 마스킹된 중간 상태 $x_t$를 자연스럽게 표현한다.

### 역과정 (Denoising Model)

모델 $p_\theta$는 마스킹된 시퀀스 $x_t$를 받아 원본 토큰을 예측한다. 핵심 설계 원리는 **마스킹된 위치만 예측 대상**으로 삼는 것이다:

$$p_\theta(x_0|x_t) = \prod_{i:\, x_t^i=[\text{MASK}]} p_\theta(x_0^i|x_t)$$

이미 관측된 토큰($x_t^i \neq [\text{MASK}]$)은 그대로 유지된다. 이 설계는 표준 Transformer의 **양방향 어텐션(bidirectional attention)**과 자연스럽게 결합된다. 마스킹되지 않은 토큰들이 양쪽 방향에서 문맥 정보를 제공하고, 모델은 이를 활용해 마스킹 위치를 복원한다. 이는 AR 모델의 causal(단방향) 어텐션과 대비되는 LLaDA의 구조적 장점이다.

### 학습 목표 (Masked Diffusion ELBO)

마스크 확산의 evidence lower bound(ELBO)를 전개하면 다음의 단순한 형태로 수렴한다:

$$\mathcal{L} = \mathbb{E}_{t,x_0,x_t}\left[\frac{1}{t}\sum_{i:\, x_t^i=[\text{MASK}]} \log p_\theta(x_0^i|x_t)\right]$$

여기서 $1/t$ 가중치는 $t$가 작을수록(마스킹이 적을수록) 손실에 더 높은 가중치를 부여한다. 직관적으로, $t$가 작다는 것은 대부분의 토큰이 이미 드러나 있고 소수의 마스크만 남은 상태를 의미한다. 이 상황에서의 예측은 맥락이 거의 완전한 상태에서 정확한 단어를 맞춰야 하는 어려운 과제이므로, 높은 가중치를 부여하는 것이 타당하다.

실제 구현에서는 수치 안정성을 위해 $t \sim U[\epsilon, 1]$($\epsilon = 10^{-3}$)로 샘플링하고, 마스크된 토큰들의 평균 교차 엔트로피를 계산한다.

### 추론 절차

추론은 $x_1 = [\text{MASK}]^L$에서 시작해 시간을 $t=1 \to 0$ 방향으로 역행한다. 총 $T$개의 스텝으로 시간을 $1 = t_0 > t_1 > \cdots > t_T = 0$으로 분할한 뒤, 각 스텝에서 다음을 수행한다:

1. $p_\theta(x_0|x_t)$를 통해 모든 마스크 위치의 토큰을 동시에 예측
2. 예측 **신뢰도(confidence)**가 높은 위치부터 순서대로 마스크를 해제
3. 나머지 위치는 다시 마스킹(remasking)하여 다음 스텝으로 전달

스텝 수 $T$를 조절하면 생성 품질과 속도 사이의 트레이드오프를 유연하게 설정할 수 있다. 일반적으로 $T = 25 \sim 100$ 범위에서 좋은 결과를 얻는다.

다음 그림은 LLaDA가 수학 문제를 풀 때 토큰이 어떤 순서로 생성되는지를 시각화한 것이다. 색이 밝을수록 초기 스텝에서, 어두울수록 후기 스텝에서 예측된 토큰이다.

![LLaDA의 수학 문제 풀이 샘플링 과정 시각화](figures/fig_4.png)
*마스크 확산 샘플링 과정의 시각화. 밝은 색의 토큰은 초기 단계에서, 어두운 색의 토큰은 후반 단계에서 예측된다. AR 모델과 달리 순서에 구애받지 않고 확신이 높은 토큰부터 병렬적으로 생성되는 것을 확인할 수 있다.*

이 시각화에서 주목할 점은, 확산 모델이 반드시 왼쪽에서 오른쪽으로 생성하는 것이 아니라 **전체 문맥에서 확신이 높은 토큰부터 우선 결정**한다는 것이다. 이는 AR 모델에서는 불가능한, 확산 기반 접근법의 고유한 특성이다.

### Semi-Autoregressive 생성

매우 긴 시퀀스의 경우, 전체를 한번에 확산으로 생성하면 품질이 저하될 수 있다. LLaDA는 이를 해결하기 위해 **Semi-AR(반자기회귀)** 방식을 도입한다.

![Semi-Autoregressive 샘플링 개요](figures/fig_5.png)
*Semi-AR 샘플링의 개념도. 응답을 여러 블록으로 나눈 뒤, 각 블록 내부는 마스크 확산으로 병렬 생성하되, 블록 간에는 왼쪽에서 오른쪽으로 순차 진행한다. 이전 블록의 결과가 다음 블록의 조건으로 사용된다.*

각 블록(chunk) 내부는 병렬 확산으로 생성하되, 블록 간에는 왼쪽에서 오른쪽으로 진행하여 전체적인 일관성을 유지한다. 이 방식은 확산의 병렬성과 AR의 순차적 일관성을 결합한 하이브리드 전략이다.

### 아키텍처 및 학습 설정

아키텍처는 LLaMA와 동일한 표준 Transformer를 사용하며, 변경점은 최소화했다:

- $[\text{MASK}]$ 토큰을 어휘에 추가
- 단방향 causal attention 대신 **양방향 full attention** 사용
- 그 외 RMSNorm, SwiGLU, RoPE 등은 동일

8B 파라미터 모델을 2.3T 토큰으로 사전학습 후, instruction following을 위한 SFT를 수행했다. SFT 시에는 사용자 입력(prompt)은 조건으로 유지하고, 어시스턴트 응답 부분만 마스킹 및 복원 대상으로 설정한다. 이는 위의 Figure 2 (b)에 해당하는 과정이다.

## 실험 결과

### 사전학습 모델 성능

상식 추론 벤치마크에서 LLaDA 8B Base는 동급 AR 모델과 거의 동등한 성능을 달성했다.

| 모델 | 방식 | HellaSwag | PIQA | ARC-E | ARC-C | Avg |
|------|------|-----------|------|-------|-------|-----|
| LLaMA 3 8B | AR | 82.1 | 80.9 | 80.9 | 53.5 | 74.4 |
| Mistral 7B | AR | 81.3 | 82.2 | 80.0 | 52.2 | 73.9 |
| LLaDA 8B | 마스크 확산 | 80.5 | 82.8 | 81.2 | 53.8 | 74.6 |

평균 기준으로 LLaDA 8B가 74.6으로 LLaMA 3 8B(74.4), Mistral 7B(73.9)을 오히려 소폭 상회하는 결과를 보였다. 이는 마스크 확산이 사전학습 단계에서 AR 모델과 동등한 언어 이해 능력을 학습할 수 있음을 시사한다.

다음 레이더 차트는 더 넓은 범위의 벤치마크에서 LLaDA와 AR 모델들의 성능을 비교한 것이다.

![LLaDA 8B와 LLaMA 모델들의 벤치마크 성능 비교](figures/fig_1.png)
*다양한 zero/few-shot 벤치마크에서의 성능 비교. LLaDA 8B Base(빨간색)가 LLaMA 3 8B Base(보라색), LLaMA 2 7B Base(파란색)와 대부분의 태스크에서 경쟁적인 성능을 보인다. 특히 일반 태스크(MMLU, ARC-C)와 중국어 벤치마크(C-Eval, CMMLU)에서 강세를 보이며, 코드(HumanEval, MBPP)와 수학(Math, GSM8K)에서는 상대적으로 격차가 있다.*

### Instruction 모델 성능

Instruction 모델(SFT 적용)에서는 LLaMA 3 8B Instruct 대비 MT-Bench와 코드 생성(HumanEval)에서 격차가 존재하지만, GSM8K 수학 추론에서는 70% 이상의 경쟁력 있는 수치를 보였다.

### 스케일링 법칙

스케일링 분석에서 마스크 확산도 AR 모델과 유사한 스케일링 법칙(scaling law)을 따름을 확인했다. 모델 크기와 데이터 양이 증가함에 따라 성능이 예측 가능한 멱법칙(power law)으로 향상된다는 것은, 마스크 확산 LM이 AR 모델처럼 대규모 확장이 가능한 패러다임임을 의미한다.

### 추론 효율

추론 효율 측면에서, 25 스텝으로 AR 모델과 유사한 품질을 달성하면서 **3배 이상 빠른 생성 속도**를 보였다. 이는 각 스텝에서 여러 토큰을 동시에 예측하기 때문이며, 스텝 수를 줄이면 품질이 다소 감소하지만 생성 속도는 더욱 빨라져 속도-품질 트레이드오프의 유연한 조절이 가능하다.

아래 그래프들은 샘플링 스텝 수(NFEs, Number of Function Evaluations)에 따른 성능 변화를 보여준다. 두 벤치마크 모두에서 NFE가 증가할수록 성능이 향상되며, 특히 256 이상에서 큰 폭의 개선이 나타난다.

![샘플링 스텝 수에 따른 GSM8K 성능 변화](figures/fig_6_1.png)
*샘플링 스텝(NFEs)에 따른 GSM8K 0-shot 정확도 -- 64 스텝에서는 약 5% 수준이지만, 256 스텝에서 40% 이상, 1024 스텝에서 약 65%까지 급격하게 향상된다. 수학 추론 태스크에서는 충분한 디노이징 스텝이 핵심적으로 중요함을 보여준다. (Nie et al., 2025)*

![샘플링 스텝 수에 따른 HumanEval 성능 변화](figures/fig_6_2.png)
*샘플링 스텝(NFEs)에 따른 HumanEval 0-shot 정확도 -- GSM8K와 유사한 경향으로, 코드 생성 역시 스텝 수 증가에 따라 성능이 지속적으로 개선된다. 512 스텝 이상에서 약 30%의 정확도에 도달하며, 스텝 수-품질 트레이드오프의 실용적 지침을 제공한다. (Nie et al., 2025)*

## 의의 및 한계

### 의의

LLaDA는 마스크 확산 언어 모델이 대규모 스케일에서도 AR 모델과 경쟁할 수 있음을 처음으로 보인 이정표적 연구다. 구체적인 기여는 다음과 같다:

- **패러다임 다양성**: AR이 유일한 선택지가 아님을 8B 스케일에서 증명. 언어 모델 설계의 탐색 공간을 확장했다.
- **양방향 컨텍스트 활용**: 생성 시 양방향 맥락을 동시에 고려할 수 있어, 전체 문맥의 일관성 측면에서 잠재적 이점이 있다. 아래 시각화는 LLaDA가 다중 턴 대화에서 확산 기반으로 자연스러운 응답을 생성하는 과정을 보여준다.

![LLaDA의 다중 턴 대화 생성 과정 시각화](figures/fig_8_1.jpg)
*다중 턴 대화에서의 LLaDA 샘플링 시각화 -- 어두운 색의 토큰은 후반 단계에서, 밝은 색의 토큰은 초기 단계에서 예측된다. Random remasking 전략을 사용하며, AR 모델과 달리 문맥적으로 중요한 토큰(키워드, 구조어)이 먼저 결정되는 패턴이 관찰된다. (Nie et al., 2025)*
- **속도-품질 트레이드오프**: 생성 스텝 수를 조절하여 상황에 맞게 속도와 품질의 균형을 유연하게 설정 가능하다.
- **후속 연구 촉발**: LLaDA 이후 dLLM, BD3-LM, MDLM 등 후속 연구들이 이어지며 확산 LM 분야가 빠르게 발전하고 있다.

### 한계

- **코드/추론 태스크**: MT-Bench와 HumanEval에서 AR 모델 대비 성능 격차가 여전히 존재한다. 특히 정확한 구문이 중요한 코드 생성에서 약세를 보인다.
- **Chain-of-Thought**: 단계적 추론이 필요한 태스크에서 상대적으로 낮은 성능을 보인다. 이는 확산 모델이 순차적 논리 전개에 불리할 수 있음을 시사한다.
- **정렬(Alignment) 미성숙**: RLHF, DPO 등 AR 모델에서 발전한 정렬 방법론을 확산 LM에 적용하는 연구가 아직 초기 단계에 있다.
- **추론 비용**: 스텝 수를 늘려야 고품질 생성이 가능하며, 최적의 스텝 수를 결정하는 것이 추가적인 하이퍼파라미터가 된다.

## 코드 예제

아래는 LLaDA의 마스크 확산 학습 손실과 추론을 PyTorch로 구현한 핵심 예시다.

```python
import torch
import torch.nn.functional as F

MASK_TOKEN_ID = 32000


def masked_diffusion_loss(model, x0, attention_mask=None):
    """
    LLaDA 학습 손실: masked diffusion ELBO.
    x0: (B, L) 원본 토큰 시퀀스
    """
    B, L = x0.shape
    device = x0.device

    # 시간 균등 샘플링 t ~ U[eps, 1]
    t = torch.rand(B, device=device) * (1 - 1e-3) + 1e-3

    # 전진 과정: 선형 스케줄로 독립적 마스킹
    # q(x_t^i | x_0^i) = (1-t) * delta_{x_0^i} + t * delta_{[MASK]}
    mask_prob = t[:, None].expand(B, L)
    is_masked = torch.bernoulli(mask_prob).bool()
    if attention_mask is not None:
        is_masked = is_masked & attention_mask.bool()

    x_t = x0.clone()
    x_t[is_masked] = MASK_TOKEN_ID

    # 디노이징 모델 예측: p_theta(x_0^i | x_t)
    logits = model(x_t, t)  # (B, L, V)

    # 마스크된 위치에서만 교차 엔트로피 계산 (1/t 가중치는 평균으로 근사)
    if not is_masked.any():
        return torch.tensor(0.0, device=device, requires_grad=True)

    loss = F.cross_entropy(
        logits[is_masked],   # (N_masked, V)
        x0[is_masked],       # (N_masked,)
        reduction="mean",
    )
    return loss


@torch.no_grad()
def llada_generate(model, prompt_ids, max_new_tokens=128, num_steps=25, temperature=1.0):
    """
    LLaDA 추론: x_1 = [MASK]^L 에서 시작해 반복적으로 언마스킹.
    신뢰도 기반으로 확신이 높은 토큰부터 복원한다.
    """
    device = prompt_ids.device
    prompt_len = prompt_ids.shape[1]

    # 응답 부분을 [MASK]로 초기화
    x = torch.cat([
        prompt_ids,
        torch.full((1, max_new_tokens), MASK_TOKEN_ID, device=device, dtype=torch.long),
    ], dim=1)

    response_mask = torch.zeros(1, x.shape[1], dtype=torch.bool, device=device)
    response_mask[0, prompt_len:] = True

    timesteps = torch.linspace(1.0, 0.0, num_steps + 1, device=device)

    for step in range(num_steps):
        t_curr = timesteps[step]
        t_next = timesteps[step + 1]

        currently_masked = (x == MASK_TOKEN_ID) & response_mask
        if not currently_masked.any():
            break

        # p_theta(x_0 | x_t) 계산
        t_tensor = t_curr.unsqueeze(0)
        logits = model(x, t_tensor)                        # (1, L, V)
        probs = F.softmax(logits / temperature, dim=-1)
        pred_tokens = probs.argmax(dim=-1)                 # 그리디 디코딩
        confidence = probs.max(dim=-1).values              # (1, L)

        # 이번 스텝에서 언마스킹할 비율 결정
        n_masked = currently_masked.sum().item()
        frac = (t_curr - t_next) / t_curr if t_curr > 0 else 1.0
        n_to_unmask = max(1, int(n_masked * frac.item()))

        # 신뢰도 상위 n_to_unmask개 위치 언마스킹
        masked_conf = confidence[currently_masked]
        threshold = masked_conf.sort().values[max(0, len(masked_conf) - n_to_unmask)]
        should_unmask = currently_masked & (confidence >= threshold)
        x = torch.where(should_unmask, pred_tokens, x)

    return x[0, prompt_len:]  # 응답 토큰만 반환
```

## 관련 문서

- [MDLM: Simple and Effective Masked Diffusion Language Models](https://arxiv.org/abs/2406.07524) ( LLaDA의 직접적 이론적 선행 연구
- [D3PM: Structured Denoising Diffusion Models in Discrete State-Spaces](https://arxiv.org/abs/2107.03006) ) 이산 확산의 수학적 토대
- [BERT: Pre-training of Deep Bidirectional Transformers](https://arxiv.org/abs/1810.04805) ( 마스크 언어 모델링의 원점
- [LLaMA 3](https://arxiv.org/abs/2407.21783) ) 주요 비교 베이스라인 AR 모델
