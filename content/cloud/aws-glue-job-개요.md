---
title: AWS Glue Job 개요
slug: "aws-glue-job-개요"
category: cloud
tags: ["aws-glue", "data-lake", "etl", "job-bookmark", "pyspark", "python", "ray", "spark", "streaming"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.942580+00:00"
---

AWS Glue Job은 AWS Glue에서 ETL(Extract, Transform, Load) 작업을 실제로 실행하는 실행 단위입니다.

---

## 한 줄 정의

> **AWS Glue Job은 데이터를 읽고, 변환하고, 다른 저장소로 적재하는 ETL 로직을 실행하는 Glue의 핵심 실행 객체입니다.**

---

## Glue Job의 역할

- 데이터 추출: S3, JDBC, DynamoDB 등
- 데이터 변환: 정제, 타입 변환, 조인, 집계
- 데이터 적재: S3, Redshift, RDS 등

👉 ETL의 “엔진” 역할

---

## Glue Job의 주요 유형

### 1️⃣ Spark ETL Job (가장 일반적)

- Apache Spark 기반
- PySpark 사용
- 대용량 데이터 처리에 적합

---

### 2️⃣ Python Shell Job

- Spark 없음
- 순수 Python 실행
- 소규모 파일 처리, API 호출, 제어 로직에 적합

---

### 3️⃣ Streaming Job

- 실시간 스트리밍 처리
- Kinesis / Kafka 연동

---

### 4️⃣ Ray Job (신규)

- Python 분산 처리
- ML/고급 처리 용도

---

## Glue Job의 핵심 구성 요소

|구성 요소|설명|
|---|---|
|Script|PySpark / Python 코드|
|IAM Role|S3, Redshift 접근 권한|
|Worker Type|처리 성능/비용|
|Worker 수|병렬 처리 정도|
|Job Bookmark|증분 처리|
|Retry|실패 시 재시도|

---

## Glue Job 실행 방식

- 수동 실행
- Glue Trigger
- Glue Workflow
- EventBridge
- API/CLI

---

## Glue Job 예시 (PySpark)

```python
datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": ["s3://bucket/input/"]},
    format="json"
)

mapped = ApplyMapping.apply(
    frame=datasource,
    mappings=[("id", "string", "id", "string")]
)

glueContext.write_dynamic_frame.from_options(
    frame=mapped,
    connection_type="s3",
    connection_options={"path": "s3://bucket/output/"},
    format="parquet"
)
```

---

## Glue Job vs Glue Workflow vs Trigger

| 항목            | 역할        |
| ------------- | --------- |
| Glue Job      | 실제 ETL 실행 |
| Glue Workflow | 여러 Job 묶기 |
| Glue Trigger  | 실행 조건/스케줄 |

---

## 언제 Glue Job을 쓰나?

- 데이터 레이크 ETL
- S3 ↔ Redshift 적재
- 대규모 배치 처리
- 증분 파이프라인

---

## 핵심 포인트

- “ETL 실행 단위” → Glue Job
- “PySpark 기반” → Glue Job
- “증분 처리” → Job Bookmark