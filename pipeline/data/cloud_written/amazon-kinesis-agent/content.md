<!-- infographic-hero -->
![Amazon Kinesis Agent 핵심 요약](figures/infographic.svg)

*Figure: Amazon Kinesis Agent 한 장 요약 인포그래픽*

# Amazon Kinesis Agent

## 개요

Amazon Kinesis Agent는 서버에 설치하여 로그 파일이나 데이터 파일을 Amazon Kinesis Data Streams 또는 Amazon Kinesis Data Firehose로 자동으로 수집하고 전송하는 독립형 Java 애플리케이션입니다.

Kinesis Agent는 AWS에서 공식적으로 제공하는 오픈소스 데이터 수집 도구로, Linux 서버에 설치하면 지정된 파일을 지속적으로 모니터링하고, 새로운 데이터가 추가될 때마다 자동으로 Kinesis 서비스로 전송합니다. Fluentd나 Logstash와 유사한 역할을 하지만, Kinesis 서비스에 특화되어 있어 설정이 단순하고 AWS 서비스와의 통합이 자연스럽습니다.

### Kinesis Agent를 선택해야 하는 경우

- EC2 인스턴스나 온프레미스 서버의 로그 파일을 실시간으로 Kinesis에 전송해야 하는 경우
- 별도의 애플리케이션 코드 수정 없이 기존 로그 파일을 스트리밍하고 싶은 경우
- 간단한 데이터 전처리(로그 포맷 변환, CSV를 JSON으로 변환 등)가 필요한 경우
- 전송 실패 시 자동 재시도와 체크포인팅이 필요한 경우

### Kinesis Agent vs 대안

Kinesis Agent 외에도 데이터를 Kinesis로 전송하는 방법은 여러 가지가 있습니다.

- **AWS SDK/KPL**: 애플리케이션 코드에서 직접 전송. 높은 유연성이 필요한 경우 적합합니다.
- **Fluentd/Fluent Bit**: Kinesis 플러그인을 사용. 다양한 출력 대상이 필요한 경우 적합합니다.
- **CloudWatch Agent**: CloudWatch Logs로 전송 후 구독 필터로 Kinesis에 연결. CloudWatch Logs도 함께 사용하는 경우 적합합니다.
- **Kinesis Agent**: Kinesis 전용. 가장 단순한 설정으로 Kinesis에 직접 전송. 순수한 로그 수집이 목적인 경우 최적입니다.

## 핵심 기능

### 파일 모니터링

Kinesis Agent는 지정된 파일 패턴(glob 패턴)에 일치하는 파일들을 지속적으로 모니터링합니다. 새로운 데이터가 파일에 추가되면 이를 감지하여 전송합니다. 파일 로테이션도 자동으로 처리합니다.

### 데이터 전처리

Kinesis Agent는 전송 전에 데이터를 변환할 수 있는 내장 전처리 기능을 제공합니다.

- **SINGLELINE**: 여러 줄에 걸친 레코드를 단일 라인으로 변환
- **CSVTOJSON**: CSV 형식 데이터를 JSON으로 변환
- **LOGTOJSON**: 공백이나 탭으로 구분된 로그를 JSON으로 변환
- **SYSLOGTOJSON**: Syslog 형식을 JSON으로 변환
- **APACHELOGTOJSON**: Apache/HTTPD 로그를 JSON으로 변환

### 전송 보장

Kinesis Agent는 체크포인팅 메커니즘을 사용하여, 에이전트가 재시작되더라도 마지막으로 전송된 위치부터 다시 전송을 시작합니다. 이를 통해 데이터 손실을 방지합니다.

### 배치 전송

개별 레코드를 하나씩 전송하는 대신, 여러 레코드를 배치로 묶어 전송하여 효율성을 높입니다. 배치 크기와 전송 간격을 설정할 수 있습니다.

### CloudWatch 메트릭 발행

Kinesis Agent는 자체적으로 CloudWatch에 메트릭을 발행합니다. 전송된 레코드 수, 바이트 수, 전송 실패 수, 재시도 횟수 등을 모니터링할 수 있습니다.

### 다중 대상 지원

하나의 Kinesis Agent에서 여러 파일을 모니터링하고, 각각 다른 Kinesis Data Stream 또는 Firehose 전송 스트림으로 전송할 수 있습니다.

## 아키텍처/동작 원리

### 내부 아키텍처

Kinesis Agent의 내부는 다음과 같은 구성요소로 이루어져 있습니다.

1. **File Tailer**: 지정된 파일 패턴에 일치하는 파일을 모니터링합니다. 파일의 현재 위치(offset)를 추적하고, 새로운 데이터가 추가되면 이를 읽어들입니다.
2. **Parser**: 읽어들인 원시 데이터를 레코드 단위로 파싱합니다. 데이터 전처리(변환)가 설정되어 있으면 이 단계에서 수행됩니다.
3. **Buffer**: 파싱된 레코드를 배치로 묶기 위한 내부 버퍼입니다. 버퍼 크기 또는 시간 제한에 도달하면 전송을 시작합니다.
4. **Sender**: 배치된 레코드를 Kinesis Data Streams 또는 Firehose로 전송합니다. PutRecords(KDS) 또는 PutRecordBatch(Firehose) API를 사용합니다.
5. **Checkpointer**: 성공적으로 전송된 위치를 로컬 파일에 기록합니다. 에이전트 재시작 시 이 위치부터 다시 전송합니다.

### 파일 로테이션 처리

Kinesis Agent는 파일 로테이션을 자동으로 감지합니다. 파일이 로테이션되면(예: access.log가 access.log.1로 이동하고 새 access.log가 생성), Agent는 이전 파일의 나머지 데이터를 먼저 전송하고, 새 파일로 자동 전환합니다. 이 동작은 inode 추적을 통해 이루어집니다.

### 전송 실패 처리

전송 실패 시 다음과 같은 재시도 메커니즘이 동작합니다.

1. 전송 실패 발생
2. 지수 백오프(Exponential Backoff)를 적용하여 재시도
3. 개별 레코드 수준에서 실패를 처리 (부분 실패 시 실패한 레코드만 재전송)
4. 최대 재시도 횟수를 초과하면 에러를 로깅하고 다음 배치로 이동

### 데이터 흐름

```
[로그 파일] --> [File Tailer] --> [Parser/Preprocessor] --> [Buffer]
                                                             |
                                                             v
[Checkpoint File] <-- [Checkpointer] <-- [Sender] --> [Kinesis Data Streams]
                                                  +--> [Kinesis Data Firehose]
```

## 실전 활용

### 설치

```bash
# Amazon Linux 2 / Amazon Linux 2023
sudo yum install -y amazon-kinesis-agent

# Ubuntu/Debian
sudo apt-get install -y amazon-kinesis-agent

# 소스에서 설치 (최신 버전)
sudo yum install -y java-1.8.0-openjdk
cd /tmp
git clone https://github.com/awslabs/amazon-kinesis-agent.git
cd amazon-kinesis-agent
sudo ./setup --install
```

### 기본 설정

Kinesis Agent의 설정 파일은 `/etc/aws-kinesis/agent.json`에 위치합니다.

```json
{
  "cloudwatch.emitMetrics": true,
  "cloudwatch.endpoint": "monitoring.ap-northeast-2.amazonaws.com",
  "kinesis.endpoint": "kinesis.ap-northeast-2.amazonaws.com",
  "firehose.endpoint": "firehose.ap-northeast-2.amazonaws.com",
  "flows": [
    {
      "filePattern": "/var/log/nginx/access.log*",
      "kinesisStream": "web-access-logs-stream",
      "partitionKeyOption": "RANDOM",
      "dataProcessingOptions": [
        {
          "optionName": "LOGTOJSON",
          "logFormat": "COMBINEDAPACHELOG"
        }
      ]
    },
    {
      "filePattern": "/var/log/app/error.log*",
      "deliveryStream": "app-error-logs-firehose",
      "dataProcessingOptions": [
        {
          "optionName": "SINGLELINE"
        }
      ]
    }
  ]
}
```

### 다양한 전처리 설정 예시

**CSV를 JSON으로 변환하는 설정:**

```json
{
  "flows": [
    {
      "filePattern": "/var/log/app/metrics.csv*",
      "kinesisStream": "app-metrics-stream",
      "dataProcessingOptions": [
        {
          "optionName": "CSVTOJSON",
          "customFieldNames": ["timestamp", "server_id", "cpu_usage", "memory_usage", "disk_io", "network_in", "network_out"]
        }
      ]
    }
  ]
}
```

**Apache 로그를 JSON으로 변환하는 설정:**

```json
{
  "flows": [
    {
      "filePattern": "/var/log/httpd/access_log*",
      "kinesisStream": "apache-logs-stream",
      "dataProcessingOptions": [
        {
          "optionName": "APACHELOGTOJSON",
          "logFormat": "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\""
        }
      ]
    }
  ]
}
```

### 에이전트 관리 (AWS CLI 및 시스템 명령)

```bash
# 에이전트 시작
sudo systemctl start aws-kinesis-agent

# 에이전트 중지
sudo systemctl stop aws-kinesis-agent

# 에이전트 상태 확인
sudo systemctl status aws-kinesis-agent

# 부팅 시 자동 시작 설정
sudo systemctl enable aws-kinesis-agent

# 에이전트 로그 확인
tail -f /var/log/aws-kinesis-agent/aws-kinesis-agent.log

# Kinesis Data Stream 상태 확인 (AWS CLI)
aws kinesis describe-stream \
  --stream-name web-access-logs-stream \
  --query 'StreamDescription.{Status:StreamStatus,Shards:Shards[*].ShardId}'

# Firehose 전송 스트림 상태 확인
aws firehose describe-delivery-stream \
  --delivery-stream-name app-error-logs-firehose \
  --query 'DeliveryStreamDescription.DeliveryStreamStatus'

# CloudWatch에서 Agent 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace "AWSKinesisAgent" \
  --metric-name "RecordsSentToKinesisStream" \
  --dimensions Name=StreamName,Value=web-access-logs-stream \
  --start-time "$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 300 \
  --statistics Sum
```

### 고급 설정

```json
{
  "cloudwatch.emitMetrics": true,
  "kinesis.endpoint": "kinesis.ap-northeast-2.amazonaws.com",
  "assumeRoleARN": "arn:aws:iam::123456789012:role/KinesisAgentRole",
  "assumeRoleExternalId": "kinesis-agent-external-id",
  "maxBufferAgeMillis": 1000,
  "maxBufferSizeRecords": 500,
  "flows": [
    {
      "filePattern": "/var/log/nginx/access.log*",
      "kinesisStream": "web-access-logs-stream",
      "partitionKeyOption": "RANDOM",
      "maxBufferAgeMillis": 500,
      "maxBufferSizeBytes": 1048576,
      "maxBufferSizeRecords": 1000,
      "minTimeBetweenFilePollsMillis": 100,
      "initialPosition": "END_OF_FILE",
      "dataProcessingOptions": [
        {
          "optionName": "LOGTOJSON",
          "logFormat": "COMBINEDAPACHELOG"
        }
      ]
    }
  ]
}
```

주요 고급 설정 항목의 의미는 다음과 같습니다.

- **maxBufferAgeMillis**: 버퍼의 최대 대기 시간 (밀리초). 이 시간이 지나면 배치가 완성되지 않았더라도 전송합니다.
- **maxBufferSizeRecords**: 한 배치에 포함할 최대 레코드 수.
- **maxBufferSizeBytes**: 한 배치의 최대 바이트 크기.
- **minTimeBetweenFilePollsMillis**: 파일 변경을 확인하는 폴링 간격 (밀리초).
- **initialPosition**: 에이전트 최초 시작 시 파일을 읽기 시작하는 위치. START_OF_FILE 또는 END_OF_FILE.
- **partitionKeyOption**: KDS 파티션 키 생성 방식. RANDOM 또는 DETERMINISTIC.

### IAM 역할 설정

Kinesis Agent가 실행되는 EC2 인스턴스에는 적절한 IAM 역할이 필요합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kinesis:PutRecord",
        "kinesis:PutRecords",
        "kinesis:DescribeStream"
      ],
      "Resource": "arn:aws:kinesis:ap-northeast-2:123456789012:stream/web-access-logs-stream"
    },
    {
      "Effect": "Allow",
      "Action": [
        "firehose:PutRecord",
        "firehose:PutRecordBatch",
        "firehose:DescribeDeliveryStream"
      ],
      "Resource": "arn:aws:firehose:ap-northeast-2:123456789012:deliverystream/app-error-logs-firehose"
    },
    {
      "Effect": "Allow",
      "Action": ["cloudwatch:PutMetricData"],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "AWSKinesisAgent"
        }
      }
    }
  ]
}
```

### 트러블슈팅

```bash
# 에이전트 로그에서 에러 확인
grep -i "error\|exception\|failed" /var/log/aws-kinesis-agent/aws-kinesis-agent.log | tail -20

# 체크포인트 파일 확인 (에이전트가 파일을 어디까지 읽었는지)
ls -la /var/run/aws-kinesis-agent/

# Java 프로세스 확인
ps aux | grep kinesis-agent

# 메모리 사용량 확인
jstat -gc $(pgrep -f kinesis-agent) 1000 5
```

## 모범 사례/보안

### 성능 최적화

**1. 버퍼 설정 조정**: 처리량이 높은 환경에서는 maxBufferSizeRecords와 maxBufferSizeBytes를 늘려 배치 효율을 높입니다. 지연에 민감한 환경에서는 maxBufferAgeMillis를 줄여 전송 지연을 낮춥니다.

**2. 파일 폴링 간격**: minTimeBetweenFilePollsMillis를 너무 짧게 설정하면 CPU 사용률이 높아집니다. 일반적으로 100~1000ms가 적절합니다.

**3. JVM 메모리 설정**: 대량의 로그를 처리하는 경우 `/usr/bin/start-aws-kinesis-agent`에서 JVM 힙 크기를 조정합니다.

**4. 파티션 키 전략**: KDS로 전송할 때 RANDOM 파티션 키를 사용하면 샤드 간 균등한 분배가 됩니다. 특정 키로 정렬이 필요한 경우 DETERMINISTIC을 사용합니다.

### 보안 모범 사례

- EC2 인스턴스 프로파일을 통해 IAM 역할을 할당합니다. 설정 파일에 AWS 자격 증명을 직접 입력하지 않습니다.
- IAM 역할에는 필요한 Kinesis 스트림/Firehose에 대한 최소한의 권한만 부여합니다.
- 크로스 계정 전송이 필요한 경우 assumeRoleARN을 사용합니다.
- Agent 로그 파일의 접근 권한을 적절히 설정하여 민감한 정보가 노출되지 않도록 합니다.

### 운영 모범 사례

- CloudWatch 메트릭을 기반으로 알람을 설정하여 전송 실패를 모니터링합니다.
- 체크포인트 디렉토리(/var/run/aws-kinesis-agent/)의 디스크 공간을 확인합니다.
- 로그 로테이션이 올바르게 설정되어 있는지 확인합니다. copytruncate 방식보다 rename 방식이 Kinesis Agent와 호환성이 더 좋습니다.
- 에이전트 업데이트를 정기적으로 수행합니다.

## 관련 서비스 비교

### Kinesis Agent vs CloudWatch Agent

| 항목 | Kinesis Agent | CloudWatch Agent |
|------|--------------|------------------|
| 전송 대상 | KDS, Firehose | CloudWatch Logs, CloudWatch Metrics |
| 데이터 전처리 | CSV->JSON, Log->JSON 등 | 제한적 |
| 실시간성 | 높음 (직접 전송) | 중간 (CW Logs 경유) |
| 시스템 메트릭 | 미지원 | CPU, 메모리 등 수집 |
| 설치 플랫폼 | Linux만 | Linux, Windows |

### Kinesis Agent vs Fluent Bit

| 항목 | Kinesis Agent | Fluent Bit |
|------|--------------|------------|
| 언어 | Java | C |
| 메모리 사용 | 높음 (~256MB) | 낮음 (~5MB) |
| 출력 대상 | Kinesis만 | 70+ 플러그인 |
| AWS 통합 | 네이티브 | 플러그인 필요 |
| 컨테이너 친화 | 낮음 | 높음 |

### Kinesis Agent vs KPL

| 항목 | Kinesis Agent | KPL (Producer Library) |
|------|--------------|------------------------|
| 사용 방식 | 독립형 에이전트 | 애플리케이션 라이브러리 |
| 데이터 소스 | 파일 | 애플리케이션 코드 |
| Aggregation | 미지원 | 지원 |
| 유연성 | 제한적 | 높음 |
| 설정 복잡도 | 낮음 | 높음 |

## 요약

Amazon Kinesis Agent는 서버의 로그 파일을 Kinesis 서비스로 안정적으로 전송하는 간편한 데이터 수집 도구입니다. 핵심 포인트를 정리하면 다음과 같습니다.

- **독립형 에이전트**: 별도의 애플리케이션 코드 수정 없이, 설정 파일 하나로 로그 수집을 시작할 수 있습니다.
- **파일 모니터링**: glob 패턴으로 파일을 지정하면, 파일 추가/로테이션을 자동으로 감지하고 처리합니다.
- **내장 전처리**: CSV->JSON, Apache Log->JSON 등의 변환을 에이전트 수준에서 수행할 수 있습니다.
- **전송 보장**: 체크포인팅과 재시도 메커니즘으로 데이터 손실을 방지합니다.
- **다중 대상**: 하나의 에이전트에서 여러 파일을 모니터링하고 각각 다른 스트림으로 전송할 수 있습니다.
- **적합한 사용 사례**: EC2 서버의 로그 파일을 Kinesis로 간단하게 전송하고 싶은 경우에 최적의 선택입니다. 컨테이너 환경이나 고급 기능이 필요한 경우에는 Fluent Bit이나 KPL을 고려해야 합니다.