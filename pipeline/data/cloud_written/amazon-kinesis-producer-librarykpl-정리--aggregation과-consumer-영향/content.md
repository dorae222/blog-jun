# Amazon Kinesis Producer Library (KPL) 정리 - Aggregation과 Consumer 영향 분석

## 개요

Amazon Kinesis Producer Library(KPL)는 Kinesis Data Streams에 대량의 데이터를 효율적으로 전송하기 위한 고성능 프로듀서 라이브러리입니다. KPL의 가장 핵심적인 기능은 Aggregation과 Collection으로, 작은 레코드들을 하나의 큰 Kinesis 레코드로 묶어 전송함으로써 처리량을 극대화하고 비용을 절감합니다.

그러나 KPL의 Aggregation은 Consumer 측에서 De-aggregation을 수행해야 한다는 중요한 전제 조건이 있습니다. 이를 고려하지 않으면 데이터 손실이나 처리 오류가 발생할 수 있습니다. 이 글에서는 KPL의 동작 원리, Aggregation 메커니즘, 그리고 Consumer에 미치는 영향을 상세히 분석합니다.

## 핵심 기능

### Aggregation (집계)

Aggregation은 여러 개의 사용자 레코드(User Record)를 하나의 Kinesis 레코드(KPL Record)로 묶는 과정입니다. PUT 요청 당 과금되는 25KB 단위를 최대한 활용하여 비용을 절감합니다.

```
[User Record A: 1KB] --+
[User Record B: 2KB] --+--> [Aggregated KPL Record: 18KB] --> Kinesis Shard
[User Record C: 3KB] --+         (1 PutRecord 호출)
[User Record D: 5KB] --+
[User Record E: 4KB] --+
[User Record F: 3KB] --+
```

Aggregation 없이 개별 전송하면 6번의 PutRecord 호출이 필요하지만, Aggregation을 사용하면 1번의 호출로 처리됩니다.

### Collection (수집)

Collection은 여러 개의 Aggregated Record를 하나의 PutRecords API 호출로 묶는 과정입니다. PutRecords는 한 번에 최대 500건의 레코드를 전송할 수 있습니다.

```
[Aggregated Record 1] --+
[Aggregated Record 2] --+--> [PutRecords API 호출 1회]
[Aggregated Record 3] --+         (최대 500건)
...                      +
[Aggregated Record N] --+
```

### 두 단계의 최적화 효과

| 최적화 단계 | 목적 | 효과 |
|------------|------|------|
| Aggregation | 작은 레코드를 하나로 묶기 | PutRecord 과금 단위(25KB) 최적화 |
| Collection | 여러 레코드를 한 API 호출로 | API 호출 횟수 절감, 네트워크 효율화 |

두 단계를 결합하면, 예를 들어 1KB 레코드 10,000개를 전송할 때:
- Aggregation 없이: PutRecords 20회 (500건씩) x 25KB 과금 = 10,000 PUT 단위
- Aggregation 적용: ~400개 Aggregated Record (25KB씩) -> PutRecords 1회 = ~400 PUT 단위

약 96%의 비용 절감 효과를 얻을 수 있습니다.

### KPL 주요 설정 파라미터

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| AggregationEnabled | true | Aggregation 활성화 여부 |
| AggregationMaxCount | 4294967295 | Aggregated Record 내 최대 User Record 수 |
| AggregationMaxSize | 51200 (50KB) | Aggregated Record 최대 크기 |
| CollectionMaxCount | 500 | PutRecords 호출당 최대 레코드 수 |
| CollectionMaxSize | 5242880 (5MB) | PutRecords 호출당 최대 데이터 크기 |
| RecordMaxBufferedTime | 100ms | 레코드 버퍼링 최대 시간 |
| RecordTtl | 30000ms | 레코드 전송 제한 시간 |

## 아키텍처 및 동작 원리

### KPL 내부 처리 흐름

```
[애플리케이션 코드]
    |
    v
[KPL addUserRecord()]
    |
    v
[Aggregation Buffer]
    |  (RecordMaxBufferedTime 또는 AggregationMaxSize 도달)
    v
[Aggregated Record 생성]
    |  (Protobuf 직렬화 + MD5 체크섬)
    |
    v
[Collection Buffer]
    |  (CollectionMaxCount 또는 CollectionMaxSize 도달)
    v
[PutRecords API 호출]
    |
    v
[Kinesis Data Streams Shard]
    |
    v
[Consumer (KCL / Lambda)]
    |
    v
[De-aggregation]
    |
    v
[개별 User Record 처리]
```

### Aggregated Record 바이너리 형식

KPL Aggregated Record는 Protocol Buffers(Protobuf) 형식으로 직렬화됩니다. 구조는 다음과 같습니다.

```
[Magic Number: 4 bytes (0xF3899AC2)]
[Protobuf Payload]
    - partition_key_table: [파티션 키 목록]
    - records: [
        {partition_key_index, data, tags},
        {partition_key_index, data, tags},
        ...
    ]
[MD5 Checksum: 16 bytes]
```

Consumer가 Kinesis로부터 레코드를 가져올 때, Magic Number(0xF3899AC2)를 확인하여 Aggregated Record 여부를 판별합니다.

## 실전 활용

### Java KPL 설정 및 사용

```java
import com.amazonaws.services.kinesis.producer.KinesisProducer;
import com.amazonaws.services.kinesis.producer.KinesisProducerConfiguration;
import com.amazonaws.services.kinesis.producer.UserRecordResult;
import com.google.common.util.concurrent.FutureCallback;
import com.google.common.util.concurrent.Futures;

KinesisProducerConfiguration config = new KinesisProducerConfiguration()
    .setRegion("ap-northeast-2")
    .setAggregationEnabled(true)
    .setAggregationMaxCount(100)
    .setRecordMaxBufferedTime(200)
    .setMaxConnections(10)
    .setRequestTimeout(60000);

KinesisProducer producer = new KinesisProducer(config);

for (Event event : events) {
    ByteBuffer data = ByteBuffer.wrap(event.toJson().getBytes("UTF-8"));
    ListenableFuture<UserRecordResult> future = producer.addUserRecord(
        "my-stream",
        event.getUserId(),
        data
    );
    Futures.addCallback(future, new FutureCallback<UserRecordResult>() {
        public void onSuccess(UserRecordResult result) {
            // 성공 처리
        }
        public void onFailure(Throwable t) {
            // 실패 처리 및 재시도
        }
    });
}

producer.flushSync();
producer.destroy();
```

### Consumer 측 De-aggregation

#### KCL (Kinesis Client Library) 사용 시

KCL 2.x는 자동으로 De-aggregation을 수행합니다. 추가 설정이 필요 없습니다.

```java
// KCL 2.x - 자동 De-aggregation
public class MyRecordProcessor implements ShardRecordProcessor {
    @Override
    public void processRecords(ProcessRecordsInput input) {
        for (KinesisClientRecord record : input.records()) {
            // 이미 De-aggregation된 개별 User Record
            String data = new String(record.data().array());
            processEvent(data);
        }
    }
}
```

#### AWS Lambda 사용 시

Lambda를 Kinesis 트리거로 사용할 때는 De-aggregation 라이브러리를 명시적으로 사용해야 합니다.

```python
# Lambda 함수 - KPL De-aggregation
import aws_kinesis_agg.deaggregator as deagg
import base64
import json

def lambda_handler(event, context):
    raw_records = event['Records']
    
    # KPL Aggregated Record를 De-aggregation
    user_records = deagg.deaggregate_records(raw_records)
    
    for record in user_records:
        payload = base64.b64decode(record['kinesis']['data'])
        data = json.loads(payload)
        process_event(data)
    
    return {'statusCode': 200}
```

필요한 패키지 설치:

```bash
pip install aws-kinesis-agg
```

### AWS CLI를 사용한 KPL 모니터링

```bash
# KPL 메트릭 확인 (CloudWatch)
aws cloudwatch get-metric-statistics \
    --namespace AWS/Kinesis \
    --metric-name IncomingRecords \
    --dimensions Name=StreamName,Value=my-event-stream \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-01T01:00:00Z \
    --period 300 \
    --statistics Sum Average

# KPL User Record 메트릭 (KPL 자체 메트릭)
aws cloudwatch get-metric-statistics \
    --namespace KinesisProducerLibrary \
    --metric-name UserRecordsPut \
    --dimensions Name=StreamName,Value=my-event-stream \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-01T01:00:00Z \
    --period 300 \
    --statistics Sum

# Aggregation 효율 확인: UserRecords vs KinesisRecords 비율
aws cloudwatch get-metric-statistics \
    --namespace KinesisProducerLibrary \
    --metric-name KinesisRecordsPut \
    --dimensions Name=StreamName,Value=my-event-stream \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-01T01:00:00Z \
    --period 300 \
    --statistics Sum
```

## 모범 사례 및 보안

### KPL Aggregation 설정 최적화

- **RecordMaxBufferedTime**: 지연 시간과 처리량의 트레이드오프를 결정합니다. 실시간성이 중요하면 100ms 이하, 처리량 우선이면 500ms~1000ms를 설정합니다.
- **AggregationMaxSize**: 25KB의 배수로 설정하여 과금 단위를 최대한 활용합니다. 기본값 50KB는 대부분의 시나리오에서 적합합니다.
- **RecordTtl**: 네트워크 장애 시 재시도 한도를 결정합니다. 너무 짧으면 데이터 손실, 너무 길면 메모리 압박이 발생합니다.

### Consumer 선택 시 De-aggregation 고려

| Consumer | De-aggregation | 주의사항 |
|----------|---------------|---------|
| KCL 2.x | 자동 지원 | 추가 설정 불필요 |
| KCL 1.x | 자동 지원 | 추가 설정 불필요 |
| AWS Lambda | 수동 필요 | aws-kinesis-agg 라이브러리 사용 |
| SDK GetRecords | 수동 필요 | Protobuf 파싱 직접 구현 |
| Kinesis Firehose | 자동 지원 | KPL 레코드 자동 De-aggregation |
| Kinesis Data Analytics | 자동 지원 | 추가 설정 불필요 |

### 보안

- KPL은 AWS SDK 자격 증명을 사용합니다. IAM 역할 또는 환경 변수를 통해 자격 증명을 제공합니다.
- TLS를 통해 전송 중 데이터를 암호화합니다. KPL 설정에서 `setVerifyCertificate(true)`를 확인합니다.
- KPL 메트릭에 민감한 데이터가 포함되지 않도록 CloudWatch 메트릭 네임스페이스 접근을 제한합니다.

## 관련 서비스 비교

| 항목 | KPL | AWS SDK PutRecords | Kinesis Agent |
|------|-----|-------------------|---------------|
| Aggregation | 지원 (자동) | 미지원 | 미지원 |
| Collection | 지원 (자동) | 수동 구현 | 자동 |
| 비동기 전송 | 지원 | 동기/비동기 선택 | 비동기 |
| 재시도 | 자동 (설정 가능) | 수동 구현 | 자동 |
| 언어 지원 | Java, C++ (+ Python wrapper) | 모든 SDK 언어 | Java (파일 전용) |
| 적합한 상황 | 고처리량 애플리케이션 | 간단한 전송 | 로그 파일 스트리밍 |

## 요약

Kinesis Producer Library(KPL)는 Aggregation과 Collection 두 단계 최적화를 통해 Kinesis Data Streams에 대한 데이터 전송 효율을 극대화합니다. Aggregation은 작은 레코드를 Protobuf 형식으로 묶어 25KB 과금 단위를 최적화하고, Collection은 묶인 레코드를 PutRecords API로 일괄 전송합니다. Consumer 측에서는 KCL이 자동으로 De-aggregation을 처리하지만, Lambda나 직접 SDK를 사용하는 경우 aws-kinesis-agg 라이브러리를 통한 명시적 De-aggregation이 필수입니다. KPL 도입 시 반드시 Consumer 측의 De-aggregation 지원 여부를 확인하여 데이터 처리 오류를 방지해야 합니다.