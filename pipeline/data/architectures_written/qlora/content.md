# QLoRA: 양자화된 대형 언어 모델의 효율적 파인튜닝

**University of Washington** · **2023-05-23** · **오픈소스**

## 개요

QLoRA(Quantized LoRA)는 Tim Dettmers 등이 2023년 워싱턴 대학교에서 제안한 기법으로, **4비트 양자화와 LoRA를 결합**하여 65B 규모의 대형 언어 모델을 단일 48GB GPU에서 파인튜닝할 수 있게 한다.

기존의 16비트 LoRA도 메모리를 크게 절감하지만, 65B 모델의 16비트 가중치 자체가 약 130GB를 차지하므로 여전히 다수의 고가 GPU가 필요하다. QLoRA는 사전 학습 가중치를 **4비트로 양자화하여 저장**하고, 역전파 시에만 BF16으로 디퀀타이즈하여 그래디언트를 계산한다.

NF4(NormalFloat 4-bit), Double Quantization, Paged Optimizers라는 **세 가지 핵심 혁신**으로 메모리를 극적으로 절감하면서도 16비트 풀 파인튜닝과 동등한 성능을 보존한다. Guanaco-33B 모델은 단일 GPU에서 12시간 학습만으로 **ChatGPT의 99.3% 수준**에 도달했다.

![Architecture](figures/architecture.svg)

아래 그림은 Full Finetuning, LoRA, QLoRA의 메모리 구조를 비교한 것으로, QLoRA가 4비트 양자화된 트랜스포머 위에 LoRA 어댑터를 적용하고 Paged Optimizers로 GPU-CPU 간 메모리를 관리하는 구조를 보여준다.

![Full Finetuning, LoRA, QLoRA 메모리 구조 비교](figures/fig_1.png)
*Figure 1: 파인튜닝 기법별 메모리 구조 비교 — Full Finetuning은 16비트 모델 전체를 학습하고, LoRA는 16비트 모델 위에 어댑터만 학습하며, QLoRA는 4비트 양자화 모델에 어댑터를 적용하고 Paged Optimizers로 메모리 스파이크를 처리한다. (Source: Dettmers et al., 2023)*

## 기법 상세

### 혁신 1: NF4 (NormalFloat 4-bit) 데이터 타입

QLoRA의 첫 번째 혁신은 **정보 이론적으로 최적인 4비트 데이터 타입** NF4의 설계이다.

사전 학습된 LLM의 가중치 분포는 평균 0, 표준편차 σ인 **정규 분포**를 따른다는 실증적 관찰에 기반한다. NF4는 이 정규 분포의 분위수(quantile)에 맞춰 양자화 구간을 설정하여, 각 구간에 동일한 확률 질량이 배정되도록 한다.

```python
# NF4 양자화 원리 (개념적 코드)
import torch
from scipy.stats import norm

# 정규 분포의 분위수 기반 양자화 레벨 계산
# 4비트 = 16개 레벨, 0은 정확히 표현
num_levels = 16
# [-1, 1] 범위에서 정규 분포의 분위수로 양자화 포인트 결정
quantiles = norm.ppf(torch.linspace(0, 1, num_levels + 1))
# 인접한 분위수의 중간값을 양자화 레벨로 사용
nf4_levels = [(quantiles[i] + quantiles[i+1]) / 2 for i in range(num_levels)]
```

| 데이터 타입 | 이론적 최적성 | 정보 손실 (vs FP32) |
|------------|-------------|-------------------|
| INT4 (균등 분할) | 낮음 | 높음 |
| FP4 | 중간 | 중간 |
| **NF4** | **정보 이론 최적** | **최소 (~0.5%)** |

NF4는 균등 간격의 INT4보다 정규 분포 가중치에 대해 **정보 손실이 유의미하게 낮다**. 실험적으로 FP32 대비 약 **0~1%의 성능 저하**만 발생한다.

다음 그래프는 4비트 데이터 타입별 LLaMA 모델의 제로샷 정확도를 비교한 것으로, NFloat(NF4)가 일반 Float4보다 모든 모델 크기에서 우수한 성능을 보인다.

![4비트 데이터 타입별 제로샷 정확도 비교 — NFloat vs Float4](figures/fig_3.png)
*Figure 3: 4비트 데이터 타입 성능 비교 — NFloat(NF4, 파란색)가 일반 Float4(초록색)보다 모든 모델 크기에서 유의미하게 높은 제로샷 정확도를 달성한다. Double Quantization(주황색)은 추가 메모리 절감을 제공한다. (Source: Dettmers et al., 2023)*

### 혁신 2: Double Quantization (이중 양자화)

양자화 과정에서는 블록 크기(보통 64개 가중치) 단위로 양자화 상수(scale factor)를 저장해야 한다. 이 양자화 상수 자체도 FP32로 저장되어 파라미터당 약 0.5비트의 추가 메모리 오버헤드가 발생한다.

Double Quantization은 **양자화 상수 자체를 다시 8비트로 양자화**하여 이 오버헤드를 약 0.127비트로 줄인다.

```
1차 양자화: 가중치 FP32 → NF4 (블록당 1개 FP32 양자화 상수)
2차 양자화: 양자화 상수 FP32 → FP8 (256개 상수를 하나의 그룹으로)

메모리 절감 효과:
- 1차 양자화만: 4비트 + 0.5비트(양자화 상수) = 4.5비트/파라미터
- Double Quantization: 4비트 + 0.127비트 = 4.127비트/파라미터
- 65B 모델 기준 약 3GB 추가 절감
```

### 혁신 3: Paged Optimizers (페이지드 옵티마이저)

대형 모델 학습 시 긴 시퀀스나 큰 배치에서 GPU 메모리 부족(OOM)이 간헐적으로 발생할 수 있다. QLoRA는 NVIDIA의 **통합 메모리(Unified Memory)** 기능을 활용하여, 옵티마이저 상태가 GPU VRAM에 들어가지 않으면 자동으로 **CPU RAM으로 페이징**한다.

```
일반 학습:
  GPU OOM 발생 → 학습 중단 → 배치 크기 줄이고 재시작

QLoRA Paged Optimizers:
  GPU 메모리 부족 감지 → 옵티마이저 상태 CPU로 자동 이동
  → GPU 메모리 확보 후 다시 로드 → 학습 계속
```

이는 OS의 가상 메모리 페이징과 유사한 개념으로, 메모리 스파이크 상황에서도 **학습이 중단되지 않고 안정적으로 진행**된다.

### QLoRA 전체 순전파/역전파 흐름

```
순전파:
  1. NF4 가중치 → BF16으로 디퀀타이즈
  2. BF16 가중치로 정상 순전파
  3. LoRA 경로: x → A(BF16) → B(BF16) → α/r 스케일링 → 출력에 합산

역전파:
  1. 그래디언트를 BF16으로 계산
  2. LoRA 파라미터(A, B)만 업데이트
  3. NF4 기저 가중치는 동결 (그래디언트 불필요)
  4. 옵티마이저 상태: LoRA 파라미터에 대해서만 유지
```

## 핵심 혁신

| 혁신 | 설명 | 메모리 절감 |
|------|------|------------|
| NF4 | 정규 분포 최적 4비트 양자화 | 가중치 16비트→4비트 (4배) |
| Double Quantization | 양자화 상수의 재양자화 | 파라미터당 0.37비트 절감 |
| Paged Optimizers | GPU↔CPU 자동 메모리 페이징 | OOM 방지 |
| LoRA 결합 | 4비트 기저 + BF16 LoRA 어댑터 | 학습 파라미터 수만 배 감소 |

## 벤치마크/성능

### 메모리 사용량 비교

| 모델 크기 | Full FT (16비트) | LoRA (16비트) | QLoRA (NF4) |
|----------|-----------------|-------------|-------------|
| 7B | ~56GB | ~28GB | **~6GB** |
| 13B | ~104GB | ~52GB | **~10GB** |
| 33B | ~264GB | ~132GB | **~18GB** |
| 65B | ~520GB | ~260GB | **~33GB** |

### 양자화 방식별 성능 비교 (LLaMA 7B, MMLU 5-shot)

| 양자화 방법 | 비트 | MMLU | PPL (WikiText2) |
|------------|------|------|------------------|
| FP16 (기준) | 16 | 35.1 | 5.68 |
| RTN INT4 | 4 | 32.8 | 6.31 |
| GPTQ INT4 | 4 | 33.5 | 6.09 |
| **NF4** | **4** | **34.9** | **5.72** |
| NF4 + DQ | 4.127 | 34.9 | 5.71 |

NF4는 4비트임에도 불구하고 **FP16과 거의 동일한 성능**을 유지한다.

아래 그래프는 4비트 QLoRA와 16비트 파인튜닝의 RougeL 성능을 비교한 것으로, QLoRA가 모든 Transformer 레이어에 LoRA를 적용했을 때 16비트 풀 파인튜닝과 동등한 성능을 달성함을 보여준다.

![QLoRA vs 16비트 파인튜닝 RougeL 성능 비교](figures/fig_2.png)
*Figure 2: QLoRA 성능 검증 — 4비트 QLoRA-All(파란색)이 16비트 Full Finetuning(주황색)과 동등한 RougeL 점수를 달성한다. 모든 Transformer 레이어에 LoRA를 적용하는 것이 핵심이다. (Source: Dettmers et al., 2023)*

### Guanaco 모델 성능 (Vicuna 벤치마크)

| 모델 | GPU | 학습 시간 | ChatGPT 대비 |
|------|-----|----------|-------------|
| Guanaco-7B | 1× RTX 3090 (24GB) | 6시간 | 85.4% |
| Guanaco-13B | 1× RTX 4090 (24GB) | 12시간 | 91.6% |
| Guanaco-33B | 1× A6000 (48GB) | 18시간 | 97.8% |
| Guanaco-65B | 1× A100 (40GB) | 40시간 | **99.3%** |

**단일 소비자급 GPU**에서 ChatGPT에 근접하는 성능을 달성한 것은 QLoRA의 가장 인상적인 결과다.

## 관련 기법 비교

| 기법 | 가중치 정밀도 | 학습 파라미터 | 최소 GPU | 65B 학습 가능? |
|------|------------|-------------|---------|---------------|
| Full Fine-tuning | FP16 | 전체 | 8× A100 80GB | O (막대한 비용) |
| LoRA | FP16 | ~0.1% | 4× A100 80GB | 어려움 |
| **QLoRA** | **NF4** | **~0.1%** | **1× A6000 48GB** | **O** |
| GPTQ + LoRA | INT4 | ~0.1% | 1× A6000 48GB | O (성능 열세) |

## 실무 활용

### bitsandbytes + PEFT (표준 방법)

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# 1. 4비트 양자화 설정
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,                    # NF4 4비트 로드
    bnb_4bit_quant_type="nf4",            # NF4 데이터 타입
    bnb_4bit_compute_dtype=torch.bfloat16, # 연산은 BF16
    bnb_4bit_use_double_quant=True,       # Double Quantization 활성화
)

# 2. 모델 로드 (4비트 양자화 적용)
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-70b-hf",
    quantization_config=bnb_config,
    device_map="auto",                     # 자동 GPU 배치
)

# 3. 그래디언트 체크포인팅 활성화 (메모리 절약)
model = prepare_model_for_kbit_training(model)

# 4. LoRA 어댑터 설정 및 적용
lora_config = LoraConfig(
    r=16,                                  # QLoRA에서는 r=16~64 권장
    lora_alpha=32,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"  # MLP도 포함
    ],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# 출력: trainable params: 83,886,080 || all params: 70,637,924,352 || trainable%: 0.1187%
```

### 학습 및 Paged Optimizer 설정

```python
from transformers import TrainingArguments, Trainer

training_args = TrainingArguments(
    output_dir="./qlora-llama2-70b",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16,     # 효과적 배치 크기 = 16
    learning_rate=2e-4,
    num_train_epochs=1,
    bf16=True,                          # BF16 혼합 정밀도
    optim="paged_adamw_8bit",           # Paged AdamW 8비트 옵티마이저
    max_grad_norm=0.3,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    gradient_checkpointing=True,        # 활성화 메모리 절약
    logging_steps=10,
    save_strategy="steps",
    save_steps=100,
)

trainer = Trainer(
    model=model,
    train_dataset=train_dataset,
    args=training_args,
    data_collator=data_collator,
)
trainer.train()
```

### TRL + QLoRA (RLHF/SFT 통합)

```python
from trl import SFTTrainer

# TRL의 SFTTrainer로 간편하게 QLoRA SFT 학습
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    dataset_text_field="text",
    max_seq_length=2048,
    peft_config=lora_config,           # LoRA 설정 전달
    args=training_args,
)
trainer.train()
```

다음 그래프는 LLaMA 모델 크기별 메모리 사용량 구성을 보여준다. QLoRA를 통해 65B 모델도 45GB에 수용되어 단일 GPU에서 학습이 가능하다.

![LLaMA 모델 크기별 메모리 풋프린트 분석](figures/fig_6.png)
*Figure 6: 메모리 풋프린트 분석 — 모델 가중치(파란색)가 메모리의 대부분을 차지하며, QLoRA의 4비트 양자화로 65B 모델이 45GB에 들어간다. Paged Optimizers가 남은 메모리 스파이크를 처리한다. (Source: Dettmers et al., 2023)*

## 한계 및 전망

### 현재 한계
- **학습 속도 저하**: NF4→BF16 디퀀타이즈 과정으로 인해 16비트 LoRA 대비 학습 속도가 약 **30~50% 느림**
- **추론 시 양자화**: 학습된 모델의 추론 성능은 양자화 정밀도에 여전히 의존한다
- **Paged Optimizer 오버헤드**: CPU↔GPU 페이징이 빈번하면 학습 속도가 크게 저하될 수 있다
- **제한된 하드웨어 지원**: bitsandbytes의 NF4 구현이 NVIDIA GPU에만 최적화되어 있다

### 발전 방향
QLoRA는 **대형 모델 파인튜닝의 민주화**에 결정적 역할을 했다. 이후 등장한 후속 연구들:
- **GGUF/GGML**: 양자화 모델의 CPU 추론 최적화
- **AWQ**(2023): 활성화 기반 양자화로 더 정밀한 4비트 양자화
- **AQLM**(2024): 다차원 양자화 코드북으로 2비트까지 압축
- **Unsloth**(2024): QLoRA 학습 속도를 커스텀 Triton 커널로 2배 향상

QLoRA는 bitsandbytes와 HuggingFace PEFT를 통해 구현되며, 현재 소비자용 GPU에서의 대형 모델 파인튜닝의 **표준 방법론**으로 자리 잡았다. 단일 RTX 3090(24GB)에서도 7B 모델을 학습할 수 있다는 접근성은 오픈소스 LLM 생태계의 폭발적 성장을 가능케 한 핵심 요인이다.

## 참고 자료

- [논문](https://arxiv.org/abs/2305.14314)
- [코드](https://github.com/artidoro/qlora)

## 관련 문서

- [[lora|LoRA: Low-Rank Adaptation of Large Language Models]] — 발전 기반
