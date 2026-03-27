## 개요

Transformer의 Self-Attention은 시퀀스 길이 $N$에 대해 $O(N^2)$의 시간 및 메모리 복잡도를 가집니다. 이는 긴 시퀀스를 처리할 때 심각한 병목이 됩니다. Albert Gu와 Tri Dao(2023)가 발표한 **Mamba**는 **선택적 상태 공간(Selective State Space)**을 도입하여 이 문제를 해결합니다. 입력 데이터에 따라 SSM 파라미터가 동적으로 변화하여, 관련 정보를 선택적으로 기억하고 불필요한 정보를 필터링할 수 있습니다.

Mamba는 발표 직후 Semantic Scholar 기준 5,000회 이상의 인용(이 중 893회는 highly influential citation)을 기록하며, Transformer의 대안으로서 SSM의 가능성을 입증한 기념비적 연구입니다. 이후 Mamba-2(2024), Mamba-3(2026)으로 발전하며, Jamba, Zamba 등 하이브리드 아키텍처 연구를 촉발했습니다.

본 논문의 핵심 기여는 세 가지로 요약할 수 있습니다.

1. **선택 메커니즘(Selection Mechanism)**: SSM 파라미터를 입력의 함수로 만들어 내용 기반 추론(content-based reasoning)을 가능하게 했습니다. 기존 LTI(Linear Time-Invariant) SSM이 모든 시점에서 동일한 파라미터를 적용하는 것과 달리, 입력 토큰의 의미에 따라 $B_t, C_t, \Delta_t$가 동적으로 결정됩니다.
2. **하드웨어 효율적 병렬 스캔 알고리즘**: 시간 변이(time-varying) 파라미터로 인해 FFT 기반 컨볼루션이 불가능해진 문제를, 결합 법칙(associativity)을 활용한 병렬 접두사 스캔과 GPU 메모리 계층 최적화로 해결했습니다.
3. **간결한 통합 아키텍처**: Transformer의 MHA(Multi-Head Attention)와 FFN(Feed-Forward Network)을 단일 Mamba 블록으로 통합하여, 동일 파라미터 수에서 약 2배 깊은 네트워크를 구성할 수 있게 했습니다.

---

## 배경 및 문제

### Transformer의 이차 스케일링 문제

Transformer는 2017년 "Attention Is All You Need" 이후 자연어 처리, 컴퓨터 비전, 오디오 등 거의 모든 시퀀스 모델링 분야를 지배해 왔습니다. 그 핵심인 Self-Attention은 시퀀스 내 모든 토큰 쌍 간의 관계를 직접 계산합니다:

$$\text{Attn}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

여기서 $QK^T \in \mathbb{R}^{N \times N}$ 행렬을 구성해야 하므로, $O(N^2 D)$의 시간 복잡도와 $O(N^2)$의 메모리 복잡도가 발생합니다. 시퀀스 길이가 1K에서 64K로 64배 증가하면 어텐션의 계산량은 $64^2 = 4{,}096$배 증가합니다.

추론 단계에서도 병목이 존재합니다. Autoregressive 생성 시 Transformer는 이전 모든 토큰의 Key-Value를 **KV 캐시**에 저장해야 하며, 이는 시퀀스 길이에 비례하는 $O(N \cdot d_{\text{head}} \cdot n_{\text{heads}} \cdot n_{\text{layers}})$의 메모리를 소비합니다. 128K 토큰 컨텍스트를 가진 대규모 모델에서는 KV 캐시만으로 수십 GB의 GPU 메모리가 필요합니다.

### Sub-Quadratic 모델의 시도와 한계

이차 복잡도를 줄이기 위해 다양한 접근이 시도되었지만, 각각 근본적인 한계를 가집니다:

- **Linear Attention**: $\text{softmax}(QK^T)$를 커널 함수 $\phi(Q)\phi(K)^T$로 근사하여 $O(ND^2)$를 달성하지만, softmax의 비선형성을 잃어 성능이 크게 저하됩니다.
- **Sparse Attention** (Longformer, BigBird): 어텐션 패턴을 국소적으로 제한하지만, 전역적 의존성 포착에 한계가 있습니다.
- **Flash Attention**: IO 효율성을 개선하여 실제 속도를 높이지만, 근본적인 $O(N^2)$ 복잡도 자체는 변하지 않습니다.

### 상태 공간 모델(SSM)의 발전

상태 공간 모델은 제어 이론에서 유래한 시퀀스 모델링 프레임워크입니다. SSM 계열의 발전 과정은 다음과 같습니다:

| 모델 | 연도 | 핵심 기여 |
|------|------|-----------|
| **HiPPO** | 2020 | 직교 다항식 기반 상태 초기화 ( 긴 시퀀스 역사를 수학적 최적 방식으로 압축 |
| **LSSL** | 2021 | HiPPO를 딥러닝 프레임워크에 통합하는 최초 시도 |
| **S4** | 2021 | 구조화된 SSM으로 Long Range Arena에서 Transformer를 최초 능가 |
| **S4D, S5, H3, Hyena** | 2022-23 | 대각화, 다중 헤드, 암묵적 컨볼루션 등 다양한 변형 |

그러나 S4를 포함한 기존 SSM들은 **시간 불변(LTI)** 파라미터를 사용합니다. 즉, 상태 전이 행렬 $A$, 입력 행렬 $B$, 출력 행렬 $C$가 입력에 관계없이 고정됩니다. 이 LTI 속성 덕분에 재귀 연산을 **전역 컨볼루션**으로 변환하여 FFT로 $O(N \log N)$ 병렬 계산이 가능하지만, 수학적으로 **선형 어텐션과 동치**이며, 입력 내용에 따라 동적으로 처리할 수 없다는 근본적 한계를 갖습니다. 저자들은 이를 "내용 인식(content-awareness)의 부재"라고 표현합니다.

---

## 핵심 아이디어

### 선택적 상태 공간 (Selective State Spaces)

Mamba의 핵심은 SSM에 **선택성(selectivity)**을 부여하는 것입니다. 기존 SSM이 모든 입력을 동일한 가중치로 처리하는 것과 달리, Mamba는 입력에 따라 SSM 파라미터($B, C, \Delta$)를 동적으로 조절합니다. 이를 통해 **관련 정보는 기억하고 무관한 정보는 무시**하는 내용 기반 필터링이 가능합니다.

저자들은 선택성의 필요성을 두 가지 합성 태스크로 논증합니다.

**선택적 복사(Selective Copy) 태스크** ) 입력 시퀀스에서 유효한 토큰만 골라 출력하는 과제입니다:

```
입력: [A, B, 0, 0, C, 0, D] (0은 노이즈)
목표: [A, B, C, D]          (관련 토큰만 선택)
```

시간 불변 SSM은 모든 시점에서 동일한 $\bar{A}, \bar{B}$가 적용되므로 노이즈 토큰과 유효 토큰을 구별할 수 없어 실패합니다.

**유도 헤드(Induction Head) 태스크** ( 시퀀스 내에서 특정 패턴이 반복될 때 이전 패턴의 다음 토큰을 예측하는 과제입니다. 예를 들어 "...AB...A"가 주어지면 "B"를 예측해야 합니다. 이는 in-context learning의 기본 메커니즘으로, 내용 기반의 조건부 추론 능력이 필요합니다.

Mamba는 두 태스크 모두에서 시퀀스 길이 $2^{12} = 4{,}096$까지 완벽한 정확도를 달성하며, 선택성이 SSM의 표현력을 근본적으로 확장함을 실증합니다.

### 선택성과 압축의 트레이드오프

저자들은 시퀀스 모델의 효율성을 **압축(compression)**의 관점에서 분석합니다:

| 모델 | 컨텍스트 표현 | 압축 수준 | 정보 접근 |
|------|--------------|----------|----------|
| **Attention** | 전체 KV 캐시 저장 | 압축 없음 ($O(N)$ 메모리) | 임의 토큰 직접 접근 |
| **LTI SSM** | 고정 크기 상태 벡터 | 균일 압축 | 간접 접근 (정보 손실) |
| **Mamba** | 고정 크기 상태 벡터 | **선택적 압축** | 간접 접근 (정보 밀도 극대화) |

선택 메커니즘은 "어떤 정보를 상태에 유지하고 어떤 정보를 버릴 것인가"를 입력 내용에 기반하여 결정함으로써, 고정 크기 상태의 정보 밀도를 극대화합니다. 이것이 Mamba가 $O(1)$ 추론 메모리로도 Transformer에 필적하는 성능을 달성할 수 있는 핵심 원리입니다.

---

## 방법론

### 연속 상태 공간 모델

기본 SSM은 선형 ODE(상미분방정식)로 정의됩니다:

$$h'(t) = A h(t) + B x(t)$$
$$y(t) = C h(t) + D x(t)$$

여기서 $h(t) \in \mathbb{R}^N$은 숨겨진 상태, $x(t) \in \mathbb{R}$은 입력 신호, $y(t) \in \mathbb{R}$은 출력입니다. 각 행렬의 역할은 다음과 같습니다:

- $A \in \mathbb{R}^{N \times N}$: **상태 전이 행렬** ) 이전 상태가 다음 상태에 미치는 영향을 결정
- $B \in \mathbb{R}^{N \times 1}$: **입력 행렬** ( 새로운 입력이 상태에 기록되는 방식을 결정
- $C \in \mathbb{R}^{1 \times N}$: **출력 행렬** ) 상태에서 출력을 읽어내는 방식을 결정
- $D$: 스킵 연결로 구현되며, 핵심 분석에서는 생략

직관적으로, SSM은 입력 신호 $x(t)$를 $N$차원 숨겨진 상태 $h(t)$를 거쳐 출력 $y(t)$로 변환하는 선형 동적 시스템입니다.

### 이산화 (Discretization)

연속 모델을 이산 시퀀스에 적용하기 위해 ZOH(Zero-Order Hold) 이산화를 적용합니다. 타임스텝 크기 $\Delta$를 사용하여 연속 파라미터 $(A, B)$를 이산 파라미터 $(\bar{A}, \bar{B})$로 변환합니다:

$$\bar{A} = \exp(\Delta A)$$
$$\bar{B} = (\Delta A)^{-1}(\exp(\Delta A) - I) \cdot \Delta B \approx \Delta B$$

근사 $\bar{B} \approx \Delta B$는 $\Delta$가 충분히 작을 때 (Euler 이산화와 일치) 성립합니다. 이산화된 SSM의 재귀식은 다음과 같습니다:

$$h_t = \bar{A} h_{t-1} + \bar{B} x_t$$
$$y_t = C h_t$$

시간 불변 SSM에서는 $\bar{A}, \bar{B}$가 모든 시점에서 동일하므로, 재귀식을 전개하면 출력이 입력과 커널 $\bar{K}$의 **전역 컨볼루션**으로 표현됩니다:

$$\bar{K} = (C\bar{B},\; C\bar{A}\bar{B},\; C\bar{A}^2\bar{B},\; \ldots,\; C\bar{A}^{L-1}\bar{B})$$
$$y = x * \bar{K}$$

이 컨볼루션은 FFT를 사용하여 $O(N \log N)$에 병렬 계산할 수 있지만, LTI 속성에 의존하므로 파라미터가 시간에 따라 변하면 적용할 수 없습니다.

### 선택 메커니즘 (Selection Mechanism)

Mamba의 핵심 혁신은 $B, C, \Delta$를 **입력 $x$의 함수**로 만드는 것입니다. 이를 통해 SSM이 S4의 6개 파라미터를 가진다는 의미에서 **S6(Selective S4, 혹은 Selective Structured State Space)**이라 명명합니다:

$$B_t = s_B(x_t) = \text{Linear}_N(x_t) \in \mathbb{R}^{B \times L \times N}$$
$$C_t = s_C(x_t) = \text{Linear}_N(x_t) \in \mathbb{R}^{B \times L \times N}$$
$$\Delta_t = s_\Delta(x_t) = \text{softplus}\!\left(\text{Linear}_1(x_t) + \text{broadcast}(\text{Parameter})\right) \in \mathbb{R}^{B \times L \times D}$$

여기서 $s_B, s_C$는 입력을 $N$차원으로 투영하는 선형 변환이며, $s_\Delta$는 $D$차원에서 랭크-1 투영($D \to 1 \to D$) 후 softplus 활성화를 적용합니다. **$A$ 행렬만 입력 독립적으로 유지**하여 HiPPO 초기화의 이점을 보존합니다.

#### $\Delta_t$의 역할: 선택적 게이팅

$\Delta_t$는 이산화 공식을 통해 입력 토큰의 **"중요도 게이트"**로 기능합니다. 이산화 수식에 $\Delta_t$를 대입하면:

$$\bar{A}_t = \exp(\Delta_t A), \quad \bar{B}_t \approx \Delta_t B_t$$

이로부터 두 가지 극단적 동작이 도출됩니다:

| $\Delta_t$ 값 | $\bar{A}_t$ | $\bar{B}_t$ | 동작 | 직관적 의미 |
|:---:|:---:|:---:|:---|:---|
| **큼** | $\approx 0$ | $\approx \Delta_t B_t$ (큼) | 이전 상태 리셋, 현재 입력 강하게 반영 | "이 토큰은 중요하다 ( 기억하라" |
| **작음** | $\approx I$ | $\approx 0$ | 이전 상태 유지, 현재 입력 무시 | "이 토큰은 무시하라 ) 기존 상태를 지켜라" |

이는 RNN의 게이트 메커니즘과 깊은 연관이 있습니다. 실제로 저자들은 $\Delta_t$가 LSTM의 forget gate와 수학적으로 유사하며, $B_t$와 $C_t$가 각각 input gate와 output gate에 대응함을 보입니다. 그러나 LSTM과 달리 SSM 프레임워크에서 동작하므로 병렬 스캔이 가능하다는 결정적 차이가 있습니다.

연결 관계를 수식으로 정리하면:

$$\underbrace{h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t}_{\text{Mamba (선택적 SSM)}} \quad \longleftrightarrow \quad \underbrace{h_t = f_t \odot h_{t-1} + i_t \odot \tilde{h}_t}_{\text{LSTM (게이트 RNN)}}$$

여기서 $\bar{A}_t \leftrightarrow f_t$ (forget gate), $\bar{B}_t \leftrightarrow i_t$ (input gate), $C_t \leftrightarrow o_t$ (output gate)에 대응합니다. 핵심 차이는 Mamba의 게이트가 **구조화된 행렬**(대각 $A$에서 유래)이므로 병렬 결합 스캔이 가능하다는 점입니다.

### 하드웨어 효율적 알고리즘 (Hardware-Aware Algorithm)

선택적 SSM은 시간 변이 파라미터를 사용하므로 FFT 기반 컨볼루션으로 계산할 수 없습니다. 순차 재귀 계산은 $O(BLDN)$이지만 GPU에서 병렬화가 불가능합니다. Mamba는 세 가지 핵심 기법으로 이를 해결합니다.

**1) 병렬 접두사 스캔(Parallel Associative Scan)**

재귀식 $h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t$에서 결합 연산자 $\bullet$를 정의합니다:

$$(\bar{A}_i, \bar{B}_i x_i) \bullet (\bar{A}_j, \bar{B}_j x_j) = (\bar{A}_j \bar{A}_i,\; \bar{A}_j \bar{B}_i x_i + \bar{B}_j x_j)$$

이 연산자는 **결합 법칙**(associativity)을 만족합니다: $(a \bullet b) \bullet c = a \bullet (b \bullet c)$. 이 성질 덕분에 Blelloch(1990)의 병렬 접두사 합 알고리즘을 적용하여, 길이 $L$의 시퀀스에 대한 모든 접두사 합을 $O(L)$ 연산량과 $O(\log L)$ 깊이의 병렬 계산으로 구할 수 있습니다.

구체적으로, 순차 계산에서는 $L$단계가 필요하지만, 병렬 스캔에서는 up-sweep과 down-sweep 각각 $\log_2 L$단계만 필요합니다. 예를 들어 $L = 4{,}096$일 때 순차 계산은 4,096단계이지만, 병렬 스캔은 $2 \times 12 = 24$단계로 줄어듭니다.

**2) 커널 퓨전과 메모리 계층 최적화**

현대 GPU에서는 FLOP보다 **메모리 대역폭**이 더 큰 병목인 경우가 많습니다(memory-bound 연산). Mamba는 Flash Attention과 유사한 전략을 적용합니다:

- 이산화, 선택적 스캔, 출력 곱셈 등 여러 연산을 **하나의 CUDA 커널로 퓨전**
- 크기가 큰 중간 상태 $h_t \in \mathbb{R}^{B \times D \times N}$을 HBM에 쓰지 않고 **SRAM에서 직접 계산**하여 출력으로 변환
- HBM-SRAM 사이의 데이터 이동을 최소화

**3) 역전파 시 재계산(Recomputation)**

순전파 시 중간 상태를 저장하지 않고, 역전파에서 기울기 계산 시 다시 계산합니다. 메모리를 $O(BLDN)$에서 $O(BLD + DN)$으로 줄이는 대신 계산량을 약간 증가시키는 트레이드오프이지만, 메모리 대역폭 병목이 해소되어 실제 벽시계 시간(wall-clock time)은 오히려 감소합니다.

### 간결한 아키텍처 (Simplified Architecture)

Mamba 블록은 Transformer의 두 개 서브블록(MHA + FFN)을 **하나의 통합 블록**으로 대체합니다. H3 아키텍처와 게이트 MLP에서 영감을 받은 구조입니다.

![Mamba 블록 아키텍처 ( 선형 투영, Conv1d, 선택적 SSM, 게이팅 분기의 통합 구조](figures/architecture.png)
*Mamba 블록 아키텍처. 입력은 두 분기로 나뉘어, SSM 경로(Linear→Conv1d→SiLU→Selective SSM)와 게이팅 경로(Linear→SiLU)를 거친 후 element-wise 곱셈으로 결합된다. 선택 메커니즘이 SSM 파라미터 $A, B, C, \Delta$를 입력 의존적으로 생성하는 것이 핵심이다.*

설계의 핵심 포인트는 다음과 같습니다:

- **확장 계수(Expand Factor)** $E = 2D$: SSM 경로의 내부 차원을 모델 차원의 2배로 확장하여 표현력을 높입니다.
- **1D 깊이별 컨볼루션(Depthwise Conv1d)**: 커널 크기 $d_{\text{conv}} = 4$로, SSM이 처리하기 어려운 인접 토큰 간의 세밀한 지역적 의존성을 보완합니다.
- **게이팅 분기(Gating Branch)**: SiLU 활성화를 거친 후 SSM 출력과 element-wise 곱셈으로 결합됩니다. GLU(Gated Linear Unit) 변형으로, 정보 흐름을 조절하는 추가적인 비선형 게이팅을 제공합니다.

Transformer 블록(Attention + LayerNorm + FFN + LayerNorm)을 하나로 통합하므로, 동일한 파라미터 수에서 Mamba는 약 2배 많은 블록을 쌓을 수 있어 더 깊은 네트워크를 구성할 수 있습니다.

---

## 코드 예제

아래는 Mamba의 핵심인 선택적 SSM과 Mamba 블록을 PyTorch로 구현한 교육용 코드입니다. 실제 Mamba는 CUDA 커널 퓨전을 사용하지만, 알고리즘의 핵심 로직을 이해하기 위해 순수 PyTorch로 작성합니다.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class SelectiveSSM(nn.Module):
    """Mamba의 핵심: 선택적 상태 공간 모델 (S6)

    기존 SSM의 고정 파라미터(B, C, Δ)를 입력의 함수로 만들어,
    각 시점에서 어떤 정보를 기억/무시할지 동적으로 결정한다.
    """
    def __init__(self, d_model, d_state=16, dt_rank='auto'):
        super().__init__()
        self.d_model = d_model
        self.d_state = d_state
        self.dt_rank = d_model // 16 if dt_rank == 'auto' else dt_rank

        # 입력 의존적 파라미터 생성을 위한 투영
        # x → (dt, B, C): 하나의 선형 변환으로 세 파라미터를 동시에 생성
        self.x_proj = nn.Linear(d_model, self.dt_rank + 2 * d_state, bias=False)
        # dt_rank → d_model: 저랭크 투영으로 Δ를 d_model 차원으로 확장
        self.dt_proj = nn.Linear(self.dt_rank, d_model, bias=True)

        # A는 입력 독립적 (HiPPO 초기화 ) 음수 실수 대각 행렬)
        A = torch.arange(1, d_state + 1).float().repeat(d_model, 1)
        self.A_log = nn.Parameter(torch.log(A))  # log 공간에서 학습하여 안정성 확보
        self.D = nn.Parameter(torch.ones(d_model))  # 스킵 연결 (D 항)

    def forward(self, x):
        """
        x: (B, L, D) ( 배치, 시퀀스 길이, 모델 차원
        반환: (B, L, D) ) 선택적으로 필터링된 출력
        """
        B, L, D = x.shape
        N = self.d_state

        # === 선택 메커니즘: 입력에서 시간 변이 파라미터 생성 ===
        x_dbl = self.x_proj(x)  # (B, L, dt_rank + 2*N)
        dt, B_param, C_param = x_dbl.split(
            [self.dt_rank, N, N], dim=-1
        )
        # Δ_t = softplus(Linear(dt)), 항상 양수, 게이트 역할
        dt = F.softplus(self.dt_proj(dt))  # (B, L, D)

        # A 복원: -exp(A_log)로 음수 보장 (안정적 동역학)
        A = -torch.exp(self.A_log)  # (D, N)

        # === 이산화 및 선택적 스캔 ===
        # 실제 Mamba는 CUDA 병렬 스캔을 사용 (여기서는 교육용 순차 구현)
        h = torch.zeros(B, D, N, device=x.device)
        outputs = []
        for t in range(L):
            # 이산화: A_bar = exp(Δ_t * A), B_bar ≈ Δ_t * B_t
            dt_t = dt[:, t, :].unsqueeze(-1)      # (B, D, 1)
            A_bar = torch.exp(dt_t * A.unsqueeze(0))  # (B, D, N)
            B_bar = dt_t * B_param[:, t, :].unsqueeze(1)  # (B, D, N)

            # 상태 업데이트: h_t = A_bar * h_{t-1} + B_bar * x_t
            h = A_bar * h + B_bar * x[:, t, :].unsqueeze(-1)

            # 출력: y_t = C_t · h_t (내적)
            y = (C_param[:, t, :].unsqueeze(1) * h).sum(-1)  # (B, D)
            outputs.append(y)

        y = torch.stack(outputs, dim=1)  # (B, L, D)
        y = y + x * self.D.unsqueeze(0).unsqueeze(0)  # 스킵 연결
        return y


class MambaBlock(nn.Module):
    """Mamba 블록: Transformer의 MHA+FFN을 단일 블록으로 대체

    구조: Input → [Linear×2 분기] → Conv1d+SiLU+SSM ⊗ SiLU → Linear → Output
    """
    def __init__(self, d_model, d_state=16, expand=2, d_conv=4):
        super().__init__()
        d_inner = int(expand * d_model)

        # 두 분기로 분할: SSM 경로 + 게이팅 경로
        self.in_proj = nn.Linear(d_model, d_inner * 2, bias=False)
        # 깊이별 1D 컨볼루션: 지역적 패턴 포착 (커널 크기 4)
        self.conv1d = nn.Conv1d(
            d_inner, d_inner, kernel_size=d_conv,
            groups=d_inner, padding=d_conv - 1
        )
        self.ssm = SelectiveSSM(d_inner, d_state)
        self.out_proj = nn.Linear(d_inner, d_model, bias=False)
        self.norm = nn.LayerNorm(d_model)

    def forward(self, x):
        residual = x
        x = self.norm(x)
        xz = self.in_proj(x)  # (B, L, 2*d_inner)
        x_branch, z = xz.chunk(2, dim=-1)

        # SSM 경로: Conv1d → SiLU → Selective SSM
        x_branch = self.conv1d(x_branch.transpose(1, 2))[:, :, :x.size(1)]
        x_branch = x_branch.transpose(1, 2)
        x_branch = F.silu(x_branch)
        y = self.ssm(x_branch)

        # 게이팅: SSM 출력 ⊗ SiLU(z)
        output = y * F.silu(z)
        return self.out_proj(output) + residual


# 모델 생성 및 실행 예시
block = MambaBlock(d_model=768, d_state=16, expand=2)
x = torch.randn(2, 1024, 768)  # 배치 2, 시퀀스 1024, 차원 768
y = block(x)
print(f"입출력 shape: {x.shape} -> {y.shape}")
# 출력: 입출력 shape: torch.Size([2, 1024, 768]) -> torch.Size([2, 1024, 768])
```

---

## 실험 결과

저자들은 합성 태스크, 언어 모델링, DNA 서열 분석, 오디오 처리 등 다양한 도메인에서 Mamba를 평가합니다.

### Transformer vs Mamba 복잡도 비교

| 특성 | Transformer | Mamba |
|------|-------------|-------|
| 학습 복잡도 | $O(N^2 D)$ | $O(N D \log N)$ |
| 추론 복잡도 (토큰당) | $O(N D)$ (KV 캐시 참조) | $O(D^2)$ (고정 상태) |
| 추론 메모리 | $O(N \cdot d_{\text{kv}} \cdot L)$ (KV 캐시) | $O(D \cdot N_{\text{state}})$ (고정) |
| 내용 기반 추론 | Self-Attention | 선택적 게이팅 |
| 긴 시퀀스 효율 | 낮음 (이차 증가) | 높음 (선형 증가) |
| 병렬 학습 | 완전 병렬 | 병렬 스캔 ($O(\log N)$ 깊이) |

### 합성 태스크

| 태스크 | S4 | H3 | Hyena | Mamba |
|--------|----|----|-------|-------|
| 선택적 복사 (L=4096) | 실패 | 실패 | 실패 | **100%** |
| 유도 헤드 (L=256) | 실패 | 실패 | 실패 | **100%** |

기존 LTI SSM(S4, H3, Hyena)은 두 태스크 모두에서 랜덤 수준의 성능에 머무르지만, Mamba는 완벽한 정확도를 달성합니다. 이는 선택 메커니즘이 SSM의 표현력을 근본적으로 확장함을 증명합니다.

### 언어 모델링 (The Pile)

| 모델 | 파라미터 | Perplexity |
|------|---------|------------|
| Transformer++ | 125M | 10.56 |
| Hyena | 125M | 10.64 |
| H3 | 125M | 10.49 |
| **Mamba** | **130M** | **10.52** |
| Transformer++ | 350M | 8.56 |
| Hyena | 355M | 8.71 |
| RetNet | 355M | 8.63 |
| H3 | 355M | 8.60 |
| **Mamba** | **370M** | **8.14** |
| Transformer++ | 760M | 7.89 |
| **Mamba** | **790M** | **7.33** |
| Transformer++ | 1.3B | 7.18 |
| **Mamba** | **1.4B** | **6.80** |

The Pile 데이터셋에서의 zero-shot perplexity 결과입니다. 핵심적으로 두 가지 경향이 관찰됩니다:

1. **규모가 커질수록 격차 확대**: 125M에서는 Transformer++와 거의 동등(10.52 vs 10.56)하지만, 1.4B에서는 6.80 vs 7.18로 격차가 벌어집니다. 이는 Mamba의 스케일링 법칙(scaling law)이 Transformer보다 우수함을 시사합니다.
2. **다른 sub-quadratic 모델 대비 압도적 우위**: 370M 규모에서 Hyena(8.71), RetNet(8.63), H3(8.60) 대비 Mamba(8.14)는 큰 폭으로 우수합니다.

### 하위 평가 벤치마크 (Zero-Shot)

| 벤치마크 | Mamba-1.4B | Mamba-2.8B | Pythia-1.4B | Pythia-2.8B |
|----------|-----------|-----------|------------|------------|
| HellaSwag | 59.1 | 65.5 | 52.1 | 59.3 |
| PIQA | 73.8 | 76.0 | 71.1 | 74.2 |
| WinoGrande | 56.1 | 60.5 | 53.5 | 59.6 |
| ARC-Easy | 61.2 | 65.6 | 57.6 | 63.9 |
| ARC-Challenge | 32.8 | 36.3 | 28.5 | 32.9 |
| **Average** | **56.6** | **60.8** | 52.6 | 58.0 |

Mamba-1.4B는 동일 규모 Pythia-1.4B(Transformer) 대비 모든 벤치마크에서 우위를 보이며, 평균 56.6 vs 52.6으로 **4.0포인트 차이**를 기록합니다. 특히 HellaSwag(59.1 vs 52.1)에서의 7.0포인트 격차가 눈에 띕니다. Mamba-2.8B는 Pythia-2.8B보다 크기가 동일하면서도 평균 2.8포인트 우위를 보입니다.

### DNA 서열 모델링 (HG38)

| 모델 | 파라미터 | Perplexity |
|------|---------|------------|
| Transformer++ | 1.6M | 8.63 |
| Hyena | 1.4M | 8.19 |
| **Mamba** | **1.4M** | **7.18** |
| Transformer++ | 6.4M | 7.85 |
| Hyena | 6.5M | 6.58 |
| **Mamba** | **7.0M** | **5.92** |

DNA 서열 모델링에서 Mamba는 Transformer와 Hyena를 큰 폭으로 능가합니다. 유전체 서열은 수천~수만 base pair의 긴 시퀀스를 다루므로 Mamba의 선형 복잡도가 특히 유리하며, 선택 메커니즘이 염기 서열의 문맥 의존적 패턴(프로모터, 인핸서, 스플라이스 사이트 등)을 선택적으로 포착하는 능력이 성능 향상에 기여합니다.

### 오디오 처리 (SC10)

| 모델 | Accuracy |
|------|----------|
| Transformer | 93.96% |
| S4 | 98.32% |
| S4D | 98.32% |
| **Mamba** | **98.68%** |

Speech Commands 10 분류 태스크에서 Mamba는 S4(98.32%)를 소폭 능가하는 98.68%의 정확도를 달성합니다. 오디오 신호는 16kHz 샘플링 기준 1초에 16,000개 시점을 포함하므로, 선형 복잡도의 이점이 극대화되는 도메인입니다. Transformer(93.96%)와의 격차가 크다는 점도 주목할 만합니다.

### 추론 속도

A100 GPU에서 측정한 결과, Mamba는 시퀀스 길이 증가에 따른 추론 처리량에서 Transformer 대비 압도적인 우위를 보입니다:

| 시퀀스 길이 | Mamba 속도 향상 |
|:---:|:---:|
| 512 | ~2배 |
| 2K | ~3배 |
| 8K | ~4배 |
| 16K | ~**5배** |

시퀀스가 길어질수록 격차가 확대되는 것은 Mamba의 추론 상태 크기가 $O(D \cdot N_{\text{state}})$로 시퀀스 길이와 **무관하게 고정**되기 때문입니다. Transformer는 KV 캐시가 $O(N)$으로 증가하므로, 시퀀스가 길어질수록 메모리 대역폭 병목이 심화됩니다.

---

## 의의 및 한계

### 의의

**효율성 패러다임의 전환**: Transformer의 이차 복잡도를 선형으로 줄이면서 동등 이상의 성능을 달성하는 첫 번째 실용적 대안을 제시했습니다. "어텐션이 유일한 해답은 아니다"라는 가능성을 구체적으로 입증한 것입니다.

**선택적 처리의 핵심 발견**: LTI SSM의 "효율적이지만 표현력이 제한적"이라는 딜레마를 입력 의존적 파라미터로 해결했습니다. 이 인사이트는 이후 모든 SSM 연구의 기본 전제가 되었습니다.

**하드웨어 인식 알고리즘 설계**: GPU 메모리 계층(HBM vs SRAM)을 인식한 커널 퓨전 설계로, 이론적 효율성을 실제 벽시계 시간의 속도 향상으로 전환했습니다. Flash Attention과 함께 "하드웨어를 고려한 알고리즘 설계"의 중요성을 보여주는 대표 사례입니다.

**범용 시퀀스 모델**: 언어, DNA, 오디오 등 다양한 모달리티에서 일관된 성능 향상을 보였습니다. 특히 DNA 서열과 오디오처럼 매우 긴 시퀀스를 다루는 도메인에서 Transformer 대비 뚜렷한 이점이 있습니다.

**후속 연구 촉발**: Mamba-2(SSD 프레임워크), Vision Mamba(Vim), Jamba(AI21 Labs), Zamba(Zyphra) 등 수많은 후속 연구와 하이브리드 아키텍처를 촉발했습니다.

### 한계

**압축 상태의 정보 손실**: 과거 정보를 고정 크기 상태($D \times N_{\text{state}}$ 차원)로 압축하므로, 먼 과거의 특정 토큰을 정확히 검색(retrieval)하는 능력이 Transformer의 KV 캐시보다 열위합니다. Transformer는 어텐션으로 임의의 과거 토큰에 직접 접근할 수 있지만, Mamba는 상태를 통해 간접적으로만 접근합니다.

**In-Context Learning 열위**: Transformer의 어텐션 기반 ICL 능력에 비해 약합니다. 어텐션은 본질적으로 in-context에서 key-value 매핑을 학습할 수 있지만, 고정 크기 상태로 압축하는 재귀 모델은 이 능력이 제한적입니다. 이 한계가 Jamba 같은 Mamba-Transformer 하이브리드 아키텍처가 등장한 핵심 배경입니다.

**구현 복잡성**: 하드웨어 효율적 병렬 스캔의 CUDA 커널 구현이 복잡하여, Transformer 대비 프레임워크 생태계 지원이 부족합니다. Transformer는 `nn.MultiheadAttention`이나 Flash Attention으로 쉽게 사용할 수 있지만, Mamba는 전용 커널 설치가 필요합니다.

**학습 안정성**: 선택적 게이팅으로 인한 기울기 소실/폭발 위험이 있으며, 특히 대규모 모델(>7B)에서 안정적 학습을 위해 추가 기법(gradient clipping, 학습률 스케줄링 등)이 필요합니다.

---

## 후속 연구

### Mamba-2 (2024)

구조적 상태 공간 이중성(SSD: Structured State Space Duality) 프레임워크를 제안하여, Mamba의 선택적 SSM이 특수한 형태의 **구조화된 어텐션**임을 증명했습니다. 구체적으로, SSM의 상태 차원 $N$이 어텐션의 헤드 차원에 대응하며, 재귀 연산이 반인과(semi-separable) 행렬과의 곱셈으로 표현됩니다. 이 이론적 통합을 기반으로 텐서 병렬화와 더 큰 상태 차원을 활용하여 Mamba 대비 **2~8배 빠른 학습 속도**를 달성했습니다.

### Mamba-3 (2026)

개선된 상태 공간 원리를 활용한 시퀀스 모델링의 최신 발전으로, SSM 아키텍처의 지속적인 진화를 보여줍니다.

### 하이브리드 아키텍처

**Jamba**(AI21 Labs)는 Mamba 레이어와 Transformer 레이어를 교차 배치하여 SSM의 효율성과 Attention의 ICL 능력을 결합합니다. 52B 파라미터 중 12B만 활성화하는 MoE를 함께 사용하여, 단일 80GB GPU에서 256K 토큰 컨텍스트를 처리할 수 있습니다. **Zamba**(Zyphra)도 유사한 하이브리드 접근을 취하며, 이러한 하이브리드 아키텍처들이 순수 Transformer나 순수 SSM보다 실용적으로 우수한 성능을 보이는 경우가 늘어나고 있습니다.

---

## 결론

Mamba는 상태 공간 모델에 "선택성"이라는 단 하나의 핵심 원리를 부여함으로써, Transformer의 내용 기반 추론 능력을 확보하면서도 선형 시간 복잡도를 유지하는 데 성공했습니다. 기존 SSM의 LTI 제약을 깨고 입력 의존적 파라미터 $B_t, C_t, \Delta_t$를 도입하되, 병렬 결합 스캔과 하드웨어 인식 커널 퓨전을 통해 효율성을 유지한 것이 핵심입니다.

특히 $\Delta_t$가 LSTM의 forget gate에 대응하면서도 병렬 스캔이 가능하다는 발견은, "게이트 RNN의 표현력 + 병렬 계산의 효율성"을 동시에 달성할 수 있음을 보여준 이론적으로 중요한 기여입니다. 수십만 토큰의 초장기 시퀀스 처리가 필요한 영역에서 Transformer를 대체하거나 보완할 수 있는 유망한 대안을 제시합니다.

향후 SSM과 Transformer의 이론적 통합(Mamba-2의 SSD), 하이브리드 아키텍처(Jamba, Zamba), 비전/멀티모달 확장(Vision Mamba) 등 다양한 방향으로 연구가 활발하게 진행되고 있으며, Mamba는 "어텐션이 전부가 아니다(Attention is not all you need)"라는 메시지를 강력하게 전달하며 시퀀스 모델링의 새로운 장을 열었습니다.

## 관련 문서

- [[s4|S4]] -- 발전 기반
- [[mamba-2|Mamba-2]] -- 후속 모델
- [[h3|H3]] -- 영감
- [[griffin|Griffin]] -- 영감을 줌
- [[jamba|Jamba: A Hybrid Transformer-Mamba Language Model]] -- 영감을 줌
