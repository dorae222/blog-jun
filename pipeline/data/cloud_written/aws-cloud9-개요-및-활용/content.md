<!-- infographic-hero -->
![AWS Cloud9 핵심 요약](figures/infographic.svg)

*Figure: AWS Cloud9 한 장 요약 인포그래픽*

## 개요

AWS Cloud9은 브라우저에서 코드를 작성, 실행, 디버깅할 수 있는 클라우드 기반 통합 개발 환경(IDE)입니다. 별도의 로컬 IDE 설치 없이 웹 브라우저만으로 완전한 개발 환경을 사용할 수 있으며, AWS 서비스와의 긴밀한 통합을 제공합니다.

Cloud9의 핵심 가치는 다음과 같습니다.

1. **일관된 개발 환경**: 팀원 모두가 동일한 개발 환경을 사용하여 "내 컴퓨터에서는 되는데" 문제를 제거합니다.
2. **AWS 네이티브 통합**: AWS CLI, SAM CLI, CDK 등이 사전 설치되어 있어 AWS 개발을 즉시 시작할 수 있습니다.
3. **실시간 협업**: 여러 개발자가 동시에 같은 환경에서 코드를 편집하고 터미널을 공유할 수 있습니다.
4. **비용 효율성**: 사용하지 않을 때 EC2 인스턴스가 자동으로 중지되어 비용을 절약합니다.

Cloud9 자체는 무료이며, 기반 EC2 인스턴스의 비용만 발생합니다. t2.micro 인스턴스를 사용하면 프리 티어 범위 내에서 무료로 사용할 수 있습니다.

참고로 AWS는 2024년 7월부터 신규 Cloud9 환경 생성을 제한하고 있으며, 기존 사용자는 계속 사용할 수 있습니다. 장기적으로는 Amazon CodeCatalyst의 Dev Environments로 전환을 권장하고 있습니다.

## 핵심 기능

### 개발 환경 유형

Cloud9은 두 가지 유형의 개발 환경을 지원합니다.

#### EC2 환경

Cloud9이 자동으로 EC2 인스턴스를 생성하고 관리합니다. 가장 일반적인 사용 방식입니다.

```bash
# AWS CLI로 Cloud9 EC2 환경 생성
aws cloud9 create-environment-ec2 \
    --name my-dev-environment \
    --description "Python/Node.js 개발 환경" \
    --instance-type t3.small \
    --image-id amazonlinux-2-x86_64 \
    --subnet-id subnet-0123456789abcdef0 \
    --automatic-stop-time-minutes 30 \
    --owner-arn arn:aws:iam::123456789012:user/developer

# 환경 목록 조회
aws cloud9 list-environments

# 환경 상세 정보 조회
aws cloud9 describe-environments \
    --environment-ids env-0123456789abcdef0
```

EC2 환경의 특성은 다음과 같습니다.
- Amazon Linux 2, Ubuntu Server 등을 지원합니다.
- t2.micro부터 m5.4xlarge까지 다양한 인스턴스 타입을 선택할 수 있습니다.
- 자동 중지 기능으로 비활성 시 EC2가 자동으로 중지됩니다.
- EBS 볼륨 크기를 사용자가 지정할 수 있습니다.

#### SSH 환경

기존 Linux 서버에 SSH로 연결하여 Cloud9 IDE를 사용합니다. 온프레미스 서버나 다른 클라우드의 서버에서도 사용할 수 있습니다.

```bash
# SSH 환경 생성
aws cloud9 create-environment-membership \
    --environment-id env-0123456789abcdef0 \
    --user-arn arn:aws:iam::123456789012:user/teammate \
    --permissions read-write
```

### 코드 편집기

Cloud9의 코드 편집기는 ACE 에디터를 기반으로 하며 다음 기능을 제공합니다.

- 40개 이상의 프로그래밍 언어 구문 강조
- 코드 자동 완성 (JavaScript, Python, PHP 등)
- 코드 포맷팅 및 린팅
- 파일 탐색기 및 검색
- 분할 뷰 (여러 파일 동시 편집)
- 키보드 단축키 (Vim, Emacs, Sublime Text 모드 지원)
- Git 통합

### 통합 터미널

Cloud9은 브라우저 내에서 완전한 Linux 터미널을 제공합니다. AWS CLI, Git, Docker, Node.js, Python 등 개발에 필요한 도구가 사전 설치되어 있습니다.

```bash
# Cloud9 터미널에서 사용 가능한 사전 설치 도구
aws --version          # AWS CLI
node --version         # Node.js
python3 --version      # Python 3
git --version          # Git
docker --version       # Docker
sam --version          # AWS SAM CLI
cdk --version          # AWS CDK
```

### AWS 서비스 통합

Cloud9은 AWS 서비스와 긴밀하게 통합됩니다.

1. **AWS 자격 증명 자동 관리**: EC2 환경의 경우 AWS 관리형 임시 자격 증명(AWS Managed Temporary Credentials)이 자동으로 제공됩니다.
2. **Lambda 함수 로컬 실행**: SAM CLI를 통해 Lambda 함수를 로컬에서 테스트할 수 있습니다.
3. **API Gateway 로컬 테스트**: SAM CLI로 API Gateway 엔드포인트를 로컬에서 시뮬레이션할 수 있습니다.
4. **DynamoDB 로컬**: DynamoDB Local을 실행하여 오프라인에서 테이블 작업을 테스트할 수 있습니다.

### 실시간 협업

Cloud9의 가장 차별화된 기능 중 하나는 실시간 페어 프로그래밍 지원입니다.

```bash
# 팀원에게 환경 접근 권한 부여
aws cloud9 create-environment-membership \
    --environment-id env-0123456789abcdef0 \
    --user-arn arn:aws:iam::123456789012:user/teammate \
    --permissions read-write

# 환경 멤버 목록 조회
aws cloud9 describe-environment-memberships \
    --environment-id env-0123456789abcdef0

# 멤버 권한 변경
aws cloud9 update-environment-membership \
    --environment-id env-0123456789abcdef0 \
    --user-arn arn:aws:iam::123456789012:user/teammate \
    --permissions read-only
```

협업 기능의 특성은 다음과 같습니다.
- 여러 사용자가 동시에 같은 파일을 편집할 수 있습니다.
- 각 사용자의 커서 위치가 실시간으로 표시됩니다.
- 채팅 기능으로 코드 토론이 가능합니다.
- 터미널도 공유하여 같은 명령어 실행을 관찰할 수 있습니다.

## 아키텍처/동작 원리

### EC2 환경 아키텍처

1. **Cloud9 IDE 서비스**: AWS에서 관리하는 웹 IDE 프론트엔드입니다. 브라우저에서 실행됩니다.
2. **Cloud9 에이전트**: EC2 인스턴스에 설치되어 IDE 서비스와 통신합니다. WebSocket을 통해 실시간 양방향 통신을 수행합니다.
3. **EC2 인스턴스**: 실제 개발 작업이 수행되는 컴퓨팅 환경입니다.
4. **EBS 볼륨**: 소스 코드와 개발 환경 설정이 저장됩니다.

### 자동 중지 메커니즘

Cloud9 EC2 환경은 설정된 비활성 시간이 경과하면 EC2 인스턴스를 자동으로 중지합니다. IDE에 다시 접속하면 인스턴스가 자동으로 시작됩니다.

동작 방식은 다음과 같습니다.
- 키보드/마우스 입력이 없으면 비활성으로 간주합니다.
- 기본 자동 중지 시간은 30분입니다.
- 중지된 인스턴스의 EBS 데이터는 유지됩니다.
- 인스턴스 재시작 시 이전 작업 상태가 복원됩니다.

### AWS 관리형 임시 자격 증명

Cloud9 EC2 환경에서는 AWS Managed Temporary Credentials(AMTC)가 자동으로 관리됩니다.

- 환경 소유자의 IAM 사용자 권한을 기반으로 임시 자격 증명이 발급됩니다.
- 자격 증명은 자동으로 갱신됩니다.
- 일부 권한이 제한됩니다 (예: IAM 사용자/역할 생성 불가, CloudTrail 로깅 비활성화 불가).
- 필요시 AMTC를 비활성화하고 EC2 인스턴스 프로파일이나 수동 자격 증명을 사용할 수 있습니다.

## 실전 활용

### Lambda 함수 개발

Cloud9은 서버리스 애플리케이션 개발에 특히 적합합니다.

```bash
# SAM 프로젝트 초기화
sam init --runtime python3.12 --name my-serverless-app

# 로컬에서 Lambda 함수 테스트
cd my-serverless-app
sam build
sam local invoke HelloWorldFunction --event events/event.json

# 로컬 API Gateway 실행
sam local start-api --port 3000

# 배포
sam deploy --guided
```

### CDK 프로젝트 개발

```bash
# CDK 프로젝트 생성
mkdir my-cdk-app && cd my-cdk-app
cdk init app --language typescript

# 의존성 설치
npm install

# CDK 스택 합성
cdk synth

# 차이점 확인
cdk diff

# 배포
cdk deploy
```

### EBS 볼륨 확장

Cloud9 환경의 디스크 공간이 부족할 때 EBS 볼륨을 확장할 수 있습니다.

```bash
# 현재 디스크 사용량 확인
df -h

# EBS 볼륨 크기 확장 (AWS CLI)
INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
VOLUME_ID=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].BlockDeviceMappings[0].Ebs.VolumeId' \
    --output text)

aws ec2 modify-volume \
    --volume-id $VOLUME_ID \
    --size 30

# 파일 시스템 확장
sudo growpart /dev/xvda 1
sudo resize2fs /dev/xvda1
```

### Docker 개발 환경 구성

```bash
# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Docker 기반 개발 환경 실행
docker-compose up -d

# 컨테이너 로그 확인
docker-compose logs -f
```

### AWS CLI를 활용한 Cloud9 환경 관리

```bash
# 모든 Cloud9 환경 조회
aws cloud9 list-environments --query 'environmentIds'

# 환경 상세 정보 조회 (여러 환경 동시 조회)
aws cloud9 describe-environments \
    --environment-ids env-abc123 env-def456 \
    --query 'environments[*].{Name:name,Type:type,Status:lifecycle.status,InstanceType:instanceType}' \
    --output table

# 환경 설정 업데이트 (자동 중지 시간 변경)
aws cloud9 update-environment \
    --environment-id env-abc123 \
    --name my-dev-environment \
    --description "Updated description" \
    --managed-credentials-action ENABLE

# 환경 삭제
aws cloud9 delete-environment \
    --environment-id env-abc123

# Cloud9 환경의 EC2 인스턴스 태그 확인
aws ec2 describe-instances \
    --filters "Name=tag:aws:cloud9:environment,Values=env-abc123" \
    --query 'Reservations[*].Instances[*].{InstanceId:InstanceId,State:State.Name,Type:InstanceType}' \
    --output table
```

## 모범 사례/보안

### 환경 구성 모범 사례

1. **적절한 인스턴스 타입을 선택합니다.** 일반 웹 개발에는 t3.small, ML/데이터 처리에는 m5.large 이상을 권장합니다. t2.micro는 프리 티어로 학습용에 적합합니다.

2. **자동 중지 시간을 설정합니다.** 30분 기본값이 적절하며, 긴 빌드/테스트가 필요한 경우 1~2시간으로 설정합니다. "Never"로 설정하면 비용이 급증할 수 있으므로 주의합니다.

3. **EBS 볼륨 크기를 충분히 설정합니다.** 기본 10GB는 Docker 이미지나 대규모 프로젝트에 부족할 수 있습니다. 20~30GB를 권장합니다.

4. **VPC 서브넷을 명시적으로 지정합니다.** 보안 그룹과 네트워크 정책이 적용된 프라이빗 서브넷에 배치하는 것을 권장합니다.

5. **환경별 용도를 명확히 구분합니다.** 프로젝트별 또는 용도별(개발/실험)로 별도의 환경을 생성하여 관리합니다.

### 보안 모범 사례

1. **AWS 관리형 임시 자격 증명을 활용합니다.** 수동으로 Access Key를 환경에 저장하지 않습니다. 필요한 경우 EC2 인스턴스 프로파일을 사용합니다.

2. **환경 멤버십을 최소화합니다.** 필요한 팀원에게만 접근 권한을 부여하고, 읽기 전용(read-only) 권한을 기본으로 사용합니다.

3. **인바운드 보안 그룹 규칙을 제한합니다.** Cloud9 EC2 인스턴스의 보안 그룹에 불필요한 인바운드 규칙을 추가하지 않습니다.

4. **민감 정보를 코드에 하드코딩하지 않습니다.** AWS Secrets Manager나 환경 변수를 활용합니다.

```bash
# 환경 변수로 민감 정보 관리
export DB_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id my-db-password \
    --query 'SecretString' \
    --output text)
```

5. **정기적으로 미사용 환경을 정리합니다.** 사용하지 않는 Cloud9 환경은 삭제하여 불필요한 EC2 비용을 방지합니다.

## 관련 서비스 비교

### Cloud9 vs VS Code (로컬)

| 항목 | AWS Cloud9 | VS Code (로컬) |
|------|-----------|----------------|
| 실행 환경 | 브라우저 | 데스크톱 애플리케이션 |
| 설치 | 불필요 | 로컬 설치 필요 |
| 컴퓨팅 | EC2 (클라우드) | 로컬 머신 |
| 협업 | 실시간 공유 내장 | Live Share 확장 |
| AWS 통합 | 네이티브 | AWS Toolkit 확장 |
| 확장성 | 제한적 | 풍부한 마켓플레이스 |
| 오프라인 | 불가 | 가능 |
| 비용 | EC2 비용 | 무료 |

### Cloud9 vs Amazon CodeCatalyst Dev Environments

| 항목 | Cloud9 | CodeCatalyst Dev Environments |
|------|--------|------------------------------|
| 상태 | 신규 생성 제한 (2024.07~) | 활성 서비스 |
| IDE | 자체 웹 IDE | VS Code, JetBrains 연동 |
| DevOps 통합 | 수동 구성 | CI/CD 내장 |
| 환경 정의 | 수동 | devfile 기반 선언적 |
| 비용 | EC2 비용 | 컴퓨트 시간 기반 |

### Cloud9 vs AWS CloudShell

| 항목 | Cloud9 | CloudShell |
|------|--------|------------|
| 용도 | 전체 개발 환경 | CLI 작업 전용 |
| 코드 편집 | 풍부한 IDE | 기본 편집기만 |
| 스토리지 | EBS (영구) | 1GB (세션 간 유지) |
| 비용 | EC2 비용 | 무료 |
| 인스턴스 커스텀 | 가능 | 불가 |
| 최대 사용 시간 | 무제한 | 세션당 제한 |

## 요약

AWS Cloud9은 브라우저 기반 통합 개발 환경으로, 별도의 로컬 설치 없이 AWS 서비스와 긴밀하게 통합된 개발 환경을 제공합니다. AWS CLI, SAM CLI, CDK 등이 사전 설치되어 있어 서버리스 애플리케이션과 AWS 인프라 개발에 특히 적합합니다.

실시간 협업 기능은 Cloud9의 가장 큰 차별점으로, 페어 프로그래밍과 코드 리뷰를 브라우저에서 직접 수행할 수 있습니다. 자동 중지 기능과 AWS 관리형 임시 자격 증명으로 비용과 보안을 효율적으로 관리할 수 있습니다.

다만 2024년 7월부터 신규 환경 생성이 제한되었으므로, 새로운 프로젝트에서는 Amazon CodeCatalyst Dev Environments, VS Code Remote - SSH, 또는 GitHub Codespaces를 대안으로 고려해야 합니다. 기존 Cloud9 사용자는 당분간 계속 사용할 수 있지만, 장기적인 마이그레이션 계획을 수립하는 것이 바람직합니다.