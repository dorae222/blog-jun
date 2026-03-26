## 개요

트랜스포머(Transformer)는 자연어 처리를 비롯한 다양한 딥러닝 분야에서 핵심 아키텍처로 자리잡았다. 그러나 원래 Vaswani et al.(2017)이 제안한 트랜스포머는 Layer Normalization(LN)을 서브레이어의 **출력** 이후에 배치하는 이른바 Post-LN 구조를 사용하였다. 이 구조는 학습 초기에 기울기가 불안정해지기 쉬워, 반드시 학습률 웜업(warmup) 스케줄을 병행해야 한다는 실용적 한계가 있었다.

Xiong et al.(2020)은 ICML 2020에서 발표된 이 논문을 통해 Post-LN과 Pre-LN의 기울기 분포를 이론적으로 비교 분석하고, Pre-LN이 왜 더 안정적인 학습을 보장하는지를 수학적으로 규명하였다. 저자들은 Post-LN 구조에서 출력 레이어에 가까운 파라미터의 기울기 기대값이 초기화 시점에서 매우 크다는 것을 증명하고, 이것이 웜업 스케줄이 반드시 필요한 이론적 원인임을 밝혔다. 반면 Pre-LN 구조에서는 이러한 현상이 나타나지 않아 웜업 없이도 안정적 학습이 가능함을 보였다. 이 연구는 이후 GPT-3, LLaMA 등 현대 대규모 언어 모델 설계에 직접적인 영향을 미쳤다.

## 배경 및 문제

### Layer Normalization의 역할

Layer Normalization(Ba et al., 2016)은 각 샘플의 히든 상태를 정규화하는 기법으로, Batch Normalization과 달리 배치 크기에 의존하지 않아 시퀀스 모델에 적합하다. 구체적으로, 입력 벡터 $x \in \mathbb{R}^d$에 대해:

$$\text{LN}(x) = \frac{x - \mu}{\sigma} \cdot \gamma + \beta$$

여기서 $\mu = \frac{1}{d}\sum_{i=1}^d x_i$, $\sigma = \sqrt{\frac{1}{d}\sum_{i=1}^d (x_i - \mu)^2 + \epsilon}$이며, $\gamma, \beta$는 학습 가능한 아핀 변환 파라미터이다. $\epsilon$은 수치 안정성을 위한 작은 상수(보통 $10^{-5}$)이다.

Layer Normalization의 핵심 성질을 정리하면 다음과 같다:

| 성질 | 설명 |
|------|------|
| 스케일 불변성 | $\text{LN}(\alpha x) = \text{LN}(x)$ for $\alpha > 0$ |
| 평행 이동 불변성 | $\text{LN}(x + c\mathbf{1}) = \text{LN}(x)$ for constant $c$ |
| 배치 독립성 | 각 샘플 독립 정규화, Batch Norm과 달리 미니배치 통계에 의존하지 않음 |
| 차원 축소 효과 | 출력이 $d-1$ 차원 초평면 위에 놓임 |

이 성질들 중 **스케일 불변성**이 기울기 전파에서 핵심적인 역할을 한다. LN을 통과한 후에는 입력의 크기 정보가 사라지므로, LN의 야코비안(Jacobian)은 입력 크기에 반비례하는 스케일링 효과를 가진다:

$$\frac{\partial \text{LN}(x)}{\partial x} = \frac{1}{\sigma} \left( I - \frac{1}{d}\mathbf{1}\mathbf{1}^T - \frac{(x - \mu)(x - \mu)^T}{d\sigma^2} \right) \cdot \text{diag}(\gamma)$$

이 야코비안의 스펙트럼 노름(spectral norm)은 대략 $\|\gamma\| / \sigma$에 비례한다. 학습 초기에 $\sigma$가 작으면 기울기가 크게 증폭될 수 있으며, 이것이 Post-LN 구조에서 문제가 되는 핵심 메커니즘이다.

트랜스포머에서 LN은 Residual Connection과 결합되어 사용되는데, **LN의 배치 위치**가 학습 동역학에 결정적인 영향을 미친다는 것이 이 논문의 핵심 발견이다.

### 웜업 스케줄의 필수성 문제

원래 트랜스포머 논문(Vaswani et al., 2017)은 학습 초기에 학습률을 선형으로 증가시키는 웜업 스케줄을 사용했다:

$$lr(t) = d_{\text{model}}^{-0.5} \cdot \min(t^{-0.5}, t \cdot \text{warmup}^{-1.5})$$

이 웜업 없이 학습하면 Post-LN 트랜스포머는 높은 확률로 **학습이 발산**한다. 실무에서 웜업 스텝 수를 잘못 설정하면 학습이 실패하는 경우가 빈번하여, 이 문제의 근본 원인을 이해하는 것이 중요했다.

다음 그림은 SGD 옵티마이저를 사용한 Post-LN 트랜스포머의 학습 곡선으로, 웜업 없이는 검증 손실과 BLEU가 모두 정체되어 학습이 사실상 실패하는 모습을 보여준다.

![SGD 옵티마이저에서 Post-LN 트랜스포머의 웜업 유무에 따른 학습 곡선 비교](figures/fig_4.png)
*Post-LN 트랜스포머의 SGD 학습 곡선. 웜업 없이 학습(점선)하면 검증 손실이 수렴하지 못하고 BLEU가 0에 가까운 반면, 4000 스텝 웜업(실선)을 적용해야 비로소 정상적인 학습이 진행된다. Adam보다 적응력이 낮은 SGD에서 Post-LN의 기울기 불안정성이 더욱 극명하게 드러난다. (Xiong et al., 2020)*

이 논문 이전에도 웜업이 필요하다는 사실은 경험적으로 잘 알려져 있었지만, **왜** 필요한지에 대한 이론적 설명은 부재했다. 기존 설명들은 주로 Adam 옵티마이저의 분산 추정 편향(variance estimation bias)이나 초기 학습 불안정성 같은 일반적인 원인을 지목했으나, 이것만으로는 트랜스포머에서 유독 심각한 이유를 설명할 수 없었다. 본 논문은 이 질문에 대해 Layer Normalization의 위치라는 구조적 관점에서 명확한 답을 제시한다.

### Batch Normalization과의 비교

정규화 기법의 선택은 모델 아키텍처에 따라 달라진다. 트랜스포머가 Layer Normalization을 사용하는 이유를 이해하기 위해 Batch Normalization(BN)과의 차이를 살펴보자:

| 구분 | Batch Normalization | Layer Normalization |
|------|---------------------|---------------------|
| 정규화 축 | 배치 차원 (같은 특성의 다른 샘플들) | 특성 차원 (같은 샘플의 다른 특성들) |
| 배치 크기 의존 | 있음 (작은 배치에서 불안정) | 없음 |
| 추론 시 동작 | 이동 평균 사용 | 학습 시와 동일 |
| 시퀀스 길이 처리 | 가변 길이 처리 어려움 | 자연스럽게 처리 |
| 주요 사용처 | CNN (ResNet, EfficientNet) | Transformer, RNN |

BN은 배치 차원에 대해 정규화하므로 배치 크기가 작을 때 통계 추정이 불안정해진다. 또한 자기회귀(autoregressive) 모델에서는 미래 토큰의 정보가 배치 통계를 통해 누출될 위험이 있다. 반면 LN은 각 토큰의 특성 차원에 대해 독립적으로 정규화하므로 이러한 문제가 없다.

## 핵심 아이디어 (Pre-LN vs Post-LN)

### 구조적 차이

두 구조의 차이는 단순하지만 그 효과는 극적이다.

**Post-LN** (원래 트랜스포머):
$$x_{l+1} = \text{LN}(x_l + F_l(x_l))$$

**Pre-LN** (본 논문에서 분석):
$$x_{l+1} = x_l + F_l(\text{LN}(x_l))$$

여기서 $x_l$은 $l$번째 레이어의 입력, $F_l$은 서브레이어(멀티헤드 어텐션 또는 FFN), $\text{LN}$은 Layer Normalization을 의미한다.

실제 트랜스포머에서는 각 블록이 멀티헤드 어텐션(MHA)과 피드포워드 네트워크(FFN) 두 개의 서브레이어로 구성된다. 따라서 $l$번째 블록의 전체 연산은 다음과 같다:

**Post-LN 전체 블록**:
$$h_l = \text{LN}(x_l + \text{MHA}(x_l, x_l, x_l))$$
$$x_{l+1} = \text{LN}(h_l + \text{FFN}(h_l))$$

**Pre-LN 전체 블록**:
$$h_l = x_l + \text{MHA}(\text{LN}(x_l), \text{LN}(x_l), \text{LN}(x_l))$$
$$x_{l+1} = h_l + \text{FFN}(\text{LN}(h_l))$$

Pre-LN에서 중요한 점은 최종 출력 직전에 **추가적인 LN**이 필요하다는 것이다. 이는 Pre-LN의 출력이 정규화되지 않은 상태이므로, 최종 예측 헤드(prediction head)에 전달하기 전에 정규화를 수행해야 하기 때문이다.

시각적으로 비교하면:

| 구성 요소 | Post-LN | Pre-LN |
|----------|---------|--------|
| 연산 순서 | Input -> Sublayer -> Add -> LN | Input -> LN -> Sublayer -> Add |
| 잔차 경로 | LN이 잔차 경로 위에 위치 | LN이 잔차 경로 밖에 위치 |
| 기울기 흐름 | LN을 통과하며 왜곡 | 잔차 경로로 직접 전달 |
| 최종 출력 | 정규화된 상태 | 정규화되지 않은 상태 (별도 LN 필요) |
| 초기 행동 | 서브레이어 출력에 의존 | 항등 함수에 근접 |

### 기울기 크기의 이론적 분석

논문의 핵심 이론 결과는 다음과 같다. $L$개의 레이어를 가진 모델에서 최종 손실 $\mathcal{L}$에 대한 $l$번째 레이어 파라미터 $\theta_l$의 기울기를 분석하면:

**Post-LN의 경우**, Layer Normalization이 잔차 경로 상에 있기 때문에 기울기가 역전파될 때 배율이 $O(L)$에 비례하여 증가할 수 있다:

$$\left\|\frac{\partial \mathcal{L}}{\partial x_l}\right\|_{\text{Post-LN}} = O(L - l + 1) \cdot \left\|\frac{\partial \mathcal{L}}{\partial x_L}\right\|$$

즉, 하위 레이어($l$이 작을수록)일수록 기울기 크기가 레이어 수 $L$에 비례하여 커진다. 예를 들어, 96 레이어 모델(GPT-3 규모)에서 첫 번째 레이어의 기울기는 마지막 레이어보다 **약 96배** 클 수 있다. 이는 깊은 트랜스포머에서 하위 레이어가 매우 큰 기울기를 받아 학습이 불안정해짐을 의미한다.

**Pre-LN의 경우**, Layer Normalization이 Residual Connection 내부에 있어 기울기는 잔차 경로를 통해 직접 전파된다:

$$\left\|\frac{\partial \mathcal{L}}{\partial x_l}\right\|_{\text{Pre-LN}} \approx \left\|\frac{\partial \mathcal{L}}{\partial x_L}\right\|$$

이는 깊이에 무관하게 기울기 크기가 거의 일정하게 유지됨을 의미하며, 매우 깊은 네트워크에서도 안정적인 학습을 가능하게 한다.

논문에서는 더 정밀한 분석도 제시한다. Post-LN 구조에서 마지막 레이어의 파라미터에 대한 기울기 기대값을 Xavier 초기화 가정 하에서 유도하면:

$$\mathbb{E}\left[\left\|\frac{\partial \mathcal{L}}{\partial W_L}\right\|^2\right] \propto d_{\text{model}} \cdot \beta_L^2$$

여기서 $\beta_L$은 마지막 LN의 shift 파라미터 $\beta$에 의존하는 항이다. 초기화 시점에서 $\beta_L$은 0에 가까우므로 이 기울기도 작아야 하지만, 실제로는 LN의 야코비안에 포함된 $1/\sigma$ 항이 문제를 일으킨다. 서브레이어의 초기 출력이 작을 때 잔차 합산 후의 분산 $\sigma$도 작아지고, 이로 인해 기울기가 크게 증폭되는 것이다.

## 방법론 (gradient flow analysis, training stability)

### 이론적 프레임워크

아래 그림은 Post-LN과 Pre-LN의 구조적 차이를 직관적으로 보여준다. Post-LN은 잔차 합산 이후에 LayerNorm을 적용하여 기울기가 LN을 매번 통과해야 하는 반면, Pre-LN은 잔차 경로가 LN을 우회하여 기울기가 직접 전달된다.

![Post-LN과 Pre-LN Transformer 블록 구조 비교](figures/fig_1.png)
*(a) Post-LN과 (b) Pre-LN Transformer 블록 구조. Post-LN은 Sublayer 출력 이후에 LayerNorm을 적용하여 잔차 경로 위에 LN이 위치하는 반면, Pre-LN은 Sublayer 입력 이전에 LayerNorm을 적용하여 잔차 경로를 통한 직접적인 기울기 전달을 보장한다. (Xiong et al., 2020)*

저자들은 다음과 같은 단순화된 가정 하에서 분석을 수행했다:

1. **서브레이어 출력 가정**: 서브레이어 $F_l$의 출력은 입력에 비해 작다 (초기화 시점). 구체적으로 $\|F_l(x)\| \ll \|x\|$를 가정한다.
2. **독립 초기화 가정**: 각 레이어의 파라미터는 독립적으로 Xavier/He 초기화로 설정된다.
3. **균등 어텐션 가정**: 어텐션 가중치는 균등 분포에 가깝다 (초기화 시점). 즉, $\text{softmax}(QK^T/\sqrt{d_k}) \approx \frac{1}{n}\mathbf{1}\mathbf{1}^T$이다.

이 가정들은 실제 학습 시작 시점의 모델 상태를 합리적으로 근사한다. Xavier 초기화에서 각 레이어의 가중치 행렬은 $W \sim \mathcal{N}(0, 2/(d_{\text{in}} + d_{\text{out}}))$로 설정되므로, 서브레이어의 초기 출력은 실제로 매우 작다.

이 가정 하에서 초기화 시점의 레이어별 기울기 기대값을 측정하면, 두 구조 간의 차이가 극명하게 드러난다. 아래 그림에서 Pre-LN(파랑)은 모든 레이어에서 균일한 기울기를 보이는 반면, Post-LN(주황)은 상위 레이어에서 기울기가 폭발적으로 증가한다.

![초기화 시점에서 레이어별 기울기 기대값 비교: Pre-LN vs Post-LN](figures/fig_5_1.png)
*FFN 가중치의 레이어별 기울기 기대값. Pre-LN(파랑)은 초기화 시점부터 모든 레이어에서 안정적인 기울기를 유지하는 반면, Post-LN(주황)은 상위 레이어로 갈수록 기울기가 급격히 증가한다. 웜업 4000 스텝 이후 Post-LN(초록)의 기울기가 비로소 안정화되는 것을 확인할 수 있다. (Xiong et al., 2020)*

레이어 수를 증가시키면 이 불안정성이 해소되지 않음을 다음 그림이 보여준다. Post-LN에서는 레이어 수가 6에서 14로 증가해도 기울기 기대값이 지속적으로 높은 수준을 유지한다.

![Post-LN 트랜스포머에서 레이어 수 증가에 따른 기울기 기대값 변화](figures/fig_5_4.png)
*Post-LN에서 레이어 수 증가에 따른 기울기 기대값. 레이어 수가 6에서 14로 증가해도 기울기 기대값이 1.6~1.8 범위에서 지속적으로 높게 유지되어, Post-LN의 구조적 불안정성이 깊이와 무관하게 항상 존재함을 보여준다. (Xiong et al., 2020)*

### 핵심 정리 (Theorem)

논문의 주요 정리를 요약하면 다음과 같다:

**정리 1 (Post-LN 기울기 상한)**: Post-LN 트랜스포머에서, 초기화 시점의 기울기에 대해 다음이 성립한다:

$$\mathbb{E}\left[\left\|\frac{\partial \mathcal{L}}{\partial \theta_l}\right\|^2\right] \geq C \cdot (L - l)^2$$

여기서 $C$는 모델 차원과 입력에만 의존하는 상수이다. 이는 하위 레이어의 기울기가 깊이의 제곱에 비례하여 커질 수 있음을 의미한다.

**정리 2 (Pre-LN 기울기 유계성)**: Pre-LN 트랜스포머에서, 초기화 시점의 기울기에 대해 다음이 성립한다:

$$\mathbb{E}\left[\left\|\frac{\partial \mathcal{L}}{\partial \theta_l}\right\|^2\right] \leq C'$$

여기서 $C'$는 레이어 인덱스 $l$에 의존하지 않는 상수이다. 즉, 기울기 크기가 깊이와 무관하게 유계(bounded)이다.

### 수학적 직관

Pre-LN이 안정적인 이유를 직관적으로 이해하자. Pre-LN 구조에서 $L$개 레이어를 거친 최종 출력은:

$$x_L = x_0 + \sum_{l=0}^{L-1} F_l(\text{LN}(x_l))$$

역전파 시 $x_0$에 대한 기울기는:

$$\frac{\partial \mathcal{L}}{\partial x_0} = \frac{\partial \mathcal{L}}{\partial x_L} \cdot \left(I + \sum_{l=0}^{L-1} \frac{\partial F_l(\text{LN}(x_l))}{\partial x_0}\right)$$

핵심은 **항등 행렬 $I$의 존재**이다. 잔차 경로를 통한 직접적인 기울기 전달($I$항)이 보장되므로, 서브레이어의 기울기 기여가 작더라도 기울기가 사라지지 않는다. 이는 ResNet(He et al., 2016)에서 skip connection이 기울기 소실을 방지하는 원리와 동일하다.

반면 Post-LN에서는 LN이 이 잔차 경로를 끊는다. Post-LN의 역전파를 전개하면:

$$\frac{\partial \mathcal{L}}{\partial x_l} = \frac{\partial \mathcal{L}}{\partial x_{l+1}} \cdot \frac{\partial \text{LN}(x_l + F_l(x_l))}{\partial (x_l + F_l(x_l))} \cdot \left(I + \frac{\partial F_l(x_l)}{\partial x_l}\right)$$

여기서 $\frac{\partial \text{LN}}{\partial \cdot}$이 매 레이어마다 곱해지면서 기울기의 방향과 크기를 왜곡한다. 특히 초기화 시점에서 $x_l + F_l(x_l) \approx x_l$이므로 LN의 야코비안이 불안정한 스케일링을 유발한다.

### 초기화와의 관계

Post-LN의 불안정성은 초기화 시점에도 두드러진다. 학습 초기에 파라미터가 무작위로 초기화되면 서브레이어 $F_l$의 출력이 상대적으로 작고, Layer Normalization이 이를 과도하게 증폭시켜 기울기 폭발(gradient explosion)을 유발한다. 반면 Pre-LN에서는 Layer Normalization 이후에 서브레이어가 적용되므로, 초기에는 입력이 그대로 다음 레이어로 전달되는 항등 함수(identity mapping)에 가까운 행동을 보인다.

이것이 웜업 스케줄이 필요한 근본적 이유이다. Post-LN에서는 학습 초기의 큰 기울기를 억제하기 위해 학습률을 처음에 매우 낮게 설정하고 점진적으로 높여야 한다. 이는 하이퍼파라미터 튜닝의 복잡성을 높이고 재현성을 떨어뜨린다.

### 수렴 속도에 대한 분석

저자들은 기울기의 균일성이 수렴 속도에도 영향을 미침을 보였다. SGD 기반 최적화에서 레이어별 기울기 크기가 불균형하면 효과적인 학습률이 레이어마다 달라지게 된다. Post-LN에서 하위 레이어의 기울기가 $O(L)$배 크면, 동일한 학습률을 적용했을 때 하위 레이어는 과도하게 갱신되고 상위 레이어는 충분히 갱신되지 않는 문제가 발생한다.

Adam 옵티마이저는 기울기의 2차 모멘트로 나누어 이 문제를 부분적으로 완화하지만, 학습 초기에 2차 모멘트 추정이 정확하지 않으므로 웜업이 여전히 필요하다. Pre-LN에서는 기울기 크기가 처음부터 균일하므로 Adam의 적응적 학습률 조정이 더 효과적으로 작동한다.

### 실험 설정

이론적 결과를 검증하기 위해 다양한 태스크에서 실험을 수행했다:

1. **기계 번역**: WMT 2014 English-German (4.5M 문장 쌍), WMT 2014 English-French (36M 문장 쌍)
2. **언어 모델링**: WikiText-103 (약 1억 토큰)
3. **다양한 깊이**: 6, 12, 18, 24 레이어
4. **옵티마이저**: Adam ($\beta_1=0.9$, $\beta_2=0.98$, $\epsilon=10^{-9}$)
5. **학습률**: 기본 $5 \times 10^{-4}$, 웜업 유무에 따른 비교

## 실험 결과 (tables)

아래 그림은 소규모 IWSLT14 De-En 번역 과제에서 Adam 옵티마이저를 사용한 Pre-LN과 Post-LN의 학습 곡선 비교이다. Pre-LN은 웜업 없이도 Post-LN(웜업 포함)과 유사한 최종 성능에 도달하며, 다양한 학습률 설정에서 안정적으로 수렴한다.

![IWSLT14 De-En 번역에서 Pre-LN의 다양한 학습률 설정별 학습 곡선](figures/fig_2_1.png)
*IWSLT14 De-En 번역 - Pre-LN 학습 곡선. 검증 손실(좌)과 BLEU(우)에서 Pre-LN이 웜업 없이도 다양한 학습률(1e-3, 5e-4) 설정에서 안정적으로 수렴함을 보여준다. 웜업 500/4000 스텝 설정과 비교해도 최종 성능 차이가 미미하다. (Xiong et al., 2020)*

### Machine Translation (WMT En-De)

| 설정 | BLEU | 학습 안정성 | 비고 |
|------|------|----------|------|
| Post-LN + 웜업 (4000 스텝) | 27.3 | 안정 | 기준선 |
| Post-LN + 웜업 없음 | 발산 | 실패 | NaN loss |
| Pre-LN + 웜업 | 27.2 | 안정 | 기준선 대비 -0.1 |
| **Pre-LN + 웜업 없음** | **27.0** | **안정** | **웜업 없이 수렴** |
| Post-LN + 짧은 웜업 (500 스텝) | 발산 | 실패 | 웜업 부족 |
| Pre-LN + RAdam | 27.1 | 안정 | 웜업 대체 가능 |

Pre-LN은 웜업 없이도 Post-LN과 유사한 성능을 달성하며, 더 간단한 학습 설정으로도 경쟁력 있는 결과를 보였다. Post-LN은 웜업 없이 학습하면 완전히 발산하여 학습 자체가 불가능했다. 특히 웜업 스텝 수가 충분하지 않은 경우(500 스텝)에도 발산하여, Post-LN이 웜업 하이퍼파라미터에 매우 민감함을 확인하였다.

다양한 옵티마이저와 웜업 설정의 조합에서 검증 손실 수렴 양상을 비교하면, Pre-LN의 강건성이 더욱 명확해진다. 아래 그림은 Adam과 RAdam 옵티마이저에서의 수렴 비교이다.

![다양한 옵티마이저와 웜업 설정에서 Pre-LN과 Post-LN의 검증 손실 비교](figures/fig_10_1.png)
*다양한 설정에서의 검증 손실 수렴 곡선. Pre-LN(실선)은 Adam과 RAdam 모두에서 웜업 없이도 안정적으로 학습되는 반면, Post-LN(점선)은 RAdam 없이는 발산하는 경향이 있다. RAdam이 Post-LN의 부분적 대안이 될 수 있으나, Pre-LN의 근본적 안정성에는 미치지 못한다. (Xiong et al., 2020)*

### 깊은 모델에서의 비교

| 레이어 수 | Post-LN + 웜업 | Pre-LN + 웜업 없음 | 기울기 비율 (Layer1/LayerL) |
|----------|---------------|------------------|---------------------------|
| 6 | 27.3 (웜업 4K) | 27.0 | Post: ~12x, Pre: ~1.2x |
| 12 | 27.5 (웜업 4K) | 27.4 | Post: ~25x, Pre: ~1.3x |
| 18 | 발산 (웜업 8K 필요) | 27.6 | Post: ~40x, Pre: ~1.2x |
| 24 | 발산 (웜업 16K 필요) | 27.5 | Post: ~55x, Pre: ~1.3x |

모델이 깊어질수록 Post-LN은 더 긴 웜업이 필요하고 학습이 불안정해지는 반면, Pre-LN은 깊이에 관계없이 안정적으로 학습되었다. 기울기 비율 열을 보면, Post-LN의 레이어 간 기울기 불균형이 깊이에 비례하여 심화되는 반면 Pre-LN은 거의 일정하게 유지됨을 확인할 수 있다.

소규모 IWSLT 과제뿐 아니라 대규모 WMT En-De 번역 과제에서도 동일한 패턴이 관찰된다. Pre-LN(웜업 없음)은 WMT 과제에서도 Post-LN(웜업 포함)과 대등한 최종 성능(BLEU 약 26~27)에 도달하며, 초기 수렴 속도에서는 오히려 우위를 보였다.

다양한 학습률과 웜업 설정의 조합에서 최종 성능을 비교한 아래 그림은 Pre-LN이 하이퍼파라미터 선택에 훨씬 강건함을 정량적으로 보여준다.

![IWSLT14 De-En 번역 과제에서 다양한 학습률과 웜업 설정의 최종 성능 비교](figures/fig_19.png)
*IWSLT14 De-En 과제 최종 성능 비교. Pre-LN은 넓은 학습률 범위(1e-4~1e-3)에서 안정적인 검증 손실과 BLEU를 유지하는 반면, Post-LN은 웜업 스텝과 학습률 조합에 매우 민감하게 반응한다. Pre-LN이 하이퍼파라미터 튜닝 부담을 크게 줄임을 정량적으로 보여준다. (Xiong et al., 2020)*

### 언어 모델링 (WikiText-103)

| 설정 | Perplexity | 학습 안정성 |
|------|-----------|------------|
| Post-LN (16L) + 웜업 | 18.7 | 안정 |
| Post-LN (16L) + 웜업 없음 | 발산 | 실패 |
| Pre-LN (16L) + 웜업 없음 | 18.9 | 안정 |
| Pre-LN (16L) + 웜업 | 18.6 | 안정 |

Pre-LN 트랜스포머는 동일한 파라미터 수에서 Post-LN과 비슷하거나 약간 더 높은 perplexity를 기록하면서도, 학습 안정성은 현저히 향상되었다. 특히 학습률 웜업 없이도 학습이 발산하지 않고 수렴하는 것이 핵심 장점으로 부각되었다. Pre-LN + 웜업 조합이 가장 낮은 perplexity를 기록했으며, 이는 웜업이 Pre-LN에서도 약간의 추가 이점을 줄 수 있음을 시사한다.

번역 과제를 넘어 BERT 사전학습에서도 Pre-LN의 수렴 속도 우위가 확인된다. 아래 그림은 BERT 모델의 사전학습 검증 손실을 비교한 것으로, Pre-LN이 전 구간에 걸쳐 Post-LN보다 낮은 손실을 유지하며 더 빠르게 수렴함을 보여준다.

![BERT 사전학습에서 Pre-LN과 Post-LN의 검증 손실 수렴 비교](figures/fig_16.png)
*BERT 사전학습 검증 손실 비교. Pre-LN(주황, 실선)이 100K 스텝부터 1M 스텝까지 전 구간에서 Post-LN(파랑, 점선)보다 일관되게 낮은 검증 손실을 기록한다. Pre-LN은 학습 초기(100K~300K)에 이미 Post-LN의 500K 스텝 수준의 손실에 도달하여, 사전학습 비용을 크게 절감할 수 있음을 시사한다. (Xiong et al., 2020)*

### 기울기 분포 시각화

논문에서는 학습 초기(1K 스텝)의 기울기 크기를 레이어별로 시각화하여:

- **Post-LN**: 하위 레이어의 기울기가 상위 레이어보다 **수십 배** 이상 크게 나타남. 레이어 1의 기울기 norm이 레이어 6의 약 20~50배에 달했다. 인코더와 디코더 모두에서 동일한 패턴이 관찰되었다.
- **Pre-LN**: 모든 레이어에서 기울기 크기가 **균일**하게 유지됨. 레이어 간 기울기 norm의 비율이 대부분 1.0~1.5 범위 내에 있었다.

이 시각화는 이론적 분석을 직접적으로 뒷받침하는 강력한 경험적 증거이다.

### 학습 속도 비교

Pre-LN은 웜업이 불필요하므로 학습 초기부터 높은 학습률을 사용할 수 있어, 동일한 최종 성능에 도달하는 wall-time이 **약 40% 이상 단축**되는 것으로 보고되었다. 이는 대규모 모델 학습에서 상당한 비용 절감을 의미한다.

학습 곡선을 비교하면, Post-LN은 웜업 구간(수천 스텝) 동안 매우 느리게 학습이 진행되다가 웜업 종료 후 급격히 수렴하는 패턴을 보인다. 반면 Pre-LN은 학습 시작부터 일정한 속도로 손실이 감소하여, 전체적으로 더 효율적인 학습 궤적을 보인다.

## 의의 및 한계

### 의의

- **현대 LLM 아키텍처의 표준화**: 이 논문의 결과를 바탕으로 GPT-3(Brown et al., 2020), PaLM(Chowdhery et al., 2022), LLaMA(Touvron et al., 2023) 등 거의 모든 현대 대규모 언어 모델이 Pre-LN 구조를 채택하였다. [[gpt-3]]에서 Pre-LN이 명시적으로 사용되었으며, 이후 모든 GPT 계열 모델이 이를 따랐다.
- **하이퍼파라미터 튜닝 간소화**: 웜업 스케줄에 대한 의존성이 줄어들어, 학습 파이프라인이 단순해졌다. 웜업 스텝 수를 결정하는 것은 실무에서 상당히 번거로운 작업이었으며, 모델 크기, 데이터셋 크기, 배치 크기에 따라 최적값이 달라지기 때문이다.
- **이론적 기반 제공**: 단순한 경험적 관찰을 넘어 수학적 증명을 통해 설계 선택을 정당화하였다는 점에서 학문적 가치가 크다. 이는 "왜 이렇게 하는가?"라는 근본적 질문에 대한 답을 제공한다.
- **깊은 트랜스포머의 실현**: Pre-LN 덕분에 96 레이어(GPT-3), 120 레이어 등 매우 깊은 트랜스포머의 안정적 학습이 가능해졌다. 이는 모델 스케일링 법칙(scaling law) 연구의 토대가 되었다.

### 한계

- **표현력 차이**: 일부 연구에서는 Pre-LN이 Post-LN에 비해 표현력(representational capacity)이 약간 낮을 수 있다는 주장도 있다. Post-LN은 각 레이어의 출력이 정규화되므로 더 깊은 레이어가 더 정제된 표현을 학습하는 데 유리할 수 있다. Pre-LN에서는 잔차 합산이 정규화 없이 누적되므로, 깊은 레이어에서 은닉 상태의 크기가 점진적으로 증가하는 "representation collapse" 현상이 관찰되기도 한다.
- **RMS Norm과의 관계**: 이후 연구에서는 LayerNorm을 더 경량화한 RMSNorm(Zhang & Sennrich, 2019)이 제안되었다:

$$\text{RMSNorm}(x) = \frac{x}{\text{RMS}(x)} \cdot g, \quad \text{RMS}(x) = \sqrt{\frac{1}{n}\sum_{i=1}^n x_i^2}$$

RMSNorm은 mean centering($x - \mu$ 연산)을 제거하여 계산량을 약 10~15% 줄이면서도 유사한 정규화 효과를 제공한다. LLaMA, Mistral 등 현대 모델은 Pre-LN + RMSNorm 조합을 사용한다.

| 정규화 방법 | 연산량 | 파라미터 수 | 성능 차이 | 대표 모델 |
|------------|--------|-----------|----------|----------|
| LayerNorm | $O(d)$ | $2d$ ($\gamma, \beta$) | 기준선 | BERT, GPT-2 |
| RMSNorm | $O(d)$ (약간 적음) | $d$ ($g$만) | 거의 동등 | LLaMA, Mistral |
| GroupNorm | $O(d)$ | $2G$ | 태스크 의존 | Vision Transformer |

- **분석의 단순화 가정**: 이론적 분석이 선형 어텐션과 같은 단순화된 모델을 기반으로 하여, 실제 비선형 트랜스포머에 대한 완전한 이론적 설명은 아직 미완이다. softmax 어텐션의 비선형성, multi-head의 상호작용, dropout의 효과 등은 분석에서 제외되었다.
- **최적성 보장 부재**: Pre-LN이 안정적이라는 것이 최적이라는 것을 의미하지는 않는다. 학습이 수렴한다고 해서 반드시 최고 성능에 도달하는 것은 아니며, 적절한 불안정성이 더 나은 local minimum을 찾는 데 도움이 될 수도 있다.

### 후속 연구의 흐름

이 논문을 기점으로 트랜스포머 정규화 위치에 대한 활발한 후속 연구가 이어졌다:

| 방법 | 구조 | 특징 | 대표 모델 | 연도 |
|------|------|------|----------|------|
| Post-LN | LN(x + F(x)) | 표현력 우수, 학습 불안정 | 원래 Transformer, BERT | 2017 |
| Pre-LN | x + F(LN(x)) | 학습 안정, 표현력 약간 저하 | GPT-3, LLaMA, PaLM | 2020 |
| Sandwich-LN | LN(x + LN(F(LN(x)))) | 안정성+표현력 절충 | CogView | 2021 |
| DeepNorm | $x \cdot \alpha + F(\text{LN}(x))$ | 1000 레이어 이상 안정 학습 | GLM-130B | 2022 |
| QK-Norm | Pre-LN + QK정규화 | 어텐션 logit 안정화 | ViT-22B | 2023 |
| **Peri-LN** | LN(x) + F(LN(x)) | 안정성+표현력 동시 달성 | (연구 단계) | 2025 |

DeepNorm은 잔차 연결에 스케일링 계수 $\alpha$를 도입하여 초기화를 조정하는 방식으로 1,000 레이어 이상의 트랜스포머도 안정적으로 학습할 수 있음을 보였다. $\alpha = (2L)^{1/4}$로 설정하고 서브레이어의 가중치를 $\beta = (8L)^{-1/4}$로 스케일링하면 기울기가 깊이에 무관하게 $O(1)$로 유지된다.

## 코드 예제

### Post-LN Transformer 레이어

원래 Transformer(Vaswani et al., 2017) 구조로, Add 후 LayerNorm을 적용한다. 하위 레이어 기울기 폭발 문제가 있다.

```python
import torch
import torch.nn as nn
import math

class PostLNTransformerLayer(nn.Module):
    """Post-LN: 원래 Transformer (Vaswani et al., 2017) 구조.
    문제: 깊은 네트워크에서 하위 레이어 기울기 폭발.
    """
    def __init__(self, d_model=512, n_heads=8, d_ff=2048, dropout=0.1):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff), nn.ReLU(), nn.Linear(d_ff, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # Post-LN: Add -> Norm
        attn_out, _ = self.self_attn(x, x, x)
        x = self.norm1(x + self.dropout(attn_out))  # LN이 잔차 합산 이후
        ffn_out = self.ffn(x)
        x = self.norm2(x + self.dropout(ffn_out))    # LN이 잔차 합산 이후
        return x

```

### Pre-LN Transformer 레이어

LayerNorm을 서브레이어 전에 적용하는 구조로, 기울기가 균일하여 웜업 없이도 안정적으로 학습된다.

```python
class PreLNTransformerLayer(nn.Module):
    """Pre-LN: Xiong et al. (2020) 구조.
    장점: 기울기가 레이어 전반에 걸쳐 균일, 웜업 불필요.
    """
    def __init__(self, d_model=512, n_heads=8, d_ff=2048, dropout=0.1):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff), nn.ReLU(), nn.Linear(d_ff, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # Pre-LN: Norm -> Sublayer -> Add
        normed = self.norm1(x)
        attn_out, _ = self.self_attn(normed, normed, normed)
        x = x + self.dropout(attn_out)   # 잔차 경로가 LN을 우회
        normed = self.norm2(x)
        ffn_out = self.ffn(normed)
        x = x + self.dropout(ffn_out)    # 잔차 경로가 LN을 우회
        return x

```

### DeepNorm Transformer 레이어

잔차 연결에 alpha 스케일링을 적용하여 1000+ 레이어에서도 안정적 학습을 가능하게 하는 구조이다.

```python
class DeepNormTransformerLayer(nn.Module):
    """DeepNorm: 1000+ 레이어도 안정적으로 학습 가능.
    핵심: 잔차 연결에 alpha 스케일링, 가중치에 beta 스케일링.
    """
    def __init__(self, d_model=512, n_heads=8, d_ff=2048,
                 dropout=0.1, alpha=1.0, beta=1.0):
        super().__init__()
        self.alpha = alpha
        self.self_attn = nn.MultiheadAttention(d_model, n_heads, batch_first=True)
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff), nn.ReLU(), nn.Linear(d_ff, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        # 가중치 초기화 스케일링
        self._init_weights(beta)

    def _init_weights(self, beta):
        for module in [self.self_attn, self.ffn]:
            for p in module.parameters():
                if p.dim() > 1:
                    nn.init.xavier_normal_(p)
                    p.data *= beta  # beta 스케일링

    def forward(self, x):
        normed = self.norm1(x)
        attn_out, _ = self.self_attn(normed, normed, normed)
        x = x * self.alpha + self.dropout(attn_out)  # alpha 스케일링
        normed = self.norm2(x)
        ffn_out = self.ffn(normed)
        x = x * self.alpha + self.dropout(ffn_out)    # alpha 스케일링
        return x

```

### 기울기 분포 비교

Post-LN / Pre-LN / DeepNorm 세 구조의 레이어별 기울기 크기를 직접 비교하는 실험 코드이다.

```python
def compare_gradient_norms(n_layers=12, d_model=256, seq_len=32, batch=4):
    """Post-LN vs Pre-LN vs DeepNorm의 레이어별 기울기 크기 비교."""
    alpha = (2 * n_layers) ** 0.25
    beta = (8 * n_layers) ** (-0.25)
    results = {}
    for name, LayerClass, kwargs in [
        ('Post-LN', PostLNTransformerLayer, {}),
        ('Pre-LN', PreLNTransformerLayer, {}),
        ('DeepNorm', DeepNormTransformerLayer, {'alpha': alpha, 'beta': beta}),
    ]:
        layers = nn.ModuleList([
            LayerClass(d_model=d_model, n_heads=4, d_ff=d_model*4, **kwargs)
            for _ in range(n_layers)
        ])
        x = torch.randn(batch, seq_len, d_model, requires_grad=True)
        h = x
        for layer in layers:
            h = layer(h)
        loss = h.sum()
        loss.backward()

        grad_norms = []
        for i, layer in enumerate(layers):
            total_norm = 0
            for p in layer.parameters():
                if p.grad is not None:
                    total_norm += p.grad.norm().item() ** 2
            grad_norms.append(math.sqrt(total_norm))
        results[name] = grad_norms
        print(f"\n{name} 기울기 norm (레이어 1~{n_layers}):")
        for i, gn in enumerate(grad_norms):
            bar = '=' * int(gn / max(grad_norms) * 30)
            print(f"  Layer {i+1:2d}: {gn:8.2f} {bar}")

    # 기울기 불균형 정도
    print(f"\n기울기 불균형 (Layer 1 / Layer {n_layers}):")
    for name in results:
        ratio = results[name][0] / max(results[name][-1], 1e-8)
        print(f"  {name:10s}: {ratio:.2f}x")

compare_gradient_norms(n_layers=12)
```

> **핵심 통찰**: 위 코드를 실행하면 Post-LN에서 하위 레이어(Layer 1)의 기울기가 상위 레이어(Layer 12)보다 수배~수십배 큰 반면, Pre-LN에서는 모든 레이어의 기울기가 비교적 균일한 것을 확인할 수 있다. DeepNorm은 Pre-LN과 유사하게 균일한 기울기를 유지하면서도 잔차 스케일링을 통해 더 깊은 모델에서도 안정성을 보장한다. 이 간단한 실험이 논문의 핵심 주장을 직접적으로 검증한다. Pre-LN은 단순히 LayerNorm의 위치를 한 줄 바꾸는 것이지만, 그 효과는 수백 레이어 모델의 학습 성공 여부를 결정할 만큼 극적이다.

### 실무 적용 가이드

정규화 위치 선택 시 실무적 지침을 정리하면 다음과 같다:

1. **기본 선택**: Pre-LN을 기본으로 사용한다. 대부분의 경우 충분한 성능과 안정성을 제공한다.
2. **깊은 모델 (24+ 레이어)**: Pre-LN 또는 DeepNorm을 권장한다. Post-LN은 깊은 모델에서 학습 실패 위험이 높다.
3. **최고 성능 추구**: Post-LN + 충분한 웜업 조합이 약간 더 나은 최종 성능을 보일 수 있으나, 학습 비용과 하이퍼파라미터 민감도를 고려해야 한다.
4. **최종 LN 추가**: Pre-LN 사용 시 모델 최종 출력에 별도의 LayerNorm을 반드시 추가해야 한다. 이를 빠뜨리면 출력의 스케일이 레이어 수에 따라 증가하여 성능이 저하된다.
5. **RMSNorm 활용**: 계산 효율이 중요한 대규모 모델에서는 LayerNorm 대신 RMSNorm을 사용하는 것이 효과적이다.