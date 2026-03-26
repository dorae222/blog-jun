## 개요

Amazon Personalize는 Amazon.com에서 20년 이상 발전시켜 온 추천 기술을 기반으로, 개인화된 추천 시스템을 완전 관리형으로 구축할 수 있는 ML 서비스입니다. 추천 시스템 알고리즘에 대한 전문 지식 없이도, 사용자 행동 데이터를 제공하면 자동으로 최적의 모델을 학습하고 실시간 추천을 제공합니다.

추천 시스템은 이커머스, 미디어 스트리밍, 뉴스, 광고 등 다양한 도메인에서 비즈니스 성과를 직접적으로 향상시키는 핵심 기술입니다. 하지만 자체적으로 추천 시스템을 구축하려면 데이터 엔지니어링, ML 모델 개발, A/B 테스트 인프라, 실시간 서빙 시스템 등 광범위한 기술 스택이 필요합니다.

Amazon Personalize는 이러한 복잡성을 추상화하여 다음과 같은 가치를 제공합니다.

- **자동 모델 선택**: 데이터 특성에 맞는 최적의 추천 알고리즘을 자동으로 선택하고 튜닝합니다.
- **실시간 개인화**: 사용자의 최신 행동을 실시간으로 반영하여 추천을 업데이트합니다.
- **콜드 스타트 처리**: 신규 사용자나 신규 아이템에 대해서도 적절한 추천을 제공합니다.
- **비즈니스 규칙 통합**: 프로모션, 필터링 등 비즈니스 로직을 추천 결과에 반영할 수 있습니다.

---

## 핵심 기능

### 1. 데이터셋 구성

Amazon Personalize는 세 가지 유형의 데이터셋을 사용합니다.

- **Interactions**: 사용자-아이템 상호작용 데이터 (필수)
- **Items**: 아이템 메타데이터 (선택)
- **Users**: 사용자 속성 데이터 (선택)

```bash
# Dataset Group 생성
aws personalize create-dataset-group \
  --name "ecommerce-recommendations" \
  --region us-east-1

# Interactions 스키마 생성
aws personalize create-schema \
  --name "ecommerce-interactions-schema" \
  --schema '{
    "type": "record",
    "name": "Interactions",
    "namespace": "com.amazonaws.personalize.schema",
    "fields": [
      {"name": "USER_ID", "type": "string"},
      {"name": "ITEM_ID", "type": "string"},
      {"name": "EVENT_TYPE", "type": "string"},
      {"name": "EVENT_VALUE", "type": ["float", "null"]},
      {"name": "TIMESTAMP", "type": "long"}
    ],
    "version": "1.0"
  }' \
  --region us-east-1

# Items 스키마 생성
aws personalize create-schema \
  --name "ecommerce-items-schema" \
  --schema '{
    "type": "record",
    "name": "Items",
    "namespace": "com.amazonaws.personalize.schema",
    "fields": [
      {"name": "ITEM_ID", "type": "string"},
      {"name": "CATEGORY", "type": ["string", "null"], "categorical": true},
      {"name": "PRICE", "type": ["float", "null"]},
      {"name": "CREATION_TIMESTAMP", "type": "long"}
    ],
    "version": "1.0"
  }' \
  --region us-east-1
```

```bash
# Dataset 생성
aws personalize create-dataset \
  --name "interactions-dataset" \
  --dataset-group-arn "arn:aws:personalize:us-east-1:123456789012:dataset-group/ecommerce-recommendations" \
  --dataset-type Interactions \
  --schema-arn "arn:aws:personalize:us-east-1:123456789012:schema/ecommerce-interactions-schema" \
  --region us-east-1

# 데이터 임포트 작업 시작
aws personalize create-dataset-import-job \
  --job-name "import-interactions-20240101" \
  --dataset-arn "arn:aws:personalize:us-east-1:123456789012:dataset-group/ecommerce-recommendations/dataset/INTERACTIONS" \
  --data-source '{"dataLocation": "s3://my-personalize-data/interactions/"}' \
  --role-arn "arn:aws:iam::123456789012:role/PersonalizeDataAccessRole" \
  --region us-east-1
```

### 2. 솔루션 (Solution) 생성 - 모델 학습

Amazon Personalize는 다양한 레시피(알고리즘)를 제공합니다.

| 레시피 | 유형 | 설명 |
|--------|------|------|
| User-Personalization-v2 | USER_PERSONALIZATION | 사용자별 개인화 추천 |
| Popularity-Count | USER_PERSONALIZATION | 인기도 기반 추천 (베이스라인) |
| Similar-Items | RELATED_ITEMS | 유사 아이템 추천 |
| Personalized-Ranking | PERSONALIZED_RANKING | 개인화된 아이템 랭킹 |
| Trending-Now | USER_SEGMENTATION | 현재 트렌딩 아이템 |

```bash
# 솔루션 생성 (모델 학습)
aws personalize create-solution \
  --name "user-personalization-solution" \
  --dataset-group-arn "arn:aws:personalize:us-east-1:123456789012:dataset-group/ecommerce-recommendations" \
  --recipe-arn "arn:aws:personalize:::recipe/aws-user-personalization-v2" \
  --solution-config '{
    "eventValueThreshold": "0.5",
    "hpoConfig": {
      "hpoObjective": {
        "type": "MAXIMIZE",
        "metricName": "precision_at_25"
      }
    }
  }' \
  --region us-east-1

# 솔루션 버전 생성 (실제 학습 시작)
aws personalize create-solution-version \
  --solution-arn "arn:aws:personalize:us-east-1:123456789012:solution/user-personalization-solution" \
  --training-mode FULL \
  --region us-east-1

# 학습 상태 확인
aws personalize describe-solution-version \
  --solution-version-arn "arn:aws:personalize:us-east-1:123456789012:solution/user-personalization-solution/version/abc123" \
  --region us-east-1
```

### 3. 캠페인 (Campaign) 배포

학습된 모델을 실시간 추론 엔드포인트로 배포합니다.

```bash
# 캠페인 생성 (실시간 추론 엔드포인트)
aws personalize create-campaign \
  --name "user-personalization-campaign" \
  --solution-version-arn "arn:aws:personalize:us-east-1:123456789012:solution/user-personalization-solution/version/abc123" \
  --min-provisioned-tps 10 \
  --campaign-config '{
    "enableMetadataWithRecommendations": true
  }' \
  --region us-east-1
```

### 4. 실시간 추천 요청

```bash
# 사용자별 개인화 추천 요청
aws personalize-runtime get-recommendations \
  --campaign-arn "arn:aws:personalize:us-east-1:123456789012:campaign/user-personalization-campaign" \
  --user-id "user-001" \
  --num-results 10 \
  --region us-east-1
```

```python
import boto3

personalize_runtime = boto3.client('personalize-runtime', region_name='us-east-1')

# 사용자별 개인화 추천
response = personalize_runtime.get_recommendations(
    campaignArn='arn:aws:personalize:us-east-1:123456789012:campaign/user-personalization-campaign',
    userId='user-001',
    numResults=10,
    filterArn='arn:aws:personalize:us-east-1:123456789012:filter/exclude-purchased'
)

for item in response['itemList']:
    print(f"추천 아이템: {item['itemId']} (점수: {item.get('score', 'N/A')})")

# 유사 아이템 추천
response = personalize_runtime.get_recommendations(
    campaignArn='arn:aws:personalize:us-east-1:123456789012:campaign/similar-items-campaign',
    itemId='item-123',
    numResults=10
)

# 개인화 랭킹
response = personalize_runtime.get_personalized_ranking(
    campaignArn='arn:aws:personalize:us-east-1:123456789012:campaign/ranking-campaign',
    userId='user-001',
    inputList=['item-001', 'item-002', 'item-003', 'item-004', 'item-005']
)
```

### 5. 실시간 이벤트 트래킹

사용자의 실시간 행동을 추적하여 추천을 즉시 업데이트합니다.

```bash
# 이벤트 트래커 생성
aws personalize create-event-tracker \
  --name "user-behavior-tracker" \
  --dataset-group-arn "arn:aws:personalize:us-east-1:123456789012:dataset-group/ecommerce-recommendations" \
  --region us-east-1
```

```python
import boto3
import json
import time

personalize_events = boto3.client('personalize-events', region_name='us-east-1')

# 실시간 이벤트 전송
personalize_events.put_events(
    trackingId='tracking-id-abc123',
    userId='user-001',
    sessionId='session-xyz',
    eventList=[
        {
            'sentAt': int(time.time()),
            'eventType': 'click',
            'eventValue': 1.0,
            'itemId': 'item-456',
            'properties': json.dumps({
                'category': 'electronics',
                'price': 299000
            })
        }
    ]
)
```

### 6. 필터 (Filter)

비즈니스 규칙에 따라 추천 결과를 필터링합니다.

```bash
# 이미 구매한 아이템 제외 필터
aws personalize create-filter \
  --name "exclude-purchased" \
  --dataset-group-arn "arn:aws:personalize:us-east-1:123456789012:dataset-group/ecommerce-recommendations" \
  --filter-expression 'EXCLUDE itemId WHERE INTERACTIONS.event_type IN ("purchase")' \
  --region us-east-1

# 특정 카테고리만 포함하는 필터
aws personalize create-filter \
  --name "electronics-only" \
  --dataset-group-arn "arn:aws:personalize:us-east-1:123456789012:dataset-group/ecommerce-recommendations" \
  --filter-expression 'INCLUDE itemId WHERE Items.CATEGORY IN ("electronics", "gadgets")' \
  --region us-east-1

# 동적 파라미터를 사용하는 필터
aws personalize create-filter \
  --name "price-range-filter" \
  --dataset-group-arn "arn:aws:personalize:us-east-1:123456789012:dataset-group/ecommerce-recommendations" \
  --filter-expression 'INCLUDE itemId WHERE Items.PRICE >= $MIN_PRICE AND Items.PRICE <= $MAX_PRICE' \
  --region us-east-1
```

---

## 아키텍처/동작 원리

### Amazon Personalize 전체 아키텍처

```
[데이터 수집]
  +--- S3 (배치 데이터) -------+
  +--- Event Tracker (실시간) --+---> [Dataset Group]
                                         |
                                         v
                                  [Solution 학습]
                                  (자동 알고리즘 선택)
                                  (HPO 하이퍼파라미터 최적화)
                                         |
                                         v
                                  [Solution Version]
                                  (학습된 모델)
                                         |
                                         v
                                  [Campaign 배포]
                                  (실시간 추론 엔드포인트)
                                         |
                          +--------------+---------------+
                          |              |               |
                          v              v               v
                  [개인화 추천]   [유사 아이템]    [개인화 랭킹]
                          |              |               |
                          +---------+----+------+--------+
                                    |           |
                                    v           v
                              [Filter 적용] [프로모션 적용]
                                    |
                                    v
                             [최종 추천 결과]
```

### 모델 학습 및 업데이트 전략

```
[초기 FULL 학습] ------> [배포]
                            |
                            v
[실시간 이벤트] -----> [모델이 실시간 행동 반영]
                            |
                            v (주기적)
[UPDATE 학습] -------> [새 데이터로 모델 증분 학습]
                            |
                            v (월 단위)
[FULL 재학습] -------> [전체 데이터로 모델 재학습]
```

- **FULL 학습**: 전체 데이터로 모델을 처음부터 학습합니다. 초기 배포 시 또는 월 단위로 수행합니다.
- **UPDATE 학습**: 기존 모델에 새로운 데이터를 반영합니다. 주간 단위로 수행하여 모델을 최신 상태로 유지합니다.
- **실시간 반영**: Event Tracker를 통해 수집된 실시간 행동은 학습 없이도 추천에 즉시 반영됩니다.

---

## 실전 활용

### 사례 1: 이커머스 추천 시스템 전체 구축

```python
import boto3
import time

def build_recommendation_system():
    personalize = boto3.client('personalize', region_name='us-east-1')
    
    # 1. Dataset Group 생성
    dsg = personalize.create_dataset_group(name='ecommerce-reco')
    dsg_arn = dsg['datasetGroupArn']
    
    # Dataset Group이 활성화될 때까지 대기
    while True:
        status = personalize.describe_dataset_group(
            datasetGroupArn=dsg_arn
        )['datasetGroup']['status']
        if status == 'ACTIVE':
            break
        time.sleep(30)
    
    # 2. 스키마 생성
    schema_arn = personalize.create_schema(
        name='interactions-schema',
        schema='''{
            "type": "record",
            "name": "Interactions",
            "namespace": "com.amazonaws.personalize.schema",
            "fields": [
                {"name": "USER_ID", "type": "string"},
                {"name": "ITEM_ID", "type": "string"},
                {"name": "EVENT_TYPE", "type": "string"},
                {"name": "TIMESTAMP", "type": "long"}
            ],
            "version": "1.0"
        }'''
    )['schemaArn']
    
    # 3. Dataset 생성
    dataset_arn = personalize.create_dataset(
        name='interactions',
        datasetGroupArn=dsg_arn,
        datasetType='Interactions',
        schemaArn=schema_arn
    )['datasetArn']
    
    # 4. 데이터 임포트
    import_job = personalize.create_dataset_import_job(
        jobName='initial-import',
        datasetArn=dataset_arn,
        dataSource={'dataLocation': 's3://my-data/interactions.csv'},
        roleArn='arn:aws:iam::123456789012:role/PersonalizeRole'
    )
    
    # 5. 솔루션 생성 및 학습 시작
    solution_arn = personalize.create_solution(
        name='user-personalization',
        datasetGroupArn=dsg_arn,
        recipeArn='arn:aws:personalize:::recipe/aws-user-personalization-v2'
    )['solutionArn']
    
    solution_version_arn = personalize.create_solution_version(
        solutionArn=solution_arn,
        trainingMode='FULL'
    )['solutionVersionArn']
    
    # 6. 캠페인 배포
    campaign_arn = personalize.create_campaign(
        name='main-campaign',
        solutionVersionArn=solution_version_arn,
        minProvisionedTPS=10
    )['campaignArn']
    
    return campaign_arn
```

### 사례 2: 프로모션 적용

```python
import boto3

personalize_runtime = boto3.client('personalize-runtime', region_name='us-east-1')

# 프로모션이 적용된 추천 (특정 아이템을 상위에 포함)
response = personalize_runtime.get_recommendations(
    campaignArn='arn:aws:personalize:us-east-1:123456789012:campaign/main-campaign',
    userId='user-001',
    numResults=10,
    promotions=[
        {
            'name': 'summer-sale',
            'percentPromotedItems': 30,  # 전체 결과의 30%를 프로모션 아이템으로
            'filterArn': 'arn:aws:personalize:us-east-1:123456789012:filter/summer-sale-items'
        }
    ]
)
```

---

## 모범 사례/보안

### 데이터 준비 모범 사례

- Interactions 데이터는 최소 1,000명의 사용자와 1,000개의 고유 아이템, 50,000개 이상의 상호작용 레코드를 준비합니다.
- 이벤트 유형에 가중치(EVENT_VALUE)를 부여하여 구매 > 장바구니 담기 > 조회 순으로 중요도를 반영합니다.
- 데이터는 최소 3개월 이상의 기간을 포함해야 합니다.
- 봇 트래픽, 테스트 데이터 등 노이즈를 사전에 제거합니다.

### 보안 설정

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "personalize:GetRecommendations",
        "personalize:GetPersonalizedRanking"
      ],
      "Resource": "arn:aws:personalize:us-east-1:123456789012:campaign/*"
    },
    {
      "Effect": "Allow",
      "Action": "personalize:PutEvents",
      "Resource": "arn:aws:personalize:us-east-1:123456789012:event-tracker/*"
    }
  ]
}
```

### 비용 최적화

- 캠페인의 minProvisionedTPS를 실제 트래픽에 맞게 설정합니다. 오버프로비저닝은 비용 낭비입니다.
- Auto Scaling을 활성화하여 트래픽 변동에 대응합니다.
- 사용하지 않는 캠페인과 솔루션 버전은 즉시 삭제합니다.
- UPDATE 학습을 활용하여 FULL 학습 빈도를 줄입니다.

```bash
# 캠페인 Auto Scaling 설정
aws application-autoscaling register-scalable-target \
  --service-namespace personalize \
  --resource-id "campaign/arn:aws:personalize:us-east-1:123456789012:campaign/main-campaign" \
  --scalable-dimension "personalize:campaign:DesiredProvisionedTPS" \
  --min-capacity 5 \
  --max-capacity 100 \
  --region us-east-1
```

---

## 관련 서비스 비교

| 항목 | Amazon Personalize | 자체 구축 (SageMaker) | Google Recommendations AI | 오픈소스 (Surprise/LightFM) |
|------|--------------------|-----------------------|---------------------------|-----------------------------|
| 관리 수준 | 완전 관리형 | 반관리형 | 완전 관리형 | 자체 관리 |
| 알고리즘 선택 | 자동 | 수동 | 자동 | 수동 |
| 실시간 반영 | 네이티브 지원 | 직접 구현 | 지원 | 직접 구현 |
| 콜드 스타트 | 자동 처리 | 직접 구현 | 자동 처리 | 직접 구현 |
| 필터/프로모션 | 내장 | 직접 구현 | 제한적 | 직접 구현 |
| 시작 난이도 | 낮음 | 높음 | 낮음 | 중간 |
| 커스터마이징 | 제한적 | 완전 자유 | 제한적 | 완전 자유 |
| 비용 | 데이터량+TPS 기반 | 인스턴스 기반 | 예측 요청 기반 | 인프라 비용만 |

---

## 요약

Amazon Personalize는 Amazon.com의 추천 기술을 기반으로 한 완전 관리형 개인화 추천 서비스입니다. 주요 특징을 정리하면 다음과 같습니다.

- Interactions, Items, Users 데이터셋을 기반으로 자동 알고리즘 선택과 하이퍼파라미터 최적화를 수행합니다.
- User-Personalization, Similar-Items, Personalized-Ranking 등 다양한 추천 유형을 지원합니다.
- Event Tracker를 통해 실시간 사용자 행동을 추적하고, 학습 없이도 즉시 추천에 반영합니다.
- Filter와 Promotions 기능으로 비즈니스 규칙을 추천 결과에 통합할 수 있습니다.
- 콜드 스타트 문제를 자동으로 처리하여, 신규 사용자와 신규 아이템에 대해서도 적절한 추천을 제공합니다.
- FULL/UPDATE 학습 모드와 Auto Scaling을 통해 비용 효율적인 운영이 가능합니다.

Amazon Personalize는 추천 시스템의 ML 복잡성을 추상화하여, 비즈니스 팀이 데이터만 준비하면 빠르게 프로덕션급 추천 시스템을 구축할 수 있게 해줍니다.