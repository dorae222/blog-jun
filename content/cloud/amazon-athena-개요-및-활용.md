---
title: Amazon Athena 개요 및 활용
slug: "amazon-athena-개요-및-활용"
category: cloud
tags: ["amazon-athena", "analytics", "aws", "data-lake", "glue", "presto", "s3", "serverless", "sql"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.768115+00:00"
---

NOTE:
- serverless query service for analyzing data in Amazon S3 using SQL

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **서비스명**       | Amazon Athena |
| **유형**           | **서버리스 대화형 쿼리 서비스** |
| **주요 목적**       | Amazon S3에 저장된 데이터를 **표준 SQL**로 **분석**할 수 있도록 지원 |

> 💡 **Athena**는 인프라를 직접 관리할 필요 없이 S3에 저장된 데이터를 바로 쿼리할 수 있는 서버리스 서비스로,
> **대화형 분석, 로그 분석, 데이터 레이크 쿼리**에 적합합니다.

---

## 🔧 동작 방식

1. **데이터 소스**  
   - Amazon S3에 저장된 CSV, JSON, Parquet, ORC, Avro 등 다양한 포맷
2. **스키마 정의**  
   - AWS Glue Data Catalog를 통해 테이블 및 스키마를 정의
3. **SQL 쿼리 실행**  
   - ANSI SQL 표준 기반의 Presto/Trino 엔진으로 쿼리를 실행
4. **결과 반환 및 저장**  
   - 결과를 즉시 반환하고, 필요 시 S3에 결과 파일을 저장

---

## ✅ 주요 특징

| 항목 | 설명 |
|------|------|
| **서버리스** | 클러스터나 인프라를 직접 관리할 필요 없음 |
| **확장성** | 수 TB에서 PB 단위의 대용량 데이터를 병렬 처리 가능 |
| **다양한 포맷 지원** | CSV, JSON, Parquet, ORC 등 다양한 파일 포맷 지원 |
| **AWS 통합** | S3, Glue, QuickSight, Lake Formation과 긴밀히 통합 |
| **쿼리 기반 과금** | 스캔한 데이터 양(GB 단위)을 기준으로 요금이 청구됨 |

---

## 🧪 예시 쿼리

```sql
-- S3에 저장된 웹 로그 분석
SELECT user_id, COUNT(*) AS visit_count
FROM web_logs
WHERE status = 200
GROUP BY user_id
ORDER BY visit_count DESC
LIMIT 10;
````

```sql
-- CTAS(Create Table As Select) 활용
CREATE TABLE top_users
WITH (
  format = 'PARQUET',
  external_location = 's3://my-bucket/athena-output/'
) AS
SELECT user_id, COUNT(*) AS visit_count
FROM web_logs
GROUP BY user_id;
```

---

## 📊 활용 사례

- **로그 분석**: CloudFront, ELB, VPC Flow Logs 등 S3에 저장된 로그를 쿼리하여 분석

- **데이터 레이크 분석**: S3 기반 데이터 레이크에서 대화형 탐색 수행

- **ETL 간소화**: Glue ETL, Redshift Spectrum 등과 함께 사용하여 ETL 파이프라인 단순화

- **비즈니스 분석**: QuickSight와 연계해 대시보드와 시각화를 구현

---

## ⚠️ 유의사항

|항목|설명|
|---|---|
|**데이터 스캔 비용 최적화 필요**|Parquet/ORC 등 컬럼 기반 포맷과 파티셔닝을 사용해 스캔할 데이터 양을 줄이기 권장|
|**성능 최적화 필요**|불필요한 컬럼이나 행 스캔을 최소화해야 효율적임|
|**보안 연계**|IAM, Lake Formation, S3 버킷 정책 등으로 접근 제어와 보안 설정 필요|

---

## 🧾 요약

| 항목       | 설명                                       |
| -------- | ---------------------------------------- |
| **정의**   | Amazon S3 데이터를 표준 SQL로 서버리스 방식으로 분석할 수 있는 서비스 |
| **장점**   | 서버리스, 즉시 사용 가능, 대화형 쿼리, 다양한 포맷 지원           |
| **활용 예** | 로그 분석, 데이터 레이크 탐색, ETL 전처리, BI 연계        |