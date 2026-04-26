<!-- infographic-hero -->
![DeepSeek V4 핵심 요약](figures/infographic.svg)

*Figure: DeepSeek V4 한 장 요약 인포그래픽*

# DeepSeek V4 Pro/Flash: 1.6T MoE와 BenchLM 1위의 오픈 가중치 정점

## 개요

DeepSeek V4는 2026년 중국 항저우 소재 DeepSeek AI가 공개한 4세대 General Language Model이다. V3 대비 파라미터 규모를 약 **4배 확장**하면서도 MoE 라우팅과 활성 파라미터 효율을 동시에 개선하였다.

라인업은 두 가지로 분화되었다.

- **DeepSeek V4 Pro**: 1.6T(1조 6천억) 총 파라미터에 49B 활성 파라미터
- **DeepSeek V4 Flash**: 284B 총 파라미터에 13B 활성 파라미터

두 모델 모두 가중치를 공개(open-weights)하였으며, 종합 평가 BenchLM에서 **87점**으로 오픈 가중치 진영 1위를 기록하였다. DeepSeek는 V2의 MLA 도입, V3의 FP8 학습과 MTP 도입에 이어, V4에서는 이 모든 기법을 정교화하면서 동급 폐쇄형 모델 대비 압도적인 가격 효율성을 유지한다.

## 아키텍처 상세

### 기본 구조

| 구성 요소 | V4 Pro | V4 Flash |
|-----------|--------|----------|
| **아키텍처** | MoE Decoder-only Transformer | MoE Decoder-only Transformer |
| **총 파라미터** | 1.6T | 284B |
| **활성 파라미터** | 49B | 13B |
| **어텐션** | MLA (Multi-head Latent Attention) | MLA |
| **정규화** | RMSNorm | RMSNorm |
| **활성화** | SwiGLU | SwiGLU |
| **위치 인코딩** | RoPE | RoPE |
| **학습 정밀도** | FP8 혼합 | FP8 혼합 |
| **보조 목적** | Multi-Token Prediction (MTP) | MTP |
| **라이선스** | Custom (Open Weights) | Custom (Open Weights) |

세부 레이어/전문가 수치는 GitHub에 점진적으로 공개된다.

### Multi-head Latent Attention (MLA)

MLA는 V2에서 처음 도입된 DeepSeek 고유의 어텐션 변형으로, KV 캐시를 잠재 공간으로 압축한다. 표준 MHA의 KV 캐시 크기는

$$\text{KV Cache Size} \propto L \times H \times d_h$$

이지만 (L: 시퀀스 길이, H: 헤드 수, $d_h$: 헤드 차원), MLA는

$$\text{KV Cache Size}_{\text{MLA}} \propto L \times d_c$$

로 압축된다 ($d_c \ll H \times d_h$). 이는 동일 메모리 예산에서 더 긴 컨텍스트와 큰 배치를 처리할 수 있게 한다.

### DeepSeekMoE 라우팅

V4의 MoE 라우팅은 V3 구조를 계승하면서 다음을 정교화하였다.

1. **Auxiliary-loss-free balancing**: 보조 균형 손실 없이도 전문가 활용도를 균형 있게 유지
2. **Shared experts**: 일부 전문가는 모든 토큰에 활성화되어 공통 표현 학습
3. **Routed experts**: 토큰별로 동적으로 선택되는 전문가

라우팅은 다음과 같이 표현된다.

$$g_i = \text{TopK}(\text{Softmax}(W_g x), k)$$

여기서 $g_i$는 i번째 토큰에 대한 전문가 선택 확률이다.

## 핵심 혁신

### 1. MoE 스케일과 효율의 균형

V4 Pro의 1.6T 총 파라미터는 약 256개 전문가에 활성 8개 라우팅 구조로 추정되며, 활성 49B만으로 1.6T급 표현력을 확보한다. 이는 추론 비용 면에서 49B Dense 모델과 동일한 수준이면서, 능력은 1.6T 모델에 근접하는 효율을 의미한다.

Flash 변형은 비용 민감 시나리오를 위해 분리되었으며, 13B 활성 파라미터로 빠르고 저렴한 추론을 제공한다. 이러한 라인업 분화는 DeepSeek가 폐쇄형 진영의 Pro/Mini/Nano 패턴을 오픈 가중치 진영에 도입한 사례이다.

### 2. FP8 혼합 정밀도 학습의 정교화

V3에서 도입된 FP8 학습은 V4에서 더 안정화되었다. FP8은 8비트 부동소수점으로, BF16 대비 메모리와 통신 비용을 절반으로 줄인다. DeepSeek는 활성/그래디언트별로 다른 양자화 전략을 적용하여 수치 안정성을 확보한다.

### 3. 다중 토큰 예측 (MTP)

표준 LM은 한 번에 한 토큰을 예측하지만, MTP는 향후 $k$개 토큰을 동시에 예측하는 보조 목적을 추가한다.

$$L_{\text{total}} = L_{\text{LM}} + \lambda \sum_{i=1}^{k} L_{\text{MTP},i}$$

이는 토큰당 학습 신호를 증가시켜 학습 효율을 높이며, 추론 시에는 추측 디코딩(speculative decoding)과 결합하여 처리량을 가속한다.

### 4. 학습 비용 효율

DeepSeek는 V3에서 약 600만 달러 수준의 학습 비용을 보고하여 화제가 되었다. V4 Pro는 4배 파라미터 확장에도 학습 비용은 약 2배 수준으로 억제된 것으로 추정되며, 이는 폐쇄형 모델 대비 한 자릿수 비율의 비용으로 동급 성능을 달성하였음을 의미한다.

## 벤치마크/성능

### 종합 벤치마크 비교

| 벤치마크 | DeepSeek V4 Pro | DeepSeek V4 Flash | DeepSeek V3 | GLM-5.1 |
|----------|-----------------|-------------------|-------------|---------|
| **BenchLM** | **87** | 약 80 | 약 78 | 약 82 |
| **SWE-bench Verified** | 약 79% | 약 72% | 약 65% | 약 76% |
| **GPQA Diamond** | 약 85% | 약 75% | 약 75% | 약 80% |
| **MATH-500** | 약 95% | 약 88% | 약 90% | 약 88% |
| **활성 파라미터** | 49B | 13B | 37B | 미공개 |
| **총 파라미터** | 1.6T | 284B | 671B | 미공개 |
| **API 가격** | 매우 저렴 | 더 저렴 | 저렴 | 저렴 |

### 폐쇄형 모델 대비 성능 비율

| 항목 | V4 Pro / Claude Opus 4.7 |
|------|--------------------------|
| **SWE-bench** | 약 96% |
| **GPQA Diamond** | 약 94% |
| **MATH-500** | 약 100%+ |
| **API 가격** | 약 5~10% (압도적 저렴) |

## 한계 및 의의

### 한계

1. **컨텍스트 길이 미공개**: V3에서는 128K였으며 V4의 정확한 길이는 추가 발표가 필요하다.
2. **추론 인프라 부담**: 1.6T 총 파라미터는 추론 시에도 모든 전문가 가중치를 메모리에 적재해야 하므로, 자체 호스팅에는 다수 GPU가 필요하다.
3. **에이전트/도구 호출 신뢰성**: Claude Opus 4.7이나 GPT-5.5 대비 함수 호출 신뢰성이 다소 낮은 것으로 평가된다.
4. **라이선스 제약**: 오픈 가중치이지만 상업적 이용에 일부 제약이 있는 Custom 라이선스이다.

### 의의

DeepSeek V4는 **오픈 가중치 진영이 폐쇄형 최상위 모델의 95% 이상을 따라잡았음**을 입증한 모델이다. 첫째, BenchLM 87점 1위는 학술 평가에서 폐쇄형 모델과의 격차가 사실상 사라졌음을 의미한다. 둘째, MLA, MTP, FP8 학습 등의 기법은 향후 모든 진영의 표준 도구로 확산될 것이다. 셋째, 한 자릿수 비율의 학습 비용으로 동급 성능을 달성한 것은 AI 인프라 경제학의 패러다임 전환을 시사한다.

향후 DeepSeek는 멀티모달 확장(VL 계열), 추론 특화 모델(R3 등), 그리고 더 큰 활성 파라미터를 갖는 V5 세대로 확장할 것으로 전망된다.

## 관련 문서

- [[deepseek-v3|DeepSeek V3]] - 직접적 발전 기반
- [[deepseek-v2|DeepSeek V2]] - MLA 최초 도입 모델
- [[deepseek-r1|DeepSeek R1]] - GRPO 추론 학습 원형
- [[glm-5-1|GLM-5.1]] - 동시대 오픈 가중치 경쟁 모델
