---
title: Amazon Kinesis Producer Library(KPL) 정리 — Aggregation과 Consumer 영향
slug: "amazon-kinesis-producer-librarykpl-정리--aggregation과-consumer-영향"
category: cloud
tags: ["aggregation", "aws", "deaggregation", "kcl", "kinesis", "kinesis-producer-library", "lambda", "producer", "streaming"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.303890+00:00"
---

**NOTE:**

- **Kinesis Data Streams 전용 고성능 Producer 라이브러리**

- **배치(Batching)·집계(Aggregation)·압축(Compression)** 자동 처리

- **처리량 극대화 & 비용 절감** 목적

- **At-least-once 전송 보장**

- Java / C++ 기반 (다른 언어는 간접 사용)

- **Shard 한도(1MB/s, 1,000 records/s)** 를 효율적으로 활용


**Amazon Kinesis Producer Library(KPL)**는  
**Kinesis Data Streams로 데이터를 대량·고속으로 전송하기 위해 최적화된 Producer 전용 라이브러리**다.

---

## 🚀 Amazon Kinesis Producer Library란?

> **KPL**은  
> **애플리케이션에서 발생하는 많은 작은 레코드들을 자동으로 묶어  
> Kinesis Data Streams에 효율적으로 전송**해 주는 라이브러리다.

- AWS SDK `PutRecord`의 **고성능 대안**
    
- **Producer 최적화에 특화**
    
- Consumer는 **KCL**이 담당
    
---

## 🏗️ 동작 방식

```text
[Producer App]
 (KPL)
   ├─ Aggregation
   ├─ Batching
   └─ Compression
        │
        ▼
[Kinesis Data Streams]
 (Shard)
```

- 작은 레코드들을 묶어 큰 레코드로 전송한다.
    
- Shard 한도를 효율적으로 사용하도록 설계되었다.
    
---

## 🧩 KPL의 핵심 기능

|기능|설명|
|---|---|
|**Aggregation**|여러 사용자 레코드를 하나의 Kinesis 레코드로 묶음|
|**Batching**|API 호출 수 감소|
|**Compression**|네트워크 비용 절감|
|**비동기 전송**|애플리케이션 지연 최소화|
|**재시도 처리**|실패 시 자동 재전송|

---

## 📦 Aggregation 개념 (중요)

```text
User Record 1 ┐
User Record 2 ├─▶ Aggregated Record (≤ 1MB)
User Record 3 ┘
```

- Kinesis는 **1MB 단위**로 과금/제한된다.
    
- KPL은 **수십~수백 개의 작은 레코드**를 하나로 묶어 전송한다.
    
- **비용 ↓ / 처리량 ↑**
    

📌 Consumer에서는 **Deaggregation**이 필요하다.

---

## 🧑‍💻 지원 언어

|언어|지원 방식|
|---|---|
|**Java**|네이티브 지원|
|**C++**|네이티브 지원|
|Python / Node.js|Java 기반 데몬 연동|

---

## 🧠 KPL vs AWS SDK (Producer)

|항목|AWS SDK|KPL|
|---|---|---|
|처리량|보통|매우 높음|
|배치|수동|자동|
|집계|X|O|
|압축|X|O|
|난이도|낮음|중간|
|비용 효율|낮음|높음|

👉 **대규모 Producer → KPL 권장**

---

## ⚠️ 주의 사항

- **Consumer에서 Deaggregation 필요**
    
    - KCL → 자동 처리
        
    - Lambda / 직접 Consumer → 라이브러리 필요
        
- **Exactly-once ❌**
    
    - At-least-once 보장
        
- Kinesis Data Streams 전용 (Firehose ❌)
    

---

## 🧩 KPL + KCL 조합 (정석 아키텍처)

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

- 시험/실무에서 가장 자주 나오는 조합이다.

---

## ✅ 사용 사례

- 📊 대규모 로그/이벤트 스트리밍
    
- 🎮 게임 이벤트 전송
    
- 📡 IoT 센서 데이터 수집
    
- 💳 금융 트랜잭션 이벤트
    
- 🧑‍💻 고처리량 마이크로서비스 이벤트
    
---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**Amazon Kinesis Producer Library**|
|대상|**Producer 전용**|
|목적|고처리량·저비용 데이터 전송|
|핵심 기능|Aggregation, Batching, Compression|
|보장|At-least-once|
|조합|**KPL + KCL**|

- Amazon Kinesis Data Streams
    
- Amazon Kinesis SDK
    
- Amazon Kinesis Client Library
    
---
# KPL Aggregation이 Consumer에 미치는 영향

다음은 **시험에서 가장 자주 함정으로 나오는 주제**인  
**「KPL Aggregation이 Consumer에 미치는 영향」**을 **개념 → 영향 → 소비자별 동작 → 시험 포인트** 순서로 정리한 것이다.

---

# 🧠 KPL Aggregation이란? (짧은 복습)

**Kinesis Producer Library(KPL)**는  
여러 개의 **User Record**를 **하나의 Kinesis Record(≤ 1MB)**로 묶어서 전송한다.

```text
User Record A ┐
User Record B ├─▶ Aggregated Kinesis Record
User Record C ┘
```

- 목적: **처리량 극대화 / 비용 절감**
    
- Aggregation은 **Producer 측 동작**이다.
    
---

# 🚨 Consumer에 미치는 핵심 영향

> **Consumer는 “Kinesis Record”가 아니라  
> “User Record” 단위로 처리해야 한다**

👉 **Aggregation을 모르면 데이터가 깨진 것처럼 보일 수 있다**

---

## 1️⃣ Consumer가 Aggregation을 인식하지 못하면?

### ❌ 잘못된 소비 결과

```text
GetRecords()
 └─ Record 1 (Binary blob)
```

- Consumer는 **하나의 큰 Record**만 인식한다.
    
- 실제로는 **수십~수백 개 User Record가 포함**되어 있다.
    
- JSON 파싱 실패 / 데이터 누락이 발생할 수 있다.
    

📌 시험 표현

> _“Consumer에서 예상보다 레코드 수가 적다”_  
> _“데이터 포맷이 깨져 보인다”_

➡️ **Aggregation 미처리 의심**

---

## 2️⃣ Consumer별 영향 정리 (중요)

### ✅ KCL Consumer

|항목|동작|
|---|---|
|Aggregation 인식|✅ 자동|
|Deaggregation|✅ 자동|
|추가 작업|❌ 불필요|

```text
[KPL] → [Kinesis] → [KCL]
               (자동 분해)
```

📌 **시험 정답 키워드**

> _“KCL automatically deaggregates KPL records”_

---

### ⚠️ AWS Lambda Consumer

|항목|동작|
|---|---|
|Aggregation 인식|❌ 기본 미지원|
|Deaggregation|❌ 직접 처리 필요|
|결과|데이터 파싱 오류 가능|

#### 해결 방법

- **Kinesis Aggregation Library 사용**
    
- 또는 **KCL 기반 Consumer로 변경**
    
📌 시험 함정

> _“Lambda에서 KPL로 보낸 데이터를 그대로 읽는다”_ ❌

---

### ⚠️ Custom Consumer (AWS SDK)

|항목|동작|
|---|---|
|Aggregation 인식|❌|
|Deaggregation|❌|
|필요 작업|직접 라이브러리 사용|

- `GetRecords()` 결과는 **Aggregated Record**이다.
    
- 반드시 **Deaggregation 로직 구현**이 필요하다.
    
---

## 3️⃣ Enhanced Fan-Out과 Aggregation

|항목|영향|
|---|---|
|Fan-Out|Consumer 처리량 증가|
|Aggregation|Record 내부 구조 문제|

📌 **Fan-Out ≠ Deaggregation**

- Fan-Out은 **대역폭 문제**를 해결한다.
    
- Aggregation은 **데이터 구조 문제**이다.
    
➡️ **서로 해결 영역이 다르다**

---

# 📊 시험 단골 비교 표

|Consumer 유형|Aggregation 자동 처리|
|---|---|
|**KCL**|✅|
|**Lambda**|❌|
|**Custom SDK**|❌|
|**Flink (Managed)**|✅ (내부 처리)|

---

# 🧪 시험에서 나오는 전형적인 질문 패턴

---

### ❓ 문제 1

> KPL을 사용해 데이터를 전송했더니  
> Consumer에서 JSON 파싱 에러가 발생한다.  
> 가장 적절한 해결책은?

✅ 정답

- **KCL 사용**
    
- 또는 **Deaggregation 라이브러리 추가**
    
---

### ❓ 문제 2

> 대량의 작은 이벤트를 비용 효율적으로 전송하고  
> Consumer 구현을 단순화하려면?

✅ 정답

- **KPL + KCL**
    
---

### ❓ 문제 3

> Lambda로 Kinesis 데이터를 소비 중이다.  
> KPL을 도입했더니 레코드 수가 줄어 보인다. 왜인가?

✅ 정답

- **Aggregation된 Record를 Lambda가 분해하지 못함**
    
---

# ⚠️ 꼭 기억해야 할 시험 한 줄 요약

> **KPL은 Producer 최적화,  
> KCL은 Consumer 안정화**

> **KPL Aggregation →  
> KCL만 자동 Deaggregation 제공**

---

# ✅ 최종 요약 (암기용)

|항목|핵심|
|---|---|
|KPL Aggregation|여러 User Record → 1 Kinesis Record|
|문제 발생 지점|Consumer|
|자동 해결|**KCL**|
|Lambda / SDK|직접 처리 필요|
|시험 키워드|_Deaggregation, KCL, Aggregation_|