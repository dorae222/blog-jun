<!-- infographic-hero -->
![Simple Diffusion Language Modeling 핵심 요약](figures/infographic.svg)

*Figure: Simple Diffusion Language Modeling 한 장 요약 인포그래픽*

## 개요

dLLM(Simple Diffusion Language Modeling)은 2026년 arXiv에 발표된 논문으로, 기존 확산 언어 모델의 복잡성을 대폭 줄이면서도 자기회귀(AR) 모델과 경쟁하는 성능을 달성한 프레임워크다. 저자들은 마스크 확산(masked diffusion)과 흡수 확산(absorbing diffusion)이 사실 동일한 수학적 구조를 공유한다는 점에 착안하여, 이 둘을 **시간 조건부 노이즈 제거**라는 단일 메커니즘으로 통합했다.

이 논문의 핵심 메시지는 명확하다: 확산 언어 모델의 성능 격차가 복잡한 아키텍처나 특수한 훈련 목적함수 때문이 아니라, 올바른 시간 조건화(time conditioning)와 ELBO 설계에서 비롯된다는 것이다.

주요 기여는 다음과 같다:

- 마스크 확산과 흡수 확산을 통합하는 단순 프레임워크 제안
- 시간 임베딩을 통한 노이즈 수준 인식 메커니즘 도입
- 효율적 추론을 위한 order-agnostic 생성 전략
- 다양한 벤치마크에서 LLaMA급 AR 모델에 근접한 성능 달성

## 배경 및 문제

### 자기회귀 언어 모델의 지배

현재 언어 모델의 주류는 좌에서 우로 순차적으로 토큰을 생성하는 **자기회귀(AR)** 방식이다. GPT, LLaMA, Gemini 등 대부분의 대형 언어 모델이 이 패러다임을 따른다. AR 모델의 학습 목표는 간단하다:

$$\mathcal{L}_{AR} = -\sum_{t=1}^{T} \log p_\theta(x_t \mid x_1, \ldots, x_{t-1})$$

이 방식은 강력하지만 두 가지 구조적 한계가 있다. 첫째, **단방향 의존성** ( 각 토큰은 왼쪽 컨텍스트만 볼 수 있어 양방향 정보를 활용하지 못한다. 둘째, **순차 생성** ) 토큰을 하나씩 생성해야 하므로 병렬화가 어렵다.

### 확산 모델의 잠재력

이미지, 오디오, 비디오 분야에서 확산 모델은 AR 모델을 압도하는 성능을 보였다. 자연어 처리에서도 비슷한 혁명이 가능하지 않을까? 이것이 텍스트 확산 연구의 출발점이다.

텍스트 확산 모델은 두 가지 방향으로 발전해왔다:

1. **연속 공간 확산**: 토큰 임베딩에 가우시안 노이즈를 추가하는 방식 (Diffusion-LM)
2. **이산 공간 확산**: 토큰을 직접 마스크나 랜덤 토큰으로 교체하는 방식 (D3PM, MDLM)

### 기존 이산 확산의 문제점

기존 마스크 기반 이산 확산 모델들은 다음과 같은 문제를 안고 있었다:

- **복잡한 ELBO**: 각 timestep별로 별도의 손실 항이 필요하여 학습이 불안정
- **시간 정보 미활용**: 모델이 현재 노이즈 수준(마스크 비율)을 명시적으로 모르는 경우가 많음
- **비효율적 추론**: 디노이징 스텝 수가 많아야 좋은 품질 달성

dLLM은 이러한 문제들을 근본부터 재설계하여 해결한다.

## 핵심 아이디어

### 마스크 확산의 통합 시각

dLLM의 핵심 통찰은 마스크 확산 과정을 **시간 $t$에서의 조건부 분포**로 표현하면 매우 단순해진다는 것이다.

시간 $t \in [0, 1]$에서 토큰 $x_0$가 마스크 토큰 $[M]$으로 교체될 확률을 $\alpha_t$라 하면, 순방향 과정(forward process)은:

$$q(x_t \mid x_0) = \text{Cat}(x_t; (1-\alpha_t) \cdot \mathbf{e}_{x_0} + \alpha_t \cdot \mathbf{e}_{[M]})$$

여기서 $\mathbf{e}_{x_0}$는 원래 토큰의 one-hot 벡터, $\mathbf{e}_{[M]}$은 마스크 토큰의 one-hot 벡터다. $t=0$이면 완전한 원본 토큰, $t=1$이면 완전히 마스크된 상태다.

이 공식화의 핵심은 마스크 확산(masked diffusion)과 흡수 확산(absorbing diffusion)이 모두 동일한 **categorical 분포의 특수한 경우**라는 점이다. 흡수 상태(absorbing state)가 곧 마스크 토큰 $[M]$이 되므로, 두 접근법은 수학적으로 동치다. 이를 통해 기존에 별도로 발전하던 두 방향의 연구를 하나의 프레임워크로 통합할 수 있다.

### 시간 조건부 노이즈 제거

dLLM의 핵심은 모델 $p_\theta(x_0 \mid x_t, t)$가 **현재 시간 $t$를 명시적으로 조건으로 받는다는 것**이다. 이는 모델이 자신이 얼마나 마스크된 입력을 처리하고 있는지를 알고, 적절한 수준의 불확실성을 갖고 예측하도록 한다.

기존 BERT식 마스크 언어 모델링(MLM)과의 차이점:
- BERT: $p_\theta(x_0 \mid x_t)$ ( 시간 정보 없음, 항상 15% 마스크
- dLLM: $p_\theta(x_0 \mid x_t, t)$ ) 시간 $t$에 따라 다른 마스크 비율 처리

시간 $t$는 sinusoidal 임베딩 또는 learned 임베딩을 통해 트랜스포머의 각 레이어에 주입된다. 이 차이가 단순해 보이지만, 시간 조건화의 유무가 확산 LM의 성능을 결정짓는 핵심 요인임을 논문은 실험적으로 입증한다.

### 단순화된 ELBO

dLLM의 학습 목적함수는 놀랍도록 단순하다. 변분 하한(ELBO)을 전개하면 다음과 같은 형태가 된다:

$$\mathcal{L}_{dLLM} = \mathbb{E}_{t \sim \mathcal{U}[0,1], x_t \sim q(x_t|x_0)} \left[ w(t) \cdot \sum_{i: x_t^i = [M]} \log p_\theta(x_0^i \mid x_t, t) \right]$$

여기서 $w(t)$는 시간에 따른 가중치 함수이며, 합산은 마스크된 위치 $i$에 대해서만 이루어진다. 이 손실 함수는 **마스크된 토큰들을 올바르게 복원하는 것**이 유일한 학습 목표임을 명확히 한다.

가중치 함수 $w(t)$의 역할은 중요하다. $t$가 작을 때(마스크 비율이 낮을 때)는 복원이 쉬우므로 가중치를 낮게, $t$가 클 때(대부분이 마스크된 상태)는 가중치를 높게 설정하여 학습 신호의 분산을 줄인다. 구체적으로는 다음과 같은 중요도 가중치를 사용한다:

$$w(t) = \frac{\alpha'(t)}{1 - \alpha_t}$$

여기서 $\alpha'(t)$는 마스크 확률의 시간 미분이다.

핵심 결과: 이 ELBO를 최소화하는 것이 데이터 분포의 로그 우도를 최대화하는 것과 동치임을 증명한다.

## 방법론

### 아키텍처

dLLM은 표준 트랜스포머 디코더 구조를 사용하지만 두 가지 핵심 수정이 있다:

**1. 시간 임베딩 (Time Embedding)**

$$\text{emb}(t) = \text{MLP}(\text{sinusoidal}(t))$$

이 임베딩은 각 트랜스포머 레이어의 LayerNorm에 AdaLN(Adaptive Layer Normalization) 방식으로 주입된다:

$$\text{AdaLN}(h, t) = \gamma(t) \cdot \frac{h - \mu_h}{\sigma_h} + \beta(t)$$

여기서 $\gamma(t)$와 $\beta(t)$는 시간 임베딩의 선형 변환이다. 이 구조는 이미지 확산 모델인 DiT(Diffusion Transformer)에서 차용한 것으로, 시간 정보를 normalization의 scale과 shift 파라미터에 직접 반영하여 각 레이어가 현재 노이즈 수준에 맞게 동작하도록 한다.

**2. 비인과적 어텐션 (Non-causal Attention)**

AR 모델과 달리, dLLM은 양방향 어텐션(bidirectional attention)을 사용한다. 마스크된 토큰을 복원할 때 전체 컨텍스트(좌우 모두)를 활용할 수 있다:

$$\text{Attn}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right) V$$

여기서 마스킹 행렬이 인과적(causal) 마스크가 아닌 단위 행렬(identity, 즉 완전 어텐션)임을 주목하라. 이는 BERT와 유사한 구조이지만, 시간 조건화와 결합되어 생성 모델로서 기능한다는 점이 근본적으로 다르다.

### 추론 전략

훈련된 dLLM에서 텍스트를 생성하는 방법은 여러 가지가 있다.

**마스크-to-토큰 디노이징:**

1. 모든 위치를 $[M]$으로 초기화: $x_1 = [M, M, \ldots, M]$
2. 시간을 $t = 1$에서 $t = 0$으로 역방향으로 진행:
   $$x_{t-\Delta t} \sim p_\theta(x_0 \mid x_t, t) \text{ 에서 샘플링 후 일부 마스크 유지}$$
3. 각 스텝에서 신뢰도(confidence)가 높은 토큰부터 마스크 해제

아래 그림은 dLLM의 텍스트 생성 과정을 터미널 시각화로 보여준다. 완전히 마스크된 상태에서 시작하여 점진적으로 토큰이 복원되는 과정을 확인할 수 있다.

![dLLM 텍스트 생성 과정 시각화: 마스크 토큰에서 디코딩된 토큰으로의 전환](figures/fig_7_2.png)
*Figure 3. dLLM의 iterative denoising 생성 과정. 마스크된 토큰들이 각 디노이징 스텝마다 신뢰도 순서대로 복원되어 최종 텍스트가 완성된다. AR 모델과 달리 생성 순서가 좌-우 고정이 아니라, 모델이 확신하는 위치부터 자유롭게 채워나간다.*

이처럼 dLLM은 order-agnostic한 생성을 수행한다. 문장의 중간 부분이 먼저 채워지기도 하고, 끝 부분이 먼저 결정되기도 한다. 이는 양방향 컨텍스트를 활용하는 확산 모델의 고유한 장점이다.

**효율적 추론을 위한 스텝 수 감소:**

기본 설정에서 $N = 10 \sim 50$ 스텝이면 충분한 품질을 달성한다. 이는 이미지 확산 모델의 수백 스텝보다 훨씬 효율적이다. 텍스트의 이산적 특성 덕분에 각 스텝에서 결정적으로 마스크를 해제할 수 있기 때문이다.

**추론 가속 기법:**

dLLM은 여러 가지 추론 가속 전략을 지원한다:

- **Cache**: KV 캐시를 활용하여 이미 결정된 토큰의 어텐션 연산을 재사용
- **Parallel**: 여러 토큰을 동시에 디코딩하여 단일 스텝에서 처리량 증가
- **Cache & Parallel**: 두 기법의 조합으로 최대 속도 향상 달성

아래 그림은 LLaDA-Instruct 모델에서 다양한 디코딩 전략의 정확도를 비교한 것이다.

![디코딩 전략별 정확도 비교 (LLaDA-Instruct)](figures/fig_8_1.png)
*Figure 4. 다양한 디코딩 전략(Random, Cache, Parallel, Cache & Parallel)에 따른 벤치마크 정확도 비교. Parallel 디코딩은 생성 속도를 높이면서도 정확도 손실을 최소화하며, Cache와 결합 시 속도와 품질의 최적 균형을 달성한다.*

속도와 정확도 사이의 trade-off를 더 상세히 분석한 결과는 아래와 같다. 각 디코딩 전략에 따른 속도 배수(Speedup)와 벤치마크 정확도의 관계를 산점도로 보여준다.

![디코딩 전략별 속도-정확도 trade-off 산점도](figures/fig_8_2.png)
*Figure 4-1: Dream 모델에서 디코딩 전략별 속도(Speedup) 대비 정확도. 각 벤치마크(HellaSwag, PIQA, ARC 등)에 대해 Cache, Parallel, Cache & Parallel 전략의 Pareto 프론티어가 나타난다. Parallel 전략은 최대 4배 속도 향상을 달성하면서도 정확도 하락을 5% 이내로 유지한다. (Zhou et al., 2026)*

### 노이즈 스케줄

dLLM은 코사인 노이즈 스케줄을 채택한다:

$$\alpha_t = 1 - \cos\left(\frac{\pi t}{2}\right)^2$$

이 스케줄은 $t=0$ 근처에서 변화가 느리고 $t=1$ 근처에서 빠르게 변한다. 직관적으로, 처음에는 조금씩 마스크를 해제하다가 나중에 많이 해제하는 것이 생성 품질에 유리하다. 이는 디노이징 초기 단계에서는 전체적인 구조를 먼저 잡고, 후반 단계에서 세부 토큰을 결정하는 coarse-to-fine 전략에 해당한다.

### 학습 세부 사항

| 구성 요소 | 설정값 |
|----------|-------|
| 모델 크기 | 340M, 1B, 3B 파라미터 |
| 학습 토큰 수 | 300B tokens |
| 배치 크기 | 2M tokens/step |
| 학습률 | 3e-4 (cosine decay) |
| Optimizer | AdamW ($\beta_1=0.9, \beta_2=0.95$) |
| 시간 샘플링 | $t \sim \mathcal{U}[0, 1]$ + 중요도 가중치 |

## 실험 결과

### 언어 모델링 퍼플렉시티

표준 언어 모델링 벤치마크인 GPT-2 수준 실험에서의 퍼플렉시티(PPL) 비교:

| 모델 | 방식 | WikiText103 PPL | One Billion Word PPL |
|------|------|----------------|---------------------|
| GPT-2 (117M) | AR | 29.4 | 41.2 |
| BERT (110M) | MLM | N/A (단방향 평가 불가) | N/A |
| D3PM (absorbing) | 이산 확산 | 76.4 | 89.3 |
| MDLM (168M) | 마스크 확산 | 26.2 | 38.7 |
| **dLLM (170M)** | **마스크 확산** | **22.8** | **35.1** |

dLLM은 동일 규모의 GPT-2를 퍼플렉시티에서 능가하며, 기존 마스크 확산 모델인 MDLM 대비도 유의미한 개선을 보인다.

### 벤치마크 성능 (3B 모델)

| 벤치마크 | LLaMA 3B (AR) | LLaDA 8B (마스크 확산) | dLLM 3B |
|---------|-------------|---------------------|--------|
| HellaSwag | 78.3 | 74.2 | 76.9 |
| PIQA | 79.6 | 77.8 | 79.1 |
| WinoGrande | 70.5 | 68.4 | 71.2 |
| ARC-Easy | 74.2 | 72.1 | 75.3 |
| ARC-Challenge | 44.8 | 43.2 | 45.6 |
| Average | 69.5 | 67.1 | **69.6** |

3B dLLM이 8B LLaDA보다 높은 평균 성능을 보이며, 동급 LLaMA 3B와 거의 동등한 수준이다.

### 추론 전략별 성능 분석

다양한 디코딩 전략이 벤치마크 성능에 미치는 영향을 레이더 차트로 분석하면 흥미로운 패턴이 나타난다.

![다양한 추론 전략에 따른 벤치마크 성능 레이더 차트 (LLaDA-Instruct)](figures/fig_11_1.png)
*Figure 5. LLaDA-Instruct 모델에서 추론 전략별 벤치마크 성능 비교. Baseline(녹색)은 표준 디코딩, Parallel@4(청색)는 4-way 병렬 디코딩, Suppress(보라)는 low-confidence 토큰 억제, CFG(주황)는 Classifier-Free Guidance를 적용한 결과다. CFG는 HumanEval, MBPP 등 코드 생성 벤치마크에서 특히 강한 성능 향상을 보이며, Suppress 전략은 전반적으로 안정적인 성능을 유지한다.*

Dream-Instruct 모델에서도 유사한 패턴이 관찰되며, 특히 Suppress 전략이 코드 생성 및 수학 벤치마크에서 안정적인 성능을 보인다.

![Dream-Instruct 모델에서의 추론 전략별 벤치마크 성능 레이더 차트](figures/fig_11_2.png)
*Figure 5-1: Dream-Instruct 모델에서 추론 전략별 벤치마크 성능 비교. Baseline(녹색) 대비 Parallel@4(청색)는 속도를 높이지만 일부 벤치마크에서 성능 하락이 있으며, Temp@0(보라)은 결정론적 생성으로 GSM8K와 Minerva에서 강한 성능을 보인다. (Zhou et al., 2026)*

Classifier-Free Guidance(CFG)는 확산 이미지 모델에서 입증된 기법으로, 조건부 생성과 비조건부 생성의 차이를 증폭시켜 생성 품질을 높인다. dLLM에서는 다음과 같이 적용된다:

$$\tilde{p}_\theta(x_0 \mid x_t, t, c) = (1 + \lambda) \cdot p_\theta(x_0 \mid x_t, t, c) - \lambda \cdot p_\theta(x_0 \mid x_t, t)$$

여기서 $c$는 조건(프롬프트)이고 $\lambda$는 guidance scale이다. 이 기법이 텍스트 확산 모델에서도 유효하다는 것은 중요한 발견이다.

### 생성 품질 (Human Evaluation)

500개의 오픈엔디드 생성 태스크에서 인간 평가:

| 비교 쌍 | dLLM 선호율 | Tie | 상대 선호율 |
|--------|-----------|-----|----------|
| dLLM vs MDLM | 64.2% | 12.1% | 73.2% |
| dLLM vs D3PM | 71.5% | 8.3% | 78.1% |
| dLLM vs LLaMA 3B | 44.8% | 15.6% | 53.2% |

### 추론 속도

| 모델 | 토큰/초 (A100) | 스텝 수 |
|------|--------------|-------|
| LLaMA 3B (AR) | 145 | T (순차) |
| dLLM 3B (10 steps) | 312 | 10 |
| dLLM 3B (25 steps) | 189 | 25 |
| dLLM 3B (50 steps) | 98 | 50 |

10 스텝 설정에서 dLLM은 AR 모델 대비 2.1배 빠른 생성 속도를 달성한다. 이는 병렬 생성의 구조적 이점에서 비롯된다.

### 파인튜닝 및 추론 능력

기존 사전학습된 확산 언어 모델을 추론(reasoning) 태스크에 파인튜닝할 수 있는지도 중요한 연구 질문이다. 아래 그림은 LLaDA와 Dream 모델을 수학/코드 추론 데이터로 파인튜닝한 학습 곡선을 보여준다.

![확산 언어 모델의 추론 파인튜닝 학습 곡선](figures/fig_14.png)
*Figure 6. 오픈소스 확산 언어 모델(LLaDA-Base/Instruct, Dream-Base/Instruct)을 추론 태스크에 파인튜닝할 때의 Train loss(좌)와 Eval loss(우). Dream 계열 모델은 안정적으로 학습이 수렴하는 반면, LLaDA 계열은 학습 손실의 변동이 크다. 특히 LLaDA-Instruct의 Eval loss가 초반에 급증 후 감소하는 패턴은 Instruct 튜닝과 추론 파인튜닝 간의 분포 차이를 시사한다.*

이 결과는 확산 언어 모델의 파인튜닝 가능성을 보여주면서도, 모델 아키텍처와 사전학습 방식에 따라 파인튜닝 안정성이 크게 달라질 수 있음을 시사한다. AR 모델에서는 RLHF와 SFT가 이미 성숙한 기술이지만, 확산 LM에서는 아직 최적의 파인튜닝 전략이 확립되지 않았다.

흥미로운 실험으로, 기존 BERT 모델을 채팅용으로 파인튜닝하는 시도도 보고된다. 이는 마스크 언어 모델이 확산 생성 모델로 전환될 수 있는지를 검증한다.

![BERT 모델을 채팅용으로 파인튜닝할 때의 학습 곡선](figures/fig_15.png)
*Figure 7: ModernBERT(base, large)를 채팅 데이터로 파인튜닝할 때의 Train loss(좌)와 Eval loss(우). 두 모델 모두 안정적으로 수렴하며, 이는 BERT 계열 마스크 모델이 생성 태스크로 전환 가능함을 보여준다. (Zhou et al., 2026)*

더 나아가, 기존 AR 모델을 확산 언어 모델로 변환하는 실험도 수행되었다.

![AR 언어 모델을 확산 언어 모델로 변환하는 파인튜닝 학습 곡선](figures/fig_16.png)
*Figure 8: Qwen 기반 AR 모델을 확산 LM(bd3lm, mdlm)으로 변환하는 파인튜닝 학습 곡선. bdlm 방식이 mdlm보다 더 빠르게 수렴하며, Eval loss도 더 낮은 수준에 도달한다. 이는 기존 AR 모델의 사전학습 지식을 확산 모델로 전이할 수 있는 가능성을 시사한다. (Zhou et al., 2026)*

## 의의 및 한계

### 의의

- **단순성**: 복잡한 ELBO 없이 단일 손실 함수로 마스크 확산 학습. 기존 D3PM이 $T$개의 전이 행렬을 관리해야 했던 것과 대조적으로, dLLM은 시간 $t$만으로 전체 과정을 매개변수화한다.
- **시간 인식 디노이징**: 시간 조건화가 확산 LM 성능의 핵심임을 체계적으로 입증. 시간 임베딩을 제거하면 성능이 급격히 하락한다는 ablation 결과는 이 주장을 강력히 뒷받침한다.
- **AR 경쟁력**: 최초로 확산 LM이 동급 AR 모델과 실질적으로 경쟁하는 결과 제시. 3B 모델이 LLaMA 3B와 동등한 벤치마크 점수를 달성했다.
- **병렬 생성**: 순차 생성의 병목 없이 고품질 텍스트 생성 가능. 10 스텝 설정에서 AR 대비 2배 이상의 처리량을 보인다.
- **이론적 기여**: 마스크 확산과 흡수 확산의 통합 프레임워크 정립. 두 접근법이 동일한 수학적 구조의 특수 사례임을 증명함으로써, 향후 연구의 이론적 기반을 마련했다.

### 한계

- **롱폼 일관성**: 긴 텍스트 생성 시 AR 모델에 비해 전체적 일관성이 떨어지는 경향. 양방향 어텐션이 지역적 일관성에는 유리하지만, 전체적 내러티브 구조를 유지하는 데는 좌-우 순차 생성이 여전히 유리하다.
- **Conditional 생성**: 프롬프트 조건부 생성 품질이 AR 대비 다소 낮음 (채팅, 지시 이행). CFG로 부분적 개선이 가능하지만, AR 모델의 in-context learning 능력에는 미치지 못한다.
- **추론 비용**: 최고 품질을 위해서는 50+ 스텝이 필요하여 짧은 AR 생성보다 느릴 수 있음. 스텝 수와 품질 사이의 trade-off가 존재한다.
- **긴 컨텍스트**: 포지셔널 인코딩의 설계 상 긴 시퀀스 처리 시 성능 저하
- **명령 조정(Instruction Tuning)**: RLHF 등 정렬 기술의 확산 LM 적용은 아직 초기 단계. 앞선 파인튜닝 실험 결과에서 보듯이, 모델에 따라 학습 안정성에 차이가 있다.

### 향후 연구 방향

dLLM은 텍스트 확산의 가능성을 실용적 수준으로 끌어올린 중요한 이정표다. 앞으로의 연구 방향은:

1. 더 큰 규모(10B+)로의 확장 및 성능 검증
2. 인스트럭션 파인튜닝 및 RLHF 적용
3. 다모달(멀티모달) 확산 언어 모델과의 결합
4. 더 효율적인 추론 알고리즘 (adaptive step 등)

## 코드 예제

### 순방향 과정 (Forward Process)

```python
import torch
import torch.nn.functional as F


def forward_process(x0: torch.Tensor, t: float, mask_token_id: int) -> torch.Tensor:
    """
    dLLM 순방향 과정: 시간 t에서 토큰 x0에 마스크 적용.

    Args:
        x0: 원본 토큰 시퀀스 [batch, seq_len]
        t: 노이즈 시간 [0, 1]
        mask_token_id: [MASK] 토큰 ID

    Returns:
        x_t: 마스크가 적용된 토큰 시퀀스 [batch, seq_len]
    """
    # 코사인 노이즈 스케줄: alpha_t = 마스크 확률
    alpha_t = 1.0 - (torch.cos(torch.tensor(t * torch.pi / 2)) ** 2).item()

    # 각 토큰 독립적으로 마스킹 여부 결정
    mask = torch.bernoulli(torch.full_like(x0, alpha_t, dtype=torch.float))
    x_t = torch.where(mask.bool(), torch.full_like(x0, mask_token_id), x0)
    return x_t


def cosine_schedule(t: torch.Tensor) -> torch.Tensor:
    """코사인 노이즈 스케줄 alpha_t 계산."""
    return 1.0 - torch.cos(t * torch.pi / 2) ** 2
```

### dLLM 모델 정의

```python
import torch
import torch.nn as nn
import math


class SinusoidalTimeEmbedding(nn.Module):
    """시간 t를 사인파 임베딩으로 변환."""

    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.SiLU(),
            nn.Linear(dim * 4, dim),
        )

    def forward(self, t: torch.Tensor) -> torch.Tensor:
        half = self.dim // 2
        freqs = torch.exp(
            -math.log(10000) * torch.arange(half, device=t.device) / half
        )
        x = t[:, None] * freqs[None, :]  # [B, half]
        x = torch.cat([x.sin(), x.cos()], dim=-1)  # [B, dim]
        return self.mlp(x)


class AdaLN(nn.Module):
    """Adaptive LayerNorm ( 시간 임베딩으로 scale/shift 조정."""

    def __init__(self, d_model: int, time_dim: int):
        super().__init__()
        self.norm = nn.LayerNorm(d_model, elementwise_affine=False)
        self.proj = nn.Linear(time_dim, d_model * 2)  # gamma, beta

    def forward(self, x: torch.Tensor, t_emb: torch.Tensor) -> torch.Tensor:
        gamma_beta = self.proj(t_emb).unsqueeze(1)  # [B, 1, 2*D]
        gamma, beta = gamma_beta.chunk(2, dim=-1)   # [B, 1, D] each
        return self.norm(x) * (1 + gamma) + beta


class DLLMTransformerLayer(nn.Module):
    """시간 조건부 양방향 트랜스포머 레이어."""

    def __init__(self, d_model: int, nhead: int, time_dim: int, dropout: float = 0.1):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(
            d_model, nhead, dropout=dropout, batch_first=True
        )
        self.ff = nn.Sequential(
            nn.Linear(d_model, d_model * 4),
            nn.GELU(),
            nn.Linear(d_model * 4, d_model),
            nn.Dropout(dropout),
        )
        self.adaln1 = AdaLN(d_model, time_dim)
        self.adaln2 = AdaLN(d_model, time_dim)

    def forward(
        self, x: torch.Tensor, t_emb: torch.Tensor
    ) -> torch.Tensor:
        # AdaLN 후 양방향 Self-Attention (causal mask 없음)
        h = self.adaln1(x, t_emb)
        attn_out, _ = self.self_attn(h, h, h)  # 완전 양방향 어텐션
        x = x + attn_out

        # AdaLN 후 Feed-Forward
        h = self.adaln2(x, t_emb)
        x = x + self.ff(h)
        return x


class DLLM(nn.Module):
    """
    dLLM: Simple Diffusion Language Model.
    시간 조건부 양방향 트랜스포머로 마스크된 토큰 복원.
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int = 768,
        nhead: int = 12,
        num_layers: int = 12,
        max_len: int = 1024,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.token_embed = nn.Embedding(vocab_size, d_model)
        self.pos_embed = nn.Embedding(max_len, d_model)
        self.time_embed = SinusoidalTimeEmbedding(d_model)

        self.layers = nn.ModuleList([
            DLLMTransformerLayer(d_model, nhead, d_model, dropout)
            for _ in range(num_layers)
        ])
        self.norm = nn.LayerNorm(d_model)
        self.output_head = nn.Linear(d_model, vocab_size, bias=False)

        # 가중치 공유 (GPT 스타일)
        self.output_head.weight = self.token_embed.weight

    def forward(
        self, x_t: torch.Tensor, t: torch.Tensor
    ) -> torch.Tensor:
        """
        x_t: 마스크된 토큰 시퀀스 [B, L]
        t: 노이즈 시간 [B] (값 범위: [0, 1])
        returns: 로짓 [B, L, V]
        """
        B, L = x_t.shape
        positions = torch.arange(L, device=x_t.device).unsqueeze(0).expand(B, -1)

        h = self.token_embed(x_t) + self.pos_embed(positions)
        t_emb = self.time_embed(t)  # [B, D]

        for layer in self.layers:
            h = layer(h, t_emb)

        h = self.norm(h)
        return self.output_head(h)  # [B, L, V]
```

### 학습 루프

```python
import torch
import torch.nn.functional as F

MASK_TOKEN_ID = 0  # [MASK] = 0으로 가정


def dllm_loss(
    model: DLLM,
    x0: torch.Tensor,
    mask_token_id: int = MASK_TOKEN_ID,
) -> torch.Tensor:
    """
    dLLM 학습 손실.
    마스크된 위치의 교차 엔트로피만 최소화.
    """
    B, L = x0.shape
    device = x0.device

    # 1) 시간 t를 균등 분포에서 샘플링
    t = torch.rand(B, device=device)  # [B]

    # 2) 순방향 과정: x0 -> x_t
    alpha_t = cosine_schedule(t)  # [B]
    mask_prob = alpha_t[:, None].expand(B, L)  # [B, L]
    is_masked = torch.bernoulli(mask_prob).bool()  # [B, L]
    x_t = torch.where(is_masked, torch.full_like(x0, mask_token_id), x0)

    # 3) 역방향 예측: p_theta(x0 | x_t, t)
    logits = model(x_t, t)  # [B, L, V]

    # 4) 마스크된 위치에서만 손실 계산
    if is_masked.sum() == 0:
        return torch.tensor(0.0, requires_grad=True, device=device)

    loss = F.cross_entropy(
        logits[is_masked],  # [num_masked, V]
        x0[is_masked],      # [num_masked]
        reduction="mean",
    )
    return loss


def train_dllm(
    model: DLLM,
    dataloader,
    optimizer,
    num_epochs: int = 10,
    device: str = "cuda",
):
    """dLLM 학습 루프."""
    model.train()
    for epoch in range(num_epochs):
        total_loss = 0.0
        for batch in dataloader:
            x0 = batch["input_ids"].to(device)

            loss = dllm_loss(model, x0)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            optimizer.zero_grad()

            total_loss += loss.item()

        print(f"Epoch {epoch+1}: loss={total_loss / len(dataloader):.4f}")
```

### 텍스트 생성 (Iterative Denoising)

```python
@torch.no_grad()
def generate(
    model: DLLM,
    seq_len: int,
    num_steps: int = 25,
    mask_token_id: int = MASK_TOKEN_ID,
    temperature: float = 1.0,
    device: str = "cuda",
) -> torch.Tensor:
    """
    dLLM 텍스트 생성: 전체 마스크 -> 순차 디노이징.

    Args:
        model: 학습된 dLLM
        seq_len: 생성할 시퀀스 길이
        num_steps: 디노이징 스텝 수 (10-50)
        temperature: 샘플링 온도

    Returns:
        generated: 생성된 토큰 시퀀스 [1, seq_len]
    """
    model.eval()

    # 전체를 마스크로 초기화 (t=1)
    x = torch.full((1, seq_len), mask_token_id, dtype=torch.long, device=device)

    # t: 1 -> 0 방향으로 디노이징
    timesteps = torch.linspace(1.0, 0.0, num_steps + 1, device=device)

    for i in range(num_steps):
        t_curr = timesteps[i]
        t_next = timesteps[i + 1]
        t_tensor = t_curr.unsqueeze(0)  # [1]

        # 현재 노이즈 수준에서 원본 예측
        logits = model(x, t_tensor) / temperature  # [1, L, V]
        probs = F.softmax(logits, dim=-1)          # [1, L, V]

        # 마스크된 위치만 업데이트
        is_masked = (x == mask_token_id)           # [1, L]
        if not is_masked.any():
            break

        # 예측 토큰 샘플링
        sampled = torch.multinomial(
            probs.view(-1, probs.shape[-1]), num_samples=1
        ).view(1, seq_len)  # [1, L]

        # t_next에서의 마스크 확률 계산
        alpha_next = cosine_schedule(t_next.unsqueeze(0))  # [1]
        # 신뢰도가 높은 토큰부터 마스크 해제 (mask 일부 유지)
        confidence = probs.max(dim=-1).values  # [1, L]
        threshold = torch.quantile(
            confidence[is_masked], 1.0 - alpha_next.item()
        ) if is_masked.sum() > 1 else 0.0

        # 신뢰도 >= threshold인 위치의 마스크 해제
        should_unmask = is_masked & (confidence >= threshold)
        x = torch.where(should_unmask, sampled, x)

    return x
```

## 관련 문서

- [[mdlm|Simple and Effective Masked Diffusion Language Models (MDLM)]] ) dLLM의 직접적 전작
- [[llada|Large Language Diffusion with mAsking (LLaDA)]] ( 대규모 마스크 확산 LM
- [[d3pm|Structured Denoising Diffusion Models in Discrete State-Spaces (D3PM)]] ) 이산 확산의 이론적 기반
- [[sedd|Score Entropy Discrete Diffusion (SEDD)]] ( 이산 스코어 매칭 기반 접근
- [[bd3lm|Block Diffusion (BD3LM)]] ) AR과 확산의 블록 단위 혼합
