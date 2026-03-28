# xLSTM: LSTM의 발명자가 현대 LLM 시대에 맞게 재설계한 확장 LSTM

**NXAI / JKU Linz (Sepp Hochreiter)** · **2024-05-07** · **SSM** · **NXAI Open License (비상업적 오픈소스)**

## 개요

xLSTM(Extended Long Short-Term Memory)은 2024년 LSTM의 발명자 Sepp Hochreiter가 NXAI 연구소와 JKU Linz와 함께 발표한 모델로, 1997년에 탄생한 고전 LSTM을 현대 LLM 설계 원칙에 맞게 근본적으로 재설계한 아키텍처이다. 30년 가까운 세월 동안 LSTM은 RNN의 대명사로 군림했지만, Transformer의 등장 이후 주류에서 밀려났다. xLSTM은 "LSTM이 현대 기술로 무장하면 어떻게 될까?"라는 질문에 답한다.

xLSTM은 LSTM의 핵심 한계였던 스칼라 메모리 셀을 행렬 메모리로 확장한 mLSTM(matrix LSTM)과 안정적인 지수 게이팅(exponential gating)을 가진 sLSTM(scalar LSTM) 두 블록을 조합한다. Mamba, RWKV 등 SSM 계열이 제어 이론에서, RetNet이 어텐션 변형에서 출발한 것과 달리, xLSTM은 LSTM의 게이팅 이론을 직접 확장하는 독자적인 경로를 취한다.

같은 파라미터 수의 Transformer 및 Mamba 대비 언어 모델링 perplexity에서 경쟁력 있는 성능을 달성했으며, LSTM 기반 모델이 대형 언어 모델 시대에도 유효함을 증명한 연구이다. 30년간 축적된 LSTM 연구의 통찰을 현대적으로 재활용했다는 점에서 학술적 의의가 크다.

![xLSTM 아키텍처 — mLSTM(행렬 메모리)과 sLSTM(지수 게이팅)을 조합한 확장 LSTM 구조](figures/architecture.svg)

*Figure 1: xLSTM 아키텍처 — LSTM의 스칼라 메모리 셀을 행렬 메모리로 확장한 mLSTM과 지수 게이팅의 sLSTM 블록을 조합하여, 현대 LLM 시대에서도 경쟁력 있는 언어 모델링 성능을 달성한다.*

## 아키텍처 상세

xLSTM은 두 가지 핵심 블록으로 구성된다.

### sLSTM (scalar LSTM)

기존 LSTM에 두 가지 핵심 개선을 추가했다.

**지수 게이팅(Exponential Gating)**: 기존 LSTM의 sigmoid 게이트를 지수 함수 기반 게이트로 교체했다.

$$f_t = \exp(\tilde{f}_t), \quad i_t = \exp(\tilde{i}_t)$$

sigmoid는 출력 범위가 $[0, 1]$로 제한되어 많은 타임스텝에 걸쳐 곱해지면 기울기가 급격히 소실된다. 수학적으로 $T$ 스텝 후의 기울기 크기는 다음과 같다.

$$\prod_{t=1}^{T} \sigma(\tilde{f}_t) \leq \left(\frac{1}{2}\right)^T \to 0 \quad \text{(sigmoid)}$$
$$\prod_{t=1}^{T} \exp(\tilde{f}_t) = \exp\left(\sum_{t=1}^{T} \tilde{f}_t\right) \quad \text{(exponential)}$$

지수 함수는 이론적으로 임의의 큰 값을 가질 수 있어 장거리 의존성 포착에 유리하다.

**안정화 트릭**: 셀 상태의 크기가 발산하는 것을 방지하기 위해 log-space 계산과 정규화를 결합한다.

$$m_t = \max(\tilde{f}_t + m_{t-1}, \tilde{i}_t)$$
$$f_t' = \exp(\tilde{f}_t + m_{t-1} - m_t), \quad i_t' = \exp(\tilde{i}_t - m_t)$$

### mLSTM (matrix LSTM)

LSTM의 스칼라 셀 상태를 행렬 메모리로 확장한 것이 핵심이다.

$$C_t = f_t \odot C_{t-1} + i_t \odot v_t k_t^T$$
$$n_t = f_t \odot n_{t-1} + i_t \odot k_t$$
$$h_t = o_t \odot \frac{C_t q_t}{\max(|n_t^T q_t|, 1)}$$

여기서 $C_t \in \mathbb{R}^{d_k \times d_v}$가 행렬 메모리이며, $v_t k_t^T$(외적)로 키-값 쌍을 저장한다. 조회 시에는 $C_t q_t$로 쿼리에 해당하는 값을 검색한다. $n_t$는 정규화 항이다.

SSM과의 연결을 명확히 하면, mLSTM의 상태 업데이트는 GLA와 구조적으로 유사하다.

$$\underbrace{C_t = f_t \odot C_{t-1} + i_t \odot v_t k_t^T}_{\text{mLSTM}} \quad \leftrightarrow \quad \underbrace{S_t = G_t \odot S_{t-1} + k_t^T v_t}_{\text{GLA}}$$

차이점은 mLSTM이 지수 게이팅을 사용하고, GLA가 sigmoid 게이팅을 사용한다는 것이다. 이 구조는 본질적으로 어텐션의 KV 캐시를 고정 크기 행렬로 압축한 것으로 볼 수 있다.

### xLSTM 블록 구성

mLSTM이 주요 시퀀스 처리를, sLSTM이 보조 게이팅을 담당한다. 이를 residual connection과 LayerNorm으로 연결하여 xLSTM 블록을 형성한다. 추론 시 $O(1)$ 메모리와 $O(N)$ 시간 복잡도를 달성한다.

## 핵심 혁신

xLSTM의 핵심 혁신은 세 가지이다.

첫째, **행렬 메모리**이다. 스칼라 셀 상태를 행렬로 확장하여 어텐션과 유사한 KV 저장/검색 능력을 순환 모델에 부여했다. 이는 GLA, RetNet 등의 KV 상태와 유사하지만, LSTM의 게이팅 메커니즘과 결합되었다는 점에서 차별화된다.

둘째, **지수 게이팅**이다. sigmoid 대신 지수 함수 기반 게이트를 사용하여 기울기 소실 문제를 근본적으로 완화했다.

셋째, **LSTM 이론적 토대**이다. 30년간 축적된 LSTM 연구의 통찰을 활용할 수 있다는 장점이 있다.

## 벤치마크/성능

| 모델 (1.3B) | SlimPajama PPL↓ | HellaSwag | PIQA | WinoGrande |
|------------|-----------------|-----------|------|------------|
| xLSTM | 6.85 | 62.4 | 76.5 | 60.8 |
| Mamba | 6.78 | 63.1 | 76.8 | 61.2 |
| Transformer++ | 6.62 | 65.2 | 78.1 | 62.5 |
| RWKV-4 | 7.12 | 59.8 | 74.3 | 58.5 |
| RetNet | 7.05 | 60.5 | 75.1 | 59.2 |

| 모델 | 메모리 유형 | 게이팅 | 이론적 기반 | 병렬화 |
|------|-----------|--------|-----------|--------|
| xLSTM | 행렬 + 스칼라 | 지수 게이팅 | LSTM | Chunkwise |
| Mamba | 벡터 | 선택적 $\Delta$ | SSM | Parallel scan |
| GLA | 행렬 | 입력 의존 게이트 | 선형 어텐션 | Chunkwise |
| RWKV | 벡터 | WKV 감쇠 | RNN-Transformer 하이브리드 | 시간축 병렬 |
| RetNet | 행렬 | 고정 감쇠 | 어텐션 변형 | 완전 병렬 |

xLSTM은 Mamba와 경쟁적인 성능을 보이며, RetNet과 RWKV-4를 일관되게 능가한다.

## 학습

SlimPajama 데이터셋으로 학습하며(300B 토큰), A100 GPU를 사용한다. GPT-NeoX 기반 토크나이저를 적용하고, Adam 옵티마이저와 코사인 학습률 스케줄을 사용한다. 1.3B 모델을 기준으로 Mamba 1.3B, Transformer++ 1.3B와 동일한 설정에서 직접 비교 실험을 수행했다.

다음은 mLSTM의 행렬 메모리 업데이트와 지수 게이팅을 구현한 예시이다.

```python
import torch
import torch.nn as nn

class mLSTM(nn.Module):
    """행렬 메모리를 가진 확장 LSTM"""
    def __init__(self, d_model, d_key, d_value):
        super().__init__()
        self.W_q = nn.Linear(d_model, d_key)
        self.W_k = nn.Linear(d_model, d_key)
        self.W_v = nn.Linear(d_model, d_value)
        self.W_f = nn.Linear(d_model, 1)  # forget gate (pre-exp)
        self.W_i = nn.Linear(d_model, 1)  # input gate (pre-exp)
        self.W_o = nn.Linear(d_model, d_value)  # output gate

    def forward_recurrent(self, x_t, C_prev, n_prev, m_prev):
        """mLSTM 순환 추론"""
        q = self.W_q(x_t)  # 쿼리
        k = self.W_k(x_t)  # 키
        v = self.W_v(x_t)  # 값
        
        # 지수 게이팅 (안정화 트릭 포함)
        f_tilde = self.W_f(x_t).squeeze(-1)
        i_tilde = self.W_i(x_t).squeeze(-1)
        
        # 안정화: m_t = max(f_tilde + m_{t-1}, i_tilde)
        m_t = torch.max(f_tilde + m_prev, i_tilde)
        f_t = torch.exp(f_tilde + m_prev - m_t)
        i_t = torch.exp(i_tilde - m_t)
        
        # 행렬 메모리 업데이트
        # C_t = f_t * C_{t-1} + i_t * v @ k^T
        C_t = f_t * C_prev + i_t * torch.outer(v, k)
        n_t = f_t * n_prev + i_t * k
        
        # 출력: o_t * (C_t @ q_t) / max(|n_t^T q_t|, 1)
        o_t = torch.sigmoid(self.W_o(x_t))
        numerator = C_t @ q
        denominator = torch.clamp(torch.abs(n_t @ q), min=1.0)
        h_t = o_t * (numerator / denominator)
        
        return h_t, C_t, n_t, m_t
```

## 관련 모델

xLSTM은 GitHub(NX-AI/xlstm)에서 사용할 수 있다. LSTM에 익숙한 연구자가 현대적 언어 모델을 구축하려 할 때 자연스러운 선택지이다. sLSTM의 지수 게이팅이 수치적으로 불안정할 수 있다는 한계와, NXAI Open License(비상업적)로 상업적 사용에 제약이 있다는 점이 실용적 한계이다. 그러나 LSTM의 발명자가 직접 현대적 재설계를 시도했다는 학술적 의의는 크며, 행렬 메모리와 지수 게이팅이라는 두 가지 아이디어는 후속 연구에 영향을 미치고 있다.

## 참고 자료

- 논문: [xLSTM: Extended Long Short-Term Memory](https://arxiv.org/abs/2405.04517)
- 코드: [NX-AI/xlstm](https://github.com/NX-AI/xlstm)

## 관련 문서

- [[s4|S4]] — 영감
