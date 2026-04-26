<!-- infographic-hero -->
![AWS Glue Data Catalog 핵심 요약](figures/infographic.svg)

*Figure: AWS Glue Data Catalog 한 장 요약 인포그래픽*

# AWS Glue Data Catalog

## 개요

AWS Glue Data Catalog은 AWS의 중앙 집중식 메타데이터 저장소(Centralized Metadata Repository)입니다. S3, RDS, Redshift, DynamoDB 등 다양한 데이터 소스의 테이블 정의, 스키마 정보, 파티션 메타데이터를 하나의 카탈로그로 통합 관리합니다.

Apache Hive Metastore와 호환되는 인터페이스를 제공하며, Amazon Athena, Amazon Redshift Spectrum, Amazon EMR, AWS Glue ETL 등 다양한 AWS 분석 서비스에서 공유 메타데이터 저장소로 활용됩니다. 즉, Data Catalog에 테이블을 한 번 등록하면 여러 분석 서비스에서 동일한 메타데이터를 참조하여 데이터에 접근할 수 있습니다.

Data Catalog은 서버리스 서비스로 별도의 인프라 관리가 필요 없으며, 자동으로 스케일링됩니다. 리전당 최대 100만 개의 테이블을 저장할 수 있으며, 각 테이블은 최대 1,000만 개의 파티션을 가질 수 있습니다.

## 핵심 기능

### 1. 데이터베이스(Database)와 테이블(Table)

Data Catalog의 기본 구조는 데이터베이스와 테이블의 계층적 구조입니다. 데이터베이스는 테이블의 논리적 그룹이며, 테이블은 데이터의 스키마와 위치 정보를 담고 있습니다.

```bash
# 데이터베이스 생성
aws glue create-database \
  --database-input '{
    "Name": "analytics_db",
    "Description": "분석용 데이터베이스",
    "LocationUri": "s3://my-data-lake/analytics/",
    "Parameters": {
      "CreatedBy": "data-engineering-team"
    }
  }'
```

```bash
# 테이블 생성 (S3에 저장된 Parquet 데이터)
aws glue create-table \
  --database-name "analytics_db" \
  --table-input '{
    "Name": "user_events",
    "Description": "사용자 이벤트 로그 테이블",
    "StorageDescriptor": {
      "Columns": [
        {"Name": "user_id", "Type": "string", "Comment": "사용자 고유 ID"},
        {"Name": "event_type", "Type": "string", "Comment": "이벤트 유형"},
        {"Name": "event_timestamp", "Type": "timestamp", "Comment": "이벤트 발생 시각"},
        {"Name": "properties", "Type": "map<string,string>", "Comment": "이벤트 속성"}
      ],
      "Location": "s3://my-data-lake/analytics/user_events/",
      "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
      "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
      "SerdeInfo": {
        "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
      }
    },
    "PartitionKeys": [
      {"Name": "year", "Type": "string"},
      {"Name": "month", "Type": "string"},
      {"Name": "day", "Type": "string"}
    ],
    "TableType": "EXTERNAL_TABLE",
    "Parameters": {
      "classification": "parquet",
      "has_encrypted_data": "false"
    }
  }'
```

```bash
# 테이블 목록 조회
aws glue get-tables --database-name "analytics_db" --max-results 20
```

### 2. 크롤러(Crawler)

크롤러는 Data Catalog의 핵심 자동화 기능입니다. 지정된 데이터 소스를 스캔하여 스키마를 자동으로 추론하고, 테이블 메타데이터를 생성하거나 업데이트합니다.

```bash
# S3 크롤러 생성
aws glue create-crawler \
  --name "user-events-crawler" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --database-name "analytics_db" \
  --targets '{
    "S3Targets": [
      {
        "Path": "s3://my-data-lake/analytics/user_events/",
        "Exclusions": ["**.tmp", "**_temporary/**"]
      }
    ]
  }' \
  --schema-change-policy '{
    "UpdateBehavior": "UPDATE_IN_DATABASE",
    "DeleteBehavior": "LOG"
  }' \
  --recrawl-policy '{"RecrawlBehavior": "CRAWL_NEW_FOLDERS_ONLY"}' \
  --configuration '{"Version": 1.0, "Grouping": {"TableGroupingPolicy": "CombineCompatibleSchemas"}}'
```

```bash
# 크롤러 실행
aws glue start-crawler --name "user-events-crawler"
```

```bash
# 크롤러 상태 확인
aws glue get-crawler --name "user-events-crawler" --query 'Crawler.{State:State,LastCrawl:LastCrawl}'
```

크롤러의 주요 설정 옵션은 다음과 같습니다.

- **RecrawlPolicy**: `CRAWL_EVERYTHING`(전체 재스캔), `CRAWL_NEW_FOLDERS_ONLY`(새 폴더만), `CRAWL_EVENT_MODE`(S3 이벤트 기반)
- **SchemaChangePolicy**: 스키마 변경 시 동작 정의 (업데이트, 로깅, 삭제)
- **TableGroupingPolicy**: 호환 가능한 스키마를 하나의 테이블로 그룹화
- **Classifiers**: 커스텀 분류기를 통한 데이터 형식 식별

### 3. 분류기(Classifier)

크롤러가 데이터 형식을 자동으로 식별하지 못하는 경우, 커스텀 분류기를 정의할 수 있습니다.

```bash
# Grok 패턴 기반 커스텀 분류기 생성
aws glue create-classifier \
  --grok-classifier '{
    "Classification": "custom-access-log",
    "Name": "access-log-classifier",
    "GrokPattern": "%{IP:client_ip} %{USER:ident} %{USER:auth} \\[%{HTTPDATE:timestamp}\\] \"%{WORD:method} %{URIPATHPARAM:request} HTTP/%{NUMBER:httpversion}\" %{NUMBER:status} %{NUMBER:bytes}"
  }'
```

```bash
# CSV 분류기 생성
aws glue create-classifier \
  --csv-classifier '{
    "Name": "pipe-delimited-csv",
    "Delimiter": "|",
    "QuoteSymbol": "\"",
    "ContainsHeader": "PRESENT",
    "Header": ["id", "name", "email", "created_at"]
  }'
```

### 4. 파티션(Partition) 관리

대규모 데이터셋에서 쿼리 성능을 최적화하는 핵심 요소가 파티셔닝입니다. Data Catalog은 파티션 메타데이터를 관리하며, 파티션 프루닝(Partition Pruning)을 통해 불필요한 데이터 스캔을 줄여줍니다.

```bash
# 파티션 수동 추가
aws glue batch-create-partition \
  --database-name "analytics_db" \
  --table-name "user_events" \
  --partition-input-list '[
    {
      "Values": ["2024", "01", "15"],
      "StorageDescriptor": {
        "Columns": [
          {"Name": "user_id", "Type": "string"},
          {"Name": "event_type", "Type": "string"},
          {"Name": "event_timestamp", "Type": "timestamp"},
          {"Name": "properties", "Type": "map<string,string>"}
        ],
        "Location": "s3://my-data-lake/analytics/user_events/year=2024/month=01/day=15/",
        "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
        "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
        "SerdeInfo": {
          "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
        }
      }
    }
  ]'
```

```bash
# 파티션 목록 조회
aws glue get-partitions \
  --database-name "analytics_db" \
  --table-name "user_events" \
  --expression "year='2024' AND month='01'" \
  --max-results 31
```

### 5. 파티션 인덱스(Partition Index)

파티션 수가 수십만 개 이상인 테이블에서는 파티션 인덱스를 생성하여 파티션 필터링 성능을 대폭 향상시킬 수 있습니다.

```bash
# 파티션 인덱스 생성
aws glue create-partition-index \
  --database-name "analytics_db" \
  --table-name "user_events" \
  --partition-index '{
    "Keys": ["year", "month"],
    "IndexName": "year-month-index"
  }'
```

### 6. 스키마 레지스트리(Schema Registry)

Glue Schema Registry는 Avro, JSON Schema, Protobuf 스키마를 중앙에서 관리하고 버전 관리할 수 있는 기능입니다. 특히 Kafka, Kinesis Data Streams와 같은 스트리밍 데이터 소스의 스키마 관리에 유용합니다.

```bash
# 스키마 레지스트리 생성
aws glue create-registry \
  --registry-name "streaming-schemas" \
  --description "스트리밍 데이터 스키마 레지스트리"
```

```bash
# Avro 스키마 등록
aws glue create-schema \
  --registry-id '{"RegistryName": "streaming-schemas"}' \
  --schema-name "user-event-schema" \
  --data-format "AVRO" \
  --compatibility "BACKWARD" \
  --schema-definition '{
    "type": "record",
    "name": "UserEvent",
    "namespace": "com.example.analytics",
    "fields": [
      {"name": "user_id", "type": "string"},
      {"name": "event_type", "type": "string"},
      {"name": "timestamp", "type": "long"},
      {"name": "properties", "type": {"type": "map", "values": "string"}}
    ]
  }'
```

호환성 모드는 다음과 같은 옵션을 제공합니다.

- **NONE**: 호환성 검사 없음
- **BACKWARD**: 새 스키마로 이전 데이터 읽기 가능
- **FORWARD**: 이전 스키마로 새 데이터 읽기 가능
- **FULL**: BACKWARD + FORWARD
- **BACKWARD_ALL/FORWARD_ALL/FULL_ALL**: 모든 이전 버전과의 호환성 보장

## 아키텍처/동작 원리

### Data Catalog의 위치와 역할

Data Catalog은 AWS 데이터 분석 생태계의 중심에 위치합니다.

```
                        [AWS Glue Data Catalog]
                               |
              +----------------+----------------+
              |                |                |
        [Athena]          [Redshift         [EMR]
              |            Spectrum]           |
              |                |                |
              +-------+--------+-------+--------+
                      |                |
                   [S3 Data Lake]   [RDS/Redshift]

크롤러 동작 흐름:
[S3/JDBC 소스] --> [Glue Crawler] --> [Data Catalog]
                       |                   |
                  스키마 추론          테이블 메타데이터
                  파티션 탐지          파티션 정보
                  형식 분류            분류 정보
```

### 크롤러의 내부 동작

크롤러가 실행되면 다음과 같은 단계를 거칩니다.

1. **소스 탐색**: 지정된 S3 경로나 JDBC 소스를 탐색합니다.
2. **형식 분류**: 내장 분류기와 커스텀 분류기를 순서대로 적용하여 데이터 형식을 식별합니다.
3. **스키마 추론**: 데이터 샘플을 읽어 컬럼명, 데이터 타입을 추론합니다.
4. **그룹화**: 호환 가능한 스키마를 가진 파일들을 하나의 테이블로 그룹화합니다.
5. **파티션 탐지**: Hive 스타일 파티셔닝(`key=value/`) 또는 S3 경로 패턴에서 파티션을 탐지합니다.
6. **카탈로그 업데이트**: 기존 테이블과 비교하여 새로 생성, 업데이트, 또는 삭제합니다.

### 메타데이터 동기화

Data Catalog의 메타데이터와 실제 데이터 간의 동기화는 크롤러를 통해 이루어집니다. 하지만 실시간 동기화는 아니므로, 크롤러 실행 주기에 따라 메타데이터가 최신 상태가 아닐 수 있습니다.

S3 이벤트 기반 크롤링(`CRAWL_EVENT_MODE`)을 활용하면 새 데이터가 추가될 때 자동으로 메타데이터를 업데이트할 수 있습니다.

```bash
# S3 이벤트 기반 크롤러 설정
aws glue create-crawler \
  --name "event-driven-crawler" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --database-name "analytics_db" \
  --targets '{"S3Targets": [{"Path": "s3://my-data-lake/events/", "EventQueueArn": "arn:aws:sqs:ap-northeast-2:123456789012:glue-crawler-events"}]}' \
  --recrawl-policy '{"RecrawlBehavior": "CRAWL_EVENT_MODE"}'
```

## 실전 활용

### 사례 1: 멀티 서비스 데이터 레이크 구축

Data Catalog을 중심으로 Athena, Redshift Spectrum, EMR이 동일한 메타데이터를 공유하는 데이터 레이크를 구축합니다.

```bash
# 1단계: 데이터 레이크 데이터베이스 생성
aws glue create-database \
  --database-input '{"Name": "data_lake", "Description": "중앙 데이터 레이크"}'

# 2단계: 크롤러로 기존 S3 데이터 카탈로깅
aws glue create-crawler \
  --name "data-lake-crawler" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --database-name "data_lake" \
  --targets '{
    "S3Targets": [
      {"Path": "s3://my-data-lake/sales/"},
      {"Path": "s3://my-data-lake/customers/"},
      {"Path": "s3://my-data-lake/products/"}
    ]
  }' \
  --table-prefix "dl_" \
  --configuration '{"Version": 1.0, "CrawlerOutput": {"Partitions": {"AddOrUpdateBehavior": "InheritFromTable"}}}'

# 3단계: 크롤러 실행
aws glue start-crawler --name "data-lake-crawler"
```

크롤러 실행 후 생성된 테이블은 Athena에서 바로 쿼리할 수 있습니다.

```bash
# Athena에서 Data Catalog 테이블 쿼리
aws athena start-query-execution \
  --query-string "SELECT * FROM data_lake.dl_sales WHERE year='2024' LIMIT 10" \
  --query-execution-context '{"Database": "data_lake", "Catalog": "AwsDataCatalog"}' \
  --result-configuration '{"OutputLocation": "s3://my-query-results/athena/"}'
```

### 사례 2: 크로스 계정 Data Catalog 공유

AWS RAM(Resource Access Manager) 또는 Lake Formation을 활용하여 여러 AWS 계정에서 동일한 Data Catalog을 공유할 수 있습니다.

```bash
# Lake Formation을 통한 크로스 계정 테이블 권한 부여
aws lakeformation grant-permissions \
  --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::987654321098:role/AnalystRole"}' \
  --resource '{"Table": {"DatabaseName": "data_lake", "Name": "dl_sales", "CatalogId": "123456789012"}}' \
  --permissions '["SELECT", "DESCRIBE"]'
```

### 사례 3: JDBC 소스 크롤링

RDS나 Redshift의 스키마 정보를 Data Catalog으로 가져올 수 있습니다.

```bash
# JDBC 연결 생성
aws glue create-connection \
  --connection-input '{
    "Name": "rds-postgres-conn",
    "ConnectionType": "JDBC",
    "ConnectionProperties": {
      "JDBC_CONNECTION_URL": "jdbc:postgresql://mydb.cluster-xxx.ap-northeast-2.rds.amazonaws.com:5432/analytics",
      "USERNAME": "admin",
      "PASSWORD": "your-password"
    },
    "PhysicalConnectionRequirements": {
      "SubnetId": "subnet-0123456789abcdef0",
      "SecurityGroupIdList": ["sg-0123456789abcdef0"],
      "AvailabilityZone": "ap-northeast-2a"
    }
  }'

# JDBC 크롤러 생성
aws glue create-crawler \
  --name "rds-schema-crawler" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --database-name "rds_mirror" \
  --targets '{"JdbcTargets": [{"ConnectionName": "rds-postgres-conn", "Path": "analytics/%"}]}'
```

### 사례 4: 자동 파티션 관리 스크립트

크롤러 대신 직접 파티션을 관리하는 방법입니다. ETL 잡이 새 파티션에 데이터를 쓴 후 즉시 파티션을 등록합니다.

```python
import boto3
from datetime import datetime

def register_partition(database, table, year, month, day, s3_location):
    """Data Catalog에 새 파티션을 등록합니다."""
    glue = boto3.client('glue')
    
    # 기존 테이블 정보 조회
    table_info = glue.get_table(DatabaseName=database, Name=table)
    storage_descriptor = table_info['Table']['StorageDescriptor'].copy()
    storage_descriptor['Location'] = s3_location
    
    try:
        glue.create_partition(
            DatabaseName=database,
            TableName=table,
            PartitionInput={
                'Values': [str(year), str(month).zfill(2), str(day).zfill(2)],
                'StorageDescriptor': storage_descriptor
            }
        )
        print(f"파티션 등록 완료: {year}/{month}/{day}")
    except glue.exceptions.AlreadyExistsException:
        # 이미 존재하면 업데이트
        glue.update_partition(
            DatabaseName=database,
            TableName=table,
            PartitionValueList=[str(year), str(month).zfill(2), str(day).zfill(2)],
            PartitionInput={
                'Values': [str(year), str(month).zfill(2), str(day).zfill(2)],
                'StorageDescriptor': storage_descriptor
            }
        )
        print(f"파티션 업데이트 완료: {year}/{month}/{day}")

# 사용 예시
today = datetime.now()
register_partition(
    database='analytics_db',
    table='user_events',
    year=today.year,
    month=today.month,
    day=today.day,
    s3_location=f's3://my-data-lake/analytics/user_events/year={today.year}/month={today.month:02d}/day={today.day:02d}/'
)
```

## 모범 사례/보안

### 보안 모범 사례

1. **Lake Formation 통합**: Data Catalog의 세밀한 접근 제어를 위해 AWS Lake Formation을 활용합니다. 테이블, 컬럼, 행 수준의 접근 제어가 가능합니다.

```bash
# Lake Formation에서 컬럼 수준 접근 제어
aws lakeformation grant-permissions \
  --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::123456789012:role/AnalystRole"}' \
  --resource '{"TableWithColumns": {"DatabaseName": "analytics_db", "Name": "user_events", "ColumnNames": ["event_type", "event_timestamp"]}}' \
  --permissions '["SELECT"]'
```

2. **리소스 정책(Resource Policy)**: Data Catalog 수준에서 리소스 정책을 설정하여 크로스 계정 접근을 제어합니다.

```bash
# Data Catalog 리소스 정책 설정
aws glue put-resource-policy \
  --policy-in-json '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"AWS": "arn:aws:iam::987654321098:root"},
        "Action": ["glue:GetDatabase", "glue:GetTable", "glue:GetPartitions"],
        "Resource": [
          "arn:aws:glue:ap-northeast-2:123456789012:catalog",
          "arn:aws:glue:ap-northeast-2:123456789012:database/analytics_db",
          "arn:aws:glue:ap-northeast-2:123456789012:table/analytics_db/*"
        ]
      }
    ]
  }'
```

3. **암호화 설정**: Data Catalog 메타데이터를 KMS로 암호화합니다.

```bash
# Data Catalog 암호화 설정
aws glue put-data-catalog-encryption-settings \
  --data-catalog-encryption-settings '{
    "EncryptionAtRest": {
      "CatalogEncryptionMode": "SSE-KMS",
      "SseAwsKmsKeyId": "arn:aws:kms:ap-northeast-2:123456789012:key/my-key-id"
    },
    "ConnectionPasswordEncryption": {
      "ReturnConnectionPasswordEncrypted": true,
      "AwsKmsKeyId": "arn:aws:kms:ap-northeast-2:123456789012:key/my-key-id"
    }
  }'
```

4. **JDBC 연결 비밀번호 관리**: JDBC 연결의 비밀번호는 AWS Secrets Manager를 통해 관리하는 것이 안전합니다.

### 운영 모범 사례

1. **테이블 접두사 활용**: 크롤러의 `--table-prefix` 옵션을 활용하여 소스별로 테이블을 구분합니다.

2. **크롤러 실행 최적화**: `CRAWL_NEW_FOLDERS_ONLY` 정책을 사용하여 불필요한 전체 스캔을 방지합니다.

3. **파티션 인덱스 활용**: 파티션이 많은 테이블에는 반드시 파티션 인덱스를 생성하여 쿼리 성능을 최적화합니다.

4. **스키마 변경 관리**: 크롤러의 `SchemaChangePolicy`를 적절히 설정하여 의도치 않은 스키마 변경을 방지합니다. 프로덕션 환경에서는 `LOG` 모드를 권장합니다.

5. **정기적 메타데이터 정리**: 사용하지 않는 테이블과 파티션을 정기적으로 정리하여 카탈로그를 깨끗하게 유지합니다.

```bash
# 오래된 파티션 정리 (90일 이전)
aws glue batch-delete-partition \
  --database-name "analytics_db" \
  --table-name "user_events" \
  --partitions-to-delete '[{"Values": ["2023", "01", "01"]}, {"Values": ["2023", "01", "02"]}]'
```

## 관련 서비스 비교

| 항목 | AWS Glue Data Catalog | Apache Hive Metastore | AWS Lake Formation |
|------|----------------------|----------------------|--------------------|
| 관리 방식 | 완전 관리형 | 자체 관리 (EMR/EC2) | 완전 관리형 |
| 확장성 | 자동 스케일링 | 수동 스케일링 | 자동 스케일링 |
| 접근 제어 | IAM 기반 | Ranger/Sentry | 세밀한 FGAC |
| 테이블 제한 | 리전당 100만 개 | 인스턴스 성능에 의존 | Data Catalog 기반 |
| 스키마 레지스트리 | 지원 | 미지원 | Data Catalog 기반 |
| 비용 | 요청당 과금 + 스토리지 | 인스턴스 비용 | Data Catalog 비용 포함 |
| Hive 호환 | 호환 | 네이티브 | 호환 |
| 크로스 계정 | 지원 | 제한적 | 기본 지원 |

**Data Catalog은 Lake Formation의 기반입니다.** Lake Formation은 Data Catalog 위에 세밀한 접근 제어(Fine-Grained Access Control), 데이터 필터링, 태그 기반 접근 제어 등의 기능을 추가한 서비스입니다. 새로운 데이터 레이크를 구축한다면 Lake Formation과 함께 사용하는 것을 권장합니다.

## 요약

AWS Glue Data Catalog은 AWS 데이터 레이크의 핵심 메타데이터 저장소입니다. 크롤러를 통한 자동 스키마 추론, 파티션 관리, 스키마 레지스트리 등의 기능을 제공하며, Athena, Redshift Spectrum, EMR 등 다양한 분석 서비스와 통합됩니다.

Hive Metastore 호환 인터페이스를 제공하므로 기존 Hive 기반 워크로드를 쉽게 마이그레이션할 수 있으며, Lake Formation과 함께 사용하면 세밀한 접근 제어까지 구현할 수 있습니다. 서버리스 아키텍처로 별도의 인프라 관리가 필요 없고, 리전당 최대 100만 개의 테이블을 지원하여 대규모 데이터 레이크 환경에서도 안정적으로 동작합니다.

효과적인 Data Catalog 운영을 위해서는 크롤러 실행 정책을 최적화하고, 파티션 인덱스를 활용하며, Lake Formation을 통한 보안 관리를 체계화하는 것이 중요합니다.