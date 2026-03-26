# NVLink 완전 이해: GPU 인터커넥트의 모든 것

## 들어가며

:::info
이 글은 [[reasoning-vs-inference|Reasoning vs Inference]] 시리즈의 **HW Inference** 축에 해당하며, [[multi-gpu-parallel-pytorch|Multi-GPU 병렬 처리]]의 심화편이다.
:::

Multi-GPU 병렬 처리의 성능을 결정하는 가장 중요한 요소는 **GPU 간 통신 대역폭**이다. 아무리 강력한 GPU를 여러 개 사용해도, GPU 사이의 데이터 전송이 느리면 병렬 처리의 이점이 상쇄된다.

NVLink는 NVIDIA가 이 문제를 해결하기 위해 개발한 GPU 전용 고속 인터커넥트이다. PCIe 대비 **최대 14배 빠른 대역폭**을 제공하며, 대규모 AI 학습·추론의 핵심 인프라 기술이다.

---

## PCIe vs NVLink: 근본적 차이

### PCIe (Peripheral Component Interconnect Express)

PCIe는 범용 I/O 인터페이스로, GPU뿐 아니라 SSD, 네트워크 카드 등 모든 주변 장치가 사용하는 표준 버스이다.

| 세대 | 단방향 대역폭 (x16) | 양방향 | 출시 |
|------|-------------------|--------|------|
| PCIe 3.0 | 16 GB/s | 32 GB/s | 2010 |
| PCIe 4.0 | 32 GB/s | 64 GB/s | 2017 |
| PCIe 5.0 | 64 GB/s | 128 GB/s | 2019 |
| PCIe 6.0 | 128 GB/s | 256 GB/s | 2022 |

소비자 GPU(RTX 3090, 4090)는 일반적으로 **PCIe 4.0 x16** (32 GB/s 단방향)으로 연결된다.

### NVLink

NVLink는 GPU 간 직접 통신을 위해 설계된 전용 인터커넥트이다.

| 세대 | 단방향 대역폭 | 양방향 | 적용 GPU | 배수 (vs PCIe 4.0) |
|------|------------|--------|---------|-----------------|
| NVLink 1.0 | 40 GB/s | 80 GB/s | P100 | 2.5x |
| NVLink 2.0 | 75 GB/s | 150 GB/s | V100 | 4.7x |
| NVLink 3.0 | 300 GB/s | 600 GB/s | A100 | 9.4x |
| NVLink 4.0 | 450 GB/s | 900 GB/s | H100/H200 | 14x |
| NVLink 5.0 | 900 GB/s | 1800 GB/s | B100/B200 | 28x |

NVLink 5.0(Blackwell)은 PCIe 4.0 대비 **28배** 빠르다. 이 차이가 [[multi-gpu-parallel-pytorch|Multi-GPU 병렬 처리]]에서 TP의 실효성을 결정한다.

### 핵심 차이

| 특성 | PCIe | NVLink |
|------|------|--------|
| 설계 목적 | 범용 I/O | GPU 간 전용 통신 |
| 토폴로지 | 트리 (CPU 경유) | P2P (GPU 직접 연결) |
| 지연시간 | 높음 | 매우 낮음 |
| 대역폭 | 최대 64 GB/s | 최대 1800 GB/s |
| 메모리 접근 | GPU→CPU→GPU | GPU→GPU 직접 |
| 가격 | 포함 (기본) | 추가 비용 |

PCIe는 데이터가 **CPU(호스트 메모리)를 경유**해야 하는 경우가 많지만, NVLink는 GPU 간 **직접(peer-to-peer)** 메모리 접근이 가능하다. 이로 인해 NVLink는 대역폭뿐 아니라 **지연시간에서도** 큰 우위를 가진다.

---

## NVSwitch: All-to-All 연결

### 문제: GPU 수가 증가하면?

NVLink는 기본적으로 **점대점(point-to-point)** 연결이다. 8개 GPU를 모두 직접 연결하려면 $\binom{8}{2} = 28$개의 NVLink 연결이 필요한데, 물리적으로 불가능하다.

### NVSwitch의 역할

NVSwitch는 이 문제를 해결하는 **GPU 전용 스위치 칩**이다. 여러 GPU의 NVLink 포트를 NVSwitch에 연결하면, **모든 GPU 쌍이 동시에 최대 대역폭으로 통신** 가능하다.

| 구성 | 기술 | 최대 GPU 수 | All-to-All 대역폭 |
|------|------|-----------|-----------------|
| DGX A100 | NVLink 3.0 + NVSwitch 2.0 | 8 | 600 GB/s |
| DGX H100 | NVLink 4.0 + NVSwitch 3.0 | 8 | 900 GB/s |
| GB200 NVL72 | NVLink 5.0 + NVSwitch 4.0 | 72 | 1800 GB/s |

DGX H100은 8개 H100 GPU를 NVSwitch 3.0으로 연결하여, 모든 GPU 쌍이 900 GB/s로 통신할 수 있다. 이는 하나의 거대한 통합 메모리 공간처럼 작동한다.

### GB200 NVL72: 극한의 스케일

Blackwell 아키텍처의 GB200 NVL72는 **72개 GPU를 NVLink 5.0으로 연결**하는 초대규모 시스템이다. 72개 GPU의 메모리(각 192GB)가 하나의 통합 주소 공간으로 동작하여, **총 13.8TB의 GPU 메모리**를 제공한다. 이는 수조 파라미터 모델의 추론을 단일 노드에서 처리할 수 있는 규모다.

---

## NVLink가 성능에 미치는 영향

### Tensor Parallelism에서의 차이

[[multi-gpu-parallel-pytorch|Tensor Parallelism]]은 매 레이어마다 GPU 간 AllReduce를 수행한다. 32-layer 모델에서 forward pass만으로 최소 32번의 AllReduce가 필요하다.

7B 모델을 2 GPU로 TP하는 경우, 각 AllReduce에서 전송되는 데이터 크기는 hidden_size × batch_size × 2(바이트)다. hidden_size=4096, batch_size=32, FP16 기준:

$$\text{데이터/AllReduce} = 4096 \times 32 \times 2 = 256\text{KB}$$
$$\text{총 통신량(32 layers)} = 256\text{KB} \times 32 \times 2 \approx 16\text{MB}$$

| 인터커넥트 | 대역폭 | 16MB 전송 시간 | 연산 대비 비율 |
|-----------|--------|-------------|-------------|
| PCIe 4.0 | 32 GB/s | 0.5 ms | ~15% 오버헤드 |
| NVLink 4.0 | 450 GB/s | 0.035 ms | ~1% 오버헤드 |

PCIe에서는 통신이 전체 연산 시간의 15%를 차지하지만, NVLink에서는 1%에 불과하다. **배치 크기가 작거나 모델이 클수록 이 차이는 더 극대화**된다.

### FSDP에서의 차이

FSDP는 매 레이어마다 AllGather(파라미터 수집) + ReduceScatter(gradient 분산)를 수행한다. 통신량이 TP보다 훨씬 크기 때문에, NVLink의 유무가 학습 효율에 결정적 영향을 미친다.

7B 모델 FSDP (2 GPU):
- 매 레이어 AllGather: ~파라미터 크기의 1/N 전송
- PCIe 4.0: 학습 효율 **60-70%** (나머지는 통신 대기)
- NVLink 4.0: 학습 효율 **90-95%**

### 추론에서의 영향

추론은 학습보다 배치 크기가 작고 토큰 단위로 순차 처리하므로, 개별 AllReduce의 데이터가 작다. 이 경우 **대역폭보다 지연시간이 중요**해지며, NVLink의 낮은 지연시간이 더 큰 이점을 제공한다.

---

## NVLink 없이 Multi-GPU 활용하기

소비자 GPU(RTX 3090/4090)는 NVLink를 지원하지 않는다 (RTX 3090은 NVLink 브리지를 지원했지만, RTX 4090은 제거). PCIe 연결에서 효율적으로 Multi-GPU를 활용하는 전략:

### 1. Pipeline Parallelism 우선 사용

PP는 레이어 경계에서만 통신이 발생하므로, PCIe 대역폭에서도 효율적이다. Ollama는 기본적으로 PP 방식으로 GPU에 레이어를 분배한다.

### 2. TP는 2 GPU까지만

PCIe 4.0에서 TP는 2 GPU까지 실용적이다. 3 GPU 이상에서는 통신 오버헤드가 급증하여 단일 GPU 대비 오히려 느려질 수 있다.

### 3. 양자화로 단일 GPU 범위 확대

[[nvfp4-quantization-concepts|4비트 양자화]]로 모델 크기를 줄이면, 더 큰 모델을 적은 GPU에 탑재할 수 있다:
- 70B INT4 → ~35GB → 2x RTX 3090(24GB)에 PP로 분배
- 13B FP16 → ~26GB → 단일 RTX 3090에 약간 부족, INT8로 ~13GB로 단일 GPU 탑재

### 4. 비동기 통신 활용

FSDP의 `cpu_offload` 옵션으로 파라미터를 CPU RAM에 저장하고 필요할 때만 GPU로 전송할 수 있다. 속도는 느려지지만, 메모리 제약을 극복할 수 있다.

---

## 세대별 NVLink 정리

| 세대 | 출시 | 대역폭 (양방향) | GPU | 특징 |
|------|------|--------------|-----|------|
| 1.0 | 2016 | 80 GB/s | P100 | 최초 도입 |
| 2.0 | 2017 | 150 GB/s | V100 | NVSwitch 1.0 도입 (DGX-2) |
| 3.0 | 2020 | 600 GB/s | A100 | NVSwitch 2.0, 8 GPU all-to-all |
| 4.0 | 2022 | 900 GB/s | H100/H200 | NVSwitch 3.0, SHARP 지원 |
| 5.0 | 2024 | 1800 GB/s | B100/B200 | NVSwitch 4.0, 72 GPU 연결 (GB200 NVL72) |

8년간 대역폭이 80 → 1800 GB/s로 **22.5배** 성장했다. 같은 기간 PCIe는 32 → 128 GB/s로 4배 성장에 그쳤다. 이 격차가 점점 벌어지고 있다는 것은, 대규모 AI 워크로드에서 **NVLink의 중요성이 계속 증가**한다는 의미다.

---

## 정리

| 질문 | 답변 |
|------|------|
| NVLink가 필요한가? | TP를 3+ GPU에서 사용하거나, FSDP로 대규모 학습을 한다면 **필수** |
| PCIe에서 Multi-GPU가 가능한가? | 가능하지만, PP 중심으로 사용하고 TP는 2 GPU까지만 권장 |
| 소비자 GPU에서 대안은? | 양자화로 모델 크기 축소 + PP 방식 분배가 가장 실용적 |
| 클라우드에서는? | A100/H100 인스턴스는 NVLink 기본 제공. Multi-GPU 추론 시 TP 적극 활용 |

NVLink는 "있으면 좋은" 기술이 아니라, Multi-GPU AI 워크로드의 **효율을 결정하는 핵심 인프라**다. [[multi-gpu-parallel-pytorch|병렬 처리 전략]]을 선택할 때, GPU 자체의 성능만큼이나 **GPU 간 연결**을 고려해야 한다.
