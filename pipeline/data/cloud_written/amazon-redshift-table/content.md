<!-- infographic-hero -->
![Amazon Redshift Table 핵심 요약](figures/infographic.svg)

*Figure: Amazon Redshift Table 한 장 요약 인포그래픽*

## 개요

Amazon Redshift의 테이블 설계는 클러스터 성능을 결정짓는 가장 중요한 요소입니다. Redshift는 MPP(Massively Parallel Processing) 아키텍처를 채택하고 있어, 데이터가 여러 노드의 슬라이스에 어떻게 분산되고 정렬되는지에 따라 쿼리 성능이 극적으로 달라집니다.

Redshift 테이블 설계에서 핵심적으로 고려해야 할 세 가지 요소는 다음과 같습니다.

1. **분산 스타일(Distribution Style)**: 데이터가 노드 간에 어떻게 분배되는지 결정합니다.
2. **정렬 키(Sort Key)**: 각 슬라이스 내에서 데이터가 어떤 순서로 저장되는지 결정합니다.
3. **컬럼 인코딩(Encoding)**: 각 컬럼의 압축 방식을 결정합니다.

이 세 가지 요소를 적절히 설정하면 스토리지 비용을 절감하면서 동시에 쿼리 성능을 수배에서 수십 배까지 향상시킬 수 있습니다. 이 글에서는 각 요소의 동작 원리, 선택 기준, 실전 활용 방법을 상세히 다룹니다.

## 핵심 기능

### 분산 스타일 (Distribution Style)

Redshift는 데이터를 클러스터의 여러 노드에 분산 저장합니다. 분산 스타일은 이 분배 방식을 결정합니다.

#### KEY 분산

특정 컬럼의 값을 기반으로 동일한 값을 가진 행들을 같은 슬라이스에 저장합니다. 해당 컬럼으로 조인할 때 노드 간 데이터 이동(redistribution)을 최소화합니다.

```sql
-- KEY 분산: customer_id를 기준으로 분산
CREATE TABLE orders (
    order_id BIGINT NOT NULL,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(12,2),
    status VARCHAR(20)
)
DISTKEY(customer_id)
SORTKEY(order_date);

-- 같은 DISTKEY를 가진 테이블과 조인 시 co-located join 발생
CREATE TABLE customers (
    customer_id INT NOT NULL,
    customer_name VARCHAR(100),
    email VARCHAR(200),
    segment VARCHAR(30)
)
DISTKEY(customer_id)
SORTKEY(customer_id);
```

KEY 분산의 선택 기준은 다음과 같습니다.
- 조인에 자주 사용되는 컬럼
- 카디널리티(고유 값 수)가 높은 컬럼
- 값 분포가 균등한 컬럼 (데이터 스큐 방지)

#### EVEN 분산

라운드 로빈 방식으로 모든 슬라이스에 균등하게 데이터를 분배합니다. 조인 성능보다 균등한 데이터 분포가 중요할 때 적합합니다.

```sql
CREATE TABLE log_entries (
    log_id BIGINT NOT NULL,
    log_time TIMESTAMP,
    level VARCHAR(10),
    message VARCHAR(1000)
)
DISTSTYLE EVEN
SORTKEY(log_time);
```

#### ALL 분산

테이블의 전체 복사본을 모든 노드에 저장합니다. 작은 디멘전 테이블에 적합하며, 조인 시 데이터 이동이 전혀 발생하지 않습니다.

```sql
-- 소규모 디멘전 테이블에 ALL 분산 적용
CREATE TABLE product_categories (
    category_id INT NOT NULL,
    category_name VARCHAR(100),
    parent_category_id INT
)
DISTSTYLE ALL;
```

ALL 분산 주의사항은 다음과 같습니다.
- 데이터 크기가 클러스터 노드 수만큼 복제되므로 스토리지 비용이 증가합니다.
- INSERT/UPDATE/DELETE가 모든 노드에 반영되어야 하므로 쓰기 성능이 저하됩니다.
- 일반적으로 수십만 행 이하의 작은 테이블에만 적용합니다.

#### AUTO 분산

Redshift가 테이블 크기와 쿼리 패턴에 따라 자동으로 최적의 분산 스타일을 선택합니다.

```sql
CREATE TABLE auto_table (
    id BIGINT,
    data VARCHAR(200)
)
DISTSTYLE AUTO;
```

AUTO 분산은 처음에는 ALL로 시작하고 테이블이 커지면 EVEN으로 전환됩니다. Redshift Advisor의 추천에 따라 KEY로 전환될 수도 있습니다.

### 정렬 키 (Sort Key)

정렬 키는 데이터가 디스크에 저장되는 물리적 순서를 결정합니다. 적절한 정렬 키는 Zone Map을 활용한 블록 스킵핑을 가능하게 하여 I/O를 크게 줄입니다.

#### Compound Sort Key

여러 컬럼을 지정된 순서대로 정렬합니다. 정렬 키의 앞부분 컬럼이 쿼리 필터에 포함되어야 효과적입니다.

```sql
-- Compound SORTKEY: 앞쪽 컬럼부터 순서대로 사용해야 효과적
CREATE TABLE web_logs (
    request_time TIMESTAMP NOT NULL,
    user_id INT,
    url VARCHAR(500),
    response_code INT,
    response_time_ms INT
)
DISTKEY(user_id)
COMPOUND SORTKEY(request_time, user_id);
```

#### Interleaved Sort Key

여러 컬럼에 대해 동등한 가중치를 부여하여 정렬합니다. 다양한 필터 조합의 쿼리에 적합합니다.

```sql
-- Interleaved SORTKEY: 어떤 컬럼 조합으로 필터해도 효과적
CREATE TABLE product_searches (
    search_id BIGINT,
    category VARCHAR(50),
    brand VARCHAR(50),
    price_range VARCHAR(20),
    rating INT
)
DISTSTYLE EVEN
INTERLEAVED SORTKEY(category, brand, price_range);
```

Interleaved Sort Key의 주의사항은 다음과 같습니다.
- VACUUM REINDEX가 필요하며 Compound보다 비용이 높습니다.
- 컬럼 수가 4개를 초과하면 효과가 크게 감소합니다.
- 대규모 데이터 로드 후 반드시 VACUUM REINDEX를 수행해야 합니다.

### 컬럼 인코딩 (Compression Encoding)

Redshift는 컬럼형 스토리지를 사용하므로 각 컬럼에 최적의 압축 알고리즘을 적용할 수 있습니다.

```sql
-- 인코딩을 명시적으로 지정
CREATE TABLE sales_explicit_encoding (
    sale_id BIGINT ENCODE AZ64,
    sale_date DATE ENCODE AZ64,
    customer_id INT ENCODE AZ64,
    product_name VARCHAR(200) ENCODE ZSTD,
    category VARCHAR(50) ENCODE BYTEDICT,
    amount DECIMAL(10,2) ENCODE AZ64,
    notes VARCHAR(1000) ENCODE ZSTD
);
```

주요 인코딩 알고리즘은 다음과 같습니다.

| 인코딩 | 적합 데이터 유형 | 설명 |
|--------|------------------|------|
| AZ64 | 숫자, 날짜, 타임스탬프 | Amazon 독자 알고리즘, 높은 압축률 |
| ZSTD | 가변 길이 문자열 | Zstandard, 범용 압축 |
| LZO | 긴 문자열 | 빠른 압축/해제 |
| BYTEDICT | 카디널리티 낮은 문자열 | 사전 기반 압축 |
| DELTA | 연속적인 숫자/날짜 | 차이값만 저장 |
| RUNLENGTH | 연속 중복 값 | 같은 값의 반복 횟수 저장 |
| RAW | 정렬 키 첫 컬럼 | 압축 없음 |

### 테이블 유형

#### 임시 테이블 (Temporary Table)

세션 종료 시 자동 삭제되는 테이블입니다. 중간 결과 저장이나 ETL 과정에서 유용합니다.

```sql
CREATE TEMP TABLE temp_daily_summary AS
SELECT
    order_date,
    COUNT(*) AS order_count,
    SUM(total_amount) AS daily_total
FROM orders
WHERE order_date = CURRENT_DATE - INTERVAL '1 day'
GROUP BY order_date;
```

#### 딥 카피 (Deep Copy)

테이블의 데이터를 새로운 테이블로 복사하면서 정렬 상태를 최적화하는 기법입니다. VACUUM보다 빠를 수 있습니다.

```sql
-- 딥 카피 절차
CREATE TABLE orders_new (LIKE orders);
INSERT INTO orders_new SELECT * FROM orders;
DROP TABLE orders;
ALTER TABLE orders_new RENAME TO orders;
```

## 아키텍처/동작 원리

### 컬럼형 스토리지

Redshift는 행 기반이 아닌 컬럼 기반으로 데이터를 저장합니다. 각 컬럼의 데이터가 연속된 디스크 블록(1MB)에 저장되며, 쿼리에 필요한 컬럼만 읽으면 됩니다.

이 구조의 장점은 다음과 같습니다.
- 쿼리에 필요한 컬럼만 I/O하므로 불필요한 데이터 읽기가 없습니다.
- 동일 컬럼의 데이터가 모여 있어 압축 효율이 높습니다.
- Zone Map을 통한 블록 스킵핑이 가능합니다.

### Zone Map

Redshift는 각 1MB 블록에 대해 해당 블록에 저장된 값의 최솟값과 최댓값을 메타데이터로 기록합니다. 이를 Zone Map이라 하며, 쿼리의 WHERE 절과 비교하여 해당 블록을 읽을 필요가 있는지 판단합니다.

정렬 키가 올바르게 설정되어 있으면 Zone Map의 효과가 극대화됩니다. 예를 들어 `order_date`로 정렬된 테이블에서 특정 날짜 범위를 조회하면, 해당 범위 밖의 블록은 완전히 건너뜁니다.

### 데이터 분산과 쿼리 실행

1. **리더 노드**가 쿼리를 파싱하고 실행 계획을 생성합니다.
2. 실행 계획이 **컴퓨트 노드**로 전달됩니다.
3. 각 노드의 **슬라이스**가 자신이 보유한 데이터에 대해 병렬로 처리합니다.
4. 조인이 필요한 경우, 분산 키가 일치하면 로컬 조인, 아니면 재분산(redistribution)이 발생합니다.
5. 결과가 리더 노드로 집계되어 클라이언트에 반환됩니다.

## 실전 활용

### 테이블 설계 분석 및 최적화

AWS CLI와 시스템 뷰를 활용하여 기존 테이블의 설계를 분석하고 최적화할 수 있습니다.

```bash
# Redshift Advisor 추천사항 조회
aws redshift-data execute-statement \
    --cluster-identifier my-cluster \
    --database dev \
    --db-user admin \
    --sql "SELECT * FROM SVV_ALTER_TABLE_RECOMMENDATIONS ORDER BY benefit DESC LIMIT 20"

# 쿼리 실행 ID 확인 후 결과 조회
aws redshift-data describe-statement --id "실행-ID"
aws redshift-data get-statement-result --id "실행-ID"

# 테이블 크기 및 행 수 조회
aws redshift-data execute-statement \
    --cluster-identifier my-cluster \
    --database dev \
    --db-user admin \
    --sql "SELECT \"table\", size AS size_mb, tbl_rows FROM SVV_TABLE_INFO WHERE schema = 'public' ORDER BY size DESC LIMIT 20"
```

### 데이터 스큐 진단

```sql
-- 슬라이스별 데이터 분포 확인 (스큐 진단)
SELECT
    t."table" AS table_name,
    t.skew_rows,
    t.skew_sortkey1
FROM SVV_TABLE_INFO t
WHERE t.schema = 'public'
ORDER BY t.skew_rows DESC;

-- 특정 DISTKEY 컬럼의 값 분포 확인
SELECT
    customer_id,
    COUNT(*) AS row_count
FROM orders
GROUP BY customer_id
ORDER BY row_count DESC
LIMIT 20;
```

### ANALYZE와 VACUUM

```sql
-- 통계 정보 업데이트
ANALYZE orders;

-- 삭제된 행 회수 및 정렬 복원
VACUUM FULL orders;

-- 정렬만 수행
VACUUM SORT ONLY orders;

-- 삭제된 행만 회수
VACUUM DELETE ONLY orders;

-- Interleaved Sort Key 테이블은 VACUUM REINDEX 필요
VACUUM REINDEX product_searches;
```

### CTAS (CREATE TABLE AS SELECT)

```sql
-- CTAS로 최적화된 테이블 생성
CREATE TABLE orders_optimized
DISTKEY(customer_id)
SORTKEY(order_date)
AS
SELECT
    order_id,
    customer_id,
    order_date,
    total_amount,
    status
FROM orders
WHERE order_date >= '2024-01-01';
```

## 모범 사례/보안

### 테이블 설계 모범 사례

1. **분산 키 선택**: 가장 자주 조인하는 대형 팩트 테이블 간에 동일한 DISTKEY를 사용합니다. 카디널리티가 높고 데이터 분포가 균등한 컬럼을 선택합니다.

2. **정렬 키 선택**: WHERE 절의 범위 조건에 가장 빈번히 사용되는 컬럼을 정렬 키로 지정합니다. 타임스탬프 기반 필터링이 많다면 해당 컬럼이 최우선 정렬 키 후보입니다.

3. **인코딩은 AUTO로 시작합니다.** Redshift가 데이터 로드 시 자동으로 최적의 인코딩을 선택합니다. 특별한 이유가 없다면 기본값을 사용하는 것이 좋습니다.

4. **NOT NULL 제약 조건을 활용합니다.** NULL이 없는 컬럼에 NOT NULL을 지정하면 옵티마이저가 더 효율적인 실행 계획을 생성할 수 있습니다.

5. **PRIMARY KEY와 FOREIGN KEY를 정의합니다.** Redshift는 이를 강제하지 않지만, 옵티마이저 힌트로 활용합니다.

### 보안 모범 사례

1. **컬럼 레벨 접근 제어를 적용합니다.**

```sql
-- 특정 사용자에게 특정 컬럼만 접근 허용
GRANT SELECT (order_id, order_date, status) ON orders TO analyst_role;

-- 민감 컬럼 접근 제한
REVOKE SELECT (total_amount) ON orders FROM analyst_role;
```

2. **행 레벨 보안(RLS)을 적용합니다.**

```sql
-- RLS 정책 생성
CREATE RLS POLICY region_policy
WITH (region VARCHAR(50))
USING (region = current_setting('app.current_region'));

-- 테이블에 정책 적용
ATTACH RLS POLICY region_policy ON orders TO analyst_role;
ALTER TABLE orders ROW LEVEL SECURITY ON;
```

3. **감사 로깅 활성화**: STL_QUERY, STL_DDLTEXT 등의 시스템 테이블을 통해 테이블 접근 및 변경 이력을 추적합니다.

## 관련 서비스 비교

### Redshift 테이블 vs Aurora PostgreSQL 테이블

| 항목 | Redshift 테이블 | Aurora PostgreSQL |
|------|----------------|-------------------|
| 스토리지 | 컬럼형 | 행 기반 |
| 분산 | DISTKEY/EVEN/ALL | 단일 노드 스토리지 |
| 인덱스 | Zone Map (자동) | B-Tree, GIN 등 수동 |
| 압축 | 컬럼별 인코딩 | 페이지 레벨 |
| 적합 워크로드 | OLAP (분석) | OLTP (트랜잭션) |
| 트랜잭션 | 직렬화 격리 | MVCC |

### Redshift vs BigQuery 테이블

| 항목 | Redshift | BigQuery |
|------|----------|----------|
| 분산 제어 | 사용자 지정 가능 | 자동 |
| 정렬 키 | 사용자 지정 | 클러스터링 (자동 관리) |
| 파티셔닝 | DISTKEY 기반 | 시간/정수 파티셔닝 |
| VACUUM | 수동/자동 | 불필요 |
| 과금 | 프로비저닝 또는 서버리스 | 쿼리당 과금 |

## 요약

Amazon Redshift 테이블 설계는 분산 스타일, 정렬 키, 컬럼 인코딩의 세 가지 축으로 이루어집니다. 올바른 설계는 쿼리 성능을 수십 배까지 향상시킬 수 있으며, 잘못된 설계는 심각한 성능 저하와 비용 낭비를 초래합니다.

분산 키는 조인 성능에, 정렬 키는 필터링 성능에, 인코딩은 I/O 및 스토리지 효율에 직접적으로 영향을 미칩니다. SVV_TABLE_INFO, SVV_ALTER_TABLE_RECOMMENDATIONS 등의 시스템 뷰를 활용하여 지속적으로 테이블 설계를 모니터링하고 최적화하는 것이 Redshift 운영의 핵심입니다.

테이블 크기가 작은 초기 단계에서는 AUTO 분산과 기본 인코딩으로 시작하고, 데이터가 증가하고 쿼리 패턴이 확립되면 Redshift Advisor의 추천에 따라 점진적으로 최적화하는 접근을 권장합니다.