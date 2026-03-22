---
title: "n-gram 기반 생성 텍스트 평가 지표"
slug: "n-gram-기반-생성-텍스트-평가-지표"
category: cloud
tags: ["brevity-penalty", "evaluation-metrics", "machine-translation", "n-gram", "nlp", "precision", "text-generation", "text-summarization"]
status: published
post_type: article
quality_score: 7.0
created_at: "2026-03-02T01:08:06.246029+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: B

---

### 개념
- 기계번역과 텍스트 생성 모델의 품질을 평가하는 지표
- 생성된 텍스트와 참조 텍스트(reference) 간의 n-gram 일치도를 측정

### 계산 방법
- n-gram precision의 기하 평균을 계산
- Brevity Penalty(BP)를 적용하여 짧은 번역에 대한 불이익 부여
- 일반적으로 1-gram부터 4-gram까지 사용

### 특징
- **장점**: 계산이 빠르고 간단하며, 널리 사용되어 비교 가능
- **단점**: 의미적 유사성보다는 단어 일치에 집중하고, 참조 번역이 필요

### 적용 분야
- 기계번역 평가
- 텍스트 요약 평가
- 자연어 생성 모델 평가