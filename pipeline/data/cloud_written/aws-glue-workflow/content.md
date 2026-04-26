<!-- infographic-hero -->
![AWS Glue Workflow - 복잡한 ETL 파이프라인 오케스트레이션 완벽 가이드 핵심 요약](figures/infographic.svg)

*Figure: AWS Glue Workflow - 복잡한 ETL 파이프라인 오케스트레이션 완벽 가이드 한 장 요약 인포그래픽*

## 개요

AWS Glue Workflow는 여러 Glue Job, Crawler, Trigger를 하나의 논리적 단위로 묶어 관리하는 오케스트레이션 기능입니다. 실무에서 ETL 파이프라인은 단일 작업으로 끝나는 경우가 드뭅니다. 데이터 수집, 검증, 변환, 적재, 후처리 등 다양한 단계가 순차적 또는 병렬로 연결되어야 하며, 각 단계의 성공과 실패에 따른 분기 처리도 필요합니다.

Glue Workflow는 이러한 복잡한 파이프라인을 시각적으로 설계하고, 하나의 실행 단위로 관리할 수 있게 해줍니다. Workflow를 사용하면 전체 파이프라인의 실행 상태를 한눈에 파악할 수 있고, 실행 이력 추적과 디버깅이 용이해집니다.

본 글에서는 Glue Workflow의 구조와 동작 원리를 깊이 있게 살펴보고, AWS CLI를 활용한 실전 구성 방법과 프로덕션 환경에서의 운영 노하우를 공유합니다.

## 핵심 기능

### Workflow 구성 요소

Glue Workflow는 다음 세 가지 요소의 조합으로 구성됩니다.

- **Job**: 실제 ETL 로직을 수행하는 Apache Spark 또는 Python Shell 작업
- **Crawler**: 데이터 소스를 탐색하여 Data Catalog에 메타데이터를 등록하는 작업
- **Trigger**: Job과 Crawler의 실행 시점과 조건을 제어하는 구성 요소

Workflow는 이 세 요소를 DAG(Directed Acyclic Graph) 형태로 연결하여 복잡한 파이프라인을 표현합니다.

### Workflow 생성 및 기본 구성

```bash
# Workflow 생성
aws glue create-workflow \
  --name "data-warehouse-pipeline" \
  --description "일일 데이터 웨어하우스 적재 파이프라인" \
  --default-run-properties '{
    "processing_date": "2024-01-15",
    "environment": "production"
  }' \
  --max-concurrent-runs 1
```

`--default-run-properties`는 Workflow 내 모든 Job에서 접근할 수 있는 공유 파라미터입니다. Job 스크립트에서 `workflow_params = glueContext.get_workflow_run_properties(workflow_run_id)` 형태로 읽어올 수 있습니다.

### Workflow에 Trigger 연결

Workflow의 핵심은 트리거를 통해 작업 간 의존성을 정의하는 것입니다.

```bash
# Step 1: Workflow 시작 트리거 (스케줄 기반)
aws glue create-trigger \
  --name "wf-start-trigger" \
  --workflow-name "data-warehouse-pipeline" \
  --type SCHEDULED \
  --schedule "cron(0 17 * * ? *)" \
  --actions '[
    {"JobName": "extract-rds-job"},
    {"JobName": "extract-api-job"},
    {"CrawlerName": "s3-raw-data-crawler"}
  ]' \
  --start-on-creation

# Step 2: 모든 추출 작업 완료 후 변환 시작
aws glue create-trigger \
  --name "wf-transform-trigger" \
  --workflow-name "data-warehouse-pipeline" \
  --type CONDITIONAL \
  --predicate '{
    "Logical": "AND",
    "Conditions": [
      {"LogicalOperator": "EQUALS", "JobName": "extract-rds-job", "State": "SUCCEEDED"},
      {"LogicalOperator": "EQUALS", "JobName": "extract-api-job", "State": "SUCCEEDED"},
      {"LogicalOperator": "EQUALS", "CrawlerName": "s3-raw-data-crawler", "CrawlState": "SUCCEEDED"}
    ]
  }' \
  --actions '[{"JobName": "transform-and-merge-job"}]' \
  --start-on-creation

# Step 3: 변환 완료 후 적재 및 품질 검증
aws glue create-trigger \
  --name "wf-load-trigger" \
  --workflow-name "data-warehouse-pipeline" \
  --type CONDITIONAL \
  --predicate '{
    "Conditions": [{
      "LogicalOperator": "EQUALS",
      "JobName": "transform-and-merge-job",
      "State": "SUCCEEDED"
    }]
  }' \
  --actions '[
    {"JobName": "load-to-redshift-job"},
    {"JobName": "data-quality-check-job"}
  ]' \
  --start-on-creation

# Step 4: 최종 정리 작업
aws glue create-trigger \
  --name "wf-cleanup-trigger" \
  --workflow-name "data-warehouse-pipeline" \
  --type CONDITIONAL \
  --predicate '{
    "Logical": "AND",
    "Conditions": [
      {"LogicalOperator": "EQUALS", "JobName": "load-to-redshift-job", "State": "SUCCEEDED"},
      {"LogicalOperator": "EQUALS", "JobName": "data-quality-check-job", "State": "SUCCEEDED"}
    ]
  }' \
  --actions '[{"JobName": "cleanup-staging-job"}]' \
  --start-on-creation
```

### Workflow Run Properties 활용

Workflow의 런타임 속성은 Job 간 데이터를 공유하는 메커니즘을 제공합니다.

```python
# Glue Job 스크립트 내에서 Workflow Run Properties 읽기/쓰기
import sys
import boto3
from awsglue.utils import getResolvedOptions

args = getResolvedOptions(sys.argv, ['WORKFLOW_NAME', 'WORKFLOW_RUN_ID'])
glue_client = boto3.client('glue')

# Workflow Run Properties 읽기
workflow_run = glue_client.get_workflow_run(
    Name=args['WORKFLOW_NAME'],
    RunId=args['WORKFLOW_RUN_ID']
)
run_properties = workflow_run['Run']['WorkflowRunProperties']
processing_date = run_properties.get('processing_date', '2024-01-15')

# Workflow Run Properties 업데이트 (후속 Job에 값 전달)
glue_client.put_workflow_run_properties(
    Name=args['WORKFLOW_NAME'],
    RunId=args['WORKFLOW_RUN_ID'],
    RunProperties={
        **run_properties,
        'records_processed': '1500000',
        'extract_status': 'completed'
    }
)
```

```bash
# CLI로 Workflow Run Properties 확인
aws glue get-workflow-run \
  --name "data-warehouse-pipeline" \
  --run-id "wr_abc123def456" \
  --query 'Run.WorkflowRunProperties'
```

## 아키텍처/동작 원리

### Workflow 실행 흐름

```
[Workflow 시작]
       |
       v
[시작 트리거 평가 (SCHEDULED/ON_DEMAND)]
       |
       v
[병렬 실행: Job A, Job B, Crawler C]
       |         |           |
       v         v           v
  [완료]    [완료]      [완료]
       \        |        /
        v       v       v
[조건부 트리거 평가 (AND 조건)]
       |
       v
[다음 단계 Job 실행]
       |
       v
[Workflow 실행 완료 → 상태 기록]
```

### Workflow 실행 상태

Workflow Run은 다음과 같은 상태를 가집니다.

| 상태 | 설명 |
|------|------|
| RUNNING | 하나 이상의 Job 또는 Crawler가 실행 중 |
| COMPLETED | 모든 작업이 완료됨 (성공 또는 실패 포함) |
| STOPPING | 중단 요청을 처리 중 |
| STOPPED | 사용자에 의해 중단됨 |
| ERROR | Workflow 자체에서 오류 발생 |

중요한 점은, **Workflow의 COMPLETED 상태가 모든 Job의 성공을 의미하지 않는다**는 것입니다. 일부 Job이 실패하더라도 더 이상 실행할 트리거가 없으면 COMPLETED로 전환됩니다. 따라서 개별 Job의 성공 여부는 별도로 확인해야 합니다.

### 그래프 구조와 노드 탐색

```bash
# Workflow의 전체 그래프 구조 조회
aws glue get-workflow \
  --name "data-warehouse-pipeline" \
  --include-graph

# 특정 실행의 그래프와 노드 상태 조회
aws glue get-workflow-run \
  --name "data-warehouse-pipeline" \
  --run-id "wr_abc123def456" \
  --include-graph
```

그래프 응답에는 각 노드(Job, Crawler, Trigger)의 실행 상태와 시작/종료 시간이 포함되어, 전체 파이프라인의 실행 과정을 상세히 추적할 수 있습니다.

### Blueprint를 활용한 템플릿화

AWS Glue Blueprint는 반복적으로 사용되는 Workflow 패턴을 템플릿으로 만들 수 있는 기능입니다. 데이터 소스나 대상 테이블만 바꿔가며 동일한 구조의 파이프라인을 여러 개 생성할 때 유용합니다.

```bash
# Blueprint 목록 조회
aws glue list-blueprints

# Blueprint로부터 Workflow 생성
aws glue start-blueprint-run \
  --blueprint-name "etl-pipeline-template" \
  --role-arn "arn:aws:iam::123456789012:role/GlueBlueprintRole" \
  --parameters '{"source_database": "sales_db", "target_bucket": "s3://analytics-dw/"}'
```

## 실전 활용

### 사례 1: 데이터 레이크 ETL 파이프라인

S3 기반 데이터 레이크에서 원본 데이터를 정제하고 파티셔닝하는 전체 파이프라인입니다.

```bash
# 1. Workflow 생성
aws glue create-workflow \
  --name "data-lake-etl" \
  --description "S3 데이터 레이크 ETL 파이프라인" \
  --max-concurrent-runs 1

# 2. 시작 트리거: 매일 새벽 1시
aws glue create-trigger \
  --name "dl-start" \
  --workflow-name "data-lake-etl" \
  --type SCHEDULED \
  --schedule "cron(0 16 * * ? *)" \
  --actions '[{"CrawlerName": "raw-zone-crawler"}]' \
  --start-on-creation

# 3. 크롤러 완료 후 정제 작업
aws glue create-trigger \
  --name "dl-after-crawl" \
  --workflow-name "data-lake-etl" \
  --type CONDITIONAL \
  --predicate '{
    "Conditions": [{
      "LogicalOperator": "EQUALS",
      "CrawlerName": "raw-zone-crawler",
      "CrawlState": "SUCCEEDED"
    }]
  }' \
  --actions '[
    {"JobName": "cleanse-user-data"},
    {"JobName": "cleanse-transaction-data"},
    {"JobName": "cleanse-product-data"}
  ]' \
  --start-on-creation

# 4. 정제 완료 후 통합 분석 테이블 생성
aws glue create-trigger \
  --name "dl-aggregate" \
  --workflow-name "data-lake-etl" \
  --type CONDITIONAL \
  --predicate '{
    "Logical": "AND",
    "Conditions": [
      {"LogicalOperator": "EQUALS", "JobName": "cleanse-user-data", "State": "SUCCEEDED"},
      {"LogicalOperator": "EQUALS", "JobName": "cleanse-transaction-data", "State": "SUCCEEDED"},
      {"LogicalOperator": "EQUALS", "JobName": "cleanse-product-data", "State": "SUCCEEDED"}
    ]
  }' \
  --actions '[{"JobName": "build-analytics-tables"}]' \
  --start-on-creation

# 5. 분석 테이블 완료 후 Athena 카탈로그 업데이트
aws glue create-trigger \
  --name "dl-catalog-update" \
  --workflow-name "data-lake-etl" \
  --type CONDITIONAL \
  --predicate '{
    "Conditions": [{
      "LogicalOperator": "EQUALS",
      "JobName": "build-analytics-tables",
      "State": "SUCCEEDED"
    }]
  }' \
  --actions '[{"CrawlerName": "analytics-zone-crawler"}]' \
  --start-on-creation
```

### 사례 2: Workflow 실행 모니터링 스크립트

```bash
# Workflow 실행 이력 조회
aws glue get-workflow-runs \
  --name "data-lake-etl" \
  --max-results 10

# 특정 실행의 상세 정보와 각 노드 상태 확인
aws glue get-workflow-run \
  --name "data-lake-etl" \
  --run-id "wr_abc123" \
  --include-graph \
  --query 'Run.{Status: Status, StartedOn: StartedOn, CompletedOn: CompletedOn, Statistics: Statistics}'
```

### 사례 3: Workflow 수동 실행 및 런타임 속성 오버라이드

```bash
# 기본 속성으로 수동 실행
aws glue start-workflow-run \
  --name "data-lake-etl"

# 런타임 속성을 오버라이드하여 실행
aws glue start-workflow-run \
  --name "data-lake-etl" \
  --run-properties '{
    "processing_date": "2024-01-10",
    "environment": "production",
    "full_refresh": "true"
  }'
```

### 사례 4: CloudFormation으로 Workflow 정의

인프라스트럭처를 코드로 관리하려면 CloudFormation을 활용합니다.

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Glue Workflow Pipeline

Resources:
  DataPipelineWorkflow:
    Type: AWS::Glue::Workflow
    Properties:
      Name: data-pipeline-workflow
      Description: CloudFormation managed ETL pipeline
      DefaultRunProperties:
        environment: production
      MaxConcurrentRuns: 1

  StartTrigger:
    Type: AWS::Glue::Trigger
    Properties:
      Name: wf-start
      WorkflowName: !Ref DataPipelineWorkflow
      Type: SCHEDULED
      Schedule: "cron(0 17 * * ? *)"
      StartOnCreation: true
      Actions:
        - JobName: extract-job

  TransformTrigger:
    Type: AWS::Glue::Trigger
    Properties:
      Name: wf-transform
      WorkflowName: !Ref DataPipelineWorkflow
      Type: CONDITIONAL
      StartOnCreation: true
      Predicate:
        Conditions:
          - LogicalOperator: EQUALS
            JobName: extract-job
            State: SUCCEEDED
      Actions:
        - JobName: transform-job
```

## 모범 사례/보안

### 오류 처리 패턴

**패턴 1: 실패 시 알림 발송**

```bash
# EventBridge를 활용한 Workflow 실패 감지
aws events put-rule \
  --name "glue-workflow-failure" \
  --event-pattern '{
    "source": ["aws.glue"],
    "detail-type": ["Glue Job State Change"],
    "detail": {
      "state": ["FAILED", "TIMEOUT"],
      "jobName": [{"prefix": "data-lake-"}]
    }
  }'

aws events put-targets \
  --rule "glue-workflow-failure" \
  --targets '[{
    "Id": "sns-notification",
    "Arn": "arn:aws:sns:ap-northeast-2:123456789012:data-team-alerts"
  }]'
```

**패턴 2: 실패 작업 재실행**

특정 작업만 실패한 경우, 전체 Workflow를 재실행하는 대신 실패한 Job만 개별적으로 재실행할 수 있습니다.

```bash
# 실패한 Job Run 확인
aws glue get-workflow-run \
  --name "data-lake-etl" \
  --run-id "wr_abc123" \
  --include-graph \
  --query 'Run.Graph.Nodes[?{JobDetails: JobDetails}].{Name: Name, State: JobDetails.JobRuns[0].JobRunState}'

# 실패한 Job 개별 재실행
aws glue start-job-run \
  --job-name "cleanse-transaction-data" \
  --arguments '{
    "--processing_date": "2024-01-15"
  }'
```

### 동시 실행 제어

```bash
# Workflow 레벨 동시 실행 제한
aws glue update-workflow \
  --name "data-lake-etl" \
  --max-concurrent-runs 1

# Job 레벨 동시 실행 제한
aws glue update-job \
  --job-name "transform-job" \
  --job-update '{"MaxRetries": 2, "Timeout": 180}'
```

### 리소스 태깅 전략

```bash
# Workflow에 태그 적용
aws glue tag-resource \
  --resource-arn "arn:aws:glue:ap-northeast-2:123456789012:workflow/data-lake-etl" \
  --tags-to-add '{
    "Project": "data-lake",
    "Environment": "production",
    "Owner": "data-engineering",
    "CostCenter": "DE-001"
  }'
```

### 보안 고려사항

- **IAM 역할 분리**: Workflow 관리 역할과 Job 실행 역할을 분리합니다. Workflow를 생성하고 관리하는 역할은 `glue:CreateWorkflow`, `glue:UpdateWorkflow` 등의 권한을, Job 실행 역할은 데이터 소스 접근 권한을 각각 부여합니다.
- **VPC 보안**: Glue Job이 RDS, Redshift 등 VPC 내 리소스에 접근해야 하는 경우, Glue Connection을 통해 VPC 서브넷과 보안 그룹을 설정합니다.
- **암호화**: Job Bookmark, 임시 파일, Data Catalog 메타데이터 모두 KMS 키로 암호화할 수 있습니다.
- **CloudTrail 감사**: Workflow 생성, 수정, 삭제, 실행 등 모든 API 호출이 CloudTrail에 기록됩니다.

## 관련 서비스 비교

| 항목 | Glue Workflow | Step Functions | MWAA (Airflow) | Data Pipeline (레거시) |
|------|-------------|----------------|----------------|---------------------|
| 대상 워크로드 | Glue ETL 전용 | 범용 워크플로 | 범용 데이터 파이프라인 | ETL/데이터 이동 |
| 서버리스 | 예 | 예 | 아니오 | 아니오 |
| 시각적 편집기 | Glue 콘솔 그래프 | Workflow Studio | Airflow DAG UI | 콘솔 편집기 |
| 프로그래밍 모델 | 선언적 (트리거+조건) | JSON/YAML ASL | Python DAG | JSON Pipeline Definition |
| Glue 네이티브 연동 | 최상 | SDK 통해 연동 | Operator 통해 연동 | 제한적 |
| 복잡한 분기 로직 | 제한적 | 매우 강력 | 매우 강력 | 보통 |
| 비용 | 무료 (Job만 과금) | 상태 전이당 과금 | 환경 운영 비용 | 사용량 기반 |
| 재시도/오류 처리 | Job 레벨 재시도 | 내장 재시도+Catch | 태스크 레벨 재시도 | 재시도 설정 |
| 상태 | GA | GA | GA | 지원 종료 예정 |

**Glue Workflow가 적합한 경우:**
- ETL 파이프라인이 Glue Job과 Crawler로만 구성된 경우
- 추가 인프라 비용 없이 파이프라인을 관리하고 싶은 경우
- 단순한 의존성 체인으로 충분한 경우

**Step Functions가 더 적합한 경우:**
- Lambda, ECS, SageMaker 등 다양한 서비스를 조합해야 하는 경우
- 복잡한 분기, 병렬, 맵, 에러 처리 로직이 필요한 경우

## 요약

AWS Glue Workflow는 Glue 생태계 내에서 ETL 파이프라인을 오케스트레이션하는 가장 자연스러운 방법입니다. 핵심 내용을 정리하면 다음과 같습니다.

- **통합 관리**: 여러 Job, Crawler, Trigger를 하나의 Workflow로 묶어 단일 실행 단위로 관리합니다.
- **DAG 구조**: 작업 간 의존성을 조건부 트리거의 AND/OR 논리로 표현하여 병렬 실행과 순차 실행을 조합합니다.
- **Run Properties**: Workflow 레벨 공유 파라미터를 통해 Job 간 데이터를 전달할 수 있습니다.
- **모니터링**: 전체 파이프라인의 실행 이력과 각 노드의 상태를 통합적으로 조회할 수 있습니다.
- **Blueprint**: 반복되는 파이프라인 패턴을 템플릿화하여 재사용할 수 있습니다.
- **무료**: Workflow 자체는 추가 비용이 없으며, 실행하는 Job과 Crawler의 비용만 발생합니다.
- **한계**: 복잡한 분기 로직이나 Glue 외 서비스 연동이 필요하면 Step Functions 또는 MWAA를 검토합니다.

Glue Workflow는 복잡성을 최소화하면서도 안정적인 ETL 파이프라인을 운영하고자 하는 팀에게 가장 적합한 선택입니다.