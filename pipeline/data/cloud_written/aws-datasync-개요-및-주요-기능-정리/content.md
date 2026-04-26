<!-- infographic-hero -->
![AWS DataSync 개요 및 주요 기능 핵심 요약](figures/infographic.svg)

*Figure: AWS DataSync 개요 및 주요 기능 한 장 요약 인포그래픽*

## 개요

AWS DataSync는 온프레미스와 AWS 간, 또는 AWS 서비스 간 대용량 데이터를 빠르고 안전하게 전송할 수 있는 완전 관리형 데이터 전송 서비스입니다. 네트워크 최적화, 데이터 무결성 검증, 전송 스케줄링 등을 자동으로 처리하여 수동 스크립트나 오픈소스 도구 대비 최대 10배 빠른 전송 속도를 제공합니다.

데이터 마이그레이션, 정기적인 데이터 동기화, 재해 복구 데이터 복제 등 다양한 시나리오에서 활용됩니다. 특히 수십 TB에서 PB 규모의 데이터 전송에서 강점을 보이며, 전송 과정의 모든 단계에서 데이터 무결성을 검증합니다.

### DataSync를 선택하는 이유

기존에 rsync, robocopy 등의 도구로 대용량 데이터를 전송하면 다음과 같은 문제가 발생합니다.

- 네트워크 대역폭을 효율적으로 활용하지 못합니다.
- 전송 중 오류 발생 시 처음부터 다시 시작해야 합니다.
- 전송 완료 후 데이터 무결성을 별도로 검증해야 합니다.
- 전송 스케줄링과 모니터링을 직접 구현해야 합니다.

DataSync는 이러한 문제를 모두 해결하며, 병렬 전송, 멀티스레딩, 파이프라이닝 기술을 활용하여 네트워크 대역폭을 최대한 활용합니다.

## 핵심 기능

### 1. 지원 스토리지 유형

**소스 (Source) 스토리지**
- NFS (Network File System) v3, v4.0, v4.1
- SMB (Server Message Block) 2.1, 3.0, 3.1.1
- HDFS (Hadoop Distributed File System)
- 자체 관리형 오브젝트 스토리지 (S3 호환 API)
- Amazon S3 (모든 스토리지 클래스)
- Amazon EFS
- Amazon FSx (Windows File Server, Lustre, OpenZFS, NetApp ONTAP)

**대상 (Destination) 스토리지**
- Amazon S3 (모든 스토리지 클래스)
- Amazon EFS
- Amazon FSx (모든 유형)
- NFS 서버
- SMB 서버

### 2. 전송 최적화

DataSync는 다음과 같은 기술을 통해 전송 속도를 최적화합니다.

- **병렬 전송**: 여러 파일을 동시에 전송합니다.
- **멀티스레딩**: 단일 파일을 여러 스레드로 분할 전송합니다.
- **파이프라이닝**: 데이터 읽기, 전송, 쓰기를 동시에 수행합니다.
- **인라인 압축**: 전송 중 데이터를 압축하여 네트워크 사용량을 줄입니다.
- **인라인 암호화**: TLS 1.2를 사용하여 전송 중 데이터를 암호화합니다.
- **증분 전송**: 변경된 데이터만 전송하여 이후 전송 시간을 단축합니다.

### 3. 데이터 무결성 검증

DataSync는 전송 과정에서 데이터 무결성을 다단계로 검증합니다.

- 전송 중: 체크섬 계산 및 비교
- 전송 후: 소스와 대상의 체크섬 전체 검증
- 메타데이터: 파일 권한, 타임스탬프, 소유권 등의 메타데이터도 검증

### 4. 전송 스케줄링 및 필터링

```bash
# DataSync 태스크에 스케줄 설정 (매일 오전 2시 실행)
aws datasync create-task \
  --source-location-arn "arn:aws:datasync:ap-northeast-2:123456789012:location/loc-src123" \
  --destination-location-arn "arn:aws:datasync:ap-northeast-2:123456789012:location/loc-dst456" \
  --name "daily-sync-task" \
  --schedule ScheduleExpression="cron(0 2 * * ? *)" \
  --options '{"VerifyMode":"ONLY_FILES_TRANSFERRED","OverwriteMode":"ALWAYS","Atime":"BEST_EFFORT","Mtime":"PRESERVE","PreserveDeletedFiles":"PRESERVE","TransferMode":"CHANGED"}' \
  --includes '[{"FilterType":"SIMPLE_PATTERN","Value":"/data/*.parquet"},{"FilterType":"SIMPLE_PATTERN","Value":"/logs/*.gz"}]' \
  --excludes '[{"FilterType":"SIMPLE_PATTERN","Value":"*.tmp"},{"FilterType":"SIMPLE_PATTERN","Value":"/cache/*"}]' \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### DataSync 에이전트 아키텍처

온프레미스에서 AWS로 데이터를 전송할 때는 DataSync 에이전트가 필요합니다. 에이전트는 VMware ESXi, KVM, Microsoft Hyper-V 등의 하이퍼바이저에 가상 머신으로 배포하거나, Amazon EC2 인스턴스로 배포할 수 있습니다.

```
온프레미스 환경                          AWS 클라우드
┌─────────────────────┐                ┌─────────────────────┐
│  NFS/SMB 서버       │                │  Amazon S3          │
│  ┌───────────┐      │    TLS 1.2     │  Amazon EFS         │
│  │   Data    │◄────►│◄──────────────►│  Amazon FSx         │
│  └───────────┘      │                │                     │
│                     │                │  ┌───────────────┐  │
│  ┌───────────────┐  │                │  │ DataSync       │  │
│  │ DataSync      │  │    포트 443     │  │ Service        │  │
│  │ Agent (VM)    │──│───────────────►│  │ Endpoint       │  │
│  │               │  │                │  └───────────────┘  │
│  └───────────────┘  │                │                     │
│                     │                │  ┌───────────────┐  │
│  Direct Connect     │                │  │ CloudWatch     │  │
│  또는 VPN           │                │  │ (모니터링)      │  │
└─────────────────────┘                └─────────────────────┘
```

**에이전트 배포 방법**

```bash
# 1. 에이전트 VM 배포 후 활성화 키 획득
# 에이전트 VM의 포트 80에 접속하여 활성화 키를 받거나 CLI로 직접 생성
curl "http://AGENT_IP_ADDRESS/?gatewayType=SYNC&activationRegion=ap-northeast-2&no_redirect"

# 2. 에이전트 등록
aws datasync create-agent \
  --activation-key "ACTIVATION_KEY_FROM_STEP1" \
  --agent-name "onprem-datasync-agent" \
  --vpc-endpoint-id "vpce-0123456789abcdef0" \
  --subnet-arns "arn:aws:ec2:ap-northeast-2:123456789012:subnet/subnet-abc123" \
  --security-group-arns "arn:aws:ec2:ap-northeast-2:123456789012:security-group/sg-abc123" \
  --region ap-northeast-2

# 3. 에이전트 상태 확인
aws datasync list-agents \
  --query 'Agents[*].{Name:Name,Status:Status,AgentArn:AgentArn}' \
  --output table \
  --region ap-northeast-2
```

### 전송 프로세스 상세

DataSync 태스크가 실행되면 다음과 같은 단계로 데이터가 전송됩니다.

**Phase 1: LAUNCHING**
- 태스크 실행 환경을 초기화합니다.

**Phase 2: PREPARING**
- 소스와 대상의 파일 시스템을 스캔합니다.
- 파일 메타데이터를 수집하고 비교합니다.
- 전송이 필요한 파일 목록을 생성합니다.

**Phase 3: TRANSFERRING**
- 실제 데이터 전송이 이루어집니다.
- 병렬 전송 및 대역폭 최적화가 적용됩니다.
- 전송 중 체크섬을 계산합니다.

**Phase 4: VERIFYING**
- 전송된 데이터의 무결성을 검증합니다.
- 소스와 대상의 체크섬을 비교합니다.

### AWS 서비스 간 전송 (에이전트 불필요)

AWS 서비스 간 전송 시에는 에이전트가 필요하지 않습니다. 예를 들어 S3에서 EFS로, 또는 서로 다른 리전의 S3 간 전송이 가능합니다.

```bash
# S3 소스 로케이션 생성
aws datasync create-location-s3 \
  --s3-bucket-arn "arn:aws:s3:::source-bucket" \
  --s3-config BucketAccessRoleArn="arn:aws:iam::123456789012:role/DataSyncS3Role" \
  --s3-storage-class STANDARD \
  --subdirectory "/data/input/" \
  --region ap-northeast-2

# EFS 대상 로케이션 생성
aws datasync create-location-efs \
  --efs-filesystem-arn "arn:aws:elasticfilesystem:ap-northeast-2:123456789012:file-system/fs-abc123" \
  --ec2-config SubnetArn="arn:aws:ec2:ap-northeast-2:123456789012:subnet/subnet-abc123",SecurityGroupArns="arn:aws:ec2:ap-northeast-2:123456789012:security-group/sg-abc123" \
  --subdirectory "/mnt/data/" \
  --region ap-northeast-2

# 크로스 리전 S3 전송용 대상 로케이션 (다른 리전)
aws datasync create-location-s3 \
  --s3-bucket-arn "arn:aws:s3:::destination-bucket" \
  --s3-config BucketAccessRoleArn="arn:aws:iam::123456789012:role/DataSyncS3Role" \
  --s3-storage-class STANDARD_IA \
  --subdirectory "/backup/" \
  --region us-west-2
```

## 실전 활용

### 시나리오 1: 온프레미스 NFS에서 S3로 대규모 마이그레이션

수십 TB의 데이터를 온프레미스 NFS 서버에서 S3로 마이그레이션하는 시나리오입니다.

```bash
# 1. NFS 소스 로케이션 생성
aws datasync create-location-nfs \
  --server-hostname "192.168.1.100" \
  --on-prem-config AgentArns="arn:aws:datasync:ap-northeast-2:123456789012:agent/agent-abc123" \
  --subdirectory "/exports/data/" \
  --mount-options Version=NFS4_1 \
  --region ap-northeast-2

# 2. S3 대상 로케이션 생성
aws datasync create-location-s3 \
  --s3-bucket-arn "arn:aws:s3:::migration-target-bucket" \
  --s3-config BucketAccessRoleArn="arn:aws:iam::123456789012:role/DataSyncS3AccessRole" \
  --s3-storage-class INTELLIGENT_TIERING \
  --subdirectory "/migrated-data/" \
  --region ap-northeast-2

# 3. 전송 태스크 생성 (대역폭 제한 포함)
aws datasync create-task \
  --source-location-arn "arn:aws:datasync:ap-northeast-2:123456789012:location/loc-nfs123" \
  --destination-location-arn "arn:aws:datasync:ap-northeast-2:123456789012:location/loc-s3456" \
  --name "nfs-to-s3-migration" \
  --options '{"VerifyMode":"POINT_IN_TIME_CONSISTENT","OverwriteMode":"ALWAYS","Atime":"BEST_EFFORT","Mtime":"PRESERVE","Uid":"NONE","Gid":"NONE","PreserveDeletedFiles":"PRESERVE","PreserveDevices":"NONE","PosixPermissions":"NONE","BytesPerSecond":-1,"TaskQueueing":"ENABLED","LogLevel":"TRANSFER","TransferMode":"ALL","ObjectTags":"PRESERVE"}' \
  --cloud-watch-log-group-arn "arn:aws:logs:ap-northeast-2:123456789012:log-group:/aws/datasync:*" \
  --region ap-northeast-2

# 4. 태스크 실행
aws datasync start-task-execution \
  --task-arn "arn:aws:datasync:ap-northeast-2:123456789012:task/task-abc123" \
  --region ap-northeast-2

# 5. 실행 상태 모니터링
aws datasync describe-task-execution \
  --task-execution-arn "arn:aws:datasync:ap-northeast-2:123456789012:task/task-abc123/execution/exec-xyz789" \
  --query '{Status:Status,BytesTransferred:BytesTransferred,FilesTransferred:FilesTransferred,EstimatedBytesToTransfer:EstimatedBytesToTransfer}' \
  --output json \
  --region ap-northeast-2
```

### 시나리오 2: EFS 간 크로스 리전 재해 복구

프로덕션 EFS의 데이터를 DR 리전의 EFS로 정기적으로 복제하는 시나리오입니다.

```bash
# 태스크 생성 (증분 전송, 매 6시간 실행)
aws datasync create-task \
  --source-location-arn "arn:aws:datasync:ap-northeast-2:123456789012:location/loc-efs-prod" \
  --destination-location-arn "arn:aws:datasync:ap-northeast-1:123456789012:location/loc-efs-dr" \
  --name "efs-cross-region-dr-sync" \
  --schedule ScheduleExpression="rate(6 hours)" \
  --options '{"VerifyMode":"ONLY_FILES_TRANSFERRED","OverwriteMode":"ALWAYS","TransferMode":"CHANGED","PreserveDeletedFiles":"REMOVE","PosixPermissions":"PRESERVE","Uid":"INT_VALUE","Gid":"INT_VALUE","LogLevel":"TRANSFER"}' \
  --region ap-northeast-2
```

### 시나리오 3: S3 스토리지 클래스 간 마이그레이션

S3 Standard에서 S3 Glacier Deep Archive로 오래된 데이터를 이동하는 시나리오입니다.

```bash
# S3 Glacier Deep Archive 로케이션 생성
aws datasync create-location-s3 \
  --s3-bucket-arn "arn:aws:s3:::archive-bucket" \
  --s3-config BucketAccessRoleArn="arn:aws:iam::123456789012:role/DataSyncS3Role" \
  --s3-storage-class DEEP_ARCHIVE \
  --subdirectory "/archived-data/" \
  --region ap-northeast-2

# 태스크 생성 (특정 경로만 필터링)
aws datasync create-task \
  --source-location-arn "arn:aws:datasync:ap-northeast-2:123456789012:location/loc-s3-standard" \
  --destination-location-arn "arn:aws:datasync:ap-northeast-2:123456789012:location/loc-s3-archive" \
  --name "s3-archival-task" \
  --includes '[{"FilterType":"SIMPLE_PATTERN","Value":"/old-data/2022/*"},{"FilterType":"SIMPLE_PATTERN","Value":"/old-data/2021/*"}]' \
  --region ap-northeast-2
```

### 전송 모니터링 및 알림 설정

```bash
# CloudWatch 메트릭으로 전송 모니터링
aws cloudwatch get-metric-statistics \
  --namespace AWS/DataSync \
  --metric-name BytesTransferred \
  --dimensions Name=TaskId,Value=task-abc123 \
  --start-time 2025-01-01T00:00:00Z \
  --end-time 2025-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum \
  --region ap-northeast-2

# 전송 실패 시 SNS 알림을 위한 EventBridge 규칙
aws events put-rule \
  --name "datasync-task-failure-alert" \
  --event-pattern '{"source":["aws.datasync"],"detail-type":["DataSync Task Execution State Change"],"detail":{"State":["ERROR"]}}' \
  --region ap-northeast-2

aws events put-targets \
  --rule "datasync-task-failure-alert" \
  --targets "Id"="1","Arn"="arn:aws:sns:ap-northeast-2:123456789012:datasync-alerts" \
  --region ap-northeast-2
```

## 모범 사례/보안

### 성능 최적화

1. **네트워크 대역폭을 사전에 평가하십시오.** DataSync는 10Gbps 링크를 완전히 활용할 수 있습니다. Direct Connect를 사용하면 안정적인 대역폭을 확보할 수 있습니다.

2. **에이전트 리소스를 충분히 할당하십시오.** 에이전트 VM에는 최소 4 vCPU, 16GB RAM을 권장합니다. 수백만 개의 파일을 전송하는 경우 더 많은 리소스가 필요합니다.

3. **대역폭 제한을 적절히 설정하십시오.** 프로덕션 네트워크와 공유하는 환경에서는 `BytesPerSecond` 옵션으로 대역폭 사용량을 제한하여 다른 서비스에 영향을 주지 않도록 하십시오.

4. **파일 수가 많은 경우 필터를 활용하십시오.** PREPARING 단계에서 파일 스캔에 시간이 오래 걸릴 수 있으므로, 필터를 사용하여 전송 대상을 최소화하십시오.

### 보안 모범 사례

- DataSync 에이전트와 AWS 간 통신은 TLS 1.2로 암호화됩니다. 추가로 VPC 엔드포인트를 사용하면 퍼블릭 인터넷을 경유하지 않고 데이터를 전송할 수 있습니다.
- S3 대상에 SSE-S3, SSE-KMS, SSE-C 등의 서버 측 암호화를 활성화하십시오.
- DataSync 태스크의 IAM 역할에 최소 권한 원칙을 적용하십시오.
- CloudWatch Logs를 활성화하여 전송 활동을 기록하고 감사하십시오.
- VPC 엔드포인트를 사용하여 프라이빗 네트워크에서 데이터를 전송하십시오.

```bash
# DataSync VPC 엔드포인트 생성
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-abc123 \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.ap-northeast-2.datasync \
  --subnet-ids subnet-abc123 \
  --security-group-ids sg-abc123 \
  --private-dns-enabled \
  --region ap-northeast-2
```

### 비용 최적화

- DataSync 비용은 전송된 데이터 양(GB당)에 따라 과금됩니다. 증분 전송(TransferMode: CHANGED)을 사용하면 변경된 데이터만 전송하여 비용을 절감할 수 있습니다.
- S3 대상의 스토리지 클래스를 적절히 선택하십시오. 자주 접근하지 않는 데이터는 S3 IA나 Glacier를 선택합니다.
- 대역폭 비용을 고려하여 Direct Connect를 사용하는 것이 장기적으로 유리할 수 있습니다.

## 관련 서비스 비교

### DataSync vs Transfer Family vs Snow Family

| 항목 | DataSync | Transfer Family | Snow Family |
|------|----------|----------------|-------------|
| 용도 | 대용량 데이터 전송/동기화 | SFTP/FTPS/FTP 파일 전송 | 오프라인 대용량 전송 |
| 전송 방식 | 온라인 (네트워크) | 온라인 (프로토콜 기반) | 오프라인 (물리 장비) |
| 데이터 규모 | GB ~ PB | 개별 파일 | TB ~ EB |
| 속도 | 최대 10Gbps | 프로토콜 제한 | 물리 운송 시간 |
| 에이전트 | 온프레미스 시 필요 | 불필요 | 불필요 |
| 스케줄링 | 내장 | 별도 구현 필요 | 해당 없음 |
| 무결성 검증 | 자동 | 별도 구현 필요 | 자동 |

### DataSync vs S3 Replication

| 항목 | DataSync | S3 Replication |
|------|----------|----------------|
| 대상 | 다양한 스토리지 | S3 버킷만 |
| 전송 방식 | 태스크 기반 (배치) | 실시간 (이벤트 기반) |
| 필터링 | 경로/이름 패턴 | 접두사/태그 기반 |
| 기존 데이터 | 전체 전송 가능 | 신규 객체만 (S3 Batch Replication으로 기존 객체 가능) |
| 비용 | GB당 과금 | GB당 + 요청당 과금 |

### DataSync vs AWS Migration Hub

DataSync는 데이터 전송에 특화된 서비스이고, Migration Hub는 전체 마이그레이션 프로젝트를 추적하고 관리하는 서비스입니다. 두 서비스는 상호 보완적이며, Migration Hub에서 DataSync 전송 상태를 추적할 수 있습니다.

## 요약

AWS DataSync는 대용량 데이터를 빠르고 안전하게 전송하는 완전 관리형 서비스입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **폭넓은 스토리지 지원**: NFS, SMB, HDFS, S3, EFS, FSx 등 온프레미스와 AWS의 다양한 스토리지를 지원합니다.
- **자동 최적화**: 병렬 전송, 멀티스레딩, 인라인 압축/암호화를 통해 최대 10배 빠른 전송 속도를 제공합니다.
- **데이터 무결성**: 전송 중 및 전송 후 자동 체크섬 검증으로 데이터 정확성을 보장합니다.
- **유연한 스케줄링**: cron 표현식 기반의 자동 스케줄링과 필터링을 지원합니다.
- **보안**: TLS 1.2 암호화, VPC 엔드포인트, IAM 기반 접근 제어를 제공합니다.
- **비용 효율**: 증분 전송을 활용하면 반복 전송 시 비용을 크게 절감할 수 있습니다.

DataSync는 마이그레이션뿐 아니라 지속적인 데이터 동기화, 재해 복구 복제, 아카이빙 등 다양한 데이터 전송 시나리오에서 핵심 서비스로 활용됩니다.