## 개요

AWS Application Migration Service(AWS MGN, 이전 CloudEndure Migration)는 물리 서버, 가상 머신(VMware, Hyper-V 등), 기타 클라우드 환경의 서버를 AWS로 마이그레이션하는 완전관리형 서비스입니다. 리프트 앤 시프트(Lift and Shift, Rehost) 방식의 마이그레이션을 자동화하여, 소스 서버를 최소한의 변경으로 AWS EC2 인스턴스로 전환할 수 있습니다.

MGN의 핵심 가치는 "지속적 블록 수준 복제(Continuous Block-Level Replication)"에 있습니다. 소스 서버에 경량 에이전트를 설치하면, 디스크의 블록 수준 변경 사항이 실시간으로 AWS의 스테이징 영역에 복제됩니다. 이 과정에서 소스 서버의 워크로드에 미치는 영향은 최소화되며, 애플리케이션을 중단하지 않고도 마이그레이션을 준비할 수 있습니다.

마이그레이션 준비가 완료되면 테스트 인스턴스를 실행하여 AWS 환경에서의 동작을 검증하고, 최종적으로 컷오버(cutover)를 수행하여 프로덕션 트래픽을 AWS로 전환합니다. 컷오버 시점의 다운타임은 일반적으로 분 단위에 불과합니다.

MGN은 CloudEndure Migration의 후속 서비스로, AWS에 완전히 통합되어 IAM, CloudTrail, CloudWatch 등 AWS 네이티브 서비스와 원활하게 연동됩니다. 또한 Migration Hub와 통합되어 마이그레이션 진행 상태를 중앙에서 추적할 수 있습니다.

## 핵심 기능

### 지속적 블록 수준 복제

MGN의 핵심 메커니즘입니다. 소스 서버에 설치된 AWS Replication Agent가 디스크의 블록 수준 변경을 실시간으로 감지하여 AWS로 전송합니다.

- **에이전트리스 복제**: vCenter 환경에서는 에이전트 없이 복제가 가능합니다.
- **에이전트 기반 복제**: 물리 서버, 비VMware VM 등에서는 Replication Agent를 설치합니다.
- **대역폭 스로틀링**: 복제 트래픽이 프로덕션 네트워크에 미치는 영향을 제한할 수 있습니다.
- **암호화 전송**: 전송 중 데이터는 TLS 1.2로 암호화됩니다.

### 스테이징 영역 (Staging Area)

복제된 데이터는 AWS 계정 내의 스테이징 영역(Staging Area Subnet)에 저장됩니다. 스테이징 영역은 경량 EC2 인스턴스(Replication Server)와 EBS 볼륨으로 구성되며, 소스 서버의 디스크 데이터가 이곳에 지속적으로 동기화됩니다.

### 테스트 및 컷오버

- **테스트 인스턴스**: 프로덕션에 영향 없이 마이그레이션된 서버를 테스트할 수 있습니다.
- **컷오버 인스턴스**: 최종 마이그레이션을 수행하여 프로덕션 EC2 인스턴스를 생성합니다.
- **자동 전환**: OS 드라이버, 부트로더, 네트워크 설정 등을 AWS 환경에 맞게 자동 변환합니다.

### 런치 템플릿 설정

마이그레이션된 EC2 인스턴스의 사양을 사전에 정의할 수 있습니다.

- 인스턴스 유형
- 서브넷 및 보안 그룹
- IAM 역할
- 태그
- EBS 볼륨 유형 및 크기
- 라이선스 설정

## 아키텍처/동작 원리

### 마이그레이션 프로세스 단계

**1단계: 초기화 및 에이전트 설치**

```bash
# MGN 서비스 초기화 (리전당 최초 1회)
aws mgn initialize-service

# 복제 설정 템플릿 조회
aws mgn describe-replication-configuration-templates \
  --query 'items[*].{Id:replicationConfigurationTemplateID,StagingSubnet:stagingAreaSubnetId,InstanceType:replicationServerInstanceType}' \
  --output table
```

소스 서버에 Replication Agent를 설치합니다.

```bash
# Linux 서버에 Replication Agent 설치
sudo wget -O ./aws-replication-installer-init.py \
  https://aws-application-migration-service-ap-northeast-2.s3.ap-northeast-2.amazonaws.com/latest/linux/aws-replication-installer-init.py

sudo python3 aws-replication-installer-init.py \
  --region ap-northeast-2 \
  --aws-access-key-id <ACCESS_KEY> \
  --aws-secret-access-key <SECRET_KEY>
```

**2단계: 초기 동기화 및 지속적 복제**

에이전트가 설치되면 초기 동기화(Full Sync)가 시작됩니다. 전체 디스크 데이터가 AWS로 복제되며, 완료 후에는 변경된 블록만 증분으로 복제됩니다.

```bash
# 소스 서버 복제 상태 확인
aws mgn describe-source-servers \
  --filters '{"isArchived": false}' \
  --query 'items[*].{ServerID:sourceServerID,Hostname:sourceProperties.identificationHints.hostname,State:dataReplicationInfo.dataReplicationState,Lag:dataReplicationInfo.lagDuration}' \
  --output table
```

```bash
# 특정 소스 서버의 상세 복제 정보
aws mgn describe-source-servers \
  --filters '{"sourceServerIDs": ["s-0123456789abcdef0"]}' \
  --query 'items[0].dataReplicationInfo'
```

**3단계: 런치 설정 구성**

```bash
# 런치 설정 업데이트
aws mgn update-launch-configuration \
  --source-server-id s-0123456789abcdef0 \
  --target-instance-type-right-sizing-method BASIC \
  --launch-disposition STARTED \
  --licensing '{"osByol": false}' \
  --boot-mode LEGACY_BIOS

# EC2 런치 템플릿 수정 (인스턴스 유형, 서브넷 등)
aws mgn update-launch-configuration \
  --source-server-id s-0123456789abcdef0 \
  --ec2-launch-template-id lt-0123456789abcdef0
```

**4단계: 테스트**

```bash
# 테스트 인스턴스 시작
aws mgn start-test \
  --source-server-ids s-0123456789abcdef0 s-0fedcba9876543210

# 테스트 상태 확인
aws mgn describe-source-servers \
  --filters '{"lifeCycleStates": ["TESTING"]}' \
  --query 'items[*].{ServerID:sourceServerID,Hostname:sourceProperties.identificationHints.hostname,TestStatus:lifeCycle.state}' \
  --output table
```

테스트 인스턴스에서 다음 항목을 검증합니다.

- 애플리케이션 정상 동작 여부
- 네트워크 연결 (다른 서비스와의 통신)
- 성능 (CPU, 메모리, 디스크 I/O)
- 라이선스 활성화 상태

```bash
# 테스트 완료 표시
aws mgn mark-as-archived \
  --source-server-id s-0123456789abcdef0
```

**5단계: 컷오버 (Cutover)**

```bash
# 컷오버 시작
aws mgn start-cutover \
  --source-server-ids s-0123456789abcdef0

# 컷오버 상태 모니터링
aws mgn describe-source-servers \
  --filters '{"lifeCycleStates": ["CUTTING_OVER"]}' \
  --query 'items[*].{ServerID:sourceServerID,State:lifeCycle.state}' \
  --output table
```

컷오버 프로세스는 다음 순서로 진행됩니다.

1. 소스 서버의 최종 데이터를 동기화합니다.
2. 대상 EC2 인스턴스를 생성합니다.
3. OS 드라이버 및 부트로더를 AWS 환경에 맞게 변환합니다.
4. 네트워크 설정을 적용합니다.
5. 인스턴스를 시작합니다.

```bash
# 컷오버 완료 후 정리
aws mgn finalize-cutover \
  --source-server-id s-0123456789abcdef0

# 복제 중단 및 리소스 정리
aws mgn disconnect-from-service \
  --source-server-id s-0123456789abcdef0
```

## 실전 활용

### 사례 1: 대규모 데이터센터 마이그레이션

수백 대의 서버를 마이그레이션하는 대규모 프로젝트에서는 웨이브(Wave) 기반 접근법을 사용합니다.

```bash
# 웨이브 생성
aws mgn create-wave \
  --name "Wave-1-WebServers" \
  --tags '{"Environment": "Production", "Phase": "1"}'

# 애플리케이션 생성 및 웨이브에 연결
aws mgn create-application \
  --name "E-Commerce-Frontend" \
  --wave-id wave-0123456789abcdef0

# 소스 서버를 애플리케이션에 연결
aws mgn associate-source-servers \
  --application-id app-0123456789abcdef0 \
  --source-server-ids s-0123456789abcdef0 s-0fedcba9876543210
```

### 사례 2: 라이선스 관리

Windows Server나 SQL Server 등 라이선스가 필요한 소프트웨어의 마이그레이션 시, 기존 라이선스(BYOL)를 사용할지 AWS 라이선스를 사용할지 결정해야 합니다.

```bash
# BYOL 설정으로 런치 구성 업데이트
aws mgn update-launch-configuration \
  --source-server-id s-0123456789abcdef0 \
  --licensing '{"osByol": true}'
```

### 사례 3: 포스트 마이그레이션 자동화

MGN은 포스트 런치 액션을 지원하여, 마이그레이션 완료 후 자동으로 설정 작업을 수행할 수 있습니다.

```bash
# SSM 문서를 포스트 런치 액션으로 설정
aws mgn put-source-server-action \
  --source-server-id s-0123456789abcdef0 \
  --action-id install-cloudwatch-agent \
  --action-name "Install CloudWatch Agent" \
  --document-identifier "AWS-ConfigureAWSPackage" \
  --order 1 \
  --parameters '{"action": ["Install"], "name": ["AmazonCloudWatchAgent"]}' \
  --active
```

## 모범 사례/보안

### 보안 모범 사례

1. **IAM 최소 권한**: Replication Agent에 부여하는 자격 증명은 MGN 관련 권한만 포함합니다.
2. **네트워크 보안**: 소스 서버와 AWS 간 통신을 위해 VPN 또는 Direct Connect를 사용합니다.
3. **스테이징 영역 격리**: 스테이징 서브넷은 프로덕션 서브넷과 분리하고, 필요한 포트(TCP 1500)만 허용합니다.
4. **데이터 암호화**: 스테이징 영역의 EBS 볼륨에 KMS 암호화를 적용합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "mgn:SendAgentMetricsForMgn",
        "mgn:SendAgentLogsForMgn",
        "mgn:SendClientLogsForMgn"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "mgn:RegisterAgentForMgn",
        "mgn:UpdateAgentSourcePropertiesForMgn",
        "mgn:UpdateAgentReplicationInfoForMgn",
        "mgn:UpdateAgentConversionInfoForMgn"
      ],
      "Resource": "*"
    }
  ]
}
```

### 운영 모범 사례

1. **사전 테스트 필수**: 컷오버 전에 반드시 테스트 인스턴스로 검증합니다.
2. **웨이브 계획**: 종속성 순서를 고려하여 마이그레이션 웨이브를 계획합니다.
3. **롤백 계획**: 컷오버 후 문제 발생 시 소스 서버로 롤백하는 절차를 사전에 준비합니다.
4. **네트워크 대역폭**: 초기 동기화 시 대역폭 소비가 크므로, 비업무 시간에 시작하거나 스로틀링을 설정합니다.
5. **라이트사이징**: MGN의 자동 라이트사이징 기능을 활용하여 적절한 EC2 인스턴스 유형을 선택합니다.

```bash
# 복제 설정 템플릿 업데이트 (대역폭 스로틀링, 암호화)
aws mgn update-replication-configuration-template \
  --replication-configuration-template-id rct-0123456789abcdef0 \
  --bandwidth-throttling 500 \
  --ebs-encryption DEFAULT \
  --replication-server-instance-type t3.small \
  --use-dedicated-replication-server false
```

## 관련 서비스 비교

| 항목 | AWS MGN | VM Import/Export | Server Migration Service | Database Migration Service |
|------|---------|-----------------|------------------------|---------------------------|
| 마이그레이션 대상 | 서버 (OS+앱) | VM 이미지 | VM | 데이터베이스 |
| 복제 방식 | 블록 수준 지속 복제 | 이미지 내보내기/가져오기 | 스냅샷 기반 증분 | 로그 기반 CDC |
| 다운타임 | 분 단위 | 시간~일 단위 | 시간 단위 | 분 단위 |
| 에이전트 필요 | 필요 (또는 에이전트리스) | 불필요 | Connector 필요 | 불필요 |
| 테스트 기능 | 비파괴적 테스트 지원 | 미지원 | 제한적 | 미지원 |
| 지원 OS | Windows, Linux 다수 | Windows, Linux | VMware VM | 해당 없음 |
| 물리 서버 지원 | 지원 | 미지원 | 미지원 | 해당 없음 |
| Migration Hub 통합 | 자동 | 미지원 | 자동 | 자동 |
| 상태 | 현재 권장 | 유지 보수 | 서비스 종료 | 현재 권장 |

AWS MGN은 Server Migration Service(SMS)의 후속 서비스로, 모든 신규 마이그레이션 프로젝트에서 MGN 사용이 권장됩니다.

## 요약

AWS Application Migration Service(MGN)는 서버를 AWS로 리프트 앤 시프트 마이그레이션하는 핵심 서비스입니다. 주요 포인트를 정리하면 다음과 같습니다.

- **지속적 블록 수준 복제**: 소스 서버의 데이터를 실시간으로 AWS에 동기화하여, 최소한의 다운타임으로 마이그레이션합니다.
- **광범위한 소스 지원**: 물리 서버, VMware, Hyper-V, Azure, GCP 등 다양한 소스를 지원합니다.
- **논스톱 테스트**: 프로덕션에 영향 없이 마이그레이션된 서버를 테스트할 수 있습니다.
- **자동 변환**: OS 드라이버, 부트로더, 네트워크 설정을 AWS 환경에 맞게 자동 변환합니다.
- **웨이브 관리**: 대규모 마이그레이션을 웨이브 단위로 체계적으로 관리합니다.
- **포스트 런치 자동화**: SSM 문서를 통해 마이그레이션 후 설정 작업을 자동화합니다.
- **Migration Hub 통합**: 마이그레이션 진행 상태를 중앙에서 추적합니다.

MGN은 AWS 마이그레이션 도구 생태계의 핵심이며, ADS(탐색), Migration Evaluator(평가), DMS(데이터베이스)와 함께 사용하여 종합적인 마이그레이션 전략을 수립하는 것이 바람직합니다.