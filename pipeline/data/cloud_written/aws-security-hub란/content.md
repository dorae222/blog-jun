<!-- infographic-hero -->
![AWS Security Hub 완벽 가이드: 클라우드 보안 상태 중앙 관리 핵심 요약](figures/infographic.svg)

*Figure: AWS Security Hub 완벽 가이드: 클라우드 보안 상태 중앙 관리 한 장 요약 인포그래픽*

## 개요

AWS Security Hub는 AWS 환경의 보안 상태를 중앙에서 종합적으로 관리할 수 있는 클라우드 보안 태세 관리(CSPM, Cloud Security Posture Management) 서비스입니다.

Security Hub는 다음과 같은 핵심 역할을 수행합니다.

- **보안 검사 자동화**: CIS AWS Foundations Benchmark, PCI DSS, AWS Foundational Security Best Practices 등의 보안 표준에 따라 자동으로 보안 검사를 수행합니다.
- **보안 결과 집계**: GuardDuty, Inspector, Macie, Firewall Manager 등 여러 AWS 보안 서비스의 결과를 한 곳에 집계합니다.
- **우선순위 지정**: 보안 결과에 심각도를 부여하고, 자동으로 정규화하여 우선순위를 지정합니다.
- **자동 대응**: EventBridge, Lambda를 활용하여 보안 결과에 대한 자동 대응을 구현할 수 있습니다.

수십 개의 AWS 계정과 여러 리전에 걸친 보안 상태를 개별적으로 확인하는 것은 사실상 불가능합니다. Security Hub는 이러한 복잡성을 해결하고 단일 대시보드에서 전체 보안 상태를 파악할 수 있게 해줍니다.

## 핵심 기능

### Security Hub 활성화

```bash
# Security Hub 활성화
aws securityhub enable-security-hub \
  --enable-default-standards \
  --tags Environment=Production

# 특정 보안 표준만 활성화하여 Security Hub 활성화
aws securityhub enable-security-hub \
  --no-enable-default-standards

# 개별 보안 표준 활성화
aws securityhub batch-enable-standards \
  --standards-subscription-requests '[{
    "StandardsArn": "arn:aws:securityhub:ap-northeast-2::standards/cis-aws-foundations-benchmark/v/1.4.0"
  }, {
    "StandardsArn": "arn:aws:securityhub:ap-northeast-2::standards/aws-foundational-security-best-practices/v/1.0.0"
  }]'
```

### 보안 표준 (Security Standards)

Security Hub에서 지원하는 주요 보안 표준은 다음과 같습니다.

| 보안 표준 | 설명 | 컨트롤 수 |
|----------|------|----------|
| AWS Foundational Security Best Practices (FSBP) | AWS 서비스별 보안 모범 사례 | 200+ |
| CIS AWS Foundations Benchmark v1.4.0 | CIS 보안 벤치마크 | 50+ |
| CIS AWS Foundations Benchmark v3.0.0 | 최신 CIS 벤치마크 | 60+ |
| PCI DSS v3.2.1 | 결제 카드 산업 데이터 보안 표준 | 30+ |
| NIST SP 800-53 Rev. 5 | 미국 정부 보안 표준 | 200+ |

```bash
# 활성화된 보안 표준 확인
aws securityhub get-enabled-standards \
  --query 'StandardsSubscriptions[*].{Standard:StandardsArn,Status:StandardsStatus}' \
  --output table

# 특정 보안 표준의 컨트롤 목록 확인
aws securityhub describe-standards-controls \
  --standards-subscription-arn "arn:aws:securityhub:ap-northeast-2:123456789012:subscription/cis-aws-foundations-benchmark/v/1.4.0" \
  --query 'Controls[?ControlStatus==`ENABLED`].{Id:ControlId,Title:Title,Severity:SeverityRating}' \
  --output table
```

### 보안 결과 (Findings)

Security Hub의 모든 보안 결과는 AWS Security Finding Format(ASFF)으로 정규화됩니다. 이를 통해 서로 다른 보안 서비스의 결과를 일관된 형식으로 처리할 수 있습니다.

```bash
# 심각도가 CRITICAL인 보안 결과 조회
aws securityhub get-findings \
  --filters '{
    "SeverityLabel": [{"Value": "CRITICAL", "Comparison": "EQUALS"}],
    "WorkflowStatus": [{"Value": "NEW", "Comparison": "EQUALS"}],
    "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}]
  }' \
  --sort-criteria '{"Field": "SeverityNormalized", "SortOrder": "desc"}' \
  --max-items 10

# 특정 AWS 서비스의 보안 결과 조회
aws securityhub get-findings \
  --filters '{
    "ProductName": [{"Value": "GuardDuty", "Comparison": "EQUALS"}],
    "RecordState": [{"Value": "ACTIVE", "Comparison": "EQUALS"}]
  }'

# 보안 결과 상태 업데이트
aws securityhub batch-update-findings \
  --finding-identifiers '[{
    "Id": "arn:aws:securityhub:ap-northeast-2:123456789012:finding/abc123",
    "ProductArn": "arn:aws:securityhub:ap-northeast-2::product/aws/securityhub"
  }]' \
  --workflow '{"Status": "RESOLVED"}' \
  --note '{"Text": "Remediated by applying encryption", "UpdatedBy": "security-team"}'
```

### 통합 보안 점수

Security Hub는 활성화된 보안 표준의 컨트롤 준수율을 기반으로 보안 점수를 제공합니다.

```bash
# 전체 보안 점수 확인
aws securityhub get-security-control-definitions \
  --query 'SecurityControlDefinitions[0:5].{Id:SecurityControlId,Title:Title,Severity:SeverityRating}' \
  --output table

# 표준별 컨트롤 상태 요약
aws securityhub describe-standards-controls \
  --standards-subscription-arn "arn:aws:securityhub:ap-northeast-2:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0" \
  --query 'Controls[].ControlStatus' \
  --output text | tr '\t' '\n' | sort | uniq -c
```

## 아키텍처/동작 원리

### Security Hub 데이터 흐름

Security Hub의 데이터 흐름은 다음과 같습니다.

```
[보안 서비스]              [Security Hub]              [대응]
                          
 GuardDuty -----+
 Inspector -----+
 Macie ---------+--->  Finding 집계   ---->  보안 점수
 Firewall Mgr --+      & 정규화 (ASFF)        대시보드
 Config Rules --+                    |
 3rd Party -----+                    +---->  EventBridge
                                     |         |
 [자동 보안 검사]                     |         v
                                     |      Lambda
 CIS Benchmark --+                   |      Step Functions
 FSBP ----------++--->  컨트롤 평가  |
 PCI DSS -------+                    +---->  Custom Action
 NIST 800-53 ---+                            (수동 대응)
```

### AWS Config와의 관계

Security Hub의 보안 검사는 내부적으로 AWS Config 규칙을 사용합니다. 따라서 Security Hub를 사용하려면 AWS Config가 활성화되어 있어야 합니다.

```bash
# AWS Config 상태 확인
aws configservice describe-configuration-recorders \
  --query 'ConfigurationRecorders[*].{Name:name,Recording:recordingGroup.allSupported}'

# AWS Config 활성화 (Security Hub 전제 조건)
aws configservice put-configuration-recorder \
  --configuration-recorder name=default,roleARN=arn:aws:iam::123456789012:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig \
  --recording-group allSupported=true,includeGlobalResourceTypes=true

aws configservice start-configuration-recorder --configuration-recorder-name default
```

### 멀티 계정/멀티 리전 관리

AWS Organizations와 통합하여 모든 계정과 리전의 보안 결과를 중앙에서 관리할 수 있습니다.

```bash
# 관리자 계정으로 지정
aws securityhub enable-organization-admin-account \
  --admin-account-id 123456789012

# 멤버 계정 자동 활성화 설정
aws securityhub update-organization-configuration \
  --auto-enable \
  --auto-enable-standards DEFAULT

# 멤버 계정 목록 확인
aws securityhub list-members \
  --query 'Members[*].{AccountId:AccountId,Status:MemberStatus}' \
  --output table

# 리전 집계 설정 (특정 리전에서 모든 리전의 결과 확인)
aws securityhub create-finding-aggregator \
  --region ap-northeast-2 \
  --region-linking-mode ALL_REGIONS
```

## 실전 활용

### 자동 대응 구현

Security Hub 결과에 대한 자동 대응 파이프라인을 구축합니다.

```bash
# EventBridge 규칙 생성 (CRITICAL 결과 감지)
aws events put-rule \
  --name SecurityHubCriticalFindings \
  --event-pattern '{
    "source": ["aws.securityhub"],
    "detail-type": ["Security Hub Findings - Imported"],
    "detail": {
      "findings": {
        "Severity": {
          "Label": ["CRITICAL"]
        },
        "Workflow": {
          "Status": ["NEW"]
        }
      }
    }
  }'

# SNS 대상 추가 (알림)
aws events put-targets \
  --rule SecurityHubCriticalFindings \
  --targets 'Id=1,Arn=arn:aws:sns:ap-northeast-2:123456789012:security-critical-alerts'
```

자동 대응 Lambda 함수의 예시입니다.

```python
import json
import boto3

def lambda_handler(event, context):
    """Security Hub CRITICAL 결과 자동 대응"""
    finding = event['detail']['findings'][0]
    
    control_id = finding.get('ProductFields', {}).get('ControlId', '')
    resource_type = finding['Resources'][0]['Type']
    resource_id = finding['Resources'][0]['Id']
    
    print(f"처리 중: {control_id} - {resource_type} - {resource_id}")
    
    # S3 버킷 퍼블릭 액세스 차단
    if control_id == 'S3.2':  # S3 bucket should prohibit public read access
        s3 = boto3.client('s3')
        bucket_name = resource_id.split(':::')[-1]
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                'BlockPublicAcls': True,
                'IgnorePublicAcls': True,
                'BlockPublicPolicy': True,
                'RestrictPublicBuckets': True
            }
        )
        print(f"S3 버킷 {bucket_name}의 퍼블릭 액세스를 차단했습니다.")
    
    # 미사용 보안 그룹 삭제
    elif control_id == 'EC2.22':  # Unused EC2 security groups should be removed
        ec2 = boto3.client('ec2')
        sg_id = resource_id.split('/')[-1]
        try:
            ec2.delete_security_group(GroupId=sg_id)
            print(f"미사용 보안 그룹 {sg_id}를 삭제했습니다.")
        except Exception as e:
            print(f"보안 그룹 삭제 실패: {e}")
    
    # Security Hub 결과 상태 업데이트
    securityhub = boto3.client('securityhub')
    securityhub.batch_update_findings(
        FindingIdentifiers=[{
            'Id': finding['Id'],
            'ProductArn': finding['ProductArn']
        }],
        Workflow={'Status': 'RESOLVED'},
        Note={
            'Text': 'Auto-remediated by Lambda function',
            'UpdatedBy': 'security-automation'
        }
    )
    
    return {'statusCode': 200}
```

### 커스텀 보안 결과 전송

자체 보안 도구의 결과를 Security Hub로 전송할 수 있습니다.

```bash
# 커스텀 보안 결과 전송
aws securityhub batch-import-findings \
  --findings '[{
    "SchemaVersion": "2018-10-08",
    "Id": "custom/vulnerability-scan/finding-001",
    "ProductArn": "arn:aws:securityhub:ap-northeast-2:123456789012:product/123456789012/default",
    "GeneratorId": "custom-vulnerability-scanner",
    "AwsAccountId": "123456789012",
    "Types": ["Software and Configuration Checks/Vulnerabilities/CVE"],
    "CreatedAt": "2024-01-15T09:00:00Z",
    "UpdatedAt": "2024-01-15T09:00:00Z",
    "Severity": {"Label": "HIGH"},
    "Title": "Critical vulnerability found in application dependency",
    "Description": "CVE-2024-XXXX found in log4j 2.14.0",
    "Resources": [{
      "Type": "AwsEcsTaskDefinition",
      "Id": "arn:aws:ecs:ap-northeast-2:123456789012:task-definition/my-app:10",
      "Region": "ap-northeast-2"
    }],
    "WorkflowStatus": "NEW",
    "RecordState": "ACTIVE"
  }]'
```

### 특정 컨트롤 비활성화

환경에 맞지 않는 컨트롤은 비활성화할 수 있습니다.

```bash
# 특정 컨트롤 비활성화
aws securityhub update-standards-control \
  --standards-control-arn "arn:aws:securityhub:ap-northeast-2:123456789012:control/aws-foundational-security-best-practices/v/1.0.0/IAM.6" \
  --control-status DISABLED \
  --disabled-reason "Hardware MFA is not applicable for our organization"

# 비활성화된 컨트롤 확인
aws securityhub describe-standards-controls \
  --standards-subscription-arn "arn:aws:securityhub:ap-northeast-2:123456789012:subscription/aws-foundational-security-best-practices/v/1.0.0" \
  --query 'Controls[?ControlStatus==`DISABLED`].{Id:ControlId,Reason:DisabledReason}' \
  --output table
```

## 모범 사례/보안

### 단계별 도입 전략

1. **1단계**: AWS Foundational Security Best Practices (FSBP) 활성화
2. **2단계**: CRITICAL/HIGH 결과 우선 해결
3. **3단계**: CIS Benchmark 활성화 및 준수
4. **4단계**: 자동 대응 파이프라인 구축
5. **5단계**: 멀티 계정/멀티 리전 통합

### 비용 관리

Security Hub 비용은 보안 검사 수와 결과 수에 따라 결정됩니다.

| 항목 | 비용 |
|------|------|
| 보안 검사 | 첫 100,000건/계정/리전/월 무료, 이후 건당 $0.0010 |
| Finding 수집 이벤트 | 첫 10,000건/계정/리전/월 무료, 이후 건당 $0.00003 |

비용을 최적화하려면 불필요한 보안 표준을 비활성화하고, 환경에 적용되지 않는 컨트롤은 비활성화합니다.

### 보안 권장 사항

1. **모든 리전에서 활성화**: 사용하지 않는 리전에서도 Security Hub를 활성화하여 무단 활동을 탐지합니다.
2. **리전 집계 활성화**: 단일 리전에서 모든 리전의 결과를 확인합니다.
3. **자동 대응 구현**: 반복적인 보안 결과에 대해 자동 대응을 구현합니다.
4. **정기 리뷰**: 주간/월간으로 보안 점수와 미해결 결과를 리뷰합니다.
5. **비활성화 사유 문서화**: 컨트롤을 비활성화하는 경우 명확한 사유를 기록합니다.

## 관련 서비스 비교

### Security Hub vs GuardDuty vs Inspector

| 항목 | Security Hub | GuardDuty | Inspector |
|------|-------------|-----------|----------|
| 역할 | 보안 상태 중앙 관리 | 위협 탐지 | 취약점 스캔 |
| 데이터 소스 | 다른 보안 서비스 결과 + 자체 검사 | VPC Flow Logs, DNS, CloudTrail | EC2, ECR, Lambda |
| 검사 유형 | 설정 준수 (CSPM) | 행위 기반 이상 탐지 | CVE 기반 취약점 |
| 자동 대응 | EventBridge 연동 | EventBridge 연동 | EventBridge 연동 |
| 규정 준수 | CIS, PCI DSS, NIST | 해당 없음 | 해당 없음 |

이 세 서비스는 상호 보완적입니다. GuardDuty와 Inspector의 결과를 Security Hub로 집계하여 통합 관리하는 것이 권장됩니다.

### Security Hub vs AWS Config

| 항목 | Security Hub | AWS Config |
|------|-------------|------------|
| 초점 | 보안 모범 사례 준수 | 리소스 설정 변경 추적 |
| 규칙 | 보안 표준 기반 | 사용자 정의 가능 |
| 집계 | 멀티 서비스 결과 통합 | Config 결과만 |
| 점수 | 보안 점수 제공 | 준수율 대시보드 |

## 요약

AWS Security Hub는 AWS 환경의 보안 상태를 중앙에서 관리하는 필수 서비스입니다.

1. **보안 표준**(CIS, FSBP, PCI DSS, NIST)에 따라 자동으로 보안 검사를 수행합니다.
2. **GuardDuty, Inspector, Macie** 등 다른 보안 서비스의 결과를 **단일 대시보드**에서 확인할 수 있습니다.
3. **ASFF(AWS Security Finding Format)**로 모든 보안 결과를 정규화하여 일관된 처리가 가능합니다.
4. **AWS Organizations와 통합**하여 멀티 계정, 멀티 리전 보안 관리를 지원합니다.
5. **EventBridge와 Lambda**를 활용한 자동 대응 파이프라인을 구축할 수 있습니다.
6. AWS Config가 **전제 조건**이므로 먼저 활성화해야 합니다.
7. **단계별 도입**을 통해 점진적으로 보안 수준을 높여가는 것이 효과적입니다.