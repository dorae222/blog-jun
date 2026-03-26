# Amazon SageMaker Model Registry 개요 및 워크플로

## 개요

Amazon SageMaker Model Registry는 MLOps 파이프라인에서 모델 버전 관리와 배포 승인을 중앙에서 관리하는 서비스입니다. 이 글에서는 Model Registry의 전체적인 개념을 개요 수준에서 정리하고, 실제 프로젝트에서 모델 등록부터 프로덕션 배포까지의 워크플로를 단계별로 안내합니다.

ML 프로젝트에서 모델 관리는 다음과 같은 도전 과제를 수반합니다.

- 여러 실험에서 생성된 다수의 모델 버전을 어떻게 체계적으로 추적할 것인가
- 프로덕션에 배포할 모델을 누가, 어떤 기준으로 승인할 것인가
- 모델에 문제가 발생했을 때 어떻게 이전 버전으로 롤백할 것인가
- 개발 환경에서 검증된 모델을 스테이징/프로덕션 환경으로 어떻게 안전하게 전달할 것인가

Model Registry는 이러한 문제를 해결하기 위한 표준화된 워크플로를 제공합니다. 모델 패키지 그룹이라는 논리적 단위로 모델을 조직하고, 각 모델 버전에 대한 승인 상태를 관리하며, 이벤트 기반 자동화를 통해 배포를 트리거하는 체계를 갖추고 있습니다.

## 핵심 기능

### 1. 워크플로 전체 구조

Model Registry 기반의 표준 워크플로는 다음 다섯 단계로 구성됩니다.

**1단계: 모델 훈련 (Training)**

SageMaker Training Job, SageMaker Pipelines, 또는 외부 환경에서 모델을 훈련합니다. 훈련이 완료되면 모델 아티팩트가 S3에 저장됩니다.

**2단계: 모델 평가 (Evaluation)**

훈련된 모델의 성능을 평가합니다. 정확도, AUC-ROC, F1 Score 등의 메트릭을 측정하고, 베이스라인 성능과 비교합니다.

**3단계: 모델 등록 (Registration)**

평가를 통과한 모델을 Model Registry에 등록합니다. 모델 아티팩트, 추론 사양, 성능 메트릭, 커스텀 메타데이터를 함께 기록합니다.

**4단계: 모델 승인 (Approval)**

등록된 모델에 대한 승인 프로세스를 진행합니다. 자동 승인 또는 수동 승인 방식을 선택할 수 있습니다.

**5단계: 모델 배포 (Deployment)**

승인된 모델을 프로덕션 엔드포인트에 배포합니다. EventBridge 이벤트를 통해 자동으로 트리거될 수 있습니다.

### 2. 모델 패키지 그룹 설계

모델 패키지 그룹은 관련 모델 버전을 하나로 묶는 논리적 컨테이너입니다. 효과적인 그룹 설계 전략은 다음과 같습니다.

```python
import boto3

sm_client = boto3.client('sagemaker')

# 비즈니스 도메인별 모델 패키지 그룹 생성
groups = [
    {
        'name': 'fraud-detection-realtime',
        'description': '실시간 사기 탐지 모델 그룹',
        'tags': [{'Key': 'Domain', 'Value': 'risk'}, {'Key': 'UseCase', 'Value': 'fraud'}]
    },
    {
        'name': 'customer-churn-batch',
        'description': '고객 이탈 예측 배치 모델 그룹',
        'tags': [{'Key': 'Domain', 'Value': 'marketing'}, {'Key': 'UseCase', 'Value': 'churn'}]
    },
    {
        'name': 'product-recommendation',
        'description': '상품 추천 모델 그룹',
        'tags': [{'Key': 'Domain', 'Value': 'commerce'}, {'Key': 'UseCase', 'Value': 'recommendation'}]
    }
]

for group in groups:
    sm_client.create_model_package_group(
        ModelPackageGroupName=group['name'],
        ModelPackageGroupDescription=group['description'],
        Tags=group['tags']
    )
    print(f"그룹 생성 완료: {group['name']}")
```

```bash
# 생성된 모델 패키지 그룹 확인
aws sagemaker list-model-package-groups \
  --region us-east-1 \
  --sort-by CreationTime \
  --sort-order Descending \
  --output table
```

### 3. 자동 성능 게이트

모델 등록 전 성능 기준을 자동으로 검증하는 게이트 로직을 구현할 수 있습니다.

```python
def evaluate_and_register(model_artifact_uri, evaluation_results, group_name, min_metrics):
    """
    모델 성능을 평가하고 기준을 충족하면 Model Registry에 등록합니다.
    
    Args:
        model_artifact_uri: S3 모델 아티팩트 경로
        evaluation_results: 평가 결과 딕셔너리
        group_name: 모델 패키지 그룹 이름
        min_metrics: 최소 성능 기준 딕셔너리
    """
    sm_client = boto3.client('sagemaker')
    
    # 성능 게이트 검증
    gate_passed = True
    gate_messages = []
    
    for metric, threshold in min_metrics.items():
        actual = evaluation_results.get(metric, 0)
        if actual < threshold:
            gate_passed = False
            gate_messages.append(
                f"{metric}: 실제값 {actual:.4f} < 기준값 {threshold:.4f}"
            )
    
    if not gate_passed:
        print(f"성능 게이트 미통과: {'; '.join(gate_messages)}")
        return None
    
    # 성능 기준 충족 시 모델 등록
    response = sm_client.create_model_package(
        ModelPackageGroupName=group_name,
        ModelPackageDescription=f'자동 등록 - 모든 성능 게이트 통과',
        InferenceSpecification={
            'Containers': [{
                'Image': '683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-xgboost:1.7-1',
                'ModelDataUrl': model_artifact_uri
            }],
            'SupportedTransformInstanceTypes': ['ml.m5.xlarge'],
            'SupportedRealtimeInferenceInstanceTypes': ['ml.m5.xlarge'],
            'SupportedContentTypes': ['text/csv'],
            'SupportedResponseMIMETypes': ['text/csv']
        },
        ModelApprovalStatus='PendingManualApproval',
        CustomerMetadataProperties={
            k: str(v) for k, v in evaluation_results.items()
        }
    )
    
    print(f"모델 등록 완료: {response['ModelPackageArn']}")
    return response['ModelPackageArn']

# 사용 예시
evaluation_results = {
    'accuracy': 0.9523,
    'auc_roc': 0.9891,
    'f1_score': 0.9467,
    'precision': 0.9512,
    'recall': 0.9423
}

min_metrics = {
    'accuracy': 0.90,
    'auc_roc': 0.95,
    'f1_score': 0.90
}

model_arn = evaluate_and_register(
    model_artifact_uri='s3://my-bucket/models/xgboost/model.tar.gz',
    evaluation_results=evaluation_results,
    group_name='fraud-detection-realtime',
    min_metrics=min_metrics
)
```

### 4. 승인 워크플로 설계

승인 프로세스는 자동 승인과 수동 승인 두 가지 방식으로 구성할 수 있습니다.

**자동 승인**: 성능 메트릭이 사전 정의된 기준을 모두 충족하면 자동으로 승인합니다. 빠른 반복이 필요한 개발/스테이징 환경에 적합합니다.

**수동 승인**: 담당자가 모델의 성능, 공정성, 설명 가능성 등을 검토한 후 수동으로 승인합니다. 규제가 엄격한 프로덕션 환경에 적합합니다.

```python
# 수동 승인 프로세스
def review_and_approve(model_package_arn, reviewer, approval_notes):
    sm_client = boto3.client('sagemaker')
    
    # 모델 패키지 상세 정보 조회
    model_pkg = sm_client.describe_model_package(
        ModelPackageName=model_package_arn
    )
    
    print("=== 모델 검토 정보 ===")
    print(f"모델 버전: {model_pkg['ModelPackageVersion']}")
    print(f"현재 상태: {model_pkg['ModelApprovalStatus']}")
    print(f"메타데이터: {model_pkg.get('CustomerMetadataProperties', {})}")
    
    # 승인 처리
    sm_client.update_model_package(
        ModelPackageArn=model_package_arn,
        ModelApprovalStatus='Approved',
        ApprovalDescription=f'검토자: {reviewer}. {approval_notes}'
    )
    
    print(f"모델 승인 완료: {model_package_arn}")
```

```bash
# 승인 대기 중인 모델 목록 조회
aws sagemaker list-model-packages \
  --model-package-group-name "fraud-detection-realtime" \
  --model-approval-status PendingManualApproval \
  --region us-east-1 \
  --query 'ModelPackageSummaryList[].{ARN: ModelPackageArn, Version: ModelPackageVersion, Created: CreationTime}' \
  --output table

# 모델 승인 처리
aws sagemaker update-model-package \
  --model-package-arn "arn:aws:sagemaker:us-east-1:123456789012:model-package/fraud-detection-realtime/3" \
  --model-approval-status Approved \
  --approval-description "프로덕션 배포 승인 - 성능 기준 충족 확인" \
  --region us-east-1
```

## 아키텍처/동작 원리

### 전체 워크플로 아키텍처

Model Registry 기반의 전체 MLOps 워크플로는 다음과 같은 아키텍처로 구성됩니다.

```
[데이터 준비] -> [모델 훈련] -> [모델 평가] -> [성능 게이트]
                                                    |
                                              (기준 충족?)
                                              /          \
                                          Yes              No
                                           |                |
                                    [Model Registry     [알림/로그]
                                     에 등록]                
                                           |
                                    [승인 대기]
                                           |
                                    (승인됨?)
                                    /        \
                                Yes            No
                                 |              |
                          [EventBridge     [Rejected
                           이벤트 발생]     로그 기록]
                                 |
                          [배포 Lambda
                           트리거]
                                 |
                          [SageMaker
                           엔드포인트 배포]
                                 |
                          [Model Monitor
                           모니터링 시작]
```

### 이벤트 기반 자동화 메커니즘

Model Registry의 상태 변경은 Amazon EventBridge 이벤트를 발생시킵니다. 이 이벤트를 활용하여 다양한 자동화를 구현할 수 있습니다.

발생되는 주요 이벤트는 다음과 같습니다.

- **ModelPackageGroup 이벤트**: 그룹 생성/삭제
- **ModelPackage 이벤트**: 모델 등록, 승인 상태 변경, 삭제

```python
import boto3
import json

events_client = boto3.client('events')

# 승인 상태 변경 이벤트 패턴
event_pattern = {
    'source': ['aws.sagemaker'],
    'detail-type': ['SageMaker Model Package State Change'],
    'detail': {
        'ModelApprovalStatus': ['Approved']
    }
}

# EventBridge 규칙 생성
events_client.put_rule(
    Name='model-approval-trigger',
    EventPattern=json.dumps(event_pattern),
    State='ENABLED',
    Description='모델 승인 시 자동 배포 트리거'
)

# 대상 설정 (Lambda, StepFunctions, CodePipeline 등)
events_client.put_targets(
    Rule='model-approval-trigger',
    Targets=[
        {
            'Id': 'deploy-pipeline',
            'Arn': 'arn:aws:states:us-east-1:123456789012:stateMachine:ModelDeployPipeline',
            'RoleArn': 'arn:aws:iam::123456789012:role/EventBridgeRole'
        }
    ]
)
```

### 크로스 계정 배포 아키텍처

엔터프라이즈 환경에서는 개발/스테이징/프로덕션 환경이 별도의 AWS 계정으로 분리되어 있는 경우가 많습니다. Model Registry는 크로스 계정 모델 공유를 지원합니다.

```
[개발 계정]              [스테이징 계정]         [프로덕션 계정]
 Model Registry   --->   모델 참조/배포   --->   모델 참조/배포
 (모델 등록)              (통합 테스트)            (프로덕션 서빙)
```

```bash
# 개발 계정에서 리소스 정책 설정 (크로스 계정 접근 허용)
aws sagemaker put-model-package-group-policy \
  --model-package-group-name "fraud-detection-realtime" \
  --resource-policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "CrossAccountDeployAccess",
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::111111111111:root",
          "arn:aws:iam::222222222222:root"
        ]
      },
      "Action": [
        "sagemaker:DescribeModelPackageGroup",
        "sagemaker:DescribeModelPackage",
        "sagemaker:ListModelPackages"
      ],
      "Resource": "arn:aws:sagemaker:us-east-1:123456789012:model-package-group/fraud-detection-realtime"
    }]
  }' \
  --region us-east-1
```

## 실전 활용

### 사례 1: SageMaker Pipelines 통합 워크플로

SageMaker Pipelines에 Model Registry를 통합한 전체 워크플로 구현입니다.

```python
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import TrainingStep, ProcessingStep
from sagemaker.workflow.step_collections import RegisterModel
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.functions import JsonGet
from sagemaker.workflow.parameters import ParameterFloat, ParameterString

# 파이프라인 파라미터 정의
min_accuracy = ParameterFloat(name="MinAccuracy", default_value=0.90)
model_group = ParameterString(name="ModelGroup", default_value="fraud-detection-realtime")

# 조건부 모델 등록 (성능 기준 충족 시에만)
condition = ConditionGreaterThanOrEqualTo(
    left=JsonGet(
        step_name="EvaluateModel",
        property_file=evaluation_report,
        json_path="metrics.accuracy.value"
    ),
    right=min_accuracy
)

# 모델 등록 단계
register_step = RegisterModel(
    name="RegisterModel",
    estimator=estimator,
    model_data=training_step.properties.ModelArtifacts.S3ModelArtifacts,
    content_types=["text/csv"],
    response_types=["text/csv"],
    inference_instances=["ml.m5.xlarge"],
    transform_instances=["ml.m5.xlarge"],
    model_package_group_name=model_group,
    approval_status="PendingManualApproval"
)

# 조건부 실행 단계
condition_step = ConditionStep(
    name="CheckAccuracy",
    conditions=[condition],
    if_steps=[register_step],
    else_steps=[]  # 기준 미달 시 등록하지 않음
)

# 파이프라인 생성
pipeline = Pipeline(
    name="FraudDetectionPipeline",
    parameters=[min_accuracy, model_group],
    steps=[processing_step, training_step, evaluation_step, condition_step]
)

pipeline.upsert(role_arn=role)
```

### 사례 2: 롤백 프로세스 자동화

프로덕션에서 문제가 발생했을 때 이전 버전으로 자동 롤백하는 프로세스입니다.

```python
def rollback_to_previous_version(group_name, endpoint_name):
    """
    현재 프로덕션 모델에 문제가 있을 때 이전 승인된 버전으로 롤백합니다.
    """
    sm_client = boto3.client('sagemaker')
    
    # 승인된 모델 목록 조회 (최신순)
    approved_models = sm_client.list_model_packages(
        ModelPackageGroupName=group_name,
        ModelApprovalStatus='Approved',
        SortBy='CreationTime',
        SortOrder='Descending',
        MaxResults=5
    )['ModelPackageSummaryList']
    
    if len(approved_models) < 2:
        print("롤백할 이전 버전이 없습니다.")
        return
    
    # 현재 버전(첫 번째)을 건너뛰고 이전 버전(두 번째) 사용
    rollback_model_arn = approved_models[1]['ModelPackageArn']
    rollback_version = approved_models[1]['ModelPackageVersion']
    
    print(f"롤백 대상 모델: 버전 {rollback_version} ({rollback_model_arn})")
    
    # 롤백 모델로 엔드포인트 업데이트
    model_name = f"{group_name}-rollback-v{rollback_version}"
    config_name = f"{group_name}-rollback-config-v{rollback_version}"
    
    # 모델 생성
    sm_client.create_model(
        ModelName=model_name,
        PrimaryContainer={'ModelPackageName': rollback_model_arn},
        ExecutionRoleArn='arn:aws:iam::123456789012:role/SageMakerRole'
    )
    
    # 엔드포인트 설정 생성
    sm_client.create_endpoint_config(
        EndpointConfigName=config_name,
        ProductionVariants=[{
            'VariantName': 'rollback',
            'ModelName': model_name,
            'InstanceType': 'ml.m5.xlarge',
            'InitialInstanceCount': 1
        }]
    )
    
    # 엔드포인트 업데이트
    sm_client.update_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=config_name
    )
    
    print(f"롤백 완료: {endpoint_name} -> 버전 {rollback_version}")
```

```bash
# 현재 엔드포인트에 배포된 모델 확인
aws sagemaker describe-endpoint \
  --endpoint-name "fraud-detection-endpoint" \
  --region us-east-1 \
  --query '{Status: EndpointStatus, Config: EndpointConfigName, LastModified: LastModifiedTime}'
```

### 사례 3: 모델 비교 대시보드 데이터 생성

여러 모델 버전의 성능을 비교하는 데이터를 생성합니다.

```python
def generate_model_comparison(group_name):
    sm_client = boto3.client('sagemaker')
    
    models = sm_client.list_model_packages(
        ModelPackageGroupName=group_name,
        SortBy='CreationTime',
        SortOrder='Descending',
        MaxResults=10
    )['ModelPackageSummaryList']
    
    comparison_data = []
    for model_summary in models:
        detail = sm_client.describe_model_package(
            ModelPackageName=model_summary['ModelPackageArn']
        )
        
        metadata = detail.get('CustomerMetadataProperties', {})
        comparison_data.append({
            'version': detail['ModelPackageVersion'],
            'status': detail['ModelApprovalStatus'],
            'created': str(detail['CreationTime']),
            'accuracy': metadata.get('accuracy', 'N/A'),
            'auc_roc': metadata.get('auc_roc', 'N/A'),
            'f1_score': metadata.get('f1_score', 'N/A'),
            'description': detail.get('ModelPackageDescription', '')
        })
    
    return comparison_data

# 사용 예시
comparison = generate_model_comparison('fraud-detection-realtime')
for model in comparison:
    print(f"v{model['version']} [{model['status']}] "
          f"acc={model['accuracy']} auc={model['auc_roc']} f1={model['f1_score']}")
```

## 모범 사례/보안

### 워크플로 설계 모범 사례

1. **환경별 승인 전략 분리**: 개발 환경에서는 자동 승인을, 프로덕션 환경에서는 수동 승인을 적용합니다.

2. **성능 게이트 의무화**: 모델 등록 전 자동화된 성능 평가를 반드시 거치도록 파이프라인을 설계합니다.

3. **메타데이터 표준화**: 팀 전체에서 일관된 메타데이터 스키마를 사용합니다.

```python
# 표준 메타데이터 스키마 예시
standard_metadata = {
    'algorithm': 'xgboost',
    'framework_version': '1.7.1',
    'training_dataset_uri': 's3://bucket/data/v3/',
    'training_dataset_hash': 'sha256:abc123...',
    'training_instance_type': 'ml.m5.4xlarge',
    'training_duration_seconds': '1847',
    'accuracy': '0.9523',
    'auc_roc': '0.9891',
    'f1_score': '0.9467',
    'code_repository': 'https://github.com/org/repo',
    'code_commit': 'abc123def456',
    'author': 'team-data-science'
}
```

4. **롤백 계획 수립**: 모든 프로덕션 배포에 대해 롤백 절차를 사전에 준비합니다.

5. **정기 감사**: 등록된 모델의 상태와 사용 현황을 정기적으로 감사합니다.

### 보안 구성

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "RegisterModels",
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateModelPackage",
        "sagemaker:DescribeModelPackage",
        "sagemaker:ListModelPackages"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/Role": "data-scientist"
        }
      }
    },
    {
      "Sid": "ApproveModels",
      "Effect": "Allow",
      "Action": "sagemaker:UpdateModelPackage",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/Role": "ml-lead"
        }
      }
    },
    {
      "Sid": "DeployModels",
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateModel",
        "sagemaker:CreateEndpointConfig",
        "sagemaker:CreateEndpoint",
        "sagemaker:UpdateEndpoint"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/Role": "ml-engineer"
        }
      }
    }
  ]
}
```

```bash
# CloudTrail로 모델 승인 이력 감사
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=UpdateModelPackage \
  --region us-east-1 \
  --max-results 20 \
  --output json
```

## 관련 서비스 비교

### 워크플로 자동화 도구 비교

| 항목 | Model Registry + EventBridge | SageMaker Pipelines | AWS Step Functions |
|------|---------------------------|--------------------|-----------------|
| 트리거 | 이벤트 기반 | 스케줄/수동 | 이벤트/API |
| 복잡도 | 낮음 | 중간 | 높음 |
| 유연성 | 제한적 | ML 특화 | 범용적 |
| 시각화 | CloudWatch | Studio Pipeline UI | Step Functions 콘솔 |
| 적합한 사용 사례 | 간단한 배포 자동화 | ML 파이프라인 | 복잡한 오케스트레이션 |

### 모델 승인 방식 비교

| 방식 | 장점 | 단점 | 적합한 환경 |
|------|------|------|------------|
| 자동 승인 | 빠른 반복 | 거버넌스 부족 | 개발/실험 |
| 수동 승인 | 높은 통제력 | 병목 발생 가능 | 프로덕션/규제 |
| 조건부 자동 | 균형잡힌 접근 | 구현 복잡 | 스테이징 |

## 요약

Amazon SageMaker Model Registry의 워크플로를 정리하면 다음과 같습니다.

- 표준 워크플로는 훈련, 평가, 등록, 승인, 배포의 5단계로 구성됩니다.
- 모델 패키지 그룹을 비즈니스 도메인이나 사용 사례별로 설계하면 관리 효율성이 높아집니다.
- 성능 게이트를 모델 등록 전에 배치하여, 기준 미달 모델이 Registry에 등록되는 것을 방지합니다.
- EventBridge 이벤트를 활용하면 승인 상태 변경 시 자동으로 배포 파이프라인을 트리거할 수 있습니다.
- 크로스 계정 아키텍처를 통해 개발/스테이징/프로덕션 환경 간 안전한 모델 이동이 가능합니다.
- IAM 역할 분리를 통해 등록(데이터 과학자), 승인(ML 리드), 배포(ML 엔지니어) 권한을 분리합니다.
- 롤백 프로세스를 사전에 준비하여, 프로덕션 문제 발생 시 신속하게 이전 버전으로 복구할 수 있어야 합니다.

Model Registry 기반 워크플로는 ML 모델의 신뢰성과 재현성을 보장하는 핵심 인프라이며, 규모가 커질수록 그 가치가 더욱 분명해집니다.