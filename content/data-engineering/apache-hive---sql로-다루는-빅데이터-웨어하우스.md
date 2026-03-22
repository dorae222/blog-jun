---
title: "Apache Hive - SQL로 다루는 빅데이터 웨어하우스"
slug: "apache-hive---sql로-다루는-빅데이터-웨어하우스"
category: "data-engineering"
tags: ["bigdata", "data-warehouse", "hadoop", "hive", "hiveql", "metastore", "orc", "schema-on-read"]
status: published
post_type: tutorial
quality_score: 7.0
created_at: "2026-03-02T01:08:46.844597+00:00"
---

# Apache Hive - SQL로 다루는 빅데이터 웨어하우스

## Hive란?

Apache Hive는 Hadoop 위에서 동작하는 데이터 웨어하우스 소프트웨어다. SQL과 유사한 **HiveQL(HQL)** 쿼리 언어를 제공하여, MapReduce 프로그래밍 없이도 HDFS에 저장된 대용량 데이터를 분석할 수 있다. Facebook이 내부 데이터 분석 용도로 개발한 후 Apache 재단에 기증하였다.

## HiveQL vs SQL 비교

Hive는 SQL과 문법이 매우 유사하지만, 전통적인 RDBMS와는 근본적인 차이가 있다.

| 항목 | Hive (HiveQL) | RDBMS (SQL) |
|------|--------------|-------------|
| 처리 방식 | MapReduce / Tez / Spark 변환 | 인덱스 기반 즉시 처리 |
| 응답 속도 | 배치 처리(수초 ~ 수분) | 실시간(ms 단위) |
| 스키마 적용 | Schema on Read | Schema on Write |
| 데이터 수정 | 제한적 (INSERT OVERWRITE) | UPDATE / DELETE 자유 |
| 적합 용도 | 대용량 배치 분석 | 트랜잭션, OLTP |

## Hive Metastore

Hive의 핵심 구성 요소 중 하나가 **Metastore**다. Metastore는 HDFS에 저장된 데이터에 대한 스키마 정보(테이블명, 컬럼, 데이터 타입, HDFS 경로 등)를 관계형 데이터베이스(기본적으로 Derby, 운영환경에서는 MySQL/PostgreSQL)에 저장한다.

- Metastore를 통해 HDFS의 원시 데이터를 테이블 형태로 추상화할 수 있다.
- Schema on Read 방식이므로, 데이터를 저장할 때 스키마를 강제하지 않고 읽을 때 스키마를 적용한다.

## HiveQL 기본 문법

```sql
-- 데이터베이스 생성 및 선택
CREATE DATABASE mydb;
USE mydb;

-- 외부 테이블 생성 (HDFS 경로의 기존 데이터 참조)
CREATE EXTERNAL TABLE sales (
    id      INT,
    product STRING,
    amount  DOUBLE,
    dt      STRING
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/user/hive/warehouse/sales/';

-- 파티셔닝 테이블 (대용량 데이터 성능 최적화)
CREATE TABLE sales_partitioned (
    id      INT,
    product STRING,
    amount  DOUBLE
)
PARTITIONED BY (dt STRING)
STORED AS ORC;

-- 데이터 조회
SELECT product, SUM(amount) AS total
FROM sales
WHERE dt = '2024-01-01'
GROUP BY product
ORDER BY total DESC;

-- 데이터 삽입
INSERT INTO TABLE sales_partitioned PARTITION (dt='2024-01-01')
SELECT id, product, amount FROM sales WHERE dt = '2024-01-01';
```

## Hive 아키텍처

```
클라이언트 (HiveQL 쿼리 입력)
    ↓
Driver (쿼리 파싱, 최적화, 실행 계획 생성)
    ↓
Metastore (스키마/파티션 메타데이터 조회)
    ↓
Execution Engine (MapReduce / Tez / Spark)
    ↓
HDFS (실제 데이터 읽기/쓰기)
```

## Hive 파일 포맷

- **TEXTFILE**: 기본 포맷. 사람이 읽을 수 있으나 성능이 낮다.
- **ORC(Optimized Row Columnar)**: 컬럼 기반 압축 포맷. Hive에 최적화되어 쿼리 성능이 높다.
- **Parquet**: 컬럼 기반 포맷. Spark, Impala 등과 호환성이 좋다.
- **Avro**: 행 기반 직렬화 포맷. 스키마 진화(Schema Evolution)를 지원한다.

## Hive vs Pig 비교

| 항목 | Hive | Pig |
|------|------|-----|
| 언어 | HiveQL (SQL 유사) | Pig Latin (절차적) |
| 대상 사용자 | SQL 친숙한 분석가 | ETL 개발자 |
| 최적 용도 | 구조화된 데이터 분석 | 비정형 데이터 ETL |
| 실행 엔진 | MapReduce / Tez / Spark | MapReduce |
