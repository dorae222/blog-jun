---
title: Amazon Redshift Spectrum
slug: "amazon-redshift-spectrum"
category: cloud
tags: ["amazon-redshift", "analytics", "aws-glue", "big-data", "data-lake", "parquet", "redshift-spectrum", "s3", "sql"]
status: published
post_type: tutorial
quality_score: 9.0
created_at: "2026-03-02T01:08:05.646266+00:00"
---

**Amazon Redshift Spectrum**은
Amazon Redshift 클러스터에서 **S3에 저장된 데이터를 직접 쿼리할 수 있도록 해주는 기능**입니다.
즉, Redshift 테이블뿐만 아니라 **Amazon S3의 데이터 레이크에 있는 데이터까지 통합 분석**할 수 있게 해줍니다.

---

## 📌 Amazon Redshift Spectrum이란?

> **Redshift Spectrum**은
> Amazon Redshift 외부의 **Amazon S3에 저장된 데이터를 SQL로 쿼리할 수 있게 해주는 분석 기능**입니다.

- 데이터를 Redshift에 로딩하지 않고도 **S3 데이터에 직접 접근**할 수 있습니다.
- **표준 ANSI SQL**을 사용하여 Redshift와 동일한 방식으로 쿼리할 수 있습니다.
- Redshift의 저장소와 **S3 데이터 레이크를 통합 분석**할 수 있습니다.

---

## 🎯 언제 쓰나?

|사용 시나리오|예시|
|---|---|
|**데이터 레이크 분석**|데이터가 S3에 저장되어 있고, 그대로 분석하고 싶을 때|
|**저장비용 절감**|자주 사용하지 않는 데이터는 Redshift에 로딩하지 않고 S3에서 직접 조회|
|**대용량 로그 분석**|웹 로그, IoT 데이터 등 대규모 데이터를 별도로 적재하지 않고 바로 분석|
|**ETL 단계 줄이기**|데이터를 Redshift에 이동하지 않고 S3에 있는 원본 데이터를 기반으로 쿼리|

---

## 🧩 구성 요소

|구성 요소|설명|
|---|---|
|**Amazon S3**|외부 데이터 저장소 (CSV, Parquet, ORC 등)|
|**Redshift 클러스터**|사용자 쿼리를 실행하는 SQL 인터페이스|
|**Redshift Spectrum**|S3에 있는 데이터를 Redshift SQL 엔진과 연결해주는 중간 계층|
|**AWS Glue Data Catalog**|S3에 저장된 데이터의 **스키마를 정의**하고 **테이블화** (메타데이터 역할)|

---

## 🧪 작동 방식

1. S3에 있는 데이터 파일을 AWS Glue 또는 Athena를 통해 **스키마 등록**합니다.
2. Redshift에서 `CREATE EXTERNAL SCHEMA` 및 `EXTERNAL TABLE`을 생성합니다.
3. `SELECT` 쿼리로 Redshift에서 S3 데이터를 직접 분석합니다.
4. 분석 결과는 Redshift에서 반환되며, S3의 원본 데이터는 이동하지 않습니다.

---

## ✅ 장점

|장점|설명|
|---|---|
|**저비용 저장 + 고성능 분석**|S3의 저렴한 저장비 + Redshift의 분석 성능 결합|
|**데이터 복제 불필요**|S3 데이터를 Redshift로 복사하지 않아도 됨|
|**확장성**|Spectrum은 **분리된 컴퓨팅 리소스를 사용**하여 대규모 쿼리 확장|
|**표준 SQL 사용**|별도 언어나 툴 없이 기존 SQL로 분석 가능|
|**데이터 레이크 통합**|Redshift 안에서 **RDB + S3 데이터 레이크를 함께 분석**|

---

## ⚠️ 주의 사항

|항목|내용|
|---|---|
|포맷|성능을 위해 **Parquet/ORC 등 열 지향 포맷 권장**|
|파티셔닝|**S3 데이터 파티셔닝 구조와 매핑** 중요 (필터링 성능에 영향)|
|비용|Spectrum 쿼리는 **스캔한 바이트 수 기준으로 요금 부과됨**|
|Glue Catalog|테이블 및 스키마 관리에는 **Glue 데이터 카탈로그 필수**|

---

## 📝 예제 쿼리

```sql
-- 외부 스키마 생성
CREATE EXTERNAL SCHEMA spectrum_schema
FROM data catalog
DATABASE 'spectrumdb'
IAM_ROLE 'arn:aws:iam::123456789012:role/MyRedshiftRole'
REGION 'us-west-2';

-- 외부 테이블 생성
CREATE EXTERNAL TABLE spectrum_schema.s3_sales_data (
  id INT,
  region STRING,
  amount FLOAT
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION 's3://mybucket/sales/';

-- 쿼리 실행
SELECT region, SUM(amount)
FROM spectrum_schema.s3_sales_data
GROUP BY region;
```

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**Amazon Redshift Spectrum**|
|목적|**S3 데이터를 Redshift에서 직접 쿼리**|
|필요 구성|Redshift 클러스터 + S3 + AWS Glue Catalog|
|장점|비용 절감, 데이터 복제 제거, 데이터 레이크 통합 분석|
|요금|**S3에서 스캔한 데이터 양 기준**으로 청구|
