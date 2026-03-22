---
title: Kinesis SDK 개요
slug: "kinesis-sdk-개요"
category: cloud
tags: ["amazon-kinesis", "aws-sdk", "cloudwatch", "dynamodb", "kinesis-client-library", "kinesis-data-streams", "kinesis-sdk", "producer-consumer", "stream-processing"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.315211+00:00"
---

**NOTE:**

- **Amazon Kinesis 서비스를 애플리케이션에서 직접 사용하기 위한 개발 도구 모음**

- **Producer / Consumer 애플리케이션 구현**에 사용

- 주로 **Kinesis Data Streams**와 함께 사용

- 언어별 SDK + **Kinesis Client Library(KCL)** 포함

- **체크포인트, 샤드 관리, 재시도** 등을 자동화

- 고수준(KCL) / 저수준(API) 방식 모두 제공


**Kinesis SDK**는  
**애플리케이션에서 Kinesis 스트림에 데이터를 쓰거나 읽기 위해 사용하는 개발 라이브러리 집합**이다.

---

## 🌊 Kinesis SDK란?

**Kinesis SDK**는  
**개발자가 직접 Producer·Consumer 애플리케이션을 구현**할 수 있도록  
**AWS에서 제공하는 공식 개발 키트**이다.

- Kinesis Agent → **파일 기반 Producer**
    
- Kinesis SDK → **코드 기반 Producer / Consumer**
    

👉 **유연성과 제어력이 가장 높음**

---

## 🧩 구성 요소

Kinesis SDK는 크게 **두 계층**으로 나뉜다.

### 1️⃣ AWS SDK (Low-level API)

|항목|설명|
|---|---|
|대상|Producer, Consumer 모두|
|방식|Kinesis API 직접 호출|
|난이도|높음|
|제어|매우 세밀|

- `PutRecord`, `PutRecords`
    
- `GetRecords`, `GetShardIterator`
    

---

### 2️⃣ Kinesis Client Library (KCL) – High-level

|항목|설명|
|---|---|
|대상|Consumer 전용|
|기능|샤드 분산, 체크포인트 자동화|
|난이도|낮음|
|운영 부담|매우 낮음|

👉 **실무/시험에서 가장 자주 등장**

---

## 🧑‍💻 지원 언어

### AWS SDK

- Java
    
- Python (boto3)
    
- JavaScript
    
- Go
    
- C++
    
- .NET
    

### KCL

- **Java**
    
- **Python (MultiLangDaemon 기반)**
    

---

## 🏗️ 아키텍처 흐름

```text
[Producer App]
 (AWS SDK)
        │
        ▼
[Kinesis Data Stream]
        │
        ▼
[Consumer App]
 (KCL)
        │
        ▼
[Process / Store / Analytics]
```

---

## 🚀 Producer (AWS SDK)

### 주요 기능

- 스트림에 데이터 전송
    
- Partition Key 지정
    
- 배치 전송 가능
    

### 핵심 API

|API|설명|
|---|---|
|`PutRecord`|단일 레코드 전송|
|`PutRecords`|배치 전송 (최대 500개)|

📌 **Partition Key**에 따라 Shard 결정 → 순서 보장

---

## 🧠 Consumer (KCL 중심)

### KCL이 자동으로 처리해주는 것

|기능|설명|
|---|---|
|**Shard 분배**|Consumer 간 자동 분산|
|**Failover**|장애 시 다른 Consumer가 인계|
|**Checkpoint**|DynamoDB에 처리 위치 저장|
|**Scale 대응**|Shard Split/Merge 자동 반영|

---

### KCL 내부 구성

```text
[KCL Worker]
   ├─ Record Processor (Shard별)
   ├─ Checkpointer
   └─ Lease Manager (DynamoDB)
```

- **DynamoDB**: 체크포인트 & Lease 관리
    
- **CloudWatch**: 메트릭 기록
    

---

## 🆚 SDK vs Agent vs Lambda

|항목|Kinesis SDK|Kinesis Agent|Lambda|
|---|---|---|---|
|방식|코드 기반|파일 기반|이벤트 기반|
|유연성|매우 높음|낮음|중간|
|운영 난이도|중간|낮음|매우 낮음|
|주 용도|커스텀 처리|로그 수집|간단 처리|

---

## ⚠️ 주의 사항

- KCL 사용 시 **DynamoDB 필수**
    
- Consumer 수 ≠ Shard 수 (자동 조정됨)
    
- Enhanced Fan-Out 사용 가능
    
- Exactly-once ❌ (At-least-once 보장)
    

---

## ✅ 사용 사례

- 🧑‍💻 커스텀 Producer/Consumer 개발
    
- 📊 실시간 데이터 처리 애플리케이션
    
- 🎮 게임 이벤트 처리
    
- 💳 금융 트랜잭션 스트림 처리
    
- 🔔 이벤트 기반 마이크로서비스
    

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**Kinesis SDK**|
|구성|AWS SDK + KCL|
|역할|Kinesis 스트림 연동 개발|
|Producer|AWS SDK|
|Consumer|KCL (권장)|
|장점|유연성, 제어력|
|단점|직접 개발 필요|

- Amazon Kinesis Data Streams
    
- Amazon Kinesis Agent
    
- Amazon Managed Service for Apache Flink