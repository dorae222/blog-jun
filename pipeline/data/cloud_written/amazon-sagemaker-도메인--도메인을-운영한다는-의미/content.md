<!-- infographic-hero -->
![Amazon SageMaker 도메인 -- "도메인을 운영한다"는 의미 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker 도메인 -- "도메인을 운영한다"는 의미 한 장 요약 인포그래픽*

# Amazon SageMaker 도메인 -- "도메인을 운영한다"는 의미

## 개요

Amazon SageMaker를 실무에서 사용하려면 가장 먼저 마주하는 개념이 **SageMaker 도메인(Domain)**입니다. SageMaker Studio, Canvas, RStudio 등 SageMaker의 통합 개발 환경에 접근하려면 반드시 도메인을 생성해야 합니다. 그런데 단순히 "도메인을 만들었다"는 것이 구체적으로 무엇을 의미하는지, 그리고 "도메인을 운영한다"는 것이 어떤 책임을 수반하는지를 명확히 이해하는 분은 많지 않습니다.

SageMaker 도메인은 단순한 접속 포털이 아닙니다. 이것은 **ML 팀의 격리된 작업 환경 전체를 정의하는 단위**입니다. 사용자 인증, IAM 역할, 네트워크 구성, 스토리지 볼륨, 공유 공간, 앱 설정이 모두 도메인 수준에서 관리됩니다. 도메인 하나는 하나의 VPC와 연결되며, 그 안에서 여러 사용자 프로필이 각자의 격리된 실행 환경을 갖습니다.

이 글에서는 SageMaker 도메인의 구조를 해부하고, 도메인을 운영한다는 것이 실제로 어떤 작업들을 의미하는지를 아키텍처, 보안, 비용 관점에서 체계적으로 다룹니다.

## 핵심 기능

### 도메인의 구성 요소

SageMaker 도메인은 다음과 같은 계층 구조로 이루어져 있습니다.

```
SageMaker Domain
+-- Domain Settings (인증 방식, 기본 실행 역할, 보안 그룹)
|   +-- VPC Configuration (서브넷, 보안 그룹)
|   +-- Default User Settings (기본 JupyterServer, KernelGateway 설정)
|
+-- User Profile 1 (개인 작업 환경)
|   +-- Execution Role (IAM 역할)
|   +-- EFS Home Directory (/home/sagemaker-user)
|   +-- Apps (JupyterServer, KernelGateway, TensorBoard, etc.)
|
+-- User Profile 2
|   +-- Execution Role
|   +-- EFS Home Directory
|   +-- Apps
|
+-- Shared Space (팀 공유 작업 환경)
|   +-- Execution Role
|   +-- Shared EFS Directory
|   +-- Shared Apps
|
+-- Amazon EFS (도메인 전체 공유 파일 시스템)
```

### 인증 모드

SageMaker 도메인은 두 가지 인증 방식을 지원합니다.

| 인증 모드 | 설명 | 적합한 환경 |
|-----------|------|------------|
| IAM | AWS IAM을 통한 인증 | 소규모 팀, AWS 계정 직접 관리 |
| IAM Identity Center (SSO) | 기업 IdP와 통합된 SSO 인증 | 대규모 조직, 중앙 집중 사용자 관리 |

IAM 모드에서는 각 사용자가 AWS IAM 사용자 또는 역할로 인증하며, IAM Identity Center 모드에서는 Okta, Azure AD 등 기업 IdP와 연동하여 Single Sign-On을 구현합니다.

### 도메인 생성

```bash
# SageMaker 도메인 생성 (IAM 인증 모드)
aws sagemaker create-domain \
  --domain-name "ml-team-domain" \
  --auth-mode IAM \
  --default-user-settings '{
    "ExecutionRole": "arn:aws:iam::123456789012:role/SageMakerDefaultRole",
    "SecurityGroups": ["sg-0abc123def456"],
    "JupyterServerAppSettings": {
      "DefaultResourceSpec": {
        "InstanceType": "system",
        "SageMakerImageArn": "arn:aws:sagemaker:ap-northeast-2:123456789012:image/jupyter-server-3"
      }
    },
    "KernelGatewayAppSettings": {
      "DefaultResourceSpec": {
        "InstanceType": "ml.t3.medium",
        "SageMakerImageArn": "arn:aws:sagemaker:ap-northeast-2:123456789012:image/datascience-3.0"
      }
    }
  }' \
  --subnet-ids "subnet-0abc123" "subnet-0def456" \
  --vpc-id "vpc-0abc123456" \
  --region ap-northeast-2

# 도메인 상태 확인
aws sagemaker describe-domain \
  --domain-id "d-abcdefghij" \
  --region ap-northeast-2
```

### 사용자 프로필 관리

사용자 프로필은 도메인 내에서 개별 사용자의 작업 환경을 정의합니다. 각 프로필은 독립된 EFS 홈 디렉토리와 실행 역할을 가집니다.

```bash
# 사용자 프로필 생성
aws sagemaker create-user-profile \
  --domain-id "d-abcdefghij" \
  --user-profile-name "data-scientist-kim" \
  --user-settings '{
    "ExecutionRole": "arn:aws:iam::123456789012:role/SageMakerDataScientistRole",
    "JupyterServerAppSettings": {
      "DefaultResourceSpec": {
        "InstanceType": "system"
      }
    },
    "KernelGatewayAppSettings": {
      "DefaultResourceSpec": {
        "InstanceType": "ml.m5.large"
      },
      "CustomImages": [{
        "ImageName": "custom-ds-image",
        "ImageVersionNumber": 1,
        "AppImageConfigName": "custom-ds-config"
      }]
    }
  }' \
  --region ap-northeast-2

# 사용자 프로필 목록 조회
aws sagemaker list-user-profiles \
  --domain-id "d-abcdefghij" \
  --region ap-northeast-2

# 사용자의 Presigned URL 생성 (Studio 접속 링크)
aws sagemaker create-presigned-domain-url \
  --domain-id "d-abcdefghij" \
  --user-profile-name "data-scientist-kim" \
  --session-expiration-duration-in-seconds 43200 \
  --region ap-northeast-2
```

### 공유 공간 (Shared Spaces)

팀원들이 동일한 노트북과 데이터에서 협업할 수 있는 공유 공간을 생성할 수 있습니다.

```bash
# 공유 공간 생성
aws sagemaker create-space \
  --domain-id "d-abcdefghij" \
  --space-name "team-collaboration" \
  --space-settings '{
    "JupyterServerAppSettings": {
      "DefaultResourceSpec": {
        "InstanceType": "system"
      }
    },
    "KernelGatewayAppSettings": {
      "DefaultResourceSpec": {
        "InstanceType": "ml.m5.xlarge"
      }
    }
  }' \
  --ownership-settings '{
    "OwnerUserProfileName": "data-scientist-kim"
  }' \
  --space-sharing-settings '{
    "SharingType": "Shared"
  }' \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### 네트워크 아키텍처

SageMaker 도메인의 네트워크 구성은 크게 두 가지 모드로 나뉩니다.

```
[PublicInternetOnly 모드]
+------------------------------------------------------+
|  VPC                                                 |
|  +------------------+  +------------------+          |
|  | Private Subnet 1 |  | Private Subnet 2 |          |
|  |                  |  |                  |          |
|  | ENI (SageMaker)  |  | ENI (SageMaker)  |          |
|  +--------+---------+  +--------+---------+          |
|           |                     |                    |
|           +----------+----------+                    |
|                      |                               |
+----------------------+-------------------------------+
                       |
               NAT Gateway / IGW
                       |
                   Internet
                       |
              SageMaker API / S3 / ECR

[VPCOnly 모드 - 권장]
+------------------------------------------------------+
|  VPC                                                 |
|  +------------------+  +------------------+          |
|  | Private Subnet 1 |  | Private Subnet 2 |          |
|  |                  |  |                  |          |
|  | ENI (SageMaker)  |  | ENI (SageMaker)  |          |
|  +--------+---------+  +--------+---------+          |
|           |                     |                    |
|           +----------+----------+                    |
|                      |                               |
|  +--VPC Endpoints----+-----------------------------+ |
|  | SageMaker API | SageMaker Runtime | S3 | ECR   | |
|  | STS           | CloudWatch Logs   | KMS        | |
|  +---------------------------------------------------|
+------------------------------------------------------+
```

**VPCOnly 모드**에서는 모든 트래픽이 VPC 내부에서 VPC 엔드포인트를 통해 AWS 서비스에 접근합니다. 인터넷 게이트웨이가 필요 없으므로 보안 수준이 높아집니다. 다만, 필요한 VPC 엔드포인트를 모두 생성해야 합니다.

### EFS 파일 시스템

도메인을 생성하면 자동으로 Amazon EFS(Elastic File System)가 프로비저닝됩니다. 이 EFS는 다음과 같은 역할을 합니다.

- **사용자별 홈 디렉토리**: 각 사용자 프로필은 EFS 내에 격리된 홈 디렉토리(/home/sagemaker-user)를 갖습니다.
- **영구 저장소**: Studio 앱이 종료되어도 파일이 보존됩니다.
- **공유 가능**: 공유 공간을 통해 팀원 간 파일 공유가 가능합니다.

EFS 볼륨 크기는 자동으로 확장되며, 저장된 데이터 양에 따라 과금됩니다. 대용량 데이터셋은 S3에 저장하고 EFS에는 코드와 설정 파일만 두는 것이 비용 최적화에 유리합니다.

### 도메인 수준의 설정 상속

```
Domain Default Settings
        |
        v
User Profile Settings (도메인 설정을 상속하되 개별 재정의 가능)
        |
        v
App Settings (사용자 설정을 상속)
```

도메인 수준에서 설정한 기본값은 모든 사용자 프로필에 상속됩니다. 개별 사용자 프로필에서 이를 재정의(Override)할 수 있습니다. 이 계층적 설정 구조 덕분에, 도메인 관리자는 전체 팀의 기본 환경을 일괄적으로 관리하면서도 개별 사용자의 특수한 요구사항을 수용할 수 있습니다.

## 실전 활용

### 1. 역할별 사용자 프로필 설계

실무에서는 역할(Role)에 따라 서로 다른 권한과 리소스를 할당하는 것이 일반적입니다.

```python
import boto3

sm = boto3.client('sagemaker', region_name='ap-northeast-2')

# 역할별 사용자 프로필 설정
role_configs = {
    'data-scientist': {
        'execution_role': 'arn:aws:iam::123456789012:role/SageMakerDataScientistRole',
        'instance_type': 'ml.m5.xlarge',
        'description': '모델 개발 및 실험 수행'
    },
    'ml-engineer': {
        'execution_role': 'arn:aws:iam::123456789012:role/SageMakerMLEngineerRole',
        'instance_type': 'ml.m5.2xlarge',
        'description': '모델 최적화 및 배포 파이프라인 구축'
    },
    'data-analyst': {
        'execution_role': 'arn:aws:iam::123456789012:role/SageMakerAnalystRole',
        'instance_type': 'ml.t3.large',
        'description': '데이터 탐색 및 시각화'
    }
}

def create_team_profiles(domain_id, team_members):
    """팀원 목록에 대해 역할별 프로필 생성"""
    for member in team_members:
        config = role_configs[member['role']]
        sm.create_user_profile(
            DomainId=domain_id,
            UserProfileName=member['name'],
            UserSettings={
                'ExecutionRole': config['execution_role'],
                'KernelGatewayAppSettings': {
                    'DefaultResourceSpec': {
                        'InstanceType': config['instance_type']
                    }
                }
            },
            Tags=[{
                'Key': 'Role',
                'Value': member['role']
            }]
        )
        print(f"프로필 생성: {member['name']} ({config['description']})")

# 사용 예시
team = [
    {'name': 'kim-ds', 'role': 'data-scientist'},
    {'name': 'lee-mle', 'role': 'ml-engineer'},
    {'name': 'park-da', 'role': 'data-analyst'}
]
create_team_profiles('d-abcdefghij', team)
```

### 2. 도메인 상태 모니터링 스크립트

```python
import boto3
from datetime import datetime

sm = boto3.client('sagemaker', region_name='ap-northeast-2')

def audit_domain(domain_id):
    """도메인의 현재 상태를 감사합니다."""
    # 도메인 정보 조회
    domain = sm.describe_domain(DomainId=domain_id)
    print(f"도메인: {domain['DomainName']}")
    print(f"상태: {domain['Status']}")
    print(f"인증 모드: {domain['AuthMode']}")
    print(f"VPC: {domain.get('VpcId', 'N/A')}")
    print(f"서브넷: {domain.get('SubnetIds', [])}")
    print("---")

    # 사용자 프로필 목록
    profiles = sm.list_user_profiles(DomainIdEquals=domain_id)
    print(f"사용자 프로필 수: {len(profiles['UserProfiles'])}")

    for profile in profiles['UserProfiles']:
        detail = sm.describe_user_profile(
            DomainId=domain_id,
            UserProfileName=profile['UserProfileName']
        )
        print(f"  - {profile['UserProfileName']}")
        print(f"    상태: {detail['Status']}")
        print(f"    실행 역할: {detail.get('UserSettings', {}).get('ExecutionRole', 'Domain Default')}")

        # 실행 중인 앱 조회
        apps = sm.list_apps(
            DomainIdEquals=domain_id,
            UserProfileNameEquals=profile['UserProfileName']
        )
        running_apps = [a for a in apps['Apps'] if a['Status'] == 'InService']
        if running_apps:
            print(f"    실행 중인 앱: {len(running_apps)}개")
            for app in running_apps:
                print(f"      - {app['AppType']}: {app.get('ResourceSpec', {}).get('InstanceType', 'N/A')}")

audit_domain('d-abcdefghij')
```

### 3. 비용 관리를 위한 유휴 앱 정리

```bash
# 도메인 내 실행 중인 모든 앱 조회
aws sagemaker list-apps \
  --domain-id "d-abcdefghij" \
  --region ap-northeast-2 \
  --query 'Apps[?Status==`InService`].[UserProfileName,AppType,AppName]' \
  --output table

# 특정 사용자의 KernelGateway 앱 종료 (비용 절감)
aws sagemaker delete-app \
  --domain-id "d-abcdefghij" \
  --user-profile-name "data-scientist-kim" \
  --app-type KernelGateway \
  --app-name "datascience-3-0-ml-m5-xlarge-abc123" \
  --region ap-northeast-2
```

## 모범 사례/보안

### VPCOnly 모드 필수 VPC 엔드포인트

VPCOnly 모드를 사용할 때 반드시 생성해야 하는 VPC 엔드포인트 목록입니다.

| VPC 엔드포인트 | 용도 |
|---------------|------|
| com.amazonaws.region.sagemaker.api | SageMaker API 호출 |
| com.amazonaws.region.sagemaker.runtime | 추론 엔드포인트 호출 |
| com.amazonaws.region.sts | IAM 역할 자격 증명 |
| com.amazonaws.region.s3 (Gateway) | S3 데이터 접근 |
| com.amazonaws.region.logs | CloudWatch Logs |
| com.amazonaws.region.ecr.api | ECR 이미지 풀링 |
| com.amazonaws.region.ecr.dkr | ECR 이미지 풀링 |

### 실행 역할 최소 권한 설계

역할별로 필요한 최소 권한만 부여하는 것이 중요합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DataScientistS3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::ml-team-data-bucket",
        "arn:aws:s3:::ml-team-data-bucket/*"
      ]
    },
    {
      "Sid": "SageMakerTrainingOnly",
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateTrainingJob",
        "sagemaker:DescribeTrainingJob",
        "sagemaker:StopTrainingJob"
      ],
      "Resource": "arn:aws:sagemaker:ap-northeast-2:123456789012:training-job/*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "ap-northeast-2"
        }
      }
    },
    {
      "Sid": "DenyExpensiveInstances",
      "Effect": "Deny",
      "Action": "sagemaker:CreateTrainingJob",
      "Resource": "*",
      "Condition": {
        "ForAnyValue:StringLike": {
          "sagemaker:InstanceTypes": [
            "ml.p4d.*",
            "ml.p5.*"
          ]
        }
      }
    }
  ]
}
```

### 도메인 운영 체크리스트

도메인을 운영한다는 것은 다음 작업들을 주기적으로 수행한다는 것을 의미합니다.

1. **사용자 프로필 라이프사이클 관리**: 퇴사자 프로필 비활성화, 신규 팀원 프로필 생성
2. **실행 중인 앱 모니터링**: 유휴 상태의 인스턴스를 정기적으로 종료하여 비용 절감
3. **EFS 용량 모니터링**: 불필요한 데이터 정리, 대용량 데이터는 S3로 이관
4. **IAM 역할 감사**: 불필요한 권한 제거, 조건 키를 활용한 세밀한 권한 제어
5. **보안 그룹 검토**: 인바운드/아웃바운드 규칙의 적절성 확인
6. **SageMaker 이미지 업데이트**: 새로운 프레임워크 버전이 출시되면 커스텀 이미지 갱신
7. **비용 보고서 분석**: AWS Cost Explorer에서 SageMaker 관련 비용 추이 확인

## 관련 서비스 비교

| 항목 | SageMaker Domain | EMR Studio | Databricks Workspace | Google Vertex AI Workbench |
|------|-----------------|------------|---------------------|---------------------------|
| 주요 용도 | ML 개발/배포 통합 환경 | Spark/Hive 분석 환경 | 통합 데이터/AI 플랫폼 | ML 개발 환경 |
| 사용자 관리 | 프로필 기반 | IAM/SSO | SCIM 기반 | IAM 기반 |
| 노트북 | JupyterLab (Studio) | Jupyter | Databricks Notebook | JupyterLab |
| 협업 기능 | Shared Spaces | EMR 노트북 공유 | 실시간 공동 편집 | 공유 인스턴스 |
| 스토리지 | EFS (자동 프로비저닝) | EMRFS / S3 | DBFS / Unity Catalog | GCS |
| 네트워크 격리 | VPCOnly 모드 | VPC | VPC / PrivateLink | VPC Service Controls |
| 과금 | 인스턴스 + EFS + 기타 | 클러스터 시간 | DBU (Databricks Unit) | 인스턴스 시간 |

## 요약

SageMaker 도메인은 ML 팀의 작업 환경을 정의하고 관리하는 핵심 단위입니다. "도메인을 운영한다"는 것은 단순히 도메인을 만드는 것을 넘어, 다음과 같은 지속적인 관리 활동을 의미합니다.

- **도메인은 VPC, 인증, IAM, 스토리지를 아우르는 통합 환경 단위**이며, 팀의 모든 ML 활동이 이 도메인 내에서 이루어집니다.
- **사용자 프로필**을 통해 팀원별 격리된 환경과 역할별 권한을 부여할 수 있으며, 도메인 수준의 기본 설정을 상속하면서도 개별 재정의가 가능합니다.
- **VPCOnly 모드**를 사용하면 모든 트래픽이 VPC 내부에서 처리되어 보안을 강화할 수 있지만, 필요한 VPC 엔드포인트를 누락 없이 생성해야 합니다.
- **비용 관리**의 핵심은 유휴 앱(커널 인스턴스) 정리와 EFS 용량 모니터링이며, 자동화 스크립트를 통해 주기적으로 수행하는 것을 권장합니다.
- 도메인 관리자는 사용자 라이프사이클, 권한 감사, 보안 설정, 비용 최적화를 지속적으로 수행해야 합니다.