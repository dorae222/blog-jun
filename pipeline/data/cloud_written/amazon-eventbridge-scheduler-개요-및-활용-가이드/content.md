## 개요

Amazon EventBridge Scheduler는 서버리스 작업 스케줄링을 위한 완전관리형 서비스입니다. 이 글에서는 기본적인 스케줄 생성을 넘어, 프로덕션 환경에서 EventBridge Scheduler를 효과적으로 활용하기 위한 고급 패턴과 아키텍처를 다룹니다.

EventBridge Scheduler가 기존 스케줄링 솔루션과 차별화되는 핵심 가치는 다음 세 가지입니다. 첫째, 수백만 개의 개별 스케줄을 관리할 수 있어 사용자별/테넌트별 개인화된 스케줄링이 가능합니다. 둘째, 범용 타겟(Universal Target)을 통해 거의 모든 AWS API를 스케줄 타겟으로 사용할 수 있습니다. 셋째, 일회성 스케줄과 자동 삭제 기능으로 이벤트 소싱 패턴과의 궁합이 뛰어납니다.

이 글에서는 이러한 특성을 활용한 실전 아키텍처 패턴, CloudFormation/Terraform을 통한 IaC 관리, 그리고 대규모 운영 시 고려해야 할 성능/비용 최적화 전략을 상세히 살펴보겠습니다.

## 핵심 기능

### 범용 타겟 (Universal Target) 심화

범용 타겟은 EventBridge Scheduler의 가장 강력한 기능 중 하나입니다. 템플릿화된 타겟(Lambda, Step Functions, SQS, SNS 등 주요 서비스)과 달리, 범용 타겟은 AWS SDK의 거의 모든 API 액션을 호출할 수 있습니다.

범용 타겟의 ARN 형식은 다음과 같습니다.

```
arn:aws:scheduler:::aws-sdk:{service}:{apiAction}
```

예를 들어, RDS 스냅샷을 생성하려면 다음과 같이 지정합니다.

```bash
# RDS 자동 스냅샷 생성 스케줄
aws scheduler create-schedule \
  --name "weekly-rds-snapshot" \
  --schedule-expression "cron(0 18 ? * FRI *)" \
  --schedule-expression-timezone "Asia/Seoul" \
  --target '{
    "Arn": "arn:aws:scheduler:::aws-sdk:rds:createDBSnapshot",
    "RoleArn": "arn:aws:iam::123456789012:role/SchedulerRDSRole",
    "Input": "{\"DbInstanceIdentifier\": \"prod-database\", \"DbSnapshotIdentifier\": \"weekly-snapshot-<aws.scheduler.execution-id>\"}"
  }' \
  --flexible-time-window '{"Mode": "FLEXIBLE", "MaximumWindowInMinutes": 30}'
```

### 스케줄 표현식 고급 패턴

Cron 표현식에서 자주 사용되는 고급 패턴을 정리하면 다음과 같습니다.

```bash
# 매월 첫 번째 월요일 오전 9시
"cron(0 0 ? * 2#1 *)"

# 매월 마지막 날 오후 11시
"cron(0 14 L * ? *)"

# 매 분기 첫 날 (1/1, 4/1, 7/1, 10/1) 오전 6시
"cron(0 21 1 1,4,7,10 ? *)"

# 평일(월-금) 업무 시간(9시-18시) 매 30분마다
"cron(0/30 0-9 ? * MON-FRI *)"
```

### 입력 템플릿과 컨텍스트 변수

EventBridge Scheduler는 타겟에 전달하는 입력 데이터에 컨텍스트 변수를 삽입할 수 있습니다.

- `<aws.scheduler.schedule-arn>`: 스케줄 ARN
- `<aws.scheduler.scheduled-time>`: 예정 실행 시간
- `<aws.scheduler.execution-id>`: 실행 고유 ID
- `<aws.scheduler.attempt-number>`: 현재 시도 번호

## 아키텍처/동작 원리

### 대규모 스케줄 관리 아키텍처

SaaS 플랫폼이나 멀티 테넌트 시스템에서 수만~수백만 개의 스케줄을 관리해야 하는 경우, 다음과 같은 아키텍처를 권장합니다.

**계층 구조 설계**

```
Schedule Groups (테넌트/환경별)
  ├── tenant-alpha-prod
  │   ├── report-daily-001
  │   ├── report-weekly-001
  │   └── cleanup-monthly-001
  ├── tenant-beta-prod
  │   ├── report-daily-001
  │   └── sync-hourly-001
  └── system-maintenance
      ├── db-snapshot-weekly
      └── log-rotation-daily
```

```bash
# 테넌트별 스케줄 그룹 생성
aws scheduler create-schedule-group \
  --name "tenant-alpha-prod" \
  --tags '[{"Key": "TenantId", "Value": "alpha"}, {"Key": "Environment", "Value": "production"}]'

# 그룹 내 스케줄 생성
aws scheduler create-schedule \
  --name "report-daily-001" \
  --group-name "tenant-alpha-prod" \
  --schedule-expression "cron(0 0 * * ? *)" \
  --schedule-expression-timezone "Asia/Seoul" \
  --target '{
    "Arn": "arn:aws:lambda:ap-northeast-2:123456789012:function:generate-tenant-report",
    "RoleArn": "arn:aws:iam::123456789012:role/SchedulerLambdaRole",
    "Input": "{\"tenantId\": \"alpha\", \"reportType\": \"daily\"}"
  }' \
  --flexible-time-window '{"Mode": "FLEXIBLE", "MaximumWindowInMinutes": 15}'
```

### Step Functions 연동 패턴

EventBridge Scheduler와 Step Functions를 연동하면, 스케줄 트리거 이후의 복잡한 워크플로우를 정의할 수 있습니다.

```bash
# Step Functions 상태 머신을 타겟으로 하는 스케줄
aws scheduler create-schedule \
  --name "etl-pipeline-daily" \
  --schedule-expression "cron(0 20 * * ? *)" \
  --schedule-expression-timezone "Asia/Seoul" \
  --target '{
    "Arn": "arn:aws:states:ap-northeast-2:123456789012:stateMachine:etl-pipeline",
    "RoleArn": "arn:aws:iam::123456789012:role/SchedulerStepFunctionsRole",
    "Input": "{\"source\": \"scheduler\", \"executionDate\": \"<aws.scheduler.scheduled-time>\"}"
  }' \
  --flexible-time-window '{"Mode": "OFF"}'
```

### 이벤트 소싱 패턴: 지연 처리 (Delayed Processing)

주문 후 30분 내 결제가 완료되지 않으면 자동 취소하는 패턴을 EventBridge Scheduler의 일회성 스케줄로 구현할 수 있습니다.

```python
import boto3
import json
from datetime import datetime, timedelta

def create_order_timeout_schedule(order_id: str, timeout_minutes: int = 30):
    """주문 타임아웃 스케줄을 생성합니다."""
    client = boto3.client('scheduler')
    
    cancel_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
    
    response = client.create_schedule(
        Name=f"order-timeout-{order_id}",
        GroupName='order-timeouts',
        ScheduleExpression=f"at({cancel_at.strftime('%Y-%m-%dT%H:%M:%S')})",
        Target={
            'Arn': 'arn:aws:lambda:ap-northeast-2:123456789012:function:cancel-unpaid-order',
            'RoleArn': 'arn:aws:iam::123456789012:role/SchedulerLambdaRole',
            'Input': json.dumps({
                'orderId': order_id,
                'reason': 'PAYMENT_TIMEOUT',
                'scheduledAt': cancel_at.isoformat()
            }),
            'RetryPolicy': {
                'MaximumRetryAttempts': 3,
                'MaximumEventAgeInSeconds': 600
            },
            'DeadLetterConfig': {
                'Arn': 'arn:aws:sqs:ap-northeast-2:123456789012:order-timeout-dlq'
            }
        },
        FlexibleTimeWindow={'Mode': 'OFF'},
        ActionAfterCompletion='DELETE'
    )
    
    return response['ScheduleArn']


def cancel_order_timeout_schedule(order_id: str):
    """결제 완료 시 타임아웃 스케줄을 삭제합니다."""
    client = boto3.client('scheduler')
    
    try:
        client.delete_schedule(
            Name=f"order-timeout-{order_id}",
            GroupName='order-timeouts'
        )
    except client.exceptions.ResourceNotFoundException:
        pass  # 이미 실행되었거나 삭제된 경우
```

## 실전 활용

### CloudFormation을 통한 IaC 관리

```yaml
# cloudformation-scheduler.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: EventBridge Scheduler Infrastructure

Resources:
  SchedulerExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: EventBridgeSchedulerExecutionRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: scheduler.amazonaws.com
            Action: sts:AssumeRole
            Condition:
              StringEquals:
                aws:SourceAccount: !Ref AWS::AccountId
      Policies:
        - PolicyName: InvokeLambda
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action: lambda:InvokeFunction
                Resource: !GetAtt ReportFunction.Arn

  MaintenanceGroup:
    Type: AWS::Scheduler::ScheduleGroup
    Properties:
      Name: system-maintenance
      Tags:
        - Key: Environment
          Value: production

  DailyReportSchedule:
    Type: AWS::Scheduler::Schedule
    Properties:
      Name: daily-report
      GroupName: !Ref MaintenanceGroup
      ScheduleExpression: 'cron(0 0 * * ? *)'
      ScheduleExpressionTimezone: 'Asia/Seoul'
      FlexibleTimeWindow:
        Mode: 'FLEXIBLE'
        MaximumWindowInMinutes: 15
      Target:
        Arn: !GetAtt ReportFunction.Arn
        RoleArn: !GetAtt SchedulerExecutionRole.Arn
        Input: '{"reportType": "daily"}'
        RetryPolicy:
          MaximumRetryAttempts: 3
          MaximumEventAgeInSeconds: 3600
        DeadLetterConfig:
          Arn: !GetAtt SchedulerDLQ.Arn

  SchedulerDLQ:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: scheduler-dlq
      MessageRetentionPeriod: 1209600
```

### Terraform을 통한 관리

```bash
# Terraform 리소스 확인
aws scheduler list-schedules --query 'Schedules[*].{Name:Name,State:State,Group:GroupName}' --output table
```

### 대규모 스케줄 일괄 생성 스크립트

```python
import boto3
import json
import time

def batch_create_schedules(schedules: list, group_name: str, role_arn: str):
    """대량의 스케줄을 일괄 생성합니다. API 스로틀링을 고려한 배치 처리."""
    client = boto3.client('scheduler')
    results = {'success': [], 'failed': []}
    
    for i, schedule in enumerate(schedules):
        try:
            client.create_schedule(
                Name=schedule['name'],
                GroupName=group_name,
                ScheduleExpression=schedule['expression'],
                ScheduleExpressionTimezone=schedule.get('timezone', 'Asia/Seoul'),
                Target={
                    'Arn': schedule['target_arn'],
                    'RoleArn': role_arn,
                    'Input': json.dumps(schedule.get('input', {})),
                    'RetryPolicy': {
                        'MaximumRetryAttempts': 3,
                        'MaximumEventAgeInSeconds': 3600
                    }
                },
                FlexibleTimeWindow={
                    'Mode': schedule.get('flex_mode', 'OFF')
                }
            )
            results['success'].append(schedule['name'])
        except Exception as e:
            results['failed'].append({
                'name': schedule['name'],
                'error': str(e)
            })
        
        # API 스로틀링 방지: 매 10개마다 0.5초 대기
        if (i + 1) % 10 == 0:
            time.sleep(0.5)
    
    return results
```

### 비용 최적화 전략

EventBridge Scheduler의 과금은 스케줄 호출 건수 기준입니다. 월 1,400만 건까지 무료 티어가 제공되며, 이후 호출 건당 $0.000001(백만 건당 $1.00)이 과금됩니다.

```bash
# 현재 스케줄 수 확인
aws scheduler list-schedules \
  --query 'length(Schedules)' \
  --output text

# 비활성 스케줄 확인
aws scheduler list-schedules \
  --state "DISABLED" \
  --query 'Schedules[*].{Name:Name,Group:GroupName}' \
  --output table
```

비용 최적화를 위한 주요 전략은 다음과 같습니다.

1. **불필요한 스케줄 정리**: 더 이상 사용하지 않는 스케줄을 비활성화하거나 삭제합니다.
2. **ActionAfterCompletion 활용**: 일회성 스케줄에는 반드시 `DELETE`를 설정합니다.
3. **Rate 최적화**: 필요 이상으로 높은 빈도의 스케줄을 식별하고 조정합니다.
4. **배치 처리 활용**: 개별 스케줄 대신 하나의 스케줄에서 여러 작업을 배치로 처리하도록 설계합니다.

## 모범 사례/보안

### 보안 심화

**조건부 접근 제어**: IAM 정책에서 스케줄 그룹이나 이름 패턴에 따라 접근을 제한할 수 있습니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "scheduler:CreateSchedule",
        "scheduler:UpdateSchedule",
        "scheduler:DeleteSchedule"
      ],
      "Resource": "arn:aws:scheduler:ap-northeast-2:123456789012:schedule/tenant-alpha-*/*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/TenantId": "alpha"
        }
      }
    }
  ]
}
```

**Confused Deputy 방지**: 실행 역할의 신뢰 정책에 `aws:SourceArn` 조건을 추가하여, 특정 스케줄에서만 해당 역할을 사용할 수 있도록 제한합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "scheduler.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "123456789012"
        },
        "StringLike": {
          "aws:SourceArn": "arn:aws:scheduler:ap-northeast-2:123456789012:schedule/system-maintenance/*"
        }
      }
    }
  ]
}
```

### 모니터링 대시보드 구성

```bash
# CloudWatch 대시보드 위젯용 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace AWS/Scheduler \
  --metric-name InvocationAttemptCount \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum \
  --dimensions Name=ScheduleGroup,Value=default
```

## 관련 서비스 비교

| 사용 사례 | 추천 서비스 | 이유 |
|----------|-----------|------|
| 정기적 Lambda 트리거 | EventBridge Scheduler | 타임존 지원, 유연한 시간 윈도우 |
| 미래 시점 일회성 작업 | EventBridge Scheduler | 일회성 스케줄 + 자동 삭제 |
| 이벤트 기반 라우팅 | EventBridge Rules | 이벤트 패턴 매칭에 특화 |
| 복잡한 워크플로우 | Step Functions + Scheduler | 스케줄 트리거 + 워크플로우 오케스트레이션 |
| 대규모 개인화 스케줄 | EventBridge Scheduler | 수백만 개 스케줄 지원 |
| 컨테이너 기반 배치 작업 | EventBridge Scheduler + ECS | 범용 타겟으로 ECS RunTask 호출 |
| EC2 시작/중지 자동화 | EventBridge Scheduler | 범용 타겟으로 EC2 API 직접 호출 |
| 크로스 리전 작업 | EventBridge Rules + Bus | 글로벌 이벤트 버스 활용 |

## 요약

이 글에서는 Amazon EventBridge Scheduler의 고급 활용 패턴을 다루었습니다. 핵심 내용을 정리하면 다음과 같습니다.

- **범용 타겟**: 270개 이상 AWS 서비스의 6,000개 이상 API를 직접 호출하여, Lambda를 거치지 않고도 다양한 AWS 작업을 스케줄링할 수 있습니다.
- **대규모 멀티 테넌트 관리**: 스케줄 그룹과 IAM 조건부 정책을 활용하여 테넌트별 격리된 스케줄 관리가 가능합니다.
- **이벤트 소싱 패턴**: 일회성 스케줄과 자동 삭제를 활용한 지연 처리(주문 타임아웃 등) 구현이 효과적입니다.
- **IaC 관리**: CloudFormation/Terraform을 통해 스케줄 인프라를 코드로 관리할 수 있습니다.
- **보안 강화**: Confused Deputy 방지, 스케줄 그룹별 접근 제어 등 엔터프라이즈급 보안 구성이 가능합니다.
- **비용 최적화**: 무료 티어 활용, 불필요한 스케줄 정리, 배치 처리 등을 통해 비용을 최적화할 수 있습니다.

EventBridge Scheduler는 서버리스 아키텍처에서 스케줄링 계층을 담당하는 핵심 서비스로, 올바르게 활용하면 운영 복잡성을 크게 줄이면서도 확장 가능한 스케줄링 인프라를 구축할 수 있습니다.