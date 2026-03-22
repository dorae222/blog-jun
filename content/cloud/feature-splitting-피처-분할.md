---
title: Feature Splitting (피처 분할)
slug: "feature-splitting-피처-분할"
category: cloud
tags: ["categorical-encoding", "data-preprocessing", "datetime", "feature-engineering", "feature-extraction", "feature-splitting", "machine-learning"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:08.391922+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---

---
aliases:
  - Feature splitting
  - 피처 분할
---
## 🧩 Quick Overview

| 항목            | 설명 |
|-----------------|------|
| **용어명**       | Feature Splitting (피처 분할) |
| **소속 분야**    | 머신러닝, 피처 엔지니어링 |
| **기본 개념**    | 하나의 복합적인 피처를 **여러 개의 더 단순하고 의미 있는 피처로 나누는 과정** |

> ✂️ **목적**: 모델이 더 잘 이해하고 학습할 수 있도록 **복잡하거나 중첩된 데이터를 분해**하여 정보 전달을 명확히 하고 학습 효율을 높임

---

## 🔍 사용 예시

### 1. **날짜/시간 분할**
- `2023-07-29 14:30:00` → `year`, `month`, `day`, `hour`, `weekday`

### 2. **카테고리 분할**
- `location = "Seoul_Gangnam"` → `city = Seoul`, `district = Gangnam`

### 3. **문자열 토큰 분할**
- `product_tags = "electronics|mobile|android"` → 다중 이진 피처 (one-hot)

### 4. **좌표 분할**
- `coordinates = "37.5665,126.9780"` → `lat`, `lng`

---

## ✅ 장점

| 항목 | 설명 |
|------|------|
| **모델 성능 개선** | 더 의미 있는 변수로 분해하여 학습 성능을 개선할 수 있음 |
| **해석 가능성 증가** | 단순한 피처가 모델 결과 해석에 도움을 줌 |
| **다양한 모델 지원** | 비트리 기반 모델뿐 아니라 선형 회귀 등 다양한 모델에 유용함 |

---

## ⚠️ 주의사항

| 항목 | 설명 |
|------|------|
| **과도한 분할은 노이즈 유입** | 지나친 분할은 정보 희석이나 희소성 증가로 이어질 수 있음 |
| **피처 간 상관관계 고려 필수** | 분할된 피처들이 서로 중복되거나 강한 상관관계를 갖지 않도록 주의해야 함 |
| **스케일링/정규화 필요 가능성** | 수치형 피처로 변환한 경우 후속 스케일링이나 정규화가 필요할 수 있음 |

---

## 🧾 요약

| 항목 | 설명 |
|------|------|
| **정의** | 하나의 복합 피처를 다수의 의미 있는 피처로 분할하는 전처리 기법 |
| **활용 목적** | 모델 학습 최적화, 성능 개선, 해석 용이성 증가 |
| **대표 예시** | 날짜 분해, 문자열 토큰화, 위치 좌표 나누기 |