## 개요

Amazon Aurora는 AWS가 클라우드 환경에 최적화하여 설계한 완전관리형 관계형 데이터베이스 서비스입니다. MySQL 및 PostgreSQL과 호환되면서도, 상용 데이터베이스 수준의 성능과 가용성을 오픈소스 데이터베이스의 비용 효율성으로 제공합니다.

AWS에 따르면 Aurora는 표준 MySQL 대비 최대 5배, 표준 PostgreSQL 대비 최대 3배의 처리량을 제공합니다. 이러한 성능 향상은 스토리지와 컴퓨팅을 분리한 클라우드 네이티브 아키텍처에서 비롯됩니다.

Aurora의 핵심 차별점은 다음과 같습니다.

- 3개 가용 영역에 걸쳐 6개 데이터 복사본을 자동으로 유지합니다.
- 스토리지가 10GB 단위로 최대 128TB까지 자동 확장됩니다.
- 장애 발생 시 30초 이내 자동 장애 조치(Failover)를 수행합니다.
- 연속 백업을 S3에 저장하여 특정 시점 복원(PITR)을 지원합니다.
- 최대 15개의 읽기 전용 복제본을 지원합니다.

## 핵심 기능

### Aurora 클러스터 구성

Aurora 클러스터는 하나의 기본(Primary) 인스턴스와 최대 15개의 Aurora 복제본으로 구성됩니다. 모든 인스턴스는 공유 클러스터 볼륨(Cluster Volume)에 연결됩니다.

```bash
# Aurora MySQL 클러스터 생성
aws rds create-db-cluster \
  --db-cluster-identifier my-aurora-cluster \
  --engine aurora-mysql \
  --engine-version 8.0.mysql_aurora.3.04.0 \
  --master-username admin \
  --master-user-password MySecurePassword123! \
  --db-subnet-group-name my-db-subnet-group \
  --vpc-security-group-ids sg-0123456789abcdef0 \
  --storage-encrypted \
  --kms-key-id arn:aws:kms:ap-northeast-2:123456789012:key/abc-123 \
  --backup-retention-period 35 \
  --preferred-backup-window 03:00-04:00 \
  --preferred-maintenance-window Mon:04:00-Mon:05:00

# 기본(Writer) 인스턴스 생성
aws rds create-db-instance \
  --db-instance-identifier my-aurora-writer \
  --db-cluster-identifier my-aurora-cluster \
  --engine aurora-mysql \
  --db-instance-class db.r6g.xlarge \
  --availability-zone ap-northeast-2a

# 읽기 전용 복제본 생성
aws rds create-db-instance \
  --db-instance-identifier my-aurora-reader-1 \
  --db-cluster-identifier my-aurora-cluster \
  --engine aurora-mysql \
  --db-instance-class db.r6g.xlarge \
  --availability-zone ap-northeast-2b

aws rds create-db-instance \
  --db-instance-identifier my-aurora-reader-2 \
  --db-cluster-identifier my-aurora-cluster \
  --engine aurora-mysql \
  --db-instance-class db.r6g.large \
  --availability-zone ap-northeast-2c
```

### 엔드포인트 유형

Aurora는 여러 유형의 엔드포인트를 제공하여 읽기/쓰기 트래픽을 효율적으로 라우팅합니다.

- **클러스터 엔드포인트 (Writer Endpoint)**: 기본 인스턴스에 연결합니다. 쓰기 작업에 사용합니다.
- **리더 엔드포인트 (Reader Endpoint)**: 읽기 전용 복제본에 로드 밸런싱됩니다.
- **사용자 정의 엔드포인트 (Custom Endpoint)**: 특정 인스턴스 그룹에 연결합니다. 분석 쿼리용 대형 인스턴스 그룹 등에 활용합니다.
- **인스턴스 엔드포인트**: 개별 인스턴스에 직접 연결합니다.

```bash
# 사용자 정의 엔드포인트 생성
aws rds create-db-cluster-endpoint \
  --db-cluster-identifier my-aurora-cluster \
  --db-cluster-endpoint-identifier analytics-endpoint \
  --endpoint-type READER \
  --static-members my-aurora-reader-2

# 클러스터 엔드포인트 정보 조회
aws rds describe-db-cluster-endpoints \
  --db-cluster-identifier my-aurora-cluster
```

### Aurora Serverless v2

Aurora Serverless v2는 워크로드에 따라 자동으로 컴퓨팅 용량을 확장/축소합니다. ACU(Aurora Capacity Unit) 단위로 스케일링되며, 0.5 ACU에서 최대 256 ACU까지 조절됩니다.

```bash
# Aurora Serverless v2 클러스터 생성
aws rds create-db-cluster \
  --db-cluster-identifier my-serverless-cluster \
  --engine aurora-mysql \
  --engine-version 8.0.mysql_aurora.3.04.0 \
  --master-username admin \
  --master-user-password MySecurePassword123! \
  --db-subnet-group-name my-db-subnet-group \
  --vpc-security-group-ids sg-0123456789abcdef0 \
  --serverless-v2-scaling-configuration MinCapacity=0.5,MaxCapacity=64

# Serverless v2 인스턴스 생성
aws rds create-db-instance \
  --db-instance-identifier my-serverless-instance \
  --db-cluster-identifier my-serverless-cluster \
  --engine aurora-mysql \
  --db-instance-class db.serverless

# 스케일링 구성 수정
aws rds modify-db-cluster \
  --db-cluster-identifier my-serverless-cluster \
  --serverless-v2-scaling-configuration MinCapacity=1,MaxCapacity=128
```

Serverless v2의 주요 장점은 다음과 같습니다.

- 초 단위의 세밀한 스케일링 (기존 v1은 분 단위)
- 프로비저닝된 인스턴스와 혼용 가능
- 글로벌 데이터베이스, Multi-AZ 배포 등 모든 Aurora 기능 지원

### Aurora Global Database

Aurora Global Database는 여러 AWS 리전에 걸쳐 데이터베이스를 복제합니다. 기본 리전에서 보조 리전으로 일반적으로 1초 이내의 지연 시간으로 데이터를 복제합니다.

```bash
# 글로벌 클러스터 생성 (기존 클러스터를 기본 리전으로)
aws rds create-global-cluster \
  --global-cluster-identifier my-global-db \
  --source-db-cluster-identifier arn:aws:rds:ap-northeast-2:123456789012:cluster:my-aurora-cluster

# 보조 리전에 클러스터 추가
aws rds create-db-cluster \
  --db-cluster-identifier my-aurora-secondary \
  --engine aurora-mysql \
  --engine-version 8.0.mysql_aurora.3.04.0 \
  --global-cluster-identifier my-global-db \
  --db-subnet-group-name secondary-subnet-group \
  --region us-east-1

# 보조 리전에 인스턴스 생성
aws rds create-db-instance \
  --db-instance-identifier secondary-reader \
  --db-cluster-identifier my-aurora-secondary \
  --engine aurora-mysql \
  --db-instance-class db.r6g.xlarge \
  --region us-east-1

# 장애 조치 (보조 리전을 기본으로 승격)
aws rds failover-global-cluster \
  --global-cluster-identifier my-global-db \
  --target-db-cluster-identifier arn:aws:rds:us-east-1:123456789012:cluster:my-aurora-secondary
```

### 병렬 쿼리 (Parallel Query)

분석 쿼리의 성능을 향상시키기 위해 스토리지 계층에서 쿼리 처리를 병렬화하는 기능입니다. OLTP와 OLAP 워크로드를 하나의 클러스터에서 동시에 처리할 수 있습니다.

```bash
# 병렬 쿼리 활성화된 클러스터 생성
aws rds create-db-cluster \
  --db-cluster-identifier parallel-query-cluster \
  --engine aurora-mysql \
  --engine-version 8.0.mysql_aurora.3.04.0 \
  --master-username admin \
  --master-user-password MySecurePassword123! \
  --db-subnet-group-name my-db-subnet-group \
  --engine-mode parallelquery
```

## 아키텍처/동작 원리

### 분산 스토리지 아키텍처

Aurora의 핵심은 컴퓨팅과 스토리지의 분리입니다. 기존 데이터베이스는 각 인스턴스가 자체 스토리지를 가지지만, Aurora는 모든 인스턴스가 하나의 공유 클러스터 볼륨에 연결됩니다.

클러스터 볼륨은 3개 가용 영역에 걸쳐 분산되며, 각 가용 영역에 2개씩 총 6개의 데이터 복사본을 유지합니다. 이 설계의 핵심 원리는 다음과 같습니다.

- **쓰기**: 6개 복사본 중 4개에 쓰기가 성공하면 커밋으로 인정합니다 (4/6 쿼럼).
- **읽기**: 6개 복사본 중 3개에서 읽기가 성공하면 데이터를 반환합니다 (3/6 쿼럼).
- **자가 복구**: 장애가 발생한 복사본은 나머지 복사본에서 자동으로 복구됩니다.

이 쿼럼 기반 설계 덕분에, 하나의 가용 영역이 완전히 장애가 나더라도(2개 복사본 손실) 데이터 손실 없이 읽기와 쓰기가 모두 가능합니다. 2개의 가용 영역이 동시에 장애가 나더라도 읽기는 가능합니다.

### 로그 기반 복제

Aurora는 전통적인 데이터베이스처럼 데이터 페이지 전체를 복제하지 않고, Redo 로그만 스토리지에 전송합니다. 스토리지 노드가 로그를 받아 비동기적으로 데이터 페이지를 재구성합니다. 이 방식은 네트워크 I/O를 크게 줄여 성능을 향상시킵니다.

### 복제본 지연

Aurora 복제본은 기본 인스턴스와 동일한 스토리지 볼륨을 공유하므로, 복제 지연이 일반적으로 20밀리초 이하입니다. 이는 MySQL의 비동기 복제 방식(초~분 단위 지연)보다 훨씬 빠릅니다.

### 장애 조치 메커니즘

기본 인스턴스에 장애가 발생하면, Aurora는 자동으로 읽기 전용 복제본 중 하나를 새로운 기본 인스턴스로 승격합니다. 이 과정은 일반적으로 30초 이내에 완료됩니다. 복제본이 없는 경우 새로운 인스턴스를 생성하는데, 이 경우 시간이 더 소요됩니다.

장애 조치 우선순위는 티어(0-15)로 설정할 수 있으며, 티어 값이 낮을수록 높은 우선순위를 가집니다.

```bash
# 복제본 장애 조치 우선순위 설정
aws rds modify-db-instance \
  --db-instance-identifier my-aurora-reader-1 \
  --promotion-tier 0

# 수동 장애 조치 실행
aws rds failover-db-cluster \
  --db-cluster-identifier my-aurora-cluster \
  --target-db-instance-identifier my-aurora-reader-1
```

## 실전 활용

### 고가용성 웹 애플리케이션

```bash
# 다중 AZ Aurora 클러스터 + Serverless v2 리더 구성
aws rds create-db-cluster \
  --db-cluster-identifier webapp-cluster \
  --engine aurora-mysql \
  --engine-version 8.0.mysql_aurora.3.04.0 \
  --master-username admin \
  --master-user-password MySecurePassword123! \
  --db-subnet-group-name multi-az-subnet-group \
  --vpc-security-group-ids sg-0123456789abcdef0 \
  --storage-encrypted \
  --backup-retention-period 35 \
  --serverless-v2-scaling-configuration MinCapacity=0.5,MaxCapacity=32

# 프로비저닝된 Writer 인스턴스
aws rds create-db-instance \
  --db-instance-identifier webapp-writer \
  --db-cluster-identifier webapp-cluster \
  --engine aurora-mysql \
  --db-instance-class db.r6g.xlarge

# Serverless v2 Reader (자동 스케일링)
aws rds create-db-instance \
  --db-instance-identifier webapp-reader-sv2 \
  --db-cluster-identifier webapp-cluster \
  --engine aurora-mysql \
  --db-instance-class db.serverless
```

### 클러스터 파라미터 튜닝

```bash
# 클러스터 파라미터 그룹 생성
aws rds create-db-cluster-parameter-group \
  --db-cluster-parameter-group-name my-aurora-params \
  --db-parameter-group-family aurora-mysql8.0 \
  --description "Custom Aurora MySQL 8.0 parameters"

# 파라미터 설정
aws rds modify-db-cluster-parameter-group \
  --db-cluster-parameter-group-name my-aurora-params \
  --parameters '[
    {"ParameterName": "innodb_buffer_pool_size", "ParameterValue": "{DBInstanceClassMemory*3/4}", "ApplyMethod": "pending-reboot"},
    {"ParameterName": "max_connections", "ParameterValue": "2000", "ApplyMethod": "immediate"},
    {"ParameterName": "slow_query_log", "ParameterValue": "1", "ApplyMethod": "immediate"},
    {"ParameterName": "long_query_time", "ParameterValue": "1", "ApplyMethod": "immediate"}
  ]'
```

### 백업 및 복원

```bash
# 수동 스냅샷 생성
aws rds create-db-cluster-snapshot \
  --db-cluster-identifier my-aurora-cluster \
  --db-cluster-snapshot-identifier my-snapshot-20260323

# 특정 시점 복원 (PITR)
aws rds restore-db-cluster-to-point-in-time \
  --source-db-cluster-identifier my-aurora-cluster \
  --db-cluster-identifier restored-cluster \
  --restore-to-time 2026-03-23T10:00:00Z \
  --db-subnet-group-name my-db-subnet-group

# 스냅샷에서 복원
aws rds restore-db-cluster-from-snapshot \
  --db-cluster-identifier restored-from-snapshot \
  --snapshot-identifier my-snapshot-20260323 \
  --engine aurora-mysql

# 복원 가능한 시점 조회
aws rds describe-db-clusters \
  --db-cluster-identifier my-aurora-cluster \
  --query 'DBClusters[0].{EarliestRestorableTime: EarliestRestorableTime, LatestRestorableTime: LatestRestorableTime}'
```

### CloudWatch 모니터링

```bash
# Aurora 핵심 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBClusterIdentifier,Value=my-aurora-cluster \
  --start-time 2026-03-22T00:00:00Z \
  --end-time 2026-03-23T00:00:00Z \
  --period 3600 \
  --statistics Average

# 복제 지연 모니터링 알람
aws cloudwatch put-metric-alarm \
  --alarm-name aurora-replica-lag \
  --namespace AWS/RDS \
  --metric-name AuroraReplicaLag \
  --dimensions Name=DBInstanceIdentifier,Value=my-aurora-reader-1 \
  --statistic Average \
  --period 60 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 3 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:db-alerts
```

## 모범 사례/보안

### 보안

1. **전송 중 암호화**: SSL/TLS를 사용하여 클라이언트와 Aurora 간 통신을 암호화합니다.
2. **저장 시 암호화**: KMS를 사용하여 클러스터 볼륨, 스냅샷, 백업을 암호화합니다.
3. **IAM 데이터베이스 인증**: 비밀번호 대신 IAM 역할/사용자를 사용하여 인증합니다.
4. **VPC 내 배포**: Aurora를 프라이빗 서브넷에 배포하고, 보안 그룹으로 접근을 제어합니다.
5. **감사 로깅**: Advanced Auditing을 활성화하여 데이터베이스 활동을 기록합니다.

### 성능 최적화

1. **적절한 인스턴스 크기 선택**: Performance Insights를 활용하여 워크로드에 맞는 인스턴스 크기를 선택합니다.
2. **읽기/쓰기 분리**: 애플리케이션에서 읽기 트래픽을 리더 엔드포인트로 분산합니다.
3. **Connection Pooling**: RDS Proxy를 활용하여 데이터베이스 연결을 효율적으로 관리합니다.

### 비용 최적화

1. **Reserved Instances**: 장기 운영 클러스터에는 예약 인스턴스를 활용합니다.
2. **Serverless v2**: 트래픽이 변동하는 워크로드에는 Serverless v2를 활용하여 비용을 절감합니다.
3. **I/O 최적화 스토리지**: I/O 비용이 높은 워크로드에는 Aurora I/O-Optimized 구성을 고려합니다.

## 관련 서비스 비교

### Aurora vs RDS MySQL/PostgreSQL

| 항목 | Aurora | RDS MySQL/PostgreSQL |
|------|--------|---------------------|
| 스토리지 | 공유 분산 스토리지 (최대 128TB) | 인스턴스별 EBS (최대 64TB) |
| 복제본 수 | 최대 15개 | 최대 5개 (MySQL) |
| 복제 지연 | 20ms 이하 | 초~분 단위 |
| 장애 조치 | 30초 이내 | 1~2분 |
| 비용 | RDS 대비 약 20% 높음 | 기본 |
| Global Database | 지원 | 미지원 |
| Serverless | 지원 (v2) | 미지원 |

### Aurora vs DynamoDB

Aurora는 관계형 데이터베이스이고 DynamoDB는 NoSQL 데이터베이스입니다. 복잡한 조인, 트랜잭션, ACID가 필요한 워크로드에는 Aurora가 적합하고, 대규모 키-값 저장, 단순 쿼리 패턴, 무제한 스케일링이 필요한 경우에는 DynamoDB가 적합합니다.

## 요약

Amazon Aurora는 MySQL 및 PostgreSQL 호환 클라우드 네이티브 관계형 데이터베이스로, 분산 스토리지 아키텍처를 통해 높은 성능, 가용성, 내구성을 제공합니다. 3개 AZ에 6개 데이터 복사본, 쿼럼 기반 읽기/쓰기, 자동 장애 조치 등의 기능으로 프로덕션 워크로드에 적합합니다.

Serverless v2를 통한 자동 스케일링, Global Database를 통한 리전 간 복제, Parallel Query를 통한 분석 처리 등 다양한 고급 기능을 제공합니다. 프로덕션 환경에서는 암호화 활성화, 읽기/쓰기 분리, 적절한 백업 정책 설정, Performance Insights를 통한 지속적인 모니터링을 권장합니다.