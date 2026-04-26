<!-- infographic-hero -->
![AWS Glue Job Bookmark 핵심 요약](figures/infographic.svg)

*Figure: AWS Glue Job Bookmark 한 장 요약 인포그래픽*

# AWS Glue Job Bookmark

## 개요

AWS Glue Job Bookmark는 Glue ETL 작업에서 이미 처리한 데이터를 기억해 다음 실행 시 새 데이터만 처리하도록 하는 증분 처리(Incremental Processing) 기능입니다. 데이터 레이크 환경에서 S3에 지속적으로 데이터가 누적되는 파이프라인을 운영할 때, Job Bookmark 없이는 매번 전체 데이터를 처리해야 합니다. 이는 불필요한 비용 증가, 처리 시간 증가, 중복 데이터 생성 등의 문제를 야기합니다.

Job Bookmark를 활성화하면 Glue가 각 실행 시 처리한 데이터의 메타데이터(경로, 파일명, 타임스탬프 등)를 내부적으로 저장합니다. 이후 실행에서는 이 Bookmark 상태를 참조하여 이미 처리된 데이터를 건너뛰고, 새로 추가된 데이터만 읽어서 처리합니다. 이는 대규모 배치 파이프라인의 운영 효율성을 크게 향상시키는 핵심 기능입니다.

## 핵심 기능

### Job Bookmark의 상태 관리

Job Bookmark는 세 가지 상태를 지원합니다.

| 상태 | 설명 | 사용 시나리오 |
|------|------|-------------|
| **Enable** | 증분 처리 활성화. 이전 실행 상태를 저장하고, 다음 실행 시 새 데이터만 처리 | 일반적인 증분 ETL 파이프라인 |
| **Disable** | Bookmark를 사용하지 않음. 매 실행 시 전체 데이터를 처리 | 전체 재처리가 필요한 경우 |
| **Pause** | 현재 Bookmark 상태를 유지하되 갱신하지 않음. 동일한 데이터 범위를 반복 처리 | 디버깅 및 테스트 시 |

### 데이터 소스별 Bookmark 지원

| 데이터 소스 | Bookmark 지원 | 추적 방식 |
|------------|-------------|----------|
| Amazon S3 | 지원 | 파일 경로, 수정 시간, 크기 기반 추적 |
| JDBC 소스(RDS, Redshift 등) | 지원 | Primary Key 또는 Watermark 컬럼 기반 추적 |
| DynamoDB | 제한적 지원 | 테이블 전체 스캔 방식으로 제한 |
| 스트리밍(Kinesis, Kafka) | 미지원 | 스트리밍은 별도 체크포인트 메커니즘 사용 |

### S3 소스의 Bookmark 동작

S3를 소스로 사용하는 경우 Job Bookmark는 다음 정보를 추적합니다.

- **파일 경로(Key)**: 처리된 파일의 S3 경로
- **수정 시간(LastModified)**: 파일의 마지막 수정 타임스탬프
- **파일 크기(Size)**: 파일의 바이트 크기

이 세 가지 정보의 조합으로 이미 처리된 파일을 식별하고, 새로 추가되거나 수정된 파일만 다음 실행에서 처리합니다.

### JDBC 소스의 Bookmark 동작

JDBC 소스에서는 두 가지 방식으로 증분 처리가 가능합니다.

- **Primary Key 기반**: 정렬 가능한 PK를 기반으로 마지막 처리된 값 이후의 레코드만 조회합니다.
- **Watermark 컬럼 기반**: `jobBookmarkKeys`와 `jobBookmarkKeysSortOrder` 옵션을 통해 사용자 지정 컬럼으로 추적합니다.

## 아키텍처/동작 원리

Job Bookmark의 내부 동작은 다음과 같은 단계로 이루어집니다.

```text
[1차 실행]
S3 버킷 스캔 --> 파일 A, B, C 발견
                  |
            파일 A, B, C 처리
                  |
            Bookmark 상태 저장
            (A, B, C의 메타데이터)

[2차 실행]
S3 버킷 스캔 --> 파일 A, B, C, D, E 발견
                  |
            Bookmark 비교
            (A, B, C는 이미 처리됨)
                  |
            파일 D, E만 처리
                  |
            Bookmark 상태 갱신
            (A, B, C, D, E의 메타데이터)
```

### transformation_ctx의 역할

Job Bookmark가 정확하게 동작하려면 `transformation_ctx` 파라미터가 필수입니다. 이 파라미터는 각 데이터 소스 읽기 작업에 고유 식별자를 부여하여, Glue가 어떤 소스의 상태를 추적해야 하는지 구별할 수 있게 합니다.

하나의 Job에서 여러 소스를 읽는 경우, 각 소스마다 서로 다른 `transformation_ctx`를 지정해야 합니다. 이를 누락하면 Bookmark가 올바르게 동작하지 않습니다.

## 실전 활용

### Job Bookmark 활성화 (AWS CLI)

```bash
# Job 생성 시 Bookmark 활성화
aws glue create-job \
  --name "incremental-etl-job" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --command '{
    "Name": "glueetl",
    "ScriptLocation": "s3://my-scripts/incremental_etl.py",
    "PythonVersion": "3"
  }' \
  --default-arguments '{
    "--job-bookmark-option": "job-bookmark-enable",
    "--TempDir": "s3://my-temp/temp/"
  }' \
  --glue-version "4.0" \
  --number-of-workers 5 \
  --worker-type "G.1X"
```

```bash
# Bookmark 상태 초기화 (전체 재처리가 필요한 경우)
aws glue reset-job-bookmark \
  --job-name "incremental-etl-job"
```

```bash
# Bookmark 상태 조회
aws glue get-job-bookmark \
  --job-name "incremental-etl-job"
```

```bash
# Job 실행 이력 조회
aws glue get-job-runs \
  --job-name "incremental-etl-job" \
  --max-results 5
```

### S3 증분 처리 PySpark 스크립트

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# transformation_ctx를 반드시 지정해야 Bookmark가 동작합니다
datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="s3",
    connection_options={
        "paths": ["s3://my-data-lake/raw/events/"],
        "recurse": True
    },
    format="json",
    transformation_ctx="datasource_events"  # 필수: Bookmark 추적 식별자
)

print(f"이번 실행에서 처리할 레코드 수: {datasource.count()}")

# 데이터 변환
mapped = ApplyMapping.apply(
    frame=datasource,
    mappings=[
        ("event_id", "string", "event_id", "string"),
        ("user_id", "string", "user_id", "string"),
        ("event_type", "string", "event_type", "string"),
        ("timestamp", "string", "event_time", "timestamp"),
        ("payload", "string", "payload", "string")
    ],
    transformation_ctx="mapped"
)

# Parquet으로 저장 (날짜 파티셔닝)
glueContext.write_dynamic_frame.from_options(
    frame=mapped,
    connection_type="s3",
    connection_options={
        "path": "s3://my-data-lake/processed/events/",
        "partitionKeys": ["event_type"]
    },
    format="parquet",
    transformation_ctx="output_events"  # 출력에도 ctx 지정 권장
)

# job.commit()이 호출되어야 Bookmark 상태가 갱신됩니다
job.commit()
```

### JDBC 소스 증분 처리 예시

```python
# JDBC 소스에서 Bookmark 기반 증분 읽기
datasource = glueContext.create_dynamic_frame.from_catalog(
    database="my_database",
    table_name="orders",
    transformation_ctx="jdbc_orders",
    additional_options={
        "jobBookmarkKeys": ["order_id"],
        "jobBookmarkKeysSortOrder": "asc"
    }
)
```

## 모범 사례 및 보안

### Bookmark 운영 모범 사례

- **transformation_ctx 항상 지정**: 모든 소스 읽기 및 출력 쓰기에 고유한 `transformation_ctx`를 지정합니다.
- **job.commit() 반드시 호출**: 스크립트 마지막에 `job.commit()`을 호출해야 Bookmark 상태가 갱신됩니다.
- **파티션 구조 활용**: S3 소스에 `year/month/day` 형태의 파티션 구조를 사용하면 Bookmark의 효율성이 향상됩니다.
- **파일 덮어쓰기 금지**: 같은 경로에 파일을 덮어쓰면 Bookmark가 변경을 감지하지 못할 수 있습니다. 새 파일은 항상 새 경로에 생성합니다.
- **정기적 모니터링**: CloudWatch 메트릭에서 처리 레코드 수를 확인하여 Bookmark가 정상 동작하는지 검증합니다.

### 트러블슈팅 가이드

| 증상 | 원인 | 해결 방법 |
|------|------|----------|
| Bookmark를 켰는데 전체 재처리됨 | transformation_ctx 누락 | 모든 소스/타겟에 transformation_ctx 추가 |
| 새 파일이 처리되지 않음 | 파일 덮어쓰기(같은 경로/이름) | 고유한 파일명 사용(UUID, 타임스탬프 활용) |
| 간헐적 중복 처리 | S3 최종 일관성 이슈 | S3 강력한 일관성 모델(2020년 이후 기본 적용) 확인 |
| Job 실패 후 재처리 안됨 | 실패한 실행의 Bookmark가 커밋됨 | `reset-job-bookmark` 후 재실행 |
| JDBC 소스에서 누락 발생 | PK가 정렬 불가능한 타입 | jobBookmarkKeys에 정렬 가능한 컬럼 지정 |

### 보안 고려사항

- **Bookmark 암호화**: Glue Security Configuration에서 Job Bookmark 암호화(CSE-KMS)를 활성화합니다.
- **IAM 권한**: Glue Job Role에 `glue:GetJobBookmark`, `glue:ResetJobBookmark` 권한을 적절히 부여합니다.
- **S3 접근 권한**: Bookmark가 정상 동작하려면 S3 객체의 메타데이터를 읽을 수 있는 `s3:GetObject`, `s3:ListBucket` 권한이 필요합니다.

```bash
# Bookmark 암호화가 포함된 Security Configuration 생성
aws glue create-security-configuration \
  --name "bookmark-encrypted-config" \
  --encryption-configuration '{
    "JobBookmarksEncryption": {
      "JobBookmarksEncryptionMode": "CSE-KMS",
      "KmsKeyArn": "arn:aws:kms:ap-northeast-2:123456789012:key/my-key-id"
    }
  }'
```

## 관련 서비스 비교

| 항목 | Glue Job Bookmark | 수동 증분 처리 | DynamoDB Streams | S3 Event Notification |
|------|-------------------|-------------|------------------|---------------------|
| 구현 난이도 | 매우 낮음 | 높음 | 중간 | 중간 |
| 운영 부담 | 낮음 | 높음 | 낮음 | 중간 |
| 유연성 | 중간 | 높음 | 낮음(DDB 한정) | 중간 |
| 정확성 | 높음(파일 단위) | 구현에 따라 다름 | 높음(레코드 단위) | 높음(이벤트 단위) |
| Glue 통합 | 네이티브 | 직접 구현 | Lambda 연동 필요 | Lambda/SQS 연동 필요 |
| 적합한 시나리오 | 배치 ETL 증분 처리 | 복잡한 커스텀 로직 | 실시간 변경 감지 | 파일 도착 기반 트리거 |

Glue Job Bookmark는 배치 ETL 파이프라인에서 가장 간편하게 증분 처리를 구현할 수 있는 방법입니다. 수동으로 마지막 처리 시점을 추적하는 로직을 구현할 필요 없이, 설정 한 줄로 증분 처리가 가능합니다.

## 요약

AWS Glue Job Bookmark는 ETL 파이프라인에서 이미 처리한 데이터를 자동으로 추적하여 증분 처리를 가능하게 하는 핵심 기능입니다. Enable, Disable, Pause 세 가지 상태를 지원하며, S3와 JDBC 소스에서 효과적으로 동작합니다. transformation_ctx 지정, job.commit() 호출, 파일 덮어쓰기 방지 등의 모범 사례를 준수하면 안정적인 증분 ETL 파이프라인을 운영할 수 있습니다. 비용 절감, 처리 시간 단축, 중복 데이터 방지라는 세 가지 핵심 이점을 제공하는 Glue Job Bookmark는 대규모 데이터 파이프라인의 필수 기능입니다.