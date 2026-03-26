# AWS Clean Rooms 개요 및 활용

## 개요

AWS Clean Rooms는 여러 조직이 원본 데이터를 서로 공유하지 않으면서도 공동 분석을 수행할 수 있게 해주는 서비스입니다. 2023년에 정식 출시된 이 서비스는 데이터 프라이버시와 보안을 유지하면서 협업 분석을 가능하게 합니다.

현대 비즈니스 환경에서 기업 간 데이터 협업의 필요성은 계속 증가하고 있습니다. 그러나 개인정보 보호법(GDPR, CCPA 등)의 강화와 데이터 보안에 대한 우려로 인해, 원본 데이터를 직접 공유하는 것은 점점 더 어려워지고 있습니다. AWS Clean Rooms는 이 문제를 해결하기 위해 설계되었습니다.

주요 특징은 다음과 같습니다.

- **데이터 이동 없는 협업**: 원본 데이터를 복사하거나 이동하지 않고, 각자의 AWS 환경에 데이터를 유지한 채 공동 분석을 수행합니다.
- **세밀한 분석 규칙**: 어떤 쿼리를 실행할 수 있는지, 어떤 형태로 결과를 받을 수 있는지 상세한 규칙을 설정할 수 있습니다.
- **암호화 컴퓨팅(Cryptographic Computing)**: 데이터를 암호화한 상태에서도 조인 및 집계 연산을 수행할 수 있습니다.
- **AWS Glue 통합**: 기존 AWS Glue 데이터 카탈로그와 연동하여 메타데이터를 관리합니다.
- **감사 로그**: 모든 쿼리 실행 이력을 CloudTrail로 추적할 수 있습니다.

## 핵심 기능

### 1. 협업(Collaboration) 생성

협업은 Clean Rooms의 기본 단위로, 둘 이상의 AWS 계정이 참여하여 공동 분석 환경을 구성합니다.

```bash
# 협업 생성
aws cleanrooms create-collaboration \
  --name "marketing-analytics-collab" \
  --description "마케팅 분석을 위한 광고주-퍼블리셔 협업" \
  --creator-member-abilities '["CAN_QUERY", "CAN_RECEIVE_RESULTS"]' \
  --creator-display-name "Advertiser Inc." \
  --members '[{
    "accountId": "987654321098",
    "memberAbilities": ["CAN_QUERY"],
    "displayName": "Publisher Corp."
  }]' \
  --query-log-status ENABLED \
  --data-encryption-metadata '{
    "allowCleartext": false,
    "allowDuplicates": false,
    "allowJoinsOnColumnsWithDifferentNames": true,
    "preserveNulls": false
  }'
```

### 2. 멤버십(Membership)

협업에 참여하는 각 AWS 계정은 멤버십을 통해 역할과 권한을 갖습니다.

- **CAN_QUERY**: 쿼리를 실행할 수 있는 권한입니다.
- **CAN_RECEIVE_RESULTS**: 쿼리 결과를 받을 수 있는 권한입니다.

```bash
# 멤버십 생성 (초대받은 멤버가 수락)
aws cleanrooms create-membership \
  --collaboration-identifier abc123-collaboration-id \
  --query-log-status ENABLED \
  --default-result-configuration '{
    "outputConfiguration": {
      "s3": {
        "resultFormat": "PARQUET",
        "bucket": "my-cleanrooms-results",
        "keyPrefix": "results/"
      }
    },
    "roleArn": "arn:aws:iam::987654321098:role/CleanRoomsResultRole"
  }'

# 협업 목록 조회
aws cleanrooms list-collaborations \
  --member-status ACTIVE \
  --query 'collaborationList[].{Name:name,Id:id,MemberStatus:memberStatus}' \
  --output table
```

### 3. 구성된 테이블(Configured Table)

각 멤버는 자신의 AWS Glue Data Catalog 테이블을 Clean Rooms에 등록하여 분석에 사용할 수 있도록 합니다.

```bash
# 구성된 테이블 생성
aws cleanrooms create-configured-table \
  --name "customer-segments" \
  --table-reference '{
    "glue": {
      "tableName": "customer_segments",
      "databaseName": "marketing_db"
    }
  }' \
  --allowed-columns '["hashed_email", "segment", "ltv_score", "region"]' \
  --analysis-method DIRECT_QUERY

# 구성된 테이블에 분석 규칙 생성
aws cleanrooms create-configured-table-analysis-rule \
  --configured-table-identifier table-abc123 \
  --analysis-rule-type AGGREGATION \
  --analysis-rule-policy '{
    "v1": {
      "aggregation": {
        "aggregateColumns": [{
          "columnNames": ["ltv_score"],
          "function": "AVG"
        }],
        "joinColumns": ["hashed_email"],
        "joinRequired": "QUERY_RUNNER",
        "dimensionColumns": ["segment", "region"],
        "scalarFunctions": ["UPPER", "LOWER"],
        "outputConstraints": [{
          "columnName": "hashed_email",
          "minimum": 100,
          "type": "COUNT_DISTINCT"
        }]
      }
    }
  }'
```

### 4. 분석 규칙 (Analysis Rules)

Clean Rooms의 핵심 보안 메커니즘으로, 데이터에 대해 허용되는 분석 유형과 결과의 형태를 제한합니다.

#### 분석 규칙 유형

- **AGGREGATION**: 집계 쿼리만 허용합니다. COUNT, SUM, AVG 등의 집계 함수를 사용해야 하며, 개별 레코드 수준의 결과는 반환되지 않습니다.
- **LIST**: 개별 레코드를 반환할 수 있지만, 허용된 열만 출력됩니다.
- **CUSTOM**: 사용자 정의 분석 규칙으로, 더 유연한 쿼리 제어가 가능합니다.

#### 출력 제약 (Output Constraints)

집계 결과에 최소 레코드 수 제약을 설정하여, 너무 적은 수의 레코드로 구성된 그룹이 반환되지 않도록 합니다. 이를 통해 개인 식별의 위험을 줄입니다.

### 5. 암호화 컴퓨팅 (Cryptographic Computing)

AWS Clean Rooms Cryptographic Computing을 사용하면 데이터를 암호화된 상태로 유지하면서 조인 및 집계 연산을 수행할 수 있습니다.

```bash
# 암호화 컴퓨팅이 활성화된 협업에서 사용할 키 페어 생성
# Clean Rooms ML을 사용한 유사 모델링
aws cleanrooms-ml create-training-dataset \
  --name "lookalike-training" \
  --role-arn arn:aws:iam::123456789012:role/CleanRoomsMLRole \
  --training-data '[{
    "type": "INTERACTIONS",
    "inputConfig": {
      "s3Source": {
        "s3Uri": "s3://my-training-data/interactions/"
      }
    }
  }]'
```

### 6. Clean Rooms ML

Clean Rooms ML은 기계 학습 기반의 유사 사용자 모델링(Lookalike Modeling)을 Clean Rooms 환경에서 수행할 수 있게 합니다.

## 아키텍처/동작 원리

### 전체 아키텍처

```
[멤버 A - AWS 계정]              [멤버 B - AWS 계정]
  |                                |
  [Glue Data Catalog]             [Glue Data Catalog]
  |                                |
  [구성된 테이블 A]               [구성된 테이블 B]
  |                                |
  +---------- [협업] -------------+
              |
         [분석 규칙]
              |
         [쿼리 실행]
              |
         [결과 (S3)]
```

### 동작 흐름

1. **협업 생성**: 멤버 A가 협업을 생성하고 멤버 B를 초대합니다.
2. **테이블 등록**: 각 멤버가 자신의 Glue 테이블을 Clean Rooms에 등록하고 분석 규칙을 설정합니다.
3. **쿼리 실행**: 쿼리 권한을 가진 멤버가 SQL 쿼리를 실행합니다.
4. **규칙 검증**: Clean Rooms가 쿼리를 분석 규칙과 대조하여 검증합니다.
5. **데이터 처리**: 검증된 쿼리가 각 멤버의 데이터에 대해 실행됩니다.
6. **결과 반환**: 분석 규칙에 맞는 형태로 결과가 S3에 저장됩니다.

### 데이터 보호 메커니즘

#### 분석 규칙 기반 보호

- 허용된 쿼리 유형만 실행 가능합니다.
- 결과에 최소 집계 크기 제약이 적용됩니다.
- 허용된 열만 출력에 포함됩니다.

#### 암호화 컴퓨팅

- 클라이언트 측 암호화로 데이터가 전송 전에 암호화됩니다.
- 암호화된 상태에서 조인 키 매칭이 수행됩니다.
- Clean Rooms 서비스도 원본 데이터를 볼 수 없습니다.

## 실전 활용

### 활용 사례 1: 광고 효과 측정

광고주와 퍼블리셔가 각자의 고객 데이터를 공유하지 않으면서 광고 캠페인의 효과를 측정합니다.

```bash
# 보호된 쿼리 실행 (광고 효과 측정)
aws cleanrooms start-protected-query \
  --type SQL \
  --sql-parameters '{
    "queryString": "SELECT a.campaign_id, a.ad_group, COUNT(DISTINCT a.hashed_email) as reach, COUNT(DISTINCT CASE WHEN b.converted = true THEN b.hashed_email END) as conversions, CAST(COUNT(DISTINCT CASE WHEN b.converted = true THEN b.hashed_email END) AS DOUBLE) / COUNT(DISTINCT a.hashed_email) as conversion_rate FROM advertiser_impressions a INNER JOIN publisher_conversions b ON a.hashed_email = b.hashed_email GROUP BY a.campaign_id, a.ad_group HAVING COUNT(DISTINCT a.hashed_email) >= 100"
  }' \
  --membership-identifier membership-xyz789 \
  --result-configuration '{
    "outputConfiguration": {
      "s3": {
        "resultFormat": "CSV",
        "bucket": "my-cleanrooms-results",
        "keyPrefix": "campaign-analysis/"
      }
    }
  }'

# 보호된 쿼리 상태 확인
aws cleanrooms get-protected-query \
  --membership-identifier membership-xyz789 \
  --protected-query-identifier query-abc123 \
  --query 'protectedQuery.{Status:status,ResultS3:result.output.s3.location}'
```

### 활용 사례 2: 금융 기관 간 사기 탐지 협업

여러 금융 기관이 각자의 거래 데이터를 공유하지 않으면서, 의심 거래 패턴을 공동으로 분석합니다.

```bash
# 사기 탐지용 구성된 테이블 분석 규칙
aws cleanrooms create-configured-table-analysis-rule \
  --configured-table-identifier fraud-detection-table \
  --analysis-rule-type AGGREGATION \
  --analysis-rule-policy '{
    "v1": {
      "aggregation": {
        "aggregateColumns": [
          {"columnNames": ["transaction_amount"], "function": "SUM"},
          {"columnNames": ["transaction_amount"], "function": "AVG"},
          {"columnNames": ["transaction_id"], "function": "COUNT"}
        ],
        "joinColumns": ["hashed_account_id"],
        "joinRequired": "QUERY_RUNNER",
        "dimensionColumns": ["transaction_type", "risk_level", "country"],
        "scalarFunctions": ["UPPER"],
        "outputConstraints": [{
          "columnName": "hashed_account_id",
          "minimum": 50,
          "type": "COUNT_DISTINCT"
        }]
      }
    }
  }'
```

### 활용 사례 3: 헬스케어 데이터 공동 연구

제약사와 병원이 환자 데이터를 직접 공유하지 않으면서 임상 연구를 수행합니다. Clean Rooms의 분석 규칙을 통해 개인 환자를 식별할 수 없는 형태로만 결과를 받을 수 있습니다.

### 활용 사례 4: 유사 고객 모델링 (Lookalike Modeling)

Clean Rooms ML을 사용하여 파트너사의 고객 데이터를 기반으로 유사 고객 세그먼트를 생성합니다.

```bash
# 유사 모델 학습 데이터셋 조회
aws cleanrooms-ml list-training-datasets \
  --query 'trainingDatasets[].{Name:name,Status:status,Created:createTime}' \
  --output table
```

## 모범 사례/보안

### 보안 모범 사례

1. **최소 권한 원칙**: 각 멤버에게 필요한 최소한의 능력(CAN_QUERY, CAN_RECEIVE_RESULTS)만 부여합니다.

2. **엄격한 분석 규칙 설정**: 출력 제약의 최소값을 충분히 높게 설정하여 개인 식별 위험을 최소화합니다. 일반적으로 COUNT_DISTINCT 최소값을 100 이상으로 설정하는 것을 권장합니다.

3. **암호화 컴퓨팅 활용**: 데이터의 민감도가 높은 경우 암호화 컴퓨팅을 활성화하여, Clean Rooms 서비스조차도 원본 데이터에 접근할 수 없도록 합니다.

4. **쿼리 로그 활성화**: 모든 협업에서 쿼리 로그를 활성화하여 감사 추적이 가능하도록 합니다.

```bash
# 협업의 쿼리 로그 상태 확인
aws cleanrooms get-collaboration \
  --collaboration-identifier collab-abc123 \
  --query 'collaboration.{Name:name,QueryLogStatus:queryLogStatus}'
```

5. **정기적인 분석 규칙 검토**: 비즈니스 요구사항의 변화에 따라 분석 규칙을 정기적으로 검토하고 업데이트합니다.

6. **IAM 정책 세분화**: Clean Rooms API에 대한 IAM 정책을 세밀하게 설정하여, 인증된 사용자만 협업에 참여하고 쿼리를 실행할 수 있도록 합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cleanrooms:StartProtectedQuery",
        "cleanrooms:GetProtectedQuery",
        "cleanrooms:ListProtectedQueries"
      ],
      "Resource": "arn:aws:cleanrooms:ap-northeast-2:123456789012:membership/membership-xyz789"
    },
    {
      "Effect": "Deny",
      "Action": [
        "cleanrooms:DeleteCollaboration",
        "cleanrooms:DeleteConfiguredTable"
      ],
      "Resource": "*"
    }
  ]
}
```

### 운영 모범 사례

1. **결과 S3 버킷 관리**: 쿼리 결과가 저장되는 S3 버킷에 적절한 수명 주기 정책을 설정하여 비용을 관리합니다.
2. **비용 모니터링**: Clean Rooms의 쿼리 실행 비용을 AWS Cost Explorer를 통해 모니터링합니다.
3. **데이터 품질 관리**: 조인 키(해시된 이메일 등)의 형식을 멤버 간에 사전에 합의하여 매칭률을 높입니다.

## 관련 서비스 비교

| 항목 | AWS Clean Rooms | AWS Data Exchange | Amazon Redshift Data Sharing | AWS Lake Formation |
|------|----------------|-------------------|-----------------------------|-----------------------|
| 목적 | 프라이버시 보호 공동 분석 | 데이터 거래/공유 | 클러스터 간 데이터 공유 | 데이터 레이크 거버넌스 |
| 데이터 이동 | 없음 | 구독 기반 전달 | 없음 (라이브 공유) | 없음 |
| 프라이버시 보호 | 분석 규칙 + 암호화 컴퓨팅 | 없음 (원본 공유) | 없음 | 접근 제어 수준 |
| 대상 | 기업 간 협업 | 데이터 제공자/소비자 | Redshift 사용자 | 조직 내 데이터 팀 |
| 비용 모델 | 쿼리 기반 | 구독 기반 | Redshift 비용에 포함 | Lake Formation 비용 |

## 요약

AWS Clean Rooms는 데이터 프라이버시를 보장하면서 기업 간 데이터 협업을 가능하게 하는 혁신적인 서비스입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **데이터 이동 없는 협업**: 원본 데이터를 복사하거나 이동하지 않고 각자의 AWS 환경에서 공동 분석을 수행합니다.
- **세밀한 분석 규칙**: AGGREGATION, LIST, CUSTOM 규칙을 통해 허용되는 쿼리와 결과 형태를 정밀하게 제어합니다.
- **출력 제약**: 최소 집계 크기 제약으로 개인 식별 위험을 줄입니다.
- **암호화 컴퓨팅**: 데이터를 암호화한 상태에서 연산을 수행하여 최고 수준의 프라이버시를 보장합니다.
- **Clean Rooms ML**: 유사 고객 모델링 등 ML 기반 협업 분석을 지원합니다.
- **감사 추적**: CloudTrail 연동으로 모든 쿼리 실행 이력을 추적할 수 있습니다.

광고 효과 측정, 금융 사기 탐지, 헬스케어 공동 연구 등 데이터 프라이버시가 중요한 협업 시나리오에서 Clean Rooms는 매우 효과적인 솔루션입니다.