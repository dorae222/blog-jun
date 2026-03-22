---
title: "🔹 `MSCK REPAIR TABLE` 이란?"
slug: "-msck-repair-table-이란"
category: cloud
tags: ["amazon-athena", "aws", "etl", "glue-data-catalog", "hive", "msck-repair-table", "partitioning", "s3", "schema-on-read"]
status: published
post_type: tutorial
quality_score: 9.0
created_at: "2026-03-02T01:08:06.219744+00:00"
---

>> **Amazon Athena에서
>> S3에 이미 존재하는 파티션 디렉터리를 스캔해서
>> Glue Data Catalog(메타데이터)에 자동으로 등록하는 명령어**

📌 한 줄 요약

> **MSCK REPAIR TABLE = “S3 파티션 구조 → 메타데이터 동기화”**

---

## 🧠 왜 필요한가?

Athena/Hive는 **Schema-on-Read** 방식입니다.

- S3에 데이터 파일이 있어도

- **파티션을 자동으로 인식하지 않습니다 ❌**

👉 **쿼리를 위해서는 메타데이터(Glue Catalog)에 파티션 정보가 있어야 합니다**

---

## 🏗️ 동작 개념

```text
[S3]
s3://logs/
 ├─ year=2024/
 │   └─ month=12/
 └─ year=2025/
     └─ month=01/

        │
        │ MSCK REPAIR TABLE
        ▼

[Glue Data Catalog]
Partitions:
- year=2024, month=12
- year=2025, month=01
```

---

## 🧩 언제 사용하는가? (시험 포인트)

### ✅ 이런 상황이면 `MSCK REPAIR TABLE`

|상황|이유|
|---|---|
|S3에 파티션 디렉터리를 **직접 생성**|Glue가 모름|
|ETL이 S3에 새 파티션 추가|메타데이터 미반영|
|Athena에서 쿼리가 안 됨|파티션 누락|

📌 시험 문장

> _“S3에 데이터는 있는데 Athena 쿼리 결과가 없다”_
> ➡️ **MSCK REPAIR TABLE**

---

## 🧪 기본 사용법

```sql
MSCK REPAIR TABLE my_table;
```

- S3 전체를 스캔합니다

- 누락된 파티션을 **모두 자동 등록**합니다

---

## 🆚 `ALTER TABLE ADD PARTITION` vs `MSCK REPAIR TABLE`

|항목|MSCK REPAIR TABLE|ALTER TABLE|
|---|---|---|
|파티션 수|많음|소수|
|방식|자동|수동|
|대상|S3 전체 스캔|특정 파티션|
|시험 선호|⭐⭐⭐|⭐|

📌 **파티션이 많으면 → MSCK**

---

## ⚠️ 주의 사항 (시험 & 실무)

### 1️⃣ 성능/비용

- **S3 전체 스캔**이므로 비용과 시간이 증가합니다

- 대규모 테이블에서 자주 실행하는 것은 권장되지 않습니다 ❌


### 2️⃣ Athena 전용

- DML 아님 ❌

- 데이터 이동 아님 ❌

- **메타데이터만 수정**합니다

---

## 🧠 Glue Crawler와의 관계

|도구|역할|
|---|---|
|**MSCK REPAIR TABLE**|이미 정의된 테이블의 파티션 동기화|
|**Glue Crawler**|테이블/스키마 자동 생성|

📌 시험 구분

> _“테이블은 있는데 파티션만 누락”_ → **MSCK**
> _“테이블 자체가 없음”_ → **Crawler**

---

## 🧪 시험에 자주 나오는 문제 유형

### ❓ 문제

> S3에 파티션 구조로 데이터가 저장되어 있다.
> Athena 테이블은 이미 존재하지만
> 최근 추가된 파티션이 쿼리되지 않는다.
> 가장 간단한 해결책은?

✅ 정답

```sql
MSCK REPAIR TABLE table_name;
```

---

## ❌ 오답 유도

- `COPY` ❌ (Redshift)

- `UNLOAD` ❌ (Export)

- Glue Job 실행 ❌ (불필요)

- 테이블 재생성 ❌

---

## ✅ 최종 요약 (암기용)

|항목|핵심|
|---|---|
|MSCK REPAIR TABLE|파티션 메타데이터 동기화|
|대상|Athena / Hive|
|실제 데이터|❌ 변경 없음|
|사용 시점|S3 파티션 추가 후|
|시험 키워드|_“파티션 인식 안 됨”_|

---

### 📌 한 줄 요약 (시험용)

> **MSCK REPAIR TABLE = S3 파티션을 Athena가 알게 만드는 명령**
