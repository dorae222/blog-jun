# RWKV-7 (Goose): Delta Rule로 재설계된 RWKV의 최신 진화

**RWKV Foundation** · **2025-03-21** · **SSM** · **Apache-2.0**

## 개요

RWKV-7(코드명 'Goose')는 2025년 RWKV Foundation이 발표한 RWKV 시리즈 최신 버전으로, 기존 RWKV의 WKV 연산자를 Delta Rule 기반으로 전면 재설계하여 표현력을 대폭 향상시킨 모델이다. RWKV-4부터 RWKV-6까지의 점진적 개선과 달리, RWKV-7은 핵심 연산의 이론적 토대를 연상 기억(associative memory) 이론으로 재구축한 근본적 변화이다.

Delta Rule은 신경과학과 기계학습의 교차점에 위치한 온라인 학습 규칙으로, 현재 키-값 쌍과 메모리에 저장된 예측값의 오차를 기반으로 상태를 업데이트한다. 이는 Widrow-Hoff 학습 규칙으로도 알려져 있으며, 헤비안 학습(Hebbian learning)의 오차 수정 버전이다.

2.9B 파라미터 모델이 동일 규모 Mamba-2 및 RWKV-6 대비 여러 NLP 벤치마크에서 SoTA를 달성했으며, 특히 in-context learning과 다국어 처리에서 두드러진 성능 향상을 보였다. World Tokenizer v3의 도입으로 100개 이상 언어를 지원하며, 한국어 포함 CJK 언어에서의 토크나이제이션 효율이 크게 개선되었다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

RWKV-7의 핵심 혁신은 순환 상태에 LoRA(Low-Rank Adaptation) 스타일의 delta rule 업데이트를 적용한 것이다.

### Delta Rule 상태 업데이트

상태 업데이트 수식은 다음과 같다.

$$h_t = h_{t-1} + (v_t - h_{t-1} k_t) u_t^T$$

이 수식의 각 항을 분석하면 다음과 같다.

**메모리 예측 $h_{t-1} k_t$**: 현재 키 $k_t$에 대해 메모리 $h_{t-1}$이 예측하는 값이다. 이상적으로 이 값은 실제 값 $v_t$와 같아야 한다.

**예측 오차 $(v_t - h_{t-1} k_t)$**: 실제 값과 메모리 예측값의 차이이다. 이 오차가 클수록 메모리를 더 강하게 수정한다.

**업데이트 방향 $u_t^T$**: 오차를 어느 방향으로 반영할지를 결정하는 벡터이다. 이는 LoRA에서의 저랭크 업데이트와 유사한 역할을 한다.

SSM과의 연결을 명확히 하면, 일반적인 선형 순환 상태 업데이트는 다음과 같다.

$$h_t = \bar{A} h_{t-1} + \bar{B} x_t$$

RWKV-7의 delta rule은 이를 확장한 것으로, $\bar{A} = I - k_t u_t^T$(저랭크 업데이트된 항등 행렬)이고 $\bar{B} x_t = v_t u_t^T$(값-업데이트 외적)로 해석할 수 있다.

$$h_t = (I - k_t u_t^T) h_{t-1} + v_t u_t^T = h_{t-1} + (v_t - h_{t-1} k_t) u_t^T$$

### 전체 Time Mixing 모듈

전체 동작 흐름은 다음과 같다.

1. Token Shift로 현재/이전 토큰 정보를 보간
2. R, K, V, W, U 변수를 각각 선형 변환으로 계산
3. Delta rule로 상태 $h_t$를 업데이트
4. 출력 $o_t = h_t q_t$를 Receptance 게이트 $\sigma(r_t)$로 조절

### RWKV-6에서의 차이

RWKV-6는 데이터 의존적 감쇠와 bonus term을 사용했다.

$$h_t^{\text{v6}} = w_t \odot h_{t-1} + k_t v_t^T + \text{bonus}$$

RWKV-7은 bonus term을 제거하고 delta rule로 대체함으로써 이론적 근거를 명확히 하면서도 실제 성능을 크게 향상시켰다.

## 핵심 혁신

RWKV-7의 핵심 혁신은 세 가지이다.

첫째, **Delta Rule 기반 메모리 수정**이다. 단순 누적(RWKV-4) → 데이터 의존적 감쇠(RWKV-5/6) → 예측 오차 기반 수정(RWKV-7)으로의 진화는 연상 기억의 정밀도를 크게 향상시킨다.

둘째, **World Tokenizer v3**이다. 65,536 vocab 크기로 100개 이상 언어를 지원하며, CJK 언어에서 특히 효과적이다.

셋째, **연산 효율 유지**이다. Delta rule 도입에도 불구하고 추론 시 $O(1)$ 메모리를 유지하는 RNN 특성을 그대로 보존한다.

## 벤치마크/성능

| 모델 (2.9B) | ARC-C | HellaSwag | PIQA | WinoGrande | MMLU |
|------------|-------|-----------|------|------------|------|
| RWKV-7 | 39.8 | 68.5 | 77.3 | 64.2 | 42.1 |
| RWKV-6 | 36.2 | 65.1 | 75.8 | 61.5 | 38.7 |
| Mamba-2 | 38.5 | 67.3 | 76.8 | 63.1 | 40.5 |
| Pythia | 37.1 | 66.8 | 76.2 | 62.3 | 39.2 |

| 모델 | 상태 업데이트 | 메모리 수정 | 토크나이저 | 다국어 |
|------|-------------|-----------|----------|--------|
| RWKV-7 | Delta Rule | 예측 오차 기반 | World v3 (65K) | 100+ 언어 |
| RWKV-6 | 데이터 의존적 감쇠 | Bonus term | World v2 | 60+ 언어 |
| RWKV-4 | 고정 감쇠 | 단순 누적 | World v1 | 제한적 |
| Gated DeltaNet | 게이팅 + Delta Rule | 게이팅 + 오차 | LLaMA 기반 | 영어 중심 |
| Mamba | 선택적 SSM | 이산화 기반 | GPT-NeoX | 영어 중심 |

## 학습

다국어 대규모 코퍼스로 학습하며(영어, 중국어, 일본어 등 중심), H100 GPU 클러스터를 사용한다. RWKV World Tokenizer v3(65,536 vocab)을 적용한다. 2.9B 모델은 약 1.1T 토큰으로 학습하여 RWKV-6 대비 동일 컴퓨트에서 더 낮은 perplexity를 달성했다.

다음은 RWKV-7의 Delta Rule 상태 업데이트를 구현한 예시이다.

```python
import torch
import torch.nn as nn

class RWKV7DeltaRule(nn.Module):
    def __init__(self, d_model, d_state):
        super().__init__()
        self.W_k = nn.Linear(d_model, d_state, bias=False)
        self.W_v = nn.Linear(d_model, d_state, bias=False)
        self.W_u = nn.Linear(d_model, d_state, bias=False)
        self.W_q = nn.Linear(d_model, d_state, bias=False)
        self.W_r = nn.Linear(d_model, d_model, bias=False)

    def forward_recurrent(self, x_t, h_prev):
        """RWKV-7 Delta Rule 순환 추론"""
        k_t = self.W_k(x_t)   # (B, d_state)
        v_t = self.W_v(x_t)   # (B, d_state)
        u_t = self.W_u(x_t)   # (B, d_state)
        q_t = self.W_q(x_t)   # (B, d_state)
        r_t = self.W_r(x_t)   # (B, d_model)

        # 메모리 예측: h_{t-1} @ k_t
        prediction = torch.einsum('bik,bk->bi', h_prev, k_t)
        # 예측 오차
        error = v_t - prediction
        # Delta Rule 상태 업데이트
        # h_t = h_{t-1} + error @ u_t^T
        h_t = h_prev + torch.einsum('bi,bj->bij', error, u_t)

        # 출력 = h_t @ q_t, Receptance 게이트 적용
        o_t = torch.einsum('bij,bj->bi', h_t, q_t)
        o_t = torch.sigmoid(r_t) * o_t
        return o_t, h_t
```

## 관련 모델

RWKV-7은 GitHub(BlinkDL/RWKV-LM)에서 사용할 수 있으며, Apache-2.0 라이선스로 상용 활용이 가능하다. Delta Rule 기반의 향상된 in-context learning 능력과 World Tokenizer v3의 다국어 지원 덕분에, 한국어 포함 다국어 챗봇, 번역, 문서 요약 등 다양한 태스크에 활용할 수 있다. Transformer 기반 대형 모델(Llama-3 등) 대비 전체 벤치마크 평균에서는 여전히 격차가 존재하지만, 추론 효율과 다국어 지원이라는 고유 강점은 특정 사용 사례에서 큰 가치를 제공한다.

## 참고 자료

- 논문: [RWKV-7: Goose with Associative Memory](https://arxiv.org/abs/2503.14456)
- 코드: [BlinkDL/RWKV-LM](https://github.com/BlinkDL/RWKV-LM)

## 관련 문서

- [[rwkv|RWKV]] — 발전 기반
