---
title: "QLoRA: Efficient Finetuning of Quantized LLMs"
slug: qlora
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.402136+00:00"
architecture_entry: qlora
---

## 개요

LoRA가 학습 파라미터를 크게 줄였지만, 사전학습 모델 자체의 가중치를 FP16 또는 BF16으로 로드하는 것은 여전히 막대한 GPU 메모리를 요구합니다. 65B 모델의 경우 FP16 로딩만으로 약 130GB의 GPU 메모리가 필요합니다.

QLoRA는 모델을 4비트로 양자화하여 메모리를 줄이고, LoRA 어댑터만 BF16으로 학습하는 접근법입니다. 세 가지 새로운 기술을 통해 단일 48GB GPU에서 65B 모델 파인튜닝을 실현하면서도 성능 저하를 최소화합니다.

## 배경 및 문제

### 기존 양자화의 한계

일반적인 INT8 또는 INT4 양자화는 추론에는 효과적이지만 학습 시에는 양자화 오차가 그래디언트를 통해 증폭되는 문제가 있습니다. 기존 방법들은 양자화와 파인튜닝을 동시에 지원하는 실용적 프레임워크가 부재했습니다.

### 메모리 요구량 분석

| 모델 크기 | FP16 메모리 | INT8 메모리 | INT4 메모리 |
|---------|-----------|-----------|----------|
| 7B | ~14 GB | ~7 GB | ~3.5 GB |
| 13B | ~26 GB | ~13 GB | ~6.5 GB |
| 33B | ~66 GB | ~33 GB | ~16.5 GB |
| 65B | ~130 GB | ~65 GB | ~32.5 GB |

4비트 양자화를 통해 65B 모델도 단일 48GB GPU에 탑재 가능합니다.

## 핵심 기술

### 1. 4비트 NormalFloat (NF4)

기존 INT4 양자화는 값을 균등하게 분할하지만, 정규분포를 따르는 신경망 가중치에는 비효율적입니다. NF4는 가중치가 정규분포를 따른다는 사실을 활용하여 **정보 이론적으로 최적**인 양자화를 수행합니다.

NF4 양자화 절차:
1. 가중치를 타일 단위로 정규화: $w_i^{\text{norm}} = w_i / \max(|w_i|)$
2. 정규분포의 동등 확률 구간(equal quantile)에 해당하는 16개 격자점 계산
3. 각 가중치를 가장 가까운 격자점으로 매핑 (4비트 = 16개 값)

격자점 $q_i$는 다음 조건을 만족합니다:
$$q_i = \frac{1}{2}\left(Q_X^{-1}\left(\frac{i-1}{2^k-1}\right) + Q_X^{-1}\left(\frac{i}{2^k-1}\right)\right)$$

여기서 $Q_X^{-1}$는 표준정규분포의 분위수 함수, $k=4$입니다.

동등한 비트 수에서 INT4보다 낮은 양자화 오차를 가집니다.

### 2. 이중 양자화 (Double Quantization)

4비트 블록별 양자화(block-wise quantization)에서는 각 블록의 스케일 팩터를 저장해야 합니다. 블록 크기 64, FP32 스케일 팩터의 경우 파라미터당 약 0.5비트의 추가 오버헤드가 발생합니다.

이중 양자화는 스케일 팩터 자체를 다시 8비트로 양자화합니다:

$$c_2^{\text{FP32}} \xrightarrow{\text{양자화}} c_1^{\text{INT8}}$$

이를 통해 스케일 팩터의 메모리 오버헤드를 0.5비트/파라미터 → 약 0.127비트/파라미터로 감소시킵니다. 65B 모델 기준 약 2.1 GB 메모리 절약 효과가 있습니다.

### 3. 페이지드 옵티마이저 (Paged Optimizers)

Adam 옵티마이저는 파라미터당 2개의 상태(1차, 2차 모멘트)를 유지합니다. 긴 시퀀스 처리 시 미니배치 내에서 일시적으로 GPU 메모리가 급증하는 경우(메모리 스파이크) OOM(Out of Memory)이 발생할 수 있습니다.

NVIDIA의 통합 메모리(unified memory)를 활용하여 옵티마이저 상태를 CPU DRAM과 GPU DRAM 사이에서 자동으로 페이징합니다:

- GPU 메모리 부족 시 옵티마이저 상태를 CPU RAM으로 자동 이동
- 업데이트 필요 시 다시 GPU로 전송
- 처리량 손실 없이 OOM 방지

## 방법론

### QLoRA 학습 프로세스

1. **모델 로드**: 사전학습 모델을 NF4 4비트로 양자화하여 로드
2. **LoRA 추가**: 양자화된 가중치에 BF16 LoRA 어댑터 레이어 삽입
3. **역전파**: BF16으로 그래디언트 계산 (양자화 가중치는 동결, 자동으로 역양자화)
4. **업데이트**: LoRA 파라미터만 업데이트 (전체 파라미터 대비 0.1~1% 수준)

### 역전파의 수치 정밀도

양자화된 가중치 $W_4$와 LoRA 가중치 $L_{BF16}$의 연산:

$$Y_{BF16} = X_{BF16} \cdot \text{dequant}(W_4^{NF4}) + X_{BF16} \cdot L_{BF16}$$

역방향 패스에서 $\text{dequant}(W_4)$는 BF16으로 변환되어 연산되므로 그래디언트의 수치 안정성이 유지됩니다.

## 실험 결과

### Guanaco (65B) vs ChatGPT

Vicuna 벤치마크(GPT-4 평가, 80개 대화 질문):

| 모델 | ChatGPT 대비 성능 |
|------|----------------|
| GPT-4 | 97.9% |
| Guanaco-65B (QLoRA) | **99.3%** |
| Guanaco-33B (QLoRA) | 97.8% |
| Guanaco-13B (QLoRA) | 91.2% |
| Guanaco-7B (QLoRA) | 87.5% |

65B Guanaco는 ChatGPT와 비교 가능한 수준을 달성했습니다.

### MMLU 5-shot 결과

| 모델 | 방법 | MMLU (5-shot) |
|------|------|-------------|
| LLaMA 65B | FT (전체) | 63.1 |
| LLaMA 65B | QLoRA | 62.9 |
| LLaMA 33B | QLoRA | 60.4 |
| LLaMA 13B | QLoRA | 54.7 |
| GPT-3.5 | - | 70.0 |

QLoRA는 전체 파인튜닝 대비 0.2% 수준의 성능 손실만으로 메모리를 대폭 절감합니다.

### 메모리 사용량 비교 (65B 기준)

| 방법 | GPU 메모리 | 필요 GPU 수 |
|------|----------|----------|
| FP16 전체 파인튜닝 | ~780 GB | A100 80GB × 10+ |
| LoRA (BF16) | ~160 GB | A100 80GB × 2 |
| QLoRA (NF4) | ~48 GB | A100 80GB × 1 |

## 의의 및 한계

### 의의

- **민주화**: 소규모 연구팀과 개인도 65B 이상의 모델을 단일 GPU로 파인튜닝 가능
- **성능 보존**: NF4 양자화 오차가 매우 작아 전체 파인튜닝과 성능 격차가 미미
- **실용적 도구**: bitsandbytes, HuggingFace PEFT와 결합하여 즉시 사용 가능한 라이브러리로 배포
- **후속 연구**: GPTQ, AWQ, LoftQ 등 양자화+PEFT 연구의 기반

### 한계

- 4비트 양자화로 인한 누적 정밀도 손실은 완전히 제거할 수 없음
- 역양자화-재양자화 과정으로 학습 속도가 전체 파인튜닝보다 느림 (약 1.5~2x 느림)
- 매우 작은 모델(7B 이하)에서는 양자화 오차의 상대적 영향이 커짐
- NF4는 추론 시에도 매번 역양자화가 필요하여 추론 속도에 영향을 줄 수 있음

## 코드 예제

### QLoRA: 4비트 양자화 + LoRA 파인튜닝 (bitsandbytes + PEFT)

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model
from peft import TaskType

# NF4 양자화 설정 (QLoRA 핵심)
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,              # 4비트로 로드
    bnb_4bit_quant_type="nf4",       # NormalFloat 4-bit (정규분포 최적)
    bnb_4bit_compute_dtype=torch.bfloat16,  # 연산은 BF16으로
    bnb_4bit_use_double_quant=True,  # Double Quantization: 양자화 상수도 양자화
)

# 모델 로드 (NF4로 양자화된 상태)
model_id = "meta-llama/Llama-2-7b-hf"  # 또는 다른 모델
# model = AutoModelForCausalLM.from_pretrained(
#     model_id,
#     quantization_config=bnb_config,
#     device_map="auto",
# )

# QLoRA 설정
qlora_config = LoraConfig(
    r=64,                    # 랭크 (QLoRA 논문 권장)
    lora_alpha=16,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",  # 어텐션
        "gate_proj", "up_proj", "down_proj",        # FFN
    ],
    lora_dropout=0.1,
    bias="none",
    task_type=TaskType.CAUSAL_LM,
)

# NF4 데이터 타입 직접 구현 (이해용)
def create_nf4_bins(num_bins=16):
    """NF4: 정규분포의 균등 분위수를 양자화 포인트로 사용.
    일반 int4 대비 정규분포 가중치에 최적화.
    """
    import scipy.stats as stats
    import numpy as np
    # 균등 분위수 계산 (정규분포)
    quantiles = np.linspace(0, 1, num_bins + 1)
    bins = stats.norm.ppf(quantiles[:-1] + (quantiles[1:] - quantiles[:-1]) / 2)
    bins = bins / max(abs(bins.min()), abs(bins.max()))  # [-1, 1] 정규화
    return torch.tensor(bins, dtype=torch.float32)

def quantize_to_nf4(weight, nf4_bins):
    """가중치를 NF4로 양자화."""
    # 최댓값으로 정규화
    absmax = weight.abs().max()
    normalized = weight / absmax
    # 가장 가까운 NF4 빈에 매핑
    distances = (normalized.unsqueeze(-1) - nf4_bins).abs()
    indices = distances.argmin(dim=-1).to(torch.uint8)  # 4비트 인덱스
    return indices, absmax

def dequantize_nf4(indices, absmax, nf4_bins):
    """NF4 인덱스 → BF16 복원 (역전파 시 사용)."""
    quantized = nf4_bins[indices.long()]
    return (quantized * absmax).to(torch.bfloat16)

# 메모리 절감 계산
print("=== QLoRA 메모리 분석 ===")
llama_7b_params = 7e9
bf16_mem = llama_7b_params * 2 / 1024**3   # BF16: 2바이트/파라미터
nf4_mem = llama_7b_params * 0.5 / 1024**3  # NF4: 0.5바이트/파라미터 (4비트)
lora_overhead = 0.1e9 * 2 / 1024**3        # LoRA 어댑터 ~100M 파라미터
print(f"표준 BF16 파인튜닝: {llama_7b_params * 2 * 2 / 1024**3:.0f} GB (모델+옵티마이저)")
print(f"QLoRA: {nf4_mem + lora_overhead:.1f} GB (NF4 모델 + LoRA 어댑터)")
print(f"절감률: {(1-(nf4_mem+lora_overhead)/(llama_7b_params*4/1024**3))*100:.0f}%")
```

> **QLoRA 핵심 공식**: `frozen(NF4(W₀)) + trainable(LoRA)` — 베이스 모델은 4비트로 동결, LoRA 어댑터만 BF16으로 학습. 역전파 시 NF4 → BF16 디퀀타이즈 → 그래디언트 계산 → LoRA 업데이트.