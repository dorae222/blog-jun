---
title: Amazon EMR — 대규모 분산 데이터 처리를 위한 관리형 빅데이터 플랫폼
slug: "amazon-emr--대규모-분산-데이터-처리를-위한-관리형-빅데이터-플랫폼"
category: cloud
tags: ["amazon-emr", "aws", "big-data", "data-lake", "emrfs", "etl", "hadoop", "s3", "spark"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.158434+00:00"
---

> **NOTE:**
> 
> - **대규모 데이터 처리용 관리형 빅데이터 플랫폼**
>     
> - Apache **Spark, Hadoop, Hive, HBase, Flink, Presto(Trino)** 등 지원
>     
> - **EC2 기반 클러스터**를 자동으로 프로비저닝·관리
>     
> - **S3를 주 데이터 저장소(Data Lake)**로 사용 가능
>     
> - 배치 처리, 스트리밍 처리, 대화형 분석 모두 지원
>     
> - Auto Scaling, Spot 인스턴스 활용으로 **비용 최적화 가능**
>     

**Amazon EMR**은
**대규모 데이터를 분산 처리하기 위한 오픈소스 빅데이터 프레임워크를 AWS에서 관리형으로 제공하는 서비스**다.

---

## 🌐 Amazon EMR이란?

> **Amazon Elastic MapReduce(EMR)**는
> **수 TB~PB 규모의 데이터를 빠르고 유연하게 처리**할 수 있도록
> **분산 컴퓨팅 클러스터를 손쉽게 생성·운영**하게 해주는 서비스다.

- 온프레미스 Hadoop/Spark 클러스터의 **클라우드 대체재**

- **서버 관리 부담 감소**, 데이터 처리 성능 향상

---

## 🏗️ 동작 방식

```text
[S3 / HDFS / Kinesis / Kafka]
            │
            ▼
        [EMR Cluster]
 ┌────────┬────────┬────────┐
 │ Master │ Core   │ Task   │
 │ Node   │ Nodes  │ Nodes  │
 └────────┴────────┴────────┘
            │
            ▼
      [결과 저장 (S3, RDS 등)]
```

---

## 🧱 EMR 클러스터 구성 (시험 단골)

|노드 유형|역할|
|---|---|
|**Master Node**|클러스터 관리, Job 스케줄링|
|**Core Node**|데이터 저장(HDFS) + 처리|
|**Task Node**|처리 전용 (저장 X, Spot에 적합)|

📌 시험 포인트

> _“저장은 필요 없고 연산만 확장” → Task Node_

---

## 🚀 주요 특징

|기능|설명|
|---|---|
|**관리형 클러스터**|설치·패치·모니터링 자동|
|**다양한 엔진**|Spark, Hadoop, Hive, Flink 등|
|**확장성**|수백~수천 노드 확장|
|**비용 절감**|Spot, Auto Scaling|
|**S3 연동**|EMRFS 사용 (HDFS 대체)|
|**보안**|IAM, KMS, Kerberos, VPC|

---

## 📦 지원 프레임워크

|분류|도구|
|---|---|
|배치 처리|Hadoop MapReduce, Spark|
|실시간/스트리밍|Spark Streaming, Flink|
|SQL 분석|Hive, Presto(Trino)|
|NoSQL|HBase|
|ML|Spark MLlib|

---

## 🧠 EMR Storage 모델 (중요)

### 1️⃣ HDFS

- Core Node에 데이터 저장

- 클러스터 종료 시 데이터 소멸


### 2️⃣ Amazon S3 (권장)

- **EMRFS** 사용

- 내구성 높음 (11 9’s)

- 클러스터 종료 후에도 데이터 유지

📌 시험 포인트

> _“장기 저장, Data Lake” → S3_

---

## 🆚 EMR vs 다른 서비스

### vs Amazon Athena

|항목|EMR|Athena|
|---|---|---|
|처리 방식|클러스터 기반|서버리스|
|성능 제어|매우 높음|제한적|
|복잡한 로직|O|X|
|운영 부담|있음|거의 없음|

---

### vs Amazon Glue

|항목|EMR|Glue|
|---|---|---|
|목적|범용 빅데이터 처리|ETL 특화|
|제어 수준|매우 높음|중간|
|커스터마이징|자유로움|제한적|

---

### vs Amazon Managed Service for Apache Flink

|항목|EMR|Managed Flink|
|---|---|---|
|처리 유형|배치 + 스트림|실시간 스트림|
|운영 모델|클러스터|서버리스에 가까움|
|주 용도|대규모 분석|실시간 이벤트 처리|

---

## ✅ 사용 사례

- 📊 대규모 로그 분석

- 🧪 데이터 웨어하우스 전처리

- 🧠 머신러닝 학습 데이터 처리

- 📡 IoT 데이터 배치 분석

- 🔄 ETL 파이프라인

- 💰 금융/광고 데이터 분석

---

## ⚠️ 시험 단골 포인트 정리

- **EMR = 클러스터 기반**

- **Master / Core / Task 노드 역할 구분**

- **S3 + EMRFS 조합**

- 비용 최적화 → **Spot + Task Node**

- 장기 저장 X → HDFS ❌

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**Amazon Elastic MapReduce (EMR)**|
|목적|대규모 분산 데이터 처리|
|기반|Hadoop / Spark 생태계|
|저장|HDFS 또는 S3|
|장점|확장성, 유연성|
|단점|운영 부담 (서버리스 아님)|

- Amazon Athena

- Glue

- Amazon Managed Service for Apache Flink

- Amazon Simple Storage Service