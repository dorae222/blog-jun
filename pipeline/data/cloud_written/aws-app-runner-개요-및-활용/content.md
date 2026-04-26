<!-- infographic-hero -->
![AWS App Runner 개요 및 활용 - 컨테이너 애플리케이션 자동 배포 서비스 핵심 요약](figures/infographic.svg)

*Figure: AWS App Runner 개요 및 활용 - 컨테이너 애플리케이션 자동 배포 서비스 한 장 요약 인포그래픽*

# AWS App Runner 개요 및 활용 - 컨테이너 애플리케이션 자동 배포 서비스

## 개요

AWS App Runner는 소스 코드 저장소나 컨테이너 이미지로부터 웹 애플리케이션과 API를 자동으로 빌드, 배포, 스케일링하는 완전관리형 서비스입니다. 인프라 관리, 로드 밸런서 설정, TLS 인증서 프로비저닝, Auto Scaling 구성 등을 AWS가 모두 처리하므로, 개발자는 코드 작성에만 집중할 수 있습니다.

App Runner는 ECS나 EKS 같은 컨테이너 오케스트레이션 서비스와 달리, 클러스터 관리나 태스크 정의 등의 인프라 구성이 필요하지 않습니다. 소스 코드를 GitHub에 푸시하거나 ECR 이미지를 업데이트하면 자동으로 새 버전이 배포됩니다.

주요 특징은 다음과 같습니다.

- 소스 코드(GitHub) 또는 컨테이너 이미지(ECR)에서 직접 배포
- 트래픽 기반 자동 스케일링 (0에서 N까지)
- HTTPS 자동 적용 (TLS 인증서 자동 관리)
- 커스텀 도메인 연결 지원
- VPC Connector를 통한 프라이빗 리소스 접근

## 핵심 기능

### 소스 기반 배포 (Source-based)

GitHub 저장소를 직접 연결하여 소스 코드에서 컨테이너 이미지를 자동 빌드합니다. Python, Node.js, Java, Go, .NET, Ruby, PHP를 지원하며, 각 런타임에 맞는 빌드 환경이 자동으로 구성됩니다.

```yaml
# apprunner.yaml (저장소 루트에 배치)
version: 1.0
runtime: python312
build:
  commands:
    build:
      - pip install -r requirements.txt
run:
  command: gunicorn app:app --bind 0.0.0.0:8080
  network:
    port: 8080
  env:
    - name: ENVIRONMENT
      value: production
```

### 이미지 기반 배포 (Image-based)

Amazon ECR(Public/Private)의 컨테이너 이미지를 직접 배포합니다. 멀티 스테이지 빌드나 커스텀 런타임이 필요한 경우에 적합합니다.

### Auto Scaling 구성

| 파라미터 | 기본값 | 범위 | 설명 |
|---------|--------|------|------|
| MaxConcurrency | 100 | 1-200 | 인스턴스당 최대 동시 요청 수 |
| MaxSize | 25 | 1-200 | 최대 인스턴스 수 |
| MinSize | 1 | 1-25 | 최소 인스턴스 수 |

App Runner는 동시 요청 수를 기준으로 자동 스케일링합니다. 한 인스턴스의 동시 요청이 MaxConcurrency에 도달하면 새 인스턴스가 추가됩니다.

### VPC Connector

VPC Connector를 사용하면 App Runner 서비스가 VPC 내의 프라이빗 리소스(RDS, ElastiCache, 내부 API 등)에 접근할 수 있습니다.

### 배포 전략

| 전략 | 설명 |
|------|------|
| 자동 배포 | 소스 변경 감지 시 자동 배포 (CI/CD) |
| 수동 배포 | 명시적 배포 트리거 필요 |
| 롤링 업데이트 | 무중단 배포 (기본) |
| 롤백 | 이전 버전으로 즉시 복원 |

## 아키텍처 및 동작 원리

App Runner 서비스의 내부 아키텍처는 다음과 같습니다.

```
[GitHub Repository / ECR Image]
          |
          v
[App Runner Service]
    |
    +-- [Build Phase] (소스 기반만)
    |       +-- Docker 이미지 빌드
    |       +-- ECR에 이미지 저장
    |
    +-- [Deploy Phase]
    |       +-- 컨테이너 인스턴스 프로비저닝
    |       +-- Health Check 확인
    |       +-- 트래픽 전환 (롤링)
    |
    +-- [Runtime]
            +-- [Load Balancer] (자동 관리)
            |       +-- HTTPS 종단 (TLS 자동)
            |       +-- 커스텀 도메인
            |
            +-- [Instance 1] -- [Instance 2] -- ... -- [Instance N]
            |       (Auto Scaling: MaxConcurrency 기반)
            |
            +-- [VPC Connector] (선택)
                    +-- RDS / ElastiCache / 내부 API
```

App Runner 서비스는 기본적으로 퍼블릭 엔드포인트를 통해 접근 가능합니다. 내부 전용 서비스가 필요한 경우 Ingress를 Private으로 설정하면 VPC 내에서만 접근할 수 있는 VPC Endpoint가 생성됩니다.

### 콜드 스타트와 Provisioned Instances

MinSize를 1 이상으로 설정하면 항상 실행 중인 인스턴스가 유지되어 콜드 스타트가 방지됩니다. MinSize가 0이면 트래픽이 없을 때 인스턴스가 완전히 종료되어 비용이 절감되지만, 첫 요청 시 콜드 스타트가 발생합니다.

## 실전 활용

### AWS CLI를 사용한 App Runner 서비스 관리

```bash
# ECR 이미지 기반 서비스 생성
aws apprunner create-service \
    --service-name my-api-service \
    --source-configuration '{
        "ImageRepository": {
            "ImageIdentifier": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/my-api:latest",
            "ImageConfiguration": {
                "Port": "8080",
                "RuntimeEnvironmentVariables": {
                    "DATABASE_URL": "postgresql://...",
                    "REDIS_URL": "redis://..."
                }
            },
            "ImageRepositoryType": "ECR"
        },
        "AutoDeploymentsEnabled": true,
        "AuthenticationConfiguration": {
            "AccessRoleArn": "arn:aws:iam::123456789012:role/AppRunnerECRAccessRole"
        }
    }' \
    --instance-configuration '{
        "Cpu": "1024",
        "Memory": "2048",
        "InstanceRoleArn": "arn:aws:iam::123456789012:role/AppRunnerInstanceRole"
    }' \
    --health-check-configuration '{
        "Protocol": "HTTP",
        "Path": "/health",
        "Interval": 10,
        "Timeout": 5,
        "HealthyThreshold": 1,
        "UnhealthyThreshold": 5
    }'

# Auto Scaling 구성 생성
aws apprunner create-auto-scaling-configuration \
    --auto-scaling-configuration-name production-scaling \
    --max-concurrency 100 \
    --min-size 2 \
    --max-size 10

# 서비스 상태 확인
aws apprunner describe-service \
    --service-arn arn:aws:apprunner:ap-northeast-2:123456789012:service/my-api-service/abc123 \
    --query '{Status:Service.Status,URL:Service.ServiceUrl,Created:Service.CreatedAt}'

# VPC Connector 생성
aws apprunner create-vpc-connector \
    --vpc-connector-name my-vpc-connector \
    --subnets subnet-0abc123 subnet-0def456 \
    --security-groups sg-0abc123

# 서비스에 VPC Connector 연결
aws apprunner update-service \
    --service-arn arn:aws:apprunner:ap-northeast-2:123456789012:service/my-api-service/abc123 \
    --network-configuration '{
        "EgressConfiguration": {
            "EgressType": "VPC",
            "VpcConnectorArn": "arn:aws:apprunner:ap-northeast-2:123456789012:vpcconnector/my-vpc-connector/1/abc123"
        }
    }'

# 커스텀 도메인 연결
aws apprunner associate-custom-domain \
    --service-arn arn:aws:apprunner:ap-northeast-2:123456789012:service/my-api-service/abc123 \
    --domain-name api.example.com \
    --enable-www-subdomain

# 수동 배포 트리거
aws apprunner start-deployment \
    --service-arn arn:aws:apprunner:ap-northeast-2:123456789012:service/my-api-service/abc123

# 서비스 목록 조회
aws apprunner list-services \
    --query 'ServiceSummaryList[].{Name:ServiceName,Status:Status,URL:ServiceUrl}' \
    --output table
```

### GitHub 소스 기반 배포

```bash
# GitHub 연결 생성 (콘솔에서 OAuth 인증 필요)
aws apprunner create-connection \
    --connection-name github-connection \
    --provider-type GITHUB

# GitHub 소스 기반 서비스 생성
aws apprunner create-service \
    --service-name my-web-app \
    --source-configuration '{
        "CodeRepository": {
            "RepositoryUrl": "https://github.com/myorg/myapp",
            "SourceCodeVersion": {"Type": "BRANCH", "Value": "main"},
            "CodeConfiguration": {
                "ConfigurationSource": "REPOSITORY"
            }
        },
        "AutoDeploymentsEnabled": true,
        "AuthenticationConfiguration": {
            "ConnectionArn": "arn:aws:apprunner:ap-northeast-2:123456789012:connection/github-connection/abc123"
        }
    }'
```

## 모범 사례 및 보안

### 비용 최적화

- 프로비저닝된 인스턴스(MinSize > 0)는 유휴 시에도 비용이 발생합니다. 개발/스테이징 환경에서는 MinSize=0으로 설정합니다.
- CPU와 Memory는 애플리케이션 프로파일링을 기반으로 적절히 설정합니다. 과도한 리소스 할당은 비용 낭비입니다.
- MaxConcurrency를 높게 설정하면 인스턴스당 더 많은 요청을 처리하여 인스턴스 수를 줄일 수 있습니다.
- 빌드 비용은 빌드 시간에 비례하므로, 이미지 기반 배포가 소스 기반보다 빌드 비용을 절약할 수 있습니다.

### 보안

- Instance Role에 최소 권한을 부여하여 애플리케이션이 접근할 수 있는 AWS 리소스를 제한합니다.
- 환경 변수에 민감한 정보를 직접 저장하지 않고, Secrets Manager나 SSM Parameter Store를 참조합니다.
- VPC Connector를 통해 데이터베이스와 내부 서비스에 프라이빗하게 접근합니다.
- WAF를 연동하여 웹 애플리케이션 방화벽을 적용합니다.
- CloudTrail을 활성화하여 서비스 변경 이력을 감사합니다.

### 운영 전략

- Health Check 경로에 실제 의존성(DB 연결 등)을 확인하는 로직을 포함하여 정확한 상태를 보고합니다.
- 자동 배포를 프로덕션에 바로 적용하기보다, 스테이징 서비스에서 먼저 검증한 후 프로덕션에 수동 배포하는 전략을 권장합니다.
- CloudWatch 로그와 X-Ray 추적을 활성화하여 관측 가능성을 확보합니다.

## 관련 서비스 비교

| 항목 | App Runner | ECS Fargate | Lambda | Elastic Beanstalk |
|------|-----------|-------------|--------|-------------------|
| 인프라 관리 | 전혀 없음 | 태스크/서비스 정의 | 없음 | 환경 설정 |
| 스케일링 | 동시 요청 기반 자동 | 태스크 수 기반 | 자동 | Auto Scaling Group |
| 시작 시간 | 초 단위 (웜) | 분 단위 | 밀리초~초 | 분 단위 |
| 최대 실행 시간 | 무제한 | 무제한 | 15분 | 무제한 |
| 비용 모델 | vCPU/메모리 시간 | vCPU/메모리 시간 | 요청+실행시간 | EC2 인스턴스 |
| 적합한 워크로드 | 웹앱/API | 마이크로서비스 | 이벤트 기반 | 전통적 웹앱 |
| VPC 통합 | VPC Connector | 네이티브 | VPC 설정 | 네이티브 |
| 사용 난이도 | 매우 쉬움 | 보통 | 쉬움 | 보통 |

## 요약

AWS App Runner는 웹 애플리케이션과 API를 가장 간단하게 배포할 수 있는 완전관리형 컨테이너 서비스입니다. 소스 코드 또는 컨테이너 이미지에서 자동으로 빌드하고 배포하며, HTTPS, Auto Scaling, 로드 밸런싱이 기본 제공됩니다. 인프라 관리 부담을 완전히 제거하면서도 VPC Connector를 통해 프라이빗 리소스에 접근할 수 있어, 빠른 프로토타이핑부터 프로덕션 워크로드까지 폭넓게 활용할 수 있습니다.