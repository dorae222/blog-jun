---
title: "🔹 Amazon Redshift `UNLOAD`란?"
slug: "-amazon-redshift-unload란"
category: cloud
tags: ["amazon-redshift", "aws", "copy-command", "data-archiving", "parquet", "redshift", "s3", "spectrum", "unload"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.668752+00:00"
---

# 🔹 Amazon Redshift `UNLOAD`란?

> **Amazon Redshift UNLOAD**는  
> **Redshift 테이블(또는 쿼리 결과)을 Amazon S3로 내보내는 SQL 명령어**입니다.

📌 한 줄 정의

> **UNLOAD = Redshift → S3 데이터 내보내기(Export)**

---

## 🧠 UNLOAD의 역할을 한 문장으로 보면

> **Redshift에 있는 오래된(Cold) 데이터를 S3로 옮겨 클러스터 스토리지와 비용을 줄이기 위한 기능입니다.**

---

## 🏗️ 동작 개념

```text
[Amazon Redshift]
 (Table / Query Result)
        │
        │  UNLOAD
        ▼
[Amazon S3]
 (CSV / Parquet / JSON)
```

- Redshift → S3 **단방향**

- 대량 데이터도 병렬로 빠르게 Export

---

## 🧩 UNLOAD의 핵심 특징 (시험 포인트)

|항목|설명|
|---|---|
|대상|**테이블 또는 SELECT 결과**|
|목적|데이터 아카이빙 / 공유|
|저장 위치|**Amazon S3**|
|형식|CSV, Parquet, JSON|
|성능|병렬 처리|
|자동화|스케줄링 가능 (월별 등)|

---

## 🧪 질문 문장 다시 해석해보자

> **“UNLOAD 명령을 사용하여 15개월 이상 된 데이터를 Amazon S3에 복사”**

### 의미는?

- Redshift 테이블 중  
    👉 **15개월 이상 된 오래된 레코드만 SELECT**
    
- 그 결과를  
    👉 **UNLOAD로 S3에 Export**
    
```sql
UNLOAD ('
  SELECT *
  FROM sales
  WHERE sale_date < dateadd(month, -15, current_date)
')
TO 's3://my-archive-bucket/sales/'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftRole'
FORMAT AS PARQUET;
```

---

## 🧠 왜 UNLOAD + Spectrum 조합을 쓰는가? (시험 핵심)

|단계|이유|
|---|---|
|UNLOAD → S3|Redshift 스토리지 비용 ↓|
|Redshift에서 DELETE|클러스터 성능 유지|
|Spectrum|S3의 과거 데이터도 SQL로 조회 가능|

📌 시험 키워드

> **“Hot / Cold 데이터 분리”**  
> **“Redshift 비용 최적화”**

---

## 🆚 UNLOAD vs COPY (헷갈리는 포인트)

|명령|방향|용도|
|---|---|---|
|**COPY**|S3 → Redshift|데이터 적재|
|**UNLOAD**|Redshift → S3|데이터 내보내기|

📌 시험에서 COPY/UNLOAD 방향 바꾸면 바로 오답

---

## ❌ UNLOAD가 아닌 경우

- 실시간 스트리밍 ❌
    
- ETL 변환 ❌
    
- S3 → Redshift ❌ (COPY 사용)
    
---

## ✅ 최종 요약 (암기용)

|항목|핵심|
|---|---|
|UNLOAD|Redshift → S3 Export|
|사용 목적|아카이빙, 비용 절감|
|시험 조합|**UNLOAD + Spectrum**|
|반대 명령|COPY|

---

### 📌 한 줄 요약 (시험용)

> **UNLOAD = Redshift 데이터를 S3로 빼는 명령어**
