---
title: Amazon Redshift ML — SQL로 수행하는 Redshift 내 머신러닝
slug: "amazon-redshift-ml--sql로-수행하는-redshift-내-머신러닝"
category: cloud
tags: ["amazon-redshift", "amazon-sagemaker", "automl", "aws", "data-analytics", "ml-in-database", "predictive-analytics", "redshift-ml", "sql-ml"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.618280+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **서비스명**       | Amazon Redshift ML |
| **기능**           | SQL만으로 **Redshift 내에서 머신러닝 모델 생성, 훈련, 예측 가능** |
| **기반 엔진**      | Amazon SageMaker (백엔드에서 자동 연계)
| **언어**           | SQL (CREATE MODEL, SELECT PREDICT 등)

> 🧠 **목적**: 데이터 엔지니어나 분석가가 Redshift 안에서 데이터를 이동시키지 않고 **SQL로 직접 ML 모델을 생성하고 활용**할 수 있게 함

---

## 🔍 주요 기능

| 기능 | 설명 |
|------|------|
| `CREATE MODEL` | Redshift 테이블 기반으로 ML 모델 생성 (AutoML 방식) |
| `SELECT PREDICT` | 훈련된 모델로 예측 결과 조회 |
| `EXPORT MODEL` | 모델을 SageMaker에서 추론용으로 재사용 가능 |
| `CREATE EXTERNAL MODEL` | SageMaker에 이미 있는 모델을 Redshift에서 호출 가능 (inference only)

---

## ✅ 장점

- **SQL만으로 ML 가능** (개발자가 아닌 분석가도 사용 가능)
- **데이터 이동 불필요** (Redshift 내에서 직접 처리)
- **AutoML 기반** → 모델 튜닝 자동화
- **SageMaker 연계** → 고성능 인프라 활용
- **예측 결과를 SQL JOIN 등과 함께 즉시 사용 가능**

---

## 🧪 사용 예시

```sql
-- 모델 생성
CREATE MODEL churn_model
FROM (SELECT age, tenure, usage, churn FROM users)
TARGET churn
FUNCTION my_churn_predictor
IAM_ROLE 'arn:aws:iam::123456789012:role/MySageMakerRole'
AUTO ON;

-- 예측 사용
SELECT user_id, my_churn_predictor(age, tenure, usage)
FROM users
WHERE region = 'APAC';
````

---

## ⚠️ 제한 사항

|항목|설명|
|---|---|
|**복잡한 모델 제어 제한**|세부 하이퍼파라미터를 수동으로 튜닝하기 어려움|
|**실시간 추론 아님**|일반 SELECT 쿼리와 유사한 지연 시간|
|**모델 훈련 시간**|훈련에 몇 분~수십 분이 소요될 수 있음 (SageMaker 리소스 사용)|

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|Redshift SQL을 통해 ML 모델 생성/예측이 가능한 기능|
|**백엔드 엔진**|Amazon SageMaker|
|**사용 방식**|`CREATE MODEL`, `PREDICT()`|
|**장점**|SQL만으로 예측 수행, 데이터 이동 없음|
|**적합 대상**|분석가, BI 사용자, 간단한 예측 모델 운영|