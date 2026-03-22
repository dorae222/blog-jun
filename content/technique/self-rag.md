---
title: "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection"
slug: "self-rag"
category: technique
tags: []
status: published
post_type: paper_review
quality_score: 0.0
created_at: "2026-03-17T21:24:56.406749+00:00"
---

## 개요

Self-RAG는 2023년 Akari Asai(워싱턴대학교) 등이 ICLR에 발표한 논문으로, 언어 모델에 **자기 반성(self-reflection)** 능력을 부여하여 검색과 생성의 품질을 스스로 제어하는 방법을 제안한다. 기존 RAG 시스템은 모든 입력에 대해 무조건 외부 문서를 검색하므로, 간단한 질문이나 검색이 불필요한 경우에도 불필요한 연산과 노이즈가 발생할 수 있었다. Self-RAG는 이를 해결하기 위해 **반성 토큰(reflection token)**이라는 특수 토큰을 도입한다.

## 배경 및 문제 정의

### 기존 RAG의 한계

표준 RAG(Lewis et al., 2020)는 다음과 같은 문제를 지닌다:

1. **무조건적 검색**: 입력이 단순한 인사말이나 창의적 글쓰기 요청이더라도 항상 검색을 수행
2. **검색 품질 비평 부재**: 검색된 문서가 실제로 답변에 유용한지 검증하지 않음
3. **생성 품질 비평 부재**: 생성된 텍스트가 검색 문서에 의해 충분히 지지되는지 평가하지 않음
4. **적응성 부재**: 태스크 유형에 따라 검색 빈도나 방식을 조절하지 못함

Self-RAG는 이러한 문제를 **반성 토큰을 통한 자기 비평**으로 해결한다.

## 핵심 아이디어

### 반성 토큰 (Reflection Tokens)

Self-RAG는 네 가지 유형의 특수 반성 토큰을 정의한다:

| 토큰 유형 | 역할 | 가능한 값 |
|---------|------|----------|
| `[Retrieve]` | 검색 필요 여부 판단 | yes / no / continue |
| `[IsRel]` | 검색 문서의 관련성 평가 | relevant / irrelevant |
| `[IsSup]` | 생성 텍스트의 문서 지지 여부 | fully supported / partially supported / no support |
| `[IsUse]` | 최종 응답의 유용성 평가 | 1~5점 척도 |

이 토큰들은 기존 어휘(vocabulary)에 추가되어, 모델이 일반 텍스트 토큰을 생성하는 것과 동일한 방식으로 자연스럽게 생성된다.

### 생성 과정

입력 $x$와 이전까지 생성된 텍스트 $y_{<t}$가 주어졌을 때, Self-RAG의 생성 과정은 다음과 같다:

**Step 1: 검색 필요성 판단**
$$\hat{r} = \arg\max_r p_\theta(r | x, y_{<t}), \quad r \in \{\text{yes, no, continue}\}$$

**Step 2: 검색 수행 (if $\hat{r}$ = yes)**
$$\{d_1, d_2, \ldots, d_k\} = \text{Retrieve}(x, y_{<t})$$

**Step 3: 관련성 평가 및 세그먼트 생성**
각 문서 $d_i$에 대해:
$$\hat{y}_t^{(i)}, \hat{c}_t^{(i)} = \arg\max_{y, c} p_\theta(y, c | x, y_{<t}, d_i)$$

여기서 $c$는 `[IsSup]` 토큰값이다.

**Step 4: 세그먼트 선택**
`[IsUse]` 점수와 `[IsSup]` 값을 조합하여 최적 세그먼트 선택:
$$\hat{y}_t = \arg\max_{y^{(i)}} \left[ \text{score}_{\text{rel}}(d_i) + \text{score}_{\text{sup}}(y^{(i)}) + \text{score}_{\text{use}}(y^{(i)}) \right]$$

### 학습 방법

**Critic 모델 학습**: GPT-4를 사용하여 기존 데이터에 반성 토큰 레이블을 자동으로 생성

**Generator 모델 학습**: 반성 토큰이 포함된 증강 데이터로 Llama2-7B/13B를 파인튜닝

$$\mathcal{L}(\theta) = -\sum_{t=1}^{T} \log p_\theta(y_t^* | x, y_{<t}^*)$$

여기서 $y^*$는 반성 토큰이 삽입된 정답 시퀀스이다.

## 아키텍처 / 방법론

### 데이터 생성 파이프라인

1. **오프라인 단계**: GPT-4 기반 Critic 모델로 학습 데이터의 각 문단에 반성 토큰 자동 레이블링
2. **학습 단계**: 레이블된 데이터로 언어 모델(Llama2) 파인튜닝, 단일 모델이 검색 판단·생성·비평을 모두 수행
3. **추론 단계**: 반성 토큰을 기반으로 Tree-decoding 또는 Beam search로 최적 출력 선택

### 추론 시 유연한 제어

추론 시 반성 토큰의 가중치를 조정하여 사용 사례에 맞게 동작을 제어할 수 있다:
- 사실성 중시 태스크: `[IsSup]` 토큰 가중치 증가
- 다양성 중시 태스크: 검색 빈도 감소

## 실험 결과

### 오픈 도메인 QA

| 모델 | PopQA | TriviaQA | PubHealth |
|-----|-------|----------|-----------|
| ChatGPT | 29.3 | 74.7 | 70.1 |
| Llama2-chat 13B | 20.0 | 63.5 | 57.6 |
| Perplexity.ai | 34.8 | - | - |
| **Self-RAG 13B** | **54.9** | **67.3** | **78.2** |

### 장문 생성 태스크 (ASQA, QAMPARI)

Self-RAG는 인용 정밀도(citation precision)와 재현율(citation recall)에서 기존 RAG 대비 평균 10% 이상 향상을 보였다.

### 의학 QA (MedQA)

Self-RAG 7B가 ChatGPT를 2.4포인트 능가하는 성능을 보였다.

## 의의 및 한계

### 의의

1. **적응적 검색**: 태스크 복잡도에 따라 검색 여부를 동적으로 결정하여 효율성 향상
2. **자기 감사(self-audit)**: 생성된 내용이 근거 문서에 의해 지지되는지 스스로 검증
3. **단일 모델 통합**: 별도의 Critic 모델 없이 하나의 모델로 검색·생성·비평을 모두 수행
4. **추론 시 제어 가능성**: 반성 토큰 가중치 조정으로 사용자 요구에 맞는 동작 커스터마이징

### 후속 연구와의 연결

Self-RAG의 아이디어는 이후 CRAG(Corrective RAG), FLARE, ReSP 등의 후속 연구에 영향을 미쳤으며, 강화학습 기반 RAG 최적화 연구의 기반이 되었다.

### 한계

1. **학습 데이터 의존성**: 반성 토큰 레이블 생성을 위해 GPT-4가 필요하여 데이터 구축 비용이 높음
2. **반성 토큰 정확도**: 학습된 모델의 자기 비평이 항상 정확하지 않을 수 있음
3. **복잡한 추론 제한**: 다단계 추론이 필요한 태스크에서는 여전히 한계가 있음
4. **지연 시간 증가**: 다중 세그먼트 생성 및 비교로 인해 표준 RAG 대비 추론 속도 감소