<!-- infographic-hero -->
![Amazon Redshift View 개요 핵심 요약](figures/infographic.svg)

*Figure: Amazon Redshift View 개요 한 장 요약 인포그래픽*

## 개요

Amazon Redshift의 View(뷰)는 자주 사용하는 쿼리를 저장된 가상 테이블로 정의하여 재사용성, 보안, 유지보수성을 높이는 데이터베이스 객체입니다. Redshift는 세 가지 유형의 뷰를 지원하며, 각각 서로 다른 특성과 사용 시나리오를 가지고 있습니다.

1. **일반 뷰(Regular View)**: 쿼리 정의를 저장하며, 참조 시마다 해당 쿼리가 실행됩니다.
2. **Late Binding View**: 스키마 바인딩을 실행 시점으로 지연시켜 유연성을 제공합니다.
3. **Materialized View**: 쿼리 결과를 물리적으로 저장하여 반복 쿼리의 성능을 크게 향상시킵니다.

뷰의 올바른 활용은 데이터 웨어하우스 운영에서 매우 중요합니다. 복잡한 비즈니스 로직을 뷰에 캡슐화하면 분석가들이 SQL 세부사항을 알 필요 없이 데이터에 접근할 수 있으며, 뷰 단위로 권한을 제어하여 보안을 강화할 수 있습니다.

## 핵심 기능

### 일반 뷰 (Regular View)

일반 뷰는 쿼리 정의를 저장하는 가상 테이블입니다. 뷰를 참조하면 저장된 쿼리가 실행되며, 기반 테이블의 최신 데이터가 항상 반영됩니다.

```sql
-- 일반 뷰 생성
CREATE VIEW v_monthly_sales AS
SELECT
    DATE_TRUNC('month', sale_date) AS sale_month,
    region,
    product_category,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_revenue,
    AVG(amount) AS avg_order_value,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM sales
JOIN products USING (product_id)
JOIN regions USING (region_id)
GROUP BY 1, 2, 3;

-- 뷰 사용
SELECT * FROM v_monthly_sales
WHERE sale_month >= '2024-01-01'
ORDER BY total_revenue DESC;
```

일반 뷰의 특성은 다음과 같습니다.
- 기반 테이블의 스키마가 변경되면 뷰가 무효화될 수 있습니다.
- 뷰 생성 시 기반 테이블이 반드시 존재해야 합니다.
- 참조할 때마다 쿼리가 실행되므로 성능은 기반 쿼리의 복잡도에 의존합니다.
- 중첩 뷰(뷰를 참조하는 뷰)가 가능합니다.

```sql
-- 중첩 뷰 예시
CREATE VIEW v_top_regions AS
SELECT *
FROM v_monthly_sales
WHERE total_revenue > 1000000
ORDER BY total_revenue DESC;
```

### Late Binding View

Late Binding View는 뷰 생성 시 기반 테이블의 존재 여부를 확인하지 않으며, 실행 시점에 스키마를 바인딩합니다. Redshift Spectrum의 외부 테이블을 참조할 때 특히 유용합니다.

```sql
-- Late Binding View 생성 (WITH NO SCHEMA BINDING)
CREATE VIEW v_combined_sales AS
SELECT
    'recent' AS data_source,
    sale_id,
    customer_id,
    sale_date,
    amount
FROM public.recent_sales
UNION ALL
SELECT
    'archive' AS data_source,
    sale_id,
    customer_id,
    sale_date,
    amount
FROM spectrum_schema.archived_sales
WITH NO SCHEMA BINDING;
```

Late Binding View의 핵심 특성은 다음과 같습니다.
- 생성 시 기반 테이블이 없어도 됩니다.
- 기반 테이블의 스키마가 변경되어도 뷰가 자동으로 적응합니다.
- Spectrum 외부 테이블과 로컬 테이블을 자유롭게 결합할 수 있습니다.
- 기반 테이블이 삭제되고 재생성되어도 뷰가 유효합니다.

```sql
-- Spectrum 외부 테이블을 참조하는 Late Binding View
CREATE VIEW v_data_lake_analytics AS
SELECT
    event_date,
    event_type,
    COUNT(*) AS event_count
FROM spectrum_schema.raw_events
WHERE event_date >= DATEADD(day, -30, CURRENT_DATE)
GROUP BY event_date, event_type
WITH NO SCHEMA BINDING;
```

### Materialized View

Materialized View는 쿼리 결과를 물리적으로 저장하여 반복 쿼리의 성능을 극적으로 향상시킵니다. 기반 테이블의 데이터가 변경되면 REFRESH를 통해 최신 상태로 갱신합니다.

```sql
-- Materialized View 생성
CREATE MATERIALIZED VIEW mv_daily_revenue AS
SELECT
    sale_date,
    region,
    SUM(amount) AS daily_revenue,
    COUNT(*) AS transaction_count,
    AVG(amount) AS avg_order_value
FROM sales
GROUP BY sale_date, region;

-- Materialized View 새로고침
REFRESH MATERIALIZED VIEW mv_daily_revenue;

-- 자동 새로고침 설정
CREATE MATERIALIZED VIEW mv_hourly_metrics
AUTO REFRESH YES AS
SELECT
    DATE_TRUNC('hour', event_time) AS event_hour,
    event_type,
    COUNT(*) AS event_count
FROM events
GROUP BY 1, 2;
```

Materialized View의 핵심 특성은 다음과 같습니다.
- 쿼리 결과가 물리적으로 저장되어 재실행 없이 즉시 반환됩니다.
- 증분 새로고침(Incremental Refresh)이 가능하여 전체 재계산 없이 변경분만 반영합니다.
- AUTO REFRESH 옵션으로 Redshift가 자동으로 새로고침 시점을 결정합니다.
- 분산 키, 정렬 키를 지정할 수 있어 쿼리 패턴에 맞게 최적화됩니다.

```sql
-- 분산 키와 정렬 키가 포함된 Materialized View
CREATE MATERIALIZED VIEW mv_customer_summary
DISTKEY(customer_id)
SORTKEY(last_order_date)
AS
SELECT
    customer_id,
    COUNT(*) AS total_orders,
    SUM(amount) AS lifetime_value,
    MAX(sale_date) AS last_order_date,
    MIN(sale_date) AS first_order_date
FROM sales
GROUP BY customer_id;
```

### 뷰 관리 명령어

```sql
-- 뷰 정의 확인
SELECT definition FROM pg_views WHERE viewname = 'v_monthly_sales';

-- Materialized View 상태 확인
SELECT
    mv.schema AS schema_name,
    mv.name AS mv_name,
    mv.state,
    mv.is_stale,
    mv.rows AS row_count,
    mv.autorefresh
FROM STV_MV_INFO mv;

-- 뷰 삭제
DROP VIEW v_monthly_sales;
DROP VIEW v_combined_sales;
DROP MATERIALIZED VIEW mv_daily_revenue;

-- 뷰 교체 (OR REPLACE)
CREATE OR REPLACE VIEW v_monthly_sales AS
SELECT
    DATE_TRUNC('month', sale_date) AS sale_month,
    region,
    SUM(amount) AS total_revenue
FROM sales
JOIN regions USING (region_id)
GROUP BY 1, 2;
```

## 아키텍처/동작 원리

### 일반 뷰의 동작

일반 뷰는 쿼리 파싱 단계에서 뷰 정의로 대체(expansion)됩니다. 즉 뷰를 참조하는 쿼리가 실행되면, Redshift 옵티마이저는 뷰의 정의 쿼리를 인라인하여 전체 실행 계획을 생성합니다.

이 과정에서 옵티마이저는 뷰의 필터와 외부 쿼리의 필터를 병합하여 최적화할 수 있습니다. 예를 들어 뷰 외부에서 WHERE 조건을 추가하면, 옵티마이저가 해당 조건을 기반 테이블 스캔 단계로 푸시다운할 수 있습니다.

### Late Binding View의 동작

Late Binding View는 뷰 생성 시 메타데이터 카탈로그에 쿼리 텍스트만 저장합니다. 컬럼 바인딩이 실행 시점에 이루어지므로 다음과 같은 유연성을 제공합니다.

- 기반 테이블에 컬럼이 추가/삭제되어도 뷰가 유효합니다 (뷰가 참조하는 컬럼이 여전히 존재하는 한).
- 기반 테이블을 DROP 후 재생성해도 뷰가 작동합니다.
- Spectrum 외부 테이블의 스키마 변경에 자동으로 적응합니다.

### Materialized View의 동작

1. **초기 생성**: CREATE MATERIALIZED VIEW 실행 시 쿼리가 실행되어 결과가 물리적 테이블에 저장됩니다.
2. **자동 쿼리 라우팅**: Redshift 옵티마이저는 기반 테이블을 직접 쿼리하는 경우에도 적합한 Materialized View가 있으면 자동으로 해당 MV를 사용합니다 (Auto MV Rewrite).
3. **증분 새로고침**: 기반 테이블의 변경사항을 추적하여 전체 재계산 없이 변경분만 반영합니다.
4. **Stale 상태**: 기반 데이터가 변경되면 MV는 stale(오래된) 상태가 됩니다. AUTO REFRESH가 활성화되어 있으면 Redshift가 적절한 시점에 자동으로 새로고침합니다.

## 실전 활용

### 비즈니스 인텔리전스 레이어

복잡한 비즈니스 로직을 뷰에 캡슐화하여 BI 도구에서 쉽게 접근할 수 있도록 합니다.

```sql
-- 고객 세그먼트 분석 뷰
CREATE VIEW v_customer_segments AS
SELECT
    c.customer_id,
    c.customer_name,
    c.signup_date,
    COALESCE(s.total_orders, 0) AS total_orders,
    COALESCE(s.lifetime_value, 0) AS lifetime_value,
    CASE
        WHEN s.lifetime_value >= 10000 THEN 'VIP'
        WHEN s.lifetime_value >= 5000 THEN 'Gold'
        WHEN s.lifetime_value >= 1000 THEN 'Silver'
        WHEN s.lifetime_value > 0 THEN 'Bronze'
        ELSE 'Inactive'
    END AS segment,
    DATEDIFF(day, s.last_order_date, CURRENT_DATE) AS days_since_last_order
FROM customers c
LEFT JOIN (
    SELECT
        customer_id,
        COUNT(*) AS total_orders,
        SUM(amount) AS lifetime_value,
        MAX(sale_date) AS last_order_date
    FROM sales
    GROUP BY customer_id
) s ON c.customer_id = s.customer_id;
```

### 데이터 보안 레이어

뷰를 통해 민감 정보를 마스킹하거나 행 레벨 필터링을 구현할 수 있습니다.

```sql
-- 개인정보 마스킹 뷰
CREATE VIEW v_customers_masked AS
SELECT
    customer_id,
    LEFT(customer_name, 1) || '***' AS customer_name,
    LEFT(email, 3) || '***@' || SPLIT_PART(email, '@', 2) AS email,
    segment,
    signup_date
FROM customers;

-- 분석가에게는 마스킹된 뷰만 접근 허용
GRANT SELECT ON v_customers_masked TO analyst_group;
REVOKE SELECT ON customers FROM analyst_group;
```

### Materialized View를 활용한 대시보드 최적화

```sql
-- 실시간 대시보드용 MV
CREATE MATERIALIZED VIEW mv_realtime_dashboard
AUTO REFRESH YES AS
SELECT
    DATE_TRUNC('hour', order_time) AS hour,
    COUNT(*) AS orders,
    SUM(amount) AS revenue,
    COUNT(DISTINCT customer_id) AS customers,
    AVG(amount) AS aov
FROM orders
WHERE order_time >= DATEADD(day, -7, CURRENT_DATE)
GROUP BY 1;
```

### AWS CLI를 활용한 뷰 관리

```bash
# 뷰 목록 조회
aws redshift-data execute-statement \
    --cluster-identifier my-cluster \
    --database dev \
    --db-user admin \
    --sql "SELECT schemaname, viewname, viewowner FROM pg_views WHERE schemaname = 'public' ORDER BY viewname"

# Materialized View 상태 모니터링
aws redshift-data execute-statement \
    --cluster-identifier my-cluster \
    --database dev \
    --db-user admin \
    --sql "SELECT schema, name, state, is_stale, autorefresh, rows FROM STV_MV_INFO"

# Materialized View 새로고침 실행
aws redshift-data execute-statement \
    --cluster-identifier my-cluster \
    --database dev \
    --db-user admin \
    --sql "REFRESH MATERIALIZED VIEW mv_daily_revenue"

# 쿼리 결과 조회
aws redshift-data get-statement-result --id "실행-ID"
```

## 모범 사례/보안

### 뷰 설계 모범 사례

1. **뷰 중첩을 3단계 이내로 제한합니다.** 과도한 중첩은 옵티마이저의 최적화를 어렵게 하고 디버깅을 복잡하게 만듭니다.

2. **Materialized View에 적합한 쿼리를 선별합니다.** 집계(GROUP BY), 조인이 포함된 고비용 쿼리 중 빈번히 실행되는 것을 MV 후보로 선정합니다.

3. **Late Binding View는 외부 테이블 참조 시 사용합니다.** 일반 Redshift 테이블만 참조하는 경우 일반 뷰가 적합합니다.

4. **뷰 이름에 접두사 규칙을 적용합니다.** `v_`(일반 뷰), `mv_`(Materialized View) 등의 접두사로 구분하면 관리가 용이합니다.

5. **Materialized View의 AUTO REFRESH를 적극 활용합니다.** 수동 새로고침은 운영 부담이 크므로 AUTO REFRESH YES를 기본으로 사용합니다.

### 보안 모범 사례

1. **뷰 단위로 접근 권한을 관리합니다.** 기반 테이블 접근을 제한하고 뷰를 통해서만 데이터에 접근하도록 구성합니다.

2. **민감 데이터는 마스킹 뷰를 통해 노출합니다.** PII(개인식별정보)가 포함된 테이블에는 직접 접근을 차단하고 마스킹 뷰를 제공합니다.

3. **뷰 정의에 보안 함수를 포함하지 않습니다.** 암호화 키나 비밀번호 등이 뷰 정의에 포함되지 않도록 주의합니다. 뷰 정의는 pg_views에서 조회 가능합니다.

## 관련 서비스 비교

### 세 가지 뷰 유형 비교

| 항목 | 일반 뷰 | Late Binding View | Materialized View |
|------|---------|-------------------|--------------------|
| 데이터 저장 | 없음 (정의만) | 없음 (정의만) | 물리적 저장 |
| 실행 시 동작 | 매번 쿼리 실행 | 매번 쿼리 실행 | 저장된 결과 반환 |
| 스키마 바인딩 | 생성 시 | 실행 시 | 생성 시 |
| 외부 테이블 | 미지원 | 지원 | 미지원 |
| 성능 | 기반 쿼리 의존 | 기반 쿼리 의존 | 매우 빠름 |
| 데이터 최신성 | 항상 최신 | 항상 최신 | REFRESH 의존 |
| 스토리지 비용 | 없음 | 없음 | 있음 |
| OR REPLACE | 지원 | 지원 | 미지원 |

### Redshift MV vs PostgreSQL MV

| 항목 | Redshift MV | PostgreSQL MV |
|------|------------|---------------|
| 증분 새로고침 | 지원 | 미지원 (전체 재계산) |
| 자동 새로고침 | AUTO REFRESH | 수동만 |
| 자동 쿼리 라우팅 | 지원 | 미지원 |
| 분산/정렬 키 | 지원 | 해당없음 |

## 요약

Amazon Redshift는 일반 뷰, Late Binding View, Materialized View의 세 가지 뷰 유형을 제공합니다. 각 유형은 서로 다른 특성과 적합한 사용 시나리오를 가지고 있으며, 올바른 선택이 데이터 웨어하우스의 성능과 운영 효율성에 직접적인 영향을 미칩니다.

일반 뷰는 비즈니스 로직의 캡슐화와 보안 제어에 적합하며, Late Binding View는 Spectrum 외부 테이블을 참조할 때 필수적입니다. Materialized View는 고비용 집계/조인 쿼리의 성능을 극적으로 향상시키며, AUTO REFRESH와 자동 쿼리 라우팅을 통해 운영 부담을 최소화합니다.

뷰를 활용한 데이터 접근 레이어를 구축하면 복잡한 비즈니스 로직을 재사용 가능한 형태로 관리하고, 민감 데이터를 마스킹하여 안전하게 노출하며, 대시보드와 BI 도구의 응답 시간을 크게 개선할 수 있습니다.