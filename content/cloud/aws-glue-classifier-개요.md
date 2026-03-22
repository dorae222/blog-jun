---
title: AWS Glue Classifier 개요
slug: "aws-glue-classifier-개요"
category: cloud
tags: ["aws", "aws-glue", "crawler", "custom-classifier", "data-catalog", "etl", "glue-classifier", "s3", "schema-inference"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.849809+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

**AWS Glue Classifier**는
AWS Glue가 **데이터 소스의 형식과 스키마를 자동으로 식별**하기 위해 사용하는 **규칙 집합**입니다.

---

## 한 줄 정의

> **AWS Glue Classifier는 데이터 파일의 포맷과 컬럼 구조를 판별하기 위한 메타데이터 인식 규칙이다.**

---

## 왜 Classifier가 필요한가?

Glue Crawler가 S3, JDBC 등에서 데이터를 탐색할 때 다음을 알아야 테이블을 생성할 수 있습니다:

- 이 파일이 **CSV인지, JSON인지, Parquet인지**
- 컬럼은 무엇이고 타입은 무엇인지

이 판단을 하는 것이 바로 **Classifier**입니다.

---

## Classifier의 역할

1. 데이터 포맷 식별
2. 스키마 추론 (컬럼명, 타입)
3. Glue Data Catalog 테이블 생성 지원

---

## 기본 제공 Classifier

AWS Glue는 여러 **내장 Classifier**를 제공합니다.

|Classifier|대상|
|---|---|
|CSV|CSV 파일|
|JSON|JSON 파일|
|Parquet|Parquet|
|ORC|ORC|
|Avro|Avro|
|XML|XML|
|Grok|로그 패턴|

---

## Custom Classifier (중요)

기본 분류기로 인식되지 않는 경우 **사용자 정의 Classifier**를 생성할 수 있습니다.

### 예: Custom CSV Classifier

- 구분자(`|`, `;` 등) 지정
- 헤더 여부
- 따옴표 문자
- 날짜 포맷

---

## Crawler + Classifier 관계

```text
Glue Crawler
   └─ Classifier 적용
        └─ 데이터 포맷/스키마 인식
             └─ Glue Data Catalog 테이블 생성
```

- Crawler는 여러 Classifier를 순서대로 적용합니다.
- 가장 먼저 매칭되는 Classifier를 사용합니다.

---

## Classifier vs Schema Registry

|구분|Classifier|Schema Registry|
|---|---|---|
|용도|스키마 **추론**|스키마 **관리/버전**|
|사용 시점|수집 시|생산/소비 시|
|Glue 구성요소|✅|별도 서비스|

---

## 언제 Classifier를 쓰나?

- Crawler가 데이터를 잘못 인식할 때
- CSV/로그 포맷이 비표준일 때
- XML/로그 구조가 복잡할 때

---

## 시험 대비 핵심 포인트

- “데이터 포맷 자동 인식” → **Classifier**
- “Crawler가 스키마 추론” → **Classifier**
- “Custom 포맷 처리” → **Custom Classifier**