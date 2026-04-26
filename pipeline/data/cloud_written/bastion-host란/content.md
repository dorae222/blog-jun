<!-- infographic-hero -->
![Bastion Host 완벽 가이드: AWS 환경에서의 안전한 원격 접속 전략 핵심 요약](figures/infographic.svg)

*Figure: Bastion Host 완벽 가이드: AWS 환경에서의 안전한 원격 접속 전략 한 장 요약 인포그래픽*

## 개요

Bastion Host(배스천 호스트, 점프 박스라고도 합니다)는 퍼블릭 네트워크에서 프라이빗 네트워크에 있는 리소스에 안전하게 접근하기 위한 중간 서버입니다. 네트워크 보안에서 "관문(Gateway)" 역할을 수행하며, 모든 원격 접속 트래픽이 이 서버를 경유하도록 강제합니다.

AWS 환경에서 프라이빗 서브넷에 배치된 EC2 인스턴스, RDS 데이터베이스, ElastiCache 등에 직접 접근하는 것은 불가능합니다. 이때 퍼블릭 서브넷에 Bastion Host를 배치하여 SSH(Linux) 또는 RDP(Windows) 터널링을 통해 프라이빗 리소스에 접근합니다.

### Bastion Host를 사용하는 이유

- **네트워크 격리**: 프라이빗 서브넷의 리소스를 인터넷에 직접 노출하지 않습니다.
- **접근 제어**: 모든 원격 접속을 단일 진입점에서 제어하고 감사합니다.
- **공격 표면 최소화**: SSH/RDP 포트를 인터넷에 직접 노출하는 인스턴스 수를 줄입니다.
- **감사 로깅**: Bastion Host를 통한 모든 접속 이력을 기록합니다.

## 핵심 기능

### Bastion Host 아키텍처

```
                Internet
                   |
          +--------+--------+
          |  Internet GW    |
          +--------+--------+
                   |
     +-------------+-------------+
     |        Public Subnet      |
     |  +---------------------+  |
     |  |    Bastion Host     |  |
     |  |  (SSH: Port 22)     |  |
     |  |  SG: 22 from MyIP   |  |
     |  +----------+----------+  |
     +-------------+-------------+
                   |
     +-------------+-------------+
     |       Private Subnet      |
     |  +--------+  +--------+   |
     |  | EC2    |  | RDS    |   |
     |  | App    |  | DB     |   |
     |  | Server |  |        |   |
     |  +--------+  +--------+   |
     |  SG: 22 from Bastion SG   |
     +---------------------------+
```

### EC2 기반 Bastion Host 구축

```bash
# 1. Bastion Host용 보안 그룹 생성
BAST_SG=$(aws ec2 create-security-group \
  --group-name bastion-sg \
  --description "Bastion Host Security Group" \
  --vpc-id vpc-0a1b2c3d4e5f6g7h8 \
  --query 'GroupId' \
  --output text)

# SSH 접근 허용 (관리자 IP만)
aws ec2 authorize-security-group-ingress \
  --group-id $BAST_SG \
  --protocol tcp \
  --port 22 \
  --cidr 203.0.113.50/32

# 2. 프라이빗 인스턴스 보안 그룹에 Bastion SG에서의 SSH 허용
aws ec2 authorize-security-group-ingress \
  --group-id sg-private-instances \
  --protocol tcp \
  --port 22 \
  --source-group $BAST_SG

# 3. Bastion Host EC2 인스턴스 생성
aws ec2 run-instances \
  --image-id ami-0a1b2c3d4e5f6g7h8 \
  --instance-type t3.micro \
  --key-name my-bastion-key \
  --subnet-id subnet-public-a \
  --security-group-ids $BAST_SG \
  --associate-public-ip-address \
  --iam-instance-profile Name=BastionHostRole \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=bastion-host},{Key=Environment,Value=Production}]' \
  --user-data '#!/bin/bash
yum update -y
yum install -y amazon-cloudwatch-agent
# SSH 세션 로깅 설정
echo "ForceCommand /usr/bin/script -q -a /var/log/ssh-sessions/\$(date +%Y%m%d_%H%M%S)_\${USER}.log" >> /etc/ssh/sshd_config
mkdir -p /var/log/ssh-sessions
systemctl restart sshd'

# 4. Elastic IP 할당 (고정 IP)
EIP_ALLOC=$(aws ec2 allocate-address \
  --domain vpc \
  --query 'AllocationId' \
  --output text)

aws ec2 associate-address \
  --instance-id i-bastion123 \
  --allocation-id $EIP_ALLOC
```

### SSH 터널링을 통한 프라이빗 리소스 접근

Bastion Host를 통해 프라이빗 리소스에 접근하는 방법입니다.

```bash
# 방법 1: SSH ProxyJump (권장)
ssh -J ec2-user@bastion.example.com ec2-user@10.0.1.100

# 방법 2: SSH 포트 포워딩 (RDS 접근)
ssh -L 3306:mydb.cluster-abc123.ap-northeast-2.rds.amazonaws.com:3306 \
  ec2-user@bastion.example.com

# 로컬에서 RDS에 접속 (다른 터미널)
mysql -h 127.0.0.1 -P 3306 -u admin -p

# 방법 3: SSH Config 파일 활용 (~/.ssh/config)
```

SSH Config 파일을 설정하면 편리하게 접속할 수 있습니다.

```bash
# ~/.ssh/config
Host bastion
    HostName 54.180.100.50
    User ec2-user
    IdentityFile ~/.ssh/bastion-key.pem
    ForwardAgent yes

Host private-app
    HostName 10.0.1.100
    User ec2-user
    IdentityFile ~/.ssh/app-key.pem
    ProxyJump bastion

Host private-db
    HostName 10.0.2.50
    User ec2-user
    IdentityFile ~/.ssh/db-key.pem
    ProxyJump bastion
    LocalForward 3306 mydb.cluster-abc123.ap-northeast-2.rds.amazonaws.com:3306
```

```bash
# 간편하게 접속
ssh private-app
ssh private-db  # RDS 포트 포워딩도 자동 설정
```

### Auto Scaling 기반 고가용성 Bastion Host

프로덕션 환경에서는 Auto Scaling Group을 사용하여 Bastion Host의 가용성을 보장합니다.

```bash
# Launch Template 생성
aws ec2 create-launch-template \
  --launch-template-name bastion-template \
  --launch-template-data '{
    "ImageId": "ami-0a1b2c3d4e5f6g7h8",
    "InstanceType": "t3.micro",
    "KeyName": "bastion-key",
    "SecurityGroupIds": ["sg-bastion-abc123"],
    "IamInstanceProfile": {"Name": "BastionHostRole"},
    "TagSpecifications": [{
      "ResourceType": "instance",
      "Tags": [{"Key": "Name", "Value": "bastion-host"}]
    }],
    "UserData": "IyEvYmluL2Jhc2gKeXVtIHVwZGF0ZSAteQ=="
  }'

# Auto Scaling Group 생성 (최소 1대 유지)
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name bastion-asg \
  --launch-template LaunchTemplateName=bastion-template,Version='$Latest' \
  --min-size 1 \
  --max-size 1 \
  --desired-capacity 1 \
  --vpc-zone-identifier subnet-public-a,subnet-public-c \
  --tags Key=Name,Value=bastion-host,PropagateAtLaunch=true
```

## 아키텍처/동작 원리

### Bastion Host의 보안 계층

Bastion Host를 통한 접근 제어는 여러 계층에서 이루어집니다.

| 계층 | 구성 요소 | 역할 |
|------|----------|------|
| 네트워크 | Security Group | IP/포트 기반 접근 제어 |
| 네트워크 | NACL | 서브넷 수준 접근 제어 |
| 인증 | SSH Key Pair | 키 기반 인증 |
| 인가 | IAM (Instance Connect) | AWS 자격 증명 기반 접근 제어 |
| 감사 | CloudTrail + CloudWatch | 접속 이력 기록 |
| 시스템 | OS 수준 보안 | SSH 설정, 방화벽, 패치 |

### SSH Agent Forwarding vs ProxyJump

**SSH Agent Forwarding** (`-A` 옵션)

SSH Agent Forwarding을 사용하면 Bastion Host에 Private Key를 저장하지 않고도 프라이빗 인스턴스에 접근할 수 있습니다. 하지만 Bastion Host가 침해된 경우 SSH Agent를 통해 다른 서버에도 접근이 가능하므로 보안 위험이 있습니다.

**ProxyJump** (`-J` 옵션, 권장)

ProxyJump는 SSH Agent Forwarding의 보안 문제를 해결합니다. SSH 연결이 Bastion Host를 통해 직접 터널링되므로, Bastion Host에서 SSH Agent에 접근할 수 없습니다.

```bash
# ProxyJump 사용 (권장)
ssh -J bastion-user@bastion:22 app-user@10.0.1.100

# Agent Forwarding 사용 (보안 주의)
ssh -A bastion-user@bastion
# bastion에서
ssh app-user@10.0.1.100
```

## 실전 활용

### Bastion Host 보안 강화

```bash
# Bastion Host SSH 보안 설정 (/etc/ssh/sshd_config)
```

```yaml
# sshd_config 주요 설정
Port 22
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
MaxSessions 5
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers ec2-user
LogLevel VERBOSE
Banner /etc/ssh/banner
```

```bash
# SSH 배너 설정
echo "WARNING: Authorized access only. All activities are logged and monitored." > /etc/ssh/banner

# SSH 서비스 재시작
sudo systemctl restart sshd
```

### CloudWatch를 통한 SSH 접속 모니터링

```bash
# CloudWatch Logs Agent 설정으로 SSH 로그 전송
# /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/secure",
            "log_group_name": "/bastion/ssh-access",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          },
          {
            "file_path": "/var/log/ssh-sessions/*.log",
            "log_group_name": "/bastion/ssh-sessions",
            "log_stream_name": "{instance_id}",
            "timezone": "UTC"
          }
        ]
      }
    }
  }
}
```

```bash
# CloudWatch 메트릭 필터 생성 (SSH 실패 로그인 감지)
aws logs put-metric-filter \
  --log-group-name /bastion/ssh-access \
  --filter-name SSHFailedLogin \
  --filter-pattern '"Failed password"' \
  --metric-transformations \
    metricName=SSHFailedLogins,metricNamespace=BastionHost,metricValue=1

# SSH 실패 로그인 경보
aws cloudwatch put-metric-alarm \
  --alarm-name BastionSSHFailedLogins \
  --metric-name SSHFailedLogins \
  --namespace BastionHost \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:security-alerts
```

### EC2 Instance Connect

EC2 Instance Connect는 Bastion Host의 현대적 대안 중 하나입니다. IAM 정책을 통해 SSH 접근을 제어하고, 임시 SSH 키를 사용합니다.

```bash
# EC2 Instance Connect로 접속
aws ec2-instance-connect send-ssh-public-key \
  --instance-id i-0a1b2c3d4e5f6g7h8 \
  --instance-os-user ec2-user \
  --ssh-public-key file://~/.ssh/id_rsa.pub \
  --availability-zone ap-northeast-2a

# 60초 이내에 SSH 접속
ssh ec2-user@10.0.1.100

# 또는 AWS CLI로 직접 접속
aws ec2-instance-connect ssh \
  --instance-id i-0a1b2c3d4e5f6g7h8
```

EC2 Instance Connect Endpoint를 사용하면 프라이빗 서브넷의 인스턴스에도 Bastion Host 없이 접근할 수 있습니다.

```bash
# EC2 Instance Connect Endpoint 생성
aws ec2 create-instance-connect-endpoint \
  --subnet-id subnet-private-a \
  --security-group-ids sg-eice-abc123 \
  --tags Key=Name,Value=my-eice

# Endpoint를 통해 프라이빗 인스턴스에 접속
aws ec2-instance-connect ssh \
  --instance-id i-private-abc123 \
  --connection-type eice
```

### AWS Systems Manager Session Manager

Session Manager는 Bastion Host를 완전히 대체할 수 있는 AWS 관리형 서비스입니다.

```bash
# Session Manager로 접속 (SSH 포트 열 필요 없음)
aws ssm start-session \
  --target i-0a1b2c3d4e5f6g7h8

# Session Manager를 통한 포트 포워딩 (RDS 접근)
aws ssm start-session \
  --target i-0a1b2c3d4e5f6g7h8 \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{
    "host": ["mydb.cluster-abc123.ap-northeast-2.rds.amazonaws.com"],
    "portNumber": ["3306"],
    "localPortNumber": ["3306"]
  }'

# Session Manager 설정 (세션 로깅)
aws ssm update-document \
  --name SSM-SessionManagerRunShell \
  --document-version '$LATEST' \
  --content '{
    "schemaVersion": "1.0",
    "description": "Session Manager Settings",
    "sessionType": "Standard_Stream",
    "inputs": {
      "cloudWatchLogGroupName": "/aws/ssm/sessions",
      "cloudWatchEncryptionEnabled": true,
      "s3BucketName": "my-session-logs-bucket",
      "s3EncryptionEnabled": true,
      "idleSessionTimeout": "20",
      "maxSessionDuration": "60",
      "kmsKeyId": "arn:aws:kms:ap-northeast-2:123456789012:key/abc123"
    }
  }'
```

Session Manager의 장점은 다음과 같습니다.

- SSH 키 관리가 필요 없습니다.
- 인바운드 포트를 열 필요가 없습니다 (보안 그룹에서 SSH 허용 불필요).
- IAM 정책으로 접근을 제어합니다.
- 모든 세션이 CloudTrail에 기록됩니다.
- CloudWatch Logs 또는 S3로 세션 로그를 저장합니다.

```bash
# Session Manager용 IAM 정책
aws iam create-policy \
  --policy-name SessionManagerAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "ssm:StartSession"
        ],
        "Resource": [
          "arn:aws:ec2:ap-northeast-2:123456789012:instance/*"
        ],
        "Condition": {
          "StringLike": {
            "ssm:resourceTag/Environment": ["Development", "Staging"]
          }
        }
      },
      {
        "Effect": "Allow",
        "Action": [
          "ssm:TerminateSession",
          "ssm:ResumeSession"
        ],
        "Resource": "arn:aws:ssm:*:*:session/${aws:username}-*"
      }
    ]
  }'
```

## 모범 사례/보안

### Bastion Host 보안 체크리스트

1. **최소 접근**: 보안 그룹에서 관리자 IP만 SSH 접근을 허용합니다.
2. **키 관리**: SSH 키를 정기적으로 교체하고, SSH Agent Forwarding 대신 ProxyJump를 사용합니다.
3. **패치 관리**: Bastion Host의 OS와 패키지를 항상 최신 상태로 유지합니다.
4. **세션 로깅**: 모든 SSH 세션을 기록하고 CloudWatch Logs로 전송합니다.
5. **MFA 적용**: SSH 접속 시 MFA(Multi-Factor Authentication)를 적용합니다.
6. **불필요한 소프트웨어 제거**: Bastion Host에는 SSH 접속에 필요한 최소한의 소프트웨어만 설치합니다.
7. **자동 종료**: 업무 시간 외에는 Bastion Host를 중지하여 공격 표면을 줄입니다.

```bash
# 업무 시간 외 Bastion Host 자동 중지 (EventBridge + Lambda)
aws events put-rule \
  --name StopBastionAfterHours \
  --schedule-expression 'cron(0 19 ? * MON-FRI *)' \
  --description "Stop bastion host after business hours"

aws events put-rule \
  --name StartBastionBusinessHours \
  --schedule-expression 'cron(0 8 ? * MON-FRI *)' \
  --description "Start bastion host during business hours"
```

### 현대적 대안 선택 가이드

| 시나리오 | 권장 솔루션 |
|---------|----------|
| 단순 SSH 접근 (프라이빗 인스턴스) | EC2 Instance Connect Endpoint |
| 포트 포워딩 (RDS, Redis 접근) | Session Manager 포트 포워딩 |
| 감사/규정 준수 필수 | Session Manager (세션 로깅) |
| 레거시 SSH 기반 워크플로우 | Bastion Host + ProxyJump |
| 멀티 서비스 접근 (SSH + RDP) | Session Manager |
| 비용 최소화 | EC2 Instance Connect Endpoint |

## 관련 서비스 비교

### Bastion Host vs Session Manager vs EC2 Instance Connect

| 항목 | Bastion Host | Session Manager | EC2 Instance Connect Endpoint |
|------|-------------|----------------|-------------------------------|
| 인프라 관리 | EC2 운영 필요 | 에이전트만 필요 | AWS 관리형 |
| SSH 포트 | 필요 (22) | 불필요 | 불필요 |
| SSH 키 관리 | 필요 | 불필요 | 임시 키 (60초) |
| IAM 통합 | 제한적 | 완전 | 완전 |
| 세션 로깅 | 직접 구성 | 내장 (CW/S3) | CloudTrail |
| 포트 포워딩 | SSH 터널링 | 내장 지원 | SSH 터널링 |
| 비용 | EC2 비용 | 무료 (SSM Agent) | 무료 |
| 장점 | 익숙한 SSH 워크플로우 | SSH 키/포트 불필요, 완전한 감사 | Bastion 없이 프라이빗 접근 |
| 단점 | 운영 부담, 보안 취약점 | SSM Agent 필요 | 리전당 5개 제한 |

### VPN vs Bastion Host

| 항목 | VPN (Client VPN) | Bastion Host |
|------|-----------------|-------------|
| 접근 범위 | VPC 전체 네트워크 | 특정 리소스만 (터널링) |
| 설정 복잡도 | 높음 | 낮음 |
| 비용 | 시간당 + 연결당 과금 | EC2 비용만 |
| 보안 | 네트워크 수준 | 호스트 수준 |
| 확장성 | 높음 | 제한적 |

## 요약

Bastion Host는 프라이빗 네트워크 리소스에 안전하게 접근하기 위한 전통적인 방법이지만, AWS는 더 안전하고 편리한 대안을 제공합니다.

1. **Bastion Host**는 퍼블릭 서브넷에 배치하여 프라이빗 리소스에 대한 SSH 게이트웨이 역할을 합니다.
2. **보안 그룹**에서 관리자 IP만 허용하고, **SSH 키 인증**을 강제해야 합니다.
3. **ProxyJump** (`-J`)를 사용하여 Agent Forwarding의 보안 위험을 피합니다.
4. **Session Manager**는 SSH 포트와 키 관리가 불필요하여 가장 안전한 대안입니다.
5. **EC2 Instance Connect Endpoint**는 Bastion Host 없이 프라이빗 인스턴스에 접근할 수 있는 최신 솔루션입니다.
6. 신규 프로젝트에서는 **Session Manager 또는 EC2 Instance Connect Endpoint**를 우선 검토하는 것이 권장됩니다.
7. 기존 Bastion Host 환경에서는 **Session Manager로의 마이그레이션**을 계획하는 것이 보안과 운영 측면에서 유리합니다.
8. 어떤 방식을 선택하든 **세션 로깅과 감사**는 필수적으로 구현해야 합니다.