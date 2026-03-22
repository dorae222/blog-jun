---
title: "Aurora zero-ETL integration 개요"
slug: "aurora-zero-etl-integration-개요"
category: cloud
tags: ["amazon-redshift", "aurora", "aws", "data-replication", "dms", "etl", "glue", "real-time-analytics", "zero-etl"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.808457+00:00"
---

**Aurora zero-ETL integration**은
**Amazon Aurora의 트랜잭션 데이터를 별도의 ETL 파이프라인 없이 Amazon Redshift로 거의 실시간 동기화**해 주는 **관리형 통합 기능**입니다.

---

## 한 줄 정의

> **Aurora zero-ETL integration은 Aurora의 변경 데이터를 자동으로 Redshift로 복제해 분석에 바로 쓰게 해주는 ‘ETL 없는’ 통합이다.**

---

## 왜 필요한가?

전통적으로는:

- Aurora → DMS/Glue → S3/Redshift
- 파이프라인 구축·운영 부담
- 지연(latency) 발생

👉 **zero-ETL은 이 모든 과정을 제거**합니다.

---

## 핵심 특징

### 1️⃣ ETL 파이프라인 불필요

- **AWS DMS, Glue, Lambda 없음**
- 설정 몇 번으로 자동 동기화 시작

---

### 2️⃣ 거의 실시간 복제

- Aurora에서 **INSERT/UPDATE/DELETE 발생**
- Redshift에 **수 분 이내 반영**
- 운영 DB 성능 영향 최소화

---

### 3️⃣ 완전관리형

- 스케일링, 장애 처리, 재시도 자동
- 운영 오버헤드 최소

---

### 4️⃣ 분석에 최적화된 Redshift 사용

- 조인, 집계, 리포트는 Redshift에서 수행
- Aurora는 OLTP에 집중

---

## 지원 범위 (중요)

|항목|지원 여부|
|---|---|
|Aurora MySQL|✅|
|Aurora PostgreSQL|✅|
|대상 분석 엔진|**Amazon Redshift**|
|사용자 정의 변환|❌|
|다른 타깃(S3 등)|❌|

> ❗ “ETL 없음” = **변환 로직 없음**  
> (필요하면 Redshift 쿼리/MV로 처리)

---

## 동작 구조 (개념)

```
Aurora (OLTP)
  └─ change log
        ↓
Zero-ETL integration
        ↓
Amazon Redshift (OLAP)
```

- 내부적으로 변경 로그를 활용
- 애플리케이션 수정 불필요

---

## 언제 쓰면 좋은가?

- 운영 DB(Aurora)의 데이터를 **즉시 분석**해야 할 때
- **마케팅/운영 리포트**, 실시간 대시보드
- ETL 운영 인력을 최소화하고 싶을 때

---

## 언제 쓰기 어렵나?

- 복잡한 데이터 변환이 필요
- Redshift가 아닌 다른 타깃(S3, Athena 등)
- 완전 실시간(ms 단위)이 반드시 필요한 경우

---

## 시험 대비 핵심 포인트

- “Aurora → Redshift 실시간 분석”
- “ETL 관리 부담 최소”
- “운영 DB 성능 영향 최소”  
    → **Aurora zero-ETL integration**