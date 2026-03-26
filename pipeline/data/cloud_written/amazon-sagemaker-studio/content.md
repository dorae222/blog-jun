# Amazon SageMaker Studio - 통합 ML 개발 환경 완벽 가이드

## 개요

Amazon SageMaker Studio는 머신러닝 워크플로우의 전체 수명주기를 단일 웹 기반 인터페이스에서 관리할 수 있는 통합 개발 환경(IDE)입니다. 데이터 준비, 모델 훈련, 튜닝, 배포, 모니터링까지 모든 ML 작업을 하나의 환경에서 수행할 수 있어, 다양한 도구와 서비스 간의 컨텍스트 전환을 최소화합니다.

2023년 말 대규모 업데이트를 통해 SageMaker Studio는 JupyterLab 기반의 새로운 경험을 제공하게 되었습니다. 기존의 SageMaker Studio Classic과 구분하여 '신규 SageMaker Studio'로 불리며, Code Editor(VS Code 기반), JupyterLab, 터미널 등 다양한 개발 도구를 통합적으로 제공합니다.

주요 활용 시나리오는 다음과 같습니다.

- 데이터 사이언스 팀의 협업 환경 구축
- 노트북 기반 실험 및 프로토타이핑
- 자동화된 ML 파이프라인 구축 및 모니터링
- 모델 레지스트리를 통한 모델 거버넌스 관리
- Feature Store를 통한 특성 엔지니어링 중앙화

## 핵심 기능

### JupyterLab 기반 IDE

신규 SageMaker Studio는 JupyterLab 4를 기반으로 구축되었습니다. 표준 JupyterLab 확장을 설치할 수 있으며, 터미널 접근, 파일 브라우저, Git 통합 등 익숙한 개발 환경을 제공합니다.

### Code Editor (VS Code 기반)

Code-OSS(Visual Studio Code 오픈소스 버전)를 기반으로 한 Code Editor를 내장하고 있습니다. VS Code 확장 마켓플레이스에서 확장을 설치할 수 있으며, 터미널, 디버거, Git 등 VS Code의 핵심 기능을 모두 사용할 수 있습니다.

### SageMaker Studio Spaces

Spaces는 SageMaker Studio에서 개발 환경을 격리하는 단위입니다. 각 Space는 독립적인 컴퓨팅 인스턴스와 스토리지를 가지며, JupyterLab Space 또는 Code Editor Space를 생성할 수 있습니다.

| 구성 요소 | 설명 |
|-----------|------|
| Domain | Studio 환경의 최상위 단위 (리전당 1개) |
| User Profile | 도메인 내 개별 사용자 설정 |
| Space | 격리된 개발 환경 (인스턴스 + 스토리지) |
| App | Space 내 실행 중인 애플리케이션 |

### 통합 SageMaker 서비스 접근

Studio 인터페이스에서 다음 SageMaker 서비스에 직접 접근할 수 있습니다.

- **SageMaker Experiments**: 실험 추적 및 비교
- **SageMaker Pipelines**: ML 워크플로우 파이프라인 구축
- **Model Registry**: 모델 버전 관리 및 승인 워크플로우
- **Feature Store**: 특성 저장소 관리
- **Data Wrangler**: 시각적 데이터 전처리
- **Ground Truth**: 데이터 라벨링 관리
- **Model Monitor**: 배포된 모델 모니터링

## 아키텍처 및 동작 원리

SageMaker Studio의 아키텍처는 다음과 같은 계층 구조로 이루어져 있습니다.

```
[AWS Account]
    |
    +-- [SageMaker Domain] (리전당 최대 5개)
            |
            +-- [User Profile A]
            |       |
            |       +-- [JupyterLab Space] --> [ml.t3.medium 인스턴스]
            |       |       +-- EBS Volume (5-16384 GB)
            |       |
            |       +-- [Code Editor Space] --> [ml.m5.large 인스턴스]
            |               +-- EBS Volume
            |
            +-- [User Profile B]
            |       |
            |       +-- [JupyterLab Space] --> [ml.g4dn.xlarge 인스턴스]
            |               +-- EBS Volume
            |
            +-- [Shared Space] (팀 공유)
                    +-- [JupyterLab Space] --> [ml.m5.2xlarge 인스턴스]
```

각 Space는 독립적인 EC2 인스턴스 위에서 실행되며, EBS 볼륨이 영구 스토리지로 연결됩니다. Space를 중지하면 인스턴스는 종료되지만 EBS 볼륨의 데이터는 유지됩니다. Space를 다시 시작하면 동일한 EBS 볼륨이 재연결되어 작업을 이어갈 수 있습니다.

### 네트워크 아키텍처

SageMaker Studio Domain은 두 가지 네트워크 모드를 지원합니다.

- **PublicInternetOnly**: 인터넷을 통해 Studio에 접근하며, NAT Gateway를 통해 외부 리소스에 접근합니다.
- **VpcOnly**: VPC 내에서만 Studio에 접근하며, VPC Endpoint를 통해 AWS 서비스에 접근합니다. 보안이 중요한 환경에서 권장됩니다.

## 실전 활용

### AWS CLI를 사용한 Studio Domain 생성

```bash
# VPC 및 서브넷 확인
aws ec2 describe-vpcs --query 'Vpcs[].{ID:VpcId,CIDR:CidrBlock}' --output table
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-0abc123" \
    --query 'Subnets[].{ID:SubnetId,AZ:AvailabilityZone,CIDR:CidrBlock}' --output table

# SageMaker Studio Domain 생성
aws sagemaker create-domain \
    --domain-name ml-team-studio \
    --auth-mode IAM \
    --default-user-settings '{
        "ExecutionRole": "arn:aws:iam::123456789012:role/SageMakerStudioRole",
        "JupyterLabAppSettings": {
            "DefaultResourceSpec": {
                "SageMakerImageArn": "arn:aws:sagemaker:ap-northeast-2:123456789012:image/sagemaker-distribution-cpu",
                "InstanceType": "ml.t3.medium"
            }
        },
        "SecurityGroups": ["sg-0abc123"]
    }' \
    --subnet-ids subnet-0abc123 subnet-0def456 \
    --vpc-id vpc-0abc123 \
    --app-network-access-type VpcOnly

# User Profile 생성
aws sagemaker create-user-profile \
    --domain-id d-abcdefg123 \
    --user-profile-name data-scientist-kim \
    --user-settings '{
        "ExecutionRole": "arn:aws:iam::123456789012:role/SageMakerStudioRole"
    }'

# Space 생성 (JupyterLab)
aws sagemaker create-space \
    --domain-id d-abcdefg123 \
    --space-name experiment-space \
    --space-settings '{
        "JupyterLabAppSettings": {
            "DefaultResourceSpec": {
                "InstanceType": "ml.m5.large",
                "SageMakerImageArn": "arn:aws:sagemaker:ap-northeast-2:123456789012:image/sagemaker-distribution-cpu"
            }
        },
        "SpaceStorageSettings": {
            "EbsStorageSettings": {
                "EbsVolumeSizeInGb": 50
            }
        }
    }' \
    --ownership-settings '{
        "OwnerUserProfileName": "data-scientist-kim"
    }'

# Domain 상태 확인
aws sagemaker describe-domain \
    --domain-id d-abcdefg123 \
    --query '{Status:Status,Url:Url,VpcId:VpcId}'
```

### Presigned URL로 Studio 접근

```bash
# Studio 접속 URL 생성
aws sagemaker create-presigned-domain-url \
    --domain-id d-abcdefg123 \
    --user-profile-name data-scientist-kim \
    --expires-in-seconds 300 \
    --query AuthorizedUrl \
    --output text
```

### Space 관리

```bash
# Space 목록 조회
aws sagemaker list-spaces \
    --domain-id d-abcdefg123 \
    --query 'Spaces[].{Name:SpaceName,Status:Status,Created:CreationTime}' \
    --output table

# Space 중지 (인스턴스 종료, 데이터 유지)
aws sagemaker delete-app \
    --domain-id d-abcdefg123 \
    --space-name experiment-space \
    --app-type JupyterLab \
    --app-name default

# Space 인스턴스 타입 변경
aws sagemaker update-space \
    --domain-id d-abcdefg123 \
    --space-name experiment-space \
    --space-settings '{
        "JupyterLabAppSettings": {
            "DefaultResourceSpec": {
                "InstanceType": "ml.g4dn.xlarge"
            }
        }
    }'
```

### Lifecycle Configuration으로 환경 자동 설정

```bash
# Lifecycle Config 생성 (Space 시작 시 자동 실행)
aws sagemaker create-studio-lifecycle-config \
    --studio-lifecycle-config-name auto-setup \
    --studio-lifecycle-config-content $(echo '#!/bin/bash
set -e
pip install pandas scikit-learn matplotlib seaborn boto3
conda install -y -c conda-forge lightgbm xgboost
echo "환경 설정 완료"' | base64) \
    --studio-lifecycle-config-app-type JupyterLab
```

## 모범 사례 및 보안

### 비용 관리

- 사용하지 않는 Space의 인스턴스를 적극적으로 중지합니다. Lifecycle Configuration에 자동 종료 스크립트를 설정하여 유휴 인스턴스를 자동으로 종료할 수 있습니다.
- 탐색/프로토타이핑 단계에서는 ml.t3.medium 같은 소형 인스턴스를 사용하고, 본격적인 훈련 시에만 대형 인스턴스로 전환합니다.
- EBS 볼륨 크기를 필요한 만큼만 할당합니다. 데이터는 S3에 저장하고 필요할 때 로드하는 패턴을 권장합니다.
- AWS Budgets와 CloudWatch 알람을 설정하여 비용 임계값을 모니터링합니다.

### 보안 강화

- VpcOnly 모드를 사용하여 인터넷 직접 접근을 차단합니다.
- IAM Identity Center(SSO)를 통해 사용자 인증을 관리하고, 도메인별 접근 권한을 세분화합니다.
- S3 데이터 접근에 IAM 역할 기반 권한을 적용하고, KMS 암호화를 활성화합니다.
- VPC Endpoint를 통해 SageMaker API, S3, ECR 등의 AWS 서비스에 프라이빗하게 접근합니다.
- CloudTrail을 활성화하여 Studio 내 모든 API 호출을 기록합니다.

### 팀 협업 전략

- Shared Space를 활용하여 팀 공용 노트북과 코드를 관리합니다.
- Git 연동을 통해 코드 버전 관리와 코드 리뷰 프로세스를 적용합니다.
- SageMaker Experiments를 활용하여 실험 결과를 체계적으로 기록하고 팀원과 공유합니다.
- Model Registry를 통해 모델 승인 워크플로우를 구축하여 프로덕션 배포 전 검증 프로세스를 강화합니다.

## 관련 서비스 비교

| 항목 | SageMaker Studio (신규) | Studio Classic | SageMaker Notebook Instances |
|------|------------------------|----------------|------------------------------|
| 기반 | JupyterLab 4 + Code Editor | 커스텀 JupyterLab 3 | JupyterLab / Jupyter Notebook |
| 인스턴스 관리 | Space 단위 격리 | App 단위 | 인스턴스 1:1 |
| VS Code 지원 | Code Editor 내장 | 미지원 | 미지원 |
| 공유 Space | 지원 | 미지원 | 미지원 |
| 서비스 통합 | 전체 SageMaker 서비스 | 전체 SageMaker 서비스 | 제한적 |
| 시작 시간 | 빠름 (이미지 캐싱) | 느림 | 보통 |
| EBS 영속성 | Space 수준 | 사용자 수준 | 인스턴스 수준 |
| 권장 사항 | 신규 프로젝트 권장 | 마이그레이션 권장 | 단순 노트북 작업 |

## 요약

Amazon SageMaker Studio는 ML 워크플로우의 전체 수명주기를 단일 환경에서 관리할 수 있는 통합 IDE입니다. JupyterLab 4 기반의 노트북 환경과 VS Code 기반의 Code Editor를 제공하며, SageMaker의 모든 서비스(Experiments, Pipelines, Model Registry, Feature Store 등)에 직접 접근할 수 있습니다. Space를 통해 개발 환경을 격리하고, VpcOnly 모드와 IAM 기반 접근 제어로 엔터프라이즈 수준의 보안을 확보할 수 있습니다. 신규 프로젝트에서는 Studio Classic 대신 신규 SageMaker Studio를 사용하는 것을 권장합니다.