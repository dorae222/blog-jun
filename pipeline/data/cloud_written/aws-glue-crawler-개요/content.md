# AWS Glue Crawler 개요 - 자동 스키마 탐색과 데이터 카탈로그 구축

## 개요

AWS Glue Crawler는 다양한 데이터 소스(S3, JDBC, DynamoDB 등)를 자동으로 스캔하여 데이터의 스키마를 추론하고, AWS Glue Data Catalog에 테이블 메타데이터를 등록하는 완전관리형 서비스입니다. 데이터 레이크에 저장된 수천 개의 파일을 수동으로 스키마 정의하는 번거로움 없이, Crawler가 자동으로 파일 형식을 감지하고 컬럼명, 데이터 타입, 파티션 구조를 추론합니다.

Crawler가 생성한 메타데이터는 Glue Data Catalog에 저장되어, Athena, Redshift Spectrum, EMR, Glue ETL Job 등 다양한 AWS 분석 서비스에서 공통적으로 활용됩니다. 이를 통해 데이터 분석가와 엔지니어는 데이터의 물리적 형식이나 저장 위치에 관계없이 일관된 메타데이터를 기반으로 쿼리와 분석을 수행할 수 있습니다.

## 핵심 기능

### 자동 스키마 추론

Crawler는 데이터 소스를 스캔하여 다음 정보를 자동으로 추론합니다.

| 추론 항목 | 설명 |
|-----------|------|
| 파일 형식 | CSV, JSON, Parquet, ORC, Avro, XML 등 |
| 컬럼명 | 헤더 또는 데이터 패턴 기반 추론 |
| 데이터 타입 | string, int, bigint, double, timestamp 등 |
| 파티션 구조 | S3 경로 패턴(year=2024/month=01/) 기반 |
| 압축 형식 | gzip, snappy, lzo, bzip2 등 |

### Classifier (분류기)

Classifier는 Crawler가 데이터 형식을 판별하는 규칙입니다. 내장 Classifier(JSON, CSV, Parquet 등)가 자동으로 적용되며, 비표준 형식의 데이터에 대해 Custom Classifier를 정의할 수 있습니다.

내장 Classifier 우선순위:
1. Custom Classifier (사용자 정의)
2. Apache Avro
3. Apache Parquet
4. Apache ORC
5. JSON
6. CSV
7. XML

### 스케줄 기반 실행

Crawler는 cron 표현식 기반 스케줄링을 지원합니다. 데이터가 주기적으로 적재되는 환경에서 스케줄을 설정하면, 새로운 파티션이나 스키마 변경을 자동으로 감지하고 카탈로그를 업데이트합니다.

### 스키마 변경 정책

| 정책 | 동작 |
|------|------|
| UPDATE_IN_DATABASE | 기존 테이블 정의를 새 스키마로 업데이트 |
| LOG | 스키마 변경을 감지하되, 카탈로그를 수정하지 않고 로그만 기록 |
| ADD_NEW_COLUMNS | 새 컬럼만 추가하고 기존 컬럼은 유지 |

## 아키텍처 및 동작 원리

Crawler의 내부 처리 흐름은 다음과 같습니다.

```
[Crawler 실행 시작]
      |
      v
[데이터 소스 접근]
      |  (S3 / JDBC / DynamoDB / Catalog)
      v
[파일/테이블 샘플링]
      |  (전체 스캔 또는 샘플링)
      v
[Classifier 적용]
      |  (파일 형식 판별)
      v
[스키마 추론]
      |  (컬럼명, 데이터 타입)
      v
[파티션 탐색]
      |  (S3 경로 패턴 분석)
      v
[스키마 변경 감지]
      |  (기존 카탈로그와 비교)
      v
[Data Catalog 업데이트]
      |  (테이블/파티션 생성 또는 수정)
      v
[Crawler 실행 완료]
```

### S3 파티션 탐색

S3 경로가 `s3://bucket/data/year=2024/month=01/day=15/` 형태로 구조화되어 있으면, Crawler는 자동으로 year, month, day를 파티션 키로 인식합니다. Hive 스타일(`key=value`) 뿐 아니라, 경로 깊이 기반 파티션도 지원합니다.

### Grouping 동작

Crawler는 유사한 스키마를 가진 S3 경로들을 하나의 테이블로 그룹화합니다. 예를 들어 `logs/2024/01/`, `logs/2024/02/` 경로의 파일들이 동일한 스키마를 가지면 하나의 테이블로 합쳐집니다. `TableGroupingPolicy`를 통해 이 동작을 제어할 수 있습니다.

## 실전 활용

### AWS CLI를 사용한 Crawler 생성 및 실행

```bash
# Crawler용 IAM 역할 확인
aws iam get-role --role-name AWSGlueServiceRole-Crawler \
    --query 'Role.Arn' --output text

# S3 데이터 소스를 대상으로 Crawler 생성
aws glue create-crawler \
    --name sales-data-crawler \
    --role arn:aws:iam::123456789012:role/AWSGlueServiceRole-Crawler \
    --database-name analytics_db \
    --targets '{
        "S3Targets": [
            {
                "Path": "s3://my-datalake/sales/",
                "Exclusions": ["**/temp/**", "**/staging/**"]
            }
        ]
    }' \
    --schema-change-policy '{
        "UpdateBehavior": "UPDATE_IN_DATABASE",
        "DeleteBehavior": "LOG"
    }' \
    --recrawl-policy '{"RecrawlBehavior": "CRAWL_NEW_FOLDERS_ONLY"}' \
    --configuration '{"Version": 1.0, "Grouping": {"TableGroupingPolicy": "CombineCompatibleSchemas"}}'

# Crawler 즉시 실행
aws glue start-crawler --name sales-data-crawler

# 실행 상태 확인
aws glue get-crawler \
    --name sales-data-crawler \
    --query '{Status:Crawler.State,LastRun:Crawler.LastCrawl.Status,Tables:Crawler.LastCrawl.LogGroup}'

# 스케줄 설정 (매일 새벽 2시 실행)
aws glue update-crawler \
    --name sales-data-crawler \
    --schedule 'cron(0 2 * * ? *)'

# Crawler가 생성한 테이블 확인
aws glue get-tables \
    --database-name analytics_db \
    --query 'TableList[].{Name:Name,Columns:StorageDescriptor.Columns|length(@),Partitions:PartitionKeys[].Name}' \
    --output table

# 특정 테이블의 파티션 목록 조회
aws glue get-partitions \
    --database-name analytics_db \
    --table-name sales \
    --query 'Partitions[].Values' \
    --output table
```

### JDBC 데이터 소스 크롤링

```bash
# Glue Connection 생성 (RDS/Aurora)
aws glue create-connection \
    --connection-input '{
        "Name": "rds-postgres-conn",
        "ConnectionType": "JDBC",
        "ConnectionProperties": {
            "JDBC_CONNECTION_URL": "jdbc:postgresql://mydb.cluster-xxx.ap-northeast-2.rds.amazonaws.com:5432/mydb",
            "USERNAME": "admin",
            "PASSWORD": "secret"
        },
        "PhysicalConnectionRequirements": {
            "SubnetId": "subnet-0abc123",
            "SecurityGroupIdList": ["sg-0abc123"],
            "AvailabilityZone": "ap-northeast-2a"
        }
    }'

# JDBC Crawler 생성
aws glue create-crawler \
    --name rds-schema-crawler \
    --role arn:aws:iam::123456789012:role/AWSGlueServiceRole-Crawler \
    --database-name rds_catalog \
    --targets '{
        "JdbcTargets": [{
            "ConnectionName": "rds-postgres-conn",
            "Path": "mydb/public/%",
            "Exclusions": ["mydb/public/temp_*"]
        }]
    }'
```

### Crawler 실행 이력 모니터링

```bash
# 최근 실행 이력 조회
aws glue get-crawler-metrics \
    --crawler-name-list sales-data-crawler \
    --query 'CrawlerMetricsList[].{Name:CrawlerName,Running:StillEstimating,TablesCreated:TablesCreated,TablesUpdated:TablesUpdated,MedianRuntime:MedianRuntimeSeconds}' \
    --output table
```



### DynamoDB 크롤링

Crawler는 DynamoDB 테이블도 스캔할 수 있습니다. DynamoDB의 스키마리스 특성상, Crawler가 테이블의 항목을 샘플링하여 가장 보편적인 속성 집합을 스키마로 추론합니다.

```bash
# DynamoDB Crawler 생성
aws glue create-crawler \
    --name dynamodb-crawler \
    --role arn:aws:iam::123456789012:role/AWSGlueServiceRole-Crawler \
    --database-name nosql_catalog \
    --targets '{
        "DynamoDBTargets": [{
            "Path": "my-dynamodb-table",
            "scanAll": false,
            "scanRate": 0.5
        }]
    }'
```

`scanRate`를 0.5로 설정하면 DynamoDB 테이블의 프로비저닝된 읽기 용량의 50%만 사용하여 프로덕션 영향을 최소화합니다.

### Delta Lake / Iceberg 테이블 크롤링

Glue Crawler는 Apache Hudi, Delta Lake, Apache Iceberg 같은 테이블 포맷도 지원합니다.

```bash
# Delta Lake Crawler 생성
aws glue create-crawler \
    --name delta-lake-crawler \
    --role arn:aws:iam::123456789012:role/AWSGlueServiceRole-Crawler \
    --database-name lakehouse_db \
    --targets '{
        "DeltaTargets": [{
            "DeltaTables": ["s3://my-datalake/delta/sales/"],
            "WriteManifest": true
        }]
    }'

# Iceberg Crawler 생성
aws glue create-crawler \
    --name iceberg-crawler \
    --role arn:aws:iam::123456789012:role/AWSGlueServiceRole-Crawler \
    --database-name lakehouse_db \
    --targets '{
        "IcebergTargets": [{
            "Paths": ["s3://my-datalake/iceberg/orders/"],
            "MaximumTraversalDepth": 10
        }]
    }'
```

### Crawler 실행 자동화 (EventBridge 연동)

S3에 새 파일이 업로드될 때 자동으로 Crawler를 실행하려면 EventBridge 규칙을 사용합니다.

```bash
# EventBridge 규칙 생성: S3 이벤트 -> Glue Crawler 시작
aws events put-rule \
    --name trigger-crawler-on-upload \
    --event-pattern '{
        "source": ["aws.s3"],
        "detail-type": ["Object Created"],
        "detail": {
            "bucket": {"name": ["my-datalake"]},
            "object": {"key": [{"prefix": "raw/sales/"}]}
        }
    }'

aws events put-targets \
    --rule trigger-crawler-on-upload \
    --targets '[{
        "Id": "GlueCrawler",
        "Arn": "arn:aws:glue:ap-northeast-2:123456789012:crawler/sales-data-crawler",
        "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeGlueRole"
    }]'
```

### Custom Classifier 작성

비표준 CSV 파일(구분자가 파이프 등)이나 특수한 형식의 데이터에 대해 Custom Classifier를 정의할 수 있습니다.

```bash
# CSV Custom Classifier (파이프 구분자)
aws glue create-classifier \
    --csv-classifier '{
        "Name": "pipe-delimited-csv",
        "Delimiter": "|",
        "QuoteSymbol": "\"",
        "ContainsHeader": "PRESENT",
        "Header": ["id", "name", "amount", "date"]
    }'

# Grok Custom Classifier (로그 파일)
aws glue create-classifier \
    --grok-classifier '{
        "Name": "apache-access-log",
        "Classification": "apache-log",
        "GrokPattern": "%{COMBINEDAPACHELOG}"
    }'

# Crawler에 Custom Classifier 적용
aws glue create-crawler \
    --name custom-csv-crawler \
    --role arn:aws:iam::123456789012:role/AWSGlueServiceRole-Crawler \
    --database-name analytics_db \
    --classifiers pipe-delimited-csv \
    --targets '{"S3Targets": [{"Path": "s3://my-bucket/pipe-data/"}]}'
```

## 모범 사례 및 보안

### 성능 최적화

- **RecrawlPolicy**: `CRAWL_NEW_FOLDERS_ONLY`를 설정하면 이전에 크롤링한 폴더를 건너뛰어 실행 시간을 단축합니다. 새로운 파티션만 추가되는 일반적인 데이터 레이크 시나리오에 적합합니다.
- **S3 Exclusions**: 임시 파일, 로그, 체크포인트 등 크롤링이 불필요한 경로를 제외하여 스캔 범위를 최소화합니다.
- **샘플링**: 대용량 데이터셋에서는 Crawler가 자동으로 샘플링을 수행합니다. 스키마가 일관된 데이터라면 이 동작이 효율적입니다.

### 비용 관리

- Crawler 실행 시간에 따라 DPU(Data Processing Unit) 비용이 발생합니다.
- 스케줄 빈도를 데이터 적재 주기에 맞추어 불필요한 크롤링을 방지합니다.
- 파티션만 추가되는 경우 `MSCK REPAIR TABLE` (Athena) 또는 `BatchCreatePartition` API가 Crawler보다 비용 효율적일 수 있습니다.

### 보안

- Crawler IAM 역할에 최소한의 S3/JDBC 접근 권한만 부여합니다.
- JDBC 연결 시 비밀번호를 Secrets Manager에 저장하고 참조합니다.
- Data Catalog에 Lake Formation 권한을 적용하여 테이블 접근을 제어합니다.
- VPC 내 데이터 소스(RDS, Redshift)에 접근할 때는 Glue Connection에 VPC 설정을 구성합니다.

## 관련 서비스 비교

| 항목 | Glue Crawler | MSCK REPAIR TABLE | Glue ETL CreateTable | Lake Formation Blueprints |
|------|-------------|-------------------|---------------------|-------------------------|
| 스키마 추론 | 자동 | 불가 (스키마 필요) | 수동 정의 | 자동 |
| 파티션 탐색 | 자동 | 자동 | 수동 | 자동 |
| 스케줄링 | 지원 | 미지원 (Athena 쿼리) | Glue Workflow | 지원 |
| 비용 | DPU 시간 | Athena 쿼리 비용 | ETL Job 비용 | DPU 시간 |
| 적합한 상황 | 초기 스키마 탐색 | 파티션만 추가 | 정확한 스키마 필요 시 | 데이터 레이크 자동화 |

## 요약

AWS Glue Crawler는 데이터 레이크와 데이터베이스의 스키마를 자동으로 탐색하여 Glue Data Catalog에 등록하는 핵심 서비스입니다. S3, JDBC, DynamoDB 등 다양한 데이터 소스를 지원하며, 파일 형식 감지, 컬럼 타입 추론, 파티션 구조 분석을 자동으로 수행합니다. Crawler가 생성한 메타데이터는 Athena, Redshift Spectrum, EMR 등 AWS 분석 서비스 전반에서 공통적으로 활용되어, 데이터 카탈로그의 중앙 허브 역할을 합니다. 스케줄 실행과 RecrawlPolicy를 적절히 설정하여 비용을 최적화하고, Lake Formation 연동으로 세밀한 접근 제어를 적용하는 것이 모범 사례입니다.