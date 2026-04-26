<!-- infographic-hero -->
![Amazon Athena Workgroup vs Data Catalog 정리 핵심 요약](figures/infographic.svg)

*Figure: Amazon Athena Workgroup vs Data Catalog 정리 한 장 요약 인포그래픽*

# Amazon Athena Workgroup vs Data Catalog 정리

## 개요

Amazon Athena를 사용하다 보면 Workgroup과 Data Catalog이라는 두 가지 핵심 개념을 반드시 마주하게 됩니다. 이 두 개념은 자주 혼동되지만, 완전히 다른 역할을 수행합니다.

- **Workgroup**: 쿼리 실행 환경을 관리합니다. 누가, 어떤 조건으로 쿼리를 실행하고, 결과를 어디에 저장하며, 비용을 어떻게 제한할지를 결정합니다.
- **Data Catalog**: 데이터 메타데이터를 관리합니다. 어떤 데이터베이스와 테이블이 있고, 각 테이블의 스키마와 파티션 정보, 데이터 위치가 무엇인지를 관리합니다.

비유하자면, Workgroup은 사무실의 "회의실 예약 시스템"이고, Data Catalog은 "도서관 카탈로그"입니다. 회의실에서 어떤 책을 읽을지(Data Catalog)와 회의실의 사용 규칙(Workgroup)은 별개의 관심사입니다.

이 글에서는 두 개념의 차이점, 세부 설정 방법, 그리고 실전에서 어떻게 조합하여 활용하는지를 깊이 있게 다루겠습니다.

## 핵심 기능

### Workgroup의 핵심 기능

Workgroup은 Athena 쿼리 실행 환경을 논리적으로 분리하는 단위입니다.

**1. 쿼리 결과 위치 관리**: 각 Workgroup은 고유한 S3 쿼리 결과 저장 위치를 가질 수 있습니다. `EnforceWorkGroupConfiguration`을 활성화하면 사용자가 이 위치를 변경할 수 없습니다.

**2. 비용 제어**: 쿼리당 스캔 데이터 양 제한(`BytesScannedCutoffPerQuery`)을 설정하여 비용 폭증을 방지할 수 있습니다.

**3. CloudWatch 메트릭 발행**: Workgroup별로 쿼리 수, 실행 시간, 스캔 데이터 양 등의 메트릭을 CloudWatch에 발행할 수 있습니다.

**4. 쿼리 이력 관리**: 각 Workgroup의 쿼리 이력이 별도로 관리되므로, 팀별 또는 프로젝트별 쿼리 사용 현황을 파악할 수 있습니다.

**5. IAM 기반 접근 제어**: Workgroup 수준에서 IAM 정책을 적용하여, 특정 사용자나 역할에 대한 접근을 제어할 수 있습니다.

**6. 태그 기반 비용 할당**: Workgroup에 태그를 부착하여 AWS Cost Explorer에서 팀별 비용을 추적할 수 있습니다.

**7. 엔진 버전 지정**: Workgroup별로 Athena 엔진 버전(v2, v3)을 선택할 수 있습니다.

### Data Catalog의 핵심 기능

Data Catalog은 AWS Glue의 구성요소로, Athena가 사용하는 메타스토어 역할을 합니다.

**1. 데이터베이스 관리**: 논리적 데이터베이스를 정의하여 테이블을 그룹화합니다.

**2. 테이블 메타데이터**: 테이블의 스키마(컬럼명, 데이터 타입), 데이터 위치(S3 경로), 파일 포맷, SerDe 정보를 관리합니다.

**3. 파티션 관리**: 테이블의 파티션 정보를 저장하여 Athena가 파티션 프루닝을 수행할 수 있도록 합니다.

**4. 크로스 서비스 공유**: Glue Data Catalog은 Athena뿐만 아니라 Redshift Spectrum, EMR, Glue ETL 등 여러 AWS 서비스에서 공유됩니다.

**5. 크로스 계정 접근**: Resource-based 정책을 통해 다른 AWS 계정과 Data Catalog을 공유할 수 있습니다.

**6. 크롤러 연동**: Glue 크롤러가 S3 데이터를 스캔하여 자동으로 테이블 스키마를 탐지하고 Data Catalog에 등록합니다.

**7. 스키마 버전 관리**: Schema Registry를 통해 테이블 스키마의 버전 이력을 관리할 수 있습니다.

## 아키텍처/동작 원리

### Workgroup의 동작 원리

Athena에서 쿼리를 실행할 때 Workgroup이 관여하는 방식은 다음과 같습니다.

1. 사용자가 쿼리를 제출할 때 Workgroup을 지정합니다 (지정하지 않으면 "primary" Workgroup 사용).
2. Athena는 해당 Workgroup의 설정을 확인합니다.
3. `EnforceWorkGroupConfiguration`이 활성화되어 있으면, 사용자의 개별 설정을 무시하고 Workgroup 설정을 강제 적용합니다.
4. `BytesScannedCutoffPerQuery`가 설정되어 있으면, 스캔 중 이 한도를 초과하는 쿼리를 자동으로 중단합니다.
5. 쿼리 결과를 Workgroup에 지정된 S3 위치에 저장합니다.
6. `PublishCloudWatchMetricsEnabled`가 활성화되어 있으면 CloudWatch에 메트릭을 발행합니다.

### Data Catalog의 동작 원리

Athena가 쿼리를 실행할 때 Data Catalog이 관여하는 방식은 다음과 같습니다.

1. 사용자가 SQL에서 테이블을 참조합니다 (예: `analytics_db.logs`).
2. Athena 엔진이 Data Catalog에서 `analytics_db` 데이터베이스의 `logs` 테이블 메타데이터를 조회합니다.
3. 메타데이터에서 테이블의 S3 위치, 스키마, 파일 포맷, SerDe, 파티션 정보를 가져옵니다.
4. 쿼리의 WHERE 절과 파티션 정보를 비교하여 파티션 프루닝을 수행합니다.
5. 해당하는 S3 경로의 데이터를 스캔합니다.

### 두 개념의 관계

Workgroup과 Data Catalog은 독립적으로 동작합니다. 하나의 Workgroup에서 여러 Data Catalog의 테이블을 쿼리할 수 있고, 하나의 Data Catalog의 테이블을 여러 Workgroup에서 쿼리할 수 있습니다.

```
[사용자] --> [Workgroup: 쿼리 실행 환경]
                  |
                  +--> [Data Catalog A: AwsDataCatalog] --> [S3 데이터]
                  |
                  +--> [Data Catalog B: dynamodb_catalog] --> [DynamoDB]
                  |
                  +--> [Data Catalog C: rds_catalog] --> [RDS]
```

## 실전 활용

### Workgroup 생성 및 관리 (AWS CLI)

```bash
# 팀별 Workgroup 생성
aws athena create-work-group \
  --name "data-engineering-team" \
  --configuration '{
    "ResultConfiguration": {
      "OutputLocation": "s3://athena-results-bucket/data-engineering/",
      "EncryptionConfiguration": {
        "EncryptionOption": "SSE_S3"
      }
    },
    "EnforceWorkGroupConfiguration": true,
    "PublishCloudWatchMetricsEnabled": true,
    "BytesScannedCutoffPerQuery": 10737418240,
    "EngineVersion": {
      "SelectedEngineVersion": "Athena engine version 3"
    }
  }' \
  --description "Data Engineering team workgroup - 10GB scan limit" \
  --tags Key=Team,Value=DataEngineering Key=Environment,Value=Production

# 분석팀 Workgroup 생성 (더 엄격한 제한)
aws athena create-work-group \
  --name "analytics-team" \
  --configuration '{
    "ResultConfiguration": {
      "OutputLocation": "s3://athena-results-bucket/analytics/",
      "EncryptionConfiguration": {
        "EncryptionOption": "SSE_KMS",
        "KmsKey": "arn:aws:kms:ap-northeast-2:123456789012:key/12345678-1234-1234-1234-123456789012"
      }
    },
    "EnforceWorkGroupConfiguration": true,
    "PublishCloudWatchMetricsEnabled": true,
    "BytesScannedCutoffPerQuery": 1073741824
  }' \
  --description "Analytics team workgroup - 1GB scan limit"

# Workgroup 목록 조회
aws athena list-work-groups

# Workgroup 상세 정보 조회
aws athena get-work-group --work-group "data-engineering-team"

# Workgroup 설정 업데이트
aws athena update-work-group \
  --work-group "analytics-team" \
  --configuration-updates '{
    "BytesScannedCutoffPerQuery": 5368709120
  }' \
  --description "Analytics team workgroup - 5GB scan limit (updated)"

# 특정 Workgroup에서 쿼리 실행
aws athena start-query-execution \
  --query-string "SELECT COUNT(*) FROM analytics_db.logs WHERE year=2024" \
  --work-group "data-engineering-team"
```

### Data Catalog 관리 (AWS CLI)

```bash
# Glue 데이터베이스 생성
aws glue create-database \
  --database-input '{
    "Name": "analytics_db",
    "Description": "Analytics database for log analysis",
    "Parameters": {
      "classification": "analytics"
    }
  }'

# Glue 테이블 생성
aws glue create-table \
  --database-name "analytics_db" \
  --table-input '{
    "Name": "access_logs",
    "Description": "Web access logs",
    "StorageDescriptor": {
      "Columns": [
        {"Name": "request_id", "Type": "string"},
        {"Name": "timestamp", "Type": "timestamp"},
        {"Name": "method", "Type": "string"},
        {"Name": "path", "Type": "string"},
        {"Name": "status_code", "Type": "int"},
        {"Name": "response_time", "Type": "double"}
      ],
      "Location": "s3://my-data-bucket/access-logs/",
      "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
      "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
      "SerdeInfo": {
        "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
      }
    },
    "PartitionKeys": [
      {"Name": "year", "Type": "int"},
      {"Name": "month", "Type": "int"},
      {"Name": "day", "Type": "int"}
    ],
    "TableType": "EXTERNAL_TABLE"
  }'

# 테이블 목록 조회
aws glue get-tables --database-name "analytics_db"

# 테이블 상세 정보 조회
aws glue get-table --database-name "analytics_db" --name "access_logs"

# 파티션 추가
aws glue batch-create-partition \
  --database-name "analytics_db" \
  --table-name "access_logs" \
  --partition-input-list '[
    {
      "Values": ["2024", "1", "15"],
      "StorageDescriptor": {
        "Location": "s3://my-data-bucket/access-logs/year=2024/month=1/day=15/",
        "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
        "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
        "SerdeInfo": {
          "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
        },
        "Columns": [
          {"Name": "request_id", "Type": "string"},
          {"Name": "timestamp", "Type": "timestamp"},
          {"Name": "method", "Type": "string"},
          {"Name": "path", "Type": "string"},
          {"Name": "status_code", "Type": "int"},
          {"Name": "response_time", "Type": "double"}
        ]
      }
    }
  ]'

# Federated 카탈로그 등록 확인
aws athena list-data-catalogs
```

### IAM 정책: Workgroup 기반 접근 제어

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSpecificWorkgroup",
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StopQueryExecution",
        "athena:ListQueryExecutions"
      ],
      "Resource": [
        "arn:aws:athena:ap-northeast-2:123456789012:workgroup/analytics-team"
      ]
    },
    {
      "Sid": "AllowGlueReadAccess",
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetDatabases",
        "glue:GetTable",
        "glue:GetTables",
        "glue:GetPartition",
        "glue:GetPartitions",
        "glue:BatchGetPartition"
      ],
      "Resource": [
        "arn:aws:glue:ap-northeast-2:123456789012:catalog",
        "arn:aws:glue:ap-northeast-2:123456789012:database/analytics_db",
        "arn:aws:glue:ap-northeast-2:123456789012:table/analytics_db/*"
      ]
    },
    {
      "Sid": "AllowS3DataAccess",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-data-bucket",
        "arn:aws:s3:::my-data-bucket/*"
      ]
    },
    {
      "Sid": "AllowS3ResultsAccess",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::athena-results-bucket/analytics/*"
    }
  ]
}
```

### IAM 정책: Data Catalog 기반 접근 제어 (Lake Formation)

Lake Formation을 사용하면 컬럼 수준의 세밀한 접근 제어가 가능합니다.

```bash
# Lake Formation 권한 부여 - 특정 테이블의 특정 컬럼만 접근 허용
aws lakeformation grant-permissions \
  --principal DataLakePrincipalIdentifier=arn:aws:iam::123456789012:role/AnalystRole \
  --resource '{
    "TableWithColumns": {
      "DatabaseName": "analytics_db",
      "Name": "user_events",
      "ColumnNames": ["event_type", "timestamp", "page_url"]
    }
  }' \
  --permissions '["SELECT"]'
```

### 크로스 계정 Data Catalog 공유

```bash
# Glue Data Catalog 리소스 정책 설정
aws glue put-resource-policy \
  --policy-in-json '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "AWS": "arn:aws:iam::987654321098:root"
        },
        "Action": [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions"
        ],
        "Resource": [
          "arn:aws:glue:ap-northeast-2:123456789012:catalog",
          "arn:aws:glue:ap-northeast-2:123456789012:database/shared_db",
          "arn:aws:glue:ap-northeast-2:123456789012:table/shared_db/*"
        ]
      }
    ]
  }'
```

### 실전 조합 전략

대규모 조직에서 Workgroup과 Data Catalog을 조합하는 전략 예시입니다.

```
[조직 구조]
  +-- Data Platform Team
  |     Workgroup: data-platform (scan limit: 100GB)
  |     Databases: raw_data, staging_data, curated_data
  |
  +-- Analytics Team
  |     Workgroup: analytics (scan limit: 10GB)
  |     Databases: curated_data (읽기 전용)
  |
  +-- ML Team
  |     Workgroup: ml-team (scan limit: 50GB)
  |     Databases: curated_data, ml_features
  |
  +-- Business Team
        Workgroup: business (scan limit: 1GB)
        Databases: curated_data (특정 테이블만)
```

이 구조에서 각 팀은 자신의 Workgroup에서만 쿼리를 실행할 수 있고, IAM 정책과 Lake Formation으로 접근 가능한 데이터베이스와 테이블이 제한됩니다.

## 모범 사례/보안

### Workgroup 운영 모범 사례

**1. 용도별 Workgroup 분리**: 팀별, 환경별(개발/스테이징/프로덕션), 또는 비용 센터별로 Workgroup을 분리합니다.

**2. EnforceWorkGroupConfiguration 활성화**: 사용자가 Workgroup 설정을 우회하지 못하도록 반드시 활성화합니다. 이 설정이 비활성화되어 있으면 사용자가 쿼리 결과 위치를 임의로 변경할 수 있어 데이터 유출 위험이 있습니다.

**3. 스캔 제한 설정**: BytesScannedCutoffPerQuery를 반드시 설정하여, 실수로 인한 대규모 스캔을 방지합니다.

**4. CloudWatch 메트릭 활성화**: 모든 Workgroup에서 CloudWatch 메트릭을 활성화하여 쿼리 패턴과 비용을 모니터링합니다.

**5. 태그 기반 비용 추적**: Workgroup에 팀, 프로젝트, 비용 센터 태그를 부착하여 비용 할당을 추적합니다.

### Data Catalog 운영 모범 사례

**1. 명명 규칙 일관성**: 데이터베이스와 테이블에 일관된 명명 규칙을 적용합니다. 예를 들어 `{layer}_{domain}` 형식 (raw_clickstream, curated_user_events)을 사용합니다.

**2. 파티션 관리 자동화**: Glue 크롤러 또는 MSCK REPAIR TABLE을 스케줄링하여 새로운 파티션을 자동으로 등록합니다.

**3. 테이블 설명 문서화**: 테이블과 컬럼에 설명(Description)을 반드시 기록하여 데이터 카탈로그의 가치를 높입니다.

**4. Lake Formation 연동**: 프로덕션 환경에서는 Lake Formation을 통한 세밀한 접근 제어를 적용합니다.

### 보안 모범 사례

- Workgroup의 쿼리 결과는 반드시 암호화 설정을 활성화합니다 (SSE-S3 또는 SSE-KMS).
- Data Catalog 접근은 IAM 정책 또는 Lake Formation으로 제어하되, 두 방식을 혼용하지 않는 것이 관리에 유리합니다.
- 크로스 계정 공유 시 리소스 정책의 범위를 최소화합니다.
- Workgroup별 쿼리 이력을 정기적으로 감사합니다.

## 관련 서비스 비교

### Workgroup vs Data Catalog 핵심 비교표

| 항목 | Workgroup | Data Catalog |
|------|-----------|-------------|
| 관리 대상 | 쿼리 실행 환경 | 데이터 메타데이터 |
| 소속 서비스 | Amazon Athena | AWS Glue |
| 주요 설정 | 결과 위치, 스캔 제한, 암호화 | 데이터베이스, 테이블, 파티션, 스키마 |
| 접근 제어 | IAM (Workgroup ARN 기반) | IAM + Lake Formation (컬럼 수준) |
| 비용 관리 | 직접 (스캔 제한, 태그) | 간접 (파티셔닝, 포맷 최적화) |
| 공유 범위 | 단일 계정 내 | 크로스 계정 가능 |
| 모니터링 | CloudWatch 메트릭 | Glue 크롤러 로그 |
| 엔진 버전 | Workgroup별 지정 가능 | 해당 없음 |

### Athena Workgroup vs Redshift WLM

Redshift의 WLM(Workload Management)은 쿼리 큐를 관리하고, 동시성과 메모리 할당을 제어합니다. Athena Workgroup은 비용과 결과 관리에 초점이 맞추어져 있어, Redshift WLM보다 단순하지만 서버리스 환경에 최적화되어 있습니다.

### Glue Data Catalog vs Apache Hive Metastore

Glue Data Catalog은 관리형 Hive Metastore의 대안입니다. EMR에서 Hive Metastore 대신 Glue Data Catalog을 사용하면, Athena와 Redshift Spectrum에서도 동일한 메타데이터를 공유할 수 있다는 장점이 있습니다.

## 요약

Amazon Athena의 Workgroup과 Data Catalog은 서로 다른 관심사를 다루는 독립적인 구성요소입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **Workgroup은 "실행 환경"**: 쿼리 결과 위치, 비용 제한, 암호화, CloudWatch 메트릭 등 쿼리 실행에 관한 모든 설정을 관리합니다.
- **Data Catalog은 "메타데이터"**: 데이터베이스, 테이블, 스키마, 파티션, S3 위치 등 데이터에 관한 모든 정보를 관리합니다.
- **독립적 관계**: 하나의 Workgroup에서 여러 Catalog의 테이블을 쿼리할 수 있고, 그 반대도 가능합니다.
- **Workgroup 핵심 설정**: EnforceWorkGroupConfiguration과 BytesScannedCutoffPerQuery는 반드시 활성화/설정해야 합니다.
- **Data Catalog 핵심 활용**: 파티션 관리 자동화와 Lake Formation 연동이 운영 효율성의 핵심입니다.
- **실전 전략**: 팀별 Workgroup 분리 + IAM/Lake Formation 기반 Data Catalog 접근 제어 조합이 가장 효과적입니다.