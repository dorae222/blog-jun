---
title: Athena Catalog(데이터 카탈로그) 개요
slug: "athena-catalog데이터-카탈로그-개요"
category: cloud
tags: ["athena", "aws", "data-catalog", "glue", "metadata", "s3", "sql"]
status: published
post_type: til
quality_score: 7.0
created_at: "2026-03-02T01:08:04.750924+00:00"
---

### 정의

> Catalog는 Athena가 쿼리할 데이터의 스키마와 위치를 정의하는 메타데이터 저장소입니다.

### 기본 Catalog

- `AwsDataCatalog`  
    → **AWS Glue Data Catalog 기반**
    
### Catalog가 관리하는 것

- 데이터베이스
- 테이블
- 컬럼
- 파티션
- 데이터 위치(S3)
    
### 예시

```sql
SELECT * FROM sales_db.orders;
```

|요소|Catalog 역할|
|---|---|
|sales_db|데이터베이스|
|orders|테이블|
|S3 위치|s3://bucket/path/|