<!-- infographic-hero -->
![Amazon ElastiCache 개요 핵심 요약](figures/infographic.svg)

*Figure: Amazon ElastiCache 개요 한 장 요약 인포그래픽*

## 개요

Amazon ElastiCache는 AWS에서 제공하는 완전관리형 인메모리 데이터 스토어 및 캐시 서비스입니다. Redis OSS(Open Source Software)와 Memcached 두 가지 엔진을 지원하며, 마이크로초 단위의 응답 시간으로 데이터를 읽고 쓸 수 있습니다.

인메모리 캐싱은 현대 애플리케이션 아키텍처에서 필수적인 구성 요소입니다. 데이터베이스 쿼리 결과, API 응답, 세션 데이터 등을 캐시에 저장하면 백엔드 시스템의 부하를 줄이고, 응답 시간을 획기적으로 개선할 수 있습니다.

ElastiCache가 해결하는 핵심 문제는 다음과 같습니다.

- **데이터베이스 부하 경감**: 반복적인 읽기 쿼리를 캐시에서 처리하여 DB 부하를 줄입니다.
- **응답 시간 개선**: 밀리초 단위의 DB 응답을 마이크로초 단위로 개선합니다.
- **확장성 향상**: 읽기 트래픽의 급증에 유연하게 대응합니다.
- **세션 관리**: 분산 환경에서 사용자 세션을 중앙에서 관리합니다.

ElastiCache는 프로비저닝, 패치, 모니터링, 장애 복구, 백업 등 인프라 관리를 자동으로 처리하므로, 개발자가 캐싱 로직에만 집중할 수 있게 합니다.

## 핵심 기능

### Redis OSS vs Memcached 선택

두 엔진의 주요 차이점을 이해하는 것이 올바른 선택의 첫 단계입니다.

| 기능 | Redis OSS | Memcached |
|------|-----------|----------|
| 데이터 구조 | String, Hash, List, Set, Sorted Set, Stream 등 | String만 지원 |
| 데이터 지속성 | 지원 (RDB, AOF) | 미지원 |
| 복제 | 지원 (읽기 전용 복제본) | 미지원 |
| 클러스터 모드 | 지원 (샤딩) | 지원 (멀티스레드) |
| Pub/Sub | 지원 | 미지원 |
| Lua 스크립팅 | 지원 | 미지원 |
| 트랜잭션 | 지원 (MULTI/EXEC) | 미지원 |
| 멀티스레드 | I/O 스레딩 지원 | 네이티브 멀티스레드 |
| 적합한 사용 사례 | 범용, 복잡한 데이터, 영속성 필요 | 단순 캐싱, 멀티스레드 고성능 |

대부분의 새로운 프로젝트에서는 Redis OSS를 권장합니다. Memcached는 단순한 키-값 캐싱에 특화되어 있으며, 멀티스레드 아키텍처로 특정 워크로드에서 높은 성능을 보여줍니다.

### ElastiCache Serverless

ElastiCache Serverless는 용량 계획 없이 자동으로 스케일링되는 서버리스 캐시 옵션입니다.

```bash
# ElastiCache Serverless 캐시 생성 (Redis)
aws elasticache create-serverless-cache \
  --serverless-cache-name my-serverless-cache \
  --engine redis \
  --cache-usage-limits '{
    "DataStorage": {"Maximum": 10, "Unit": "GB"},
    "ECPUPerSecond": {"Maximum": 10000}
  }' \
  --security-group-ids sg-0123456789abcdef0 \
  --subnet-ids subnet-01 subnet-02 subnet-03

# Serverless 캐시 상태 확인
aws elasticache describe-serverless-caches \
  --serverless-cache-name my-serverless-cache
```

### Redis OSS 클러스터 생성

```bash
# 서브넷 그룹 생성
aws elasticache create-cache-subnet-group \
  --cache-subnet-group-name my-cache-subnet-group \
  --cache-subnet-group-description "Cache subnet group" \
  --subnet-ids subnet-01 subnet-02 subnet-03

# 파라미터 그룹 생성
aws elasticache create-cache-parameter-group \
  --cache-parameter-group-name my-redis-params \
  --cache-parameter-group-family redis7 \
  --description "Custom Redis 7 parameters"

# 클러스터 모드 비활성화 - 복제 그룹 생성
aws elasticache create-replication-group \
  --replication-group-id my-redis-cluster \
  --replication-group-description "Production Redis cluster" \
  --engine redis \
  --engine-version 7.1 \
  --cache-node-type cache.r7g.large \
  --num-cache-clusters 3 \
  --cache-subnet-group-name my-cache-subnet-group \
  --security-group-ids sg-0123456789abcdef0 \
  --cache-parameter-group-name my-redis-params \
  --automatic-failover-enabled \
  --multi-az-enabled \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --snapshot-retention-limit 7 \
  --preferred-snapshot-window 03:00-04:00 \
  --snapshot-name daily-snapshot

# 클러스터 상태 확인
aws elasticache describe-replication-groups \
  --replication-group-id my-redis-cluster
```

### Memcached 클러스터 생성

```bash
# Memcached 클러스터 생성
aws elasticache create-cache-cluster \
  --cache-cluster-id my-memcached-cluster \
  --engine memcached \
  --engine-version 1.6.22 \
  --cache-node-type cache.r7g.large \
  --num-cache-nodes 3 \
  --cache-subnet-group-name my-cache-subnet-group \
  --security-group-ids sg-0123456789abcdef0 \
  --az-mode cross-az
```

### 파라미터 튜닝

```bash
# Redis 파라미터 최적화
aws elasticache modify-cache-parameter-group \
  --cache-parameter-group-name my-redis-params \
  --parameter-name-values '[
    {"ParameterName": "maxmemory-policy", "ParameterValue": "allkeys-lru"},
    {"ParameterName": "timeout", "ParameterValue": "300"},
    {"ParameterName": "tcp-keepalive", "ParameterValue": "60"},
    {"ParameterName": "notify-keyspace-events", "ParameterValue": "Ex"}
  ]'
```

maxmemory-policy 옵션에 따른 동작:

- **allkeys-lru**: 모든 키 중 가장 오래 사용되지 않은 키를 제거 (가장 일반적)
- **volatile-lru**: TTL이 설정된 키 중 LRU 제거
- **allkeys-lfu**: 모든 키 중 가장 적게 사용된 키를 제거
- **noeviction**: 메모리가 가득 차면 쓰기 거부

## 아키텍처/동작 원리

### 캐싱 전략

#### Cache-Aside (Lazy Loading)

가장 일반적인 캐싱 전략입니다. 애플리케이션이 먼저 캐시를 확인하고, 캐시 미스 시 데이터베이스에서 읽어 캐시에 저장합니다.

```python
import redis
import json

redis_client = redis.Redis(
    host='my-redis-cluster.abc123.ng.0001.apn2.cache.amazonaws.com',
    port=6379,
    ssl=True,
    decode_responses=True
)

def get_user(user_id):
    """Cache-Aside 패턴으로 사용자 정보를 조회합니다."""
    cache_key = f'user:{user_id}'
    
    # 1. 캐시 확인
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 2. 캐시 미스 - DB에서 조회
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    
    # 3. 캐시에 저장 (TTL 1시간)
    if user:
        redis_client.setex(cache_key, 3600, json.dumps(user))
    
    return user
```

#### Write-Through

데이터를 쓸 때 캐시와 데이터베이스를 동시에 업데이트합니다. 캐시가 항상 최신 데이터를 보유하지만 쓰기 지연이 증가합니다.

```python
def update_user(user_id, data):
    """Write-Through 패턴으로 사용자 정보를 업데이트합니다."""
    # 1. DB 업데이트
    db.execute("UPDATE users SET ... WHERE id = %s", (user_id,))
    
    # 2. 캐시 업데이트
    cache_key = f'user:{user_id}'
    redis_client.setex(cache_key, 3600, json.dumps(data))
```

#### Write-Behind (Write-Back)

캐시에 먼저 쓰고, 비동기적으로 데이터베이스에 반영합니다. 쓰기 성능이 매우 빠르지만 데이터 유실 위험이 있습니다.

### Redis 복제 구조

ElastiCache Redis는 기본-복제본(Primary-Replica) 구조를 사용합니다. 기본 노드에서 쓰기 작업을 처리하고, 비동기 복제를 통해 복제본에 데이터를 전파합니다.

- **자동 장애 조치**: 기본 노드 장애 시 복제본이 자동으로 승격됩니다. Multi-AZ가 활성화되면 다른 AZ의 복제본이 우선 승격됩니다.
- **읽기 분산**: 리더 엔드포인트를 통해 읽기 트래픽을 복제본에 분산합니다.

### Memcached 클러스터 구조

Memcached는 복제를 지원하지 않으며, 각 노드가 독립적으로 데이터의 일부를 저장합니다. 클라이언트 측에서 일관된 해싱(Consistent Hashing)을 통해 키를 노드에 분배합니다.

## 실전 활용

### 세션 관리

분산 웹 애플리케이션에서 Redis를 세션 스토어로 활용합니다.

```python
import redis
import uuid
import json
from datetime import timedelta

class RedisSessionStore:
    def __init__(self, redis_url, session_ttl=3600):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.session_ttl = session_ttl
    
    def create_session(self, user_data):
        session_id = str(uuid.uuid4())
        session_key = f'session:{session_id}'
        self.redis.setex(
            session_key,
            self.session_ttl,
            json.dumps(user_data)
        )
        return session_id
    
    def get_session(self, session_id):
        session_key = f'session:{session_id}'
        data = self.redis.get(session_key)
        if data:
            # 세션 접근 시 TTL 연장
            self.redis.expire(session_key, self.session_ttl)
            return json.loads(data)
        return None
    
    def destroy_session(self, session_id):
        self.redis.delete(f'session:{session_id}')
```

### 리더보드 (Sorted Set 활용)

Redis의 Sorted Set을 활용한 실시간 리더보드 구현입니다.

```python
def update_score(user_id, score):
    """사용자 점수를 업데이트합니다."""
    redis_client.zadd('leaderboard', {user_id: score})

def get_top_players(count=10):
    """상위 플레이어를 조회합니다."""
    return redis_client.zrevrange('leaderboard', 0, count - 1, withscores=True)

def get_player_rank(user_id):
    """특정 사용자의 순위를 조회합니다 (0-based)."""
    rank = redis_client.zrevrank('leaderboard', user_id)
    return rank + 1 if rank is not None else None

def get_players_around(user_id, range_size=5):
    """특정 사용자 주변 순위의 플레이어를 조회합니다."""
    rank = redis_client.zrevrank('leaderboard', user_id)
    if rank is None:
        return []
    start = max(0, rank - range_size)
    end = rank + range_size
    return redis_client.zrevrange('leaderboard', start, end, withscores=True)
```

### Rate Limiting (속도 제한)

Redis를 활용한 API 속도 제한 구현입니다.

```python
def is_rate_limited(client_id, max_requests=100, window_seconds=60):
    """슬라이딩 윈도우 방식의 속도 제한을 확인합니다."""
    import time
    
    key = f'ratelimit:{client_id}'
    now = time.time()
    window_start = now - window_seconds
    
    pipe = redis_client.pipeline()
    # 윈도우 밖의 오래된 요청 제거
    pipe.zremrangebyscore(key, 0, window_start)
    # 현재 요청 추가
    pipe.zadd(key, {f'{now}': now})
    # 윈도우 내 요청 수 확인
    pipe.zcard(key)
    # TTL 설정
    pipe.expire(key, window_seconds)
    
    results = pipe.execute()
    request_count = results[2]
    
    return request_count > max_requests
```

### 캐시 무효화 패턴

```bash
# ElastiCache 이벤트 알림 구독 설정
aws elasticache create-cache-cluster \
  --cache-cluster-id my-cache \
  --notification-topic-arn arn:aws:sns:ap-northeast-2:123456789012:cache-events \
  --engine redis

# CloudWatch 메트릭 기반 캐시 적중률 모니터링
aws cloudwatch get-metric-statistics \
  --namespace AWS/ElastiCache \
  --metric-name CacheHitRate \
  --dimensions Name=CacheClusterId,Value=my-redis-cluster-001 \
  --start-time 2026-03-22T00:00:00Z \
  --end-time 2026-03-23T00:00:00Z \
  --period 3600 \
  --statistics Average
```

## 모범 사례/보안

### 보안

1. **VPC 내 배포**: ElastiCache를 프라이빗 서브넷에 배치합니다.
2. **전송 중 암호화 (TLS)**: transit-encryption-enabled를 활성화합니다.
3. **저장 시 암호화**: at-rest-encryption-enabled를 활성화합니다.
4. **Redis AUTH**: 비밀번호 기반 인증을 설정합니다.
5. **IAM 인증**: Redis 7.0 이상에서 IAM 기반 인증을 사용할 수 있습니다.

```bash
# 보안 설정이 포함된 클러스터 생성
aws elasticache create-replication-group \
  --replication-group-id secure-redis \
  --replication-group-description "Secure Redis cluster" \
  --engine redis \
  --engine-version 7.1 \
  --cache-node-type cache.r7g.large \
  --num-cache-clusters 3 \
  --at-rest-encryption-enabled \
  --transit-encryption-enabled \
  --auth-token MyStrongAuthToken123! \
  --cache-subnet-group-name private-subnet-group \
  --security-group-ids sg-0123456789abcdef0
```

### 성능 최적화

1. **적절한 TTL 설정**: 너무 짧으면 캐시 효과가 떨어지고, 너무 길면 데이터 일관성 문제가 발생합니다.
2. **키 설계**: 의미 있는 접두사를 사용하고, 키 길이를 적절히 유지합니다.
3. **직렬화 최적화**: JSON 대신 MessagePack이나 Protocol Buffers를 고려합니다.
4. **파이프라인 활용**: 여러 명령을 묶어서 네트워크 라운드트립을 줄입니다.
5. **Connection Pooling**: 연결 풀을 사용하여 연결 생성/해제 오버헤드를 줄입니다.

### 모니터링

핵심 모니터링 메트릭은 다음과 같습니다.

- **CacheHitRate**: 캐시 적중률. 80% 이상을 목표로 합니다.
- **EngineCPUUtilization**: CPU 사용률. 90%를 초과하면 스케일 업을 고려합니다.
- **DatabaseMemoryUsagePercentage**: 메모리 사용률.
- **CurrConnections**: 현재 연결 수.
- **Evictions**: 메모리 부족으로 제거된 키 수.
- **ReplicationLag**: 복제 지연 시간.

```bash
# 핵심 메트릭 알람 설정
aws cloudwatch put-metric-alarm \
  --alarm-name elasticache-high-memory \
  --namespace AWS/ElastiCache \
  --metric-name DatabaseMemoryUsagePercentage \
  --dimensions Name=CacheClusterId,Value=my-redis-cluster-001 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 3 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:cache-alerts
```

## 관련 서비스 비교

### ElastiCache vs DynamoDB DAX

| 항목 | ElastiCache | DynamoDB DAX |
|------|-------------|-------------|
| 대상 | 범용 캐싱 | DynamoDB 전용 캐싱 |
| 프로토콜 | Redis/Memcached | DynamoDB API 호환 |
| 설정 | 수동 캐시 로직 구현 | 투명한 캐싱 (코드 변경 최소) |
| 데이터 소스 | 모든 데이터 소스 | DynamoDB만 |
| 유연성 | 높음 | DynamoDB에 한정 |

### ElastiCache vs MemoryDB for Redis

MemoryDB for Redis는 Redis 호환의 내구성 있는 인메모리 데이터베이스입니다. ElastiCache가 캐시 계층에 적합하다면, MemoryDB는 인메모리 속도의 프라이머리 데이터베이스로 적합합니다. MemoryDB는 Multi-AZ 트랜잭션 로그를 통해 데이터 내구성을 보장합니다.

### ElastiCache vs CloudFront 캐싱

CloudFront는 CDN 엣지 캐싱, ElastiCache는 애플리케이션 수준 데이터 캐싱입니다. 정적 콘텐츠와 API 응답 캐싱에는 CloudFront를, 데이터베이스 쿼리 캐싱과 세션 관리에는 ElastiCache를 사용합니다.

## 요약

Amazon ElastiCache는 Redis OSS와 Memcached를 지원하는 완전관리형 인메모리 캐싱 서비스로, 마이크로초 단위의 응답 시간을 제공합니다. 대부분의 사용 사례에서는 풍부한 데이터 구조와 복제, 지속성을 제공하는 Redis OSS를 권장합니다.

Cache-Aside, Write-Through 등 적절한 캐싱 전략을 선택하고, 세션 관리, 리더보드, 속도 제한 등 다양한 패턴에 활용할 수 있습니다. ElastiCache Serverless를 사용하면 용량 계획 없이 자동 스케일링되는 캐시를 구성할 수 있습니다.

프로덕션 환경에서는 VPC 내 배포, TLS 암호화, AUTH 토큰 설정을 반드시 적용하고, CacheHitRate, 메모리 사용률, Evictions 등 핵심 메트릭을 지속적으로 모니터링해야 합니다.