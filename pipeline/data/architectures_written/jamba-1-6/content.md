# Jamba 1.6: 대규모 하이브리드 SSM-Transformer의 기업용 진화

**AI21 Labs** · **2025-03-27** · **llm** · **Jamba Open Model License**

## 개요

Jamba 1.6는 AI21 Labs가 2025년 3월 27일 공개한 차세대 하이브리드 SSM-Transformer 언어 모델로, 2024년 3월 공개된 초대 Jamba(52B/12B active)의 대규모 후속작이다. 전체 파라미터를 398B로 확장하면서도 MoE 구조를 통해 토큰당 52B만 활성화하며, Mamba SSM과 Transformer Attention의 인터리브드 설계로 256K 토큰 컨텍스트를 기존 순수 Transformer 대비 극적으로 낮은 메모리 비용으로 처리한다.

Jamba 1.6의 개발 동기는 기업 환경에서의 실용적 장문 처리 문제에 있다. 법률 계약서, 기업 재무 보고서, 대규모 코드베이스 분석 등 실제 비즈니스 시나리오에서는 수만~수십만 토큰의 입력을 처리해야 하는 경우가 빈번하다. 순수 Transformer 모델은 이 규모에서 KV 캐시만으로 수십 GB의 GPU 메모리를 소모하지만, Jamba 1.6의 하이브리드 설계는 SSM 레이어의 고정 크기 상태 벡터 덕분에 이 문제를 근본적으로 해결한다.

특히 처리량(throughput) 기준으로 동급 Transformer 모델 대비 3배 이상의 효율을 달성하여, API 서빙 비용 절감에 직접적으로 기여한다. 기업용 AI 솔루션에서는 성능뿐 아니라 비용 효율이 채택 결정의 핵심 요소이며, Jamba 1.6는 이 두 가지를 동시에 충족하는 모델로 자리매김하였다.

![Architecture](figures/architecture.svg)

## 아키텍처 상세

### 하이브리드 SSM-Attention 인터리브드 구조

Jamba 1.6는 초대 Jamba에서 검증된 Mamba SSM과 Transformer Attention의 교차 배치 구조를 계승하되, 규모를 대폭 확장하였다.

| 구성 요소 | Jamba (초대) | Jamba 1.6 |
|-----------|-------------|----------|
| 전체 파라미터 | 52B | **398B** |
| 활성 파라미터 | 12B | **52B** |
| 컨텍스트 길이 | 256K | **256K** |
| 어휘 크기 | 65,536 | **65,536** |
| 정규화 | RMSNorm | **RMSNorm** |
| 활성화 | SiLU | **SwiGLU** |
| Attention:Mamba 비율 | 1:3 | **~1:3 (계승)** |

반복 블록의 기본 구조는 초대 Jamba의 패턴을 따른다:

```
[Mamba + MoE] → [Mamba + MoE] → [Mamba + MoE] → [Attention + MoE]
```

이 4-레이어 블록이 반복되어 전체 모델을 구성하며, 전체 레이어의 약 75%가 Mamba SSM, 약 25%가 Attention이다.

### Mamba SSM(Selective State Space Model)

Mamba 레이어는 Gu & Dao(2023)의 선택적 상태 공간 모델(S6)을 기반으로 한다. 핵심 재귀 수식은 다음과 같다:

$$h_t = \bar{A}_t h_{t-1} + \bar{B}_t x_t$$
$$y_t = C_t h_t + D x_t$$

여기서 $\bar{A}_t$와 $\bar{B}_t$는 입력 $x_t$에 의존하는 이산화된 상태 전이 행렬이다. '선택적(selective)'이라 불리는 이유는 이 행렬들이 입력에 따라 동적으로 변화하여, 관련 정보를 선택적으로 기억하거나 잊을 수 있기 때문이다.

SSM의 핵심 장점은 시퀀스 길이에 대한 **선형 복잡도** $O(n)$이다:

| 메커니즘 | 시간 복잡도 | 공간 복잡도 (KV 캐시) |
|----------|-----------|---------------------|
| Self-Attention | $O(n^2 \cdot d)$ | $O(n \cdot d)$ — 시퀀스에 비례 |
| Mamba SSM | $O(n \cdot d \cdot s)$ | $O(d \cdot s)$ — 고정 크기 |

여기서 $n$은 시퀀스 길이, $d$는 히든 차원, $s$는 SSM 상태 크기이다. SSM은 시퀀스 길이와 무관하게 고정 크기의 상태 벡터만 유지하므로, 256K 같은 초장문에서도 메모리 사용량이 거의 증가하지 않는다.

### MoE(Mixture of Experts) 통합

Jamba 1.6는 대부분의 레이어에 MoE를 적용한다. 각 토큰은 라우터(router)에 의해 최적의 전문가 조합으로 라우팅된다:

$$y = \sum_{i \in \text{TopK}} g_i \cdot E_i(x), \quad g = \text{TopK}(\text{Softmax}(W_r \cdot x))$$

398B 전체 파라미터 중 토큰당 52B만 활성화되므로, 추론 시 실제 연산량은 52B Dense 모델과 유사하면서도 398B에 해당하는 모델 용량을 확보한다.

### Attention 레이어의 보완적 역할

전체의 약 25%를 차지하는 Attention 레이어는 SSM의 약점을 보완한다. SSM은 순차적 상태 압축의 특성상 특정 위치의 정보를 정확히 검색(retrieval)하는 데 한계가 있다. Attention은 전체 시퀀스에서 원하는 위치의 정보를 직접 참조할 수 있어, needle-in-a-haystack 같은 정밀 검색 태스크에서 SSM을 보완한다:

$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right) V$$

### SwiGLU 활성화 함수

초대 Jamba의 SiLU에서 SwiGLU로 업그레이드되었다:

$$\text{SwiGLU}(x, W, V) = \text{SiLU}(xW) \otimes (xV)$$

SwiGLU는 게이트 메커니즘을 통해 정보 흐름을 선택적으로 제어하며, LLaMA, Mistral 등 현대 LLM에서 표준으로 채택된 활성화 함수이다.

## 핵심 혁신

### 1. 삼중 하이브리드의 대규모 검증

Jamba 1.6는 SSM + Attention + MoE라는 세 가지 효율화 기법을 398B 규모에서 동시에 결합한 모델이다. 각 기법의 효율화 축은 서로 독립적이다:

- **SSM**: 시퀀스 길이에 대한 선형 복잡도 → 장문 처리 메모리 효율
- **Attention**: 전역 의존성 정밀 포착 → 정보 검색 품질 보장
- **MoE**: 파라미터 대비 활성 연산량 절감 → 추론 비용 효율

### 2. KV 캐시 최소화

전체 레이어의 75%가 Mamba SSM이므로, 256K 컨텍스트에서도 KV 캐시 메모리 사용이 극적으로 줄어든다. 순수 Transformer가 256K 처리에 A100 80GB 4~8장을 필요로 하는 반면, Jamba 1.6는 훨씬 적은 GPU로 동일 컨텍스트를 처리할 수 있다.

### 3. 처리량 3배 이상

동급 Transformer 모델 대비 3배 이상의 추론 처리량을 달성하여, 동시 요청이 많은 API 서비스 환경에서의 서빙 비용을 크게 절감한다.

## 벤치마크/성능

| 벤치마크 | Jamba 1.6 (52B active) | Llama 3.1 70B | Mixtral 8x22B | Command R+ |
|---------|----------------------|---------------|---------------|------------|
| MMLU | ~75% | 79.3% | 81.2% | 75.7% |
| HumanEval | ~72% | 80.5% | 78.0% | 71.7% |
| GSM8K | ~80% | 83.7% | 81.0% | 74.3% |
| 처리량 (상대) | **3x+** | 1x | ~1.2x | ~0.8x |
| 256K KV 캐시 | **최소** | 대형 | 대형 | 대형 |

### 효율성 비교

| 지표 | Jamba 1.6 | 동급 순수 Transformer |
|------|-----------|---------------------|
| 256K 처리 시 GPU 수 | 1-2x A100 80GB | 4-8x A100 80GB |
| 토큰당 추론 비용 | 낮음 | 높음 |
| 처리량 (tokens/sec) | ~3x | 1x (기준) |
| 장문 품질 유지 | 우수 | 위치 편향 발생 가능 |

## 학습

대규모 다국어 데이터와 코드, 명령 수행(instruction following) 데이터를 혼합하여 사전 학습하였다. 하이브리드 SSM-Attention 구조의 특성상, 장문 컨텍스트 연속성을 유지하기 위한 특화 훈련 기법이 적용되었다. 구체적인 토큰 수 및 데이터 구성은 공개되지 않았다. Instruct 버전은 SFT와 DPO를 통해 정렬되었으며, SwiGLU 활성화 함수로의 전환은 학습 안정성과 최종 성능 모두에 긍정적 효과를 가져온 것으로 알려져 있다.

## 관련 모델

| 모델 | 아키텍처 | 파라미터 (전체/활성) | 컨텍스트 | 장문 효율 |
|------|---------|-------------------|---------|----------|
| Jamba (초대) | SSM+Attn+MoE | 52B/12B | 256K | 높음 |
| **Jamba 1.6** | **SSM+Attn+MoE** | **398B/52B** | **256K** | **최고** |
| Mixtral 8x22B | MoE Transformer | 176B/39B | 64K | 중간 |
| LLaMA 3 70B | Dense Transformer | 70B/70B | 128K | 낮음 |
| Mamba-2 | Pure SSM | 2.7B | 가변 | 높음 |

Jamba 1.6는 순수 SSM(Mamba-2)이나 순수 Transformer(LLaMA 3)와 달리 두 구조의 장점을 결합하는 하이브리드 접근을 취한다. 이 접근은 RWKV, Griffin, Qwen3.5 DeltaNet 등 다른 비-Attention 아키텍처 연구와 함께 포스트-Transformer 아키텍처의 중요한 축을 형성하고 있다.

## 참고 자료

- [Jamba 1.6 발표 블로그](https://www.ai21.com/blog/jamba-1-6)
- [Jamba 원본 논문 (arXiv:2403.19887)](https://arxiv.org/abs/2403.19887)

## 관련 문서

- [[jamba|Jamba: A Hybrid Transformer-Mamba Language Model]] — 발전 기반
