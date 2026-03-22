---
title: On Layer Normalization in the Transformer Architecture
slug: "layer-norm-transformer"
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.426889+00:00"
---

## 논문 개요

트랜스포머(Transformer)는 자연어 처리를 비롯한 다양한 딥러닝 분야에서 핵심 아키텍처로 자리잡았다. 그러나 원래 Vaswani et al.(2017)이 제안한 트랜스포머는 Layer Normalization(Layer Normalization, LN)를 서브레이어의 **출력** 이후에 배치하는 이른바 Post-LN 구조를 사용하였다. 이 구조는 학습 초기에 기울기가 불안정해지기 쉬워, 반드시 학습률 웜업(warmup) 스케줄을 병행해야 한다는 실용적 한계가 있었다.

Xiong et al.(2020)은 ICML 2020에서 발표된 이 논문을 통해 Post-LN과 Pre-LN의 기울기 분포를 이론적으로 비교 분석하고, Pre-LN이 왜 더 안정적인 학습을 보장하는지를 수학적으로 규명하였다. 이 연구는 이후 GPT-3, LLaMA 등 현대 대규모 언어 모델 설계에 직접적인 영향을 미쳤다.

---

## 핵심 기여

1. **Post-LN의 기울기 불안정성 이론화**: 학습 초기 Post-LN 트랜스포머에서 하위 레이어의 기울기 크기가 상위 레이어보다 훨씬 크다는 사실을 수식으로 증명하였다.
2. **Pre-LN의 기울기 안정성 보장**: Pre-LN 구조에서는 역전파 시 기울기의 크기가 레이어 전반에 걸쳐 균일하게 유지됨을 이론적으로 보였다.
3. **웜업 없는 학습 가능성 실증**: Pre-LN을 사용하면 학습률 웜업 없이도 SOTA 수준의 성능을 달성할 수 있음을 Machine Translation, 언어 모델링 등 다양한 과제에서 검증하였다.

---

## 방법론 상세

### Post-LN vs Pre-LN 구조 비교

**Post-LN** (원래 트랜스포머):
$$x_{l+1} = \text{LN}(x_l + F_l(x_l))$$

**Pre-LN** (본 논문에서 분석):
$$x_{l+1} = x_l + F_l(\text{LN}(x_l))$$

여기서 $x_l$은 $l$번째 레이어의 입력, $F_l$은 서브레이어(멀티헤드 어텐션 또는 FFN), $\text{LN}$은 Layer Normalization를 의미한다.

### 기울기 크기 분석

논문의 핵심 이론 결과는 다음과 같다. $L$개의 레이어를 가진 모델에서 최종 손실 $\mathcal{L}$에 대한 $l$번째 레이어 파라미터 $\theta_l$의 기울기를 분석하면:

**Post-LN의 경우**, Layer Normalization가 잔차 경로 상에 있기 때문에 기울기가 역전파될 때 배율이 $O(L)$에 비례하여 증가할 수 있다:
$$\left\|\frac{\partial \mathcal{L}}{\partial x_l}\right\| = O(L - l + 1) \cdot \left\|\frac{\partial \mathcal{L}}{\partial x_L}\right\|$$

즉, 하위 레이어(l이 작을수록)일수록 기울기 크기가 레이어 수 $L$에 비례하여 커진다. 이는 깊은 트랜스포머에서 하위 레이어가 매우 큰 기울기를 받아 학습이 불안정해짐을 의미한다.

**Pre-LN의 경우**, Layer Normalization가 Residual Connection 내부에 있어 기울기는 잔차 경로를 통해 직접 전파된다:
$$\left\|\frac{\partial \mathcal{L}}{\partial x_l}\right\| \approx \left\|\frac{\partial \mathcal{L}}{\partial x_L}\right\|$$

이는 깊이에 무관하게 기울기 크기가 거의 일정하게 유지됨을 의미하며, 매우 깊은 네트워크에서도 안정적인 학습을 가능하게 한다.

### 초기화와의 관계

Post-LN의 불안정성은 초기화 시점에도 두드러진다. 학습 초기에 파라미터가 무작위로 초기화되면 서브레이어 $F_l$의 출력이 상대적으로 작고, Layer Normalization가 이를 과도하게 증폭시켜 기울기 폭발(gradient explosion)을 유발한다. 반면 Pre-LN에서는 Layer Normalization 이후에 서브레이어가 적용되므로, 초기에는 입력이 그대로 다음 레이어로 전달되는 항등 함수(identity mapping)에 가까운 행동을 보인다.

웜업 스케줄이 필요한 이유도 이 때문이다. Post-LN에서는 학습 초기의 큰 기울기를 억제하기 위해 학습률을 처음에 매우 낮게 설정하고 점진적으로 높여야 한다. 이는 하이퍼파라미터 튜닝의 복잡성을 높이고 재현성을 떨어뜨린다.

---

## 실험 결과

### Machine Translation (WMT En-De)

| 설정 | BLEU |
|------|------|
| Post-LN + 웜업 | 27.3 |
| Pre-LN + 웜업 | 27.2 |
| Pre-LN + 웜업 없음 | 27.0 |

Pre-LN은 웜업 없이도 Post-LN과 유사한 성능을 달성하며, 더 간단한 학습 설정으로도 경쟁력 있는 결과를 보였다.

### 언어 모델링 (WikiText-103)

Pre-LN 트랜스포머는 동일한 파라미터 수에서 Post-LN과 비슷하거나 약간 더 낮은 perplexity를 기록하면서도, 학습 안정성은 현저히 향상되었다. 특히 학습률 웜업 없이도 학습이 발산하지 않고 수렴하는 것이 핵심 장점으로 부각되었다.

### 기울기 분포 시각화

논문에서는 학습 초기(1K 스텝)의 기울기 크기를 레이어별로 시각화하여, Post-LN에서 하위 레이어의 기울기가 수십 배 이상 크게 나타남을 직접적으로 보였다. Pre-LN에서는 이러한 현상이 관찰되지 않았다.

---

## 의의 및 한계

### 의의

- **현대 LLM 아키텍처의 표준화**: 이 논문의 결과를 바탕으로 GPT-3(Brown et al., 2020), PaLM(Chowdhery et al., 2022), LLaMA(Touvron et al., 2023) 등 거의 모든 현대 대규모 언어 모델이 Pre-LN 구조를 채택하였다.
- **하이퍼파라미터 튜닝 간소화**: 웜업 스케줄에 대한 의존성이 줄어들어, 학습 파이프라인이 단순해졌다.
- **이론적 기반 제공**: 단순한 경험적 관찰을 넘어 수학적 증명을 통해 설계 선택을 정당화하였다는 점에서 학문적 가치가 크다.

### 한계

- **표현력 차이**: 일부 연구에서는 Pre-LN이 Post-LN에 비해 표현력(representational capacity)이 약간 낮을 수 있다는 주장도 있다. Post-LN은 더 깊은 레이어가 더 정제된 표현을 학습하는 데 유리할 수 있다.
- **RMS Norm과의 관계**: 이후 연구에서는 LayerNorm을 더 경량화한 RMSNorm($\text{RMSNorm}(x) = \frac{x}{\text{RMS}(x)} \cdot g$, 여기서 $\text{RMS}(x) = \sqrt{\frac{1}{n}\sum x_i^2}$)이 제안되었으며, LLaMA 시리즈에서 이를 Pre-LN과 결합하여 사용한다.
- **분석의 단순화 가정**: 이론적 분석이 선형 어텐션과 같은 단순화된 모델을 기반으로 하여, 실제 비선형 트랜스포머에 대한 완전한 이론적 설명은 아직 미완이다.

### 후속 영향

Pre-LN은 이제 단순한 대안이 아닌 표준이 되었다. DeepNorm(Wang et al., 2022), ResiDual(Tie et al., 2023) 등 정규화 위치를 더욱 세밀하게 제어하는 후속 연구들이 등장하였으며, 이 논문은 그 출발점이 되었다. 특히 수천억 파라미터 규모의 모델에서 학습 안정성은 단순한 편의 문제가 아니라 학습 성공 여부를 결정하는 핵심 요인이기 때문에, 이 논문의 기여는 실용적 차원에서 매우 크다.