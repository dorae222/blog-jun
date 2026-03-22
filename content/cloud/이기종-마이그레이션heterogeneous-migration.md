---
title: 이기종 마이그레이션(Heterogeneous Migration)
slug: "이기종-마이그레이션heterogeneous-migration"
category: cloud
tags: ["aws", "aws-dms", "aws-sct", "database-migration", "dynamodb", "heterogeneous-migration", "mysql", "oracle", "postgresql", "rds"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:08.303953+00:00"
---

**이기종 마이그레이션(Heterogeneous Migration)**은 **서로 다른 데이터베이스 엔진 또는 구조 간의 마이그레이션**을 의미합니다.

---

## 🔄 이기종 마이그레이션(Heterogeneous Migration)이란?

> **이기종 마이그레이션**은 소스 데이터베이스와 대상 데이터베이스가 **서로 다른 유형(엔진)**일 때 수행하는 마이그레이션을 말합니다.

즉, **관계형 DB → NoSQL DB**, 또는
**Oracle → PostgreSQL**, **MySQL → DynamoDB** 등
**DB 구조, 쿼리 언어, 저장 방식이 다른 시스템 간의 이전 작업**을 의미합니다.

---

## 🔁 반대로, 동종 마이그레이션(Homogeneous Migration)

> 소스와 대상이 **같은 DB 엔진**인 경우 (예: RDS MySQL → RDS MySQL)

---

## 🧪 본문 예시 적용

- **현재:** RDS DB 인스턴스 (예: MySQL, PostgreSQL, Oracle 등 **관계형 데이터베이스**)
    
- **대상:** Amazon **DynamoDB** (NoSQL 키-값 또는 문서형 데이터베이스)
    
- → 관계형 → NoSQL  
    ✅ 따라서 이건 **이기종 마이그레이션**입니다.
    
---

## ⚙️ 이기종 마이그레이션 시 필요한 것들

| 항목 | 설명 |
| ---------------------------------------------- | -------------------------------------------------------- |
| **스키마 변환** | 테이블 구조, 데이터 타입, 관계 등을 NoSQL 모델로 재설계 필요 |
| **SQL → API 전환** | RDS는 SQL 기반, DynamoDB는 API 기반 읽기/쓰기 |
| **AWS SCT 사용** | 스키마 자동 변환을 위해 **AWS Schema Conversion Tool (SCT)** 사용 권장 |
| **AWS DMS 지원** | 실제 데이터 이동은 **AWS DMS**로 가능 (실시간 복제 포함) |

---

## ✅ 요약

| 항목 | 내용 |
| ------ | ------------------------------------------ |
| 용어 | **이기종 마이그레이션 (Heterogeneous Migration)** |
| 의미 | 소스와 대상이 **다른 DB 엔진 또는 구조**일 때의 마이그레이션 |
| 예시 | RDS → DynamoDB, Oracle → Aurora PostgreSQL |
| 도구 | **AWS DMS**, **AWS SCT** 필요 |
| 본문과 관련 | 관계형 RDS → NoSQL DynamoDB → ✅ 이기종 마이그레이션 맞음 |
