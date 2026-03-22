---
title: AWS Glue for Apache Spark
slug: "aws-glue-for-apache-spark"
category: cloud
tags: ["apache-spark", "aws", "aws-glue", "data-catalog", "etl", "glue-dynamicframe", "glue-studio", "pyspark", "serverless"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.994204+00:00"
---

## 🧩 Quick Overview

| 항목              | 설명 |
|-------------------|------|
| **이름**           | AWS Glue for Apache Spark |
| **유형**           | **서버리스 분산 처리 기반 ETL 엔진** |
| **핵심 역할**       | Apache Spark를 기반으로 **데이터 추출, 변환, 적재(ETL)** 작업을 **코드 또는 시각적으로 수행** |
| **통합 서비스**     | AWS Glue Studio, Glue Job, Glue Data Catalog, Crawler 등과 함께 사용 |

> ⚙️ **AWS Glue for Apache Spark**는 Glue 작업(Glue Job) 내에서 실행되는 Spark 엔진으로,
> **대용량 데이터의 전처리, 통합, 정제, 변환 작업을 분산 환경에서 처리**할 수 있도록 합니다.

---

## 🔥 핵심 특징

| 항목 | 설명 |
|------|------|
| **서버리스 실행** | 클러스터를 직접 관리하지 않고도 Spark 기반 작업을 실행할 수 있습니다 |
| **자동 스케일링** | 데이터 양에 따라 워커 노드를 자동으로 확장/축소합니다 |
| **Spark SQL/PySpark 지원** | 기존 Spark API를 그대로 사용할 수 있습니다 (`glueContext`, `SparkSession`) |
| **Glue DynamicFrame 제공** | Spark DataFrame보다 Glue 환경에 최적화된 래퍼 객체를 제공합니다 |
| **Glue Studio 연계** | GUI 기반의 시각적 ETL 설계를 Spark 코드로 실행할 수 있습니다 |

---

## ✅ 일반 사용 예시

```python
from awsglue.context import GlueContext
from pyspark.context import SparkContext

sc = SparkContext()
glueContext = GlueContext(sc)

datasource = glueContext.create_dynamic_frame.from_catalog(
    database="my_db",
    table_name="my_table"
)

transformed = datasource.drop_fields(['ssn', 'dob'])
glueContext.write_dynamic_frame.from_options(
    frame=transformed,
    connection_type="s3",
    connection_options={"path": "s3://my-output"},
    format="parquet"
)
````

---

## 📦 Glue DynamicFrame vs Spark DataFrame

|항목|DynamicFrame|DataFrame|
|---|---|---|
|**타입 유연성**|더 유연 (스키마 없음 허용)|스키마가 명확히 정의되어야 함|
|**변환 작업**|`.apply_mapping()`, `.resolveChoice()` 등 Glue 전용 변환 지원|Spark SQL 및 DataFrame API 사용|
|**Glue 통합성**|Crawler, Catalog, S3 Sink 등과 원활히 연동되도록 설계|범용 Spark 코드로 Glue 친화성은 상대적으로 낮음|

---

## ✅ 장점

|항목|설명|
|---|---|
|**대규모 데이터 처리에 적합**|수 TB 이상 규모의 데이터 전처리 및 통합에 적합합니다|
|**서버 관리 불필요**|클러스터 프로비저닝이나 종료 같은 운영 부담을 줄여줍니다|
|**ETL 파이프라인 통합 용이**|Glue Workflow, Trigger 등과 연동하여 파이프라인 자동화가 쉽습니다|
|**Data Catalog 자동 활용**|스키마 자동 인식 및 중앙화된 메타데이터 관리를 지원합니다|

---

## ⚠️ 유의사항

|항목|설명|
|---|---|
|**Job 실행 시간에 따라 요금 발생**|초 단위 과금 모델이므로 비용 최적화가 필요합니다|
|**초기 Cold Start 존재**|작업 시작 시 몇 분의 준비 시간이 발생할 수 있습니다|
|**실시간 처리에는 부적합**|배치 중심 아키텍처이며 실시간 스트리밍 처리는 Glue Streaming을 고려해야 합니다|

---

## 🧾 요약

|항목|설명|
|---|---|
|**정의**|AWS Glue 환경에서 Apache Spark를 서버리스로 실행해 **분산 ETL 작업을 수행**할 수 있게 하는 구성 요소입니다|
|**기능**|PySpark 기반 코드 실행, DynamicFrame 사용, 자동 스케일링, Glue Studio와의 통합을 지원합니다|
|**장점**|대규모 데이터 전처리에 적합하고 운영 부담을 줄여주며 ETL 자동화가 용이합니다|
|**활용 사례**|로그 정제, 데이터 웨어하우스 적재 전 처리, 데이터 마이그레이션 등 |
