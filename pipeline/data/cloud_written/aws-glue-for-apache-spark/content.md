# AWS Glue for Apache Spark

## 개요

AWS Glue for Apache Spark는 완전 관리형 Apache Spark 환경을 제공하는 서버리스 ETL 서비스입니다. 사용자가 Spark 클러스터의 프로비저닝, 설정, 스케일링, 패치 적용 등 인프라 관리를 신경 쓰지 않고 ETL 로직에만 집중할 수 있도록 설계되었습니다.

Glue 4.0 기준으로 Apache Spark 3.3.0을 기반으로 하며, PySpark와 Scala를 모두 지원합니다. EMR과 비교했을 때 Glue의 핵심 차별점은 서버리스 운영 모델, Data Catalog과의 네이티브 통합, DynamicFrame/Job Bookmark 같은 ETL 전용 기능, 그리고 자동 스케일링입니다.

Glue Spark 잡은 DPU(Data Processing Unit) 단위로 컴퓨팅 리소스를 할당합니다. 각 DPU는 4 vCPU와 16GB 메모리를 제공하며, 워커 타입(G.1X, G.2X, G.4X, G.8X, Z.2X)에 따라 DPU 할당량이 달라집니다.

## 핵심 기능

### 1. Glue 버전과 Spark 버전 매핑

Glue 버전에 따라 사용 가능한 Spark 버전과 Python 버전이 달라집니다.

| Glue 버전 | Spark 버전 | Python 버전 | 주요 특징 |
|-----------|-----------|------------|----------|
| 4.0 | 3.3.0 | 3.10 | 최신, Auto Scaling 개선, 성능 최적화 |
| 3.0 | 3.1.1 | 3.7 | Spark 3.x 도입, 성능 개선 |
| 2.0 | 2.4.3 | 3.6/2.7 | Spark 2.x, ML Transform 지원 |

```bash
# Glue 4.0 Spark Job 생성
aws glue create-job \
  --name "spark-etl-job" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --command '{
    "Name": "glueetl",
    "ScriptLocation": "s3://my-scripts/spark_etl.py",
    "PythonVersion": "3"
  }' \
  --glue-version "4.0" \
  --number-of-workers 10 \
  --worker-type "G.1X" \
  --default-arguments '{
    "--job-bookmark-option": "job-bookmark-enable",
    "--TempDir": "s3://my-data-lake/temp/",
    "--enable-metrics": "true",
    "--enable-continuous-cloudwatch-log": "true",
    "--enable-spark-ui": "true",
    "--spark-event-logs-path": "s3://my-data-lake/spark-logs/",
    "--enable-auto-scaling": "true"
  }' \
  --max-retries 1 \
  --timeout 120 \
  --description "Spark 기반 ETL 잡"
```

### 2. 워커 타입과 리소스 할당

각 워커 타입은 서로 다른 리소스 스펙을 가집니다.

| 워커 타입 | DPU | vCPU | 메모리 | 디스크 | 적합한 워크로드 |
|-----------|-----|------|--------|--------|----------------|
| G.1X | 1 | 4 | 16 GB | 64 GB SSD | 일반 ETL |
| G.2X | 2 | 8 | 32 GB | 128 GB SSD | 메모리 집약적 |
| G.4X | 4 | 16 | 64 GB | 256 GB SSD | ML/대규모 조인 |
| G.8X | 8 | 32 | 128 GB | 512 GB SSD | 초대규모 처리 |
| Z.2X | 2 | 8 | 64 GB | 128 GB SSD | 메모리 최적화(Ray) |

```bash
# 메모리 집약적 워크로드를 위한 G.2X 잡
aws glue create-job \
  --name "memory-intensive-job" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --command '{"Name": "glueetl", "ScriptLocation": "s3://my-scripts/heavy_join.py", "PythonVersion": "3"}' \
  --glue-version "4.0" \
  --number-of-workers 20 \
  --worker-type "G.2X" \
  --default-arguments '{
    "--enable-auto-scaling": "true",
    "--conf": "spark.sql.shuffle.partitions=400"
  }'
```

### 3. Auto Scaling

Glue 3.0 이상에서는 Auto Scaling을 지원합니다. 잡 실행 중 Spark 단계의 병렬성과 리소스 사용률에 따라 워커 수를 자동으로 조절합니다.

```bash
# Auto Scaling 활성화된 잡
aws glue create-job \
  --name "auto-scaling-job" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --command '{"Name": "glueetl", "ScriptLocation": "s3://my-scripts/etl.py", "PythonVersion": "3"}' \
  --glue-version "4.0" \
  --number-of-workers 50 \
  --worker-type "G.1X" \
  --default-arguments '{"--enable-auto-scaling": "true"}'
```

`--number-of-workers`는 Auto Scaling 활성화 시 최대 워커 수를 의미합니다. Glue는 실제 워크로드에 따라 최소 2개부터 최대 지정 수까지 동적으로 조절합니다.

### 4. Spark UI와 모니터링

Glue는 Spark UI를 S3에 이벤트 로그 형태로 제공합니다. 이를 통해 잡의 DAG, 스테이지, 태스크 수준의 상세 실행 정보를 확인할 수 있습니다.

```bash
# Spark UI 활성화 및 잡 실행
aws glue start-job-run \
  --job-name "spark-etl-job" \
  --arguments '{
    "--enable-spark-ui": "true",
    "--spark-event-logs-path": "s3://my-data-lake/spark-ui-logs/"
  }'
```

```bash
# 잡 실행 상태 및 메트릭 확인
aws glue get-job-run \
  --job-name "spark-etl-job" \
  --run-id "jr_abc123" \
  --query '{
    JobRunState: JobRunState,
    ExecutionTime: ExecutionTime,
    DPUSeconds: DPUSeconds,
    MaxCapacity: MaxCapacity
  }'
```

```bash
# CloudWatch 메트릭으로 잡 모니터링
aws cloudwatch get-metric-statistics \
  --namespace "Glue" \
  --metric-name "glue.driver.aggregate.bytesRead" \
  --dimensions Name=JobName,Value=spark-etl-job Name=JobRunId,Value=jr_abc123 \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 300 \
  --statistics Average
```

### 5. 추가 라이브러리와 커넥터

Glue Spark 잡에서 외부 Python 라이브러리나 JAR 파일을 사용할 수 있습니다.

```bash
# 추가 라이브러리를 포함한 잡 생성
aws glue create-job \
  --name "job-with-libraries" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --command '{"Name": "glueetl", "ScriptLocation": "s3://my-scripts/etl_with_libs.py", "PythonVersion": "3"}' \
  --glue-version "4.0" \
  --number-of-workers 10 \
  --worker-type "G.1X" \
  --default-arguments '{
    "--additional-python-modules": "pandas==2.0.3,requests==2.31.0,pyarrow==12.0.1",
    "--extra-py-files": "s3://my-scripts/libs/custom_module.zip",
    "--extra-jars": "s3://my-scripts/jars/custom-connector.jar",
    "--TempDir": "s3://my-data-lake/temp/"
  }'
```

### 6. Glue Connector와 Marketplace 커넥터

Glue는 다양한 데이터 소스에 대한 내장 커넥터와 AWS Marketplace를 통한 서드파티 커넥터를 제공합니다.

```bash
# 커스텀 커넥터 생성 (예: MongoDB)
aws glue create-connection \
  --connection-input '{
    "Name": "mongodb-conn",
    "ConnectionType": "MARKETPLACE",
    "ConnectionProperties": {
      "CONNECTOR_TYPE": "Spark",
      "CONNECTOR_URL": "s3://my-scripts/connectors/mongodb-connector.jar",
      "CONNECTOR_CLASS_NAME": "com.mongodb.spark.sql.DefaultSource"
    }
  }'
```

## 아키텍처/동작 원리

### Glue Spark 잡 실행 아키텍처

```
[사용자]
    |
    v
[Glue API / Console]
    |
    v
[Glue Job Orchestrator]
    |
    +-- 워커 프로비저닝 (서버리스)
    |       |
    |   [Spark Driver]  (1 워커)
    |       |
    |   [Spark Executor 1] [Spark Executor 2] ... [Spark Executor N]
    |       |                   |                       |
    |   [Task] [Task]      [Task] [Task]           [Task] [Task]
    |
    +-- Data Catalog 접근
    |       |
    |   [메타데이터 조회: 스키마, 파티션, 위치 정보]
    |
    +-- 데이터 소스/타겟
            |
        [S3]  [JDBC]  [DynamoDB]  [Kinesis]  [Kafka]
```

### Spark Execution Model in Glue

Glue에서 Spark 잡이 실행되는 과정은 다음과 같습니다.

1. **잡 제출**: 사용자가 잡을 시작하면 Glue 서비스가 요청을 받습니다.
2. **리소스 할당**: 지정된 워커 타입과 수에 따라 컴퓨팅 리소스가 프로비저닝됩니다. 콜드 스타트 시간은 보통 1~3분 정도입니다.
3. **Spark 클러스터 초기화**: Driver와 Executor가 시작되고 Spark 세션이 생성됩니다.
4. **스크립트 실행**: 사용자의 PySpark/Scala 스크립트가 Driver에서 실행됩니다.
5. **분산 처리**: Spark의 DAG 스케줄러에 의해 작업이 Task 단위로 분할되어 Executor에서 병렬 실행됩니다.
6. **정리**: 잡 완료 후 리소스가 자동으로 해제됩니다.

### Spark 설정 커스터마이징

Glue에서도 Spark 설정을 커스터마이징할 수 있습니다.

```python
# GlueContext를 통한 Spark 설정
from pyspark.context import SparkContext
from awsglue.context import GlueContext

# SparkContext 설정 커스터마이징
conf = SparkContext.getOrCreate().getConf()
conf.set("spark.sql.shuffle.partitions", "200")
conf.set("spark.sql.adaptive.enabled", "true")
conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
conf.set("spark.serializer", "org.apache.spark.serializer.KryoSerializer")

sc = SparkContext.getOrCreate(conf=conf)
glueContext = GlueContext(sc)
spark = glueContext.spark_session
```

```bash
# CLI에서 Spark 설정 전달
aws glue start-job-run \
  --job-name "spark-etl-job" \
  --arguments '{
    "--conf": "spark.sql.shuffle.partitions=400 --conf spark.sql.adaptive.enabled=true --conf spark.sql.files.maxPartitionBytes=134217728"
  }'
```

## 실전 활용

### 사례 1: 대규모 데이터 레이크 ETL

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F
from pyspark.sql.window import Window

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'source_database', 'target_path'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Adaptive Query Execution 활성화
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")

# 소스 데이터 로드 (파티션 프루닝 적용)
events_dyf = glueContext.create_dynamic_frame.from_catalog(
    database=args['source_database'],
    table_name="raw_events",
    push_down_predicate="year='2024' AND month='01'",
    transformation_ctx="events_source",
    additional_options={
        "boundedSize": "1000000000",  # 1GB 단위로 읽기
        "boundedFiles": "100"          # 한 번에 100파일씩
    }
)

users_dyf = glueContext.create_dynamic_frame.from_catalog(
    database=args['source_database'],
    table_name="users",
    transformation_ctx="users_source"
)

# DataFrame으로 변환하여 복잡한 처리 수행
events_df = events_dyf.toDF()
users_df = users_dyf.toDF()

# 브로드캐스트 조인 (작은 테이블)
from pyspark.sql.functions import broadcast
enriched_df = events_df.join(
    broadcast(users_df),
    events_df.user_id == users_df.user_id,
    "left"
).drop(users_df.user_id)

# 집계 처리
daily_summary = enriched_df \
    .withColumn("event_date", F.to_date("event_timestamp")) \
    .groupBy("event_date", "event_type", "user_segment") \
    .agg(
        F.count("*").alias("event_count"),
        F.countDistinct("user_id").alias("unique_users"),
        F.sum("revenue").alias("total_revenue"),
        F.avg("revenue").alias("avg_revenue")
    )

# 결과 저장 (파티셔닝)
daily_summary.write \
    .mode("overwrite") \
    .partitionBy("event_date") \
    .parquet(args['target_path'])

job.commit()
```

```bash
# 위 잡 실행
aws glue start-job-run \
  --job-name "spark-etl-job" \
  --arguments '{
    "--source_database": "analytics_db",
    "--target_path": "s3://my-data-lake/curated/daily_summary/"
  }'
```

### 사례 2: 스트리밍 ETL (Glue Streaming)

Glue는 Spark Structured Streaming을 기반으로 스트리밍 ETL도 지원합니다.

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Kinesis Data Streams에서 스트리밍 데이터 읽기
kinesis_dyf = glueContext.create_data_frame.from_catalog(
    database="streaming_db",
    table_name="kinesis_events",
    transformation_ctx="kinesis_source",
    additional_options={
        "startingPosition": "TRIM_HORIZON",
        "inferSchema": "true"
    }
)

# 윈도우 기반 집계
from pyspark.sql.functions import window

windowed_counts = kinesis_dyf \
    .withWatermark("event_timestamp", "10 minutes") \
    .groupBy(
        window("event_timestamp", "5 minutes"),
        "event_type"
    ) \
    .count()

# S3에 스트리밍 쓰기
glueContext.forEachBatch(
    frame=windowed_counts,
    batch_function=lambda df, epoch_id: df.write
        .mode("append")
        .parquet("s3://my-data-lake/streaming/windowed_counts/"),
    options={
        "windowSize": "60 seconds",
        "checkpointLocation": "s3://my-data-lake/checkpoints/windowed_counts/"
    }
)

job.commit()
```

```bash
# 스트리밍 잡 생성
aws glue create-job \
  --name "streaming-etl-job" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --command '{"Name": "gluestreaming", "ScriptLocation": "s3://my-scripts/streaming_etl.py", "PythonVersion": "3"}' \
  --glue-version "4.0" \
  --number-of-workers 5 \
  --worker-type "G.1X" \
  --default-arguments '{
    "--enable-metrics": "true",
    "--enable-continuous-cloudwatch-log": "true"
  }'
```

### 사례 3: 성능 튜닝 적용 예시

```python
import sys
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 성능 최적화 설정
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.broadcastTimeout", "600")
spark.conf.set("spark.sql.shuffle.partitions", "auto")

# 대용량 테이블 읽기 (파티션 프루닝 + 컬럼 프루닝)
large_table = spark.read \
    .format("parquet") \
    .load("s3://my-data-lake/large_table/") \
    .select("user_id", "event_type", "amount", "event_date") \
    .filter(F.col("event_date") >= "2024-01-01")

# 작은 룩업 테이블 (캐싱)
lookup_table = spark.read.parquet("s3://my-data-lake/lookup/").cache()
lookup_table.count()  # 캐싱 강제 실행

# 브로드캐스트 조인
from pyspark.sql.functions import broadcast
result = large_table.join(
    broadcast(lookup_table),
    "user_id"
)

# 결과를 적절한 파티션 수로 coalesce 후 저장
result \
    .repartition(100, "event_date") \
    .write \
    .mode("overwrite") \
    .partitionBy("event_date") \
    .option("compression", "snappy") \
    .parquet("s3://my-data-lake/optimized_output/")

lookup_table.unpersist()
job.commit()
```

## 모범 사례/보안

### 성능 최적화 모범 사례

1. **Adaptive Query Execution (AQE) 활성화**: Spark 3.x에서 제공하는 AQE를 활성화하면 런타임에 실행 계획을 최적화합니다.

2. **파티션 프루닝**: `push_down_predicate`를 활용하여 불필요한 파티션을 읽지 않도록 합니다.

3. **브로드캐스트 조인**: 작은 테이블(수 GB 이하)과의 조인에는 브로드캐스트 조인을 사용합니다.

4. **데이터 포맷 최적화**: Parquet + Snappy 압축 조합이 일반적으로 최적의 성능을 제공합니다.

5. **적절한 파티션 수**: 셔플 파티션 수를 데이터 크기에 맞게 조정합니다. 일반적으로 파티션당 128MB~256MB가 적절합니다.

6. **S3 요청 최적화**: 작은 파일이 많으면 S3 API 호출이 병목이 됩니다. 파일을 합쳐서 적절한 크기(128MB~512MB)로 유지합니다.

```bash
# Glue 잡의 메트릭과 로그 확인
aws glue get-job-run \
  --job-name "spark-etl-job" \
  --run-id "jr_abc123" \
  --query 'JobRun.{State:JobRunState,ExecutionTime:ExecutionTime,DPUSeconds:DPUSeconds,ErrorMessage:ErrorMessage}'
```

### 보안 모범 사례

1. **IAM 최소 권한**: Glue 잡의 IAM 역할에 필요한 최소 권한만 부여합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::my-data-lake/raw/*",
        "arn:aws:s3:::my-data-lake/curated/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetTable",
        "glue:GetPartitions",
        "glue:GetDatabase"
      ],
      "Resource": [
        "arn:aws:glue:ap-northeast-2:123456789012:catalog",
        "arn:aws:glue:ap-northeast-2:123456789012:database/analytics_db",
        "arn:aws:glue:ap-northeast-2:123456789012:table/analytics_db/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["logs:*"],
      "Resource": "arn:aws:logs:*:*:log-group:/aws-glue/*"
    }
  ]
}
```

2. **데이터 암호화**: S3 데이터와 Glue 임시 데이터를 KMS로 암호화합니다.

3. **VPC 네트워크 격리**: JDBC 소스에 접근하는 잡은 VPC 내에서 실행하도록 Connection을 설정합니다.

4. **보안 설정(Security Configuration)**: Glue 보안 설정을 통해 S3 암호화, CloudWatch 로그 암호화, Job Bookmark 암호화를 일괄 적용합니다.

```bash
# 보안 설정 생성
aws glue create-security-configuration \
  --name "secure-etl-config" \
  --encryption-configuration '{
    "S3Encryption": [{"S3EncryptionMode": "SSE-KMS", "KmsKeyArn": "arn:aws:kms:ap-northeast-2:123456789012:key/my-key"}],
    "CloudWatchEncryption": {"CloudWatchEncryptionMode": "SSE-KMS", "KmsKeyArn": "arn:aws:kms:ap-northeast-2:123456789012:key/my-key"},
    "JobBookmarksEncryption": {"JobBookmarksEncryptionMode": "CSE-KMS", "KmsKeyArn": "arn:aws:kms:ap-northeast-2:123456789012:key/my-key"}
  }'
```

### 비용 최적화

1. **Auto Scaling 활용**: 고정 워커 수 대신 Auto Scaling을 활성화하여 실제 필요한 만큼만 리소스를 사용합니다.
2. **Flex 실행 클래스**: 비긴급 잡에는 Flex 실행 클래스를 사용하여 비용을 절감합니다.
3. **타임아웃 설정**: 무한 실행을 방지하기 위해 적절한 타임아웃을 설정합니다.

```bash
# Flex 실행 클래스로 잡 실행 (비용 절감)
aws glue start-job-run \
  --job-name "batch-etl-job" \
  --execution-class "FLEX"
```

## 관련 서비스 비교

| 항목 | AWS Glue Spark | Amazon EMR | Amazon EMR Serverless |
|------|---------------|------------|----------------------|
| 관리 방식 | 서버리스 | 관리형 클러스터 | 서버리스 |
| Spark 버전 | Glue 버전에 고정 | 자유 선택 | 자유 선택 |
| 인프라 관리 | 불필요 | 클러스터 관리 필요 | 불필요 |
| 시작 시간 | 1~3분 (콜드 스타트) | 5~15분 | 수 초~분 |
| Auto Scaling | 지원 (워커 수) | 지원 (인스턴스) | 네이티브 |
| Data Catalog 통합 | 네이티브 | 설정 필요 | 설정 필요 |
| DynamicFrame | 지원 | 라이브러리 추가 | 라이브러리 추가 |
| Job Bookmark | 지원 | 미지원 | 미지원 |
| 비용 모델 | DPU 분 단위 | 인스턴스 시간 | vCPU/메모리 시간 |
| 커스터마이징 | 제한적 | 완전한 제어 | 중간 수준 |
| 스트리밍 | Micro-batch | 실시간 지원 | 실시간 지원 |
| 적합한 워크로드 | ETL 중심 | 범용 빅데이터 | 간헐적 빅데이터 |

## 요약

AWS Glue for Apache Spark는 서버리스 관리형 Spark 환경을 제공하여 ETL 워크로드에 최적화된 서비스입니다. Glue 4.0 기준 Spark 3.3.0을 기반으로 하며, DynamicFrame, Job Bookmark, Data Catalog 통합 등 ETL에 특화된 기능을 추가로 제공합니다.

다양한 워커 타입(G.1X~G.8X)으로 워크로드 특성에 맞는 리소스를 할당할 수 있으며, Auto Scaling을 통해 비용을 최적화할 수 있습니다. Spark UI, CloudWatch 메트릭, 연속 로깅 등 모니터링 기능도 충실합니다.

EMR 대비 인프라 관리 부담이 없고 ETL에 특화된 기능이 풍부하지만, Spark 버전 선택의 자유도가 낮고 클러스터 수준의 세밀한 튜닝이 제한적입니다. ETL 중심 워크로드에는 Glue를, 범용 빅데이터 처리에는 EMR을 선택하는 것이 일반적인 가이드라인입니다.