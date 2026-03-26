# Amazon SageMaker 모델 카드 소개: 왜 모델 문서화가 필요한가

## 개요

"이 모델은 누가 만들었나요?" "어떤 데이터로 훈련했나요?" "성능은 어느 정도인가요?" "어떤 제한사항이 있나요?"

ML 모델을 운영하다 보면 이런 질문이 끊임없이 발생합니다. 모델을 만든 사람이 이직하거나, 다른 팀에서 모델을 재사용하려고 하거나, 감사 기관에서 모델의 공정성을 검증하려고 할 때 이 질문들에 대한 답을 찾기 어려운 경우가 많습니다. 코드에 주석을 다는 것처럼, ML 모델에도 체계적인 문서화가 필요합니다.

**Model Cards**는 2019년 Google 연구팀이 발표한 논문 "Model Cards for Model Reporting"에서 제안된 개념입니다. 모델의 성능 특성, 의도된 용도, 한계점, 윤리적 고려사항을 구조화된 문서로 작성하여, 모델의 투명성과 책임 있는 AI 사용을 촉진하는 것이 목적입니다.

Amazon SageMaker Model Cards는 이 개념을 AWS 클라우드 환경에서 실제로 구현한 서비스입니다. 이 글에서는 Model Cards가 왜 필요한지부터 시작하여, SageMaker에서 어떻게 활용하는지를 소개하며, 조직 내 첫 도입을 위한 실용적인 가이드를 제공합니다.

## 핵심 기능

### 모델 문서화가 필요한 이유

모델 문서화가 없을 때 발생하는 대표적인 문제들은 다음과 같습니다.

| 문제 상황 | 설명 | 영향 |
|-----------|------|------|
| 지식 손실 | 모델 개발자 이직/전환 시 모델 정보 유실 | 유지보수 불가, 재개발 비용 발생 |
| 오용 위험 | 모델의 적용 범위를 모르고 부적합한 곳에 사용 | 잘못된 의사결정, 사고 발생 |
| 규제 미준수 | AI 규제(EU AI Act 등) 요구사항 미충족 | 법적 제재, 벌금 |
| 편향 방치 | 모델의 편향이 문서화되지 않아 인지하지 못함 | 특정 그룹에 불공정한 결과 |
| 재현 불가능 | 훈련 조건이 기록되지 않아 동일 결과 재현 불가 | 디버깅 곤란, 신뢰 저하 |

### SageMaker Model Cards의 핵심 개념

SageMaker Model Cards는 다음 다섯 가지 핵심 섹션으로 모델 정보를 구조화합니다.

**1. Model Overview (모델 개요)**

모델의 기본 정보를 담습니다. 이름, 설명, 버전, 제작자, 알고리즘 유형, 모델 아티팩트 위치 등이 포함됩니다. 프로젝트에 참여하지 않은 사람도 이 섹션만 읽으면 모델의 전체 윤곽을 파악할 수 있어야 합니다.

**2. Intended Uses (의도된 용도)**

가장 중요한 섹션입니다. 모델이 어떤 상황에서 사용되어야 하는지, 그리고 어떤 상황에서는 사용되면 안 되는지를 명시합니다. 위험 등급(Risk Rating)과 그 근거도 함께 기록합니다.

**3. Training Details (훈련 상세)**

훈련 데이터, 알고리즘, 하이퍼파라미터, 훈련 환경 등 모델 재현에 필요한 정보를 담습니다.

**4. Evaluation Details (평가 상세)**

평가 데이터셋, 평가 지표, 성능 결과를 기록합니다. 가능하면 하위 그룹별 성능 차이도 포함합니다.

**5. Additional Information (추가 정보)**

윤리적 고려사항, 데이터 보관 정책, 모델 재훈련 주기 등 사용자 정의 정보를 자유롭게 기록합니다.

### 첫 번째 모델 카드 만들기

```bash
# 가장 간단한 형태의 모델 카드 생성
aws sagemaker create-model-card \
  --model-card-name "my-first-model-card" \
  --model-card-status "Draft" \
  --content '{
    "model_overview": {
      "model_description": "고객 이탈 예측을 위한 로지스틱 회귀 모델입니다. 고객의 최근 3개월 활동 데이터를 기반으로 향후 30일 이내 이탈 확률을 예측합니다.",
      "model_creator": "Data Science Team",
      "algorithm_type": "Logistic Regression",
      "problem_type": "Binary Classification"
    },
    "intended_uses": {
      "purpose_of_model": "마케팅 팀이 이탈 위험 고객을 식별하여 선제적 리텐션 캠페인을 실행하기 위한 모델입니다.",
      "intended_uses": "고객 CRM 시스템에서 일일 배치로 실행되어 이탈 확률 상위 10% 고객 리스트를 생성합니다.",
      "factors_affecting_model_efficiency": "신규 가입 30일 미만 고객은 활동 데이터가 부족하여 예측 정확도가 낮습니다.",
      "risk_rating": "Low",
      "explanations_for_risk_rating": "마케팅 캠페인 대상 선정에만 사용되며, 고객에게 직접적인 불이익을 주는 의사결정에는 사용되지 않습니다."
    },
    "evaluation_details": [
      {
        "name": "2024 Q1 평가",
        "evaluation_observation": "2024년 1분기 실제 이탈 데이터와 예측 결과를 비교한 평가입니다.",
        "metric_groups": [
          {
            "name": "Performance Metrics",
            "metric_data": [
              {"name": "AUC-ROC", "type": "number", "value": 0.82},
              {"name": "Precision@10%", "type": "number", "value": 0.45},
              {"name": "Recall@10%", "type": "number", "value": 0.31}
            ]
          }
        ]
      }
    ]
  }' \
  --region ap-northeast-2
```

### 모델 카드 조회 및 수정

```bash
# 모델 카드 상세 조회
aws sagemaker describe-model-card \
  --model-card-name "my-first-model-card" \
  --region ap-northeast-2

# 모델 카드 업데이트 - 평가 결과 추가
aws sagemaker update-model-card \
  --model-card-name "my-first-model-card" \
  --content '{
    "model_overview": {
      "model_description": "고객 이탈 예측을 위한 로지스틱 회귀 모델입니다. 고객의 최근 3개월 활동 데이터를 기반으로 향후 30일 이내 이탈 확률을 예측합니다.",
      "model_creator": "Data Science Team",
      "algorithm_type": "Logistic Regression",
      "problem_type": "Binary Classification"
    },
    "intended_uses": {
      "purpose_of_model": "마케팅 팀이 이탈 위험 고객을 식별하여 선제적 리텐션 캠페인을 실행하기 위한 모델입니다.",
      "intended_uses": "고객 CRM 시스템에서 일일 배치로 실행되어 이탈 확률 상위 10% 고객 리스트를 생성합니다.",
      "factors_affecting_model_efficiency": "신규 가입 30일 미만 고객은 활동 데이터가 부족하여 예측 정확도가 낮습니다.",
      "risk_rating": "Low",
      "explanations_for_risk_rating": "마케팅 캠페인 대상 선정에만 사용되며, 고객에게 직접적인 불이익을 주는 의사결정에는 사용되지 않습니다."
    },
    "evaluation_details": [
      {
        "name": "2024 Q1 평가",
        "evaluation_observation": "2024년 1분기 실제 이탈 데이터와 예측 결과를 비교한 평가입니다.",
        "metric_groups": [
          {
            "name": "Performance Metrics",
            "metric_data": [
              {"name": "AUC-ROC", "type": "number", "value": 0.82},
              {"name": "Precision@10%", "type": "number", "value": 0.45},
              {"name": "Recall@10%", "type": "number", "value": 0.31}
            ]
          }
        ]
      },
      {
        "name": "2024 Q2 평가",
        "evaluation_observation": "2024년 2분기 데이터로 재평가하였습니다. 성능이 소폭 하락하여 재훈련이 필요합니다.",
        "metric_groups": [
          {
            "name": "Performance Metrics",
            "metric_data": [
              {"name": "AUC-ROC", "type": "number", "value": 0.78},
              {"name": "Precision@10%", "type": "number", "value": 0.39},
              {"name": "Recall@10%", "type": "number", "value": 0.27}
            ]
          }
        ]
      }
    ],
    "additional_information": {
      "custom_details": {
        "retrain_trigger": "AUC-ROC가 0.75 이하로 하락하면 재훈련을 실행합니다.",
        "data_source": "내부 CRM 데이터베이스 (MySQL)"
      }
    }
  }' \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### Google Model Cards 논문 vs AWS 구현

```
[Google Model Cards 논문 (2019)]
- 개념적 프레임워크 제시
- 구조화된 문서 템플릿
- 사람이 수동으로 작성
- 저장/배포 방법은 정의하지 않음

            |
            v

[AWS SageMaker Model Cards]
- 논문의 개념을 API/서비스로 구현
- JSON 기반 구조화 스키마
- SageMaker 에코시스템과 자동 연동
- 상태 관리 (Draft/Review/Approved)
- 버전 관리 자동화
- PDF 내보내기
- KMS 암호화
- IAM 접근 제어
```

Google의 논문이 "무엇을 문서화해야 하는가"를 정의했다면, AWS의 구현은 "어떻게 자동화하고 관리할 것인가"에 초점을 맞추고 있습니다.

### Model Card 라이프사이클

모델 카드는 모델의 전체 라이프사이클을 따라 함께 진화합니다.

```
[모델 개발 단계]
1. 훈련 시작 --> Model Card Draft 자동 생성
2. 훈련 완료 --> Training Details 자동 기록
3. 평가 완료 --> Evaluation Details 자동 기록

[모델 검토 단계]
4. Intended Uses / Risk Rating 수동 작성
5. 상태를 PendingReview로 변경
6. 리뷰어가 검토 후 Approved 또는 반려

[모델 운영 단계]
7. 주기적 재평가 결과를 Evaluation에 추가
8. 모델 드리프트 감지 시 추가 정보 업데이트
9. 모델 폐기 시 상태를 Archived로 변경
```

### 저장 및 버전 관리

Model Card를 업데이트할 때마다 자동으로 새 버전이 생성됩니다. 이전 버전은 삭제되지 않으며, 특정 시점의 모델 카드 상태를 조회할 수 있습니다.

```bash
# 모델 카드의 모든 버전 목록 조회
aws sagemaker list-model-card-versions \
  --model-card-name "my-first-model-card" \
  --region ap-northeast-2

# 특정 버전의 모델 카드 조회
aws sagemaker describe-model-card \
  --model-card-name "my-first-model-card" \
  --model-card-version 1 \
  --region ap-northeast-2
```

## 실전 활용

### 1. 팀 도입을 위한 최소 템플릿

처음 Model Cards를 도입할 때는 모든 섹션을 완벽하게 채우려고 하기보다, 핵심 정보부터 시작하는 것이 좋습니다.

```python
import boto3
import json

sm = boto3.client('sagemaker', region_name='ap-northeast-2')

def create_minimal_model_card(name, description, purpose, risk_level, metrics):
    """최소한의 정보로 모델 카드를 생성하는 헬퍼 함수"""
    content = {
        'model_overview': {
            'model_description': description,
            'model_creator': 'ML Team'
        },
        'intended_uses': {
            'purpose_of_model': purpose,
            'risk_rating': risk_level
        },
        'evaluation_details': [{
            'name': 'Initial Evaluation',
            'metric_groups': [{
                'name': 'Key Metrics',
                'metric_data': [
                    {'name': k, 'type': 'number', 'value': v}
                    for k, v in metrics.items()
                ]
            }]
        }]
    }

    response = sm.create_model_card(
        ModelCardName=name,
        ModelCardStatus='Draft',
        Content=json.dumps(content)
    )
    print(f"Model Card 생성: {name}")
    return response

# 사용 예시
create_minimal_model_card(
    name='churn-prediction-v1',
    description='고객 이탈 예측 로지스틱 회귀 모델',
    purpose='마케팅 팀의 리텐션 캠페인 대상 선정',
    risk_level='Low',
    metrics={'AUC-ROC': 0.82, 'Precision': 0.75, 'Recall': 0.68}
)
```

### 2. 기존 모델 인벤토리화

이미 운영 중인 모델들에 대해 일괄적으로 Model Card를 생성하는 스크립트입니다.

```python
def inventory_existing_models(domain_id=None):
    """기존 SageMaker 모델들의 인벤토리를 생성합니다."""
    models = sm.list_models(SortBy='CreationTime', SortOrder='Descending')

    inventory = []
    for model_summary in models['Models']:
        model_detail = sm.describe_model(ModelName=model_summary['ModelName'])
        inventory.append({
            'name': model_summary['ModelName'],
            'arn': model_summary['ModelArn'],
            'creation_time': str(model_summary['CreationTime']),
            'container': model_detail.get('PrimaryContainer', {}).get('Image', 'Unknown'),
            'model_data': model_detail.get('PrimaryContainer', {}).get('ModelDataUrl', 'Unknown')
        })
        print(f"  - {model_summary['ModelName']}")

    print(f"\n총 {len(inventory)}개 모델 발견")
    print("Model Card가 없는 모델에 대해 Draft 카드를 생성하는 것을 권장합니다.")
    return inventory
```

### 3. 정기 검토 자동화

```python
import boto3
from datetime import datetime, timedelta

def check_review_schedule():
    """분기별 검토가 필요한 모델 카드를 식별합니다."""
    sm = boto3.client('sagemaker', region_name='ap-northeast-2')
    cards = sm.list_model_cards(ModelCardStatus='Approved')

    review_needed = []
    three_months_ago = datetime.utcnow() - timedelta(days=90)

    for card_summary in cards['ModelCardSummaries']:
        card = sm.describe_model_card(
            ModelCardName=card_summary['ModelCardName']
        )
        last_modified = card['LastModifiedTime'].replace(tzinfo=None)

        if last_modified < three_months_ago:
            review_needed.append({
                'name': card_summary['ModelCardName'],
                'last_modified': str(last_modified),
                'days_since_review': (datetime.utcnow() - last_modified).days
            })

    if review_needed:
        print(f"검토가 필요한 모델 카드: {len(review_needed)}개")
        for item in review_needed:
            print(f"  - {item['name']}: {item['days_since_review']}일 전 마지막 수정")
    else:
        print("모든 모델 카드가 최신 상태입니다.")

    return review_needed
```

## 모범 사례/보안

### 도입 단계별 로드맵

**Phase 1 - 인식 (1-2주)**
- 팀 내 Model Cards 개념 공유
- 기존 모델 인벤토리 작성
- 최소 템플릿 합의

**Phase 2 - 시범 적용 (2-4주)**
- 가장 중요한 모델 3-5개에 대해 Model Card 작성
- 작성 가이드라인 초안 마련
- 검토 프로세스 시범 운영

**Phase 3 - 확대 (1-2개월)**
- 모든 운영 모델에 대해 Model Card 생성
- CI/CD 파이프라인에 Model Card 생성 자동화 통합
- 정기 검토 스케줄 수립

**Phase 4 - 성숙 (지속)**
- Model Card 품질 기준 수립
- 자동화된 드리프트 감지 -> Model Card 업데이트 연동
- 외부 감사/규제 대응 프로세스 정립

### 작성 품질 체크리스트

- [ ] model_description이 모델을 처음 보는 사람도 이해할 수 있을 만큼 명확한가?
- [ ] intended_uses에 부적합한 용도가 명시되어 있는가?
- [ ] risk_rating에 대한 근거가 explanations_for_risk_rating에 기술되어 있는가?
- [ ] evaluation_details에 최소 2개 이상의 평가 지표가 포함되어 있는가?
- [ ] 알려진 편향(Bias)이나 제한사항이 기록되어 있는가?
- [ ] 모델 재훈련 주기/조건이 명시되어 있는가?

### 접근 권한 분리

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DataScientistCanDraft",
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateModelCard",
        "sagemaker:UpdateModelCard",
        "sagemaker:DescribeModelCard"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "sagemaker:ModelCardStatus": "Draft"
        }
      }
    },
    {
      "Sid": "MLLeadCanApprove",
      "Effect": "Allow",
      "Action": "sagemaker:UpdateModelCard",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "sagemaker:ModelCardStatus": ["PendingReview", "Approved"]
        }
      }
    }
  ]
}
```

## 관련 서비스 비교

| 항목 | SageMaker Model Cards | Hugging Face Model Cards | Google Model Cards (개념) | MLflow Tags/Description |
|------|----------------------|--------------------------|---------------------------|------------------------|
| 형태 | AWS 관리형 서비스 (API) | Markdown 파일 (README.md) | 논문에서 제안한 프레임워크 | 자유 형식 메타데이터 |
| 구조화 수준 | JSON 스키마 기반, 높음 | Markdown 기반, 중간 | 섹션 가이드라인, 높음 | 키-값 태그, 낮음 |
| 상태 관리 | Draft/Review/Approved/Archived | 없음 | 정의하지 않음 | 없음 |
| 버전 관리 | 자동 | Git 기반 | 정의하지 않음 | 없음 |
| PDF 내보내기 | 지원 | 미지원 | 해당 없음 | 미지원 |
| 자동화 수준 | SageMaker 에코시스템 연동 | 수동 또는 Hub API | 해당 없음 | 수동 |
| 비용 | 무료 (SageMaker 사용 시) | 무료 | 해당 없음 | 무료 |

### SageMaker Model Cards vs Hugging Face Model Cards

Hugging Face의 Model Cards는 Markdown 기반으로 자유도가 높지만, 구조화된 관리와 상태 워크플로우가 없습니다. 오픈소스 모델 공유에는 Hugging Face 방식이, 기업 내부의 거버넌스와 규제 준수에는 SageMaker Model Cards가 더 적합합니다.

## 요약

Amazon SageMaker Model Cards는 ML 모델의 체계적인 문서화를 위한 서비스입니다. 처음 도입하는 팀을 위해 핵심 내용을 정리합니다.

- **Model Cards는 모델의 투명성과 책임 있는 AI 사용을 위해 필수적**입니다. 모델이 무엇인지, 어디에 사용해야 하는지, 어디에 사용하면 안 되는지를 명확히 문서화합니다.
- **다섯 가지 핵심 섹션**(Model Overview, Intended Uses, Training Details, Evaluation Details, Additional Information)으로 구조화되어 있으며, 최소한 Overview와 Intended Uses는 반드시 작성해야 합니다.
- **상태 관리**(Draft -> PendingReview -> Approved -> Archived)를 통해 검토/승인 워크플로우를 구현할 수 있습니다.
- **도입은 점진적으로**: 처음부터 완벽을 추구하기보다, 핵심 모델에 대한 최소 템플릿부터 시작하여 점차 범위와 깊이를 확장하는 것이 효과적입니다.
- Model Cards 작성은 기술적 작업이 아닌 **조직 문화의 변화**입니다. 경영진의 지원과 팀 내 합의가 성공적 도입의 핵심입니다.
- EU AI Act, 금융감독원 AI 가이드라인 등 **AI 규제가 강화**되면서, 모델 문서화는 선택이 아닌 필수가 되어가고 있습니다.