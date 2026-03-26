## 개요

AWS Lake Formation은 안전한 데이터 레이크를 며칠이 아닌 몇 시간 만에 구축하고 관리할 수 있도록 도와주는 관리형 서비스입니다. 기존에 데이터 레이크를 구축하려면 S3 버킷 설정, IAM 정책 관리, Glue Crawler 설정, 데이터 암호화, 접근 제어 등 수많은 단계를 수동으로 구성해야 했습니다.

Lake Formation은 이러한 복잡한 과정을 중앙 집중식으로 관리할 수 있는 단일 인터페이스를 제공합니다. 특히 **열(Column) 수준, 행(Row) 수준, 셀(Cell) 수준의 세밀한 접근 제어**를 지원하여, 대규모 조직에서 다양한 팀과 사용자가 같은 데이터를 서로 다른 권한으로 안전하게 활용할 수 있습니다.

본 글에서는 Lake Formation의 핵심 개념부터 실전 구성, 보안 모범 사례까지 상세하게 다루겠습니다.

## 핵심 기능

### 1. 데이터 레이크 등록 및 관리

Lake Formation에서 데이터 레이크를 구성하려면 먼저 S3 위치를 등록해야 합니다.

```bash
# S3 데이터 레이크 위치 등록
aws lakeformation register-resource \
  --resource-arn "arn:aws:s3:::my-data-lake-bucket" \
  --use-service-linked-role

# 등록된 리소스 확인
aws lakeformation list-resources
```

데이터 레이크 위치를 등록하면 Lake Formation이 해당 S3 경로에 대한 접근을 중앙에서 관리합니다. `--use-service-linked-role` 옵션을 사용하면 Lake Formation 서비스 연결 역할이 해당 S3 위치에 대한 접근을 관리합니다.

### 2. Data Catalog 통합

Lake Formation은 AWS Glue Data Catalog를 기반으로 메타데이터를 관리합니다.

```bash
# 데이터베이스 생성
aws glue create-database \
  --database-input '{
    "Name": "analytics_db",
    "Description": "분석용 데이터베이스",
    "LocationUri": "s3://my-data-lake-bucket/analytics/"
  }'

# Lake Formation에서 데이터베이스 권한 부여
aws lakeformation grant-permissions \
  --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::123456789012:role/DataAnalystRole"}' \
  --resource '{"Database": {"Name": "analytics_db"}}' \
  --permissions '["DESCRIBE", "CREATE_TABLE"]'
```

### 3. 세밀한 접근 제어 (Fine-Grained Access Control)

Lake Formation의 가장 강력한 기능은 열, 행, 셀 수준의 접근 제어입니다.

**열 수준 접근 제어:**

```bash
# 특정 열만 접근 허용
aws lakeformation grant-permissions \
  --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::123456789012:role/MarketingAnalyst"}' \
  --resource '{
    "TableWithColumns": {
      "DatabaseName": "analytics_db",
      "Name": "customer_table",
      "ColumnNames": ["customer_id", "region", "signup_date", "purchase_count"]
    }
  }' \
  --permissions '["SELECT"]'
```

위 예시에서 MarketingAnalyst 역할은 customer_table의 4개 열에만 접근할 수 있으며, 이메일, 전화번호 등 민감한 열에는 접근할 수 없습니다.

**행 수준 접근 제어 (Data Filters):**

```bash
# 데이터 필터 생성 - 특정 리전 데이터만 접근 허용
aws lakeformation create-data-cells-filter \
  --table-data '{
    "TableCatalogId": "123456789012",
    "DatabaseName": "analytics_db",
    "TableName": "customer_table",
    "Name": "korea-region-filter",
    "RowFilter": {
      "FilterExpression": "region = '\''KR'\''" 
    },
    "ColumnNames": ["customer_id", "region", "signup_date", "purchase_count"]
  }'

# 데이터 필터를 적용한 권한 부여
aws lakeformation grant-permissions \
  --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::123456789012:role/KoreaTeamAnalyst"}' \
  --resource '{
    "DataCellsFilter": {
      "TableCatalogId": "123456789012",
      "DatabaseName": "analytics_db",
      "TableName": "customer_table",
      "Name": "korea-region-filter"
    }
  }' \
  --permissions '["SELECT"]'
```

### 4. 태그 기반 접근 제어 (LF-TBAC)

Lake Formation Tag-Based Access Control은 태그를 활용하여 대규모 데이터 레이크의 접근 제어를 간소화합니다.

```bash
# LF-Tag 생성
aws lakeformation create-lf-tag \
  --tag-key "sensitivity" \
  --tag-values '["public", "internal", "confidential", "restricted"]'

aws lakeformation create-lf-tag \
  --tag-key "department" \
  --tag-values '["engineering", "marketing", "finance", "hr"]'

# 테이블에 LF-Tag 할당
aws lakeformation add-lf-tags-to-resource \
  --resource '{"Table": {"DatabaseName": "analytics_db", "Name": "revenue_table"}}' \
  --lf-tags '[{"TagKey": "sensitivity", "TagValues": ["confidential"]}, {"TagKey": "department", "TagValues": ["finance"]}]'

# 태그 기반 접근 권한 부여
aws lakeformation grant-permissions \
  --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::123456789012:role/FinanceTeamRole"}' \
  --resource '{
    "LFTagPolicy": {
      "ResourceType": "TABLE",
      "Expression": [
        {"TagKey": "department", "TagValues": ["finance"]},
        {"TagKey": "sensitivity", "TagValues": ["public", "internal", "confidential"]}
      ]
    }
  }' \
  --permissions '["SELECT", "DESCRIBE"]'
```

이 방식을 사용하면 새로운 테이블이 추가될 때 적절한 태그만 부여하면 기존 권한 정책이 자동으로 적용되므로, 관리 부담이 크게 줄어듭니다.

### 5. 데이터 수집 (Blueprints)

Lake Formation은 다양한 데이터 소스로부터 데이터를 수집하는 Blueprint를 제공합니다.

```bash
# 사용 가능한 Blueprint 목록 조회
aws lakeformation list-blueprints

# RDS에서 데이터 레이크로 수집하는 Blueprint 실행
aws glue start-blueprint-run \
  --blueprint-name "lakeformation-rds-to-datalake" \
  --role-arn "arn:aws:iam::123456789012:role/LakeFormationWorkflowRole" \
  --parameters '{
    "source_database": "production_db",
    "target_database": "analytics_db",
    "datalake_location": "s3://my-data-lake-bucket/ingested/"
  }'
```

## 아키텍처/동작 원리

### Lake Formation 아키텍처 개요

```
[데이터 소스]
  ├── Amazon RDS
  ├── Amazon S3
  ├── On-premises DB
  └── SaaS Applications
       |
       v
[Lake Formation]
  ├── Data Ingestion (Blueprints/Glue Jobs)
  ├── Data Catalog (Glue Data Catalog)
  ├── Security & Access Control
  │    ├── LF-TBAC (태그 기반)
  │    ├── Column-level Security
  │    ├── Row-level Security  
  │    └── Cell-level Security
  └── Data Location Registration
       |
       v
[S3 Data Lake]
  ├── Raw Zone
  ├── Curated Zone
  └── Analytics Zone
       |
       v
[분석 서비스 (소비자)]
  ├── Amazon Athena
  ├── Amazon Redshift Spectrum
  ├── Amazon EMR
  └── AWS Glue ETL
```

### 권한 모델의 동작 원리

Lake Formation은 기존 IAM 기반 접근 제어를 보완하는 별도의 권한 레이어를 추가합니다. 데이터에 접근하려면 다음 두 가지 조건이 모두 충족되어야 합니다.

1. **IAM 권한**: 해당 서비스(Athena, Redshift 등)에 대한 IAM 권한
2. **Lake Formation 권한**: 해당 데이터(데이터베이스, 테이블, 열)에 대한 Lake Formation 권한

이 이중 레이어 구조 덕분에 IAM 정책을 단순하게 유지하면서도 세밀한 데이터 접근 제어가 가능합니다.

### Super 권한과 IAMAllowedPrincipals

Lake Formation을 처음 설정할 때 주의해야 할 점이 있습니다. 기본적으로 `IAMAllowedPrincipals`라는 그룹에 모든 데이터베이스와 테이블에 대한 Super 권한이 부여되어 있습니다. 이는 기존 IAM 기반 접근 제어와의 하위 호환성을 위한 것이지만, Lake Formation의 세밀한 접근 제어를 활용하려면 이 기본 권한을 제거해야 합니다.

```bash
# IAMAllowedPrincipals의 기본 권한 제거
aws lakeformation revoke-permissions \
  --principal '{"DataLakePrincipalIdentifier": "IAM_ALLOWED_PRINCIPALS"}' \
  --resource '{"Database": {"Name": "analytics_db"}}' \
  --permissions '["ALL"]'

# Data Lake 설정에서 기본 권한 비활성화
aws lakeformation put-data-lake-settings \
  --data-lake-settings '{
    "DataLakeAdmins": [
      {"DataLakePrincipalIdentifier": "arn:aws:iam::123456789012:role/DataLakeAdmin"}
    ],
    "CreateDatabaseDefaultPermissions": [],
    "CreateTableDefaultPermissions": []
  }'
```

## 실전 활용

### 사례 1: 멀티 팀 데이터 레이크 구축

여러 팀이 같은 데이터 레이크를 사용하되, 각 팀은 자신의 업무에 필요한 데이터에만 접근할 수 있도록 구성합니다.

```bash
# 1. Data Lake Admin 설정
aws lakeformation put-data-lake-settings \
  --data-lake-settings '{
    "DataLakeAdmins": [
      {"DataLakePrincipalIdentifier": "arn:aws:iam::123456789012:role/DataPlatformAdmin"}
    ],
    "CreateDatabaseDefaultPermissions": [],
    "CreateTableDefaultPermissions": []
  }'

# 2. 부서별 태그 생성
aws lakeformation create-lf-tag \
  --tag-key "access_level" \
  --tag-values '["all", "analytics", "engineering", "finance"]'

# 3. 데이터에 태그 할당
aws lakeformation add-lf-tags-to-resource \
  --resource '{"Table": {"DatabaseName": "shared_db", "Name": "user_activity"}}' \
  --lf-tags '[{"TagKey": "access_level", "TagValues": ["all"]}]'

aws lakeformation add-lf-tags-to-resource \
  --resource '{"Table": {"DatabaseName": "shared_db", "Name": "financial_metrics"}}' \
  --lf-tags '[{"TagKey": "access_level", "TagValues": ["finance"]}]'

# 4. 팀별 접근 권한 부여
aws lakeformation grant-permissions \
  --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::123456789012:role/AnalyticsTeamRole"}' \
  --resource '{
    "LFTagPolicy": {
      "ResourceType": "TABLE",
      "Expression": [{"TagKey": "access_level", "TagValues": ["all", "analytics"]}]
    }
  }' \
  --permissions '["SELECT", "DESCRIBE"]'
```

### 사례 2: 크로스 계정 데이터 공유

```bash
# 다른 AWS 계정에 데이터베이스 접근 권한 부여
aws lakeformation grant-permissions \
  --principal '{"DataLakePrincipalIdentifier": "987654321098"}' \
  --resource '{"Database": {"Name": "shared_analytics"}}' \
  --permissions '["DESCRIBE"]'

# 특정 테이블의 읽기 권한 부여
aws lakeformation grant-permissions \
  --principal '{"DataLakePrincipalIdentifier": "987654321098"}' \
  --resource '{"Table": {"DatabaseName": "shared_analytics", "Name": "aggregated_metrics"}}' \
  --permissions '["SELECT", "DESCRIBE"]' \
  --permissions-with-grant-option '["SELECT", "DESCRIBE"]'
```

### 사례 3: Governed Tables 활용

Lake Formation Governed Tables는 ACID 트랜잭션을 지원하여 데이터 레이크에서도 데이터 일관성을 보장합니다.

```bash
# Governed Table 생성
aws glue create-table \
  --database-name "analytics_db" \
  --table-input '{
    "Name": "governed_transactions",
    "StorageDescriptor": {
      "Columns": [
        {"Name": "transaction_id", "Type": "string"},
        {"Name": "amount", "Type": "decimal(10,2)"},
        {"Name": "timestamp", "Type": "timestamp"}
      ],
      "Location": "s3://my-data-lake-bucket/governed/transactions/",
      "InputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
      "OutputFormat": "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
      "SerdeInfo": {
        "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
      }
    },
    "TableType": "GOVERNED"
  }'
```

### 권한 조회 및 감사

```bash
# 특정 보안 주체의 권한 조회
aws lakeformation list-permissions \
  --principal '{"DataLakePrincipalIdentifier": "arn:aws:iam::123456789012:role/AnalyticsTeamRole"}'

# 특정 리소스에 대한 모든 권한 조회
aws lakeformation list-permissions \
  --resource '{"Table": {"DatabaseName": "analytics_db", "Name": "customer_table"}}'

# LF-Tag 목록 조회
aws lakeformation list-lf-tags
```

## 모범 사례/보안

### 1. 최소 권한 원칙 적용

- IAMAllowedPrincipals의 기본 Super 권한을 반드시 제거합니다.
- 데이터베이스 레벨이 아닌 테이블, 열 레벨에서 권한을 부여합니다.
- `GRANT_WITH_OPTION`은 반드시 필요한 경우에만 사용합니다.

### 2. 태그 기반 접근 제어 우선 활용

- 리소스가 수백, 수천 개로 늘어나면 개별 권한 관리는 비현실적입니다.
- LF-TBAC를 사용하면 태그만 올바르게 관리하면 권한이 자동으로 적용됩니다.
- 태그 키와 값의 네이밍 컨벤션을 조직 차원에서 정의합니다.

### 3. 데이터 분류 체계 수립

```bash
# 데이터 민감도 분류 태그
aws lakeformation create-lf-tag \
  --tag-key "data_classification" \
  --tag-values '["public", "internal", "confidential", "highly_confidential"]'

# PII 포함 여부 태그
aws lakeformation create-lf-tag \
  --tag-key "contains_pii" \
  --tag-values '["yes", "no"]'
```

### 4. 감사 및 모니터링

- CloudTrail에서 Lake Formation API 호출을 모니터링합니다.
- AWS Config 규칙을 설정하여 권한 변경을 추적합니다.
- 주기적으로 `list-permissions`를 실행하여 불필요한 권한을 정리합니다.

### 5. 암호화 설정

- S3 버킷에 SSE-S3 또는 SSE-KMS 암호화를 반드시 적용합니다.
- Lake Formation 등록 시 KMS 키를 지정하여 데이터를 암호화합니다.
- 전송 중 암호화(TLS)는 AWS 서비스 간 통신에서 기본 적용됩니다.

## 관련 서비스 비교

| 항목 | Lake Formation | Glue Data Catalog 단독 | S3 + IAM 직접 관리 |
|------|---------------|----------------------|-------------------|
| 접근 제어 수준 | 열/행/셀 수준 | 데이터베이스/테이블 수준 | 버킷/접두사 수준 |
| 관리 복잡도 | 중간 (중앙 관리) | 낮음 | 높음 (분산 관리) |
| 크로스 계정 공유 | 내장 지원 | 제한적 | S3 버킷 정책 필요 |
| 태그 기반 접근 | LF-TBAC 지원 | 미지원 | IAM 태그 조건 |
| ACID 트랜잭션 | Governed Tables | 미지원 | 미지원 |
| 감사 추적 | CloudTrail 통합 | CloudTrail 통합 | S3 액세스 로그 |
| 비용 | 무료 (연동 서비스만 과금) | 무료 | 무료 |
| 적합한 규모 | 중대규모 조직 | 소규모 팀 | 단일 팀/프로젝트 |

## 요약

AWS Lake Formation은 데이터 레이크의 구축, 보안, 관리를 중앙에서 통합적으로 수행할 수 있는 서비스입니다. 핵심 내용을 정리하면 다음과 같습니다.

- **중앙 집중식 보안**: IAM과 별도로 Lake Formation 권한 레이어를 추가하여 세밀한 접근 제어를 구현합니다.
- **Fine-Grained Access Control**: 열, 행, 셀 수준의 접근 제어로 민감한 데이터를 보호합니다.
- **LF-TBAC**: 태그 기반 접근 제어로 대규모 데이터 레이크의 권한 관리를 자동화합니다.
- **크로스 계정 공유**: 다른 AWS 계정에 안전하게 데이터를 공유할 수 있습니다.
- **Glue Data Catalog 통합**: 기존 Glue 기반 메타데이터를 그대로 활용하면서 보안을 강화합니다.
- **무료 서비스**: Lake Formation 자체는 무료이며, 연동 서비스(S3, Glue, Athena 등)의 비용만 발생합니다.
- **주의사항**: IAMAllowedPrincipals 기본 권한 제거, 데이터 분류 체계 수립, 정기적 권한 감사가 필수적입니다.

Lake Formation은 데이터 거버넌스를 중요시하는 조직에서 반드시 도입을 검토해야 하는 서비스입니다.