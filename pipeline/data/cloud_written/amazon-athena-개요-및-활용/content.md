<!-- infographic-hero -->
![Amazon Athena 개요 및 활용 핵심 요약](figures/infographic.svg)

*Figure: Amazon Athena 개요 및 활용 한 장 요약 인포그래픽*

# Amazon Athena 개요 및 활용

## 개요

Amazon Athena는 Amazon S3에 저장된 데이터를 표준 SQL을 사용하여 직접 분석할 수 있는 서버리스 대화형 쿼리 서비스입니다. 별도의 서버를 프로비저닝하거나 관리할 필요 없이, S3에 있는 데이터를 그대로 쿼리할 수 있다는 것이 가장 큰 특징입니다.

Athena는 내부적으로 Presto(현재 Trino) 엔진을 기반으로 동작하며, ANSI SQL을 지원합니다. 사용자는 쿼리가 스캔한 데이터 양에 대해서만 비용을 지불하므로, 비용 효율적인 데이터 분석이 가능합니다. 2016년 re:Invent에서 처음 발표된 이후, AWS 데이터 분석 생태계에서 핵심적인 위치를 차지하고 있습니다.

### Athena를 선택해야 하는 경우

Athena는 다음과 같은 상황에서 특히 유용합니다.

- S3에 이미 대량의 로그 데이터가 적재되어 있고, 빠르게 ad-hoc 분석이 필요한 경우
- ETL 파이프라인 없이 데이터 레이크의 데이터를 직접 조회하고 싶은 경우
- 주기적이지 않은 일회성 또는 비정기적 분석 작업이 많은 경우
- 데이터 웨어하우스를 구축하기 전 탐색적 데이터 분석(EDA)을 수행하는 경우

### 가격 체계

Athena의 가격은 매우 단순합니다. 쿼리당 스캔한 데이터 1TB에 대해 $5.00가 과금됩니다. 최소 과금 단위는 쿼리당 10MB이며, DDL 문이나 실패한 쿼리에는 비용이 부과되지 않습니다. 이 과금 모델은 데이터 포맷 최적화와 파티셔닝 전략이 비용에 직접적인 영향을 미친다는 것을 의미합니다.

## 핵심 기능

### 서버리스 아키텍처

Athena는 완전한 서버리스 서비스입니다. 사용자는 클러스터를 생성하거나, 노드 수를 조정하거나, 소프트웨어를 업데이트할 필요가 전혀 없습니다. 쿼리를 실행하면 Athena가 자동으로 필요한 컴퓨팅 리소스를 할당하고, 쿼리가 완료되면 리소스를 반환합니다.

### 지원 데이터 포맷

Athena는 다양한 데이터 포맷을 지원합니다.

- **텍스트 기반**: CSV, TSV, JSON, Apache Web Logs
- **컬럼형 포맷**: Apache Parquet, Apache ORC
- **기타**: Avro, CloudTrail Logs, Apache Hudi, Delta Lake, Apache Iceberg

특히 컬럼형 포맷인 Parquet과 ORC를 사용하면 쿼리 성능이 크게 향상되고, 스캔 데이터 양이 줄어들어 비용을 절감할 수 있습니다.

### CTAS (Create Table As Select)

CTAS는 SELECT 쿼리의 결과를 새로운 테이블로 생성하는 기능입니다. 이를 활용하면 데이터 변환과 포맷 전환을 SQL 한 줄로 처리할 수 있습니다.

```sql
CREATE TABLE my_database.optimized_logs
WITH (
  format = 'PARQUET',
  parquet_compression = 'SNAPPY',
  external_location = 's3://my-bucket/optimized-logs/',
  partitioned_by = ARRAY['year', 'month']
) AS
SELECT
  request_id,
  timestamp,
  status_code,
  response_time,
  year(timestamp) AS year,
  month(timestamp) AS month
FROM my_database.raw_logs
WHERE timestamp >= date '2024-01-01';
```

### INSERT INTO

INSERT INTO 문을 사용하면 기존 테이블에 쿼리 결과를 추가할 수 있습니다. 이를 통해 점진적 데이터 변환 파이프라인을 구축할 수 있습니다.

### 뷰(View) 지원

Athena는 표준 SQL 뷰를 지원하여, 복잡한 쿼리를 캡슐화하고 재사용할 수 있습니다.

```sql
CREATE OR REPLACE VIEW daily_error_summary AS
SELECT
  date_trunc('day', timestamp) AS day,
  status_code,
  COUNT(*) AS error_count,
  AVG(response_time) AS avg_response_time
FROM my_database.optimized_logs
WHERE status_code >= 400
GROUP BY 1, 2;
```

### Prepared Statements

Prepared Statements를 사용하면 파라미터화된 쿼리를 미리 정의하고 재사용할 수 있습니다. SQL 인젝션 방지와 쿼리 재사용성 향상에 도움이 됩니다.

```sql
PREPARE my_query FROM
SELECT * FROM my_database.logs
WHERE status_code = ? AND timestamp > ?;

EXECUTE my_query USING 500, timestamp '2024-01-01 00:00:00';
```

## 아키텍처/동작 원리

### 내부 아키텍처

Athena의 내부 아키텍처는 다음과 같은 계층으로 구성됩니다.

1. **쿼리 인터페이스 계층**: AWS Management Console, AWS CLI, JDBC/ODBC 드라이버, SDK를 통해 쿼리를 접수합니다.
2. **쿼리 플래닝 계층**: 접수된 SQL을 파싱하고, AWS Glue Data Catalog에서 테이블 메타데이터를 조회하여 실행 계획을 수립합니다.
3. **쿼리 실행 계층**: Presto/Trino 엔진이 분산 환경에서 쿼리를 실행합니다. S3에서 데이터를 병렬로 읽어들이고, 필터링, 집계, 조인 등의 연산을 수행합니다.
4. **결과 반환 계층**: 쿼리 결과를 지정된 S3 버킷에 저장하고, 사용자에게 반환합니다.

### Glue Data Catalog 연동

Athena는 AWS Glue Data Catalog을 메타스토어로 사용합니다. Data Catalog에 데이터베이스와 테이블을 정의하면, Athena가 이를 참조하여 S3 데이터의 위치, 스키마, 파티션 정보를 파악합니다.

```bash
# AWS CLI로 Glue 데이터베이스 생성
aws glue create-database \
  --database-input '{"Name": "analytics_db", "Description": "Analytics database for log analysis"}'

# Glue 크롤러 생성 - S3 데이터를 자동으로 스키마 탐지
aws glue create-crawler \
  --name "logs-crawler" \
  --role "arn:aws:iam::123456789012:role/GlueCrawlerRole" \
  --database-name "analytics_db" \
  --targets '{"S3Targets": [{"Path": "s3://my-bucket/raw-logs/"}]}'

# 크롤러 실행
aws glue start-crawler --name "logs-crawler"
```

### 쿼리 실행 흐름

사용자가 쿼리를 제출하면 다음과 같은 순서로 처리됩니다.

1. SQL 파싱 및 유효성 검증
2. Glue Data Catalog에서 메타데이터 조회
3. 쿼리 최적화 (조건 푸시다운, 파티션 프루닝 등)
4. S3에서 데이터 병렬 스캔
5. 분산 쿼리 실행 (필터링, 집계, 조인)
6. 결과를 S3 결과 버킷에 저장
7. 사용자에게 결과 반환

### 파티셔닝과 쿼리 최적화

파티셔닝은 Athena 성능 최적화에서 가장 중요한 요소입니다. S3의 데이터를 특정 키(예: 날짜, 리전)로 분할하여 저장하면, Athena가 쿼리 조건에 해당하는 파티션만 스캔하여 성능과 비용을 모두 최적화할 수 있습니다.

S3 데이터 구조 예시는 다음과 같습니다.

```
s3://my-bucket/logs/
  year=2024/
    month=01/
      day=01/
        data-001.parquet
        data-002.parquet
      day=02/
        data-003.parquet
    month=02/
      ...
```

파티션을 활용한 테이블 생성은 다음과 같습니다.

```sql
CREATE EXTERNAL TABLE analytics_db.partitioned_logs (
  request_id STRING,
  timestamp TIMESTAMP,
  method STRING,
  path STRING,
  status_code INT,
  response_time DOUBLE,
  user_agent STRING
)
PARTITIONED BY (year INT, month INT, day INT)
STORED AS PARQUET
LOCATION 's3://my-bucket/logs/';

-- 파티션 자동 로드
MSCK REPAIR TABLE analytics_db.partitioned_logs;
```

파티션 프루닝이 적용되는 쿼리를 작성하면 스캔 범위가 극적으로 줄어듭니다.

```sql
-- 파티션 프루닝 적용: 2024년 1월 데이터만 스캔
SELECT status_code, COUNT(*) AS cnt
FROM analytics_db.partitioned_logs
WHERE year = 2024 AND month = 1
GROUP BY status_code
ORDER BY cnt DESC;
```

## 실전 활용

### AWS CLI를 통한 Athena 쿼리 실행

Athena 쿼리를 AWS CLI로 실행하는 방법은 다음과 같습니다.

```bash
# 쿼리 실행 시작
QUERY_EXECUTION_ID=$(aws athena start-query-execution \
  --query-string "SELECT status_code, COUNT(*) as cnt FROM analytics_db.partitioned_logs WHERE year=2024 AND month=1 GROUP BY status_code ORDER BY cnt DESC" \
  --query-execution-context Database=analytics_db \
  --result-configuration OutputLocation=s3://my-athena-results/output/ \
  --output text --query 'QueryExecutionId')

echo "Query Execution ID: $QUERY_EXECUTION_ID"

# 쿼리 상태 확인
aws athena get-query-execution \
  --query-execution-id "$QUERY_EXECUTION_ID" \
  --query 'QueryExecution.Status.State'

# 쿼리 결과 조회
aws athena get-query-results \
  --query-execution-id "$QUERY_EXECUTION_ID" \
  --output json
```

### CloudTrail 로그 분석

CloudTrail 로그를 Athena로 분석하는 것은 가장 대표적인 활용 사례 중 하나입니다.

```sql
CREATE EXTERNAL TABLE cloudtrail_logs (
  eventVersion STRING,
  userIdentity STRUCT<
    type: STRING,
    principalId: STRING,
    arn: STRING,
    accountId: STRING,
    invokedBy: STRING,
    accessKeyId: STRING,
    userName: STRING,
    sessionContext: STRUCT<
      attributes: STRUCT<
        mfaAuthenticated: STRING,
        creationDate: STRING>,
      sessionIssuer: STRUCT<
        type: STRING,
        principalId: STRING,
        arn: STRING,
        accountId: STRING,
        userName: STRING>>>,
  eventTime STRING,
  eventSource STRING,
  eventName STRING,
  awsRegion STRING,
  sourceIPAddress STRING,
  userAgent STRING,
  errorCode STRING,
  errorMessage STRING,
  requestParameters STRING,
  responseElements STRING,
  additionalEventData STRING,
  requestId STRING,
  eventId STRING,
  resources ARRAY<STRUCT<
    arn: STRING,
    accountId: STRING,
    type: STRING>>,
  eventType STRING,
  recipientAccountId STRING
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
LOCATION 's3://my-cloudtrail-bucket/AWSLogs/123456789012/CloudTrail/';
```

CloudTrail 로그에서 보안 관련 이벤트를 분석하는 쿼리는 다음과 같습니다.

```sql
-- 최근 7일간 실패한 API 호출 상위 10개
SELECT
  eventSource,
  eventName,
  errorCode,
  COUNT(*) AS error_count
FROM cloudtrail_logs
WHERE errorCode IS NOT NULL
  AND from_iso8601_timestamp(eventTime) > current_timestamp - interval '7' day
GROUP BY eventSource, eventName, errorCode
ORDER BY error_count DESC
LIMIT 10;

-- 콘솔 로그인 실패 감지
SELECT
  userIdentity.userName,
  sourceIPAddress,
  eventTime,
  errorMessage
FROM cloudtrail_logs
WHERE eventName = 'ConsoleLogin'
  AND errorMessage = 'Failed authentication'
ORDER BY eventTime DESC;
```

### VPC Flow Logs 분석

VPC Flow Logs를 Athena로 분석하면 네트워크 트래픽 패턴을 파악할 수 있습니다.

```sql
CREATE EXTERNAL TABLE vpc_flow_logs (
  version INT,
  account_id STRING,
  interface_id STRING,
  srcaddr STRING,
  dstaddr STRING,
  srcport INT,
  dstport INT,
  protocol BIGINT,
  packets BIGINT,
  bytes BIGINT,
  start BIGINT,
  "end" BIGINT,
  action STRING,
  log_status STRING
)
PARTITIONED BY (dt STRING)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ' '
LOCATION 's3://my-vpc-flow-logs-bucket/AWSLogs/123456789012/vpcflowlogs/';

-- 거부된 트래픽 분석
SELECT
  srcaddr,
  dstaddr,
  dstport,
  protocol,
  SUM(packets) AS total_packets,
  SUM(bytes) AS total_bytes
FROM vpc_flow_logs
WHERE action = 'REJECT'
  AND dt >= '2024-01-01'
GROUP BY srcaddr, dstaddr, dstport, protocol
ORDER BY total_bytes DESC
LIMIT 20;
```

### ALB Access Logs 분석

```sql
CREATE EXTERNAL TABLE alb_logs (
  type STRING,
  time STRING,
  elb STRING,
  client_ip STRING,
  client_port INT,
  target_ip STRING,
  target_port INT,
  request_processing_time DOUBLE,
  target_processing_time DOUBLE,
  response_processing_time DOUBLE,
  elb_status_code INT,
  target_status_code STRING,
  received_bytes BIGINT,
  sent_bytes BIGINT,
  request_verb STRING,
  request_url STRING,
  request_proto STRING,
  user_agent STRING,
  ssl_cipher STRING,
  ssl_protocol STRING,
  target_group_arn STRING,
  trace_id STRING,
  domain_name STRING,
  chosen_cert_arn STRING,
  matched_rule_priority STRING,
  request_creation_time STRING,
  actions_executed STRING,
  redirect_url STRING,
  lambda_error_reason STRING,
  target_port_list STRING,
  target_status_code_list STRING,
  classification STRING,
  classification_reason STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.RegexSerDe'
WITH SERDEPROPERTIES (
  'serialization.format' = '1',
  'input.regex' = '([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*):([0-9]*) ([^ ]*)[:-]([0-9]*) ([-.0-9]*) ([-.0-9]*) ([-.0-9]*) (|[0-9]*) (-|[0-9]*) ([-0-9]*) ([-0-9]*) \"([^ ]*) (.*) (- |[^ ]*)\" \"([^\"]*)\" ([A-Z0-9-_]+) ([A-Za-z0-9.-]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^\"]*)\" ([-.0-9]*) ([^ ]*) \"([^\"]*)\" \"([^\"]*)\" \"([^ ]*)\" \"([^\s]*)\" \"([^ ]*)\" \"([^ ]*)\"'
)
LOCATION 's3://my-alb-logs-bucket/AWSLogs/123456789012/elasticloadbalancing/';

-- 응답 시간이 느린 요청 분석
SELECT
  request_url,
  AVG(target_processing_time) AS avg_processing_time,
  MAX(target_processing_time) AS max_processing_time,
  COUNT(*) AS request_count
FROM alb_logs
WHERE target_processing_time > 1.0
GROUP BY request_url
ORDER BY avg_processing_time DESC
LIMIT 20;
```

### Python Boto3를 활용한 자동화

```python
import boto3
import time

def run_athena_query(query, database, output_location):
    """Athena 쿼리를 실행하고 결과를 반환하는 함수"""
    client = boto3.client('athena')

    # 쿼리 시작
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': output_location}
    )
    query_execution_id = response['QueryExecutionId']

    # 쿼리 완료 대기
    while True:
        result = client.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        state = result['QueryExecution']['Status']['State']
        if state in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)

    if state != 'SUCCEEDED':
        reason = result['QueryExecution']['Status'].get('StateChangeReason', 'Unknown')
        raise Exception(f"Query failed: {reason}")

    # 결과 조회
    results = client.get_query_results(
        QueryExecutionId=query_execution_id
    )

    # 스캔 데이터 양 확인
    stats = result['QueryExecution']['Statistics']
    scanned_bytes = stats['DataScannedInBytes']
    execution_time = stats['EngineExecutionTimeInMillis']
    print(f"Scanned: {scanned_bytes / (1024**2):.2f} MB")
    print(f"Execution time: {execution_time} ms")

    return results

# 사용 예시
results = run_athena_query(
    query="SELECT status_code, COUNT(*) as cnt FROM logs WHERE year=2024 GROUP BY status_code",
    database="analytics_db",
    output_location="s3://my-athena-results/output/"
)
```

## 모범 사례/보안

### 성능 최적화 모범 사례

**1. 컬럼형 포맷 사용**: CSV 대신 Parquet 또는 ORC 포맷을 사용하면 스캔 데이터 양을 90% 이상 줄일 수 있습니다. 특히 SELECT 절에서 특정 컬럼만 조회하는 경우 효과가 극대화됩니다.

**2. 데이터 압축 적용**: Snappy, GZIP, LZ4, ZSTD 등의 압축을 적용하면 스캔 데이터 양과 비용이 줄어듭니다. Parquet의 경우 Snappy 압축이 기본적으로 권장됩니다.

**3. 적절한 파티셔닝**: 자주 사용되는 필터 조건(날짜, 리전 등)으로 파티셔닝하면 불필요한 데이터 스캔을 방지할 수 있습니다. 단, 파티션이 너무 많으면(수십만 개 이상) 오히려 성능이 저하될 수 있으므로 적절한 수준을 유지해야 합니다.

**4. 파일 크기 최적화**: S3의 개별 파일 크기를 128MB~512MB 범위로 유지하는 것이 좋습니다. 너무 작은 파일이 많으면 S3 GET 요청 오버헤드가 증가하고, 너무 크면 병렬 처리 효율이 떨어집니다.

**5. SELECT *를 피하기**: 필요한 컬럼만 명시적으로 지정하면, 특히 컬럼형 포맷에서 스캔 데이터 양을 크게 줄일 수 있습니다.

### 보안 모범 사례

**1. IAM 정책을 통한 접근 제어**: Athena에 대한 접근을 IAM 정책으로 세밀하게 제어할 수 있습니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults"
      ],
      "Resource": "arn:aws:athena:ap-northeast-2:123456789012:workgroup/analytics-team"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-data-bucket",
        "arn:aws:s3:::my-data-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject"],
      "Resource": "arn:aws:s3:::my-athena-results/*"
    }
  ]
}
```

**2. Workgroup을 통한 격리**: 팀별 또는 용도별로 Workgroup을 분리하여 쿼리 리소스와 비용을 관리할 수 있습니다.

```bash
# Workgroup 생성
aws athena create-work-group \
  --name "analytics-team" \
  --configuration '{
    "ResultConfiguration": {
      "OutputLocation": "s3://my-athena-results/analytics-team/",
      "EncryptionConfiguration": {
        "EncryptionOption": "SSE_S3"
      }
    },
    "EnforceWorkGroupConfiguration": true,
    "PublishCloudWatchMetricsEnabled": true,
    "BytesScannedCutoffPerQuery": 1073741824
  }' \
  --description "Analytics team workgroup with 1GB scan limit"
```

**3. 쿼리 결과 암호화**: S3에 저장되는 쿼리 결과를 SSE-S3, SSE-KMS, 또는 CSE-KMS로 암호화할 수 있습니다.

**4. Lake Formation 연동**: AWS Lake Formation과 연동하면 컬럼 수준의 세밀한 접근 제어가 가능합니다.

### 비용 최적화 팁

다음은 실전에서 비용을 크게 절감할 수 있는 방법들입니다.

- CSV에서 Parquet으로 전환하면 비용이 30~90% 절감됩니다.
- 파티셔닝 적용으로 불필요한 데이터 스캔을 제거합니다.
- Workgroup에서 쿼리당 스캔 제한(BytesScannedCutoffPerQuery)을 설정하여 비용 폭증을 방지합니다.
- CTAS를 사용하여 자주 조회되는 데이터를 최적화된 포맷으로 변환합니다.

## 관련 서비스 비교

### Athena vs Amazon Redshift

| 항목 | Amazon Athena | Amazon Redshift |
|------|--------------|----------------|
| 서버 관리 | 서버리스 (관리 불필요) | 클러스터 프로비저닝 필요 (Serverless 옵션 있음) |
| 과금 방식 | 스캔 데이터 양 기반 | 노드/RPU 시간 기반 |
| 최적 사용 사례 | Ad-hoc 쿼리, 비정기 분석 | 대규모 반복 쿼리, 대시보드 |
| 동시 쿼리 | 제한적 (기본 20~25) | 높음 (WLM 설정 가능) |
| 데이터 위치 | S3 (외부 데이터) | 자체 스토리지 + S3 Spectrum |
| 성능 | 데이터 크기에 비례 | 클러스터 크기에 따라 일정 |

### Athena vs Amazon Redshift Spectrum

Redshift Spectrum은 Redshift 클러스터에서 S3 데이터를 조회하는 기능입니다. Athena와 유사하지만, Redshift 클러스터가 필요하고, Redshift의 쿼리 최적화 기능을 활용할 수 있다는 차이가 있습니다. 이미 Redshift를 사용하고 있다면 Spectrum을, S3 데이터만 분석한다면 Athena를 선택하는 것이 적합합니다.

### Athena vs AWS Glue

Glue는 ETL 서비스이고, Athena는 쿼리 서비스입니다. 둘은 상호 보완적인 관계입니다. Glue로 데이터를 변환하고, Athena로 분석하는 패턴이 일반적입니다. Glue Data Catalog은 두 서비스 모두의 메타스토어 역할을 합니다.

### Athena vs Amazon EMR

EMR은 Hadoop, Spark, Presto 등을 실행할 수 있는 관리형 클러스터 서비스입니다. 복잡한 데이터 처리나 ML 파이프라인에는 EMR이, 단순 SQL 분석에는 Athena가 적합합니다.

## 요약

Amazon Athena는 S3 데이터 레이크 위에서 표준 SQL을 사용하여 서버리스로 대화형 분석을 수행할 수 있는 강력한 서비스입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **서버리스**: 인프라 관리가 전혀 필요 없으며, 쿼리 실행 시 자동으로 리소스가 할당됩니다.
- **비용 효율적**: 스캔한 데이터 양에 대해서만 과금되므로, 포맷 최적화와 파티셔닝으로 비용을 극적으로 줄일 수 있습니다.
- **다양한 활용**: CloudTrail, VPC Flow Logs, ALB 로그 등 AWS 서비스 로그 분석에 특히 강력합니다.
- **최적화 핵심**: Parquet/ORC 컬럼형 포맷 사용, 적절한 파티셔닝, 파일 크기 최적화가 성능과 비용 모두에 결정적입니다.
- **보안**: Workgroup 격리, IAM 정책, Lake Formation 연동으로 세밀한 접근 제어가 가능합니다.

Athena는 데이터 레이크 분석의 시작점으로, 복잡한 인프라 없이도 S3 데이터를 즉시 분석할 수 있는 가장 빠른 경로를 제공합니다.