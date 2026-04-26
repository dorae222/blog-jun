<!-- infographic-hero -->
![Amazon SageMaker Model Registry 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker Model Registry 한 장 요약 인포그래픽*

# Amazon SageMaker Model Registry

## 개요

Amazon SageMaker Model Registry는 머신러닝 모델의 전체 생명주기를 체계적으로 관리하기 위한 중앙화된 모델 저장소입니다. 모델 버전 관리, 메타데이터 추적, 승인 워크플로, 그리고 배포 자동화를 위한 통합 인터페이스를 제공하여, MLOps 파이프라인의 핵심 구성 요소로 활용됩니다.

소프트웨어 개발에서 Git이 코드 버전 관리의 표준이 되었듯이, ML 프로젝트에서는 모델의 버전 관리가 필수적입니다. 하지만 ML 모델은 단순한 코드와 달리 모델 아티팩트(가중치 파일), 훈련 데이터, 하이퍼파라미터, 성능 메트릭, 환경 설정 등 다양한 요소가 결합되어 있어, 일반적인 버전 관리 시스템만으로는 효과적으로 관리하기 어렵습니다.

SageMaker Model Registry는 이러한 ML 특화 버전 관리 문제를 해결하기 위해 다음과 같은 핵심 개념을 제공합니다.

- **모델 패키지 그룹(Model Package Group)**: 관련 모델 버전을 묶어 관리하는 논리적 컨테이너입니다.
- **모델 패키지(Model Package)**: 개별 모델 버전으로, 모델 아티팩트와 메타데이터를 포함합니다.
- **승인 상태(Approval Status)**: 각 모델 버전의 배포 승인 상태를 관리합니다 (Approved, Rejected, PendingManualApproval).

## 핵심 기능

### 1. 모델 패키지 그룹 관리

모델 패키지 그룹은 동일한 ML 문제를 해결하는 여러 모델 버전을 하나의 그룹으로 관리합니다. 예를 들어, "고객 이탈 예측 모델"이라는 그룹 안에 v1, v2, v3 등 여러 버전의 모델이 포함될 수 있습니다.

```python
import boto3

sm_client = boto3.client('sagemaker')

# 모델 패키지 그룹 생성
sm_client.create_model_package_group(
    ModelPackageGroupName='customer-churn-prediction',
    ModelPackageGroupDescription='고객 이탈 예측 모델 그룹 - XGBoost 기반',
    Tags=[
        {'Key': 'Project', 'Value': 'customer-analytics'},
        {'Key': 'Team', 'Value': 'data-science'},
        {'Key': 'Environment', 'Value': 'production'}
    ]
)
```

```bash
# 모델 패키지 그룹 목록 조회
aws sagemaker list-model-package-groups \
  --region us-east-1 \
  --sort-by CreationTime \
  --sort-order Descending \
  --output table

# 특정 모델 패키지 그룹 상세 정보 확인
aws sagemaker describe-model-package-group \
  --model-package-group-name "customer-churn-prediction" \
  --region us-east-1
```

### 2. 모델 패키지(버전) 등록

훈련이 완료된 모델을 Model Registry에 등록하는 과정입니다. 모델 아티팩트 위치, 추론 사양, 성능 메트릭 등을 함께 기록합니다.

```python
from sagemaker.model_metrics import (
    MetricsSource,
    ModelMetrics
)

# 모델 메트릭 정의
model_metrics = ModelMetrics(
    model_statistics=MetricsSource(
        s3_uri="s3://my-bucket/evaluation/statistics.json",
        content_type="application/json"
    ),
    model_constraints=MetricsSource(
        s3_uri="s3://my-bucket/evaluation/constraints.json",
        content_type="application/json"
    )
)

# 모델 패키지 등록
model_package = sm_client.create_model_package(
    ModelPackageGroupName='customer-churn-prediction',
    ModelPackageDescription='XGBoost v2 - 하이퍼파라미터 최적화 적용',
    InferenceSpecification={
        'Containers': [
            {
                'Image': '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1',
                'ModelDataUrl': 's3://my-bucket/models/xgboost-churn/model.tar.gz'
            }
        ],
        'SupportedTransformInstanceTypes': ['ml.m5.xlarge', 'ml.m5.2xlarge'],
        'SupportedRealtimeInferenceInstanceTypes': ['ml.m5.xlarge', 'ml.t2.medium'],
        'SupportedContentTypes': ['text/csv'],
        'SupportedResponseMIMETypes': ['text/csv']
    },
    ModelApprovalStatus='PendingManualApproval',
    MetadataProperties={
        'GeneratedBy': 'sagemaker-pipeline-v2',
        'ProjectId': 'customer-analytics-001'
    },
    CustomerMetadataProperties={
        'training_accuracy': '0.9523',
        'validation_accuracy': '0.9412',
        'f1_score': '0.9467',
        'auc_roc': '0.9891',
        'training_dataset': 's3://my-bucket/data/train/2024-Q1/',
        'training_instance': 'ml.m5.4xlarge',
        'training_duration_seconds': '1847'
    }
)

print(f"등록된 모델 ARN: {model_package['ModelPackageArn']}")
```

### 3. 승인 워크플로

모델의 프로덕션 배포 전 승인 프로세스를 관리합니다. 이는 ML 모델의 거버넌스와 규정 준수에 핵심적인 기능입니다.

```python
# 모델 승인 상태 업데이트
sm_client.update_model_package(
    ModelPackageArn='arn:aws:sagemaker:us-east-1:123456789012:model-package/customer-churn-prediction/2',
    ModelApprovalStatus='Approved',
    ApprovalDescription='모델 검증 완료 - 프로덕션 배포 승인. AUC-ROC 0.989, F1 0.947 달성.'
)
```

```bash
# 특정 그룹의 모든 모델 버전과 승인 상태 조회
aws sagemaker list-model-packages \
  --model-package-group-name "customer-churn-prediction" \
  --region us-east-1 \
  --sort-by CreationTime \
  --sort-order Descending \
  --query 'ModelPackageSummaryList[].{Version: ModelPackageVersion, Status: ModelApprovalStatus, Created: CreationTime}' \
  --output table

# 승인된 모델만 필터링
aws sagemaker list-model-packages \
  --model-package-group-name "customer-churn-prediction" \
  --model-approval-status Approved \
  --region us-east-1 \
  --output json
```

### 4. 모델 메타데이터 관리

Model Registry는 모델에 대한 풍부한 메타데이터를 저장하고 조회할 수 있습니다.

```python
# 모델 패키지 상세 정보 조회
model_detail = sm_client.describe_model_package(
    ModelPackageName='arn:aws:sagemaker:us-east-1:123456789012:model-package/customer-churn-prediction/2'
)

print(f"모델 버전: {model_detail['ModelPackageVersion']}")
print(f"승인 상태: {model_detail['ModelApprovalStatus']}")
print(f"생성 시간: {model_detail['CreationTime']}")
print(f"커스텀 메타데이터: {model_detail.get('CustomerMetadataProperties', {})}")
```

### 5. 크로스 계정 모델 공유

Model Registry는 AWS Organizations 또는 Resource Access Manager(RAM)를 통해 여러 AWS 계정 간에 모델을 공유할 수 있습니다.

```python
# 크로스 계정 접근을 위한 리소스 정책 설정
sm_client.put_model_package_group_policy(
    ModelPackageGroupName='customer-churn-prediction',
    ResourcePolicy=json.dumps({
        'Version': '2012-10-17',
        'Statement': [
            {
                'Sid': 'CrossAccountAccess',
                'Effect': 'Allow',
                'Principal': {
                    'AWS': 'arn:aws:iam::987654321098:root'
                },
                'Action': [
                    'sagemaker:DescribeModelPackageGroup',
                    'sagemaker:DescribeModelPackage',
                    'sagemaker:ListModelPackages',
                    'sagemaker:CreateModel'
                ],
                'Resource': 'arn:aws:sagemaker:us-east-1:123456789012:model-package-group/customer-churn-prediction'
            }
        ]
    })
)
```

## 아키텍처/동작 원리

### Model Registry의 내부 구조

Model Registry는 계층적 구조로 모델을 관리합니다.

```
Model Registry
  +-- Model Package Group: customer-churn-prediction
  |     +-- Model Package v1: XGBoost baseline (Rejected)
  |     +-- Model Package v2: XGBoost optimized (Approved)
  |     +-- Model Package v3: LightGBM experiment (PendingManualApproval)
  +-- Model Package Group: product-recommendation
  |     +-- Model Package v1: Collaborative filtering (Approved)
  |     +-- Model Package v2: Neural CF (PendingManualApproval)
```

각 모델 패키지는 다음 구성 요소를 포함합니다.

1. **InferenceSpecification**: 추론에 필요한 컨테이너 이미지, 모델 아티팩트 경로, 지원 인스턴스 타입
2. **ModelMetrics**: 모델 성능 메트릭 (정확도, AUC, F1 등)
3. **MetadataProperties**: 모델의 출처와 계보 정보
4. **CustomerMetadataProperties**: 사용자 정의 메타데이터
5. **ApprovalStatus**: 배포 승인 상태

### SageMaker Pipelines과의 통합 아키텍처

Model Registry는 SageMaker Pipelines과 깊게 통합되어, 훈련 파이프라인의 출력으로 자동 모델 등록이 가능합니다.

```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import TrainingStep, ProcessingStep
from sagemaker.workflow.model_step import ModelStep
from sagemaker.workflow.step_collections import RegisterModel

# 파이프라인에서 모델 등록 단계 정의
register_step = RegisterModel(
    name="RegisterChurnModel",
    estimator=xgb_estimator,
    model_data=training_step.properties.ModelArtifacts.S3ModelArtifacts,
    content_types=["text/csv"],
    response_types=["text/csv"],
    inference_instances=["ml.m5.xlarge", "ml.t2.medium"],
    transform_instances=["ml.m5.xlarge"],
    model_package_group_name="customer-churn-prediction",
    approval_status="PendingManualApproval",
    model_metrics=model_metrics
)

# 파이프라인 정의
pipeline = Pipeline(
    name="ChurnModelPipeline",
    steps=[processing_step, training_step, evaluation_step, register_step]
)
```

### 이벤트 기반 배포 자동화

Model Registry의 승인 상태 변경을 트리거로 활용하여 자동 배포 파이프라인을 구성할 수 있습니다.

```python
import boto3
import json

events_client = boto3.client('events')

# 모델 승인 시 자동 배포 트리거
events_client.put_rule(
    Name='model-approved-deploy',
    EventPattern=json.dumps({
        'source': ['aws.sagemaker'],
        'detail-type': ['SageMaker Model Package State Change'],
        'detail': {
            'ModelApprovalStatus': ['Approved'],
            'ModelPackageGroupName': ['customer-churn-prediction']
        }
    }),
    State='ENABLED'
)

# Lambda 함수를 배포 트리거로 연결
events_client.put_targets(
    Rule='model-approved-deploy',
    Targets=[{
        'Id': 'deploy-lambda',
        'Arn': 'arn:aws:lambda:us-east-1:123456789012:function:deploy-approved-model'
    }]
)
```

## 실전 활용

### 사례 1: 완전 자동화된 MLOps 파이프라인

훈련부터 배포까지 완전 자동화된 파이프라인에서 Model Registry의 역할을 살펴봅니다.

```python
import boto3
import json

lambda_client = boto3.client('lambda')

# 모델 배포 Lambda 함수
deploy_function_code = """
import boto3
import json

def handler(event, context):
    sm_client = boto3.client('sagemaker')
    
    # 이벤트에서 승인된 모델 패키지 ARN 추출
    model_package_arn = event['detail']['ModelPackageArn']
    
    # 모델 패키지 정보 조회
    model_pkg = sm_client.describe_model_package(
        ModelPackageName=model_package_arn
    )
    
    model_name = f"churn-model-{model_pkg['ModelPackageVersion']}"
    endpoint_config_name = f"churn-config-{model_pkg['ModelPackageVersion']}"
    
    # SageMaker 모델 생성
    sm_client.create_model(
        ModelName=model_name,
        PrimaryContainer={
            'ModelPackageName': model_package_arn
        },
        ExecutionRoleArn='arn:aws:iam::123456789012:role/SageMakerRole'
    )
    
    # 엔드포인트 설정 생성
    sm_client.create_endpoint_config(
        EndpointConfigName=endpoint_config_name,
        ProductionVariants=[{
            'VariantName': 'primary',
            'ModelName': model_name,
            'InstanceType': 'ml.m5.xlarge',
            'InitialInstanceCount': 1,
            'InitialVariantWeight': 1.0
        }]
    )
    
    # 엔드포인트 업데이트 (기존 엔드포인트가 있는 경우)
    try:
        sm_client.update_endpoint(
            EndpointName='churn-prediction-endpoint',
            EndpointConfigName=endpoint_config_name
        )
    except sm_client.exceptions.ClientError:
        sm_client.create_endpoint(
            EndpointName='churn-prediction-endpoint',
            EndpointConfigName=endpoint_config_name
        )
    
    return {'statusCode': 200, 'body': f'모델 {model_name} 배포 완료'}
"""
```

### 사례 2: 모델 계보(Lineage) 추적

Model Registry와 SageMaker Lineage Tracking을 결합하여 모델의 전체 계보를 추적합니다.

```python
from sagemaker.lineage.context import Context
from sagemaker.lineage.artifact import Artifact

# 모델의 계보 정보 조회
model_artifact = Artifact.list(
    source_uri=model_package['ModelPackageArn'],
    sagemaker_session=session
)

for artifact in model_artifact:
    print(f"아티팩트: {artifact.artifact_name}")
    print(f"유형: {artifact.artifact_type}")
    print(f"소스: {artifact.source.source_uri}")
    
    # 연관된 상위 아티팩트 (훈련 데이터, 코드 등) 조회
    associations = artifact.associations(direction='Ascendant')
    for assoc in associations:
        print(f"  <- {assoc.source_arn} ({assoc.association_type})")
```

```bash
# CLI로 모델 패키지의 태그 추가 (계보 추적용)
aws sagemaker add-tags \
  --resource-arn "arn:aws:sagemaker:us-east-1:123456789012:model-package/customer-churn-prediction/2" \
  --tags Key=TrainingJob,Value=xgboost-churn-2024-01-15 \
         Key=DatasetVersion,Value=2024-Q1 \
         Key=CodeCommit,Value=abc123def \
  --region us-east-1
```

### 사례 3: A/B 테스트를 위한 다중 모델 배포

Model Registry에서 여러 승인된 모델을 조회하여 A/B 테스트를 구성합니다.

```python
# 승인된 최신 2개 모델 조회
approved_models = sm_client.list_model_packages(
    ModelPackageGroupName='customer-churn-prediction',
    ModelApprovalStatus='Approved',
    SortBy='CreationTime',
    SortOrder='Descending',
    MaxResults=2
)

models = approved_models['ModelPackageSummaryList']

# A/B 테스트 엔드포인트 설정
sm_client.create_endpoint_config(
    EndpointConfigName='churn-ab-test-config',
    ProductionVariants=[
        {
            'VariantName': 'model-v2-champion',
            'ModelName': 'churn-model-v2',
            'InstanceType': 'ml.m5.xlarge',
            'InitialInstanceCount': 1,
            'InitialVariantWeight': 0.8  # 80% 트래픽
        },
        {
            'VariantName': 'model-v3-challenger',
            'ModelName': 'churn-model-v3',
            'InstanceType': 'ml.m5.xlarge',
            'InitialInstanceCount': 1,
            'InitialVariantWeight': 0.2  # 20% 트래픽
        }
    ]
)
```

## 모범 사례/보안

### 모델 거버넌스 모범 사례

1. **명확한 네이밍 규칙**: 모델 패키지 그룹과 버전에 일관된 네이밍 규칙을 적용합니다.

2. **풍부한 메타데이터 기록**: 훈련 데이터 버전, 하이퍼파라미터, 성능 메트릭, 코드 커밋 해시 등을 메타데이터로 기록합니다.

3. **승인 프로세스 의무화**: 프로덕션 배포 전 반드시 수동 또는 자동 승인 프로세스를 거치도록 합니다.

4. **감사 추적**: CloudTrail을 통해 모든 Model Registry 작업을 기록합니다.

### 보안 모범 사례

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DataScientistAccess",
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateModelPackage",
        "sagemaker:DescribeModelPackage",
        "sagemaker:ListModelPackages"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyApproval",
      "Effect": "Deny",
      "Action": [
        "sagemaker:UpdateModelPackage"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "sagemaker:ModelApprovalStatus": "Approved"
        }
      }
    }
  ]
}
```

위 정책은 데이터 과학자가 모델을 등록할 수 있지만, 승인 권한은 별도의 역할(ML 엔지니어 또는 관리자)에게만 부여하는 패턴입니다.

```bash
# Model Registry 관련 CloudTrail 이벤트 조회
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=UpdateModelPackage \
  --start-time "2024-01-01T00:00:00Z" \
  --end-time "2024-01-31T23:59:59Z" \
  --region us-east-1 \
  --output json
```

### 운영 모범 사례

1. **자동화된 모델 등록**: SageMaker Pipelines의 RegisterModel 스텝을 사용하여 훈련 완료 시 자동으로 모델을 등록합니다.
2. **성능 게이트**: 모델 등록 전 자동 평가를 수행하고, 기준 미달 시 등록을 차단합니다.
3. **롤백 전략**: 이전 승인된 모델 버전으로 빠르게 롤백할 수 있는 프로세스를 마련합니다.
4. **정기 정리**: 오래되었거나 Rejected된 모델 버전을 정기적으로 정리합니다.

## 관련 서비스 비교

### Model Registry vs MLflow Model Registry

| 항목 | SageMaker Model Registry | MLflow Model Registry |
|------|-------------------------|----------------------|
| 관리 방식 | 완전 관리형 | 셀프 호스팅/관리형 |
| AWS 통합 | 네이티브 | 추가 구성 필요 |
| 승인 워크플로 | 내장 | 커스텀 구현 필요 |
| 크로스 계정 | 지원 (IAM 기반) | 제한적 |
| 비용 | 무료 (저장/컴퓨팅 비용만) | 오픈소스 무료 |
| 멀티 클라우드 | AWS 전용 | 멀티 클라우드 지원 |

### Model Registry vs Amazon ECR (컨테이너 레지스트리)

| 항목 | Model Registry | ECR |
|------|---------------|-----|
| 대상 | ML 모델 아티팩트 | 컨테이너 이미지 |
| 메타데이터 | ML 특화 (메트릭, 계보) | 이미지 태그/다이제스트 |
| 승인 워크플로 | 내장 | 미지원 |
| 용도 | 모델 버전 관리 | 서빙 컨테이너 관리 |

### Model Registry vs DVC (Data Version Control)

| 항목 | Model Registry | DVC |
|------|---------------|-----|
| 접근 방식 | 서비스 기반 | Git 기반 |
| 데이터 버전 관리 | 모델 중심 | 데이터+모델 |
| 실험 추적 | 제한적 | 지원 (DVC Experiments) |
| 팀 협업 | AWS IAM 기반 | Git 기반 |

## 요약

Amazon SageMaker Model Registry는 ML 모델의 생명주기를 체계적으로 관리하기 위한 핵심 MLOps 도구입니다. 이 글의 핵심 내용을 정리하면 다음과 같습니다.

- Model Registry는 모델 패키지 그룹과 모델 패키지의 계층 구조로 모델 버전을 관리합니다.
- 승인 워크플로(Approved/Rejected/PendingManualApproval)를 통해 프로덕션 배포의 거버넌스를 확보합니다.
- SageMaker Pipelines과 통합하여 훈련 완료 시 자동으로 모델을 등록하고, 승인 시 자동으로 배포하는 파이프라인을 구축할 수 있습니다.
- 크로스 계정 모델 공유를 통해 개발/스테이징/프로덕션 환경 간 모델 이동을 안전하게 관리합니다.
- CloudTrail 감사, IAM 최소 권한, 역할 분리 등의 보안 모범 사례를 적용해야 합니다.
- A/B 테스트, 카나리 배포, 롤백 등의 배포 전략과 결합하여 안전한 모델 배포를 실현합니다.

Model Registry는 개별 도구로도 가치가 있지만, SageMaker Pipelines, Model Monitor, Feature Store 등 다른 SageMaker 서비스들과 결합될 때 완전한 MLOps 플랫폼으로서의 진가를 발휘합니다.