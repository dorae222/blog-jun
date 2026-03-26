# Amazon QuickSight SPICE 개요

## 개요

SPICE(Super-fast, Parallel, In-memory Calculation Engine)는 Amazon QuickSight의 핵심 인메모리 분석 엔진입니다. SPICE는 대규모 데이터를 인메모리에 로드하여 초고속 쿼리 성능을 제공하며, QuickSight의 서버리스 아키텍처를 뒷받침하는 기반 기술입니다.

전통적인 BI 도구는 데이터 소스에 직접 쿼리를 실행하기 때문에, 복잡한 분석 쿼리가 원본 데이터베이스의 성능에 영향을 줄 수 있었습니다. SPICE는 이 문제를 해결하기 위해 데이터를 별도의 인메모리 스토어에 캐싱하여, 원본 데이터 소스에 부하를 주지 않으면서도 빠른 분석을 가능하게 합니다.

SPICE의 주요 특징은 다음과 같습니다.

- **초고속 쿼리**: 인메모리 처리를 통해 밀리초 단위의 쿼리 응답 시간을 제공합니다.
- **자동 확장**: 동시 사용자 수에 따라 자동으로 확장되어 일관된 성능을 보장합니다.
- **컬럼 기반 저장**: 데이터를 컬럼 기반으로 저장하여 분석 쿼리에 최적화된 성능을 제공합니다.
- **데이터 압축**: 효율적인 압축 알고리즘을 사용하여 스토리지 사용량을 최소화합니다.
- **데이터 소스 부하 제거**: 원본 데이터 소스에 쿼리를 실행하지 않으므로 운영 데이터베이스의 성능에 영향을 주지 않습니다.

## 핵심 기능

### 1. 데이터 임포트 및 SPICE 용량 관리

SPICE에 데이터를 임포트하면 QuickSight가 데이터를 내부 인메모리 스토어에 로드합니다. 각 AWS 계정에는 리전별로 SPICE 용량이 할당되며, Enterprise 에디션 기준 사용자당 10GB가 기본 제공됩니다.

```bash
# SPICE 용량 확인
aws quicksight describe-account-settings \
  --aws-account-id 123456789012

# SPICE 데이터셋 생성 (import-mode: SPICE)
aws quicksight create-data-set \
  --aws-account-id 123456789012 \
  --data-set-id spice-sales-data \
  --name "Sales Data (SPICE)" \
  --import-mode SPICE \
  --physical-table-map '{
    "sales-table": {
      "RelationalTable": {
        "DataSourceArn": "arn:aws:quicksight:ap-northeast-2:123456789012:datasource/rds-source",
        "Schema": "public",
        "Name": "sales",
        "InputColumns": [
          {"Name": "sale_date", "Type": "DATETIME"},
          {"Name": "product_id", "Type": "STRING"},
          {"Name": "category", "Type": "STRING"},
          {"Name": "region", "Type": "STRING"},
          {"Name": "amount", "Type": "DECIMAL"},
          {"Name": "quantity", "Type": "INTEGER"}
        ]
      }
    }
  }'
```

### 2. 데이터 새로고침 (Refresh)

SPICE 데이터는 원본 데이터와 자동으로 동기화되지 않으므로, 정기적인 새로고침이 필요합니다. QuickSight는 전체 새로고침과 증분 새로고침 두 가지 방식을 지원합니다.

#### 전체 새로고침 (Full Refresh)

원본 데이터 소스에서 전체 데이터를 다시 로드합니다.

```bash
# 전체 새로고침 실행
aws quicksight create-ingestion \
  --aws-account-id 123456789012 \
  --data-set-id spice-sales-data \
  --ingestion-id full-refresh-$(date +%Y%m%d%H%M%S)

# 새로고침 상태 확인
aws quicksight describe-ingestion \
  --aws-account-id 123456789012 \
  --data-set-id spice-sales-data \
  --ingestion-id full-refresh-20240115100000 \
  --query 'Ingestion.{Status:IngestionStatus,RowsIngested:RowInfo.RowsIngested,TimeTaken:IngestionTimeInSeconds}'
```

#### 증분 새로고침 (Incremental Refresh)

특정 기간의 데이터만 새로 로드하여 새로고침 시간과 리소스를 절약합니다. 날짜/시간 컬럼을 기준으로 새로운 데이터만 추가 또는 업데이트합니다.

```bash
# 증분 새로고침이 포함된 스케줄 생성
aws quicksight create-refresh-schedule \
  --aws-account-id 123456789012 \
  --data-set-id spice-sales-data \
  --schedule '{
    "ScheduleId": "incremental-daily",
    "ScheduleFrequency": {
      "Interval": "DAILY",
      "TimeOfTheDay": "02:00"
    },
    "StartAfterDateTime": "2024-01-01T00:00:00Z",
    "RefreshType": "INCREMENTAL_REFRESH"
  }'

# 새로고침 스케줄 목록 조회
aws quicksight list-refresh-schedules \
  --aws-account-id 123456789012 \
  --data-set-id spice-sales-data
```

### 3. SPICE 용량 구매 및 관리

기본 제공되는 SPICE 용량이 부족한 경우, 추가 용량을 구매할 수 있습니다.

```bash
# SPICE 용량 조회
aws quicksight describe-account-subscription \
  --aws-account-id 123456789012 \
  --query 'AccountInfo.{Edition:Edition,NotificationEmail:NotificationEmail}'

# 데이터셋별 SPICE 사용량 확인
aws quicksight describe-data-set \
  --aws-account-id 123456789012 \
  --data-set-id spice-sales-data \
  --query 'DataSet.{Name:Name,ImportMode:ImportMode,ConsumedSpiceCapacityInBytes:ConsumedSpiceCapacityInBytes}'

# 모든 데이터셋의 SPICE 사용량 조회
aws quicksight list-data-sets \
  --aws-account-id 123456789012 \
  --query 'DataSetSummaries[?ImportMode==`SPICE`].{Name:Name,DataSetId:DataSetId}' \
  --output table
```

### 4. Direct Query 모드와의 비교

QuickSight는 SPICE 모드 외에도 Direct Query 모드를 지원합니다. 각 모드의 특성을 이해하고 적절한 상황에 맞는 모드를 선택하는 것이 중요합니다.

| 항목 | SPICE 모드 | Direct Query 모드 |
|------|-----------|------------------|
| 쿼리 대상 | 인메모리 캐시 | 원본 데이터 소스 |
| 응답 시간 | 밀리초 단위 | 데이터 소스에 의존 |
| 데이터 최신성 | 마지막 새로고침 시점 | 실시간 |
| 데이터 소스 부하 | 없음 | 있음 |
| 비용 | SPICE 용량 비용 | 데이터 소스 쿼리 비용 |
| 데이터 크기 제한 | 용량 제한 있음 | 제한 없음 |

## 아키텍처/동작 원리

### SPICE 내부 아키텍처

SPICE 엔진은 다음과 같은 내부 구조를 가지고 있습니다.

#### 1. 데이터 임포트 레이어

원본 데이터 소스에서 데이터를 추출하여 SPICE 형식으로 변환합니다. 이 과정에서 데이터 타입 변환, 압축, 컬럼 기반 저장이 이루어집니다.

#### 2. 컬럼 기반 스토리지

SPICE는 데이터를 행(Row) 기반이 아닌 열(Column) 기반으로 저장합니다. 분석 쿼리는 일반적으로 특정 열만 읽기 때문에, 컬럼 기반 저장은 불필요한 데이터 읽기를 줄여 성능을 크게 향상시킵니다.

```
행 기반 저장:                    컬럼 기반 저장:
[date, product, region, amount]  [date]    [product] [region] [amount]
[date, product, region, amount]  [date]    [product] [region] [amount]
[date, product, region, amount]  [date]    [product] [region] [amount]
...                              ...       ...       ...      ...

-> SUM(amount) 쿼리 시:          -> SUM(amount) 쿼리 시:
   모든 행을 읽어야 함              amount 열만 읽으면 됨
```

#### 3. 인메모리 캐시 레이어

변환된 데이터를 인메모리에 캐싱하여 빠른 쿼리 응답을 제공합니다. 자주 사용되는 데이터는 핫 캐시에 유지되고, 접근 빈도가 낮은 데이터는 워밍 프로세스를 통해 필요 시 로드됩니다.

#### 4. 쿼리 엔진

병렬 처리를 통해 복잡한 집계, 필터링, 조인 연산을 고속으로 수행합니다. 사용자 수가 증가하면 쿼리 엔진이 자동으로 확장됩니다.

### 데이터 새로고침 프로세스

```
[원본 데이터 소스] --> [데이터 추출] --> [변환/압축] --> [SPICE 로드] --> [캐시 업데이트]
      |                                                                    |
    RDS/S3/                                                          이전 데이터
    Athena 등                                                        교체/병합
```

### 데이터 압축

SPICE는 다양한 압축 기법을 사용하여 데이터 크기를 줄입니다.

- **사전 인코딩(Dictionary Encoding)**: 반복되는 값(카테고리, 지역 등)을 사전으로 관리하여 저장 공간을 절약합니다.
- **런 렝스 인코딩(Run-Length Encoding)**: 연속으로 동일한 값이 반복되는 경우 효율적으로 압축합니다.
- **비트 패킹(Bit Packing)**: 정수 값을 필요한 최소 비트 수로 표현하여 저장 공간을 줄입니다.

이러한 압축 덕분에 원본 데이터 대비 약 25~50% 수준으로 SPICE 용량이 절약됩니다.

### 자동 확장 메커니즘

SPICE는 동시 사용자 수와 쿼리 복잡도에 따라 자동으로 확장됩니다. 사용자가 개입할 필요 없이, 대시보드 접속자가 급증해도 일관된 성능을 유지합니다.

## 실전 활용

### 활용 사례 1: 대규모 로그 분석 대시보드

수십억 건의 로그 데이터를 SPICE에 집계 형태로 임포트하여 실시간 분석 대시보드를 구축합니다.

```bash
# Athena를 데이터 소스로 사용하여 집계 데이터를 SPICE에 임포트
aws quicksight create-data-set \
  --aws-account-id 123456789012 \
  --data-set-id log-analytics \
  --name "Log Analytics (Aggregated)" \
  --import-mode SPICE \
  --physical-table-map '{
    "athena-logs": {
      "CustomSql": {
        "DataSourceArn": "arn:aws:quicksight:ap-northeast-2:123456789012:datasource/athena-source",
        "Name": "aggregated_logs",
        "SqlQuery": "SELECT date_trunc('\''hour'\'' , event_time) as hour, service_name, log_level, COUNT(*) as event_count, COUNT(DISTINCT request_id) as unique_requests FROM application_logs WHERE event_time >= current_date - interval '\''30'\'' day GROUP BY 1, 2, 3",
        "Columns": [
          {"Name": "hour", "Type": "DATETIME"},
          {"Name": "service_name", "Type": "STRING"},
          {"Name": "log_level", "Type": "STRING"},
          {"Name": "event_count", "Type": "INTEGER"},
          {"Name": "unique_requests", "Type": "INTEGER"}
        ]
      }
    }
  }'
```

### 활용 사례 2: 다중 데이터 소스 통합 분석

여러 데이터 소스(RDS, S3, Athena)의 데이터를 SPICE에서 조인하여 통합 분석 뷰를 생성합니다.

```bash
# 데이터셋에 논리적 테이블 맵 업데이트 (조인 설정)
aws quicksight update-data-set \
  --aws-account-id 123456789012 \
  --data-set-id integrated-analysis \
  --name "Integrated Analysis" \
  --import-mode SPICE \
  --physical-table-map '{
    "orders": {
      "RelationalTable": {
        "DataSourceArn": "arn:aws:quicksight:ap-northeast-2:123456789012:datasource/rds-source",
        "Schema": "public",
        "Name": "orders",
        "InputColumns": [
          {"Name": "order_id", "Type": "STRING"},
          {"Name": "customer_id", "Type": "STRING"},
          {"Name": "amount", "Type": "DECIMAL"}
        ]
      }
    },
    "customers": {
      "S3Source": {
        "DataSourceArn": "arn:aws:quicksight:ap-northeast-2:123456789012:datasource/s3-source",
        "InputColumns": [
          {"Name": "customer_id", "Type": "STRING"},
          {"Name": "name", "Type": "STRING"},
          {"Name": "segment", "Type": "STRING"}
        ],
        "UploadSettings": {"Format": "CSV", "StartFromRow": 1, "ContainsHeader": true}
      }
    }
  }' \
  --logical-table-map '{
    "orders-logical": {
      "Alias": "Orders",
      "Source": {"PhysicalTableId": "orders"}
    },
    "customers-logical": {
      "Alias": "Customers",
      "Source": {"PhysicalTableId": "customers"}
    },
    "joined": {
      "Alias": "Orders with Customers",
      "Source": {
        "JoinInstruction": {
          "LeftOperand": "orders-logical",
          "RightOperand": "customers-logical",
          "Type": "LEFT",
          "OnClause": "customer_id = customer_id"
        }
      }
    }
  }'
```

### 활용 사례 3: API를 통한 자동화된 SPICE 관리

CI/CD 파이프라인에서 SPICE 데이터셋을 자동으로 관리하는 스크립트를 구성합니다.

```python
import boto3
import time
from datetime import datetime

def refresh_spice_dataset(account_id, dataset_id):
    client = boto3.client('quicksight', region_name='ap-northeast-2')
    
    ingestion_id = f"auto-refresh-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 새로고침 시작
    response = client.create_ingestion(
        AwsAccountId=account_id,
        DataSetId=dataset_id,
        IngestionId=ingestion_id
    )
    
    # 새로고침 완료 대기
    while True:
        status = client.describe_ingestion(
            AwsAccountId=account_id,
            DataSetId=dataset_id,
            IngestionId=ingestion_id
        )
        
        ingestion_status = status['Ingestion']['IngestionStatus']
        
        if ingestion_status == 'COMPLETED':
            rows = status['Ingestion']['RowInfo']['RowsIngested']
            print(f"새로고침 완료: {rows}행 임포트됨")
            return True
        elif ingestion_status in ('FAILED', 'CANCELLED'):
            print(f"새로고침 실패: {status['Ingestion'].get('ErrorInfo', {})}")
            return False
        
        time.sleep(10)
```

## 모범 사례/보안

### 성능 최적화 모범 사례

1. **필요한 데이터만 임포트**: 분석에 필요한 열과 행만 SPICE에 임포트합니다. Custom SQL을 사용하여 사전 필터링과 집계를 수행하면 SPICE 용량을 절약하고 쿼리 성능도 향상됩니다.

2. **증분 새로고침 활용**: 대규모 데이터셋의 경우 전체 새로고침 대신 증분 새로고침을 사용합니다. 날짜 기반 파티셔닝과 결합하면 새로고침 시간을 대폭 줄일 수 있습니다.

3. **데이터 타입 최적화**: 문자열 대신 적절한 데이터 타입(INTEGER, DECIMAL, DATETIME)을 사용하면 압축 효율이 높아지고 SPICE 용량이 절약됩니다.

4. **사전 집계**: 원시 데이터를 그대로 임포트하기보다, 분석에 필요한 수준으로 사전 집계하여 데이터량을 줄입니다.

5. **비활성 데이터셋 정리**: 사용하지 않는 SPICE 데이터셋을 정기적으로 정리하여 용량을 확보합니다.

```bash
# 비활성 데이터셋 식별 (최근 30일간 사용되지 않은 데이터셋)
aws quicksight list-data-sets \
  --aws-account-id 123456789012 \
  --query 'DataSetSummaries[?ImportMode==`SPICE`].{Name:Name,DataSetId:DataSetId,LastUpdated:LastUpdatedTime}' \
  --output table
```

### 비용 최적화

1. **SPICE 용량 모니터링**: 정기적으로 SPICE 사용량을 모니터링하고, 불필요한 데이터셋을 삭제합니다.
2. **Direct Query 혼합 사용**: 자주 접근하는 데이터만 SPICE에 임포트하고, 대용량이지만 접근 빈도가 낮은 데이터는 Direct Query를 사용합니다.
3. **새로고침 스케줄 최적화**: 비즈니스 요구사항에 맞는 최소한의 새로고침 빈도를 설정합니다.

### 보안 고려사항

1. **저장 시 암호화**: SPICE에 저장되는 데이터는 AWS 관리형 키로 자동 암호화됩니다. 고객 관리형 키(CMK)를 사용하여 추가적인 보안을 적용할 수도 있습니다.
2. **전송 중 암호화**: 데이터 소스에서 SPICE로의 데이터 전송은 TLS로 암호화됩니다.
3. **접근 제어**: SPICE 데이터셋에 대한 접근은 QuickSight의 IAM 정책과 데이터셋 권한으로 제어됩니다.

## 관련 서비스 비교

| 항목 | SPICE | Amazon Redshift | Amazon Athena | Amazon ElastiCache |
|------|-------|-----------------|---------------|--------------------|
| 유형 | 분석 전용 인메모리 | 데이터 웨어하우스 | 서버리스 쿼리 | 범용 인메모리 캐시 |
| 저장 방식 | 컬럼 기반 인메모리 | 컬럼 기반 디스크 | S3 기반 | 키-값 인메모리 |
| 쿼리 언어 | QuickSight 내부 | SQL | SQL | Redis/Memcached |
| 자동 확장 | 완전 자동 | 수동/자동(Serverless) | 완전 자동 | 수동/자동 |
| 용도 | BI 대시보드 분석 | 데이터 웨어하우징 | Ad-hoc 쿼리 | 애플리케이션 캐싱 |
| 통합 | QuickSight 전용 | 범용 | 범용 | 범용 |

## 요약

SPICE는 Amazon QuickSight의 성능과 사용자 경험을 결정하는 핵심 엔진입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **초고속 쿼리**: 컬럼 기반 인메모리 저장과 병렬 처리를 통해 밀리초 단위의 쿼리 응답을 제공합니다.
- **자동 확장**: 사용자 수에 따라 자동으로 확장되어 일관된 성능을 보장합니다.
- **효율적 압축**: 사전 인코딩, 런 렝스 인코딩 등 다양한 압축 기법으로 스토리지 사용량을 최소화합니다.
- **유연한 새로고침**: 전체 새로고침과 증분 새로고침을 지원하며, 스케줄 기반 자동 새로고침이 가능합니다.
- **데이터 소스 보호**: 원본 데이터 소스에 쿼리 부하를 주지 않아 운영 데이터베이스의 성능을 보호합니다.
- **비용 효율성**: 필요한 데이터만 임포트하고, 적절한 새로고침 전략을 사용하면 비용을 최적화할 수 있습니다.

SPICE를 효과적으로 활용하려면 데이터셋 설계 단계에서부터 SPICE의 특성을 고려하여, 필요한 데이터만 임포트하고 적절한 새로고침 주기를 설정하는 것이 중요합니다. 이를 통해 QuickSight의 성능을 극대화하면서도 비용을 효율적으로 관리할 수 있습니다.