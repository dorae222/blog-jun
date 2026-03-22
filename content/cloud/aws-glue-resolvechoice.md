---
title: AWS Glue ResolveChoice
slug: "aws-glue-resolvechoice"
category: cloud
tags: ["aws", "aws-glue", "dynamicframe", "etl", "glue", "parquet", "redshift", "resolvechoice", "spark"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.952463+00:00"
---

**AWS Glue ResolveChoice**는
Glue ETL 작업에서 **데이터 타입이 모호하거나 여러 타입으로 추론된 컬럼을 명확하게 처리**하기 위한 **DynamicFrame 전용 변환(Transform)** 입니다.

---

## 한 줄 정의

> **ResolveChoice는 AWS Glue DynamicFrame에서 동일 컬럼에 여러 데이터 타입(choice type)이 존재할 때 이를 하나의 타입 또는 구조로 “해결(resolve)”하는 변환이다.**

---

## 왜 ResolveChoice가 필요한가?

AWS Glue는 **DynamicFrame**을 사용할 때:

- 서로 다른 파일/파티션에서
    
- 같은 컬럼이 **서로 다른 타입**(예: string vs int)으로 존재하면
    
해당 컬럼을 **`choice` 타입**으로 추론합니다.

예:

```text
age: choice<int, string>
```

이 상태로는:

- Parquet/Redshift에 쓰기 실패
    
- Spark DataFrame 변환 오류
    
- 집계/연산 불가
    
👉 그래서 **ResolveChoice가 필수**

---

## 주요 동작 방식 (4가지)

### 1️⃣ `make_cols`

- 각 타입을 **별도 컬럼으로 분리**
    
```python
ResolveChoice.make_cols("age")
```

결과:

```text
age_int
age_string
```

---

### 2️⃣ `cast`

- 지정한 타입으로 **강제 변환**
    
```python
ResolveChoice.cast("age", "int")
```

---

### 3️⃣ `make_struct`

- 여러 타입을 **struct로 묶음**
    
```python
ResolveChoice.make_struct("age")
```

결과:

```text
age.int
age.string
```

---

### 4️⃣ `project`

- 하나의 타입만 선택 (나머지 제거)
    
```python
ResolveChoice.project("age", "int")
```

---

## 사용 예시 (실전)

```python
from awsglue.transforms import ResolveChoice

resolved = ResolveChoice.apply(
    frame=dynamic_frame,
    choice="cast:double"
)
```

또는 컬럼별 지정:

```python
resolved = ResolveChoice.apply(
    frame=dynamic_frame,
    specs=[("age", "cast:int"), ("salary", "cast:double")]
)
```

---

## ResolveChoice vs DataFrame cast

|항목|ResolveChoice|Spark DataFrame cast|
|---|---|---|
|대상|DynamicFrame|DataFrame|
|choice 타입 처리|✅|❌|
|Null/유연성|높음|엄격|
|Glue 특화|✅|❌|

👉 **DynamicFrame 단계에서는 ResolveChoice**,  
DataFrame 변환 후에는 Spark cast 사용이 일반적

---

## 시험 대비 핵심 포인트

- **choice 타입 오류 해결** → ResolveChoice
    
- Glue ETL에서 **타입 충돌**
    
- Redshift/Parquet 쓰기 전 필수 단계
    
- DynamicFrame 전용
    
---

## 한 문장 암기

> **ResolveChoice는 Glue DynamicFrame의 다중 타입 컬럼을 단일 타입으로 정리하는 변환이다.**