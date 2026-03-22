---
title: Amazon Redshift Federated Query 요약 및 Athena 비교
slug: "amazon-redshift-federated-query-요약-및-athena-비교"
category: cloud
tags: ["amazon-redshift", "athena", "aurora", "aws", "data-warehousing", "federated-query", "postgresql", "rds", "spectrum"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.603594+00:00"
---

**Amazon Redshift Federated Query**는 Redshift 클러스터에서 **외부 데이터베이스를 SQL로 직접 조회**할 수 있게 해주는 기능입니다.

---

## 한 줄 정의

> **Amazon Redshift Federated Query는 Redshift에서 RDS/Aurora 같은 외부 OLTP 데이터베이스를 ETL 없이 직접 쿼리하는 기능이다.**

---

## 무엇을 할 수 있나?

Redshift에 데이터를 적재하지 않고도 다음 DB에 있는 테이블을 **Redshift SQL로 조인·조회**할 수 있습니다:

- **Amazon RDS for PostgreSQL**
- **Amazon Aurora PostgreSQL**

---

## 핵심 특징

### 1️⃣ ETL 불필요

- 데이터 복제 없이 **실시간 조회**
- 데이터 최신성 보장

---

### 2️⃣ Redshift SQL 그대로 사용

```sql
SELECT *
FROM local_orders o
JOIN federated_db.public.customers c
  ON o.customer_id = c.id;
```

---

### 3️⃣ 외부 DB에서 실행(pushdown)

- 가능한 연산은 **외부 DB로 푸시다운**
- 네트워크 전송량 최소화

---

### 4️⃣ IAM + 보안 통합

- IAM 역할로 인증
- Secrets Manager로 DB 자격증명 관리
- VPC 프라이빗 연결

---

## 아키텍처 개요

```
Redshift Cluster
   |
   | Federated Query
   |
RDS / Aurora PostgreSQL
```

---

## 지원 대상

|데이터베이스|지원 여부|
|---|---|
|RDS PostgreSQL|✅|
|Aurora PostgreSQL|✅|
|RDS MySQL|❌|
|Aurora MySQL|❌|
|DynamoDB|❌|

👉 **PostgreSQL 계열만 지원** (시험 포인트)

---

## Redshift Federated Query vs Spectrum

|항목|Federated Query|Spectrum|
|---|---|---|
|대상|외부 DB|S3 데이터|
|ETL|불필요|불필요|
|실시간성|실시간|파일 기반|
|주 용도|OLTP 참조|Data Lake|

---

## 언제 쓰면 좋나?

- 소량 참조 데이터
- 최신 데이터 즉시 필요
- ETL 지연 허용 불가
- 간단한 조인/조회

❌ 대용량 분석에는 부적합 (외부 DB 부하 위험)

---

## 시험 대비 핵심 문장

> **Redshift Federated Query는 PostgreSQL 계열 외부 DB를 Redshift에서 직접 쿼리하는 기능이다.**

---

## 요약

- ETL 없이 외부 DB 조회
- PostgreSQL 전용
- 실시간 최신 데이터
- 소규모·보조 쿼리에 적합


---

# Federated Query 비교 정리

## (Redshift vs Athena)

---

## 한 줄 요약

- **Redshift Federated Query**  
    → _Redshift에서 외부 OLTP DB를 직접 쿼리_
    
- **Athena Federated Query**  
    → _Athena에서 다양한 외부 데이터 소스를 SQL로 쿼리_
    
---

## 1️⃣ 기본 개념

|항목|Redshift Federated Query|Athena Federated Query|
|---|---|---|
|주체|Amazon Redshift|Amazon Athena|
|목적|DW에서 OLTP 데이터 직접 조회|서버리스 SQL로 다양한 외부 소스 조회|
|ETL 필요|❌|❌|
|실행 위치|Redshift 클러스터|Athena (Lambda 기반 커넥터)|

---

## 2️⃣ 지원 데이터 소스

### Redshift Federated Query

> **매우 제한적**

- Amazon RDS for **PostgreSQL**
- Amazon Aurora **PostgreSQL**

❌ MySQL, DynamoDB, MongoDB 등 미지원

---

### Athena Federated Query

> **범용·확장형**

- Amazon RDS (MySQL, PostgreSQL)
- Amazon DynamoDB
- Amazon Redshift
- Amazon OpenSearch
- Amazon Aurora
- Custom source (Lambda 커넥터)

👉 **Lambda 커넥터만 만들면 무엇이든 가능**

---

## 3️⃣ 아키텍처 차이

### Redshift Federated Query

```
Redshift Cluster
   |
   | SQL (Federated)
   |
RDS / Aurora PostgreSQL
```

- Redshift가 직접 외부 DB에 연결
- 일부 연산 **푸시다운**
- DW 중심 구조

---

### Athena Federated Query

```
Athena
   |
   | SQL
   |
Lambda Connector
   |
External Data Source
```

- Athena → Lambda → 외부 소스
- 완전 서버리스
- 커넥터별 성능 차이 큼

---

## 4️⃣ 성능 및 사용 적합성

|항목|Redshift FQ|Athena FQ|
|---|---|---|
|대용량 분석|❌|❌|
|소량 실시간 조회|✅|⚠️|
|DW 조인|✅|❌|
|스케일|클러스터 의존|서버리스|
|외부 DB 부하|중간|높을 수 있음|

---

## 5️⃣ 비용 모델

|항목|Redshift FQ|Athena FQ|
|---|---|---|
|인프라 비용|Redshift 노드 비용|Athena 스캔 비용 + Lambda|
|쿼리 비용|포함|쿼리 스캔 + Lambda 실행|
|상시 비용|있음|없음|

---

## 6️⃣ 보안 및 인증

|항목|Redshift FQ|Athena FQ|
|---|---|---|
|인증|IAM + Secrets Manager|IAM + Lambda 역할|
|네트워크|VPC 내부|VPC/퍼블릭 모두 가능|
|감사|CloudTrail|CloudTrail|

---

## 7️⃣ 언제 무엇을 써야 하나?

### Redshift Federated Query 선택

- 이미 Redshift 사용 중
- PostgreSQL 계열 DB만 필요
- DW 쿼리에서 최신 참조 데이터 필요
- ETL 지연 불가

### Athena Federated Query 선택

- 서버리스 환경 선호
- 다양한 소스 연결 필요
- 일회성/Ad-hoc 쿼리
- 커넥터 커스터마이징 필요

---

## 8️⃣ 시험 대비 핵심 문장

### Redshift Federated Query

> **Redshift에서 PostgreSQL 계열 외부 DB를 ETL 없이 직접 쿼리한다.**

### Athena Federated Query

> **Athena에서 Lambda 커넥터를 통해 다양한 외부 데이터 소스를 SQL로 조회한다.**

---

## 9️⃣ 한눈에 비교 요약

|구분|Redshift FQ|Athena FQ|
|---|---|---|
|중심 서비스|Redshift|Athena|
|서버리스|❌|✅|
|소스 다양성|낮음|높음|
|DW 통합|높음|낮음|
|시험 출제|잦음|잦음|

---

## 최종 정리 한 줄

> **DW 중심 + PostgreSQL 한정 → Redshift Federated Query**  
> **서버리스 + 다양한 소스 → Athena Federated Query**