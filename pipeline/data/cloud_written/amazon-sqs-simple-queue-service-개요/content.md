<!-- infographic-hero -->
![Amazon SQS 핵심 요약](figures/infographic.svg)

*Figure: Amazon SQS 한 장 요약 인포그래픽*

# Amazon SQS - 완전 관리형 메시지 큐 서비스 개요

## 개요

Amazon SQS(Simple Queue Service)는 AWS가 제공하는 완전 관리형 메시지 큐 서비스입니다. 2004년에 출시되어 AWS의 가장 오래된 서비스 중 하나로 꼽히며, 분산 시스템에서 컴포넌트 간 결합도를 낮추고 비동기 처리를 가능하게 하는 핵심 인프라 역할을 수행합니다.

전통적으로 메시지 큐는 RabbitMQ, ActiveMQ, Kafka 등 자체 구축이 필요했고, 클러스터 운영, 장애 복구, 스케일링이 모두 운영자의 책임이었습니다. SQS는 이 모든 운영 부담을 AWS가 가져가고, 사용자는 큐 생성과 메시지 송수신 API만 호출하면 무제한 처리량과 높은 가용성을 보장받을 수 있습니다.

SQS의 핵심 가치는 다음과 같이 요약됩니다.

- **느슨한 결합(Loose Coupling)**: Producer와 Consumer가 서로의 가용성에 영향을 받지 않습니다.
- **무제한 처리량**: Standard 큐는 거의 무제한 TPS를 지원하며, 자동으로 스케일링됩니다.
- **운영 부담 제거**: 인프라 프로비저닝, 패치, 장애 복구를 사용자가 수행할 필요가 없습니다.
- **AWS 통합**: Lambda, ECS, Step Functions, EventBridge와 네이티브 통합됩니다.

---

## 핵심 기능

### 1. 큐 종류 - Standard vs FIFO

SQS는 두 가지 유형의 큐를 제공하며, 각각 트레이드오프가 명확합니다.

| 항목 | Standard 큐 | FIFO 큐 |
|------|-------------|---------|
| 전달 보장 | At-least-once (중복 발생 가능) | Exactly-once |
| 순서 보장 | Best-effort (순서 X) | MessageGroupId 단위 보장 |
| 처리량 | 무제한 TPS | 300 TPS (배치 시 3,000 TPS), High Throughput Mode 시 70K+ |
| 가격 | 100만 요청당 $0.40 | 100만 요청당 $0.50 |
| 사용 사례 | 멱등(Idempotent) 처리, 로그 수집, Fanout | 결제, 주문 처리, 트랜잭션 |

Standard 큐는 메시지가 두 번 이상 전달될 수 있으므로 Consumer 측에서 멱등성(Idempotency)을 보장해야 합니다. FIFO 큐는 5분 중복 제거 윈도우 내에서 동일한 MessageDeduplicationId를 가진 메시지를 자동으로 제거합니다.

### 2. Visibility Timeout

Visibility Timeout은 메시지가 Consumer에게 전달된 후 일정 시간 동안 다른 Consumer에게 보이지 않도록 숨기는 메커니즘입니다.

- 기본값: 30초
- 최대값: 12시간 (43,200초)
- 처리 완료 시 Consumer가 명시적으로 `DeleteMessage`를 호출해야 큐에서 제거됩니다.
- 처리 중 타임아웃이 임박하면 `ChangeMessageVisibility`로 연장 가능합니다.

```bash
# Visibility Timeout이 60초인 큐 생성
aws sqs create-queue \
  --queue-name my-task-queue \
  --attributes VisibilityTimeout=60,MessageRetentionPeriod=345600 \
  --region ap-northeast-2

# 처리 중 Visibility 연장 (예: 30초 더)
aws sqs change-message-visibility \
  --queue-url https://sqs.ap-northeast-2.amazonaws.com/123456789012/my-task-queue \
  --receipt-handle "AQEBwJnKyrHigUMZj6rYigCgxlaS3Sj..." \
  --visibility-timeout 90 \
  --region ap-northeast-2
```

처리 시간이 Visibility Timeout보다 길어지면 동일 메시지가 다른 Consumer에게 다시 전달되어 중복 처리가 발생합니다. 따라서 처리 시간 분포의 P99에 안전 마진을 더해 설정하는 것이 권장됩니다.

### 3. Long Polling

Long Polling은 큐가 비어 있을 때 Consumer의 ReceiveMessage 응답을 일정 시간 지연시켜 빈 응답(empty receive)을 줄이고 비용을 절감하는 기능입니다.

- 기본값: 0초 (Short Polling)
- 최대값: 20초

```bash
# Long Polling 활성화 (큐 속성)
aws sqs set-queue-attributes \
  --queue-url https://sqs.ap-northeast-2.amazonaws.com/123456789012/my-task-queue \
  --attributes ReceiveMessageWaitTimeSeconds=20 \
  --region ap-northeast-2

# 또는 ReceiveMessage 호출 시 지정
aws sqs receive-message \
  --queue-url https://sqs.ap-northeast-2.amazonaws.com/123456789012/my-task-queue \
  --wait-time-seconds 20 \
  --max-number-of-messages 10 \
  --region ap-northeast-2
```

Short Polling은 평균적으로 빈 응답이 많이 발생하여 API 호출 비용이 증가합니다. 거의 모든 프로덕션 환경에서는 Long Polling 20초가 권장됩니다.

### 4. Dead Letter Queue (DLQ)

DLQ는 일정 횟수 이상 처리에 실패한 메시지를 격리하는 별도의 큐입니다. 무한 재시도 루프를 방지하고, 실패 메시지를 분석하여 버그를 추적하는 데 사용됩니다.

```bash
# DLQ 생성
aws sqs create-queue \
  --queue-name my-task-queue-dlq \
  --region ap-northeast-2

# 원본 큐에 RedrivePolicy 적용 (3회 실패 시 DLQ로)
aws sqs set-queue-attributes \
  --queue-url https://sqs.ap-northeast-2.amazonaws.com/123456789012/my-task-queue \
  --attributes '{
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:ap-northeast-2:123456789012:my-task-queue-dlq\",\"maxReceiveCount\":\"3\"}"
  }' \
  --region ap-northeast-2
```

2021년 출시된 DLQ Redrive 기능을 사용하면 콘솔에서 클릭 몇 번으로 DLQ 메시지를 원본 큐로 다시 보낼 수 있습니다.

### 5. 메시지 크기와 보존 기간

- **메시지 크기**: 최대 256KB. SQS Extended Client Library를 사용하면 S3에 페이로드를 저장하고 SQS에는 참조만 보내 최대 2GB까지 처리 가능합니다.
- **보존 기간(Message Retention)**: 1분 ~ 14일 (기본 4일).
- **메시지 그룹 한도**: FIFO에서 MessageGroupId 단위로 순서가 보장되므로, 그룹 수가 많을수록 병렬 처리량이 늘어납니다.

```python
# Python boto3로 메시지 송신
import boto3
import json

sqs = boto3.client('sqs', region_name='ap-northeast-2')

response = sqs.send_message(
    QueueUrl='https://sqs.ap-northeast-2.amazonaws.com/123456789012/my-task-queue',
    MessageBody=json.dumps({
        'task_id': 'task-001',
        'user_id': 12345,
        'action': 'process_order'
    }),
    MessageAttributes={
        'TaskType': {
            'StringValue': 'OrderProcessing',
            'DataType': 'String'
        }
    }
)
print(f"Sent message ID: {response['MessageId']}")
```

---

## 아키텍처 / 동작 원리

### SQS 내부 동작

SQS는 AWS 내부적으로 다중 AZ에 메시지를 복제하여 저장합니다. 메시지 흐름은 다음과 같습니다.

```text
[Producer]
    |
    v  SendMessage API
[SQS Queue (multi-AZ replicated)]
    |
    v  ReceiveMessage API
[Consumer]
    |  처리
    v  DeleteMessage API
[Queue에서 제거]
```

1. **Producer**가 `SendMessage`를 호출하면 메시지가 큐에 저장됩니다.
2. **Consumer**가 `ReceiveMessage`로 메시지를 polling합니다. 메시지 전달 시 Visibility Timeout이 시작됩니다.
3. Consumer가 처리를 완료하면 `DeleteMessage`로 큐에서 제거합니다.
4. 처리에 실패하거나 타임아웃되면 메시지가 다시 보이게 되어 다른 Consumer에게 전달됩니다.
5. `maxReceiveCount`를 초과하면 DLQ로 이동합니다.

### Lambda Event Source Mapping

SQS는 Lambda와 네이티브 통합됩니다. Lambda는 내부적으로 SQS를 polling하여 메시지를 받아 함수를 트리거합니다.

```bash
# Lambda에 SQS 트리거 추가
aws lambda create-event-source-mapping \
  --function-name my-task-processor \
  --event-source-arn arn:aws:sqs:ap-northeast-2:123456789012:my-task-queue \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 5 \
  --region ap-northeast-2
```

- **Batch Size**: 한 번에 받는 메시지 수 (Standard 최대 10,000, FIFO 최대 10).
- **Batching Window**: 메시지가 배치 크기에 미치지 못해도 대기할 최대 시간.
- **Partial Batch Response**: 2021년부터 배치 내 일부 메시지만 실패 처리하도록 응답 가능.

```python
# Lambda 핸들러 (Partial Batch Response)
def lambda_handler(event, context):
    failed_message_ids = []
    for record in event['Records']:
        try:
            body = json.loads(record['body'])
            process_task(body)
        except Exception as e:
            print(f"Failed: {record['messageId']}, error: {e}")
            failed_message_ids.append({
                'itemIdentifier': record['messageId']
            })
    return {'batchItemFailures': failed_message_ids}
```

### Visibility Timeout과 동시성

여러 Consumer가 같은 큐를 polling할 때, Visibility Timeout이 메시지의 동시 처리를 방지합니다.

```text
시간 t=0:  Consumer A가 메시지 M을 ReceiveMessage
          → M의 Visibility Timeout 시작 (30초)
시간 t=10: Consumer B가 ReceiveMessage 시도
          → M은 보이지 않음 → 다른 메시지를 받거나 빈 응답
시간 t=25: Consumer A가 DeleteMessage 호출 → M 제거
시간 t=35: 만약 Consumer A가 DeleteMessage 실패했다면
          → M이 다시 보이게 되어 Consumer B에게 전달
```

---

## 실전 사용

### 1. Producer-Consumer 패턴 (Python boto3)

```python
import boto3
import json
import time

sqs = boto3.client('sqs', region_name='ap-northeast-2')
QUEUE_URL = 'https://sqs.ap-northeast-2.amazonaws.com/123456789012/my-task-queue'

def producer(tasks):
    """배치로 메시지 전송 (최대 10개)"""
    entries = [
        {
            'Id': str(i),
            'MessageBody': json.dumps(task)
        }
        for i, task in enumerate(tasks)
    ]
    response = sqs.send_message_batch(
        QueueUrl=QUEUE_URL,
        Entries=entries
    )
    return response

def consumer():
    """Long Polling으로 메시지 수신 및 처리"""
    while True:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
            VisibilityTimeout=60
        )
        messages = response.get('Messages', [])
        if not messages:
            continue

        for msg in messages:
            try:
                body = json.loads(msg['Body'])
                process_task(body)
                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=msg['ReceiptHandle']
                )
            except Exception as e:
                print(f"Processing failed: {e}")

def process_task(task):
    print(f"Processing: {task}")
    time.sleep(1)
```

### 2. FIFO 큐로 순서 보장 처리

```python
# FIFO 큐 생성 (큐 이름은 .fifo로 끝나야 함)
sqs.create_queue(
    QueueName='order-processing.fifo',
    Attributes={
        'FifoQueue': 'true',
        'ContentBasedDeduplication': 'true',
        'DeduplicationScope': 'messageGroup',
        'FifoThroughputLimit': 'perMessageGroupId'
    }
)

# 순서가 중요한 메시지는 동일한 MessageGroupId 사용
sqs.send_message(
    QueueUrl='https://sqs.ap-northeast-2.amazonaws.com/123456789012/order-processing.fifo',
    MessageBody=json.dumps({'order_id': 1001, 'event': 'created'}),
    MessageGroupId='customer-12345',
    MessageDeduplicationId='order-1001-created'
)
```

`DeduplicationScope=messageGroup` + `FifoThroughputLimit=perMessageGroupId`를 함께 설정하면 High Throughput Mode가 활성화되어 그룹별 70,000+ TPS까지 처리 가능합니다.

### 3. SNS와 통합한 Fanout 패턴

[[amazon-sns-simple-notification-service-개요|Amazon SNS]] Topic에 SQS 큐들을 구독시키면, 단일 publish가 여러 큐로 전달되는 Fanout 패턴을 구성할 수 있습니다.

```bash
# SNS Topic 구독 (각 SQS 큐를 개별 구독)
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-northeast-2:123456789012:order-events \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:ap-northeast-2:123456789012:billing-queue \
  --region ap-northeast-2

aws sns subscribe \
  --topic-arn arn:aws:sns:ap-northeast-2:123456789012:order-events \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:ap-northeast-2:123456789012:notification-queue \
  --region ap-northeast-2
```

이 패턴의 장점은 각 Consumer가 자신의 처리 속도로 메시지를 소비할 수 있다는 점입니다. SNS만으로는 직접 push 방식이라 Consumer 가용성에 영향을 받지만, SQS를 중간에 두면 메시지가 큐에 쌓여 보존됩니다.

---

## 가격 / 한도

### 가격 (us-east-1 기준)

| 항목 | 가격 |
|------|------|
| Standard 큐 요청 | 100만 요청당 $0.40 |
| FIFO 큐 요청 | 100만 요청당 $0.50 |
| 무료 티어 | 매월 100만 요청 무료 |
| 데이터 전송 (Outbound) | 표준 AWS 데이터 전송 요금 적용 |
| Extended Client (S3 백업) | S3 스토리지 + 요청 비용 별도 |

### 주요 한도

| 항목 | 한도 |
|------|------|
| 메시지 크기 | 256KB (Extended Library 사용 시 2GB) |
| 메시지 보존 기간 | 1분 ~ 14일 (기본 4일) |
| Visibility Timeout | 0초 ~ 12시간 |
| 큐당 in-flight 메시지 | Standard 120,000 / FIFO 20,000 |
| ReceiveMessage 배치 크기 | 최대 10 |
| FIFO TPS | 300 (배치 미사용), 3,000 (배치), High Throughput Mode 시 70K+ |
| SendMessageBatch 페이로드 | 256KB |

---

## Best Practice

### 1. 멱등성 보장

Standard 큐는 At-least-once 전달을 보장하므로 Consumer는 반드시 멱등하게 작성해야 합니다.

```python
import hashlib

def process_message_idempotent(message):
    # 메시지 해시 기반 처리 ID 생성
    msg_hash = hashlib.sha256(message['Body'].encode()).hexdigest()

    # 이미 처리된 메시지인지 DynamoDB에서 확인
    if dynamodb.get_item(Key={'msg_hash': msg_hash}):
        return  # 이미 처리됨, skip

    # 처리 + 처리 기록을 트랜잭션으로
    process_business_logic(message)
    dynamodb.put_item(Item={'msg_hash': msg_hash, 'ttl': time.time() + 86400})
```

### 2. Visibility Timeout 적정값 설정

- 처리 시간 P99 + 안전 마진 (예: 50%)으로 설정합니다.
- 처리가 길어질 가능성이 있다면 `change-message-visibility`로 동적으로 연장합니다.

### 3. DLQ + CloudWatch Alarm 조합

DLQ에 메시지가 쌓이면 [[amazon-cloudwatch-모니터링-서비스-개요|CloudWatch Alarm]]으로 즉시 알림을 받을 수 있습니다.

```bash
# DLQ에 메시지가 1개 이상이면 알람
aws cloudwatch put-metric-alarm \
  --alarm-name sqs-dlq-has-messages \
  --metric-name ApproximateNumberOfMessagesVisible \
  --namespace AWS/SQS \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=QueueName,Value=my-task-queue-dlq \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:ops-alerts \
  --region ap-northeast-2
```

### 4. 보안 - VPC Endpoint와 KMS 암호화

- **VPC Endpoint(Interface Endpoint)**: SQS 트래픽을 인터넷으로 나가지 않고 AWS 내부 네트워크로 처리합니다.
- **SSE-SQS / SSE-KMS**: 메시지 본문을 저장 시 암호화합니다.
- **IAM 정책**: 큐 접근을 최소 권한으로 제한합니다.

```bash
# KMS 암호화 큐 생성
aws sqs create-queue \
  --queue-name my-encrypted-queue \
  --attributes '{
    "KmsMasterKeyId": "alias/aws/sqs",
    "KmsDataKeyReusePeriodSeconds": "300"
  }' \
  --region ap-northeast-2
```

### 5. 모니터링 핵심 지표

| 지표 | 의미 | 알람 기준 |
|------|------|-----------|
| ApproximateNumberOfMessagesVisible | 큐에 대기 중인 메시지 수 | 임계치 초과 시 Consumer 부족 |
| ApproximateAgeOfOldestMessage | 가장 오래된 메시지 나이 | 처리 지연 감지 |
| NumberOfMessagesSent / Received | 송수신 처리량 | 비정상 트래픽 감지 |
| ApproximateNumberOfMessagesNotVisible | in-flight 메시지 수 | Visibility Timeout 적정성 검증 |

---

## 관련 서비스 비교

### SQS vs SNS vs Kinesis

| 항목 | Amazon SQS | Amazon SNS | Amazon Kinesis Data Streams |
|------|-----------|-----------|------------------------------|
| 모델 | 메시지 큐 (Pull) | Pub/Sub (Push) | 스트림 (Pull, 재처리 가능) |
| 전달 보장 | At-least-once / Exactly-once(FIFO) | At-least-once | At-least-once |
| 메시지 보존 | 1분 ~ 14일 | 미보존 (즉시 전달) | 1 ~ 365일 |
| 다중 Consumer | 큐 1개당 단일 Consumer (다중 Consumer는 SNS+SQS Fanout) | 다중 구독자 | 다중 Consumer (재처리 가능) |
| 순서 보장 | FIFO 큐만 | FIFO Topic만 | Shard 단위 보장 |
| 처리량 | 무제한 (Standard) | 무제한 (Standard) | Shard당 1MB/s 또는 1,000 records/s |
| 가격 | 요청 수 기반 | 요청 수 기반 | Shard 시간당 + 요청 수 |
| 적합 용도 | 작업 큐, 비동기 처리 | 알림, Fanout, 모바일 푸시 | 이벤트 스트림, 분석, 재처리 |

**선택 기준**

- **SQS**: 작업을 하나의 Consumer가 처리하고 끝내는 경우 (작업 큐)
- **SNS**: 한 이벤트를 여러 시스템이 동시에 받아야 하지만 보존이 필요 없는 경우
- **SNS + SQS**: 한 이벤트를 여러 Consumer가 자기 페이스로 처리해야 하는 경우 (Fanout)
- **Kinesis**: 이벤트를 시간순으로 보존하면서 다수 Consumer가 재처리할 수 있어야 하는 경우 (분석, ML)

### SQS vs Amazon MQ

| 항목 | SQS | Amazon MQ |
|------|-----|-----------|
| 프로토콜 | AWS 독자 API | AMQP, MQTT, STOMP, OpenWire (RabbitMQ/ActiveMQ) |
| 마이그레이션 | 코드 변경 필요 | 기존 AMQP/JMS 코드 그대로 |
| 운영 | Serverless | 브로커 인스턴스 관리 필요 |
| 가격 | 요청당 | 인스턴스 시간당 |

기존 RabbitMQ/ActiveMQ를 사용하던 시스템을 AWS로 옮길 때는 코드 호환성을 위해 Amazon MQ가 유리합니다. 신규 시스템이라면 SQS가 운영 부담과 비용 측면에서 우수합니다.

---

## 관련 문서

- [[amazon-sns-simple-notification-service-개요|Amazon SNS]] - SQS와 함께 Fanout 패턴 구성
- [[amazon-cloudwatch-모니터링-서비스-개요|Amazon CloudWatch]] - SQS 큐 모니터링 및 DLQ 알람
- [[aws-cloudformation-iac-개요|AWS CloudFormation]] - SQS 큐를 IaC로 관리

---

## 요약

Amazon SQS는 분산 시스템의 비동기 메시지 큐 인프라로 가장 널리 쓰이는 AWS 서비스입니다. 핵심 포인트를 정리하면 다음과 같습니다.

1. **Standard 큐는 무제한 처리량**과 At-least-once 전달, **FIFO 큐는 순서 보장과 Exactly-once**를 제공합니다.
2. **Visibility Timeout**으로 메시지 중복 처리를 방지하고, **Long Polling**으로 비용을 절감합니다.
3. **DLQ**로 처리 실패 메시지를 격리하고, **CloudWatch Alarm**과 결합하여 운영 가시성을 확보합니다.
4. **Lambda Event Source Mapping**으로 서버리스 아키텍처를 손쉽게 구성할 수 있습니다.
5. **SNS + SQS Fanout** 패턴으로 한 이벤트를 여러 Consumer가 안전하게 받을 수 있습니다.
6. 멱등성 보장, 적정 Visibility Timeout, KMS 암호화는 운영 안정성의 핵심입니다.

SQS는 가장 단순하면서도 가장 강력한 AWS 통합 서비스 중 하나이며, 모든 이벤트 기반 아키텍처의 기본 빌딩 블록으로 활용됩니다.
