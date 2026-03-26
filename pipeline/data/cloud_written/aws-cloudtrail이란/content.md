## 개요

AWS CloudTrail은 AWS 계정에서 발생하는 모든 API 호출과 관련 활동을 기록하는 거버넌스, 컴플라이언스, 감사 서비스입니다. AWS Management Console, AWS CLI, AWS SDK, 기타 AWS 서비스를 통해 수행되는 모든 작업이 CloudTrail 이벤트로 기록됩니다.

클라우드 환경에서 "누가, 언제, 어디서, 무엇을, 어떻게" 했는지를 추적하는 것은 보안과 규정 준수의 기본입니다. CloudTrail은 이러한 감사 추적(audit trail)을 자동으로 생성합니다. EC2 인스턴스를 시작한 사람, S3 버킷 정책을 변경한 사람, IAM 역할을 생성한 사람 등 모든 API 활동의 주체, 시간, 소스 IP, 파라미터, 결과를 기록합니다.

CloudTrail은 AWS 계정 생성 시 기본적으로 활성화되어 있으며, 최근 90일간의 관리 이벤트(Management Events)를 무료로 조회할 수 있습니다. 장기 보존이나 S3 전송, 데이터 이벤트 기록 등 고급 기능을 사용하려면 트레일(Trail) 또는 CloudTrail Lake를 설정해야 합니다.

보안 인시던트 대응, 규정 준수 감사, 운영 문제 해결, 비정상 활동 탐지 등 다양한 시나리오에서 CloudTrail은 핵심적인 역할을 수행합니다. AWS Well-Architected Framework의 보안 기둥에서도 CloudTrail 활성화를 필수 사항으로 권장하고 있습니다.

## 핵심 기능

### 이벤트 유형

CloudTrail은 세 가지 유형의 이벤트를 기록합니다.

**1. 관리 이벤트 (Management Events)**

AWS 리소스에 대한 관리(제어) 작업을 기록합니다. 기본적으로 모든 관리 이벤트가 기록됩니다.

예시:
- EC2 인스턴스 시작/중지 (RunInstances, StopInstances)
- IAM 사용자/역할 생성 (CreateUser, CreateRole)
- S3 버킷 생성/삭제 (CreateBucket, DeleteBucket)
- VPC 보안 그룹 변경 (AuthorizeSecurityGroupIngress)
- CloudFormation 스택 배포 (CreateStack)

관리 이벤트는 읽기 이벤트(Describe, Get, List 등)와 쓰기 이벤트(Create, Update, Delete 등)로 구분됩니다.

**2. 데이터 이벤트 (Data Events)**

AWS 리소스 내의 데이터 수준 작업을 기록합니다. 기본적으로 비활성화되어 있으며, 별도로 활성화해야 합니다. 대량으로 발생할 수 있어 추가 비용이 발생합니다.

예시:
- S3 객체 읽기/쓰기 (GetObject, PutObject)
- Lambda 함수 호출 (Invoke)
- DynamoDB 항목 읽기/쓰기 (GetItem, PutItem)
- EBS 스냅샷 직접 접근 API

**3. 인사이트 이벤트 (Insights Events)**

비정상적인 API 활동 패턴을 자동으로 감지합니다. 예를 들어, 평소 대비 비정상적으로 많은 TerminateInstances API 호출이 발생하면 인사이트 이벤트가 생성됩니다.

### 트레일 (Trail)

트레일은 CloudTrail 이벤트를 S3 버킷에 지속적으로 전달하는 설정입니다. 단일 리전 또는 모든 리전에 적용할 수 있습니다.

### CloudTrail Lake

CloudTrail Lake는 이벤트를 SQL 기반으로 쿼리할 수 있는 관리형 데이터 레이크입니다. S3 + Athena 조합보다 설정이 간편하며, 최대 7년까지 이벤트를 보존할 수 있습니다.

## 아키텍처/동작 원리

### CloudTrail 이벤트 흐름

1. 사용자 또는 서비스가 AWS API를 호출합니다.
2. API 엔드포인트가 요청을 처리합니다.
3. CloudTrail이 API 호출 메타데이터를 이벤트로 기록합니다.
4. 이벤트는 이벤트 이력(Event History)에 저장됩니다 (90일 무료).
5. 트레일이 설정된 경우, 이벤트가 S3 버킷으로 전달됩니다.
6. CloudWatch Logs로도 전달 설정이 가능합니다.
7. SNS 알림을 설정할 수 있습니다.

### 트레일 생성

```bash
# 모든 리전에 적용되는 트레일 생성
aws cloudtrail create-trail \
  --name production-audit-trail \
  --s3-bucket-name my-cloudtrail-logs-bucket \
  --s3-key-prefix cloudtrail \
  --is-multi-region-trail \
  --include-global-service-events \
  --enable-log-file-validation \
  --kms-key-id arn:aws:kms:ap-northeast-2:123456789012:key/12345678-1234-1234-1234-123456789012 \
  --cloud-watch-logs-log-group-arn arn:aws:logs:ap-northeast-2:123456789012:log-group:CloudTrail/production:* \
  --cloud-watch-logs-role-arn arn:aws:iam::123456789012:role/CloudTrail_CloudWatchLogs_Role

# 트레일 로깅 시작
aws cloudtrail start-logging \
  --name production-audit-trail
```

```bash
# 트레일 상태 확인
aws cloudtrail get-trail-status \
  --name production-audit-trail

# 트레일 상세 정보 조회
aws cloudtrail describe-trails \
  --trail-name-list production-audit-trail
```

### 이벤트 구조

CloudTrail 이벤트의 핵심 필드를 살펴보겠습니다.

```json
{
  "eventVersion": "1.08",
  "userIdentity": {
    "type": "AssumedRole",
    "principalId": "AROAEXAMPLEID:admin-session",
    "arn": "arn:aws:sts::123456789012:assumed-role/AdminRole/admin-session",
    "accountId": "123456789012",
    "sessionContext": {
      "sessionIssuer": {
        "type": "Role",
        "principalId": "AROAEXAMPLEID",
        "arn": "arn:aws:iam::123456789012:role/AdminRole",
        "accountId": "123456789012",
        "userName": "AdminRole"
      }
    }
  },
  "eventTime": "2024-01-15T09:30:00Z",
  "eventSource": "ec2.amazonaws.com",
  "eventName": "TerminateInstances",
  "awsRegion": "ap-northeast-2",
  "sourceIPAddress": "203.0.113.50",
  "userAgent": "aws-cli/2.15.0 Python/3.11.6",
  "requestParameters": {
    "instancesSet": {
      "items": [{"instanceId": "i-0123456789abcdef0"}]
    }
  },
  "responseElements": {
    "instancesSet": {
      "items": [{
        "instanceId": "i-0123456789abcdef0",
        "currentState": {"code": 32, "name": "shutting-down"}
      }]
    }
  },
  "eventID": "12345678-1234-1234-1234-123456789012",
  "eventType": "AwsApiCall",
  "readOnly": false
}
```

### 데이터 이벤트 설정

```bash
# S3 데이터 이벤트 기록 활성화
aws cloudtrail put-event-selectors \
  --trail-name production-audit-trail \
  --advanced-event-selectors '[
    {
      "Name": "S3DataEvents",
      "FieldSelectors": [
        {"Field": "eventCategory", "Equals": ["Data"]},
        {"Field": "resources.type", "Equals": ["AWS::S3::Object"]},
        {"Field": "resources.ARN", "StartsWith": ["arn:aws:s3:::sensitive-data-bucket/"]}
      ]
    },
    {
      "Name": "LambdaDataEvents",
      "FieldSelectors": [
        {"Field": "eventCategory", "Equals": ["Data"]},
        {"Field": "resources.type", "Equals": ["AWS::Lambda::Function"]}
      ]
    }
  ]'
```

### CloudTrail 인사이트 설정

```bash
# 인사이트 이벤트 활성화
aws cloudtrail put-insight-selectors \
  --trail-name production-audit-trail \
  --insight-selectors '[{"InsightType": "ApiCallRateInsight"}, {"InsightType": "ApiErrorRateInsight"}]'
```

## 실전 활용

### 사례 1: 보안 인시던트 조사

보안 인시던트 발생 시 CloudTrail을 활용하여 원인을 추적합니다.

```bash
# 특정 시간 범위에서 특정 사용자의 활동 조회
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=suspicious-user \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --max-results 50

# 특정 이벤트명으로 조회 (예: 보안 그룹 변경)
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AuthorizeSecurityGroupIngress \
  --start-time 2024-01-14T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z
```

### 사례 2: CloudWatch Alarms 기반 보안 알림

CloudTrail 로그를 CloudWatch Logs로 전송하고, 메트릭 필터를 설정하여 보안 관련 이벤트를 실시간으로 모니터링합니다.

```bash
# 루트 계정 사용 감지 메트릭 필터
aws logs put-metric-filter \
  --log-group-name CloudTrail/production \
  --filter-name RootAccountUsage \
  --filter-pattern '{$.userIdentity.type = "Root" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != "AwsServiceEvent"}' \
  --metric-transformations '[{
    "metricName": "RootAccountUsageCount",
    "metricNamespace": "CloudTrailMetrics",
    "metricValue": "1",
    "defaultValue": 0
  }]'

# 알람 설정
aws cloudwatch put-metric-alarm \
  --alarm-name root-account-usage \
  --metric-name RootAccountUsageCount \
  --namespace CloudTrailMetrics \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:security-alerts
```

```bash
# 콘솔 로그인 실패 감지
aws logs put-metric-filter \
  --log-group-name CloudTrail/production \
  --filter-name ConsoleSignInFailures \
  --filter-pattern '{($.eventName = ConsoleLogin) && ($.errorMessage = "Failed authentication")}' \
  --metric-transformations '[{
    "metricName": "ConsoleSignInFailureCount",
    "metricNamespace": "CloudTrailMetrics",
    "metricValue": "1",
    "defaultValue": 0
  }]'

# 무단 API 호출 감지
aws logs put-metric-filter \
  --log-group-name CloudTrail/production \
  --filter-name UnauthorizedAPICalls \
  --filter-pattern '{($.errorCode = "*UnauthorizedAccess*") || ($.errorCode = "AccessDenied*")}' \
  --metric-transformations '[{
    "metricName": "UnauthorizedAPICallCount",
    "metricNamespace": "CloudTrailMetrics",
    "metricValue": "1",
    "defaultValue": 0
  }]'
```

### 사례 3: CloudTrail Lake를 활용한 고급 쿼리

```bash
# CloudTrail Lake 이벤트 데이터 스토어 생성
aws cloudtrail create-event-data-store \
  --name "security-audit-store" \
  --retention-period 365 \
  --multi-region-enabled \
  --organization-enabled false \
  --advanced-event-selectors '[{
    "Name": "ManagementEvents",
    "FieldSelectors": [
      {"Field": "eventCategory", "Equals": ["Management"]}
    ]
  }]'
```

```bash
# CloudTrail Lake SQL 쿼리 실행
aws cloudtrail start-query \
  --query-statement "SELECT eventTime, userIdentity.arn, eventName, sourceIPAddress, errorCode FROM security-audit-store WHERE eventTime > '2024-01-01 00:00:00' AND eventName = 'DeleteBucket' ORDER BY eventTime DESC"

# 쿼리 결과 확인
aws cloudtrail get-query-results \
  --event-data-store arn:aws:cloudtrail:ap-northeast-2:123456789012:eventdatastore/EXAMPLE-store-id \
  --query-id EXAMPLE-query-id
```

### 사례 4: 멀티 계정 조직 트레일

AWS Organizations를 사용하는 경우, 조직 전체에 적용되는 트레일을 생성할 수 있습니다.

```bash
# 조직 트레일 생성 (관리 계정에서 실행)
aws cloudtrail create-trail \
  --name organization-audit-trail \
  --s3-bucket-name org-cloudtrail-central-logs \
  --is-organization-trail \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --kms-key-id arn:aws:kms:ap-northeast-2:111111111111:key/org-trail-key
```

## 모범 사례/보안

### 필수 보안 설정

1. **로그 파일 무결성 검증**: `--enable-log-file-validation`을 반드시 활성화하여 로그 파일의 변조를 감지합니다.
2. **S3 버킷 보안**: CloudTrail 로그 버킷에 대한 접근을 엄격히 제한하고, MFA Delete를 활성화합니다.
3. **KMS 암호화**: 로그 파일을 고객 관리형 KMS 키로 암호화합니다.
4. **멀티 리전 트레일**: 모든 리전의 활동을 기록하도록 멀티 리전 트레일을 설정합니다.
5. **로그 파일 변경 불가**: S3 Object Lock을 활용하여 로그 파일이 삭제/수정되지 않도록 합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AWSCloudTrailAclCheck",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudtrail.amazonaws.com"
      },
      "Action": "s3:GetBucketAcl",
      "Resource": "arn:aws:s3:::my-cloudtrail-logs-bucket"
    },
    {
      "Sid": "AWSCloudTrailWrite",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudtrail.amazonaws.com"
      },
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::my-cloudtrail-logs-bucket/cloudtrail/AWSLogs/*",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-acl": "bucket-owner-full-control",
          "aws:SourceArn": "arn:aws:cloudtrail:ap-northeast-2:123456789012:trail/production-audit-trail"
        }
      }
    },
    {
      "Sid": "DenyUnencryptedObjectUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::my-cloudtrail-logs-bucket/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}
```

### CIS AWS Foundations Benchmark 권장 사항

CloudTrail 관련 CIS 벤치마크 주요 항목입니다.

- 모든 리전에서 CloudTrail이 활성화되어 있어야 합니다.
- 로그 파일 무결성 검증이 활성화되어 있어야 합니다.
- CloudTrail 로그가 CloudWatch Logs로 전달되어야 합니다.
- S3 버킷 로깅이 활성화되어 있어야 합니다.
- CloudTrail 로그가 KMS로 암호화되어 있어야 합니다.

```bash
# 로그 파일 무결성 검증
aws cloudtrail validate-logs \
  --trail-arn arn:aws:cloudtrail:ap-northeast-2:123456789012:trail/production-audit-trail \
  --start-time 2024-01-14T00:00:00Z \
  --end-time 2024-01-15T00:00:00Z
```

## 관련 서비스 비교

| 항목 | CloudTrail | AWS Config | VPC Flow Logs | GuardDuty |
|------|-----------|-----------|--------------|----------|
| 기록 대상 | API 활동 | 리소스 구성 변경 | 네트워크 트래픽 | 위협 탐지 |
| 주요 목적 | 감사/컴플라이언스 | 구성 관리/규정 준수 | 네트워크 모니터링 | 보안 위협 탐지 |
| 데이터 형식 | JSON 이벤트 | 구성 스냅샷 | 플로우 레코드 | 보안 알림 |
| 분석 도구 | Athena, CloudTrail Lake | Config Rules | Athena, CloudWatch | GuardDuty 콘솔 |
| 실시간 알림 | CloudWatch Logs + Alarms | Config Rules + SNS | CloudWatch Alarms | SNS, EventBridge |
| 무료 티어 | 관리 이벤트 90일 | 없음 (규칙당 과금) | 없음 (로그 저장 비용) | 30일 무료 |

이 네 가지 서비스는 상호 보완적이며, AWS 보안 모범 사례에서는 네 가지를 모두 활성화할 것을 권장합니다.

## 요약

AWS CloudTrail은 AWS 계정의 모든 API 활동을 기록하는 감사 서비스로, 보안과 규정 준수의 기반입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **전체 API 기록**: AWS 계정에서 발생하는 모든 관리/데이터 이벤트를 기록합니다.
- **세 가지 이벤트 유형**: 관리 이벤트(기본), 데이터 이벤트(선택), 인사이트 이벤트(비정상 감지)를 지원합니다.
- **멀티 리전/멀티 계정**: 모든 리전과 조직 전체에 걸친 통합 감사가 가능합니다.
- **CloudTrail Lake**: SQL 기반 이벤트 쿼리로 고급 분석이 가능합니다.
- **실시간 모니터링**: CloudWatch Logs와 메트릭 필터를 통해 보안 이벤트를 실시간으로 감지합니다.
- **로그 무결성**: 로그 파일 검증을 통해 변조를 감지할 수 있습니다.
- **규정 준수**: CIS, PCI DSS, HIPAA 등 주요 규정 준수 프레임워크의 요구사항을 충족합니다.

CloudTrail은 AWS 보안 아키텍처의 가장 기본적이면서도 가장 중요한 서비스입니다. 모든 AWS 계정에서 멀티 리전 트레일을 설정하고, 로그 파일 무결성 검증과 KMS 암호화를 활성화하는 것이 첫 번째 보안 설정이 되어야 합니다.