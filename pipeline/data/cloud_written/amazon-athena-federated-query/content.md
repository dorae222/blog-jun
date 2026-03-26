# Amazon Athena Federated Query

## 개요

Amazon Athena Federated Query는 Athena가 S3 이외의 다양한 데이터 소스에 대해 SQL 쿼리를 실행할 수 있도록 하는 기능입니다. 기존 Athena는 S3에 저장된 데이터만 분석할 수 있었지만, Federated Query를 사용하면 Amazon RDS, Amazon DynamoDB, Amazon Redshift, Amazon CloudWatch Logs, 온프레미스 데이터베이스 등 다양한 소스의 데이터를 단일 SQL 쿼리로 조합하여 분석할 수 있습니다.

이 기능은 데이터를 한 곳으로 이동(ETL)하지 않고도, 데이터가 있는 위치에서 직접 쿼리할 수 있게 해주는 "데이터 연합(Federation)" 개념을 구현한 것입니다. 이를 통해 데이터 이동에 따른 비용, 지연, 복잡성을 크게 줄일 수 있습니다.

### Federated Query가 필요한 상황

다음과 같은 상황에서 Federated Query가 특히 유용합니다.

- S3의 로그 데이터와 RDS의 사용자 정보를 조인하여 분석해야 하는 경우
- 여러 데이터 소스에 분산된 데이터를 하나의 대시보드로 통합해야 하는 경우
- ETL 파이프라인 구축 없이 빠르게 크로스 소스 분석을 수행해야 하는 경우
- DynamoDB의 실시간 데이터와 S3의 이력 데이터를 비교 분석해야 하는 경우

## 핵심 기능

### 데이터 소스 커넥터

Federated Query의 핵심은 데이터 소스 커넥터입니다. 각 커넥터는 AWS Lambda 함수로 구현되며, 특정 데이터 소스에 대한 연결, 메타데이터 조회, 데이터 읽기를 담당합니다.

AWS에서 공식적으로 제공하는 사전 구축 커넥터는 다음과 같습니다.

- **Amazon DynamoDB Connector**: DynamoDB 테이블을 SQL로 조회
- **Amazon RDS/JDBC Connector**: MySQL, PostgreSQL, SQL Server 등 JDBC 호환 데이터베이스
- **Amazon Redshift Connector**: Redshift 클러스터/서버리스
- **Amazon CloudWatch Logs Connector**: CloudWatch 로그 그룹
- **Amazon CloudWatch Metrics Connector**: CloudWatch 메트릭스
- **Amazon DocumentDB Connector**: DocumentDB 컬렉션
- **Amazon Neptune Connector**: Neptune 그래프 데이터베이스
- **Amazon Timestream Connector**: 시계열 데이터
- **Apache HBase Connector**: HBase on EMR
- **Redis Connector**: ElastiCache for Redis
- **Google BigQuery Connector**: 크로스 클라우드 쿼리
- **Snowflake Connector**: 크로스 플랫폼 쿼리

### Custom Connector 개발

AWS에서 제공하지 않는 데이터 소스에 대해서는 Athena Query Federation SDK를 사용하여 커스텀 커넥터를 개발할 수 있습니다. SDK는 Java로 제공되며, 다음 인터페이스를 구현해야 합니다.

- **MetadataHandler**: 카탈로그, 스키마, 테이블 목록과 테이블 스키마를 반환
- **RecordHandler**: 실제 데이터를 읽어 Apache Arrow 포맷으로 반환

### 조건 푸시다운 (Predicate Pushdown)

Federated Query는 WHERE 절의 조건을 데이터 소스로 푸시다운하여, 소스 수준에서 필터링을 수행합니다. 이를 통해 Lambda 함수가 전송해야 하는 데이터 양이 크게 줄어들어 성능이 향상됩니다.

### 병렬 처리 (Split)

Federated Query는 데이터를 여러 "Split"으로 분할하여 병렬로 읽어들입니다. 각 Split은 별도의 Lambda 호출로 처리되므로, 대량의 데이터도 효율적으로 처리할 수 있습니다.

## 아키텍처/동작 원리

### 전체 아키텍처

Federated Query의 동작 아키텍처는 다음과 같은 구성요소로 이루어져 있습니다.

1. **Athena 엔진**: 사용자의 SQL 쿼리를 파싱하고 실행 계획을 수립합니다.
2. **AWS Glue Data Catalog**: 페더레이션 카탈로그 등록을 포함한 메타데이터를 관리합니다.
3. **Lambda 데이터 소스 커넥터**: 각 데이터 소스에 대한 연결과 데이터 읽기를 수행합니다.
4. **Amazon S3 Spill Bucket**: Lambda 함수의 응답 크기가 제한(6MB)을 초과할 경우, 중간 결과를 S3에 임시 저장합니다.
5. **데이터 소스**: RDS, DynamoDB, Redshift 등 실제 데이터가 저장된 서비스입니다.

### 쿼리 실행 흐름

사용자가 Federated Query를 실행하면 다음과 같은 순서로 처리됩니다.

1. Athena 엔진이 SQL을 파싱하고, 어떤 데이터 소스가 관련되는지 파악합니다.
2. 각 데이터 소스의 Lambda 커넥터에 메타데이터 요청을 보냅니다 (GetTableLayout, GetSplits).
3. Lambda 커넥터가 데이터를 Split으로 분할하는 방법을 반환합니다.
4. Athena 엔진이 각 Split에 대해 Lambda 커넥터를 병렬 호출하여 데이터를 읽어옵니다 (ReadRecords).
5. Lambda 커넥터는 데이터를 Apache Arrow 포맷으로 변환하여 반환합니다.
6. 데이터가 Lambda 응답 크기 제한을 초과하면 S3 Spill Bucket에 저장합니다.
7. Athena 엔진이 모든 소스의 데이터를 조합하여 최종 쿼리 결과를 생성합니다.

### Lambda 커넥터 내부 구조

Lambda 커넥터는 내부적으로 두 가지 핸들러로 구성됩니다.

**MetadataHandler의 주요 메서드:**
- `doListSchemas()`: 사용 가능한 스키마(데이터베이스) 목록 반환
- `doListTables()`: 스키마 내의 테이블 목록 반환
- `doGetTable()`: 특정 테이블의 스키마 정보 반환
- `doGetTableLayout()`: 파티션 정보 반환
- `doGetSplits()`: 데이터를 병렬로 읽을 수 있는 Split 정보 반환

**RecordHandler의 주요 메서드:**
- `readWithConstraint()`: 특정 Split의 데이터를 조건 적용하여 읽기

### Spill 메커니즘

Lambda 함수의 응답 크기는 6MB로 제한되어 있습니다. Federated Query에서 처리하는 데이터가 이 제한을 초과하면, Lambda 커넥터는 데이터를 S3 Spill Bucket에 암호화하여 저장하고, 참조 정보만 응답으로 반환합니다. Athena 엔진은 이 참조를 통해 S3에서 데이터를 읽어옵니다.

Spill 데이터는 AES-GCM 256비트 암호화가 적용되며, 쿼리 완료 후 자동으로 정리됩니다.

## 실전 활용

### 커넥터 배포

AWS Serverless Application Repository에서 사전 구축 커넥터를 배포할 수 있습니다.

```bash
# DynamoDB 커넥터 배포 (SAR 사용)
aws serverlessrepo create-cloud-formation-change-set \
  --application-id arn:aws:serverlessrepo:us-east-1:292517598671:applications/AthenaDynamoDBConnector \
  --stack-name athena-dynamodb-connector \
  --capabilities CAPABILITY_IAM CAPABILITY_RESOURCE_POLICY \
  --parameter-overrides '[{"Name":"SpillBucket","Value":"my-athena-spill-bucket"},{"Name":"AthenaCatalogName","Value":"dynamodb_catalog"}]'
```

### 카탈로그 등록

커넥터 Lambda 함수를 배포한 후, Athena에서 데이터 카탈로그로 등록합니다.

```bash
# Athena에서 데이터 카탈로그 등록
aws athena create-data-catalog \
  --name dynamodb_catalog \
  --type LAMBDA \
  --parameters function=arn:aws:lambda:ap-northeast-2:123456789012:function:athena-dynamodb-connector

# 등록된 카탈로그 확인
aws athena list-data-catalogs
```

### DynamoDB 테이블 쿼리

DynamoDB에 저장된 데이터를 SQL로 직접 조회할 수 있습니다.

```sql
-- DynamoDB 카탈로그를 통한 직접 쿼리
SELECT
  user_id,
  user_name,
  email,
  created_at
FROM dynamodb_catalog.default.users
WHERE user_id = '12345';

-- DynamoDB 데이터와 S3 로그 데이터 조인
SELECT
  u.user_name,
  u.email,
  l.request_path,
  l.status_code,
  l.timestamp
FROM dynamodb_catalog.default.users u
JOIN analytics_db.access_logs l
  ON u.user_id = l.user_id
WHERE l.timestamp > timestamp '2024-01-01'
  AND l.status_code >= 400
ORDER BY l.timestamp DESC
LIMIT 100;
```

### RDS(MySQL) 쿼리

JDBC 커넥터를 사용하여 RDS MySQL 데이터를 직접 조회할 수 있습니다.

```bash
# JDBC 커넥터에 필요한 연결 정보를 Secrets Manager에 저장
aws secretsmanager create-secret \
  --name athena-rds-connection \
  --description "RDS connection for Athena Federated Query" \
  --secret-string '{
    "username": "athena_reader",
    "password": "SecurePassword123!",
    "engine": "mysql",
    "host": "my-rds-instance.abcdefg12345.ap-northeast-2.rds.amazonaws.com",
    "port": "3306",
    "dbname": "production_db"
  }'
```

```sql
-- RDS 카탈로그를 통한 쿼리
SELECT
  o.order_id,
  o.product_name,
  o.quantity,
  o.order_date,
  u.user_name,
  u.email
FROM rds_catalog.production_db.orders o
JOIN rds_catalog.production_db.users u
  ON o.user_id = u.id
WHERE o.order_date >= DATE '2024-01-01'
ORDER BY o.order_date DESC;

-- S3 로그 + RDS 주문 데이터 크로스 소스 조인
SELECT
  r.product_name,
  COUNT(DISTINCT s.session_id) AS page_views,
  COUNT(DISTINCT r.order_id) AS orders,
  CAST(COUNT(DISTINCT r.order_id) AS DOUBLE) / COUNT(DISTINCT s.session_id) AS conversion_rate
FROM analytics_db.web_sessions s
JOIN rds_catalog.production_db.orders r
  ON s.user_id = CAST(r.user_id AS VARCHAR)
WHERE s.year = 2024 AND s.month = 1
GROUP BY r.product_name
ORDER BY conversion_rate DESC;
```

### CloudWatch Logs 쿼리

```sql
-- CloudWatch Logs에서 Lambda 에러 분석
SELECT
  log_stream,
  message,
  ingestion_time
FROM cloudwatch_catalog.default."/aws/lambda/my-function"
WHERE message LIKE '%ERROR%'
  AND ingestion_time > to_unixtime(current_timestamp - interval '24' hour) * 1000
ORDER BY ingestion_time DESC
LIMIT 50;
```

### 멀티 소스 대시보드 쿼리

여러 데이터 소스를 하나의 쿼리로 조합하는 실전 예시입니다.

```sql
-- S3 이벤트 로그 + DynamoDB 사용자 + RDS 주문 통합 분석
WITH user_events AS (
  SELECT
    user_id,
    COUNT(*) AS event_count,
    MAX(timestamp) AS last_event
  FROM analytics_db.event_logs
  WHERE year = 2024 AND month = 1
  GROUP BY user_id
),
user_orders AS (
  SELECT
    CAST(user_id AS VARCHAR) AS user_id,
    COUNT(*) AS order_count,
    SUM(amount) AS total_amount
  FROM rds_catalog.production_db.orders
  WHERE order_date >= DATE '2024-01-01'
  GROUP BY user_id
)
SELECT
  d.user_name,
  d.email,
  d.subscription_tier,
  COALESCE(e.event_count, 0) AS events,
  COALESCE(o.order_count, 0) AS orders,
  COALESCE(o.total_amount, 0) AS revenue
FROM dynamodb_catalog.default.users d
LEFT JOIN user_events e ON d.user_id = e.user_id
LEFT JOIN user_orders o ON d.user_id = o.user_id
WHERE d.subscription_tier = 'premium'
ORDER BY revenue DESC;
```

### Python 자동화

```python
import boto3
import json

def deploy_federated_connector(connector_arn, catalog_name, spill_bucket, region='ap-northeast-2'):
    """Federated Query 커넥터를 배포하고 카탈로그를 등록하는 함수"""
    sar_client = boto3.client('serverlessrepo', region_name='us-east-1')
    athena_client = boto3.client('athena', region_name=region)

    # SAR에서 커넥터 애플리케이션 배포
    response = sar_client.create_cloud_formation_change_set(
        ApplicationId=connector_arn,
        StackName=f'athena-{catalog_name}-connector',
        Capabilities=['CAPABILITY_IAM', 'CAPABILITY_RESOURCE_POLICY'],
        ParameterOverrides=[
            {'Name': 'SpillBucket', 'Value': spill_bucket},
            {'Name': 'AthenaCatalogName', 'Value': catalog_name}
        ]
    )
    print(f"Change set created: {response['ChangeSetId']}")

    # Athena 카탈로그 등록
    lambda_arn = f'arn:aws:lambda:{region}:123456789012:function:{catalog_name}'
    athena_client.create_data_catalog(
        Name=catalog_name,
        Type='LAMBDA',
        Parameters={'function': lambda_arn}
    )
    print(f"Data catalog '{catalog_name}' registered")

# 사용 예시
deploy_federated_connector(
    connector_arn='arn:aws:serverlessrepo:us-east-1:292517598671:applications/AthenaDynamoDBConnector',
    catalog_name='dynamodb_catalog',
    spill_bucket='my-athena-spill-bucket'
)
```

## 모범 사례/보안

### 성능 최적화

**1. 조건 푸시다운 활용**: WHERE 절에 데이터 소스의 인덱스 컬럼이나 파티션 키를 사용하면, 소스 수준에서 필터링이 수행되어 성능이 향상됩니다. DynamoDB의 경우 파티션 키와 정렬 키를 조건에 포함시키는 것이 중요합니다.

**2. Lambda 동시성 관리**: 대량 데이터를 처리할 때 Lambda 동시 실행 수가 급증할 수 있습니다. Lambda의 Reserved Concurrency를 적절히 설정하여 다른 Lambda 함수에 영향을 주지 않도록 해야 합니다.

**3. Spill Bucket 최적화**: Spill Bucket은 Lambda 함수와 같은 리전에 위치해야 하며, S3 수명 주기 정책을 설정하여 Spill 데이터가 자동으로 정리되도록 해야 합니다.

```json
{
  "Rules": [
    {
      "ID": "CleanupSpillData",
      "Status": "Enabled",
      "Prefix": "athena-spill/",
      "Expiration": {
        "Days": 1
      }
    }
  ]
}
```

**4. 데이터 소스 쪽 리소스 관리**: Federated Query는 데이터 소스에 직접 쿼리하므로, 소스의 처리 용량을 고려해야 합니다. RDS의 경우 읽기 전용 복제본을, DynamoDB의 경우 On-Demand 용량 모드를 사용하는 것이 안전합니다.

### 보안 설정

**1. Lambda 실행 역할 최소 권한**: 커넥터 Lambda 함수의 IAM 역할에는 필요한 최소한의 권한만 부여해야 합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:DescribeTable",
        "dynamodb:ListTables",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:ap-northeast-2:123456789012:table/users"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::my-athena-spill-bucket/athena-spill/*"
    },
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:athena-*"
    }
  ]
}
```

**2. VPC 구성**: RDS 등 VPC 내부의 데이터 소스에 접근해야 하는 경우, Lambda 커넥터를 VPC에 배치해야 합니다. 이때 NAT Gateway나 VPC Endpoint를 통해 S3 및 기타 AWS 서비스에 접근할 수 있도록 네트워크를 구성해야 합니다.

**3. Secrets Manager 연동**: 데이터베이스 자격 증명은 반드시 AWS Secrets Manager에 저장하고, Lambda 함수에서 이를 참조하도록 해야 합니다. 하드코딩된 자격 증명은 절대 사용하지 않아야 합니다.

**4. Spill 데이터 암호화**: Spill Bucket에 저장되는 중간 데이터는 기본적으로 AES-GCM 256비트로 암호화됩니다. 추가적으로 S3 버킷 정책에서 SSL 전송을 강제하는 것이 좋습니다.

### 비용 최적화

- Federated Query의 비용은 Athena 쿼리 비용(스캔 데이터 기반) + Lambda 실행 비용 + 데이터 소스 비용으로 구성됩니다.
- Lambda 함수의 메모리를 적절히 설정하면 실행 시간과 비용을 최적화할 수 있습니다.
- 자주 조회되는 외부 데이터는 CTAS를 사용하여 S3에 스냅샷을 만들어 두면 비용을 절감할 수 있습니다.

## 관련 서비스 비교

### Federated Query vs ETL (AWS Glue)

| 항목 | Federated Query | ETL (AWS Glue) |
|------|----------------|----------------|
| 데이터 이동 | 없음 (소스에서 직접 쿼리) | S3로 데이터 복사 |
| 데이터 신선도 | 실시간 (항상 최신) | ETL 주기에 따라 다름 |
| 성능 | 소스 성능에 의존 | S3 최적화 포맷으로 빠름 |
| 비용 | 쿼리마다 소스 부하 발생 | 초기 ETL 비용 후 쿼리 저렴 |
| 적합한 사용 사례 | Ad-hoc 분석, 실시간 조인 | 대규모 반복 분석 |

### Federated Query vs Redshift Spectrum

Redshift Spectrum은 S3 데이터만 연합 쿼리할 수 있는 반면, Athena Federated Query는 다양한 데이터 소스를 지원합니다. 하지만 Redshift 환경에서 S3 데이터를 조회하는 것이 목적이라면, Spectrum이 Redshift의 쿼리 최적화 기능을 활용할 수 있어 더 나은 성능을 제공합니다.

### Federated Query vs Amazon Data Pipeline

Data Pipeline은 데이터를 이동시키는 서비스인 반면, Federated Query는 데이터를 이동시키지 않고 직접 쿼리합니다. 일회성 분석이나 실시간 데이터가 필요한 경우 Federated Query가, 정기적인 대량 데이터 이동이 필요한 경우 Data Pipeline이 적합합니다.

### Custom Connector vs AWS 제공 Connector

| 항목 | AWS 제공 Connector | Custom Connector |
|------|-------------------|------------------|
| 배포 방식 | SAR에서 원클릭 배포 | 직접 개발 및 배포 |
| 유지보수 | AWS가 업데이트 관리 | 직접 관리 필요 |
| 최적화 | 데이터 소스에 최적화됨 | 비즈니스 로직에 최적화 가능 |
| 데이터 소스 | 사전 정의된 소스만 | 모든 소스 가능 |

## 요약

Amazon Athena Federated Query는 데이터를 이동시키지 않고 다양한 데이터 소스를 단일 SQL로 분석할 수 있는 강력한 기능입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **Lambda 기반 커넥터**: 각 데이터 소스에 대한 커넥터가 Lambda 함수로 동작하며, AWS에서 25개 이상의 사전 구축 커넥터를 제공합니다.
- **크로스 소스 조인**: S3, RDS, DynamoDB, CloudWatch 등 다양한 소스의 데이터를 단일 쿼리로 조인할 수 있습니다.
- **조건 푸시다운**: WHERE 절의 조건이 데이터 소스로 푸시다운되어 성능을 최적화합니다.
- **Spill 메커니즘**: Lambda 응답 크기 제한을 S3 Spill Bucket으로 우회하며, 데이터는 AES-GCM으로 암호화됩니다.
- **보안**: Lambda 역할의 최소 권한, Secrets Manager를 통한 자격 증명 관리, VPC 배치가 핵심입니다.
- **활용 판단**: 실시간 데이터가 필요한 ad-hoc 분석에는 Federated Query를, 반복적인 대규모 분석에는 ETL 파이프라인이 적합합니다.

Federated Query는 데이터 사일로를 허물고, 조직 전체의 데이터를 하나의 SQL 인터페이스로 통합할 수 있는 핵심 기술입니다.