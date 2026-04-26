<!-- infographic-hero -->
![AWS Systems Manager OpsItems 핵심 요약](figures/infographic.svg)

*Figure: AWS Systems Manager OpsItems 한 장 요약 인포그래픽*

# AWS Systems Manager OpsItems 심층 분석

## 개요

AWS Systems Manager OpsItems는 AWS 환경에서 발생하는 운영 이슈(Operational Issues)를 중앙 집중적으로 추적, 조사, 해결할 수 있도록 설계된 서비스입니다. OpsItems는 Systems Manager의 OpsCenter 콘솔 내에서 관리되며, 각 OpsItem은 특정 운영 문제에 대한 컨텍스트 정보를 포함합니다.

클라우드 인프라를 운영하다 보면 EC2 인스턴스 장애, RDS 성능 저하, Lambda 함수 오류 등 다양한 운영 이슈가 발생합니다. 이러한 이슈들을 개별적으로 추적하면 관리가 분산되고, 이슈 간의 상관관계를 파악하기 어렵습니다. OpsItems는 이 문제를 해결하기 위해 모든 운영 이슈를 단일 대시보드에서 관리할 수 있는 프레임워크를 제공합니다.

OpsItems는 단순한 티켓 시스템이 아닙니다. AWS 서비스와 깊이 통합되어 있어 CloudWatch 경보, EventBridge 이벤트, Config 규칙 위반 등에서 자동으로 OpsItem을 생성할 수 있으며, Systems Manager Automation 런북과 연동하여 자동 해결 워크플로우를 구성할 수 있습니다.

### OpsItems의 핵심 가치

- **중앙 집중 관리**: 여러 AWS 서비스에서 발생하는 운영 이슈를 하나의 인터페이스에서 관리합니다.
- **컨텍스트 보존**: 관련 리소스, 런북, 관련 OpsItem 등의 정보를 함께 저장하여 문제 해결에 필요한 맥락을 보존합니다.
- **자동화 연동**: EventBridge, CloudWatch와 연동하여 이슈 생성을 자동화하고, Automation 런북으로 해결을 자동화합니다.
- **교차 계정 관리**: AWS Organizations와 통합하여 여러 계정의 OpsItem을 하나의 관리 계정에서 볼 수 있습니다.

## 핵심 기능

### 1. OpsItem 생성 및 관리

OpsItem은 수동으로 생성하거나 다른 AWS 서비스에서 자동으로 생성할 수 있습니다. 각 OpsItem에는 다음과 같은 속성이 포함됩니다.

- **제목(Title)**: 운영 이슈를 간결하게 설명하는 제목
- **소스(Source)**: OpsItem을 생성한 서비스(예: CloudWatch, SSM, 수동)
- **심각도(Severity)**: 1(Critical)부터 4(Low)까지의 심각도 수준
- **상태(Status)**: Open, InProgress, Resolved, Closed 등
- **설명(Description)**: 이슈에 대한 상세 설명
- **관련 리소스(Related Resources)**: 이슈와 관련된 AWS 리소스 ARN
- **운영 데이터(Operational Data)**: 키-값 쌍으로 저장되는 추가 메타데이터

AWS CLI를 사용하여 OpsItem을 생성하는 예제입니다.

```bash
# OpsItem 수동 생성
aws ssm create-ops-item \
  --title "EC2 인스턴스 CPU 사용률 90% 초과" \
  --description "프로덕션 웹 서버 i-0abc123def456의 CPU 사용률이 지속적으로 90%를 초과하고 있습니다. 스케일 아웃 또는 인스턴스 타입 업그레이드를 검토해야 합니다." \
  --source "Manual" \
  --severity "2" \
  --priority 1 \
  --operational-data '{"instance-id":{"Value":"i-0abc123def456","Type":"SearchableString"},"environment":{"Value":"production","Type":"SearchableString"}}' \
  --tags Key=Team,Value=DevOps Key=Environment,Value=Production
```

### 2. 자동 OpsItem 생성 (EventBridge 연동)

EventBridge 규칙을 통해 특정 이벤트 발생 시 자동으로 OpsItem을 생성할 수 있습니다. 이를 통해 수동 개입 없이 운영 이슈를 추적할 수 있습니다.

```bash
# EventBridge 규칙 생성: EC2 인스턴스 상태 변경 시 OpsItem 자동 생성
aws events put-rule \
  --name "ec2-state-change-to-opsitem" \
  --event-pattern '{
    "source": ["aws.ec2"],
    "detail-type": ["EC2 Instance State-change Notification"],
    "detail": {
      "state": ["stopped", "terminated"]
    }
  }' \
  --state ENABLED

# 규칙 대상으로 SSM OpsItem 생성 설정
aws events put-targets \
  --rule "ec2-state-change-to-opsitem" \
  --targets '[{
    "Id": "create-opsitem",
    "Arn": "arn:aws:ssm:ap-northeast-2:123456789012:opsitem",
    "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeSSMRole",
    "InputTransformer": {
      "InputPathsMap": {
        "instance": "$.detail.instance-id",
        "state": "$.detail.state"
      },
      "InputTemplate": "{\"title\":\"EC2 인스턴스 <instance> 상태 변경: <state>\",\"description\":\"EC2 인스턴스가 예기치 않게 상태가 변경되었습니다.\",\"source\":\"EC2\",\"severity\":\"2\"}"
    }
  }]'
```

### 3. CloudWatch 경보 연동

CloudWatch 경보가 ALARM 상태로 전환될 때 자동으로 OpsItem을 생성하도록 구성할 수 있습니다.

```bash
# CloudWatch 경보 생성 시 OpsItem 자동 생성 활성화
aws cloudwatch put-metric-alarm \
  --alarm-name "high-cpu-production" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 90 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 3 \
  --dimensions Name=InstanceId,Value=i-0abc123def456 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:ops-alerts
```

CloudWatch에서 OpsItem을 자동 생성하려면 Systems Manager 콘솔의 OpsCenter 설정에서 CloudWatch 소스를 활성화해야 합니다.

```bash
# OpsCenter에서 CloudWatch 소스 활성화 상태 확인
aws ssm get-service-setting \
  --setting-id arn:aws:ssm:ap-northeast-2:123456789012:servicesetting/ssm/opsitem/EC2
```

### 4. OpsItem 조회 및 필터링

OpsItem을 다양한 조건으로 조회하고 필터링할 수 있습니다.

```bash
# 열린 상태의 OpsItem 조회
aws ssm describe-ops-items \
  --ops-item-filters '[{"Key":"Status","Values":["Open"],"Operator":"Equal"}]'

# 심각도 1(Critical) OpsItem 조회
aws ssm describe-ops-items \
  --ops-item-filters '[{"Key":"Severity","Values":["1"],"Operator":"Equal"}]'

# 특정 소스에서 생성된 OpsItem 조회
aws ssm describe-ops-items \
  --ops-item-filters '[{"Key":"Source","Values":["CloudWatch"],"Operator":"Equal"}]'

# 복합 필터: 열린 상태이면서 심각도 1 또는 2인 OpsItem
aws ssm describe-ops-items \
  --ops-item-filters '[
    {"Key":"Status","Values":["Open","InProgress"],"Operator":"Equal"},
    {"Key":"Severity","Values":["1","2"],"Operator":"Equal"}
  ]'
```

### 5. 관련 리소스 및 런북 연결

OpsItem에 관련 리소스와 해결을 위한 Automation 런북을 연결할 수 있습니다.

```bash
# OpsItem에 관련 리소스 추가
aws ssm update-ops-item \
  --ops-item-id "oi-0abc123456" \
  --related-ops-items '[{"OpsItemId":"oi-0def789012"}]'

# OpsItem 상태 업데이트
aws ssm update-ops-item \
  --ops-item-id "oi-0abc123456" \
  --status "InProgress"

# OpsItem에 운영 데이터 추가
aws ssm update-ops-item \
  --ops-item-id "oi-0abc123456" \
  --operational-data '{"runbook-id":{"Value":"AWS-RestartEC2Instance","Type":"SearchableString"},"assigned-to":{"Value":"devops-team","Type":"SearchableString"}}'
```

## 아키텍처/동작 원리

### OpsCenter 아키텍처 구성

OpsItems는 Systems Manager OpsCenter의 핵심 구성요소입니다. 전체 아키텍처는 다음과 같이 구성됩니다.

```
[이벤트 소스]                    [OpsCenter]               [해결 자동화]
+------------------+         +------------------+      +------------------+
| CloudWatch Alarm | ------> |                  |      |                  |
| EventBridge Rule | ------> |    OpsItems      | ---> | SSM Automation   |
| Config Rules     | ------> |    Dashboard     |      | RunBooks         |
| Security Hub     | ------> |                  |      |                  |
| Manual Creation  | ------> |                  |      +------------------+
+------------------+         +------------------+
                                    |
                             +------+------+
                             |             |
                        [관련 리소스]  [운영 데이터]
                        - EC2 ARN     - 키-값 메타데이터
                        - RDS ARN     - 검색 가능 문자열
                        - Lambda ARN  - 사용자 정의 데이터
```

### OpsItem 생명주기

OpsItem은 다음과 같은 생명주기를 가집니다.

1. **생성(Created)**: 이벤트 소스에 의해 자동 생성되거나 수동으로 생성됩니다.
2. **Open 상태**: 생성 직후의 기본 상태입니다. 아직 누구도 이 이슈를 처리하지 않은 상태입니다.
3. **InProgress 상태**: 운영 담당자가 이슈를 확인하고 처리를 시작한 상태입니다.
4. **Resolved 상태**: 이슈가 해결된 상태입니다. 검증이 필요할 수 있습니다.
5. **Closed 상태**: 이슈가 완전히 종료된 상태입니다.

### 중복 제거(Deduplication) 메커니즘

OpsItems는 동일한 이슈에 대해 중복 OpsItem이 생성되는 것을 방지하는 중복 제거 기능을 제공합니다. 이는 `OperationalData` 필드의 특정 키를 기반으로 동작합니다.

```bash
# 중복 제거를 위한 키를 포함하여 OpsItem 생성
aws ssm create-ops-item \
  --title "Lambda 함수 오류율 증가" \
  --description "payment-processor Lambda 함수의 오류율이 5%를 초과했습니다." \
  --source "CloudWatch" \
  --severity "2" \
  --operational-data '{
    "/aws/dedup":{"Value":"{\"dedupString\":\"lambda-payment-processor-error-rate\"}","Type":"SearchableString"}
  }'
```

`/aws/dedup` 키를 사용하면, 동일한 `dedupString` 값을 가진 OpsItem이 이미 Open 또는 InProgress 상태로 존재할 경우 새로운 OpsItem이 생성되지 않습니다.

### 교차 계정 OpsItem 관리

AWS Organizations를 사용하는 환경에서는 여러 계정의 OpsItem을 중앙 관리 계정에서 조회하고 관리할 수 있습니다. 이를 위해서는 다음과 같은 설정이 필요합니다.

1. 관리 계정에서 Systems Manager Explorer를 활성화합니다.
2. 리소스 데이터 동기화(Resource Data Sync)를 설정합니다.
3. 멤버 계정에 적절한 IAM 역할을 배포합니다.

```bash
# 리소스 데이터 동기화 생성 (관리 계정에서 실행)
aws ssm create-resource-data-sync \
  --sync-name "organization-ops-sync" \
  --sync-type "SyncFromSource" \
  --sync-source '{
    "SourceType": "SingleAccountMultiRegions",
    "SourceRegions": ["ap-northeast-2", "us-east-1", "eu-west-1"],
    "IncludeFutureRegions": true
  }'
```

## 실전 활용

### 사례 1: EC2 인스턴스 자동 복구 워크플로우

프로덕션 환경에서 EC2 인스턴스가 비정상적으로 중지되었을 때, OpsItem을 자동으로 생성하고 Automation 런북으로 복구하는 워크플로우를 구성할 수 있습니다.

```bash
# 1단계: Automation 런북으로 EC2 인스턴스 재시작
aws ssm start-automation-execution \
  --document-name "AWS-RestartEC2Instance" \
  --parameters '{"InstanceId":["i-0abc123def456"]}'

# 2단계: 실행 결과 확인
aws ssm describe-automation-executions \
  --filters '[{"Key":"ExecutionId","Values":["execution-id-here"]}]'

# 3단계: OpsItem 상태 업데이트
aws ssm update-ops-item \
  --ops-item-id "oi-0abc123456" \
  --status "Resolved" \
  --operational-data '{"resolution":{"Value":"자동 복구 런북으로 인스턴스를 재시작했습니다.","Type":"SearchableString"}}'
```

### 사례 2: 비용 이상 탐지 OpsItem

AWS Budgets와 연동하여 예산 초과 시 자동으로 OpsItem을 생성하는 패턴입니다.

```bash
# Budget 초과 알림을 SNS로 발송하고, Lambda를 통해 OpsItem 생성
# Lambda 함수에서 사용할 boto3 코드 예시
```

```python
import boto3
import json

def lambda_handler(event, context):
    ssm = boto3.client('ssm')
    
    # SNS 메시지에서 Budget 정보 추출
    message = json.loads(event['Records'][0]['Sns']['Message'])
    budget_name = message.get('budgetName', 'Unknown')
    actual_amount = message.get('actualAmount', '0')
    threshold = message.get('threshold', '0')
    
    response = ssm.create_ops_item(
        Title=f'예산 초과 경고: {budget_name}',
        Description=f'Budget "{budget_name}"이 임계값을 초과했습니다.\n'
                    f'실제 사용량: ${actual_amount}\n'
                    f'임계값: {threshold}%',
        Source='Budget',
        Severity='2',
        OperationalData={
            'budget-name': {
                'Value': budget_name,
                'Type': 'SearchableString'
            },
            'actual-amount': {
                'Value': str(actual_amount),
                'Type': 'SearchableString'
            },
            '/aws/dedup': {
                'Value': json.dumps({'dedupString': f'budget-alert-{budget_name}'}),
                'Type': 'SearchableString'
            }
        },
        Tags=[
            {'Key': 'Category', 'Value': 'Cost'},
            {'Key': 'AutoGenerated', 'Value': 'true'}
        ]
    )
    
    return {
        'statusCode': 200,
        'opsItemId': response['OpsItemId']
    }
```

### 사례 3: 보안 이벤트 통합 대시보드

Security Hub 발견 항목을 OpsItem으로 변환하여 보안 이슈도 OpsCenter에서 통합 관리할 수 있습니다.

```bash
# Security Hub 소스 활성화
aws ssm update-service-setting \
  --setting-id "arn:aws:ssm:ap-northeast-2:123456789012:servicesetting/ssm/opsitem/securityhub" \
  --setting-value "true"

# Security Hub에서 생성된 OpsItem 조회
aws ssm describe-ops-items \
  --ops-item-filters '[{"Key":"Source","Values":["SecurityHub"],"Operator":"Equal"}]'
```

### 사례 4: OpsItem 보고서 자동화

주기적으로 OpsItem 현황을 보고서로 생성하는 스크립트입니다.

```bash
# 지난 7일간 생성된 OpsItem 통계 조회
aws ssm describe-ops-items \
  --ops-item-filters '[
    {"Key":"CreatedTime","Values":["2024-01-01T00:00:00Z"],"Operator":"GreaterThan"}
  ]' \
  --max-results 50 \
  --query 'OpsItemSummaries[].{Id:OpsItemId,Title:Title,Status:Status,Severity:Severity,Source:Source}' \
  --output table
```

## 모범 사례/보안

### IAM 권한 최소화

OpsItems에 대한 접근은 세밀하게 제어해야 합니다. 다음은 읽기 전용 정책의 예시입니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:DescribeOpsItems",
        "ssm:GetOpsItem",
        "ssm:GetOpsSummary"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": [
        "ssm:DeleteOpsItem",
        "ssm:UpdateOpsItem"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:PrincipalTag/Role": "OpsAdmin"
        }
      }
    }
  ]
}
```

### 운영 데이터 보안

OpsItem의 운영 데이터에 민감한 정보를 저장하지 않도록 주의해야 합니다. 비밀번호, API 키, 개인정보 등은 절대 운영 데이터에 포함하지 않아야 합니다. 대신 Systems Manager Parameter Store(SecureString)를 참조하는 방식을 사용합니다.

### 알림 폭주(Alert Fatigue) 방지

- **중복 제거 활용**: `/aws/dedup` 키를 적극 사용하여 동일한 이슈에 대한 중복 OpsItem 생성을 방지합니다.
- **심각도 기준 명확화**: 팀 내에서 심각도 1~4의 기준을 명확히 정의하고 문서화합니다.
- **자동 해결 구성**: 자주 발생하는 알려진 이슈는 Automation 런북과 연동하여 자동으로 해결하도록 구성합니다.

### 태깅 전략

OpsItem에 일관된 태그를 적용하여 분류와 보고를 용이하게 합니다.

```bash
# 태그 기반 OpsItem 관리 예시
aws ssm create-ops-item \
  --title "데이터베이스 복제 지연" \
  --description "RDS Aurora 읽기 복제본의 복제 지연이 60초를 초과했습니다." \
  --source "CloudWatch" \
  --severity "2" \
  --tags \
    Key=Team,Value=DBA \
    Key=Service,Value=OrderSystem \
    Key=Environment,Value=Production \
    Key=Category,Value=Performance
```

### 보존 정책

OpsItems는 기본적으로 삭제되지 않습니다. 오래된 OpsItem이 쌓이면 관리가 어려워질 수 있으므로, 정기적으로 Resolved/Closed 상태의 오래된 OpsItem을 정리하는 프로세스를 수립해야 합니다.

## 관련 서비스 비교

### OpsItems vs CloudWatch Alarms

| 항목 | OpsItems | CloudWatch Alarms |
|------|----------|-------------------|
| 목적 | 운영 이슈 추적 및 관리 | 메트릭 기반 임계값 모니터링 |
| 상태 관리 | Open/InProgress/Resolved/Closed | OK/ALARM/INSUFFICIENT_DATA |
| 컨텍스트 | 관련 리소스, 런북, 운영 데이터 포함 | 메트릭 데이터 중심 |
| 자동 해결 | Automation 런북 연동 | SNS/Lambda 트리거 |
| 히스토리 | 전체 이력 보존 | 제한된 이력 |

CloudWatch Alarms는 모니터링 도구이고, OpsItems는 이슈 관리 도구입니다. 두 서비스를 함께 사용하면 모니터링에서 이슈 해결까지의 전체 워크플로우를 구성할 수 있습니다.

### OpsItems vs AWS Health Dashboard

| 항목 | OpsItems | AWS Health Dashboard |
|------|----------|---------------------|
| 범위 | 사용자 정의 운영 이슈 | AWS 서비스 상태 |
| 생성 주체 | 사용자/자동화 규칙 | AWS |
| 커스터마이징 | 완전 커스터마이징 가능 | 읽기 전용 |
| 해결 워크플로우 | Automation 런북 연동 | 없음 |

### OpsItems vs Jira/ServiceNow

| 항목 | OpsItems | Jira/ServiceNow |
|------|----------|------------------|
| AWS 통합 | 네이티브 통합 | 플러그인/커넥터 필요 |
| 비용 | 추가 비용 없음 | 별도 라이선스 비용 |
| 기능 범위 | AWS 운영 이슈 중심 | 범용 ITSM |
| 커스터마이징 | 제한적 | 매우 유연 |
| 워크플로우 | 기본 상태 관리 | 복잡한 워크플로우 지원 |

대규모 조직에서는 OpsItems와 Jira/ServiceNow를 함께 사용하는 경우가 많습니다. OpsItems에서 1차적으로 AWS 운영 이슈를 포착하고, 중요한 이슈는 ITSM 도구로 에스컬레이션하는 패턴입니다.

## 요약

AWS Systems Manager OpsItems는 AWS 환경에서 발생하는 운영 이슈를 체계적으로 관리하기 위한 핵심 도구입니다. CloudWatch, EventBridge, Security Hub 등 다양한 AWS 서비스와의 네이티브 통합을 통해 이슈를 자동으로 포착하고, Automation 런북과 연동하여 해결까지 자동화할 수 있습니다.

핵심 포인트를 정리하면 다음과 같습니다.

- OpsItems는 운영 이슈의 전체 생명주기(생성-추적-해결-종료)를 관리합니다.
- 중복 제거 메커니즘으로 알림 폭주를 방지할 수 있습니다.
- 교차 계정/교차 리전 관리가 가능하여 대규모 환경에서도 유용합니다.
- IAM 정책으로 세밀한 접근 제어가 가능하며, 운영 데이터에 민감 정보를 저장하지 않도록 주의해야 합니다.
- CloudWatch Alarms와 결합하면 모니터링에서 이슈 해결까지의 완전한 운영 워크플로우를 구현할 수 있습니다.

OpsItems를 효과적으로 활용하기 위해서는 팀 내 심각도 기준을 명확히 정의하고, 자주 발생하는 이슈에 대한 자동 해결 런북을 사전에 준비하며, 일관된 태깅 전략을 수립하는 것이 중요합니다.