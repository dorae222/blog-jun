<!-- infographic-hero -->
![AWS Glue Trigger - ETL 작업 자동화를 위한 트리거 완벽 가이드 핵심 요약](figures/infographic.svg)

*Figure: AWS Glue Trigger - ETL 작업 자동화를 위한 트리거 완벽 가이드 한 장 요약 인포그래픽*

## 개요

AWS Glue는 서버리스 데이터 통합 서비스로, ETL(Extract, Transform, Load) 작업을 손쉽게 구성하고 실행할 수 있습니다. 이 중에서 **Glue Trigger**는 ETL 작업의 실행 시점을 제어하는 핵심 구성 요소입니다. 트리거를 올바르게 설정하면 수동 개입 없이도 데이터 파이프라인을 완전히 자동화할 수 있습니다.

데이터 엔지니어링 환경에서는 매일 수십, 수백 개의 ETL 작업이 특정 시점에 실행되어야 하며, 작업 간 의존성도 관리해야 합니다. AWS Glue Trigger는 이러한 요구사항을 충족하기 위해 다양한 트리거 유형을 제공합니다. 스케줄 기반으로 정해진 시간에 실행하거나, 이전 작업의 완료를 감지하여 다음 작업을 자동으로 시작하거나, API 호출을 통해 온디맨드로 실행하는 것이 가능합니다.

본 글에서는 AWS Glue Trigger의 세 가지 유형을 깊이 있게 살펴보고, AWS CLI를 활용한 실전 설정 방법과 함께 프로덕션 환경에서의 모범 사례를 다루겠습니다.

## 핵심 기능

### 트리거 유형 개요

AWS Glue Trigger는 크게 세 가지 유형으로 나뉩니다.

**1. 스케줄 트리거 (Scheduled Trigger)**

cron 표현식 또는 rate 표현식을 사용하여 정해진 주기에 따라 작업을 실행합니다. 일일 배치 처리, 시간별 데이터 동기화 등 정기적인 작업에 적합합니다.

```bash
# 매일 오전 9시(UTC)에 실행되는 스케줄 트리거 생성
aws glue create-trigger \
  --name "daily-etl-trigger" \
  --type SCHEDULED \
  --schedule "cron(0 9 * * ? *)" \
  --actions '[{"JobName": "my-etl-job"}]' \
  --start-on-creation
```

스케줄 표현식에서 사용 가능한 형식은 다음과 같습니다.

- **cron 표현식**: `cron(분 시 일 월 요일 연도)` - 세밀한 스케줄링이 가능합니다.
- **rate 표현식**: `rate(값 단위)` - 단순 반복 주기 설정에 적합합니다.

```bash
# rate 표현식 예시: 2시간마다 실행
aws glue create-trigger \
  --name "periodic-sync-trigger" \
  --type SCHEDULED \
  --schedule "rate(2 hours)" \
  --actions '[{"JobName": "data-sync-job"}]' \
  --start-on-creation
```

**2. 조건부 트리거 (Conditional Trigger)**

하나 이상의 작업 또는 크롤러의 완료 상태를 조건으로 다음 작업을 실행합니다. ETL 파이프라인에서 작업 간 의존성을 관리하는 데 필수적입니다.

```bash
# job-a가 성공한 후 job-b를 실행하는 조건부 트리거
aws glue create-trigger \
  --name "conditional-trigger" \
  --type CONDITIONAL \
  --predicate '{
    "Conditions": [
      {
        "LogicalOperator": "EQUALS",
        "JobName": "job-a",
        "State": "SUCCEEDED"
      }
    ]
  }' \
  --actions '[{"JobName": "job-b"}]' \
  --start-on-creation
```

조건부 트리거에서는 `Logical` 파라미터를 사용하여 여러 조건을 조합할 수 있습니다.

```bash
# 여러 작업이 모두 성공해야 실행 (AND 조건)
aws glue create-trigger \
  --name "multi-condition-trigger" \
  --type CONDITIONAL \
  --predicate '{
    "Logical": "AND",
    "Conditions": [
      {"LogicalOperator": "EQUALS", "JobName": "extract-job", "State": "SUCCEEDED"},
      {"LogicalOperator": "EQUALS", "JobName": "validate-job", "State": "SUCCEEDED"}
    ]
  }' \
  --actions '[{"JobName": "transform-job"}]' \
  --start-on-creation
```

**3. 온디맨드 트리거 (On-Demand Trigger)**

API 호출이나 수동 실행을 통해 필요한 시점에 즉시 작업을 실행합니다. 테스트, 긴급 데이터 처리, 외부 시스템 연동 등에 활용됩니다.

```bash
# 온디맨드 트리거 생성
aws glue create-trigger \
  --name "on-demand-trigger" \
  --type ON_DEMAND \
  --actions '[{"JobName": "ad-hoc-etl-job"}]'

# 온디맨드 트리거 수동 실행
aws glue start-trigger --name "on-demand-trigger"
```

### 이벤트 기반 트리거 (EventBridge 연동)

AWS Glue는 Amazon EventBridge와 연동하여 이벤트 기반 트리거도 지원합니다. S3에 새로운 파일이 업로드되거나, 특정 AWS 서비스에서 이벤트가 발생했을 때 ETL 작업을 자동으로 시작할 수 있습니다.

```bash
# EventBridge 규칙을 통한 S3 이벤트 기반 트리거
aws events put-rule \
  --name "s3-upload-trigger-rule" \
  --event-pattern '{
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {"name": ["my-data-bucket"]},
      "object": {"key": [{"prefix": "raw-data/"}]}
    }
  }'

# EventBridge 타겟으로 Glue Job 설정
aws events put-targets \
  --rule "s3-upload-trigger-rule" \
  --targets '[{
    "Id": "glue-job-target",
    "Arn": "arn:aws:glue:ap-northeast-2:123456789012:job/s3-ingestion-job",
    "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeGlueRole"
  }]'
```

### 트리거 상태 관리

트리거는 다음과 같은 상태를 가집니다.

| 상태 | 설명 |
|------|------|
| CREATED | 생성되었지만 아직 활성화되지 않은 상태 |
| ACTIVATED | 활성화되어 조건 충족 시 작업을 실행하는 상태 |
| DEACTIVATED | 비활성화된 상태로, 조건이 충족되어도 작업을 실행하지 않음 |
| ACTIVATING | 활성화 중인 전이 상태 |
| DEACTIVATING | 비활성화 중인 전이 상태 |

```bash
# 트리거 상태 확인
aws glue get-trigger --name "daily-etl-trigger"

# 트리거 활성화
aws glue start-trigger --name "daily-etl-trigger"

# 트리거 비활성화
aws glue stop-trigger --name "daily-etl-trigger"
```

## 아키텍처/동작 원리

### 트리거 실행 흐름

AWS Glue Trigger의 내부 동작 원리를 이해하면 더 효과적인 파이프라인을 설계할 수 있습니다.

```
[트리거 조건 발생]
       |
       v
[Glue 스케줄러가 조건 평가]
       |
       v
[조건 충족 여부 확인]
       |
   Yes / No
   /       \
  v         v
[작업 실행]  [대기 상태 유지]
  |
  v
[Job Run 생성 및 리소스 할당]
  |
  v
[ETL 작업 수행]
  |
  v
[작업 완료 → 다음 조건부 트리거 평가]
```

**스케줄 트리거**는 내부적으로 CloudWatch Events(EventBridge)와 유사한 메커니즘을 사용하여 시간 기반 스케줄링을 수행합니다. cron 표현식이 평가되어 해당 시점이 되면 자동으로 지정된 작업을 시작합니다.

**조건부 트리거**는 Glue 서비스 내부에서 작업 상태 변화를 모니터링합니다. 선행 작업이 완료될 때마다 트리거의 조건(Predicate)을 평가하여, 모든 조건이 충족되면 후속 작업을 실행합니다.

### 트리거와 Workflow의 관계

트리거는 독립적으로 사용할 수도 있지만, AWS Glue Workflow 내에서 사용할 때 더 강력한 오케스트레이션이 가능합니다.

```
[Workflow]
  ├── Trigger A (SCHEDULED) → Job 1
  ├── Trigger B (CONDITIONAL: Job 1 성공) → Job 2
  ├── Trigger C (CONDITIONAL: Job 1 성공) → Job 3
  └── Trigger D (CONDITIONAL: Job 2 AND Job 3 성공) → Job 4
```

Workflow 내에서 트리거를 사용하면 전체 파이프라인의 실행 상태를 하나의 단위로 관리할 수 있으며, 실행 이력과 통계를 통합적으로 모니터링할 수 있습니다.

### Batch Stop 동작

트리거를 비활성화하면 현재 실행 중인 작업에는 영향을 주지 않습니다. 이미 시작된 Job Run은 계속 실행되며, 트리거 비활성화는 새로운 작업 실행만 방지합니다. 실행 중인 작업을 중단하려면 별도로 `batch-stop-job-run` API를 호출해야 합니다.

```bash
# 실행 중인 Job Run 확인
aws glue get-job-runs --job-name "my-etl-job" --max-results 5

# 특정 Job Run 중단
aws glue batch-stop-job-run \
  --job-name "my-etl-job" \
  --job-run-ids "jr_abc123"
```

## 실전 활용

### 사례 1: 일일 데이터 웨어하우스 적재 파이프라인

매일 새벽에 원본 데이터를 추출하고, 변환 후 데이터 웨어하우스에 적재하는 파이프라인을 구성해 보겠습니다.

```bash
# Step 1: Extract Job 생성 (S3에서 원본 데이터 추출)
aws glue create-job \
  --name "dw-extract-job" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --command '{
    "Name": "glueetl",
    "ScriptLocation": "s3://my-scripts/extract.py",
    "PythonVersion": "3"
  }' \
  --default-arguments '{
    "--source_database": "raw_db",
    "--target_path": "s3://my-staging/extracted/"
  }' \
  --glue-version "4.0" \
  --number-of-workers 10 \
  --worker-type "G.1X"

# Step 2: Transform Job 생성
aws glue create-job \
  --name "dw-transform-job" \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --command '{
    "Name": "glueetl",
    "ScriptLocation": "s3://my-scripts/transform.py",
    "PythonVersion": "3"
  }' \
  --glue-version "4.0" \
  --number-of-workers 20 \
  --worker-type "G.2X"

# Step 3: 매일 새벽 2시에 Extract 시작하는 스케줄 트리거
aws glue create-trigger \
  --name "dw-daily-extract-trigger" \
  --type SCHEDULED \
  --schedule "cron(0 2 * * ? *)" \
  --actions '[{"JobName": "dw-extract-job"}]' \
  --start-on-creation

# Step 4: Extract 성공 시 Transform 시작하는 조건부 트리거
aws glue create-trigger \
  --name "dw-transform-after-extract" \
  --type CONDITIONAL \
  --predicate '{
    "Conditions": [{
      "LogicalOperator": "EQUALS",
      "JobName": "dw-extract-job",
      "State": "SUCCEEDED"
    }]
  }' \
  --actions '[{"JobName": "dw-transform-job"}]' \
  --start-on-creation
```

### 사례 2: 멀티 소스 데이터 통합 파이프라인

여러 데이터 소스에서 병렬로 데이터를 수집하고, 모든 수집이 완료되면 통합 처리를 수행하는 패턴입니다.

```bash
# 병렬 수집 작업들을 시작하는 스케줄 트리거
aws glue create-trigger \
  --name "parallel-ingest-trigger" \
  --type SCHEDULED \
  --schedule "cron(0 1 * * ? *)" \
  --actions '[
    {"JobName": "ingest-mysql-job"},
    {"JobName": "ingest-api-job"},
    {"JobName": "ingest-s3-csv-job"}
  ]' \
  --start-on-creation

# 모든 수집 작업이 성공한 후 통합 작업 실행
aws glue create-trigger \
  --name "merge-after-all-ingest" \
  --type CONDITIONAL \
  --predicate '{
    "Logical": "AND",
    "Conditions": [
      {"LogicalOperator": "EQUALS", "JobName": "ingest-mysql-job", "State": "SUCCEEDED"},
      {"LogicalOperator": "EQUALS", "JobName": "ingest-api-job", "State": "SUCCEEDED"},
      {"LogicalOperator": "EQUALS", "JobName": "ingest-s3-csv-job", "State": "SUCCEEDED"}
    ]
  }' \
  --actions '[{"JobName": "merge-and-dedupe-job"}]' \
  --start-on-creation
```

### 사례 3: 크롤러 완료 후 ETL 실행

Glue Crawler가 새로운 데이터를 카탈로그에 등록한 후 자동으로 ETL 작업을 실행하는 패턴입니다.

```bash
# 크롤러 완료를 감지하는 조건부 트리거
aws glue create-trigger \
  --name "etl-after-crawl" \
  --type CONDITIONAL \
  --predicate '{
    "Conditions": [{
      "LogicalOperator": "EQUALS",
      "CrawlerName": "raw-data-crawler",
      "CrawlState": "SUCCEEDED"
    }]
  }' \
  --actions '[{"JobName": "process-new-data-job"}]' \
  --start-on-creation
```

### 사례 4: Job 파라미터를 동적으로 전달하는 트리거

트리거에서 작업에 인수를 전달하여 동적으로 동작을 제어할 수 있습니다.

```bash
# 파라미터를 포함한 트리거 생성
aws glue create-trigger \
  --name "parameterized-trigger" \
  --type SCHEDULED \
  --schedule "cron(0 6 * * ? *)" \
  --actions '[{
    "JobName": "configurable-etl-job",
    "Arguments": {
      "--processing_date": "2024-01-15",
      "--target_table": "analytics.daily_summary",
      "--mode": "incremental"
    }
  }]' \
  --start-on-creation
```

### 트리거 목록 조회 및 관리

```bash
# 전체 트리거 목록 조회
aws glue get-triggers

# 특정 트리거 상세 정보 조회
aws glue get-trigger --name "daily-etl-trigger"

# 트리거 업데이트 (스케줄 변경)
aws glue update-trigger \
  --name "daily-etl-trigger" \
  --trigger-update '{
    "Schedule": "cron(0 3 * * ? *)"
  }'

# 트리거 삭제
aws glue delete-trigger --name "old-trigger"
```

## 모범 사례/보안

### IAM 권한 최소화

Glue Trigger를 관리하는 IAM 정책은 최소 권한 원칙을 따라야 합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "glue:CreateTrigger",
        "glue:GetTrigger",
        "glue:GetTriggers",
        "glue:UpdateTrigger",
        "glue:DeleteTrigger",
        "glue:StartTrigger",
        "glue:StopTrigger",
        "glue:BatchGetTriggers"
      ],
      "Resource": "arn:aws:glue:ap-northeast-2:123456789012:trigger/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:StartJobRun",
        "glue:GetJobRun",
        "glue:GetJobRuns"
      ],
      "Resource": "arn:aws:glue:ap-northeast-2:123456789012:job/*"
    }
  ]
}
```

### 실패 처리 전략

프로덕션 환경에서는 작업 실패 시 대응 전략이 필수적입니다.

```bash
# Job에 재시도 설정 적용
aws glue update-job \
  --job-name "critical-etl-job" \
  --job-update '{
    "MaxRetries": 3,
    "Timeout": 120
  }'

# CloudWatch 알람으로 트리거 실패 모니터링
aws cloudwatch put-metric-alarm \
  --alarm-name "glue-trigger-failure-alarm" \
  --namespace "AWS/Glue" \
  --metric-name "TriggeredJobRunsFailed" \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --evaluation-periods 1 \
  --alarm-actions "arn:aws:sns:ap-northeast-2:123456789012:glue-alerts"
```

### 태그 기반 관리

트리거에 태그를 부여하여 체계적으로 관리합니다.

```bash
# 트리거에 태그 추가
aws glue tag-resource \
  --resource-arn "arn:aws:glue:ap-northeast-2:123456789012:trigger/daily-etl-trigger" \
  --tags-to-add '{"Environment": "production", "Team": "data-engineering", "CostCenter": "DE-001"}'
```

### 주의 사항

- **동시 실행 제한**: 같은 Job에 대해 동시에 실행 가능한 최대 수를 `MaxConcurrentRuns`로 설정해야 합니다. 스케줄 트리거가 이전 실행이 끝나기 전에 다시 실행되는 상황을 방지합니다.
- **시간대 고려**: cron 표현식은 UTC 기준입니다. 한국 시간(KST, UTC+9)을 적용하려면 9시간을 빼서 설정해야 합니다.
- **트리거 활성화 순서**: Workflow 내에서 조건부 트리거는 반드시 선행 트리거보다 먼저 활성화되어 있어야 합니다.
- **비용 관리**: 트리거 자체는 비용이 발생하지 않지만, 트리거가 실행하는 Job의 DPU 사용량에 대해 과금됩니다.

## 관련 서비스 비교

| 항목 | Glue Trigger | EventBridge Rule | Step Functions | Apache Airflow (MWAA) |
|------|-------------|-----------------|----------------|----------------------|
| 스케줄링 | cron/rate 지원 | cron/rate 지원 | 직접 지원 없음 (EventBridge 연동) | cron 표현식 지원 |
| 조건부 실행 | Job/Crawler 상태 기반 | 이벤트 패턴 매칭 | Choice State로 분기 | 태스크 의존성 DAG |
| 복잡한 워크플로 | Workflow와 함께 사용 | 제한적 | 매우 강력 | 매우 강력 |
| 서버리스 | 예 | 예 | 예 | 아니오 (관리형 클러스터) |
| Glue 네이티브 연동 | 최상 | 좋음 | 좋음 | 좋음 |
| 비용 | 무료 (Job 실행 비용만) | 이벤트당 과금 | 상태 전이당 과금 | 환경 운영 비용 |
| 모니터링 | Glue 콘솔 | CloudWatch | 콘솔 + X-Ray | Airflow UI |

**언제 Glue Trigger를 선택해야 하는가?**

- Glue Job과 Crawler만으로 구성된 단순한 ETL 파이프라인에 가장 적합합니다.
- 외부 서비스 연동이 필요 없고, Glue 생태계 내에서 완결되는 워크플로에 권장됩니다.
- 복잡한 분기 로직이나 다양한 AWS 서비스를 조합해야 한다면 Step Functions를 고려하는 것이 좋습니다.
- 이미 Airflow 기반 파이프라인이 있다면 Amazon MWAA와의 연동도 대안이 됩니다.

## 요약

AWS Glue Trigger는 ETL 작업의 실행 시점을 자동화하는 핵심 구성 요소입니다. 스케줄 트리거로 정기적인 배치 처리를, 조건부 트리거로 작업 간 의존성을, 온디맨드 트리거로 유연한 실행을 각각 지원합니다. Workflow와 결합하면 복잡한 다단계 파이프라인도 단일 단위로 관리할 수 있습니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **스케줄 트리거**: cron/rate 표현식으로 정해진 시간에 자동 실행 (UTC 기준 주의)
- **조건부 트리거**: 선행 Job/Crawler의 상태를 감지하여 AND/OR 논리로 후속 작업 실행
- **온디맨드 트리거**: API 호출 또는 콘솔에서 수동 실행
- **EventBridge 연동**: S3 이벤트 등 외부 이벤트 기반 실행 가능
- **모범 사례**: IAM 최소 권한, 재시도 설정, CloudWatch 알람, MaxConcurrentRuns 설정
- **Workflow 연계**: 트리거를 Workflow에 편입시켜 전체 파이프라인을 통합 관리

Glue Trigger는 그 자체로는 단순한 기능이지만, 올바르게 조합하면 완전 자동화된 서버리스 데이터 파이프라인의 근간이 됩니다. 다음 글에서는 이러한 트리거들을 하나의 파이프라인으로 엮는 AWS Glue Workflow에 대해 상세히 다루겠습니다.