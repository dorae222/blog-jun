---
title: ORC 형식(Optimized Row Columnar)
slug: "orc-형식optimized-row-columnar"
category: cloud
tags: ["amazon-athena", "aws", "aws-glue", "big-data", "columnar-storage", "data-lake", "emr", "hive", "orc", "parquet"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.205697+00:00"
---

ORC 형식(Optimized Row Columnar)은 대규모 분석 워크로드를 위해 설계된 고성능 컬럼 기반(Columnar) 저장 포맷입니다.

---

## 한 줄 정의

> ORC는 데이터를 컬럼 단위로 저장하고 고급 압축·인덱싱을 제공하는 분석 최적화 파일 포맷이다.

---

## ORC의 핵심 특징

### 1️⃣ 컬럼 기반 저장 (Columnar Storage)

- 필요한 컬럼만 읽음
- 디스크 I/O 최소화
- 집계·스캔 성능 우수

---

### 2️⃣ 강력한 압축

- 컬럼별 압축
- ZLIB, Snappy 등 지원
- 저장 비용 절감

---

### 3️⃣ 내장 인덱스

- Min/Max 값, Row Group 정보
- 불필요한 데이터 블록 스킵
- 쿼리 성능 향상

---

### 4️⃣ 타입 정보 포함

- 스키마 포함
- 정형 데이터에 강함
- 스키마 진화 제한적 지원

---

## ORC vs 다른 포맷

|포맷|저장 방식|주 용도|
|---|---|---|
|ORC|컬럼 기반|Hive, 대규모 분석|
|Parquet|컬럼 기반|범용 분석|
|AVRO|행 기반|스트리밍|
|JSON|텍스트|로그/API|
|CSV|텍스트|단순 데이터|

---

## ORC vs Parquet (시험 포인트)

|항목|ORC|Parquet|
|---|---|---|
|최초 개발|Apache Hive|Twitter/Cloudera|
|압축·인덱스|매우 강력|강력|
|Hive 친화성|**최고**|높음|
|범용성|중간|**높음**|

---

## AWS에서 ORC 사용

- Amazon Athena
- AWS Glue
- Amazon EMR (Hive)
- Presto/Trino

---

## 언제 ORC를 쓰나?

- Hive 중심 데이터 레이크
- 대규모 배치 분석
- 컬럼 기반 집계 위주

---

## 핵심 포인트

- “컬럼 기반 포맷” → ORC
- “고급 압축·인덱스” → ORC
- “대규모 분석 성능 최적화” → ORC