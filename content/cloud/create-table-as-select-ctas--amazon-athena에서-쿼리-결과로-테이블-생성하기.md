---
title: CREATE TABLE AS SELECT (CTAS) — Amazon Athena에서 쿼리 결과로 테이블 생성하기
slug: "create-table-as-select-ctas--amazon-athena에서-쿼리-결과로-테이블-생성하기"
category: cloud
tags: ["amazon-athena", "aws", "ctas", "data-lake", "etl", "parquet", "s3", "sql"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.306655+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

---
aliases:
  - CTAS
---
## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | `CREATE TABLE AS SELECT` (CTAS) |
| **소속 서비스**     | Amazon Athena |
| **기능 유형**       | 쿼리 결과를 기반으로 새로운 테이블 생성

> 🛠️ **CTAS 문(CREATE TABLE AS SELECT)**은  
> **SELECT 쿼리 결과를 Amazon S3에 저장하고, 그 결과를 새로운 Athena 테이블로 등록**하는 기능입니다.

---

## 🧪 기본 문법

```sql
CREATE TABLE new_table_name
WITH (
  format = 'Parquet',
  external_location = 's3://my-bucket/output/',
  partitioned_by = ARRAY['col1'],
  bucketed_by = ARRAY['col2'],
  bucket_count = 4
) AS
SELECT col1, col2, col3
FROM existing_table
WHERE col4 > 100;
````

---

## ✅ 주요 옵션

|옵션 항목|설명|
|---|---|
|`format`|저장 포맷 (예: `Parquet`, `ORC`, `JSON`, `TEXTFILE`)|
|`external_location`|결과가 저장될 S3 경로 (생략 시 기본 위치 사용)|
|`partitioned_by`|파티셔닝할 컬럼 목록|
|`bucketed_by`|버킷화할 컬럼 목록|
|`bucket_count`|버킷 개수 (버킷 사용 시 필요)|

---

## 🎯 활용 목적

|사용 시나리오|설명|
|---|---|
|**쿼리 결과 캐싱**|자주 사용하는 SELECT 결과를 테이블로 만들어 빠르게 재사용할 수 있습니다.|
|**데이터 포맷 변경**|CSV → Parquet 등 효율적인 포맷으로 변환하여 저장할 때 유용합니다.|
|**S3 테이블 분리**|큰 테이블에서 필요한 컬럼이나 행만 선택해 별도로 저장할 수 있습니다.|
|**ETL 후 저장**|정제된 결과를 새 테이블로 저장해 후속 분석에 활용합니다.|

---

## 🧾 장점

|항목|설명|
|---|---|
|**결과 저장 + 메타 등록**|데이터 파일과 테이블 정의를 동시에 생성합니다.|
|**쿼리 비용 절감**|정제된 결과만 저장하면 이후 분석 시 비용을 줄일 수 있습니다.|
|**Parquet 등 포맷 최적화**|압축 및 컬럼 단위 저장으로 성능이 향상됩니다.|
|**분할 관리 용이**|파티셔닝 및 버킷화 설정을 통해 데이터 관리가 쉬워집니다.|

---

## ⚠️ 주의사항

|항목|설명|
|---|---|
|**기본 저장 위치**|`query result location` 또는 명시적 `external_location`를 지정해야 합니다.|
|**기존 테이블 덮어쓰기 안 됨**|동일한 이름의 테이블이 이미 있으면 오류가 발생합니다.|
|**기본 테이블은 관리형(managed)**|`EXTERNAL` 테이블로 만들려면 `external_location`을 반드시 지정해야 합니다.|

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|SELECT 쿼리 결과를 기반으로 **새로운 Athena 테이블과 S3 저장 파일을 동시에 생성**하는 명령입니다.|
|**활용 예**|결과 캐싱, 포맷 변경, ETL 저장, 파티셔닝 등 다양한 목적에 활용할 수 있습니다.|
|**주요 포인트**|WITH 절을 통해 포맷과 저장 위치를 명시하는 것이 필수적입니다.|
