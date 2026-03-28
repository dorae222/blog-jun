# Mamba-3: SSM과 Sparse Attention의 전략적 하이브리드

**Carnegie Mellon University / Princeton University** · **2026-03-19** · **Hybrid SSM** · **Apache-2.0**

## 개요

Mamba-3는 2026년 ICLR에서 발표된 Mamba 시리즈의 세 번째 버전으로, 순수 SSM과 하이브리드 아키텍처 간의 균형을 재탐색한 모델이다. Mamba-1과 Mamba-2가 "SSM만으로 Transformer를 대체할 수 있는가"라는 질문에 도전했다면, Mamba-3는 "SSM과 어텐션의 최적 조합은 무엇인가"라는 더 실용적인 질문에 답한다.

Mamba-2의 SSD(Structured State Space Duality) 프레임워크를 계승하면서도 소수의 sparse attention 레이어를 전략적으로 배치하는 하이브리드 설계를 채택했다. SSM만으로는 어려운 in-context learning과 정밀 검색 태스크에서 hybrid 구조가 더 효과적임을 대규모 실험으로 입증했다. 동일 규모 Llama 계열 대비 학습 효율은 유지하면서 특정 추론 태스크에서 성능이 향상되었다.

Mamba-3는 SSM 기반 모델의 실용 배포에 가장 가까워진 이정표로 평가받는다. 순수 SSM의 $O(1)$ 메모리 장점을 대부분 유지하면서, 소수의 어텐션 레이어로 in-context retrieval 능력을 크게 보완한 절충안을 제시한다.

![Mamba-3 아키텍처 — SSD 블록과 소수의 Sparse Attention 레이어를 전략적으로 교차 배치한 하이브리드 구조](figures/architecture.svg)

*Figure 1: Mamba-3 아키텍처 — 전체 레이어의 85~90%를 SSD 블록으로, 10~15%를 Sparse Attention으로 구성하여 SSM의 O(1) 메모리 장점을 유지하면서 in-context retrieval 능력을 보완한다.*

## 아키텍처 상세

Mamba-3의 아키텍처는 두 가지 유형의 레이어를 전략적으로 교차 배치한다.

### SSD 블록 (85~90%)

전체 레이어의 대다수를 차지하며, Mamba-2의 Structured State Space Duality 블록을 그대로 사용한다. 각 SSD 블록은 멀티-헤드 선택적 SSM으로, 입력 의존적인 $B$, $C$, $\Delta$ 파라미터를 통해 시퀀스를 처리한다.

$$h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t, \quad y_t = C_t h_t$$

여기서 $\bar{A}_t = \exp(\Delta_t A)$이며, $\Delta_t$는 입력에 의존적으로 계산된다. SSM 레이어는 명시적 위치 인코딩 없이 순환 구조를 통해 암묵적으로 위치를 처리한다.

SSD 프레임워크의 이중성에 따라, 이 연산은 다음과 같은 구조화된 마스크 어텐션으로도 표현할 수 있다.

$$Y = (L \odot QK^T) \cdot V$$

학습 시에는 행렬 곱셈 관점(어텐션 모드)으로, 추론 시에는 순환 관점(SSM 모드)으로 동작한다.

### Mamba-2 대비 SSD 블록 개선점

Mamba-3의 SSD 블록은 Mamba-2의 구조를 기반으로 하되 몇 가지 중요한 개선을 도입했다. 첫째, **청크 크기 적응형 스케줄링**이다. Mamba-2에서는 고정 청크 크기(예: 256)로 시퀀스를 분할하여 병렬 처리했으나, Mamba-3에서는 레이어 깊이에 따라 청크 크기를 동적으로 조절한다. 초기 레이어에서는 작은 청크(128)로 세밀한 로컬 패턴을 포착하고, 후기 레이어에서는 큰 청크(512)로 장거리 의존성을 효율적으로 처리한다.

둘째, **상태 공간 차원의 확장**이다. Mamba-2의 기본 상태 차원($N = 64$)을 Mamba-3에서는 $N = 128$로 확장하여 더 풍부한 히든 상태 표현이 가능하다. 상태 차원 확장에 따른 연산량 증가는 SSM의 선형 복잡도 특성 덕분에 관리 가능한 수준이며, 특히 장거리 의존성 모델링에서 유의미한 성능 향상을 가져온다.

### Multi-Head Latent Attention 통합

Mamba-3의 sparse attention 레이어에서 주목할 점은 **Multi-Head Latent Attention(MLA)** 방식의 통합이다. DeepSeek-V2에서 제안된 MLA는 key-value 쌍을 저차원 잠재 공간으로 압축하여 KV 캐시 메모리를 대폭 줄인다.

$$c_t^{KV} = W^{DKV} x_t$$

$$k_t = W^{UK} c_t^{KV}, \quad v_t = W^{UV} c_t^{KV}$$

여기서 $c_t^{KV} \in \mathbb{R}^{d_c}$는 압축된 잠재 벡터이고, $d_c \ll d_k \cdot n_h$이다. 이를 통해 KV 캐시 크기가 기존 Multi-Head Attention 대비 $\frac{d_c}{2 \cdot d_k \cdot n_h}$로 감소한다. Mamba-3는 이 MLA를 sparse attention 레이어에 적용하여, 소수의 어텐션 레이어가 존재함에도 전체 KV 캐시 오버헤드를 최소화했다.

### Sparse Attention 블록 (10~15%)

전체 레이어 중 소수를 차지하며, sliding window 또는 sparse attention을 수행한다. 이 레이어에는 RoPE(Rotary Position Embedding)를 적용해 상대적 위치 정보를 명시적으로 제공한다.

$$\text{Attn}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}} \odot W\right) V$$

여기서 $W$는 sliding window 마스크로, 윈도우 크기 내의 토큰만 참조한다. Multi-Query Attention(MQA) 방식을 사용하여 KV 캐시 메모리를 최소화한다.

Sparse attention 레이어의 역할은 SSM이 구조적으로 약한 **정밀 정보 검색(precise information retrieval)**을 보완하는 것이다. SSM은 순환 상태를 통해 정보를 압축하여 전달하기 때문에 "100번째 문장에서 언급된 이름을 정확히 반환하라"와 같은 needle-in-a-haystack 태스크에서 성능이 떨어진다. 어텐션 레이어는 모든 토큰 쌍 간의 직접적인 상호작용을 허용하므로 이러한 정밀 검색에 효과적이다.

### 레이어 배치 전략

어텐션 레이어의 배치 위치가 핵심이다. 단순히 균등 간격으로 배치하는 것이 아니라, 네트워크의 특정 깊이에 집중 배치하는 것이 더 효과적임을 실험적으로 확인했다. 8B 모델(32 레이어) 기준 최적 배치는 다음과 같다.

| 영역 | 레이어 번호 | 유형 | 역할 |
|------|-----------|------|------|
| 초기 | 2, 4 | Sparse Attn | 기본 패턴 인식 |
| 중간 | 15, 16 | Sparse Attn | 중거리 의존성 |
| 후기 | 30 | Sparse Attn | 최종 정보 통합 |
| 나머지 | 그 외 27개 | SSD | 장거리 + 일반 처리 |

이 배치 전략은 광범위한 ablation study를 통해 도출되었다. 균등 배치(레이어 5, 11, 16, 22, 27) 대비 전략적 배치가 평균 1.5%p 높은 벤치마크 점수를 보였다. 특히 초기 레이어(2, 4)의 어텐션이 중요한데, 이는 네트워크 초반에서 토큰 간 명시적 상호작용을 통해 기본 표현을 형성하는 것이 후속 SSD 레이어의 성능에 큰 영향을 미치기 때문이다.

## 핵심 혁신

Mamba-3의 핵심 혁신은 세 가지이다.

첫째, **전략적 하이브리드 레시피**이다. 어텐션 레이어의 비율(10~15%)과 배치 위치를 광범위한 ablation을 통해 최적화했다. 이 레시피는 "어디에 어텐션을 넣어야 최대 효과를 얻는가"라는 실용적 질문에 대한 답을 제공한다.

둘째, **완전한 병렬화 지원**이다. Tensor parallelism과 sequence parallelism을 완전히 지원하도록 재설계되어, 멀티-노드 학습 효율이 Mamba-2 대비 30% 이상 개선되었다.

셋째, **장거리 컨텍스트 확장**이다. 기본 시퀀스 길이 8192에서 최대 128K까지 컨텍스트 확장 실험을 진행하여, SSM의 선형 복잡도 이점이 긴 컨텍스트에서 더욱 두드러짐을 보였다.

## 벤치마크/성능

| 모델 | 파라미터 | HellaSwag | PIQA | MMLU | In-context Retrieval |
|------|---------|-----------|------|------|---------------------|
| Mamba-3 | 8B | 79.2 | 81.5 | 58.3 | 92.1% |
| Mamba-2 | 2.7B | 68.8 | 78.1 | 45.2 | 78.5% |
| Llama-3 | 8B | 79.8 | 80.9 | 62.1 | 98.2% |
| Mamba-3 (SSM only) | 8B | 77.1 | 80.2 | 54.8 | 71.3% |

Sparse attention 레이어 추가의 효과가 특히 in-context retrieval에서 두드러진다(71.3% → 92.1%). 일반 벤치마크에서도 SSM-only 대비 향상이 관찰된다.

### Mamba 시리즈 진화 비교

| 특성 | Mamba-1 | Mamba-2 | Mamba-3 |
|------|---------|---------|---------|
| 핵심 구조 | 선택적 SSM | SSD (SSM-Attention 이중성) | SSD + Sparse Attention 하이브리드 |
| 어텐션 사용 | 없음 | 없음 | 10~15% Sparse Attention |
| 상태 차원 | 16 | 64 | 128 |
| 병렬 학습 | 제한적 | 부분적 | 완전 지원 |
| 최대 컨텍스트 | 이론상 무제한 | 이론상 무제한 | 128K (실험 검증) |
| In-context Retrieval | 약함 | 약함 | 강함 (92.1%) |
| 추론 메모리 | $O(1)$ | $O(1)$ | $O(1)$ + 소수 KV 캐시 |

Mamba-1에서 Mamba-3로의 진화는 "순수성 vs 실용성"의 스펙트럼에서 점진적으로 실용성 쪽으로 이동한 과정이다. Mamba-1은 SSM만으로 Transformer를 대체할 수 있음을 보여주려 했고, Mamba-2는 SSM과 어텐션의 수학적 이중성을 발견하여 학습 효율을 높였다. Mamba-3는 이 이중성을 실질적으로 활용하여 소수의 명시적 어텐션 레이어를 추가함으로써, 순수 SSM의 약점을 직접적으로 보완했다.

### 코드 및 언어 태스크 성능

| 벤치마크 | Mamba-3 8B | Llama-3 8B | Mamba-2 2.7B |
|----------|-----------|-----------|-------------|
| HumanEval (pass@1) | 34.2% | 37.8% | 18.5% |
| MBPP (pass@1) | 42.1% | 45.3% | 25.7% |
| GSM8K (CoT) | 52.8% | 56.1% | 31.4% |
| ARC-Challenge | 55.7% | 57.2% | 42.3% |

코드 생성과 수학적 추론에서 Mamba-3는 Llama-3에 근접하는 성능을 보인다. 특히 Mamba-2 대비 코드 생성 능력이 크게 향상되었는데, 이는 하이브리드 구조가 코드의 장거리 참조 패턴(함수 호출, 변수 참조 등)을 더 효과적으로 처리하기 때문이다.

| 모델 | SSM 비율 | 어텐션 비율 | 어텐션 유형 | 최대 컨텍스트 |
|------|---------|-----------|-----------|-------------|
| Mamba-3 | 85~90% | 10~15% | Sparse/SW | 128K |
| Griffin | ~67% | ~33% | Local MQA | 2K (window) |
| Jamba | ~50% | ~50% | Full + MoE | 256K |
| Mamba-2 | 100% | 0% | 없음 | Unlimited |

## 학습

ICLR 2026 발표 기준으로, 대규모 다국어 코퍼스로 사전학습했다. A100/H100 GPU 클러스터에서 시퀀스 길이 8192를 기본으로 학습하며, 최대 128K까지 컨텍스트 확장 실험을 진행했다. SSD + sparse attention 혼합 커널로 연산을 최적화했다.

### 학습 방법론 상세

Mamba-3의 학습은 세 단계로 구성된다.

**1단계: SSD 전용 사전학습**. 먼저 어텐션 레이어 없이 SSD 블록만으로 구성된 모델을 전체 토큰의 80%로 사전학습한다. 이 단계에서 SSM의 기본 언어 모델링 능력을 확립한다.

**2단계: 어텐션 레이어 삽입 및 하이브리드 학습**. 사전학습된 SSD 블록의 가중치를 유지한 채, 전략적 위치에 sparse attention 레이어를 삽입한다. 새로 삽입된 어텐션 레이어는 랜덤 초기화되며, 전체 모델을 나머지 20% 토큰으로 공동 학습한다. 이 단계적 접근법은 처음부터 하이브리드로 학습하는 것 대비 5% 적은 총 연산량으로 유사한 성능을 달성한다.

**3단계: 컨텍스트 확장**. 기본 시퀀스 길이 8192에서 학습된 모델을 32K, 64K, 128K로 점진적으로 확장한다. SSM 레이어는 순환 구조 덕분에 추가 수정 없이 긴 시퀀스를 처리할 수 있으며, 어텐션 레이어에는 YaRN 기반 RoPE 스케일링을 적용한다.

다음은 Mamba-3의 하이브리드 레이어 구성을 보여주는 예시 코드이다.

```python
import torch.nn as nn

def build_mamba3_layers(n_layers=32, attn_positions=[2, 4, 15, 16, 30]):
    """Mamba-3 하이브리드 레이어 스택 구성"""
    layers = []
    for i in range(n_layers):
        if i in attn_positions:
            # Sparse Attention 레이어 (RoPE 포함)
            layers.append(SparseAttentionBlock(
                d_model=4096,
                n_heads=32,
                window_size=2048,
                use_rope=True,
            ))
        else:
            # SSD 블록 (Mamba-2 계승)
            layers.append(SSDBlock(
                d_model=4096,
                d_state=128,
                n_heads=32,
                chunk_size=256,
            ))
    return nn.ModuleList(layers)
```

## 한계 및 과제

1. **MMLU 성능 격차**: 가장 두드러진 한계는 MMLU에서 Llama-3 대비 3.8%p 낮은 점수(58.3% vs 62.1%)이다. 이는 SSM의 구조적 특성상 방대한 세계 지식을 저장하고 검색하는 능력에서 full attention Transformer에 미치지 못함을 시사한다. SSM의 고정 크기 상태 벡터가 정보 병목(information bottleneck)으로 작용할 수 있다.

2. **KV 캐시 복잡성**: 순수 SSM의 $O(1)$ 메모리라는 깔끔한 장점이 하이브리드 구조에서 부분적으로 희석된다. 전체 레이어의 10~15%에 불과하지만, 어텐션 레이어의 KV 캐시가 추론 시 메모리 관리의 복잡성을 높인다. 특히 128K 같은 긴 컨텍스트에서 sparse attention 레이어의 윈도우 크기 설정이 성능과 메모리 간의 트레이드오프를 발생시킨다.

3. **하이브리드 레시피의 일반화 문제**: 8B 모델에서 최적화된 어텐션 레이어 배치(레이어 2, 4, 15, 16, 30)가 다른 규모(1B, 30B, 70B)에서도 최적인지 검증되지 않았다. 모델 규모가 달라지면 최적 배치도 달라질 가능성이 높으며, 이를 매번 ablation으로 탐색하는 것은 비용이 크다.

4. **SSM 커널 생태계의 미성숙**: Transformer의 FlashAttention처럼 고도로 최적화된 하드웨어 커널이 SSM 진영에서는 아직 충분히 발전하지 않았다. SSD 블록의 이론적 FLOP 효율성이 실제 하드웨어 활용률로 완전히 전환되지 못하고 있으며, 특히 NVIDIA GPU에서의 Triton 커널 최적화가 지속적으로 필요하다.

5. **하이브리드 구조의 아키텍처 검색 비용**: SSM과 어텐션의 최적 비율, 배치 위치, 어텐션 유형(full/sparse/sliding window)을 결정하는 데 상당한 실험 비용이 소요된다. 순수 Transformer나 순수 SSM 대비 설계 공간이 크게 확장되어, 하이퍼파라미터 탐색이 더욱 복잡해진다.

## 관련 모델

Mamba-3는 하이브리드 접근법을 채택함으로써 순수 SSM의 "어텐션 없이도 가능하다"는 철학에서 한 걸음 물러섰다. 이는 현재 SSM 기술의 한계를 솔직하게 인정한 것이기도 하다. Sparse attention 레이어로 인해 해당 레이어에서는 KV 캐시가 필요하며, 순수 SSM의 $O(1)$ 메모리 장점을 일부 희석시킨다. 그러나 전체 레이어의 10~15%만 어텐션을 사용하므로 영향은 제한적이며, SSM 기반 모델의 실용 배포를 향한 중요한 진전이다. Griffin(Google DeepMind)이나 Jamba(AI21)보다 적은 어텐션 비율로 경쟁적 성능을 달성했다.

## 참고 자료

- 논문: [Mamba-3: Hybrid State Space Models with Strategic Sparse Attention](https://arxiv.org/abs/2603.15569)
- 코드: [state-spaces/mamba](https://github.com/state-spaces/mamba)

## 관련 문서

- [[mamba-2|Mamba-2]] — 발전 기반
