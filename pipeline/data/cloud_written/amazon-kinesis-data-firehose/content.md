<!-- infographic-hero -->
![Amazon Kinesis Data Firehose 핵심 요약](figures/infographic.svg)

*Figure: Amazon Kinesis Data Firehose 한 장 요약 인포그래픽*

# Amazon Kinesis Data Firehose

## 개요

Amazon Kinesis Data Firehose(현재 공식 명칭: Amazon Data Firehose)는 스트리밍 데이터를 데이터 스토어와 분석 서비스로 안정적으로 전달하는 완전 관리형 서비스입니다. Firehose는 사용자가 스트리밍 데이터 전달 인프라를 관리할 필요 없이, 데이터를 수집하고 변환하고 배달하는 전 과정을 자동으로 처리합니다.

Kinesis Data Streams가 범용 스트리밍 데이터 저장소인 반면, Firehose는 "데이터 배달"에 특화된 서비스입니다. 스트림에서 데이터를 소비하는 코드를 직접 작성하지 않아도, Firehose가 자동으로 데이터를 지정된 대상(S3, Redshift, OpenSearch 등)으로 전달합니다.

### Firehose의 핵심 특성

- **완전 관리형**: 서버, 샤드, 스케일링을 관리할 필요가 없습니다.
- **자동 스케일링**: 데이터 처리량에 따라 자동으로 확장됩니다.
- **Near Real-Time**: 버퍼링을 통해 최소 60초~최대 900초 간격으로 배달합니다 (완전한 실시간이 아닌 준실시간).
- **데이터 변환**: Lambda를 통한 데이터 변환, Parquet/ORC 포맷 변환을 지원합니다.
- **오류 처리**: 전달 실패 시 자동 재시도와 백업 S3 버킷으로의 실패 데이터 저장을 지원합니다.

### Firehose vs Kinesis Data Streams

이 두 서비스는 이름이 비슷하지만 근본적으로 다른 역할을 합니다.

- **KDS**: 스트리밍 데이터를 저장하고, 소비자(KCL, Lambda 등)가 데이터를 읽어가는 구조입니다.
- **Firehose**: 스트리밍 데이터를 자동으로 대상에 배달하는 구조입니다. 소비자 코드가 필요 없습니다.

## 핵심 기능

### 지원하는 데이터 대상 (Destination)

**AWS 서비스:**
- Amazon S3
- Amazon Redshift (S3를 경유하여 COPY)
- Amazon OpenSearch Service
- Amazon OpenSearch Serverless

**서드파티:**
- Datadog
- Splunk
- New Relic
- MongoDB Cloud
- Snowflake

**커스텀:**
- HTTP 엔드포인트 (모든 HTTP API)

### 데이터 소스 (Source)

Firehose로 데이터를 전송하는 방법은 다음과 같습니다.

- **Direct PUT**: AWS SDK, Kinesis Agent, CloudWatch Logs, CloudWatch Events, IoT Core 등에서 직접 전송
- **Kinesis Data Streams**: KDS를 소스로 연결하여 KDS의 데이터를 자동으로 배달

### 버퍼링

Firehose는 배달 전에 수신된 데이터를 내부적으로 버퍼링합니다. 버퍼 설정에는 두 가지 조건이 있으며, 둘 중 하나라도 먼저 충족되면 배달이 시작됩니다.

- **버퍼 크기(Buffer Size)**: 1MB ~ 128MB
- **버퍼 간격(Buffer Interval)**: 60초 ~ 900초

예를 들어 버퍼 크기를 5MB, 버퍼 간격을 300초로 설정하면, 5MB가 먼저 차거나 300초가 먼저 경과하면 배달이 수행됩니다.

### 데이터 변환

**Lambda 변환**: Firehose는 배달 전에 Lambda 함수를 호출하여 데이터를 변환할 수 있습니다. 로그 포맷 변환, 데이터 필터링, 필드 추가/제거 등을 수행할 수 있습니다.

**포맷 변환**: JSON 데이터를 Apache Parquet 또는 Apache ORC 포맷으로 자동 변환할 수 있습니다. 이를 통해 Athena나 Redshift Spectrum에서의 쿼리 성능을 크게 향상시킬 수 있습니다.

### 동적 파티셔닝

동적 파티셔닝 기능을 사용하면, 레코드의 필드 값에 따라 S3의 다른 경로에 데이터를 저장할 수 있습니다. 예를 들어 `customer_id` 필드에 따라 `s3://bucket/year=2024/month=01/customer_id=ABC/` 경로에 저장할 수 있습니다.

### 데이터 압축 및 암호화

- **압축**: GZIP, ZIP, Snappy, Hadoop Snappy 지원 (S3 대상)
- **암호화**: SSE-S3 또는 SSE-KMS를 통한 S3 저장 데이터 암호화, 전송 중 TLS 암호화

## 아키텍처/동작 원리

### 전체 아키텍처

```
[데이터 소스]
  +-- Direct PUT (SDK, Agent, CloudWatch)
  +-- Kinesis Data Streams
        |
        v
[Kinesis Data Firehose]
  +-- 수신 (Ingestion)
  +-- 버퍼링 (Buffering)
  +-- Lambda 변환 (Optional)
  +-- 포맷 변환 (Optional: Parquet/ORC)
  +-- 압축 (Optional: GZIP/Snappy)
  +-- 암호화 (Optional: SSE-S3/KMS)
        |
        v
[대상 (Destination)]
  +-- S3
  +-- Redshift (S3 -> COPY)
  +-- OpenSearch
  +-- HTTP Endpoint
  +-- Splunk / Datadog 등
        |
        v
[백업 (S3)]
  +-- 변환 실패 레코드
  +-- 배달 실패 레코드
```

### 배달 프로세스 상세

**S3 대상인 경우:**
1. 데이터 수신
2. 버퍼에 축적
3. (선택) Lambda 변환 호출
4. (선택) Parquet/ORC 포맷 변환
5. (선택) 압축 적용
6. S3에 파일 업로드
7. (선택) S3 -> Redshift COPY 실행

**OpenSearch 대상인 경우:**
1. 데이터 수신
2. 버퍼에 축적
3. (선택) Lambda 변환 호출
4. OpenSearch Bulk API로 인덱싱
5. 실패 레코드는 S3 백업 버킷에 저장

### Lambda 변환 프로세스

Lambda 변환의 동작 방식은 다음과 같습니다.

1. Firehose가 배치 단위로 Lambda 함수를 호출합니다.
2. Lambda 함수는 각 레코드에 대해 `Ok`, `Dropped`, `ProcessingFailed` 중 하나의 상태를 반환합니다.
3. `Ok`: 변환된 데이터가 대상으로 배달됩니다.
4. `Dropped`: 레코드가 의도적으로 삭제됩니다.
5. `ProcessingFailed`: 변환에 실패한 레코드는 S3 백업 버킷에 저장됩니다.

```python
import base64
import json

def lambda_handler(event, context):
    """Firehose 데이터 변환 Lambda 함수"""
    output = []

    for record in event['records']:
        # Base64 디코딩
        payload = base64.b64decode(record['data']).decode('utf-8')

        try:
            data = json.loads(payload)

            # 데이터 변환 로직
            transformed = {
                'timestamp': data.get('timestamp'),
                'user_id': data.get('user_id'),
                'event_type': data.get('event_type'),
                'page_url': data.get('page', {}).get('url'),
                'processed_at': context.function_name
            }

            # 결과 인코딩
            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(
                    (json.dumps(transformed) + '\n').encode('utf-8')
                ).decode('utf-8')
            }
        except Exception as e:
            # 변환 실패 시
            output_record = {
                'recordId': record['recordId'],
                'result': 'ProcessingFailed',
                'data': record['data']
            }

        output.append(output_record)

    return {'records': output}
```

### 오류 처리 메커니즘

Firehose는 다단계 오류 처리를 수행합니다.

1. **자동 재시도**: 대상 서비스에 대한 배달이 실패하면, 자동으로 최대 24시간까지 재시도합니다.
2. **백업 S3 버킷**: 최종적으로 실패한 레코드는 별도의 S3 백업 버킷에 저장됩니다.
3. **Lambda 변환 실패**: 변환에 실패한 레코드 역시 S3 백업 버킷에 원본 형태로 저장됩니다.

## 실전 활용

### Firehose 전송 스트림 생성 (AWS CLI)

```bash
# S3 대상 Firehose 전송 스트림 생성
aws firehose create-delivery-stream \
  --delivery-stream-name web-events-firehose \
  --delivery-stream-type DirectPut \
  --extended-s3-destination-configuration '{
    "RoleARN": "arn:aws:iam::123456789012:role/FirehoseDeliveryRole",
    "BucketARN": "arn:aws:s3:::my-data-lake-bucket",
    "Prefix": "web-events/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
    "ErrorOutputPrefix": "web-events-errors/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/!{firehose:error-output-type}/",
    "BufferingHints": {
      "SizeInMBs": 64,
      "IntervalInSeconds": 300
    },
    "CompressionFormat": "GZIP",
    "EncryptionConfiguration": {
      "KMSEncryptionConfig": {
        "AWSKMSKeyARN": "arn:aws:kms:ap-northeast-2:123456789012:key/12345678-1234-1234-1234-123456789012"
      }
    },
    "DataFormatConversionConfiguration": {
      "Enabled": true,
      "SchemaConfiguration": {
        "RoleARN": "arn:aws:iam::123456789012:role/FirehoseDeliveryRole",
        "DatabaseName": "analytics_db",
        "TableName": "web_events",
        "Region": "ap-northeast-2"
      },
      "InputFormatConfiguration": {
        "Deserializer": {
          "OpenXJsonSerDe": {}
        }
      },
      "OutputFormatConfiguration": {
        "Serializer": {
          "ParquetSerDe": {
            "Compression": "SNAPPY"
          }
        }
      }
    }
  }'

# 전송 스트림 상태 확인
aws firehose describe-delivery-stream \
  --delivery-stream-name web-events-firehose \
  --query 'DeliveryStreamDescription.{Status:DeliveryStreamStatus,Destinations:Destinations[0].S3DestinationDescription.BucketARN}'
```

### KDS를 소스로 하는 Firehose 생성

```bash
# KDS -> Firehose -> S3 파이프라인
aws firehose create-delivery-stream \
  --delivery-stream-name kds-to-s3-firehose \
  --delivery-stream-type KinesisStreamAsSource \
  --kinesis-stream-source-configuration '{
    "KinesisStreamARN": "arn:aws:kinesis:ap-northeast-2:123456789012:stream/my-data-stream",
    "RoleARN": "arn:aws:iam::123456789012:role/FirehoseKinesisRole"
  }' \
  --extended-s3-destination-configuration '{
    "RoleARN": "arn:aws:iam::123456789012:role/FirehoseDeliveryRole",
    "BucketARN": "arn:aws:s3:::my-data-lake-bucket",
    "Prefix": "stream-data/",
    "BufferingHints": {
      "SizeInMBs": 128,
      "IntervalInSeconds": 300
    },
    "CompressionFormat": "GZIP"
  }'
```

### 동적 파티셔닝 설정

```bash
# 동적 파티셔닝이 적용된 Firehose
aws firehose create-delivery-stream \
  --delivery-stream-name dynamic-partition-firehose \
  --delivery-stream-type DirectPut \
  --extended-s3-destination-configuration '{
    "RoleARN": "arn:aws:iam::123456789012:role/FirehoseDeliveryRole",
    "BucketARN": "arn:aws:s3:::my-data-lake-bucket",
    "Prefix": "events/customer_id=!{partitionKeyFromQuery:customer_id}/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
    "ErrorOutputPrefix": "errors/",
    "BufferingHints": {
      "SizeInMBs": 64,
      "IntervalInSeconds": 60
    },
    "DynamicPartitioningConfiguration": {
      "Enabled": true
    },
    "ProcessingConfiguration": {
      "Enabled": true,
      "Processors": [
        {
          "Type": "MetadataExtraction",
          "Parameters": [
            {
              "ParameterName": "MetadataExtractionQuery",
              "ParameterValue": "{customer_id: .customer_id}"
            },
            {
              "ParameterName": "JsonParsingEngine",
              "ParameterValue": "JQ-1.6"
            }
          ]
        },
        {
          "Type": "AppendDelimiterToRecord",
          "Parameters": [
            {
              "ParameterName": "Delimiter",
              "ParameterValue": "\\n"
            }
          ]
        }
      ]
    }
  }'
```

### 데이터 전송 테스트

```bash
# 테스트 레코드 전송
aws firehose put-record \
  --delivery-stream-name web-events-firehose \
  --record '{"Data": "{\"timestamp\":\"2024-01-15T10:30:00Z\",\"user_id\":\"user-123\",\"event_type\":\"page_view\",\"page_url\":\"/products/item-1\"}\n"}'

# 배치 레코드 전송
aws firehose put-record-batch \
  --delivery-stream-name web-events-firehose \
  --records \
    '{"Data": "{\"timestamp\":\"2024-01-15T10:30:01Z\",\"user_id\":\"user-124\",\"event_type\":\"click\"}\n"}' \
    '{"Data": "{\"timestamp\":\"2024-01-15T10:30:02Z\",\"user_id\":\"user-125\",\"event_type\":\"purchase\"}\n"}'

# CloudWatch 모니터링
aws cloudwatch get-metric-statistics \
  --namespace "AWS/Firehose" \
  --metric-name "DeliveryToS3.Success" \
  --dimensions Name=DeliveryStreamName,Value=web-events-firehose \
  --start-time "$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 300 \
  --statistics Sum
```

## 모범 사례/보안

### 성능 최적화

**1. 버퍼 크기 최적화**: 데이터 양이 많은 경우 버퍼 크기를 크게(64~128MB), 실시간성이 중요한 경우 버퍼 간격을 짧게(60초) 설정합니다.

**2. Parquet 변환 활용**: JSON 데이터를 Parquet으로 변환하면 S3 저장 비용과 후속 쿼리(Athena) 비용을 크게 절감할 수 있습니다.

**3. 동적 파티셔닝**: 자주 필터링되는 키로 동적 파티셔닝을 설정하면, Athena 쿼리 시 파티션 프루닝으로 비용과 시간을 절약할 수 있습니다.

**4. Lambda 변환 최적화**: Lambda 변환 함수의 타임아웃과 메모리를 적절히 설정합니다. Firehose는 Lambda를 3번까지 재시도하며, 모두 실패하면 레코드를 S3 백업에 저장합니다.

### 보안 모범 사례

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:AbortMultipartUpload",
        "s3:GetBucketLocation",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:ListBucketMultipartUploads",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::my-data-lake-bucket",
        "arn:aws:s3:::my-data-lake-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["lambda:InvokeFunction", "lambda:GetFunctionConfiguration"],
      "Resource": "arn:aws:lambda:ap-northeast-2:123456789012:function:firehose-transformer"
    },
    {
      "Effect": "Allow",
      "Action": ["kms:Decrypt", "kms:GenerateDataKey"],
      "Resource": "arn:aws:kms:ap-northeast-2:123456789012:key/*"
    },
    {
      "Effect": "Allow",
      "Action": ["logs:PutLogEvents"],
      "Resource": "arn:aws:logs:ap-northeast-2:123456789012:log-group:/aws/kinesisfirehose/*"
    }
  ]
}
```

- 전송 스트림에 SSE-KMS 암호화를 활성화합니다.
- S3 대상 버킷에 버킷 정책으로 SSL 전송을 강제합니다.
- CloudWatch Logs를 활성화하여 배달 오류를 모니터링합니다.

### 비용 최적화

- Firehose는 수집된 데이터 양(GB 단위)으로 과금됩니다.
- Parquet 변환 시 추가 요금이 발생하지만, 후속 Athena 쿼리 비용 절감이 더 큽니다.
- Lambda 변환의 비용은 Lambda 호출 비용으로 별도 발생합니다.
- 불필요한 데이터를 Lambda에서 필터링(Dropped)하면 S3 저장 비용을 줄일 수 있습니다.

## 관련 서비스 비교

### Firehose vs Kinesis Data Streams

| 항목 | Firehose | KDS |
|------|----------|-----|
| 관리 방식 | 완전 관리형 | 샤드 관리 필요 (On-Demand 제외) |
| 실시간성 | Near Real-Time (60초~) | Real-Time (밀리초) |
| 데이터 재처리 | 불가 | 가능 (보존 기간 내) |
| 소비자 코드 | 불필요 | 필요 (KCL/Lambda) |
| 대상 | 특정 서비스 (S3, Redshift 등) | 자유 (코드로 결정) |
| 데이터 변환 | Lambda/포맷 변환 내장 | 소비자에서 처리 |

### Firehose vs AWS Glue Streaming ETL

| 항목 | Firehose | Glue Streaming ETL |
|------|----------|--------------------|
| 변환 복잡도 | 단순 (Lambda) | 복잡 (Spark) |
| 상태 관리 | 없음 | Spark Checkpoint |
| 윈도우 처리 | 미지원 | 지원 |
| 비용 | 데이터 양 기반 | DPU 시간 기반 |

### 일반적인 파이프라인 패턴

실전에서 Firehose는 다음과 같은 패턴으로 주로 사용됩니다.

1. **Direct PUT -> Firehose -> S3**: 가장 간단한 로그 수집 패턴
2. **KDS -> Firehose -> S3**: 실시간 처리(KDS + Lambda/KCL)와 저장(Firehose)을 동시에 수행
3. **CloudWatch Logs -> Firehose -> S3**: 로그 아카이빙
4. **IoT Core -> Firehose -> S3 -> Athena**: IoT 데이터 분석 파이프라인

## 요약

Amazon Kinesis Data Firehose는 스트리밍 데이터를 다양한 대상으로 자동 배달하는 완전 관리형 서비스입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **완전 관리형**: 서버, 샤드, 스케일링 관리가 불필요합니다. 데이터를 넣으면 자동으로 배달됩니다.
- **Near Real-Time**: 버퍼링(최소 60초)을 통해 효율적으로 배달하므로, 실시간이 아닌 준실시간 서비스입니다.
- **데이터 변환**: Lambda 변환과 Parquet/ORC 포맷 변환을 내장하여, ETL 없이 분석에 최적화된 형태로 저장할 수 있습니다.
- **동적 파티셔닝**: 레코드의 필드 값에 따라 S3의 다른 경로에 저장하여, 후속 쿼리 성능을 최적화합니다.
- **오류 처리**: 자동 재시도와 S3 백업으로 데이터 손실을 방지합니다.
- **비용 효율적**: 수집 데이터 양 기반 과금으로, 유휴 시에는 비용이 발생하지 않습니다.

Firehose는 "데이터를 S3/Redshift/OpenSearch에 안정적으로 전달"하는 것이 목표일 때 가장 적합한 선택입니다.