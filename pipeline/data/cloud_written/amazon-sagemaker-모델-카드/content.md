<!-- infographic-hero -->
![Amazon SageMaker 모델 카드: ML 모델 거버넌스와 문서화 자동화 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker 모델 카드: ML 모델 거버넌스와 문서화 자동화 한 장 요약 인포그래픽*

# Amazon SageMaker 모델 카드: ML 모델 거버넌스와 문서화 자동화

## 개요

머신러닝 모델이 비즈니스 의사결정에 점점 더 많이 활용되면서, 모델의 투명성과 문서화에 대한 요구가 급증하고 있습니다. 모델이 어떤 데이터로 훈련되었는지, 어떤 평가 지표를 기준으로 성능을 검증했는지, 어떤 편향(Bias)이 존재하는지, 어떤 제한사항이 있는지를 체계적으로 기록하고 공유해야 합니다.

Amazon SageMaker Model Cards는 이러한 모델 문서화를 표준화하고 자동화하기 위한 서비스입니다. Google의 Model Cards 논문(2019)에서 제시한 개념을 AWS 생태계에 구현한 것으로, ML 모델의 메타데이터, 훈련 정보, 평가 결과, 의도된 용도, 제한사항 등을 구조화된 형식으로 관리할 수 있습니다.

Model Cards는 단순한 문서 작성 도구가 아닙니다. SageMaker Model Registry, SageMaker Experiments와 통합되어 모델 훈련부터 배포까지의 전체 라이프사이클에 걸친 문서를 자동으로 생성하고 관리합니다. 이를 통해 ML 거버넌스(Governance), 감사(Audit), 규제 준수(Compliance)를 효율적으로 달성할 수 있습니다.

## 핵심 기능

### 모델 카드의 구조

SageMaker Model Card는 다음과 같은 섹션으로 구성됩니다.

| 섹션 | 내용 | 필수 여부 |
|------|------|----------|
| Model Overview | 모델 이름, 설명, 버전, 소유자 | 필수 |
| Intended Uses | 의도된 용도, 부적합한 용도, 위험 등급 | 필수 |
| Training Details | 훈련 데이터셋, 알고리즘, 하이퍼파라미터 | 권장 |
| Evaluation Details | 평가 지표, 데이터셋, 결과 | 권장 |
| Additional Information | 사용자 정의 정보, 윤리적 고려사항 | 선택 |
| Business Details | 비즈니스 영향, 이해관계자 | 선택 |

### 모델 카드 생성

```bash
# AWS CLI로 모델 카드 생성
aws sagemaker create-model-card \
  --model-card-name "fraud-detection-model-v2" \
  --model-card-status "Draft" \
  --content '{
    "model_overview": {
      "model_description": "신용카드 거래 사기 탐지를 위한 XGBoost 기반 이진 분류 모델",
      "model_creator": "ML Engineering Team",
      "model_artifact": ["s3://ml-models/fraud-detection/v2/model.tar.gz"],
      "algorithm_type": "XGBoost",
      "problem_type": "Binary Classification"
    },
    "intended_uses": {
      "purpose_of_model": "실시간 신용카드 거래에서 사기 거래를 탐지하여 차단 여부를 판단하는 데 사용됩니다.",
      "intended_uses": "신용카드 결제 시스템의 실시간 사기 탐지 파이프라인에서 사용됩니다. 거래 금액, 가맹점 정보, 사용자 행동 패턴 등을 입력으로 받아 사기 확률을 출력합니다.",
      "factors_affecting_model_efficiency": "모델은 한국 신용카드 거래 데이터로 훈련되었으므로, 해외 거래 패턴에 대해서는 성능이 저하될 수 있습니다.",
      "risk_rating": "High",
      "explanations_for_risk_rating": "금융 거래에 직접적으로 영향을 미치므로 고위험으로 분류됩니다. 오탐(False Positive)은 정상 거래 차단, 미탐(False Negative)은 사기 거래 승인으로 이어집니다."
    },
    "training_details": {
      "training_observations": "2023년 1월부터 12월까지의 거래 데이터 약 500만 건을 사용하였습니다. 사기 거래 비율은 약 0.3%로 심각한 클래스 불균형이 존재하며, SMOTE 기법을 적용하여 보정하였습니다.",
      "objective_function": {
        "function": "binary:logistic",
        "notes": "로그 손실 함수를 사용하여 확률 출력을 최적화하였습니다."
      },
      "training_job_details": {
        "training_arn": "arn:aws:sagemaker:ap-northeast-2:123456789012:training-job/fraud-detection-v2-20240115",
        "training_environment": {
          "container_image": ["123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/xgboost:1.7-1"]
        },
        "hyper_parameters": [
          {"name": "max_depth", "value": "8"},
          {"name": "eta", "value": "0.1"},
          {"name": "num_round", "value": "500"},
          {"name": "scale_pos_weight", "value": "333"}
        ]
      }
    },
    "evaluation_details": [
      {
        "name": "Test Set Evaluation",
        "evaluation_observation": "2024년 1월 데이터를 테스트셋으로 사용하였습니다.",
        "datasets": ["s3://ml-data/fraud-detection/test/202401/"],
        "metric_groups": [
          {
            "name": "Classification Metrics",
            "metric_data": [
              {"name": "AUC-ROC", "type": "number", "value": 0.9823},
              {"name": "Precision", "type": "number", "value": 0.8745},
              {"name": "Recall", "type": "number", "value": 0.9156},
              {"name": "F1-Score", "type": "number", "value": 0.8946},
              {"name": "False Positive Rate", "type": "number", "value": 0.0012}
            ]
          }
        ]
      }
    ],
    "additional_information": {
      "ethical_considerations": "모델은 거래 금액과 패턴에 기반하므로, 특정 지역이나 가맹점 유형에 대한 편향이 존재할 수 있습니다. 분기별로 Bias 분석을 수행하여 공정성을 모니터링합니다.",
      "custom_details": {
        "data_retention": "모델 훈련에 사용된 원본 데이터는 금융감독원 규정에 따라 5년간 보관됩니다.",
        "model_review_schedule": "분기별 성능 재평가, 반기별 재훈련"
      }
    }
  }' \
  --security-config '{
    "KmsKeyId": "arn:aws:kms:ap-northeast-2:123456789012:key/abc-123-def-456"
  }' \
  --region ap-northeast-2
```

### 모델 카드 상태 관리

모델 카드는 라이프사이클에 따라 다음 상태를 가집니다.

```
Draft --> PendingReview --> Approved --> Archived
  |            |               |
  +---[수정]---+    [재검토]---+
```

```bash
# 모델 카드 상태를 PendingReview로 변경
aws sagemaker update-model-card \
  --model-card-name "fraud-detection-model-v2" \
  --model-card-status "PendingReview" \
  --region ap-northeast-2

# 승인 처리
aws sagemaker update-model-card \
  --model-card-name "fraud-detection-model-v2" \
  --model-card-status "Approved" \
  --region ap-northeast-2
```

### PDF 내보내기

모델 카드를 PDF로 내보내어 외부 감사관이나 규제 기관에 제출할 수 있습니다.

```bash
# PDF 내보내기 작업 시작
aws sagemaker create-model-card-export-job \
  --model-card-name "fraud-detection-model-v2" \
  --model-card-export-job-name "fraud-model-v2-export-20240115" \
  --output-config '{
    "S3OutputPath": "s3://ml-governance/model-cards/exports/"
  }' \
  --region ap-northeast-2

# 내보내기 작업 상태 확인
aws sagemaker describe-model-card-export-job \
  --model-card-export-job-arn "arn:aws:sagemaker:ap-northeast-2:123456789012:model-card/fraud-detection-model-v2/export-job/fraud-model-v2-export-20240115" \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### Model Card와 SageMaker 에코시스템 통합

```
+------------------------------------------------------------------+
|                    SageMaker ML 라이프사이클                       |
+------------------------------------------------------------------+
|                                                                  |
|  [Training]         [Registry]         [Deployment]              |
|  SageMaker          Model Package      Endpoint                  |
|  Training Job  -->  Group/Version  --> Configuration             |
|       |                  |                  |                    |
|       v                  v                  v                    |
|  +------------------------------------------------------+       |
|  |              SageMaker Model Card                     |       |
|  |                                                      |       |
|  |  - Training Details  (Training Job에서 자동 수집)      |       |
|  |  - Model Artifact    (Registry에서 참조)               |       |
|  |  - Evaluation Metrics (Experiments에서 자동 수집)       |       |
|  |  - Deployment Info   (Endpoint에서 참조)               |       |
|  |                                                      |       |
|  +------------------------------------------------------+       |
|       |                                                          |
|       v                                                          |
|  [Export]  --> PDF/HTML --> 감사/규제 기관 제출                    |
|  [Versioning] --> 변경 이력 추적                                  |
+------------------------------------------------------------------+
```

### 데이터 저장 구조

Model Card의 콘텐츠는 JSON 형식으로 저장됩니다. 내부적으로 AWS가 관리하는 스토리지에 저장되며, KMS 키를 지정하면 저장 시 암호화(Encryption at Rest)가 적용됩니다.

버전 관리는 자동으로 이루어집니다. 모델 카드를 업데이트할 때마다 새 버전이 생성되며, 이전 버전은 보존됩니다. 이를 통해 모델 카드의 변경 이력을 추적할 수 있습니다.

```bash
# 모델 카드 버전 목록 조회
aws sagemaker list-model-card-versions \
  --model-card-name "fraud-detection-model-v2" \
  --region ap-northeast-2
```

### 모델 카드 JSON 스키마

Model Card의 content 필드는 AWS가 정의한 JSON 스키마를 따릅니다. 주요 최상위 키는 다음과 같습니다.

```json
{
  "model_overview": {},
  "intended_uses": {},
  "training_details": {},
  "evaluation_details": [],
  "additional_information": {},
  "business_details": {}
}
```

각 섹션의 필드는 자유 텍스트(String)와 구조화된 데이터(Object/Array)를 조합하여 유연하게 정보를 기록할 수 있습니다.

## 실전 활용

### 1. Python SDK를 활용한 자동화된 모델 카드 생성

```python
import boto3
import json
from datetime import datetime

sm = boto3.client('sagemaker', region_name='ap-northeast-2')

def create_model_card_from_training_job(training_job_name, model_card_name):
    """훈련 작업 정보를 기반으로 모델 카드를 자동 생성합니다."""

    # 훈련 작업 상세 정보 조회
    training_job = sm.describe_training_job(
        TrainingJobName=training_job_name
    )

    # 하이퍼파라미터 추출
    hyper_params = [
        {'name': k, 'value': str(v)}
        for k, v in training_job.get('HyperParameters', {}).items()
        if not k.startswith('sagemaker_')  # SageMaker 내부 파라미터 제외
    ]

    # 훈련 메트릭 추출
    metrics = []
    for metric in training_job.get('FinalMetricDataList', []):
        metrics.append({
            'name': metric['MetricName'],
            'type': 'number',
            'value': metric['Value']
        })

    # 모델 카드 콘텐츠 구성
    content = {
        'model_overview': {
            'model_description': f'{training_job_name}에서 훈련된 모델입니다.',
            'model_creator': 'ML Engineering Team',
            'model_artifact': [
                training_job.get('ModelArtifacts', {}).get('S3ModelArtifacts', '')
            ],
            'algorithm_type': training_job.get('AlgorithmSpecification', {}).get('TrainingImage', 'Unknown')
        },
        'intended_uses': {
            'purpose_of_model': '(작성 필요)',
            'intended_uses': '(작성 필요)',
            'risk_rating': 'Medium'
        },
        'training_details': {
            'training_job_details': {
                'training_arn': training_job['TrainingJobArn'],
                'training_environment': {
                    'container_image': [
                        training_job.get('AlgorithmSpecification', {}).get('TrainingImage', '')
                    ]
                },
                'hyper_parameters': hyper_params
            },
            'training_observations': (
                f"훈련 인스턴스: {training_job.get('ResourceConfig', {}).get('InstanceType', 'N/A')}, "
                f"훈련 시간: {training_job.get('TrainingTimeInSeconds', 0)}초"
            )
        },
        'evaluation_details': [{
            'name': 'Training Metrics',
            'evaluation_observation': '훈련 과정에서 수집된 최종 메트릭입니다.',
            'metric_groups': [{
                'name': 'Final Metrics',
                'metric_data': metrics
            }]
        }] if metrics else []
    }

    # 모델 카드 생성
    response = sm.create_model_card(
        ModelCardName=model_card_name,
        ModelCardStatus='Draft',
        Content=json.dumps(content)
    )

    print(f"모델 카드 생성 완료: {response['ModelCardArn']}")
    return response

# 사용 예시
create_model_card_from_training_job(
    training_job_name='fraud-detection-v2-20240115',
    model_card_name='fraud-detection-v2-auto'
)
```

### 2. SageMaker Clarify와 연동한 Bias 정보 포함

```python
def add_bias_analysis_to_card(model_card_name, clarify_analysis_path):
    """Clarify Bias 분석 결과를 모델 카드에 추가합니다."""
    import json

    s3 = boto3.client('s3')

    # Clarify 분석 결과 로드
    bucket, key = clarify_analysis_path.replace('s3://', '').split('/', 1)
    response = s3.get_object(Bucket=bucket, Key=key)
    bias_report = json.loads(response['Body'].read())

    # 기존 모델 카드 조회
    card = sm.describe_model_card(ModelCardName=model_card_name)
    content = json.loads(card['Content'])

    # Bias 메트릭을 evaluation_details에 추가
    bias_metrics = []
    for facet_name, facet_data in bias_report.get('facets', {}).items():
        for metric_name, metric_value in facet_data.get('metrics', {}).items():
            bias_metrics.append({
                'name': f"{facet_name}_{metric_name}",
                'type': 'number',
                'value': metric_value.get('value', 0)
            })

    content.setdefault('evaluation_details', []).append({
        'name': 'Bias Analysis (SageMaker Clarify)',
        'evaluation_observation': 'SageMaker Clarify를 사용한 편향 분석 결과입니다.',
        'datasets': [clarify_analysis_path],
        'metric_groups': [{
            'name': 'Bias Metrics',
            'metric_data': bias_metrics
        }]
    })

    # 모델 카드 업데이트
    sm.update_model_card(
        ModelCardName=model_card_name,
        Content=json.dumps(content)
    )
    print(f"Bias 분석 결과가 모델 카드에 추가되었습니다.")
```

### 3. 모델 카드 일괄 관리 스크립트

```bash
# 모든 모델 카드 목록 조회
aws sagemaker list-model-cards \
  --region ap-northeast-2 \
  --query 'ModelCardSummaries[*].[ModelCardName,ModelCardStatus,CreationTime]' \
  --output table

# Draft 상태인 모델 카드만 필터링
aws sagemaker list-model-cards \
  --model-card-status Draft \
  --region ap-northeast-2 \
  --query 'ModelCardSummaries[*].ModelCardName' \
  --output text

# 특정 모델 카드의 내용을 JSON으로 조회
aws sagemaker describe-model-card \
  --model-card-name "fraud-detection-model-v2" \
  --query 'Content' \
  --output text \
  --region ap-northeast-2 | python3 -m json.tool
```

## 모범 사례/보안

### 효과적인 모델 카드 작성 가이드라인

1. **intended_uses를 구체적으로 작성하세요**: "사기 탐지에 사용"이 아니라 "신용카드 실시간 거래에서 임계값 0.7 이상일 때 차단 의사결정에 사용"처럼 구체적으로 기술합니다.
2. **부적합한 용도를 명시하세요**: 모델이 사용되어서는 안 되는 시나리오를 명확히 기록합니다. 예를 들어, "이 모델은 대출 심사에 사용해서는 안 됩니다."
3. **평가 지표를 다각도로 기록하세요**: Accuracy만이 아니라 Precision, Recall, F1, AUC-ROC 등 다양한 지표를 포함하고, 가능하면 하위 그룹별 성능도 기록합니다.
4. **위험 등급과 근거를 함께 기록하세요**: High/Medium/Low 등급만이 아니라 왜 그 등급인지를 설명합니다.

### 거버넌스 워크플로우 설계

```
[모델 개발] --> [모델 카드 Draft 생성]
                      |
              [자동: Training/Eval 정보 수집]
                      |
              [수동: Intended Uses, Risk 작성]
                      |
              [상태: PendingReview]
                      |
              [ML 리드 검토]
                      |
           +-----+-----+
           |           |
       [승인]       [반려: 보완 요청]
           |           |
    [상태: Approved]  [상태: Draft로 복귀]
           |
    [Model Registry에 등록]
           |
    [배포 승인]
```

### KMS 암호화 설정

모델 카드에는 민감한 비즈니스 정보가 포함될 수 있으므로, 반드시 KMS 키로 암호화합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateModelCard",
        "sagemaker:DescribeModelCard",
        "sagemaker:UpdateModelCard",
        "sagemaker:ListModelCards"
      ],
      "Resource": "arn:aws:sagemaker:ap-northeast-2:123456789012:model-card/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "kms:Decrypt",
        "kms:GenerateDataKey"
      ],
      "Resource": "arn:aws:kms:ap-northeast-2:123456789012:key/abc-123"
    }
  ]
}
```

## 관련 서비스 비교

| 항목 | SageMaker Model Cards | SageMaker Model Registry | MLflow Model Registry | Google Vertex AI Model Cards |
|------|----------------------|------------------------|-----------------------|------------------------------|
| 주요 목적 | 모델 문서화/거버넌스 | 모델 버전/배포 관리 | 모델 버전/배포 관리 | 모델 문서화/투명성 |
| 문서 구조 | 표준화된 섹션 | 모델 패키지 메타데이터 | 자유 형식 태그/설명 | 표준화된 섹션 |
| Bias 분석 연동 | Clarify 통합 | Clarify 통합 | 별도 구현 필요 | What-If Tool 연동 |
| PDF 내보내기 | 지원 | 미지원 | 미지원 | 지원 |
| 상태 관리 | Draft/Review/Approved/Archived | Pending/Approved/Rejected | Stage 기반 | 미지원 |
| 버전 관리 | 자동 버전 추적 | 모델 패키지 버전 | 버전 기반 | 미지원 |
| 암호화 | KMS 지원 | KMS 지원 | 별도 구현 | CMEK 지원 |

### Model Cards vs Model Registry

두 서비스는 상호 보완적입니다. Model Registry는 모델 아티팩트의 버전 관리와 배포 승인 워크플로우에 초점을 맞추고, Model Cards는 모델의 투명성과 문서화에 초점을 맞춥니다. 실무에서는 Model Registry의 각 모델 패키지 버전마다 대응하는 Model Card를 생성하여, 기술적 관리와 거버넌스 문서화를 동시에 수행하는 것이 이상적입니다.

## 요약

Amazon SageMaker Model Cards는 ML 모델의 투명성, 문서화, 거버넌스를 체계적으로 관리하기 위한 서비스입니다.

- 모델의 **개요, 의도된 용도, 훈련 정보, 평가 결과, 추가 정보**를 구조화된 형식으로 기록합니다.
- **Draft -> PendingReview -> Approved -> Archived**의 상태 관리를 통해 검토/승인 워크플로우를 구현할 수 있습니다.
- Training Job, Experiments, Clarify와 통합되어 훈련 정보와 Bias 분석 결과를 자동으로 수집할 수 있습니다.
- **PDF 내보내기** 기능으로 감사 기관이나 규제 당국에 제출할 문서를 생성할 수 있습니다.
- KMS 암호화를 통해 민감한 모델 정보를 보호하며, IAM을 통해 모델 카드 접근 권한을 세밀하게 제어할 수 있습니다.
- 규제가 강한 산업(금융, 의료, 공공)에서 특히 가치가 높으며, EU AI Act 등 AI 규제 대응에도 활용될 수 있습니다.