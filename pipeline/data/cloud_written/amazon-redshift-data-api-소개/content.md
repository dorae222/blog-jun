<!-- infographic-hero -->
![Amazon Redshift Data API 핵심 요약](figures/infographic.svg)

*Figure: Amazon Redshift Data API 한 장 요약 인포그래픽*

## 개요

Amazon Redshift Data API는 Redshift 클러스터 또는 Redshift Serverless에 대해 JDBC/ODBC 드라이버 없이 HTTP 기반으로 SQL 쿼리를 실행할 수 있는 관리형 API 서비스입니다. 2020년에 출시되었으며, 서버리스 환경(Lambda, Step Functions, EventBridge)에서 Redshift를 활용하는 데 핵심적인 역할을 합니다.

기존에 Redshift에 쿼리를 실행하려면 JDBC/ODBC 드라이버를 설치하고, 클러스터에 대한 네트워크 연결(VPC, 보안 그룹)을 설정하고, 데이터베이스 자격 증명을 관리해야 했습니다. Data API는 이러한 복잡성을 제거하고, AWS SDK 호출 한 번으로 쿼리를 실행할 수 있게 합니다.

Data API의 주요 특징은 다음과 같습니다.

- **드라이버 불필요**: JDBC/ODBC 드라이버 설치 없이 AWS SDK 또는 CLI로 호출합니다.
- **VPC 연결 불필요**: Data API가 내부적으로 Redshift에 연결하므로, 호출자가 VPC에 있을 필요가 없습니다.
- **비동기 실행**: 쿼리를 제출하면 즉시 Statement ID가 반환되고, 결과는 별도로 조회합니다.
- **IAM 인증**: 데이터베이스 자격 증명 대신 IAM 역할 또는 Secrets Manager를 통해 인증합니다.
- **자동 연결 관리**: 연결 풀링, 연결 생성/해제를 자동으로 처리합니다.

---

## 핵심 기능

### 1. 비동기 쿼리 실행

Data API의 핵심 호출 패턴은 "제출 → 상태 확인 → 결과 조회"의 3단계입니다.

```bash
# 1단계: 쿼리 제출 (비동기)
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --db-user admin \
  --sql "SELECT product_category, SUM(amount) as total_sales FROM sales WHERE sale_date >= '2024-01-01' GROUP BY product_category ORDER BY total_sales DESC LIMIT 10;" \
  --region ap-northeast-2

# 응답 예시:
# {
#     "Id": "d9b6c0c9-0747-4bf4-b142-e8883122f766",
#     "CreatedAt": "2024-01-15T10:30:00Z",
#     "Database": "analytics",
#     "ClusterIdentifier": "my-redshift-cluster"
# }

# 2단계: 실행 상태 확인
aws redshift-data describe-statement \
  --id d9b6c0c9-0747-4bf4-b142-e8883122f766 \
  --region ap-northeast-2

# 3단계: 결과 조회 (상태가 FINISHED일 때)
aws redshift-data get-statement-result \
  --id d9b6c0c9-0747-4bf4-b142-e8883122f766 \
  --region ap-northeast-2
```

### 2. 배치 실행 (Batch Execute)

여러 SQL 문을 하나의 API 호출로 제출할 수 있습니다.

```bash
# 다중 SQL 배치 실행
aws redshift-data batch-execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --db-user admin \
  --sqls \
    "CREATE TEMP TABLE tmp_summary AS SELECT product_id, SUM(amount) as total FROM sales GROUP BY product_id;" \
    "UPDATE products SET last_total_sales = tmp.total FROM tmp_summary tmp WHERE products.product_id = tmp.product_id;" \
    "DROP TABLE tmp_summary;" \
  --region ap-northeast-2
```

배치 실행의 제약 사항은 다음과 같습니다.

- 최대 40개의 SQL 문을 하나의 배치로 실행할 수 있습니다.
- 모든 SQL 문은 단일 트랜잭션으로 실행됩니다 (하나라도 실패하면 전체 롤백).
- 각 SQL 문의 결과를 개별적으로 조회할 수 있습니다.

### 3. 인증 방식

Data API는 세 가지 인증 방식을 지원합니다.

**IAM 임시 자격 증명 (db-user)**
- IAM 역할을 통해 Redshift의 임시 DB 자격 증명을 자동 생성합니다.
- 가장 간단한 방식이며, Lambda에서 권장됩니다.

**Secrets Manager 연동**
- DB 자격 증명을 Secrets Manager에 저장하고, Secret ARN으로 참조합니다.
- 자격 증명 로테이션이 필요한 환경에 적합합니다.

**Redshift Serverless 워크그룹**
- 클러스터 식별자 대신 워크그룹 이름으로 접근합니다.

```bash
# Secrets Manager 기반 인증
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --secret-arn arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:redshift-creds \
  --sql "SELECT COUNT(*) FROM sales;" \
  --region ap-northeast-2

# Redshift Serverless 워크그룹 기반
aws redshift-data execute-statement \
  --workgroup-name my-serverless-workgroup \
  --database analytics \
  --db-user admin \
  --sql "SELECT COUNT(*) FROM sales;" \
  --region ap-northeast-2
```

### 4. 파라미터 바인딩

SQL Injection을 방지하기 위한 파라미터 바인딩을 지원합니다.

```bash
# 파라미터 바인딩을 사용한 안전한 쿼리
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --db-user admin \
  --sql "SELECT * FROM sales WHERE product_id = :product_id AND sale_date >= :start_date" \
  --parameters '[{"name":"product_id","value":"12345"},{"name":"start_date","value":"2024-01-01"}]' \
  --region ap-northeast-2
```

### 5. EventBridge 연동

Data API는 쿼리 완료 시 EventBridge 이벤트를 발생시킵니다. 이를 활용하면 폴링 없이 결과를 처리할 수 있습니다.

```json
{
  "source": ["aws.redshift-data"],
  "detail-type": ["Redshift Data Statement Status Change"],
  "detail": {
    "state": ["FINISHED", "FAILED"]
  }
}
```

---

## 아키텍처/동작 원리

### Data API 내부 동작 흐름

```
[1. 쿼리 제출]
Caller (Lambda/CLI/SDK)
    |
    v
[AWS Data API Service]
    |- IAM 인증 검증
    |- Secrets Manager에서 DB 자격 증명 조회 (선택)
    |- Statement ID 생성 및 반환
    |
    v
[2. 쿼리 실행]
[Redshift Cluster / Serverless]
    |- Data API가 내부적으로 연결 생성
    |- SQL 실행
    |- 결과를 Data API 서비스에 캐시
    |
    v
[3. 결과 반환]
[AWS Data API Service]
    |- 상태: SUBMITTED → PICKED → STARTED → FINISHED/FAILED
    |- EventBridge 이벤트 발행 (상태 변경 시)
    |- 결과 캐시 (24시간 유지)
    |
    v
Caller: get-statement-result로 결과 조회
```

### 쿼리 상태 전이

```
SUBMITTED → PICKED → STARTED → FINISHED
                                    ↓
                               FAILED / ABORTED
```

- **SUBMITTED**: API 호출이 접수되었습니다.
- **PICKED**: Data API 서비스가 쿼리를 수신했습니다.
- **STARTED**: Redshift에서 쿼리가 실행 중입니다.
- **FINISHED**: 쿼리가 성공적으로 완료되었습니다.
- **FAILED**: 쿼리 실행 중 오류가 발생했습니다.
- **ABORTED**: 사용자가 쿼리를 취소했습니다.

### 결과 데이터 제한

- 최대 결과 크기: 100MB
- 결과 보존 기간: 24시간
- 페이지당 최대 행 수: 없음 (NextToken으로 페이징)
- 동시 활성 쿼리 수: 리전당 기본 200개 (조정 가능)

---

## 실전 활용

### 1. Lambda에서 Data API 활용

```python
import boto3
import json
import time

def lambda_handler(event, context):
    client = boto3.client('redshift-data', region_name='ap-northeast-2')
    
    # 쿼리 제출
    response = client.execute_statement(
        ClusterIdentifier='my-redshift-cluster',
        Database='analytics',
        DbUser='admin',
        Sql="""
            SELECT 
                product_category,
                COUNT(*) as order_count,
                SUM(amount) as total_sales,
                AVG(amount) as avg_order_value
            FROM sales 
            WHERE sale_date >= :start_date
            GROUP BY product_category
            ORDER BY total_sales DESC
        """,
        Parameters=[
            {'name': 'start_date', 'value': event.get('start_date', '2024-01-01')}
        ]
    )
    
    statement_id = response['Id']
    
    # 동기식으로 결과 대기 (Lambda 타임아웃 주의)
    while True:
        status = client.describe_statement(Id=statement_id)
        state = status['Status']
        
        if state == 'FINISHED':
            break
        elif state == 'FAILED':
            raise Exception(f"Query failed: {status.get('Error', 'Unknown error')}")
        
        time.sleep(1)
    
    # 결과 조회
    result = client.get_statement_result(Id=statement_id)
    
    columns = [col['name'] for col in result['ColumnMetadata']]
    rows = []
    for record in result['Records']:
        row = {}
        for i, field in enumerate(record):
            value = list(field.values())[0]
            row[columns[i]] = value
        rows.append(row)
    
    return {
        'statusCode': 200,
        'body': json.dumps(rows, default=str)
    }
```

### 2. Step Functions + EventBridge를 활용한 비동기 패턴

Lambda의 15분 타임아웃 제한이 문제가 되는 장시간 쿼리의 경우, Step Functions과 EventBridge를 결합한 비동기 패턴을 사용합니다.

```json
{
  "Comment": "Redshift Data API async query pattern",
  "StartAt": "SubmitQuery",
  "States": {
    "SubmitQuery": {
      "Type": "Task",
      "Resource": "arn:aws:states:::aws-sdk:redshiftdata:executeStatement",
      "Parameters": {
        "ClusterIdentifier": "my-redshift-cluster",
        "Database": "analytics",
        "DbUser": "admin",
        "Sql": "SELECT * FROM large_aggregation_view;"
      },
      "ResultPath": "$.QuerySubmission",
      "Next": "WaitForCompletion"
    },
    "WaitForCompletion": {
      "Type": "Task",
      "Resource": "arn:aws:states:::aws-sdk:redshiftdata:describeStatement",
      "Parameters": {
        "Id.$": "$.QuerySubmission.Id"
      },
      "ResultPath": "$.QueryStatus",
      "Next": "CheckStatus"
    },
    "CheckStatus": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.QueryStatus.Status",
          "StringEquals": "FINISHED",
          "Next": "GetResults"
        },
        {
          "Variable": "$.QueryStatus.Status",
          "StringEquals": "FAILED",
          "Next": "QueryFailed"
        }
      ],
      "Default": "WaitAndRetry"
    },
    "WaitAndRetry": {
      "Type": "Wait",
      "Seconds": 5,
      "Next": "WaitForCompletion"
    },
    "GetResults": {
      "Type": "Task",
      "Resource": "arn:aws:states:::aws-sdk:redshiftdata:getStatementResult",
      "Parameters": {
        "Id.$": "$.QuerySubmission.Id"
      },
      "End": true
    },
    "QueryFailed": {
      "Type": "Fail",
      "Error": "QueryExecutionFailed",
      "Cause": "Redshift query execution failed"
    }
  }
}
```

### 3. 쿼리 이력 관리

```bash
# 최근 실행된 쿼리 목록 조회
aws redshift-data list-statements \
  --status ALL \
  --region ap-northeast-2

# 특정 상태의 쿼리만 조회
aws redshift-data list-statements \
  --status FAILED \
  --region ap-northeast-2

# 실행 중인 쿼리 취소
aws redshift-data cancel-statement \
  --id d9b6c0c9-0747-4bf4-b142-e8883122f766 \
  --region ap-northeast-2
```

---

## 모범 사례/보안

### IAM 정책 최소 권한

Data API 호출에 필요한 최소 IAM 권한을 설정합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "redshift-data:ExecuteStatement",
        "redshift-data:BatchExecuteStatement",
        "redshift-data:DescribeStatement",
        "redshift-data:GetStatementResult",
        "redshift-data:ListStatements",
        "redshift-data:CancelStatement"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "redshift:GetClusterCredentials",
      "Resource": [
        "arn:aws:redshift:ap-northeast-2:123456789012:dbname:my-redshift-cluster/analytics",
        "arn:aws:redshift:ap-northeast-2:123456789012:dbuser:my-redshift-cluster/admin"
      ]
    }
  ]
}
```

### 성능 최적화

1. **EventBridge 연동**: 폴링 대신 EventBridge를 사용하여 완료 이벤트를 수신합니다.
2. **배치 실행 활용**: 관련 SQL을 배치로 묶어 트랜잭션 오버헤드를 줄입니다.
3. **결과 크기 제한**: SELECT에 LIMIT을 걸어 100MB 한도를 초과하지 않도록 합니다.
4. **파라미터 바인딩**: SQL Injection 방지와 함께 쿼리 캐시 활용률도 높입니다.

### 에러 핸들링

```bash
# 실패한 쿼리의 상세 에러 확인
aws redshift-data describe-statement \
  --id d9b6c0c9-0747-4bf4-b142-e8883122f766 \
  --query "{Status:Status,Error:Error,Duration:Duration,ResultRows:ResultRows}" \
  --region ap-northeast-2
```

---

## 관련 서비스 비교

| 항목 | Redshift Data API | JDBC/ODBC | Redshift Query Editor v2 |
|------|-------------------|-----------|-------------------------|
| 연결 방식 | HTTP (AWS API) | TCP (직접 연결) | 웹 브라우저 |
| 드라이버 필요 | 불필요 | 필요 | 불필요 |
| VPC 연결 필요 | 불필요 | 필요 | 불필요 |
| 인증 | IAM / Secrets Manager | DB 자격 증명 | IAM SSO |
| 실행 방식 | 비동기 | 동기 | 동기 (UI) |
| 최대 결과 크기 | 100MB | 무제한 | UI 제한 |
| 적합 환경 | 서버리스, 자동화 | 전통적 앱, BI 도구 | 대화형 분석 |
| Lambda 호환 | 최적 | VPC 설정 필요 | 해당 없음 |

---

## 요약

Amazon Redshift Data API는 서버리스 환경에서 Redshift를 활용하기 위한 필수 인터페이스입니다.

1. **드라이버/VPC 불필요**: JDBC/ODBC 드라이버 설치나 VPC 네트워크 설정 없이 HTTP API로 쿼리를 실행합니다.
2. **비동기 실행 모델**: 쿼리 제출 후 Statement ID로 상태 확인 및 결과 조회를 분리합니다.
3. **IAM 기반 인증**: DB 비밀번호 관리 부담을 제거하고, IAM 정책으로 세밀한 접근 제어를 적용합니다.
4. **EventBridge 연동**: 쿼리 완료 이벤트를 수신하여 폴링 없는 비동기 워크플로우를 구성합니다.
5. **Lambda/Step Functions 최적**: 서버리스 컴퓨팅과의 조합이 자연스럽고 효율적입니다.
6. **배치 실행**: 최대 40개의 SQL을 단일 트랜잭션으로 실행하여 복잡한 ETL 작업을 처리합니다.

Data API는 기존 JDBC/ODBC를 완전히 대체하는 것이 아니라, 서버리스 및 자동화 시나리오에 최적화된 보완적 인터페이스입니다. 대화형 분석에는 Query Editor v2, BI 도구 연결에는 JDBC/ODBC, 자동화에는 Data API를 사용하는 것이 최적의 조합입니다.