<!-- infographic-hero -->
![Amazon Kinesis Data Streams (KDS) 개요 핵심 요약](figures/infographic.svg)

*Figure: Amazon Kinesis Data Streams (KDS) 개요 한 장 요약 인포그래픽*

# Amazon Kinesis Data Streams (KDS) 개요

## 개요

Amazon Kinesis Data Streams(KDS)는 대규모 실시간 데이터 스트리밍을 처리하기 위한 서버리스 데이터 스트리밍 서비스입니다. 웹 클릭스트림, 애플리케이션 로그, IoT 센서 데이터, 소셜 미디어 피드 등 지속적으로 생성되는 데이터를 초 단위의 지연으로 수집하고 처리할 수 있습니다.

KDS의 핵심 아이디어는 "데이터 생산자(Producer)"와 "데이터 소비자(Consumer)"를 분리(decouple)하는 것입니다. 생산자는 데이터를 스트림에 쓰기만 하고, 소비자는 스트림에서 데이터를 읽어가기만 합니다. 이 구조 덕분에 생산자와 소비자를 독립적으로 스케일링할 수 있으며, 하나의 스트림에 여러 소비자가 동시에 접근할 수 있습니다.

### KDS를 선택해야 하는 경우

- 밀리초 수준의 실시간 데이터 처리가 필요한 경우
- 여러 소비자가 동일한 데이터를 독립적으로 처리해야 하는 경우
- 데이터를 일정 기간 보존하면서 재처리가 가능해야 하는 경우
- 순서가 보장되는 데이터 처리가 필요한 경우

### KDS의 위치: Kinesis 패밀리

Amazon Kinesis 패밀리는 여러 서비스로 구성되어 있습니다.

- **Kinesis Data Streams (KDS)**: 실시간 데이터 스트리밍 (이 글의 주제)
- **Kinesis Data Firehose**: 데이터 배달 (S3, Redshift 등으로 자동 전송)
- **Kinesis Data Analytics**: 스트리밍 데이터에 대한 SQL/Apache Flink 분석
- **Kinesis Video Streams**: 비디오 스트리밍

## 핵심 기능

### 샤드 (Shard)

샤드는 KDS의 기본 처리량 단위입니다. 각 샤드는 다음과 같은 처리량을 제공합니다.

- **쓰기**: 1MB/s 또는 1,000 records/s
- **읽기**: 2MB/s (공유) 또는 소비자당 2MB/s (Enhanced Fan-Out)

스트림의 총 처리량은 샤드 수에 비례합니다. 예를 들어 10개의 샤드로 구성된 스트림은 쓰기 10MB/s, 읽기 20MB/s의 처리량을 제공합니다.

### 데이터 레코드

KDS에 저장되는 데이터의 기본 단위는 레코드(Record)입니다. 각 레코드는 다음으로 구성됩니다.

- **파티션 키(Partition Key)**: 레코드가 저장될 샤드를 결정하는 키. MD5 해시를 통해 샤드에 매핑됩니다.
- **데이터 블롭(Data Blob)**: 실제 데이터. 최대 1MB.
- **시퀀스 번호(Sequence Number)**: KDS가 자동으로 부여하는 고유 식별자. 같은 샤드 내에서 순서를 보장합니다.

### 데이터 보존 (Retention Period)

KDS는 수신된 데이터를 일정 기간 보존합니다.

- **기본**: 24시간
- **확장**: 최대 8,760시간 (365일)
- **보존 기간 내의 데이터는 언제든 재처리 가능**

이 기능은 소비자에 장애가 발생했을 때 데이터 손실 없이 복구할 수 있게 해줍니다.

### 용량 모드

KDS는 두 가지 용량 모드를 제공합니다.

**Provisioned Mode:**
- 사용자가 샤드 수를 직접 지정합니다.
- 샤드당 과금됩니다.
- 트래픽 예측이 가능한 경우 비용 효율적입니다.
- 수동으로 리샤딩(샤드 분할/병합)을 수행합니다.

**On-Demand Mode:**
- 샤드 수를 자동으로 관리합니다.
- 데이터 수집량에 따라 자동 스케일링됩니다.
- 트래픽 예측이 어렵거나 급변하는 경우 적합합니다.
- 쓰기 처리량 기본 4MB/s, 최대 200MB/s까지 자동 확장됩니다.
- Provisioned보다 단가가 높지만 운영 부담이 없습니다.

### Enhanced Fan-Out

기본적으로 하나의 샤드에서 모든 소비자가 2MB/s의 읽기 처리량을 공유합니다. Enhanced Fan-Out을 사용하면 각 소비자가 샤드당 전용 2MB/s 처리량을 보장받습니다.

- **기본 (Shared)**: GetRecords API, 폴링 방식, 소비자 공유 2MB/s
- **Enhanced Fan-Out**: SubscribeToShard API, HTTP/2 푸시 방식, 소비자별 전용 2MB/s

Enhanced Fan-Out은 2개 이상의 소비자 애플리케이션이 동일한 스트림을 읽을 때, 또는 200ms 이하의 전파 지연이 필요할 때 권장됩니다.

### 서버 측 암호화

KDS는 AWS KMS를 사용한 서버 측 암호화를 지원합니다. 활성화하면 데이터가 KDS에 저장될 때 자동으로 암호화되고, 소비자가 읽을 때 자동으로 복호화됩니다.

## 아키텍처/동작 원리

### 전체 아키텍처

```
[생산자 (Producer)]
  +-- AWS SDK (PutRecord/PutRecords)
  +-- KPL (Kinesis Producer Library)
  +-- Kinesis Agent
  +-- CloudWatch Logs Subscription
  +-- IoT Core Rules
        |
        v
[Kinesis Data Stream]
  +-- Shard-0 (Hash Range: 0 ~ 85070591730234615865843651857942052863)
  +-- Shard-1 (Hash Range: 85070591730234615865843651857942052864 ~ 170141183460469231731687303715884105727)
  +-- Shard-2 (Hash Range: ...)
  +-- ...
        |
        v
[소비자 (Consumer)]
  +-- KCL (Kinesis Client Library)
  +-- AWS Lambda (Event Source Mapping)
  +-- Kinesis Data Firehose
  +-- Kinesis Data Analytics
  +-- AWS SDK (GetRecords)
```

### 파티션 키와 샤드 매핑

파티션 키가 샤드에 매핑되는 과정은 다음과 같습니다.

1. 생산자가 레코드와 함께 파티션 키(문자열)를 제공합니다.
2. KDS가 파티션 키의 MD5 해시를 계산합니다 (128비트 정수).
3. 해시 값이 속하는 해시 키 범위를 가진 샤드에 레코드가 저장됩니다.
4. 전체 해시 공간(0 ~ 2^128-1)이 샤드 수만큼 분할되어 있습니다.

같은 파티션 키를 가진 레코드는 항상 같은 샤드에 저장됩니다. 이를 통해 특정 키에 대한 순서가 보장됩니다.

### 리샤딩 (Resharding)

리샤딩은 스트림의 샤드 수를 변경하는 작업입니다.

**샤드 분할 (Split)**: 하나의 샤드를 두 개로 분할합니다. 처리량을 늘릴 때 사용합니다.

**샤드 병합 (Merge)**: 인접한 두 샤드를 하나로 병합합니다. 처리량을 줄일 때 사용합니다.

리샤딩 중에도 데이터의 읽기/쓰기는 계속됩니다. 부모 샤드의 데이터는 완전히 소비된 후에야 자식 샤드로 전환됩니다.

### 시퀀스 번호와 순서 보장

- 같은 샤드 내에서는 시퀀스 번호 순으로 레코드가 정렬됩니다.
- 다른 샤드 간에는 순서가 보장되지 않습니다.
- 따라서 순서가 중요한 데이터는 동일한 파티션 키를 사용하여 같은 샤드에 저장되도록 해야 합니다.

### 읽기 모드 상세

**공유 처리량 소비자 (GetRecords):**
- 소비자가 5초당 최대 5회 GetRecords를 호출할 수 있습니다.
- 호출당 최대 10,000개 레코드, 10MB까지 반환됩니다.
- 같은 샤드를 읽는 모든 소비자가 2MB/s를 공유합니다.

**Enhanced Fan-Out 소비자 (SubscribeToShard):**
- HTTP/2 기반 푸시 방식으로 데이터를 수신합니다.
- 소비자당 샤드별 전용 2MB/s가 보장됩니다.
- 최대 20개의 Enhanced Fan-Out 소비자를 등록할 수 있습니다.
- 전파 지연이 평균 70ms로 매우 짧습니다.

## 실전 활용

### 스트림 생성 및 관리 (AWS CLI)

```bash
# Provisioned 모드 스트림 생성
aws kinesis create-stream \
  --stream-name web-clickstream \
  --shard-count 4

# On-Demand 모드 스트림 생성
aws kinesis create-stream \
  --stream-name web-clickstream-ondemand \
  --stream-mode-details StreamMode=ON_DEMAND

# 스트림 상태 확인
aws kinesis describe-stream-summary \
  --stream-name web-clickstream

# 샤드 목록 확인
aws kinesis list-shards \
  --stream-name web-clickstream

# 데이터 보존 기간 변경 (168시간 = 7일)
aws kinesis increase-stream-retention-period \
  --stream-name web-clickstream \
  --retention-period-hours 168

# 서버 측 암호화 활성화
aws kinesis start-stream-encryption \
  --stream-name web-clickstream \
  --encryption-type KMS \
  --key-id "alias/aws/kinesis"

# 용량 모드 변경 (Provisioned -> On-Demand)
aws kinesis update-stream-mode \
  --stream-arn "arn:aws:kinesis:ap-northeast-2:123456789012:stream/web-clickstream" \
  --stream-mode-details StreamMode=ON_DEMAND
```

### 데이터 쓰기/읽기

```bash
# 단일 레코드 쓰기
aws kinesis put-record \
  --stream-name web-clickstream \
  --partition-key "user-12345" \
  --data '{"user_id":"user-12345","event":"page_view","url":"/products","timestamp":"2024-01-15T10:30:00Z"}'

# 배치 레코드 쓰기
aws kinesis put-records \
  --stream-name web-clickstream \
  --records \
    '{"Data": "{\"user_id\":\"user-001\",\"event\":\"click\"}", "PartitionKey": "user-001"}' \
    '{"Data": "{\"user_id\":\"user-002\",\"event\":\"purchase\"}", "PartitionKey": "user-002"}' \
    '{"Data": "{\"user_id\":\"user-003\",\"event\":\"page_view\"}", "PartitionKey": "user-003"}'

# 샤드 이터레이터 가져오기
SHARD_ITERATOR=$(aws kinesis get-shard-iterator \
  --stream-name web-clickstream \
  --shard-id shardId-000000000000 \
  --shard-iterator-type TRIM_HORIZON \
  --query 'ShardIterator' --output text)

# 레코드 읽기
aws kinesis get-records \
  --shard-iterator "$SHARD_ITERATOR" \
  --limit 10
```

### 리샤딩

```bash
# 샤드 분할 (스케일 업)
aws kinesis split-shard \
  --stream-name web-clickstream \
  --shard-to-split shardId-000000000000 \
  --new-starting-hash-key "170141183460469231731687303715884105728"

# 샤드 병합 (스케일 다운)
aws kinesis merge-shards \
  --stream-name web-clickstream \
  --shard-to-merge shardId-000000000001 \
  --adjacent-shard-to-merge shardId-000000000002

# 원하는 샤드 수로 업데이트 (간편 API)
aws kinesis update-shard-count \
  --stream-name web-clickstream \
  --target-shard-count 8 \
  --scaling-type UNIFORM_SCALING
```

### Python Boto3를 활용한 생산자

```python
import boto3
import json
import time
import random

def produce_events(stream_name, events_per_second=100, duration_seconds=60):
    """KDS에 이벤트를 생산하는 함수"""
    client = boto3.client('kinesis', region_name='ap-northeast-2')

    event_types = ['page_view', 'click', 'add_to_cart', 'purchase', 'search']
    pages = ['/home', '/products', '/products/item-1', '/cart', '/checkout']

    total_sent = 0
    start_time = time.time()

    while time.time() - start_time < duration_seconds:
        # 배치 레코드 준비 (최대 500개)
        records = []
        batch_size = min(events_per_second, 500)

        for _ in range(batch_size):
            user_id = f"user-{random.randint(1, 10000):05d}"
            event = {
                'user_id': user_id,
                'event_type': random.choice(event_types),
                'page_url': random.choice(pages),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'session_id': f"sess-{random.randint(1, 100000)}"
            }
            records.append({
                'Data': json.dumps(event).encode('utf-8'),
                'PartitionKey': user_id  # 같은 사용자는 같은 샤드로
            })

        # 배치 전송
        response = client.put_records(
            StreamName=stream_name,
            Records=records
        )

        failed = response['FailedRecordCount']
        total_sent += len(records) - failed

        if failed > 0:
            print(f"Failed records: {failed}/{len(records)}")

        time.sleep(1)  # 초당 제어

    print(f"Total records sent: {total_sent}")

# 사용
produce_events('web-clickstream', events_per_second=200, duration_seconds=30)
```

### CloudWatch 모니터링

```bash
# 수신 바이트 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace "AWS/Kinesis" \
  --metric-name "IncomingBytes" \
  --dimensions Name=StreamName,Value=web-clickstream \
  --start-time "$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 \
  --statistics Sum

# 쓰기 스로틀링 확인
aws cloudwatch get-metric-statistics \
  --namespace "AWS/Kinesis" \
  --metric-name "WriteProvisionedThroughputExceeded" \
  --dimensions Name=StreamName,Value=web-clickstream \
  --start-time "$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 \
  --statistics Sum

# 읽기 반복자 만료 확인 (소비자가 뒤처지고 있는 지표)
aws cloudwatch get-metric-statistics \
  --namespace "AWS/Kinesis" \
  --metric-name "GetRecords.IteratorAgeMilliseconds" \
  --dimensions Name=StreamName,Value=web-clickstream \
  --start-time "$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 300 \
  --statistics Maximum
```

## 모범 사례/보안

### 파티션 키 전략

파티션 키 선택은 KDS 성능에 가장 큰 영향을 미치는 요소입니다.

**균등 분배가 중요**: 특정 샤드에 데이터가 집중되면(Hot Shard) 처리량 초과 오류가 발생합니다. 파티션 키는 높은 카디널리티(고유 값이 많은)를 가져야 합니다.

- 좋은 파티션 키: user_id, session_id, device_id (값이 많고 균등하게 분포)
- 나쁜 파티션 키: country (값이 적고 편중됨), event_type (값이 몇 개 안 됨)

**순서 보장이 필요한 경우**: 같은 사용자의 이벤트 순서가 중요하면 user_id를 파티션 키로 사용합니다. 같은 파티션 키는 항상 같은 샤드에 저장되므로, 샤드 내 순서가 보장됩니다.

### 스로틀링 대응

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords",
        "kinesis:DescribeStream",
        "kinesis:DescribeStreamSummary"
      ],
      "Resource": "arn:aws:kinesis:ap-northeast-2:123456789012:stream/web-clickstream"
    }
  ]
}
```

WriteProvisionedThroughputExceeded 메트릭이 지속적으로 발생하면 다음과 같이 대응합니다.

1. 샤드 수를 늘립니다 (update-shard-count).
2. 파티션 키의 분포를 확인하여 Hot Shard 문제를 해결합니다.
3. KPL의 Aggregation 기능을 사용하여 레코드를 묶어 전송합니다.
4. 지수 백오프(Exponential Backoff)를 적용한 재시도 로직을 구현합니다.

### 보안 모범 사례

- 서버 측 암호화(SSE)를 반드시 활성화합니다.
- VPC 엔드포인트를 사용하여 프라이빗 네트워크에서 KDS에 접근합니다.
- IAM 정책으로 스트림별 접근을 제어합니다.
- CloudTrail로 API 호출을 감사합니다.

### 비용 최적화

- **On-Demand vs Provisioned**: 트래픽이 예측 가능하면 Provisioned가 저렴합니다. 예측이 어려우면 On-Demand를 사용합니다.
- **데이터 보존 기간**: 기본 24시간에서 늘리면 추가 비용이 발생합니다. 필요한 만큼만 설정합니다.
- **Enhanced Fan-Out**: 소비자당 추가 비용이 발생합니다. 2개 이상의 소비자가 있을 때만 고려합니다.
- **PUT Payload 최적화**: PutRecords(배치)를 사용하면 개별 PutRecord보다 비용 효율적입니다.

## 관련 서비스 비교

### KDS vs Amazon MSK (Managed Streaming for Apache Kafka)

| 항목 | KDS | Amazon MSK |
|------|-----|------------|
| 관리 수준 | 서버리스 | 관리형 (클러스터 관리) |
| 프로토콜 | AWS 독자 | Apache Kafka 프로토콜 |
| 메시지 크기 | 최대 1MB | 기본 1MB, 최대 10MB |
| 보존 기간 | 최대 365일 | 무제한 (디스크 용량 내) |
| 생태계 | AWS SDK, KCL, KPL | Kafka Connect, Kafka Streams |
| 비용 | 샤드/처리량 기반 | 브로커 인스턴스 기반 |
| 적합한 경우 | AWS 네이티브, 단순 스트리밍 | Kafka 생태계 활용, 복잡한 요구 |

### KDS vs Amazon SQS

| 항목 | KDS | SQS |
|------|-----|-----|
| 패턴 | 스트리밍 (1:N) | 메시징 (1:1) |
| 소비자 | 여러 소비자가 동일 데이터 읽기 | 메시지 소비 후 삭제 |
| 순서 보장 | 샤드 내 보장 | FIFO 큐에서만 보장 |
| 데이터 보존 | 24시간~365일 | 최대 14일 |
| 재처리 | 가능 | 불가 (소비 후 삭제) |
| 처리량 | 샤드당 고정 | 자동 스케일링 |

### KDS vs Amazon EventBridge

| 항목 | KDS | EventBridge |
|------|-----|-------------|
| 패턴 | 고처리량 스트리밍 | 이벤트 라우팅 |
| 처리량 | 샤드당 1MB/s 쓰기 | 초당 수천 이벤트 |
| 라우팅 | 파티션 키 기반 | 이벤트 패턴 매칭 |
| 적합한 경우 | 대용량 데이터 스트리밍 | 서비스 간 이벤트 기반 통합 |

## 요약

Amazon Kinesis Data Streams는 대규모 실시간 데이터 스트리밍을 위한 핵심 AWS 서비스입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **샤드 기반 아키텍처**: 샤드가 처리량의 기본 단위이며, 스트림의 처리량은 샤드 수에 비례합니다.
- **순서 보장**: 같은 파티션 키를 가진 레코드는 같은 샤드에 저장되어 순서가 보장됩니다.
- **데이터 보존**: 24시간(기본)~365일까지 데이터를 보존하며, 보존 기간 내 재처리가 가능합니다.
- **용량 모드**: Provisioned(수동 관리, 저렴)와 On-Demand(자동 스케일링, 편리) 중 선택합니다.
- **Enhanced Fan-Out**: 소비자별 전용 처리량이 필요하면 EFO를 활성화합니다.
- **파티션 키 전략**: 높은 카디널리티의 균등한 파티션 키 선택이 성능의 핵심입니다.
- **모니터링**: WriteProvisionedThroughputExceeded와 IteratorAgeMilliseconds가 핵심 모니터링 지표입니다.