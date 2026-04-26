<!-- infographic-hero -->
![Apache Hive: SQL-Based Big Data Warehouse on Hadoop 핵심 요약](figures/infographic.svg)

*Figure: Apache Hive: SQL-Based Big Data Warehouse on Hadoop 한 장 요약 인포그래픽*

# Apache Hive - SQL로 다루는 빅데이터 웨어하우스

## 개요

Hadoop 에코시스템이 등장하면서 페타바이트 규모의 데이터를 분산 저장하고 처리하는 일이 가능해졌습니다. 그러나 MapReduce를 직접 Java로 작성하는 방식은 진입 장벽이 높았고, SQL에 익숙한 분석가나 데이터 엔지니어에게는 상당한 부담이었습니다.

Apache Hive는 이 문제를 정면으로 해결한 프로젝트입니다. Facebook이 내부 데이터 분석 용도로 개발한 후 2008년 Apache 재단에 기증했으며, SQL과 유사한 HiveQL(HQL)을 통해 HDFS에 저장된 대용량 데이터를 쿼리할 수 있게 해줍니다. 사용자가 SELECT 문을 작성하면 Hive가 이를 MapReduce, Tez, 또는 Spark 작업으로 변환하여 실행합니다.

이 글에서는 Hive의 아키텍처와 핵심 개념을 살펴보고, 실전에서 사용하는 HiveQL 문법, 파일 포맷 선택 전략, 성능 최적화 기법, 그리고 현대 데이터 플랫폼에서 Hive가 차지하는 위치까지 체계적으로 정리합니다.

## 핵심 개념

### Hive의 정체: 데이터 웨어하우스 소프트웨어

Hive를 데이터베이스로 오해하는 경우가 많지만, Hive는 데이터베이스가 아닙니다. Hive는 HDFS 위에 테이블이라는 추상화 레이어를 올려놓은 데이터 웨어하우스 소프트웨어입니다. 실제 데이터는 HDFS에 파일 형태로 존재하며, Hive는 그 파일들에 스키마를 입혀서 SQL처럼 쿼리할 수 있게 해주는 역할을 합니다.

이 구조에서 가장 중요한 개념이 Schema on Read입니다.

### Schema on Read vs Schema on Write

전통적인 RDBMS는 Schema on Write 방식을 따릅니다. 데이터를 삽입할 때 스키마를 검증하고, 스키마에 맞지 않는 데이터는 거부합니다. 이 방식은 데이터 정합성을 보장하지만, 스키마 변경 비용이 크고 비정형 데이터를 다루기 어렵습니다.

Hive는 Schema on Read 방식을 채택했습니다. 데이터를 저장할 때는 스키마를 강제하지 않고, 데이터를 읽는 시점에 스키마를 적용합니다. 덕분에 먼저 데이터를 HDFS에 적재하고 나중에 테이블 구조를 정의할 수 있습니다. 스키마가 맞지 않는 필드는 NULL로 처리됩니다.

이 방식은 데이터 레이크 환경에서 특히 유용합니다. 다양한 소스에서 들어오는 데이터를 일단 원본 그대로 저장한 뒤, 분석 목적에 맞게 여러 가지 스키마를 적용할 수 있기 때문입니다.

### HiveQL과 SQL의 차이

HiveQL은 SQL과 문법이 매우 유사하지만, 전통적인 RDBMS와는 근본적인 차이가 있습니다.

| 항목 | Hive (HiveQL) | RDBMS (SQL) |
|------|--------------|-------------|
| 처리 방식 | MapReduce / Tez / Spark 변환 | 인덱스 기반 즉시 처리 |
| 응답 속도 | 배치 처리(수초 ~ 수분) | 실시간(ms 단위) |
| 스키마 적용 | Schema on Read | Schema on Write |
| 데이터 수정 | 제한적 (INSERT OVERWRITE) | UPDATE / DELETE 자유 |
| 적합 용도 | 대용량 배치 분석 | 트랜잭션, OLTP |

특히 응답 속도의 차이가 큽니다. Hive는 간단한 SELECT 쿼리라 하더라도 MapReduce 작업을 생성하고 클러스터에 배포하는 오버헤드가 있어 최소 수십 초가 소요됩니다. 따라서 Hive는 대화형(interactive) 쿼리보다는 배치 분석에 적합합니다.

### Hive Metastore

Hive의 핵심 구성 요소 중 하나가 Metastore입니다. Metastore는 HDFS에 저장된 데이터에 대한 스키마 정보를 관계형 데이터베이스에 저장합니다. 구체적으로 다음과 같은 메타데이터를 관리합니다.

- 데이터베이스 및 테이블 정의(이름, 소유자, 생성 시간)
- 컬럼 이름과 데이터 타입
- 파티션 정보
- HDFS 상의 데이터 위치(LOCATION)
- 저장 포맷(SerDe) 정보

기본적으로 Derby를 내장 데이터베이스로 사용하지만, 운영 환경에서는 MySQL이나 PostgreSQL을 사용합니다. Derby는 단일 세션만 지원하기 때문에 여러 사용자가 동시에 Hive에 접속하는 환경에서는 사용할 수 없습니다.

Metastore는 독립 서비스(Hive Metastore Service, HMS)로 분리하여 운영할 수 있으며, 이 경우 Spark, Presto, Trino 등 다른 쿼리 엔진에서도 동일한 메타데이터를 공유할 수 있습니다. 현대 데이터 레이크 아키텍처에서 Hive Metastore가 여전히 핵심 컴포넌트로 활용되는 이유가 여기에 있습니다.

### Hive 아키텍처

Hive의 쿼리 처리 흐름은 다음과 같습니다.

```
클라이언트 (HiveQL 쿼리 입력)
    |
    v
Driver (쿼리 파싱, 최적화, 실행 계획 생성)
    |
    v
Metastore (스키마/파티션 메타데이터 조회)
    |
    v
Execution Engine (MapReduce / Tez / Spark)
    |
    v
HDFS (실제 데이터 읽기/쓰기)
```

Driver는 내부적으로 여러 단계를 거칩니다. 먼저 Parser가 HiveQL을 AST(Abstract Syntax Tree)로 변환합니다. 그 다음 Semantic Analyzer가 Metastore를 참조하여 테이블과 컬럼의 유효성을 검사합니다. 이후 Optimizer가 실행 계획을 최적화하고, 최종적으로 Execution Engine이 물리적인 작업을 수행합니다.

실행 엔진의 선택은 성능에 큰 영향을 미칩니다. MapReduce는 중간 결과를 디스크에 기록하므로 느린 반면, Tez는 DAG(Directed Acyclic Graph) 기반으로 중간 결과를 메모리에 유지하여 2~3배 빠른 성능을 보입니다. Spark를 실행 엔진으로 사용하면(Hive on Spark) 인메모리 처리의 이점을 최대한 활용할 수 있습니다.

```bash
# 실행 엔진 설정 (hive-site.xml 또는 세션 레벨)
hive> SET hive.execution.engine=tez;
hive> SET hive.execution.engine=spark;
hive> SET hive.execution.engine=mr;  -- MapReduce (기본값, 레거시)
```

### 테이블 유형: Managed Table vs External Table

Hive에는 두 가지 유형의 테이블이 있습니다.

Managed Table(내부 테이블)은 Hive가 데이터의 생명주기를 관리합니다. 테이블을 DROP하면 메타데이터와 함께 HDFS의 실제 데이터도 삭제됩니다.

External Table(외부 테이블)은 Hive가 메타데이터만 관리합니다. 테이블을 DROP해도 HDFS의 원본 데이터는 그대로 남아 있습니다. 여러 팀이 같은 데이터를 다른 스키마로 조회해야 하거나, 원본 데이터를 보존해야 하는 경우에 외부 테이블을 사용합니다.

실무에서는 대부분 External Table을 사용하는 것이 안전합니다. 실수로 테이블을 삭제해도 원본 데이터가 보존되기 때문입니다.

### 파일 포맷 선택

Hive에서 사용할 수 있는 주요 파일 포맷은 다음과 같습니다.

- TEXTFILE: 기본 포맷입니다. CSV, TSV 등 사람이 읽을 수 있는 텍스트 형식이지만, 압축률이 낮고 쿼리 성능이 떨어집니다.
- ORC(Optimized Row Columnar): Hive에 최적화된 컬럼 기반 압축 포맷입니다. 컬럼 단위로 데이터를 저장하므로, 특정 컬럼만 조회하는 분석 쿼리에서 I/O를 크게 줄일 수 있습니다. Predicate Pushdown, 내장 인덱스 등의 최적화 기능을 제공합니다.
- Parquet: 마찬가지로 컬럼 기반 포맷이지만, Spark, Impala, Presto 등 다양한 엔진과의 호환성이 더 좋습니다.
- Avro: 행 기반 직렬화 포맷으로, 스키마 진화(Schema Evolution)를 잘 지원합니다. 스키마가 자주 변경되는 환경에 적합합니다.

Hive 위주의 분석 환경이라면 ORC가 최선의 선택이고, 여러 엔진을 혼용하는 환경이라면 Parquet가 범용적인 선택입니다.

## 실전 코드

### 데이터베이스와 테이블 생성

```sql
-- 데이터베이스 생성 및 선택
CREATE DATABASE IF NOT EXISTS mydb;
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
```

EXTERNAL 키워드를 사용하면 외부 테이블이 됩니다. LOCATION은 HDFS 상의 데이터 디렉토리를 지정합니다. 해당 디렉토리에 CSV 파일을 넣어두면 Hive가 자동으로 인식합니다.

### 파티셔닝 테이블

파티셔닝은 Hive에서 가장 중요한 성능 최적화 기법입니다. 파티션 컬럼의 값에 따라 데이터를 별도의 HDFS 디렉토리에 분리 저장하여, 쿼리 시 불필요한 데이터를 읽지 않도록 합니다.

```sql
-- 파티셔닝 테이블 생성
CREATE TABLE sales_partitioned (
    id      INT,
    product STRING,
    amount  DOUBLE
)
PARTITIONED BY (dt STRING)
STORED AS ORC;

-- 정적 파티션 삽입
INSERT INTO TABLE sales_partitioned PARTITION (dt='2024-01-01')
SELECT id, product, amount FROM sales WHERE dt = '2024-01-01';

-- 동적 파티션 삽입 (파티션 값을 데이터에서 자동 추출)
SET hive.exec.dynamic.partition=true;
SET hive.exec.dynamic.partition.mode=nonstrict;

INSERT INTO TABLE sales_partitioned PARTITION (dt)
SELECT id, product, amount, dt FROM sales;
```

동적 파티셔닝을 사용하면 데이터의 dt 컬럼 값에 따라 자동으로 파티션이 생성됩니다. 예를 들어 dt에 '2024-01-01', '2024-01-02', '2024-01-03' 값이 있으면 HDFS에 세 개의 파티션 디렉토리가 만들어집니다.

```
/user/hive/warehouse/mydb.db/sales_partitioned/
    dt=2024-01-01/
    dt=2024-01-02/
    dt=2024-01-03/
```

파티셔닝된 테이블에 WHERE 조건으로 파티션 컬럼을 지정하면 해당 파티션의 데이터만 스캔합니다. 전체 테이블이 1TB라도 특정 날짜의 파티션이 10GB라면 10GB만 읽게 됩니다.

### 버켓팅(Bucketing)

버켓팅은 파티셔닝의 보완 기법입니다. 파티셔닝만으로는 파티션 하나의 크기가 여전히 클 수 있는데, 버켓팅은 해시 함수를 사용하여 데이터를 고정 개수의 파일로 분할합니다.

```sql
CREATE TABLE sales_bucketed (
    id      INT,
    product STRING,
    amount  DOUBLE
)
PARTITIONED BY (dt STRING)
CLUSTERED BY (product) INTO 32 BUCKETS
STORED AS ORC;
```

버켓팅은 특히 JOIN 성능 개선에 효과적입니다. 두 테이블이 같은 컬럼을 기준으로 같은 수의 버켓으로 나뉘어 있으면, Hive는 Sort-Merge-Bucket JOIN을 수행하여 각 버켓끼리만 조인합니다.

### 분석 쿼리 작성

```sql
-- 일별 제품별 매출 집계
SELECT
    dt,
    product,
    SUM(amount) AS total_amount,
    COUNT(*)    AS order_count,
    AVG(amount) AS avg_amount
FROM sales_partitioned
WHERE dt BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY dt, product
ORDER BY dt, total_amount DESC;

-- 윈도우 함수를 활용한 누적 매출 계산
SELECT
    dt,
    product,
    amount,
    SUM(amount) OVER (
        PARTITION BY product
        ORDER BY dt
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_amount
FROM sales_partitioned
WHERE dt >= '2024-01-01';
```

HiveQL은 GROUP BY, JOIN, 서브쿼리, 윈도우 함수 등 표준 SQL의 주요 기능을 대부분 지원합니다. 다만 RDBMS에 있는 UPDATE, DELETE 문은 ACID 트랜잭션이 활성화된 ORC 테이블에서만 제한적으로 사용할 수 있습니다.

### ACID 트랜잭션 지원

Hive 3.0부터는 제한적이지만 ACID 트랜잭션을 지원합니다.

```sql
-- ACID 트랜잭션을 위한 설정
SET hive.support.concurrency=true;
SET hive.txn.manager=org.apache.hadoop.hive.ql.lockmgr.DbTxnManager;

-- Transactional 테이블 생성 (ORC 필수)
CREATE TABLE accounts (
    account_id INT,
    name       STRING,
    balance    DOUBLE
)
STORED AS ORC
TBLPROPERTIES ('transactional'='true');

-- UPDATE/DELETE 가능
UPDATE accounts SET balance = balance + 1000 WHERE account_id = 1;
DELETE FROM accounts WHERE balance < 0;

-- MERGE (Upsert) 지원
MERGE INTO accounts AS target
USING new_transactions AS source
ON target.account_id = source.account_id
WHEN MATCHED THEN UPDATE SET balance = target.balance + source.amount
WHEN NOT MATCHED THEN INSERT VALUES (source.account_id, source.name, source.amount);
```

ACID를 사용하면 기존에 불가능했던 데이터 수정과 삭제가 가능해집니다. 다만 내부적으로 delta 파일을 생성하는 방식이므로, 주기적으로 compaction을 수행하여 성능을 유지해야 합니다.

## 활용 사례

### 1. 대규모 로그 분석

가장 전통적이면서도 여전히 유효한 사례입니다. 웹 서버, 애플리케이션, IoT 장비에서 생성되는 대량의 로그를 HDFS에 적재하고, Hive로 분석합니다.

```sql
-- 웹 서버 로그 테이블 (일별 파티셔닝)
CREATE EXTERNAL TABLE web_logs (
    ip          STRING,
    timestamp   STRING,
    method      STRING,
    url         STRING,
    status_code INT,
    response_time DOUBLE
)
PARTITIONED BY (log_date STRING)
STORED AS ORC
LOCATION '/data/web_logs/';

-- 시간대별 오류율 분석
SELECT
    SUBSTR(timestamp, 12, 2) AS hour,
    COUNT(CASE WHEN status_code >= 500 THEN 1 END) AS error_count,
    COUNT(*) AS total_count,
    ROUND(COUNT(CASE WHEN status_code >= 500 THEN 1 END) * 100.0 / COUNT(*), 2) AS error_rate
FROM web_logs
WHERE log_date = '2024-01-15'
GROUP BY SUBSTR(timestamp, 12, 2)
ORDER BY hour;
```

일별로 수십 GB의 로그가 쌓여도 파티셔닝과 ORC 포맷의 조합으로 특정 날짜의 데이터를 빠르게 분석할 수 있습니다.

### 2. 데이터 웨어하우스 ETL 파이프라인

Hive는 ETL 파이프라인의 변환(Transform) 단계에서 많이 활용됩니다. 원본 데이터를 정제하고 집계하여 분석용 마트 테이블을 만드는 작업을 HiveQL로 수행합니다.

```sql
-- 원본 데이터(raw) -> 정제 데이터(cleaned) -> 집계 테이블(mart)
-- Step 1: 정제
INSERT OVERWRITE TABLE sales_cleaned PARTITION (dt)
SELECT
    id,
    TRIM(LOWER(product)) AS product,
    CASE WHEN amount < 0 THEN 0 ELSE amount END AS amount,
    dt
FROM sales_raw
WHERE id IS NOT NULL;

-- Step 2: 일별 집계 마트 생성
INSERT OVERWRITE TABLE daily_sales_mart PARTITION (dt)
SELECT
    product,
    SUM(amount) AS daily_total,
    COUNT(*) AS order_count,
    dt
FROM sales_cleaned
GROUP BY product, dt;
```

INSERT OVERWRITE를 사용하면 기존 파티션의 데이터를 덮어쓸 수 있어, 멱등성(idempotency) 있는 파이프라인을 구축할 수 있습니다. 같은 배치를 여러 번 실행해도 결과가 동일하다는 뜻입니다.

### 3. Hive Metastore를 활용한 데이터 레이크

현대 데이터 아키텍처에서 Hive의 가장 중요한 역할은 Metastore입니다. Hive 쿼리 엔진 자체는 Trino(구 PrestoSQL)나 Spark SQL로 대체되는 추세이지만, Hive Metastore는 데이터 레이크의 중앙 카탈로그로 계속 사용됩니다.

```
┌─────────────────────────────────────────────┐
│          Hive Metastore Service              │
│     (테이블, 파티션, 스키마 메타데이터)        │
├─────────────────────────────────────────────┤
│                    │                         │
│   Spark SQL    Trino/Presto    Hive CLI      │
│      │              │             │          │
│      └──────────────┼─────────────┘          │
│                     │                        │
│          HDFS / S3 / Cloud Storage           │
└─────────────────────────────────────────────┘
```

AWS EMR, Google Dataproc 같은 클라우드 빅데이터 서비스에서도 Hive Metastore를 기본으로 통합하고 있으며, AWS Glue Data Catalog는 Hive Metastore의 API 호환 서비스입니다.

### 4. Hive vs Pig: 용도에 따른 선택

같은 Hadoop 에코시스템 안에서 Hive와 자주 비교되는 프로젝트가 Pig입니다.

| 항목 | Hive | Pig |
|------|------|-----|
| 언어 | HiveQL (SQL 유사) | Pig Latin (절차적) |
| 대상 사용자 | SQL 친숙한 분석가 | ETL 개발자 |
| 적합 용도 | 구조화된 데이터 분석 | 비정형 데이터 ETL |
| 실행 엔진 | MapReduce / Tez / Spark | MapReduce |

SQL에 익숙한 팀이라면 Hive가 자연스러운 선택이고, 복잡한 데이터 변환 로직이 필요한 ETL 작업에서는 Pig가 더 유연합니다. 다만 Pig는 현재 Apache 재단에서 은퇴(retired) 상태이므로, 신규 프로젝트에서는 Spark를 사용하는 것이 일반적입니다.

## 성능 최적화 팁

Hive를 실무에서 사용할 때 알아두면 좋은 최적화 기법을 정리합니다.

### 파티션 프루닝

WHERE 절에 반드시 파티션 컬럼을 포함하여 불필요한 데이터 스캔을 방지합니다. 파티션 프루닝이 작동하지 않으면 전체 테이블 풀 스캔이 발생합니다.

### 적절한 파일 포맷과 압축

분석용 테이블은 ORC 또는 Parquet 포맷을 사용합니다. Snappy 또는 Zlib 압축을 적용하면 I/O를 줄이면서도 CPU 오버헤드를 적정 수준으로 유지할 수 있습니다.

```sql
CREATE TABLE optimized_table (
    col1 STRING,
    col2 INT
)
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');
```

### Map Join 활용

작은 테이블과 큰 테이블을 조인할 때 Map Join을 사용하면 Reduce 단계 없이 Map 단계에서 조인을 완료합니다.

```sql
SET hive.auto.convert.join=true;
SET hive.mapjoin.smalltable.filesize=25000000;  -- 25MB 이하 테이블 자동 Map Join

SELECT /*+ MAPJOIN(d) */
    s.product,
    d.category_name,
    SUM(s.amount)
FROM sales s
JOIN dim_category d ON s.category_id = d.id
GROUP BY s.product, d.category_name;
```

### Vectorized Query Execution

Hive 0.13부터 지원하는 벡터화 실행은 한 번에 하나의 행이 아니라 1024개의 행을 묶어서 처리합니다. ORC 포맷과 함께 사용하면 쿼리 성능이 크게 향상됩니다.

```hql
SET hive.vectorized.execution.enabled=true;
SET hive.vectorized.execution.reduce.enabled=true;
```

## 정리

Apache Hive는 Hadoop 에코시스템에서 SQL 인터페이스를 통해 대용량 데이터를 분석할 수 있게 해주는 데이터 웨어하우스 소프트웨어입니다. 이 글에서 다룬 내용을 요약하면 다음과 같습니다.

첫째, Hive는 데이터베이스가 아니라 HDFS 위에 테이블 추상화를 제공하는 소프트웨어입니다. Schema on Read 방식으로 동작하며, HiveQL을 MapReduce/Tez/Spark 작업으로 변환하여 실행합니다.

둘째, Metastore는 Hive의 핵심 컴포넌트로, 테이블 스키마와 파티션 정보를 관리합니다. 현대 데이터 레이크에서도 중앙 카탈로그로 활용되고 있으며, Spark, Trino 등 다른 엔진과 메타데이터를 공유할 수 있습니다.

셋째, 성능 최적화의 핵심은 파티셔닝, 적절한 파일 포맷(ORC/Parquet) 선택, 그리고 실행 엔진(Tez/Spark)의 활용입니다.

넷째, Hive 쿼리 엔진 자체는 Trino나 Spark SQL로 대체되는 추세이지만, Hive Metastore는 AWS Glue Data Catalog 등의 형태로 여전히 데이터 플랫폼의 근간을 이루고 있습니다.

데이터 엔지니어로서 Hive를 이해하는 것은 단순히 하나의 도구를 배우는 것이 아니라, 분산 환경에서의 데이터 웨어하우징 원리를 이해하는 것입니다. 이 개념은 클라우드 기반의 현대 데이터 플랫폼에서도 그대로 적용됩니다.

---

참고 자료:
- [Apache Hive 공식 문서](https://hive.apache.org/)
- [Hive Language Manual](https://cwiki.apache.org/confluence/display/Hive/LanguageManual)
- [Programming Hive (Edward Capriolo 외)](https://www.oreilly.com/library/view/programming-hive/9781449326944/)