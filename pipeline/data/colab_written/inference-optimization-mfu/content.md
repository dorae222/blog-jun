<!-- infographic-hero -->
![LLM Inference Optimization: From MFU to Production Serving 핵심 요약](figures/infographic.svg)

*Figure: LLM Inference Optimization: From MFU to Production Serving 한 장 요약 인포그래픽*

# LLM 추론 최적화: MFU부터 프로덕션 서빙까지

## 들어가며

:::info
이 글은 LLM 추론 최적화의 전체 그림을 다루는 실전 가이드이다. [[multi-gpu-parallel-pytorch]]에서 다룬 병렬 처리 전략 위에, 추론 단계에서의 핵심 최적화 기법과 프로덕션 서빙 프레임워크를 비교 정리한다.
:::

LLM 추론은 학습과 근본적으로 다른 연산 패턴을 가진다. 학습은 대규모 행렬 곱셈이 지배적인 **compute-bound** 작업인 반면, 추론(특히 디코딩)은 **memory-bound** 작업이다. GPU의 연산 유닛은 대부분 놀고 있고, 메모리에서 가중치를 읽어오는 데 대부분의 시간을 소비한다.

이 차이가 의미하는 바는 명확하다. **학습과 추론은 완전히 다른 최적화 전략이 필요하다**. MFU가 학습 효율의 핵심 지표라면, 추론에서는 **처리량(throughput)**, **지연시간(latency)**, **토큰당 비용(cost per token)**이 핵심 지표다.

---

## 추론 핵심 지표

추론 최적화를 논의하기 전에, 성능을 측정하는 핵심 지표를 정리한다.

| 지표 | 정의 | 단위 | 중요도 |
|------|------|------|--------|
| TTFT | Time to First Token. 요청 후 첫 토큰까지 지연시간 | ms | 체감 속도 |
| ITL | Inter-Token Latency. 토큰 간 생성 간격 | ms | 스트리밍 품질 |
| Throughput | 초당 생성 토큰 수 (전체 시스템) | tok/s | 서버 효율 |
| Latency | 전체 응답 완료까지 걸리는 시간 | ms | 사용자 경험 |
| Cost/Token | 토큰 하나 생성에 드는 비용 | $/Mtok | 운영 비용 |
| MFU | GPU 이론 최대 연산 대비 실제 활용률 | % | HW 효율 |

TTFT는 Prefill 성능에 의존하고, ITL은 Decode 성능에 의존한다. 처리량은 배칭 전략에 크게 좌우된다.

---

## MFU(Model FLOPs Utilization) 정의와 계산

MFU는 GPU의 이론적 최대 연산 성능 대비 실제로 모델 연산에 사용된 비율을 나타내는 지표다.

$$\text{MFU} = \frac{\text{실제 모델 FLOPs}}{\text{GPU 이론 최대 FLOPs} \times \text{소요 시간}}$$

### 학습 vs 추론의 MFU

| 구분 | 학습 | 추론 (Prefill) | 추론 (Decode) |
|------|------|---------------|--------------|
| 지배적 연산 | 대규모 행렬 곱셈 | 대규모 행렬 곱셈 | 벡터-행렬 곱셈 |
| 연산 특성 | compute-bound | compute-bound | memory-bound |
| 병렬성 | 높음 (배치 크기 확장) | 높음 (입력 토큰 병렬) | 극히 낮음 (순차 생성) |
| 전형적 MFU | 30~60% | 20~50% | **1~5%** |
| 병목 요인 | 통신, 메모리 | 통신 | **메모리 대역폭** |

Decode 단계의 MFU가 극히 낮은 이유는, 단일 토큰을 위해 전체 모델 가중치를 메모리에서 읽어야 하기 때문이다. A100 80GB의 이론 연산 성능은 312 TFLOPS(BF16)인데, Decode 시에는 이 중 1~5%만 활용된다.

### GPU별 이론 성능과 추론 처리 능력

| GPU | FP16/BF16 TFLOPS | HBM 대역폭 | HBM 용량 | Decode 이론 최대 (7B) | Decode 이론 최대 (70B) |
|-----|:-----------------:|:----------:|:--------:|:--------------------:|:---------------------:|
| A100 80GB | 312 | 2.0 TB/s | 80 GB | ~143 tok/s | ~14 tok/s |
| H100 SXM | 990 | 3.35 TB/s | 80 GB | ~239 tok/s | ~24 tok/s |
| H200 | 990 | 4.8 TB/s | 141 GB | ~343 tok/s | ~34 tok/s |
| RTX 4090 | 165 | 1.0 TB/s | 24 GB | ~71 tok/s | N/A (메모리 부족) |
| L40S | 362 | 0.86 TB/s | 48 GB | ~61 tok/s | N/A (메모리 부족) |

> **Decode 이론 최대**: FP16 모델 가중치 크기 / HBM 대역폭으로 계산. 실제로는 KV-Cache, attention 연산 오버헤드로 이보다 낮다.

---

## 추론 파이프라인: Prefill vs Decode

LLM 추론은 두 단계로 구성된다. 이 구분을 이해하는 것이 모든 최적화의 출발점이다.

### Prefill (프롬프트 처리)

사용자의 입력 프롬프트 전체를 한 번에 처리하는 단계다.

- **특성**: 입력 토큰 수에 비례하는 대규모 행렬 곱셈이므로 **compute-bound**
- **병렬성**: 높음. 모든 입력 토큰을 동시에 처리 가능
- **MFU**: 상대적으로 높음 (학습과 유사한 연산 패턴)
- **출력**: 첫 번째 출력 토큰 + KV-Cache

### Decode (토큰 생성)

한 번에 **하나의 토큰**을 자기회귀적으로 생성하는 단계다.

- **특성**: 단일 토큰을 위해 전체 모델 가중치를 메모리에서 읽어야 하므로 **memory-bound**
- **병렬성**: 낮음. 각 토큰이 이전 토큰에 의존
- **MFU**: 극히 낮음 (단일 벡터-행렬 곱셈)
- **출력**: 토큰 하나씩 순차 생성

### Decode가 병목인 이유

Prefill은 수천 토큰을 병렬로 처리하므로 GPU를 충분히 활용한다. 반면 Decode는 **매 토큰마다 전체 모델 가중치를 메모리에서 GPU 연산 유닛으로 전송**해야 한다.

7B 모델(FP16, ~14GB)의 경우:
- **Decode 1 토큰**: 14GB를 메모리에서 읽어야 함
- A100의 메모리 대역폭: 2TB/s
- **최소 소요 시간**: 14GB / 2TB/s = **7ms**
- 이론상 초당 최대 ~143 토큰

실제로는 KV-Cache 읽기, attention 연산 등이 추가되어 이보다 느리다. 따라서 추론 최적화의 핵심은 이 **memory bandwidth 병목을 어떻게 완화하느냐**에 있다.

---

## 핵심 최적화 기법 총괄 비교

각 최적화 기법이 어떤 병목을 해결하고, 어떤 효과를 가져오는지 먼저 전체적으로 비교한다.

| 기법 | 해결하는 병목 | Prefill 영향 | Decode 영향 | 처리량 향상 | 지연시간 감소 | 구현 복잡도 |
|------|-------------|:-----------:|:----------:|:----------:|:----------:|:----------:|
| KV-Cache | 중복 연산 | - | 필수 | - | 수십 배 | 낮음 |
| PagedAttention | 메모리 단편화 | 간접 | 간접 | 2~4x | - | 중간 |
| Continuous Batching | GPU 유휴 시간 | - | 간접 | 2~10x | - | 중간 |
| Chunked Prefill | Prefill 블로킹 | 직접 | 간접 | 소폭 | 감소 | 중간 |
| Speculative Decoding | 순차적 디코딩 | - | 직접 | - | 2~5x | 높음 |
| Flash Attention | 메모리 IO | 직접 | 직접 | 소폭 | 감소 | 낮음 (라이브러리) |
| [[quantization-guide\|양자화]] | 모델 크기 | 직접 | 직접 | 향상 | 감소 | 중간 |

---

## KV-Cache

:::tip
**핵심 원리**: 이전 토큰의 Key-Value 벡터를 재계산하지 않고 캐시에 저장하여 재사용한다.
:::

KV-Cache가 없으면, 100번째 토큰 생성 시 이전 99개 토큰에 대한 Key/Value를 모두 재계산해야 한다. KV-Cache는 이 중복 연산을 제거하여 **토큰 생성 속도를 수십 배** 향상시킨다.

### KV-Cache 메모리 계산

KV-Cache의 크기는 시퀀스 길이에 비례하여 증가한다:

$$\text{KV-Cache 크기} = 2 \times n_{\text{layers}} \times n_{\text{kv\_heads}} \times d_{\text{head}} \times \text{seq\_len} \times \text{bytes}$$

| 모델 | 레이어 수 | KV 헤드 수 | 헤드 차원 | 8K 시 KV-Cache | 32K 시 KV-Cache | 128K 시 KV-Cache |
|------|:--------:|:---------:|:--------:|:-------------:|:--------------:|:---------------:|
| LLaMA 3 8B | 32 | 8 (GQA) | 128 | ~1 GB | ~4 GB | ~16 GB |
| LLaMA 3 70B | 80 | 8 (GQA) | 128 | ~2.5 GB | ~10 GB | ~40 GB |
| Mistral 7B | 32 | 8 (GQA) | 128 | ~1 GB | ~4 GB | ~16 GB |
| GPT-4 (추정) | 120 | MHA | 128 | ~60 GB | ~240 GB | OOM |

추론 모델(DeepSeek-R1 등)은 수천 토큰의 CoT를 생성하므로, KV-Cache 관리가 특히 중요하다.

### KV-Cache 최적화 전략

| 전략 | 원리 | 메모리 절감 | 품질 영향 | 대표 모델 |
|------|------|:---------:|:--------:|----------|
| GQA | KV 헤드 수 감소 | 4~8x | 없음 (학습 시 적용) | LLaMA 2+, Gemma |
| MQA | KV 헤드 1개 | 최대 | 약간 저하 가능 | Falcon, GPT-J |
| KV 양자화 | FP8/INT8로 양자화 | 2x | 미미 | TensorRT-LLM |
| Sliding Window | 최근 N 토큰만 캐시 | 고정 크기 | 긴 의존성 손실 | Mistral |
| Token Eviction | 중요도 낮은 토큰 제거 | 가변 | 약간 저하 | H2O, StreamingLLM |

---

## PagedAttention

:::tip
**핵심 원리**: 운영체제의 가상 메모리 페이징에서 영감을 받아, KV-Cache를 고정 크기 블록으로 관리한다.
:::

기존 방식에서는 각 요청에 대해 최대 시퀀스 길이만큼의 연속 메모리를 미리 할당했다. 짧은 응답에서도 전체 버퍼가 예약되어 **60~80%의 메모리가 낭비**되었다.

PagedAttention은 KV-Cache를 **고정 크기 블록(보통 16 토큰 단위)**으로 분할하고, 필요할 때만 블록을 할당한다:
- 메모리 단편화 제거로 같은 메모리에서 **2~4x 더 많은 요청** 동시 처리
- 블록이 연속할 필요 없음. 가상 메모리처럼 물리적 분산 저장 가능
- 블록 공유를 통해 동일 프롬프트의 KV-Cache를 여러 요청이 공유 (Parallel Sampling)

---

## Continuous Batching

:::warning
Static Batching에서는 배치 내 가장 긴 요청이 완료될 때까지 모든 GPU 자원이 묶인다. 응답 길이가 10 토큰인 요청과 500 토큰인 요청이 같은 배치에 있으면, 짧은 요청은 490 토큰 동안 GPU를 낭비한다.
:::

Continuous Batching은 **iteration-level scheduling**을 도입한다:
- 매 디코딩 스텝마다 완료된 요청을 제거
- 빈 슬롯에 대기 중인 새 요청을 즉시 삽입
- 요청 길이 편차가 클수록 효과가 크며, 처리량 **2~10x 향상**

### Static vs Continuous Batching 비교

| 항목 | Static Batching | Continuous Batching |
|------|:--------------:|:------------------:|
| 스케줄링 단위 | 배치 전체 | 개별 iteration |
| GPU 유휴 시간 | 길이 편차만큼 낭비 | 최소화 |
| 새 요청 삽입 | 배치 완료 후 | 매 스텝마다 |
| 메모리 관리 | 고정 할당 | 동적 할당 |
| 처리량 | 기준선 | 2~10x 향상 |
| 구현 프레임워크 | 기본 HF generate | vLLM, TGI, SGLang |

---

## Chunked Prefill

긴 프롬프트의 Prefill 연산을 작은 청크로 분할하여, Decode 요청과 인터리빙하는 기법이다.

**문제**: 10,000 토큰의 긴 프롬프트가 Prefill 중이면, 진행 중인 Decode 요청들이 모두 대기해야 한다 (head-of-line blocking).

**해결**: Prefill을 512~1024 토큰 단위로 분할하고, 각 청크 사이에 Decode 스텝을 삽입한다. 이를 통해 Prefill의 높은 GPU 활용률과 Decode의 낮은 지연시간을 동시에 달성한다.

---

## Speculative Decoding

자기회귀 디코딩의 근본적 문제는 **순차적**이라는 것이다. 매 토큰마다 전체 모델을 통과해야 하므로, GPU의 병렬 처리 능력을 활용하지 못한다.

### 작동 방식

1. **Draft**: 작은 모델(예: 1B)이 K개 토큰을 빠르게 생성 (draft tokens)
2. **Verify**: 큰 모델(예: 70B)이 K개 토큰을 **한 번의 forward pass**로 동시 검증
3. **Accept/Reject**: 확률 분포 비교를 통해 수용/거절 결정

검증 단계에서 큰 모델은 K개 토큰을 병렬로 처리하므로, 1개 토큰 처리 비용으로 K개 토큰을 검증할 수 있다.

### Speculative Decoding 성능 특성

| 항목 | 설명 |
|------|------|
| 속도 향상 | 일반적으로 2~3x, draft 모델이 좋으면 3~5x |
| 품질 보장 | target 모델의 출력 분포를 **정확히 보존** |
| 수용률 의존 | draft 모델의 정확도가 높을수록 효과 증가 |
| 추가 메모리 | draft 모델 파라미터만큼 추가 필요 |
| 적용 조건 | draft 모델이 target과 유사한 분포를 가져야 효과적 |

---

## Flash Attention

표준 Attention 구현은 중간 결과(Attention matrix)를 GPU의 HBM(느린 메모리)에 쓰고 다시 읽는다. Flash Attention은 이를 **타일링(tiling)**으로 해결한다:

- Q, K, V를 작은 블록으로 분할
- 각 블록을 SRAM(빠른 메모리)에서 처리
- 중간 결과를 HBM에 쓰지 않고 on-the-fly로 통합
- HBM 접근 횟수를 $O(N^2)$에서 $O(N)$으로 감소

### Flash Attention 버전 비교

| 항목 | Flash Attention 1 | Flash Attention 2 | Flash Attention 3 |
|------|:-----------------:|:-----------------:|:-----------------:|
| 출시 | 2022 | 2023 | 2024 |
| 속도 향상 (vs 표준) | 2~4x | 추가 2x | 추가 1.5~2x |
| GQA/MQA 지원 | 제한적 | 완전 지원 | 완전 지원 |
| FP8 지원 | 없음 | 없음 | 지원 (Hopper) |
| 비동기 실행 | 없음 | 없음 | warp 특화 파이프라이닝 |
| 지원 GPU | Ampere+ | Ampere+ | Hopper (H100+) |

Flash Attention은 **모델 출력을 전혀 변경하지 않는** 순수한 구현 최적화이므로, 학습/추론 모두에서 무조건 사용하는 것이 이득이다. 현재 거의 모든 LLM 프레임워크의 기본 옵션이다.

---

## 양자화와 추론 최적화

[[quantization-guide]]에서 자세히 다루지만, 추론 관점에서의 양자화 효과를 정리한다.

| 정밀도 | 모델 크기 (70B) | 메모리 대역폭 요구 | Decode 속도 배수 | 품질 영향 |
|--------|:--------------:|:-----------------:|:--------------:|:--------:|
| FP16 | 140 GB | 기준선 | 1x | 없음 |
| FP8 | 70 GB | 0.5x | ~2x | 미미 |
| INT8 | 70 GB | 0.5x | ~2x | 미미~소폭 |
| INT4 (GPTQ/AWQ) | 35 GB | 0.25x | ~3.5x | 소폭 |
| [[nvfp4-quantization-concepts\|NF4]] (QLoRA) | 35 GB | 0.25x | ~3.5x | 소폭 |
| INT4 (GGUF Q4_K_M) | ~37 GB | 0.26x | ~3.3x | 소폭 |

양자화는 memory-bound인 Decode 단계에서 직접적 효과를 발휘한다. 모델 가중치를 절반으로 줄이면 메모리에서 읽는 시간도 절반으로 줄어, Decode 속도가 거의 2배가 된다.

---

## 서빙 프레임워크 비교

### 기능 비교

| 기능 | vLLM | TGI | TensorRT-LLM | SGLang | Ollama |
|------|:----:|:---:|:------------:|:------:|:------:|
| PagedAttention | O (창시자) | O | O | O | X |
| Continuous Batching | O | O | O | O | 제한적 |
| Speculative Decoding | O | O | O | O | X |
| Flash Attention | O | O | O | O | X |
| FP8 양자화 | O | O | O (최고) | O | X |
| INT4 (GPTQ/AWQ) | O | O | O | O | GGUF만 |
| Tensor Parallel | O | O | O | O | X |
| Pipeline Parallel | O | 제한적 | O | O | 레이어 분할 |
| Chunked Prefill | O | O | O | O | X |
| OpenAI API 호환 | O | O | O | O | O |
| Structured Output | O | O | O | O (최고) | O |
| LoRA 동적 로딩 | O | O | O | O | X |

### 성능 벤치마크 (LLaMA 3 70B, A100 80GB x 4, TP=4)

| 프레임워크 | 처리량 (tok/s) | TTFT (ms) | ITL (ms) | 동시 요청 수 |
|-----------|:------------:|:---------:|:--------:|:----------:|
| vLLM | ~2,400 | ~120 | ~28 | 256 |
| TGI | ~2,100 | ~140 | ~32 | 128 |
| TensorRT-LLM | ~3,000 | ~80 | ~22 | 256 |
| SGLang | ~2,600 | ~100 | ~26 | 256 |
| Ollama | N/A | N/A | N/A | 제한적 |

> **TTFT**: Time to First Token (첫 토큰 생성까지 시간). **ITL**: Inter-Token Latency (토큰 간 지연시간). 벤치마크는 입력 512토큰, 출력 256토큰, FP16 기준이며 실제 환경에 따라 편차가 크다.

### 프레임워크 선택 기준

| 시나리오 | 추천 프레임워크 | 이유 |
|---------|:------------:|------|
| 최대 처리량 (프로덕션) | TensorRT-LLM | NVIDIA GPU 최적화, 커널 퓨전 |
| 유연성 + 빠른 프로토타이핑 | vLLM | 넓은 모델 지원, 활발한 커뮤니티 |
| HuggingFace 생태계 통합 | TGI | 모델 허브 직접 연동, Docker 배포 |
| 구조적 생성 (JSON 등) | SGLang | RadixAttention, 고급 스케줄링 |
| 로컬 실행 (개인용) | Ollama | 간편 설치, macOS Metal 지원 |
| 연구/실험 | SGLang | 고급 기능, 커스텀 스케줄러 |

---

## vLLM 서빙 설정 실전

### 기본 서버 실행

```bash
# 단일 GPU 서빙
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3-8B-Instruct \
    --dtype auto \
    --max-model-len 8192 \
    --gpu-memory-utilization 0.9 \
    --port 8000

# Multi-GPU Tensor Parallel (4 GPU)
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3-70B-Instruct \
    --tensor-parallel-size 4 \
    --dtype float16 \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9

# Speculative Decoding 활성화
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3-70B-Instruct \
    --speculative-model meta-llama/Llama-3-8B-Instruct \
    --num-speculative-tokens 5 \
    --tensor-parallel-size 4
```

### GPU 활용 모니터링

```bash
# 실시간 GPU 상태 모니터링 (1초 간격)
watch -n 1 nvidia-smi

# GPU 활용률, 메모리, 온도를 CSV로 로깅
nvidia-smi --query-gpu=timestamp,index,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu \
    --format=csv -l 1 > gpu_log.csv

# vLLM 메트릭 확인 (Prometheus 형식)
curl http://localhost:8000/metrics | grep -E "vllm:(num_requests|gpu_cache|avg_generation)"

# 특정 프로세스의 GPU 메모리 사용량
nvidia-smi pmon -s um -d 1
```

---

## 토큰당 비용 분석

### GPU별 추론 비용 비교 (70B FP16 모델 기준)

| GPU 구성 | 시간당 비용 (클라우드) | 처리량 (tok/s) | 100만 토큰당 비용 | 비용 효율 |
|---------|:-------------------:|:------------:|:---------------:|:--------:|
| A100 80GB x 4 | ~$16/hr | ~2,400 | ~$1.85 | 기준선 |
| H100 SXM x 4 | ~$32/hr | ~4,800 | ~$1.85 | A100과 유사 |
| H100 SXM x 2 | ~$16/hr | ~2,200 | ~$2.02 | 소폭 불리 |
| L40S x 4 | ~$8/hr | ~1,200 | ~$1.85 | A100과 유사 |

### 양자화에 따른 비용 절감

| 정밀도 | GPU 구성 (70B) | 시간당 비용 | 처리량 (tok/s) | 100만 토큰당 비용 | 절감률 |
|--------|:-------------:|:----------:|:------------:|:---------------:|:-----:|
| FP16 | A100 x 4 | ~$16/hr | ~2,400 | ~$1.85 | 기준선 |
| INT8 | A100 x 2 | ~$8/hr | ~2,000 | ~$1.11 | ~40% |
| INT4 (AWQ) | A100 x 1 | ~$4/hr | ~1,500 | ~$0.74 | ~60% |
| INT4 (GPTQ) | RTX 4090 x 2 | ~$1.5/hr | ~600 | ~$0.69 | ~63% |

양자화는 필요 GPU 수를 줄여 비용을 크게 절감한다. INT4의 경우 품질 저하가 있지만, 대부분의 일반 대화 작업에서는 체감 차이가 미미하다.

---

## MFU 관점에서 본 최적화 효과 종합

각 최적화가 GPU 활용률에 미치는 영향을 정리하면:

| 최적화 | 주요 개선 대상 | MFU 직접 영향 | 처리량 영향 | 비용 영향 |
|--------|-------------|:----------:|:---------:|:--------:|
| KV-Cache | 중복 연산 제거 | 연산량 감소 | 필수 | 필수 |
| PagedAttention | 메모리 효율 | 배치 증가로 MFU 향상 | 2~4x | 50~75% 절감 |
| Continuous Batching | GPU 유휴 시간 | 활용률 향상 | 2~10x | 비례 절감 |
| Chunked Prefill | Prefill 블로킹 | 균형 활용 | 소폭 | 소폭 |
| Flash Attention | 메모리 IO | IO 병목 제거 | 소폭 | 소폭 |
| Speculative Decoding | 순차 병목 | 검증 배치로 향상 | - | 레이턴시 개선 |
| [[quantization-guide\|양자화]] | 모델 크기 | 대역폭 감소 | 향상 | 40~60% 절감 |
| [[multi-gpu-parallel-pytorch\|Tensor Parallel]] | 대역폭 합산 | 선형 확장 | 선형 | GPU 비용 증가 |

추론에서 MFU가 낮은 근본 원인은 **Decode의 memory-bound 특성**이다. 위 최적화들은 각각 다른 각도에서 이 문제를 완화하며, **조합하여 적용할 때 최대 효과**를 발휘한다.

---

## 선택 가이드: 시나리오별 최적 구성

### 레이턴시 우선 (챗봇, 실시간 서비스)

| 항목 | 권장 |
|------|------|
| 프레임워크 | vLLM 또는 TensorRT-LLM |
| 핵심 기법 | Speculative Decoding + Flash Attention |
| 양자화 | FP8 (품질 유지 + 속도 향상) |
| GPU 구성 | TP 최대화 ([[nvlink-concepts\|NVLink]] 필수) |
| 목표 지표 | TTFT < 200ms, ITL < 30ms |

### 처리량 우선 (배치 처리, API 서비스)

| 항목 | 권장 |
|------|------|
| 프레임워크 | vLLM 또는 TensorRT-LLM |
| 핵심 기법 | Continuous Batching + PagedAttention |
| 양자화 | INT4 (최대 처리량) |
| GPU 구성 | 비용 대비 GPU 수 최적화 |
| 목표 지표 | tok/s 최대, 비용/토큰 최소 |

### 비용 우선 (스타트업, 개인 프로젝트)

| 항목 | 권장 |
|------|------|
| 프레임워크 | Ollama (로컬) 또는 vLLM (서버) |
| 핵심 기법 | INT4 양자화 + 적절한 모델 크기 선택 |
| 양자화 | GGUF Q4_K_M (Ollama) 또는 AWQ (vLLM) |
| GPU 구성 | RTX 4090 단일 또는 L40S |
| 목표 지표 | 비용/토큰 최소, 수용 가능한 품질 |

### [[long-context-techniques|긴 컨텍스트]] 처리 (RAG, 문서 분석)

| 항목 | 권장 |
|------|------|
| 프레임워크 | vLLM 또는 SGLang |
| 핵심 기법 | Chunked Prefill + KV-Cache 양자화 |
| 양자화 | FP8 모델 + INT8 KV-Cache |
| GPU 구성 | HBM 용량 최대화 (H200 권장) |
| 목표 지표 | 128K+ 컨텍스트 안정 처리 |

---

## 정리

LLM 추론 최적화는 Prefill의 compute-bound 특성과 Decode의 memory-bound 특성이라는 **근본적 이중성**에서 출발한다.

핵심 교훈:
1. **Decode가 진짜 병목**: 전체 추론 시간의 대부분을 차지하며, memory bandwidth에 의해 제한된다
2. **최적화는 조합이 핵심**: KV-Cache + PagedAttention + Continuous Batching + Flash Attention을 모두 적용해야 프로덕션 수준의 성능에 도달한다
3. **MFU가 낮은 이유를 이해하라**: Decode의 MFU는 1~5%에 불과하며, 이는 연산이 아니라 메모리 전송이 병목이기 때문이다
4. **양자화는 최고의 비용 절감**: INT4 양자화만으로 GPU 비용을 60% 이상 절감하면서 대부분의 작업에서 수용 가능한 품질을 유지한다
5. **프레임워크 선택이 절반**: 같은 하드웨어에서도 vLLM/TensorRT-LLM과 naive 서빙의 처리량 차이는 10배 이상이다
6. **추론 모델은 더 어렵다**: 긴 CoT 생성으로 KV-Cache가 폭증하고, 토큰당 비용이 일반 LLM의 5~10배에 달한다
