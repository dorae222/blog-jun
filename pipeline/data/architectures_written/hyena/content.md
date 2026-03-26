# Hyena: 암묵적 장거리 컨볼루션으로 어텐션을 완전 대체한 서브-이차 모델

**Stanford / Hazy Research / Together AI** · **2023-02-21** · **SSM** · **Apache-2.0**

## 개요

Hyena는 2023년 Stanford Hazy Research가 발표한 모델로, attention을 완전히 제거하고 암묵적 장거리 컨볼루션(implicit long convolution)만으로 Transformer의 표현력에 근접하려 한 서브-이차(sub-quadratic) 아키텍처이다. H3에서 한 발 더 나아가 MHA(Multi-Head Attention)를 단 한 개도 사용하지 않으면서 GPT 계열 모델과 경쟁할 수 있음을 보였다.

Hyena의 핵심 통찰은 어텐션의 표현력이 두 가지 요소에서 나온다는 것이다. 첫째, **데이터 의존적 가중치** -- 입력에 따라 달라지는 어텐션 가중치이다. 둘째, **전역적 상호작용** -- 모든 토큰 쌍 간의 정보 교환이다. Hyena는 이를 암묵적으로 파라미터화된 장거리 컨볼루션과 multiplicative gating의 조합으로 근사한다.

생물학적 서열(DNA) 처리에서 긴 컨텍스트 처리 능력이 두드러지며, 수십만 토큰 길이의 시퀀스에서도 $O(N \log N)$ 복잡도를 유지한다. HyenaDNA 모델은 최대 백만 bp(base pair) 길이의 DNA 서열을 처리하여 게놈 분석에 활용되고 있다. Hyena는 attention-free 대형 언어 모델의 가능성을 열어준 중요한 이정표이다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

Hyena 연산자는 **Hyena Hierarchy**라는 계층적 구조로 구성된다.

### 1단계: 입력 프로젝션

입력 $x \in \mathbb{R}^{L \times d}$를 $N$개의 프로젝션 $v, x_1, x_2, \ldots, x_{N-1}$으로 분리한다. 이 프로젝션은 학습 가능한 선형 변환으로 계산된다.

$$v, x_1, \ldots, x_{N-1} = \text{split}(W_{\text{proj}} \cdot x)$$

### 2단계: 암묵적 장거리 컨볼루션

각 프로젝션에 암묵적으로 파라미터화된 장거리 컨볼루션 필터를 적용한다. 컨볼루션 필터 $h(t)$는 작은 FFN(Feed-Forward Network)으로 생성되며, 이 FFN의 입력은 위치 인코딩이다.

$$h(t) = \text{FFN}(\text{pos\_enc}(t)) \cdot w(t)$$

여기서 $w(t) = e^{-\alpha t}$는 지수 감쇠 윈도우로, 먼 거리의 영향을 자연스럽게 감쇠시킨다. 이 암묵적 파라미터화 방식의 핵심 장점은 어떤 시퀀스 길이에도 적응적으로 동작한다는 것이다. 고정 길이의 필터를 학습하는 것이 아니라 연속 함수를 학습하므로, 학습 시 길이와 다른 길이에서도 자연스럽게 일반화된다.

SSM과의 연결을 수식으로 표현하면, S4의 컨볼루션 커널 $\bar{K} = (C\bar{B}, C\bar{A}\bar{B}, \ldots)$을 SSM의 상태 방정식에서 유도하는 대신, Hyena는 FFN으로 직접 커널을 생성한다.

$$\bar{K}_{\text{S4}} = f(A, B, C) \quad \text{vs} \quad \bar{K}_{\text{Hyena}} = \text{FFN}(\text{positions})$$

### 3단계: Multiplicative Gating

컨볼루션 출력들을 element-wise 곱으로 계층적으로 혼합한다. 이 gating 구조가 데이터 의존적 가중치를 근사하는 핵심 메커니즘이다.

$$y = x_{N-1} \odot (h_{N-1} * (x_{N-2} \odot (h_{N-2} * (\cdots))))$$

이 계층적 곱셈 구조에서 내부 컨볼루션 결과가 외부 프로젝션에 의해 게이팅되므로, 입력에 따라 효과적으로 다른 가중치가 적용되는 효과를 만든다.

## 핵심 혁신

Hyena의 핵심 혁신은 세 가지이다.

첫째, **암묵적 컨볼루션 필터**이다. 고정 길이 커널 대신 FFN으로 연속 함수를 학습하여, 임의의 시퀀스 길이에 대응할 수 있다. 이는 S4의 SSM 커널과 유사한 아이디어이지만, 상태 공간 수식 없이 직접 필터를 생성한다는 점에서 다르다.

둘째, **완전 어텐션-프리**이다. H3도 실질적으로 attention 1개를 포함해야 최적 성능을 달성했지만, Hyena는 attention 없이도 경쟁적인 성능을 보인다.

셋째, **FlashFFTConv**이다. GPU에서 FFT 기반 컨볼루션을 효율적으로 수행하는 커스텀 CUDA 커널을 개발했다. 시퀀스 길이 8K에서 어텐션 대비 FLOP 절약률이 최대 100배에 달한다.

## 벤치마크/성능

| 모델 (153M) | Pile PPL↓ | WikiText PPL↓ | 속도(8K seq) |
|------------|-----------|---------------|----------------|
| Hyena | 10.2 | 16.3 | 100x faster |
| GPT-Neo | 9.8 | 15.1 | 1x (baseline) |
| S4D | 12.8 | 21.5 | 50x faster |
| H3 | 10.6 | 17.1 | 60x faster |

Hyena는 특히 긴 시퀀스에서 속도 이점이 극대화된다. DNA 서열 처리에서는 수십만 bp 길이의 입력을 처리할 수 있다.

| 모델 | 시퀀스 믹싱 | 데이터 의존성 | 복잡도 | 어텐션 사용 |
|------|-----------|-------------|--------|------------|
| Hyena | 암묵적 컨볼루션 + Gating | Gating으로 근사 | $O(N \log N)$ | 없음 |
| H3 | Shift SSM + SSM + Gating | Gating으로 근사 | $O(N \log N)$ | 선택적 |
| S4 | SSM 컨볼루션 | 없음(LTI) | $O(N \log N)$ | 없음 |
| Mamba | 선택적 SSM | 완전 입력 의존 | $O(N)$ | 없음 |
| Transformer | Self-Attention | 완전 입력 의존 | $O(N^2)$ | 핵심 |

## 학습

Pile 데이터셋으로 학습하며, GPT-NeoX 토크나이저를 사용한다. 시퀀스 길이 2048~8192로 실험하며, A100 GPU 클러스터에서 학습한다. 생물정보학 적용을 위해 Human Reference Genome 데이터셋으로도 추가 학습했다. FlashFFTConv 커스텀 CUDA 커널로 메모리 및 속도를 최적화했다.

다음은 Hyena 연산자의 핵심인 암묵적 컨볼루션 필터 생성을 보여주는 예시이다.

```python
import torch
import torch.nn as nn
import torch.fft

class ImplicitFilter(nn.Module):
    """Hyena의 암묵적 컨볼루션 필터 생성기"""
    def __init__(self, d_model, order=2, num_freqs=64):
        super().__init__()
        self.order = order
        # 위치 인코딩 -> 필터 생성 FFN
        self.filter_fn = nn.Sequential(
            nn.Linear(num_freqs, d_model),
            nn.SiLU(),
            nn.Linear(d_model, d_model * order),
        )
        self.decay = nn.Parameter(torch.ones(order) * 0.5)

    def forward(self, seq_len):
        t = torch.arange(seq_len, dtype=torch.float32)
        # 위치 인코딩 (사인/코사인 기저)
        pos_enc = self._positional_encoding(t)
        # FFN으로 연속 필터 생성
        filters = self.filter_fn(pos_enc)
        # 지수 감쇠 윈도우 적용
        decay_window = torch.exp(-self.decay.abs() * t.unsqueeze(-1))
        return filters * decay_window

def hyena_operator(x, filters):
    """Hyena Hierarchy: 계층적 컨볼루션 + gating"""
    v, *projs = x.chunk(len(filters) + 1, dim=-1)
    for h, x_i in zip(filters, projs):
        # FFT 기반 장거리 컨볼루션
        conv_out = fft_conv(v, h)
        # Multiplicative gating
        v = conv_out * x_i
    return v
```

## 관련 모델

Hyena는 특히 긴 시퀀스 처리가 필수적인 도메인에서 실용적 가치가 크다. DNA/RNA 서열 분석, 고해상도 시계열 데이터, 긴 문서 처리 등에서 Transformer가 메모리 한계로 처리하지 못하는 길이의 입력을 선형 복잡도로 처리할 수 있다. multiplicative gating이 어텐션의 데이터 의존적 가중치를 완벽하게 근사하지 못한다는 한계는 Mamba의 선택적 메커니즘이 해결하려 한 문제와 동일하다. 그러나 Hyena의 암묵적 컨볼루션은 생물학적 서열 모델링(HyenaDNA) 등 특수 도메인에서 여전히 강력한 도구이다.

## 참고 자료

- 논문: [Hyena Hierarchy: Towards Larger Convolutional Language Models](https://arxiv.org/abs/2302.10866)
- 코드: [HazyResearch/safari](https://github.com/HazyResearch/safari)

## 관련 문서

- [[h3|H3]] — 발전 기반
