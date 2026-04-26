<!-- infographic-hero -->
![Amazon Redshift Materialized View 핵심 요약](figures/infographic.svg)

*Figure: Amazon Redshift Materialized View 한 장 요약 인포그래픽*

## 개요

Materialized View(MV, 구체화된 뷰)는 쿼리 결과를 물리적으로 저장하는 데이터베이스 객체입니다. 일반 뷰(View)가 쿼리 실행 시마다 기반 테이블을 다시 스캔하는 반면, MV는 미리 계산된 결과를 저장해두고 조회 시 즉시 반환합니다.

Amazon Redshift의 Materialized View는 대규모 분석 쿼리에서 특히 강력합니다. 수십억 건의 팩트 테이블을 매번 집계하는 대신, MV에 집계 결과를 미리 저장하면 대시보드 쿼리의 응답 시간을 수 초에서 밀리초 수준으로 단축할 수 있습니다.

Redshift MV의 핵심 차별점은 다음과 같습니다.

- **자동 갱신(Auto Refresh)**: 기반 테이블 변경 시 자동으로 MV를 갱신합니다.
- **증분 갱신(Incremental Refresh)**: 전체 데이터를 다시 계산하지 않고, 변경된 부분만 갱신합니다.
- **쿼리 자동 리다이렉션(Automatic Query Rewriting)**: 기반 테이블을 직접 쿼리해도 옵티마이저가 MV를 자동으로 활용합니다.

---

## 핵심 기능

### 1. MV 생성

```sql
-- 기본 MV 생성
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT 
    sale_date,
    product_category,
    COUNT(*) as order_count,
    SUM(amount) as total_sales,
    AVG(amount) as avg_order_value,
    MIN(amount) as min_order,
    MAX(amount) as max_order
FROM sales
GROUP BY sale_date, product_category;

-- 자동 갱신이 활성화된 MV 생성
CREATE MATERIALIZED VIEW mv_hourly_metrics
AUTO REFRESH YES
AS
SELECT 
    DATE_TRUNC('hour', event_time) as hour,
    event_type,
    COUNT(*) as event_count,
    COUNT(DISTINCT user_id) as unique_users
FROM events
GROUP BY DATE_TRUNC('hour', event_time), event_type;
```

```bash
# Data API를 통한 MV 생성
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --db-user admin \
  --sql "CREATE MATERIALIZED VIEW mv_daily_sales AUTO REFRESH YES AS SELECT sale_date, product_category, COUNT(*) as order_count, SUM(amount) as total_sales FROM sales GROUP BY sale_date, product_category;" \
  --region ap-northeast-2
```

### 2. MV 갱신 (Refresh)

**수동 갱신**

```sql
-- 전체 갱신 (Full Refresh)
REFRESH MATERIALIZED VIEW mv_daily_sales;

-- 증분 갱신 여부는 Redshift가 자동 판단
-- 증분 가능한 경우 증분으로, 불가능한 경우 전체로 실행
```

**자동 갱신 (Auto Refresh)**

AUTO REFRESH YES로 생성된 MV는 기반 테이블에 데이터가 변경되면 Redshift가 백그라운드에서 자동으로 갱신합니다. 자동 갱신의 특성은 다음과 같습니다.

- 갱신 시점은 Redshift가 클러스터 부하를 고려하여 결정합니다.
- 실시간 갱신이 아니라 수 분~수십 분의 지연이 있을 수 있습니다.
- 자동 갱신은 유지 관리 윈도우 이외 시간에도 수행됩니다.

```bash
# MV의 자동 갱신 상태 확인
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --db-user admin \
  --sql "SELECT schema_name, mv_name, state, autorefresh, is_stale FROM stv_mv_info ORDER BY mv_name;" \
  --region ap-northeast-2
```

### 3. 증분 갱신 (Incremental Refresh)

증분 갱신은 MV의 성능을 좌우하는 핵심 기능입니다. 전체 갱신이 기반 테이블을 처음부터 다시 스캔하는 반면, 증분 갱신은 마지막 갱신 이후 변경된 데이터만 처리합니다.

**증분 갱신이 가능한 조건**

- 기반 테이블에 대한 INSERT만 발생한 경우 (UPDATE/DELETE가 없어야 함)
- MV 정의에 집계 함수가 SUM, COUNT, MIN, MAX, AVG만 사용된 경우
- OUTER JOIN, HAVING, DISTINCT, UNION이 없는 경우
- Subquery, 윈도우 함수가 없는 경우

**증분 갱신이 불가능한 경우 (전체 갱신 필요)**

- 기반 테이블에 UPDATE 또는 DELETE가 발생한 경우
- MV 정의에 OUTER JOIN, HAVING, DISTINCT 등이 포함된 경우
- Volatile 함수(GETDATE(), RANDOM() 등)가 포함된 경우

```sql
-- 증분 갱신 가능한 MV (INSERT-only 패턴)
CREATE MATERIALIZED VIEW mv_sales_incremental
AUTO REFRESH YES
AS
SELECT 
    sale_date,
    region,
    SUM(amount) as total,
    COUNT(*) as cnt
FROM sales_append_only  -- INSERT만 발생하는 테이블
GROUP BY sale_date, region;

-- 증분 갱신 불가 (DISTINCT 사용)
CREATE MATERIALIZED VIEW mv_unique_customers
AS
SELECT DISTINCT customer_id, customer_segment
FROM orders;
-- → 항상 전체 갱신 수행
```

### 4. 자동 쿼리 리다이렉션 (Automatic Query Rewriting)

Redshift 옵티마이저는 사용자가 기반 테이블을 직접 쿼리해도, 적절한 MV가 존재하면 자동으로 MV를 사용하여 쿼리를 처리합니다.

```sql
-- 사용자가 실행하는 쿼리
SELECT sale_date, SUM(amount) 
FROM sales 
WHERE sale_date >= '2024-01-01' 
GROUP BY sale_date;

-- Redshift 옵티마이저가 자동으로 다음과 같이 리다이렉션
-- → SELECT sale_date, total_sales FROM mv_daily_sales 
--   WHERE sale_date >= '2024-01-01';
```

자동 리다이렉션이 동작하려면 다음 조건을 만족해야 합니다.

- MV가 stale(만료) 상태가 아니어야 합니다.
- 쿼리의 집계/그룹핑 패턴이 MV와 호환 가능해야 합니다.
- 사용자가 MV에 대한 SELECT 권한을 가지고 있어야 합니다.

---

## 아키텍처/동작 원리

### MV 내부 동작 구조

```
[기반 테이블 변경 감지]
    |
    v
[변경 로그 (System Log) 확인]
    |- INSERT만 발생? → 증분 갱신 가능 여부 판단
    |- UPDATE/DELETE 발생? → 전체 갱신 필요
    |
    v
[갱신 방식 결정]
    |
    +-- [증분 갱신]
    |     |- 변경된 행만 스캔
    |     |- 기존 MV 결과에 증분 병합
    |     |- 빠른 갱신 (변경량에 비례)
    |
    +-- [전체 갱신]
          |- 기반 테이블 전체 스캔
          |- MV 결과 재계산
          |- 느린 갱신 (전체 데이터에 비례)
    |
    v
[MV 물리적 저장소 업데이트]
    |
    v
[MV 상태: FRESH]
```

### Stale 상태 관리

MV는 기반 테이블이 변경되면 "stale(만료)" 상태가 됩니다.

- **FRESH**: MV가 기반 테이블과 동기화된 상태입니다.
- **STALE**: 기반 테이블이 변경되어 MV가 최신이 아닌 상태입니다.
- **RECOMPUTE**: 증분 갱신이 불가능하여 전체 재계산이 필요한 상태입니다.

```sql
-- MV 상태 확인
SELECT 
    schema_name,
    mv_name,
    state,         -- FRESH, STALE, RECOMPUTE
    autorefresh,   -- 자동 갱신 여부
    is_stale,      -- stale 여부
    rows_inserted, -- 마지막 갱신 이후 삽입된 행 수
    rows_deleted,  -- 마지막 갱신 이후 삭제된 행 수
    rows_updated   -- 마지막 갱신 이후 업데이트된 행 수
FROM stv_mv_info;
```

---

## 실전 활용

### 1. BI 대시보드 성능 최적화

대시보드에서 자주 사용되는 집계 쿼리를 MV로 사전 계산합니다.

```sql
-- 일별/카테고리별 매출 대시보드 MV
CREATE MATERIALIZED VIEW mv_dashboard_daily
AUTO REFRESH YES
AS
SELECT 
    sale_date,
    product_category,
    region,
    COUNT(*) as order_count,
    COUNT(DISTINCT customer_id) as unique_customers,
    SUM(amount) as total_revenue,
    SUM(quantity) as total_quantity,
    AVG(amount) as avg_order_value
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY sale_date, product_category, region;

-- 대시보드 쿼리: 밀리초 수준 응답
SELECT 
    region,
    SUM(total_revenue) as revenue,
    SUM(unique_customers) as customers
FROM mv_dashboard_daily
WHERE sale_date BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY region
ORDER BY revenue DESC;
```

### 2. 계층적 MV 구성

세분화된 MV를 기반으로 상위 집계 MV를 구성하는 계층적 패턴입니다.

```sql
-- Level 1: 시간별 세부 집계
CREATE MATERIALIZED VIEW mv_hourly_detail
AUTO REFRESH YES
AS
SELECT 
    DATE_TRUNC('hour', event_time) as hour,
    event_type,
    source_platform,
    COUNT(*) as event_count,
    COUNT(DISTINCT session_id) as session_count
FROM events
GROUP BY DATE_TRUNC('hour', event_time), event_type, source_platform;

-- Level 2: 일별 요약 (Level 1 MV 기반)
CREATE MATERIALIZED VIEW mv_daily_summary
AUTO REFRESH YES
AS
SELECT 
    DATE_TRUNC('day', hour) as day,
    event_type,
    SUM(event_count) as total_events,
    SUM(session_count) as total_sessions
FROM mv_hourly_detail
GROUP BY DATE_TRUNC('day', hour), event_type;
```

### 3. Spectrum 외부 테이블에 대한 MV

S3 데이터(Spectrum)에 대한 쿼리도 MV로 캐시할 수 있습니다.

```sql
-- S3 데이터에 대한 MV (Spectrum 스캔 비용 절감)
CREATE MATERIALIZED VIEW mv_s3_monthly_agg
AS
SELECT 
    DATE_TRUNC('month', event_date) as month,
    event_type,
    COUNT(*) as event_count,
    SUM(revenue) as total_revenue
FROM spectrum_schema.web_events
GROUP BY DATE_TRUNC('month', event_date), event_type;
```

### 4. MV 관리 자동화

```bash
# 전체 MV 목록 및 상태 조회
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --db-user admin \
  --sql "SELECT mv_name, state, autorefresh, is_stale FROM stv_mv_info ORDER BY is_stale DESC, mv_name;" \
  --region ap-northeast-2

# stale 상태인 MV 수동 갱신
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --db-user admin \
  --sql "REFRESH MATERIALIZED VIEW mv_daily_sales;" \
  --region ap-northeast-2
```

---

## 모범 사례/보안

### MV 설계 모범 사례

1. **INSERT-only 패턴 설계**: 기반 테이블에 UPDATE/DELETE를 최소화하여 증분 갱신을 활용합니다. 가능하면 Append-only 테이블 구조를 설계합니다.
2. **적절한 집계 수준**: 너무 세분화된 MV는 효과가 적고, 너무 광범위한 MV는 유연성이 떨어집니다. 대시보드의 주요 쿼리 패턴에 맞춰 설계합니다.
3. **자동 갱신 활용**: AUTO REFRESH YES를 설정하여 수동 관리 부담을 줄입니다.
4. **갱신 모니터링**: stv_mv_info를 정기적으로 확인하여 갱신 상태를 모니터링합니다.
5. **불필요한 MV 정리**: 사용되지 않는 MV는 스토리지와 갱신 리소스를 낭비하므로 제거합니다.

### 권한 관리

```sql
-- MV에 대한 SELECT 권한 부여
GRANT SELECT ON mv_daily_sales TO GROUP analysts;

-- 특정 사용자에게 MV REFRESH 권한 부여
GRANT ALL ON mv_daily_sales TO etl_user;
```

### 성능 영향 고려

- MV 갱신은 클러스터 리소스를 소비합니다. 자동 갱신의 경우 Redshift가 부하를 고려하여 시점을 조절하지만, 수동 갱신은 즉시 실행되므로 피크 시간대를 피하는 것이 좋습니다.
- MV는 물리적 스토리지를 차지합니다. 대형 MV가 많으면 스토리지 비용이 증가합니다.

---

## 관련 서비스 비교

| 항목 | Materialized View | 일반 View | CTAS (CREATE TABLE AS) |
|------|-------------------|-----------|------------------------|
| 데이터 저장 | 물리적 저장 | 저장 안 함 (정의만) | 물리적 저장 |
| 조회 성능 | 매우 빠름 (사전 계산) | 매번 재계산 | 매우 빠름 (테이블) |
| 자동 갱신 | 지원 (AUTO REFRESH) | 해당 없음 | 미지원 (수동 재생성) |
| 증분 갱신 | 지원 (조건 충족 시) | 해당 없음 | 미지원 |
| 쿼리 리다이렉션 | 자동 지원 | 해당 없음 | 미지원 |
| 스토리지 비용 | 발생 | 없음 | 발생 |
| 데이터 신선도 | 갱신 주기에 따라 | 항상 최신 | 생성 시점 고정 |
| 적합 시나리오 | 반복 집계, 대시보드 | 복잡한 쿼리 단순화 | 일회성 스냅샷 |

---

## 요약

Amazon Redshift Materialized View는 대규모 분석 쿼리의 성능을 획기적으로 개선하는 핵심 기능입니다.

1. **사전 계산된 결과**: 복잡한 집계 쿼리의 결과를 물리적으로 저장하여 밀리초 수준의 응답 시간을 제공합니다.
2. **자동 갱신(AUTO REFRESH)**: 기반 테이블 변경 시 자동으로 MV를 업데이트하여 관리 부담을 줄입니다.
3. **증분 갱신**: INSERT-only 패턴에서 변경된 데이터만 처리하여 갱신 효율을 극대화합니다.
4. **자동 쿼리 리다이렉션**: 기반 테이블 쿼리를 자동으로 MV로 리다이렉션하여 투명한 성능 개선을 제공합니다.
5. **Spectrum MV**: S3 데이터에 대한 MV로 반복적인 Spectrum 스캔 비용을 절감합니다.
6. **INSERT-only 설계가 핵심**: 증분 갱신의 이점을 최대화하려면 기반 테이블을 Append-only 패턴으로 설계하는 것이 중요합니다.

MV는 대시보드 성능 최적화, 반복 집계 쿼리 가속, Spectrum 비용 절감 등 다양한 시나리오에서 Redshift 운영의 핵심 도구로 활용됩니다.