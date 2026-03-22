---
title: Amazon Kinesis Data Streams (KDS) 개요
slug: "amazon-kinesis-data-streams-kds-개요"
category: cloud
tags: ["amazon-kinesis", "aws", "aws-lambda", "data-streaming", "flink", "iot", "kinesis-data-streams", "real-time", "stream-processing"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.292780+00:00"
---

> **NOTE:**
> 
> - **대규모 실시간 데이터 스트리밍 수집 서비스**
>     
> - 초당 **수백만 건 이벤트** 처리 가능
>     
> - 데이터는 **Shard 단위로 분산 저장**
>     
> - **Shard 내부 순서 보장**
>     
> - 기본 **데이터 보존 24시간 (최대 365일)**
>     
> - **Pull 기반 Consumer 모델**
>     
> - 서버 관리 불필요 (완전 관리형)
>     
> - 실시간 처리 엔진(Flink 등)과 함께 사용 시 강력
>     
> - Kinesis 데이터 스트림은 파티션 키를 기준으로 데이터를 샤드에 분배
> 	- 각 샤드 내에서는 메시지 순서가 보장됨

**Amazon Kinesis Data Streams(KDS)**는  
**실시간으로 발생하는 대규모 데이터를 안정적으로 수집하고 여러 소비자가 병렬로 처리할 수 있게 하는 스트리밍 플랫폼**이다.

---

## 🌊 Amazon Kinesis Data Streams란?

> **Amazon Kinesis Data Streams**는  
> **로그, 클릭스트림, IoT, 이벤트 데이터**와 같은  
> **연속적인 데이터 스트림을 실시간으로 수집·저장·전달**하는 AWS 서비스이다.

- **실시간 데이터 파이프라인의 핵심 Source**
    
- 분석·처리는 **Consumer**가 담당
    
---

## 🏗️ 동작 방식

```text
[Producer]
 (App / IoT / Log)
        │
        ▼
[Kinesis Data Stream]
 ├─ Shard 1
 ├─ Shard 2
 └─ Shard N
        │
        ▼
[Consumer]
 (Lambda / Flink / EC2)
```

- **Producer**: 데이터를 스트림으로 전송
    
- **Stream**: 데이터를 샤드 단위로 저장
    
- **Consumer**: 스트림에서 데이터를 읽어 처리
    
---

## 🚀 주요 특징

|기능|설명|
|---|---|
|**실시간 스트리밍**|ms~초 단위 지연|
|**확장성**|Shard 증설로 처리량 확장|
|**내결함성**|다중 AZ 복제|
|**순서 보장**|Shard 내부 순서 유지|
|**다중 Consumer**|동일 데이터 병렬 소비 가능|
|**재처리 가능**|Retention 기간 내 재읽기|

---

## 📦 핵심 개념 정리

|개념|설명|
|---|---|
|**Stream**|데이터가 흐르는 논리적 단위|
|**Shard**|처리량의 최소 단위|
|**Record**|스트림에 저장되는 데이터|
|**Partition Key**|Shard 분배 기준|
|**Sequence Number**|Record 순서 보장|
|**Retention Period**|데이터 보관 시간|

---

## 🧩 Shard 처리 성능

|항목|Shard 1개당 한도|
|---|---|
|**쓰기**|1MB/s 또는 1,000 records/s|
|**읽기**|2MB/s|
|**보존**|24시간 ~ 365일|

👉 처리량 부족 시 **Shard Scale-out**

---

## 🧑‍💻 Producer & Consumer

### 🔼 Producer 예시

- EC2 / On-Prem App
    
- AWS SDK
    
- Kinesis Agent
    
- IoT Core
    

### 🔽 Consumer 예시

- **AWS Lambda**
    
- **Amazon Managed Service for Apache Flink**
    
- EC2 / ECS / EKS
    
- Kinesis Client Library (KCL)
    
---

## 🧠 Consumer 모델

|방식|설명|
|---|---|
|**Standard Consumer**|Shard당 2MB/s 공유|
|**Enhanced Fan-Out**|Consumer별 2MB/s 전용|

- 다수의 Consumer가 필요하면 **Enhanced Fan-Out** 사용 권장
    
- 비용은 증가하지만 지연(latency)은 감소
    
---

## 🪜 확장 방식

|방식|설명|
|---|---|
|**Shard Split**|처리량 증가|
|**Shard Merge**|비용 최적화|
|**On-demand Mode**|자동 확장 (최근 추가 기능)|

---

## 🆚 다른 서비스와 비교

### vs Amazon SQS

|항목|Kinesis Data Streams|SQS|
|---|---|---|
|데이터 모델|스트림|큐|
|순서 보장|O (Shard 단위)|FIFO만|
|재처리|O|제한적|
|실시간 분석|매우 적합|부적합|

---

### vs Kinesis Data Firehose

|항목|Data Streams|Firehose|
|---|---|---|
|실시간 처리|O|Near Real-time|
|Consumer 제어|사용자가 직접|AWS 관리|
|목적|실시간 처리|저장/적재|

---

## ✅ 사용 사례

- 📊 실시간 로그 분석
    
- 🖱️ 클릭 스트림 처리
    
- 📡 IoT 데이터 수집
    
- 🎮 게임 이벤트 처리
    
- 💰 금융 트랜잭션 스트림
    
- 🔔 이벤트 기반 아키텍처
    
---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**Amazon Kinesis Data Streams**|
|역할|**실시간 데이터 수집 스트림**|
|처리 단위|Shard|
|순서 보장|O (Shard 내부)|
|보존 기간|24h ~ 365d|
|확장 방식|Shard 증설|

- Amazon Managed Service for Apache Flink
    
- Amazon Kinesis Data Firehose
    
- Amazon MSK
