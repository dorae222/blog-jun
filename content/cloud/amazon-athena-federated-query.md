---
title: Amazon Athena Federated Query
slug: "amazon-athena-federated-query"
category: cloud
tags: ["amazon-athena", "aws", "aws-lambda", "data-integration", "dynamodb", "federated-query", "jdbc", "s3"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.209765+00:00"
---

**Amazon Athena Federated Query**는 Athena에서 **S3 외부의 다양한 데이터 소스**를 **ETL 없이 SQL로 직접 조회**할 수 있게 해주는 기능입니다.

---

## 한 줄 정의

> **Athena Federated Query는 Lambda 커넥터를 통해 외부 데이터 소스를 Athena SQL로 쿼리하는 서버리스 기능이다.**

---

## 왜 필요한가?

Athena는 기본적으로 **S3 데이터**만 쿼리합니다. 하지만 현실에서는 데이터가 여러 시스템(DB, NoSQL, SaaS 등)에 흩어져 있습니다.

👉 **Federated Query로 “한 번의 SQL”로 여러 소스를 조회할 수 있습니다.**

---

## 핵심 구조

```
Athena
  |
  | SQL Query
  |
Lambda Connector
  |
External Data Source
```

- Athena 쿼리 실행 시
- Lambda가 외부 소스에 연결해
- 결과를 Athena에 반환합니다

---

## 지원 데이터 소스 (대표)

|소스|지원|
|---|---|
|Amazon DynamoDB|✅|
|Amazon RDS (MySQL/PostgreSQL)|✅|
|Amazon Redshift|✅|
|Amazon OpenSearch|✅|
|JDBC 기반 DB|✅|
|Custom API|✅|

※ Lambda 커넥터로 확장 가능합니다

---

## 특징 요약

### 1️⃣ ETL 불필요

- 데이터 복제 없이 **실시간 조회**
- 최신 데이터에 즉시 접근 가능

---

### 2️⃣ 서버리스

- 인프라 관리 불필요
- 사용한 만큼만 비용 지불

---

### 3️⃣ 확장성

- 커넥터만 있으면 다양한 소스 연결 가능
- AWS 제공 커넥터와 커뮤니티 커넥터가 다수 존재

---

### 4️⃣ 성능 특성

- 일부 연산은 **pushdown**이 가능
- 네트워크 및 외부 소스 성능의 영향을 많이 받음
- 대용량 분석 작업에는 적합하지 않음

---

## 비용 모델

- Athena 쿼리 스캔 비용
- Lambda 실행 비용
- 외부 DB 리소스 비용

---

## 언제 사용하면 좋은가?

- 일회성 또는 Ad-hoc 분석
- 여러 소스의 데이터를 결합하여 조회할 때
- ETL 파이프라인 구축이 과도한 경우
- 서버리스 아키텍처를 선호할 때

❌ 대규모 반복 분석에는 부적합

---

## Athena Federated Query vs 일반 Athena

|항목|일반 Athena|Federated|
|---|---|---|
|데이터 위치|S3|S3 + 외부|
|엔진|Presto/Trino|Presto/Trino + Lambda|
|성능|높음|상대적으로 낮음|
|용도|대용량 분석|소규모 실시간 조회|
