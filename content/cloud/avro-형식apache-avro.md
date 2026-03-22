---
title: AVRO 형식(Apache Avro)
slug: "avro-형식apache-avro"
category: cloud
tags: ["avro", "aws", "data-lake", "glue", "kafka", "kinesis", "parquet", "s3", "schema-evolution", "serialization"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:06.072604+00:00"
---

**AVRO 형식(Apache Avro)**은 대규모 데이터 처리 환경에서 사용되는 **이진(Binary) 기반의 스키마 포함 직렬화 데이터 포맷**입니다.

---

## 한 줄 정의

> **AVRO는 스키마를 데이터와 함께 저장하는 이진 직렬화 포맷으로, 빠른 처리와 스키마 진화를 지원한다.**

---

## AVRO의 핵심 특징

### 1️⃣ 이진(Binary) 포맷

- 텍스트(JSON/CSV)보다 **용량이 작음**
- 읽기·쓰기 성능 우수
- 네트워크 전송에 유리

---

### 2️⃣ 스키마 포함 (Schema-included)

- 스키마가 **파일에 함께 저장**됨
- 데이터 해석 시 외부 메타데이터에 대한 의존도가 낮음

```json
{
  "name": "User",
  "type": "record",
  "fields": [
    {"name": "id", "type": "int"},
    {"name": "email", "type": "string"}
  ]
}
```

---

### 3️⃣ 스키마 진화(Schema Evolution) 지원

- 컬럼 추가/삭제/기본값 변경을 허용
- 과거 데이터와의 **호환성 유지**
- 스트리밍·이벤트 데이터에 적합

---

### 4️⃣ 행(Row) 기반 저장

- 레코드 단위 처리에 효율적
- 스트리밍, 메시징(Kafka)과 궁합이 좋음

---

## AVRO vs 다른 포맷

|포맷|특징|적합한 용도|
|---|---|---|
|**AVRO**|이진 + 스키마 포함|스트리밍, 이벤트|
|JSON|텍스트, 가독성|API, 로그|
|CSV|단순|소규모 데이터|
|Parquet|컬럼 기반|대규모 분석|
|ORC|컬럼 기반|Hive/Presto|

👉 **스트리밍 = AVRO**, **분석 = Parquet/ORC**

---

## AWS에서 AVRO 활용 예

- Amazon Kinesis / MSK 메시지
- AWS Glue ETL 입출력
- Amazon S3 데이터 레이크
- Schema Registry 연계

---

## 핵심 포인트

- “스키마 포함 이진 포맷” → **AVRO**
- “스키마 진화” → **AVRO**
- “스트리밍 데이터” → **AVRO**
- “컬럼 기반 아님” → **중요**