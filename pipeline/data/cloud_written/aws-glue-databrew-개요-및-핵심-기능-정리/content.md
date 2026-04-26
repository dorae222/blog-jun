<!-- infographic-hero -->
![AWS Glue DataBrew 개요 및 핵심 기능 정리 핵심 요약](figures/infographic.svg)

*Figure: AWS Glue DataBrew 개요 및 핵심 기능 정리 한 장 요약 인포그래픽*

# AWS Glue DataBrew 개요 및 핵심 기능 정리

## 개요

AWS Glue DataBrew는 코드를 작성하지 않고도 데이터를 정리하고 정규화할 수 있는 시각적 데이터 준비(Data Preparation) 서비스입니다. 데이터 엔지니어, 데이터 분석가, 데이터 사이언티스트가 별도의 코딩 없이 250개 이상의 내장 변환(Transformation)을 활용하여 데이터 전처리 작업을 수행할 수 있습니다.

전통적으로 데이터 전처리는 전체 데이터 파이프라인 작업 시간의 60~80%를 차지한다고 알려져 있습니다. DataBrew는 이러한 반복적이고 시간 소모적인 작업을 시각적 인터페이스를 통해 대폭 단축시켜 줍니다. S3, Redshift, RDS, Glue Data Catalog 등 다양한 AWS 데이터 소스와 직접 연동되며, 프로젝트(Project)와 레시피(Recipe), 잡(Job) 단위로 전처리 워크플로우를 관리합니다.

DataBrew는 AWS Glue 생태계의 일부이지만, Glue ETL Job과는 별도의 서비스로 동작합니다. Glue ETL이 Apache Spark 기반의 코드 중심 ETL 도구라면, DataBrew는 비주얼 인터페이스 중심의 데이터 준비 도구라는 점에서 차이가 있습니다.

## 핵심 기능

### 1. 프로젝트(Project)와 데이터셋(Dataset)

DataBrew의 작업 단위는 프로젝트입니다. 프로젝트는 하나의 데이터셋과 연결되며, 해당 데이터셋에 대한 변환 작업을 정의하는 공간입니다.

데이터셋은 S3 버킷의 CSV, JSON, Parquet, ORC, Excel 등 다양한 형식의 파일을 지원합니다. Glue Data Catalog 테이블이나 JDBC 커넥터를 통한 데이터베이스 연결도 가능합니다.

```bash
# DataBrew 데이터셋 생성 (S3 소스)
aws databrew create-dataset \
  --name "sales-raw-dataset" \
  --format CSV \
  --format-options '{"Csv": {"Delimiter": ",", "HeaderRow": true}}' \
  --input '{"S3InputDefinition": {"Bucket": "my-data-lake", "Key": "raw/sales/"}}'
```

```bash
# 데이터셋 목록 조회
aws databrew list-datasets --max-results 10
```

### 2. 레시피(Recipe)와 변환(Transformation)

레시피는 데이터에 적용할 변환 단계들의 순서화된 집합입니다. DataBrew는 250개 이상의 내장 변환을 제공하며, 주요 카테고리는 다음과 같습니다.

- **형식 변환**: 날짜/시간 형식 변경, 문자열-숫자 변환, 대소문자 변환
- **정리(Cleaning)**: 결측값 처리, 중복 제거, 공백 제거, 특수문자 제거
- **구조 변환**: 컬럼 분할/병합, 피벗/언피벗, 중첩 JSON 평탄화
- **수학/통계**: 집계, 이동 평균, 정규화, 표준화
- **필터링**: 조건부 행 필터, 컬럼 선택/삭제
- **인코딩**: 원-핫 인코딩, 바이너리 인코딩, 해싱

```bash
# 레시피 생성
aws databrew create-recipe \
  --name "sales-cleaning-recipe" \
  --steps '[{"Action": {"Operation": "REMOVE_MISSING", "Parameters": {"sourceColumn": "price", "strategy": "DELETE_ROWS"}}}]'
```

```bash
# 레시피 퍼블리시 (버전 생성)
aws databrew publish-recipe \
  --name "sales-cleaning-recipe" \
  --description "v1.0 - 결측값 제거 및 형식 정규화"
```

레시피는 버전 관리가 가능합니다. 작업 중인 레시피를 퍼블리시하면 새로운 버전이 생성되며, 잡(Job)을 실행할 때 특정 버전의 레시피를 지정할 수 있습니다.

### 3. 프로파일링(Profiling)

DataBrew의 프로파일링 기능은 데이터셋의 통계적 특성을 자동으로 분석합니다. 프로파일 잡을 실행하면 다음과 같은 정보를 얻을 수 있습니다.

- 각 컬럼의 데이터 타입 분포
- 결측값 비율 및 패턴
- 유니크 값 수 및 최빈값
- 숫자 컬럼의 통계 요약(평균, 중앙값, 표준편차, 분위수)
- 문자열 컬럼의 길이 분포
- 상관관계 매트릭스
- 데이터 이상치(Outlier) 탐지

```bash
# 프로파일 잡 생성 및 실행
aws databrew create-profile-job \
  --name "sales-profile-job" \
  --dataset-name "sales-raw-dataset" \
  --role-arn "arn:aws:iam::123456789012:role/DataBrewRole" \
  --output-location '{"Bucket": "my-data-lake", "Key": "profiles/sales/"}' \
  --configuration '{"DatasetStatisticsConfiguration": {"IncludedStatistics": ["CORRELATION", "DUPLICATE_ROWS_COUNT"]}}'
```

```bash
# 프로파일 잡 실행
aws databrew start-job-run --name "sales-profile-job"
```

### 4. 데이터 품질 규칙(Data Quality Rules)

DataBrew는 데이터 품질을 검증하기 위한 규칙셋(Ruleset)을 정의할 수 있습니다. 프로파일 잡 실행 시 규칙셋을 함께 적용하면, 데이터가 정의된 품질 기준을 충족하는지 자동으로 검증합니다.

```bash
# 데이터 품질 규칙셋 생성
aws databrew create-ruleset \
  --name "sales-quality-rules" \
  --target-arn "arn:aws:databrew:ap-northeast-2:123456789012:dataset/sales-raw-dataset" \
  --rules '[{"Name": "price-not-null", "Disabled": false, "CheckExpression": "IS_NOT_NULL(:col)", "ColumnSelectors": [{"Name": "price"}], "Threshold": {"Value": 95, "Type": "GREATER_THAN_OR_EQUAL"}}]'
```

### 5. 스케줄링과 잡(Job) 관리

변환 작업을 실제 데이터에 적용하려면 레시피 잡(Recipe Job)을 생성합니다. 잡은 수동 실행 또는 스케줄 기반으로 실행할 수 있습니다.

```bash
# 레시피 잡 생성
aws databrew create-recipe-job \
  --name "sales-transform-job" \
  --dataset-name "sales-raw-dataset" \
  --recipe '{"Name": "sales-cleaning-recipe", "RecipeVersion": "1.0"}' \
  --role-arn "arn:aws:iam::123456789012:role/DataBrewRole" \
  --outputs '[{"Location": {"Bucket": "my-data-lake", "Key": "processed/sales/"}, "Format": "PARQUET", "Overwrite": true, "CompressionFormat": "SNAPPY"}]'
```

```bash
# 스케줄 생성 (매일 오전 6시 실행)
aws databrew create-schedule \
  --name "daily-sales-transform" \
  --cron-expression "cron(0 6 * * ? *)" \
  --job-names '["sales-transform-job"]'
```

## 아키텍처/동작 원리

### DataBrew 워크플로우 아키텍처

DataBrew의 전체 워크플로우는 다음과 같은 단계로 구성됩니다.

```
[데이터 소스]       [DataBrew 프로젝트]         [출력]
    |                    |                      |
 S3/RDS/Redshift  -->  Dataset 연결             |
    |                    |                      |
 Glue Data       -->  프로파일링 실행           |
 Catalog                |                      |
                    레시피 정의/편집            |
                        |                      |
                    레시피 퍼블리시             |
                        |                      |
                    레시피 잡 실행  -------->  S3 (Parquet/CSV)
                        |                      |
                    스케줄 연동               Redshift
                        |                      |
                    CloudWatch 모니터링       Glue Data Catalog
```

### 내부 동작 방식

DataBrew는 내부적으로 서버리스 아키텍처로 동작합니다. 프로젝트를 열면 DataBrew 세션이 시작되며, 데이터셋의 샘플을 로드하여 인터랙티브하게 변환을 미리보기할 수 있습니다. 이때 전체 데이터가 아닌 샘플 데이터(기본 500행)에 대해 변환을 적용하므로 빠른 피드백이 가능합니다.

잡을 실행하면 DataBrew는 내부적으로 분산 처리 엔진을 활용하여 전체 데이터셋에 레시피를 적용합니다. 잡의 처리 용량은 자동으로 스케일링되며, 노드 수를 직접 지정할 수도 있습니다(최대 149노드).

### IAM 권한 구성

DataBrew가 데이터 소스에 접근하려면 적절한 IAM 역할이 필요합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::my-data-lake",
        "arn:aws:s3:::my-data-lake/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetTable",
        "glue:GetTables",
        "glue:GetDatabase",
        "glue:GetDatabases"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws-glue-databrew/*"
    }
  ]
}
```

### 세션 관리와 비용 구조

DataBrew 세션은 프로젝트를 열 때 시작되며, 30분간 비활성 상태가 지속되면 자동으로 종료됩니다. 세션 비용은 30분 단위로 과금되며, 잡 실행 비용은 DataBrew 노드 시간 기준으로 과금됩니다.

## 실전 활용

### 사례 1: CSV 데이터 정리 파이프라인

매일 외부 시스템에서 S3로 업로드되는 CSV 파일을 자동으로 정리하는 파이프라인을 구축하는 예시입니다.

```bash
# 1단계: 데이터셋 생성
aws databrew create-dataset \
  --name "daily-orders" \
  --format CSV \
  --format-options '{"Csv": {"Delimiter": ",", "HeaderRow": true}}' \
  --input '{"S3InputDefinition": {"Bucket": "orders-bucket", "Key": "incoming/"}}' \
  --path-options '{"LastModifiedDateCondition": {"Expression": "val > :date", "ValuesMap": {":date": "2024-01-01T00:00:00Z"}}}'
```

```bash
# 2단계: 레시피 정의 (다단계 변환)
aws databrew create-recipe \
  --name "orders-cleaning" \
  --steps '[
    {"Action": {"Operation": "REMOVE_DUPLICATES", "Parameters": {"sourceColumns": "[\"order_id\"]"}}},
    {"Action": {"Operation": "REMOVE_MISSING", "Parameters": {"sourceColumn": "customer_id", "strategy": "DELETE_ROWS"}}},
    {"Action": {"Operation": "CHANGE_DATA_TYPE", "Parameters": {"sourceColumn": "order_date", "targetDateFormat": "yyyy-MM-dd", "targetDataType": "date"}}},
    {"Action": {"Operation": "UPPER_CASE", "Parameters": {"sourceColumn": "status"}}},
    {"Action": {"Operation": "DELETE_COLUMN", "Parameters": {"sourceColumn": "temp_notes"}}}
  ]'
```

```bash
# 3단계: 레시피 잡 생성 (Parquet 출력, Snappy 압축)
aws databrew create-recipe-job \
  --name "orders-daily-clean" \
  --dataset-name "daily-orders" \
  --recipe '{"Name": "orders-cleaning", "RecipeVersion": "LATEST_PUBLISHED"}' \
  --role-arn "arn:aws:iam::123456789012:role/DataBrewRole" \
  --outputs '[{"Location": {"Bucket": "orders-bucket", "Key": "cleaned/"}, "Format": "PARQUET", "CompressionFormat": "SNAPPY", "Overwrite": true, "PartitionColumns": ["order_date"]}]' \
  --max-capacity 5
```

```bash
# 4단계: 매일 새벽 2시 자동 실행 스케줄
aws databrew create-schedule \
  --name "daily-orders-schedule" \
  --cron-expression "cron(0 2 * * ? *)" \
  --job-names '["orders-daily-clean"]'
```

### 사례 2: 데이터 프로파일링을 통한 품질 모니터링

```bash
# 프로파일 잡 생성 (상세 통계 포함)
aws databrew create-profile-job \
  --name "orders-quality-check" \
  --dataset-name "daily-orders" \
  --role-arn "arn:aws:iam::123456789012:role/DataBrewRole" \
  --output-location '{"Bucket": "orders-bucket", "Key": "quality-reports/"}' \
  --configuration '{
    "DatasetStatisticsConfiguration": {
      "IncludedStatistics": ["CORRELATION", "DUPLICATE_ROWS_COUNT", "OUTLIER_DETECTION"]
    },
    "ProfileColumns": [
      {"Regex": ".*"}
    ],
    "ColumnStatisticsConfigurations": [
      {
        "Selectors": [{"Name": "price"}],
        "Statistics": {
          "IncludedStatistics": ["MEAN", "STANDARD_DEVIATION", "MINIMUM", "MAXIMUM"]
        }
      }
    ]
  }'
```

### 사례 3: 다중 출력 형식 지원

DataBrew 잡은 하나의 실행으로 여러 형식의 출력을 동시에 생성할 수 있습니다.

```bash
# 다중 출력 잡 (Parquet + CSV 동시 출력)
aws databrew create-recipe-job \
  --name "multi-output-job" \
  --dataset-name "daily-orders" \
  --recipe '{"Name": "orders-cleaning", "RecipeVersion": "1.0"}' \
  --role-arn "arn:aws:iam::123456789012:role/DataBrewRole" \
  --outputs '[
    {"Location": {"Bucket": "analytics-bucket", "Key": "parquet/"}, "Format": "PARQUET", "CompressionFormat": "SNAPPY"},
    {"Location": {"Bucket": "reports-bucket", "Key": "csv/"}, "Format": "CSV", "Overwrite": true}
  ]'
```

### 사례 4: EventBridge와 연동한 이벤트 드리븐 파이프라인

S3에 새 파일이 업로드되면 자동으로 DataBrew 잡을 트리거하는 구성도 가능합니다. EventBridge 규칙과 Lambda를 조합하여 구현합니다.

```python
import boto3
import json

def lambda_handler(event, context):
    """S3 이벤트로 트리거되어 DataBrew 잡을 시작하는 Lambda 함수"""
    databrew = boto3.client('databrew')
    
    # S3 이벤트에서 파일 정보 추출
    bucket = event['detail']['bucket']['name']
    key = event['detail']['object']['key']
    
    print(f"새 파일 감지: s3://{bucket}/{key}")
    
    # DataBrew 잡 실행
    response = databrew.start_job_run(
        Name='orders-daily-clean'
    )
    
    run_id = response['RunId']
    print(f"DataBrew 잡 실행 시작: RunId={run_id}")
    
    return {
        'statusCode': 200,
        'body': json.dumps({'runId': run_id})
    }
```

## 모범 사례/보안

### 보안 모범 사례

1. **최소 권한 원칙 적용**: DataBrew 역할에는 필요한 S3 버킷과 Glue Data Catalog 리소스에 대한 권한만 부여합니다. 와일드카드(`*`) 사용을 최소화합니다.

2. **데이터 암호화**: S3 출력에 SSE-S3 또는 SSE-KMS 암호화를 적용합니다.

```bash
# KMS 암호화 적용 출력 설정
aws databrew create-recipe-job \
  --name "encrypted-output-job" \
  --dataset-name "sensitive-data" \
  --recipe '{"Name": "pii-masking-recipe", "RecipeVersion": "1.0"}' \
  --role-arn "arn:aws:iam::123456789012:role/DataBrewRole" \
  --outputs '[{"Location": {"Bucket": "secure-bucket", "Key": "output/"}, "Format": "PARQUET", "Overwrite": true}]' \
  --encryption-key-arn "arn:aws:kms:ap-northeast-2:123456789012:key/my-key-id" \
  --encryption-mode "SSE-KMS"
```

3. **VPC 엔드포인트 활용**: 민감한 데이터를 처리할 때는 VPC 엔드포인트를 통해 S3와 통신하도록 설정하여 데이터가 인터넷을 경유하지 않도록 합니다.

4. **CloudTrail 로깅**: DataBrew API 호출을 CloudTrail로 기록하여 감사 추적(Audit Trail)을 유지합니다.

### 운영 모범 사례

1. **레시피 버전 관리**: 레시피를 변경할 때마다 퍼블리시하여 버전을 관리합니다. 프로덕션 잡에는 항상 특정 버전을 지정하고, `LATEST_PUBLISHED`는 개발/테스트 환경에서만 사용합니다.

2. **적절한 노드 수 설정**: `--max-capacity` 옵션으로 잡의 최대 노드 수를 제한하여 비용을 통제합니다. 데이터 크기에 따라 5~20노드가 일반적입니다.

3. **파티셔닝 출력**: 대용량 데이터는 날짜나 카테고리 기준으로 파티셔닝하여 출력하면 후속 쿼리 성능이 향상됩니다.

4. **프로파일링 우선 실행**: 새로운 데이터셋에 대해 먼저 프로파일 잡을 실행하여 데이터 특성을 파악한 후 레시피를 설계합니다.

5. **태그 기반 리소스 관리**: 모든 DataBrew 리소스에 태그를 부여하여 비용 추적과 접근 제어를 체계화합니다.

```bash
# 리소스에 태그 추가
aws databrew tag-resource \
  --resource-arn "arn:aws:databrew:ap-northeast-2:123456789012:job/orders-daily-clean" \
  --tags '{"Environment": "production", "Team": "data-engineering", "CostCenter": "DE-001"}'
```

### 비용 최적화

- 인터랙티브 세션은 사용하지 않을 때 즉시 종료합니다 (30분 자동 종료 대기하지 않기).
- 프로파일 잡에서 불필요한 통계 항목은 제외하여 실행 시간을 단축합니다.
- 대용량 데이터는 샘플링 옵션을 활용하여 프로파일링합니다.

## 관련 서비스 비교

| 항목 | AWS Glue DataBrew | AWS Glue ETL | Amazon SageMaker Data Wrangler |
|------|-------------------|--------------|-------------------------------|
| 대상 사용자 | 분석가, 비개발자 | 데이터 엔지니어 | 데이터 사이언티스트 |
| 인터페이스 | 시각적 UI | 코드(PySpark/Scala) | 시각적 UI + 노트북 |
| 변환 방식 | 250+ 내장 변환 | 커스텀 코드 | ML 특화 변환 |
| 실행 엔진 | DataBrew 자체 엔진 | Apache Spark | SageMaker Processing |
| ML 통합 | 제한적 | 가능 | 네이티브 통합 |
| 비용 모델 | 세션 + 노드 시간 | DPU 시간 | 인스턴스 시간 |
| 스케줄링 | 내장 스케줄러 | Glue Trigger/Workflow | SageMaker Pipeline |
| 데이터 프로파일링 | 내장 지원 | 별도 구현 필요 | 내장 지원 |
| 코드 내보내기 | 제한적 | 해당 없음 | Python/PySpark 내보내기 가능 |

**DataBrew를 선택해야 하는 경우:**
- 코딩 없이 빠르게 데이터 정리 작업을 수행해야 할 때
- 반복적인 데이터 전처리 작업을 자동화해야 할 때
- 데이터 품질 프로파일링이 주요 요구사항일 때
- 비개발 인력이 데이터 준비 작업에 참여해야 할 때

**Glue ETL을 선택해야 하는 경우:**
- 복잡한 비즈니스 로직이 포함된 변환이 필요할 때
- 여러 데이터 소스를 조인하는 복잡한 ETL이 필요할 때
- Spark의 분산 처리 성능이 필요한 대규모 데이터일 때

**SageMaker Data Wrangler를 선택해야 하는 경우:**
- ML 모델 학습을 위한 피처 엔지니어링이 목적일 때
- SageMaker 파이프라인과 통합이 필요할 때

## 요약

AWS Glue DataBrew는 코드 없이 시각적 인터페이스로 데이터 전처리를 수행할 수 있는 서버리스 데이터 준비 서비스입니다. 250개 이상의 내장 변환, 자동 데이터 프로파일링, 레시피 버전 관리, 스케줄 기반 자동화 등의 핵심 기능을 제공합니다.

DataBrew는 특히 반복적인 데이터 정리 작업을 비개발 인력도 수행할 수 있게 해주며, S3, Glue Data Catalog, Redshift 등 AWS 데이터 생태계와 긴밀하게 통합됩니다. 보안 측면에서는 IAM 역할 기반 접근 제어, KMS 암호화, VPC 엔드포인트를 통한 네트워크 격리를 지원합니다.

운영 시에는 레시피 버전 관리를 철저히 하고, 프로파일링을 먼저 실행하여 데이터를 이해한 후 변환을 설계하며, 태그 기반 리소스 관리와 적절한 노드 수 설정으로 비용을 최적화하는 것이 중요합니다. Glue ETL이나 SageMaker Data Wrangler와의 역할 분담을 명확히 하여 각 도구의 강점을 최대한 활용하는 것을 권장합니다.