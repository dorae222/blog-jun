## 개요

Amazon EC2 Mac 인스턴스는 Apple Mac mini 하드웨어를 AWS Nitro 시스템에 통합하여 macOS 워크로드를 클라우드에서 실행할 수 있게 하는 서비스입니다. 2020년 Intel Mac mini 기반 `mac1.metal` 인스턴스를 시작으로, 2022년에는 Apple Silicon M1 기반 `mac2.metal` 인스턴스가, 이후 M2 기반 `mac2-m2.metal`, M2 Pro 기반 `mac2-m2pro.metal` 인스턴스가 출시되었습니다.

iOS, macOS, watchOS, tvOS 앱을 개발하는 조직에서는 Xcode 빌드, 테스트, 서명 작업을 수행할 macOS 환경이 필수적입니다. 기존에는 물리적 Mac 장비를 구매하고 관리해야 했지만, EC2 Mac 인스턴스를 사용하면 필요한 만큼의 macOS 빌드 환경을 클라우드에서 탄력적으로 운영할 수 있습니다.

본 글에서는 M1 Mac 인스턴스를 중심으로, 아키텍처, 실전 활용, CI/CD 파이프라인 구축, 그리고 비용 최적화 전략까지 상세히 다루겠습니다.

## 핵심 기능

### EC2 Mac 인스턴스 유형

| 인스턴스 유형 | 칩 | CPU 코어 | 메모리 | 스토리지 | 네트워크 |
|-------------|-----|---------|--------|---------|--------|
| mac1.metal | Intel i7 (8세대) | 12 vCPU | 32 GiB | EBS Only | 10 Gbps |
| mac2.metal | Apple M1 | 8 코어 (4P+4E) | 16 GiB | EBS Only | 10 Gbps |
| mac2-m2.metal | Apple M2 | 8 코어 (4P+4E) | 24 GiB | EBS Only | 10 Gbps |
| mac2-m2pro.metal | Apple M2 Pro | 12 코어 (8P+4E) | 32 GiB | EBS Only | 10 Gbps |

M1 Mac 인스턴스(`mac2.metal`)는 Apple Silicon의 뛰어난 성능 대비 전력 효율을 클라우드 환경에서 활용할 수 있습니다. Xcode 빌드 속도가 Intel 기반 `mac1.metal` 대비 최대 60% 향상됩니다.

### Dedicated Host 기반 운영

EC2 Mac 인스턴스는 반드시 **Dedicated Host** 위에서 실행됩니다. 이는 Apple의 macOS 라이선스 조건 때문입니다.

```bash
# Mac Dedicated Host 할당
aws ec2 allocate-hosts \
  --instance-type mac2.metal \
  --availability-zone ap-northeast-2a \
  --quantity 1 \
  --tag-specifications 'ResourceType=dedicated-host,Tags=[{Key=Name,Value=mac-m1-host-1},{Key=Purpose,Value=iOS-CI}]'
```

중요한 제약사항으로, **Mac Dedicated Host의 최소 할당 기간은 24시간**입니다. 24시간 이전에는 호스트를 해제할 수 없으므로 비용 계획 시 이를 반드시 고려해야 합니다.

```bash
# Dedicated Host 상태 확인
aws ec2 describe-hosts \
  --filter "Name=instance-type,Values=mac2.metal" \
  --query 'Hosts[*].{
    HostId: HostId,
    State: State,
    AZ: AvailabilityZone,
    InstanceType: Instances[0].InstanceType,
    InstanceId: Instances[0].InstanceId,
    AllocationTime: AllocationTime
  }' \
  --output table
```

### macOS AMI

AWS는 다양한 macOS 버전의 AMI를 제공합니다.

```bash
# 사용 가능한 macOS AMI 조회 (M1용 arm64)
aws ec2 describe-images \
  --owners amazon \
  --filters \
    "Name=name,Values=amzn-ec2-macos-14*" \
    "Name=architecture,Values=arm64_mac" \
  --query 'Images[*].{Name: Name, ImageId: ImageId, CreationDate: CreationDate}' \
  --output table

# 특정 macOS 버전 AMI 조회
aws ec2 describe-images \
  --owners amazon \
  --filters \
    "Name=name,Values=*macos-sonoma*" \
    "Name=architecture,Values=arm64_mac" \
  --query 'sort_by(Images, &CreationDate)[-1].{Name: Name, ImageId: ImageId}'
```

### 인스턴스 시작 및 접속

```bash
# Mac 인스턴스 시작 (Dedicated Host 지정)
aws ec2 run-instances \
  --image-id ami-0abc123def456789 \
  --instance-type mac2.metal \
  --placement HostId=h-0abc123def456789 \
  --key-name my-mac-keypair \
  --security-group-ids sg-abc123 \
  --subnet-id subnet-abc123 \
  --block-device-mappings '[{
    "DeviceName": "/dev/sda1",
    "Ebs": {
      "VolumeSize": 200,
      "VolumeType": "gp3",
      "Iops": 6000,
      "Throughput": 400
    }
  }]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=mac-m1-builder}]'

# SSH 접속
# ssh -i my-mac-keypair.pem ec2-user@<public-ip>

# VNC를 통한 GUI 접속 (원격 데스크톱)
# ssh -i my-mac-keypair.pem -L 5900:localhost:5900 ec2-user@<public-ip>
# 이후 VNC 클라이언트로 localhost:5900 접속
```

## 아키텍처/동작 원리

### Nitro 시스템과 Mac mini 통합

```
[AWS Nitro System]
  ├── Nitro Card (네트워크) <──> Thunderbolt 연결 <──> [Mac mini M1]
  ├── Nitro Card (EBS)     <──> Thunderbolt 연결 <──>    ├── Apple M1 SoC
  ├── Nitro Security Chip                                ├── 16 GB 통합 메모리
  └── Nitro Hypervisor                                   └── macOS
```

EC2 Mac 인스턴스는 물리적 Mac mini를 Thunderbolt 연결을 통해 AWS Nitro 시스템에 연결하는 구조입니다. Nitro 카드가 VPC 네트워킹과 EBS 스토리지를 처리하므로, Mac mini는 일반 EC2 인스턴스처럼 VPC 내에서 동작합니다.

중요한 특징은 **Bare Metal 인스턴스**라는 점입니다. 가상화 레이어 없이 Mac mini 하드웨어에 직접 접근하므로, macOS와 Xcode가 네이티브 성능으로 동작합니다.

### 부팅 및 초기화 프로세스

1. Dedicated Host에 Mac mini가 할당됩니다.
2. EBS 볼륨에서 macOS AMI가 로드됩니다.
3. Nitro 시스템이 네트워크 인터페이스와 EBS 연결을 구성합니다.
4. macOS가 부팅되고, EC2 Launch 에이전트가 메타데이터를 설정합니다.
5. SSH 접속이 가능해집니다.

Mac 인스턴스의 부팅 시간은 일반 EC2 인스턴스보다 길 수 있습니다 (약 6-15분). 이는 macOS의 부팅 과정과 내부 디스크 크기 조정 때문입니다.

### 인스턴스 중지 및 종료 시 동작

인스턴스 중지 시 내부적으로 macOS의 완전한 정리(scrub) 과정이 수행됩니다. 이전 사용자의 데이터가 남지 않도록 보장하기 위한 것으로, 인스턴스 재시작에 약 15-25분이 소요될 수 있습니다.

```bash
# 인스턴스 중지
aws ec2 stop-instances --instance-ids i-0abc123def456789

# 인스턴스 종료 (Dedicated Host 해제 전 필수)
aws ec2 terminate-instances --instance-ids i-0abc123def456789

# Dedicated Host 해제 (24시간 경과 후 가능)
aws ec2 release-hosts --host-ids h-0abc123def456789
```

## 실전 활용

### 사례 1: iOS CI/CD 빌드 파이프라인 구축

GitHub Actions 또는 Jenkins와 연동하여 iOS 앱 빌드 파이프라인을 구축하는 패턴입니다.

```bash
# 1. 빌드 환경 구성을 위한 사용자 데이터 스크립트 준비
# user-data.sh 예시:
# #!/bin/bash
# # Homebrew 설치
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
# # 빌드 도구 설치
# brew install fastlane cocoapods
# # Xcode Command Line Tools 확인
# xcode-select --install 2>/dev/null || true

# 2. 커스텀 AMI 생성 (빌드 도구가 사전 설치된)
aws ec2 create-image \
  --instance-id i-0abc123def456789 \
  --name "mac-m1-ios-builder-v1" \
  --description "iOS build environment with Xcode 15, Fastlane, CocoaPods" \
  --no-reboot

# 3. AMI 생성 상태 확인
aws ec2 describe-images \
  --image-ids ami-newimage123 \
  --query 'Images[0].State'
```

### 사례 2: Auto Scaling 유사 패턴 구현

Mac 인스턴스는 Auto Scaling Group을 직접 지원하지 않지만, Lambda와 EventBridge를 활용하여 유사한 패턴을 구현할 수 있습니다.

```bash
# 업무 시간에 Mac 인스턴스 시작 (EventBridge 스케줄)
aws events put-rule \
  --name "start-mac-builders" \
  --schedule-expression "cron(0 0 ? * MON-FRI *)" \
  --description "월-금 오전 9시(KST)에 Mac 빌드 서버 시작"

# 업무 종료 후 인스턴스 중지
aws events put-rule \
  --name "stop-mac-builders" \
  --schedule-expression "cron(0 12 ? * MON-FRI *)" \
  --description "월-금 오후 9시(KST)에 Mac 빌드 서버 중지"

# Lambda 함수를 타겟으로 설정
aws events put-targets \
  --rule "start-mac-builders" \
  --targets '[{"Id": "start-lambda", "Arn": "arn:aws:lambda:ap-northeast-2:123456789012:function:manage-mac-instances"}]'
```

### 사례 3: EBS 볼륨 최적화

Xcode 프로젝트 빌드는 디스크 I/O가 집중적이므로 EBS 볼륨 성능이 중요합니다.

```bash
# 고성능 gp3 볼륨으로 교체
aws ec2 create-volume \
  --availability-zone ap-northeast-2a \
  --volume-type gp3 \
  --size 500 \
  --iops 10000 \
  --throughput 500 \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=mac-build-volume}]'

# 기존 볼륨 성능 수정
aws ec2 modify-volume \
  --volume-id vol-abc123 \
  --volume-type gp3 \
  --iops 10000 \
  --throughput 500
```

### 사례 4: Systems Manager를 활용한 원격 관리

```bash
# SSM Agent 설치 확인 (macOS에서)
# Mac 인스턴스에는 기본적으로 SSM Agent가 포함되어 있음

# SSM을 통한 원격 명령 실행
aws ssm send-command \
  --instance-ids i-0abc123def456789 \
  --document-name "AWS-RunShellScript" \
  --parameters '{"commands": ["sw_vers", "xcodebuild -version", "system_profiler SPHardwareDataType"]}'

# 명령 결과 확인
aws ssm get-command-invocation \
  --command-id "cmd-abc123" \
  --instance-id i-0abc123def456789
```

### 사례 5: 비용 최적화를 위한 Savings Plans

```bash
# Mac 인스턴스 사용량 조회
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" "UsageQuantity" \
  --filter '{
    "Dimensions": {
      "Key": "INSTANCE_TYPE",
      "Values": ["mac2.metal"]
    }
  }'

# Dedicated Host 예약 (1년 또는 3년)
aws ec2 purchase-host-reservation \
  --host-id-set h-0abc123def456789 \
  --offering-id hro-abc123
```

## 모범 사례/보안

### 1. AMI 관리 전략

- Xcode, CocoaPods, Fastlane 등 빌드 도구가 사전 설치된 Golden AMI를 주기적으로 생성합니다.
- macOS 보안 업데이트가 나올 때마다 AMI를 갱신합니다.
- AMI에 민감한 인증서나 프로비저닝 프로파일을 포함하지 않습니다. AWS Secrets Manager에서 런타임에 가져오는 방식을 사용합니다.

### 2. 보안 구성

```bash
# Mac 인스턴스 전용 보안 그룹
aws ec2 create-security-group \
  --group-name "mac-builder-sg" \
  --description "Security group for Mac build instances" \
  --vpc-id vpc-abc123

# SSH만 허용 (특정 CIDR)
aws ec2 authorize-security-group-ingress \
  --group-id sg-mac123 \
  --protocol tcp \
  --port 22 \
  --cidr 10.0.0.0/8

# VNC는 SSH 터널링으로만 접근 (직접 노출 금지)
```

### 3. 24시간 최소 할당 관리

- Dedicated Host는 24시간 전에 해제할 수 없으므로, 가능한 한 인스턴스를 중지(stop)하되 호스트는 유지하는 방식으로 운영합니다.
- 지속적으로 사용하는 경우 Dedicated Host Reservation을 구매하여 비용을 절감합니다.
- 1년 예약 시 약 33%, 3년 예약 시 약 54% 비용 절감이 가능합니다.

### 4. 모니터링

```bash
# CloudWatch 메트릭 확인
aws cloudwatch get-metric-data \
  --metric-data-queries '[{
    "Id": "cpu",
    "MetricStat": {
      "Metric": {
        "Namespace": "AWS/EC2",
        "MetricName": "CPUUtilization",
        "Dimensions": [{"Name": "InstanceId", "Value": "i-0abc123def456789"}]
      },
      "Period": 300,
      "Stat": "Average"
    }
  }]' \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z
```

## 관련 서비스 비교

| 항목 | EC2 Mac (M1) | EC2 Mac (Intel) | MacStadium | GitHub Actions (macOS) |
|------|-------------|----------------|------------|----------------------|
| 하드웨어 | Apple M1 | Intel i7 8세대 | M1/M2/M1 Ultra | Apple Silicon |
| Xcode 빌드 속도 | 매우 빠름 | 보통 | 매우 빠름 | 빠름 |
| 최소 할당 | 24시간 | 24시간 | 월 단위 | 분 단위 |
| AWS 서비스 연동 | 네이티브 | 네이티브 | 제한적 | GitHub 연동 |
| 가격 모델 | 시간당 과금 | 시간당 과금 | 월 정액 | 분당 과금 |
| 커스터마이징 | 완전한 제어 | 완전한 제어 | 완전한 제어 | 제한적 |
| 네트워크 | VPC 통합 | VPC 통합 | 독립 네트워크 | GitHub 네트워크 |
| 적합한 용도 | 대규모 CI/CD | 레거시 빌드 | 전용 인프라 | 소규모 프로젝트 |

## 요약

Amazon EC2 M1 Mac 인스턴스는 Apple Silicon의 강력한 성능을 AWS 클라우드 인프라와 결합한 서비스입니다. 핵심 내용을 정리하면 다음과 같습니다.

- **Apple M1 네이티브 성능**: Bare Metal 인스턴스로 가상화 오버헤드 없이 macOS와 Xcode가 네이티브로 동작합니다.
- **Nitro 시스템 통합**: VPC 네트워킹, EBS 스토리지 등 AWS 인프라와 완전히 통합됩니다.
- **Dedicated Host 필수**: Apple 라이선스 요구사항으로 Dedicated Host 위에서만 운영 가능하며, 최소 24시간 할당이 필요합니다.
- **iOS CI/CD**: Xcode 빌드, 테스트, 서명 작업을 클라우드에서 탄력적으로 수행할 수 있습니다.
- **비용 최적화**: Host Reservation(1년/3년)을 통해 최대 54%까지 비용을 절감할 수 있습니다.
- **인스턴스 유형 진화**: mac1.metal(Intel) -> mac2.metal(M1) -> mac2-m2.metal(M2) -> mac2-m2pro.metal(M2 Pro)로 지속적으로 발전하고 있습니다.
- **주의사항**: 부팅 시간이 길고(6-15분), 인스턴스 재시작 시 정리 작업으로 15-25분 소요될 수 있습니다.

macOS 기반 워크로드를 AWS에서 운영해야 하는 조직에게 EC2 Mac 인스턴스는 유일하면서도 매우 강력한 선택지입니다.