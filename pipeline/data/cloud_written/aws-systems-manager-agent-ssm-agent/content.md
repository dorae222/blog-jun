<!-- infographic-hero -->
![AWS Systems Manager Agent (SSM Agent) - 설치, 구성, 트러블슈팅 가이드 핵심 요약](figures/infographic.svg)

*Figure: AWS Systems Manager Agent (SSM Agent) - 설치, 구성, 트러블슈팅 가이드 한 장 요약 인포그래픽*

# AWS Systems Manager Agent (SSM Agent) - 설치, 구성, 트러블슈팅 가이드

## 개요

AWS Systems Manager Agent(SSM Agent)는 AWS Systems Manager 서비스가 EC2 인스턴스, 온프레미스 서버, 가상 머신과 통신하고 관리 작업을 실행할 수 있게 해주는 소프트웨어입니다. SSM Agent는 Systems Manager의 핵심 구성 요소로, Run Command, Session Manager, Patch Manager, Inventory, State Manager 등 모든 노드 관리 기능의 실행을 담당합니다.

SSM Agent는 인스턴스에서 백그라운드 서비스로 실행되며, SSM 서비스 엔드포인트와 HTTPS 아웃바운드 통신을 수행합니다. 인바운드 포트를 열 필요가 없으므로 SSH 기반 관리 방식보다 보안이 크게 강화됩니다.

Amazon Linux 2, Amazon Linux 2023, Ubuntu Server(16.04 이상), Windows Server(2012 이상) 등 주요 AMI에는 SSM Agent가 기본 설치되어 있습니다. 그러나 IAM 역할 구성, 네트워크 설정, 에이전트 업데이트 등 올바른 동작을 위한 추가 구성이 필요합니다.

## 핵심 기능

### 에이전트 역할 및 책임

| 기능 | SSM Agent 역할 |
|------|---------------|
| Run Command | 원격 명령 수신 및 로컬 실행, 결과 반환 |
| Session Manager | 대화형 셸 세션 중개, 세션 로그 전송 |
| Patch Manager | 패치 스캔 및 설치 실행 |
| Inventory | OS, 소프트웨어, 네트워크 정보 수집 및 전송 |
| State Manager | 원하는 상태(Association) 적용 및 유지 |
| Distributor | 소프트웨어 패키지 설치/제거 |

### 지원 운영체제

| OS | 버전 | 기본 설치 여부 |
|----|------|---------------|
| Amazon Linux 2 | 전체 | 기본 설치 |
| Amazon Linux 2023 | 전체 | 기본 설치 |
| Ubuntu Server | 16.04+ | 기본 설치 (일부 AMI) |
| RHEL | 7.x, 8.x, 9.x | 수동 설치 |
| CentOS | 7.x, 8.x | 수동 설치 |
| Windows Server | 2012+ | 기본 설치 |
| macOS | 11+ (M1/Intel) | 수동 설치 |
| Debian | 9+ | 수동 설치 |
| SUSE | 12 SP2+ | 수동 설치 |

### 통신 아키텍처

SSM Agent는 다음 세 가지 AWS 서비스 엔드포인트와 통신합니다.

- `ssm.{region}.amazonaws.com`: SSM API 엔드포인트 (명령, 파라미터, 문서)
- `ssmmessages.{region}.amazonaws.com`: Session Manager 웹소켓 통신
- `ec2messages.{region}.amazonaws.com`: Run Command 메시지 전달

모든 통신은 HTTPS(포트 443) 아웃바운드로 이루어지며, 인바운드 포트는 필요하지 않습니다.

## 아키텍처 및 동작 원리

SSM Agent의 동작 흐름은 다음과 같습니다.

```
[AWS Systems Manager Service]
    |   ^                    |
    |   | (결과 반환)          | (세션 데이터)
    v   |                    v
[ec2messages]          [ssmmessages]
    |                        |
    v                        v
[SSM Agent - 메시지 폴링]  [SSM Agent - WebSocket]
    |                        |
    +--------+-------+-------+
             |       |
     [Run Command] [Session Manager]
             |       |
     [로컬 명령 실행] [셸 세션 중개]
             |       |
             v       v
     [OS / 애플리케이션]
```

### 폴링 메커니즘

SSM Agent는 `ec2messages` 엔드포인트를 주기적으로 폴링하여 대기 중인 명령을 확인합니다. 기본 폴링 간격은 5초이며, 유휴 상태에서는 폴링 빈도가 감소합니다.

Session Manager의 경우 `ssmmessages` 엔드포인트와 WebSocket 연결을 유지하여 실시간 대화형 세션을 지원합니다.

### Managed Instance 등록

SSM Agent가 정상적으로 시작되면 Systems Manager에 Managed Instance로 자동 등록됩니다. EC2 인스턴스는 인스턴스 메타데이터와 IAM 역할을 통해 자동 인증되며, 온프레미스 서버는 Hybrid Activation을 통해 등록합니다.

## 실전 활용

### SSM Agent 설치 및 관리 (AWS CLI)

```bash
# SSM Agent 상태 확인 (Linux)
sudo systemctl status amazon-ssm-agent

# SSM Agent 상태 확인 (Windows PowerShell)
Get-Service AmazonSSMAgent

# SSM Agent 수동 설치 (Amazon Linux 2 / RHEL)
sudo yum install -y https://s3.ap-northeast-2.amazonaws.com/amazon-ssm-ap-northeast-2/latest/linux_amd64/amazon-ssm-agent.rpm
sudo systemctl enable amazon-ssm-agent
sudo systemctl start amazon-ssm-agent

# SSM Agent 수동 설치 (Ubuntu/Debian)
sudo snap install amazon-ssm-agent --classic
sudo systemctl enable snap.amazon-ssm-agent.amazon-ssm-agent.service
sudo systemctl start snap.amazon-ssm-agent.amazon-ssm-agent.service

# SSM Agent 자동 업데이트 설정 (State Manager 연동)
aws ssm create-association \
    --name "AWS-UpdateSSMAgent" \
    --targets '[{"Key":"InstanceIds","Values":["*"]}]' \
    --schedule-expression "rate(14 days)" \
    --association-name auto-update-ssm-agent

# Managed Instance 목록 확인
aws ssm describe-instance-information \
    --query 'InstanceInformationList[].{Id:InstanceId,Platform:PlatformType,PlatformVersion:PlatformVersion,AgentVersion:AgentVersion,Status:PingStatus,LastPing:LastPingDateTime}' \
    --output table

# 특정 인스턴스의 SSM Agent 버전 확인
aws ssm describe-instance-information \
    --filters 'Key=InstanceIds,Values=i-0abc123' \
    --query 'InstanceInformationList[0].{AgentVersion:AgentVersion,PingStatus:PingStatus}'
```

### IAM 역할 구성

```bash
# SSM 관리를 위한 IAM 역할 생성
aws iam create-role \
    --role-name SSMInstanceRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'

# 필수 관리형 정책 연결
aws iam attach-role-policy \
    --role-name SSMInstanceRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore

# (선택) CloudWatch Agent 연동 시
aws iam attach-role-policy \
    --role-name SSMInstanceRole \
    --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy

# 인스턴스 프로파일 생성 및 역할 연결
aws iam create-instance-profile --instance-profile-name SSMInstanceProfile
aws iam add-role-to-instance-profile \
    --instance-profile-name SSMInstanceProfile \
    --role-name SSMInstanceRole

# 기존 인스턴스에 프로파일 연결
aws ec2 associate-iam-instance-profile \
    --instance-id i-0abc123 \
    --iam-instance-profile Name=SSMInstanceProfile
```

### 온프레미스 서버 등록 (Hybrid Activation)

```bash
# Hybrid Activation 생성
aws ssm create-activation \
    --default-instance-name "on-prem-server" \
    --iam-role "SSMServiceRole" \
    --registration-limit 10 \
    --expiration-date "2024-12-31" \
    --tags '[{"Key":"Environment","Value":"production"}]'

# 반환된 ActivationId와 ActivationCode로 에이전트 등록 (온프레미스 서버에서 실행)
sudo amazon-ssm-agent -register \
    -code "activation-code" \
    -id "activation-id" \
    -region "ap-northeast-2"
sudo systemctl restart amazon-ssm-agent
```

### VPC Endpoint 구성 (프라이빗 서브넷)

```bash
# SSM Agent가 필요로 하는 3개의 VPC Endpoint 생성
for service in ssm ssmmessages ec2messages; do
    aws ec2 create-vpc-endpoint \
        --vpc-id vpc-0abc123 \
        --service-name com.amazonaws.ap-northeast-2.${service} \
        --vpc-endpoint-type Interface \
        --subnet-ids subnet-0abc123 subnet-0def456 \
        --security-group-ids sg-0abc123 \
        --private-dns-enabled
    echo "Created endpoint for ${service}"
done

# (선택) S3 Gateway Endpoint (패치 다운로드, 에이전트 업데이트용)
aws ec2 create-vpc-endpoint \
    --vpc-id vpc-0abc123 \
    --service-name com.amazonaws.ap-northeast-2.s3 \
    --vpc-endpoint-type Gateway \
    --route-table-ids rtb-0abc123
```

### 트러블슈팅

```bash
# SSM Agent 로그 확인 (Linux)
sudo tail -50 /var/log/amazon/ssm/amazon-ssm-agent.log
sudo tail -50 /var/log/amazon/ssm/errors.log

# SSM Agent 로그 확인 (Windows)
Get-Content "C:\ProgramData\Amazon\SSM\Logs\amazon-ssm-agent.log" -Tail 50

# 연결 테스트 (필요한 엔드포인트 접근 확인)
for endpoint in ssm ssmmessages ec2messages; do
    curl -s -o /dev/null -w "%{http_code}" \
        https://${endpoint}.ap-northeast-2.amazonaws.com
    echo " - ${endpoint}"
done

# SSM Agent 재시작
sudo systemctl restart amazon-ssm-agent
```

## 모범 사례 및 보안

### 에이전트 관리

- SSM Agent 자동 업데이트를 State Manager Association으로 설정하여 항상 최신 버전을 유지합니다.
- 에이전트 로그를 CloudWatch Logs로 전송하여 중앙에서 모니터링합니다.
- Managed Instance 목록을 정기적으로 확인하여 비활성 인스턴스를 식별합니다.

### 보안

- `AmazonSSMManagedInstanceCore` 정책만 연결하고, 추가 권한은 커스텀 정책으로 최소한만 부여합니다.
- Session Manager 세션 로그를 S3와 CloudWatch Logs에 저장하여 감사 추적을 확보합니다.
- SSH 포트(22)와 RDP 포트(3389)를 보안 그룹에서 차단하고 Session Manager만 사용합니다.
- 프라이빗 서브넷의 인스턴스는 VPC Endpoint를 통해 SSM에 접근합니다.

### 네트워크 요구사항 체크리스트

- HTTPS(443) 아웃바운드 허용
- ssm, ssmmessages, ec2messages 엔드포인트 접근 가능
- S3 엔드포인트 접근 가능 (패치 다운로드, 에이전트 업데이트)
- 프라이빗 서브넷: VPC Endpoint 또는 NAT Gateway 필요
- 프록시 환경: SSM Agent 프록시 설정 필요

## 관련 서비스 비교

| 항목 | SSM Agent | CloudWatch Agent | CodeDeploy Agent | Inspector Agent |
|------|-----------|-----------------|-----------------|----------------|
| 목적 | 원격 관리 전반 | 메트릭/로그 수집 | 애플리케이션 배포 | 보안 취약점 스캔 |
| 통신 방식 | HTTPS Polling + WebSocket | HTTPS Push | HTTPS Polling | HTTPS Push |
| IAM 정책 | SSMManagedInstanceCore | CloudWatchAgentServerPolicy | 커스텀 | InspectorAccess |
| 기본 설치 | Amazon Linux 2+ | 수동 | 수동 | 수동 |
| 인바운드 포트 | 불필요 | 불필요 | 불필요 | 불필요 |

## 요약

SSM Agent는 AWS Systems Manager의 모든 노드 관리 기능(Run Command, Session Manager, Patch Manager, Inventory 등)을 실행하는 핵심 에이전트입니다. HTTPS 아웃바운드 통신만 사용하므로 인바운드 포트를 열 필요가 없어 보안이 강화되며, Amazon Linux 2 이상의 주요 AMI에 기본 설치되어 있습니다. 올바른 동작을 위해 IAM 역할(AmazonSSMManagedInstanceCore), 네트워크 접근(ssm, ssmmessages, ec2messages 엔드포인트), 에이전트 업데이트 자동화를 구성해야 합니다. 온프레미스 서버는 Hybrid Activation을 통해 등록하여 동일한 방식으로 관리할 수 있습니다.