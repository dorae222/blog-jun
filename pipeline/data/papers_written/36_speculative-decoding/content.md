## 개요

대규모 언어 모델(LLM)의 자기회귀(autoregressive) 생성은 토큰을 하나씩 순차적으로 생성하기 때문에 추론 속도가 느립니다. 모델 크기가 커질수록 단일 포워드 패스(forward pass)의 지연이 증가하며, 이는 실시간 대화형 서비스에서 심각한 병목이 됩니다. GPT-3 175B 규모의 모델이 토큰 하나를 생성하는 데 수십 밀리초가 소요되고, 수백 토큰의 응답을 생성하려면 수초에서 수십 초가 걸리는 상황에서, 추론 지연을 줄이는 것은 LLM 상용화의 핵심 과제입니다.

Leviathan, Beck, Shazeer가 ICML 2023에서 발표한 **추측 디코딩(Speculative Decoding)**은 이 문제를 근본적으로 새로운 관점에서 접근합니다. 기존의 모델 압축(양자화, 증류, 가지치기)이 모델 품질을 희생하며 속도를 얻는 것과 달리, 추측 디코딩은 **대상 모델의 출력 분포를 수학적으로 완벽하게 보존하면서** 추론 속도를 2~3배 향상시킵니다.

![추측 디코딩의 핵심 개념: 표준 자기회귀 생성과 추측 디코딩의 비교](figures/architecture.png)
*추측 디코딩의 핵심 구조. 왼쪽의 표준 자기회귀 방식은 토큰마다 대상 모델의 포워드 패스가 필요하지만, 오른쪽의 추측 디코딩은 작은 초안 모델이 여러 토큰을 빠르게 생성한 뒤 대상 모델이 한 번의 포워드 패스로 병렬 검증한다. 수정된 거부 샘플링(Modified Rejection Sampling)을 통해 대상 모델과 동일한 출력 분포를 보장한다.*

이 논문의 핵심 통찰은 LLM 추론의 병목이 순수 연산량(FLOPs)이 아니라 **메모리 대역폭과 순차적 실행**에 있다는 점이며, GPU의 병렬 처리 능력을 활용하여 여러 토큰을 동시에 검증하면 사실상 추가 비용 없이 처리량을 높일 수 있다는 것입니다.

이 논문은 Google Research에서 발표되었으며, 같은 시기에 DeepMind에서도 독립적으로 유사한 아이디어를 제안(Chen et al., 2023)하여 추측 디코딩이 빠르게 LLM 서빙의 표준 기술로 자리잡는 계기가 되었습니다. 현재 vLLM, HuggingFace TGI, NVIDIA TensorRT-LLM 등 사실상 모든 주요 LLM 서빙 프레임워크에서 지원되는 핵심 기능으로, 학술적 기여뿐 아니라 산업적 영향력 측면에서도 LLM 추론 최적화 분야의 이정표가 된 연구입니다.

## 배경 및 문제

### 자기회귀 생성의 순차적 병목

트랜스포머 기반 LLM은 자기회귀 방식으로 텍스트를 생성합니다. 시퀀스 $x_1, x_2, \ldots, x_T$를 생성할 때, 각 토큰 $x_t$는 이전 모든 토큰 $x_{1:t-1}$에 조건부로 생성됩니다.

$$x_t \sim p(\cdot | x_1, x_2, \ldots, x_{t-1})$$

이 과정에서 $t$번째 토큰을 생성하려면 반드시 $t-1$번째 토큰까지 생성이 완료되어야 하므로, $T$개의 토큰을 생성하려면 최소 $T$번의 순차적 포워드 패스가 필요합니다. 이는 본질적으로 병렬화가 불가능한 순차적 의존성(sequential dependency)입니다.

학습(training) 단계에서는 교사 강제(teacher forcing)를 통해 모든 토큰의 손실을 병렬로 계산할 수 있지만, 추론(inference) 단계에서는 이전 토큰의 출력이 다음 토큰의 입력이 되므로 이러한 병렬화가 불가능합니다. 이 근본적인 비대칭성이 LLM 추론 최적화를 어렵게 만드는 핵심 요인입니다.

### 메모리 대역폭 제약 (Memory-Bound) 문제

LLM 추론이 느린 근본 원인은 연산량 부족이 아닙니다. 현대 GPU의 연산 능력과 메모리 대역폭 사이에는 심각한 불균형이 존재합니다. NVIDIA A100 GPU를 예로 들어 보겠습니다.

A100 GPU는 312 TFLOPS(FP16)의 연산 능력을 갖추고 있지만, HBM 대역폭은 약 2 TB/s에 불과합니다. 산술 강도(arithmetic intensity)의 관점에서 보면, 연산과 메모리 접근이 균형을 이루는 지점은 약 156 ops/byte입니다. 즉, 메모리에서 1바이트를 읽을 때마다 156회 이상의 연산을 수행해야 GPU 연산 유닛이 완전히 활용됩니다.

단일 토큰 생성 시의 산술 강도를 분석하면 이 불균형이 명확히 드러납니다. 70B 파라미터 모델의 가중치를 FP16으로 저장하면 약 140GB입니다. 토큰 하나를 생성할 때 이 가중치 전체를 HBM에서 읽어야 하므로, 가중치 로딩에만 다음과 같은 시간이 소요됩니다.

$$T_{\text{load}} = \frac{140 \text{ GB}}{2 \text{ TB/s}} = 70 \text{ ms}$$

반면 실제 행렬 연산은 GPU 코어에서 수 밀리초 내에 완료됩니다. 단일 토큰 생성에서의 산술 강도는 약 2 ops/byte로, 이론적 균형점인 156 ops/byte의 1.3%에 불과합니다. 즉, **GPU 연산 유닛의 약 98.7%가 메모리 로딩을 기다리며 유휴 상태**에 놓입니다.

이 관찰에서 핵심적인 통찰이 도출됩니다. 배치 크기를 1에서 $B$로 늘려도 가중치 로딩 시간은 동일합니다. 한 번 가중치를 읽은 뒤 $B$개의 입력에 대해 동시에 연산하면 되기 때문입니다. 산술 강도는 $B$배 증가하여 $2B$ ops/byte가 됩니다. $B \approx 78$일 때 비로소 연산과 메모리가 균형을 이루게 됩니다. 이것이 추측 디코딩의 이론적 기반입니다. **1개의 토큰을 검증하든 $\gamma$개의 토큰을 동시에 검증하든, 가중치 로딩이라는 지배적 비용은 거의 동일합니다.**

이를 수식으로 표현하면, 대상 모델의 포워드 패스 시간 $T_p$에 대해 $\gamma$개의 토큰을 동시에 검증하는 시간 $T_p(\gamma)$는 다음과 같이 근사됩니다.

$$T_p(\gamma) \approx T_p(1) + \epsilon(\gamma)$$

여기서 $\epsilon(\gamma)$는 추가적인 연산 오버헤드로, $\gamma$가 수십 이하인 범위에서는 $T_p(1)$에 비해 무시할 수 있을 정도로 작습니다.

### 기존 가속 방법의 한계

추론 가속을 위한 기존 접근법들은 각각 고유한 한계를 갖고 있습니다.

| 방법 | 원리 | 한계 |
|------|------|------|
| **양자화(Quantization)** | INT8/INT4로 가중치 압축 | 정밀도 손실, 극단적 양자화 시 perplexity 증가 |
| **지식 증류(Distillation)** | 큰 모델의 지식을 작은 모델로 전달 | 교사 모델의 능력 완전 전달 불가, long-tail 성능 차이 |
| **가지치기(Pruning)** | 불필요한 파라미터 제거 | 높은 압축률에서 성능 저하, 구조적/비구조적 트레이드오프 |
| **비자기회귀 생성(NAR)** | 모든 토큰 동시 생성 | 반복 토큰 문제, 토큰 간 의존성 무시로 인한 품질 저하 |

이 네 가지 방법 모두 **속도와 품질 사이의 교환(trade-off)**을 전제로 합니다. 추측 디코딩은 이 교환 관계 자체를 깨뜨리는 것이 핵심 차별점입니다.

## 핵심 아이디어

추측 디코딩의 핵심 아이디어는 두 가지 관찰에 기반합니다.

**관찰 1: 작은 모델과 큰 모델의 예측 일치.** 작은 "초안 모델(draft model)" $M_q$가 큰 "대상 모델(target model)" $M_p$와 상당 부분 일치하는 예측을 합니다. 특히 문맥이 분명한 토큰(관사, 전치사, 흔한 이어지는 단어 등)에서는 두 모델의 출력 분포가 매우 유사합니다. 예를 들어 "The capital of France is"라는 프롬프트에서 7B 모델과 70B 모델 모두 "Paris"에 95% 이상의 확률을 부여할 것이며, 이런 경우 작은 모델의 예측을 신뢰해도 무방합니다.

**관찰 2: 병렬 검증의 무료 점심.** GPU에서 여러 토큰을 동시에 검증하는 비용이 단일 토큰 검증과 거의 같습니다. 이는 앞서 설명한 메모리 대역폭 제약 때문입니다. 가중치를 한 번 메모리에서 읽은 후, 1개의 토큰에 대해 연산하든 8개의 토큰에 대해 연산하든 지배적인 비용(가중치 로딩)은 동일합니다.

이 두 관찰을 결합하면 다음과 같은 전략이 도출됩니다. 초안 모델로 $\gamma$개의 토큰을 빠르게 생성하고, 대상 모델이 이를 한 번의 포워드 패스로 동시에 검증하여, **대상 모델 1회 호출로 평균적으로 여러 토큰을 확정**할 수 있습니다. 그리고 거부 샘플링(rejection sampling)을 통해 이 과정이 대상 모델에서 직접 샘플링한 것과 **수학적으로 동일한 분포**를 보장합니다.

이 아이디어의 이름이 "추측(speculative)" 디코딩인 이유가 여기에 있습니다. 컴퓨터 아키텍처에서의 추측 실행(speculative execution)과 개념적으로 유사합니다. CPU가 분기 결과를 예측하여 미리 실행하고 예측이 틀리면 롤백하는 것처럼, 초안 모델이 다음 토큰들을 예측하여 미리 생성하고, 대상 모델이 틀린 예측을 거부하는 것입니다.

## 방법론

### 문제 정의

대상 모델 $M_p$의 조건부 분포를 $p(x_{t+1} | x_{1:t})$, 초안 모델 $M_q$의 조건부 분포를 $q(x_{t+1} | x_{1:t})$로 표기합니다. 두 모델은 동일한 어휘 $V$를 공유하지만, $M_p$는 $M_q$보다 훨씬 큰 모델입니다 (예: 70B vs 7B). 목표는 $p$로부터의 샘플링을 $q$의 도움으로 가속하되, 최종 출력 분포가 $p$와 정확히 일치하도록 하는 것입니다.

공식적으로, 추측 디코딩 알고리즘 $\mathcal{A}$가 생성하는 토큰 시퀀스의 분포가 다음을 만족해야 합니다.

$$\forall t, \forall x: \quad P_{\mathcal{A}}(x_t = x | x_{1:t-1}) = p(x | x_{1:t-1})$$

### 추측 디코딩 알고리즘

![추측 디코딩의 단계별 동작 예시: 수용된 토큰(녹색), 거부된 토큰(빨간색), 보정 토큰(파란색)](figures/fig_1.png)
*추측 디코딩의 실제 동작 예시. 각 줄은 알고리즘의 한 이터레이션을 나타낸다. 녹색 토큰은 초안 모델(6M 파라미터)이 제안하여 대상 모델(97M 파라미터)이 수용한 것이고, 빨간색은 거부된 제안, 파란색은 보정 분포에서 새로 샘플링된 토큰이다. 예를 들어 첫 번째 줄에서는 대상 모델이 단 1회만 실행되었지만 5개 토큰이 생성되었다.*

알고리즘은 세 단계로 구성됩니다.

**단계 1: 초안 생성 (Draft Generation)**

초안 모델 $M_q$를 사용하여 $\gamma$개의 토큰을 자기회귀적으로 생성합니다.

$$\tilde{x}_{n+1} \sim q(\cdot | x_{1:n}), \quad \tilde{x}_{n+2} \sim q(\cdot | x_{1:n}, \tilde{x}_{n+1}), \quad \ldots, \quad \tilde{x}_{n+\gamma} \sim q(\cdot | x_{1:n+\gamma-1})$$

$M_q$가 $M_p$보다 훨씬 작으므로 이 과정은 매우 빠릅니다. 예를 들어 7B 모델의 포워드 패스는 70B 모델보다 약 10배 빠르므로, $\gamma$개의 초안 토큰을 생성하는 비용은 대상 모델 1회 포워드 패스 비용의 $\gamma / 10$ 정도에 불과합니다.

**단계 2: 병렬 검증 (Parallel Verification)**

프롬프트 $x_{1:n}$과 초안 토큰 $\tilde{x}_{n+1}, \ldots, \tilde{x}_{n+\gamma}$를 연결하여 대상 모델 $M_p$에 한 번에 입력합니다. KV 캐시를 활용하면 실제로 계산해야 하는 것은 $\gamma$개의 새 토큰 위치뿐입니다. 이 단일 포워드 패스로 $\gamma+1$개의 조건부 분포를 동시에 얻습니다.

$$p(\cdot | x_{1:n}), \; p(\cdot | x_{1:n}, \tilde{x}_{n+1}), \; \ldots, \; p(\cdot | x_{1:n}, \tilde{x}_{n+1}, \ldots, \tilde{x}_{n+\gamma})$$

트랜스포머의 인과적 마스킹(causal masking) 덕분에, 이 $\gamma+1$개의 분포가 단일 포워드 패스에서 자연스럽게 계산됩니다. 위치 $i$에서의 출력은 위치 $1$부터 $i$까지의 입력에만 의존하므로, 모든 위치의 출력을 동시에 얻을 수 있습니다.

**단계 3: 거부 샘플링을 통한 토큰 확정 (Token Acceptance via Rejection Sampling)**

각 초안 토큰 $\tilde{x}_{n+i}$에 대해 순서대로 수용 여부를 판정합니다. 균일 분포 $u \sim \text{Uniform}(0, 1)$에서 난수를 추출한 뒤, 다음 조건으로 판정합니다.

$$\text{수용 조건: } u < \min\left(1, \frac{p(\tilde{x}_{n+i} | x_{1:n+i-1})}{q(\tilde{x}_{n+i} | x_{1:n+i-1})}\right)$$

직관적으로, 대상 모델이 초안 모델보다 해당 토큰에 더 높은 확률을 부여하면($p \geq q$) 항상 수용합니다. 대상 모델이 더 낮은 확률을 부여하면($p < q$) 확률 $p/q$로 수용합니다. 이는 고전적인 거부 샘플링(rejection sampling) 기법의 적용입니다.

첫 번째로 거부되는 위치를 $k$라 하면:
- 위치 $1$부터 $k-1$까지의 토큰은 확정됩니다.
- 위치 $k$에서는 **보정 분포(adjusted distribution)**로부터 새 토큰을 샘플링합니다.

$$x_{n+k} \sim \text{norm}\left(\max\left(0, \; p(\cdot | x_{1:n+k-1}) - q(\cdot | x_{1:n+k-1})\right)\right)$$

여기서 $\text{norm}(\cdot)$은 확률 분포가 되도록 정규화하는 연산입니다. 이 보정 분포는 대상 모델의 분포 $p$에서 초안 모델이 이미 "커버한" 부분 $q$를 제거한 잔차(residual) 분포로 해석할 수 있습니다.

모든 $\gamma$개 토큰이 수용되면, 추가로 한 토큰을 $p(\cdot | x_{1:n+\gamma})$에서 보너스로 샘플링합니다. 따라서 **한 라운드에서 최소 1개, 최대 $\gamma + 1$개의 토큰이 확정**됩니다.

### 분포 동등성 증명

**정리**: 위 알고리즘으로 생성된 각 토큰의 한계 분포(marginal distribution)는 대상 모델 $M_p$에서 직접 샘플링한 분포와 동일합니다.

**증명**: 특정 위치에서 토큰 $x$가 최종 선택될 총 확률을 계산합니다. 토큰 $x$가 선택되는 경로는 두 가지입니다.

**경로 1** (초안 토큰이 수용): 초안 모델이 $x$를 생성할 확률 $q(x)$와 이를 수용할 확률 $\min(1, p(x)/q(x))$의 곱입니다.

$$P_1(x) = q(x) \cdot \min\left(1, \frac{p(x)}{q(x)}\right) = \min(q(x), p(x))$$

**경로 2** (초안 토큰이 거부된 후 보정 분포에서 샘플링): 어떤 토큰 $x'$가 생성되어 거부될 확률의 합은 다음과 같습니다.

$$P_{\text{reject}} = \sum_{x' \in V} q(x') \cdot \max\left(0, 1 - \frac{p(x')}{q(x')}\right) = \sum_{x' \in V} \max(0, q(x') - p(x'))$$

거부 후 보정 분포에서 $x$를 뽑을 확률은 $\frac{\max(0, p(x) - q(x))}{\sum_{x'} \max(0, p(x') - q(x'))}$입니다.

분모를 정리하면 $\sum_{x'} \max(0, p(x') - q(x')) = \sum_{x'} \max(0, q(x') - p(x')) = P_{\text{reject}}$가 됩니다. 이 등식은 $\sum_{x'} p(x') = \sum_{x'} q(x') = 1$이라는 확률 분포의 정규화 조건에서 도출됩니다.

따라서:

$$P_2(x) = P_{\text{reject}} \cdot \frac{\max(0, p(x) - q(x))}{P_{\text{reject}}} = \max(0, p(x) - q(x))$$

두 경로를 합산하면:

$$P(x) = P_1(x) + P_2(x) = \min(p(x), q(x)) + \max(0, p(x) - q(x)) = p(x)$$

마지막 등식은 임의의 실수 $a, b$에 대해 $\min(a, b) + \max(0, a - b) = a$라는 항등식에서 도출됩니다. $a \geq b$일 때 $\min(a,b) = b$이고 $\max(0, a-b) = a-b$이므로 합은 $a$, $a < b$일 때 $\min(a,b) = a$이고 $\max(0, a-b) = 0$이므로 합 역시 $a$입니다. $\square$

이 증명이 중요한 이유는, 추측 디코딩이 단순한 근사가 아니라 **정확히 동일한 분포**를 보장한다는 것을 의미하기 때문입니다. 어떤 평가 지표(perplexity, BLEU, ROUGE, 인간 평가 등)로 측정하더라도 차이가 발생할 수 없습니다.

### 예상 수용 길이 분석

한 라운드에서 수용되는 토큰 수의 기대값은 초안 모델과 대상 모델의 분포 유사도에 의해 결정됩니다. 위치별 평균 수용률을 $\alpha$로 정의하면:

$$\alpha = \mathbb{E}_{x \sim q}\left[\min\left(1, \frac{p(x)}{q(x)}\right)\right] = \sum_{x \in V} \min(p(x), q(x))$$

이는 두 분포 $p$와 $q$ 사이의 **총 변이 거리(Total Variation Distance)**와 직접적으로 관련됩니다.

$$\alpha = 1 - \text{TV}(p, q) = 1 - \frac{1}{2}\sum_{x \in V} |p(x) - q(x)|$$

$\gamma$개의 초안 토큰에 대해, 위치 $i$에서의 수용 여부가 독립적이라고 가정하면(실제로는 약한 의존성이 있지만 근사적으로 성립), 수용되는 토큰 수의 기대값은 기하 분포(geometric distribution)로 모델링됩니다.

$$E[\text{수용 토큰 수}] = \frac{1 - \alpha^{\gamma+1}}{1 - \alpha}$$

![수용률(alpha)과 초안 길이(gamma)에 따른 이터레이션당 기대 생성 토큰 수](figures/fig_2.png)
*수용률 $\alpha$와 초안 길이 $\gamma$에 따른 이터레이션당 기대 생성 토큰 수. $\alpha$가 높을수록(두 모델이 유사할수록), $\gamma$가 클수록 한 라운드에 더 많은 토큰이 확정되어 속도 향상이 커진다. $\alpha = 0.9$, $\gamma = \infty$일 때 기대 토큰 수는 10에 달한다.*

$\alpha \to 1$이면(두 모델이 거의 동일하면) 이 값은 $\gamma + 1$에 근접합니다. 즉, 거의 모든 초안 토큰이 수용되어 보너스 토큰까지 포함하면 한 라운드에 $\gamma + 1$개의 토큰이 확정됩니다. 반대로 $\alpha \to 0$이면 이 값은 1에 근접하여, 한 라운드에 1개의 토큰만 확정됩니다(초안 생성 비용이 낭비됨).

### 속도 향상 비율의 이론적 분석

대상 모델의 단일 포워드 패스 시간을 $T_p$, 초안 모델의 단일 포워드 패스 시간을 $T_q$, 병렬 검증의 추가 오버헤드를 무시하면, 한 라운드의 소요 시간은 $\gamma \cdot T_q + T_p$이고 생성되는 토큰 수의 기대값은 $\frac{1 - \alpha^{\gamma+1}}{1 - \alpha}$입니다.

토큰당 평균 시간은:

$$\text{시간/토큰}_{\text{spec}} = \frac{\gamma \cdot T_q + T_p}{\frac{1 - \alpha^{\gamma+1}}{1 - \alpha}}$$

비용 비율 $c = T_q / T_p$를 정의하면, 속도 향상 비율은 다음과 같이 정리됩니다.

$$\text{Speedup} = \frac{T_p}{\text{시간/토큰}_{\text{spec}}} = \frac{\frac{1 - \alpha^{\gamma+1}}{1 - \alpha}}{\gamma \cdot c + 1}$$

이 식에서 다음과 같은 통찰을 얻을 수 있습니다:

1. **$c$가 작을수록** (초안 모델이 상대적으로 빠를수록) 분모가 작아져 속도 향상이 커집니다. 이상적으로 $c \to 0$이면 $\text{Speedup} \to \frac{1 - \alpha^{\gamma+1}}{1 - \alpha}$입니다.
2. **$\alpha$가 클수록** (두 모델이 유사할수록) 분자가 커져 속도 향상이 커집니다. $\alpha = 1$이면 $\text{Speedup} = \frac{\gamma + 1}{\gamma c + 1}$입니다.
3. **$c = 0$이고 $\alpha = 1$인 이상적 경우**: $\text{Speedup} = \gamma + 1$로, 초안 길이에 비례하는 속도 향상을 얻습니다.

### 최적 초안 길이 선택

$\gamma$가 너무 작으면 병렬 검증의 이점을 충분히 활용하지 못하고, 너무 크면 후반부 토큰의 거부 확률이 높아져 초안 생성에 소비한 시간이 낭비됩니다. 논문은 $\gamma$의 최적값을 수용률 $\alpha$와 비용 비율 $c$의 함수로 도출합니다.

속도 향상 비율을 $\gamma$에 대해 미분하고 0으로 놓으면 최적 $\gamma^*$를 구할 수 있습니다. 해석적 해는 복잡하지만, 근사적으로 다음과 같은 경향을 보입니다.

- $\alpha$가 높은 경우 (예: 0.9): $\gamma^* \approx 8 \sim 12$
- $\alpha$가 중간인 경우 (예: 0.7): $\gamma^* \approx 4 \sim 6$
- $\alpha$가 낮은 경우 (예: 0.5): $\gamma^* \approx 2 \sim 3$

다음 그래프는 수용률 $\alpha$와 비용 비율 $c$에 따른 최적 $\gamma$ 값을 시각적으로 보여줍니다.

![수용률(alpha)과 비용 비율(c)에 따른 최적 초안 길이(gamma) 그래프](figures/fig_3.png)
*Figure 3: 수용률 $\alpha$와 비용 비율 $c$에 따른 최적 초안 길이 $\gamma^*$. 비용 비율 $c$가 낮을수록(초안 모델이 상대적으로 빠를수록) 더 긴 초안 길이가 최적이 되며, 수용률이 높아질수록 최적 $\gamma$가 급격히 증가한다. (Leviathan et al., 2023)*

논문에서는 대부분의 실험에서 $\gamma = 4 \sim 8$이 최적으로 나타났습니다. 실질적으로는 태스크와 입력에 따라 $\alpha$가 변동하므로, 적응적으로 $\gamma$를 조절하는 전략도 가능합니다. 일부 후속 연구(SpecInfer, Medusa 등)에서는 최근 수용률의 이동 평균을 추적하여 $\gamma$를 동적으로 조정하는 방식을 구현하였습니다.

## 실험 결과

### 주요 벤치마크 결과

논문은 다양한 모델 크기와 태스크에서 추측 디코딩의 효과를 검증하였습니다.

| 대상 모델 | 초안 모델 | 태스크 | 수용률 $\alpha$ | 속도 향상 | 품질 변화 |
|----------|----------|-------|----------------|----------|----------|
| Chinchilla 70B | Chinchilla 7B | 텍스트 생성 | 0.75~0.85 | 2.1~3.0x | 동일 |
| T5-XXL (11B) | T5-Small (60M) | 번역 | 0.70~0.80 | 2.0~2.5x | 동일 |
| T5-XXL (11B) | T5-Small (60M) | 요약 | 0.65~0.75 | 1.8~2.3x | 동일 |
| PaLM 540B | PaLM 62B | 텍스트 생성 | 0.70~0.80 | 2.0~2.2x | 동일 |

품질 변화가 모두 "동일"인 것은 우연이 아니라, 앞서 증명한 분포 동등성의 직접적 결과입니다. 어떤 다운스트림 평가에서도 성능 저하가 원리적으로 발생할 수 없습니다.

### 태스크별 수용률 분석

수용률 $\alpha$는 태스크의 예측 가능성에 따라 크게 달라집니다.

- **코드 생성** ($\alpha$ 높음, 2.5~3.0x): 프로그래밍 언어의 구문이 규칙적이므로 초안 모델의 예측이 거의 완벽합니다. 특히 함수 시그니처, 반복문, 조건문 등의 정형화된 패턴에서 수용률이 매우 높습니다.
- **번역** ($\alpha$ 중간, 2.0~2.5x): 소스 언어가 강한 제약을 제공하므로 중간 수준의 수용률을 보입니다.
- **자유 형식 텍스트 생성** ($\alpha$ 낮음, 1.5~2.0x): 창의적 글쓰기처럼 다음 토큰의 불확실성이 높은 태스크에서는 수용률이 상대적으로 낮습니다.
- **문서 요약** ($\alpha$ 가변적): 추출적 요약에 가까울수록 $\alpha$가 높고, 생성적 요약에서는 낮아집니다.

### 속도 향상과 연산량의 관계

![수용률(alpha)과 초안 길이(gamma)에 따른 속도 향상 비율 및 산술 연산 증가량](figures/fig_4.png)
*수용률 $\alpha$와 초안 길이 $\gamma$에 따른 속도 향상 비율(실선)과 산술 연산 증가량(점선). 핵심적인 관찰은 산술 연산이 증가하더라도 wall-clock 속도는 향상된다는 점이다. $\gamma$가 클수록 연산은 많이 증가하지만, $\alpha$가 충분히 높으면(0.7 이상) 속도 향상이 연산 증가를 상쇄하고도 남는다. 이는 LLM 추론이 연산이 아닌 메모리 대역폭에 의해 제약됨을 실험적으로 입증한다.*

이 그래프에서 주목할 점은 실선(속도 향상)과 점선(연산량 증가)의 상반된 경향입니다. $\gamma = 10$일 때 산술 연산은 약 5~6배 증가하지만, $\alpha = 0.9$에서는 wall-clock 속도가 오히려 약 3배 빨라집니다. 이는 추측 디코딩이 "더 많은 연산을 하되, 순차적 단계를 줄여서 전체 시간을 단축한다"는 전략임을 보여줍니다.

### 초안 길이에 따른 속도 변화

$\gamma$ 값에 따른 실험 결과는 다음과 같습니다 (Chinchilla 70B / 7B 기준, $\alpha \approx 0.8$).

| 초안 길이 $\gamma$ | 평균 수용 토큰 | 라운드당 시간 | 토큰당 시간 | 속도 향상 |
|---|---|---|---|---|
| 1 | 1.8 | 1.1$T_p$ | 0.61$T_p$ | 1.6x |
| 4 | 3.4 | 1.4$T_p$ | 0.41$T_p$ | 2.4x |
| 8 | 4.8 | 1.8$T_p$ | 0.38$T_p$ | 2.6x |
| 16 | 5.5 | 2.6$T_p$ | 0.47$T_p$ | 2.1x |

$\gamma = 4 \sim 8$ 구간에서 최적 성능이 관찰되며, $\gamma = 16$에서는 초안 생성 비용 대비 추가 수용 토큰이 적어 오히려 속도가 감소합니다. 이는 기하급수적으로 감소하는 수용 확률($\alpha^{\gamma}$)과 선형적으로 증가하는 초안 비용($\gamma \cdot T_q$) 사이의 균형에서 비롯됩니다.

아래 트레이스 다이어그램은 표준 디코딩과 추측 디코딩($\gamma=3$, $\gamma=7$)의 wall-clock 시간을 직관적으로 비교합니다. 초안 모델($M_q$, 파란색)의 실행 시간이 대상 모델($M_p$, 보라색)에 비해 매우 짧기 때문에, $\gamma$가 증가해도 전체 라운드 시간의 증가는 미미한 반면 대상 모델 호출 횟수가 크게 줄어드는 것을 확인할 수 있습니다.

![인코더-디코더 트랜스포머에서 표준 디코딩과 추측 디코딩의 실행 시간 비교 트레이스 다이어그램](figures/fig_5.png)
*Figure 5: 인코더-디코더 트랜스포머의 실행 시간 트레이스 다이어그램. 상단은 $\gamma=7$의 추측 디코딩으로, 대상 모델(보라색) 호출 사이에 초안 모델(파란색)이 7번 실행된다. 중간은 $\gamma=3$, 하단은 표준 디코딩이다. 표준 디코딩 대비 대상 모델의 순차적 호출 횟수가 크게 줄어들어 전체 wall-clock 시간이 단축됨을 시각적으로 확인할 수 있다. (Leviathan et al., 2023)*

### 온도(Temperature)에 따른 영향

샘플링 온도가 수용률에 미치는 영향도 분석되었습니다. 온도가 낮을수록 (greedy에 가까울수록) 두 모델의 분포가 모두 sharp해지면서 수용률이 높아집니다. 반대로 온도가 높으면 분포가 평탄해지면서 두 모델 간의 차이가 커지고 수용률이 낮아집니다. 온도 0(greedy decoding)에서는 수용률이 가장 높아 속도 향상이 극대화되지만, 이 경우 거부 샘플링이 아닌 단순 비교(초안 토큰이 argmax와 일치하는지 확인)로 단순화됩니다.

### 품질 검증

추측 디코딩의 출력이 대상 모델의 직접 출력과 분포적으로 동일함을 실험적으로도 확인하였습니다. 1,000개의 프롬프트에 대해 각각 추측 디코딩과 직접 샘플링으로 다수의 응답을 생성한 뒤, 토큰 단위 분포의 KL 발산(KL Divergence)을 측정한 결과 통계적으로 유의미한 차이가 관찰되지 않았습니다. 구체적으로 양측 검정(two-sided test)에서 $p$-value가 0.05를 크게 초과하여, 두 분포가 동일하다는 귀무가설을 기각할 수 없었습니다.

## 의의 및 한계

### 의의

**무손실 가속의 달성.** 추측 디코딩의 가장 큰 의의는 품질-속도 교환 관계를 깨뜨렸다는 점입니다. 양자화, 증류, 가지치기와 같은 기존 방법들은 모두 일정 수준의 품질 저하를 전제로 하지만, 추측 디코딩은 수학적으로 동일한 출력을 보장합니다. 이는 의료, 법률, 금융 등 출력 품질이 절대적으로 중요한 분야에서 특히 가치 있습니다.

**실용적 적용 용이성.** 대상 모델이나 초안 모델을 재학습하거나 수정할 필요가 없습니다. 기존에 배포된 모델 체크포인트를 그대로 사용할 수 있어, 프로덕션 환경에 즉시 적용 가능합니다. 또한 양자화, 증류 등의 기존 최적화와 직교적(orthogonal)이므로, 이들과 함께 적용하여 누적 속도 향상을 얻을 수 있습니다.

**LLM 서빙 프레임워크 통합.** vLLM, HuggingFace TGI, NVIDIA TensorRT-LLM 등 주요 LLM 서빙 시스템에 표준 기능으로 통합되었습니다. 특히 vLLM에서는 `--speculative-model` 플래그 하나로 활성화할 수 있어 사용 편의성이 뛰어납니다.

**후속 연구의 촉발.** 이 논문은 다양한 후속 연구의 이론적 토대가 되었습니다.

| 후속 연구 | 핵심 아이디어 | 차별점 |
|----------|-------------|-------|
| **Medusa** (Cai et al., 2024) | 단일 모델에 여러 예측 헤드 부착 | 별도 초안 모델 불필요 |
| **Eagle** (Li et al., 2024) | 모델 중간 레이어에서 자기 초안 생성 | 추가 메모리 최소화 |
| **SpecInfer** (Miao et al., 2024) | 트리 구조 초안으로 더 많은 후보 검증 | 한 라운드에서 탐색 범위 확대 |
| **Lookahead Decoding** (Fu et al., 2024) | Jacobi 반복법 활용 | 초안 모델 자체 불필요 |
| **Draft & Verify** (Zhang et al., 2024) | n-gram 매칭 활용 | 신경망 초안 모델 대체 |

### 한계

**초안 모델 의존성.** 효과적인 초안 모델의 선택이 성능에 결정적 영향을 미칩니다. 초안 모델이 대상 모델과 너무 다르면 수용률이 낮아 이득이 줄어들고, 너무 크면 초안 생성 비용이 증가합니다. 이상적으로는 대상 모델과 동일한 학습 데이터로 훈련된 작은 모델이 최적이지만, 이런 모델이 항상 존재하지는 않습니다.

**메모리 오버헤드.** 대상 모델과 초안 모델을 동시에 GPU 메모리에 적재해야 하므로, 메모리가 제한된 환경에서는 적용이 어렵습니다. 예를 들어 70B 대상 모델과 7B 초안 모델을 모두 FP16으로 A100 80GB에 올리려면 약 154GB가 필요하여 최소 2개의 GPU가 필요합니다. 이 문제는 Medusa나 Eagle처럼 별도 초안 모델이 불필요한 후속 방식으로 부분적으로 해결됩니다.

**배치 추론에서의 제한.** 추측 디코딩은 주로 단일 요청의 지연 시간(latency)을 줄이는 데 효과적입니다. 대용량 배치 처리 환경에서는 이미 GPU 활용률이 높아 추가적인 병렬화 여지가 적습니다. 배치 크기가 충분히 크면 메모리 대역폭이 아닌 연산(compute)이 병목이 되므로, 추측 디코딩의 전제 조건인 "메모리 바운드" 상황이 성립하지 않을 수 있습니다.

**가변적 속도 향상.** 태스크와 입력에 따라 속도 향상 폭이 크게 달라집니다. 예측 가능성이 높은 입력에서는 3배 가속이 가능하지만, 불확실성이 높은 입력에서는 1.2~1.5배에 그칠 수 있습니다. 최악의 경우 초안 생성 오버헤드로 인해 속도가 오히려 미세하게 감소할 수도 있으며, 이러한 변동성은 서비스 수준 목표(SLO) 설정을 어렵게 만듭니다.

**KV 캐시 관리의 복잡성.** 거부된 토큰 이후의 KV 캐시 항목을 무효화해야 하므로, KV 캐시 관리 로직이 복잡해집니다. [[paged-attention|PagedAttention]]과 같은 메모리 관리 기법과의 통합 시 추가적인 엔지니어링이 필요합니다.

## 코드 예제

추측 디코딩의 핵심 알고리즘을 PyTorch 스타일의 의사 코드(pseudocode)로 구현하면 다음과 같습니다.

```python
import torch
import torch.nn.functional as F

def speculative_decode(
    target_model,   # 대상 모델 M_p (큰 모델)
    draft_model,    # 초안 모델 M_q (작은 모델)
    input_ids,      # 초기 프롬프트 토큰 [batch, seq_len]
    gamma=5,        # 초안 길이
    temperature=1.0,
    max_new_tokens=100,
):
    """
    추측 디코딩 알고리즘 구현.
    대상 모델의 출력 분포를 정확히 보존하면서 추론을 가속합니다.
    """
    generated = input_ids.clone()
    num_generated = 0

    while num_generated < max_new_tokens:
        # === 단계 1: 초안 생성 ===
        draft_tokens = []    # 초안 토큰 저장
        draft_probs = []     # 초안 모델의 확률 분포 저장
        draft_input = generated.clone()

        for _ in range(gamma):
            with torch.no_grad():
                logits = draft_model(draft_input).logits[:, -1, :]
            probs = F.softmax(logits / temperature, dim=-1)
            token = torch.multinomial(probs, num_samples=1)
            draft_tokens.append(token)
            draft_probs.append(probs)
            draft_input = torch.cat([draft_input, token], dim=-1)

        draft_tokens = torch.cat(draft_tokens, dim=-1)  # [batch, gamma]

        # === 단계 2: 병렬 검증 ===
        # 초안 토큰을 모두 포함한 시퀀스를 대상 모델에 입력
        verify_input = torch.cat([generated, draft_tokens], dim=-1)
        with torch.no_grad():
            target_logits = target_model(verify_input).logits

        # 검증 대상 위치의 확률 분포 추출
        n = generated.shape[-1]
        target_probs = [
            F.softmax(target_logits[:, n + i - 1, :] / temperature, dim=-1)
            for i in range(gamma + 1)
        ]

        # === 단계 3: 거부 샘플링 ===
        accepted_count = 0
        for i in range(gamma):
            token = draft_tokens[:, i]
            p_x = target_probs[i].gather(-1, token.unsqueeze(-1)).squeeze(-1)
            q_x = draft_probs[i].gather(-1, token.unsqueeze(-1)).squeeze(-1)

            # 수용 확률 계산: min(1, p(x) / q(x))
            accept_prob = torch.clamp(p_x / q_x, max=1.0)
            u = torch.rand_like(accept_prob)

            if (u < accept_prob).all():
                # 수용: 이 토큰을 확정
                accepted_count += 1
            else:
                # 거부: 보정 분포에서 새 토큰 샘플링
                adjusted = F.relu(target_probs[i] - draft_probs[i])
                adjusted = adjusted / adjusted.sum(dim=-1, keepdim=True)
                new_token = torch.multinomial(adjusted, num_samples=1)
                generated = torch.cat(
                    [generated, draft_tokens[:, :i], new_token], dim=-1
                )
                num_generated += i + 1
                break
        else:
            # 모든 초안 토큰이 수용됨 -> 보너스 토큰 추가
            bonus_token = torch.multinomial(
                target_probs[gamma], num_samples=1
            )
            generated = torch.cat(
                [generated, draft_tokens, bonus_token], dim=-1
            )
            num_generated += gamma + 1

    return generated
```

vLLM에서 추측 디코딩을 활용하는 실제 사용 예시는 다음과 같습니다.

```python
from vllm import LLM, SamplingParams

# vLLM에서 추측 디코딩 활성화
llm = LLM(
    model="meta-llama/Llama-3.1-70B-Instruct",
    speculative_model="meta-llama/Llama-3.1-8B-Instruct",
    num_speculative_tokens=5,   # gamma 값
    tensor_parallel_size=4,     # 70B 모델을 위한 텐서 병렬화
)

sampling_params = SamplingParams(
    temperature=0.7,
    top_p=0.9,
    max_tokens=512,
)

prompts = [
    "Explain the theory of relativity in simple terms.",
    "Write a Python function to sort a list.",
]

outputs = llm.generate(prompts, sampling_params)
for output in outputs:
    print(output.outputs[0].text)
```

HuggingFace Transformers에서의 활용 예시도 살펴보겠습니다.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# 대상 모델과 초안 모델 로드
target_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-70B-Instruct",
    device_map="auto",
    torch_dtype="auto",
)
draft_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct",
    device_map="auto",
    torch_dtype="auto",
)
tokenizer = AutoTokenizer.from_pretrained(
    "meta-llama/Llama-3.1-70B-Instruct"
)

prompt = "The future of artificial intelligence is"
input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to("cuda")

# assistant_model 파라미터로 추측 디코딩 활성화
outputs = target_model.generate(
    input_ids,
    assistant_model=draft_model,
    max_new_tokens=200,
    do_sample=True,
    temperature=0.7,
)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

위 코드에서 HuggingFace의 `generate` 메서드는 `assistant_model` 파라미터가 지정되면 자동으로 추측 디코딩을 수행합니다. 내부적으로 초안 생성, 병렬 검증, 거부 샘플링의 전체 과정이 투명하게 처리됩니다.

수용률 $\alpha$를 모니터링하는 유틸리티 코드도 실무에서 유용합니다.

```python
def compute_acceptance_rate(target_probs, draft_probs):
    """
    두 분포 간의 토큰별 수용률 alpha를 계산합니다.
    alpha = sum_x min(p(x), q(x))
    """
    alpha = torch.min(target_probs, draft_probs).sum(dim=-1)
    return alpha.mean().item()

def estimate_speedup(alpha, gamma, cost_ratio):
    """
    이론적 속도 향상 비율을 추정합니다.

    Args:
        alpha: 평균 수용률 (0 ~ 1)
        gamma: 초안 길이
        cost_ratio: T_q / T_p (초안 모델 비용 / 대상 모델 비용)

    Returns:
        예상 속도 향상 비율
    """
    expected_tokens = (1 - alpha ** (gamma + 1)) / (1 - alpha)
    round_cost = gamma * cost_ratio + 1
    return expected_tokens / round_cost

# 사용 예시
alpha = 0.8
for gamma in [2, 4, 6, 8, 12, 16]:
    speedup = estimate_speedup(alpha, gamma, cost_ratio=0.1)
    expected = (1 - alpha ** (gamma + 1)) / (1 - alpha)
    print(
        f"gamma={gamma:2d}: "
        f"E[tokens]={expected:.2f}, "
        f"speedup={speedup:.2f}x"
    )
```

## 관련 문서

- [[paged-attention|Efficient Memory Management for Large Language Model Serving with PagedAttention]] -- LLM 서빙 최적화
- [[flash-attention|FlashAttention]] -- 추론 가속 관련 기법
- [[mixtral|Mixtral of Experts]] -- 효율적 모델 아키텍처
