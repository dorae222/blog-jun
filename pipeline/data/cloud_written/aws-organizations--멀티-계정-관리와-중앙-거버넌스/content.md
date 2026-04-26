<!-- infographic-hero -->
![AWS Organizations 핵심 요약](figures/infographic.svg)

*Figure: AWS Organizations 한 장 요약 인포그래픽*

## 개요

AWS Organizations는 여러 AWS 계정을 하나의 조직(Organization)으로 묶어 중앙에서 관리할 수 있게 해주는 서비스입니다. 단일 계정으로 시작한 AWS 환경이 성장하면서 팀별, 프로젝트별, 환경별로 계정을 분리해야 하는 시점이 옵니다. Organizations는 이러한 멀티 계정 환경의 거버넌스, 비용 관리, 보안 정책을 중앙에서 통합 관리합니다.

AWS는 공식적으로 멀티 계정 전략을 권장합니다. 단일 계정에서 모든 워크로드를 운영하면 보안 경계가 모호해지고, 비용 추적이 어려워지며, 서비스 한도(Quota)가 공유되는 문제가 발생합니다. Organizations를 통해 계정을 분리하면 이러한 문제를 근본적으로 해결할 수 있습니다.

### 멀티 계정 전략의 핵심 원칙

- **보안 격리**: 워크로드 간 보안 경계를 명확히 분리합니다.
- **비용 가시성**: 팀별, 프로젝트별 비용을 정확하게 추적합니다.
- **서비스 한도 격리**: 한 워크로드가 다른 워크로드의 서비스 한도에 영향을 주지 않습니다.
- **거버넌스**: 일관된 보안 정책을 조직 전체에 적용합니다.

## 핵심 기능

### 1. 조직 구조 (Organization Structure)

**Root**
- 조직의 최상위 컨테이너입니다.
- 모든 OU와 계정의 부모 역할을 합니다.
- Root에 적용된 SCP는 조직 전체에 영향을 미칩니다.

**OU (Organizational Unit)**
- 계정을 논리적으로 그룹화하는 컨테이너입니다.
- OU 안에 하위 OU를 생성할 수 있습니다 (최대 5단계 깊이).
- OU에 적용된 SCP는 해당 OU와 그 하위 모든 OU/계정에 적용됩니다.

**계정 (Account)**
- 개별 AWS 계정입니다.
- 관리 계정(Management Account): 조직을 생성하고 관리하는 계정입니다. SCP의 영향을 받지 않습니다.
- 멤버 계정(Member Account): 조직에 속한 나머지 모든 계정입니다.

```bash
# 조직 생성
aws organizations create-organization \
  --feature-set ALL

# 조직 정보 확인
aws organizations describe-organization \
  --query 'Organization.{Id:Id,MasterAccountId:MasterAccountId,FeatureSet:FeatureSet}' \
  --output json

# OU 생성
aws organizations create-organizational-unit \
  --parent-id r-abc1 \
  --name "Security"

aws organizations create-organizational-unit \
  --parent-id r-abc1 \
  --name "Workloads"

aws organizations create-organizational-unit \
  --parent-id ou-abc1-workloads \
  --name "Production"

aws organizations create-organizational-unit \
  --parent-id ou-abc1-workloads \
  --name "Non-Production"

# 새 계정 생성
aws organizations create-account \
  --email "app-prod@example.com" \
  --account-name "App-A Production" \
  --iam-user-access-to-billing ALLOW

# 계정을 특정 OU로 이동
aws organizations move-account \
  --account-id 123456789012 \
  --source-parent-id r-abc1 \
  --destination-parent-id ou-abc1-production

# 조직 구조 조회
aws organizations list-roots \
  --query 'Roots[0].Id' \
  --output text

aws organizations list-organizational-units-for-parent \
  --parent-id r-abc1 \
  --query 'OrganizationalUnits[*].{Id:Id,Name:Name}' \
  --output table

aws organizations list-accounts-for-parent \
  --parent-id ou-abc1-production \
  --query 'Accounts[*].{Id:Id,Name:Name,Email:Email,Status:Status}' \
  --output table
```

### 2. 서비스 제어 정책 (SCP - Service Control Policies)

SCP는 Organizations의 가장 강력한 거버넌스 도구입니다. OU 또는 계정에 적용하여 허용되는 AWS API 호출을 제한합니다.

**SCP의 핵심 특성**

- SCP는 권한을 부여하지 않습니다. 최대 허용 범위를 정의합니다.
- 실제 권한 = IAM 정책 교집합 SCP 허용 범위
- 관리 계정에는 SCP가 적용되지 않습니다.
- 기본 SCP인 `FullAWSAccess`는 모든 서비스를 허용합니다.

**Deny 기반 SCP 예시**

특정 리전 외에서의 서비스 사용을 금지하는 SCP입니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyAllOutsideAllowedRegions",
      "Effect": "Deny",
      "NotAction": [
        "a]4iam:*",
        "organizations:*",
        "route53:*",
        "budgets:*",
        "waf:*",
        "cloudfront:*",
        "globalaccelerator:*",
        "importexport:*",
        "support:*",
        "sts:*",
        "health:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "ap-northeast-2",
            "us-east-1"
          ]
        }
      }
    }
  ]
}
```

```bash
# SCP 생성
aws organizations create-policy \
  --name "DenyRegionRestriction" \
  --description "Deny actions outside allowed regions" \
  --type SERVICE_CONTROL_POLICY \
  --content file://deny-region-restriction.json

# SCP를 OU에 연결
aws organizations attach-policy \
  --policy-id p-abc123 \
  --target-id ou-abc1-workloads

# 특정 OU에 연결된 SCP 목록 조회
aws organizations list-policies-for-target \
  --target-id ou-abc1-workloads \
  --filter SERVICE_CONTROL_POLICY \
  --query 'Policies[*].{Id:Id,Name:Name,Description:Description}' \
  --output table

# SCP 내용 확인
aws organizations describe-policy \
  --policy-id p-abc123 \
  --query 'Policy.{Name:PolicySummary.Name,Content:Content}' \
  --output json

# SCP 분리
aws organizations detach-policy \
  --policy-id p-abc123 \
  --target-id ou-abc1-workloads
```

### 3. 통합 결제 (Consolidated Billing)

모든 멤버 계정의 비용이 관리 계정으로 통합되어 청구됩니다.

**통합 결제의 이점**

- **볼륨 할인**: 전체 사용량이 합산되어 더 높은 할인 구간에 도달할 수 있습니다.
- **RI/Savings Plans 공유**: 하나의 계정에서 구매한 Reserved Instance나 Savings Plans가 조직 전체에서 공유됩니다.
- **단일 청구서**: 하나의 관리 계정으로 통합 청구되어 결제 관리가 간편합니다.

```bash
# 조직의 모든 계정 목록 (결제 관련)
aws organizations list-accounts \
  --query 'Accounts[*].{Id:Id,Name:Name,Email:Email,JoinedMethod:JoinedMethod,Status:Status}' \
  --output table

# 특정 계정의 비용 조회 (Cost Explorer API)
aws ce get-cost-and-usage \
  --time-period Start=2025-01-01,End=2025-01-31 \
  --granularity MONTHLY \
  --metrics "BlendedCost" "UnblendedCost" \
  --group-by Type=DIMENSION,Key=LINKED_ACCOUNT \
  --output json
```

### 4. 위임 관리자 (Delegated Administrator)

관리 계정에서 직접 모든 서비스를 운영하는 것은 보안 위험이 높습니다. 위임 관리자 기능을 사용하면 특정 AWS 서비스의 관리 권한을 멤버 계정에 위임할 수 있습니다.

```bash
# 보안 계정을 SecurityHub의 위임 관리자로 지정
aws organizations register-delegated-administrator \
  --account-id 444455556666 \
  --service-principal securityhub.amazonaws.com

# GuardDuty 위임 관리자 지정
aws organizations register-delegated-administrator \
  --account-id 444455556666 \
  --service-principal guardduty.amazonaws.com

# Config 위임 관리자 지정
aws organizations register-delegated-administrator \
  --account-id 444455556666 \
  --service-principal config.amazonaws.com

# 위임 관리자 목록 확인
aws organizations list-delegated-administrators \
  --query 'DelegatedAdministrators[*].{AccountId:Id,Name:Name,Services:DelegationEnabledDate}' \
  --output table

# 특정 서비스의 위임 관리자 확인
aws organizations list-delegated-administrators \
  --service-principal securityhub.amazonaws.com \
  --output json
```

### 5. 정책 유형

Organizations는 SCP 외에도 다양한 정책 유형을 지원합니다.

| 정책 유형 | 설명 |
|----------|------|
| SCP (Service Control Policy) | AWS API 호출 제한 |
| Tag Policy | 리소스 태그 표준 강제 |
| Backup Policy | 백업 정책 중앙 관리 |
| AI Services Opt-out Policy | AI 서비스의 데이터 사용 옵트아웃 |

```bash
# 태그 정책 활성화
aws organizations enable-policy-type \
  --root-id r-abc1 \
  --policy-type TAG_POLICY

# 태그 정책 생성 - 리소스에 필수 태그 강제
aws organizations create-policy \
  --name "RequiredTags" \
  --description "Enforce required tags on resources" \
  --type TAG_POLICY \
  --content '{
    "tags": {
      "Environment": {
        "tag_key": {"@@assign": "Environment"},
        "tag_value": {"@@assign": ["Production", "Staging", "Development", "Sandbox"]},
        "enforced_for": {"@@assign": ["ec2:instance", "ec2:volume", "rds:db", "s3:bucket"]}
      },
      "CostCenter": {
        "tag_key": {"@@assign": "CostCenter"},
        "enforced_for": {"@@assign": ["ec2:instance", "rds:db"]}
      }
    }
  }'

# 백업 정책 활성화
aws organizations enable-policy-type \
  --root-id r-abc1 \
  --policy-type BACKUP_POLICY
```

## 아키텍처/동작 원리

### Organizations 계층 구조와 SCP 상속

SCP는 상위에서 하위로 상속되며, 각 수준의 SCP가 교차(intersection)되어 적용됩니다.

```
Root (FullAWSAccess)
│
├── SCP: DenyRegionRestriction (리전 제한)
│
├── Security OU
│   ├── SCP: FullAWSAccess
│   ├── Log Archive Account
│   └── Audit Account
│
├── Workloads OU
│   ├── SCP: DenyExpensiveServices (고비용 서비스 제한)
│   │
│   ├── Production OU
│   │   ├── SCP: DenyDeleteProtection (삭제 보호)
│   │   ├── App-A Prod Account
│   │   │   └── 실제 권한 = IAM 정책
│   │   │       교집합 Root SCP
│   │   │       교집합 Workloads SCP
│   │   │       교집합 Production SCP
│   │   └── App-B Prod Account
│   │
│   └── Non-Production OU
│       ├── SCP: AllowAllServices
│       ├── Dev Account
│       └── Staging Account
│
└── Sandbox OU
    ├── SCP: DenyProductionResources
    └── Sandbox Accounts
```

### SCP 평가 로직

SCP 평가는 다음 순서로 이루어집니다.

1. Root에 연결된 SCP를 확인합니다.
2. 부모 OU에 연결된 SCP를 확인합니다.
3. 현재 OU/계정에 연결된 SCP를 확인합니다.
4. 모든 수준의 SCP에서 허용된 작업만 실행 가능합니다.
5. 어느 한 수준에서라도 Deny되면 해당 작업은 차단됩니다.

### 기능 세트 (Feature Sets)

Organizations는 두 가지 기능 세트를 제공합니다.

- **ALL**: SCP, 태그 정책, 백업 정책 등 모든 기능을 사용할 수 있습니다.
- **Consolidated Billing Only**: 통합 결제 기능만 사용합니다. SCP 등의 고급 기능은 사용할 수 없습니다.

## 실전 활용

### 실전 SCP 패턴

**패턴 1: CloudTrail 비활성화 방지**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyCloudTrailDisable",
      "Effect": "Deny",
      "Action": [
        "cloudtrail:StopLogging",
        "cloudtrail:DeleteTrail",
        "cloudtrail:UpdateTrail"
      ],
      "Resource": "*"
    }
  ]
}
```

**패턴 2: S3 퍼블릭 액세스 차단 강제**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyS3PublicAccess",
      "Effect": "Deny",
      "Action": [
        "s3:PutBucketPublicAccessBlock",
        "s3:PutAccountPublicAccessBlock"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "s3:PublicAccessBlockConfiguration/BlockPublicAcls": "true",
          "s3:PublicAccessBlockConfiguration/BlockPublicPolicy": "true"
        }
      }
    }
  ]
}
```

**패턴 3: 루트 사용자 활동 제한**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyRootUserActions",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:root"
        }
      }
    }
  ]
}
```

```bash
# 위 SCP들을 일괄 생성하는 예시
for policy_file in deny-cloudtrail-disable.json deny-s3-public.json deny-root-user.json; do
  policy_name=$(basename "$policy_file" .json)
  aws organizations create-policy \
    --name "$policy_name" \
    --description "Security guardrail: $policy_name" \
    --type SERVICE_CONTROL_POLICY \
    --content "file://$policy_file"
done
```

### 새 멤버 계정 초대 및 생성

```bash
# 기존 AWS 계정을 조직에 초대
aws organizations invite-account-to-organization \
  --target '{"Id":"987654321098","Type":"ACCOUNT"}' \
  --notes "Please join our organization for centralized management"

# 초대 목록 확인
aws organizations list-handshakes-for-organization \
  --filter '{"ActionType":"INVITE"}' \
  --query 'Handshakes[*].{Id:Id,State:State,AccountId:Parties[?Type==`ACCOUNT`].Id}' \
  --output table

# 조직 내에서 새 계정 직접 생성
aws organizations create-account \
  --email "new-team@example.com" \
  --account-name "New Team Account" \
  --role-name "OrganizationAccountAccessRole" \
  --iam-user-access-to-billing ALLOW

# 계정 생성 상태 확인
aws organizations describe-create-account-status \
  --create-account-request-id "car-abc123" \
  --output json
```

### 크로스 계정 접근 설정

```bash
# 관리 계정에서 멤버 계정으로 역할 전환
aws sts assume-role \
  --role-arn "arn:aws:iam::123456789012:role/OrganizationAccountAccessRole" \
  --role-session-name "admin-session" \
  --output json

# 임시 자격 증명으로 멤버 계정 리소스 접근
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_SESSION_TOKEN="FwoGZXIvYXdzEHYaD..."

aws sts get-caller-identity
```

### Organizations 서비스 통합

Organizations는 다양한 AWS 서비스와 통합됩니다.

```bash
# 통합된 서비스 목록 확인
aws organizations list-aws-service-access-for-organization \
  --query 'EnabledServicePrincipals[*].{Service:ServicePrincipal,Date:DateEnabled}' \
  --output table

# AWS Config 통합 활성화
aws organizations enable-aws-service-access \
  --service-principal config.amazonaws.com

# CloudFormation StackSets 통합 활성화
aws organizations enable-aws-service-access \
  --service-principal member.org.stacksets.cloudformation.amazonaws.com

# RAM (Resource Access Manager) 통합 활성화
aws organizations enable-aws-service-access \
  --service-principal ram.amazonaws.com
```

## 모범 사례/보안

### OU 설계 모범 사례

1. **워크로드 특성과 거버넌스 요구사항에 따라 OU를 설계하십시오.** 팀이 아닌 환경과 보안 요구사항 기준으로 OU를 구성하는 것이 효과적입니다.

2. **Sandbox OU를 반드시 생성하십시오.** 개발자가 자유롭게 실험할 수 있는 격리된 환경을 제공하면, 프로덕션 환경에서의 위험한 실험을 방지할 수 있습니다.

3. **Suspended OU를 준비하십시오.** 더 이상 사용하지 않는 계정을 이동시킬 OU입니다. 모든 서비스를 Deny하는 SCP를 적용합니다.

4. **OU 깊이를 3단계 이내로 유지하십시오.** OU가 너무 깊으면 SCP 상속이 복잡해지고 관리가 어려워집니다.

### SCP 설계 모범 사례

1. **Deny 기반으로 SCP를 설계하십시오.** Allow 기반은 관리가 복잡해질 수 있습니다. 기본 FullAWSAccess를 유지하고, 금지할 항목만 Deny로 추가하는 것이 효과적입니다.

2. **SCP를 테스트 환경에서 먼저 검증하십시오.** 잘못된 SCP는 전체 OU의 서비스를 중단시킬 수 있습니다.

3. **SCP의 영향을 사전에 시뮬레이션하십시오.** IAM Policy Simulator를 사용하여 SCP 적용 전 영향도를 확인합니다.

### 보안 모범 사례

- 관리 계정에서 워크로드를 실행하지 마십시오. 관리 계정은 SCP의 영향을 받지 않으므로, 보안 위험이 높습니다.
- 관리 계정의 루트 사용자에 MFA를 반드시 활성화하십시오.
- 위임 관리자를 적극 활용하여 관리 계정에 대한 직접 접근을 최소화하십시오.
- CloudTrail Organization Trail을 활성화하여 모든 계정의 API 호출을 기록하십시오.
- 정기적으로 SCP를 검토하고 불필요한 정책을 정리하십시오.

```bash
# Organization Trail 생성
aws cloudtrail create-trail \
  --name "organization-trail" \
  --s3-bucket-name "org-cloudtrail-logs" \
  --is-organization-trail \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --region us-east-1

aws cloudtrail start-logging \
  --name "organization-trail" \
  --region us-east-1
```

## 관련 서비스 비교

### Organizations vs Control Tower

| 항목 | Organizations | Control Tower |
|------|--------------|---------------|
| 역할 | 기반 인프라 | 자동화 계층 |
| 설정 방식 | 수동 (API/CLI/콘솔) | 자동 (Landing Zone) |
| SCP 관리 | 직접 작성 및 관리 | 사전 정의된 가드레일 제공 |
| 계정 생성 | API/CLI/콘솔 | Account Factory |
| 학습 곡선 | 중간 | 낮음 |
| 유연성 | 높음 | 프레임워크 내 제한 |
| 비용 | 무료 | 무료 (사용 서비스 비용만) |

Control Tower는 Organizations 위에 구축된 서비스입니다. Organizations를 직접 사용하면 더 유연한 구성이 가능하지만, Control Tower를 사용하면 모범 사례에 기반한 환경을 빠르게 구축할 수 있습니다.

### Organizations와 통합되는 주요 AWS 서비스

| 서비스 | 통합 목적 |
|--------|----------|
| AWS SSO (IAM Identity Center) | 중앙 집중식 SSO 관리 |
| AWS Config | 조직 전체 규정 준수 모니터링 |
| AWS CloudTrail | 조직 전체 API 감사 |
| AWS Security Hub | 조직 전체 보안 상태 관리 |
| Amazon GuardDuty | 조직 전체 위협 탐지 |
| AWS Backup | 조직 전체 백업 정책 |
| AWS RAM | 조직 내 리소스 공유 |
| CloudFormation StackSets | 조직 전체 리소스 배포 |

## 요약

AWS Organizations는 멀티 계정 AWS 환경의 기반이 되는 핵심 서비스입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **조직 구조**: Root, OU, Account의 계층 구조로 멀티 계정 환경을 구성합니다.
- **SCP (Service Control Policy)**: 조직 전체에 보안 가드레일을 적용하는 가장 강력한 도구입니다.
- **통합 결제**: 모든 계정의 비용을 통합 관리하고, 볼륨 할인과 RI/SP 공유 혜택을 받을 수 있습니다.
- **위임 관리자**: 관리 계정의 직접 사용을 최소화하고, 서비스별 관리를 멤버 계정에 위임합니다.
- **다양한 정책**: SCP, Tag Policy, Backup Policy, AI Opt-out Policy 등 다양한 정책을 중앙에서 관리합니다.
- **서비스 통합**: 30개 이상의 AWS 서비스와 통합되어 조직 전체의 보안, 규정 준수, 운영을 중앙에서 관리합니다.

Organizations는 AWS 멀티 계정 전략의 근간이며, Control Tower, Security Hub, GuardDuty 등 대부분의 관리 서비스가 Organizations를 기반으로 동작합니다. 조직의 규모와 관계없이 멀티 계정 전략을 수립하고 Organizations를 활용하는 것이 AWS 운영의 모범 사례입니다.