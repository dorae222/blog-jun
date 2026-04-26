<!-- infographic-hero -->
![AWS Elastic Beanstalk 개요 핵심 요약](figures/infographic.svg)

*Figure: AWS Elastic Beanstalk 개요 한 장 요약 인포그래픽*

## 개요

AWS Elastic Beanstalk는 웹 애플리케이션과 서비스를 간편하게 배포, 관리, 확장할 수 있는 완전관리형 PaaS(Platform as a Service) 서비스입니다. 개발자가 코드를 업로드하면 Elastic Beanstalk가 자동으로 용량 프로비저닝, 로드 밸런싱, Auto Scaling, 애플리케이션 상태 모니터링을 처리합니다.

Elastic Beanstalk의 가장 큰 장점은 인프라 관리의 복잡성을 추상화하면서도, 기반 AWS 리소스에 대한 완전한 제어권을 유지할 수 있다는 점입니다. EC2 인스턴스, RDS 데이터베이스, ELB 로드 밸런서 등 Elastic Beanstalk가 생성하는 모든 리소스에 직접 접근할 수 있으며, 필요에 따라 수동으로 구성을 변경할 수도 있습니다.

지원하는 플랫폼은 매우 다양합니다.

- Java (Tomcat, Corretto)
- .NET (Windows Server, Linux)
- Node.js
- Python
- Ruby
- PHP
- Go
- Docker (Single Container, Multi Container, ECS Managed)

Elastic Beanstalk 자체에는 추가 비용이 없으며, 실제로 사용하는 AWS 리소스(EC2, ELB, RDS 등)에 대해서만 요금이 부과됩니다.

## 핵심 기능

### 환경 유형

Elastic Beanstalk는 두 가지 환경 유형을 제공합니다.

**웹 서버 환경 (Web Server Environment)**: HTTP/HTTPS 요청을 처리하는 웹 애플리케이션에 적합합니다. ELB + Auto Scaling 그룹 + EC2 인스턴스로 구성됩니다.

**워커 환경 (Worker Environment)**: 백그라운드 작업이나 장시간 실행 작업에 적합합니다. SQS 대기열에서 메시지를 가져와 처리하는 구조입니다.

```bash
# EB CLI 설치
pip install awsebcli

# 프로젝트 초기화
eb init my-web-app \
  --platform python-3.11 \
  --region ap-northeast-2

# 웹 서버 환경 생성
eb create production-env \
  --instance-type t3.medium \
  --scale 2 \
  --elb-type application \
  --envvars DATABASE_URL=postgresql://... \
  --tags Project=MyApp,Environment=Production

# 워커 환경 생성
eb create worker-env \
  --tier worker \
  --instance-type t3.small \
  --scale 1
```

AWS CLI로도 환경을 생성할 수 있습니다.

```bash
# 애플리케이션 생성
aws elasticbeanstalk create-application \
  --application-name my-web-app \
  --description "My Web Application"

# 환경 생성
aws elasticbeanstalk create-environment \
  --application-name my-web-app \
  --environment-name production-env \
  --solution-stack-name "64bit Amazon Linux 2023 v4.0.0 running Python 3.11" \
  --option-settings '[
    {
      "Namespace": "aws:autoscaling:launchconfiguration",
      "OptionName": "InstanceType",
      "Value": "t3.medium"
    },
    {
      "Namespace": "aws:autoscaling:asg",
      "OptionName": "MinSize",
      "Value": "2"
    },
    {
      "Namespace": "aws:autoscaling:asg",
      "OptionName": "MaxSize",
      "Value": "6"
    },
    {
      "Namespace": "aws:elasticbeanstalk:environment",
      "OptionName": "EnvironmentType",
      "Value": "LoadBalanced"
    }
  ]'

# 환경 상태 확인
aws elasticbeanstalk describe-environments \
  --application-name my-web-app \
  --environment-names production-env

# 사용 가능한 솔루션 스택 목록 조회
aws elasticbeanstalk list-available-solution-stacks \
  --query 'SolutionStacks[?contains(@, `Python`)]'
```

### 배포 전략

Elastic Beanstalk는 다양한 배포 전략을 지원합니다.

**All at once**: 모든 인스턴스를 동시에 업데이트합니다. 가장 빠르지만 다운타임이 발생합니다.

**Rolling**: 배치 단위로 순차적으로 업데이트합니다. 일부 인스턴스가 항상 서비스를 유지합니다.

**Rolling with additional batch**: 새 인스턴스를 추가한 후 순차적으로 업데이트합니다. 전체 용량을 유지하면서 배포합니다.

**Immutable**: 완전히 새로운 인스턴스 세트를 생성한 후 트래픽을 전환합니다. 가장 안전하지만 비용이 많이 듭니다.

**Traffic splitting**: Canary 배포처럼 트래픽의 일부만 새 버전으로 전송하여 테스트합니다.

**Blue/Green**: 새로운 환경을 별도로 생성한 후 CNAME을 스왑합니다.

```bash
# Rolling 배포 설정
aws elasticbeanstalk update-environment \
  --environment-name production-env \
  --option-settings '[
    {
      "Namespace": "aws:elasticbeanstalk:command",
      "OptionName": "DeploymentPolicy",
      "Value": "Rolling"
    },
    {
      "Namespace": "aws:elasticbeanstalk:command",
      "OptionName": "BatchSizeType",
      "Value": "Percentage"
    },
    {
      "Namespace": "aws:elasticbeanstalk:command",
      "OptionName": "BatchSize",
      "Value": "25"
    }
  ]'

# Blue/Green 배포 - CNAME 스왑
aws elasticbeanstalk swap-environment-cnames \
  --source-environment-name production-blue \
  --destination-environment-name production-green
```

### .ebextensions를 활용한 커스터마이징

.ebextensions 디렉토리에 YAML 또는 JSON 설정 파일을 추가하여 환경을 커스터마이징할 수 있습니다.

```yaml
# .ebextensions/01-packages.config
packages:
  yum:
    postgresql-devel: []
    gcc: []

container_commands:
  01_migrate:
    command: "python manage.py migrate --noop"
    leader_only: true
  02_collectstatic:
    command: "python manage.py collectstatic --noinput"

option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: config.wsgi:application
  aws:elasticbeanstalk:environment:proxy:staticfiles:
    /static: static
```

```yaml
# .ebextensions/02-alb.config
option_settings:
  aws:elbv2:listener:443:
    Protocol: HTTPS
    SSLCertificateArns: arn:aws:acm:ap-northeast-2:123456789012:certificate/abc-123
    SSLPolicy: ELBSecurityPolicy-TLS13-1-2-2021-06
  aws:elasticbeanstalk:environment:process:default:
    HealthCheckPath: /health/
    MatcherHTTPCode: 200
```

```yaml
# .ebextensions/03-cloudwatch.config
files:
  "/opt/aws/amazon-cloudwatch-agent/etc/config.json":
    mode: "000644"
    owner: root
    group: root
    content: |
      {
        "metrics": {
          "metrics_collected": {
            "mem": {
              "measurement": ["mem_used_percent"]
            },
            "disk": {
              "measurement": ["disk_used_percent"],
              "resources": ["/"]
            }
          }
        }
      }

container_commands:
  start_cloudwatch_agent:
    command: "/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/config.json -s"
```

### Platform Hooks

Elastic Beanstalk는 배포 과정의 특정 시점에 사용자 정의 스크립트를 실행할 수 있는 Platform Hooks를 제공합니다.

- `prebuild/`: 애플리케이션 빌드 전
- `predeploy/`: 애플리케이션 배포 전
- `postdeploy/`: 애플리케이션 배포 후

### Saved Configurations

환경 구성을 저장하고 다른 환경에 적용할 수 있습니다.

```bash
# 현재 환경 설정 저장
aws elasticbeanstalk create-configuration-template \
  --application-name my-web-app \
  --template-name production-config \
  --environment-id e-abc123def4

# 저장된 설정으로 새 환경 생성
aws elasticbeanstalk create-environment \
  --application-name my-web-app \
  --environment-name staging-env \
  --template-name production-config
```

## 아키텍처/동작 원리

### 웹 서버 환경 아키텍처

웹 서버 환경은 다음과 같은 구성 요소로 이루어집니다.

1. **Application Load Balancer (ALB)**: 들어오는 HTTP/HTTPS 트래픽을 여러 인스턴스에 분배합니다.
2. **Auto Scaling Group**: 트래픽 변화에 따라 인스턴스 수를 자동으로 조절합니다.
3. **EC2 인스턴스**: 애플리케이션이 실행되는 서버입니다. 호스트 매니저(Host Manager)가 각 인스턴스에서 실행되어 배포, 로그 수집, 상태 보고를 담당합니다.
4. **Security Groups**: ALB와 EC2 인스턴스 간의 네트워크 접근을 제어합니다.

### 배포 프로세스

1. 사용자가 소스 번들(ZIP/WAR)을 S3에 업로드합니다.
2. Elastic Beanstalk가 애플리케이션 버전을 생성합니다.
3. 배포 정책에 따라 각 인스턴스에서 다음 작업이 수행됩니다.
   - 기존 애플리케이션 중지
   - 새 소스 번들 다운로드 및 압축 해제
   - Platform Hooks 실행
   - 새 애플리케이션 시작
   - 헬스 체크 통과 확인

### 상태 모니터링

Elastic Beanstalk는 기본(Basic)과 향상된(Enhanced) 두 가지 상태 모니터링을 제공합니다. Enhanced Health는 인스턴스 수준의 상세한 상태 정보를 제공하며, 요청 지연 시간, 5xx 오류 비율, CPU 사용률 등 다양한 메트릭을 보여줍니다.

## 실전 활용

### Django 애플리케이션 배포

Django 프로젝트를 Elastic Beanstalk에 배포하는 전체 과정입니다.

```bash
# 프로젝트 구조
# myproject/
# +-- .ebextensions/
# |   +-- 01-django.config
# +-- .platform/
# |   +-- nginx/
# |       +-- conf.d/
# |           +-- proxy.conf
# +-- config/
# |   +-- settings/
# |       +-- base.py
# |       +-- production.py
# +-- requirements.txt
# +-- manage.py

# EB CLI로 초기화 및 배포
eb init my-django-app --platform python-3.11 --region ap-northeast-2
eb create production --instance-type t3.medium --scale 2

# 환경 변수 설정
aws elasticbeanstalk update-environment \
  --environment-name production \
  --option-settings '[
    {
      "Namespace": "aws:elasticbeanstalk:application:environment",
      "OptionName": "DJANGO_SETTINGS_MODULE",
      "Value": "config.settings.production"
    },
    {
      "Namespace": "aws:elasticbeanstalk:application:environment",
      "OptionName": "SECRET_KEY",
      "Value": "your-secret-key-here"
    },
    {
      "Namespace": "aws:elasticbeanstalk:application:environment",
      "OptionName": "DATABASE_URL",
      "Value": "postgresql://user:pass@rds-endpoint:5432/dbname"
    }
  ]'

# 배포
eb deploy production
```

### Docker 기반 배포

Dockerfile을 사용한 배포도 지원합니다.

```bash
# Dockerrun.aws.json (ECS Managed Docker Platform)
# 또는 단순히 Dockerfile을 프로젝트 루트에 배치

# Docker 플랫폼으로 환경 생성
aws elasticbeanstalk create-environment \
  --application-name my-docker-app \
  --environment-name docker-env \
  --solution-stack-name "64bit Amazon Linux 2023 v4.3.0 running Docker" \
  --option-settings '[
    {
      "Namespace": "aws:autoscaling:launchconfiguration",
      "OptionName": "InstanceType",
      "Value": "t3.medium"
    }
  ]'
```

### RDS 연동

Elastic Beanstalk 환경 내부에 RDS를 생성할 수 있지만, 환경 삭제 시 RDS도 함께 삭제되므로 프로덕션에서는 외부 RDS를 사용하는 것을 강력히 권장합니다.

```bash
# 외부 RDS 보안 그룹 설정 - EB 환경의 보안 그룹에서 RDS 접근 허용
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds-security-group \
  --protocol tcp \
  --port 5432 \
  --source-group sg-eb-instance-security-group
```

### 로그 관리

```bash
# 최근 로그 조회
aws elasticbeanstalk request-environment-info \
  --environment-name production-env \
  --info-type tail

# 잠시 대기 후 로그 검색
aws elasticbeanstalk retrieve-environment-info \
  --environment-name production-env \
  --info-type tail

# 전체 로그 번들 요청
aws elasticbeanstalk request-environment-info \
  --environment-name production-env \
  --info-type bundle
```

## 모범 사례/보안

### 보안 모범 사례

1. **HTTPS 설정**: ALB에 ACM 인증서를 연결하고, HTTP에서 HTTPS로의 리다이렉트를 설정합니다.
2. **보안 그룹 제한**: 불필요한 포트를 열지 않고, ALB에서만 인스턴스에 접근할 수 있도록 설정합니다.
3. **환경 변수로 시크릿 관리**: 데이터베이스 비밀번호 등 민감한 정보는 코드에 하드코딩하지 않고, 환경 변수 또는 Secrets Manager를 통해 관리합니다.
4. **IMDSv2 강제 적용**: 인스턴스 메타데이터 서비스 v2를 강제 적용하여 SSRF 공격을 방지합니다.

```yaml
# .ebextensions/security.config
option_settings:
  aws:autoscaling:launchconfiguration:
    DisableIMDSv1: true
```

5. **VPC 내 배포**: Elastic Beanstalk 환경을 VPC 내 프라이빗 서브넷에 배포하고, ALB만 퍼블릭 서브넷에 배치합니다.

### 운영 모범 사례

1. **Immutable 배포 사용**: 프로덕션 환경에서는 Immutable 또는 Blue/Green 배포 전략을 사용하여 롤백을 용이하게 합니다.
2. **Managed Platform Updates**: 관리형 플랫폼 업데이트를 활성화하여 보안 패치를 자동으로 적용합니다.
3. **Enhanced Health Reporting**: 향상된 상태 보고를 활성화하여 애플리케이션의 상세한 상태를 모니터링합니다.
4. **환경 복제**: 프로덕션 환경을 복제하여 스테이징 환경을 구성합니다.

```bash
# 환경 복제
aws elasticbeanstalk create-environment \
  --application-name my-web-app \
  --environment-name staging-env \
  --template-name production-config

# 관리형 플랫폼 업데이트 설정
aws elasticbeanstalk update-environment \
  --environment-name production-env \
  --option-settings '[
    {
      "Namespace": "aws:elasticbeanstalk:managedactions",
      "OptionName": "ManagedActionsEnabled",
      "Value": "true"
    },
    {
      "Namespace": "aws:elasticbeanstalk:managedactions",
      "OptionName": "PreferredStartTime",
      "Value": "Sun:02:00"
    },
    {
      "Namespace": "aws:elasticbeanstalk:managedactions:platformupdate",
      "OptionName": "UpdateLevel",
      "Value": "minor"
    }
  ]'
```

## 관련 서비스 비교

### Elastic Beanstalk vs ECS/EKS

| 항목 | Elastic Beanstalk | ECS/EKS |
|------|-------------------|--------|
| 추상화 수준 | 높음 (PaaS) | 중간 (컨테이너 오케스트레이션) |
| 학습 곡선 | 낮음 | 높음 (특히 EKS) |
| 유연성 | 중간 | 높음 |
| 마이크로서비스 | 제한적 | 최적 |
| 비용 | AWS 리소스 비용만 | AWS 리소스 + (EKS 관리 비용) |
| 적합한 케이스 | 단일 애플리케이션, 빠른 시작 | 복잡한 마이크로서비스 아키텍처 |

### Elastic Beanstalk vs AWS App Runner

App Runner는 Elastic Beanstalk보다 더 높은 수준의 추상화를 제공합니다. 컨테이너 이미지 또는 소스 코드 리포지토리를 지정하면 나머지를 모두 자동으로 처리합니다. 다만, Elastic Beanstalk에 비해 커스터마이징 옵션이 제한적이며, .ebextensions와 같은 세밀한 환경 제어가 어렵습니다.

### Elastic Beanstalk vs Lightsail

Lightsail은 단순한 웹사이트나 블로그에 적합한 VPS 서비스입니다. 고정 월 요금이 부과되며 설정이 간단합니다. 하지만 Auto Scaling, 로드 밸런싱 등 엔터프라이즈 기능이 제한적이므로, 트래픽이 변동하는 실제 서비스에는 Elastic Beanstalk가 더 적합합니다.

## 요약

AWS Elastic Beanstalk는 웹 애플리케이션 배포의 복잡성을 크게 줄여주는 PaaS 서비스입니다. Java, Python, Node.js, Docker 등 다양한 플랫폼을 지원하며, 코드를 업로드하면 로드 밸런싱, Auto Scaling, 모니터링 등을 자동으로 구성합니다.

.ebextensions와 Platform Hooks를 통한 세밀한 커스터마이징, Rolling/Immutable/Blue-Green 등 다양한 배포 전략, Enhanced Health Reporting을 통한 상세 모니터링 등 프로덕션 운영에 필요한 기능을 포괄적으로 제공합니다.

다만, 복잡한 마이크로서비스 아키텍처에는 ECS나 EKS가 더 적합하며, 극도로 단순한 배포에는 App Runner가 더 편리할 수 있습니다. Elastic Beanstalk는 중간 수준의 복잡성을 가진 웹 애플리케이션에 가장 적합한 선택입니다. 프로덕션 환경에서는 외부 RDS 사용, HTTPS 설정, Immutable 배포 전략 적용을 반드시 고려해야 합니다.