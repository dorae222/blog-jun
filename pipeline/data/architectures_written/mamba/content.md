# Mamba: 선택적 상태 공간 모델로 Transformer에 도전한 SSM의 전환점

**Carnegie Mellon University / Princeton University** · **2023-12-01** · **SSM** · **Apache-2.0**

## 개요

Mamba는 2023년 Albert Gu(CMU)와 Tri Dao(Princeton)가 발표한 모델로, SSM(State Space Model) 연구의 결정적 전환점이 된 아키텍처이다. 기존 S4, H3 등 SSM의 핵심 한계는 LTI(Linear Time-Invariant) 특성이었다. A, B, C, $\Delta$ 파라미터가 입력과 무관하게 고정되어 있어 콘텐츠 기반 추론이 어렵다는 근본적 문제가 있었다.

Mamba는 선택적 메커니즘(Selective Mechanism)을 도입해 $B$, $C$, $\Delta$ 파라미터를 입력에 따라 동적으로 결정함으로써 이 문제를 해결했다. 2.8B 크기에서 동일 규모 Transformer 기반 언어 모델과 동등하거나 우수한 perplexity를 달성하면서도 시퀀스 길이에 선형 복잡도를 유지한다. 추론 시 FlashAttention 대비 5배 빠른 처리 속도와 $O(1)$ 메모리 사용이라는 실용적 이점을 제공하며, "SSM은 언어 모델에 부적합하다"는 기존 인식을 완전히 뒤집었다.

Mamba는 SSM 연구사에서 가장 영향력 있는 단일 모델로, 이후 Mamba-2(SSD), Mamba-3(하이브리드), Griffin(Google DeepMind), Jamba(AI21) 등 수많은 후속 연구와 산업 적용의 기반이 되었다.

![Mamba 아키텍처 - 선택적 메커니즘으로 B, C, Delta 파라미터를 입력 의존적으로 결정하는 SSM 블록 구조](figures/architecture.svg)

*Figure 1: Mamba 아키텍처 - 기존 SSM의 LTI 한계를 극복하여 B, C, Delta를 입력에 따라 동적으로 결정하는 선택적 SSM 블록으로, 시퀀스 길이에 선형 복잡도와 O(1) 추론 메모리를 달성한다.*

## 아키텍처 상세

Mamba의 핵심은 선택적 SSM(Selective State Space Model)이다.

### 기존 SSM의 한계: LTI 시스템

전통적인 SSM(S4 등)은 다음과 같은 연속 시간 상태 방정식으로 정의된다.

$$h'(t) = Ah(t) + Bx(t)$$
$$y(t) = Ch(t) + Dx(t)$$

ZOH(Zero-Order Hold)로 이산화하면 다음과 같다.

$$h_t = \bar{A}h_{t-1} + \bar{B}x_t, \quad y_t = Ch_t$$

여기서 $\bar{A} = \exp(\Delta A)$, $\bar{B} = (\Delta A)^{-1}(\exp(\Delta A) - I) \cdot \Delta B$이다. S4에서는 $A$, $B$, $C$, $\Delta$가 모두 입력과 무관한 고정 파라미터였다. 이 LTI 특성 덕분에 컨볼루션 모드(FFT 병렬 학습)가 가능하지만, 모든 입력을 동일하게 처리한다는 근본적 한계가 있다.

### 선택적 메커니즘(Selective Mechanism)

Mamba는 $B$, $C$, $\Delta$를 입력 $x$의 선형 프로젝션으로 계산하여 입력 의존적으로 만들었다.

$$B_t = \text{Linear}_B(x_t) \in \mathbb{R}^N$$
$$C_t = \text{Linear}_C(x_t) \in \mathbb{R}^N$$
$$\Delta_t = \text{softplus}(\text{Linear}_\Delta(x_t)) \in \mathbb{R}^D$$

$\Delta_t$(이산화 스텝 크기)가 특히 중요하다. $\Delta_t$가 크면 $\bar{A}_t = \exp(\Delta_t A)$의 감쇠가 커져 과거 상태를 빠르게 잊고 현재 입력에 집중한다. $\Delta_t$가 작으면 과거 상태를 유지한다. 이 메커니즘은 Transformer의 soft attention과 기능적으로 유사하며, 모델이 "이 토큰은 상태에 기록하고, 저 토큰은 무시해라"라는 판단을 내릴 수 있게 한다.

### 하드웨어 친화적 구현

선택적 메커니즘은 LTI 특성을 깨뜨리므로, S4의 FFT 기반 컨볼루션이 불가능해진다. 이를 해결하기 위해 Mamba는 **parallel associative scan**을 도입했다. 순환 연산 $h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t$는 결합 법칙(associativity)을 만족하므로 이진 트리 구조로 병렬화할 수 있다.

$$\text{scan}(h_0, [(\bar{A}_1, \bar{B}_1 x_1), \ldots, (\bar{A}_L, \bar{B}_L x_L)])$$

또한 재계산(recomputation)과 커널 융합(kernel fusion)을 통해 GPU HBM-SRAM 간 데이터 이동을 최소화했다.

### Mamba 블록

Mamba 블록은 MLP와 SSM 경로를 병렬로 두고 multiplicative gate로 결합하는 구조이다.

$$x_{\text{ssm}} = \text{SSM}(\text{Conv1D}(\text{Linear}(x)))$$
$$x_{\text{gate}} = \text{SiLU}(\text{Linear}(x))$$
$$y = \text{Linear}(x_{\text{ssm}} \odot x_{\text{gate}})$$

Transformer의 MHA+FFN 이중 잔차 구조 대신, 단일 Mamba 블록만 반복하는 간결한 설계를 채택했다.

## 핵심 혁신

Mamba의 핵심 혁신은 세 가지이다.

첫째, **선택적 메커니즘**이다. LTI SSM의 근본적 한계를 입력 의존적 파라미터화로 극복했다. 이는 SSM 역사에서 가장 중요한 단일 기여로 평가된다.

둘째, **하드웨어 인식 알고리즘**이다. 이론적 복잡도뿐 아니라 실제 GPU 하드웨어의 메모리 계층(SRAM vs HBM)을 고려한 구현으로, FlashAttention 대비 5배 빠른 추론 속도를 달성했다.

셋째, **단순화된 아키텍처**이다. Transformer의 이중 잔차(MHA+FFN) 대신 단일 Mamba 블록만 반복하는 설계로 파라미터 효율과 구현 단순성을 동시에 제공한다.

## 벤치마크/성능

| 모델 | 파라미터 | Pile PPL↓ | HellaSwag | PIQA | WinoGrande |
|------|---------|-----------|-----------|------|------------|
| Mamba | 2.8B | 6.22 | 66.1 | 77.5 | 63.5 |
| Pythia | 2.8B | 6.73 | 59.3 | 75.1 | 60.5 |
| GPT-Neo | 2.7B | 7.50 | 55.7 | 73.2 | 57.6 |
| RWKV-4 | 3B | 6.85 | 58.8 | 74.3 | 59.8 |
| Mamba | 1.4B | 7.31 | 59.5 | 75.8 | 61.2 |

| 모델 | 파라미터 의존성 | 복잡도 | 학습 병렬화 | 추론 상태 |
|------|--------------|--------|-----------|----------|
| Mamba | 입력 의존적 | $O(N)$ | Parallel scan | $O(1)$ |
| S4 | 입력 무관(LTI) | $O(N \log N)$ | FFT 컨볼루션 | $O(1)$ |
| H3 | 부분적 | $O(N \log N)$ | FlashConv | $O(1)$ |
| Transformer | 입력 의존적 | $O(N^2)$ | 완전 병렬 | $O(N)$ KV cache |
| RetNet | 입력 무관 | $O(N)$ | 병렬 모드 | $O(1)$ |

## 학습

Pile 데이터셋으로 학습하며, GPT-NeoX 토크나이저를 사용한다. A100 80GB GPU에서 FlashMamba CUDA 커스텀 커널로 속도를 최적화했다. 배치 크기 1M 토큰/스텝으로 학습하며, 2.8B 모델은 300B 토큰으로 학습되었다.

다음은 Mamba의 선택적 SSM 순환 추론을 PyTorch로 구현한 예시이다.

```python
import torch
import torch.nn.functional as F

def selective_ssm_recurrence(x, A, B_proj, C_proj, dt_proj):
    """Mamba 선택적 SSM의 순환 모드 추론"""
    B, L, D = x.shape
    N = A.shape[0]  # 상태 차원
    h = torch.zeros(B, D, N, device=x.device)
    outputs = []
    
    for t in range(L):
        # 입력 의존적 파라미터 계산 (선택적 메커니즘)
        B_t = B_proj(x[:, t])          # (B, N)
        C_t = C_proj(x[:, t])          # (B, N)
        dt = F.softplus(dt_proj(x[:, t]))  # (B, D)
        
        # 이산화
        A_bar = torch.exp(dt.unsqueeze(-1) * A)  # (B, D, N)
        B_bar = dt.unsqueeze(-1) * B_t.unsqueeze(1)  # (B, D, N)
        
        # 상태 업데이트
        h = A_bar * h + B_bar * x[:, t].unsqueeze(-1)
        y_t = (h * C_t.unsqueeze(1)).sum(-1)  # (B, D)
        outputs.append(y_t)
    
    return torch.stack(outputs, dim=1)
```

## 관련 모델

Mamba는 Hugging Face에서 다양한 크기의 사전학습 모델을 사용할 수 있다. 긴 시퀀스 추론이 필요한 코드 생성, 문서 요약, 대화형 AI 등에서 Transformer 대비 메모리 효율적인 대안을 제공한다. Mamba의 in-context retrieval 한계는 Mamba-2의 SSD 프레임워크와 Mamba-3의 하이브리드 접근법으로 점진적으로 개선되고 있다. Jamba(AI21), Zamba(Zyphra) 등 상용 모델에서도 Mamba 레이어를 활용하고 있다.

## 참고 자료

- 논문: [Mamba: Linear-Time Sequence Modeling with Selective State Spaces](https://arxiv.org/abs/2312.00752)
- 코드: [state-spaces/mamba](https://github.com/state-spaces/mamba)

## 관련 문서

- [[s4|S4]] - 발전 기반
- [[mamba-2|Mamba-2]] - 후속 모델
- [[h3|H3]] - 영감
- [[griffin|Griffin]] - 영감을 줌
- [[jamba|Jamba: A Hybrid Transformer-Mamba Language Model]] - 영감을 줌
