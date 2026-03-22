---
title: "AWS Glue DynamicFrame란?"
slug: "aws-glue-dynamicframe란"
category: cloud
tags: ["aws-glue", "big-data", "data-processing", "dynamicframe", "etl", "json", "s3", "schema-evolution", "spark"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.906264+00:00"
---

## AWS Glue DynamicFrame란?

**AWS Glue DynamicFrame**은
Glue ETL에서 사용하는 **스키마 유연성이 높은 데이터 추상화 객체**로,
반정형 데이터·스키마 변화·대량 소형 파일 처리까지 **안정적인 ETL을 위해 설계된 Glue 전용 구조**입니다.

---

## DynamicFrame의 주요 특징 (보완 정리)

### 1️⃣ 스키마 유연성

- 컬럼 타입 불일치 시 `choice` 타입으로 유지
- ETL을 중단하지 않고 데이터 보존
- 이후 `ResolveChoice`로 타입을 명확히 지정 가능

---

### 2️⃣ 반정형·비정형 데이터 처리

- JSON, 중첩 구조, 배열 처리에 적합
- `Relationalize`, `ApplyMapping` 등 Glue 전용 변환 제공

---

### 3️⃣ 결측치·불완전 데이터에 강함

- 일부 파일에 없는 컬럼을 허용
- null/누락으로 인한 작업 실패를 방지

---

### 4️⃣ **대량 소형 파일 처리에 유리한 내부 최적화 포함**

DynamicFrame은 S3에 존재하는:

- 수만~수십만 개의 작은 파일
- 파티션 단위로 분산된 데이터

를 처리할 때:

- 내부적으로 파일을 묶어 처리하거나
- Spark 작업 수를 줄여
- ETL 오버헤드를 완화할 수 있는 옵션을 제공합니다

> 이 과정에서 **그룹화(Grouping) 옵션**이 사용될 수 있으며,
> 이는 **집계 목적이 아니라 처리 효율 개선 목적**입니다.

---

### 5️⃣ Spark DataFrame과 상호 변환 가능

- 초기 수집·정제 단계에서는 DynamicFrame을 사용
- 복잡한 연산·집계 단계에서는 Spark DataFrame을 사용

```python
df = dynamic_frame.toDF()
dyf = DynamicFrame.fromDF(df, glueContext, "dyf")
```

---

## DynamicFrame vs Spark DataFrame (보완)

|항목|DynamicFrame|DataFrame|
|---|---|---|
|스키마 변화|매우 강함|엄격|
|반정형 데이터|우수|제한|
|소형 파일 ETL 안정성|높음|낮음|
|집계(groupBy)|제한적|강력|
|사용 시점|수집·정제|분석·집계|

---

## 언제 DynamicFrame이 적합한가?

- Glue ETL **초기 단계**
- JSON/CSV 혼합 데이터
- 파티션·파일 스키마 불균일
- 수많은 소형 파일 처리
- 안정성이 성능보다 중요한 경우

---

## 핵심 포인트 (정리)

- Glue ETL 기본 데이터 구조 → **DynamicFrame**
- 스키마 불안정 → **DynamicFrame**
- choice 타입 → **DynamicFrame**
- 소형 파일 ETL 안정성 → **DynamicFrame**
- 고급 집계 → DataFrame
