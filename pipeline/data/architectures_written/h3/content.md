# H3: SSM을 언어 모델링에 도입한 이중 상태 공간 아키텍처

**Stanford / Hazy Research** · **2022-12-29** · **Hybrid SSM** · **Apache-2.0**

## 개요

H3(Hungry Hungry Hippos)는 2022년 Stanford Hazy Research 그룹이 발표한 모델로, SSM(State Space Model)을 언어 모델링에 본격적으로 적용하려 한 첫 대규모 시도이다. S4가 Long Range Arena 같은 합성 벤치마크에서 뛰어난 성능을 보였지만, 실제 언어 모델링에서는 Transformer에 크게 뒤처지는 한계가 있었다. H3는 이 간극의 원인을 정밀하게 분석하고 해결책을 제시했다.

H3 연구진은 Transformer가 SSM보다 뛰어난 이유를 두 가지 핵심 능력으로 귀결시켰다. 첫째, **인접 토큰 비교(adjacent token comparison)** -- 바로 이전 토큰과 현재 토큰을 직접 비교하는 능력이다. 둘째, **연상 기억(associative recall)** -- 시퀀스 초반에 등장한 특정 키-값 쌍을 나중에 정확히 기억하고 검색하는 능력이다. S4의 LTI(Linear Time-Invariant) 특성으로는 이 두 가지를 동시에 달성하기 어려웠다.

H3는 이 두 능력을 SSM으로 구현하기 위해 이중 SSM 구조를 설계했다. GPT-2 규모에서 attention 레이어 하나만 유지하고 나머지를 H3로 대체하면 순수 Transformer 대비 perplexity 차이가 0.5 미만임을 보여, 하이브리드 접근법의 가능성을 최초로 입증했다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

H3 레이어는 두 개의 SSM을 직렬/병렬로 구성하는 독특한 구조를 가진다.

### Shift SSM

첫 번째 SSM은 이전 토큰을 현재 위치로 당기는 단순 이동(shift) 연산을 수행한다. 상태 전이 행렬 $A$가 단위 이동 행렬(shift matrix)로 설정되어 있어, 입력 시퀀스를 한 칸씩 밀어주는 효과를 낸다.

$$x'_t = \text{ShiftSSM}(x_t) \approx x_{t-1}$$

이는 bigram 통계를 포착하는 것과 유사하며, Transformer에서 인접 토큰을 비교하는 능력에 대응한다. SSM의 상태 방정식으로 표현하면 다음과 같다.

$$h_t = A_{\text{shift}} h_{t-1} + B_{\text{shift}} x_t, \quad A_{\text{shift}} = \begin{pmatrix} 0 & 0 & \cdots \\ 1 & 0 & \cdots \\ 0 & 1 & \cdots \end{pmatrix}$$

### 장거리 SSM

두 번째 SSM은 S4D 또는 S4 기반의 장거리 의존성을 포착하는 SSM이다. HiPPO 초기화를 사용하여 과거 입력의 압축된 표현을 유지한다.

$$h'(t) = Ah(t) + Bx(t), \quad y(t) = Ch(t)$$

이산화 후 컨볼루션 모드로 학습하며, 시퀀스 전체에 걸친 장거리 패턴을 포착한다.

### Multiplicative Gating

두 SSM의 출력을 element-wise 곱(Hadamard product)으로 결합한다. 이 multiplicative interaction이 H3의 표현력을 결정하는 핵심 요소이다.

$$y_t = \text{ShiftSSM}(x_t) \odot \text{LongSSM}(x_t)$$

Shift SSM의 출력이 인접 토큰 정보를, 장거리 SSM이 전역 컨텍스트를 제공하며, 이 둘의 곱이 "어떤 전역 정보를 인접 토큰 비교 결과로 게이팅할 것인가"를 결정한다. 이 구조는 어텐션의 QKV 메커니즘을 SSM으로 분해한 것으로 해석할 수 있다.

### FlashConv 알고리즘

IO-aware 컨볼루션 알고리즘을 도입해 GPU 메모리 계층(SRAM/HBM)을 최적화했다. FlashAttention과 동일한 원리로, 컨볼루션 커널의 물질화(materialization)를 피하고 on-the-fly 계산으로 메모리 사용량을 크게 줄였다.

## 핵심 혁신

H3의 핵심 혁신은 세 가지이다.

첫째, **SSM의 언어 모델링 한계 진단**이다. 기존 S4가 언어 모델링에서 실패하는 원인을 induction head와 associative recall이라는 두 가지 합성 태스크로 정량화했다.

둘째, **FlashConv 알고리즘**이다. GPU 메모리 계층을 최적화한 IO-aware 컨볼루션으로, FlashAttention과 동일한 원리를 SSM에 적용한 최초 사례이다.

셋째, **하이브리드 검증**이다. GPT-2 규모에서 attention 1개 + H3 나머지 구조로 순수 Transformer 대비 perplexity 차이가 0.5 미만임을 보였다. "소수의 어텐션 레이어가 SSM의 한계를 보완할 수 있다"는 하이브리드 접근법의 가능성을 최초로 입증한 것이다.

## 벤치마크/성능

| 모델 (125M) | Pile PPL↓ | Induction Head | Associative Recall |
|------------|-----------|----------------|-------------------|
| H3 | 12.1 | 98.5% | 89.2% |
| S4D | 14.6 | 12.3% | 15.7% |
| Transformer | 11.6 | 99.1% | 98.8% |
| H3 + 1 Attn | 11.8 | 99.0% | 97.5% |

H3는 S4D 대비 언어 모델링에서 큰 폭의 개선을 달성했으며, 어텐션 1개만 추가하면 순수 Transformer에 근접한다.

| 모델 | 접근법 | 토큰 믹싱 | 장거리 의존성 | 인접 토큰 비교 |
|------|--------|----------|-------------|---------------|
| H3 | 이중 SSM + Gating | Multiplicative | S4D SSM | Shift SSM |
| S4 | 단일 SSM | 컨볼루션 | HiPPO | 약함 |
| Hyena | 암묵적 컨볼루션 | Multiplicative | Long Conv | 학습된 필터 |
| Mamba | 선택적 SSM | 게이팅 | 선택적 상태 | 입력 의존 $\Delta$ |

## 학습

Pile 데이터셋으로 학습하며, GPT-NeoX 토크나이저를 사용한다. A100 80GB GPU 클러스터에서 시퀀스 길이 2048로 학습한다. FlashConv 커널로 메모리 효율을 최적화했다. 125M부터 2.7B까지 다양한 크기에서 실험하며, attention과 SSM의 최적 하이브리드 비율을 탐색했다.

다음은 H3의 이중 SSM + multiplicative gating 구조를 보여주는 예시이다.

```python
import torch
import torch.nn as nn

class H3Block(nn.Module):
    def __init__(self, d_model, ssm_size=64):
        super().__init__()
        self.shift_ssm = ShiftSSM(d_model, ssm_size)
        self.long_ssm = S4DLayer(d_model, ssm_size)  # HiPPO 초기화
        self.out_proj = nn.Linear(d_model, d_model)

    def forward(self, x):
        # Shift SSM: 인접 토큰 비교
        shift_out = self.shift_ssm(x)  # x_{t-1} 근사
        # Long SSM: 장거리 의존성
        long_out = self.long_ssm(x)
        # Multiplicative gating: 두 출력의 element-wise 곱
        gated = shift_out * long_out
        return self.out_proj(gated)

class ShiftSSM(nn.Module):
    """단위 이동 행렬 기반 SSM"""
    def forward(self, x):
        # 한 타임스텝 왼쪽으로 이동 (이전 토큰)
        return torch.cat([x[:, :1] * 0, x[:, :-1]], dim=1)
```

## 관련 모델

H3는 직접적인 프로덕션 사용보다는 후속 연구(Hyena, Mamba)의 이론적 토대로서의 가치가 크다. SSM 기반 언어 모델의 한계를 진단하고 하이브리드 접근법의 가능성을 보여줌으로써, 현재 SSM 생태계의 기반을 마련했다. H3에서 진단한 associative recall의 한계는 Mamba의 선택적 메커니즘 개발로 직접 이어졌으며, H3는 SSM 연구사에서 S4와 Mamba를 잇는 핵심 다리 역할을 했다.

## 참고 자료

- 논문: [Hungry Hungry Hippos: Towards Language Modeling with State Space Models](https://arxiv.org/abs/2212.14052)
- 코드: [HazyResearch/H3](https://github.com/HazyResearch/H3)

## 관련 문서

- [[s4|S4]] — 발전 기반
- [[hyena|Hyena]] — 후속 모델
- [[mamba|Mamba: Linear-Time Sequence Modeling with Selective State Spaces]] — 영감을 줌
