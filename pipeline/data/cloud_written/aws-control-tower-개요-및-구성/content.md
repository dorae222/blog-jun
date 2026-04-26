<!-- infographic-hero -->
![AWS Control Tower 개요 및 구성 핵심 요약](figures/infographic.svg)

*Figure: AWS Control Tower 개요 및 구성 한 장 요약 인포그래픽*

## 개요

AWS Control Tower는 AWS 멀티 계정 환경을 자동으로 설정하고 거버넌스를 적용할 수 있도록 지원하는 관리형 서비스입니다. 기업이 AWS를 도입할 때 가장 먼저 직면하는 과제 중 하나가 바로 멀티 계정 전략 수립과 보안 거버넌스 적용입니다. AWS Control Tower는 이러한 복잡한 초기 설정 과정을 자동화하고, 지속적인 거버넌스 준수를 보장합니다.

AWS Control Tower는 내부적으로 AWS Organizations, AWS Service Catalog, AWS IAM Identity Center(구 AWS SSO), AWS Config, AWS CloudTrail 등 여러 AWS 서비스를 조합하여 하나의 통합된 Landing Zone을 구성합니다. 사용자는 Control Tower 콘솔에서 몇 번의 클릭만으로 모범 사례에 기반한 멀티 계정 환경을 구축할 수 있습니다.

### Control Tower를 사용해야 하는 이유

멀티 계정 환경을 수동으로 구성하려면 수많은 서비스 설정이 필요합니다. Organizations OU 구성, 각 계정별 CloudTrail 활성화, Config 규칙 배포, IAM 정책 작성, SSO 설정 등을 개별적으로 수행해야 합니다. Control Tower는 이 모든 과정을 자동화하고, 표준화된 환경을 제공합니다.

주요 도입 시나리오는 다음과 같습니다.

- 신규 AWS 환경을 처음부터 모범 사례에 맞게 구축하려는 경우
- 기존 멀티 계정 환경에 거버넌스를 체계적으로 적용하려는 경우
- 규정 준수(Compliance) 요구사항을 자동으로 충족해야 하는 경우
- 중앙 집중식 로깅 및 감사 체계를 구축하려는 경우

## 핵심 기능

### 1. Landing Zone

Landing Zone은 Control Tower가 구성하는 멀티 계정 환경의 기반 인프라입니다. Landing Zone 설정 시 자동으로 생성되는 요소들은 다음과 같습니다.

**관리 계정 (Management Account)**
- Control Tower의 관리 주체가 되는 루트 계정입니다.
- Organizations의 관리 계정 역할을 수행합니다.
- 빌링 통합 및 전체 정책 관리를 담당합니다.

**로그 아카이브 계정 (Log Archive Account)**
- 모든 계정의 AWS CloudTrail 로그와 AWS Config 로그를 중앙 집중 저장합니다.
- S3 버킷에 로그가 자동으로 수집되며, 보안 팀만 접근할 수 있도록 제한됩니다.

**감사 계정 (Audit Account)**
- 보안 및 규정 준수 감사를 위한 전용 계정입니다.
- 크로스 계정 접근 역할이 자동으로 구성됩니다.
- AWS Config Aggregator가 설정되어 전체 계정의 규정 준수 상태를 한눈에 파악할 수 있습니다.

**OU (Organizational Unit) 구조**
- Security OU: 로그 아카이브 및 감사 계정이 위치합니다.
- Sandbox OU: 개발 및 테스트용 계정을 위한 기본 OU입니다.
- 추가 Custom OU를 필요에 따라 생성할 수 있습니다.

Landing Zone의 현재 버전을 확인하려면 다음 AWS CLI 명령을 사용합니다.

```bash
# Landing Zone 정보 조회
aws controltower list-landing-zones --region us-east-1

# 특정 Landing Zone의 상세 정보 확인
aws controltower get-landing-zone \
  --landing-zone-identifier "arn:aws:controltower:us-east-1:123456789012:landingzone/ABCDEFGHIJKL0123" \
  --region us-east-1
```

### 2. 가드레일 (Controls / Guardrails)

가드레일은 Control Tower 환경 내에서 보안 및 운영 정책을 강제하거나 탐지하는 규칙입니다. Control Tower 3.0부터는 공식 명칭이 "Controls"로 변경되었지만, 가드레일이라는 용어도 여전히 널리 사용됩니다.

**가드레일의 종류**

| 유형 | 설명 | 구현 방식 |
|------|------|----------|
| 예방적 (Preventive) | 특정 작업을 사전에 차단합니다 | SCP (Service Control Policy) |
| 탐지적 (Detective) | 규정 위반을 탐지하여 알립니다 | AWS Config Rules |
| 사전 예방적 (Proactive) | CloudFormation 배포 전 규정 준수를 확인합니다 | CloudFormation Hooks |

**가드레일 적용 수준**

- 필수 (Mandatory): Landing Zone 설정 시 자동으로 활성화되며 비활성화할 수 없습니다.
- 강력 권장 (Strongly Recommended): AWS 모범 사례에 기반하며, 활성화가 권장됩니다.
- 선택적 (Elective): 특정 요구사항에 따라 선택적으로 활성화합니다.

가드레일을 OU에 활성화하는 CLI 명령은 다음과 같습니다.

```bash
# 활성화된 가드레일(Controls) 목록 조회
aws controltower list-enabled-controls \
  --target-identifier "arn:aws:organizations::123456789012:ou/o-abc123/ou-def456" \
  --region us-east-1

# 특정 가드레일 활성화
aws controltower enable-control \
  --control-identifier "arn:aws:controltower:us-east-1::control/AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS" \
  --target-identifier "arn:aws:organizations::123456789012:ou/o-abc123/ou-def456" \
  --region us-east-1

# 가드레일 비활성화
aws controltower disable-control \
  --control-identifier "arn:aws:controltower:us-east-1::control/AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS" \
  --target-identifier "arn:aws:organizations::123456789012:ou/o-abc123/ou-def456" \
  --region us-east-1
```

### 3. 대시보드

Control Tower 대시보드는 전체 멀티 계정 환경의 거버넌스 상태를 한눈에 파악할 수 있는 중앙 관제 화면입니다.

대시보드에서 확인할 수 있는 정보는 다음과 같습니다.

- OU별 계정 수 및 상태
- 가드레일 준수 현황 (준수/위반/알 수 없음)
- 계정 프로비저닝 상태
- 드리프트 발생 여부

## 아키텍처/동작 원리

### Landing Zone 내부 아키텍처

Control Tower Landing Zone이 설정되면 내부적으로 다음과 같은 아키텍처가 구성됩니다.

```
Management Account (Control Tower 관리)
├── AWS Organizations (조직 구조 관리)
│   ├── Security OU
│   │   ├── Log Archive Account
│   │   │   ├── S3 Bucket (CloudTrail Logs)
│   │   │   ├── S3 Bucket (Config Logs)
│   │   │   └── S3 Bucket (Access Logs)
│   │   └── Audit Account
│   │       ├── AWS Config Aggregator
│   │       ├── SNS Topics (알림)
│   │       └── Cross-Account IAM Roles
│   └── Sandbox OU (또는 Custom OUs)
│       ├── Workload Account 1
│       ├── Workload Account 2
│       └── ...
├── AWS IAM Identity Center (SSO 관리)
├── AWS CloudTrail (Organization Trail)
├── AWS Config (Organization-wide Rules)
└── AWS Service Catalog (Account Factory)
```

### 가드레일 동작 메커니즘

**예방적 가드레일의 동작 원리**

예방적 가드레일은 AWS Organizations의 SCP(Service Control Policy)를 활용합니다. SCP는 OU 또는 계정 수준에서 적용되며, 허용되지 않은 API 호출을 원천적으로 차단합니다.

예를 들어, "루트 사용자 액세스 키 생성 금지" 가드레일은 다음과 같은 SCP로 구현됩니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "GRRESTRICTROOTUSERACCESSKEYS",
      "Effect": "Deny",
      "Action": "iam:CreateAccessKey",
      "Resource": [
        "arn:aws:iam::*:root"
      ],
      "Condition": {
        "StringLike": {
          "aws:PrincipalArn": [
            "arn:aws:iam::*:root"
          ]
        }
      }
    }
  ]
}
```

**탐지적 가드레일의 동작 원리**

탐지적 가드레일은 AWS Config Rules를 사용합니다. Config는 리소스의 구성 변경을 지속적으로 모니터링하고, 규칙에 위반되는 변경이 감지되면 비준수(Non-Compliant) 상태로 표시합니다.

**사전 예방적 가드레일의 동작 원리**

사전 예방적 가드레일은 AWS CloudFormation Hooks를 활용합니다. CloudFormation 스택이 생성되거나 업데이트될 때, 리소스가 실제로 프로비저닝되기 전에 규정 준수 여부를 검증합니다. 위반이 감지되면 배포 자체가 실패합니다.

### 드리프트 감지 및 복구

드리프트(Drift)는 Control Tower가 관리하는 환경이 원래 설정에서 벗어난 상태를 의미합니다. 다음과 같은 경우 드리프트가 발생할 수 있습니다.

- Control Tower 외부에서 OU 구조를 직접 변경한 경우
- SCP를 직접 수정하거나 삭제한 경우
- 필수 계정(Log Archive, Audit)을 이동하거나 삭제한 경우
- IAM Identity Center 설정을 직접 변경한 경우

드리프트 상태를 확인하고 복구하는 방법은 다음과 같습니다.

```bash
# Landing Zone 드리프트 상태 확인
aws controltower get-landing-zone \
  --landing-zone-identifier "arn:aws:controltower:us-east-1:123456789012:landingzone/ABCDEFGHIJKL0123" \
  --query 'landingZone.driftStatus' \
  --region us-east-1

# Landing Zone 리셋 (드리프트 복구)
aws controltower reset-landing-zone \
  --landing-zone-identifier "arn:aws:controltower:us-east-1:123456789012:landingzone/ABCDEFGHIJKL0123" \
  --region us-east-1
```

## 실전 활용

### Landing Zone 초기 설정

Control Tower Landing Zone을 설정하기 전에 다음 사전 조건을 확인해야 합니다.

1. 관리 계정에 AWS Organizations가 아직 설정되지 않았거나, 기존 Organizations를 사용할 준비가 되어 있어야 합니다.
2. 관리 계정에 관리자 권한이 있어야 합니다.
3. Landing Zone 설정에 사용할 리전을 결정해야 합니다(홈 리전 및 거버넌스 리전).

```bash
# Control Tower 지원 리전 확인
aws controltower list-landing-zones --region us-east-1

# Landing Zone 생성 (CLI로 직접 생성 가능)
aws controltower create-landing-zone \
  --manifest file://landing-zone-manifest.json \
  --version "3.3" \
  --region us-east-1
```

Landing Zone 매니페스트 파일 예시는 다음과 같습니다.

```json
{
  "governedRegions": ["us-east-1", "ap-northeast-2"],
  "organizationStructure": {
    "security": {
      "name": "Security"
    },
    "sandbox": {
      "name": "Sandbox"
    }
  },
  "centralizedLogging": {
    "accountId": "111122223333",
    "configurations": {
      "loggingBucket": {
        "retentionDays": 365
      },
      "accessLoggingBucket": {
        "retentionDays": 365
      }
    },
    "enabled": true
  },
  "securityRoles": {
    "accountId": "444455556666"
  },
  "accessManagement": {
    "enabled": true
  }
}
```

### OU 구성 전략

AWS에서 권장하는 OU 구성 전략은 워크로드의 특성과 거버넌스 요구사항에 따라 OU를 분리하는 것입니다.

```
Root
├── Security OU (보안 계정)
│   ├── Log Archive
│   └── Audit
├── Infrastructure OU (공유 인프라)
│   ├── Network Account (Transit Gateway, VPN)
│   └── Shared Services Account (AD, DNS)
├── Workloads OU (업무 환경)
│   ├── Production OU
│   │   ├── App-A Prod Account
│   │   └── App-B Prod Account
│   └── Non-Production OU
│       ├── App-A Dev Account
│       └── App-B Staging Account
├── Sandbox OU (실험 환경)
│   └── Developer Sandbox Accounts
└── Suspended OU (비활성 계정)
    └── Decommissioned Accounts
```

OU를 생성하고 Control Tower에 등록하는 CLI 명령은 다음과 같습니다.

```bash
# Organizations에서 OU 생성
aws organizations create-organizational-unit \
  --parent-id r-abc1 \
  --name "Workloads"

# Control Tower에 OU 등록 (Baseline 적용)
aws controltower enable-baseline \
  --baseline-identifier "arn:aws:controltower:us-east-1::baseline/AWSControlTowerBaseline" \
  --baseline-version "4.0" \
  --target-identifier "arn:aws:organizations::123456789012:ou/o-abc123/ou-workloads789" \
  --parameters '[{"key":"NotificationForwarderConfiguration","value":"{\"configuration\":{\"email\":\"admin@example.com\"}}"}]' \
  --region us-east-1
```

### Terraform을 활용한 Control Tower 관리

Control Tower 환경을 코드로 관리하려면 Terraform의 AWS Control Tower 프로바이더를 활용할 수 있습니다.

```python
# Terraform 구성 예시 (HCL이지만 python 태그로 구문 강조)
# main.tf
resource "aws_controltower_control" "restrict_root_access_keys" {
  control_identifier = "arn:aws:controltower:us-east-1::control/AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS"
  target_identifier  = aws_organizations_organizational_unit.workloads.arn
}

resource "aws_controltower_landing_zone" "example" {
  manifest_json = file("${path.module}/landing-zone-manifest.json")
  version       = "3.3"
}
```

### 기존 AWS 환경에 Control Tower 적용하기

이미 AWS Organizations를 사용하고 있는 기존 환경에 Control Tower를 적용하는 것도 가능합니다. 다만 다음 사항에 주의해야 합니다.

1. 기존 OU와 계정은 Control Tower에 등록(enroll)해야 가드레일이 적용됩니다.
2. 등록 과정에서 기존 Config 규칙과 충돌이 발생할 수 있으므로 사전 검토가 필요합니다.
3. 기존 CloudTrail 설정이 Control Tower의 Organization Trail과 중복될 수 있습니다.

```bash
# 기존 계정을 Control Tower에 등록
aws controltower enable-baseline \
  --baseline-identifier "arn:aws:controltower:us-east-1::baseline/AWSControlTowerBaseline" \
  --baseline-version "4.0" \
  --target-identifier "arn:aws:organizations::123456789012:ou/o-abc123/ou-existing456" \
  --parameters '[]' \
  --region us-east-1

# 등록 상태 확인
aws controltower list-enabled-baselines --region us-east-1
```

## 모범 사례/보안

### Landing Zone 설계 모범 사례

1. **리전 선택을 신중하게 결정하십시오.** 홈 리전은 변경할 수 없으므로, 주요 워크로드가 운영될 리전을 홈 리전으로 설정해야 합니다. 거버넌스 리전은 규정 준수가 필요한 모든 리전을 포함해야 합니다.

2. **OU 구조를 사전에 설계하십시오.** OU 구조는 나중에 변경하기 어려우므로, 워크로드 분류 체계, 환경 분리 전략, 보안 요구사항을 고려하여 사전에 설계해야 합니다.

3. **로그 보관 정책을 수립하십시오.** 규정 준수 요구사항에 따라 CloudTrail 및 Config 로그의 보관 기간을 설정해야 합니다. 기본값은 1년이지만, 금융 등 규제 산업에서는 더 긴 보관 기간이 필요할 수 있습니다.

### 가드레일 적용 모범 사례

1. **단계적으로 가드레일을 활성화하십시오.** 모든 가드레일을 한꺼번에 활성화하면 기존 워크로드에 영향을 줄 수 있습니다. Sandbox OU에서 먼저 테스트한 후 점진적으로 확대하는 것이 안전합니다.

2. **예방적 가드레일을 우선 적용하십시오.** 보안상 중요한 규칙은 탐지보다 예방이 효과적입니다. 루트 사용자 제한, 로깅 비활성화 방지 등 핵심 보안 가드레일을 먼저 활성화하십시오.

3. **사용자 정의 가드레일을 활용하십시오.** 조직 고유의 보안 정책이 있다면, 사용자 정의 SCP나 Config Rules를 추가로 구성할 수 있습니다.

### 보안 권장 사항

- 관리 계정에서는 워크로드를 실행하지 마십시오. 관리 계정은 거버넌스 관리 전용으로 사용해야 합니다.
- 로그 아카이브 계정에 대한 접근을 최소한으로 제한하십시오. 보안 팀만 접근할 수 있도록 설정해야 합니다.
- IAM Identity Center를 통해 SSO를 구성하고, 각 계정에 대한 직접적인 IAM 사용자 생성을 최소화하십시오.
- CloudTrail Organization Trail의 로그 파일 무결성 검증을 활성화하십시오.
- 감사 계정에서 정기적으로 규정 준수 보고서를 생성하고 검토하십시오.

```bash
# CloudTrail 로그 파일 무결성 검증 활성화 확인
aws cloudtrail describe-trails \
  --query 'trailList[*].{Name:Name,LogFileValidation:LogFileValidationEnabled}' \
  --output table

# Config 규칙 준수 상태 확인 (감사 계정에서)
aws configservice describe-compliance-by-config-rule \
  --query 'ComplianceByConfigRules[?Compliance.ComplianceType==`NON_COMPLIANT`]' \
  --output json
```

## 관련 서비스 비교

### Control Tower vs Organizations 직접 구성

| 항목 | Control Tower | Organizations 직접 구성 |
|------|--------------|------------------------|
| 설정 난이도 | 낮음 (자동화) | 높음 (수동 구성) |
| Landing Zone | 자동 구성 | 직접 설계 필요 |
| 가드레일 | 사전 정의된 규칙 제공 | SCP/Config 직접 작성 |
| 계정 프로비저닝 | Account Factory | 수동 또는 자체 자동화 |
| 드리프트 감지 | 내장 | 직접 구현 필요 |
| 유연성 | 제한적 (프레임워크 내) | 높음 (자유 구성) |
| 비용 | 무료 (사용 서비스 비용만) | 무료 (사용 서비스 비용만) |

### Control Tower vs AWS Landing Zone Solution (구버전)

AWS Landing Zone Solution은 Control Tower 출시 이전에 사용되던 솔루션으로, 현재는 Control Tower로 마이그레이션이 권장됩니다. Control Tower는 Landing Zone Solution의 기능을 관리형 서비스로 제공하며, 지속적인 업데이트와 신규 기능이 추가되고 있습니다.

### Control Tower와 함께 사용하면 좋은 서비스

- **AWS Security Hub**: 전체 계정의 보안 상태를 통합 관리합니다.
- **Amazon GuardDuty**: 위협 탐지를 조직 전체에 활성화합니다.
- **AWS Backup**: 조직 전체의 백업 정책을 중앙에서 관리합니다.
- **AWS Firewall Manager**: 방화벽 규칙을 조직 전체에 배포합니다.

## 요약

AWS Control Tower는 멀티 계정 AWS 환경의 설정과 거버넌스를 자동화하는 핵심 관리 서비스입니다. Landing Zone을 통해 모범 사례에 기반한 계정 구조를 자동으로 구성하고, 가드레일을 통해 지속적인 규정 준수를 보장합니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **Landing Zone**: Organizations, CloudTrail, Config, IAM Identity Center를 자동 구성하여 안전한 멀티 계정 환경을 제공합니다.
- **가드레일 (Controls)**: 예방적(SCP), 탐지적(Config Rules), 사전 예방적(CloudFormation Hooks) 세 가지 유형으로 거버넌스를 적용합니다.
- **드리프트 관리**: 환경 변경을 감지하고 원래 상태로 복구할 수 있습니다.
- **Account Factory**: Service Catalog 기반의 계정 자동 프로비저닝을 지원합니다.
- **확장성**: Customizations for Control Tower(CfCT)나 Terraform을 통해 추가 커스터마이징이 가능합니다.

Control Tower는 AWS 멀티 계정 전략의 시작점이자 지속적인 거버넌스 관리의 중심입니다. 특히 규모가 커지는 조직에서는 Control Tower를 도입하여 일관된 보안 정책과 운영 기준을 유지하는 것이 중요합니다.