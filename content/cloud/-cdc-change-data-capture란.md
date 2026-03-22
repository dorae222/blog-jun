---
title: "🔄 CDC (Change Data Capture)란?"
slug: "-cdc-change-data-capture란"
category: cloud
tags: ["amazon-s3", "aws", "aws-dms", "cdc", "change-data-capture", "data-lake", "data-pipeline", "data-replication", "kinesis"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.340901+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - CDC
---
## 🔄 CDC (Change Data Capture)란?

**CDC**는 데이터베이스의 **변경된 레코드(데이터 변화)를 캡처하고 추출**하여, 분석, 동기화, 데이터 레이크 적재 등 다양한 목적을 위해 **다른 시스템으로 전송**하는 기법입니다.

---

## 📌 AWS DMS에서의 CDC

- **AWS DMS**는 단순한 마이그레이션 도구를 넘어 **데이터 스트리밍 파이프라인** 구축에도 활용됩니다.

- DMS 복제 작업은 일반적으로 다음 두 단계로 동작합니다:

|단계|설명|
|---|---|
|**1. 전체 로드(Full Load)**|초기 전체 데이터를 대상(예: S3 등)으로 적재합니다.|
|**2. CDC**|그 이후 원본 DB에서 발생하는 변경 사항을 **지속적으로 추적하여 전송**합니다.|

즉, **CDC는 초기 전체 적재 이후 변경분만 지속적으로 복제하는 기능**입니다.

---

## 🧠 CDC의 활용 목적

|목적|설명|
|---|---|
|🧩 **데이터 레이크 연동**|예: 변경된 데이터를 Amazon S3에 지속 스트리밍하여 분석용 데이터 레이크를 구성합니다.|
|🔄 **DB 복제/동기화**|주 데이터베이스와 보조 시스템 간의 데이터 동기화에 사용됩니다.|
|📊 **실시간 분석**|최신 데이터를 기반으로 실시간 분석을 수행할 때 유용합니다 (예: Kinesis, Athena 등과 연계).|
|🪄 **이벤트 기반 처리**|데이터 변경 이벤트를 기반으로 Lambda 등 트리거를 실행할 수 있습니다.|

---

## ✅ 요약

|항목|내용|
|---|---|
|용어|**CDC (Change Data Capture)**|
|의미|DB의 **변경된 데이터만 감지하여 추출·전송**하는 방식|
|AWS 서비스 연계|**AWS DMS**에서 Full Load 이후 CDC를 활성화하여 사용 가능|
|대상 예시|**Amazon S3, Redshift, Kinesis, DynamoDB 등**|
|주요 장점|**실시간 동기화**, 네트워크/스토리지 비용 절감, **최신 데이터 기반 분석**|
