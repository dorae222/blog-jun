# Gated DeltaNet: Delta Rule과 게이팅을 결합한 선형 어텐션의 최전선

**Tsinghua University / Shanghai AI Lab** · **2024-12-05** · **SSM** · **MIT**

## 개요

Gated DeltaNet은 2024년 청화대학교와 상하이 AI Lab이 발표한 모델로, Delta Rule 기반 선형 어텐션에 입력 의존적 게이팅(data-dependent gating)을 결합하여 선형 복잡도 모델의 표현력 한계를 극복한 아키텍처이다. 이 모델은 두 가지 핵심 메커니즘 -- DeltaNet의 연상 기억 업데이트와 GLA의 선택적 망각 게이트 -- 을 단일 프레임워크로 통합한다.

DeltaNet의 delta rule은 연상 기억(associative memory)에서 오래된 연관을 정밀하게 수정하는 능력이 있지만, 장기 의존성 제어를 위한 명시적 망각 메커니즘이 부족했다. 반대로 GLA는 강력한 망각 게이트를 가지지만 메모리 내 특정 연관을 정밀하게 수정하는 능력은 제한적이었다. Gated DeltaNet은 이 두 접근법의 장점을 결합하여 7B 파라미터 기준 RetNet, GLA, Mamba 계열 대비 여러 언어 이해 및 생성 벤치마크에서 SoTA를 달성했다.

이 모델은 선형 어텐션 연구의 최전선에 위치하며, "메모리를 어떻게 관리할 것인가"라는 근본적 질문에 게이팅(전역적 망각)과 delta rule(지역적 수정)이라는 이중 메커니즘으로 답한다.

![Gated DeltaNet 아키텍처 - 입력 의존적 게이팅과 Delta Rule을 결합한 선형 어텐션 블록 구조](figures/architecture.svg)

*Figure 1: Gated DeltaNet 아키텍처 - DeltaNet의 연상 기억 업데이트(지역적 수정)와 GLA의 선택적 망각 게이트(전역적 망각)를 단일 프레임워크로 통합한 선형 복잡도 시퀀스 모델이다.*

## 아키텍처 상세

Gated DeltaNet의 핵심은 상태 업데이트 규칙에 있다.

### 게이팅 + Delta Rule 통합 업데이트

$$S_t = G_t \odot S_{t-1} + \beta_t(v_t - S_{t-1}k_t)k_t^T$$

이 수식에서 두 항의 역할을 분석하면 다음과 같다.

**전역적 망각 (GLA 계승)**: 첫 번째 항 $G_t \odot S_{t-1}$은 GLA에서 가져온 행렬 게이트이다. $G_t$는 입력에 의존적으로 계산되는 행렬 게이트로, 각 상태 차원별로 독립적인 망각률을 적용한다. 이 항은 "전체적으로 어떤 정보를 보존하고 어떤 정보를 잊을 것인가"를 제어한다.

**지역적 수정 (DeltaNet 계승)**: 두 번째 항 $\beta_t(v_t - S_{t-1}k_t)k_t^T$는 delta rule이다.

$$\underbrace{v_t}_{\text{실제 값}} - \underbrace{S_{t-1}k_t}_{\text{메모리 예측}} = \underbrace{\text{prediction error}}_{\text{예측 오차}}$$

$S_{t-1}k_t$는 현재 키 $k_t$에 대해 메모리가 예측하는 값이다. $(v_t - S_{t-1}k_t)$는 예측 오차이며, 이 오차를 기반으로 메모리를 정밀하게 수정한다. $\beta_t$는 학습 속도 스케일러로, 수정 강도를 제어한다.

### SSM과의 연결

Gated DeltaNet의 업데이트를 SSM 형태로 재해석하면 다음과 같다.

$$S_t = \underbrace{(G_t - \beta_t k_t k_t^T)}_{\bar{A}_t} \odot S_{t-1} + \underbrace{\beta_t v_t k_t^T}_{\bar{B}_t x_t}$$

상태 전이 행렬 $\bar{A}_t$가 게이팅과 delta rule의 조합으로 구성되며, 입력 의존적이다(선택적 메커니즘). 이는 Mamba의 선택적 SSM을 행렬 메모리 공간으로 확장한 것으로 볼 수 있다.

### 출력 계산

$$o_t = S_t q_t$$

쿼리 벡터 $q_t$로 상태에서 필요한 정보를 검색한다. 이는 Transformer의 어텐션이 Q, K, V로 정보를 검색하는 것과 기능적으로 유사하지만, 고정 크기 상태를 통해 $O(1)$ 메모리로 동작한다.

### Chunkwise Parallel 구현

학습 시 시퀀스를 청크 단위로 분할하여 병렬 처리한다. flash-linear-attention 라이브러리에 통합된 효율적인 CUDA 커널을 제공한다.

## 핵심 혁신

Gated DeltaNet의 핵심 혁신은 세 가지이다.

첫째, **이중 메모리 제어**이다. 게이팅을 통한 전역적 망각과 delta rule을 통한 지역적 수정을 동시에 수행한다. 이는 인간의 기억에서 전체적인 망각(시간 경과)과 특정 기억의 갱신(새로운 정보로 기존 인식 수정)이 동시에 일어나는 것과 유사하다.

둘째, **하드웨어 효율적 청크 병렬 계산**이다. Chunkwise parallelism을 지원하여 학습 시 병렬 처리, 추론 시 순환 모드로 $O(1)$ 메모리를 유지한다.

셋째, **스케일링 검증**이다. 340M부터 7B까지 다양한 규모에서 일관된 성능 향상을 확인했다.

## 벤치마크/성능

| 모델 (7B) | ARC-C | HellaSwag | PIQA | WinoGrande | 평균 |
|-----------|-------|-----------|------|------------|------|
| Gated DeltaNet | 44.2 | 72.1 | 78.6 | 68.3 | 65.8 |
| GLA | 41.5 | 70.4 | 77.8 | 66.9 | 64.2 |
| DeltaNet | 42.3 | 71.0 | 77.5 | 67.1 | 64.5 |
| Mamba-2 | 43.1 | 71.5 | 78.2 | 67.8 | 65.2 |
| RetNet | 40.8 | 69.8 | 77.1 | 66.2 | 63.5 |

| 모델 | 상태 업데이트 | 게이팅 | 메모리 수정 | 복잡도 |
|------|-------------|--------|-----------|--------|
| Gated DeltaNet | 게이팅 + Delta Rule | 행렬 게이트 | 예측 오차 기반 | $O(N)$ |
| GLA | 게이팅만 | 행렬 게이트 | 단순 덧셈 | $O(N)$ |
| DeltaNet | Delta Rule만 | 없음 | 예측 오차 기반 | $O(N)$ |
| RetNet | 지수 감쇠 | 고정 감쇠율 | 단순 덧셈 | $O(N)$ |
| Mamba | 선택적 SSM | 스칼라 게이트 | 이산화 기반 | $O(N)$ |

## 학습

SlimPajama, RedPajama 등 공개 코퍼스로 학습하며, H100/A100 GPU를 사용한다. LLaMA 학습 설정을 준수하여 공정한 비교를 보장한다. 청크 크기 64~256으로 chunkwise parallel 학습을 수행하며, 3B 모델 기준 약 300B 토큰을 학습한다.

다음은 Gated DeltaNet의 상태 업데이트를 구현한 예시이다.

```python
import torch
import torch.nn as nn

class GatedDeltaNetLayer(nn.Module):
    def __init__(self, d_model, d_key, d_value, n_heads):
        super().__init__()
        self.W_q = nn.Linear(d_model, n_heads * d_key)
        self.W_k = nn.Linear(d_model, n_heads * d_key)
        self.W_v = nn.Linear(d_model, n_heads * d_value)
        self.W_g = nn.Linear(d_model, n_heads * d_key * d_value)
        self.W_beta = nn.Linear(d_model, n_heads)  # 학습 속도

    def forward_recurrent(self, x_t, S_prev):
        """순환 모드: 게이팅 + Delta Rule"""
        q = self.W_q(x_t)  # 쿼리
        k = self.W_k(x_t)  # 키
        v = self.W_v(x_t)  # 값
        
        # 행렬 게이트 (전역적 망각)
        G = torch.sigmoid(self.W_g(x_t))
        # 학습 속도 스케일러
        beta = torch.sigmoid(self.W_beta(x_t))
        
        # 메모리 예측
        prediction = S_prev @ k  # S_{t-1} k_t
        # 예측 오차
        error = v - prediction
        
        # Gated DeltaNet 상태 업데이트
        # S_t = G_t * S_{t-1} + beta_t * error @ k_t^T
        S_t = G * S_prev + beta * torch.outer(error, k)
        
        # 출력: o_t = S_t @ q_t
        o_t = S_t @ q
        return o_t, S_t
```

## 관련 모델

Gated DeltaNet은 flash-linear-attention 라이브러리를 통해 실무에서 바로 사용할 수 있다. GLA와 DeltaNet의 결합이라는 명확한 설계 원칙은 향후 선형 어텐션 연구의 중요한 방향성을 제시하며, 순수 선형 어텐션 모델의 고유 한계인 정밀한 위치 기반 검색에서는 여전히 Transformer에 미치지 못하지만, Mamba-3 같은 하이브리드 접근법과의 결합도 기대되는 방향이다.

## 참고 자료

- 논문: [Gated Delta Networks: Improving Mamba2 with Delta Rule](https://arxiv.org/abs/2412.06464)
- 코드: [fla-org/flash-linear-attention](https://github.com/fla-org/flash-linear-attention)

## 관련 문서

- [[retnet|RetNet]] - 영감
