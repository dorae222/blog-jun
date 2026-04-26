<!-- infographic-hero -->
![Amazon Redshift Spectrum 핵심 요약](figures/infographic.svg)

*Figure: Amazon Redshift Spectrum 한 장 요약 인포그래픽*

## 개요

Amazon Redshift Spectrum은 Amazon Redshift의 확장 기능으로, Amazon S3에 저장된 데이터를 Redshift 클러스터로 로드하지 않고도 SQL 쿼리를 실행할 수 있게 해줍니다. 이를 통해 엑사바이트 규모의 비정형 및 반정형 데이터를 기존 Redshift 데이터와 조인하여 분석할 수 있습니다.

전통적인 데이터 웨어하우스 환경에서는 분석 대상 데이터를 반드시 클러스터로 적재해야 했습니다. 그러나 데이터 규모가 페타바이트 이상으로 증가하면 스토리지 비용과 적재 시간이 큰 부담이 됩니다. Redshift Spectrum은 이러한 문제를 해결하기 위해 S3를 외부 스토리지 레이어로 활용하는 아키텍처를 제공합니다.

Redshift Spectrum은 별도의 인프라 프로비저닝 없이 사용할 수 있으며, 쿼리 시 스캔한 데이터 양에 따라 과금됩니다. S3에 저장된 CSV, Parquet, ORC, JSON, Avro 등 다양한 파일 포맷을 지원하며, AWS Glue Data Catalog 또는 Apache Hive 메타스토어를 통해 외부 테이블의 스키마를 관리합니다.

## 핵심 기능

### 외부 스키마 및 외부 테이블

Redshift Spectrum을 사용하려면 먼저 외부 스키마(External Schema)를 생성해야 합니다. 외부 스키마는 AWS Glue Data Catalog 또는 Hive 메타스토어의 데이터베이스와 매핑됩니다.

```sql
CREATE EXTERNAL SCHEMA spectrum_schema
FROM DATA CATALOG
DATABASE 'my_spectrum_db'
IAM_ROLE 'arn:aws:iam::123456789012:role/MySpectrumRole'
CREATE EXTERNAL DATABASE IF NOT EXISTS;
```

외부 테이블은 S3에 저장된 데이터의 구조를 정의합니다. 실제 데이터는 S3에 그대로 남아 있으며, 메타데이터만 카탈로그에 저장됩니다.

```sql
CREATE EXTERNAL TABLE spectrum_schema.sales (
    sale_id BIGINT,
    product_id INT,
    customer_id INT,
    sale_date DATE,
    amount DECIMAL(10,2),
    region VARCHAR(50)
)
STORED AS PARQUET
LOCATION 's3://my-data-lake/sales/';
```

### 지원 데이터 포맷

Redshift Spectrum은 다음 파일 포맷을 지원합니다.

| 포맷 | 압축 지원 | 컬럼 프루닝 | 비고 |
|------|-----------|-------------|------|
| Parquet | Snappy, GZIP | 지원 | 권장 포맷 |
| ORC | Snappy, ZLIB | 지원 | Hive 에코시스템 호환 |
| CSV/TSV | GZIP, BZIP2 | 미지원 | 단순 데이터 적합 |
| JSON | GZIP | 미지원 | 반정형 데이터 |
| Avro | Snappy | 지원 | 스키마 내장 |
| Ion | 없음 | 미지원 | AWS 네이티브 포맷 |

### 파티셔닝

파티셔닝은 Spectrum 성능 최적화의 핵심입니다. S3 경로 구조를 기반으로 파티션을 정의하면 쿼리 시 필요한 파티션만 스캔하여 비용과 시간을 절감할 수 있습니다.

```sql
CREATE EXTERNAL TABLE spectrum_schema.sales_partitioned (
    sale_id BIGINT,
    product_id INT,
    customer_id INT,
    amount DECIMAL(10,2)
)
PARTITIONED BY (sale_year INT, sale_month INT, region VARCHAR(50))
STORED AS PARQUET
LOCATION 's3://my-data-lake/sales_partitioned/';
```

파티션을 추가하는 방법은 두 가지입니다.

```sql
-- 방법 1: ALTER TABLE로 수동 추가
ALTER TABLE spectrum_schema.sales_partitioned
ADD PARTITION (sale_year=2024, sale_month=1, region='ap-northeast-2')
LOCATION 's3://my-data-lake/sales_partitioned/sale_year=2024/sale_month=1/region=ap-northeast-2/';

-- 방법 2: MSCK REPAIR TABLE로 자동 탐지 (Glue Crawler 활용 권장)
```

AWS CLI를 사용하여 Glue Crawler를 실행해 파티션을 자동으로 탐지할 수 있습니다.

```bash
# Glue Crawler 생성
aws glue create-crawler \
    --name sales-crawler \
    --role arn:aws:iam::123456789012:role/GlueCrawlerRole \
    --database-name my_spectrum_db \
    --targets '{"S3Targets": [{"Path": "s3://my-data-lake/sales_partitioned/"}]}'

# Crawler 실행
aws glue start-crawler --name sales-crawler

# Crawler 상태 확인
aws glue get-crawler --name sales-crawler --query 'Crawler.State'
```

### 쿼리 처리 아키텍처

Spectrum 쿼리가 실행되면 다음 과정을 거칩니다.

1. Redshift 리더 노드가 쿼리를 파싱하고 실행 계획을 생성합니다.
2. 외부 테이블 관련 부분은 Spectrum 레이어로 위임됩니다.
3. Spectrum 전용 컴퓨팅 노드(수천 개까지 확장 가능)가 S3 데이터를 병렬로 스캔합니다.
4. 필터링, 집계 등의 연산이 Spectrum 레이어에서 수행됩니다(Predicate Pushdown).
5. 결과가 Redshift 클러스터로 반환되어 로컬 테이블과 조인됩니다.

## 아키텍처/동작 원리

### Spectrum 처리 레이어

Redshift Spectrum은 Redshift 클러스터와 독립적인 전용 컴퓨팅 레이어를 사용합니다. 이 레이어는 AWS가 관리하는 수천 개의 노드로 구성되며, 쿼리 복잡도에 따라 자동으로 스케일링됩니다.

핵심 동작 원리는 다음과 같습니다.

1. **메타데이터 조회**: AWS Glue Data Catalog에서 테이블 스키마, 파티션 정보, 파일 위치를 조회합니다.
2. **파티션 프루닝**: WHERE 절의 파티션 키 조건에 따라 불필요한 파티션을 제외합니다.
3. **파일 스캐닝**: Spectrum 노드가 해당 S3 파일을 병렬로 읽습니다.
4. **Predicate Pushdown**: 필터 조건을 Spectrum 레이어에서 직접 적용하여 네트워크 전송량을 줄입니다.
5. **컬럼 프루닝**: Parquet/ORC 같은 컬럼형 포맷의 경우, 쿼리에 필요한 컬럼만 읽습니다.
6. **결과 반환**: 처리된 결과만 Redshift 클러스터로 전송합니다.

### 비용 모델

Spectrum의 비용은 스캔한 데이터 양에 비례합니다. 2024년 기준 US East(N. Virginia) 리전에서 스캔된 데이터 1TB당 약 5 USD가 과금됩니다. 따라서 비용 최적화를 위해 다음 전략이 중요합니다.

- **컬럼형 포맷 사용**: Parquet, ORC를 사용하면 필요한 컬럼만 스캔합니다.
- **파티셔닝 적용**: 파티션 프루닝으로 스캔 범위를 줄입니다.
- **압축 적용**: Snappy, GZIP 등으로 파일을 압축하면 스캔량이 감소합니다.
- **적절한 파일 크기**: 128MB~512MB 범위의 파일 크기가 최적입니다.

## 실전 활용

### 데이터 레이크와 데이터 웨어하우스 통합 쿼리

가장 일반적인 활용 패턴은 S3 데이터 레이크의 히스토리 데이터와 Redshift 클러스터의 최신 데이터를 조인하는 것입니다.

```sql
-- Redshift 로컬 테이블: 최근 30일 주문
-- Spectrum 외부 테이블: 과거 전체 주문
SELECT
    c.customer_name,
    c.segment,
    SUM(o.amount) AS total_amount,
    COUNT(*) AS order_count
FROM spectrum_schema.orders_history o
JOIN public.customers c ON o.customer_id = c.customer_id
WHERE o.order_year = 2024
    AND o.order_month BETWEEN 1 AND 6
GROUP BY c.customer_name, c.segment
ORDER BY total_amount DESC
LIMIT 100;
```

### ETL 파이프라인에서의 활용

Spectrum을 활용하면 S3에 적재된 원본 데이터를 별도의 ETL 도구 없이 SQL로 변환하여 Redshift 테이블에 삽입할 수 있습니다.

```sql
-- S3 원본 데이터를 변환하여 Redshift 테이블에 적재
INSERT INTO public.daily_summary
SELECT
    sale_date,
    region,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_revenue,
    AVG(amount) AS avg_order_value
FROM spectrum_schema.raw_transactions
WHERE sale_date = CURRENT_DATE - INTERVAL '1 day'
GROUP BY sale_date, region;
```

### AWS CLI를 활용한 운영 관리

```bash
# Redshift 클러스터의 Spectrum 관련 IAM 역할 확인
aws redshift describe-clusters \
    --cluster-identifier my-cluster \
    --query 'Clusters[0].IamRoles[*].IamRoleArn'

# Spectrum용 IAM 역할 추가
aws redshift modify-cluster-iam-roles \
    --cluster-identifier my-cluster \
    --add-iam-roles arn:aws:iam::123456789012:role/MySpectrumRole

# S3 데이터 레이크 파티션 구조 확인
aws s3 ls s3://my-data-lake/sales_partitioned/ --recursive | head -20

# Glue Data Catalog 테이블 목록 조회
aws glue get-tables \
    --database-name my_spectrum_db \
    --query 'TableList[*].Name'

# 특정 테이블의 파티션 목록 조회
aws glue get-partitions \
    --database-name my_spectrum_db \
    --table-name sales_partitioned \
    --query 'Partitions[*].Values'
```

### 성능 모니터링

Spectrum 쿼리 성능을 모니터링하기 위해 시스템 뷰를 활용할 수 있습니다.

```sql
-- Spectrum 쿼리 실행 통계 확인
SELECT
    query,
    segment,
    elapsed,
    s3_scanned_rows,
    s3_scanned_bytes,
    s3query_returned_rows,
    s3query_returned_bytes,
    files
FROM SVL_S3QUERY_SUMMARY
ORDER BY query DESC
LIMIT 10;

-- Spectrum 스캔 대비 반환 비율 확인 (낮을수록 효율적)
SELECT
    query,
    ROUND(s3query_returned_bytes::FLOAT / NULLIF(s3_scanned_bytes, 0) * 100, 2) AS return_ratio_pct
FROM SVL_S3QUERY_SUMMARY
WHERE s3_scanned_bytes > 0
ORDER BY query DESC
LIMIT 10;
```

## 모범 사례/보안

### 성능 최적화 모범 사례

1. **Parquet 포맷 + Snappy 압축 조합을 사용합니다.** 컬럼 프루닝과 Predicate Pushdown을 모두 활용할 수 있어 스캔 데이터량을 크게 줄입니다.

2. **파티셔닝 전략을 수립합니다.** 날짜 기반 파티셔닝이 가장 일반적이며, 쿼리 패턴에 맞게 파티션 키를 선정합니다. 과도한 파티셔닝(수백만 개의 파티션)은 메타데이터 조회 오버헤드를 증가시킵니다.

3. **파일 크기를 최적화합니다.** 너무 작은 파일(1MB 이하)이 많으면 파일 오픈 오버헤드가 커집니다. 128MB에서 512MB 사이의 파일 크기가 권장됩니다.

4. **자주 사용하는 데이터는 Redshift 로컬 테이블에 적재합니다.** Spectrum은 콜드 데이터 조회에 적합하며, 핫 데이터는 로컬 테이블이 더 빠릅니다.

### 보안 모범 사례

1. **최소 권한 IAM 역할을 사용합니다.** Spectrum에 부여하는 IAM 역할은 필요한 S3 버킷과 Glue Catalog에만 접근할 수 있도록 제한합니다.

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-data-lake",
                "arn:aws:s3:::my-data-lake/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "glue:GetTable",
                "glue:GetTables",
                "glue:GetDatabase",
                "glue:GetDatabases",
                "glue:GetPartition",
                "glue:GetPartitions",
                "glue:BatchGetPartition"
            ],
            "Resource": "*"
        }
    ]
}
```

2. **S3 서버 측 암호화를 활성화합니다.** SSE-S3, SSE-KMS 모두 Spectrum이 투명하게 복호화할 수 있습니다.

3. **VPC 엔드포인트를 통해 S3에 접근합니다.** 데이터가 퍼블릭 인터넷을 경유하지 않도록 S3용 VPC 엔드포인트를 구성합니다.

4. **Lake Formation 통합으로 세분화된 접근 제어를 적용합니다.** 테이블 및 컬럼 수준의 권한 관리가 필요한 경우 AWS Lake Formation을 활용합니다.

## 관련 서비스 비교

### Redshift Spectrum vs Amazon Athena

| 항목 | Redshift Spectrum | Amazon Athena |
|------|-------------------|---------------|
| 실행 환경 | Redshift 클러스터 필요 | 서버리스 (클러스터 불필요) |
| 로컬 테이블 조인 | 지원 | 미지원 |
| 과금 방식 | 스캔 데이터량 | 스캔 데이터량 |
| 동시성 | 클러스터 WLM 관리 | 계정당 동시 쿼리 제한 |
| 성능 | 복잡한 조인에 유리 | 단순 스캔에 유리 |
| 사용 사례 | DW 확장 | 임시 분석 |

핵심 차이점은 Spectrum이 Redshift 클러스터 내부의 로컬 테이블과 조인할 수 있다는 것입니다. 기존 Redshift 환경이 있고 S3 데이터를 함께 분석해야 한다면 Spectrum이 적합하며, 클러스터 없이 S3 데이터만 분석한다면 Athena가 적합합니다.

### Redshift Spectrum vs Redshift COPY

| 항목 | Spectrum | COPY |
|------|----------|------|
| 데이터 위치 | S3 (외부) | Redshift (내부) |
| 적재 과정 | 불필요 | 필요 |
| 쿼리 성능 | 상대적 느림 | 빠름 |
| 스토리지 비용 | S3 비용만 | Redshift 노드 비용 |
| 적합 시나리오 | 대규모 히스토리 데이터 | 자주 조회하는 핫 데이터 |

## 요약

Amazon Redshift Spectrum은 S3 데이터 레이크와 Redshift 데이터 웨어하우스를 연결하는 핵심 기능입니다. 엑사바이트 규모의 S3 데이터를 로드 없이 SQL로 쿼리할 수 있으며, Redshift 로컬 테이블과 조인하여 통합 분석이 가능합니다.

효과적인 활용을 위해서는 Parquet/ORC 같은 컬럼형 포맷 사용, 적절한 파티셔닝 전략, 파일 크기 최적화가 필수적입니다. 보안 측면에서는 최소 권한 IAM 역할, S3 암호화, VPC 엔드포인트, Lake Formation 통합을 고려해야 합니다.

Spectrum은 콜드 데이터의 비용 효율적 분석에 탁월하며, 핫 데이터는 Redshift 로컬 테이블, 임시 분석은 Athena와 함께 사용하는 것이 최적의 아키텍처입니다.