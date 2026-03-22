---
title: Amazon Redshift Table
slug: "amazon-redshift-table"
category: cloud
tags: ["aws", "columnar-storage", "compression", "data-warehouse", "distribution", "olap", "redshift", "security", "sort-key"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.658167+00:00"
---

**Amazon Redshift Table**은 Redshift 데이터 웨어하우스 내부에서 **실제 데이터를 물리적으로 저장**하며, 대규모 분석 쿼리를 빠르게 처리하기 위한 **기본 데이터 저장 단위**입니다.

---

## 한 줄 정의

> **Amazon Redshift Table은 컬럼 지향 방식으로 데이터를 저장해 대용량 분석(OLAP)을 효율적으로 수행하는 물리적 테이블 객체이다.**

---

## Redshift Table의 핵심 특징

### 1️⃣ 물리적 데이터 저장 ✅

- 데이터가 **디스크에 실제로 저장**됩니다.
- View와 달리 결과가 아닌 **원본 데이터**를 보관합니다.

---

### 2️⃣ 컬럼 지향 저장 (Columnar Storage)

- 컬럼별로 데이터를 저장합니다.
- 필요한 컬럼만 읽어 **I/O를 최소화**합니다.
- 분석 쿼리에 최적화되어 있습니다.

---

### 3️⃣ 분산 저장 (Distribution)

- 테이블이 **여러 노드에 분산**되어 저장됩니다.
- 병렬 처리로 성능이 향상됩니다.

분산 방식:

- **KEY**: 특정 컬럼을 기준으로 분산합니다.
- **EVEN**: 균등하게 분산합니다.
- **ALL**: 모든 노드에 복제합니다 (소형 테이블에 적합).

---

### 4️⃣ 정렬 키 (Sort Key)

- 디스크 상에서 **정렬된 상태로 저장**됩니다.
- 범위 필터링 및 조인 성능을 향상시킵니다.

종류:

- **COMPOUND**
- **INTERLEAVED**

---

### 5️⃣ 자동 압축 (Encoding)

- 컬럼별로 최적의 압축을 적용합니다.
- 저장 비용을 절감합니다.
- 스캔 속도가 향상됩니다.

---

## 기본 생성 예시

```sql
CREATE TABLE orders (
    order_id BIGINT,
    customer_id BIGINT,
    order_date DATE,
    amount DECIMAL(10,2)
)
DISTKEY(customer_id)
SORTKEY(order_date);
```

---

## Redshift Table vs 다른 객체

|객체|데이터 저장|용도|
|---|---|---|
|Table|✅|원본/팩트 데이터|
|View|❌|논리적 쿼리|
|Materialized View|✅|성능 최적화|
|External Table|❌|S3 데이터 조회|

---

## Redshift Table의 보안

- RBAC(Role-Based Access Control)
- Row-Level Security (RLS)
- Column-Level Security (CLS)
- Dynamic Data Masking

---

## 운영 관련 포인트

### 데이터 로드

- `COPY` 명령 (S3, DynamoDB 등)을 사용합니다.
- 병렬 로드를 지원합니다.

### 데이터 변경

- INSERT / UPDATE / DELETE / MERGE를 지원합니다.
- VACUUM / ANALYZE가 필요합니다 (클러스터 운영 시).

---

## 언제 Redshift Table을 쓰나?

- 대규모 분석 데이터 저장에 적합합니다.
- 반복적 집계 및 리포팅에 적합합니다.
- 데이터 웨어하우스의 핵심 저장소로 사용됩니다.

---

## 시험 대비 핵심 문장

> **Redshift Table은 컬럼 지향·분산 저장을 사용하는 분석용 물리 테이블이다.**