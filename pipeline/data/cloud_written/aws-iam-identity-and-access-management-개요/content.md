<!-- infographic-hero -->
![AWS IAM 핵심 요약](figures/infographic.svg)

*Figure: AWS IAM 한 장 요약 인포그래픽*

# AWS IAM (Identity and Access Management) 개요

## 개요

AWS IAM(Identity and Access Management)은 AWS 리소스에 대한 자격 증명(Identity)과 접근 제어(Access Control)를 통합 관리하는 서비스입니다. 2011년 정식 출시(GA)된 이래 AWS의 모든 보안 모델의 근간으로 자리잡았으며, 콘솔/CLI/SDK/API를 통한 모든 요청은 IAM의 권한 평가 엔진을 거쳐 허용 또는 거부됩니다.

IAM 자체는 무료 서비스이지만, AWS 보안의 출발점이자 종착점이라는 점에서 가장 중요한 서비스 중 하나입니다. IAM 설계가 잘못되면 단 하나의 노출된 액세스 키로 전체 계정이 탈취될 수 있는 반면, 잘 설계된 IAM은 최소 권한 원칙(Principle of Least Privilege)을 코드 수준에서 강제할 수 있는 강력한 도구가 됩니다.

IAM의 주요 책임은 다음과 같습니다.

- **인증(Authentication)**: 누가(Who) 요청을 보냈는지 확인합니다.
- **인가(Authorization)**: 그 요청자가 무엇을(What) 할 수 있는지 결정합니다.
- **감사(Audit)**: 누가, 언제, 무엇을 했는지 CloudTrail과 연계하여 추적합니다.

IAM은 글로벌 서비스로, 리전 개념이 없습니다. 한 번 생성한 사용자, 역할, 정책은 모든 리전에서 동일하게 적용됩니다.

---

## 핵심 기능

### 1. 4가지 핵심 구성 요소

IAM은 네 가지 주요 엔티티로 구성됩니다.

| 구성 요소 | 설명 | 사용 예시 |
|----------|------|----------|
| User | 사람 또는 애플리케이션을 위한 영구 자격 증명 | 개발자, CI/CD 파이프라인 |
| Group | User들의 논리적 묶음. 정책을 일괄 부여 | DevOps Group, Auditor Group |
| Role | 임시 자격 증명을 부여하는 엔티티 | EC2 Instance Profile, Lambda 실행 역할 |
| Policy | 권한을 JSON 문서로 정의 | AdministratorAccess, ReadOnlyAccess |

```bash
# IAM User 생성
aws iam create-user --user-name developer-jun

# Group 생성 및 정책 연결
aws iam create-group --group-name DevOpsTeam
aws iam attach-group-policy \
  --group-name DevOpsTeam \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# User를 Group에 추가
aws iam add-user-to-group \
  --user-name developer-jun \
  --group-name DevOpsTeam
```

### 2. Policy의 6가지 유형

IAM Policy는 적용 대상과 평가 방식에 따라 6가지로 나뉩니다.

- **Identity-based Policy**: User, Group, Role에 부착되는 정책. 가장 일반적입니다.
- **Resource-based Policy**: S3 Bucket Policy, KMS Key Policy처럼 리소스에 직접 부착되는 정책. Principal 필드가 필수입니다.
- **Permissions Boundary**: User나 Role이 가질 수 있는 최대 권한의 한계를 정의. 위임된 권한 부여 시 안전장치 역할을 합니다.
- **SCP(Service Control Policy)**: AWS Organizations에서 OU(Organizational Unit) 또는 계정 단위로 적용되는 가드레일 정책.
- **Session Policy**: AssumeRole 시 인라인으로 전달되는 임시 정책. 세션 중에만 유효합니다.
- **ACL(Access Control List)**: 레거시 방식. S3와 같은 일부 서비스에서만 사용됩니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3ReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:PrincipalOrgID": "o-abc123def4"
        }
      }
    }
  ]
}
```

### 3. IAM Role과 STS

Role은 IAM의 가장 강력한 기능입니다. 영구 자격 증명을 보관하지 않고 STS(Security Token Service)를 통해 임시 자격 증명을 발급받아 사용합니다.

Role은 두 가지 정책으로 구성됩니다.

- **Trust Policy**: 누가 이 Role을 가정(Assume)할 수 있는지 정의. Principal 필드가 핵심입니다.
- **Permissions Policy**: 이 Role이 가정되었을 때 어떤 권한을 가지는지 정의.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

```bash
# Role 생성 및 AssumeRole
aws iam create-role \
  --role-name EC2-S3-Read-Role \
  --assume-role-policy-document file://trust-policy.json

aws sts assume-role \
  --role-arn arn:aws:iam::123456789012:role/EC2-S3-Read-Role \
  --role-session-name dev-session-001
```

STS가 발급하는 임시 자격 증명은 AccessKeyId, SecretAccessKey, SessionToken 세 가지로 구성되며, 기본 1시간(최대 12시간)의 만료 시간을 가집니다.

### 4. IAM Identity Center (구 AWS SSO)

IAM Identity Center는 AWS Organizations 환경에서 다계정에 걸친 사용자 관리를 단순화하는 서비스입니다. 2022년 AWS SSO에서 이름이 변경되었습니다.

- **SAML 2.0 / OIDC 연동**: Okta, Azure AD, Google Workspace 등 외부 IdP와 통합 가능합니다.
- **Permission Set**: 권한 집합을 정의하여 여러 계정에 일관되게 배포합니다.
- **AWS Access Portal**: 단일 로그인 포털로 여러 계정/역할을 선택할 수 있습니다.
- **무료**: 별도 비용 없이 사용 가능합니다.

```bash
# Identity Center 인스턴스 조회
aws sso-admin list-instances

# Permission Set 생성
aws sso-admin create-permission-set \
  --instance-arn arn:aws:sso:::instance/ssoins-1234567890abcdef \
  --name DeveloperAccess \
  --session-duration PT8H
```

### 5. IAM Access Analyzer

Access Analyzer는 외부 엔티티가 접근 가능한 리소스를 자동으로 분석하여 의도하지 않은 접근을 탐지합니다. 2019년 출시되었습니다.

- **External Access Analyzer**: S3, IAM Role, KMS Key, Lambda 등에서 외부 계정/조직의 접근을 탐지합니다.
- **Unused Access Analyzer**: 90일 이상 사용되지 않은 권한, Role, 액세스 키를 식별합니다.
- **IAM Policy Generator**: CloudTrail 로그를 분석하여 실제 사용된 권한 기반으로 최소 권한 정책을 자동 생성합니다.
- **Policy Validation**: IAM 정책 작성 시 100가지 이상의 검사로 보안 모범 사례 위반을 사전에 탐지합니다.

```bash
# Access Analyzer 활성화
aws accessanalyzer create-analyzer \
  --analyzer-name org-analyzer \
  --type ORGANIZATION

# 발견된 위험 조회
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:ap-northeast-2:123456789012:analyzer/org-analyzer
```

### 6. IAM Roles Anywhere

IAM Roles Anywhere는 온프레미스 서버, 컨테이너, 외부 클라우드 워크로드에서 X.509 인증서를 사용해 IAM Role의 임시 자격 증명을 획득할 수 있게 합니다. 2022년 출시되었습니다.

- 장기 액세스 키를 온프레미스에 저장할 필요가 없습니다.
- PKI 기반의 인증서로 신뢰 체계를 구축합니다.
- AWS Private CA(구 ACM PCA) 또는 외부 CA를 사용할 수 있습니다.

```bash
# Trust Anchor 생성 (CA 등록)
aws rolesanywhere create-trust-anchor \
  --name my-onprem-ca \
  --source sourceType=CERTIFICATE_BUNDLE,sourceData={x509CertificateData=...}
```

---

## 아키텍처

### IAM Policy 평가 로직

IAM은 다음 순서로 정책을 평가합니다. 이 흐름을 정확히 이해하는 것이 IAM 설계의 핵심입니다.

```
[Request 도착]
    |
    v
[1. 인증(Authentication) - Principal 확인]
    |
    v
[2. 모든 적용 가능한 정책 수집]
    - SCP, Permissions Boundary, Identity Policy, Resource Policy, Session Policy
    |
    v
[3. Explicit Deny 평가]
    - 하나라도 Deny가 있으면 즉시 거부
    |
    v
[4. SCP 평가 (Organization 환경)]
    - SCP에서 허용되지 않으면 거부
    |
    v
[5. Resource-based Policy 평가]
    - 명시적 Allow가 있으면 허용
    |
    v
[6. Identity-based Policy + Permissions Boundary 평가]
    - 양쪽 모두에서 Allow되어야 허용
    |
    v
[7. Session Policy 평가 (있는 경우)]
    - 세션 정책에서도 Allow되어야 허용
    |
    v
[Default Deny - 어떤 정책도 명시적 허용이 없으면 거부]
```

핵심 규칙은 다음과 같습니다.

1. **Explicit Deny가 항상 우선**: 어떤 정책에서든 Deny가 있으면 다른 모든 Allow를 무시합니다.
2. **Default Deny**: 명시적 Allow가 없으면 거부됩니다.
3. **Permissions Boundary는 상한선**: User/Role의 실제 권한은 Identity Policy와 Boundary의 교집합입니다.

### Federation 흐름

외부 IdP를 통한 인증 흐름을 SAML 2.0 기반으로 표현하면 다음과 같습니다.

```
[User] -> [Corporate IdP (Okta)]
                    |
                    | SAML Assertion
                    v
[User] -> [AWS sts:AssumeRoleWithSAML]
                    |
                    v
            [임시 자격 증명 발급]
                    |
                    v
            [AWS Console / CLI 사용]
```

OIDC 기반(GitHub Actions, Google 등)은 `sts:AssumeRoleWithWebIdentity`를 사용하며, 모바일 앱은 Cognito를 거쳐 Identity Pool로 임시 자격 증명을 받습니다.

### Service-Linked Role

일부 AWS 서비스는 자신의 동작을 위해 사전 정의된 Role이 필요합니다. 이를 Service-Linked Role(SLR)이라고 합니다.

- AWS가 Trust Policy와 Permissions Policy를 관리합니다.
- 사용자가 임의로 수정하거나 삭제할 수 없습니다.
- 예: `AWSServiceRoleForElasticLoadBalancing`, `AWSServiceRoleForAutoScaling`.

---

## 실전 사용

### 1. IAM Conditions 활용

IAM Policy의 Condition 블록은 정밀한 접근 제어의 핵심입니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::sensitive-bucket/*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": ["203.0.113.0/24"]
        },
        "Bool": {
          "aws:SecureTransport": "true",
          "aws:MultiFactorAuthPresent": "true"
        },
        "StringEquals": {
          "aws:PrincipalOrgID": "o-abc123def4"
        }
      }
    }
  ]
}
```

자주 사용되는 Condition Key는 다음과 같습니다.

- `aws:SourceIp`: 요청 IP 제한
- `aws:PrincipalOrgID`: Organization 내부 호출만 허용
- `aws:SecureTransport`: HTTPS 강제
- `aws:MultiFactorAuthPresent`: MFA 인증 강제
- `aws:RequestedRegion`: 특정 리전에서만 허용
- `aws:ResourceTag/<key>`: 태그 기반 접근 제어(ABAC)

### 2. EC2 Instance Profile

EC2가 다른 AWS 서비스를 호출할 때는 액세스 키가 아니라 Instance Profile을 사용해야 합니다.

```bash
# Instance Profile 생성 및 Role 추가
aws iam create-instance-profile --instance-profile-name webapp-profile
aws iam add-role-to-instance-profile \
  --instance-profile-name webapp-profile \
  --role-name webapp-role

# EC2 인스턴스에 Profile 부착
aws ec2 associate-iam-instance-profile \
  --instance-id i-0123456789abcdef0 \
  --iam-instance-profile Name=webapp-profile
```

EC2 내부에서는 IMDSv2(Instance Metadata Service v2)를 통해 임시 자격 증명을 자동으로 가져옵니다. AWS SDK는 이 과정을 투명하게 처리합니다.

### 3. CloudTrail로 IAM 활동 감사

모든 IAM 호출은 CloudTrail에 기록됩니다. 다음 이벤트는 보안 알람을 설정하는 것이 좋습니다.

- `ConsoleLogin` (특히 Root 계정)
- `CreateAccessKey` / `DeleteAccessKey`
- `AttachUserPolicy` / `PutUserPolicy`
- `AssumeRole` (예상치 못한 Principal)

```bash
# CloudTrail에서 Root 로그인 검색
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin \
  --max-results 50
```

### 4. ABAC (Attribute-Based Access Control)

태그 기반 접근 제어로 정책 수를 폭발적으로 줄일 수 있습니다.

```json
{
  "Effect": "Allow",
  "Action": ["ec2:StartInstances", "ec2:StopInstances"],
  "Resource": "arn:aws:ec2:*:*:instance/*",
  "Condition": {
    "StringEquals": {
      "aws:ResourceTag/Owner": "${aws:username}"
    }
  }
}
```

위 정책은 자신의 username과 같은 Owner 태그를 가진 인스턴스만 시작/중지할 수 있게 합니다. 사용자가 수백 명이어도 정책 하나로 관리됩니다.

---

## 가격/한도

### 가격

- **IAM 자체**: 완전 무료
- **IAM Identity Center**: 완전 무료
- **IAM Access Analyzer**: External Access는 무료, Unused Access는 사용한 IAM Role/User 1개당 월 $0.20

### 주요 한도

| 항목 | 기본 한도 | 비고 |
|------|----------|------|
| 계정당 User 수 | 5,000 | Identity Center 사용 권장 |
| 계정당 Role 수 | 1,000 | 증가 요청 가능 |
| 계정당 Group 수 | 300 | |
| Group당 User 수 | 무제한 | |
| User당 액세스 키 | 2개 | 회전 시 일시적 2개 운용 |
| User당 정책 부착 수 | 10개 | |
| Policy 크기 | 6,144자 (관리형), 2,048자 (인라인 User) | |
| AssumeRole 세션 시간 | 15분 ~ 12시간 | 기본 1시간 |

---

## Best Practice

### 1. Root 사용자 사용 금지

Root 계정은 다음 작업에만 사용하고, 이외에는 절대 사용하지 않습니다.

- AWS 계정 폐쇄
- 결제 정보 변경
- IAM 사용자 권한 복구 (다른 모든 사용자가 잠긴 경우)
- AWS Support 플랜 변경

Root 계정에는 반드시 다음을 적용합니다.

- 강력한 비밀번호 설정
- 하드웨어 MFA 활성화 (소프트웨어 MFA보다 권장)
- 액세스 키 발급 금지 (이미 있다면 즉시 삭제)

### 2. 최소 권한 원칙(Least Privilege)

처음에는 최소 권한으로 시작하고, 필요할 때만 권한을 추가합니다. IAM Access Analyzer의 Policy Generator를 활용하여 CloudTrail 기반으로 실사용 권한 정책을 생성하는 것이 효과적입니다.

### 3. MFA 강제

다음 정책으로 MFA가 없으면 모든 작업을 거부할 수 있습니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyAllExceptMFASetup",
      "Effect": "Deny",
      "NotAction": [
        "iam:ChangePassword",
        "iam:CreateVirtualMFADevice",
        "iam:EnableMFADevice",
        "iam:GetUser",
        "iam:ListMFADevices",
        "sts:GetSessionToken"
      ],
      "Resource": "*",
      "Condition": {
        "BoolIfExists": {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    }
  ]
}
```

### 4. 액세스 키 회전 및 제거

- 90일 주기로 액세스 키를 회전합니다.
- 가능하다면 액세스 키 자체를 사용하지 말고, IAM Role + STS 또는 IAM Identity Center를 사용합니다.
- IAM Credentials Report로 미사용 키를 정기적으로 점검합니다.

```bash
# Credentials Report 생성 및 다운로드
aws iam generate-credential-report
aws iam get-credential-report --query 'Content' --output text | base64 -d > report.csv
```

### 5. Permissions Boundary로 위임

개발자에게 IAM 권한을 위임할 때는 반드시 Permissions Boundary를 함께 적용하여 권한 상승(Privilege Escalation)을 방지합니다.

### 6. 정기 감사

- IAM Access Analyzer의 Findings를 주간 단위로 검토합니다.
- 90일 이상 미사용된 자격 증명, 정책, Role을 정리합니다.
- AWS Config Rule로 IAM 모범 사례 준수 여부를 자동 점검합니다.

---

## 관련 서비스

| 서비스 | 관계 |
|--------|------|
| AWS Organizations | SCP를 통한 다계정 가드레일 |
| AWS KMS | Key Policy + IAM Policy 이중 인가 |
| AWS Secrets Manager | IAM 기반 시크릿 접근 제어 |
| AWS CloudTrail | IAM 활동 감사 로그 |
| AWS Config | IAM 모범 사례 준수 자동 점검 |
| Amazon Cognito | 외부 사용자(B2C)용 인증, Identity Pool로 IAM 자격 증명 발급 |
| AWS Security Hub | IAM 보안 점수 통합 대시보드 |

---

## 관련 문서

- [[aws-kms-key-management-service-개요|AWS KMS]] - IAM과 함께 이중 인가 모델 구성
- [[amazon-cognito-사용자-인증-서비스-개요|Amazon Cognito]] - 외부 사용자 인증 후 IAM Role 발급
- [[amazon-rds|Amazon RDS]] - IAM Database Authentication으로 패스워드 없는 접근
