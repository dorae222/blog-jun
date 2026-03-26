## 개요

Amazon Redshift Advisor는 Redshift 클러스터의 운영 메트릭과 쿼리 패턴을 자동으로 분석하여, 성능 향상과 비용 절감을 위한 구체적인 권장 사항을 제공하는 내장 도구입니다. DBA(Database Administrator)가 수동으로 수행하던 성능 튜닝 분석을 자동화하여, 전문 지식이 없는 팀에서도 Redshift의 성능을 최적화할 수 있도록 지원합니다.

Redshift Advisor는 추가 비용 없이 모든 Redshift 클러스터에서 사용할 수 있으며, AWS 콘솔의 Advisor 탭 또는 시스템 뷰(SVV_ALTER_TABLE_RECOMMENDATIONS 등)를 통해 권장 사항을 확인할 수 있습니다.

Advisor가 분석하는 영역은 크게 다음과 같습니다.

- 테이블 설계 (분산 키, 정렬 키, 압축 인코딩)
- 데이터 관리 (VACUUM, ANALYZE, 정렬 비율)
- 쿼리 패턴 및 워크로드
- 클러스터 리소스 활용률
- 보안 설정

---

## 핵심 기능

### 1. 테이블 설계 권장 사항

Advisor는 실제 쿼리 실행 패턴을 분석하여 테이블의 분산 키(DISTKEY)와 정렬 키(SORTKEY)를 최적화하도록 권장합니다.

**분산 키 변경 권장**

Advisor는 다음 조건에서 분산 키 변경을 권장합니다.

- 특정 테이블의 JOIN 쿼리에서 데이터 재분배(Redistribution)가 빈번하게 발생하는 경우
- 현재 분산 키의 데이터 편향(Skew)이 심한 경우
- EVEN 분산이 설정된 테이블에서 특정 키 기반 JOIN이 반복되는 경우

```bash
# Advisor의 테이블 변경 권장 사항 조회
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database mydb \
  --db-user admin \
  --sql "SELECT * FROM svv_alter_table_recommendations ORDER BY benefit DESC;" \
  --region ap-northeast-2

# 실행 결과 확인
aws redshift-data get-statement-result \
  --id <statement-id> \
  --region ap-northeast-2
```

`svv_alter_table_recommendations` 뷰의 주요 컬럼은 다음과 같습니다.

| 컬럼 | 설명 |
|------|------|
| type | 권장 유형 (redistribution, encoding, sortkey) |
| database | 대상 데이터베이스 |
| schema | 대상 스키마 |
| table | 대상 테이블 |
| ddl | 실행할 DDL 문 |
| benefit | 예상 성능 개선 효과 (상대값) |

**정렬 키 변경 권장**

정렬 키 권장은 쿼리의 WHERE/JOIN 절 분석을 기반으로 합니다.

```sql
-- Advisor가 권장하는 DDL 예시
ALTER TABLE sales ALTER SORTKEY (sale_date, product_id);

-- 변경 전후 Zone Map 효과 확인
SELECT 
    "table",
    sortkey1,
    unsorted,
    tbl_rows,
    skew_rows
FROM svv_table_info 
WHERE schema = 'public'
ORDER BY unsorted DESC;
```

### 2. 압축 인코딩 권장

Advisor는 테이블의 각 컬럼에 대해 최적의 압축 인코딩을 분석합니다.

```bash
# 특정 테이블의 압축 분석 실행
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database mydb \
  --db-user admin \
  --sql "ANALYZE COMPRESSION sales;" \
  --region ap-northeast-2
```

압축 분석 결과 예시는 다음과 같습니다.

```
 Column     | Encoding | Est_reduction_pct
-----------+----------+------------------
 sale_id    | az64     | 45.2
 product_id | az64     | 38.7
 sale_date  | az64     | 52.1
 amount     | az64     | 41.3
 status     | bytedict | 78.5
 notes      | zstd     | 65.2
```

압축 인코딩 변경 시 주의사항이 있습니다. Redshift에서는 기존 테이블의 컬럼 인코딩을 직접 변경할 수 없습니다. 새 테이블을 생성하고 데이터를 이동하는 Deep Copy 방식을 사용해야 합니다.

```sql
-- Deep Copy를 통한 압축 인코딩 변경
CREATE TABLE sales_new (
    sale_id BIGINT ENCODE az64,
    product_id INTEGER ENCODE az64,
    sale_date DATE ENCODE az64,
    amount DECIMAL(10,2) ENCODE az64,
    status VARCHAR(20) ENCODE bytedict,
    notes VARCHAR(500) ENCODE zstd
)
DISTKEY(product_id)
SORTKEY(sale_date);

INSERT INTO sales_new SELECT * FROM sales;

DROP TABLE sales;
ALTER TABLE sales_new RENAME TO sales;
```

### 3. VACUUM 및 ANALYZE 권장

Advisor는 다음 상황에서 VACUUM 또는 ANALYZE 실행을 권장합니다.

- **VACUUM 권장 조건**: 테이블의 비정렬(unsorted) 비율이 높은 경우, 삭제된 행(ghost rows)이 많은 경우
- **ANALYZE 권장 조건**: 테이블의 통계 정보가 오래된 경우, 대량 데이터 로드 후 통계가 갱신되지 않은 경우

```bash
# VACUUM 필요 테이블 확인
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database mydb \
  --db-user admin \
  --sql "SELECT \"table\", unsorted, empty as ghost_rows_pct, stats_off FROM svv_table_info WHERE schema = 'public' AND (unsorted > 5 OR empty > 5 OR stats_off > 10) ORDER BY unsorted DESC;" \
  --region ap-northeast-2
```

### 4. 워크로드 관리(WLM) 권장

Advisor는 WLM 큐의 대기 시간, 메모리 사용률, 동시 쿼리 수 등을 분석하여 WLM 설정 최적화를 권장합니다.

주요 권장 사항은 다음과 같습니다.

- **Short Query Acceleration (SQA) 활성화**: 짧은 쿼리가 긴 쿼리 뒤에서 대기하는 것을 방지합니다.
- **Concurrency Scaling 활성화**: 피크 시간대 동시성을 자동 확장합니다.
- **큐 메모리 재분배**: 특정 큐의 메모리가 과다/과소 할당된 경우 재조정합니다.

### 5. 보안 권장 사항

Advisor는 보안 관련 권장 사항도 제공합니다.

- SSL 연결이 강제되지 않은 경우 경고
- 감사 로그가 비활성화된 경우 활성화 권장
- 공개 접근이 가능한 클러스터에 대한 경고

---

## 아키텍처/동작 원리

### Advisor 데이터 수집 파이프라인

Redshift Advisor는 다음 데이터 소스를 기반으로 권장 사항을 생성합니다.

```
[시스템 테이블/뷰]
  |- STL_QUERY (쿼리 실행 이력)
  |- STL_WLM_QUERY (WLM 큐 이력)
  |- STL_SCAN (테이블 스캔 이력)
  |- STL_DIST (데이터 재분배 이력)
  |- SVV_TABLE_INFO (테이블 메타데이터)
  |- SVL_QUERY_SUMMARY (쿼리 실행 요약)
        |
        v
[Advisor 분석 엔진]
  |- 쿼리 패턴 분석
  |- 리소스 활용률 분석
  |- 테이블 설계 분석
  |- 보안 설정 분석
        |
        v
[권장 사항 생성]
  |- svv_alter_table_recommendations
  |- AWS Console Advisor 탭
  |- CloudWatch 메트릭
```

### 권장 사항의 우선순위 결정

Advisor는 각 권장 사항에 benefit 점수를 부여합니다. 이 점수는 다음 요소를 종합적으로 고려합니다.

1. **영향 범위**: 해당 변경이 영향을 미치는 쿼리 수
2. **성능 개선 폭**: 예상되는 쿼리 실행 시간 단축 비율
3. **리소스 절감**: CPU, I/O, 메모리 절감 규모
4. **적용 난이도**: 변경에 필요한 다운타임 및 작업 복잡도

### Automatic Table Optimization (ATO)

Redshift는 Advisor의 권장 사항을 자동으로 적용하는 ATO(Automatic Table Optimization) 기능도 제공합니다.

- 테이블 생성 시 DISTKEY/SORTKEY를 AUTO로 설정하면, Redshift가 쿼리 패턴에 따라 자동으로 최적의 키를 선택하고 변경합니다.
- 인코딩도 AUTO로 설정하면 자동 최적화됩니다.

```sql
-- ATO가 활성화된 테이블 생성
CREATE TABLE orders (
    order_id BIGINT,
    customer_id INTEGER,
    order_date DATE,
    total_amount DECIMAL(12,2),
    status VARCHAR(20)
)
DISTSTYLE AUTO
SORTKEY AUTO
ENCODE AUTO;
```

---

## 실전 활용

### 1. Advisor 권장 사항 일괄 조회 및 적용 워크플로우

실전에서는 Advisor 권장 사항을 정기적으로 확인하고 우선순위에 따라 적용하는 워크플로우를 구축하는 것이 효과적입니다.

```bash
# 모든 테이블 변경 권장 사항 조회
aws redshift-data execute-statement \
  --cluster-identifier my-redshift-cluster \
  --database mydb \
  --db-user admin \
  --sql "SELECT type, \"table\", ddl, benefit FROM svv_alter_table_recommendations WHERE benefit > 50 ORDER BY benefit DESC LIMIT 20;" \
  --region ap-northeast-2
```

권장 적용 절차는 다음과 같습니다.

1. **benefit 점수순 정렬**: 가장 효과가 큰 권장 사항부터 적용합니다.
2. **개발 환경 테스트**: 프로덕션 적용 전 개발 클러스터에서 검증합니다.
3. **실행 계획 비교**: 변경 전후의 EXPLAIN 결과를 비교합니다.
4. **점진적 적용**: 한 번에 모든 변경을 적용하지 않고, 하나씩 적용하며 효과를 측정합니다.

### 2. 쿼리 성능 진단과 Advisor 활용

느린 쿼리가 발견되면 다음 단계로 원인을 분석합니다.

```sql
-- 1단계: 실행 시간이 긴 쿼리 식별
SELECT 
    query,
    TRIM(querytxt) as sql_text,
    starttime,
    endtime,
    DATEDIFF(seconds, starttime, endtime) as duration_sec,
    aborted
FROM stl_query
WHERE starttime >= DATEADD(day, -1, GETDATE())
  AND userid > 1
ORDER BY duration_sec DESC
LIMIT 10;

-- 2단계: 쿼리의 실행 단계별 시간 분석
SELECT 
    query,
    segment,
    step,
    label,
    rows,
    bytes,
    elapsed/1000000.0 as elapsed_sec
FROM svl_query_summary
WHERE query = <query_id>
ORDER BY segment, step;

-- 3단계: 데이터 재분배(Redistribution) 확인
SELECT 
    query,
    tbl,
    rows,
    bytes,
    packets
FROM stl_dist
WHERE query = <query_id>
ORDER BY bytes DESC;
```

### 3. 비용 최적화를 위한 Advisor 활용

Advisor는 직접적으로 비용 절감 권장 사항을 제공하지는 않지만, 성능 최적화를 통해 간접적으로 비용을 절감할 수 있습니다.

- **압축 최적화**: 스토리지 사용량 감소로 RA3 노드의 Managed Storage 비용 절감
- **쿼리 효율화**: Concurrency Scaling 사용량 감소
- **리소스 활용 최적화**: 더 작은 노드 타입으로 다운사이징 가능

```bash
# 클러스터 리소스 사용률 확인
aws cloudwatch get-metric-statistics \
  --namespace AWS/Redshift \
  --metric-name CPUUtilization \
  --dimensions Name=ClusterIdentifier,Value=my-redshift-cluster \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-16T00:00:00Z \
  --period 3600 \
  --statistics Average \
  --region ap-northeast-2
```

---

## 모범 사례/보안

### Advisor 활용 모범 사례

1. **주간 리뷰**: 최소 주 1회 Advisor 권장 사항을 확인합니다.
2. **자동화**: Lambda + EventBridge를 사용하여 새로운 Advisor 권장 사항을 Slack/Teams로 자동 알림합니다.
3. **ATO 활용**: 신규 테이블에는 DISTSTYLE AUTO, SORTKEY AUTO를 기본으로 적용합니다.
4. **SQA 활성화**: Short Query Acceleration을 활성화하여 짧은 쿼리의 대기 시간을 줄입니다.
5. **VACUUM/ANALYZE 자동화**: 정기적으로 VACUUM과 ANALYZE를 실행하는 스케줄을 구성합니다.

### 보안 권장 사항 준수

```bash
# SSL 연결 강제
aws redshift modify-cluster-parameter-group \
  --parameter-group-name my-params \
  --parameters '[{"ParameterName":"require_ssl","ParameterValue":"true","ApplyType":"static"}]' \
  --region ap-northeast-2

# 감사 로그 활성화
aws redshift enable-logging \
  --cluster-identifier my-redshift-cluster \
  --bucket-name my-redshift-audit-logs \
  --s3-key-prefix audit/ \
  --region ap-northeast-2
```

---

## 관련 서비스 비교

| 항목 | Redshift Advisor | AWS Trusted Advisor | Performance Insights (RDS) |
|------|-----------------|--------------------|--------------------------|
| 대상 서비스 | Redshift 전용 | AWS 전체 | RDS/Aurora 전용 |
| 분석 영역 | 테이블 설계, 쿼리, WLM, 보안 | 비용, 성능, 보안, 내결함성 | DB 부하, 대기 이벤트 |
| 자동 적용 | ATO (분산/정렬/압축) | 수동 적용 필요 | 해당 없음 (모니터링 전용) |
| 비용 | 무료 (Redshift에 포함) | Basic/Developer: 일부 무료 | 무료 (7일) / 유료 (2년) |
| 데이터 소스 | 시스템 테이블 (STL/SVV) | CloudWatch, Config 등 | Performance Schema |
| 갱신 주기 | 실시간~일 단위 | 일 단위 | 초 단위 |

---

## 요약

Amazon Redshift Advisor는 Redshift 클러스터의 성능과 비용을 최적화하기 위한 필수 도구입니다.

1. **쿼리 패턴 기반 분석**: 실제 워크로드를 분석하여 테이블 설계(분산 키, 정렬 키, 압축)를 최적화하는 구체적인 DDL을 제안합니다.
2. **benefit 점수**: 각 권장 사항에 정량적인 효과 점수를 부여하여 우선순위 결정을 지원합니다.
3. **VACUUM/ANALYZE 관리**: 데이터 정리와 통계 갱신이 필요한 테이블을 자동으로 식별합니다.
4. **WLM 최적화**: 큐 설정, SQA, Concurrency Scaling에 대한 권장 사항을 제공합니다.
5. **ATO와 연계**: DISTSTYLE AUTO, SORTKEY AUTO를 사용하면 Advisor의 분석 결과가 자동으로 적용됩니다.
6. **무료**: 추가 비용 없이 모든 Redshift 클러스터에서 사용할 수 있습니다.

Advisor의 권장 사항을 정기적으로 확인하고 체계적으로 적용하는 것이, Redshift 운영 최적화의 첫걸음입니다.