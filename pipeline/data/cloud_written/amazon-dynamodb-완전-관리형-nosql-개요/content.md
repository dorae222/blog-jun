<!-- infographic-hero -->
![Amazon DynamoDB 완전 관리형 NoSQL 개요 핵심 요약](figures/infographic.svg)

*Figure: Amazon DynamoDB 완전 관리형 NoSQL 개요 한 장 요약 인포그래픽*

# Amazon DynamoDB 완전 관리형 NoSQL 개요

## 개요

Amazon DynamoDB는 AWS가 2012년에 출시한 완전 관리형(Fully Managed) NoSQL 데이터베이스 서비스입니다. Key-Value와 Document 데이터 모델을 모두 지원하며, 어떤 규모에서도 한 자릿수 밀리초의 응답 시간을 보장하도록 설계되었습니다. Amazon이 2007년에 발표한 논문 "Dynamo: Amazon's Highly Available Key-value Store"의 분산 시스템 원리에 기반하고 있으며, 이후 SSD 기반 스토리지와 멀티 리전 복제 기능이 추가되어 현재의 형태로 발전했습니다.

DynamoDB는 다음과 같은 특성을 가집니다.

- **서버리스(Serverless)**: 인프라 관리, 패치 적용, 클러스터 구성이 모두 자동화됩니다.
- **수평 확장(Horizontal Scaling)**: 파티션 자동 분할로 트래픽 증가에 자동 대응합니다.
- **단일 자릿수 밀리초 지연**: 어떤 규모에서도 일관된 응답 시간을 제공합니다.
- **다중 리전(Multi-Region) 액티브-액티브 복제**: Global Tables로 글로벌 분산을 지원합니다.

전통적인 RDBMS와 달리 DynamoDB는 스키마가 유연하며, 조인이 없고, Primary Key 설계가 성능과 비용을 좌우합니다. 따라서 데이터 모델링 단계에서 액세스 패턴을 미리 정의하는 "Single Table Design" 또는 "Access Pattern First" 접근법이 권장됩니다.

---

## 핵심 기능

### 1. 데이터 모델

DynamoDB의 데이터 구조는 다음과 같은 계층으로 구성됩니다.

| 개념 | 설명 |
|------|------|
| Table | 데이터의 최상위 컨테이너. 관계형의 테이블에 해당 |
| Item | 한 행(row)에 해당하는 단위. 최대 400KB |
| Attribute | 항목의 속성. Scalar, Document, Set 타입 지원 |
| Primary Key | Partition Key 단독 또는 Partition Key + Sort Key 조합 |

Primary Key는 두 가지 형태가 있습니다.

- **Simple Primary Key**: Partition Key 1개로 항목을 고유 식별합니다.
- **Composite Primary Key**: Partition Key + Sort Key 조합. 같은 Partition Key 내에서 Sort Key로 정렬되며 Range Query가 가능합니다.

Partition Key는 내부적으로 해시 함수에 입력되어 데이터가 저장될 물리 파티션을 결정합니다. 따라서 Partition Key의 카디널리티(고유 값의 다양성)와 액세스 분포가 균등해야 핫 파티션(Hot Partition) 문제를 피할 수 있습니다.

### 2. 용량 모드 (Capacity Mode)

DynamoDB는 두 가지 청구 모드를 제공합니다.

**On-Demand 모드**
- 실제 요청 수에 비례하여 과금합니다.
- 트래픽이 예측 불가능하거나 신규 워크로드에 적합합니다.
- 즉시 트래픽 폭증에 대응 가능합니다.

**Provisioned 모드**
- 초당 읽기/쓰기 처리량을 사전 예약합니다.
- 단위: RCU(Read Capacity Unit), WCU(Write Capacity Unit).
- Auto Scaling을 활성화하여 사용량에 따라 자동 증감 가능합니다.
- 예측 가능한 워크로드와 비용 최적화에 유리합니다.

| 작업 | 단위 | 항목 크기 기준 |
|------|------|----------------|
| Strongly Consistent Read | 1 RCU | 4KB 이하 |
| Eventually Consistent Read | 0.5 RCU | 4KB 이하 |
| Transactional Read | 2 RCU | 4KB 이하 |
| Standard Write | 1 WCU | 1KB 이하 |
| Transactional Write | 2 WCU | 1KB 이하 |

```bash
# On-Demand 모드로 테이블 생성
aws dynamodb create-table \
  --table-name UserSessions \
  --attribute-definitions \
    AttributeName=user_id,AttributeType=S \
    AttributeName=session_id,AttributeType=S \
  --key-schema \
    AttributeName=user_id,KeyType=HASH \
    AttributeName=session_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region ap-northeast-2
```

```bash
# Provisioned 모드 + Auto Scaling
aws dynamodb create-table \
  --table-name OrderEvents \
  --attribute-definitions \
    AttributeName=order_id,AttributeType=S \
  --key-schema \
    AttributeName=order_id,KeyType=HASH \
  --provisioned-throughput \
    ReadCapacityUnits=100,WriteCapacityUnits=50 \
  --region ap-northeast-2
```

### 3. 읽기 일관성 모델

DynamoDB는 두 가지 일관성 옵션을 제공합니다.

- **Eventually Consistent Read (기본)**: 쓰기가 모든 복제본에 전파되기 전에 읽으면 이전 값이 반환될 수 있습니다. 응답 시간이 빠르고 비용이 절반입니다.
- **Strongly Consistent Read (옵션)**: 가장 최근 쓰기를 보장합니다. 비용이 두 배이며 약간의 지연이 추가됩니다.

또한 트랜잭션이 필요한 경우 `TransactGetItems`, `TransactWriteItems`로 ACID 보장이 가능합니다. 트랜잭션은 일반 작업의 두 배 비용이 청구됩니다.

### 4. 인덱스 (GSI / LSI)

DynamoDB는 Primary Key 외에 두 가지 보조 인덱스를 지원합니다.

**Global Secondary Index (GSI)**
- 다른 Partition Key + Sort Key를 사용한 인덱스입니다.
- 테이블 생성 후에도 추가/삭제 가능합니다.
- 자체 RCU/WCU를 가지며, 비동기적으로 복제됩니다(Eventually Consistent).
- 테이블당 최대 20개.

**Local Secondary Index (LSI)**
- Partition Key는 같지만 Sort Key가 다른 인덱스입니다.
- 테이블 생성 시에만 정의 가능합니다.
- Strongly Consistent Read를 지원합니다.
- 테이블당 최대 5개.

```bash
# GSI를 포함한 테이블 생성
aws dynamodb create-table \
  --table-name Posts \
  --attribute-definitions \
    AttributeName=post_id,AttributeType=S \
    AttributeName=author_id,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema \
    AttributeName=post_id,KeyType=HASH \
  --global-secondary-indexes \
    "[{
      \"IndexName\": \"AuthorIndex\",
      \"KeySchema\": [
        {\"AttributeName\":\"author_id\",\"KeyType\":\"HASH\"},
        {\"AttributeName\":\"created_at\",\"KeyType\":\"RANGE\"}
      ],
      \"Projection\": {\"ProjectionType\":\"ALL\"}
    }]" \
  --billing-mode PAY_PER_REQUEST \
  --region ap-northeast-2
```

### 5. Global Tables

Global Tables는 멀티 리전 액티브-액티브(Active-Active) 복제를 제공합니다.

- 여러 리전에 동일한 테이블을 배포하고, 각 리전에서 모두 읽기/쓰기가 가능합니다.
- 리전 간 비동기 복제로 일반적으로 1초 이내에 전파됩니다.
- 충돌 해결 전략은 Last Writer Wins(LWW)를 기본으로 합니다.
- 글로벌 사용자 대상 서비스, DR(Disaster Recovery), 지리적 분산 읽기에 활용됩니다.

```bash
# Global Tables 활성화 (Version 2019.11.21)
aws dynamodb update-table \
  --table-name UserProfiles \
  --replica-updates "[{\"Create\": {\"RegionName\": \"us-west-2\"}}]" \
  --region ap-northeast-2
```

### 6. DAX (DynamoDB Accelerator)

DAX는 DynamoDB 전용 인메모리 캐시 클러스터입니다.

- 마이크로초(microsecond) 단위 응답 시간을 제공합니다.
- 애플리케이션 코드 변경 없이 DynamoDB SDK와 호환됩니다.
- Write-Through 캐시로 동작하므로 쓰기는 DynamoDB와 DAX에 동시 반영됩니다.
- 읽기 비중이 높고 동일 항목을 반복 조회하는 워크로드에 적합합니다.

### 7. DynamoDB Streams

Streams는 테이블의 항목 변경 이벤트(INSERT, MODIFY, REMOVE)를 24시간 동안 시간 순서로 캡처합니다. 변경 데이터 캡처(CDC, Change Data Capture) 패턴의 핵심 구성 요소입니다.

- Lambda 트리거로 직접 연동하여 이벤트 기반 아키텍처를 구성할 수 있습니다.
- Kinesis Data Streams로도 라우팅 가능합니다.
- StreamViewType: KEYS_ONLY, NEW_IMAGE, OLD_IMAGE, NEW_AND_OLD_IMAGES.

상세 내용은 [[amazon-dynamodb-streams|DynamoDB Streams]] 포스트를 참고하세요.

### 8. TTL (Time To Live)

TTL은 항목별 만료 시간을 지정하여 자동 삭제하는 기능입니다.

- 만료 시간은 Unix Timestamp(초 단위) 속성으로 지정합니다.
- 만료 후 최대 48시간 이내에 백그라운드에서 삭제됩니다.
- 삭제 시 WCU를 소비하지 않으므로 비용이 절감됩니다.
- 세션 데이터, 임시 토큰, 로그 데이터 정리에 활용됩니다.

```bash
# TTL 활성화
aws dynamodb update-time-to-live \
  --table-name UserSessions \
  --time-to-live-specification "Enabled=true,AttributeName=expires_at" \
  --region ap-northeast-2
```

### 9. 백업 및 PITR (Point-in-Time Recovery)

DynamoDB는 두 가지 백업 메커니즘을 제공합니다.

- **On-Demand Backup**: 사용자가 명시적으로 생성. 보존 기간 제한 없음.
- **PITR (Point-in-Time Recovery)**: 35일 이내 어느 시점으로든 초 단위 복원 가능.

```bash
# PITR 활성화
aws dynamodb update-continuous-backups \
  --table-name OrderEvents \
  --point-in-time-recovery-specification "PointInTimeRecoveryEnabled=true" \
  --region ap-northeast-2

# 특정 시점으로 복원
aws dynamodb restore-table-to-point-in-time \
  --source-table-name OrderEvents \
  --target-table-name OrderEvents-restored \
  --restore-date-time "2026-04-25T10:30:00Z" \
  --region ap-northeast-2
```

---

## 아키텍처

### 내부 동작 원리

DynamoDB는 다음과 같은 분산 아키텍처로 동작합니다.

```
[Application]
    |
    v
[DynamoDB API Endpoint (HTTPS)]
    |
    v
[Request Router]
    |
    +--> [Partition 1] --> [3개 AZ에 복제]
    +--> [Partition 2] --> [3개 AZ에 복제]
    +--> [Partition N] --> [3개 AZ에 복제]
              |
              v
         [SSD Storage Layer]
```

1. **Partition Key Hashing**: 클라이언트가 보낸 Partition Key는 내부 해시 함수를 거쳐 특정 파티션으로 라우팅됩니다.
2. **3개 AZ 복제**: 각 파티션은 동일 리전 내 3개의 가용 영역(AZ)에 동기적으로 복제됩니다.
3. **Quorum 기반 일관성**: Strongly Consistent Read는 다수의 복제본에서 응답을 받아 최신 값을 반환합니다.

### 파티션 자동 분할

DynamoDB는 다음 두 가지 조건에서 파티션을 자동으로 분할합니다.

- 파티션의 데이터 크기가 10GB를 초과한 경우
- 파티션의 처리량이 3,000 RCU 또는 1,000 WCU를 초과한 경우

이로 인해 잘 설계된 Partition Key는 데이터 분포와 액세스 분포가 모두 균등해야 합니다. 모든 트래픽이 한 파티션에 집중되면 핫 파티션 문제가 발생하여 ProvisionedThroughputExceededException이 발생할 수 있습니다.

### Adaptive Capacity

DynamoDB는 Adaptive Capacity 기능을 통해 일시적인 핫 파티션에도 자동으로 처리량을 재분배합니다. 다만 데이터 모델 자체가 잘못된 경우(예: 단일 user_id가 전체 트래픽의 90%를 차지)는 근본적으로 모델 재설계가 필요합니다.

---

## 실전 사용

### 1. CLI로 항목 조작

```bash
# PutItem (단일 항목 삽입)
aws dynamodb put-item \
  --table-name Posts \
  --item '{
    "post_id": {"S": "p-001"},
    "author_id": {"S": "u-100"},
    "title": {"S": "DynamoDB 시작하기"},
    "created_at": {"S": "2026-04-26T10:00:00Z"},
    "view_count": {"N": "0"}
  }' \
  --region ap-northeast-2

# GetItem (Primary Key로 조회)
aws dynamodb get-item \
  --table-name Posts \
  --key '{"post_id": {"S": "p-001"}}' \
  --consistent-read \
  --region ap-northeast-2

# Query (특정 author의 게시물 조회 - GSI 사용)
aws dynamodb query \
  --table-name Posts \
  --index-name AuthorIndex \
  --key-condition-expression "author_id = :aid AND created_at > :ts" \
  --expression-attribute-values '{
    ":aid": {"S": "u-100"},
    ":ts": {"S": "2026-01-01"}
  }' \
  --region ap-northeast-2

# UpdateItem (원자적 카운터 증가)
aws dynamodb update-item \
  --table-name Posts \
  --key '{"post_id": {"S": "p-001"}}' \
  --update-expression "ADD view_count :inc" \
  --expression-attribute-values '{":inc": {"N": "1"}}' \
  --region ap-northeast-2
```

### 2. Python (boto3) 예제

```python
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb", region_name="ap-northeast-2")
table = dynamodb.Table("Posts")

# 단일 항목 삽입
table.put_item(
    Item={
        "post_id": "p-002",
        "author_id": "u-100",
        "title": "DynamoDB 모델링",
        "created_at": "2026-04-26T11:00:00Z",
        "view_count": 0,
    }
)

# Query (특정 작성자의 최근 게시물)
response = table.query(
    IndexName="AuthorIndex",
    KeyConditionExpression=Key("author_id").eq("u-100"),
    ScanIndexForward=False,  # 최신순 정렬
    Limit=10,
)
for item in response["Items"]:
    print(item["title"], item["created_at"])
```

### 3. Terraform 예제

```hcl
resource "aws_dynamodb_table" "posts" {
  name         = "Posts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "post_id"

  attribute {
    name = "post_id"
    type = "S"
  }

  attribute {
    name = "author_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "AuthorIndex"
    hash_key        = "author_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  tags = {
    Environment = "production"
    Service     = "blog"
  }
}
```

### 4. Single Table Design 패턴

복잡한 액세스 패턴을 단일 테이블로 표현하는 기법입니다. PK/SK에 엔티티 타입 접두사를 부여하여 다양한 엔티티를 함께 저장합니다.

| PK | SK | 항목 종류 |
|----|-----|----------|
| `USER#u-100` | `PROFILE` | 사용자 프로필 |
| `USER#u-100` | `POST#p-001` | 사용자가 작성한 게시물 |
| `USER#u-100` | `FOLLOWER#u-200` | 팔로워 관계 |
| `POST#p-001` | `COMMENT#c-001` | 게시물 댓글 |

이 패턴은 BatchGetItem 한 번으로 다양한 엔티티를 조회할 수 있어 RDB의 JOIN을 대체하는 효과가 있습니다.

---

## 가격 / 한도

### 주요 비용 (서울 리전 기준, 2026년 4월)

| 항목 | On-Demand | Provisioned |
|------|-----------|-------------|
| 쓰기 | $1.25 / 100만 WRU | $0.00065 / WCU-시간 |
| 읽기 | $0.25 / 100만 RRU | $0.00013 / RCU-시간 |
| 스토리지 | $0.25 / GB-월 | $0.25 / GB-월 |
| 백업 (PITR) | $0.20 / GB-월 | 동일 |
| Global Tables 복제 | $1.875 / 100만 rWCU | 동일 |

WRU/RRU(On-Demand)는 WCU/RCU와 단위는 동일하지만 청구 방식이 다릅니다.

### 주요 한도

| 항목 | 한도 |
|------|------|
| 항목 크기 | 400 KB |
| Partition Key 크기 | 2,048 바이트 |
| Sort Key 크기 | 1,024 바이트 |
| 테이블당 GSI | 20개 |
| 테이블당 LSI | 5개 |
| Query 응답 크기 | 1 MB |
| BatchGetItem | 100개 항목 / 16 MB |
| BatchWriteItem | 25개 항목 / 16 MB |

---

## Best Practice

### 데이터 모델링

1. **액세스 패턴 우선**: 데이터 모델링 전에 모든 쿼리 패턴을 정리합니다.
2. **Partition Key 카디널리티 확보**: user_id, order_id 등 고유 값이 많은 속성을 사용합니다.
3. **Hot Partition 회피**: timestamp만 사용하는 PK는 피하고, 접두사나 샤딩을 추가합니다.
4. **Single Table Design 검토**: 관련 엔티티를 한 테이블에 저장하면 비용과 지연 시간이 모두 감소합니다.
5. **Sparse Index 활용**: 특정 속성이 있는 항목만 인덱싱되도록 GSI를 설계하면 비용 절감 효과가 큽니다.

### 성능

1. **Eventually Consistent Read 우선**: 강한 일관성이 필요하지 않다면 비용을 절반으로 줄입니다.
2. **BatchGetItem / BatchWriteItem 사용**: 다수 항목 처리 시 네트워크 라운드트립을 줄입니다.
3. **DAX 도입**: 동일 항목 반복 조회가 많다면 마이크로초 응답이 가능합니다.
4. **Projection 최소화**: GSI에서 ALL 대신 필요한 속성만 projection하면 비용과 응답 크기가 감소합니다.

### 운영

1. **CloudWatch 알람**: ConsumedReadCapacityUnits, ThrottledRequests를 모니터링합니다.
2. **PITR 활성화**: 프로덕션 테이블은 반드시 PITR을 활성화합니다.
3. **태그 일관성**: 비용 추적을 위해 Environment, Owner, Service 태그를 일관되게 적용합니다.
4. **IAM 최소 권한**: 테이블 단위, 항목 단위(Condition)로 권한을 세밀하게 부여합니다.
5. **Streams 보존 기간 24시간 인지**: Lambda 처리 실패 시 DLQ를 구성합니다.

---

## 관련 서비스

| 서비스 | 비교 포인트 |
|--------|-------------|
| Amazon RDS | 관계형 / 트랜잭션 / JOIN 지원. 복잡한 보고서 쿼리에 강점 |
| Amazon Aurora | RDS의 클라우드 네이티브 버전. 분산 스토리지로 성능 강화 |
| Amazon ElastiCache | 인메모리 키-값 캐시. DynamoDB 앞단에 두거나 DAX 대안 |
| Amazon Keyspaces | Cassandra 호환. CQL 인터페이스 필요 시 |
| Amazon DocumentDB | MongoDB 호환. JSON 문서 + Aggregation Pipeline 필요 시 |
| Amazon Neptune | Graph DB. 관계 탐색이 핵심인 경우 |

DynamoDB는 키 기반 조회가 명확하고 예측 가능한 액세스 패턴을 가진 워크로드(IoT, 게임 리더보드, 세션 스토어, 카탈로그, 광고 서빙 등)에 최적화되어 있습니다.

---

## 관련 문서

- [[amazon-dynamodb-streams|DynamoDB Streams]] - 변경 이벤트 캡처와 Lambda 트리거 패턴
- [[amazon-rds|Amazon RDS]] - 관계형 데이터베이스 관리 서비스 비교
- [[amazon-aurora-개요|Amazon Aurora]] - 클라우드 네이티브 관계형 DB
- [[amazon-elasticache인메모리-캐시-서비스-개요|Amazon ElastiCache]] - 인메모리 캐시
