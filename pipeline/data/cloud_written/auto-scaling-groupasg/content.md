<!-- infographic-hero -->
![Auto Scaling Group(ASG) - EC2 자동 확장/축소 완벽 가이드 핵심 요약](figures/infographic.svg)

*Figure: Auto Scaling Group(ASG) - EC2 자동 확장/축소 완벽 가이드 한 장 요약 인포그래픽*

## 개요

Auto Scaling Group(ASG)은 Amazon EC2 인스턴스의 수를 자동으로 조절하여 애플리케이션의 가용성을 보장하고 비용을 최적화하는 서비스입니다. 트래픽이 증가하면 인스턴스를 자동으로 추가(Scale Out)하고, 트래픽이 감소하면 불필요한 인스턴스를 제거(Scale In)합니다.

현대의 클라우드 아키텍처에서 Auto Scaling은 선택이 아닌 필수입니다. 고정된 수의 서버로 운영하면 피크 시간에는 성능 저하가 발생하고, 비수기에는 불필요한 비용이 낭비됩니다. ASG를 올바르게 구성하면 수요에 정확히 맞는 인프라를 유지하면서 비용을 최대 70%까지 절감할 수 있습니다.

본 글에서는 ASG의 핵심 개념부터 고급 설정, 실전 운영 노하우까지 체계적으로 다루겠습니다.

## 핵심 기능

### 1. 시작 템플릿 (Launch Template)

ASG에서 생성되는 인스턴스의 구성을 정의합니다. 이전의 시작 구성(Launch Configuration)을 대체하는 권장 방식입니다.

```bash
# 시작 템플릿 생성
aws ec2 create-launch-template \
  --launch-template-name "web-server-template" \
  --version-description "v1 - Initial template" \
  --launch-template-data '{
    "ImageId": "ami-0abc123def456789",
    "InstanceType": "t3.medium",
    "KeyName": "my-key",
    "SecurityGroupIds": ["sg-abc123"],
    "IamInstanceProfile": {
      "Arn": "arn:aws:iam::123456789012:instance-profile/WebServerRole"
    },
    "BlockDeviceMappings": [{
      "DeviceName": "/dev/xvda",
      "Ebs": {
        "VolumeSize": 30,
        "VolumeType": "gp3",
        "Encrypted": true
      }
    }],
    "UserData": "IyEvYmluL2Jhc2gKeXVtIHVwZGF0ZSAteQp5dW0gaW5zdGFsbCAteSBodHRwZApzeXN0ZW1jdGwgc3RhcnQgaHR0cGQ=",
    "TagSpecifications": [{
      "ResourceType": "instance",
      "Tags": [{"Key": "Name", "Value": "web-server"}, {"Key": "Environment", "Value": "production"}]
    }],
    "Monitoring": {"Enabled": true},
    "MetadataOptions": {
      "HttpTokens": "required",
      "HttpEndpoint": "enabled"
    }
  }'

# 시작 템플릿 버전 관리
aws ec2 create-launch-template-version \
  --launch-template-name "web-server-template" \
  --source-version 1 \
  --version-description "v2 - Updated AMI" \
  --launch-template-data '{"ImageId": "ami-new123abc"}'
```

### 2. Auto Scaling Group 생성

```bash
# ASG 생성
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name "web-server-asg" \
  --launch-template '{
    "LaunchTemplateName": "web-server-template",
    "Version": "$Latest"
  }' \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 3 \
  --vpc-zone-identifier "subnet-abc123,subnet-def456,subnet-ghi789" \
  --target-group-arns "arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:targetgroup/web-tg/abc123" \
  --health-check-type ELB \
  --health-check-grace-period 300 \
  --default-cooldown 300 \
  --termination-policies '["OldestLaunchTemplate", "OldestInstance"]' \
  --tags '[
    {"Key": "Name", "Value": "web-server", "PropagateAtLaunch": true},
    {"Key": "Environment", "Value": "production", "PropagateAtLaunch": true}
  ]'
```

핵심 파라미터 설명:
- **min-size**: 최소 인스턴스 수. 절대로 이 수 이하로 줄어들지 않습니다.
- **max-size**: 최대 인스턴스 수. 아무리 트래픽이 많아도 이 수를 초과하지 않습니다.
- **desired-capacity**: 현재 유지하고자 하는 인스턴스 수입니다.
- **health-check-type**: EC2 상태 체크만 할 것인지(EC2), ALB 헬스체크도 포함할 것인지(ELB) 선택합니다.
- **health-check-grace-period**: 새 인스턴스 시작 후 헬스체크를 유예하는 시간(초)입니다.

### 3. 스케일링 정책

**Target Tracking Scaling (추천)**

지정한 메트릭의 목표 값을 유지하도록 자동으로 조절합니다.

```bash
# CPU 사용률 기반 Target Tracking
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name "web-server-asg" \
  --policy-name "cpu-target-tracking" \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    },
    "TargetValue": 60.0,
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'

# ALB 요청 수 기반 Target Tracking
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name "web-server-asg" \
  --policy-name "request-count-tracking" \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ALBRequestCountPerTarget",
      "ResourceLabel": "app/my-alb/abc123/targetgroup/web-tg/def456"
    },
    "TargetValue": 1000.0
  }'

# 커스텀 메트릭 기반 Target Tracking
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name "web-server-asg" \
  --policy-name "custom-metric-tracking" \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "CustomizedMetricSpecification": {
      "MetricName": "ActiveConnections",
      "Namespace": "MyApp/Metrics",
      "Statistic": "Average",
      "Unit": "Count"
    },
    "TargetValue": 500.0
  }'
```

**Step Scaling**

CloudWatch 알람에 연동하여 단계별로 인스턴스 수를 조절합니다.

```bash
# Step Scaling 정책 생성
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name "web-server-asg" \
  --policy-name "step-scale-out" \
  --policy-type StepScaling \
  --adjustment-type ChangeInCapacity \
  --step-adjustments '[
    {"MetricIntervalLowerBound": 0, "MetricIntervalUpperBound": 20, "ScalingAdjustment": 1},
    {"MetricIntervalLowerBound": 20, "MetricIntervalUpperBound": 40, "ScalingAdjustment": 2},
    {"MetricIntervalLowerBound": 40, "ScalingAdjustment": 3}
  ]'
```

**Predictive Scaling**

머신러닝을 활용하여 미래 트래픽을 예측하고 선제적으로 인스턴스를 프로비저닝합니다.

```bash
# Predictive Scaling 정책
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name "web-server-asg" \
  --policy-name "predictive-scaling" \
  --policy-type PredictiveScaling \
  --predictive-scaling-configuration '{
    "MetricSpecifications": [{
      "TargetValue": 60.0,
      "PredefinedMetricPairSpecification": {
        "PredefinedMetricType": "ASGCPUUtilization"
      }
    }],
    "Mode": "ForecastAndScale",
    "SchedulingBufferTime": 300
  }'
```

**Scheduled Scaling**

예측 가능한 트래픽 패턴에 맞춰 미리 인스턴스 수를 조절합니다.

```bash
# 업무 시간 확장
aws autoscaling put-scheduled-update-group-action \
  --auto-scaling-group-name "web-server-asg" \
  --scheduled-action-name "scale-up-business-hours" \
  --recurrence "0 0 * * MON-FRI" \
  --min-size 5 \
  --max-size 20 \
  --desired-capacity 8

# 야간 축소
aws autoscaling put-scheduled-update-group-action \
  --auto-scaling-group-name "web-server-asg" \
  --scheduled-action-name "scale-down-night" \
  --recurrence "0 12 * * *" \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 2
```

### 4. 수명 주기 후크 (Lifecycle Hooks)

인스턴스 시작/종료 시 추가 작업을 수행할 수 있습니다.

```bash
# 인스턴스 시작 시 후크 (앱 초기화 대기)
aws autoscaling put-lifecycle-hook \
  --auto-scaling-group-name "web-server-asg" \
  --lifecycle-hook-name "launch-hook" \
  --lifecycle-transition "autoscaling:EC2_INSTANCE_LAUNCHING" \
  --heartbeat-timeout 600 \
  --default-result ABANDON \
  --notification-target-arn "arn:aws:sns:ap-northeast-2:123456789012:asg-notifications"

# 인스턴스 종료 시 후크 (로그 백업, 연결 드레이닝)
aws autoscaling put-lifecycle-hook \
  --auto-scaling-group-name "web-server-asg" \
  --lifecycle-hook-name "terminate-hook" \
  --lifecycle-transition "autoscaling:EC2_INSTANCE_TERMINATING" \
  --heartbeat-timeout 300 \
  --default-result CONTINUE

# 수명 주기 작업 완료 알림
aws autoscaling complete-lifecycle-action \
  --auto-scaling-group-name "web-server-asg" \
  --lifecycle-hook-name "launch-hook" \
  --instance-id i-0abc123 \
  --lifecycle-action-result CONTINUE
```

### 5. 혼합 인스턴스 정책 (Mixed Instances Policy)

Spot 인스턴스와 온디맨드 인스턴스를 혼합하여 비용을 절감합니다.

```bash
# 혼합 인스턴스 ASG 생성
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name "cost-optimized-asg" \
  --mixed-instances-policy '{
    "LaunchTemplate": {
      "LaunchTemplateSpecification": {
        "LaunchTemplateName": "web-server-template",
        "Version": "$Latest"
      },
      "Overrides": [
        {"InstanceType": "t3.medium"},
        {"InstanceType": "t3a.medium"},
        {"InstanceType": "t2.medium"},
        {"InstanceType": "m5.large"}
      ]
    },
    "InstancesDistribution": {
      "OnDemandBaseCapacity": 2,
      "OnDemandPercentageAboveBaseCapacity": 25,
      "SpotAllocationStrategy": "capacity-optimized",
      "SpotMaxPrice": ""
    }
  }' \
  --min-size 2 \
  --max-size 20 \
  --desired-capacity 8 \
  --vpc-zone-identifier "subnet-abc123,subnet-def456"
```

## 아키텍처/동작 원리

### ASG 스케일링 동작 흐름

```
[CloudWatch 메트릭 수집]
       |
       v
[스케일링 정책 평가]
       |
       v
[Desired Capacity 변경 결정]
       |
   Scale Out / Scale In
   /                   \
  v                     v
[인스턴스 시작]     [인스턴스 종료]
  |                     |
  v                     v
[Lifecycle Hook]    [Lifecycle Hook]
(launch)            (terminate)
  |                     |
  v                     v
[ELB 등록]          [ELB 해제 + 드레이닝]
  |                     |
  v                     v
[헬스체크 통과]     [인스턴스 종료]
  |                     
  v                    
[서비스 투입]
```

### 가용 영역 밸런싱

ASG는 인스턴스를 지정된 가용 영역에 균등하게 분산합니다. Scale In 시에는 가장 인스턴스가 많은 AZ에서 먼저 제거하여 균형을 유지합니다.

### 종료 정책 (Termination Policy)

Scale In 시 어떤 인스턴스를 먼저 종료할지 결정합니다.

| 정책 | 설명 |
|------|------|
| Default | 가장 오래된 시작 구성/템플릿의 인스턴스 우선 종료 |
| OldestInstance | 가장 오래된 인스턴스 우선 종료 |
| NewestInstance | 가장 최근 인스턴스 우선 종료 |
| OldestLaunchTemplate | 가장 오래된 시작 템플릿 버전의 인스턴스 우선 |
| ClosestToNextInstanceHour | 다음 과금 시간에 가장 가까운 인스턴스 우선 |

### 인스턴스 갱신 (Instance Refresh)

실행 중인 인스턴스를 새 시작 템플릿 버전으로 점진적으로 교체합니다.

```bash
# 인스턴스 갱신 시작
aws autoscaling start-instance-refresh \
  --auto-scaling-group-name "web-server-asg" \
  --preferences '{
    "MinHealthyPercentage": 90,
    "InstanceWarmup": 300,
    "MaxHealthyPercentage": 110
  }'

# 인스턴스 갱신 상태 확인
aws autoscaling describe-instance-refreshes \
  --auto-scaling-group-name "web-server-asg" \
  --query 'InstanceRefreshes[0].{Id: InstanceRefreshId, Status: Status, PercentageComplete: PercentageComplete}'
```

## 실전 활용

### 사례 1: 웹 애플리케이션 3-Tier 아키텍처

```bash
# Web Tier ASG
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name "web-tier-asg" \
  --launch-template '{"LaunchTemplateName": "web-template", "Version": "$Latest"}' \
  --min-size 2 --max-size 10 --desired-capacity 3 \
  --vpc-zone-identifier "subnet-pub-a,subnet-pub-b" \
  --target-group-arns "arn:aws:elasticloadbalancing:...:targetgroup/web-tg/..."

# App Tier ASG
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name "app-tier-asg" \
  --launch-template '{"LaunchTemplateName": "app-template", "Version": "$Latest"}' \
  --min-size 2 --max-size 20 --desired-capacity 4 \
  --vpc-zone-identifier "subnet-priv-a,subnet-priv-b" \
  --target-group-arns "arn:aws:elasticloadbalancing:...:targetgroup/app-tg/..."
```

### 사례 2: ASG 상태 모니터링

```bash
# ASG 전체 상태 확인
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names "web-server-asg" \
  --query 'AutoScalingGroups[0].{
    Name: AutoScalingGroupName,
    Min: MinSize,
    Max: MaxSize,
    Desired: DesiredCapacity,
    InService: length(Instances[?LifecycleState==`InService`]),
    Pending: length(Instances[?LifecycleState==`Pending`]),
    Terminating: length(Instances[?LifecycleState==`Terminating`])
  }'

# 스케일링 활동 이력 조회
aws autoscaling describe-scaling-activities \
  --auto-scaling-group-name "web-server-asg" \
  --max-items 10 \
  --query 'Activities[*].{Description: Description, StatusCode: StatusCode, StartTime: StartTime, Cause: Cause}'
```

### 사례 3: Warm Pool 설정

미리 초기화된 인스턴스를 대기 상태로 유지하여 Scale Out 시간을 단축합니다.

```bash
# Warm Pool 생성
aws autoscaling put-warm-pool \
  --auto-scaling-group-name "web-server-asg" \
  --pool-state Stopped \
  --min-size 2 \
  --max-group-prepared-capacity 5

# Warm Pool 상태 확인
aws autoscaling describe-warm-pool \
  --auto-scaling-group-name "web-server-asg"
```

## 모범 사례/보안

### 1. 다중 AZ 배포

- 최소 2개 이상의 가용 영역에 서브넷을 배포합니다.
- min-size를 AZ 수 이상으로 설정하여 각 AZ에 최소 1개 인스턴스를 유지합니다.

### 2. 헬스체크 설정

- ALB와 함께 사용하는 경우 반드시 `health-check-type`을 ELB로 설정합니다.
- `health-check-grace-period`를 애플리케이션 시작 시간보다 넉넉하게 설정합니다.

### 3. 보안 강화

```bash
# IMDSv2 필수 설정 (시작 템플릿에서)
# MetadataOptions.HttpTokens: "required"

# 인스턴스 프로파일에 최소 권한 IAM 역할 사용
# EBS 볼륨 암호화 활성화
```

### 4. 비용 최적화

- Spot 인스턴스 혼합으로 최대 70% 비용 절감이 가능합니다.
- Predictive Scaling으로 불필요한 Scale Out을 줄입니다.
- Scheduled Scaling으로 비수기 리소스를 선제적으로 축소합니다.

### 5. 모니터링 알림 설정

```bash
# ASG 알림 구성
aws autoscaling put-notification-configuration \
  --auto-scaling-group-name "web-server-asg" \
  --topic-arn "arn:aws:sns:ap-northeast-2:123456789012:asg-alerts" \
  --notification-types \
    "autoscaling:EC2_INSTANCE_LAUNCH" \
    "autoscaling:EC2_INSTANCE_LAUNCH_ERROR" \
    "autoscaling:EC2_INSTANCE_TERMINATE" \
    "autoscaling:EC2_INSTANCE_TERMINATE_ERROR"
```

## 관련 서비스 비교

| 항목 | EC2 Auto Scaling | ECS Service Auto Scaling | EKS + Karpenter | Lambda |
|------|-----------------|------------------------|----------------|--------|
| 대상 | EC2 인스턴스 | ECS 태스크 | Kubernetes Pod | 함수 |
| 확장 단위 | 인스턴스 | 태스크 | Pod + 노드 | 동시 실행 수 |
| 확장 속도 | 분 단위 (Warm Pool로 단축) | 초~분 단위 | 초~분 단위 | 밀리초 단위 |
| Spot 지원 | 예 (혼합 정책) | 예 (Fargate Spot) | 예 | N/A |
| Predictive Scaling | 예 | 미지원 | 미지원 | N/A |
| 복잡도 | 중간 | 낮음 | 높음 | 매우 낮음 |
| 커스터마이징 | 높음 | 중간 | 매우 높음 | 제한적 |

## 요약

Auto Scaling Group은 EC2 기반 워크로드의 탄력성과 비용 효율성을 확보하는 핵심 서비스입니다. 핵심 내용을 정리하면 다음과 같습니다.

- **시작 템플릿**: 인스턴스 구성을 버전 관리하며, IMDSv2, EBS 암호화 등 보안 설정을 포함합니다.
- **스케일링 정책**: Target Tracking(가장 추천), Step Scaling, Predictive Scaling, Scheduled Scaling 4가지 유형을 상황에 맞게 조합합니다.
- **혼합 인스턴스**: Spot과 온디맨드를 혼합하여 최대 70% 비용을 절감합니다.
- **수명 주기 후크**: 인스턴스 시작/종료 시 커스텀 작업(초기화, 로그 백업 등)을 수행합니다.
- **인스턴스 갱신**: 무중단으로 전체 인스턴스를 새 AMI/설정으로 교체합니다.
- **Warm Pool**: 미리 초기화된 인스턴스를 대기시켜 Scale Out 속도를 단축합니다.
- **다중 AZ**: 최소 2개 이상의 AZ에 배포하여 고가용성을 확보합니다.

ASG는 AWS에서 가장 많이 사용되는 서비스 중 하나이며, 올바른 설정 하나가 비용과 가용성 모두에 큰 영향을 미칩니다.