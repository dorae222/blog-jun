<!-- infographic-hero -->
![AWS Glue 개요 및 주요 특징 핵심 요약](figures/infographic.svg)

*Figure: AWS Glue 개요 및 주요 특징 한 장 요약 인포그래픽*

# AWS Glue 개요 및 주요 특징

## 개요

AWS Glue는 데이터 통합을 위한 완전 관리형 서버리스 ETL(Extract, Transform, Load) 서비스입니다. 데이터 소스의 검색, 카탈로그 작성, 변환, 로드를 자동화하여 분석 워크로드를 위한 데이터 준비 과정을 크게 간소화합니다.

AWS Glue는 2017년에 처음 출시된 이후 지속적으로 기능이 확장되어, 현재는 ETL뿐만 아니라 데이터 카탈로그, 데이터 품질 관리, 스트리밍 ETL, 데이터 준비(DataBrew) 등 포괄적인 데이터 통합 플랫폼으로 발전했습니다.

주요 특징은 다음과 같습니다.

- **서버리스**: 인프라를 프로비저닝하거나 관리할 필요가 없습니다. Glue가 필요한 리소스를 자동으로 할당합니다.
- **Apache Spark 기반**: 대규모 데이터 처리를 위해 Apache Spark 엔진을 기반으로 합니다.
- **Data Catalog**: 중앙 집중식 메타데이터 저장소로, 데이터 소스의 스키마와 위치 정보를 관리합니다.
- **자동 스키마 검색**: Crawler가 데이터 소스를 자동으로 스캔하여 스키마를 검색합니다.
- **다양한 커넥터**: S3, RDS, Redshift, DynamoDB, Kinesis 등 다양한 데이터 소스와 연결됩니다.
- **Visual ETL**: 코드 없이 드래그 앤 드롭으로 ETL 파이프라인을 구성할 수 있습니다.

## 핵심 기능

### 1. AWS Glue Data Catalog

Data Catalog은 AWS Glue의 핵심 구성 요소로, 중앙 집중식 메타데이터 저장소입니다. Apache Hive Metastore와 호환되며, Amazon Athena, Amazon Redshift Spectrum, Amazon EMR 등에서 공유 메타데이터 저장소로 사용됩니다.

```bash
# 데이터베이스 생성
aws glue create-database \
  --database-input '{
    "Name": "analytics_db",
    "Description": "분석용 데이터베이스",
    "LocationUri": "s3://my-data-lake/analytics/"
  }'

# 데이터베이스 목록 조회
aws glue get-databases \
  --query 'DatabaseList[].{Name:Name,Description:Description,Location:LocationUri}' \
  --output table

# 테이블 생성
aws glue create-table \
  --database-name analytics_db \
  --table-input '{
    "Name": "sales_data",
    "Description": "일별 매출 데이터",
    "StorageDescriptor": {
      "Columns": [
        {"Name": "sale_date", "Type": "date", "Comment": "매출 발생 일자"},
        {"Name": "product_id", "Type": "string", "Comment": "제품 ID"},
        {"Name": "category", "Type": "string", "Comment": "제품 카테고리"},
        {"Name": "amount", "Type": "decimal(10,2)", "Comment": "매출액"},
        {"Name": "quantity", "Type": "int", "Comment": "판매 수량"}
      ],
      "Location": "s3://my-data-lake/analytics/sales/",
      "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
      "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
      "SerdeInfo": {
        "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
      }
    },
    "PartitionKeys": [
      {"Name": "year", "Type": "string"},
      {"Name": "month", "Type": "string"}
    ],
    "TableType": "EXTERNAL_TABLE"
  }'
```

### 2. ETL 작업 (Jobs)

Glue ETL 작업은 데이터 변환 로직을 실행하는 핵심 구성 요소입니다. Python Shell, PySpark, Spark(Scala), Ray 등 다양한 런타임을 지원합니다.

#### 작업 유형

- **Spark 작업**: Apache Spark 기반의 대규모 데이터 처리에 적합합니다. PySpark 또는 Scala로 작성합니다.
- **Python Shell 작업**: 소규모 데이터 처리나 API 호출 등 간단한 작업에 적합합니다.
- **Ray 작업**: Ray 프레임워크를 기반으로 한 분산 Python 작업입니다.
- **Streaming 작업**: Kinesis Data Streams나 Apache Kafka에서 실시간 데이터를 처리합니다.

```bash
# Spark ETL 작업 생성
aws glue create-job \
  --name "sales-etl-job" \
  --role "arn:aws:iam::123456789012:role/GlueETLRole" \
  --command '{
    "Name": "glueetl",
    "ScriptLocation": "s3://my-glue-scripts/etl/sales_transform.py",
    "PythonVersion": "3"
  }' \
  --default-arguments '{
    "--job-language": "python",
    "--job-bookmark-option": "job-bookmark-enable",
    "--enable-metrics": "true",
    "--enable-continuous-cloudwatch-log": "true",
    "--enable-glue-datacatalog": "true",
    "--TempDir": "s3://my-glue-temp/temp/",
    "--additional-python-modules": "pandas==2.0.0,pyarrow==14.0.0"
  }' \
  --glue-version "4.0" \
  --number-of-workers 10 \
  --worker-type "G.1X" \
  --timeout 120

# 작업 실행
aws glue start-job-run \
  --job-name "sales-etl-job" \
  --arguments '{"--source_path": "s3://raw-data/sales/", "--target_path": "s3://processed-data/sales/"}'

# 작업 실행 상태 확인
aws glue get-job-run \
  --job-name "sales-etl-job" \
  --run-id jr_abc123 \
  --query 'JobRun.{Status:JobRunState,StartedOn:StartedOn,ExecutionTime:ExecutionTime,DPUSeconds:DPUSeconds}'
```

### 3. Glue Crawler

Crawler는 데이터 소스를 자동으로 스캔하여 스키마를 검색하고 Data Catalog에 메타데이터를 등록합니다. (별도의 포스트에서 자세히 다룹니다.)

### 4. Glue Classifier

Classifier는 Crawler가 데이터의 스키마를 판별하는 데 사용하는 규칙입니다. (별도의 포스트에서 자세히 다룹니다.)

### 5. Job Bookmark

Job Bookmark는 ETL 작업이 이전에 처리한 데이터를 추적하여, 동일한 데이터를 중복 처리하지 않도록 하는 기능입니다.

```bash
# Job Bookmark 초기화 (필요 시)
aws glue reset-job-bookmark \
  --job-name "sales-etl-job"

# Job Bookmark 상태 조회
aws glue get-job-bookmark \
  --job-name "sales-etl-job"
```

### 6. Glue DataBrew

Glue DataBrew는 코드 없이 시각적으로 데이터를 탐색하고 변환할 수 있는 데이터 준비 도구입니다.

```bash
# DataBrew 프로젝트 목록 조회
aws databrew list-projects \
  --query 'Projects[].{Name:Name,RecipeName:RecipeName,DatasetName:DatasetName}' \
  --output table

# DataBrew 레시피 작업 생성
aws databrew create-recipe-job \
  --name "data-cleansing-job" \
  --project-name "sales-cleansing" \
  --role-arn "arn:aws:iam::123456789012:role/DataBrewRole" \
  --outputs '[{
    "Location": {"Bucket": "cleaned-data", "Key": "sales/"},
    "Format": "PARQUET",
    "Overwrite": true,
    "CompressionFormat": "SNAPPY"
  }]'
```

### 7. Glue Data Quality

Glue Data Quality는 DQDL(Data Quality Definition Language)을 사용하여 데이터 품질 규칙을 정의하고 검증합니다.

```bash
# 데이터 품질 규칙셋 생성
aws glue create-data-quality-ruleset \
  --name "sales-quality-rules" \
  --ruleset "Rules = [ \n  RowCount > 0, \n  IsComplete \"product_id\", \n  IsComplete \"amount\", \n  ColumnValues \"amount\" > 0, \n  IsUnique \"order_id\", \n  Completeness \"category\" >= 0.95 \n]" \
  --target-table '{"DatabaseName": "analytics_db", "TableName": "sales_data"}'
```

### 8. Glue Workflow

Glue Workflow는 여러 Glue 작업(Crawler, ETL Job, Trigger)을 연결하여 복잡한 데이터 파이프라인을 구성합니다.

```bash
# 워크플로 생성
aws glue create-workflow \
  --name "daily-etl-pipeline" \
  --description "일별 ETL 파이프라인" \
  --max-concurrent-runs 1

# 트리거 생성 (스케줄 기반)
aws glue create-trigger \
  --name "daily-trigger" \
  --type SCHEDULED \
  --schedule "cron(0 6 * * ? *)" \
  --workflow-name "daily-etl-pipeline" \
  --actions '[{"JobName": "sales-etl-job"}]' \
  --start-on-creation

# 조건부 트리거 (이전 작업 완료 후 실행)
aws glue create-trigger \
  --name "post-etl-crawler" \
  --type CONDITIONAL \
  --workflow-name "daily-etl-pipeline" \
  --predicate '{"Conditions": [{"LogicalOperator": "EQUALS", "JobName": "sales-etl-job", "State": "SUCCEEDED"}]}' \
  --actions '[{"CrawlerName": "sales-crawler"}]' \
  --start-on-creation
```

## 아키텍처/동작 원리

### 전체 아키텍처

```
[데이터 소스]          [AWS Glue]                    [데이터 대상]
  S3            -->  [Crawler] --> [Data Catalog]     --> Athena
  RDS           -->  [ETL Job] --> [변환 처리]        --> Redshift
  DynamoDB      -->  [DataBrew] --> [데이터 정제]     --> S3 Data Lake
  Kinesis       -->  [Streaming Job] --> [실시간 처리] --> OpenSearch
                     [Workflow] --> [파이프라인 오케스트레이션]
                     [Data Quality] --> [품질 검증]
```

### DPU (Data Processing Unit)

Glue의 리소스 단위는 DPU(Data Processing Unit)입니다. 1 DPU는 4 vCPU와 16GB 메모리를 제공합니다.

#### Worker Type

| Worker Type | vCPU | 메모리 | 디스크 | 적합한 용도 |
|-------------|------|--------|--------|-------------|
| Standard | 4 | 16 GB | 50 GB | 일반 ETL |
| G.1X | 4 | 16 GB | 64 GB | 메모리 집약적 ETL |
| G.2X | 8 | 32 GB | 128 GB | 대규모 데이터 처리 |
| G.4X | 16 | 64 GB | 256 GB | ML 변환 작업 |
| G.8X | 32 | 128 GB | 512 GB | 초대규모 처리 |
| Z.2X | 8 | 64 GB | 128 GB | Ray 작업 |

### Spark 기반 처리

Glue ETL은 내부적으로 Apache Spark를 사용합니다. Glue는 Spark의 DataFrame/Dataset API를 확장하여 DynamicFrame이라는 자체 추상화를 제공합니다.

#### DynamicFrame vs DataFrame

- **DynamicFrame**: Glue 고유의 추상화로, 스키마가 불일치하는 데이터를 유연하게 처리할 수 있습니다. 동일한 열에 서로 다른 데이터 타입이 존재하는 경우를 자동으로 처리합니다.
- **DataFrame**: Spark의 표준 추상화로, 고정된 스키마를 기반으로 동작합니다. 더 넓은 Spark 생태계의 기능을 활용할 수 있습니다.

```python
# Glue ETL 스크립트 예시
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'source_path', 'target_path'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Data Catalog에서 소스 데이터 읽기
source_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="analytics_db",
    table_name="raw_sales",
    transformation_ctx="source"
)

# 스키마 변환
mapped_dyf = ApplyMapping.apply(
    frame=source_dyf,
    mappings=[
        ("sale_date", "string", "sale_date", "date"),
        ("product_id", "string", "product_id", "string"),
        ("category", "string", "category", "string"),
        ("amount", "string", "amount", "decimal(10,2)"),
        ("quantity", "string", "quantity", "int")
    ]
)

# NULL 값 제거
filtered_dyf = Filter.apply(
    frame=mapped_dyf,
    f=lambda x: x["product_id"] is not None and x["amount"] is not None
)

# S3에 Parquet 형식으로 저장
glueContext.write_dynamic_frame.from_options(
    frame=filtered_dyf,
    connection_type="s3",
    connection_options={
        "path": args['target_path'],
        "partitionKeys": ["category"]
    },
    format="parquet"
)

job.commit()
```

## 실전 활용

### 활용 사례 1: 데이터 레이크 ETL 파이프라인

S3 기반 데이터 레이크에서 원시 데이터를 정제하여 분석 가능한 형태로 변환하는 파이프라인입니다.

```bash
# 완성된 파이프라인의 워크플로 실행
aws glue start-workflow-run \
  --name "daily-etl-pipeline"

# 워크플로 실행 상태 확인
aws glue get-workflow-run \
  --name "daily-etl-pipeline" \
  --run-id wr_abc123 \
  --query 'Run.{Status:Status,StartedOn:StartedOn,Statistics:Statistics}'
```

### 활용 사례 2: CDC(Change Data Capture) 처리

RDS에서 DMS를 통해 S3로 전달된 CDC 데이터를 Glue로 처리하여 데이터 레이크를 업데이트합니다.

### 활용 사례 3: 스트리밍 ETL

Kinesis Data Streams의 실시간 데이터를 Glue Streaming으로 처리합니다.

```bash
# 스트리밍 ETL 작업 생성
aws glue create-job \
  --name "streaming-etl-job" \
  --role "arn:aws:iam::123456789012:role/GlueETLRole" \
  --command '{"Name": "gluestreaming", "ScriptLocation": "s3://my-glue-scripts/streaming/kinesis_to_s3.py", "PythonVersion": "3"}' \
  --glue-version "4.0" \
  --number-of-workers 2 \
  --worker-type "G.1X"
```

## 모범 사례/보안

### 성능 최적화

1. **파티셔닝**: 대규모 데이터셋은 날짜, 카테고리 등으로 파티셔닝하여 Crawler와 ETL 작업의 성능을 향상시킵니다.
2. **Parquet/ORC 형식**: 컬럼 기반 형식을 사용하면 스캔량을 줄여 비용과 시간을 절약합니다.
3. **Job Bookmark**: 증분 처리를 활성화하여 이미 처리된 데이터를 건너뜁니다.
4. **적절한 Worker 구성**: 데이터 크기와 복잡도에 맞는 Worker Type과 수를 설정합니다.
5. **Push-Down Predicate**: 소스 수준에서 필터링을 수행하여 불필요한 데이터 읽기를 줄입니다.

### 보안 모범 사례

1. **IAM 역할 분리**: ETL 작업별로 최소 권한의 IAM 역할을 사용합니다.
2. **데이터 암호화**: S3 SSE 또는 KMS를 사용하여 저장 데이터를 암호화합니다.
3. **VPC 연결**: 프라이빗 데이터 소스에 접근할 때는 Glue Connection을 통해 VPC에 연결합니다.
4. **CloudWatch 모니터링**: 작업 메트릭과 로그를 CloudWatch로 전송하여 모니터링합니다.

```bash
# Glue Connection 생성 (VPC 연결)
aws glue create-connection \
  --connection-input '{
    "Name": "rds-vpc-connection",
    "ConnectionType": "JDBC",
    "ConnectionProperties": {
      "JDBC_CONNECTION_URL": "jdbc:postgresql://mydb.abc123.ap-northeast-2.rds.amazonaws.com:5432/mydb",
      "USERNAME": "glue_user",
      "PASSWORD": "PLACEHOLDER"
    },
    "PhysicalConnectionRequirements": {
      "SubnetId": "subnet-abc123",
      "SecurityGroupIdList": ["sg-abc123"],
      "AvailabilityZone": "ap-northeast-2a"
    }
  }'
```

### 비용 최적화

1. **Auto Scaling 활성화**: Glue 4.0에서는 Worker 수를 자동으로 조절하는 Auto Scaling을 지원합니다.
2. **Flex 실행**: 비긴급 작업에는 Flex 실행 유형을 사용하여 비용을 절감합니다.
3. **작업 타임아웃 설정**: 무한 실행을 방지하기 위해 적절한 타임아웃을 설정합니다.
4. **Python Shell 활용**: 소규모 작업에는 Spark 대신 Python Shell을 사용하여 비용을 절감합니다.

## 관련 서비스 비교

| 항목 | AWS Glue | Amazon EMR | AWS Step Functions | Apache Airflow (MWAA) |
|------|---------|------------|-------------------|----------------------|
| 유형 | 서버리스 ETL | 관리형 Hadoop/Spark | 서버리스 오케스트레이션 | 관리형 워크플로 |
| 인프라 관리 | 불필요 | 클러스터 관리 | 불필요 | 반관리형 |
| 데이터 카탈로그 | 내장 | Glue 연동 | 미포함 | 미포함 |
| 스트리밍 | 지원 | 지원 | 미지원 | 미지원 |
| 비용 모델 | DPU/초 | 인스턴스/시간 | 상태 전환 횟수 | 환경 비용 |
| 적합한 용도 | ETL/데이터 통합 | 대규모 데이터 처리 | 마이크로서비스 오케스트레이션 | 복잡한 DAG 워크플로 |

## 요약

AWS Glue는 데이터 통합과 ETL을 위한 포괄적인 서버리스 플랫폼입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **서버리스 ETL**: 인프라 관리 없이 대규모 데이터 변환 작업을 실행할 수 있습니다.
- **Data Catalog**: Athena, Redshift Spectrum, EMR 등과 공유할 수 있는 중앙 집중식 메타데이터 저장소를 제공합니다.
- **자동 스키마 검색**: Crawler와 Classifier를 통해 데이터 소스의 스키마를 자동으로 검색합니다.
- **다양한 작업 유형**: Spark, Python Shell, Ray, Streaming 등 워크로드에 맞는 작업 유형을 선택할 수 있습니다.
- **DynamicFrame**: 스키마가 불일치하는 데이터를 유연하게 처리하는 Glue 고유의 추상화를 제공합니다.
- **Data Quality**: DQDL을 통해 데이터 품질 규칙을 정의하고 자동으로 검증합니다.
- **Workflow**: 여러 작업을 연결하여 복잡한 데이터 파이프라인을 구성할 수 있습니다.

AWS에서 데이터 레이크를 구축하거나 ETL 파이프라인을 운영하는 조직에게 Glue는 핵심적인 서비스입니다.