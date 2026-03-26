# Amazon ElastiCache for Redis (Redis OSS) 클러스터 개요

## 개요

Amazon ElastiCache for Redis(Redis OSS) 클러스터는 AWS에서 제공하는 Redis 오픈소스 소프트웨어 기반의 완전관리형 인메모리 데이터 저장소 및 캐시 서비스입니다. Redis는 키-값 기반의 인메모리 데이터베이스로, 마이크로초 수준의 빠른 데이터 접근 속도를 제공합니다.

ElastiCache for Redis 클러스터는 여러 개의 노드(Node)로 구성되며, 이를 통해 스케일 아웃과 고가용성 구성이 가능합니다. 성능이 중요한 웹 애플리케이션, 실시간 분석, 세션 관리, 게임 리더보드, ML 피처 스토어 등에서 널리 사용되고 있습니다.

AWS는 ElastiCache를 통해 Redis 클러스터의 프로비저닝, 패치 적용, 백업, 복구, 장애 감지 등 운영 부담을 대폭 줄여줍니다. 사용자는 인프라 관리 대신 애플리케이션 로직에 집중할 수 있습니다.

## 핵심 기능

### 구성 요소 계층 구조

ElastiCache for Redis 클러스터는 다음과 같은 계층적 구조로 구성됩니다.

**노드(Node)**

노드는 실제 데이터가 저장되는 인스턴스 단위입니다. 각 노드는 고유한 DNS 이름과 포트를 가지며, 특정 크기의 메모리를 할당받습니다. cache.t3.micro부터 cache.r7g.16xlarge까지 다양한 인스턴스 유형을 선택할 수 있습니다.

**샤드(Shard)**

샤드는 Redis 데이터의 파티션 단위입니다. 하나의 샤드는 1개의 Primary 노드와 0~5개의 Replica 노드로 구성됩니다. 클러스터 모드가 활성화된 경우, 데이터는 해시 슬롯(0~16383)에 기반하여 여러 샤드에 분산 저장됩니다.

**클러스터(Cluster)**

클러스터는 여러 샤드로 구성된 전체 Redis 시스템을 의미합니다. 클러스터 모드에 따라 단일 샤드 또는 멀티 샤드로 운영할 수 있습니다.

**엔드포인트(Endpoint)**

애플리케이션이 연결할 수 있는 주소입니다. 클러스터 모드 비활성화 시에는 Primary/Reader 엔드포인트가 제공되고, 클러스터 모드 활성화 시에는 Configuration 엔드포인트가 제공됩니다.

### 클러스터 모드

**클러스터 모드 비활성화 (단일 샤드)**

- 모든 데이터가 하나의 샤드에 저장됩니다
- Primary 노드 1개와 최대 5개의 Replica 노드로 구성할 수 있습니다
- 간단한 워크로드나 캐시 용도에 적합합니다
- 자동 샤딩은 불가능하지만, 노드 유형 변경(수직 확장)은 가능합니다
- 최대 메모리는 단일 노드의 인스턴스 유형에 의해 제한됩니다

**클러스터 모드 활성화 (Multi-Shard)**

- 데이터가 여러 샤드에 해시 슬롯 기반으로 자동 분산 저장됩니다
- 최대 500개의 샤드를 구성할 수 있어 수 테라바이트 규모의 데이터를 처리할 수 있습니다
- 각 샤드에 복제본을 구성하여 고가용성을 확보할 수 있습니다
- 온라인 리샤딩으로 서비스 중단 없이 샤드 수를 조정할 수 있습니다
- 쓰기 처리량이 여러 샤드에 분산되어 수평 확장이 가능합니다

### 고가용성 기능

- Multi-AZ 배포로 Primary 노드 장애 시 자동으로 Replica를 승격합니다
- 장애 조치는 일반적으로 수 초 이내에 완료됩니다
- 자동 백업(스냅샷)으로 데이터 손실에 대비할 수 있습니다
- 글로벌 데이터스토어를 통해 리전 간 복제가 가능합니다

### 데이터 영속성

- RDB 스냅샷: 지정된 간격으로 전체 데이터 세트의 시점 스냅샷을 생성합니다
- AOF(Append Only File): 모든 쓰기 작업을 로그로 기록하여 데이터 내구성을 높입니다
- 자동 백업: 매일 자동으로 스냅샷을 생성하고 지정된 기간 동안 보관합니다

## 아키텍처/동작 원리

### 클러스터 모드 비활성화 아키텍처

```
[Application]
      |
      v
[Primary Endpoint] ---------> [Primary Node (AZ-a)]
[Reader Endpoint]  ---------> [Replica Node 1 (AZ-b)]
                   ---------> [Replica Node 2 (AZ-c)]
```

이 구조에서 쓰기 작업은 Primary 노드로, 읽기 작업은 Reader 엔드포인트를 통해 Replica 노드로 분산됩니다. Primary 노드에 장애가 발생하면 Replica 중 하나가 자동으로 Primary로 승격됩니다.

### 클러스터 모드 활성화 아키텍처

```
[Application]
      |
      v
[Configuration Endpoint]
      |
      +---> [Shard 1] Primary (Slot 0-5460)     <-> Replica
      +---> [Shard 2] Primary (Slot 5461-10922)  <-> Replica
      +---> [Shard 3] Primary (Slot 10923-16383)  <-> Replica
```

클러스터 모드 활성화 시 16384개의 해시 슬롯이 샤드에 균등하게 분배됩니다. 클라이언트는 Configuration 엔드포인트에 연결하여 샤드 매핑 정보를 얻고, 적절한 샤드로 요청을 라우팅합니다.

### 데이터 복제 흐름

Primary 노드에서 쓰기 작업이 수행되면, 해당 변경 사항이 비동기적으로 Replica 노드에 전파됩니다. 이는 최종 일관성(Eventual Consistency) 모델을 따르며, 복제 지연(Replication Lag)이 발생할 수 있습니다.

## 실전 활용

### Redis 복제 그룹 생성 (클러스터 모드 비활성화)

```bash
# 서브넷 그룹 생성
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name my-redis-subnet \
  --cache-subnet-group-description "Redis subnet group" \
  --subnet-ids subnet-0123456789abcdef0 subnet-0987654321fedcba0

# Redis 복제 그룹 생성 (클러스터 모드 비활성화, Multi-AZ)
aws elasticache create-replication-group \
  --replication-group-id my-redis-rg \
  --replication-group-description "Production Redis" \
  --engine redis \
  --engine-version 7.1 \
  --cache-node-type cache.r7g.large \
  --num-cache-clusters 3 \
  --automatic-failover-enabled \
  --multi-az-enabled \
  --cache-subnet-group-name my-redis-subnet \
  --security-group-ids sg-0123456789abcdef0 \
  --snapshot-retention-limit 7 \
  --snapshot-window 03:00-05:00 \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled
```

### Redis 복제 그룹 생성 (클러스터 모드 활성화)

```bash
# 클러스터 모드 활성화 (3 샤드, 각 1 Replica)
aws elasticache create-replication-group \
  --replication-group-id my-redis-cluster \
  --replication-group-description "Clustered Redis" \
  --engine redis \
  --engine-version 7.1 \
  --cache-node-type cache.r7g.large \
  --num-node-groups 3 \
  --replicas-per-node-group 1 \
  --automatic-failover-enabled \
  --cache-subnet-group-name my-redis-subnet \
  --security-group-ids sg-0123456789abcdef0 \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled
```

### 온라인 리샤딩

```bash
# 샤드 수를 3에서 6으로 확장
aws elasticache modify-replication-group-shard-configuration \
  --replication-group-id my-redis-cluster \
  --node-group-count 6 \
  --apply-immediately
```

### 스냅샷 생성 및 복원

```bash
# 수동 스냅샷 생성
aws elasticache create-snapshot \
  --replication-group-id my-redis-rg \
  --snapshot-name my-redis-backup-20260323

# 스냅샷에서 복원
aws elasticache create-replication-group \
  --replication-group-id my-redis-restored \
  --replication-group-description "Restored from snapshot" \
  --snapshot-name my-redis-backup-20260323 \
  --cache-node-type cache.r7g.large \
  --num-cache-clusters 3
```

### Python 클라이언트 예시 (redis-py-cluster)

```python
from redis.cluster import RedisCluster

# 클러스터 모드 활성화된 ElastiCache 연결
rc = RedisCluster(
    host='my-cluster.abc123.clustercfg.apn2.cache.amazonaws.com',
    port=6379,
    ssl=True,
    decode_responses=True
)

# 데이터 저장 및 조회
rc.set('session:user123', '{"name": "홍길동", "role": "admin"}')
session = rc.get('session:user123')

# Sorted Set으로 리더보드 구현
rc.zadd('leaderboard', {'player_a': 1500, 'player_b': 2300, 'player_c': 1800})
top_players = rc.zrevrange('leaderboard', 0, 9, withscores=True)
```

## 모범 사례 및 보안

### 클러스터 설계

- 예상 데이터 크기와 처리량에 따라 클러스터 모드(비활성화/활성화)를 결정합니다
- 클러스터 모드 활성화 시 키 분산을 고려하여 해시 태그를 적절히 활용합니다
- 메모리 사용량의 75%를 초과하지 않도록 모니터링하고, 필요 시 스케일 아웃합니다
- Reserved Nodes를 활용하면 온디맨드 대비 상당한 비용 절감이 가능합니다

### 데이터 보호

- 복제본 없이 운영할 경우 노드 장애 시 데이터가 손실될 수 있으므로, 프로덕션 환경에서는 반드시 복제본을 구성합니다
- RDB 또는 AOF 백업을 활성화하여 데이터 영속성을 확보합니다
- 자동 스냅샷의 보존 기간을 적절히 설정합니다 (최대 35일)

### 보안 설정

- VPC 내부에 배치하고 보안 그룹으로 필요한 포트(6379)만 허용합니다
- 전송 중 암호화(TLS)와 저장 시 암호화를 모두 활성화합니다
- AUTH 토큰을 설정하여 인증되지 않은 접근을 차단합니다
- IAM 인증을 활용하면 토큰 관리 없이 역할 기반 접근 제어가 가능합니다

### 성능 최적화

- 쓰기 집중 워크로드에서는 복제 지연(Replication Lag)을 모니터링합니다
- 파이프라이닝을 활용하여 여러 명령을 한 번에 전송하면 네트워크 왕복 횟수를 줄일 수 있습니다
- KEYS 명령 대신 SCAN 명령을 사용하여 프로덕션 환경에서의 블로킹을 방지합니다
- 큰 키(Large Key)를 분할하여 메모리 단편화를 방지합니다

## 관련 서비스 비교

| 항목 | ElastiCache Redis (클러스터 비활성화) | ElastiCache Redis (클러스터 활성화) | Amazon MemoryDB for Redis | Amazon ElastiCache Memcached |
|------|-------------------------------------|-------------------------------------|---------------------------|-----------------------------|
| 샤드 수 | 1개 | 최대 500개 | 최대 500개 | N/A (노드 기반) |
| 수평 확장 | 불가 (수직만 가능) | 온라인 리샤딩 가능 | 온라인 리샤딩 가능 | 노드 추가 가능 |
| 최대 메모리 | 단일 노드 한도 | 수 TB | 수 TB | 노드 수 x 노드 메모리 |
| 데이터 내구성 | RDB/AOF 선택적 | RDB/AOF 선택적 | 트랜잭션 로그 기반 내구성 보장 | 없음 |
| Multi-AZ | 지원 | 지원 | 지원 | 미지원 |
| 글로벌 복제 | 글로벌 데이터스토어 | 글로벌 데이터스토어 | 미지원 | 미지원 |
| 사용 사례 | 소규모 캐시 | 대규모 분산 캐시 | 인메모리 DB | 단순 캐시 |

- **클러스터 모드 비활성화 vs 활성화**: 데이터 크기가 단일 노드의 메모리로 충분하고 쓰기 처리량이 높지 않다면 비활성화 모드로 충분합니다. 데이터가 크거나 쓰기 확장이 필요하면 클러스터 모드를 활성화합니다.
- **ElastiCache vs MemoryDB**: ElastiCache는 캐시 용도에, MemoryDB는 인메모리 데이터베이스(내구성 보장) 용도에 적합합니다.

## 요약

Amazon ElastiCache for Redis 클러스터는 Redis OSS 기반의 완전관리형 인메모리 서비스로, 노드-샤드-클러스터의 계층적 구조를 통해 유연한 확장성과 고가용성을 제공합니다. 클러스터 모드 비활성화(단일 샤드)는 간단한 캐시 워크로드에, 클러스터 모드 활성화(멀티 샤드)는 대규모 분산 처리가 필요한 워크로드에 적합합니다. Multi-AZ 자동 장애 조치, 온라인 리샤딩, 스냅샷 백업 등 엔터프라이즈급 기능을 갖추고 있으며, 웹 캐시, 세션 관리, 실시간 리더보드, Pub/Sub 메시징, ML 피처 스토어 등 다양한 고속 데이터 처리 시나리오의 핵심 인프라로 활용됩니다.