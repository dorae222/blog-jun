<!-- infographic-hero -->
![Amazon RDS Blue/Green 배포 핵심 요약](figures/infographic.svg)

*Figure: Amazon RDS Blue/Green 배포 한 장 요약 인포그래픽*

## 개요

데이터베이스 변경은 애플리케이션 배포에서 가장 위험한 작업 중 하나입니다. 스키마 변경, 엔진 버전 업그레이드, 파라미터 변경 등이 예기치 않은 문제를 일으킬 경우, 롤백이 어렵고 서비스 중단이 길어질 수 있습니다.

Amazon RDS Blue/Green Deployments는 이러한 위험을 최소화하기 위해 2022년 re:Invent에서 발표된 기능입니다. 프로덕션 데이터베이스(Blue 환경)의 완전한 복제본(Green 환경)을 생성하고, Green 환경에서 변경 사항을 적용 및 검증한 후, 1분 미만의 다운타임으로 트래픽을 전환(Switchover)하는 메커니즘을 제공합니다.

이 글에서는 Blue/Green Deployments의 상세 동작 원리를 분석하고, 유사한 배포 전략인 Canary 배포와 비교하며, 실전 적용 시 고려해야 할 사항들을 정리합니다.

---

## 핵심 기능

### Blue/Green Deployments의 핵심 구성

**Blue 환경 (현재 프로덕션)**
- 현재 운영 중인 RDS 인스턴스 및 관련 리소스입니다.
- Read Replica가 있는 경우 함께 Blue 환경에 포함됩니다.
- Switchover 전까지 모든 프로덕션 트래픽을 처리합니다.

**Green 환경 (스테이징)**
- Blue 환경의 물리적 복제본입니다.
- 논리적 복제(Logical Replication)를 통해 Blue로부터 실시간 데이터 동기화가 이루어집니다.
- 변경 사항(엔진 업그레이드, 스키마 변경, 파라미터 변경 등)을 안전하게 적용할 수 있습니다.
- Blue 환경의 Read Replica도 Green 환경에 동일하게 복제됩니다.

### 지원 범위

| 항목 | 지원 여부 |
|------|----------|
| RDS for MySQL 5.7, 8.0 | 지원 |
| RDS for MariaDB 10.2+ | 지원 |
| RDS for PostgreSQL | 지원 (16.1 이상) |
| Aurora MySQL | 지원 |
| Aurora PostgreSQL | 지원 |
| Multi-AZ 인스턴스 | 지원 |
| Read Replica | 지원 (함께 복제) |
| Cross-Region Replica | 미지원 |
| Oracle, SQL Server | 미지원 |

### Switchover 과정에서 수행되는 작업

Switchover는 단순한 DNS 전환이 아닙니다. 다음 과정이 자동으로 수행됩니다.

1. Blue 환경에 대한 신규 쓰기를 차단합니다.
2. Green 환경이 Blue와 완전히 동기화될 때까지 대기합니다.
3. Blue와 Green의 DB 인스턴스 이름(식별자)을 서로 교환합니다.
4. Green이 새로운 프로덕션이 되며, 이전 Blue는 이름이 변경되어 보존됩니다.
5. 엔드포인트(DNS)가 새로운 프로덕션(이전 Green)을 가리킵니다.

```bash
# Blue/Green Deployment 생성
aws rds create-blue-green-deployment \
  --blue-green-deployment-name my-blue-green \
  --source arn:aws:rds:ap-northeast-2:123456789012:db:my-production-db \
  --target-engine-version 8.0.35 \
  --target-db-parameter-group-name my-new-params \
  --region ap-northeast-2

# 상태 확인
aws rds describe-blue-green-deployments \
  --blue-green-deployment-identifier my-blue-green \
  --region ap-northeast-2
```

---

## 아키텍처/동작 원리

### Blue/Green 내부 동작 흐름

```
[1. 생성 단계]
Blue (Production DB) 
    |--- 스냅샷 기반 복제 ---> Green (Staging DB)
    |--- Logical Replication 설정 ---> 실시간 데이터 동기화

[2. 변경 적용 단계]
Blue: 프로덕션 트래픽 처리 (변경 없음)
Green: 엔진 업그레이드 / 스키마 변경 / 파라미터 변경 적용
       + Blue로부터 데이터 동기화 지속

[3. 검증 단계]
Green: 테스트 트래픽으로 변경 사항 검증
       성능 테스트, 호환성 테스트 수행

[4. Switchover 단계]
Blue: 쓰기 차단 → Green 동기화 완료 대기
Blue ↔ Green: 식별자 교환
Green → 새 Production (기존 Blue 엔드포인트 계승)
Blue → 보존 (rollback 대비)
```

### Logical Replication의 역할

Blue/Green Deployments는 내부적으로 MySQL의 `binlog` 기반 복제 또는 PostgreSQL의 논리적 복제를 사용합니다. 이는 일반적인 물리적 복제(Physical Replication)와 다음과 같은 차이가 있습니다.

**물리적 복제**: 바이트 단위로 데이터를 복제합니다. 소스와 복제본의 엔진 버전이 동일해야 합니다.

**논리적 복제**: SQL 레벨의 변경 사항(INSERT, UPDATE, DELETE)을 복제합니다. 소스와 복제본의 엔진 버전이 다를 수 있어, 메이저 버전 업그레이드 시에도 실시간 동기화가 가능합니다.

이 논리적 복제 덕분에 Green 환경에서 엔진 버전 업그레이드를 적용하면서도 Blue로부터의 실시간 데이터 동기화를 유지할 수 있습니다.

### Switchover 시 다운타임 분석

Switchover 과정에서 다운타임은 주로 다음 요인에 의해 결정됩니다.

1. **복제 지연 해소 시간**: Green이 Blue를 완전히 따라잡는 데 걸리는 시간입니다. 쓰기 부하가 높을수록 길어집니다.
2. **연결 드레이닝**: 기존 Blue 연결이 종료되는 시간입니다.
3. **DNS 전파**: 엔드포인트가 새로운 인스턴스를 가리키는 데 걸리는 시간입니다.

AWS 공식 문서에 따르면, 일반적으로 1분 미만의 다운타임이 발생합니다. 다만, 장시간 실행 중인 트랜잭션이나 높은 쓰기 부하는 Switchover 시간을 늘릴 수 있습니다.

```bash
# Switchover 실행
aws rds switchover-blue-green-deployment \
  --blue-green-deployment-identifier bgd-abcdefghijklmnop \
  --switchover-timeout 300 \
  --region ap-northeast-2

# Switchover 후 이전 Blue 환경 삭제
aws rds delete-blue-green-deployment \
  --blue-green-deployment-identifier bgd-abcdefghijklmnop \
  --delete-target \
  --region ap-northeast-2
```

---

## 실전 활용

### 사례 1: MySQL 메이저 버전 업그레이드 (5.7 → 8.0)

메이저 버전 업그레이드는 가장 일반적인 Blue/Green 활용 사례입니다.

```bash
# 1단계: Blue/Green 배포 생성 (버전 업그레이드 포함)
aws rds create-blue-green-deployment \
  --blue-green-deployment-name mysql-57-to-80-upgrade \
  --source arn:aws:rds:ap-northeast-2:123456789012:db:prod-mysql-57 \
  --target-engine-version 8.0.35 \
  --target-db-parameter-group-name mysql80-custom-params \
  --region ap-northeast-2

# 2단계: Green 환경 상태 확인 (AVAILABLE이 될 때까지 대기)
aws rds describe-blue-green-deployments \
  --filters Name=blue-green-deployment-name,Values=mysql-57-to-80-upgrade \
  --query "BlueGreenDeployments[0].Status" \
  --output text \
  --region ap-northeast-2

# 3단계: Green 환경에서 호환성 테스트
# - 애플리케이션의 Green 엔드포인트 접속 테스트
# - 쿼리 호환성 확인 (GROUP BY, default collation 변경 등)
# - Performance Schema 활용 성능 비교

# 4단계: Switchover 실행
aws rds switchover-blue-green-deployment \
  --blue-green-deployment-identifier bgd-abcdefghijklmnop \
  --switchover-timeout 600 \
  --region ap-northeast-2
```

### 사례 2: 스키마 변경과 함께 배포

Green 환경에서 DDL(스키마 변경)을 적용한 후 Switchover하는 패턴입니다.

주의사항이 있습니다. Blue/Green 배포에서 DDL을 적용할 때, 논리적 복제가 중단되지 않도록 해야 합니다. 다음과 같은 DDL은 안전합니다.

- `ALTER TABLE ... ADD COLUMN` (기본값 있는 nullable 컬럼 추가)
- `CREATE INDEX`
- `ALTER TABLE ... MODIFY COLUMN` (호환 가능한 타입 변경)

반면, 다음과 같은 DDL은 복제를 중단시킬 수 있으므로 주의가 필요합니다.

- `ALTER TABLE ... DROP COLUMN`
- `ALTER TABLE ... RENAME COLUMN`
- `DROP TABLE`

### 사례 3: 파라미터 변경 적용

```bash
# 새 파라미터 그룹 생성 및 수정
aws rds create-db-parameter-group \
  --db-parameter-group-name mysql80-optimized \
  --db-parameter-group-family mysql8.0 \
  --description "Optimized parameters for MySQL 8.0" \
  --region ap-northeast-2

aws rds modify-db-parameter-group \
  --db-parameter-group-name mysql80-optimized \
  --parameters \
    "ParameterName=innodb_buffer_pool_size,ParameterValue={DBInstanceClassMemory*3/4},ApplyMethod=pending-reboot" \
    "ParameterName=innodb_io_capacity,ParameterValue=2000,ApplyMethod=immediate" \
  --region ap-northeast-2

# Blue/Green 배포 생성 시 새 파라미터 그룹 지정
aws rds create-blue-green-deployment \
  --blue-green-deployment-name param-change-deploy \
  --source arn:aws:rds:ap-northeast-2:123456789012:db:prod-mysql \
  --target-db-parameter-group-name mysql80-optimized \
  --region ap-northeast-2
```

### Canary 배포와의 비교

Canary 배포는 새 버전에 일부 트래픽만 먼저 라우팅하여 점진적으로 검증하는 전략입니다. 데이터베이스 영역에서의 두 전략을 비교하면 다음과 같습니다.

| 항목 | Blue/Green 배포 | Canary 배포 |
|------|----------------|-------------|
| 트래픽 전환 | 전체 트래픽 일괄 전환 | 일부 트래픽부터 점진적 전환 |
| 다운타임 | 1분 미만 (Switchover 시) | 거의 없음 (점진적 전환) |
| 데이터 일관성 | 논리적 복제로 보장 | 복잡한 이중 쓰기 필요 |
| 롤백 | 이전 Blue 환경이 보존되어 빠른 롤백 | 트래픽 비율 조정으로 롤백 |
| 구현 복잡도 | AWS 관리형 (간단) | 애플리케이션 레벨 구현 필요 |
| 비용 | Green 환경 유지 기간 동안 이중 비용 | 추가 인스턴스 비용 |
| 적합 시나리오 | 엔진 업그레이드, 파라미터 변경 | 애플리케이션 코드와 함께 배포 |

데이터베이스의 경우, 트래픽을 비율로 분할하기 어렵고 데이터 일관성 유지가 복잡하기 때문에, 순수 DB 변경에는 Blue/Green 배포가 더 적합합니다. Canary 배포는 애플리케이션 레이어에서 Route 53 가중치 기반 라우팅 등을 활용하여 전체 스택(앱 + DB)을 점진적으로 전환할 때 유용합니다.

---

## 모범 사례/보안

### Switchover 전 체크리스트

1. **복제 지연 확인**: Green 환경의 복제 지연이 0에 근접한지 확인합니다.
2. **장시간 트랜잭션 종료**: 장시간 실행 중인 트랜잭션은 Switchover를 지연시킵니다.
3. **애플리케이션 호환성 테스트**: Green 엔드포인트에 테스트 트래픽을 보내 검증합니다.
4. **유지 관리 윈도우 설정**: 트래픽이 가장 적은 시간대에 Switchover를 수행합니다.
5. **모니터링 대시보드 준비**: CloudWatch, Performance Insights 대시보드를 준비합니다.
6. **롤백 계획 수립**: Switchover 후 문제가 발생할 경우의 롤백 절차를 미리 준비합니다.

```bash
# Green 환경의 복제 지연 확인
aws rds describe-blue-green-deployments \
  --blue-green-deployment-identifier bgd-abcdefghijklmnop \
  --query "BlueGreenDeployments[0].Tasks" \
  --output json \
  --region ap-northeast-2
```

### 보안 고려사항

- **Green 환경 접근 제어**: Green 환경은 테스트 목적으로만 접근하고, 프로덕션 애플리케이션에서는 접근하지 않도록 보안 그룹을 분리합니다.
- **암호화 설정 유지**: Blue 환경이 KMS 암호화를 사용하는 경우, Green 환경도 동일한 암호화 설정이 자동으로 적용됩니다.
- **감사 로그**: Switchover 전후의 모든 작업을 CloudTrail에서 추적할 수 있습니다.

### 비용 최적화

Green 환경은 Blue와 동일한 사양으로 생성되므로, 이중 비용이 발생합니다. 비용을 최소화하려면 다음을 고려합니다.

- Green 환경 생성부터 Switchover까지의 기간을 최소화합니다.
- Switchover 후 이전 Blue 환경을 신속하게 삭제합니다.
- 불필요한 Green 환경의 Read Replica를 먼저 삭제합니다.

---

## 관련 서비스 비교

| 항목 | RDS Blue/Green | Aurora Blue/Green | RDS 수동 업그레이드 |
|------|---------------|-------------------|--------------------|
| 다운타임 | 1분 미만 | 1분 미만 | 수십 분~수 시간 |
| 실시간 동기화 | 논리적 복제 | 논리적 복제 | 없음 (스냅샷 복원) |
| 롤백 | 이전 환경 보존 | 이전 환경 보존 | 스냅샷 복원 (수십 분) |
| 테스트 가능 | Green에서 사전 테스트 | Green에서 사전 테스트 | 별도 테스트 환경 필요 |
| Read Replica 포함 | 자동 복제 | 자동 복제 | 수동 재생성 필요 |
| 비용 | 이중 비용 (일시적) | 이중 비용 (일시적) | 추가 비용 없음 |

---

## 요약

Amazon RDS Blue/Green Deployments는 데이터베이스 변경을 안전하고 신속하게 수행할 수 있는 강력한 도구입니다.

1. **프로덕션 영향 최소화**: Blue 환경은 변경 없이 운영되며, 모든 변경은 Green에서 수행됩니다.
2. **1분 미만 Switchover**: 논리적 복제를 통한 실시간 동기화 덕분에 매우 짧은 다운타임으로 전환됩니다.
3. **안전한 롤백**: Switchover 후에도 이전 Blue 환경이 보존되어 빠른 롤백이 가능합니다.
4. **메이저 버전 업그레이드에 최적**: 물리적 복제가 불가능한 버전 간 업그레이드에서도 논리적 복제로 동기화를 유지합니다.
5. **Canary 배포와 상호 보완적**: 순수 DB 변경에는 Blue/Green, 전체 스택 배포에는 Canary를 적용하는 전략이 효과적입니다.
6. **비용 주의**: Green 환경 유지 기간을 최소화하여 이중 비용을 관리해야 합니다.

프로덕션 데이터베이스의 엔진 업그레이드, 파라미터 변경, 인스턴스 클래스 변경 등 위험이 수반되는 작업에서는 Blue/Green Deployments를 적극 활용하는 것을 권장합니다.