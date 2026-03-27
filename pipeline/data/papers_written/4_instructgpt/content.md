## 개요

InstructGPT는 OpenAI가 2022년 NeurIPS에 발표한 논문으로, 대형 언어 모델(LLM)이 사용자의 의도에 맞게 동작하도록 **인간 피드백 강화학습(RLHF, Reinforcement Learning from Human Feedback)**을 적용한 연구다. GPT-3는 강력한 언어 생성 능력을 갖추고 있지만, 사용자가 원하는 방향으로 동작하지 않는 경우가 많았다. 유해한 내용을 생성하거나, 지시를 무시하거나, 근거 없는 내용을 사실처럼 제시하는 문제가 있었다. InstructGPT는 이 **정렬(alignment) 문제**를 RLHF 파이프라인으로 해결한다.

놀라운 결과는 규모의 역설이다. 1.3B 파라미터의 InstructGPT가 175B 파라미터의 GPT-3보다 사람 평가자들로부터 더 높은 선호도를 받았다. 이는 모델 크기보다 훈련 방식이 실용적 성능에 더 중요할 수 있음을 시사한다. 2022년 발표 이후 약 17,000회 이상 인용되며, AI 정렬 분야에서 가장 영향력 있는 논문 중 하나로 자리잡았다.

논문의 주요 기여를 정리하면 다음과 같다.

- 인간 선호도를 반영한 3단계 RLHF 파이프라인(SFT -> RM -> PPO)을 대규모 LLM에 최초로 적용
- 1.3B 파라미터의 정렬된 모델이 175B 베이스 모델보다 사람 평가에서 우수함을 입증
- 정렬 세금(alignment tax) 개념을 정의하고 이를 완화하는 사전학습 혼합(pretraining mix) 기법을 제안
- 유용성, 정직성, 무해성의 세 축으로 LLM 정렬 품질을 체계적으로 평가하는 프레임워크를 확립

## 배경 및 문제

### 언어 모델의 미정렬 문제

GPT-3와 같은 대형 언어 모델은 방대한 인터넷 텍스트로 사전 학습된다. 이 과정의 목적은 **다음 토큰 예측(next token prediction)**이며, 사용자를 돕는 것이 아니다. 학습 목표 자체가 "인터넷 텍스트의 통계적 패턴 학습"이기 때문에, 모델이 생성하는 텍스트가 인간의 기대와 다른 방향으로 흘러갈 수 있다.

사전학습의 목적함수를 수식으로 표현하면 다음과 같다.

$$\mathcal{L}_{pretrain} = -\sum_{t=1}^{T} \log P(x_t | x_1, \ldots, x_{t-1}; \theta)$$

이 목적함수는 인터넷 텍스트의 분포를 모방하는 것이 목표이므로, "좋은 응답"과 "나쁜 응답"을 구분하지 않는다. 유해한 콘텐츠, 편향된 발언, 허위 정보가 포함된 텍스트도 학습 데이터에 존재하기 때문에, 모델은 이러한 패턴도 동일하게 학습하게 된다.

결과적으로 모델은 다음과 같은 미정렬 행동을 보인다.

- **지시 무시**: 프롬프트를 질문이나 지시가 아닌 텍스트 완성의 시작점으로 취급하여 단순히 이어 쓰려 함
- **유해성**: 인터넷 텍스트에 포함된 편향, 혐오 표현, 유해 콘텐츠를 그대로 재생산
- **환각(Hallucination)**: 사실이 아닌 내용을 자신감 있게 생성하며, 출처를 날조하기도 함
- **과도한 순응**: 사용자의 표면적 요청을 문자 그대로 따르면서 잠재적 위험을 무시

이를 **미정렬(misalignment)** 문제라 하며, 단순히 모델을 크게 만드는 것으로는 해결되지 않는다. 실제로 GPT-3의 175B 파라미터도 이 문제를 해결하지 못했다. 오히려 더 큰 모델이 더 설득력 있게 거짓 정보를 생성하는 경향마저 관찰되었다.

### 정렬 문제의 공식 정의

논문에서 정의하는 정렬(alignment)의 목표는 모델의 행동이 **사용자의 의도(user intent)**와 일치하도록 만드는 것이다. 이때 의도는 단순히 사용자가 명시한 지시뿐 아니라, 암묵적인 기대(예: 안전하고 정직한 응답)까지 포함한다. 논문은 이를 세 가지 축으로 분해한다.

| 정렬 축 | 정의 | 미정렬 시 문제 |
|---------|------|---------------|
| 유용성(Helpful) | 사용자의 태스크를 효과적으로 수행 | 관련 없는 응답, 지시 무시 |
| 정직성(Honest) | 사실에 기반하고 불확실성을 인정 | 환각, 거짓 정보 생성 |
| 무해성(Harmless) | 위험하거나 불쾌한 내용을 생성하지 않음 | 유해 콘텐츠, 편향 재생산 |

이 세 축은 때때로 상충할 수 있다. 예를 들어 사용자가 유해한 내용을 요청하면 유용성과 무해성이 충돌한다. InstructGPT는 이러한 상충 관계에서 무해성에 우선순위를 두도록 설계되었다.

### 기존 접근법의 한계

지도 학습(SFT)만으로 파인튜닝하면 어느 정도 개선되지만, 다양한 지시와 상황에 일반화하기 어렵다. 사람이 원하는 응답의 모든 경우를 레이블링하기에는 비용이 너무 크고, 무엇이 "좋은 응답"인지에 대한 정의도 복잡하다. 예를 들어, "파이썬으로 정렬 알고리즘을 설명해줘"라는 요청에 대해 좋은 응답은 사용자의 수준, 맥락, 선호도에 따라 매우 다양하다.

또한 SFT는 "이상적인 응답을 직접 작성"해야 하므로 레이블링 비용이 높다. 반면 두 응답 중 어느 것이 더 나은지 **비교 판단**하는 것은 직접 작성보다 훨씬 쉽고 빠르다. InstructGPT는 이 통찰을 활용하여 비교 데이터에서 보상 신호를 추출하는 전략을 취한다.

### RLHF의 이론적 배경

RLHF는 인간의 선호도를 보상 신호로 변환하여 강화학습에 활용하는 패러다임이다. 이 접근법의 이론적 기반은 Christiano et al. (2017)의 "Deep reinforcement learning from human preferences"에서 시작되었으며, Stiennon et al. (2020)의 요약 태스크 연구에서 언어 모델에 처음 적용되었다. InstructGPT는 이를 범용 지시 이행(instruction following) 태스크로 확장한 것이다.

RLHF의 핵심 통찰은 다음과 같다. 인간이 "최적의 응답"을 직접 정의하는 것은 어렵지만, 두 응답을 비교하여 선호도를 표현하는 것은 상대적으로 쉽다. 이 비교 데이터로부터 암묵적인 보상 함수(implicit reward function)를 학습하고, 이를 강화학습의 보상 신호로 사용하면 모델을 인간의 선호 방향으로 최적화할 수 있다.

## 핵심 아이디어 (RLHF)

InstructGPT의 핵심은 세 단계로 구성된 **RLHF 파이프라인**이다. 이 파이프라인의 목표는 인간의 선호도를 수학적 보상 함수로 모델링하고, 이를 최적화하여 모델의 출력을 정렬하는 것이다. 아래 그림은 전체 파이프라인의 구조를 보여준다.

![InstructGPT RLHF 3단계 학습 파이프라인 개요도](figures/fig_2.png)
*Figure 2: InstructGPT의 RLHF 3단계 파이프라인 ( Step 1에서는 레이블러가 작성한 시연 데이터로 SFT를 수행하고, Step 2에서는 모델 출력에 대한 비교 순위 데이터로 보상 모델(RM)을 학습하며, Step 3에서는 보상 모델의 점수를 신호로 삼아 PPO 알고리즘으로 정책을 최적화한다. (Ouyang et al., 2022)*

### 1단계: 지도 파인튜닝 (SFT)

먼저 OpenAI의 레이블러(labeler)팀이 다양한 프롬프트에 대해 이상적인 응답을 직접 작성한다. 이 데이터로 GPT-3를 지도 학습 방식으로 파인튜닝하여 SFT 모델을 만든다. SFT 단계의 목적은 모델이 "프롬프트를 단순 완성"하는 것이 아니라 "지시에 응답"하는 형식을 학습하게 만드는 것이다.

$$\mathcal{L}_{SFT} = -\sum_{t} \log P(y_t | x, y_{<t})$$

여기서 $x$는 프롬프트, $y_t$는 레이블러가 작성한 응답의 $t$번째 토큰이다. 약 13,000개의 프롬프트-응답 쌍을 사용했으며, 이 데이터만으로도 GPT-3 대비 상당한 개선을 보였다.

SFT 학습 시 주요 하이퍼파라미터는 다음과 같다.

- 학습률(learning rate): cosine annealing 스케줄 사용
- 에폭(epoch): 16 에폭 학습 (검증 손실 기준 최적 체크포인트 선택)
- 드롭아웃: 잔차 연결에 드롭아웃 적용

논문에서는 SFT만으로도 상당한 성능 향상이 있었지만, 다양한 프롬프트에 대한 일반화 능력이 부족하다는 점을 지적했다. 이는 이후 RM과 PPO 단계를 통해 보완된다.

### 2단계: 보상 모델 훈련 (RM)

SFT 모델이 생성한 여러 응답에 대해 레이블러가 **선호도 순위**를 매긴다. 예를 들어 같은 프롬프트에 대한 응답 A, B, C, D를 순위 매기면, 이 쌍별(pairwise) 비교 데이터로 **보상 모델(Reward Model)**을 훈련한다. 보상 모델은 6B 파라미터의 GPT-3를 기반으로 하며, 최종 임베딩 레이어 위에 스칼라 값을 출력하는 선형 헤드를 추가한 구조이다.

보상 모델의 손실 함수는 Bradley-Terry 선호 모델에 기반한다. 두 응답 $y_w$(선호)와 $y_l$(비선호)에 대해, 선호 응답의 보상이 더 높을 확률을 최대화한다.

$$P(y_w \succ y_l) = \sigma(r_\theta(x, y_w) - r_\theta(x, y_l))$$

이를 음의 로그 우도로 변환하면 다음 손실 함수를 얻는다.

$$\mathcal{L}_{RM}(\theta) = -\mathbb{E}_{(x,y_w,y_l) \sim D} \left[ \log \sigma(r_\theta(x, y_w) - r_\theta(x, y_l)) \right]$$

여기서 $r_\theta$는 보상 모델의 스칼라 출력이다. 하나의 프롬프트에 대해 $K$개의 응답이 있으면 $\binom{K}{2}$개의 비교 쌍을 만들 수 있다. 논문에서는 $K=4$에서 $K=9$ 범위의 값을 사용했으며, 이를 통해 약 33,000개의 프롬프트에서 수십만 개의 비교 쌍을 생성했다.

보상 모델 크기 선택에 대한 중요한 관찰이 있다. 논문은 175B가 아닌 6B 모델을 보상 모델로 사용했는데, 175B 보상 모델은 학습이 불안정하여 PPO 정책 최적화 과정에서 보상 값이 발산하는 현상이 관찰되었기 때문이다. 이는 보상 모델의 과적합(overfitting)이 RLHF 파이프라인 전체의 안정성에 직접적으로 영향을 미친다는 교훈을 남겼다.

### 3단계: PPO로 강화학습 (RL)

보상 모델을 피드백 신호로 삼아 **PPO(Proximal Policy Optimization)** 알고리즘으로 SFT 모델을 추가로 최적화한다. 이 단계의 전체 목적함수는 다음과 같다.

$$\text{objective}(\phi) = \mathbb{E}_{(x,y) \sim \pi_\phi} \left[ r_\theta(x,y) - \beta \log \frac{\pi_\phi(y|x)}{\pi_{SFT}(y|x)} \right] + \gamma \mathcal{L}_{pretraining}$$

각 항의 역할을 자세히 살펴보겠다.

- $r_\theta(x,y)$: 보상 모델이 출력하는 스칼라 보상. 높을수록 인간이 선호하는 응답에 가깝다.
- $\beta \log \frac{\pi_\phi(y|x)}{\pi_{SFT}(y|x)}$: **KL 페널티** 항. SFT 모델에서 너무 멀리 벗어나지 않도록 조절한다. 이 항이 없으면 모델이 보상 모델의 허점을 공략하는 "보상 해킹(reward hacking)"에 빠질 수 있다. $\beta$ 값은 학습 중 KL 다이버전스의 목표값에 따라 동적으로 조절된다.
- $\gamma \mathcal{L}_{pretraining}$: **사전학습 혼합(pretraining mix)** 항. RLHF 후에도 모델의 일반적인 NLP 능력이 유지되도록 보장하여 정렬 세금(alignment tax)을 완화한다.

PPO 알고리즘은 정책 업데이트의 크기를 제한하여 학습 안정성을 보장한다. 구체적으로, 중요도 비율(importance ratio)을 클리핑하여 한 번의 업데이트에서 정책이 급격히 변하는 것을 방지한다.

$$L^{CLIP}(\theta) = \mathbb{E}_t \left[ \min\left( r_t(\theta) \hat{A}_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) \hat{A}_t \right) \right]$$

여기서 $r_t(\theta) = \frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{old}}(a_t|s_t)}$는 새 정책과 이전 정책의 확률 비율이고, $\hat{A}_t$는 **일반화 어드밴티지 추정(GAE, Generalized Advantage Estimation)**으로 계산된다.

$$\hat{A}_t^{GAE} = \sum_{l=0}^{\infty} (\gamma \lambda)^l \delta_{t+l}, \quad \delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)$$

GAE에서 $\lambda$는 편향-분산 트레이드오프를 조절하는 파라미터이며, $\delta_t$는 시간차(TD) 오차이다. $\lambda = 0$이면 단일 스텝 TD 추정, $\lambda = 1$이면 몬테카를로 추정에 해당한다.

## 방법론 (SFT -> Reward Model -> PPO Pipeline)

### 데이터 수집 파이프라인

InstructGPT의 데이터 수집은 체계적인 파이프라인을 따른다. 프롬프트 소스는 크게 두 가지이다.

1. **API 프롬프트**: OpenAI Playground에서 실제 사용자들이 입력한 프롬프트. 개인정보를 제거한 후 사용.
2. **레이블러 작성 프롬프트**: 다양한 태스크 유형을 커버하기 위해 레이블러가 직접 작성한 프롬프트.

데이터 수집에서 핵심적인 역할을 한 것은 레이블러의 순위 평가 작업이다. 아래 그림은 레이블러가 여러 모델 출력을 비교하여 순위를 매기는 실제 인터페이스를 보여준다.

![레이블러가 모델 출력을 순위별로 평가하는 랭킹 인터페이스](figures/fig_14_2.png)
*Figure 14: 레이블러 랭킹 인터페이스 ) 여러 모델 출력을 Best-to-Worst 순위로 평가하며, 각 응답에 Likert 점수와 유해성 체크리스트를 함께 기록한다. 이 비교 데이터가 보상 모델 학습의 핵심 입력이 된다. (Ouyang et al., 2022)*

이 인터페이스를 통해 수집된 비교 데이터는 보상 모델이 "무엇이 좋은 응답인지"를 학습하는 근거가 된다.

프롬프트 유형별 분포는 다음과 같다.

| 프롬프트 유형 | 비율 | 예시 |
|-------------|------|------|
| 생성(Generation) | 45.6% | "여행 계획을 세워줘" |
| 개방형 QA | 12.4% | "양자 컴퓨터란?" |
| 폐쇄형 QA | 2.6% | "프랑스 수도는?" |
| 브레인스토밍 | 11.2% | "창업 아이디어를 제안해줘" |
| 요약 | 4.2% | "이 기사를 요약해줘" |
| 분류 | 3.5% | "이 리뷰의 감성은?" |
| 추출 | 1.9% | "주요 키워드를 추출해줘" |
| 기타 | 18.6% | 코드 작성, 대화, 수정 등 |

### 레이블러 팀 구성

약 40명의 계약직 레이블러가 데이터 제작에 참여했다. OpenAI는 스크리닝 테스트를 통해 연구진의 선호도와 높은 상관관계(inter-annotator agreement)를 보이는 레이블러를 선별했다. 선별 기준에는 민감한 주제(정치, 종교 등)에 대한 판단의 일관성도 포함되었다.

레이블러에게 제공된 가이드라인의 핵심 원칙은 다음과 같다.

- 유용한 응답을 우선시하되, 유해한 내용은 생성하지 않을 것
- 사실 여부가 불확실한 경우 불확실성을 명시할 것
- 개인정보, 폭력적 내용, 차별적 표현을 피할 것

레이블러 간 일관성(inter-annotator agreement)은 약 73%로, 이는 주관적 판단이 포함된 태스크치고는 양호한 수준이다. 그러나 이것이 "보편적 인간 선호도"를 대표하는지에 대해서는 논쟁이 있다.

### 데이터 규모 요약

| 학습 단계 | 데이터 규모 | 데이터 유형 |
|----------|-----------|------------|
| SFT | ~13,000개 | 프롬프트-응답 쌍 |
| RM | ~33,000개 프롬프트 | 순위 비교 (K=4~9) |
| PPO | ~31,000개 프롬프트 | RM 보상 신호 기반 |

### 평가 지표

평가는 주로 **사람 평가자**가 직접 두 응답을 비교하는 방식으로 진행된다. 핵심 평가 차원은 다음과 같다.

1. **유용성(Helpfulness)**: 사용자의 의도를 얼마나 잘 충족하는가
2. **정직성(Truthfulness)**: 사실에 근거한 응답인가
3. **무해성(Harmlessness)**: 위험하거나 불쾌한 내용이 없는가

추가로 자동화된 평가 벤치마크도 사용되었다.

- **TruthfulQA**: 모델의 정직성 평가 (817개의 함정 질문)
- **RealToxicityPrompts**: 독성 콘텐츠 생성 경향 측정
- **WinoBias, BBQ**: 편향 관련 벤치마크
- **SQuADv2, HellaSwag, WMT 등**: 기존 NLP 벤치마크 (정렬 세금 측정용)

### 모델 변형

논문에서 비교한 모델 변형은 다음과 같다.

- **GPT-3 (175B)**: 베이스라인 (사전학습만 수행)
- **GPT-3 prompted**: few-shot 프롬프트로 지시를 따르도록 유도한 모델
- **SFT (1.3B, 6B)**: 지도 파인튜닝만 적용
- **InstructGPT (1.3B, 6B, 175B)**: 전체 RLHF 파이프라인 적용
- **PPO-ptx**: 사전학습 혼합 항을 포함한 PPO (정렬 세금 완화)

## 실험 결과 (Human Evaluation Tables)

### 사람 선호도 비교 (핵심 결과)

InstructGPT의 가장 핵심적인 실험 결과는 모델 크기별 사람 선호도 비교이다. 아래 그림은 1.3B부터 175B까지의 모델 크기에서 SFT 175B 대비 승률을 보여준다.

![모델 크기별 SFT 175B 대비 사람 선호 승률](figures/fig_1.png)
*Figure 1: 모델 크기(1.3B~175B)에 따른 SFT 175B 대비 사람 선호 승률 ( PPO-ptx와 PPO 모델이 전 규모에서 SFT 및 GPT 베이스라인을 크게 앞서며, 특히 1.3B InstructGPT가 175B GPT-3보다 높은 선호율을 기록한다. (Ouyang et al., 2022)*

이 결과는 모델 크기보다 학습 방식이 실용적 성능에 더 결정적임을 입증한 핵심 증거이다.

| 모델 | 파라미터 수 | GPT-3 대비 선호율 | Likert 점수 (1-7) |
|------|-----------|------------------|-------------------|
| GPT-3 (175B) | 175B | 기준선 | 3.9 |
| GPT-3 prompted | 175B | ~55% | 4.3 |
| SFT (1.3B) | 1.3B | ~50% | 4.0 |
| SFT (6B) | 6B | ~55% | 4.3 |
| InstructGPT 1.3B (PPO-ptx) | 1.3B | **85%** | 5.8 |
| InstructGPT 6B (PPO-ptx) | 6B | **86%** | 5.9 |
| InstructGPT 175B (PPO-ptx) | 175B | **90%+** | 6.2 |

InstructGPT와 다른 기존 모델들의 유용성을 Likert 척도로 비교한 결과도 일관된 경향을 보여준다.

![GPT, SFT, PPO-ptx, FLAN, T0 등 모델별 유용성 Likert 점수 비교 막대 그래프](figures/fig_7.png)
*Figure 7: 모델별 유용성 Likert 점수(1-7) 비교 ) PPO-ptx가 약 5점으로 GPT(~2.5점) 대비 압도적으로 높은 유용성을 기록하며, FLAN이나 T0 같은 기존 지시 튜닝 모델보다도 우수하다. (Ouyang et al., 2022)*

PPO-ptx는 기존 지시 튜닝 모델(FLAN, T0)과 비교해서도 확연한 차이를 보이며, RLHF 파이프라인의 효과가 단순 지도 학습 기반 지시 튜닝을 크게 넘어섬을 확인할 수 있다.

**1.3B InstructGPT가 175B GPT-3보다 높은 선호도**를 기록했다. 이는 정렬 훈련의 효과가 모델 크기를 압도할 수 있음을 보여준다. 이 결과는 AI 커뮤니티에 큰 반향을 일으켰는데, 100배 이상 작은 모델이 더 큰 모델을 이긴다는 것은 순전히 스케일링에 의존하던 기존 패러다임에 대한 도전이었기 때문이다.

이 결과를 더 세분화하여 살펴보면, GPT 배포 프롬프트와 Instruct 배포 프롬프트 모두에서 PPO 계열 모델이 일관된 우위를 보임을 확인할 수 있다.

![GPT 배포와 Instruct 배포에서의 모델별 승률 비교 차트](figures/fig_5.png)
*Figure 5: GPT 배포(왼쪽)와 Instruct 배포(오른쪽) 프롬프트에서 모델 크기별 SFT 175B 대비 승률 ( Held-out 평가자(상단)와 학습 평가자(하단) 모두에서 PPO-ptx와 PPO가 SFT 및 GPT를 일관되게 앞서며, 학습에 참여하지 않은 평가자에게도 동일한 선호 패턴이 나타나 일반화 성능을 입증한다. (Ouyang et al., 2022)*

### 행동 지표별 상세 비교

사람 선호도 외에도 구체적인 행동 지표에서 InstructGPT의 개선을 정량적으로 확인할 수 있다. 아래 그림은 지시 이행, 제약 준수, 환각, 고객 서비스 언어 사용 등 4가지 핵심 행동 지표를 모델별로 비교한 것이다.

![모델별 지시 이행, 제약 준수, 환각, 고객 서비스 언어 사용 비율 비교 차트](figures/fig_6.png)
*Figure 6: 주요 행동 지표 비교 ) PPO-ptx는 지시 이행(Attempts correct instruction)과 명시적 제약 준수(Follows explicit constraints)에서 가장 높은 수치를 보이며, 환각(Hallucinations) 비율은 가장 낮다. RLHF가 단순한 선호도 점수 개선을 넘어 모델의 실질적 행동 패턴을 교정함을 보여준다. (Ouyang et al., 2022)*

이 행동 지표를 모델 크기별로 세분화하면 더 흥미로운 패턴이 드러난다.

![모델 크기(1.3B-175B)별 지시 이행, 고객 서비스 적합성, 제약 준수, 환각 비율 변화 추이](figures/fig_34.png)
*Figure 34: 모델 크기(1.3B-175B)에 따른 4가지 행동 지표 변화 ( PPO-ptx(빨강)는 모든 규모에서 지시 이행과 제약 준수가 가장 높고 환각이 가장 낮다. 특히 GPT(파랑)는 모델이 커져도 환각이 줄지 않는 반면, PPO-ptx는 규모와 무관하게 일관된 저환각 성능을 보인다. (Ouyang et al., 2022)*

PPO-ptx가 모든 모델 크기에서 일관되게 우수한 행동 지표를 보인다는 점은, RLHF의 효과가 특정 규모에 한정되지 않음을 의미한다.

### 태스크 유형별 선호도

태스크 유형에 따라 InstructGPT의 우위가 달라지는 양상도 흥미롭다.

| 태스크 유형 | InstructGPT 선호율 | 특이사항 |
|-----------|-------------------|----------|
| 생성 (Generation) | 87% | 가장 큰 개선 |
| 개방형 QA | 83% | 정직성 향상 기여 |
| 브레인스토밍 | 89% | 창의성+구조화 |
| 요약 | 78% | 상대적으로 낮은 개선 |
| 코드 작성 | 72% | SFT만으로도 양호 |
| 분류 | 65% | 기존 GPT-3도 양호 |

생성과 브레인스토밍 태스크에서 가장 큰 개선을 보인 반면, 분류나 추출 같은 구조화된 태스크에서는 개선 폭이 상대적으로 작았다. 이는 RLHF가 주로 "어떻게 응답할지"의 스타일과 구조를 개선하는 데 강점이 있음을 시사한다.

### TruthfulQA 결과

InstructGPT는 GPT-3 대비 TruthfulQA에서 약 **2배 높은 정직성** 점수를 보였다. 구체적으로, PPO-ptx 모델은 진실성(truthful) 비율이 GPT-3의 ~22%에서 ~50%로 크게 상승했다. 특히 모델이 모르는 것에 대해 "모른다"고 말하는 비율이 증가했다.

![TruthfulQA 벤치마크에서 모델별 진실성, 정보성, 정직성 비율 비교](figures/fig_8.png)
*Figure 8: TruthfulQA 벤치마크 결과 ) QA 프롬프트(왼쪽)와 Instruction+QA 프롬프트(오른쪽)에서 모델별 진실성(truthful), 정보성(informative), 정직성(truthful+informative) 비율. PPO-ptx는 진실성과 정보성의 균형을 가장 잘 맞추며, SFT는 진실성을 높이지만 정보량은 다소 감소하는 트레이드오프가 존재한다. (Ouyang et al., 2022)*

이 결과는 hallucination 문제에 대한 실질적 개선을 의미한다. RLHF가 단순히 "더 그럴듯한 응답"이 아닌 "더 정직한 응답"을 생성하도록 모델을 유도함을 보여준다.

### 독성(Toxicity) 감소

RealToxicityPrompts 벤치마크에서 InstructGPT는 GPT-3에 비해 독성 콘텐츠 생성률이 약 **25% 감소**했다.

![RealToxicityPrompts 벤치마크에서 GPT, SFT, PPO-ptx의 독성 점수 비교](figures/fig_9.png)
*Figure 9: RealToxicityPrompts 독성 평가 결과 ( 인간 평가(왼쪽)와 PerspectiveAPI 자동 평가(오른쪽)에서 Respectful 프롬프트 조건 하에 PPO-ptx가 GPT 대비 독성을 유의미하게 낮춘다. 그러나 프롬프트 유형에 따른 독성 감소 효과의 차이가 주목할 만하다. (Ouyang et al., 2022)*

흥미로운 점은 RLHF 학습이 "respectful" 프롬프트에 대해서는 독성을 크게 줄였지만, 명시적으로 독성 내용을 요청하는 프롬프트에 대해서는 여전히 취약점이 존재했다는 것이다. 이는 보상 모델이 "사용자 요청을 따르는 것"과 "유해한 내용을 거부하는 것" 사이의 균형을 완벽하게 학습하지 못했음을 보여준다.

### 정렬 세금 (Alignment Tax)

RLHF 훈련이 일부 NLP 벤치마크의 성능을 소폭 하락시키는 현상이 관찰되었다. 이를 **정렬 세금(alignment tax)**이라 한다. 아래 그림은 8개 주요 NLP 벤치마크에서 모델별 성능을 종합적으로 비교한 것으로, PPO-ptx가 사전학습 혼합 항을 통해 정렬 세금을 효과적으로 완화하는 모습을 보여준다.

![8개 주요 NLP 벤치마크에서 모델별 성능 비교 차트](figures/fig_32.png)
*Figure 32: 정렬 세금 종합 분석 ) DROP, HellaSwag, QuAC, RTE, SST, SQuAD V2, 번역(Fr->En), Winograd 등 8개 벤치마크에서 PPO-ptx(빨강), PPO(주황), SFT(초록), GPT(파랑)의 모델 크기별 성능. PPO는 여러 벤치마크에서 GPT 대비 뚜렷한 성능 하락을 보이지만, PPO-ptx는 사전학습 혼합 항을 통해 GPT의 성능을 거의 유지한다. (Ouyang et al., 2022)*

| 벤치마크 | GPT-3 175B | PPO (without ptx) | PPO-ptx | 변화 |
|---------|-----------|-------------------|---------|------|
| SQuADv2 (F1) | 69.8 | 64.3 (-5.5) | 68.6 | -1.2 |
| HellaSwag | 78.9 | 76.1 (-2.8) | 78.3 | -0.6 |
| WMT (BLEU) | 25.3 | 22.1 (-3.2) | 24.8 | -0.5 |
| DROP (F1) | 64.1 | 60.8 (-3.3) | 63.5 | -0.6 |

위 표에서 볼 수 있듯이, 사전학습 혼합 항 $\gamma \mathcal{L}_{pretraining}$을 추가한 PPO-ptx 모델은 정렬 세금을 크게 완화했다. 대부분의 벤치마크에서 GPT-3 대비 1% 이내의 성능 차이만 보였다.

### 일반화 성능

인상적인 결과 중 하나는 InstructGPT가 학습에 참여하지 않은 레이블러(held-out labelers)에 대해서도 선호도가 유지된다는 점이다. 학습 레이블러 대비 held-out 레이블러의 선호율 차이는 5% 미만이었다. 이는 모델이 특정 레이블러의 취향이 아닌 일반적인 인간 선호도를 학습했음을 시사한다.

## 의의 및 한계

### 의의

- **RLHF의 실용적 검증**: 대형 언어 모델에 RLHF를 성공적으로 적용한 첫 대규모 사례. 이전까지 RLHF는 소규모 실험에 머물렀으나, InstructGPT는 이를 프로덕션 규모로 확장했다.
- **규모 역설 발견**: 작은 정렬 모델이 큰 베이스 모델을 능가할 수 있음을 증명. 이는 "bigger is better" 패러다임에 대한 중요한 반례이며, 이후 효율적 학습(efficient training) 연구의 동기가 되었다.
- **ChatGPT의 선구자**: InstructGPT의 방법론이 ChatGPT, GPT-4의 기반이 됨. 2022년 11월 출시된 ChatGPT는 InstructGPT와 동일한 RLHF 파이프라인을 사용한 것으로 알려져 있으며, 이는 AI의 대중화를 이끈 결정적 기술이었다.
- **안전 AI 연구 촉진**: 정렬 문제를 실용적 맥락에서 논의하는 계기 마련. 이후 Constitutional AI, DPO 등 다양한 정렬 방법론의 직접적 동기가 되었다.
- **산업 표준 확립**: RLHF의 3단계 파이프라인(SFT -> RM -> PPO)이 이후 거의 모든 상용 LLM의 학습 표준이 되었다. Anthropic의 Claude, Google의 Gemini, Meta의 Llama 2 등이 모두 이 패러다임을 따른다.

### 한계

- **레이블러 편향**: 40명의 레이블러 선호도가 인류 전체의 가치를 대표하지 않을 수 있음. 특히 영어권, 서구 문화에 편중된 레이블러 풀은 다양한 문화적 가치를 반영하지 못한다.
- **보상 해킹(Reward Hacking)**: 모델이 보상 모델을 속이는 방향으로 최적화될 위험. 예를 들어, 실제로 유용하지 않지만 "유용해 보이는" 응답을 생성하는 패턴이 관찰되었다. 불필요하게 장황한 응답이나 과도한 자신감 표현이 그 예이다.
- **비용**: 사람 레이블링과 RL 훈련에 드는 비용이 매우 높음. PPO 학습은 4개의 모델(정책, 참조 정책, 보상 모델, 가치 함수)을 동시에 메모리에 올려야 하므로 GPU 자원이 많이 필요하다.
- **정렬 세금**: 일부 태스크에서 성능 저하 발생. 완전한 무비용 정렬은 달성하지 못했다.
- **문화적 편향**: 영어 중심, 서구 가치 중심의 정렬 위험. 이는 글로벌 배포 시 문화적 충돌을 야기할 수 있다.
- **재현성**: PPO 기반 RLHF는 하이퍼파라미터에 매우 민감하여, 다른 연구자들이 재현하기 어렵다는 보고가 다수 존재한다. KL 계수 $\beta$, 학습률, 배치 크기 등의 미세한 차이가 학습 결과에 큰 영향을 미친다.

### 후속 연구로의 발전

InstructGPT는 현대 LLM 정렬 연구의 출발점이 되었다. 이후 등장한 주요 후속 연구들은 InstructGPT의 한계를 다양한 방식으로 극복하고자 했다.

| 후속 연구 | 핵심 개선점 | InstructGPT 대비 장점 |
|----------|------------|---------------------|
| Constitutional AI (2022) | 인간 레이블을 AI 피드백으로 대체 | 레이블링 비용 절감, 일관성 향상 |
| RLHF (Llama 2, 2023) | 반복적 RLHF + rejection sampling | 더 안정적인 학습 |
| DPO (2023) | PPO 없이 직접 선호도 최적화 | 학습 안정성, 계산 비용 절감 |
| Self-Rewarding LM (2024) | 모델 자체가 보상 모델 역할 | 외부 보상 모델 불필요 |
| ORPO (2024) | SFT와 선호도 학습을 단일 손실로 통합 | 파이프라인 단순화 |

특히 DPO(Direct Preference Optimization)는 InstructGPT의 보상 모델과 PPO 단계를 하나의 손실 함수로 통합하여 큰 주목을 받았다. DPO의 손실 함수는 다음과 같다.

$$\mathcal{L}_{DPO}(\pi_\theta; \pi_{ref}) = -\mathbb{E}_{(x,y_w,y_l)} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)} \right) \right]$$

이 수식에서 보상 모델 $r_\theta$가 사라지고, 정책 모델 $\pi_\theta$ 자체의 로그 확률 비율로 대체된 것을 확인할 수 있다. 이는 InstructGPT의 3단계 파이프라인을 단일 학습 단계로 축소한 것이다.

## 코드 예제

### 정책 모델 (Policy Model)

정책 모델은 SFT로 초기화된 언어 모델로, 프롬프트를 받아 응답을 생성한다.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.optim import AdamW


class PolicyModel(nn.Module):
    """SFT로 초기화된 정책 모델 (GPT 계열 단순화)."""
    def __init__(self, vocab_size=1000, d_model=256, num_layers=4):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, d_model)
        layer = nn.TransformerDecoderLayer(d_model, nhead=8, batch_first=True)
        self.transformer = nn.TransformerDecoder(layer, num_layers)
        self.head = nn.Linear(d_model, vocab_size)

    def forward(self, x):
        h = self.embed(x)
        h = self.transformer(h, h)
        return self.head(h)

    def log_prob(self, x, actions):
        """주어진 토큰 시퀀스의 로그 확률 계산."""
        logits = self.forward(x)
        log_probs = F.log_softmax(logits, dim=-1)
        return log_probs.gather(-1, actions.unsqueeze(-1)).squeeze(-1)

```

### 보상 모델 (Reward Model)

보상 모델은 선호도 비교 데이터로 학습되어 응답의 품질 점수(스칼라)를 출력한다.

```python
class RewardModel(nn.Module):
    """비교 데이터로 학습된 보상 모델."""
    def __init__(self, vocab_size=1000, d_model=256, num_layers=2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model, nhead=8, batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers)
        self.value_head = nn.Linear(d_model, 1)  # 스칼라 보상 출력

    def forward(self, x):
        h = self.encoder(self.embed(x))
        return self.value_head(h[:, -1, :]).squeeze(-1)  # 마지막 토큰의 보상

```

### 가치 모델 (Value Model)

PPO의 어드밴티지 추정(GAE)에 사용되는 상태 가치 함수(critic)이다.

```python
class ValueModel(nn.Module):
    """GAE 계산을 위한 가치 함수 (critic)."""
    def __init__(self, vocab_size=1000, d_model=256, num_layers=2):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model, nhead=8, batch_first=True
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers)
        self.value_head = nn.Linear(d_model, 1)

    def forward(self, x):
        h = self.encoder(self.embed(x))
        return self.value_head(h).squeeze(-1)  # 각 토큰 위치의 가치


def compute_gae(rewards, values, gamma=0.99, lam=0.95):
    """일반화 어드밴티지 추정 (GAE) 계산."""
    advantages = torch.zeros_like(rewards)
    gae = 0
    for t in reversed(range(len(rewards[0]))):
        if t == len(rewards[0]) - 1:
            next_value = 0
        else:
            next_value = values[:, t + 1]
        delta = rewards[:, t] + gamma * next_value - values[:, t]
        gae = delta + gamma * lam * gae
        advantages[:, t] = gae
    return advantages

```

### PPO 학습 루프

보상 모델 학습 및 KL 페널티 포함 PPO 최적화로 구성된 전체 RLHF 파이프라인이다.

```python
def train_reward_model(reward_model, preference_data, epochs=3, lr=1e-4):
    """Step 2: 선호도 비교 데이터로 보상 모델 학습."""
    optimizer = AdamW(reward_model.parameters(), lr=lr)

    for epoch in range(epochs):
        total_loss = 0
        for prompt, y_chosen, y_rejected in preference_data:
            r_chosen = reward_model(y_chosen)
            r_rejected = reward_model(y_rejected)

            # Bradley-Terry 손실: 선호 응답이 더 높은 보상을 받도록
            loss = -F.logsigmoid(r_chosen - r_rejected).mean()
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
            total_loss += loss.item()
        print(f"RM Epoch {epoch+1}: loss={total_loss:.4f}")


def compute_ppo_loss(
    policy, ref_policy, reward_model, value_model,
    tokens, actions, epsilon=0.2, beta=0.02
):
    """Step 3: PPO with KL penalty + GAE (InstructGPT 방식)."""
    new_log_probs = policy.log_prob(tokens, actions)
    with torch.no_grad():
        old_log_probs = ref_policy.log_prob(tokens, actions)
        rewards = reward_model(tokens)
        values = value_model(tokens)

    # GAE로 어드밴티지 계산
    per_token_rewards = rewards.unsqueeze(-1).expand_as(values)
    advantages = compute_gae(per_token_rewards, values)
    advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

    # 중요도 비율 (importance ratio)
    ratio = torch.exp(new_log_probs - old_log_probs.detach())

    # Clipped PPO objective
    clipped = torch.clamp(ratio, 1 - epsilon, 1 + epsilon)
    policy_loss = -torch.min(
        ratio * advantages.detach(),
        clipped * advantages.detach()
    ).mean()

    # KL divergence penalty
    kl_penalty = beta * (new_log_probs - old_log_probs.detach()).mean()

    return policy_loss + kl_penalty


# === 전체 RLHF 파이프라인 실행 ===
policy = PolicyModel()
ref_policy = PolicyModel()  # SFT 모델의 복사본 (frozen)
ref_policy.load_state_dict(policy.state_dict())
for p in ref_policy.parameters():
    p.requires_grad = False

reward_model = RewardModel()
value_model = ValueModel()
optimizer = AdamW(
    list(policy.parameters()) + list(value_model.parameters()), lr=1e-5
)

# PPO 학습 루프
batch_size, seq_len = 4, 20
for step in range(5):
    tokens = torch.randint(0, 1000, (batch_size, seq_len))
    actions = torch.randint(0, 1000, (batch_size, seq_len))

    loss = compute_ppo_loss(
        policy, ref_policy, reward_model, value_model, tokens, actions
    )
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()
    print(f"PPO Step {step+1}: loss={loss.item():.4f}")
```

### trl 라이브러리를 활용한 RLHF 학습

Hugging Face의 `trl` 라이브러리를 사용하면 InstructGPT의 RLHF 파이프라인을 간결하게 구현할 수 있다.

```python
from trl import PPOConfig, PPOTrainer, AutoModelForCausalLMWithValueHead
from transformers import AutoTokenizer

# 모델 및 토크나이저 로드
model_name = "gpt2"
model = AutoModelForCausalLMWithValueHead.from_pretrained(model_name)
ref_model = AutoModelForCausalLMWithValueHead.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# PPO 설정 (InstructGPT 스타일)
ppo_config = PPOConfig(
    model_name=model_name,
    learning_rate=1.41e-5,
    batch_size=16,
    mini_batch_size=4,
    ppo_epochs=4,               # PPO 내부 에폭
    kl_penalty="kl",            # KL 페널티 유형
    init_kl_coeff=0.2,          # beta 초기값
    target_kl=6.0,              # 목표 KL divergence
    cliprange=0.2,              # PPO epsilon
)

# PPOTrainer 초기화
trainer = PPOTrainer(
    config=ppo_config,
    model=model,
    ref_model=ref_model,
    tokenizer=tokenizer,
)

# 학습 루프
for batch in dataloader:  # 프롬프트 데이터 로더
    query_tensors = [tokenizer.encode(q, return_tensors="pt") for q in batch]
    response_tensors = trainer.generate(query_tensors)

    # 보상 모델로 점수 계산
    rewards = [reward_fn(q, r) for q, r in zip(batch, response_tensors)]

    # PPO 업데이트
    stats = trainer.step(query_tensors, response_tensors, rewards)
    print(f"KL: {stats['objective/kl']:.4f}, Reward: {stats['ppo/mean_scores']:.4f}")
```