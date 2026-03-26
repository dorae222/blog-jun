# Amazon Kinesis 요약 - KPU 기반 과금 및 주요 특징 심층 분석

## 개요

Amazon Kinesis는 대규모 실시간 데이터 스트리밍을 수집, 처리, 분석할 수 있는 완전관리형 서비스 제품군입니다. IoT 디바이스 로그, 클릭스트림, 소셜 미디어 피드, 금융 거래 데이터 등 초당 수백만 건의 이벤트를 실시간으로 처리할 수 있습니다.

Kinesis 서비스 제품군은 네 가지 주요 서비스로 구성됩니다.

- **Kinesis Data Streams (KDS)**: 실시간 데이터 스트리밍 수집 및 저장
- **Kinesis Data Firehose**: 스트리밍 데이터의 대상 서비스로의 실시간 전송
- **Kinesis Data Analytics**: SQL 또는 Apache Flink 기반 실시간 스트림 분석
- **Kinesis Video Streams**: 비디오 스트리밍 수집 및 처리

이 글에서는 Kinesis 서비스의 과금 체계, 특히 KPU(Kinesis Processing Unit) 기반 과금과 각 서비스의 핵심 특징을 종합적으로 정리합니다.

## 핵심 기능

### KPU (Kinesis Processing Unit) 기반 과금

KPU는 Kinesis Data Analytics에서 사용되는 과금 단위입니다. 1 KPU는 4GB 메모리와 1 vCPU에 해당하는 컴퓨팅 리소스를 나타냅니다.

| 과금 항목 | 단위 | 설명 |
|-----------|------|------|
| KPU-시간 | 1 KPU = 4GB + 1vCPU | Data Analytics 처리 리소스 |
| 실행 중 KPU | 앱 실행 시간 기준 | 실제 처리에 사용된 KPU |
| 오케스트레이션 KPU | 앱당 고정 1 KPU | Apache Flink 앱 관리용 |
| 내구성 스토리지 | GB-월 | 애플리케이션 상태 백업용 |

KPU 과금의 핵심 포인트는 다음과 같습니다.

- 최소 과금 단위: 1 KPU-시간
- Auto Scaling으로 KPU 수가 자동 조절되므로, 트래픽 변동에 따라 비용이 유동적입니다
- 오케스트레이션 KPU는 Flink 앱당 항상 1개가 고정 과금됩니다
- 병렬 처리(parallelism) 설정에 따라 필요한 KPU 수가 결정됩니다

### Kinesis Data Streams 과금 체계

KDS는 KPU가 아닌 Shard 기반으로 과금됩니다.

**On-Demand 모드**:
- 스트림 시간당 과금 (데이터 처리량에 따라 자동 스케일링)
- 쓰기: 데이터 인입량(GB) 기준
- 읽기: 데이터 조회량(GB) 기준
- Enhanced Fan-Out 사용 시 추가 소비자별 과금

**Provisioned 모드**:
- Shard 시간당 과금 (수동으로 Shard 수 관리)
- 1 Shard = 쓰기 1MB/s, 읽기 2MB/s
- PUT Payload Units (25KB 단위) 기준 추가 과금

### Kinesis Data Firehose 과금 체계

Firehose는 처리된 데이터 볼륨(GB) 기준으로 과금됩니다. 최소 레코드 크기는 5KB로, 5KB 미만의 레코드도 5KB로 반올림됩니다.

| 과금 항목 | 기준 | 비고 |
|-----------|------|------|
| 데이터 인입 | GB당 | 최소 5KB/레코드 |
| 포맷 변환 | GB당 추가 | Parquet/ORC 변환 시 |
| VPC 전송 | GB당 + 시간당 | VPC 내 전송 시 |
| 동적 파티셔닝 | GB당 추가 | JQ 기반 파티셔닝 시 |

## 아키텍처 및 동작 원리

### Kinesis 서비스 간 통합 아키텍처

```
[데이터 소스]
    |
    v
[Kinesis Data Streams] ----> [Kinesis Data Analytics]
    |                              |  (SQL / Apache Flink)
    |                              |
    |                              v
    |                         [실시간 분석 결과]
    |                              |
    v                              v
[Kinesis Data Firehose] ----> [S3 / Redshift / OpenSearch / Splunk]
    |
    +-- Lambda 변환 (선택)
    +-- 포맷 변환 (Parquet/ORC)
    +-- 동적 파티셔닝
```

### Shard와 파티션 키

KDS에서 데이터는 Shard 단위로 분산 저장됩니다. 파티션 키(Partition Key)를 기반으로 해시 함수가 레코드를 특정 Shard에 할당합니다. 동일한 파티션 키를 가진 레코드는 항상 같은 Shard에 저장되어 순서가 보장됩니다.

### Consumer 모델

KDS는 두 가지 Consumer 모델을 지원합니다.

**Shared Throughput (표준)**: 모든 Consumer가 Shard당 2MB/s의 읽기 용량을 공유합니다. GetRecords API를 사용하며, 5초 간격으로 폴링합니다.

**Enhanced Fan-Out (EFO)**: 각 Consumer가 Shard당 독립적인 2MB/s 읽기 용량을 가집니다. SubscribeToShard API를 사용하며, HTTP/2 Push 방식으로 약 70ms의 지연 시간을 달성합니다.

## 실전 활용

### AWS CLI를 사용한 Kinesis Data Streams 관리

```bash
# On-Demand 모드로 스트림 생성
aws kinesis create-stream \
    --stream-name my-event-stream \
    --stream-mode-details '{"StreamMode": "ON_DEMAND"}'

# 스트림 상세 정보 조회 (Shard 수, 모드 확인)
aws kinesis describe-stream-summary \
    --stream-name my-event-stream \
    --query '{
        Status: StreamDescriptionSummary.StreamStatus,
        Mode: StreamDescriptionSummary.StreamModeDetails.StreamMode,
        Shards: StreamDescriptionSummary.OpenShardCount,
        Retention: StreamDescriptionSummary.RetentionPeriodHours
    }'

# 데이터 전송 테스트
aws kinesis put-record \
    --stream-name my-event-stream \
    --partition-key user-123 \
    --data $(echo '{"event": "page_view", "page": "/products", "timestamp": "2024-01-01T12:00:00Z"}' | base64)

# 대량 데이터 전송 (PutRecords - 최대 500건/요청)
aws kinesis put-records \
    --stream-name my-event-stream \
    --records '[
        {"Data": "eyJldmVudCI6ICJjbGljayJ9", "PartitionKey": "user-1"},
        {"Data": "eyJldmVudCI6ICJ2aWV3In0=", "PartitionKey": "user-2"},
        {"Data": "eyJldmVudCI6ICJwdXJjaGFzZSJ9", "PartitionKey": "user-3"}
    ]'

# Enhanced Fan-Out Consumer 등록
aws kinesis register-stream-consumer \
    --stream-arn arn:aws:kinesis:ap-northeast-2:123456789012:stream/my-event-stream \
    --consumer-name analytics-consumer

# 보존 기간 변경 (기본 24시간 -> 168시간)
aws kinesis increase-stream-retention-period \
    --stream-name my-event-stream \
    --retention-period-hours 168

# 스트림 모드 변경 (On-Demand -> Provisioned)
aws kinesis update-stream-mode \
    --stream-arn arn:aws:kinesis:ap-northeast-2:123456789012:stream/my-event-stream \
    --stream-mode-details '{"StreamMode": "PROVISIONED"}'

# Shard 수 조정 (Provisioned 모드)
aws kinesis update-shard-count \
    --stream-name my-event-stream \
    --target-shard-count 4 \
    --scaling-type UNIFORM_SCALING
```

### Kinesis Data Analytics (Apache Flink) 비용 모니터링

```bash
# Flink 애플리케이션의 KPU 사용량 확인
aws cloudwatch get-metric-statistics \
    --namespace AWS/KinesisAnalytics \
    --metric-name KPUs \
    --dimensions Name=Application,Value=my-flink-app \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-02T00:00:00Z \
    --period 3600 \
    --statistics Average Maximum \
    --query 'Datapoints[].{Time:Timestamp,AvgKPU:Average,MaxKPU:Maximum}' \
    --output table
```

### Python SDK로 실시간 데이터 수집

```python
import boto3
import json
import time

kinesis = boto3.client('kinesis', region_name='ap-northeast-2')

def send_events(stream_name, events):
    records = []
    for event in events:
        records.append({
            'Data': json.dumps(event).encode('utf-8'),
            'PartitionKey': event.get('user_id', 'default')
        })
    
    # 500건 단위로 배치 전송
    for i in range(0, len(records), 500):
        batch = records[i:i+500]
        response = kinesis.put_records(
            StreamName=stream_name,
            Records=batch
        )
        failed = response['FailedRecordCount']
        if failed > 0:
            print(f'재시도 필요: {failed}건 실패')

# 비용 추정 함수
def estimate_kds_cost(mode, avg_record_size_kb, records_per_sec, retention_hours=24):
    if mode == 'on_demand':
        write_gb = (avg_record_size_kb * records_per_sec * 3600) / (1024 * 1024)
        hourly_cost = 0.08 + (write_gb * 0.08)
        return f'시간당 약 ${hourly_cost:.4f}'
    elif mode == 'provisioned':
        write_throughput = (avg_record_size_kb * records_per_sec) / 1024
        shards_needed = max(1, int(write_throughput / 1))
        hourly_cost = shards_needed * 0.015
        return f'Shard {shards_needed}개, 시간당 약 ${hourly_cost:.4f}'
```

## 모범 사례 및 보안

### 비용 최적화 전략

- **스트림 모드 선택**: 트래픽이 예측 가능하면 Provisioned, 변동이 크면 On-Demand를 선택합니다. On-Demand는 편리하지만 단가가 높습니다.
- **보존 기간 최적화**: 기본 24시간에서 필요 최소한으로 설정합니다. 365일까지 연장 가능하지만, 보존 기간이 길수록 비용이 증가합니다.
- **Firehose 버퍼 설정**: 버퍼 크기와 간격을 최적화하여 S3 PUT 요청 수를 줄입니다. 버퍼 크기 128MB, 간격 300초가 일반적인 최적값입니다.
- **KPU Auto Scaling**: Flink 앱의 parallelism을 적절히 설정하고, Auto Scaling을 활성화하여 유휴 KPU를 최소화합니다.

### 보안

- **전송 중 암호화**: KDS는 TLS를 통해 전송 중 데이터를 암호화합니다.
- **저장 시 암호화**: KMS 키를 사용하여 Shard 내 데이터를 암호화합니다.
- **VPC Endpoint**: PrivateLink를 통해 VPC 내에서 Kinesis에 접근하여 인터넷 노출을 방지합니다.
- **IAM 정책**: 스트림별, 작업별(PutRecord, GetRecords 등) 세분화된 접근 제어를 적용합니다.
- **Enhanced Fan-Out 소비자별 접근 제어**: 각 Consumer ARN에 대해 개별 IAM 정책을 적용할 수 있습니다.

```bash
# KMS 암호화 활성화
aws kinesis start-stream-encryption \
    --stream-name my-event-stream \
    --encryption-type KMS \
    --key-id alias/kinesis-key
```

## 관련 서비스 비교

| 항목 | Kinesis Data Streams | Kinesis Firehose | Amazon MSK | Amazon SQS |
|------|---------------------|-----------------|------------|------------|
| 모델 | 실시간 스트리밍 | 전송 파이프라인 | Apache Kafka | 메시지 큐 |
| 순서 보장 | Shard 내 보장 | 보장 안 됨 | 파티션 내 보장 | FIFO만 보장 |
| 지연 시간 | ~200ms | 60초 버퍼 | ~10ms | ~ms |
| 소비자 | 다중 소비자 | 단일 대상 | 다중 소비자 | 단일 소비자 |
| 보존 | 24시간~365일 | 재시도만 | 무제한 | 14일 |
| 과금 | Shard/데이터 | 데이터 볼륨 | 브로커 시간 | 요청 수 |
| 관리 수준 | 완전관리 | 완전관리 | 반관리 | 완전관리 |

## 요약

Amazon Kinesis는 실시간 데이터 스트리밍을 위한 포괄적인 서비스 제품군으로, Data Streams(수집/저장), Firehose(전송), Data Analytics(분석)가 상호 연동하여 완전한 스트리밍 파이프라인을 구성합니다. 과금 체계는 서비스별로 다르며, KDS는 Shard/데이터 기반, Firehose는 처리 볼륨 기반, Data Analytics는 KPU-시간 기반입니다. 비용 최적화를 위해 스트림 모드 선택, 보존 기간 조정, KPU Auto Scaling 활성화 등의 전략을 적용하는 것이 중요합니다.