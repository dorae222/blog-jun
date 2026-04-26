<!-- infographic-hero -->
![AWS Health Dashboard 핵심 요약](figures/infographic.svg)

*Figure: AWS Health Dashboard 한 장 요약 인포그래픽*

## 개요

AWS Health Dashboard는 AWS 인프라의 서비스 상태를 실시간으로 확인하고, 사용자 계정에 직접적으로 영향을 미치는 이벤트를 추적할 수 있는 모니터링 서비스입니다. 기존에 분리되어 있던 AWS Service Health Dashboard(공개)와 AWS Personal Health Dashboard(계정별)가 2022년에 통합되어 하나의 Health Dashboard로 제공되고 있습니다.

AWS에서 장애나 유지보수가 발생했을 때, 자신의 리소스가 영향을 받는지 신속하게 파악하는 것은 운영의 핵심입니다. Health Dashboard는 AWS 전체의 서비스 상태뿐 아니라, 특정 계정의 특정 리소스에 영향을 미치는 이벤트까지 세부적으로 알려줍니다.

### Health Dashboard의 두 가지 관점

**Service Health (서비스 상태)**
- AWS 전체 서비스의 글로벌 상태를 보여줍니다.
- 모든 사용자가 인증 없이 확인할 수 있습니다.
- 리전별, 서비스별 현재 상태와 과거 이벤트 이력을 제공합니다.
- URL: https://health.aws.amazon.com/health/status

**Your Account Health (계정 상태)**
- 로그인한 계정의 리소스에 영향을 미치는 이벤트만 필터링하여 보여줍니다.
- 예정된 유지보수, 서비스 장애, 계정 알림 등을 포함합니다.
- 영향받는 리소스의 구체적인 정보(인스턴스 ID, ARN 등)를 제공합니다.

## 핵심 기능

### 1. 이벤트 유형

Health Dashboard에서 제공하는 이벤트는 세 가지 유형으로 분류됩니다.

**이슈 (Issue)**
- AWS 서비스에서 발생한 장애나 성능 저하를 알립니다.
- 사용자 계정의 리소스에 영향을 미치는 경우 Your Account Health에 표시됩니다.
- 예: EC2 인스턴스가 위치한 가용 영역의 네트워크 장애

**예정된 변경 (Scheduled Change)**
- AWS에서 계획한 유지보수나 변경 사항을 사전에 알립니다.
- 일반적으로 수일에서 수주 전에 통보됩니다.
- 예: RDS 인스턴스의 필수 보안 패치, EC2 호스트의 하드웨어 유지보수

**계정 알림 (Account Notification)**
- 계정 수준의 운영 관련 알림입니다.
- 예: 인증서 만료 예정, 서비스 한도 초과 경고

### 2. AWS Health API

AWS Health API를 사용하면 프로그래밍 방식으로 Health 이벤트를 조회할 수 있습니다. 이 API는 AWS Business Support 또는 Enterprise Support 플랜에서만 사용할 수 있습니다.

```bash
# 현재 활성 이벤트 조회
aws health describe-events \
  --filter '{"eventStatusCodes":["open","upcoming"],"regions":["ap-northeast-2"]}' \
  --region us-east-1

# 특정 이벤트의 상세 정보 조회
aws health describe-event-details \
  --event-arns "arn:aws:health:ap-northeast-2::event/EC2/AWS_EC2_OPERATIONAL_ISSUE/1234567890" \
  --region us-east-1

# 이벤트에 영향받는 엔터티(리소스) 조회
aws health describe-affected-entities \
  --filter '{"eventArns":["arn:aws:health:ap-northeast-2::event/EC2/AWS_EC2_OPERATIONAL_ISSUE/1234567890"]}' \
  --region us-east-1

# 이벤트 유형 목록 조회
aws health describe-event-types \
  --filter '{"services":["EC2","RDS"],"eventTypeCategories":["scheduledChange"]}' \
  --region us-east-1
```

주의: Health API는 반드시 `us-east-1` 리전 엔드포인트를 사용해야 합니다. 이는 Health API가 글로벌 서비스이기 때문입니다.

### 3. AWS Health Organizational View

AWS Organizations를 사용하는 경우, 조직 전체의 Health 이벤트를 관리 계정에서 통합 조회할 수 있습니다.

```bash
# Organizational Health 활성화
aws health enable-health-service-access-for-organization \
  --region us-east-1

# 조직 전체의 이벤트 조회
aws health describe-events-for-organization \
  --filter '{"regions":["ap-northeast-2"],"eventStatusCodes":["open"]}' \
  --region us-east-1

# 조직 내 영향받는 계정 조회
aws health describe-affected-accounts-for-organization \
  --event-arn "arn:aws:health:ap-northeast-2::event/EC2/AWS_EC2_OPERATIONAL_ISSUE/1234567890" \
  --region us-east-1

# 조직 내 영향받는 엔터티 조회
aws health describe-affected-entities-for-organization \
  --organization-entity-filters '[{"eventArn":"arn:aws:health:ap-northeast-2::event/EC2/AWS_EC2_OPERATIONAL_ISSUE/1234567890","awsAccountId":"123456789012"}]' \
  --region us-east-1
```

### 4. EventBridge 연동

Health 이벤트를 Amazon EventBridge와 연동하면 자동화된 대응이 가능합니다. 이것이 Health Dashboard의 가장 강력한 기능 중 하나입니다.

```bash
# Health 이벤트를 EventBridge로 전달하는 규칙 생성
aws events put-rule \
  --name "aws-health-ec2-events" \
  --event-pattern '{
    "source": ["aws.health"],
    "detail-type": ["AWS Health Event"],
    "detail": {
      "service": ["EC2"],
      "eventTypeCategory": ["issue", "scheduledChange"]
    }
  }' \
  --region ap-northeast-2

# SNS 토픽으로 알림 전달
aws events put-targets \
  --rule "aws-health-ec2-events" \
  --targets "Id"="1","Arn"="arn:aws:sns:ap-northeast-2:123456789012:health-alerts" \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### Health 이벤트 처리 아키텍처

```
AWS 인프라 이벤트 발생
    │
    ▼
AWS Health Service (글로벌)
    │
    ├── Service Health Dashboard (공개)
    │   └── 전체 서비스 상태 표시
    │
    ├── Personal Health Dashboard (계정별)
    │   └── 영향받는 리소스 식별 및 알림
    │
    ├── Health API (프로그래밍 접근)
    │   ├── describe-events
    │   ├── describe-event-details
    │   └── describe-affected-entities
    │
    └── EventBridge 연동
        │
        ├── Lambda (자동 복구)
        ├── SNS (알림)
        ├── SQS (큐잉)
        └── Step Functions (워크플로우)
```

### Health 이벤트 수명 주기

```
1. 이벤트 생성 (Created)
   └── AWS에서 이슈 감지 또는 유지보수 예정

2. 이벤트 공개 (Open / Upcoming)
   ├── Open: 현재 진행 중인 이슈
   └── Upcoming: 예정된 유지보수

3. 이벤트 업데이트 (Updated)
   └── 상태 변경, 영향 범위 변경 등

4. 이벤트 종료 (Closed)
   └── 이슈 해결 또는 유지보수 완료
```

Health 이벤트의 JSON 구조 예시입니다.

```json
{
  "version": "0",
  "id": "abcdefgh-1234-5678-9012-abcdefghijkl",
  "detail-type": "AWS Health Event",
  "source": "aws.health",
  "account": "123456789012",
  "time": "2025-01-15T10:30:00Z",
  "region": "ap-northeast-2",
  "resources": [
    "i-0abcdef1234567890"
  ],
  "detail": {
    "eventArn": "arn:aws:health:ap-northeast-2::event/EC2/AWS_EC2_INSTANCE_RETIREMENT/1234567890",
    "service": "EC2",
    "eventTypeCode": "AWS_EC2_INSTANCE_RETIREMENT",
    "eventTypeCategory": "scheduledChange",
    "startTime": "2025-01-20T00:00:00Z",
    "endTime": "2025-01-20T06:00:00Z",
    "eventDescription": [{
      "language": "en_US",
      "latestDescription": "Your EC2 instance i-0abcdef1234567890 is scheduled for retirement..."
    }],
    "affectedEntities": [{
      "entityValue": "i-0abcdef1234567890",
      "tags": {
        "Name": "production-web-server"
      }
    }]
  }
}
```

## 실전 활용

### 자동 장애 대응 시스템 구축

EC2 인스턴스 장애 이벤트 발생 시 자동으로 대체 인스턴스를 시작하는 Lambda 함수를 EventBridge와 연동하는 예시입니다.

```python
import json
import boto3

def lambda_handler(event, context):
    """
    AWS Health EC2 이벤트 수신 시 자동 대응
    """
    detail = event.get('detail', {})
    event_type = detail.get('eventTypeCode', '')
    affected_entities = detail.get('affectedEntities', [])
    
    ec2 = boto3.client('ec2')
    sns = boto3.client('sns')
    
    for entity in affected_entities:
        instance_id = entity.get('entityValue', '')
        
        if event_type == 'AWS_EC2_INSTANCE_RETIREMENT':
            # 인스턴스 은퇴 예정 - 자동으로 대체 인스턴스 프로비저닝
            response = ec2.describe_instances(InstanceIds=[instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            
            # 기존 인스턴스의 AMI 생성
            ami_response = ec2.create_image(
                InstanceId=instance_id,
                Name=f"backup-{instance_id}-retirement",
                NoReboot=True
            )
            
            # 알림 전송
            sns.publish(
                TopicArn='arn:aws:sns:ap-northeast-2:123456789012:health-alerts',
                Subject=f'EC2 Instance Retirement: {instance_id}',
                Message=json.dumps({
                    'event_type': event_type,
                    'instance_id': instance_id,
                    'ami_created': ami_response['ImageId'],
                    'action': 'AMI created for replacement'
                }, indent=2)
            )
    
    return {'statusCode': 200, 'body': 'Health event processed'}
```

### EventBridge 규칙 상세 설정

다양한 서비스별 Health 이벤트에 대한 EventBridge 규칙을 설정하는 예시입니다.

```bash
# RDS 유지보수 이벤트 알림
aws events put-rule \
  --name "aws-health-rds-maintenance" \
  --event-pattern '{
    "source": ["aws.health"],
    "detail-type": ["AWS Health Event"],
    "detail": {
      "service": ["RDS"],
      "eventTypeCategory": ["scheduledChange"],
      "eventTypeCode": ["AWS_RDS_MAINTENANCE_SCHEDULED"]
    }
  }' \
  --region ap-northeast-2

# 모든 서비스의 장애 이벤트 알림
aws events put-rule \
  --name "aws-health-all-issues" \
  --event-pattern '{
    "source": ["aws.health"],
    "detail-type": ["AWS Health Event"],
    "detail": {
      "eventTypeCategory": ["issue"]
    }
  }' \
  --region ap-northeast-2

# Lambda 함수를 타겟으로 추가
aws events put-targets \
  --rule "aws-health-all-issues" \
  --targets '[{"Id":"lambda-target","Arn":"arn:aws:lambda:ap-northeast-2:123456789012:function:health-event-handler"},{"Id":"sns-target","Arn":"arn:aws:sns:ap-northeast-2:123456789012:ops-alerts"}]' \
  --region ap-northeast-2
```

### Slack/Teams 연동 알림 시스템

AWS Chatbot을 활용하여 Health 이벤트를 Slack이나 Microsoft Teams로 전달하는 구성입니다.

```bash
# SNS 토픽 생성 (Chatbot 연동용)
aws sns create-topic \
  --name "aws-health-chatbot" \
  --region ap-northeast-2

# EventBridge에서 SNS로 전달
aws events put-targets \
  --rule "aws-health-all-issues" \
  --targets "Id"="chatbot-sns","Arn"="arn:aws:sns:ap-northeast-2:123456789012:aws-health-chatbot" \
  --region ap-northeast-2

# AWS Chatbot은 콘솔에서 Slack 워크스페이스 연동 후
# 해당 SNS 토픽을 구독하도록 설정합니다
```

### Organizations 전체 Health 모니터링

멀티 계정 환경에서 모든 계정의 Health 이벤트를 중앙에서 모니터링하는 방법입니다.

```bash
# 1. 관리 계정에서 Organization Health 활성화
aws health enable-health-service-access-for-organization \
  --region us-east-1

# 2. 조직 전체의 활성 이벤트 조회
aws health describe-events-for-organization \
  --filter '{
    "regions": ["ap-northeast-2", "us-east-1"],
    "eventStatusCodes": ["open", "upcoming"],
    "eventTypeCategories": ["issue", "scheduledChange"]
  }' \
  --region us-east-1

# 3. 위임 관리자 설정 (보안 계정에 위임)
aws organizations register-delegated-administrator \
  --account-id 444455556666 \
  --service-principal health.amazonaws.com
```

## 모범 사례/보안

### 모니터링 모범 사례

1. **EventBridge 규칙을 반드시 설정하십시오.** 콘솔에서 수동으로 확인하는 것만으로는 중요한 이벤트를 놓칠 수 있습니다. EventBridge를 통해 자동 알림을 구성해야 합니다.

2. **서비스별 대응 계획을 수립하십시오.** EC2 인스턴스 은퇴, RDS 유지보수, Lambda 런타임 지원 종료 등 서비스별로 적절한 대응 절차를 사전에 정의해야 합니다.

3. **Organizations Health View를 활용하십시오.** 멀티 계정 환경에서는 반드시 Organization Health를 활성화하여 전체 계정의 상태를 중앙에서 모니터링하십시오.

4. **Health 이벤트를 ITSM 도구와 연동하십시오.** ServiceNow, Jira 등의 ITSM 도구와 연동하면 인시던트 관리 프로세스에 Health 이벤트를 자동으로 포함시킬 수 있습니다.

### 보안 관련 모범 사례

- Health API 접근 권한을 운영팀과 보안팀으로 제한하십시오.
- Health 이벤트 알림에 민감한 정보가 포함될 수 있으므로, SNS 토픽에 적절한 접근 정책을 적용하십시오.
- Organization Health의 위임 관리자를 보안 계정 또는 운영 계정으로 설정하십시오.

### 주의 사항

- Health API는 Business 또는 Enterprise Support 플랜에서만 사용 가능합니다. Developer 또는 Basic 플랜에서는 콘솔만 사용할 수 있습니다.
- Health API 호출은 반드시 `us-east-1` 리전 엔드포인트를 사용해야 합니다.
- EventBridge를 통한 Health 이벤트 수신은 모든 Support 플랜에서 가능합니다.

## 관련 서비스 비교

### Health Dashboard vs CloudWatch vs EventBridge

| 항목 | Health Dashboard | CloudWatch | EventBridge |
|------|-----------------|------------|-------------|
| 목적 | AWS 서비스 상태 모니터링 | 리소스 메트릭/로그 모니터링 | 이벤트 라우팅/자동화 |
| 데이터 소스 | AWS 인프라 이벤트 | 사용자 리소스 메트릭 | 다양한 이벤트 소스 |
| 범위 | AWS 관리형 이벤트 | 사용자 리소스 | 전체 이벤트 버스 |
| 알림 | EventBridge 연동 | SNS/Lambda 직접 연동 | 다양한 타겟 지원 |
| 비용 | 무료 (API는 Support 플랜 필요) | 사용량 기반 과금 | 이벤트당 과금 |

### Health Dashboard vs 서드파티 상태 모니터링

Datadog, PagerDuty 등의 서드파티 도구도 AWS 상태 모니터링을 지원합니다. Health Dashboard와의 차이점은 다음과 같습니다.

- Health Dashboard는 AWS 공식 소스로서 가장 정확하고 빠른 정보를 제공합니다.
- 서드파티 도구는 AWS 외의 인프라도 통합 모니터링할 수 있는 장점이 있습니다.
- 두 가지를 병행 사용하는 것이 가장 효과적입니다.

## 요약

AWS Health Dashboard는 AWS 서비스 상태와 계정 영향도를 실시간으로 모니터링하는 핵심 운영 도구입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **이중 관점**: Service Health(전체 서비스 상태)와 Your Account Health(계정별 영향)를 함께 제공합니다.
- **이벤트 유형**: 이슈(장애), 예정된 변경(유지보수), 계정 알림의 세 가지 유형으로 분류됩니다.
- **Health API**: 프로그래밍 방식으로 이벤트를 조회할 수 있습니다. Business/Enterprise Support 플랜이 필요합니다.
- **EventBridge 연동**: 자동 알림 및 자동 대응 시스템을 구축할 수 있습니다.
- **Organization Health**: 멀티 계정 환경에서 전체 조직의 Health 이벤트를 중앙에서 관리합니다.
- **운영 필수**: 프로덕션 환경에서는 EventBridge 기반 알림 설정이 필수적입니다.

Health Dashboard를 효과적으로 활용하면 AWS 인프라 장애에 대한 대응 시간을 크게 단축하고, 예정된 유지보수에 선제적으로 대비할 수 있습니다.