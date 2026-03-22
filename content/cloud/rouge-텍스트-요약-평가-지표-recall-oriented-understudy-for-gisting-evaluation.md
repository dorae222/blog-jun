---
title: "ROUGE: 텍스트 요약 평가 지표 (Recall-Oriented Understudy for Gisting Evaluation)"
slug: "rouge-텍스트-요약-평가-지표-recall-oriented-understudy-for-gisting-evaluation"
category: cloud
tags: ["evaluation-metrics", "nlp", "nlp-evaluation", "rouge", "rouge-l", "rouge-n", "rouge-s", "rouge-w", "text-summarization"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:07.354010+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

> **Alias:**
> Recall-Oriented Understudy for Gisting Evaluation

### 개념
- 텍스트 요약의 품질을 평가하기 위한 지표
- 생성된 요약과 참조 요약 간의 겹침 정도를 측정한다

### 주요 변형
- **ROUGE-N**: n-gram 기반의 평가
- **ROUGE-L**: 최장 공통 부분 수열(LCS) 기반
- **ROUGE-W**: 가중치가 적용된 LCS
- **ROUGE-S**: Skip-bigram 기반

### 계산 방법 (ROUGE-N 예시)
$ROUGE\text{-}N = \frac{\sum \text{Count}_{\text{match}}(n\text{-}gram)}{\sum \text{Count}(n\text{-}gram)}$

여기서:
- $\text{Count}_{\text{match}}(n\text{-}gram)$: 참조요약의 n-gram 중 생성요약과 일치하는 수
- $\text{Count}(n\text{-}gram)$: 참조요약의 전체 n-gram 수

### 특징
- **장점**: 요약의 내용 포함도를 잘 측정하며, 다양한 변형을 통해 평가 관점을 확장할 수 있다
- **단점**: 단어 순서나 의미적 유사성은 충분히 고려하지 못한다

### 적용 분야
- 자동 텍스트 요약 평가
- 질의응답 시스템 평가