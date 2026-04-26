<!-- infographic-hero -->
![AWS Glue Job 개요 핵심 요약](figures/infographic.svg)

*Figure: AWS Glue Job 개요 한 장 요약 인포그래픽*

# AWS Glue Job 개요

## 개요

AWS Glue Job은 AWS Glue 서비스에서 ETL(Extract, Transform, Load) 작업을 실제로 실행하는 핵심 실행 단위입니다. 데이터 레이크, 데이터 웨어하우스, 분석 파이프라인 등 다양한 데이터 처리 시나리오에서 활용되며, Apache Spark 기반의 분산 처리 엔진을 통해 대용량 데이터를 효율적으로 처리할 수 있습니다.

Glue Job은 서버리스로 동작하기 때문에 인프라를 직접 관리할 필요가 없습니다. DPU(Data Processing Unit)를 기반으로 자동 확장되며, 사용자는 ETL 로직 개발에만 집중할 수 있습니다. S3, RDS, Redshift, DynamoDB 등 AWS의 주요 데이터 저장소와 원활하게 연동되어, 엔터프라이즈 수준의 데이터 파이프라인을 구축하는 데 적합합니다.

Glue Job의 핵심 역할은 다음 세 가지로 요약할 수 있습니다.

- **데이터 추출(Extract)**: S3, JDBC, DynamoDB, Kinesis 등 다양한 소스에서 데이터를 읽어옵니다.
- **데이터 변환(Transform)**: 정제, 타입 변환, 조인, 집계, 필터링 등 비즈니스 로직을 적용합니다.
- **데이터 적재(Load)**: S3, Redshift, RDS, Elasticsearch 등 대상 저장소로 결과를 저장합니다.

## 핵심 기능

### Glue Job의 주요 유형

AWS Glue Job은 처리 목적과 데이터 규모에 따라 네 가지 유형을 제공합니다.

#### 1. Spark ETL Job

Glue Job의 가장 대표적인 유형으로, Apache Spark 엔진 기반의 분산 처리를 수행합니다. PySpark 또는 Scala로 작성된 스크립트를 실행하며, 수 테라바이트 규모의 데이터를 처리할 수 있습니다.

- 대규모 배치 ETL 작업에 최적화되어 있습니다.
- DynamicFrame과 DataFrame을 모두 지원합니다.
- Glue Data Catalog와 연동하여 스키마 자동 감지가 가능합니다.
- Worker Type(G.1X, G.2X, G.025X)에 따라 성능과 비용을 조절할 수 있습니다.

#### 2. Python Shell Job

Apache Spark 없이 순수 Python 환경에서 실행되는 경량 Job입니다. 소규모 데이터 처리, API 호출, 파이프라인 제어 로직 등에 적합합니다.

- Spark 오버헤드가 없어 빠르게 시작됩니다.
- 1 DPU 또는 0.0625 DPU로 실행할 수 있어 비용이 매우 저렴합니다.
- pandas, boto3, requests 등 Python 라이브러리를 자유롭게 사용할 수 있습니다.
- 수 MB에서 수 GB 수준의 소규모 데이터 처리에 권장됩니다.

#### 3. Streaming ETL Job

Apache Spark Structured Streaming을 기반으로 실시간 스트리밍 데이터를 처리합니다.

- Amazon Kinesis Data Streams, Apache Kafka(MSK)와 연동됩니다.
- 마이크로 배치 방식으로 준실시간 처리를 수행합니다.
- 윈도우 기반 집계, 필터링, 변환 등을 지원합니다.
- 체크포인트를 통해 장애 복구가 가능합니다.

#### 4. Ray Job

비교적 최근 추가된 유형으로, Python 분산 컴퓨팅 프레임워크인 Ray를 기반으로 합니다.

- 머신러닝 워크로드, 고급 데이터 처리에 적합합니다.
- Python 네이티브 분산 처리가 가능합니다.
- TensorFlow, PyTorch 등 ML 프레임워크와 통합할 수 있습니다.

### Glue Job의 핵심 구성 요소

| 구성 요소 | 설명 |
|-----------|------|
| Script | PySpark, Python, 또는 Scala로 작성된 ETL 스크립트 |
| IAM Role | S3, Redshift, Data Catalog 등에 접근하기 위한 권한 |
| Worker Type | G.1X(4vCPU/16GB), G.2X(8vCPU/32GB), G.025X(2vCPU/4GB) 등 |
| Number of Workers | 병렬 처리 정도를 결정하는 Worker 수 |
| Job Bookmark | 증분 처리를 위한 상태 추적 기능 |
| Timeout | 최대 실행 시간 설정(기본 2880분) |
| Max Retries | 실패 시 자동 재시도 횟수(기본 0) |
| Glue Version | Spark 및 Python 엔진 버전(4.0, 3.0 등) |
| Connections | VPC 내 JDBC 소스 접근을 위한 연결 설정 |

## 아키텍처/동작 원리

AWS Glue Job의 실행 아키텍처는 다음과 같은 흐름으로 구성됩니다.

```text
[데이터 소스]          [AWS Glue Job]              [데이터 타겟]
 S3 / RDS /    -->   Spark 클러스터 (서버리스)  -->   S3 / Redshift /
 DynamoDB /          DynamicFrame 처리              RDS / ES
 Kinesis              변환 로직 실행
                         |
                    [Glue Data Catalog]
                    스키마 메타데이터 참조
```

### 실행 흐름

1. **Job 시작**: 수동, Trigger, Workflow, EventBridge, 또는 API/CLI를 통해 실행됩니다.
2. **리소스 프로비저닝**: 설정된 Worker Type과 수에 따라 Spark 클러스터가 자동 생성됩니다.
3. **데이터 읽기**: Data Catalog 또는 직접 지정한 소스에서 데이터를 DynamicFrame으로 읽어옵니다.
4. **변환 처리**: 사용자가 작성한 ETL 스크립트에 따라 데이터를 변환합니다.
5. **데이터 쓰기**: 변환된 데이터를 지정된 타겟에 저장합니다.
6. **리소스 해제**: 작업 완료 후 클러스터가 자동으로 종료됩니다.

### 실행 방식

Glue Job을 실행하는 방법은 다섯 가지가 있습니다.

- **수동 실행**: AWS Console에서 직접 Run 버튼을 클릭합니다.
- **Glue Trigger**: 시간 기반(Cron) 또는 이벤트 기반 트리거를 설정합니다.
- **Glue Workflow**: 여러 Job과 Crawler를 DAG(방향 비순환 그래프)로 연결하여 실행합니다.
- **Amazon EventBridge**: S3 이벤트 등 외부 이벤트에 반응하여 실행합니다.
- **API/CLI**: 프로그래밍 방식으로 실행합니다.

## 실전 활용

### Glue Job 생성 (AWS CLI)

```bash
# Spark ETL Job 생성
aws glue create-job \
  --name "my-etl-job" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --command '{
    "Name": "glueetl",
    "ScriptLocation": "s3://my-scripts-bucket/etl/my_script.py",
    "PythonVersion": "3"
  }' \
  --default-arguments '{
    "--job-bookmark-option": "job-bookmark-enable",
    "--TempDir": "s3://my-temp-bucket/temp/",
    "--enable-metrics": "true",
    "--enable-continuous-cloudwatch-log": "true"
  }' \
  --glue-version "4.0" \
  --number-of-workers 10 \
  --worker-type "G.1X" \
  --max-retries 1 \
  --timeout 120
```

```bash
# Job 실행
aws glue start-job-run \
  --job-name "my-etl-job" \
  --arguments '{
    "--input_path": "s3://my-bucket/input/2024/03/",
    "--output_path": "s3://my-bucket/output/2024/03/"
  }'
```

```bash
# Job 실행 상태 확인
aws glue get-job-run \
  --job-name "my-etl-job" \
  --run-id "jr_abc123def456"
```

```bash
# Job 목록 조회
aws glue get-jobs --max-results 10
```

### PySpark ETL 스크립트 예시

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

# 초기화
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'input_path', 'output_path'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 데이터 읽기 (S3에서 JSON 파일)
datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={
        "paths": [args['input_path']],
        "recurse": True
    },
    format="json",
    transformation_ctx="datasource"
)

# 데이터 변환 - 컬럼 매핑
mapped = ApplyMapping.apply(
    frame=datasource,
    mappings=[
        ("id", "string", "user_id", "string"),
        ("name", "string", "user_name", "string"),
        ("created_at", "string", "created_date", "timestamp"),
        ("amount", "string", "amount", "double")
    ],
    transformation_ctx="mapped"
)

# choice 타입 해결
resolved = ResolveChoice.apply(
    frame=mapped,
    choice="make_struct",
    transformation_ctx="resolved"
)

# null 값 제거
dropped = DropNullFields.apply(
    frame=resolved,
    transformation_ctx="dropped"
)

# 데이터 쓰기 (Parquet 형식으로 S3에 저장)
glueContext.write_dynamic_frame.from_options(
    frame=dropped,
    connection_type="s3",
    connection_options={
        "path": args['output_path'],
        "partitionKeys": ["created_date"]
    },
    format="parquet",
    transformation_ctx="output"
)

job.commit()
```

### Python Shell Job 예시

```python
import boto3
import pandas as pd
from io import StringIO

s3 = boto3.client('s3')

# S3에서 CSV 읽기
obj = s3.get_object(Bucket='my-bucket', Key='data/input.csv')
df = pd.read_csv(obj['Body'])

# 데이터 처리
df['processed_date'] = pd.to_datetime(df['date_str'])
df = df[df['status'] == 'active']
df['amount_usd'] = df['amount_krw'] / 1300

# 결과 저장
csv_buffer = StringIO()
df.to_csv(csv_buffer, index=False)
s3.put_object(
    Bucket='my-bucket',
    Key='data/output.csv',
    Body=csv_buffer.getvalue()
)
```

## 모범 사례 및 보안

### 성능 최적화

- **Worker Type 선택**: 메모리 집약적 작업에는 G.2X, 일반 작업에는 G.1X를 사용합니다. Python Shell Job은 소규모 작업에 G.025X로 비용을 절약합니다.
- **파티셔닝 활용**: 출력 데이터를 날짜, 리전 등으로 파티셔닝하면 후속 쿼리 성능이 향상됩니다.
- **Parquet 형식 사용**: 컬럼 기반 포맷인 Parquet으로 저장하면 스토리지 비용과 읽기 성능 모두 개선됩니다.
- **Job Bookmark 활용**: 전체 데이터를 매번 처리하는 대신 증분 처리를 통해 비용과 시간을 절약합니다.

### 보안 모범 사례

- **최소 권한 IAM Role**: Glue Job에 필요한 최소한의 S3, Redshift, Data Catalog 권한만 부여합니다.
- **VPC 내 실행**: 민감한 데이터베이스에 접근해야 하는 경우 VPC Connection을 통해 프라이빗 네트워크에서 실행합니다.
- **데이터 암호화**: S3 SSE, KMS 키를 활용하여 저장 데이터 및 전송 데이터를 암호화합니다.
- **CloudWatch 모니터링**: 실행 로그, 메트릭, 에러를 CloudWatch에서 모니터링합니다.
- **Security Configuration**: Glue Security Configuration을 생성하여 S3 암호화, CloudWatch 암호화, Job Bookmark 암호화를 일괄 설정합니다.

```bash
# Security Configuration 생성
aws glue create-security-configuration \
  --name "my-security-config" \
  --encryption-configuration '{
    "S3Encryption": [{
      "S3EncryptionMode": "SSE-KMS",
      "KmsKeyArn": "arn:aws:kms:ap-northeast-2:123456789012:key/my-key-id"
    }],
    "CloudWatchEncryption": {
      "CloudWatchEncryptionMode": "SSE-KMS",
      "KmsKeyArn": "arn:aws:kms:ap-northeast-2:123456789012:key/my-key-id"
    },
    "JobBookmarksEncryption": {
      "JobBookmarksEncryptionMode": "CSE-KMS",
      "KmsKeyArn": "arn:aws:kms:ap-northeast-2:123456789012:key/my-key-id"
    }
  }'
```

### 비용 최적화

- **Auto Scaling 활성화**: Glue 3.0 이상에서 Worker 수를 자동으로 조절합니다.
- **Flex Execution**: 비긴급 작업에는 Flex 실행 클래스를 사용하여 최대 34% 비용 절감이 가능합니다.
- **Timeout 설정**: 무한 실행을 방지하기 위해 적절한 Timeout을 설정합니다.
- **메트릭 기반 튜닝**: CloudWatch 메트릭에서 Worker 사용률을 확인하고 과도한 리소스를 줄입니다.

## 관련 서비스 비교

| 항목 | AWS Glue Job | Amazon EMR | AWS Step Functions | AWS Lambda |
|------|-------------|------------|-------------------|------------|
| 유형 | 서버리스 ETL | 관리형 클러스터 | 워크플로 오케스트레이션 | 서버리스 함수 |
| 엔진 | Spark/Python/Ray | Spark/Hive/Presto | 상태 머신 | 커스텀 런타임 |
| 데이터 규모 | TB급 | PB급 | - | MB~GB급 |
| 인프라 관리 | 불필요 | 클러스터 설정 필요 | 불필요 | 불필요 |
| 비용 모델 | DPU 시간당 | 인스턴스 시간당 | 상태 전환당 | 요청/실행 시간당 |
| Data Catalog 통합 | 네이티브 | 수동 연결 | 해당 없음 | 해당 없음 |
| 증분 처리 | Job Bookmark | 직접 구현 | 해당 없음 | 직접 구현 |
| 적합한 용도 | 정형 ETL | 대규모 분석 | 파이프라인 조합 | 이벤트 처리 |

### Glue Job vs Glue Workflow vs Glue Trigger

| 항목 | 역할 |
|------|------|
| Glue Job | 실제 ETL 로직을 실행하는 단위 |
| Glue Workflow | 여러 Job과 Crawler를 DAG로 묶어 실행하는 오케스트레이션 |
| Glue Trigger | Job을 시작하는 조건(시간/이벤트)을 정의 |

Glue Job은 단일 ETL 작업의 실행 단위이고, Workflow는 여러 Job을 의존성에 따라 순서대로 실행하는 파이프라인을 구성할 때 사용합니다. Trigger는 Job이나 Workflow를 언제 실행할지 결정하는 조건을 정의합니다.

## 요약

AWS Glue Job은 서버리스 ETL 처리의 핵심 실행 단위입니다. Spark ETL, Python Shell, Streaming, Ray 네 가지 유형을 제공하며, 데이터의 규모와 처리 방식에 따라 적절한 유형을 선택할 수 있습니다. DynamicFrame을 통한 유연한 스키마 처리, Job Bookmark를 통한 증분 처리, Data Catalog와의 네이티브 통합 등이 Glue Job의 핵심 강점입니다.

데이터 레이크 ETL, S3와 Redshift 간 데이터 적재, 대규모 배치 처리, 증분 데이터 파이프라인 등 다양한 시나리오에서 Glue Job을 활용할 수 있으며, 보안 설정과 비용 최적화를 통해 엔터프라이즈 수준의 안정적인 데이터 파이프라인을 구축할 수 있습니다.