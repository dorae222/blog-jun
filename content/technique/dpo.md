---
title: "Direct Preference Optimization: Your Language Model is Secretly a Reward Model"
slug: dpo
category: technique
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.411171+00:00"
---

## 논문 개요

RLHF(Reinforcement Learning from Human Feedback)는 ChatGPT, InstructGPT 등 대형 언어 모델의 정렬(alignment)에 핵심적인 역할을 해왔습니다. 그러나 RLHF는 구현이 복잡하고, 보상 모델(reward model)과 정책 모델(policy model)을 별도로 학습해야 하며, PPO 같은 온라인 강화학습 알고리즘의 불안정성 문제가 있습니다.

Rafailov 등(2023)이 NeurIPS에서 발표한 **DPO(Direct Preference Optimization)**는 이 모든 복잡성을 제거합니다. 핵심 통찰은 "언어 모델 자체가 이미 암묵적인 보상 모델"이라는 것입니다. RLHF의 최적화 목표를 수학적으로 재구성하면, 보상 모델을 명시적으로 학습할 필요 없이 언어 모델에 대한 단순한 이진 분류 손실로 변환된다는 것을 증명합니다.

---

## 핵심 기여

1. **RLHF 목표를 닫힌 형태 정책으로 변환**: 기존 RLHF의 최적화 문제를 분석적으로 풀어 최적 정책을 명시적으로 표현
2. **보상 모델 불필요**: 별도의 보상 모델 학습 단계 제거
3. **PPO 불필요**: 온라인 강화학습 없이 지도학습(supervised learning) 방식으로 선호도 학습
4. **단순하고 안정적인 학습**: 기존 SFT(Supervised Fine-Tuning) 파이프라인과 거의 동일한 복잡도

---

## 방법론 상세

### RLHF의 기존 목표 함수

RLHF는 다음 목표를 최대화합니다:

$$\max_{\pi_\theta} \mathbb{E}_{x \sim \mathcal{D},\, y \sim \pi_\theta(y|x)} \left[ r(x, y) \right] - \beta \, D_{\mathrm{KL}}\left[\pi_\theta(y|x) \,\|\, \pi_{\mathrm{ref}}(y|x)\right]$$

여기서 $r(x, y)$는 보상 함수, $\pi_{\mathrm{ref}}$는 SFT로 학습된 참조 정책, $\beta$는 KL 페널티 계수입니다. 이 목표는 보상을 최대화하면서 참조 정책에서 너무 많이 벗어나지 않도록 제어합니다.

### 최적 정책의 닫힌 형태

DPO의 핵심 수학적 결과: 위 최적화 문제의 해는 다음과 같은 닫힌 형태를 가집니다.

$$\pi^*(y|x) = \frac{1}{Z(x)} \pi_{\mathrm{ref}}(y|x) \exp\left(\frac{1}{\beta} r(x, y)\right)$$

여기서 $Z(x) = \sum_y \pi_{\mathrm{ref}}(y|x) \exp\left(\frac{r(x,y)}{\beta}\right)$는 분배 함수(partition function)입니다.

이 식을 $r(x, y)$에 대해 역으로 풀면:

$$r(x, y) = \beta \log \frac{\pi^*(y|x)}{\pi_{\mathrm{ref}}(y|x)} + \beta \log Z(x)$$

즉, **보상 함수는 두 정책의 로그 비율로 표현**됩니다.

### Bradley-Terry 모델과 DPO 손실 함수 유도

Bradley-Terry 모델은 인간 선호도를 다음과 같이 모델링합니다:

$$p(y_w \succ y_l \mid x) = \sigma\left(r(x, y_w) - r(x, y_l)\right)$$

여기서 $y_w$는 선호된(winning) 응답, $y_l$은 거부된(losing) 응답입니다. 앞서 유도한 보상 표현을 대입하면:

$$p(y_w \succ y_l \mid x) = \sigma\left(\beta \log \frac{\pi_\theta(y_w|x)}{\pi_{\mathrm{ref}}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{\mathrm{ref}}(y_l|x)}\right)$$

분배 함수 $Z(x)$가 상쇄됩니다. 이로부터 DPO 손실 함수가 도출됩니다:

$$\mathcal{L}_{\mathrm{DPO}}(\pi_\theta; \pi_{\mathrm{ref}}) = -\mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}} \left[ \log \sigma\left(\beta \log \frac{\pi_\theta(y_w|x)}{\pi_{\mathrm{ref}}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{\mathrm{ref}}(y_l|x)}\right) \right]$$

이 손실 함수는 단순한 **이진 교차 엔트로피** 형태로, 일반적인 딥러닝 프레임워크에서 쉽게 구현할 수 있습니다.

### 직관적 해석

DPO 손실을 최소화하는 것은:
- 선호된 응답 $y_w$에 대해 $\pi_\theta / \pi_{\mathrm{ref}}$ 비율을 **높이는** 방향
- 거부된 응답 $y_l$에 대해 $\pi_\theta / \pi_{\mathrm{ref}}$ 비율을 **낮추는** 방향

으로 모델을 업데이트합니다. 이는 보상 모델 없이도 인간의 선호도 신호를 직접 학습에 반영하는 것과 동일합니다.

### RLHF vs DPO 비교

| 단계 | RLHF (PPO 기반) | DPO |
|------|----------------|-----|
| 1단계 | SFT | SFT |
| 2단계 | 보상 모델 학습 | (생략) |
| 3단계 | PPO로 정책 최적화 | DPO 손실로 직접 학습 |
| 필요 모델 수 | 4개 (정책×2, 보상, 가치) | 2개 (정책, 참조) |
| 안정성 | 낮음 (PPO 하이퍼파라미터 민감) | 높음 |
| 구현 복잡도 | 매우 높음 | 낮음 |

### 구현 예시

```python
import torch
import torch.nn.functional as F

def dpo_loss(policy_logps_chosen, policy_logps_rejected,
             ref_logps_chosen, ref_logps_rejected, beta=0.1):
    """
    DPO 손실 함수 계산
    Args:
        policy_logps_chosen: 정책 모델의 선호 응답 로그 확률
        policy_logps_rejected: 정책 모델의 거부 응답 로그 확률
        ref_logps_chosen: 참조 모델의 선호 응답 로그 확률
        ref_logps_rejected: 참조 모델의 거부 응답 로그 확률
        beta: KL 페널티 계수
    """
    # 로그 비율 (암묵적 보상)
    pi_logratios = policy_logps_chosen - policy_logps_rejected
    ref_logratios = ref_logps_chosen - ref_logps_rejected
    
    # DPO 손실
    logits = pi_logratios - ref_logratios
    losses = -F.logsigmoid(beta * logits)
    
    return losses.mean()
```

---

## 실험 결과

### 요약 생성 (TL;DR)

 Reddit 포스트 요약 태스크에서 DPO는 PPO 기반 RLHF와 비교해 동등하거나 더 나은 승률을 기록했습니다. GPT-4 평가 기준 승률:

| 방법 | vs SFT 승률 |
|------|------------|
| SFT | 기준선 |
| PPO (RLHF) | ~60% |
| **DPO** | **~61%** |

### 감정 제어 생성

IMDb 리뷰의 긍정 감정 생성 태스크에서 DPO는 PPO보다 높은 보상을 달성하면서도 참조 정책에서의 KL 발산이 더 작았습니다.

### 대화 능력 (Anthropic HH 데이터셋)

도움이 되면서도 무해한 응답 생성에서 DPO는 기존 RLHF 방식과 경쟁적인 성능을 보여주었습니다.

---

## 후속 연구 및 변형

### IPO (Identity Preference Optimization)

IPO는 Bradley-Terry 모델 가정 없이 직접 선호도를 학습합니다:

$$\mathcal{L}_{\mathrm{IPO}} = \mathbb{E}\left[\left(\log\frac{\pi_\theta(y_w|x)}{\pi_{\mathrm{ref}}(y_w|x)} - \log\frac{\pi_\theta(y_l|x)}{\pi_{\mathrm{ref}}(y_l|x)} - \frac{1}{2\beta}\right)^2\right]$$

### SimPO (Simple Preference Optimization)

SimPO는 참조 모델 없이 선호도를 학습합니다. 응답 길이로 정규화된 로그 확률을 사용:

$$\mathcal{L}_{\mathrm{SimPO}} = -\mathbb{E}\left[\log\sigma\left(\frac{\beta}{|y_w|}\log\pi_\theta(y_w|x) - \frac{\beta}{|y_l|}\log\pi_\theta(y_l|x) - \gamma\right)\right]$$

참조 모델이 필요 없어 메모리 효율이 두 배 향상됩니다.

### KTO (Kahneman-Tversky Optimization)

KTO는 쌍(pair) 데이터 없이 개별 응답의 선/악 레이블만으로 학습 가능합니다.

### ORPO (Odds Ratio Preference Optimization)

SFT와 선호도 학습을 단일 손실로 통합:

$$\mathcal{L}_{\mathrm{ORPO}} = \mathcal{L}_{\mathrm{SFT}} - \lambda \cdot \mathbb{E}\left[\log\sigma\left(\log\frac{\mathrm{odds}_\theta(y_w|x)}{\mathrm{odds}_\theta(y_l|x)}\right)\right]$$

---

## 의의 및 한계

### 의의

- **실용적 단순성**: 보상 모델과 PPO 없이 선호도 학습 가능, 구현이 간단
- **학문적 기여**: RLHF와 지도학습의 수학적 동치 관계 증명
- **광범위한 채택**: Llama, Mistral, Qwen 등 대부분의 오픈소스 모델 정렬에 사용
- **오프라인 학습**: 사전 수집된 선호도 데이터만으로 학습 가능

### 한계

- **오프라인 데이터 분포 문제**: 학습 데이터와 모델이 생성하는 응답 분포 간의 불일치(distribution shift)
- **선호도 데이터 품질 의존성**: 노이즈 있는 선호도 레이블에 민감
- **온라인 RLHF보다 약한 탐색**: PPO는 새로운 응답을 탐색하며 학습하지만 DPO는 고정 데이터셋에 의존
- **보상 해킹 가능성**: 명시적 보상 모델 없이 Bradley-Terry 가정에만 의존

### 실무 팁

```python
# DPO 학습 시 주요 하이퍼파라미터
config = {
    "beta": 0.1,          # KL 페널티 (너무 크면 학습 안됨, 보통 0.01~0.5)
    "learning_rate": 5e-7, # SFT보다 낮은 학습률 권장
    "max_length": 1024,    # 시퀀스 최대 길이
    "batch_size": 4,       # 선호도 쌍 배치 크기
}
```

---

## 결론

DPO는 RLHF의 복잡한 3단계 파이프라인을 단 하나의 손실 함수로 대체하는 우아한 방법론입니다. 수학적으로는 RLHF와 동치임을 증명하면서도, 실용적으로는 훨씬 간단하고 안정적인 학습을 제공합니다. 2023년 발표 이후 대형 언어 모델 정렬 분야의 사실상 표준(de facto standard)이 되었으며, SimPO, IPO, KTO 등 수많은 변형 알고리즘의 토대가 되었습니다.