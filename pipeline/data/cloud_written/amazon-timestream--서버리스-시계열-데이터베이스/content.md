<!-- infographic-hero -->
![Amazon Timestream 핵심 요약](figures/infographic.svg)

*Figure: Amazon Timestream 한 장 요약 인포그래픽*

## 개요

Amazon Timestream은 IoT 센서 데이터, 애플리케이션 메트릭, DevOps 모니터링 로그 등 시계열(time-series) 데이터를 위해 특별히 설계된 완전관리형 서버리스 데이터베이스입니다. 하루에 수조 건의 이벤트를 저장하고 분석할 수 있으며, 관계형 데이터베이스 대비 최대 1,000배 빠르고 1/10 수준의 비용으로 시계열 데이터를 처리할 수 있습니다.

Timestream은 AWS의 목적별 데이터베이스(purpose-built database) 철학을 반영한 서비스입니다. 범용 관계형 데이터베이스로 시계열 데이터를 다루면 시간이 지남에 따라 테이블 크기가 급격히 커지고, 시간 범위 쿼리의 성능이 저하되며, 오래된 데이터의 관리가 복잡해집니다. Timestream은 이러한 문제를 계층형 스토리지, 자동 데이터 라이프사이클 관리, 시계열 전용 쿼리 함수로 근본적으로 해결합니다.

Timestream은 서버리스로 운영되므로 인프라 프로비저닝, 용량 계획, 스케일링 관리가 불필요합니다. 데이터 수집량과 쿼리 양에 따라 자동으로 확장/축소되며, 사용한 만큼만 과금됩니다.

## 핵심 기능

### 데이터 모델

Timestream의 데이터 모델은 시계열 데이터에 최적화되어 있습니다.

- **Database**: 최상위 컨테이너로, 관련 테이블을 그룹화합니다.
- **Table**: 시계열 데이터를 저장하는 단위입니다.
- **Record**: 하나의 데이터 포인트로, 디멘전(Dimensions), 측정값(Measures), 타임스탬프로 구성됩니다.
- **Dimension**: 데이터의 메타데이터 (예: device_id, region, sensor_type). 인덱싱됩니다.
- **Measure**: 실제 측정값 (예: temperature, cpu_usage, latency).
- **Time**: 레코드의 타임스탬프.

```sql
-- Timestream 테이블 구조 예시 (개념적 표현)
-- Dimensions: device_id(VARCHAR), region(VARCHAR)
-- Measure Name: temperature, humidity
-- Measure Value: DOUBLE
-- Time: TIMESTAMP
```

### 계층형 스토리지

Timestream은 두 가지 스토리지 계층을 제공합니다.

1. **메모리 스토어(Memory Store)**: 최신 데이터를 저장합니다. 빠른 쓰기와 포인트 쿼리에 최적화되어 있습니다. 보존 기간을 시간/일 단위로 설정합니다.

2. **마그네틱 스토어(Magnetic Store)**: 과거 데이터를 저장합니다. 비용 효율적이며 대량 분석 쿼리에 최적화되어 있습니다. 보존 기간을 일/월/년 단위로 설정합니다.

데이터는 메모리 스토어에서 마그네틱 스토어로 자동 이동되며, 보존 기간이 만료되면 자동 삭제됩니다. 이 과정은 완전히 자동화되어 있어 별도의 관리가 필요하지 않습니다.

### 시계열 전용 쿼리 함수

Timestream은 SQL 호환 쿼리 언어에 시계열 분석을 위한 전용 함수를 추가로 제공합니다.

```sql
-- 시간 기반 집계
SELECT
    device_id,
    bin(time, 1h) AS hourly_bucket,
    AVG(measure_value::double) AS avg_temperature,
    MAX(measure_value::double) AS max_temperature,
    MIN(measure_value::double) AS min_temperature
FROM "iot_db"."sensor_data"
WHERE measure_name = 'temperature'
    AND time BETWEEN ago(24h) AND now()
GROUP BY device_id, bin(time, 1h)
ORDER BY device_id, hourly_bucket;

-- 시간 보간 (Interpolation)
SELECT
    device_id,
    INTERPOLATE_LINEAR(
        CREATE_TIME_SERIES(time, measure_value::double),
        SEQUENCE(ago(1h), now(), 5m)
    ) AS interpolated_temp
FROM "iot_db"."sensor_data"
WHERE measure_name = 'temperature'
    AND time BETWEEN ago(1h) AND now()
GROUP BY device_id;

-- 이동 평균 (Moving Average)
SELECT
    device_id,
    time,
    measure_value::double AS temperature,
    AVG(measure_value::double) OVER (
        PARTITION BY device_id
        ORDER BY time
        RANGE BETWEEN INTERVAL '30' MINUTE PRECEDING AND CURRENT ROW
    ) AS moving_avg_30m
FROM "iot_db"."sensor_data"
WHERE measure_name = 'temperature'
    AND time BETWEEN ago(6h) AND now()
ORDER BY device_id, time;
```

### 다중 측정값 레코드 (Multi-Measure Records)

하나의 레코드에 여러 측정값을 포함할 수 있어 저장 효율이 높고 쿼리가 간결해집니다.

```python
import boto3
import time

client = boto3.client('timestream-write', region_name='ap-northeast-2')

# 다중 측정값 레코드 쓰기
record = {
    'Dimensions': [
        {'Name': 'device_id', 'Value': 'sensor-001'},
        {'Name': 'region', 'Value': 'ap-northeast-2'}
    ],
    'MeasureName': 'environment',
    'MeasureValueType': 'MULTI',
    'MeasureValues': [
        {'Name': 'temperature', 'Value': '23.5', 'Type': 'DOUBLE'},
        {'Name': 'humidity', 'Value': '65.2', 'Type': 'DOUBLE'},
        {'Name': 'pressure', 'Value': '1013.25', 'Type': 'DOUBLE'},
        {'Name': 'battery_level', 'Value': '87', 'Type': 'BIGINT'}
    ],
    'Time': str(int(time.time() * 1000)),
    'TimeUnit': 'MILLISECONDS'
}

client.write_records(
    DatabaseName='iot_db',
    TableName='sensor_data',
    Records=[record]
)
```

## 아키텍처/동작 원리

### 데이터 수집 아키텍처

Timestream으로 데이터를 수집하는 주요 경로는 다음과 같습니다.

1. **직접 쓰기**: AWS SDK를 통해 애플리케이션에서 직접 WriteRecords API를 호출합니다.
2. **AWS IoT Core 룰**: IoT Core에서 수신한 MQTT 메시지를 규칙 엔진을 통해 Timestream으로 라우팅합니다.
3. **Amazon Kinesis Data Streams**: Kinesis에서 Lambda를 통해 Timestream으로 변환/적재합니다.
4. **Telegraf 플러그인**: Telegraf의 Timestream 출력 플러그인을 사용하여 인프라 메트릭을 수집합니다.
5. **Amazon MSK/Kafka Connect**: Kafka Connect의 Timestream Sink Connector를 활용합니다.

### 쿼리 처리 엔진

Timestream의 쿼리 엔진은 다음과 같은 최적화를 수행합니다.

1. **적응형 쿼리 처리**: 쿼리의 시간 범위에 따라 메모리 스토어, 마그네틱 스토어, 또는 양쪽 모두에서 데이터를 읽습니다.
2. **파티션 프루닝**: 시간 기반 파티셔닝을 활용하여 불필요한 데이터 스캔을 제거합니다.
3. **디멘전 인덱싱**: 디멘전 컬럼에 자동으로 인덱스를 생성하여 필터링 성능을 향상시킵니다.
4. **컬럼형 스토리지**: 마그네틱 스토어는 컬럼형으로 데이터를 저장하여 분석 쿼리 성능을 최적화합니다.

### 자동 스케일링

Timestream은 완전한 서버리스 아키텍처를 채택하고 있습니다.

- **쓰기 처리량**: 초당 수백만 건의 쓰기를 자동으로 처리합니다.
- **쿼리 처리량**: 동시 쿼리 수에 따라 컴퓨팅 리소스가 자동으로 확장됩니다.
- **스토리지**: 데이터 양에 따라 스토리지가 자동으로 확장되며 상한이 없습니다.

## 실전 활용

### IoT 센서 모니터링 시스템 구축

```python
import boto3
import json

# Timestream 데이터베이스 및 테이블 생성
write_client = boto3.client('timestream-write', region_name='ap-northeast-2')

# 데이터베이스 생성
write_client.create_database(
    DatabaseName='iot_monitoring'
)

# 테이블 생성 (메모리 24시간, 마그네틱 365일 보존)
write_client.create_table(
    DatabaseName='iot_monitoring',
    TableName='device_metrics',
    RetentionProperties={
        'MemoryStoreRetentionPeriodInHours': 24,
        'MagneticStoreRetentionPeriodInDays': 365
    },
    MagneticStoreWriteProperties={
        'EnableMagneticStoreWrites': True
    }
)
```

### 이상 탐지 쿼리

```sql
-- 표준편차 기반 이상치 탐지
WITH stats AS (
    SELECT
        device_id,
        AVG(measure_value::double) AS avg_temp,
        STDDEV(measure_value::double) AS std_temp
    FROM "iot_monitoring"."device_metrics"
    WHERE measure_name = 'temperature'
        AND time BETWEEN ago(7d) AND now()
    GROUP BY device_id
)
SELECT
    d.device_id,
    d.time,
    d.measure_value::double AS temperature,
    s.avg_temp,
    s.std_temp,
    ABS(d.measure_value::double - s.avg_temp) / s.std_temp AS z_score
FROM "iot_monitoring"."device_metrics" d
JOIN stats s ON d.device_id = s.device_id
WHERE d.measure_name = 'temperature'
    AND d.time BETWEEN ago(1h) AND now()
    AND ABS(d.measure_value::double - s.avg_temp) / s.std_temp > 3
ORDER BY z_score DESC;

-- 시간대별 패턴 비교 (전주 동시간대 대비)
SELECT
    device_id,
    bin(time, 1h) AS hour_bucket,
    AVG(measure_value::double) AS current_avg,
    LAG(AVG(measure_value::double), 168) OVER (
        PARTITION BY device_id ORDER BY bin(time, 1h)
    ) AS last_week_avg
FROM "iot_monitoring"."device_metrics"
WHERE measure_name = 'temperature'
    AND time BETWEEN ago(8d) AND now()
GROUP BY device_id, bin(time, 1h)
ORDER BY device_id, hour_bucket DESC
LIMIT 48;
```

### DevOps 메트릭 분석

```sql
-- 서비스별 응답 시간 백분위수 분석
SELECT
    service_name,
    bin(time, 5m) AS time_bucket,
    APPROX_PERCENTILE(measure_value::double, 0.50) AS p50_latency,
    APPROX_PERCENTILE(measure_value::double, 0.95) AS p95_latency,
    APPROX_PERCENTILE(measure_value::double, 0.99) AS p99_latency,
    COUNT(*) AS request_count
FROM "devops_db"."service_metrics"
WHERE measure_name = 'response_time_ms'
    AND time BETWEEN ago(1h) AND now()
GROUP BY service_name, bin(time, 5m)
ORDER BY service_name, time_bucket;
```

### AWS CLI를 활용한 Timestream 운영

```bash
# 데이터베이스 목록 조회
aws timestream-write describe-endpoints
aws timestream-write list-databases

# 데이터베이스 생성
aws timestream-write create-database --database-name iot_monitoring

# 테이블 생성 (메모리 24시간, 마그네틱 365일)
aws timestream-write create-table \
    --database-name iot_monitoring \
    --table-name device_metrics \
    --retention-properties \
        MemoryStoreRetentionPeriodInHours=24,MagneticStoreRetentionPeriodInDays=365

# 테이블 정보 조회
aws timestream-write describe-table \
    --database-name iot_monitoring \
    --table-name device_metrics

# Timestream 쿼리 실행
aws timestream-query query \
    --query-string "SELECT device_id, time, measure_value::double AS temperature FROM \"iot_monitoring\".\"device_metrics\" WHERE measure_name = 'temperature' AND time > ago(1h) ORDER BY time DESC LIMIT 10"

# 보존 기간 업데이트
aws timestream-write update-table \
    --database-name iot_monitoring \
    --table-name device_metrics \
    --retention-properties \
        MemoryStoreRetentionPeriodInHours=48,MagneticStoreRetentionPeriodInDays=730

# 예약된 쿼리 생성 (정기적 집계)
aws timestream-query create-scheduled-query \
    --name daily-aggregation \
    --query-string "SELECT device_id, bin(time, 1h) AS hour, AVG(measure_value::double) AS avg_temp FROM \"iot_monitoring\".\"device_metrics\" WHERE measure_name = 'temperature' AND time BETWEEN ago(1d) AND now() GROUP BY device_id, bin(time, 1h)" \
    --schedule-configuration '{"ScheduleExpression": "cron(0 0 * * ? *)"}' \
    --notification-configuration '{"SnsTopicArn": "arn:aws:sns:ap-northeast-2:123456789012:timestream-alerts"}' \
    --target-configuration '{"TimestreamConfiguration": {"DatabaseName": "iot_monitoring", "TableName": "hourly_aggregates", "TimeColumn": "hour", "DimensionMappings": [{"Name": "device_id", "DimensionValueType": "VARCHAR"}], "MixedMeasureMappings": [{"MeasureName": "avg_temp", "MeasureValueType": "DOUBLE", "SourceColumn": "avg_temp"}]}}' \
    --scheduled-query-execution-role-arn arn:aws:iam::123456789012:role/TimestreamScheduledQueryRole
```

### Grafana 연동

Timestream은 Grafana와 네이티브로 통합됩니다. Amazon Managed Grafana 또는 자체 호스팅 Grafana에서 Timestream 데이터 소스를 추가하여 실시간 대시보드를 구성할 수 있습니다.

```json
{
    "datasource": {
        "type": "grafana-timestream-datasource",
        "access": "proxy",
        "jsonData": {
            "authType": "default",
            "defaultRegion": "ap-northeast-2",
            "defaultDatabase": "iot_monitoring",
            "defaultTable": "device_metrics"
        }
    }
}
```

## 모범 사례/보안

### 데이터 모델링 모범 사례

1. **디멘전을 신중히 선택합니다.** 디멘전은 인덱싱되므로 쿼리 필터에 자주 사용되는 속성만 디멘전으로 정의합니다. 카디널리티가 매우 높은 값(예: UUID)은 디멘전으로 적합하지 않습니다.

2. **다중 측정값 레코드를 활용합니다.** 동일 시점에 여러 측정값이 발생하는 경우 Multi-Measure Records를 사용하면 저장 비용을 약 80% 절감할 수 있습니다.

3. **적절한 보존 기간을 설정합니다.** 메모리 스토어는 비용이 높으므로 최소한의 기간(예: 1~24시간)만 유지하고, 장기 데이터는 마그네틱 스토어에 보관합니다.

4. **배치 쓰기를 활용합니다.** WriteRecords API 호출 시 최대 100개의 레코드를 배치로 전송하여 API 호출 비용을 줄입니다.

### 보안 모범 사례

1. **VPC 엔드포인트를 구성합니다.** Timestream에 대한 접근이 퍼블릭 인터넷을 경유하지 않도록 인터페이스 VPC 엔드포인트를 설정합니다.

2. **최소 권한 IAM 정책을 적용합니다.**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "timestream:WriteRecords",
                "timestream:DescribeEndpoints"
            ],
            "Resource": "arn:aws:timestream:ap-northeast-2:123456789012:database/iot_monitoring/table/device_metrics"
        }
    ]
}
```

3. **저장 데이터 암호화를 확인합니다.** Timestream은 기본적으로 AWS 관리형 키로 데이터를 암호화합니다. 고객 관리형 KMS 키(CMK)를 사용하여 추가적인 제어가 가능합니다.

4. **CloudTrail 로깅을 활성화합니다.** Timestream API 호출을 CloudTrail로 기록하여 감사 추적을 유지합니다.

## 관련 서비스 비교

### Timestream vs InfluxDB (자체 호스팅)

| 항목 | Amazon Timestream | InfluxDB (자체 호스팅) |
|------|-------------------|----------------------|
| 운영 모델 | 완전관리형 서버리스 | 자체 운영 필요 |
| 스케일링 | 자동 | 수동 (클러스터링) |
| 쿼리 언어 | SQL 호환 | InfluxQL / Flux |
| 데이터 계층화 | 자동 (메모리/마그네틱) | 수동 구성 필요 |
| 고가용성 | 자동 (3AZ 복제) | 수동 구성 필요 |
| 비용 모델 | 사용량 기반 | 인스턴스 비용 + 운영 비용 |

### Timestream vs CloudWatch Metrics

| 항목 | Amazon Timestream | CloudWatch Metrics |
|------|-------------------|-----------|
| 데이터 유형 | 범용 시계열 | AWS 리소스 메트릭 |
| 쿼리 유연성 | SQL 기반 (높음) | 제한적 |
| 커스텀 데이터 | 완전 지원 | PutMetricData 제한 |
| 보존 기간 | 무제한 설정 가능 | 최대 15개월 |
| 비용 | 사용량 기반 | 커스텀 메트릭 과금 |
| 적합 사용 사례 | 대규모 IoT/분석 | AWS 인프라 모니터링 |

### Timestream vs DynamoDB (시계열 패턴)

| 항목 | Amazon Timestream | DynamoDB |
|------|-------------------|-----------|
| 시계열 함수 | 풍부 (보간, 집계 등) | 없음 |
| 데이터 계층화 | 자동 | 수동 (TTL + S3) |
| 분석 쿼리 | 강력함 | 제한적 (Scan 기반) |
| 쓰기 성능 | 높음 | 매우 높음 |
| 적합 사용 사례 | 시계열 분석 | 범용 NoSQL |

## 요약

Amazon Timestream은 시계열 데이터를 위한 목적별 서버리스 데이터베이스입니다. 메모리 스토어와 마그네틱 스토어의 계층형 아키텍처로 비용과 성능을 자동 최적화하며, 시계열 전용 함수(보간, 시간 기반 집계, 이동 평균 등)를 통해 복잡한 시계열 분석을 SQL로 수행할 수 있습니다.

IoT 센서 모니터링, DevOps 메트릭 분석, 애플리케이션 성능 관리 등 대규모 시계열 워크로드에 적합하며, 서버리스 특성으로 인프라 관리 없이 자동으로 스케일링됩니다. Grafana, Amazon QuickSight 등 다양한 시각화 도구와 네이티브로 통합되어 실시간 대시보드 구축이 용이합니다.

디멘전 설계, 다중 측정값 레코드 활용, 적절한 보존 기간 설정이 Timestream 운영의 핵심이며, VPC 엔드포인트와 최소 권한 IAM 정책으로 보안을 강화해야 합니다.