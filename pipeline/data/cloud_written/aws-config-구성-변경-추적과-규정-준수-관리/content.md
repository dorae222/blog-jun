## 개요

AWS Config는 AWS 리소스의 구성(Configuration)을 지속적으로 모니터링하고 기록하는 서비스입니다. 리소스가 생성, 수정, 삭제될 때마다 구성 변경 내역이 자동으로 기록되며, 이를 기반으로 리소스가 조직의 보안 정책이나 규정 준수 요구사항에 부합하는지 자동으로 평가할 수 있습니다.

클라우드 환경에서는 리소스의 변경이 빈번하게 발생합니다. 보안 그룹 규칙 변경, S3 버킷 정책 수정, IAM 역할 권한 변경 등 매일 수많은 구성 변경이 이루어집니다. 이러한 변경이 보안 정책에 위배되거나, 규정 준수 요구사항을 충족하지 못하는 경우를 수동으로 모니터링하는 것은 사실상 불가능합니다.

AWS Config는 이 문제를 해결합니다. Config Rules를 정의하면, 리소스 구성 변경이 발생할 때마다 자동으로 규칙을 평가하여 규정 준수(COMPLIANT) 또는 미준수(NON_COMPLIANT) 여부를 판단합니다. 미준수 리소스에 대해서는 자동 수정(Auto Remediation)을 설정하여, 정책 위반을 자동으로 해결할 수도 있습니다.

AWS Config는 CloudTrail과 상호 보완적입니다. CloudTrail이 "누가 무엇을 했는지"(API 활동)를 기록한다면, AWS Config는 "리소스가 어떻게 변경되었는지"(구성 변경)를 기록합니다. 두 서비스를 함께 사용하면 변경의 "원인"과 "결과"를 모두 추적할 수 있습니다.

## 핵심 기능

### 구성 기록 (Configuration Recording)

AWS Config는 지원되는 AWS 리소스의 구성을 지속적으로 기록합니다. 기록되는 정보에는 리소스의 메타데이터, 속성, 다른 리소스와의 관계, 구성 변경 이력 등이 포함됩니다.

지원되는 리소스 유형은 계속 확장되고 있으며, EC2, S3, IAM, VPC, RDS, Lambda, ECS 등 주요 서비스의 거의 모든 리소스를 지원합니다.

### Config Rules

Config Rules는 리소스의 구성이 특정 조건을 만족하는지 평가하는 규칙입니다. 세 가지 유형이 있습니다.

**1. AWS 관리형 규칙 (Managed Rules)**

AWS가 사전 정의한 규칙으로, 300개 이상이 제공됩니다. 코드 작성 없이 바로 사용할 수 있습니다.

예시:
- `s3-bucket-server-side-encryption-enabled`: S3 버킷 암호화 확인
- `ec2-instance-no-public-ip`: EC2에 퍼블릭 IP 미할당 확인
- `iam-root-access-key-check`: 루트 계정 액세스 키 미사용 확인
- `rds-instance-public-access-check`: RDS 퍼블릭 접근 차단 확인

**2. 커스텀 규칙 (Custom Rules)**

Lambda 함수로 구현하는 커스텀 평가 로직입니다. 관리형 규칙으로 해결되지 않는 조직 고유의 정책을 구현할 수 있습니다.

**3. CloudFormation Guard 규칙**

CloudFormation Guard 정책 언어로 작성하는 규칙입니다. Lambda 함수 없이도 커스텀 규칙을 정의할 수 있습니다.

### Conformance Packs

여러 Config Rules와 수정 작업을 하나의 패키지로 묶어서 관리하는 기능입니다. PCI DSS, CIS AWS Foundations 등 규정 준수 프레임워크에 맞는 사전 정의된 패키지를 제공합니다.

### 자동 수정 (Auto Remediation)

Config Rules 평가 결과 미준수(NON_COMPLIANT)로 판정된 리소스에 대해 자동으로 수정 작업을 수행합니다. SSM Automation 문서를 실행하여 미준수 상태를 자동으로 해결합니다.

### Config Aggregator

여러 AWS 계정과 리전의 Config 데이터를 하나의 계정에서 중앙 집중적으로 조회할 수 있습니다. AWS Organizations와 통합하여 조직 전체의 규정 준수 현황을 한눈에 파악할 수 있습니다.

## 아키텍처/동작 원리

### Config 동작 흐름

1. AWS 리소스가 생성, 수정, 삭제됩니다.
2. Config가 변경을 감지하고 구성 항목(Configuration Item)을 생성합니다.
3. 구성 항목이 Config 히스토리에 저장되고 S3 버킷으로 전달됩니다.
4. 관련된 Config Rules가 트리거되어 규칙 평가가 실행됩니다.
5. 평가 결과가 COMPLIANT 또는 NON_COMPLIANT로 기록됩니다.
6. NON_COMPLIANT인 경우, 자동 수정이 설정되어 있으면 수정 작업이 실행됩니다.
7. SNS 알림이 전송됩니다.

### Config 설정

```bash
# Config Recorder 생성 (모든 리소스 기록)
aws configservice put-configuration-recorder \
  --configuration-recorder '{"name": "default", "roleARN": "arn:aws:iam::123456789012:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig", "recordingGroup": {"allSupported": true, "includeGlobalResourceTypes": true}}'

# 전달 채널 설정 (S3 + SNS)
aws configservice put-delivery-channel \
  --delivery-channel '{
    "name": "default",
    "s3BucketName": "my-config-bucket",
    "s3KeyPrefix": "config",
    "snsTopicARN": "arn:aws:sns:ap-northeast-2:123456789012:config-notifications",
    "configSnapshotDeliveryProperties": {
      "deliveryFrequency": "TwentyFour_Hours"
    }
  }'

# Config 기록 시작
aws configservice start-configuration-recorder \
  --configuration-recorder-name default
```

```bash
# Config Recorder 상태 확인
aws configservice describe-configuration-recorder-status

# 전달 채널 상태 확인
aws configservice describe-delivery-channel-status
```

### Config Rules 설정

```bash
# AWS 관리형 규칙 추가: S3 버킷 퍼블릭 접근 차단
aws configservice put-config-rule \
  --config-rule '{
    "ConfigRuleName": "s3-bucket-public-read-prohibited",
    "Source": {
      "Owner": "AWS",
      "SourceIdentifier": "S3_BUCKET_PUBLIC_READ_PROHIBITED"
    },
    "Scope": {
      "ComplianceResourceTypes": ["AWS::S3::Bucket"]
    }
  }'

# AWS 관리형 규칙 추가: EC2 인스턴스 퍼블릭 IP 금지
aws configservice put-config-rule \
  --config-rule '{
    "ConfigRuleName": "ec2-instance-no-public-ip",
    "Source": {
      "Owner": "AWS",
      "SourceIdentifier": "EC2_INSTANCE_NO_PUBLIC_IP_V2"
    },
    "Scope": {
      "ComplianceResourceTypes": ["AWS::EC2::Instance"]
    }
  }'

# AWS 관리형 규칙 추가: 보안 그룹 SSH 접근 제한
aws configservice put-config-rule \
  --config-rule '{
    "ConfigRuleName": "restricted-ssh",
    "Source": {
      "Owner": "AWS",
      "SourceIdentifier": "INCOMING_SSH_DISABLED"
    },
    "Scope": {
      "ComplianceResourceTypes": ["AWS::EC2::SecurityGroup"]
    }
  }'

# EBS 볼륨 암호화 확인
aws configservice put-config-rule \
  --config-rule '{
    "ConfigRuleName": "encrypted-volumes",
    "Source": {
      "Owner": "AWS",
      "SourceIdentifier": "ENCRYPTED_VOLUMES"
    },
    "Scope": {
      "ComplianceResourceTypes": ["AWS::EC2::Volume"]
    }
  }'
```

### 자동 수정 설정

```bash
# S3 퍼블릭 접근 차단 자동 수정
aws configservice put-remediation-configurations \
  --remediation-configurations '[{
    "ConfigRuleName": "s3-bucket-public-read-prohibited",
    "TargetType": "SSM_DOCUMENT",
    "TargetId": "AWS-DisableS3BucketPublicReadWrite",
    "TargetVersion": "1",
    "Parameters": {
      "S3BucketName": {
        "ResourceValue": {
          "Value": "RESOURCE_ID"
        }
      },
      "AutomationAssumeRole": {
        "StaticValue": {
          "Values": ["arn:aws:iam::123456789012:role/ConfigRemediationRole"]
        }
      }
    },
    "Automatic": true,
    "MaximumAutomaticAttempts": 3,
    "RetryAttemptSeconds": 60
  }]'
```

## 실전 활용

### 사례 1: 규정 준수 대시보드

```bash
# 전체 규칙의 규정 준수 현황 조회
aws configservice describe-compliance-by-config-rule \
  --query 'ComplianceByConfigRules[*].{Rule:ConfigRuleName,Status:Compliance.ComplianceType}' \
  --output table

# 미준수 리소스 목록 조회
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name s3-bucket-public-read-prohibited \
  --compliance-types NON_COMPLIANT \
  --query 'EvaluationResults[*].{ResourceType:EvaluationResultIdentifier.EvaluationResultQualifier.ResourceType,ResourceId:EvaluationResultIdentifier.EvaluationResultQualifier.ResourceId,Time:ResultRecordedTime}' \
  --output table
```

### 사례 2: 리소스 구성 변경 이력 추적

```bash
# 특정 리소스의 구성 변경 이력 조회
aws configservice get-resource-config-history \
  --resource-type AWS::EC2::SecurityGroup \
  --resource-id sg-0123456789abcdef0 \
  --limit 10 \
  --query 'configurationItems[*].{Time:configurationItemCaptureTime,Status:configurationItemStatus}' \
  --output table

# 특정 시점의 리소스 구성 조회
aws configservice get-resource-config-history \
  --resource-type AWS::EC2::SecurityGroup \
  --resource-id sg-0123456789abcdef0 \
  --earlier-time 2024-01-01T00:00:00Z \
  --later-time 2024-01-15T23:59:59Z
```

### 사례 3: 고급 쿼리 (Config Advanced Query)

SQL 기반의 고급 쿼리를 사용하여 리소스 구성을 분석할 수 있습니다.

```bash
# 퍼블릭 IP가 할당된 EC2 인스턴스 조회
aws configservice select-resource-config \
  --expression "SELECT resourceId, resourceName, configuration.instanceType, configuration.publicIpAddress WHERE resourceType = 'AWS::EC2::Instance' AND configuration.publicIpAddress IS NOT NULL"

# 암호화되지 않은 EBS 볼륨 조회
aws configservice select-resource-config \
  --expression "SELECT resourceId, configuration.size, configuration.encrypted WHERE resourceType = 'AWS::EC2::Volume' AND configuration.encrypted = false"

# 태그가 누락된 리소스 조회
aws configservice select-resource-config \
  --expression "SELECT resourceId, resourceType, tags WHERE resourceType IN ('AWS::EC2::Instance', 'AWS::RDS::DBInstance') AND tags.tag('Environment') IS NULL"
```

### 사례 4: Conformance Pack 배포

```bash
# CIS AWS Foundations Benchmark Conformance Pack 배포
aws configservice put-conformance-pack \
  --conformance-pack-name "CIS-AWS-Foundations" \
  --template-s3-uri "s3://my-config-bucket/conformance-packs/cis-aws-foundations.yaml" \
  --delivery-s3-bucket "my-config-bucket" \
  --delivery-s3-key-prefix "conformance-packs-results"

# Conformance Pack 규정 준수 현황 조회
aws configservice get-conformance-pack-compliance-summary \
  --conformance-pack-names "CIS-AWS-Foundations"
```

### 사례 5: 커스텀 Config Rule (Lambda)

```python
import json
import boto3

def lambda_handler(event, context):
    """EC2 인스턴스에 'Environment' 태그가 있는지 확인하는 커스텀 규칙"""
    config = boto3.client('config')
    
    invoking_event = json.loads(event['invokingEvent'])
    configuration_item = invoking_event['configurationItem']
    
    resource_id = configuration_item['resourceId']
    tags = configuration_item.get('tags', {})
    
    compliance_type = 'COMPLIANT'
    annotation = 'Environment tag is present'
    
    if 'Environment' not in tags:
        compliance_type = 'NON_COMPLIANT'
        annotation = 'Missing required tag: Environment'
    elif tags['Environment'] not in ['production', 'staging', 'development']:
        compliance_type = 'NON_COMPLIANT'
        annotation = f"Invalid Environment tag value: {tags['Environment']}"
    
    config.put_evaluations(
        Evaluations=[
            {
                'ComplianceResourceType': configuration_item['resourceType'],
                'ComplianceResourceId': resource_id,
                'ComplianceType': compliance_type,
                'Annotation': annotation,
                'OrderingTimestamp': configuration_item['configurationItemCaptureTime']
            }
        ],
        ResultToken=event['resultToken']
    )
```

```bash
# 커스텀 규칙 등록
aws configservice put-config-rule \
  --config-rule '{
    "ConfigRuleName": "required-environment-tag",
    "Source": {
      "Owner": "CUSTOM_LAMBDA",
      "SourceIdentifier": "arn:aws:lambda:ap-northeast-2:123456789012:function:config-rule-environment-tag",
      "SourceDetails": [{
        "EventSource": "aws.config",
        "MessageType": "ConfigurationItemChangeNotification"
      }]
    },
    "Scope": {
      "ComplianceResourceTypes": ["AWS::EC2::Instance"]
    }
  }'
```

## 모범 사례/보안

### 보안 모범 사례

1. **모든 리소스 기록**: `allSupported: true`로 설정하여 지원되는 모든 리소스의 구성을 기록합니다.
2. **글로벌 리소스 포함**: `includeGlobalResourceTypes: true`로 IAM 등 글로벌 리소스도 기록합니다.
3. **S3 버킷 보안**: Config 구성 스냅샷이 저장되는 S3 버킷에 대한 접근을 제한합니다.
4. **자동 수정 주의**: 프로덕션 환경에서 자동 수정을 활성화할 때는 충분한 테스트 후 적용합니다.
5. **멀티 계정 Aggregator**: 조직 전체의 규정 준수를 중앙에서 모니터링합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "config:GetComplianceDetailsByConfigRule",
        "config:GetComplianceSummaryByConfigRule",
        "config:DescribeComplianceByConfigRule",
        "config:DescribeConfigRules",
        "config:GetResourceConfigHistory",
        "config:SelectResourceConfig"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": [
        "config:DeleteConfigRule",
        "config:DeleteConfigurationRecorder",
        "config:StopConfigurationRecorder"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:PrincipalArn": "arn:aws:iam::123456789012:role/SecurityAdmin"
        }
      }
    }
  ]
}
```

### 비용 최적화

AWS Config의 비용은 기록된 구성 항목 수와 Config Rule 평가 횟수에 따라 결정됩니다.

1. **기록 범위 최적화**: 모든 리소스 대신 필요한 리소스 유형만 기록할 수 있습니다.
2. **규칙 평가 주기 조정**: 변경 트리거 대신 주기적 평가(24시간)를 사용하여 평가 횟수를 줄일 수 있습니다.
3. **스냅샷 빈도 조정**: 구성 스냅샷 전달 빈도를 업무 요구사항에 맞게 조정합니다.

```bash
# Config 기록 리소스 유형 제한 (비용 최적화)
aws configservice put-configuration-recorder \
  --configuration-recorder '{
    "name": "default",
    "roleARN": "arn:aws:iam::123456789012:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig",
    "recordingGroup": {
      "allSupported": false,
      "includeGlobalResourceTypes": true,
      "resourceTypes": [
        "AWS::EC2::Instance",
        "AWS::EC2::SecurityGroup",
        "AWS::S3::Bucket",
        "AWS::IAM::Role",
        "AWS::IAM::Policy",
        "AWS::RDS::DBInstance",
        "AWS::Lambda::Function"
      ]
    }
  }'
```

### Config Aggregator 설정

```bash
# 조직 수준 Aggregator 생성
aws configservice put-configuration-aggregator \
  --configuration-aggregator-name org-aggregator \
  --organization-aggregation-source '{
    "RoleArn": "arn:aws:iam::123456789012:role/ConfigAggregatorRole",
    "AwsRegions": ["ap-northeast-2", "us-east-1", "eu-west-1"],
    "AllAwsRegions": false
  }'

# Aggregator에서 규정 준수 현황 조회
aws configservice get-aggregate-compliance-details-by-config-rule \
  --configuration-aggregator-name org-aggregator \
  --config-rule-name s3-bucket-server-side-encryption-enabled \
  --compliance-type NON_COMPLIANT \
  --account-id 234567890123 \
  --aws-region ap-northeast-2
```

## 관련 서비스 비교

| 항목 | AWS Config | CloudTrail | Security Hub | Systems Manager |
|------|-----------|-----------|-------------|----------------|
| 주요 목적 | 구성 관리/규정 준수 | API 활동 감사 | 통합 보안 대시보드 | 운영 관리 |
| 기록 대상 | 리소스 구성 변경 | API 호출 | 보안 알림 집계 | 인스턴스 상태/패치 |
| 규칙 평가 | Config Rules | 미지원 | 보안 표준 확인 | 컴플라이언스 |
| 자동 수정 | SSM Automation | 미지원 | 미지원 (연동) | SSM Automation |
| 쿼리 기능 | Advanced Query (SQL) | CloudTrail Lake (SQL) | 미지원 | Inventory Query |
| 멀티 계정 | Aggregator | 조직 트레일 | 위임 관리자 | Organizations 통합 |
| 비용 | 구성 항목 + 규칙 평가 | 이벤트 수 | 보안 확인 수 | 무료 (일부 유료) |

AWS Config와 Security Hub는 자주 함께 사용됩니다. Security Hub는 Config Rules의 결과를 포함한 다양한 보안 알림을 통합하여 보여주며, 조직 전체의 보안 상태를 한눈에 파악할 수 있게 해줍니다.

## 요약

AWS Config는 AWS 리소스의 구성 변경을 추적하고 규정 준수를 자동으로 평가하는 서비스입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **지속적 구성 기록**: 모든 리소스의 구성 변경을 자동으로 기록하고 이력을 관리합니다.
- **300+ 관리형 규칙**: AWS가 제공하는 사전 정의된 규칙으로 즉시 규정 준수 평가를 시작할 수 있습니다.
- **커스텀 규칙**: Lambda 또는 CloudFormation Guard로 조직 고유의 정책을 구현합니다.
- **자동 수정**: 미준수 리소스를 SSM Automation으로 자동 수정합니다.
- **Conformance Packs**: CIS, PCI DSS 등 규정 준수 프레임워크를 패키지로 배포합니다.
- **고급 쿼리**: SQL 기반 쿼리로 리소스 구성을 분석합니다.
- **멀티 계정 Aggregator**: 조직 전체의 규정 준수 현황을 중앙에서 관리합니다.

AWS Config는 CloudTrail, Security Hub, GuardDuty와 함께 AWS 보안 거버넌스의 핵심 축을 구성합니다. 모든 프로덕션 AWS 계정에서 Config를 활성화하고, 조직의 보안 정책에 맞는 규칙을 설정하는 것이 클라우드 거버넌스의 기본입니다.