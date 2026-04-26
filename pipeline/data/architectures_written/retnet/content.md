<!-- infographic-hero -->
![RetNet 핵심 요약](figures/infographic.svg)

*Figure: RetNet 한 장 요약 인포그래픽*

# RetNet: 학습 병렬화와 효율적 추론을 동시에 달성한 Retention 메커니즘

**Microsoft Research** · **2023-07-17** · **SSM** · **MIT**

## 개요

RetNet(Retentive Network)은 2023년 Microsoft Research가 발표한 모델로, 학습 병렬화, $O(1)$ 추론 메모리, 선형 복잡도의 세 가지 목표를 동시에 달성하는 Retention 메커니즘을 제안했다. 이 세 가지는 시퀀스 모델링의 "불가능한 삼각형(impossible triangle)"으로 여겨졌다.

기존 Transformer는 학습은 완전 병렬화되지만 추론 시 KV 캐시가 $O(N)$으로 증가한다. RNN/SSM은 추론은 $O(1)$로 효율적이지만 학습 병렬화가 제한적이다. RetNet은 이 트릴레마를 해결하기 위해 retention 연산을 **병렬 모드(학습)**, **순환 모드(추론)**, **청크 순환 모드(배치 추론)** 세 가지로 등가 변환하여 사용 목적에 맞게 전환 가능하게 했다. GPT-3 수준 크기(6.7B)에서 추론 메모리를 8배, 처리량을 8.4배 향상시켰다.

RetNet의 삼중 모드 전환 아이디어는 SSM/선형 어텐션 연구에서 핵심적 설계 원칙으로 자리잡았으며, GLA, Gated DeltaNet 등 후속 연구의 직접적 기반이 되었다.

![RetNet 아키텍처 - Retention 메커니즘의 병렬/순환/청크 순환 삼중 모드 전환 구조](figures/architecture.svg)

*Figure 1: RetNet 아키텍처 - Retention 연산을 병렬 모드(학습), 순환 모드(추론), 청크 순환 모드(배치 추론)로 등가 변환하여 학습 병렬화, O(1) 추론 메모리, 선형 복잡도를 동시에 달성한다.*

RetNet은 기존 접근법들이 해결하지 못했던 "불가능한 삼각형"을 달성한다. 아래 그림은 Transformer, Linear Transformer, RNN 각각이 삼각형의 한 변씩만 달성하는 반면, RetNet은 세 꼭짓점을 모두 달성함을 보여준다.

![RetNet의 불가능한 삼각형 - 학습 병렬화, 강한 성능, 저비용 추론을 동시에 달성](figures/fig_2.png)
*Figure 1: 불가능한 삼각형 - Transformer는 학습 병렬화와 강한 성능을, RNN은 저비용 추론과 강한 성능을, Linear Transformer는 학습 병렬화와 저비용 추론을 각각 달성하지만, RetNet은 세 가지를 모두 달성한다. (Source: arXiv 2307.08621)*

## 아키텍처 상세

RetNet의 핵심은 Retention 연산이다. 이 연산은 세 가지 수학적으로 동치인 형태로 표현된다.

### 병렬 모드 (학습)

아래 그림은 병렬 모드에서의 Retention 연산 구조를 보여준다. Q, K, V로부터 행렬 연산을 통해 한 번에 출력을 계산하는 방식이다.

![Retention 병렬 표현 - Q, K, V 행렬 연산과 감쇠 마스크 D를 통한 병렬 계산](figures/fig_4.png)
*Figure 2: Retention 병렬 표현 - 입력 X에서 Q, K, V를 추출하고, 감쇠 마스크 D와 함께 $(QK^T \odot D)V$ 행렬 연산으로 출력 O를 계산한다. (Source: arXiv 2307.08621)*

전체 시퀀스에 대해 행렬 연산으로 한 번에 계산한다.

$$\text{Ret}(X) = (Q \odot \Theta)(K \odot \bar{\Theta})^T \odot D \cdot V$$

여기서 $\Theta$는 xPos 위치 인코딩, $D$는 지수 감쇠 마스크 행렬이다. $D_{nm} = \gamma^{n-m}$ (단, $n \geq m$, 아니면 0)으로, 먼 거리의 토큰일수록 기하급수적으로 감소하는 가중치를 부여한다. 이 형태는 softmax를 사용하지 않는 점을 제외하면 어텐션과 매우 유사하며, GPU에서 완전 병렬화된다.

### 순환 모드 (추론)

다음 그림은 순환 모드에서의 Retention 연산을 보여준다. 이전 상태 $S_{n-1}$에 감쇠율 $\gamma$를 적용하며 고정 크기 상태만으로 효율적인 추론이 가능하다.

![Retention 순환 표현 - 고정 크기 상태를 유지하며 한 토큰씩 처리하는 구조](figures/fig_5.png)
*Figure 3: Retention 순환 표현 - 상태 $S_n$은 이전 상태에 감쇠율 $\gamma$를 곱하고 새로운 키-값 외적을 더하여 갱신된다. 추론 시 $O(1)$ 메모리로 동작한다. (Source: arXiv 2307.08621)*

한 토큰씩 순차적으로 처리하며, 고정 크기 상태만 유지한다.

$$s_t = \gamma \cdot s_{t-1} + k_t^T v_t$$
$$o_t = q_t \cdot s_t$$

여기서 $s_t \in \mathbb{R}^{d_k \times d_v}$는 상태 행렬이다. 각 토큰을 처리할 때 이전 상태에 감쇠율 $\gamma$를 곱하고 새로운 키-값 외적을 더한다. SSM의 상태 업데이트 $h_t = \bar{A}h_{t-1} + \bar{B}x_t$와 구조적으로 동일하며, $\gamma$가 $\bar{A}$의 역할을, $k_t^T v_t$가 $\bar{B}x_t$의 역할을 한다.

### 청크 순환 모드 (배치 추론)

시퀀스를 고정 크기 청크로 분할한다. 청크 내부에서는 병렬 모드로 계산하고, 청크 간에서는 순환 모드로 상태를 전파한다.

$$Y_{\text{chunk}} = \underbrace{(Q_c D_c K_c^T) V_c}_{\text{intra-chunk (parallel)}} + \underbrace{Q_c \gamma^{\text{pos}} s_{\text{prev}}}_{\text{inter-chunk (recurrence)}}$$

### Multi-Scale Retention (MSR)

멀티-헤드 구조에서 각 헤드마다 다른 감쇠율 $\gamma_h$를 사용한다.

$$\gamma_h \in \{0.95, 0.97, 0.99, 0.999, \ldots\}$$

작은 $\gamma$의 헤드는 최근 정보에 집중(단거리 패턴), 큰 $\gamma$의 헤드는 과거 정보를 오래 유지(장거리 의존성)한다. 이 다중 스케일 설계로 하나의 모델이 다양한 시간 스케일의 패턴을 동시에 포착한다.

### xPos 위치 인코딩

xPos는 RoPE(Rotary Position Embedding)에 지수 감쇠를 결합한 위치 인코딩으로, 학습 시퀀스 길이를 넘는 외삽(extrapolation)에 강하다.

## 핵심 혁신

RetNet의 핵심 혁신은 세 가지이다.

첫째, **삼중 등가 표현**이다. 하나의 연산을 학습/추론/배치 추론 세 가지 모드로 등가 변환할 수 있어, 학습 시에는 GPU 활용도를 극대화하고 배포 시에는 메모리를 최소화할 수 있다.

둘째, **지수 감쇠 마스크**이다. softmax 대신 지수 감쇠를 사용함으로써 순환 형태로의 변환이 가능해졌다. softmax는 전체 시퀀스에 대한 정규화가 필요하므로 순환 형태로 변환할 수 없지만, 지수 감쇠는 각 타임스텝에서 독립적으로 계산 가능하다.

셋째, **다중 스케일 의존성 포착**이다. 헤드별로 다른 감쇠율을 사용하여, 단거리부터 장거리까지 다양한 시간 스케일의 패턴을 동시에 포착한다.

## 벤치마크/성능

아래 그래프들은 RetNet의 핵심 성능 지표를 보여준다. 모델 크기가 커질수록 Transformer 대비 RetNet의 이점이 두드러지며, GPU 메모리 사용량과 추론 처리량에서 압도적인 차이를 보인다.

![RetNet vs Transformer 스케일링 곡선 - 모델 크기 증가에 따른 Perplexity 비교](figures/fig_7.png)
*Figure 4: 스케일링 곡선 - 모델 크기가 2B를 넘으면 RetNet이 Transformer보다 낮은 Perplexity를 달성한다. 크기가 커질수록 RetNet의 이점이 확대되는 경향을 보인다. (Source: arXiv 2307.08621)*

![RetNet vs Transformer GPU 메모리 사용량 - 시퀀스 길이에 따른 메모리 비교](figures/fig_9.png)
*Figure 5: GPU 메모리 비교 - Transformer는 시퀀스 길이가 증가할수록 KV 캐시로 인해 메모리가 선형 증가하지만, RetNet은 고정 크기 상태만 유지하므로 시퀀스 길이에 무관하게 일정한 메모리를 사용한다. (Source: arXiv 2307.08621)*

| 모델 | 파라미터 | PPL↓ | 추론 메모리 | 처리량 |
|------|---------|------|-----------|--------|
| RetNet | 6.7B | 7.12 | 1x | 8.4x |
| Transformer | 6.7B | 7.08 | 8x | 1x |
| RetNet | 2.7B | 8.15 | 1x | 6.2x |
| RWKV | 7B | 7.35 | 1.2x | 5.1x |

| 모델 | 학습 병렬화 | 추론 메모리 | 복잡도 | 위치 인코딩 |
|------|-----------|-----------|--------|------------|
| RetNet | 완전 병렬 | $O(1)$ | $O(N)$ | xPos |
| Transformer | 완전 병렬 | $O(N)$ | $O(N^2)$ | RoPE |
| RWKV | 시간축 병렬 | $O(1)$ | $O(N)$ | 암묵적 감쇠 |
| Mamba | Parallel scan | $O(1)$ | $O(N)$ | 없음(SSM) |

## 학습

The Pile 및 내부 Microsoft 데이터셋으로 학습하며, A100 80GB GPU를 사용한다. Llama와 유사한 학습 설정을 적용하고 SentencePiece 토크나이저를 사용한다. 병렬 학습 모드에서는 표준 Transformer와 동일한 방식으로 학습한다. 6.7B 모델은 약 150B 토큰으로 학습되었다.

다음은 RetNet의 Retention 연산을 세 가지 모드로 구현한 예시이다.

```python
import torch
import torch.nn as nn

class Retention(nn.Module):
    def __init__(self, d_model, n_heads, gamma=0.99):
        super().__init__()
        self.d_k = d_model // n_heads
        self.gamma = gamma
        self.W_q = nn.Linear(d_model, d_model)
        self.W_k = nn.Linear(d_model, d_model)
        self.W_v = nn.Linear(d_model, d_model)

    def parallel_forward(self, x):
        """병렬 모드 (학습)"""
        Q, K, V = self.W_q(x), self.W_k(x), self.W_v(x)
        L = x.size(1)
        # 지수 감쇠 마스크 D 생성
        positions = torch.arange(L, device=x.device)
        D = self.gamma ** (positions.unsqueeze(0) - positions.unsqueeze(1))
        D = D.tril()  # causal mask
        # Retention 계산
        return (Q @ K.transpose(-1, -2) * D) @ V

    def recurrent_forward(self, x_t, state):
        """순환 모드 (추론) - O(1) 메모리"""
        q_t = self.W_q(x_t)  # (B, d_k)
        k_t = self.W_k(x_t)  # (B, d_k)
        v_t = self.W_v(x_t)  # (B, d_v)
        # 상태 업데이트: s_t = gamma * s_{t-1} + k_t^T v_t
        state = self.gamma * state + k_t.unsqueeze(-1) * v_t.unsqueeze(-2)
        # 출력: o_t = q_t * s_t
        o_t = (q_t.unsqueeze(-1) * state).sum(-2)
        return o_t, state
```

## 관련 모델

RetNet은 Microsoft의 torchscale 라이브러리를 통해 사용할 수 있다. 삼중 모드 전환 기능 덕분에 개발-배포 파이프라인이 매우 유연하다. 감쇠율 $\gamma$가 학습 전에 고정된다는 한계는 GLA(입력 의존적 게이팅)나 Mamba(선택적 $\Delta$)에서 해결되었으며, RetNet의 삼중 모드 전환과 Multi-Scale Retention 아이디어는 GLA, Gated DeltaNet 등 후속 연구에서 핵심적으로 활용되고 있다.

## 참고 자료

- 논문: [Retentive Network: A Successor to Transformer for Large Language Models](https://arxiv.org/abs/2307.08621)
- 코드: [microsoft/torchscale](https://github.com/microsoft/torchscale)

## 관련 문서

- [[transformer|Transformer]] - 영감
- [[gated-deltanet|Gated DeltaNet]] - 영감을 줌
- [[gla|GLA]] - 영감을 줌
