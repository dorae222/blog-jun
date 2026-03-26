## 개요

"TiDAR: Think in Diffusion, Talk in Autoregression" (Jingyu Liu et al., 2025)은 **Autoregressive(AR) 모델의 높은 생성 품질**과 **Diffusion 모델의 병렬 생성 속도**를 하나의 모델 아키텍처 안에서 결합한 혁신적인 연구입니다. 논문의 제목이 함축하듯, "Diffusion으로 사고(think)하고, Autoregression으로 말(talk)하라"는 철학을 구현합니다. 즉, 다음에 올 토큰 블록을 Diffusion으로 병렬 초안(draft)하고, 실제 출력은 AR의 인과적(causal) 샘플링으로 확정하는 이중 구조입니다.

기존의 텍스트 생성은 크게 두 갈래로 나뉘었습니다. **AR 모델**(GPT, LLaMA 등)은 한 번에 한 토큰씩 순차적으로 생성하여 높은 품질을 보장하지만, 토큰 수만큼의 forward pass가 필요해 느립니다. 반면, **Discrete Diffusion 모델**(MDLM, LLaDA, Dream 등)은 마스크된 토큰을 병렬로 복원하여 빠르지만, 토큰 간 의존성을 충분히 포착하지 못해 품질이 떨어집니다. TiDAR는 이 두 가지의 장점을 하나의 forward pass에서 동시에 실현합니다.

핵심 성과를 요약하면 다음과 같습니다:

- **1.5B 모델**: Qwen2.5 1.5B 대비 **4.71배 처리량(throughput) 가속**을 달성하면서 HumanEval 평균 43.29%, MBPP 41.40%, GSM8K 53.90%로 AR 수준의 품질 유지
- **8B 모델**: Qwen3 8B 대비 **5.91배 가속**을 달성하면서 HumanEval 57.93%, MBPP 65.40%, GSM8K 80.44%를 기록
- Speculative decoding(EAGLE-3)과 Block Diffusion 모두를 **효율-품질 파레토 프론티어**에서 압도
- 별도의 Draft 모델 없이 **단일 모델의 단일 forward pass**로 초안 생성과 검증을 동시 수행
- 추론 시 **하이퍼파라미터 튜닝이 불필요**하며, AR 모델과 동일한 **정확한 KV cache** 지원

이 논문이 제시하는 패러다임은 단순히 "더 빠른 생성"을 넘어, **AR과 Diffusion이 배타적 선택이 아니라 상보적 역할로 공존할 수 있음**을 이론적, 실험적으로 증명한다는 점에서 의미가 깊습니다.

## 배경 및 문제

### AR 모델의 구조적 한계: 순차 생성의 병목

현재 대규모 언어 모델(LLM)의 주류는 Autoregressive 방식입니다. GPT 시리즈, LLaMA, Qwen 등 거의 모든 최신 LLM이 이 패러다임을 따릅니다. AR 모델은 다음 토큰의 확률 분포를 조건부로 모델링합니다:

$$p_{\text{AR}}(\mathbf{x}; \theta) = \prod_{i=1}^{n} p_\theta(x_i \mid x_{<i})$$

이 수식은 chain rule of probability에 의한 정확한 분해입니다. 즉, 시퀀스 $\mathbf{x} = (x_1, x_2, ..., x_n)$의 결합 확률을 조건부 확률의 곱으로 표현한 것이므로, **어떤 근사도 포함하지 않습니다**. 이것이 AR 모델의 높은 생성 품질의 수학적 근거입니다.

그러나 이 인과적(causal) 구조는 근본적인 병목을 내포합니다. 길이 $n$의 시퀀스를 생성하려면 **정확히 $n$번의 forward pass**가 필요합니다. 토큰 $x_i$를 생성하려면 반드시 $x_1, x_2, ..., x_{i-1}$이 모두 확정되어야 하므로, 병렬화가 원천적으로 불가능합니다. 이는 학습(training) 단계에서는 teacher forcing을 통해 모든 위치를 병렬로 처리할 수 있는 것과 대조적입니다.

현대 GPU 아키텍처(NVIDIA H100, A100 등)는 수천 개의 CUDA 코어와 Tensor 코어를 갖추고 있어 대규모 병렬 연산에 최적화되어 있습니다. 그러나 AR 디코딩에서는 **한 번에 단 하나의 토큰만 생성**하므로, 이 방대한 병렬 처리 능력의 대부분이 유휴 상태로 낭비됩니다. 구체적으로:

- **학습 시**: batch size $\times$ sequence length 만큼의 토큰을 동시에 처리하므로 GPU 활용률이 높습니다
- **추론 시 (prefill)**: 입력 프롬프트의 모든 토큰을 동시에 처리하므로 GPU 활용률이 높습니다
- **추론 시 (decoding)**: 한 번에 1개의 토큰만 생성하므로 GPU 활용률이 극히 낮습니다

특히 batch size가 1인 실시간 추론 시나리오(챗봇, 코드 어시스턴트 등)에서 이 문제가 가장 두드러집니다. 이러한 맥락에서 "AR 디코딩의 GPU 활용률을 어떻게 높일 것인가?"가 TiDAR의 출발점입니다.

### Discrete Diffusion 모델의 등장과 한계

이 병목을 해결하기 위해 **Discrete Diffusion Language Model**이라는 새로운 패러다임이 등장했습니다. 연속 공간(continuous space)의 이미지 생성에서 성공한 Diffusion 모델을 이산 공간(discrete space)의 텍스트 생성에 적용한 것입니다. MDLM (Sahoo et al., 2024), SEDD (Lou et al., 2024), LLaDA (Nie et al., 2025), Dream (Dream et al., 2025) 등이 대표적이며, 이들은 마스크된 토큰을 병렬로 복원(denoising)합니다:

$$p_{\text{Diff}}(\mathbf{x}; \theta) = \mathbb{E}_{\tilde{\mathbf{x}} \sim q(\cdot|\mathbf{x})} \prod_{i} p_\theta(x_i \mid \tilde{\mathbf{x}})$$

여기서 $q(\cdot|\mathbf{x})$는 원본 토큰을 마스크 토큰 $[\text{mask}]$으로 변환하는 forward corruption process입니다. 생성 시에는 이 과정을 역방향으로 수행하여, 전체가 마스크된 시퀀스에서 시작하여 점진적으로 토큰을 복원합니다.

Diffusion 모델은 한 번의 forward pass로 **여러 마스크 위치를 동시에 복원**할 수 있어 이론적으로 빠릅니다. 그러나 근본적인 한계가 있습니다.

#### 독립 가정(Independence Assumption)의 문제

Diffusion 모델에서 각 토큰의 예측은 **주변 분포(marginal distribution)**에 기반합니다. 즉, 다른 마스크 위치의 값과 독립적으로 각 위치를 예측합니다. $K$개의 마스크 위치에 대해:

$$p_{\text{Diff,Independent}}^K(\mathbf{x}; \theta) = \mathbb{E}_{\tilde{\mathbf{x}} \sim q(\cdot|\mathbf{x}),\ \tilde{x}_{i \in K} = [\text{mask}]} \prod_{i \in K} p_\theta(x_i \mid \tilde{\mathbf{x}})$$

이 독립 가정은 **토큰 간 일관성(consistency) 저하**로 이어집니다. 구체적인 예를 들어보겠습니다:

**예시 1: 고유명사**
- 프롬프트: "The capital of France is ___"
- AR 모델: $p(\text{Paris}) = 0.95$ (한 토큰으로 정확히 생성)
- Diffusion 모델 (2토큰 동시 생성): $p(\text{Pa}) \times p(\text{ris})$를 독립적으로 예측. "Pa" 위치에서 "Ne"를, "ris" 위치에서 "ris"를 생성하면 "Neris"라는 무의미한 결과가 나올 수 있습니다.

**예시 2: 코드 생성**
- `for i in range(___):` 에서 `10`을 2토큰으로 생성할 때, `1`과 `0`이 독립적으로 예측되어 `1` 다음에 `5`가 오는 등의 불일치가 발생할 수 있습니다.

AR 모델은 $p(\text{0} \mid \text{1}, \text{context})$를 직접 모델링하므로 이런 문제가 구조적으로 발생하지 않습니다.

#### KV Cache 불가능

또 다른 중요한 한계는 **KV cache를 활용할 수 없다**는 점입니다. AR 모델에서는 이전에 계산된 토큰의 Key/Value를 캐시하여 다음 토큰 생성 시 재활용합니다. 이를 통해 각 step에서 새로운 토큰 하나만 처리하면 됩니다. 그러나 Diffusion 모델은 매 denoising step마다 **전체 시퀀스를 재계산**해야 합니다. 왜냐하면 각 step에서 마스크 위치가 변경되고, 양방향(bidirectional) attention을 사용하므로 이전 계산 결과를 재활용할 수 없기 때문입니다.

이로 인해 Diffusion 모델은 한 step에서 여러 토큰을 동시에 생성하더라도, step 수가 늘어나면 전체 연산량이 AR보다 커질 수 있습니다. 특히 긴 시퀀스에서 이 문제가 심각해집니다.

### Speculative Decoding: 기존의 가속 접근법

AR 모델 가속의 대표적 접근법인 **Speculative Decoding**(Leviathan et al., 2023; Chen et al., 2023)은 "Draft-then-Verify" 패러다임을 제시했습니다. 기본 아이디어는 다음과 같습니다:

1. **Draft 단계**: 작고 빠른 Draft 모델 $M_{\text{draft}}$가 $K$개의 토큰을 빠르게 생성합니다
2. **Verify 단계**: 크고 정확한 Target 모델 $M_{\text{target}}$이 한 번의 forward pass로 $K$개의 토큰을 동시에 검증합니다
3. **Acceptance**: Rejection sampling을 통해 $M_{\text{target}}$의 분포와 일치하는 토큰만 수락합니다

이 방식은 Target 모델의 출력 분포를 정확히 재현하면서도, Draft 모델이 충분히 정확하면 여러 토큰이 한 번에 수락되어 가속을 달성합니다. 그러나 두 가지 실용적 한계가 있습니다:

1. **별도의 Draft 모델이 필요합니다**: Draft 모델의 학습, 관리, GPU 메모리 적재 비용이 추가됩니다. EAGLE-3과 같은 최신 기법은 feature-level draft 모델을 사용하여 정확도를 높이지만, 여전히 추가 파라미터와 학습이 필요합니다.

2. **Draft와 Verify가 순차적입니다**: Draft 후 Verify, 다시 Draft 후 Verify의 순환이 직렬로 수행됩니다. Verify 결과를 알아야 다음 Draft를 시작할 수 있으므로, 두 단계 사이의 직렬 오버헤드가 발생합니다.

TiDAR는 이 두 가지 한계를 모두 극복합니다. 별도의 Draft 모델 없이 **자기 자신이 Draft와 Verify를 하나의 forward pass에서 동시에 수행**합니다.

### Latency Scaling: TiDAR를 가능하게 한 핵심 통찰

TiDAR의 설계를 가능하게 한 핵심 관찰은 현대 GPU에서의 **Latency Scaling** 현상입니다. 이 관찰은 단순하지만 매우 중요합니다.

![GPU Latency Scaling 분석](figures/fig_1.png)
*Figure 1: GPU Latency Scaling. Qwen3-32B를 NVIDIA H100에서 batch size=1, Flash Attention 2로 디코딩할 때의 latency를 token slot 수에 따라 측정한 결과. 다양한 prefix 길이(64, 256, 1024, 4096)에서 일정 수의 토큰까지는 latency가 거의 일정(free + cheap slots)하다가, 이후 compute-bound 구간으로 전환된다.*

현대 GPU에서 Transformer의 forward pass latency는 처리하는 토큰 수에 대해 **비선형적**입니다. 이를 이해하려면 GPU의 연산 모델을 알아야 합니다.

#### Memory-Bound vs. Compute-Bound

GPU 연산은 두 가지 병목에 의해 제한됩니다:

- **Memory-Bound**: 데이터를 GPU 메모리(HBM)에서 읽어오는 속도가 병목. 연산 유닛은 유휴 상태.
- **Compute-Bound**: 연산 유닛(Tensor Core, CUDA Core)의 처리 속도가 병목. 데이터는 충분히 빨리 공급됨.

AR 디코딩에서 1개의 토큰만 처리할 때, 모델 가중치를 메모리에서 로드하는 시간이 실제 연산 시간보다 훨씬 깁니다. 즉, **memory-bound** 상태입니다. 이 상태에서 토큰을 추가로 처리해도, 어차피 가중치 로드 시간이 지배적이므로 latency가 거의 변하지 않습니다.

이로부터 세 가지 구간이 자연스럽게 도출됩니다:

1. **Free Token Slots**: 토큰을 추가해도 latency가 **전혀 증가하지 않는** 구간. 추가 토큰의 연산이 가중치 로드 대기 시간에 완전히 숨겨집니다.
2. **Cheap Token Slots**: 토큰을 추가하면 latency가 **약간만 증가**하는 구간. Memory-bound에서 Compute-bound로의 전환 영역입니다.
3. **Compute-Bound Regime**: 토큰 추가가 latency를 **선형적으로 증가**시키는 구간. GPU의 연산 유닛이 완전히 포화됩니다.

Figure 1에서 이 특성이 명확히 관찰됩니다. 예를 들어, prefix 길이 1024에서 약 16개의 추가 토큰까지는 latency가 거의 일정하고, 이후부터 선형적으로 증가합니다.

#### TiDAR에의 함의

이 관찰의 의미는 강력합니다. AR 디코딩에서 한 토큰만 생성하면 대부분의 GPU 자원이 낭비됩니다. 만약 **같은 latency 내에서 여러 토큰을 동시에 처리**할 수 있다면, 사실상 "공짜"로 병렬 생성이 가능합니다.

TiDAR는 이 Free/Cheap Token Slots를 활용하여 Diffusion 기반 초안(pre-draft) 생성을 AR 디코딩에 "무료로 끼워넣습니다." AR 검증을 위한 draft 토큰과 다음 단계를 위한 mask 토큰을 함께 처리해도, 이들이 Free/Cheap Slots에 들어가면 총 latency 증가가 미미합니다. 이것이 TiDAR가 5~6배의 throughput 가속을 달성하면서도 wall-clock time 기준으로도 실질적인 가속을 보이는 이유입니다.

## 핵심 아이디어

TiDAR의 핵심은 세 가지 설계 원리로 요약됩니다. 이 세 가지는 각각 독립적인 기여가 아니라, 서로 긴밀하게 연결되어 전체 시스템의 효율과 품질을 동시에 보장합니다.

### 1. AR의 Joint Distribution + Diffusion의 Marginal Distribution

AR 모델은 토큰 시퀀스의 **결합 분포(joint distribution)**를 정확히 모델링합니다. Chain rule에 의해:

$$p(x_1, x_2, ..., x_n) = p(x_1) \cdot p(x_2 \mid x_1) \cdot p(x_3 \mid x_1, x_2) \cdots p(x_n \mid x_{<n})$$

이 분해는 어떤 근사도 포함하지 않으므로, 각 토큰이 이전 모든 토큰에 대한 완전한 의존성을 가집니다.

반면, Diffusion 모델은 각 토큰의 **주변 분포(marginal distribution)** $p(x_i \mid \text{context})$를 독립적으로 예측합니다. 개별 토큰의 예측 정확도는 높을 수 있지만, 여러 토큰을 동시에 생성할 때 **토큰 간 일관성을 보장하지 못합니다**.

TiDAR의 통찰은 이 두 분포를 **역할 분리**하는 것입니다:

- **Diffusion (사고/think)**: 다음에 올 토큰 블록의 초안(draft)을 병렬로 생성. Marginal distribution을 활용하여 빠르게 "대략적인" 예측을 수행합니다. 완벽할 필요 없이, "그럴듯한(plausible)" 후보를 만들면 됩니다.
- **AR (말/talk)**: 초안된 토큰을 순차적으로 검증하고 최종 출력을 확정. Joint distribution으로 토큰 간 일관성을 보장합니다. 초안이 정확하면 빠르게 수락하고, 부정확하면 교정합니다.

이 구조에서 Diffusion은 "대략적인 방향을 제시하는 직관(intuition)"의 역할을, AR은 "정확성을 보장하는 논리적 검증(verification)"의 역할을 수행합니다. 인간의 사고 과정에 비유하면, 빠르고 대략적인 System 1 사고(Diffusion)와 느리지만 정확한 System 2 사고(AR)의 결합과 유사합니다.

이는 Speculative Decoding의 Draft-Verify 패러다임과 구조적으로 유사하지만, **별도의 Draft 모델 없이 하나의 모델이 두 역할을 동시에 수행**한다는 점에서 근본적으로 다릅니다.

### 2. 단일 Forward Pass에서 Draft + Verify + Pre-Draft

전통적인 Speculative Decoding의 시간적 흐름은 다음과 같습니다:

```
Step t:   [Draft Model 실행] → [Target Model 실행] → [수락/거절 결정]
Step t+1: [Draft Model 실행] → [Target Model 실행] → [수락/거절 결정]
...
```

각 step 내에서 Draft와 Verify가 직렬로 수행되고, step 간에도 순차적입니다. TiDAR는 이 구조를 근본적으로 재설계합니다:

```
Step t의 Single Forward Pass:
  ├── [이전 draft 토큰 AR 검증] (causal attention)  ─── 현재 step의 Verify
  └── [다음 step의 draft 생성] (block-causal attention) ── 다음 step의 Draft
```

하나의 forward pass에서 세 가지를 동시에 처리합니다:

1. 이전 단계에서 초안된 토큰을 **AR로 검증/샘플링** (causal attention)
2. 수락된 프리픽스에 기반하여 **다음 단계의 초안을 Diffusion으로 생성** (block-causal attention)
3. **KV cache 관리**: 수락된 토큰의 KV cache를 유지, 거절된 토큰의 KV cache를 폐기

이를 통해 Draft와 Verify 사이의 직렬 오버헤드가 완전히 제거됩니다. 한 step의 Verify와 다음 step의 Draft가 **동시에** 수행되므로, wall-clock time 기준으로 사실상 Draft 비용이 "무료"가 됩니다.

### 3. Block-Causal Attention으로 두 세계를 연결

하나의 Transformer forward pass에서 AR과 Diffusion을 동시에 수행하려면, 시퀀스의 서로 다른 영역에 서로 다른 Attention 패턴이 필요합니다. AR은 causal(왼쪽만 참조), Diffusion은 bidirectional(양방향 참조)을 요구합니다. TiDAR는 이를 **구조화된 Attention Mask**로 해결합니다:

- **Clean 토큰(이미 확정된 프리픽스 + draft 토큰)**: 일반적인 **Causal Attention**을 적용합니다. 각 토큰은 자신 이전의 토큰만 참조합니다. 이를 통해 AR의 조건부 분포를 정확히 계산합니다.
- **Mask 토큰(Diffusion 초안 대상)**: 같은 블록 내에서는 **Bidirectional Attention**을 적용하고, 이전 블록과 프리픽스에 대해서는 Causal Attention을 적용합니다. 이를 통해 블록 내 토큰들이 서로의 정보를 참조하여 더 일관된 초안을 생성합니다.

이 Block-Causal Attention은 clean 토큰 영역에서 AR의 인과적 구조를 **엄격하게** 유지하면서, mask 토큰 영역에서 Diffusion의 양방향 정보 교환을 가능하게 합니다. 중요한 것은 **clean 토큰이 mask 토큰을 절대 참조하지 않는다**는 점입니다. 이를 통해 clean 토큰 영역의 AR 예측이 mask 토큰에 의해 오염(contamination)되지 않습니다.

## TiDAR 아키텍처

### 전체 구조

![TiDAR 아키텍처 개요](figures/fig_2.png)
*Figure 2: TiDAR 아키텍처. 단일 forward pass에서 이전 단계의 초안 토큰을 AR로 샘플링하고, 동시에 다음 단계의 초안을 Diffusion으로 생성한다. Clean 토큰은 causal attention, mask 토큰은 block-causal attention(블록 내 양방향)을 적용한다. Draft 길이 3, 수락 길이 2인 예시를 보여준다.*

TiDAR의 추론 시 하나의 forward pass에서 처리되는 시퀀스는 세 개의 영역으로 구성됩니다:

**1. Prefix (프리픽스)**

이전까지 수락되어 확정된 토큰들입니다. 이들의 KV cache는 이미 저장되어 있으므로 재계산이 필요 없습니다. 프리픽스 길이를 $P$라 하면, KV cache의 크기는 $P \times d_{\text{model}}$입니다.

**2. Draft Tokens (이전 단계의 초안 토큰)**

이전 Diffusion step에서 생성된 초안 토큰들입니다. 이들은 현재 forward pass에서 AR의 causal attention으로 처리되어, 수락 여부가 결정됩니다. Draft 길이를 $K$라 하면, $K$개의 토큰이 프리픽스 뒤에 배치됩니다.

이 토큰들은 **정확히 AR 디코딩에서와 동일한 causal attention**을 적용받습니다. 즉, 위치 $P + j$의 토큰은 프리픽스 $x_1, ..., x_P$와 이전 draft 토큰 $x_{P+1}, ..., x_{P+j-1}$만 참조합니다. 이를 통해 각 위치에서의 AR 확률 $p_\theta(x_{P+j} \mid x_{\leq P+j-1})$이 정확하게 계산됩니다.

**3. Mask Tokens (다음 단계를 위한 마스크 위치)**

$[\text{mask}]$ 토큰으로 채워진 위치들입니다. 이들은 block-causal attention을 통해 Diffusion 방식으로 다음 단계의 초안을 생성합니다. 핵심적으로, 이 mask 토큰들은 **모든 가능한 수락 시나리오에 대해 조건부 초안을 동시에 생성**합니다.

왜 "모든 가능한 수락 시나리오"를 고려해야 할까요? Draft 토큰 $K$개에 대한 rejection sampling 결과, 수락 길이 $L$은 $0, 1, 2, ..., K$ 중 하나입니다. 수락 길이에 따라 다음 draft의 시작점이 달라지므로, mask 토큰은 각 시작점에 대응하는 초안을 미리 계산합니다. 수락 길이 $L$이 결정되면, 해당하는 초안 블록만 선택합니다.

핵심은 영역 (2)와 (3)이 **동일한 forward pass에서 병렬 처리**된다는 점입니다. GPU의 Free/Cheap Token Slots를 활용하므로, mask 토큰의 추가 처리가 latency를 거의 증가시키지 않습니다.

### Attention Mask 설계

![TiDAR Attention Mask 구조](figures/fig_3.png)
*Figure 3: TiDAR의 Attention Mask. (좌) 학습 시 마스크: block 길이 3으로 마스크 토큰을 입력에 append하여, clean 토큰은 causal self-attention, mask 토큰은 블록 내 양방향 attention + 프리픽스 참조를 수행한다. (우) 추론 시 병렬 디코딩 마스크: 사전 초기화된 마스크에서 현재 프리픽스 길이에 따라 slice하여 사용한다. 토큰 순서를 재배치하여 마스크 재사용을 최적화한다.*

TiDAR의 Attention Mask는 전체 시스템의 핵심 메커니즘입니다. 학습 시와 추론 시 마스크 구조를 상세히 분석합니다.

#### 학습 시 마스크 (Training Mask)

학습 시 입력 시퀀스는 다음과 같이 구성됩니다. 원본 시퀀스를 블록 크기 $B$로 분할한 후, 각 블록 뒤에 동일 길이의 $[\text{mask}]$ 토큰을 interleave합니다:

$$\underbrace{x_1, ..., x_B}_{\text{Block 1 (clean)}} \quad \underbrace{[\text{m}], ..., [\text{m}]}_{\text{Block 1 (mask)}} \quad \underbrace{x_{B+1}, ..., x_{2B}}_{\text{Block 2 (clean)}} \quad \underbrace{[\text{m}], ..., [\text{m}]}_{\text{Block 2 (mask)}} \quad \cdots$$

이 확장된 시퀀스에 대해 Attention Mask를 다음과 같이 구성합니다:

| 영역 | Query | Key | Attention 유형 | 이유 |
|------|-------|-----|--------------|------|
| Clean $\rightarrow$ Clean | Clean 토큰 | 이전 Clean 토큰 | Causal (하삼각) | AR next-token prediction을 위해 미래 정보 차단 |
| Mask $\rightarrow$ Clean | Mask 토큰 | 해당 블록까지의 Clean 프리픽스 | Causal | 마스크 복원 시 올바른 컨텍스트 참조 |
| Mask $\rightarrow$ Mask (같은 블록) | Mask 토큰 | 같은 블록의 다른 Mask 토큰 | Bidirectional | 블록 내 토큰 간 상호 정보 교환 |
| Clean $\rightarrow$ Mask | Clean 토큰 | Mask 토큰 | **차단 (Blocked)** | Clean 토큰이 Mask 정보에 오염되는 것 방지 |
| Mask $\rightarrow$ Mask (다른 블록) | Mask 토큰 | 다른 블록의 Mask 토큰 | **차단 (Blocked)** | 블록 간 독립성 유지 |

이 마스크 구조를 통해 모델은 동시에 두 가지를 학습합니다:

1. **Clean 토큰 영역**: 표준 AR next-token prediction. 위치 $i$의 clean 토큰은 $x_1, ..., x_{i-1}$만 참조하여 $x_{i+1}$을 예측합니다. 이는 표준 causal language modeling과 동일합니다.

2. **Mask 토큰 영역**: One-step Diffusion denoising. 마스크 토큰은 해당 블록까지의 clean 프리픽스와 같은 블록 내의 다른 마스크 토큰을 참조하여, 원본 토큰을 복원합니다.

#### 추론 시 마스크 (Inference Mask)

추론 시에는 시퀀스의 구조가 학습 시와 약간 다릅니다. Draft 토큰(이전 단계의 초안)이 clean 토큰처럼 causal하게 처리되고, 그 뒤에 다음 단계를 위한 mask 토큰이 배치됩니다.

추론 시 핵심 최적화는 **사전 초기화된 마스크의 slice 재사용**입니다. 구체적으로:

1. 모델 초기화 시 `(max_seq_len + block_size, max_seq_len + block_size)` 크기의 전체 마스크를 한 번 생성합니다
2. 각 추론 step에서 현재 프리픽스 길이에 따라 해당 영역을 slice하여 사용합니다
3. 이를 위해 추론 시 토큰 순서를 재배치합니다: `[Mask 토큰 | Draft 토큰 | Clean 프리픽스]`가 되도록 재정렬하여, 가변적인 프리픽스 길이에도 동일한 마스크 패턴을 재사용할 수 있게 합니다

이 최적화는 **FlexAttention**(PyTorch의 고성능 커스텀 attention 구현)을 활용하여 구현됩니다. 마스크 재생성의 오버헤드를 완전히 제거하며, block-sparse attention 패턴을 효율적으로 처리합니다.

#### Mask 토큰의 조건부 Pre-Draft 메커니즘

추론 시 mask 토큰의 가장 정교한 부분은 **모든 가능한 수락 시나리오를 동시에 처리**하는 것입니다. Draft 길이 $K = 3$인 경우를 예로 들면:

- **수락 길이 $L = 0$**: Draft가 모두 거절됨. 다음 draft는 현재 프리픽스 직후부터 시작
- **수락 길이 $L = 1$**: 첫 번째 draft만 수락. 다음 draft는 프리픽스 + 1토큰 뒤부터 시작
- **수락 길이 $L = 2$**: 두 번째까지 수락. 다음 draft는 프리픽스 + 2토큰 뒤부터 시작
- **수락 길이 $L = 3$**: 모두 수락. 다음 draft는 프리픽스 + 3토큰 뒤부터 시작

Mask 토큰은 이 4가지 시나리오 각각에 대한 초안을 **병렬로** 생성합니다. 각 mask 블록은 해당 시나리오의 프리픽스에 대해 block-causal attention을 적용받아, 올바른 컨텍스트 하에서 초안을 만듭니다. 수락 길이 $L$이 결정되면, 해당 블록만 선택하여 다음 step의 draft로 사용합니다.

이 방식이 가능한 이유는 block-causal attention 구조 덕분입니다. 각 mask 블록은 자신에 해당하는 프리픽스만 참조하고, 다른 시나리오의 mask 블록은 참조하지 않습니다. 따라서 여러 시나리오의 초안이 서로 간섭 없이 병렬로 계산됩니다.

### 추론 프로세스 상세

TiDAR의 추론을 단계별로 상세히 설명합니다. Draft 길이를 $K$라 하겠습니다.

**Step 0 (초기화)**:
1. 입력 프롬프트(프리픽스)를 causal attention으로 처리하여 KV cache를 생성합니다.
2. 프리픽스 뒤에 $K$개의 $[\text{mask}]$ 토큰을 배치하여 첫 번째 Diffusion 초안을 생성합니다. 이것이 Step 1에서 검증할 draft 토큰이 됩니다.
3. 프리픽스의 마지막 토큰에 대한 AR 예측으로 첫 번째 "bonus" 토큰도 생성합니다.

**Step $t$ ($t \geq 1$)**:
1. **입력 구성**: `[이전 draft 토큰 $K$개] + [mask 토큰]`을 KV cache에 추가하여 forward pass를 실행합니다. 프리픽스의 KV cache는 이미 저장되어 있으므로 재계산하지 않습니다. 총 forward 길이는 약 $2K$입니다.

2. **AR 샘플링 (Draft 토큰 영역)**: Draft 토큰들은 causal attention으로 처리됩니다. 각 위치 $j$ ($1 \leq j \leq K$)에서:
   - AR logits $\text{logits}_{P+j}^{\text{AR}}$을 계산합니다
   - AR 확률 $p_{\text{AR}}(x_{P+j} \mid x_{\leq P+j-1})$을 구합니다
   - 이전 Diffusion step의 예측 확률 $p_{\text{draft}}(x_{P+j})$와 비교하여 rejection sampling을 수행합니다

3. **Rejection Sampling**: 각 위치 $j$에서의 수락/거절 판정은 Speculative Decoding의 표준 rejection sampling을 따릅니다:

   Draft 토큰 $\hat{x}_{P+j}$에 대해:

   $$\text{Accept}(\hat{x}_{P+j}) = \begin{cases} \text{True} & \text{if } u \leq \min\left(1, \frac{p_{\text{AR}}(\hat{x}_{P+j} \mid x_{\leq P+j-1})}{p_{\text{draft}}(\hat{x}_{P+j})}\right) \\ \text{False} & \text{otherwise} \end{cases}$$

   여기서 $u \sim \text{Uniform}(0, 1)$입니다. 이 rejection sampling의 핵심 성질은 **수락된 토큰의 분포가 정확히 $p_{\text{AR}}$을 따른다는 것**입니다. 즉, TiDAR의 최종 출력은 AR 모델의 분포에서 샘플링한 것과 통계적으로 동일합니다.

   거절이 발생하면 해당 위치에서 수정된 분포로부터 교정 토큰을 샘플링합니다:

   $$x_{\text{corrected}} \sim \text{norm}\left(\max\left(0, p_{\text{AR}}(\cdot \mid x_{\leq P+j-1}) - p_{\text{draft}}(\cdot)\right)\right)$$

   거절 이후의 모든 draft 토큰은 폐기됩니다. 이는 AR의 chain rule에 의해, 현재 위치의 토큰이 변경되면 이후 모든 조건부 확률이 달라지기 때문입니다.

   이 rejection sampling은 **최종 출력이 AR 모델의 분포를 정확히 따르도록** 보장합니다. Draft가 완벽하면 모두 수락되고, 부정확하면 AR이 교정합니다.

4. **수락 길이 결정**: 연속으로 수락된 토큰의 수 $L$ ($0 \leq L \leq K$)을 결정합니다:
   - 수락된 토큰($L$개)의 KV cache는 유지합니다
   - 거절된 토큰($K - L$개)의 KV cache는 폐기(evict)합니다
   - 거절 위치에서 AR이 생성한 교정 토큰 1개를 추가로 수락합니다 (bonus token)

5. **Pre-Draft 선택 (Mask 토큰 영역)**: 수락 길이 $L$이 결정되면, 대응하는 mask 블록의 Diffusion 예측을 선택합니다. 이것이 다음 step의 draft 토큰이 됩니다.

6. **프리픽스 업데이트**: 프리픽스 길이를 $P \leftarrow P + L + 1$ (수락된 토큰 + bonus token)로 업데이트합니다.

7. **반복**: Step $t+1$로 진행합니다.

이 과정에서 핵심은 **Step 2-3의 AR 검증과 Step 5의 Diffusion 초안 생성이 동일한 forward pass에서 동시에 수행**된다는 점입니다. NFE(Number of Function Evaluations)당 생성되는 토큰 수는 평균 $L + 1$이며, 이 값이 클수록 가속 효과가 큽니다.

### KV Cache 관리

TiDAR의 KV cache 관리는 AR 모델과 동일한 정확성(exact caching)을 보장합니다. 이는 순수 Diffusion 모델에서는 달성할 수 없는 중요한 특성입니다.

- **수락된 토큰**: Causal attention으로 처리되었으므로, KV cache가 정확히 AR 모델의 것과 동일합니다. 해당 위치의 Key/Value 벡터는 오직 이전 토큰들에만 의존하므로, 이후 어떤 토큰이 추가되더라도 변하지 않습니다. 따라서 안전하게 유지할 수 있습니다.

- **거절된 토큰**: KV cache를 폐기(evict)합니다. 거절된 위치 이후의 시퀀스가 달라지므로, 해당 KV cache는 더 이상 유효하지 않습니다.

- **Mask 토큰**: Bidirectional attention으로 처리되어, KV cache가 다른 mask 토큰에 의존합니다. 따라서 KV cache를 유지하지 않습니다. 매 step에서 새로운 mask 토큰이 생성됩니다.

이 관리 전략은 Block Diffusion 모델과의 중요한 차이점입니다. Block Diffusion은 모든 블록이 양방향으로 처리되어 KV cache 재사용이 불가능합니다. TiDAR는 확정된 토큰에 대해 정확한 KV cache를 유지할 수 있어, 긴 시퀀스에서의 메모리 효율과 계산 효율이 모두 우수합니다.

### Tokens per NFE (T/NFE) 분석

TiDAR의 효율성을 측정하는 핵심 지표는 **T/NFE (Tokens per Number of Function Evaluations)**입니다. 이는 한 번의 forward pass(= 1 NFE)당 평균적으로 생성되는 토큰 수를 의미합니다.

- **AR 모델**: T/NFE = 1 (항상)
- **TiDAR 1.5B (B=16)**: T/NFE = 7.45 (평균)
- **TiDAR 8B (B=16)**: T/NFE = 8.25 (평균)

T/NFE가 높다는 것은 한 번의 forward pass에서 더 많은 토큰이 수락되었다는 의미이며, 이는 Diffusion 초안의 품질이 높다는 것을 의미합니다. TiDAR 8B에서 T/NFE = 8.25라는 것은, 평균적으로 8.25개의 토큰이 한 번의 forward pass에서 생성된다는 뜻입니다.

T/NFE와 실제 throughput 가속은 약간 다릅니다. 추가 토큰 처리에 따른 Free/Cheap Token Slot의 활용과 약간의 latency 증가를 고려하면, T/NFE 8.25에서 실제 throughput 가속은 5.91배가 됩니다.

### 구체적 추론 예시: 단계별 Walkthrough

TiDAR의 추론 과정을 코드 생성 예시로 구체적으로 따라가 보겠습니다. Draft 길이 $K = 3$으로 설정합니다.

**프롬프트**: `def fibonacci(n):`

**Step 0 (초기화)**:
```
입력: [def, fibonacci, (, n, ), :, M, M, M]
                                      |← mask →|
```

- 프리픽스 `[def, fibonacci, (, n, ), :]`를 causal attention으로 처리, KV cache 생성
- 마지막 clean 토큰 `:`에서 AR 예측 → bonus token `\n` 생성
- Mask 토큰 3개에서 Diffusion 예측 → draft 초안 `[if, n, <=]` 생성
- 프리픽스 업데이트: `[def, fibonacci, (, n, ), :, \n]`

**Step 1**:
```
입력 (KV cache + 새 토큰): [...cached..., if, n, <=, M, M, M, M, M, M]
                                          |← draft →| |← mask(L=0) →| |← mask(L=1) →| ...
```

- **AR 검증**: `if`에 대해 $p_{\text{AR}}(\text{if} \mid ...\text{:}\text{\textbackslash n})$를 계산
  - AR이 `if`를 높은 확률로 예측 → **수락**
- `n`에 대해 $p_{\text{AR}}(\text{n} \mid ...\text{if})$를 계산
  - AR도 `n`을 높은 확률로 예측 → **수락**
- `<=`에 대해 $p_{\text{AR}}(\text{<=} \mid ...\text{n})$를 계산
  - AR은 `==`를 더 높은 확률로 예측, `<=`는 낮은 확률 → **거절**
  - AR이 교정 토큰 `==` 생성 (bonus token)

- **수락 길이 $L = 2$**: `if`, `n`은 수락, `<=`는 거절
- **Pre-Draft 선택**: $L = 2$에 대응하는 mask 블록의 Diffusion 예측 선택 → 다음 draft `[0, :, \n]`
- **프리픽스 업데이트**: `[def, fibonacci, (, n, ), :, \n, if, n, ==]` (수락 2개 + bonus 1개)

**Step 2**:
```
입력 (KV cache + 새 토큰): [...cached..., 0, :, \n, M, M, M]
                                          |← draft →| |← mask →|
```

- **AR 검증**: `0`에 대해 AR 확인 → **수락** (`n == 0`이 자연스러움)
- `:` 확인 → **수락**
- `\n` 확인 → **수락** (Python 문법상 자연스러움)

- **수락 길이 $L = 3$**: 모두 수락! Diffusion 초안이 정확했습니다.
- Bonus token으로 AR이 추가로 `return` 생성
- **프리픽스 업데이트**: `[def, fibonacci, (, n, ), :, \n, if, n, ==, 0, :, \n, return]`

이 예시에서 Step 1에서는 3개 중 2개가 수락되어 T/NFE = 3, Step 2에서는 3개 전부 수락되어 T/NFE = 4입니다. 평균 T/NFE = 3.5로, 3.5배의 가속을 달성합니다.

핵심 관찰: Diffusion 초안이 완벽하지 않아도 됩니다. `<=` 대신 `==`가 필요한 상황에서 AR이 즉시 교정하여 품질을 유지합니다. 반면, Diffusion이 정확한 경우(Step 2의 `0, :, \n`) 모든 토큰이 한 번에 수락되어 최대 가속을 달성합니다.

### 연산 복잡도 분석

TiDAR의 연산 복잡도를 AR, Speculative Decoding, Block Diffusion과 비교합니다.

길이 $N$의 시퀀스를 생성할 때, 블록 크기 $B$, 평균 수락 길이 $\bar{L}$이라 하면:

| 방법 | Forward Pass 수 | Pass당 토큰 수 | KV Cache | 총 FLOPs (대략) |
|------|---------------|--------------|---------|---------------|
| AR | $N$ | 1 | 정확 | $N \cdot C_{\text{single}}$ |
| Speculative Decoding | $\frac{2N}{\bar{L}+1}$ | $B$ (draft) + $B$ (verify) | 정확 | $\frac{2N}{\bar{L}+1} \cdot C_{\text{batch}}(B)$ |
| Block Diffusion | $\frac{N \cdot T}{B}$ | $B$ | 불가 | $\frac{N \cdot T}{B} \cdot C_{\text{full}}(N)$ |
| **TiDAR** | $\frac{N}{\bar{L}+1}$ | $2B$ | 정확 | $\frac{N}{\bar{L}+1} \cdot C_{\text{batch}}(2B)$ |

여기서 $T$는 Block Diffusion의 denoising step 수, $C_{\text{single}}$은 1토큰 forward의 비용, $C_{\text{batch}}(k)$는 $k$토큰 forward의 비용입니다.

TiDAR의 핵심 이점은:
1. Forward pass 수가 Speculative Decoding의 절반 (Draft와 Verify가 합쳐짐)
2. Latency Scaling 덕분에 $C_{\text{batch}}(2B) \approx C_{\text{single}}$ (Free Token Slots 활용)
3. KV cache가 정확하므로 이전 계산을 완전히 재활용

## 학습 방법

### 학습 목표 (Training Objective)

TiDAR는 하나의 모델에 두 가지 학습 목표를 동시에 적용합니다:

$$\mathcal{L}_{\text{TiDAR}}(\theta) = \frac{1}{1+\alpha} \left[ \sum_{i=1}^{S-1} \frac{\alpha}{S-1} \cdot \mathcal{L}_{\text{AR}}(x_i, x_{i+1}; \theta) + \sum_{i=1}^{S-1} \frac{1}{S-1} \cdot \mathcal{L}_{\text{Diff}}([\text{mask}], x_i; \theta) \right]$$

여기서:
- $S$는 시퀀스 내 블록의 수
- $\alpha \in [0, 1]$는 AR loss와 Diffusion loss 간의 균형을 조절하는 하이퍼파라미터
- $\mathcal{L}_{\text{AR}}(x_i, x_{i+1}; \theta)$는 clean 토큰 $x_i$가 주어졌을 때 다음 토큰 $x_{i+1}$을 예측하는 표준 next-token prediction loss (cross-entropy)
- $\mathcal{L}_{\text{Diff}}([\text{mask}], x_i; \theta)$는 마스크 위치에서 원본 토큰 $x_i$를 복원하는 denoising loss (cross-entropy)

이 수식을 직관적으로 이해해 보겠습니다:

**AR Loss 항**: 정규화 계수 $\frac{\alpha}{(1+\alpha)(S-1)}$을 가지며, 모델이 clean 토큰을 순차적으로 읽을 때 다음 토큰을 정확히 예측하도록 학습합니다. 이는 표준 language modeling과 완전히 동일합니다. $\alpha$가 클수록 AR 성능에 더 많은 가중치를 부여합니다.

**Diffusion Loss 항**: 정규화 계수 $\frac{1}{(1+\alpha)(S-1)}$을 가지며, 모델이 마스크 토큰을 볼 때 해당 위치의 원래 토큰을 복원하도록 학습합니다. 이는 one-step denoising 능력을 부여합니다. Full Mask 전략에서는 모든 마스크 위치에서 loss를 계산하므로, $S-1$개의 Diffusion loss 항이 생깁니다.

전체 정규화 계수 $\frac{1}{1+\alpha}$는 두 loss의 합이 적절한 스케일을 유지하도록 합니다. $\alpha = 1$이면 AR과 Diffusion loss가 동등한 가중치를 가지고, $\alpha = 0$이면 Diffusion loss만 적용됩니다.

### Full Mask 전략

TiDAR의 학습에서 가장 중요한 설계 선택 중 하나는 **Full Mask 전략**입니다. 기존 Discrete Diffusion 모델들은 random corruption schedule을 사용합니다. 시간 $t$에서의 corruption rate $\gamma(t)$에 따라 입력의 일부($\gamma(t)$ 비율)만 마스킹하고, 나머지는 원본을 유지합니다. 이를 통해 모델은 다양한 noise level에서의 denoising을 학습합니다.

TiDAR는 이와 근본적으로 다른 접근을 취합니다. **Diffusion 영역의 모든 토큰을 $[\text{mask}]$로 설정**합니다. 즉, corruption rate가 항상 100%입니다. 이 전략의 장점은 세 가지입니다:

**1. 밀집한 Diffusion Loss 신호 (Dense Signal)**

Random masking에서는 마스킹되지 않은 위치의 loss가 0이므로, 실질적인 학습 신호가 마스킹된 위치에서만 발생합니다. 예를 들어, corruption rate가 50%이면 Diffusion loss의 유효 항 수는 절반으로 줄어듭니다. Full Mask 전략은 **모든 마스크 위치에서 loss를 계산**하므로, 학습 효율이 높습니다.

**2. 간단한 Loss 균형**

Full Mask에서는 AR loss 항의 수와 Diffusion loss 항의 수가 동일합니다 (각각 $S-1$개). 따라서 $\alpha$의 조절이 직관적입니다. Random masking에서는 마스킹 비율에 따라 유효 loss 항 수가 달라지므로, $\alpha$ 조절이 더 복잡해집니다.

**3. One-Step Inference와의 분포 일치**

TiDAR의 추론에서는 항상 **one-step denoising**을 수행합니다. 즉, 전체가 마스크된 블록에서 한 번의 forward pass로 모든 토큰을 예측합니다. 학습 시에도 항상 전체 마스크를 사용하면, 학습과 추론 사이의 **분포 불일치(distribution mismatch)**가 없습니다.

Random masking을 사용하면, 학습 시에는 일부 토큰이 보이는 상태에서 denoising하지만 추론 시에는 모든 토큰이 마스크된 상태에서 denoising해야 합니다. 이 불일치는 추론 품질을 저하시킬 수 있습니다.

실험적으로도 Full Mask 전략은 Random Mask 대비 **평균 약 3%p의 품질 향상**을 보여줍니다 (후술하는 Ablation Study 참조).

### Dual-Mode Backbone 학습

학습 시 입력 시퀀스의 구성을 좀 더 구체적으로 살펴보겠습니다. 블록 크기 $B = 4$이고 원본 시퀀스가 $[A, B, C, D, E, F, G, H]$인 경우:

```
학습 입력: [A, B, C, D, M, M, M, M, E, F, G, H, M, M, M, M]
            |←Block 1(clean)→| |←Block 1(mask)→| |←Block 2(clean)→| |←Block 2(mask)→|
```

여기서 $M = [\text{mask}]$입니다. 이 확장된 시퀀스의 길이는 원본의 2배가 됩니다 (이것이 시퀀스 길이 제약의 원인입니다).

이 구성에 Block-Causal Attention Mask를 적용하면:

- **Clean 토큰 영역**: `A`는 아무것도 참조하지 않고, `B`는 `A`만, `C`는 `A, B`만, `D`는 `A, B, C`만 참조합니다 (causal). `E`는 `A, B, C, D`만 참조하고, `F`는 `A, B, C, D, E`만 참조합니다. **Mask 토큰은 절대 참조하지 않습니다.**

- **Mask 토큰 영역 (Block 1)**: 4개의 mask 토큰은 서로를 양방향으로 참조하고, clean 프리픽스 `A, B, C, D`를 참조합니다. 이를 통해 `E, F, G, H`를 one-step으로 예측합니다.

이로써 모델은 **두 가지 역할을 동시에 수행할 수 있는 Dual-Mode Backbone**으로 학습됩니다. 중요한 것은 이 두 모드가 **동일한 파라미터를 공유**한다는 점입니다. 별도의 AR 모델과 Diffusion 모델이 아니라, 하나의 Transformer가 Attention Mask에 따라 두 가지 역할을 전환합니다. 파라미터 공유 덕분에 AR과 Diffusion 사이의 표현(representation)이 자연스럽게 정렬됩니다.

### Block Diffusion과의 차이: Label Leakage 방지

TiDAR와 Block Diffusion (Arriola et al., 2025)의 가장 중요한 구조적 차이를 상세히 분석합니다.

**Block Diffusion의 구조**: Block Diffusion은 시퀀스를 고정 크기의 블록으로 나누고, **모든 블록을 양방향(bidirectional) attention**으로 처리합니다. 블록 간에는 causal 관계가 있지만, 블록 내부에서는 모든 토큰이 서로 참조합니다.

이 구조의 문제는 **label leakage**입니다. 블록 내의 모든 토큰이 양방향으로 참조하므로, 위치 $i$의 예측에 $i+1$, $i+2$, ... 의 정보가 유입됩니다. 이렇게 되면 clean 토큰 영역에서 AR next-token prediction loss를 적용할 수 없습니다. 미래 토큰을 이미 "본" 상태에서 예측하는 것은 의미가 없기 때문입니다.

**TiDAR의 해결**: TiDAR는 **clean 토큰 영역을 엄격히 causal하게 유지**합니다. 양방향 attention은 오직 mask 토큰 영역(마지막 블록)에만 적용됩니다. 이를 통해:

1. Clean 토큰 영역에서 AR loss를 제약 없이 적용할 수 있습니다
2. AR backbone의 성능이 보존됩니다 (likelihood 벤치마크에서 확인)
3. Exact KV caching이 가능합니다 (clean 토큰의 KV는 이전 토큰에만 의존)

이것이 TiDAR가 AR 수준의 품질을 유지하면서 Diffusion의 속도 이점을 얻을 수 있는 핵심 이유입니다. Block Diffusion은 AR loss를 적용할 수 없어, 순수 Diffusion loss로만 학습되므로 품질 한계가 있습니다.

### 학습 하이퍼파라미터

모든 모델은 기존 사전 학습된 AR 모델로부터 **Continual Pretraining**으로 학습됩니다. 즉, AR 모델의 가중치를 초기값으로 사용하고, TiDAR의 Dual-Mode 학습 목표로 추가 학습합니다. 이는 scratch 학습 대비 학습 비용을 크게 절감합니다.

**1.5B 모델 (Qwen2.5 1.5B 기반)**:
- 학습 토큰: 50B (원본 사전학습 대비 소규모)
- Global batch size: 2M 토큰
- Optimizer: Distributed Adam
- Learning rate: max $1 \times 10^{-5}$, min $3 \times 10^{-6}$ (cosine schedule)
- Warmup: 전체 step의 1%
- 최대 시퀀스 길이: 4,096 (마스크 포함 시 원본 시퀀스 약 2,048)
- 블록 크기: 4, 8, 16 (각각 별도 모델 학습하여 비교)

**4B 모델 (Qwen3 4B 기반)**:
- 학습 토큰: 150B
- 블록 크기: 16

**8B 모델 (Qwen3 8B 기반)**:
- 학습 토큰: 150B
- 블록 크기: 16
- 나머지는 1.5B와 동일한 설정

학습 데이터와 설정을 통일한 이유는 **공정한 비교**를 위해서입니다. 같은 데이터로 AR 모델을 fine-tuning한 baseline (AR FT)과 비교하여, TiDAR의 품질 향상이 단순 추가 학습 효과가 아닌 아키텍처적 이점임을 보여줍니다.

### AR과 Diffusion 출력의 신뢰도 균형

TiDAR 모델은 같은 위치에 대해 AR과 Diffusion 두 가지 예측을 모두 생성합니다. Draft 토큰 위치에서는 AR logits($\text{logits}^{\text{AR}}$)이 causal attention을 통해 계산되고, Diffusion logits($\text{logits}^{\text{Diff}}$)은 이전 step의 mask 토큰에서 생성됩니다.

최종 출력을 결정할 때, 두 예측을 가중 결합하는 방식을 사용할 수 있습니다:

$$\hat{x}_i = \arg\max_{v \in |V|} \left\{ \beta \cdot \text{logits}_i^{\text{AR}} + (1 - \beta) \cdot \text{logits}_i^{\text{Diff}} \right\}$$

여기서 $\beta \in [0, 1]$은 AR 예측에 대한 신뢰도 가중치입니다. $\beta = 1$이면 AR만 사용하고, $\beta = 0$이면 Diffusion만 사용합니다.

논문의 실험에서 $\beta$를 0부터 1까지 변화시켜도 성능이 거의 일정하게 유지됩니다. 이는 매우 중요한 발견으로, 두 가지를 시사합니다:

1. **AR과 Diffusion의 예측이 잘 정렬(align)되어 있습니다**: Dual-Mode 학습이 두 모드 간의 일관성을 자연스럽게 달성합니다. 파라미터를 공유하므로, 같은 입력에 대해 두 모드가 유사한 출력을 생성하게 됩니다.

2. **추론 시 별도의 하이퍼파라미터 튜닝이 불필요합니다**: $\beta$ 값에 관계없이 성능이 안정적이므로, 사용자가 $\beta$를 고민할 필요가 없습니다. 이는 Block Diffusion의 confidence threshold와 대조적입니다. Block Diffusion에서는 threshold 값에 따라 품질-효율 트레이드오프가 크게 변하므로, 적절한 threshold를 찾기 위한 별도의 실험이 필요합니다.

## 실험 결과

### 실험 설정

TiDAR의 성능은 다양한 벤치마크에서 평가되었으며, 비교 대상은 다음과 같습니다:

**Baseline 모델**:
- **AR**: Qwen2.5 1.5B Base, Qwen3 8B Base/Instruct (원본 AR 모델)
- **AR + Fine-Tuned**: 동일한 데이터와 설정으로 추가 학습된 AR 모델 (TiDAR의 품질 향상이 추가 학습 자체의 효과인지 구분하기 위한 공정 비교 baseline)
- **EAGLE-3**: Qwen3 8B 기반 speculative decoding (별도 draft 모델 사용, 현 시점 SOTA)
- **Block Diffusion**: 1.5B 스케일의 block-level discrete diffusion 모델
- **LLaDA 8B**: Large-scale masked discrete diffusion 언어 모델
- **Dream 7B**: Machine-level discrete diffusion 언어 모델

**생성 벤치마크** (greedy decoding, pass@1):
- **코드 생성**: HumanEval, HumanEval+, MBPP, MBPP+
- **수학 추론**: GSM8K (8-shot), Minerva Math (4-shot)

**Likelihood 벤치마크** (log-probability 기반):
- **지식/이해**: MMLU (5-shot)
- **상식 추론**: ARC-Easy, ARC-Challenge, HellaSwag, PIQA, WinoGrande

모든 벤치마크는 `lm_eval_harness v0.4.8`로 평가되었으며, 속도 측정은 NVIDIA H100 GPU에서 batch size=1로 수행되었습니다.

### 효율-품질 벤치마킹

![효율-품질 벤치마킹 결과](figures/fig_4.png)
*Figure 4: 효율-품질 벤치마킹. 1.5B 및 8B 스케일에서 TiDAR, AR, EAGLE-3, Block Diffusion을 비교한다. x축은 AR 대비 상대 디코딩 throughput 가속 배수, y축은 개별 태스크 점수. 각 점 위의 숫자는 NFE(Number of Function Evaluations)당 평균 토큰 수. 같은 색의 점은 동일 모델 크기, 다른 마커는 다른 방법을 나타낸다.*

#### 1.5B 스케일 결과

| 벤치마크 | Qwen2.5 1.5B (AR) | Block Diff 1.5B (max) | Block Diff 1.5B (0.8) | TiDAR 1.5B (B=4) | TiDAR 1.5B (B=8) | TiDAR 1.5B (B=16) |
|---------|-------------------|----------------------|----------------------|------------------|-----------------|-------------------|
| HumanEval | 35.98% | 39.02% | - | 40.85% | 42.07% | **43.29%** |
| HumanEval+ | 29.88% | 28.66% | - | 33.54% | 34.15% | **35.98%** |
| MBPP | 43.60% | 34.00% | - | 39.20% | 40.80% | **41.40%** |
| MBPP+ | 37.83% | 29.89% | - | 37.04% | 38.10% | **39.42%** |
| GSM8K | 54.74% | 52.99% | - | 53.15% | 53.60% | 53.90% |
| T/NFE | 1.00 | - | - | 3.47 | 5.49 | 6.50 |
| **평균** | 41.64% | 38.41% | - | 40.76% | 41.74% | **44.03%** |

1.5B 스케일에서 TiDAR는 놀라운 결과를 보여줍니다:

**TiDAR > 원본 AR**: TiDAR 1.5B (B=16)는 원본 Qwen2.5 1.5B보다 **평균 2.39%p 높은 품질**을 달성하면서, 동시에 **4.71배의 throughput 가속**을 얻었습니다. 일반적으로 가속 기법은 품질을 희생하는데, TiDAR는 오히려 품질이 향상되었습니다. 이는 50B 토큰의 Continual Pretraining이 모델 능력을 추가적으로 향상시킨 결과입니다.

**TiDAR >> Block Diffusion**: Block Diffusion 대비 **평균 5.62%p 높은 품질**과 더 높은 throughput을 동시에 달성했습니다. Block Diffusion이 threshold를 낮추면(0.8) throughput은 증가하지만 품질이 급격히 하락하는 반면, TiDAR는 블록 크기를 4 → 8 → 16으로 키워도 품질 저하가 미미합니다. 이는 TiDAR의 AR rejection sampling이 품질을 안정적으로 보장함을 보여줍니다.

**블록 크기에 따른 스케일링**: 블록 크기를 키우면 T/NFE가 3.47 → 5.49 → 6.50으로 증가하면서, 품질도 40.76% → 41.74% → 44.03%으로 함께 증가합니다. 이는 직관에 반하는 결과입니다. 보통 더 많은 토큰을 동시에 예측하면 품질이 떨어질 것으로 예상되지만, TiDAR에서는 큰 블록이 더 긴 Continual Pretraining 데이터 exposure를 의미하므로(같은 50B 토큰에서 더 많은 mask 위치를 학습) 오히려 품질이 향상됩니다.

#### 8B 스케일 결과

| 벤치마크 | Qwen3 8B (AR) | LLaDA 8B | Dream 7B | EAGLE-3 | TiDAR 8B (Trust Diff) | TiDAR 8B (Trust AR) |
|---------|--------------|----------|----------|---------|----------------------|---------------------|
| HumanEval | 64.63% | 32.32% | 54.88% | 64.63% | 57.93% | 57.32% |
| HumanEval+ | 59.76% | 25.00% | 44.51% | 59.76% | 55.49% | 54.27% |
| MBPP | 69.40% | 40.80% | 56.80% | 69.40% | 65.40% | 65.60% |
| MBPP+ | 59.79% | 34.39% | 47.09% | 59.79% | 57.41% | 57.67% |
| GSM8K | 81.80% | 70.96% | 77.18% | 81.80% | 80.44% | 80.59% |
| T/NFE | 1.00 | - | - | ~3.5 | 8.25 | 8.23 |
| **평균** | 68.09% | 41.78% | 58.74% | 68.09% | **65.31%** | 65.09% |

8B 스케일에서는 더 극적인 대비가 드러납니다:

**TiDAR vs. 순수 Diffusion 모델**: LLaDA 8B 대비 **23.53%p**, Dream 7B 대비 **6.57%p** 높은 품질. 이 격차는 압도적이며, AR의 joint distribution 기반 검증이 Diffusion의 marginal 예측을 얼마나 효과적으로 보정하는지를 명확히 보여줍니다. 특히 LLaDA 8B의 HumanEval 32.32%와 TiDAR 8B의 57.93%는 거의 2배에 가까운 차이입니다.

**TiDAR vs. EAGLE-3 (Speculative Decoding)**: EAGLE-3은 Target 모델의 분포를 정확히 재현하므로 품질이 AR과 동일합니다 (lossless). 그러나 throughput 가속 배수가 TiDAR의 5.91배에 비해 낮습니다. 또한 EAGLE-3은 **별도의 draft 모델을 학습, 저장, GPU에 로드**해야 하는 실용적 부담이 있습니다. TiDAR는 단일 모델만으로 더 높은 가속을 달성합니다.

**TiDAR vs. AR**: Qwen3 8B 대비 품질 차이가 **2.78%p**에 불과하면서, throughput이 **5.91배** 높습니다. 이 수준의 품질 차이는 많은 실용적 시나리오에서 수용 가능하며, 5.91배의 가속은 사용자 체감 latency를 극적으로 줄입니다.

**Trust AR vs. Trust Diff**: AR 예측과 Diffusion 예측 중 어느 쪽을 신뢰하든 결과가 거의 동일합니다 (65.31% vs 65.09%). 이는 두 모드의 정렬이 잘 되어 있음을 확인합니다.

#### Likelihood 기반 벤치마크 (1.5B)

| 벤치마크 | Qwen2.5 1.5B | Block Diff 1.5B | TiDAR 1.5B |
|---------|-------------|-----------------|-----------|
| MMLU | 60.96% | 57.94% | 58.99% |
| ARC-Easy | 71.93% | 67.26% | 71.63% |
| ARC-Challenge | 45.05% | 45.73% | 45.39% |
| HellaSwag | 67.90% | 56.26% | 65.26% |
| PIQA | 76.82% | 74.43% | 76.17% |
| WinoGrande | 64.64% | 60.06% | 64.33% |
| **평균** | 65.16% | 61.05% | **64.43%** |

Likelihood 기반 벤치마크에서 TiDAR는 원본 AR 모델과 거의 동일한 성능을 유지합니다 (평균 0.73%p 차이). Block Diffusion 대비로는 **3.38%p 우위**를 보여줍니다.

이 결과는 특히 중요합니다. Likelihood 벤치마크는 모델의 **언어 모델링 능력 자체**를 평가하므로, TiDAR의 Dual-Mode 학습이 AR backbone의 성능을 거의 손상시키지 않았음을 확인합니다. 반면 Block Diffusion은 AR loss를 적용할 수 없어 HellaSwag 등에서 큰 성능 저하(-11.64%p)를 보입니다.

### 파레토 프론티어 분석

![파레토 프론티어 분석](figures/fig_5.png)
*Figure 5: 동일한 학습 조건에서의 파레토 프론티어 비교. 1.5B 스케일에서 AR, Fine-Tuned AR, Block Diffusion(다양한 threshold), TiDAR(다양한 draft 길이)의 성능-효율 트레이드오프를 보여준다. TiDAR가 모든 벤치마크에서 최적의 파레토 프론티어를 달성한다. 빨간 점선은 원본 AR 모델의 품질 수준.*

파레토 프론티어 분석은 TiDAR의 가장 강력한 논거입니다. 동일한 학습 데이터와 설정(same recipe)에서 각 방법의 **효율(T/NFE)-품질 트레이드오프**를 시각화했습니다.

**그래프 해석 방법**: x축은 T/NFE (높을수록 효율적), y축은 벤치마크 점수 (높을수록 정확). 이상적인 모델은 **우상단**에 위치합니다. 파레토 프론티어란, 같은 효율에서 최고의 품질 또는 같은 품질에서 최고의 효율을 달성하는 점들의 집합입니다.

각 방법의 파레토 프론티어 특성:

- **AR (1x T/NFE)**: 기준점. NFE당 1개의 토큰을 생성합니다. 품질은 높지만 효율이 최저입니다.
- **AR Fine-Tuned (1x T/NFE)**: 동일 데이터로 추가 학습하면 품질이 소폭 상승합니다. 이 baseline은 "TiDAR의 품질 향상이 단순 추가 학습 효과인지, 아키텍처 혁신 덕분인지"를 구분하기 위해 중요합니다.
- **Block Diffusion**: threshold를 max에서 0.8으로 낮추면 T/NFE가 증가(효율 향상)하지만, 품질이 급격히 하락합니다. 파레토 프론티어의 기울기가 가파릅니다.
- **TiDAR**: block 크기 4, 8, 16을 조절하면 T/NFE가 비례적으로 증가하면서, **품질 저하가 매우 완만**합니다. 모든 벤치마크에서 Block Diffusion과 AR의 파레토 프론티어를 **지배(dominate)**합니다.

특히 주목할 점은 두 가지입니다:

1. TiDAR의 Full Mask 변형(block=4, 8, 16)이 모두 Block Diffusion의 어떤 설정보다도 높은 품질과 효율을 달성합니다.
2. TiDAR의 가장 효율적인 설정(블록 크기 16, 약 7x T/NFE)이 **Fine-Tuned AR의 품질에 근접**합니다. 즉, 7배 빠른 속도에서 AR과 거의 동일한 품질을 달성합니다.

### Ablation Study

#### Full Mask vs. Random Mask

Full Mask 전략의 효과를 검증하기 위한 ablation 결과입니다:

| 마스킹 전략 | Draft 길이 | HumanEval Avg | MBPP Avg | GSM8K | 전체 평균 |
|-----------|-----------|--------------|---------|-------|---------|
| Random Mask | 4 | 32.62% | 48.63% | 55.11% | 45.45% |
| Random Mask | 8 | 33.85% | 48.77% | 54.43% | 45.68% |
| **Full Mask** | 4 | **38.42%** | **50.96%** | **55.87%** | **48.42%** |
| **Full Mask** | 8 | **39.94%** | **52.13%** | 54.74% | **48.94%** |

Full Mask 전략은 Random Mask 대비 **평균 약 3%p의 품질 향상**을 가져옵니다. 특히 코드 생성(HumanEval)에서 **5.8%p** (32.62% → 38.42%)의 큰 개선이 관찰됩니다. 이는 코드가 토큰 간 의존성이 높은 도메인이므로, one-step denoising에서 학습-추론 분포 일치가 더 중요하기 때문으로 해석됩니다.

반면 GSM8K에서는 Full Mask의 우위가 미미합니다 (55.87% vs 55.11%). 수학 추론은 중간 단계의 논리적 일관성이 중요한데, 이는 AR rejection sampling에 의해 이미 보장되므로 마스킹 전략의 영향이 상대적으로 작습니다.

#### 디코딩 전략 비교

TiDAR의 디코딩 전략을 Diffusion 모델에서 흔히 사용되는 다른 접근법과 비교합니다:

| 디코딩 전략 | T/NFE | HumanEval Avg | MBPP Avg |
|-----------|-------|--------------|---------|
| Confidence Max (확신도 최고 1개만) | 1.00 | 34.45% | 43.92% |
| Left-to-Right AR (순차적 1토큰) | 1.00 | 36.28% | 46.51% |
| Confidence > 0.9 (확신도 0.9 이상) | 2.63 | 32.01% | 42.50% |
| **TiDAR (4 drafts)** | 3.47 | **38.42%** | **50.96%** |
| **TiDAR (8 drafts)** | 5.49 | 39.94% | 52.13% |
| **TiDAR (16 drafts)** | 6.97 | 41.16% | 51.26% |

이 비교에서 핵심적인 관찰은:

1. **Confidence 기반 디코딩의 한계**: Confidence > 0.9 전략은 T/NFE 2.63으로 꽤 효율적이지만, 품질이 32.01%로 **T/NFE 1.00인 Left-to-Right AR보다도 낮습니다**. 이는 confidence threshold만으로는 토큰 간 일관성을 보장할 수 없음을 보여줍니다. "높은 confidence"가 반드시 "정확한 예측"을 의미하지 않습니다.

2. **TiDAR의 품질 보장**: TiDAR (4 drafts)는 T/NFE 3.47로 Confidence > 0.9보다 높은 효율을 보이면서, 품질도 38.42%로 **6%p 이상** 높습니다. 이는 AR rejection sampling이 **joint distribution 기반의 정확한 품질 보장**을 제공하기 때문입니다.

3. **스케일링 특성**: Draft 수를 4 → 8 → 16으로 늘리면 T/NFE가 3.47 → 5.49 → 6.97로 선형에 가깝게 증가하면서, 품질도 38.42% → 39.94% → 41.16%로 함께 증가합니다. 이 "효율을 높이면 품질도 좋아지는" 특성은 TiDAR 고유의 장점입니다.

## 관련 연구와의 비교

### Discrete Diffusion Language Models

최근 Discrete Diffusion Language Model 분야는 빠르게 발전하고 있습니다. 주요 연구들의 특성과 TiDAR와의 차이점을 체계적으로 정리합니다:

| 모델 | 접근법 | 토큰 간 의존성 | KV Cache | 별도 모델 | 품질 수준 |
|------|-------|-------------|---------|---------|---------|
| MDLM (Sahoo et al., 2024) | Continuous-time masked diffusion | 독립 (marginal) | 불가 | 불필요 | AR 대비 열등 |
| SEDD (Lou et al., 2024) | Score-entropy discrete diffusion | 독립 (marginal) | 불가 | 불필요 | AR 대비 열등 |
| LLaDA (Nie et al., 2025) | Large-scale masked diffusion LM | 독립 (marginal) | 불가 | 불필요 | AR 대비 열등 |
| Dream (Dream et al., 2025) | Machine-level discrete diffusion | 독립 (marginal) | 불가 | 불필요 | AR 대비 열등 |
| Block Diffusion (Arriola et al., 2025) | Block-level discrete diffusion | 블록 내 양방향 | 제한적 | 불필요 | AR 대비 열등 |
| **TiDAR** | AR + Diffusion 하이브리드 | **AR joint distribution** | **정확한 캐싱** | **불필요** | **AR에 근접** |

TiDAR는 Diffusion의 병렬 생성 속도를 활용하면서, AR의 joint distribution으로 품질을 보장하는 유일한 모델입니다.

### Speculative Decoding 계보

Speculative Decoding은 AR 모델 가속의 주류 접근법으로, 2023년 이후 다양한 변형이 제안되었습니다:

- **원조 Speculative Decoding** (Leviathan et al., 2023; Chen et al., 2023): 작은 draft 모델 + 큰 target 모델. 개념을 처음 제안했으며, target 모델의 분포를 정확히 재현하는 rejection sampling을 도입했습니다.
- **Self-Speculative Decoding** (Zhang et al., 2023): 동일 모델의 일부 레이어(early exit)를 draft로 사용. 별도 모델이 불필요하지만, draft 품질이 제한적입니다.
- **Medusa** (Cai et al., 2024): 추가 MLP head를 학습하여 여러 위치의 토큰을 병렬 예측. Tree-based verification으로 수락률을 높입니다.
- **EAGLE / EAGLE-2 / EAGLE-3** (Li et al., 2024): Feature-level draft 모델을 학습. Target 모델의 중간 표현을 활용하여 높은 수락률을 달성합니다. 현재 Speculative Decoding 분야의 SOTA입니다.
- **Lookahead Decoding** (Fu et al., 2024): N-gram pool을 구축하여 병렬 검증. Draft 모델이 불필요하지만, N-gram pool 구축에 메모리가 필요합니다.

TiDAR는 이 모든 접근법과 근본적으로 다릅니다:

| 차원 | 전통적 Speculative Decoding | TiDAR |
|------|-------------------------|-------|
| Draft 메커니즘 | 별도 모델 (또는 self의 일부) | 동일 모델의 Diffusion mode |
| Draft-Verify 관계 | 직렬 (Draft → Verify) | 병렬 (같은 forward pass) |
| 추가 파라미터 | 필요 (draft 모델/head) | 불필요 |
| 출력 분포 | Target과 동일 (lossless) | AR에 근접 (near-lossless) |
| T/NFE | ~3-4x | ~5-8x |

### Hybrid AR-Diffusion 모델

AR과 Diffusion을 결합하는 시도는 이전에도 있었지만, TiDAR는 접근 방식이 근본적으로 다릅니다:

- **Transfusion** (Zhou et al., 2024): 텍스트는 AR, 이미지는 continuous Diffusion으로 처리하는 **모달리티 분리** 방식. 같은 Transformer가 두 모달리티를 처리하지만, 텍스트 생성 자체는 순수 AR입니다.

- **Mercury** (Cai et al., 2024): TiDAR와 가장 유사한 선행 연구. Diffusion으로 draft하고 AR로 verify하지만, **두 개의 forward pass**가 필요합니다 (하나는 Diffusion draft용, 하나는 AR verify용). TiDAR는 이를 **하나의 forward pass**로 통합합니다.

- **d3** (Arriola et al., 2024): AR과 Diffusion의 상보적 강점을 활용하려는 시도이지만, 학습과 추론 프로세스가 복잡합니다.

- **TiDAR**: **하나의 forward pass**에서 AR과 Diffusion을 동시에 수행하는 **단일 모달리티 통합** 방식. Attention Mask만으로 두 모드를 전환하므로, 아키텍처적 복잡성이 최소화됩니다.

이 계보에서 TiDAR의 위치를 명확히 하면: Transfusion은 "서로 다른 모달리티에 서로 다른 생성 방식을 적용"하는 접근이고, Mercury는 "같은 모달리티에서 Diffusion draft + AR verify를 2-pass로 수행"하는 접근이며, TiDAR는 "같은 모달리티에서 Diffusion draft + AR verify를 **1-pass**로 통합"하는 접근입니다. 이 1-pass 통합이 가능한 핵심 메커니즘이 Block-Causal Attention Mask입니다.

### 텍스트 생성 효율화 연구의 큰 그림

더 넓은 관점에서, 텍스트 생성 효율화 연구는 크게 세 가지 방향으로 진행되어 왔습니다:

1. **모델 경량화**: Quantization, Pruning, Distillation 등으로 모델 자체를 가볍게 만드는 접근. 품질 손실이 불가피합니다.
2. **디코딩 가속**: Speculative Decoding, Parallel Decoding 등으로 디코딩 과정을 가속하는 접근. 모델 구조는 유지하면서 생성 속도를 높입니다.
3. **아키텍처 혁신**: AR 대신 Diffusion, Non-AR 등 새로운 생성 패러다임을 제시하는 접근. 근본적인 효율 개선이 가능하지만 품질 보장이 어렵습니다.

TiDAR는 (2)와 (3)의 **교차점**에 위치합니다. 아키텍처를 혁신하면서(AR+Diffusion 하이브리드), 동시에 디코딩 과정 자체도 가속합니다(self-speculative decoding). 이 두 가지를 하나의 프레임워크에서 통합한 것이 TiDAR의 독보적인 기여입니다.

## 의의 및 한계

### 이론적 의의

TiDAR의 가장 중요한 기여는 **AR과 Diffusion이 배타적 선택이 아님**을 증명한 것입니다.

기존에는 "AR이냐 Diffusion이냐"가 이분법적 설계 선택이었습니다. AR을 선택하면 높은 품질과 느린 속도를, Diffusion을 선택하면 빠른 속도와 낮은 품질을 감수해야 했습니다. TiDAR는 하나의 모델 안에서 **Attention Mask만으로 두 가지 모드를 전환**할 수 있음을 보여주었습니다.

이는 Transformer 아키텍처의 **유연성(flexibility)**에 대한 새로운 통찰을 제공합니다. 동일한 파라미터가 Attention Mask에 따라 causal(AR) 또는 bidirectional(Diffusion) 연산을 수행할 수 있으며, 이 두 모드가 서로를 보완합니다. 이 관찰은 향후 더 다양한 하이브리드 아키텍처의 가능성을 열어줍니다.

또한 Latency Scaling이라는 GPU 특성을 체계적으로 분석하고 이를 아키텍처 설계에 활용한 것은, **하드웨어-소프트웨어 공동 최적화(HW-SW co-design)**의 좋은 사례입니다. 알고리즘 설계가 하드웨어 특성을 깊이 이해하고 활용할 때 더 큰 효율을 달성할 수 있음을 보여줍니다.

### 실용적 의의

1. **별도 모델 불필요**: Speculative Decoding의 가장 큰 실용적 장벽인 "draft 모델 관리"를 완전히 제거합니다. 하나의 모델만 학습, 저장, 배포하면 됩니다. 이는 모델 서빙 인프라를 단순화하고, GPU 메모리 사용량을 줄입니다.

2. **추론 하이퍼파라미터 불필요**: Block Diffusion의 confidence threshold처럼 성능에 민감한 추론 하이퍼파라미터가 없습니다. 배포 후 튜닝 없이 바로 사용할 수 있습니다.

3. **정확한 KV Cache**: AR 모델과 동일한 exact KV caching을 지원하여, 긴 시퀀스에서도 메모리 효율적입니다. 이는 순수 Diffusion 모델이 매 step마다 전체 시퀀스를 재계산해야 하는 것과 대조적입니다.

4. **Continual Pretraining 가능**: 기존 AR 모델(Qwen2.5, Qwen3)에서 시작하여 추가 학습만으로 TiDAR를 얻을 수 있습니다. Scratch 학습이 필요 없으므로, 기존 AR 모델 생태계의 투자를 보존합니다.

5. **스케일링 가능성**: 1.5B, 4B, 8B에서 일관된 결과를 보여, 더 큰 모델에서도 유사한 가속이 기대됩니다.

### 한계

1. **Batch Size 제약**: 현재 실험은 batch size=1에 초점을 맞추고 있습니다. 실시간 챗봇이나 코드 어시스턴트에서는 이 설정이 적합하지만, 대규모 배치 서빙(throughput-oriented serving)에서는 상황이 다릅니다. Batch size가 커지면 GPU가 이미 compute-bound 상태가 되어 Free Token Slots가 줄어들고, TiDAR의 병렬 처리 이점이 감소할 수 있습니다.

2. **시퀀스 길이 확장**: 학습 시 마스크 토큰을 append하여 시퀀스 길이가 2배로 늘어나므로, 긴 컨텍스트 학습에 제약이 생깁니다. 예를 들어, 4,096 context length 모델에서는 실제 유효 시퀀스 길이가 약 2,048로 줄어듭니다. 128K context window를 목표로 하는 현대 LLM 트렌드와 이 제약의 상호작용은 추가 연구가 필요합니다.

3. **시스템 최적화 여지**: 현재 결과는 Native PyTorch + FlexAttention 구현 기반입니다. Custom CUDA kernel, Triton 최적화, 또는 TensorRT-LLM/vLLM 등의 최적화된 추론 엔진과의 통합이 이루어지면 추가적인 가속이 가능할 것으로 예상됩니다.

4. **품질 갭**: 8B 스케일에서 AR 모델 대비 약 2.78%p의 품질 차이가 여전히 존재합니다. 이는 Diffusion 초안의 수락률이 100%가 아니기 때문입니다. 수락되지 않은 위치에서는 AR이 교정하지만, 교정 이후 다음 draft는 새로운 Diffusion 초안에서 시작하므로 약간의 불연속이 발생합니다.

5. **Instruction-Tuned 모델**: 현재 실험은 Base 모델 위주입니다. Qwen3 8B Instruct에 대한 일부 결과가 있지만, TiDAR의 Dual-Mode 학습이 RLHF/DPO 같은 alignment 과정과 어떻게 상호작용하는지에 대한 깊은 분석은 향후 과제로 남아 있습니다.

6. **Multi-step Diffusion 미탐구**: 현재 TiDAR는 one-step denoising만 사용합니다. Multi-step denoising을 허용하면 Diffusion 초안의 품질이 높아져 수락률이 올라갈 수 있지만, latency도 증가합니다. 이 트레이드오프는 탐구되지 않았습니다.

### 향후 연구 방향

TiDAR가 열어놓은 연구 방향은 다양합니다:

**1. 대규모 스케일링**: 현재 최대 8B 모델에서 검증되었지만, 70B, 405B 등 더 큰 모델에서의 성능은 미지수입니다. 모델이 커지면 Diffusion 초안의 품질이 높아져 수락률이 올라갈 가능성이 있지만, GPU의 Latency Scaling 특성도 변할 수 있습니다. 특히 70B+ 모델에서는 이미 memory-bound에서 compute-bound로의 전환이 더 빨리 일어나므로, Free Token Slots가 줄어들 수 있습니다.

**2. Continuous Diffusion과의 결합**: TiDAR는 discrete diffusion (masked token → clean token)을 사용합니다. 이미지 생성에서 성공적인 continuous diffusion을 텍스트에 적용하면 (예: 임베딩 공간에서의 diffusion), 초안 품질이 더 높아질 수 있습니다. 최근의 Flow Matching 기반 접근법도 탐구할 가치가 있습니다.

**3. 적응적 블록 크기(Adaptive Block Size)**: 현재 TiDAR는 고정 블록 크기 $B$를 사용합니다. 그러나 텍스트의 예측 난이도는 위치마다 다릅니다. 쉬운 구간(일반적인 문장)에서는 큰 블록으로 많이 draft하고, 어려운 구간(수학 추론, 복잡한 코드)에서는 작은 블록으로 신중하게 생성하는 적응적 전략이 효율을 더 높일 수 있습니다.

**4. vLLM/TensorRT-LLM 통합**: 실용적 배포를 위해서는 vLLM, TensorRT-LLM 등의 고성능 추론 프레임워크와의 통합이 필수적입니다. 특히 continuous batching, paged attention 등의 최적화 기법과 TiDAR의 KV cache 관리 전략 간의 호환성을 확보해야 합니다.

**5. Multimodal 확장**: TiDAR의 Dual-Mode 아이디어는 텍스트에 국한될 필요가 없습니다. Transfusion이 텍스트(AR)와 이미지(Diffusion)를 결합했듯이, TiDAR의 Block-Causal Attention을 multimodal 생성에 적용하면 텍스트와 이미지를 더 효율적으로 동시 생성할 수 있을 것입니다.

**6. Reinforcement Learning과의 결합**: TiDAR로 학습된 모델에 RLHF/DPO를 적용할 때, AR loss만 fine-tuning할지 Diffusion loss도 함께 조정할지는 흥미로운 연구 문제입니다. Alignment 학습이 Dual-Mode backbone의 균형을 어떻게 변화시키는지 분석이 필요합니다.

## 결론

TiDAR는 "Diffusion으로 사고하고, Autoregression으로 말한다"는 직관적이면서도 강력한 아이디어를 제시합니다. GPU의 Latency Scaling 특성을 정밀하게 활용하여, 단일 forward pass에서 Diffusion의 병렬 초안 생성과 AR의 순차적 품질 보증을 동시에 수행합니다.

핵심 기술적 기여를 다시 정리하면:

- **Block-Causal Attention Mask**: 하나의 Transformer에서 causal(AR)과 bidirectional(Diffusion) 연산을 동시에 수행하는 구조화된 attention mask. Clean 영역의 causal 구조를 엄격히 유지하여 AR 품질을 보존하면서, mask 영역의 bidirectional 구조로 병렬 초안을 생성합니다.

- **Fully Parallelizable Self-Speculative Decoding**: Draft와 Verify를 단일 forward pass에서 병렬화하여, 별도 draft 모델 없이 speculative decoding의 가속을 달성. 전통적인 Draft-Verify 직렬 순환의 오버헤드를 완전히 제거합니다.

- **Full Mask 학습 전략**: One-step denoising에 최적화된 학습 전략으로, random masking 대비 3~5%p 품질 향상. 학습-추론 분포 일치와 밀집 학습 신호를 동시에 제공합니다.

- **Exact KV Caching**: AR 영역의 causal 구조를 유지하여, 순수 Diffusion 모델에서는 불가능한 정확한 KV cache 재사용을 실현. 긴 시퀀스에서의 효율성을 보장합니다.

다음 표는 TiDAR의 핵심 특성을 기존 접근법들과 최종 비교한 것입니다:

| 특성 | AR | Discrete Diffusion | Speculative Decoding | Block Diffusion | **TiDAR** |
|------|----|--------------------|---------------------|-----------------|-----------|
| 생성 품질 | 최고 | 낮음 | AR과 동일 | 중간 | **AR에 근접** |
| Throughput 가속 | 1x | 2-4x | 2-4x | 2-5x | **4.7-5.9x** |
| 별도 모델 필요 | 없음 | 없음 | **필요** | 없음 | **없음** |
| KV Cache | 정확 | 불가 | 정확 | 제한적 | **정확** |
| 추론 하이퍼파라미터 | 없음 | threshold 필요 | 없음 | threshold 필요 | **없음** |
| 토큰 간 의존성 | Joint | Marginal | Joint | 블록 내 | **Joint** |
| Continual PT | - | Scratch | 별도 학습 | Scratch | **가능** |

1.5B에서 4.71배, 8B에서 5.91배의 throughput 가속을 AR 수준의 품질과 함께 달성한 TiDAR는, **AR과 Diffusion의 이분법을 초월하는 새로운 패러다임**을 제시합니다. 텍스트 생성의 미래가 순수 AR도, 순수 Diffusion도 아닌, 두 가지의 장점을 정교하게 결합한 하이브리드 아키텍처에 있을 수 있음을 보여주는 중요한 이정표입니다.
