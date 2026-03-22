---
title: "F1-Score 개념 및 계산법"
slug: "f1-score-개념-및-계산법"
category: cloud
tags: ["classification", "evaluation-metrics", "f1-score", "imbalanced-data", "information-retrieval", "multiclass", "nlp", "precision", "recall"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:06.793862+00:00"
---

### 개념
- 분류 모델의 성능을 평가하는 대표적인 지표
- Precision(정밀도)과 Recall(재현율)의 조화평균으로 정의됨

### 계산 방법
$Precision = \frac{TP}{TP + FP}$

$Recall = \frac{TP}{TP + FN}$

$F1\text{-}Score = \frac{2 \times Precision \times Recall}{Precision + Recall}$

여기서:
- $TP$: True Positive
- $FP$: False Positive
- $FN$: False Negative

### 특징
- 장점: 정밀도와 재현율을 동시에 고려하여 균형 있는 성능 평가가 가능하며, 클래스 불균형이 있는 데이터셋에서 특히 유용함
- 단점: True Negative(TN)를 고려하지 않으므로, TN 정보가 중요한 상황에서는 한계가 있음

### 변형
- Macro F1: 각 클래스별 F1을 단순 평균한 값
- Micro F1: 전체 TP, FP, FN을 합산하여 계산한 F1
- Weighted F1: 클래스 빈도에 따라 가중치를 부여한 F1 평균

### 적용 분야
- 이진 분류 및 다중 분류 평가
- 정보 검색
- 자연어 처리(NLP) 태스크 평가