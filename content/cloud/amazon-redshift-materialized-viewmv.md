---
title: Amazon Redshift Materialized View(MV)
slug: "amazon-redshift-materialized-viewmv"
category: cloud
tags: ["amazon-redshift", "data-warehouse", "incremental-refresh", "materialized-view", "mv", "performance-tuning", "query-optimization", "refresh", "sql"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.628372+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

**Amazon Redshift Materialized View(MV)** 는
쿼리 결과를 **물리적으로 저장**해 두어 **조회 성능을 크게 향상**시키는 Redshift 객체입니다.

---

## 한 줄 정의

> **Amazon Redshift Materialized View는 SELECT 쿼리 결과를 디스크에 저장해 두고, 필요 시 새로 고쳐 사용하는 고성능 캐시형 뷰입니다.**

---

## 왜 Materialized View가 필요한가?

일반 View는 조회할 때마다 기본 테이블을 다시 스캔합니다.
반면 **Materialized View는 미리 계산된 결과를 저장**하므로:

- 대용량 테이블 집계
    
- 복잡한 조인
    
- 반복 조회되는 리포트
    

에서 **쿼리 시간이 극적으로 감소**합니다.

---

## 핵심 특징

### 1️⃣ 물리적 데이터 저장 ✅

- 결과를 Redshift 스토리지에 저장
    
- 일반 테이블처럼 빠르게 조회 가능
    

---

### 2️⃣ 새로 고침(Refresh) 필요

```sql
REFRESH MATERIALIZED VIEW sales_mv;
```

- 새 데이터를 반영하려면 **명시적 새로 고침**이 필요합니다.

- 자동 새로 고침은 스케줄링을 통해 구현할 수 있습니다.

---

### 3️⃣ 쿼리 재작성(Query Rewrite)

- 조건이 맞으면 Redshift 옵티마이저가
    
    - 원본 쿼리 → MV로 **자동 대체**합니다.
        
- 사용자는 MV를 직접 조회하지 않아도 옵티마이저가 대체해 줍니다.
    

---

### 4️⃣ Incremental Refresh (제한적)

- 특정 조건을 만족하면
    
    - 변경분만 반영하는 **증분 새로 고침**을 지원합니다.
        
- 다만 모든 쿼리가 증분 새로 고침 대상으로 적합한 것은 아닙니다.
    

---

## 기본 사용 예시

```sql
CREATE MATERIALIZED VIEW daily_sales_mv
AS
SELECT order_date, SUM(amount) total_sales
FROM orders
GROUP BY order_date;
```

조회:

```sql
SELECT * FROM daily_sales_mv;
```

새로 고침:

```sql
REFRESH MATERIALIZED VIEW daily_sales_mv;
```

---

## View vs Materialized View

|항목|View|Materialized View|
|---|---|---|
|데이터 저장|❌|✅|
|성능|느림|매우 빠름|
|최신성|항상 최신|Refresh 시점 기준|
|스토리지 비용|없음|발생|
|사용 목적|단순화/보안|성능 최적화|

---

## Redshift MV의 제약 사항 (시험 포인트)

- 일부 SQL만 지원합니다.
    
- 비결정적 함수는 제한됩니다.
    
- 모든 MV가 증분 refresh 가능한 것은 아닙니다.
    
- 기본 테이블 변경 시 **자동 반영되지 않습니다.**
    

---

## 언제 Materialized View를 써야 하나?

- 동일한 집계/조인 쿼리가 **반복 실행**될 때
    
- 리포트/대시보드 성능이 중요할 때
    
- 약간의 데이터 지연을 허용할 수 있을 때
    
- 쿼리 비용 감소가 목표일 때
    

---

## 운영 팁

- **Query Editor v2 Scheduled Queries**로 refresh를 자동화하세요.

- 사용 빈도가 낮은 MV는 refresh 주기를 늘리세요.

- MV는 전용 스키마로 관리하면 편리합니다.

---

## 요약

- Materialized View = **결과를 저장하는 고성능 뷰**
    
- 성능 ↔ 최신성의 트레이드오프가 있습니다.
    
- Redshift 성능 튜닝의 핵심 기능입니다.
