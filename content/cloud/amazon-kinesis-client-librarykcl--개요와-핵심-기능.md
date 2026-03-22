---
title: Amazon Kinesis Client Library(KCL) — 개요와 핵심 기능
slug: "amazon-kinesis-client-librarykcl--개요와-핵심-기능"
category: cloud
tags: ["aws", "dynamodb", "enhanced-fan-out", "kcl", "kinesis", "kinesis-data-streams", "kinesis-producer-library", "stream-processing"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.257654+00:00"
---

**NOTE:**

- **Kinesis Data Streams 전용 Consumer 라이브러리**

- **Shard 분산 처리·Failover·Checkpoint 자동화**

- **At-least-once 처리 보장**

- **DynamoDB를 사용해 상태(Lease, Checkpoint) 관리**

- **Enhanced Fan-Out 지원**

- Java / Python 지원

- 대규모 Consumer 애플리케이션의 **표준 선택**

**Amazon Kinesis Client Library(KCL)**는  
**Kinesis Data Streams에서 데이터를 안정적으로 소비(Consume)하기 위한 고수준 Consumer 라이브러리**다.

---

## 🌊 Amazon Kinesis Client Library란?

> **KCL**은  
> **여러 Consumer 애플리케이션이 하나의 Kinesis 스트림을 안정적으로 병렬 소비**할 수 있도록  
> **복잡한 Consumer 로직을 자동으로 처리**해 주는 라이브러리다.

- Shard 관리
    
- 장애 복구
    
- 체크포인트 관리  
    👉 **개발자는 비즈니스 로직에만 집중**
    
---

## 🏗️ 동작 구조

```text
[Kinesis Data Streams]
        │
        ▼
[KCL Application]
 ├─ Worker 1
 ├─ Worker 2
 └─ Worker N
        │
        ▼
[Record Processor]
 (Shard 단위)
```

- **Worker**: Consumer 인스턴스
    
- **Record Processor**: Shard별 레코드 처리기
    
---

## 🚀 KCL의 핵심 기능

|기능|설명|
|---|---|
|**Shard 분산 처리**|여러 Worker 간 Shard 자동 할당|
|**Failover**|Worker 장애 시 Shard 재할당|
|**Checkpoint**|처리 위치 자동 저장|
|**Scale 대응**|Shard Split / Merge 자동 반영|
|**Deaggregation**|KPL 집계 레코드 자동 분해|
|**Enhanced Fan-Out**|Consumer 전용 처리량 확보|

---

## 📦 내부 구성 요소 (중요)

```text
[KCL Worker]
 ├─ RecordProcessor
 ├─ LeaseCoordinator
 ├─ Checkpointer
 └─ Scheduler
```

### 🔐 DynamoDB 사용 이유

|항목|용도|
|---|---|
|**Lease Table**|Shard 소유권 관리|
|**Checkpoint**|마지막 처리 위치 저장|

📌 **KCL 사용 시 DynamoDB 필수**

---

## 🧠 처리 보장 모델

|항목|설명|
|---|---|
|처리 보장|**At-least-once**|
|중복 가능성|O (재처리 시)|
|Exactly-once|❌ (애플리케이션에서 보완)|

---

## 🧑‍💻 지원 언어

|언어|지원 방식|
|---|---|
|**Java**|네이티브|
|**Python**|MultiLangDaemon 기반|

---

## 🆚 KCL vs Lambda Consumer

|항목|KCL|Lambda|
|---|---|---|
|제어 수준|매우 높음|낮음|
|운영 부담|중간|매우 낮음|
|처리 복잡도|복잡한 로직|단순 처리|
|대규모 처리|매우 적합|제한적|

---

## 🧩 KPL과의 관계 (시험 단골)

```text
[Producer (KPL)]
        │
        ▼
[Kinesis Data Streams]
        │
        ▼
[Consumer (KCL)]
 (자동 Deaggregation)
```

- **KPL Aggregation → KCL이 자동 처리**
    
- 가장 이상적인 Producer/Consumer 조합
    
---

## ⚠️ 주의 사항 (시험 포인트)

- **DynamoDB 비용 고려**
    
- Consumer 수 ≠ Shard 수
    
- 순서 보장은 **Shard 내부**
    
- Exactly-once 아님
    
---

## ✅ 사용 사례

- 📊 실시간 로그 분석
    
- 🎮 게임 이벤트 처리
    
- 💳 금융 트랜잭션 소비
    
- 📡 IoT 데이터 처리
    
- 🔔 이벤트 기반 서비스
    
---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**Amazon Kinesis Client Library (KCL)**|
|역할|**Kinesis Consumer 표준 라이브러리**|
|자동 처리|Shard, Failover, Checkpoint|
|저장소|DynamoDB|
|보장|At-least-once|
|조합|**KPL + KCL**|

- Amazon Kinesis Data Streams
    
- Amazon Kinesis Producer Library
    
- Kinesis SDK