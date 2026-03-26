## 개요

Amazon Redshift Federated Query는 Redshift 클러스터에서 외부 데이터베이스(RDS, Aurora 등)의 데이터를 직접 쿼리할 수 있는 기능입니다. 데이터를 Redshift로 ETL(추출-변환-적재)하지 않고도, 라이브 운영 데이터베이스의 최신 데이터를 실시간으로 분석 쿼리에 포함시킬 수 있습니다.

전통적으로 운영 데이터베이스(OLTP)의 데이터를 분석하려면 다음과 같은 과정이 필요했습니다.

1. 운영 DB에서 데이터를 추출(Extract)
2. 변환(Transform) 수행
3. 데이터 웨어하우스에 적재(Load)
4. 적재된 데이터로 분석 쿼리 실행

이 ETL 과정은 시간이 걸리며, ETL 주기(보통 1시간~1일) 동안의 데이터 지연이 발생합니다. Federated Query를 사용하면 이 지연을 제거하고, 운영 DB의 실시간 데이터를 Redshift 내부 테이블과 JOIN하여 분석할 수 있습니다.

---

## 핵심 기능

### 1. 지원 데이터 소스

Redshift Federated Query가 지원하는 외부 데이터 소스는 다음과 같습니다.

| 데이터 소스 | 프로토콜 | 지원 버전 |
|------------|---------|----------|
| Amazon RDS for PostgreSQL | PostgreSQL wire protocol | 9.6+ |
| Amazon Aurora PostgreSQL | PostgreSQL wire protocol | 9.6+ |
| Amazon RDS for MySQL | MySQL wire protocol | 5.7, 8.0 |
| Amazon Aurora MySQL | MySQL wire protocol | 5.7, 8.0+ |

추가로 Redshift Spectrum을 통해 S3(Data Lake)의 데이터도 함께 쿼리할 수 있으므로, 사실상 OLTP(RDS/Aurora) + Data Warehouse(Redshift) + Data Lake(S3)를 하나의 SQL로 통합 분석하는 것이 가능합니다.

### 2. 외부 스키마 설정

Federated Query를 사용하려면 먼저 외부 스키마(External Schema)를 생성해야 합니다.

```sql
-- PostgreSQL 기반 외부 스키마 생성
CREATE EXTERNAL SCHEMA rds_postgres
FROM POSTGRES
DATABASE 'mydb'
SCHEMA 'public'
URI 'my-rds-instance.abcdefg12345.ap-northeast-2.rds.amazonaws.com'
PORT 5432
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftFederatedRole'
SECRET_ARN 'arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:rds-creds';

-- MySQL 기반 외부 스키마 생성
CREATE EXTERNAL SCHEMA rds_mysql
FROM MYSQL
DATABASE 'mydb'
URI 'my-mysql-rds.abcdefg12345.ap-northeast-2.rds.amazonaws.com'
PORT 3306
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftFederatedRole'
SECRET_ARN 'arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:mysql-creds';
```

```bash
# 외부 스키마 생성을 Data API로 실행
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --db-user admin \
  --sql "CREATE EXTERNAL SCHEMA rds_postgres FROM POSTGRES DATABASE 'mydb' SCHEMA 'public' URI 'my-rds-instance.abcdefg12345.ap-northeast-2.rds.amazonaws.com' PORT 5432 IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftFederatedRole' SECRET_ARN 'arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:rds-creds';" \
  --region ap-northeast-2
```

### 3. 통합 쿼리 실행

외부 스키마가 설정되면, Redshift 내부 테이블과 외부 테이블을 하나의 SQL에서 자유롭게 JOIN할 수 있습니다.

```sql
-- Redshift 내부 테이블(과거 판매 데이터)과
-- RDS의 실시간 주문 데이터를 결합한 분석
SELECT 
    c.customer_name,
    c.customer_segment,
    hist.total_past_sales,
    live.pending_orders,
    live.pending_amount
FROM (
    -- Redshift 내부: 과거 판매 집계
    SELECT 
        customer_id,
        SUM(amount) as total_past_sales
    FROM sales_history
    WHERE sale_date < CURRENT_DATE
    GROUP BY customer_id
) hist
JOIN (
    -- RDS (Federated): 실시간 미처리 주문
    SELECT 
        customer_id,
        COUNT(*) as pending_orders,
        SUM(amount) as pending_amount
    FROM rds_postgres.orders
    WHERE status = 'PENDING'
    GROUP BY customer_id
) live ON hist.customer_id = live.customer_id
JOIN customers c ON hist.customer_id = c.customer_id
ORDER BY live.pending_amount DESC
LIMIT 50;
```

### 4. 3-Way Join: OLTP + DW + Data Lake

```sql
-- RDS(실시간) + Redshift(DW) + S3(Data Lake) 3-Way 분석
SELECT 
    p.product_category,
    SUM(rds_orders.amount) as live_sales,
    SUM(dw_sales.amount) as historical_sales,
    SUM(s3_logs.page_views) as total_page_views
FROM rds_postgres.orders rds_orders
JOIN sales_history dw_sales 
    ON rds_orders.product_id = dw_sales.product_id
JOIN spectrum_schema.web_analytics s3_logs 
    ON rds_orders.product_id = s3_logs.product_id
JOIN products p 
    ON rds_orders.product_id = p.product_id
WHERE rds_orders.order_date >= '2024-01-01'
GROUP BY p.product_category
ORDER BY live_sales DESC;
```

---

## 아키텍처/동작 원리

### Federated Query 실행 흐름

```
[Client]
    |
    v
[Redshift Leader Node]
    |- SQL 파싱
    |- 외부 테이블 참조 감지
    |- 쿼리 분해: 외부 쿼리 + 내부 쿼리
    |
    +--- 내부 쿼리 ---> [Compute Nodes] ---> 내부 데이터 스캔
    |
    +--- 외부 쿼리 ---> [Compute Nodes] ---> [RDS/Aurora]
                                                |
                                          (Secrets Manager에서
                                           자격 증명 조회)
                                                |
                                          외부 데이터 가져오기
    |
    v
[Leader Node: 결과 결합]
    |- 내부 데이터 + 외부 데이터 JOIN
    |- 최종 결과 반환
```

### Predicate Pushdown

Federated Query의 핵심 최적화 기법은 Predicate Pushdown(조건 푸시다운)입니다. Redshift는 외부 데이터베이스에서 가져올 데이터를 최소화하기 위해, WHERE 조건을 외부 쿼리에 포함시킵니다.

```sql
-- 원본 쿼리
SELECT * FROM rds_postgres.orders WHERE status = 'PENDING' AND amount > 1000;

-- Redshift가 RDS에 실제로 보내는 쿼리 (Predicate Pushdown)
-- SELECT * FROM orders WHERE status = 'PENDING' AND amount > 1000
-- → RDS에서 필터링된 결과만 Redshift로 전송
```

그러나 모든 조건이 푸시다운되는 것은 아닙니다. Redshift 전용 함수나 복잡한 표현식은 푸시다운되지 않으므로, 외부 테이블 필터링에는 단순한 비교 연산자를 사용하는 것이 좋습니다.

### 네트워크 요구사항

- Redshift 클러스터와 RDS/Aurora 인스턴스가 동일 VPC에 있거나, VPC Peering으로 연결되어 있어야 합니다.
- Enhanced VPC Routing이 활성화된 경우, 모든 트래픽이 VPC 내부로 라우팅됩니다.
- 보안 그룹에서 Redshift → RDS 방향의 데이터베이스 포트(5432/3306)를 허용해야 합니다.

```bash
# Redshift 클러스터에서 RDS로의 보안 그룹 설정
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds-security-group \
  --protocol tcp \
  --port 5432 \
  --source-group sg-redshift-security-group \
  --region ap-northeast-2
```

---

## 실전 활용

### 1. 실시간 대시보드 데이터 보강

가장 일반적인 활용 사례는 DW의 과거 데이터에 운영 DB의 실시간 데이터를 보강하는 것입니다.

```sql
-- 대시보드용: 고객별 실시간 + 과거 종합 분석
CREATE VIEW v_customer_360 AS
SELECT 
    c.customer_id,
    c.customer_name,
    c.segment,
    COALESCE(hist.total_orders, 0) as historical_orders,
    COALESCE(hist.total_revenue, 0) as historical_revenue,
    COALESCE(live.active_orders, 0) as active_orders,
    COALESCE(live.active_revenue, 0) as active_revenue,
    COALESCE(hist.total_revenue, 0) + COALESCE(live.active_revenue, 0) as lifetime_value
FROM customers c
LEFT JOIN (
    SELECT customer_id, COUNT(*) as total_orders, SUM(amount) as total_revenue
    FROM sales_history
    GROUP BY customer_id
) hist ON c.customer_id = hist.customer_id
LEFT JOIN (
    SELECT customer_id, COUNT(*) as active_orders, SUM(amount) as active_revenue
    FROM rds_postgres.orders
    WHERE status IN ('PENDING', 'PROCESSING')
    GROUP BY customer_id
) live ON c.customer_id = live.customer_id;
```

### 2. ETL 없는 데이터 검증

ETL 파이프라인의 데이터 품질을 검증할 때, 소스(RDS)와 타겟(Redshift)의 데이터를 직접 비교할 수 있습니다.

```sql
-- 소스(RDS)와 타겟(Redshift)의 행 수 비교
SELECT 
    'RDS' as source, COUNT(*) as row_count 
FROM rds_postgres.orders 
WHERE order_date = CURRENT_DATE - 1
UNION ALL
SELECT 
    'Redshift' as source, COUNT(*) as row_count 
FROM orders_fact 
WHERE order_date = CURRENT_DATE - 1;
```

### 3. Federated Query 성능 모니터링

```bash
# Federated Query 실행 통계 확인
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database analytics \
  --db-user admin \
  --sql "SELECT query, external_scanned, s3_scanned, elapsed, source_type FROM svl_federated_query ORDER BY elapsed DESC LIMIT 20;" \
  --region ap-northeast-2
```

---

## 모범 사례/보안

### 성능 최적화

1. **필터 조건 최적화**: 외부 테이블에 대한 WHERE 조건을 최대한 구체적으로 작성하여 Predicate Pushdown을 극대화합니다.
2. **데이터 전송량 최소화**: SELECT *를 피하고 필요한 컬럼만 선택합니다.
3. **집계 로직 분리**: 외부 데이터에 대한 집계는 서브쿼리에서 수행하여 전송 데이터를 줄입니다.
4. **결과 캐싱**: 동일한 외부 데이터를 반복 조회하는 경우, Redshift의 결과 캐시를 활용합니다.
5. **운영 DB 부하 고려**: Federated Query는 운영 DB에 읽기 부하를 발생시킵니다. Read Replica에 연결하는 것을 권장합니다.

### 보안

- **Secrets Manager**: 외부 DB 자격 증명은 반드시 Secrets Manager를 통해 관리합니다.
- **최소 권한 IAM**: Federated Role에는 필요한 최소한의 권한만 부여합니다.
- **네트워크 격리**: Enhanced VPC Routing을 활성화하여 데이터가 퍼블릭 인터넷을 거치지 않도록 합니다.
- **외부 DB Read-Only**: 외부 스키마의 DB 사용자에게는 읽기 전용 권한만 부여합니다.

---

## 관련 서비스 비교

### Redshift Federated Query vs Athena Federated Query

| 항목 | Redshift Federated Query | Athena Federated Query |
|------|-------------------------|------------------------|
| 실행 엔진 | Redshift MPP 클러스터 | Athena (Presto/Trino) |
| 데이터 소스 | RDS/Aurora (PostgreSQL, MySQL) | DynamoDB, RDS, CloudWatch, S3, 커스텀 |
| 확장 가능 커넥터 | 고정 (AWS 지원 소스만) | Lambda 기반 무제한 커스텀 |
| 설정 복잡도 | 외부 스키마 생성 (간단) | Lambda 커넥터 배포 필요 |
| 성능 (대규모) | MPP 병렬 처리로 우수 | 커넥터 Lambda 성능에 종속 |
| 비용 | 클러스터 비용에 포함 | 스캔 데이터량 + Lambda 비용 |
| 내부 테이블 JOIN | Redshift 테이블과 고성능 JOIN | S3 데이터와 JOIN |
| 적합 시나리오 | DW 분석에 실시간 OLTP 데이터 보강 | 다양한 데이터 소스 Ad-hoc 쿼리 |

**선택 기준**

- **Redshift Federated Query를 선택하는 경우**: Redshift DW가 이미 구축되어 있고, RDS/Aurora의 실시간 데이터를 DW 분석에 포함시키고 싶은 경우. 내부 테이블과의 대규모 JOIN이 빈번한 경우.
- **Athena Federated Query를 선택하는 경우**: 다양한 데이터 소스(DynamoDB, CloudWatch Logs, SaaS 등)를 Ad-hoc으로 쿼리하고 싶은 경우. 서버리스 환경을 선호하는 경우. 커스텀 커넥터가 필요한 경우.

| 항목 | Redshift Federated | Redshift Spectrum | AWS Glue ETL |
|------|-------------------|-------------------|---------------|
| 데이터 이동 | 불필요 (실시간 쿼리) | 불필요 (S3 직접 쿼리) | 필요 (ETL) |
| 데이터 신선도 | 실시간 | S3 적재 시점 | ETL 주기 의존 |
| 지원 소스 | RDS/Aurora | S3 | 거의 모든 소스 |
| 성능 (대규모) | 외부 DB 부하 고려 필요 | S3 스캔 병렬화 | ETL 후 최적 성능 |
| 비용 | 클러스터 비용 | 스캔 데이터량 | Glue DPU + 스토리지 |

---

## 요약

Amazon Redshift Federated Query는 데이터 웨어하우스와 운영 데이터베이스 사이의 경계를 허무는 강력한 기능입니다.

1. **ETL 없는 실시간 분석**: RDS/Aurora의 최신 데이터를 Redshift에서 직접 쿼리하여 데이터 지연을 제거합니다.
2. **통합 SQL**: OLTP(RDS) + DW(Redshift) + Data Lake(S3/Spectrum)를 하나의 SQL로 분석합니다.
3. **Predicate Pushdown**: 외부 데이터베이스에 필터 조건을 전달하여 네트워크 전송을 최소화합니다.
4. **Secrets Manager 연동**: 외부 DB 자격 증명을 안전하게 관리합니다.
5. **Read Replica 권장**: 운영 DB 부하를 방지하기 위해 Read Replica에 연결합니다.
6. **Athena와 상호 보완**: Redshift Federated는 DW 중심 분석에, Athena Federated는 다양한 소스의 Ad-hoc 분석에 각각 적합합니다.

Federated Query는 ETL 파이프라인을 완전히 대체하는 것이 아니라, ETL 이전의 실시간 데이터 접근과 ETL 데이터 검증에 활용하는 것이 가장 효과적인 사용 패턴입니다.