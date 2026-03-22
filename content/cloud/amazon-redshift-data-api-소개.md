---
title: Amazon Redshift Data API 소개
slug: "amazon-redshift-data-api-소개"
category: cloud
tags: ["amazon-redshift", "aws", "aws-secrets-manager", "data-api", "eventbridge", "jdbc", "lambda", "odbc", "serverless", "step-functions"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.592952+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

## 한 줄 정의

> **Amazon Redshift Data API는 JDBC/ODBC 연결 없이 API 호출만으로 Redshift SQL을 실행·모니터링할 수 있는 관리형 API입니다.**

---

## 왜 Data API가 필요한가?

기존 방식은:

- JDBC/ODBC 드라이버가 필요함
- VPC 네트워크 설정이 필요함
- 장기 연결을 관리해야 함

👉 **Data API는 이 모든 부담을 제거합니다.**

---

## 핵심 특징

### 1️⃣ 서버리스 API 기반

- HTTPS API 호출 방식
- 보안 그룹·포트 등 네트워크 설정 불필요
- Lambda, Step Functions, EventBridge와 연동에 적합

---

### 2️⃣ 비동기 SQL 실행

- `ExecuteStatement`로 쿼리 실행 시작
- 실행 ID를 반환
- `GetStatementResult` / `DescribeStatement`로 상태 및 결과 조회

```text
START → RUNNING → FINISHED / FAILED
```

---

### 3️⃣ 자격 증명 관리 자동화

- IAM 기반 인증 사용
- AWS Secrets Manager와 연동
- DB 사용자/비밀번호를 코드에 노출할 필요 없음

---

### 4️⃣ 클러스터 & Serverless 모두 지원

- Redshift provisioned cluster 지원
- Redshift Serverless workgroup 지원

---

## 기본 동작 흐름

```text
Client (Lambda / App)
   ↓ ExecuteStatement
Redshift Data API
   ↓
Redshift
   ↓
Query Result / Status
```

---

## 주요 API 예시

### SQL 실행

```python
ExecuteStatement(
  Sql="INSERT INTO sales VALUES (...)",
  Database="dev",
  WorkgroupName="wg"
)
```

### 상태 확인

```python
DescribeStatement(Id="query-id")
```

---

## 언제 Data API를 쓰나?

- Lambda에서 Redshift 쿼리를 실행할 때
- 이벤트 기반 데이터 처리 파이프라인에서
- 배치 작업의 상태를 추적할 때
- VPC 접근이 어렵거나 네트워크 설정을 피하고 싶을 때

---

## Data API vs JDBC/ODBC

|항목|Data API|JDBC/ODBC|
|---|---|---|
|네트워크 연결|❌|필요|
|드라이버|❌|필요|
|비동기|✅|제한|
|서버리스 연계|**최적**|부적합|
|대화형 분석|❌|✅|

---

## 핵심 포인트

- "Lambda에서 Redshift SQL 실행" → **Data API**
- "네트워크 설정 없이" → **Data API**
- "비동기 SQL 실행" → **Data API**
