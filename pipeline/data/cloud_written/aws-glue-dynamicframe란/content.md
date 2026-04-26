<!-- infographic-hero -->
![AWS Glue DynamicFrame란? 핵심 요약](figures/infographic.svg)

*Figure: AWS Glue DynamicFrame란? 한 장 요약 인포그래픽*

# AWS Glue DynamicFrame란?

## 개요

AWS Glue DynamicFrame은 AWS Glue ETL에서 제공하는 핵심 데이터 추상화로, Apache Spark의 DataFrame을 확장한 개념입니다. 가장 큰 특징은 셀프 디스크라이빙(self-describing) 레코드를 지원한다는 점입니다. 즉, 각 레코드가 자체적으로 스키마 정보를 가지고 있어 동일한 컬럼에 서로 다른 데이터 타입이 혼재하는 상황을 유연하게 처리할 수 있습니다.

Spark DataFrame은 모든 행이 동일한 스키마를 따라야 합니다. 하지만 실제 데이터, 특히 JSON이나 NoSQL 데이터베이스에서 가져온 데이터는 동일한 필드라도 레코드마다 다른 타입을 가질 수 있습니다. 예를 들어 `age` 필드가 어떤 레코드에서는 정수(25), 다른 레코드에서는 문자열("twenty-five")로 저장되어 있을 수 있습니다. DataFrame은 이런 상황에서 스키마 추론 실패나 데이터 손실이 발생할 수 있지만, DynamicFrame은 ChoiceType이라는 특수한 타입을 통해 이러한 불일치를 안전하게 보존합니다.

DynamicFrame은 Glue ETL의 기본 데이터 구조이며, DynamicRecord의 분산 컬렉션입니다. 각 DynamicRecord는 자체 스키마(DynamicSchema)를 가지며, 이를 통해 스키마가 불규칙한 데이터도 손실 없이 처리할 수 있습니다.

## 핵심 기능

### 1. ChoiceType과 스키마 유연성

DynamicFrame의 가장 핵심적인 기능은 ChoiceType입니다. 하나의 컬럼에 여러 데이터 타입이 혼재할 때, DynamicFrame은 이를 ChoiceType으로 표현합니다.

```python
from awsglue.context import GlueContext
from pyspark.context import SparkContext

sc = SparkContext()
glueContext = GlueContext(sc)

# Data Catalog에서 DynamicFrame 생성
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="raw_db",
    table_name="mixed_type_data"
)

# 스키마 확인 - ChoiceType이 있을 수 있음
dyf.printSchema()
# root
# |-- user_id: string
# |-- age: choice
# |    |-- int
# |    |-- string
# |-- metadata: struct
# |    |-- source: string
# |    |-- version: choice
# |    |    |-- int
# |    |    |-- double
```

### 2. DynamicFrame 생성 방법

DynamicFrame을 생성하는 주요 방법은 다음과 같습니다.

```python
# 1. Data Catalog에서 생성
dyf_catalog = glueContext.create_dynamic_frame.from_catalog(
    database="analytics_db",
    table_name="user_events",
    transformation_ctx="source_catalog",
    push_down_predicate="year='2024' AND month='01'"
)

# 2. S3에서 직접 생성
dyf_s3 = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={
        "paths": ["s3://my-data-lake/raw/events/"],
        "recurse": True
    },
    format="json",
    transformation_ctx="source_s3"
)

# 3. JDBC 소스에서 생성
dyf_jdbc = glueContext.create_dynamic_frame.from_options(
    connection_type="mysql",
    connection_options={
        "url": "jdbc:mysql://mydb.example.com:3306/analytics",
        "dbtable": "user_events",
        "user": "admin",
        "password": "password"
    },
    transformation_ctx="source_jdbc"
)

# 4. Spark DataFrame에서 변환
from awsglue.dynamicframe import DynamicFrame
spark_df = spark.read.parquet("s3://my-data-lake/data/")
dyf_from_df = DynamicFrame.fromDF(spark_df, glueContext, "from_df")
```

```bash
# AWS CLI로 Glue Job 실행 시 DynamicFrame 관련 파라미터 전달
aws glue start-job-run \
  --job-name "etl-with-dynamicframe" \
  --arguments '{
    "--source_database": "raw_db",
    "--source_table": "mixed_data",
    "--target_path": "s3://my-data-lake/processed/"
  }'
```

### 3. 핵심 변환(Transformation) API

DynamicFrame은 Glue ETL의 다양한 변환 API를 지원합니다.

**ApplyMapping - 컬럼 매핑 및 타입 변환:**

```python
from awsglue.transforms import ApplyMapping

mapped_dyf = ApplyMapping.apply(
    frame=dyf,
    mappings=[
        ("user_id", "string", "user_id", "string"),
        ("event_type", "string", "event_type", "string"),
        ("event_timestamp", "string", "event_ts", "timestamp"),
        ("price", "double", "price", "decimal(10,2)"),
        ("metadata.source", "string", "source", "string")
    ],
    transformation_ctx="apply_mapping"
)
```

**Filter - 조건부 필터링:**

```python
from awsglue.transforms import Filter

filtered_dyf = Filter.apply(
    frame=dyf,
    f=lambda x: x["event_type"] == "purchase" and x["price"] is not None and x["price"] > 0,
    transformation_ctx="filter_purchases"
)
```

**DropNullFields - null 필드 제거:**

```python
from awsglue.transforms import DropNullFields

cleaned_dyf = DropNullFields.apply(
    frame=dyf,
    transformation_ctx="drop_nulls"
)
```

**Relationalize - 중첩 구조 평탄화:**

```python
from awsglue.transforms import Relationalize

# 중첩 JSON을 관계형 테이블로 평탄화
relationalized = Relationalize.apply(
    frame=dyf,
    staging_path="s3://my-data-lake/temp/relationalize/",
    name="root",
    transformation_ctx="relationalize"
)

# 결과는 DynamicFrameCollection (여러 테이블)
for key in relationalized.keys():
    print(f"테이블: {key}")
    frame = relationalized.select(key)
    frame.printSchema()
    print(f"레코드 수: {frame.count()}")
```

**SelectFields / DropFields - 컬럼 선택/제거:**

```python
from awsglue.transforms import SelectFields, DropFields

# 필요한 컬럼만 선택
selected_dyf = SelectFields.apply(
    frame=dyf,
    paths=["user_id", "event_type", "event_timestamp", "price"],
    transformation_ctx="select_fields"
)

# 불필요한 컬럼 제거
dropped_dyf = DropFields.apply(
    frame=dyf,
    paths=["temp_field", "debug_info"],
    transformation_ctx="drop_fields"
)
```

### 4. DataFrame과의 상호 변환

DynamicFrame과 Spark DataFrame은 자유롭게 상호 변환할 수 있습니다. DynamicFrame의 변환 API로 처리하기 어려운 복잡한 연산은 DataFrame으로 변환하여 수행합니다.

```python
# DynamicFrame -> DataFrame
spark_df = dyf.toDF()

# DataFrame에서 복잡한 연산 수행
from pyspark.sql.functions import col, when, regexp_replace, to_timestamp

transformed_df = spark_df \
    .withColumn("clean_price", when(col("price").isNull(), 0.0).otherwise(col("price"))) \
    .withColumn("event_date", to_timestamp(col("event_timestamp"), "yyyy-MM-dd'T'HH:mm:ss")) \
    .filter(col("event_type").isNotNull()) \
    .groupBy("user_id", "event_type") \
    .agg({"clean_price": "sum", "*": "count"})

# DataFrame -> DynamicFrame
result_dyf = DynamicFrame.fromDF(transformed_df, glueContext, "result")
```

### 5. 쓰기(Write) 연산

```python
# S3에 Parquet 형식으로 쓰기
glueContext.write_dynamic_frame.from_options(
    frame=result_dyf,
    connection_type="s3",
    connection_options={
        "path": "s3://my-data-lake/processed/events/",
        "partitionKeys": ["year", "month"]
    },
    format="parquet",
    format_options={"compression": "snappy"},
    transformation_ctx="write_s3"
)

# Data Catalog 테이블에 쓰기
glueContext.write_dynamic_frame.from_catalog(
    frame=result_dyf,
    database="curated_db",
    table_name="events_curated",
    transformation_ctx="write_catalog"
)
```

## 아키텍처/동작 원리

### DynamicFrame의 내부 구조

```
[DynamicFrame]
    |
    +-- DynamicRecord 1: {user_id: "U001", age: int(25), score: 85.5}
    +-- DynamicRecord 2: {user_id: "U002", age: string("N/A"), score: 92.0}
    +-- DynamicRecord 3: {user_id: "U003", age: int(30), score: null}
    |
    +-- Schema (추론): 
         user_id: string
         age: choice{int, string}    <-- ChoiceType
         score: double
```

### DataFrame과의 핵심 차이점

```
[Spark DataFrame]                    [Glue DynamicFrame]
- 고정 스키마 (StructType)           - 유동 스키마 (DynamicSchema)
- 모든 행 동일 타입                  - 행마다 다른 타입 허용 (ChoiceType)
- 스키마 위반 시 null/에러           - 스키마 불일치를 보존
- Spark SQL 네이티브               - Glue ETL 네이티브
- Catalyst 최적화 적용              - Glue 변환 최적화 적용
- RDD[Row] 기반                    - RDD[DynamicRecord] 기반
```

### 변환 실행 흐름

DynamicFrame의 변환은 Spark의 지연 평가(Lazy Evaluation) 모델을 따릅니다. 변환을 정의하는 시점에는 실제 계산이 이루어지지 않고, 액션(write, count, show 등)이 호출될 때 전체 변환 파이프라인이 실행됩니다.

```
[소스 읽기]                      (Lazy)
    |
[ApplyMapping]                   (Lazy)
    |
[ResolveChoice]                  (Lazy)
    |
[Filter]                         (Lazy)
    |
[Write to S3]                    (Action!) --> 전체 파이프라인 실행
```

### transformation_ctx의 역할

각 변환에 지정하는 `transformation_ctx`는 Job Bookmark에서 사용됩니다. Job Bookmark는 이전에 처리한 데이터를 추적하여 중복 처리를 방지하는 기능인데, `transformation_ctx`를 통해 각 변환 단계를 식별합니다.

## 실전 활용

### 사례 1: 혼합 타입 데이터 정리 파이프라인

JSON 데이터에서 동일 필드에 여러 타입이 혼재하는 경우를 처리하는 전체 파이프라인입니다.

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 1. 소스 데이터 로드
source_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="raw_db",
    table_name="user_profiles",
    transformation_ctx="source"
)

print(f"원본 레코드 수: {source_dyf.count()}")
print("원본 스키마:")
source_dyf.printSchema()

# 2. ChoiceType 해결 (ResolveChoice)
resolved_dyf = ResolveChoice.apply(
    frame=source_dyf,
    choice="match_catalog",
    database="raw_db",
    table_name="user_profiles",
    transformation_ctx="resolve_choice"
)

# 3. 컬럼 매핑 및 타입 변환
mapped_dyf = ApplyMapping.apply(
    frame=resolved_dyf,
    mappings=[
        ("user_id", "string", "user_id", "string"),
        ("name", "string", "name", "string"),
        ("age", "int", "age", "int"),
        ("email", "string", "email", "string"),
        ("created_at", "string", "created_at", "timestamp"),
        ("preferences.language", "string", "language", "string"),
        ("preferences.timezone", "string", "timezone", "string")
    ],
    transformation_ctx="mapping"
)

# 4. null 필드 정리
cleaned_dyf = DropNullFields.apply(
    frame=mapped_dyf,
    transformation_ctx="clean_nulls"
)

# 5. 필터링 (유효한 이메일만)
valid_dyf = Filter.apply(
    frame=cleaned_dyf,
    f=lambda x: x["email"] is not None and "@" in str(x.get("email", "")),
    transformation_ctx="filter_valid"
)

# 6. 결과 저장
glueContext.write_dynamic_frame.from_options(
    frame=valid_dyf,
    connection_type="s3",
    connection_options={
        "path": "s3://my-data-lake/curated/user_profiles/"
    },
    format="parquet",
    format_options={"compression": "snappy"},
    transformation_ctx="write_output"
)

print(f"처리된 레코드 수: {valid_dyf.count()}")
job.commit()
```

```bash
# 위 잡 생성 및 실행
aws glue create-job \
  --name "user-profiles-etl" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --command '{"Name": "glueetl", "ScriptLocation": "s3://my-scripts/user_profiles_etl.py", "PythonVersion": "3"}' \
  --default-arguments '{
    "--job-bookmark-option": "job-bookmark-enable",
    "--TempDir": "s3://my-data-lake/temp/",
    "--enable-metrics": "true",
    "--enable-continuous-cloudwatch-log": "true"
  }' \
  --glue-version "4.0" \
  --number-of-workers 10 \
  --worker-type "G.1X"

aws glue start-job-run --job-name "user-profiles-etl"
```

### 사례 2: 중첩 JSON 평탄화 (Relationalize)

복잡한 중첩 JSON 데이터를 관계형 테이블로 변환하는 패턴입니다.

```python
# 중첩 JSON 예시:
# {
#   "order_id": "ORD001",
#   "customer": {"id": "C001", "name": "김철수"},
#   "items": [
#     {"product_id": "P001", "quantity": 2, "price": 15000},
#     {"product_id": "P002", "quantity": 1, "price": 30000}
#   ]
# }

# DynamicFrame 로드
orders_dyf = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={"paths": ["s3://my-data-lake/raw/orders/"]},
    format="json",
    transformation_ctx="orders_source"
)

# Relationalize로 평탄화
relationalized = Relationalize.apply(
    frame=orders_dyf,
    staging_path="s3://my-data-lake/temp/relationalize/",
    name="orders",
    transformation_ctx="relationalize_orders"
)

# 결과: orders (메인 테이블), orders_items (배열 테이블)
for key in relationalized.keys():
    frame = relationalized.select(key)
    print(f"\n=== {key} ===")
    frame.printSchema()
    frame.toDF().show(5, truncate=False)
    
    # 각 테이블을 별도로 저장
    glueContext.write_dynamic_frame.from_options(
        frame=frame,
        connection_type="s3",
        connection_options={"path": f"s3://my-data-lake/curated/{key}/"},
        format="parquet",
        transformation_ctx=f"write_{key}"
    )
```

### 사례 3: DynamicFrame과 DataFrame 혼합 사용

```python
# DynamicFrame으로 소스 로드 (ChoiceType 처리 활용)
source_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="raw_db",
    table_name="transactions",
    transformation_ctx="source"
)

# ChoiceType 해결
resolved_dyf = ResolveChoice.apply(
    frame=source_dyf,
    choice="cast:double",
    transformation_ctx="resolve"
)

# DataFrame으로 변환하여 복잡한 집계 수행
df = resolved_dyf.toDF()

from pyspark.sql import functions as F
from pyspark.sql.window import Window

# 윈도우 함수를 활용한 분석
window_spec = Window.partitionBy("customer_id").orderBy("transaction_date")

analysis_df = df \
    .withColumn("running_total", F.sum("amount").over(window_spec)) \
    .withColumn("transaction_rank", F.row_number().over(window_spec)) \
    .withColumn("prev_amount", F.lag("amount", 1).over(window_spec)) \
    .withColumn("amount_change", F.col("amount") - F.coalesce(F.col("prev_amount"), F.lit(0)))

# 다시 DynamicFrame으로 변환하여 Glue 기능 활용 (Bookmark 등)
result_dyf = DynamicFrame.fromDF(analysis_df, glueContext, "analysis_result")

# Glue Data Catalog 테이블로 쓰기
glueContext.write_dynamic_frame.from_catalog(
    frame=result_dyf,
    database="curated_db",
    table_name="transaction_analysis",
    transformation_ctx="write_result"
)
```

## 모범 사례/보안

### 성능 최적화

1. **Push-down Predicate 활용**: Data Catalog에서 읽을 때 파티션 필터를 적용하여 불필요한 데이터 읽기를 최소화합니다.

```python
# 파티션 프루닝으로 읽기 최적화
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="analytics_db",
    table_name="events",
    push_down_predicate="year='2024' AND month='01'",
    transformation_ctx="source"
)
```

2. **적절한 시점에 DataFrame 변환**: DynamicFrame의 변환 API로 충분한 작업은 DynamicFrame에서 처리하고, 복잡한 집계나 조인이 필요한 경우에만 DataFrame으로 변환합니다.

3. **transformation_ctx 일관성**: Job Bookmark가 올바르게 동작하려면 모든 변환에 고유한 `transformation_ctx`를 지정해야 합니다.

4. **Relationalize 스테이징 경로 관리**: Relationalize 변환의 스테이징 경로에 생성되는 임시 파일을 주기적으로 정리합니다.

### DynamicFrame vs DataFrame 선택 기준

| 상황 | 권장 선택 |
|------|----------|
| 스키마 불일치 데이터 | DynamicFrame |
| ChoiceType 처리 필요 | DynamicFrame |
| 중첩 JSON 평탄화 | DynamicFrame (Relationalize) |
| 복잡한 집계/조인 | DataFrame |
| 윈도우 함수 사용 | DataFrame |
| ML 라이브러리 연동 | DataFrame |
| Job Bookmark 활용 | DynamicFrame |
| Data Catalog 직접 읽기/쓰기 | DynamicFrame |

### 보안 고려사항

1. **임시 데이터 정리**: Relationalize 등에서 생성되는 임시 S3 파일에 민감한 데이터가 포함될 수 있으므로, S3 버킷에 수명 주기 정책을 설정합니다.

2. **JDBC 연결 보안**: JDBC를 통해 DynamicFrame을 생성할 때, 비밀번호는 AWS Secrets Manager에서 가져오도록 합니다.

```bash
# Secrets Manager에서 JDBC 비밀번호를 참조하는 Glue Connection 생성
aws glue create-connection \
  --connection-input '{
    "Name": "secure-rds-conn",
    "ConnectionType": "JDBC",
    "ConnectionProperties": {
      "JDBC_CONNECTION_URL": "jdbc:mysql://mydb.example.com:3306/analytics",
      "SECRET_ID": "rds/analytics/credentials"
    },
    "PhysicalConnectionRequirements": {
      "SubnetId": "subnet-abc123",
      "SecurityGroupIdList": ["sg-abc123"]
    }
  }'
```

3. **암호화**: DynamicFrame을 S3에 쓸 때 서버 측 암호화를 활성화합니다.

## 관련 서비스 비교

| 항목 | DynamicFrame | Spark DataFrame | Pandas DataFrame |
|------|-------------|----------------|------------------|
| 실행 환경 | AWS Glue ETL | Spark (범용) | 단일 머신 |
| 스키마 | 유동적 (ChoiceType) | 고정 (StructType) | 유동적 (dtype) |
| 분산 처리 | 지원 (Spark 기반) | 지원 | 미지원 |
| 데이터 규모 | 대규모 (TB+) | 대규모 (TB+) | 소규모 (GB) |
| ETL 특화 변환 | ApplyMapping, Relationalize 등 | 범용 변환 | 범용 변환 |
| Job Bookmark | 네이티브 지원 | 미지원 | 미지원 |
| Data Catalog 통합 | 네이티브 | 가능 (Glue Context 필요) | 미지원 |
| 중첩 구조 처리 | Relationalize | explode/flatMap | json_normalize |
| 학습 곡선 | Glue ETL 전용 | Spark 생태계 | Python 생태계 |

## 요약

AWS Glue DynamicFrame은 ETL 워크로드에 특화된 데이터 추상화로, Spark DataFrame의 한계인 고정 스키마 제약을 ChoiceType을 통해 해결합니다. 각 레코드가 자체 스키마를 가지는 셀프 디스크라이빙 방식으로, 실제 데이터에서 흔히 발생하는 타입 불일치 문제를 안전하게 처리합니다.

ApplyMapping, ResolveChoice, Relationalize, Filter 등 ETL에 특화된 변환 API를 제공하며, Spark DataFrame과의 자유로운 상호 변환으로 양쪽의 장점을 모두 활용할 수 있습니다. Job Bookmark 통합, Data Catalog 직접 읽기/쓰기, push-down predicate를 통한 파티션 프루닝 등 AWS Glue 생태계와의 긴밀한 통합이 핵심 강점입니다.

실전에서는 스키마 불일치 처리와 ETL 변환에는 DynamicFrame을 사용하고, 복잡한 집계, 조인, 윈도우 함수가 필요한 경우에만 DataFrame으로 변환하는 하이브리드 접근 방식을 권장합니다.