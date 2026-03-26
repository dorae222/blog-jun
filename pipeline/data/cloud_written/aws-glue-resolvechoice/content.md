# AWS Glue ResolveChoice

## 개요

AWS Glue ResolveChoice는 Glue ETL 작업에서 데이터 타입이 모호하거나 여러 타입으로 추론된 컬럼을 명확하게 처리하기 위한 DynamicFrame 전용 변환(Transform)입니다. AWS Glue는 반정형 데이터를 처리할 때 유연한 스키마 추론 기능을 제공하는데, 이 과정에서 동일한 컬럼이 서로 다른 데이터 파일에서 서로 다른 타입으로 존재하는 경우가 발생합니다.

예를 들어, JSON 파일 A에서는 `age` 필드가 정수(25)로 존재하고, JSON 파일 B에서는 문자열("twenty-five")로 존재할 수 있습니다. Glue의 DynamicFrame은 이런 상황에서 해당 컬럼을 `choice` 타입으로 추론합니다.

```text
age: choice<int, string>
```

이 choice 타입 상태로는 Parquet 파일로 저장하거나, Redshift에 적재하거나, Spark DataFrame으로 변환하는 것이 불가능합니다. 따라서 ResolveChoice를 통해 타입을 명확히 해결해야 합니다. 이는 실무 ETL 파이프라인에서 데이터 품질을 보장하는 핵심 단계입니다.

## 핵심 기능

### 네 가지 해결 전략

ResolveChoice는 choice 타입을 해결하기 위해 네 가지 전략을 제공합니다.

#### 1. make_cols (컬럼 분리)

각 타입을 별도의 컬럼으로 분리합니다. 원본 데이터를 최대한 보존해야 하는 경우에 유용합니다.

```python
from awsglue.transforms import ResolveChoice

# age: choice<int, string> --> age_int, age_string 두 컬럼으로 분리
resolved = ResolveChoice.apply(
    frame=dynamic_frame,
    choice="make_cols",
    transformation_ctx="resolve_make_cols"
)
```

변환 전후 스키마 비교:

```text
[변환 전]
root
|-- name: string
|-- age: choice
|   |-- int
|   |-- string

[변환 후]
root
|-- name: string
|-- age_int: int
|-- age_string: string
```

#### 2. cast (강제 타입 변환)

모든 값을 지정한 하나의 타입으로 강제 변환합니다. 변환이 불가능한 값은 null이 됩니다.

```python
# 모든 choice 타입 컬럼을 string으로 강제 변환
resolved = ResolveChoice.apply(
    frame=dynamic_frame,
    choice="cast:string",
    transformation_ctx="resolve_cast"
)

# 또는 double로 변환 (숫자 데이터의 경우)
resolved = ResolveChoice.apply(
    frame=dynamic_frame,
    choice="cast:double",
    transformation_ctx="resolve_cast_double"
)
```

#### 3. make_struct (구조체로 변환)

여러 타입의 값을 struct 형태로 묶습니다. 모든 타입의 값을 보존하면서도 하나의 컬럼으로 유지할 수 있습니다.

```python
# choice 타입을 struct로 변환
resolved = ResolveChoice.apply(
    frame=dynamic_frame,
    choice="make_struct",
    transformation_ctx="resolve_struct"
)
```

변환 후 스키마:

```text
root
|-- name: string
|-- age: struct
|   |-- int: int
|   |-- string: string
```

#### 4. project (단일 타입 선택)

여러 타입 중 하나만 선택하고 나머지를 제거합니다. 데이터 정합성이 확실한 경우에 사용합니다.

```python
# int 타입 값만 유지, string 값은 null 처리
resolved = ResolveChoice.apply(
    frame=dynamic_frame,
    choice="project:int",
    transformation_ctx="resolve_project"
)
```

### 컬럼별 개별 지정 (specs 파라미터)

여러 컬럼에 서로 다른 해결 전략을 적용할 수 있습니다. 실무에서 가장 많이 사용되는 패턴입니다.

```python
resolved = ResolveChoice.apply(
    frame=dynamic_frame,
    specs=[
        ("age", "cast:int"),
        ("salary", "cast:double"),
        ("address", "make_cols"),
        ("metadata", "make_struct")
    ],
    transformation_ctx="resolve_specs"
)
```

## 아키텍처/동작 원리

ResolveChoice의 동작 원리를 ETL 파이프라인 전체 흐름 속에서 이해하면 다음과 같습니다.

```text
[S3 소스 데이터]
 JSON 파일들 (스키마 불일치 존재)
          |
          v
[DynamicFrame 생성]
 Glue가 스키마 자동 추론
 choice 타입 발생 가능
          |
          v
[ResolveChoice 적용]  <-- 핵심 단계
 choice 타입을 단일 타입으로 해결
          |
          v
[추가 변환 작업]
 ApplyMapping, Filter, Join 등
          |
          v
[타겟에 저장]
 Parquet/Redshift/RDS 등
 (정확한 스키마 필요)
```

### DynamicFrame과 choice 타입

Glue의 DynamicFrame은 Spark의 DataFrame과 달리 레코드 단위로 스키마를 관리합니다. 이로 인해 서로 다른 레코드가 같은 필드에 다른 타입의 값을 가질 수 있으며, 이를 `choice` 타입으로 표현합니다.

DynamicFrame의 이 유연성은 JSON, CSV 등 반정형 데이터를 처리할 때 큰 장점이지만, 최종적으로 정형화된 포맷(Parquet, Redshift 등)에 저장하려면 ResolveChoice를 통해 타입을 명확히 해결해야 합니다.

### ResolveChoice가 필요한 이유

choice 타입이 남아있는 상태에서 다음 작업을 수행하면 오류가 발생합니다.

- **Parquet 저장**: Parquet은 컬럼 기반의 정확한 스키마를 요구합니다.
- **Redshift 적재**: Redshift 테이블은 각 컬럼에 하나의 데이터 타입만 허용합니다.
- **DataFrame 변환**: `toDF()` 호출 시 choice 타입 변환 오류가 발생합니다.
- **집계/연산**: SUM, AVG 등 수치 연산이 불가능합니다.

## 실전 활용

### Glue Job에서 ResolveChoice 적용 (전체 스크립트)

```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# 1. 데이터 읽기
datasource = glueContext.create_dynamic_frame.from_catalog(
    database="my_catalog_db",
    table_name="raw_events",
    transformation_ctx="datasource"
)

# 2. 스키마 확인 (choice 타입 존재 여부 확인)
print("원본 스키마:")
datasource.printSchema()

# 3. ResolveChoice 적용 - 컬럼별 전략 지정
resolved = ResolveChoice.apply(
    frame=datasource,
    specs=[
        ("age", "cast:int"),
        ("price", "cast:double"),
        ("quantity", "cast:long"),
        ("description", "cast:string")
    ],
    transformation_ctx="resolved"
)

# 4. 나머지 choice 타입이 있으면 일괄 처리
resolved_all = ResolveChoice.apply(
    frame=resolved,
    choice="make_struct",
    transformation_ctx="resolved_all"
)

# 5. null 필드 정리
cleaned = DropNullFields.apply(
    frame=resolved_all,
    transformation_ctx="cleaned"
)

print("변환 후 스키마:")
cleaned.printSchema()

# 6. Parquet으로 저장
glueContext.write_dynamic_frame.from_options(
    frame=cleaned,
    connection_type="s3",
    connection_options={
        "path": "s3://my-data-lake/processed/events/"
    },
    format="parquet",
    transformation_ctx="output"
)

job.commit()
```

### AWS CLI로 Glue Job 관리

```bash
# ResolveChoice를 사용하는 ETL Job 생성
aws glue create-job \
  --name "resolve-choice-etl" \
  --role "arn:aws:iam::123456789012:role/GlueETLRole" \
  --command '{
    "Name": "glueetl",
    "ScriptLocation": "s3://my-scripts/resolve_choice_etl.py",
    "PythonVersion": "3"
  }' \
  --glue-version "4.0" \
  --number-of-workers 5 \
  --worker-type "G.1X" \
  --default-arguments '{
    "--job-bookmark-option": "job-bookmark-enable",
    "--TempDir": "s3://my-temp/temp/",
    "--enable-metrics": "true"
  }'
```

```bash
# Data Catalog에서 테이블 스키마 확인 (choice 타입 포함 여부)
aws glue get-table \
  --database-name "my_catalog_db" \
  --name "raw_events" \
  --query 'Table.StorageDescriptor.Columns[*].{Name:Name,Type:Type}' \
  --output table
```

```bash
# Crawler를 실행하여 스키마 재탐색
aws glue start-crawler --name "raw-events-crawler"
```

### 스키마 진단 유틸리티

```python
def diagnose_choice_types(dynamic_frame):
    """DynamicFrame에서 choice 타입 컬럼을 진단합니다."""
    schema = dynamic_frame.schema()
    choice_columns = []

    for field in schema:
        type_str = str(field.dataType)
        if "choice" in type_str.lower():
            choice_columns.append({
                "column": field.name,
                "types": type_str
            })

    if choice_columns:
        print(f"choice 타입이 발견된 컬럼 수: {len(choice_columns)}")
        for col in choice_columns:
            print(f"  - {col['column']}: {col['types']}")
    else:
        print("choice 타입 컬럼이 없습니다.")

    return choice_columns
```

## 모범 사례 및 보안

### 전략 선택 가이드라인

| 상황 | 권장 전략 | 이유 |
|------|----------|------|
| 데이터 손실 없이 모든 값 보존 | make_cols | 각 타입의 값을 별도 컬럼으로 분리하여 보존 |
| 타입이 명확하고 변환이 안전한 경우 | cast | 간결하고 결과 스키마가 깔끔함 |
| 복잡한 중첩 구조를 유지해야 하는 경우 | make_struct | struct 내부에 모든 타입 값 유지 |
| 하나의 타입만 필요하고 나머지는 무시 가능 | project | 불필요한 타입 제거로 스키마 단순화 |

### 운영 모범 사례

- **ETL 초기에 ResolveChoice 적용**: 데이터를 읽은 직후, 다른 변환 전에 ResolveChoice를 수행합니다. 이렇게 하면 후속 변환에서 타입 관련 오류를 예방할 수 있습니다.
- **specs 파라미터 우선 사용**: 전체 일괄 적용(choice 파라미터)보다 컬럼별 지정(specs 파라미터)이 더 정밀한 제어를 제공합니다.
- **스키마 모니터링**: Crawler를 정기적으로 실행하여 소스 데이터의 스키마 변화를 추적하고, 새로운 choice 타입 발생 여부를 모니터링합니다.
- **테스트 데이터로 검증**: 프로덕션 적용 전에 소규모 샘플 데이터로 ResolveChoice 결과를 검증합니다.

### 보안 고려사항

- **Data Catalog 접근 제어**: IAM 정책을 통해 Data Catalog의 테이블 정의 수정 권한을 제한합니다.
- **민감 데이터 처리**: cast 전략 사용 시 변환 불가능한 값이 null로 처리되므로, 민감 데이터의 예기치 않은 손실에 주의합니다.
- **감사 로그**: CloudWatch Logs에서 ResolveChoice 전후의 레코드 수를 비교하여 데이터 손실 여부를 확인합니다.

## 관련 서비스 비교

| 항목 | ResolveChoice (DynamicFrame) | DataFrame cast (Spark) | Athena CAST | Redshift CAST |
|------|---------------------------|----------------------|-------------|---------------|
| 대상 | Glue DynamicFrame | Spark DataFrame | Athena 쿼리 | Redshift 쿼리 |
| choice 타입 처리 | 지원 | 미지원 | 미지원 | 미지원 |
| null 허용 유연성 | 높음 | 엄격(오류 발생 가능) | 중간 | 중간 |
| Glue 특화 기능 | 지원 | 미지원 | 해당 없음 | 해당 없음 |
| 컬럼별 전략 지정 | specs로 가능 | withColumn별 개별 처리 | 쿼리별 지정 | 쿼리별 지정 |
| 사용 단계 | ETL 변환 중 | ETL 변환 중 | 쿼리 실행 시 | 쿼리 실행 시 |

DynamicFrame 단계에서는 ResolveChoice를 사용하고, `toDF()`로 DataFrame 변환 후에는 Spark의 `cast()` 함수를 사용하는 것이 일반적인 패턴입니다.

## 요약

AWS Glue ResolveChoice는 DynamicFrame에서 발생하는 choice 타입(다중 데이터 타입 컬럼)을 해결하는 필수 변환입니다. make_cols(컬럼 분리), cast(강제 변환), make_struct(구조체 변환), project(단일 타입 선택)의 네 가지 전략을 제공하며, specs 파라미터를 통해 컬럼별로 서로 다른 전략을 적용할 수 있습니다. Parquet, Redshift 등 정형 타겟에 데이터를 적재하기 전에 반드시 수행해야 하는 단계이며, ETL 파이프라인의 데이터 품질을 보장하는 핵심 역할을 합니다.