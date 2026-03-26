# AWS Glue Classifier 개요

## 개요

AWS Glue Classifier는 Crawler가 데이터 소스를 스캔할 때 데이터의 스키마와 형식을 판별하는 규칙 세트입니다. Classifier는 Crawler의 핵심 구성 요소로, 데이터의 구조를 올바르게 인식하여 Data Catalog에 정확한 메타데이터를 등록하는 역할을 합니다.

Glue에는 CSV, JSON, Avro, Parquet, ORC 등 일반적인 데이터 형식을 인식하는 내장 Classifier가 포함되어 있습니다. 그러나 비표준 형식의 데이터나 특수한 구조의 데이터를 처리해야 하는 경우, 커스텀 Classifier를 생성하여 Crawler가 데이터를 올바르게 인식하도록 할 수 있습니다.

Classifier의 주요 역할은 다음과 같습니다.

- **데이터 형식 판별**: 데이터가 CSV인지, JSON인지, XML인지 등의 형식을 판별합니다.
- **스키마 추출**: 데이터의 열 이름, 데이터 타입, 중첩 구조 등을 추출합니다.
- **데이터 분류**: 데이터를 적절한 테이블로 분류하여 Data Catalog에 등록합니다.
- **Serde 결정**: 데이터를 읽고 쓸 때 사용할 직렬화/역직렬화(SerDe) 라이브러리를 결정합니다.

## 핵심 기능

### 1. 내장 Classifier

Glue는 다양한 데이터 형식에 대한 내장 Classifier를 제공합니다. Crawler가 실행되면 내장 Classifier가 순서대로 데이터를 평가하여, 데이터 형식과 스키마를 자동으로 판별합니다.

#### 지원하는 내장 분류

- **구조화된 형식**: Apache Avro, Apache ORC, Apache Parquet, JSON, BSON, XML
- **텍스트 형식**: CSV, TSV
- **이진 형식**: Ion, Combined Apache Log, Apache Log
- **데이터베이스**: JDBC를 통한 데이터베이스 테이블

```bash
# 커스텀 Classifier 목록 조회
aws glue get-classifiers \
  --query 'Classifiers[].{Name:GrokClassifier.Name||JsonClassifier.Name||CsvClassifier.Name||XMLClassifier.Name,Type:GrokClassifier&&`Grok`||JsonClassifier&&`JSON`||CsvClassifier&&`CSV`||XMLClassifier&&`XML`}' \
  --output table
```

#### 내장 Classifier의 평가 순서

Crawler가 데이터를 스캔할 때, 다음 순서로 Classifier가 평가됩니다.

1. **커스텀 Classifier**: 사용자가 정의한 Classifier가 먼저 평가됩니다. Crawler에 지정된 순서대로 평가합니다.
2. **내장 Classifier**: 커스텀 Classifier가 데이터를 인식하지 못하면 내장 Classifier가 순서대로 평가됩니다.

각 Classifier는 데이터 샘플을 분석하여 "확신도(Certainty)"를 반환합니다. 확신도가 1.0(100%)인 Classifier가 발견되면 해당 Classifier가 선택됩니다.

### 2. Grok Classifier (커스텀)

Grok Classifier는 정규 표현식 기반의 패턴 매칭을 사용하여 비정형 텍스트 데이터의 스키마를 추출합니다. 로그 파일 분석에 특히 유용합니다.

```bash
# Grok Classifier 생성 (Apache 로그 형식)
aws glue create-classifier \
  --grok-classifier '{
    "Classification": "apache-access-log",
    "Name": "apache-log-classifier",
    "GrokPattern": "%{COMBINEDAPACHELOG}"
  }'

# 커스텀 Grok 패턴이 포함된 Classifier
aws glue create-classifier \
  --grok-classifier '{
    "Classification": "custom-app-log",
    "Name": "app-log-classifier",
    "GrokPattern": "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} \\[%{DATA:thread}\\] %{JAVACLASS:class} - %{GREEDYDATA:message}",
    "CustomPatterns": "LOGLEVEL (TRACE|DEBUG|INFO|WARN|ERROR|FATAL)"
  }'
```

#### 주요 Grok 패턴

| 패턴 | 설명 | 예시 |
|------|------|------|
| %{IP:client_ip} | IP 주소 | 192.168.1.1 |
| %{TIMESTAMP_ISO8601:ts} | ISO 8601 타임스탬프 | 2024-01-15T10:30:00 |
| %{NUMBER:status:int} | 숫자 (정수 변환) | 200 |
| %{WORD:method} | 단일 단어 | GET |
| %{GREEDYDATA:msg} | 나머지 전체 문자열 | Any text here |
| %{COMBINEDAPACHELOG} | Apache Combined 로그 전체 | 전체 로그 라인 |
| %{JAVACLASS:class} | Java 클래스명 | com.example.MyClass |

### 3. JSON Classifier (커스텀)

JSON Classifier는 JSON 데이터에서 스키마를 추출하기 위한 JSONPath 표현식을 정의합니다. 중첩된 JSON 구조에서 특정 경로의 데이터를 테이블의 행으로 매핑할 수 있습니다.

```bash
# JSON Classifier 생성
aws glue create-classifier \
  --json-classifier '{
    "Name": "nested-events-classifier",
    "JsonPath": "$.events[*]"
  }'

# 깊이 중첩된 JSON 구조용 Classifier
aws glue create-classifier \
  --json-classifier '{
    "Name": "api-response-classifier",
    "JsonPath": "$.data.results[*]"
  }'
```

#### JSON Classifier 동작 원리

JSON Classifier가 지정한 JSONPath에 해당하는 각 요소가 테이블의 하나의 행으로 매핑됩니다.

예를 들어, 다음과 같은 JSON 데이터가 있을 때:

```json
{
  "events": [
    {"id": 1, "type": "click", "timestamp": "2024-01-15T10:00:00Z"},
    {"id": 2, "type": "purchase", "timestamp": "2024-01-15T10:05:00Z"}
  ],
  "metadata": {
    "source": "web"
  }
}
```

JSONPath `$.events[*]`를 사용하면, 각 이벤트 객체가 하나의 행으로 변환되어 `id`, `type`, `timestamp` 열이 생성됩니다.

### 4. CSV Classifier (커스텀)

CSV Classifier는 CSV 데이터의 구분자, 따옴표 문자, 헤더 존재 여부 등을 지정합니다.

```bash
# 커스텀 CSV Classifier 생성
aws glue create-classifier \
  --csv-classifier '{
    "Name": "pipe-delimited-classifier",
    "Delimiter": "|",
    "QuoteSymbol": "\"",
    "ContainsHeader": "PRESENT",
    "Header": ["id", "name", "email", "created_at", "amount"],
    "DisableValueTrimming": false,
    "AllowSingleColumn": false
  }'

# 탭 구분 파일용 Classifier
aws glue create-classifier \
  --csv-classifier '{
    "Name": "tsv-classifier",
    "Delimiter": "\t",
    "QuoteSymbol": "\"",
    "ContainsHeader": "PRESENT",
    "DisableValueTrimming": false
  }'
```

#### ContainsHeader 옵션

| 값 | 설명 |
|---|------|
| PRESENT | 첫 번째 행을 헤더로 사용합니다. |
| ABSENT | 헤더가 없으며, Header 배열에서 열 이름을 지정합니다. |
| UNKNOWN | Classifier가 자동으로 판별합니다. |

### 5. XML Classifier (커스텀)

XML Classifier는 XML 데이터에서 행으로 사용할 태그를 지정합니다.

```bash
# XML Classifier 생성
aws glue create-classifier \
  --xml-classifier '{
    "Name": "order-xml-classifier",
    "Classification": "orders",
    "RowTag": "order"
  }'
```

예를 들어, 다음과 같은 XML 데이터에서 `RowTag`를 `order`로 지정하면:

```xml
<orders>
  <order>
    <id>1001</id>
    <product>Widget A</product>
    <amount>29.99</amount>
  </order>
  <order>
    <id>1002</id>
    <product>Widget B</product>
    <amount>49.99</amount>
  </order>
</orders>
```

각 `<order>` 요소가 하나의 행으로 변환되어 `id`, `product`, `amount` 열이 생성됩니다.

### 6. Classifier 관리

```bash
# 특정 Classifier 상세 조회
aws glue get-classifier \
  --name "apache-log-classifier"

# Classifier 업데이트 (Grok)
aws glue update-classifier \
  --grok-classifier '{
    "Name": "app-log-classifier",
    "GrokPattern": "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} \\[%{DATA:thread}\\] %{JAVACLASS:class} - %{GREEDYDATA:message}",
    "CustomPatterns": "LOGLEVEL (TRACE|DEBUG|INFO|WARN|ERROR|FATAL|UNKNOWN)"
  }'

# Classifier 삭제
aws glue delete-classifier \
  --name "old-classifier"
```

## 아키텍처/동작 원리

### Classifier 평가 프로세스

Crawler가 데이터 소스를 스캔할 때 Classifier의 평가는 다음과 같은 프로세스로 진행됩니다.

```
[데이터 소스] --> [데이터 샘플링] --> [Classifier 평가]
                                       |
                              [커스텀 Classifier 1] --> 확신도 0.8 (불합격)
                              [커스텀 Classifier 2] --> 확신도 1.0 (합격!) --> [스키마 추출]
                              [내장 JSON Classifier] --> (평가 안 됨)
                              [내장 CSV Classifier]  --> (평가 안 됨)
                                                                              |
                                                                         [Data Catalog 등록]
```

#### 상세 동작 순서

1. **데이터 샘플링**: Crawler가 데이터 소스에서 샘플 데이터를 읽습니다. S3의 경우 파일의 첫 부분을 읽습니다.

2. **커스텀 Classifier 평가**: Crawler에 지정된 커스텀 Classifier가 순서대로 평가됩니다. 각 Classifier는 데이터 샘플을 분석하여 확신도를 계산합니다.

3. **내장 Classifier 평가**: 커스텀 Classifier가 데이터를 인식하지 못하면, 내장 Classifier가 순서대로 평가됩니다.

4. **스키마 추출**: 선택된 Classifier가 데이터의 스키마(열 이름, 데이터 타입 등)를 추출합니다.

5. **Data Catalog 등록**: 추출된 스키마와 메타데이터가 Data Catalog에 테이블로 등록됩니다.

### 확신도 (Certainty) 계산

Classifier의 확신도는 0.0에서 1.0 사이의 값으로, 데이터가 해당 형식에 얼마나 잘 맞는지를 나타냅니다.

- **1.0**: 데이터가 해당 형식에 완벽하게 맞습니다. Classifier가 즉시 선택됩니다.
- **0.0 ~ 0.99**: 부분적으로 맞거나 불확실합니다. 더 높은 확신도의 Classifier를 계속 탐색합니다.
- **0.0**: 데이터가 해당 형식에 전혀 맞지 않습니다.

### Classifier와 Crawler의 관계

하나의 Crawler에 여러 개의 커스텀 Classifier를 지정할 수 있으며, 지정된 순서대로 평가됩니다. 커스텀 Classifier의 순서는 분류 결과에 영향을 줄 수 있으므로, 가장 구체적인 Classifier를 먼저 배치하는 것이 좋습니다.

```bash
# Crawler에 커스텀 Classifier 지정
aws glue create-crawler \
  --name "multi-format-crawler" \
  --role "arn:aws:iam::123456789012:role/GlueCrawlerRole" \
  --database-name "analytics_db" \
  --classifiers '["apache-log-classifier", "app-log-classifier", "pipe-delimited-classifier"]' \
  --targets '{
    "S3Targets": [{
      "Path": "s3://my-data-lake/raw-logs/"
    }]
  }'
```

## 실전 활용

### 활용 사례 1: 멀티 포맷 로그 파일 분류

다양한 형식의 로그 파일이 혼재하는 S3 경로에서 각 형식을 올바르게 분류하여 별도의 테이블로 등록합니다.

```bash
# 애플리케이션 로그용 Grok Classifier
aws glue create-classifier \
  --grok-classifier '{
    "Classification": "application-log",
    "Name": "spring-boot-log-classifier",
    "GrokPattern": "%{TIMESTAMP_ISO8601:timestamp} %{SPACE}%{LOGLEVEL:level} %{NUMBER:pid} --- \\[%{DATA:thread}\\] %{JAVACLASS:logger} %{SPACE}: %{GREEDYDATA:message}",
    "CustomPatterns": "LOGLEVEL (TRACE|DEBUG|INFO|WARN|ERROR|FATAL)"
  }'

# Nginx 액세스 로그용 Grok Classifier
aws glue create-classifier \
  --grok-classifier '{
    "Classification": "nginx-access-log",
    "Name": "nginx-log-classifier",
    "GrokPattern": "%{IPORHOST:remote_addr} - %{DATA:remote_user} \\[%{HTTPDATE:time_local}\\] \\\"%{WORD:method} %{URIPATHPARAM:request} HTTP/%{NUMBER:http_version}\\\" %{NUMBER:status:int} %{NUMBER:body_bytes_sent:int} \\\"%{DATA:http_referer}\\\" \\\"%{DATA:http_user_agent}\\\""
  }'

# Crawler 실행
aws glue start-crawler --name "multi-format-crawler"

# Crawler 상태 확인
aws glue get-crawler \
  --name "multi-format-crawler" \
  --query 'Crawler.{State:State,LastCrawl:LastCrawl}'
```

### 활용 사례 2: 비표준 CSV 파일 처리

파이프(|) 구분자, 커스텀 날짜 형식, 인코딩이 특수한 CSV 파일을 올바르게 분류합니다.

```bash
# 한국어 데이터가 포함된 파이프 구분 파일용 Classifier
aws glue create-classifier \
  --csv-classifier '{
    "Name": "korean-pipe-csv",
    "Delimiter": "|",
    "QuoteSymbol": "\"",
    "ContainsHeader": "PRESENT",
    "Header": ["주문번호", "고객명", "제품명", "수량", "금액", "주문일시"],
    "DisableValueTrimming": false
  }'
```

### 활용 사례 3: 중첩 JSON API 응답 처리

REST API의 응답으로 받는 중첩된 JSON 데이터에서 원하는 레벨의 데이터를 테이블로 변환합니다.

```bash
# API 응답 JSON Classifier
aws glue create-classifier \
  --json-classifier '{
    "Name": "api-paginated-response",
    "JsonPath": "$.data.items[*]"
  }'

# Crawler에 JSON Classifier 적용
aws glue create-crawler \
  --name "api-data-crawler" \
  --role "arn:aws:iam::123456789012:role/GlueCrawlerRole" \
  --database-name "api_data_db" \
  --classifiers '["api-paginated-response"]' \
  --targets '{
    "S3Targets": [{
      "Path": "s3://my-api-data/responses/",
      "Exclusions": ["**/error/**", "**/metadata/**"]
    }]
  }'
```

### 활용 사례 4: XML 데이터 파이프라인

레거시 시스템에서 생성된 XML 데이터를 Glue Data Catalog에 등록하고 Athena로 분석합니다.

```bash
# XML Classifier 생성
aws glue create-classifier \
  --xml-classifier '{
    "Name": "transaction-xml",
    "Classification": "financial-transactions",
    "RowTag": "transaction"
  }'

# Crawler 생성 및 실행
aws glue create-crawler \
  --name "xml-transaction-crawler" \
  --role "arn:aws:iam::123456789012:role/GlueCrawlerRole" \
  --database-name "finance_db" \
  --classifiers '["transaction-xml"]' \
  --targets '{"S3Targets": [{"Path": "s3://legacy-data/transactions/"}]}'

aws glue start-crawler --name "xml-transaction-crawler"
```

## 모범 사례/보안

### Classifier 설계 모범 사례

1. **구체적인 Classifier 우선 배치**: 여러 커스텀 Classifier를 사용할 때, 가장 구체적인 패턴의 Classifier를 먼저 배치합니다. 이렇게 하면 오분류의 가능성이 줄어듭니다.

2. **Grok 패턴 테스트**: Grok Classifier를 생성하기 전에, 온라인 Grok 디버거(예: grokdebugger.com)에서 패턴을 먼저 테스트합니다.

3. **최소 데이터 타입 지정**: Grok Classifier에서 데이터 타입을 지정할 때(예: `%{NUMBER:status:int}`), 필요한 경우에만 타입 변환을 수행합니다.

4. **CSV Classifier 헤더 명시**: 헤더가 일관되지 않을 수 있는 경우, `ContainsHeader`를 `ABSENT`으로 설정하고 `Header` 배열에서 열 이름을 직접 지정합니다.

5. **JSON Classifier 경로 검증**: JSONPath 표현식이 실제 데이터의 구조와 일치하는지 사전에 검증합니다.

6. **Classifier 버전 관리**: Classifier의 변경 이력을 Git이나 CloudFormation으로 관리하여 추적 가능성을 확보합니다.

### 문제 해결

```bash
# Crawler 로그 확인 (CloudWatch Logs)
aws logs filter-log-events \
  --log-group-name /aws-glue/crawlers \
  --log-stream-name-prefix "multi-format-crawler" \
  --filter-pattern "classifier" \
  --query 'events[].message' \
  --output text

# Crawler 실행 이력 조회
aws glue get-crawler-metrics \
  --crawler-name-list '["multi-format-crawler"]' \
  --query 'CrawlerMetricsList[].{Name:CrawlerName,TablesCreated:TablesCreated,TablesUpdated:TablesUpdated,LastRuntimeSeconds:LastRuntimeSeconds}'
```

### 보안 고려사항

1. **IAM 권한 분리**: Classifier 생성/수정 권한과 Crawler 실행 권한을 분리합니다.
2. **변경 감사**: CloudTrail을 통해 Classifier의 생성, 수정, 삭제 이력을 추적합니다.
3. **데이터 접근 제어**: Classifier가 스캔하는 데이터 소스에 대한 접근을 IAM 정책으로 제한합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "glue:CreateClassifier",
        "glue:UpdateClassifier",
        "glue:GetClassifier",
        "glue:GetClassifiers"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Deny",
      "Action": "glue:DeleteClassifier",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:PrincipalTag/Role": "DataAdmin"
        }
      }
    }
  ]
}
```

## 관련 서비스 비교

| 항목 | Glue Classifier | Glue Crawler | Glue Data Catalog | AWS Lake Formation |
|------|----------------|-------------|-------------------|--------------------|
| 역할 | 데이터 형식 판별 | 데이터 스캔 | 메타데이터 저장 | 데이터 거버넌스 |
| 동작 시점 | Crawler 실행 중 | 수동/스케줄 실행 | 항상 가용 | 항상 가용 |
| 커스터마이징 | Grok/JSON/CSV/XML | 대상/제외 패턴 | 테이블/파티션 | 권한/태그 |
| 의존 관계 | Crawler에 의존 | Classifier 사용 | Crawler 결과 저장 | Data Catalog 활용 |

### Classifier vs 수동 테이블 정의

| 방식 | 장점 | 단점 |
|------|------|------|
| Classifier + Crawler | 자동화, 스키마 변경 자동 감지 | 복잡한 구조 인식 한계 |
| 수동 테이블 정의 | 완전한 제어, 정확한 스키마 | 수동 유지보수, 변경 추적 어려움 |
| 혼합 방식 | 유연성 극대화 | 관리 복잡성 증가 |

## 요약

AWS Glue Classifier는 데이터의 형식과 스키마를 자동으로 판별하여 Data Catalog에 정확한 메타데이터를 등록하는 핵심 구성 요소입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **네 가지 커스텀 유형**: Grok(정규 표현식), JSON(JSONPath), CSV(구분자/헤더), XML(RowTag) 네 가지 유형의 커스텀 Classifier를 지원합니다.
- **내장 Classifier**: CSV, JSON, Avro, Parquet, ORC 등 일반적인 형식에 대한 내장 Classifier가 제공됩니다.
- **평가 순서**: 커스텀 Classifier가 내장 Classifier보다 먼저 평가되며, 확신도 1.0인 Classifier가 선택됩니다.
- **Grok 패턴**: 로그 파일 등 비정형 텍스트 데이터의 스키마 추출에 강력한 도구입니다.
- **JSON 경로 매핑**: 중첩된 JSON 구조에서 원하는 레벨의 데이터를 테이블 행으로 변환할 수 있습니다.
- **Crawler 연동**: Classifier는 Crawler의 구성 요소로, Crawler 실행 시 자동으로 평가됩니다.

비표준 데이터 형식이나 복잡한 구조의 데이터를 Data Catalog에 등록해야 하는 경우, 적절한 커스텀 Classifier를 설계하는 것이 올바른 메타데이터 관리의 첫 걸음입니다.