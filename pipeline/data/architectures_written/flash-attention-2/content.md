<!-- infographic-hero -->
![FlashAttention-2 핵심 요약](figures/infographic.svg)

*Figure: FlashAttention-2 한 장 요약 인포그래픽*

# FlashAttention-2: 최적화된 병렬성과 워크 파티셔닝

**Stanford University / Together AI** · **2023-07-17** · **오픈소스**

## 개요

FlashAttention-2는 Tri Dao가 2023년 Together AI에서 제안한 FlashAttention의 개선 버전이다. FlashAttention-1이 IO-aware 타일링으로 어텐션 연산의 메모리 병목을 해결했다면, FlashAttention-2는 **GPU 하드웨어 활용률 극대화**에 초점을 맞추었다.

A100 GPU의 이론 최대 연산량은 312 TFLOPS(FP16)이지만, FlashAttention-1은 이 중 약 35%만 활용했다. FlashAttention-2는 non-matmul FLOP 감소, 쿼리 루프 병렬화, GQA/MQA 네이티브 지원의 **세 가지 핵심 최적화**를 통해 이론 최대의 **약 72%(~230 TFLOPS)**를 달성한다. 이는 FlashAttention-1 대비 약 **2배**의 처리량 향상이며, 현재 LLM 추론 및 학습 프레임워크 전반에서 사실상 표준 어텐션 구현으로 채택되어 있다.

![FlashAttention-2 아키텍처 - 쿼리 루프 병렬화와 non-matmul FLOP 최소화로 GPU 활용률을 극대화한 구조](figures/architecture.svg)

*Figure 1: FlashAttention-2 아키텍처 - FlashAttention-1의 타일링 전략을 계승하면서 쿼리 기준 병렬화, non-matmul 연산 최소화, GQA/MQA 네이티브 지원으로 A100 이론 최대의 72%를 달성한다.*

## 기법 상세

FlashAttention의 핵심 아이디어는 어텐션 행렬을 블록 단위로 나누어 SRAM에서 계산하고, 중간 결과를 HBM에 기록하지 않는 것이다. 다음 다이어그램은 이 타일링 기반 포워드 패스의 전체 흐름을 보여준다.

![FlashAttention 포워드 패스 타일링 다이어그램](figures/fig_1.png)
*Figure 1: FlashAttention 포워드 패스 다이어그램 - K, V를 블록으로 분할하여 SRAM에서 계산 후 rescaling으로 정확한 결과를 얻으며, 중간 행렬 S, P의 HBM 접근을 회피한다. (Source: Dao, 2023)*

### 개선 1: Non-matmul FLOP 최소화

GPU에서 행렬 곱셈(matmul)은 텐서 코어를 통해 매우 높은 처리량을 보이지만, 그 외 연산(rescaling, 비교, 지수 함수 등)은 일반 CUDA 코어에서 처리되어 **16배 이상 느리다**. FlashAttention-1에서는 온라인 소프트맥스 과정에서 각 블록마다 이전 출력을 rescale하는 연산이 발생했다.

```
FlashAttention-1:
  O_i = diag(l_prev/l_new)^{-1} * O_prev + diag(l_curr/l_new)^{-1} * exp(S_ij - m_new) * V_j

FlashAttention-2:
  최종 루프 종료 후에만 한 번 rescale:
  O = diag(l)^{-1} * O_accumulated
```

FlashAttention-2는 **rescaling을 루프 종료 후 한 번만 수행**하도록 알고리즘을 재구성했다. 루프 내에서는 정규화되지 않은 출력을 누적하고, 마지막에 한 번만 정규화한다. 이로써 non-matmul FLOP이 **절반으로 감소**한다.

### 개선 2: 워프 병렬화(Warp Parallelism) 최적화

FlashAttention-1에서는 K, V 블록을 외부 루프, Q 블록을 내부 루프로 처리했다. 이 방식에서는 하나의 스레드 블록 내의 여러 워프(warp)가 K, V를 공유 메모리에서 읽고, 각 워프가 Q의 서로 다른 부분을 담당하여 출력의 서로 다른 조각을 계산한 뒤 결과를 합산해야 했다. 이 합산 과정에서 **워프 간 동기화(shared memory reduction)**가 필요했다.

FlashAttention-2는 **루프 구조를 뒤집었다**: Q 블록을 외부 루프로, K/V 블록을 내부 루프로 변경했다. 이에 따라 포워드/백워드 패스에서 워커(스레드 블록)의 병렬화 방식도 달라진다.

![포워드 및 백워드 패스에서의 워커 병렬화 방식](figures/fig_2.png)
*Figure 2: 포워드/백워드 패스 병렬화 전략 - 포워드 패스에서는 각 워커가 어텐션 행렬의 행 블록을 담당하고, 백워드 패스에서는 열 블록을 담당한다. (Source: Dao, 2023)*

```
FlashAttention-1:
  for each (K_j, V_j) block:      ← 외부 루프
    for each Q_i block:            ← 내부 루프
      워프들이 Q_i의 다른 부분 처리 → 결과 합산 필요 (동기화)

FlashAttention-2:
  for each Q_i block:              ← 외부 루프
    for each (K_j, V_j) block:     ← 내부 루프
      각 워프가 Q_i의 자기 행만 전담 → 합산 불필요 (독립 실행)
```

이 변경으로 각 워프가 **독립적으로 자신의 출력 행을 계산**할 수 있게 되어, 워프 간 공유 메모리 통신과 동기화가 **완전히 제거**되었다. 이는 전체 성능의 핵심적인 향상 요소다. 아래 그림은 FA1과 FA2의 워프 파티셔닝 차이를 명확히 보여준다.

![FlashAttention-1의 워프 파티셔닝 - K를 워프 간 분할](figures/fig_3_1.png)
*Figure 3a: FlashAttention-1 워프 파티셔닝 - K를 워프 간에 분할하여 결과를 합산(reduction)해야 하므로 워프 간 동기화가 필요하다. (Source: Dao, 2023)*

![FlashAttention-2의 워프 파티셔닝 - Q를 워프 간 분할](figures/fig_3_2.png)
*Figure 3b: FlashAttention-2 워프 파티셔닝 - Q를 워프 간에 분할하여 각 워프가 독립적으로 출력 행을 계산하므로, 워프 간 통신 없이 병렬 실행이 가능하다. (Source: Dao, 2023)*

### 개선 3: GQA/MQA 네이티브 지원

최신 대형 언어 모델들은 추론 효율을 위해 GQA(Grouped Query Attention) 또는 MQA(Multi-Query Attention)를 널리 채택하고 있다. GQA에서는 여러 쿼리 헤드가 하나의 KV 헤드를 공유한다.

| 어텐션 유형 | 쿼리 헤드 | KV 헤드 | 예시 모델 |
|------------|----------|---------|----------|
| MHA | 32 | 32 | GPT-3, LLaMA-1 |
| GQA | 32 | 8 | LLaMA-2 70B, Mistral |
| MQA | 32 | 1 | PaLM, Falcon |

FlashAttention-1에서 GQA를 사용하려면 KV 텐서를 쿼리 헤드 수만큼 **브로드캐스팅(복제)**해야 했다. FlashAttention-2는 커널 내부에서 헤드 매핑을 직접 처리하여 **메모리 복제 없이** GQA/MQA를 지원한다. 이를 통해 KV 캐시 메모리를 크게 절약하면서도 최적의 연산 효율을 유지한다.

## 핵심 혁신

| 혁신 | FlashAttention-1 | FlashAttention-2 | 개선 효과 |
|------|-----------------|-----------------|----------|
| non-matmul FLOP | 매 블록마다 rescale | 최종 1회 rescale | FLOP 절반 감소 |
| 루프 순서 | K/V 외부, Q 내부 | Q 외부, K/V 내부 | 워프 동기화 제거 |
| GQA/MQA | 브로드캐스트 필요 | 네이티브 지원 | 메모리 절약 |
| 헤드 차원 | 최대 128 | 최대 256 | 더 큰 헤드 지원 |
| GPU 활용률 | ~35% | ~72% | 2배 향상 |

## 벤치마크/성능

다음 벤치마크는 A100 80GB에서 다양한 시퀀스 길이에 따른 FlashAttention-2의 속도 우위를 보여준다.

![A100 GPU에서의 어텐션 구현별 속도 비교 벤치마크](figures/fig_7.png)
*Figure 4: A100 80GB에서 시퀀스 길이별 어텐션 속도 비교 (head_dim=64, causal mask 없음) - FlashAttention-2가 PyTorch, xFormers, FA1, Triton 구현을 모두 압도하며, 16K 시퀀스에서 176 TFLOPS/s를 달성한다. (Source: Dao, 2023)*

### A100 80GB SXM5 기준 처리량

| 시퀀스 길이 | FlashAttention-1 | FlashAttention-2 | 속도 향상 |
|------------|-----------------|-----------------|----------|
| 2K | ~120 TFLOPS | ~220 TFLOPS | 1.8× |
| 4K | ~130 TFLOPS | ~230 TFLOPS | 1.8× |
| 8K | ~125 TFLOPS | ~225 TFLOPS | 1.8× |
| 16K | ~120 TFLOPS | ~220 TFLOPS | 1.8× |

### Triton 구현 대비

FlashAttention-2의 CUDA 구현은 Triton 구현 대비 약 **1.3~1.5배** 빠르다. 이는 CUDA의 세밀한 메모리 관리(공유 메모리 뱅크 충돌 방지, 레지스터 할당 최적화)가 Triton의 자동 코드 생성보다 여전히 우위에 있기 때문이다.

### End-to-End 학습 성능

GPT-style 모델 학습에서 FlashAttention-2를 적용하면 전체 학습 시간이 **약 1.3~1.5배 단축**된다 (어텐션이 전체 학습 시간의 약 40~60%를 차지하므로).

## 관련 기법 비교

| 항목 | FlashAttention-1 | FlashAttention-2 | xFormers |
|------|-----------------|-----------------|----------|
| GPU 활용률 | ~35% | ~72% | ~50% |
| GQA 지원 | 브로드캐스트 | 네이티브 | 네이티브 |
| 최대 head_dim | 128 | 256 | 128 |
| Triton 지원 | O | O | O |
| 역전파 최적화 | 기본 | 개선 | 기본 |

## 실무 활용

### PyTorch 2.0+ (가장 간편한 방법)

```python
import torch
import torch.nn.functional as F

# PyTorch 2.0+에서는 자동으로 FlashAttention-2 백엔드 선택
q = torch.randn(2, 32, 4096, 128, device="cuda", dtype=torch.float16)
k = torch.randn(2, 8, 4096, 128, device="cuda", dtype=torch.float16)  # GQA: 8 KV heads
v = torch.randn(2, 8, 4096, 128, device="cuda", dtype=torch.float16)

# GQA를 위해 enable_gqa=True 설정
output = F.scaled_dot_product_attention(
    q, k, v,
    is_causal=True,
    enable_gqa=True  # PyTorch 2.3+ GQA 지원
)
```

### flash-attn 라이브러리 직접 사용

```python
from flash_attn import flash_attn_func, flash_attn_varlen_func

# 기본 사용: (batch, seqlen, nheads, headdim)
q = torch.randn(2, 4096, 32, 128, device="cuda", dtype=torch.float16)
k = torch.randn(2, 4096, 8, 128, device="cuda", dtype=torch.float16)  # GQA
v = torch.randn(2, 4096, 8, 128, device="cuda", dtype=torch.float16)

output = flash_attn_func(q, k, v, causal=True)

# 가변 길이 시퀀스 지원 (배치 내 패딩 제거)
output_varlen = flash_attn_varlen_func(
    q.reshape(-1, 32, 128),  # (total_seqlen, nheads, headdim)
    k.reshape(-1, 8, 128),
    v.reshape(-1, 8, 128),
    cu_seqlens_q=torch.tensor([0, 2048, 6144], device="cuda", dtype=torch.int32),
    cu_seqlens_k=torch.tensor([0, 2048, 6144], device="cuda", dtype=torch.int32),
    max_seqlen_q=4096,
    max_seqlen_k=4096,
    causal=True
)
```

### HuggingFace Transformers에서 활성화

```python
from transformers import AutoModelForCausalLM

# FlashAttention-2를 명시적으로 활성화
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-70b-hf",
    torch_dtype=torch.bfloat16,
    attn_implementation="flash_attention_2",  # FA-2 활성화
    device_map="auto"
)
# 추가 코드 변경 없이 자동으로 GQA + FlashAttention-2 적용
```

## 한계 및 전망

### 현재 한계
- **NVIDIA 전용**: Ampere(A100) 이상 GPU에서 최적 성능. Volta(V100)에서도 동작하지만 성능 이점이 줄어든다
- **head_dim 제약**: 256 이하의 헤드 차원만 지원
- **FP16/BF16 전용**: FP32 연산은 지원하지 않으며, 혼합 정밀도 학습이 전제된다
- **Window Attention**: Sliding window attention 등 특수 마스크 패턴의 지원이 제한적이다 (FlashAttention-3에서 개선)

### FlashAttention-3로의 발전
2024년 발표된 FlashAttention-3는 NVIDIA H100 GPU의 새로운 기능을 활용한다. TMA(Tensor Memory Accelerator)를 통한 비동기 메모리 접근, FP8 텐서 코어 지원, 그리고 warp 특화 소프트맥스 파이프라이닝으로 H100에서 이론 최대의 **약 75%**에 달하는 처리량을 달성한다.

현재 FlashAttention-2는 **vLLM, TGI, Megatron-LM, DeepSpeed** 등 모든 주요 LLM 프레임워크에서 기본 어텐션 커널로 채택되어 있으며, LLM 생태계에서 가장 중요한 시스템 최적화 기법 중 하나로 자리매김했다.

## 참고 자료

- [논문](https://arxiv.org/abs/2307.08691)
- [코드](https://github.com/Dao-AILab/flash-attention)

## 관련 문서

- [[flash-attention|FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness]] - 발전 기반
