## 개요

Mixture-of-Experts(MoE)는 모델의 전체 파라미터 수를 대폭 늘리면서도 각 입력에 대해 실제로 활성화되는 연산량은 고정 수준으로 유지하는 **희소(sparse) 확장 전략**이다. 각 입력 토큰이 전체 전문가(expert) 중 단 하나만 활성화하므로, 파라미터 수가 극적으로 증가하더라도 학습 및 추론 시의 FLOPs는 거의 늘어나지 않는다.

그러나 기존 MoE 방식(Shazeer et al., 2017)은 Top-2 라우팅의 복잡성, 학습 불안정성, 전문가 간 부하 불균형 등 심각한 실용적 한계를 안고 있었다. Fedus, Zoph, Shazeer가 JMLR 2022에 발표한 **Switch Transformers**는 이러한 한계를 체계적으로 극복하고, 최초로 조 단위($10^{12}$) 파라미터 규모의 언어 모델을 성공적으로 학습하였다.

Switch Transformers의 핵심 기여는 다음과 같다:

1. **Switch(Top-1) 라우팅**: 각 토큰을 단 하나의 전문가에게만 라우팅하여 설계를 극적으로 단순화하고 통신 비용을 절감한다.
2. **보조 로드 밸런싱 손실**: 전문가 간 균등한 토큰 분배를 유도하는 미분 가능한 보조 손실 함수를 도입한다.
3. **학습 안정성 기법**: 전문가별 가중치 초기화 스케일링, bf16 혼합 정밀도, 선택적 fp32 적용 등으로 학습 발산을 방지한다.
4. **T5 대비 7배 속도 향상**: 동일 학습 FLOPs에서 Switch Transformer는 T5-Base보다 7배 빠르게 동일 품질에 도달한다.
5. **1.6조 파라미터 모델**: Switch Transformer-1.6T(2048개 전문가)를 학습하여 희소 모델 스케일링의 실용성을 입증한다.

이 논문의 영향은 단순히 모델 크기의 기록을 세운 것에 그치지 않는다. Switch Transformers는 MoE 아키텍처의 설계 원칙을 정립하여, 이후 등장한 [[GLaM]], [[ST-MoE]], [[Mixtral]], [[DeepSeek-MoE]], Grok, DBRX 등 거의 모든 현대 MoE 모델의 설계적 기반이 되었다.

---

## 배경 및 문제

### 밀집 모델의 스케일링 한계

트랜스포머의 [[Scaling Law|스케일링 법칙]]에 따르면, 모델 성능은 파라미터 수, 학습 데이터, 학습 연산량의 멱법칙(power law)으로 향상된다. 그러나 밀집(dense) 모델에서는 파라미터 수를 늘리면 모든 입력에 대해 모든 파라미터가 활성화되므로, 파라미터 수 증가가 곧 연산량 증가를 의미한다. 파라미터를 10배 늘리면 연산량도 대략 10배 증가하여 하드웨어 비용이 선형적으로 상승한다.

Chinchilla 연구(Hoffmann et al., 2022)는 학습 토큰 수와 모델 크기의 최적 비율을 제시하였지만, 이 프레임워크 내에서도 더 큰 모델은 더 많은 학습 연산을 필요로 한다. 연산 예산이 고정된 상황에서 "동일한 FLOPs로 더 나은 성능"을 달성하려면, 파라미터 수와 연산량을 분리(decouple)하는 새로운 접근이 필요하다.

### 조건부 연산(Conditional Computation)과 MoE의 원리

조건부 연산은 입력에 따라 모델의 일부만 활성화하는 패러다임이다. MoE는 이 패러다임의 대표적 구현으로, Jacobs et al.(1991)이 처음 제안하고 Shazeer et al.(2017)이 심층 신경망에 적용하였다.

MoE의 핵심 원리는 다음과 같다:

- 하나의 레이어에 $N$개의 **전문가(expert)** 네트워크를 배치한다.
- **라우터(router)** 네트워크가 각 입력 토큰을 적절한 전문가에게 라우팅한다.
- 각 토큰은 $N$개 중 소수의 전문가만 활성화하므로, 전체 파라미터 대비 활성화 파라미터가 희소(sparse)하다.

수학적으로 표현하면, 전체 출력은 다음과 같이 계산된다:

$$y = \sum_{i=1}^{N} g_i(x) \cdot E_i(x)$$

여기서 $g_i(x)$는 게이팅 함수(gating function)이며, $E_i(x)$는 $i$번째 전문가의 출력이다. Dense 모델에서 하나의 FFN이 처리하던 작업을 $N$개의 전문가가 나누어 처리하되, 라우터가 각 토큰에 가장 적합한 전문가를 선택하는 구조이다.

### 기존 MoE(Top-2)의 문제점

Shazeer et al.(2017)의 MoE는 각 토큰을 Top-2 전문가에게 라우팅한다. 이 설계에는 다음과 같은 핵심 문제가 있었다.

**통신 비용 과다**: 분산 학습에서 전문가가 서로 다른 디바이스에 배치될 때, 각 토큰이 2개의 전문가에게 전달되어야 하므로 All-to-All 통신량이 2배가 된다. GPU/TPU 클러스터에서 디바이스 간 통신은 연산보다 훨씬 느리므로, 이 통신 오버헤드가 전체 학습 속도의 병목이 된다.

**전문가 붕괴(Expert Collapse)**: 학습 초기에 특정 전문가가 우연히 더 나은 출력을 생성하면, 라우터가 점점 더 많은 토큰을 해당 전문가에게 보내는 양의 피드백 루프(positive feedback loop)가 형성된다. 결국 소수의 전문가만 활용되고 나머지는 학습되지 않는 붕괴 현상이 발생한다.

**학습 불안정성**: 모델 규모가 커질수록 학습 중 손실이 갑자기 발산(diverge)하는 현상이 빈번하게 관찰되었다. 특히 fp16 혼합 정밀도 학습에서 라우팅 확률의 수치적 불안정이 발산의 주요 원인으로 지목되었다.

**구현 복잡성**: 분산 학습 환경에서 전문가 병렬(Expert Parallelism)을 구현하려면 정교한 통신 패턴과 부하 분산 로직이 필요하며, 이는 연구자들의 진입 장벽을 높였다.

Switch Transformers는 이러한 문제들을 체계적으로 해결하며, MoE의 실용성을 크게 향상시킨다.

---

## 핵심 아이디어

Switch Transformers의 핵심 아이디어는 **"단순화를 통한 확장(scaling through simplification)"**이다. 기존 MoE의 Top-2 라우팅이 이론적으로 더 풍부한 표현력을 갖는다고 여겨졌지만, 실제로는 추가적인 복잡성(통신 비용, 학습 불안정)이 이론적 이점을 상쇄한다.

Switch Transformers는 다음 가설을 제시한다: **각 토큰을 단 하나의 전문가에게만 라우팅(Top-1)하더라도, 전문가 수를 충분히 늘리면 Top-2 이상의 성능을 달성할 수 있다.** 이 가설은 실험적으로 일관되게 검증되었으며, 단순화로 얻은 효율성 이점이 표현력의 이론적 손실을 압도한다는 것을 보여준다.

Top-1 라우팅의 장점을 정리하면 다음과 같다:

- **통신 비용 절반**: 분산 환경에서 각 토큰이 하나의 디바이스로만 이동하므로 통신량이 절반으로 줄어든다.
- **연산량 절감**: 각 토큰에 대해 FFN을 하나만 실행하므로, 같은 계산 예산으로 더 많은 전문가를 배치할 수 있다.
- **설계 단순성**: 두 전문가의 출력을 가중 합하는 로직이 불필요해져 구현이 간결해진다.
- **용량 효율성**: 같은 FLOPs 예산에서 더 많은 전문가를 사용할 수 있어 모델의 전체 용량이 증가한다.

스케일링 관점에서 보면, Dense 모델에서 파라미터를 $k$배 늘리면 FLOPs도 $k$배 증가하지만, Switch Transformer에서는 전문가 수를 $k$배 늘려도 각 토큰의 FLOPs는 동일하게 유지된다. 이는 [[Scaling Law]]에서 파라미터 축(parameter axis)만을 효율적으로 확장하는 것에 해당한다.

---

## 방법론

### Switch 라우팅 메커니즘

![Switch Transformer 인코더 블록 구조 - 라우터가 각 토큰을 단일 전문가 FFN으로 라우팅](figures/fig_2.png)
*Figure 2: Switch Transformer 인코더 블록. 표준 Transformer의 밀집 FFN 레이어를 희소 Switch FFN 레이어로 교체한다. 라우터가 각 토큰("More", "Parameters")을 독립적으로 4개 전문가 중 하나로 라우팅하며, 선택된 전문가의 출력에 라우터 게이트 값을 곱하여 최종 출력을 생성한다.*

Switch Transformer는 표준 [[Transformer]]의 FFN(Feed-Forward Network) 레이어를 MoE 레이어로 교체한다. 셀프 어텐션 레이어는 변경하지 않는다. $N$개의 전문가 FFN $\{E_1, E_2, \ldots, E_N\}$이 있고, 학습 가능한 라우터 가중치 $W_r \in \mathbb{R}^{d_{\text{model}} \times N}$이 각 토큰 $x \in \mathbb{R}^{d_{\text{model}}}$를 어느 전문가에게 보낼지 결정한다.

먼저 라우터가 각 전문가에 대한 확률을 계산한다:

$$p_i(x) = \frac{\exp(x \cdot w_r^{(i)})}{\sum_{j=1}^{N} \exp(x \cdot w_r^{(j)})}, \quad i = 1, \ldots, N$$

여기서 $w_r^{(i)}$는 $W_r$의 $i$번째 열 벡터이다. 그런 다음 확률이 가장 높은 전문가 하나를 선택한다:

$$i^* = \arg\max_{i \in \{1, \ldots, N\}} \, p_i(x)$$

최종 출력은 선택된 전문가의 출력에 해당 라우팅 확률을 곱한 값이다:

$$y = p_{i^*}(x) \cdot E_{i^*}(x)$$

여기서 $p_{i^*}(x)$를 곱하는 이유는 두 가지이다. 첫째, 라우터의 확신도(confidence)를 반영하여 출력의 크기를 조절한다. 둘째, $p_{i^*}(x)$를 통해 라우터 가중치 $W_r$로 그래디언트가 전달되므로 라우터의 학습이 가능해진다. $\arg\max$ 연산 자체는 미분 불가능하지만, 선택된 전문가의 확률값을 곱함으로써 라우팅 결정에 대한 간접적인 그래디언트 경로가 형성된다.

### 전문가 용량(Expert Capacity) 관리

![토큰 라우팅 동작과 전문가 용량 계수에 따른 오버플로우 및 패딩](figures/fig_3.png)
*Figure 3: 전문가 용량(Capacity Factor)에 따른 토큰 라우팅 동작. 각 전문가는 (총 토큰 수 / 전문가 수) x 용량 계수만큼의 고정 배치를 처리한다. 용량을 초과하면 토큰이 드롭(점선 빨간색)되고, 용량 계수가 클수록 오버플로우는 줄지만 패딩으로 인한 연산 낭비가 증가한다.*

분산 학습 환경에서 각 전문가는 서로 다른 디바이스(TPU/GPU)에 배치된다. 효율적인 배치 처리를 위해 각 전문가가 한 배치에서 처리할 수 있는 토큰 수에 **용량 제한(capacity limit)**을 둔다:

$$C = \left\lfloor \frac{T}{N} \times c \right\rfloor$$

여기서 $T$는 배치 내 총 토큰 수, $N$은 전문가 수, $c$는 **용량 계수(capacity factor)**이다. 균등 분배 시 각 전문가에 $T/N$개의 토큰이 할당되므로, $c$는 이 기준 대비 얼마나 여유를 둘지를 결정한다.

- $c = 1.0$: 균등 분배만큼만 허용 (토큰 드롭 가능성 높음)
- $c = 1.25$: 25% 여유 (논문의 권장 기본값)
- $c = 2.0$: 100% 여유 (드롭 적지만 메모리 사용량 증가)

특정 전문가에 $C$개를 초과하는 토큰이 라우팅되면, 초과분은 **오버플로우(overflow)**되어 해당 전문가를 거치지 않는다. 오버플로우된 토큰은 잔차 연결(residual connection)을 통해 그대로 다음 레이어로 전달된다. 이 설계는 하드웨어 효율성과 모델 품질 간의 균형을 맞추는 역할을 한다.

용량 계수의 선택은 연산 효율과 토큰 처리율 사이의 트레이드오프이다. $c$가 크면 오버플로우가 줄어들어 더 많은 토큰이 처리되지만, 각 전문가에 할당된 메모리와 연산 예산이 증가한다. $c$가 작으면 효율적이지만 오버플로우로 인한 정보 손실이 커진다.

### 로드 밸런싱 보조 손실

라우터가 자유롭게 학습되면, 초기에 우연히 좋은 성능을 보인 소수의 전문가에게 토큰이 집중되는 **전문가 붕괴(expert collapse)** 현상이 발생한다. 이를 방지하기 위해 메인 학습 손실에 보조 로드 밸런싱 손실을 추가한다:

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{main}} + \alpha \cdot \mathcal{L}_{\text{aux}}$$

보조 손실은 다음과 같이 정의된다:

$$\mathcal{L}_{\text{aux}} = N \cdot \sum_{i=1}^{N} f_i \cdot P_i$$

여기서 각 항의 의미는 다음과 같다:

- $f_i$: 전문가 $i$에 실제로 라우팅된 토큰의 비율 (dispatch fraction)

$$f_i = \frac{1}{T} \sum_{x \in \mathcal{B}} \mathbf{1}[\arg\max_j \, p_j(x) = i]$$

- $P_i$: 전문가 $i$에 대한 소프트 라우팅 확률의 배치 평균 (routing probability)

$$P_i = \frac{1}{T} \sum_{x \in \mathcal{B}} p_i(x)$$

- $\alpha$: 보조 손실 가중치 (hyperparameter, 논문에서는 $\alpha = 10^{-2}$ 사용)
- $N$: 전문가 수 (정규화를 위한 스케일링 상수)

이 손실의 직관은 다음과 같다. 모든 전문가에 균등하게 토큰이 분배되면 $f_i = P_i = 1/N$이 되어 $\mathcal{L}_{\text{aux}} = N \cdot N \cdot (1/N)^2 = 1$이 최솟값이 된다. 반면 특정 전문가 $k$에 토큰이 집중되면 $f_k \approx 1, P_k \approx 1$이 되어 $\mathcal{L}_{\text{aux}} \approx N$으로 최대화된다. 따라서 이 손실을 최소화하면 균등 분배가 달성된다.

중요한 점은 $f_i$가 $\arg\max$를 포함하므로 미분 불가능하다는 것이다. 그러나 $P_i$는 소프트맥스 기반이므로 미분 가능하며, 이를 통해 라우터 가중치로 그래디언트가 전달된다. $f_i$는 그래디언트 계산에서 상수로 취급되어 현재 라우팅 불균형의 "신호"를 제공하는 역할을 한다.

### 전문가 병렬(Expert Parallelism)

![데이터·모델·전문가 병렬화 전략에서 가중치와 데이터 분할 방식 비교](figures/fig_9.png)
*Figure 9: 분산 학습을 위한 5가지 파티셔닝 전략. 상단은 모델 가중치의 코어별 분할 방식, 하단은 데이터 배치의 분할 방식을 보여준다. 전문가 병렬(Expert Parallelism)은 각 전문가를 별도 코어에 배치하여 파라미터 수를 크게 늘리면서도 코어당 메모리를 일정하게 유지한다.*

Switch Transformer는 대규모 학습을 위해 **전문가 병렬(Expert Parallelism)**을 활용한다. 이는 기존의 데이터 병렬(Data Parallelism) 및 모델 병렬(Model Parallelism)과 결합하여 사용된다.

전문가 병렬의 핵심은 $N$개의 전문가를 $D$개의 서로 다른 디바이스에 분산 배치하는 것이다(각 디바이스에 $N/D$개 전문가). 각 디바이스는 할당된 전문가만 보유하며, 토큰은 **All-to-All 통신** 패턴을 통해 해당 전문가가 위치한 디바이스로 전송된다.

전체 학습 과정의 통신 흐름은 다음과 같다:

1. 각 디바이스가 로컬 배치의 토큰에 대해 라우팅 확률을 계산한다.
2. All-to-All 통신으로 토큰을 올바른 전문가 디바이스로 전송한다.
3. 각 디바이스가 로컬 전문가로 토큰을 처리한다.
4. All-to-All 통신으로 처리된 토큰을 원래 디바이스로 반환한다.

Top-1 라우팅은 이 과정에서 각 토큰이 하나의 디바이스로만 이동하므로, Top-2 대비 통신량이 절반으로 감소한다. $D$개의 디바이스에서 통신 비용은 대략 $O(T \cdot d_{\text{model}} / D)$이며, Top-2에서는 이것이 2배가 된다. 이는 대규모 클러스터에서의 학습 효율성을 크게 향상시킨다.

**데이터 병렬과의 결합**: 비전문가 레이어(어텐션, 임베딩 등)는 모든 디바이스에 복제되어 표준 데이터 병렬로 처리된다. 전문가 레이어에서만 All-to-All 통신이 발생하므로, 전체 통신 오버헤드가 모델 병렬(매 레이어마다 All-Reduce 필요)보다 효율적이다.

### 학습 안정성 기법

MoE 모델의 학습 불안정성은 오랫동안 알려진 문제이다. Switch Transformers는 세 가지 기법을 조합하여 이 문제를 완화한다.

**1. 선택적 혼합 정밀도(Selective Precision)**

대부분의 연산은 bf16(Brain Float 16)으로 수행하되, 수치적으로 민감한 부분은 fp32로 처리한다. 구체적으로:

- 라우터의 소프트맥스 계산: fp32
- 보조 손실 계산: fp32
- 전문가 FFN 연산: bf16
- 어텐션 연산: bf16

bf16은 fp16과 같은 16비트 부동소수점이지만, 지수부(exponent)가 8비트로 fp32와 동일하여 표현 가능한 수의 범위가 넓다. 이로 인해 fp16에서 자주 발생하는 오버플로우/언더플로우 문제가 크게 완화된다.

| 정밀도 | 비트 | 지수부 | 가수부 | 표현 범위 |
|--------|------|--------|--------|----------|
| fp32 | 32 | 8 | 23 | $\pm 3.4 \times 10^{38}$ |
| fp16 | 16 | 5 | 10 | $\pm 6.5 \times 10^{4}$ |
| bf16 | 16 | 8 | 7 | $\pm 3.4 \times 10^{38}$ |

라우팅 확률의 미세한 차이가 어떤 전문가를 선택할지를 결정하므로, 이 부분에서의 수치 정밀도가 학습 안정성에 결정적이다.

**2. 전문가 초기화 스케일링**

전문가 FFN의 가중치를 초기화할 때, 표준 트랜스포머의 초기화 분산을 스케일링 계수로 나누어 조정한다:

$$W_{\text{expert}} \sim \mathcal{N}\left(0, \frac{\sigma^2}{s}\right)$$

여기서 $s$는 초기화 스케일링 계수이며, 논문에서는 $s = 10$을 사용한다. 이를 통해 전문가 수가 증가해도 MoE 레이어의 출력 분산이 안정적으로 유지된다.

**3. 차등 드롭아웃(Differential Dropout)**

MoE 모델은 파라미터 수가 많아 파인튜닝 시 과적합(overfitting) 위험이 있다. 이를 방지하기 위해 MoE 레이어(전문가 FFN)에만 더 높은 드롭아웃 비율을 적용하고, 비전문가 레이어(어텐션 등)에는 표준 드롭아웃을 유지하는 전략을 사용한다.

### Dense 모델로의 증류(Distillation)

논문에서는 학습된 대규모 Switch Transformer를 작은 Dense 모델로 **증류(distillation)**하는 방법도 제안한다. 이는 서빙 시 MoE 모델의 높은 메모리 요구사항을 완화하기 위한 전략이다. 저자들은 Switch-Base/128(7.4B 파라미터)를 T5-Base(223M 파라미터) 크기의 Dense 모델로 증류했을 때, 원래 T5-Base 대비 약 30%의 품질 격차를 유지하면서도 학습 시간을 크게 절약할 수 있음을 보였다. 이는 MoE 모델이 학습 시에는 희소 구조의 이점을 활용하고, 서빙 시에는 증류를 통해 밀집 모델의 효율성을 취하는 하이브리드 전략의 가능성을 보여준다.

---

## 실험 결과

### 희소 모델 파라미터에 따른 스케일링

![전문가 수(파라미터 규모) 증가에 따른 테스트 손실 스케일링 곡선](figures/fig_1_1.png)
*Figure 1 (좌): 희소 모델 파라미터에 따른 테스트 손실 스케일링. 전문가 1개(dense)에서 256개까지 확장할 때 테스트 손실이 로그-선형적으로 감소한다. 동일 FLOPs 예산에서 전문가 수를 늘리는 것만으로 일관된 성능 향상을 달성한다.*

전문가 수를 체계적으로 변화시킨 실험에서, 성능은 전문가 수의 로그에 대해 대략적으로 선형적인 관계를 보인다:

$$\text{Perplexity} \propto -\beta \cdot \log N + C$$

| 전문가 수 ($N$) | 파라미터 수 | Neg. Log Perplexity 향상 |
|----------------|-----------|------------------------|
| 2 | ~400M | 기준 |
| 4 | ~800M | +0.05 |
| 8 | ~1.6B | +0.10 |
| 16 | ~3.2B | +0.14 |
| 32 | ~6.4B | +0.17 |
| 64 | ~12.8B | +0.19 |
| 128 | ~25.6B | +0.21 |
| 256 | ~51.2B | +0.22 |

전문가 수를 2배로 늘릴 때마다 일정량의 perplexity 감소를 얻지만, 256개 이상에서는 수익 체감(diminishing returns)이 뚜렷해진다. Dense 모델의 스케일링 법칙과 유사한 형태를 보이며, 이는 MoE 모델의 설계 시 자원 배분에 대한 실용적 지침을 제공한다.

### T5와의 사전학습 속도 비교

![Switch Transformer의 학습 속도 우위 - 64 전문가 모델이 T5-Base 대비 7배 빠르게 수렴](figures/fig_5.png)
*Figure 5: Switch Transformer의 학습 속도 우위. 32개 TPUv3 코어에서 동일 FLOPs로 학습 시, Switch-Base 64전문가 모델이 T5-Base와 동일한 품질에 1/7 시간 만에 도달하며, 이후에도 지속적으로 성능이 향상된다.*

동일한 FLOPs(계산량) 예산에서 Switch Transformer와 T5의 사전학습 속도를 비교한 결과이다:

| 모델 | 전문가 수 | 총 파라미터 | 활성 파라미터 | 동일 품질 도달 속도 |
|------|----------|------------|-------------|-------------------|
| T5-Base | - | 223M | 223M | 기준 (1x) |
| Switch-Base/8 | 8 | 1.1B | 223M | 3x |
| Switch-Base/32 | 32 | 3.7B | 223M | 5x |
| Switch-Base/128 | 128 | 7.4B | 223M | **7x** |
| T5-Large | - | 739M | 739M | 기준 (1x) |
| Switch-Large/128 | 128 | 26.3B | 739M | 4x |
| T5-XXL | - | 11B | 11B | 기준 (1x) |
| Switch-XXL/128 | 128 | 395B | 11B | 4x |

Switch-Base/128이 7.4B 파라미터를 가지지만 활성 파라미터는 T5-Base와 동일한 223M이라는 점이 핵심이다. 토큰당 연산량은 같으면서 7배 빠르게 동일 품질에 도달한다. 이는 MoE의 희소 파라미터가 밀집 파라미터보다 FLOPs당 더 많은 정보를 저장할 수 있음을 시사한다.

### 다운스트림 과제 성능 (SuperGLUE)

사전학습된 Switch Transformer를 SuperGLUE 벤치마크에서 파인튜닝한 결과이다:

| 모델 | 파라미터 | FLOPs/토큰 | SuperGLUE 점수 |
|------|---------|------------|---------------|
| T5-Base | 223M | 223M | 74.6 |
| Switch-Base/128 | 7.4B | 223M | 80.1 |
| T5-Large | 739M | 739M | 82.7 |
| Switch-Large/128 | 26.3B | 739M | 86.0 |
| T5-XXL | 11B | 11B | 89.3 |
| Switch-XXL/128 | 395B | 11B | 90.7 |

Switch-Base/128은 T5-Base와 동일한 연산량으로 5.5점 높은 SuperGLUE 점수를 달성한다. Switch-XXL/128은 T5-XXL보다 1.4점 높으며, 이는 MoE의 추가 파라미터가 다운스트림 태스크에서도 유의미한 이점을 제공함을 보여준다.

### 조(兆) 파라미터 모델: Switch-C

논문의 가장 상징적인 실험은 **Switch-C** 모델이다. 2048개의 전문가를 사용하여 1.6조($1.6 \times 10^{12}$) 파라미터에 도달하며, 각 전문가는 별도의 TPU 코어에 배치된다. 이 모델은 T5-XXL(11B)과 동일한 FLOPs/토큰을 사용하면서 사전학습 perplexity에서 4배 빠른 수렴을 보였다.

그러나 Switch-C의 학습에서는 안정성 문제가 더 두드러졌다. 학습 과정에서 여러 차례의 손실 스파이크(loss spike)가 관찰되었으며, 일부는 체크포인트 복구와 학습률 감소로 대응해야 했다. 이는 초대규모 MoE 학습의 실용적 한계를 보여주는 동시에, 안정화 기법의 중요성을 강조한다.

### 용량 계수(Capacity Factor)의 영향

용량 계수 $c$에 따른 성능 변화도 체계적으로 분석되었다:

| 용량 계수 ($c$) | 토큰 드롭 비율 | 품질 (Perplexity) | 학습 속도 |
|----------------|--------------|------------------|---------|
| 1.0 | ~10% | 보통 | 빠름 |
| 1.25 | ~2-3% | 좋음 | 보통 |
| 2.0 | <1% | 최고 | 느림 |

논문에서는 $c = 1.0 \sim 1.5$를 권장하며, $c = 1.25$가 품질과 효율성 간의 최적 균형점으로 보인다.

---

## 의의 및 한계

### 학술적 및 산업적 의의

**1. MoE 아키텍처의 실용화**

Switch Transformers 이전에 MoE는 이론적으로 매력적이지만 실용적으로 어려운 기술로 인식되었다. 이 논문은 Top-1 라우팅이라는 극단적 단순화와 체계적인 안정화 기법을 통해, MoE를 대규모 언어 모델 학습의 실용적 도구로 전환시켰다.

**2. 후속 MoE 모델의 설계 원칙 확립**

[[Mixtral]](Mistral AI)은 8개 전문가에 Top-2 라우팅을 사용하지만, Switch Transformers에서 확립된 보조 로드 밸런싱 손실과 용량 관리 메커니즘을 그대로 활용한다. [[DeepSeek-MoE]]는 세분화된 전문가(fine-grained experts)와 공유 전문가(shared experts)를 도입하지만, 기본 프레임워크는 Switch Transformers를 따른다. ST-MoE(Zoph et al., 2022)는 라우터 z-loss를 추가하여 안정성을 더욱 개선한다. 이처럼 현대 MoE 모델의 거의 모든 설계 결정이 이 논문에서 시작되었다.

**3. 파라미터-연산 분리 스케일링**

밀집 모델에서는 파라미터 수 = 연산량이었지만, MoE는 이 등식을 깨뜨린다. Switch Transformers는 이 분리가 실질적으로 유효함을 대규모 실험으로 증명하여, 스케일링 법칙의 새로운 차원을 열었다.

**4. 공정한 비교 프레임워크**

T5와 동일한 코드베이스(mesh-tensorflow), 동일한 데이터(C4), 동일한 학습 설정에서 비교하여 실험 결과의 신뢰성이 높다. 후속 연구에서 이 비교 프레임워크가 표준으로 인용된다.

### 한계점

**1. 학습 불안정성의 근본적 해결 부족**

논문에서 제안한 안정화 기법들은 경험적(heuristic) 수준의 해결책이다. 왜 MoE 모델이 불안정한지에 대한 이론적 분석이 부족하며, 제안된 기법들이 모든 규모와 설정에서 작동한다는 보장이 없다. 실제로 Switch-C 학습에서 여러 차례의 손실 스파이크가 관찰되었고, 이를 수동으로 체크포인트 복구해야 했다. 후속 연구인 ST-MoE에서 라우터 z-loss를 도입하여 이 문제를 부분적으로 완화하였다.

**2. 전문가 전문화(Specialization)의 불명확성**

이상적으로는 각 전문가가 서로 다른 유형의 입력(예: 특정 언어, 도메인, 구문 구조)을 담당해야 한다. 일부 분석에서 전문가가 특정 토큰 유형(구두점, 숫자, 특정 언어)에 약하게 전문화되는 것이 관찰되었지만, 명확한 의미적 분리가 이루어지지는 않으며 논문에서도 이에 대한 심층 분석이 제한적이다.

**3. 추론 시 메모리 요구사항**

각 토큰에 대해 활성화되는 파라미터는 적지만, 서빙 시 전체 전문가 가중치를 메모리에 올려두어야 한다. Switch-Base/128(7.4B 파라미터)은 활성화 파라미터가 ~223M에 불과하지만, 전체 모델을 로드하려면 약 15GB의 GPU 메모리가 필요하다. 이는 Dense 모델 대비 서빙 비용을 크게 증가시킨다. [[Mixtral]]-8x7B(46.7B 총 파라미터)를 단일 GPU에서 서빙하기 어려운 것도 같은 이유이다.

**4. 파인튜닝 시 과적합**

대규모 파라미터에도 불구하고, 파인튜닝 시에는 소규모 데이터셋에서 과적합이 발생하기 쉽다. 차등 드롭아웃 등의 정규화 기법이 제안되었지만, Dense 모델 대비 파인튜닝 안정성이 떨어지는 것은 여전한 과제이다.

**5. 토큰 드롭(Token Dropping) 문제**

용량 제한으로 인해 일부 토큰이 전문가를 거치지 못하고 드롭되는 문제는 근본적으로 해결되지 않는다. 드롭된 토큰은 잔차 연결만으로 전달되므로 정보 손실이 발생하며, 이는 특히 긴 시퀀스에서 문제가 될 수 있다.

**6. 로드 불균형의 잔존**

보조 손실에도 불구하고 학습 과정에서 완벽한 부하 균형이 달성되지 않는다. 특정 전문가에 토큰이 지속적으로 집중되는 현상이 관찰되며, 보조 손실의 가중치 $\alpha$를 키우면 균형은 개선되지만 메인 태스크 성능이 저하된다. 이 트레이드오프의 최적점을 찾는 것은 여전히 실험적 과정이다.

---

## 코드 예제

다음은 Switch Transformer의 핵심인 Switch 라우팅 메커니즘과 로드 밸런싱 손실을 PyTorch로 구현한 예제이다.

### Switch 라우터

각 토큰을 단일 전문가(Top-1)로 라우팅하는 Switch Router로, 전문가 용량 초과 시 토큰을 드롭한다.

```python

import torch
import torch.nn as nn
import torch.nn.functional as F


class SwitchRouter(nn.Module):
    """Switch(Top-1) 라우터: 각 토큰을 하나의 전문가에게 라우팅"""

    def __init__(self, d_model: int, num_experts: int):
        super().__init__()
        self.num_experts = num_experts
        # 라우터 가중치: 토큰 임베딩 -> 전문가별 점수
        self.w_router = nn.Linear(d_model, num_experts, bias=False)

    def forward(self, x: torch.Tensor):
        """
        Args:
            x: (batch_size, seq_len, d_model) 형태의 토큰 임베딩
        Returns:
            expert_idx: (batch_size, seq_len) 선택된 전문가 인덱스
            router_prob: (batch_size, seq_len) 선택된 전문가의 라우팅 확률
            router_probs: (batch_size, seq_len, num_experts) 전체 라우팅 확률
        """
        # fp32로 라우팅 계산 (수치 안정성)
        router_logits = self.w_router(x.float())
        router_probs = F.softmax(router_logits, dim=-1)

        # Top-1 선택
        expert_idx = torch.argmax(router_probs, dim=-1)  # (B, S)
        router_prob = router_probs.gather(
            dim=-1, index=expert_idx.unsqueeze(-1)
        ).squeeze(-1)  # (B, S)

        return expert_idx, router_prob, router_probs


```

### 로드 밸런싱 손실

전문가별 토큰 분포와 라우팅 확률 분포의 내적으로 부하 균형을 유도하는 보조 손실이다.

```python
def load_balancing_loss(
    router_probs: torch.Tensor,
    expert_idx: torch.Tensor,
    num_experts: int,
    alpha: float = 0.01
) -> torch.Tensor:
    """
    보조 로드 밸런싱 손실 계산
    L_aux = alpha * N * sum(f_i * P_i)

    Args:
        router_probs: (B, S, N) 소프트맥스 라우팅 확률
        expert_idx: (B, S) 각 토큰의 선택된 전문가 인덱스
        num_experts: 전문가 수 N
        alpha: 보조 손실 가중치
    """
    B, S, N = router_probs.shape
    T = B * S  # 총 토큰 수

    # f_i: 각 전문가에 실제 라우팅된 토큰 비율
    one_hot = F.one_hot(expert_idx, num_classes=num_experts).float()  # (B, S, N)
    f = one_hot.sum(dim=[0, 1]) / T  # (N,)

    # P_i: 각 전문가에 대한 소프트 라우팅 확률의 평균
    P = router_probs.sum(dim=[0, 1]) / T  # (N,)

    # 보조 손실: alpha * N * dot(f, P)
    loss = alpha * num_experts * (f * P).sum()
    return loss


```

### 전문가 FFN

각 전문가가 담당하는 독립적인 FFN 레이어로, 게이팅 값에 의해 가중합산된다.

```python
class ExpertFFN(nn.Module):
    """개별 전문가 FFN (표준 Transformer FFN과 동일 구조)"""

    def __init__(self, d_model: int, d_ff: int, dropout: float = 0.1):
        super().__init__()
        self.w1 = nn.Linear(d_model, d_ff)
        self.w2 = nn.Linear(d_ff, d_model)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.w2(self.dropout(F.relu(self.w1(x))))


```

### Switch MoE 레이어

라우터, 전문가 FFN, 로드 밸런싱 손실을 통합한 전체 Switch Transformer MoE 레이어와 사용 예시이다.

```python
class SwitchMoELayer(nn.Module):
    """Switch Transformer MoE 레이어"""

    def __init__(
        self,
        d_model: int,
        d_ff: int,
        num_experts: int,
        capacity_factor: float = 1.25,
        dropout: float = 0.1,
        alpha: float = 0.01
    ):
        super().__init__()
        self.num_experts = num_experts
        self.capacity_factor = capacity_factor
        self.alpha = alpha

        self.router = SwitchRouter(d_model, num_experts)
        self.experts = nn.ModuleList([
            ExpertFFN(d_model, d_ff, dropout)
            for _ in range(num_experts)
        ])
        self.layer_norm = nn.LayerNorm(d_model)

    def forward(self, x: torch.Tensor):
        """
        Args:
            x: (batch_size, seq_len, d_model)
        Returns:
            output: (batch_size, seq_len, d_model)
            aux_loss: 스칼라 보조 손실
        """
        residual = x
        x = self.layer_norm(x)
        B, S, D = x.shape
        T = B * S

        # 라우팅 결정
        expert_idx, router_prob, router_probs = self.router(x)

        # 보조 손실 계산
        aux_loss = load_balancing_loss(
            router_probs, expert_idx, self.num_experts, self.alpha
        )

        # 전문가 용량 계산
        capacity = int(T / self.num_experts * self.capacity_factor)

        # 각 전문가별 토큰 처리
        x_flat = x.view(T, D)
        idx_flat = expert_idx.view(T)
        prob_flat = router_prob.view(T)
        output = torch.zeros_like(x_flat)

        for i in range(self.num_experts):
            # 전문가 i에 라우팅된 토큰 마스크
            mask = (idx_flat == i)
            token_indices = mask.nonzero(as_tuple=True)[0]

            # 용량 제한 적용 (초과분 드롭)
            if len(token_indices) > capacity:
                token_indices = token_indices[:capacity]

            if len(token_indices) == 0:
                continue

            # 전문가 처리 + 라우팅 확률 곱셈
            expert_input = x_flat[token_indices]
            expert_output = self.experts[i](expert_input)
            output[token_indices] = (
                prob_flat[token_indices].unsqueeze(-1) * expert_output
            )

        output = output.view(B, S, D)
        return residual + output, aux_loss


# 사용 예시
if __name__ == "__main__":
    d_model = 768
    d_ff = 3072
    num_experts = 8
    batch_size = 4
    seq_len = 128

    moe_layer = SwitchMoELayer(
        d_model=d_model,
        d_ff=d_ff,
        num_experts=num_experts,
        capacity_factor=1.25
    )

    x = torch.randn(batch_size, seq_len, d_model)
    output, aux_loss = moe_layer(x)

    print(f"입력 shape: {x.shape}")
    print(f"출력 shape: {output.shape}")
    print(f"보조 손실: {aux_loss.item():.4f}")
    print(f"전체 파라미터: {sum(p.numel() for p in moe_layer.parameters()):,}")
    print(f"활성 파라미터 (1개 전문가): "
          f"{sum(p.numel() for p in moe_layer.experts[0].parameters()):,}")
```

위 코드에서 핵심적인 구현 포인트는 다음과 같다:

1. **라우터의 fp32 계산**: `x.float()`로 라우팅 시 fp32 정밀도를 사용하여 수치 안정성을 확보한다.
2. **용량 제한**: `token_indices[:capacity]`로 초과 토큰을 드롭하며, 드롭된 토큰은 잔차 연결을 통해 전달된다(`residual + output`에서 `output`이 0으로 유지).
3. **라우팅 확률 곱셈**: `prob_flat[token_indices].unsqueeze(-1) * expert_output`으로 라우터의 확신도를 반영하고 그래디언트를 전달한다.
4. **보조 손실**: `f`(hard assignment 비율)와 `P`(soft probability 평균)의 내적으로 로드 밸런싱을 유도한다.

실제 대규모 학습에서는 이 구현을 전문가 병렬(각 전문가를 별도 디바이스에 배치)과 결합하고, All-to-All 통신으로 토큰을 전송하는 분산 구현이 필요하다. Google의 mesh-tensorflow, Meta의 fairseq, Hugging Face의 transformers 라이브러리 등에서 이러한 분산 MoE 구현을 제공하고 있다.

---

## 관련 연구

- [[mixtral|Mixtral of Experts]] -- Top-2 라우팅을 사용하는 후속 오픈소스 MoE 아키텍처
- [[deepseek-v2|DeepSeek-V2]] -- 세분화된 전문가와 공유 전문가를 도입한 MoE 모델
- [[deepseek-v3|DeepSeek-V3]] -- MoE 스케일링의 최신 발전
- [[sparse-expert-models|A Review of Sparse Expert Models]] -- MoE 아키텍처 서베이
- [[scaling-laws|Scaling Laws for Neural Language Models]] -- Dense 모델의 스케일링 법칙