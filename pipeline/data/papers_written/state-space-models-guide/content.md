# State Space Models: S4에서 Mamba까지

## 개요

State Space Models(SSM)은 Transformer의 이차(O(n^2)) 복잡도 한계를 극복하기 위해 등장한 선형(O(n)) 복잡도 시퀀스 모델링 아키텍처입니다. 제어 이론과 신호 처리에서 유래한 상태 공간 모델을 딥러닝에 접목하여, 긴 시퀀스를 효율적으로 처리하면서도 Transformer에 버금가는 성능을 목표로 합니다.

2021년 [S4](/post/s4)의 등장으로 시작된 SSM 연구는 2023년 [Mamba](/post/mamba)를 통해 실질적인 경쟁력을 갖추게 되었고, 현재 Transformer와의 하이브리드 아키텍처가 활발히 연구되고 있습니다.

### 왜 SSM이 중요한가?

Transformer의 Self-Attention은 시퀀스 길이에 대해 O(n^2) 복잡도를 가집니다. 100만 토큰 이상의 긴 컨텍스트를 처리해야 하는 현대 AI에서 이는 심각한 병목이 됩니다. SSM은 O(n) 복잡도로 이론적으로 무한한 시퀀스를 처리할 수 있으며, 추론 시 상수 메모리만으로 동작할 수 있습니다. Transformer의 대안으로서, 그리고 Transformer와의 상호보완적 결합으로서 SSM의 중요성은 계속 커지고 있습니다.

---

## 핵심 흐름: SSM 기술 발전 타임라인

### Phase 1: 이론적 기초 (2021-2022)

연속 시간 상태 공간 모델을 딥러닝에 적용하는 이론적 토대가 마련된 시기입니다.

**State Space Model의 기본 원리**

SSM은 연속 시간 선형 동역학 시스템에서 출발합니다.

```
h'(t) = A·h(t) + B·x(t)    (상태 방정식)
y(t) = C·h(t) + D·x(t)     (출력 방정식)
```

여기서 A는 상태 전이 행렬, B는 입력 행렬, C는 출력 행렬입니다. 이를 이산화(discretization)하여 시퀀스 모델로 변환합니다.

**핵심 모델들**

- [S4 (Structured State Spaces for Sequence Modeling)](/post/s4) (2021): SSM의 이론적 돌파구. HiPPO 초기화로 장기 의존성 문제 해결. 구조화된 행렬(대각 + 저랭크)로 효율적 계산. Long Range Arena(LRA) 벤치마크에서 Transformer를 압도하는 성능.

- [H3 (Hungry Hungry Hippos)](/post/h3) (2022): S4를 언어 모델링에 최적화. 두 개의 SSM 레이어 사이에 곱셈적 상호작용 삽입. Attention 없이도 언어 모델링에서 경쟁력 있는 성능.

- [Hyena](/post/hyena) (2023): Attention을 긴 합성곱으로 대체하는 접근. 암묵적(implicit) 합성곱 필터 학습. Sub-quadratic 복잡도.

### Phase 2: Mamba — SSM의 실질적 돌파 (2023)

- [Mamba](/post/mamba) (2023): SSM에 **선택적 메커니즘(Selective Mechanism)**을 도입. 입력에 따라 B, C, Δ 파라미터가 동적으로 변화. 하드웨어 최적화된 선택적 스캔(Selective Scan) 알고리즘. 1.4B 파라미터에서 Transformer와 동등한 언어 모델링 성능. 시퀀스 길이에 대해 선형 스케일링으로 100만 토큰 이상 처리 가능.

Mamba의 핵심 혁신은 기존 SSM의 **시불변(time-invariant)** 제약을 제거한 것입니다. 기존 S4는 A, B, C 행렬이 입력과 무관하게 고정되어 있어 내용 기반 추론(content-based reasoning)에 한계가 있었습니다. Mamba는 이를 입력에 의존하는 **시변(time-varying)** 파라미터로 확장하여, Attention과 유사한 선택적 정보 처리를 O(n) 복잡도로 구현했습니다.

### Phase 3: 하이브리드 아키텍처와 확장 (2024)

SSM과 Transformer를 결합하여 양쪽의 장점을 취하는 하이브리드 아키텍처가 등장했습니다.

- [Mamba-2](/post/mamba-2) (2024): **State Space Duality (SSD)** 발견. SSM과 Semi-Separable 행렬, 특정 형태의 Attention이 수학적으로 동치임을 증명. 이를 통해 Tensor Core 활용이 가능해져 Mamba 대비 2-8배 속도 향상. 더 큰 상태 차원(64→128+)으로 표현력 증가.

- [Jamba](/post/jamba) (2024): AI21 Labs의 SSM-Transformer 하이브리드. Mamba 레이어 + Attention 레이어 + MoE를 결합. 52B 파라미터, 12B 활성화. 256K 토큰 컨텍스트. 단일 80GB GPU에서 동작 가능한 효율성.

- [Jamba 1.6](/post/jamba-1-6) (2024): Jamba의 확장. 대규모 모델에서도 하이브리드의 효율성 유지.

### Phase 4: Linear Attention과 RNN 부활 (2023-현재)

SSM과 함께 Linear Attention, 새로운 형태의 RNN도 활발히 연구되고 있습니다. 이들은 모두 O(n) 복잡도로 시퀀스를 처리한다는 공통점이 있습니다.

**Linear Attention 계열**

- [GLA (Gated Linear Attention)](/post/gla) (2024): 게이팅 메커니즘을 가진 선형 어텐션. 하드웨어 효율적인 청크 기반 학습 알고리즘. Mamba와 비교할 만한 성능.

- [Gated DeltaNet](/post/gated-deltanet) (2024): Delta Rule 기반 선형 어텐션. 키-값 연관 메모리를 효율적으로 업데이트.

**RNN 부활**

- [RWKV](/post/rwkv) (2023): RNN과 Transformer의 장점을 결합. WKV(Weighted Key-Value) 메커니즘. Transformer 수준 성능을 RNN의 효율성으로 달성.

- [RWKV-7](/post/rwkv-7) (2024): 상태 진화 규칙 개선. 더 강력한 컨텍스트 모델링.

- [xLSTM](/post/xlstm) (2024): LSTM의 현대화. 지수 게이팅(Exponential Gating)과 행렬 메모리(Matrix Memory). sLSTM(스칼라)과 mLSTM(행렬) 두 가지 변형.

- [RetNet](/post/retnet) (2023): Retentive Network. 학습 시 병렬 처리, 추론 시 순환 처리. 학습-추론의 불가능한 삼각관계(impossible triangle) 해결 시도.

**기타 효율적 아키텍처**

- [HGRN](/post/hgrn) (2023): Hierarchically Gated Recurrent Network. 계층적 게이팅으로 다양한 시간 스케일 모델링.

- [Griffin](/post/griffin) (2024): Google DeepMind의 Recurrence + Attention 하이브리드. Local Attention + RG-LRU(Real-Gated Linear Recurrent Unit).

### Phase 5: 최신 발전 (2025-)

- [Mamba-3](/post/mamba-3) (2025): Mamba 아키텍처의 지속적 발전. 더 큰 규모에서의 검증과 개선.

---

## 주요 SSM/Linear 모델 요약 테이블

| 모델 | 연도 | 복잡도 | 핵심 기여 | 유형 |
|------|------|--------|----------|------|
| [S4](/post/s4) | 2021 | O(n) | HiPPO, 구조화된 SSM | SSM |
| [H3](/post/h3) | 2022 | O(n) | 언어 모델링용 SSM | SSM |
| [Hyena](/post/hyena) | 2023 | O(n log n) | 암묵적 합성곱 | Convolution |
| [RWKV](/post/rwkv) | 2023 | O(n) | RNN-Transformer 결합 | RNN |
| [RetNet](/post/retnet) | 2023 | O(n) | Retention 메커니즘 | Hybrid |
| [Mamba](/post/mamba) | 2023 | O(n) | 선택적 SSM | SSM |
| [GLA](/post/gla) | 2024 | O(n) | 게이트 선형 어텐션 | Linear Attn |
| [Mamba-2](/post/mamba-2) | 2024 | O(n) | SSD, Tensor Core 활용 | SSM |
| [Jamba](/post/jamba) | 2024 | O(n) | SSM-Attn-MoE 하이브리드 | Hybrid |
| [xLSTM](/post/xlstm) | 2024 | O(n) | LSTM 현대화 | RNN |
| [RWKV-7](/post/rwkv-7) | 2024 | O(n) | 개선된 상태 진화 | RNN |
| [Griffin](/post/griffin) | 2024 | O(n) | RG-LRU + Local Attn | Hybrid |
| [Gated DeltaNet](/post/gated-deltanet) | 2024 | O(n) | Delta Rule 선형 어텐션 | Linear Attn |
| [Mamba-3](/post/mamba-3) | 2025 | O(n) | 대규모 SSM 검증 | SSM |

---

## SSM의 핵심 개념

### 1. Transformer vs SSM: 근본적 차이

| 특성 | Transformer | SSM |
|------|------------|-----|
| 복잡도 | O(n^2) | O(n) |
| 메모리 | O(n) KV 캐시 | O(1) 상수 상태 |
| 추론 | KV 캐시 누적 | 상태 업데이트 |
| 학습 | 완전 병렬 | 합성곱/스캔 |
| 장기 의존성 | 직접 접근 | 상태 압축 |
| 내용 기반 추론 | 강함 (Attention) | Mamba부터 가능 |

### 2. S4와 Mamba의 구체적 비교

S4와 Mamba는 SSM의 두 중요한 이정표이며, 근본적인 설계 철학의 차이가 있습니다.

**S4의 핵심 혁신: HiPPO 초기화**

S4는 상태 전이 행렬 $A$를 HiPPO(High-order Polynomial Projection Operator) 행렬로 초기화합니다. HiPPO 행렬은 입력 시퀀스를 다항식 기저 위에 최적 투영하도록 설계되어, 이론적으로 무한한 과거 입력을 유한한 상태 벡터에 압축할 수 있습니다:

$$A_{nk} = -\begin{cases} (2n+1)^{1/2}(2k+1)^{1/2} & \text{if } n > k \\ n+1 & \text{if } n = k \\ 0 & \text{if } n < k \end{cases}$$

이 초기화 덕분에 S4는 Long Range Arena(LRA) 벤치마크에서 Path-X 태스크(시퀀스 길이 16,384)를 최초로 해결한 모델이 되었습니다.

**Mamba의 핵심 혁신: 선택적 메커니즘**

Mamba는 S4의 시불변(time-invariant) 제약을 제거하고, 입력에 따라 SSM 파라미터를 동적으로 결정합니다:

```
S4 (시불변):  h_t = A · h_{t-1} + B · x_t     (A, B 고정)
Mamba (시변): h_t = A(x_t) · h_{t-1} + B(x_t) · x_t  (A, B가 입력 의존)
```

구체적으로, Mamba는 입력 $x_t$로부터 $B$, $C$, $\Delta$(이산화 스텝)를 선형 투영으로 결정합니다:

$$B_t = \text{Linear}_B(x_t), \quad C_t = \text{Linear}_C(x_t), \quad \Delta_t = \text{softplus}(\text{Linear}_\Delta(x_t))$$

**S4 vs Mamba 상세 비교:**

| 비교 항목 | S4 | Mamba |
|-----------|-----|-------|
| 파라미터 구조 | 시불변 (A, B, C 고정) | 시변 (B, C, Δ 입력 의존) |
| 초기화 | HiPPO 행렬 | 학습 기반 |
| 학습 방법 | FFT 기반 합성곱 | Selective Scan (GPU 최적화) |
| 추론 방법 | 순환 모드 | 순환 모드 |
| LRA 성능 | 86.1% (평균) | 미해당 (언어 중심) |
| 언어 모델링 | 제한적 | GPT3급 (1.4B) |
| 하드웨어 효율 | 보통 | FlashAttention급 커널 |
| In-context Learning | 어려움 | 가능 |
| 복사/검색 태스크 | 실패 | 성공 |

:::info
S4가 실패한 복사(copying) 태스크에서 Mamba가 성공한 이유는 선택적 메커니즘에 있습니다. "어떤 토큰을 기억하고 어떤 토큰을 무시할지"를 입력 내용에 따라 결정하는 능력은, Attention의 핵심 기능인 "관련 정보에 집중"하는 것을 O(n) 복잡도로 근사한 것입니다.
:::

### 3. SSM의 이중 모드 (Dual Mode)

SSM의 핵심 강점 중 하나는 학습과 추론에서 서로 다른 모드로 동작할 수 있다는 점입니다.

- **학습 시 (합성곱 모드)**: 전체 시퀀스를 한 번에 처리. 병렬 계산 가능. GPU 효율적.
- **추론 시 (순환 모드)**: 토큰을 하나씩 처리. 상수 메모리. 긴 시퀀스에서도 일정한 비용.

이 이중성은 [Mamba-2](/post/mamba-2)의 **State Space Duality**에서 이론적으로 정리되었습니다.

합성곱 모드에서 SSM의 출력은 다음과 같이 계산됩니다:

$$y = x * \bar{K}, \quad \text{where } \bar{K} = (C\bar{B},\ C\bar{A}\bar{B},\ C\bar{A}^2\bar{B},\ \ldots)$$

여기서 $\bar{A}, \bar{B}$는 이산화된 SSM 파라미터이고, $*$는 합성곱 연산입니다. FFT를 사용하면 이 합성곱을 $O(n \log n)$ 복잡도로 수행할 수 있습니다.

순환 모드에서는 다음과 같이 상태를 업데이트합니다:

$$h_t = \bar{A} \cdot h_{t-1} + \bar{B} \cdot x_t, \quad y_t = C \cdot h_t$$

이 모드는 $O(1)$ 메모리로 동작하므로, 아무리 긴 시퀀스도 일정한 비용으로 추론할 수 있습니다.

### 4. 선형 어텐션(Linear Attention)과의 관계

SSM과 선형 어텐션은 표면적으로 다르지만 수학적으로 깊은 연관이 있습니다. [Mamba-2](/post/mamba-2)의 State Space Duality(SSD)가 이 연결을 형식화했습니다.

**Standard Attention:**

$$\text{Attn}(Q, K, V) = \text{softmax}(QK^\top / \sqrt{d}) \cdot V$$

**Linear Attention:**

$$\text{LinAttn}(Q, K, V) = \phi(Q) \cdot (\phi(K)^\top V)$$

여기서 $\phi$는 커널 특성 맵(kernel feature map)입니다. 우항의 괄호를 먼저 계산하면 복잡도가 $O(n \cdot d^2)$로 줄어들어 시퀀스 길이에 선형입니다.

**SSM과 Linear Attention의 대응 관계:**

| 요소 | SSM | Linear Attention |
|------|-----|-----------------|
| 상태 | $h_t \in \mathbb{R}^{N}$ | $S_t = \sum_{i \leq t} \phi(k_i) v_i^\top$ |
| 상태 업데이트 | $h_t = A h_{t-1} + B x_t$ | $S_t = S_{t-1} + \phi(k_t) v_t^\top$ |
| 출력 | $y_t = C h_t$ | $y_t = \phi(q_t)^\top S_t$ |
| 감쇠(decay) | $A$ 행렬 (정보 망각) | 없음 (기본) / 게이팅 (GLA) |

핵심 차이는 **감쇠 메커니즘**입니다. SSM의 $A$ 행렬은 오래된 정보를 점진적으로 망각하는 역할을 하며, Linear Attention에서는 [GLA](/post/gla)의 게이팅이 이에 대응합니다. [Gated DeltaNet](/post/gated-deltanet)은 Delta Rule을 통해 키-값 연관 메모리를 더 정밀하게 업데이트합니다.

:::tip
SSM, Linear Attention, RNN은 모두 "고정 크기 상태를 유지하면서 시퀀스를 순차 처리"한다는 공통 구조를 가집니다. 이들의 차이는 상태 업데이트 규칙과 출력 계산 방식에 있으며, Mamba-2의 SSD 프레임워크는 이를 통합적으로 이해할 수 있게 합니다.
:::

### 5. 벤치마크 비교

#### Long Range Arena (LRA)

LRA는 장기 의존성 모델링 능력을 평가하는 벤치마크로, 시퀀스 길이 1K-16K의 6개 태스크로 구성됩니다:

| 모델 | ListOps | Text | Retrieval | Image | Path | Path-X | 평균 |
|------|---------|------|-----------|-------|------|--------|------|
| Transformer | 36.4 | 64.3 | 57.5 | 42.4 | 71.4 | FAIL | 53.7 |
| Linear Trans. | 16.1 | 65.9 | 53.1 | 42.3 | 75.3 | FAIL | 50.5 |
| S4 | 58.4 | 76.0 | 87.1 | 88.7 | 94.2 | 96.4 | 83.5 |
| H3 | 57.0 | 78.0 | 81.0 | 88.0 | 92.0 | - | 79.2 |
| Hyena | 55.0 | 78.5 | 83.5 | 89.0 | 93.5 | - | 79.9 |

S4는 Transformer가 완전히 실패하는 Path-X(16K 길이)에서도 96.4%의 정확도를 달성했습니다.

#### 언어 모델링 (Pile 데이터셋)

| 모델 | 파라미터 | PPL | 학습 토큰 | 비고 |
|------|---------|-----|----------|------|
| GPT-3 (125M) | 125M | 32.0 | 300B | AR Transformer |
| H3 (125M) | 125M | 34.5 | 300B | SSM |
| Mamba (130M) | 130M | 32.2 | 300B | Selective SSM |
| Mamba (370M) | 370M | 24.4 | 300B | Selective SSM |
| Mamba (1.4B) | 1.4B | 16.4 | 300B | Selective SSM |
| GPT-3 (1.3B) | 1.3B | 16.7 | 300B | AR Transformer |

Mamba는 1.4B 규모에서 GPT-3(1.3B)와 동등하거나 약간 나은 퍼플렉시티를 달성하면서도, 추론 시 5배 높은 처리량을 보였습니다.

#### 추론 효율성 비교

| 모델 | 시퀀스 길이 8K | 시퀀스 길이 64K | 시퀀스 길이 256K | 메모리 |
|------|--------------|---------------|-----------------|--------|
| Transformer | 1x (기준) | 16x 느림 | OOM | O(n) KV 캐시 |
| Mamba | 1x | 1x | 1x | O(1) 상태 |
| Jamba | 1x | ~2x 느림 | ~4x 느림 | O(n) 일부 Attn |

:::warning
벤치마크 수치는 논문 발표 시점 기준이며, 구현 최적화와 하드웨어에 따라 달라질 수 있습니다. 특히 Flash Attention과 같은 최적화가 적용된 Transformer는 실무에서 이론적 O(n^2)보다 훨씬 효율적으로 동작합니다.
:::

### 6. 선택적 메커니즘의 중요성

기존 SSM(S4)은 **시불변(time-invariant)** 시스템으로, 모든 입력에 동일한 필터를 적용했습니다. 이는 장기 의존성 모델링에는 좋지만, "이 토큰은 기억하고 저 토큰은 무시하라"는 **내용 기반 선택**이 불가능했습니다.

[Mamba](/post/mamba)의 선택적 메커니즘은 입력에 따라 B, C, Δ를 동적으로 결정하여 이 한계를 극복했습니다. 이는 Attention의 "어디에 집중할지 선택"하는 능력을 O(n) 복잡도로 근사한 것으로 볼 수 있습니다.

### 7. 하이브리드가 최적인 이유

순수 SSM은 정확한 토큰 매칭(exact token recall)과 같은 태스크에서 Transformer에 뒤처지는 경향이 있습니다. 반면 Transformer는 긴 시퀀스에서 메모리와 계산 비용이 급증합니다.

[Jamba](/post/jamba)와 같은 하이브리드 아키텍처는 대부분의 레이어를 SSM으로 구성하고, 일부 레이어에만 Attention을 사용하여 양쪽의 장점을 취합니다.

구체적으로 Jamba의 구조는 다음과 같습니다:

- **총 80개 레이어** 중 7:1 비율로 Mamba:Attention 배치
- **MoE(Mixture of Experts)** 통합으로 활성 파라미터 절감
- 결과: 52B 총 파라미터, 12B 활성화, 256K 컨텍스트

이 설계가 효과적인 이유는, 대부분의 레이어에서는 SSM의 O(n) 효율을 누리면서, 핵심 레이어에서만 Attention을 사용하여 정확한 매칭이 필요한 능력을 보전할 수 있기 때문입니다.

---

## 추천 학습 경로

### 초심자 (SSM 입문)

SSM의 기본 원리와 핵심 모델을 이해합니다.

1. Transformer의 한계 이해 — O(n^2) 복잡도, KV 캐시 문제
2. [S4](/post/s4) — SSM의 이론적 기초 (HiPPO, 구조화된 행렬)
3. [Mamba](/post/mamba) — 선택적 메커니즘의 이해
4. [Jamba](/post/jamba) — SSM-Transformer 하이브리드의 실제 적용

### 중급 (이론 심화)

SSM의 수학적 기초와 다양한 변형을 깊이 학습합니다.

1. [H3](/post/h3) — 언어 모델링에서의 SSM
2. [Mamba-2](/post/mamba-2) — State Space Duality 이론
3. [RetNet](/post/retnet) — Retention 메커니즘
4. [GLA](/post/gla) + [Gated DeltaNet](/post/gated-deltanet) — Linear Attention 변형
5. [RWKV](/post/rwkv) + [RWKV-7](/post/rwkv-7) — RNN 기반 접근
6. [xLSTM](/post/xlstm) — LSTM의 현대화

### 고급 (최신 연구)

최전선의 SSM 연구를 추적합니다.

1. [Mamba-3](/post/mamba-3) — 최신 SSM 발전
2. [Griffin](/post/griffin) — Google의 하이브리드 접근
3. [Jamba 1.6](/post/jamba-1-6) — 대규모 하이브리드 모델
4. [Hyena](/post/hyena) + [HGRN](/post/hgrn) — 대안적 접근법
5. SSM의 멀티모달 확장과 비전 응용

---

## SSM의 미래 전망

SSM은 여전히 활발한 연구 분야입니다. 주요 연구 방향은 다음과 같습니다.

1. **더 큰 규모에서의 검증**: Mamba를 100B+ 규모로 확장한 결과 검증
2. **하이브리드 최적화**: SSM-Attention 비율의 최적화
3. **멀티모달 확장**: 비전, 오디오 등 다양한 모달리티에 SSM 적용
4. **하드웨어 최적화**: SSM에 특화된 하드웨어 설계와 커널 최적화
5. **이론적 이해**: SSM과 Attention의 표현력 차이에 대한 이론적 분석

---

## 관련 카테고리

- [AI/ML 아키텍처 로드맵](/post/ai-ml-architecture-roadmap) — 전체 AI/ML 지형도
- [LLM 핵심 논문 가이드](/post/llm-paper-guide) — SSM이 도전하는 LLM 영역
- [AI 핵심 기법 총정리](/post/ai-core-techniques-guide) — Attention, Flash Attention 등 관련 기법
