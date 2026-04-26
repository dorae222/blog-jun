<!-- infographic-hero -->
![Amazon MQ: 표준 메시지 브로커의 완전관리형 서비스 핵심 요약](figures/infographic.svg)

*Figure: Amazon MQ: 표준 메시지 브로커의 완전관리형 서비스 한 장 요약 인포그래픽*

## 개요

Amazon MQ는 Apache ActiveMQ와 RabbitMQ를 위한 AWS 완전관리형 메시지 브로커 서비스입니다. 메시지 브로커는 분산 시스템에서 애플리케이션 간 비동기 통신을 가능하게 하는 핵심 미들웨어이며, Amazon MQ는 이러한 메시지 브로커의 프로비저닝, 설정, 유지 관리를 AWS가 대신 처리해줍니다.

기업 환경에서는 이미 ActiveMQ나 RabbitMQ 기반의 메시징 시스템을 운영하고 있는 경우가 많습니다. 이러한 시스템을 클라우드로 마이그레이션할 때, Amazon SQS나 SNS로 전환하려면 애플리케이션 코드를 상당 부분 수정해야 합니다. SQS/SNS는 JMS(Java Message Service), AMQP, MQTT, STOMP 등의 표준 메시징 프로토콜을 지원하지 않기 때문입니다.

Amazon MQ는 이 문제를 해결합니다. 표준 메시징 프로토콜과 API를 그대로 지원하므로, 기존 애플리케이션의 코드를 거의 변경하지 않고 클라우드 환경으로 마이그레이션할 수 있습니다. 연결 문자열(브로커 엔드포인트)만 변경하면 되는 경우가 대부분입니다.

다만, 신규 프로젝트에서 메시징 시스템을 처음 도입하는 경우에는 Amazon SQS/SNS를 먼저 고려하는 것이 좋습니다. SQS/SNS는 서버리스로 운영되어 관리 부담이 적고, 자동 확장이 무제한이며, 비용 효율성이 더 높기 때문입니다. Amazon MQ는 주로 기존 시스템의 마이그레이션 시나리오에 최적화된 서비스입니다.

## 핵심 기능

### 지원 엔진

**Apache ActiveMQ**

ActiveMQ는 가장 널리 사용되는 오픈소스 메시지 브로커 중 하나입니다. Amazon MQ for ActiveMQ는 ActiveMQ 5.x 버전을 지원하며, 다음 프로토콜을 사용할 수 있습니다.

- JMS (Java Message Service) 1.1
- AMQP 1.0
- MQTT 3.1.1
- STOMP 1.2
- OpenWire
- WebSocket

**Apache RabbitMQ**

RabbitMQ는 AMQP 프로토콜 기반의 경량 메시지 브로커입니다. Amazon MQ for RabbitMQ는 RabbitMQ 3.x 버전을 지원하며, 다음 기능을 제공합니다.

- AMQP 0-9-1 프로토콜
- Exchange, Queue, Binding 기반 라우팅
- 관리 콘솔 (RabbitMQ Management Plugin)
- 다양한 Exchange 타입 (Direct, Fanout, Topic, Headers)

### 배포 모드

**단일 인스턴스 (Single-Instance)**

개발/테스트 환경에 적합한 단일 브로커 구성입니다. 비용이 가장 저렴하지만 고가용성을 제공하지 않습니다.

**활성/대기 (Active/Standby)**

ActiveMQ 전용 고가용성 구성입니다. 두 개의 AZ에 걸쳐 활성 브로커와 대기 브로커가 배포되며, Amazon EFS를 통해 메시지 저장소를 공유합니다. 활성 브로커에 장애가 발생하면 대기 브로커가 자동으로 인계받습니다.

**클러스터 (Cluster)**

RabbitMQ 전용 고가용성 구성입니다. 3개의 AZ에 걸쳐 3개의 노드로 클러스터를 구성하며, 큐 미러링을 통해 메시지 복제를 보장합니다.

### 인스턴스 유형

Amazon MQ는 다양한 인스턴스 유형을 제공합니다. mq.t3.micro부터 mq.m5.4xlarge까지 워크로드에 맞게 선택할 수 있습니다.

```bash
# 사용 가능한 브로커 인스턴스 유형 확인
aws mq describe-broker-instance-options \
  --engine-type ACTIVEMQ \
  --query 'BrokerInstanceOptions[*].{HostInstanceType:HostInstanceType,EngineVersion:SupportedEngineVersions}' \
  --output table
```

## 아키텍처/동작 원리

### ActiveMQ 브로커 아키텍처

Amazon MQ for ActiveMQ의 Active/Standby 구성에서는 다음과 같이 동작합니다.

1. 활성 브로커가 모든 클라이언트 연결과 메시지 처리를 담당합니다.
2. 메시지 저장소는 Amazon EFS에 저장되어 두 브로커가 공유합니다.
3. 활성 브로커에 장애가 발생하면, EFS의 파일 락이 해제됩니다.
4. 대기 브로커가 EFS 락을 획득하고 활성 상태로 전환됩니다.
5. Network Load Balancer가 트래픽을 새 활성 브로커로 라우팅합니다.

장애 조치(failover) 시간은 일반적으로 1~2분 정도 소요됩니다.

```bash
# ActiveMQ Active/Standby 브로커 생성
aws mq create-broker \
  --broker-name prod-activemq-broker \
  --engine-type ACTIVEMQ \
  --engine-version "5.17.6" \
  --host-instance-type mq.m5.large \
  --deployment-mode ACTIVE_STANDBY_MULTI_AZ \
  --auto-minor-version-upgrade \
  --publicly-accessible false \
  --subnet-ids subnet-0123456789abcdef0 subnet-0abcdef1234567890 \
  --security-groups sg-0123456789abcdef0 \
  --users '[{
    "ConsoleAccess": true,
    "Username": "admin",
    "Password": "SecurePassword123!",
    "Groups": ["admin"]
  }]' \
  --encryption-options '{
    "UseAwsOwnedKey": false,
    "KmsKeyId": "arn:aws:kms:ap-northeast-2:123456789012:key/12345678-1234-1234-1234-123456789012"
  }' \
  --logs '{
    "Audit": true,
    "General": true
  }'
```

### RabbitMQ 클러스터 아키텍처

Amazon MQ for RabbitMQ 클러스터 구성에서는 다음과 같이 동작합니다.

1. 3개의 AZ에 각각 하나의 RabbitMQ 노드가 배포됩니다.
2. 클러스터 내 노드들은 Erlang Distribution Protocol로 통신합니다.
3. 큐는 기본적으로 Quorum Queue로 생성되어, 3개 노드 중 과반수(2개)에 메시지가 복제됩니다.
4. NLB가 클라이언트 연결을 가용한 노드로 분산합니다.

```bash
# RabbitMQ 클러스터 브로커 생성
aws mq create-broker \
  --broker-name prod-rabbitmq-cluster \
  --engine-type RABBITMQ \
  --engine-version "3.11.20" \
  --host-instance-type mq.m5.large \
  --deployment-mode CLUSTER_MULTI_AZ \
  --auto-minor-version-upgrade \
  --publicly-accessible false \
  --subnet-ids subnet-0123456789abcdef0 subnet-0abcdef1234567890 subnet-0fedcba9876543210 \
  --security-groups sg-0123456789abcdef0 \
  --users '[{
    "ConsoleAccess": true,
    "Username": "admin",
    "Password": "SecurePassword123!"
  }]'
```

### 네트워크 구성

Amazon MQ 브로커는 VPC 내에 배포되며, 다음과 같은 네트워크 구성을 갖습니다.

- **프라이빗 배포**: `--publicly-accessible false`로 설정하면 VPC 내에서만 접근 가능합니다.
- **보안 그룹**: 필요한 포트(ActiveMQ: 61617, RabbitMQ: 5671)만 허용합니다.
- **VPC 엔드포인트**: AWS PrivateLink를 통해 다른 VPC나 온프레미스에서 프라이빗하게 접근할 수 있습니다.

## 실전 활용

### 사례 1: 온프레미스 ActiveMQ 마이그레이션

기존 온프레미스 ActiveMQ에서 Amazon MQ로 마이그레이션하는 단계별 절차입니다.

```bash
# 1단계: 브로커 생성 후 상태 확인
aws mq describe-broker \
  --broker-id b-1234-5678-9012 \
  --query '{Status:BrokerState,Endpoints:BrokerInstances[*].Endpoints}'
```

```bash
# 2단계: 브로커 구성 확인
aws mq describe-configuration \
  --configuration-id c-1234-5678-9012
```

기존 ActiveMQ의 activemq.xml 설정을 Amazon MQ 구성에 맞게 조정해야 합니다. Amazon MQ는 activemq.xml의 일부 설정을 지원하며, 지원되지 않는 설정(예: 외부 저장소 플러그인)은 제거해야 합니다.

### 사례 2: Java JMS 클라이언트 연동

```java
// ActiveMQ JMS 연결 예시
import org.apache.activemq.ActiveMQConnectionFactory;
import javax.jms.*;

public class MQProducer {
    public static void main(String[] args) throws Exception {
        // Amazon MQ 엔드포인트로 연결
        String brokerUrl = "ssl://b-1234-5678-9012.mq.ap-northeast-2.amazonaws.com:61617";
        
        ActiveMQConnectionFactory factory = new ActiveMQConnectionFactory(brokerUrl);
        factory.setUserName("admin");
        factory.setPassword("SecurePassword123!");
        
        // Failover 프로토콜 사용 (Active/Standby 구성 시)
        String failoverUrl = "failover:(ssl://b-1234-active.mq.ap-northeast-2.amazonaws.com:61617," +
                             "ssl://b-1234-standby.mq.ap-northeast-2.amazonaws.com:61617)";
        ActiveMQConnectionFactory failoverFactory = new ActiveMQConnectionFactory(failoverUrl);
        
        Connection connection = failoverFactory.createConnection("admin", "SecurePassword123!");
        connection.start();
        
        Session session = connection.createSession(false, Session.AUTO_ACKNOWLEDGE);
        Queue queue = session.createQueue("ORDER.QUEUE");
        MessageProducer producer = session.createProducer(queue);
        
        TextMessage message = session.createTextMessage("{\"orderId\": \"ORD-001\"}");
        producer.send(message);
        
        producer.close();
        session.close();
        connection.close();
    }
}
```

### 사례 3: RabbitMQ Python 클라이언트 연동

```python
import pika
import ssl
import json

def publish_message(queue_name: str, message: dict):
    """RabbitMQ에 메시지를 발행합니다."""
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    ssl_context.set_ciphers('ECDHE+AESGCM:!ECDSA')
    
    credentials = pika.PlainCredentials('admin', 'SecurePassword123!')
    
    parameters = pika.ConnectionParameters(
        host='b-5678-1234-9012.mq.ap-northeast-2.amazonaws.com',
        port=5671,
        virtual_host='/',
        credentials=credentials,
        ssl_options=pika.SSLOptions(ssl_context)
    )
    
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    
    # Quorum Queue 선언
    channel.queue_declare(
        queue=queue_name,
        durable=True,
        arguments={'x-queue-type': 'quorum'}
    )
    
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # 메시지 영속화
            content_type='application/json'
        )
    )
    
    connection.close()
```

### 사례 4: 브로커 모니터링

```bash
# CloudWatch에서 브로커 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace AWS/AmazonMQ \
  --metric-name CpuUtilization \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Average \
  --dimensions Name=Broker,Value=prod-activemq-broker

# 큐 깊이 모니터링 (메시지 적체 감지)
aws cloudwatch get-metric-statistics \
  --namespace AWS/AmazonMQ \
  --metric-name QueueSize \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 60 \
  --statistics Maximum \
  --dimensions Name=Broker,Value=prod-activemq-broker Name=Queue,Value=ORDER.QUEUE
```

## 모범 사례/보안

### 보안 구성

1. **프라이빗 배포**: 브로커를 반드시 VPC 내 프라이빗 서브넷에 배포합니다.
2. **TLS 암호화**: 모든 클라이언트 연결에 TLS를 사용합니다. Amazon MQ는 기본적으로 TLS 엔드포인트를 제공합니다.
3. **KMS 암호화**: 저장 데이터에 대해 고객 관리형 KMS 키를 사용합니다.
4. **보안 그룹 제한**: 필요한 포트와 소스 IP만 허용합니다.
5. **CloudTrail 감사**: 브로커 관리 API 호출을 CloudTrail로 기록합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "mq:DescribeBroker",
        "mq:ListBrokers"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "mq:CreateBroker",
        "mq:DeleteBroker",
        "mq:UpdateBroker",
        "mq:RebootBroker"
      ],
      "Resource": "arn:aws:mq:ap-northeast-2:123456789012:broker:prod-*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "ap-northeast-2"
        }
      }
    }
  ]
}
```

### 성능 최적화

1. **인스턴스 크기 선택**: 메시지 처리량과 동시 연결 수를 기준으로 적절한 인스턴스 유형을 선택합니다.
2. **Prefetch 설정**: Consumer의 prefetch 크기를 워크로드에 맞게 조정합니다. 기본값이 너무 크면 메시지가 한 Consumer에 편중될 수 있습니다.
3. **메시지 영속화**: 중요하지 않은 메시지는 비영속(non-persistent) 모드로 전송하여 성능을 높일 수 있습니다.
4. **큐 분할**: 단일 큐에 과도한 메시지가 집중되지 않도록 파티셔닝 전략을 적용합니다.
5. **EBS 최적화**: ActiveMQ의 경우 EFS 대신 EBS 기반 스토리지를 사용하면 더 높은 IOPS를 확보할 수 있습니다.

### 운영 모범 사례

```bash
# 유지 관리 윈도우 설정 확인
aws mq describe-broker \
  --broker-id b-1234-5678-9012 \
  --query 'MaintenanceWindowStartTime'

# 브로커 구성 업데이트
aws mq update-broker \
  --broker-id b-1234-5678-9012 \
  --auto-minor-version-upgrade \
  --logs '{"Audit": true, "General": true}'
```

## 관련 서비스 비교

| 항목 | Amazon MQ | Amazon SQS | Amazon SNS | Amazon MSK |
|------|-----------|-----------|-----------|------------|
| 유형 | 관리형 브로커 | 관리형 큐 | 관리형 Pub/Sub | 관리형 Kafka |
| 프로토콜 | JMS, AMQP, MQTT, STOMP | HTTP/SQS API | HTTP/SNS API | Kafka 프로토콜 |
| 주요 사용 사례 | 마이그레이션 | 신규 구축 | 팬아웃 알림 | 스트리밍 |
| 자동 확장 | 수동 (인스턴스 변경) | 자동 (무제한) | 자동 (무제한) | 수동 (브로커 추가) |
| 메시지 순서 | 보장 (큐 단위) | FIFO 큐에서만 | 미보장 | 보장 (파티션 단위) |
| 메시지 크기 | 수 MB | 256KB (최대 2GB 참조) | 256KB | 수 MB |
| 메시지 보존 | 디스크 용량까지 | 최대 14일 | 즉시 전달 | 설정 가능 (무제한) |
| 비용 모델 | 인스턴스 시간 + 스토리지 | 요청 수 | 발행/전달 수 | 인스턴스 시간 + 스토리지 |
| 관리 부담 | 중간 | 낮음 | 낮음 | 높음 |

**Amazon MQ를 선택해야 하는 경우**
- 기존 ActiveMQ/RabbitMQ 기반 시스템을 마이그레이션할 때
- JMS, AMQP, MQTT, STOMP 프로토콜이 필수인 경우
- 기존 코드 변경을 최소화해야 하는 경우

**SQS/SNS를 선택해야 하는 경우**
- 신규 프로젝트에서 메시징을 처음 도입하는 경우
- 서버리스 아키텍처를 구축하는 경우
- 인프라 관리 부담을 최소화하고 싶은 경우

## 요약

Amazon MQ는 Apache ActiveMQ와 RabbitMQ를 위한 완전관리형 메시지 브로커 서비스입니다. 핵심 가치를 정리하면 다음과 같습니다.

- **표준 프로토콜 지원**: JMS, AMQP, MQTT, STOMP 등 업계 표준 메시징 프로토콜을 지원하여 코드 변경 없이 마이그레이션이 가능합니다.
- **고가용성**: ActiveMQ의 Active/Standby 구성, RabbitMQ의 3-AZ 클러스터 구성으로 프로덕션 수준의 가용성을 제공합니다.
- **완전관리형**: 프로비저닝, 패치, 백업, 모니터링을 AWS가 관리합니다.
- **보안**: VPC 내 프라이빗 배포, TLS 암호화, KMS 저장 암호화, IAM 접근 제어를 지원합니다.
- **마이그레이션 최적화**: 기존 온프레미스 메시징 시스템의 클라우드 전환에 최적화된 서비스입니다.

Amazon MQ는 "기존 시스템의 마이그레이션"이라는 명확한 사용 사례를 가지고 있으며, 신규 프로젝트에서는 SQS/SNS를 먼저 검토하는 것이 바람직합니다. 올바른 서비스 선택이 아키텍처 성공의 첫 걸음입니다.