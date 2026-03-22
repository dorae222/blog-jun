---
title: "Mamba: Linear-Time Sequence Modeling with Selective State Spaces"
slug: mamba
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.421496+00:00"
architecture_entry: mamba
---

## 논문 개요

Transformer의 Self-Attention은 시퀀스 길이 $N$에 대해 $O(N^2)$의 시간 및 메모리 복잡도를 가집니다. 이는 긴 시퀀스를 처리할 때 심각한 병목이 됩니다. 이를 해결하기 위해 상태 공간 모델(State Space Model, SSM)이 주목받았지만, S4 등 기존 SSM은 시간 불변(time-invariant) 파라미터를 사용해 입력 내용에 따른 선택적 처리가 불가능했습니다.

Albert Gu와 Tri Dao(2023)가 발표한 **Mamba**는 **선택적 상태 공간(Selective State Space)**을 도입하여 이 문제를 해결합니다. 입력 데이터에 따라 SSM 파라미터가 동적으로 변화하여, 관련 정보를 선택적으로 기억하고 불필요한 정보를 필터링할 수 있습니다.

---

## 핵심 기여

1. **선택적 SSM**: 입력 의존적(input-dependent) SSM 파라미터로 내용 기반 추론 가능
2. **하드웨어 효율적 병렬 스캔**: GPU 메모리 계층을 활용한 재귀 연산의 효율적 구현
3. **단순화된 아키텍처**: 어텐션과 MLP 블록을 SSM 블록 하나로 대체
4. **선형 시간 복잡도**: 시퀀스 길이에 대해 $O(N)$ 추론, $O(N \log N)$ 학습

---

## 방법론 상세

### 연속 상태 공간 모델 (Continuous SSM)

기본 SSM은 선형 ODE(상미분방정식)로 정의됩니다:

$$h'(t) = A h(t) + B x(t)$$
$$y(t) = C h(t)$$

여기서 $h(t) \in \mathbb{R}^N$은 숨겨진 상태(hidden state), $x(t) \in \mathbb{R}$은 입력, $y(t) \in \mathbb{R}$은 출력입니다. $A, B, C$는 학습 가능한 파라미터 행렬입니다.

### 이산화 (Discretization)

연속 모델을 이산 시퀀스에 적용하기 위해 ZOH(Zero-Order Hold) 이산화를 적용합니다:

$$\bar{A} = \exp(\Delta A)$$
$$\bar{B} = (\Delta A)^{-1}(\exp(\Delta A) - I) \cdot \Delta B \approx \Delta B$$

이산화된 SSM:

$$h_t = \bar{A} h_{t-1} + \bar{B} x_t$$
$$y_t = C h_t$$

여기서 $\Delta$는 타임스텝 크기(step size)입니다.

### S4의 한계: 시간 불변 파라미터

S4 등 기존 SSM에서 $A, B, C, \Delta$는 **입력에 독립적인 고정 파라미터**입니다. 이는 Linear Attention과 수학적으로 동치이지만, 입력 내용에 따라 동적으로 처리할 수 없습니다.

예시 문제 - 선택적 복사(Selective Copy):
```
입력: [A, B, 0, 0, C, 0, D] (0은 노이즈)
목표: [A, B, C, D]          (관련 토큰만 선택)
```
시간 불변 SSM은 어떤 토큰이 중요한지 "선택"할 수 없어 이 태스크에서 실패합니다.

### 선택적 SSM (Selective SSM = S6)

Mamba의 핵심 혁신: $B, C, \Delta$를 **입력 $x$의 함수**로 만듭니다:

$$B_t = s_B(x_t) = \text{Linear}(x_t) \in \mathbb{R}^N$$
$$C_t = s_C(x_t) = \text{Linear}(x_t) \in \mathbb{R}^N$$
$$\Delta_t = s_\Delta(x_t) = \text{softplus}(\text{Linear}(x_t)) \in \mathbb{R}^D$$

$A$ 행렬만 입력 독립적으로 유지합니다 (HiPPO 초기화 사용).

$\Delta$의 역할:
- $\Delta_t$ **크면**: $\bar{A} \approx 0$, $\bar{B} \approx \Delta B$ → 현재 입력을 상태에 강하게 반영
- $\Delta_t$ **작으면**: $\bar{A} \approx I$, $\bar{B} \approx 0$ → 이전 상태 유지, 현재 입력 무시

이는 선택적 게이팅(selective gating)처럼 동작합니다.

### 하드웨어 효율적 병렬 스캔

선택적 SSM의 이산 재귀:

$$h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t$$

$\bar{A}_t$가 입력 의존적이므로 단순 컨볼루션으로 처리할 수 없습니다. 순차 계산(sequential scan)은 $O(N)$이지만 병렬화가 불가능합니다.

Mamba는 **병렬 접두사 스캔(parallel prefix scan)** 알고리즘을 사용합니다:

$$\text{prefix\_scan}([a_1, a_2, \ldots, a_N]) \rightarrow [a_1, a_1 a_2, \ldots, \prod_{i=1}^N a_i]$$

시간 복잡도: $O(N \log N)$ (GPU 병렬 환경에서 효율적)

**메모리 최적화**: 상태 행렬을 HBM(High Bandwidth Memory) 대신 SRAM(빠른 온칩 메모리)에 유지하여 메모리 IO 병목 해소. Flash Attention과 유사한 하드웨어 인식(hardware-aware) 접근법.

### Mamba 블록 아키텍처

```
입력 x ∈ ℝ^(B×L×D)
        │
   ┌────┴────┐
   │         │
  Linear    Linear    (확장: D → E, 보통 E=2D)
   │         │
  SSM     SiLU 활성화
   │         │
   └────×────┘        (element-wise 곱: 게이팅)
        │
    Linear (E → D)    (투영: E → D)
        │
      출력
```

Mamba 블록은 Transformer의 MHA + FFN을 대체하며, 단 하나의 블록으로 구성됩니다.

```python
class MambaBlock(nn.Module):
    def __init__(self, d_model, d_state=16, expand=2):
        super().__init__()
        d_inner = int(expand * d_model)
        
        self.in_proj = nn.Linear(d_model, d_inner * 2, bias=False)
        self.conv1d = nn.Conv1d(d_inner, d_inner, kernel_size=4, 
                                 groups=d_inner, padding=3)
        
        # S6 (선택적 SSM) 파라미터
        self.x_proj = nn.Linear(d_inner, d_state * 2 + 1)  # B, C, Delta
        self.dt_proj = nn.Linear(1, d_inner)
        self.A_log = nn.Parameter(...)  # 고정 구조
        
        self.out_proj = nn.Linear(d_inner, d_model, bias=False)
    
    def forward(self, x):
        B, L, D = x.shape
        xz = self.in_proj(x)  # (B, L, 2*E)
        x_branch, z = xz.chunk(2, dim=-1)
        
        # 선택적 SSM 적용
        y = self.selective_scan(x_branch)  # (B, L, E)
        
        # 게이팅
        output = y * F.silu(z)
        return self.out_proj(output)
```

### Transformer vs Mamba 비교

| 특성 | Transformer | Mamba |
|------|-------------|-------|
| 시간 복잡도 (추론) | $O(N^2 D)$ | $O(N D^2)$ |
| 메모리 복잡도 | $O(N^2)$ (KV 캐시) | $O(D^2)$ (고정 상태) |
| 컨텍스트 처리 | 전체 어텐션 | 압축된 상태 |
| 병렬 학습 | 완전 병렬 | 병렬 스캔 |
| 내용 기반 추론 | Self-Attention | 선택적 게이팅 |
| 긴 시퀀스 효율 | 낮음 | 높음 |

---

## 실험 결과

### 언어 모델링 (The Pile)

| 모델 | 파라미터 | Perplexity ↓ |
|------|---------|-------------|
| Transformer++ | 370M | 8.14 |
| Hyena | 370M | 8.38 |
| RetNet | 370M | 8.06 |
| **Mamba** | **370M** | **8.14** |
| **Mamba** | **1.4B** | **7.58** |

Mamba는 동일 파라미터의 Transformer와 동등한 Perplexity를 달성합니다.

### 추론 속도 (A100 GPU)

시퀀스 길이 1K~16K에서 Mamba의 추론 처리량:
- 16K 시퀀스에서 Transformer 대비 **5배 빠른 추론**
- 메모리 사용량: KV 캐시가 선형적으로 증가하는 Transformer와 달리 **상태 크기 고정**

### 긴 시퀀스 선택적 복사 태스크

- Mamba: 100% 정확도 (시퀀스 길이 4096까지)
- S4/H3: 실패
- Transformer: 제한된 컨텍스트에서만 성공

---

## 후속 연구

### Mamba-2 (2024)

구조적 상태 공간 이중성(SSD: Structured State Space Duality) 프레임워크 제안. Mamba의 선택적 SSM이 특수한 형태의 어텐션임을 증명하여 두 패러다임을 통합:

$$y = (M \odot L) x$$

여기서 $M$은 마스크 행렬, $L$은 학습된 행렬. Mamba-2는 Mamba 대비 2~8배 빠른 학습 속도 달성.

### Vision Mamba, VMamba

ViT의 Self-Attention을 선택적 SSM으로 대체하여 이미지 인식에 적용.

### Jamba, Zamba

Mamba와 Transformer를 혼합한 하이브리드 아키텍처.

---

## 의의 및 한계

### 의의

- **효율성**: 긴 시퀀스에서 Transformer 대비 선형 복잡도로 극적인 효율 향상
- **선택적 처리**: 입력 의존적 파라미터로 관련 정보만 선택하는 능력
- **하드웨어 최적화**: GPU 메모리 계층을 인식한 알고리즘 설계
- **범용성**: 언어, 비전, 오디오, DNA 등 다양한 시퀀스 모달리티에 적용 가능

### 한계

- **메모리 기반 처리의 한계**: 과거 정보를 고정 크기 상태로 압축하여 먼 과거 정보 손실 가능
- **In-Context Learning 열위**: Transformer의 KV 캐시 기반 ICL 능력에 비해 약함
- **구현 복잡성**: 하드웨어 효율적 스캔 알고리즘 구현이 복잡
- **학습 불안정**: 선택적 게이팅으로 인한 기울기 소실/폭발 위험

---

## 결론

Mamba는 상태 공간 모델에 "선택성(selectivity)"을 부여함으로써 Transformer의 핵심 장점인 내용 기반 추론 능력을 확보하면서도 선형 시간 복잡도를 유지하는 데 성공했습니다. 특히 수십만 토큰의 초장기 시퀀스 처리가 필요한 영역에서 Transformer를 대체하거나 보완할 수 있는 유망한 대안을 제시합니다. Mamba-2와 하이브리드 아키텍처로의 발전은 SSM과 Transformer의 융합이라는 새로운 패러다임을 열고 있습니다.