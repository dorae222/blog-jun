---
title: "Apache Spark - In-Memory 분산 처리 프레임워크"
slug: "apache-spark---in-memory-분산-처리-프레임워크"
category: "data-engineering"
tags: ["bigdata", "dataframe", "in-memory", "mapreduce", "mllib", "pyspark", "rdd", "spark"]
status: published
post_type: tutorial
quality_score: 8.5
created_at: "2026-03-02T01:08:46.857051+00:00"
---

# Apache Spark - In-Memory 분산 처리 프레임워크

## Spark 개요

Apache Spark는 MapReduce 형태의 클러스터 컴퓨팅 패러다임의 한계를 극복하고자 등장한 오픈소스 분산 클러스터 컴퓨팅 프레임워크다.

**MapReduce의 한계:**
- Disk로부터 데이터를 읽은 후 Map → Reduce 후 다시 Disk에 저장하는 방식
- 파일 기반의 Disk I/O는 성능이 좋지 못했음

**Spark의 특징:**
- In-memory 연산을 통해 처리 성능을 향상 → 디스크 기반의 Hadoop에 비해 약 100배 성능 향상
- Fault Tolerance(내결함성) & Data Parallelism(데이터 병렬성)을 가진 클러스터 프로그래밍
- RDD, DataFrame, Dataset의 3가지 API 제공
- 범용적 분산 처리: 배치, 스트리밍, 머신러닝, SQL 모두 지원

### Spark 아키텍처

**Cluster Manager:**
- **Standalone**: Spark에 포함된 기본 리소스 매니저
- **YARN** (Hadoop): Hadoop에 포함된 리소스 매니저
- **Kubernetes**: 가상화된 분산 컨테이너로 동작하는 매니저

**Distributed Storage System:**
- HDFS, Amazon S3, Cassandra 등
- 가장 많이 사용되는 Storage System은 Hadoop HDFS

---

## Spark Standalone Cluster 설치

```bash
# Master 데몬 실행 (네임노드만)
cd ~/bigdata/spark/sbin && ./start-master.sh --host 192.168.56.101

# Workers 데몬 실행 (데이터 노드 1, 2, 3)
cd ~/bigdata/spark/sbin && ./start-slave.sh spark://192.168.56.101:7077

# PySpark 쉘 실행
cd ~/bigdata/spark/bin && ./pyspark --master spark://192.168.56.101:7077
```

Workers 연결 확인: `http://192.168.56.101:8080/` 에서 브라우저로 확인

---

## 데이터 처리 방법

### Spark 데이터 구조 비교

| 구조 | 특징 | 사용 시점 |
|------|------|-----------|
| RDD | 스키마 없음, 낮은 수준 API | 비정형 데이터, 세밀한 제어 필요 시 |
| DataFrame | 스키마 있음, 행/열 구조 | 구조화 데이터 분석 (가장 일반적) |
| Dataset | DataFrame 확장, typed API | Scala에서 컴파일 타임 오류 검출 필요 시 |

### PySpark RDD

```python
from pyspark import SparkContext

sc = SparkContext("local", "RDD Example")

# RDD 생성 (리스트에서)
rdd = sc.parallelize([1, 2, 2, 3, 3, 4, 5])

# 기본 액션
print(rdd.count())           # 요소 개수: 7
print(rdd.countByValue())    # 값별 개수
print(rdd.first())           # 첫 번째 요소: 1
print(rdd.top(3))            # 상위 3개: [5, 4, 3]

# map vs flatmap
rdd2 = sc.parallelize(["hello world", "foo bar"])
mapped = rdd2.map(lambda x: x.split())       # [['hello', 'world'], ['foo', 'bar']]
flatmapped = rdd2.flatMap(lambda x: x.split()) # ['hello', 'world', 'foo', 'bar']

# reduceByKey: Key 기준으로 Value 합산
pairs = sc.parallelize([("a", 1), ("b", 1), ("a", 1)])
result = pairs.reduceByKey(lambda a, b: a + b)
# [("a", 2), ("b", 1)]
```

### PySpark DataFrame / SQL

```python
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

spark = SparkSession.builder.appName("DataFrame Example").getOrCreate()

# 리스트 + 컬럼명으로 생성
columns = ["name", "age", "dept"]
data = [("Alice", 30, "Engineering"), ("Bob", 25, "Marketing")]
df = spark.createDataFrame(data).toDF(*columns)

# 스키마 확인 및 데이터 출력
df.printSchema()
df.show(truncate=False)

# CSV 파일 읽기
df_csv = spark.read.option("header", True).csv("/tmp/data/stocks.csv")

# SQL 사용
df.createOrReplaceTempView("employees")
result = spark.sql("SELECT dept, COUNT(*) as cnt FROM employees GROUP BY dept")
result.show()

# DataFrame to Pandas
pandas_df = df.toPandas()
```

---

## 머신러닝 (MLlib)

```python
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.feature import VectorAssembler

# 피처 벡터 조합
assembler = VectorAssembler(inputCols=["age", "salary"], outputCol="features")
df_assembled = assembler.transform(df)

# 모델 학습
lr = LogisticRegression(featuresCol="features", labelCol="label")
model = lr.fit(df_assembled)
```

---

## Spark 동작 과정

```
Driver Program (SparkContext 생성)
    ↓
Cluster Manager (리소스 요청 및 할당)
    ↓
Worker Node 1, 2, 3 ... (Executor 실행)
    ↓
HDFS / Storage System (데이터 읽기/쓰기)
```

- **Driver**: SparkContext를 생성하고 전체 애플리케이션을 조율
- **Executor**: Worker Node에서 실행되며 Task를 처리하고 데이터를 캐싱
- **Task**: 실제 연산의 최소 단위, 각 파티션에 하나씩 할당
