<!-- infographic-hero -->
![Multi-GPU Parallel Processing: DDP, FSDP, and Tensor Parallelism 핵심 요약](figures/infographic.svg)

*Figure: Multi-GPU Parallel Processing: DDP, FSDP, and Tensor Parallelism 한 장 요약 인포그래픽*

# Multi-GPU 병렬 처리 실전: DDP, FSDP, Tensor Parallelism

## 들어가며

:::info
이 글은 [[reasoning-vs-inference|Reasoning vs Inference]] 시리즈의 **HW Inference** 축에 해당하며, [[inference-optimization-mfu|추론 최적화 가이드]]의 확장편이다.
:::

단일 GPU로 처리할 수 없는 작업이 점점 많아지고 있다. LLaMA 3 70B(FP16)는 **140GB의 메모리**가 필요한데, 가장 큰 소비자 GPU(RTX 4090)도 24GB에 불과하다. 4비트 양자화를 적용해도 ~35GB로, 여전히 단일 GPU에 탑재할 수 없다.

이 글에서는 여러 GPU에 모델과 데이터를 분산하는 세 가지 핵심 병렬 처리 전략을 비교하고, 추론과 학습 각각에서의 실전 적용 방법을 정리한다.

---

## 병렬 처리 전략 개요

| 전략 | 무엇을 나누는가 | 주 용도 | GPU 간 통신 |
|------|--------------|--------|-----------|
| **Data Parallelism (DP/DDP)** | 데이터 (미니배치) | 학습 | gradient 동기화 |
| **FSDP** | 데이터 + 모델 파라미터 | 학습 | 파라미터 + gradient |
| **Tensor Parallelism (TP)** | 모델 레이어 내부 | 추론 | 중간 activation |
| **Pipeline Parallelism (PP)** | 모델 레이어 그룹 | 학습/추론 | 레이어 간 activation |

---

## Data Parallelism: DDP

### 원리

DDP(DistributedDataParallel)는 가장 기본적인 멀티 GPU 전략이다:

1. 모델 전체를 **각 GPU에 복제**
2. 데이터 배치를 GPU 수만큼 분할
3. 각 GPU가 독립적으로 forward/backward 수행
4. Gradient를 **AllReduce**로 동기화 (모든 GPU의 gradient 평균)
5. 동일한 gradient로 모든 GPU의 모델을 동시 업데이트

### 장점과 한계

**장점**:
- 구현이 간단 ( PyTorch에서 `DistributedDataParallel` 래핑만으로 적용
- 거의 선형적 학습 속도 향상 ) N개 GPU → ~N배 빠른 학습
- 통신 오버헤드가 작음 ( gradient만 동기화

**한계**:
- **모델 전체가 각 GPU에 맞아야 함** ) 70B 모델은 DDP 불가 (GPU 메모리 부족)
- GPU 수 증가에 따라 AllReduce 통신 비용 증가

### PyTorch 코드

```python
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

dist.init_process_group("nccl")
local_rank = int(os.environ["LOCAL_RANK"])
model = MyModel().to(local_rank)
model = DDP(model, device_ids=[local_rank])

# 이후 일반 학습 루프와 동일
for batch in dataloader:
    loss = model(batch)
    loss.backward()  # gradient가 자동으로 AllReduce됨
    optimizer.step()
```

실행: `torchrun --nproc_per_node=2 train.py`

---

## FSDP: 대규모 모델을 위한 데이터 병렬

### 원리

FSDP(Fully Sharded Data Parallel)는 DDP의 메모리 한계를 극복한다. 핵심 아이디어: **모델 파라미터 자체를 GPU들에 분산 저장**하고, 필요할 때만 수집(AllGather)하여 연산에 사용한다.

DDP vs FSDP 메모리 비교 (7B 모델, 2 GPU):

| 항목 | DDP (각 GPU) | FSDP (각 GPU) |
|------|-----------|------------|
| 파라미터 | 14 GB | **7 GB** |
| Gradient | 14 GB | **7 GB** |
| Optimizer state | 28 GB | **14 GB** |
| **합계** | **56 GB** | **28 GB** |

FSDP는 각 GPU가 모델의 **1/N 만큼만 저장**하므로, GPU 수에 비례하여 메모리 요구가 감소한다.

### 작동 방식

1. **분할 (Sharding)**: 모델 파라미터를 N개 GPU에 균등 분할 저장
2. **Forward 시**: 현재 레이어에 필요한 파라미터를 AllGather로 수집 → 연산 → 바로 메모리에서 해제
3. **Backward 시**: 동일하게 AllGather → gradient 계산 → ReduceScatter로 gradient 분할 저장
4. **업데이트**: 각 GPU가 자신이 담당하는 파라미터만 업데이트

### 통신 비용 트레이드오프

FSDP는 DDP 대비 **통신량이 많다** ( 매 레이어마다 AllGather/ReduceScatter가 필요하기 때문이다. 따라서 **GPU 간 대역폭이 핵심**이다:

- **NVLink**: 900 GB/s (5세대) → FSDP 효율 높음
- **PCIe 5.0**: 64 GB/s → FSDP 효율 저하, 학습 속도 병목

### PyTorch 코드

```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP

model = MyModel()
model = FSDP(
    model,
    sharding_strategy=ShardingStrategy.FULL_SHARD,
    mixed_precision=MixedPrecision(
        param_dtype=torch.bfloat16,
        reduce_dtype=torch.float32,
    ),
)
```

---

## Tensor Parallelism: 추론의 핵심

### 원리

Tensor Parallelism(TP)은 모델의 **각 레이어를 여러 GPU에 분할**한다. 하나의 행렬 곱셈을 여러 GPU가 나눠서 수행하고 결과를 합친다.

Transformer의 각 레이어에서:
- **Attention**: Q, K, V 행렬을 헤드 단위로 분할 → 각 GPU가 일부 헤드 담당
- **FFN**: 중간 차원을 분할 → 각 GPU가 일부 뉴런 담당
- **결과 합산**: AllReduce로 부분 결과를 합산

### 왜 추론에서 TP가 중요한가

추론(Decode)은 **memory-bound**이다. 모델 가중치를 메모리에서 읽는 속도가 병목이다. TP로 모델을 N개 GPU에 분산하면:

1. 각 GPU가 읽어야 할 가중치 크기가 **1/N**으로 감소
2. N개 GPU의 메모리 대역폭을 합산하여 사용
3. **결과**: Decode 레이턴시가 거의 **1/N**으로 감소

이는 처리량만 늘리는 DDP/FSDP와 근본적으로 다르다. TP는 **단일 요청의 응답 속도**를 직접적으로 향상시킨다.

### 통신 요구사항

TP는 **매 레이어마다** GPU 간 AllReduce가 발생한다. 32-layer 모델이면 forward pass에서 최소 32번의 AllReduce가 필요하다. 따라서 **GPU 간 대역폭이 절대적으로 중요**하다.

| 인터커넥트 | 대역폭 | TP 실효성 |
|-----------|--------|----------|
| PCIe 4.0 | 32 GB/s | 2 GPU까지 가능, 그 이상은 통신 병목 |
| PCIe 5.0 | 64 GB/s | 2 GPU 적합 |
| NVLink (4세대) | 600 GB/s | 4-8 GPU 효율적 |
| NVLink (5세대) | 900 GB/s | 8+ GPU 가능 |

:::warning
**RTX 3090/4090 사용자**: PCIe 연결에서 TP는 **2 GPU까지만 실용적**이다. 3 GPU 이상에서는 통신 오버헤드가 연산 이득을 상쇄한다.
:::

---

## Pipeline Parallelism

### 원리

Pipeline Parallelism(PP)은 모델의 **레이어 그룹을 각 GPU에 순차 배치**한다:

- GPU 0: 레이어 1-16
- GPU 1: 레이어 17-32

데이터가 GPU 0 → GPU 1으로 순차적으로 흐른다.

### 장점과 한계

**장점**:
- GPU 간 통신이 **레이어 경계에서만** 발생 ) TP 대비 통신량 훨씬 적음
- PCIe 연결에서도 효율적
- 매우 큰 모델 탑재 가능

**한계**:
- **파이프라인 버블**: GPU가 순차적으로 처리하므로 유휴 시간 발생
- 레이턴시 감소 효과 없음, 총 레이턴시는 동일 (TP와 대비)
- 학습에서는 micro-batching으로 버블을 완화하지만, 추론에서는 효과 제한적

### 추론에서의 PP

추론에서 PP는 TP를 보완하는 용도로 사용된다:
- **TP로 레이턴시 감소** + **PP로 메모리 용량 확보**
- 예: 8 GPU 구성 → TP=4, PP=2 (4 GPU가 한 그룹으로 TP, 2 그룹이 PP)

---

## 실전 적용

### vLLM에서의 Multi-GPU 추론

vLLM은 Tensor Parallelism을 기본 지원한다:

```bash
# 2 GPU Tensor Parallel
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3-70B-Instruct \
    --tensor-parallel-size 2 \
    --dtype float16

# 4 GPU (TP=2, PP=2)
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3-70B-Instruct \
    --tensor-parallel-size 2 \
    --pipeline-parallel-size 2
```

### Ollama에서의 Multi-GPU

Ollama는 GGUF 모델의 레이어를 GPU에 자동 분배한다:

```bash
# 자동으로 사용 가능한 GPU에 분산
CUDA_VISIBLE_DEVICES=0,1 ollama run llama3:70b

# GPU별 레이어 할당 확인
ollama ps
```

Ollama는 PP 방식으로 레이어를 분배하므로, NVLink 없이도 비교적 효율적이다.

### 2x RTX 3090 (24GB x 2) 실전 가이드

| 작업 | 전략 | 가능한 모델 크기 |
|------|------|---------------|
| 학습 | DDP | 7B까지 (각 GPU에 모델 전체 로드) |
| 학습 | FSDP | 13B까지 (파라미터 분할) |
| 추론 | TP=2 | 70B INT4 (~35GB, PCIe에서 TP 통신 감내) |
| 추론 | PP (Ollama) | 70B INT4 (레이어 분할, 통신 최소) |
| 파인튜닝 | QLoRA + DDP | 13B (4비트 베이스 + LoRA 어댑터) |

:::tip
**PCIe 연결 2 GPU 핵심 팁**: 추론은 **Ollama PP 방식**이 가장 안정적. vLLM TP는 작동하지만 PCIe 병목으로 2 GPU 대비 기대만큼의 속도 향상을 못 얻을 수 있다. [[nvlink-concepts|NVLink]] 없이 TP를 사용할 때의 한계를 이해하는 것이 중요하다.
:::

---

## 전략 비교 총정리

| 전략 | 메모리 절감 | 레이턴시 감소 | 처리량 증가 | 필요 대역폭 | 주 용도 |
|------|:---------:|:----------:|:---------:|:---------:|--------|
| DDP | ❌ | ❌ | ✅✅ | 낮음 | 학습 (스케일아웃) |
| FSDP | ✅✅ | ❌ | ✅ | 높음 | 대모델 학습 |
| TP | ✅ | ✅✅ | ✅ | 매우 높음 | 추론 (레이턴시) |
| PP | ✅ | ❌ | ✅ | 낮음 | 대모델 탑재 |

선택 기준:
- **"GPU 하나에 모델이 들어간다"** → DDP (학습) 또는 단일 GPU 추론
- **"모델이 GPU 하나에 안 들어간다"** → FSDP (학습) 또는 TP/PP (추론)
- **"추론 속도가 중요하다"** → TP (NVLink 필수 권장)
- **"NVLink 없이 큰 모델을 실행해야 한다"** → PP (Ollama)
