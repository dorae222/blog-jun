<!-- infographic-hero -->
![Amazon EBS 핵심 요약](figures/infographic.svg)

*Figure: Amazon EBS 한 장 요약 인포그래픽*

# Amazon EBS(Elastic Block Store) 개요

## 개요

Amazon EBS(Elastic Block Store)는 EC2 인스턴스에 부착할 수 있는 고가용성, 고성능 블록 스토리지 서비스입니다. EC2 인스턴스가 사용하는 인스턴스 스토어(Instance Store)는 인스턴스가 종료되면 데이터가 사라지는 휘발성 스토리지인 반면, EBS는 인스턴스 라이프사이클과 독립적으로 데이터가 보존되는 영구(persistent) 스토리지입니다.

EBS는 기본적으로 단일 가용 영역(AZ) 내에서 자동으로 복제되어 99.8%-99.999%의 내구성을 제공하며, 스냅샷을 통해 S3에 백업하여 가용 영역 장애 또는 리전 단위 재해에도 데이터를 보호할 수 있습니다. 또한 KMS 암호화, Multi-Attach, Fast Snapshot Restore 등 엔터프라이즈 워크로드에 필요한 다양한 기능을 제공합니다.

EBS가 해결하는 핵심 문제는 다음과 같습니다.

- **인스턴스 종료 시 데이터 소실 방지**: 인스턴스 스토어와 달리 인스턴스를 종료해도 데이터 유지
- **유연한 용량 확장**: 라이브 상태에서 볼륨 크기/IOPS/Throughput을 조정 가능 (Elastic Volumes)
- **백업 자동화**: Snapshot을 통한 시점 백업, 다른 리전으로의 복사
- **고성능 데이터베이스/엔터프라이즈 워크로드**: io2 Block Express는 256K IOPS, 4000 MB/s 처리량 제공

---

## 핵심 기능

### 1. 볼륨 타입

EBS는 SSD 기반과 HDD 기반으로 나뉘며, 각각 용도가 다릅니다.

| 타입 | 카테고리 | 최대 IOPS | 최대 처리량 | 내구성 | 주 용도 |
|------|----------|-----------|-------------|--------|---------|
| gp3 (기본) | SSD 범용 | 16,000 | 1,000 MB/s | 99.8%-99.9% | 부트 볼륨, 일반 워크로드 |
| gp2 (레거시) | SSD 범용 | 16,000 | 250 MB/s | 99.8%-99.9% | 신규 사용 비권장 |
| io2 | SSD 프로비저닝 | 64,000 | 1,000 MB/s | 99.999% | OLTP, 미션 크리티컬 DB |
| io2 Block Express | SSD 프로비저닝 | 256,000 | 4,000 MB/s | 99.999% | SAP HANA, 대규모 DB |
| st1 | HDD 처리량 최적화 | 500 | 500 MB/s | 99.8%-99.9% | 빅데이터, 로그, 데이터 웨어하우스 |
| sc1 | HDD 콜드 | 250 | 250 MB/s | 99.8%-99.9% | 자주 액세스하지 않는 데이터 |

**gp3의 특징**: 2020년 출시 이후 EBS 기본 볼륨으로 자리잡았습니다. 기본 3,000 IOPS와 125 MB/s 처리량이 무료로 제공되며, 추가로 IOPS와 처리량을 독립적으로 프로비저닝할 수 있습니다. gp2 대비 GB당 약 20% 저렴합니다.

**io2 Block Express의 특징**: 2021년 출시된 차세대 io2로, 단일 볼륨에서 64TB 용량과 256,000 IOPS를 지원합니다. 99.999% 내구성으로 SAP HANA 같은 엔터프라이즈 인메모리 DB에 적합합니다.

```bash
# gp3 볼륨 생성
aws ec2 create-volume \
  --availability-zone ap-northeast-2a \
  --volume-type gp3 \
  --size 100 \
  --iops 5000 \
  --throughput 250 \
  --encrypted \
  --kms-key-id arn:aws:kms:ap-northeast-2:123456789012:key/abc \
  --tag-specifications 'ResourceType=volume,Tags=[{Key=Name,Value=my-data-volume}]' \
  --region ap-northeast-2

# io2 Block Express 볼륨 생성 (64TB)
aws ec2 create-volume \
  --availability-zone ap-northeast-2a \
  --volume-type io2 \
  --size 65536 \
  --iops 200000 \
  --multi-attach-enabled \
  --region ap-northeast-2
```

### 2. Elastic Volumes

Elastic Volumes는 라이브 상태에서 볼륨의 타입, 크기, IOPS, 처리량을 변경할 수 있는 기능입니다.

- **다운타임 없음**: 인스턴스를 중지하지 않고 변경 가능
- **변경 후 6시간 대기**: 동일 볼륨에 다음 변경을 적용하려면 6시간 대기 필요
- **파일 시스템 확장 필요**: 볼륨 크기를 늘린 후 OS 내부에서 파일 시스템도 확장해야 함

```bash
# 볼륨을 gp2 -> gp3로 변경하면서 크기 증설
aws ec2 modify-volume \
  --volume-id vol-0123456789abcdef0 \
  --volume-type gp3 \
  --size 500 \
  --iops 6000 \
  --throughput 250 \
  --region ap-northeast-2

# 변경 진행 상태 확인
aws ec2 describe-volumes-modifications \
  --volume-ids vol-0123456789abcdef0 \
  --region ap-northeast-2

# Linux에서 파일 시스템 확장 (ext4 예시)
sudo resize2fs /dev/nvme1n1
# XFS의 경우
sudo xfs_growfs -d /mnt/data
```

### 3. 스냅샷 (EBS Snapshots)

스냅샷은 EBS 볼륨의 시점 백업이며, S3에 증분식(incremental)으로 저장됩니다.

- **증분 저장**: 변경된 블록만 저장하므로 첫 스냅샷 이후 두 번째부터 빠르고 저렴
- **리전 간 복사**: 다른 리전으로 복사하여 DR 구성 가능
- **AMI 베이스**: AMI를 생성하면 EBS 스냅샷이 자동 생성됨
- **EBS Snapshots Archive**: 장기 보관용 75% 더 저렴한 스토리지 계층 (90일 이상 보관 시)

```bash
# 스냅샷 생성
aws ec2 create-snapshot \
  --volume-id vol-0123456789abcdef0 \
  --description "Daily backup 2026-04-26" \
  --tag-specifications 'ResourceType=snapshot,Tags=[{Key=Backup,Value=daily}]' \
  --region ap-northeast-2

# 스냅샷에서 볼륨 복원
aws ec2 create-volume \
  --availability-zone ap-northeast-2a \
  --snapshot-id snap-0123456789abcdef0 \
  --volume-type gp3 \
  --region ap-northeast-2

# 스냅샷을 다른 리전으로 복사 (DR)
aws ec2 copy-snapshot \
  --source-region ap-northeast-2 \
  --source-snapshot-id snap-0123456789abcdef0 \
  --destination-region us-west-2 \
  --description "DR backup" \
  --encrypted \
  --kms-key-id arn:aws:kms:us-west-2:123456789012:key/dr-key

# Snapshots Archive로 이동
aws ec2 modify-snapshot-tier \
  --snapshot-id snap-0123456789abcdef0 \
  --storage-tier archive \
  --region ap-northeast-2
```

### 4. KMS 암호화

EBS는 AWS KMS와 통합되어 데이터를 자동으로 암호화합니다.

- **저장 데이터 암호화 (AES-256-XTS)**: 볼륨, 스냅샷, AMI 모두 적용
- **계정 기본 암호화**: `EnableEbsEncryptionByDefault` 설정으로 신규 볼륨 자동 암호화
- **인스턴스-볼륨 간 데이터 전송 암호화**: Nitro 시스템 기반 인스턴스에서 자동 적용
- **암호화 무료**: KMS API 호출 비용은 발생하지만 EBS 자체 암호화는 추가 비용 없음

```bash
# 계정 기본 암호화 활성화 (리전 단위)
aws ec2 enable-ebs-encryption-by-default --region ap-northeast-2

# 기본 KMS 키 변경
aws ec2 modify-ebs-default-kms-key-id \
  --kms-key-id arn:aws:kms:ap-northeast-2:123456789012:key/my-cmk \
  --region ap-northeast-2

# 암호화되지 않은 볼륨을 암호화로 전환 (스냅샷 -> 암호화 복사 -> 새 볼륨)
aws ec2 create-snapshot --volume-id vol-unencrypted --description "to-encrypt"
aws ec2 copy-snapshot --source-snapshot-id snap-xxx --encrypted --kms-key-id alias/aws/ebs
aws ec2 create-volume --snapshot-id snap-encrypted-yyy --availability-zone ap-northeast-2a
```

### 5. Multi-Attach

Multi-Attach는 단일 io1/io2 볼륨을 최대 16개의 EC2 인스턴스에 동시에 부착하는 기능입니다.

- **지원 볼륨**: io1, io2, io2 Block Express만 가능
- **동일 AZ 내**: 동일 가용 영역의 Nitro 인스턴스만 부착 가능
- **공유 파일 시스템 필요**: ext4/XFS는 동시 쓰기 불가능 - GFS2, OCFS2 같은 클러스터 파일 시스템 필요
- **활용**: SQL Server Failover Cluster, SAP, 고가용성 클러스터링

```bash
# Multi-Attach 활성화 볼륨 생성
aws ec2 create-volume \
  --availability-zone ap-northeast-2a \
  --volume-type io2 \
  --size 500 \
  --iops 32000 \
  --multi-attach-enabled \
  --region ap-northeast-2

# 여러 인스턴스에 부착
aws ec2 attach-volume --volume-id vol-xxx --instance-id i-aaa --device /dev/sdf
aws ec2 attach-volume --volume-id vol-xxx --instance-id i-bbb --device /dev/sdf
```

---

## 아키텍처

### EBS 내부 구조

```
[EC2 Instance]
      |
      v
[Nitro System (Storage Controller)]
      |
      v (NVMe over Fabrics, AZ 내부)
[EBS Storage Cluster]
      |
      v (동기 복제 - 동일 AZ 내 다중 노드)
[Persistent Block Storage]
      |
      v (스냅샷 시)
[Amazon S3 (증분 저장)]
```

1. **AZ 내 복제**: EBS 볼륨은 동일 AZ 내 여러 스토리지 서버에 자동 복제됩니다. 단, 다른 AZ로의 복제는 자동이 아니며 스냅샷을 통해 수동으로 처리해야 합니다.
2. **NVMe 인터페이스**: Nitro 기반 인스턴스는 EBS를 NVMe 디바이스로 인식합니다(`/dev/nvme1n1` 등).
3. **S3 백킹 스냅샷**: 스냅샷은 S3에 증분식으로 저장되어 99.999999999%(11 Nines) 내구성을 가집니다.

### 처리량 vs IOPS 이해

| 측정 항목 | 정의 | 영향 |
|-----------|------|------|
| IOPS | 초당 입출력 작업 수 | 작은 블록 랜덤 액세스 (DB OLTP) |
| Throughput | 초당 데이터 전송량 (MB/s) | 큰 블록 순차 액세스 (로그, 백업, 빅데이터) |
| Latency | 작업 완료까지 소요 시간 | 응답성 |

EBS의 처리량은 다음 공식과 같이 IOPS와 블록 크기로 계산됩니다.

```
Throughput (MB/s) = IOPS x I/O Size (KB) / 1024
```

예를 들어 16K I/O 크기에서 5,000 IOPS는 약 80 MB/s 처리량을 의미합니다.

### Fast Snapshot Restore (FSR)

기본적으로 스냅샷에서 새 볼륨을 만들면 처음 액세스되는 블록은 S3에서 lazy load되어 지연이 발생합니다. FSR은 스냅샷을 미리 "warm-up" 상태로 만들어 새 볼륨을 즉시 풀 성능으로 사용할 수 있게 합니다.

```bash
# FSR 활성화 (특정 AZ에 대해)
aws ec2 enable-fast-snapshot-restores \
  --availability-zones ap-northeast-2a ap-northeast-2c \
  --source-snapshot-ids snap-0123456789abcdef0 \
  --region ap-northeast-2

# 비용: AZ당 시간당 $0.75
```

---

## 실전 사용

### 1. EC2 인스턴스 + EBS 볼륨 연결

```bash
# 1) 볼륨 생성
VOLUME_ID=$(aws ec2 create-volume \
  --availability-zone ap-northeast-2a \
  --volume-type gp3 \
  --size 100 \
  --encrypted \
  --query "VolumeId" --output text \
  --region ap-northeast-2)

# 2) 인스턴스에 부착
aws ec2 attach-volume \
  --volume-id $VOLUME_ID \
  --instance-id i-0123456789abcdef0 \
  --device /dev/sdf \
  --region ap-northeast-2

# 3) 인스턴스 내부에서 파일 시스템 생성 및 마운트
sudo mkfs -t xfs /dev/nvme1n1
sudo mkdir /mnt/data
sudo mount /dev/nvme1n1 /mnt/data

# 4) /etc/fstab에 등록 (재부팅 시 자동 마운트)
UUID=$(sudo blkid -s UUID -o value /dev/nvme1n1)
echo "UUID=$UUID  /mnt/data  xfs  defaults,nofail  0  2" | sudo tee -a /etc/fstab
```

### 2. Data Lifecycle Manager (DLM)로 스냅샷 자동화

DLM은 태그 기반으로 자동 스냅샷 정책을 적용하는 관리형 서비스입니다.

```bash
# 매일 자정 스냅샷 + 7일 보관 정책
aws dlm create-lifecycle-policy \
  --description "Daily snapshots, 7-day retention" \
  --state ENABLED \
  --execution-role-arn arn:aws:iam::123456789012:role/AWSDataLifecycleManagerDefaultRole \
  --policy-details '{
    "PolicyType": "EBS_SNAPSHOT_MANAGEMENT",
    "ResourceTypes": ["VOLUME"],
    "TargetTags": [{"Key": "Backup", "Value": "daily"}],
    "Schedules": [{
      "Name": "DailySnapshots",
      "CreateRule": {"Interval": 24, "IntervalUnit": "HOURS", "Times": ["15:00"]},
      "RetainRule": {"Count": 7},
      "CopyTags": true
    }]
  }' \
  --region ap-northeast-2
```

### 3. CloudWatch 알람으로 EBS 모니터링

```bash
# VolumeQueueLength가 너무 높으면 IOPS 부족 신호
aws cloudwatch put-metric-alarm \
  --alarm-name ebs-high-queue-length \
  --metric-name VolumeQueueLength \
  --namespace AWS/EBS \
  --statistic Average \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=VolumeId,Value=vol-0123456789abcdef0 \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:ops-alerts \
  --region ap-northeast-2
```

---

## 가격/한도

### 가격 모델 (us-east-1)

| 항목 | 가격 |
|------|------|
| gp3 스토리지 | GB-월 $0.08 |
| gp3 IOPS (3,000 초과분) | IOPS-월 $0.005 |
| gp3 Throughput (125 MB/s 초과분) | MB/s-월 $0.04 |
| gp2 스토리지 | GB-월 $0.10 |
| io2 스토리지 | GB-월 $0.125 |
| io2 IOPS | IOPS-월 $0.065 (32,000 IOPS 이하) |
| io2 Block Express IOPS | IOPS-월 차등 (계층별) |
| st1 스토리지 | GB-월 $0.045 |
| sc1 스토리지 | GB-월 $0.015 |
| 스냅샷 (Standard) | GB-월 $0.05 |
| 스냅샷 (Archive) | GB-월 $0.0125 |
| 스냅샷 Archive 복원 | GB당 $0.03 |
| Fast Snapshot Restore | AZ당 시간당 $0.75 |

**비용 절감 팁**:
- gp2 -> gp3 마이그레이션으로 약 20% 절감
- 미사용 볼륨/스냅샷 정리 (AWS Trusted Advisor 활용)
- 90일 이상 보관 스냅샷은 Archive 계층으로 이동

### 주요 한도

| 항목 | 기본 한도 |
|------|-----------|
| 단일 볼륨 최대 크기 (gp3) | 16TB |
| 단일 볼륨 최대 크기 (io2 Block Express) | 64TB |
| 인스턴스당 EBS 볼륨 수 | 28 (Nitro 인스턴스) |
| Multi-Attach 최대 인스턴스 | 16 |
| 계정/리전 EBS 총 용량 | 50TB (조정 가능) |
| 동시 진행 가능한 스냅샷 | 수십 개 (계정/리전) |

---

## Best Practice

### 권장 패턴

1. **gp3를 기본 선택**: 신규 워크로드는 gp3로 시작, 필요시 io2/io2 Block Express로 전환
2. **계정 기본 암호화 활성화**: 누락된 암호화로 인한 컴플라이언스 위반 방지
3. **DLM으로 스냅샷 자동화**: 수동 스크립트 대신 관리형 서비스 사용
4. **CloudWatch 모니터링**: VolumeQueueLength, BurstBalance(gp2), VolumeReadOps/WriteOps 추적
5. **인스턴스 종료 시 볼륨 보존**: `DeleteOnTermination=false`로 데이터 손실 방지
6. **EBS-optimized 인스턴스 사용**: m5/c5 이상 Nitro 인스턴스는 기본 활성화
7. **스냅샷 lifecycle 정책**: 30일 후 Archive 이동, 1년 후 삭제 같은 자동화

### 안티 패턴

1. **gp2 신규 사용**: gp3가 더 빠르고 저렴
2. **io2 Block Express 남용**: 일반 워크로드에 사용하면 비용 폭증 - DB 워크로드에만 적용
3. **암호화 안 한 볼륨 운영**: 컴플라이언스 위반 + 향후 변환 작업 부담
4. **스냅샷 무한 보관**: 비용 누적 - lifecycle 정책 필수
5. **Multi-Attach + 일반 ext4/XFS**: 데이터 손상 위험 - 클러스터 파일 시스템(GFS2, OCFS2) 필요
6. **볼륨 크기만 늘리고 IOPS/처리량 미조정**: gp3는 독립 프로비저닝 가능하므로 워크로드 패턴에 맞게 튜닝

---

## 관련 서비스

| 서비스 | 관계 |
|--------|------|
| Amazon EC2 | EBS의 주된 클라이언트 |
| Amazon S3 | 스냅샷 저장 백엔드 |
| AWS KMS | EBS 암호화 키 관리 |
| AWS Backup | EBS + 다른 서비스 통합 백업 |
| Amazon EFS | 다중 인스턴스 공유 파일 시스템 (대안) |
| Amazon FSx | Windows/Lustre/NetApp 파일 스토리지 (대안) |
| AWS Storage Gateway | 온프레미스에서 EBS 스타일 스토리지 |
| Amazon RDS | 내부적으로 EBS 사용 |
| Amazon EKS (EBS CSI) | Kubernetes PVC 동적 프로비저닝 |
| Data Lifecycle Manager | 스냅샷 자동화 |

---

## 관련 문서

- [[amazon-efs-elastic-file-system-개요|Amazon EFS]] - 다중 인스턴스 공유 NFS 파일 시스템 (EBS 대안)
- [[amazon-eks-elastic-kubernetes-service-개요|Amazon EKS]] - EBS CSI Driver로 PVC 제공
- [[amazon-rds|Amazon RDS]] - 내부적으로 EBS 스토리지 사용
- [[aws-fargate-서버리스-컨테이너-실행-개요|AWS Fargate]] - 2024년부터 ECS Fargate에서 EBS 부착 지원
