## 개요

AWS CodeDeploy는 Amazon EC2 인스턴스, AWS Lambda 함수, Amazon ECS 서비스, 온프레미스 서버 등 다양한 컴퓨팅 플랫폼에 애플리케이션을 자동으로 배포하는 완전관리형 배포 서비스입니다.

수동 배포는 휴먼 에러의 원인이 되며, 서버 수가 증가할수록 일관된 배포가 어려워집니다. CodeDeploy는 이러한 문제를 해결하기 위해 표준화된 배포 프로세스, 다양한 배포 전략, 자동 롤백 메커니즘을 제공합니다.

CodeDeploy의 핵심 장점은 다음과 같습니다.

1. **플랫폼 독립성**: EC2, Lambda, ECS, 온프레미스 서버를 하나의 도구로 관리합니다.
2. **다양한 배포 전략**: In-Place, Blue/Green, Canary, Linear 등 비즈니스 요구에 맞는 전략을 선택할 수 있습니다.
3. **자동 롤백**: 배포 실패 시 이전 버전으로 자동 롤백하여 서비스 영향을 최소화합니다.
4. **무중단 배포**: 롤링 또는 Blue/Green 전략으로 다운타임 없이 배포합니다.
5. **무료**: CodeDeploy 자체는 무료이며, 기반 리소스(EC2, Lambda 등)의 비용만 발생합니다.

## 핵심 기능

### 핵심 개념

#### Application (애플리케이션)

CodeDeploy에서 배포를 관리하는 최상위 컨테이너입니다. 하나의 애플리케이션은 하나의 컴퓨팅 플랫폼(EC2/On-Premises, Lambda, ECS)에 매핑됩니다.

```bash
# EC2/On-Premises 애플리케이션 생성
aws deploy create-application \
    --application-name my-web-app \
    --compute-platform Server

# Lambda 애플리케이션 생성
aws deploy create-application \
    --application-name my-lambda-app \
    --compute-platform Lambda

# ECS 애플리케이션 생성
aws deploy create-application \
    --application-name my-ecs-app \
    --compute-platform ECS
```

#### Deployment Group (배포 그룹)

배포 대상 인스턴스/서비스의 집합입니다. EC2의 경우 태그, Auto Scaling 그룹, 또는 둘의 조합으로 대상을 지정합니다.

```bash
# EC2 배포 그룹 생성 (In-Place 배포)
aws deploy create-deployment-group \
    --application-name my-web-app \
    --deployment-group-name production \
    --deployment-config-name CodeDeployDefault.OneAtATime \
    --ec2-tag-filters Key=Environment,Value=Production,Type=KEY_AND_VALUE \
    --service-role-arn arn:aws:iam::123456789012:role/CodeDeployServiceRole \
    --auto-rollback-configuration enabled=true,events=DEPLOYMENT_FAILURE

# Blue/Green 배포 그룹 생성
aws deploy create-deployment-group \
    --application-name my-web-app \
    --deployment-group-name production-bg \
    --deployment-config-name CodeDeployDefault.AllAtOnce \
    --ec2-tag-filters Key=Environment,Value=Production,Type=KEY_AND_VALUE \
    --service-role-arn arn:aws:iam::123456789012:role/CodeDeployServiceRole \
    --auto-scaling-groups my-asg \
    --deployment-style deploymentType=BLUE_GREEN,deploymentOption=WITH_TRAFFIC_CONTROL \
    --blue-green-deployment-configuration '{"terminateBlueInstancesOnDeploymentSuccess": {"action": "TERMINATE", "terminationWaitTimeInMinutes": 60}, "deploymentReadyOption": {"actionOnTimeout": "CONTINUE_DEPLOYMENT", "waitTimeInMinutes": 0}, "greenFleetProvisioningOption": {"action": "COPY_AUTO_SCALING_GROUP"}}' \
    --load-balancer-info '{"targetGroupInfoList": [{"name": "my-target-group"}]}' \
    --auto-rollback-configuration enabled=true,events=DEPLOYMENT_FAILURE
```

#### Revision (리비전)

배포할 애플리케이션의 버전입니다. S3 버킷 또는 GitHub 저장소에서 가져올 수 있습니다.

### AppSpec 파일

AppSpec(Application Specification) 파일은 배포의 핵심 구성 파일로, 배포 대상, 파일 배치, 라이프사이클 훅을 정의합니다.

#### EC2/On-Premises AppSpec (appspec.yml)

```yaml
version: 0.0
os: linux
files:
  - source: /
    destination: /var/www/myapp
    overwrite: true
permissions:
  - object: /var/www/myapp
    owner: www-data
    group: www-data
    mode: "755"
    type:
      - directory
  - object: /var/www/myapp
    owner: www-data
    group: www-data
    mode: "644"
    pattern: "**/*.html"
hooks:
  BeforeInstall:
    - location: scripts/before_install.sh
      timeout: 300
      runas: root
  AfterInstall:
    - location: scripts/after_install.sh
      timeout: 300
      runas: root
  ApplicationStart:
    - location: scripts/start_server.sh
      timeout: 300
      runas: root
  ApplicationStop:
    - location: scripts/stop_server.sh
      timeout: 300
      runas: root
  ValidateService:
    - location: scripts/validate_service.sh
      timeout: 300
      runas: root
```

#### Lambda AppSpec (appspec.yml)

```yaml
version: 0.0
Resources:
  - MyLambdaFunction:
      Type: AWS::Lambda::Function
      Properties:
        Name: my-function
        Alias: live
        CurrentVersion: 1
        TargetVersion: 2
Hooks:
  - BeforeAllowTraffic: CodeDeployHook_BeforeAllowTraffic
  - AfterAllowTraffic: CodeDeployHook_AfterAllowTraffic
```

#### ECS AppSpec (appspec.yml)

```yaml
version: 0.0
Resources:
  - TargetService:
      Type: AWS::ECS::Service
      Properties:
        TaskDefinition: "arn:aws:ecs:ap-northeast-2:123456789012:task-definition/my-task:2"
        LoadBalancerInfo:
          ContainerName: "my-container"
          ContainerPort: 8080
        PlatformVersion: "LATEST"
Hooks:
  - BeforeInstall: "LambdaFunctionToValidateBeforeInstall"
  - AfterInstall: "LambdaFunctionToValidateAfterInstall"
  - AfterAllowTestTraffic: "LambdaFunctionToValidateAfterTestTraffic"
  - BeforeAllowTraffic: "LambdaFunctionToValidateBeforeTraffic"
  - AfterAllowTraffic: "LambdaFunctionToValidateAfterTraffic"
```

### 배포 전략

#### In-Place 배포

기존 인스턴스에서 애플리케이션을 중지하고, 새 버전을 설치한 후 다시 시작합니다. EC2/On-Premises 플랫폼에서만 사용 가능합니다.

| 배포 구성 | 설명 |
|-----------|------|
| CodeDeployDefault.OneAtATime | 한 번에 하나의 인스턴스씩 배포 |
| CodeDeployDefault.HalfAtATime | 절반씩 배포 |
| CodeDeployDefault.AllAtOnce | 모든 인스턴스에 동시 배포 |

#### Blue/Green 배포

새로운 인스턴스 세트(Green)를 프로비저닝하고, 새 버전을 배포한 후 트래픽을 전환합니다. 롤백이 빠르고 안전합니다.

#### Canary 배포 (Lambda/ECS)

트래픽을 단계적으로 새 버전으로 전환합니다.

```bash
# Lambda Canary 배포 구성 생성
aws deploy create-deployment-config \
    --deployment-config-name Canary10Percent5Minutes \
    --compute-platform Lambda \
    --traffic-routing-config '{"type": "TimeBasedCanary", "timeBasedCanary": {"canaryPercentage": 10, "canaryInterval": 5}}'

# Lambda Linear 배포 구성 생성
aws deploy create-deployment-config \
    --deployment-config-name Linear10PercentEvery3Minutes \
    --compute-platform Lambda \
    --traffic-routing-config '{"type": "TimeBasedLinear", "timeBasedLinear": {"linearPercentage": 10, "linearInterval": 3}}'
```

### 라이프사이클 훅

EC2/On-Premises 배포의 라이프사이클 훅 순서는 다음과 같습니다.

1. **ApplicationStop**: 기존 애플리케이션을 중지합니다.
2. **DownloadBundle**: S3/GitHub에서 리비전을 다운로드합니다. (사용자 스크립트 불가)
3. **BeforeInstall**: 설치 전 준비 작업 (백업, 디렉토리 생성 등).
4. **Install**: AppSpec의 files 섹션에 따라 파일을 배치합니다. (사용자 스크립트 불가)
5. **AfterInstall**: 설치 후 설정 작업 (설정 파일 수정, 권한 설정 등).
6. **ApplicationStart**: 새 버전의 애플리케이션을 시작합니다.
7. **ValidateService**: 서비스 정상 동작을 검증합니다.

## 아키텍처/동작 원리

### CodeDeploy 에이전트

EC2/On-Premises 환경에서는 각 인스턴스에 CodeDeploy 에이전트가 설치되어 있어야 합니다.

```bash
# Amazon Linux 2에 CodeDeploy 에이전트 설치
sudo yum update -y
sudo yum install -y ruby wget

wget https://aws-codedeploy-ap-northeast-2.s3.ap-northeast-2.amazonaws.com/latest/install
chmod +x ./install
sudo ./install auto

# 에이전트 상태 확인
sudo service codedeploy-agent status

# 에이전트 로그 확인
tail -f /var/log/aws/codedeploy-agent/codedeploy-agent.log
```

에이전트의 동작은 다음과 같습니다.
1. 에이전트가 주기적으로(기본 1초) CodeDeploy 서비스를 폴링합니다.
2. 새 배포가 있으면 S3/GitHub에서 리비전을 다운로드합니다.
3. AppSpec에 정의된 라이프사이클 훅에 따라 스크립트를 순차 실행합니다.
4. 각 단계의 성공/실패를 CodeDeploy 서비스에 보고합니다.

### 배포 실행 흐름

1. 사용자 또는 CI/CD 파이프라인이 배포를 트리거합니다.
2. CodeDeploy 서비스가 배포 그룹의 대상 인스턴스를 확인합니다.
3. 배포 구성에 따라 배치 단위를 결정합니다 (OneAtATime, HalfAtATime 등).
4. 각 배치의 인스턴스에서 에이전트가 배포를 실행합니다.
5. 로드 밸런서가 있으면 배포 중인 인스턴스를 연결 해제합니다.
6. 배포 완료 후 인스턴스를 로드 밸런서에 재등록합니다.
7. 검증 단계(ValidateService)에서 실패하면 자동 롤백이 트리거됩니다.

## 실전 활용

### 배포 스크립트 예시

```bash
# scripts/stop_server.sh
#!/bin/bash
set -e
if systemctl is-active --quiet nginx; then
    systemctl stop nginx
fi
echo "Server stopped successfully"

# scripts/before_install.sh
#!/bin/bash
set -e
# 기존 애플리케이션 백업
if [ -d /var/www/myapp ]; then
    cp -r /var/www/myapp /var/www/myapp.backup.$(date +%Y%m%d%H%M%S)
fi
# 디렉토리 준비
mkdir -p /var/www/myapp
echo "Before install completed"

# scripts/after_install.sh
#!/bin/bash
set -e
cd /var/www/myapp
# 의존성 설치
npm install --production
# 설정 파일 링크
ln -sf /etc/myapp/config.json /var/www/myapp/config.json
# 권한 설정
chown -R www-data:www-data /var/www/myapp
echo "After install completed"

# scripts/start_server.sh
#!/bin/bash
set -e
systemctl start nginx
echo "Server started successfully"

# scripts/validate_service.sh
#!/bin/bash
set -e
# 헬스 체크
for i in {1..30}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80/health)
    if [ "$HTTP_CODE" = "200" ]; then
        echo "Service validation passed"
        exit 0
    fi
    echo "Waiting for service... (attempt $i/30)"
    sleep 2
done
echo "Service validation FAILED"
exit 1
```

### AWS CLI를 활용한 배포 실행 및 관리

```bash
# S3에 리비전 업로드 (배포 번들 생성)
aws deploy push \
    --application-name my-web-app \
    --s3-location s3://my-deploy-bucket/my-web-app/app-v1.0.zip \
    --source /path/to/my-app

# 배포 생성 (실행)
aws deploy create-deployment \
    --application-name my-web-app \
    --deployment-group-name production \
    --s3-location bucket=my-deploy-bucket,key=my-web-app/app-v1.0.zip,bundleType=zip \
    --description "Version 1.0 production deployment" \
    --file-exists-behavior OVERWRITE

# 배포 상태 확인
aws deploy get-deployment \
    --deployment-id d-ABCDEF123 \
    --query 'deploymentInfo.{Status:status,Creator:creator,CreateTime:createTime,CompleteTime:completeTime}'

# 배포 인스턴스별 상태 확인
aws deploy list-deployment-targets \
    --deployment-id d-ABCDEF123

aws deploy get-deployment-target \
    --deployment-id d-ABCDEF123 \
    --target-id i-0123456789abcdef0

# 배포 중지
aws deploy stop-deployment \
    --deployment-id d-ABCDEF123 \
    --auto-rollback-enabled

# 최근 배포 이력 조회
aws deploy list-deployments \
    --application-name my-web-app \
    --deployment-group-name production \
    --include-only-statuses Succeeded Failed \
    --query 'deployments[:5]'

# 수동 롤백 (이전 성공 배포로 재배포)
aws deploy create-deployment \
    --application-name my-web-app \
    --deployment-group-name production \
    --s3-location bucket=my-deploy-bucket,key=my-web-app/app-v0.9.zip,bundleType=zip \
    --description "Rollback to v0.9"
```

### CodePipeline 통합

CodeDeploy는 CodePipeline의 배포 스테이지로 자연스럽게 통합됩니다.

```bash
# CodePipeline에서 CodeDeploy 스테이지 확인
aws codepipeline get-pipeline \
    --name my-pipeline \
    --query 'pipeline.stages[?name==`Deploy`]'
```

## 모범 사례/보안

### 배포 모범 사례

1. **Blue/Green 배포를 기본 전략으로 사용합니다.** In-Place 배포보다 롤백이 빠르고 안전합니다. Auto Scaling 그룹과 함께 사용하면 새 인스턴스 프로비저닝이 자동화됩니다.

2. **자동 롤백을 항상 활성화합니다.** 배포 실패나 CloudWatch 알람 트리거 시 자동으로 이전 버전으로 롤백되도록 설정합니다.

3. **ValidateService 훅을 반드시 구현합니다.** 배포 후 서비스가 정상적으로 동작하는지 검증하는 헬스 체크를 구현하여, 문제가 있으면 즉시 롤백이 트리거되도록 합니다.

4. **배포 번들의 크기를 최소화합니다.** 불필요한 파일(테스트 코드, 문서, 빌드 도구 등)을 제외하여 배포 시간을 단축합니다.

5. **단계적 배포를 적용합니다.** 개발 -> 스테이징 -> 프로덕션(카나리) -> 프로덕션(전체) 순서로 단계적으로 배포합니다.

### 보안 모범 사례

1. **최소 권한 서비스 역할을 사용합니다.**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceStatus",
                "tag:GetResources"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-deploy-bucket",
                "arn:aws:s3:::my-deploy-bucket/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "autoscaling:CompleteLifecycleAction",
                "autoscaling:DeleteLifecycleHook",
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeLifecycleHooks",
                "autoscaling:PutLifecycleHook",
                "autoscaling:RecordLifecycleActionHeartbeat"
            ],
            "Resource": "*"
        }
    ]
}
```

2. **S3 배포 번들을 암호화합니다.** SSE-S3 또는 SSE-KMS를 사용하여 배포 아티팩트를 암호화합니다.

3. **배포 스크립트에 민감 정보를 포함하지 않습니다.** 비밀번호, API 키 등은 AWS Secrets Manager나 SSM Parameter Store를 통해 런타임에 주입합니다.

4. **CloudTrail로 배포 활동을 감사합니다.** 누가 언제 어떤 배포를 트리거했는지 추적합니다.

## 관련 서비스 비교

### CodeDeploy vs Elastic Beanstalk

| 항목 | CodeDeploy | Elastic Beanstalk |
|------|-----------|-------------------|
| 추상화 수준 | 배포만 담당 | 인프라 + 배포 통합 |
| 인프라 관리 | 별도 관리 필요 | 자동 프로비저닝 |
| 배포 대상 | EC2, Lambda, ECS, 온프레미스 | 웹 애플리케이션 |
| 배포 전략 | 다양함 (In-Place, Blue/Green 등) | Rolling, Immutable |
| 유연성 | 높음 | 보통 |
| 비용 | 무료 (리소스 비용만) | 무료 (리소스 비용만) |

### CodeDeploy vs AWS Systems Manager

| 항목 | CodeDeploy | Systems Manager |
|------|-----------|------------------|
| 주요 목적 | 애플리케이션 배포 | 인프라 운영 관리 |
| 배포 전략 | Blue/Green, Canary 등 | Run Command |
| 롤백 | 자동 롤백 지원 | 수동 처리 필요 |
| 적합 시나리오 | 정형화된 배포 | 패치, 설정 변경 등 |

### CodeDeploy vs GitHub Actions Deploy

| 항목 | CodeDeploy | GitHub Actions |
|------|-----------|----------------|
| AWS 통합 | 네이티브 | 별도 설정 필요 |
| 배포 전략 | 다양한 내장 전략 | 커스텀 구현 |
| 롤백 | 자동 | 수동 구현 |
| 모니터링 | CloudWatch 통합 | 제한적 |
| 비용 | 무료 | GitHub Actions 분 과금 |

## 요약

AWS CodeDeploy는 EC2, Lambda, ECS, 온프레미스를 아우르는 범용 배포 서비스입니다. AppSpec 파일을 통해 배포 프로세스를 선언적으로 정의하고, 라이프사이클 훅으로 각 단계를 세밀하게 제어할 수 있습니다.

Blue/Green 배포와 자동 롤백을 활용하면 무중단 배포와 빠른 장애 복구가 가능합니다. Lambda와 ECS 환경에서는 Canary와 Linear 배포 전략으로 트래픽을 점진적으로 전환하여 배포 위험을 최소화할 수 있습니다.

CodeDeploy는 CodePipeline, CodeBuild와 함께 AWS의 CI/CD 파이프라인의 핵심 구성 요소이며, CodeDeploy 자체는 무료로 사용할 수 있어 비용 효율적입니다. ValidateService 훅을 통한 배포 후 검증과 자동 롤백 설정은 프로덕션 배포의 안전성을 보장하는 핵심 모범 사례입니다.