# AWS Systems Manager Parameter Store 심층 분석

## 개요

AWS Systems Manager Parameter Store는 애플리케이션의 구성 데이터, 데이터베이스 연결 문자열, API 키, 비밀번호 등을 중앙에서 안전하게 저장하고 관리할 수 있는 서비스입니다. 하드코딩된 구성 값을 코드에서 분리하여 보안을 강화하고 운영 효율성을 높이는 것이 핵심 목표입니다.

클라우드 네이티브 애플리케이션을 개발하면서 가장 흔히 마주치는 문제 중 하나는 설정값 관리입니다. 데이터베이스 호스트 주소, API 키, 인증서 경로 등 환경별로 달라지는 값들을 어떻게 안전하게 관리할 것인가가 핵심 과제입니다. Parameter Store는 이 문제에 대한 AWS의 네이티브 솔루션입니다.

Parameter Store는 AWS KMS(Key Management Service)와 통합되어 민감한 데이터를 암호화하여 저장할 수 있으며, IAM 정책으로 세밀한 접근 제어가 가능합니다. 또한 파라미터 변경 이력을 자동으로 추적하고, EventBridge와 연동하여 변경 알림을 받을 수 있습니다.

### Parameter Store vs Secrets Manager

AWS에는 비밀 값을 관리하는 서비스가 두 가지 있습니다. Parameter Store와 Secrets Manager입니다. 두 서비스의 차이를 이해하는 것이 중요합니다.

- **Parameter Store**: 구성 데이터와 비밀 값 모두 저장 가능, 무료 표준 계층 제공, 계층적 구조 지원
- **Secrets Manager**: 비밀 값 전용, 자동 교체(Rotation) 기본 지원, 교차 계정 공유 용이

Parameter Store는 범용적인 구성 관리에 적합하고, Secrets Manager는 데이터베이스 자격 증명처럼 주기적 교체가 필요한 비밀 값에 적합합니다.

## 핵심 기능

### 1. 파라미터 유형

Parameter Store는 세 가지 파라미터 유형을 지원합니다.

**String**: 일반 텍스트 값을 저장합니다.

```bash
# String 타입 파라미터 생성
aws ssm put-parameter \
  --name "/app/config/api-endpoint" \
  --type "String" \
  --value "https://api.example.com/v2" \
  --description "프로덕션 API 엔드포인트" \
  --tags Key=Environment,Value=Production Key=Team,Value=Backend
```

**StringList**: 쉼표로 구분된 문자열 목록을 저장합니다.

```bash
# StringList 타입 파라미터 생성
aws ssm put-parameter \
  --name "/app/config/allowed-origins" \
  --type "StringList" \
  --value "https://www.example.com,https://app.example.com,https://admin.example.com" \
  --description "허용된 CORS 오리진 목록"
```

**SecureString**: AWS KMS로 암호화된 문자열을 저장합니다.

```bash
# SecureString 타입 파라미터 생성 (기본 KMS 키 사용)
aws ssm put-parameter \
  --name "/app/secrets/database-password" \
  --type "SecureString" \
  --value "MyS3cur3P@ssw0rd!" \
  --description "프로덕션 데이터베이스 비밀번호"

# 사용자 지정 KMS 키로 암호화
aws ssm put-parameter \
  --name "/app/secrets/api-key" \
  --type "SecureString" \
  --value "sk-abc123def456ghi789" \
  --key-id "alias/my-app-key" \
  --description "외부 서비스 API 키"
```

### 2. 계층적 파라미터 구조

Parameter Store는 파일 시스템과 유사한 계층적 경로 구조를 지원합니다. 이를 통해 파라미터를 논리적으로 분류하고, 경로 기반으로 접근 제어를 적용할 수 있습니다.

```
/
├── app/
│   ├── config/
│   │   ├── api-endpoint
│   │   ├── allowed-origins
│   │   └── feature-flags/
│   │       ├── new-ui-enabled
│   │       └── beta-features
│   ├── secrets/
│   │   ├── database-password
│   │   ├── api-key
│   │   └── jwt-secret
│   └── database/
│       ├── host
│       ├── port
│       └── name
├── staging/
│   └── app/
│       └── ...
└── production/
    └── app/
        └── ...
```

```bash
# 계층 구조를 활용한 파라미터 일괄 생성
aws ssm put-parameter --name "/production/app/database/host" --type "String" --value "prod-db.cluster-abc123.ap-northeast-2.rds.amazonaws.com"
aws ssm put-parameter --name "/production/app/database/port" --type "String" --value "5432"
aws ssm put-parameter --name "/production/app/database/name" --type "String" --value "myapp_production"
aws ssm put-parameter --name "/production/app/database/password" --type "SecureString" --value "ProdP@ssw0rd!"

# 경로 기반 일괄 조회
aws ssm get-parameters-by-path \
  --path "/production/app/database" \
  --recursive \
  --with-decryption \
  --query 'Parameters[].{Name:Name,Value:Value}' \
  --output table
```

### 3. 버전 관리

Parameter Store는 파라미터 값이 변경될 때마다 자동으로 버전을 생성합니다. 이를 통해 변경 이력을 추적하고, 필요 시 이전 값을 참조할 수 있습니다.

```bash
# 파라미터 값 업데이트 (새 버전 생성)
aws ssm put-parameter \
  --name "/app/config/api-endpoint" \
  --type "String" \
  --value "https://api-v3.example.com" \
  --overwrite

# 특정 버전의 파라미터 조회
aws ssm get-parameter \
  --name "/app/config/api-endpoint:1"

# 최신 버전 조회
aws ssm get-parameter \
  --name "/app/config/api-endpoint"

# 파라미터 변경 이력 조회
aws ssm get-parameter-history \
  --name "/app/config/api-endpoint" \
  --query 'Parameters[].{Version:Version,Value:Value,LastModifiedDate:LastModifiedDate}' \
  --output table
```

### 4. 파라미터 정책 (Advanced Tier)

고급 계층(Advanced Tier)에서는 파라미터에 정책을 적용할 수 있습니다. 만료 정책(Expiration)과 변경 알림 정책(Notification)을 지원합니다.

```bash
# 만료 정책이 포함된 파라미터 생성
aws ssm put-parameter \
  --name "/app/secrets/temp-token" \
  --type "SecureString" \
  --value "temp-token-abc123" \
  --tier "Advanced" \
  --policies '[
    {
      "Type": "Expiration",
      "Version": "1.0",
      "Attributes": {
        "Timestamp": "2025-12-31T23:59:59.000Z"
      }
    },
    {
      "Type": "ExpirationNotification",
      "Version": "1.0",
      "Attributes": {
        "Before": "15",
        "Unit": "Days"
      }
    }
  ]'
```

### 5. Standard vs Advanced 계층

| 항목 | Standard | Advanced |
|------|----------|----------|
| 최대 파라미터 수 | 10,000 | 100,000 |
| 최대 값 크기 | 4 KB | 8 KB |
| 파라미터 정책 | 미지원 | 지원 |
| 비용 | 무료 | 유료 (파라미터당 $0.05/월) |
| 처리량 | 기본 40 TPS | 기본 1,000 TPS |

```bash
# Advanced 계층으로 파라미터 생성
aws ssm put-parameter \
  --name "/app/config/large-config" \
  --type "String" \
  --value "$(cat large-config.json)" \
  --tier "Advanced"

# 파라미터 계층 확인
aws ssm describe-parameters \
  --parameter-filters Key=Name,Values=/app/config/large-config \
  --query 'Parameters[].{Name:Name,Tier:Tier,Type:Type}'
```

## 아키텍처/동작 원리

### Parameter Store 내부 동작

Parameter Store의 내부 동작 원리를 이해하면 보다 효율적인 사용이 가능합니다.

```
[클라이언트]          [Parameter Store]         [KMS]
    |                      |                    |
    |-- PutParameter ----->|                    |
    |   (SecureString)     |-- Encrypt -------->|
    |                      |<-- CipherText -----|        [DynamoDB]
    |                      |-- Store ---------->| (내부 저장소)
    |<-- 200 OK -----------|                    |
    |                      |                    |
    |-- GetParameter ----->|                    |
    |   (WithDecryption)   |<-- Retrieve -------|
    |                      |-- Decrypt -------->|
    |                      |<-- PlainText ------|        [CloudTrail]
    |<-- Parameter --------|-- Log API Call --->| (감사 로그)
```

### KMS 통합 상세

SecureString 파라미터는 AWS KMS를 사용하여 암호화됩니다. 기본적으로 `aws/ssm` 관리형 키가 사용되지만, 사용자 지정 CMK(Customer Master Key)를 사용할 수도 있습니다.

사용자 지정 KMS 키를 사용하면 다음과 같은 이점이 있습니다.

- 키 순환 정책을 직접 관리할 수 있습니다.
- 교차 계정에서 파라미터를 복호화할 수 있습니다.
- CloudTrail에서 키 사용 이력을 추적할 수 있습니다.

```bash
# 사용자 지정 KMS 키 생성
aws kms create-key \
  --description "Parameter Store 암호화 키" \
  --tags TagKey=Purpose,TagValue=ParameterStore

# 키 별칭 생성
aws kms create-alias \
  --alias-name "alias/parameter-store-key" \
  --target-key-id "key-id-here"

# 사용자 지정 키로 SecureString 파라미터 저장
aws ssm put-parameter \
  --name "/app/secrets/critical-api-key" \
  --type "SecureString" \
  --value "critical-secret-value" \
  --key-id "alias/parameter-store-key"
```

### EventBridge 통합

파라미터 변경 시 EventBridge 이벤트가 자동으로 발생합니다. 이를 통해 구성 변경에 대한 실시간 대응이 가능합니다.

```bash
# 파라미터 변경 감지 EventBridge 규칙 생성
aws events put-rule \
  --name "parameter-change-notification" \
  --event-pattern '{
    "source": ["aws.ssm"],
    "detail-type": ["Parameter Store Change"],
    "detail": {
      "name": [{
        "prefix": "/production/"
      }],
      "operation": ["Create", "Update", "Delete"]
    }
  }'

# SNS 토픽으로 알림 전송
aws events put-targets \
  --rule "parameter-change-notification" \
  --targets '[{
    "Id": "notify-ops",
    "Arn": "arn:aws:sns:ap-northeast-2:123456789012:parameter-changes"
  }]'
```

## 실전 활용

### 사례 1: EC2/ECS 애플리케이션 구성 주입

EC2 인스턴스나 ECS 태스크에서 Parameter Store의 값을 읽어와 애플리케이션 구성으로 사용하는 패턴입니다.

```bash
# EC2 인스턴스 User Data에서 파라미터 값 조회
#!/bin/bash
DB_HOST=$(aws ssm get-parameter --name "/production/app/database/host" --query 'Parameter.Value' --output text)
DB_PORT=$(aws ssm get-parameter --name "/production/app/database/port" --query 'Parameter.Value' --output text)
DB_PASSWORD=$(aws ssm get-parameter --name "/production/app/database/password" --with-decryption --query 'Parameter.Value' --output text)

export DATABASE_URL="postgresql://appuser:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/myapp"
```

ECS 태스크 정의에서는 `secrets` 필드를 사용하여 Parameter Store 값을 환경 변수로 주입합니다.

```json
{
  "containerDefinitions": [
    {
      "name": "my-app",
      "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/my-app:latest",
      "secrets": [
        {
          "name": "DATABASE_PASSWORD",
          "valueFrom": "arn:aws:ssm:ap-northeast-2:123456789012:parameter/production/app/database/password"
        },
        {
          "name": "API_KEY",
          "valueFrom": "arn:aws:ssm:ap-northeast-2:123456789012:parameter/production/app/secrets/api-key"
        }
      ],
      "environment": [
        {
          "name": "DB_HOST",
          "value": "prod-db.cluster-abc123.ap-northeast-2.rds.amazonaws.com"
        }
      ]
    }
  ]
}
```

### 사례 2: Lambda 함수에서의 활용

Lambda 함수에서 Parameter Store를 사용하는 최적 패턴입니다. Lambda 확장(Extension)인 AWS Parameters and Secrets Lambda Extension을 사용하면 캐싱을 통해 API 호출을 최소화할 수 있습니다.

```python
import json
import boto3
from functools import lru_cache

ssm = boto3.client('ssm')

@lru_cache(maxsize=32)
def get_parameter(name, with_decryption=False):
    """파라미터 값을 캐싱하여 반환합니다."""
    response = ssm.get_parameter(
        Name=name,
        WithDecryption=with_decryption
    )
    return response['Parameter']['Value']

def get_database_config():
    """데이터베이스 설정을 일괄 조회합니다."""
    response = ssm.get_parameters_by_path(
        Path='/production/app/database',
        Recursive=True,
        WithDecryption=True
    )
    config = {}
    for param in response['Parameters']:
        key = param['Name'].split('/')[-1]
        config[key] = param['Value']
    return config

def lambda_handler(event, context):
    db_config = get_database_config()
    api_key = get_parameter('/production/app/secrets/api-key', with_decryption=True)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Configuration loaded successfully'})
    }
```

### 사례 3: CloudFormation과의 통합

CloudFormation 템플릿에서 Parameter Store 값을 동적으로 참조할 수 있습니다.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Parameter Store 값을 참조하는 CloudFormation 스택

Resources:
  MyEC2Instance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: !Sub '{{resolve:ssm:/production/app/config/instance-type}}'
      ImageId: !Sub '{{resolve:ssm:/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2}}'
      
  MyRDSInstance:
    Type: AWS::RDS::DBInstance
    Properties:
      DBInstanceClass: db.t3.medium
      MasterUsername: admin
      MasterUserPassword: !Sub '{{resolve:ssm-secure:/production/app/database/password}}'
      Engine: postgres
```

### 사례 4: 피처 플래그(Feature Flag) 관리

Parameter Store를 간단한 피처 플래그 시스템으로 활용할 수 있습니다.

```bash
# 피처 플래그 파라미터 생성
aws ssm put-parameter \
  --name "/app/feature-flags/new-checkout-flow" \
  --type "String" \
  --value '{"enabled": true, "rollout_percentage": 25, "allowed_users": ["user123", "user456"]}'

# 피처 플래그 조회
aws ssm get-parameter \
  --name "/app/feature-flags/new-checkout-flow" \
  --query 'Parameter.Value' \
  --output text

# 피처 플래그 일괄 조회
aws ssm get-parameters-by-path \
  --path "/app/feature-flags" \
  --recursive \
  --query 'Parameters[].{Name:Name,Value:Value}' \
  --output table
```

## 모범 사례/보안

### IAM 정책 설계

경로 기반으로 세밀한 접근 제어를 적용합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ],
      "Resource": "arn:aws:ssm:ap-northeast-2:123456789012:parameter/production/app/config/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter",
        "ssm:GetParameters"
      ],
      "Resource": "arn:aws:ssm:ap-northeast-2:123456789012:parameter/production/app/secrets/*",
      "Condition": {
        "StringEquals": {
          "ssm:ResourceTag/Team": "${aws:PrincipalTag/Team}"
        }
      }
    },
    {
      "Effect": "Allow",
      "Action": "kms:Decrypt",
      "Resource": "arn:aws:kms:ap-northeast-2:123456789012:key/key-id"
    }
  ]
}
```

### 네이밍 컨벤션

일관된 네이밍 컨벤션을 수립하는 것이 중요합니다. 권장 패턴은 다음과 같습니다.

```
/{environment}/{application}/{category}/{parameter-name}

예시:
/production/order-service/database/host
/staging/order-service/database/host
/production/order-service/secrets/api-key
/production/shared/config/log-level
```

### 캐싱 전략

Parameter Store API에는 처리량 제한(Throttling)이 있으므로, 적절한 캐싱 전략이 필수적입니다.

- Standard 계층: 기본 40 TPS (초당 트랜잭션)
- Advanced 계층: 기본 1,000 TPS
- 처리량 증가 요청 가능

애플리케이션 레벨에서 캐싱을 구현하거나, AWS Lambda의 경우 AWS Parameters and Secrets Lambda Extension을 사용하여 로컬 캐싱을 활용합니다.

### CloudTrail 감사

모든 Parameter Store API 호출은 CloudTrail에 기록됩니다. 민감한 파라미터에 대한 접근을 모니터링하기 위해 CloudTrail 로그를 정기적으로 검토해야 합니다.

```bash
# Parameter Store 관련 CloudTrail 이벤트 조회
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetParameter \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-31T23:59:59Z" \
  --query 'Events[].{Time:EventTime,User:Username,Event:EventName}' \
  --output table
```

## 관련 서비스 비교

### Parameter Store vs Secrets Manager

| 항목 | Parameter Store | Secrets Manager |
|------|----------------|------------------|
| 비용 | Standard 무료 / Advanced 유료 | 비밀당 $0.40/월 + API 호출 비용 |
| 자동 교체 | 미지원 (직접 구현 필요) | 기본 지원 (Lambda 기반) |
| 최대 값 크기 | 4 KB (Standard) / 8 KB (Advanced) | 64 KB |
| 계층 구조 | 지원 | 미지원 |
| 교차 계정 공유 | KMS 정책 필요 | 리소스 정책으로 간편 공유 |
| CloudFormation 참조 | resolve:ssm / resolve:ssm-secure | resolve:secretsmanager |
| 파라미터 유형 | String, StringList, SecureString | SecretString, SecretBinary |

### Parameter Store vs AWS AppConfig

| 항목 | Parameter Store | AppConfig |
|------|----------------|------------|
| 목적 | 파라미터/비밀 값 저장 | 애플리케이션 구성 배포 |
| 배포 전략 | 즉시 적용 | 점진적 배포 지원 |
| 검증 | 없음 | JSON Schema 검증 지원 |
| 롤백 | 수동 (버전 지정) | 자동 롤백 지원 |

### Parameter Store vs 환경 변수

| 항목 | Parameter Store | 환경 변수 |
|------|----------------|----------|
| 보안 | KMS 암호화, IAM 접근 제어 | 평문, 접근 제어 제한적 |
| 변경 관리 | 버전 관리, 변경 이력 추적 | 이력 없음 |
| 중앙 관리 | AWS 콘솔/CLI로 중앙 관리 | 배포 도구별 분산 관리 |
| 런타임 변경 | 가능 | 재시작 필요 |
| 비용 | API 호출 지연 | 추가 비용 없음, 빠른 접근 |

## 요약

AWS Systems Manager Parameter Store는 클라우드 환경에서 애플리케이션 구성과 비밀 값을 관리하기 위한 필수 서비스입니다. 무료 Standard 계층만으로도 대부분의 사용 사례를 충족할 수 있으며, KMS 암호화와 IAM 접근 제어를 통해 보안을 확보할 수 있습니다.

핵심 포인트를 정리하면 다음과 같습니다.

- 세 가지 파라미터 유형(String, StringList, SecureString)으로 다양한 구성 데이터를 저장할 수 있습니다.
- 계층적 경로 구조를 활용하여 파라미터를 논리적으로 분류하고 경로 기반 접근 제어를 적용합니다.
- 자동 버전 관리로 변경 이력을 추적하고, 필요 시 이전 버전으로 복원할 수 있습니다.
- EventBridge 통합으로 파라미터 변경 시 실시간 알림과 자동 대응이 가능합니다.
- ECS, Lambda, CloudFormation 등 다양한 AWS 서비스와 네이티브로 통합됩니다.
- 처리량 제한을 고려하여 적절한 캐싱 전략을 수립하는 것이 중요합니다.
- 단순 비밀 값 관리에는 Parameter Store, 자동 교체가 필요한 경우에는 Secrets Manager를 선택합니다.