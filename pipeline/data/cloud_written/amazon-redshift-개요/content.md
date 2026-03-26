## 개요

Amazon Redshift는 AWS에서 제공하는 완전 관리형 페타바이트급 클라우드 데이터 웨어하우스 서비스입니다. PostgreSQL 8.0.2를 기반으로 개발되었으며, 대규모 분석 쿼리(OLAP)에 최적화된 열 기반(Columnar) 스토리지와 대규모 병렬 처리(MPP, Massively Parallel Processing) 아키텍처를 채택하고 있습니다.

전통적인 데이터 웨어하우스 솔루션(Teradata, Oracle Exadata 등)은 초기 하드웨어 비용이 수억 원에 달하고, 용량 확장에도 상당한 시간과 비용이 필요합니다. Redshift는 이러한 진입 장벽을 낮추어, 시간당 $0.25부터 시작하여 필요에 따라 페타바이트 규모까지 확장할 수 있는 유연한 데이터 웨어하우스를 제공합니다.

2023년에는 Amazon Redshift Serverless가 GA(General Availability)되면서, 클러스터 프로비저닝 없이도 쿼리 실행 시에만 과금되는 서버리스 방식도 선택할 수 있게 되었습니다.

---

## 핵심 기능

### 1. Columnar Storage (열 기반 스토리지)

전통적인 행 기반(Row-based) 데이터베이스와 달리, Redshift는 데이터를 열(Column) 단위로 저장합니다. 이는 분석 쿼리에서 극적인 성능 향상을 가져옵니다.

**행 기반 vs 열 기반 비교**

```
[행 기반 저장]
Block 1: | id=1, name=Alice, age=30, city=Seoul     |
Block 2: | id=2, name=Bob,   age=25, city=Busan     |
Block 3: | id=3, name=Carol, age=35, city=Seoul     |

→ SELECT AVG(age) FROM users; 
  → 모든 블록을 읽어야 함 (불필요한 name, city도 읽음)

[열 기반 저장]
Block 1: | id:   1, 2, 3, 4, 5, ...    |
Block 2: | name: Alice, Bob, Carol, ... |
Block 3: | age:  30, 25, 35, ...        |
Block 4: | city: Seoul, Busan, Seoul, ...|

→ SELECT AVG(age) FROM users;
  → age 블록만 읽으면 됨 (I/O 대폭 감소)
```

열 기반 저장의 장점은 다음과 같습니다.

- **I/O 감소**: 쿼리에 필요한 컬럼만 읽어 디스크 I/O를 최소화합니다.
- **높은 압축률**: 같은 타입의 데이터가 연속으로 저장되어 압축 효율이 매우 높습니다.
- **벡터 처리**: CPU의 SIMD 명령어를 활용한 벡터 연산이 가능합니다.

### 2. 압축 인코딩 (Compression Encoding)

Redshift는 컬럼별로 최적의 압축 인코딩을 적용합니다.

| 인코딩 | 설명 | 적합한 데이터 |
|--------|------|---------------|
| AZ64 | Amazon 독자 알고리즘, 숫자/날짜에 최적 | 숫자, 날짜/시간 |
| LZO | 범용 압축 | VARCHAR, 긴 문자열 |
| ZSTD | 높은 압축률과 빠른 압축/해제 | 대부분의 데이터 타입 |
| Bytedict | 고유 값이 적은 경우 딕셔너리 기반 | 카테고리, 상태 코드 |
| Delta | 연속 값의 차이만 저장 | 자동 증가 ID, 타임스탬프 |
| Runlength | 연속 반복 값을 횟수로 저장 | 정렬된 컬럼의 반복 값 |
| Raw | 비압축 | SORTKEY의 첫 번째 컬럼 |

```bash
# 테이블의 최적 압축 인코딩 분석
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database mydb \
  --db-user admin \
  --sql "ANALYZE COMPRESSION sales;" \
  --region ap-northeast-2
```

### 3. 분산 스타일 (Distribution Style)

데이터를 노드 간에 어떻게 분배할지 결정하는 분산 스타일은 쿼리 성능에 결정적인 영향을 미칩니다.

- **KEY**: 지정한 컬럼 값의 해시에 따라 같은 값을 같은 노드에 배치합니다. JOIN이 빈번한 대형 테이블에 적합합니다.
- **EVEN**: 라운드 로빈 방식으로 균등 분배합니다. JOIN이 없는 테이블에 적합합니다.
- **ALL**: 모든 노드에 전체 데이터를 복사합니다. 작은 차원(Dimension) 테이블에 적합합니다.
- **AUTO**: Redshift가 데이터 크기와 쿼리 패턴에 따라 자동으로 최적 분산 스타일을 선택합니다.

```sql
-- KEY 분산: 대형 팩트 테이블
CREATE TABLE sales (
    sale_id BIGINT IDENTITY(1,1),
    product_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,
    sale_date DATE NOT NULL,
    amount DECIMAL(10,2) NOT NULL
)
DISTKEY(product_id)
SORTKEY(sale_date);

-- ALL 분산: 작은 차원 테이블
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name VARCHAR(200),
    category VARCHAR(50),
    price DECIMAL(10,2)
)
DISTSTYLE ALL;
```

### 4. 정렬 키 (Sort Key)

Sort Key는 디스크에 데이터가 물리적으로 정렬되는 기준을 정의합니다.

- **Compound Sort Key**: 지정 순서대로 다단계 정렬합니다. 첫 번째 키를 포함하는 쿼리에서 효과적입니다.
- **Interleaved Sort Key**: 모든 키에 동일한 가중치를 부여합니다. 다양한 컬럼으로 필터링하는 경우 효과적이지만, VACUUM 비용이 높습니다.
- **AUTO Sort Key**: Redshift가 쿼리 패턴을 분석하여 자동으로 정렬 키를 관리합니다.

Sort Key를 잘 설정하면 Zone Map을 통한 블록 스킵이 가능해져 I/O가 크게 감소합니다.

---

## 아키텍처/동작 원리

### Redshift 클러스터 아키텍처

```
[Client / BI Tool / Application]
        |
        v
[Leader Node]
  - SQL 파싱 및 쿼리 플랜 생성
  - 쿼리 컴파일 및 코드 생성
  - Compute Node로 실행 계획 분배
  - 결과 집계 및 클라이언트 반환
        |
        v
[Compute Node 1]  [Compute Node 2]  [Compute Node N]
  |-- Slice 1       |-- Slice 1       |-- Slice 1
  |-- Slice 2       |-- Slice 2       |-- Slice 2
  |-- ...           |-- ...           |-- ...
```

**Leader Node**: SQL을 파싱하고 실행 계획을 수립합니다. 쿼리를 컴파일하여 최적화된 C++ 코드를 생성합니다. 결과를 집계하여 클라이언트에 반환합니다. 단, 분산 처리가 필요하지 않은 쿼리(EXPLAIN, SHOW 등)는 Leader Node에서만 실행됩니다.

**Compute Node**: 실제 데이터 처리를 수행합니다. 각 노드는 여러 개의 Slice로 나뉘며, 각 Slice가 독립적으로 쿼리를 처리합니다. 노드 유형에 따라 Slice 수가 결정됩니다(예: dc2.large = 2 slices, ra3.xlplus = 2 slices).

**Slice**: Compute Node 내의 가상 처리 단위입니다. 각 Slice는 고유한 메모리, CPU, 스토리지를 할당받아 독립적으로 쿼리를 실행합니다. 분산 스타일에 따라 데이터가 Slice에 배치됩니다.

### RA3 노드와 Managed Storage

Redshift의 최신 노드 타입인 RA3는 컴퓨팅과 스토리지를 분리하여 독립적으로 확장할 수 있습니다.

- **Redshift Managed Storage (RMS)**: 데이터를 자동으로 로컬 SSD와 S3 사이에 계층화합니다. 자주 접근하는 데이터(Hot Data)는 로컬 SSD에, 덜 접근하는 데이터(Cold Data)는 S3에 저장합니다.
- **확장성**: 스토리지는 S3로 무제한 확장되며, 컴퓨팅은 노드 수를 조정하여 확장합니다.

```bash
# RA3 노드 기반 클러스터 생성
aws redshift create-cluster \
  --cluster-identifier my-redshift-cluster \
  --node-type ra3.xlplus \
  --number-of-nodes 2 \
  --master-username admin \
  --master-user-password "SecurePass123!" \
  --db-name mydb \
  --vpc-security-group-ids sg-0123456789abcdef0 \
  --cluster-subnet-group-name my-redshift-subnet \
  --iam-roles arn:aws:iam::123456789012:role/RedshiftS3ReadRole \
  --encrypted \
  --kms-key-id arn:aws:kms:ap-northeast-2:123456789012:key/my-key \
  --region ap-northeast-2
```

### 쿼리 실행 흐름

1. 클라이언트가 Leader Node에 SQL 쿼리를 전송합니다.
2. Leader Node가 쿼리를 파싱하고 실행 계획(Query Plan)을 수립합니다.
3. 실행 계획을 C++ 코드로 컴파일합니다 (Code Generation).
4. 컴파일된 코드를 각 Compute Node의 관련 Slice에 분배합니다.
5. 각 Slice가 병렬로 데이터를 처리합니다.
6. 중간 결과가 필요한 경우 노드 간 데이터 재분배(Redistribution)가 발생합니다.
7. Leader Node가 모든 Slice의 결과를 집계하여 클라이언트에 반환합니다.

---

## 실전 활용

### 1. COPY 명령을 통한 대량 데이터 로드

Redshift에 데이터를 로드하는 가장 효율적인 방법은 COPY 명령입니다.

```bash
# S3에서 데이터 로드 (COPY 명령 실행)
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database mydb \
  --db-user admin \
  --sql "COPY sales FROM 's3://my-data-bucket/sales/' IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftS3ReadRole' FORMAT AS PARQUET;" \
  --region ap-northeast-2
```

COPY 명령 최적화 팁은 다음과 같습니다.

- **파일 분할**: 파일 수를 Slice 수의 배수로 맞추면 병렬 로딩 효율이 극대화됩니다.
- **Parquet/ORC 사용**: 열 기반 포맷을 사용하면 변환 오버헤드가 줄어듭니다.
- **COMPUPDATE OFF**: 대량 로드 시 자동 압축 분석을 건너뛰어 로드 속도를 높입니다.
- **Manifest 파일**: 정확한 파일 목록을 지정하여 의도치 않은 파일 로드를 방지합니다.

### 2. UNLOAD를 통한 데이터 추출

```sql
UNLOAD ('SELECT * FROM sales WHERE sale_date >= \'2024-01-01\'') 
TO 's3://my-data-bucket/exports/sales_2024/' 
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftS3WriteRole'
FORMAT AS PARQUET
PARTITION BY (sale_date)
ALLOWOVERWRITE;
```

### 3. Workload Management (WLM)

WLM은 동시 쿼리 실행을 관리하는 메커니즘입니다. 쿼리를 큐에 분류하여 리소스를 할당합니다.

```bash
# WLM 설정이 포함된 파라미터 그룹 생성
aws redshift create-cluster-parameter-group \
  --parameter-group-name my-wlm-config \
  --parameter-group-family redshift-1.0 \
  --description "Custom WLM configuration" \
  --region ap-northeast-2

# WLM 큐 설정
aws redshift modify-cluster-parameter-group \
  --parameter-group-name my-wlm-config \
  --parameters '[{"ParameterName":"wlm_json_configuration","ParameterValue":"[{\"query_group\":[\"etl\"],\"memory_percent_to_use\":50,\"query_concurrency\":5},{\"query_group\":[\"dashboard\"],\"memory_percent_to_use\":30,\"query_concurrency\":10},{\"memory_percent_to_use\":20,\"query_concurrency\":5}]","ApplyType":"dynamic"}]' \
  --region ap-northeast-2
```

### 4. Redshift Spectrum

Redshift Spectrum을 사용하면 S3에 있는 데이터를 Redshift 테이블처럼 직접 쿼리할 수 있습니다. ETL 없이 데이터 레이크의 데이터를 분석할 수 있습니다.

```sql
-- 외부 스키마 생성 (Glue Data Catalog 연동)
CREATE EXTERNAL SCHEMA spectrum_schema
FROM DATA CATALOG
DATABASE 'my_datalake_db'
IAM_ROLE 'arn:aws:iam::123456789012:role/RedshiftSpectrumRole'
REGION 'ap-northeast-2';

-- S3의 외부 테이블과 Redshift 내부 테이블을 JOIN
SELECT 
    s.product_id,
    p.product_name,
    SUM(s.amount) as total_sales
FROM spectrum_schema.sales_history s
JOIN products p ON s.product_id = p.product_id
WHERE s.sale_date >= '2024-01-01'
GROUP BY s.product_id, p.product_name
ORDER BY total_sales DESC
LIMIT 20;
```

---

## 모범 사례/보안

### 성능 최적화

1. **적절한 분산 키 선택**: JOIN에 자주 사용되는 컬럼을 DISTKEY로 설정하여 노드 간 데이터 재분배를 최소화합니다.
2. **정렬 키 활용**: WHERE 절에 자주 사용되는 컬럼(날짜, 상태 등)을 SORTKEY로 설정합니다.
3. **VACUUM 정기 실행**: DELETE/UPDATE 후 발생하는 고스트 행(Ghost Rows)을 정리합니다.
4. **ANALYZE 실행**: 통계 정보를 최신 상태로 유지하여 쿼리 옵티마이저의 판단을 돕습니다.
5. **Result Cache 활용**: 동일한 쿼리가 반복되면 결과를 캐시에서 반환합니다.

```bash
# 테이블 상태 확인 (비정렬 비율, 고스트 행 비율)
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database mydb \
  --db-user admin \
  --sql "SELECT \"table\", unsorted, empty, tbl_rows FROM svv_table_info WHERE schema = 'public' ORDER BY unsorted DESC;" \
  --region ap-northeast-2
```

### 보안 체계

- **VPC 격리**: Redshift 클러스터를 Private Subnet에 배치합니다.
- **저장 데이터 암호화**: KMS 또는 HSM(Hardware Security Module)을 사용하여 AES-256 암호화를 적용합니다.
- **전송 암호화**: SSL/TLS를 사용하여 클라이언트와 클러스터 간 통신을 암호화합니다.
- **감사 로그**: 연결, 사용자 활동, 쿼리를 S3에 로깅합니다.
- **컬럼 레벨 접근 제어**: GRANT/REVOKE로 특정 컬럼에 대한 접근을 제어합니다.

```bash
# 감사 로그 활성화
aws redshift modify-cluster \
  --cluster-identifier my-redshift-cluster \
  --logging-properties BucketName=my-redshift-logs-bucket,S3KeyPrefix=redshift-audit/ \
  --region ap-northeast-2
```

---

## 관련 서비스 비교

| 항목 | Amazon Redshift | Amazon Athena | Google BigQuery | Snowflake |
|------|----------------|---------------|-----------------|----------|
| 유형 | 프로비저닝 + 서버리스 | 서버리스 | 서버리스 | 프로비저닝 + 서버리스 |
| 스토리지 | Managed Storage (SSD+S3) | S3 직접 쿼리 | 자체 관리형 | 자체 관리형 |
| 쿼리 엔진 | MPP + Columnar | Presto/Trino | Dremel | MPP + Columnar |
| 동시성 | WLM 기반 관리 | 무제한 (쿼리별 과금) | 슬롯 기반 | 가상 웨어하우스 |
| 가격 모델 | 노드 시간 또는 RPU | 스캔 데이터량 | 스캔 데이터량 또는 슬롯 | 크레딧 |
| 적합 시나리오 | 대규모 정형 분석, BI | Ad-hoc 쿼리, 데이터 레이크 | 서버리스 분석 | 멀티 클라우드 분석 |

---

## 요약

Amazon Redshift는 대규모 데이터 분석을 위한 업계 선도적인 클라우드 데이터 웨어하우스입니다.

1. **열 기반 스토리지 + MPP 아키텍처**로 페타바이트급 데이터를 빠르게 분석합니다.
2. **분산 키(DISTKEY)와 정렬 키(SORTKEY)**를 적절히 설정하는 것이 성능의 핵심입니다.
3. **RA3 노드**의 Managed Storage로 컴퓨팅과 스토리지를 독립적으로 확장합니다.
4. **Redshift Spectrum**으로 데이터 레이크(S3)의 데이터를 ETL 없이 직접 쿼리할 수 있습니다.
5. **WLM**을 통해 다양한 워크로드의 리소스를 효과적으로 관리합니다.
6. **KMS 암호화, VPC 격리, 감사 로그**로 엔터프라이즈급 보안을 제공합니다.
7. 정기적인 **VACUUM**과 **ANALYZE** 실행이 안정적인 성능 유지의 핵심입니다.