<!-- infographic-hero -->
![Amazon SageMaker Real-time Inference 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker Real-time Inference 한 장 요약 인포그래픽*

# Amazon SageMaker Real-time Inference

## 개요

Amazon SageMaker Real-time Inference는 ML 모델을 실시간 추론 엔드포인트로 배포하여, 밀리초 수준의 지연 시간으로 예측 결과를 반환하는 서비스입니다. 웹 애플리케이션, 모바일 앱, IoT 디바이스 등에서 즉시 응답이 필요한 ML 추론 워크로드에 최적화되어 있습니다.

실시간 추론은 ML 모델을 비즈니스에 적용하는 가장 일반적인 패턴입니다. 사용자가 상품을 검색하면 즉시 추천 결과를 보여주거나, 금융 거래가 발생하면 실시간으로 사기 여부를 판단하거나, 이미지를 업로드하면 바로 분류 결과를 반환하는 것이 모두 실시간 추론의 사례입니다.

SageMaker Real-time Inference는 다음과 같은 핵심 요소로 구성됩니다.

- **SageMaker Model**: 모델 아티팩트와 추론 컨테이너를 정의합니다.
- **Endpoint Configuration**: 인스턴스 타입, 인스턴스 수, 모델 변형(Variant) 등 배포 설정을 정의합니다.
- **Endpoint**: 실제 트래픽을 처리하는 실행 단위입니다. HTTPS REST API로 접근합니다.

## 핵심 기능

### 1. 엔드포인트 배포

모델을 실시간 추론 엔드포인트로 배포하는 기본 과정입니다.

```python
import sagemaker
from sagemaker.pytorch import PyTorchModel

session = sagemaker.Session()
role = sagemaker.get_execution_role()

# PyTorch 모델 정의
model = PyTorchModel(
    model_data='s3://my-bucket/models/classification/model.tar.gz',
    role=role,
    framework_version='2.0',
    py_version='py310',
    entry_point='inference.py',
    source_dir='./src'
)

# 실시간 엔드포인트 배포
predictor = model.deploy(
    initial_instance_count=2,
    instance_type='ml.g4dn.xlarge',
    endpoint_name='realtime-classification',
    wait=True
)

# 추론 테스트
import json
result = predictor.predict(
    json.dumps({"inputs": "AWS SageMaker는 ML 모델 배포 서비스입니다."}),
    initial_args={"ContentType": "application/json"}
)
print(result)
```

```bash
# 엔드포인트 상태 확인
aws sagemaker describe-endpoint \
  --endpoint-name "realtime-classification" \
  --region us-east-1 \
  --query '{Status: EndpointStatus, Variants: ProductionVariants[].{Name: VariantName, Instance: CurrentInstanceCount, Weight: CurrentWeight}}'

# 엔드포인트 목록 조회
aws sagemaker list-endpoints \
  --status-equals InService \
  --region us-east-1 \
  --sort-by CreationTime \
  --sort-order Descending \
  --output table
```

### 2. 프로덕션 변형(Production Variants)

하나의 엔드포인트에 여러 모델 변형을 배포하여 A/B 테스트나 카나리 배포를 수행할 수 있습니다.

```python
import boto3

sm_client = boto3.client('sagemaker')

# 두 개의 모델 변형을 포함한 엔드포인트 설정
sm_client.create_endpoint_config(
    EndpointConfigName='ab-test-config',
    ProductionVariants=[
        {
            'VariantName': 'model-v1-champion',
            'ModelName': 'classification-model-v1',
            'InstanceType': 'ml.g4dn.xlarge',
            'InitialInstanceCount': 2,
            'InitialVariantWeight': 0.9  # 90% 트래픽
        },
        {
            'VariantName': 'model-v2-challenger',
            'ModelName': 'classification-model-v2',
            'InstanceType': 'ml.g4dn.xlarge',
            'InitialInstanceCount': 1,
            'InitialVariantWeight': 0.1  # 10% 트래픽
        }
    ]
)

# 엔드포인트 생성
sm_client.create_endpoint(
    EndpointName='ab-test-endpoint',
    EndpointConfigName='ab-test-config'
)
```

트래픽 비율을 동적으로 조정할 수도 있습니다.

```bash
# 트래픽 비율 변경 (v2를 50%로 증가)
aws sagemaker update-endpoint-weights-and-capacities \
  --endpoint-name "ab-test-endpoint" \
  --desired-weights-and-capacities '[
    {"VariantName": "model-v1-champion", "DesiredWeight": 50},
    {"VariantName": "model-v2-challenger", "DesiredWeight": 50}
  ]' \
  --region us-east-1
```

### 3. 오토스케일링

트래픽 변동에 따라 자동으로 인스턴스를 확장/축소하는 오토스케일링을 설정할 수 있습니다.

```bash
# 오토스케일링 대상 등록
aws application-autoscaling register-scalable-target \
  --service-namespace sagemaker \
  --resource-id "endpoint/realtime-classification/variant/AllTraffic" \
  --scalable-dimension "sagemaker:variant:DesiredInstanceCount" \
  --min-capacity 2 \
  --max-capacity 10 \
  --region us-east-1

# 대상 추적 스케일링 정책 (평균 호출 수 기준)
aws application-autoscaling put-scaling-policy \
  --service-namespace sagemaker \
  --resource-id "endpoint/realtime-classification/variant/AllTraffic" \
  --scalable-dimension "sagemaker:variant:DesiredInstanceCount" \
  --policy-name "invocations-scaling" \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 1000,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }' \
  --region us-east-1
```

### 4. 멀티 모델 엔드포인트(Multi-Model Endpoint)

하나의 엔드포인트에 수백~수천 개의 모델을 호스팅하여 비용을 절감할 수 있습니다. 요청 시 해당 모델이 메모리에 로드되고, 사용하지 않는 모델은 자동으로 언로드됩니다.

```python
from sagemaker.multidatamodel import MultiDataModel

# 멀티 모델 엔드포인트 설정
multi_model = MultiDataModel(
    name='multi-tenant-models',
    model_data_prefix='s3://my-bucket/multi-models/',
    model=base_model,
    sagemaker_session=session
)

# 배포
predictor = multi_model.deploy(
    initial_instance_count=2,
    instance_type='ml.g4dn.xlarge',
    endpoint_name='multi-model-endpoint'
)

# 특정 모델로 추론
result = predictor.predict(
    data=input_data,
    target_model='tenant-a/model.tar.gz'  # 특정 테넌트의 모델 지정
)
```

### 5. 추론 파이프라인(Inference Pipeline)

여러 컨테이너를 체이닝하여 전처리 -> 추론 -> 후처리를 하나의 엔드포인트에서 수행할 수 있습니다.

```python
from sagemaker.pipeline import PipelineModel
from sagemaker.sklearn.model import SKLearnModel
from sagemaker.pytorch import PyTorchModel

# 전처리 모델 (Scikit-learn)
preprocessor = SKLearnModel(
    model_data='s3://my-bucket/models/preprocessor/model.tar.gz',
    role=role,
    framework_version='1.2-1',
    entry_point='preprocessor.py'
)

# 추론 모델 (PyTorch)
inference_model = PyTorchModel(
    model_data='s3://my-bucket/models/classifier/model.tar.gz',
    role=role,
    framework_version='2.0',
    py_version='py310',
    entry_point='inference.py'
)

# 파이프라인 모델 생성
pipeline_model = PipelineModel(
    name='preprocessing-inference-pipeline',
    role=role,
    models=[preprocessor, inference_model],
    sagemaker_session=session
)

# 배포
predictor = pipeline_model.deploy(
    initial_instance_count=1,
    instance_type='ml.g4dn.xlarge',
    endpoint_name='pipeline-endpoint'
)
```

## 아키텍처/동작 원리

### 엔드포인트 내부 아키텍처

SageMaker 실시간 추론 엔드포인트는 다음과 같은 내부 구조를 가집니다.

```
[클라이언트 요청]
      |
[SageMaker Runtime API] -- InvokeEndpoint
      |
[Load Balancer] -- 트래픽 분산
      |
[Production Variant(s)]
      |
[ML Instance 1] [ML Instance 2] ... [ML Instance N]
      |              |                    |
[Container]    [Container]          [Container]
      |              |                    |
[Model Server] [Model Server]      [Model Server]
      |              |                    |
[Model Artifact] [Model Artifact]  [Model Artifact]
```

### 요청 처리 흐름

1. **클라이언트**: `InvokeEndpoint` API를 호출합니다.
2. **SageMaker Runtime**: 요청을 인증하고, 적절한 엔드포인트로 라우팅합니다.
3. **로드 밸런서**: Production Variant 가중치에 따라 트래픽을 분산합니다.
4. **컨테이너**: 모델 서버가 요청을 받아 추론을 수행합니다.
5. **응답**: 추론 결과를 클라이언트에 반환합니다.

### 추론 컨테이너 구조

```python
# inference.py - 커스텀 추론 스크립트의 표준 구조
import torch
import json
import os

def model_fn(model_dir):
    """모델 로드 (인스턴스 시작 시 1회 실행)"""
    model = torch.load(os.path.join(model_dir, 'model.pth'))
    model.eval()
    return model

def input_fn(request_body, request_content_type):
    """요청 데이터 역직렬화"""
    if request_content_type == 'application/json':
        data = json.loads(request_body)
        return torch.tensor(data['inputs'])
    raise ValueError(f"지원하지 않는 Content-Type: {request_content_type}")

def predict_fn(input_data, model):
    """추론 실행"""
    with torch.no_grad():
        output = model(input_data)
    return output

def output_fn(prediction, accept):
    """응답 데이터 직렬화"""
    if accept == 'application/json':
        return json.dumps({
            'predictions': prediction.numpy().tolist()
        })
    raise ValueError(f"지원하지 않는 Accept: {accept}")
```

### Shadow 테스트

SageMaker는 Shadow 변형을 통해 실제 프로덕션 트래픽을 미러링하여 새 모델을 테스트할 수 있습니다.

```python
# Shadow 변형이 포함된 엔드포인트 설정
sm_client.create_endpoint_config(
    EndpointConfigName='shadow-test-config',
    ProductionVariants=[
        {
            'VariantName': 'production',
            'ModelName': 'model-v1',
            'InstanceType': 'ml.g4dn.xlarge',
            'InitialInstanceCount': 2
        }
    ],
    ShadowProductionVariants=[
        {
            'VariantName': 'shadow-v2',
            'ModelName': 'model-v2',
            'InstanceType': 'ml.g4dn.xlarge',
            'InitialInstanceCount': 1,
            'SamplingPercentage': 50  # 50% 트래픽 미러링
        }
    ]
)
```

## 실전 활용

### 사례 1: 고가용성 추론 엔드포인트 배포

프로덕션 환경에서의 고가용성 배포 전략입니다.

```python
import boto3

sm_client = boto3.client('sagemaker')

# 다중 가용 영역 배포를 위한 설정
sm_client.create_endpoint_config(
    EndpointConfigName='ha-inference-config',
    ProductionVariants=[
        {
            'VariantName': 'primary',
            'ModelName': 'fraud-detection-model',
            'InstanceType': 'ml.g4dn.xlarge',
            'InitialInstanceCount': 3,  # 3개 인스턴스로 고가용성 확보
            'InitialVariantWeight': 1.0,
            'RoutingConfig': {
                'RoutingStrategy': 'LEAST_OUTSTANDING_REQUESTS'
            }
        }
    ],
    DataCaptureConfig={
        'EnableCapture': True,
        'InitialSamplingPercentage': 20,
        'DestinationS3Uri': 's3://my-bucket/data-capture/',
        'CaptureOptions': [
            {'CaptureMode': 'Input'},
            {'CaptureMode': 'Output'}
        ],
        'CaptureContentTypeHeader': {
            'CsvContentTypes': ['text/csv'],
            'JsonContentTypes': ['application/json']
        }
    }
)

sm_client.create_endpoint(
    EndpointName='ha-fraud-detection',
    EndpointConfigName='ha-inference-config'
)
```

### 사례 2: 추론 성능 모니터링 및 최적화

```python
import boto3
from datetime import datetime, timedelta

cw_client = boto3.client('cloudwatch')

# 엔드포인트 지연 시간 메트릭 조회
response = cw_client.get_metric_statistics(
    Namespace='AWS/SageMaker',
    MetricName='ModelLatency',
    Dimensions=[
        {'Name': 'EndpointName', 'Value': 'ha-fraud-detection'},
        {'Name': 'VariantName', 'Value': 'primary'}
    ],
    StartTime=datetime.utcnow() - timedelta(hours=24),
    EndTime=datetime.utcnow(),
    Period=300,  # 5분 간격
    Statistics=['Average', 'p50', 'p99']
)

for point in sorted(response['Datapoints'], key=lambda x: x['Timestamp']):
    print(f"시간: {point['Timestamp']}, "
          f"평균: {point['Average']/1000:.1f}ms, "
          f"P99: {point.get('ExtendedStatistics', {}).get('p99', 0)/1000:.1f}ms")
```

```bash
# CloudWatch 대시보드에서 확인할 주요 메트릭
# 1. 모델 지연 시간
aws cloudwatch get-metric-statistics \
  --namespace "AWS/SageMaker" \
  --metric-name "ModelLatency" \
  --dimensions Name=EndpointName,Value=ha-fraud-detection Name=VariantName,Value=primary \
  --start-time $(date -u -v-1H +"%Y-%m-%dT%H:%M:%SZ") \
  --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --period 300 \
  --statistics Average \
  --region us-east-1

# 2. 호출 횟수
aws cloudwatch get-metric-statistics \
  --namespace "AWS/SageMaker" \
  --metric-name "Invocations" \
  --dimensions Name=EndpointName,Value=ha-fraud-detection Name=VariantName,Value=primary \
  --start-time $(date -u -v-1H +"%Y-%m-%dT%H:%M:%SZ") \
  --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --period 300 \
  --statistics Sum \
  --region us-east-1
```

### 사례 3: 블루/그린 배포

무중단 모델 업데이트를 위한 블루/그린 배포 전략입니다.

```python
def blue_green_deploy(endpoint_name, new_model_name, new_instance_type, new_instance_count):
    sm_client = boto3.client('sagemaker')
    
    # 새 엔드포인트 설정 생성 (그린)
    new_config_name = f"{endpoint_name}-green-{int(time.time())}"
    
    sm_client.create_endpoint_config(
        EndpointConfigName=new_config_name,
        ProductionVariants=[{
            'VariantName': 'AllTraffic',
            'ModelName': new_model_name,
            'InstanceType': new_instance_type,
            'InitialInstanceCount': new_instance_count
        }]
    )
    
    # 엔드포인트 업데이트 (블루 -> 그린 전환)
    sm_client.update_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=new_config_name,
        RetainAllVariantProperties=False,
        DeploymentConfig={
            'BlueGreenUpdatePolicy': {
                'TrafficRoutingConfiguration': {
                    'Type': 'CANARY',
                    'CanarySize': {
                        'Type': 'INSTANCE_COUNT',
                        'Value': 1
                    },
                    'WaitIntervalInSeconds': 300  # 5분 카나리 테스트
                },
                'TerminationWaitInSeconds': 120,
                'MaximumExecutionTimeoutInSeconds': 1800
            },
            'AutoRollbackConfiguration': {
                'Alarms': [
                    {
                        'AlarmName': f'{endpoint_name}-high-error-rate'
                    }
                ]
            }
        }
    )
    
    print(f"블루/그린 배포 시작: {endpoint_name} -> {new_model_name}")
```

## 모범 사례/보안

### 성능 최적화 모범 사례

1. **적절한 인스턴스 선택**: 모델 크기와 추론 패턴에 맞는 인스턴스를 선택합니다.
2. **배치 추론 활용**: 가능한 경우 여러 요청을 배치로 처리하여 처리량을 향상시킵니다.
3. **모델 최적화**: SageMaker Neo, TensorRT 등을 활용하여 추론 속도를 높입니다.
4. **연결 재사용**: Keep-Alive 연결을 사용하여 연결 오버헤드를 줄입니다.
5. **컨테이너 워밍업**: 모델 로드 시간을 최소화하기 위해 컨테이너 사전 워밍업을 활용합니다.

### 보안 모범 사례

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeEndpointOnly",
      "Effect": "Allow",
      "Action": "sagemaker:InvokeEndpoint",
      "Resource": "arn:aws:sagemaker:us-east-1:123456789012:endpoint/ha-fraud-detection"
    },
    {
      "Sid": "DenyPublicEndpoint",
      "Effect": "Deny",
      "Action": "sagemaker:CreateEndpoint",
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "sagemaker:VpcSubnets": "true"
        }
      }
    }
  ]
}
```

- VPC Endpoint(PrivateLink)를 통해 인터넷을 거치지 않고 엔드포인트를 호출합니다.
- 모든 추론 요청은 TLS로 암호화됩니다.
- IAM 정책으로 엔드포인트 호출 권한을 세밀하게 제어합니다.

### 비용 최적화

```bash
# 엔드포인트별 비용 분석을 위한 태그 확인
aws sagemaker list-tags \
  --resource-arn "arn:aws:sagemaker:us-east-1:123456789012:endpoint/ha-fraud-detection" \
  --region us-east-1
```

- Savings Plans를 활용하여 장기 사용 엔드포인트의 비용을 절감합니다.
- 트래픽이 적은 시간대에 인스턴스 수를 줄이는 스케줄링 기반 스케일링을 적용합니다.
- 멀티 모델 엔드포인트를 활용하여 여러 모델의 인프라를 공유합니다.

## 관련 서비스 비교

### SageMaker 추론 옵션 비교

| 항목 | Real-time Inference | Serverless Inference | Batch Transform | Async Inference |
|------|--------------------|--------------------|----------------|----------------|
| 지연 시간 | 밀리초 | 초~밀리초 | 분~시간 | 초~분 |
| 트래픽 패턴 | 지속적 | 간헐적 | 대량 배치 | 비동기 처리 |
| 비용 모델 | 인스턴스 시간 | 호출 + 처리 시간 | 인스턴스 시간 | 인스턴스 시간 |
| 오토스케일링 | 지원 | 자동 (0까지) | N/A | 지원 |
| 최대 페이로드 | 6MB | 4MB | 무제한 (S3) | 1GB |
| 최대 응답 시간 | 60초 | 60초 | N/A | 1시간 |
| 적합한 사례 | 웹 앱 실시간 추론 | 가변적 트래픽 | 대량 데이터 처리 | 대규모 모델/긴 처리 |

### Real-time Inference vs API Gateway + Lambda

| 항목 | SageMaker Real-time | API GW + Lambda |
|------|--------------------|-----------------|
| 모델 크기 | 제한 없음 | Lambda 한도 (10GB) |
| GPU 지원 | 지원 | 미지원 |
| Cold Start | 최소 (상시 실행) | 있음 |
| 관리 복잡도 | 낮음 | 중간 |
| ML 최적화 | 내장 | 직접 구현 |

## 요약

Amazon SageMaker Real-time Inference는 ML 모델을 프로덕션에 배포하는 가장 일반적이고 강력한 방법입니다. 핵심 내용을 정리하면 다음과 같습니다.

- 실시간 추론 엔드포인트는 Model, Endpoint Configuration, Endpoint의 3계층 구조로 구성됩니다.
- Production Variants를 활용하여 A/B 테스트, 카나리 배포, Shadow 테스트를 수행할 수 있습니다.
- Application Auto Scaling을 통해 트래픽 변동에 따른 자동 확장/축소가 가능합니다.
- 멀티 모델 엔드포인트로 수백 개의 모델을 하나의 엔드포인트에서 호스팅하여 비용을 절감할 수 있습니다.
- 추론 파이프라인을 통해 전처리-추론-후처리를 하나의 엔드포인트에서 처리할 수 있습니다.
- 블루/그린 배포와 자동 롤백을 통해 무중단 모델 업데이트가 가능합니다.
- VPC PrivateLink, IAM, TLS 등을 통해 엔터프라이즈급 보안을 확보합니다.
- 지속적 트래픽에는 Real-time, 간헐적 트래픽에는 Serverless, 대량 처리에는 Batch Transform을 선택합니다.

Real-time Inference는 ML 모델의 비즈니스 가치를 실현하는 최종 단계이며, 안정적이고 확장 가능한 배포 전략이 모델의 성능만큼 중요합니다.