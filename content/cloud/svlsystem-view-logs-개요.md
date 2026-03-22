---
title: SVL(System View Logs) 개요
slug: "svlsystem-view-logs-개요"
category: cloud
tags: ["amazon-redshift", "aws", "database", "monitoring", "performance", "redshift", "sql", "stl", "stv", "svl"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:07.951695+00:00"
---

## SVL이란?

**SVL(System View Logs)**은
Amazon Redshift의 **STL(System Table Logs)과 STV(System Table Views)를 결합해 제공하는 요약 뷰(View)**입니다.

> ✔️ 과거 실행 기록 + 요약 정보  
> ✔️ STL보다 쉽게 조회  
> ✔️ STV보다 오래 유지  
> ✔️ 읽기 전용

---

## 한 줄 정의

> **SVL은 Redshift 쿼리 실행 정보를 로그와 뷰를 결합해 제공하는 요약 시스템 뷰다.**

---

## STL / STV / SVL 비교 (중요)

|구분|STL|STV|SVL|
|---|---|---|---|
|의미|로그 테이블|실시간 뷰|로그 요약 뷰|
|데이터|상세|현재 상태|요약|
|유지 기간|제한적|순간|제한적|
|사용 목적|분석·감사|실시간 모니터링|빠른 분석|
|난이도|높음|중간|낮음|

---

## SVL의 주요 장점

- STL 여러 테이블을 직접 조인할 필요 없음 ❌
- 쿼리 성능 분석이 쉬움
- 운영 보고에 적합

---

## 자주 쓰는 SVL 뷰 예시

### 1️⃣ 쿼리 요약

```sql
SELECT * FROM svl_qlog;
```

### 2️⃣ 오류/경고 요약

```sql
SELECT * FROM svl_error_log;
```

### 3️⃣ 사용자별 쿼리

```sql
SELECT * FROM svl_userlog;
```

---

## 언제 SVL을 쓰나?

- 쿼리 실행 이력을 간단히 보고 싶을 때
- 운영 리포트 작성 시
- 빠른 성능 분석이 필요할 때

---

## 포인트

- **SVL = 요약 뷰**
- STL은 상세 로그
- STV는 실시간
- “빠른 분석/요약” → SVL