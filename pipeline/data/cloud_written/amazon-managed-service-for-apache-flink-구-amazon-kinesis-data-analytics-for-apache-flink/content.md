<!-- infographic-hero -->
![Amazon Managed Service for Apache Flink 핵심 요약](figures/infographic.svg)

*Figure: Amazon Managed Service for Apache Flink 한 장 요약 인포그래픽*

# Amazon Managed Service for Apache Flink (구 Amazon Kinesis Data Analytics for Apache Flink)

## 개요

Amazon Managed Service for Apache Flink는 Apache Flink 애플리케이션을 완전 관리형으로 실행할 수 있는 AWS 서비스입니다. 이전에는 Amazon Kinesis Data Analytics for Apache Flink라는 이름으로 제공되었으며, 2023년 하반기에 현재의 이름으로 변경되었습니다.

Apache Flink는 분산 스트림 처리 프레임워크로, 실시간 데이터 스트림과 배치 데이터를 통합된 방식으로 처리할 수 있습니다. AWS는 이 오픈소스 프레임워크를 관리형 서비스로 제공함으로써, 사용자가 인프라 관리 없이 스트림 처리 로직에만 집중할 수 있도록 합니다.

이 서비스의 핵심 가치는 다음과 같습니다.

- **인프라 관리 불필요**: 클러스터 프로비저닝, 구성, 패치 적용을 AWS가 자동으로 처리합니다.
- **자동 스케일링**: 입력 데이터의 처리량에 따라 자동으로 리소스를 조절합니다.
- **내결함성**: 체크포인트 및 스냅샷을 통해 애플리케이션 상태를 안정적으로 유지합니다.
- **통합 생태계**: Kinesis Data Streams, Amazon MSK, Amazon S3 등 다양한 AWS 서비스와 네이티브 통합됩니다.

기존에 Kinesis Data Analytics for SQL이라는 SQL 기반의 간단한 분석 서비스도 존재했지만, Apache Flink 기반의 서비스는 훨씬 더 복잡하고 강력한 스트림 처리 파이프라인을 구축할 수 있습니다.

## 핵심 기능

### 1. Apache Flink 런타임 완전 관리

AWS는 Apache Flink 1.15, 1.18, 1.19 등 다양한 버전의 런타임을 지원합니다. 사용자는 Java, Scala, Python(PyFlink)으로 Flink 애플리케이션을 작성하고, JAR 파일 또는 ZIP 아카이브 형태로 업로드하면 됩니다.

```bash
# Flink 애플리케이션 생성
aws kinesisanalyticsv2 create-application \
  --application-name my-flink-app \
  --runtime-environment FLINK-1_19 \
  --service-execution-role arn:aws:iam::123456789012:role/MyFlinkRole \
  --application-configuration '{
    "FlinkApplicationConfiguration": {
      "CheckpointConfiguration": {
        "ConfigurationType": "CUSTOM",
        "CheckpointingEnabled": true,
        "CheckpointInterval": 60000,
        "MinPauseBetweenCheckpoints": 5000
      },
      "ParallelismConfiguration": {
        "ConfigurationType": "CUSTOM",
        "Parallelism": 4,
        "ParallelismPerKPU": 1,
        "AutoScalingEnabled": true
      }
    },
    "ApplicationCodeConfiguration": {
      "CodeContent": {
        "S3ContentLocation": {
          "BucketARN": "arn:aws:s3:::my-flink-bucket",
          "FileKey": "flink-app.jar"
        }
      },
      "CodeContentType": "ZIPFILE"
    }
  }'
```

### 2. 자동 스케일링 (Auto Scaling)

KPU(Kinesis Processing Unit)를 단위로 리소스를 할당하며, 각 KPU는 1 vCPU와 4GB 메모리를 제공합니다. 자동 스케일링을 활성화하면 입력 데이터량의 변화에 따라 KPU 수를 자동으로 조절합니다.

```bash
# 애플리케이션의 병렬 처리 설정 업데이트
aws kinesisanalyticsv2 update-application \
  --application-name my-flink-app \
  --current-application-version-id 1 \
  --application-configuration-update '{
    "FlinkApplicationConfigurationUpdate": {
      "ParallelismConfigurationUpdate": {
        "ConfigurationTypeUpdate": "CUSTOM",
        "ParallelismUpdate": 8,
        "ParallelismPerKPUUpdate": 1,
        "AutoScalingEnabledUpdate": true
      }
    }
  }'
```

### 3. 체크포인트 및 스냅샷

Flink의 체크포인트 메커니즘을 통해 애플리케이션 상태를 주기적으로 저장합니다. 장애 발생 시 마지막 체크포인트에서 자동으로 복구되며, 스냅샷을 통해 특정 시점의 상태를 수동으로 저장할 수도 있습니다.

```bash
# 애플리케이션 스냅샷 생성
aws kinesisanalyticsv2 create-application-snapshot \
  --application-name my-flink-app \
  --snapshot-name my-snapshot-2024-01

# 스냅샷 목록 조회
aws kinesisanalyticsv2 list-application-snapshots \
  --application-name my-flink-app
```

### 4. Apache Flink Studio (Zeppelin 노트북)

Apache Zeppelin 기반의 대화형 노트북 환경을 제공하여, SQL, Python, Scala를 사용한 실시간 데이터 탐색 및 프로토타이핑이 가능합니다. 개발자가 복잡한 스트림 처리 로직을 빠르게 테스트하고 반복할 수 있는 환경을 제공합니다.

### 5. VPC 연결

프라이빗 서브넷의 리소스(Amazon RDS, Amazon ElastiCache, Amazon Redshift 등)에 접근해야 하는 경우, VPC 구성을 통해 안전하게 연결할 수 있습니다.

```bash
# VPC 구성이 포함된 애플리케이션 생성
aws kinesisanalyticsv2 create-application \
  --application-name my-flink-vpc-app \
  --runtime-environment FLINK-1_19 \
  --service-execution-role arn:aws:iam::123456789012:role/MyFlinkRole \
  --application-configuration '{
    "VpcConfigurations": [{
      "SubnetIds": ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"],
      "SecurityGroupIds": ["sg-0123456789abcdef0"]
    }],
    "ApplicationCodeConfiguration": {
      "CodeContent": {
        "S3ContentLocation": {
          "BucketARN": "arn:aws:s3:::my-flink-bucket",
          "FileKey": "flink-vpc-app.jar"
        }
      },
      "CodeContentType": "ZIPFILE"
    }
  }'
```

## 아키텍처/동작 원리

### 전체 아키텍처

Amazon Managed Service for Apache Flink의 아키텍처는 크게 세 부분으로 구성됩니다.

1. **소스(Source)**: 데이터가 유입되는 입력 스트림입니다. Amazon Kinesis Data Streams, Amazon MSK(Managed Streaming for Apache Kafka), Amazon S3 등이 소스로 사용될 수 있습니다.

2. **처리 엔진(Processing Engine)**: Apache Flink 런타임이 실행되는 관리형 클러스터입니다. 사용자가 작성한 Flink 애플리케이션이 이 엔진 위에서 실행됩니다.

3. **싱크(Sink)**: 처리된 데이터가 출력되는 대상입니다. Amazon S3, Amazon Kinesis Data Streams, Amazon DynamoDB, Amazon OpenSearch Service, Amazon Redshift 등 다양한 대상으로 출력할 수 있습니다.

### 내부 동작 원리

#### Task Manager와 Job Manager

Flink 애플리케이션은 내부적으로 Job Manager와 Task Manager로 구성됩니다. Job Manager는 작업 스케줄링과 체크포인트 조율을 담당하고, Task Manager는 실제 데이터 처리를 수행합니다. AWS 관리형 서비스에서는 이러한 컴포넌트의 배포와 관리가 자동으로 이루어집니다.

#### 병렬 처리 모델

Flink의 병렬 처리는 다음과 같은 계층 구조를 따릅니다.

- **Parallelism**: 전체 애플리케이션의 병렬 처리 수준을 결정합니다.
- **ParallelismPerKPU**: 각 KPU당 할당되는 병렬 작업의 수를 결정합니다.
- **실제 KPU 수**: Parallelism / ParallelismPerKPU로 계산됩니다.

예를 들어, Parallelism이 8이고 ParallelismPerKPU가 2라면, 4개의 KPU가 할당됩니다.

#### 체크포인트 메커니즘

Flink는 Chandy-Lamport 알고리즘 기반의 분산 스냅샷 메커니즘을 사용합니다. 체크포인트 배리어(Checkpoint Barrier)가 데이터 스트림을 따라 전파되면서, 각 오퍼레이터의 상태를 일관성 있게 저장합니다. AWS에서는 이 체크포인트 데이터를 내부 스토리지에 안전하게 보관합니다.

#### Exactly-Once 처리 보장

Flink는 체크포인트와 Two-Phase Commit 프로토콜을 결합하여 end-to-end exactly-once 처리를 지원합니다. 이는 금융 거래 처리나 정확한 집계가 필요한 시나리오에서 매우 중요한 기능입니다.

### 데이터 흐름 예시

```
Kinesis Data Stream --> [Source Operator] --> [Map/Filter] --> [Window Aggregation] --> [Sink Operator] --> S3/DynamoDB
                                                                    |
                                                            체크포인트 저장
```

## 실전 활용

### 활용 사례 1: 실시간 클릭스트림 분석

웹사이트의 클릭 이벤트를 실시간으로 분석하여 사용자 행동 패턴을 파악하는 파이프라인을 구축할 수 있습니다.

```java
// Flink 애플리케이션 예시 (Java)
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.streaming.api.windowing.time.Time;
import org.apache.flink.streaming.connectors.kinesis.FlinkKinesisConsumer;
import org.apache.flink.streaming.connectors.kinesis.FlinkKinesisProducer;

public class ClickstreamAnalyzer {
    public static void main(String[] args) throws Exception {
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        
        // Kinesis Data Stream에서 클릭 이벤트 읽기
        Properties consumerConfig = new Properties();
        consumerConfig.setProperty("aws.region", "ap-northeast-2");
        consumerConfig.setProperty("stream.initial.position", "LATEST");
        
        FlinkKinesisConsumer<String> consumer = new FlinkKinesisConsumer<>(
            "clickstream-input",
            new SimpleStringSchema(),
            consumerConfig
        );
        
        env.addSource(consumer)
            .map(event -> parseClickEvent(event))
            .keyBy(event -> event.getUserId())
            .window(Time.minutes(5))
            .aggregate(new ClickCountAggregator())
            .addSink(createS3Sink());
        
        env.execute("Clickstream Analyzer");
    }
}
```

### 활용 사례 2: IoT 센서 데이터 이상 탐지

IoT 장치에서 전송되는 센서 데이터를 실시간으로 모니터링하고, 이상 패턴을 감지하여 알림을 보내는 시스템을 구현할 수 있습니다.

```python
# PyFlink 예시
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.common.time import Time

def anomaly_detection():
    env = StreamExecutionEnvironment.get_execution_environment()
    
    # Kinesis Source 설정
    kinesis_source = KinesisSource.builder() \
        .set_stream_name("iot-sensor-stream") \
        .set_aws_region("ap-northeast-2") \
        .set_starting_position(StartingPosition.latest()) \
        .set_deserialization_schema(SimpleStringSchema()) \
        .build()
    
    ds = env.from_source(
        kinesis_source,
        WatermarkStrategy.no_watermarks(),
        "Kinesis Source"
    )
    
    # 5분 윈도우 기준 이상 탐지
    ds.key_by(lambda x: x["device_id"]) \
      .window(TumblingProcessingTimeWindows.of(Time.minutes(5))) \
      .process(AnomalyDetector()) \
      .add_sink(sns_sink)
    
    env.execute("IoT Anomaly Detection")
```

### 활용 사례 3: 실시간 ETL 파이프라인

여러 소스에서 유입되는 데이터를 실시간으로 변환하고 데이터 레이크에 적재하는 ETL 파이프라인입니다.

```bash
# 애플리케이션 시작
aws kinesisanalyticsv2 start-application \
  --application-name real-time-etl \
  --run-configuration '{
    "FlinkRunConfiguration": {
      "AllowNonRestoredState": false
    },
    "ApplicationRestoreConfiguration": {
      "ApplicationRestoreType": "RESTORE_FROM_LATEST_SNAPSHOT"
    }
  }'

# 애플리케이션 상태 확인
aws kinesisanalyticsv2 describe-application \
  --application-name real-time-etl \
  --query 'ApplicationDetail.{Status:ApplicationStatus,Version:ApplicationVersionId,LastUpdate:LastUpdateTimestamp}'
```

### 활용 사례 4: Flink SQL을 활용한 스트림 처리

Flink Studio에서 SQL을 사용하여 간단한 스트림 처리를 수행할 수 있습니다.

```sql
-- 실시간 주문 집계
CREATE TABLE orders (
    order_id STRING,
    product_id STRING,
    amount DECIMAL(10, 2),
    order_time TIMESTAMP(3),
    WATERMARK FOR order_time AS order_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kinesis',
    'stream' = 'orders-stream',
    'aws.region' = 'ap-northeast-2',
    'format' = 'json'
);

CREATE TABLE hourly_sales (
    window_start TIMESTAMP(3),
    window_end TIMESTAMP(3),
    product_id STRING,
    total_amount DECIMAL(10, 2),
    order_count BIGINT
) WITH (
    'connector' = 's3',
    'path' = 's3://my-analytics-bucket/hourly-sales/',
    'format' = 'parquet'
);

INSERT INTO hourly_sales
SELECT 
    window_start,
    window_end,
    product_id,
    SUM(amount) AS total_amount,
    COUNT(*) AS order_count
FROM TABLE(
    TUMBLE(TABLE orders, DESCRIPTOR(order_time), INTERVAL '1' HOUR)
)
GROUP BY window_start, window_end, product_id;
```

## 모범 사례/보안

### 보안 모범 사례

1. **IAM 최소 권한 원칙**: 애플리케이션의 실행 역할에는 필요한 최소한의 권한만 부여합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:GetRecords",
        "kinesis:GetShardIterator",
        "kinesis:DescribeStream",
        "kinesis:ListShards"
      ],
      "Resource": "arn:aws:kinesis:ap-northeast-2:123456789012:stream/my-input-stream"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::my-output-bucket/*"
    }
  ]
}
```

2. **VPC 내 배포**: 프라이빗 리소스에 접근해야 하는 경우 반드시 VPC 구성을 사용합니다.
3. **전송 중 암호화**: Kinesis Data Streams, MSK 등과의 통신에서 TLS 암호화를 활성화합니다.
4. **CloudWatch 모니터링**: 애플리케이션 메트릭을 CloudWatch로 전송하여 실시간 모니터링 체계를 구축합니다.

### 운영 모범 사례

1. **체크포인트 간격 최적화**: 체크포인트 간격이 너무 짧으면 성능이 저하되고, 너무 길면 장애 복구 시 데이터 재처리량이 증가합니다. 일반적으로 30초~5분 사이의 값을 권장합니다.

2. **스냅샷 관리**: 애플리케이션 업데이트 전에 반드시 스냅샷을 생성하고, 롤백 계획을 수립합니다.

3. **로그 레벨 관리**: 프로덕션 환경에서는 WARN 이상의 로그 레벨을 사용하여 CloudWatch Logs 비용을 절감합니다.

```bash
# CloudWatch 로그 모니터링 설정
aws kinesisanalyticsv2 add-application-cloud-watch-logging-option \
  --application-name my-flink-app \
  --current-application-version-id 1 \
  --cloud-watch-logging-option '{"LogStreamARN": "arn:aws:logs:ap-northeast-2:123456789012:log-group:/aws/kinesis-analytics/my-flink-app:log-stream:kinesis-analytics-log-stream"}'
```

4. **Parallelism 설정**: 입력 소스의 파티션/샤드 수에 맞춰 Parallelism을 설정하면 최적의 성능을 얻을 수 있습니다.

5. **메모리 관리**: Flink의 State Backend 설정을 통해 대규모 상태 관리 시 메모리 사용을 최적화합니다. RocksDB State Backend를 사용하면 디스크 기반 상태 관리가 가능합니다.

## 관련 서비스 비교

| 항목 | Managed Apache Flink | Amazon EMR (Flink) | Amazon Kinesis Data Streams | AWS Lambda |
|------|---------------------|--------------------|-----------------------------|------------|
| 관리 수준 | 완전 관리형 | 반관리형 | 완전 관리형 | 완전 관리형 |
| 처리 방식 | 스트림/배치 | 스트림/배치 | 스트림 수집 | 이벤트 기반 |
| 상태 관리 | 지원 (Stateful) | 지원 (Stateful) | 미지원 | 미지원 |
| 처리 보장 | Exactly-Once | Exactly-Once | At-Least-Once | At-Least-Once |
| 복잡도 | 중간 | 높음 | 낮음 | 낮음 |
| 지연 시간 | 밀리초 단위 | 밀리초 단위 | 밀리초 단위 | 초 단위 |
| 적합한 용도 | 복잡한 스트림 처리 | 대규모 데이터 처리 | 데이터 수집/전달 | 간단한 이벤트 처리 |

### 선택 기준

- **Managed Apache Flink**: 복잡한 윈도우 연산, 상태 기반 처리, exactly-once 보장이 필요한 경우에 적합합니다.
- **Amazon EMR (Flink)**: Flink 설정을 세밀하게 제어하거나, Flink 외에 Spark 등 다른 프레임워크도 함께 사용해야 하는 경우에 적합합니다.
- **Kinesis Data Streams + Lambda**: 간단한 변환이나 필터링 작업에는 Lambda를 사용하는 것이 더 경제적이고 간편합니다.
- **Amazon MSK + Flink**: Kafka 생태계를 이미 사용 중이라면 MSK를 소스로, Managed Flink를 처리 엔진으로 사용하는 조합이 효과적입니다.

## 요약

Amazon Managed Service for Apache Flink는 실시간 스트림 처리를 위한 강력하고 완전 관리형인 서비스입니다. Apache Flink의 강력한 스트림 처리 능력을 AWS의 관리형 인프라와 결합하여, 개발자가 인프라 관리 부담 없이 비즈니스 로직에 집중할 수 있도록 합니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **완전 관리형**: 클러스터 관리, 패치 적용, 장애 복구가 자동으로 이루어집니다.
- **자동 스케일링**: KPU 단위의 자동 스케일링으로 비용 효율적인 운영이 가능합니다.
- **Exactly-Once 보장**: 체크포인트 메커니즘을 통해 정확한 데이터 처리를 보장합니다.
- **다양한 통합**: Kinesis, MSK, S3, DynamoDB 등 AWS 서비스와 네이티브 통합됩니다.
- **Flink Studio**: Zeppelin 노트북 기반의 대화형 개발 환경을 제공합니다.
- **VPC 지원**: 프라이빗 네트워크 리소스에 안전하게 접근할 수 있습니다.

실시간 데이터 처리 파이프라인을 구축해야 하는 경우, 특히 복잡한 이벤트 처리, 윈도우 기반 집계, 상태 기반 처리가 필요한 시나리오에서 이 서비스를 적극적으로 고려하시기 바랍니다.