<!-- infographic-hero -->
![Speculative Decoding and Beyond: An In-Depth Survey of Techniques 핵심 요약](figures/infographic.svg)

*Figure: Speculative Decoding and Beyond: An In-Depth Survey of Techniques 한 장 요약 인포그래픽*

## 개요

"Speculative Decoding and Beyond: An In-Depth Survey of Techniques"(Yunhai Hu et al., 2025)는 대규모 언어 모델(LLM)의 추론 효율성을 획기적으로 개선하는 **Speculative Decoding(투기적 디코딩)** 기법들을 포괄적으로 정리한 서베이 논문이다. LLM이 산업 전반에 배포되면서 추론 지연(inference latency)은 가장 시급한 병목으로 떠올랐고, speculative decoding은 **출력 품질을 훼손하지 않으면서** 추론 속도를 2~3배 이상 향상시킬 수 있는 유일한 방법론 중 하나로 주목받고 있다.

이 서베이는 speculative decoding의 핵심 원리인 **draft-then-verify 패러다임**부터 시작하여, draft 생성 방법의 분류 체계(taxonomy), 검증 전략, tree-based 확장, 비동기/이종 스케줄링, 그리고 이미지 생성까지의 응용을 망라한다. 기존 서베이들이 특정 측면만 다룬 것과 달리, 이 논문은 **generation-refinement라는 통합 프레임워크** 아래 모든 기법을 체계적으로 분류하여 이 분야의 전체 지형도를 제시한다.

Speculative decoding은 2022~2023년 Leviathan et al.과 Chen et al.에 의해 독립적으로 제안된 이후, 2024~2025년에 걸쳐 폭발적으로 연구가 확장되었다. Meta의 Llama 3, Google의 Gemini, Anthropic의 Claude 등 주요 LLM 서비스에서 이미 실전 배포되고 있으며, 이 서베이는 그 기술적 기반을 이해하기 위한 최고의 출발점이다. 80개 이상의 논문을 분석하여 이 분야의 과거, 현재, 미래를 조망하고 있다.

## 배경 및 문제

### Auto-regressive Decoding의 병목

현대 LLM은 Transformer 디코더 아키텍처에 기반하며, 토큰을 하나씩 순차적으로 생성하는 **auto-regressive decoding**을 사용한다. 시퀀스 $\mathbf{x} = (x_1, x_2, \ldots, x_n)$을 생성할 때, 각 토큰 $x_t$의 확률은 이전 모든 토큰에 대해 조건부로 계산된다:

$$P(\mathbf{x}) = \prod_{t=1}^{n} P(x_t \mid x_1, x_2, \ldots, x_{t-1})$$

이 방식의 근본적 문제는 **메모리 바운드(memory-bound)** 연산이라는 점이다. 각 디코딩 스텝에서 모델의 전체 파라미터를 GPU 메모리에서 읽어야 하지만, 실제 연산량은 단 하나의 토큰에 대한 forward pass뿐이다. 즉, GPU의 연산 유닛(compute unit)은 대부분의 시간 동안 유휴 상태에 놓인다.

Transformer 디코더 블록은 Self-Attention(SA) 블록과 Feed-Forward Network(FFN) 블록으로 구성된다. Llama 같은 최신 모델에서는 이러한 블록이 수십 개 쌓여있으며, 각 디코딩 스텝에서 이 모든 블록의 파라미터를 순차적으로 읽어야 한다. 이 구조적 특성이 auto-regressive decoding의 메모리 바운드 병목을 만든다.

### Prefill vs. Decode Phase

LLM 추론은 크게 두 단계로 나뉜다:

**Prefill Phase**: 입력 프롬프트의 모든 토큰을 한 번에 처리하여 KV cache를 구성한다. 이 단계에서는 $n$개의 토큰을 동시에 처리하므로 **compute-bound**이며, GPU 활용도가 높다. 행렬-행렬 곱셈(GEMM)이 주요 연산이다.

**Decode Phase**: 토큰을 하나씩 생성한다. 이 단계에서는 행렬-벡터 곱셈(GEMV)이 주요 연산이며, **memory-bound**이다. GPU 연산 능력의 극히 일부만 활용된다.

Speculative decoding의 핵심 통찰은 이 두 단계의 비용 비대칭성을 활용하는 것이다. $\gamma$개의 draft 토큰을 검증하는 것은 prefill과 유사한 연산으로, decode를 $\gamma$번 반복하는 것보다 훨씬 효율적이다.

### Arithmetic Intensity 분석

이 비효율성을 정량적으로 이해하기 위해 **arithmetic intensity**(연산 강도)를 살펴보자. Arithmetic intensity는 메모리에서 읽은 바이트 당 수행한 부동소수점 연산 수(FLOPs/byte)로 정의된다:

$$\text{Arithmetic Intensity} = \frac{\text{FLOPs}}{\text{Memory Access (bytes)}}$$

단일 토큰 디코딩의 경우, 파라미터가 $P$개인 모델에서:

- **FLOPs**: 약 $2P$ (각 파라미터에 대해 곱셈과 덧셈 1회)
- **Memory Access**: 약 $2P$ bytes (FP16 기준, 파라미터당 2 bytes)
- **Arithmetic Intensity**: $\approx 1$ FLOP/byte

반면 최신 GPU(예: NVIDIA A100)의 **최적 arithmetic intensity**는 약 312 FLOP/byte (312 TFLOPS / 1 TB/s)이다. 즉, 단일 토큰 디코딩은 GPU 연산 능력의 **0.3%도 활용하지 못하는** 극단적인 메모리 바운드 상황이다.

$\gamma$개의 토큰을 동시에 처리하면 arithmetic intensity가 $\gamma$배로 증가한다:

$$\text{AI}_{\text{batch}} = \gamma \cdot \text{AI}_{\text{single}} = \gamma$$

따라서 $\gamma \geq 312$이면 compute-bound 영역에 진입한다. Speculative decoding은 이 원리를 활용하여, draft 토큰 $\gamma$개를 한 번에 검증함으로써 GPU를 더 효율적으로 활용한다. 물론 실제로 $\gamma = 312$까지 갈 필요는 없으며, $\gamma = 4 \sim 8$ 정도만 되어도 유의미한 가속이 가능하다.

### 기존 추론 최적화 기법과의 비교

Speculative decoding이 등장하기 전에도 다양한 추론 최적화 기법이 연구되었다. 이들과의 차이를 이해하면 speculative decoding의 위치가 명확해진다:

| 기법 | 접근 방식 | 품질 손실 | 가속 배율 | 결합 가능 |
|-----|---------|:-------:|:-------:|:-------:|
| **Quantization** | 파라미터 정밀도 감소 (FP16→INT8/INT4) | 있음 (보통 미미) | 1.5~2x | O |
| **Pruning** | 불필요한 가중치 제거 | 있음 | 1.5~3x | O |
| **Knowledge Distillation** | 큰 모델의 지식을 작은 모델로 전달 | 있음 | N/A | O |
| **Flash Attention** | Attention 연산의 IO 최적화 | 없음 | 1.5~2x (memory) | O |
| **KV Cache Optimization** | Cache 메모리 효율화 | 최소~없음 | 메모리 절약 | O |
| **Speculative Decoding** | Draft-then-verify | **없음** | 2~4x | O |

Speculative decoding의 가장 독보적인 특성은 **출력 품질을 전혀 희생하지 않는(lossless)** 가속이라는 점이다. 양자화나 pruning은 근사(approximation)에 의존하므로 어느 정도의 품질 저하를 수반하지만, speculative decoding은 수학적으로 원래 모델과 **정확히 동일한 출력 분포**를 보장한다.

또한 speculative decoding은 위 기법들과 **직교적(orthogonal)**이므로, 모두 결합하여 사용할 수 있다. 예를 들어, INT4 양자화된 draft 모델 + Flash Attention을 적용한 target 모델 위에서 speculative decoding을 실행하면, 각 기법의 가속 효과가 곱해진다.

### Speculative Decoding의 핵심 통찰

Speculative decoding은 메모리 바운드 문제를 **비대칭적 비용 구조**를 활용하여 해결한다. 핵심 관찰은 다음 두 가지이다:

1. **검증이 생성보다 저렴하다**: Target 모델이 $n$개의 토큰을 하나씩 생성하려면 $n$번의 forward pass가 필요하지만, $n$개의 draft 토큰을 **한 번에 검증**하는 것은 단 1번의 forward pass로 가능하다 (prefill과 동일한 연산). 이는 Transformer의 self-attention이 causal mask를 사용하므로, 입력 시퀀스의 각 위치에서의 출력이 해당 위치까지의 토큰에만 의존하기 때문이다.

2. **작은 모델의 예측이 큰 모델과 상당 부분 일치한다**: 많은 토큰(특히 관사, 전치사, 일반적인 단어)에 대해 작은 모델과 큰 모델의 예측이 동일하다. 이런 "쉬운" 토큰에 대해 굳이 거대 모델을 실행할 필요가 없다. 실제로 연구들에 따르면 일반적인 텍스트에서 토큰별 수락률은 70~90%에 달한다.

이 두 관찰을 결합하면, **작은 draft 모델로 빠르게 여러 토큰을 생성**하고, **큰 target 모델로 한 번에 검증**하는 전략이 자연스럽게 도출된다. 이것이 speculative decoding의 **draft-then-verify 패러다임**이다.

이 아이디어의 기원은 CPU 아키텍처의 **speculative execution(투기적 실행)**과 유사하다. CPU가 분기 예측(branch prediction)을 통해 다음 실행할 명령어를 미리 추측하고, 예측이 맞으면 그대로 진행하고 틀리면 롤백하는 것처럼, speculative decoding도 작은 모델이 다음 토큰들을 미리 추측하고, 큰 모델이 이를 검증하는 구조이다.

## 핵심 아이디어

### Draft-Then-Verify 패러다임

Speculative decoding의 워크플로우는 두 단계의 반복으로 구성된다:

**1단계 - Draft Generation**: 작고 빠른 **draft 모델** $M_q$가 $\gamma$개의 토큰을 auto-regressive하게 생성한다. Draft 모델은 target 모델보다 훨씬 작으므로 이 과정은 매우 빠르다. 예를 들어, target이 Llama 2-70B이면 draft로 Llama 2-7B를 사용할 수 있다. 파라미터 수가 10배 차이나므로 forward pass 속도도 대략 10배 차이가 난다.

**2단계 - Verification**: 큰 **target 모델** $M_p$가 draft 토큰들을 **병렬로 한 번에** 검증한다. 이때 target 모델은 모든 draft 위치에 대한 확률 분포를 동시에 계산한다. 이는 기술적으로 prefill 연산과 동일하며, draft 토큰 시퀀스를 입력으로 받아 각 위치에서의 next-token 확률 분포를 병렬로 출력한다.

![Speculative Decoding 워크플로우](figures/fig_2.png)
*Speculative decoding의 전체 워크플로우. (a) Draft 모델이 $\gamma$개의 토큰을 auto-regressive하게 생성한다. (b) Target 모델이 한 번의 forward pass로 모든 draft 토큰을 동시에 검증하여, 모두 수락하면 (c) 다음 라운드로 진행한다. (d) 중간에서 거부가 발생하면 (e) 거부된 위치의 보정된 토큰부터 다시 draft를 시작한다. 노란 박스는 draft 모델 생성 토큰, 파란 박스는 target 모델 생성 토큰이다.*

### Rejection Sampling 기반 수락-거부 판정

구체적으로, 각 draft 토큰 $\tilde{x}_i$에 대해 다음과 같은 **수락-거부 판정**이 이루어진다. 균일 분포에서 난수 $r \sim \text{Uniform}(0, 1)$을 샘플링하고:

$$\tilde{x}_i \text{가 수락되려면: } r < \min\left(1, \frac{p(\tilde{x}_i \mid x_{<i})}{q(\tilde{x}_i \mid x_{<i})}\right)$$

여기서 $p(\cdot)$는 target 모델의 확률 분포, $q(\cdot)$는 draft 모델의 확률 분포이다. 이 수락 기준의 핵심 성질은 다음과 같다:

- **Draft와 target의 예측이 일치하면** ($q(\tilde{x}_i) \leq p(\tilde{x}_i)$): 비율 $p/q \geq 1$이므로 확률 1로 항상 수락된다. 즉, target 모델이 draft보다 더 높은 확률을 부여한 토큰은 절대로 거부되지 않는다.
- **Draft가 과대 예측하면** ($q(\tilde{x}_i) > p(\tilde{x}_i)$): 비율 $p/q < 1$이므로 해당 비율의 확률로 수락되고, 나머지 확률로 거부된다. Draft 모델이 target에 비해 과도하게 높은 확률을 부여한 토큰일수록 거부될 가능성이 높다.

검증은 **순차적으로** 이루어진다. 즉, 첫 번째로 거부된 위치 이후의 모든 토큰은 자동으로 폐기된다. 이는 auto-regressive 모델에서 각 토큰의 확률이 이전 토큰들에 의존하기 때문이다. 위치 $i$의 토큰이 거부되면, 위치 $i+1$ 이후의 확률 분포 자체가 무효화된다.

거부된 토큰이 발생하면, 해당 위치에서 **보정된 분포(residual distribution)**에서 새 토큰을 샘플링한다:

$$p'(x) = \text{norm}\left(\max\left(0, p(x) - q(x)\right)\right) = \frac{\max(0, p(x) - q(x))}{\sum_{x'} \max(0, p(x') - q(x'))}$$

이 보정 분포는 target이 draft보다 더 높은 확률을 부여하는 토큰들에 집중된다. 직관적으로, draft 모델이 "놓친" 토큰들 중에서 샘플링하는 것이다.

### 출력 분포 보존 정리

Speculative decoding의 가장 중요한 이론적 보장은 **출력 분포가 target 모델과 정확히 동일하다**는 것이다. 즉, speculative decoding은 근사(approximation)가 아닌 **정확한(exact)** 가속 기법이다.

> **정리 (Lossless Acceleration)**: 위의 수락-거부 메커니즘을 따르면, 최종 출력의 각 토큰은 target 모델의 분포 $p(x_t \mid x_{<t})$에서 정확히 샘플링된 것과 동일한 분포를 따른다.

**증명**: 임의의 토큰 $x$가 최종 출력으로 선택될 확률을 계산하자. 이는 (1) draft 토큰 $x$가 생성되고 수락되는 경우와 (2) draft 토큰이 거부되고 보정 분포에서 $x$가 선택되는 경우의 합이다.

전체 거부 확률(어떤 토큰이든 거부될 확률)을 먼저 계산하면:

$$\beta = 1 - \sum_{x'} q(x') \cdot \min\left(1, \frac{p(x')}{q(x')}\right) = 1 - \sum_{x'} \min(q(x'), p(x'))$$

그러면 토큰 $x$가 최종 출력이 될 확률은:

$$P(\text{output} = x) = q(x) \cdot \min\left(1, \frac{p(x)}{q(x)}\right) + \beta \cdot p'(x)$$

$$= \min(q(x), p(x)) + \beta \cdot \frac{\max(0, p(x) - q(x))}{\sum_{x'}\max(0, p(x') - q(x'))}$$

핵심 관찰: $\sum_{x'} \max(0, p(x') - q(x')) = \sum_{x'} p(x') - \sum_{x'} \min(p(x'), q(x')) = 1 - \sum_{x'} \min(p(x'), q(x')) = \beta$

따라서:

$$P(\text{output} = x) = \min(q(x), p(x)) + \max(0, p(x) - q(x)) = p(x)$$

이 증명은 rejection sampling의 원리에 기반한다. Draft 모델이 아무리 부정확하더라도 출력 분포는 항상 보존되며, 단지 속도(수락률)에만 영향을 미친다. 이것이 speculative decoding의 가장 강력한 이론적 보장이다.

### 수락률과 Token Entropy의 관계

수락률은 토큰의 **예측 난이도**와 밀접한 관련이 있다. 정보 이론적으로, target 분포의 엔트로피 $H(p)$가 낮은 위치(모델이 확신하는 위치)에서는 draft 모델도 올바른 토큰을 예측하기 쉬우므로 수락률이 높다. 반면, $H(p)$가 높은 위치(모델이 불확실한 위치)에서는 draft 모델의 예측이 틀릴 가능성이 커져 수락률이 낮아진다.

구체적으로, 수락률의 상한과 하한을 분석하면:

$$\alpha = \sum_x \min(p(x), q(x)) = 1 - \frac{1}{2}\|p - q\|_1$$

여기서 $\|p - q\|_1$은 두 분포 사이의 total variation distance이다. 따라서 **draft와 target의 분포가 가까울수록 수락률이 높다**. 이 관계는 draft 모델을 KL divergence로 학습하는 DistillSpec의 이론적 근거이기도 하다.

실전에서의 토큰별 수락률 패턴:
- **관사/전치사/접속사**: 95%+ (거의 항상 수락)
- **일반 명사/동사**: 70~85% (대부분 수락)
- **전문 용어/고유 명사**: 40~60% (상황에 따라)
- **창의적 표현/비유**: 20~40% (높은 엔트로피)

이 패턴은 speculative decoding이 특히 **정형화된 텍스트**(코드, 기술 문서, 법률 문서)에서 효과적인 이유를 설명한다.

### Greedy Decoding에서의 특수 사례

Temperature가 0인 greedy decoding의 경우, 수락-거부 판정이 단순해진다. Target 모델의 argmax 토큰과 draft 토큰이 일치하면 수락, 불일치하면 거부하고 target의 argmax 토큰을 사용한다. 이 경우 출력은 결정론적(deterministic)이므로 분포 보존이 아닌 **출력 동일성**이 보장된다.

실전에서 많은 서빙 시스템이 temperature 0 또는 매우 낮은 temperature를 사용하므로, 이 특수 사례는 실용적으로 매우 중요하다. Greedy decoding에서의 speculative decoding은 구현도 더 단순하고, 수락률도 일반적으로 더 높다.

### 속도 향상 분석

Speculative decoding의 기대 속도 향상은 다음 요소에 의해 결정된다:

- **수락률 $\alpha$**: Draft 토큰이 수락될 평균 확률
- **Draft 길이 $\gamma$**: 각 라운드에서 생성하는 draft 토큰 수
- **비용 비율 $c$**: Draft 모델의 forward pass 시간 / Target 모델의 forward pass 시간

한 라운드에서 수락되는 토큰의 기대 수를 분석하자. $\gamma$개의 draft 중 처음 $k$개가 연속으로 수락되려면 확률 $\alpha^k$이 필요하고, $k+1$번째에서 거부되면 보정 분포에서 1개 토큰이 추가된다. 따라서:

$$\mathbb{E}[\text{accepted tokens}] = \sum_{k=0}^{\gamma-1} \alpha^k \cdot (1-\alpha) \cdot (k+1) + \alpha^{\gamma} \cdot (\gamma + 1)$$

이를 정리하면:

$$\mathbb{E}[\text{accepted tokens}] = \frac{1 - \alpha^{\gamma+1}}{1 - \alpha}$$

한 라운드의 wall-clock 시간은 $\gamma \cdot c \cdot T + T$ (draft 생성 $\gamma$회 + 검증 1회)이므로, 기대 속도 향상(speedup)은:

$$S = \frac{(1 - \alpha^{\gamma+1}) / (1 - \alpha)}{\gamma \cdot c + 1}$$

이 공식에서 몇 가지 중요한 통찰을 얻을 수 있다:

- **완벽한 draft** ($\alpha = 1$): $S = (\gamma + 1) / (\gamma c + 1)$이며, $c \to 0$이면 $S \to \gamma + 1$. 즉, draft가 무비용이면 $\gamma+1$배 가속이 이론적 상한
- **완전히 틀린 draft** ($\alpha = 0$): $S = 1 / (\gamma c + 1) < 1$, 즉 **오히려 느려진다**. Draft 생성에 쓴 시간이 순수 낭비가 되기 때문
- **최적 $\gamma$**가 존재하며, 이는 $\alpha$와 $c$에 의존한다. $\alpha$가 높을수록 최적 $\gamma$도 커진다

구체적인 예시를 통해 감각을 잡아보자:

| $\alpha$ | $c$ | $\gamma$ | 기대 수락 토큰 | 라운드 비용 | Speedup |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 0.9 | 0.05 | 5 | 4.69 | 1.25T | 3.75x |
| 0.8 | 0.05 | 5 | 3.69 | 1.25T | 2.95x |
| 0.7 | 0.05 | 5 | 2.95 | 1.25T | 2.36x |
| 0.8 | 0.1 | 5 | 3.69 | 1.5T | 2.46x |
| 0.8 | 0.1 | 3 | 2.95 | 1.3T | 2.27x |

실전에서 일반적으로 $\alpha \approx 0.7\text{--}0.85$, $c \approx 0.05\text{--}0.15$ 정도이며, 이 경우 2~3배의 속도 향상을 기대할 수 있다. EAGLE 같은 고급 기법은 $\alpha \approx 0.85\text{--}0.9$를 달성하여 3~4배 가속을 보고한다.

### 최적 Draft 길이

주어진 $\alpha$와 $c$에서 속도 향상을 최대화하는 최적 $\gamma^*$는 $\partial S / \partial \gamma = 0$을 풀어 구할 수 있다. 닫힌 형태의 해는 복잡하지만, 근사적으로:

$$\gamma^* \approx \frac{1}{c} \cdot \frac{-\ln \alpha}{\alpha} \quad (\alpha \text{가 1에 가까울 때})$$

예를 들어 $\alpha = 0.8$, $c = 0.1$이면 $\gamma^* \approx 2.8$, 즉 3개의 draft 토큰이 최적이다. $\alpha = 0.9$, $c = 0.05$이면 $\gamma^* \approx 2.3$이지만, 실제로는 tree-based 방법을 사용하여 더 많은 후보를 탐색하는 것이 유리하다.

## 방법론: Generation-Refinement 프레임워크

이 서베이의 핵심 기여는 다양한 speculative decoding 기법들을 **Generation-Refinement**라는 통합 프레임워크로 분류한 것이다. 모든 기법은 (1) **draft 시퀀스를 생성**하는 단계와 (2) 생성된 시퀀스를 **검증/정제**하는 단계로 구성된다.

![Generation-Refinement 프레임워크 분류 체계](figures/fig_3.png)
*Generation-Refinement 프레임워크의 분류 체계. 상단의 Sequence Generation은 draft 토큰 생성 방법을 보여주며, 크게 다섯 가지 범주로 나뉜다: Predefined Fill Tokens, Retrieval, N-gram, Auto-regressive Decoding(Draft Model 사용), Multi-token Generation. 하단의 Sequence Refinement는 검증 전략으로, Single-step Verification(Target Model 1회 실행)과 Iterative Decoding(수렴까지 반복)으로 나뉜다. 색상으로 input tokens, draft tokens, rejected tokens, accepted tokens가 구분된다.*

### 1. Sequence Generation: Draft 토큰 생성 방법

Draft 시퀀스를 생성하는 방법은 크게 다섯 가지로 분류된다. 각 방법은 **draft 생성 비용**과 **수락률** 사이의 서로 다른 트레이드오프를 가진다.

#### 1.1 Independent Drafting (모델 비의존적 방법)

신경망 모델 없이 draft 시퀀스를 생성하는 가장 경량의 방법들이다.

**Predefined Fill Tokens**: 가장 단순한 방법으로, 미리 정의된 토큰(예: 빈 토큰, 마스크 토큰, 또는 이전에 가장 빈번하게 등장한 토큰)으로 draft 시퀀스를 채운다. 토큰 생성에 전혀 비용이 들지 않으므로 $c = 0$이지만, 수락률이 매우 낮아 실용성이 제한적이다. 다만 이 방법은 speculative decoding의 하한(lower bound) 성능을 분석하는 데 유용한 기준점을 제공한다.

**Retrieval-based Drafting**: 기존 텍스트 코퍼스에서 현재 컨텍스트와 유사한 텍스트를 검색하여 draft로 사용한다. **Suffix matching** 기반의 REST(He et al., 2023)가 대표적이며, 현재까지 생성된 토큰 시퀀스의 접미사를 데이터스토어에서 검색하여 이어지는 텍스트를 draft로 활용한다.

REST의 동작을 구체적으로 설명하면:

1. 현재까지 생성된 시퀀스의 마지막 $n$개 토큰(suffix)을 추출
2. 사전 구축된 suffix array에서 이 suffix와 매칭되는 위치를 검색
3. 매칭된 위치 이후의 토큰들을 draft로 사용
4. 여러 매칭이 있을 경우 빈도 기반으로 후보를 선정

이 방법의 장단점:
- **장점**: 신경망 모델 실행 없이 매우 빠르게 draft 생성 가능, GPU 사용 불필요
- **단점**: 적절한 데이터스토어가 필요하며, 코드 완성 같은 반복적 도메인에서만 높은 수락률 달성
- **변형**: LLMA(Yang et al., 2023)는 입력 프롬프트 자체에서 draft를 추출하는 copy-and-verify 전략을 사용. 요약이나 번역 같이 입력과 출력이 상당 부분 겹치는 작업에서 효과적

**N-gram based Drafting**: 이전 컨텍스트에서 N-gram 통계를 활용하여 draft를 생성한다. 현재까지 생성된 텍스트에서 N-gram 빈도를 계산하고, 가장 가능성 높은 이어지는 토큰들을 draft로 사용한다.

- **Prompt Lookup Decoding**(Saxena, 2023): 프롬프트 내에서 N-gram 매칭을 수행하여 draft를 생성. 별도의 모델이나 데이터스토어 없이 동작하여 구현이 매우 간단. Hugging Face Transformers 라이브러리에 내장되어 있을 정도로 실용적
- **장점**: 추가 모델 불필요, 메모리 오버헤드 거의 없음, 구현이 10줄 내외로 단순
- **단점**: 프롬프트가 짧거나 생성 내용과 관련 없으면 효과 없음. 일반적인 대화에서는 수락률이 매우 낮음
- **적합한 사용 사례**: 긴 문서의 요약, 코드 내 반복 패턴, 템플릿 기반 생성

#### 1.2 Auto-regressive Draft Model

가장 널리 사용되는 방법으로, 작은 신경망 모델이 auto-regressive하게 draft 토큰을 생성한다. 이 카테고리의 핵심은 **draft 모델의 설계와 학습 방법**이다.

**독립 모델 (Independent Draft Model)**: Target 모델과 독립적으로 설계된 작은 모델을 사용한다.

- **SpecDec**(Leviathan et al., 2023) / **SpecInfer**(Chen et al., 2023): Speculative decoding을 최초로 제안한 논문들로, target 모델과 동일한 아키텍처의 축소 버전을 draft 모델로 사용. 예를 들어 Llama 70B가 target이면 Llama 7B를 draft로 사용. 두 논문은 독립적으로 거의 같은 시기에 발표되어, 이 분야의 기초를 함께 놓았다.
- **BiLD**(Kim et al., 2023): Big-Little Decoder의 약자로, 큰 모델과 작은 모델 사이의 **fallback** 메커니즘을 제안. 작은 모델의 confidence가 높을 때는 작은 모델의 출력을 사용하고, confidence가 낮을 때만 큰 모델로 전환. 엄밀한 분포 보존 대신 실용적 품질을 추구
- **Online Speculative Decoding**(Liu et al., 2024): Draft 모델을 target 모델의 출력에 대해 온라인으로 지속 학습하여 수락률을 점진적으로 향상. 서비스 운영 중에 도메인 적응이 자동으로 이루어지는 것이 핵심 장점

**Self-Drafting (Target 모델 자체 활용)**: 별도의 draft 모델 없이 target 모델의 일부만 사용하여 draft를 생성한다. **추가 메모리 비용이 없다**는 것이 가장 큰 장점이다.

- **Draft & Verify**(Zhang et al., 2023): Target 모델의 초기 레이어만 사용하여 draft 생성. 예를 들어 32-layer 모델에서 처음 8개 레이어만 실행하여 draft를 생성하고, 전체 32개 레이어로 검증. Early exit 전략으로, 전체 모델을 통과하지 않고 중간 레이어에서 출력을 예측
- **LayerSkip**(Elhoushi et al., 2024): 학습 시 layer dropout을 적용하여 초기 레이어만으로도 reasonable한 예측이 가능하도록 모델을 훈련. 학습 시 각 레이어의 dropout 확률을 점진적으로 증가시켜, 초기 레이어가 더 많은 정보를 담도록 유도. 추론 시 early exit으로 draft 생성
- **Medusa**(Cai et al., 2024): Target 모델의 마지막 hidden state 위에 추가 MLP 헤드들을 부착하여 여러 미래 토큰을 동시에 예측. 이 헤드들은 target 모델을 freeze한 상태에서 학습. Self-drafting이면서도 multi-token generation의 특성을 동시에 가진다
- **Kangaroo**(Liu et al., 2024): Self-drafting의 변형으로, target 모델의 중간 레이어 출력을 경량 adapter network로 변환하여 draft를 생성. LayerSkip보다 유연한 구조

**Knowledge Distillation 기반**: Target 모델의 지식을 증류하여 draft 모델을 학습한다.

- **DistillSpec**(Zhou et al., 2024): Target 모델의 출력 분포를 사용하여 draft 모델을 KL divergence 최소화로 학습. 표준 knowledge distillation이지만 speculative decoding의 수락률 최적화에 특화. 단순히 정답 토큰을 맞추는 것이 아니라, target의 **전체 확률 분포**를 모방하도록 학습하여 수락률을 극대화
- **MiniCache**(Liu et al., 2024): KV cache를 압축하여 draft 모델의 효율을 높이는 방법. Draft 모델이 target 모델의 KV cache를 재활용하여 메모리 사용량을 줄인다

#### 1.3 Multi-token Generation (병렬 Draft 생성)

Auto-regressive drafting은 draft 모델도 순차적으로 토큰을 생성해야 하므로, draft 생성 자체가 병목이 될 수 있다. 이를 해결하기 위해 **여러 토큰을 동시에 생성**하는 방법들이 연구되었다.

**Medusa** (Cai et al., 2024): $K$개의 추가 prediction head를 사용하여 $K$개의 미래 토큰을 **동시에** 예측한다. Head $i$는 위치 $t+i$의 토큰을 예측하며, 각 헤드는 독립적으로 작동한다.

$$\hat{x}_{t+i} = \text{Head}_i(h_t), \quad i = 1, 2, \ldots, K$$

여기서 $h_t$는 현재 위치 $t$의 hidden state이다. 각 헤드가 top-$s$ 후보를 생성하면, 이들의 조합으로 **토큰 트리(token tree)**를 구성하여 검증한다. 단 하나의 forward pass 추가 비용($K$개 MLP 헤드 실행)으로 $K$개의 미래 위치에 대한 후보를 얻을 수 있어 매우 효율적이다.

**EAGLE** (Li et al., 2024): Target 모델의 두 번째 마지막 레이어의 feature를 입력으로 받는 경량 auto-regressive 모델을 학습한다. 일반적인 토큰 임베딩 대신 target 모델의 **feature 수준**에서 auto-regressive 생성을 수행하므로, 토큰 수준보다 정보가 풍부하여 높은 수락률을 달성한다.

EAGLE의 핵심 관찰: 토큰 수준의 auto-regressive 모델링은 $\arg\max$ 연산으로 인한 정보 손실이 발생한다. 예를 들어, target 모델이 "the"에 0.4, "a"에 0.3의 확률을 부여했지만 "the"가 선택된 경우, "a"에 대한 정보는 소실된다. 반면 feature 수준에서는 이 불확실성 정보가 보존되어 있으므로 더 정확한 다음 토큰 예측이 가능하다.

EAGLE-2에서는 동적으로 draft 길이와 트리 구조를 조절하는 메커니즘을 추가하여, 수락률에 따라 자원 할당을 최적화했다. 이는 뒤에서 다룰 tree-based speculative decoding과 밀접하게 연관된다.

**Lookahead Decoding** (Fu et al., 2024): Jacobi iteration에 기반한 방법으로, 여러 미래 위치의 토큰을 동시에 예측하고 반복적으로 정제한다. 별도의 draft 모델 학습 없이 target 모델만으로 동작한다는 장점이 있다. 수학적 기반은 비선형 연립방정식의 Jacobi 반복법에서 왔다.

**Parallel Decoding** (Santilli et al., 2023): 학습 시 masked language modeling과 유사한 목적 함수를 추가하여, 모델이 여러 위치의 토큰을 동시에 예측할 수 있도록 한다. 추론 시 한 번의 forward pass로 여러 토큰을 생성한다.

#### 1.4 Draft Model 설계 시 고려사항

Draft 모델 설계에서 가장 중요한 트레이드오프는 **속도 vs. 수락률**이다. 더 큰/정교한 draft 모델은 높은 수락률을 달성하지만 draft 생성 비용(c)도 증가한다:

| 접근 방식 | Draft 생성 속도 | 수락률 | 추가 메모리 | 학습 필요 | 대표 기법 |
|-----------|:---:|:---:|:---:|:---:|:---:|
| N-gram / Retrieval | 매우 빠름 | 낮음~중간 | 최소 | 불필요 | REST, Prompt Lookup |
| 독립 소형 모델 | 빠름 | 중간 | 중간 | 불필요 (기존 모델) | SpecDec |
| Self-draft (Early exit) | 빠름 | 중간 | 없음 | 일부 필요 | LayerSkip, Draft&Verify |
| Medusa (Multi-head) | 매우 빠름 | 중간~높음 | 최소 | 필요 | Medusa, Medusa-2 |
| EAGLE (Feature-level) | 빠름 | 높음 | 소량 | 필요 | EAGLE, EAGLE-2 |
| Knowledge Distillation | 빠름 | 높음 | 중간 | 필요 | DistillSpec |

실전에서의 선택은 다음 기준을 고려해야 한다:

- **GPU 메모리 여유가 있는가?** 여유가 있으면 독립 소형 모델, 없으면 self-drafting
- **추가 학습이 가능한가?** 가능하면 EAGLE/Medusa, 불가능하면 독립 모델/N-gram
- **도메인이 특화되어 있는가?** 코드나 반복적 텍스트면 retrieval/N-gram이 효과적
- **Target 모델 업데이트가 빈번한가?** 빈번하면 학습 불필요한 방법이 유리

### 2. Sequence Refinement: 검증 전략

생성된 draft 시퀀스를 검증하고 정제하는 방법은 크게 두 가지로 나뉜다.

#### 2.1 Single-step Verification (단일 패스 검증)

가장 기본적인 검증 전략으로, target 모델이 **한 번의 forward pass**로 모든 draft 토큰을 동시에 검증한다.

**Token-level Verification**: 각 draft 토큰을 순차적으로 수락/거부한다. 앞서 설명한 rejection sampling 기반의 수락 기준이 이에 해당한다.

$$\text{Accept } \tilde{x}_i \text{ if } r < \min\left(1, \frac{p(\tilde{x}_i \mid x_{<i})}{q(\tilde{x}_i \mid x_{<i})}\right), \quad r \sim \text{Uniform}(0, 1)$$

첫 번째로 거부된 위치 이후의 모든 토큰은 자동으로 폐기되며, 거부 위치에서는 보정 분포에서 새 토큰을 샘플링한다. 이 방식은 **분포 보존이 보장**되는 유일한 검증 전략이다.

**Sequence-level Verification**: 드래프트 시퀀스 전체를 하나의 단위로 수락/거부한다. 개별 토큰이 아닌 시퀀스 전체의 품질을 평가하므로, 더 유연한 검증이 가능하지만 수학적 보장이 약해질 수 있다. 이 방식은 주로 lossy speculative decoding에서 사용된다.

**Typical Acceptance**: Cai et al.(2024)이 Medusa에서 제안한 방식으로, 엄격한 rejection sampling 대신 **typical set**에 기반한 완화된 수락 기준을 사용한다. 정보 이론의 typical set 개념을 차용하여, target 모델의 분포에서 "전형적인" 토큰이면 수락하는 전략이다.

구체적으로, 엔트로피 기반 필터링을 적용한다:

$$\text{Accept } \tilde{x}_i \text{ if } -\log p(\tilde{x}_i) \in [H(p) - \epsilon, H(p) + \epsilon]$$

여기서 $H(p)$는 target 분포의 엔트로피이고 $\epsilon$은 허용 범위이다. 이 방식은 정확한 분포 보존을 포기하는 대신 더 높은 수락률을 달성한다. 실험적으로, 품질 저하가 미미하면서도 수락률이 10~20% 향상되는 것으로 보고되었다.

**SpecTr** (Sun et al., 2024): Optimal transport 이론에 기반한 검증 전략으로, 여러 draft 후보 중 최적의 조합을 선택한다. Token-level verification의 greedy한 수락/거부 대신, 전체 draft 집합에 대한 글로벌 최적화를 수행한다.

#### 2.2 Iterative Decoding (반복적 정제)

Draft 시퀀스를 **여러 번의 반복**을 통해 점진적으로 정제하는 방법이다.

**Blockwise Parallel Decoding** (Stern et al., 2018): Speculative decoding의 선구적 연구 중 하나로, 여러 위치의 토큰을 동시에 예측하고, target 모델로 검증한 후, 불일치하는 위치의 토큰을 수정하여 다시 검증하는 과정을 반복한다. 수렴이 보장되며, 수렴 시 greedy decoding과 동일한 결과를 얻는다.

**SPEED** (Hooper et al., 2024): Speculative Pipelined Execution for Efficient Decoding의 약자로, 검증과 draft 생성을 파이프라인으로 연결하여 반복적으로 실행한다. 이전 라운드의 검증 결과를 즉시 다음 라운드의 draft 생성에 반영하는 스트리밍 방식이다.

**Consistency-based Decoding**: 여러 번의 반복을 통해 시퀀스가 "자기 일관성(self-consistency)"을 달성할 때까지 정제한다. 각 반복에서 target 모델이 시퀀스를 업데이트하고, 이전 반복과 동일한 결과가 나올 때(고정점에 도달할 때) 수렴으로 판정한다.

반복적 정제의 핵심 장점은 **한 번에 긴 시퀀스를 생성**할 수 있다는 것이다. 단일 패스 검증에서는 첫 거부 위치 이후 모든 토큰이 폐기되지만, 반복적 정제에서는 거부된 토큰만 수정하고 나머지는 유지할 수 있다. 다만, 여러 번의 target 모델 forward pass가 필요하므로 라운드당 비용이 높다는 단점이 있다.

## Tree-based Speculative Decoding

### 선형 Draft의 한계

기본적인 speculative decoding은 **단일 시퀀스(linear draft)**를 생성하고 검증한다. 이 접근의 근본적 한계는 첫 번째 거부 이후 모든 토큰이 무효화된다는 점이다. Draft 길이가 $\gamma$이고 토큰별 수락률이 $\alpha$일 때, $k$번째 토큰까지 모두 수락될 확률은 $\alpha^k$이므로, $\gamma$가 클수록 전체 시퀀스가 수락될 확률은 기하급수적으로 감소한다.

예를 들어, $\alpha = 0.8$이고 $\gamma = 5$이면:
- 5개 토큰 모두 수락: $0.8^5 \approx 0.328$ (33%)
- 4개 이상 수락: $0.8^4 \cdot (1 + 0.8) \approx 0.737$ (74%)
- 기대 수락 토큰 수: $\frac{1 - 0.8^6}{1 - 0.8} \approx 3.69$개

기대 수락 토큰은 약 3.7개이지만, 이 중 상당 부분의 연산이 "낭비"된다. 위치 3에서 거부되면 위치 4, 5에서 생성한 draft 토큰의 연산은 모두 허비된다. Tree-based approach는 이 낭비를 줄이는 것이 목표이다.

### Token Tree와 Tree Attention

Tree-based speculative decoding은 이 문제를 **여러 대안 경로를 동시에 탐색**하는 방식으로 해결한다. Draft 단계에서 단일 시퀀스 대신 **토큰 트리(token tree)**를 구성하여, 각 위치에서 여러 후보 토큰을 생성하고 이들의 조합을 트리 형태로 표현한다.

![Tree-based Speculative Decoding](figures/fig_5.png)
*Tree-based speculative decoding의 구조. 왼쪽은 토큰 트리(token tree)의 구성을 보여준다. 루트 노드에서 시작하여 각 깊이에서 여러 후보 토큰이 분기하며, 각 경로가 하나의 draft 시퀀스 후보를 나타낸다. 오른쪽은 이 트리 구조에 대응하는 tree attention mask로, 초록색 셀은 attend 가능, 빈 셀은 마스킹된 위치를 나타낸다. 각 노드는 루트에서 자신까지의 경로 상에 있는 조상 노드에만 attend할 수 있다.*

Tree attention의 핵심은 **causal attention mask를 트리 구조에 맞게 확장**하는 것이다. 일반적인 causal mask에서는 위치 $i$가 위치 $j \leq i$인 모든 토큰에 attend하지만, tree attention에서는 위치 $i$가 **자신의 조상 노드(ancestor nodes)**에만 attend한다.

구체적으로, 트리 $\mathcal{T}$의 attention mask $M$은 다음과 같이 정의된다:

$$M[i][j] = \begin{cases} 1 & \text{if node } j \text{ is an ancestor of node } i \text{ in } \mathcal{T} \\ 0 & \text{otherwise} \end{cases}$$

이를 통해 하나의 forward pass로 트리의 모든 경로를 동시에 검증할 수 있다. 트리의 각 경로에 대한 logits가 독립적으로 계산되며, 각 경로에 대해 독립적으로 수락/거부 판정이 이루어진다. 가장 긴 수락 경로가 최종 출력으로 선택된다.

### Tree 구조의 이점 분석

토큰 예산이 동일할 때, tree 구조가 linear draft보다 왜 유리한지 분석하자.

Linear draft ($\gamma = 6$): 하나의 경로, 6개 토큰
- 기대 수락 토큰 ($\alpha = 0.8$): $\frac{1 - 0.8^7}{0.2} \approx 4.0$개

Tree draft (예산 6, 2-2-2 구조): 3개의 깊이 2 경로
- 최소 하나의 경로에서 깊이 $d$까지 수락될 확률: $1 - (1 - \alpha^d)^{b_d}$
- 깊이 1에서 2개 후보 중 최소 하나 수락: $1 - (1-0.8)^2 = 0.96$
- 깊이 2에서 2개 후보 중 최소 하나 수락: $0.96 \times (1 - (1-0.8)^2) = 0.922$
- 기대 수락: 약 2.9개이지만, 실패 시 대안 경로 활용으로 전체 기대값은 더 높아짐

핵심 통찰: 트리는 **불확실한 위치에서의 분기**를 통해 "보험"을 들어, 하나의 경로가 실패하더라도 다른 경로가 성공할 가능성을 확보한다.

### Token Tree 구성 전략

트리의 구조(토폴로지)를 어떻게 설계하느냐에 따라 성능이 크게 달라진다.

**고정 트리 구조**: 미리 정해진 분기 패턴을 사용한다.

- **SpecInfer**(Miao et al., 2024): 여러 독립적인 draft 모델(SSM: Small Speculative Models)을 사용하여 각각의 draft 시퀀스를 생성하고, 이들을 합쳐서 트리를 구성. $m$개의 draft 모델이 각각 $\gamma$개의 토큰을 생성하면, 최대 $m \times \gamma$개의 노드를 가진 트리가 구성된다
- **Medusa**: 각 prediction head의 top-$k$ 후보를 조합하여 Cartesian product 형태의 트리를 구성. $K$개의 헤드, 각각 top-$s$이면 최대 $s^K$개의 리프 노드가 가능하지만, 이는 지수적으로 증가하므로 확률 기반 pruning으로 토큰 예산 내로 제한. 상위 확률 경로만 남기는 beam search 유사 전략을 사용

**동적 트리 구조**: Draft 모델의 confidence에 따라 분기를 적응적으로 결정한다.

- **EAGLE-2**(Li et al., 2024): Draft 모델의 예측 confidence가 높은 위치에서는 분기를 줄이고(해당 예측이 맞을 확률이 높으므로), 불확실한 위치에서는 분기를 늘리는(여러 대안을 탐색해야 하므로) 적응적 전략. 이를 통해 동일한 토큰 예산으로 더 높은 수락률을 달성
- **Sequoia**(Chen et al., 2024): 최적의 트리 토폴로지를 이론적으로 분석하고, 수락률을 최대화하는 트리 구조를 동적으로 구성. 하드웨어 제약(메모리, 연산 예산)을 고려한 최적화 프레임워크 제공. 이 방법의 상세 분석은 아래에서 다룬다

**토큰 예산과 트리 크기의 트레이드오프**: 트리의 노드 수(토큰 예산)가 커지면 더 많은 경로를 탐색할 수 있지만, 검증에 필요한 연산량도 증가한다. 트리의 총 노드 수를 $N$이라 하면, 검증에 필요한 attention 연산은 $O(N^2)$ (self-attention within tree) + $O(N \cdot L)$ (tree nodes attending to context of length $L$)이다.

최적의 토큰 예산은 다음을 균형있게 고려해야 한다:
- **더 많은 노드** $\rightarrow$ 더 많은 대안 경로 $\rightarrow$ 더 긴 수락 경로 기대 $\rightarrow$ 더 높은 처리량
- **더 많은 노드** $\rightarrow$ 더 큰 attention matrix $\rightarrow$ 더 높은 검증 비용 $\rightarrow$ 라운드당 지연 시간 증가
- **최적 $N$**은 하드웨어의 연산/메모리 특성에 의존: GPU가 강력할수록 더 큰 트리가 유리

## 시스템 수준 최적화

### Sequential vs. Parallel Speculative Decoding

기본적인 speculative decoding은 **sequential** 방식으로, draft 생성이 완전히 끝난 후 검증을 시작한다. 이 방식에서는 draft 생성 동안 target 모델의 GPU가 유휴 상태에 놓이고, 검증 동안 draft 모델의 자원이 유휴 상태에 놓인다.

![Sequential vs. Parallel 처리 비교](figures/fig_6.png)
*Sequential과 Parallel speculative decoding 비교. 상단의 Sequential 방식에서는 Draft 모델이 토큰 0-3을 생성한 후 Target 모델이 검증하여, 두 모델이 교대로 실행된다. 하단의 Parallel 방식에서는 Draft 모델이 다음 라운드의 draft(토큰 4-7)를 생성하는 동안 Target 모델이 현재 라운드의 draft(토큰 0-3)를 동시에 검증한다. 검증 결과(수락 표시)가 나오면 draft 모델은 유효한 부분부터 다시 시작한다.*

**Parallel speculative decoding**은 draft 생성과 검증을 **파이프라인으로 중첩**하여 실행한다:

1. **Round 1**: Draft 모델이 토큰 0-3을 생성. 이 동안 Target 모델은 대기 (초기 라운드)
2. **Round 2**: Target 모델이 토큰 0-3을 검증하는 동안, Draft 모델은 **낙관적으로** 토큰 4-7을 이미 생성 시작 (토큰 0-3이 모두 수락될 것으로 가정)
3. **결과 반영**: Target 모델의 검증 결과가 나오면:
   - 모든 토큰이 수락된 경우: Draft 모델의 토큰 4-7을 그대로 다음 검증에 사용
   - 토큰 2에서 거부된 경우: 토큰 3 이후의 draft(토큰 3, 4-7)를 모두 폐기하고, 보정된 토큰 2부터 다시 생성

이 방식의 핵심 과제는 **검증 결과가 나오기 전에 생성한 draft가 무효화될 수 있다**는 것이다. 이를 **speculative waste**라 하며, 수락률이 낮을수록 낭비가 커진다. 그러나 두 모델이 별도의 하드웨어에서 실행되는 경우(예: draft는 CPU, target은 GPU), 이 낭비는 wall-clock time에 영향을 미치지 않으므로 순수한 이득이 된다.

Parallel 방식의 이론적 속도 향상은:

$$S_{\text{parallel}} = \frac{(1 - \alpha^{\gamma+1}) / (1 - \alpha)}{\max(\gamma \cdot c, 1)}$$

$c < 1/\gamma$이면 $S_{\text{parallel}} > S_{\text{sequential}}$이 된다. 즉, draft 모델이 충분히 빠르면 parallel 방식이 항상 유리하다.

### Asynchronous & Heterogeneous Scheduling

실제 배포 환경에서는 더 정교한 스케줄링 전략이 필요하다.

![비동기 및 이종 스케줄링](figures/fig_7.png)
*비동기(Asynchronous) 및 이종(Heterogeneous) 스케줄링 전략. (a) 왼쪽: 동기(Synchronous) 스케줄에서는 draft와 검증이 순차적으로 교대 실행되어 GPU 유휴 시간이 발생한다(빨간 블록). 비동기(Asynchronous) 스케줄에서는 draft 생성이 검증과 중첩되어 GPU 유휴 시간이 감소하고, 검증 완료 시 stop signal로 draft를 중단한다. (b) 오른쪽: Non-heterogeneous 스케줄에서는 Draft LM과 Target LM이 동일한 GPU에서 시분할로 실행되지만, Heterogeneous 스케줄에서는 Draft LM을 CPU에, Target LM을 GPU에 배치하여 물리적 병렬성을 달성한다.*

**Asynchronous Scheduling**: Draft 생성과 검증을 비동기적으로 실행한다. 검증이 끝나면 즉시 중단 신호(stop signal)를 보내 진행 중인 draft 생성을 중단하고, 검증 결과를 반영하여 새 draft 생성을 시작한다.

- **ASD**(Liu et al., 2024): Asynchronous Speculative Decoding으로, draft 생성기가 검증 결과를 기다리지 않고 계속 토큰을 생성한다. 검증 실패 시 해당 시점 이후의 draft만 폐기. 핵심 설계 결정은 stop signal의 타이밍이다 -- 너무 이르면 draft가 부족하고, 너무 늦으면 speculative waste가 증가
- **장점**: GPU 유휴 시간 제거로 하드웨어 활용률 극대화. 특히 draft 생성이 target 검증보다 빠른 경우(일반적인 시나리오) 효과적
- **단점**: Speculative waste 발생, 구현 복잡도 증가, 분포 보존이 정확히 보장되려면 추가적인 처리 필요

비동기 스케줄링의 구체적 동작:

1. Draft 생성기가 지속적으로 토큰을 생성하며 큐에 저장
2. 검증기가 큐에서 $\gamma$개의 draft를 가져와 검증 실행
3. 검증 완료 시 stop signal 발생:
   - 수락된 토큰들을 최종 출력에 추가
   - 거부 위치 이후의 큐 내용을 모두 폐기
   - 보정된 토큰을 새 draft의 시작점으로 설정
4. Draft 생성기가 새 시작점부터 다시 생성 시작

**Heterogeneous Scheduling**: Draft 모델과 target 모델을 **서로 다른 하드웨어**에서 실행한다.

- Draft 모델은 CPU 또는 소형 GPU(또는 전용 가속기)에서 실행
- Target 모델은 주 GPU(또는 GPU 클러스터)에서 실행
- 두 모델이 물리적으로 분리되므로, 파이프라인 병렬성이 자연스럽게 달성

이 전략의 핵심 이점:

1. **자원 경합 제거**: 동일 GPU에서 두 모델을 시분할(time-sharing)로 실행하면, 컨텍스트 스위칭과 메모리 경합이 발생. 하드웨어를 분리하면 이 문제가 없음
2. **Draft 모델의 "무료" 실행**: CPU에서 draft를 생성하면, GPU의 검증과 완전히 병렬로 실행되므로 draft 생성의 wall-clock 비용이 0에 수렴
3. **확장성**: Target 모델이 여러 GPU에 분산되어 있을 때, draft 모델은 별도의 저비용 하드웨어에 배치 가능

이 전략은 특히 **edge deployment** 시나리오에서 유용하다. 예를 들어, 모바일 기기의 NPU에서 draft를 생성하고 클라우드 GPU에서 검증하는 구성이 가능하다. 또한 **서빙 시스템**에서는 draft 생성을 별도의 저비용 인스턴스에 오프로드하여 주 GPU의 배치 처리 효율을 높일 수 있다.

### KV Cache 관리

Speculative decoding에서 KV cache 관리는 중요하면서도 복잡한 시스템 과제이다.

**Draft 토큰의 KV cache**: 검증 과정에서 draft 토큰들의 KV cache가 생성되는데, 거부된 토큰의 KV cache는 롤백(rollback)해야 한다. Linear draft에서는 거부 위치 이후의 KV cache를 단순히 잘라내면 되지만, tree-based 방법에서는 트리 구조의 KV cache를 효율적으로 관리하는 메커니즘이 필요하다.

Tree-based KV cache 관리의 과제:
- 수락된 경로의 KV cache만 유지하고 나머지 경로의 cache를 해제
- 트리의 각 노드가 서로 다른 조상 경로를 가지므로, 경로별 독립적인 cache 관리 필요
- 다음 라운드에서 수락된 경로의 KV cache를 재활용하기 위한 효율적인 재배열

**Shared KV cache**: Self-drafting 방식(예: Medusa, EAGLE)에서는 draft 모델과 target 모델이 동일한 KV cache를 공유할 수 있어 메모리 효율이 높다. Draft 단계에서 생성된 KV cache가 검증 단계에서 그대로 사용되므로, 중복 연산이 없다. 반면, 독립 draft 모델을 사용하는 경우 별도의 KV cache가 필요하여 메모리 사용량이 증가한다.

**Paged Attention과의 통합**: vLLM 같은 서빙 프레임워크는 Paged Attention을 사용하여 KV cache를 가상 메모리처럼 관리한다. 고정 크기의 "페이지"로 KV cache를 분할하여, 동적으로 할당/해제한다. Tree-based speculative decoding의 KV cache를 Paged Attention에 통합하려면 트리 구조를 페이지 단위로 관리하는 추가 로직이 필요하다. 이는 특히 배치 환경에서 여러 요청의 트리가 동시에 존재할 때 복잡해진다.

## 주요 기법들의 심층 분석

### Medusa: Multi-head Parallel Drafting

Medusa(Cai et al., 2024)는 target 모델의 마지막 hidden state 위에 $K$개의 추가 **prediction head**를 부착하여, 단일 forward pass로 $K$개의 미래 토큰을 동시에 예측한다.

**아키텍처**: 각 Medusa head $k \in \{1, \ldots, K\}$는 단순한 ResNet 블록 + Linear layer로 구성된다:

$$h'_k = h_t + \text{SiLU}(W_k^{(1)} \cdot h_t + b_k^{(1)})$$

$$\hat{p}_{t+k} = \text{softmax}(W_k^{(2)} \cdot h'_k + b_k^{(2)})$$

여기서 $h_t$는 target 모델의 위치 $t$에서의 마지막 hidden state이다. 각 헤드의 파라미터 수는 약 $2 \times d^2$로, target 모델 전체 대비 무시할 수 있는 수준이다. 예를 들어 Llama 2-7B ($d = 4096$)에서 5개의 Medusa head는 약 168M 파라미터로, 전체 모델(7B)의 2.4%에 불과하다.

**학습**: Target 모델의 파라미터를 freeze하고, Medusa head만 학습한다. 학습 목표는 각 헤드가 해당 위치의 정확한 토큰을 예측하는 것이다:

$$\mathcal{L} = \sum_{k=1}^{K} \sum_{t} \text{CE}(\hat{p}_{t+k}, x_{t+k})$$

학습 데이터는 target 모델의 학습 데이터와 동일한 분포에서 가져오며, ShareGPT 같은 대화 데이터를 사용할 수도 있다. 학습에 필요한 시간은 수 시간 수준(A100 1대 기준)으로 비교적 빠르다.

**Tree Construction과 Pruning**: 각 헤드의 top-$s$ 후보를 사용하여 트리를 구성한다. $K$개의 헤드, 각각 top-$s$이면 최대 $s^K$개의 경로가 가능하지만, 이는 지수적으로 증가하므로 확률 기반 pruning으로 토큰 예산 내로 제한한다.

Pruning 전략: 각 경로의 결합 확률 $\prod_{k=1}^{K} \hat{p}_{t+k}(\tilde{x}_{t+k})$을 계산하고, 상위 $N$개의 경로만 유지한다. 이를 통해 토큰 예산 $N$으로 가장 유망한 후보들만 검증한다.

**Medusa-2**: 학습 시 target 모델도 함께 fine-tuning하여 Medusa head와의 호환성을 높인다:

$$\mathcal{L}_{\text{total}} = \mathcal{L}_{\text{LM}} + \lambda \sum_{k=1}^{K} \mathcal{L}_{\text{head}_k}$$

이 joint training은 target 모델의 hidden state가 Medusa head에 더 유용한 정보를 제공하도록 유도한다. 실험에서 Medusa-2는 Medusa-1 대비 약 20% 더 높은 수락률을 달성했다.

### EAGLE: Feature-level Auto-regressive Drafting

EAGLE(Li et al., 2024)은 토큰 수준이 아닌 **feature 수준**에서 auto-regressive drafting을 수행한다는 점에서 독창적이다.

**핵심 관찰**: 토큰 시퀀스 $(x_1, x_2, \ldots)$보다 target 모델의 **feature 시퀀스** $(f_1, f_2, \ldots)$ (두 번째 마지막 레이어의 hidden state)가 더 예측하기 쉽다. 이에 대한 정보 이론적 근거:

- 토큰은 이산적이고 $\arg\max$ 연산으로 인한 정보 손실이 있다. 예를 들어, 위치 $t$에서 target 모델이 "the"에 0.35, "a"에 0.30, "an"에 0.15를 부여했지만 "the"가 선택되면, 0.65에 해당하는 다른 가능성에 대한 정보가 모두 소실된다.
- Feature는 연속적이고 더 풍부한 정보를 담고 있다. Hidden state $f_t$는 해당 위치에서의 전체 확률 분포를 암시적으로 인코딩하고 있으므로, 다음 토큰 예측에 더 유용한 정보를 제공한다.

**아키텍처**: EAGLE의 draft 모델은 단일 Transformer 레이어로 매우 경량이다. 입력으로 이전 토큰의 임베딩과 이전 위치의 target feature를 받는다:

$$f'_{t+1} = \text{TransformerLayer}(\text{Concat}(\text{Embed}(x_t), f_t))$$

$$\hat{p}_{t+1} = \text{LM\_Head}(f'_{t+1})$$

여기서 LM_Head는 target 모델의 것을 재활용하여 추가 파라미터가 거의 없다. 전체 draft 모델의 파라미터 수는 target 모델의 약 1%에 불과하다.

**Auto-regressive Feature Prediction**: EAGLE의 draft 모델은 feature를 auto-regressively 예측하므로, $\gamma$개의 draft 토큰을 생성하려면 draft 모델의 $\gamma$번 forward pass가 필요하다. 그러나 draft 모델이 단일 Transformer 레이어이므로 각 forward pass의 비용이 매우 작다 ($c \approx 0.02 \sim 0.05$).

**성능**: EAGLE은 Medusa 대비 약 1.5~2배 더 높은 수락률을 달성하며, Llama 2-Chat 70B에서 3.5~4배의 lossless 속도 향상을 보고했다. 이는 feature-level prediction의 우위를 명확히 보여준다.

### Lookahead Decoding: Jacobi Iteration 기반

Lookahead Decoding(Fu et al., 2024)은 별도의 draft 모델 학습 없이 **target 모델만으로** 병렬 디코딩을 수행하는 독창적인 방법이다.

**Jacobi Iteration의 수학적 기반**: Auto-regressive decoding을 다음과 같은 비선형 연립방정식 시스템으로 볼 수 있다:

$$x_1 = g_1(\text{prompt})$$
$$x_2 = g_2(\text{prompt}, x_1)$$
$$\vdots$$
$$x_n = g_n(\text{prompt}, x_1, \ldots, x_{n-1})$$

여기서 $g_t(\cdot) = \arg\max P(x_t \mid \cdot)$ (greedy decoding의 경우). 이 시스템에 Jacobi iteration을 적용하면, 모든 위치의 토큰을 동시에 업데이트하는 반복법이 된다:

$$x_t^{(k+1)} = g_t(\text{prompt}, x_1^{(k)}, \ldots, x_{t-1}^{(k)}), \quad t = 1, \ldots, n$$

이 반복을 수렴할 때까지 계속하면, greedy decoding의 결과와 동일한 시퀀스를 얻는다. 각 반복에서 모든 위치를 병렬로 업데이트하므로 GPU 활용도가 높다. 수렴이 보장되는 이유는 auto-regressive 모델의 고정점이 유일하기 때문이다.

**Lookahead/Verification 윈도우**: 실전에서는 전체 시퀀스에 대해 Jacobi iteration을 수행하는 것이 비효율적이므로, 현재 위치 이후 $W$개의 위치에 대해서만 반복을 수행한다. 이 $W$개의 위치에서 연속적으로 고정점(fixed point)에 도달한 부분 시퀀스(n-gram)를 식별하여 한 번에 수락한다.

**장점과 한계**:
- **장점**: 별도의 draft 모델이 전혀 불필요. 추가 메모리 비용 없음. 어떤 target 모델에도 바로 적용 가능
- **한계**: Greedy decoding에만 적용 가능 (sampling 기반 디코딩은 고정점이 존재하지 않음). 수렴 속도가 예측 불가능하여 가속 배율의 분산이 큼

### DistillSpec: Distillation for Better Drafting

DistillSpec(Zhou et al., 2024)은 draft 모델의 학습에 **Knowledge Distillation**을 체계적으로 적용한다.

**학습 목표**: Draft 모델의 분포 $q$와 target 모델의 분포 $p$ 사이의 divergence를 최소화한다:

$$\mathcal{L}_{\text{distill}} = \mathbb{E}_{x \sim \mathcal{D}}\left[\sum_t D_{\text{KL}}(p(\cdot \mid x_{<t}) \| q(\cdot \mid x_{<t}))\right]$$

여기서 $D_{\text{KL}}$은 Kullback-Leibler divergence이다. 이 학습을 통해 draft 모델은 단순히 정답 토큰을 맞추는 것이 아니라, target 모델의 **전체 확률 분포**를 모방하게 된다. 이 점이 표준 지도학습(supervised learning)과의 핵심 차이이다.

표준 지도학습에서는 one-hot target을 사용하므로 "the"가 정답이면 "a"의 확률은 0으로 학습된다. 그러나 target 모델은 "a"에도 상당한 확률을 부여하고 있으며, 이 "soft" 분포를 모방하는 것이 수락률 최적화에 핵심적이다. DistillSpec의 실험에서 분포 매칭으로 학습한 draft 모델은 표준 지도학습 대비 15~25% 더 높은 수락률을 보였다.

**On-policy vs. Off-policy Distillation**: DistillSpec은 on-policy distillation이 더 효과적임을 보인다. Off-policy(고정 데이터셋 사용)에서는 draft 모델이 자신이 생성하지 않을 시퀀스에 대해서만 학습하는 분포 불일치(distribution mismatch)가 발생하지만, on-policy(draft 모델이 생성한 시퀀스에 대해 학습)에서는 이 문제가 해결된다. On-policy 학습은 draft 모델이 실제 추론 시 마주하게 될 분포에서 학습하므로, 실전 수락률이 더 높다.

### Sequoia: 최적 토큰 트리 구성

Sequoia(Chen et al., 2024)는 트리 구조의 최적화를 **이론적으로** 접근한 최초의 연구 중 하나이다.

**최적화 문제 정의**: 주어진 토큰 예산 $N$ 하에서 기대 수락 길이를 최대화하는 트리 토폴로지 $\mathcal{T}^*$를 찾는다:

$$\mathcal{T}^* = \arg\max_{\mathcal{T}: |\mathcal{T}| \leq N} \mathbb{E}[\text{max accepted path length in } \mathcal{T}]$$

**동적 프로그래밍 솔루션**: 이 최적화 문제를 동적 프로그래밍으로 효율적으로 풀 수 있음을 보인다. 핵심 관찰: 깊이 $d$에서의 최적 분기 수(branching factor) $b_d$는 해당 깊이에서의 수락률 $\alpha_d$에 의존한다. 수락률이 낮은 깊이에서는 더 많이 분기하고, 높은 깊이에서는 적게 분기하는 것이 최적이다.

**Hardware-aware 최적화**: 동일한 토큰 예산이라도 하드웨어에 따라 최적의 트리 구조가 다르다. Sequoia는 다음 비용 모델을 사용한다:

$$\text{Verification Cost}(N) = a \cdot N^2 + b \cdot N \cdot L + c$$

여기서 $a$는 tree-internal attention 비용, $b$는 tree-to-context attention 비용, $c$는 고정 오버헤드이다. 이 비용 모델의 파라미터는 하드웨어 프로파일링으로 결정되며, 이를 기반으로 하드웨어별 최적 트리가 제안된다.

실험에서 Sequoia는 고정 구조 대비 10~30% 더 높은 기대 수락 길이를 달성했다.

## 응용

### Speculative Decoding의 변형: Lossless vs. Lossy

Speculative decoding의 변형들을 **분포 보존 여부**에 따라 분류할 수 있다:

**Lossless Speculative Decoding**: 출력 분포가 target 모델과 정확히 동일. Rejection sampling 기반의 원래 방법이 여기에 해당한다. 가장 강력한 이론적 보장을 제공하지만, 수락률이 분포 일치도에 의해 제한된다.

**$\epsilon$-Lossless Speculative Decoding**: 출력 분포와 target 분포 사이의 거리가 $\epsilon$ 이내. Typical acceptance(Medusa) 등이 여기에 해당한다. $\epsilon$을 조절하여 수락률과 품질 사이의 트레이드오프를 제어할 수 있다.

**Lossy Speculative Decoding**: 출력 분포가 target과 다를 수 있으나, 실용적 품질은 유지. BiLD, speculative sampling with relaxed constraints 등이 여기에 해당한다. 가장 높은 수락률을 달성할 수 있으나, 품질 저하 가능성이 있으므로 벤치마크 평가가 필요하다.

실전에서는 대부분의 서비스가 lossless 방법을 선호한다. 이는 모델 평가와 안전성 검증이 target 모델 기준으로 이루어지기 때문에, 출력 분포가 변하면 기존 평가 결과가 무효화될 수 있기 때문이다.

### Batch Speculative Decoding

실제 서비스에서는 여러 요청을 동시에 처리하는 **배치 환경**에서 speculative decoding을 적용해야 한다. 이때의 핵심 과제는:

**가변 수락 길이**: 배치 내 각 요청의 수락 길이가 다르므로, 한 라운드 후의 진행 상태가 요청마다 다르다. 짧게 수락된 요청은 다음 라운드에서 더 많은 draft를 생성해야 하고, 길게 수락된 요청은 적은 draft로 충분하다. 이를 처리하기 위해 각 요청별 독립적인 draft 길이를 관리해야 한다.

**동적 배치 조정**: 수락/거부 패턴에 따라 배치 내 시퀀스 길이가 불균일해지므로, padding이나 dynamic batching이 필요하다. 과도한 padding은 연산 낭비를 유발하므로, 비슷한 길이의 요청끼리 그룹화하는 전략이 중요하다.

**Throughput과 Latency의 균형**: 배치 크기가 큰 환경에서는 speculative decoding이 오히려 throughput을 감소시킬 수 있다. 이는 검증 단계에서 배치 내 모든 요청의 draft를 동시에 처리해야 하므로, 단일 요청 대비 연산량이 크게 증가하기 때문이다. 따라서 배치 크기에 따라 speculative decoding의 적용 여부를 동적으로 결정하는 전략이 필요하다.

### Multi-turn / Long Context 시나리오

긴 컨텍스트에서의 speculative decoding은 추가적인 고려사항이 있다:

- **KV cache 크기**: 컨텍스트가 길어질수록 KV cache가 커져 메모리 제약이 심해진다. Tree-based 방법은 트리의 각 경로에 대한 KV cache를 관리해야 하므로 더 많은 메모리가 필요하다. 128K 컨텍스트에서 tree-based SD의 메모리 사용량은 vanilla decoding의 1.5~2배에 달할 수 있다
- **Draft 품질 변화**: 긴 컨텍스트에서는 draft 모델의 수락률이 하락할 수 있다. 이는 작은 모델이 긴 의존성을 잘 포착하지 못하기 때문이다. 특히 독립 소형 모델의 경우 이 문제가 두드러진다
- **적응적 전략**: EAGLE-2, Sequoia 등은 컨텍스트 길이에 따라 draft 길이와 트리 구조를 동적으로 조절한다. 컨텍스트가 길어지면 트리를 작게 유지하고, 짧은 컨텍스트에서는 트리를 크게 키우는 전략

### AR Image Generation에의 적용

Speculative decoding의 원리는 텍스트를 넘어 **auto-regressive 이미지 생성**에도 적용 가능하다. 최근 LlamaGen(Sun et al., 2024), VAR(Tian et al., 2024) 등의 모델이 이미지를 visual token 시퀀스로 표현하고 auto-regressive하게 생성하는데, 이러한 모델에도 speculative decoding을 적용하여 생성 속도를 향상시킬 수 있다.

AR 이미지 생성에서의 speculative decoding 파이프라인:

1. 입력 이미지/텍스트로부터 visual token 시퀀스 생성 시작
2. 작은 draft AR 모델이 visual token draft를 빠르게 생성
3. 큰 target AR 모델이 draft를 검증
4. 수락된 visual token을 Diffusion process 또는 decoder로 전달하여 최종 이미지 생성

텍스트와의 주요 차이점은:
- **시퀀스 길이**: 이미지의 visual token 수는 수백~수천 개(예: 256x256 이미지 = 1024 tokens)로 텍스트보다 훨씬 길어, 가속 효과가 더 크다
- **토큰 분포**: Visual token의 분포가 텍스트 토큰과 다르므로, draft 모델의 설계와 수락 기준을 조정해야 한다. 이미지에서는 인접 토큰 간의 상관관계가 더 강하여 수락률이 높을 수 있다
- **품질 메트릭**: 텍스트에서는 정확한 분포 보존이 중요하지만, 이미지에서는 시각적 품질(FID, IS)이 더 중요할 수 있어 **lossy** 가속도 허용 가능

### 실전 성능 벤치마크

서베이에서 정리한 주요 기법들의 실전 성능을 비교하면 다음과 같다 (Llama 2-Chat 계열 기준):

| 기법 | Target 모델 | Lossless | 속도 향상 | 추가 파라미터 |
|-----|-----------|:-------:|:-------:|:----------:|
| Vanilla SD | 70B (draft: 7B) | O | 1.8~2.2x | 7B |
| Medusa-1 | 7B | $\epsilon$-lossless | 2.0~2.5x | ~170M |
| Medusa-2 | 7B | $\epsilon$-lossless | 2.3~2.8x | ~170M |
| EAGLE | 7B | O | 2.5~3.5x | ~70M |
| EAGLE-2 | 7B | O | 3.0~4.0x | ~70M |
| Lookahead | 7B | O (greedy) | 1.5~2.0x | 0 |
| Prompt Lookup | 7B | O | 1.2~2.5x* | 0 |
| Sequoia | 70B | O | 2.5~3.5x | ~7B |

(*Prompt Lookup의 가속 배율은 입력 내용에 강하게 의존하며, 코드 완성 같은 도메인에서는 높고, 일반 대화에서는 낮다.)

이 벤치마크에서 주목할 점:
- EAGLE 계열이 가장 높은 lossless 속도 향상을 달성
- Medusa는 학습이 쉽고 구현이 단순한 장점이 있음
- Lookahead와 Prompt Lookup은 추가 학습 없이 바로 적용 가능
- 모든 기법이 양자화와 결합하면 추가 가속 가능

### Speculative Decoding과 다른 최적화 기법의 결합

Speculative decoding은 다른 추론 최적화 기법들과 **직교적(orthogonal)**이므로 결합이 가능하다:

| 최적화 기법 | 결합 방식 | 추가 효과 |
|-----------|---------|---------|
| **Quantization** | Draft/target 모델 모두 양자화 | Draft 속도 $\uparrow$, 메모리 $\downarrow$ |
| **KV Cache Compression** | Cache 크기 감소 | 더 긴 컨텍스트 지원 |
| **Flash Attention** | 검증 단계 가속 | Tree attention 효율 $\uparrow$ |
| **Model Parallelism** | Target 모델 분산 처리 | 대형 모델 지원 |
| **Continuous Batching** | 배치 환경 최적화 | 처리량(throughput) $\uparrow$ |
| **Sparse Attention** | Attention 연산 감소 | 장문 컨텍스트 지원 |

특히 **양자화(quantization)**와의 결합은 매우 효과적이다. Draft 모델을 INT4로 양자화하면 모델 크기와 연산 비용이 크게 줄어들어 draft 생성 속도가 향상되고, target 모델의 GPU 메모리를 덜 점유하게 된다. GPTQ, AWQ 같은 양자화 기법을 draft 모델에 적용하면 $c$를 0.02~0.03 수준으로 낮출 수 있어, 더 긴 draft 길이가 최적이 된다.

## 최근 발전 동향 (2024-2025)

### Online Speculative Decoding

Online Speculative Decoding(Liu et al., 2024)은 서비스 운영 중에 draft 모델을 **지속적으로 업데이트**하는 방법이다. 사용자의 실제 쿼리와 target 모델의 응답을 사용하여 draft 모델을 온라인으로 fine-tuning함으로써, 도메인 특화 수락률을 점진적으로 향상시킨다.

이 방법의 핵심 동기: 범용 draft 모델은 특정 도메인(예: 의료, 법률, 코드)에서 수락률이 낮을 수 있다. 서비스 운영 중에 해당 도메인의 데이터가 자연스럽게 축적되므로, 이를 활용하여 draft 모델을 점진적으로 도메인에 적응시킨다.

학습 전략:
- Target 모델의 출력 logits를 soft label로 사용하여 draft 모델을 distillation
- Exponential moving average로 draft 모델 파라미터를 안정적으로 업데이트
- 주기적으로 수락률을 모니터링하여 학습 속도를 조절

### Multi-model Speculative Decoding

단일 draft 모델 대신 **여러 draft 모델**을 계층적으로 사용하는 방법이다. 이를 **cascade speculative decoding**이라고도 한다:

- Tier 1: N-gram 모델 (매우 빠름, 낮은 수락률) -- "쉬운" 토큰 처리
- Tier 2: 소형 Transformer (빠름, 중간 수락률) -- 일반적인 토큰 처리
- Tier 3: 중형 Transformer (보통 속도, 높은 수락률) -- "어려운" 토큰 처리

각 tier의 출력을 결합하여 tree를 구성하면, 단일 draft 모델보다 더 풍부한 후보를 생성할 수 있다. 또한 각 tier의 confidence에 따라 동적으로 어떤 tier를 사용할지 결정하는 라우팅 메커니즘도 연구되고 있다.

### Speculative Decoding for Structured Output

JSON, SQL, 코드 등 **구조화된 출력**을 생성할 때, draft 모델에 문법 제약(grammar constraint)을 적용하여 유효하지 않은 토큰이 draft에 포함되지 않도록 한다. 이를 통해 구조적 유효성을 보장하면서도 가속 효과를 유지할 수 있다.

구체적인 적용:
- **JSON 생성**: Draft 모델의 출력을 JSON 파서로 검증하여, 구문적으로 유효한 토큰만 draft에 포함. 예를 들어, `"key":` 이후에는 값(문자열, 숫자, 배열 등)이 와야 하므로 해당 토큰만 후보로 제한
- **SQL 생성**: SQL 문법에 따른 context-free grammar로 draft 토큰을 제약. `SELECT` 이후에는 컬럼명이, `FROM` 이후에는 테이블명이 와야 하는 등의 구조적 제약을 반영
- **코드 생성**: 프로그래밍 언어의 구문 규칙에 따른 제약. 괄호 매칭, 키워드 순서, 들여쓰기 규칙 등을 draft 시점에서 강제
- **함수 호출(Tool Use)**: LLM의 function calling에서 인자 형식에 맞는 토큰만 draft에 포함하여, 유효한 함수 호출 시퀀스만 생성

이러한 제약을 draft 단계에서 적용하면, 구문적으로 무효한 토큰이 draft에 포함되지 않으므로 수락률이 향상되는 부가적 이점도 있다. 또한 constrained decoding과 speculative decoding의 결합은 서로의 장점을 강화한다 -- constrained decoding이 탐색 공간을 줄여주고, speculative decoding이 제약된 공간 내에서의 탐색을 가속한다.

### Speculative Decoding for Reasoning Models

2024~2025년에 등장한 o1, o3, DeepSeek-R1 같은 **reasoning 모델**은 chain-of-thought 토큰을 대량으로 생성하므로, speculative decoding의 가속 효과가 더욱 커진다. Reasoning 과정에서 생성되는 토큰 수가 수천~수만 개에 달하므로, 토큰당 latency 절감의 누적 효과가 매우 크다.

Reasoning 모델에서의 speculative decoding 특성:
- **Thinking tokens의 높은 예측 가능성**: Reasoning 과정에서 사용되는 논리적 연결어("therefore", "because", "let's consider" 등)는 예측하기 쉬워 높은 수락률 달성 가능
- **수학적 표현의 구조적 특성**: 수식 전개 과정에서 연산자와 변수의 패턴이 반복되므로, N-gram 기반이나 retrieval 기반 방법도 효과적
- **긴 시퀀스 생성**: 생성 시퀀스가 길수록 speculative decoding의 누적 가속 효과가 커져, reasoning 모델에서 가장 높은 ROI를 제공

### Speculative Decoding in Serving Systems

주요 LLM 서빙 프레임워크들의 speculative decoding 지원 현황 (2025년 기준):

- **vLLM**: Speculative decoding 내장 지원. Draft 모델 기반, Medusa, EAGLE, N-gram 등 다양한 방법 지원. Paged Attention과의 통합으로 메모리 효율적. `--speculative-model` flag로 쉽게 활성화 가능
- **TensorRT-LLM**: NVIDIA 최적화 엔진 위에서의 speculative decoding. CUDA 커널 수준 최적화로 높은 효율. H100의 FP8 텐서 코어를 활용한 draft 모델 가속
- **llama.cpp**: CPU/GPU 혼합 환경에서의 speculative decoding 지원. `--draft` 옵션으로 draft 모델 지정. Edge deployment에 적합한 경량 구현
- **Hugging Face TGI**: Draft 모델 기반 speculative decoding 지원. `--speculate` 옵션으로 draft 토큰 수 설정
- **SGLang**: EAGLE과 Radix Attention을 결합한 고성능 speculative decoding. Prefix caching과의 자연스러운 통합

## 의의 및 한계

### 이 서베이의 의의

1. **통합적 분류 체계**: Generation-Refinement 프레임워크라는 통합 렌즈 아래 모든 speculative decoding 기법을 체계적으로 분류하여, 각 기법의 위치와 관계를 명확히 했다. 이전에는 draft model, parallel decoding, self-speculative decoding 등이 별개의 연구 흐름으로 인식되었으나, 이 서베이가 이들의 공통 구조를 밝혀냈다.

2. **포괄적 범위**: Draft 생성 방법, 검증 전략, 트리 기반 확장, 시스템 수준 최적화, 응용까지 이 분야의 전체 지형도를 제시했다. 기존 서베이들이 특정 측면만 다룬 것과 대비된다. 특히 시스템 수준 이슈(asynchronous scheduling, heterogeneous deployment)까지 다룬 점이 차별화된다.

3. **실용적 관점**: 단순한 알고리즘 나열을 넘어, 실제 배포 시 고려해야 할 시스템 수준 이슈(스케줄링, KV cache, 배치 처리)까지 다루어 실무자에게도 유용하다. 각 기법의 적용 조건과 트레이드오프가 명확히 제시되어 있다.

4. **텍스트를 넘은 확장**: Auto-regressive 이미지 생성까지의 응용을 다루어, speculative decoding이 "LLM 기법"이 아닌 "auto-regressive 모델의 범용 가속 기법"임을 보여준다.

### Speculative Decoding의 근본적 한계

1. **수락률 의존성**: Speculative decoding의 효과는 draft 모델의 품질(수락률)에 강하게 의존한다. 수락률이 낮으면 가속 효과가 미미하거나 오히려 overhead가 될 수 있다. 특히 **창의적 생성**(높은 temperature)이나 **분포 외(out-of-distribution)** 입력에서는 수락률이 급격히 하락할 수 있다. Temperature가 높아질수록 target 분포의 엔트로피가 증가하여 draft 모델과의 불일치가 커진다.

2. **추가 메모리 비용**: 독립 draft 모델을 사용하는 경우, 추가 모델의 파라미터와 KV cache가 GPU 메모리를 점유한다. 이미 target 모델이 GPU 메모리의 대부분을 사용하는 상황(예: 70B 모델을 80GB GPU에서 실행)에서 7B draft 모델의 추가 메모리(약 14GB)는 심각한 제약이 될 수 있다. Self-drafting 방법(Medusa, EAGLE)이 이 문제를 완화하지만 완전히 해결하지는 못한다.

3. **Throughput vs. Latency 트레이드오프**: Speculative decoding은 주로 **latency**(단일 요청의 응답 시간)를 개선한다. 그러나 **throughput**(단위 시간당 처리 요청 수) 관점에서는, target 모델의 검증 단계에서 추가 연산이 필요하므로 반드시 개선되는 것은 아니다. 높은 배치 크기에서는 오히려 throughput이 감소할 수 있다. 이는 큰 배치에서 decode phase가 이미 compute-bound에 가까워져, speculative decoding의 기반이 되는 memory-bound 가정이 깨지기 때문이다.

4. **구현 복잡도**: Tree-based speculative decoding, 비동기 스케줄링 등 고급 기법은 구현이 복잡하고, 기존 서빙 인프라와의 통합이 어렵다. KV cache 관리, attention mask 처리, 배치 내 가변 길이 처리 등 많은 엔지니어링 과제가 있다. 버그 발생 시 디버깅도 어려워, 실전 배포의 진입 장벽이 높다.

5. **Draft 모델 학습/유지 비용**: Medusa, EAGLE 등은 target 모델에 특화된 학습이 필요하며, target 모델이 업데이트될 때마다 draft 모델도 재학습해야 한다. 이는 빈번한 모델 업데이트가 이루어지는 환경(예: 주 단위 fine-tuning)에서 운영 부담이 될 수 있다. 모델 버전 관리의 복잡도도 증가한다.

6. **Sampling 방식에 따른 효과 차이**: Greedy decoding에서는 높은 수락률을 달성하기 쉽지만, top-p/top-k sampling에서는 수락률이 하락한다. 특히 창의적 텍스트 생성이나 다양성이 중요한 응용에서는 가속 효과가 제한적이다.

### 향후 연구 방향

1. **Self-speculative Decoding 고도화**: 별도의 draft 모델 없이 target 모델 자체를 활용하는 방법(LayerSkip, Draft & Verify)의 효율성 향상. 메모리 추가 비용 없이 가속을 달성하는 것이 궁극적 목표이다. 모델 학습 시 speculative decoding을 위한 auxiliary loss를 추가하는 방향이 유망하다.

2. **적응적 전략**: 입력 난이도, 컨텍스트 길이, 하드웨어 상태에 따라 draft 길이, 트리 구조, 수락 기준을 **동적으로** 조절하는 meta-learning 기반 전략 연구. 입력의 각 부분별로 다른 전략을 적용하는 fine-grained adaptation도 연구되고 있다.

3. **Multimodal 확장**: 텍스트-이미지, 텍스트-오디오 등 multimodal auto-regressive 모델에 대한 speculative decoding 적용. 모달리티 간 토큰 분포의 차이를 고려한 새로운 draft 전략이 필요하다. GPT-4o 같은 통합 multimodal 모델에서의 speculative decoding은 아직 미탐구 영역이다.

4. **이론적 최적화**: 주어진 하드웨어 제약 하에서 최적의 draft 모델 크기, draft 길이, 트리 구조를 이론적으로 도출하는 연구. Sequoia가 트리 구조에 대해 이를 시작했으나, draft 모델 크기까지 포함한 전체적인 최적화 프레임워크는 아직 미흡하다.

5. **Long-context 특화**: 128K, 1M 토큰 이상의 초장문 컨텍스트에서의 speculative decoding 최적화. KV cache 관리와 draft 품질 유지가 핵심 과제이다. Sliding window attention과의 결합, sparse draft 모델 등이 연구되고 있다.

6. **MoE 모델과의 결합**: Mixture of Experts 모델에서는 활성화되는 파라미터가 동적으로 변하므로, draft 모델의 설계와 수락률 예측이 더 복잡해진다. MoE target 모델에 최적화된 speculative decoding 전략이 필요하다. 특히 MoE 모델은 토큰마다 다른 expert가 활성화되므로, draft 모델이 어떤 expert 조합이 사용될지까지 예측해야 한다는 추가적 어려움이 있다.

7. **Speculative Decoding의 이론적 하한**: 주어진 draft-target 모델 쌍에서 달성 가능한 최대 속도 향상의 이론적 상한을 분석하는 연구. 현재 기법들이 이 상한에 얼마나 가까운지 평가하고, 이론과 실전의 갭을 줄이는 방향의 연구가 필요하다.

8. **Privacy-preserving Speculative Decoding**: Draft 모델을 클라이언트 측에서 실행하고 target 모델을 서버에서 실행하는 시나리오에서, 사용자의 입력 프라이버시를 보호하면서도 speculative decoding의 가속 효과를 유지하는 방법. Homomorphic encryption이나 secure multi-party computation과의 결합이 탐구되고 있다.

## 실전 적용 가이드

이 서베이의 내용을 바탕으로, speculative decoding을 실전에 적용할 때의 의사결정 프레임워크를 정리한다.

### 기법 선택 기준

**상황 1: 빠르게 적용하고 싶을 때**
- Prompt Lookup Decoding이나 N-gram 기반 방법을 먼저 시도. 추가 학습이나 모델이 불필요하며, Hugging Face Transformers에서 몇 줄의 코드로 활성화 가능
- 반복적 패턴이 많은 도메인(코드, 템플릿)에서 1.5~2.5배 가속 기대

**상황 2: 최대 성능이 필요할 때**
- EAGLE 또는 EAGLE-2를 권장. 현재 lossless 기법 중 가장 높은 속도 향상(3~4배)을 달성
- Target 모델에 대한 추가 학습(수 시간)이 필요하지만, 한 번 학습하면 지속적으로 사용 가능

**상황 3: GPU 메모리가 부족할 때**
- Self-drafting 방법(Medusa, LayerSkip)을 사용. 추가 메모리가 거의 없음
- Medusa는 target 모델의 1~3% 수준의 추가 파라미터만 필요

**상황 4: 다양한 target 모델에 범용적으로 적용할 때**
- 독립 소형 모델 방식(SpecDec)이 적합. 동일 계열의 작은 모델이 이미 존재하면(Llama 7B → 70B) 추가 학습 없이 바로 사용 가능
- 또는 Lookahead Decoding으로 target 모델만으로 가속(단, greedy decoding만 지원)

### 성능 튜닝 팁

1. **Draft 길이 최적화**: 프로파일링을 통해 해당 환경에서의 최적 $\gamma$를 찾는다. 일반적으로 4~8이 적절하지만, 하드웨어와 모델에 따라 다르다
2. **수락률 모니터링**: 서비스 운영 중 수락률을 지속적으로 모니터링하여, 수락률이 하락하면 draft 모델 재학습 또는 전략 변경을 고려
3. **Temperature 조정**: 가능하다면 낮은 temperature를 사용하여 수락률을 높인다. Temperature 0에서 가장 높은 가속 효과
4. **배치 크기와의 균형**: 배치 크기가 커지면 speculative decoding의 효과가 줄어드므로, latency-sensitive 요청에만 선택적으로 적용하는 전략도 고려

## 결론

Speculative decoding은 LLM 추론의 메모리 바운드 병목을 해결하는 가장 유망한 접근법 중 하나이다. **출력 품질을 전혀 희생하지 않으면서** 2~3배 이상의 속도 향상을 달성할 수 있다는 점에서, 양자화나 pruning 같은 lossy 기법과는 근본적으로 다른 가치를 제공한다. 이론적 보장(분포 보존 정리)과 실용적 효과가 모두 입증된, LLM 추론 최적화의 핵심 기술이다.

이 서베이는 draft-then-verify 패러다임을 중심으로, draft 생성의 다양한 방법(retrieval, N-gram, auto-regressive, multi-token), 검증 전략(single-step, iterative), 구조적 확장(tree-based), 시스템 수준 최적화(asynchronous, heterogeneous scheduling)를 포괄적으로 정리하여, 이 빠르게 성장하는 분야의 전체 지형도를 제시한다. Generation-Refinement 프레임워크라는 통합 분류 체계를 통해, 겉보기에 다른 기법들이 공유하는 공통 구조를 드러낸 것이 이 서베이의 가장 큰 기여이다.

2024~2025년 현재, speculative decoding은 이미 주요 LLM 서비스에 실전 배포되어 있으며, EAGLE, Medusa, Sequoia 등의 진보된 기법들이 계속 등장하고 있다. 특히 self-speculative decoding과 하드웨어 인식 최적화 방향의 연구가 활발하며, auto-regressive 이미지 생성 등 새로운 도메인으로의 확장도 진행 중이다. vLLM, TensorRT-LLM, SGLang 등의 서빙 프레임워크가 speculative decoding을 기본 기능으로 제공하면서, 이 기술의 접근성도 크게 높아졌다.

LLM의 규모가 계속 커지고 실시간 응용이 늘어나는 현 상황에서, speculative decoding은 효율적 추론의 핵심 기술로서 그 중요성이 더욱 커질 것이다. Auto-regressive 모델이 존재하는 한 메모리 바운드 문제는 사라지지 않으며, speculative decoding은 이 근본적 문제에 대한 가장 우아한 해답을 제공한다. 이 서베이는 그 기술적 기반을 체계적으로 이해하기 위한 최선의 출발점이다.
