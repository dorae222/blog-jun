# Griffin: RG-LRU와 로컬 어텐션으로 실용적 하이브리드를 완성한 아키텍처

**Google DeepMind** · **2024-02-29** · **Hybrid SSM** · **Apache-2.0**

## 개요

Griffin은 2024년 Google DeepMind가 발표한 하이브리드 순환-어텐션 아키텍처로, RG-LRU(Real-Gated Linear Recurrent Unit)라는 새로운 순환 레이어와 국소 어텐션(Local Attention)을 결합했다. Mamba와 같은 순수 SSM 모델이 어텐션 없이 언어 모델링에 도전하는 시도에 응답하여, DeepMind는 순환과 제한된 어텐션의 조합이 최적의 효율-성능 균형을 제공함을 보였다.

Griffin의 핵심 주장은 명확하다. 순수 SSM 모델은 특정 태스크(in-context retrieval, 복사)에서 근본적 한계를 보이며, 소수의 어텐션 레이어를 추가하는 것만으로 이러한 한계를 극복할 수 있다는 것이다. Griffin 9B는 Llama-2 7B와 유사한 성능을 보이면서 추론 처리량이 최대 3배 높다.

다음 그래프는 학습 FLOP 대비 Hawk, Griffin, MQA(Transformer) 기준 모델의 스케일링 곡선을 보여준다.

![학습 FLOP에 따른 MQA, Hawk, Griffin 스케일링 곡선](figures/fig_2.png)
*Figure 1: 학습 스케일링 곡선 — Griffin(하이브리드)이 순수 순환 모델 Hawk보다 일관되게 낮은 검증 손실을 보이며, MQA(Transformer)와 유사한 수렴 특성을 달성한다. (Source: De et al., 2024)*

RG-LRU는 S4나 Mamba처럼 복소수 파라미터를 사용하지 않고 실수 게이트만 사용하여 구현을 크게 단순화했다. 이 설계 선택은 CUDA 구현의 복잡도를 낮추고, 양자화 등 배포 최적화에도 유리하다. Griffin은 RecurrentGemma라는 이름으로 Hugging Face에 공개되어, 산업 수준의 하이브리드 SSM-어텐션 모델 실용화에 이정표를 세웠다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

Griffin은 MLP 레이어, RG-LRU 레이어, Local Attention 레이어를 교차 배치하는 하이브리드 구조이다. 전체 레이어 중 약 2/3는 RG-LRU, 1/3은 Local Attention으로 구성된다. 아래 다이어그램은 Griffin의 전체 아키텍처 구성을 보여준다.

![Griffin 아키텍처 — Residual Block, Gated MLP, Recurrent Block 구조](figures/fig_4.png)
*Figure 2: Griffin 아키텍처 구성 — (a) Residual Block을 N번 반복, (b) Gated MLP 블록, (c) RG-LRU 기반 Recurrent Block이 MQA를 대체하는 구조. (Source: De et al., 2024)*

### RG-LRU (Real-Gated Linear Recurrent Unit)

RG-LRU는 입력에 의존적인 $a_t$(감쇠 계수)와 $r_t$(수용 게이트)를 sigmoid 함수로 계산한다.

$$a_t = \sigma(W_a h_t), \quad r_t = \sigma(W_r h_t)$$

상태 업데이트 수식은 다음과 같다.

$$x_t = a_t \odot x_{t-1} + \sqrt{1 - a_t^2} \odot (r_t \odot W_x h_t)$$

여기서 $a_t$는 이전 상태를 얼마나 유지할지를 결정하는 감쇠 계수이다. $a_t \to 1$이면 과거 정보를 거의 그대로 유지하고, $a_t \to 0$이면 새로운 입력으로 교체한다. $r_t$는 새로운 입력 정보의 흐름을 제어하는 수용 게이트이다.

정규화 항 $\sqrt{1 - a_t^2}$는 상태의 L2 norm을 안정적으로 유지하는 역할을 한다. 이는 SSM의 이산화에서 상태 크기를 보존하는 것과 유사한 목적이다.

SSM과의 연결을 명확히 하면, RG-LRU의 상태 업데이트는 Mamba의 선택적 SSM과 구조적으로 동일하다.

$$\underbrace{x_t = a_t \odot x_{t-1} + \sqrt{1-a_t^2} \odot \tilde{x}_t}_{\text{RG-LRU}} \quad \leftrightarrow \quad \underbrace{h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t}_{\text{Selective SSM}}$$

차이점은 RG-LRU가 실수 게이트만 사용하고, Mamba는 복소수 상태도 허용한다는 것이다.

### Local Attention

슬라이딩 윈도우(128~2048 토큰) 범위 내에서만 어텐션을 수행한다. Multi-Query Attention(MQA) 방식을 사용하여 KV 캐시 메모리를 절약하면서 필요한 국소 정보 접근을 제공한다.

$$\text{LocalAttn}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}} \odot M_w\right) V$$

여기서 $M_w$는 윈도우 크기 $w$ 내의 토큰만 참조하도록 하는 마스크이다. RoPE 위치 인코딩을 적용한다.

### Hawk

Griffin에서 Local Attention을 완전히 제거한 순수 순환 버전이다. 어텐션 없이도 기본적인 언어 모델링은 가능하나 in-context retrieval에서 성능 열화가 관찰된다.

## 핵심 혁신

Griffin의 핵심 혁신은 세 가지이다.

첫째, **실수 게이트 기반 순환**이다. S4, Mamba 등이 복소수 파라미터를 사용하여 진동 패턴을 표현하는 것과 달리, RG-LRU는 실수 게이트만으로 충분한 표현력을 달성한다. 이는 CUDA 구현을 크게 단순화하며, 양자화 등 최적화에도 유리하다.

둘째, **하이브리드 레시피**이다. 모든 레이어를 어텐션이나 순환 중 하나로 통일하는 것이 아니라, 2/3 순환 + 1/3 어텐션이라는 최적 비율을 광범위한 실험으로 도출했다.

셋째, **산업 수준 스케일링**이다. 2B, 9B, 14B 규모까지 학습하여 SSM 기반 하이브리드 모델이 실제 배포 가능한 규모에서도 유효함을 입증했다.

## 벤치마크/성능

다음은 400M 파라미터 규모에서 시퀀스 길이에 따른 MQA 대비 Griffin의 성능 비교이다.

![시퀀스 길이별 MQA 대비 Griffin 성능 비교 (400M 규모)](figures/fig_6.png)
*Figure 3: 400M 규모에서의 성능 비교 — Griffin이 시퀀스 길이 증가에 따라 MQA와 동등하거나 근접한 성능을 보이며, 8K 시퀀스에서도 0.98배 수준을 유지한다. (Source: De et al., 2024)*

| 모델 | 파라미터 | HellaSwag | PIQA | WinoGrande | ARC-E |
|------|---------|-----------|------|------------|-------|
| Griffin | 9B | 77.8 | 80.3 | 70.1 | 75.2 |
| Llama-2 | 7B | 78.6 | 79.1 | 69.2 | 74.8 |
| Mamba | 2.8B | 68.5 | 76.4 | 63.5 | 67.1 |
| Hawk | 9B | 74.2 | 78.5 | 67.3 | 72.1 |

| 모델 | 순환 유형 | 어텐션 | 복소수 사용 | 추론 효율 |
|------|---------|--------|-----------|----------|
| Griffin | RG-LRU + Local Attn | Sliding Window | 실수만 | 매우 높음 |
| Mamba | Selective SSM | 없음 | 실수만 | 높음 |
| Jamba | Mamba + Full Attn | Full + MoE | 실수만 | 높음 |
| S4 | HiPPO SSM | 없음 | 복소수 | 중간 |

추론 효율 측면에서 Griffin은 디코딩 토큰 수가 증가할수록 Transformer 대비 뚜렷한 이점을 보인다.

![디코딩 토큰 수에 따른 추론 처리량 비교](figures/fig_10.png)
*Figure 4: 추론 효율 비교 — 디코딩 토큰 수가 증가할수록 Griffin과 Hawk가 MQA(Transformer) 대비 더 빠른 추론 속도를 보이며, 4096 토큰에서 처리량 격차가 극대화된다. (Source: De et al., 2024)*

또한 Griffin은 in-context learning(복사, 검색) 태스크에서도 순수 순환 모델의 한계를 극복한다.

![학습 스텝에 따른 In-context 학습 정확도 비교](figures/fig_14.png)
*Figure 5: In-context 학습 정확도 — Griffin이 Local Attention 덕분에 Hawk(순수 순환) 대비 빠르게 수렴하며 MQA 수준의 정확도에 도달하여, 하이브리드 접근법의 효과를 입증한다. (Source: De et al., 2024)*

## 학습

MassiveText 및 공개 웹 코퍼스로 학습하며, TPUv4 클러스터를 사용한다. SentencePiece 토크나이저(256K vocab)를 적용하고 시퀀스 길이 2048로 학습한다. 14B 모델은 약 1T 토큰으로 학습되었다. Gemma 아키텍처와 학습 파이프라인을 공유하며 RecurrentGemma로 공개되었다.

다음은 RG-LRU의 핵심 연산을 PyTorch로 구현한 예시이다.

```python
import torch
import torch.nn as nn

class RGLRU(nn.Module):
    """Real-Gated Linear Recurrent Unit"""
    def __init__(self, d_model):
        super().__init__()
        self.W_a = nn.Linear(d_model, d_model)  # 감쇠 게이트
        self.W_r = nn.Linear(d_model, d_model)  # 수용 게이트
        self.W_x = nn.Linear(d_model, d_model)  # 입력 변환

    def forward_recurrent(self, h_t, x_prev):
        """순환 모드: 한 토큰씩 처리"""
        # 입력 의존적 게이트 계산
        a_t = torch.sigmoid(self.W_a(h_t))  # 감쇠 계수
        r_t = torch.sigmoid(self.W_r(h_t))  # 수용 게이트
        x_in = r_t * self.W_x(h_t)
        
        # 상태 업데이트 (정규화 항 포함)
        # x_t = a_t * x_{t-1} + sqrt(1 - a_t^2) * x_in
        x_t = a_t * x_prev + torch.sqrt(1 - a_t ** 2) * x_in
        return x_t

    def forward_parallel(self, h, chunk_size=256):
        """병렬 모드: 청크 단위 학습"""
        B, L, D = h.shape
        a = torch.sigmoid(self.W_a(h))  # (B, L, D)
        r = torch.sigmoid(self.W_r(h))  # (B, L, D)
        x_in = r * self.W_x(h)
        
        # 청크 단위 parallel scan으로 병렬 계산
        return parallel_scan(a, x_in, chunk_size)
```

## 관련 모델

Griffin은 RecurrentGemma 모델로 Hugging Face에서 바로 사용할 수 있다. 긴 시퀀스 추론이 필요한 문서 처리, 대화형 AI 등에서 Transformer 대비 메모리 효율적인 배포가 가능하다. Local Attention 윈도우 크기를 조절하여 성능-효율 트레이드오프를 유연하게 설정할 수 있다. RG-LRU의 표현력이 Mamba의 선택적 SSM과 비교하여 어느 것이 근본적으로 우수한지는 아직 결론이 나지 않았으나, DeepMind의 산업 수준 검증과 RecurrentGemma 공개는 하이브리드 모델 실용화의 큰 이정표이다.

## 참고 자료

- 논문: [Griffin: Mixing Gated Linear Recurrences with Local Attention for Efficient Language Models](https://arxiv.org/abs/2402.19427)
- 코드: [google-deepmind/recurrentgemma](https://github.com/google-deepmind/recurrentgemma)

## 관련 문서

- [[mamba|Mamba: Linear-Time Sequence Modeling with Selective State Spaces]] — 영감
