## 개요

Amazon Redshift의 SUPER 데이터 타입은 반정형(semi-structured) 데이터를 네이티브로 저장하고 처리할 수 있도록 설계된 데이터 타입입니다. JSON, 배열, 구조체 등 복잡한 중첩 데이터를 별도의 파싱이나 평탄화(flattening) 없이 Redshift 테이블의 컬럼으로 직접 저장할 수 있습니다.

기존에는 JSON 데이터를 Redshift에 저장하려면 VARCHAR 컬럼에 문자열로 저장한 뒤 JSON_EXTRACT_PATH_TEXT 같은 함수로 파싱해야 했습니다. 이 방식은 타입 안전성이 없고, 쿼리 성능이 떨어지며, 복잡한 중첩 구조를 다루기 어렵다는 한계가 있었습니다.

SUPER 타입은 이러한 문제를 근본적으로 해결합니다. 데이터를 바이너리 형태로 효율적으로 저장하며, PartiQL 쿼리 언어를 통해 점 표기법(dot notation)으로 중첩 필드에 직접 접근할 수 있습니다. 또한 스키마가 달라도 동일한 컬럼에 저장할 수 있어 스키마 진화(schema evolution)를 자연스럽게 처리합니다.

## 핵심 기능

### SUPER 데이터 타입 기본

SUPER 타입은 최대 16MB까지의 데이터를 저장할 수 있으며, 다음과 같은 값들을 포함할 수 있습니다.

- JSON 객체 (key-value 쌍)
- JSON 배열
- 스칼라 값 (문자열, 숫자, 불리언, null)
- 중첩된 복합 구조

```sql
-- SUPER 컬럼이 포함된 테이블 생성
CREATE TABLE events (
    event_id BIGINT IDENTITY(1,1),
    event_time TIMESTAMP DEFAULT GETDATE(),
    event_type VARCHAR(50),
    payload SUPER
);

-- JSON 데이터 삽입
INSERT INTO events (event_type, payload)
VALUES (
    'user_action',
    JSON_PARSE('{"user_id": 12345, "action": "click", "metadata": {"page": "/products", "device": "mobile", "tags": ["promo", "summer"]}}')
);

-- 배열 데이터 삽입
INSERT INTO events (event_type, payload)
VALUES (
    'batch_update',
    JSON_PARSE('[{"id": 1, "status": "active"}, {"id": 2, "status": "inactive"}]')
);
```

### PartiQL을 활용한 쿼리

PartiQL은 SQL을 확장한 쿼리 언어로, SUPER 타입의 중첩 데이터를 점 표기법과 배열 인덱싱으로 직접 접근할 수 있습니다.

```sql
-- 점 표기법으로 중첩 필드 접근
SELECT
    event_id,
    payload.user_id AS user_id,
    payload.action AS action,
    payload.metadata.page AS page,
    payload.metadata.device AS device
FROM events
WHERE event_type = 'user_action';

-- 배열 요소 접근 (0-based 인덱싱)
SELECT
    payload[0].id AS first_id,
    payload[0].status AS first_status
FROM events
WHERE event_type = 'batch_update';

-- 배열 언네스팅 (UNNEST)
SELECT
    e.event_id,
    tag
FROM events e, e.payload.metadata.tags AS tag
WHERE e.event_type = 'user_action';
```

### SUPER 타입의 함수들

Redshift는 SUPER 타입을 다루기 위한 다양한 내장 함수를 제공합니다.

```sql
-- JSON_PARSE: 문자열을 SUPER로 변환
SELECT JSON_PARSE('{"key": "value"}');

-- JSON_SERIALIZE: SUPER를 JSON 문자열로 변환
SELECT JSON_SERIALIZE(payload) FROM events LIMIT 1;

-- JSON_TYPEOF: SUPER 값의 타입 확인
SELECT
    JSON_TYPEOF(payload) AS root_type,
    JSON_TYPEOF(payload.user_id) AS user_id_type,
    JSON_TYPEOF(payload.metadata.tags) AS tags_type
FROM events
WHERE event_type = 'user_action';

-- SUPER 값을 일반 타입으로 캐스팅
SELECT
    payload.user_id::INT AS user_id_int,
    payload.action::VARCHAR AS action_str,
    payload.metadata.page::VARCHAR AS page_str
FROM events
WHERE event_type = 'user_action';
```

### COPY를 통한 대량 로드

COPY 명령어로 S3에서 JSON 데이터를 SUPER 컬럼에 직접 로드할 수 있습니다.

```sql
-- S3에서 JSON 데이터를 SUPER 컬럼으로 로드
COPY events (event_type, payload)
FROM 's3://my-bucket/events/'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftCopyRole'
FORMAT AS JSON 'auto';

-- NOSHRED 옵션: 전체 JSON을 하나의 SUPER 값으로 로드
COPY raw_json_table (raw_data)
FROM 's3://my-bucket/raw-events/'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftCopyRole'
FORMAT AS JSON 'noshred';
```

## 아키텍처/동작 원리

### 내부 저장 구조

SUPER 타입은 내부적으로 바이너리 CBOR(Concise Binary Object Representation) 형식으로 데이터를 저장합니다. 이 방식은 JSON 텍스트 저장 대비 다음과 같은 이점을 제공합니다.

- **저장 공간 효율성**: 키 이름의 중복 제거 및 바이너리 인코딩으로 공간을 절약합니다.
- **파싱 비용 절감**: 쿼리 시 매번 JSON 문자열을 파싱할 필요가 없습니다.
- **타입 보존**: 숫자, 문자열, 불리언 등의 타입이 바이너리 레벨에서 보존됩니다.

### 쿼리 실행 흐름

1. **쿼리 파싱**: PartiQL 경로 표현식(예: `payload.metadata.page`)이 내부적으로 탐색 연산으로 변환됩니다.
2. **Predicate Pushdown**: 가능한 경우 필터 조건이 스토리지 레이어로 푸시다운됩니다.
3. **Lazy Materialization**: SUPER 값의 전체 구조가 아닌 접근된 부분만 역직렬화됩니다.
4. **타입 캐스팅**: 결과가 요청된 SQL 타입으로 변환됩니다.

### 스키마 유연성

동일한 SUPER 컬럼에 서로 다른 구조의 데이터를 저장할 수 있습니다. 이를 통해 스키마 진화를 자연스럽게 처리할 수 있습니다.

```sql
-- 서로 다른 구조의 데이터 삽입
INSERT INTO events (event_type, payload) VALUES
('v1', JSON_PARSE('{"user": "alice", "score": 100}')),
('v2', JSON_PARSE('{"user": "bob", "score": 200, "bonus": 50, "level": "gold"}'));

-- 존재하지 않는 필드 접근 시 NULL 반환
SELECT
    payload.user::VARCHAR AS user_name,
    payload.score::INT AS score,
    payload.bonus::INT AS bonus,  -- v1 레코드에서는 NULL
    payload.level::VARCHAR AS level  -- v1 레코드에서는 NULL
FROM events;
```

## 실전 활용

### IoT 이벤트 분석

다양한 디바이스에서 서로 다른 구조의 데이터를 전송하는 IoT 시나리오에서 SUPER 타입이 효과적입니다.

```sql
-- IoT 이벤트 테이블
CREATE TABLE iot_events (
    device_id VARCHAR(100),
    received_at TIMESTAMP DEFAULT GETDATE(),
    device_type VARCHAR(50),
    sensor_data SUPER
);

-- 온도 센서 데이터
INSERT INTO iot_events (device_id, device_type, sensor_data) VALUES
('temp-001', 'temperature', JSON_PARSE('{"celsius": 23.5, "humidity": 65, "location": {"lat": 37.5, "lng": 127.0}}'));

-- 모션 센서 데이터 (다른 구조)
INSERT INTO iot_events (device_id, device_type, sensor_data) VALUES
('motion-001', 'motion', JSON_PARSE('{"detected": true, "confidence": 0.95, "zone": "entrance"}'));

-- 디바이스 타입별 분석
SELECT
    device_type,
    COUNT(*) AS event_count,
    CASE device_type
        WHEN 'temperature' THEN AVG(sensor_data.celsius::FLOAT)
        ELSE NULL
    END AS avg_temp
FROM iot_events
GROUP BY device_type;
```

### 중첩 배열 분석

주문 상세 정보와 같은 중첩 배열 데이터를 UNNEST로 평탄화하여 분석할 수 있습니다.

```sql
-- 주문 테이블
CREATE TABLE orders (
    order_id BIGINT,
    customer_id INT,
    order_details SUPER
);

INSERT INTO orders VALUES (
    1001, 42,
    JSON_PARSE('{"items": [{"sku": "A001", "qty": 2, "price": 29.99}, {"sku": "B002", "qty": 1, "price": 49.99}], "shipping": {"method": "express", "cost": 5.99}}')
);

-- 주문 항목 평탄화
SELECT
    o.order_id,
    o.customer_id,
    item.sku::VARCHAR AS sku,
    item.qty::INT AS quantity,
    item.price::DECIMAL(10,2) AS unit_price,
    (item.qty::INT * item.price::DECIMAL(10,2)) AS line_total,
    o.order_details.shipping.method::VARCHAR AS shipping_method
FROM orders o, o.order_details.items AS item;
```

### AWS CLI 활용

```bash
# Redshift Data API를 통한 SUPER 타입 쿼리 실행
aws redshift-data execute-statement \
    --cluster-identifier my-cluster \
    --database dev \
    --db-user admin \
    --sql "SELECT event_type, JSON_SERIALIZE(payload) FROM events LIMIT 5"

# 쿼리 결과 확인
aws redshift-data get-statement-result \
    --id "쿼리-실행-ID"

# SUPER 컬럼이 포함된 테이블 정보 조회
aws redshift-data execute-statement \
    --cluster-identifier my-cluster \
    --database dev \
    --db-user admin \
    --sql "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'events' AND data_type = 'super'"

# S3에서 JSON 데이터 로드를 위한 Redshift 명령 실행
aws redshift-data execute-statement \
    --cluster-identifier my-cluster \
    --database dev \
    --db-user admin \
    --sql "COPY events FROM 's3://my-bucket/events/' IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftCopyRole' FORMAT AS JSON 'auto'"
```

### Materialized View와의 결합

자주 사용되는 SUPER 필드 접근 패턴을 Materialized View로 최적화할 수 있습니다.

```sql
-- 자주 사용하는 SUPER 필드를 평탄화한 MV
CREATE MATERIALIZED VIEW mv_user_events AS
SELECT
    event_id,
    event_time,
    payload.user_id::INT AS user_id,
    payload.action::VARCHAR(50) AS action,
    payload.metadata.page::VARCHAR(200) AS page,
    payload.metadata.device::VARCHAR(50) AS device
FROM events
WHERE event_type = 'user_action';

-- MV 새로고침
REFRESH MATERIALIZED VIEW mv_user_events;

-- MV를 통한 빠른 쿼리
SELECT device, COUNT(*) AS action_count
FROM mv_user_events
WHERE event_time >= DATEADD(day, -7, GETDATE())
GROUP BY device
ORDER BY action_count DESC;
```

## 모범 사례/보안

### 성능 최적화

1. **자주 접근하는 필드는 일반 컬럼으로 추출합니다.** WHERE 절이나 JOIN 조건에 빈번히 사용되는 필드는 SUPER 내부에 두지 말고 별도의 타입 지정 컬럼으로 분리하면 인덱스와 소팅 키의 혜택을 받을 수 있습니다.

2. **SUPER 컬럼의 크기를 최소화합니다.** 불필요한 필드를 제거하고 핵심 데이터만 SUPER에 저장합니다. 최대 16MB까지 가능하지만 큰 SUPER 값은 쿼리 성능에 영향을 줍니다.

3. **타입 캐스팅을 명시적으로 수행합니다.** `payload.score::INT`처럼 명시적 캐스팅을 사용하면 Redshift 옵티마이저가 더 효율적인 실행 계획을 생성할 수 있습니다.

4. **Materialized View로 자주 사용하는 패턴을 사전 계산합니다.** SUPER 필드 접근은 일반 컬럼 접근보다 비용이 크므로, 반복 쿼리는 MV로 최적화합니다.

### 데이터 모델링 가이드

```sql
-- 권장: 혼합 모델 (자주 쿼리하는 필드는 일반 컬럼, 나머지는 SUPER)
CREATE TABLE optimized_events (
    event_id BIGINT IDENTITY(1,1),
    event_time TIMESTAMP DEFAULT GETDATE() SORTKEY,
    event_type VARCHAR(50) DISTKEY,
    user_id INT,           -- 자주 필터/조인하는 필드
    action VARCHAR(50),    -- 자주 필터하는 필드
    extra_data SUPER       -- 나머지 유동적인 데이터
);
```

### 보안 고려사항

1. **민감 데이터를 SUPER 내부에 저장하지 않습니다.** SUPER 타입은 컬럼 레벨 접근 제어가 적용되지만, SUPER 내부의 특정 필드에 대한 세밀한 접근 제어는 불가능합니다.

2. **JSON 입력을 검증합니다.** 외부 소스에서 받은 JSON은 JSON_PARSE 전에 크기와 구조를 검증하여 과도하게 깊은 중첩이나 큰 데이터가 삽입되는 것을 방지합니다.

3. **감사 로깅을 활성화합니다.** SUPER 컬럼에 대한 접근을 추적하기 위해 Redshift 감사 로깅을 활성화합니다.

## 관련 서비스 비교

### Redshift SUPER vs VARCHAR + JSON 함수

| 항목 | SUPER 타입 | VARCHAR + JSON 함수 |
|------|-----------|---------------------|
| 저장 방식 | 바이너리 CBOR | 텍스트 JSON |
| 쿼리 문법 | 점 표기법 (PartiQL) | JSON_EXTRACT_PATH_TEXT |
| 타입 안전성 | 캐스팅으로 보장 | 항상 문자열 반환 |
| 중첩 접근 | 자연스러움 | 복잡하고 번거로움 |
| 배열 처리 | UNNEST 지원 | 수동 파싱 필요 |
| 성능 | 빠름 | 느림 (매번 파싱) |
| 최대 크기 | 16MB | VARCHAR 최대 65535 |

### Redshift SUPER vs DynamoDB JSON

| 항목 | Redshift SUPER | DynamoDB |
|------|---------------|----------|
| 쿼리 방식 | SQL (PartiQL) | PartiQL / API |
| 분석 쿼리 | 강력함 (집계, 조인) | 제한적 |
| 트랜잭션 | 지원 | 지원 |
| 스케일링 | 클러스터 기반 | 자동 |
| 적합 사용 사례 | 분석 워크로드 | OLTP 워크로드 |

### Redshift SUPER vs Athena JSON

| 항목 | Redshift SUPER | Athena JSON |
|------|---------------|-------------|
| 데이터 위치 | Redshift 스토리지 | S3 |
| 스키마 정의 | 불필요 (스키마온리드) | SerDe 필요 |
| 쿼리 성능 | 빠름 (로컬 저장) | S3 스캔 의존 |
| 데이터 변경 | INSERT/UPDATE/DELETE | 읽기 전용 |

## 요약

Amazon Redshift SUPER 데이터 타입은 반정형 데이터를 네이티브로 처리할 수 있는 강력한 기능입니다. JSON 데이터를 바이너리 형태로 효율적으로 저장하며, PartiQL의 점 표기법과 UNNEST를 통해 복잡한 중첩 구조를 직관적으로 쿼리할 수 있습니다.

SUPER 타입의 핵심 장점은 스키마 유연성입니다. 서로 다른 구조의 데이터를 동일한 컬럼에 저장할 수 있어 IoT 이벤트, 사용자 활동 로그, API 응답 등 스키마가 유동적인 데이터 처리에 적합합니다.

최적의 성능을 위해서는 자주 필터링하거나 조인에 사용하는 필드를 별도의 타입 지정 컬럼으로 분리하고, 나머지 유동적인 데이터만 SUPER에 저장하는 혼합 모델을 권장합니다. Materialized View를 활용하면 자주 사용하는 SUPER 필드 접근 패턴을 사전 계산하여 성능을 크게 향상시킬 수 있습니다.