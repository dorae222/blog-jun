# S4: 상태 공간 모델의 시대를 연 구조화된 SSM

**Stanford University** · **2021-10-31** · **SSM** · **Apache-2.0**

## 개요

S4(Structured State Spaces for Sequence Modeling)는 2021년 Stanford의 Albert Gu가 발표한 모델로, 시퀀스 모델링에서 상태 공간 모델(SSM)의 가능성을 처음으로 입증한 기념비적 연구이다. 이 논문은 이후 H3, Hyena, Mamba로 이어지는 SSM 연구의 시발점이 되었으며, "Transformer 이후의 시퀀스 모델"에 대한 본격적인 탐색을 촉발했다.

당시 시퀀스 모델링의 지형은 명확했다. Transformer의 self-attention은 $O(N^2)$ 복잡도로 긴 시퀀스 처리에 한계가 있었고, RNN은 장거리 의존성을 포착하지 못하며 병렬화가 불가능했다. S4는 제3의 길을 제시했다. 연속 시간 상태 공간 모델(continuous-time SSM)을 이산화하고, HiPPO(High-order Polynomial Projection Operators) 행렬 초기화를 통해 장거리 의존성을 효과적으로 포착하면서도 $O(N \log N)$ 복잡도로 학습할 수 있게 했다.

pathfinder-X 같은 극단적 장거리 의존성 벤치마크(시퀀스 길이 16,384)에서 S4는 96% 정확도를 달성하며 Transformer(62%)를 압도했다. Transformer는 이 길이에서 아예 학습이 실패하지만, S4는 안정적으로 수렴한다. 이 결과는 SSM이 장거리 의존성에서 근본적 우위를 가질 수 있음을 처음으로 입증했다.

![S4 아키텍처 - HiPPO 행렬 초기화와 이산화를 통한 구조화된 상태 공간 모델](figures/architecture.svg)

*Figure 1: S4 아키텍처 - 연속 시간 SSM을 HiPPO 행렬로 초기화하고 이산화하여, 순환 모드와 컨볼루션 모드의 이중 표현으로 O(N log N) 복잡도의 장거리 의존성 모델링을 달성한다.*

다음 그림은 S4의 핵심 아이디어를 세 부분으로 요약한다. 연속 상태 공간, HiPPO 기반 장거리 의존성 포착, 그리고 효율적인 이산 표현이다.

![S4의 핵심 개념 - 연속 상태 공간, 장거리 의존성, 이산 표현의 세 가지 관점](figures/fig_1.png)
*Figure 1: S4의 개념적 프레임워크 - (좌) A, B, C, D 행렬로 매개변수화된 연속 상태 공간 모델, (중앙) HiPPO 이론 기반의 장거리 의존성 포착, (우) 순환/컨볼루션 이중 표현. (Source: S4 논문)*

## 아키텍처 상세

S4는 연속 시간 상태 공간 모델을 기반으로 한다. 제어 이론에서 유래한 상태 방정식은 다음과 같다.

### 연속 시간 SSM

$$h'(t) = Ah(t) + Bx(t)$$
$$y(t) = Ch(t) + Dx(t)$$

여기서 $A \in \mathbb{R}^{N \times N}$는 상태 전이 행렬, $B \in \mathbb{R}^{N \times 1}$은 입력 행렬, $C \in \mathbb{R}^{1 \times N}$은 출력 행렬이다. $h(t) \in \mathbb{R}^N$은 잠재 상태(latent state)로, 과거 입력의 압축된 표현을 담고 있다.

### 이산화(Discretization)

연속 시스템을 디지털 시퀀스에 적용하려면 이산화가 필요하다. S4는 ZOH(Zero-Order Hold) 방식을 사용한다.

$$\bar{A} = \exp(\Delta A)$$
$$\bar{B} = (\Delta A)^{-1}(\exp(\Delta A) - I) \cdot \Delta B$$

이산화된 시스템은 다음과 같이 순환 형태로 동작한다.

$$h_t = \bar{A} h_{t-1} + \bar{B} x_t$$
$$y_t = \bar{C} h_t$$

여기서 $\Delta$는 이산화 스텝 크기로, 연속 시간과 이산 시간 사이의 해상도를 결정한다.

### HiPPO 행렬 초기화

S4의 핵심 혁신 중 하나는 상태 전이 행렬 $A$의 초기화이다. HiPPO(High-order Polynomial Projection Operators) 행렬은 직교 다항식 기저(Legendre 다항식)를 이용해 과거 입력의 최적 압축 표현을 유지하도록 설계되었다. 구체적으로 HiPPO-LegS 행렬은 다음과 같다.

$$A_{nk} = -\begin{cases} (2n+1)^{1/2}(2k+1)^{1/2} & \text{if } n > k \\ n+1 & \text{if } n = k \\ 0 & \text{if } n < k \end{cases}$$

이 초기화는 랜덤 초기화 대비 장거리 의존성 포착 능력을 극적으로 향상시킨다. HiPPO 행렬을 사용하면 상태 벡터가 과거 입력의 다항식 근사를 유지하게 되어, 수천~수만 스텝 이전의 정보도 효과적으로 보존할 수 있다.

아래 그래프는 CIFAR-10에서 다양한 초기화 방식의 학습 수렴 속도를 비교한 것이다. HiPPO 초기화가 랜덤 초기화 대비 압도적으로 빠르게 수렴하는 것을 확인할 수 있다.

![다양한 행렬 초기화에 따른 SSM 학습 정확도 비교 - HiPPO vs Diagonal vs Random](figures/fig_14_1.png)
*Figure 2: SSM 초기화 방식별 CIFAR-10 학습 정확도 - HiPPO(파란색)가 Random(빨간색)과 Diagonal(녹색) 대비 빠르고 안정적으로 수렴한다. 특히 Frozen A(점선)에서도 HiPPO는 높은 성능을 유지한다. (Source: S4 논문)*

### DPLR 분해와 컨볼루션 모드

일반 $N \times N$ 행렬 $A$를 직접 계산하면 비용이 크다. S4는 $A$를 DPLR(Diagonal Plus Low-Rank) 형태로 분해한다.

$$A = \Lambda - PQ^T$$

이 분해 덕분에 SSM의 전달 함수(transfer function)가 Cauchy 커널로 환원되며, $O(N)$ 시간에 계산 가능하다. 전체 시퀀스에 대한 컨볼루션 커널 $\bar{K}$를 생성한 뒤 FFT로 컨볼루션을 수행하면 $O(L \log L)$ 학습 복잡도를 달성한다.

$$\bar{K} = (C\bar{B}, C\bar{A}\bar{B}, C\bar{A}^2\bar{B}, \ldots, C\bar{A}^{L-1}\bar{B})$$
$$y = \bar{K} * x \quad \xrightarrow{\text{FFT}} \quad Y = \bar{K}_{\text{freq}} \odot X_{\text{freq}}$$

학습 시에는 컨볼루션 모드로 FFT를 활용한 병렬 계산을, 추론 시에는 순환 모드로 $O(1)$ 상태 갱신을 수행한다.

## 핵심 혁신

S4의 핵심 혁신은 네 가지이다.

첫째, **HiPPO 초기화**이다. 수학적으로 최적화된 행렬 초기화로 장거리 의존성 포착이 가능해졌다. 이전의 SSM이나 RNN에서는 수천 스텝 이상의 의존성을 포착하는 것이 사실상 불가능했다.

둘째, **구조화된 행렬 분해**이다. DPLR 분해와 Cauchy 커널 계산으로 SSM의 계산 비용을 극적으로 줄였다.

셋째, **컨볼루션-순환 이중성**이다. 학습과 추론에서 각각 최적의 계산 모드를 사용할 수 있는 유연한 설계이다. 이 이중성은 이후 RetNet, RWKV 등에서도 핵심 설계 원칙으로 채택되었다.

넷째, **LTI(Linear Time-Invariant) 시스템**이다. A, B, C 파라미터가 입력과 무관하게 고정되어 있어 컨볼루션 모드가 가능하지만, 이 특성이 동시에 콘텐츠 기반 추론의 한계를 만든다.

## 벤치마크/성능

| 모델 | ListOps | Text | Retrieval | Image | Pathfinder | Path-X | 평균 |
|------|---------|------|-----------|-------|------------|--------|------|
| S4 | 58.4 | 86.8 | 87.1 | 88.7 | 94.2 | 96.0 | 85.2 |
| Transformer | 36.4 | 64.3 | 57.5 | 42.4 | 71.4 | X | 54.4 |
| LSTM | 35.0 | 56.2 | 50.3 | 35.6 | 52.1 | X | 45.8 |
| S4D | 60.5 | 86.2 | 85.3 | 88.4 | 93.9 | 91.0 | 84.2 |

Long Range Arena(LRA) 벤치마크에서 S4는 모든 태스크에서 Transformer와 LSTM을 크게 능가한다. Path-X(길이 16K)에서 Transformer는 아예 학습이 실패(X)하지만 S4는 96%를 달성한다.

다음은 Path-X 태스크의 예시와 S4가 학습한 컨볼루션 필터를 시각화한 것이다. 16,384 길이의 시퀀스에서 두 마커가 경로로 연결되어 있는지 판별하는 극단적인 장거리 의존성 태스크이다.

![Path-X 태스크 예시 - 두 마커가 점선 경로로 연결된 이미지](figures/fig_5_1.png)
*Figure 3: Path-X 태스크 예시 - 128x128 이미지(시퀀스 길이 16,384)에서 두 개의 마커가 점선 경로로 연결되어 있는지 판별해야 한다. S4는 이 태스크에서 96% 정확도를 달성했다. (Source: S4 논문)*

S4가 학습한 컨볼루션 커널은 첫 번째 레이어와 마지막 레이어에서 뚜렷이 다른 패턴을 보인다.

![S4 첫 번째 레이어의 컨볼루션 필터 - 저수준 특징 추출 패턴](figures/fig_7_1.png)
*Figure 4: S4 첫 번째 레이어 필터 - 16,384 길이의 컨볼루션 커널을 128x128로 재구성한 시각화. 초기 레이어에서는 국소적 패턴을 감지하는 필터가 학습된다. (Source: S4 논문)*

| 모델 | 행렬 A 처리 | 초기화 | LTI | 복잡도 | 언어 모델링 |
|------|-----------|--------|-----|--------|------------|
| S4 | DPLR 분해 | HiPPO | 예 | $O(N \log N)$ | 제한적 |
| S4D | 대각화 | HiPPO 대각 | 예 | $O(N \log N)$ | 개선 |
| H3 | 이중 SSM | HiPPO | 예 | $O(N \log N)$ | 양호 |
| Mamba | 입력 의존 | 없음 | 아니오 | $O(N)$ | 우수 |

## 학습

Long Range Arena(LRA) 벤치마크를 기준으로 학습하며, 배치 크기 50, A100 GPU를 사용한다. 시퀀스 길이 1K~16K 범위에서 실험한다. 컨볼루션 커널을 FFT로 계산하여 $O(N \log N)$ 학습 복잡도를 달성한다. HiPPO 행렬 초기화를 사용하며 학습 중 안정적인 수렴을 보인다.

다음은 S4의 이산화 과정을 PyTorch로 구현한 예시이다.

```python
import torch
import torch.nn as nn

class S4Kernel(nn.Module):
    def __init__(self, d_model, N=64, dt_min=0.001, dt_max=0.1):
        super().__init__()
        # HiPPO-LegS 행렬 초기화
        A = self._hippo_matrix(N)
        self.A = nn.Parameter(torch.tensor(A, dtype=torch.float32))
        self.B = nn.Parameter(torch.randn(N, 1) * 0.01)
        self.C = nn.Parameter(torch.randn(1, N) * 0.01)
        self.log_dt = nn.Parameter(
            torch.rand(d_model) * (torch.log(torch.tensor(dt_max)) 
            - torch.log(torch.tensor(dt_min))) 
            + torch.log(torch.tensor(dt_min))
        )

    def _hippo_matrix(self, N):
        """HiPPO-LegS 행렬 생성"""
        P = torch.sqrt(1 + 2 * torch.arange(N, dtype=torch.float32))
        A = -torch.outer(P, P).tril()  # 하삼각 부분
        A += torch.diag(torch.arange(N, dtype=torch.float32) + 1)
        return -A

    def discretize(self):
        """ZOH 이산화"""
        dt = torch.exp(self.log_dt)
        A_bar = torch.matrix_exp(dt.unsqueeze(-1) * self.A)
        B_bar = torch.linalg.solve(
            self.A, (A_bar - torch.eye(self.A.size(0))) @ self.B
        )
        return A_bar, B_bar
```

## 관련 모델

S4는 직접적인 프로덕션 LLM으로서의 활용보다는 시계열 예측, 오디오 처리, 생물학적 서열 분석 등 장거리 의존성이 핵심인 도메인에서 강점을 가진다. S4의 LTI 특성(A, B, C 파라미터가 입력과 무관하게 고정)은 언어 모델링에서 치명적인 약점으로, H3 연구에서 정밀하게 진단되었고 Mamba의 선택적 메커니즘으로 해결되었다. 그러나 S4의 HiPPO 초기화, DPLR 분해, 컨볼루션-순환 이중성이라는 핵심 아이디어는 모든 후속 SSM 연구의 기반이 되었으며, SSM 분야의 "Transformer 논문"에 해당하는 기념비적 연구로 남아 있다.

## 참고 자료

- 논문: [Efficiently Modeling Long Sequences with Structured State Spaces](https://arxiv.org/abs/2111.00396)
- 코드: [state-spaces/s4](https://github.com/state-spaces/s4)

## 관련 문서

- [[h3|H3]] - 후속 모델
- [[mamba|Mamba: Linear-Time Sequence Modeling with Selective State Spaces]] - 후속 모델
- [[hgrn|HGRN]] - 영감을 줌
- [[xlstm|xLSTM]] - 영감을 줌
