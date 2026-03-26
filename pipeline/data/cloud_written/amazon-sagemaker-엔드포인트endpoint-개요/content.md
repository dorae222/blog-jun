## 개요

ML 모델을 학습하는 것은 전체 ML 라이프사이클의 절반에 불과합니다. 학습된 모델이 실제 비즈니스 가치를 창출하려면, 애플리케이션에서 모델을 호출하여 예측 결과를 받을 수 있는 추론 인프라가 필요합니다. 이 추론 인프라를 구축하고 관리하는 것은 모델 학습만큼이나 복잡한 엔지니어링 과제입니다.

Amazon SageMaker Endpoint는 학습된 ML 모델을 프로덕션 환경에 배포하기 위한 완전 관리형 추론 인프라입니다. SageMaker Endpoint를 사용하면 인프라 프로비저닝, 로드 밸런싱, 오토스케일링, 모델 업데이트 등을 AWS가 관리하므로, 데이터 과학자와 ML 엔지니어는 모델 개발에 집중할 수 있습니다.

### 추론 인프라의 과제

자체 추론 인프라를 구축할 때 직면하는 과제는 다음과 같습니다.

1. **인프라 관리**: 서버 프로비저닝, 패치, 모니터링, 장애 대응
2. **확장성**: 트래픽 변동에 따른 자동 확장/축소
3. **가용성**: 다중 AZ 배포, 장애 복구, 헬스 체크
4. **배포 전략**: 무중단 배포, 카나리 배포, A/B 테스트
5. **비용 최적화**: 유휴 리소스 최소화, 적절한 인스턴스 타입 선택
6. **모니터링**: 추론 지연 시간, 오류율, 모델 드리프트 추적

SageMaker Endpoint는 이 모든 과제에 대한 관리형 솔루션을 제공합니다.

## 핵심 기능

### 1. 엔드포인트 유형

SageMaker는 네 가지 추론 배포 방식을 제공합니다. 각 방식은 서로 다른 사용 사례에 최적화되어 있습니다.

**실시간 엔드포인트 (Real-time Inference)**
- 밀리초~초 단위의 낮은 지연 시간 응답
- 항상 실행되는 인스턴스 기반
- 최대 6MB 페이로드
- 최대 60초 타임아웃
- 실시간 웹 서비스, API 백엔드에 적합

**서버리스 엔드포인트 (Serverless Inference)**
- 트래픽이 없을 때 자동으로 0으로 스케일 다운
- 콜드 스타트 존재 (수초~수십 초)
- 최대 6MB 페이로드
- 최대 60초 타임아웃
- 간헐적 트래픽, 개발/테스트 환경에 적합

**비동기 엔드포인트 (Asynchronous Inference)**
- 큐 기반의 비동기 처리
- 최대 1GB 페이로드
- 최대 3600초(1시간) 타임아웃
- 0으로 스케일 다운 가능
- 대용량 입력, 장시간 추론, 배치 처리에 적합

**배치 변환 (Batch Transform)**
- 대규모 데이터셋에 대한 일괄 추론
- 작업 완료 후 자동으로 리소스 해제
- 입력/출력 모두 S3 기반
- 데이터셋 전체에 대한 예측이 필요한 경우에 적합

### 2. 멀티 모델 엔드포인트 (Multi-Model Endpoint, MME)

하나의 엔드포인트에서 여러 모델을 호스팅할 수 있습니다. 모델은 요청 시 동적으로 로드되며, LRU(Least Recently Used) 정책에 따라 메모리에서 관리됩니다.

- 수천 개의 모델을 하나의 엔드포인트로 서빙
- 모델별 전용 엔드포인트 대비 비용 대폭 절감
- 테넌트별 모델, 지역별 모델 등의 시나리오에 적합

### 3. 멀티 컨테이너 엔드포인트 (Multi-Container Endpoint)

하나의 엔드포인트에서 여러 컨테이너를 실행할 수 있습니다. 두 가지 모드를 지원합니다.

- **직렬(Serial) 모드**: 한 컨테이너의 출력이 다음 컨테이너의 입력으로 전달 (추론 파이프라인)
- **직접 호출(Direct) 모드**: 특정 컨테이너를 지정하여 직접 호출

### 4. 오토스케일링

SageMaker Endpoint는 Application Auto Scaling과 통합하여 트래픽에 따라 인스턴스 수를 자동으로 조절합니다.

**스케일링 정책 유형**
- **대상 추적(Target Tracking)**: 특정 메트릭(예: InvocationsPerInstance)이 목표값을 유지하도록 자동 조절
- **단계(Step) 스케일링**: CloudWatch 알람에 따라 단계적으로 확장/축소
- **예약(Scheduled) 스케일링**: 예측 가능한 트래픽 패턴에 따라 사전에 확장/축소

### 5. 배포 전략

SageMaker Endpoint는 무중단 모델 업데이트를 위한 다양한 배포 전략을 지원합니다.

**블루/그린 배포(Blue/Green Deployment)**
- 새 모델 버전을 별도의 플릿(그린)에 배포한 후, 트래픽을 전환
- 문제 발생 시 즉시 이전 버전(블루)으로 롤백
- 세 가지 트래픽 전환 방식: AllAtOnce, Canary, Linear

**카나리 배포(Canary Deployment)**
- 새 모델 버전에 소량의 트래픽(예: 10%)만 먼저 전달
- 문제가 없으면 전체 트래픽을 전환
- 위험을 최소화하면서 새 모델을 테스트

**섀도 테스트(Shadow Testing)**
- 프로덕션 트래픽을 새 모델에 복제하여 실제 환경에서 테스트
- 새 모델의 응답은 기록만 하고 사용자에게는 기존 모델의 응답을 반환
- 실제 트래픽으로 새 모델의 성능을 안전하게 검증

### 6. 추론 파이프라인 (Inference Pipeline)

여러 컨테이너를 직렬로 연결하여 추론 파이프라인을 구성할 수 있습니다.

```
[요청] --> [전처리 컨테이너] --> [모델 추론 컨테이너] --> [후처리 컨테이너] --> [응답]
```

이를 통해 피처 엔지니어링, 모델 추론, 결과 후처리를 하나의 엔드포인트에서 수행할 수 있습니다.

## 아키텍처/동작 원리

### 엔드포인트 내부 아키텍처

```
[클라이언트 요청]
       |
       v
[SageMaker Runtime API]
       |
       v
[내부 로드 밸런서]
  - 요청 라우팅
  - 헬스 체크
  - 장애 인스턴스 격리
       |
       v
[추론 인스턴스 플릿]
  - 인스턴스 1: [모델 서버 (MMS/TorchServe/TFS)]
  - 인스턴스 2: [모델 서버]
  - 인스턴스 N: [모델 서버]
       |
       v
[모델 아티팩트]
  - S3에서 로드
  - EBS에 캐싱
```

### 엔드포인트 생성 프로세스

SageMaker Endpoint를 생성하는 과정은 세 단계로 구성됩니다.

1. **모델 생성(CreateModel)**: 모델 아티팩트(S3)와 추론 컨테이너 이미지를 지정
2. **엔드포인트 구성 생성(CreateEndpointConfig)**: 인스턴스 타입, 인스턴스 수, 모델 변형(Variant) 등을 설정
3. **엔드포인트 생성(CreateEndpoint)**: 실제 인프라를 프로비저닝하고 모델을 배포

### 모델 서버

SageMaker는 프레임워크에 따라 다양한 모델 서버를 사용합니다.

- **TorchServe**: PyTorch 모델용
- **TensorFlow Serving**: TensorFlow 모델용
- **Multi Model Server (MMS)**: 범용 모델 서버
- **NVIDIA Triton Inference Server**: 고성능 GPU 추론
- **DJL Serving**: 대규모 언어 모델(LLM) 서빙

## 실전 활용

### 사용 사례 1: 실시간 엔드포인트 생성 및 호출

```bash
# 1단계: 모델 생성
aws sagemaker create-model \
  --model-name my-classification-model \
  --primary-container '{
    "Image": "763104351884.dkr.ecr.ap-northeast-2.amazonaws.com/pytorch-inference:1.13-gpu-py39",
    "ModelDataUrl": "s3://my-model-bucket/models/classification/model.tar.gz",
    "Environment": {
      "SAGEMAKER_PROGRAM": "inference.py",
      "SAGEMAKER_SUBMIT_DIRECTORY": "s3://my-model-bucket/models/classification/sourcedir.tar.gz"
    }
  }' \
  --execution-role-arn arn:aws:iam::123456789012:role/SageMakerRole

# 2단계: 엔드포인트 구성 생성
aws sagemaker create-endpoint-config \
  --endpoint-config-name my-classification-endpoint-config \
  --production-variants '[
    {
      "VariantName": "primary",
      "ModelName": "my-classification-model",
      "InstanceType": "ml.g4dn.xlarge",
      "InitialInstanceCount": 2,
      "InitialVariantWeight": 1.0
    }
  ]'

# 3단계: 엔드포인트 생성
aws sagemaker create-endpoint \
  --endpoint-name my-classification-endpoint \
  --endpoint-config-name my-classification-endpoint-config

# 엔드포인트 생성 상태 확인 (InService가 될 때까지)
aws sagemaker describe-endpoint \
  --endpoint-name my-classification-endpoint \
  --query '{Status: EndpointStatus, CreationTime: CreationTime}'

# 엔드포인트 호출 (추론 요청)
aws sagemaker-runtime invoke-endpoint \
  --endpoint-name my-classification-endpoint \
  --content-type application/json \
  --body '{"features": [1.5, 2.3, 4.1, 0.8]}' \
  output.json

# 응답 확인
cat output.json
```

### 사용 사례 2: 서버리스 엔드포인트 생성

```bash
# 서버리스 엔드포인트 구성 생성
aws sagemaker create-endpoint-config \
  --endpoint-config-name serverless-endpoint-config \
  --production-variants '[
    {
      "VariantName": "primary",
      "ModelName": "my-classification-model",
      "ServerlessConfig": {
        "MemorySizeInMB": 2048,
        "MaxConcurrency": 10,
        "ProvisionedConcurrency": 2
      }
    }
  ]'

# 서버리스 엔드포인트 생성
aws sagemaker create-endpoint \
  --endpoint-name my-serverless-endpoint \
  --endpoint-config-name serverless-endpoint-config

# 상태 확인
aws sagemaker describe-endpoint \
  --endpoint-name my-serverless-endpoint \
  --query '{Status: EndpointStatus, ProductionVariants: ProductionVariants}'
```

### 사용 사례 3: 오토스케일링 설정

```bash
# 스케일링 대상 등록
aws application-autoscaling register-scalable-target \
  --service-namespace sagemaker \
  --resource-id endpoint/my-classification-endpoint/variant/primary \
  --scalable-dimension sagemaker:variant:DesiredInstanceCount \
  --min-capacity 2 \
  --max-capacity 10

# 대상 추적 스케일링 정책 생성
aws application-autoscaling put-scaling-policy \
  --service-namespace sagemaker \
  --resource-id endpoint/my-classification-endpoint/variant/primary \
  --scalable-dimension sagemaker:variant:DesiredInstanceCount \
  --policy-name target-tracking-policy \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 1000,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"
    },
    "ScaleInCooldown": 300,
    "ScaleOutCooldown": 60
  }'

# 스케일링 정책 확인
aws application-autoscaling describe-scaling-policies \
  --service-namespace sagemaker \
  --resource-id endpoint/my-classification-endpoint/variant/primary
```

### 사용 사례 4: 블루/그린 배포로 모델 업데이트

```bash
# 새 모델 생성
aws sagemaker create-model \
  --model-name my-classification-model-v2 \
  --primary-container '{
    "Image": "763104351884.dkr.ecr.ap-northeast-2.amazonaws.com/pytorch-inference:1.13-gpu-py39",
    "ModelDataUrl": "s3://my-model-bucket/models/classification-v2/model.tar.gz"
  }' \
  --execution-role-arn arn:aws:iam::123456789012:role/SageMakerRole

# 새 엔드포인트 구성 (블루/그린)
aws sagemaker create-endpoint-config \
  --endpoint-config-name my-classification-endpoint-config-v2 \
  --production-variants '[
    {
      "VariantName": "primary",
      "ModelName": "my-classification-model-v2",
      "InstanceType": "ml.g4dn.xlarge",
      "InitialInstanceCount": 2,
      "InitialVariantWeight": 1.0
    }
  ]'

# 엔드포인트 업데이트 (블루/그린 배포, 카나리 전략)
aws sagemaker update-endpoint \
  --endpoint-name my-classification-endpoint \
  --endpoint-config-name my-classification-endpoint-config-v2 \
  --deployment-config '{
    "BlueGreenUpdatePolicy": {
      "TrafficRoutingConfiguration": {
        "Type": "CANARY",
        "CanarySize": {
          "Type": "INSTANCE_COUNT",
          "Value": 1
        },
        "WaitIntervalInSeconds": 600
      },
      "TerminationWaitInSeconds": 300,
      "MaximumExecutionTimeoutInSeconds": 3600
    },
    "AutoRollbackConfiguration": {
      "Alarms": [
        {
          "AlarmName": "high-error-rate-alarm"
        }
      ]
    }
  }'

# 배포 진행 상태 확인
aws sagemaker describe-endpoint \
  --endpoint-name my-classification-endpoint \
  --query '{Status: EndpointStatus, UpdateEndpointStatus: LastEndpointConfigName}'
```

### 사용 사례 5: 비동기 엔드포인트

```bash
# 비동기 엔드포인트 구성
aws sagemaker create-endpoint-config \
  --endpoint-config-name async-endpoint-config \
  --production-variants '[
    {
      "VariantName": "primary",
      "ModelName": "my-large-model",
      "InstanceType": "ml.g5.xlarge",
      "InitialInstanceCount": 1
    }
  ]' \
  --async-inference-config '{
    "OutputConfig": {
      "S3OutputPath": "s3://my-model-bucket/async-output/",
      "NotificationConfig": {
        "SuccessTopic": "arn:aws:sns:ap-northeast-2:123456789012:async-success",
        "ErrorTopic": "arn:aws:sns:ap-northeast-2:123456789012:async-error"
      }
    },
    "ClientConfig": {
      "MaxConcurrentInvocationsPerInstance": 4
    }
  }'

# 비동기 엔드포인트 생성
aws sagemaker create-endpoint \
  --endpoint-name my-async-endpoint \
  --endpoint-config-name async-endpoint-config

# 비동기 추론 호출 (입력 데이터를 S3에 저장)
aws s3 cp large_input.json s3://my-model-bucket/async-input/request-001.json

aws sagemaker-runtime invoke-endpoint-async \
  --endpoint-name my-async-endpoint \
  --input-location s3://my-model-bucket/async-input/request-001.json \
  --content-type application/json
```

## 모범 사례/보안

### 인스턴스 타입 선택 가이드

| 사용 사례 | 권장 인스턴스 | 이유 |
|----------|-------------|------|
| CPU 기반 경량 모델 | ml.c5.xlarge | 비용 효율적, 높은 CPU 성능 |
| GPU 기반 딥러닝 | ml.g4dn.xlarge | GPU 추론 최적화, 합리적 가격 |
| 대규모 언어 모델 | ml.g5.xlarge ~ ml.p4d.24xlarge | 높은 GPU 메모리 |
| 메모리 집약적 모델 | ml.r5.xlarge | 높은 메모리 용량 |
| ARM 기반 비용 최적화 | ml.c7g.xlarge | Graviton 프로세서, 비용 절감 |
| 추론 전용 칩 | ml.inf1.xlarge | AWS Inferentia, 최저 비용 |

### 비용 최적화

1. **적절한 엔드포인트 유형 선택**: 트래픽 패턴에 따라 실시간/서버리스/비동기/배치 중 적합한 유형을 선택합니다.
2. **오토스케일링 활용**: 트래픽 변동에 맞춰 인스턴스 수를 자동 조절합니다.
3. **Savings Plans 적용**: 안정적인 워크로드에는 SageMaker Savings Plans를 적용하여 최대 64% 할인을 받습니다.
4. **AWS Inferentia 활용**: 추론 전용 칩인 AWS Inferentia(Inf1/Inf2 인스턴스)를 사용하면 GPU 대비 최대 2.3배의 처리량과 70% 비용 절감을 달성할 수 있습니다.
5. **멀티 모델 엔드포인트**: 수백~수천 개의 모델을 하나의 엔드포인트로 통합합니다.

### 보안 모범 사례

1. **VPC 엔드포인트**: SageMaker Runtime API를 VPC 엔드포인트를 통해 호출하여 인터넷을 거치지 않도록 합니다.

```bash
# VPC 엔드포인트 생성
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --service-name com.amazonaws.ap-northeast-2.sagemaker.runtime \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-0123456789abcdef0 \
  --security-group-ids sg-0123456789abcdef0 \
  --private-dns-enabled
```

2. **IAM 정책**: 엔드포인트 호출 권한을 세분화합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sagemaker:InvokeEndpoint",
      "Resource": "arn:aws:sagemaker:ap-northeast-2:123456789012:endpoint/my-classification-endpoint"
    }
  ]
}
```

3. **데이터 암호화**: 추론 요청/응답은 TLS로 암호화되며, 모델 아티팩트는 KMS로 암호화합니다.

4. **모니터링**: CloudWatch 메트릭을 통해 엔드포인트 성능을 지속적으로 모니터링합니다.

```bash
# 엔드포인트 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace AWS/SageMaker \
  --metric-name Invocations \
  --dimensions Name=EndpointName,Value=my-classification-endpoint \
               Name=VariantName,Value=primary \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum

# 지연 시간 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace AWS/SageMaker \
  --metric-name ModelLatency \
  --dimensions Name=EndpointName,Value=my-classification-endpoint \
               Name=VariantName,Value=primary \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Average
```

## 관련 서비스 비교

### SageMaker Endpoint vs AWS Lambda

| 항목 | SageMaker Endpoint | AWS Lambda |
|------|-------------------|------------|
| 주요 용도 | ML 추론 전용 | 범용 서버리스 |
| GPU 지원 | 지원 | 미지원 |
| 최대 페이로드 | 6MB (실시간) / 1GB (비동기) | 6MB |
| 최대 실행 시간 | 60초 (실시간) / 3600초 (비동기) | 900초 |
| 콜드 스타트 | 서버리스만 해당 | 항상 해당 |
| 모델 크기 | 제한 없음 | ~10GB (컨테이너) |
| 오토스케일링 | 네이티브 | 자동 |
| 비용 | 인스턴스 시간/요청 기반 | 요청 + 실행 시간 |

### SageMaker Endpoint 유형 비교

| 항목 | 실시간 | 서버리스 | 비동기 | 배치 변환 |
|------|--------|---------|--------|----------|
| 지연 시간 | 밀리초~초 | 초~십수 초 | 초~분 | 분~시간 |
| 최대 페이로드 | 6MB | 6MB | 1GB | 무제한 |
| 최대 타임아웃 | 60초 | 60초 | 3600초 | 무제한 |
| 0으로 축소 | 불가 | 가능 | 가능 | 자동 해제 |
| 최적 사용 사례 | API 서빙 | 간헐적 트래픽 | 대용량 입력 | 전체 데이터셋 |

### SageMaker Endpoint vs Google Vertex AI Endpoint

| 항목 | SageMaker Endpoint | Vertex AI Endpoint |
|------|-------------------|--------------------|
| 배포 방식 | 4가지 | 3가지 (실시간/배치/서버리스) |
| 멀티 모델 | MME 지원 | 지원 |
| 블루/그린 | 네이티브 | 트래픽 분할 |
| 섀도 테스트 | 지원 | 제한적 |
| 추론 칩 | Inferentia + GPU | TPU + GPU |
| 프레임워크 | 다양 | 다양 |

## 요약

Amazon SageMaker Endpoint는 ML 모델을 프로덕션에 배포하기 위한 포괄적인 관리형 추론 인프라입니다.

핵심 특징을 정리하면 다음과 같습니다.

- **네 가지 배포 방식**: 실시간, 서버리스, 비동기, 배치 변환으로 모든 추론 패턴을 지원
- **멀티 모델/멀티 컨테이너**: 하나의 엔드포인트에서 여러 모델을 효율적으로 서빙
- **오토스케일링**: 대상 추적, 단계, 예약 스케일링으로 트래픽 변동에 자동 대응
- **무중단 배포**: 블루/그린, 카나리 배포로 안전한 모델 업데이트
- **섀도 테스트**: 프로덕션 트래픽으로 새 모델을 안전하게 검증
- **추론 파이프라인**: 전처리, 추론, 후처리를 하나의 엔드포인트에서 수행
- **비용 최적화**: Inferentia 칩, Savings Plans, 서버리스 엔드포인트 등 다양한 비용 절감 옵션

엔드포인트 유형 선택 시에는 트래픽 패턴, 지연 시간 요구사항, 페이로드 크기, 비용 예산을 종합적으로 고려해야 합니다. 대부분의 실시간 서빙에는 실시간 엔드포인트, 간헐적 사용에는 서버리스, 대용량 처리에는 비동기 엔드포인트를 선택하는 것이 바람직합니다.