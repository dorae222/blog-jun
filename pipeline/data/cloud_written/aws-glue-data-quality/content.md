# AWS Glue Data Quality

## 개요

AWS Glue Data Quality는 ETL 파이프라인 내에서 데이터 품질을 자동으로 측정, 모니터링, 관리할 수 있는 기능입니다. 2023년에 정식 출시된 이 기능은 DQDL(Data Quality Definition Language)이라는 전용 규칙 언어를 사용하여 데이터 품질 규칙을 선언적으로 정의하고, Glue ETL Job이나 Data Catalog 테이블에 직접 적용할 수 있습니다.

데이터 품질 문제는 비즈니스 의사결정에 직접적인 영향을 미칩니다. 잘못된 데이터가 분석 파이프라인을 통과하면 잘못된 보고서, 잘못된 ML 모델, 잘못된 비즈니스 결정으로 이어질 수 있습니다. Glue Data Quality는 이러한 문제를 파이프라인 단계에서 조기에 탐지하고 차단할 수 있게 해줍니다.

Glue Data Quality는 두 가지 주요 사용 방식을 제공합니다. 첫째, Data Catalog 테이블에 규칙셋을 연결하여 주기적으로 품질을 검사하는 방식입니다. 둘째, Glue ETL Job 내에서 EvaluateDataQuality 변환을 사용하여 파이프라인 실행 중에 실시간으로 품질을 검증하는 방식입니다.

## 핵심 기능

### 1. DQDL (Data Quality Definition Language)

DQDL은 데이터 품질 규칙을 정의하기 위한 전용 선언적 언어입니다. 직관적인 문법으로 다양한 품질 규칙을 표현할 수 있습니다.

주요 규칙 유형은 다음과 같습니다.

**완전성(Completeness) 규칙:**
- `Completeness`: 컬럼의 비결측값 비율 검사
- `IsComplete`: 컬럼에 결측값이 없는지 검사

**유일성(Uniqueness) 규칙:**
- `Uniqueness`: 컬럼의 유니크 값 비율 검사
- `IsPrimaryKey`: 컬럼이 기본키 역할을 하는지 검사

**일관성(Consistency) 규칙:**
- `ColumnCorrelation`: 두 컬럼 간 상관관계 검사
- `ReferentialIntegrity`: 참조 무결성 검사

**정확성(Accuracy) 규칙:**
- `ColumnValues`: 컬럼 값의 범위, 패턴, 목록 검사
- `CustomSql`: 커스텀 SQL로 복잡한 규칙 검사
- `DataFreshness`: 데이터 신선도 검사
- `RowCount`: 행 수 검사

```bash
# Data Catalog 테이블에 데이터 품질 규칙셋 생성
aws glue create-data-quality-ruleset \
  --name "user-events-quality-rules" \
  --ruleset 'Rules = [
    Completeness "user_id" > 0.99,
    Completeness "event_type" > 0.99,
    IsComplete "event_timestamp",
    Uniqueness "user_id" > 0.7,
    ColumnValues "event_type" in ["click", "view", "purchase", "signup"],
    ColumnValues "price" between 0 and 1000000,
    RowCount > 1000,
    IsPrimaryKey "event_id",
    DataFreshness "event_timestamp" <= 24 hours
  ]' \
  --target-table '{
    "TableName": "user_events",
    "DatabaseName": "analytics_db"
  }' \
  --description "사용자 이벤트 테이블 품질 규칙"
```

### 2. 자동 규칙 추천(Automated Rule Recommendations)

Glue Data Quality는 기존 데이터를 분석하여 자동으로 품질 규칙을 추천하는 기능을 제공합니다. 데이터의 통계적 특성을 기반으로 적절한 규칙을 제안합니다.

```bash
# 데이터 품질 규칙 추천 실행 시작
aws glue start-data-quality-rule-recommendation-run \
  --data-source '{
    "GlueTable": {
      "DatabaseName": "analytics_db",
      "TableName": "user_events"
    }
  }' \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --number-of-workers 5 \
  --timeout 60
```

```bash
# 추천 결과 조회
aws glue get-data-quality-rule-recommendation-run \
  --run-id "dqrun-abc123def456" \
  --query 'RecommendedRuleset'
```

추천 기능은 데이터의 분포, 결측값 패턴, 유니크 비율, 값 범위 등을 분석하여 규칙을 제안합니다. 제안된 규칙을 검토하고 필요에 따라 조정하여 사용하면 됩니다.

### 3. 품질 평가 실행(Evaluation Run)

정의된 규칙셋을 실제 데이터에 대해 실행하여 품질을 평가합니다.

```bash
# 데이터 품질 평가 실행
aws glue start-data-quality-ruleset-evaluation-run \
  --data-source '{
    "GlueTable": {
      "DatabaseName": "analytics_db",
      "TableName": "user_events"
    }
  }' \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --ruleset-names '["user-events-quality-rules"]' \
  --number-of-workers 5 \
  --timeout 60 \
  --additional-run-options '{"CloudWatchMetricsEnabled": true, "ResultsS3Prefix": "s3://my-data-lake/quality-results/"}'
```

```bash
# 평가 결과 조회
aws glue get-data-quality-ruleset-evaluation-run \
  --run-id "dqrun-xyz789" \
  --query '{Status:Status,ResultIds:ResultIds}'
```

```bash
# 상세 결과 확인
aws glue batch-get-data-quality-result \
  --result-ids '["dqresult-abc123"]' \
  --query 'Results[0].{Score:Score,RuleResults:RuleResults}'
```

### 4. ETL Job 내 인라인 품질 검사

Glue ETL Job의 PySpark 코드 내에서 `EvaluateDataQuality` 변환을 사용하여 파이프라인 실행 중에 데이터 품질을 검증할 수 있습니다.

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsgluedq.transforms import EvaluateDataQuality

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 소스 데이터 로드
source_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="analytics_db",
    table_name="user_events"
)

# DQDL 규칙 정의
ruleset = """
    Rules = [
        Completeness "user_id" > 0.99,
        IsComplete "event_timestamp",
        ColumnValues "event_type" in ["click", "view", "purchase", "signup"],
        ColumnValues "price" >= 0,
        RowCount > 100
    ]
"""

# 데이터 품질 평가 실행
dq_results = EvaluateDataQuality.apply(
    frame=source_dyf,
    ruleset=ruleset,
    publishing_options={
        "dataQualityEvaluationContext": "user_events_quality",
        "enableDataQualityCloudWatchMetrics": True,
        "enableDataQualityResultsPublishing": True
    }
)

# 품질 결과 확인
dq_results.toDF().show(truncate=False)

# 품질 통과 데이터만 후속 처리
# EvaluateDataQuality는 원본 데이터와 결과를 모두 반환
row_level_results = EvaluateDataQuality.apply(
    frame=source_dyf,
    ruleset=ruleset,
    publishing_options={
        "dataQualityEvaluationContext": "row_level_check",
        "enableDataQualityCloudWatchMetrics": True
    },
    additional_options={"performanceTuning.caching": "CACHE_NOTHING"}
)

job.commit()
```

### 5. CloudWatch 통합

데이터 품질 평가 결과는 CloudWatch 메트릭으로 자동 발행될 수 있습니다. 이를 통해 품질 추이를 모니터링하고 알람을 설정할 수 있습니다.

```bash
# CloudWatch 알람 생성 (데이터 품질 점수 임계값)
aws cloudwatch put-metric-alarm \
  --alarm-name "user-events-quality-alarm" \
  --alarm-description "사용자 이벤트 데이터 품질 점수 하락 알람" \
  --metric-name "glue.data.quality.overall.score" \
  --namespace "Glue" \
  --statistic Average \
  --period 3600 \
  --threshold 0.9 \
  --comparison-operator LessThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions "arn:aws:sns:ap-northeast-2:123456789012:data-quality-alerts" \
  --dimensions Name=RulesetName,Value=user-events-quality-rules
```

## 아키텍처/동작 원리

### Data Quality 평가 흐름

```
[Data Catalog 테이블 / DynamicFrame]
          |
          v
  [DQDL 규칙셋 파싱]
          |
          v
  [Spark 실행 계획 생성]
  - 각 규칙을 Spark 연산으로 변환
  - 집계/통계 쿼리 생성
          |
          v
  [분산 실행 (Glue Worker)]
  - 규칙별 평가 병렬 수행
  - 각 규칙의 통과/실패 판정
          |
          v
  [결과 집계]
  - 전체 품질 점수 (Overall Score)
  - 규칙별 상세 결과
  - 행 수준 결과 (선택)
          |
          v
  [결과 발행]
  - Data Catalog 메타데이터
  - CloudWatch 메트릭
  - S3 결과 파일
  - EventBridge 이벤트
```

### 품질 점수 산출 방식

전체 품질 점수(Overall Score)는 정의된 모든 규칙의 통과 비율로 산출됩니다. 예를 들어, 10개 규칙 중 8개가 통과하면 점수는 0.8(80%)입니다.

각 규칙의 평가 결과는 다음 상태 중 하나를 가집니다.

- **PASS**: 규칙을 충족함
- **FAIL**: 규칙을 충족하지 못함
- **ERROR**: 규칙 평가 중 오류 발생

### 행 수준 결과(Row-Level Results)

Glue Data Quality는 테이블 수준뿐만 아니라 행 수준에서도 품질을 평가할 수 있습니다. 행 수준 평가를 활성화하면 각 행이 어떤 규칙을 위반했는지 식별할 수 있어, 불량 데이터를 격리하거나 수정하는 데 유용합니다.

### DQDL 규칙의 Spark 변환

DQDL로 정의된 규칙은 내부적으로 Spark DataFrame 연산으로 변환됩니다. 예를 들어 `Completeness "user_id" > 0.99` 규칙은 다음과 유사한 Spark 연산으로 변환됩니다.

```python
# 내부적으로 이와 유사한 연산이 수행됨 (개념 설명)
completeness = df.filter(col("user_id").isNotNull()).count() / df.count()
assert completeness > 0.99
```

## 실전 활용

### 사례 1: ETL 파이프라인 품질 게이트

ETL 파이프라인에서 데이터 품질 검사를 통과한 데이터만 다음 단계로 전달하는 품질 게이트 패턴입니다.

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsgluedq.transforms import EvaluateDataQuality
import boto3

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 소스 데이터 로드
source_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="raw_db",
    table_name="orders"
)

# 1단계: 소스 데이터 품질 검사
source_ruleset = """
    Rules = [
        RowCount > 0,
        Completeness "order_id" = 1.0,
        Completeness "customer_id" > 0.99,
        Completeness "order_date" > 0.99,
        ColumnValues "total_amount" >= 0,
        IsPrimaryKey "order_id",
        DataFreshness "order_date" <= 48 hours
    ]
"""

dq_result = EvaluateDataQuality.apply(
    frame=source_dyf,
    ruleset=source_ruleset,
    publishing_options={
        "dataQualityEvaluationContext": "source_quality_gate",
        "enableDataQualityCloudWatchMetrics": True,
        "enableDataQualityResultsPublishing": True
    }
)

# 품질 점수 확인
result_df = dq_result.toDF()
result_df.show(truncate=False)

# 전체 통과 여부 판단
failed_rules = result_df.filter(result_df.Outcome == "Failed").count()

if failed_rules > 0:
    # 품질 실패 시 SNS 알림 발송
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:ap-northeast-2:123456789012:data-quality-alerts',
        Subject='데이터 품질 검사 실패',
        Message=f'Orders 테이블 품질 검사에서 {failed_rules}개 규칙이 실패했습니다.'
    )
    # 실패 데이터를 quarantine 영역으로 이동
    glueContext.write_dynamic_frame.from_options(
        frame=source_dyf,
        connection_type="s3",
        connection_options={"path": "s3://my-data-lake/quarantine/orders/"},
        format="parquet"
    )
else:
    # 품질 통과 시 변환 후 적재
    transformed_dyf = ApplyMapping.apply(
        frame=source_dyf,
        mappings=[
            ("order_id", "string", "order_id", "string"),
            ("customer_id", "string", "customer_id", "string"),
            ("order_date", "string", "order_date", "date"),
            ("total_amount", "double", "total_amount", "decimal")
        ]
    )
    glueContext.write_dynamic_frame.from_catalog(
        frame=transformed_dyf,
        database="curated_db",
        table_name="orders_curated"
    )

job.commit()
```

### 사례 2: 정기적 데이터 품질 모니터링

```bash
# 여러 테이블에 대한 품질 규칙셋 일괄 생성

# 주문 테이블 규칙
aws glue create-data-quality-ruleset \
  --name "orders-quality" \
  --ruleset 'Rules = [
    RowCount > 100,
    Completeness "order_id" = 1.0,
    Completeness "customer_id" > 0.99,
    ColumnValues "status" in ["pending", "confirmed", "shipped", "delivered", "cancelled"],
    ColumnValues "total_amount" between 0 and 10000000,
    IsPrimaryKey "order_id"
  ]' \
  --target-table '{"TableName": "orders", "DatabaseName": "production_db"}'

# 고객 테이블 규칙
aws glue create-data-quality-ruleset \
  --name "customers-quality" \
  --ruleset 'Rules = [
    RowCount > 0,
    Completeness "customer_id" = 1.0,
    Completeness "email" > 0.95,
    Uniqueness "email" > 0.99,
    ColumnValues "email" matches "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
    IsPrimaryKey "customer_id"
  ]' \
  --target-table '{"TableName": "customers", "DatabaseName": "production_db"}'
```

```bash
# 품질 규칙셋 목록 조회
aws glue list-data-quality-rulesets \
  --filter '{"TargetTable": {"DatabaseName": "production_db"}}'
```

### 사례 3: 이상치 탐지와 분기 처리

품질 검사 결과에 따라 데이터를 양품/불량품으로 분리하는 패턴입니다.

```python
from awsgluedq.transforms import EvaluateDataQuality

# 행 수준 품질 평가
row_quality_ruleset = """
    Rules = [
        IsComplete "price",
        ColumnValues "price" between 0 and 100000,
        IsComplete "quantity",
        ColumnValues "quantity" between 1 and 10000
    ]
"""

# 행 수준 결과를 포함한 평가 (Glue Studio 비주얼 편집기에서도 가능)
evaluation_result = EvaluateDataQuality.apply(
    frame=source_dyf,
    ruleset=row_quality_ruleset,
    publishing_options={
        "dataQualityEvaluationContext": "row_level_quality",
        "enableDataQualityCloudWatchMetrics": True
    },
    additional_options={
        "observations.scope": "ALL",
        "performanceTuning.caching": "CACHE_NOTHING"
    }
)
```

### 사례 4: 참조 무결성 검사

여러 테이블 간의 참조 무결성을 검사하는 규칙을 정의할 수 있습니다.

```bash
# 참조 무결성 규칙이 포함된 규칙셋
aws glue create-data-quality-ruleset \
  --name "orders-referential-integrity" \
  --ruleset 'Rules = [
    ReferentialIntegrity "customer_id" "reference_db.customers.customer_id" > 0.99,
    ReferentialIntegrity "product_id" "reference_db.products.product_id" > 0.99
  ]' \
  --target-table '{"TableName": "orders", "DatabaseName": "production_db"}'
```

## 모범 사례/보안

### 품질 규칙 설계 모범 사례

1. **단계적 규칙 적용**: 처음에는 느슨한 규칙으로 시작하여 점진적으로 엄격하게 조정합니다. 자동 추천 기능을 활용하여 기준선을 설정합니다.

2. **규칙 카테고리 분류**: 완전성, 유일성, 유효성, 적시성 등 카테고리별로 규칙을 구성하면 관리가 용이합니다.

3. **임계값 설정**: 절대적인 규칙(= 1.0)과 허용 범위가 있는 규칙(> 0.99)을 적절히 혼합합니다. 처음부터 100%를 요구하면 불필요한 파이프라인 중단이 발생할 수 있습니다.

4. **CustomSql 활용**: DQDL 내장 규칙으로 표현하기 어려운 복잡한 비즈니스 로직은 CustomSql 규칙을 활용합니다.

```bash
# CustomSql을 포함한 규칙셋
aws glue create-data-quality-ruleset \
  --name "complex-quality-rules" \
  --ruleset 'Rules = [
    CustomSql "SELECT COUNT(*) FROM primary WHERE total_amount != (unit_price * quantity)" <= 10,
    CustomSql "SELECT COUNT(DISTINCT date_col) FROM primary WHERE date_col > current_date()" = 0
  ]' \
  --target-table '{"TableName": "orders", "DatabaseName": "production_db"}'
```

5. **데이터 신선도 모니터링**: `DataFreshness` 규칙을 활용하여 데이터가 적시에 적재되는지 모니터링합니다.

### 보안 모범 사례

1. **IAM 권한 분리**: 규칙셋을 생성/수정하는 권한과 평가를 실행하는 권한을 분리합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDataQualityRuleset",
        "glue:ListDataQualityRulesets",
        "glue:StartDataQualityRulesetEvaluationRun",
        "glue:GetDataQualityRulesetEvaluationRun",
        "glue:BatchGetDataQualityResult"
      ],
      "Resource": "*"
    }
  ]
}
```

2. **결과 데이터 접근 제어**: 품질 평가 결과가 저장되는 S3 경로에 대한 접근 권한을 적절히 제한합니다.

3. **알림 채널 보안**: SNS 토픽이나 EventBridge 규칙의 대상에 대한 접근 권한을 검토합니다.

### 운영 모범 사례

1. **자동 추천으로 시작**: 새로운 데이터셋에는 자동 규칙 추천을 먼저 실행하여 기준선을 확보합니다.

2. **품질 추이 대시보드**: CloudWatch 메트릭을 활용하여 시간에 따른 품질 추이를 시각화합니다.

3. **품질 실패 시 대응 프로세스**: 품질 검사 실패 시 자동으로 알림을 발송하고, 필요에 따라 파이프라인을 중단하는 프로세스를 수립합니다.

4. **quarantine 패턴**: 불량 데이터를 격리(quarantine) 영역으로 분리하고, 검토 후 재처리하는 패턴을 적용합니다.

## 관련 서비스 비교

| 항목 | AWS Glue Data Quality | Deequ (오픈소스) | Great Expectations | Amazon DataZone |
|------|----------------------|------------------|-------------------|-----------------|
| 관리 방식 | 완전 관리형 | 자체 관리 | 자체 관리 | 완전 관리형 |
| 규칙 언어 | DQDL | Scala/Python DSL | Python/YAML | 메타데이터 기반 |
| Glue 통합 | 네이티브 | 라이브러리 추가 | 라이브러리 추가 | 카탈로그 통합 |
| 자동 규칙 추천 | 지원 | 지원 (Constraint Suggestion) | 지원 (Profiling) | 제한적 |
| 행 수준 결과 | 지원 | 지원 | 지원 | 미지원 |
| CloudWatch 통합 | 네이티브 | 커스텀 구현 필요 | 커스텀 구현 필요 | 네이티브 |
| 참조 무결성 | 지원 | 커스텀 구현 | 지원 | 미지원 |
| 비용 | Glue 실행 비용에 포함 | 무료 (인프라 비용만) | 무료 (인프라 비용만) | 별도 과금 |

참고로 Glue Data Quality는 내부적으로 Deequ 오픈소스 라이브러리를 기반으로 구축되었습니다. Deequ의 핵심 기능을 서버리스 관리형 서비스로 제공하면서 DQDL이라는 직관적인 규칙 언어를 추가한 것입니다.

## 요약

AWS Glue Data Quality는 ETL 파이프라인에서 데이터 품질을 선언적으로 관리할 수 있는 관리형 서비스입니다. DQDL을 사용하여 완전성, 유일성, 유효성, 적시성 등 다양한 품질 규칙을 정의하고, 자동 규칙 추천 기능으로 초기 규칙 설정의 부담을 줄여줍니다.

Data Catalog 테이블 수준의 정기 검사와 ETL Job 내 인라인 검사를 모두 지원하며, CloudWatch와의 네이티브 통합으로 품질 추이 모니터링과 알람 설정이 용이합니다. 행 수준 결과를 활용하면 불량 데이터를 격리하는 quarantine 패턴을 구현할 수 있습니다.

효과적인 데이터 품질 관리를 위해서는 자동 추천으로 기준선을 확보한 후 단계적으로 규칙을 강화하고, 품질 실패 시 자동 대응 프로세스를 수립하며, CloudWatch 대시보드를 통해 지속적으로 추이를 모니터링하는 것을 권장합니다.