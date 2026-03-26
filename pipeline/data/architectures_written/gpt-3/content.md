# GPT-3: Language Models are Few-Shot Learners

## 개요

**GPT-3**는 OpenAI가 2020년 5월 발표한 **1750억(175B) 파라미터** 규모의 자기회귀 언어 모델이다. GPT-2의 구조를 100배 이상 확장하며, 모델 크기와 능력이 비선형적으로 폭발하는 **'Emergent Ability'** 현상을 처음으로 대규모로 입증했다.

GPT-3의 가장 중요한 기여는 **In-Context Learning(ICL)**의 발견이다. 별도의 파인튜닝 없이 프롬프트에 몇 가지 예시(Few-shot)만 제공하면 번역, 질의응답, 코드 생성 등 다양한 태스크를 수행할 수 있음을 보였다. 이는 "모든 태스크는 텍스트 생성이다"라는 GPT-2의 통찰을 실질적으로 입증한 것이다.

API를 통한 상업적 배포로 **LLM의 산업화를 촉발**했으며, ChatGPT, InstructGPT 등 후속 모델의 기반이 되었다.

## 아키텍처 상세

### 대규모 Transformer 디코더

GPT-3는 GPT-2의 아키텍처를 그대로 계승하면서 규모를 극대화했다:

| 하이퍼파라미터 | GPT-2 XL | GPT-3 175B |
|-------------|---------|------------|
| 레이어 수 | 48 | **96** |
| Hidden dim | 1600 | **12288** |
| 어텐션 헤드 | 25 | **96** |
| 컨텍스트 길이 | 1024 | **2048** |
| 파라미터 | 1.5B | **175B** |
| FFN dim | 6400 | **49152** |

Pre-Norm(LayerNorm을 서브레이어 입력 전에 적용)을 사용하여 175B 규모에서도 학습 안정성을 확보했다. 일부 레이어에는 Sparse Transformer 변형의 Alternating Dense/Sparse Attention이 적용된 것으로 알려져 있다.

### 모델 크기 시리즈

GPT-3 논문은 총 8가지 크기의 모델을 학습하여 스케일링 법칙을 체계적으로 연구했다:

| 모델 | 파라미터 | 레이어 | $d_{model}$ | 배치 크기 |
|------|---------|--------|------------|----------|
| Small | 125M | 12 | 768 | 0.5M |
| Medium | 350M | 24 | 1024 | 0.5M |
| Large | 760M | 24 | 1536 | 1M |
| XL | 1.3B | 24 | 2048 | 1M |
| 2.7B | 2.7B | 32 | 2560 | 1M |
| 6.7B | 6.7B | 32 | 4096 | 2M |
| 13B | 13B | 40 | 5140 | 2M |
| **175B** | **175B** | **96** | **12288** | **3.2M** |

### In-Context Learning 메커니즘

ICL의 세 가지 평가 설정:

1. **Zero-shot**: 태스크 설명만 제공
   - `"Translate English to French: cheese =>"`

2. **One-shot**: 태스크 설명 + 예시 1개
   - `"Translate English to French: sea otter => loutre de mer, cheese =>"`

3. **Few-shot**: 태스크 설명 + 예시 수십 개
   - 컨텍스트 윈도우(2048 토큰)가 허용하는 만큼의 예시 제공

## 핵심 혁신

### 1. In-Context Learning의 발견

별도의 그래디언트 업데이트 없이, **프롬프트만으로 태스크를 수행**하는 능력이 충분한 규모에서 창발한다는 것을 보였다. 이는 프롬프트 엔지니어링이라는 새로운 분야를 탄생시켰다.

### 2. 스케일링 법칙의 대규모 검증

모델 크기가 커질수록 Few-shot 성능이 **로그-선형적으로 향상**됨을 8가지 모델 크기에 걸쳐 체계적으로 입증했다. 특히 일부 태스크에서는 특정 규모 이상에서 갑자기 성능이 점프하는 현상(phase transition)이 관찰되었다.

### 3. LLM의 산업화

API 기반 배포를 통해 연구자뿐 아니라 일반 개발자도 대형 언어 모델을 활용할 수 있게 되었다. 이는 AI 스타트업 생태계의 폭발적 성장을 견인했다.

## 벤치마크/성능

| 벤치마크 | 설정 | GPT-3 175B | 이전 SOTA (Fine-tuned) |
|---------|------|-----------|---------------------|
| LAMBADA (Acc) | Zero-shot | 76.2% | 68% |
| LAMBADA (Acc) | Few-shot | **86.4%** | 68% |
| SuperGLUE | Few-shot | 71.8 | 89.0 (fine-tuned) |
| TriviaQA | Few-shot | **71.2%** | 68.0% |
| CoQA | Few-shot | **85.0 F1** | 90.7 (fine-tuned) |
| 2-digit 덧셈 | Few-shot | **100%** | - |
| 3-digit 덧셈 | Few-shot | 80% | - |

Few-shot으로 파인튜닝 없이 파인튜닝된 모델과 경쟁하거나 일부 태스크에서는 이를 능가했다.

## 관련 모델 비교

| 특성 | GPT-2 | GPT-3 | T5-11B |
|------|-------|-------|--------|
| 파라미터 | 1.5B | **175B** | 11B |
| 학습 데이터 | 40GB | **~570GB** | 750GB (C4) |
| 평가 방식 | Zero-shot | **Few-shot** | Fine-tuning |
| 구조 | Decoder | Decoder | Encoder-Decoder |
| SuperGLUE | - | 71.8 (FS) | 88.9 (FT) |
| 배포 | 오픈소스 | **API** | 오픈소스 |
| 학습 비용 | ~수십 GPU일 | **~$12M** | ~수천 GPU일 |

## 실무 활용

### API 기반 활용

```python
import openai

# Few-shot 분류 예시
response = openai.Completion.create(
    model="text-davinci-003",
    prompt="""Classify the sentiment of the following review.

Review: This movie was absolutely wonderful!
Sentiment: Positive

Review: The food was terrible and the service was slow.
Sentiment: Negative

Review: The hotel room was clean but a bit small.
Sentiment:""",
    max_tokens=10,
    temperature=0
)
print(response.choices[0].text.strip())  # "Neutral" 또는 "Mixed"
```

### 주요 활용 분야

- **텍스트 생성/요약**: 기사 작성, 문서 요약
- **코드 생성**: GitHub Copilot의 초기 기반
- **대화형 AI**: ChatGPT의 베이스 모델
- **번역**: 별도 학습 없이 다국어 번역
- **데이터 분석**: 자연어로 데이터 질의

## 한계 및 전망

### 한계

1. **환각(Hallucination)**: 그럴듯하지만 사실이 아닌 정보 생성
2. **편향(Bias)**: 학습 데이터의 사회적 편향 반영
3. **일관성 부족**: 긴 텍스트에서 논리적 일관성 유지 어려움
4. **비용**: 175B 모델 학습에 약 $12M, 추론에도 상당한 GPU 비용
5. **정렬(Alignment)**: 유해 콘텐츠 생성 가능성

### 전망

GPT-3의 한계를 해결하기 위해 OpenAI는 **InstructGPT**(RLHF를 통한 인간 의도 정렬)를 개발했고, 이는 **ChatGPT**로 이어졌다. GPT-4는 멀티모달 능력과 더 정교한 추론을 추가하며, LLM의 실용성을 한 단계 끌어올렸다.

---

**참고 논문**: [Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165) (Brown et al., 2020)

## 관련 문서

- [[gpt-2|GPT-2]] — 발전 기반
- [[gpt-4|GPT-4]] — 후속 모델
- [[instructgpt|Training language models to follow instructions with human feedback]] — 후속 모델
- [[bloom|BLOOM]] — 영감을 줌
- [[claude|Claude (1–3.5 Series)]] — 영감을 줌
- [[falcon|Falcon]] — 영감을 줌
- [[gopher|Gopher]] — 영감을 줌
- [[opt|OPT]] — 영감을 줌
- [[palm|PaLM]] — 영감을 줌
- [[phi|Phi]] — 영감을 줌
