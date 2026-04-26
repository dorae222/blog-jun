<!-- infographic-hero -->
![Amazon DynamoDB Streams 핵심 요약](figures/infographic.svg)

*Figure: Amazon DynamoDB Streams 한 장 요약 인포그래픽*

## 개요

Amazon DynamoDB Streams는 DynamoDB 테이블에서 발생하는 항목(Item) 수준의 변경 사항을 시간 순서대로 캡처하여 스트림으로 제공하는 기능입니다. 이를 변경 데이터 캡처(Change Data Capture, CDC)라고 하며, 테이블의 INSERT, UPDATE, DELETE 이벤트를 거의 실시간으로 처리할 수 있게 합니다.

DynamoDB Streams의 주요 활용 사례는 다음과 같습니다.

- **이벤트 기반 아키텍처**: 데이터 변경을 트리거로 하여 다른 서비스의 작업을 자동으로 실행합니다.
- **데이터 복제**: 여러 테이블 또는 리전 간 데이터를 동기화합니다.
- **집계 및 분석**: 변경 이벤트를 수집하여 실시간 대시보드나 분석 시스템에 전달합니다.
- **감사 로깅**: 데이터 변경 이력을 별도 저장소에 기록합니다.
- **캐시 무효화**: 데이터 변경 시 ElastiCache 등의 캐시를 자동으로 갱신합니다.

DynamoDB Streams 외에도 Amazon Kinesis Data Streams for DynamoDB를 사용할 수 있으며, 이 두 방식은 서로 다른 장단점을 가지고 있습니다.

## 핵심 기능

### 스트림 활성화

DynamoDB Streams를 활성화할 때 스트림 레코드에 포함할 정보의 수준(StreamViewType)을 선택합니다.

- **KEYS_ONLY**: 변경된 항목의 키 속성만 포함합니다.
- **NEW_IMAGE**: 변경 후의 전체 항목을 포함합니다.
- **OLD_IMAGE**: 변경 전의 전체 항목을 포함합니다.
- **NEW_AND_OLD_IMAGES**: 변경 전후의 전체 항목을 모두 포함합니다.

```bash
# 기존 테이블에 DynamoDB Streams 활성화
aws dynamodb update-table \
  --table-name Orders \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES

# 새 테이블 생성 시 스트림 활성화
aws dynamodb create-table \
  --table-name Products \
  --attribute-definitions \
    AttributeName=ProductId,AttributeType=S \
  --key-schema \
    AttributeName=ProductId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --stream-specification StreamEnabled=true,StreamViewType=NEW_AND_OLD_IMAGES

# 스트림 정보 확인
aws dynamodb describe-table \
  --table-name Orders \
  --query 'Table.{StreamArn: LatestStreamArn, StreamEnabled: StreamSpecification.StreamEnabled, StreamViewType: StreamSpecification.StreamViewType}'
```

### 스트림 레코드 구조

스트림 레코드는 다음과 같은 정보를 포함합니다.

```json
{
  "eventID": "abc123def456",
  "eventName": "MODIFY",
  "eventVersion": "1.1",
  "eventSource": "aws:dynamodb",
  "awsRegion": "ap-northeast-2",
  "dynamodb": {
    "ApproximateCreationDateTime": 1711180800,
    "Keys": {
      "OrderId": {"S": "ORD-001"}
    },
    "NewImage": {
      "OrderId": {"S": "ORD-001"},
      "Status": {"S": "SHIPPED"},
      "Amount": {"N": "29900"}
    },
    "OldImage": {
      "OrderId": {"S": "ORD-001"},
      "Status": {"S": "PROCESSING"},
      "Amount": {"N": "29900"}
    },
    "SequenceNumber": "111",
    "SizeBytes": 256,
    "StreamViewType": "NEW_AND_OLD_IMAGES"
  }
}
```

### Lambda 트리거 연동

DynamoDB Streams의 가장 일반적인 소비자는 AWS Lambda입니다.

```bash
# DynamoDB Streams를 Lambda 함수의 이벤트 소스로 등록
aws lambda create-event-source-mapping \
  --function-name process-order-changes \
  --event-source-arn arn:aws:dynamodb:ap-northeast-2:123456789012:table/Orders/stream/2026-03-23T00:00:00.000 \
  --batch-size 100 \
  --maximum-batching-window-in-seconds 5 \
  --starting-position LATEST \
  --maximum-retry-attempts 3 \
  --bisect-batch-on-function-error \
  --destination-config '{
    "OnFailure": {
      "Destination": "arn:aws:sqs:ap-northeast-2:123456789012:dlq-order-changes"
    }
  }'

# 이벤트 소스 매핑 조회
aws lambda list-event-source-mappings \
  --function-name process-order-changes

# 이벤트 소스 매핑 수정
aws lambda update-event-source-mapping \
  --uuid abc123-def456-ghi789 \
  --batch-size 200 \
  --maximum-batching-window-in-seconds 10
```

### Kinesis Data Streams for DynamoDB

DynamoDB Streams 대신 Kinesis Data Streams를 변경 데이터 대상으로 사용할 수도 있습니다.

```bash
# Kinesis Data Stream 생성
aws kinesis create-stream \
  --stream-name dynamodb-changes-stream \
  --shard-count 4

# DynamoDB 테이블에 Kinesis 스트림 연결
aws dynamodb enable-kinesis-streaming-destination \
  --table-name Orders \
  --stream-arn arn:aws:kinesis:ap-northeast-2:123456789012:stream/dynamodb-changes-stream

# 스트리밍 대상 상태 확인
aws dynamodb describe-kinesis-streaming-destination \
  --table-name Orders
```

Kinesis Data Streams 방식의 장점은 다음과 같습니다.

- 데이터 보존 기간: 최대 365일 (DynamoDB Streams는 24시간)
- 다중 소비자: 여러 애플리케이션이 동시에 동일 스트림을 소비 가능
- Kinesis 생태계 활용: Kinesis Data Analytics, Kinesis Data Firehose 등과 통합
- 더 높은 처리량: 샤드 수를 조절하여 스케일링 가능

## 아키텍처/동작 원리

### DynamoDB Streams 내부 구조

DynamoDB Streams는 내부적으로 샤드(Shard)로 구성됩니다. 각 샤드는 일련의 스트림 레코드를 포함하며, DynamoDB가 자동으로 샤드를 관리합니다.

1. **스트림**: 테이블당 하나의 스트림이 존재합니다.
2. **샤드**: 스트림 내의 데이터 분할 단위입니다. 테이블의 파티션 변경에 따라 자동으로 분할/병합됩니다.
3. **스트림 레코드**: 개별 변경 이벤트를 나타냅니다. 각 레코드에는 고유한 시퀀스 번호가 부여됩니다.

### 순서 보장

DynamoDB Streams는 동일한 파티션 키를 가진 항목에 대해 변경 순서를 보장합니다. 즉, 같은 항목에 대한 변경 이벤트는 발생한 순서대로 스트림 레코드에 기록됩니다.

다만, 서로 다른 파티션 키를 가진 항목들 간에는 순서가 보장되지 않습니다. 이 점은 이벤트 처리 로직을 설계할 때 반드시 고려해야 합니다.

### 보존 기간

DynamoDB Streams의 레코드는 24시간 동안 보존됩니다. 24시간이 지나면 레코드는 자동으로 삭제됩니다. 더 긴 보존 기간이 필요하면 Kinesis Data Streams를 사용하거나, Lambda를 통해 S3 등의 영구 저장소에 아카이빙해야 합니다.

### 처리량과 제한사항

- 스트림에서 읽기: 초당 최대 2회의 GetRecords API 호출 (샤드당)
- 각 GetRecords 호출: 최대 1000개 레코드 또는 1MB
- 이벤트 소스 매핑을 사용하면 이러한 제한을 Lambda가 자동으로 관리합니다

## 실전 활용

### 주문 상태 변경 알림 시스템

주문 테이블의 상태가 변경되면 고객에게 자동으로 알림을 발송하는 시스템입니다.

```python
import json
import boto3

sns_client = boto3.client('sns')
ses_client = boto3.client('ses')

def lambda_handler(event, context):
    """DynamoDB Streams 이벤트를 처리하여 주문 상태 변경 알림을 발송합니다."""
    for record in event['Records']:
        if record['eventName'] not in ('MODIFY',):
            continue
        
        new_image = record['dynamodb'].get('NewImage', {})
        old_image = record['dynamodb'].get('OldImage', {})
        
        new_status = new_image.get('Status', {}).get('S', '')
        old_status = old_image.get('Status', {}).get('S', '')
        
        # 상태가 변경된 경우에만 처리
        if new_status == old_status:
            continue
        
        order_id = new_image['OrderId']['S']
        customer_email = new_image.get('CustomerEmail', {}).get('S', '')
        
        notification_map = {
            'CONFIRMED': '주문이 확인되었습니다.',
            'SHIPPED': '상품이 발송되었습니다.',
            'DELIVERED': '상품이 배달 완료되었습니다.',
            'CANCELLED': '주문이 취소되었습니다.'
        }
        
        message = notification_map.get(new_status)
        if message and customer_email:
            # SNS로 알림 발행
            sns_client.publish(
                TopicArn='arn:aws:sns:ap-northeast-2:123456789012:order-notifications',
                Subject=f'주문 상태 변경: {order_id}',
                Message=json.dumps({
                    'order_id': order_id,
                    'old_status': old_status,
                    'new_status': new_status,
                    'message': message
                })
            )
    
    return {'statusCode': 200, 'body': 'Processed successfully'}
```

### 실시간 집계 및 대시보드

변경 스트림을 활용하여 실시간 통계를 집계하는 패턴입니다.

```python
import boto3
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
stats_table = dynamodb.Table('OrderStatistics')

def lambda_handler(event, context):
    """주문 변경 스트림에서 실시간 통계를 집계합니다."""
    for record in event['Records']:
        event_name = record['eventName']
        new_image = record['dynamodb'].get('NewImage', {})
        old_image = record['dynamodb'].get('OldImage', {})
        
        if event_name == 'INSERT':
            # 새 주문: 총 주문 수와 매출 증가
            amount = Decimal(new_image.get('Amount', {}).get('N', '0'))
            category = new_image.get('Category', {}).get('S', 'unknown')
            
            stats_table.update_item(
                Key={'StatKey': 'daily-summary', 'Date': get_today()},
                UpdateExpression='ADD TotalOrders :one, TotalRevenue :amount',
                ExpressionAttributeValues={
                    ':one': 1,
                    ':amount': amount
                }
            )
            
            # 카테고리별 집계
            stats_table.update_item(
                Key={'StatKey': f'category-{category}', 'Date': get_today()},
                UpdateExpression='ADD OrderCount :one, Revenue :amount',
                ExpressionAttributeValues={
                    ':one': 1,
                    ':amount': amount
                }
            )
        
        elif event_name == 'MODIFY':
            new_status = new_image.get('Status', {}).get('S', '')
            if new_status == 'CANCELLED':
                amount = Decimal(new_image.get('Amount', {}).get('N', '0'))
                stats_table.update_item(
                    Key={'StatKey': 'daily-summary', 'Date': get_today()},
                    UpdateExpression='ADD CancelledOrders :one, CancelledRevenue :amount',
                    ExpressionAttributeValues={
                        ':one': 1,
                        ':amount': amount
                    }
                )

def get_today():
    from datetime import datetime
    return datetime.utcnow().strftime('%Y-%m-%d')
```

### 크로스 리전 데이터 복제

DynamoDB Global Tables을 사용하지 않는 경우, Streams를 활용하여 커스텀 리전 간 복제를 구현할 수 있습니다.

```bash
# Lambda 함수에 대상 리전의 DynamoDB 접근 권한 부여
aws lambda update-function-configuration \
  --function-name cross-region-replicator \
  --environment '{
    "Variables": {
      "TARGET_REGION": "us-east-1",
      "TARGET_TABLE": "Orders-Replica"
    }
  }'

# 이벤트 소스 매핑 생성
aws lambda create-event-source-mapping \
  --function-name cross-region-replicator \
  --event-source-arn arn:aws:dynamodb:ap-northeast-2:123456789012:table/Orders/stream/2026-03-23T00:00:00.000 \
  --batch-size 100 \
  --starting-position TRIM_HORIZON \
  --maximum-retry-attempts 5 \
  --bisect-batch-on-function-error
```

### Elasticsearch/OpenSearch 동기화

DynamoDB 데이터를 OpenSearch에 실시간으로 동기화하여 전문 검색을 제공합니다.

```bash
# Kinesis Data Firehose를 통한 OpenSearch 전송 설정
aws firehose create-delivery-stream \
  --delivery-stream-name dynamodb-to-opensearch \
  --delivery-stream-type KinesisStreamAsSource \
  --kinesis-stream-source-configuration '{
    "KinesisStreamARN": "arn:aws:kinesis:ap-northeast-2:123456789012:stream/dynamodb-changes-stream",
    "RoleARN": "arn:aws:iam::123456789012:role/FirehoseRole"
  }' \
  --amazon-opensearch-service-destination-configuration '{
    "DomainARN": "arn:aws:es:ap-northeast-2:123456789012:domain/search-domain",
    "IndexName": "orders",
    "TypeName": "_doc",
    "RoleARN": "arn:aws:iam::123456789012:role/FirehoseOpenSearchRole",
    "S3Configuration": {
      "BucketARN": "arn:aws:s3:::backup-bucket",
      "RoleARN": "arn:aws:iam::123456789012:role/FirehoseS3Role"
    }
  }'
```

## 모범 사례/보안

### 오류 처리

1. **Dead Letter Queue (DLQ) 설정**: Lambda 이벤트 소스 매핑에 DLQ를 설정하여 처리 실패한 레코드를 별도로 관리합니다.
2. **bisectBatchOnFunctionError 활성화**: 배치 내 특정 레코드로 인한 오류 시 배치를 절반으로 분할하여 재시도합니다.
3. **멱등성 보장**: 스트림 레코드는 최소 한 번(at-least-once) 전달되므로, 처리 로직이 멱등성을 갖도록 설계합니다.

### 성능 최적화

1. **배치 크기 조정**: `batch-size`를 워크로드에 맞게 조정합니다. 크게 설정하면 처리량이 높아지지만 지연이 증가합니다.
2. **배치 윈도우**: `maximum-batching-window-in-seconds`를 설정하여 일정 시간 동안 레코드를 모아서 처리합니다.
3. **병렬 처리**: `parallelization-factor`를 설정하여 샤드당 여러 Lambda 인스턴스를 동시에 실행합니다.

```bash
# 최적화된 이벤트 소스 매핑 설정
aws lambda update-event-source-mapping \
  --uuid abc123-def456-ghi789 \
  --batch-size 500 \
  --maximum-batching-window-in-seconds 5 \
  --parallelization-factor 5 \
  --maximum-retry-attempts 3 \
  --bisect-batch-on-function-error
```

### 보안

1. **IAM 최소 권한**: Lambda 실행 역할에 DynamoDB Streams 읽기 권한만 부여합니다.
2. **VPC 내 실행**: Lambda를 VPC 내에서 실행하여 네트워크 격리를 유지합니다.
3. **암호화**: DynamoDB 테이블 암호화가 활성화되면 스트림 레코드도 자동으로 암호화됩니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetRecords",
        "dynamodb:GetShardIterator",
        "dynamodb:DescribeStream",
        "dynamodb:ListStreams"
      ],
      "Resource": "arn:aws:dynamodb:ap-northeast-2:123456789012:table/Orders/stream/*"
    }
  ]
}
```

## 관련 서비스 비교

### DynamoDB Streams vs Kinesis Data Streams for DynamoDB

| 항목 | DynamoDB Streams | Kinesis Data Streams |
|------|-----------------|---------------------|
| 데이터 보존 | 24시간 | 최대 365일 |
| 소비자 수 | 2개 (동시 읽기 제한) | 다중 소비자 (Enhanced Fan-Out) |
| 처리량 | 자동 스케일링 | 샤드 기반 스케일링 |
| 비용 | 읽기 API 호출 비용 | Kinesis 사용 비용 |
| Kinesis 생태계 | 미지원 | Data Analytics, Firehose 통합 |
| 설정 복잡성 | 낮음 | 중간 |

### DynamoDB Streams vs EventBridge Pipes

EventBridge Pipes는 DynamoDB Streams를 소스로 사용하여 필터링, 변환, 라우팅을 수행할 수 있습니다. Lambda를 직접 작성하지 않고도 이벤트 처리 파이프라인을 구성할 수 있다는 장점이 있습니다.

### DynamoDB Streams vs RDS/Aurora CDC

RDS/Aurora에서는 AWS DMS를 통해 CDC를 구현합니다. DynamoDB Streams는 네이티브 CDC로 별도의 서비스 없이 바로 사용할 수 있으며, Lambda와의 통합이 매우 간편합니다.

## 요약

DynamoDB Streams는 DynamoDB 테이블의 항목 수준 변경 사항을 실시간으로 캡처하는 변경 데이터 캡처(CDC) 기능입니다. NEW_AND_OLD_IMAGES 모드를 사용하면 변경 전후의 전체 데이터를 확인할 수 있어, 상태 변경 감지, 감사 로깅, 실시간 집계 등 다양한 이벤트 기반 패턴을 구현할 수 있습니다.

Lambda 트리거를 통한 서버리스 이벤트 처리가 가장 일반적인 활용 패턴이며, 더 높은 처리량이나 긴 데이터 보존이 필요한 경우 Kinesis Data Streams를 사용할 수 있습니다. 멱등성 보장, DLQ 설정, 적절한 배치 크기 조정이 안정적인 스트림 처리의 핵심입니다.