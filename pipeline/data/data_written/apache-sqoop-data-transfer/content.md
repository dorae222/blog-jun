<!-- infographic-hero -->
![Apache Sqoop: Bridging RDBMS and Hadoop for Efficient Data Transfer 핵심 요약](figures/infographic.svg)

*Figure: Apache Sqoop: Bridging RDBMS and Hadoop for Efficient Data Transfer 한 장 요약 인포그래픽*

# Apache Sqoop 완벽 가이드: RDBMS와 Hadoop 간 대용량 데이터 전송의 모든 것

## 개요

기업 환경에서 데이터는 다양한 시스템에 분산되어 있다. 운영 데이터는 MySQL, Oracle, PostgreSQL 같은 **RDBMS**에 저장되고, 대규모 분석과 배치 처리는 **Hadoop/HDFS** 기반 데이터 레이크에서 수행된다. 이 두 세계를 연결하는 핵심 도구가 바로 **Apache Sqoop**이다.

Sqoop은 **SQL-to-Hadoop**의 약어로, RDBMS(MySQL, Oracle, PostgreSQL 등)와 Hadoop 에코시스템(HDFS, Hive, HBase) 간에 **대용량 데이터를 효율적으로 전송**하기 위해 설계된 도구다. 내부적으로 MapReduce를 활용하여 병렬 데이터 전송을 수행하며, JDBC 커넥터를 통해 다양한 데이터베이스를 지원한다.

이 글에서는 Sqoop의 핵심 개념, Import/Export 메커니즘, 실전 사용법, 그리고 현대적 대안 도구들을 체계적으로 다룬다.

## 핵심 개념

### Sqoop이란?

Sqoop은 Apache Software Foundation에서 개발한 오픈소스 프로젝트로, 다음과 같은 핵심 기능을 제공한다:

1. **Import**: RDBMS → Hadoop (HDFS/Hive/HBase)으로 데이터 적재
2. **Export**: Hadoop → RDBMS로 분석 결과 전송
3. **병렬 전송**: MapReduce 기반의 병렬 데이터 이동으로 높은 처리량 보장
4. **증분 Import**: 변경된 데이터만 선택적으로 전송
5. **직접 쿼리**: Hadoop에서 RDBMS에 직접 SQL 쿼리 실행

### Sqoop의 동작 원리

Sqoop은 데이터 전송 시 내부적으로 **MapReduce 작업**을 생성하여 실행한다. 이를 통해 하나의 거대한 데이터 전송을 여러 개의 Map Task로 분할하여 병렬로 처리한다.

```
┌──────────────────────────────────────────────────┐
│                  Sqoop Import 흐름                │
├──────────────────────────────────────────────────┤
│                                                  │
│  RDBMS(MySQL)  ──JDBC──→  Sqoop  ──MapReduce──→  │
│                                                  │
│  ┌──────────┐         ┌─────────────┐            │
│  │ Table    │  ──→    │ Map Task 1  │ ──→ HDFS   │
│  │ (100만행) │         │ (25만행)    │    Part 1   │
│  │          │  ──→    │ Map Task 2  │ ──→ HDFS   │
│  │          │         │ (25만행)    │    Part 2   │
│  │          │  ──→    │ Map Task 3  │ ──→ HDFS   │
│  │          │         │ (25만행)    │    Part 3   │
│  │          │  ──→    │ Map Task 4  │ ──→ HDFS   │
│  └──────────┘         │ (25만행)    │    Part 4   │
│                       └─────────────┘            │
└──────────────────────────────────────────────────┘
```

기본적으로 **4개의 Map Task**를 사용하며(`--num-mappers` 또는 `-m` 옵션으로 조절 가능), 테이블의 Primary Key를 기준으로 데이터를 균등하게 분배한다.

### Sqoop 1 vs Sqoop 2

| 특성 | Sqoop 1 | Sqoop 2 |
|------|---------|----------|
| 아키텍처 | CLI 기반 | Server + Client 구조 |
| 커넥터 | JDBC 직접 사용 | 커넥터 API (플러그인) |
| 보안 | 명령줄에 비밀번호 노출 | Role 기반 보안 |
| 상태 | **가장 널리 사용** | 개발 중단됨 |
| Hive 직접 Import | 지원 | 미지원 |

**참고**: 실무에서는 대부분 Sqoop 1을 사용하며, Sqoop 2는 사실상 폐기되었다.

## 아키텍처

### Sqoop Import 아키텍처

```
┌────────────┐      ┌──────────┐      ┌────────────────┐
│            │      │          │      │                │
│   RDBMS    │─JDBC─│  Sqoop   │─MR──→│     HDFS       │
│            │      │ Client   │      │                │
│ ┌────────┐ │      │          │      │ ┌────────────┐ │
│ │ MySQL  │ │      │ ┌──────┐ │      │ │ /user/data │ │
│ │ Oracle │ │      │ │Code  │ │      │ │  part-m-00 │ │
│ │ PgSQL  │ │      │ │Gen   │ │      │ │  part-m-01 │ │
│ └────────┘ │      │ └──────┘ │      │ │  part-m-02 │ │
│            │      │          │      │ │  part-m-03 │ │
└────────────┘      └──────────┘      └────────────────┘
                         │
                    ┌────┴────┐
                    │  Hive   │
                    │  HBase  │
                    │  등 지원 │
                    └─────────┘
```

Sqoop Import의 핵심 단계:

1. **메타데이터 수집**: JDBC를 통해 테이블 스키마 정보 획득
2. **코드 생성**: Java 클래스를 자동 생성 (직렬화/역직렬화 담당)
3. **MapReduce 실행**: 생성된 코드로 병렬 데이터 전송 수행
4. **데이터 저장**: HDFS에 텍스트/Parquet/Avro 등의 형식으로 저장

### Sqoop Export 아키텍처

Export는 Import의 역방향이다. HDFS의 파일을 읽어 RDBMS 테이블에 INSERT 또는 UPDATE를 수행한다.

**중요**: Export 시 대상 RDBMS에 테이블이 **미리 생성되어 있어야** 한다. Sqoop은 테이블을 자동 생성하지 않는다.

## 실전 예제

### 기본 Import: 단일 테이블

```bash
# MySQL의 employees 테이블을 HDFS로 Import
sqoop import \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --table employees \
    --target-dir /tmp/sqoop_output/employees \
    --num-mappers 4

# 결과 확인
hadoop fs -ls /tmp/sqoop_output/employees/
# -rw-r--r--   part-m-00000
# -rw-r--r--   part-m-00001
# -rw-r--r--   part-m-00002
# -rw-r--r--   part-m-00003

hadoop fs -cat /tmp/sqoop_output/employees/*
```

### 복수 테이블 일괄 Import

```bash
# 데이터베이스의 모든 테이블 Import (특정 테이블 제외)
sqoop import-all-tables \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --exclude-tables 'temp_logs,staging_data' \
    --warehouse-dir /tmp/sqoop_all_tables

# 결과 구조:
# /tmp/sqoop_all_tables/employees/part-m-00000
# /tmp/sqoop_all_tables/departments/part-m-00000
# /tmp/sqoop_all_tables/salaries/part-m-00000
```

**주의**: `import-all-tables` 사용 시 `--target-dir` 대신 `--warehouse-dir`을 사용해야 한다. `--warehouse-dir`은 지정 경로 아래에 각 테이블명으로 하위 디렉토리를 자동 생성한다.

### 특정 컬럼/조건 Import

```bash
# 특정 컬럼만 Import
sqoop import \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --table employees \
    --columns 'id,name,department,salary' \
    --target-dir /tmp/sqoop_selected

# WHERE 조건 추가
sqoop import \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --table employees \
    --where 'department="Engineering" AND salary > 50000' \
    --target-dir /tmp/sqoop_filtered

# 자유 쿼리 Import (--query 사용)
sqoop import \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --query 'SELECT e.name, d.dept_name, e.salary \
             FROM employees e JOIN departments d \
             ON e.dept_id = d.id \
             WHERE $CONDITIONS' \
    --split-by e.id \
    --target-dir /tmp/sqoop_joined
```

**`$CONDITIONS` 플레이스홀더**: `--query` 옵션 사용 시 반드시 WHERE 절에 `$CONDITIONS`를 포함해야 한다. Sqoop이 이를 각 Map Task의 데이터 분할 조건으로 대체한다.

### Export: Hadoop → RDBMS

```bash
# 사전 작업: MySQL에 대상 테이블 생성
mysql -u root -p
> CREATE TABLE employees_export (
>     id INT PRIMARY KEY,
>     name VARCHAR(100),
>     department VARCHAR(50),
>     salary DOUBLE
> );

# HDFS → MySQL Export
sqoop export \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --table employees_export \
    --export-dir /tmp/sqoop_output/employees \
    --input-fields-terminated-by ','

# 결과 확인
mysql -u root -p -e "SELECT * FROM company_db.employees_export LIMIT 10;"
```

### Sqoop eval: 직접 쿼리 실행

```bash
# Hadoop 환경에서 RDBMS에 직접 SQL 실행
sqoop eval \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --query 'SELECT * FROM employees WHERE department="Engineering"'

# INSERT도 가능
sqoop eval \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --query 'INSERT INTO employees VALUES (101, "New Employee", "Data", 75000)'

# 데이터베이스/테이블 목록 확인
sqoop list-databases \
    --connect jdbc:mysql://localhost:3306/ \
    --username root \
    --password mypassword

sqoop list-tables \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword
```

### 증분 Import (Incremental Import)

실무에서 가장 중요한 기능 중 하나인 증분 Import는 이전 Import 이후 변경된 데이터만 전송한다:

```bash
# append 모드 - 새로 추가된 행만 Import (증가하는 ID 기준)
sqoop import \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --table employees \
    --target-dir /tmp/sqoop_incremental \
    --incremental append \
    --check-column id \
    --last-value 1000

# lastmodified 모드 - 수정된 행 Import (타임스탬프 기준)
sqoop import \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --table employees \
    --target-dir /tmp/sqoop_incremental \
    --incremental lastmodified \
    --check-column updated_at \
    --last-value '2024-01-01 00:00:00' \
    --merge-key id
```

### Hive로 직접 Import

```bash
# Hive 테이블로 직접 Import
sqoop import \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --table employees \
    --hive-import \
    --hive-table company.employees \
    --create-hive-table

# Parquet 형식으로 Hive Import (권장)
sqoop import \
    --connect jdbc:mysql://localhost:3306/company_db \
    --username root \
    --password mypassword \
    --table employees \
    --hive-import \
    --hive-table company.employees_parquet \
    --as-parquetfile
```

## 비교 분석

### Sqoop vs 현대적 데이터 전송 도구

Sqoop은 Hadoop 2.6 기반으로 개발되었고 현재 **개발이 사실상 중단**된 상태다. 2024년 기준으로 더 현대적인 대안들이 등장했다:

| 도구 | 유형 | 장점 | 단점 | 적합한 환경 |
|------|------|------|------|------------|
| **Sqoop** | 배치 전송 | Hadoop 네이티브, 검증된 안정성 | 개발 중단, Hadoop 3.x 호환 이슈 | 레거시 Hadoop 클러스터 |
| **Apache NiFi** | 데이터 플로우 | GUI 기반, 실시간 지원 | 설정 복잡도 높음 | 복잡한 데이터 플로우 |
| **Airbyte** | ELT | 300+ 커넥터, 오픈소스 | 상대적으로 신생 프로젝트 | 클라우드 데이터 레이크 |
| **AWS Glue** | 관리형 ETL | 서버리스, AWS 통합 | AWS 종속, 비용 | AWS 환경 |
| **Fivetran** | SaaS | 완전 관리형, 쉬운 설정 | 비용 높음 | 엔지니어 리소스 부족 시 |
| **Spark JDBC** | 프로그래밍 | 유연성, Spark 통합 | 코딩 필요 | 복잡한 변환 로직 필요 시 |

### Spark JDBC로 Sqoop 대체하기

실무에서 Sqoop 대신 PySpark의 JDBC 기능을 활용하는 사례가 늘고 있다:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("JDBC Import") \
    .config("spark.jars", "/path/to/mysql-connector-java.jar") \
    .getOrCreate()

# MySQL에서 데이터 읽기 (Sqoop import 대체)
df = spark.read \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/company_db") \
    .option("dbtable", "employees") \
    .option("user", "root") \
    .option("password", "mypassword") \
    .option("numPartitions", 4) \
    .option("partitionColumn", "id") \
    .option("lowerBound", 1) \
    .option("upperBound", 100000) \
    .load()

# 변환 작업 수행
result = df.filter(df.salary > 50000) \
           .groupBy("department") \
           .agg({"salary": "avg"})

# Parquet로 저장
result.write.parquet("/tmp/output/dept_salary", mode="overwrite")

# MySQL로 Export (Sqoop export 대체)
result.write \
    .format("jdbc") \
    .option("url", "jdbc:mysql://localhost:3306/company_db") \
    .option("dbtable", "dept_salary_summary") \
    .option("user", "root") \
    .option("password", "mypassword") \
    .mode("overwrite") \
    .save()
```

## 실전 팁: Sqoop 사용 시 주의사항

### 1. 비밀번호 보안

```bash
# 나쁜 예: 명령줄에 비밀번호 노출
sqoop import --password mypassword ...

# 좋은 예: 비밀번호 파일 사용
echo -n "mypassword" > ~/.sqoop_pass
chmod 400 ~/.sqoop_pass
sqoop import --password-file file:///home/user/.sqoop_pass ...
```

### 2. Null 값 처리

```bash
# Null을 특정 문자열로 치환
sqoop import \
    --null-string '\\N' \
    --null-non-string '\\N' \
    ...
```

### 3. 구분자 설정

```bash
# 필드/라인 구분자 지정
sqoop import \
    --fields-terminated-by '\t' \
    --lines-terminated-by '\n' \
    ...
```

### 4. Primary Key가 없는 테이블

```bash
# PK가 없으면 Mapper를 1로 지정하거나 split-by 사용
sqoop import \
    --num-mappers 1 \
    ...

# 또는 분할 기준 컬럼 직접 지정
sqoop import \
    --split-by created_date \
    ...
```

## 마무리

Apache Sqoop은 RDBMS와 Hadoop 사이의 **브릿지** 역할을 수행하는 핵심 도구로, 전통적인 데이터 웨어하우스와 빅데이터 플랫폼 간의 데이터 이동을 효율적으로 처리한다. MapReduce 기반의 병렬 전송, 증분 Import, 다양한 저장 포맷 지원 등은 여전히 강력한 기능이다.

다만 Sqoop의 개발이 중단된 현 시점에서, 신규 프로젝트라면 **Spark JDBC**, **Airbyte**, 또는 클라우드 관리형 ETL 서비스 도입을 함께 검토하는 것이 현명하다. 특히 기존 Hadoop 클러스터에 Spark가 이미 구축되어 있다면, PySpark의 JDBC 기능으로 Sqoop의 대부분의 역할을 대체할 수 있다.

레거시 환경이든 최신 클라우드 환경이든, **RDBMS와 분산 스토리지 간 데이터 이동**이라는 문제는 데이터 엔지니어링의 핵심 과제이며, Sqoop이 확립한 패턴을 이해하는 것은 어떤 도구를 사용하든 도움이 될 것이다.

---

**참고 자료:**
- [Apache Sqoop 공식 문서](https://sqoop.apache.org/docs/1.4.7/SqoopUserGuide.html)
- [Sqoop 명령어 정리](https://dlwjdcks5343.tistory.com/116)
- [Apache Sqoop Cookbook (O'Reilly)](https://www.oreilly.com/library/view/apache-sqoop-cookbook/9781449364618/)