---
title: "Apache Sqoop - RDBMS와 Hadoop 데이터 전송 도구"
slug: "apache-sqoop---rdbms와-hadoop-데이터-전송-도구"
category: "data-engineering"
tags: ["bigdata", "data-pipeline", "etl", "hadoop", "hdfs", "jdbc", "mysql", "sqoop"]
status: published
post_type: tutorial
quality_score: 7.5
created_at: "2026-03-02T01:08:46.863161+00:00"
---

# Apache Sqoop - RDBMS와 Hadoop 데이터 전송 도구

## Sqoop이란?

Apache Sqoop은 관계형 데이터베이스(RDBMS)와 Hadoop 생태계(HDFS, Hive, HBase) 사이에서 대용량 데이터를 효율적으로 주고받기 위한 커맨드라인 도구다. JDBC를 사용하여 다양한 RDBMS(MySQL, Oracle, PostgreSQL, SQL Server 등)와 연동할 수 있다.

**핵심 워크플로:**
- **Import**: RDBMS 테이블 → HDFS (또는 Hive/HBase)
- **Export**: HDFS → RDBMS 테이블

> 주의: Sqoop은 Hadoop 2.6 버전 기준으로 개발되었으며, 현재 개발이 중단된 상태다. 최신 환경에서는 Apache NiFi, Apache Kafka, Spark JDBC 등의 대안을 고려할 수 있다.

---

## MySQL 설치 및 설정

### MySQL 접속 및 기본 명령

```sql
-- MySQL 접속
mysql -u root -p

-- 데이터베이스 목록 확인
show databases;

-- 데이터베이스 선택
use test;
```

### 테이블 생성 및 데이터 입력

```sql
-- 테이블 생성
CREATE TABLE salaries (
    gender  VARCHAR(1),
    age     INT,
    salary  DOUBLE,
    zipcode INT
);

-- 기본키(PK) 컬럼 추가
ALTER TABLE salaries
    ADD COLUMN id INT(10) UNSIGNED PRIMARY KEY AUTO_INCREMENT;

-- 데이터 입력
INSERT INTO salaries (gender, age, salary, zipcode)
VALUES ('M', 30, 44000, 51531);
```

### Sqoop용 MySQL 계정 및 권한 설정

```sql
-- 외부 접속용 계정 생성
CREATE USER 'root'@'%' IDENTIFIED BY 'bigdata';

-- 모든 권한 부여
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

-- 권한 반영
FLUSH PRIVILEGES;
```

---

## Sqoop Import (DB → Hadoop)

### 단일 테이블 Import

```bash
sqoop import \
  --connect jdbc:mysql://localhost/test \
  --table salaries \
  --username root \
  --password hortonworks1 \
  --target-dir /tmp/sqoop_out
```

Import 후 HDFS에서 확인:

```bash
hadoop fs -ls /tmp/sqoop_out/
hadoop fs -cat /tmp/sqoop_out/*
```

### 복수 테이블 Import

```bash
sqoop import-all-tables \
  --connect jdbc:mysql://localhost/test \
  --username root \
  --password hortonworks1 \
  --exclude-tables test3 \
  --warehouse-dir /tmp/sqoop_out_3
```

> 단일 테이블 import 시에는 `--target-dir`, 복수 테이블 import 시에는 `--warehouse-dir`을 사용한다.

---

## Sqoop Export (Hadoop → DB)

```sql
-- MySQL에서 대상 테이블 생성
CREATE TABLE salaries_export (
    gender  VARCHAR(1),
    age     INT,
    salary  DOUBLE,
    zipcode INT
);
```

```bash
sqoop export \
  --connect jdbc:mysql://localhost/test \
  --table salaries_export \
  --username root \
  --password hortonworks1 \
  --export-dir /tmp/sqoop_out
```

---

## Sqoop Query

```bash
# SELECT 쿼리 실행
sqoop eval \
  --connect jdbc:mysql://localhost/test \
  --username root \
  --password hortonworks1 \
  --query 'SELECT * FROM salaries WHERE gender="M"'

# DB 목록 확인
sqoop list-databases \
  --connect jdbc:mysql://localhost/test \
  --username root \
  --password hortonworks1
```

---

## 증분 로드(Incremental Load)

```bash
sqoop import \
  --connect jdbc:mysql://localhost/test \
  --table salaries \
  --username root \
  --password hortonworks1 \
  --target-dir /tmp/sqoop_incremental \
  --incremental append \
  --check-column id \
  --last-value 100
```

Sqoop은 주로 운영 DB 데이터를 HDFS로 정기적으로 가져와 Hive/Spark로 분석하는 데이터 레이크 구축에 활용된다.
