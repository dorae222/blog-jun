---
title: AWS SCT (Schema Conversion Tool)
slug: "aws-sct-schema-conversion-tool"
category: cloud
tags: ["aurora-postgresql", "aws", "aws-dms", "aws-sct", "database-migration", "data-migration", "oracle", "schema-conversion"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.340923+00:00"
---

---
Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
aliases:
  - AWS SCT
---
**AWS SCT**는 **AWS Schema Conversion Tool**의 약자로, AWS DMS(Database Migration Service)와 함께 사용되는 **데이터베이스 스키마 변환 도구**입니다.

---

## 🧩 AWS SCT (Schema Conversion Tool)란?

> **AWS SCT**는 기존 데이터베이스의 **스키마(구조, 테이블, 인덱스 등)**를 AWS에서 사용하는 데이터베이스 형식으로 **자동 변환**해주는 **무료 데스크톱 애플리케이션**입니다.

특히 서로 **다른 데이터베이스 엔진 간(이기종 간)** 마이그레이션을 할 때 유용합니다.

---

## 🧠 어떤 문제를 해결하나요?

- 예를 들어 **Oracle → Amazon Aurora PostgreSQL**과 같은 이기종 마이그레이션에서는:
    - 테이블, 뷰, 저장 프로시저, 함수 등 구조가 달라 수동으로 변환하기 번거롭고 오류가 발생하기 쉽습니다.
    - AWS SCT는 이러한 스키마를 자동으로 변환하여 **시간을 절약하고 오류를 줄여줍니다**.

---

## 🧰 주요 기능

|기능|설명|
|---|---|
|**스키마 자동 변환**|소스 DB → 대상 DB로 스키마 구조 자동 매핑|
|**변환 보고서 제공**|변환 가능한 항목과 변환 불가능한 항목을 요약|
|**수동 변환 가이드**|자동 변환이 되지 않는 항목에 대해 **개발자 가이드 제공**|
|**데이터 웨어하우스 지원**|OLTP DB → Amazon Redshift 전환 지원|
|**코드 변환**|SQL, PL/SQL, T-SQL 등 코드도 대상 DB 형식으로 변환 시도|

---

## 🧪 예시 시나리오

> 한 회사가 온프레미스 **Oracle 데이터베이스를 Amazon Aurora PostgreSQL**로 이전하려고 합니다.  
> AWS SCT를 사용하면 Oracle의 **테이블, 인덱스, 뷰, 함수 등 스키마 정의를 PostgreSQL 형식으로 변환**할 수 있습니다.  
> 변환 후에는 AWS DMS로 **데이터 자체를 마이그레이션**하면 됩니다.

---

## 🔄 AWS SCT vs. AWS DMS

|항목|AWS SCT|AWS DMS|
|---|---|---|
|역할|**스키마(구조) 변환**|**데이터 자체 마이그레이션**|
|언제 사용?|**이기종 간 마이그레이션 시 필수**|동종/이기종 모두 사용 가능|
|변환 범위|테이블, 뷰, 함수, 스토어드 프로시저 등|테이블의 **데이터 값**|

둘은 함께 사용하는 것이 일반적입니다.

---

## ✅ 요약

> **AWS SCT**는 이기종 데이터베이스 마이그레이션 시 **스키마 구조를 자동으로 변환**하는 데 사용되며,  
> **AWS DMS와 함께 사용하면 전체 DB 이전이 훨씬 쉽고 효율적**입니다.
