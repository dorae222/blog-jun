<!-- infographic-hero -->
![AWS Service Catalog 핵심 요약](figures/infographic.svg)

*Figure: AWS Service Catalog 한 장 요약 인포그래픽*

## 개요

AWS Service Catalog는 조직에서 승인한 IT 서비스와 인프라 템플릿을 카탈로그 형태로 관리하고, 사용자가 셀프서비스 방식으로 프로비저닝할 수 있게 해주는 서비스입니다. 쉽게 말해, 기업의 "AWS 인프라 쇼핑몰"을 구축하는 서비스입니다.

클라우드 도입 초기에는 소수의 관리자가 모든 인프라를 직접 생성합니다. 하지만 조직이 커지면서 개발팀이 다양한 인프라를 요청하게 되면, 모든 요청을 관리자가 처리하는 것은 병목이 됩니다. 반면 개발자에게 전체 AWS 권한을 부여하면 보안과 비용 통제가 어려워집니다.

Service Catalog는 이 딜레마를 해결합니다. 관리자가 승인된 인프라 템플릿을 카탈로그에 등록하면, 개발자는 카탈로그에서 필요한 인프라를 직접 선택하여 프로비저닝할 수 있습니다. 이때 리소스는 관리자가 정의한 규격과 제약 조건에 따라 생성되므로, 보안과 비용 통제가 보장됩니다.

### Service Catalog의 핵심 가치

- **거버넌스**: 승인된 템플릿만 사용하도록 제한합니다.
- **셀프서비스**: 개발자가 직접 인프라를 프로비저닝합니다.
- **표준화**: 조직의 모범 사례에 맞는 인프라를 자동으로 구성합니다.
- **비용 통제**: 허용된 인스턴스 유형, 리전 등을 제한합니다.
- **감사**: 누가 언제 무엇을 프로비저닝했는지 추적합니다.

## 핵심 기능

### 1. 포트폴리오 (Portfolio)

포트폴리오는 제품(Product)의 논리적 그룹입니다. 팀이나 부서별로 포트폴리오를 구성하여, 해당 그룹에 적합한 제품만 노출할 수 있습니다.

```bash
# 포트폴리오 생성
aws servicecatalog create-portfolio \
  --display-name "Data Engineering Portfolio" \
  --description "데이터 엔지니어링 팀을 위한 승인된 인프라 카탈로그" \
  --provider-name "Cloud Platform Team" \
  --region ap-northeast-2

# 포트폴리오 목록 조회
aws servicecatalog list-portfolios \
  --query 'PortfolioDetails[*].{Id:Id,Name:DisplayName,Provider:ProviderName,Created:CreatedTime}' \
  --output table \
  --region ap-northeast-2

# 포트폴리오에 IAM 주체 (사용자/그룹/역할) 접근 권한 부여
aws servicecatalog associate-principal-with-portfolio \
  --portfolio-id "port-abc123" \
  --principal-arn "arn:aws:iam::123456789012:role/DataEngineerRole" \
  --principal-type IAM_PATTERN \
  --region ap-northeast-2
```

### 2. 제품 (Product)

제품은 프로비저닝 가능한 인프라 템플릿입니다. CloudFormation 템플릿 또는 Terraform 구성을 기반으로 합니다.

```bash
# CloudFormation 기반 제품 생성
aws servicecatalog create-product \
  --name "EMR-Cluster-Standard" \
  --description "표준 EMR 클러스터 (Spark + Hive)" \
  --product-type CLOUD_FORMATION_TEMPLATE \
  --owner "Cloud Platform Team" \
  --provisioning-artifact-parameters \
    'Name=v1.0,Description=Initial version,Info={LoadTemplateFromURL=https://s3.ap-northeast-2.amazonaws.com/cf-templates/emr-standard.yaml},Type=CLOUD_FORMATION_TEMPLATE' \
  --tags Key=Team,Value=Platform Key=Category,Value=BigData \
  --region ap-northeast-2

# 제품을 포트폴리오에 추가
aws servicecatalog associate-product-with-portfolio \
  --product-id "prod-abc123" \
  --portfolio-id "port-abc123" \
  --region ap-northeast-2

# 제품 목록 조회
aws servicecatalog search-products \
  --query 'ProductViewSummaries[*].{Id:ProductId,Name:Name,Owner:Owner,Type:Type}' \
  --output table \
  --region ap-northeast-2
```

제품에 사용할 CloudFormation 템플릿 예시입니다.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Standard S3 Bucket with encryption and versioning

Parameters:
  BucketNameSuffix:
    Type: String
    Description: S3 버킷 이름 접미사
    AllowedPattern: '[a-z0-9-]+'
    ConstraintDescription: 소문자, 숫자, 하이픈만 허용됩니다
  
  Environment:
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - staging
      - prod
    Description: 환경 구분

Resources:
  S3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub '${AWS::AccountId}-${Environment}-${BucketNameSuffix}'
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: aws:kms
              KMSMasterKeyID: !Ref KMSKey
      VersioningConfiguration:
        Status: Enabled
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: TransitionToIA
            Status: Enabled
            Transitions:
              - TransitionInDays: 90
                StorageClass: STANDARD_IA
          - Id: TransitionToGlacier
            Status: Enabled
            Transitions:
              - TransitionInDays: 365
                StorageClass: GLACIER
      Tags:
        - Key: Environment
          Value: !Ref Environment
        - Key: ManagedBy
          Value: ServiceCatalog

  KMSKey:
    Type: AWS::KMS::Key
    Properties:
      Description: !Sub 'KMS key for ${BucketNameSuffix} bucket'
      EnableKeyRotation: true
      KeyPolicy:
        Version: '2012-10-17'
        Statement:
          - Sid: EnableRootAccountAccess
            Effect: Allow
            Principal:
              AWS: !Sub 'arn:aws:iam::${AWS::AccountId}:root'
            Action: 'kms:*'
            Resource: '*'

Outputs:
  BucketName:
    Value: !Ref S3Bucket
  BucketArn:
    Value: !GetAtt S3Bucket.Arn
  KMSKeyId:
    Value: !Ref KMSKey
```

### 3. 제약 조건 (Constraints)

제약 조건은 제품 프로비저닝 시 적용되는 규칙입니다.

| 제약 유형 | 설명 |
|----------|------|
| Launch Constraint | 제품 실행 시 사용할 IAM 역할을 지정합니다 |
| Notification Constraint | 프로비저닝 이벤트를 SNS로 알립니다 |
| Tag Update Constraint | 프로비저닝된 제품의 태그 수정 허용 여부를 제어합니다 |
| Stack Set Constraint | CloudFormation StackSet 배포 설정을 정의합니다 |
| Template Constraint | 파라미터 값을 제한합니다 |

```bash
# Launch Constraint 생성 (중요: 사용자 대신 이 역할로 CloudFormation을 실행)
aws servicecatalog create-constraint \
  --portfolio-id "port-abc123" \
  --product-id "prod-abc123" \
  --type LAUNCH \
  --parameters '{"RoleArn":"arn:aws:iam::123456789012:role/ServiceCatalogLaunchRole"}' \
  --description "Launch constraint for S3 bucket product" \
  --region ap-northeast-2

# Template Constraint 생성 (허용된 파라미터 값 제한)
aws servicecatalog create-constraint \
  --portfolio-id "port-abc123" \
  --product-id "prod-abc123" \
  --type TEMPLATE \
  --parameters '{
    "Rules": {
      "RestrictInstanceType": {
        "Assertions": [{
          "Assert": {"Fn::Contains": [["t3.micro", "t3.small", "t3.medium"], {"Ref": "InstanceType"}]},
          "AssertDescription": "Only t3.micro, t3.small, t3.medium are allowed"
        }]
      }
    }
  }' \
  --description "Restrict instance types" \
  --region ap-northeast-2

# Notification Constraint 생성
aws servicecatalog create-constraint \
  --portfolio-id "port-abc123" \
  --product-id "prod-abc123" \
  --type NOTIFICATION \
  --parameters '{"NotificationArns":["arn:aws:sns:ap-northeast-2:123456789012:service-catalog-notifications"]}' \
  --region ap-northeast-2
```

### 4. TagOption

TagOption은 포트폴리오나 제품에 연결하여, 프로비저닝 시 자동으로 태그를 적용하는 기능입니다.

```bash
# TagOption 생성
aws servicecatalog create-tag-option \
  --key "CostCenter" \
  --value "CC-DataEng-001" \
  --region ap-northeast-2

# TagOption을 포트폴리오에 연결
aws servicecatalog associate-tag-option-with-resource \
  --resource-id "port-abc123" \
  --tag-option-id "tag-abc123" \
  --region ap-northeast-2

# TagOption 목록 조회
aws servicecatalog list-tag-options \
  --query 'TagOptionDetails[*].{Id:Id,Key:Key,Value:Value,Active:Active}' \
  --output table \
  --region ap-northeast-2
```

### 5. Terraform 지원

Service Catalog는 CloudFormation뿐만 아니라 Terraform 구성도 제품으로 등록할 수 있습니다.

```bash
# Terraform 기반 제품 생성
aws servicecatalog create-product \
  --name "EKS-Cluster-Terraform" \
  --description "Terraform으로 프로비저닝되는 표준 EKS 클러스터" \
  --product-type TERRAFORM_OPEN_SOURCE \
  --owner "Cloud Platform Team" \
  --provisioning-artifact-parameters \
    'Name=v1.0,Description=Initial Terraform version,Info={LoadTemplateFromURL=https://s3.ap-northeast-2.amazonaws.com/tf-templates/eks-cluster.tar.gz},Type=TERRAFORM_OPEN_SOURCE' \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### Service Catalog 동작 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                  Service Catalog                     │
│                                                     │
│  관리자 (Admin)                사용자 (End User)      │
│  ┌────────────┐               ┌────────────────┐    │
│  │ 포트폴리오  │               │ 제품 카탈로그    │    │
│  │ 생성/관리   │               │ 검색/프로비저닝  │    │
│  │            │               │                │    │
│  │ 제품 등록   │──────────────►│ 셀프서비스      │    │
│  │ 제약 조건   │               │ 포털            │    │
│  │ 접근 제어   │               │                │    │
│  └────────────┘               └───────┬────────┘    │
│                                       │             │
│                                       ▼             │
│                              ┌────────────────┐     │
│                              │ Provisioned     │     │
│                              │ Product         │     │
│                              │                │     │
│                              │ CloudFormation │     │
│                              │ 또는 Terraform  │     │
│                              └───────┬────────┘     │
│                                       │             │
└───────────────────────────────────────┼─────────────┘
                                        │
                                        ▼
                               ┌────────────────┐
                               │ AWS 리소스       │
                               │ (EC2, RDS, S3...) │
                               └────────────────┘
```

### Launch Constraint 동작 원리

Launch Constraint는 Service Catalog에서 가장 중요한 개념 중 하나입니다.

사용자가 제품을 프로비저닝할 때, 사용자의 IAM 권한이 아닌 Launch Constraint에 지정된 IAM 역할의 권한으로 CloudFormation이 실행됩니다. 이를 통해 사용자에게 최소한의 Service Catalog 권한만 부여하면서도, 필요한 AWS 리소스를 생성할 수 있습니다.

```
사용자 (IAM 권한: ServiceCatalog만 허용)
    │
    ▼ "S3 버킷 프로비저닝" 요청
    │
Service Catalog
    │
    ▼ Launch Constraint 역할로 전환
    │  (IAM 역할: S3, KMS 리소스 생성 권한)
    │
CloudFormation
    │
    ▼ 리소스 생성
    │
S3 Bucket + KMS Key 생성 완료
```

### 포트폴리오 공유

포트폴리오를 다른 AWS 계정이나 Organizations 전체와 공유할 수 있습니다.

```bash
# 특정 계정과 포트폴리오 공유
aws servicecatalog create-portfolio-share \
  --portfolio-id "port-abc123" \
  --account-id "987654321098" \
  --region ap-northeast-2

# Organizations 전체와 공유
aws servicecatalog create-portfolio-share \
  --portfolio-id "port-abc123" \
  --organization-node '{"Type":"ORGANIZATION","Value":"o-abc123"}' \
  --region ap-northeast-2

# 특정 OU와만 공유
aws servicecatalog create-portfolio-share \
  --portfolio-id "port-abc123" \
  --organization-node '{"Type":"ORGANIZATIONAL_UNIT","Value":"ou-abc1-production"}' \
  --region ap-northeast-2

# 공유 상태 확인
aws servicecatalog list-portfolio-access \
  --portfolio-id "port-abc123" \
  --query 'AccountIds' \
  --output json \
  --region ap-northeast-2
```

## 실전 활용

### 셀프서비스 인프라 포털 구축

개발팀이 승인된 인프라를 직접 프로비저닝할 수 있는 환경을 구축하는 전체 과정입니다.

```bash
# 1. 포트폴리오 생성
aws servicecatalog create-portfolio \
  --display-name "Development Team Infrastructure" \
  --description "개발팀용 승인된 인프라 카탈로그" \
  --provider-name "Platform Team" \
  --region ap-northeast-2

# 2. 여러 제품 등록
# 2-1. S3 버킷 제품
aws servicecatalog create-product \
  --name "Standard-S3-Bucket" \
  --product-type CLOUD_FORMATION_TEMPLATE \
  --owner "Platform Team" \
  --provisioning-artifact-parameters \
    'Name=v1.0,Info={LoadTemplateFromURL=https://s3.amazonaws.com/templates/s3-standard.yaml},Type=CLOUD_FORMATION_TEMPLATE' \
  --region ap-northeast-2

# 2-2. RDS 인스턴스 제품
aws servicecatalog create-product \
  --name "Standard-RDS-PostgreSQL" \
  --product-type CLOUD_FORMATION_TEMPLATE \
  --owner "Platform Team" \
  --provisioning-artifact-parameters \
    'Name=v1.0,Info={LoadTemplateFromURL=https://s3.amazonaws.com/templates/rds-postgresql.yaml},Type=CLOUD_FORMATION_TEMPLATE' \
  --region ap-northeast-2

# 3. 제품을 포트폴리오에 추가
aws servicecatalog associate-product-with-portfolio \
  --product-id "prod-s3abc" \
  --portfolio-id "port-dev123" \
  --region ap-northeast-2

aws servicecatalog associate-product-with-portfolio \
  --product-id "prod-rdsabc" \
  --portfolio-id "port-dev123" \
  --region ap-northeast-2

# 4. Launch Constraint 설정
aws servicecatalog create-constraint \
  --portfolio-id "port-dev123" \
  --product-id "prod-s3abc" \
  --type LAUNCH \
  --parameters '{"RoleArn":"arn:aws:iam::123456789012:role/SCLaunchRole"}' \
  --region ap-northeast-2

# 5. 개발자 역할에 접근 권한 부여
aws servicecatalog associate-principal-with-portfolio \
  --portfolio-id "port-dev123" \
  --principal-arn "arn:aws:iam::123456789012:role/DeveloperRole" \
  --principal-type IAM_PATTERN \
  --region ap-northeast-2
```

### 제품 프로비저닝 (사용자 관점)

```bash
# 사용 가능한 제품 검색
aws servicecatalog search-products \
  --query 'ProductViewSummaries[*].{Id:ProductId,Name:Name,Description:ShortDescription}' \
  --output table \
  --region ap-northeast-2

# 제품의 프로비저닝 아티팩트(버전) 확인
aws servicecatalog list-provisioning-artifacts \
  --product-id "prod-s3abc" \
  --query 'ProvisioningArtifactDetails[*].{Id:Id,Name:Name,Active:Active}' \
  --output table \
  --region ap-northeast-2

# 제품 프로비저닝
aws servicecatalog provision-product \
  --product-id "prod-s3abc" \
  --provisioning-artifact-id "pa-v1abc" \
  --provisioned-product-name "my-data-bucket" \
  --provisioning-parameters \
    Key=BucketNameSuffix,Value=ml-training-data \
    Key=Environment,Value=dev \
  --region ap-northeast-2

# 프로비저닝 상태 확인
aws servicecatalog describe-provisioned-product \
  --id "pp-abc123" \
  --query 'ProvisionedProductDetail.{Name:Name,Status:Status,Type:Type,Outputs:Outputs}' \
  --output json \
  --region ap-northeast-2

# 내가 프로비저닝한 제품 목록 조회
aws servicecatalog search-provisioned-products \
  --access-level-filter Key=Account,Value=self \
  --query 'ProvisionedProducts[*].{Name:Name,Status:Status,Id:Id,Product:ProductId}' \
  --output table \
  --region ap-northeast-2
```

### 제품 버전 관리

```bash
# 새 버전(Provisioning Artifact) 추가
aws servicecatalog create-provisioning-artifact \
  --product-id "prod-s3abc" \
  --parameters \
    'Name=v2.0,Description=Added lifecycle policy,Info={LoadTemplateFromURL=https://s3.amazonaws.com/templates/s3-standard-v2.yaml},Type=CLOUD_FORMATION_TEMPLATE' \
  --region ap-northeast-2

# 이전 버전 비활성화
aws servicecatalog update-provisioning-artifact \
  --product-id "prod-s3abc" \
  --provisioning-artifact-id "pa-v1abc" \
  --active false \
  --region ap-northeast-2
```

## 모범 사례/보안

### 카탈로그 설계 모범 사례

1. **팀/부서별 포트폴리오를 구성하십시오.** 각 팀이 필요한 제품만 볼 수 있도록 포트폴리오를 분리합니다.

2. **제품의 버전 관리를 체계적으로 하십시오.** 모든 변경은 새 버전으로 등록하고, 안정성이 확인된 후 이전 버전을 비활성화합니다.

3. **파라미터를 최소화하십시오.** 사용자가 선택해야 하는 파라미터를 줄이고, 가능한 한 기본값을 사전에 설정하십시오.

4. **Template Constraint를 적극 활용하십시오.** 인스턴스 유형, 스토리지 크기 등을 제한하여 비용을 통제합니다.

### 보안 모범 사례

- Launch Constraint 역할에 최소 권한 원칙을 적용하십시오. 제품이 생성하는 리소스에 필요한 권한만 부여합니다.
- 사용자에게는 `servicecatalog:*` 권한만 부여하고, 직접적인 AWS 리소스 생성 권한은 부여하지 마십시오.
- SNS Notification Constraint를 설정하여 프로비저닝 이벤트를 감사하십시오.
- 정기적으로 프로비저닝된 제품을 검토하여 미사용 리소스를 정리하십시오.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "servicecatalog:SearchProducts",
        "servicecatalog:DescribeProduct",
        "servicecatalog:ListProvisioningArtifacts",
        "servicecatalog:DescribeProvisioningParameters",
        "servicecatalog:ProvisionProduct",
        "servicecatalog:DescribeProvisionedProduct",
        "servicecatalog:SearchProvisionedProducts",
        "servicecatalog:TerminateProvisionedProduct",
        "servicecatalog:UpdateProvisionedProduct"
      ],
      "Resource": "*"
    }
  ]
}
```

### 비용 통제

- Template Constraint로 허용되는 인스턴스 유형을 제한하십시오.
- Budgets와 연동하여 프로비저닝된 리소스의 비용을 추적하십시오.
- TagOption을 활용하여 모든 리소스에 CostCenter 태그를 자동으로 적용하십시오.

## 관련 서비스 비교

### Service Catalog vs CloudFormation 직접 사용

| 항목 | Service Catalog | CloudFormation 직접 사용 |
|------|----------------|------------------------|
| 거버넌스 | 승인된 템플릿만 사용 | 어떤 템플릿이든 사용 가능 |
| 사용자 권한 | 최소 권한 (SC 권한만) | 리소스 생성 권한 필요 |
| 버전 관리 | 제품 버전으로 체계적 관리 | 별도 관리 필요 |
| 셀프서비스 | 카탈로그 UI 제공 | 콘솔/CLI 직접 사용 |
| 비용 | 추가 비용 없음 | 추가 비용 없음 |
| 추적 | 프로비저닝 이력 자동 기록 | CloudTrail로 추적 |

### Service Catalog vs Control Tower Account Factory

Control Tower의 Account Factory는 Service Catalog를 기반으로 구현된 특수한 사례입니다. Account Factory는 AWS 계정 프로비저닝에 특화되어 있고, Service Catalog는 범용적인 인프라 프로비저닝에 사용됩니다.

### Service Catalog와 함께 사용하면 좋은 서비스

- **AWS Config**: 프로비저닝된 리소스의 규정 준수를 지속 모니터링합니다.
- **AWS Budgets**: 리소스 비용을 추적하고 알림을 설정합니다.
- **AWS Organizations**: 조직 전체에 포트폴리오를 공유합니다.
- **AWS SSO**: 사용자별 적절한 포트폴리오 접근을 관리합니다.

## 요약

AWS Service Catalog는 승인된 인프라를 셀프서비스 방식으로 제공하는 거버넌스 서비스입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **포트폴리오**: 제품을 논리적으로 그룹화하고, 팀/부서별 접근을 제어합니다.
- **제품**: CloudFormation 또는 Terraform 기반의 프로비저닝 가능한 인프라 템플릿입니다.
- **제약 조건**: Launch Constraint(실행 역할), Template Constraint(파라미터 제한) 등으로 거버넌스를 강화합니다.
- **Launch Constraint**: 사용자에게 최소 권한만 부여하면서 필요한 리소스를 생성할 수 있게 하는 핵심 메커니즘입니다.
- **포트폴리오 공유**: Organizations 전체 또는 특정 계정/OU와 포트폴리오를 공유할 수 있습니다.
- **Terraform 지원**: CloudFormation 외에 Terraform 구성도 제품으로 등록할 수 있습니다.

Service Catalog는 클라우드 거버넌스와 개발자 생산성 사이의 균형점을 찾아주는 서비스입니다. 조직의 규모가 커질수록 Service Catalog의 가치가 높아지며, 표준화된 인프라 제공 체계의 핵심 구성 요소가 됩니다.