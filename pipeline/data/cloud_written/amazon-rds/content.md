<!-- infographic-hero -->
![Amazon RDS 핵심 요약](figures/infographic.svg)

*Figure: Amazon RDS 한 장 요약 인포그래픽*

## 개요

Amazon RDS(Relational Database Service)는 AWS에서 제공하는 완전 관리형 관계형 데이터베이스 서비스입니다. 인프라 프로비저닝, 패치 적용, 백업, 복구 등 데이터베이스 운영에 필요한 반복적이고 복잡한 관리 작업을 AWS가 대신 수행하므로, 개발자는 애플리케이션 로직과 스키마 설계에 집중할 수 있습니다.

RDS는 다음 6가지 데이터베이스 엔진을 지원합니다.

- **Amazon Aurora** (MySQL/PostgreSQL 호환)
- **MySQL**
- **PostgreSQL**
- **MariaDB**
- **Oracle Database**
- **Microsoft SQL Server**

온프레미스에서 직접 데이터베이스를 운영하면 하드웨어 조달, OS 설치, DB 엔진 설치 및 패치, 백업 스크립트 작성, 모니터링 구성, 고가용성 클러스터 구성 등 수많은 작업이 필요합니다. RDS는 이 모든 작업을 추상화하여 API 호출 또는 콘솔 클릭 몇 번으로 프로덕션급 데이터베이스를 배포할 수 있게 합니다.

---

## 핵심 기능

### 1. DB 인스턴스 클래스

RDS DB 인스턴스는 용도에 따라 세 가지 클래스로 나뉩니다.

| 클래스 | 접두사 | 용도 |
|--------|--------|------|
| 표준(Standard) | db.m5, db.m6g, db.m7g | 범용 워크로드 |
| 메모리 최적화(Memory Optimized) | db.r5, db.r6g, db.x2g | 대용량 캐시, 인메모리 분석 |
| 버스터블(Burstable) | db.t3, db.t4g | 개발/테스트, 간헐적 트래픽 |

Graviton 기반 인스턴스(db.m6g, db.r6g, db.t4g 등)는 x86 대비 최대 20% 향상된 가격 대비 성능을 제공하므로, 신규 워크로드에서는 Graviton 인스턴스를 우선 고려하는 것이 좋습니다.

```bash
# 사용 가능한 DB 인스턴스 클래스 조회
aws rds describe-orderable-db-instance-options \
  --engine postgres \
  --engine-version 15.4 \
  --query "OrderableDBInstanceOptions[].DBInstanceClass" \
  --output table \
  --region ap-northeast-2
```

### 2. 스토리지 유형

RDS는 세 가지 EBS 기반 스토리지를 지원합니다.

- **gp3 (General Purpose SSD)**: 기본 3,000 IOPS + 125 MiB/s 처리량 포함. IOPS와 처리량을 독립적으로 프로비저닝 가능. 대부분의 워크로드에 권장됩니다.
- **io1/io2 (Provisioned IOPS SSD)**: 최대 256,000 IOPS. 일관된 I/O 성능이 필요한 OLTP 워크로드에 적합합니다.
- **magnetic (Standard)**: 레거시 지원용. 신규 생성 시 사용을 권장하지 않습니다.

```bash
# gp3 스토리지로 PostgreSQL 인스턴스 생성
aws rds create-db-instance \
  --db-instance-identifier my-postgres-db \
  --db-instance-class db.r6g.large \
  --engine postgres \
  --engine-version 15.4 \
  --master-username admin \
  --master-user-password "YourSecurePassword123!" \
  --allocated-storage 100 \
  --storage-type gp3 \
  --iops 3000 \
  --storage-throughput 125 \
  --vpc-security-group-ids sg-0123456789abcdef0 \
  --db-subnet-group-name my-db-subnet-group \
  --backup-retention-period 7 \
  --multi-az \
  --region ap-northeast-2
```

### 3. Multi-AZ 배포

Multi-AZ는 RDS의 고가용성(HA) 핵심 기능입니다. 두 가지 방식이 있습니다.

**Multi-AZ 인스턴스 배포 (기존 방식)**
- Primary와 Standby 인스턴스가 서로 다른 AZ에 배포됩니다.
- 동기식 복제(Synchronous Replication)로 데이터 일관성을 보장합니다.
- 장애 시 자동 Failover가 수행되며, DNS 엔드포인트는 변경되지 않습니다.
- Failover 소요 시간은 일반적으로 60~120초입니다.

**Multi-AZ DB 클러스터 배포 (신규)**
- Writer 인스턴스 1개 + Reader 인스턴스 2개로 구성됩니다.
- Reader 인스턴스는 읽기 트래픽을 처리할 수 있어 읽기 확장에 유리합니다.
- 준동기식(Semi-Synchronous) 복제를 사용합니다.
- Failover 시간이 35초 이내로 단축됩니다.

```bash
# Multi-AZ DB 클러스터 생성 (MySQL)
aws rds create-db-cluster \
  --db-cluster-identifier my-multi-az-cluster \
  --engine mysql \
  --engine-version 8.0.35 \
  --master-username admin \
  --master-user-password "YourSecurePassword123!" \
  --db-cluster-instance-class db.r6gd.xlarge \
  --allocated-storage 100 \
  --storage-type io1 \
  --iops 3000 \
  --availability-zones ap-northeast-2a ap-northeast-2b ap-northeast-2c \
  --region ap-northeast-2
```

### 4. Read Replica

Read Replica는 읽기 트래픽을 분산하여 데이터베이스 성능을 수평 확장하는 기능입니다.

- **비동기식 복제**: Primary에서 Replica로 비동기 복제가 이루어집니다. 약간의 복제 지연(Replication Lag)이 발생할 수 있습니다.
- **최대 15개**: 하나의 소스 인스턴스에서 최대 15개의 Read Replica를 생성할 수 있습니다.
- **Cross-Region**: 다른 리전에도 Read Replica를 생성하여 DR(Disaster Recovery) 또는 지리적 분산 읽기에 활용 가능합니다.
- **승격(Promotion)**: Read Replica를 독립 인스턴스로 승격할 수 있습니다. DR 시나리오에서 유용합니다.

```bash
# Read Replica 생성
aws rds create-db-instance-read-replica \
  --db-instance-identifier my-read-replica \
  --source-db-instance-identifier my-postgres-db \
  --db-instance-class db.r6g.large \
  --region ap-northeast-2

# Read Replica의 복제 지연 확인
aws rds describe-db-instances \
  --db-instance-identifier my-read-replica \
  --query "DBInstances[0].StatusInfos" \
  --region ap-northeast-2
```

### 5. 자동 백업 및 스냅샷

RDS는 두 가지 백업 메커니즘을 제공합니다.

**자동 백업 (Automated Backups)**
- 매일 지정된 백업 윈도우 동안 자동으로 전체 스냅샷을 생성합니다.
- 트랜잭션 로그를 5분마다 S3에 저장합니다.
- 보존 기간 내 어느 시점으로든 복원(Point-in-Time Recovery, PITR)이 가능합니다.
- 보존 기간: 0~35일 (0이면 자동 백업 비활성화).

**수동 스냅샷 (Manual Snapshots)**
- 사용자가 명시적으로 생성합니다.
- 보존 기간 제한 없이 유지됩니다.
- 다른 리전으로 복사하여 DR에 활용할 수 있습니다.

```bash
# 수동 스냅샷 생성
aws rds create-db-snapshot \
  --db-instance-identifier my-postgres-db \
  --db-snapshot-identifier my-postgres-db-snapshot-20240101 \
  --region ap-northeast-2

# 특정 시점으로 복원 (PITR)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier my-postgres-db \
  --target-db-instance-identifier my-postgres-db-restored \
  --restore-time "2024-01-15T10:30:00Z" \
  --region ap-northeast-2

# 스냅샷을 다른 리전으로 복사 (DR용)
aws rds copy-db-snapshot \
  --source-db-snapshot-identifier arn:aws:rds:ap-northeast-2:123456789012:snapshot:my-postgres-db-snapshot-20240101 \
  --target-db-snapshot-identifier my-postgres-db-snapshot-dr \
  --region us-west-2
```

---

## 아키텍처/동작 원리

### RDS 내부 아키텍처

RDS 인스턴스는 내부적으로 다음과 같은 계층 구조로 동작합니다.

```
[Application] 
    |
    v
[RDS Endpoint (DNS)] 
    |
    v
[RDS Proxy (선택)] 
    |
    v
[EC2 Instance (DB Engine)]
    |
    v
[EBS Volume (Data + Logs)]
    |
    v
[S3 (Backups + Transaction Logs)]
```

1. **DNS 기반 엔드포인트**: 애플리케이션은 RDS가 제공하는 DNS 엔드포인트에 연결합니다. Failover 시 DNS가 새로운 Primary를 가리키도록 업데이트됩니다.
2. **EBS 기반 스토리지**: 데이터 파일과 로그는 EBS 볼륨에 저장됩니다. Multi-AZ에서는 EBS 볼륨도 동기식으로 복제됩니다.
3. **S3 백업**: 자동 백업과 트랜잭션 로그는 S3에 저장되어 99.999999999%(11 Nines) 내구성을 보장합니다.

### Failover 동작 원리

Multi-AZ 환경에서 Failover가 트리거되는 상황은 다음과 같습니다.

- Primary 인스턴스의 OS 또는 DB 엔진 장애
- Primary가 위치한 AZ의 네트워크 장애
- Primary 인스턴스의 EBS 볼륨 장애
- 사용자가 수동으로 Failover를 요청한 경우

Failover 프로세스는 다음 순서로 진행됩니다.

1. Primary 인스턴스 장애 감지
2. Standby 인스턴스를 새로운 Primary로 승격
3. DNS 레코드(CNAME)를 새로운 Primary IP로 업데이트
4. 이전 Primary가 복구되면 새로운 Standby로 전환

```bash
# 수동 Failover 테스트 (Multi-AZ 환경에서만 가능)
aws rds reboot-db-instance \
  --db-instance-identifier my-postgres-db \
  --force-failover \
  --region ap-northeast-2

# Failover 이벤트 확인
aws rds describe-events \
  --source-identifier my-postgres-db \
  --source-type db-instance \
  --event-categories failover \
  --duration 1440 \
  --region ap-northeast-2
```

### RDS Proxy

RDS Proxy는 데이터베이스 연결 풀링을 제공하는 완전 관리형 프록시 서비스입니다.

- **연결 풀링**: 수천 개의 애플리케이션 연결을 소수의 DB 연결로 다중화합니다.
- **Failover 시간 단축**: Proxy가 활성 연결을 유지하면서 새로운 Primary로 자동 라우팅합니다. 애플리케이션 수준의 Failover 시간이 66% 이상 단축됩니다.
- **IAM 인증 지원**: Secrets Manager와 통합하여 데이터베이스 자격 증명을 안전하게 관리합니다.
- **Lambda 통합**: 서버리스 환경에서 DB 연결 폭주를 방지하는 데 특히 효과적입니다.

```bash
# RDS Proxy 생성
aws rds create-db-proxy \
  --db-proxy-name my-db-proxy \
  --engine-family POSTGRESQL \
  --auth Description="Proxy auth",AuthScheme=SECRETS,SecretArn=arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:my-db-secret,IAMAuth=REQUIRED \
  --role-arn arn:aws:iam::123456789012:role/rds-proxy-role \
  --vpc-subnet-ids subnet-0123456789abcdef0 subnet-fedcba9876543210f \
  --region ap-northeast-2
```

---

## 실전 활용

### 1. 파라미터 그룹을 통한 튜닝

RDS에서는 DB 엔진의 설정을 파라미터 그룹으로 관리합니다. 기본 파라미터 그룹은 수정할 수 없으므로, 커스텀 파라미터 그룹을 생성하여 사용해야 합니다.

```bash
# 커스텀 파라미터 그룹 생성
aws rds create-db-parameter-group \
  --db-parameter-group-name my-postgres15-params \
  --db-parameter-group-family postgres15 \
  --description "Custom params for PostgreSQL 15" \
  --region ap-northeast-2

# 주요 파라미터 수정 (PostgreSQL 예시)
aws rds modify-db-parameter-group \
  --db-parameter-group-name my-postgres15-params \
  --parameters \
    "ParameterName=shared_buffers,ParameterValue={DBInstanceClassMemory/4},ApplyMethod=pending-reboot" \
    "ParameterName=work_mem,ParameterValue=65536,ApplyMethod=immediate" \
    "ParameterName=max_connections,ParameterValue=200,ApplyMethod=pending-reboot" \
    "ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate" \
  --region ap-northeast-2
```

### 2. Performance Insights를 활용한 성능 분석

Performance Insights는 DB 인스턴스의 부하를 시각적으로 분석할 수 있는 기능입니다. DB Load를 AAS(Average Active Sessions) 단위로 측정하여 병목 지점을 식별합니다.

```bash
# Performance Insights 활성화
aws rds modify-db-instance \
  --db-instance-identifier my-postgres-db \
  --enable-performance-insights \
  --performance-insights-retention-period 731 \
  --performance-insights-kms-key-id arn:aws:kms:ap-northeast-2:123456789012:key/my-key-id \
  --apply-immediately \
  --region ap-northeast-2

# Performance Insights 데이터 조회
aws pi get-resource-metrics \
  --service-type RDS \
  --identifier db-ABCDEFGHIJKLMNOP \
  --metric-queries '[{"Metric": "db.load.avg", "GroupBy": {"Group": "db.wait_event"}}]' \
  --start-time "2024-01-15T00:00:00Z" \
  --end-time "2024-01-15T23:59:59Z" \
  --period-in-seconds 3600 \
  --region ap-northeast-2
```

### 3. Enhanced Monitoring

Enhanced Monitoring은 OS 수준의 메트릭(CPU, 메모리, 파일 시스템, 디스크 I/O, 프로세스 목록)을 1초~60초 간격으로 수집합니다. CloudWatch의 기본 RDS 메트릭이 1분 간격인 것과 비교하면 훨씬 세밀한 모니터링이 가능합니다.

```bash
# Enhanced Monitoring 활성화 (10초 간격)
aws rds modify-db-instance \
  --db-instance-identifier my-postgres-db \
  --monitoring-interval 10 \
  --monitoring-role-arn arn:aws:iam::123456789012:role/rds-monitoring-role \
  --apply-immediately \
  --region ap-northeast-2
```

### 4. EventBridge와 연동한 자동화

RDS 이벤트를 EventBridge로 수신하여 자동화 워크플로우를 구축할 수 있습니다.

```json
{
  "source": ["aws.rds"],
  "detail-type": ["RDS DB Instance Event"],
  "detail": {
    "EventCategories": ["failover"],
    "SourceType": ["DB_INSTANCE"]
  }
}
```

```bash
# RDS 이벤트 구독 생성 (SNS 알림)
aws rds create-event-subscription \
  --subscription-name my-rds-failover-alerts \
  --sns-topic-arn arn:aws:sns:ap-northeast-2:123456789012:rds-alerts \
  --source-type db-instance \
  --event-categories failover failure \
  --source-ids my-postgres-db \
  --enabled \
  --region ap-northeast-2
```

---

## 모범 사례/보안

### 네트워크 보안

- **Private Subnet에 배치**: RDS 인스턴스는 반드시 Private Subnet에 배포하고, Public Accessibility를 비활성화합니다.
- **보안 그룹 최소 권한**: 데이터베이스 포트(예: PostgreSQL 5432)에 대해 애플리케이션 서버의 보안 그룹만 허용합니다.
- **VPC Peering / PrivateLink**: 다른 VPC에서 접근이 필요한 경우 VPC Peering 또는 PrivateLink를 사용합니다.

```bash
# 보안 그룹 인바운드 규칙 설정 (애플리케이션 SG만 허용)
aws ec2 authorize-security-group-ingress \
  --group-id sg-0123456789abcdef0 \
  --protocol tcp \
  --port 5432 \
  --source-group sg-app-server-sg-id \
  --region ap-northeast-2
```

### 암호화

- **저장 데이터 암호화(Encryption at Rest)**: KMS 키를 사용하여 EBS 볼륨, 스냅샷, Read Replica를 암호화합니다. 생성 시에만 설정 가능하며, 이미 암호화되지 않은 인스턴스를 암호화하려면 스냅샷 복사 시 암호화를 적용한 후 복원해야 합니다.
- **전송 데이터 암호화(Encryption in Transit)**: SSL/TLS 연결을 강제하여 네트워크 구간 데이터를 보호합니다.

```bash
# 암호화된 인스턴스 생성
aws rds create-db-instance \
  --db-instance-identifier my-encrypted-db \
  --db-instance-class db.r6g.large \
  --engine postgres \
  --storage-encrypted \
  --kms-key-id arn:aws:kms:ap-northeast-2:123456789012:key/my-key-id \
  --region ap-northeast-2
```

### 인증 및 접근 제어

- **IAM Database Authentication**: DB 사용자 비밀번호 대신 IAM 역할 기반 임시 토큰으로 인증합니다.
- **Secrets Manager 통합**: DB 자격 증명을 Secrets Manager에 저장하고, 자동 로테이션을 설정합니다.

```bash
# IAM DB 인증용 토큰 생성
aws rds generate-db-auth-token \
  --hostname my-postgres-db.abcdefg12345.ap-northeast-2.rds.amazonaws.com \
  --port 5432 \
  --username iam_user \
  --region ap-northeast-2
```

### 운영 모범 사례

1. **백업 보존 기간**: 프로덕션 환경에서는 최소 7일 이상으로 설정합니다.
2. **유지 관리 윈도우**: 트래픽이 가장 적은 시간대로 설정합니다.
3. **마이너 버전 자동 업그레이드**: 보안 패치를 위해 활성화를 권장합니다.
4. **삭제 보호(Deletion Protection)**: 프로덕션 인스턴스에는 반드시 활성화합니다.
5. **태깅**: 비용 추적 및 접근 제어를 위해 일관된 태깅 전략을 수립합니다.

---

## 관련 서비스 비교

| 항목 | Amazon RDS | Amazon Aurora | Amazon DynamoDB |
|------|-----------|---------------|------------------|
| 유형 | 관계형 (관리형) | 관계형 (클라우드 네이티브) | NoSQL (키-값/문서) |
| 엔진 | MySQL, PostgreSQL, Oracle, SQL Server, MariaDB | MySQL, PostgreSQL 호환 | 독자 엔진 |
| 스토리지 | EBS 기반 (최대 64TB) | 공유 분산 스토리지 (최대 128TB) | 자동 관리 |
| 복제 | Multi-AZ (동기), Read Replica (비동기) | 3개 AZ에 6개 복사본 자동 | 글로벌 테이블 (multi-region) |
| Failover | 60~120초 | 30초 미만 | 해당 없음 (서버리스) |
| 가격 모델 | 인스턴스 시간 + 스토리지 | 인스턴스 시간 + I/O 또는 스토리지 | 온디맨드/프로비저닝 RCU/WCU |
| 적합 워크로드 | 전통적 RDBMS 워크로드 | 고성능/고가용성 RDBMS | 대규모 키-값 조회, 밀리초 지연 |

**RDS vs Aurora 선택 기준**

- **RDS를 선택하는 경우**: 기존 온프레미스 DB를 최소 변경으로 마이그레이션하려는 경우, Oracle/SQL Server 엔진이 필요한 경우, 비용 최적화가 최우선인 소규모 워크로드.
- **Aurora를 선택하는 경우**: MySQL/PostgreSQL 워크로드에서 RDS 대비 3~5배 성능이 필요한 경우, 128TB까지 자동 확장이 필요한 경우, 30초 미만 Failover가 필요한 경우.

---

## 요약

Amazon RDS는 관계형 데이터베이스의 운영 복잡성을 대폭 줄여주는 핵심 AWS 서비스입니다. 주요 포인트를 정리하면 다음과 같습니다.

1. **6가지 엔진 지원**으로 대부분의 관계형 DB 워크로드를 커버합니다.
2. **Multi-AZ**를 통해 고가용성을, **Read Replica**를 통해 읽기 확장성을 확보합니다.
3. **자동 백업 + PITR**로 최대 35일 내 어느 시점으로든 복구가 가능합니다.
4. **Performance Insights + Enhanced Monitoring**으로 성능 병목을 신속하게 진단합니다.
5. **RDS Proxy**는 서버리스 환경이나 연결 수가 많은 환경에서 필수입니다.
6. **저장/전송 암호화, IAM 인증, Secrets Manager 연동**으로 보안을 강화합니다.
7. 고성능이 필요한 MySQL/PostgreSQL 워크로드에서는 **Aurora**로의 전환을 고려합니다.

RDS는 AWS 기반 아키텍처에서 가장 많이 사용되는 데이터 서비스 중 하나이며, 올바른 인스턴스 클래스 선택, Multi-AZ 구성, 적절한 백업 전략 수립이 안정적인 운영의 핵심입니다.