## 개요

AWS Batch는 배치 컴퓨팅 워크로드를 AWS 클라우드에서 효율적으로 실행할 수 있도록 설계된 완전관리형 서비스입니다. 데이터 분석, 머신러닝 학습, 금융 모델링, 영상 렌더링 등 대규모 병렬 처리가 필요한 작업을 자동으로 스케줄링하고 실행합니다.

기존 온프레미스 환경에서 배치 처리를 운영하려면 클러스터 관리, 작업 스케줄링, 리소스 프로비저닝 등 인프라 관리에 상당한 노력이 필요했습니다. AWS Batch는 이러한 복잡성을 제거하고, 사용자가 비즈니스 로직에만 집중할 수 있게 해줍니다.

AWS Batch의 핵심 가치는 다음과 같습니다.

- 인프라 관리 불필요: 컴퓨팅 리소스의 프로비저닝과 스케일링을 자동으로 처리합니다.
- 비용 최적화: Spot 인스턴스를 활용하여 최대 90%까지 비용을 절감할 수 있습니다.
- 유연한 스케줄링: 작업 우선순위와 의존성을 기반으로 지능적인 스케줄링을 제공합니다.
- 다양한 컴퓨팅 옵션: EC2, Fargate, EKS 등 다양한 컴퓨팅 환경을 지원합니다.

## 핵심 기능

### 작업 정의 (Job Definition)

작업 정의는 AWS Batch에서 실행할 작업의 청사진입니다. 컨테이너 이미지, vCPU/메모리 요구사항, 환경 변수, 마운트 포인트 등을 명시합니다.

```json
{
  "jobDefinitionName": "data-processing-job",
  "type": "container",
  "containerProperties": {
    "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/data-processor:latest",
    "vcpus": 4,
    "memory": 8192,
    "command": ["python", "process.py", "Ref::input_file"],
    "environment": [
      {"name": "AWS_DEFAULT_REGION", "value": "ap-northeast-2"},
      {"name": "OUTPUT_BUCKET", "value": "my-output-bucket"}
    ],
    "mountPoints": [
      {
        "containerPath": "/data",
        "readOnly": false,
        "sourceVolume": "data-volume"
      }
    ],
    "volumes": [
      {
        "name": "data-volume",
        "host": {"sourcePath": "/tmp/data"}
      }
    ]
  },
  "retryStrategy": {
    "attempts": 3
  },
  "timeout": {
    "attemptDurationSeconds": 3600
  }
}
```

AWS CLI를 사용하여 작업 정의를 등록하는 방법은 다음과 같습니다.

```bash
# 작업 정의 등록
aws batch register-job-definition \
  --job-definition-name data-processing-job \
  --type container \
  --container-properties '{
    "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/data-processor:latest",
    "vcpus": 4,
    "memory": 8192,
    "command": ["python", "process.py"],
    "jobRoleArn": "arn:aws:iam::123456789012:role/BatchJobRole"
  }' \
  --retry-strategy attempts=3 \
  --timeout attemptDurationSeconds=3600

# 등록된 작업 정의 조회
aws batch describe-job-definitions \
  --job-definition-name data-processing-job \
  --status ACTIVE
```

### 작업 대기열 (Job Queue)

작업 대기열은 제출된 작업이 컴퓨팅 환경에서 실행되기를 기다리는 장소입니다. 우선순위 기반 스케줄링을 지원하며, 여러 컴퓨팅 환경과 연결할 수 있습니다.

```bash
# 작업 대기열 생성
aws batch create-job-queue \
  --job-queue-name high-priority-queue \
  --state ENABLED \
  --priority 100 \
  --compute-environment-order '[
    {"order": 1, "computeEnvironment": "on-demand-env"},
    {"order": 2, "computeEnvironment": "spot-env"}
  ]'

# 작업 대기열 상태 확인
aws batch describe-job-queues \
  --job-queues high-priority-queue
```

대기열의 우선순위 값이 높을수록 먼저 스케줄링됩니다. 하나의 컴퓨팅 환경에 여러 대기열을 연결하면, 우선순위에 따라 리소스가 할당됩니다.

### 컴퓨팅 환경 (Compute Environment)

컴퓨팅 환경은 작업이 실행되는 실제 인프라입니다. 관리형(Managed)과 비관리형(Unmanaged) 두 가지 유형이 있습니다.

```bash
# 관리형 EC2 컴퓨팅 환경 생성
aws batch create-compute-environment \
  --compute-environment-name spot-compute-env \
  --type MANAGED \
  --state ENABLED \
  --compute-resources '{
    "type": "SPOT",
    "allocationStrategy": "SPOT_CAPACITY_OPTIMIZED",
    "minvCpus": 0,
    "maxvCpus": 256,
    "desiredvCpus": 0,
    "instanceTypes": ["m5.xlarge", "m5.2xlarge", "c5.xlarge", "c5.2xlarge"],
    "subnets": ["subnet-0123456789abcdef0"],
    "securityGroupIds": ["sg-0123456789abcdef0"],
    "instanceRole": "arn:aws:iam::123456789012:instance-profile/ecsInstanceRole",
    "spotIamFleetRole": "arn:aws:iam::123456789012:role/AmazonEC2SpotFleetRole"
  }'

# Fargate 컴퓨팅 환경 생성
aws batch create-compute-environment \
  --compute-environment-name fargate-compute-env \
  --type MANAGED \
  --state ENABLED \
  --compute-resources '{
    "type": "FARGATE",
    "maxvCpus": 256,
    "subnets": ["subnet-0123456789abcdef0"],
    "securityGroupIds": ["sg-0123456789abcdef0"]
  }'
```

### 배열 작업 (Array Jobs)

배열 작업은 동일한 작업 정의를 기반으로 여러 작업 인스턴스를 한 번에 실행하는 기능입니다. 대규모 병렬 처리에 매우 유용합니다.

```bash
# 1000개의 배열 작업 제출
aws batch submit-job \
  --job-name data-processing-array \
  --job-queue high-priority-queue \
  --job-definition data-processing-job \
  --array-properties size=1000

# 배열 작업 상태 확인
aws batch list-jobs \
  --job-queue high-priority-queue \
  --filters name=JOB_NAME,values=data-processing-array
```

각 배열 작업 인스턴스는 `AWS_BATCH_JOB_ARRAY_INDEX` 환경 변수를 통해 자신의 인덱스를 알 수 있으며, 이를 활용하여 데이터를 분할 처리할 수 있습니다.

### 작업 의존성 (Job Dependencies)

작업 간 의존성을 설정하여 워크플로를 구성할 수 있습니다.

```bash
# 첫 번째 작업 제출
JOB_ID_1=$(aws batch submit-job \
  --job-name extract-data \
  --job-queue high-priority-queue \
  --job-definition extract-job \
  --query 'jobId' --output text)

# 두 번째 작업 (첫 번째 작업에 의존)
JOB_ID_2=$(aws batch submit-job \
  --job-name transform-data \
  --job-queue high-priority-queue \
  --job-definition transform-job \
  --depends-on jobId=$JOB_ID_1 \
  --query 'jobId' --output text)

# 세 번째 작업 (두 번째 작업에 의존)
aws batch submit-job \
  --job-name load-data \
  --job-queue high-priority-queue \
  --job-definition load-job \
  --depends-on jobId=$JOB_ID_2
```

## 아키텍처/동작 원리

AWS Batch의 내부 동작은 크게 네 단계로 구분됩니다.

### 1단계: 작업 제출

사용자가 작업을 제출하면 AWS Batch 스케줄러가 해당 작업을 작업 대기열에 배치합니다. 작업은 SUBMITTED, PENDING, RUNNABLE, STARTING, RUNNING, SUCCEEDED, FAILED 상태를 순차적으로 거칩니다.

### 2단계: 스케줄링

AWS Batch 스케줄러는 대기열의 우선순위, 작업 의존성, 리소스 요구사항을 고려하여 작업 실행 순서를 결정합니다. 스케줄러는 주기적으로(일반적으로 몇 초 간격) 대기열을 확인하고 실행 가능한 작업을 컴퓨팅 환경에 할당합니다.

### 3단계: 리소스 프로비저닝

관리형 컴퓨팅 환경의 경우, AWS Batch가 자동으로 EC2 인스턴스 또는 Fargate 태스크를 프로비저닝합니다. Spot 인스턴스를 사용하는 경우, SPOT_CAPACITY_OPTIMIZED 전략을 통해 중단 가능성이 가장 낮은 인스턴스 풀에서 용량을 확보합니다.

### 4단계: 작업 실행

프로비저닝된 리소스에서 Docker 컨테이너가 실행되고, 작업이 완료되면 결과를 CloudWatch Logs에 기록합니다. 작업 실패 시 재시도 전략에 따라 자동으로 재실행됩니다.

### 아키텍처 다이어그램 구성 요소

전체 흐름을 정리하면 다음과 같습니다.

1. 사용자/EventBridge/Step Functions에서 작업 제출
2. Job Queue에서 우선순위 기반 대기
3. Scheduler가 Compute Environment에 작업 할당
4. EC2/Fargate에서 컨테이너 실행
5. CloudWatch Logs/S3로 결과 저장
6. EventBridge/SNS를 통한 상태 알림

## 실전 활용

### ETL 파이프라인 구축

데이터 레이크 환경에서 AWS Batch를 활용한 ETL 파이프라인을 구축하는 예제입니다.

```python
import boto3
import json

batch_client = boto3.client('batch', region_name='ap-northeast-2')

def submit_etl_pipeline(source_bucket, target_bucket, date):
    """ETL 파이프라인을 AWS Batch로 실행합니다."""
    
    # Extract 단계
    extract_response = batch_client.submit_job(
        jobName=f'extract-{date}',
        jobQueue='etl-queue',
        jobDefinition='extract-job:1',
        containerOverrides={
            'environment': [
                {'name': 'SOURCE_BUCKET', 'value': source_bucket},
                {'name': 'PROCESS_DATE', 'value': date}
            ]
        }
    )
    extract_job_id = extract_response['jobId']
    
    # Transform 단계 (Extract 완료 후 실행)
    transform_response = batch_client.submit_job(
        jobName=f'transform-{date}',
        jobQueue='etl-queue',
        jobDefinition='transform-job:1',
        dependsOn=[{'jobId': extract_job_id}],
        containerOverrides={
            'environment': [
                {'name': 'PROCESS_DATE', 'value': date}
            ]
        }
    )
    transform_job_id = transform_response['jobId']
    
    # Load 단계 (Transform 완료 후 실행)
    load_response = batch_client.submit_job(
        jobName=f'load-{date}',
        jobQueue='etl-queue',
        jobDefinition='load-job:1',
        dependsOn=[{'jobId': transform_job_id}],
        containerOverrides={
            'environment': [
                {'name': 'TARGET_BUCKET', 'value': target_bucket},
                {'name': 'PROCESS_DATE', 'value': date}
            ]
        }
    )
    
    return {
        'extract_job_id': extract_job_id,
        'transform_job_id': transform_job_id,
        'load_job_id': load_response['jobId']
    }
```

### EventBridge를 활용한 자동 트리거

S3에 파일이 업로드되면 자동으로 배치 작업을 실행하는 구성입니다.

```bash
# EventBridge 규칙 생성
aws events put-rule \
  --name "s3-upload-trigger" \
  --event-pattern '{
    "source": ["aws.s3"],
    "detail-type": ["Object Created"],
    "detail": {
      "bucket": {"name": ["input-data-bucket"]},
      "object": {"key": [{"prefix": "raw/"}]}
    }
  }'

# 대상으로 AWS Batch 작업 등록
aws events put-targets \
  --rule s3-upload-trigger \
  --targets '[{
    "Id": "batch-target",
    "Arn": "arn:aws:batch:ap-northeast-2:123456789012:job-queue/processing-queue",
    "RoleArn": "arn:aws:iam::123456789012:role/EventBridgeBatchRole",
    "BatchParameters": {
      "JobDefinition": "process-uploaded-file:1",
      "JobName": "process-upload"
    }
  }]'
```

### GPU 워크로드 (머신러닝 학습)

GPU 인스턴스를 활용한 머신러닝 학습 작업 구성입니다.

```bash
# GPU 컴퓨팅 환경 생성
aws batch create-compute-environment \
  --compute-environment-name gpu-training-env \
  --type MANAGED \
  --state ENABLED \
  --compute-resources '{
    "type": "EC2",
    "allocationStrategy": "BEST_FIT_PROGRESSIVE",
    "minvCpus": 0,
    "maxvCpus": 128,
    "instanceTypes": ["p3.2xlarge", "p3.8xlarge", "g4dn.xlarge"],
    "subnets": ["subnet-0123456789abcdef0"],
    "securityGroupIds": ["sg-0123456789abcdef0"],
    "instanceRole": "arn:aws:iam::123456789012:instance-profile/ecsInstanceRole"
  }'

# GPU 작업 정의 등록
aws batch register-job-definition \
  --job-definition-name ml-training-job \
  --type container \
  --container-properties '{
    "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/ml-trainer:latest",
    "vcpus": 8,
    "memory": 61440,
    "resourceRequirements": [
      {"type": "GPU", "value": "1"}
    ],
    "command": ["python", "train.py", "--epochs", "100"],
    "jobRoleArn": "arn:aws:iam::123456789012:role/MLTrainingRole"
  }'
```

### 멀티 노드 병렬 작업

대규모 과학 계산이나 시뮬레이션에 적합한 멀티 노드 병렬 작업 설정입니다.

```bash
# 멀티 노드 작업 정의 등록
aws batch register-job-definition \
  --job-definition-name multi-node-simulation \
  --type multinode \
  --node-properties '{
    "numNodes": 4,
    "mainNode": 0,
    "nodeRangeProperties": [
      {
        "targetNodes": "0:3",
        "container": {
          "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/mpi-simulator:latest",
          "vcpus": 16,
          "memory": 65536,
          "command": ["mpirun", "-np", "64", "./simulation"]
        }
      }
    ]
  }'
```

## 모범 사례/보안

### 비용 최적화

1. **Spot 인스턴스 활용**: 내결함성이 있는 워크로드에는 반드시 Spot 인스턴스를 사용합니다. SPOT_CAPACITY_OPTIMIZED 전략을 선택하면 중단 가능성이 가장 낮은 풀에서 인스턴스를 확보합니다.

2. **적절한 리소스 사이징**: 작업 정의에서 vCPU와 메모리를 과도하게 할당하지 않도록 합니다. CloudWatch 메트릭을 통해 실제 사용량을 모니터링하고 조정합니다.

```bash
# 작업 로그에서 리소스 사용량 확인
aws logs get-log-events \
  --log-group-name /aws/batch/job \
  --log-stream-name data-processing-job/default/abc123def456
```

3. **minvCpus를 0으로 설정**: 컴퓨팅 환경의 minvCpus를 0으로 설정하면 작업이 없을 때 인스턴스가 종료되어 비용이 발생하지 않습니다.

### 보안 모범 사례

1. **최소 권한 원칙**: 작업 역할(Job Role)에는 해당 작업이 필요로 하는 최소한의 권한만 부여합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::input-bucket/*",
        "arn:aws:s3:::output-bucket/*"
      ]
    }
  ]
}
```

2. **프라이빗 서브넷 사용**: 컴퓨팅 환경을 프라이빗 서브넷에 배치하고, NAT Gateway 또는 VPC 엔드포인트를 통해 외부 통신을 합니다.

3. **ECR 이미지 스캔**: 컨테이너 이미지를 ECR에 저장하고, 이미지 스캔 기능을 활성화하여 보안 취약점을 자동으로 탐지합니다.

4. **암호화**: S3 버킷의 서버 측 암호화를 활성화하고, 민감한 환경 변수는 AWS Secrets Manager를 통해 주입합니다.

### 운영 모범 사례

1. **재시도 전략 설정**: 일시적인 오류에 대비하여 적절한 재시도 횟수를 설정합니다.
2. **타임아웃 설정**: 무한 루프에 빠진 작업을 방지하기 위해 작업 타임아웃을 반드시 설정합니다.
3. **CloudWatch 알람 구성**: 작업 실패율, 대기열 깊이 등에 대한 알람을 설정하여 이상 상황을 조기에 감지합니다.

```bash
# 작업 실패 알람 생성
aws cloudwatch put-metric-alarm \
  --alarm-name batch-job-failures \
  --namespace AWS/Batch \
  --metric-name FailedJobCount \
  --dimensions Name=JobQueue,Value=high-priority-queue \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:batch-alerts
```

## 관련 서비스 비교

### AWS Batch vs AWS Lambda

| 항목 | AWS Batch | AWS Lambda |
|------|-----------|------------|
| 실행 시간 제한 | 무제한 (타임아웃 설정 가능) | 최대 15분 |
| 컴퓨팅 리소스 | EC2/Fargate (GPU 포함) | 최대 10GB 메모리 |
| 컨테이너 지원 | Docker 컨테이너 기본 | 컨테이너 이미지 지원 |
| 시작 지연 | 수 분 (인스턴스 프로비저닝) | 밀리초~초 단위 |
| 적합한 워크로드 | 장시간 대규모 배치 처리 | 짧은 이벤트 기반 처리 |
| 비용 모델 | EC2/Fargate 사용 시간 | 요청 수 + 실행 시간 |

### AWS Batch vs AWS Step Functions

Step Functions는 워크플로 오케스트레이션 서비스이며, AWS Batch는 배치 작업 실행 서비스입니다. 실무에서는 Step Functions에서 AWS Batch 작업을 호출하는 패턴을 자주 사용합니다. Step Functions이 전체 파이프라인의 흐름을 제어하고, 각 단계의 실제 처리는 AWS Batch가 담당하는 구조입니다.

### AWS Batch vs Amazon EMR

EMR은 Apache Spark, Hadoop 등 빅데이터 프레임워크에 특화된 서비스이고, AWS Batch는 범용 배치 처리 서비스입니다. Spark 기반 데이터 처리에는 EMR이, Docker 컨테이너 기반 커스텀 처리에는 AWS Batch가 적합합니다.

### AWS Batch on EKS

AWS Batch on EKS를 사용하면 기존 EKS 클러스터에서 Batch 작업을 실행할 수 있습니다. Kubernetes 생태계의 도구와 사례를 활용하면서도 AWS Batch의 스케줄링 기능을 함께 사용할 수 있다는 장점이 있습니다.

```bash
# EKS 기반 컴퓨팅 환경 생성
aws batch create-compute-environment \
  --compute-environment-name eks-batch-env \
  --type MANAGED \
  --state ENABLED \
  --eks-configuration '{
    "eksClusterArn": "arn:aws:eks:ap-northeast-2:123456789012:cluster/my-cluster",
    "kubernetesNamespace": "batch"
  }'
```

## 요약

AWS Batch는 대규모 배치 컴퓨팅 워크로드를 효율적으로 관리할 수 있는 완전관리형 서비스입니다. 작업 정의, 작업 대기열, 컴퓨팅 환경이라는 세 가지 핵심 구성 요소를 통해 유연한 배치 처리 환경을 구축할 수 있습니다.

Spot 인스턴스를 활용한 비용 최적화, 배열 작업을 통한 대규모 병렬 처리, 작업 의존성을 활용한 워크플로 구성 등 다양한 기능을 제공합니다. ETL 파이프라인, 머신러닝 학습, 과학 시뮬레이션, 영상 렌더링 등 다양한 분야에서 활용할 수 있으며, EventBridge, Step Functions, S3 등 다른 AWS 서비스와의 통합을 통해 자동화된 데이터 처리 파이프라인을 구축할 수 있습니다.

AWS Batch를 도입할 때는 워크로드 특성에 맞는 컴퓨팅 환경 선택, 적절한 재시도 및 타임아웃 전략 설정, 최소 권한 원칙에 따른 IAM 설정을 반드시 고려해야 합니다.