<!-- infographic-hero -->
![Apache Spark: From RDD to DataFrame and Beyond 핵심 요약](figures/infographic.svg)

*Figure: Apache Spark: From RDD to DataFrame and Beyond 한 장 요약 인포그래픽*

# Apache Spark 완벽 가이드: RDD부터 DataFrame, MLlib까지

## 개요

Apache Spark는 MapReduce의 **디스크 I/O 병목**을 극복하기 위해 등장한 오픈소스 분산 클러스터 컴퓨팅 프레임워크다. MapReduce가 매 연산 단계마다 디스크에서 데이터를 읽고 쓰는 방식이라면, Spark는 **인메모리(In-Memory) 연산**을 통해 처리 성능을 Hadoop MapReduce 대비 약 100배까지 향상시켰다.

Spark는 단순한 배치 처리 엔진이 아니다. SQL 쿼리(Spark SQL), 실시간 스트리밍(Structured Streaming), 머신러닝(MLlib), 그래프 처리(GraphX)를 **단일 통합 프레임워크**에서 지원한다. 2024년 현재 데이터 엔지니어링 분야에서 가장 널리 사용되는 분산 처리 엔진이며, 대부분의 클라우드 데이터 플랫폼(Databricks, AWS EMR, Google Dataproc)이 Spark를 핵심 엔진으로 채택하고 있다.

## 핵심 개념

### MapReduce에서 Spark로: 왜 전환이 필요했는가?

MapReduce는 분산 파일 시스템(HDFS)에서 데이터를 읽어 Map 단계에서 Key-Value 형태로 변환하고, Reduce 단계에서 집계한 뒤 다시 디스크에 저장하는 구조다. 이 과정에서 **매 단계마다 디스크 I/O가 발생**하므로, 반복적인 연산(머신러닝의 반복 학습 등)에서는 심각한 성능 저하가 나타났다.

Spark는 중간 연산 결과를 **메모리에 유지**함으로써 이 문제를 해결했다. 특히 반복적 알고리즘과 대화형 분석에서 극적인 성능 향상을 보인다.

```
┌────────────────────────────────────────────┐
│           MapReduce 처리 흐름               │
│  Disk → Map → Disk → Shuffle → Disk →     │
│  Reduce → Disk   (매 단계 디스크 I/O)       │
├────────────────────────────────────────────┤
│            Spark 처리 흐름                  │
│  Disk → Memory → Transform → Transform →  │
│  ... → Memory → Disk  (메모리 내 연산)      │
└────────────────────────────────────────────┘
```

### Spark의 핵심 특성

1. **Fault Tolerance(내결함성)**: 노드 장애 시 데이터를 자동으로 복구
2. **Data Parallelism(데이터 병렬성)**: 데이터를 파티션으로 분할하여 병렬 처리
3. **Lazy Evaluation(지연 평가)**: 액션이 호출될 때까지 변환(transformation)을 실행하지 않아 최적화 가능
4. **In-Memory Computing**: 중간 결과를 메모리에 캐시하여 반복 연산 성능 극대화

## 아키텍처

### Spark 클러스터 구성

Spark 클러스터는 **Cluster Manager**와 **Distributed Storage System** 두 가지 핵심 인프라가 필요하다.

```
┌─────────────────────────────────────────────┐
│              Driver Program                  │
│              (SparkContext)                   │
├──────────────┬──────────────────────────────┤
│              │                              │
│    Cluster Manager                          │
│    ┌─────────────────────────┐              │
│    │ Standalone│YARN│K8s│Mesos│              │
│    └─────────────────────────┘              │
│              │                              │
│  ┌───────┐ ┌───────┐ ┌───────┐             │
│  │Worker │ │Worker │ │Worker │             │
│  │Node 1 │ │Node 2 │ │Node 3 │             │
│  │┌─────┐│ │┌─────┐│ │┌─────┐│             │
│  ││Exec ││ ││Exec ││ ││Exec ││             │
│  ││Task1││ ││Task2││ ││Task3││             │
│  │└─────┘│ │└─────┘│ │└─────┘│             │
│  └───────┘ └───────┘ └───────┘             │
└─────────────────────────────────────────────┘
```

**Cluster Manager 종류:**

| Cluster Manager | 설명 | 특징 |
|----------------|------|------|
| **Standalone** | Spark 내장 리소스 매니저 | 설정이 간단, 소규모 클러스터에 적합 |
| **YARN** | Hadoop에 포함된 리소스 매니저 | Hadoop 에코시스템과 통합 시 유리 |
| **Kubernetes** | 컨테이너 기반 오케스트레이션 | 클라우드 네이티브 환경의 표준 |
| **Mesos** | Apache Mesos 기반 | 현재 지원 중단, 사용 비추천 |

**Distributed Storage System:**
- HDFS (가장 전통적, Spark와 동일 머신에서 구동 가능)
- Amazon S3, Google Cloud Storage, Azure Blob Storage
- Cassandra, Delta Lake, Apache Iceberg

### 동작 과정 상세

1. **Driver Program**이 SparkContext를 생성
2. SparkContext가 Cluster Manager에 리소스를 요청
3. Cluster Manager가 Worker Node에 **Executor**를 할당
4. Driver가 작업을 **Task** 단위로 분할하여 Executor에 전달
5. Executor가 Task를 병렬로 실행하고 결과를 반환

## 실전 예제: Spark 데이터 구조 3가지

### 1. RDD (Resilient Distributed Dataset)

RDD는 Spark의 **가장 기본적인 데이터 추상화**다. 변경 불가능(immutable)한 분산 객체 컬렉션이며, 파티션 단위로 분산되어 저장된다.

```python
from pyspark import SparkContext

sc = SparkContext("local", "RDD Example")

# RDD 생성 - parallelize()
data = [("Alice", 34), ("Bob", 45), ("Charlie", 29), ("Alice", 34)]
rdd = sc.parallelize(data)

# 기본 연산
print(f"전체 개수: {rdd.count()}")           # 4
print(f"첫 번째 요소: {rdd.first()}")         # ('Alice', 34)
print(f"상위 2개: {rdd.top(2)}")              # [('Charlie', 29), ('Bob', 45)]

# countByValue - 각 요소의 출현 횟수
print(rdd.countByValue())  # {('Alice', 34): 2, ('Bob', 45): 1, ('Charlie', 29): 1}

# map vs flatMap
nums = sc.parallelize([[1, 2], [3, 4], [5, 6]])
print(nums.map(lambda x: x).collect())      # [[1,2], [3,4], [5,6]]
print(nums.flatMap(lambda x: x).collect())   # [1, 2, 3, 4, 5, 6]

# reduceByKey - Key별 집계
pairs = sc.parallelize([("A", 10), ("B", 20), ("A", 30), ("B", 5)])
result = pairs.reduceByKey(lambda a, b: a + b)
print(result.collect())  # [('A', 40), ('B', 25)]
```

**RDD의 한계:**
- 스키마가 없어 구조화된 데이터 처리가 불편
- Catalyst Optimizer의 최적화를 받을 수 없음
- 현재는 대부분 DataFrame/Dataset API 사용을 권장

### 2. DataFrame (가장 많이 사용)

DataFrame은 RDD 위에 **스키마(행과 열 구조)**를 추가한 것이다. Pandas의 DataFrame과 유사한 개념이지만, 분산 환경에서 동작한다.

```python
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

spark = SparkSession.builder.appName("DataFrame Example").getOrCreate()

# 방법 1: 리스트에서 직접 생성
columns = ["name", "age", "city"]
data = [
    ("Alice", 34, "Seoul"),
    ("Bob", 45, "Busan"),
    ("Charlie", 29, "Daegu")
]
df = spark.createDataFrame(data).toDF(*columns)
df.show()
# +-------+---+------+
# |   name|age|  city|
# +-------+---+------+
# |  Alice| 34| Seoul|
# |    Bob| 45| Busan|
# |Charlie| 29| Daegu|
# +-------+---+------+

# 방법 2: 명시적 스키마 정의
schema = StructType([
    StructField("name", StringType(), True),
    StructField("age", IntegerType(), True),
    StructField("city", StringType(), True)
])
df2 = spark.createDataFrame(data, schema=schema)
df2.printSchema()
# root
#  |-- name: string (nullable = true)
#  |-- age: integer (nullable = true)
#  |-- city: string (nullable = true)

# 방법 3: CSV/JSON/Parquet 파일에서 읽기
df_csv = spark.read.csv("/tmp/data/users.csv", header=True, inferSchema=True)
df_json = spark.read.json("/tmp/data/users.json")
df_parquet = spark.read.parquet("/tmp/data/users.parquet")
```

**DataFrame의 주요 연산:**

```python
# 필터링
df.filter(df.age >= 30).show()

# 그룹화 및 집계
df.groupBy("city").count().show()
df.groupBy("city").agg({"age": "avg"}).show()

# 정렬
df.orderBy(df.age.desc()).show()

# 컬럼 추가/변환
from pyspark.sql.functions import col, when
df.withColumn("age_group",
    when(col("age") < 30, "young")
    .when(col("age") < 40, "middle")
    .otherwise("senior")
).show()

# Spark SQL 연동
df.createOrReplaceTempView("users")
spark.sql("SELECT city, AVG(age) as avg_age FROM users GROUP BY city").show()

# Pandas 변환
pandas_df = df.toPandas()
print(type(pandas_df))  # <class 'pandas.core.frame.DataFrame'>
```

### 3. Dataset (Scala/Java 전용)

Dataset은 DataFrame에서 확장된 형태로, **Typed API**를 제공하여 컴파일 타임에 타입 안전성을 보장한다.

```scala
// Scala 예시
case class User(name: String, age: Int, city: String)

val ds: Dataset[User] = spark.read
  .json("/tmp/users.json")
  .as[User]  // Typed 변환

// 컴파일 타임에 타입 체크
ds.filter(_.age > 30)  // User 클래스의 필드에 직접 접근
```

**중요**: Dataset은 JVM 객체를 통해 동작하므로 **PySpark에서는 지원하지 않는다**. PySpark에서는 DataFrame(= Dataset[Row])만 사용 가능하다.

### RDD vs DataFrame vs Dataset 비교

| 특성 | RDD | DataFrame | Dataset |
|------|-----|-----------|----------|
| 스키마 | 없음 | 있음 | 있음 |
| API 유형 | Low-level | High-level | High-level + Typed |
| 최적화 | 수동 | Catalyst Optimizer | Catalyst Optimizer |
| 타입 안전성 | 런타임 | 런타임 | 컴파일 타임 |
| PySpark 지원 | O | O | X |
| 성능 | 상대적 낮음 | 높음 | 높음 |
| 사용 빈도 (2024) | 낮음 | **가장 높음** | Scala 프로젝트에서 |

## 비교 분석

### Spark(Scala) vs PySpark

| 측면 | Spark (Scala) | PySpark |
|------|-------------|----------|
| 성능 | JVM 네이티브로 약간 우수 | Python-JVM 브릿지 오버헤드 |
| Dataset API | 완전 지원 (Typed API) | 미지원 |
| 라이브러리 생태계 | Scala 생태계 | NumPy, Pandas, scikit-learn 등 풍부 |
| 학습 곡선 | Scala 학습 필요 | Python 개발자에게 친숙 |
| 커뮤니티 | 상대적 작음 | 매우 큼 (데이터 사이언스 커뮤니티) |
| 추천 | 고성능 데이터 파이프라인 | 분석/ML/프로토타이핑 |

### Spark Standalone vs YARN vs Kubernetes

실무에서 Cluster Manager 선택은 인프라 환경에 따라 달라진다:

```
┌──────────────────────────────────────────────┐
│         Cluster Manager 선택 가이드           │
├──────────────────────────────────────────────┤
│ On-Premise + Hadoop 클러스터  →  YARN        │
│ 클라우드 네이티브 환경        →  Kubernetes   │
│ 소규모 개발/테스트           →  Standalone    │
│ Databricks 사용              →  관리형 제공   │
└──────────────────────────────────────────────┘
```

## 실전 팁: PySpark 성능 최적화

```python
# 1. 파티션 수 조절 - 데이터 규모에 맞게
df = df.repartition(200)  # 파티션 수를 200으로 조절

# 2. 캐싱 - 반복 사용되는 DataFrame은 캐시
df.cache()  # 또는 df.persist(StorageLevel.MEMORY_AND_DISK)

# 3. Broadcast Join - 작은 테이블 조인 시
from pyspark.sql.functions import broadcast
result = large_df.join(broadcast(small_df), "key")

# 4. Parquet 포맷 사용 - 컬럼 기반 압축 스토리지
df.write.parquet("/output/path", mode="overwrite")

# 5. 필요한 컬럼만 선택 - Projection Pushdown
df.select("name", "age").filter(df.age > 30)  # 전체 컬럼 로드 방지
```

## 마무리

Apache Spark는 MapReduce의 한계를 인메모리 연산으로 극복한 혁신적 분산 처리 프레임워크다. RDD, DataFrame, Dataset이라는 세 가지 데이터 추상화를 제공하며, 2024년 현재 **DataFrame API가 실무의 표준**이다.

특히 PySpark의 등장으로 Python 개발자들도 분산 처리의 강력한 성능을 쉽게 활용할 수 있게 되었다. Databricks, AWS EMR, Google Dataproc 등 클라우드 관리형 서비스의 확산으로, 인프라 구축 부담 없이 Spark를 활용하는 것이 점점 쉬워지고 있다.

다음 단계로는 Spark SQL의 고급 쿼리 최적화, Structured Streaming을 활용한 실시간 데이터 처리, 그리고 MLlib을 이용한 분산 머신러닝 파이프라인 구축을 학습하는 것을 추천한다.

---

**참고 자료:**
- [Apache Spark 공식 문서](https://spark.apache.org/docs/latest/)
- [Learning Spark, 2nd Edition (O'Reilly)](https://www.oreilly.com/library/view/learning-spark-2nd/9781492050032/)
- [Databricks 학습 가이드](https://www.databricks.com/learn)