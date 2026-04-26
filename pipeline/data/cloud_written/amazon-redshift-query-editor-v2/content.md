<!-- infographic-hero -->
![Amazon Redshift Query Editor v2 핵심 요약](figures/infographic.svg)

*Figure: Amazon Redshift Query Editor v2 한 장 요약 인포그래픽*

## 개요

Amazon Redshift Query Editor v2는 AWS 콘솔에서 직접 Redshift 클러스터와 Redshift Serverless에 SQL 쿼리를 실행할 수 있는 웹 기반 SQL 편집기입니다. 별도의 SQL 클라이언트 도구(DBeaver, DataGrip 등)를 설치하지 않아도, 웹 브라우저만으로 Redshift의 데이터를 분석하고 시각화할 수 있습니다.

기존 Query Editor v1이 단순한 쿼리 실행 기능만 제공했던 반면, v2는 다음과 같은 기능을 대폭 확장하여 본격적인 데이터 분석 도구로 발전했습니다.

- 여러 쿼리 탭 동시 지원
- 쿼리 결과 시각화 (차트)
- SQL 노트북 (Jupyter Notebook과 유사)
- 쿼리 공유 및 팀 협업
- 스키마 브라우저 (트리 구조)
- 버전 관리 (쿼리 히스토리)
- IAM Identity Center (SSO) 통합

---

## 핵심 기능

### 1. SQL 편집기

Query Editor v2의 SQL 편집기는 다음 기능을 제공합니다.

- **구문 강조(Syntax Highlighting)**: Redshift SQL 문법에 맞춘 컬러 코딩
- **자동 완성(Auto-Complete)**: 테이블명, 컬럼명, SQL 키워드 자동 완성
- **다중 탭**: 여러 쿼리를 동시에 편집하고 실행
- **실행 계획(EXPLAIN)**: 쿼리 실행 계획을 시각적으로 확인
- **쿼리 단축키**: Ctrl+Enter(실행), Ctrl+S(저장), Ctrl+/(주석) 등
- **부분 실행**: 선택한 SQL 문만 실행

```sql
-- Query Editor v2에서 실행하는 예시 쿼리
-- 여러 문을 탭에서 순차 실행 가능

-- 쿼리 1: 일별 매출 추이
SELECT 
    sale_date,
    SUM(amount) as daily_revenue,
    COUNT(*) as order_count,
    AVG(amount) as avg_order_value
FROM sales
WHERE sale_date >= DATEADD(day, -30, CURRENT_DATE)
GROUP BY sale_date
ORDER BY sale_date;

-- 쿼리 2: 카테고리별 비중
SELECT 
    p.product_category,
    SUM(s.amount) as category_revenue,
    ROUND(SUM(s.amount) * 100.0 / SUM(SUM(s.amount)) OVER(), 2) as pct
FROM sales s
JOIN products p ON s.product_id = p.product_id
WHERE s.sale_date >= DATEADD(day, -30, CURRENT_DATE)
GROUP BY p.product_category
ORDER BY category_revenue DESC;
```

### 2. 시각화 (Charts)

Query Editor v2는 쿼리 결과를 다양한 차트로 시각화할 수 있습니다.

지원하는 차트 유형은 다음과 같습니다.

- **Line Chart**: 시계열 데이터 추이 (매출 추이, 사용자 증가 등)
- **Bar Chart**: 범주형 비교 (카테고리별 매출, 지역별 분포)
- **Pie Chart**: 구성 비율 (시장 점유율, 트래픽 소스)
- **Area Chart**: 누적 추이
- **Scatter Plot**: 상관관계 분석

차트 설정에서 X축, Y축, 색상, 집계 방식 등을 자유롭게 지정할 수 있으며, 생성된 차트는 이미지로 다운로드하거나 대시보드에 공유할 수 있습니다.

### 3. SQL 노트북

Query Editor v2의 노트북 모드는 Jupyter Notebook과 유사한 인터페이스를 제공합니다.

- **SQL 셀**: SQL 쿼리를 실행하고 결과를 확인합니다.
- **Markdown 셀**: 분석 설명, 제목, 목차 등을 작성합니다.
- **차트 셀**: SQL 결과를 바로 시각화합니다.
- **셀 순서 실행**: 셀을 순차적으로 실행하며 분석 흐름을 구성합니다.

노트북은 데이터 분석 보고서를 작성하거나, 팀원에게 분석 과정을 공유할 때 효과적입니다.

### 4. 스키마 브라우저

좌측 패널에서 데이터베이스의 전체 구조를 트리 형태로 탐색할 수 있습니다.

```
my-redshift-cluster
├── analytics (database)
│   ├── public (schema)
│   │   ├── Tables
│   │   │   ├── sales
│   │   │   │   ├── sale_id (BIGINT)
│   │   │   │   ├── product_id (INTEGER)
│   │   │   │   ├── sale_date (DATE)
│   │   │   │   └── amount (DECIMAL)
│   │   │   ├── products
│   │   │   └── customers
│   │   ├── Views
│   │   │   └── v_daily_summary
│   │   ├── Materialized Views
│   │   │   └── mv_daily_sales
│   │   └── Functions
│   │       └── predict_churn
│   └── spectrum_schema (external)
│       └── web_events (external table)
```

테이블을 클릭하면 컬럼 정보, 데이터 타입, 분산 키, 정렬 키 등의 메타데이터를 확인할 수 있습니다.

### 5. 쿼리 공유 및 협업

Query Editor v2는 팀 협업을 위한 다양한 기능을 제공합니다.

- **저장된 쿼리(Saved Queries)**: 쿼리를 이름을 붙여 저장합니다.
- **폴더 관리**: 쿼리를 폴더 단위로 정리합니다.
- **팀 공유**: 저장된 쿼리를 다른 IAM 사용자 또는 그룹과 공유합니다.
- **노트북 공유**: SQL 노트북을 팀원과 공유하여 분석 과정을 재현합니다.
- **버전 히스토리**: 쿼리 변경 이력을 추적합니다.

```bash
# Query Editor v2의 태그 기반 리소스 관리
aws redshift create-tags \
  --resource-name arn:aws:sqlworkbench:ap-northeast-2:123456789012:query/my-saved-query \
  --tags Key=Team,Value=Analytics Key=Purpose,Value=Dashboard \
  --region ap-northeast-2
```

---

## 아키텍처/동작 원리

### Query Editor v2 아키텍처

```
[Web Browser]
    |
    v
[AWS Console / Query Editor v2 UI]
    |
    v
[AWS SQL Workbench Service]
    |- 쿼리 메타데이터 저장 (저장된 쿼리, 노트북, 차트 설정)
    |- IAM 인증/인가
    |- 쿼리 히스토리 관리
    |
    v
[Redshift Data API]
    |
    v
[Redshift Cluster / Serverless]
    |- SQL 실행
    |- 결과 반환
```

Query Editor v2는 내부적으로 Redshift Data API를 사용합니다. 따라서 Data API의 특성(비동기 실행, 결과 크기 제한 등)이 동일하게 적용됩니다.

### 인증 방식

Query Editor v2는 세 가지 인증 방식을 지원합니다.

1. **IAM 임시 자격 증명**: IAM 역할을 통해 임시 DB 자격 증명을 생성합니다.
2. **Secrets Manager**: DB 자격 증명을 Secrets Manager에서 조회합니다.
3. **Federated User (IAM Identity Center)**: SSO를 통해 인증합니다. 여러 사용자가 개별 계정으로 접근할 때 편리합니다.

```bash
# Query Editor v2 접근을 위한 IAM 정책
aws iam put-user-policy \
  --user-name analyst-user \
  --policy-name RedshiftQueryEditorV2Access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "sqlworkbench:*",
          "redshift:GetClusterCredentials",
          "redshift:DescribeClusters",
          "redshift-data:*",
          "redshift-serverless:GetCredentials",
          "redshift-serverless:ListWorkgroups",
          "secretsmanager:GetSecretValue"
        ],
        "Resource": "*"
      }
    ]
  }' \
  --region ap-northeast-2
```

### 쿼리 실행 흐름

1. 사용자가 SQL을 입력하고 실행 버튼을 클릭합니다.
2. Query Editor v2가 Redshift Data API의 `execute-statement`를 호출합니다.
3. Data API가 Redshift에서 쿼리를 실행합니다.
4. 쿼리 완료 후 `get-statement-result`로 결과를 조회합니다.
5. 결과를 테이블, 차트 등으로 렌더링합니다.

---

## 실전 활용

### 1. 데이터 탐색 워크플로우

새로운 데이터셋을 탐색할 때 Query Editor v2를 활용하는 전형적인 워크플로우입니다.

```sql
-- 1. 테이블 목록 확인
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- 2. 테이블 구조 확인
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public' AND table_name = 'sales'
ORDER BY ordinal_position;

-- 3. 데이터 프로파일링
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT customer_id) as unique_customers,
    MIN(sale_date) as earliest_date,
    MAX(sale_date) as latest_date,
    AVG(amount) as avg_amount,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount) as median_amount
FROM sales;

-- 4. 데이터 품질 확인
SELECT 
    'sale_date' as column_name,
    COUNT(*) - COUNT(sale_date) as null_count,
    ROUND((COUNT(*) - COUNT(sale_date))::FLOAT / COUNT(*) * 100, 2) as null_pct
FROM sales
UNION ALL
SELECT 
    'amount',
    COUNT(*) - COUNT(amount),
    ROUND((COUNT(*) - COUNT(amount))::FLOAT / COUNT(*) * 100, 2)
FROM sales;
```

### 2. 노트북 기반 분석 보고서

SQL 노트북을 활용하여 분석 보고서를 작성하는 예시입니다.

```
[Markdown Cell] 
# 2024년 1월 매출 분석 보고서
작성자: 분석팀 | 작성일: 2024-02-01

## 1. 전체 매출 요약

[SQL Cell]
SELECT 
    DATE_TRUNC('week', sale_date) as week,
    SUM(amount) as weekly_revenue,
    COUNT(DISTINCT customer_id) as unique_customers
FROM sales
WHERE sale_date BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY DATE_TRUNC('week', sale_date)
ORDER BY week;
→ Line Chart로 시각화

[Markdown Cell]
## 2. 카테고리별 분석
전자제품 카테고리가 전체 매출의 42%를 차지하며...

[SQL Cell]
SELECT 
    product_category,
    SUM(amount) as revenue,
    COUNT(*) as orders
FROM sales s JOIN products p ON s.product_id = p.product_id
WHERE sale_date BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY product_category
ORDER BY revenue DESC;
→ Pie Chart로 시각화
```

### 3. 데이터 로드 및 관리

Query Editor v2에서 직접 데이터를 로드할 수도 있습니다.

```sql
-- S3에서 데이터 로드
COPY sales
FROM 's3://my-data-bucket/sales/2024/01/'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftS3ReadRole'
FORMAT AS PARQUET;

-- 로드 결과 확인
SELECT 
    query,
    TRIM(filename) as file,
    lines_scanned,
    lines_loaded,
    bytes_loaded,
    load_error_count
FROM stl_load_commits
WHERE query = pg_last_query_id();

-- VACUUM 및 ANALYZE 실행
VACUUM FULL sales;
ANALYZE sales;
```

```bash
# Query Editor v2 설정 확인
aws redshift describe-clusters \
  --cluster-identifier my-redshift-cluster \
  --query "Clusters[0].{Endpoint:Endpoint.Address,Port:Endpoint.Port,Status:ClusterStatus}" \
  --output table \
  --region ap-northeast-2
```

---

## 모범 사례/보안

### 접근 제어

1. **최소 권한 원칙**: sqlworkbench 권한을 역할별로 세분화합니다.
2. **팀 기반 공유**: 쿼리 공유 시 개별 사용자가 아닌 IAM 그룹 단위로 권한을 부여합니다.
3. **데이터 마스킹**: 민감한 데이터가 포함된 컬럼에 대한 접근을 제한합니다.

```bash
# 읽기 전용 분석가용 IAM 정책
aws iam create-policy \
  --policy-name RedshiftAnalystReadOnly \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "sqlworkbench:GetQueryExecutionHistory",
          "sqlworkbench:ExecuteQuery",
          "sqlworkbench:ListSavedQueries",
          "sqlworkbench:GetSavedQuery",
          "sqlworkbench:ListNotebooks",
          "sqlworkbench:GetNotebook"
        ],
        "Resource": "*"
      },
      {
        "Effect": "Deny",
        "Action": [
          "sqlworkbench:DeleteSavedQuery",
          "sqlworkbench:DeleteNotebook"
        ],
        "Resource": "*"
      }
    ]
  }' \
  --region ap-northeast-2
```

### 사용 모범 사례

1. **쿼리 저장 습관**: 유용한 쿼리는 반드시 저장하고 설명을 추가합니다.
2. **폴더 구조화**: 팀/프로젝트/용도별로 폴더를 구성합니다.
3. **LIMIT 사용**: 대량 결과를 방지하기 위해 탐색 쿼리에 LIMIT을 추가합니다.
4. **EXPLAIN 활용**: 쿼리 실행 전 EXPLAIN으로 실행 계획을 확인합니다.
5. **노트북 문서화**: 분석 노트북에 충분한 Markdown 설명을 포함합니다.

---

## 관련 서비스 비교

| 항목 | Query Editor v2 | Query Editor v1 | DBeaver / DataGrip | Amazon QuickSight |
|------|----------------|----------------|--------------------|-----------------|
| 설치 | 불필요 (웹) | 불필요 (웹) | 로컬 설치 필요 | 불필요 (웹) |
| 다중 탭 | 지원 | 미지원 | 지원 | 해당 없음 |
| 시각화 | 기본 차트 지원 | 미지원 | 플러그인 | 고급 대시보드 |
| 노트북 | 지원 | 미지원 | 미지원 | 해당 없음 |
| 협업 | 쿼리/노트북 공유 | 미지원 | 미지원 | 대시보드 공유 |
| VPC 필요 | 불필요 | 필요 | 필요 | 불필요 |
| 인증 | IAM / SSO | IAM | DB 자격 증명 | IAM / SSO |
| 비용 | 무료 | 무료 | 무료/유료 | 사용량 기반 |
| 적합 용도 | 데이터 탐색, Ad-hoc | 단순 쿼리 | 개발, DBA 작업 | BI 대시보드 |

**사용 시나리오별 권장 도구**

- **데이터 탐색 및 Ad-hoc 분석**: Query Editor v2
- **정기 BI 대시보드**: QuickSight
- **스키마 설계 및 DBA 작업**: DBeaver / DataGrip
- **자동화된 쿼리 실행**: Data API

---

## 요약

Amazon Redshift Query Editor v2는 Redshift 데이터 분석을 위한 완전한 웹 기반 도구입니다.

1. **설치 불필요**: 웹 브라우저만으로 Redshift에 접속하여 쿼리를 실행합니다.
2. **시각화 내장**: 쿼리 결과를 Line, Bar, Pie 등 다양한 차트로 즉시 시각화합니다.
3. **SQL 노트북**: Jupyter Notebook과 유사한 인터페이스로 분석 보고서를 작성합니다.
4. **팀 협업**: 쿼리와 노트북을 팀원과 공유하고, 버전 히스토리를 추적합니다.
5. **IAM / SSO 통합**: DB 자격 증명 관리 없이 IAM 기반으로 안전하게 접근합니다.
6. **Data API 기반**: 내부적으로 Data API를 사용하므로 VPC 연결이 불필요합니다.

Query Editor v2는 별도의 SQL 클라이언트 없이 Redshift 데이터를 빠르게 탐색하고 분석할 수 있는 가장 접근성이 높은 도구이며, 특히 데이터 분석가와 비즈니스 사용자에게 권장됩니다.