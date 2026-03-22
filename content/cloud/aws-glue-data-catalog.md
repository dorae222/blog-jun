---
title: AWS Glue Data Catalog
slug: "aws-glue-data-catalog"
category: cloud
tags: ["athena", "aws", "aws-glue", "data-catalog", "etl", "glue-crawler", "metadata", "redshift-spectrum", "s3"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.866616+00:00"
---

**AWS Glue Data Catalog**는 **메타데이터(데이터에 대한 데이터)를 저장하고 관리하는 중앙 저장소**입니다. AWS 내 다양한 분석 및 처리 서비스들이 **데이터의 위치, 스키마, 포맷 등을 인식하도록 돕는 핵심 컴포넌트**입니다.

---

## 📘 AWS Glue Data Catalog란?

> **AWS Glue Data Catalog**는 Amazon S3, Amazon RDS, Redshift 등 다양한 데이터 소스에 존재하는 **데이터셋의 구조와 속성을 저장하는 메타데이터 저장소**입니다.  
> 여러 AWS 서비스가 **데이터에 손쉽게 접근하고 처리**할 수 있도록 돕는 역할을 합니다.

---

## 🔍 주요 구성 요소

|구성 요소|설명|
|---|---|
|**데이터베이스 (Database)**|논리적으로 카탈로그 항목을 그룹화하는 단위 (예: `marketing_db`, `sales_db`)|
|**테이블 (Table)**|실제 데이터셋에 대한 정의(스키마 정보, 포맷, 위치 등)|
|**파티션 (Partition)**|테이블을 세분화하여 쿼리 성능을 향상시키는 단위 (예: 날짜별 디렉터리)|
|**Crawler (크롤러)**|데이터 소스를 스캔해 자동으로 테이블과 스키마를 생성하는 도구|

---

## 🎯 왜 중요한가?

- AWS Glue, Athena, Redshift Spectrum, EMR, SageMaker 등 다양한 서비스가 Glue Catalog를 사용해 **데이터를 인식**합니다.
- 데이터 파일이 S3 등에 저장되어 있어도, 해당 데이터의 **위치와 구조 정보를 제공하는 역할은 Glue Catalog가 담당**합니다.

---

## 🛠️ 사용 예시

### 1. **Amazon S3에 저장된 CSV 파일을 분석**

- Glue Crawler로 S3 데이터를 스캔합니다.
- Glue Catalog에 테이블이 생성됩니다.
- Athena에서 SQL 쿼리를 수행합니다 → `SELECT * FROM my_catalog.my_table`

### 2. **ETL 작업에서 메타데이터 자동 연결**

- AWS Glue Job에서 테이블 이름만 지정하면 소스의 위치와 스키마가 자동으로 연결됩니다.

---

## 🧠 Glue Catalog vs 다른 메타데이터 저장소

|항목|Glue Catalog|
|---|---|
|용도|메타데이터 저장소 (데이터 정의만 관리)|
|데이터 저장|❌ 실제 데이터는 S3 등 외부에 위치함|
|자동 생성|✅ 크롤러로 테이블을 자동 생성 가능|
|연결 가능 서비스|Glue, Athena, Redshift Spectrum, EMR, Lake Formation 등|

---

## ✅ 요약

> **AWS Glue Data Catalog**는 AWS 전반의 분석 서비스에서 사용하는 **중앙 메타데이터 저장소**입니다.  
> 데이터의 위치, 스키마, 포맷 등의 정보를 관리하여 S3 같은 원시 데이터와 분석 도구를 **효율적으로 연결**해줍니다.