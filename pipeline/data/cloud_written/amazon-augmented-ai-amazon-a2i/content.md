<!-- infographic-hero -->
![Amazon Augmented AI (Amazon A2I) 핵심 요약](figures/infographic.svg)

*Figure: Amazon Augmented AI (Amazon A2I) 한 장 요약 인포그래픽*

## 개요

Amazon Augmented AI(Amazon A2I)는 기계 학습(ML) 예측에 대한 휴먼 리뷰(Human Review) 워크플로를 손쉽게 구축할 수 있도록 지원하는 완전 관리형 서비스입니다. 현실 세계에서 ML 모델은 100% 정확한 예측을 보장하지 못합니다. 특히 의료 영상 분석, 금융 문서 처리, 콘텐츠 모더레이션 등 높은 정확도가 요구되는 영역에서는 모델의 예측 결과를 사람이 검토하고 보정하는 과정이 필수적입니다.

Amazon A2I는 이러한 Human-in-the-Loop(HITL) 패턴을 AWS 서비스로 추상화하여, 별도의 복잡한 인프라를 구축하지 않고도 ML 파이프라인에 사람의 판단을 통합할 수 있게 합니다. 모델의 예측 신뢰도(Confidence Score)가 특정 임계값 이하일 때 자동으로 휴먼 리뷰를 트리거하거나, 무작위 샘플링을 통해 전체 예측 품질을 모니터링하는 워크플로를 설정할 수 있습니다.

### 핵심 가치

Amazon A2I가 해결하는 문제는 다음과 같습니다.

- ML 예측의 신뢰도가 낮은 결과에 대해 자동으로 사람의 검토를 요청합니다
- 휴먼 리뷰 워크플로 구축에 필요한 인프라와 UI를 자동으로 관리합니다
- 리뷰 결과를 수집하여 모델 재훈련에 활용할 수 있는 피드백 루프를 형성합니다
- Amazon Textract, Amazon Rekognition 등 다른 AWS AI 서비스와 기본 통합됩니다

---

## 핵심 기능

### 1. 내장 태스크 유형 (Built-in Task Types)

Amazon A2I는 AWS AI 서비스와 바로 연동할 수 있는 내장 태스크 유형을 제공합니다.

**Amazon Textract 연동**: 문서에서 추출한 키-값 쌍이나 테이블 데이터를 사람이 검토합니다.

```bash
# Amazon Textract를 사용한 문서 분석 시작
aws textract analyze-document \
  --document '{"S3Object": {"Bucket": "my-document-bucket", "Name": "invoice.pdf"}}' \
  --feature-types '["FORMS", "TABLES"]' \
  --human-loop-config '{
    "HumanLoopName": "invoice-review-001",
    "FlowDefinitionArn": "arn:aws:sagemaker:us-east-1:123456789012:flow-definition/textract-review-flow",
    "DataAttributes": {
      "ContentClassifiers": ["FreeOfPersonallyIdentifiableInformation"]
    }
  }' \
  --region us-east-1
```

**Amazon Rekognition 연동**: 이미지 콘텐츠 모더레이션 결과를 사람이 검토합니다.

```bash
# Amazon Rekognition 콘텐츠 모더레이션 + A2I 휴먼 리뷰
aws rekognition detect-moderation-labels \
  --image '{"S3Object": {"Bucket": "my-image-bucket", "Name": "user-upload.jpg"}}' \
  --human-loop-config '{
    "HumanLoopName": "moderation-review-001",
    "FlowDefinitionArn": "arn:aws:sagemaker:us-east-1:123456789012:flow-definition/moderation-flow",
    "DataAttributes": {
      "ContentClassifiers": ["FreeOfAdultContent"]
    }
  }' \
  --region us-east-1
```

### 2. 커스텀 태스크 유형 (Custom Task Types)

내장 태스크 유형 외에도 모든 ML 모델의 예측 결과에 대해 커스텀 휴먼 리뷰 워크플로를 구성할 수 있습니다. SageMaker 엔드포인트, 자체 호스팅 모델, 또는 서드파티 AI 서비스의 결과를 A2I로 보내어 리뷰를 수행합니다.

```python
import boto3
import json

a2i_runtime = boto3.client('sagemaker-a2i-runtime', region_name='us-east-1')

# 커스텀 휴먼 리뷰 루프 시작
response = a2i_runtime.start_human_loop(
    HumanLoopName='custom-review-001',
    FlowDefinitionArn='arn:aws:sagemaker:us-east-1:123456789012:flow-definition/custom-review-flow',
    HumanLoopInput={
        'InputContent': json.dumps({
            'image_url': 's3://my-bucket/images/sample.jpg',
            'model_prediction': 'cat',
            'confidence_score': 0.62,
            'all_predictions': [
                {'label': 'cat', 'score': 0.62},
                {'label': 'dog', 'score': 0.28},
                {'label': 'rabbit', 'score': 0.10}
            ]
        })
    },
    DataAttributes={
        'ContentClassifiers': ['FreeOfPersonallyIdentifiableInformation']
    }
)

print(f"Human Loop ARN: {response['HumanLoopArn']}")
```

### 3. Worker Task Template (작업자 태스크 템플릿)

리뷰어에게 표시할 UI를 HTML 기반의 Liquid 템플릿으로 정의합니다. AWS에서 제공하는 사전 구축 위젯을 활용하거나 완전히 커스텀한 UI를 생성할 수 있습니다.

```bash
# Worker Task Template 생성
aws sagemaker create-human-task-ui \
  --human-task-ui-name "my-custom-review-template" \
  --ui-template '{"Content": "<script src=\"https://assets.crowd.aws/crowd-html-elements.js\"></script>\n<crowd-form>\n  <crowd-classifier\n    name=\"category\"\n    categories=\"[\\\"Correct\\\", \\\"Incorrect\\\", \\\"Uncertain\\\"]\"\n    header=\"모델 예측 결과를 검토해 주십시오\"\n  >\n    <classification-target>\n      <p>모델 예측: {{ task.input.model_prediction }}</p>\n      <p>신뢰도: {{ task.input.confidence_score }}</p>\n    </classification-target>\n    <full-instructions header=\"상세 지침\">\n      <p>모델이 예측한 결과가 올바른지 확인하십시오.</p>\n    </full-instructions>\n  </crowd-classifier>\n</crowd-form>"}' \
  --region us-east-1
```

### 4. 워크포스 (Workforce) 관리

Amazon A2I는 세 가지 유형의 리뷰 워크포스를 지원합니다.

- **Private Workforce**: 조직 내부 직원이 리뷰를 수행합니다. Amazon Cognito 또는 OIDC IdP를 통해 인증합니다.
- **Amazon Mechanical Turk**: 대규모 크라우드소싱 작업자 풀을 활용합니다.
- **Vendor Workforce**: AWS Marketplace를 통해 전문 벤더 인력을 활용합니다.

```bash
# Private Workforce 생성 (Cognito 기반)
aws sagemaker create-workforce \
  --workforce-name "my-internal-reviewers" \
  --cognito-config '{
    "UserPool": "us-east-1_AbCdEfGhI",
    "ClientId": "1a2b3c4d5e6f7g8h9i0j"
  }' \
  --region us-east-1

# 워크팀 생성
aws sagemaker create-workteam \
  --workteam-name "document-review-team" \
  --workforce-name "my-internal-reviewers" \
  --member-definitions '[{
    "CognitoMemberDefinition": {
      "UserPool": "us-east-1_AbCdEfGhI",
      "UserGroup": "document-reviewers",
      "ClientId": "1a2b3c4d5e6f7g8h9i0j"
    }
  }]' \
  --description "문서 리뷰 전담 팀" \
  --region us-east-1
```

---

## 아키텍처/동작 원리

### 전체 워크플로 아키텍처

Amazon A2I의 동작 흐름은 다음과 같습니다.

```
[입력 데이터]
    |
    v
[ML 모델 예측] ---(높은 신뢰도)---> [자동 승인] ---> [결과 저장 (S3)]
    |
    |(낮은 신뢰도)
    v
[Flow Definition] ---> [Human Loop 생성]
    |
    v
[Worker Task Template] ---> [리뷰어 UI 렌더링]
    |
    v
[리뷰어가 검토/보정]
    |
    v
[리뷰 결과 저장 (S3)] ---> [후처리/모델 재훈련]
```

### 핵심 구성 요소

**Flow Definition(플로우 정의)**: 워크플로의 전체 흐름을 정의하는 리소스입니다. 어떤 조건에서 휴먼 리뷰를 트리거하고, 어떤 워크팀이 리뷰를 수행하며, 결과를 어디에 저장할지를 지정합니다.

```bash
# Flow Definition 생성
aws sagemaker create-flow-definition \
  --flow-definition-name "textract-review-flow" \
  --human-loop-config '{
    "WorkteamArn": "arn:aws:sagemaker:us-east-1:123456789012:workteam/private-crowd/document-review-team",
    "HumanTaskUiArn": "arn:aws:sagemaker:us-east-1:123456789012:human-task-ui/my-custom-review-template",
    "TaskTitle": "문서 추출 결과 검토",
    "TaskDescription": "Textract가 추출한 키-값 쌍이 올바른지 확인하십시오",
    "TaskCount": 1,
    "TaskAvailabilityLifetimeInSeconds": 43200,
    "TaskTimeLimitInSeconds": 3600,
    "PublicWorkforceTaskPrice": {
      "AmountInUsd": {"Dollars": 0, "Cents": 3, "TenthFractionsOfACent": 6}
    }
  }' \
  --human-loop-activation-config '{
    "HumanLoopActivationConditionsConfig": {
      "HumanLoopActivationConditions": "{\"Conditions\": [{\"ConditionType\": \"ImportantFormKeyConfidenceCheck\", \"ConditionParameters\": {\"ImportantFormKey\": \"*\", \"ImportantFormKeyAliases\": [], \"KeyValueBlockConfidenceLessThan\": 90, \"WordBlockConfidenceLessThan\": 75}}]}"
    }
  }' \
  --output-config '{
    "S3OutputPath": "s3://my-a2i-output/textract-reviews/"
  }' \
  --role-arn "arn:aws:iam::123456789012:role/AmazonA2IServiceRole" \
  --region us-east-1
```

**Human Loop(휴먼 루프)**: 개별 리뷰 작업의 인스턴스입니다. 하나의 Human Loop는 하나의 입력 데이터에 대한 리뷰 요청을 나타내며, 생성부터 완료까지의 생명주기를 가집니다.

```bash
# 활성 Human Loop 목록 조회
aws sagemaker-a2i-runtime list-human-loops \
  --flow-definition-arn "arn:aws:sagemaker:us-east-1:123456789012:flow-definition/textract-review-flow" \
  --sort-order Descending \
  --max-results 10 \
  --region us-east-1

# 특정 Human Loop 상태 조회
aws sagemaker-a2i-runtime describe-human-loop \
  --human-loop-name "invoice-review-001" \
  --region us-east-1
```

### 신뢰도 기반 라우팅 로직

A2I의 핵심은 조건부 라우팅입니다. ML 모델의 예측 신뢰도에 따라 결과를 자동 처리할지, 사람에게 넘길지 결정합니다.

```python
import boto3
import json

def process_prediction(prediction, confidence, threshold=0.85):
    """
    ML 예측 결과를 신뢰도 기반으로 라우팅합니다.
    """
    if confidence >= threshold:
        # 높은 신뢰도: 자동 처리
        return {'status': 'auto_approved', 'prediction': prediction}
    
    # 낮은 신뢰도: A2I 휴먼 리뷰 트리거
    a2i_runtime = boto3.client('sagemaker-a2i-runtime')
    
    response = a2i_runtime.start_human_loop(
        HumanLoopName=f'review-{prediction["id"]}',
        FlowDefinitionArn='arn:aws:sagemaker:us-east-1:123456789012:flow-definition/my-flow',
        HumanLoopInput={
            'InputContent': json.dumps({
                'original_input': prediction['input'],
                'model_output': prediction['output'],
                'confidence': confidence
            })
        }
    )
    
    return {
        'status': 'sent_to_human_review',
        'human_loop_arn': response['HumanLoopArn']
    }
```

---

## 실전 활용

### 사례 1: 보험 청구 문서 자동 처리 파이프라인

보험 회사에서 청구 문서를 자동으로 처리하되, 모델의 확신이 낮은 항목은 사람이 검토하는 파이프라인을 구축하는 예시입니다.

```python
import boto3
import json
from datetime import datetime

def insurance_claim_pipeline(document_s3_uri):
    textract = boto3.client('textract')
    a2i_runtime = boto3.client('sagemaker-a2i-runtime')
    s3 = boto3.client('s3')
    
    bucket, key = document_s3_uri.replace('s3://', '').split('/', 1)
    
    # Step 1: Textract로 문서 분석
    response = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=['FORMS', 'TABLES'],
        HumanLoopConfig={
            'HumanLoopName': f'claim-{datetime.now().strftime("%Y%m%d%H%M%S")}',
            'FlowDefinitionArn': 'arn:aws:sagemaker:us-east-1:123456789012:flow-definition/insurance-claim-flow',
            'DataAttributes': {
                'ContentClassifiers': ['FreeOfPersonallyIdentifiableInformation']
            }
        }
    )
    
    # Step 2: Human Loop가 생성되었는지 확인
    human_loop_status = response.get('HumanLoopActivationOutput', {})
    
    if human_loop_status.get('HumanLoopActivationReasons'):
        print(f"휴먼 리뷰가 트리거되었습니다: {human_loop_status['HumanLoopArn']}")
        return {'status': 'pending_review', 'arn': human_loop_status['HumanLoopArn']}
    else:
        print("높은 신뢰도로 자동 처리됩니다.")
        return {'status': 'auto_processed', 'blocks': response['Blocks']}
```

### 사례 2: 콘텐츠 모더레이션 자동화

사용자 업로드 콘텐츠에 대해 1차로 AI 모더레이션을 수행하고, 경계 케이스를 사람이 최종 판단하는 시스템입니다.

```bash
# Lambda 함수에서 사용할 IAM 역할 생성
aws iam create-role \
  --role-name A2IContentModerationRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# 필요한 정책 연결
aws iam attach-role-policy \
  --role-name A2IContentModerationRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonSageMakerFullAccess

aws iam attach-role-policy \
  --role-name A2IContentModerationRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonRekognitionFullAccess
```

### 사례 3: 리뷰 결과 수집 및 모델 재훈련

```python
import boto3
import json

def collect_review_results(flow_definition_arn):
    """
    완료된 Human Loop의 결과를 수집하여 모델 재훈련 데이터를 생성합니다.
    """
    a2i = boto3.client('sagemaker-a2i-runtime')
    s3 = boto3.client('s3')
    
    # 완료된 Human Loop 조회
    completed_loops = a2i.list_human_loops(
        FlowDefinitionArn=flow_definition_arn,
        StatusEquals='Completed',
        MaxResults=100
    )
    
    training_data = []
    
    for loop in completed_loops['HumanLoopSummaries']:
        loop_detail = a2i.describe_human_loop(
            HumanLoopName=loop['HumanLoopName']
        )
        
        # S3에서 리뷰 결과 가져오기
        output_uri = loop_detail['HumanLoopOutput']['OutputS3Uri']
        bucket, key = output_uri.replace('s3://', '').split('/', 1)
        
        obj = s3.get_object(Bucket=bucket, Key=key)
        review_result = json.loads(obj['Body'].read())
        
        training_data.append({
            'input': review_result['inputContent'],
            'human_label': review_result['humanAnswers'][0]['answerContent'],
            'loop_name': loop['HumanLoopName']
        })
    
    return training_data
```

---

## 모범 사례/보안

### 보안 모범 사례

**IAM 최소 권한 원칙**: A2I 관련 IAM 정책은 필요한 리소스에만 접근할 수 있도록 범위를 제한합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateFlowDefinition",
        "sagemaker:DescribeFlowDefinition",
        "sagemaker:DeleteFlowDefinition"
      ],
      "Resource": "arn:aws:sagemaker:us-east-1:123456789012:flow-definition/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker-a2i-runtime:StartHumanLoop",
        "sagemaker-a2i-runtime:DescribeHumanLoop",
        "sagemaker-a2i-runtime:ListHumanLoops",
        "sagemaker-a2i-runtime:StopHumanLoop"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject"],
      "Resource": "arn:aws:s3:::my-a2i-output/*"
    }
  ]
}
```

**데이터 보호**: 민감한 데이터가 포함된 리뷰 작업에는 반드시 Private Workforce를 사용하고, VPC 엔드포인트를 통해 네트워크 격리를 유지합니다.

```bash
# SageMaker A2I용 VPC 엔드포인트 생성
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --service-name com.amazonaws.us-east-1.sagemaker.api \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-0123456789abcdef0 \
  --security-group-ids sg-0123456789abcdef0 \
  --private-dns-enabled
```

### 운영 모범 사례

- 신뢰도 임계값은 비즈니스 요구사항에 맞게 조정합니다. 너무 낮으면 리뷰 작업이 과다해지고, 너무 높으면 오류를 놓칠 수 있습니다.
- CloudWatch 메트릭을 통해 Human Loop 처리 시간, 대기 큐 크기, 리뷰어 동의율을 모니터링합니다.
- 리뷰 결과를 주기적으로 분석하여 모델 재훈련에 활용하는 피드백 루프를 구성합니다.
- 여러 리뷰어의 합의를 요구하는 경우 TaskCount를 3 이상으로 설정하고 다수결로 최종 판단합니다.

### 비용 최적화

Amazon A2I의 비용은 주로 다음 요소로 구성됩니다.

- **Human Loop 처리 비용**: Human Loop당 과금 (리전별 상이)
- **워크포스 비용**: Mechanical Turk 사용 시 작업당 지불 비용, Private Workforce는 별도 비용 없음
- **S3 저장 비용**: 입력 데이터 및 리뷰 결과 저장 비용

비용을 최적화하려면 신뢰도 임계값을 적절히 설정하여 불필요한 휴먼 리뷰를 줄이고, 리뷰 결과를 활용한 모델 개선으로 점진적으로 휴먼 리뷰 비율을 낮추는 것이 중요합니다.

---

## 관련 서비스 비교

| 항목 | Amazon A2I | Amazon SageMaker Ground Truth | Amazon Mechanical Turk |
|------|-----------|-------------------------------|------------------------|
| 주요 목적 | ML 예측 결과의 휴먼 리뷰 | ML 훈련 데이터 라벨링 | 범용 크라우드소싱 |
| 통합 대상 | Textract, Rekognition, 커스텀 모델 | SageMaker 학습 파이프라인 | 독립 실행형 |
| 워크플로 자동화 | 신뢰도 기반 자동 트리거 | 라벨링 작업 자동 분배 | 수동 작업 생성 |
| UI 커스터마이징 | Worker Task Template (HTML/Liquid) | 라벨링 도구 (내장 + 커스텀) | HIT Template |
| 비용 모델 | Human Loop 단위 과금 | 라벨링 객체 단위 과금 | 작업 단위 직접 지불 |
| 적합한 시나리오 | 추론 시점의 품질 보증 | 학습 데이터 구축 | 다양한 마이크로태스크 |

Amazon A2I는 추론(Inference) 단계에서의 품질 보증에 특화되어 있으며, SageMaker Ground Truth는 학습(Training) 데이터 구축에 초점을 맞춥니다. 두 서비스는 상호 보완적으로 사용됩니다.

---

## 요약

Amazon Augmented AI(Amazon A2I)는 ML 모델의 예측 결과에 대한 휴먼 리뷰 워크플로를 손쉽게 구축할 수 있는 완전 관리형 서비스입니다. 핵심 특징을 정리하면 다음과 같습니다.

- Amazon Textract, Amazon Rekognition과의 내장 통합 및 커스텀 ML 모델 지원을 통해 다양한 AI/ML 워크로드에 적용할 수 있습니다.
- 신뢰도 기반 조건부 라우팅으로 자동 처리와 휴먼 리뷰를 적절히 배분합니다.
- Private Workforce, Mechanical Turk, Vendor Workforce 등 유연한 워크포스 옵션을 제공합니다.
- Worker Task Template을 통해 리뷰어 UI를 완전히 커스터마이징할 수 있습니다.
- 리뷰 결과를 S3에 저장하여 모델 재훈련 피드백 루프를 구성할 수 있습니다.

Human-in-the-Loop 패턴이 필요한 모든 ML 워크로드에서 Amazon A2I는 복잡한 인프라 구축 없이 신뢰성 높은 품질 보증 체계를 제공합니다.