<!-- infographic-hero -->
![NVLink Deep Dive: GPU Interconnect for AI Workloads 핵심 요약](figures/infographic.svg)

*Figure: NVLink Deep Dive: GPU Interconnect for AI Workloads 한 장 요약 인포그래픽*

# NVLink 완전 이해: GPU 인터커넥트의 모든 것

## 들어가며

:::info
이 글은 [[multi-gpu-parallel-pytorch|Multi-GPU 병렬 처리]]의 심화편이다. 병렬 처리 전략의 성능을 결정하는 **GPU 간 인터커넥트**를 집중적으로 다룬다.
:::

단일 GPU의 연산 성능이 아무리 높아도, 여러 GPU를 함께 사용할 때 병목은 **GPU 간 데이터 전송 속도**에서 발생한다. Tensor Parallelism은 매 레이어마다 AllReduce를 수행하고, FSDP는 매 스텝마다 AllGather와 ReduceScatter를 반복한다. 이 통신이 느리면 GPU는 연산 대신 데이터를 기다리며 유휴 상태에 빠진다.

NVLink는 NVIDIA가 이 문제를 해결하기 위해 개발한 GPU 전용 고속 인터커넥트이다. 2016년 Pascal(P100) 세대에 처음 도입되어, Blackwell(B200) 세대에서는 PCIe 4.0 대비 **최대 28배 빠른 양방향 대역폭**을 달성했다. NVSwitch와 결합하면 최대 72개 GPU를 단일 노드에서 풀 메시(full-mesh)로 연결할 수 있어, 대규모 AI 학습과 추론의 핵심 인프라 기술로 자리잡았다.

이 글에서는 PCIe, NVLink, NVSwitch의 원리와 세대별 발전을 정량적으로 비교하고, 실제 GPU 토폴로지를 확인하는 방법부터 워크로드별 인터커넥트 선택 가이드까지 실전적인 내용을 다룬다.

---

## GPU 인터커넥트 기술 비교 개요

GPU 간 통신에 사용되는 세 가지 핵심 기술을 먼저 개관한다.

| 기술 | 설계 목적 | 토폴로지 | 최대 대역폭 (양방향) | GPU 간 직접 통신 | 비용 |
|------|----------|---------|------------------|----------------|------|
| **PCIe** | 범용 I/O 버스 | 트리 (CPU 경유) | 256 GB/s (6.0) | 제한적 (P2P) | 기본 포함 |
| **NVLink** | GPU 간 전용 P2P | 포인트-투-포인트 | 1800 GB/s (5.0) | 완전 지원 | 추가 비용 |
| **NVSwitch** | GPU 간 All-to-All | 풀 메시 (스위치) | 1800 GB/s (4.0) | 완전 지원 | 서버 내장 |

| 특성 | PCIe | NVLink | NVSwitch |
|------|------|--------|----------|
| 데이터 경로 | GPU -> CPU -> GPU | GPU -> GPU 직접 | GPU -> Switch -> GPU |
| 지연시간 | 높음 (~1-10 us) | 낮음 (~0.1-1 us) | 매우 낮음 |
| 확장성 | 무제한 (슬롯) | 제한적 (링크 수) | 최대 72 GPU |
| 메모리 접근 | 호스트 메모리 경유 | 피어 메모리 직접 | 통합 메모리 공간 |
| 주요 사용처 | 소비자 GPU, 범용 서버 | 데이터센터 GPU | DGX/HGX 시스템 |
| RDMA 지원 | GPUDirect RDMA | NVLink 네이티브 | NVLink 네이티브 |

---

## PCIe: 범용 I/O 인터페이스

### PCIe의 구조

PCIe(Peripheral Component Interconnect Express)는 CPU와 주변 장치를 연결하는 범용 직렬 인터페이스이다. GPU뿐 아니라 NVMe SSD, 네트워크 카드, FPGA 등 모든 확장 장치가 PCIe 버스를 통해 CPU와 통신한다.

PCIe는 레인(lane) 단위로 대역폭이 결정된다. 각 레인은 독립적인 양방향 직렬 링크이며, GPU는 일반적으로 **x16 구성**(16레인)을 사용한다.

### PCIe 세대별 대역폭

| 세대 | 레인당 전송률 | x16 단방향 | x16 양방향 | 인코딩 | 출시 |
|------|------------|-----------|-----------|--------|------|
| PCIe 3.0 | 8 GT/s | 16 GB/s | 32 GB/s | 128b/130b | 2010 |
| PCIe 4.0 | 16 GT/s | 32 GB/s | 64 GB/s | 128b/130b | 2017 |
| PCIe 5.0 | 32 GT/s | 64 GB/s | 128 GB/s | 128b/130b | 2019 |
| PCIe 6.0 | 64 GT/s | 128 GB/s | 256 GB/s | FLIT+CRC | 2022 |

현재 데이터센터 GPU의 주류는 **PCIe 5.0**이고, 소비자 GPU(RTX 4090)는 **PCIe 4.0 x16**을 사용한다. PCIe 6.0 기반 GPU는 2026년 현재 아직 출시 전이다.

### PCIe의 한계: GPU 간 통신

PCIe는 기본적으로 CPU를 중심으로 한 **트리 토폴로지**이다. GPU 간 통신 시 데이터가 다음 경로를 따른다:

1. GPU A의 메모리 -> PCIe 링크 -> CPU/호스트 메모리
2. CPU/호스트 메모리 -> PCIe 링크 -> GPU B의 메모리

이 과정에서 PCIe 대역폭을 **2번 소모**하고, CPU 메모리 복사 오버헤드까지 추가된다. GPUDirect P2P를 지원하는 경우 CPU 메모리를 경유하지 않고 PCIe 스위치를 통해 직접 전송할 수 있지만, 여전히 PCIe 대역폭의 제한을 받는다.

---

## NVLink: GPU 전용 고속 인터커넥트

### NVLink의 원리

NVLink는 GPU 간 **직접 포인트-투-포인트 연결**을 제공하는 전용 인터커넥트이다. PCIe 버스를 거치지 않고, GPU의 NVLink 포트에서 상대 GPU의 NVLink 포트로 데이터가 직접 전송된다.

핵심 특징:

- **전용 물리 링크**: PCIe와 독립적인 별도의 물리적 연결 (NVLink 브리지 또는 NVSwitch를 통해 연결)
- **Peer-to-Peer 메모리 접근**: 한 GPU가 다른 GPU의 메모리를 로컬 메모리처럼 직접 읽고 쓸 수 있음
- **낮은 지연시간**: CPU를 경유하지 않으므로 PCIe 대비 수배 낮은 레이턴시
- **높은 대역폭**: 세대마다 크게 증가하여 PCIe 대비 최대 28배

### NVLink 세대별 스펙

| 세대 | 출시 | 링크 수 | 링크당 대역폭 | 총 양방향 대역폭 | 적용 GPU | vs PCIe 4.0 |
|------|------|---------|-------------|----------------|---------|-------------|
| NVLink 1.0 | 2016 | 4 | 20 GB/s | 80 GB/s | P100 | 1.25x |
| NVLink 2.0 | 2017 | 6 | 25 GB/s | 150 GB/s | V100 | 2.3x |
| NVLink 3.0 | 2020 | 12 | 50 GB/s | 600 GB/s | A100 | 9.4x |
| NVLink 4.0 | 2022 | 18 | 50 GB/s | 900 GB/s | H100/H200 | 14x |
| NVLink 5.0 | 2024 | 18 | 100 GB/s | 1800 GB/s | B100/B200/GB200 | 28x |

8년간 NVLink 대역폭은 80 GB/s에서 1800 GB/s로 **22.5배** 성장했다. 같은 기간 PCIe는 32 GB/s에서 128 GB/s로 **4배** 성장에 그쳤다. 이 격차는 계속 벌어지고 있으며, 대규모 AI 워크로드에서 NVLink의 중요성이 점점 커지고 있다.

### NVLink vs PCIe 핵심 비교

| 비교 항목 | PCIe 4.0 x16 | PCIe 5.0 x16 | NVLink 3.0 (A100) | NVLink 4.0 (H100) | NVLink 5.0 (B200) |
|----------|-------------|-------------|------------------|------------------|------------------|
| 양방향 대역폭 | 64 GB/s | 128 GB/s | 600 GB/s | 900 GB/s | 1800 GB/s |
| GPU 간 지연시간 | ~5 us | ~3 us | ~1 us | ~0.7 us | ~0.5 us |
| P2P 메모리 접근 | 제한적 | 제한적 | 완전 지원 | 완전 지원 | 완전 지원 |
| Atomic 연산 | 미지원 | 미지원 | 지원 | 지원 | 지원 |
| 통합 메모리 주소 | 불가 | 불가 | NVSwitch 필요 | NVSwitch 필요 | NVSwitch 지원 |
| CPU 경유 필요 | 예 | 예 | 아니오 | 아니오 | 아니오 |

---

## NVSwitch: All-to-All GPU 연결

### 스케일링 문제

NVLink는 기본적으로 **포인트-투-포인트(P2P)** 연결이다. GPU A와 GPU B를 직접 연결하는 것은 간단하지만, 8개 GPU를 모두 서로 직접 연결하려면 $\binom{8}{2} = 28$개의 독립적인 NVLink 연결이 필요하다. 각 GPU의 NVLink 포트 수가 제한되어 있으므로, 물리적으로 모든 GPU 쌍을 풀 메시로 직접 연결하는 것은 불가능하다.

### NVSwitch의 역할

NVSwitch는 이 문제를 해결하는 **GPU 전용 네트워크 스위치 칩**이다. 여러 GPU의 NVLink 포트를 NVSwitch에 연결하면, 스위치가 내부에서 크로스바(crossbar) 라우팅을 수행하여 **모든 GPU 쌍이 동시에 최대 대역폭으로 통신**할 수 있다.

NVSwitch가 없는 구성에서는 GPU 0이 GPU 7에 데이터를 보내려면 중간 GPU를 경유(hop)해야 할 수 있다. NVSwitch가 있으면 모든 통신이 단일 홉으로 완료된다.

### NVSwitch 세대별 스펙

| 세대 | 출시 | 포트 수 | 포트당 대역폭 | 총 스위칭 용량 | 적용 시스템 |
|------|------|---------|-------------|-------------|-----------|
| NVSwitch 1.0 | 2018 | 18 NVLink | 25 GB/s | 450 GB/s | DGX-2 (V100) |
| NVSwitch 2.0 | 2020 | 36 NVLink | 50 GB/s | 1800 GB/s | DGX A100 |
| NVSwitch 3.0 | 2022 | 64 NVLink | 50 GB/s | 3200 GB/s | DGX H100 |
| NVSwitch 4.0 | 2024 | 128 NVLink | 100 GB/s | 12800 GB/s | GB200 NVL72 |

### 주요 시스템 구성 비교

| 시스템 | GPU | GPU 수 | NVLink 세대 | NVSwitch 세대 | GPU당 대역폭 | 총 GPU 메모리 |
|--------|-----|--------|-----------|-------------|-------------|-------------|
| DGX-2 | V100 32GB | 16 | 2.0 | 1.0 | 150 GB/s | 512 GB |
| DGX A100 | A100 80GB | 8 | 3.0 | 2.0 | 600 GB/s | 640 GB |
| DGX H100 | H100 80GB | 8 | 4.0 | 3.0 | 900 GB/s | 640 GB |
| DGX H200 | H200 141GB | 8 | 4.0 | 3.0 | 900 GB/s | 1128 GB |
| GB200 NVL72 | B200 192GB | 72 | 5.0 | 4.0 | 1800 GB/s | 13824 GB |

### GB200 NVL72: 차세대 GPU 인터커넥트

Blackwell 아키텍처의 GB200 NVL72는 **72개 B200 GPU를 NVLink 5.0 + NVSwitch 4.0으로 완전 연결**하는 초대규모 시스템이다.

핵심 특징:

- **총 GPU 메모리**: 72 x 192GB = **13,824 GB (약 13.5 TB)**
- **통합 메모리 주소 공간**: 72개 GPU 메모리가 하나의 주소 공간으로 동작
- **GPU당 NVLink 대역폭**: 양방향 1800 GB/s
- **FP4 성능**: 총 1.44 ExaFLOPS

이 규모의 통합 메모리는 수조 파라미터 모델(예: GPT-4 클래스)의 추론을 **단일 노드에서 TP만으로** 처리할 수 있게 한다. NVSwitch 4.0의 인밴드 연산(in-network compute) 기능은 AllReduce 같은 집합 통신을 스위치 내부에서 수행하여 GPU의 연산 부담을 줄인다.

---

## GPU 토폴로지 확인 방법

### nvidia-smi topo 명령

실제 GPU 간 연결 토폴로지를 확인하는 가장 기본적인 명령이다:

```bash
# GPU 토폴로지 매트릭스 확인
nvidia-smi topo -m
```

```output
        GPU0    GPU1    GPU2    GPU3    CPU Affinity    NUMA Affinity
GPU0     X      NV12    NV12    NV12    0-63            0
GPU1    NV12     X      NV12    NV12    0-63            0
GPU2    NV12    NV12     X      NV12    64-127          1
GPU3    NV12    NV12    NV12     X      64-127          1
```

출력의 각 기호가 의미하는 바:

| 기호 | 의미 | 대역폭 수준 |
|------|------|-----------|
| X | 자기 자신 | N/A |
| NV# | NVLink 연결 (# = 링크 수) | 매우 높음 |
| SYS | PCIe + NUMA 경유 | 낮음 |
| NODE | 같은 NUMA, PCIe 스위치 경유 | 중간 |
| PIX | 같은 PCIe 스위치 직접 | 중간-높음 |
| PHB | 같은 PCIe 호스트 브리지 | 중간 |

### NVLink 상태 확인

```bash
# NVLink 연결 상태 및 대역폭 확인
nvidia-smi nvlink --status

# GPU별 NVLink 카운터 (트래픽 모니터링)
nvidia-smi nvlink --capabilities -i 0
```

### P2P 접근 가능 여부 확인

GPU 간 피어-투-피어 메모리 접근이 가능한지 확인한다. NVLink가 연결된 GPU 쌍은 P2P 접근이 활성화된다:

```bash
# CUDA 샘플의 P2P 대역폭 테스트
# (CUDA 툴킷 설치 시 포함)
/usr/local/cuda/extras/demo_suite/p2pBandwidthLatencyTest
```

```output
P2P Connectivity Matrix
     D\D     0     1     2     3
     0       1     1     1     1
     1       1     1     1     1
     2       1     1     1     1
     3       1     1     1     1

Unidirectional P2P=Enabled Bandwidth (GB/s)
   D\D     0      1      2      3
     0 1581.6  241.3  241.5  241.2
     1  241.3 1582.3  241.4  241.5
     2  241.3  241.4 1583.1  241.3
     3  241.4  241.5  241.3 1582.8
```

위 출력에서 대각선은 로컬 메모리 대역폭(~1.5 TB/s, HBM3), 비대각선은 NVLink 대역폭(~241 GB/s 단방향, NVLink 3.0 수준)을 나타낸다.

---

## NVLink가 성능에 미치는 영향

### Tensor Parallelism에서의 영향

[[multi-gpu-parallel-pytorch|Tensor Parallelism(TP)]]은 매 레이어마다 GPU 간 AllReduce를 수행한다. 32-layer 모델의 forward pass에서 최소 **32번의 AllReduce**가 필요하므로, GPU 간 대역폭이 직접적으로 추론 지연시간에 영향을 준다.

**7B 모델, 2 GPU TP, FP16 기준 통신량 계산:**

$$\text{AllReduce당 데이터} = \text{hidden\_size} \times \text{batch\_size} \times 2\text{ bytes} = 4096 \times 32 \times 2 = 256\text{ KB}$$
$$\text{총 통신량 (32 layers, forward+backward)} = 256\text{ KB} \times 32 \times 2 = 16\text{ MB}$$

| 인터커넥트 | 양방향 대역폭 | 16 MB 전송 시간 | 연산 대비 오버헤드 | TP 실효성 |
|-----------|-------------|---------------|-----------------|----------|
| PCIe 4.0 x16 | 64 GB/s | ~0.5 ms | ~15% | 2 GPU 한계 |
| PCIe 5.0 x16 | 128 GB/s | ~0.25 ms | ~8% | 2 GPU 적합 |
| NVLink 3.0 (A100) | 600 GB/s | ~0.05 ms | ~1.5% | 4-8 GPU |
| NVLink 4.0 (H100) | 900 GB/s | ~0.035 ms | ~1% | 8 GPU |
| NVLink 5.0 (B200) | 1800 GB/s | ~0.018 ms | ~0.5% | 8+ GPU |

PCIe에서는 통신 오버헤드가 15%에 달하지만, NVLink 4.0에서는 1% 미만이다. **배치 크기가 작을수록, 모델이 클수록 이 차이는 더 극대화**된다.

### FSDP에서의 영향

FSDP(Fully Sharded Data Parallel)는 매 레이어마다 AllGather(파라미터 수집) + ReduceScatter(gradient 분산)를 수행한다. 통신량이 TP보다 훨씬 크기 때문에, NVLink의 유무가 학습 효율에 결정적 영향을 준다.

| 인터커넥트 | FSDP 학습 효율 (7B, 2 GPU) | FSDP 학습 효율 (70B, 8 GPU) | 주요 병목 |
|-----------|--------------------------|---------------------------|----------|
| PCIe 4.0 | 60-70% | 사실상 불가 | AllGather 대역폭 |
| PCIe 5.0 | 70-80% | 40-50% | AllGather 대역폭 |
| NVLink 3.0 | 90-95% | 80-85% | 연산이 주 병목 |
| NVLink 4.0 | 95%+ | 85-90% | 연산이 주 병목 |

:::warning
PCIe 연결에서 FSDP로 70B 이상 모델을 학습하는 것은 **실질적으로 비효율적**이다. GPU 대부분의 시간을 통신 대기에 소모하게 된다. NVLink가 없다면 LoRA/QLoRA 같은 파라미터 효율적 방법을 사용하는 것이 현실적이다.
:::

### 추론에서의 영향

추론(특히 Decode 단계)은 배치 크기가 작고 토큰 단위로 순차 처리하므로, 개별 AllReduce의 데이터 크기가 매우 작다. 이 경우 **대역폭보다 지연시간(latency)이 더 중요**해지며, NVLink의 낮은 지연시간이 큰 이점이 된다.

| 시나리오 | PCIe 4.0 | NVLink 4.0 | 성능 차이 |
|---------|----------|-----------|----------|
| Decode (batch=1, 7B TP=2) | 토큰당 ~12 ms | 토큰당 ~8 ms | 1.5x |
| Decode (batch=1, 70B TP=8) | 사실상 불가 | 토큰당 ~25 ms | N/A |
| Prefill (batch=32, 7B TP=2) | ~45 ms | ~35 ms | 1.3x |
| Prefill (batch=32, 70B TP=8) | 사실상 불가 | ~120 ms | N/A |

---

## 멀티 노드 vs 싱글 노드 통신

### 통신 계층 구조

대규모 GPU 클러스터에서는 통신이 여러 계층으로 구분된다. 각 계층의 대역폭 차이가 병렬 처리 전략 선택에 결정적인 영향을 준다.

| 통신 계층 | 기술 | 대역폭 (H100 기준) | 지연시간 | 용도 |
|----------|------|------------------|---------|------|
| GPU 내부 (HBM) | HBM3 | 3350 GB/s | ~ns | 텐서 연산 |
| GPU 간 (노드 내) | NVLink 4.0 | 900 GB/s | ~0.7 us | TP, FSDP |
| 노드 간 (랙 내) | InfiniBand NDR | 400 Gb/s (~50 GB/s) | ~1-5 us | PP, DP |
| 랙 간 | Ethernet/IB | 100-400 Gb/s | ~10-50 us | DP |

### 계층별 병렬 전략 매핑

대역폭 차이가 크기 때문에, 통신량이 많은 병렬 전략일수록 빠른 인터커넥트에 매핑해야 한다:

| 병렬 전략 | 통신 빈도 | 통신량 | 최소 권장 인터커넥트 | 적정 매핑 계층 |
|----------|---------|--------|------------------|-------------|
| Tensor Parallelism | 매 레이어 | 중간 | NVLink | GPU 간 (노드 내) |
| FSDP | 매 레이어 | 큼 | NVLink 권장 | GPU 간 (노드 내) |
| Pipeline Parallelism | 레이어 경계 | 작음 | PCIe/IB 가능 | 노드 간 |
| Data Parallelism | 매 스텝 | 중간 | IB 가능 | 노드 간/랙 간 |

:::tip
대규모 학습에서 흔히 사용하는 **3D Parallelism**은 이 계층 구조를 활용한다. 예를 들어, DGX H100 8-node(64 GPU) 환경에서 TP=8(노드 내 NVLink), PP=4(노드 간 IB), DP=2(노드 간 IB)처럼 구성한다. 통신량이 가장 많은 TP를 NVLink에, 통신량이 적은 PP/DP를 InfiniBand에 매핑하는 것이 핵심이다.
:::

### 노드 간 통신 기술 비교

| 기술 | 대역폭 (단방향) | 지연시간 | GPU Direct | 주 사용처 |
|------|-------------|---------|-----------|----------|
| InfiniBand HDR | 200 Gb/s (25 GB/s) | ~1 us | RDMA 지원 | DGX A100 클러스터 |
| InfiniBand NDR | 400 Gb/s (50 GB/s) | ~1 us | RDMA 지원 | DGX H100 클러스터 |
| InfiniBand XDR | 800 Gb/s (100 GB/s) | ~0.5 us | RDMA 지원 | GB200 NVL72 클러스터 |
| Ethernet (RoCE) | 100-400 Gb/s | ~5-10 us | 제한적 | 클라우드 환경 |
| NVLink (노드 간) | 1800 GB/s | ~0.5 us | 네이티브 | GB200 NVL72 내부 |

---

## 클라우드 GPU 인스턴스별 인터커넥트

### AWS GPU 인스턴스

| 인스턴스 | GPU | GPU 수 | GPU 간 인터커넥트 | GPU당 대역폭 | 인스턴스 간 |
|---------|-----|--------|----------------|-------------|-----------|
| p3.16xlarge | V100 16GB | 8 | NVLink 2.0 | 150 GB/s | 25 Gbps ENA |
| p4d.24xlarge | A100 40GB | 8 | NVLink 3.0 + NVSwitch | 600 GB/s | 400 Gbps EFA |
| p4de.24xlarge | A100 80GB | 8 | NVLink 3.0 + NVSwitch | 600 GB/s | 400 Gbps EFA |
| p5.48xlarge | H100 80GB | 8 | NVLink 4.0 + NVSwitch | 900 GB/s | 3200 Gbps EFA |
| p5e.48xlarge | H200 141GB | 8 | NVLink 4.0 + NVSwitch | 900 GB/s | 3200 Gbps EFA |

### GCP GPU 인스턴스

| 인스턴스 | GPU | GPU 수 | GPU 간 인터커넥트 | 인스턴스 간 |
|---------|-----|--------|----------------|-----------|
| a2-highgpu-8g | A100 40GB | 8 | NVLink 3.0 + NVSwitch | 100 Gbps gVNIC |
| a2-ultragpu-8g | A100 80GB | 8 | NVLink 3.0 + NVSwitch | 100 Gbps gVNIC |
| a3-highgpu-8g | H100 80GB | 8 | NVLink 4.0 + NVSwitch | 3200 Gbps GPUDirect |
| a3-megagpu-8g | H200 141GB | 8 | NVLink 4.0 + NVSwitch | 3200 Gbps GPUDirect |

### 클라우드 인스턴스 선택 가이드

| 워크로드 | 최소 권장 인스턴스 | 이유 |
|---------|----------------|------|
| 7B 추론 (TP=2) | p4d/a2 (A100) | NVLink 3.0이면 충분 |
| 70B 추론 (TP=8) | p5/a3 (H100) | NVLink 4.0 + 80GB 메모리 필요 |
| 7B 학습 (FSDP) | p4d/a2 (A100) | NVLink + 충분한 메모리 |
| 70B 학습 (3D 병렬) | p5/a3 멀티 노드 | NVLink + EFA/GPUDirect |
| 405B 추론 | p5 멀티 노드 | 4+ 노드 TP+PP |

---

## NVLink 없이 Multi-GPU 활용하기

소비자 GPU(RTX 3090/4090)는 NVLink를 지원하지 않는다. RTX 3090은 NVLink 브리지(2-way)를 지원했지만, RTX 4090에서는 NVLink이 제거되었다. PCIe 연결만으로 효율적으로 Multi-GPU를 활용하는 전략을 정리한다.

### 전략 1: Pipeline Parallelism 우선 사용

PP는 레이어 경계에서만 통신이 발생하므로, PCIe 대역폭에서도 충분히 효율적이다. Ollama, llama.cpp는 기본적으로 PP 방식으로 GPU에 레이어를 분배한다.

### 전략 2: TP는 2 GPU까지만

PCIe 4.0에서 TP는 **2 GPU까지** 실용적이다. 3 GPU 이상에서는 AllReduce의 통신량이 급증하여, 오히려 단일 GPU 대비 느려질 수 있다.

| GPU 수 (TP) | PCIe 4.0 통신 오버헤드 | NVLink 4.0 통신 오버헤드 | PCIe에서 실용성 |
|------------|---------------------|----------------------|---------------|
| 2 | ~15% | ~1% | 실용적 |
| 4 | ~35% | ~2% | 비효율적 |
| 8 | ~60% | ~4% | 사실상 불가 |

### 전략 3: 양자화로 GPU 요구 수 줄이기

[[nvfp4-quantization-concepts|양자화]]로 모델 크기를 줄이면, 더 큰 모델을 적은 GPU에 탑재할 수 있다:

| 모델 | FP16 크기 | INT8 크기 | INT4 크기 | 단일 24GB GPU | 2x 24GB GPU (PP) |
|------|----------|----------|----------|-------------|----------------|
| 7B | 14 GB | 7 GB | 4 GB | INT8/INT4 가능 | FP16 가능 |
| 13B | 26 GB | 13 GB | 7 GB | INT4 가능 | INT8 가능 |
| 70B | 140 GB | 70 GB | 35 GB | 불가 | INT4로 겨우 가능 |
| 405B | 810 GB | 405 GB | 203 GB | 불가 | 불가 |

### 전략 4: CPU 오프로딩

FSDP의 `cpu_offload` 옵션으로 파라미터를 CPU RAM에 저장하고, 필요할 때만 GPU로 전송할 수 있다. 학습 속도는 느려지지만 메모리 제약을 극복할 수 있다.

---

## GPU별 인터커넥트 종합 비교

### 데이터센터 GPU

| GPU | 세대 | HBM 대역폭 | NVLink 대역폭 | PCIe | NVSwitch 지원 | VRAM |
|-----|------|-----------|-------------|------|-------------|------|
| P100 | Pascal | 732 GB/s | 80 GB/s (NVL1) | 3.0 x16 | 미지원 | 16 GB |
| V100 | Volta | 900 GB/s | 150 GB/s (NVL2) | 3.0 x16 | NVS 1.0 | 32 GB |
| A100 | Ampere | 2039 GB/s | 600 GB/s (NVL3) | 4.0 x16 | NVS 2.0 | 40/80 GB |
| H100 SXM | Hopper | 3350 GB/s | 900 GB/s (NVL4) | 5.0 x16 | NVS 3.0 | 80 GB |
| H100 PCIe | Hopper | 2039 GB/s | 미지원 | 5.0 x16 | 미지원 | 80 GB |
| H200 SXM | Hopper | 4800 GB/s | 900 GB/s (NVL4) | 5.0 x16 | NVS 3.0 | 141 GB |
| B200 | Blackwell | 8000 GB/s | 1800 GB/s (NVL5) | 5.0 x16 | NVS 4.0 | 192 GB |

:::warning
**H100 SXM vs H100 PCIe**: 같은 H100이라도 폼팩터에 따라 인터커넥트가 완전히 다르다. H100 PCIe 버전은 NVLink를 지원하지 않으며, HBM 대역폭도 SXM 대비 낮다. 클라우드 인스턴스를 선택할 때 반드시 SXM 버전인지 확인해야 한다.
:::

### 소비자 GPU

| GPU | NVLink | PCIe | VRAM | Multi-GPU 최적 전략 |
|-----|--------|------|------|------------------|
| RTX 3090 | NVLink Bridge (2-way, 112 GB/s) | 4.0 x16 | 24 GB | NVLink 2-way TP 또는 PP |
| RTX 3090 Ti | 미지원 | 4.0 x16 | 24 GB | PP only |
| RTX 4090 | 미지원 | 4.0 x16 | 24 GB | PP only |
| RTX 5090 | 미지원 | 5.0 x16 | 32 GB | PP only |

---

## 인터커넥트 비용 대비 효과 분석

### 시스템별 비용 및 성능

| 시스템 | 대략적 가격 | GPU 수 | NVLink | 총 대역폭 (GPU 간) | 가격/대역폭 |
|--------|-----------|--------|--------|------------------|-----------|
| 2x RTX 4090 (PCIe) | ~$4,000 | 2 | 없음 | 64 GB/s | $62.5/GB/s |
| 2x RTX 3090 + NVLink Bridge | ~$3,000 | 2 | Bridge | 112 GB/s | $26.8/GB/s |
| DGX A100 (640GB) | ~$200,000 | 8 | NVL3+NVS2 | 4800 GB/s | $41.7/GB/s |
| DGX H100 | ~$350,000 | 8 | NVL4+NVS3 | 7200 GB/s | $48.6/GB/s |

### 클라우드 비용 비교 (시간당 참고가)

| 인스턴스 | 시간당 비용 | GPU 간 대역폭 | 비용/대역폭 (시간당) | 적합 워크로드 |
|---------|-----------|-------------|-----------------|-----------|
| p4d.24xlarge (A100x8) | ~$32/hr | 600 GB/s x8 | $0.0067/GB/s | 학습, 대형 추론 |
| p5.48xlarge (H100x8) | ~$98/hr | 900 GB/s x8 | $0.0136/GB/s | 초대형 학습/추론 |
| g5.48xlarge (A10Gx8) | ~$16/hr | PCIe only | $0.25/GB/s | 소형 추론, 파인튜닝 |

---

## 워크로드별 인터커넥트 선택 가이드

### 의사결정 요약

| 질문 | 답변 |
|------|------|
| NVLink가 필요한 경우는? | TP를 3+ GPU에서 사용하거나, FSDP로 대규모 학습을 할 때 |
| PCIe에서 Multi-GPU가 가능한가? | 가능하지만, PP 중심으로 사용하고 TP는 2 GPU까지만 권장 |
| 소비자 GPU에서 대안은? | [[nvfp4-quantization-concepts|양자화]]로 모델 크기 축소 + PP 분배가 가장 실용적 |
| 클라우드에서는? | A100/H100 인스턴스는 NVLink 기본 제공. Multi-GPU 추론 시 TP 적극 활용 |
| H100 SXM vs PCIe? | NVLink가 필요하면 반드시 SXM 버전 선택 |
| GB200 NVL72는 언제 필요한가? | 수조 파라미터 모델을 단일 노드에서 추론할 때 |

### 시나리오별 상세 가이드

| 시나리오 | 모델 크기 | GPU 구성 | 인터커넥트 | 병렬 전략 | 예상 효율 |
|---------|---------|---------|-----------|---------|---------|
| 개인 학습 (7B) | 7B | 2x RTX 4090 | PCIe 4.0 | DDP | 85-90% |
| 개인 추론 (70B) | 70B INT4 | 2x RTX 4090 | PCIe 4.0 | PP | 70-80% |
| 클라우드 학습 (13B) | 13B | p4d (A100x8) | NVLink 3.0 | FSDP | 90-95% |
| 클라우드 추론 (70B) | 70B | p5 (H100x8) | NVLink 4.0 | TP=8 | 95%+ |
| 대규모 학습 (70B) | 70B | p5 x4 (H100x32) | NVLink+EFA | TP=8,PP=2,DP=2 | 80-85% |
| 초대규모 추론 (405B) | 405B | p5 x8 (H100x64) | NVLink+EFA | TP=8,PP=8 | 75-80% |

---

## 정리

NVLink는 "있으면 좋은" 기술이 아니라, Multi-GPU AI 워크로드의 **효율을 결정하는 핵심 인프라**이다.

핵심 포인트:

1. **대역폭 격차**: NVLink 5.0은 PCIe 4.0 대비 28배 빠르며, 이 격차는 세대가 지날수록 벌어진다
2. **TP의 전제조건**: 3개 이상 GPU에서 Tensor Parallelism을 효과적으로 사용하려면 NVLink가 사실상 필수이다
3. **NVSwitch의 역할**: NVLink를 All-to-All 토폴로지로 확장하여, 최대 72개 GPU를 단일 메모리 공간으로 통합한다
4. **PCIe 환경의 전략**: NVLink 없이는 PP 중심 + 양자화로 접근하는 것이 가장 현실적이다
5. **클라우드 활용**: A100/H100 SXM 인스턴스는 NVLink를 기본 제공하므로, TP를 적극 활용해야 비용 대비 효율이 극대화된다

[[multi-gpu-parallel-pytorch|병렬 처리 전략]]을 선택할 때, GPU 자체의 연산 성능만큼이나 **GPU 간 연결**을 반드시 고려해야 한다. [[inference-optimization-mfu|추론 최적화]] 관점에서도, MFU(Model FLOPs Utilization)를 높이려면 통신 병목을 제거하는 것이 선결 조건이다.
