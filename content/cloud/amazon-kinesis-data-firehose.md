---
title: Amazon Kinesis Data Firehose
slug: "amazon-kinesis-data-firehose"
category: cloud
tags: ["aws", "aws-lambda", "kinesis", "kinesis-data-firehose", "opensearch", "redshift", "s3", "serverless", "streaming"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.283229+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

**Amazon Kinesis Data Firehose**는
스트리밍 데이터를 **실시간으로 수집·변환·적재(delivery)** 하는 **완전관리형(서버리스) 데이터 전송 서비스**입니다.

---

## 한 줄 정의

> **Amazon Kinesis Data Firehose는 스트리밍 데이터를 자동으로 수집해 S3, Redshift, OpenSearch 등으로 전달하는 서버리스 데이터 적재 서비스이다.**

---

## 무엇을 해결해 주나?

- 스트리밍 데이터의 **버퍼링/배치/재시도/확장**을 자동으로 처리
- 서버·샤드·스케일 관리를 하지 않아도 됨
- 데이터 파이프라인을 **가장 간단하게 구성**할 수 있음

---

## 핵심 기능

### 1️⃣ 완전관리형(Serverless)

- 인프라 관리 불필요
- 자동 확장
- 장애 처리 및 재시도 자동화

---

### 2️⃣ 실시간 데이터 적재(Delivery)

- 소스:
    - Kinesis Data Streams
    - Direct PUT (API/SDK)
- 목적지:
    - **Amazon S3**
    - **Amazon Redshift**
    - **Amazon OpenSearch Service**
    - **HTTP Endpoint**
    - (서드파티: Splunk 등)

---

### 3️⃣ 버퍼링(Buffering)

- **시간 기반** 또는 **크기 기반**으로 데이터를 묶어서 전송
- 예: 60초 또는 5MB마다 S3로 적재
- → 실시간에 가깝지만 **완전 실시간(ms 단위)** 은 아님

---

### 4️⃣ 데이터 변환(선택)

- **AWS Lambda**로 변환 수행
- JSON → Parquet/ORC 변환 가능
- 필드 정제 및 포맷 변경 지원

---

### 5️⃣ 오류 처리

- 실패한 데이터는 **백업 S3 버킷**에 저장
- 데이터 유실 방지 메커니즘 제공

---

## 대표 아키텍처

```
Producers
   ↓
Kinesis Data Firehose
   ↓
(Optional Lambda Transform)
   ↓
S3 / Redshift / OpenSearch
```

---

## Firehose vs Kinesis Data Streams

|항목|Firehose|Data Streams|
|---|---|---|
|실시간성|Near-real-time|Real-time|
|소비자 관리|❌|✅|
|샤드 관리|❌|✅|
|처리 로직|제한적|자유|
|사용 난이도|**매우 쉬움**|높음|
|용도|적재(Delivery)|처리(Stream processing)|

👉 **“적재면 Firehose, 처리면 Streams”**

---

## 언제 Firehose를 쓰나?

- 스트리밍 데이터를 **S3/Redshift로 바로 쌓고 싶을 때**
- 실시간성보다 **단순성·안정성**이 더 중요할 때
- 로그, 클릭스트림, IoT 수집에 적합

---

## 시험 대비 핵심 포인트

- “자동 적재” → Firehose
- “서버리스 스트리밍 적재” → Firehose
- “버퍼링 존재” → Firehose
- “복잡한 실시간 처리” → ❌ (Streams + Flink)
