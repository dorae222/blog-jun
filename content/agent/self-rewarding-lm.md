---
title: "Self-Rewarding Language Models"
slug: "self-rewarding-lm"
category: agent
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.472286+00:00"
---

## 논문 개요

Self-Rewarding Language Models(2024, ICML)는 Meta AI의 Weizhe Yuan 등이 제안한 연구로, LLM이 **외부 보상 모델 없이 자기 자신의 응답을 평가·학습하는 반복 개선 루프**를 구축한다. RLHF(Reinforcement Learning from Human Feedback)의 핵심 병목인 인간 선호도 데이터 수집과 별도 보상 모델 학습 비용을 제거하며, 이론적으로는 **슈퍼휴먼 수준까지 자율 개선**이 가능하다는 비전을 제시한다.

기존 RLHF 파이프라인은 (1) 인간이 응답 쌍을 비교·주석하고, (2) 그 데이터로 보상 모델(RM)을 학습하며, (3) RM 신호로 LLM을 강화학습하는 3단계 구조를 갖는다. 이 구조에서 RM의 품질이 전체 파이프라인의 상한을 결정하는데, RM 자체도 인간 데이터에 의존하므로 성능 향상에 자연적인 한계가 있다. Self-Rewarding LM은 **LLM 자신이 곧 보상 모델**이라는 발상으로 이 한계를 우회한다.

## 핵심 기여

1. **자기 평가(Self-Evaluation) 루프**: 동일한 모델이 응답 생성과 품질 평가를 모두 수행하는 단일 모델 아키텍처.
2. **반복 DPO 학습**: 각 이터레이션마다 새 선호 데이터를 자체 생성하고 DPO로 업데이트하는 EFT(Evolving Fine-Tuning) 방식.
3. **LLM-as-a-Judge 프롬프팅**: 점수 척도와 판단 기준을 포함한 평가 프롬프트로 자체 채점의 일관성을 높임.
4. **인간 주석 독립성**: 초기 소량의 시드 데이터(IFT seed) 외에는 인간 개입 없이 반복 개선 가능.

## 방법론 상세

### 1. 전체 학습 파이프라인

전체 과정은 세 단계로 구성된다.

**Stage 0 — 기반 모델 준비 (SFT)**

소량의 고품질 지시 이행(IFT) 데이터로 베이스 모델을 파인튜닝하여 $M_0$를 얻는다. 이 단계는 기존 SFT와 동일하다.

**Stage 1~N — 자기 보상 이터레이션**

각 이터레이션 $t$에서 다음을 반복한다:

$$M_t \xrightarrow{\text{생성}} \{y_1, y_2, \ldots, y_K\} \xrightarrow{\text{자기 평가}} \text{선호 쌍} (y_w, y_l) \xrightarrow{\text{DPO}} M_{t+1}$$

### 2. 응답 생성 (Instruction Following)

프롬프트 $x$에 대해 모델 $M_t$가 $K$개의 후보 응답 $\{y_1, \ldots, y_K\}$를 샘플링한다(온도 $T > 0$). 다양성을 위해 nucleus sampling($p = 0.9$)을 사용한다.

### 3. LLM-as-a-Judge 자기 평가

모델 $M_t$ 자신에게 각 응답의 품질을 평가하도록 프롬프트를 구성한다. 평가 기준은 다음을 포함한다:

- **지시 이행도**: 요청된 형식과 내용을 충족하는가
- **정확성**: 사실적 오류가 없는가
- **유용성**: 실질적으로 도움이 되는가
- **무해성**: 유해하거나 편향된 내용이 없는가

평가 점수 $r_i \in \{1, 2, 3, 4, 5\}$를 각 응답에 부여하고, 가장 높은 점수의 응답 $y_w$와 가장 낮은 점수의 응답 $y_l$을 선호 쌍으로 구성한다.

$$\mathcal{D}_t = \{(x, y_w, y_l) : r(y_w) > r(y_l)\}$$

### 4. DPO 업데이트

구성된 선호 데이터셋 $\mathcal{D}_t$로 DPO(Direct Preference Optimization) 손실을 최소화한다:

$$\mathcal{L}_{\text{DPO}} = -\mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}_t} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y_w | x)}{\pi_{\text{ref}}(y_w | x)} - \beta \log \frac{\pi_\theta(y_l | x)}{\pi_{\text{ref}}(y_l | x)} \right) \right]$$

여기서 $\pi_{\text{ref}}$는 이전 이터레이션의 모델 $M_{t-1}$이 기준 정책(reference policy)이 되고, $\beta$는 KL 페널티 강도를 제어하는 하이퍼파라미터다.

### 5. 이터레이션 반복

업데이트된 $M_{t+1}$이 다시 응답 생성과 평가를 수행하며 루프가 반복된다. 이론적으로는 이 루프를 무한히 반복하면 모델이 인간 평가자 수준을 초과할 수 있다는 가설을 논문에서 제시한다.

## 실험 결과

### 기반 모델 및 데이터

- 기반 모델: Llama 2 70B Chat
- 초기 IFT 시드: Open Assistant 데이터 3,200개
- 이터레이션 횟수: 3회 (M0 → M1 → M2 → M3)

### AlpacaEval 2.0 결과

AlpacaEval 2.0은 GPT-4 Turbo를 기준 평가자로 하는 win rate 측정 벤치마크다.

| 모델 | Win Rate (%) |
|------|-------------|
| M0 (SFT baseline) | 9.94 |
| M1 (1회 이터레이션) | 11.74 |
| M2 (2회 이터레이션) | 15.38 |
| M3 (3회 이터레이션) | **20.44** |
| GPT-4 Turbo (비교군) | 19.28 |
| Claude 2 (비교군) | 17.19 |

M3는 단 3회 자기 개선만으로 GPT-4 Turbo를 초과한다.

### MT-Bench 결과

MT-Bench에서도 각 이터레이션마다 일관된 성능 향상이 관찰되었으며, 특히 추론(reasoning)과 코딩(coding) 카테고리에서 개선폭이 컸다.

## 의의 및 한계

### 의의

- **인간 주석 병목 해소**: RLHF의 가장 비싼 단계인 인간 선호도 수집을 제거한다.
- **자기 개선의 이론적 가능성**: 보상 모델 성능이 LLM 자체 성능과 함께 성장하므로 상한이 없다.
- **단순한 파이프라인**: 별도의 RM 학습 없이 단일 모델로 전체 루프를 구동한다.
- **확장성**: 더 좋은 기반 모델에 적용할수록 자기 평가 품질도 높아진다.

### 한계

- **자기 편향(Self-bias)**: 모델이 자신의 응답을 타인의 응답보다 높게 평가하는 경향이 있다.
- **평가 일관성**: 동일 응답에 대해 다른 프롬프트 표현이 주어지면 평가 점수가 달라질 수 있다.
- **오류 누적**: 자기 평가 오류가 이터레이션마다 쌓여 잘못된 방향으로 수렴할 위험이 있다.
- **초기 품질 의존**: M0의 초기 품질이 낮으면 자기 평가 자체가 신뢰할 수 없어 전체 루프가 무의미해진다.
- **안전성 미검증**: 자율 개선 루프에서 유해성(harmfulness)이 함께 강화될 가능성에 대한 분석이 부족하다.