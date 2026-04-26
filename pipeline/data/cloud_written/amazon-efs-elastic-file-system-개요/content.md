<!-- infographic-hero -->
![Amazon EFS 핵심 요약](figures/infographic.svg)

*Figure: Amazon EFS 한 장 요약 인포그래픽*

# Amazon EFS(Elastic File System) 개요

## 개요

Amazon EFS(Elastic File System)는 NFS v4.0/v4.1 프로토콜 기반의 완전 관리형 파일 시스템 서비스입니다. 2016년 일반 출시(GA)되었으며, 여러 EC2 인스턴스, 컨테이너(ECS/EKS/Fargate), Lambda 함수가 동일한 파일 시스템을 동시에 마운트하여 공유할 수 있도록 설계되었습니다.

EBS는 단일 인스턴스에 부착되는 블록 스토리지(Multi-Attach 제외)인 반면, EFS는 본질적으로 공유 파일 스토리지입니다. POSIX 호환 권한 체계를 지원하므로 기존 Linux 애플리케이션을 거의 변경 없이 그대로 사용할 수 있습니다. 또한 사용자가 용량을 미리 프로비저닝할 필요 없이 데이터가 추가될수록 자동으로 페타바이트 규모까지 확장됩니다.

EFS가 해결하는 핵심 문제는 다음과 같습니다.

- **공유 파일 시스템 구성 부담 제거**: NFS 서버를 직접 운영하지 않아도 됨
- **자동 확장**: 용량을 미리 산정하지 않아도 사용한 만큼만 과금
- **Multi-AZ 가용성**: 표준 EFS는 다중 가용 영역에 데이터 자동 복제
- **이기종 클라이언트 지원**: EC2, Lambda, ECS, EKS, Fargate, 온프레미스(Direct Connect/VPN) 모두 마운트 가능

대표적인 활용 사례는 WordPress/Drupal 같은 콘텐츠 관리 시스템, 머신러닝 학습 데이터셋 공유, 대규모 빌드 캐시, Lambda 함수의 큰 의존성 패키지 저장 등입니다.

---

## 핵심 기능

### 1. 스토리지 클래스

EFS는 데이터 액세스 빈도와 가용성 요구사항에 따라 4가지 스토리지 클래스를 제공합니다.

| 스토리지 클래스 | 설명 | 가용성 | 가격 (GB-월) |
|------------------|------|--------|--------------|
| Standard | 다중 AZ 복제, 자주 접근 | 99.99% | $0.30 |
| Standard-IA (Infrequent Access) | 다중 AZ 복제, 드물게 접근 | 99.99% | $0.025 |
| One Zone | 단일 AZ, 자주 접근 | 99.9% | $0.16 |
| One Zone-IA | 단일 AZ, 드물게 접근 | 99.9% | $0.0133 |

**One Zone 스토리지**는 단일 AZ에만 데이터가 저장되어 비용이 더 저렴하지만, AZ 장애 시 가용성이 영향을 받습니다. 개발/테스트 환경, 재생성 가능한 데이터, 로컬 백업 용도에 적합합니다.

```bash
# Standard EFS 파일 시스템 생성
aws efs create-file-system \
  --creation-token my-efs-prod \
  --performance-mode generalPurpose \
  --throughput-mode elastic \
  --encrypted \
  --kms-key-id arn:aws:kms:ap-northeast-2:123456789012:key/my-key \
  --tags Key=Name,Value=prod-efs Key=Env,Value=prod \
  --region ap-northeast-2

# One Zone EFS 파일 시스템 생성
aws efs create-file-system \
  --creation-token my-efs-onezone \
  --availability-zone-name ap-northeast-2a \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --region ap-northeast-2
```

### 2. Lifecycle Management

Lifecycle Management는 일정 기간 동안 액세스되지 않은 파일을 자동으로 IA 클래스로 이동시켜 비용을 최대 92% 절감하는 기능입니다.

| 정책 | 동작 |
|------|------|
| AFTER_7_DAYS | 7일 미접근 시 IA 이동 |
| AFTER_14_DAYS | 14일 미접근 시 IA 이동 |
| AFTER_30_DAYS (기본 권장) | 30일 미접근 시 IA 이동 |
| AFTER_60_DAYS | 60일 미접근 시 IA 이동 |
| AFTER_90_DAYS | 90일 미접근 시 IA 이동 |
| AFTER_1_DAY | 1일 미접근 시 IA 이동 |
| TransitionToPrimaryStorageClass | IA 파일 접근 시 다시 Standard로 이동 |

```bash
# Lifecycle Management 설정
aws efs put-lifecycle-configuration \
  --file-system-id fs-0123456789abcdef0 \
  --lifecycle-policies \
    '{"TransitionToIA": "AFTER_30_DAYS"}' \
    '{"TransitionToPrimaryStorageClass": "AFTER_1_ACCESS"}' \
  --region ap-northeast-2
```

### 3. 처리량 모드

EFS는 세 가지 처리량 모드를 제공합니다.

**Bursting Throughput (기본)**
- 파일 시스템 크기에 비례한 baseline 처리량 (1TB당 50 MB/s)
- BurstCreditBalance를 사용하여 일시적으로 100 MB/s 이상으로 폭증 가능
- 작은 파일 시스템에서는 baseline이 너무 낮을 수 있음

**Provisioned Throughput**
- 파일 시스템 크기와 무관하게 처리량을 미리 지정 (1-1024 MB/s)
- 작은 파일 시스템에서 일관된 성능이 필요할 때 사용
- 사용하지 않아도 비용 발생

**Elastic Throughput (2023+ 권장)**
- 워크로드에 맞춰 자동으로 처리량 확장 (최대 10 GB/s 읽기, 3 GB/s 쓰기)
- 사용한 만큼만 과금 (GB당 데이터 읽기/쓰기 요금)
- 대부분의 신규 워크로드에 권장

```bash
# Elastic Throughput으로 변경
aws efs update-file-system \
  --file-system-id fs-0123456789abcdef0 \
  --throughput-mode elastic \
  --region ap-northeast-2

# Provisioned Throughput으로 변경 (250 MB/s)
aws efs update-file-system \
  --file-system-id fs-0123456789abcdef0 \
  --throughput-mode provisioned \
  --provisioned-throughput-in-mibps 250 \
  --region ap-northeast-2
```

### 4. 성능 모드

| 성능 모드 | 특징 | 사용 사례 |
|-----------|------|-----------|
| General Purpose (기본) | 낮은 지연 시간, 분당 35,000 ops 한도 | 웹 서버, CMS, 일반 워크로드 |
| Max I/O | 높은 처리량, 약간 더 높은 지연 시간 | 빅데이터 분석, 미디어 처리 |

성능 모드는 파일 시스템 생성 시 결정되며 이후 변경할 수 없습니다. 단, Elastic Throughput을 사용하면 General Purpose 모드로도 매우 높은 성능을 낼 수 있어 대부분의 경우 General Purpose가 권장됩니다.

### 5. EFS Access Points

Access Points는 파일 시스템 내 특정 디렉토리에 대한 진입점 역할을 합니다.

- **POSIX User/Group 강제**: 클라이언트 UID/GID를 무시하고 지정된 사용자로 매핑
- **Root Directory 격리**: 파일 시스템 내 특정 경로만 노출
- **활용**: 멀티 테넌트 환경, Lambda 통합

```bash
# Access Point 생성
aws efs create-access-point \
  --file-system-id fs-0123456789abcdef0 \
  --posix-user "Uid=1001,Gid=1001" \
  --root-directory '{
    "Path": "/app-data",
    "CreationInfo": {
      "OwnerUid": 1001,
      "OwnerGid": 1001,
      "Permissions": "0755"
    }
  }' \
  --tags Key=Name,Value=app-ap \
  --region ap-northeast-2
```

---

## 아키텍처

### EFS 구성 요소

```
[VPC]
   |
   +--[AZ-a] -- Mount Target (ENI) -- 클라이언트 마운트
   +--[AZ-b] -- Mount Target (ENI) -- 클라이언트 마운트
   +--[AZ-c] -- Mount Target (ENI) -- 클라이언트 마운트
   |
   v
[EFS File System]
   - 메타데이터 스토리지
   - 데이터 스토리지 (다중 AZ 자동 복제)
   - Lifecycle Manager
   - Access Points
```

1. **Mount Target**: 각 AZ별로 1개의 Mount Target을 생성합니다. 이는 사실상 ENI이며, 클라이언트가 NFS 트래픽을 보내는 네트워크 진입점입니다.
2. **Security Group**: Mount Target에 부착된 SG로 NFS 포트(2049) 접근 제어
3. **자동 확장**: 사용량이 늘면 백엔드에서 자동으로 스토리지 노드가 추가됨

### 마운트 방법

EFS 마운트는 두 가지 방법이 있습니다.

**EFS Mount Helper (권장)**: TLS 암호화, IAM 인증, Access Points를 단순한 옵션으로 지원

```bash
# amazon-efs-utils 설치 (Amazon Linux 2)
sudo yum install -y amazon-efs-utils

# 마운트 (TLS 암호화)
sudo mkdir /mnt/efs
sudo mount -t efs -o tls fs-0123456789abcdef0:/ /mnt/efs

# Access Point + IAM 인증으로 마운트
sudo mount -t efs -o tls,iam,accesspoint=fsap-xxx fs-0123456789abcdef0 /mnt/efs

# /etc/fstab에 등록
echo "fs-0123456789abcdef0:/  /mnt/efs  efs  _netdev,tls,iam  0  0" | sudo tee -a /etc/fstab
```

**표준 NFS 클라이언트**

```bash
sudo yum install -y nfs-utils
sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 \
  fs-0123456789abcdef0.efs.ap-northeast-2.amazonaws.com:/ /mnt/efs
```

### 보안 모델

- **Security Group**: Mount Target SG가 NFS 포트(2049) 접근 제어
- **IAM 정책**: 파일 시스템 단위 접근 제어, IAM Role 기반 인증
- **POSIX 권한**: 파일/디렉토리 단위 권한
- **암호화**: 전송 중 TLS, 저장 시 KMS 통합

---

## 실전 사용

### 1. EC2에서 EFS 마운트

```bash
# 1) EFS 파일 시스템 생성 후 ID 확인
FS_ID=$(aws efs describe-file-systems --query "FileSystems[0].FileSystemId" --output text --region ap-northeast-2)

# 2) Mount Target 생성 (각 AZ별)
aws efs create-mount-target \
  --file-system-id $FS_ID \
  --subnet-id subnet-0a1b2c3d \
  --security-groups sg-efs-allow-2049 \
  --region ap-northeast-2

# 3) EC2 인스턴스에 마운트
sudo yum install -y amazon-efs-utils
sudo mkdir -p /mnt/efs
sudo mount -t efs -o tls $FS_ID:/ /mnt/efs

# 4) 확인
df -hT | grep efs
echo "Hello EFS" | sudo tee /mnt/efs/test.txt
```

### 2. Lambda + EFS

Lambda는 큰 의존성 또는 영구 데이터가 필요한 경우 EFS를 마운트할 수 있습니다.

```bash
# Lambda 함수에 EFS 부착
aws lambda update-function-configuration \
  --function-name my-ml-inference \
  --vpc-config SubnetIds=subnet-0a1b2c3d,SecurityGroupIds=sg-lambda \
  --file-system-configs \
    "Arn=arn:aws:elasticfilesystem:ap-northeast-2:123456789012:access-point/fsap-xxx,LocalMountPath=/mnt/models" \
  --region ap-northeast-2
```

```python
# Lambda 함수 내에서 사용
import torch

def handler(event, context):
    model = torch.load("/mnt/models/large_model.pt")
    return {"prediction": model(event["input"]).tolist()}
```

### 3. EKS PersistentVolumeClaim

EFS CSI Driver를 통해 Kubernetes에서 EFS를 동적으로 사용할 수 있습니다.

```yaml
# StorageClass
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs-sc
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap
  fileSystemId: fs-0123456789abcdef0
  directoryPerms: "755"
  gidRangeStart: "1000"
  gidRangeEnd: "2000"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: efs-sc
  resources:
    requests:
      storage: 10Gi
```

EFS의 핵심 가치는 `ReadWriteMany`(RWX) 접근 모드를 지원한다는 점입니다. EBS는 기본적으로 `ReadWriteOnce`(RWO)만 지원합니다.

---

## 가격/한도

### 가격 모델 (us-east-1)

| 항목 | 가격 |
|------|------|
| Standard 스토리지 | GB-월 $0.30 |
| Standard-IA 스토리지 | GB-월 $0.025 |
| One Zone 스토리지 | GB-월 $0.16 |
| One Zone-IA 스토리지 | GB-월 $0.0133 |
| IA Read/Write 데이터 | GB당 $0.01 |
| Provisioned Throughput | MB/s-월 $6.00 (baseline 초과분) |
| Elastic Throughput Read | GB당 $0.03 |
| Elastic Throughput Write | GB당 $0.06 |
| 백업 (AWS Backup) | GB-월 $0.05 |

**비용 계산 예시**: Standard 100GB + Lifecycle 30일로 70%가 IA 이동
- Standard: 30GB * $0.30 = $9.00
- IA: 70GB * $0.025 = $1.75
- 합계: $10.75/월 (전부 Standard 시 $30 대비 64% 절감)

### 주요 한도

| 항목 | 기본 한도 |
|------|-----------|
| 파일 시스템 크기 | 무제한 (페타바이트 규모) |
| 단일 파일 크기 | 47.9TB |
| 디렉토리당 파일 수 | 65,536 |
| 클라이언트 연결 수 | 25,000 |
| Mount Target (AZ당) | 1 |
| Access Points (FS당) | 1,000 |
| Bursting baseline 처리량 | 1TB당 50 MB/s |
| Bursting burst 처리량 | 1TB당 100 MB/s (최대) |

```bash
# 사용 가능한 클라이언트 수 등 메트릭 모니터링
aws cloudwatch get-metric-statistics \
  --namespace AWS/EFS \
  --metric-name ClientConnections \
  --dimensions Name=FileSystemId,Value=fs-0123456789abcdef0 \
  --start-time 2026-04-25T00:00:00Z \
  --end-time 2026-04-26T00:00:00Z \
  --period 3600 \
  --statistics Average Maximum \
  --region ap-northeast-2
```

---

## Best Practice

### 권장 패턴

1. **Elastic Throughput 우선 사용**: 신규 파일 시스템은 Elastic Throughput으로 시작
2. **Lifecycle Management 활성화**: 30일 정책으로 IA 이동 -> 비용 90% 절감
3. **TLS 암호화 마운트**: `mount -t efs -o tls` 옵션으로 전송 구간 보호
4. **IAM 인증 사용**: Lambda/EC2가 IAM Role로 마운트하여 자격 증명 관리 단순화
5. **CloudWatch 모니터링**: PercentIOLimit, BurstCreditBalance, ClientConnections 추적
6. **AWS Backup으로 백업 자동화**: EFS 자체 백업보다 정책 기반 관리 권장
7. **Access Points로 격리**: 멀티 테넌트 환경에서 디렉토리 단위 접근 제어
8. **Multi-AZ에서 EC2 분산**: 로컬 AZ Mount Target 사용으로 데이터 전송 비용 최소화

### 안티 패턴

1. **고성능 OLTP 데이터베이스 호스팅**: NFS 기반은 DB 워크로드에 부적합 - EBS io2 사용
2. **Bursting 모드 + 작은 파일 시스템**: BurstCreditBalance 고갈 시 성능 급락 - Elastic Throughput 사용
3. **Lifecycle 미설정**: 모든 데이터를 Standard로 유지하면 비용 폭증
4. **단일 Mount Target만 생성**: Multi-AZ 가용성 손실 - 모든 사용 AZ에 Mount Target 생성
5. **NFS 클라이언트로 IA 빈번 액세스**: IA 데이터는 GB당 $0.01 read 요금이 추가되므로 자주 읽으면 Standard보다 비싸짐
6. **One Zone에 미션 크리티컬 데이터**: AZ 장애 시 가용성 손실 - 표준 EFS + 백업 사용

```bash
# 권장: AWS Backup 기반 자동 백업
aws backup create-backup-plan \
  --backup-plan '{
    "BackupPlanName": "efs-daily-backup",
    "Rules": [{
      "RuleName": "DailyBackup",
      "TargetBackupVaultName": "Default",
      "ScheduleExpression": "cron(0 15 * * ? *)",
      "Lifecycle": {"DeleteAfterDays": 30}
    }]
  }' \
  --region ap-northeast-2
```

### EFS vs EBS vs FSx 선택 가이드

| 항목 | EFS | EBS | FSx for Lustre/NetApp |
|------|-----|-----|------------------------|
| 프로토콜 | NFS v4.1 | 블록 (NVMe) | Lustre/SMB/NFS |
| 동시 접근 | 다중 클라이언트 | 단일 (Multi-Attach 제한적) | 다중 클라이언트 |
| 가용성 | Multi-AZ (Standard) | 단일 AZ | 다양 |
| 최대 IOPS | 매우 높음 (Elastic) | 256K (io2 BE) | 100만+ (Lustre) |
| 가격 | GB-월 기반 | GB + IOPS | 워크로드별 |
| 적합 | CMS, ML 데이터셋 공유 | DB, 부트 볼륨 | HPC, Windows 파일 공유 |

---

## 관련 서비스

| 서비스 | 관계 |
|--------|------|
| Amazon EC2 | 가장 일반적인 EFS 클라이언트 |
| AWS Lambda | EFS 마운트로 큰 의존성/모델 저장 |
| Amazon ECS / EKS / Fargate | 컨테이너에서 RWX 볼륨으로 사용 |
| AWS DataSync | 온프레미스에서 EFS로 데이터 이전 |
| AWS Backup | 정책 기반 EFS 백업 |
| AWS Direct Connect / VPN | 온프레미스에서 EFS 마운트 |
| Amazon CloudWatch | 파일 시스템 메트릭 모니터링 |
| AWS KMS | 저장 데이터 암호화 키 관리 |
| AWS PrivateLink | EFS API 프라이빗 액세스 |
| AWS Storage Gateway | 하이브리드 파일 게이트웨이 |

---

## 관련 문서

- [[amazon-ebs-elastic-block-store-개요|Amazon EBS]] - 블록 스토리지, 단일 인스턴스용 (대비)
- [[aws-lambda-개요-및-실전-활용-가이드|AWS Lambda]] - EFS 마운트로 큰 의존성/모델 활용
- [[aws-fargate-서버리스-컨테이너-실행-개요|AWS Fargate]] - Fargate 태스크의 영구 스토리지
- [[amazon-eks-elastic-kubernetes-service-개요|Amazon EKS]] - EFS CSI Driver로 RWX PVC 제공
