# Reasoning vs Inference: AI 효율성의 두 축

## 들어가며

LLM 시대에 "효율성"이라는 단어는 두 가지 완전히 다른 의미로 사용된다.

하나는 **"어떻게 더 잘 생각하게 할 것인가"** — Chain-of-Thought, 추론 모델, test-time compute scaling 등 모델의 **추론 품질**을 높이는 SW 관점의 효율성이다. 다른 하나는 **"어떻게 더 빠르게 실행할 것인가"** — 양자화, KV-Cache, Multi-GPU 병렬 처리 등 같은 모델을 **더 적은 자원으로 실행**하는 HW 관점의 효율성이다.

이 두 축은 독립적이면서도 상호 보완적이다. 추론 모델(DeepSeek-R1, o1)은 더 많은 토큰을 생성하여 더 잘 "생각"하지만, 그만큼 Inference 비용도 증가한다. 반대로 양자화된 모델은 빠르게 실행되지만, 추론 품질이 저하될 수 있다. **두 축의 최적 균형점을 찾는 것**이 현대 LLM 배포의 핵심 과제다.

이 글은 두 축의 전체 지형도를 제시하고, 각 기술의 위치와 관계를 정리하는 **시리즈 개론**이다.

---

## SW 축: Reasoning — "어떻게 더 잘 생각하게 할 것인가"

SW Reasoning은 모델 아키텍처나 하드웨어를 변경하지 않고, **모델이 문제를 푸는 방식**을 개선하는 접근법이다. 핵심 아이디어는 "더 많이 생각하면 더 나은 답을 얻는다"는 것이다.

### Chain-of-Thought (CoT)

CoT(Wei et al., 2022)는 모델이 최종 답변 전에 **중간 추론 과정을 명시적으로 생성**하도록 유도하는 기법이다. "Let's think step by step"이라는 단순한 프롬프트 추가만으로도 수학, 논리, 상식 추론에서 극적인 성능 향상을 달성했다.

CoT의 핵심 통찰:
- 모델은 이미 추론 능력을 보유하고 있지만, 중간 단계를 건너뛰면 오류가 누적된다
- 명시적 추론 체인이 "작업 메모리(working memory)" 역할을 수행
- 문제의 복잡도가 높을수록 CoT의 이점이 커진다

이후 Self-Consistency(Wang et al., 2023), Tree of Thoughts(Yao et al., 2023) 등으로 발전하며, **다양한 추론 경로를 탐색하고 최적의 답을 선택**하는 방향으로 진화했다.

### Test-Time Compute Scaling

Snell et al.(2024)의 "Scaling LLM Test-Time Compute"는 중요한 관찰을 제시했다: **학습 시간(training-time)에 투입하는 연산을 추론 시간(test-time)으로 이동**시키면, 더 작은 모델로도 큰 모델의 성능에 도달할 수 있다.

핵심 원리:
- **Search**: 여러 후보 답변을 생성하고 최선을 선택 (Best-of-N, beam search)
- **Verification**: Process Reward Model(PRM)로 각 추론 단계를 평가
- **Adaptive compute**: 쉬운 문제에는 적은 연산, 어려운 문제에는 많은 연산 할당

이 패러다임의 실질적 함의는, 모델 크기를 키우는 것만이 성능 향상의 유일한 경로가 아니라는 점이다. 때로는 더 작은 모델에 더 많은 추론 시간을 투자하는 것이 비용 효율적이다.

### Reasoning 모델: o1, DeepSeek-R1, QwQ

2024-2025년에 등장한 추론 모델들은 CoT와 test-time compute scaling을 **모델 자체에 내재화**한 사례다.

- **OpenAI o1/o3**: 내부적으로 긴 추론 체인을 생성한 후 최종 답변만 출력. 학습 과정에서 RL(강화학습)을 사용하여 추론 전략을 최적화
- **DeepSeek-R1**: RL만으로 모델이 스스로 CoT를 학습하는 것이 가능함을 보여준 오픈소스 모델. 순수 RL(R1-Zero)과 SFT+RL(R1) 두 가지 경로를 모두 검증
- **QwQ-32B**: Reasoning 능력에 특화된 32B 모델. [[openthoughts3-dataset]]에서 교사 모델로 선택된 것처럼, 크기 대비 효율적인 추론 체인을 생성

### Distillation of Reasoning

추론 모델의 "생각하는 과정"을 작은 모델에 전달하는 것이 [[distillation-guide|지식 증류]]이다. OpenThoughts3-1.2M은 이 접근법의 대표적 성과로, QwQ-32B의 추론 체인을 7B 모델에 증류하여 SFT만으로 SOTA를 달성했다.

증류의 핵심 교훈:
- 교사 모델이 너무 크면 학생이 따라할 수 없다 (용량 격차 문제)
- 추론 과정(CoT)의 증류가 최종 답변만의 증류보다 효과적
- 다양한 풀이 경로 노출(16x 샘플링)이 단일 정답보다 효과적

---

## HW 축: Inference — "어떻게 더 빠르게 실행할 것인가"

HW Inference 최적화는 모델의 추론 품질을 유지하면서, **같은 작업을 더 적은 시간과 자원으로 수행**하는 접근법이다.

### 양자화 (Quantization)

[[quantization-guide|양자화]]는 모델의 가중치와 활성화를 낮은 비트 수로 표현하여 메모리 사용량과 연산 비용을 줄이는 기법이다. [[floating-point-arithmetic|부동소수점]] 표현의 정밀도를 낮추는 것이 핵심이다.

| 포맷 | 비트 | 메모리 절감 | 정확도 영향 | 대표 기법 |
|------|------|-----------|-----------|----------|
| FP16/BF16 | 16 | 2x | 거의 없음 | 기본 혼합 정밀도 |
| INT8 | 8 | 4x | 최소 | Dynamic/Static Quantization |
| FP8 | 8 | 4x | 최소 | H100 Transformer Engine |
| INT4/NF4 | 4 | 8x | 소폭 | GPTQ, AWQ, QLoRA |
| FP4/NVFP4 | 4 | 8x | 소폭 | Blackwell GPU 네이티브 |

4비트 양자화(INT4/NVFP4)는 70B 모델을 단일 GPU에 탑재할 수 있게 해주며, 이는 추론 모델의 실용적 배포에 결정적인 역할을 한다.

### KV-Cache와 메모리 관리

Transformer의 자기회귀(autoregressive) 디코딩에서, 이전 토큰의 Key-Value 벡터를 재계산하지 않고 캐시에 저장하는 기법이다. 긴 시퀀스에서 KV-Cache는 GPU 메모리의 주요 병목이 된다.

주요 최적화:
- **PagedAttention** (vLLM): 운영체제의 가상 메모리 관리에서 영감을 받아, KV-Cache를 고정 크기 블록으로 분할하여 메모리 단편화 제거
- **Grouped Query Attention (GQA)**: Key-Value 헤드 수를 줄여 캐시 크기 자체를 감소 (LLaMA 2+, Gemma 등)
- **Sliding Window Attention**: 전체 시퀀스가 아닌 최근 N 토큰만 캐시 (Mistral)

추론 모델은 긴 CoT를 생성하므로, KV-Cache 관리가 특히 중요하다. DeepSeek-R1은 수천 토큰의 추론 체인을 생성하는데, 이 과정에서 KV-Cache가 급격히 증가한다.

### Batching 전략

여러 요청을 묶어 GPU 활용률을 높이는 전략:

- **Static Batching**: 배치 내 모든 요청이 완료될 때까지 대기 — 비효율적
- **Continuous Batching**: 완료된 요청을 즉시 제거하고 새 요청을 삽입 — 처리량 대폭 향상
- **Chunked Prefill**: 긴 프롬프트의 prefill 단계를 청크로 분할하여 디코딩과 인터리빙

### Speculative Decoding

작고 빠른 "초안(draft)" 모델로 여러 토큰을 미리 생성하고, 큰 "검증(verify)" 모델이 한 번에 검증하는 기법이다. 자기회귀 디코딩의 순차적 병목을 우회하여 2-3x 속도 향상을 달성한다.

Speculative Decoding은 **SW Reasoning과 HW Inference가 만나는 교차점**이기도 하다. 초안 모델이 "빠르게 생각"하고, 검증 모델이 "깊게 검증"하는 구조는, CoT의 "생각 → 검증" 패턴과 구조적으로 유사하다.

### Flash Attention

Attention 연산의 메모리 접근 패턴을 최적화하여, 수학적으로 동일한 결과를 **2-4x 빠르게** 계산하는 기법이다. GPU의 SRAM(빠르지만 작음)과 HBM(크지만 느림) 사이의 데이터 이동을 최소화하는 것이 핵심 원리다.

Flash Attention은 모델의 출력을 전혀 변경하지 않으면서 순수하게 속도만 향상시키므로, 사실상 모든 현대 LLM 학습·추론에 기본 적용되고 있다.

### Multi-GPU와 인터커넥트

단일 GPU의 메모리 한계를 넘어서기 위한 병렬 처리 전략:

- **Tensor Parallelism**: 모델의 각 레이어를 여러 GPU에 분산 — 추론 레이턴시 감소에 효과적
- **Pipeline Parallelism**: 모델의 레이어 그룹을 각 GPU에 순차 배치 — 대규모 모델 탑재에 효과적
- **Data Parallelism (DDP/FSDP)**: 동일 모델을 여러 GPU에 복제하고 데이터를 분할 — 학습에 주로 사용

GPU 간 통신 대역폭은 병렬 처리의 효율을 결정하는 핵심 요소다. PCIe(64 GB/s) 대비 NVLink(900 GB/s, 5세대)는 14배 빠른 대역폭을 제공하며, 이 차이는 Tensor Parallelism의 실효성에 직접적인 영향을 미친다.

### 서빙 프레임워크

위의 최적화 기법들을 통합하여 프로덕션 배포를 지원하는 프레임워크:

| 프레임워크 | 핵심 특징 | 주요 최적화 |
|-----------|----------|-----------|
| **vLLM** | PagedAttention 창시, 높은 처리량 | Continuous batching, Tensor parallelism |
| **TGI** | HuggingFace 통합, 사용 편의성 | Flash Attention, Quantization |
| **TensorRT-LLM** | NVIDIA GPU 최적화, 최고 성능 | FP8/INT4, Custom CUDA kernels |
| **Ollama** | 로컬 실행 특화, 간편한 인터페이스 | GGUF 양자화, Metal (macOS) |

---

## 두 축의 교차점

SW Reasoning과 HW Inference는 독립적 영역이 아니라, 여러 지점에서 교차한다.

### 1. 추론 모델의 효율적 배포

추론 모델(o1, DeepSeek-R1)은 긴 CoT를 생성하므로, 일반 LLM 대비 **토큰 생성량이 5-10배** 많다. 이는 곧:
- KV-Cache 메모리 사용량 급증
- 추론 시간(latency) 증가
- API 비용 상승

따라서 추론 모델일수록 HW Inference 최적화가 더 절실하다. DeepSeek-R1의 MoE 아키텍처 선택도 이 맥락에서 이해할 수 있다 — 671B 파라미터 중 실제 활성화되는 것은 37B에 불과하여, Inference 비용을 크게 절감한다.

### 2. 양자화된 추론 모델

4비트 양자화된 DeepSeek-R1이나 QwQ-32B는 소비자급 GPU(RTX 3090/4090)에서도 실행 가능하다. 이때 핵심 질문은: "양자화가 추론 품질에 얼마나 영향을 미치는가?"이다.

최근 연구들은 **추론 과정(CoT)이 양자화에 상대적으로 견고(robust)**하다는 결과를 보여준다. 추론의 "논리 구조"는 가중치의 미세한 정밀도보다는 모델의 고수준 패턴에 의존하기 때문이다.

### 3. Speculative Decoding + Reasoning

작은 모델이 CoT 초안을 생성하고, 큰 모델이 검증하는 구조는 Speculative Decoding과 자연스럽게 결합된다. 이 조합은 추론 품질을 유지하면서 속도를 크게 향상시킬 수 있는 유망한 방향이다.

---

## MFU: 두 축을 연결하는 지표

[[mfu-understanding|MFU(Model FLOPs Utilization)]]는 GPU의 이론적 최대 연산 능력 대비 실제 활용률을 나타내는 지표다. HW Inference 최적화의 "효과"를 정량적으로 측정하는 데 핵심적인 역할을 한다.

- [[mfu-understanding]]: MFU의 개념과 계산 방법
- [[mfu-optimization]]: MFU를 높이는 최적화 전략
- [[mfu-layer-flops]]: 레이어별 FLOPs 분석

MFU가 낮다는 것은 GPU가 실제 연산보다 **메모리 접근, 통신, 대기**에 더 많은 시간을 쓴다는 의미이며, 이는 위에서 설명한 Flash Attention, Tensor Parallelism, Continuous Batching 등의 최적화가 필요한 이유이기도 하다.

---

## 시리즈 로드맵

이 글은 아래 후속 컨텐츠들의 "지도" 역할을 한다:

### HW Inference 경로
1. **양자화 심화**: NVFP4와 현대 양자화 포맷 비교 (FP4/FP8/INT4/INT8)
2. **추론 최적화**: Prefill vs Decode 파이프라인, KV-Cache, Speculative Decoding
3. **Multi-GPU**: DDP, FSDP, Tensor Parallelism 실전
4. **NVLink**: GPU 인터커넥트가 병렬 처리에 미치는 영향

### SW Reasoning 경로
1. [[openthoughts3-dataset]]: 추론 데이터 큐레이션의 체계적 방법론
2. **Test-time Compute Scaling**: 추론 시간에 더 생각하기
3. **Process Reward Models**: 단계별 보상으로 추론 향상

### 기존 컨텐츠
- [[quantization-guide]]: 양자화 기초 (Dynamic, Static, QAT)
- [[floating-point-arithmetic]]: 부동소수점 표현의 이해
- [[distillation-guide]]: 지식 증류 기초
- [[pruning-guide]]: 모델 프루닝
- [[onnx-optimization]]: ONNX 런타임 최적화
- [[mfu-understanding]] / [[mfu-optimization]] / [[mfu-layer-flops]]: MFU 3부작

---

## 정리

| 축 | 핵심 질문 | 대표 기술 | 비용 |
|-----|----------|----------|------|
| **SW Reasoning** | 어떻게 더 잘 생각하게 할까? | CoT, 추론 모델, PRM, 증류 | 더 많은 토큰 생성 |
| **HW Inference** | 어떻게 더 빠르게 실행할까? | 양자화, KV-Cache, Flash Attention, Multi-GPU | 구현 복잡도 |
| **교차점** | 두 축의 균형은? | Speculative Decoding, 양자화된 추론 모델, MoE | 설계 트레이드오프 |

두 축은 경쟁 관계가 아니라 **보완 관계**다. SW Reasoning이 "생각의 품질"을 높이면, HW Inference가 "생각의 비용"을 낮추고, 그 결과 더 많은 사람이 더 나은 AI를 사용할 수 있게 된다. 이 시리즈에서는 각 축의 핵심 기술을 하나씩 깊이 다루며, 실전에서의 적용 방법을 탐구한다.
