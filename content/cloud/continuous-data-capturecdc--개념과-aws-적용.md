---
title: Continuous Data Capture(CDC) — 개념과 AWS 적용
slug: "continuous-data-capturecdc--개념과-aws-적용"
category: cloud
tags: ["aws-dms", "cdc", "change-data-capture", "data-pipeline", "etl", "kafka", "kinesis", "log-based-cdc", "streaming"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.448847+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

키워드: **Continuous Data Capture (CDC)**  
_(일반적으로 **Change Data Capture**라고도 불림)_

---

> **NOTE:**
> 
> - **데이터베이스 변경 사항(INSERT / UPDATE / DELETE)을 실시간 또는 준실시간으로 캡처**
>     
> - 전체 테이블 재복사 ❌ → **변경분만 전송**
>     
> - **로그 기반(Log-based)** 방식이 핵심
>     
> - 실시간 데이터 파이프라인, 동기화, 스트리밍의 기반 기술
>     
> - 배치 ETL 대비 **지연 시간↓, 부하↓**
>     

**Continuous Data Capture(CDC)**는  
**데이터베이스의 변경 이벤트를 지속적으로 추적하여 다른 시스템으로 전달하는 기술/패턴**이다.

---

## 🌊 Continuous Data Capture란?

> **CDC**는  
> **데이터베이스에 발생하는 변경 사항을 실시간으로 감지하여  
> 다른 데이터 저장소·분석 시스템·스트리밍 플랫폼으로 전달하는 메커니즘**이다.

- “전체 테이블 덤프” ❌
    
- “변경된 행만 전달” ✅
    

---

## 🏗️ 동작 개념

```text
[Source DB]
 (INSERT / UPDATE / DELETE)
        │
        ▼
[DB Log]
 (Redo / Binlog / WAL)
        │
        ▼
[CDC Tool]
        │
        ▼
[Target]
 (DW / Data Lake / Stream)
```

📌 핵심 포인트

> **CDC는 애플리케이션이 아니라 DB 로그를 읽는다**

---

## 🧠 CDC 방식 분류 (시험 단골)

### 1️⃣ Log-based CDC ⭐⭐⭐ (권장)

|항목|설명|
|---|---|
|방식|DB 트랜잭션 로그 읽기|
|성능|매우 우수|
|DB 부하|매우 낮음|
|실시간성|높음|

- MySQL: **Binlog**
    
- PostgreSQL: **WAL**
    
- Oracle: **Redo Log**
    

📌 **시험에서 가장 정답률 높은 방식**

---

### 2️⃣ Trigger-based CDC

|항목|설명|
|---|---|
|방식|DB Trigger 사용|
|성능|낮음|
|DB 부하|높음|
|실시간성|중간|

- 트랜잭션마다 Trigger 실행
    
- **운영 환경에 부적합**
    
---

### 3️⃣ Timestamp / Polling 방식

|항목|설명|
|---|---|
|방식|수정 시간 기준 주기적 조회|
|실시간성|낮음|
|누락 위험|있음|
|부하|중간|

- CDC라기보다는 **증분 배치**
    
---

## 🧩 CDC 데이터 형태

CDC는 보통 **이벤트 스트림 형태**로 전달된다.

```json
{
  "op": "UPDATE",
  "table": "orders",
  "before": {...},
  "after": {...},
  "timestamp": "2025-01-01T12:00:00Z"
}
```

|필드|의미|
|---|---|
|`op`|INSERT / UPDATE / DELETE|
|`before`|변경 전|
|`after`|변경 후|

---

## 🧠 CDC vs 배치 ETL

|항목|CDC|배치 ETL|
|---|---|---|
|처리 방식|변경 이벤트|전체/부분 스캔|
|지연 시간|실시간/준실시간|분~시간|
|DB 부하|낮음|높음|
|데이터 최신성|매우 높음|낮음|
|복잡도|높음|낮음|

---

## 🧩 CDC + 스트리밍 아키텍처

```text
[RDBMS]
   │
   ▼
[CDC Tool]
   │
   ▼
[Kinesis / Kafka]
   │
   ▼
[Flink / Spark / Consumers]
```

👉 **CDC = 스트리밍 파이프라인의 Source**

---

## 🧪 시험에서 나오는 전형적 질문

### ❓ 문제 1

> 운영 중인 RDBMS에 최소한의 부하로  
> 변경 데이터를 실시간으로 다른 시스템에 전달해야 한다.

✅ 정답

- **Log-based CDC**
    
---

### ❓ 문제 2

> 데이터 웨어하우스에 항상 최신 데이터를 유지하고 싶다.

✅ 정답

- **CDC 기반 파이프라인**
    
---

### ❌ 오답 유도

- 전체 테이블 주기적 복사
    
- Trigger 기반 방식
    
- 수동 Export/Import
    
---

## ☁️ AWS에서의 CDC 구현 예

|서비스|역할|
|---|---|
|**AWS DMS (CDC 모드)**|대표적 CDC 서비스|
|Amazon MSK / Kinesis|변경 이벤트 스트림|
|Amazon S3|변경 데이터 저장|
|Amazon Redshift|CDC 기반 DW 동기화|
|Amazon Managed Flink|실시간 처리|

---

## ⚠️ 주의 사항 (시험 포인트)

- CDC ≠ 단순 증분 배치
    
- **로그 기반 CDC가 가장 안정적**
    
- Schema 변경 처리 필요
    
- Exactly-once 보장 어려움 → idempotent 처리 필요
    
---

## ✅ 사용 사례

- 🔄 RDBMS → Data Lake 실시간 동기화
    
- 📊 실시간 BI / 대시보드
    
- 🧠 마이크로서비스 간 데이터 동기화
    
- 🧪 이벤트 소싱(Event Sourcing)
    
- 💳 금융·주문 시스템 변경 추적
    
---

## ✅ 요약 (암기용)

|항목|핵심|
|---|---|
|이름|**Continuous(Change) Data Capture**|
|목적|DB 변경 사항 실시간 캡처|
|핵심 방식|**Log-based CDC**|
|장점|실시간성, 낮은 부하|
|단점|구현 복잡|
|AWS 대표|**AWS DMS (CDC)**|

---

### 📌 한 줄 요약 (시험용)

> **CDC = DB 로그를 읽어 변경 데이터만 실시간으로 전달하는 기술**
