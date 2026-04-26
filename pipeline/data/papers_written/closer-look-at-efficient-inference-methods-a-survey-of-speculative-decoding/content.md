<!-- infographic-hero -->
![Closer Look at Efficient Inference Methods: A Survey of Speculative Decoding 핵심 요약](figures/infographic.svg)

*Figure: Closer Look at Efficient Inference Methods: A Survey of Speculative Decoding 한 장 요약 인포그래픽*

## 개요

"A Closer Look at Efficient Inference Methods: A Survey of Speculative Decoding"(Hyun Ryu & Eric Kim, 2024)은 대규모 언어 모델(LLM)의 추론 속도를 가속하는 핵심 기법인 **Speculative Decoding**(투기적 디코딩)에 대한 종합 서베이 논문입니다. 이 논문은 기존 서베이들과 차별화되는 독자적인 분류 체계를 제시합니다. 핵심은 speculative decoding 방법론을 **Draft-Centric**(초안 중심)과 **Model-Centric**(모델 중심)이라는 두 가지 축으로 분류하는 것입니다.

LLM의 autoregressive 디코딩은 본질적으로 순차적이며, 한 번에 하나의 토큰만 생성합니다. 이로 인해 GPU의 병렬 처리 능력을 충분히 활용하지 못하고, 추론 latency가 토큰 수에 비례하여 증가합니다. Speculative decoding은 이 병목을 해결하기 위해 "빠르게 초안을 작성하고, 한 번에 검증하는" 전략을 취합니다. 작은 모델(또는 효율적인 메커니즘)로 여러 토큰의 초안(draft)을 생성한 뒤, 원래의 대형 모델(target model)로 이를 병렬 검증하여 정확성을 유지하면서도 처리 속도를 2~3배 이상 향상시킵니다.

본 서베이는 2018년 Blockwise Parallel Decoding부터 2024년 중반까지의 약 30개 이상의 speculative decoding 기법을 시간순으로 정리하고, 각 기법의 핵심 아이디어와 상호 관계를 체계적으로 분석합니다.

## 배경 및 문제

### Autoregressive 디코딩의 비효율성

현대 LLM은 대부분 Transformer 기반 autoregressive 모델로, 텍스트를 한 토큰씩 순차적으로 생성합니다. 시퀀스의 $t$번째 토큰 $x_t$를 생성하려면 이전 토큰들 $x_1, x_2, \ldots, x_{t-1}$이 모두 필요합니다:

$$P(x_t \mid x_1, x_2, \ldots, x_{t-1})$$

이 순차적 특성은 다음과 같은 비효율성을 야기합니다:

- **메모리 대역폭 병목(Memory-bound)**: LLM 추론은 연산량보다 메모리 대역폭에 의해 제한됩니다. 각 디코딩 스텝에서 모델의 전체 파라미터를 메모리에서 읽어와야 하지만, 실제 연산은 하나의 토큰에 대한 행렬-벡터 곱셈뿐입니다. 이로 인해 GPU의 연산 유닛(compute unit)이 대부분의 시간을 유휴 상태로 보냅니다.
- **낮은 하드웨어 활용률**: 최신 GPU(예: NVIDIA A100, H100)는 수백 TFLOPS의 연산 능력을 갖추지만, autoregressive 디코딩에서는 산술 강도(arithmetic intensity)가 매우 낮아 실제 활용률이 1~5%에 그칩니다.
- **Latency의 선형 증가**: 생성하려는 토큰 수 $N$에 대해, 총 latency는 대략 $N \times t_{\text{step}}$으로 선형적으로 증가합니다. 긴 텍스트를 생성할수록 사용자 경험이 급격히 저하됩니다.

### 기존 가속 기법의 한계

LLM 추론 가속을 위한 기존 접근법들은 각각 장단점이 있습니다:

| 기법 | 원리 | 한계 |
|------|------|------|
| **Quantization** | 가중치/활성값을 저정밀도(INT8, INT4)로 변환 | 정밀도 손실, 극단적 양자화 시 성능 저하 |
| **Pruning** | 불필요한 가중치/뉴런 제거 | 구조적 변경 필요, 재학습 비용 |
| **Knowledge Distillation** | 큰 모델의 지식을 작은 모델로 전이 | 별도 학습 필요, 원본 모델 대비 성능 저하 |
| **KV Cache 최적화** | 캐시 메모리 효율화 (PagedAttention 등) | 메모리 효율은 개선하지만 근본적 latency는 유지 |

이들 기법은 각 디코딩 스텝의 비용을 줄이는 데 집중하지만, **순차적으로 한 토큰씩 생성한다는 근본적 구조**는 변경하지 않습니다. Speculative decoding은 이 근본 구조 자체를 바꾸는 접근법입니다.

### 핵심 관찰: Compute vs. Memory 불균형

Speculative decoding이 작동하는 핵심 통찰은 다음과 같습니다. Target 모델로 하나의 토큰을 생성하든 $K$개의 후보 토큰을 병렬 검증하든, 메모리 대역폭 사용량은 거의 동일합니다. 왜냐하면 두 경우 모두 모델의 전체 파라미터를 메모리에서 한 번 읽어와야 하기 때문입니다.

이를 구체적으로 이해하기 위해, 70B 파라미터 모델의 디코딩 과정을 예로 들어보겠습니다. FP16 정밀도 기준으로 모델 가중치만 약 140GB입니다. 하나의 토큰을 생성하기 위해 이 140GB의 가중치를 메모리에서 읽어오는데, A100 GPU(2TB/s 대역폭)에서 약 70ms가 소요됩니다. 반면, 실제 행렬-벡터 곱셈의 연산량은 약 $2 \times 70 \times 10^9 = 1.4 \times 10^{11}$ FLOPs이며, A100의 312 TFLOPS 연산 능력으로는 0.45ms면 충분합니다. 즉, **연산 시간의 99% 이상이 메모리 읽기에 소비**됩니다.

$K$개의 토큰을 동시에 검증하는 경우, 모델 가중치는 여전히 한 번만 읽으면 됩니다. 추가되는 연산은 행렬-벡터 곱셈이 행렬-행렬 곱셈으로 바뀌는 것뿐인데, 이는 GPU의 유휴 연산 유닛을 활용하므로 latency 증가가 미미합니다. 따라서 $K$개의 초안 토큰을 한 번의 forward pass로 검증하면, 이상적으로는 하나의 디코딩 스텝 비용으로 $K$개의 토큰을 생성할 수 있습니다.

이것이 speculative decoding의 핵심 아이디어입니다. **유휴 연산 자원을 활용하여, 추가 비용 없이 여러 토큰을 동시에 처리합니다.**

## Speculative Decoding의 기본 원리

### 핵심 메커니즘

Speculative decoding의 기본 구조는 두 단계로 이루어집니다:

1. **Drafting (초안 생성)**: 작은 모델 $M_q$(draft model)가 $K$개의 후보 토큰 $x'_1, x'_2, \ldots, x'_K$를 autoregressive하게 빠르게 생성합니다.
2. **Verification (검증)**: 큰 모델 $M_p$(target model)가 이 $K$개의 토큰을 **한 번의 forward pass**로 병렬 검증합니다.

검증 단계에서 target 모델은 각 위치에서의 확률 분포 $p(x_t \mid x_{<t})$를 계산하고, draft 모델이 생성한 토큰 $x'_t$가 이 분포에 부합하는지 확인합니다.

이 과정을 pseudo-code로 표현하면 다음과 같습니다:

```
Input: prefix x, draft model M_q, target model M_p, speculation length K
1. Draft phase:
   for i = 1 to K:
     x'_i ~ M_q(· | x, x'_1, ..., x'_{i-1})
2. Verify phase:
   p_1, p_2, ..., p_K, p_{K+1} = M_p(x, x'_1, ..., x'_K)  # single forward pass
3. Accept/Reject:
   for i = 1 to K:
     if accept(x'_i, p_i, q_i):
       append x'_i to output
     else:
       sample x_new ~ adjusted(p_i, q_i)
       append x_new to output
       break
4. Bonus token:
   if all K tokens accepted:
     sample x_{K+1} ~ p_{K+1}  # free bonus token
```

주목할 점은 **Bonus token**입니다. 모든 $K$개의 draft 토큰이 수락되면, target 모델의 forward pass가 이미 $K+1$번째 위치의 확률 분포도 계산해 놓았으므로, 추가 비용 없이 한 토큰을 더 생성할 수 있습니다. 따라서 한 라운드에서 최소 1개(첫 토큰이 거부되어 수정 분포에서 샘플링), 최대 $K+1$개의 토큰을 생성합니다.

### 수학적 보장: Rejection Sampling

Speculative decoding의 가장 중요한 이론적 성질은 **출력 분포의 무손실 보존**입니다. 이는 수정된 rejection sampling을 통해 달성됩니다. Leviathan et al.(2023)과 Chen et al.(2023)이 독립적으로 제안한 이 기법의 핵심은 다음과 같습니다.

Draft 모델의 확률 분포를 $q(x)$, target 모델의 확률 분포를 $p(x)$라 할 때, 각 draft 토큰 $x'$에 대해:

$$\text{Accept with probability} \quad \min\left(1, \frac{p(x')}{q(x')}\right)$$

- **수락(Accept)**: $p(x') \geq q(x')$이면 항상 수락합니다. 즉, target 모델이 draft 토큰에 더 높은 확률을 부여하면 무조건 채택합니다.
- **거부(Reject)**: $p(x') < q(x')$이면 $\frac{p(x')}{q(x')}$의 확률로 수락합니다. 거부된 경우, 수정된 분포 $p'(x) = \text{norm}(\max(0, p(x) - q(x)))$에서 새로운 토큰을 샘플링합니다.

이 과정의 핵심 정리는 다음과 같습니다:

> **정리**: 위의 rejection sampling 절차를 통해 최종적으로 생성되는 토큰의 분포는 target 모델 $M_p$의 분포 $p(x)$와 **정확히 동일**합니다.

즉, speculative decoding은 출력 품질의 저하 없이 순수하게 속도만 향상시키는 **무손실(lossless)** 가속 기법입니다. 이 성질이 quantization이나 pruning 같은 근사적 방법과 근본적으로 구별되는 점입니다.

이 무손실 보장의 직관적 이해를 위해 간단한 예시를 들어보겠습니다. Target 모델이 다음 토큰으로 "the"에 0.3, "a"에 0.2, "an"에 0.1의 확률을 부여하고, draft 모델이 "the"에 0.5, "a"에 0.1, "an"에 0.1의 확률을 부여했다고 가정합니다. Draft 모델이 "the"를 생성했다면, 수락 확률은 $\min(1, 0.3/0.5) = 0.6$입니다. 만약 draft 모델이 "a"를 생성했다면, $\min(1, 0.2/0.1) = 1.0$이므로 반드시 수락됩니다. 이처럼 target 모델이 draft 모델보다 더 높은 확률을 부여하는 토큰은 항상 수락되고, 그렇지 않은 토큰은 확률적으로 거부되어 수정 분포에서 재샘플링됩니다. 이 과정을 통해 최종 분포가 target 모델의 분포와 정확히 일치하게 됩니다.

### 속도 향상의 원리

Speculative decoding의 speedup은 draft 토큰의 **수락률(acceptance rate)** $\alpha$에 의해 결정됩니다. $K$개의 draft 토큰을 생성할 때, 기대 수락 토큰 수는:

$$\mathbb{E}[\text{accepted tokens}] = \sum_{i=1}^{K} \alpha^i = \frac{\alpha(1 - \alpha^K)}{1 - \alpha}$$

Draft 모델의 한 스텝 비용을 $c_q$, target 모델의 한 스텝 비용을 $c_p$라 하면, speculative decoding의 이론적 speedup은:

$$\text{Speedup} = \frac{\mathbb{E}[\text{accepted tokens}]}{K \cdot c_q + c_p}$$

수락률 $\alpha$가 높을수록, 그리고 draft 모델이 target 모델보다 훨씬 빠를수록($c_q \ll c_p$) speedup이 증가합니다. 이로부터 speculative decoding 연구의 두 가지 핵심 방향이 도출됩니다:

1. **수락률 $\alpha$ 향상**: draft 품질 개선 (Model-Centric 접근)
2. **draft 비용 $c_q$ 최소화**: 더 효율적인 drafting 메커니즘 설계 (Draft-Centric 접근)

## 분류 체계

본 서베이가 제안하는 분류 체계는 speculative decoding 방법론을 **접근 방식의 철학**에 따라 체계적으로 나눕니다.

![Speculative decoding 방법론의 분류 체계](figures/fig_1.png)
*Figure 1: Speculative decoding 방법론의 분류 체계(Taxonomy). 최상위에서 Model-Centric과 Draft-Centric으로 나뉘며, 각각 Independent/Dependent와 Probability Based/Draft Selection으로 세분화된다.*

### 대분류: Model-Centric vs. Draft-Centric

이 분류 체계의 핵심 기준은 **"어디에 혁신을 집중하는가?"**입니다:

- **Model-Centric (모델 중심)**: Draft 모델 자체를 개선하여 더 높은 품질의 초안을 생성하는 데 집중합니다. 더 좋은 draft → 더 높은 수락률 → 더 큰 speedup이라는 논리를 따릅니다.
- **Draft-Centric (초안 중심)**: Draft 토큰의 선택 또는 생성 방식을 혁신하여 효율성을 높이는 데 집중합니다. 더 효율적인 drafting → 낮은 overhead → 높은 순이익이라는 논리를 따릅니다.

### Model-Centric 세부 분류

Model-Centric 접근법은 다시 두 갈래로 나뉩니다:

**1. Independent (독립적)**
Draft 모델이 target 모델과 **독립적으로** 구성됩니다. 별도의 작은 모델을 사용하거나, target 모델과 구조적 관련성이 없는 모델을 활용합니다.

- Speculative Sampling (Chen et al., 2023)
- Speculative Decoding (Leviathan et al., 2023)
- BiLD (Kim et al., 2024)
- Chimera (Cheng et al., 2024)
- Online SD (Liu et al., 2024)
- Medusa (Cai et al., 2024)

**2. Dependent (의존적)**
Draft 모델이 target 모델의 구조나 파라미터에 **의존적으로** 구성됩니다. Target 모델의 일부 레이어를 재활용하거나, target 모델로부터 파생된 구조를 사용합니다.

- Self-Speculative Decoding (Draft & Verify, Zhang et al., 2024)
- SpecDec++ (Huang et al., 2024)
- CaPE Tree (Svirschevski et al., 2024)
- Nuclear Sampling (Gu et al., 2024)

### Draft-Centric 세부 분류

Draft-Centric 접근법도 두 갈래로 구분됩니다:

**1. Probability Based (확률 기반)**
Draft 토큰의 선택 과정에서 확률적 방법론을 활용하여 효율성을 높입니다.

- Search Optimization: BASS (Zhong et al., 2024), SpecInfer (Miao et al., 2024)
- Tree & Graph Based: Sequoia (Chen et al., 2024), SpecDec (Xia et al., 2023)

**2. Draft Selection (초안 선택)**
더 나은 draft 토큰을 선택하기 위한 전략을 개발합니다.

- Retrieval & Adaptive: REST (He et al., 2024), EAGLE (Li et al., 2024), EAGLE-2 (Li et al., 2024)
- Sorted SD / GPU Offloading: Sorted Speculative Decoding (Yin et al., 2024), GPU Draft (Zhuge et al., 2024)

### 기존 서베이와의 분류 체계 비교

본 서베이의 분류 체계를 다른 speculative decoding 서베이와 비교하면 그 차별점이 명확해집니다:

| 서베이 | 분류 기준 | 주요 카테고리 |
|--------|----------|-------------|
| **본 서베이 (Ryu & Kim, 2024)** | 혁신의 초점 | Model-Centric / Draft-Centric |
| Xia et al. (2025, 2502.19732) | Draft 생성 방식 | Independent Model / Self-Draft / Draft-free |
| Liu et al. (2024) | 시스템 구성 요소 | Draft / Verify / Training / System |

본 서베이의 이분법은 더 **추상적이고 원리적**인 기준을 사용합니다. 예를 들어, EAGLE은 Xia et al.의 분류에서는 "Self-Draft"에 가깝지만, 본 서베이에서는 **Draft Selection**(Draft-Centric)으로 분류됩니다. 이는 EAGLE의 핵심 혁신이 draft 모델의 구조보다는 feature-level에서 draft를 생성하고 tree 구조로 조직하는 **선택 전략**에 있다고 보기 때문입니다. 이처럼 동일한 방법론이라도 분류 체계의 관점에 따라 다른 위치에 놓일 수 있으며, 이는 각 서베이가 제공하는 통찰의 차이를 반영합니다.

## Draft-Centric vs. Model-Centric: 핵심 차이

두 접근법의 근본적 차이를 시각적으로 이해하는 것이 중요합니다.

![Draft-Centric과 Model-Centric 구현의 비교](figures/fig_2.png)
*Figure 2: Draft-Centric(좌)과 Model-Centric(우) 구현의 비교. Draft-Centric은 생성된 draft 토큰 풀에서 최적의 부분집합을 선택하여 검증에 보내는 반면, Model-Centric은 drafting 모델 자체를 개선하여 처음부터 더 높은 품질의 draft를 생성한다.*

### Draft-Centric 접근법의 직관

그림 좌측에서 볼 수 있듯이, Draft-Centric 접근법에서는:

1. Drafting 단계에서 $x_1$으로부터 여러 후보 토큰 $x'_2, x'_3, \ldots, x'_6$을 생성합니다.
2. 이 중 **일부를 전략적으로 선택**합니다(빨간 점선 박스). 예를 들어, $x'_2, x'_3, x'_4$만 선택하고 $x'_5, x'_6$은 제외합니다.
3. 선택된 토큰만 target 모델에 보내 검증합니다.
4. 검증 결과 수락된 토큰($x_2, x_3, x_4$)이 최종 출력이 됩니다.

이 접근법의 핵심은 **"어떤 draft 토큰을 검증에 보낼 것인가?"**라는 선택 문제입니다. 수락될 가능성이 높은 토큰만 선별하여 검증함으로써 불필요한 연산을 줄입니다. Tree-based 방법이나 retrieval 기반 방법이 여기에 해당합니다.

### Model-Centric 접근법의 직관

그림 우측에서는:

1. **개선된(refined)** draft 모델(빗금 패턴으로 표시)이 $x_1$으로부터 후보 토큰 $x'_2, x'_3, \ldots, x'_6$을 생성합니다.
2. Draft 모델이 더 정교하므로 생성된 모든 토큰의 품질이 높습니다.
3. **모든 draft 토큰**을 target 모델에 보내 검증합니다(선택 과정 없음).
4. Draft 품질이 높으므로 대부분의 토큰($x_2, x_3, x_4, x_5, x_6$)이 수락됩니다.

이 접근법의 핵심은 **"draft 모델을 어떻게 더 좋게 만들 것인가?"**라는 모델 설계 문제입니다. Draft 모델의 품질이 높아지면 수락률이 올라가고, 결과적으로 전체 속도가 향상됩니다.

### 두 접근법의 비교

| 비교 항목 | Draft-Centric | Model-Centric |
|-----------|--------------|---------------|
| **핵심 전략** | 더 스마트한 토큰 선택 | 더 좋은 draft 모델 |
| **혁신 포인트** | 선택 알고리즘, 탐색 구조 | 모델 아키텍처, 학습 방법 |
| **추가 학습** | 보통 불필요 | 종종 필요 (fine-tuning 등) |
| **유연성** | target 모델에 독립적으로 적용 가능 | target 모델과의 관계 설계 필요 |
| **대표 기법** | Sequoia, EAGLE, REST, SpecInfer | Medusa, Online SD, Draft & Verify |

## 주요 기법 상세

### Model-Centric: Independent 계열

#### Speculative Sampling / Speculative Decoding (2023)

Chen et al.(2023)과 Leviathan et al.(2023)은 독립적으로 speculative decoding의 기본 프레임워크를 제안했습니다. 이 두 논문은 사실상 동일한 아이디어를 담고 있으며, speculative decoding 분야의 토대를 마련했습니다.

핵심 알고리즘은 다음과 같습니다:

1. Draft 모델 $M_q$로 $K$개의 토큰을 autoregressive하게 생성
2. Target 모델 $M_p$로 $K$개의 토큰을 한 번에 검증 (single forward pass)
3. 수정된 rejection sampling으로 각 토큰의 수락/거부 결정
4. 첫 번째 거부 토큰 이후는 모두 폐기하고, 수정된 분포에서 새 토큰 샘플링

이 프레임워크의 이론적 보장은 최종 출력 분포가 target 모델의 분포와 정확히 일치한다는 것입니다. Draft 모델의 선택이 핵심이며, 일반적으로 target 모델과 같은 계열의 작은 모델(예: LLaMA-7B가 target이면 LLaMA-68M이 draft)을 사용합니다.

#### BiLD (Big Little Decoder, 2024)

Kim et al.(2024)은 speculative decoding을 **Big-Little 프레임워크**로 재해석했습니다. 큰 모델(Big)과 작은 모델(Little)이 협력하는 구조에서, fallback 메커니즘을 도입하여 Little 모델의 예측이 불확실할 때만 Big 모델을 호출합니다.

BiLD의 핵심 기여는 **적응적 speculation 길이**입니다. 고정된 $K$ 대신, Little 모델의 예측 신뢰도에 따라 동적으로 speculation 길이를 조절합니다. 쉬운 토큰은 Little 모델이 계속 생성하고, 어려운 토큰에서만 Big 모델이 개입합니다.

#### Medusa (2024)

Cai et al.(2024)이 제안한 Medusa는 **별도의 draft 모델 없이** target 모델 자체에 여러 개의 prediction head를 추가하는 접근법입니다. Target 모델의 마지막 hidden state에서 분기하는 $K$개의 독립적인 MLP head가 각각 $t+1, t+2, \ldots, t+K$ 위치의 토큰을 동시에 예측합니다.

$$\hat{x}_{t+k} = \text{MLP}_k(h_t), \quad k = 1, 2, \ldots, K$$

Medusa의 장점:
- **별도 draft 모델 불필요**: 추가 MLP head만 학습하면 됩니다
- **KV cache 공유**: Target 모델과 동일한 KV cache를 사용하므로 메모리 효율적입니다
- **Tree attention**: 여러 head의 예측을 결합하여 tree 구조의 후보를 생성하고, 한 번의 forward pass로 검증합니다

Medusa에는 두 가지 변형이 있습니다:
- **Medusa-1**: Target 모델의 backbone은 고정(frozen)하고, 추가 MLP head만 학습합니다. 구현이 간단하지만 head의 예측 정확도에 한계가 있습니다.
- **Medusa-2**: Target 모델의 backbone과 MLP head를 함께 fine-tuning합니다. 더 높은 수락률을 달성하지만, 원래 모델의 성능이 변할 수 있다는 리스크가 있습니다.

Tree attention에서 Medusa는 $K$개의 head가 각각 top-$k$ 후보를 제안하면, 이들의 Cartesian product에서 tree를 구성합니다. 예를 들어 5개의 head가 각각 top-3 후보를 제안하면 $3^5 = 243$개의 후보 경로가 생기지만, 실제로는 pruning을 통해 수십 개로 줄여 하나의 forward pass로 검증합니다.

Medusa의 한계는 추가 head의 학습이 필요하다는 점과, head의 예측 정확도가 먼 위치일수록 급격히 떨어진다는 점입니다. 특히, $k$번째 head가 예측하는 $x_{t+k}$는 $x_{t+1}, \ldots, x_{t+k-1}$의 정보 없이 오직 $h_t$만으로 예측하므로, autoregressive한 의존성을 포착하기 어렵습니다.

#### Online Speculative Decoding (2024)

Liu et al.(2024)의 Online SD는 speculative decoding의 중요한 한계를 지적합니다. 기존 방식에서 draft 모델은 **고정된** 상태로 사용되지만, 실제 서비스 환경에서의 쿼리 분포는 시간에 따라 변합니다. 이로 인해 특정 도메인에서 draft 모델의 수락률이 크게 떨어질 수 있습니다.

Online SD는 draft 모델을 서비스 운영 중에 **지속적으로 업데이트**하는 방법을 제안합니다:
- Target 모델의 출력을 teacher signal로 활용
- Knowledge distillation을 online으로 수행
- 최근 쿼리 분포에 맞게 draft 모델이 자동 적응

이 접근법은 시간이 지남에 따라 수락률이 향상되는 자기개선(self-improving) 특성을 보여줍니다.

#### Chimera (2024)

Cheng et al.(2024)의 Chimera는 speculative decoding을 **멀티모달 LLM**에 적용한 최초의 연구 중 하나입니다. 멀티모달 모델에서는 이미지 토큰과 텍스트 토큰의 분포가 크게 달라 기존 draft 모델의 수락률이 낮았습니다.

Chimera는 이미지와 텍스트 각각에 특화된 draft head를 설계하여 멀티모달 환경에서도 높은 수락률을 달성합니다.

### Model-Centric: Dependent 계열

#### Draft & Verify / Self-Speculative Decoding (2024)

Zhang et al.(2024)의 Draft & Verify는 **target 모델 자체를 draft 모델로도 활용**하는 self-speculative decoding 접근법입니다. 핵심 아이디어는 target 모델의 일부 레이어만 사용하여(layer skipping) 초안을 생성하는 것입니다.

예를 들어, 32-layer Transformer에서:
- **Draft 단계**: 4, 8, 12, 16번째 레이어만 실행하여 빠르게 초안 생성 (4배 빠름)
- **Verify 단계**: 전체 32개 레이어를 실행하여 검증

이 접근법의 장점은 별도의 draft 모델 학습이나 메모리가 필요 없다는 것입니다. KV cache도 target 모델과 공유할 수 있어 메모리 효율적입니다.

Layer skipping이 작동하는 이유는 Transformer 모델의 **residual connection** 구조에 있습니다. 각 레이어의 출력이 입력에 더해지는 형태($h_{l+1} = h_l + f_l(h_l)$)이므로, 일부 레이어를 건너뛰어도 이전 레이어의 정보가 residual path를 통해 전달됩니다. 물론 건너뛴 레이어의 연산이 빠지므로 출력 품질은 저하되지만, 많은 경우 "대략적으로 맞는" 초안을 생성하기에는 충분합니다.

단, 어떤 레이어를 건너뛸지의 선택이 성능에 큰 영향을 미칩니다. 초반 레이어(토큰 표현 구성)와 마지막 레이어(최종 예측)는 유지하고, 중간 레이어를 건너뛰는 것이 일반적으로 가장 효과적입니다.

#### SpecDec++ (2024)

Huang et al.(2024)은 기존 speculative decoding에서 **거부된 토큰의 정보도 활용**하는 방법을 제안합니다. 표준 speculative decoding에서는 첫 번째 거부 이후의 모든 draft 토큰이 버려지지만, SpecDec++는 거부된 토큰의 hidden representation을 재활용하여 다음 drafting 라운드의 초기값으로 사용합니다.

#### Nuclear Sampling (2019, 2024)

Nucleus(Top-p) sampling은 원래 Holtzman et al.(2019)이 텍스트 생성 품질 향상을 위해 제안한 기법이지만, speculative decoding 맥락에서도 중요한 역할을 합니다. 누적 확률이 $p$ 이상이 되는 최소한의 토큰 집합만 고려함으로써 draft 토큰의 후보 공간을 줄이고, 수락률을 높일 수 있습니다.

### Draft-Centric: Probability Based 계열

#### SpecInfer / Speculative Inference (2024)

Miao et al.(2024)의 SpecInfer는 **여러 개의 small speculative model(SSM)**을 동시에 활용하여 **tree-structured speculation**을 수행합니다. 단일 draft 모델의 한계를 극복하기 위해, 여러 draft 모델이 각각 다른 경로의 토큰 시퀀스를 생성하고, 이를 tree 형태로 구성하여 target 모델이 한 번에 검증합니다.

Tree 구조의 장점:
- 단일 경로보다 **더 많은 후보**를 커버할 수 있습니다
- 다양한 draft 모델이 서로 다른 패턴을 포착하므로 **complementary**한 draft 생성이 가능합니다
- Tree attention을 활용하면 하나의 forward pass로 전체 tree를 검증할 수 있습니다

**Tree Attention의 작동 원리**: Tree 구조의 토큰을 검증하기 위해, SpecInfer는 특수한 attention mask를 사용합니다. 일반적인 causal attention mask는 이전의 모든 토큰에 attend하지만, tree attention mask에서 각 노드는 **자신의 조상(ancestor) 노드에만** attend합니다. 이를 통해 tree의 모든 경로를 하나의 forward pass에서 독립적으로 검증할 수 있습니다. 예를 들어, depth 3의 binary tree에서 8개의 leaf 노드(경로)를 동시에 검증하면, 최대 3개의 토큰을 수락할 수 있습니다.

SpecInfer는 또한 **token tree verification**이라는 알고리즘을 도입하여, tree의 모든 경로 중 가장 긴 수락 경로를 효율적으로 찾습니다. 이는 BFS(Breadth-First Search)를 변형한 것으로, 각 depth에서 수락된 노드만을 다음 depth의 부모로 설정합니다.

#### BASS (Batched Attention-optimized Speculative Sampling, 2024)

Zhong et al.(2024)의 BASS는 speculative decoding의 **탐색 과정을 최적화**하는 데 초점을 맞춥니다. Draft 토큰 생성을 beam search와 유사한 탐색 문제로 재정의하여, 수락 가능성이 높은 토큰 시퀀스를 체계적으로 탐색합니다.

BASS의 핵심은 attention 연산을 배치 처리에 최적화하여, 여러 후보 시퀀스를 동시에 평가하는 것입니다. 이를 통해 단순 greedy drafting보다 높은 수락률을 달성하면서도 drafting overhead를 최소화합니다.

#### Sequoia (2024)

Chen et al.(2024)의 Sequoia는 **최적의 tree 구조**를 자동으로 학습하는 알고리즘을 제안합니다. 기존 tree-based 방법들이 수동으로 설계한 tree 구조(예: 이진 트리, 고정 분기 수)를 사용한 반면, Sequoia는 hardware-aware한 최적화를 통해 주어진 하드웨어와 모델 조합에 최적인 tree topology를 탐색합니다.

최적화 대상은 다음과 같습니다:
- **Tree depth**: 깊은 tree는 더 긴 시퀀스를 커버하지만 검증 비용 증가
- **Branching factor**: 넓은 tree는 다양한 후보를 제공하지만 메모리 사용량 증가
- **Tree shape**: 각 depth에서의 노드 수를 비대칭적으로 설정

Sequoia는 이론적으로 최적의 tree를 $O(n \log n)$ 시간에 찾는 동적 프로그래밍 알고리즘을 제시합니다.

### Draft-Centric: Draft Selection 계열

#### EAGLE (Extrapolation Algorithm for Greater Language-model Efficiency, 2024)

Li et al.(2024)의 EAGLE은 speculative decoding의 draft 생성을 **feature 수준의 extrapolation**으로 재정의합니다. 토큰 수준에서 draft를 생성하는 대신, target 모델의 hidden state를 입력으로 받아 다음 위치의 hidden state를 예측하는 lightweight regression head를 학습합니다.

EAGLE의 핵심 관찰:
- 토큰 수준의 예측보다 **hidden state 수준의 예측**이 더 쉽습니다
- Hidden state는 연속 공간에서 smoother한 분포를 가지므로 예측이 용이합니다
- 예측된 hidden state로부터 토큰 분포를 복원할 수 있습니다

구체적으로, EAGLE의 extrapolation 과정은 다음과 같습니다:

1. Target 모델의 마지막 hidden state $h_t$와 embedding $e_t$를 연결(concatenate)
2. Lightweight autoregressive head가 다음 위치의 feature $\hat{h}_{t+1}$을 예측
3. 예측된 feature $\hat{h}_{t+1}$에 target 모델의 LM head를 적용하여 토큰 분포 추출
4. 샘플링된 토큰의 embedding과 $\hat{h}_{t+1}$을 다시 입력하여 $\hat{h}_{t+2}$ 예측
5. 이 과정을 $K$번 반복하여 $K$개의 draft 토큰 생성

EAGLE이 Medusa보다 우수한 핵심 이유는 **autoregressive dependency를 유지**한다는 점입니다. Medusa의 각 head는 독립적으로 예측하지만, EAGLE은 이전 예측 결과를 다음 예측의 입력으로 사용하므로 토큰 간 의존성을 반영합니다. 실험적으로 EAGLE은 Medusa 대비 더 높은 수락률과 더 빠른 속도를 보여줍니다.

#### EAGLE-2 (2024)

EAGLE의 후속 연구인 EAGLE-2는 **context-aware dynamic draft tree** 구조를 도입합니다. EAGLE이 고정된 tree 구조를 사용한 반면, EAGLE-2는 각 drafting 라운드에서 현재 context에 기반하여 tree 구조를 동적으로 결정합니다. 이를 통해 쉬운 토큰에는 깊은 tree를, 어려운 토큰에는 넓은 tree를 적응적으로 적용합니다.

#### REST (Retrieval-based Speculative Decoding, 2024)

He et al.(2024)의 REST는 완전히 다른 패러다임을 제안합니다. Draft 모델을 사용하는 대신 **텍스트 데이터베이스에서 검색**하여 draft 토큰을 생성합니다.

REST의 작동 방식:
1. 현재까지 생성된 텍스트(suffix)를 쿼리로 사용
2. 사전에 구축한 대규모 텍스트 코퍼스의 suffix array에서 매칭되는 continuation을 검색
3. 검색된 continuation을 draft 토큰으로 사용
4. Target 모델이 검증

REST의 장점:
- **Draft 모델이 전혀 필요 없습니다**: 검색만으로 draft를 생성하므로 추가 모델의 메모리나 연산 비용이 없습니다
- **도메인 적응이 용이합니다**: 도메인별 코퍼스를 인덱싱하면 자동으로 해당 도메인에 최적화됩니다
- **코드 생성에 특히 효과적입니다**: 코드는 반복 패턴이 많아 검색 기반 draft의 수락률이 높습니다

REST의 기술적 핵심은 **suffix array**입니다. Suffix array는 텍스트의 모든 suffix를 사전순으로 정렬한 인덱스로, 주어진 prefix에 매칭되는 모든 위치를 $O(\log N)$ 시간에 찾을 수 있습니다($N$은 코퍼스 크기). 이는 draft 모델의 forward pass보다 수 배 빠르며, GPU 연산이 전혀 필요 없다는 점에서 메모리 대역폭 병목도 회피합니다.

다만 REST의 한계도 명확합니다. 코퍼스에 유사한 패턴이 없는 완전히 새로운 내용을 생성할 때는 매칭 실패율이 높아져 speedup이 크게 감소합니다. 또한 suffix array의 크기가 코퍼스에 비례하므로, 매우 큰 코퍼스를 사용할 경우 메모리 사용량이 상당합니다.

#### Sorted Speculative Decoding (2024)

Yin et al.(2024)의 Sorted SD는 draft 토큰을 **확률 순서로 정렬**하여 검증 효율을 높이는 기법입니다. 높은 확률의 토큰부터 먼저 검증하면 수락될 가능성이 높은 토큰을 빨리 확정하고, 불필요한 검증을 줄일 수 있다는 직관에 기반합니다.

#### Fine-Tuned LLMs as Draft Models

Chat-Fine-Tuned LLMs를 draft 모델로 활용하는 연구도 있습니다. 이 접근법은 target 모델과 동일한 base 모델에서 출발하되, instruction tuning된 작은 모델을 draft로 사용합니다. 동일한 학습 데이터로 fine-tuning된 모델은 원래 모델과 유사한 출력 분포를 가지므로 높은 수락률을 기대할 수 있습니다.

## 시간순 발전 과정

Speculative decoding은 2018년부터 급격한 발전을 이루어 왔습니다.

![Speculative decoding 방법론의 시간순 발전 과정](figures/fig_3.png)
*Figure 3: 본 서베이에서 다루는 speculative decoding 방법론의 타임라인. 2018년 Blockwise Parallel Decoding에서 시작하여, 2023~2024년에 폭발적인 연구 성장이 이루어졌다. 파란색은 Model-Centric, 주황색은 Draft-Centric 계열을 나타낸다.*

### 2018~2019: 태동기

- **2018 - Blockwise Parallel Decoding (BPD)**: Stern et al.이 제안한 BPD는 speculative decoding의 원조격 논문입니다. Target 모델의 중간 hidden state에서 분기하는 추가 prediction head를 사용하여 여러 토큰을 동시에 예측합니다. 이후 Medusa와 같은 방법론에 직접적인 영감을 주었습니다.
- **2019 - Nuclear Sampling**: Top-p sampling의 등장으로, speculative decoding에서의 효율적인 확률 분포 처리에 대한 기반이 마련되었습니다.

### 2023: 본격적 출발

2023년은 speculative decoding이 본격적으로 학계의 주목을 받기 시작한 해입니다:

- **Speculative Sampling (Chen et al.)**: Google Research에서 발표, 이론적 프레임워크 확립
- **Speculative Decoding (Leviathan et al.)**: 독립적으로 동일한 아이디어를 제안, rejection sampling 기반 검증 방법 공식화
- **Online SD (Liu et al.)**: Draft 모델의 온라인 학습 개념 도입
- **SpecDec (Xia et al.)**: Draft 토큰의 확률적 선택 방법 제안

### 2024년 1~2월: 가속화

- **REST**: 검색 기반 drafting이라는 새로운 패러다임 등장
- **Chimera**: 멀티모달 LLM으로의 확장
- **EAGLE**: Feature-level extrapolation 기반의 고효율 drafting
- **Chat-Fine-Tuned LLMs**: Fine-tuning 기반 draft 모델 활용 연구

### 2024년 3~6월: 폭발적 성장

이 시기에 tree-based 방법의 발전과 다양한 최적화 기법이 동시에 등장합니다:

- **EAGLE-2**: Context-aware dynamic tree 도입
- **Sequoia**: Hardware-aware 최적 tree 구조 자동 탐색
- **SpecInfer**: Multi-SSM tree speculation
- **BASS**: Batched attention 기반 탐색 최적화
- **Medusa**: 추가 head 기반의 self-draft 방식
- **BiLD**: Big-Little 적응적 프레임워크
- **Sorted SD**: 정렬 기반 검증 효율화
- **SpecDec++**: 거부 토큰 정보 재활용
- **ESSD with Trustworthy**: 신뢰도 기반 early stopping

### 2024년 7~8월: 성숙기

- **Draft & Verify**: Self-speculative decoding의 체계화
- **Staged SD**: 다단계 speculative decoding
- **ProPD**: Progressive parallel decoding
- **GPU Draft Offloading**: GPU-CPU 간 연산 분배 최적화

이 타임라인에서 관찰되는 주요 트렌드:
1. **Draft 모델의 다양화**: 별도 모델 → self-draft → 검색 기반 → feature-level
2. **구조의 복잡화**: 단일 경로 → tree → dynamic tree → DAG
3. **적용 범위 확대**: 텍스트 → 멀티모달 → 코드 → 특수 도메인

## 비교 분석

### 수락률 vs. Drafting Overhead 트레이드오프

Speculative decoding의 효과는 **수락률**과 **drafting overhead**의 균형에 의해 결정됩니다. 이 트레이드오프를 이해하기 위해 주요 방법론을 분석합니다.

**높은 수락률 추구 방법들:**
- EAGLE/EAGLE-2: Feature-level extrapolation으로 토큰 수준보다 높은 수락률 달성
- Online SD: 지속적 adaptation으로 수락률이 시간에 따라 향상
- Medusa: Target 모델의 hidden state를 직접 사용하므로 정보 손실 최소화

**낮은 Drafting Overhead 추구 방법들:**
- REST: Draft 모델이 없으므로 overhead가 거의 0
- Draft & Verify: Target 모델을 재활용하므로 추가 메모리 비용 없음
- Sorted SD: 정렬이라는 경량 연산만 추가

**두 가지를 동시에 최적화하는 방법들:**
- Sequoia: Hardware-aware 최적화로 주어진 조건에서 최적 균형점 탐색
- EAGLE-2: Dynamic tree로 상황에 따라 적응적으로 균형 조정

### 메모리 효율성 비교

| 방법론 | 추가 메모리 비용 | KV Cache 공유 |
|--------|-----------------|---------------|
| Standard SD | Draft 모델 전체 파라미터 | 불가 |
| Medusa | MLP head ($K$개) | 가능 |
| EAGLE | Lightweight transformer (1 layer) | 부분 공유 |
| Draft & Verify | 없음 (self-draft) | 완전 공유 |
| REST | Suffix array 인덱스 | 해당 없음 |
| SpecInfer | 다수의 SSM 파라미터 | 불가 |

메모리가 제약 조건인 환경(예: edge device, consumer GPU)에서는 Draft & Verify나 Medusa처럼 추가 메모리가 적은 방법이 유리합니다. 반면, 메모리가 충분한 서버 환경에서는 별도 draft 모델을 사용하는 표준 speculative decoding이 더 높은 speedup을 달성할 수 있습니다.

### 학습 비용 비교

| 방법론 | 추가 학습 필요 | 학습 데이터 요구 | 학습 비용 |
|--------|--------------|----------------|----------|
| Standard SD | Draft 모델 사전학습 | 대규모 | 높음 |
| Medusa | Head fine-tuning | 중간 | 중간 |
| EAGLE | Regression head 학습 | 소규모 | 낮음 |
| Draft & Verify | 없음 | 없음 | 없음 |
| REST | 인덱스 구축 | 코퍼스 필요 | 낮음 (비학습) |
| Online SD | 온라인 distillation | 서비스 데이터 | 지속적 (낮음) |

### 적용 시나리오별 권장 방법

**1. 빠른 적용이 필요한 경우 (Training-free)**
- Draft & Verify (Self-Speculative): 추가 학습이나 모델 없이 바로 적용
- REST: 텍스트 코퍼스만 있으면 인덱싱 후 즉시 사용

**2. 최대 속도가 필요한 경우**
- EAGLE-2 + Sequoia: Feature-level draft + 최적 tree 구조의 조합
- SpecInfer: 다수의 SSM을 활용한 넓은 탐색 공간

**3. 메모리 제약이 심한 경우**
- Medusa: Target 모델에 경량 head만 추가
- Draft & Verify: 추가 메모리 비용 없음

**4. 도메인 특화 서비스**
- REST: 도메인 코퍼스 인덱싱으로 자동 특화
- Online SD: 서비스 데이터로 자동 적응

**5. 코드 생성**
- REST: 코드의 반복 패턴 활용으로 높은 수락률
- EAGLE-2: 코드의 구조적 특성을 feature level에서 포착

## 이론적 분석

### Speedup의 상한

Speculative decoding의 이론적 speedup 상한은 다음과 같이 분석됩니다. $K$를 speculation length, $\alpha$를 수락률, $c = c_q / c_p$를 draft-target 비용 비율이라 하면:

$$\text{Speedup} \leq \frac{1}{c + (1-\alpha^K) / (K \cdot \alpha^{K-1})}$$

이상적인 경우($c \to 0$, $\alpha \to 1$)에는 speedup이 $K$에 접근합니다. 즉, $K$개의 토큰을 하나의 스텝 비용으로 생성할 수 있습니다. 그러나 실제로는:

- $c > 0$: Draft 모델도 연산 비용이 있습니다
- $\alpha < 1$: 모든 토큰이 수락되지는 않습니다
- 배치 크기 증가에 따른 compute-bound 전환: 배치가 커지면 memory-bound에서 compute-bound로 전환되어 speculative decoding의 이점이 줄어듭니다

실제 보고된 speedup은 대부분 1.5x~3.5x 범위에 있으며, 4x 이상의 speedup은 매우 특수한 조건에서만 달성됩니다.

### Optimal Speculation Length

최적의 speculation length $K^*$는 다음 조건에서 결정됩니다:

$$K^* = \argmax_K \frac{\sum_{i=1}^{K} \alpha^i}{K \cdot c_q + c_p}$$

$K$가 너무 작으면 검증의 병렬성을 활용하지 못하고, $K$가 너무 크면 뒤쪽 토큰의 거부율이 높아져 낭비가 발생합니다. 최적값은 $\alpha$와 $c$에 따라 달라지며, 일반적으로 $K^* \in [3, 8]$ 범위입니다.

### Tree vs. Chain Speculation

단일 경로(chain)와 tree 구조의 이론적 비교도 중요합니다:

- **Chain**: $K$개의 토큰이 일렬로 연결. 첫 거부 이후 모든 후속 토큰 폐기
- **Tree**: 같은 $K$개의 토큰이 tree로 분기. 한 경로가 거부되어도 다른 경로 유효

동일한 검증 비용($K$개 토큰의 forward pass)에서, tree는 chain보다 **더 높은 기대 수락 토큰 수**를 제공합니다. 이는 Sequoia, SpecInfer, EAGLE-2 등이 tree 구조를 채택하는 이론적 근거입니다.

구체적인 수치 예시를 들어보겠습니다. 수락률 $\alpha = 0.7$, 총 토큰 수 $K = 7$인 경우를 비교합니다:

- **Chain (길이 7)**: 기대 수락 토큰 수 = $\frac{0.7(1 - 0.7^7)}{1 - 0.7} \approx 2.18$개
- **Binary Tree (depth 3, 7 nodes)**: 최대 3개의 토큰을 수락할 수 있으며, 각 depth에서 2개의 후보 중 하나라도 수락될 확률이 $1 - (1-0.7)^2 = 0.91$이므로, 기대 수락 토큰 수 $\approx 2.55$개

같은 검증 비용(7개 토큰)으로 tree가 약 17% 더 많은 토큰을 생성합니다. 수락률이 낮을수록 이 차이는 더 커집니다.

### Batched Inference에서의 과제

실제 서비스 환경에서 speculative decoding이 직면하는 중요한 과제는 **배치 추론과의 비호환성**입니다. 배치 크기가 커지면 다음과 같은 문제가 발생합니다:

1. **Memory-bound에서 Compute-bound로 전환**: 배치 크기가 충분히 크면 행렬-행렬 곱셈이 되어 GPU 연산 유닛이 포화됩니다. 이 경우 추가 토큰 검증에 실제 연산 비용이 발생하여 speculative decoding의 이점이 사라집니다.

2. **배치 내 불균일한 수락 길이**: 배치 내 각 요청의 수락 토큰 수가 다르므로, 가장 짧은 수락 길이에 맞춰야 하는 비효율이 발생합니다. 이를 해결하기 위해 padding이나 별도의 스케줄링이 필요합니다.

3. **Draft-target 간 KV cache 관리 복잡성**: 배치 환경에서 각 요청의 KV cache를 효율적으로 관리하는 것이 더 복잡해집니다.

이러한 이유로, speculative decoding은 현재까지 주로 **단일 요청 또는 소규모 배치** 환경에서 가장 큰 효과를 발휘하며, 대규모 배치 처리에서의 효과적인 적용은 아직 열린 연구 문제입니다.

## 실용적 고려사항

### Draft 모델 선택 가이드

실무에서 speculative decoding을 적용할 때, 가장 중요한 결정 중 하나는 적절한 draft 모델(또는 drafting 전략)을 선택하는 것입니다.

**Draft 모델의 크기**: 일반적으로 target 모델 파라미터의 5~20%가 적절합니다. 예를 들어:
- Target: LLaMA-2 70B → Draft: LLaMA-2 7B (~10%)
- Target: LLaMA-2 13B → Draft: TinyLLaMA 1.1B (~8.5%)

Draft 모델이 너무 작으면 수락률이 낮아 speedup이 제한되고, 너무 크면 drafting overhead가 커져 net speedup이 감소합니다.

**같은 계열(family) vs. 다른 계열**: 같은 학습 데이터와 토크나이저를 공유하는 모델 계열 내에서 draft 모델을 선택하면 수락률이 높습니다. 토크나이저가 다른 모델을 draft로 사용하면 토큰 매핑 문제가 추가로 발생합니다.

**Temperature의 영향**: Sampling temperature가 낮을수록(greedy에 가까울수록) 수락률이 높아집니다. Temperature가 0(greedy decoding)인 경우, draft 모델이 target 모델과 같은 토큰을 선택하기만 하면 반드시 수락됩니다. 반면 높은 temperature에서는 분포가 더 uniform해져 draft 모델이 target 분포를 정확히 모방하기 어렵습니다.

### Speculative Decoding이 효과적인 조건

Speculative decoding이 최대 효과를 발휘하는 조건을 정리하면:

1. **큰 target 모델**: 모델이 클수록 memory-bound 특성이 강해져 speculative decoding의 이점이 큽니다
2. **작은 배치 크기**: 배치 크기 1~4에서 가장 효과적이며, 32 이상에서는 효과가 크게 줄어듭니다
3. **예측 가능한 텍스트**: 반복적 패턴이 있는 텍스트(코드, 형식화된 문서)에서 수락률이 높습니다
4. **충분한 GPU 메모리**: Draft 모델을 함께 로드할 여유가 있어야 합니다(self-draft 방식 제외)
5. **낮은 sampling temperature**: Greedy 또는 낮은 temperature에서 수락률이 극대화됩니다

## 의의 및 한계

### 본 서베이의 의의

1. **체계적 분류 프레임워크**: Draft-Centric vs. Model-Centric이라는 이분법은 기존 서베이(예: Xia et al., 2025의 2502.19732)의 분류와 차별화됩니다. 기존 서베이들이 주로 draft 모델의 유형(independent model, self-draft, retrieval 등)에 따라 분류한 반면, 본 서베이는 **혁신의 초점이 어디에 있는가**라는 더 근본적인 기준을 제시합니다.

2. **시각적 직관의 제공**: Figure 2의 Draft-Centric vs. Model-Centric 비교 그림은 두 접근법의 핵심 차이를 한눈에 파악할 수 있게 합니다. 이러한 시각적 설명은 실무자가 자신의 상황에 맞는 접근법을 선택하는 데 도움이 됩니다.

3. **타임라인을 통한 발전 맥락 이해**: Figure 3의 타임라인은 각 방법론이 등장한 시점과 상호 영향 관계를 보여주며, 연구 흐름의 전체적인 맥락을 제공합니다.

4. **실용적 관점의 비교**: 메모리 비용, 학습 비용, 적용 시나리오 등 실무적 관점에서의 분석을 포함하여, 연구자뿐만 아니라 엔지니어에게도 유용합니다.

### 한계점

1. **정량적 벤치마크 부재**: 다양한 방법론을 동일한 조건에서 비교하는 정량적 실험 결과가 부족합니다. 각 논문이 서로 다른 모델, 데이터셋, 하드웨어에서 실험했기 때문에 공정한 비교가 어렵습니다.

2. **배치 추론(Batched Inference) 분석 부족**: 실제 서비스 환경에서는 여러 요청을 동시에 처리하는 배치 추론이 일반적입니다. Speculative decoding은 배치 크기가 커질수록 이점이 줄어드는 경향이 있는데(memory-bound → compute-bound 전환), 이에 대한 심층 분석이 부족합니다.

3. **하드웨어 의존성 분석 부족**: Speculative decoding의 효과는 GPU 아키텍처, 메모리 대역폭, 연산 능력 등 하드웨어 특성에 크게 의존합니다. 다양한 하드웨어에서의 성능 분석이 제한적입니다.

4. **최신 기법 미포함**: 2024년 하반기 이후 등장한 방법론(예: Jacobi decoding 기반 접근법, lookahead decoding 등)은 다루지 않았습니다. 급격히 발전하는 분야 특성상 서베이의 범위가 제한적일 수밖에 없습니다.

5. **응용 도메인별 분석 부족**: 코드 생성, 수학 추론, 대화, 요약 등 다양한 응용 도메인에서 각 방법론의 상대적 성능이 어떻게 달라지는지에 대한 분석이 필요합니다.

### 미래 연구 방향

본 서베이를 바탕으로 다음과 같은 미래 연구 방향이 도출됩니다:

1. **Adaptive Speculation**: 입력의 난이도에 따라 speculation 전략(길이, tree 구조, draft 모델)을 동적으로 선택하는 방법. EAGLE-2가 이 방향의 초기 시도이지만, 더 정교한 적응 메커니즘이 필요합니다.

2. **Hardware-Software Co-design**: Speculative decoding에 최적화된 하드웨어 가속기 설계. Tree attention의 불규칙한 연산 패턴을 효율적으로 처리하는 전용 하드웨어가 연구될 수 있습니다.

3. **Multi-modal Speculative Decoding**: Vision-Language Model, Audio-Language Model 등 다양한 멀티모달 모델에 대한 speculative decoding의 확장.

4. **Speculative Decoding + Other Optimizations**: Quantization, KV cache 최적화, continuous batching 등 기존 최적화 기법과의 조합을 통한 multiplicative speedup 달성.

5. **Draft-Centric과 Model-Centric의 융합**: 두 접근법의 장점을 결합하는 하이브리드 방법론. 예를 들어, 개선된 draft 모델(Model-Centric)이 생성한 토큰을 tree 구조(Draft-Centric)로 조직하는 통합 프레임워크.

## 결론

Speculative decoding은 LLM 추론 가속의 가장 유망한 접근법 중 하나로, 출력 품질을 완전히 보존하면서 2~3배 이상의 speedup을 달성할 수 있다는 독보적인 장점을 가집니다. 본 서베이는 이 분야를 Draft-Centric과 Model-Centric이라는 직관적이고 체계적인 프레임워크로 정리함으로써, 연구자와 실무자 모두에게 speculative decoding 방법론의 전체적인 지형도를 제공합니다.

2018년 Blockwise Parallel Decoding에서 시작된 이 분야는 불과 6년 만에 30개 이상의 방법론이 제안될 정도로 폭발적으로 성장했습니다. 특히 2024년에는 EAGLE, Sequoia, REST 등 실용적으로 우수한 방법들이 다수 등장하여, speculative decoding이 연구 단계를 넘어 실제 서비스에 적용되기 시작했습니다. 이미 vLLM, TensorRT-LLM, Hugging Face TGI 등 주요 추론 프레임워크에서 speculative decoding을 공식 지원하고 있으며, 이는 이 기법의 실용적 가치가 검증되었음을 의미합니다.

본 서베이의 Draft-Centric vs. Model-Centric 분류 체계는 이 빠르게 확장되는 분야를 이해하는 유용한 렌즈를 제공합니다. 새로운 방법론이 제안될 때 "이것은 더 나은 draft를 만드는 데 집중하는가, 아니면 draft를 더 효율적으로 선택/구성하는 데 집중하는가?"라는 질문을 통해 빠르게 위치를 파악할 수 있습니다.

앞으로 Draft-Centric과 Model-Centric의 장점을 결합하는 하이브리드 접근법, 하드웨어-소프트웨어 공동 설계, 멀티모달 확장 등이 이 분야의 핵심 연구 방향이 될 것입니다. 궁극적으로 speculative decoding은 quantization, KV cache 최적화, continuous batching 등 다른 추론 최적화 기법들과 함께 **LLM 추론 효율성의 종합적 솔루션**을 구성하는 핵심 요소로 자리잡을 것으로 예상됩니다.
