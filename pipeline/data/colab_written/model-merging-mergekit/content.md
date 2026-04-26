<!-- infographic-hero -->
![Model Merging with mergekit: Combining Multiple Models 핵심 요약](figures/infographic.svg)

*Figure: Model Merging with mergekit: Combining Multiple Models 한 장 요약 인포그래픽*

# Model Merging 실전: mergekit으로 모델 합성하기

## 들어가며

모델 A는 코딩에 강하고, 모델 B는 수학에 강하다. **두 모델의 장점을 결합한 모델 C**를 만들 수는 없을까?

**Model Merging**은 여러 모델의 가중치를 추가 학습 없이 **수학적으로 결합**하여 새로운 모델을 만드는 기법이다. 학습 비용이 들지 않고, GPU 하나로 몇 분 만에 수행할 수 있다는 점에서 매우 실용적이다. Open LLM Leaderboard 상위 모델 중 상당수가 model merging으로 만들어졌다는 사실이 이 기법의 효과를 증명한다.

이 글에서는 주요 병합 알고리즘(Linear, SLERP, TIES, DARE, Task Arithmetic, Model Stock)을 비교하고, mergekit을 사용한 실전 병합 과정을 단계별로 정리한다.

:::info
Model Merging은 [[quantization-guide|양자화]]나 [[slm-finetuning-rtx3090|파인튜닝]]과 함께 사용할 수 있는 **보완적 기법**이다. 파인튜닝으로 특화된 모델들을 만든 뒤, 병합으로 결합하는 파이프라인이 실전에서 가장 많이 활용된다.
:::

---

## Model Merging이 작동하는 이유

### Linear Mode Connectivity

같은 기본 모델에서 파인튜닝된 모델들은 **가중치 공간에서 서로 가까이** 위치한다. 이 모델들 사이의 선형 보간(linear interpolation)이 의미 있는 결과를 낳는 이유는, 파인튜닝이 기본 모델의 가중치를 **약간만** 변화시키기 때문이다.

```
기본 모델 (LLaMA-3-8B)
    |-- 파인튜닝 A: 코딩 특화 -> 가중치 W_A
    |-- 파인튜닝 B: 수학 특화 -> 가중치 W_B
    +-- 파인튜닝 C: 챗봇 특화 -> 가중치 W_C

병합: W_merged = alpha * W_A + beta * W_B + gamma * W_C
      (alpha + beta + gamma = 1)
```

### 병합의 핵심 전제 조건

| 조건 | 설명 | 위반 시 결과 |
|------|------|------------|
| 동일 기본 모델 | 같은 사전학습 모델에서 파인튜닝된 것이어야 함 | 가중치 공간이 달라 무의미한 결과 |
| 동일 아키텍처 | 레이어 수, hidden size 등이 같아야 함 | 텐서 크기 불일치로 병합 불가 |
| 동일 토크나이저 | 어휘 사전이 동일해야 함 | 토큰 매핑 불일치로 생성 품질 저하 |
| 파인튜닝 delta 크기 | 기본 모델 대비 변화량이 크지 않아야 함 | 간섭(interference) 증가 |

---

## 병합 알고리즘 비교

주요 병합 알고리즘을 한눈에 비교하면 다음과 같다.

| 알고리즘 | 병합 가능 모델 수 | 간섭 해소 | 파라미터 | 난이도 | 논문 |
|----------|:--------------:|:---------:|----------|:------:|------|
| **Linear** | 2+ | 없음 | weight | 하 | - |
| **SLERP** | 2 | 없음 | t (보간 비율) | 하 | - |
| **Task Arithmetic** | 2+ | 부분적 | scaling_coefficient | 중 | Ilharco et al., 2023 |
| **TIES** | 2+ | 다수결 부호 | density, weight | 중 | Yadav et al., 2023 |
| **DARE** | 2+ | 랜덤 드롭 | density, weight | 중 | Yu et al., 2024 |
| **Model Stock** | 2+ | 기하 평균 | - | 하 | Jang et al., 2024 |
| **Passthrough** | 2+ | 해당 없음 | layer_range | 하 | - |

---

## Linear (가중 평균)

### 원리

가장 단순한 방법. 각 모델의 가중치를 가중 평균한다.

$$W_{merged} = \alpha \cdot W_A + (1 - \alpha) \cdot W_B$$

3개 이상 모델의 경우:

$$W_{merged} = \sum_{i=1}^{N} w_i \cdot W_i, \quad \sum_{i=1}^{N} w_i = 1$$

### 장단점

| 항목 | 내용 |
|------|------|
| 장점 | 직관적, 구현 간단, N개 모델 병합 가능 |
| 단점 | 간섭 해소 없음, 3개 이상 모델에서 성능 저하 경향 |
| 적합한 경우 | 유사 도메인의 모델 2개 병합, 빠른 프로토타이핑 |

### mergekit 설정

```yaml
models:
  - model: NousResearch/Hermes-2-Pro-Llama-3-8B
    parameters:
      weight: 0.6
  - model: meta-math/MetaMath-Llama-3-8B
    parameters:
      weight: 0.4
merge_method: linear
base_model: meta-llama/Meta-Llama-3-8B
dtype: bfloat16
```

---

## SLERP (Spherical Linear Interpolation)

### 원리

가중치를 **고차원 구면 위의 점**으로 취급하고, 구면 위에서 보간한다. 단순 선형 보간보다 **가중치의 방향과 크기를 더 잘 보존**한다.

$$W_{merged} = \frac{\sin((1-t)\theta)}{\sin\theta} W_A + \frac{\sin(t\theta)}{\sin\theta} W_B$$

여기서 $\theta$는 두 가중치 벡터 사이의 각도이다. $t = 0$이면 모델 A, $t = 1$이면 모델 B가 된다.

### 장단점

| 항목 | 내용 |
|------|------|
| 장점 | 방향 보존, 크기 보존, 안정적 결과 |
| 단점 | **2개 모델만** 병합 가능, 3개 이상은 계층적 적용 필요 |
| 적합한 경우 | 2개 모델 병합의 기본 선택지, 특히 유사 도메인 |

### mergekit 설정 (레이어별 비율 적용)

```yaml
slices:
  - sources:
      - model: NousResearch/Hermes-2-Pro-Llama-3-8B
        layer_range: [0, 32]
      - model: meta-math/MetaMath-Llama-3-8B
        layer_range: [0, 32]
merge_method: slerp
base_model: meta-llama/Meta-Llama-3-8B
parameters:
  t:
    - filter: self_attn
      value: [0, 0.5, 0.3, 0.7, 1]   # 레이어별 다른 비율 (gradient)
    - filter: mlp
      value: 0.5
    - value: 0.5                       # 기본값
dtype: bfloat16
```

`t` 파라미터에 리스트를 전달하면 레이어 인덱스에 따라 선형 보간된 값이 적용된다. 예를 들어 `[0, 0.5, 0.3, 0.7, 1]`은 초반 레이어에서 모델 A를, 후반 레이어에서 모델 B를 더 많이 반영한다.

---

## Task Arithmetic

### 원리

Ilharco et al.(2023)이 제안한 방법. **파인튜닝 벡터(task vector)**를 명시적으로 다루는 접근이다.

1. 각 모델의 task vector 계산: $\tau_i = W_i - W_{base}$
2. task vector 합산: $\tau_{merged} = \sum_{i} \lambda_i \cdot \tau_i$
3. 기본 모델에 적용: $W_{merged} = W_{base} + \tau_{merged}$

핵심 발견: task vector는 **산술 연산이 가능**하다. 더하면 능력이 결합되고, 빼면 특정 능력을 제거할 수 있다(예: 유해 출력 경향 제거).

### 장단점

| 항목 | 내용 |
|------|------|
| 장점 | task vector 덧셈/뺄셈으로 능력 추가/제거, 직관적 |
| 단점 | scaling coefficient 조정 필요, 간섭 해소 미흡 |
| 적합한 경우 | 특정 능력 추가/제거, 능력 조합 실험 |

### mergekit 설정

```yaml
models:
  - model: NousResearch/Hermes-2-Pro-Llama-3-8B
    parameters:
      weight: 0.5
  - model: meta-math/MetaMath-Llama-3-8B
    parameters:
      weight: 0.3
merge_method: task_arithmetic
base_model: meta-llama/Meta-Llama-3-8B
dtype: bfloat16
```

---

## TIES (TrIm, Elect Sign & Merge)

### 원리

Yadav et al.(2023)이 제안한 방법. 단순 평균에서 발생하는 **간섭(interference) 문제**를 3단계로 해결한다.

1. **Trim**: 변화량이 작은 파라미터를 0으로 설정 (노이즈 제거, density로 제어)
2. **Elect Sign**: 각 파라미터에 대해 **다수결**로 부호 결정
3. **Merge**: 같은 부호의 값만 평균

모델 A에서 양수 방향으로 변한 파라미터가 모델 B에서 음수 방향으로 변했다면, 단순 평균은 상쇄되어 정보 손실이 발생한다. TIES는 다수결로 방향을 통일하여 이를 방지한다.

### 장단점

| 항목 | 내용 |
|------|------|
| 장점 | 간섭 해소(부호 충돌 방지), 노이즈 제거, 3개 이상 모델 병합 가능 |
| 단점 | density/weight 조정 필요, 다수결이 항상 최선은 아님 |
| 적합한 경우 | 다른 도메인 모델 2개 이상 병합, 간섭이 심한 경우 |

### mergekit 설정

```yaml
models:
  - model: NousResearch/Hermes-2-Pro-Llama-3-8B
    parameters:
      density: 0.5       # 상위 50% 파라미터만 유지
      weight: 0.5
  - model: meta-math/MetaMath-Llama-3-8B
    parameters:
      density: 0.5
      weight: 0.5
merge_method: ties
base_model: meta-llama/Meta-Llama-3-8B
parameters:
  normalize: true        # weight 합이 1이 되도록 정규화
dtype: bfloat16
```

---

## DARE (Drop And REscale)

### 원리

Yu et al.(2024)이 제안. TIES와 유사하지만, **무작위 드롭아웃**을 사용한다.

1. 각 모델의 파인튜닝 delta(원래 모델과의 차이) 계산
2. delta의 대부분을 **무작위로 0으로 설정** (드롭 확률 $p$)
3. 남은 값을 $\frac{1}{1-p}$로 **리스케일** (기대값 유지)
4. 리스케일된 delta를 TIES 또는 Linear 방식으로 병합

핵심 발견: 파인튜닝 delta의 **대부분은 중복**이므로, 90%를 제거해도 성능이 유지된다. 이를 통해 병합 시 간섭을 크게 줄일 수 있다.

### DARE 변형

| 변형 | 병합 단계 방식 | mergekit method |
|------|-------------|-----------------|
| DARE + Linear | 드롭/리스케일 후 가중 평균 | `dare_linear` |
| DARE + TIES | 드롭/리스케일 후 TIES 부호 선출 | `dare_ties` |

### mergekit 설정 (DARE-TIES, 3개 모델)

```yaml
models:
  - model: NousResearch/Hermes-2-Pro-Llama-3-8B
    parameters:
      density: 0.5       # DARE 드롭 후 남기는 비율
      weight: 0.4        # 모델 A에 40% 가중치
  - model: meta-math/MetaMath-Llama-3-8B
    parameters:
      density: 0.5
      weight: 0.3
  - model: codellama/CodeLlama-8B
    parameters:
      density: 0.5
      weight: 0.3
merge_method: dare_ties
base_model: meta-llama/Meta-Llama-3-8B
parameters:
  int_space: "cs"        # cosine similarity 기반 간섭 해소
  normalize: true
dtype: bfloat16
```

---

## Model Stock

### 원리

Jang et al.(2024)이 제안한 최신 방법. 파인튜닝된 모델들의 가중치를 **기하학적으로 분석**하여, 최적의 병합 지점을 자동으로 결정한다.

기존 방법들이 weight, density 등 하이퍼파라미터를 수동으로 조정해야 하는 반면, Model Stock은 **파라미터 없이** 자동으로 최적 병합 비율을 결정한다.

### 장단점

| 항목 | 내용 |
|------|------|
| 장점 | 하이퍼파라미터 튜닝 불필요, 이론적 근거 강함 |
| 단점 | 비교적 새로운 방법, DARE-TIES 대비 사례 적음 |
| 적합한 경우 | 빠른 프로토타이핑, 하이퍼파라미터 탐색 비용을 줄이고 싶을 때 |

### mergekit 설정

```yaml
models:
  - model: NousResearch/Hermes-2-Pro-Llama-3-8B
  - model: meta-math/MetaMath-Llama-3-8B
  - model: codellama/CodeLlama-8B
merge_method: model_stock
base_model: meta-llama/Meta-Llama-3-8B
dtype: bfloat16
```

---

## Passthrough (Frankenmerging)

### 원리

모델의 **다른 레이어를 다른 소스에서** 가져오는 방법. 알고리즘적 병합이 아니라, 레이어를 물리적으로 조합한다.

```yaml
slices:
  - sources:
      - model: model_A
        layer_range: [0, 16]     # 하위 레이어는 모델 A (일반 지식)
  - sources:
      - model: model_B
        layer_range: [16, 32]    # 상위 레이어는 모델 B (특화 지식)
merge_method: passthrough
dtype: bfloat16
```

이 방법은 이론적 근거가 약하지만, 실험적으로 흥미로운 결과를 내기도 한다. 특히 하위 레이어(일반적 표현 학습)와 상위 레이어(과제 특화 표현)의 역할이 다르다는 점을 활용한다.

---

## 알고리즘 선택 플로우

병합 상황에 따른 알고리즘 선택 가이드:

| 상황 | 권장 방법 | 이유 |
|------|----------|------|
| 2개 모델, 유사 도메인 | SLERP | 방향 보존, 안정적 |
| 2개 모델, 다른 도메인 | TIES | 간섭 해소 |
| 3개 이상 모델 | DARE-TIES | 다중 병합에 강건 |
| 하이퍼파라미터 튜닝 없이 빠르게 | Model Stock | 자동 최적화 |
| 특정 능력 추가/제거 | Task Arithmetic | task vector 연산 |
| 실험적 시도 | Passthrough | 비용 0, 의외의 결과 가능 |
| 첫 시도, 잘 모르겠을 때 | DARE-TIES | 가장 범용적 |

---

## mergekit 실전 가이드

### 설치 및 환경 설정

```bash
# 기본 설치
pip install mergekit

# CUDA 지원 설치 (GPU 가속)
pip install mergekit[cuda]

# 소스에서 설치 (최신 기능)
git clone https://github.com/arcee-ai/mergekit.git
cd mergekit && pip install -e .
```

### 병합 실행

```bash
# 기본 실행 (CPU)
mergekit-yaml config.yaml ./merged-model

# GPU 가속 (권장)
mergekit-yaml config.yaml ./merged-model --cuda --lazy-unpickle

# 메모리 부족 시: lazy-unpickle 단독 사용
mergekit-yaml config.yaml ./merged-model --lazy-unpickle

# 기존 출력 덮어쓰기
mergekit-yaml config.yaml ./merged-model --cuda --lazy-unpickle --allow-crimes
```

:::warning
`--cuda` 옵션은 병합 속도를 크게 높이지만, GPU 메모리를 사용한다. 7B 모델 병합 시 약 **16GB VRAM**이 필요하고, 13B는 약 **28GB**가 필요하다. VRAM이 부족하면 `--lazy-unpickle`만 사용하여 CPU에서 병합하는 것이 안전하다.
:::

---

## 메모리 및 컴퓨팅 요구사항

### 모델 크기별 병합 리소스

| 모델 크기 | RAM (CPU 병합) | VRAM (GPU 병합) | 디스크 공간 | 소요 시간 (GPU) |
|----------|:-------------:|:--------------:|:----------:|:--------------:|
| 1.3B | 8 GB | 6 GB | ~10 GB | ~1분 |
| 7B | 32 GB | 16 GB | ~28 GB | ~3분 |
| 13B | 64 GB | 28 GB | ~52 GB | ~8분 |
| 34B | 128 GB | 48 GB+ | ~136 GB | ~20분 |
| 70B | 256 GB | 80 GB+ | ~280 GB | ~45분 |

### 디스크 공간 계산

병합 시 필요한 디스크 공간 = (입력 모델 수 + 1) x 모델 크기. 예를 들어 7B 모델 3개를 병합하면:

- 입력 모델: 14 GB x 3 = 42 GB
- 출력 모델: 14 GB x 1 = 14 GB
- **합계: ~56 GB**

---

## 레이어별 병합 전략

### 레이어 역할에 따른 차별적 병합

Transformer 모델의 레이어는 위치에 따라 역할이 다르다. 이를 활용하면 더 정교한 병합이 가능하다.

| 레이어 위치 | 역할 | 병합 전략 |
|-----------|------|----------|
| 하위 (0~25%) | 토큰 임베딩, 기본 문법 | 기본 모델 비율 높게 (일반성 유지) |
| 중간 (25~75%) | 의미 표현, 추론 | 특화 모델 비율 높게 (능력 획득) |
| 상위 (75~100%) | 과제 특화 출력 | 목표에 따라 조정 |

### SLERP 레이어별 비율 예시

```yaml
slices:
  - sources:
      - model: model_A  # 코딩 특화
        layer_range: [0, 32]
      - model: model_B  # 수학 특화
        layer_range: [0, 32]
merge_method: slerp
base_model: meta-llama/Meta-Llama-3-8B
parameters:
  t:
    # 하위 레이어: model_A 위주 (t=0.3)
    # 중간 레이어: 균등 (t=0.5)
    # 상위 레이어: model_B 위주 (t=0.7)
    - filter: self_attn
      value: [0.3, 0.3, 0.4, 0.5, 0.5, 0.6, 0.7, 0.7]
    - filter: mlp
      value: [0.3, 0.3, 0.4, 0.5, 0.5, 0.6, 0.7, 0.7]
    - value: 0.5
dtype: bfloat16
```

---

## Open LLM Leaderboard 사례 분석

Model Merging이 실전에서 효과적이라는 증거는 Open LLM Leaderboard에서 확인할 수 있다. 상위권 모델 중 상당수가 병합 모델이다.

### 대표적 병합 모델 성과

| 모델 | 병합 방법 | 소스 모델 | 특징 |
|------|----------|----------|------|
| MergeMonster | DARE-TIES | 5개 특화 모델 | 다중 벤치마크 균형 |
| NeuralBeagle14 | SLERP + DARE | Mistral 기반 2개 | 코딩+대화 균형 |
| Goliath-120B | Passthrough | 2 x LLaMA-65B | 레이어 스택으로 크기 확장 |
| SOLAR-10.7B | Passthrough (DUS) | Mistral-7B | Depth Up-Scaling: 레이어 복제 후 학습 |

### 병합 모델이 강한 벤치마크

| 벤치마크 | 측정 능력 | 병합이 효과적인 이유 |
|----------|----------|-------------------|
| MMLU | 다분야 지식 | 여러 도메인 모델 결합으로 커버리지 확장 |
| ARC | 과학 추론 | 추론 능력 특화 모델 병합 |
| HellaSwag | 상식 추론 | 기본 모델의 상식 + 특화 모델의 정밀도 |
| GSM8K | 수학 | 수학 특화 모델의 능력 전이 |
| TruthfulQA | 진실성 | 특정 모델의 truthfulness 능력 병합 |

---

## 병합 결과 평가

### 평가 도구

병합된 모델의 품질을 객관적으로 측정하려면 벤치마크 평가가 필수적이다.

```bash
# lm-evaluation-harness로 벤치마크 실행
pip install lm-eval

# MMLU 평가 (5-shot)
lm_eval --model hf \
    --model_args pretrained=./merged-model \
    --tasks mmlu \
    --num_fewshot 5 \
    --batch_size auto

# 종합 평가 (MMLU + ARC + HellaSwag + GSM8K)
lm_eval --model hf \
    --model_args pretrained=./merged-model \
    --tasks mmlu,arc_challenge,hellaswag,gsm8k \
    --batch_size auto \
    --output_path ./eval_results
```

### 평가 체크리스트

| 평가 항목 | 방법 | 통과 기준 |
|----------|------|----------|
| 벤치마크 점수 | lm-evaluation-harness | 소스 모델 평균 이상 |
| 생성 품질 | 수동 프롬프트 테스트 | 자연스러운 응답, 할루시네이션 없음 |
| 도메인 성능 | 도메인별 프롬프트 세트 | 목표 도메인에서 소스 모델과 유사하거나 우수 |
| 안전성 | TruthfulQA, toxicity 벤치마크 | 기본 모델 대비 저하 없음 |
| Chat template | 대화형 프롬프트 | 형식 준수, 종료 토큰 정상 |

---

## 병합 시 주의사항

### 흔한 실수와 해결

| 문제 | 원인 | 해결 |
|------|------|------|
| 병합 후 의미 없는 출력 | 다른 기본 모델 사용 | 동일 기본 모델 확인 |
| 특정 능력만 사라짐 | 간섭으로 task vector 상쇄 | TIES/DARE로 간섭 해소 |
| Chat 형식 깨짐 | 다른 chat template 모델 병합 | 같은 template 모델 사용 |
| 메모리 부족 (OOM) | GPU VRAM 부족 | --lazy-unpickle (CPU 병합) 사용 |
| 성능이 소스 모델보다 낮음 | weight/density 부적절 | 하이퍼파라미터 그리드 서치 |

### 하이퍼파라미터 튜닝 가이드

| 파라미터 | 범위 | 시작값 | 조정 방향 |
|----------|------|-------|----------|
| weight | 0.0~1.0 | 균등 분배 | 중요 모델에 높은 weight |
| density (TIES) | 0.1~1.0 | 0.5 | 낮을수록 공격적 정리 |
| density (DARE) | 0.1~0.9 | 0.5 | 낮을수록 많은 파라미터 드롭 |
| t (SLERP) | 0.0~1.0 | 0.5 | 목표 모델 방향으로 이동 |
| normalize | true/false | true | weight 합이 1이 되도록 |

---

## 한계와 대안

### Model Merging의 한계

**능력의 단순 합산이 아니다.** 모델 A의 코딩 능력 + 모델 B의 수학 능력 = 코딩+수학 모두 강한 모델이 항상 성립하지는 않는다. 병합은 **최선의 경우 두 능력의 절충**이고, 최악의 경우 **두 능력 모두 저하**된다.

**이론적 이해가 부족하다.** 왜 특정 병합이 잘 작동하고 다른 것은 실패하는지에 대한 이론적 이해가 아직 부족하다. 현재는 주로 실험적 탐색에 의존한다.

**대형 모델에서 불안정하다.** 70B+ 모델에서의 병합은 7B보다 불안정한 경향이 있다. 파라미터가 많을수록 간섭의 양도 증가하기 때문이다.

### 대안 기법 비교

| 기법 | 추가 학습 | GPU 요구 | 결과 품질 | 적합한 경우 |
|------|:---------:|:--------:|:---------:|-----------|
| Model Merging | 불필요 | 낮음 | 중간 | 빠른 프로토타이핑, 리소스 제한 |
| LoRA 병합 | 불필요 | 낮음 | 중간 | LoRA 어댑터 결합 |
| [[slm-finetuning-rtx3090|파인튜닝]] | 필요 | 높음 | 높음 | 정밀한 능력 부여 |
| Knowledge Distillation | 필요 | 높음 | 높음 | 소형 모델 생성 |
| MoE 변환 | 필요 | 높음 | 높음 | 전문가 혼합 구조 |

---

## 실전 워크플로우 정리

실전에서 Model Merging을 적용하는 전체 과정은 다음과 같다.

**1단계: 소스 모델 선정**
- 같은 기본 모델([[llama-3|LLaMA 3]], [[phi|Phi]] 등)에서 파인튜닝된 모델 선택
- HuggingFace에서 목적에 맞는 특화 모델 검색
- 토크나이저 호환성 확인

**2단계: 병합 방법 선택**
- 2개 모델 + 유사 도메인: SLERP
- 3개 이상 또는 다른 도메인: DARE-TIES
- 튜닝 없이 빠르게: Model Stock

**3단계: 설정 파일 작성 및 병합 실행**
- mergekit YAML 설정 파일 작성
- `mergekit-yaml` 명령으로 병합 실행
- GPU 사용 가능 시 `--cuda` 옵션 활용

**4단계: 평가 및 반복**
- lm-evaluation-harness로 벤치마크 실행
- 수동 프롬프트 테스트
- 결과 불만족 시 하이퍼파라미터 조정 후 재병합

**5단계: 배포**
- [[quantization-guide|양자화]] 적용 (GGUF, AWQ, GPTQ)
- HuggingFace Hub 업로드 또는 로컬 배포

---

## 정리

Model Merging은 **추가 학습 없이 여러 모델의 장점을 결합**하는 효율적인 방법이다. GPU 하나로 몇 분 만에 수행할 수 있으며, Open LLM Leaderboard에서 그 효과가 검증되었다.

| 핵심 포인트 | 내용 |
|-----------|------|
| 전제 조건 | 동일 기본 모델 + 동일 아키텍처 + 동일 토크나이저 |
| 가장 범용적 | DARE-TIES (3개 이상 모델, 간섭 해소) |
| 가장 안정적 | SLERP (2개 모델, 유사 도메인) |
| 가장 간편 | Model Stock (하이퍼파라미터 자동 결정) |
| 표준 도구 | mergekit (`mergekit-yaml config.yaml ./output --cuda`) |
| 필수 평가 | lm-evaluation-harness로 벤치마크 + 수동 프롬프트 테스트 |

실전에서는 mergekit + DARE-TIES 조합이 가장 범용적이며, **데이터나 학습 없이 모델 성능을 개선**할 수 있는 유일한 방법이라는 점에서 [[slm-finetuning-rtx3090|파인튜닝]]의 보완재로서 가치가 있다.
