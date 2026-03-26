# RTX 3090에서 SLM 파인튜닝 실전 가이드

## 들어가며

RTX 3090(24GB VRAM)은 **소비자용 GPU 중 파인튜닝에 가장 실용적인 선택**이다. LoRA/QLoRA를 활용하면 7B~13B 모델의 파인튜닝이 가능하고, Unsloth 같은 최적화 라이브러리를 사용하면 학습 속도를 2배 이상 높일 수 있다.

이 가이드는 RTX 3090 한 장으로 [[small-language-models|SLM]]을 파인튜닝하는 **실전 워크플로우**를 다룬다.

---

## VRAM 예산 산정

파인튜닝 시 VRAM 사용량의 구성:

| 구성 요소 | 풀 파인튜닝 | LoRA | QLoRA |
|----------|-----------|------|-------|
| 모델 가중치 | FP16: 2B/param | FP16: 2B/param | 4-bit: 0.5B/param |
| 옵티마이저 상태 | 전체 파라미터 × 8B | 어댑터만 × 8B | 어댑터만 × 8B |
| 그래디언트 | 전체 파라미터 × 2B | 어댑터만 × 2B | 어댑터만 × 2B |
| 활성값 | 배치/시퀀스에 비례 | 동일 | 동일 |

RTX 3090 24GB에서의 **실행 가능 조합**:

| 모델 크기 | 풀 FT | LoRA | QLoRA |
|----------|-------|------|-------|
| 3B | O (배치 4) | O (배치 8) | O (배치 16) |
| 7B | X | O (배치 2-4) | O (배치 4-8) |
| 13B | X | X | O (배치 1-2) |
| 70B | X | X | X |

:::tip
**권장 조합**: 7B 모델 + QLoRA + 배치 크기 4가 RTX 3090에서 성능/효율의 최적 균형점이다.
:::

---

## QLoRA 파인튜닝 기본 코드

### 환경 설정

```bash
pip install torch transformers peft bitsandbytes datasets trl accelerate
```

### 기본 QLoRA 학습 코드

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer, SFTConfig

# 4-bit 양자화 설정
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype="bfloat16",
    bnb_4bit_use_double_quant=True,
)

model_name = "Qwen/Qwen2.5-7B-Instruct"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map="auto",
    attn_implementation="flash_attention_2",
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# LoRA 설정
lora_config = LoraConfig(
    r=16,                    # rank — 8~64, 높을수록 표현력↑ 메모리↑
    lora_alpha=32,           # 보통 r의 2배
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = prepare_model_for_kbit_training(model)
model = get_peft_model(model, lora_config)

# 학습 설정
training_args = SFTConfig(
    output_dir="./output",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,     # 유효 배치 = 4 × 4 = 16
    learning_rate=2e-4,
    lr_scheduler_type="cosine",
    warmup_ratio=0.1,
    bf16=True,
    logging_steps=10,
    save_strategy="epoch",
    max_seq_length=2048,
    gradient_checkpointing=True,       # VRAM 절약 핵심
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
)
trainer.train()
```

### 핵심 하이퍼파라미터 가이드

| 파라미터 | 권장 값 | 설명 |
|---------|--------|------|
| `r` (rank) | 16~32 | 8이면 가볍지만 약함, 64는 무겁지만 표현력 높음 |
| `lora_alpha` | r × 2 | 학습률 스케일링 역할 |
| `learning_rate` | 1e-4 ~ 2e-4 | QLoRA에서 일반적인 범위 |
| `gradient_accumulation` | 4~8 | 작은 배치 × 큰 누적으로 유효 배치 확보 |
| `max_seq_length` | 1024~2048 | 길수록 VRAM 소비 급증 |
| `gradient_checkpointing` | True | VRAM 30~40% 절약, 속도 10~20% 감소 |

---

## Unsloth로 2배 빠르게

[Unsloth](https://github.com/unslothai/unsloth)는 LoRA/QLoRA 학습을 최적화하는 라이브러리다. 커널 퓨전, 메모리 최적화를 통해 **학습 속도 2배, VRAM 사용량 60% 감소**를 달성한다.

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/Qwen2.5-7B-Instruct",
    max_seq_length=2048,
    load_in_4bit=True,
)

model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    use_gradient_checkpointing="unsloth",  # Unsloth 전용 최적화
)
```

Unsloth의 장점:
- **메모리 최적화**: 동일 모델에서 2배 큰 배치 사용 가능
- **속도 향상**: RoPE, Cross Entropy 등 커널 퓨전으로 2~3배 빠름
- **호환성**: HuggingFace Transformers API와 완전 호환

---

## 데이터 준비

### 대화 형식 (Chat Template)

대부분의 SLM은 특정 대화 형식을 기대한다:

```python
# Qwen2.5 chat template
messages = [
    {"role": "system", "content": "당신은 유용한 AI 비서입니다."},
    {"role": "user", "content": "Python에서 리스트 정렬 방법을 알려줘"},
    {"role": "assistant", "content": "Python에서 리스트를 정렬하는 방법은..."}
]

# 토큰화
text = tokenizer.apply_chat_template(messages, tokenize=False)
```

### 데이터 품질 체크리스트

- **다양성**: 같은 유형의 질문이 반복되지 않는가?
- **길이 분포**: 너무 짧거나 너무 긴 응답이 편중되지 않았는가?
- **품질**: [[synthetic-data-training|합성 데이터]]의 경우 자동 검증을 거쳤는가?
- **양**: 일반적으로 1K~10K 예제가 적정 (LIMA의 발견 — 1K로도 충분)

---

## 흔한 실수와 해결

### 1. OOM (Out of Memory)

```
CUDA out of memory. Tried to allocate 512 MiB
```

해결 순서:
1. `gradient_checkpointing=True` 확인
2. `per_device_train_batch_size` 줄이기 (4 → 2 → 1)
3. `max_seq_length` 줄이기 (2048 → 1024)
4. `gradient_accumulation_steps` 늘리기 (유효 배치 유지)

### 2. 학습 후 모델이 이상한 출력

- **과적합**: 데이터가 너무 적거나 에포크가 너무 많음 → 1~3 에포크로 제한
- **형식 불일치**: 학습 데이터의 chat template과 추론 시 template이 다름
- **빈 출력**: `pad_token`이 설정되지 않음 → `tokenizer.pad_token = tokenizer.eos_token`

### 3. Loss가 줄어들지 않음

- 학습률이 너무 높거나 낮음 → 1e-4로 시작
- 데이터에 노이즈가 많음 → 데이터 품질 검사
- 모델과 데이터의 불일치 → chat template 확인

---

## 학습 후 배포

### LoRA 어댑터 병합

```python
# 어댑터를 기본 모델에 병합
merged_model = model.merge_and_unload()
merged_model.save_pretrained("./merged-model")
tokenizer.save_pretrained("./merged-model")
```

### GGUF 변환 (Ollama 배포용)

```bash
# llama.cpp로 GGUF 변환
python convert_hf_to_gguf.py ./merged-model --outtype q4_k_m

# Ollama에 등록
ollama create my-model -f Modelfile
```

### vLLM 서빙

```bash
python -m vllm.entrypoints.openai.api_server \
    --model ./merged-model \
    --max-model-len 2048 \
    --gpu-memory-utilization 0.9
```

---

## 정리

| 단계 | 핵심 포인트 |
|------|-----------|
| 모델 선택 | 7B QLoRA가 RTX 3090 최적 |
| 데이터 | 1K~10K 고품질 예제, chat template 일치 |
| 학습 | lr=2e-4, rank=16, gradient checkpointing 필수 |
| 속도 최적화 | Unsloth로 2배 가속 |
| 배포 | GGUF + Ollama (로컬) 또는 vLLM (서버) |

RTX 3090 한 장이면 **도메인 특화 7B 모델**을 만들 수 있다. 중요한 것은 GPU 성능이 아니라 **데이터 품질과 올바른 하이퍼파라미터 선택**이다.
