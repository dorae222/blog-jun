---
title: Amazon Redshift View(뷰) 개요
slug: "amazon-redshift-view뷰-개요"
category: cloud
tags: ["amazon-redshift", "data-governance", "late-binding-view", "materialized-views", "query-optimization", "security", "sql", "views"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.677304+00:00"
---

**Amazon Redshift View**는 Redshift에 저장된 데이터를 **가상 테이블 형태로 정의**하여 복잡한 쿼리를 단순화하고, 보안·재사용성·관리성을 향상시키기 위해 사용하는 SQL 객체입니다.

---

## 한 줄 정의

> **Amazon Redshift View는 실제 데이터를 저장하지 않고, 저장된 SQL 정의를 실행 결과처럼 보여주는 논리적 테이블입니다.**

---

## View의 핵심 특징

### 1️⃣ 물리적 데이터 저장 여부

- View 자체에는 데이터가 저장되지 않습니다.
- View를 조회하면 **기본 테이블을 실시간으로 쿼리**하여 결과를 반환합니다.

---

### 2️⃣ 쿼리 단순화

```sql
CREATE VIEW sales_summary AS
SELECT region, SUM(amount) total_sales
FROM sales
GROUP BY region;
```

이후:

```sql
SELECT * FROM sales_summary;
```

➡️ 복잡한 쿼리를 반복해서 작성할 필요가 없습니다.

---

### 3️⃣ 보안(Access Control)

- 특정 컬럼을 숨기거나(마스킹)
- 특정 조건의 행만 노출하도록 행 수준 필터링을 적용할 수 있습니다.
- 사용자에게 기본 테이블 대신 **View에 대한 권한만 부여**하면 안전하게 접근 제어가 가능합니다.

```sql
GRANT SELECT ON sales_summary TO analyst_role;
```

---

### 4️⃣ 항상 최신 데이터

- 기본 테이블이 변경되면 View의 결과도 **즉시 반영**됩니다.

---

## View vs Materialized View

|구분|View|Materialized View|
|---|---|---|
|데이터 저장|❌|✅|
|조회 속도|기본 테이블 의존|빠름|
|최신성|실시간|새로고침 필요|
|비용|쿼리 시 비용|저장 + refresh 비용|
|용도|단순화/보안|성능 최적화|

---

## Redshift View의 종류

### 1️⃣ Standard View

- 일반적인 View로, 항상 실시간 결과를 반환합니다.

### 2️⃣ Late-binding View

```sql
CREATE VIEW v1 AS
SELECT * FROM schema.table;
```

```sql
CREATE VIEW v2 AS
SELECT * FROM schema.table
WITH NO SCHEMA BINDING;
```

|항목|Standard|Late-binding|
|---|---|---|
|테이블 변경 영향|있음|없음|
|참조 테이블 존재 여부|필요|불필요|
|Spectrum/외부 테이블|제한|지원|
|권장 사용처|내부 테이블|외부/유연성|

---

## 보안과 View

Redshift View는 다음과 같은 보안 패턴에 자주 사용됩니다:

- 민감한 컬럼을 숨기기(마스킹)
- 특정 조건의 행만 노출
- RBAC(Role-Based Access Control)와 결합하여 권한 관리

예:

```sql
CREATE VIEW masked_customer AS
SELECT id, '****' || RIGHT(ssn, 4) AS ssn
FROM customer;
```

---

## 언제 View를 사용해야 하나?

- 동일한 쿼리를 여러 곳에서 재사용할 때
- 사용자에게 **부분 데이터만 노출**해야 할 때
- 스키마 변경 가능성이 높아 유연하게 대응해야 할 때
- 성능보다 **관리성과 보안**이 우선일 때

---

## 요약

- Redshift View = **가상 테이블**
- 데이터 자체를 저장하지 않고 SQL 정의만 저장
- 보안·가독성·재사용성에 강점이 있음
- 성능 개선이 필요하면 **Materialized View**를 고려하세요.