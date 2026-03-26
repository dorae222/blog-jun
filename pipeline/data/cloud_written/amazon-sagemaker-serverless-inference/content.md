# Amazon SageMaker Serverless Inference

## 개요

Amazon SageMaker Serverless Inference는 인프라 관리 없이 ML 모델을 배포할 수 있는 서버리스 추론 서비스입니다. 인스턴스를 직접 프로비저닝하거나 관리할 필요 없이, 요청이 들어올 때 자동으로 컴퓨팅 리소스가 할당되고, 사용한 만큼만 비용을 지불합니다. 트래픽이 없을 때는 0으로 스케일 다운되어, 간헐적인 추론 워크로드에 이상적인 선택입니다.

전통적인 SageMaker Real-time Inference 엔드포인트는 24시간 상시 실행되므로, 트래픽이 불규칙하거나 적은 경우 과도한 비용이 발생할 수 있습니다. 예를 들어, 하루에 수백 건의 추론 요청만 처리하는 내부 도구의 경우, ml.m5.xlarge 인스턴스를 24시간 운영하면 월 $170 이상의 비용이 발생합니다. Serverless Inference를 사용하면 실제 추론에 소요된 시간만큼만 비용을 지불하므로, 동일한 워크로드에 대해 90% 이상의 비용 절감이 가능합니다.

Serverless Inference의 핵심 특성은 다음과 같습니다.

- **제로 관리**: 인스턴스 타입, 오토스케일링 등을 설정할 필요가 없습니다.
- **제로 스케일**: 트래픽이 없으면 리소스가 0으로 축소되어 비용이 발생하지 않습니다.
- **자동 확장**: 트래픽 증가 시 자동으로 스케일 아웃됩니다.
- **종량제 과금**: 추론 요청 수와 처리 시간에 따라 비용이 결정됩니다.

## 핵심 기능

### 1. 서버리스 엔드포인트 배포

서버리스 엔드포인트의 배포는 매우 간단합니다. 메모리 크기와 최대 동시 호출 수만 지정하면 됩니다.

```python
import sagemaker
from sagemaker.serverless import ServerlessInferenceConfig
from sagemaker.sklearn.model import SKLearnModel

session = sagemaker.Session()
role = sagemaker.get_execution_role()

# Scikit-learn 모델 정의
model = SKLearnModel(
    model_data='s3://my-bucket/models/sklearn-classifier/model.tar.gz',
    role=role,
    framework_version='1.2-1',
    entry_point='inference.py'
)

# 서버리스 추론 설정
serverless_config = ServerlessInferenceConfig(
    memory_size_in_mb=2048,     # 메모리 크기 (1024~6144MB)
    max_concurrency=10,          # 최대 동시 호출 수 (1~200)
    provisioned_concurrency=2    # 프로비저닝된 동시성 (Cold Start 방지)
)

# 서버리스 엔드포인트 배포
predictor = model.deploy(
    serverless_inference_config=serverless_config,
    endpoint_name='serverless-classifier'
)

# 추론 테스트
import json
result = predictor.predict(
    json.dumps({"features": [1.5, 2.3, 0.8, 4.1]})
)
print(result)
```

```bash
# 서버리스 엔드포인트 상태 확인
aws sagemaker describe-endpoint \
  --endpoint-name "serverless-classifier" \
  --region us-east-1 \
  --query '{Status: EndpointStatus, Config: EndpointConfigName}'

# 서버리스 엔드포인트 설정 상세 확인
aws sagemaker describe-endpoint-config \
  --endpoint-config-name "serverless-classifier-config" \
  --region us-east-1 \
  --query 'ProductionVariants[0].ServerlessConfig'
```

### 2. 메모리 크기 설정

메모리 크기는 서버리스 엔드포인트의 성능과 비용에 직접적인 영향을 미칩니다. 사용 가능한 메모리 크기는 1024MB, 2048MB, 3072MB, 4096MB, 5120MB, 6144MB입니다.

메모리 선택 가이드는 다음과 같습니다.

- **1024MB**: 경량 모델 (Scikit-learn, 소형 XGBoost)
- **2048MB**: 중간 규모 모델 (XGBoost, 소형 딥러닝)
- **3072~4096MB**: 중형 딥러닝 모델 (BERT-base 등)
- **5120~6144MB**: 대형 모델 (DistilBERT, 중형 트랜스포머)

### 3. 동시성 관리

최대 동시 호출 수(Max Concurrency)는 엔드포인트가 동시에 처리할 수 있는 요청 수를 결정합니다.

```python
import boto3

sm_client = boto3.client('sagemaker')

# 동시성 설정을 포함한 엔드포인트 설정
sm_client.create_endpoint_config(
    EndpointConfigName='serverless-high-concurrency-config',
    ProductionVariants=[
        {
            'VariantName': 'AllTraffic',
            'ModelName': 'my-serverless-model',
            'ServerlessConfig': {
                'MemorySizeInMB': 4096,
                'MaxConcurrency': 50,  # 최대 50개 동시 요청
                'ProvisionedConcurrency': 5  # 5개는 항상 준비 상태
            }
        }
    ]
)
```

### 4. 프로비저닝된 동시성(Provisioned Concurrency)

Cold Start 문제를 해결하기 위해 일정 수의 실행 환경을 항상 준비 상태로 유지할 수 있습니다. 프로비저닝된 동시성은 추가 비용이 발생하지만, 일관된 응답 시간을 보장합니다.

```python
# 프로비저닝된 동시성이 포함된 배포
serverless_config = ServerlessInferenceConfig(
    memory_size_in_mb=4096,
    max_concurrency=20,
    provisioned_concurrency=3  # 3개 환경을 상시 대기
)

# 프로비저닝 비용 예상:
# 4096MB x 3 동시성 = 약 $0.00002/초 x 86400초/일 x 3 = 약 $5.18/일
```

```bash
# 프로비저닝된 동시성 상태 확인
aws sagemaker describe-endpoint \
  --endpoint-name "serverless-classifier" \
  --region us-east-1 \
  --query 'ProductionVariants[0].{CurrentServerlessConfig: CurrentServerlessConfig}' \
  --output json
```

### 5. 지원 컨테이너 및 프레임워크

Serverless Inference는 SageMaker의 사전 빌드 컨테이너와 커스텀 컨테이너를 모두 지원합니다.

지원되는 사전 빌드 컨테이너는 다음과 같습니다.

- **Scikit-learn**: 0.23-1, 1.0-1, 1.2-1
- **XGBoost**: 1.3-1, 1.5-1, 1.7-1
- **PyTorch**: 1.12, 2.0, 2.1
- **TensorFlow**: 2.11, 2.12, 2.13
- **Hugging Face**: Transformers 기반 모델
- **MXNet**: 1.8, 1.9

## 아키텍처/동작 원리

### 서버리스 추론 아키텍처

Serverless Inference의 내부 아키텍처는 다음과 같습니다.

```
[클라이언트 요청]
      |
[SageMaker Runtime API]
      |
[요청 라우터]
      |
(실행 환경 있음?)  --  No  --> [Cold Start: 컨테이너 프로비저닝]
      |                                    |
     Yes                              [모델 로드]
      |                                    |
[Warm 실행 환경]  <--------------------+
      |
[추론 실행]
      |
[응답 반환]
      |
(유휴 시간 초과?)  --  Yes  --> [실행 환경 해제]
      |
     No
      |
[다음 요청 대기]
```

### Cold Start 메커니즘

Cold Start는 서버리스 추론의 가장 중요한 특성입니다. 유휴 시간이 지나 실행 환경이 해제된 후 새 요청이 들어오면, 다음 과정이 진행됩니다.

1. **컨테이너 프로비저닝**: 컨테이너 이미지를 다운로드하고 실행합니다. (수 초~수십 초)
2. **모델 로드**: S3에서 모델 아티팩트를 다운로드하고 메모리에 로드합니다. (수 초~수분)
3. **웜업**: 첫 추론을 위한 초기화를 수행합니다.

Cold Start 시간은 주로 모델 크기와 컨테이너 이미지 크기에 의해 결정됩니다.

| 모델 크기 | 컨테이너 | 예상 Cold Start 시간 |
|----------|---------|--------------------|
| ~100MB | Sklearn | 3~8초 |
| ~500MB | PyTorch | 15~30초 |
| ~1GB | HuggingFace | 30~60초 |
| ~2GB+ | 대형 모델 | 60초 이상 |

### 비용 모델

Serverless Inference의 비용은 두 가지 요소로 구성됩니다.

1. **추론 시간 비용**: 실제 추론 처리에 소요된 시간(밀리초 단위)과 메모리 크기에 따라 과금
2. **프로비저닝 동시성 비용**: 프로비저닝된 실행 환경의 유지 비용 (선택 사항)

비용 계산 공식은 다음과 같습니다.

```
추론 비용 = 요청 수 x 평균 처리 시간(초) x 메모리 가격($/GB-초)
프로비저닝 비용 = 프로비저닝 수 x 메모리 크기(GB) x 시간(초) x 프로비저닝 가격($/GB-초)
```

## 실전 활용

### 사례 1: 내부 도구용 추론 API

일일 수백 건 수준의 내부 도구에 서버리스 엔드포인트를 적용하는 사례입니다.

```python
from sagemaker.sklearn.model import SKLearnModel
from sagemaker.serverless import ServerlessInferenceConfig
import sagemaker

role = sagemaker.get_execution_role()

# 감성 분류 모델 배포
model = SKLearnModel(
    model_data='s3://my-bucket/models/sentiment/model.tar.gz',
    role=role,
    framework_version='1.2-1',
    entry_point='inference.py'
)

serverless_config = ServerlessInferenceConfig(
    memory_size_in_mb=2048,
    max_concurrency=5
)

predictor = model.deploy(
    serverless_inference_config=serverless_config,
    endpoint_name='internal-sentiment-api'
)

# 비용 분석 (월간)
# 가정: 하루 500건, 건당 평균 200ms
# 추론 비용: 500 x 30 x 0.2초 x $0.00002/GB-초 x 2GB = $0.12/월
# vs Real-time: ml.m5.large 24/7 = $115/월
# 절감률: 99.9%
```

### 사례 2: 이벤트 기반 추론 워크플로

S3 이벤트를 트리거로 서버리스 추론을 호출하는 워크플로입니다.

```python
import boto3
import json

# Lambda 함수: S3 업로드 시 서버리스 엔드포인트 호출
lambda_handler_code = """
import boto3
import json

def handler(event, context):
    sm_runtime = boto3.client('sagemaker-runtime')
    s3 = boto3.client('s3')
    
    # S3 이벤트에서 파일 정보 추출
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # S3에서 데이터 로드
    response = s3.get_object(Bucket=bucket, Key=key)
    data = json.loads(response['Body'].read().decode('utf-8'))
    
    # 서버리스 엔드포인트 호출
    result = sm_runtime.invoke_endpoint(
        EndpointName='serverless-classifier',
        ContentType='application/json',
        Body=json.dumps(data)
    )
    
    prediction = json.loads(result['Body'].read().decode('utf-8'))
    
    # 결과를 S3에 저장
    s3.put_object(
        Bucket=bucket,
        Key=f'results/{key}',
        Body=json.dumps(prediction)
    )
    
    return {'statusCode': 200, 'body': json.dumps(prediction)}
"""
```

```bash
# 서버리스 엔드포인트 호출 테스트 (AWS CLI)
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name "serverless-classifier" \
  --content-type "application/json" \
  --body '{"features": [1.5, 2.3, 0.8, 4.1]}' \
  --region us-east-1 \
  /tmp/prediction-result.json

cat /tmp/prediction-result.json
```

### 사례 3: Cold Start 최적화 전략

Cold Start를 최소화하기 위한 다양한 전략입니다.

```python
# 전략 1: 모델 아티팩트 크기 최소화
# 모델 저장 시 불필요한 데이터 제거
import joblib
import os

def save_optimized_model(model, output_dir):
    # 필요한 것만 저장
    joblib.dump(model, os.path.join(output_dir, 'model.joblib'), compress=3)
    # 불필요한 훈련 데이터, 로그 등은 제외

# 전략 2: 경량 컨테이너 사용
# Scikit-learn 컨테이너는 PyTorch 컨테이너보다 Cold Start가 빠름

# 전략 3: 프로비저닝된 동시성 활용
serverless_config = ServerlessInferenceConfig(
    memory_size_in_mb=2048,
    max_concurrency=20,
    provisioned_concurrency=2  # 최소 2개 환경 항상 대기
)

# 전략 4: 모델 로드 최적화 (inference.py)
model_load_optimization = """
import os
import joblib

# 글로벌 변수에 모델 캐싱
model = None

def model_fn(model_dir):
    global model
    if model is None:
        model = joblib.load(os.path.join(model_dir, 'model.joblib'))
    return model
"""
```

### 사례 4: Real-time vs Serverless 비용 분기점 분석

```python
def cost_comparison(requests_per_day, avg_latency_ms, memory_mb=2048):
    """
    Real-time과 Serverless의 비용을 비교합니다.
    
    Args:
        requests_per_day: 일일 평균 요청 수
        avg_latency_ms: 평균 추론 지연 시간 (밀리초)
        memory_mb: 서버리스 메모리 크기 (MB)
    """
    days_per_month = 30
    
    # Real-time 비용 (ml.m5.large 기준)
    realtime_hourly = 0.134  # us-east-1 기준
    realtime_monthly = realtime_hourly * 24 * days_per_month
    
    # Serverless 비용
    serverless_per_second = 0.00002 * (memory_mb / 1024)  # $/GB-초
    total_inference_seconds = (requests_per_day * days_per_month * 
                               avg_latency_ms / 1000)
    serverless_monthly = total_inference_seconds * serverless_per_second
    
    print(f"=== 월간 비용 비교 ===")
    print(f"일일 요청 수: {requests_per_day:,}")
    print(f"평균 지연 시간: {avg_latency_ms}ms")
    print(f"Real-time (ml.m5.large): ${realtime_monthly:.2f}/월")
    print(f"Serverless ({memory_mb}MB): ${serverless_monthly:.2f}/월")
    print(f"절감액: ${realtime_monthly - serverless_monthly:.2f}/월")
    
    # 손익분기점 계산
    breakeven_requests = (realtime_monthly / 
                          (serverless_per_second * avg_latency_ms / 1000 * 
                           days_per_month))
    print(f"손익분기점: 일일 {breakeven_requests:,.0f}건")

# 시나리오별 비교
cost_comparison(100, 200)     # 소량 트래픽
cost_comparison(10000, 200)   # 중간 트래픽
cost_comparison(100000, 200)  # 대량 트래픽
```

## 모범 사례/보안

### 배포 모범 사례

1. **메모리 크기 벤치마킹**: 여러 메모리 크기로 테스트하여 최적의 성능/비용 비율을 찾습니다.

2. **Cold Start 허용 여부 판단**: 비즈니스 요구사항에 따라 프로비저닝된 동시성 사용 여부를 결정합니다.

3. **모델 크기 최적화**: 모델 아티팩트를 가능한 한 작게 유지하여 Cold Start를 줄입니다.

4. **타임아웃 설정**: 클라이언트 측에서 Cold Start를 고려한 타임아웃을 설정합니다.

5. **모니터링 구성**: CloudWatch 메트릭으로 Cold Start 빈도와 추론 지연 시간을 모니터링합니다.

### 보안 설정

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ServerlessEndpointInvoke",
      "Effect": "Allow",
      "Action": "sagemaker:InvokeEndpoint",
      "Resource": "arn:aws:sagemaker:us-east-1:123456789012:endpoint/serverless-*"
    }
  ]
}
```

```bash
# 서버리스 엔드포인트 CloudWatch 메트릭 확인
aws cloudwatch get-metric-statistics \
  --namespace "AWS/SageMaker" \
  --metric-name "ModelSetupTime" \
  --dimensions Name=EndpointName,Value=serverless-classifier \
  --start-time $(date -u -v-24H +"%Y-%m-%dT%H:%M:%SZ") \
  --end-time $(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  --period 3600 \
  --statistics Average Maximum \
  --region us-east-1
```

## 관련 서비스 비교

### Serverless Inference vs AWS Lambda ML

| 항목 | SageMaker Serverless | Lambda ML |
|------|---------------------|----------|
| 최대 메모리 | 6144MB | 10240MB |
| 최대 실행 시간 | 60초 | 15분 |
| GPU 지원 | 미지원 | 미지원 |
| ML 프레임워크 | 사전 구성 | 직접 패키징 |
| 모델 크기 | S3에서 로드 (제한 없음) | 패키지 크기 제한 |
| Cold Start | 모델 크기에 비례 | 패키지 크기에 비례 |
| ML 최적화 | SageMaker 통합 | 없음 |

### Serverless Inference vs Serverless on Other Clouds

| 항목 | SageMaker Serverless | Google Cloud Run ML | Azure ML Serverless |
|------|---------------------|--------------------|-----------------|
| 관리 복잡도 | 최소 | 중간 (컨테이너 직접 관리) | 최소 |
| 스케일링 | 자동 (0까지) | 자동 (0까지) | 자동 |
| ML 프레임워크 | 사전 구성 | 직접 구성 | 사전 구성 |
| 가격 모델 | 처리 시간 + 메모리 | vCPU-초 + 메모리-초 | 처리 시간 |

## 요약

Amazon SageMaker Serverless Inference는 간헐적이거나 예측 불가능한 트래픽 패턴의 ML 워크로드에 최적화된 서버리스 추론 서비스입니다. 핵심 내용을 정리하면 다음과 같습니다.

- 인스턴스 관리 없이 메모리 크기와 최대 동시성만 설정하면 즉시 배포할 수 있습니다.
- 트래픽이 없을 때 0으로 스케일 다운되어, 간헐적 워크로드에서 90% 이상의 비용 절감이 가능합니다.
- Cold Start는 모델 크기와 컨테이너에 따라 3초~60초 이상 소요될 수 있으며, 프로비저닝된 동시성으로 완화할 수 있습니다.
- 메모리 크기는 1024MB~6144MB까지 선택할 수 있으며, 모델 크기와 추론 복잡도에 따라 결정합니다.
- Real-time Inference와의 비용 분기점은 일일 요청 수, 추론 지연 시간, 인스턴스 타입에 따라 달라지므로, 비용 분석을 사전에 수행하는 것이 중요합니다.
- 일일 수천 건 이하의 간헐적 트래픽에는 Serverless, 지속적인 대량 트래픽에는 Real-time을 선택합니다.
- GPU가 필요한 대규모 딥러닝 모델에는 적합하지 않으며, CPU 기반의 경량~중형 모델에 최적입니다.

Serverless Inference는 특히 MVP 단계의 프로토타입, 내부 도구, 이벤트 기반 워크플로 등에서 빠르게 ML 모델을 배포하고 비용을 최소화하는 데 탁월한 선택입니다.