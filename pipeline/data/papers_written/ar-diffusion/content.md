## 개요

AR-Diffusion(Wu et al., NeurIPS 2023)은 자기회귀(AR) 언어 모델과 확산(Diffusion) 모델을 단일 프레임워크로 통합한 텍스트 생성 모델이다. 핵심 아이디어는 시퀀스 내 각 토큰 위치 $i$에 서로 다른 노이즈 타임스텝을 할당하는 **계단식(staircase) 노이즈 스케줄**을 도입하는 것이다. 앞쪽 토큰은 노이즈가 적어 빠르게 확정되고, 뒤쪽 토큰은 노이즈가 많아 나중에 결정되므로 명시적인 인과 마스킹 없이도 자기회귀적 생성 순서가 노이즈 구조 안에 자연스럽게 내재된다. 이를 통해 AR 모델의 순서 일관성과 Diffusion 모델의 양방향 문맥 활용 및 생성 다양성을 동시에 확보한다.

---

## 배경 및 문제

텍스트 생성에서 지배적인 패러다임은 GPT 계열로 대표되는 자기회귀 모델이다. 이 모델은 왼쪽에서 오른쪽으로 토큰을 하나씩 생성하며 강력한 순서 일관성을 보장하지만, 생성 다양성이 제한되고 병렬 생성이 어렵다는 구조적 한계를 갖는다.

반면, 이미지 생성에서 큰 성공을 거둔 확산 모델을 텍스트에 적용하려는 시도들(Diffusion-LM, MDLM 등)이 있었다. 이들은 전체 시퀀스를 동시에 점진적으로 복원하여 다양성과 전역 일관성을 확보하지만, AR 모델 대비 생성 품질이 낮고 순서 의존성을 명시적으로 모델링하지 못하는 문제가 있었다.

두 방식의 근본적인 차이를 정리하면 다음과 같다.

- **AR 모델**: 토큰별 순차 생성, 인과 마스킹으로 순서 강제, 높은 품질이나 다양성 부족
- **Diffusion 모델**: 전체 시퀀스 병렬 복원, 다양성 우수, 순서 의존성 약함

AR-Diffusion은 이 두 패러다임의 한계를 동시에 극복하는 것을 목표로 한다.

---

## 핵심 아이디어

아래 그림은 AR-Diffusion의 핵심 개념을 직관적으로 보여준다. 가로축은 시퀀스 내 토큰 위치, 세로축은 확산 타임스텝을 나타내며, 세 가지 접근법의 디노이징 경로를 비교한다.

![AR-Diffusion의 핵심 개념 비교: Diffusion-LM, AR, AR-Diffusion의 디노이징 경로](figures/fig_1.png)
*Figure 1. (a) Diffusion-LM은 모든 토큰이 동일한 속도로 디노이징된다. (b) AR 모델은 확산 관점에서 토큰이 $t=T$(미결정)와 $t=0$(확정)의 두 상태만 갖는다. (c) AR-Diffusion은 앵커 포인트 $(n_e, t_e)$를 기준으로 위치별 디노이징 속도가 다르며, 앞쪽 토큰이 더 빠르게 수렴한다.*

AR-Diffusion의 핵심은 **위치 의존적 노이즈 타임스텝(position-dependent noise timestep)** 이다. 길이 $L$의 시퀀스에서 위치 $i$에 해당하는 토큰의 노이즈 레벨 $t_i$를 다음과 같이 정의한다.

$$t_i = T \cdot \frac{i}{L}$$

여기서 $T$는 전체 확산 스텝 수다. 이 수식이 의미하는 바는 직관적이다. 시퀀스 앞부분 토큰($i$가 작음)은 노이즈가 적어 거의 원본에 가깝고, 뒷부분 토큰($i$가 클수록)은 더 많은 노이즈가 더해져 불확실성이 높다. 결과적으로 노이즈 레벨 자체가 계단 모양(staircase)을 형성하며, 이것이 AR의 왼쪽에서 오른쪽으로의 생성 순서를 암묵적으로 인코딩한다.

그림 1의 (c)에서 보듯이, AR-Diffusion은 Diffusion-LM의 균일한 디노이징(a)과 AR의 이진적 상태 전환(b) 사이의 연속적 스펙트럼을 제공한다. 앵커 포인트 $(n_e, t_e)$의 위치에 따라 AR에 가까운 동작부터 Diffusion에 가까운 동작까지 유연하게 조절할 수 있다.

---

## 방법론

### 순방향 과정 (Forward Process)

각 토큰 $x_0^i$에 대해 독립적으로 Gaussian 노이즈를 추가하되, 타임스텝은 위치마다 다르다.

$$q(x_{t_i}^i \mid x_0^i) = \mathcal{N}\!\left(\sqrt{\bar{\alpha}_{t_i}}\, x_0^i,\ (1 - \bar{\alpha}_{t_i})\, \mathbf{I}\right)$$

$\bar{\alpha}_{t_i} = \prod_{s=1}^{t_i}(1 - \beta_s)$는 표준 DDPM 노이즈 스케줄의 누적 곱이다. 위치 $i$가 클수록 $t_i$가 커지고 $\bar{\alpha}_{t_i}$가 작아져 신호 성분이 줄고 노이즈가 지배적이 된다. 즉, 앞쪽 토큰은 원본에 가깝고 뒤쪽 토큰은 거의 순수한 Gaussian 노이즈 상태가 된다.

### 역방향 과정 (Reverse / Denoising)

역방향 과정에서 각 토큰의 복원은 전체 시퀀스 문맥을 양방향으로 활용한다. 위치 $i$의 복원 분포는 다음과 같다.

$$p_\theta(x_{t_i - 1}^i \mid x_t^{1:L}) = \mathcal{N}\!\left(\mu_\theta^i(x_t, t_i),\ \sigma_{t_i}^2 \mathbf{I}\right)$$

여기서 $\mu_\theta^i$는 네트워크가 예측하는 평균이며, 입력으로 전체 시퀀스 $x_t^{1:L}$을 받는다는 점이 핵심이다. 앞쪽 토큰은 낮은 $t_i$ 덕분에 이미 거의 복원된 상태이므로, 뒤쪽 토큰의 생성 시 신뢰할 수 있는 문맥을 자연스럽게 제공한다. 이는 별도의 인과 마스크 없이도 AR적 조건부 의존성을 실현하는 메커니즘이다.

### 동적 디노이징 스텝 (Dynamic Denoising Steps)

AR-Diffusion의 실용적으로 중요한 기여 중 하나는 **위치별 디노이징 스텝 수를 동적으로 조절**하는 것이다. 앞쪽 토큰은 낮은 타임스텝에서 시작하므로 적은 스텝으로 빠르게 수렴하고, 뒤쪽 토큰은 높은 타임스텝에서 시작하므로 더 많은 스텝이 필요하다. 구체적으로, 위치 $i$의 토큰에 필요한 디노이징 스텝 수는 다음과 같다.

$$S_i = \left\lceil S \cdot \frac{t_i}{T} \right\rceil$$

여기서 $S$는 전체 샘플링 스텝 수다. 이 설계는 계산 자원을 효율적으로 배분하여, 이미 확정된 앞쪽 토큰에 불필요한 계산을 낭비하지 않는다.

### 학습 목표 (Training Loss)

전체 학습 손실은 각 위치의 노이즈 예측 오차 합산이다.

$$\mathcal{L} = \sum_{i=1}^{L} \mathbb{E}_{t_i}\!\left[\left\|\epsilon_i - \epsilon_\theta^i(x_t^{1:L}, t_i)\right\|^2\right]$$

$\epsilon_\theta^i$는 위치 $i$에서 추가된 노이즈 $\epsilon_i$를 예측하는 네트워크 출력이다. 각 위치가 서로 다른 $t_i$로 조건화되기 때문에, 모델은 동일한 파라미터로 다양한 노이즈 레벨에서 동시에 작동하는 능력을 학습한다. 이는 표준 DDPM의 학습 목표를 위치별로 확장한 것으로 볼 수 있다.

### 샘플링과 가속

추론 시에는 전체 시퀀스 $x_T^{1:L}$을 계단식 노이즈 레벨로 초기화한 뒤, 점진적 복원을 수행한다. AR-Diffusion은 두 가지 샘플링 가속 전략을 지원한다.

1. **스텝 스킵(Step Skipping)**: DDPM의 전체 $T$ 스텝 중 균등 간격으로 $S$개만 선택하여 건너뛰기
2. **DDIM 적용**: 결정론적 샘플링으로 더 적은 스텝에서도 높은 품질 유지

특히 AR-Diffusion에서는 앞쪽 위치 토큰이 적은 스텝으로 빠르게 수렴하므로, 전체 샘플링 효율이 표준 확산 모델보다 유리하다.

---

## 실험 결과

AR-Diffusion은 기계 번역, 텍스트 요약, 무조건 생성 등 다양한 벤치마크에서 기존 확산 기반 텍스트 생성 모델을 일관되게 능가하는 성능을 보인다.

### 기계 번역 (Machine Translation)

IWSLT14 De$\to$En 기계 번역에서 AR-Diffusion은 기존 비자기회귀(NAR) 및 확산 기반 모델들을 크게 능가한다.

| 모델 | 유형 | SacreBLEU ↑ |
|---|---|---|
| Diffusion-LM | Diffusion | 17.0 |
| DiffuSeq | Diffusion | 22.4 |
| SeqDiffuSeq | Diffusion | 24.0 |
| GENIE | Diffusion | 30.2 |
| **AR-Diffusion** | **AR + Diffusion** | **32.3** |
| Transformer (AT) | Autoregressive | 35.2 |

AR-Diffusion은 가장 강력한 확산 기반 경쟁 모델인 GENIE 대비 2.1 BLEU 향상을 달성했으며, 자기회귀 Transformer와의 격차도 상당히 좁혔다.

### 텍스트 요약 (Summarization)

XSum 데이터셋에서의 요약 성능도 주목할 만하다.

| 모델 | ROUGE-1 ↑ | ROUGE-2 ↑ | ROUGE-L ↑ |
|---|---|---|---|
| DiffuSeq | 17.6 | 1.5 | 13.3 |
| GENIE | 28.9 | 8.2 | 22.1 |
| **AR-Diffusion** | **30.2** | **9.5** | **23.4** |

모든 ROUGE 지표에서 GENIE를 1-2점 상회하며, 특히 ROUGE-2(바이그램 정밀도)의 개선이 두드러져 생성 텍스트의 구체성이 향상되었음을 보여준다.

### 샘플링 가속 비교

아래 그림은 XSum 테스트셋에서 추론 스텝 수에 따른 AVG-ROUGE 성능 변화를 보여준다.

![XSum 데이터셋에서 추론 스텝 수에 따른 AR-Diffusion과 GENIE의 성능 비교](figures/fig_2_1.png)
*Figure 2. 추론 스텝 수에 따른 AVG-ROUGE 비교 (step skipping 방식). AR-Diffusion은 적은 스텝에서도 GENIE보다 높은 성능을 유지하며, 약 50 스텝부터 성능이 수렴한다.*

AR-Diffusion은 스텝 스킵 방식에서 모든 추론 스텝 수 구간에서 GENIE를 상회한다. 특히 10~50 스텝의 소수 추론 스텝 영역에서도 안정적인 성능을 보여, 실용적인 추론 가속이 가능함을 입증한다.

DDIM 가속을 적용한 경우에도 AR-Diffusion의 우위는 유지된다.

![DDIM 가속 적용 시 AR-Diffusion과 GENIE의 추론 스텝별 AVG-ROUGE 비교](figures/fig_2_2.png)
*Figure 5: DDIM 가속 방식에서의 추론 스텝 수 대비 AVG-ROUGE 비교. AR-Diffusion은 DDIM 적용 시에도 GENIE 대비 일관된 성능 우위를 보이며, 스텝 스킵 대비 더 빠르게 수렴한다. (Wu et al., 2023)*

아래 그림은 GENIE 모델의 스텝 스킵 및 DDIM 가속 결과를 보여주며, AR-Diffusion과의 성능 격차를 명확히 드러낸다.

![GENIE의 스텝 스킵과 DDIM 가속 성능 비교](figures/fig_2_3.png)
*Figure 6: GENIE 모델의 추론 스텝 수에 따른 AVG-ROUGE 비교 (스텝 스킵 vs DDIM). GENIE는 두 가속 방식 모두에서 AR-Diffusion보다 낮은 성능을 보인다. (Wu et al., 2023)*

### MBR 디코딩과 생성 다양성

확산 모델의 장점 중 하나는 동일 입력에서 다양한 후보를 샘플링할 수 있다는 것이다. AR-Diffusion은 이를 활용하여 Minimum Bayes Risk(MBR) 디코딩을 적용할 수 있다. 아래 그림은 후보 샘플 수와 번역 품질 간의 관계를 보여준다.

![MBR 디코딩에서 후보 샘플 수에 따른 SacreBLEU 변화](figures/fig_7.png)
*Figure 3. IWSLT14 De$\to$En에서 MBR 후보 샘플 수(n)에 따른 SacreBLEU. 샘플 수가 증가할수록 성능이 지속적으로 개선되어, AR-Diffusion이 의미 있는 다양성을 생성함을 보여준다.*

후보 샘플 수가 100개에서 약 1,000개로 증가할 때까지 SacreBLEU가 약 31.8에서 32.4 이상으로 꾸준히 향상되며, 이는 AR-Diffusion이 단순히 동일한 출력을 반복 생성하는 것이 아니라 의미적으로 유효한 다양한 변형을 생성한다는 것을 의미한다.

### 점진적 생성 과정 시각화

아래 그림은 AR-Diffusion이 순수 Gaussian 노이즈에서 실제 텍스트를 점진적으로 생성하는 과정의 중간 상태를 보여준다.

![AR-Diffusion의 20 스텝 점진적 텍스트 생성 과정](figures/fig_6.png)
*Figure 4. AR-Diffusion이 표준 Gaussian 노이즈에서 20 스텝에 걸쳐 텍스트를 생성하는 중간 상태. 색상의 밝기는 로짓 크기를 나타내며, 어두울수록 해당 토큰의 확신도가 높다. 앞쪽 토큰이 먼저 확정되고 뒤쪽 토큰이 나중에 결정되는 AR적 순서가 명확히 관찰된다.*

이 시각화에서 핵심적으로 관찰할 점은 두 가지다. 첫째, 앞쪽 위치의 토큰이 뒤쪽 위치보다 먼저 확정(어두운 색)되어 AR적 생성 순서가 실제로 작동함을 확인할 수 있다. 둘째, 각 디노이징 스텝에서 전체 시퀀스가 동시에 업데이트되므로 양방향 문맥이 활용된다는 점이다.

다양한 입력에 대한 추가 생성 사례는 이러한 점진적 복원 패턴이 일관되게 나타남을 보여준다.

![다양한 뉴스 기사에 대한 AR-Diffusion의 점진적 텍스트 생성 과정](figures/fig_10_1.png)
*Figure 7: 추가 생성 사례 — 뉴스 기사 생성에서 앞쪽 토큰이 먼저 확정되고 뒤쪽 토큰이 점진적으로 결정되는 AR적 디노이징 패턴이 일관되게 관찰된다. (Wu et al., 2023)*

---

## 의의 및 한계

**의의**

- **우아한 통합**: 계단식 노이즈라는 단순한 아이디어만으로 AR과 Diffusion을 구조적으로 결합한다. 별도의 인과 마스킹이나 추가 모듈 없이 노이즈 스케줄 설계만으로 순서 의존성이 자연스럽게 발현된다.
- **다양성 향상**: Diffusion의 다단계 확률적 복원 덕분에 AR 모델 대비 생성 다양성이 대폭 개선되며, MBR 디코딩 등 다양성 기반 전략의 활용이 가능하다.
- **유연한 조건화**: 전체 시퀀스 문맥을 양방향으로 활용하므로 텍스트 인필링, 조건부 생성 등 다양한 태스크에 자연스럽게 확장 가능하다.
- **이론적 정합성**: 위치별 타임스텝 할당이 AR 순서 의존성의 연속적 확률 해석을 제공하며, $t_i = T \cdot i/L$ 이라는 간결한 수식으로 표현된다.

**한계**

- **샘플링 비용**: 확산 모델 특성상 AR 모델 대비 샘플링 스텝이 많아 추론 속도가 느리다. 스텝 스킵과 DDIM 가속을 적용해도 AR 모델의 단일 패스 생성에 비하면 여전히 느리다.
- **연속 공간 제약**: 이산 토큰을 연속 임베딩 공간에서 확산하므로, 최종 토큰 디코딩 시 반올림(rounding) 오류가 발생할 수 있다. 이는 텍스트 확산 모델의 공통 문제이다.
- **대규모 LLM 대비 격차**: GPT-4, LLaMA 등 대형 AR 모델과의 직접 비교가 제시되지 않아, 실용적 우위 판단이 어렵다. 실험은 주로 base-scale Transformer와의 비교에 집중되어 있다.
- **긴 시퀀스 확장성**: 시퀀스가 길수록 뒤쪽 토큰의 타임스텝 $t_i$가 $T$에 가까워져 노이즈가 과도해지며, 이로 인한 품질 저하 가능성이 있다.

---

## 코드 예제

아래는 AR-Diffusion의 계단식 노이즈 스케줄을 간략히 구현한 PyTorch 예시다.

```python
import torch
import torch.nn as nn

class StaircaseNoiseSchedule:
    """AR-Diffusion의 위치 의존적 노이즈 타임스텝 스케줄"""

    def __init__(self, T: int, beta_start: float = 1e-4, beta_end: float = 0.02):
        self.T = T
        # DDPM 선형 베타 스케줄
        betas = torch.linspace(beta_start, beta_end, T)
        alphas = 1.0 - betas
        self.alpha_bar = torch.cumprod(alphas, dim=0)  # shape: (T,)

    def get_timestep(self, position: int, seq_len: int) -> int:
        """위치 i에 대한 타임스텝 t_i = T * (i / L) 반환"""
        return int(self.T * position / seq_len)

    def q_sample(self, x0: torch.Tensor, position: int, seq_len: int) -> torch.Tensor:
        """위치 position의 토큰 임베딩에 계단식 노이즈 추가"""
        t_i = self.get_timestep(position, seq_len)
        t_i = max(0, min(t_i, self.T - 1))  # 클리핑

        alpha_bar_t = self.alpha_bar[t_i]
        noise = torch.randn_like(x0)
        x_noisy = (alpha_bar_t ** 0.5) * x0 + ((1 - alpha_bar_t) ** 0.5) * noise
        return x_noisy, noise


def apply_staircase_noise(embeddings: torch.Tensor, schedule: StaircaseNoiseSchedule):
    """
    embeddings: (batch, seq_len, hidden_dim)
    각 위치에 계단식 노이즈를 적용하여 (x_noisy, noise_targets) 반환
    """
    B, L, D = embeddings.shape
    x_noisy = torch.zeros_like(embeddings)
    noise_targets = torch.zeros_like(embeddings)

    for i in range(L):
        x_noisy[:, i, :], noise_targets[:, i, :] = schedule.q_sample(
            embeddings[:, i, :], position=i, seq_len=L
        )
    return x_noisy, noise_targets


# 사용 예시
schedule = StaircaseNoiseSchedule(T=1000)
embeddings = torch.randn(4, 32, 768)  # batch=4, seq_len=32, hidden=768
x_noisy, noise_targets = apply_staircase_noise(embeddings, schedule)

# 위치별 실제 타임스텝 확인
timesteps = [schedule.get_timestep(i, seq_len=32) for i in range(32)]
print("계단식 타임스텝:", timesteps[:8], "...")  # [0, 31, 62, 93, ...]
```

---

## 관련 문서

- Diffusion-LM (Li et al., 2022): 연속 공간 확산 기반 텍스트 생성의 선구 연구
- MDLM (Sahoo et al., 2024): 마스킹 기반 이산 확산 언어 모델
- DDPM (Ho et al., 2020): AR-Diffusion이 채택한 표준 확산 노이즈 스케줄 기반
- DDIM (Song et al., 2020): 빠른 샘플링을 위한 결정론적 확산 역과정
- GENIE (Lin et al., 2023): 대규모 확산 기반 텍스트 생성 모델, AR-Diffusion의 주요 비교 대상