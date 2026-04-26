<!-- infographic-hero -->
![AWS Systems Manager 개요 및 주요 기능 - 하이브리드 인프라 통합 관리 핵심 요약](figures/infographic.svg)

*Figure: AWS Systems Manager 개요 및 주요 기능 - 하이브리드 인프라 통합 관리 한 장 요약 인포그래픽*

# AWS Systems Manager 개요 및 주요 기능 - 하이브리드 인프라 통합 관리

## 개요

AWS Systems Manager(SSM)는 AWS 클라우드와 온프레미스 인프라를 중앙에서 관리할 수 있는 통합 운영 서비스입니다. EC2 인스턴스, 온프레미스 서버, 엣지 디바이스를 하나의 콘솔에서 모니터링, 패치, 구성, 자동화할 수 있습니다.

Systems Manager는 20개 이상의 기능을 하나의 서비스로 통합하고 있으며, 크게 운영 관리, 애플리케이션 관리, 변경 관리, 노드 관리 네 가지 카테고리로 분류됩니다. SSH 포트를 열지 않고도 인스턴스에 안전하게 접속하는 Session Manager, 수천 대의 서버에 동시에 명령을 실행하는 Run Command, 애플리케이션 설정을 안전하게 저장하는 Parameter Store 등이 대표적인 기능입니다.

## 핵심 기능

### 노드 관리

**Session Manager**: SSH 키나 보안 그룹 인바운드 규칙 없이 브라우저 또는 CLI에서 인스턴스에 안전하게 접속합니다. 모든 세션은 CloudTrail에 기록되고, S3나 CloudWatch Logs에 세션 로그를 저장할 수 있습니다.

**Run Command**: 수백~수천 대의 인스턴스에 동시에 명령을 실행합니다. SSM Document(YAML/JSON)를 정의하여 재사용 가능한 명령 집합을 관리합니다.

**Patch Manager**: OS와 애플리케이션 패치를 자동으로 스캔하고 적용합니다. Patch Baseline을 정의하여 승인된 패치만 적용하도록 제어합니다.

**Inventory**: 관리 대상 인스턴스의 소프트웨어 인벤토리(설치된 패키지, OS 정보, 네트워크 설정 등)를 자동으로 수집합니다.

### 애플리케이션 관리

**Parameter Store**: 애플리케이션 설정값, 데이터베이스 연결 문자열, API 키 등을 안전하게 저장하고 관리합니다. 일반 텍스트(String)와 암호화(SecureString, KMS 연동) 두 가지 유형을 지원합니다.

| 구분 | Standard | Advanced |
|------|----------|----------|
| 최대 값 크기 | 4KB | 8KB |
| 파라미터 수 | 10,000 | 100,000 |
| 파라미터 정책 | 미지원 | 만료, 알림 지원 |
| 비용 | 무료 | 유료 |
| 처리량 | 낮음 | 높음 (초당 1000+) |

**AppConfig**: 애플리케이션의 기능 플래그, 설정 프로필을 안전하게 배포합니다. 점진적 배포(canary, linear)와 자동 롤백을 지원합니다.

### 변경 관리

**Automation**: 반복적인 운영 작업을 자동화합니다. Runbook(SSM Automation Document)을 작성하여 AMI 생성, 인스턴스 재시작, 장애 복구 등의 워크플로우를 정의합니다.

**Change Manager**: 인프라 변경에 대한 승인 워크플로우를 구축합니다. 변경 템플릿을 정의하고, 승인자를 지정하여 통제된 변경 관리를 수행합니다.

**Maintenance Windows**: 패치 적용, 스크립트 실행 등의 유지보수 작업을 예약된 시간 창에서 수행합니다.

### 운영 관리

**OpsCenter**: 운영 이슈(OpsItem)를 중앙에서 추적하고 관리합니다. CloudWatch 알람, Config 규칙 위반 등에서 자동으로 OpsItem을 생성합니다.

**Explorer**: 계정 전체의 운영 데이터(패치 준수율, 인벤토리, OpsItem 등)를 대시보드로 시각화합니다.

## 아키텍처 및 동작 원리

Systems Manager의 핵심 아키텍처는 SSM Agent와 SSM Endpoint 간의 통신을 기반으로 합니다.

```
[AWS Systems Manager Console / API]
              |
              v
[SSM Service Endpoint]
    |                   |
    v                   v
[EC2 인스턴스]      [온프레미스 서버]
  (SSM Agent)        (SSM Agent)
    |                   |
    +------- IAM Role ---+
    |    (인스턴스 프로필)   |
    v                   v
[Parameter Store]  [Run Command]
[Session Manager]  [Patch Manager]
[Inventory]        [Automation]
```

SSM Agent는 인스턴스에 설치되어 SSM 서비스 엔드포인트와 HTTPS 아웃바운드 통신을 합니다. 인바운드 포트를 열 필요가 없으므로 보안이 강화됩니다.

### 통신 방식

- SSM Agent가 SSM 서비스로 주기적으로 폴링하여 대기 중인 명령을 확인합니다
- VPC Endpoint(PrivateLink)를 통해 프라이빗 네트워크에서 통신할 수 있습니다
- 필요한 VPC Endpoint: `ssm`, `ssmmessages`, `ec2messages`

## 실전 활용

### AWS CLI를 사용한 Systems Manager 핵심 기능

```bash
# Session Manager로 인스턴스 접속 (SSH 불필요)
aws ssm start-session --target i-0abc123def456

# Run Command: 여러 인스턴스에 명령 실행
aws ssm send-command \
    --document-name "AWS-RunShellScript" \
    --targets '[{"Key":"tag:Environment","Values":["production"]}]' \
    --parameters '{"commands":["df -h","free -m","uptime"]}' \
    --comment "디스크 및 메모리 상태 점검" \
    --timeout-seconds 60

# Run Command 결과 조회
aws ssm list-command-invocations \
    --command-id abc-123-def \
    --details \
    --query 'CommandInvocations[].{Instance:InstanceId,Status:Status,Output:CommandPlugins[0].Output}'

# Parameter Store: 파라미터 저장
aws ssm put-parameter \
    --name "/myapp/production/database-url" \
    --value "postgresql://user:pass@host:5432/db" \
    --type SecureString \
    --key-id alias/myapp-key \
    --description "프로덕션 데이터베이스 연결 문자열"

# Parameter Store: 파라미터 조회
aws ssm get-parameter \
    --name "/myapp/production/database-url" \
    --with-decryption \
    --query 'Parameter.Value' --output text

# Parameter Store: 경로별 파라미터 목록
aws ssm get-parameters-by-path \
    --path "/myapp/production/" \
    --recursive \
    --with-decryption \
    --query 'Parameters[].{Name:Name,Type:Type,Version:Version}'

# Patch Manager: 패치 스캔 실행
aws ssm send-command \
    --document-name "AWS-RunPatchBaseline" \
    --targets '[{"Key":"tag:PatchGroup","Values":["web-servers"]}]' \
    --parameters '{"Operation":["Scan"]}'

# 패치 준수 현황 확인
aws ssm describe-instance-patch-states \
    --instance-ids i-0abc123 i-0def456 \
    --query 'InstancePatchStates[].{Instance:InstanceId,Installed:InstalledCount,Missing:MissingCount,Failed:FailedCount}'

# Automation: AMI 자동 생성
aws ssm start-automation-execution \
    --document-name "AWS-CreateImage" \
    --parameters '{"InstanceId":["i-0abc123"],"NoReboot":["true"]}'

# Inventory: 관리 인스턴스 목록
aws ssm describe-instance-information \
    --query 'InstanceInformationList[].{Id:InstanceId,Platform:PlatformType,AgentVersion:AgentVersion,Status:PingStatus}' \
    --output table

# Maintenance Window 생성 (매주 일요일 새벽 3시)
aws ssm create-maintenance-window \
    --name weekly-patching \
    --schedule 'cron(0 3 ? * SUN *)' \
    --duration 4 \
    --cutoff 1 \
    --allow-unassociated-targets
```

### Python SDK 활용 예시

```python
import boto3

ssm = boto3.client('ssm', region_name='ap-northeast-2')

# Parameter Store에서 설정 로드
def get_config(path):
    params = {}
    paginator = ssm.get_paginator('get_parameters_by_path')
    for page in paginator.paginate(Path=path, Recursive=True, WithDecryption=True):
        for param in page['Parameters']:
            key = param['Name'].split('/')[-1]
            params[key] = param['Value']
    return params

config = get_config('/myapp/production/')
db_url = config['database-url']
redis_url = config['redis-url']
```

## 모범 사례 및 보안

### Parameter Store 활용

- 계층적 경로 구조를 사용합니다: `/{app}/{env}/{key}` (예: `/myapp/prod/db-url`)
- 민감 정보는 반드시 SecureString 타입으로 저장합니다
- 파라미터 정책(Advanced)을 활용하여 비밀번호 만료일과 갱신 알림을 설정합니다
- IAM 정책으로 경로별 접근을 제어합니다 (`/myapp/prod/*`에 대한 읽기 권한)

### Session Manager 보안

- SSH 포트(22)를 보안 그룹에서 완전히 차단합니다. Session Manager만으로 충분합니다.
- 세션 로그를 S3와 CloudWatch Logs에 저장하여 감사 추적을 확보합니다.
- IAM 정책으로 특정 인스턴스에 대한 세션 접속 권한을 제어합니다.
- Session Manager의 쉘 프로필을 구성하여 기본 셸과 환경을 표준화합니다.

### VPC Endpoint 구성

프라이빗 서브넷의 인스턴스가 인터넷 접근 없이 SSM을 사용하려면 다음 VPC Endpoint가 필요합니다.

```bash
# 필요한 VPC Endpoint 3개 생성
for svc in ssm ssmmessages ec2messages; do
    aws ec2 create-vpc-endpoint \
        --vpc-id vpc-0abc123 \
        --service-name com.amazonaws.ap-northeast-2.$svc \
        --vpc-endpoint-type Interface \
        --subnet-ids subnet-0abc123 \
        --security-group-ids sg-0abc123
done
```

## 관련 서비스 비교

| 항목 | Systems Manager | AWS Config | CloudWatch | Ansible/Chef |
|------|----------------|------------|------------|-------------|
| 목적 | 인프라 운영 관리 | 구성 규정 준수 | 모니터링/로깅 | 구성 관리 자동화 |
| 명령 실행 | Run Command | 미지원 | 미지원 | Playbook/Recipe |
| 설정 저장소 | Parameter Store | 미지원 | 미지원 | Vault/Data Bags |
| 원격 접속 | Session Manager | 미지원 | 미지원 | SSH |
| 패치 관리 | Patch Manager | 미지원 | 미지원 | 모듈/패키지 |
| 에이전트 | SSM Agent | Config Agent | CW Agent | Ansible SSH/Agent |
| 하이브리드 | 지원 | 제한적 | 지원 | 지원 |

### Parameter Store vs Secrets Manager

| 항목 | Parameter Store | Secrets Manager |
|------|----------------|----------------|
| 비용 | Standard 무료 | 유료 |
| 자동 교체 | 미지원 | Lambda 기반 자동 교체 |
| 교차 계정 | 미지원 | 리소스 정책 지원 |
| RDS 통합 | 수동 | 자동 교체 |
| 값 크기 | 4KB/8KB | 64KB |
| 적합한 용도 | 설정값 전반 | DB 자격증명, API 키 |

## 요약

AWS Systems Manager는 20개 이상의 운영 관리 기능을 하나의 서비스로 통합하는 핵심 인프라 관리 도구입니다. Session Manager로 SSH 없이 안전하게 인스턴스에 접속하고, Run Command로 대규모 명령을 실행하며, Parameter Store로 애플리케이션 설정을 중앙 관리합니다. Patch Manager와 Maintenance Windows로 패치 관리를 자동화하고, Automation과 Change Manager로 운영 워크플로우를 체계화합니다. SSM Agent 기반으로 AWS 인스턴스와 온프레미스 서버를 동일한 방식으로 관리할 수 있어, 하이브리드 환경의 일관된 운영 관리를 실현합니다.