## 개요

D3PM(Structured Denoising Diffusion Models in Discrete State-Spaces)은 2021년 NeurIPS에서 Austin et al.이 발표한 논문으로, **이산 상태 공간에서의 확산 모델을 체계적으로 정립**한 선구적 연구다. DDPM이 연속 공간(이미지 픽셀, 오디오 신호)에서 가우시안 노이즈를 점진적으로 추가하고 제거하는 방식으로 성공을 거둔 것처럼, D3PM은 텍스트 토큰, 이산 이미지(픽셀 색상 256가지), 생물 서열 등 **이산 데이터에 확산 모델을 적용하는 통합 이론 프레임워크**를 구축했다.

이 논문의 핵심 기여는 **전이 행렬(transition matrix) $Q_t$**라는 통일된 수학적 도구로 다양한 이산 노이즈 프로세스를 표현한 것이다. 하나의 프레임워크 안에서 다음 세 가지 변형을 모두 수용하는 통합 ELBO를 도출했다:

- **균등 확산(Uniform diffusion)**: 토큰이 임의의 다른 토큰으로 균등하게 대체됨
- **흡수 확산(Absorbing diffusion)**: 토큰이 [MASK]로 비가역적으로 흡수됨
- **토큰 유사도 기반 확산(Token-based diffusion)**: 임베딩 공간에서 의미적으로 유사한 토큰으로 전환됨

D3PM은 현재 MDLM, LLaDA, dLLM, SEDD 등 모든 이산 확산 언어 모델 연구의 수학적 기반이 되는 논문이다.

## 배경 및 문제

### DDPM의 한계: 이산 데이터 불가

DDPM(Denoising Diffusion Probabilistic Models, 2020)은 연속 데이터에 가우시안 노이즈를 추가하는 순방향 과정을 다음과 같이 정의한다:

$$q(x_t \mid x_{t-1}) = \mathcal{N}(x_t; \sqrt{1-\beta_t} x_{t-1}, \beta_t I)$$

이 방식은 실수 벡터 $x$에는 완벽하게 작동하지만, 텍스트 토큰처럼 이산적인 데이터에는 직접 적용할 수 없다. "고양이"와 "강아지"의 중간 상태는 무엇인가? 이산 공간에서는 의미 있는 중간값이 존재하지 않으므로, 가우시안 노이즈 기반의 연속적 확산 프레임워크를 그대로 사용할 수 없다.

### 이전 접근법의 한계

이산 데이터에 확산을 적용하려는 이전 시도들은 각각 본질적 한계를 가지고 있었다:

1. **Hoogeboom et al. (2021)**: 범주형 균등 전이를 제안했으나 텍스트 모델링에 적합한 구조적(structured) 전이가 부재했다. 모든 토큰 간 전이를 동등하게 취급하므로 언어의 의미적 구조를 반영할 수 없었다.
2. **연속 임베딩 우회**: 토큰을 연속 임베딩으로 변환 후 연속 확산 적용 후 다시 토큰으로 디코딩하는 방식이었으나, 임베딩 공간과 이산 토큰 공간 사이의 불일치(mismatch) 문제가 발생했다.

D3PM은 이러한 한계를 극복하여 **이산 공간에서 직접 작동**하면서도 **도메인 구조를 반영할 수 있는** 유연한 프레임워크를 제안한다.

## 핵심 아이디어: 전이 행렬 기반 이산 확산

### 순방향/역방향 과정 개관

D3PM의 전체 구조는 연속 확산 모델(DDPM)과 동일한 순방향-역방향 패러다임을 따르되, 가우시안 노이즈 대신 **이산 전이 행렬**로 노이즈를 정의한다. 아래 그림은 이산 2D 범주형 변수(양자화된 Swiss Roll)를 예시로 세 가지 전이 방식의 순방향/역방향 과정을 보여준다.

![D3PM의 순방향/역방향 과정과 전이 행렬 시각화](figures/fig_1.png)
*D3PM의 순방향(상단) 및 역방향(하단) 과정. 양자화된 Swiss Roll 데이터에 대해 균등(uniform), 가우시안(Gaussian), 흡수(absorbing) 전이 행렬의 효과를 보여준다. 각 전이 행렬 $Q$의 구조(대각선 패턴)가 노이즈 주입 방식을 결정하며, 역방향 과정에서 신경망이 이를 학습하여 데이터를 복원한다.*

상단의 순방향 과정에서 각 전이 행렬의 구조적 차이가 명확히 드러난다. 균등 전이는 모든 상태로 균일하게 퍼지고, 가우시안 전이는 인접한 상태로 확산되며, 흡수 전이는 특정 상태(검은색)로 수렴한다.

### 전이 행렬 $Q_t$

D3PM의 수학적 핵심은 이산 상태 공간에서의 확산을 **전이 행렬(transition matrix)**로 표현하는 것이다. $K$개의 가능한 상태(어휘 크기)가 있을 때, 한 timestep에서의 상태 전이는 $K \times K$ 행렬 $Q_t$로 기술된다:

$$q(x_t \mid x_{t-1}) = \text{Cat}(x_t; \mathbf{p} = x_{t-1} Q_t)$$

여기서 $x_{t-1}$은 one-hot 벡터이고, $(Q_t)_{ij}$는 상태 $i$에서 상태 $j$로 전이할 확률을 나타낸다. 행렬의 각 행은 확률 분포를 이루므로 $\sum_j (Q_t)_{ij} = 1$이 성립한다.

**닫힌 형태의 주변 분포 (Closed-form Marginal):**

여러 스텝의 전이 행렬을 누적하면 임의의 timestep에서의 노이즈 상태를 한 번의 행렬 곱으로 계산할 수 있다:

$$q(x_t \mid x_0) = \text{Cat}(x_t; \mathbf{p} = x_0 \bar{Q}_t), \quad \bar{Q}_t = Q_1 Q_2 \cdots Q_t$$

여기서 $\bar{Q}_t$는 누적 전이 행렬이다. 이 성질은 학습 시 중간 스텝을 거치지 않고 $x_0$에서 $x_t$를 직접 샘플링할 수 있게 해주므로, 효율적인 학습에 핵심적이다.

**후방 분포 (Posterior):**

Bayes 정리를 적용하면 역방향 전이의 목표가 되는 후방 분포도 닫힌 형태로 얻는다:

$$q(x_{t-1} \mid x_t, x_0) = \frac{q(x_t \mid x_{t-1}) \, q(x_{t-1} \mid x_0)}{q(x_t \mid x_0)}$$

이를 행렬 연산으로 표현하면:

$$q(x_{t-1} \mid x_t, x_0) = \text{Cat}\left(x_{t-1}; \frac{x_t Q_t^{\top} \odot x_0 \bar{Q}_{t-1}}{x_0 \bar{Q}_t x_t^{\top}}\right)$$

분자의 두 항은 각각 "현재 관측 $x_t$에서 이전 상태 $x_{t-1}$로의 역전이 가능성"과 "원본 $x_0$에서 $x_{t-1}$까지의 순방향 도달 가능성"을 나타낸다. 신경망은 이 후방 분포를 근사하도록 훈련된다.

### 세 가지 전이 행렬

D3PM의 핵심 기여 중 하나는 전이 행렬의 **구조적 설계(structured design)**를 통해 다양한 이산 노이즈 프로세스를 통일적으로 표현한 것이다.

**1. 균등 전이 (Uniform Transition):**

$$Q_t^{\text{uniform}} = (1 - \beta_t) I + \frac{\beta_t}{K} \mathbf{1}\mathbf{1}^{\top}$$

확률 $\beta_t$로 현재 토큰을 $K$개 중 균등하게 샘플링된 임의 토큰으로 대체한다. 전이 행렬은 대각 성분이 $(1 - \beta_t + \beta_t/K)$이고 비대각 성분이 $\beta_t/K$인 구조다. 모든 전이를 동등하게 취급하므로 언어의 의미론적 구조를 반영하지 못한다.

**2. 흡수 전이 (Absorbing Transition):**

$$Q_t^{\text{absorb}} = (1 - \beta_t) I + \beta_t \mathbf{1} e_{[M]}^{\top}$$

확률 $\beta_t$로 현재 토큰을 [MASK] 토큰으로 "흡수"한다. [MASK]는 흡수 상태(absorbing state)이므로, 한번 마스크되면 이전 상태로 돌아갈 수 없다:

$$\lim_{T \to \infty} q(x_T = [M]^L \mid x_0) = 1$$

이 방식은 BERT의 마스크 언어 모델링과 구조적으로 유사하며, 논문에서 텍스트 생성에 가장 효과적인 것으로 나타났다.

**3. 토큰 유사도 기반 전이 (Token-based Transition):**

$$Q_t^{\text{token}} = (1 - \beta_t) I + \beta_t \Lambda$$

여기서 $\Lambda$는 토큰 간 유사도를 반영하는 확률 행렬이다. 예를 들어 임베딩 공간에서의 $k$-NN 그래프를 기반으로, 의미적으로 가까운 토큰들 사이에 더 높은 전이 확률을 부여할 수 있다. 아래 그림은 text8 데이터셋의 문자 수준에서 구축한 5-NN 그래프를 보여준다.

![문자 수준 5-NN 대칭 그래프 시각화](figures/fig_7.png)
*Figure 3: text8의 문자 수준 대칭 5-NN 그래프. 각 노드는 알파벳 문자를 나타내며, 임베딩 공간에서 가까운 문자들이 연결된다. 이 그래프 구조가 토큰 유사도 기반 전이 행렬 $\Lambda$의 기초가 되어, 의미적으로 유사한 토큰 간 전이를 우선시한다. (Austin et al., 2021)*

아래 그림은 텍스트 데이터에 대해 흡수 확산과 토큰 유사도 기반 확산이 어떻게 작동하는지를 구체적인 문장 예시로 보여준다.

![텍스트 데이터에 대한 두 가지 확산 방식 비교](figures/fig_6.png)
*텍스트 확산 노이즈 스케줄의 두 가지 예시. (a) 흡수+균등 확산: 토큰이 점진적으로 [MASK]로 대체되어 $T=25$에서는 전체가 마스킹된다. (b) 임베딩 공간 기반 최근접 이웃 확산: 의미적으로 유사한 토큰으로 전이되어 문장 구조가 점진적으로 변형된다. 왼쪽의 전이 확률 분포가 각 방식의 구조적 차이를 보여준다.*

흡수 확산(a)에서는 "The great brown fox hopped over the lazy dog"이 단계적으로 [MASK]로 대체되어 최종적으로 완전히 마스킹되는 반면, 토큰 유사도 기반 확산(b)에서는 "brown" -> "black", "dog" -> "cat"처럼 의미적으로 관련 있는 토큰으로 변형되는 패턴이 관찰된다.

### ELBO 유도

D3PM의 학습 목적함수는 변분 하한(ELBO)이다. 역과정 $p_\theta(x_{t-1} \mid x_t)$가 실제 후방 분포 $q(x_{t-1} \mid x_t, x_0)$에 가깝도록 KL 다이버전스를 최소화한다:

$$\mathcal{L}_{\text{VB}} = \mathbb{E}_{q} \left[ \underbrace{D_{\text{KL}}(q(x_T \mid x_0) \| p(x_T))}_{L_T} + \sum_{t=2}^{T} \underbrace{D_{\text{KL}}(q(x_{t-1} \mid x_t, x_0) \| p_\theta(x_{t-1} \mid x_t))}_{L_{t-1}} + \underbrace{(-\log p_\theta(x_0 \mid x_1))}_{L_0} \right]$$

각 항의 역할은 다음과 같다:
- $L_T$: 순방향 과정의 최종 분포와 사전 분포 사이의 KL (학습 파라미터 없으므로 상수)
- $L_{t-1}$: 시간 $t$에서의 역방향 전이가 실제 후방 분포를 얼마나 잘 근사하는지 측정
- $L_0$: 최종 복원 단계의 재구성 손실

실용적으로는 $p_\theta(x_{t-1} \mid x_t)$를 직접 파라미터화하는 대신, 신경망이 $\tilde{p}_\theta(\tilde{x}_0 \mid x_t)$로 원본 데이터 $x_0$를 직접 예측한 후 이를 후방 분포 공식에 대입하는 방식이 더 안정적이다:

$$p_\theta(x_{t-1} \mid x_t) = \sum_{\tilde{x}_0} q(x_{t-1} \mid x_t, \tilde{x}_0) \, \tilde{p}_\theta(\tilde{x}_0 \mid x_t)$$

이 "$x_0$-예측(x0-parameterization)" 방식은 모델이 각 timestep에서 노이즈가 제거된 원본을 추정하고, 이 추정값으로 정확한 역방향 전이 확률을 계산하는 구조다.

### 보조 크로스 엔트로피 손실

순수 ELBO만으로는 학습 신호가 불충분한 경우가 있다. D3PM은 이를 보완하기 위해 보조 크로스 엔트로피 손실을 추가했다:

$$\mathcal{L}_{\lambda} = \mathcal{L}_{\text{VB}} + \lambda \, \mathbb{E}_{t \sim \mathcal{U}(1,T), \, q(x_t \mid x_0)} \left[-\log \tilde{p}_\theta(x_0 \mid x_t)\right]$$

이 보조 손실은 모든 timestep에서 원본 데이터를 직접 예측하도록 강제하여 학습 그래디언트를 강화한다. $\lambda$는 하이퍼파라미터로, 논문에서는 $\lambda = 0.001$이 최적이었다. $\lambda$가 너무 크면 ELBO의 변분 목적이 훼손되고, 너무 작으면 보조 손실의 효과가 미미하다.

## 방법론

### 모델 아키텍처

D3PM은 데이터 도메인에 따라 서로 다른 신경망 아키텍처를 사용했다:

**텍스트 모델링:**
- 표준 트랜스포머 인코더 (양방향 어텐션) -- BERT와 유사한 구조
- sinusoidal 시간 임베딩을 토큰 임베딩에 가산
- 출력: 각 위치에서의 어휘 분포 $\tilde{p}_\theta(x_0^{(i)} \mid x_t)$ (softmax)

**이미지 생성 (이산 픽셀):**
- U-Net 구조를 채택하되, 각 픽셀의 색상을 256개 범주로 취급
- 시간 임베딩을 각 해상도 레벨에 주입

두 경우 모두, 모델의 출력은 원본 데이터 $x_0$에 대한 범주형 확률 분포이며, 이를 앞서 유도한 후방 분포 공식에 대입하여 역방향 샘플링을 수행한다.

### 노이즈 스케줄

노이즈 강도 $\beta_t$의 스케줄링은 확산 모델의 성능에 핵심적 영향을 미친다. 논문은 다음 스케줄들을 비교했다:

**선형 스케줄:**

$$\beta_t = \beta_{\min} + (\beta_{\max} - \beta_{\min}) \cdot \frac{t}{T}$$

**코사인 스케줄:**

$$\bar{\alpha}_t = \frac{f(t)}{f(0)}, \quad f(t) = \cos^2\left(\frac{t/T + 0.008}{1.008} \cdot \frac{\pi}{2}\right)$$

코사인 스케줄은 초기와 후기 단계에서 노이즈 변화가 완만하고 중간 단계에서 집중적으로 변화하는 특성이 있다. 텍스트 실험에서는 이 코사인 스케줄이 가장 좋은 성능을 보였다.

### 텍스트 실험 설정

| 설정 | 값 |
|------|----|
| 데이터셋 | text8 (100M 문자), LM1B |
| 어휘 크기 | 27 (text8: 알파벳+공백), 50K (LM1B) |
| 모델 | 6-레이어 트랜스포머 |
| Timesteps $T$ | 1000 |
| 배치 크기 | 256 |
| 보조 손실 $\lambda$ | 0.001 |

## 실험 결과

### Text8 언어 모델링

| 모델 | 방식 | BPC (Bits Per Character) |
|------|------|------------------------|
| Transformer AR | 자기회귀 | 1.13 |
| LSTM AR | 자기회귀 | 1.30 |
| D3PM (Absorbing) | 이산 확산 | 1.45 |
| D3PM (Token-based) | 이산 확산 | 1.50 |
| D3PM (Uniform) | 이산 확산 | 1.61 |

AR 모델 대비 성능 격차가 있지만, 이산 확산 모델이 텍스트 생성에 실현 가능함을 최초로 보인 결과다. 특히 흡수 확산이 세 가지 전이 유형 중 가장 우수했다.

### 흡수 vs 균등 전이 비교

| 전이 유형 | text8 BPC | LM1B PPL | 수렴 속도 |
|---------|---------|---------|--------|
| Uniform | 1.61 | 124.8 | 느림 |
| Token-based | 1.50 | 105.2 | 중간 |
| Absorbing | **1.45** | **98.3** | 빠름 |

흡수 확산이 텍스트에서 일관되게 가장 좋은 성능을 보인다. 이는 BERT 스타일의 마스킹이 자연어의 구조를 학습하는 데 가장 효과적인 귀납적 편향(inductive bias)을 제공한다는 것을 시사하며, 이것이 MDLM, LLaDA 등 후속 연구들이 흡수 확산을 채택하는 근거가 되었다.

아래 그림은 LM1B 데이터셋에서 추론 스텝 수에 따른 perplexity 변화와, 훈련된 흡수 모델의 텍스트 생성 및 복원 예시를 보여준다.

![LM1B에서의 perplexity 및 텍스트 생성/복원 결과](figures/fig_2.png)
*LM1B 실험 결과. 왼쪽: 추론 스텝 수에 따른 perplexity — 균등(uniform), 마스크(mask), 흡수(absorbing) 세 방식 비교. 스텝 수가 증가할수록 perplexity가 감소하며, 흡수 확산이 가장 낮은 perplexity를 달성한다. 오른쪽: 훈련된 D3PM 흡수 모델로 새로운 문장 생성(상단) 및 손상된 문장 복원(하단) 예시.*

### 추론 스텝 수에 따른 성능 변화

D3PM의 중요한 특성 중 하나는 추론 시 사용하는 스텝 수(inference steps)와 성능 사이의 관계다. 아래 그림은 text8 데이터셋에서 세 가지 전이 유형별로 추론 스텝 수를 변화시켰을 때의 ELBO(bits/dim) 변화를 보여준다.

![추론 스텝 수에 따른 ELBO 변화](figures/fig_10.png)
*text8에서 추론 스텝 수에 따른 ELBO(bits/dim) 스케일링. 흡수 확산(mask, 파란색)이 모든 스텝 수에서 가장 낮은 ELBO를 보이며, 특히 적은 스텝(2~16)에서의 성능 우위가 두드러진다. 32스텝 이상에서는 세 방식 모두 수렴하기 시작하며, 128스텝 이후로는 성능 향상이 미미하다.*

이 결과는 실용적으로 중요한 시사점을 제공한다. 흡수 확산은 적은 추론 스텝에서도 상대적으로 좋은 성능을 유지하므로, 추론 비용과 품질 사이의 트레이드오프에서 유리하다.

실제 추론 시간을 AR 모델과 비교하면, 확산 모델의 병렬 생성 이점이 확인된다.

![D3PM 흡수 모델과 AR 모델의 추론 시간 비교](figures/fig_11.png)
*Figure 8: text8에서 D3PM 마스크(흡수) 확산과 자기회귀 모델의 추론 시간 비교. AR 모델은 시퀀스 길이에 비례하여 일정한 시간(약 0.5초)이 소요되는 반면, 확산 모델은 추론 스텝 수에 따라 시간이 증가한다. 약 300 스텝 이하에서는 확산 모델이 AR보다 빠르며, 이는 병렬 디노이징의 이점을 보여준다. (Austin et al., 2021)*

### 이미지 생성 (이산 픽셀)

CIFAR-10에서의 이미지 생성 성능 비교:

| 모델 | FID ↓ |
|------|------|
| DDPM (연속) | 3.17 |
| D3PM (Token-based / Gauss+logistic) | **5.87** |
| D3PM (Absorbing) | 6.12 |
| D3PM (Uniform) | 7.34 |

연속 DDPM보다 FID가 높지만(즉 품질이 낮지만), 이산 공간에서도 유의미한 이미지 생성이 가능함을 입증했다. 흥미롭게도 이미지에서는 텍스트와 달리 토큰 유사도 기반 전이(Gauss+logistic)가 가장 좋은 성능을 보였는데, 이는 픽셀 값 사이의 순서 구조를 전이 행렬이 활용할 수 있기 때문이다.

아래 그림은 D3PM 흡수 모델의 점진적 샘플링 과정을 보여준다. $t=1000$(완전 마스킹)에서 $t=0$(복원된 이미지)까지 역방향 확산이 진행되면서 이미지가 점진적으로 형성되는 것을 확인할 수 있다.

![D3PM 흡수 모델의 점진적 이미지 복원 과정](figures/fig_3_1.png)
*D3PM 흡수(absorbing) 모델의 CIFAR-10 점진적 샘플링. $t=1000, 900, 800, \ldots, 0$에서의 복원 과정을 보여준다. 초기에는 거의 모든 픽셀이 마스킹되어 있다가 역방향 과정이 진행됨에 따라 점차 구조적 정보가 복원되며, 마지막 수십 스텝에서 세부 디테일이 결정된다.*

비교를 위해, Gauss+logistic 전이를 사용한 D3PM의 점진적 샘플링 과정도 함께 살펴보자. 흡수 모델과 달리 초기 상태가 균등 노이즈이며, 색상 값의 인접 구조를 활용하여 복원한다.

![D3PM Gauss+logistic 모델의 점진적 이미지 복원 과정](figures/fig_3_2.png)
*Figure 6: D3PM Gauss+logistic 모델의 CIFAR-10 점진적 샘플링. 흡수 모델과 달리 초기 상태($t=1000$)가 랜덤 색상 노이즈이며, 인접한 픽셀 값으로의 전이를 통해 점진적으로 자연스러운 이미지가 형성된다. 특히 중간 단계($t=400\sim600$)에서 이미지의 대략적 구조가 먼저 잡히는 coarse-to-fine 패턴이 관찰된다. (Austin et al., 2021)*

Gauss+logistic 모델이 생성한 비선별(non cherry-picked) CIFAR-10 샘플의 전반적 품질은 아래와 같다.

![D3PM Gauss+logistic 모델의 CIFAR-10 생성 샘플](figures/fig_3_3.png)
*Figure 7: D3PM Gauss+logistic 모델의 비선별 CIFAR-10 생성 샘플. 동물, 차량, 풍경 등 다양한 카테고리의 이미지가 생성되며, 이산 확산으로도 시각적으로 인식 가능한 수준의 이미지 품질을 달성한다. FID 5.87로 세 가지 전이 유형 중 최고 성능을 기록했다. (Austin et al., 2021)*

### 보조 손실의 효과

| 설정 | text8 BPC |
|------|----------|
| ELBO만 ($\mathcal{L}_{\text{VB}}$) | 1.52 |
| ELBO + 보조 CE ($\lambda=0.001$) | **1.45** |
| ELBO + 보조 CE ($\lambda=0.01$) | 1.47 |
| 보조 CE만 | 1.68 |

$\lambda = 0.001$에서 최적 성능을 보이며, 순수 ELBO 대비 0.07 BPC 개선이 관찰된다. 보조 CE만 사용하면 변분 목적이 없어 성능이 크게 하락하므로, ELBO와 보조 손실의 적절한 조합이 중요하다.

## 의의 및 한계

### 의의

- **이산 확산의 이론적 기반 확립**: 전이 행렬이라는 통합 수학적 도구로 이산 공간에서의 확산 모델을 체계적으로 정립했다. 이 프레임워크가 이후 모든 이산 확산 연구의 출발점이 되었다.
- **흡수 확산의 우수성 발견**: 텍스트 생성에서 흡수 전이가 균등 전이보다 일관되게 우수함을 체계적으로 입증하여, 후속 연구(MDLM, LLaDA)의 설계 방향을 제시했다.
- **엄밀한 ELBO 유도**: 이산 공간에서의 변분 하한을 닫힌 형태로 유도하고, 보조 손실과의 결합이 필요함을 실험적으로 보였다.
- **다양한 도메인 적용 가능성**: 텍스트, 이미지, 생물 서열 등 다양한 이산 데이터에 통일된 프레임워크로 적용할 수 있음을 입증했다.

### 한계

- **AR 대비 성능 격차**: 텍스트 모델링에서 자기회귀 모델 대비 BPC/PPL이 상당히 높으며, 이 격차는 후속 연구에서 점진적으로 줄어들었다.
- **느린 학습 수렴**: 이산 전이 행렬의 KL 다이버전스 계산이 연속 공간보다 복잡하여 학습이 불안정하고 수렴이 느리다.
- **고정 timestep 한계**: $T$를 크게 설정해야 품질이 보장되므로 추론 속도가 느리다(1000 스텝 기준 AR 대비 더 긴 추론 시간).
- **스케일 미검증**: 소규모 모델(6-레이어 트랜스포머)에서만 실험했으므로, 대규모(1B+) 모델에서의 성능은 확인되지 않았다.
- **보조 손실 의존**: 순수 ELBO만으로는 충분한 성능을 달성하지 못하여 보조 크로스 엔트로피 손실이 필수적이다.

### D3PM이 열어준 연구 방향

| 후속 연구 | D3PM의 어떤 측면을 발전시켰나 |
|---------|-----------------------------|
| MDLM (2024) | ELBO를 continuous-time 극한으로 확장하여 더 tight한 하한 도출 |
| SEDD (2024) | 전이 행렬 대신 스코어 함수를 이산 공간에서 직접 추정 |
| LLaDA (2025) | 흡수 확산을 8B 파라미터 규모로 스케일링하여 AR 대비 경쟁력 입증 |
| Diffusion-LM (2022) | 이산 확산 대신 연속 임베딩 공간에서의 확산을 탐구 |
| DiffuSeq (2023) | 흡수 확산을 Seq2Seq 조건부 생성 태스크에 적용 |

## 코드 예제

### 전이 행렬 구현

```python
import math
import torch
import torch.nn.functional as F


class DiscreteTransition:
    """D3PM의 이산 전이 행렬 구현."""

    @staticmethod
    def uniform(K: int, beta: float, device) -> torch.Tensor:
        """
        균등 전이 행렬.
        Q[i,j] = (1-beta)*I[i,j] + beta/K
        """
        Q = (1.0 - beta) * torch.eye(K, device=device)
        Q += (beta / K) * torch.ones(K, K, device=device)
        return Q  # [K, K]

    @staticmethod
    def absorbing(K: int, beta: float, mask_id: int, device) -> torch.Tensor:
        """
        흡수 전이 행렬.
        Q[i, mask_id] += beta  — 모든 상태에서 mask로 이동 가능
        """
        Q = (1.0 - beta) * torch.eye(K, device=device)
        Q[:, mask_id] += beta
        return Q  # [K, K]


def sample_forward(
    x0: torch.Tensor,
    Qt_bar: torch.Tensor,
) -> torch.Tensor:
    """
    순방향 과정 샘플링: q(x_t | x_0) = Cat(x_t; x_0 @ Qt_bar)

    Args:
        x0: 원본 토큰 [B, L] (정수)
        Qt_bar: 누적 전이 행렬 [K, K]

    Returns:
        x_t: 노이즈 적용 토큰 [B, L]
    """
    B, L = x0.shape
    K = Qt_bar.shape[0]

    x0_onehot = F.one_hot(x0, num_classes=K).float()  # [B, L, K]
    probs = x0_onehot @ Qt_bar  # [B, L, K] — 전이 확률

    x_t = torch.multinomial(
        probs.view(-1, K), num_samples=1
    ).view(B, L)
    return x_t


def compute_posterior(
    x_t_onehot: torch.Tensor,
    x0_pred_probs: torch.Tensor,
    Qt: torch.Tensor,
    Qt_bar: torch.Tensor,
    Qt_bar_prev: torch.Tensor,
) -> torch.Tensor:
    """
    후방 분포: q(x_{t-1} | x_t, x0) ∝ q(x_t|x_{t-1}) * q(x_{t-1}|x_0)
    = (x_t @ Qt.T) ⊙ (x0 @ Qt_bar_prev) / (x0 @ Qt_bar @ x_t)

    Args:
        x_t_onehot:    [B, L, K] — 현재 노이즈 토큰 one-hot
        x0_pred_probs: [B, L, K] — 모델의 x_0 예측 확률
        Qt, Qt_bar, Qt_bar_prev: [K, K] 전이 행렬들

    Returns:
        post_probs: [B, L, K]
    """
    left = x_t_onehot @ Qt.T          # [B, L, K]  q(x_t | x_{t-1})
    right = x0_pred_probs @ Qt_bar_prev  # [B, L, K]  q(x_{t-1} | x_0)
    numerator = left * right           # elementwise

    # 분모: x0_pred @ Qt_bar 후 x_t와 내적
    denom_probs = x0_pred_probs @ Qt_bar  # [B, L, K]
    denominator = (denom_probs * x_t_onehot).sum(-1, keepdim=True).clamp(1e-10)

    return numerator / denominator  # [B, L, K]
```

### D3PM 학습 손실

```python
class D3PM(torch.nn.Module):
    """D3PM: Discrete Denoising Diffusion Probabilistic Model (간소화 버전)."""

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 512,
        nhead: int = 8,
        num_layers: int = 6,
        T: int = 1000,
        mask_token_id: int = None,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.T = T
        self.mask_token_id = mask_token_id if mask_token_id is not None else vocab_size
        K = vocab_size + 1  # +1 for [MASK]

        self.embed = torch.nn.Embedding(K, d_model)
        self.pos_embed = torch.nn.Embedding(512, d_model)
        enc_layer = torch.nn.TransformerEncoderLayer(
            d_model, nhead, d_model * 4, batch_first=True, norm_first=True
        )
        self.encoder = torch.nn.TransformerEncoder(enc_layer, num_layers)
        self.head = torch.nn.Linear(d_model, K)
        self.time_mlp = torch.nn.Sequential(
            torch.nn.Linear(d_model, d_model * 2),
            torch.nn.SiLU(),
            torch.nn.Linear(d_model * 2, d_model),
        )

        # 코사인 스케줄로 Qt_bar 사전 계산
        betas = self._cosine_betas(T)
        self.register_buffer("betas", betas)
        Qt_bars = self._precompute_Qt_bars(betas, K)
        self.register_buffer("Qt_bars", Qt_bars)

    @staticmethod
    def _cosine_betas(T: int) -> torch.Tensor:
        steps = torch.arange(T + 1) / T
        alphas = torch.cos((steps + 0.008) / 1.008 * math.pi / 2) ** 2
        alphas = alphas / alphas[0]
        return (1 - alphas[1:] / alphas[:-1]).clamp(0, 0.999)

    def _precompute_Qt_bars(self, betas, K) -> torch.Tensor:
        Qt_bars = []
        Qt_bar = torch.eye(K)
        for t in range(self.T):
            beta = betas[t].item()
            Qt = DiscreteTransition.absorbing(
                K, beta, self.mask_token_id, device=torch.device("cpu")
            )
            Qt_bar = Qt_bar @ Qt
            Qt_bars.append(Qt_bar)
        return torch.stack(Qt_bars)  # [T, K, K]

    def sinusoidal_emb(self, t: torch.Tensor) -> torch.Tensor:
        d = self.embed.embedding_dim
        half = d // 2
        freqs = torch.exp(
            -math.log(10000)
            * torch.arange(half, device=t.device).float() / half
        )
        x = t[:, None].float() * freqs[None, :]
        return self.time_mlp(torch.cat([x.sin(), x.cos()], -1))

    def forward(self, x_t: torch.Tensor, t: torch.Tensor) -> torch.Tensor:
        B, L = x_t.shape
        pos = torch.arange(L, device=x_t.device).unsqueeze(0)
        h = self.embed(x_t) + self.pos_embed(pos)
        h = h + self.sinusoidal_emb(t).unsqueeze(1)
        return self.head(self.encoder(h))  # [B, L, K]

    def compute_loss(self, x0: torch.Tensor, lambda_aux: float = 0.001) -> torch.Tensor:
        """
        D3PM 손실: ELBO + 보조 CE
        (간소화: KL 대신 직접 CE 사용)
        """
        B, L = x0.shape
        K = self.vocab_size + 1
        device = x0.device

        # timestep 균등 샘플링
        t_idx = torch.randint(1, self.T, (B,), device=device)
        t_norm = t_idx.float() / self.T

        # 순방향: q(x_t | x_0)
        Qt_bar = self.Qt_bars[t_idx].to(device)  # [B, K, K]
        x0_oh = F.one_hot(x0, num_classes=K).float()  # [B, L, K]
        probs = torch.einsum("blk,bkj->blj", x0_oh, Qt_bar)  # [B, L, K]
        x_t = torch.multinomial(probs.view(-1, K), 1).view(B, L)

        # 역방향 예측
        logits = self.forward(x_t, t_norm)  # [B, L, K]

        # ELBO 근사: x_0 직접 예측 CE
        elbo = F.cross_entropy(logits.view(-1, K), x0.view(-1), reduction="mean")
        # 보조 손실 (동일 공식이지만 개념적으로 분리)
        aux = elbo
        return elbo + lambda_aux * aux
```

### 텍스트 생성

```python
@torch.no_grad()
def d3pm_generate(model: D3PM, seq_len: int, device: str = "cuda") -> torch.Tensor:
    """
    D3PM 생성: T에서 0으로 후방 분포 따라 역방향 샘플링.
    """
    K = model.vocab_size + 1
    T = model.T

    # t=T: 완전 마스크 초기화
    x = torch.full((1, seq_len), model.mask_token_id, dtype=torch.long, device=device)

    for t_idx in reversed(range(1, T)):
        t_norm = torch.tensor([t_idx / T], device=device)

        # x_0 예측
        logits = model(x, t_norm)
        x0_probs = F.softmax(logits, dim=-1).squeeze(0)  # [L, K]

        # 후방 계산
        Qt_bar = model.Qt_bars[t_idx].to(device)
        Qt_bar_prev = model.Qt_bars[t_idx - 1].to(device)
        beta = model.betas[t_idx].item()
        Qt = DiscreteTransition.absorbing(K, beta, model.mask_token_id, device)

        x_oh = F.one_hot(x.squeeze(0), num_classes=K).float()  # [L, K]
        post = compute_posterior(
            x_oh.unsqueeze(0), x0_probs.unsqueeze(0),
            Qt, Qt_bar, Qt_bar_prev
        ).squeeze(0)  # [L, K]

        x = torch.multinomial(post.clamp(1e-10), 1).T.unsqueeze(0)  # [1, L]

    return x.squeeze(0)
```

## 관련 문서

- [[ddpm|DDPM: Denoising Diffusion Probabilistic Models]] -- D3PM의 연속 공간 전작
- [[mdlm|Simple and Effective Masked Diffusion Language Models (MDLM)]] -- D3PM ELBO를 continuous-time으로 확장한 후속 연구
- [[sedd|Score Entropy Discrete Diffusion (SEDD)]] -- 스코어 함수 기반 이산 확산
- [[llada|Large Language Diffusion with mAsking (LLaDA)]] -- D3PM 흡수 확산의 대규모 구현
- [[diffusion-lm|Diffusion-LM]] -- 연속 공간에서 텍스트 확산을 시도한 동시기 연구
