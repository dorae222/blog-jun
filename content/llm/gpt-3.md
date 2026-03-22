---
title: "Language Models are Few-Shot Learners (GPT-3)"
slug: "gpt-3"
category: llm
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.442723+00:00"
architecture_entry: "gpt-3"
---

## 개요

**GPT-3(Generative Pre-trained Transformer 3)**는 OpenAI의 Brown et al.(2020)이 발표한 1750억($175B$) 파라미터 규모의 자동회귀 언어 모델입니다. 가장 큰 특징은 **In-Context Learning**: 별도의 파인튜닝 없이, 프롬프트 내에 몇 가지 예제만 보여주면(Few-Shot) 다양한 NLP 태스크를 수행할 수 있다는 것입니다. GPT-3는 현대 대형 언어 모델(LLM) 시대를 연 기념비적 연구로, ChatGPT와 InstructGPT의 직접적인 선조입니다.

## 배경 및 문제 정의

### 파인튜닝 패러다임의 한계

BERT 이후 NLP의 표준은 "대규모 사전 학습 + 태스크별 파인튜닝"이었습니다. 하지만 이 방식은:

- **새 태스크마다 레이블 데이터** 수집 필요
- **태스크별 파인튜닝**으로 다른 태스크에 일반화 어려움
- **허위 상관관계(spurious correlations)** 학습 가능성
- 실제 인간은 새 태스크를 몇 가지 예시만 보고도 수행 가능

### 스케일링 가설

이전 연구들(Kaplan et al., 2020)은 언어 모델 크기, 데이터 양, 계산량이 모두 멱법칙(power law)에 따라 성능과 연관됨을 보였습니다. GPT-3는 이 가설을 극한까지 밀어붙였습니다.

## 핵심 아이디어

### In-Context Learning

파인튜닝 없이 프롬프트 내 예시로 학습하는 세 가지 방식을 정의합니다:

- **Zero-Shot**: 태스크 설명만 제공, 예시 없음
- **One-Shot**: 태스크 설명 + 1개 예시
- **Few-Shot**: 태스크 설명 + $K$개 예시 (보통 $K \leq 100$)

예를 들어 번역 태스크의 Few-Shot 프롬프트:
```
Translate English to French:
sea otter => loutre de mer
peppermint => menthe poivrée
plush giraffe => girafe en peluche
cheese =>
```

모델은 이 패턴을 이해하고 "cheese"의 프랑스어 번역을 생성합니다. **가중치 업데이트 없이** 순전히 문맥에서 학습합니다.

### 스케일링 법칙

성능은 모델 크기 $N$, 데이터셋 크기 $D$, 계산량 $C$에 대해:

$$L(N) \approx \left(\frac{N_c}{N}\right)^{\alpha_N}, \quad L(D) \approx \left(\frac{D_c}{D}\right)^{\alpha_D}$$

GPT-3는 이 법칙에 따라 성능이 매끄럽게 개선됨을 실증했습니다. 특히 Few-Shot 성능은 모델이 클수록 급격히 향상됩니다.

## 아키텍처 / 방법론

### 모델 구조

GPT-3는 GPT-2와 동일한 Transformer 디코더 구조에 다음 수정을 가했습니다:

- **Alternating Dense/Sparse Attention**: 효율적인 대규모 처리를 위해 Sparse Transformer 패턴 적용
- **컨텍스트 윈도우**: 최대 2048 토큰

다양한 크기의 모델을 제안합니다:

| 모델 | 파라미터 수 | 레이어 | $d_{\text{model}}$ | 헤드 수 |
|------|----------|------|------------------|-------|
| GPT-3 Small | 125M | 12 | 768 | 12 |
| GPT-3 Medium | 350M | 24 | 1024 | 16 |
| GPT-3 Large | 760M | 24 | 1536 | 16 |
| GPT-3 XL | 1.3B | 24 | 2048 | 24 |
| GPT-3 2.7B | 2.7B | 32 | 2560 | 32 |
| GPT-3 6.7B | 6.7B | 32 | 4096 | 32 |
| GPT-3 13B | 13B | 40 | 5140 | 40 |
| **GPT-3 175B** | **175B** | **96** | **12288** | **96** |

### 학습 데이터

| 데이터셋 | 토큰 수 | 가중치 |
|---------|--------|-------|
| Common Crawl (필터링) | 410B | 60% |
| WebText2 | 19B | 22% |
| Books1 | 12B | 8% |
| Books2 | 55B | 8% |
| Wikipedia | 3B | 3% |

총 **300B 토큰**으로 학습했습니다.

## 실험 결과

### 언어 모델링 (Penn Treebank)

| 모델 | Perplexity |
|------|----------|
| SOTA (파인튜닝) | 35.8 |
| GPT-3 Zero-Shot | **20.50** |

### SuperGLUE

| 모델 | 점수 |
|------|-----|
| BERT-Large (파인튜닝) | 69.0 |
| RoBERTa (파인튜닝) | 84.6 |
| GPT-3 Few-Shot | **71.8** |
| 인간 | 89.8 |

### TriviaQA (Open-Domain QA)

| 모델 | 정확도 |
|------|------|
| RAG (파인튜닝) | 68.0% |
| GPT-3 Zero-Shot | 64.3% |
| **GPT-3 Few-Shot** | **71.2%** |

### 산술 추론 (2자리 덧셈)

| 모델 | 정확도 |
|------|------|
| GPT-3 Zero-Shot | 76% |
| GPT-3 Few-Shot (k=50) | 100% |

## 의의 및 한계

### 의의

- **LLM 시대 개막**: 충분히 큰 언어 모델은 별도 파인튜닝 없이 광범위한 태스크를 수행할 수 있음을 증명
- **프롬프트 엔지니어링의 부상**: In-Context Learning은 모델 가중치 수정 없이 프롬프트 설계만으로 성능을 크게 좌우함
- **스케일링 법칙 실증**: 모델 크기가 커질수록 새로운 능력(emergent abilities)이 나타남
- **상업적 영향**: GPT-3 API는 수천 개의 AI 애플리케이션의 기반이 됨

### 한계

- **편향과 독성(Bias/Toxicity)**: 인터넷 텍스트로 학습해 사회적 편견, 유해 콘텐츠 생성 가능
- **사실 오류(Hallucination)**: 모델이 자신 있게 틀린 정보를 생성
- **컨텍스트 길이 제한**: 2048 토큰으로 긴 문서 처리 어려움
- **추론 비용**: 175B 파라미터 모델의 인퍼런스는 매우 비쌈
- **지시 따르기 어려움**: 프롬프트 형식에 매우 민감하며, 인간의 의도를 정확히 파악하지 못하는 경우 많음 → InstructGPT로 해결
- **블랙박스**: 어떻게 동작하는지 해석하기 어려움\n\n## 코드 예제\n\n### GPT-3 In-Context Learning (OpenAI API)\n\n```python\nfrom openai import OpenAI\n\nclient = OpenAI()  # OPENAI_API_KEY 환경변수 필요\n\ndef few_shot_classify(text: str, examples: list[dict]) -> str:\n    \"\"\"Few-shot In-Context Learning으로 텍스트 분류.\n    Args:\n        text: 분류할 텍스트\n        examples: [{'input': ..., 'output': ...}, ...] 형식의 예시 목록\n    \"\"\"\n    # Few-shot 예시로 프롬프트 구성\n    prompt_parts = []\n    for ex in examples:\n        prompt_parts.append(f\"Text: {ex['input']}\\nSentiment: {ex['output']}\")\n    prompt_parts.append(f\"Text: {text}\\nSentiment:\")\n    prompt = \"\\n\\n\".join(prompt_parts)\n\n    response = client.completions.create(\n        model=\"gpt-3.5-turbo-instruct\",  # GPT-3 계열\n        prompt=prompt,\n        max_tokens=10,\n        temperature=0,  # 결정론적 출력\n    )\n    return response.choices[0].text.strip()\n\n# Few-shot 예시 정의 (GPT-3은 파인튜닝 없이 컨텍스트만으로 학습)\nfew_shot_examples = [\n    {\"input\": \"I absolutely loved this movie!\", \"output\": \"Positive\"},\n    {\"input\": \"The worst film I've ever seen.\", \"output\": \"Negative\"},\n    {\"input\": \"It was okay, nothing special.\", \"output\": \"Neutral\"},\n]\n\n# Zero-shot: 예시 없이\nzero_shot = client.completions.create(\n    model=\"gpt-3.5-turbo-instruct\",\n    prompt=\"Classify sentiment of: 'This exceeded all my expectations!'\\nSentiment:\",\n    max_tokens=10, temperature=0\n).choices[0].text.strip()\nprint(f\"Zero-shot: {zero_shot}\")\n\n# Few-shot: 3개 예시 제공\nresult = few_shot_classify(\"An outstanding achievement in cinema.\", few_shot_examples)\nprint(f\"Few-shot: {result}\")\n```\n\n> **핵심 통찰**: GPT-3의 few-shot 능력은 별도 가중치 업데이트 없이 오직 **컨텍스트 내 패턴 인식**만으로 작동합니다. 예시 수(K)가 늘어날수록 성능이 향상되는 In-Context Learning의 특성을 보여줍니다.