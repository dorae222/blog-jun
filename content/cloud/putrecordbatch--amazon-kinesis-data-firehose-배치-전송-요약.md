---
title: PutRecordBatch — Amazon Kinesis Data Firehose 배치 전송 요약
slug: "putrecordbatch--amazon-kinesis-data-firehose-배치-전송-요약"
category: cloud
tags: ["aws", "boto3", "cloud", "data-ingestion", "kinesis", "kinesis-firehose", "putrecordbatch", "python", "streaming"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.307989+00:00"
---

## 🧩 Quick Overview

| 항목                | 설명 |
|---------------------|------|
| **기능명**           | `PutRecordBatch` |
| **소속 서비스**      | Amazon Kinesis Data Firehose |
| **역할**             | 여러 개의 데이터를 **한 번에 배치로 Firehose로 전송**하는 API 작업

> 📦 **목적**: 수천 건의 스트리밍 데이터를 **네트워크 효율성 향상 및 처리량 최적화를 위해 묶어서 전송**
> → `PutRecordBatch`는 `PutRecord`에 비해 **성능과 비용 측면에서 더 효율적**

---

## 🔍 작동 방식

- 한 번의 API 호출로 **최대 500개의 레코드(record)** 전송 가능
- **최대 전체 배치 크기: 4 MB**
- 실패한 레코드만 재시도하면 됨 (응답값에 실패한 레코드 정보 포함)

---

## 🛠️ Python 예시 (boto3)

```python
import boto3

firehose = boto3.client('firehose')
response = firehose.put_record_batch(
    DeliveryStreamName='my-firehose-stream',
    Records=[
        {'Data': b'event-1\n'},
        {'Data': b'event-2\n'},
        {'Data': b'event-3\n'},
    ]
)

print("Failed record count:", response['FailedPutCount'])
```

---

## ✅ 장점

|항목|설명|
|---|---|
|**전송 효율성 향상**|단건 전송보다 API 호출 횟수를 줄여 네트워크 효율을 개선함|
|**비용 절감**|네트워크와 처리 리소스 사용을 최적화하여 비용 절감 효과를 기대할 수 있음|
|**재시도 용이**|응답에서 실패한 레코드만 확인해 부분 재처리 가능|
|**Firehose 자동 압축/전송과 연계**|전처리 없이도 Firehose가 자동으로 압축하거나 S3, Redshift, OpenSearch로 전달함|

---

## ⚠️ 주의사항

|항목|설명|
|---|---|
|**레코드 크기 제한**|개별 레코드는 최대 1,000 KB 까지 허용|
|**전체 배치 제한**|한 번의 요청에서 최대 500개 레코드 또는 총합 4 MB 이하로 제한|
|**순서 보장 없음**|Firehose는 레코드 순서를 보장하지 않음 (Kinesis Data Streams와 차이 있음)|

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|Kinesis Firehose에 **여러 데이터 레코드를 한 번에 전송**하는 배치용 API 작업|
|**제한**|최대 500개 레코드, 전체 크기 4 MB 이하|
|**활용**|로그, 센서 데이터, 이벤트 스트리밍 등 대량 데이터 전달에 적합|
|**장점**|성능 및 비용 효율 개선, 실패 레코드만 재시도 가능, 대량 데이터 전송 최적화|