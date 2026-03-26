## 개요

Amazon EventBridge Scheduler는 2022년 11월에 출시된 서버리스 스케줄링 서비스로, 대규모 작업 스케줄링을 간편하게 관리할 수 있습니다. 기존 EventBridge Rules의 스케줄 기능을 독립된 서비스로 분리하여, 더욱 강력하고 유연한 스케줄링 기능을 제공합니다.

기존에 cron 작업이나 CloudWatch Events 기반 스케줄링은 여러 제약이 있었습니다. EC2 인스턴스에서 crontab을 관리하면 단일 장애점이 되고, CloudWatch Events Rules는 리전당 300개라는 제한이 있었습니다. EventBridge Scheduler는 이러한 한계를 극복하여, 단일 계정에서 수백만 개의 스케줄을 생성할 수 있으며, 270개 이상의 AWS 서비스를 직접 호출할 수 있습니다.

EventBridge Scheduler의 가장 큰 차별점은 다음과 같습니다. 첫째, 일회성(one-time) 스케줄을 지원합니다. 특정 시점에 한 번만 실행되는 작업을 예약할 수 있어, 미래 시점의 작업 예약이 매우 간편합니다. 둘째, 타임존을 지원합니다. UTC가 아닌 특정 타임존 기준으로 스케줄을 설정할 수 있습니다. 셋째, 내장 재시도 정책과 DLQ(Dead Letter Queue)를 제공하여 안정적인 작업 실행을 보장합니다.

## 핵심 기능

### 스케줄 유형

EventBridge Scheduler는 세 가지 스케줄 유형을 지원합니다.

**1. 일회성 스케줄 (One-time Schedule)**

특정 날짜와 시간에 한 번만 실행되는 스케줄입니다. 예를 들어, 특정 시점에 데이터베이스 마이그레이션을 시작하거나, 프로모션 시작 시점에 설정을 변경하는 등의 용도로 사용됩니다.

**2. Rate 기반 스케줄**

일정 간격으로 반복 실행되는 스케줄입니다. `rate(5 minutes)`, `rate(1 hour)`, `rate(7 days)` 등의 형식으로 지정합니다.

**3. Cron 기반 스케줄**

cron 표현식을 사용하여 세밀한 반복 실행을 정의합니다. 분, 시, 일, 월, 요일, 연도를 지정할 수 있습니다.

### 범용 타겟 (Universal Target)

EventBridge Scheduler는 270개 이상의 AWS 서비스에 대해 6,000개 이상의 API 액션을 직접 호출할 수 있습니다. 이를 범용 타겟(Universal Target)이라고 하며, Lambda, Step Functions, SQS, SNS 등은 물론, EC2 인스턴스 시작/중지, RDS 스냅샷 생성, ECS 태스크 실행 등 거의 모든 AWS API를 스케줄의 타겟으로 지정할 수 있습니다.

### 유연한 시간 윈도우 (Flexible Time Window)

정확한 시간이 아닌, 특정 시간 범위 내에서 실행되도록 설정할 수 있습니다. 예를 들어, "매일 오전 2시부터 2시 15분 사이"처럼 지정하면, 동일 시간대에 대량의 스케줄이 집중되는 것을 방지하여 타겟 서비스의 부하를 분산시킬 수 있습니다.

### 재시도 정책 및 DLQ

타겟 호출이 실패할 경우 최대 185회까지 재시도할 수 있으며, 재시도 기간은 최대 24시간까지 설정할 수 있습니다. 모든 재시도가 실패하면 이벤트를 SQS Dead Letter Queue로 전송하여, 실패한 작업을 추후 분석하거나 수동 처리할 수 있습니다.

### 스케줄 그룹

스케줄을 논리적으로 그룹화하여 관리할 수 있습니다. 프로젝트별, 환경별(dev/staging/prod), 팀별로 그룹을 나누어 태그 기반 비용 추적, 일괄 삭제, 접근 제어 등에 활용할 수 있습니다.

## 아키텍처/동작 원리

EventBridge Scheduler의 내부 아키텍처는 다음과 같이 동작합니다.

### 스케줄 생성 및 저장

스케줄을 생성하면 EventBridge Scheduler는 스케줄 메타데이터(실행 시간, 타겟 정보, 재시도 정책 등)를 내부 저장소에 등록합니다. 이 저장소는 다중 AZ에 걸쳐 복제되어 고가용성을 보장합니다.

```bash
# 일회성 스케줄 생성: 특정 시점에 Lambda 함수 호출
aws scheduler create-schedule \
  --name "db-migration-trigger" \
  --schedule-expression "at(2024-03-15T02:00:00)" \
  --schedule-expression-timezone "Asia/Seoul" \
  --target '{
    "Arn": "arn:aws:lambda:ap-northeast-2:123456789012:function:db-migration",
    "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeSchedulerRole",
    "Input": "{\"action\": \"start-migration\", \"version\": \"v2.1\"}"
  }' \
  --flexible-time-window '{"Mode": "OFF"}' \
  --action-after-completion "DELETE"
```

### 스케줄 평가 및 실행

Scheduler 엔진은 지속적으로 등록된 스케줄을 평가하여, 실행 시점에 도달한 스케줄을 식별합니다. 실행 시점이 되면 지정된 IAM 역할을 사용하여 타겟 서비스의 API를 호출합니다.

```bash
# Rate 기반 반복 스케줄: 5분마다 SQS 메시지 전송
aws scheduler create-schedule \
  --name "health-check-schedule" \
  --schedule-expression "rate(5 minutes)" \
  --target '{
    "Arn": "arn:aws:sqs:ap-northeast-2:123456789012:health-check-queue",
    "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeSchedulerRole",
    "Input": "{\"check\": \"all-services\"}"
  }' \
  --flexible-time-window '{"Mode": "FLEXIBLE", "MaximumWindowInMinutes": 5}' \
  --state "ENABLED"
```

### 실패 처리 흐름

타겟 호출이 실패하면 다음 순서로 처리됩니다.

1. 재시도 정책에 따라 지수 백오프로 재시도
2. 최대 재시도 횟수 또는 재시도 기간 초과 시 재시도 중단
3. DLQ가 설정된 경우 실패 이벤트를 DLQ로 전송
4. CloudWatch 메트릭에 실패 기록

```bash
# Cron 기반 스케줄 + 재시도 정책 + DLQ 설정
aws scheduler create-schedule \
  --name "daily-report-generation" \
  --schedule-expression "cron(0 9 * * ? *)" \
  --schedule-expression-timezone "Asia/Seoul" \
  --target '{
    "Arn": "arn:aws:lambda:ap-northeast-2:123456789012:function:generate-report",
    "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeSchedulerRole",
    "RetryPolicy": {
      "MaximumEventAgeInSeconds": 3600,
      "MaximumRetryAttempts": 3
    },
    "DeadLetterConfig": {
      "Arn": "arn:aws:sqs:ap-northeast-2:123456789012:scheduler-dlq"
    }
  }' \
  --flexible-time-window '{"Mode": "OFF"}'
```

## 실전 활용

### 사례 1: EC2 인스턴스 비용 최적화

업무 시간에만 개발/스테이징 환경 EC2 인스턴스를 실행하여 비용을 절감할 수 있습니다.

```bash
# 평일 오전 9시에 인스턴스 시작
aws scheduler create-schedule \
  --name "start-dev-instances" \
  --schedule-expression "cron(0 0 ? * MON-FRI *)" \
  --schedule-expression-timezone "Asia/Seoul" \
  --target '{
    "Arn": "arn:aws:scheduler:::aws-sdk:ec2:startInstances",
    "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeSchedulerRole",
    "Input": "{\"InstanceIds\": [\"i-0123456789abcdef0\", \"i-0abcdef1234567890\"]}"
  }' \
  --flexible-time-window '{"Mode": "OFF"}'

# 평일 오후 7시에 인스턴스 중지
aws scheduler create-schedule \
  --name "stop-dev-instances" \
  --schedule-expression "cron(0 10 ? * MON-FRI *)" \
  --schedule-expression-timezone "Asia/Seoul" \
  --target '{
    "Arn": "arn:aws:scheduler:::aws-sdk:ec2:stopInstances",
    "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeSchedulerRole",
    "Input": "{\"InstanceIds\": [\"i-0123456789abcdef0\", \"i-0abcdef1234567890\"]}"
  }' \
  --flexible-time-window '{"Mode": "OFF"}'
```

### 사례 2: 예약 알림 시스템

사용자가 예약한 미래 시점에 알림을 발송하는 시스템을 구현할 수 있습니다. 일회성 스케줄을 활용하면 각 사용자별 개별 알림 시간을 설정할 수 있습니다.

```python
import boto3
from datetime import datetime, timedelta

def schedule_notification(user_id: str, message: str, notify_at: datetime):
    """사용자 알림을 EventBridge Scheduler로 예약합니다."""
    client = boto3.client('scheduler')
    
    schedule_name = f"notify-{user_id}-{int(notify_at.timestamp())}"
    
    response = client.create_schedule(
        Name=schedule_name,
        GroupName='user-notifications',
        ScheduleExpression=f"at({notify_at.strftime('%Y-%m-%dT%H:%M:%S')})",
        ScheduleExpressionTimezone='Asia/Seoul',
        Target={
            'Arn': 'arn:aws:lambda:ap-northeast-2:123456789012:function:send-notification',
            'RoleArn': 'arn:aws:iam::123456789012:role/EventBridgeSchedulerRole',
            'Input': json.dumps({
                'user_id': user_id,
                'message': message,
                'scheduled_at': notify_at.isoformat()
            })
        },
        FlexibleTimeWindow={'Mode': 'OFF'},
        ActionAfterCompletion='DELETE'  # 실행 후 자동 삭제
    )
    
    return response['ScheduleArn']
```

### 사례 3: 스케줄 그룹을 활용한 멀티 테넌트 관리

```bash
# 스케줄 그룹 생성
aws scheduler create-schedule-group \
  --name "tenant-alpha" \
  --tags '[{"Key": "tenant", "Value": "alpha"}, {"Key": "environment", "Value": "production"}]'

# 그룹 내 스케줄 목록 조회
aws scheduler list-schedules \
  --group-name "tenant-alpha" \
  --state "ENABLED"

# 그룹 삭제 (그룹 내 모든 스케줄도 함께 삭제)
aws scheduler delete-schedule-group \
  --name "tenant-alpha"
```

## 모범 사례/보안

### IAM 역할 설계

각 스케줄에는 타겟 서비스를 호출하기 위한 IAM 실행 역할이 필요합니다. 최소 권한 원칙에 따라 역할을 설계해야 합니다.

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
        }
      }
    }
  ]
}
```

### 보안 모범 사례

1. **역할 분리**: 스케줄 유형이나 타겟별로 IAM 역할을 분리하여, 하나의 역할이 과도한 권한을 갖지 않도록 합니다.
2. **DLQ 모니터링**: DLQ에 메시지가 쌓이면 알림을 발송하도록 CloudWatch Alarm을 설정합니다.
3. **스케줄 감사**: CloudTrail을 통해 스케줄 생성/수정/삭제를 감사합니다.
4. **암호화**: 타겟에 전달하는 입력 데이터에 민감 정보가 포함된 경우, Secrets Manager나 SSM Parameter Store를 참조하도록 설계합니다.

### 운영 모범 사례

1. **ActionAfterCompletion 활용**: 일회성 스케줄에는 `DELETE`를 설정하여, 실행 후 자동 삭제되도록 합니다. 이를 통해 불필요한 스케줄이 누적되는 것을 방지합니다.
2. **유연한 시간 윈도우 활용**: 정확한 시간이 중요하지 않은 작업에는 Flexible Time Window를 설정하여 타겟 서비스의 부하를 분산시킵니다.
3. **스케줄 그룹 활용**: 환경별, 프로젝트별로 그룹을 나누어 관리 편의성을 높입니다.
4. **CloudWatch 메트릭 모니터링**: `InvocationAttemptCount`, `InvocationDroppedCount`, `TargetErrorCount` 등의 메트릭을 모니터링합니다.

```bash
# 스케줄 실패 모니터링 알람
aws cloudwatch put-metric-alarm \
  --alarm-name "scheduler-target-errors" \
  --metric-name TargetErrorCount \
  --namespace AWS/Scheduler \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:ops-alerts \
  --dimensions Name=ScheduleGroup,Value=default
```

## 관련 서비스 비교

| 항목 | EventBridge Scheduler | EventBridge Rules | CloudWatch Events | Step Functions Wait |
|------|----------------------|-------------------|--------------------|---------|
| 스케줄 수 제한 | 수백만 개 | 리전당 300개 | 리전당 300개 | 워크플로우 내 |
| 일회성 스케줄 | 지원 | 미지원 | 미지원 | 지원 |
| 타임존 지원 | 지원 | 미지원 (UTC만) | 미지원 (UTC만) | 해당 없음 |
| 범용 타겟 | 270+ 서비스 | 20+ 서비스 | 20+ 서비스 | 200+ 서비스 |
| 유연한 시간 윈도우 | 지원 | 미지원 | 미지원 | 미지원 |
| 자동 완료 후 삭제 | 지원 | 미지원 | 미지원 | 해당 없음 |
| DLQ 내장 | 지원 | 별도 설정 필요 | 별도 설정 필요 | 내장 오류 처리 |
| 비용 | 스케줄 호출당 과금 | 규칙 매칭당 과금 | 규칙 매칭당 과금 | 상태 전환당 과금 |

EventBridge Scheduler는 기존 EventBridge Rules의 스케줄 기능을 완전히 대체할 수 있으며, 특히 대규모 스케줄링이나 일회성 작업 예약이 필요한 경우 최적의 선택입니다.

## 요약

Amazon EventBridge Scheduler는 서버리스 환경에서 대규모 작업 스케줄링을 간편하고 안정적으로 관리할 수 있는 완전관리형 서비스입니다. 핵심 특징을 정리하면 다음과 같습니다.

- **대규모 스케줄링**: 단일 계정에서 수백만 개의 스케줄을 생성할 수 있습니다.
- **세 가지 스케줄 유형**: 일회성, Rate 기반, Cron 기반 스케줄을 지원합니다.
- **범용 타겟**: 270개 이상의 AWS 서비스를 직접 호출할 수 있습니다.
- **타임존 지원**: UTC가 아닌 로컬 타임존 기준으로 스케줄을 설정할 수 있습니다.
- **안정적 실행**: 내장 재시도 정책과 DLQ로 실패에 대응합니다.
- **비용 효율**: 서버리스 모델로, 스케줄 호출당 과금됩니다.
- **자동 정리**: 일회성 스케줄의 실행 후 자동 삭제 기능으로 관리 부담을 줄입니다.

기존 crontab이나 CloudWatch Events Rules 기반 스케줄링에서 EventBridge Scheduler로 전환하면, 운영 부담을 크게 줄이면서도 더욱 유연하고 확장 가능한 스케줄링 인프라를 구축할 수 있습니다.