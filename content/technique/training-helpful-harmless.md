---
title: Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback
slug: "training-helpful-harmless"
category: technique
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.485532+00:00"
---

## 논문 개요

"Training a Helpful and Harmless Assistant with Reinforcement Learning from Human Feedback"(2022, arXiv)은 Anthropic의 Yuntao Bai, Andy Jones 등이 발표한 연구로, **인간 피드백 강화학습(RLHF)**을 이용하여 AI 어시스턴트를 유용하고 무해하게 학습시키는 방법론을 체계적으로 기술한다. 이 논문은 Anthropic의 Claude 모델 개발의 기반이 되는 정렬(alignment) 연구의 핵심 성과물이다.

논문의 핵심 주장은 세 가지다. 첫째, 도움(Helpfulness)과 무해함(Harmlessness)은 근본적으로 서로 긴장 관계에 있다. 둘째, 이 긴장을 완화하는 것이 AI 정렬의 핵심 과제다. 셋째, RLHF가 현재로서는 이 긴장을 관리하는 가장 효과적인 접근법이다.

## 핵심 기여

1. **3H 프레임워크 정립**: Helpful + Harmless + Honest(3H)를 AI 어시스턴트의 핵심 목표로 체계화.
2. **대규모 인간 선호도 데이터 수집**: 다양한 시나리오에서 크라우드워커가 두 응답 중 선호하는 것을 선택하는 비교 데이터 수집 방법론 상세 기술.
3. **HH 트레이드오프 정량 분석**: Helpful-Harmless 간 긴장을 실험적으로 측정하고 시각화.
4. **Constitutional AI로의 발전 토대**: 이후 Constitutional AI(2022)의 직접적인 전신 연구.

## 방법론 상세

### 1. 3H 목표 정의

**Helpful (도움)**
- 사용자의 요청을 정확히 이해하고 유용한 응답 제공
- 과도한 거절이나 불필요한 면책 조항 없이 실질적 도움 제공
- 사용자의 명시적·묵시적 의도 모두 충족

**Harmless (무해)**
- 유해하거나 위험한 정보 제공 거부
- 편향되거나 차별적인 내용 생성 방지
- 사회적 피해를 유발할 수 있는 행동 거부

**Honest (정직)**
- 불확실한 내용에 대해 자신의 한계를 인정
- 사용자를 기만하지 않음
- 사실과 의견을 명확히 구분

### 2. RLHF 파이프라인

Anthopic의 RLHF 파이프라인은 4단계로 구성된다.

**Step 1: 초기 SFT 모델 학습**

대화 데이터로 기반 언어 모델을 지도 학습(supervised fine-tuning)하여 기본 대화 능력을 갖춘 $\pi_{\text{SFT}}$를 얻는다.

**Step 2: 인간 선호도 데이터 수집**

동일한 프롬프트 $x$에 대해 $\pi_{\text{SFT}}$가 두 가지 응답 $y_1, y_2$를 생성하고, 크라우드워커가 더 선호하는 응답을 선택한다:

$$\mathcal{D}_{\text{pref}} = \{(x, y_w, y_l) : \text{human prefers } y_w \text{ over } y_l\}$$

**Step 3: 보상 모델(RM) 학습**

Bradley-Terry 모델을 기반으로 보상 모델을 학습한다:

$$\mathcal{L}_{\text{RM}}(\theta) = -\mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}_{\text{pref}}} \left[ \log \sigma(r_\theta(x, y_w) - r_\theta(x, y_l)) \right]$$

여기서 $r_\theta(x, y)$는 보상 모델이 응답 $y$에 부여하는 스칼라 점수다.

**Step 4: PPO로 강화학습**

보상 모델 신호 $r_\theta$를 사용하여 PPO(Proximal Policy Optimization)로 언어 모델을 최적화한다:

$$\mathcal{L}_{\text{PPO}}(\phi) = \mathbb{E}_{(x,y) \sim \pi_\phi} \left[ r_\theta(x, y) - \beta \cdot \text{KL}(\pi_\phi(y|x) \| \pi_{\text{SFT}}(y|x)) \right]$$

KL 페널티 항은 정책이 SFT 모델에서 너무 멀리 벗어나는 것을 방지한다. $\beta$는 유용성-안전성 균형을 조정하는 핵심 하이퍼파라미터다.

### 3. Helpful-Harmless 분리 학습

논문의 중요한 실험적 발견은, **Helpful 보상 모델**과 **Harmless 보상 모델**을 분리하여 학습하는 것이 단일 통합 보상 모델보다 유리하다는 점이다.

- **HH 통합 보상 모델**: 단일 RM이 도움도와 무해성을 동시에 평가
- **분리 보상 모델**: RM-H(도움), RM-HH(무해) 두 모델을 별도로 학습 후 가중 결합

$$r_{\text{combined}}(x, y) = \lambda \cdot r_{\text{helpful}}(x, y) + (1-\lambda) \cdot r_{\text{harmless}}(x, y)$$

$\lambda$를 조정함으로써 도움과 안전성 사이의 트레이드오프를 런타임에 제어 가능하다.

### 4. 데이터 수집 상세

**Helpful 데이터**:
- 크라우드워커가 실제 어시스턴트를 사용하듯 다양한 요청을 작성
- 두 모델 응답 중 더 유용한 것을 선택
- 약 44K 비교 쌍 수집

**Harmless 데이터 (레드팀)**:
- 크라우드워커가 의도적으로 유해한 응답을 유도하는 프롬프트 작성
- 두 응답 중 더 무해한 것을 선택
- 약 42K 비교 쌍 수집

## 실험 결과

### Elo 점수 비교

Helpful 평가에서의 Elo 점수 (높을수록 유용):

| 모델 | Elo |
|------|-----|
| SFT baseline | 1000 |
| RLHF (Helpful RM만) | 1087 |
| RLHF (HH 통합 RM) | 1074 |
| RLHF (분리 RM, 최적 $\lambda$) | **1091** |

### HH 트레이드오프 시각화

Helpful 점수와 Harmless 점수를 동시에 플롯하면 파레토 프론티어가 나타난다:

$$\text{Pareto frontier: } \{(H, HH) : \text{no solution improves both simultaneously}\}$$

$\lambda$ 증가 → Helpful 점수 상승, Harmless 점수 하락의 명확한 트레이드오프 확인.

### 안전성 평가

레드팀 프롬프트에 대한 유해 응답 비율:
- SFT 기반 모델: 약 28%
- RLHF (Harmless RM 적용): 약 6%
- 약 78% 감소

## Constitutional AI와의 연결

이 연구는 Anthropic의 후속 연구인 Constitutional AI(Bai et al., 2022b)의 직접적 전신이다. Constitutional AI는 인간 레이블러 의존성을 줄이기 위해, RLHF의 인간 선호도 데이터 수집 단계를 **AI 자체 평가**로 대체한다. 구체적으로:

1. 이 논문의 RLHF → Constitutional AI의 RLAIF(RL from AI Feedback)으로 발전
2. HH 트레이드오프 완화 → 헌법(Constitution) 기반 AI 자기 개선으로 발전
3. 수동 레드팀 → AI 기반 레드팀으로 발전

## 의의 및 한계

### 의의

- **산업계 RLHF 방법론 표준화**: OpenAI의 InstructGPT와 함께, RLHF를 AI 정렬의 주류 방법으로 확립.
- **3H 프레임워크**: 이후 AI 어시스턴트 평가의 표준 기준이 됨.
- **HH 트레이드오프 정량화**: 안전성과 유용성의 긴장 관계를 처음으로 체계적으로 정량 분석.
- **Claude의 초석**: Anthropic Claude 모델 시리즈의 직접적 기반 연구.

### 한계

- **크라우드워커 품질 의존**: 데이터 품질이 크라우드워커의 판단 능력과 편향에 크게 의존.
- **RM 오버피팅(Reward Hacking)**: 보상 모델을 최대화하는 방향으로 학습하다 보면, RM이 예측하지 못한 방식으로 점수를 높이는 행동이 발생할 수 있다.
- **Honest 목표 미흡**: 3H 중 Honesty는 나머지 둘에 비해 정량적 평가 방법이 부족하고 상대적으로 덜 다루어졌다.
- **비용 문제**: 대규모 인간 선호도 데이터 수집은 시간과 비용이 많이 들어, 소규모 조직이 재현하기 어렵다.