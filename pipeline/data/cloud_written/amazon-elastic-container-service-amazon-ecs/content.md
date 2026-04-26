<!-- infographic-hero -->
![Amazon ECS (Elastic Container Service) - 컨테이너 오케스트레이션 완벽 가이드 핵심 요약](figures/infographic.svg)

*Figure: Amazon ECS (Elastic Container Service) - 컨테이너 오케스트레이션 완벽 가이드 한 장 요약 인포그래픽*

## 개요

Amazon ECS(Elastic Container Service)는 AWS에서 제공하는 완전 관리형 컨테이너 오케스트레이션 서비스입니다. Docker 컨테이너를 대규모로 실행, 중지, 관리할 수 있으며, AWS 생태계의 다양한 서비스(ALB, CloudWatch, IAM, ECR 등)와 긴밀하게 통합됩니다.

Kubernetes 기반의 Amazon EKS와 함께 AWS의 양대 컨테이너 오케스트레이션 서비스를 구성하지만, ECS는 AWS 네이티브 서비스로서 설정이 단순하고 AWS 서비스와의 연동이 더 자연스럽다는 장점이 있습니다. 특히 AWS Fargate와 결합하면 인프라 관리 없이 컨테이너만 운영하는 완전한 서버리스 컨테이너 환경을 구현할 수 있습니다.

본 글에서는 ECS의 핵심 개념부터 프로덕션 운영까지, 실무에서 필요한 모든 내용을 체계적으로 다루겠습니다.

## 핵심 기능

### ECS 핵심 구성 요소

**1. Cluster**: 태스크와 서비스를 논리적으로 그룹화하는 최상위 리소스입니다.

```bash
# ECS 클러스터 생성
aws ecs create-cluster \
  --cluster-name production-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy '[
    {"capacityProvider": "FARGATE", "weight": 1, "base": 2},
    {"capacityProvider": "FARGATE_SPOT", "weight": 3}
  ]' \
  --configuration '{
    "executeCommandConfiguration": {
      "logging": "DEFAULT"
    }
  }' \
  --settings '[{"name": "containerInsights", "value": "enabled"}]'
```

**2. Task Definition**: 컨테이너의 실행 방법을 정의하는 청사진(Blueprint)입니다. 컨테이너 이미지, CPU/메모리, 환경 변수, 포트 매핑 등을 지정합니다.

```bash
# Task Definition 등록
aws ecs register-task-definition \
  --cli-input-json '{
    "family": "web-application",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "512",
    "memory": "1024",
    "executionRoleArn": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole",
    "taskRoleArn": "arn:aws:iam::123456789012:role/ecsTaskRole",
    "containerDefinitions": [
      {
        "name": "web",
        "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/my-app:latest",
        "portMappings": [{"containerPort": 8080, "protocol": "tcp"}],
        "essential": true,
        "healthCheck": {
          "command": ["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
          "interval": 30,
          "timeout": 5,
          "retries": 3,
          "startPeriod": 60
        },
        "logConfiguration": {
          "logDriver": "awslogs",
          "options": {
            "awslogs-group": "/ecs/web-application",
            "awslogs-region": "ap-northeast-2",
            "awslogs-stream-prefix": "web"
          }
        },
        "environment": [
          {"name": "NODE_ENV", "value": "production"}
        ],
        "secrets": [
          {"name": "DB_PASSWORD", "valueFrom": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:db-password-abc123"}
        ]
      }
    ]
  }'
```

**3. Service**: 지정된 수의 태스크를 지속적으로 실행하고 관리합니다. 로드 밸런서 연동, 오토스케일링, 롤링 배포 등을 담당합니다.

```bash
# ECS Service 생성
aws ecs create-service \
  --cluster production-cluster \
  --service-name web-service \
  --task-definition web-application:1 \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration '{
    "awsvpcConfiguration": {
      "subnets": ["subnet-abc123", "subnet-def456"],
      "securityGroups": ["sg-abc123"],
      "assignPublicIp": "DISABLED"
    }
  }' \
  --load-balancers '[{
    "targetGroupArn": "arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:targetgroup/ecs-web-tg/abc123",
    "containerName": "web",
    "containerPort": 8080
  }]' \
  --deployment-configuration '{
    "maximumPercent": 200,
    "minimumHealthyPercent": 100,
    "deploymentCircuitBreaker": {
      "enable": true,
      "rollback": true
    }
  }' \
  --enable-execute-command
```

### EC2 시작 유형 vs Fargate 시작 유형

| 항목 | EC2 시작 유형 | Fargate 시작 유형 |
|------|-------------|------------------|
| 인프라 관리 | EC2 인스턴스 관리 필요 | AWS가 관리 |
| 가격 모델 | EC2 인스턴스 비용 | vCPU+메모리 사용량 기준 |
| GPU 지원 | 지원 | 미지원 |
| 데몬 태스크 | 지원 | 미지원 |
| 최대 리소스 | 인스턴스 유형에 따라 | 4 vCPU, 30 GB |
| 시작 시간 | 빠름 (미리 프로비저닝) | 약간 느림 (온디맨드) |
| 비용 효율 | 높은 활용률 시 유리 | 가변적 워크로드에 유리 |

### Fargate Spot

Fargate Spot은 여분의 Fargate 용량을 최대 70% 할인된 가격에 사용할 수 있는 옵션입니다.

```bash
# Capacity Provider 전략에 Fargate Spot 포함
aws ecs create-service \
  --cluster production-cluster \
  --service-name batch-processor \
  --task-definition batch-job:1 \
  --desired-count 10 \
  --capacity-provider-strategy '[
    {"capacityProvider": "FARGATE", "weight": 1, "base": 2},
    {"capacityProvider": "FARGATE_SPOT", "weight": 4}
  ]' \
  --network-configuration '{
    "awsvpcConfiguration": {
      "subnets": ["subnet-abc123"],
      "securityGroups": ["sg-abc123"]
    }
  }'
```

## 아키텍처/동작 원리

### ECS 아키텍처 개요

```
[사용자 요청]
     |
     v
[Application Load Balancer]
     |
     v
[ECS Service]
  ├── Task 1 (Fargate)
  │    ├── Container A (web)
  │    └── Container B (sidecar)
  ├── Task 2 (Fargate)
  │    ├── Container A (web)
  │    └── Container B (sidecar)
  └── Task 3 (Fargate)
       ├── Container A (web)
       └── Container B (sidecar)
     |
     v
[ECR] [CloudWatch] [Secrets Manager] [RDS/DynamoDB]
```

### 네트워크 모드

ECS는 여러 네트워크 모드를 지원하지만, Fargate에서는 `awsvpc` 모드만 사용 가능합니다.

- **awsvpc**: 각 태스크에 ENI(Elastic Network Interface)가 할당되어 고유한 프라이빗 IP를 갖습니다. 보안 그룹을 태스크 수준에서 적용할 수 있어 가장 권장되는 모드입니다.
- **bridge**: Docker 기본 브릿지 네트워크를 사용합니다. EC2 시작 유형에서만 지원됩니다.
- **host**: 호스트의 네트워크 스택을 직접 사용합니다. EC2 시작 유형에서만 지원됩니다.

### 서비스 디스커버리

ECS는 AWS Cloud Map과 통합되어 서비스 디스커버리를 제공합니다.

```bash
# Cloud Map 네임스페이스 생성
aws servicediscovery create-private-dns-namespace \
  --name ecs.local \
  --vpc vpc-abc123

# 서비스 디스커버리 서비스 생성
aws servicediscovery create-service \
  --name web-service \
  --namespace-id ns-abc123 \
  --dns-config '{
    "DnsRecords": [{"Type": "A", "TTL": 60}],
    "RoutingPolicy": "MULTIVALUE"
  }' \
  --health-check-custom-config '{"FailureThreshold": 1}'
```

### 배포 전략

**롤링 업데이트 (기본)**

```bash
# 새 버전 배포 (Task Definition 업데이트)
aws ecs update-service \
  --cluster production-cluster \
  --service web-service \
  --task-definition web-application:2 \
  --deployment-configuration '{
    "maximumPercent": 200,
    "minimumHealthyPercent": 100
  }'
```

**Blue/Green 배포 (CodeDeploy 연동)**

```bash
# CodeDeploy 배포 그룹 생성
aws deploy create-deployment-group \
  --application-name ecs-app \
  --deployment-group-name ecs-dg \
  --service-role-arn "arn:aws:iam::123456789012:role/CodeDeployECSRole" \
  --deployment-config-name CodeDeployDefault.ECSLinear10PercentEvery1Minutes \
  --ecs-services '[{
    "serviceName": "web-service",
    "clusterName": "production-cluster"
  }]' \
  --load-balancer-info '{
    "targetGroupPairInfoList": [{
      "targetGroups": [
        {"name": "ecs-tg-blue"},
        {"name": "ecs-tg-green"}
      ],
      "prodTrafficRoute": {"listenerArns": ["arn:aws:elasticloadbalancing:...:listener/app/..."]}
    }]
  }' \
  --auto-rollback-configuration '{"enabled": true, "events": ["DEPLOYMENT_FAILURE"]}'
```

## 실전 활용

### 사례 1: 오토스케일링 구성

```bash
# Application Auto Scaling 타겟 등록
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/production-cluster/web-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 20

# CPU 기반 Target Tracking 정책
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/production-cluster/web-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name cpu-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'

# 요청 수 기반 스케일링 (ALB RequestCount)
aws application-autoscaling put-scaling-policy \
  --service-namespace ecs \
  --resource-id service/production-cluster/web-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-name request-scaling \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 1000.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ALBRequestCountPerTarget",
      "ResourceLabel": "app/my-alb/abc123/targetgroup/ecs-tg/def456"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'
```

### 사례 2: ECS Exec으로 컨테이너 디버깅

```bash
# ECS Exec으로 실행 중인 컨테이너에 접속
aws ecs execute-command \
  --cluster production-cluster \
  --task arn:aws:ecs:ap-northeast-2:123456789012:task/production-cluster/abc123 \
  --container web \
  --interactive \
  --command "/bin/sh"
```

### 사례 3: 서비스 상태 모니터링

```bash
# 서비스 상태 확인
aws ecs describe-services \
  --cluster production-cluster \
  --services web-service \
  --query 'services[0].{
    Status: status,
    DesiredCount: desiredCount,
    RunningCount: runningCount,
    PendingCount: pendingCount,
    Deployments: deployments[*].{Status: status, DesiredCount: desiredCount, RunningCount: runningCount, TaskDefinition: taskDefinition}
  }'

# 태스크 목록 조회
aws ecs list-tasks \
  --cluster production-cluster \
  --service-name web-service \
  --desired-status RUNNING

# 태스크 상세 정보
aws ecs describe-tasks \
  --cluster production-cluster \
  --tasks arn:aws:ecs:ap-northeast-2:123456789012:task/production-cluster/abc123 \
  --query 'tasks[0].{TaskArn: taskArn, LastStatus: lastStatus, HealthStatus: healthStatus, Containers: containers[*].{Name: name, LastStatus: lastStatus, HealthStatus: healthStatus}}'
```

### 사례 4: Scheduled Task (예약 작업)

```bash
# EventBridge 규칙으로 예약 작업 생성
aws events put-rule \
  --name "daily-batch-job" \
  --schedule-expression "cron(0 2 * * ? *)" \
  --description "매일 오전 11시(KST) 배치 작업"

aws events put-targets \
  --rule "daily-batch-job" \
  --targets '[{
    "Id": "ecs-batch-target",
    "Arn": "arn:aws:ecs:ap-northeast-2:123456789012:cluster/production-cluster",
    "RoleArn": "arn:aws:iam::123456789012:role/ecsEventsRole",
    "EcsParameters": {
      "TaskDefinitionArn": "arn:aws:ecs:ap-northeast-2:123456789012:task-definition/batch-job:1",
      "TaskCount": 1,
      "LaunchType": "FARGATE",
      "NetworkConfiguration": {
        "awsvpcConfiguration": {
          "Subnets": ["subnet-abc123"],
          "SecurityGroups": ["sg-abc123"]
        }
      }
    }
  }]'
```

## 모범 사례/보안

### IAM 역할 분리

- **Task Execution Role**: ECR에서 이미지 풀, CloudWatch Logs 쓰기, Secrets Manager 읽기 등 ECS 에이전트가 사용하는 역할입니다.
- **Task Role**: 컨테이너 내 애플리케이션이 AWS 서비스에 접근할 때 사용하는 역할입니다. 최소 권한 원칙을 적용합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-app-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:Query",
        "dynamodb:PutItem"
      ],
      "Resource": "arn:aws:dynamodb:ap-northeast-2:123456789012:table/my-table"
    }
  ]
}
```

### 이미지 보안

- ECR 이미지 스캔을 활성화하여 취약점을 자동으로 감지합니다.
- 이미지 태그 불변성(Immutability)을 설정하여 태그 덮어쓰기를 방지합니다.
- latest 태그 대신 구체적인 버전 태그를 사용합니다.

### 로깅 및 모니터링

```bash
# Container Insights 활성화 확인
aws ecs describe-clusters \
  --clusters production-cluster \
  --include SETTINGS \
  --query 'clusters[0].settings'

# CloudWatch 로그 그룹 생성
aws logs create-log-group \
  --log-group-name /ecs/web-application \
  --retention-in-days 30
```

### 비용 최적화

- Fargate Spot을 배치 작업이나 비중요 서비스에 활용합니다.
- Compute Savings Plans로 Fargate 비용을 절감합니다 (최대 50%).
- 태스크의 CPU/메모리를 실제 사용량에 맞게 Right-sizing합니다.

## 관련 서비스 비교

| 항목 | Amazon ECS | Amazon EKS | AWS App Runner | AWS Lambda |
|------|-----------|-----------|----------------|------------|
| 오케스트레이터 | ECS (AWS 네이티브) | Kubernetes | 관리형 (내부 ECS) | 없음 |
| 관리 복잡도 | 중간 | 높음 | 매우 낮음 | 낮음 |
| 커스터마이징 | 높음 | 매우 높음 | 낮음 | 중간 |
| 멀티 클라우드 | AWS 전용 | 이식 가능 | AWS 전용 | AWS 전용 |
| 가격 | Fargate/EC2 | Fargate/EC2 + 관리비 | 요청+리소스 | 요청+실행시간 |
| GPU 지원 | 지원 (EC2) | 지원 | 미지원 | 미지원 |
| 적합한 규모 | 중대규모 | 대규모/멀티클라우드 | 소규모 웹앱 | 이벤트 기반 |

## 요약

Amazon ECS는 AWS 환경에서 컨테이너 워크로드를 운영하기 위한 핵심 서비스입니다. 핵심 내용을 정리하면 다음과 같습니다.

- **Fargate**: 인프라 관리 없이 컨테이너를 실행하는 서버리스 옵션으로, 대부분의 워크로드에 권장됩니다.
- **Task Definition**: 컨테이너 구성의 청사진으로, 이미지, 리소스, 환경 변수, 시크릿 등을 정의합니다.
- **Service**: 지정된 수의 태스크를 유지하고 로드 밸런서와 연동하며 롤링/Blue-Green 배포를 지원합니다.
- **오토스케일링**: CPU, 메모리, 요청 수 기반의 자동 확장/축소가 가능합니다.
- **보안**: Task Execution Role과 Task Role을 분리하고, ECR 이미지 스캔을 활성화합니다.
- **비용 최적화**: Fargate Spot(최대 70% 할인)과 Savings Plans(최대 50% 할인)을 활용합니다.
- **ECS Exec**: 실행 중인 컨테이너에 직접 접속하여 디버깅할 수 있습니다.

ECS는 Kubernetes의 복잡성 없이 AWS에서 컨테이너를 효율적으로 운영하고자 하는 팀에게 최적의 선택입니다.