<!-- infographic-hero -->
![AWS Glue Studio 개요 및 핵심 포인트 - 시각적 ETL 작업 구축 가이드 핵심 요약](figures/infographic.svg)

*Figure: AWS Glue Studio 개요 및 핵심 포인트 - 시각적 ETL 작업 구축 가이드 한 장 요약 인포그래픽*

# AWS Glue Studio 개요 및 핵심 포인트 - 시각적 ETL 작업 구축 가이드

## 개요

AWS Glue Studio는 AWS Glue ETL 작업을 시각적 인터페이스로 설계, 실행, 모니터링할 수 있는 완전관리형 서비스입니다. 코드를 직접 작성하지 않고도 드래그 앤 드롭 방식의 DAG(Directed Acyclic Graph) 에디터를 통해 복잡한 데이터 변환 파이프라인을 구축할 수 있습니다.

기존 Glue Console에서 ETL Job을 생성하려면 PySpark나 Scala 코드를 직접 작성해야 했지만, Glue Studio는 시각적 노드 기반 편집기를 제공하여 데이터 소스 선택, 변환 적용, 대상 지정을 GUI로 수행할 수 있습니다. 시각적으로 구성한 파이프라인은 자동으로 PySpark 코드로 변환되어 실행됩니다.

## 핵심 기능

### 시각적 DAG 에디터

Glue Studio의 핵심은 시각적 DAG 에디터입니다. 세 가지 유형의 노드를 조합하여 ETL 파이프라인을 구성합니다.

| 노드 유형 | 역할 | 예시 |
|-----------|------|------|
| Source | 데이터 소스 정의 | S3, Glue Catalog, JDBC, Kinesis, Kafka |
| Transform | 데이터 변환 로직 | Filter, Join, Map, Aggregate, Custom SQL |
| Target | 변환 결과 저장 대상 | S3, Glue Catalog, JDBC, Redshift |

### 주요 변환 노드

**ApplyMapping**: 컬럼명 변경, 데이터 타입 캐스팅, 불필요한 컬럼 제거

**Filter**: 조건 기반 레코드 필터링 (예: `status = 'active'`)

**Join**: 두 데이터셋의 결합 (Inner, Left, Right, Full Outer, Left Semi, Left Anti)

**Aggregate**: 그룹별 집계 (Count, Sum, Average, Min, Max)

**SelectFields / DropFields**: 특정 컬럼 선택 또는 제거

**SplitRows**: 조건에 따라 레코드를 두 개의 출력으로 분기

**FillMissingValues**: 머신러닝 기반 결측값 자동 채우기

**Custom Code**: PySpark, Spark SQL 코드 직접 삽입

### 데이터 프리뷰

파이프라인 구성 중 각 노드의 출력을 미리 확인할 수 있습니다. 샘플 데이터로 변환 결과를 즉시 검증하여 디버깅 시간을 단축합니다.

### Job Monitoring Dashboard

Glue Studio는 실행 중인 Job과 완료된 Job의 상태를 시각적 대시보드로 제공합니다.

- 실행 시간, DPU 사용량, 처리된 행 수
- 실행 이력 및 트렌드 그래프
- 에러 로그 및 CloudWatch 연동
- Job Bookmark 상태 확인

## 아키텍처 및 동작 원리

Glue Studio의 내부 동작 흐름은 다음과 같습니다.

```
[Glue Studio 시각적 에디터]
          |
          v
[DAG 노드 구성 (Source -> Transform -> Target)]
          |
          v
[자동 PySpark 코드 생성]
          |
          v
[Glue ETL Job으로 등록]
          |
          v
[Spark 클러스터에서 실행]
    |         |
[DPU 자동 할당]  [Job Bookmark 관리]
    |         |
    v         v
[데이터 처리 및 변환]
          |
          v
[대상(S3/Redshift/JDBC)에 결과 저장]
          |
          v
[Monitoring Dashboard 업데이트]
```

시각적으로 구성한 파이프라인은 내부적으로 GlueContext, DynamicFrame 기반의 PySpark 코드로 변환됩니다. 'Script' 탭에서 생성된 코드를 확인하고 필요 시 직접 수정할 수 있습니다.

### Worker Type과 DPU

| Worker Type | vCPU | 메모리 | 디스크 | 적합한 작업 |
|------------|------|--------|--------|------------|
| G.1X | 4 | 16GB | 64GB | 일반 ETL |
| G.2X | 8 | 32GB | 128GB | 메모리 집약 작업 |
| G.4X | 16 | 64GB | 256GB | ML Transform |
| G.8X | 32 | 128GB | 512GB | 대규모 셔플 |
| G.025X | 2 | 4GB | 64GB | 소규모 작업 |
| Z.2X | 8 | 64GB | 128GB | Ray 기반 작업 |

## 실전 활용

### AWS CLI를 사용한 Glue Studio Job 관리

```bash
# 기존 Glue Studio Job 목록 조회
aws glue get-jobs \
    --query 'Jobs[?Command.Name==`glueetl`].{Name:Name,Type:Command.Name,Workers:NumberOfWorkers,WorkerType:WorkerType,Created:CreatedOn}' \
    --output table

# Glue Studio Job 실행
aws glue start-job-run \
    --job-name sales-etl-pipeline \
    --arguments '{"--source_path": "s3://my-datalake/raw/sales/", "--target_path": "s3://my-datalake/curated/sales/"}'

# Job 실행 상태 확인
aws glue get-job-run \
    --job-name sales-etl-pipeline \
    --run-id jr_abc123 \
    --query '{Status:JobRun.JobRunState,Started:JobRun.StartedOn,DPU:JobRun.AllocatedCapacity,Duration:JobRun.ExecutionTime}'

# Job 실행 이력 조회
aws glue get-job-runs \
    --job-name sales-etl-pipeline \
    --query 'JobRuns[].{RunId:Id,Status:JobRunState,Duration:ExecutionTime,DPU:NumberOfWorkers}' \
    --output table

# Job Bookmark 초기화 (전체 재처리 필요 시)
aws glue reset-job-bookmark \
    --job-name sales-etl-pipeline

# Glue Studio Job 생성 (CLI)
aws glue create-job \
    --name new-etl-job \
    --role arn:aws:iam::123456789012:role/AWSGlueServiceRole \
    --command '{
        "Name": "glueetl",
        "ScriptLocation": "s3://my-glue-scripts/etl/new-etl-job.py",
        "PythonVersion": "3"
    }' \
    --glue-version "4.0" \
    --number-of-workers 2 \
    --worker-type G.1X \
    --default-arguments '{
        "--job-bookmark-option": "job-bookmark-enable",
        "--TempDir": "s3://my-glue-temp/",
        "--enable-metrics": "true",
        "--enable-continuous-cloudwatch-log": "true"
    }'
```

### Glue Studio에서 생성된 PySpark 코드 예시

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

# Source: S3 (Glue Catalog)
source_df = glueContext.create_dynamic_frame.from_catalog(
    database="analytics_db",
    table_name="raw_sales",
    transformation_ctx="source"
)

# Transform: Filter active records
filtered_df = Filter.apply(
    frame=source_df,
    f=lambda row: row["status"] == "active"
)

# Transform: ApplyMapping
mapped_df = ApplyMapping.apply(
    frame=filtered_df,
    mappings=[
        ("order_id", "string", "order_id", "string"),
        ("amount", "string", "amount", "double"),
        ("created_at", "string", "created_at", "timestamp")
    ]
)

# Target: S3 Parquet
glueContext.write_dynamic_frame.from_options(
    frame=mapped_df,
    connection_type="s3",
    format="parquet",
    connection_options={"path": "s3://my-datalake/curated/sales/"},
    transformation_ctx="target"
)

job.commit()
```



### Notebook 기반 개발

Glue Studio는 Jupyter Notebook 기반의 대화형 개발 환경도 제공합니다. 시각적 에디터와 노트북 에디터를 전환하며 작업할 수 있어, 프로토타이핑과 디버깅에 유용합니다.

```python
# Glue Studio Notebook에서 Interactive Session 시작
%idle_timeout 60
%glue_version 4.0
%worker_type G.1X
%number_of_workers 2

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session

# 대화형으로 데이터 탐색
df = glueContext.create_dynamic_frame.from_catalog(
    database="analytics_db", table_name="raw_sales"
)
df.toDF().show(5)
df.toDF().printSchema()
```

### Glue Workflow 연동

Glue Studio에서 만든 Job을 Glue Workflow로 연결하여 복잡한 ETL 파이프라인을 구성할 수 있습니다.

```bash
# Workflow 생성
aws glue create-workflow --name sales-etl-workflow

# Crawler 트리거 (Workflow 시작점)
aws glue create-trigger \
    --name start-crawler \
    --type ON_DEMAND \
    --workflow-name sales-etl-workflow \
    --actions '[{"CrawlerName": "sales-data-crawler"}]'

# Crawler 완료 후 ETL Job 실행
aws glue create-trigger \
    --name after-crawler \
    --type CONDITIONAL \
    --workflow-name sales-etl-workflow \
    --predicate '{
        "Logical": "ANY",
        "Conditions": [{
            "LogicalOperator": "EQUALS",
            "CrawlerName": "sales-data-crawler",
            "CrawlState": "SUCCEEDED"
        }]
    }' \
    --actions '[{"JobName": "sales-etl-pipeline"}]'

# Workflow 실행
aws glue start-workflow-run --name sales-etl-workflow

# Workflow 실행 상태 확인
aws glue get-workflow-run \
    --name sales-etl-workflow \
    --run-id wr_abc123 \
    --include-graph
```

### 데이터 품질 검사 (Data Quality)

Glue Studio는 ETL 파이프라인에 데이터 품질 검사 노드를 추가할 수 있습니다. DQDL(Data Quality Definition Language)로 규칙을 정의합니다.

```python
# Data Quality 규칙 예시 (DQDL)
rules = """
Rules = [
    ColumnExists "order_id",
    IsComplete "order_id",
    IsUnique "order_id",
    ColumnValues "amount" > 0,
    ColumnValues "status" in ["active", "completed", "cancelled"],
    Completeness "email" >= 0.95,
    RowCount between 1000 and 10000000
]
"""
```

Glue Studio의 시각적 에디터에서 'Evaluate Data Quality' 노드를 추가하면, 위 규칙을 GUI로 작성하고 품질 검사 결과에 따라 파이프라인을 분기시킬 수 있습니다(통과한 레코드와 실패한 레코드를 분리).

### Sensitive Data Detection

Glue Studio는 PII(개인식별정보) 탐지 변환 노드를 제공합니다. 이메일, 전화번호, 신용카드 번호 등을 자동으로 감지하고 마스킹할 수 있습니다.

```bash
# Sensitive Data Detection 결과 확인
aws glue get-job-run \
    --job-name pii-detection-job \
    --run-id jr_abc123 \
    --query 'JobRun.{Status:JobRunState,Metrics:Arguments}'
```

## 모범 사례 및 보안

### 성능 최적화

- Worker Type은 작업 특성에 맞게 선택합니다. 일반 ETL은 G.1X, Join이 많은 작업은 G.2X, 소규모 작업은 G.025X가 적합합니다.
- Job Bookmark를 활성화하여 증분 처리를 구현합니다. 이미 처리된 데이터를 건너뛰어 실행 시간과 비용을 절감합니다.
- Auto Scaling을 활성화하면 필요에 따라 Worker 수가 자동 조절됩니다.
- Parquet/ORC 같은 컬럼 기반 포맷으로 출력하여 다운스트림 쿼리 성능을 개선합니다.

### 비용 관리

- DPU-시간 기반 과금이므로, 실행 시간을 단축하는 것이 비용 절감의 핵심입니다.
- 개발/테스트 시 Worker 수를 최소(2개)로 설정하고, 프로덕션에서만 스케일 업합니다.
- 연속 실행(Continuous Logging)은 CloudWatch 비용이 추가되므로, 디버깅 시에만 활성화합니다.
- Glue Studio의 데이터 프리뷰 기능을 적극 활용하여 개발 단계에서 오류를 조기에 발견합니다.

### 보안

- Glue Job IAM 역할에 최소 권한을 부여합니다. 소스와 타깃 S3 버킷에 대해서만 접근을 허용합니다.
- JDBC 연결 시 Secrets Manager를 통해 데이터베이스 자격 증명을 안전하게 관리합니다.
- S3 데이터에 KMS 암호화를 적용하고, Glue Job에서 KMS 키 사용 권한을 부여합니다.
- VPC 내에서 Job을 실행하여 데이터 소스에 대한 네트워크 접근을 제어합니다.
- CloudTrail을 활성화하여 Glue API 호출을 감사합니다.

## 관련 서비스 비교

| 항목 | Glue Studio | Glue Console (코드) | Step Functions | MWAA (Airflow) |
|------|------------|--------------------|----|-----|
| 인터페이스 | 시각적 DAG | 코드 에디터 | 시각적 상태 머신 | DAG 코드 |
| 코딩 필요 | 최소 | PySpark/Scala | JSON/YAML | Python |
| ETL 특화 | 높음 | 높음 | 범용 | 범용 |
| 모니터링 | 내장 대시보드 | CloudWatch | 실행 이력 | Airflow UI |
| 적합한 사용자 | 데이터 분석가 | 데이터 엔지니어 | 개발자 | 데이터 엔지니어 |

## 요약

AWS Glue Studio는 시각적 DAG 에디터를 통해 코드 작성 없이 ETL 파이프라인을 구축할 수 있는 서비스입니다. Source, Transform, Target 노드를 드래그 앤 드롭으로 연결하면 PySpark 코드가 자동 생성되어 Spark 클러스터에서 실행됩니다. 데이터 프리뷰와 모니터링 대시보드를 제공하여 개발과 운영 효율성을 높이며, Custom Code 노드를 통해 복잡한 변환도 처리할 수 있습니다. 데이터 분석가와 엔지니어 모두에게 적합한 ETL 도구로, Job Bookmark를 통한 증분 처리와 Auto Scaling을 통한 비용 최적화가 핵심 모범 사례입니다.