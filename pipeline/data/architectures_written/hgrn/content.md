# HGRN: 계층적 게이팅으로 다중 시간 스케일을 포착하는 순환 네트워크

**Shanghai AI Lab / Tsinghua University** · **2023-11-09** · **SSM** · **MIT**

## 개요

HGRN(Hierarchically Gated Recurrent Network)은 2023년 상하이 AI Lab과 청화대학교가 발표한 모델로, 선형 RNN에 계층적 망각 게이트(hierarchical forget gate)를 도입하여 단거리와 장거리 의존성을 동시에 효과적으로 포착하는 아키텍처이다.

기존 선형 RNN 모델들(RWKV, RetNet 등)은 모든 레이어에서 동일한 시간 스케일의 망각을 적용한다. 이는 얕은 레이어도 깊은 레이어도 같은 속도로 정보를 잊어버린다는 의미이다. 그러나 자연어에는 명확한 정보 계층 구조가 존재한다. 단어 수준의 지역적 패턴(구문론)부터 문단 수준의 전역적 의미(담화 구조)까지, 서로 다른 시간 스케일의 정보가 동시에 흐른다.

HGRN은 이 관찰에서 출발하여 레이어 깊이에 따라 망각 게이트의 동작 범위를 차별화했다. 얕은 레이어는 빠른 망각(단거리 패턴 포착), 깊은 레이어는 느린 망각(장거리 의존성 포착)으로 자연스럽게 분화된다. 이 계층적 설계로 SSM/선형 어텐션 계열 모델 중 언어 모델링에서 경쟁력 있는 성능을 달성했다.

신호 처리 관점에서 HGRN은 **멀티-스케일 분석(multi-resolution analysis)**과 유사한 원리를 따른다. 얕은 레이어가 고주파 성분(지역적 패턴)을, 깊은 레이어가 저주파 성분(전역적 의미)을 담당하는 자연스러운 역할 분화가 일어난다.

![HGRN의 신경 아키텍처 구조 — HGRN 블록, HGRU 토큰 믹서, HRU 순환 유닛의 3단계 구성](figures/fig_2.png)
*Figure 1: HGRN 아키텍처 — 각 레이어는 HGRU(토큰 믹서)와 GLU(채널 믹서)로 구성된다. HRU 내부에서 레이어별 하한값 $\gamma^k$가 적용된 계층적 망각 게이트를 통해 복소수 도메인의 선형 순환 연산을 수행한다. (Source: Qin et al., 2023)*

![HGRN 아키텍처 — 레이어 깊이에 따라 망각 게이트를 차별화하는 계층적 순환 네트워크 구조](figures/architecture.svg)

*Figure 2: HGRN 전체 아키텍처 — 얕은 레이어는 빠른 망각(단거리 패턴), 깊은 레이어는 느린 망각(장거리 의존성)으로 자연스럽게 분화되는 계층적 게이팅 메커니즘을 적용한다.*

## 아키텍처 상세

### 상태 업데이트 수식

HGRN 블록의 상태 업데이트는 다음과 같다.

$$h_t = f_t \odot h_{t-1} + i_t \odot \tilde{h}_t$$

여기서 $f_t$는 forget gate, $i_t$는 input gate, $\tilde{h}_t$는 후보 상태이다.

### 계층적 망각 게이트

핵심은 $f_t$의 계산 방식에 있다. 레이어 인덱스 $l$에 따라 forget gate의 하한값(lower bound)을 다르게 설정한다.

$$f_t^{(l)} = \sigma(W_f^{(l)} x_t + b_f^{(l)}) \cdot (1 - \alpha_l) + \alpha_l$$

여기서 $\alpha_l$은 레이어 $l$의 하한값으로, 깊은 레이어일수록 큰 값을 가진다. 구체적으로 선형 스케줄을 사용한다.

$$\alpha_l = \alpha_{\min} + \frac{l}{L-1}(\alpha_{\max} - \alpha_{\min})$$

예를 들어 $\alpha_{\min} = 0.0$(첫 번째 레이어, 빠른 망각), $\alpha_{\max} = 0.9$(마지막 레이어, 매우 느린 망각)으로 설정하면 다음과 같은 동작이 일어난다.

| 레이어 | $\alpha_l$ | $f_t$ 범위 | 역할 |
|--------|-----------|-----------|------|
| 0 (얕은) | 0.0 | [0, 1] | 빠른 망각, 단어/구문 패턴 |
| L/4 | 0.225 | [0.225, 1] | 중간 망각, 절 수준 패턴 |
| L/2 | 0.45 | [0.45, 1] | 느린 망각, 문장 수준 의미 |
| L-1 (깊은) | 0.9 | [0.9, 1] | 매우 느린 망각, 문단/담화 |

![얕은 레이어(Layer 1)의 망각률 분포 — 낮은 망각률에 집중되어 단거리 패턴 포착](figures/fig_10_1.png)
*Figure 3: 레이어별 망각률 분포 (Layer 1) — 얕은 레이어에서는 망각률이 0.3~0.6 범위에 집중되어 빠른 정보 갱신(단거리 패턴 포착)이 이루어진다. 깊은 레이어로 갈수록 분포가 높은 망각률(0.9~1.0) 쪽으로 이동한다. (Source: Qin et al., 2023)*

### 게이트 제약 조건

업데이트 게이트와 망각 게이트의 합이 1이 되는 제약이 적용된다.

$$i_t = 1 - f_t$$

이 제약은 상태의 크기를 안정적으로 유지하는 역할을 한다. SSM 관점에서 이는 이산화 시 상태 보존 조건과 유사하다.

### SSM과의 연결

HGRN의 상태 업데이트를 SSM 형태로 재해석하면 다음과 같다.

$$h_t = \underbrace{f_t}_{\bar{A}_t} \odot h_{t-1} + \underbrace{(1-f_t) \odot \tilde{h}_t}_{\bar{B}_t x_t}$$

이는 Mamba의 선택적 SSM $h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t$와 구조적으로 동일하다. 차이점은 HGRN이 $\bar{A}_t$의 하한을 레이어별로 제약한다는 것이다.

또한 복소수 값 상태를 사용하여 표현력을 높였다. 복소수 상태는 진동(oscillation) 패턴을 자연스럽게 표현할 수 있어, 주기적 패턴이 중요한 태스크에서 유리하다.

![얕은 레이어의 토큰 믹싱 행렬 — 대각선 근처에 집중된 지역적 어텐션 패턴](figures/fig_29_1.png)
*Figure 4(a): 토큰 믹싱 행렬 (Layer 1) — 얕은 레이어에서는 대각선 근처에 어텐션이 집중되어 지역적 패턴(단어/구문 수준)을 처리한다. (Source: Qin et al., 2023)*

![깊은 레이어의 토큰 믹싱 행렬 — 넓은 범위의 장거리 의존성을 포착하는 패턴](figures/fig_29_6.png)
*Figure 4(f): 토큰 믹싱 행렬 (깊은 레이어) — 깊은 레이어에서는 어텐션이 넓은 범위로 확산되어 문단/담화 수준의 장거리 의존성을 포착한다. 계층적 게이팅의 효과를 시각적으로 확인할 수 있다. (Source: Qin et al., 2023)*

## 핵심 혁신

HGRN의 핵심 혁신은 두 가지이다.

첫째, **계층적 시간 스케일 분화**이다. 레이어 깊이에 따라 시간 스케일을 자동으로 분화시키는 간단하지만 효과적인 설계이다. 하한값 $\alpha_l$이라는 하나의 하이퍼파라미터만으로 구현되므로 추가 비용이 거의 없다.

둘째, **청크 단위 병렬 계산**이다. 순환 연산의 순차적 특성을 극복하기 위해, 시퀀스를 청크로 분할하고 청크 내부에서는 병렬 계산, 청크 간에는 순환 전파를 수행한다.

## 벤치마크/성능

| 모델 (1.3B) | Pile PPL↓ | ARC-E | LAMBADA | WikiText PPL↓ |
|------------|-----------|-------|---------|---------------|
| HGRN | 8.42 | 62.3 | 68.5 | 7.95 |
| RetNet | 8.67 | 60.1 | 66.2 | 8.31 |
| RWKV-4 | 8.54 | 61.0 | 67.1 | 8.12 |
| S4D | 9.85 | 55.2 | 58.3 | 9.67 |

| 모델 | 망각 게이트 | 시간 스케일 | 상태 유형 | 게이트 제약 |
|------|-----------|-----------|---------|------------|
| HGRN | 계층적 하한 | 레이어별 분화 | 복소수 | $i + f = 1$ |
| RWKV | 균일 감쇠 | 모든 레이어 동일 | 실수 | 없음 |
| RetNet | 고정 $\gamma$ | 헤드별 차이 | 실수 | 없음 |
| GLA | 입력 의존 | 동적 | 실수 행렬 | 없음 |
| Mamba | 선택적 $\Delta$ | 동적 | 실수 | 없음 |

HGRN은 RetNet과 RWKV-4 대비 일관되게 더 낮은 perplexity를 기록한다. 특히 장거리 의존성이 중요한 LAMBADA에서 두드러진다.

## 학습

RedPajama 데이터셋으로 학습하며, A100 GPU를 사용한다. SwiGLU FFN을 적용하고 LLaMA 기반 학습 파이프라인을 준용한다. 1.3B 모델 기준 200B 토큰으로 학습한다. 2024년에 발표된 HGRN2는 확장성을 개선한 후속 버전이다.

다음은 HGRN의 계층적 망각 게이트를 구현한 예시이다.

```python
import torch
import torch.nn as nn

class HGRNLayer(nn.Module):
    def __init__(self, d_model, layer_idx, total_layers,
                 alpha_min=0.0, alpha_max=0.9):
        super().__init__()
        # 계층적 하한값 계산
        self.alpha = alpha_min + layer_idx / (total_layers - 1) * \
                     (alpha_max - alpha_min)
        self.W_f = nn.Linear(d_model, d_model)
        self.W_h = nn.Linear(d_model, d_model)

    def forward_recurrent(self, x_t, h_prev):
        """HGRN 순환 모드"""
        # 계층적 forget gate
        # f_t = sigmoid(W_f x_t) * (1 - alpha) + alpha
        f_raw = torch.sigmoid(self.W_f(x_t))
        f_t = f_raw * (1 - self.alpha) + self.alpha
        
        # Input gate: i_t = 1 - f_t (보존 제약)
        i_t = 1 - f_t
        
        # 후보 상태
        h_tilde = self.W_h(x_t)
        
        # 상태 업데이트
        h_t = f_t * h_prev + i_t * h_tilde
        return h_t

# 전체 HGRN 스택 구성
def build_hgrn_stack(d_model, n_layers):
    return nn.ModuleList([
        HGRNLayer(d_model, l, n_layers) for l in range(n_layers)
    ])
```

## 관련 모델

HGRN은 flash-linear-attention 라이브러리를 통해 사용할 수 있다. 다양한 시간 스케일의 패턴을 포착해야 하는 시계열 분석, 음성 처리, 장문 텍스트 이해 등에 적합하다. 계층적 게이팅의 하한값 $\alpha_l$이 학습 전에 고정되는 하이퍼파라미터라는 한계는 후속 연구인 HGRN2에서 완화되었다. HGRN은 "레이어 깊이에 따른 시간 스케일 분화"라는 직관적이고 효과적인 설계 원칙을 확립한 모델이다.

## 참고 자료

- 논문: [HGRN: Efficiently Modeling Long Sequences with Linear RNNs](https://arxiv.org/abs/2311.04823)
- 코드: [fla-org/flash-linear-attention](https://github.com/fla-org/flash-linear-attention)

## 관련 문서

- [[s4|S4]] — 영감
