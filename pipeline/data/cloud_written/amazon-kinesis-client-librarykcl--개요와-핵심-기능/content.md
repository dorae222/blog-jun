<!-- infographic-hero -->
![Amazon Kinesis Client Library(KCL) -- 개요와 핵심 기능 핵심 요약](figures/infographic.svg)

*Figure: Amazon Kinesis Client Library(KCL) -- 개요와 핵심 기능 한 장 요약 인포그래픽*

# Amazon Kinesis Client Library(KCL) -- 개요와 핵심 기능

## 개요

Amazon Kinesis Client Library(KCL)는 Kinesis Data Streams에서 데이터를 소비(consume)하기 위한 클라이언트 라이브러리입니다. KCL은 단순히 데이터를 읽어오는 것을 넘어, 분산 환경에서의 샤드 할당, 체크포인팅, 장애 복구, 로드 밸런싱 등 복잡한 문제를 자동으로 처리해 줍니다.

Kinesis Data Streams에서 데이터를 읽는 가장 기본적인 방법은 AWS SDK의 GetRecords API를 사용하는 것입니다. 하지만 프로덕션 환경에서는 여러 샤드에서 동시에 데이터를 읽고, 여러 워커 인스턴스 간에 샤드를 분배하고, 처리 상태를 기록하고, 장애 발생 시 자동으로 복구해야 합니다. KCL은 이러한 복잡한 로직을 추상화하여, 개발자가 비즈니스 로직에만 집중할 수 있게 합니다.

### KCL 버전

- **KCL 1.x**: 초기 버전. DynamoDB를 리스 테이블로 사용. Java만 직접 지원하며, 다른 언어는 MultiLangDaemon을 통해 지원합니다.
- **KCL 2.x**: Enhanced Fan-Out 지원, Graceful shutdown, 개선된 리스 관리. Java, Python, .NET 등을 직접 지원합니다.

현재 2.x 버전 사용이 권장되며, 이 글에서는 주로 KCL 2.x를 기준으로 설명합니다.

## 핵심 기능

### 샤드 리스 관리 (Lease Management)

KCL의 가장 핵심적인 기능은 샤드 리스 관리입니다. KCL은 DynamoDB 테이블을 사용하여 어떤 워커가 어떤 샤드를 처리하고 있는지를 추적합니다.

- **리스(Lease)**: 특정 샤드에 대한 소유권을 나타내는 DynamoDB 레코드입니다.
- **리스 획득**: 워커가 시작하면 사용 가능한 샤드의 리스를 획득합니다.
- **리스 갱신**: 리스를 보유한 워커는 주기적으로 리스를 갱신(heartbeat)하여 소유권을 유지합니다.
- **리스 탈취(Stealing)**: 워커 간 샤드 불균형이 감지되면, 리스가 적은 워커가 리스가 많은 워커로부터 리스를 탈취합니다.

### 체크포인팅 (Checkpointing)

체크포인팅은 각 샤드에서 마지막으로 성공적으로 처리한 레코드의 시퀀스 번호를 DynamoDB에 기록하는 메커니즘입니다.

- 워커가 재시작되거나 장애 복구 시, 마지막 체크포인트 위치부터 처리를 재개합니다.
- 개발자가 명시적으로 체크포인트를 호출해야 합니다 (자동 체크포인팅 아님).
- 체크포인트 빈도는 정확성(exactly-once에 가까운 처리)과 성능(DynamoDB 쓰기 비용) 간의 트레이드오프입니다.

### 로드 밸런싱

KCL은 여러 워커 인스턴스 간에 샤드를 자동으로 분배합니다. 예를 들어 4개의 샤드가 있고 2개의 워커가 실행 중이면, 각 워커가 2개의 샤드를 처리합니다. 워커가 추가되거나 제거되면 자동으로 리밸런싱됩니다.

### 장애 복구

워커가 비정상적으로 종료되면, 해당 워커의 리스 갱신이 중단됩니다. 일정 시간(리스 타임아웃) 후 다른 워커가 해당 리스를 인계받아 처리를 계속합니다.

### Enhanced Fan-Out 지원 (KCL 2.x)

KCL 2.x는 Enhanced Fan-Out(EFO)을 지원합니다. EFO를 사용하면 각 소비자가 샤드당 전용 2MB/s 처리량을 보장받습니다. HTTP/2 기반 SubscribeToShard API를 사용하여 푸시 방식으로 데이터를 수신합니다.

### Graceful Shutdown (KCL 2.x)

KCL 2.x는 애플리케이션 종료 시 진행 중인 레코드 처리를 완료하고, 최종 체크포인트를 기록한 후 안전하게 종료하는 Graceful Shutdown을 지원합니다.

## 아키텍처/동작 원리

### 전체 아키텍처

```
[Kinesis Data Stream]
  +-- Shard-0 ----+
  +-- Shard-1 -+  |
  +-- Shard-2 -+  |
  +-- Shard-3 -+--+
               |  |
               v  v
[KCL Worker A]  [KCL Worker B]
  Shard-0,1      Shard-2,3
     |              |
     v              v
[DynamoDB Lease Table]
  Shard-0: Worker-A, seq=12345, checkpoint=12340
  Shard-1: Worker-A, seq=23456, checkpoint=23450
  Shard-2: Worker-B, seq=34567, checkpoint=34560
  Shard-3: Worker-B, seq=45678, checkpoint=45670
```

### KCL 내부 컴포넌트

**1. Scheduler (구 Worker)**: KCL 애플리케이션의 최상위 컴포넌트입니다. 리스 관리, 샤드 탐지, RecordProcessor 할당을 조율합니다.

**2. LeaseCoordinator**: DynamoDB 리스 테이블과 상호작용하여 리스 획득, 갱신, 탈취를 수행합니다.

**3. ShardDetector**: Kinesis Data Stream의 샤드 변경(리샤딩)을 감지합니다.

**4. RecordProcessor**: 개발자가 구현하는 인터페이스로, 실제 레코드 처리 로직이 들어갑니다.

**5. RecordProcessorFactory**: 새로운 샤드가 할당될 때 RecordProcessor 인스턴스를 생성합니다.

### 리스 테이블 구조

DynamoDB 리스 테이블의 주요 속성은 다음과 같습니다.

| 속성 | 설명 |
|------|------|
| leaseKey | 샤드 ID (파티션 키) |
| leaseOwner | 현재 리스를 보유한 워커 ID |
| leaseCounter | 리스 갱신 카운터 (낙관적 잠금에 사용) |
| checkpoint | 마지막 체크포인트 시퀀스 번호 |
| parentShardId | 리샤딩 시 부모 샤드 ID |

### 리스 획득 및 갱신 프로세스

1. 워커 시작 시 DynamoDB 리스 테이블을 스캔합니다.
2. 소유자가 없거나 만료된 리스를 발견하면 조건부 쓰기(Conditional Write)로 리스를 획득합니다.
3. 리스를 보유한 워커는 leaseRenewalIntervalMillis(기본 10초) 간격으로 리스를 갱신합니다.
4. 리스 갱신 시 leaseCounter를 증가시키고, 이전 카운터 값을 조건으로 사용하여 충돌을 방지합니다.
5. failoverTimeMillis(기본 10초) 이상 갱신되지 않은 리스는 다른 워커가 인계할 수 있습니다.

### 리샤딩 처리

Kinesis Data Stream의 샤드가 분할(split) 또는 병합(merge)되면, KCL이 자동으로 이를 감지하고 처리합니다.

- **샤드 분할**: 부모 샤드의 처리가 완료된 후, 두 자식 샤드의 처리가 시작됩니다.
- **샤드 병합**: 두 부모 샤드의 처리가 모두 완료된 후, 병합된 자식 샤드의 처리가 시작됩니다.

이 순서가 보장되어야 데이터의 순서가 유지됩니다.

## 실전 활용

### Java KCL 2.x 구현

```java
import software.amazon.kinesis.processor.ShardRecordProcessor;
import software.amazon.kinesis.processor.ShardRecordProcessorFactory;
import software.amazon.kinesis.lifecycle.events.*;
import software.amazon.kinesis.coordinator.Scheduler;
import software.amazon.kinesis.common.ConfigsBuilder;

// RecordProcessor 구현
public class MyRecordProcessor implements ShardRecordProcessor {

    private String shardId;

    @Override
    public void initialize(InitializationInput initializationInput) {
        this.shardId = initializationInput.shardId();
        System.out.println("Initialized processor for shard: " + shardId);
    }

    @Override
    public void processRecords(ProcessRecordsInput processRecordsInput) {
        processRecordsInput.records().forEach(record -> {
            String data = new String(record.data().array());
            System.out.println("Processing record: " + data);
        });

        // 체크포인트 (배치 단위로 수행)
        try {
            processRecordsInput.checkpointer().checkpoint();
        } catch (Exception e) {
            System.err.println("Checkpoint failed: " + e.getMessage());
        }
    }

    @Override
    public void leaseLost(LeaseLostInput leaseLostInput) {
        System.out.println("Lease lost for shard: " + shardId);
    }

    @Override
    public void shardEnded(ShardEndedInput shardEndedInput) {
        try {
            shardEndedInput.checkpointer().checkpoint();
        } catch (Exception e) {
            System.err.println("Shard end checkpoint failed: " + e.getMessage());
        }
    }

    @Override
    public void shutdownRequested(ShutdownRequestedInput shutdownRequestedInput) {
        try {
            shutdownRequestedInput.checkpointer().checkpoint();
        } catch (Exception e) {
            System.err.println("Shutdown checkpoint failed: " + e.getMessage());
        }
    }
}
```

### Python KCL 2.x 구현

```python
import amazon_kinesis_client as kcl
from amazon_kinesis_client.v3 import processor
import json
import logging

logger = logging.getLogger(__name__)

class MyRecordProcessor(processor.RecordProcessorBase):
    """Kinesis 레코드를 처리하는 프로세서"""

    def __init__(self):
        self.shard_id = None
        self.largest_seq = None
        self.last_checkpoint_time = 0
        self.CHECKPOINT_INTERVAL_SECONDS = 60

    def initialize(self, initialize_input):
        """샤드 프로세서 초기화"""
        self.shard_id = initialize_input.shard_id
        logger.info(f"Initialized processor for shard: {self.shard_id}")

    def process_records(self, process_records_input):
        """레코드 배치 처리"""
        import time

        for record in process_records_input.records:
            data = record.data.decode('utf-8')
            seq = record.sequence_number
            self.largest_seq = seq

            # 비즈니스 로직
            try:
                parsed = json.loads(data)
                self.handle_event(parsed)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON record: {data[:100]}")

        # 주기적 체크포인팅
        current_time = time.time()
        if current_time - self.last_checkpoint_time > self.CHECKPOINT_INTERVAL_SECONDS:
            self.checkpoint(process_records_input.checkpointer)
            self.last_checkpoint_time = current_time

    def handle_event(self, event):
        """이벤트 처리 비즈니스 로직"""
        event_type = event.get('type')
        logger.info(f"Processing event: {event_type}")

    def checkpoint(self, checkpointer):
        """체크포인트 수행"""
        try:
            checkpointer.checkpoint()
            logger.info(f"Checkpoint successful for shard: {self.shard_id}")
        except Exception as e:
            logger.error(f"Checkpoint failed: {e}")

    def lease_lost(self, lease_lost_input):
        logger.info(f"Lease lost for shard: {self.shard_id}")

    def shard_ended(self, shard_ended_input):
        shard_ended_input.checkpointer.checkpoint()
        logger.info(f"Shard ended: {self.shard_id}")

    def shutdown_requested(self, shutdown_requested_input):
        shutdown_requested_input.checkpointer.checkpoint()
        logger.info(f"Shutdown requested for shard: {self.shard_id}")
```

### AWS CLI를 통한 모니터링

```bash
# Kinesis Data Stream 상태 확인
aws kinesis describe-stream-summary \
  --stream-name my-data-stream

# 샤드 목록 조회
aws kinesis list-shards \
  --stream-name my-data-stream

# DynamoDB 리스 테이블 조회 (KCL이 생성한 테이블)
aws dynamodb scan \
  --table-name my-kcl-application \
  --select "ALL_ATTRIBUTES" \
  --output table

# 특정 샤드의 리스 정보 조회
aws dynamodb get-item \
  --table-name my-kcl-application \
  --key '{"leaseKey": {"S": "shardId-000000000000"}}'

# CloudWatch에서 KCL 메트릭 확인 - 밀리비하인드
aws cloudwatch get-metric-statistics \
  --namespace "my-kcl-application" \
  --metric-name "MillisBehindLatest" \
  --dimensions Name=Operation,Value=ProcessTask \
  --start-time "$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 300 \
  --statistics Average Maximum

# Enhanced Fan-Out Consumer 등록
aws kinesis register-stream-consumer \
  --stream-arn "arn:aws:kinesis:ap-northeast-2:123456789012:stream/my-data-stream" \
  --consumer-name "my-kcl-consumer"

# 등록된 Consumer 확인
aws kinesis list-stream-consumers \
  --stream-arn "arn:aws:kinesis:ap-northeast-2:123456789012:stream/my-data-stream"
```

### KCL 설정 최적화

```java
// KCL 2.x 설정 예시 (Java)
ConfigsBuilder configsBuilder = new ConfigsBuilder(
    streamName,
    applicationName,
    kinesisClient,
    dynamoClient,
    cloudWatchClient,
    workerId,
    new MyRecordProcessorFactory()
);

// 리스 관리 설정
configsBuilder.leaseManagementConfig()
    .failoverTimeMillis(20000)        // 리스 타임아웃: 20초
    .shardSyncIntervalMillis(60000)   // 샤드 동기화 간격: 60초
    .maxLeasesForWorker(10)           // 워커당 최대 리스 수
    .maxLeasesToStealAtOneTime(1);    // 한 번에 탈취할 최대 리스 수

// 폴링 설정
configsBuilder.retrievalConfig()
    .retrievalSpecificConfig(
        new PollingConfig(streamName, kinesisClient)
            .maxRecords(10000)               // 배치당 최대 레코드 수
            .idleTimeBetweenReadsInMillis(1000) // 폴링 간격
    );

// 체크포인트 설정
configsBuilder.checkpointConfig()
    .checkpointFactory(checkpointFactory);

Scheduler scheduler = new Scheduler(
    configsBuilder.checkpointConfig(),
    configsBuilder.coordinatorConfig(),
    configsBuilder.leaseManagementConfig(),
    configsBuilder.lifecycleConfig(),
    configsBuilder.metricsConfig(),
    configsBuilder.processorConfig(),
    configsBuilder.retrievalConfig()
);
```

## 모범 사례/보안

### 체크포인팅 모범 사례

**1. 주기적 체크포인팅**: 모든 레코드마다 체크포인트를 호출하면 DynamoDB 쓰기 비용이 급증합니다. 시간 기반(예: 60초마다) 또는 레코드 수 기반(예: 1000개마다) 체크포인팅을 권장합니다.

**2. 멱등성 보장**: 체크포인트 간격 사이의 레코드는 장애 시 재처리될 수 있으므로, 레코드 처리 로직은 멱등성(idempotency)을 보장해야 합니다.

**3. shardEnded에서 반드시 체크포인트**: 리샤딩 시 부모 샤드가 종료될 때 체크포인트를 호출하지 않으면, 자식 샤드의 처리가 시작되지 않습니다.

### 성능 최적화

**1. 워커 수 결정**: 워커 수는 샤드 수 이하로 유지합니다. 워커 수가 샤드 수를 초과하면 유휴 워커가 발생합니다.

**2. Enhanced Fan-Out 활용**: 여러 소비자 애플리케이션이 동일한 스트림을 읽는 경우, EFO를 사용하여 각 소비자에게 전용 처리량을 보장합니다.

**3. DynamoDB 프로비저닝**: 리스 테이블의 DynamoDB 용량이 부족하면 리스 관리에 지연이 발생합니다. On-Demand 모드를 사용하거나, 워커 수에 비례하여 WCU를 프로비저닝합니다.

### 보안 모범 사례

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
        "kinesis:DescribeStreamSummary",
        "kinesis:ListShards",
        "kinesis:SubscribeToShard"
      ],
      "Resource": "arn:aws:kinesis:ap-northeast-2:123456789012:stream/my-data-stream"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:SubscribeToShard",
        "kinesis:DescribeStreamConsumer"
      ],
      "Resource": "arn:aws:kinesis:ap-northeast-2:123456789012:stream/my-data-stream/consumer/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:CreateTable",
        "dynamodb:DescribeTable",
        "dynamodb:Scan",
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem"
      ],
      "Resource": "arn:aws:dynamodb:ap-northeast-2:123456789012:table/my-kcl-application"
    },
    {
      "Effect": "Allow",
      "Action": ["cloudwatch:PutMetricData"],
      "Resource": "*"
    }
  ]
}
```

### 운영 모범 사례

- **MillisBehindLatest** 메트릭을 모니터링하여 소비자가 생산자를 얼마나 따라가고 있는지 확인합니다. 이 값이 지속적으로 증가하면 소비자의 처리 용량을 늘려야 합니다.
- 리스 테이블의 DynamoDB 용량 부족 알람을 설정합니다.
- KCL 워커의 로그를 중앙 로그 시스템으로 수집하여 장애 시 진단에 활용합니다.

## 관련 서비스 비교

### KCL vs AWS SDK (GetRecords)

| 항목 | KCL | AWS SDK (GetRecords) |
|------|-----|---------------------|
| 샤드 관리 | 자동 | 수동 구현 필요 |
| 체크포인팅 | 내장 (DynamoDB) | 수동 구현 필요 |
| 로드 밸런싱 | 자동 | 수동 구현 필요 |
| 장애 복구 | 자동 | 수동 구현 필요 |
| 복잡도 | 낮음 (비즈니스 로직만) | 높음 (모든 것을 구현) |
| 유연성 | KCL 프레임워크에 종속 | 완전한 자유도 |

### KCL vs AWS Lambda (이벤트 소스 매핑)

| 항목 | KCL | Lambda |
|------|-----|--------|
| 실행 환경 | 자체 서버/컨테이너 | 서버리스 |
| 처리 시간 제한 | 없음 | 15분 |
| 상태 관리 | DynamoDB 체크포인트 | 자동 |
| 비용 모델 | 인스턴스 비용 | 호출 횟수 기반 |
| 적합한 사용 사례 | 장시간 처리, 복잡한 로직 | 간단한 변환, 짧은 처리 |

### KCL vs Kinesis Data Analytics (Apache Flink)

| 항목 | KCL | Kinesis Data Analytics |
|------|-----|----------------------|
| 처리 방식 | 마이크로배치 | 스트림 처리 |
| 윈도우 함수 | 직접 구현 | 내장 |
| SQL 지원 | 미지원 | 지원 |
| 복잡한 이벤트 처리 | 직접 구현 | Flink CEP 활용 |
| 관리 비용 | 자체 관리 | 관리형 |

## 요약

Amazon Kinesis Client Library(KCL)는 Kinesis Data Streams의 소비자 측에서 복잡한 분산 처리 문제를 해결해주는 핵심 라이브러리입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **자동 샤드 관리**: DynamoDB 리스 테이블을 통해 여러 워커 간 샤드를 자동으로 분배하고 장애 시 자동 복구합니다.
- **체크포인팅**: 처리 상태를 DynamoDB에 기록하여 장애 시 마지막 체크포인트부터 재처리합니다.
- **로드 밸런싱**: 워커 추가/제거 시 자동으로 샤드를 리밸런싱합니다.
- **Enhanced Fan-Out**: KCL 2.x에서 EFO를 지원하여 소비자별 전용 처리량을 보장합니다.
- **개발자 책임**: 비즈니스 로직(RecordProcessor)과 체크포인트 호출 시점만 결정하면 됩니다.
- **핵심 설정**: failoverTimeMillis, maxLeasesForWorker, 폴링 간격이 성능에 직접적인 영향을 미칩니다.
- **멱등성**: 체크포인트 간격 사이의 레코드 재처리에 대비하여 멱등한 처리 로직이 필수적입니다.