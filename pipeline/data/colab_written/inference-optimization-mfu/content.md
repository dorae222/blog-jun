# LLM 추론 최적화: MFU부터 프로덕션 서빙까지

## 들어가며

:::info
이 글은 [[reasoning-vs-inference|Reasoning vs Inference]] 시리즈의 **HW Inference** 축에 해당하며, [[mfu-understanding|MFU 3부작]]의 실전 확장편이다.
:::

LLM 추론은 학습과 근본적으로 다른 연산 패턴을 가진다. 학습은 대규모 행렬 곱셈이 지배적인 **compute-bound** 작업인 반면, 추론(특히 디코딩)은 **memory-bound** 작업이다. GPU의 연산 유닛은 대부분 놀고 있고, 메모리에서 가중치를 읽어오는 데 대부분의 시간을 소비한다.

이 차이가 의미하는 바는 명확하다: **학습과 추론은 완전히 다른 최적화 전략이 필요하다**. [[mfu-understanding|MFU]]가 학습 효율의 핵심 지표라면, 추론에서는 **처리량(throughput)**, **지연시간(latency)**, **토큰당 비용(cost per token)**이 핵심 지표다.

---

## 추론 파이프라인: Prefill vs Decode

LLM 추론은 두 단계로 구성된다. 이 구분을 이해하는 것이 모든 최적화의 출발점이다.

### Prefill (프롬프트 처리)

사용자의 입력 프롬프트 전체를 한 번에 처리하는 단계.

- **특성**: 입력 토큰 수에 비례하는 대규모 행렬 곱셈 → **compute-bound**
- **병렬성**: 높음 — 모든 입력 토큰을 동시에 처리 가능
- **MFU**: 상대적으로 높음 (학습과 유사한 연산 패턴)
- **출력**: 첫 번째 출력 토큰 + KV-Cache

### Decode (토큰 생성)

한 번에 **하나의 토큰**을 자기회귀적으로 생성하는 단계.

- **특성**: 단일 토큰을 위해 전체 모델 가중치를 메모리에서 읽어야 함 → **memory-bound**
- **병렬성**: 낮음 — 각 토큰이 이전 토큰에 의존
- **MFU**: 극히 낮음 (단일 벡터-행렬 곱셈)
- **출력**: 토큰 하나씩 순차 생성

### 왜 Decode가 병목인가

Prefill은 수천 토큰을 병렬로 처리하므로 GPU를 충분히 활용한다. 반면 Decode는 **매 토큰마다 전체 모델 가중치를 메모리에서 GPU 연산 유닛으로 전송**해야 한다.

7B 모델(FP16, ~14GB)의 경우:
- **Decode 1 토큰**: 14GB를 메모리에서 읽어야 함
- A100의 메모리 대역폭: 2TB/s
- **최소 소요 시간**: 14GB / 2TB/s ≈ **7ms**
- 이론상 초당 최대 ~143 토큰

실제로는 KV-Cache 읽기, attention 연산 등이 추가되어 이보다 느리다. 따라서 추론 최적화의 핵심은 이 **memory bandwidth 병목을 어떻게 완화하느냐**에 있다.

---

## 핵심 최적화 기법

### 1. KV-Cache

:::tip
**원리**: 이전 토큰의 Key-Value 벡터를 재계산하지 않고 캐시에 저장하여 재사용.
:::

KV-Cache가 없으면, 100번째 토큰 생성 시 이전 99개 토큰에 대한 Key/Value를 모두 재계산해야 한다. KV-Cache는 이 중복 연산을 제거하여 **토큰 생성 속도를 수십 배** 향상시킨다.

**문제: 메모리 소비**

KV-Cache의 크기는 시퀀스 길이에 비례하여 증가한다:

$$\text{KV-Cache 크기} = 2 \times n_{\text{layers}} \times n_{\text{heads}} \times d_{\text{head}} \times \text{seq\_len} \times \text{bytes}$$

LLaMA 3 70B 기준, 시퀀스 길이 8K에서 KV-Cache만 **~10GB**를 차지한다. 추론 모델(DeepSeek-R1 등)은 수천 토큰의 CoT를 생성하므로, KV-Cache 관리가 특히 중요하다.

**해결책들**:
- **GQA (Grouped Query Attention)**: Key-Value 헤드 수를 줄여 캐시 크기 자체를 감소. LLaMA 2+, Gemma 등에서 채택
- **KV-Cache 양자화**: KV 값을 FP8/INT8로 양자화하여 메모리 절감
- **Sliding Window Attention**: 최근 N 토큰만 캐시 (Mistral). 단, 긴 의존성 처리에 제약

### 2. PagedAttention (vLLM)

:::tip
**원리**: 운영체제의 가상 메모리 페이징에서 영감을 받아, KV-Cache를 고정 크기 블록으로 관리.
:::

기존 방식에서는 각 요청에 대해 최대 시퀀스 길이만큼의 연속 메모리를 미리 할당했다. 짧은 응답에서도 전체 버퍼가 예약되어 **60-80%의 메모리가 낭비**되었다.

PagedAttention은 KV-Cache를 **고정 크기 블록(보통 16 토큰 단위)**으로 분할하고, 필요할 때만 블록을 할당한다:
- 메모리 단편화 제거 → 같은 메모리로 **2-4x 더 많은 요청** 동시 처리
- 블록이 연속할 필요 없음 → 가상 메모리처럼 물리적 분산 저장 가능
- 블록 공유 → 동일 프롬프트의 KV-Cache를 여러 요청이 공유 (Parallel sampling)

### 3. Continuous Batching

:::tip
**원리**: 배치 내 완료된 요청을 즉시 제거하고 새 요청을 삽입.
:::

Static Batching에서는 배치 내 가장 긴 요청이 완료될 때까지 모든 GPU 자원이 묶인다. 응답 길이가 10 토큰인 요청과 500 토큰인 요청이 같은 배치에 있으면, 짧은 요청은 490 토큰 동안 GPU를 낭비한다.

Continuous Batching은 **iteration-level scheduling**을 도입한다:
- 매 디코딩 스텝마다 완료된 요청을 제거
- 빈 슬롯에 대기 중인 새 요청을 즉시 삽입
- **결과**: 처리량 2-10x 향상 (요청 길이 편차가 클수록 효과 증가)

### 4. Chunked Prefill

긴 프롬프트의 Prefill 연산을 작은 청크로 분할하여, Decode 요청과 인터리빙하는 기법이다.

**문제**: 10,000 토큰의 긴 프롬프트가 Prefill 중이면, 진행 중인 Decode 요청들이 모두 대기해야 한다 (head-of-line blocking).

**해결**: Prefill을 512-1024 토큰 단위로 분할하고, 각 청크 사이에 Decode 스텝을 삽입. 이를 통해 Prefill의 높은 GPU 활용률과 Decode의 낮은 지연시간을 동시에 달성한다.

### 5. Speculative Decoding

:::tip
**원리**: 작고 빠른 draft 모델이 여러 토큰을 미리 생성하고, 큰 target 모델이 한 번에 검증.
:::

자기회귀 디코딩의 근본적 문제는 **순차적**이라는 것이다. 매 토큰마다 전체 모델을 통과해야 하므로, GPU의 병렬 처리 능력을 활용하지 못한다.

Speculative Decoding의 작동 방식:
1. **Draft**: 작은 모델(예: 1B)이 K개 토큰을 빠르게 생성 (draft tokens)
2. **Verify**: 큰 모델(예: 70B)이 K개 토큰을 **한 번의 forward pass**로 동시 검증
3. **Accept/Reject**: 확률 분포 비교를 통해 수용/거절 결정

검증 단계에서 큰 모델은 K개 토큰을 병렬로 처리하므로, 1개 토큰 처리 비용으로 K개 토큰을 검증할 수 있다. Draft 모델의 정확도가 높을수록 수용률이 높아져 속도 향상이 증가한다.

- **수학적 보장**: Speculative Decoding은 target 모델의 출력 분포를 **정확히 보존**한다. 속도만 바뀌고 품질은 동일
- **속도 향상**: 일반적으로 **2-3x**, draft 모델이 좋으면 **3-5x**까지 가능

### 6. Flash Attention

:::tip
**원리**: Attention 연산의 메모리 접근 패턴을 최적화하여, 수학적으로 동일한 결과를 훨씬 빠르게 계산.
:::

표준 Attention 구현은 중간 결과(Attention matrix)를 GPU의 HBM(느린 메모리)에 쓰고 다시 읽는다. Flash Attention은 이를 **타일링(tiling)**으로 해결한다:

- Q, K, V를 작은 블록으로 분할
- 각 블록을 SRAM(빠른 메모리)에서 처리
- 중간 결과를 HBM에 쓰지 않고 on-the-fly로 통합
- **결과**: HBM 접근 횟수를 $O(N^2)$ → $O(N)$으로 감소

Flash Attention은 **모델 출력을 전혀 변경하지 않는** 순수한 구현 최적화이므로, 학습·추론 모두에서 무조건 사용하는 것이 이득이다. 현재 거의 모든 LLM 프레임워크의 기본 옵션이다.

---

## 서빙 프레임워크 비교

위의 최적화 기법들을 통합하여 프로덕션 배포를 지원하는 대표 프레임워크:

| 프레임워크 | PagedAttention | Continuous Batching | Speculative | FP8/INT4 | Tensor Parallel |
|-----------|:-----------:|:----------------:|:----------:|:-------:|:-------------:|
| **vLLM** | ✅ (창시자) | ✅ | ✅ | ✅ | ✅ |
| **TGI** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **TensorRT-LLM** | ✅ | ✅ | ✅ | ✅ (최고) | ✅ |
| **Ollama** | ❌ | 제한적 | ❌ | GGUF | ❌ |
| **SGLang** | ✅ | ✅ | ✅ | ✅ | ✅ |

### 선택 기준

- **최대 처리량**: TensorRT-LLM (NVIDIA GPU 최적화, 최고 성능)
- **유연성 + 커뮤니티**: vLLM (가장 넓은 모델 지원, 활발한 개발)
- **HuggingFace 생태계**: TGI (모델 허브 통합, 배포 편의성)
- **로컬 실행**: Ollama (간편한 인터페이스, macOS Metal 지원)
- **연구/실험**: SGLang (구조적 생성, 고급 스케줄링)

---

## MFU 관점에서 본 최적화 효과

각 최적화가 GPU 활용률에 미치는 영향을 [[mfu-understanding|MFU]] 관점에서 정리하면:

| 최적화 | 주요 개선 대상 | MFU 영향 |
|--------|-------------|---------|
| KV-Cache | 중복 연산 제거 | 연산량 자체를 감소 |
| PagedAttention | 메모리 효율 | 동시 배치 크기 증가 → MFU 향상 |
| Continuous Batching | GPU 유휴 시간 | 처리량 증가, GPU 활용률 향상 |
| Flash Attention | 메모리 대역폭 | IO 병목 제거 → 연산 유닛 활용 증가 |
| Speculative Decoding | 순차적 병목 | 검증 단계에서 배치 효과로 MFU 향상 |
| 양자화 | 모델 크기 | 메모리 대역폭 요구 감소 → 처리 속도 향상 |

추론에서 MFU가 낮은 근본 원인은 **Decode의 memory-bound 특성**이다. 위 최적화들은 각각 다른 각도에서 이 문제를 완화하며, **조합하여 적용할 때 최대 효과**를 발휘한다.

---

## 정리

LLM 추론 최적화는 Prefill의 compute-bound 특성과 Decode의 memory-bound 특성이라는 **근본적 이중성**에서 출발한다.

핵심 교훈:
1. **Decode가 진짜 병목**: 전체 추론 시간의 대부분을 차지하며, memory bandwidth에 의해 제한된다
2. **최적화는 조합이 핵심**: KV-Cache + PagedAttention + Continuous Batching + Flash Attention을 모두 적용해야 프로덕션 수준의 성능에 도달한다
3. **추론 모델은 더 어렵다**: 긴 CoT 생성으로 KV-Cache가 폭증하고, 토큰당 비용이 일반 LLM의 5-10배에 달한다
4. **[[nvfp4-quantization-concepts|양자화]]와 시너지**: 양자화로 모델 크기를 줄이면 memory bandwidth 병목이 직접적으로 완화된다
