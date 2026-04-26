<!-- infographic-hero -->
![AWS Control Tower Account Factory 핵심 요약](figures/infographic.svg)

*Figure: AWS Control Tower Account Factory 한 장 요약 인포그래픽*

## 개요

AWS Control Tower Account Factory는 멀티 계정 환경에서 새로운 AWS 계정을 표준화된 방식으로 자동 프로비저닝하는 기능입니다. AWS Service Catalog를 기반으로 동작하며, 사전 정의된 네트워크 구성, 보안 설정, 리전 제한 등을 적용하여 일관성 있는 계정을 빠르게 생성할 수 있습니다.

기업 환경에서 새로운 프로젝트나 팀이 생길 때마다 수동으로 AWS 계정을 생성하고 기본 설정을 적용하는 것은 비효율적이고 오류가 발생하기 쉽습니다. Account Factory는 이러한 과정을 자동화하여, 계정 생성부터 기본 인프라 배포까지 전체 프로세스를 표준화합니다.

### Account Factory의 주요 가치

- **표준화**: 모든 계정이 동일한 기본 구성으로 생성되어 일관성을 보장합니다.
- **자동화**: 수작업 없이 몇 분 내에 완전히 구성된 계정을 프로비저닝합니다.
- **거버넌스**: Control Tower 가드레일이 자동으로 적용되어 보안 기준을 충족합니다.
- **셀프서비스**: 적절한 권한이 있는 사용자가 직접 계정을 요청하고 생성할 수 있습니다.

## 핵심 기능

### 1. 기본 Account Factory

Account Factory의 기본 기능은 AWS Service Catalog 제품(Product)으로 구현됩니다. 계정 생성 시 다음 항목을 구성할 수 있습니다.

**계정 기본 설정**
- 계정 이름 및 이메일 주소
- IAM Identity Center 사용자 또는 그룹 매핑
- 소속 OU(Organizational Unit) 지정

**네트워크 구성**
- VPC CIDR 범위 지정
- 서브넷 구성 (퍼블릭/프라이빗)
- 리전별 VPC 생성 여부
- NAT Gateway 구성

**거버넌스 설정**
- 허용 리전 제한
- 가드레일 자동 적용
- CloudTrail/Config 자동 활성화

계정 생성에 사용할 수 있는 AWS CLI 명령은 다음과 같습니다.

```bash
# Service Catalog에서 Account Factory 제품 확인
aws servicecatalog search-products \
  --query 'ProductViewSummaries[?Name==`AWS Control Tower Account Factory`]' \
  --output json

# Account Factory 제품의 프로비저닝 아티팩트(버전) 확인
aws servicecatalog list-provisioning-artifacts \
  --product-id "prod-abcdefghijkl" \
  --output json

# Account Factory를 통한 계정 프로비저닝
aws servicecatalog provision-product \
  --product-id "prod-abcdefghijkl" \
  --provisioning-artifact-id "pa-abcdefghijkl" \
  --provisioned-product-name "new-workload-account" \
  --provisioning-parameters \
    Key=AccountName,Value=workload-prod \
    Key=AccountEmail,Value=workload-prod@example.com \
    Key=SSOUserEmail,Value=admin@example.com \
    Key=SSOUserFirstName,Value=Admin \
    Key=SSOUserLastName,Value=User \
    Key=ManagedOrganizationalUnit,Value=Workloads \
  --region us-east-1
```

### 2. Account Factory Customization (AFC)

AFC는 Account Factory에 사용자 정의 블루프린트를 추가할 수 있는 기능입니다. Service Catalog 블루프린트를 통해 계정 생성 시 추가적인 리소스를 자동으로 배포할 수 있습니다.

AFC에서 사용할 수 있는 블루프린트 유형은 다음과 같습니다.

- **CloudFormation 템플릿**: 표준 AWS 리소스를 프로비저닝합니다.
- **Terraform 구성**: HashiCorp Terraform을 사용한 인프라 배포를 지원합니다.
- **CDK 기반 블루프린트**: AWS CDK로 작성한 인프라를 블루프린트로 등록할 수 있습니다.

블루프린트 예시 - 기본 보안 구성을 자동 배포하는 CloudFormation 템플릿입니다.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Account Factory Custom Blueprint - Security Baseline

Resources:
  SecurityAlarmSNSTopic:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: security-alarms
      DisplayName: Security Alarm Notifications

  RootAccountUsageAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: RootAccountUsage
      AlarmDescription: Root account usage detected
      MetricName: RootAccountUsage
      Namespace: CloudTrailMetrics
      Statistic: Sum
      Period: 300
      EvaluationPeriods: 1
      Threshold: 1
      ComparisonOperator: GreaterThanOrEqualToThreshold
      AlarmActions:
        - !Ref SecurityAlarmSNSTopic

  EBSEncryptionByDefault:
    Type: AWS::EC2::EncryptionByDefault
    Properties:
      Enabled: true

  S3AccountPublicAccessBlock:
    Type: AWS::S3::AccountPublicAccessBlock
    Properties:
      BlockPublicAcls: true
      BlockPublicPolicy: true
      IgnorePublicAcls: true
      RestrictPublicBuckets: true

  IMDSv2LaunchTemplate:
    Type: AWS::EC2::LaunchTemplate
    Properties:
      LaunchTemplateName: enforce-imdsv2
      LaunchTemplateData:
        MetadataOptions:
          HttpEndpoint: enabled
          HttpTokens: required
          HttpPutResponseHopLimit: 1
```

```bash
# 블루프린트를 Service Catalog 제품으로 등록
aws servicecatalog create-product \
  --name "Security-Baseline-Blueprint" \
  --owner "Cloud-Team" \
  --product-type CLOUD_FORMATION_TEMPLATE \
  --provisioning-artifact-parameters \
    Name=v1.0,Info={LoadTemplateFromURL=https://s3.amazonaws.com/my-bucket/security-baseline.yaml},Type=CLOUD_FORMATION_TEMPLATE \
  --region us-east-1
```

### 3. Account Factory for Terraform (AFT)

AFT는 HashiCorp Terraform을 사용하여 Account Factory를 확장하는 오픈소스 솔루션입니다. Terraform 코드로 계정 요청, 커스터마이징, 프로비저닝 전체 과정을 관리할 수 있습니다.

AFT의 아키텍처는 다음과 같은 구성 요소로 이루어집니다.

- **AFT Management Account**: AFT 인프라가 배포되는 전용 계정입니다.
- **Account Request Repository**: 계정 요청을 Terraform 코드로 정의합니다.
- **Global Customizations Repository**: 모든 계정에 공통으로 적용할 커스터마이징을 정의합니다.
- **Account Customizations Repository**: 특정 계정에만 적용할 커스터마이징을 정의합니다.
- **Account Provisioning Customizations Repository**: 프로비저닝 시점에 실행할 커스터마이징을 정의합니다.

AFT를 통한 계정 요청 코드 예시입니다.

```python
# aft-account-request/terraform/main.tf
module "new_workload_account" {
  source = "./modules/aft-account-request"

  control_tower_parameters = {
    AccountEmail              = "workload-app-a@example.com"
    AccountName               = "workload-app-a-prod"
    ManagedOrganizationalUnit = "Workloads (ou-abc1-23456789)"
    SSOUserEmail              = "admin@example.com"
    SSOUserFirstName          = "Admin"
    SSOUserLastName           = "User"
  }

  account_tags = {
    Environment = "Production"
    Team        = "App-A"
    CostCenter  = "CC-1234"
  }

  change_management_parameters = {
    change_requested_by = "cloud-team"
    change_reason       = "New production account for App-A"
  }

  custom_fields = {
    vpc_cidr     = "10.100.0.0/16"
    environment  = "prod"
    enable_guard_duty = "true"
  }

  account_customizations_name = "production-baseline"
}
```

## 아키텍처/동작 원리

### Account Factory 프로비저닝 워크플로우

Account Factory를 통한 계정 생성은 다음 단계로 진행됩니다.

```
1. 계정 요청 (Account Request)
   ├── Service Catalog 제품 프로비저닝 시작
   └── 또는 AFT의 Terraform 코드 커밋

2. 계정 생성 (Account Creation)
   ├── Organizations에서 새 계정 생성
   ├── 지정된 OU로 계정 이동
   └── IAM Identity Center 사용자/역할 구성

3. 기본 설정 적용 (Baseline Application)
   ├── CloudTrail 활성화
   ├── AWS Config 활성화 및 규칙 배포
   ├── 가드레일 SCP 적용
   └── VPC 네트워크 구성 (선택적)

4. 커스터마이징 (Customization)
   ├── 블루프린트 배포 (AFC)
   ├── Global Customizations 실행 (AFT)
   └── Account Customizations 실행 (AFT)

5. 완료 및 알림
   ├── 프로비저닝 상태 업데이트
   └── 요청자에게 완료 알림
```

### AFT 내부 아키텍처

AFT는 내부적으로 AWS 서비스를 조합하여 파이프라인을 구성합니다.

```
CodeCommit/GitHub Repository
    │
    ▼
CodePipeline (Account Request Pipeline)
    │
    ├── CodeBuild (Terraform Plan/Apply)
    │       │
    │       ▼
    │   Control Tower API (CreateManagedAccount)
    │       │
    │       ▼
    │   Step Functions (Customization Orchestration)
    │       │
    │       ├── Lambda (Pre-Processing)
    │       ├── CodeBuild (Global Customizations)
    │       ├── CodeBuild (Account Customizations)
    │       └── Lambda (Post-Processing)
    │
    └── DynamoDB (Account Request Tracking)
        └── SNS (Notifications)
```

### VPC 기본 구성

Account Factory에서 VPC를 함께 구성하면, 다음과 같은 기본 네트워크가 생성됩니다.

```json
{
  "VPC": {
    "CIDR": "10.0.0.0/16",
    "Subnets": {
      "Public": [
        {"AZ": "az-1", "CIDR": "10.0.0.0/24"},
        {"AZ": "az-2", "CIDR": "10.0.1.0/24"}
      ],
      "Private": [
        {"AZ": "az-1", "CIDR": "10.0.10.0/24"},
        {"AZ": "az-2", "CIDR": "10.0.11.0/24"}
      ]
    },
    "InternetGateway": true,
    "NATGateway": true
  }
}
```

## 실전 활용

### 계정 프로비저닝 자동화 파이프라인 구축

실무에서는 Account Factory를 CI/CD 파이프라인과 연동하여 완전 자동화된 계정 프로비저닝 체계를 구축합니다.

```bash
# 1. AFT 모듈 배포 (AFT Management Account에서)
terraform init
terraform plan -out=aft-plan
terraform apply aft-plan

# 2. 계정 요청 레포지토리에 새 계정 요청 추가
git clone https://github.com/org/aft-account-request.git
cd aft-account-request

# 3. 새 계정 요청 Terraform 파일 작성 후 커밋
git add terraform/new-account.tf
git commit -m "Request new production account for App-B"
git push origin main

# 4. 계정 프로비저닝 상태 모니터링
aws servicecatalog describe-provisioned-product \
  --id "pp-abcdefghijkl" \
  --query 'ProvisionedProductDetail.Status' \
  --output text

# 5. 프로비저닝된 계정 목록 확인
aws servicecatalog search-provisioned-products \
  --access-level-filter Key=Account,Value=self \
  --query 'ProvisionedProducts[*].{Name:Name,Status:Status,Id:Id}' \
  --output table
```

### 네트워크 사전 구성 자동화

대규모 환경에서는 계정 생성 시 Transit Gateway 연결까지 자동으로 구성하는 것이 일반적입니다.

```yaml
# account-network-baseline.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Network baseline with Transit Gateway attachment

Parameters:
  VpcCidr:
    Type: String
    Default: '10.0.0.0/16'
  TransitGatewayId:
    Type: String
    Description: Shared Transit Gateway ID

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VpcCidr
      EnableDnsSupport: true
      EnableDnsHostnames: true
      Tags:
        - Key: Name
          Value: !Sub '${AWS::AccountId}-main-vpc'

  TransitGatewayAttachment:
    Type: AWS::EC2::TransitGatewayAttachment
    Properties:
      TransitGatewayId: !Ref TransitGatewayId
      VpcId: !Ref VPC
      SubnetIds:
        - !Ref PrivateSubnet1
        - !Ref PrivateSubnet2
      Tags:
        - Key: Name
          Value: !Sub '${AWS::AccountId}-tgw-attachment'

  PrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: !Select [0, !Cidr [!Ref VpcCidr, 4, 8]]
      AvailabilityZone: !Select [0, !GetAZs '']

  PrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: !Select [1, !Cidr [!Ref VpcCidr, 4, 8]]
      AvailabilityZone: !Select [1, !GetAZs '']
```

### 계정 업데이트 및 재등록

기존 계정의 구성을 변경하거나, Control Tower 업그레이드 후 계정을 재등록해야 하는 경우가 있습니다.

```bash
# 프로비저닝된 제품 업데이트 (OU 변경 등)
aws servicecatalog update-provisioned-product \
  --provisioned-product-id "pp-abcdefghijkl" \
  --product-id "prod-abcdefghijkl" \
  --provisioning-artifact-id "pa-newversion123" \
  --provisioning-parameters \
    Key=ManagedOrganizationalUnit,Value=Production \
  --region us-east-1

# 계정 재등록 (Re-enroll) - Control Tower 콘솔에서 수행하거나
# Organizations API를 통해 계정 OU를 이동하면 자동으로 재등록됩니다
aws organizations move-account \
  --account-id 123456789012 \
  --source-parent-id ou-abc1-oldou \
  --destination-parent-id ou-abc1-newou
```

### 계정 폐기 프로세스

더 이상 필요하지 않은 계정을 정리하는 프로세스도 중요합니다.

```bash
# 1. 계정의 모든 리소스 확인
aws resourcegroupstaggingapi get-resources \
  --query 'ResourceTagMappingList[*].ResourceARN' \
  --output json

# 2. Service Catalog에서 프로비저닝된 제품 종료
aws servicecatalog terminate-provisioned-product \
  --provisioned-product-id "pp-abcdefghijkl" \
  --region us-east-1

# 3. 계정을 Suspended OU로 이동
aws organizations move-account \
  --account-id 123456789012 \
  --source-parent-id ou-abc1-workloads \
  --destination-parent-id ou-abc1-suspended

# 4. 계정 폐쇄 (Organizations에서)
aws organizations close-account \
  --account-id 123456789012
```

## 모범 사례/보안

### 계정 프로비저닝 모범 사례

1. **이메일 주소 관리 체계를 수립하십시오.** AWS 계정마다 고유한 이메일 주소가 필요합니다. 이메일 별칭(alias) 기능을 활용하면 효율적으로 관리할 수 있습니다. 예를 들어 `aws+workload-prod@example.com`과 같은 형식을 사용합니다.

2. **계정 태깅 전략을 정의하십시오.** 모든 계정에 일관된 태그를 적용하면 비용 추적, 리소스 관리, 보안 감사에 유리합니다.

```json
{
  "tags": {
    "Environment": "Production",
    "Team": "Platform",
    "CostCenter": "CC-5678",
    "DataClassification": "Confidential",
    "ComplianceScope": "PCI-DSS"
  }
}
```

3. **VPC 설계를 사전에 표준화하십시오.** CIDR 블록 충돌을 방지하기 위해 IP 주소 관리(IPAM)를 도입하고, 환경별 CIDR 범위를 사전에 할당하십시오.

4. **커스터마이징을 코드로 관리하십시오.** AFC 블루프린트나 AFT 커스터마이징은 반드시 버전 관리 시스템(Git)에서 관리해야 합니다.

### 보안 관련 모범 사례

- 계정 생성 후 즉시 보안 기준선(Security Baseline)을 적용하십시오. GuardDuty 활성화, S3 퍼블릭 액세스 차단, EBS 기본 암호화 등이 포함됩니다.
- 계정의 루트 사용자에 대해 MFA를 반드시 활성화하십시오.
- 계정 요청 승인 워크플로우를 구축하여 무분별한 계정 생성을 방지하십시오.
- 미사용 계정은 Suspended OU로 이동하여 리소스 생성을 차단하십시오.

### 비용 관리 모범 사례

- 계정 생성 시 AWS Budgets를 자동으로 설정하여 예산 초과를 방지하십시오.
- VPC NAT Gateway는 비용이 높으므로, 개발 환경에서는 VPC 엔드포인트나 단순화된 네트워크 구성을 사용하는 것을 고려하십시오.
- Account Factory에서 불필요한 기본 VPC 생성을 비활성화하여 비용을 절감하십시오.

## 관련 서비스 비교

### Account Factory vs AFT vs 직접 자동화

| 항목 | Account Factory (기본) | AFC (Customization) | AFT (Terraform) | 직접 자동화 |
|------|----------------------|--------------------|-----------------|-----------|
| 도구 | Service Catalog 콘솔 | Service Catalog + 블루프린트 | Terraform + Pipeline | 자체 스크립트 |
| IaC 지원 | 제한적 | CloudFormation/CDK | Terraform | 자유 선택 |
| 커스터마이징 범위 | 기본 설정만 | 블루프린트 배포 | 전체 인프라 | 무제한 |
| 승인 워크플로우 | 수동 | 수동 | Git 기반 | 자체 구현 |
| 학습 곡선 | 낮음 | 중간 | 높음 | 매우 높음 |
| 유지보수 부담 | 낮음 | 중간 | 중간 | 높음 |

### Account Factory와 연동되는 서비스

- **AWS Service Catalog**: Account Factory의 기반 서비스로, 계정 프로비저닝을 제품으로 관리합니다.
- **AWS IAM Identity Center**: 생성된 계정에 SSO 사용자 및 권한 세트를 자동 할당합니다.
- **AWS Organizations**: 계정 생성 및 OU 배치를 관리합니다.
- **Amazon VPC IPAM**: 계정별 VPC CIDR 자동 할당에 활용할 수 있습니다.

## 요약

AWS Control Tower Account Factory는 멀티 계정 환경에서 계정 프로비저닝을 자동화하고 표준화하는 핵심 기능입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **기본 Account Factory**: Service Catalog 기반으로 표준화된 계정을 빠르게 프로비저닝합니다.
- **AFC (Account Factory Customization)**: 블루프린트를 통해 계정 생성 시 추가 리소스를 자동 배포합니다.
- **AFT (Account Factory for Terraform)**: Terraform 코드로 전체 계정 라이프사이클을 관리합니다.
- **네트워크 자동화**: VPC, 서브넷, Transit Gateway 연결까지 자동으로 구성할 수 있습니다.
- **라이프사이클 관리**: 계정 생성부터 업데이트, 폐기까지 전체 과정을 체계적으로 관리합니다.

조직의 규모와 성숙도에 따라 기본 Account Factory에서 시작하여 AFC, AFT로 점진적으로 확장하는 것이 권장됩니다. 특히 계정 수가 50개를 초과하거나, 계정 프로비저닝 빈도가 높은 환경에서는 AFT를 도입하여 완전 자동화된 계정 관리 체계를 구축하는 것이 효과적입니다.