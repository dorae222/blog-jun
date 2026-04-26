<!-- infographic-hero -->
![Amazon SNS 핵심 요약](figures/infographic.svg)

*Figure: Amazon SNS 한 장 요약 인포그래픽*

# Amazon SNS - 완전 관리형 Pub/Sub 메시징 서비스 개요

## 개요

Amazon SNS(Simple Notification Service)는 AWS가 제공하는 완전 관리형 Pub/Sub(Publish/Subscribe) 메시징 서비스입니다. 2010년에 출시되었으며, 단일 메시지를 다수의 구독자에게 동시에 전달하는 분산 메시징의 핵심 인프라 역할을 수행합니다.

[[amazon-sqs-simple-queue-service-개요|Amazon SQS]]가 일대일 메시지 큐(Producer가 보낸 메시지를 단일 Consumer가 처리)에 적합하다면, SNS는 일대다(Fanout) 모델에 최적화되어 있습니다. SNS Topic에 메시지를 publish하면 모든 구독자(Subscriber)에게 동시에 push됩니다.

SNS의 핵심 가치는 다음과 같습니다.

- **다중 프로토콜 지원**: SQS, Lambda, HTTP/HTTPS, Email, SMS, Mobile Push, Kinesis Data Firehose 등 다양한 엔드포인트로 전달 가능합니다.
- **Push 기반 전달**: 구독자가 polling할 필요 없이 SNS가 자동으로 메시지를 전송합니다.
- **Fanout 패턴**: 1번의 publish로 N개의 구독자에게 메시지가 분산됩니다.
- **AWS 통합**: CloudWatch Alarm, S3 Event, EC2 Auto Scaling 등 AWS 서비스의 알림 채널로 자주 사용됩니다.

---

## 핵심 기능

### 1. Topic 종류 - Standard vs FIFO

SNS는 두 가지 Topic 유형을 제공합니다.

| 항목 | Standard Topic | FIFO Topic |
|------|----------------|------------|
| 처리량 | 무제한 (스로틀링 없음) | 300 publish/s (배치 시 3,000) |
| 순서 보장 | Best-effort (X) | MessageGroupId 단위 보장 |
| 중복 제거 | 없음 | 5분 윈도우 내 자동 |
| 구독 가능 프로토콜 | 모든 프로토콜 | SQS FIFO 큐만 |
| 가격 | 100만 요청당 $0.50 | 100만 요청당 $0.50 + 별도 처리 비용 |

FIFO Topic은 2020년에 출시되었으며, 결제, 주문, 트랜잭션 같이 순서가 중요한 도메인에 사용됩니다. 단, 구독자가 SQS FIFO 큐로 제한된다는 점에 유의해야 합니다.

### 2. 구독자(Subscriber) 프로토콜

SNS는 다음 프로토콜로 메시지를 전달할 수 있습니다.

| 프로토콜 | 용도 | 특징 |
|---------|------|------|
| Amazon SQS | 비동기 처리, Fanout | 가장 보편적인 패턴 |
| AWS Lambda | 서버리스 함수 트리거 | 자동 스케일링 |
| HTTP/HTTPS | 외부 웹훅 | 재시도 정책 설정 가능 |
| Email / Email-JSON | 사람에게 알림 | 구독 확인 필요 |
| SMS | 모바일 텍스트 메시지 | 국가별 가격 차등 |
| Mobile Push | 푸시 알림 | APNs, FCM, Baidu, ADM 지원 |
| Kinesis Data Firehose | 데이터 레이크 적재 | S3, Redshift, OpenSearch로 전달 |

### 3. Fanout 패턴

가장 자주 사용되는 패턴은 SNS → 다수 SQS 큐 Fanout입니다.

```text
                    [SNS Topic: order-events]
                            |
              +-------------+-------------+
              |             |             |
              v             v             v
      [SQS: billing]  [SQS: shipping]  [SQS: notification]
              |             |             |
              v             v             v
        [Lambda A]    [Lambda B]    [Lambda C]
```

이 구조의 장점은 다음과 같습니다.

- 각 Consumer가 자신의 처리 속도로 메시지를 소비할 수 있습니다.
- 구독자 추가가 Producer 코드 변경 없이 가능합니다.
- 한 Consumer의 장애가 다른 Consumer에 영향을 주지 않습니다.

```bash
# SNS Topic 생성
aws sns create-topic \
  --name order-events \
  --region ap-northeast-2

# SQS 큐를 Topic에 구독
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-northeast-2:123456789012:order-events \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:ap-northeast-2:123456789012:billing-queue \
  --region ap-northeast-2

# 메시지 publish
aws sns publish \
  --topic-arn arn:aws:sns:ap-northeast-2:123456789012:order-events \
  --message '{"order_id": 1001, "amount": 50000}' \
  --message-attributes '{
    "EventType": {"DataType": "String", "StringValue": "OrderCreated"}
  }' \
  --region ap-northeast-2
```

### 4. Message Filtering

Message Filtering은 구독자별로 받을 메시지를 JSON 정책으로 필터링하는 기능입니다. 각 구독자가 자기 관심사 메시지만 받도록 하여, Producer가 단일 Topic에 모든 이벤트를 보내도 Consumer 측에서 분리할 수 있습니다.

```bash
# 구독에 필터 정책 적용 (OrderCreated 이벤트만 받도록)
aws sns set-subscription-attributes \
  --subscription-arn arn:aws:sns:ap-northeast-2:123456789012:order-events:abc-123 \
  --attribute-name FilterPolicy \
  --attribute-value '{
    "EventType": ["OrderCreated", "OrderUpdated"],
    "amount": [{"numeric": [">=", 10000]}]
  }' \
  --region ap-northeast-2
```

지원하는 연산자.

- 값 일치: `["A", "B"]`
- prefix: `[{"prefix": "USA"}]`
- 숫자 비교: `[{"numeric": [">=", 100]}]`, `[{"numeric": ["<", 100]}]`
- exists: `[{"exists": true}]`
- anything-but: `[{"anything-but": "X"}]`

기본은 Message Attribute 기반 필터링이지만, 2023년부터 메시지 본문(Payload) 기반 필터링도 지원됩니다.

### 5. Dead Letter Queue (DLQ)

SNS 구독별로 DLQ를 설정하여 전달 실패 메시지를 격리할 수 있습니다.

```bash
# 구독에 DLQ 설정
aws sns set-subscription-attributes \
  --subscription-arn arn:aws:sns:ap-northeast-2:123456789012:order-events:abc-123 \
  --attribute-name RedrivePolicy \
  --attribute-value '{
    "deadLetterTargetArn": "arn:aws:sqs:ap-northeast-2:123456789012:sns-dlq"
  }' \
  --region ap-northeast-2
```

HTTP/HTTPS 엔드포인트는 재시도 정책(Delivery Retry Policy)을 별도로 설정 가능하며, 기본적으로 3회 fast retry + 50회 backoff retry로 약 23일간 재시도합니다.

### 6. Mobile Push와 SMS

SNS는 모바일 푸시 알림을 위한 통합 인터페이스를 제공합니다.

| 플랫폼 | 서비스 |
|--------|--------|
| iOS | APNs (Apple Push Notification service) |
| Android | FCM (Firebase Cloud Messaging) |
| Amazon Fire | ADM (Amazon Device Messaging) |
| 중국 Android | Baidu Cloud Push |

```bash
# Platform Application 생성 (FCM)
aws sns create-platform-application \
  --name MyAndroidApp \
  --platform GCM \
  --attributes PlatformCredential=YOUR_FCM_SERVER_KEY \
  --region ap-northeast-2

# 디바이스 등록
aws sns create-platform-endpoint \
  --platform-application-arn arn:aws:sns:ap-northeast-2:123456789012:app/GCM/MyAndroidApp \
  --token DEVICE_TOKEN_FROM_FCM \
  --region ap-northeast-2

# 푸시 발송
aws sns publish \
  --target-arn arn:aws:sns:ap-northeast-2:123456789012:endpoint/GCM/MyAndroidApp/abc \
  --message-structure json \
  --message '{"GCM": "{\"notification\":{\"title\":\"안녕하세요\",\"body\":\"새 메시지\"}}"}' \
  --region ap-northeast-2
```

SMS는 두 가지 타입으로 발송됩니다.

- **Transactional**: OTP, 계정 보안 등 중요 메시지. 전달 신뢰도 높음, 가격 높음.
- **Promotional**: 마케팅 메시지. 비용 절감을 위해 일부 캐리어 우회.

```bash
# SMS 직접 발송 (Topic 없이)
aws sns publish \
  --phone-number "+821012345678" \
  --message "인증번호는 123456 입니다" \
  --message-attributes '{
    "AWS.SNS.SMS.SMSType": {"DataType": "String", "StringValue": "Transactional"}
  }' \
  --region ap-northeast-2
```

---

## 아키텍처 / 동작 원리

### SNS 메시지 전달 흐름

```text
[Publisher]
    |
    v  Publish API
[SNS Topic]
    |
    +--> Filter Policy 평가 (구독별)
    |
    v  Push 전달
[다수 Subscribers (병렬)]
    |
    +--> SQS / Lambda / HTTP / Email / SMS / Push
    |
    +--> 실패 시 재시도 → DLQ
```

1. **Publisher**가 `Publish` API를 호출하면 메시지가 Topic에 도착합니다.
2. SNS는 모든 구독자를 병렬로 순회하며 Filter Policy를 평가합니다.
3. 통과한 구독자에게 push 방식으로 전달합니다.
4. 전달 실패 시 프로토콜별 재시도 정책에 따라 재전송하고, 최종 실패 시 DLQ로 이동합니다.

### Cross-Account / Cross-Region

SNS Topic은 다른 AWS 계정의 SQS 큐나 Lambda 함수도 구독자로 받을 수 있습니다. 이때 Topic의 액세스 정책(Resource Policy)에 권한을 부여해야 합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "AllowCrossAccountSubscribe",
    "Effect": "Allow",
    "Principal": {"AWS": "arn:aws:iam::999999999999:root"},
    "Action": "sns:Subscribe",
    "Resource": "arn:aws:sns:ap-northeast-2:123456789012:order-events"
  }]
}
```

### Message Attribute vs Message Body

SNS 메시지는 본문(Body)과 별개로 Message Attribute를 가질 수 있습니다.

- **Body**: 실제 페이로드. 최대 256KB.
- **Attributes**: 메타데이터 키-값 쌍. 최대 10개. 필터링과 라우팅에 활용.

```python
import boto3

sns = boto3.client('sns', region_name='ap-northeast-2')

sns.publish(
    TopicArn='arn:aws:sns:ap-northeast-2:123456789012:order-events',
    Message=json.dumps({
        'order_id': 1001,
        'customer_id': 12345,
        'amount': 50000
    }),
    MessageAttributes={
        'EventType': {
            'DataType': 'String',
            'StringValue': 'OrderCreated'
        },
        'Region': {
            'DataType': 'String',
            'StringValue': 'KR'
        },
        'Priority': {
            'DataType': 'Number',
            'StringValue': '1'
        }
    }
)
```

---

## 실전 사용

### 1. CloudWatch Alarm + SNS 알림 패턴

[[amazon-cloudwatch-모니터링-서비스-개요|CloudWatch Alarm]]이 발생했을 때 SNS Topic에 publish하면 다양한 채널(Email, Slack, PagerDuty 등)로 알림을 보낼 수 있습니다.

```bash
# 1. SNS Topic 생성
aws sns create-topic --name ops-alerts --region ap-northeast-2

# 2. Email 구독 (확인 메일 클릭 필요)
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-northeast-2:123456789012:ops-alerts \
  --protocol email \
  --notification-endpoint ops-team@example.com \
  --region ap-northeast-2

# 3. Slack 알림용 Lambda 구독 (HTTP webhook 호출)
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-northeast-2:123456789012:ops-alerts \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:ap-northeast-2:123456789012:function:slack-notifier \
  --region ap-northeast-2

# 4. CloudWatch Alarm이 SNS Topic으로 발송
aws cloudwatch put-metric-alarm \
  --alarm-name high-cpu-alarm \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:ops-alerts \
  --region ap-northeast-2
```

### 2. SNS + SQS Fanout 구현 (Python)

```python
import boto3
import json

sns = boto3.client('sns', region_name='ap-northeast-2')
sqs = boto3.client('sqs', region_name='ap-northeast-2')

# Topic 생성
topic_arn = sns.create_topic(Name='order-events')['TopicArn']

# 큐들 생성
billing_queue_url = sqs.create_queue(QueueName='billing-queue')['QueueUrl']
shipping_queue_url = sqs.create_queue(QueueName='shipping-queue')['QueueUrl']

# 큐 ARN 조회
billing_queue_arn = sqs.get_queue_attributes(
    QueueUrl=billing_queue_url,
    AttributeNames=['QueueArn']
)['Attributes']['QueueArn']

# SNS가 SQS에 메시지를 보낼 수 있도록 큐 정책 설정
queue_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "sns.amazonaws.com"},
        "Action": "sqs:SendMessage",
        "Resource": billing_queue_arn,
        "Condition": {
            "ArnEquals": {"aws:SourceArn": topic_arn}
        }
    }]
}
sqs.set_queue_attributes(
    QueueUrl=billing_queue_url,
    Attributes={'Policy': json.dumps(queue_policy)}
)

# 구독 (Filter 적용)
sns.subscribe(
    TopicArn=topic_arn,
    Protocol='sqs',
    Endpoint=billing_queue_arn,
    Attributes={
        'FilterPolicy': json.dumps({
            'EventType': ['OrderCreated', 'PaymentCompleted']
        }),
        'RawMessageDelivery': 'true'  # SNS 메타데이터 없이 본문만 전달
    }
)

# 메시지 발행
sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps({'order_id': 1001, 'amount': 50000}),
    MessageAttributes={
        'EventType': {'DataType': 'String', 'StringValue': 'OrderCreated'}
    }
)
```

`RawMessageDelivery=true`를 설정하면 SNS가 추가하는 메타데이터 래퍼 없이 원본 메시지만 SQS에 전달됩니다. Lambda나 처리 로직에서 파싱이 단순해집니다.

### 3. Kinesis Data Firehose로 데이터 레이크 적재

2021년 출시된 기능으로 SNS 메시지를 Firehose를 거쳐 S3, Redshift, OpenSearch에 자동 적재할 수 있습니다.

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-northeast-2:123456789012:order-events \
  --protocol firehose \
  --notification-endpoint arn:aws:firehose:ap-northeast-2:123456789012:deliverystream/order-events-to-s3 \
  --attributes '{"SubscriptionRoleArn": "arn:aws:iam::123456789012:role/SNSToFirehose"}' \
  --region ap-northeast-2
```

이 패턴은 이벤트 기반 분석 파이프라인 구축에 유용하며, EventBridge Pipes의 등장 이전에는 가장 간단한 방법이었습니다.

---

## 가격 / 한도

### 가격 (us-east-1 기준)

| 항목 | 가격 |
|------|------|
| Standard Topic 요청 | 100만 요청당 $0.50 |
| FIFO Topic 발행 | 100만 요청당 $0.30 + 페이로드당 $0.017/GB |
| 무료 티어 | 매월 100만 publish 무료 |
| HTTP/HTTPS 전달 | 10만건당 $0.60 |
| Email / Email-JSON | 10만건당 $2.00 |
| SMS (한국) | 건당 약 $0.0653 (캐리어/타입 따라 변동) |
| Mobile Push | 100만건당 $0.50 |

### 주요 한도

| 항목 | 한도 |
|------|------|
| Topic당 구독 수 | 12,500,000 |
| 메시지 크기 | 256KB (SMS는 140 bytes/segment) |
| Message Attribute 수 | 10 |
| 계정당 Topic 수 | 100,000 (확장 가능) |
| FIFO publish 처리량 | 300/s (배치 시 3,000/s) |
| 필터 정책 크기 | 256KB |

---

## Best Practice

### 1. Idempotency 보장

Standard Topic은 At-least-once 전달이므로 구독자가 동일 메시지를 두 번 받을 수 있습니다. SQS Consumer와 마찬가지로 멱등성을 보장해야 합니다.

### 2. RawMessageDelivery 활용

SQS 구독 시 `RawMessageDelivery=true`로 설정하면 SNS의 JSON 래핑 없이 원본 메시지만 전달되어 Consumer 코드가 단순해집니다.

```python
# RawMessageDelivery=false (기본): SNS 래핑됨
{
  "Type": "Notification",
  "MessageId": "...",
  "TopicArn": "...",
  "Message": "{\"order_id\": 1001}",
  "Timestamp": "2024-01-15T10:00:00.000Z",
  ...
}

# RawMessageDelivery=true: 원본 그대로
{"order_id": 1001}
```

### 3. Filter Policy로 Topic 단순화

이벤트마다 Topic을 분리하지 말고, 단일 Topic + Filter Policy로 관리하면 운영이 간소화됩니다. 단, Filter가 너무 복잡해지면 EventBridge로의 이전을 검토합니다.

### 4. 보안 - 암호화와 액세스 제어

- **SSE-KMS**: KMS CMK로 메시지를 저장 시 암호화합니다.
- **VPC Endpoint**: VPC 내부에서 SNS API를 호출할 때 인터넷 우회 없이 호출합니다.
- **Topic Policy**: Cross-account publish/subscribe를 명시적으로 허용합니다.
- **HTTPS 강제**: Topic Policy에 `aws:SecureTransport=true` 조건을 추가하여 평문 트래픽을 차단합니다.

```bash
# KMS 암호화 Topic 생성
aws sns create-topic \
  --name encrypted-events \
  --attributes KmsMasterKeyId=alias/aws/sns \
  --region ap-northeast-2
```

### 5. 모니터링 핵심 지표

| 지표 | 의미 |
|------|------|
| NumberOfMessagesPublished | 발행된 메시지 수 |
| NumberOfNotificationsDelivered | 성공적으로 전달된 알림 수 |
| NumberOfNotificationsFailed | 전달 실패 수 (DLQ로 이동 전 포함) |
| NumberOfNotificationsFilteredOut | Filter Policy로 제외된 메시지 수 |
| PublishSize | publish된 메시지 평균 크기 |

`NumberOfNotificationsFailed`가 증가하면 구독자 엔드포인트(Lambda, HTTP, Email 등)의 가용성을 점검해야 합니다.

---

## 관련 서비스 비교

### SNS vs Amazon EventBridge

| 항목 | SNS | EventBridge |
|------|-----|-------------|
| 모델 | Pub/Sub Topic | Event Bus + Rules |
| 라우팅 | 단순 (Topic 단위) | 복잡한 룰 기반 라우팅 |
| 스키마 관리 | X | Schema Registry 제공 |
| 이벤트 보존 | 미보존 | Archive로 보존 가능 |
| 재처리 | X | Replay 지원 |
| SaaS 통합 | X | Salesforce, Datadog, Zendesk 등 90+ 제공자 |
| 처리량 | 매우 높음 | Default Bus 10K events/s |
| 가격 | 100만건당 $0.50 | 100만건당 $1.00 (Default Bus 무료) |
| 적합 용도 | 단순 Pub/Sub, Fanout | 이벤트 기반 마이크로서비스, SaaS 연동 |

**선택 기준**

- **SNS**: 단순한 Fanout, 알림, 모바일 푸시, SMS
- **EventBridge**: 복잡한 라우팅 룰, SaaS 이벤트 통합, 이벤트 재처리, 스키마 거버넌스

EventBridge는 SNS의 상위 호환 기능이 많지만 가격이 더 높고 응답 지연이 약간 더 있습니다. 단순한 알림 채널이라면 SNS가 더 적합합니다.

### SNS vs SQS

| 항목 | SNS | SQS |
|------|-----|-----|
| 모델 | Pub/Sub (Push) | 큐 (Pull) |
| 다중 Consumer | 지원 (구독자) | 큐 자체로는 X (SNS+SQS Fanout 필요) |
| 메시지 보존 | 즉시 전달, 미보존 | 1분 ~ 14일 |
| Consumer 가용성 | 영향 받음 (push) | 영향 없음 (pull) |
| 사용 시기 | 즉각 알림, 다수 구독자 | 비동기 작업 큐, 백프레셔 필요 |

[[amazon-sqs-simple-queue-service-개요|SQS]]와 SNS는 자주 함께 사용되는 보완 관계입니다. SNS가 메시지를 분배하고 각 SQS 큐가 Consumer 측 버퍼 역할을 하는 SNS+SQS Fanout이 가장 안정적인 패턴입니다.

---

## 관련 문서

- [[amazon-sqs-simple-queue-service-개요|Amazon SQS]] - SNS와 함께 Fanout 패턴 구성
- [[amazon-cloudwatch-모니터링-서비스-개요|Amazon CloudWatch]] - Alarm을 SNS Topic으로 알림 발송
- [[aws-cloudformation-iac-개요|AWS CloudFormation]] - SNS Topic을 IaC로 관리

---

## 요약

Amazon SNS는 분산 시스템에서 일대다 메시징을 책임지는 완전 관리형 Pub/Sub 서비스입니다. 핵심 포인트를 정리하면 다음과 같습니다.

1. **Standard Topic은 무제한 처리량**, **FIFO Topic은 순서 보장과 중복 제거**를 제공합니다.
2. **Fanout 패턴**(SNS → 다수 SQS)으로 한 이벤트를 여러 Consumer가 안전하게 받을 수 있습니다.
3. **Message Filtering**으로 단일 Topic에 이벤트를 모으고 구독자별로 라우팅을 분리할 수 있습니다.
4. **Mobile Push, SMS, Email**을 단일 API로 발송하여 알림 인프라를 통합합니다.
5. **CloudWatch Alarm + SNS** 조합은 AWS 운영 알림의 표준 패턴입니다.
6. 복잡한 라우팅 룰이나 SaaS 이벤트 통합이 필요하다면 **EventBridge**로의 이전을 고려합니다.

SNS는 SQS와 함께 AWS 통합 카테고리에서 가장 기본적이면서도 핵심적인 서비스이며, 이벤트 기반 아키텍처의 출발점이 되는 빌딩 블록입니다.
