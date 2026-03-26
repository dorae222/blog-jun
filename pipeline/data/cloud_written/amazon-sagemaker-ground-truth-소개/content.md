# Amazon SageMaker Ground Truth 소개

## 개요

Amazon SageMaker Ground Truth는 머신러닝 학습용 데이터에 정확한 라벨(Label)을 부여할 수 있는 완전관리형 데이터 라벨링 서비스입니다. 머신러닝 프로젝트에서 고품질의 학습 데이터를 확보하는 것은 모델 성능을 결정짓는 가장 중요한 요소 중 하나입니다. 그러나 대규모 데이터셋에 수작업으로 라벨을 부여하는 것은 시간과 비용이 많이 드는 작업입니다.

SageMaker Ground Truth는 이러한 문제를 해결하기 위해 사람(Human Labeler)과 기계(Auto-Labeling ML Model)의 협업 방식을 채택합니다. 초기에 소량의 데이터를 사람이 라벨링하면, 서비스가 자동으로 ML 모델을 학습시켜 나머지 데이터에 대한 라벨을 예측합니다. 이 과정에서 액티브 러닝(Active Learning) 기술을 사용하여 모델의 예측 신뢰도가 높은 데이터만 자동으로 라벨링하고, 신뢰도가 낮은 데이터는 다시 사람에게 검수를 요청합니다.

이를 통해 전통적인 수작업 라벨링 대비 최대 70%까지 비용을 절감할 수 있으며, 동시에 높은 라벨 품질을 유지할 수 있습니다. Ground Truth는 이미지, 텍스트, 동영상, 3D 포인트 클라우드(LiDAR), 문서 등 다양한 데이터 유형의 라벨링을 지원합니다.

## 핵심 기능

### 수동 라벨링 (Human Labeling)

Ground Truth는 세 가지 유형의 작업자(Workforce)를 지원합니다.

| 작업자 유형 | 설명 | 적합한 경우 |
|------------|------|------------|
| **Amazon Mechanical Turk** | 수십만 명의 크라우드 워커 풀 | 일반적인 라벨링 작업, 대규모 처리 |
| **타사 벤더** | AWS Marketplace의 전문 라벨링 업체 | 전문성이 필요한 라벨링(의료, 법률 등) |
| **프라이빗 팀** | 자체 조직 내 라벨러 | 민감한 데이터, 보안 요구사항 |

내장된 라벨링 UI 도구를 통해 바운딩 박스, 시맨틱 세그멘테이션, 이미지 분류, 텍스트 주석, 개체명 인식(NER) 등 다양한 라벨링 작업을 수행할 수 있습니다.

### 자동 라벨링 (Auto-Labeling)

자동 라벨링은 Ground Truth의 가장 강력한 기능입니다. 작동 방식은 다음과 같습니다.

1. 사람이 일부 데이터(수백~수천 건)를 라벨링합니다
2. Ground Truth가 이 데이터로 ML 모델을 학습합니다
3. 학습된 모델이 나머지 데이터에 대한 라벨을 예측합니다
4. 예측 신뢰도가 높은 라벨은 자동으로 적용됩니다
5. 신뢰도가 낮은 데이터는 다시 사람에게 전달됩니다

이 과정이 반복되면서 자동 라벨링의 정확도가 점진적으로 향상됩니다.

### 라벨링 가능한 데이터 유형

| 데이터 유형 | 라벨링 작업 | 활용 분야 |
|------------|-----------|----------|
| **이미지** | 객체 감지, 분류, 시맨틱 세그멘테이션, 키포인트 | 자율주행, 의료 영상, 리테일 |
| **텍스트** | 감성 분석, 개체명 인식(NER), 텍스트 분류 | NLP, 챗봇, 문서 분석 |
| **동영상** | 프레임별 객체 추적, 비디오 분류 | 보안, 스포츠 분석 |
| **3D 포인트 클라우드** | LiDAR 데이터 라벨링, 3D 바운딩 박스 | 자율주행, 로보틱스 |
| **문서** | OCR 필드 추출, 표/문단 분류 | 문서 자동화, 보험 처리 |

### 워크플로우 관리

라벨링 작업의 전체 생명주기를 관리할 수 있습니다. 작업 생성, 작업자 할당, 진행 상태 모니터링, 품질 검수, 비용 추적까지 하나의 인터페이스에서 수행합니다. 커스텀 라벨링 워크플로우가 필요한 경우 Custom Task Template(HTML 기반)을 작성하여 독자적인 라벨링 UI를 구성할 수도 있습니다.

### 출력 포맷

라벨링 결과는 S3에 JSON 또는 Manifest 파일 형태로 저장됩니다. SageMaker의 학습 작업에서 바로 사용할 수 있는 형식이므로 별도의 변환 과정 없이 학습 파이프라인에 연결할 수 있습니다.

```json
{
  "source-ref": "s3://my-bucket/images/image001.jpg",
  "label": 1,
  "label-metadata": {
    "confidence": 0.95,
    "human-annotated": "yes",
    "creation-date": "2025-07-29T12:00:00",
    "type": "groundtruth/image-classification"
  }
}
```

## 아키텍처 / 동작 원리

### 전체 워크플로우

Ground Truth의 라벨링 파이프라인은 다음과 같은 순서로 동작합니다.

1. **데이터 준비**: 라벨링할 데이터를 S3 버킷에 업로드하고, Input Manifest 파일을 생성합니다
2. **라벨링 작업 생성**: 작업 유형, 작업자 유형, 라벨 카테고리 등을 설정합니다
3. **작업 분배**: Ground Truth가 데이터를 작업자에게 분배하고 라벨링 UI를 제공합니다
4. **라벨링 수행**: 사람이 라벨링을 수행하고, 결과가 수집됩니다
5. **자동 라벨링**: 충분한 수동 라벨이 모이면 자동 라벨링 모델이 활성화됩니다
6. **품질 검증**: 합의 기반(Consolidated Annotation) 또는 신뢰도 기반으로 라벨 품질을 확인합니다
7. **결과 저장**: Output Manifest 파일이 S3에 저장됩니다

### 액티브 러닝 메커니즘

액티브 러닝은 Ground Truth의 자동 라벨링을 지탱하는 핵심 기술입니다. 모델이 예측한 라벨의 신뢰도(Confidence Score)를 기준으로 두 가지 경로로 분기합니다.

- **고신뢰도 예측 (Confidence >= 임계값)**: 자동으로 라벨이 적용됩니다. 이 임계값은 Ground Truth가 데이터셋에 맞게 자동으로 최적화합니다.
- **저신뢰도 예측 (Confidence < 임계값)**: 해당 데이터를 다시 사람에게 전달하여 수동 라벨링을 요청합니다. 이 새로운 라벨은 모델 재학습에 사용됩니다.

### 합의 기반 라벨링 (Annotation Consolidation)

동일한 데이터에 대해 여러 작업자가 독립적으로 라벨링을 수행하고, 이를 종합하여 최종 라벨을 결정합니다. 다수결, 가중 투표, 통계적 방법 등을 통해 개별 작업자의 편향을 줄이고 라벨 품질을 높입니다.

## 실전 활용

### AWS CLI를 활용한 라벨링 작업 관리

```bash
# 라벨링 작업 목록 조회
aws sagemaker list-labeling-jobs \
  --sort-by CreationTime \
  --sort-order Descending \
  --max-results 10

# 라벨링 작업 상세 정보 조회
aws sagemaker describe-labeling-job \
  --labeling-job-name "image-classification-job-001"

# 라벨링 작업 생성
aws sagemaker create-labeling-job \
  --labeling-job-name "product-image-classification" \
  --label-attribute-name "product-label" \
  --input-config '{
    "DataSource": {
      "S3DataSource": {
        "ManifestS3Uri": "s3://my-bucket/manifests/input.manifest"
      }
    }
  }' \
  --output-config '{
    "S3OutputPath": "s3://my-bucket/output/"
  }' \
  --role-arn "arn:aws:iam::123456789012:role/SageMakerRole" \
  --human-task-config '{
    "WorkteamArn": "arn:aws:sagemaker:us-east-1:123456789012:workteam/private-crowd/my-team",
    "UiConfig": {
      "UiTemplateS3Uri": "s3://my-bucket/templates/template.html"
    },
    "PreHumanTaskLambdaArn": "arn:aws:lambda:us-east-1:123456789012:function:pre-labeling",
    "AnnotationConsolidationConfig": {
      "AnnotationConsolidationLambdaArn": "arn:aws:lambda:us-east-1:123456789012:function:consolidation"
    },
    "TaskTitle": "Product Image Classification",
    "TaskDescription": "Classify the product image into the correct category",
    "NumberOfHumanWorkersPerDataObject": 3,
    "TaskTimeLimitInSeconds": 300,
    "MaxConcurrentTaskCount": 100
  }'

# 라벨링 작업 중지
aws sagemaker stop-labeling-job \
  --labeling-job-name "product-image-classification"

# 워크팀 목록 조회
aws sagemaker list-workteams --sort-by CreationTime
```

### Python SDK를 활용한 라벨링 작업 생성

```python
import sagemaker
from sagemaker import get_execution_role

session = sagemaker.Session()
role = get_execution_role()
bucket = session.default_bucket()

# Input Manifest 파일 생성
import json

manifest_data = [
    {"source-ref": f"s3://{bucket}/images/img_{i:04d}.jpg"}
    for i in range(1000)
]

manifest_path = f"s3://{bucket}/manifests/input.manifest"
with open("/tmp/input.manifest", "w") as f:
    for item in manifest_data:
        f.write(json.dumps(item) + "\n")

# S3에 업로드
session.upload_data("/tmp/input.manifest", bucket=bucket, key_prefix="manifests")

# 라벨링 작업 설정
import boto3

sm_client = boto3.client('sagemaker')

response = sm_client.create_labeling_job(
    LabelingJobName='image-classification-job-001',
    LabelAttributeName='image-label',
    InputConfig={
        'DataSource': {
            'S3DataSource': {
                'ManifestS3Uri': manifest_path
            }
        }
    },
    OutputConfig={
        'S3OutputPath': f's3://{bucket}/labeling-output/'
    },
    RoleArn=role,
    LabelCategoryConfigS3Uri=f's3://{bucket}/label-categories.json',
    HumanTaskConfig={
        'WorkteamArn': 'arn:aws:sagemaker:us-east-1:123456789012:workteam/private-crowd/my-team',
        'UiConfig': {
            'UiTemplateS3Uri': f's3://{bucket}/templates/classification.html'
        },
        'PreHumanTaskLambdaArn': 'arn:aws:lambda:us-east-1:123456789012:function:pre-labeling',
        'TaskTitle': 'Image Classification',
        'TaskDescription': 'Classify each image into the appropriate category',
        'NumberOfHumanWorkersPerDataObject': 3,
        'TaskTimeLimitInSeconds': 300,
        'AnnotationConsolidationConfig': {
            'AnnotationConsolidationLambdaArn': 'arn:aws:lambda:us-east-1:123456789012:function:consolidation'
        }
    }
)

print(f"라벨링 작업 생성됨: {response['LabelingJobArn']}")
```

### 라벨링 결과 분석

```python
import json
import boto3

s3 = boto3.client('s3')

# Output Manifest 파일 다운로드 및 분석
response = s3.get_object(
    Bucket=bucket,
    Key='labeling-output/image-classification-job-001/manifests/output/output.manifest'
)

results = []
for line in response['Body'].read().decode('utf-8').strip().split('\n'):
    record = json.loads(line)
    results.append({
        'source': record['source-ref'],
        'label': record.get('image-label', 'N/A'),
        'confidence': record.get('image-label-metadata', {}).get('confidence', 0),
        'human_annotated': record.get('image-label-metadata', {}).get('human-annotated', 'unknown')
    })

# 통계 분석
auto_labeled = sum(1 for r in results if r['human_annotated'] == 'no')
human_labeled = sum(1 for r in results if r['human_annotated'] == 'yes')
avg_confidence = sum(r['confidence'] for r in results) / len(results)

print(f"전체 라벨: {len(results)}")
print(f"자동 라벨링: {auto_labeled} ({auto_labeled/len(results)*100:.1f}%)")
print(f"수동 라벨링: {human_labeled} ({human_labeled/len(results)*100:.1f}%)")
print(f"평균 신뢰도: {avg_confidence:.3f}")
```

## 모범 사례 및 보안

### 라벨링 품질 향상 모범 사례

- **명확한 라벨링 지침 작성**: 작업자에게 제공하는 가이드라인을 최대한 구체적으로 작성합니다. 모호한 기준은 라벨 품질 저하의 주요 원인입니다.
- **다수 작업자 활용**: 동일 데이터에 최소 3명 이상의 작업자를 할당하여 합의 기반 라벨링을 수행합니다.
- **초기 데이터 품질 확보**: 자동 라벨링의 정확도는 초기 수작업 라벨의 품질에 크게 의존합니다. 처음 수백 건의 라벨링에 특히 주의를 기울입니다.
- **정기적 품질 검수**: 무작위 샘플링을 통해 라벨 품질을 주기적으로 검증합니다.
- **적절한 단가 설정**: 작업 난이도와 예상 소요 시간에 맞는 단가를 설정하여 작업자의 동기를 유지합니다.

### 보안 설정

- **프라이빗 워크팀 구성**: 민감한 데이터(의료, 금융 등)는 조직 내부 팀으로 라벨링 워크팀을 구성합니다.
- **VPC 격리**: 라벨링 환경을 VPC 내에서 운영하여 데이터 유출을 방지합니다.
- **S3 버킷 정책**: 라벨링 입출력 데이터가 저장되는 S3 버킷에 적절한 접근 제어를 설정합니다.
- **KMS 암호화**: 민감한 데이터는 KMS로 암호화하여 저장합니다.
- **CloudTrail 감사**: 모든 API 호출을 기록하여 데이터 접근 이력을 추적합니다.

## 관련 서비스 비교

| 항목 | SageMaker Ground Truth | Label Studio (오픈소스) | Labelbox | Scale AI |
|------|----------------------|----------------------|----------|----------|
| **유형** | AWS 관리형 | 오픈소스 (셀프호스트) | SaaS | SaaS |
| **자동 라벨링** | 액티브 러닝 기반 내장 | 플러그인으로 지원 | ML-Assisted | 자체 ML 모델 |
| **작업자 관리** | MTurk + 프라이빗 팀 | 자체 관리 | 자체 관리 | Scale 전문 인력 |
| **3D 포인트 클라우드** | 지원 (LiDAR) | 제한적 | 지원 | 지원 |
| **SageMaker 통합** | 완전 통합 | 별도 연동 필요 | API 연동 | API 연동 |
| **비용** | 작업량 기반 | 무료 (인프라 비용) | 구독 + 작업량 | 작업량 기반 |
| **확장성** | 수백만 건 처리 가능 | 인프라에 의존 | 대규모 지원 | 대규모 지원 |

Ground Truth는 AWS 생태계 내에서 가장 자연스러운 통합을 제공합니다. 특히 SageMaker의 학습 파이프라인과 직접 연동되어 라벨링 결과를 바로 모델 학습에 활용할 수 있다는 점이 큰 장점입니다. 반면 멀티 클라우드 환경이나 온프레미스에서의 유연성이 필요한 경우 Label Studio나 Labelbox가 더 적합할 수 있습니다.

## 요약

Amazon SageMaker Ground Truth는 ML 프로젝트에서 가장 시간과 비용이 많이 드는 데이터 라벨링 작업을 효율화하는 핵심 서비스입니다. 액티브 러닝 기반의 자동 라벨링을 통해 최대 70%의 비용 절감이 가능하며, Amazon Mechanical Turk, 전문 벤더, 프라이빗 팀 등 다양한 작업자 유형을 지원하여 프로젝트 요구사항에 맞는 유연한 라벨링 파이프라인을 구축할 수 있습니다.

이미지, 텍스트, 동영상, 3D 포인트 클라우드 등 폭넓은 데이터 유형을 지원하고, SageMaker의 학습 파이프라인과 직접 연동되어 라벨링부터 모델 학습까지 원활한 워크플로우를 제공합니다. 자율주행, 의료 AI, 전자상거래, 문서 자동화 등 대규모 라벨링이 필요한 ML 프로젝트에서 Ground Truth는 필수적인 도구로 자리잡고 있습니다.