---
title: "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
slug: rag
category: technique
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.404744+00:00"
---

## 개요

RAG(Retrieval-Augmented Generation)는 2020년 NeurIPS에서 Meta AI(당시 Facebook AI)의 Patrick Lewis 등이 발표한 논문으로, **사전학습 언어 모델(LM)에 외부 문서 검색 기능을 결합**하는 프레임워크를 제안한다. 기존 seq2seq 모델은 학습 시점에 파라미터 안에 지식을 고정적으로 저장하므로, 새로운 사실이나 롱테일 지식에 취약하다는 한계가 있었다. RAG는 이 문제를 비모수적(non-parametric) 메모리인 외부 문서 저장소와 결합함으로써 해결한다.

## 배경 및 문제 정의

### 기존 방법의 한계

사전학습 언어 모델(GPT, BERT, T5 등)은 대규모 텍스트 코퍼스를 학습하며 방대한 지식을 파라미터 안에 내재화한다. 하지만 이 **파라미터 기억(parametric memory)**은 다음과 같은 문제를 지닌다:

1. **지식의 정적성**: 학습 이후 새로운 사실을 반영하려면 전체 모델을 재학습해야 한다.
2. **불투명성**: 모델이 어떤 근거로 답변을 생성하는지 추적하기 어렵다.
3. **롱테일 지식 취약**: 학습 데이터에 적게 등장하는 희귀한 사실에 대한 답변 정확도가 낮다.
4. **환각(hallucination)**: 정확한 사실 근거 없이 그럴듯한 내용을 생성하는 경향이 있다.

이러한 한계를 극복하기 위해 RAG는 **파라미터 기억과 비모수적 외부 메모리를 결합**하는 접근법을 채택한다.

## 핵심 아이디어

RAG의 핵심은 생성(generation) 과정에서 외부 문서 검색 결과를 조건으로 활용하는 것이다. 입력 질문 $x$에 대해 관련 문서 $z$를 검색한 뒤, 이를 컨텍스트로 사용하여 최종 답변 $y$를 생성한다.

$$p(y|x) = \sum_{z \in \text{top-k}(p(\cdot|x))} p_\eta(z|x) \cdot p_\theta(y|x, z)$$

여기서:
- $p_\eta(z|x)$: DPR(Dense Passage Retriever)이 질문 $x$에 대해 문서 $z$를 반환할 확률
- $p_\theta(y|x, z)$: BART 기반 생성 모델이 $(x, z)$를 입력으로 답변 $y$를 생성할 확률
- top-k: 가장 관련성 높은 $k$개의 문서만 합산

논문은 두 가지 변형을 제안한다:

**RAG-Sequence**: 전체 답변 시퀀스에 동일한 문서를 사용한다.
$$p_{\text{RAG-Seq}}(y|x) \approx \sum_{z \in \text{top-k}} p_\eta(z|x) \prod_{i=1}^{N} p_\theta(y_i | x, z, y_{1:i-1})$$

**RAG-Token**: 각 토큰 생성 시마다 다른 문서를 조건으로 활용할 수 있다.
$$p_{\text{RAG-Token}}(y|x) \approx \prod_{i=1}^{N} \sum_{z \in \text{top-k}} p_\eta(z|x) \cdot p_\theta(y_i | x, z, y_{1:i-1})$$

## 아키텍처 / 방법론

### 구성 요소

RAG는 두 개의 주요 컴포넌트로 구성된다:

**1. Retriever: DPR (Dense Passage Retriever)**
- 질문 인코더 $q(\cdot)$와 문서 인코더 $d(\cdot)$를 각각 BERT 기반으로 구성
- 질문 벡터 $q(x)$와 문서 벡터 $d(z)$의 내적(dot product)으로 유사도를 계산
$$\text{sim}(x, z) = q(x)^\top d(z)$$
- Wikipedia 전체를 100 단어 단위의 청크로 분할한 약 2,100만 개의 패시지를 FAISS 인덱스에 저장
- 빠른 최근접 이웃 탐색으로 top-k 문서를 실시간 검색

**2. Generator: BART**
- `[SEP]` 토큰으로 질문과 검색 문서를 연결하여 입력 구성
- BART-large를 사용하여 최종 답변 텍스트 생성
- Retriever와 Generator를 함께 end-to-end로 파인튜닝 (문서 인덱스는 고정)

### 학습 방식

문서 인코더를 포함한 인덱스는 학습 중 고정하고, 질문 인코더와 BART 파라미터만 역전파로 업데이트한다. 이를 통해 학습 효율성을 유지하면서도 실제 검색을 활용한 학습이 가능하다.

$$\mathcal{L}(\theta, \eta) = -\sum_{(x_i, y_i)} \log p(y_i | x_i)$$

## 실험 결과

### 오픈 도메인 QA 벤치마크

| 데이터셋 | 기존 SOTA | RAG-Token | RAG-Sequence |
|---------|---------|----------|-------------|
| NaturalQuestions | 44.5 | 44.5 | **44.5** |
| TriviaQA | 57.9 | **56.8** | 55.8 |
| WebQuestions | 41.7 | 45.2 | **45.5** |
| CuratedTREC | 42.9 | **68.0** | 65.7 |

### Jeopardy 질문 생성

인간 평가에서 RAG가 생성한 질문이 BART 단독 생성 대비 **더 사실적이고 구체적**이라는 평가를 받았다.

### FEVER 팩트 검증

RAG는 FEVER 벤치마크에서 4.3% 향상된 성능을 보였으며, 별도의 IR 시스템 없이도 경쟁력 있는 결과를 달성했다.

## 의의 및 한계

### 의의

RAG 논문은 현대 LLM 시대의 검색 증강 생성 패러다임의 토대를 마련했다. 핵심 기여는 다음과 같다:

1. **지식의 외재화**: 모든 지식을 파라미터 안에 저장할 필요 없이 외부 저장소를 활용
2. **업데이트 용이성**: 문서 저장소만 갱신하면 새로운 지식을 즉시 반영
3. **해석 가능성**: 어떤 문서를 근거로 답변했는지 추적 가능
4. **범용 프레임워크**: 다양한 지식 집약적 NLP 태스크에 적용 가능

### 후속 연구와의 연결

RAG는 이후 Self-RAG, REALM, RETRO, Atlas, LlamaIndex, LangChain 등 수많은 후속 연구의 기반이 되었다. 특히 LLM의 환각 문제를 줄이기 위한 RAG 시스템은 현재 프로덕션 AI 응용프로그램의 핵심 구성 요소가 되었다.

### 한계

1. **검색 병목**: 검색 품질이 전체 성능의 상한선이 되어, 관련 문서가 없을 경우 성능이 급락
2. **문서 길이 제한**: 검색된 문서를 컨텍스트 윈도우 안에 모두 담기 어려운 경우 존재
3. **검색-생성 불일치**: 검색된 문서와 생성 모델이 동일한 방향으로 학습되지 않을 수 있음
4. **추론 속도**: 실시간 검색이 필요하므로 순수 생성 모델 대비 지연시간이 증가