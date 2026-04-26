<!-- infographic-hero -->
![AWS Lambda 핵심 요약](figures/infographic.svg)

*Figure: AWS Lambda 한 장 요약 인포그래픽*

# AWS Lambda 개요 및 실전 활용 가이드

## 개요

AWS Lambda는 2014년 re:Invent에서 발표된 서버리스(Serverless) 함수 실행 서비스로, 클라우드 컴퓨팅 패러다임을 근본적으로 바꾼 대표적인 서비스입니다. 사용자는 코드만 작성하여 업로드하면 되고, 서버 프로비저닝, OS 패치, 오토스케일링, 가용 영역 분산 같은 인프라 관리 작업은 AWS가 모두 자동으로 처리합니다.

전통적인 EC2 기반 워크로드는 트래픽이 없는 시간에도 인스턴스가 항상 실행 중이어야 했고, 트래픽이 갑자기 증가하면 Auto Scaling 그룹이 새 인스턴스를 띄울 때까지 수 분의 지연이 발생했습니다. Lambda는 이러한 한계를 해결하기 위해 다음과 같은 모델을 채택했습니다.

- **이벤트 기반 실행(Event-driven)**: 함수는 특정 이벤트(HTTP 요청, S3 객체 업로드, DynamoDB 변경 등)에 반응하여 호출됩니다.
- **밀리초 단위 과금**: 실제 함수가 실행된 시간만 1ms 단위로 청구됩니다. 호출이 없는 동안에는 비용이 발생하지 않습니다.
- **자동 확장**: 동시에 수만 개의 인스턴스가 자동으로 생성되어 트래픽 폭증을 처리합니다.
- **고가용성**: AWS가 여러 가용 영역(AZ)에 걸쳐 함수 실행 환경을 자동 분산합니다.

Lambda는 현재 마이크로서비스 백엔드, 데이터 처리 파이프라인, IoT 백엔드, 이벤트 기반 자동화, ETL 작업, 챗봇, 모바일 백엔드 등 광범위한 분야에서 활용되고 있습니다.

---

## 핵심 기능

### 1. 다양한 런타임 지원

Lambda는 다양한 프로그래밍 언어를 지원하며, 각 런타임은 AWS가 관리하는 베이스 이미지로 제공됩니다.

| 런타임 | 지원 버전 | 특징 |
|--------|-----------|------|
| Python | 3.9, 3.10, 3.11, 3.12, 3.13 | 데이터 처리/ML 워크로드에 인기 |
| Node.js | 18, 20, 22 | API/웹 백엔드에 적합 |
| Java | 11, 17, 21 | 엔터프라이즈, SnapStart로 콜드 스타트 단축 |
| .NET | 6, 8 | C#/F# 지원, SnapStart 지원 |
| Go | 1.x (provided.al2) | 정적 컴파일, 빠른 콜드 스타트 |
| Ruby | 3.2, 3.3 | Rails 애플리케이션과 통합 |
| Custom Runtime | provided.al2023 | Rust, PHP, COBOL 등 자유로운 구현 |
| Container Image | 최대 10GB | 자체 베이스 이미지로 패키징 |

```bash
# 사용 가능한 런타임 목록 조회
aws lambda list-runtimes \
  --query "Runtimes[]" \
  --output table \
  --region ap-northeast-2

# 특정 런타임의 기본 함수 생성 예시
aws lambda create-function \
  --function-name my-python-function \
  --runtime python3.12 \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --handler app.handler \
  --zip-file fileb://function.zip \
  --memory-size 512 \
  --timeout 30 \
  --region ap-northeast-2
```

### 2. Container Image 지원

2020년부터 Lambda는 OCI 호환 컨테이너 이미지를 함수 패키지로 사용할 수 있게 되었습니다. 기존 ZIP 패키징의 250MB 한도를 넘는 대형 의존성(예: PyTorch, OpenCV, TensorFlow)이 필요한 워크로드에서 특히 유용합니다.

- **이미지 크기 한도**: 최대 10GB
- **베이스 이미지**: AWS 관리 베이스 이미지(`public.ecr.aws/lambda/python:3.12`) 또는 커스텀 이미지
- **Lambda Runtime API**: 컨테이너 내부에서 Lambda가 호출될 수 있도록 RIE(Runtime Interface Emulator) 지원

```dockerfile
# Dockerfile 예시 (Python 3.12 + 머신러닝 의존성)
FROM public.ecr.aws/lambda/python:3.12

# 의존성 설치
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt --target ${LAMBDA_TASK_ROOT}

# 함수 코드 복사
COPY app.py ${LAMBDA_TASK_ROOT}

# 핸들러 지정
CMD ["app.handler"]
```

```bash
# ECR에 이미지 푸시 후 Lambda 함수 생성
aws ecr create-repository --repository-name my-lambda-image --region ap-northeast-2

docker build -t my-lambda-image:latest .
docker tag my-lambda-image:latest 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/my-lambda-image:latest
docker push 123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/my-lambda-image:latest

aws lambda create-function \
  --function-name my-container-function \
  --package-type Image \
  --code ImageUri=123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/my-lambda-image:latest \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --memory-size 2048 \
  --timeout 300 \
  --region ap-northeast-2
```

### 3. Lambda Layers

Lambda Layers는 함수 코드와 의존성을 분리하여 재사용성을 높이는 기능입니다. 공통 라이브러리, SDK, 유틸리티를 별도 Layer로 패키징하여 여러 함수에서 공유할 수 있습니다.

- **최대 5개 Layer 부착 가능**
- **Layer 크기 합계 250MB 이하** (압축 해제 기준)
- **버전 관리**: Layer는 immutable 버전으로 관리되며 ARN에 버전 번호 포함

```bash
# 의존성 패키징
mkdir -p python/lib/python3.12/site-packages
pip install requests pydantic -t python/lib/python3.12/site-packages
zip -r layer.zip python/

# Layer 게시
aws lambda publish-layer-version \
  --layer-name my-shared-deps \
  --description "Shared Python dependencies" \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11 python3.12 \
  --region ap-northeast-2

# 함수에 Layer 연결
aws lambda update-function-configuration \
  --function-name my-python-function \
  --layers arn:aws:lambda:ap-northeast-2:123456789012:layer:my-shared-deps:1 \
  --region ap-northeast-2
```

### 4. SnapStart

SnapStart는 Lambda 함수의 초기화된 상태(JVM warm-up, 클래스 로딩 등)를 스냅샷으로 저장하여 콜드 스타트 시간을 최대 90% 단축하는 기능입니다.

- **지원 런타임**: Java(Corretto 11/17/21), Python(3.12+), .NET(8+)
- **추가 비용 없음** (Java), **Python/.NET은 캐싱/복원 비용 별도**
- **버전 게시 시 스냅샷 생성**: 새 버전을 게시할 때 자동으로 초기화 후 스냅샷 저장

```bash
# Java 함수에 SnapStart 활성화
aws lambda update-function-configuration \
  --function-name my-java-function \
  --snap-start ApplyOn=PublishedVersions \
  --region ap-northeast-2

# 새 버전 게시 (스냅샷 자동 생성)
aws lambda publish-version \
  --function-name my-java-function \
  --description "v1.0 with SnapStart" \
  --region ap-northeast-2
```

### 5. Lambda@Edge

Lambda@Edge는 CloudFront 엣지 로케이션에서 Lambda 함수를 실행하는 기능입니다. HTTP 요청/응답을 엣지에서 변형하여 사용자에게 가까운 위치에서 처리합니다.

- **트리거 시점**: Viewer Request, Viewer Response, Origin Request, Origin Response
- **지원 런타임**: Node.js, Python (제한적)
- **메모리/타임아웃 한도**: Viewer 트리거는 128MB/5초, Origin 트리거는 10240MB/30초
- **활용**: A/B 테스트, 인증 토큰 검증, URL 재작성, 헤더 조작

---

## 아키텍처

### Lambda 실행 환경 구조

Lambda 함수는 내부적으로 다음 계층으로 실행됩니다.

```
[Event Source]
    |
    v
[Lambda Service (Invoke API)]
    |
    v
[Worker Manager / Placement]
    |
    v
[Firecracker MicroVM]
    |   - Linux 커널
    |   - 런타임 (Python/Node.js/JVM 등)
    |   - 함수 코드
    v
[Execution Environment (EE)]
    |
    v
[Handler 호출]
```

1. **Firecracker microVM**: Lambda는 AWS가 자체 개발한 경량 가상화 기술인 Firecracker 위에서 실행됩니다. 부팅 시간은 약 125ms로 매우 짧으며, 강력한 격리성을 제공합니다.
2. **Execution Environment (EE)**: 동일 함수의 후속 호출은 같은 EE에서 재사용됩니다(Warm Start). 글로벌 변수와 `/tmp` 디렉토리(최대 10GB)도 EE 수명 동안 유지됩니다.
3. **동시 실행(Concurrency)**: 새로운 호출이 들어왔을 때 사용 가능한 EE가 없으면 새 EE를 생성합니다(Cold Start).

### 콜드 스타트 vs 웜 스타트

| 단계 | Cold Start | Warm Start |
|------|------------|------------|
| 코드 다운로드 | 발생 | 생략 |
| Firecracker microVM 부팅 | 발생 | 생략 |
| 런타임 초기화 | 발생 | 생략 |
| 핸들러 외부 코드 실행 | 발생 | 생략 |
| 핸들러 호출 | 발생 | 발생 |
| 일반적 추가 지연 | 100ms-수 초 | 거의 없음 |

콜드 스타트를 줄이는 주요 방법은 다음과 같습니다.

- **Provisioned Concurrency**: 미리 지정한 수의 EE를 항상 워밍업 상태로 유지합니다.
- **SnapStart**: 초기화된 상태를 스냅샷으로 저장합니다.
- **Lambda Power Tuning**: 메모리를 늘리면 vCPU 비율도 함께 증가하여 초기화가 빨라집니다.
- **함수 패키지 최소화**: 필요 없는 의존성을 제거합니다.

```bash
# Provisioned Concurrency 설정
aws lambda put-provisioned-concurrency-config \
  --function-name my-python-function \
  --qualifier 1 \
  --provisioned-concurrent-executions 10 \
  --region ap-northeast-2

# Provisioned Concurrency 상태 조회
aws lambda get-provisioned-concurrency-config \
  --function-name my-python-function \
  --qualifier 1 \
  --region ap-northeast-2
```

### 트리거 메커니즘

Lambda는 200개 이상의 AWS 서비스 및 SaaS와 통합되며, 트리거 방식에 따라 두 가지로 구분됩니다.

**Synchronous Invoke (동기 호출)**
- 호출자가 응답을 기다림
- 예: API Gateway, Application Load Balancer, Cognito
- 최대 응답 페이로드: 6MB

**Asynchronous Invoke (비동기 호출)**
- 호출 즉시 반환, 결과는 별도 처리
- 예: S3, SNS, EventBridge, SES
- DLQ(Dead Letter Queue) 또는 OnFailure/OnSuccess 대상 설정 가능

**Stream/Poll-based (스트림 기반)**
- Lambda가 소스에서 폴링하여 배치로 처리
- 예: DynamoDB Streams, Kinesis, SQS, MSK, Amazon MQ
- 배치 크기, Maximum Batch Window, Parallelization Factor 등 조정 가능

```bash
# S3 이벤트 트리거 등록
aws lambda add-permission \
  --function-name my-s3-processor \
  --statement-id s3-trigger \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::my-upload-bucket \
  --region ap-northeast-2

aws s3api put-bucket-notification-configuration \
  --bucket my-upload-bucket \
  --notification-configuration '{
    "LambdaFunctionConfigurations": [{
      "LambdaFunctionArn": "arn:aws:lambda:ap-northeast-2:123456789012:function:my-s3-processor",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {"Key": {"FilterRules": [{"Name": "suffix", "Value": ".jpg"}]}}
    }]
  }'

# SQS 이벤트 소스 매핑
aws lambda create-event-source-mapping \
  --function-name my-queue-processor \
  --event-source-arn arn:aws:sqs:ap-northeast-2:123456789012:my-queue \
  --batch-size 10 \
  --maximum-batching-window-in-seconds 5 \
  --region ap-northeast-2
```

---

## 실전 사용

### 1. API Gateway + Lambda 백엔드

REST API 또는 HTTP API를 Lambda 함수로 처리하는 가장 일반적인 패턴입니다.

```python
# app.py - Python 핸들러 예시
import json

def handler(event, context):
    method = event.get("httpMethod") or event["requestContext"]["http"]["method"]
    path = event.get("path") or event["rawPath"]

    if method == "GET" and path == "/health":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "ok"})
        }

    return {
        "statusCode": 404,
        "body": json.dumps({"error": "Not Found"})
    }
```

```bash
# HTTP API 생성 + Lambda 통합
aws apigatewayv2 create-api \
  --name my-http-api \
  --protocol-type HTTP \
  --target arn:aws:lambda:ap-northeast-2:123456789012:function:my-python-function \
  --region ap-northeast-2

# Lambda에 API Gateway 호출 권한 부여
aws lambda add-permission \
  --function-name my-python-function \
  --statement-id apigw-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:ap-northeast-2:123456789012:abc123/*/*"
```

### 2. 이미지 처리 파이프라인 (S3 + Lambda)

S3에 이미지가 업로드되면 Lambda가 자동으로 썸네일을 생성하는 패턴입니다.

```python
# thumbnail.py
import boto3
from PIL import Image
import io

s3 = boto3.client("s3")

def handler(event, context):
    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # 원본 다운로드
        obj = s3.get_object(Bucket=bucket, Key=key)
        img = Image.open(obj["Body"])

        # 썸네일 생성 (300x300)
        img.thumbnail((300, 300))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)

        # 썸네일 업로드
        thumb_key = f"thumbnails/{key}"
        s3.put_object(
            Bucket=bucket,
            Key=thumb_key,
            Body=buffer.getvalue(),
            ContentType="image/jpeg"
        )
    return {"status": "ok"}
```

### 3. EventBridge 스케줄 트리거 (Cron)

주기적인 작업(예: 매일 오전 9시 보고서 생성)을 EventBridge로 트리거합니다.

```bash
# 매일 09:00 KST(UTC 00:00)에 실행되는 규칙 생성
aws events put-rule \
  --name daily-report-trigger \
  --schedule-expression "cron(0 0 * * ? *)" \
  --region ap-northeast-2

aws events put-targets \
  --rule daily-report-trigger \
  --targets "Id"="1","Arn"="arn:aws:lambda:ap-northeast-2:123456789012:function:daily-report"

aws lambda add-permission \
  --function-name daily-report \
  --statement-id eventbridge-trigger \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:ap-northeast-2:123456789012:rule/daily-report-trigger
```

---

## 가격/한도

### 가격 모델

Lambda는 두 가지 차원으로 청구됩니다.

| 항목 | 가격 (us-east-1, x86) |
|------|----------------------|
| 요청 수 | 100만 건당 $0.20 |
| 컴퓨트 시간 | GB-초당 $0.0000166667 |
| Provisioned Concurrency 요청 | 100만 건당 $0.20 |
| Provisioned Concurrency 컴퓨트 | GB-초당 $0.0000041667 |
| Graviton (arm64) | x86 대비 약 20% 저렴 |

**계산 예시**: 512MB 메모리, 평균 200ms 실행, 월 1000만 호출
- 컴퓨트: 10,000,000 * 0.2 * 0.5 = 1,000,000 GB-초 -> $16.67
- 요청: 10 * $0.20 = $2.00
- 합계: 약 $18.67/월

### 프리 티어

매월 1,000,000건의 무료 요청과 400,000 GB-초의 컴퓨트 시간이 영구적으로 제공됩니다(만료 없음).

### 주요 한도

| 항목 | 기본 한도 | 조정 가능 |
|------|-----------|-----------|
| 메모리 | 128MB - 10240MB (1MB 단위) | 고정 |
| 타임아웃 | 1초 - 900초 (15분) | 고정 |
| 함수 패키지 (ZIP, 압축) | 50MB | 고정 |
| 함수 패키지 (ZIP, 압축 해제) | 250MB | 고정 |
| Container Image | 10GB | 고정 |
| 환경 변수 합계 | 4KB | 고정 |
| `/tmp` 임시 스토리지 | 512MB - 10240MB | 고정 |
| 동시 실행 (Concurrent Executions) | 1000 (계정/리전) | 가능 |
| 페이로드 (Sync) | 6MB | 고정 |
| 페이로드 (Async) | 256KB | 고정 |

```bash
# 동시 실행 한도 조회 및 함수별 예약
aws service-quotas get-service-quota \
  --service-code lambda \
  --quota-code L-B99A9384 \
  --region ap-northeast-2

aws lambda put-function-concurrency \
  --function-name my-critical-function \
  --reserved-concurrent-executions 100 \
  --region ap-northeast-2
```

---

## Best Practice

### 권장 패턴

1. **핸들러 외부에서 초기화**: DB 연결, SDK 클라이언트는 핸들러 외부에서 한 번 생성하여 EE 재사용 시 비용을 절감합니다.
2. **환경별 별칭(Alias) 활용**: `dev`, `staging`, `prod` 별칭을 사용하여 카나리 배포(Routing Configuration)와 즉시 롤백을 구현합니다.
3. **구조화된 로깅**: JSON 로그를 사용하여 CloudWatch Logs Insights에서 효율적으로 쿼리할 수 있도록 합니다.
4. **AWS Lambda Powertools 사용**: 로깅, 트레이싱, 메트릭, 멱등성 등 공통 기능을 표준화된 라이브러리로 처리합니다.
5. **Idempotency 보장**: 비동기/스트림 트리거는 재시도 가능성이 있으므로 멱등성 키 기반 처리가 필요합니다.
6. **VPC 연결 최소화**: VPC 연결이 필요한 경우 ENI 재사용을 고려하고, NAT Gateway 비용에 주의합니다.

### 안티 패턴

1. **장시간 실행 워크로드**: 15분 이상 걸리는 배치는 Step Functions, ECS Task, EKS Job으로 전환합니다.
2. **무거운 동기 호출 체인**: Lambda -> Lambda 동기 호출은 비용이 두 배가 되고 타임아웃 누적이 발생합니다. SQS 또는 Step Functions를 사용하세요.
3. **상태 저장 워크로드**: Lambda는 본질적으로 stateless이므로 세션은 DynamoDB, ElastiCache, S3에 저장합니다.
4. **거대한 패키지**: 250MB 한도 근처의 ZIP은 콜드 스타트가 매우 느립니다. Container Image 또는 Layer로 분리하세요.
5. **Provisioned Concurrency 남용**: 트래픽이 매우 적은 함수에 PC를 설정하면 비용 효율이 급락합니다.

```python
# 안티 패턴: 핸들러 내부에서 매번 클라이언트 생성
def handler(event, context):
    client = boto3.client("dynamodb")  # 매번 생성 -> 느림
    return client.get_item(...)

# 권장 패턴: 핸들러 외부에서 1회 생성
import boto3
client = boto3.client("dynamodb")  # EE당 1회

def handler(event, context):
    return client.get_item(...)
```

---

## 관련 서비스

| 서비스 | 관계 |
|--------|------|
| API Gateway | HTTP/REST API 진입점, Lambda 통합 |
| EventBridge | 이벤트 라우팅 및 스케줄 트리거 |
| SQS | 비동기 메시지 큐, Lambda Event Source Mapping |
| SNS | Pub/Sub, Lambda 비동기 트리거 |
| DynamoDB | NoSQL 상태 저장소, Streams 트리거 |
| S3 | 객체 스토리지, ObjectCreated 이벤트 트리거 |
| Step Functions | 장기 실행 워크플로우 오케스트레이션 |
| CloudFront + Lambda@Edge | 엣지 컴퓨팅 |
| ECR | Container Image 저장소 |
| X-Ray | 분산 트레이싱 |
| CloudWatch Logs | 로그 수집 및 Insights 쿼리 |
| AWS SAM / CDK | IaC 기반 Lambda 배포 |

---

## 관련 문서

- [[aws-fargate-서버리스-컨테이너-실행-개요|AWS Fargate]] - 컨테이너 기반 서버리스 컴퓨트, 장시간 실행 워크로드 대안
- [[amazon-eks-elastic-kubernetes-service-개요|Amazon EKS]] - Kubernetes 기반 컨테이너 워크로드, Knative와 함께 서버리스 패턴 구현 가능
- [[amazon-rds|Amazon RDS]] - Lambda에서 자주 호출되는 관계형 DB, RDS Proxy 권장
- [[amazon-eventbridge-scheduler-개요-및-활용-가이드|EventBridge Scheduler]] - Lambda 스케줄 트리거의 차세대 방식
