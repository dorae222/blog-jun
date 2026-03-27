# RTX 3090에서 SLM 파인튜닝 실전 가이드

## 들어가며

:::info
이 글은 [[small-language-models|SLM]] 파인튜닝의 실전 워크플로우를 다루며, [[quantization-guide|양자화 가이드]]와 함께 읽으면 더 효과적이다.
:::

RTX 3090(24GB VRAM)은 **소비자용 GPU 중 파인튜닝에 가장 실용적인 선택**이다. LoRA/QLoRA를 활용하면 7B~13B 모델의 파인튜닝이 가능하고, Unsloth 같은 최적화 라이브러리를 사용하면 학습 속도를 2배 이상 높일 수 있다.

이 가이드에서는 RTX 3090 한 장으로 SLM을 파인튜닝하는 전체 파이프라인을 단계별로 정리한다. 모델 선정부터 데이터 준비, 학습 설정, 평가, 배포까지 하나의 워크플로우로 연결한다.

---

## RTX 3090 파인튜닝 후보 모델 비교

RTX 3090 24GB에서 파인튜닝 가능한 주요 SLM 후보를 비교한다. 모델 선택은 태스크 특성, 라이선스, 한국어 지원 여부에 따라 달라진다.

| 모델 | 파라미터 | 라이선스 | 한국어 | QLoRA VRAM | 특징 |
|------|---------|---------|:------:|-----------|------|
| [[llama-3\|LLaMA 3.1]] 8B | 8B | Meta | 제한적 | ~10 GB | 영어 최강, 넓은 생태계 |
| [[phi\|Phi-3.5]] Mini | 3.8B | MIT | 제한적 | ~6 GB | 소형 모델 대비 높은 성능 |
| Qwen2.5 7B Instruct | 7B | Apache 2.0 | 양호 | ~10 GB | 다국어, 코딩 강점 |
| Qwen2.5 3B Instruct | 3B | Apache 2.0 | 양호 | ~5 GB | 경량 실험 적합 |
| Gemma 2 9B | 9B | Google | 제한적 | ~12 GB | 고품질 사전학습 |
| Gemma 2 2B | 2B | Google | 제한적 | ~4 GB | 초경량 디바이스용 |
| EXAONE 3.5 7.8B | 7.8B | LG | 우수 | ~11 GB | 한국어 특화 |
| SOLAR 10.7B | 10.7B | Apache 2.0 | 우수 | ~13 GB | DUS 구조, 한국어 강점 |
| Mistral 7B v0.3 | 7B | Apache 2.0 | 제한적 | ~10 GB | 효율적 아키텍처 |

:::tip
**한국어 태스크 권장**: EXAONE 3.5 7.8B 또는 Qwen2.5 7B. **영어/코드 태스크 권장**: LLaMA 3.1 8B 또는 Phi-3.5 Mini. 경량 실험에는 Qwen2.5 3B부터 시작하는 것이 효율적이다.
:::

---

## 파인튜닝 방식 비교: Full vs LoRA vs QLoRA

### 세 가지 방식의 원리

- **Full Fine-tuning**: 모델의 모든 파라미터를 업데이트한다. 표현력은 최고지만 VRAM 소비가 크다.
- **LoRA (Low-Rank Adaptation)**: 기존 가중치를 동결하고, 저랭크 분해 행렬(A, B)만 학습한다. 학습 파라미터 수가 전체의 0.1~1% 수준이다.
- **QLoRA**: LoRA에 4비트 양자화를 결합한다. 베이스 모델을 4비트로 로드하고, LoRA 어댑터만 FP16/BF16으로 학습한다.

### VRAM 사용량 비교

파인튜닝 시 VRAM 사용량은 모델 가중치, 옵티마이저 상태, 그래디언트, 활성값으로 구성된다.

| 구성 요소 | Full Fine-tuning | LoRA | QLoRA |
|----------|-----------------|------|-------|
| 모델 가중치 | FP16: 2B/param | FP16: 2B/param | 4-bit: ~0.5B/param |
| 옵티마이저 상태 | 전체 파라미터 x 8B | 어댑터만 x 8B | 어댑터만 x 8B |
| 그래디언트 | 전체 파라미터 x 2B | 어댑터만 x 2B | 어댑터만 x 2B |
| 활성값 | 배치/시퀀스 비례 | 동일 | 동일 |
| **7B 모델 총량** | **~56 GB** | **~18 GB** | **~10 GB** |

### RTX 3090에서 실행 가능 조합

| 모델 크기 | Full FT | LoRA | QLoRA | 비고 |
|----------|:-------:|:----:|:-----:|------|
| 1.5~3B | O (배치 4~8) | O (배치 8~16) | O (배치 16+) | 가장 빠른 실험 |
| 7~8B | X | O (배치 2~4) | O (배치 4~8) | 최적 균형점 |
| 10~13B | X | X | O (배치 1~2) | 메모리 여유 적음 |
| 70B | X | X | X | 단일 GPU 불가 |

### 학습 속도 벤치마크

Qwen2.5 7B 기준, RTX 3090에서의 예상 학습 속도 비교이다.

| 방식 | 배치 크기 | 학습률(steps/s) | 1K 샘플 소요 시간 |
|------|---------|---------------|-----------------|
| QLoRA (PEFT) | 4 | ~1.2 steps/s | ~14분 |
| QLoRA (Unsloth) | 4 | ~2.5 steps/s | ~7분 |
| LoRA (PEFT) | 2 | ~0.8 steps/s | ~21분 |
| LoRA (Unsloth) | 2 | ~1.6 steps/s | ~10분 |

---

## VRAM 예산 산정 방법

RTX 3090의 24GB VRAM을 효율적으로 배분하려면 사전에 예산을 계산해야 한다. 7B QLoRA 기준 예산 산정 예시이다.

| 항목 | 계산식 | 예상 VRAM |
|------|--------|----------|
| 모델 가중치 (4-bit) | 7B x 0.5B | ~3.5 GB |
| LoRA 어댑터 (BF16) | 7B x 1% x 2B x 2(A,B) | ~0.3 GB |
| 옵티마이저 (AdamW) | 어댑터 x 8B | ~1.1 GB |
| 그래디언트 | 어댑터 x 2B | ~0.3 GB |
| 활성값 (seq=2048, bs=4) | 가변 | ~4~6 GB |
| CUDA 커널/오버헤드 | 고정 | ~1~2 GB |
| **합계** | | **~10~13 GB** |
| **여유 VRAM** | 24 - 13 | **~11 GB** |

여유 VRAM이 있으므로 배치 크기를 늘리거나 시퀀스 길이를 확장할 수 있다. `gradient_checkpointing=True`를 적용하면 활성값 VRAM을 30~40% 추가 절약한다.

---

## QLoRA 파인튜닝 기본 코드

### 환경 설정

```bash
pip install torch transformers peft bitsandbytes datasets trl accelerate
# Flash Attention 2 지원 시 (Ampere 이상)
pip install flash-attn --no-build-isolation
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
    r=16,
    lora_alpha=32,
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
    gradient_accumulation_steps=4,     # 유효 배치 = 4 x 4 = 16
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

---

## 핵심 하이퍼파라미터 튜닝 가이드

### LoRA 관련 파라미터

| 파라미터 | 권장 범위 | 기본 권장값 | 설명 |
|---------|---------|-----------|------|
| `r` (rank) | 8~64 | 16 | 낮으면 경량/약함, 높으면 표현력 높지만 메모리 증가 |
| `lora_alpha` | r x 1~2 | r x 2 | 실질적 학습률 스케일링 (alpha/r) |
| `target_modules` | 모델별 상이 | 전체 proj 레이어 | q,k,v,o,gate,up,down 모두 적용 권장 |
| `lora_dropout` | 0~0.1 | 0.05 | 과적합 방지, 데이터 적으면 높이기 |
| `bias` | "none" | "none" | bias 학습 여부, 대부분 none이 최적 |

### 학습 관련 파라미터

| 파라미터 | 권장 범위 | 기본 권장값 | 설명 |
|---------|---------|-----------|------|
| `learning_rate` | 5e-5 ~ 3e-4 | 2e-4 | QLoRA 표준 범위, Full FT는 1e-5~5e-5 |
| `num_train_epochs` | 1~5 | 3 | 데이터 1K 이하면 3~5, 10K 이상이면 1~2 |
| `per_device_train_batch_size` | 1~8 | 4 | VRAM에 맞춰 최대한 키우기 |
| `gradient_accumulation_steps` | 2~16 | 4 | 유효 배치 = batch_size x accumulation |
| `max_seq_length` | 512~4096 | 2048 | 길수록 VRAM 급증, 데이터 분포에 맞추기 |
| `lr_scheduler_type` | cosine/linear | cosine | cosine이 일반적으로 안정적 |
| `warmup_ratio` | 0.03~0.1 | 0.1 | 전체 스텝의 3~10%를 워밍업에 할당 |
| `gradient_checkpointing` | True/False | True | VRAM 30~40% 절약, 속도 10~20% 감소 |

---

## Unsloth로 2배 빠른 학습

[Unsloth](https://github.com/unslothai/unsloth)는 LoRA/QLoRA 학습을 최적화하는 라이브러리다. 커널 퓨전, 메모리 최적화를 통해 학습 속도 2배, VRAM 사용량 60% 감소를 달성한다.

### Unsloth 설정 코드

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

### PEFT vs Unsloth 비교

| 항목 | HuggingFace PEFT | Unsloth |
|------|-----------------|---------|
| 학습 속도 | 기준 (1x) | 2~3x |
| VRAM 사용량 | 기준 (1x) | ~0.6x |
| 지원 모델 | 거의 모든 모델 | 주요 모델만 (LLaMA, Mistral, Qwen 등) |
| API 호환성 | 기준 | HuggingFace 완전 호환 |
| Gradient Checkpointing | 표준 | 독자 최적화 (추가 VRAM 절약) |
| RoPE 최적화 | 미적용 | 커널 퓨전 적용 |

:::tip
**선택 기준**: 빠른 실험 반복이 중요하면 Unsloth를, 커스텀 모델이나 최신 아키텍처를 사용해야 하면 PEFT를 선택한다. Unsloth에서 학습 후 어댑터를 표준 PEFT 형식으로 저장하므로 배포 시 호환성 문제는 없다.
:::

---

## 데이터 준비 파이프라인

### 데이터 형식: Chat Template

대부분의 SLM은 특정 대화 형식을 기대한다. 모델별로 다른 템플릿을 사용하므로 반드시 해당 모델의 chat template을 적용해야 한다.

```python
# Qwen2.5 chat template 적용
messages = [
    {"role": "system", "content": "당신은 유용한 AI 비서입니다."},
    {"role": "user", "content": "Python에서 리스트 정렬 방법을 알려줘"},
    {"role": "assistant", "content": "Python에서 리스트를 정렬하는 방법은..."}
]

# 토큰화
text = tokenizer.apply_chat_template(messages, tokenize=False)
```

### 데이터 소스별 준비 방법

| 데이터 소스 | 형식 | 전처리 핵심 | 적합한 태스크 |
|-----------|------|-----------|-------------|
| 자체 수집 FAQ | JSON/CSV | 질문-답변 쌍 정제, 중복 제거 | 고객 응대, 도메인 QA |
| [[synthetic-data-training\|합성 데이터]] | JSON | 품질 필터링, 다양성 검증 | 범용 학습 데이터 확장 |
| ShareGPT 형식 | JSON | 대화 길이 필터링, 포맷 변환 | 대화형 모델 |
| Alpaca 형식 | JSON | instruction/input/output 매핑 | 지시 따르기 |
| [[60_lima\|LIMA]] 스타일 | JSON | 소량 고품질, 수동 검수 필수 | 정밀한 행동 조정 |

### 데이터 품질 체크리스트

- **다양성**: 같은 유형의 질문이 반복되지 않는가?
- **길이 분포**: 너무 짧거나 너무 긴 응답이 편중되지 않았는가?
- **품질**: 합성 데이터의 경우 자동 검증을 거쳤는가?
- **양**: 1K~10K 예제가 적정. LIMA 논문의 발견처럼 1K 고품질 데이터만으로도 충분한 경우가 많다.
- **형식 일치**: 학습 데이터의 chat template이 추론 시 사용할 template과 동일한가?

---

## 학습 모니터링과 조기 종료

### 학습 중 체크 포인트

학습 과정에서 다음 지표를 모니터링한다.

| 지표 | 정상 범위 | 이상 신호 | 대응 |
|------|---------|---------|------|
| Training Loss | 점진적 감소 | 감소 없음/발산 | lr 조정, 데이터 확인 |
| Eval Loss | Training Loss와 유사 | Training 대비 증가 | 과적합, 에포크 줄이기 |
| Learning Rate | 스케줄대로 변화 | N/A | 스케줄러 확인 |
| GPU VRAM | 안정 | 점진적 증가 | 메모리 누수 확인 |
| Steps/sec | 일정 | 급락 | I/O 병목, 데이터 로딩 확인 |

### Weights & Biases 연동

```python
# SFTConfig에 wandb 설정 추가
training_args = SFTConfig(
    ...
    report_to="wandb",
    run_name="qwen2.5-7b-qlora-domain",
)

# 환경변수 설정
# export WANDB_PROJECT="slm-finetuning"
# export WANDB_API_KEY="your-key"
```

---

## 학습 후 평가

### 평가 지표

파인튜닝 효과를 측정하기 위해 태스크에 맞는 평가 지표를 선택한다.

| 평가 유형 | 지표 | 도구 | 적합한 태스크 |
|----------|------|------|-------------|
| 자동 벤치마크 | MMLU, ARC, HellaSwag | lm-evaluation-harness | 범용 능력 확인 |
| 생성 품질 | BLEU, ROUGE, BERTScore | evaluate 라이브러리 | 번역, 요약 |
| 지시 따르기 | MT-Bench, AlpacaEval | FastChat | 대화형 모델 |
| 도메인 특화 | 자체 테스트셋 정확도 | 직접 구현 | 분류, QA |
| 인간 평가 | A/B 테스트, 5점 척도 | 수동 | 최종 품질 판단 |

### lm-evaluation-harness 사용 예시

```bash
# 파인튜닝 전후 벤치마크 비교
lm_eval --model hf \
    --model_args pretrained=./merged-model \
    --tasks mmlu,arc_easy,hellaswag \
    --batch_size 4
```

---

## 흔한 실수와 해결

### OOM (Out of Memory)

```
CUDA out of memory. Tried to allocate 512 MiB
```

해결 순서 (위에서부터 시도):
1. `gradient_checkpointing=True` 확인
2. `per_device_train_batch_size` 줄이기 (4 -> 2 -> 1)
3. `max_seq_length` 줄이기 (2048 -> 1024)
4. `gradient_accumulation_steps` 늘리기 (유효 배치 유지)
5. `load_in_4bit=True` 확인 (QLoRA)

### 학습 후 모델이 이상한 출력

- **과적합**: 데이터가 너무 적거나 에포크가 너무 많음. 1~3 에포크로 제한한다.
- **형식 불일치**: 학습 데이터의 chat template과 추론 시 template이 다름.
- **빈 출력**: `pad_token`이 설정되지 않음. `tokenizer.pad_token = tokenizer.eos_token`으로 설정한다.

### Loss가 줄어들지 않음

- 학습률이 너무 높거나 낮음. 1e-4로 시작한다.
- 데이터에 노이즈가 많음. 데이터 품질을 검사한다.
- 모델과 데이터의 불일치. chat template을 확인한다.

---

## 비용 비교: 클라우드 GPU vs 로컬 RTX 3090

### 비용 산정 기준

7B QLoRA, 10K 샘플, 3 에포크 기준 학습 소요 시간을 약 2시간으로 가정한다.

| 항목 | RTX 3090 (로컬) | A100 40GB (클라우드) | H100 (클라우드) |
|------|----------------|--------------------|----|
| 시간당 비용 | 전기세 ~300원 | ~$2.5/hr (~3,300원) | ~$4.0/hr (~5,300원) |
| 2시간 학습 비용 | ~600원 | ~6,600원 | ~10,600원 |
| 월 50회 학습 | ~30,000원 | ~330,000원 | ~530,000원 |
| 초기 투자 | GPU ~100만원 | 없음 | 없음 |
| 손익분기점 | ~150회 학습 | N/A | N/A |
| 데이터 프라이버시 | 완전 로컬 | 클라우드 정책 의존 | 클라우드 정책 의존 |

### 선택 가이드

| 상황 | 권장 옵션 |
|------|----------|
| 월 10회 이하 실험 | 클라우드 (RunPod, Lambda) |
| 월 30회 이상 반복 학습 | 로컬 RTX 3090 |
| 민감 데이터 학습 | 로컬 RTX 3090 (데이터 유출 방지) |
| 70B 이상 대규모 모델 | 클라우드 A100/H100 필수 |
| 빠른 프로토타이핑 | Google Colab (무료/Pro) |

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

# Ollama Modelfile 작성
cat > Modelfile << 'EOF'
FROM ./merged-model-Q4_K_M.gguf
PARAMETER temperature 0.7
PARAMETER top_p 0.9
SYSTEM "당신은 도메인 전문 AI 비서입니다."
EOF

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

### 배포 방식 비교

| 배포 방식 | 장점 | 단점 | 적합한 경우 |
|----------|------|------|-----------|
| Ollama (GGUF) | 간편한 설정, CPU 지원 | 처리량 제한 | 개인/소규모 |
| vLLM | 높은 처리량, 배칭 | GPU 전용 | 프로덕션 API |
| TGI | Docker 원스텝 배포 | 설정 복잡도 | HuggingFace 생태계 |
| [[model-merging-mergekit\|MergeKit]] 후 배포 | 모델 병합으로 성능 향상 | 추가 실험 필요 | 고급 활용 |

---

## 태스크별 모델+방식 선택 가이드

어떤 모델과 어떤 파인튜닝 방식을 선택할지에 대한 실전 가이드이다.

| 태스크 | 권장 모델 | 방식 | 데이터 규모 | 비고 |
|--------|---------|------|-----------|------|
| 한국어 QA | EXAONE 3.5 7.8B | QLoRA | 3K~10K | 한국어 사전학습 강점 |
| 영어 챗봇 | LLaMA 3.1 8B | QLoRA | 5K~20K | 생태계 넓음, 레퍼런스 풍부 |
| 코드 생성 | Qwen2.5 7B | QLoRA | 10K+ | 코드 벤치마크 상위 |
| 요약/추출 | Phi-3.5 Mini | LoRA | 1K~5K | 소형 모델로 빠른 추론 |
| 분류 태스크 | Gemma 2 2B | Full FT | 500~2K | 소형 모델이면 Full FT 가능 |
| RAG 임베딩 | Qwen2.5 3B | QLoRA | 5K~10K | 경량 실험 후 스케일업 |
| 도메인 전문가 | SOLAR 10.7B | QLoRA (배치 1) | 3K~10K | 13B 근접 성능, 한국어 |

---

## 정리

| 단계 | 핵심 포인트 |
|------|-----------|
| 모델 선택 | 7B QLoRA가 RTX 3090 최적 균형점, 한국어는 EXAONE/Qwen |
| 데이터 | 1K~10K 고품질 예제, chat template 반드시 일치 |
| 학습 설정 | lr=2e-4, rank=16, gradient checkpointing 필수 |
| 속도 최적화 | Unsloth로 2배 가속, VRAM 60% 절약 |
| 평가 | 자동 벤치마크 + 도메인 테스트셋 병행 |
| 비용 | 월 30회 이상이면 로컬 RTX 3090이 경제적 |
| 배포 | GGUF + Ollama (로컬) 또는 vLLM (프로덕션) |

RTX 3090 한 장이면 **도메인 특화 7B 모델**을 만들 수 있다. 중요한 것은 GPU 성능이 아니라 **데이터 품질과 올바른 하이퍼파라미터 선택**이다. 소규모로 시작해서(Qwen2.5 3B + 1K 데이터) 검증한 뒤, 본격적인 학습(7B + 10K 데이터)으로 확장하는 점진적 접근을 권장한다.
