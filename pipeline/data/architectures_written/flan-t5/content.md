<!-- infographic-hero -->
![Flan-T5 핵심 요약](figures/infographic.svg)

*Figure: Flan-T5 한 장 요약 인포그래픽*

# Flan-T5: 명령어 튜닝으로 소형 모델이 거대 모델을 넘다

## 개요

Flan-T5는 2022년 10월 Google Research가 발표한 **명령어 파인튜닝(Instruction Tuning)** 모델이다. 핵심 질문은 단순하다: "파라미터를 키우지 않고도 모델을 더 똑똑하게 만들 수 있을까?"

답은 **명령어 튜닝**에 있었다. T5를 1,836개의 다양한 태스크에 걸쳐 자연어 명령어 형태로 파인튜닝한 결과, 3B 파라미터 Flan-T5 XL이 175B GPT-3를 MMLU에서 능가하는 놀라운 결과가 나왔다. 이는 모델의 크기보다 **학습 방법론**이 더 중요할 수 있다는 패러다임 전환의 신호탄이었다.

'Flan'은 **Finetuned Language Net**의 약자로, Google이 개발한 대규모 명령어 튜닝 방법론을 지칭한다.

- **논문**: [Scaling Instruction-Finetuned Language Models](https://arxiv.org/abs/2210.11416)
- **코드**: [t5x (GitHub)](https://github.com/google-research/t5x)
- **라이선스**: Apache 2.0

![Flan-T5 아키텍처 개요 - 인코더-디코더 구조에 명령어 튜닝 적용](figures/architecture.png)
*Figure 1: Flan-T5 아키텍처 - T5의 인코더-디코더 구조를 유지하면서 Flan Collection(1,836 태스크)과 CoT 파인튜닝을 적용한 설계. (Source: arXiv 2210.11416)*

## 아키텍처 상세

Flan-T5는 T5의 인코더-디코더 구조를 그대로 유지한다. 아키텍처적 변경은 없으며, **데이터와 학습 방법론**만 변경했다:

| 모델 | 파라미터 | 레이어 | Hidden Dim | Heads |
|------|---------|--------|-----------|-------|
| Flan-T5 Small | 80M | 8 | 512 | 6 |
| Flan-T5 Base | 250M | 12 | 768 | 12 |
| Flan-T5 Large | 780M | 24 | 1,024 | 16 |
| Flan-T5 XL | 3B | 24 | 2,048 | 32 |
| Flan-T5 XXL | 11B | 24 | 4,096 | 64 |

모든 모델은 다음 구성을 공유한다:
- **Vocab Size**: 32,100 (SentencePiece)
- **정규화**: RMSNorm (Pre-Norm)
- **활성화 함수**: ReLU
- **위치 인코딩**: Relative Attention Bias

## 핵심 혁신: Flan Collection과 Chain-of-Thought

![명령어 튜닝 개념도 - 1.8K 태스크로 학습 후 미지의 태스크에 일반화](figures/fig_1.png)
*Figure 2: 명령어 튜닝 개념 - 1,836개 태스크를 명령어 형태로 파인튜닝하고, 제로샷·퓨샷·CoT 등 다양한 설정에서 미지의 태스크에 일반화하는 과정. (Source: arXiv 2210.11416)*

### Flan Collection

Flan-T5의 핵심은 **1,836개 태스크**로 구성된 대규모 명령어 데이터셋인 Flan Collection이다:

$$\text{Flan Collection} = \text{Flan 2021} + \text{P3++} + \text{Super-Natural Instructions} + \text{Custom}$$

- **태스크 유형**: 분류, 번역, 요약, QA, 추론, 수학, 코드, 대화 등
- **템플릿**: 각 태스크마다 최대 10개의 명령어 템플릿 사용
- **Input Inversion**: 역 태스크도 학습하여 다양한 형식에 강건하게 대응

![Flan Collection 구성 - 파인튜닝 태스크와 평가 벤치마크 구분](figures/fig_2.png)
*Figure 3: Flan Collection 구성 - T0-SF, Muffin, Natural Instructions v2, CoT(추론) 데이터셋을 포함한 473개 데이터셋, 1,836개 태스크. MMLU, BBH 등은 평가용으로 분리. (Source: arXiv 2210.11416)*

### Chain-of-Thought (CoT) 파인튜닝

![파인튜닝 데이터 형식 조합 - 제로샷, 퓨샷, CoT의 혼합](figures/fig_3.png)
*Figure 4: 파인튜닝 데이터 형식 - 명령어 유무, 예시(exemplar) 유무, CoT 유무를 조합하여 다양한 프롬프트 형식으로 학습. 모든 조합을 혼합 학습한 것이 핵심. (Source: arXiv 2210.11416)*

Flan-T5의 두 번째 핵심 혁신은 **CoT 데이터를 파인튜닝에 포함**한 것이다:

```
질문: 사과가 3개 있고 2개를 더 샀다면 총 몇 개인가?

# CoT 없는 답변
답: 5개

# CoT 포함 답변  
생각: 처음에 사과 3개가 있었다. 2개를 더 샀으므로 3 + 2 = 5이다.
답: 5개
```

**핵심 발견**: CoT 데이터를 5%만 포함해도 제로샷·퓨샷 모두에서 1~7포인트 향상이 나타났다.

### 혼합 프롬프트 설정

![제로샷 CoT 추론 예시 - BIG-Bench 태스크에서의 단계별 추론](figures/fig_7.png)
*Figure 5: 제로샷 CoT 추론 - CoT 데이터를 포함하여 파인튜닝하면 미지의 BIG-Bench 태스크에서도 단계별 추론이 가능해짐. Boolean Expressions, Disambiguation QA 등에서 효과 입증. (Source: arXiv 2210.11416)*

제로샷, 퓨샷, CoT 프롬프트를 **혼합하여 학습**했을 때 모든 설정에서 2%+ 성능 향상이 나타났다.

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Flan-T5 모델 로드
tokenizer = AutoTokenizer.from_pretrained('google/flan-t5-xl')
model = AutoModelForSeq2SeqLM.from_pretrained('google/flan-t5-xl')

# 제로샷 명령어 수행
prompt = "Translate the following sentence to French: 'The weather is nice today.'"
inputs = tokenizer(prompt, return_tensors='pt')
outputs = model.generate(inputs['input_ids'], max_length=100)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
# 출력: "Le temps est beau aujourd'hui."

# CoT 추론
prompt_cot = """Answer the following question by reasoning step by step.
Question: If a train travels at 60 km/h for 2.5 hours, how far does it go?"""
inputs = tokenizer(prompt_cot, return_tensors='pt')
outputs = model.generate(inputs['input_ids'], max_length=200)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

## 벤치마크/성능

| 벤치마크 | Flan-T5 XL (3B) | Flan-T5 XXL (11B) | GPT-3 (175B) | PaLM 62B |
|----------|-----------------|-------------------|-------------|----------|
| MMLU | **52.4%** | **55.1%** | 43.9% | 49.0% |
| BBH-direct | - | **43.7%** | - | 37.5% |
| BBH-CoT | - | **45.3%** | - | 42.1% |

### 핵심 결과
- Flan-T5 XL(3B)이 GPT-3(175B)를 MMLU에서 **8.5%p 능가** (52.4% vs 43.9%)
- Flan-T5 XXL(11B)이 PaLM 62B를 BBH-direct에서 **6.2%p 능가** (43.7% vs 37.5%)
- 동일 크기 T5 대비 평균 **9% 이상** 성능 향상
- MMLU에서 **3%+**, BBH에서 **8%** 개선

## 관련 모델 비교

| 특성 | T5 | Flan-T5 | GPT-3 | InstructGPT |
|------|-----|---------|-------|-------------|
| 구조 | Enc-Dec | Enc-Dec | Dec-only | Dec-only |
| 명령어 튜닝 | X | **O (1,836 태스크)** | X | O (SFT+RLHF) |
| CoT 학습 | X | **O** | X | 부분적 |
| 제로샷 일반화 | 약함 | **강함** | 보통 | 강함 |
| 오픈소스 | O | **O** | X | X |
| 파라미터 효율 | 보통 | **높음** | 낮음 | 낮음 |

## 학습 상세

### 시작점
- T5 사전 학습 체크포인트에서 시작 (추가 사전 학습 없음)

### 명령어 튜닝 설정
- 데이터: Flan Collection (1,836 태스크)
- 배치 크기: 64
- Optimizer: Adafactor (lr = 5e-4)
- CoT 태스크 가중치 상향 조정
- 인프라: 128 TPU v3 코어

## 실무 활용

### 1. 제로샷 NLP 파이프라인
파인튜닝 없이 다양한 NLP 태스크를 처리할 수 있는 범용 모델로 활용된다.

### 2. 경량 추론 서버
Flan-T5 Small/Base는 CPU에서도 구동 가능하여, 비용 효율적인 추론 서버를 구축할 수 있다.

### 3. RAG 시스템의 생성 컴포넌트
Retrieval-Augmented Generation에서 검색된 문서를 기반으로 답변을 생성하는 생성기(generator)로 널리 사용된다.

### 4. 교육 및 연구
다양한 크기로 제공되어 리소스 제약이 있는 환경에서도 실험이 가능하다.

### 5. 파인튜닝 베이스
이미 명령어를 이해하는 상태에서 추가 파인튜닝하면, 순수 T5에서 시작하는 것보다 빠르게 수렴한다.

## 한계 및 전망

### 한계
1. **컨텍스트 길이**: 512 토큰으로 제한되어 긴 문서 처리에 부적합하다
2. **다국어 지원**: 영어 중심 학습으로 다국어 성능이 제한적이다
3. **환각(Hallucination)**: 모르는 것을 "모른다"고 답하기보다 생성하는 경향이 있다
4. **최신 지식 부재**: 2022년 이후 정보를 포함하지 않는다

### 전망
Flan-T5는 **명령어 튜닝의 효과를 대규모로 입증한 역사적 모델**이다. 이 모델이 보여준 핵심 교훈-"작은 모델 + 좋은 학습 방법 > 큰 모델"-은 이후 Alpaca, Vicuna, LIMA 등 데이터 효율적 정렬(alignment) 연구의 이론적 근거가 되었다. 오픈소스로 공개되어 2024년 기준으로도 Hugging Face에서 가장 많이 다운로드되는 모델 중 하나이며, 특히 RAG 시스템과 경량 NLP 파이프라인에서 여전히 현역으로 활약하고 있다.

---

**참고 문헌**
- Chung, H. W., et al. (2022). "Scaling Instruction-Finetuned Language Models." arXiv:2210.11416
- Longpre, S., et al. (2023). "The Flan Collection: Designing Data and Methods for Effective Instruction Tuning."
- Wei, J., et al. (2022). "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models."

## 관련 문서

- [[t5|T5]] - 발전 기반
