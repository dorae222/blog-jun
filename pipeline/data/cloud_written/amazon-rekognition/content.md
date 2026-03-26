# Amazon Rekognition: AWS의 완전관리형 이미지/비디오 분석 서비스

## 개요

Amazon Rekognition은 AWS가 제공하는 완전관리형 컴퓨터 비전 서비스입니다. 머신러닝에 대한 전문 지식 없이도 이미지와 비디오에서 객체, 사람, 텍스트, 장면, 활동을 식별하고 분석할 수 있습니다. AWS가 자체적으로 수십억 장의 이미지를 학습시킨 딥러닝 모델을 기반으로 하며, 사용자는 API 호출만으로 고성능 비전 기능을 즉시 활용할 수 있습니다.

Rekognition은 크게 두 가지 제품 라인으로 구분됩니다. 정적 이미지를 분석하는 **Rekognition Image**와 저장된 비디오 또는 스트리밍 비디오를 분석하는 **Rekognition Video**입니다. 두 서비스 모두 사전 훈련된 모델을 사용하므로 별도의 학습 데이터나 모델 훈련 과정이 필요하지 않습니다.

기업에서는 보안 감시 시스템의 얼굴 인식, 미디어 플랫폼의 콘텐츠 모더레이션, 제조업의 품질 검사, 소매업의 고객 분석 등 다양한 분야에서 Rekognition을 활용하고 있습니다. 특히 서버리스 아키텍처와 결합하면 인프라 관리 부담 없이 대규모 이미지/비디오 분석 파이프라인을 구축할 수 있다는 점이 큰 장점입니다.

## 핵심 기능

### 1. 객체 및 장면 탐지 (Object and Scene Detection)

Rekognition은 이미지에서 수천 가지의 객체와 장면을 식별할 수 있습니다. 각 탐지 결과에는 신뢰도(Confidence) 점수가 포함되며, 이를 통해 결과의 정확도를 판단할 수 있습니다.

```bash
# AWS CLI를 사용한 객체 탐지
aws rekognition detect-labels \
  --image '{"S3Object":{"Bucket":"my-image-bucket","Name":"sample.jpg"}}' \
  --max-labels 10 \
  --min-confidence 80 \
  --region ap-northeast-2
```

응답 예시는 다음과 같습니다.

```json
{
  "Labels": [
    {
      "Name": "Car",
      "Confidence": 99.15,
      "Instances": [
        {
          "BoundingBox": {
            "Width": 0.35,
            "Height": 0.27,
            "Left": 0.22,
            "Top": 0.45
          },
          "Confidence": 99.15
        }
      ],
      "Parents": [
        {"Name": "Vehicle"},
        {"Name": "Transportation"}
      ]
    },
    {
      "Name": "Road",
      "Confidence": 97.82,
      "Instances": [],
      "Parents": []
    }
  ]
}
```

`Instances` 배열에는 해당 객체가 이미지 내에서 구체적으로 어느 위치에 있는지를 나타내는 바운딩 박스(BoundingBox) 좌표가 포함됩니다. `Parents` 배열은 탐지된 레이블의 상위 카테고리를 나타내어 계층적 분류가 가능합니다.

### 2. 얼굴 탐지 및 분석 (Face Detection and Analysis)

얼굴 탐지는 이미지에서 얼굴의 위치를 찾고, 나이 범위, 성별, 감정 상태, 안경 착용 여부 등 다양한 속성을 분석합니다.

```bash
# 얼굴 탐지 및 속성 분석
aws rekognition detect-faces \
  --image '{"S3Object":{"Bucket":"my-image-bucket","Name":"portrait.jpg"}}' \
  --attributes ALL \
  --region ap-northeast-2
```

### 3. 얼굴 비교 및 검색 (Face Comparison and Search)

Rekognition은 두 얼굴 간의 유사도를 비교하거나, 사전에 등록된 얼굴 컬렉션에서 특정 얼굴을 검색하는 기능을 제공합니다.

```bash
# 얼굴 컬렉션 생성
aws rekognition create-collection \
  --collection-id "employee-faces" \
  --region ap-northeast-2

# 컬렉션에 얼굴 인덱싱(등록)
aws rekognition index-faces \
  --collection-id "employee-faces" \
  --image '{"S3Object":{"Bucket":"my-image-bucket","Name":"employee-001.jpg"}}' \
  --external-image-id "employee-001" \
  --detection-attributes ALL \
  --region ap-northeast-2

# 얼굴 검색 - 새 이미지에서 컬렉션 내 일치하는 얼굴 찾기
aws rekognition search-faces-by-image \
  --collection-id "employee-faces" \
  --image '{"S3Object":{"Bucket":"my-image-bucket","Name":"visitor.jpg"}}' \
  --face-match-threshold 90 \
  --max-faces 5 \
  --region ap-northeast-2
```

얼굴 컬렉션은 최대 2,000만 개의 얼굴을 저장할 수 있으며, 검색 속도는 컬렉션 크기와 무관하게 일정합니다. 이는 내부적으로 벡터 인덱싱 기술을 사용하기 때문입니다.

### 4. 텍스트 탐지 (Text Detection)

이미지 내의 텍스트를 탐지하고 인식하는 OCR(Optical Character Recognition) 기능을 제공합니다. 도로 표지판, 명함, 문서 등에서 텍스트를 추출할 때 유용합니다.

```bash
# 이미지 내 텍스트 탐지
aws rekognition detect-text \
  --image '{"S3Object":{"Bucket":"my-image-bucket","Name":"sign.jpg"}}' \
  --region ap-northeast-2
```

### 5. Custom Labels

Rekognition Custom Labels는 사전 훈련된 모델로는 탐지할 수 없는 비즈니스 특화 객체를 인식하기 위한 기능입니다. 소량의 학습 데이터(최소 10장)만으로도 커스텀 모델을 훈련시킬 수 있으며, AWS가 전이 학습(Transfer Learning) 기법을 자동으로 적용합니다.

```bash
# Custom Labels 프로젝트 생성
aws rekognition create-project \
  --project-name "defect-detection" \
  --region ap-northeast-2

# 프로젝트 목록 조회
aws rekognition describe-projects \
  --region ap-northeast-2
```

### 6. 비디오 분석 (Video Analysis)

Rekognition Video는 비동기 방식으로 동작합니다. 분석 작업을 시작하면 Job ID가 반환되고, 작업 완료 후 SNS 알림을 통해 결과를 가져옵니다.

```bash
# 비디오에서 레이블 탐지 시작 (비동기)
aws rekognition start-label-detection \
  --video '{"S3Object":{"Bucket":"my-video-bucket","Name":"traffic.mp4"}}' \
  --notification-channel '{"SNSTopicArn":"arn:aws:sns:ap-northeast-2:123456789012:rekognition-results","RoleArn":"arn:aws:iam::123456789012:role/RekognitionRole"}' \
  --region ap-northeast-2

# 결과 조회
aws rekognition get-label-detection \
  --job-id "abc123def456" \
  --sort-by TIMESTAMP \
  --region ap-northeast-2
```

## 아키텍처/동작 원리

### 전체 아키텍처

Rekognition의 내부 아키텍처는 다음과 같은 계층 구조로 구성됩니다.

```
+------------------------------------------------------------------+
|                      API Gateway Layer                           |
|  (REST API / SDK / CLI)                                          |
+------------------------------------------------------------------+
|                                                                  |
|  +-------------------+  +-------------------+  +---------------+ |
|  | Rekognition Image |  | Rekognition Video |  | Custom Labels | |
|  | - DetectLabels    |  | - StartLabel...   |  | - Train Model | |
|  | - DetectFaces     |  | - StartFace...    |  | - Detect      | |
|  | - DetectText      |  | - StartPerson...  |  |               | |
|  | - CompareFaces    |  | - StartText...    |  |               | |
|  +-------------------+  +-------------------+  +---------------+ |
|                                                                  |
+------------------------------------------------------------------+
|                    Deep Learning Models                           |
|  (CNN, ResNet 기반 사전 훈련 모델)                                 |
+------------------------------------------------------------------+
|                                                                  |
|  +----------------+  +--------------+  +-----------------------+ |
|  | S3 Integration |  | SNS/SQS      |  | Face Collection       | |
|  | (이미지/비디오) |  | (비동기 알림) |  | (벡터 인덱스 스토어)  | |
|  +----------------+  +--------------+  +-----------------------+ |
+------------------------------------------------------------------+
```

### 이미지 분석 처리 흐름

1. 클라이언트가 S3 객체 참조 또는 Base64 인코딩된 이미지 바이트를 API에 전달합니다.
2. Rekognition이 이미지를 사전 훈련된 딥러닝 모델에 입력합니다.
3. CNN(Convolutional Neural Network) 기반 특징 추출이 수행됩니다.
4. 추출된 특징으로부터 객체 분류, 위치 특정, 속성 분석이 이루어집니다.
5. 결과가 JSON 형식으로 클라이언트에 반환됩니다.

이미지 분석은 동기(Synchronous) 방식으로 처리되므로, API 호출 후 즉시 결과를 받을 수 있습니다. 이미지 크기 제한은 S3 참조 시 15MB, 바이트 전송 시 5MB입니다.

### 비디오 분석 처리 흐름

비디오 분석은 비동기(Asynchronous) 방식으로 동작합니다.

```
클라이언트 --> Start API 호출 --> Job ID 반환
                                    |
                              [백그라운드 처리]
                              프레임 추출 --> 각 프레임 분석
                                    |
                              SNS 알림 전송 (SUCCEEDED/FAILED)
                                    |
클라이언트 <-- Get API로 결과 조회 <--+
```

비디오는 프레임 단위로 분해된 후 각 프레임에 대해 이미지 분석이 수행됩니다. 결과에는 각 탐지 항목의 타임스탬프가 포함되어, 비디오의 어느 시점에서 무엇이 감지되었는지를 정확히 파악할 수 있습니다.

### 얼굴 컬렉션 동작 원리

얼굴 컬렉션은 Rekognition의 가장 강력한 기능 중 하나입니다. 내부적으로는 다음과 같은 과정을 거칩니다.

1. **인덱싱(Indexing)**: `IndexFaces` API를 호출하면 이미지에서 얼굴을 탐지하고, 각 얼굴의 특징을 128차원 벡터로 변환합니다.
2. **저장**: 변환된 벡터는 얼굴 컬렉션에 저장됩니다. 원본 이미지는 저장되지 않으며, 오직 특징 벡터만 보관됩니다.
3. **검색**: `SearchFacesByImage` API가 호출되면 입력 이미지의 얼굴을 벡터로 변환한 후, 컬렉션 내 저장된 벡터들과 코사인 유사도를 계산합니다.
4. **결과 반환**: 유사도가 임계값 이상인 얼굴들을 유사도 순서로 반환합니다.

## 실전 활용

### 1. 서버리스 이미지 분석 파이프라인

S3에 이미지가 업로드되면 자동으로 분석하는 서버리스 파이프라인을 구성할 수 있습니다.

```python
# Lambda 함수 - S3 이벤트 트리거로 자동 분석
import json
import boto3

rekognition = boto3.client('rekognition', region_name='ap-northeast-2')
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
table = dynamodb.Table('ImageAnalysisResults')

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # 객체 및 장면 탐지
    label_response = rekognition.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}},
        MaxLabels=20,
        MinConfidence=75
    )

    # 얼굴 탐지
    face_response = rekognition.detect_faces(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}},
        Attributes=['ALL']
    )

    # 텍스트 탐지
    text_response = rekognition.detect_text(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}}
    )

    # DynamoDB에 결과 저장
    table.put_item(Item={
        'image_key': key,
        'bucket': bucket,
        'labels': json.dumps(label_response['Labels'], default=str),
        'face_count': len(face_response['FaceDetails']),
        'detected_text': [t['DetectedText'] for t in text_response['TextDetections']
                          if t['Type'] == 'LINE'],
        'analyzed_at': context.get_remaining_time_in_millis()
    })

    return {
        'statusCode': 200,
        'body': json.dumps({
            'labels': len(label_response['Labels']),
            'faces': len(face_response['FaceDetails']),
            'text_lines': len([t for t in text_response['TextDetections']
                              if t['Type'] == 'LINE'])
        })
    }
```

### 2. 실시간 비디오 스트림 분석

Kinesis Video Streams와 연동하여 실시간 비디오 분석이 가능합니다.

```bash
# Kinesis Video Stream에서 얼굴 검색 시작
aws rekognition create-stream-processor \
  --name "entrance-monitor" \
  --input '{"KinesisVideoStream":{"Arn":"arn:aws:kinesisvideo:ap-northeast-2:123456789012:stream/entrance-camera/1234567890"}}' \
  --output '{"KinesisDataStream":{"Arn":"arn:aws:kinesis:ap-northeast-2:123456789012:stream/rekognition-results"}}' \
  --role-arn "arn:aws:iam::123456789012:role/RekognitionStreamRole" \
  --settings '{"FaceSearch":{"CollectionId":"employee-faces","FaceMatchThreshold":85}}' \
  --region ap-northeast-2

# 스트림 프로세서 시작
aws rekognition start-stream-processor \
  --name "entrance-monitor" \
  --region ap-northeast-2
```

### 3. Python SDK를 활용한 배치 처리

대량의 이미지를 배치로 처리할 때는 다음과 같은 패턴을 사용합니다.

```python
import boto3
import concurrent.futures
from botocore.config import Config

# 재시도 설정
config = Config(
    retries={'max_attempts': 5, 'mode': 'adaptive'},
    max_pool_connections=25
)
rekognition = boto3.client('rekognition', region_name='ap-northeast-2', config=config)
s3 = boto3.client('s3', region_name='ap-northeast-2')

def analyze_image(bucket, key):
    """단일 이미지 분석"""
    try:
        response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxLabels=15,
            MinConfidence=80
        )
        return {
            'key': key,
            'status': 'success',
            'labels': [{
                'name': label['Name'],
                'confidence': label['Confidence']
            } for label in response['Labels']]
        }
    except Exception as e:
        return {'key': key, 'status': 'error', 'error': str(e)}

def batch_analyze(bucket, prefix, max_workers=10):
    """S3 프리픽스 하위의 모든 이미지를 병렬 분석"""
    paginator = s3.get_paginator('list_objects_v2')
    image_keys = []

    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            if obj['Key'].lower().endswith(('.jpg', '.jpeg', '.png')):
                image_keys.append(obj['Key'])

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(analyze_image, bucket, key): key
            for key in image_keys
        }
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    return results

# 실행
results = batch_analyze('my-image-bucket', 'uploads/2024/', max_workers=10)
print(f"분석 완료: {len(results)}개 이미지")
```

## 모범 사례/보안

### IAM 최소 권한 원칙

Rekognition API 호출에 필요한 최소 권한만 부여하는 것이 중요합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RekognitionReadOnly",
      "Effect": "Allow",
      "Action": [
        "rekognition:DetectLabels",
        "rekognition:DetectFaces",
        "rekognition:DetectText",
        "rekognition:SearchFacesByImage"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3ReadForRekognition",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::my-image-bucket/*"
    }
  ]
}
```

### 비용 최적화 전략

1. **MinConfidence 파라미터 활용**: 높은 신뢰도 결과만 필터링하여 후처리 비용을 절감합니다.
2. **MaxLabels 제한**: 필요한 수만큼의 레이블만 반환받아 불필요한 데이터 전송을 줄입니다.
3. **이미지 크기 최적화**: 분석 전 이미지를 적절한 크기로 리사이즈합니다. Rekognition은 내부적으로 이미지를 리사이즈하지만, 전송 비용과 지연 시간을 줄일 수 있습니다.
4. **캐싱 전략**: 동일한 이미지에 대한 반복 분석을 피하기 위해 DynamoDB나 ElastiCache에 결과를 캐싱합니다.

### 데이터 프라이버시

- Rekognition은 분석을 위해 전달된 이미지를 서비스 개선 목적으로 사용하지 않습니다(AWS 정책).
- 얼굴 컬렉션에는 원본 이미지가 저장되지 않고 특징 벡터만 저장됩니다.
- 전송 중 데이터는 TLS로 암호화되며, S3에 저장된 이미지는 SSE-S3 또는 SSE-KMS로 암호화할 수 있습니다.
- GDPR, CCPA 등 개인정보 보호 규정 준수를 위해 얼굴 데이터 수집 전 동의를 받아야 합니다.

### 성능 최적화

- **API 호출 제한(Throttling)**: 기본 TPS(Transactions Per Second)가 정해져 있으므로, 대량 처리 시 지수 백오프(Exponential Backoff) 재시도 로직을 구현해야 합니다.
- **리전 선택**: 이미지가 저장된 S3 버킷과 동일한 리전에서 Rekognition을 호출하면 지연 시간을 최소화할 수 있습니다.
- **비동기 처리**: 비디오 분석이나 대량 이미지 처리는 SNS/SQS와 연동한 비동기 패턴을 사용합니다.

## 관련 서비스 비교

| 항목 | Amazon Rekognition | Amazon Textract | Amazon Lookout for Vision | Google Cloud Vision AI |
|------|-------------------|----------------|--------------------------|----------------------|
| 주요 용도 | 범용 이미지/비디오 분석 | 문서 텍스트 추출 | 산업용 이상 탐지 | 범용 이미지 분석 |
| 얼굴 인식 | 지원 | 미지원 | 미지원 | 지원 |
| 비디오 분석 | 지원 | 미지원 | 미지원 | 지원 (Video AI) |
| 커스텀 모델 | Custom Labels | 미지원 | 지원 (핵심 기능) | AutoML Vision |
| 문서 OCR | 기본 텍스트 탐지 | 정밀 문서 분석 | 미지원 | 문서 AI 별도 |
| 스트리밍 분석 | Kinesis 연동 | 미지원 | 미지원 | 미지원 |
| 과금 방식 | 이미지/분 단위 | 페이지 단위 | 이미지/훈련 시간 | 이미지 단위 |

### Rekognition vs Textract 선택 기준

- **이미지 내 간단한 텍스트**(간판, 번호판 등)를 인식할 때는 Rekognition의 `DetectText` API가 적합합니다.
- **구조화된 문서**(양식, 테이블, 영수증 등)에서 데이터를 추출할 때는 Textract를 사용해야 합니다.
- Textract는 키-값 쌍, 테이블 구조까지 이해하지만, Rekognition은 단순 텍스트 위치와 내용만 반환합니다.

### Rekognition vs Lookout for Vision

- Rekognition Custom Labels는 범용적인 커스텀 객체 인식에 적합합니다.
- Lookout for Vision은 제조업 품질 검사처럼 정상/비정상을 이진 분류하는 데 특화되어 있습니다.
- 정상 이미지만으로도 학습이 가능한 이상 탐지(Anomaly Detection)가 필요하면 Lookout for Vision이 더 적합합니다.

## 요약

Amazon Rekognition은 AWS의 핵심 AI 서비스 중 하나로, 이미지와 비디오에 대한 포괄적인 분석 기능을 제공합니다. 사전 훈련된 모델을 활용하여 객체 탐지, 얼굴 분석, 텍스트 인식, 콘텐츠 모더레이션, 비디오 분석 등을 API 호출만으로 수행할 수 있습니다.

핵심 요점을 정리하면 다음과 같습니다.

- **이미지 분석은 동기, 비디오 분석은 비동기** 방식으로 처리됩니다.
- **얼굴 컬렉션**은 벡터 기반으로 동작하며, 원본 이미지를 저장하지 않아 프라이버시 측면에서 유리합니다.
- **Custom Labels**를 통해 비즈니스 특화 객체 인식 모델을 소량의 데이터로 훈련할 수 있습니다.
- **서버리스 아키텍처**(Lambda + S3 + DynamoDB)와 결합하면 확장 가능하고 비용 효율적인 파이프라인을 구축할 수 있습니다.
- 비용 최적화를 위해 MinConfidence, MaxLabels 파라미터를 적극 활용하고, 결과를 캐싱하는 전략을 적용하는 것이 좋습니다.
- 대규모 처리 시에는 API 스로틀링 한도를 고려하여 지수 백오프와 병렬 처리를 조합해야 합니다.