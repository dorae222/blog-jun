<!-- infographic-hero -->
![AWS Data Exchange 개요 및 활용 핵심 요약](figures/infographic.svg)

*Figure: AWS Data Exchange 개요 및 활용 한 장 요약 인포그래픽*

# AWS Data Exchange 개요 및 활용

## 개요

AWS Data Exchange는 AWS Marketplace를 통해 서드파티 데이터를 안전하게 검색, 구독, 사용할 수 있는 관리형 서비스입니다. 데이터 제공자(Provider)는 자신의 데이터 제품을 등록하여 판매하고, 데이터 소비자(Subscriber)는 필요한 데이터를 구독하여 자신의 AWS 환경에서 바로 활용할 수 있습니다.

전통적으로 서드파티 데이터를 확보하기 위해서는 복잡한 라이선스 계약, 수동 데이터 전송, 형식 변환 등의 과정이 필요했습니다. AWS Data Exchange는 이러한 과정을 자동화하고 표준화하여, 데이터 확보에 소요되는 시간과 비용을 크게 줄여줍니다.

주요 특징은 다음과 같습니다.

- **AWS Marketplace 통합**: AWS Marketplace의 과금 및 라이선스 관리 인프라를 활용합니다.
- **다양한 데이터 유형**: S3 파일, API, Amazon Redshift 테이블, AWS Lake Formation 데이터 등 다양한 형태의 데이터를 지원합니다.
- **자동 업데이트**: 데이터 제공자가 데이터를 업데이트하면 구독자에게 자동으로 전달됩니다.
- **보안 및 감사**: IAM, CloudTrail, 서비스 제어 정책(SCP) 등 AWS의 보안 인프라를 활용합니다.
- **데이터 사용 추적**: 데이터 제공자는 구독자의 데이터 사용 패턴을 추적할 수 있습니다.

## 핵심 기능

### 1. 데이터 제품 유형

AWS Data Exchange는 네 가지 유형의 데이터 제품을 지원합니다.

#### S3 파일 기반

CSV, JSON, Parquet 등의 파일을 S3를 통해 제공합니다. 가장 기본적이고 널리 사용되는 유형입니다.

```bash
# Data Exchange에서 사용 가능한 데이터셋 검색
aws dataexchange list-data-sets \
  --query 'DataSets[].{Name:Name,Id:Id,Origin:OriginDetails.ProductId,Updated:UpdatedAt}' \
  --output table

# 특정 데이터셋의 리비전 목록 조회
aws dataexchange list-data-set-revisions \
  --data-set-id ds-abc123 \
  --query 'Revisions[].{Id:Id,Comment:Comment,Created:CreatedAt,Finalized:Finalized}' \
  --output table
```

#### API 기반

REST API를 통해 실시간으로 데이터를 제공합니다. 실시간 가격 데이터, 날씨 정보 등 최신 데이터가 필요한 경우에 적합합니다.

#### Amazon Redshift 기반

Redshift 데이터 공유를 통해 라이브 데이터에 직접 쿼리를 실행할 수 있습니다. 데이터를 복사하지 않고 실시간 분석이 가능합니다.

#### AWS Lake Formation 기반

Lake Formation을 통해 관리되는 데이터에 대한 세밀한 접근 제어가 가능합니다.

### 2. 데이터 구독 및 엑스포트

```bash
# 데이터셋의 특정 리비전에서 에셋 목록 조회
aws dataexchange list-revision-assets \
  --data-set-id ds-abc123 \
  --revision-id rev-def456 \
  --query 'Assets[].{Name:Name,Id:Id,Type:AssetType,Size:AssetDetails.S3SnapshotAsset.Size}' \
  --output table

# S3로 데이터 엑스포트 작업 생성
aws dataexchange create-job \
  --type EXPORT_REVISIONS_TO_S3 \
  --details '{
    "ExportRevisionsToS3": {
      "DataSetId": "ds-abc123",
      "RevisionDestinations": [{
        "RevisionId": "rev-def456",
        "Bucket": "my-data-bucket",
        "KeyPattern": "data-exchange/${Asset.Name}"
      }]
    }
  }'

# 작업 시작
aws dataexchange start-job --job-id job-ghi789

# 작업 상태 확인
aws dataexchange get-job \
  --job-id job-ghi789 \
  --query 'Job.{Type:Type,State:State,Errors:Errors}'
```

### 3. 자동 엑스포트 설정

데이터 제공자가 새로운 리비전을 게시할 때마다 자동으로 S3에 엑스포트되도록 EventBridge 규칙을 설정할 수 있습니다.

```bash
# EventBridge 규칙 생성 (새 리비전 자동 엑스포트)
aws events put-rule \
  --name "data-exchange-auto-export" \
  --event-pattern '{
    "source": ["aws.dataexchange"],
    "detail-type": ["Revision Published To Data Set"],
    "resources": ["arn:aws:dataexchange:ap-northeast-2:123456789012:data-sets/ds-abc123"]
  }'

# Lambda 타겟 설정
aws events put-targets \
  --rule "data-exchange-auto-export" \
  --targets '[{
    "Id": "auto-export-lambda",
    "Arn": "arn:aws:lambda:ap-northeast-2:123456789012:function:AutoExportDataExchange"
  }]'
```

```python
# Lambda 함수 예시: 자동 엑스포트
import boto3
import json

def lambda_handler(event, context):
    client = boto3.client('dataexchange')
    
    data_set_id = event['resources'][0].split('/')[-1]
    revision_id = event['detail']['RevisionId']
    
    # 엑스포트 작업 생성
    response = client.create_job(
        Type='EXPORT_REVISIONS_TO_S3',
        Details={
            'ExportRevisionsToS3': {
                'DataSetId': data_set_id,
                'RevisionDestinations': [{
                    'RevisionId': revision_id,
                    'Bucket': 'my-data-bucket',
                    'KeyPattern': f'data-exchange/{data_set_id}/${{Asset.Name}}'
                }]
            }
        }
    )
    
    # 작업 시작
    client.start_job(JobId=response['Id'])
    
    return {
        'statusCode': 200,
        'body': json.dumps({'jobId': response['Id']})
    }
```

### 4. 데이터 제품 게시 (제공자 관점)

데이터 제공자는 AWS Marketplace를 통해 데이터 제품을 게시하고 수익을 창출할 수 있습니다.

```bash
# 데이터셋 생성 (제공자)
aws dataexchange create-data-set \
  --asset-type S3_SNAPSHOT \
  --description "한국 시장 일별 주식 거래 데이터" \
  --name "KR Stock Market Daily Data" \
  --tags '{"Category": "Financial", "Region": "Korea"}'

# 리비전 생성
aws dataexchange create-revision \
  --data-set-id ds-provider-abc123 \
  --comment "2024년 1월 데이터 업데이트"

# S3에서 에셋 임포트
aws dataexchange create-job \
  --type IMPORT_ASSETS_FROM_S3 \
  --details '{
    "ImportAssetsFromS3": {
      "DataSetId": "ds-provider-abc123",
      "RevisionId": "rev-provider-def456",
      "AssetSources": [{
        "Bucket": "my-provider-bucket",
        "Key": "stock-data/2024-01/daily-trades.parquet"
      }]
    }
  }'

# 작업 시작
aws dataexchange start-job --job-id job-provider-ghi789

# 리비전 확정 (Finalize)
aws dataexchange update-revision \
  --data-set-id ds-provider-abc123 \
  --revision-id rev-provider-def456 \
  --finalized
```

### 5. 프라이빗 오퍼

특정 AWS 계정에게만 데이터를 제공하는 프라이빗 오퍼를 생성할 수 있습니다. 이는 비공개 비즈니스 관계에서의 데이터 거래에 유용합니다.

## 아키텍처/동작 원리

### 전체 아키텍처

```
[데이터 제공자]                              [데이터 소비자]
  |                                            |
  [S3/API/Redshift] --> [데이터셋] -->        |
                        [리비전]              |
                        [에셋]                |
                          |                   |
                     [AWS Marketplace]         |
                          |                   |
                     [구독/라이선스]  <--------+
                          |                   |
                     [자동 전달] ----------> [S3/API/Redshift]
                                              |
                                          [분석 파이프라인]
                                          (Athena, Glue,
                                           Redshift, etc.)
```

### 데이터 전달 메커니즘

#### S3 기반 전달

1. 제공자가 S3에서 에셋을 임포트하여 리비전을 생성합니다.
2. 리비전이 확정되면 구독자에게 알림이 전송됩니다.
3. 구독자가 엑스포트 작업을 실행하면 데이터가 구독자의 S3 버킷으로 복사됩니다.
4. 또는 EventBridge를 통해 자동 엑스포트를 구성할 수 있습니다.

#### API 기반 전달

1. 제공자가 API 게이트웨이를 통해 API 엔드포인트를 등록합니다.
2. 구독자가 Data Exchange를 통해 API를 호출합니다.
3. 인증 및 사용량 제한이 자동으로 관리됩니다.

#### Redshift 기반 전달

1. 제공자가 Redshift 데이터 공유를 등록합니다.
2. 구독자의 Redshift 클러스터에서 공유된 데이터에 직접 쿼리를 실행합니다.
3. 데이터 복사 없이 실시간 분석이 가능합니다.

### 과금 모델

- **구독료**: 데이터 제공자가 설정한 월간/연간 구독료를 AWS Marketplace를 통해 결제합니다.
- **AWS 수수료**: AWS는 거래 금액의 일정 비율을 수수료로 받습니다.
- **데이터 전송 비용**: S3로의 데이터 엑스포트 시 표준 S3 요금이 적용됩니다.

## 실전 활용

### 활용 사례 1: 금융 시장 데이터 분석

금융 데이터 제공업체의 시장 데이터를 구독하여 자동화된 분석 파이프라인을 구축합니다.

```bash
# Marketplace에서 금융 데이터 검색 (AWS Marketplace CLI)
aws marketplace-catalog list-entities \
  --catalog AWSMarketplace \
  --entity-type DataProduct \
  --filter-list '[{"Name":"DataSetType","Values":["S3_SNAPSHOT"]}]'

# 구독 후 데이터 엑스포트 자동화
aws dataexchange list-data-sets \
  --origin ENTITLED \
  --query 'DataSets[].{Name:Name,Id:Id,Updated:UpdatedAt}' \
  --output table
```

### 활용 사례 2: 날씨 API 데이터 연동

API 기반 날씨 데이터를 구독하여 물류/유통 예측 시스템에 통합합니다.

```bash
# API 기반 데이터셋 에셋 조회
aws dataexchange list-revision-assets \
  --data-set-id ds-weather-api \
  --revision-id rev-latest \
  --query 'Assets[?AssetType==`API_GATEWAY_API`].{Name:Name,Id:Id}'

# API 에셋에 대한 엔드포인트 정보 조회
aws dataexchange get-asset \
  --data-set-id ds-weather-api \
  --revision-id rev-latest \
  --asset-id asset-api-123 \
  --query 'AssetDetails.ApiGatewayApiAsset.{ApiEndpoint:ApiEndpoint,Stage:Stage}'
```

### 활용 사례 3: 데이터 제공자로서의 비즈니스

자체 데이터를 AWS Data Exchange를 통해 판매하는 데이터 비즈니스를 구축합니다.

```bash
# 데이터 제품의 사용량 통계 조회
aws dataexchange list-event-actions \
  --query 'EventActions[].{Id:Id,Event:Event.RevisionPublished.DataSetId,Action:Action}' \
  --output table

# 새 리비전 게시 자동화 스크립트
aws dataexchange create-revision \
  --data-set-id ds-my-product \
  --comment "$(date +%Y-%m-%d) 정기 업데이트"
```

### 활용 사례 4: Redshift를 통한 실시간 데이터 분석

Redshift 기반 데이터 제품을 구독하여 데이터 복사 없이 실시간 분석을 수행합니다.

```sql
-- Redshift에서 Data Exchange 데이터 직접 쿼리
SELECT 
    region,
    product_category,
    SUM(revenue) as total_revenue,
    COUNT(DISTINCT customer_id) as unique_customers
FROM data_exchange_schema.market_intelligence
WHERE report_date >= DATEADD(day, -30, CURRENT_DATE)
GROUP BY region, product_category
ORDER BY total_revenue DESC;
```

## 모범 사례/보안

### 데이터 소비자 모범 사례

1. **자동 엑스포트 구성**: EventBridge와 Lambda를 사용하여 새 리비전이 게시될 때 자동으로 데이터를 엑스포트합니다.
2. **데이터 품질 검증**: 수신한 데이터에 대한 자동화된 품질 검증 파이프라인을 구축합니다.
3. **비용 관리**: 구독 중인 데이터 제품의 실제 활용도를 정기적으로 평가하여 불필요한 구독을 해지합니다.
4. **접근 제어**: 수신한 데이터에 대한 접근 권한을 IAM 정책으로 엄격하게 관리합니다.

### 데이터 제공자 모범 사례

1. **정기적인 업데이트**: 일관된 스케줄로 데이터를 업데이트하여 구독자의 신뢰를 유지합니다.
2. **명확한 문서화**: 데이터 스키마, 업데이트 빈도, 데이터 품질 보증 등을 명확하게 문서화합니다.
3. **데이터 품질 관리**: 게시 전에 자동화된 데이터 품질 검증을 수행합니다.
4. **버전 관리**: 스키마 변경 시 하위 호환성을 유지하거나, 충분한 사전 공지를 합니다.

### 보안 모범 사례

1. **IAM 최소 권한**: Data Exchange API에 대한 접근을 최소 권한으로 제한합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dataexchange:ListDataSets",
        "dataexchange:ListDataSetRevisions",
        "dataexchange:ListRevisionAssets",
        "dataexchange:GetAsset",
        "dataexchange:CreateJob",
        "dataexchange:StartJob",
        "dataexchange:GetJob"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "dataexchange:JobType": "EXPORT_REVISIONS_TO_S3"
        }
      }
    }
  ]
}
```

2. **S3 버킷 정책**: 엑스포트 대상 S3 버킷에 적절한 암호화 및 접근 정책을 설정합니다.
3. **CloudTrail 감사**: Data Exchange API 호출을 CloudTrail로 기록하여 감사 추적을 유지합니다.
4. **VPC 엔드포인트**: Data Exchange API 호출을 VPC 엔드포인트를 통해 프라이빗하게 수행합니다.

## 관련 서비스 비교

| 항목 | AWS Data Exchange | AWS Clean Rooms | AWS Lake Formation | Snowflake Data Marketplace |
|------|-------------------|-----------------|-----------------------|----------------------------|
| 목적 | 데이터 거래/구독 | 프라이버시 보호 협업 | 데이터 레이크 거버넌스 | 데이터 거래/공유 |
| 데이터 이동 | 구독자에게 복사 | 없음 | 없음 | 플랫폼 내 공유 |
| 데이터 유형 | S3/API/Redshift/LF | Glue 테이블 | S3/Glue | Snowflake 테이블 |
| 과금 | Marketplace 기반 | 쿼리 기반 | Lake Formation 비용 | Marketplace 기반 |
| 프라이버시 | 원본 데이터 전달 | 분석 규칙 보호 | 접근 제어 | 원본/보호 데이터 |
| 적합한 용도 | 서드파티 데이터 확보 | 민감 데이터 협업 | 내부 데이터 관리 | Snowflake 생태계 |

## 요약

AWS Data Exchange는 서드파티 데이터의 검색, 구독, 활용을 간소화하는 관리형 데이터 마켓플레이스 서비스입니다.

핵심 포인트를 정리하면 다음과 같습니다.

- **다양한 데이터 유형**: S3 파일, API, Redshift, Lake Formation 등 다양한 형태의 데이터 제품을 지원합니다.
- **자동화된 전달**: 새 리비전이 게시되면 EventBridge를 통해 자동으로 데이터를 수신할 수 있습니다.
- **AWS Marketplace 통합**: 과금, 라이선스, 구독 관리가 AWS Marketplace를 통해 자동으로 처리됩니다.
- **양방향 비즈니스**: 데이터 소비자뿐만 아니라 데이터 제공자로서도 활용할 수 있습니다.
- **보안 및 감사**: IAM, CloudTrail, VPC 엔드포인트 등 AWS의 보안 인프라를 완전히 활용합니다.
- **분석 파이프라인 통합**: Athena, Glue, Redshift, QuickSight 등과 원활하게 연동됩니다.

외부 데이터를 분석 파이프라인에 통합해야 하는 조직에게 AWS Data Exchange는 데이터 확보 과정을 크게 간소화할 수 있는 효과적인 솔루션입니다.