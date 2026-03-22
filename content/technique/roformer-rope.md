---
title: "RoFormer: Enhanced Transformer with Rotary Position Embedding"
slug: "roformer-rope"
category: technique
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.388148+00:00"
---

## 논문 개요

"RoFormer: Enhanced Transformer with Rotary Position Embedding"은 Jianlin Su, Yu Lu, Shengfeng Pan, Ahmed Murtadha, Bo Wen, Yunfeng Liu가 2021년 발표한 논문으로, **RoPE(Rotary Position Embedding)**라는 새로운 Positional Embedding 기법을 제안한다.

이 논문은 이후 LLM 발전에 있어 가장 영향력 있는 기술 논문 중 하나로 평가받는다. LLaMA, LLaMA 2/3, PaLM, GPT-NeoX, Falcon, Mistral, Qwen, Yi 등 사실상 2022년 이후 등장한 거의 모든 주요 오픈소스 LLM이 RoPE를 채택했다.

RoPE가 해결하고자 한 핵심 문제는 **위치 정보를 어텐션 메커니즘에 효율적으로 통합하는 방법**이다. 기존 절대 Positional Embedding은 학습 범위 밖의 위치로 일반화되지 않으며, 상대 Positional Embedding은 구현이 복잡하고 계산 비용이 높은 문제가 있었다.

---

## 핵심 기여

### 1. RoPE의 핵심 아이디어

RoPE의 핵심 아이디어는 간단하지만 우아하다: **위치 정보를 학습 가능한 임베딩으로 추가하는 대신, 쿼리와 키 벡터에 회전 변환을 적용한다.**

목표: 위치 $m$의 쿼리와 위치 $n$의 키 사이의 어텐션 점수가 두 위치의 **상대 거리** $m - n$에만 의존하도록 설계한다.

$$\langle f_q(x_m, m), f_k(x_n, n) \rangle = g(x_m, x_n, m - n)$$

이 조건을 만족하는 함수 $f_q, f_k$를 찾는 것이 RoPE의 출발점이다.

### 2. 추가 파라미터 불필요

기존 학습 가능한 Positional Embedding(예: BERT, GPT-2)과 달리, RoPE는 순전히 **수학적 변환**으로 구현되어 추가 파라미터가 전혀 없다. 모든 주파수 값($\theta_i$)은 미리 정해진 공식으로 계산된다.

### 3. 뛰어난 외삽 능력

RoPE는 학습 시 본 컨텍스트 길이 이상으로도 어느 정도 일반화된다. 이는 주파수 기반의 연속적인 위치 표현 덕분이며, 이후 YaRN, LongRoPE 등의 확장 연구로 이어졌다.

---

## 방법론 상세

### 2D 케이스로 이해하는 RoPE

먼저 $d = 2$ (2차원 벡터)인 경우를 살펴보자. 위치 $m$에 있는 쿼리 벡터 $q = (q_1, q_2)$에 대해 다음 함수를 정의한다:

$$f_q(x_m, m) = \begin{pmatrix} \cos m\theta & -\sin m\theta \\ \sin m\theta & \cos m\theta \end{pmatrix} \begin{pmatrix} q_1 \\ q_2 \end{pmatrix}$$

마찬가지로 위치 $n$의 키 벡터 $k = (k_1, k_2)$에 대해:

$$f_k(x_n, n) = \begin{pmatrix} \cos n\theta & -\sin n\theta \\ \sin n\theta & \cos n\theta \end{pmatrix} \begin{pmatrix} k_1 \\ k_2 \end{pmatrix}$$

이 두 벡터의 내적을 계산하면:

$$f_q^T f_k = \begin{pmatrix} q_1 & q_2 \end{pmatrix} \begin{pmatrix} \cos(m-n)\theta & -\sin(m-n)\theta \\ \sin(m-n)\theta & \cos(m-n)\theta \end{pmatrix} \begin{pmatrix} k_1 \\ k_2 \end{pmatrix}$$

결과가 **$(m - n)\theta$** 에만 의존한다. 즉, 상대 위치만을 인코딩한다.

### 일반적인 d차원 케이스

$d$차원 벡터의 경우, 쌍(pair)을 이루어 2D 회전을 적용한다. 전체 회전 행렬은:

$$R_{\Theta, m}^d = \begin{pmatrix}
\cos m\theta_1 & -\sin m\theta_1 & & & \\
\sin m\theta_1 & \cos m\theta_1 & & & \\
 & & \cos m\theta_2 & -\sin m\theta_2 & \\
 & & \sin m\theta_2 & \cos m\theta_2 & \\
 & & & & \ddots \\
 & & & & & \cos m\theta_{d/2} & -\sin m\theta_{d/2} \\
 & & & & & \sin m\theta_{d/2} & \cos m\theta_{d/2}
\end{pmatrix}$$

각 주파수 $\theta_i$는 정현파의 주파수를 로그 스케일로 배치한다:

$$\theta_i = 10000^{-2(i-1)/d}, \quad i = 1, 2, \ldots, d/2$$

이는 Transformer 원논문의 sinusoidal Positional Encoding과 동일한 주파수를 사용하며, 낮은 인덱스는 높은 주파수(세밀한 위치 구분), 높은 인덱스는 낮은 주파수(전반적인 위치 구분)를 담당한다.

### 복소수 표현

RoPE는 복소수 관점에서 더욱 우아하게 표현된다. $d$차원 실수 벡터를 $d/2$차원 복소수 벡터로 해석하면:

$$\mathbf{q} = (q_1 + iq_2, q_3 + iq_4, \ldots, q_{d-1} + iq_d)$$

위치 $m$에서의 RoPE 변환은 각 복소수 성분에 복소 지수를 곱하는 것과 동일:

$$f_q(\mathbf{q}, m)_j = (q_{2j-1} + iq_{2j}) \cdot e^{im\theta_j}$$

두 벡터의 내적은 복소수 내적의 실수 부분으로:

$$\langle f_q(\mathbf{q}_m), f_k(\mathbf{k}_n) \rangle = \text{Re}\left[\sum_{j=1}^{d/2} (q_{2j-1} + iq_{2j})^* (k_{2j-1} + ik_{2j}) e^{i(n-m)\theta_j}\right]$$

이는 $m - n$에만 의존하는 함수임이 명확하다.

### 효율적인 구현

RoPE는 행렬 전체를 구성하지 않고도 효율적으로 계산할 수 있다:

```python
import torch
import math

def precompute_freqs_cis(dim: int, end: int, theta: float = 10000.0):
    """RoPE 주파수 사전 계산"""
    freqs = 1.0 / (theta ** (torch.arange(0, dim, 2).float() / dim))
    t = torch.arange(end)  # 위치 인덱스
    freqs = torch.outer(t, freqs)  # [end, dim/2]
    freqs_cis = torch.polar(torch.ones_like(freqs), freqs)  # 복소수 형태
    return freqs_cis

def apply_rotary_emb(xq, xk, freqs_cis):
    """쿼리와 키에 RoPE 적용"""
    xq_ = torch.view_as_complex(xq.float().reshape(*xq.shape[:-1], -1, 2))
    xk_ = torch.view_as_complex(xk.float().reshape(*xk.shape[:-1], -1, 2))
    
    freqs_cis = freqs_cis.unsqueeze(0).unsqueeze(2)  # 브로드캐스팅
    
    xq_out = torch.view_as_real(xq_ * freqs_cis).flatten(3)
    xk_out = torch.view_as_real(xk_ * freqs_cis).flatten(3)
    
    return xq_out.type_as(xq), xk_out.type_as(xk)

# 사용 예시
seq_len, d_model = 2048, 4096
heads = 32
head_dim = d_model // heads

freqs_cis = precompute_freqs_cis(head_dim, seq_len)

# 어텐션 전
q = torch.randn(1, seq_len, heads, head_dim)
k = torch.randn(1, seq_len, heads, head_dim)

q_rotated, k_rotated = apply_rotary_emb(q, k, freqs_cis)
```

### 절대 Positional Embedding과의 비교

| 특성 | 절대 Positional Embedding | Sinusoidal | RoPE |
|---|---|---|---|
| 학습 파라미터 | 있음 | 없음 | 없음 |
| 상대 Positional Encoding | 간접적 | 간접적 | 직접적 |
| 외삽 가능성 | 제한적 | 보통 | 우수 |
| 구현 복잡도 | 낮음 | 낮음 | 보통 |
| 성능 | 보통 | 보통 | 높음 |
| 채택 모델 | BERT, GPT-2 | 원 Transformer | LLaMA, PaLM 등 |

---

## 실험 결과

### 장문 텍스트 성능

| 모델 | Positional Embedding | CMRC2018 | DRCD |
|---|---|---|---|
| BERT | 학습 가능 | 78.2 | 84.4 |
| RoBERTa | 학습 가능 | 80.3 | 86.6 |
| RoFormer | RoPE | **80.5** | **87.2** |

### 긴 시퀀스에서의 외삽

RoPE는 학습 시 보지 못한 긴 시퀀스에서도 상대적으로 안정적인 성능을 보인다:

$$\text{성능 저하율} = 1 - \frac{P(L_{\text{test}})}{P(L_{\text{train}})}, \quad L_{\text{test}} > L_{\text{train}}$$

RoPE의 경우 이 저하율이 절대 Positional Embedding 대비 낮으며, 이는 이후 YaRN, LongRoPE 등의 컨텍스트 확장 연구의 기초가 된다.

### 어텐션 패턴 분석

RoPE를 시각화하면, 동일한 상대 거리를 가진 토큰 쌍들이 일관된 어텐션 패턴을 보임을 확인할 수 있다. 이는 RoPE가 실제로 상대 위치 정보를 효과적으로 인코딩하고 있음을 시각적으로 보여준다.

---

## 의의 및 한계

### 의의

**현대 LLM의 기반 기술**: RoPE는 2022년 이후 등장한 대부분의 주요 LLM에 채택되어 사실상의 표준 Positional Embedding이 되었다. LLaMA 시리즈, PaLM, GPT-NeoX, Falcon, Mistral, Qwen, Yi, DeepSeek 등이 모두 RoPE를 사용한다.

**수학적 우아함**: RoPE는 복소수 회전이라는 단순한 수학적 아이디어로 Positional Encoding 문제를 해결한다. 이 수학적 명확성은 이론적 분석과 후속 연구를 용이하게 한다.

**파라미터 효율**: 추가 학습 파라미터 없이 위치 정보를 인코딩하므로 모델 복잡도를 줄인다.

**장문 컨텍스트 확장의 기초**: RoPE의 주파수 기반 설계는 컨텍스트 길이 확장 연구(YaRN, LongRoPE, ALiBi 비교 연구 등)의 출발점이 되었다.

**후속 연구 파급 효과**: RoPE의 등장은 다음 연구들을 직접 가능하게 했다:
- **YaRN**: RoPE 주파수 스케일링으로 32K→128K 확장
- **LongRoPE**: 256K+ 컨텍스트 지원
- **RoPE 외삽 연구**: 선형/비선형 스케일링 방법
- **Position Interpolation (PI)**: 위치 보간으로 컨텍스트 확장

### 한계

**순수 외삽의 한계**: RoPE 자체만으로는 학습 시 본 컨텍스트의 2~4배 이상을 안정적으로 처리하기 어렵다. YaRN 등의 추가 기법이 필요하다.

**주파수 선택의 경험적 설정**: $\theta = 10000$이라는 기저 주파수는 경험적으로 선택된 것으로, 최적값에 대한 이론적 근거가 부족하다. (이후 LLaMA 3는 $\theta = 500000$으로 변경)

**2D/멀티모달 확장의 복잡성**: 1D 시퀀스에 최적화되어 있어 이미지(2D) 등 다차원 위치 정보를 다루는 경우 별도의 확장이 필요하다 (2D RoPE, 3D RoPE 등).

**비균일한 어텐션 감쇠**: 거리에 따른 어텐션 가중치의 감쇠가 비선형적이고 비균일하여, 특정 거리 범위에서 급격한 성능 저하가 발생할 수 있다.

RoPE는 단순한 수학적 아이디어가 어떻게 분야 전체에 영향을 미칠 수 있는지를 잘 보여주는 사례다. 2021년 발표 이후 수많은 LLM 연구자들이 이 기술을 채택하고 발전시켜, 현대 LLM 아키텍처의 근간을 이루고 있다.