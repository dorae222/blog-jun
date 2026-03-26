# Amazon Rekognition Content Moderation 소개: 유해 콘텐츠 자동 감지 시스템 구축

## 개요

온라인 플랫폼에서 사용자 생성 콘텐츠(UGC, User-Generated Content)의 양이 폭발적으로 증가하면서, 유해 콘텐츠를 실시간으로 감지하고 차단하는 것이 플랫폼 운영의 핵심 과제가 되었습니다. 수동 검토만으로는 초당 수천 건씩 업로드되는 이미지와 비디오를 처리하는 것이 불가능하며, 자동화된 시스템이 반드시 필요합니다.

Amazon Rekognition Content Moderation은 이러한 문제를 해결하기 위한 AWS의 완전관리형 서비스입니다. 이미지와 비디오에서 부적절하거나 불쾌하거나 유해한 콘텐츠를 자동으로 탐지하며, AWS의 딥러닝 모델이 지속적으로 업데이트되어 새로운 유형의 유해 콘텐츠에도 대응할 수 있습니다.

특히 Amazon Augmented AI(A2I)와 결합하면, 자동 감지 결과의 신뢰도가 낮은 경우에만 사람이 검토하는 Human-in-the-Loop 워크플로우를 구축할 수 있습니다. 이를 통해 자동화의 효율성과 사람의 판단력을 모두 활용하는 최적의 모더레이션 시스템을 설계할 수 있습니다.

## 핵심 기능

### 탐지 가능한 콘텐츠 카테고리

Rekognition Content Moderation은 다음과 같은 유해 콘텐츠 카테고리를 탐지합니다.

| 최상위 카테고리 | 하위 카테고리 | 설명 |
|----------------|-------------|------|
| Explicit Nudity | Nudity, Graphic Male Nudity, Graphic Female Nudity, Sexual Activity | 노출 및 성적 콘텐츠 |
| Suggestive | Female Swimwear Or Underwear, Male Swimwear Or Underwear, Partial Nudity | 선정적 콘텐츠 |
| Violence | Graphic Violence Or Gore, Physical Violence, Weapon Violence, Self Injury | 폭력적 콘텐츠 |
| Visually Disturbing | Emaciated Bodies, Corpses, Hanging | 시각적으로 불쾌한 콘텐츠 |
| Rude Gestures | Middle Finger | 불쾌한 제스처 |
| Drugs | Drug Products, Drug Use, Pills, Drug Paraphernalia | 마약 관련 콘텐츠 |
| Tobacco | Tobacco Products, Smoking | 담배 관련 콘텐츠 |
| Alcohol | Drinking, Alcoholic Beverages | 음주 관련 콘텐츠 |
| Gambling | Gambling | 도박 관련 콘텐츠 |
| Hate Symbols | Nazi Party, White Supremacy, Extremist | 혐오 상징물 |

각 카테고리에는 0에서 100 사이의 신뢰도 점수가 부여됩니다. 플랫폼의 정책에 따라 적절한 임계값을 설정하여 차단 수준을 조절할 수 있습니다.

### 이미지 콘텐츠 모더레이션

```bash
# 이미지 콘텐츠 모더레이션 실행
aws rekognition detect-moderation-labels \
  --image '{"S3Object":{"Bucket":"ugc-image-bucket","Name":"user-upload-001.jpg"}}' \
  --min-confidence 60 \
  --region ap-northeast-2
```

응답 형식은 다음과 같습니다.

```json
{
  "ModerationLabels": [
    {
      "Confidence": 93.56,
      "Name": "Graphic Violence Or Gore",
      "ParentName": "Violence",
      "TaxonomyLevel": 2
    },
    {
      "Confidence": 93.56,
      "Name": "Violence",
      "ParentName": "",
      "TaxonomyLevel": 1
    }
  ],
  "ModerationModelVersion": "7.0"
}
```

`TaxonomyLevel`은 카테고리의 계층 수준을 나타냅니다. Level 1은 최상위 카테고리이고, Level 2는 하위 카테고리입니다. 모더레이션 정책을 설계할 때 상위 카테고리 단위로 차단 규칙을 적용하면 더 넓은 범위의 유해 콘텐츠를 포괄할 수 있습니다.

### 비디오 콘텐츠 모더레이션

비디오 모더레이션은 비동기 방식으로 동작합니다. 비디오를 프레임 단위로 분석하며, 유해 콘텐츠가 감지된 시점의 타임스탬프를 함께 반환합니다.

```bash
# 비디오 모더레이션 시작
aws rekognition start-content-moderation \
  --video '{"S3Object":{"Bucket":"ugc-video-bucket","Name":"user-video-001.mp4"}}' \
  --min-confidence 60 \
  --notification-channel '{"SNSTopicArn":"arn:aws:sns:ap-northeast-2:123456789012:moderation-results","RoleArn":"arn:aws:iam::123456789012:role/RekognitionRole"}' \
  --region ap-northeast-2

# 결과 조회
aws rekognition get-content-moderation \
  --job-id "abc123def456" \
  --sort-by TIMESTAMP \
  --region ap-northeast-2
```

비디오 모더레이션 결과에는 각 감지 시점의 밀리초 단위 타임스탬프가 포함되어, 문제가 되는 구간을 정확히 파악할 수 있습니다.

### Custom Moderation Adapter

Rekognition의 기본 모더레이션 모델은 범용적인 유해 콘텐츠를 탐지하지만, 플랫폼마다 콘텐츠 정책이 다를 수 있습니다. Custom Moderation Adapter를 사용하면 기본 모델의 탐지 임계값을 플랫폼의 정책에 맞게 미세 조정할 수 있습니다.

```bash
# 어댑터 프로젝트 생성
aws rekognition create-project \
  --project-name "custom-moderation-adapter" \
  --feature CONTENT_MODERATION \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### Content Moderation 파이프라인 아키텍처

실전에서 사용되는 콘텐츠 모더레이션 파이프라인의 전체 아키텍처는 다음과 같습니다.

```
+------------------------------------------------------------------+
|                    콘텐츠 업로드                                    |
|  사용자 --> API Gateway --> Lambda --> S3 (원본 저장)              |
+------------------------------------------------------------------+
                              |
                    S3 Event Notification
                              |
+------------------------------------------------------------------+
|                    1차 자동 검토                                   |
|  S3 Event --> Lambda --> Rekognition DetectModerationLabels       |
|                              |                                    |
|                   +----------+----------+                         |
|                   |                     |                         |
|            신뢰도 >= 90%          60% <= 신뢰도 < 90%             |
|            (자동 차단)            (사람 검토 필요)                  |
|                   |                     |                         |
|            DynamoDB 기록          A2I Human Loop 생성             |
|            + SNS 알림                   |                         |
+------------------------------------------------------------------+
                                          |
+------------------------------------------------------------------+
|                    2차 사람 검토 (A2I)                             |
|  A2I Human Loop --> SageMaker Workforce --> 검토 UI               |
|                              |                                    |
|                   +----------+----------+                         |
|                   |                     |                         |
|              승인 (게시)           거절 (차단)                     |
|                   |                     |                         |
|            콘텐츠 공개            DynamoDB 기록 + 사용자 알림      |
+------------------------------------------------------------------+
```

### 신뢰도 기반 라우팅 로직

모더레이션 시스템의 핵심은 신뢰도 점수에 따른 라우팅 로직입니다. 일반적으로 다음과 같은 3단계 분류를 적용합니다.

1. **자동 승인** (신뢰도 < 낮은 임계값): 유해 콘텐츠가 감지되지 않은 경우, 자동으로 게시를 허용합니다.
2. **사람 검토** (낮은 임계값 <= 신뢰도 < 높은 임계값): 모델이 확신하지 못하는 경우, 사람 검토자에게 전달합니다.
3. **자동 차단** (신뢰도 >= 높은 임계값): 유해 콘텐츠가 확실한 경우, 자동으로 차단합니다.

이 임계값은 플랫폼의 특성에 따라 조정해야 합니다. 아동 대상 플랫폼은 낮은 임계값을 적용하여 더 엄격하게 필터링하고, 성인 콘텐츠 플랫폼은 높은 임계값을 적용하여 과도한 차단을 방지합니다.

### A2I(Amazon Augmented AI) 연동 원리

A2I는 ML 예측에 사람의 검토를 추가하는 서비스입니다. Rekognition Content Moderation과의 통합은 다음과 같이 동작합니다.

1. Rekognition이 이미지를 분석하여 모더레이션 레이블과 신뢰도를 반환합니다.
2. 신뢰도가 설정된 범위 내에 있으면 A2I Human Loop가 자동으로 생성됩니다.
3. 사전에 구성된 작업자 팀(Private Workforce 또는 Amazon Mechanical Turk)에게 검토 작업이 할당됩니다.
4. 작업자가 커스텀 UI를 통해 콘텐츠를 검토하고 판정 결과를 제출합니다.
5. 판정 결과가 S3에 저장되고, CloudWatch Events를 통해 후속 처리가 트리거됩니다.

## 실전 활용

### 1. Lambda를 활용한 자동 모더레이션 함수

```python
import json
import boto3
from datetime import datetime

rekognition = boto3.client('rekognition', region_name='ap-northeast-2')
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
sns = boto3.client('sns', region_name='ap-northeast-2')

table = dynamodb.Table('ModerationResults')

# 모더레이션 정책 설정
MODERATION_POLICY = {
    'auto_block_threshold': 90,
    'human_review_threshold': 60,
    'blocked_categories': [
        'Explicit Nudity', 'Violence', 'Hate Symbols',
        'Drugs', 'Visually Disturbing'
    ],
    'warning_categories': [
        'Suggestive', 'Tobacco', 'Alcohol', 'Gambling'
    ]
}

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # Rekognition 모더레이션 분석
    response = rekognition.detect_moderation_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}},
        MinConfidence=MODERATION_POLICY['human_review_threshold']
    )

    moderation_labels = response['ModerationLabels']

    if not moderation_labels:
        # 유해 콘텐츠 미감지 - 자동 승인
        decision = 'APPROVED'
        reason = 'No moderation labels detected'
    else:
        # 최고 신뢰도 레이블 확인
        max_label = max(moderation_labels, key=lambda x: x['Confidence'])
        top_category = max_label.get('ParentName') or max_label['Name']

        if (max_label['Confidence'] >= MODERATION_POLICY['auto_block_threshold']
                and top_category in MODERATION_POLICY['blocked_categories']):
            decision = 'BLOCKED'
            reason = f"{max_label['Name']} detected with {max_label['Confidence']:.1f}% confidence"
        elif top_category in MODERATION_POLICY['blocked_categories']:
            decision = 'HUMAN_REVIEW'
            reason = f"{max_label['Name']} detected with {max_label['Confidence']:.1f}% confidence - needs review"
        elif top_category in MODERATION_POLICY['warning_categories']:
            decision = 'APPROVED_WITH_WARNING'
            reason = f"{max_label['Name']} detected - age restriction applied"
        else:
            decision = 'APPROVED'
            reason = 'Detected content within acceptable range'

    # 결과 저장
    table.put_item(Item={
        'image_key': key,
        'decision': decision,
        'reason': reason,
        'labels': json.dumps(moderation_labels, default=str),
        'model_version': response.get('ModerationModelVersion', 'unknown'),
        'timestamp': datetime.utcnow().isoformat()
    })

    # 차단 시 관리자 알림
    if decision == 'BLOCKED':
        sns.publish(
            TopicArn='arn:aws:sns:ap-northeast-2:123456789012:moderation-alerts',
            Subject=f'Content Blocked: {key}',
            Message=json.dumps({
                'image_key': key,
                'decision': decision,
                'reason': reason,
                'labels': moderation_labels
            }, default=str)
        )

    return {'decision': decision, 'reason': reason}
```

### 2. A2I Human Loop 설정

```python
import boto3

a2i = boto3.client('sagemaker-a2i-runtime', region_name='ap-northeast-2')

def create_human_review(image_key, bucket, moderation_labels):
    """A2I Human Loop를 생성하여 사람 검토 요청"""
    response = a2i.start_human_loop(
        HumanLoopName=f"moderation-review-{image_key.replace('/', '-')}",
        FlowDefinitionArn='arn:aws:sagemaker:ap-northeast-2:123456789012:flow-definition/content-moderation-flow',
        HumanLoopInput={
            'InputContent': json.dumps({
                'taskObject': f"s3://{bucket}/{image_key}",
                'moderationLabels': moderation_labels
            })
        }
    )
    return response['HumanLoopArn']
```

### 3. CloudFormation을 활용한 인프라 정의

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Content Moderation Pipeline

Resources:
  UGCBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: ugc-content-bucket
      NotificationConfiguration:
        LambdaConfigurations:
          - Event: s3:ObjectCreated:*
            Function: !GetAtt ModerationFunction.Arn
            Filter:
              S3Key:
                Rules:
                  - Name: prefix
                    Value: uploads/

  ModerationResultsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: ModerationResults
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: image_key
          AttributeType: S
      KeySchema:
        - AttributeName: image_key
          KeyType: HASH

  ModerationFunction:
    Type: AWS::Lambda::Function
    Properties:
      FunctionName: content-moderation
      Runtime: python3.12
      Handler: index.lambda_handler
      Timeout: 60
      MemorySize: 256
      Role: !GetAtt ModerationFunctionRole.Arn

  ModerationFunctionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
      Policies:
        - PolicyName: ModerationPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - rekognition:DetectModerationLabels
                Resource: '*'
              - Effect: Allow
                Action:
                  - s3:GetObject
                Resource: !Sub '${UGCBucket.Arn}/*'
              - Effect: Allow
                Action:
                  - dynamodb:PutItem
                Resource: !GetAtt ModerationResultsTable.Arn
```

## 모범 사례/보안

### 임계값 튜닝 전략

모더레이션 시스템의 성능은 임계값 설정에 크게 좌우됩니다. 다음과 같은 접근 방식을 권장합니다.

1. **초기 설정**: 자동 차단 임계값을 90%, 사람 검토 임계값을 50%로 시작합니다.
2. **데이터 수집**: 2-4주간 실제 트래픽에 대한 모더레이션 결과를 수집합니다.
3. **Precision/Recall 분석**: 사람 검토 결과와 자동 판정 결과를 비교하여 오탐률(False Positive)과 미탐률(False Negative)을 측정합니다.
4. **임계값 조정**: 오탐이 많으면 임계값을 올리고, 미탐이 많으면 임계값을 내립니다.
5. **카테고리별 차등 적용**: 폭력/혐오 콘텐츠는 낮은 임계값을, 음주/흡연 콘텐츠는 높은 임계값을 적용합니다.

### 비용 관리

- 이미지 모더레이션은 분석된 이미지 수에 따라 과금됩니다 (약 $0.001/이미지, 대량 할인 적용).
- 비디오 모더레이션은 분석된 비디오의 분(minute) 단위로 과금됩니다.
- A2I 사람 검토 비용은 별도이므로, Human Loop로 전달되는 비율을 모니터링하고 최적화해야 합니다.
- 모더레이션이 필요 없는 시스템 생성 이미지(썸네일, 로고 등)는 필터링하여 불필요한 API 호출을 방지합니다.

### 법적/윤리적 고려사항

- 자동 모더레이션 시스템의 판정에 이의를 제기할 수 있는 절차를 마련해야 합니다.
- 특정 문화권에서는 허용되지만 다른 문화권에서는 부적절한 콘텐츠가 존재하므로, 지역별 정책을 차등 적용해야 합니다.
- 모더레이션 결과와 판정 로그를 감사 추적(Audit Trail) 목적으로 보관해야 합니다.
- AWS의 AI 서비스 이용 약관을 준수하여 얼굴 인식 등 민감한 기능의 사용을 적절히 제한해야 합니다.

### 모니터링 및 알림

```bash
# CloudWatch 메트릭 기반 알림 설정
aws cloudwatch put-metric-alarm \
  --alarm-name "HighBlockRate" \
  --alarm-description "Content block rate exceeds 10%" \
  --namespace "ContentModeration" \
  --metric-name "BlockedContentCount" \
  --statistic Sum \
  --period 3600 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions "arn:aws:sns:ap-northeast-2:123456789012:ops-alerts" \
  --region ap-northeast-2
```

## 관련 서비스 비교

| 항목 | Rekognition Content Moderation | AWS Comprehend (텍스트) | Google Cloud Vision SafeSearch | Azure Content Moderator |
|------|-------------------------------|----------------------|-------------------------------|------------------------|
| 이미지 모더레이션 | 지원 | 미지원 | 지원 | 지원 |
| 비디오 모더레이션 | 지원 | 미지원 | 미지원 | 지원 |
| 텍스트 모더레이션 | 미지원 | 지원 (PII/유해 언어) | 미지원 | 지원 |
| Human-in-the-Loop | A2I 연동 | A2I 연동 | 별도 구현 필요 | Review Tool 내장 |
| 커스텀 모델 | Custom Adapter | Custom Classifier | 미지원 | Custom Terms List |
| 카테고리 세분화 | 10개 상위, 30+개 하위 | 유해 언어 탐지 | 5개 카테고리 | 3개 카테고리 |
| 스트리밍 지원 | Kinesis 연동 | 미지원 | 미지원 | 미지원 |

### Rekognition Content Moderation vs 텍스트 기반 모더레이션

이미지/비디오 모더레이션과 텍스트 모더레이션은 상호 보완적입니다. 완전한 UGC 모더레이션 시스템을 구축하려면 두 가지를 모두 적용해야 합니다. 텍스트 모더레이션에는 Amazon Comprehend의 유해 언어 탐지 기능이나 Bedrock Guardrails를 활용할 수 있습니다.

## 요약

Amazon Rekognition Content Moderation은 이미지와 비디오에서 유해 콘텐츠를 자동으로 탐지하는 강력한 서비스입니다. 핵심 내용을 정리하면 다음과 같습니다.

- **10개 이상의 상위 카테고리**와 30개 이상의 하위 카테고리를 지원하여 폭넓은 유해 콘텐츠 유형을 탐지합니다.
- **신뢰도 기반 라우팅**을 통해 자동 승인, 사람 검토, 자동 차단의 3단계 워크플로우를 구성할 수 있습니다.
- **A2I(Amazon Augmented AI)**와 연동하면 모델이 확신하지 못하는 콘텐츠에 대해서만 사람이 검토하는 효율적인 시스템을 구축할 수 있습니다.
- **비디오 모더레이션**은 비동기 방식으로 동작하며, 유해 콘텐츠가 감지된 정확한 타임스탬프를 제공합니다.
- 임계값은 플랫폼 특성에 맞게 카테고리별로 차등 적용하고, 실제 데이터를 기반으로 지속적으로 튜닝해야 합니다.
- 법적/윤리적 고려사항을 반영하여 이의 제기 절차와 감사 추적 로그를 반드시 구현해야 합니다.