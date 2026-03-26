# Textbooks Are All You Need: 교과서 품질 데이터의 힘

## 논문 개요

:::info
**Paper:** Textbooks Are All You Need (arXiv:2306.11644, 2023.06)
**저자:** Suriya Gunasekar, Yi Zhang, Jyoti Aneja et al.
**소속:** Microsoft Research
**모델:** [HuggingFace: microsoft/phi-1](https://huggingface.co/microsoft/phi-1)
:::

2023년 6월, Microsoft Research는 AI 커뮤니티의 상식을 뒤집는 논문을 발표했다. **1.3B 파라미터의 Phi-1**이 HumanEval에서 **51%**를 달성한 것이다. 이는 당시 15B 규모의 StarCoder(33.6%)를 크게 능가하고, GPT-3.5(47%)에도 근접하는 수치였다.

비결은 모델의 크기가 아니라 **데이터의 품질**이었다. 논문의 제목 그대로, "교과서만 있으면 된다(Textbooks Are All You Need)."

---

## 핵심 아이디어: 데이터 품질 > 데이터 양

### 기존 접근법의 문제

대형 코드 생성 모델(StarCoder, CodeLlama 등)은 GitHub에서 수집한 **수천억 토큰**의 코드로 학습한다. 그러나 이 데이터의 대부분은:

- 반복적이고 관용적인 보일러플레이트 코드
- 문서화가 없거나 부족한 코드
- 잘못된 패턴이나 안티패턴을 포함하는 코드

이런 데이터로 학습한 모델은 **흔한 패턴을 암기**하는 데는 능하지만, **새로운 문제를 논리적으로 해결**하는 능력이 제한적이다.

### 교과서 품질 데이터

Phi-1의 학습 데이터는 두 가지로 구성된다:

1. **CodeTextbook** (~6B 토큰): GPT-3.5를 사용하여 생성한 **교과서 스타일의 합성 데이터**
   - 개념 설명이 포함된 코드
   - 점진적으로 복잡해지는 예제
   - 명확한 변수명과 주석

2. **CodeExercises** (~180M 토큰): GPT-3.5가 생성한 **연습 문제와 풀이**
   - 함수 서명 + docstring → 풀이 형태
   - HumanEval과 유사한 형식

합쳐서 약 **7B 토큰** — StarCoder의 학습 데이터(783B 토큰)의 **1/100** 수준이다.

---

## 실험 결과

![HumanEval에서의 데이터 품질 효과](figures/p03_fig01.png)

*Figure 1: 데이터 품질이 모델 성능에 미치는 영향. 같은 모델 크기(350M)에서 The Stack 데이터(11%) vs CodeTextbook(16%) vs CodeTextbook+CodeExercises(41%). 데이터 품질만으로 4배의 성능 차이가 발생한다. (Gunasekar et al., 2023)*

### 핵심 발견

| 모델 | 파라미터 | 학습 데이터 | HumanEval |
|------|---------|-----------|-----------|
| StarCoder | 15.5B | 783B tokens (The Stack) | 33.6% |
| CodeGen-Multi | 16.1B | 577B tokens | 18.3% |
| **Phi-1-small** | **350M** | 7B tokens (합성) | **45%** |
| **Phi-1** | **1.3B** | 7B tokens (합성) | **51%** |

350M 파라미터의 Phi-1-small이 15B의 StarCoder를 능가한다. 이는 **모델 크기를 40배 줄이고도 더 높은 성능을 달성**할 수 있음을 의미한다.

### 데이터 품질의 영향 (Ablation)

같은 350M 모델 + 같은 학습 시간에서 데이터만 변경한 결과:

- **The Stack** (일반 코드): HumanEval 11%
- **CodeTextbook** (합성 교과서): HumanEval 16%
- **CodeTextbook → CodeExercises** (교과서 + 연습): HumanEval **41%**

같은 모델, 같은 연산이지만 데이터 품질만으로 **4배의 성능 차이**가 발생한다.

---

## 무엇이 "교과서 품질"인가

논문은 교과서 품질의 데이터가 가져야 할 특성을 다음과 같이 정의한다:

### 1. 자기 완결적 (Self-contained)

각 예제가 외부 컨텍스트 없이 **그 자체로 이해 가능**해야 한다. GitHub 코드는 다른 파일, 라이브러리, 프로젝트 구조에 의존하지만, 교과서 코드는 독립적이다.

### 2. 교육적 (Instructive)

코드가 **왜 이렇게 작성되었는지** 설명이 포함되어야 한다. 단순히 "작동하는 코드"가 아니라 "배울 수 있는 코드"다.

### 3. 균형적 (Balanced)

쉬운 개념부터 어려운 개념까지 **점진적으로** 다뤄야 한다. 일반 코드 데이터셋은 간단한 CRUD가 대부분이고, 알고리즘적 사고가 필요한 코드는 극소수다.

---

## Phi 시리즈의 발전

Phi-1의 성공은 Microsoft의 Phi 시리즈로 이어졌다:

| 모델 | 크기 | 연도 | 핵심 발전 |
|------|------|------|----------|
| Phi-1 | 1.3B | 2023.06 | 코드 생성 특화, 교과서 품질 증명 |
| Phi-1.5 | 1.3B | 2023.09 | 코드 → 일반 추론으로 확장 |
| Phi-2 | 2.7B | 2023.12 | 합성+웹 데이터 혼합, MMLU 56.3% |
| Phi-3-mini | 3.8B | 2024.04 | 128K 컨텍스트, Mixtral 8x7B 대항 |
| Phi-4 | 14B | 2024.12 | 합성 데이터 고도화, 추론 강화 |

일관된 철학: **"더 좋은 데이터로 더 작은 모델을."** 이 철학은 [[small-language-models|SLM]] 트렌드 전체의 이론적 기반이 되었다.

---

## 시사점과 영향

### 1. Scaling Law에 대한 재고

Chinchilla의 scaling law는 "모델 크기와 데이터 양의 균형"을 다뤘지만, **데이터 품질**은 고려하지 않았다. Phi-1은 scaling law의 숨겨진 차원 — 데이터 품질 — 을 드러냈다.

### 2. 합성 데이터 패러다임의 시작

Phi-1은 [[synthetic-data-training|합성 데이터]]를 LLM 학습의 핵심 전략으로 확립한 최초의 대규모 실증이다. 이후 [[openthoughts3-dataset|OpenThoughts3]], Cosmopedia, Magpie 등 합성 데이터셋이 폭발적으로 증가했다.

### 3. SLM의 실용성 증명

1.3B 모델이 15B 모델을 능가할 수 있다는 결과는, [[small-language-models|SLM]]이 단순히 "저렴한 대안"이 아니라 **올바른 전략 하에서 최적의 선택**이 될 수 있음을 보여줬다. 이후 Google(Gemma), Alibaba(Qwen), Meta(LLaMA-3.2) 등이 SLM 경쟁에 뛰어든 배경이 되었다.

---

## 한계

### 1. 코드 도메인 한정

Phi-1은 **Python 코드 생성**에 특화되어 있다. 일반 자연어 과제에서의 성능은 검증되지 않았다. (이후 Phi-1.5/2/3에서 일반화됨)

### 2. 교사 모델 의존

교과서 품질 데이터는 GPT-3.5로 생성되었다. 따라서 Phi-1의 성능 상한은 **GPT-3.5의 코드 생성 능력에 의해 제약**된다. 이는 [[synthetic-data-training|합성 데이터의 일반적 한계]]다.

### 3. "교과서 품질"의 정의

무엇이 교과서 품질인지에 대한 **엄밀한 정의가 부족**하다. 현재는 "교육적이고 자기 완결적인 텍스트"라는 직관적 기준에 의존하며, 이를 자동으로 판별하는 방법은 아직 미해결 과제다.

## Paper Summary

| 항목 | 내용 |
|------|------|
| 제목 | Textbooks Are All You Need |
| 저자 | Suriya Gunasekar, Yi Zhang et al. |
| 소속 | Microsoft Research |
| 연도 | 2023 |
| 학회 | arXiv preprint |
| 원문 | [arXiv:2306.11644](https://arxiv.org/abs/2306.11644) |
| 모델 | [HuggingFace: microsoft/phi-1](https://huggingface.co/microsoft/phi-1) |
| 핵심 키워드 | Data Quality, Synthetic Data, Code Generation, Small Language Model, HumanEval |
