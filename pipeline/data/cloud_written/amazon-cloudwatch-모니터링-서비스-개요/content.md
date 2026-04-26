<!-- infographic-hero -->
![Amazon CloudWatch 핵심 요약](figures/infographic.svg)

*Figure: Amazon CloudWatch 한 장 요약 인포그래픽*

# Amazon CloudWatch - 통합 모니터링 및 관찰 가능성 서비스 개요

## 개요

Amazon CloudWatch는 AWS의 통합 모니터링 및 관찰 가능성(Observability) 플랫폼입니다. 2009년에 출시된 이후 지속적으로 기능이 확장되어, 현재는 메트릭(Metrics), 로그(Logs), 알람(Alarms), 대시보드(Dashboards), 합성 모니터링(Synthetics), Application Insights 등 관찰 가능성에 필요한 거의 모든 영역을 포괄합니다.

전통적인 모니터링이 단순히 시스템 상태를 보는 것에 그쳤다면, CloudWatch는 메트릭 + 로그 + 트레이스(X-Ray 통합)를 결합하여 분산 시스템의 동작을 종합적으로 분석할 수 있게 합니다. 또한 [[amazon-sns-simple-notification-service-개요|Amazon SNS]]와 결합하면 이상 상황 발생 시 즉시 알림을 발송하는 자동화된 운영 체계를 구성할 수 있습니다.

CloudWatch가 제공하는 핵심 가치는 다음과 같습니다.

- **AWS 네이티브 통합**: 모든 AWS 서비스가 자동으로 메트릭을 발행합니다.
- **통합 인터페이스**: 메트릭, 로그, 알람, 트레이스를 하나의 콘솔에서 분석할 수 있습니다.
- **자동화 트리거**: Alarm으로 SNS 알림, Auto Scaling, Lambda 등을 자동 실행합니다.
- **유연한 쿼리**: Logs Insights 쿼리 언어로 대용량 로그를 빠르게 분석합니다.

---

## 핵심 기능

### 1. CloudWatch Metrics

Metrics는 시계열 수치 데이터를 수집/저장/분석하는 기능입니다.

**메트릭 분류**

| 분류 | 설명 |
|------|------|
| AWS 기본 메트릭 | EC2, RDS, Lambda 등 모든 AWS 서비스가 자동 발행 |
| Custom Metrics | `PutMetricData` API로 사용자가 직접 발행 |
| EMF (Embedded Metric Format) | 로그에 JSON 포맷으로 메트릭 포함하여 자동 추출 |

**해상도(Resolution)**

| 해상도 | 간격 | 비고 |
|--------|------|------|
| Standard Resolution | 60초 (1분) | 기본값, 대부분의 AWS 서비스 |
| High Resolution | 1초 | Custom Metrics에서만 사용 가능, 추가 비용 |

```bash
# Custom Metric 발행 (Python)
import boto3
cloudwatch = boto3.client('cloudwatch', region_name='ap-northeast-2')

cloudwatch.put_metric_data(
    Namespace='MyApp/Orders',
    MetricData=[
        {
            'MetricName': 'OrderProcessingTime',
            'Dimensions': [
                {'Name': 'Environment', 'Value': 'production'},
                {'Name': 'Region', 'Value': 'ap-northeast-2'}
            ],
            'Value': 1.234,
            'Unit': 'Seconds',
            'StorageResolution': 60
        }
    ]
)
```

**보존 기간**

- 1분 이하 데이터: 15일
- 5분 데이터: 63일
- 1시간 데이터: 455일

세부 데이터는 시간이 지나면 더 큰 단위로 자동 집계되어 보존됩니다.

### 2. CloudWatch Logs

Logs는 애플리케이션과 AWS 서비스의 로그를 수집/저장/검색하는 기능입니다.

**구조**

```text
Log Group (보존 정책 단위)
  └── Log Stream (인스턴스/소스 단위)
        └── Log Events (개별 로그 라인)
```

**주요 기능**

- **CloudWatch Logs Agent / unified CloudWatch Agent**: EC2/온프레미스 서버에서 로그를 수집합니다.
- **Subscription Filter**: 로그를 실시간으로 Lambda, Kinesis, OpenSearch로 스트리밍합니다.
- **Logs Insights**: SQL과 유사한 쿼리 언어로 로그를 분석합니다.
- **Logs Live Tail (2023+)**: 콘솔에서 실시간으로 로그를 스트리밍합니다.
- **Logs Anomaly Detection**: ML 기반 이상 패턴 감지.

```bash
# Log Group 생성 + 보존 기간 설정
aws logs create-log-group \
  --log-group-name /aws/lambda/my-function \
  --region ap-northeast-2

aws logs put-retention-policy \
  --log-group-name /aws/lambda/my-function \
  --retention-in-days 30 \
  --region ap-northeast-2
```

**Logs Insights 쿼리 예시**

```sql
-- 최근 1시간 동안 ERROR 로그 상위 10개
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 10

-- API 응답 시간 P99 분석 (5분 단위)
fields @timestamp, response_time
| filter ispresent(response_time)
| stats pct(response_time, 99) as p99 by bin(5m)

-- 사용자별 에러 카운트
fields @timestamp, user_id, error_code
| filter ispresent(error_code)
| stats count(*) as error_count by user_id
| sort error_count desc
| limit 20
```

### 3. CloudWatch Alarms

Alarm은 메트릭이 임계치를 초과했을 때 자동 액션을 트리거합니다.

**상태**

| 상태 | 의미 |
|------|------|
| OK | 메트릭이 임계치 이내 |
| ALARM | 임계치를 초과한 상태 |
| INSUFFICIENT_DATA | 데이터 부족으로 판단 불가 |

**액션 종류**

- [[amazon-sns-simple-notification-service-개요|Amazon SNS]] Topic으로 알림 발송
- EC2 Auto Scaling 그룹 스케일 인/아웃
- EC2 인스턴스 stop / terminate / reboot / recover
- Systems Manager OpsItem 생성
- Lambda 호출 (EventBridge 경유)

```bash
# CPU 80% 이상 5분 지속 시 알람
aws cloudwatch put-metric-alarm \
  --alarm-name ec2-high-cpu \
  --alarm-description "EC2 CPU > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 60 \
  --evaluation-periods 5 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=InstanceId,Value=i-0123456789abcdef0 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:ops-alerts \
  --region ap-northeast-2
```

**Composite Alarm**

여러 Alarm을 AND/OR 논리로 조합하여 단일 알림으로 통합합니다. 알림 피로도(alert fatigue)를 줄이는 데 유용합니다.

```bash
aws cloudwatch put-composite-alarm \
  --alarm-name service-degraded \
  --alarm-rule "ALARM(ec2-high-cpu) AND ALARM(rds-high-latency)" \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:ops-alerts \
  --region ap-northeast-2
```

### 4. CloudWatch Dashboards

Dashboard는 메트릭, 로그, 알람을 한 화면에 시각화하는 위젯 모음입니다.

- **위젯 종류**: Line, Stacked area, Number, Gauge, Bar, Pie, Logs Table, Alarm Status, Custom (HTML/Markdown)
- **JSON 정의**: 코드로 관리 가능
- **Cross-Account / Cross-Region**: 한 Dashboard에서 여러 계정과 리전의 메트릭을 동시에 표시

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/EC2", "CPUUtilization", "InstanceId", "i-0123456789abcdef0"]
        ],
        "period": 60,
        "stat": "Average",
        "region": "ap-northeast-2",
        "title": "EC2 CPU"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/lambda/my-function' | fields @timestamp, @message | sort @timestamp desc | limit 20",
        "region": "ap-northeast-2",
        "title": "Recent Errors"
      }
    }
  ]
}
```

### 5. CloudWatch Synthetics

Synthetics는 Canary라는 스크립트를 정기적으로 실행하여 엔드포인트의 가용성과 성능을 모니터링합니다.

- **Blueprint**: Heartbeat, API Canary, Broken Link Checker, Visual Monitoring, Canary Recorder
- **실행 주기**: 1분 ~ 임의 cron
- **결과**: 스크린샷, HAR 파일, 로그를 S3에 저장
- **Lambda 기반**: Canary 코드는 Node.js 또는 Python으로 작성

```python
# Canary Python 예시
from aws_synthetics.selenium import synthetics_webdriver as webdriver
from aws_synthetics.common import synthetics_logger as logger

def main():
    browser = webdriver.Chrome()
    browser.get("https://example.com")
    title = browser.title
    logger.info(f"Page title: {title}")
    assert "Example" in title
    browser.quit()

def handler(event, context):
    return main()
```

### 6. Container/Application/Lambda Insights

특정 워크로드에 특화된 자동 메트릭/로그 수집 기능입니다.

| 기능 | 대상 | 수집 데이터 |
|------|------|-------------|
| Container Insights | ECS/EKS/Kubernetes | 컨테이너 CPU/메모리/네트워크/디스크, 클러스터 전체 |
| Application Insights | RDS/EC2 등 애플리케이션 | 자동 이상 감지, 권장 사항 제시 |
| Lambda Insights | Lambda | Cold start, 메모리, CPU, 네트워크 |

```bash
# EKS 클러스터에서 Container Insights 활성화 (CloudWatch Agent + Fluent Bit DaemonSet)
ClusterName=my-eks-cluster
RegionName=ap-northeast-2
FluentBitHttpPort='2020'
FluentBitReadFromHead='Off'
FluentBitReadFromTail='On'

curl https://raw.githubusercontent.com/aws-samples/amazon-cloudwatch-container-insights/latest/k8s-deployment-manifest-templates/deployment-mode/daemonset/container-insights-monitoring/quickstart/cwagent-fluent-bit-quickstart.yaml | sed 's/{{cluster_name}}/'${ClusterName}'/;s/{{region_name}}/'${RegionName}'/;s/{{http_server_toggle}}/"On"/;s/{{http_server_port}}/"2020"/;s/{{read_from_head}}/"Off"/;s/{{read_from_tail}}/"On"/' | kubectl apply -f -
```

### 7. ServiceLens (X-Ray 통합)

ServiceLens는 X-Ray 트레이스 + CloudWatch 메트릭/로그를 결합하여 마이크로서비스의 의존성과 성능 병목을 시각화합니다.

- **Service Map**: 서비스 간 호출 관계를 그래프로 표시
- **Latency / Error Rate**: 각 노드별 응답 시간과 오류율
- **Trace 조회**: 특정 요청의 전체 경로 추적

---

## 아키텍처 / 동작 원리

### 메트릭 수집 흐름

```text
[AWS Service / Application]
        |
        v  PutMetricData / EMF
[CloudWatch Metrics]
        |
        +--> Alarm 평가 (1분 단위)
        |       |
        |       v  threshold 초과
        |     [SNS / Auto Scaling / Lambda]
        |
        +--> Dashboard 시각화
        |
        +--> CloudWatch API (조회)
```

### 로그 수집 흐름

```text
[Application]
   |
   v  CloudWatch Agent / SDK
[CloudWatch Logs]
   |
   +--> Log Group (보존 정책)
   |       └── Log Stream
   |             └── Log Events
   |
   +--> Subscription Filter
   |       |
   |       +--> Lambda
   |       +--> Kinesis Data Streams / Firehose
   |       +--> OpenSearch
   |
   +--> Logs Insights (쿼리)
   |
   +--> Metric Filter (로그→메트릭 변환)
```

### Metric Filter 패턴

로그에서 특정 패턴을 추출하여 Custom Metric으로 변환합니다. 가령 "ERROR" 단어가 포함된 로그 수를 메트릭화하면, 이를 Alarm으로 연결하여 에러 급증 시 알림을 받을 수 있습니다.

```bash
# Log에서 ERROR 카운팅
aws logs put-metric-filter \
  --log-group-name /aws/lambda/my-function \
  --filter-name ErrorCount \
  --filter-pattern "ERROR" \
  --metric-transformations \
    metricName=LambdaErrors,metricNamespace=MyApp,metricValue=1 \
  --region ap-northeast-2
```

### Embedded Metric Format (EMF)

EMF는 로그 안에 JSON 포맷으로 메트릭을 포함하면 CloudWatch가 자동으로 추출하여 Metric으로 만드는 방식입니다. 별도 PutMetricData API 호출이 필요 없어 Lambda나 컨테이너에서 효율적입니다.

```python
# EMF 예시
import json

emf_log = {
    "_aws": {
        "Timestamp": 1700000000000,
        "CloudWatchMetrics": [{
            "Namespace": "MyApp",
            "Dimensions": [["Service"]],
            "Metrics": [{"Name": "ProcessingTime", "Unit": "Milliseconds"}]
        }]
    },
    "Service": "OrderService",
    "ProcessingTime": 234,
    "OrderId": "12345"
}

print(json.dumps(emf_log))  # stdout으로 출력하면 CloudWatch Logs가 수집
```

---

## 실전 사용

### 1. ALB 5xx 에러 모니터링 + 자동 알림

```bash
# 1. SNS Topic + 이메일 구독
aws sns create-topic --name ops-alerts --region ap-northeast-2
aws sns subscribe \
  --topic-arn arn:aws:sns:ap-northeast-2:123456789012:ops-alerts \
  --protocol email \
  --notification-endpoint ops@example.com \
  --region ap-northeast-2

# 2. ALB 5xx 비율이 1% 초과 시 알람
aws cloudwatch put-metric-alarm \
  --alarm-name alb-5xx-high \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --evaluation-periods 5 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=LoadBalancer,Value=app/my-alb/abc123 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:ops-alerts \
  --treat-missing-data notBreaching \
  --region ap-northeast-2
```

### 2. RDS 성능 대시보드 구성

```python
import boto3
import json

cloudwatch = boto3.client('cloudwatch', region_name='ap-northeast-2')

dashboard_body = {
    "widgets": [
        {
            "type": "metric",
            "x": 0, "y": 0, "width": 12, "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "my-db"],
                    [".", "DatabaseConnections", ".", "."],
                    [".", "FreeableMemory", ".", "."]
                ],
                "period": 60,
                "stat": "Average",
                "region": "ap-northeast-2",
                "title": "RDS Resource Usage"
            }
        },
        {
            "type": "metric",
            "x": 12, "y": 0, "width": 12, "height": 6,
            "properties": {
                "metrics": [
                    ["AWS/RDS", "ReadLatency", "DBInstanceIdentifier", "my-db"],
                    [".", "WriteLatency", ".", "."]
                ],
                "period": 60,
                "stat": "Average",
                "region": "ap-northeast-2",
                "title": "RDS Latency"
            }
        }
    ]
}

cloudwatch.put_dashboard(
    DashboardName='RDS-Production',
    DashboardBody=json.dumps(dashboard_body)
)
```

### 3. Logs Insights로 P99 지연 추적

```sql
fields @timestamp, @message, response_time
| filter ispresent(response_time)
| stats
    count(*) as request_count,
    avg(response_time) as avg_time,
    pct(response_time, 50) as p50,
    pct(response_time, 95) as p95,
    pct(response_time, 99) as p99
  by bin(5m)
| sort @timestamp desc
```

이 쿼리는 5분 단위로 요청 수와 P50/P95/P99 응답 시간을 집계합니다. 결과를 Dashboard에 위젯으로 추가하면 실시간 SLA 모니터링이 가능합니다.

### 4. Anomaly Detection 활용

전통적인 정적 임계치 대신 ML이 학습한 정상 범위(밴드)를 벗어날 때 알람을 발생시킵니다.

```bash
aws cloudwatch put-anomaly-detector \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0123456789abcdef0 \
  --stat Average \
  --region ap-northeast-2

# Anomaly 기반 Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name ec2-cpu-anomaly \
  --metrics file://anomaly-metric.json \
  --evaluation-periods 5 \
  --threshold-metric-id ad1 \
  --comparison-operator GreaterThanUpperThreshold \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:ops-alerts \
  --region ap-northeast-2
```

---

## 가격 / 한도

### 가격 (us-east-1 기준)

| 항목 | 가격 |
|------|------|
| Custom Metric | 첫 10,000개까지 $0.30/지표/월, 이후 점차 할인 |
| API 요청 (PutMetricData) | 1,000 요청당 $0.01 |
| Logs Ingestion | $0.50/GB |
| Logs Storage (압축) | $0.03/GB-월 |
| Logs Insights 쿼리 | 스캔된 데이터 GB당 $0.005 |
| Dashboard | 첫 3개 무료, 이후 월 $3.00/개 |
| Alarm | $0.10/알람/월 (Standard), $0.30 (High Resolution) |
| Synthetics Canary 실행 | $0.0012/실행 |
| Contributor Insights 룰 | 실행당 $0.50 |

### 주요 한도

| 항목 | 한도 |
|------|------|
| 메트릭당 최대 dimension 수 | 30 |
| 한 PutMetricData 호출당 메트릭 수 | 1,000 |
| 메트릭 데이터 보존 | 1분: 15일, 5분: 63일, 1시간: 455일 |
| Log Group 보존 기간 | 1일 ~ 영구 |
| Alarm 평가 주기 | 10초, 30초, 또는 60의 배수 |
| Logs Insights 쿼리 동시 실행 | 30개/계정 |

---

## Best Practice

### 1. 비용 최적화

- **Log Group 보존 기간 설정**: 신규 Log Group은 기본 영구 보존이라 비용이 누적됩니다. 반드시 보존 정책을 설정합니다.
- **불필요한 Custom Metric 정리**: 사용하지 않는 메트릭도 월 $0.30씩 부과됩니다.
- **High Resolution Metric 신중 사용**: 1초 해상도는 비용이 높으므로 정말 필요한 경우에만 사용합니다.
- **Logs Insights 쿼리 최적화**: 시간 범위를 좁히고 `filter`를 먼저 적용해 스캔량을 줄입니다.
- **Log Group → S3 export**: 장기 보존이 필요한 로그는 S3로 export하여 비용을 절감합니다.

```bash
# 모든 Log Group의 보존 기간을 30일로 일괄 설정
aws logs describe-log-groups --query 'logGroups[*].logGroupName' --output text | \
  tr '\t' '\n' | \
  xargs -I {} aws logs put-retention-policy --log-group-name {} --retention-in-days 30
```

### 2. 알람 피로도(Alert Fatigue) 방지

- **Composite Alarm**: 관련 알람을 하나로 묶어 단일 알림으로 발송합니다.
- **`evaluation-periods` 적정 설정**: 1~2회 평가로는 노이즈가 많으므로 3~5회 연속 위반을 기준으로 합니다.
- **`treat-missing-data` 설정**: missing 데이터를 어떻게 처리할지 명시합니다 (`notBreaching` / `breaching` / `ignore`).
- **OK 액션 활용**: 복구 시에도 알림을 보내 자동 화이트리스트를 갱신합니다.

### 3. 구조화된 로깅

JSON 포맷으로 로그를 출력하면 Logs Insights 쿼리가 훨씬 강력해집니다.

```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_event(event_type, **kwargs):
    logger.info(json.dumps({
        "event_type": event_type,
        "timestamp": time.time(),
        **kwargs
    }))

log_event("OrderProcessed", order_id=1001, processing_time_ms=234, user_id=12345)
```

### 4. Tag 기반 메트릭 그룹핑

리소스에 일관된 태깅을 적용하면 환경별/팀별 비용과 메트릭을 손쉽게 분리할 수 있습니다.

### 5. SLO 기반 모니터링

CPU/메모리 같은 시스템 지표보다 사용자 경험에 직결되는 SLO 지표(P99 지연, 에러율, 가용성)를 중심으로 알람을 구성합니다.

---

## 관련 서비스 비교

### CloudWatch vs Datadog vs Grafana / Prometheus

| 항목 | CloudWatch | Datadog | Grafana + Prometheus |
|------|-----------|---------|----------------------|
| 배포 모델 | 완전 관리형 (AWS) | SaaS | 자체 호스팅 또는 Cloud |
| AWS 통합 | 네이티브 (자동) | Agent + 통합 모듈 | Exporter 필요 |
| 멀티 클라우드 | X (AWS only) | O (AWS, GCP, Azure 등) | O |
| 비용 모델 | 메트릭/로그 양 기반 | 호스트당 + 기능별 | 인프라 비용 + Grafana Cloud 옵션 |
| 로그 검색 성능 | 쿼리당 비용, P95 양호 | 매우 빠름 | Loki 사용 시 양호 |
| APM | X-Ray와 분리 | 통합 APM 강력 | Jaeger/Tempo 결합 |
| 학습 곡선 | 중 | 중-고 | 고 (Self-hosted 시) |
| 보안/규정 | AWS 보안 모델 그대로 | SaaS 의존 | 자체 통제 가능 |

**선택 기준**

- **CloudWatch**: AWS 단일 클라우드, AWS 보안 정책 통합, AWS 서비스 메트릭 자동화가 중요한 경우
- **Datadog**: 멀티 클라우드, 다양한 SaaS와의 통합, APM/RUM/Synthetics가 필요하며 비용에 민감하지 않은 경우
- **Grafana + Prometheus**: 자체 호스팅, 비용 절감, Kubernetes 중심 환경

CloudWatch는 AWS 비용 모델 특성상 메트릭/로그 양이 많아질수록 빠르게 비싸집니다. 대규모 환경에서는 일부를 Datadog/Grafana로 분산하거나, 로그를 S3로 export 후 Athena로 쿼리하는 패턴이 자주 사용됩니다.

### CloudWatch Events → EventBridge

과거 CloudWatch Events라는 이름이었던 기능은 2019년 EventBridge로 분리되었습니다. EventBridge는 CloudWatch Events의 상위 호환이며, AWS 이벤트 외에 SaaS 이벤트, Custom Event Bus, Schema Registry 등 추가 기능을 제공합니다. 신규 워크로드는 EventBridge를 사용하는 것이 권장됩니다.

---

## 관련 문서

- [[amazon-sns-simple-notification-service-개요|Amazon SNS]] - CloudWatch Alarm의 알림 채널
- [[amazon-sqs-simple-queue-service-개요|Amazon SQS]] - DLQ 메시지 누적 모니터링
- [[aws-cloudformation-iac-개요|AWS CloudFormation]] - CloudWatch Alarm/Dashboard를 IaC로 관리

---

## 요약

Amazon CloudWatch는 AWS의 관찰 가능성(Observability) 핵심 인프라이며, 단순 모니터링을 넘어 자동화된 운영 체계의 토대를 제공합니다. 핵심 포인트를 정리하면 다음과 같습니다.

1. **Metrics, Logs, Alarms, Dashboards**는 CloudWatch의 4대 축이며, 모두 단일 콘솔에서 통합 관리됩니다.
2. **Custom Metric + EMF**로 애플리케이션 KPI를 자유롭게 추적할 수 있습니다.
3. **Logs Insights**로 대용량 로그를 SQL 유사 문법으로 빠르게 분석할 수 있습니다.
4. **Composite Alarm + SNS** 조합은 알림 피로도를 줄이고 운영 자동화를 강화하는 표준 패턴입니다.
5. **Container/Lambda Insights, Synthetics, ServiceLens**는 워크로드별 깊이 있는 가시성을 제공합니다.
6. **비용 관리**가 핵심 운영 과제이며, Log Group 보존 정책, 메트릭 정리, 쿼리 최적화가 필수입니다.

CloudWatch는 AWS 운영 자동화의 출발점이며, 잘 설계된 모니터링 체계는 장애 대응 시간(MTTR)을 획기적으로 단축시킵니다.
