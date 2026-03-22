---
title: Apache Hive
slug: "apache-hive"
category: cloud
tags: ["apache-hive", "aws-athena", "big-data", "data-lake", "hadoop", "hdfs", "hive", "s3", "schema-on-read", "sql-on-hadoop"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.096478+00:00"
---

> **NOTE:**
> 
> - **Hadoop 기반 SQL-on-BigData 엔진**
>     
> - **HDFS / S3(Data Lake)** 위 데이터를 **SQL(HiveQL)** 로 분석
>     
> - **Schema-on-Read** 방식
>     
> - 배치 분석에 적합 (대화형 ❌, 실시간 ❌)
>     
> - 실행 엔진: **MapReduce / Tez / Spark**
>     
> - 메타데이터는 **Metastore**에 저장
>     

**Apache Hive**는  
**대규모 분산 스토리지에 저장된 데이터를 SQL로 조회·분석할 수 있게 해주는 데이터 웨어하우스 인프라**다.

---

## 🐝 Apache Hive란?

> **Apache Hive**는  
> **Hadoop(HDFS) 또는 S3에 저장된 대규모 데이터를  
> SQL과 유사한 언어(HiveQL)로 분석**하기 위한 도구다.

- 개발자와 데이터 분석가에게 친화적이다.
- 복잡한 MapReduce 코드를 SQL 수준에서 추상화하여 사용할 수 있다.

---

## 🏗️ 동작 방식

```text
[User]
 (HiveQL)
        │
        ▼
[Hive]
 ├─ Parser / Optimizer
 ├─ Metastore
 └─ Execution Engine
        │
        ▼
[MapReduce / Tez / Spark]
        │
        ▼
[HDFS / S3]
```

---

## 🚀 주요 특징

|기능|설명|
|---|---|
|**SQL 인터페이스**|HiveQL 제공|
|**대용량 처리**|TB~PB 데이터|
|**Schema-on-Read**|읽을 때 스키마 적용|
|**확장성**|Hadoop/Spark 기반|
|**저비용**|Data Lake 활용|

---

## 📦 핵심 구성 요소

### 1️⃣ Hive Metastore ⭐ (시험 단골)

|항목|설명|
|---|---|
|역할|테이블 메타데이터 관리|
|저장 정보|스키마, 위치, 파티션|
|저장소|MySQL, PostgreSQL 등|

📌 시험 포인트

> _“Hive 테이블 정의 정보는 Metastore에 저장”_

---

### 2️⃣ Execution Engine

|엔진|특징|
|---|---|
|MapReduce|안정적, 느림|
|Tez|DAG 기반, 빠름|
|Spark|메모리 기반, 가장 빠름|

---

## 🧩 테이블 타입 (중요)

### 1️⃣ Managed Table (Internal)

|항목|설명|
|---|---|
|데이터 관리|Hive|
|DROP TABLE|데이터 삭제됨|

---

### 2️⃣ External Table ⭐

|항목|설명|
|---|---|
|데이터 관리|사용자|
|DROP TABLE|메타데이터만 삭제|
|S3 연동|매우 적합|

📌 시험 키워드

> _“S3 데이터 보호” → External Table_

---

## 🧠 파티셔닝 & 버킷팅

### 🔹 Partitioning

- 디렉터리 단위로 데이터를 분리한다.
- WHERE 조건을 통해 스캔할 데이터 양을 줄일 수 있다.

```text
/year=2025/month=01/
```

### 🔹 Bucketing

- 해시 기반으로 데이터를 분산시킨다.
- 조인 성능 개선에 도움을 준다.

---

## 🆚 Hive vs 다른 SQL 엔진

### vs Presto / Trino

|항목|Hive|Presto|
|---|---|---|
|처리 방식|배치|대화형|
|지연 시간|높음|낮음|
|사용 사례|정기 분석|애드혹 쿼리|

---

### vs Amazon Athena

| 항목 | Hive | Athena |  
|---|---|  
| 관리 | 클러스터 필요 | 서버리스 |  
| 엔진 | Hive/Spark | Presto |  
| 운영 부담 | 높음 | 낮음 |

---

## 🧪 시험에 자주 나오는 문제 유형

### ❓ 문제 1

> S3에 저장된 대규모 로그 데이터를  
> SQL로 배치 분석하려 한다.

✅ 정답

- **Apache Hive (External Table)**
    
---

### ❓ 문제 2

> 테이블 정의는 삭제하되  
> 원본 데이터는 유지하고 싶다.

✅ 정답

- **External Table**
    
---

### ❌ 오답 유도

- 실시간 분석 → ❌
    
- OLTP → ❌
    

---

## ⚠️ 제한 사항 (시험 포인트)

- 실시간 처리 ❌
    
- 낮은 쿼리 응답성
    
- 트랜잭션(ACID) 제한적
    
- 소규모 데이터 ❌
    

---

## ✅ 사용 사례

- 📊 대규모 로그 배치 분석
    
- 🧪 데이터 웨어하우스 전처리
    
- 🔄 ETL 중간 단계
    
- 🧠 Data Lake SQL 분석
    
- 🗄️ 아카이빙 데이터 조회
    

---

## ✅ 요약 (암기용)

|항목|핵심|
|---|---|
|이름|**Apache Hive**|
|목적|SQL 기반 빅데이터 분석|
|저장소|HDFS / S3|
|스키마|Schema-on-Read|
|처리|배치|
|메타데이터|Metastore|

---

### 📌 한 줄 요약 (시험용)

> **Hive = Hadoop/S3 위 대규모 데이터를 SQL로 배치 분석하는 엔진**