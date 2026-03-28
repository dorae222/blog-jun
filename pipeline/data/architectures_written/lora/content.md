# LoRA: 저랭크 적응을 통한 대형 언어 모델 파인튜닝

**Microsoft** · **2021-10-16** · **오픈소스**

## 개요

LoRA(Low-Rank Adaptation)는 Edward Hu 등이 2021년 Microsoft Research에서 제안한 **파라미터 효율적 파인튜닝(PEFT)** 기법이다. GPT-3(175B) 규모의 대형 언어 모델을 파인튜닝하려면 모든 파라미터를 업데이트해야 하므로 막대한 GPU 메모리와 저장 공간이 필요하다. 각 다운스트림 태스크마다 175B 파라미터 전체의 복사본을 유지해야 하는 것은 비현실적이다.

LoRA는 이 문제를 **저랭크 분해(Low-Rank Decomposition)**로 해결한다. 사전 학습된 가중치를 동결한 채로 각 Transformer 레이어에 작은 저랭크 행렬 쌍을 삽입하여, GPT-3 기준 학습 파라미터를 **최대 10,000배** 줄이면서도 전체 파인튜닝과 동등하거나 더 나은 성능을 달성한다. 추론 시에는 어댑터 가중치를 원본에 병합할 수 있어 **추론 지연이 전혀 발생하지 않는다**.

![LoRA 아키텍처 — 사전 학습 가중치를 동결한 채 저랭크 행렬 쌍을 삽입하는 파라미터 효율적 파인튜닝 구조](figures/architecture.svg)

*Figure 1: LoRA 아키텍처 — 각 Transformer 레이어에 저랭크 행렬 A와 B를 병렬로 삽입하여, 학습 파라미터를 최대 10,000배 줄이면서 추론 시 지연 없이 원본 가중치에 병합 가능한 구조이다.*

## 기법 상세

### 핵심 수학 원리

아래 그림은 LoRA의 재파라미터화 방식을 시각적으로 보여준다. 사전 학습된 가중치 W는 동결하고, 저랭크 행렬 A와 B만 학습한다.

![LoRA 재파라미터화 구조 — 동결된 사전 학습 가중치 W와 저랭크 행렬 A, B의 병렬 구조](figures/fig_1.png)
*Figure 1: LoRA 재파라미터화 — 사전 학습된 가중치 W는 동결하고, 저랭크 행렬 A(가우시안 초기화)와 B(0 초기화)만 학습한다. (Source: Hu et al., 2021)*

사전 학습된 가중치 행렬 W₀ ∈ R^{d×k}가 있을 때, 파인튜닝은 이 가중치를 W₀ + ΔW로 업데이트한다. LoRA의 핵심 가설은 **가중치 변화량 ΔW가 낮은 내재 랭크(intrinsic rank)를 가진다**는 것이다.

```
ΔW = BA,  B ∈ R^{d×r},  A ∈ R^{r×k},  r ≪ min(d, k)
```

순전파 시 출력은 다음과 같이 계산된다:

```
h = W₀x + (α/r) · BAx
```

여기서:
- W₀: 사전 학습 가중치 (동결, gradient 비활성화)
- B: **0으로 초기화** → 학습 초기에 ΔW = BA = 0
- A: **가우시안 랜덤 초기화**
- α: 스케일링 하이퍼파라미터
- r: 랭크 (일반적으로 4, 8, 16, 32)

α/r 스케일링은 중요한 설계 결정이다. 랭크 r을 변경할 때 학습률을 다시 튜닝할 필요 없이, 동일한 α 값으로 안정적인 학습이 가능하다.

### 적용 위치

LoRA는 Transformer의 어떤 가중치 행렬에든 적용할 수 있지만, 논문에서는 **어텐션 행렬(Wq, Wk, Wv, Wo)**에 적용하는 것이 가장 효과적임을 실험적으로 보였다.

| 적용 위치 | 파라미터 수 (r=4, d=768) | 효과 |
|----------|----------------------|------|
| Wq만 | 768 × 4 × 2 = 6,144 | 보통 |
| Wq + Wv | 12,288 | 최적 (논문 권장) |
| Wq + Wk + Wv + Wo | 24,576 | 약간 더 좋음 |
| 모든 선형 레이어 | ~49,152 | 최대 유연성 |

실험 결과, Wq와 Wv에만 랭크 4로 적용해도 전체 파인튜닝의 **97~100%** 성능을 달성한다.

### 파라미터 효율성

GPT-3 175B 기준:

| 방법 | 학습 파라미터 | 비율 | GPU 메모리 |
|------|-------------|------|------------|
| 전체 파인튜닝 | 175B | 100% | ~780GB |
| Adapter (r=64) | 40M | 0.023% | ~350GB |
| Prefix Tuning | 20M | 0.011% | ~350GB |
| **LoRA (r=4)** | **4.7M** | **0.0027%** | **~250GB** |

학습 파라미터가 0.01% 미만이면서, 옵티마이저 상태(Adam의 momentum, variance)도 LoRA 파라미터에 대해서만 유지하면 되므로 **GPU 메모리 사용량이 약 1/3로 감소**한다.

### 랭크 선택 가이드

| 랭크 (r) | 파라미터 수 (d=4096) | 적합한 상황 |
|----------|-------------------|------------|
| 4 | 32,768 | 간단한 분류, 유사 도메인 |
| 8 | 65,536 | 일반적인 파인튜닝 (권장) |
| 16 | 131,072 | 도메인 간 전이, 복잡한 태스크 |
| 32 | 262,144 | 대규모 데이터, 높은 표현력 필요 |
| 64+ | 524,288+ | 전체 파인튜닝에 근접 |

놀랍게도 랭크 4만으로도 대부분의 태스크에서 충분한 성능을 보이며, 이는 **사전 학습된 모델의 가중치 변화가 본질적으로 저차원**임을 시사한다.

다음 히트맵은 서로 다른 랭크(r=8, r=64)의 LoRA 행렬 A 열 벡터 간 부분공간 유사도를 분석한 결과로, 낮은 랭크에서도 핵심 방향이 충분히 포착됨을 보여준다.

![랭크별 부분공간 유사도 분석 — r=8과 r=64 간 ΔWq, ΔWv 열 벡터 비교](figures/fig_3.png)
*Figure 3: 랭크별 부분공간 유사도 — r=8의 상위 방향이 r=64에도 포함되어 있어, 낮은 랭크로도 핵심 적응 방향을 효과적으로 포착할 수 있음을 입증한다. (Source: Hu et al., 2021)*

## 핵심 혁신

| 혁신 | 설명 |
|------|------|
| 저랭크 분해 | ΔW = BA로 가중치 변화를 근사 |
| 제로 초기화 | B=0으로 시작하여 학습 초기 안정성 보장 |
| 추론 병합 | W = W₀ + (α/r)BA로 추론 시 추가 비용 없음 |
| α/r 스케일링 | 랭크 변경 시 학습률 재튜닝 불필요 |
| 모듈식 어댑터 | 태스크별 LoRA 어댑터 교체 가능 |

추론 시 병합의 장점은 매우 크다. Adapter, Prefix Tuning 등 다른 PEFT 기법은 추론 시 추가 레이어나 토큰을 거쳐야 하므로 지연이 발생하지만, LoRA는 가중치를 미리 합산하면 **원본 모델과 동일한 추론 속도**를 유지한다.

## 벤치마크/성능

### RoBERTa-large (355M) 결과

| 방법 | MNLI | SST-2 | MRPC | CoLA | 학습 파라미터 |
|------|------|-------|------|------|-------------|
| Full FT | 90.2 | 96.4 | 90.9 | 68.0 | 355M |
| Adapter | 90.3 | 96.1 | 89.7 | 67.8 | 3.6M |
| **LoRA (r=8)** | **90.6** | **96.2** | **90.5** | **68.2** | **0.8M** |

### GPT-3 175B 결과

| 방법 | WikiSQL | MNLI-m | SAMSum | 학습 파라미터 |
|------|---------|--------|--------|-------------|
| Full FT | 73.8 | 89.5 | 52.0 | 175B |
| Adapter | 73.2 | 89.1 | 53.2 | 40M |
| **LoRA (r=4)** | **73.4** | **91.7** | **53.8** | **4.7M** |

LoRA는 학습 파라미터가 수만 배 적으면서도 전체 파인튜닝과 동등하거나 **더 나은 성능**을 보인다.

아래 그래프는 GPT-3 175B에서 학습 가능한 파라미터 수 대비 성능을 비교한 것으로, LoRA가 다른 적응 기법보다 우수한 확장성과 태스크 성능을 보여준다.

![GPT-3 175B 검증 정확도 vs 학습 가능 파라미터 수 — 다양한 적응 기법 비교](figures/fig_2.png)
*Figure 2: GPT-3 175B 성능 비교 — WikiSQL과 MNLI-matched에서 학습 가능 파라미터 수 대비 검증 정확도. LoRA가 적은 파라미터로 더 높은 성능을 달성한다. (Source: Hu et al., 2021)*

## 관련 기법 비교

| 기법 | 추론 지연 | 파라미터 효율 | 학습 안정성 | 멀티태스크 |
|------|----------|-------------|-----------|------------|
| Full Fine-tuning | 없음 | 낮음 | 높음 | 불가 |
| Adapter | 있음 | 중간 | 높음 | 가능 |
| Prefix Tuning | 있음 | 높음 | 중간 | 가능 |
| **LoRA** | **없음** | **매우 높음** | **높음** | **가능** |
| Prompt Tuning | 있음 | 매우 높음 | 낮음 | 가능 |

LoRA만이 **추론 지연 없이** 높은 파라미터 효율성과 학습 안정성을 동시에 제공한다.

다음 히트맵은 Adapter 기반 방식의 추론 지연 비율을 배치 크기와 시퀀스 길이에 따라 측정한 결과다. 짧은 시퀀스와 작은 배치에서 Adapter의 지연이 30% 이상에 달하는 반면, LoRA는 가중치 병합으로 이러한 지연이 완전히 제거된다.

![Adapter 추론 지연 히트맵 — 배치 크기 및 시퀀스 길이별 지연 비율](figures/fig_5.png)
*Figure 5: Adapter 추론 지연 분석 — 배치 크기와 시퀀스 길이에 따른 Adapter의 추론 지연 비율. 온라인 환경에서 최대 30% 이상의 지연이 발생하며, LoRA의 병합 방식이 이를 완전히 해결한다. (Source: Hu et al., 2021)*

## 실무 활용

### HuggingFace PEFT 라이브러리 (권장)

```python
from peft import LoraConfig, get_peft_model, TaskType
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer

# 1. 베이스 모델 로드
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    torch_dtype=torch.float16,
    device_map="auto"
)

# 2. LoRA 설정
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=8,                          # 랭크
    lora_alpha=16,                # 스케일링 α (보통 r의 2배)
    lora_dropout=0.05,            # 드롭아웃
    target_modules=[              # 적용할 모듈
        "q_proj", "v_proj",       # 기본: query + value
        # "k_proj", "o_proj",     # 선택: key + output
        # "gate_proj", "up_proj", "down_proj"  # MLP에도 적용 가능
    ],
    bias="none",                  # bias는 학습하지 않음
)

# 3. LoRA 어댑터 적용
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# 출력: trainable params: 4,194,304 || all params: 6,742,609,920 || trainable%: 0.0622%

# 4. 학습
trainer = Trainer(
    model=model,
    train_dataset=train_dataset,
    args=TrainingArguments(
        output_dir="./lora-llama2",
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        learning_rate=2e-4,        # LoRA는 보통 1e-4 ~ 3e-4
        num_train_epochs=3,
        fp16=True,
    ),
)
trainer.train()

# 5. 어댑터 저장 (수 MB만 저장)
model.save_pretrained("./lora-adapter")
```

### 추론 시 어댑터 병합

```python
from peft import PeftModel

# 베이스 모델 + LoRA 어댑터 로드
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")
model = PeftModel.from_pretrained(base_model, "./lora-adapter")

# 가중치 병합: W = W0 + (α/r) * BA
merged_model = model.merge_and_unload()

# 병합된 모델은 원본과 동일한 구조 → 추론 지연 없음
merged_model.save_pretrained("./merged-llama2")
```

### 멀티 어댑터 전환

```python
from peft import PeftModel

model = PeftModel.from_pretrained(base_model, "./adapter-korean")
model.load_adapter("./adapter-code", adapter_name="code")
model.load_adapter("./adapter-medical", adapter_name="medical")

# 태스크에 따라 어댑터 전환 (모델 리로드 불필요)
model.set_adapter("code")       # 코드 생성 모드
model.set_adapter("medical")    # 의료 질의응답 모드
model.set_adapter("default")    # 한국어 모드
```

## 한계 및 전망

### 현재 한계
- **랭크 제한**: 저랭크 근사이므로 가중치 변화가 고랭크인 태스크에서는 성능 저하 가능
- **적용 위치 선택**: 어떤 모듈에 LoRA를 적용할지 수동으로 결정해야 하며, 최적 조합은 모델과 태스크에 따라 다름
- **단일 태스크 학습**: 원본 LoRA는 태스크당 하나의 어댑터를 학습하며, 태스크 간 지식 공유가 제한적
- **연속 학습 한계**: 순차적 태스크 학습 시 이전 어댑터의 지식이 손실될 수 있음

### 발전 방향
LoRA는 현재 파인튜닝 생태계의 근간을 이루며 수많은 후속 연구를 낳았다:
- **QLoRA**(2023): 4비트 양자화와 결합하여 메모리를 더욱 절감
- **DoRA**(2024): 가중치를 크기(magnitude)와 방향(direction)으로 분리하여 LoRA의 표현력 향상
- **LoRA+**(2024): A와 B에 서로 다른 학습률을 적용하여 수렴 속도 개선
- **AdaLoRA**(2023): 중요한 레이어에 더 높은 랭크를 자동 할당

LoRA는 HuggingFace PEFT 라이브러리에 기본 내장되어 현재 LLM 파인튜닝의 **사실상 표준**으로 사용되고 있다.

## 참고 자료

- [논문](https://arxiv.org/abs/2106.09685)
- [코드](https://github.com/microsoft/LoRA)

## 관련 문서

- [[qlora|QLoRA: Efficient Finetuning of Quantized LLMs]] — 후속 모델
