---
title: Apache Iceberg — 데이터 레이크를 위한 차세대 테이블 포맷
slug: "apache-iceberg--데이터-레이크를-위한-차세대-테이블-포맷"
category: cloud
tags: ["apache-iceberg", "athena", "aws", "data-lake", "flink", "lakehouse", "s3", "schema-evolution", "spark", "time-travel"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.107139+00:00"
---

**Apache Iceberg**는 대규모 데이터 레이크에서 **테이블을 안정적·일관되게 관리**하기 위한 **오픈소스 테이블 포맷(Table Format)**입니다. Amazon S3 같은 객체 스토리지 위에서 **데이터 웨어하우스 수준의 신뢰성**을 제공하도록 설계되었습니다.

---

## 한 줄 정의

> **Apache Iceberg는 S3·HDFS 같은 데이터 레이크 위에서 ACID 트랜잭션, 스키마 진화, 시간 여행을 제공하는 차세대 테이블 포맷입니다.**

---

## 왜 Iceberg가 필요한가?

기존 데이터 레이크(Parquet/ORC + Hive 메타스토어)는 다음과 같은 문제를 가지고 있습니다:

- 동시 쓰기 시 데이터 손상 가능
- 스키마 변경이 어려움
- 파티션 관리 복잡
- 데이터 변경(UPDATE/DELETE/MERGE) 비효율

👉 **Iceberg는 이러한 문제들을 근본적으로 해결**합니다.

---

## 핵심 기능

### 1️⃣ ACID 트랜잭션

- **원자적 커밋** 보장
- 여러 작업자가 동시에 읽고 써도 **일관성 유지**
- 실패 시 자동 롤백

---

### 2️⃣ 스키마 진화 (Schema Evolution)

- 컬럼 **추가 / 삭제 / 이름 변경 / 타입 변경** 지원
- 기존 데이터를 재작성할 필요 없이 적용 가능

---

### 3️⃣ 파티션 진화 (Hidden Partitioning)

- 사용자는 `WHERE date = '2024-01-01'`만 작성하면 됨
- Iceberg가 내부적으로 최적 파티션을 처리
- 파티션 변경 시 쿼리 수정 불필요

---

### 4️⃣ Time Travel (시간 여행)

- 과거 시점의 테이블을 조회 가능

```sql
SELECT * FROM table
FOR TIMESTAMP AS OF '2024-01-01 00:00:00';
```

- 데이터 감사, 디버깅, 롤백에 유용

---

### 5️⃣ UPDATE / DELETE / MERGE 지원

- 기존 데이터 레이크에서 어렵던 **행 단위 변경**이 가능
- CDC, GDPR(삭제 요청) 처리에 적합

---

## 아키텍처 개요 (간단)

```
Query Engine (Spark / Flink / Trino / Athena / Snowflake*)
        ↓
   Iceberg Metadata
   (Snapshots, Manifests)
        ↓
   Parquet / ORC / Avro Files
        ↓
   Object Storage (S3, HDFS)
```

---

## 지원 엔진

- Apache Spark
- Apache Flink
- Trino / Presto
- Amazon Athena
- Amazon EMR
- Snowflake (읽기 지원)
- Dremio

---

## Iceberg vs 다른 테이블 포맷

|기능|Iceberg|Delta Lake|Hudi|
|---|---|---|---|
|ACID|✅|✅|✅|
|Time Travel|✅|✅|제한|
|Hidden Partitioning|✅|❌|❌|
|Engine 독립성|**매우 높음**|Spark 중심|제한적|
|대규모 테이블|**최적**|좋음|좋음|

---

## AWS에서 Iceberg

- **Amazon Athena**: Iceberg 테이블 쿼리 가능
- **AWS Glue Data Catalog**: 메타데이터 관리
- **Amazon EMR / Spark / Flink**: ETL & 스트리밍
- **S3 + Iceberg**: 대표적인 Lakehouse 아키텍처

---

## 언제 Iceberg를 써야 하나?

- 데이터 레이크에서 **UPDATE/DELETE/MERGE**가 필요할 때
- 여러 엔진에서 같은 데이터를 **공유**해야 할 때
- 파티션 설계 변경이 잦을 때
- 대규모 분석과 높은 신뢰성이 필요할 때

---

## 요약

- Apache Iceberg = **데이터 레이크의 테이블 관리 표준**
- Data Lake와 Data Warehouse의 장점을 결합한 **Lakehouse 핵심 기술**
- 현대 데이터 플랫폼에서 **사실상 필수 구성 요소**
