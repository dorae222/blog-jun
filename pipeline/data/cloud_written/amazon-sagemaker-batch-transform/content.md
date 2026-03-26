# Amazon SageMaker Batch Transform - 대규모 배치 추론 완벽 가이드

## 개요

Amazon SageMaker Batch Transform은 미리 저장된 대량의 데이터에 대해 오프라인 추론을 수행할 수 있는 완전관리형 배치 추론 서비스입니다. 실시간 API 호출이 필요 없으며, S3에 저장된 파일을 기반으로 한 번에 예측을 수행하고 결과를 저장하는 방식으로 동작합니다.

실시간 응답이 필요하지 않은 대량 예측 작업에서 SageMaker Batch Transform은 비용 효율성과 운영 편의성을 모두 충족하는 최적의 선택지입니다. 엔드포인트를 상시 유지할 필요가 없으므로 사용한 시간만큼만 비용이 발생하며, 작업 완료 후 인스턴스가 자동으로 종료됩니다.

주요 활용 시나리오는 다음과 같습니다.

- 야간 배치로 수백만 건의 고객 데이터에 대한 이탈 예측 수행
- 월말 정산 시 대량의 거래 데이터에 대한 이상 탐지
- 모델 검증을 위한 전체 테스트 데이터셋 추론
- 데이터 전처리 파이프라인의 일부로 특성 변환 수행

## 핵심 기능

### 자동 리소스 관리

Batch Transform은 작업 실행 시 지정된 인스턴스를 자동으로 프로비저닝하고, 작업 완료 후 자동으로 종료합니다. 운영자가 인스턴스 생명주기를 직접 관리할 필요가 없습니다.

| 항목 | 설명 |
|------|------|
| 서비스 유형 | 비동기 오프라인 추론 |
| 입출력 형태 | S3 기반 파일 입출력 |
| 운영 형태 | 일회성 실행 (엔드포인트 불필요) |
| 지원 포맷 | CSV, JSON, RecordIO, TFRecord |
| 최대 페이로드 | 개별 레코드 최대 100MB |

### 데이터 분배 전략

Batch Transform은 두 가지 데이터 분배 전략을 지원합니다.

**SingleRecord 전략**: 입력 파일의 각 레코드를 개별 추론 요청으로 전송합니다. 레코드 간 독립적인 예측이 필요한 경우에 적합합니다.

**MultiRecord 전략**: 여러 레코드를 하나의 미니배치로 묶어 전송합니다. MaxPayloadInMB 설정에 따라 배치 크기가 결정되며, 처리량이 크게 향상됩니다.

### 데이터 조인 및 필터링

Batch Transform은 추론 결과를 원본 입력 데이터와 조인하는 기능을 제공합니다. `AssembleWith` 파라미터로 출력 파일 결합 방식을 지정하고, `JoinSource` 파라미터로 입력 데이터를 출력에 포함할 수 있습니다.

```python
transformer = sagemaker.transformer.Transformer(
    model_name='my-model',
    instance_count=1,
    instance_type='ml.m5.xlarge',
    output_path='s3://my-bucket/output/',
    assemble_with='Line',
    accept='text/csv'
)

transformer.transform(
    data='s3://my-bucket/input/',
    content_type='text/csv',
    split_type='Line',
    join_source='Input'
)
```

## 아키텍처 및 동작 원리

Batch Transform의 전체 워크플로우는 다음과 같이 진행됩니다.

```
[S3 입력 데이터] --> [Batch Transform Job 생성]
                          |
                    [인스턴스 프로비저닝]
                          |
                    [모델 컨테이너 로드]
                          |
                    [데이터 분할 및 분배]
                          |
              +-----------+-----------+
              |           |           |
         [인스턴스1]  [인스턴스2]  [인스턴스N]
              |           |           |
              +-----------+-----------+
                          |
                    [결과 병합]
                          |
                    [S3 출력 저장]
                          |
                    [인스턴스 자동 종료]
```

1단계에서 S3에 입력 데이터를 CSV, JSON 등의 형식으로 준비합니다. 2단계에서 훈련이 완료된 모델을 SageMaker에 등록하거나 기존 모델을 참조합니다. 3단계에서 Batch Transform Job을 생성하면 AWS가 자동으로 클러스터를 시작합니다. 4단계에서 입력 데이터를 분할하여 각 인스턴스에 분배하고 병렬 추론을 수행합니다. 5단계에서 모든 추론이 완료되면 결과를 S3에 저장하고 인스턴스를 자동 종료합니다.

### 다중 인스턴스 병렬 처리

`instance_count`를 2 이상으로 설정하면 입력 데이터가 자동으로 여러 인스턴스에 분배됩니다. 각 인스턴스는 독립적으로 추론을 수행하며, 모든 결과가 출력 경로에 통합됩니다.

## 실전 활용

### AWS CLI를 사용한 Batch Transform Job 생성

```bash
# 모델 생성
aws sagemaker create-model \
    --model-name my-xgboost-model \
    --primary-container '{
        "Image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/sagemaker-xgboost:1.5-1",
        "ModelDataUrl": "s3://my-bucket/models/xgboost/model.tar.gz"
    }' \
    --execution-role-arn arn:aws:iam::123456789012:role/SageMakerRole

# Batch Transform Job 생성
aws sagemaker create-transform-job \
    --transform-job-name my-batch-job-$(date +%Y%m%d-%H%M%S) \
    --model-name my-xgboost-model \
    --transform-input '{
        "DataSource": {
            "S3DataSource": {
                "S3DataType": "S3Prefix",
                "S3Uri": "s3://my-bucket/input/"
            }
        },
        "ContentType": "text/csv",
        "SplitType": "Line"
    }' \
    --transform-output '{
        "S3OutputPath": "s3://my-bucket/output/",
        "AssembleWith": "Line"
    }' \
    --transform-resources '{
        "InstanceType": "ml.m5.xlarge",
        "InstanceCount": 2
    }' \
    --max-payload-in-mb 6 \
    --batch-strategy MultiRecord

# Job 상태 확인
aws sagemaker describe-transform-job \
    --transform-job-name my-batch-job-20240101-120000
```

### SageMaker Python SDK 활용

```python
import sagemaker
from sagemaker import Transformer

session = sagemaker.Session()
role = 'arn:aws:iam::123456789012:role/SageMakerRole'

# Transformer 객체 생성
transformer = Transformer(
    model_name='my-trained-model',
    instance_count=2,
    instance_type='ml.m5.xlarge',
    output_path='s3://my-bucket/output/',
    strategy='MultiRecord',
    max_payload=6,
    assemble_with='Line',
    accept='text/csv'
)

# 배치 추론 실행
transformer.transform(
    data='s3://my-bucket/input/',
    content_type='text/csv',
    split_type='Line',
    join_source='Input'
)

# 작업 완료 대기
transformer.wait()
print(f'Output: {transformer.output_path}')
```

### 대규모 데이터셋 처리 패턴

수백만 건의 레코드를 처리할 때는 데이터를 여러 파일로 분할하여 S3에 업로드하는 것이 효과적입니다.

```python
import pandas as pd
import boto3

def upload_chunked_data(df, bucket, prefix, chunk_size=10000):
    s3 = boto3.client('s3')
    chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]
    
    for idx, chunk in enumerate(chunks):
        key = f'{prefix}/part-{idx:05d}.csv'
        csv_buffer = chunk.to_csv(index=False, header=False)
        s3.put_object(Bucket=bucket, Key=key, Body=csv_buffer)
    
    print(f'{len(chunks)}개 파일 업로드 완료')
```

## 모범 사례 및 보안

### 비용 최적화

- 인스턴스 유형 선택 시 모델 크기와 데이터 특성을 고려합니다. GPU 인스턴스는 딥러닝 모델에, CPU 인스턴스는 전통적 ML 모델에 적합합니다.
- `MaxConcurrentTransforms` 파라미터로 인스턴스당 동시 추론 수를 조절하여 처리량을 극대화합니다.
- 대량 데이터는 여러 인스턴스로 병렬 처리하되, 인스턴스 시작/종료 오버헤드를 고려합니다.

### 보안 설정

```bash
# VPC 내에서 Batch Transform 실행
aws sagemaker create-transform-job \
    --transform-job-name secure-batch-job \
    --model-name my-model \
    --transform-input '{...}' \
    --transform-output '{
        "S3OutputPath": "s3://my-bucket/output/",
        "KmsKeyId": "arn:aws:kms:ap-northeast-2:123456789012:key/my-key-id"
    }' \
    --transform-resources '{
        "InstanceType": "ml.m5.xlarge",
        "InstanceCount": 1,
        "VolumeKmsKeyId": "arn:aws:kms:ap-northeast-2:123456789012:key/my-volume-key"
    }'
```

- S3 출력 데이터에 KMS 암호화를 적용합니다.
- 볼륨 암호화로 인스턴스 스토리지의 임시 데이터를 보호합니다.
- VPC 구성으로 네트워크 격리를 적용하고, IAM 역할에 최소 권한 원칙을 적용합니다.
- CloudWatch Logs를 통해 추론 실행 로그를 모니터링합니다.

### 오류 처리

`MaxPayloadInMB`를 적절히 설정하여 페이로드 크기 초과 오류를 방지합니다. `StopTransformJob` API로 장시간 실행되는 작업을 중단할 수 있으며, CloudWatch 알람으로 비정상 실행 시간을 감지합니다.

## 관련 서비스 비교

| 항목 | Batch Transform | Real-Time Inference | Async Inference | Serverless Inference |
|------|----------------|--------------------|-----------------|-----------------------|
| 응답 시간 | 수분~수시간 | 밀리초~초 | 초~분 | 밀리초~초 |
| 엔드포인트 | 불필요 | 상시 운영 | 상시 운영 | 자동 스케일링 |
| 과금 방식 | 실행 시간 | 인스턴스 가동 시간 | 인스턴스 가동 시간 | 요청당 |
| 최대 페이로드 | 100MB/레코드 | 6MB | 1GB | 4MB |
| 적합한 워크로드 | 대량 일괄 처리 | 실시간 서비스 | 대용량 비동기 | 간헐적 트래픽 |
| 콜드 스타트 | 인스턴스 시작 시간 | 없음 | 없음 | 있음 |

### Batch Transform vs AWS Glue ML Transform

Batch Transform은 SageMaker에서 훈련한 ML 모델의 추론에 특화되어 있습니다. AWS Glue ML Transform은 ETL 파이프라인 내에서 데이터 정제(FindMatches 등)에 초점을 맞춘 서비스입니다. 목적에 따라 적합한 서비스를 선택합니다.

## 요약

Amazon SageMaker Batch Transform은 대규모 데이터에 대한 오프라인 추론을 비용 효율적으로 수행하는 완전관리형 서비스입니다. 엔드포인트를 상시 유지하지 않으므로 비용을 절감할 수 있으며, 다중 인스턴스 병렬 처리로 수백만 건의 데이터를 빠르게 처리할 수 있습니다. S3 기반의 파일 입출력 방식으로 기존 데이터 파이프라인과의 통합이 용이하며, KMS 암호화와 VPC 지원으로 엔터프라이즈 수준의 보안 요건을 충족합니다.