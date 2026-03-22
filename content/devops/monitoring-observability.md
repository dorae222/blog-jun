---
title: "모니터링 & 옵저버빌리티: Prometheus, Grafana, OpenTelemetry 실전 가이드"
slug: "monitoring-observability"
category: cloud
tags: ["devops", "monitoring", "prometheus", "grafana", "observability"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# 모니터링 & 옵저버빌리티: Prometheus, Grafana, OpenTelemetry 실전 가이드

## 1. 모니터링 vs 옵저버빌리티

**모니터링(Monitoring)**과 **옵저버빌리티(Observability)**는 비슷하지만 다른 개념이다.

| 구분 | 모니터링 | 옵저버빌리티 |
|------|---------|-------------|
| **질문** | "시스템이 정상인가?" | "시스템에 무슨 일이 일어나고 있는가?" |
| **접근** | 미리 정의된 지표를 감시 | 어떤 질문이든 답할 수 있는 역량 |
| **알림** | 임계값 기반 (CPU > 80%) | 이상 패턴 감지 |
| **목적** | 장애 감지 (Detection) | 근본 원인 분석 (Root Cause) |
| **범위** | 알려진 문제 | 알려지지 않은 문제 포함 |

```
모니터링:  "CPU 사용률이 95%입니다!" → 알림 발생
                                        └── 그래서 왜?

옵저버빌리티: "특정 API 엔드포인트의 응답 시간이 3초로 증가했고,
               해당 요청이 DB 쿼리에서 풀스캔을 하고 있으며,
               최근 배포에서 인덱스가 누락된 마이그레이션이 적용되었음"
               └── 근본 원인까지 추적 가능
```

> 모니터링은 옵저버빌리티의 **부분집합**이다. 옵저버빌리티가 좋은 시스템은 모니터링도 잘 되지만, 모니터링만으로는 옵저버빌리티를 달성할 수 없다.

---

## 2. 옵저버빌리티 3축: Logs, Metrics, Traces

옵저버빌리티는 세 가지 신호(Signal)로 구성된다:

```
                    옵저버빌리티 (Observability)
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
           Logs           Metrics          Traces
         (로그)           (메트릭)         (트레이스)
              │               │               │
        "무엇이         "얼마나 많이,     "요청이 어떤
         일어났는가?"     어떤 상태인가?"    경로로 흘렀는가?"
              │               │               │
        구조화된 이벤트   시계열 수치 데이터  분산 요청 추적
```

| 신호 | 특징 | 용도 | 예시 도구 |
|------|------|------|-----------|
| **Logs** | 이벤트 단위, 텍스트/구조화 | 디버깅, 감사 추적 | ELK, Loki |
| **Metrics** | 숫자, 시계열, 집계 가능 | 대시보드, 알림 | Prometheus |
| **Traces** | 요청 흐름, 서비스 간 연관 | 분산 시스템 디버깅 | Jaeger, Tempo |

### 세 가지를 함께 사용하는 이유

```
알림 발생: "주문 API 에러율 5% 초과" (Metrics)
    │
    ▼
대시보드 확인: "14:30부터 에러율 상승, 결제 서비스 응답시간 증가" (Metrics)
    │
    ▼
트레이스 분석: "주문 → 재고확인(OK) → 결제(Timeout)" (Traces)
    │
    ▼
로그 확인: "결제 서비스에서 DB 커넥션 풀 고갈 에러" (Logs)
    │
    ▼
근본 원인: DB 커넥션 풀 설정 부족 → 수정 및 배포
```

---

## 3. 로그 수집 및 관리

### ELK Stack (Elasticsearch + Logstash + Kibana)

```
┌──────────┐    ┌───────────┐    ┌───────────────┐    ┌──────────┐
│ App Logs │───▶│  Logstash │───▶│ Elasticsearch │───▶│  Kibana  │
│ (JSON)   │    │ (수집/변환)│    │  (저장/검색)   │    │ (시각화)  │
└──────────┘    └───────────┘    └───────────────┘    └──────────┘
```

### EFK Stack (Elasticsearch + Fluentd + Kibana)

Kubernetes 환경에서 더 널리 사용되는 구성:

```
┌──────────┐    ┌──────────┐    ┌───────────────┐    ┌──────────┐
│ App Logs │───▶│ Fluentd  │───▶│ Elasticsearch │───▶│  Kibana  │
│ (stdout) │    │(DaemonSet)│   │  (StatefulSet) │    │(Service) │
└──────────┘    └──────────┘    └───────────────┘    └──────────┘
```

### Grafana Loki (경량 로그 시스템)

Prometheus의 철학을 로그에 적용한 시스템으로, **로그 내용을 인덱싱하지 않고 라벨만 인덱싱**하여 비용을 크게 절감한다:

```yaml
# Docker Compose: Loki + Promtail
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki-data:/loki

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
```

### 구조화된 로그 (Structured Logging)

```json
{
  "timestamp": "2026-03-22T10:30:00.123Z",
  "level": "ERROR",
  "service": "order-service",
  "trace_id": "abc123def456",
  "span_id": "789ghi",
  "message": "Failed to process order",
  "order_id": "ORD-12345",
  "user_id": "USR-67890",
  "error": "ConnectionTimeout",
  "duration_ms": 5023
}
```

> **비구조화 로그**: `[2026-03-22 10:30:00] ERROR: Failed to process order ORD-12345`
> **구조화 로그**: JSON 형식으로 필드를 명시 → 검색/필터링/집계가 훨씬 용이

---

## 4. 메트릭 수집: Prometheus

### Prometheus 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     Prometheus 아키텍처                       │
│                                                             │
│  ┌──────────┐                                               │
│  │ Exporter │──┐                                            │
│  │ (node)   │  │   Pull    ┌────────────┐    ┌───────────┐ │
│  └──────────┘  ├──────────▶│ Prometheus │───▶│  Grafana  │ │
│  ┌──────────┐  │  /metrics │   Server   │    │ Dashboard │ │
│  │ Exporter │──┤           │            │    └───────────┘ │
│  │ (app)    │  │           │  ┌──────┐  │                   │
│  └──────────┘  │           │  │ TSDB │  │    ┌───────────┐ │
│  ┌──────────┐  │           │  └──────┘  │───▶│AlertManager│ │
│  │  App     │──┘           │            │    │  (알림)     │ │
│  │/metrics  │              └────────────┘    └───────────┘ │
│  └──────────┘                    ▲                          │
│                                  │                          │
│                         ┌────────────────┐                  │
│                         │ Service        │                  │
│                         │ Discovery      │                  │
│                         │ (K8s, Consul)  │                  │
│                         └────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

### Pull 모델 vs Push 모델

```
Pull 모델 (Prometheus):
  Prometheus ──▶ /metrics 엔드포인트를 주기적으로 수집
  장점: 타겟 상태 확인 가능, 간단한 구성
  단점: 방화벽/NAT 뒤 타겟 수집 어려움

Push 모델 (Datadog, InfluxDB):
  앱 ──▶ 메트릭 수집 서버로 직접 전송
  장점: 방화벽 뒤에서도 가능, 단기 Job에 적합
  단점: 수집 서버 과부하 가능

Prometheus의 Push Gateway:
  단기 배치 Job ──▶ Push Gateway ──▶ Prometheus (Pull)
```

### 메트릭 타입

| 타입 | 설명 | 사용 예시 |
|------|------|-----------|
| **Counter** | 단조 증가하는 값 | HTTP 요청 수, 에러 수 |
| **Gauge** | 증감 가능한 현재 값 | CPU 사용률, 메모리 사용량, 큐 크기 |
| **Histogram** | 값의 분포 (버킷) | 응답 시간 분포 |
| **Summary** | 값의 분포 (분위수) | 응답 시간 백분위 |

### 커스텀 메트릭 노출 예시 (Python)

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Counter: 총 요청 수
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

# Histogram: 응답 시간 분포
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# Gauge: 현재 활성 연결 수
ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections'
)

# 사용 예시
@app.route('/api/orders')
def get_orders():
    ACTIVE_CONNECTIONS.inc()
    with REQUEST_DURATION.labels(method='GET', endpoint='/api/orders').time():
        result = process_request()
    REQUEST_COUNT.labels(method='GET', endpoint='/api/orders', status='200').inc()
    ACTIVE_CONNECTIONS.dec()
    return result

# 메트릭 엔드포인트 시작
start_http_server(8000)  # :8000/metrics 에서 노출
```

### PromQL 기초

```promql
# 현재 값 조회
http_requests_total

# 레이블 필터링
http_requests_total{method="GET", status="200"}

# 5분간 초당 요청률 (rate)
rate(http_requests_total[5m])

# 에러율 계산
sum(rate(http_requests_total{status=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))
* 100

# 응답 시간 95번째 백분위
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 상위 5개 API (요청률 기준)
topk(5, sum by (endpoint)(rate(http_requests_total[5m])))

# CPU 사용률 (%)
100 - (avg by (instance)(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

### Prometheus 설정

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'app'
    metrics_path: /metrics
    static_configs:
      - targets: ['app:8000']

  # Kubernetes 서비스 디스커버리
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
```

---

## 5. 시각화: Grafana

### Grafana 개요

Grafana는 다양한 데이터 소스를 연결하여 **대시보드**를 구성할 수 있는 시각화 플랫폼이다.

### 지원 데이터 소스

- Prometheus, InfluxDB, Elasticsearch
- MySQL, PostgreSQL
- Loki (로그), Tempo (트레이스)
- CloudWatch, Azure Monitor

### 패널 타입

| 패널 타입 | 용도 | 적합한 데이터 |
|-----------|------|--------------|
| **Time Series** | 시간별 추이 | CPU, 메모리, 요청률 |
| **Stat** | 단일 수치 강조 | 현재 에러율, 활성 사용자 수 |
| **Gauge** | 범위 내 현재 값 | 디스크 사용률, SLO 달성률 |
| **Table** | 표 형식 데이터 | Top N 쿼리, 인스턴스 목록 |
| **Heatmap** | 분포 시각화 | 응답 시간 히트맵 |
| **Logs** | 로그 뷰어 | Loki 연동 로그 |
| **Bar Chart** | 비교 차트 | 서비스별 에러 수 비교 |

### 대시보드 구성 예시 (JSON 모델)

```json
{
  "dashboard": {
    "title": "Application Overview",
    "panels": [
      {
        "title": "Request Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (service)",
            "legendFormat": "{{service}}"
          }
        ]
      },
      {
        "title": "Error Rate (%)",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100"
          }
        ],
        "thresholds": {
          "steps": [
            {"color": "green", "value": 0},
            {"color": "yellow", "value": 1},
            {"color": "red", "value": 5}
          ]
        }
      }
    ]
  }
}
```

### Grafana as Code (프로비저닝)

```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
```

---

## 6. 분산 트레이싱

### OpenTelemetry

**OpenTelemetry(OTel)**는 CNCF의 표준 옵저버빌리티 프레임워크로, 로그/메트릭/트레이스를 통합 수집한다.

```
┌──────────────────────────────────────────────────────────────┐
│                     OpenTelemetry 구조                        │
│                                                              │
│  ┌─────────┐    ┌──────────────────┐    ┌────────────────┐  │
│  │  App    │───▶│  OTel Collector  │───▶│ Jaeger (Trace) │  │
│  │ (SDK)   │    │                  │───▶│ Prometheus     │  │
│  └─────────┘    │  수집 → 처리 → 전송│───▶│ Loki (Log)     │  │
│                 └──────────────────┘    └────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 트레이싱 개념

```
Trace ID: abc-123-def
│
├── Span: API Gateway (12ms)
│   │
│   ├── Span: Auth Service (3ms)
│   │
│   ├── Span: Order Service (45ms)
│   │   │
│   │   ├── Span: DB Query - get_inventory (5ms)
│   │   │
│   │   └── Span: Payment Service (35ms)   ← 병목!
│   │       │
│   │       └── Span: External API Call (30ms)
│   │
│   └── Span: Response Serialization (1ms)
```

### Python 애플리케이션에 OTel 적용

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

# 트레이서 설정
provider = TracerProvider()
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://otel-collector:4317")
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# Flask 자동 계측
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# 수동 스팬 생성
@app.route('/api/orders/<order_id>')
def get_order(order_id):
    with tracer.start_as_current_span("get_order") as span:
        span.set_attribute("order.id", order_id)

        with tracer.start_as_current_span("db_query"):
            order = db.get_order(order_id)

        with tracer.start_as_current_span("enrich_data"):
            enriched = enrich_order_data(order)

        return jsonify(enriched)
```

---

## 7. 알림 설정: AlertManager

### 알림 규칙 정의

```yaml
# alert_rules.yml
groups:
  - name: application
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m]))
          > 0.05
        for: 5m                    # 5분 이상 지속 시
        labels:
          severity: critical
        annotations:
          summary: "에러율이 5%를 초과했습니다"
          description: "현재 에러율: {{ $value | humanizePercentage }}"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "P95 응답 시간이 2초를 초과했습니다"

      - alert: HighCPUUsage
        expr: |
          100 - (avg by (instance)(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "CPU 사용률이 80%를 초과했습니다 (인스턴스: {{ $labels.instance }})"
```

### AlertManager 라우팅 및 에스컬레이션

```yaml
# alertmanager.yml
global:
  resolve_timeout: 5m

route:
  receiver: 'default'
  group_by: ['alertname', 'service']
  group_wait: 30s                    # 그룹핑 대기 시간
  group_interval: 5m                 # 같은 그룹 알림 간격
  repeat_interval: 4h                # 반복 알림 간격
  routes:
    # Critical: 즉시 전화 + 메신저
    - match:
        severity: critical
      receiver: 'critical-alerts'
      continue: true

    # Warning: 메신저만
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://notification-service:8080/webhook'

  - name: 'critical-alerts'
    webhook_configs:
      - url: 'http://notification-service:8080/webhook/critical'

  - name: 'warning-alerts'
    webhook_configs:
      - url: 'http://notification-service:8080/webhook/warning'

# 특정 시간대 알림 억제
inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']   # critical이 있으면 warning 억제
```

### 에스컬레이션 흐름

```
알림 발생
    │
    ▼
[30초 대기] ← 같은 유형의 알림을 그룹핑
    │
    ▼
1차 알림: 메신저 채널에 전송
    │
    ├── 5분 내 확인(ACK) → 종료
    │
    ▼ (미확인)
2차 알림: 온콜 담당자에게 직접 전송
    │
    ├── 15분 내 확인 → 종료
    │
    ▼ (미확인)
3차 알림: 팀 리더에게 에스컬레이션
```

---

## 8. SLI / SLO / SLA 개념

### 정의

| 용어 | 정의 | 예시 |
|------|------|------|
| **SLI** (Service Level Indicator) | 서비스 품질을 나타내는 **측정 지표** | 가용률, 응답 시간, 에러율 |
| **SLO** (Service Level Objective) | 내부적으로 설정하는 **목표 수준** | "가용률 99.9%" |
| **SLA** (Service Level Agreement) | 고객과의 **계약** (위반 시 보상) | "가용률 99.9% 미만 시 크레딧 지급" |

```
SLI ⊂ SLO ⊂ SLA

SLI: "지난 30일간 가용률이 99.95%입니다" (측정값)
SLO: "가용률을 99.9% 이상 유지해야 합니다" (내부 목표)
SLA: "가용률 99.9% 미만 시 월 요금의 10%를 환불합니다" (계약)
```

### 에러 버짓 (Error Budget)

SLO가 99.9%라면, **0.1%는 허용되는 장애 범위**다.

```
월간 에러 버짓 계산:

30일 × 24시간 × 60분 = 43,200분

SLO 99.9%일 때:
  허용 다운타임 = 43,200 × 0.001 = 43.2분/월

SLO 99.99%일 때:
  허용 다운타임 = 43,200 × 0.0001 = 4.32분/월
```

| SLO | 월간 허용 다운타임 | 연간 허용 다운타임 |
|-----|-------------------|--------------------|
| 99% | 7시간 18분 | 3일 15시간 |
| 99.9% | 43분 | 8시간 46분 |
| 99.95% | 21분 | 4시간 23분 |
| 99.99% | 4.3분 | 52분 |
| 99.999% | 26초 | 5분 15초 |

### PromQL로 SLI 계산

```promql
# 가용률 SLI (30일간)
1 - (
  sum(increase(http_requests_total{status=~"5.."}[30d]))
  /
  sum(increase(http_requests_total[30d]))
)

# 에러 버짓 남은 비율
(
  1 - (
    sum(increase(http_requests_total{status=~"5.."}[30d]))
    /
    sum(increase(http_requests_total[30d]))
  )
  - 0.999    # SLO 목표
) / 0.001    # 에러 버짓 (1 - SLO)
```

---

## 9. 실전 모니터링 스택 구성 예시

### Docker Compose 기반 통합 스택

```yaml
# docker-compose.monitoring.yml
services:
  # ──────── 메트릭 수집 ────────
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./prometheus/alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'

  node-exporter:
    image: prom/node-exporter:latest
    pid: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'

  # ──────── 로그 수집 ────────
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki-data:/loki

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log:ro
      - ./promtail/config.yml:/etc/promtail/config.yml

  # ──────── 트레이싱 ────────
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    volumes:
      - ./otel/config.yml:/etc/otelcol/config.yaml
    ports:
      - "4317:4317"    # gRPC
      - "4318:4318"    # HTTP

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI

  # ──────── 시각화 ────────
  grafana:
    image: grafana/grafana:latest
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}

  # ──────── 알림 ────────
  alertmanager:
    image: prom/alertmanager:latest
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - "9093:9093"

volumes:
  prometheus-data:
  loki-data:
  grafana-data:
```

### OpenTelemetry Collector 설정

```yaml
# otel/config.yml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
    send_batch_size: 1000

  memory_limiter:
    check_interval: 1s
    limit_mib: 512

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"

  otlp/jaeger:
    endpoint: jaeger:4317
    tls:
      insecure: true

  loki:
    endpoint: http://loki:3100/loki/api/v1/push

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [otlp/jaeger]

    metrics:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [prometheus]

    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [loki]
```

### 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    모니터링 스택 전체 구성                         │
│                                                                 │
│  ┌─────────┐    ┌──────────────────┐                            │
│  │  App 1  │───▶│                  │    ┌────────────┐          │
│  └─────────┘    │  OpenTelemetry   │───▶│ Prometheus │──┐      │
│  ┌─────────┐    │    Collector     │    └────────────┘  │      │
│  │  App 2  │───▶│                  │───▶┌────────────┐  │      │
│  └─────────┘    │  (수집/처리/전송) │    │   Jaeger   │  │      │
│  ┌─────────┐    │                  │───▶└────────────┘  │      │
│  │  App 3  │───▶│                  │    ┌────────────┐  │      │
│  └─────────┘    └──────────────────┘───▶│    Loki    │  │      │
│                                         └────────────┘  │      │
│                                                │        │      │
│  ┌─────────────┐                              ▼        ▼      │
│  │AlertManager │◀──────────────────── ┌──────────────────┐    │
│  │  (알림)      │                      │     Grafana      │    │
│  └─────────────┘                      │   (통합 대시보드)  │    │
│        │                              └──────────────────┘    │
│        ▼                                                       │
│  메신저/이메일/PagerDuty                                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 마무리

모니터링과 옵저버빌리티는 서비스 운영의 **눈**이다. 핵심 포인트를 정리하면:

- **모니터링은 "정상인가"**, **옵저버빌리티는 "왜 비정상인가"**에 답한다
- **Logs, Metrics, Traces** 세 가지 신호를 통합적으로 수집해야 진정한 옵저버빌리티를 달성할 수 있다
- **Prometheus**는 Pull 기반 메트릭 수집의 표준이며, **PromQL**로 강력한 쿼리가 가능하다
- **OpenTelemetry**는 옵저버빌리티 신호의 통합 수집 표준으로 자리 잡고 있다
- **SLI/SLO/SLA** 체계를 수립하여 데이터 기반으로 서비스 품질을 관리한다
- **알림은 실행 가능해야 한다**: 알림을 받고 무엇을 해야 하는지 명확하지 않으면 알림 피로(Alert Fatigue)가 발생한다

완성도 높은 모니터링 체계는 하루아침에 만들어지지 않는다. 핵심 메트릭부터 시작하여 점진적으로 확장해나가는 것이 바람직하다.
