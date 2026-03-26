## 개요

RLHF(Reinforcement Learning from Human Feedback)는 [[InstructGPT]], ChatGPT 등 대형 언어 모델의 정렬(alignment)에 핵심적인 역할을 해왔습니다. 그러나 RLHF는 보상 모델(reward model)과 정책 모델(policy model)을 별도로 학습해야 하고, [[PPO]] 같은 온라인 강화학습 알고리즘의 불안정성과 막대한 GPU 자원 요구라는 실용적 한계를 가집니다.

Stanford 대학교의 Rafael Rafailov 등이 2023년 NeurIPS에서 발표한 **DPO(Direct Preference Optimization)**는 이 복잡성을 수학적으로 제거합니다. 핵심 통찰은 KL-제약 RLHF의 최적화 문제를 닫힌 형태(closed-form)로 풀면, **보상 함수가 최적 정책과 참조 정책의 로그 비율로 정확히 표현**된다는 것입니다. 이를 통해 보상 모델 학습 단계를 완전히 건너뛰고, 선호도 데이터에 대한 단순한 이진 분류 손실만으로 정책을 직접 최적화할 수 있습니다.

![RLHF와 DPO 파이프라인 비교](figures/fig_1.png)
*Figure 1. RLHF(좌)는 보상 모델을 먼저 학습한 뒤 강화학습 루프로 정책을 최적화하는 반면, DPO(우)는 선호도 데이터로부터 최대 우도(maximum likelihood) 목적함수로 직접 정책을 학습한다. 보상 모델 학습과 PPO 강화학습이라는 두 단계를 완전히 제거한 것이 DPO의 핵심 기여이다. (Rafailov et al., 2023)*

DPO는 발표 이후 Semantic Scholar 기준 약 **6,500회 이상 인용**(1,531건의 고영향력 인용 포함)되었으며, [[Llama 3]], [[Mistral]], Qwen, Gemma 등 대부분의 오픈소스 모델이 DPO 또는 그 변형을 사용하여 정렬됩니다.

## 배경: RLHF의 복잡성

### RLHF 파이프라인의 3단계 구조

기존 RLHF는 다음과 같은 3단계 파이프라인으로 구성됩니다.

**1단계: SFT(Supervised Fine-Tuning)**. 사전학습된 언어 모델을 고품질 시연(demonstration) 데이터로 미세조정합니다. 이 결과물이 참조 정책 $\pi_{\mathrm{ref}}$가 됩니다.

**2단계: 보상 모델(Reward Model) 학습**. 동일 프롬프트에 대한 두 응답의 쌍별(pairwise) 선호도 데이터로 보상 모델 $r_\phi(x, y)$를 학습합니다. 보상 모델은 프롬프트-응답 쌍에 대해 스칼라 점수를 출력하는 별도의 신경망입니다.

**3단계: RL 최적화**. 학습된 보상 모델을 신호로 사용하여 PPO(Proximal Policy Optimization)로 정책 모델을 최적화합니다. 참조 정책으로부터의 KL divergence 페널티를 부과하여 과도한 이탈을 방지합니다.

### RLHF의 근본적 문제점

이 파이프라인은 다음과 같은 문제점을 가집니다.

1. **4개 모델 동시 관리**: 정책(actor), 참조(reference), 보상(reward), 가치 함수(critic) 모델을 동시에 GPU에 올려야 합니다. 7B 모델 기준 약 56GB 이상의 GPU 메모리가 필요합니다.

2. **PPO의 불안정성**: 클리핑 비율($\epsilon$), GAE 파라미터($\lambda$), 학습률, 미니배치 크기 등 수많은 하이퍼파라미터에 민감합니다. 작은 변화가 mode collapse나 reward hacking으로 이어질 수 있습니다.

3. **보상 모델의 오버헤드와 병목**: 별도 보상 모델의 과적합이나 분포 이동(distribution shift)이 전체 파이프라인의 성능 상한을 결정합니다.

4. **온라인 생성의 비용**: PPO는 매 이터레이션마다 현재 정책으로 응답을 생성하고, 보상 모델로 평가하는 루프를 반복해야 합니다.

DPO의 핵심 질문은 이것입니다: **보상 모델을 명시적으로 학습하지 않고도, 동일한 최적화 목표를 달성할 수 있는가?**

## 방법론

### RLHF 목표 함수에서 출발

RLHF는 다음 목표를 최대화합니다.

$$\max_{\pi_\theta} \mathbb{E}_{x \sim \mathcal{D},\, y \sim \pi_\theta(y|x)} \left[ r(x, y) - \beta \log \frac{\pi_\theta(y|x)}{\pi_{\mathrm{ref}}(y|x)} \right]$$

여기서 $r(x, y)$는 보상 함수, $\pi_{\mathrm{ref}}$는 SFT로 학습된 참조 정책, $\beta > 0$는 KL 페널티 계수입니다. 보상을 최대화하되, 참조 정책과의 KL divergence에 비례하는 비용을 지불하는 구조입니다.

### 1단계: 최적 정책의 닫힌 형태 유도

이 KL-제약 최적화 문제는 각 프롬프트 $x$에 대해 독립적으로 풀 수 있습니다. 확률 분포 제약 $\sum_y \pi(y|x) = 1$ 하에서 라그랑주 승수법을 적용하면, 최적 정책이 다음과 같은 닫힌 형태(closed-form)를 가짐을 보일 수 있습니다.

$$\pi^*(y|x) = \frac{1}{Z(x)} \pi_{\mathrm{ref}}(y|x) \exp\!\left(\frac{1}{\beta} r(x, y)\right)$$

여기서 $Z(x) = \sum_y \pi_{\mathrm{ref}}(y|x) \exp\!\left(\frac{r(x,y)}{\beta}\right)$는 분배 함수(partition function)입니다. 이 결과는 직관적으로도 자연스럽습니다. 최적 정책은 참조 정책을 기반으로, 보상이 높은 응답의 확률을 지수적으로 증가시키되, $\beta$가 이 증폭의 강도를 조절합니다.

**유도 과정.** 라그랑지안을 구성합니다.

$$\mathcal{L}(\pi, \lambda) = \sum_y \pi(y|x)\left[r(x,y) - \beta\log\frac{\pi(y|x)}{\pi_{\mathrm{ref}}(y|x)}\right] - \lambda\!\left(\sum_y \pi(y|x) - 1\right)$$

$\pi(y|x)$에 대해 미분하고 0으로 놓으면:

$$r(x,y) - \beta\log\frac{\pi(y|x)}{\pi_{\mathrm{ref}}(y|x)} - \beta - \lambda = 0$$

이를 $\pi(y|x)$에 대해 정리하면 위의 볼츠만 분포 형태가 나오며, 정규화 상수 $Z(x)$는 라그랑주 승수 $\lambda$에 의해 결정됩니다.

### 2단계: 보상 함수의 재매개변수화 -- DPO의 핵심 통찰

위 최적 정책 표현을 $r(x, y)$에 대해 역으로 풀면:

$$r(x, y) = \beta \log \frac{\pi^*(y|x)}{\pi_{\mathrm{ref}}(y|x)} + \beta \log Z(x)$$

이 등식이 DPO의 핵심입니다. **보상 함수는 최적 정책과 참조 정책의 로그 비율로 정확히 표현됩니다.** $\beta \log Z(x)$ 항은 응답 $y$에 의존하지 않는 상수(프롬프트 $x$에만 의존)이므로, 두 응답 간의 보상 차이를 계산할 때 자동으로 상쇄됩니다.

이 등식의 의미는 심오합니다. 최적 정책 $\pi^*$를 알면 보상 함수 $r$을 완벽하게 복원할 수 있으며, 정책 자체가 보상 함수의 정보를 완전히 인코딩합니다. 따라서 **"언어 모델은 암묵적으로 보상 모델"**입니다.

### 3단계: DPO 손실 함수 유도

Bradley-Terry 모델은 인간의 쌍별 선호도를 보상 차이의 시그모이드로 모델링합니다.

$$p(y_w \succ y_l \mid x) = \sigma\!\left(r(x, y_w) - r(x, y_l)\right)$$

여기서 $\sigma(z) = \frac{1}{1+e^{-z}}$는 시그모이드 함수, $y_w$는 선호된(winning) 응답, $y_l$은 거부된(losing) 응답입니다.

2단계에서 유도한 보상 함수 표현을 대입하면:

$$r(x, y_w) - r(x, y_l) = \beta \log \frac{\pi^*(y_w|x)}{\pi_{\mathrm{ref}}(y_w|x)} - \beta \log \frac{\pi^*(y_l|x)}{\pi_{\mathrm{ref}}(y_l|x)}$$

여기서 $\beta \log Z(x)$ 항이 **완벽하게 상쇄**됩니다. 분배 함수 $Z(x)$는 모든 가능한 응답에 대한 합으로 정의되어 일반적으로 계산 불가능(intractable)한데, DPO는 이 항을 계산할 필요 자체를 제거합니다. 이것이 DPO를 실용적으로 만드는 결정적인 수학적 성질입니다.

최적 정책 $\pi^*$를 학습 가능한 파라미터 $\theta$를 가진 정책 $\pi_\theta$로 대체하면, 최종 DPO 손실 함수가 도출됩니다.

$$\boxed{\mathcal{L}_{\mathrm{DPO}}(\pi_\theta; \pi_{\mathrm{ref}}) = -\mathbb{E}_{(x, y_w, y_l) \sim \mathcal{D}} \left[ \log \sigma\!\left(\beta \log \frac{\pi_\theta(y_w|x)}{\pi_{\mathrm{ref}}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{\mathrm{ref}}(y_l|x)}\right) \right]}$$

이 손실 함수는 단순한 **이진 교차 엔트로피** 형태입니다. 보상 모델도, PPO도, 가치 함수도 필요 없습니다. 선호도 데이터 $(x, y_w, y_l)$과 참조 모델 $\pi_{\mathrm{ref}}$만 있으면 됩니다.

### RLHF와의 수학적 동치성

**정리 (Rafailov et al., 2023)**: Bradley-Terry 선호도 모델과 KL-제약 보상 최대화 RLHF 목표 하에서, DPO 손실 함수의 전역 최소점(global minimum)은 RLHF 목표의 최적 정책과 일치합니다.

동치성의 핵심 조건:

- 선호도 데이터가 Bradley-Terry 모델을 따릅니다.
- 선호도 데이터의 분포가 최적 정책의 분포를 충분히 커버합니다.
- 정책 클래스가 충분히 표현력이 있어서 최적 정책을 포함합니다.

이 조건들이 만족되면, DPO는 RLHF의 3단계 파이프라인을 수학적으로 동일한 단일 지도학습 단계로 대체합니다.

### 그래디언트 분석: DPO가 학습하는 방식

DPO 손실의 그래디언트를 분석하면 알고리즘의 동작 원리를 더 깊이 이해할 수 있습니다.

$$\nabla_\theta \mathcal{L}_{\mathrm{DPO}} = -\beta \, \mathbb{E} \left[ \underbrace{\sigma\!\left(\hat{r}_\theta(x, y_l) - \hat{r}_\theta(x, y_w)\right)}_{\text{가중치: 모델이 순위를 잘못 매긴 정도}} \left( \underbrace{\nabla_\theta \log \pi_\theta(y_w|x)}_{\text{선호 응답 확률 증가}} - \underbrace{\nabla_\theta \log \pi_\theta(y_l|x)}_{\text{거부 응답 확률 감소}} \right) \right]$$

여기서 $\hat{r}_\theta(x, y) = \beta \log \frac{\pi_\theta(y|x)}{\pi_{\mathrm{ref}}(y|x)}$는 **암묵적 보상(implicit reward)**입니다.

가중치 항 $\sigma(\hat{r}_\theta(x, y_l) - \hat{r}_\theta(x, y_w))$의 의미가 중요합니다. 이 값은 모델이 현재 거부 응답 $y_l$에 선호 응답 $y_w$보다 **높은 암묵적 보상을 부여하고 있을 때**, 즉 순위를 잘못 매기고 있을 때 커집니다. 반대로 이미 올바르게 순위를 매긴 쌍에 대해서는 작아집니다.

이 그래디언트 구조는 두 가지 핵심 성질을 내포합니다.

**적응적 가중치(Adaptive Weighting).** DPO는 자동으로 "어려운 예제"에 집중합니다. 이미 올바르게 학습된 쌍은 무시하고, 아직 순위가 틀린 쌍에 학습 자원을 집중하는 **hard example mining** 효과가 내재되어 있습니다. 이는 focal loss와 유사한 메커니즘으로, 추가적인 하이퍼파라미터 없이 자연스럽게 발생합니다.

**암묵적 KL 제약.** 참조 모델 대비 상대적 로그 확률을 사용하므로, 참조 정책에서 과도하게 벗어나는 업데이트는 자연스럽게 억제됩니다. PPO처럼 명시적인 KL 페널티 항을 따로 관리할 필요가 없습니다. 단순히 $y_w$의 절대 확률을 높이는 것이 아니라 참조 모델 대비 **상대적 확률**을 조절하므로, 참조 정책에서 너무 벗어나는 것이 자연스럽게 방지됩니다.

### RLHF vs DPO 비교

| 항목 | RLHF (PPO 기반) | DPO |
|------|----------------|-----|
| 1단계 | SFT | SFT |
| 2단계 | 보상 모델 학습 | **(생략)** |
| 3단계 | PPO로 정책 최적화 | DPO 손실로 직접 학습 |
| 필요 모델 수 | 4개 (정책, 참조, 보상, 가치) | **2개** (정책, 참조) |
| GPU 메모리 | ~56GB (7B 기준) | **~28GB** (7B 기준) |
| 학습 안정성 | 낮음 (PPO 하이퍼파라미터 민감) | **높음** |
| 구현 복잡도 | 매우 높음 (수천 줄) | **낮음** (핵심 ~20줄) |
| 하이퍼파라미터 | 다수 ($\epsilon$, $\lambda$, lr, epochs 등) | **소수** ($\beta$, lr) |
| 온라인 생성 | 필요 (매 이터레이션) | **불필요** (오프라인) |

## 실험 결과

논문에서는 세 가지 태스크에서 DPO를 평가했습니다: 감정 제어 생성(IMDb), 요약 생성(TL;DR), 대화 생성(Anthropic HH). 핵심 결과는 DPO가 PPO 기반 RLHF와 동등하거나 우수한 성능을 달성하면서, 학습 비용은 크게 절감했다는 것입니다.

### 감정 제어 생성 (IMDb): 최적화 품질의 정량적 검증

IMDb 리뷰 데이터를 이용한 긍정 감정 생성 태스크에서, DPO와 PPO의 **보상-KL 프론티어(frontier)**를 비교했습니다. 이 프론티어는 "주어진 KL divergence 예산 내에서 달성 가능한 최대 보상"을 나타내며, 알고리즘의 최적화 품질을 가장 직접적으로 평가하는 지표입니다.

![IMDb 감정 생성에서 DPO와 PPO의 보상-KL 프론티어 비교](figures/fig_2_1.png)
*Figure 2. IMDb 감정 생성 태스크에서 보상-KL 발산 프론티어. DPO(주황)가 모든 KL 값에서 가장 높은 기대 보상을 달성하여, 동일 보상을 더 낮은 KL divergence로 얻는다. 이는 DPO가 reward hacking 없이 실질적으로 원하는 속성을 학습함을 정량적으로 보여준다. (Rafailov et al., 2023)*

| 방법 | 최대 보상 | KL @ 최대 보상 | 보상-KL 효율 |
|------|----------|---------------|-------------|
| PPO | ~3.5 | ~15 nats | 기준선 |
| DPO ($\beta=0.1$) | ~3.8 | ~10 nats | **1.6x** |
| DPO ($\beta=0.5$) | ~3.2 | ~5 nats | **2.7x** |
| Unlikelihood | ~2.5 | ~12 nats | 0.9x |

DPO는 PPO보다 **높은 보상을 더 낮은 KL divergence**로 달성했습니다. PPO는 보상이 증가할수록 KL divergence도 급격히 증가하는 반면, DPO는 완만한 증가를 보였습니다. 이는 DPO의 암묵적 KL 제약이 reward hacking을 효과적으로 방지함을 시사합니다.

### 요약 생성 (TL;DR)

Reddit 포스트 요약 태스크에서 DPO는 PPO 기반 RLHF의 최고 성능을 초과했습니다.

![TL;DR 요약에서 다양한 샘플링 온도에 따른 인간 요약 대비 승률](figures/fig_2_2.png)
*Figure 3. TL;DR 요약 태스크에서 인간 작성 요약 대비 GPT-4 평가 승률. DPO(주황)가 모든 샘플링 온도에서 PPO(파랑)를 능가하며, 온도 변화에 대한 강건성도 더 높다. (Rafailov et al., 2023)*

| 방법 | vs SFT 승률 | vs 인간 요약 승률 | KL Divergence |
|------|------------|-----------------|---------------|
| SFT | 기준선 | ~25% | 0 |
| PPO (Best of N) | ~57% | ~35% | 중간 |
| PPO (RLHF) | ~60% | ~37% | 높음 |
| **DPO** | **~61%** | **~38%** | **낮음** |

DPO가 **더 높은 승률을 더 낮은 KL divergence**로 달성했다는 점이 핵심입니다. DPO 손실 함수 자체에 KL 제약이 암묵적으로 포함되어 있어, PPO에서 빈번한 보상 과최적화(reward over-optimization) 문제가 자연스럽게 완화됩니다.

### 대화 능력 (Anthropic HH)

도움이 되면서도 무해한 응답 생성에서 DPO는 데이터셋의 선택된 응답(chosen)을 능가한 **유일한 방법**이었습니다.

![Anthropic-HH 대화 태스크에서 GPT-4 평가 승률](figures/fig_3_1.png)
*Figure 4. Anthropic-HH 단일 대화에서 GPT-4 평가 승률. DPO(주황)가 데이터셋의 선택된 응답 대비 50% 이상의 승률을 기록한 유일한 방법이다. Preferred-FT(분홍)와 Pythia-2.8B(파랑) 기준선은 50% 미만으로, 데이터셋 레이블보다 성능이 낮다. (Rafailov et al., 2023)*

![Anthropic-HH 대화에서 학습 과정에 따른 승률 변화](figures/fig_3_2.png)
*Figure 5. Anthropic-HH 대화 태스크에서 학습 진행에 따른 승률 변화. 다양한 샘플링 온도에서 DPO의 성능 향상이 학습 전반에 걸쳐 안정적으로 유지된다. (Rafailov et al., 2023)*

| 방법 | Helpful 승률 | Harmless 승률 | 평균 |
|------|-------------|---------------|------|
| SFT | 기준선 | 기준선 | 기준선 |
| Unlikelihood | 48% | 52% | 50% |
| PPO (RLHF) | 55% | 58% | 56.5% |
| **DPO** | **57%** | **60%** | **58.5%** |
| PPO (Ground Truth RM) | 58% | 61% | 59.5% |

"PPO (Ground Truth RM)"은 학습된 보상 모델 대신 실제 인간 선호도의 ground truth 보상을 사용한 이상적인 상한선(oracle)입니다. DPO가 이 상한선에 매우 근접했다는 것은, 보상 모델 학습 과정에서 발생하는 정보 손실을 DPO가 효과적으로 우회할 수 있음을 보여줍니다.

### $\beta$ 하이퍼파라미터의 영향

$\beta$는 DPO에서 가장 중요한 하이퍼파라미터로, KL 페널티의 강도를 제어합니다.

| $\beta$ 값 | 효과 | 권장 시나리오 |
|-----------|------|-------------|
| 0.01 | 공격적 최적화, 참조에서 많이 벗어남 | 강한 선호도 신호가 있을 때 |
| 0.1 | **균형잡힌 최적화** (기본값) | 대부분의 경우 |
| 0.5 | 보수적 최적화, 참조에 가까움 | 안전성이 중요할 때 |
| 1.0 | 매우 보수적, 거의 학습 안됨 | 극도의 안전성 요구 시 |

실무적으로는 $\beta \in [0.05, 0.3]$ 범위에서 시작하여, 검증 세트의 성능을 기준으로 조정하는 것이 권장됩니다.

### Best of N 기준선과의 비교

Best of N 샘플링은 참조 정책에서 N개의 응답을 생성한 뒤, 보상 모델로 최고 점수의 응답을 선택하는 방법입니다. 이 단순한 기준선과의 비교를 통해 DPO의 최적화 품질을 검증할 수 있습니다.

![Anthropic-HH 대화에서 Best of N 기준선 성능](figures/fig_4_1.png)
*Figure 6. Anthropic-HH 대화 태스크에서 Best of N 기준선의 승률. N이 64~128을 넘으면 성능이 정체되며, DPO는 이 정체 구간의 성능을 단일 샘플로 달성한다. (Rafailov et al., 2023)*

![TL;DR 요약에서 Best of N 기준선 성능](figures/fig_4_2.png)
*Figure 7. TL;DR 요약 태스크에서 Best of N 기준선의 승률. 마찬가지로 N=64~128에서 성능이 수렴하며, DPO가 추론 시 다중 샘플링 없이도 경쟁력 있는 성능을 제공함을 보여준다. (Rafailov et al., 2023)*

## 의의 및 한계

### 의의

**실용적 단순성.** 보상 모델과 PPO 없이 선호도 학습이 가능합니다. 핵심 구현이 약 20줄의 PyTorch 코드로 가능하며, 단일 A100 GPU로도 7B 모델의 DPO 학습이 가능합니다. RLHF 대비 GPU 요구량을 절반으로 줄여, GPU 자원이 제한적인 연구자도 정렬 연구를 수행할 수 있게 했습니다.

**이론적 기여.** RLHF의 KL-제약 보상 최대화와 지도학습 기반 선호도 최적화 사이의 수학적 동치 관계를 엄밀하게 증명했습니다. 이 이론적 프레임워크는 IPO, KTO, SimPO, ORPO 등 후속 연구의 기초가 되었습니다.

**광범위한 채택.** [[Llama 3]], [[Mistral]], Qwen, Gemma, Yi, DeepSeek 등 대부분의 오픈소스 모델 정렬에 사용됩니다. HuggingFace TRL 라이브러리의 `DPOTrainer` 클래스 하나로 학습을 시작할 수 있어, 2023년 이후 LLM 정렬의 사실상 표준(de facto standard)이 되었습니다.

### 한계

**오프라인 데이터 분포 문제(Distribution Shift).** 학습 데이터는 참조 정책 $\pi_{\mathrm{ref}}$의 응답 분포를 반영하지만, 학습이 진행되면서 $\pi_\theta$의 분포가 변합니다. 이 분포 불일치가 심해지면 정책 품질이 저하될 수 있으며, Online DPO와 Iterative DPO가 이 문제를 해결합니다.

**선호도 데이터 품질 의존성.** 레이블 노이즈가 10% 이상이면 성능이 급격히 저하됩니다. 인간 평가자 간의 불일치(inter-annotator disagreement)가 높은 데이터에서는 성능이 불안정합니다.

**온라인 RLHF보다 약한 탐색.** PPO는 현재 정책으로 새로운 응답을 생성하며 탐색하지만, DPO는 고정된 데이터셋에 의존합니다. 학습 데이터에 없는 새로운 패턴을 발견하기 어렵습니다.

**Bradley-Terry 가정의 한계.** 선호도가 항상 이행적(transitive)이라는 가정(A > B, B > C이면 A > C)을 하지만, 현실에서는 비이행적 선호도가 존재합니다. 또한 선호도의 강도(margin)를 구분하지 않아, "약간 선호"와 "강하게 선호"를 동일하게 취급합니다.

**길이 편향(Length Bias).** 로그 확률의 합을 사용하므로, 긴 응답이 자연스럽게 낮은 로그 확률을 가집니다. 이로 인해 짧은 응답이 선호되는 편향이 발생할 수 있으며, SimPO의 길이 정규화가 이를 해결합니다.

## 후속 연구 및 변형

DPO의 성공은 각 한계점을 해결하는 수많은 변형 알고리즘의 개발을 촉진했습니다.

| 변형 | 핵심 개선 | 해결하는 DPO의 한계 |
|------|---------|------------------|
| **IPO** | Bradley-Terry 가정 제거 | 비이행적 선호도 처리 |
| **SimPO** | 참조 모델 불필요, 길이 정규화 | 길이 편향, 메모리 50% 절감 |
| **KTO** | 쌍 데이터 불필요, 개별 레이블만 | 데이터 수집 비용 |
| **ORPO** | SFT+DPO 단일 손실 | 학습 단계 통합 |
| **cDPO** | 레이블 노이즈에 강건 | 노이즈 데이터 처리 |
| **Online DPO** | 온라인 생성 + DPO | 분포 불일치 |
| **Iterative DPO** | 반복적 데이터 갱신 | 탐색 부족 |

### IPO (Identity Preference Optimization)

$$\mathcal{L}_{\mathrm{IPO}} = \mathbb{E}\left[\left(\log\frac{\pi_\theta(y_w|x)}{\pi_{\mathrm{ref}}(y_w|x)} - \log\frac{\pi_\theta(y_l|x)}{\pi_{\mathrm{ref}}(y_l|x)} - \frac{1}{2\beta}\right)^2\right]$$

Bradley-Terry 가정을 제거하고, 손실 함수를 회귀(regression) 형태로 변경합니다. 시그모이드 함수의 포화(saturation) 문제를 피할 수 있습니다.

### SimPO (Simple Preference Optimization)

$$\mathcal{L}_{\mathrm{SimPO}} = -\mathbb{E}\left[\log\sigma\!\left(\frac{\beta}{|y_w|}\log\pi_\theta(y_w|x) - \frac{\beta}{|y_l|}\log\pi_\theta(y_l|x) - \gamma\right)\right]$$

참조 모델이 필요 없어 메모리 효율이 두 배 향상됩니다. 시퀀스 길이 $|y|$로 나누는 정규화를 통해 길이 편향을 해결합니다.

### ORPO (Odds Ratio Preference Optimization)

$$\mathcal{L}_{\mathrm{ORPO}} = \mathcal{L}_{\mathrm{SFT}} - \lambda \cdot \mathbb{E}\left[\log\sigma\!\left(\log\frac{\mathrm{odds}_\theta(y_w|x)}{\mathrm{odds}_\theta(y_l|x)}\right)\right]$$

SFT와 선호도 학습을 단일 손실로 통합하여, 별도의 SFT 단계가 불필요합니다.

## 코드 예제

### DPO 핵심 구현 (PyTorch)

```python
import torch
import torch.nn.functional as F
from torch.optim import AdamW


def compute_log_probs(model, input_ids, labels, attention_mask=None):
    """시퀀스의 토큰별 로그 확률을 합산합니다."""
    with torch.cuda.amp.autocast():  # 혼합 정밀도 지원
        logits = model(input_ids, attention_mask=attention_mask).logits
    # labels 위치의 로그 확률만 추출
    log_probs = F.log_softmax(logits[:, :-1, :], dim=-1)
    target = labels[:, 1:]  # 한 토큰 시프트
    per_token_log_probs = log_probs.gather(-1, target.unsqueeze(-1)).squeeze(-1)
    # 패딩 토큰 마스킹
    if attention_mask is not None:
        mask = attention_mask[:, 1:]  # 시프트된 마스크
        per_token_log_probs = per_token_log_probs * mask
    return per_token_log_probs.sum(dim=-1)  # [batch_size]


def dpo_loss(
    policy_chosen_logps, policy_rejected_logps,
    ref_chosen_logps, ref_rejected_logps,
    beta=0.1,
    label_smoothing=0.0,
):
    """
    DPO 손실 함수 (레이블 스무딩 포함).

    Args:
        policy_chosen_logps: 정책 모델의 선호 응답 로그 확률 [B]
        policy_rejected_logps: 정책 모델의 거부 응답 로그 확률 [B]
        ref_chosen_logps: 참조 모델의 선호 응답 로그 확률 [B]
        ref_rejected_logps: 참조 모델의 거부 응답 로그 확률 [B]
        beta: KL 페널티 계수 (기본값 0.1)
        label_smoothing: 레이블 스무딩 비율 (cDPO, 기본값 0.0)
    Returns:
        loss: 스칼라 DPO 손실
        metrics: 학습 모니터링용 메트릭 딕셔너리
    """
    # 암묵적 보상 (implicit reward) 계산
    chosen_rewards = beta * (policy_chosen_logps - ref_chosen_logps)
    rejected_rewards = beta * (policy_rejected_logps - ref_rejected_logps)

    # DPO 로짓 = r(y_w) - r(y_l)
    logits = chosen_rewards - rejected_rewards

    # 레이블 스무딩 적용 (cDPO 변형)
    if label_smoothing > 0:
        loss = (
            -F.logsigmoid(logits) * (1 - label_smoothing)
            - F.logsigmoid(-logits) * label_smoothing
        ).mean()
    else:
        loss = -F.logsigmoid(logits).mean()

    # 모니터링 메트릭
    with torch.no_grad():
        reward_margin = (chosen_rewards - rejected_rewards).mean()
        accuracy = (logits > 0).float().mean()

    metrics = {
        "loss": loss.item(),
        "reward_margin": reward_margin.item(),
        "accuracy": accuracy.item(),
        "chosen_reward": chosen_rewards.mean().item(),
        "rejected_reward": rejected_rewards.mean().item(),
    }
    return loss, metrics


# === DPO 학습 루프 ===
def train_dpo(policy_model, ref_model, dataloader, epochs=3, lr=5e-7, beta=0.1):
    """DPO 학습 전체 루프."""
    optimizer = AdamW(policy_model.parameters(), lr=lr, weight_decay=0.01)
    scaler = torch.cuda.amp.GradScaler()  # 혼합 정밀도

    # 참조 모델 고정
    ref_model.eval()
    for p in ref_model.parameters():
        p.requires_grad = False

    for epoch in range(epochs):
        policy_model.train()
        total_loss, total_acc = 0.0, 0.0
        for step, batch in enumerate(dataloader):
            chosen_ids = batch["chosen_ids"].cuda()
            rejected_ids = batch["rejected_ids"].cuda()
            chosen_mask = batch["chosen_mask"].cuda()
            rejected_mask = batch["rejected_mask"].cuda()

            # 정책 모델 로그 확률
            pi_chosen = compute_log_probs(
                policy_model, chosen_ids, chosen_ids, chosen_mask
            )
            pi_rejected = compute_log_probs(
                policy_model, rejected_ids, rejected_ids, rejected_mask
            )

            # 참조 모델 로그 확률 (기울기 불필요)
            with torch.no_grad():
                ref_chosen = compute_log_probs(
                    ref_model, chosen_ids, chosen_ids, chosen_mask
                )
                ref_rejected = compute_log_probs(
                    ref_model, rejected_ids, rejected_ids, rejected_mask
                )

            loss, metrics = dpo_loss(
                pi_chosen, pi_rejected,
                ref_chosen, ref_rejected, beta
            )

            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(
                policy_model.parameters(), max_norm=1.0
            )
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()

            total_loss += metrics["loss"]
            total_acc += metrics["accuracy"]

            if step % 50 == 0:
                print(
                    f"Epoch {epoch+1} Step {step} | "
                    f"Loss: {metrics['loss']:.4f} | "
                    f"Acc: {metrics['accuracy']:.2%} | "
                    f"Margin: {metrics['reward_margin']:.4f}"
                )

        avg_loss = total_loss / len(dataloader)
        avg_acc = total_acc / len(dataloader)
        print(f"Epoch {epoch+1} 완료 | 평균 Loss: {avg_loss:.4f} | 평균 Acc: {avg_acc:.2%}")
```

### HuggingFace TRL 활용

```python
from trl import DPOConfig, DPOTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer
from datasets import load_dataset

# 모델 및 토크나이저 로드
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-8B-SFT")
ref_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3-8B-SFT")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3-8B-SFT")

# 선호도 데이터셋 로드 (prompt, chosen, rejected 컬럼 필요)
dataset = load_dataset("Anthropic/hh-rlhf", split="train")

# DPO 학습 설정
training_args = DPOConfig(
    output_dir="./dpo_output",
    beta=0.1,                   # KL 페널티 계수
    learning_rate=5e-7,          # 낮은 학습률
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    num_train_epochs=1,
    warmup_ratio=0.1,
    bf16=True,                   # BFloat16 혼합 정밀도
    logging_steps=10,
    max_length=1024,
    max_prompt_length=512,
)

# DPOTrainer로 학습 (핵심 로직은 라이브러리가 처리)
trainer = DPOTrainer(
    model=model,
    ref_model=ref_model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
)
trainer.train()
```

### 실무 하이퍼파라미터 가이드

```python
# DPO 학습 시 주요 하이퍼파라미터
config = {
    "beta": 0.1,                # KL 페널티 (0.01~0.5, 기본값 0.1)
    "learning_rate": 5e-7,      # SFT보다 낮은 학습률 (1e-7 ~ 1e-6)
    "max_length": 1024,         # 시퀀스 최대 길이
    "batch_size": 4,            # 선호도 쌍 배치 크기
    "epochs": 1,                # 보통 1~3 에포크 (과적합 방지)
    "warmup_ratio": 0.1,        # 학습률 워밍업 비율
    "gradient_accumulation": 4, # 유효 배치 크기 확장
    "max_grad_norm": 1.0,       # 그래디언트 클리핑
    "label_smoothing": 0.0,     # 레이블 스무딩 (노이즈 데이터: 0.1)
}
# beta가 너무 크면 -> 참조 모델에 가까워져 학습 안됨
# beta가 너무 작으면 -> 참조에서 크게 벗어나 불안정
# 선호도 데이터 10K 쌍 이상 권장, 최소 1K 쌍
```

> **핵심 포인트**: DPO는 $\mathcal{L}_{\mathrm{DPO}} = -\log \sigma\!\left(\beta\!\left(\log \frac{\pi_\theta(y_w|x)}{\pi_{\mathrm{ref}}(y_w|x)} - \log \frac{\pi_\theta(y_l|x)}{\pi_{\mathrm{ref}}(y_l|x)}\right)\right)$라는 단일 손실 함수로 RLHF의 3단계 파이프라인을 대체합니다. 보상 모델을 정책의 로그 비율로 재매개변수화하는 수학적 통찰이 핵심이며, 분배 함수의 상쇄가 이를 가능하게 합니다. GPU 메모리는 절반, 구현 코드는 20줄이면 충분하며, 2023년 이후 오픈소스 LLM 정렬의 사실상 표준이 되었습니다.
