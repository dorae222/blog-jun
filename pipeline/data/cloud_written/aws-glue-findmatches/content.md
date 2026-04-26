<!-- infographic-hero -->
![AWS Glue FindMatches 핵심 요약](figures/infographic.svg)

*Figure: AWS Glue FindMatches 한 장 요약 인포그래픽*

# AWS Glue FindMatches

## 개요

AWS Glue FindMatches는 머신러닝(ML) 기반의 레코드 매칭 서비스로, 정확히 일치하지 않는(fuzzy) 중복 레코드를 탐지하고 연결합니다. 전통적인 문자열 비교나 규칙 기반 매칭으로는 해결하기 어려운 엔터티 해상도(Entity Resolution) 문제를 ML 모델로 해결합니다.

예를 들어, 동일 고객이 다음과 같이 여러 형태로 등록되어 있을 수 있습니다.
- "김철수", "서울특별시 강남구 역삼동 123-4", "010-1234-5678"
- "Kim Cheolsu", "서울 강남구 역삼동 123-4번지", "01012345678"
- "김철수", "서울시 강남구 역삼동", "010-1234-5678"

이런 레코드들을 동일 엔터티로 식별하는 것이 FindMatches의 핵심 역할입니다. 사용자가 일부 레코드 쌍에 대해 "같다/다르다"라는 레이블을 제공하면, FindMatches는 이를 학습하여 전체 데이터셋에 적용합니다.

FindMatches는 AWS Glue ML Transform의 한 유형이며, Glue ETL Job 내에서 또는 독립적으로 사용할 수 있습니다. 코드 작성 없이 콘솔이나 API를 통해 설정하고, 결과를 ETL 파이프라인에 통합할 수 있습니다.

## 핵심 기능

### 1. ML Transform 생성과 설정

FindMatches를 사용하려면 먼저 ML Transform을 생성합니다.

```bash
# FindMatches ML Transform 생성
aws glue create-ml-transform \
  --name "customer-dedup-transform" \
  --input-record-tables '[{
    "DatabaseName": "raw_db",
    "TableName": "customers"
  }]' \
  --parameters '{
    "TransformType": "FIND_MATCHES",
    "FindMatchesParameters": {
      "PrimaryKeyColumnName": "customer_id",
      "PrecisionRecallTradeoff": 0.9,
      "AccuracyCostTradeoff": 0.5,
      "EnforceProvidedLabels": true
    }
  }' \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --glue-version "4.0" \
  --number-of-workers 5 \
  --worker-type "G.1X" \
  --description "고객 중복 제거용 ML Transform"
```

주요 파라미터를 설명합니다.

- **PrimaryKeyColumnName**: 각 레코드를 고유하게 식별하는 컬럼입니다.
- **PrecisionRecallTradeoff**: 정밀도-재현율 균형을 조정합니다. 값이 1에 가까울수록 정밀도를 높이고(false positive 최소화), 0에 가까울수록 재현율을 높입니다(false negative 최소화).
- **AccuracyCostTradeoff**: 정확도-비용 균형을 조정합니다. 값이 1에 가까울수록 정확도를 높이지만 실행 시간이 길어집니다.
- **EnforceProvidedLabels**: true로 설정하면 사용자가 제공한 레이블이 최종 결과에 반드시 반영됩니다.

```bash
# ML Transform 목록 조회
aws glue get-ml-transforms \
  --filter '{"TransformType": "FIND_MATCHES"}' \
  --sort '{"Column": "CREATED", "SortDirection": "DESCENDING"}'
```

### 2. 레이블링(Labeling) 워크플로우

FindMatches는 지도 학습(Supervised Learning) 기반이므로, 모델 학습을 위한 레이블 데이터가 필요합니다.

```bash
# 레이블링 파일 생성 (레이블링할 레코드 쌍 추출)
aws glue start-export-labels-task-run \
  --transform-id "tfm-abc123def456" \
  --output-s3-path "s3://my-data-lake/labels/customer-dedup/export/"
```

내보내진 파일은 CSV 형식이며, 다음과 같은 구조를 가집니다.

```
labeling_set_id,customer_id,name,address,phone,label
ls_001,C001,김철수,서울 강남구 역삼동,010-1234-5678,
ls_001,C005,Kim Cheolsu,서울시 강남구 역삼동,01012345678,
ls_002,C002,박영희,부산 해운대구,010-9876-5432,
ls_002,C010,박영희,부산광역시 해운대구,010-9876-5432,
```

`labeling_set_id`가 같은 레코드들은 잠재적 매치 후보입니다. 사용자는 `label` 컬럼에 같은 값을 부여하여 "이 레코드들은 동일 엔터티다"라고 표시합니다.

```bash
# 레이블링된 파일 업로드
aws glue start-import-labels-task-run \
  --transform-id "tfm-abc123def456" \
  --input-s3-path "s3://my-data-lake/labels/customer-dedup/labeled/labels.csv" \
  --replace-all-labels
```

레이블링의 핵심 원칙은 다음과 같습니다.
- 최소 수백 개의 레이블 쌍이 필요합니다 (AWS는 최소 100개 권장).
- 매치와 비매치의 비율이 균형을 이루어야 합니다.
- 다양한 매칭 패턴을 포함해야 합니다 (이름 변형, 주소 약어, 전화번호 형식 등).
- 라운드를 반복하며 점진적으로 레이블을 추가할 수 있습니다.

### 3. 모델 학습과 평가

레이블 데이터가 준비되면 모델을 학습시킵니다.

```bash
# ML Transform 학습 실행
aws glue start-ml-evaluation-task-run \
  --transform-id "tfm-abc123def456"
```

```bash
# 학습 상태 확인
aws glue get-ml-transform \
  --transform-id "tfm-abc123def456" \
  --query '{
    Status: Status,
    LabelCount: LabelCount,
    EvaluationMetrics: EvaluationMetrics
  }'
```

평가 메트릭은 다음과 같은 정보를 제공합니다.

- **Precision**: 매치로 판정한 레코드 중 실제 매치인 비율
- **Recall**: 실제 매치 중 매치로 판정된 비율
- **F1 Score**: Precision과 Recall의 조화 평균
- **Area Under PR Curve**: 전체적인 모델 성능 지표
- **Confusion Matrix**: 정분류/오분류 행렬

```bash
# 상세 평가 결과 확인
aws glue get-ml-task-runs \
  --transform-id "tfm-abc123def456" \
  --filter '{"TaskRunType": "EVALUATION"}' \
  --sort '{"Column": "STARTED", "SortDirection": "DESCENDING"}'
```

### 4. Transform 실행

학습된 모델을 전체 데이터셋에 적용합니다.

```bash
# ML Transform 실행 (Glue Job으로)
aws glue start-ml-labeling-set-generation-task-run \
  --transform-id "tfm-abc123def456"
```

Glue ETL Job 내에서 FindMatches Transform을 사용하는 방법도 있습니다.

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'transform_id'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 소스 데이터 로드
customers_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="raw_db",
    table_name="customers",
    transformation_ctx="source"
)

# FindMatches Transform 적용
matched_dyf = FindMatches.apply(
    frame=customers_dyf,
    transformId=args['transform_id'],
    transformation_ctx="find_matches"
)

# 결과: 원본 컬럼 + match_id 컬럼이 추가됨
# 같은 match_id를 가진 레코드는 동일 엔터티
matched_dyf.toDF().show(20, truncate=False)

# 중복 제거: match_id 그룹 내에서 대표 레코드 선택
df = matched_dyf.toDF()
from pyspark.sql import Window
from pyspark.sql.functions import row_number, col

window = Window.partitionBy("match_id").orderBy("customer_id")
deduped_df = df.withColumn("rn", row_number().over(window)).filter(col("rn") == 1).drop("rn", "match_id")

print(f"원본 레코드 수: {df.count()}")
print(f"중복 제거 후: {deduped_df.count()}")

from awsglue.dynamicframe import DynamicFrame
result_dyf = DynamicFrame.fromDF(deduped_df, glueContext, "deduped")

glueContext.write_dynamic_frame.from_options(
    frame=result_dyf,
    connection_type="s3",
    connection_options={"path": "s3://my-data-lake/curated/customers_deduped/"},
    format="parquet",
    transformation_ctx="write_output"
)

job.commit()
```

```bash
# 위 잡 실행
aws glue start-job-run \
  --job-name "customer-dedup-job" \
  --arguments '{"--transform_id": "tfm-abc123def456"}'
```

### 5. 증분 매칭(Incremental Matching)

신규 데이터가 들어올 때마다 전체 데이터셋을 다시 매칭할 필요 없이, 기존 결과를 기반으로 신규 레코드만 매칭할 수 있습니다.

```python
# 증분 매칭: 기존 데이터 + 신규 데이터를 함께 로드
existing_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="curated_db",
    table_name="customers_with_match_id",
    transformation_ctx="existing"
)

new_dyf = glueContext.create_dynamic_frame.from_catalog(
    database="raw_db",
    table_name="new_customers",
    transformation_ctx="new_data"
)

# 기존 데이터와 신규 데이터를 합친 후 FindMatches 적용
from awsglue.dynamicframe import DynamicFrame

combined_df = existing_dyf.toDF().union(new_dyf.toDF())
combined_dyf = DynamicFrame.fromDF(combined_df, glueContext, "combined")

matched_dyf = FindMatches.apply(
    frame=combined_dyf,
    transformId=args['transform_id'],
    transformation_ctx="incremental_match"
)
```

## 아키텍처/동작 원리

### FindMatches 처리 파이프라인

```
[레이블링 단계]
(1) 레이블 파일 내보내기
         |
(2) 수동 레이블링 (같다/다르다)
         |
(3) 레이블 파일 가져오기
         |
(4) 모델 학습 (ML Training)
         |
(5) 평가 메트릭 확인
         |
    +--> 성능 불충분? --> (1)로 돌아가 추가 레이블링
         |
[실행 단계]
(6) 전체 데이터에 Transform 적용
         |
(7) match_id 컬럼이 추가된 결과
         |
(8) 후처리 (중복 제거, 병합 등)
```

### ML 모델의 내부 동작

FindMatches는 내부적으로 다음과 같은 단계로 동작합니다.

1. **블로킹(Blocking)**: 전체 레코드 쌍을 모두 비교하면 O(n^2)의 비용이 발생합니다. 블로킹 단계에서 유사할 가능성이 있는 레코드 쌍만 후보로 선별합니다.

2. **특성 추출(Feature Extraction)**: 각 레코드 쌍에 대해 유사도 특성을 추출합니다. 문자열 유사도(Jaro-Winkler, Levenshtein), 토큰 유사도, 음성 유사도(Soundex, Metaphone) 등을 계산합니다.

3. **분류(Classification)**: 추출된 특성을 기반으로 ML 모델이 각 레코드 쌍이 매치인지 비매치인지 판정합니다.

4. **클러스터링(Clustering)**: 매치로 판정된 레코드 쌍들을 그래프로 연결하고, 연결 컴포넌트를 찾아 동일 엔터티 그룹(match_id)을 할당합니다.

### PrecisionRecallTradeoff의 영향

이 파라미터는 결과의 특성을 크게 좌우합니다.

- **높은 값 (0.9~1.0)**: 정밀도 우선. "확실한 매치만 연결합니다." false positive가 적지만 일부 매치를 놓칠 수 있습니다. 금융, 의료 등 오매칭 비용이 큰 도메인에 적합합니다.
- **낮은 값 (0.0~0.3)**: 재현율 우선. "가능한 모든 매치를 찾습니다." 매치를 놓치는 경우가 적지만 잘못된 매칭이 발생할 수 있습니다. 마케팅 데이터 통합 등에 적합합니다.
- **중간 값 (0.4~0.6)**: 균형 잡힌 접근. 일반적인 중복 제거에 적합합니다.

## 실전 활용

### 사례 1: 고객 데이터 중복 제거

```bash
# 1단계: Transform 생성
aws glue create-ml-transform \
  --name "customer-master-dedup" \
  --input-record-tables '[{"DatabaseName": "crm_db", "TableName": "customers_raw"}]' \
  --parameters '{
    "TransformType": "FIND_MATCHES",
    "FindMatchesParameters": {
      "PrimaryKeyColumnName": "id",
      "PrecisionRecallTradeoff": 0.85,
      "AccuracyCostTradeoff": 0.7,
      "EnforceProvidedLabels": true
    }
  }' \
  --role "arn:aws:iam::123456789012:role/GlueServiceRole" \
  --glue-version "4.0" \
  --number-of-workers 10 \
  --worker-type "G.1X"
```

```bash
# 2단계: 레이블링 세트 생성
TRANSFORM_ID=$(aws glue get-ml-transforms \
  --filter '{"Name": "customer-master-dedup"}' \
  --query 'Transforms[0].TransformId' --output text)

aws glue start-ml-labeling-set-generation-task-run \
  --transform-id $TRANSFORM_ID

# 3단계: 레이블 내보내기
aws glue start-export-labels-task-run \
  --transform-id $TRANSFORM_ID \
  --output-s3-path "s3://my-data-lake/labels/customer-dedup/round1/"
```

```bash
# 레이블링 완료 후 가져오기 및 학습
aws glue start-import-labels-task-run \
  --transform-id $TRANSFORM_ID \
  --input-s3-path "s3://my-data-lake/labels/customer-dedup/round1/labeled.csv"

# 모델 학습
aws glue start-ml-evaluation-task-run \
  --transform-id $TRANSFORM_ID
```

### 사례 2: 제품 카탈로그 통합

여러 공급업체에서 들어오는 제품 데이터를 통합하는 시나리오입니다.

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql import functions as F
from pyspark.sql.window import Window

args = getResolvedOptions(sys.argv, ['JOB_NAME', 'transform_id'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 여러 공급업체의 제품 데이터 통합
supplier_a = glueContext.create_dynamic_frame.from_catalog(
    database="supply_db", table_name="products_supplier_a",
    transformation_ctx="supplier_a"
)
supplier_b = glueContext.create_dynamic_frame.from_catalog(
    database="supply_db", table_name="products_supplier_b",
    transformation_ctx="supplier_b"
)

# 스키마 통일 후 합치기
df_a = supplier_a.toDF().withColumn("source", F.lit("supplier_a"))
df_b = supplier_b.toDF().withColumn("source", F.lit("supplier_b"))
combined_df = df_a.unionByName(df_b, allowMissingColumns=True)

combined_dyf = DynamicFrame.fromDF(combined_df, glueContext, "combined")

# FindMatches 적용
matched_dyf = FindMatches.apply(
    frame=combined_dyf,
    transformId=args['transform_id'],
    transformation_ctx="product_matching"
)

# 매칭 그룹별 대표 제품 선택 (가장 완전한 레코드 우선)
matched_df = matched_dyf.toDF()

# 각 레코드의 완전성 점수 계산
columns_to_check = ["product_name", "description", "category", "brand", "price", "sku"]
completeness_expr = sum([F.when(F.col(c).isNotNull(), 1).otherwise(0) for c in columns_to_check])

scored_df = matched_df.withColumn("completeness_score", completeness_expr)

# match_id 그룹 내에서 가장 완전한 레코드 선택
window = Window.partitionBy("match_id").orderBy(F.desc("completeness_score"))
master_products = scored_df \
    .withColumn("rank", F.row_number().over(window)) \
    .filter(F.col("rank") == 1) \
    .drop("rank", "completeness_score", "match_id")

print(f"원본 제품 수: {combined_df.count()}")
print(f"통합 후 제품 수: {master_products.count()}")

result_dyf = DynamicFrame.fromDF(master_products, glueContext, "master_products")
glueContext.write_dynamic_frame.from_options(
    frame=result_dyf,
    connection_type="s3",
    connection_options={"path": "s3://my-data-lake/curated/products_master/"},
    format="parquet",
    transformation_ctx="write_master"
)

job.commit()
```

### 사례 3: 매칭 결과 분석 및 검증

```bash
# Transform 실행 이력 조회
aws glue get-ml-task-runs \
  --transform-id "tfm-abc123def456" \
  --filter '{"TaskRunType": "FIND_MATCHES"}' \
  --sort '{"Column": "STARTED", "SortDirection": "DESCENDING"}' \
  --max-results 5
```

```bash
# Transform 통계 확인
aws glue get-ml-transform \
  --transform-id "tfm-abc123def456" \
  --query '{
    Name: Name,
    Status: Status,
    LabelCount: LabelCount,
    CreatedOn: CreatedOn,
    EvaluationMetrics: EvaluationMetrics.FindMatchesMetrics.{
      Precision: Precision,
      Recall: Recall,
      F1: F1,
      AreaUnderPRCurve: AreaUnderPRCurve
    }
  }'
```

## 모범 사례/보안

### 레이블링 모범 사례

1. **충분한 레이블 확보**: 최소 100개 이상의 레이블 쌍을 제공합니다. 데이터 복잡도에 따라 500~1,000개가 필요할 수 있습니다.

2. **다양한 패턴 포함**: 다양한 유형의 매치와 비매치를 레이블에 포함합니다. 비슷하지만 다른 엔터티(hard negative)를 충분히 포함해야 모델 정확도가 높아집니다.

3. **반복적 개선**: 한 번에 완벽한 레이블을 만들려 하지 말고, 여러 라운드에 걸쳐 점진적으로 개선합니다.

4. **도메인 전문가 참여**: 레이블링은 데이터에 대한 도메인 지식이 필요한 작업이므로 해당 분야 전문가가 참여해야 합니다.

### 성능 최적화

1. **데이터 전처리**: FindMatches 적용 전에 기본적인 데이터 정규화(소문자 변환, 공백 제거, 전화번호 형식 통일 등)를 수행하면 매칭 정확도가 향상됩니다.

2. **적절한 PrecisionRecallTradeoff 설정**: 비즈니스 요구사항에 맞게 조정합니다. 오매칭 비용이 높으면 정밀도를 우선하고, 누락 비용이 높으면 재현율을 우선합니다.

3. **워커 수 조정**: 데이터 규모에 따라 워커 수를 조정합니다. 대규모 데이터셋에는 더 많은 워커가 필요합니다.

```bash
# Transform 설정 업데이트 (워커 수 증가)
aws glue update-ml-transform \
  --transform-id "tfm-abc123def456" \
  --number-of-workers 20 \
  --worker-type "G.2X"
```

### 보안 고려사항

1. **데이터 접근 제어**: FindMatches가 접근하는 데이터에 민감한 개인정보(PII)가 포함될 수 있으므로, IAM 역할의 권한을 최소화합니다.

2. **레이블 파일 보안**: 레이블 파일에는 실제 데이터 샘플이 포함되므로, S3 버킷의 접근 권한과 암호화 설정을 확인합니다.

3. **결과 데이터 관리**: 매칭 결과에서 match_id를 통해 개인 간 연결 관계가 노출될 수 있으므로, 결과 데이터의 접근 권한을 적절히 관리합니다.

```bash
# Transform에 태그 추가 (관리 및 비용 추적)
aws glue tag-resource \
  --resource-arn "arn:aws:glue:ap-northeast-2:123456789012:mlTransform/tfm-abc123def456" \
  --tags-to-add '{"Environment": "production", "DataClassification": "PII", "Team": "data-engineering"}'
```

## 관련 서비스 비교

| 항목 | AWS Glue FindMatches | AWS Entity Resolution | 오픈소스 (Dedupe/Splink) |
|------|---------------------|----------------------|-------------------------|
| 방식 | ML 기반 (지도학습) | 규칙 + ML | ML 기반 (다양) |
| 레이블링 | 필수 (수동) | 선택적 | 라이브러리에 따라 다름 |
| 관리 방식 | Glue 통합 | 독립 서비스 | 자체 관리 |
| 확장성 | Glue 워커 기반 | 서버리스 | 인프라에 의존 |
| Glue 파이프라인 통합 | 네이티브 | API 연동 | 커스텀 구현 |
| 비용 | DPU 시간 | 레코드당 과금 | 인프라 비용만 |
| 적합한 규모 | 중~대규모 | 대규모 | 소~중규모 |
| 실시간 처리 | 배치 | 배치/실시간 | 구현에 따라 다름 |

AWS Entity Resolution은 FindMatches의 후속 서비스적 성격이 강하며, 더 다양한 매칭 기법(규칙 기반, ML 기반, 프로바이더 서비스)을 제공합니다. 신규 프로젝트에서는 Entity Resolution도 함께 검토하는 것을 권장합니다.

## 요약

AWS Glue FindMatches는 ML 기반의 퍼지 매칭 서비스로, 정확히 일치하지 않는 중복 레코드를 탐지하고 동일 엔터티를 식별합니다. 사용자가 제공하는 레이블 데이터를 기반으로 지도 학습 모델을 훈련하며, PrecisionRecallTradeoff 파라미터로 정밀도-재현율 균형을 조정할 수 있습니다.

효과적인 활용을 위해서는 충분하고 다양한 레이블 데이터를 확보하고, 반복적으로 모델을 개선하는 것이 핵심입니다. 데이터 전처리를 통한 입력 품질 향상, 비즈니스 요구사항에 맞는 트레이드오프 설정, 그리고 결과에 대한 도메인 전문가의 검증이 성공적인 엔터티 해상도의 핵심 요소입니다.

Glue ETL Job 내에서 네이티브로 통합되어 전체 ETL 파이프라인의 일부로 자연스럽게 사용할 수 있으며, 증분 매칭을 통해 신규 데이터에 대한 효율적인 처리도 가능합니다.