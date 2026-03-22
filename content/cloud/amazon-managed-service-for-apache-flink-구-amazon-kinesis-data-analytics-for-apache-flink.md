---
title: "Amazon Managed Service for Apache Flink (구: Amazon Kinesis Data Analytics for Apache Flink)"
slug: "amazon-managed-service-for-apache-flink-구-amazon-kinesis-data-analytics-for-apache-flink"
category: cloud
tags: ["apache-flink", "aws", "event-time", "flink-sql", "kinesis", "msk", "real-time", "stateful-processing", "stream-processing"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.273398+00:00"
---

_구: Amazon Kinesis Data Analytics for Apache Flink_

---

> **NOTE:**
> 
> - **Apache Flink 기반의 실시간 스트림 처리 서비스**
>     
> - 서버 및 클러스터 관리 없이 **Flink 애플리케이션 실행**
>     
> - **이벤트 시간(Event Time)** 기반 정확한 스트림 처리 지원
>     
> - **상태 저장(Stateful) 스트림 처리** 가능
>     
> - Kinesis Data Streams, MSK, S3 등과 연동
>     
> - **Exactly-once 처리 보장**
>     
> - Java, Scala, SQL(Flink SQL) 지원
>     

**Amazon Managed Service for Apache Flink**는
**실시간 스트리밍 데이터를 고급 분석·처리하기 위해 Apache Flink를 완전 관리형으로 제공하는 서비스**입니다.

---

## 🌊 Amazon Managed Service for Apache Flink란?

> **Amazon Managed Service for Apache Flink**는
> **Apache Flink 오픈소스 엔진을 AWS에서 관리형으로 제공**하여
> **복잡한 실시간 스트림 처리 애플리케이션을 손쉽게 구축·운영**할 수 있게 해줍니다.

- **Kinesis Data Streams 자체는 “데이터 파이프”**
    
- **Flink는 “실시간 처리 엔진”**
    
- 둘을 함께 사용하면 **고급 실시간 분석 파이프라인** 구성 가능
    
---

## 🏗️ 동작 방식

```text
[Producer]
   │
   ▼
[Kinesis / MSK / Source]
   │
   ▼
[Apache Flink Application]
 (Window, State, Join, CEP)
   │
   ▼
[Sink]
 (S3, OpenSearch, RDS, Redshift, Kinesis)
```

- **Source**: 스트림 입력 (Kinesis, Kafka 등)
    
- **Flink App**: 실시간 계산 및 상태 관리
    
- **Sink**: 처리 결과 저장 또는 전달
    
---

## 🚀 주요 특징

|기능|설명|
|---|---|
|**완전 관리형 Flink**|클러스터/서버 관리 불필요|
|**실시간 처리**|ms~초 단위 지연|
|**Stateful Processing**|상태 기반 연산 (집계, 조인)|
|**Event Time 지원**|늦게 도착한 이벤트 처리 가능|
|**Exactly-once 보장**|데이터 정합성 확보|
|**자동 확장**|병렬성 조절로 처리량 확장|

---

## 📦 핵심 개념 정리

|개념|설명|
|---|---|
|**Flink Application**|실행되는 스트림 처리 애플리케이션|
|**Task Slot**|병렬 처리 단위|
|**State**|스트림 처리 중 유지되는 상태 데이터|
|**Checkpoint**|장애 복구를 위한 상태 스냅샷|
|**Watermark**|이벤트 시간 진행 기준|
|**Window**|시간/개수 기반 데이터 그룹|

---

## 🧩 처리 모델 (Flink의 강점)

### ⏱️ Time 개념

|구분|설명|
|---|---|
|**Event Time**|실제 이벤트 발생 시간|
|**Processing Time**|Flink가 처리한 시간|
|**Ingestion Time**|스트림에 들어온 시간|

👉 **Event Time 기반 처리**가 Flink의 핵심 강점

---

### 🪟 Window 연산 예시

|유형|설명|
|---|---|
|**Tumbling Window**|고정 길이, 겹치지 않음|
|**Sliding Window**|겹치는 윈도우|
|**Session Window**|사용자 활동 기반|

---

## 🧑‍💻 개발 방식

### 지원 언어

- **Java**
    
- **Scala**
    
- **Flink SQL**
    

### 배포 방식

- JAR 업로드
    
- 애플리케이션 설정 후 실행
    
- AWS가 인프라 자동 관리
    
---

## 🆚 Amazon Kinesis Data Streams와의 관계

|구분|Kinesis Data Streams|Managed Flink|
|---|---|---|
|역할|데이터 수집/저장|데이터 처리/분석|
|상태 관리|X|O|
|Window / Join|제한적|강력|
|목적|스트림 파이프라인|실시간 분석 엔진|

👉 **Kinesis = Source**, **Flink = Processor**

---

## 🆚 Managed Flink vs Kinesis Data Firehose

|항목|Managed Flink|Firehose|
|---|---|---|
|처리 복잡도|매우 높음|낮음|
|실시간성|매우 높음|Near Real-time|
|사용자 제어|높음|낮음|
|목적|분석/연산|적재(ETL)|

---

## ✅ 사용 사례

- 📊 실시간 대시보드 집계
    
- 💳 금융 이상 거래 탐지
    
- 🎮 게임 실시간 랭킹 계산
    
- 🖱️ 클릭스트림 분석
    
- 📡 IoT 이벤트 처리
    
- 🔔 CEP(Complex Event Processing)
    
---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**Amazon Managed Service for Apache Flink**|
|목적|**고급 실시간 스트림 처리**|
|기반|Apache Flink|
|핵심 기능|State, Window, Event Time|
|연동|Kinesis, MSK, S3 등|
|장점|정확성, 확장성, 관리 편의성|

- Amazon Kinesis Data Streams
    
- Amazon MSK
    
- Amazon Kinesis Data Firehose