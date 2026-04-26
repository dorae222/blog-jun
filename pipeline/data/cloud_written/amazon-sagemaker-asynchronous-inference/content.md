<!-- infographic-hero -->
![Amazon SageMaker Asynchronous Inference: 대용량 요청을 위한 비동기 추론 완벽 가이드 핵심 요약](figures/infographic.svg)

*Figure: Amazon SageMaker Asynchronous Inference: 대용량 요청을 위한 비동기 추론 완벽 가이드 한 장 요약 인포그래픽*

# Amazon SageMaker Asynchronous Inference: 대용량 요청을 위한 비동기 추론 완벽 가이드

## 개요

머신러닝 추론 요청 중에는 처리 시간이 수 분에서 수십 분이 걸리는 경우가 있습니다. 대용량 이미지 처리, 긴 문서의 NLP 분석, 복잡한 모델의 예측 등이 대표적입니다. 이런 요청을 실시간 추론 엔드포인트로 처리하면 HTTP 타임아웃(60초)에 걸리거나, 요청이 몰릴 때 리소스가 부족해질 수 있습니다.

Amazon SageMaker Asynchronous Inference는 이러한 장시간/대용량 추론 요청을 처리하기 위해 설계된 배포 옵션입니다. 요청을 내부 큐에 저장한 후 순차적으로 처리하며, 결과는 S3에 저장됩니다. 처리 완료 시 SNS 알림을 통해 클라이언트에 통보할 수 있습니다.

비동기 추론의 가장 큰 장점은 **최대 1시간**의 처리 시간을 지원한다는 점과, 요청이 없을 때 **인스턴스를 0까지 스케일 다운**할 수 있다는 점입니다. 서버리스 추론이 CPU 전용이고 메모리 6GB로 제한되는 것과 달리, 비동기 추론은 GPU 인스턴스를 사용할 수 있으며 최대 1GB의 페이로드를 지원합니다.

## 핵심 기능

### 비동기 추론의 핵심 특성

| 특성 | 설명 |
|------|------|
| 최대 페이로드 크기 | 1GB (S3 경유) |
| 최대 처리 시간 | 3,600초 (1시간) |
| 큐 대기 시간 | 최대 6시간 |
| GPU 지원 | 지원 |
| Scale to Zero | 지원 (Auto Scaling 설정 필요) |
| 결과 저장 | S3 |
| 완료 알림 | SNS (성공/실패 각각 설정 가능) |
| 동시 처리 | MaxConcurrentInvocationsPerInstance 설정 |

### 비동기 엔드포인트 생성

```bash
# 1. 모델 등록
aws sagemaker create-model \
  --model-name "nlp-async-model" \
  --primary-container '{
    "Image": "763104351884.dkr.ecr.ap-northeast-2.amazonaws.com/huggingface-pytorch-inference:2.0.0-transformers4.28.1-gpu-py310-cu118-ubuntu20.04",
    "ModelDataUrl": "s3://my-model-bucket/nlp-model/model.tar.gz",
    "Environment": {
      "SAGEMAKER_PROGRAM": "inference.py",
      "SAGEMAKER_MODEL_SERVER_TIMEOUT": "3600"
    }
  }' \
  --execution-role-arn "arn:aws:iam::123456789012:role/SageMakerRole" \
  --region ap-northeast-2

# 2. 비동기 엔드포인트 설정 생성
aws sagemaker create-endpoint-config \
  --endpoint-config-name "nlp-async-config" \
  --production-variants '[{
    "VariantName": "AllTraffic",
    "ModelName": "nlp-async-model",
    "InstanceType": "ml.g5.xlarge",
    "InitialInstanceCount": 1
  }]' \
  --async-inference-config '{
    "OutputConfig": {
      "S3OutputPath": "s3://my-inference-bucket/async-output/",
      "NotificationConfig": {
        "SuccessTopic": "arn:aws:sns:ap-northeast-2:123456789012:async-success",
        "ErrorTopic": "arn:aws:sns:ap-northeast-2:123456789012:async-error",
        "IncludeInferenceResponseIn": ["SUCCESS_NOTIFICATION_TOPIC"]
      },
      "S3FailurePath": "s3://my-inference-bucket/async-failures/"
    },
    "ClientConfig": {
      "MaxConcurrentInvocationsPerInstance": 4
    }
  }' \
  --region ap-northeast-2

# 3. 엔드포인트 생성
aws sagemaker create-endpoint \
  --endpoint-name "nlp-async-endpoint" \
  --endpoint-config-name "nlp-async-config" \
  --region ap-northeast-2
```

### 비동기 추론 호출

비동기 추론은 입력 데이터를 S3에 업로드한 후, S3 URI를 엔드포인트에 전달하는 방식으로 동작합니다.

```bash
# 입력 데이터를 S3에 업로드
aws s3 cp input-document.json s3://my-inference-bucket/async-input/request-001.json

# 비동기 추론 호출
aws sagemaker-runtime invoke-endpoint-async \
  --endpoint-name "nlp-async-endpoint" \
  --input-location "s3://my-inference-bucket/async-input/request-001.json" \
  --content-type "application/json" \
  --region ap-northeast-2
```

응답으로 다음과 같은 정보가 즉시 반환됩니다.

```json
{
  "InferenceId": "11111-22222-33333-44444",
  "OutputLocation": "s3://my-inference-bucket/async-output/11111-22222-33333-44444.out"
}
```

클라이언트는 `OutputLocation`을 폴링하거나 SNS 알림을 구독하여 결과를 받을 수 있습니다.

### Scale to Zero 설정

비동기 추론 엔드포인트는 Auto Scaling을 통해 인스턴스를 0까지 축소할 수 있습니다. 이는 서버리스 추론과 유사한 비용 구조를 GPU 인스턴스에서도 달성할 수 있게 합니다.

```bash
# Auto Scaling 대상 등록
aws application-autoscaling register-scalable-target \
  --service-namespace sagemaker \
  --resource-id "endpoint/nlp-async-endpoint/variant/AllTraffic" \
  --scalable-dimension "sagemaker:variant:DesiredInstanceCount" \
  --min-capacity 0 \
  --max-capacity 5

# 큐 기반 스케일링 정책 설정
aws application-autoscaling put-scaling-policy \
  --service-namespace sagemaker \
  --resource-id "endpoint/nlp-async-endpoint/variant/AllTraffic" \
  --scalable-dimension "sagemaker:variant:DesiredInstanceCount" \
  --policy-name "queue-based-scaling" \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 5.0,
    "CustomizedMetricSpecification": {
      "MetricName": "ApproximateBacklogSizePerInstance",
      "Namespace": "AWS/SageMaker",
      "Dimensions": [{
        "Name": "EndpointName",
        "Value": "nlp-async-endpoint"
      }],
      "Statistic": "Average"
    },
    "ScaleInCooldown": 600,
    "ScaleOutCooldown": 120
  }'
```

`ApproximateBacklogSizePerInstance`는 인스턴스당 대기 중인 요청 수를 나타내는 메트릭입니다. 이 값이 목표치(TargetValue)를 초과하면 스케일 아웃되고, 0이 되면 스케일 인되어 최종적으로 인스턴스 0까지 축소됩니다.

## 아키텍처/동작 원리

### 비동기 추론 처리 흐름

```
+------------------------------------------------------------------+
|                    비동기 추론 아키텍처                             |
+------------------------------------------------------------------+
|                                                                  |
|  1. Client --> InvokeEndpointAsync API                           |
|                (InputLocation: s3://input/request.json)           |
|                         |                                        |
|                         v                                        |
|  2. SageMaker Internal Queue (SQS 기반)                          |
|     [request-001] [request-002] [request-003] ...                |
|                         |                                        |
|                         v                                        |
|  3. Inference Instance(s)                                        |
|     +------------------+  +------------------+                   |
|     | Instance 1       |  | Instance 2       |                   |
|     | - Download input  |  | - Download input  |                  |
|     |   from S3        |  |   from S3        |                   |
|     | - Run inference  |  | - Run inference  |                   |
|     | - Upload result  |  | - Upload result  |                   |
|     |   to S3          |  |   to S3          |                   |
|     +------------------+  +------------------+                   |
|                         |                                        |
|                         v                                        |
|  4. S3 Output: s3://output/{InferenceId}.out                     |
|                         |                                        |
|                         v                                        |
|  5. SNS Notification (Success / Error)                           |
|     --> Lambda / SQS / HTTP Endpoint                             |
+------------------------------------------------------------------+
```

### 내부 큐잉 메커니즘

비동기 추론 엔드포인트의 내부에는 SQS 기반의 큐가 존재합니다. 이 큐의 동작 방식은 다음과 같습니다.

1. `InvokeEndpointAsync` API가 호출되면 요청이 큐에 등록됩니다.
2. 큐에서 요청을 FIFO(First-In-First-Out) 순서로 가져옵니다.
3. `MaxConcurrentInvocationsPerInstance` 설정에 따라 인스턴스당 동시 처리 수가 제한됩니다.
4. 큐에 요청이 남아있고 처리 용량이 부족하면 Auto Scaling이 트리거됩니다.
5. 큐가 비어있고 일정 시간이 지나면 Scale to Zero가 실행됩니다.

큐에서 대기 중인 요청은 최대 6시간까지 보존됩니다. 6시간을 초과하면 요청이 만료되며, 실패 알림이 전송됩니다.

### MaxConcurrentInvocationsPerInstance 동작

이 설정은 하나의 인스턴스에서 동시에 처리할 수 있는 최대 요청 수를 정의합니다.

- **값이 1이면**: 요청이 순차적으로 처리됩니다. 한 요청의 처리가 완료된 후 다음 요청이 시작됩니다.
- **값이 N이면**: 최대 N개의 요청이 동시에 처리됩니다. 모델이 병렬 처리를 지원해야 합니다.

GPU 모델의 경우 일반적으로 1로 설정합니다 (GPU 메모리를 하나의 추론에 전부 사용). CPU 기반 경량 모델은 인스턴스의 vCPU 수에 맞춰 설정할 수 있습니다.

## 실전 활용

### 1. Python SDK를 활용한 비동기 추론 클라이언트

```python
import boto3
import json
import time

sm_runtime = boto3.client('sagemaker-runtime', region_name='ap-northeast-2')
s3 = boto3.client('s3', region_name='ap-northeast-2')

def invoke_async(endpoint_name, input_data, input_bucket, input_prefix):
    """비동기 추론 요청을 전송합니다."""
    # 입력 데이터를 S3에 업로드
    input_key = f"{input_prefix}/{int(time.time())}.json"
    s3.put_object(
        Bucket=input_bucket,
        Key=input_key,
        Body=json.dumps(input_data),
        ContentType='application/json'
    )

    # 비동기 추론 호출
    response = sm_runtime.invoke_endpoint_async(
        EndpointName=endpoint_name,
        InputLocation=f"s3://{input_bucket}/{input_key}",
        ContentType='application/json',
        Accept='application/json'
    )

    return {
        'inference_id': response['InferenceId'],
        'output_location': response['OutputLocation']
    }

def wait_for_result(output_location, timeout=600, poll_interval=10):
    """결과가 준비될 때까지 대기합니다."""
    bucket, key = output_location.replace('s3://', '').split('/', 1)
    start = time.time()

    while time.time() - start < timeout:
        try:
            response = s3.get_object(Bucket=bucket, Key=key)
            result = json.loads(response['Body'].read())
            return {'status': 'success', 'result': result}
        except s3.exceptions.NoSuchKey:
            time.sleep(poll_interval)

    return {'status': 'timeout', 'output_location': output_location}

# 사용 예시
result_info = invoke_async(
    endpoint_name='nlp-async-endpoint',
    input_data={'text': '분석할 긴 문서 내용...'},
    input_bucket='my-inference-bucket',
    input_prefix='async-input'
)

print(f"추론 ID: {result_info['inference_id']}")
print(f"결과 위치: {result_info['output_location']}")

# 결과 대기
result = wait_for_result(result_info['output_location'])
print(f"결과: {result}")
```

### 2. SNS 알림 기반 이벤트 처리

```python
# Lambda 함수 - SNS 알림을 받아 후속 처리 수행
import json
import boto3

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('InferenceResults')

def lambda_handler(event, context):
    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])

        inference_id = message.get('inferenceId')
        output_location = message.get('responseParameters', {}).get('outputLocation')

        if not output_location:
            print(f"추론 실패: {inference_id}")
            table.put_item(Item={
                'inference_id': inference_id,
                'status': 'FAILED',
                'error': message.get('failureReason', 'Unknown')
            })
            return

        # S3에서 결과 읽기
        bucket, key = output_location.replace('s3://', '').split('/', 1)
        response = s3.get_object(Bucket=bucket, Key=key)
        result = json.loads(response['Body'].read())

        # DynamoDB에 결과 저장
        table.put_item(Item={
            'inference_id': inference_id,
            'status': 'COMPLETED',
            'output_location': output_location,
            'result_summary': json.dumps(result)[:1000]  # 요약만 저장
        })

        print(f"추론 완료: {inference_id}")
```

### 3. 대량 요청 배치 전송

```python
import concurrent.futures

def batch_invoke_async(endpoint_name, requests, input_bucket, max_workers=20):
    """대량의 비동기 추론 요청을 병렬로 전송합니다."""
    results = []

    def submit_one(idx, data):
        return invoke_async(
            endpoint_name=endpoint_name,
            input_data=data,
            input_bucket=input_bucket,
            input_prefix=f"async-batch/{idx}"
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(submit_one, i, req): i
            for i, req in enumerate(requests)
        }
        for future in concurrent.futures.as_completed(futures):
            idx = futures[future]
            try:
                result = future.result()
                results.append({'index': idx, **result})
            except Exception as e:
                results.append({'index': idx, 'error': str(e)})

    print(f"전송 완료: {len(results)}건")
    return results

# 100개 요청 동시 전송
requests = [{'text': f'문서 {i}의 내용...'} for i in range(100)]
results = batch_invoke_async('nlp-async-endpoint', requests, 'my-inference-bucket')
```

## 모범 사례/보안

### Scale to Zero 운영 시 주의사항

Scale to Zero는 비용 절감에 효과적이지만, 다음 사항을 고려해야 합니다.

1. **Cold Start 시간**: 인스턴스가 0일 때 새 요청이 들어오면 인스턴스 프로비저닝과 모델 로딩에 수 분이 소요됩니다. GPU 인스턴스의 경우 5-10분까지 걸릴 수 있습니다.
2. **ScaleInCooldown 설정**: 스케일 인 쿨다운을 충분히 길게 설정(600초 이상)하여, 간헐적 트래픽 시 불필요한 스케일 인/아웃 반복을 방지합니다.
3. **최소 인스턴스 유지**: 비즈니스 시간에는 최소 1개 인스턴스를 유지하는 스케줄링 정책을 적용하는 것이 좋습니다.

### 에러 처리 전략

```python
# 실패한 요청을 재시도하는 Lambda 함수
def handle_async_failure(event, context):
    """SNS Error Topic을 구독하여 실패한 요청을 재시도합니다."""
    sm_runtime = boto3.client('sagemaker-runtime')
    max_retries = 3

    for record in event['Records']:
        message = json.loads(record['Sns']['Message'])
        inference_id = message.get('inferenceId')
        input_location = message.get('requestParameters', {}).get('inputLocation')
        retry_count = int(message.get('customAttributes', {}).get('retryCount', 0))

        if retry_count >= max_retries:
            print(f"최대 재시도 횟수 초과: {inference_id}")
            # Dead Letter Queue로 전송하거나 관리자에게 알림
            return

        # 재시도
        sm_runtime.invoke_endpoint_async(
            EndpointName='nlp-async-endpoint',
            InputLocation=input_location,
            ContentType='application/json',
            CustomAttributes=json.dumps({'retryCount': retry_count + 1})
        )
        print(f"재시도 ({retry_count + 1}/{max_retries}): {inference_id}")
```

### IAM 권한 설정

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sagemaker:InvokeEndpointAsync",
      "Resource": "arn:aws:sagemaker:ap-northeast-2:123456789012:endpoint/nlp-async-endpoint"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::my-inference-bucket/*"
    }
  ]
}
```

## 관련 서비스 비교

| 항목 | Async Inference | Real-time Inference | Serverless Inference | Batch Transform |
|------|----------------|--------------------|--------------------|------------------|
| 응답 방식 | 비동기 (S3 + SNS) | 동기 (HTTP 응답) | 동기 (HTTP 응답) | 비동기 (S3) |
| 최대 페이로드 | 1GB (S3) | 6MB | 6MB | 제한 없음 (S3) |
| 최대 처리 시간 | 3,600초 | 60초 | 60초 | 제한 없음 |
| GPU 지원 | 지원 | 지원 | 미지원 | 지원 |
| Scale to Zero | 지원 | 미지원 | 자동 (내장) | 해당 없음 |
| 큐잉 | 내장 | 미지원 | 미지원 | 해당 없음 |
| 적합한 워크로드 | 대용량 입력, 긴 처리 시간, GPU 필요 | 저지연 실시간 서비스 | 간헐적 트래픽, 경량 모델 | 대량 일괄 처리 |
| 비용 (낮은 트래픽) | 낮음 (Scale to Zero 시) | 높음 (상시 가동) | 매우 낮음 | 보통 |

### Async Inference를 선택해야 하는 경우

- 추론 처리 시간이 60초를 초과하는 경우
- 입력 페이로드가 6MB를 초과하는 경우 (대용량 이미지, 긴 문서)
- GPU가 필요하지만 트래픽이 간헐적인 경우 (Scale to Zero 활용)
- 요청 급증에 대한 버퍼링이 필요한 경우 (내장 큐)

## 요약

Amazon SageMaker Asynchronous Inference는 장시간/대용량 추론 요청을 효율적으로 처리하기 위한 배포 옵션입니다.

- **내부 큐**가 요청을 버퍼링하여 트래픽 급증에 안정적으로 대응하며, 결과는 **S3에 저장**됩니다.
- **최대 1GB 페이로드**와 **최대 1시간 처리 시간**을 지원하여 실시간 추론의 제한을 극복합니다.
- **Scale to Zero**를 통해 GPU 인스턴스에서도 서버리스와 유사한 비용 효율성을 달성할 수 있습니다.
- **SNS 알림**을 통해 추론 완료/실패 이벤트를 Lambda 등 후속 처리 시스템에 연동할 수 있습니다.
- `MaxConcurrentInvocationsPerInstance`와 Auto Scaling 정책을 적절히 설정하여 처리량과 비용의 균형을 맞추는 것이 중요합니다.
- Scale to Zero 사용 시 Cold Start 시간(GPU 인스턴스의 경우 5-10분)을 고려하여 설계해야 합니다.