---
title: Amazon Redshift Query Editor v2
slug: "amazon-redshift-query-editor-v2"
category: cloud
tags: ["amazon-redshift", "aws", "iam", "materialized-views", "query-editor", "scheduled-queries", "secrets-manager", "serverless", "sql"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.640343+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

## 한 줄 정의

> **Amazon Redshift Query Editor v2는 Redshift에 대해 SQL 작성, 실행, 결과 분석, 일정 실행까지 제공하는 AWS 관리형 웹 기반 통합 쿼리 도구이다.**

---

## 무엇을 할 수 있나?

### 1️⃣ SQL 작성 및 실행

- 브라우저에서 바로 SQL을 실행할 수 있음
- 클러스터 및 Serverless 환경 모두 지원
- 별도 세션 관리가 필요 없음

---

### 2️⃣ 쿼리 결과 시각화

- 결과를 테이블 형식으로 확인
- CSV로 다운로드 가능
- 쿼리 결과를 공유할 수 있음

---

### 3️⃣ 저장된 쿼리 관리

- 쿼리 저장 기능 제공
- 버전 관리 지원
- 팀 내 공유 가능

---

### 4️⃣ **Scheduled Queries (중요)**

- SQL을 **주기적으로 자동 실행** 가능
- Materialized View refresh 지원
- 집계 테이블 갱신에 활용
- 배치 작업을 대체할 수 있음

```sql
REFRESH MATERIALIZED VIEW sales_mv;
```

---

### 5️⃣ 권한·보안 통합

- IAM 인증 지원
- Secrets Manager와 연계
- RBAC(역할 기반 접근 제어) 지원

---

## Query Editor v2 vs psql / SQL Client

|항목|Query Editor v2|psql/Client|
|---|---|---|
|설치|❌|필요|
|스케줄링|✅|❌|
|브라우저 사용|✅|❌|
|IAM 연동|✅|제한|
|운영 자동화|**우수**|낮음|

---

## 언제 쓰면 좋은가?

- 운영 및 분석 팀에서 SQL만으로 작업을 수행할 때
- Materialized View를 자동으로 새로 고쳐야 할 때
- 서버를 별도 운영하지 않고 배치용 SQL을 실행할 때
- 빠른 운영 대응이 필요할 때

---

## 핵심 포인트

- “Redshift SQL 스케줄링” → **Query Editor v2**
- “Materialized View refresh 자동화” → **Query Editor v2**
- “웹 기반 Redshift 관리” → **Query Editor v2**
