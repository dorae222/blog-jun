<!-- infographic-hero -->
![Amazon Bedrock 핵심 요약](figures/infographic.svg)

*Figure: Amazon Bedrock 한 장 요약 인포그래픽*

## 개요

Amazon Bedrock은 AWS에서 제공하는 완전 관리형 생성형 AI 서비스로, 다양한 선도적 AI 기업의 파운데이션 모델(Foundation Model, FM)을 서버리스 API를 통해 사용할 수 있게 합니다. 인프라를 직접 관리하거나 모델을 배포할 필요 없이, API 호출만으로 텍스트 생성, 이미지 생성, 임베딩, 채팅 등의 생성형 AI 기능을 애플리케이션에 통합할 수 있습니다.

Bedrock이 제공하는 핵심 가치는 다음과 같습니다.

- **모델 선택의 자유**: Anthropic Claude, Meta Llama, Mistral, Cohere, Stability AI, Amazon Titan 등 다양한 FM을 단일 API로 접근합니다.
- **프라이빗 커스터마이징**: 자체 데이터로 모델을 미세 조정(Fine-tuning)하거나 사전 학습을 이어서 진행(Continued Pre-training)할 수 있으며, 데이터가 AWS 계정을 벗어나지 않습니다.
- **서버리스 운영**: 모델 인프라 관리가 불필요하며, 사용한 만큼만 과금됩니다.
- **엔터프라이즈 보안**: AWS PrivateLink, KMS 암호화, IAM 기반 접근 제어 등 엔터프라이즈급 보안을 제공합니다.

### Amazon Bedrock이 해결하는 문제

기존에 파운데이션 모델을 활용하려면 GPU 인스턴스 프로비저닝, 모델 가중치 다운로드, 서빙 인프라 구축, 스케일링 관리 등 복잡한 작업이 필요했습니다. Amazon Bedrock은 이러한 모든 운영 부담을 제거하고, 개발자가 애플리케이션 로직에만 집중할 수 있게 합니다.

---

## 핵심 기능

### 1. 다양한 파운데이션 모델 접근

Amazon Bedrock에서 제공하는 주요 모델 공급자와 모델은 다음과 같습니다.

| 공급자 | 주요 모델 | 특화 영역 |
|--------|----------|----------|
| Anthropic | Claude 3.5 Sonnet, Claude 3 Opus/Haiku | 대화, 분석, 코딩 |
| Meta | Llama 3.1 (8B/70B/405B) | 범용 텍스트 생성 |
| Mistral | Mistral Large, Mixtral 8x7B | 다국어, 코딩 |
| Cohere | Command R/R+, Embed | 검색, RAG |
| Stability AI | Stable Diffusion XL | 이미지 생성 |
| Amazon | Titan Text, Titan Embeddings, Titan Image | 범용 (AWS 자체 모델) |

```bash
# 사용 가능한 파운데이션 모델 목록 조회
aws bedrock list-foundation-models \
  --region us-east-1 \
  --query 'modelSummaries[*].[modelId,modelName,providerName]' \
  --output table

# 특정 모델 상세 정보 조회
aws bedrock get-foundation-model \
  --model-identifier anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --region us-east-1
```

### 2. 모델 호출 (Invoke Model)

```bash
# Claude 3.5 Sonnet 모델 호출 (Messages API)
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --content-type application/json \
  --accept application/json \
  --body '{
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1024,
    "messages": [
      {
        "role": "user",
        "content": "Amazon Bedrock의 주요 장점 3가지를 설명해 주십시오."
      }
    ]
  }' \
  --region us-east-1 \
  output.json
```

```python
import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# Claude 모델 호출
response = bedrock_runtime.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
    contentType='application/json',
    accept='application/json',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 2048,
        'temperature': 0.7,
        'messages': [
            {
                'role': 'user',
                'content': 'AWS의 서버리스 서비스를 종류별로 분류해 주십시오.'
            }
        ]
    })
)

result = json.loads(response['body'].read())
print(result['content'][0]['text'])
```

### 3. 스트리밍 응답

대화형 애플리케이션에서는 스트리밍 응답을 통해 사용자 경험을 크게 향상시킬 수 있습니다.

```python
import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

response = bedrock_runtime.invoke_model_with_response_stream(
    modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
    contentType='application/json',
    accept='application/json',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 2048,
        'messages': [
            {'role': 'user', 'content': 'Python으로 퀵소트를 구현해 주십시오.'}
        ]
    })
)

# 스트리밍 이벤트 처리
for event in response['body']:
    chunk = json.loads(event['chunk']['bytes'])
    if chunk['type'] == 'content_block_delta':
        print(chunk['delta'].get('text', ''), end='', flush=True)
```

### 4. 모델 커스터마이징

**Fine-tuning**: 특정 도메인 데이터로 모델의 성능을 개선합니다.

```bash
# Fine-tuning 작업 생성
aws bedrock create-model-customization-job \
  --job-name "my-custom-model-job" \
  --custom-model-name "my-domain-model" \
  --role-arn "arn:aws:iam::123456789012:role/BedrockCustomizationRole" \
  --base-model-identifier "amazon.titan-text-express-v1" \
  --customization-type "FINE_TUNING" \
  --training-data-config '{"s3Uri": "s3://my-training-data/train.jsonl"}' \
  --validation-data-config '{"validators": [{"s3Uri": "s3://my-training-data/validation.jsonl"}]}' \
  --output-data-config '{"s3Uri": "s3://my-model-output/"}' \
  --hyper-parameters '{"epochCount": "3", "batchSize": "8", "learningRate": "0.00001"}' \
  --region us-east-1

# Fine-tuning 작업 상태 확인
aws bedrock get-model-customization-job \
  --job-identifier "my-custom-model-job" \
  --region us-east-1
```

훈련 데이터 형식(JSONL)은 다음과 같습니다.

```json
{"prompt": "AWS Lambda의 최대 실행 시간은?", "completion": "AWS Lambda 함수의 최대 실행 시간(타임아웃)은 15분(900초)입니다."}
{"prompt": "S3 버킷의 최대 객체 크기는?", "completion": "Amazon S3에 저장할 수 있는 단일 객체의 최대 크기는 5TB입니다."}
```

### 5. Knowledge Bases (RAG)

Amazon Bedrock Knowledge Bases는 Retrieval-Augmented Generation(RAG) 패턴을 완전 관리형으로 제공합니다.

```bash
# Knowledge Base 생성
aws bedrock-agent create-knowledge-base \
  --name "company-docs-kb" \
  --description "사내 문서 기반 지식 베이스" \
  --role-arn "arn:aws:iam::123456789012:role/BedrockKBRole" \
  --knowledge-base-configuration '{
    "type": "VECTOR",
    "vectorKnowledgeBaseConfiguration": {
      "embeddingModelArn": "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
    }
  }' \
  --storage-configuration '{
    "type": "OPENSEARCH_SERVERLESS",
    "opensearchServerlessConfiguration": {
      "collectionArn": "arn:aws:aoss:us-east-1:123456789012:collection/abc123",
      "vectorIndexName": "company-docs-index",
      "fieldMapping": {
        "vectorField": "embedding",
        "textField": "text",
        "metadataField": "metadata"
      }
    }
  }' \
  --region us-east-1

# 데이터 소스 추가 (S3 버킷)
aws bedrock-agent create-data-source \
  --knowledge-base-id "KB12345678" \
  --name "s3-documents" \
  --data-source-configuration '{
    "type": "S3",
    "s3Configuration": {
      "bucketArn": "arn:aws:s3:::my-company-docs"
    }
  }' \
  --region us-east-1
```

### 6. Provisioned Throughput

일관된 성능이 필요한 프로덕션 워크로드를 위해 전용 처리량을 예약합니다.

```bash
# Provisioned Throughput 생성
aws bedrock create-provisioned-model-throughput \
  --model-units 1 \
  --provisioned-model-name "prod-claude-throughput" \
  --model-id "anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --commitment-duration "SixMonths" \
  --region us-east-1
```

---

## 아키텍처/동작 원리

### Bedrock의 내부 아키텍처

```
[클라이언트 애플리케이션]
        |
        v
[API Gateway / VPC Endpoint]
        |
        v
[Amazon Bedrock Control Plane]
  - 모델 관리
  - 접근 제어
  - 모니터링
        |
        v
[Amazon Bedrock Data Plane (Runtime)]
  - 모델 추론 엔진
  - 요청 라우팅
  - 토큰 계산/과금
        |
        +---> [FM Provider A: Anthropic Claude]
        +---> [FM Provider B: Meta Llama]
        +---> [FM Provider C: Amazon Titan]
        +---> [Custom Fine-tuned Models]
```

### RAG 아키텍처 (Knowledge Bases)

```
[데이터 수집 단계]
S3 문서 ---> [문서 파서] ---> [청킹] ---> [임베딩 모델] ---> [벡터 DB]
                                                              (OpenSearch Serverless
                                                               / Aurora PostgreSQL
                                                               / Pinecone / Redis)

[쿼리 단계]
사용자 질문 ---> [임베딩 모델] ---> [벡터 유사도 검색] ---> [관련 문서 검색]
                                                              |
                                                              v
                                                    [프롬프트 + 컨텍스트 구성]
                                                              |
                                                              v
                                                    [FM 모델 (Claude 등)]
                                                              |
                                                              v
                                                    [응답 생성 + 출처 표시]
```

### 요청 처리 흐름

1. 클라이언트가 Bedrock Runtime API에 요청을 보냅니다.
2. IAM 인증 및 권한 검증이 수행됩니다.
3. 요청이 해당 모델 제공자의 추론 엔진으로 라우팅됩니다.
4. 모델이 추론을 수행하고 결과를 반환합니다.
5. 입력/출력 토큰 수가 계산되어 과금됩니다.
6. CloudWatch에 메트릭과 로그가 기록됩니다.

---

## 실전 활용

### 사례 1: 멀티모달 분석 애플리케이션

Claude 3의 비전 기능을 활용하여 이미지를 분석하는 예시입니다.

```python
import boto3
import json
import base64

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# 이미지 파일을 base64로 인코딩
with open('architecture-diagram.png', 'rb') as f:
    image_data = base64.standard_b64encode(f.read()).decode('utf-8')

response = bedrock_runtime.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
    contentType='application/json',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 4096,
        'messages': [{
            'role': 'user',
            'content': [
                {
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': 'image/png',
                        'data': image_data
                    }
                },
                {
                    'type': 'text',
                    'text': '이 아키텍처 다이어그램을 분석하고 잠재적인 개선 사항을 제안해 주십시오.'
                }
            ]
        }]
    })
)

result = json.loads(response['body'].read())
print(result['content'][0]['text'])
```

### 사례 2: 배치 추론

대량의 데이터를 비용 효율적으로 처리할 때는 배치 추론을 활용합니다.

```bash
# 배치 추론 작업 생성
aws bedrock create-model-invocation-job \
  --job-name "batch-summarization-job" \
  --model-id "anthropic.claude-3-haiku-20240307-v1:0" \
  --role-arn "arn:aws:iam::123456789012:role/BedrockBatchRole" \
  --input-data-config '{
    "s3InputDataConfig": {
      "s3Uri": "s3://my-batch-input/requests.jsonl",
      "s3InputFormat": "JSONL"
    }
  }' \
  --output-data-config '{
    "s3OutputDataConfig": {
      "s3Uri": "s3://my-batch-output/"
    }
  }' \
  --region us-east-1
```

### 사례 3: Converse API 활용

Converse API는 모든 Bedrock 모델에 대해 통일된 인터페이스를 제공합니다.

```python
import boto3

client = boto3.client('bedrock-runtime', region_name='us-east-1')

# Converse API - 모델 간 통일된 인터페이스
response = client.converse(
    modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
    messages=[
        {
            'role': 'user',
            'content': [{'text': 'DynamoDB와 Aurora의 주요 차이점을 표로 정리해 주십시오.'}]
        }
    ],
    inferenceConfig={
        'maxTokens': 2048,
        'temperature': 0.5,
        'topP': 0.9
    },
    system=[{'text': '당신은 AWS 전문 기술 컨설턴트입니다. 정확하고 실용적인 정보를 제공합니다.'}]
)

print(response['output']['message']['content'][0]['text'])
print(f"입력 토큰: {response['usage']['inputTokens']}")
print(f"출력 토큰: {response['usage']['outputTokens']}")
```

---

## 모범 사례/보안

### 보안 아키텍처

```bash
# VPC 엔드포인트를 통한 프라이빗 접근
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --service-name com.amazonaws.us-east-1.bedrock-runtime \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-0123456789abcdef0 \
  --security-group-ids sg-0123456789abcdef0 \
  --private-dns-enabled
```

**모델 호출 로깅 설정**: 모든 모델 호출을 CloudWatch Logs 또는 S3에 기록하여 감사 추적을 유지합니다.

```bash
# 모델 호출 로깅 활성화
aws bedrock put-model-invocation-logging-configuration \
  --logging-config '{
    "cloudWatchConfig": {
      "logGroupName": "/aws/bedrock/model-invocations",
      "roleArn": "arn:aws:iam::123456789012:role/BedrockLoggingRole",
      "largeDataDeliveryS3Config": {
        "bucketName": "my-bedrock-logs",
        "keyPrefix": "large-data/"
      }
    },
    "textDataDeliveryEnabled": true,
    "imageDataDeliveryEnabled": false,
    "embeddingDataDeliveryEnabled": false
  }' \
  --region us-east-1
```

### IAM 정책 모범 사례

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSpecificModelInvocation",
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-*",
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-*"
      ]
    },
    {
      "Sid": "DenyExpensiveModels",
      "Effect": "Deny",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-opus-*"
    }
  ]
}
```

### 비용 최적화 전략

- 프로토타이핑에는 온디맨드 과금, 프로덕션에는 Provisioned Throughput을 사용합니다.
- 가벼운 태스크에는 Haiku와 같은 경량 모델을, 복잡한 태스크에만 Sonnet/Opus를 사용합니다.
- 대량 처리에는 Batch Inference를 활용하여 최대 50% 비용을 절감합니다.
- 캐싱 가능한 응답은 애플리케이션 레벨에서 캐싱하여 중복 호출을 줄입니다.
- CloudWatch 메트릭으로 모델별 사용량과 비용을 모니터링합니다.

---

## 관련 서비스 비교

| 항목 | Amazon Bedrock | Amazon SageMaker JumpStart | OpenAI API | Azure OpenAI Service |
|------|---------------|---------------------------|------------|---------------------|
| 서비스 유형 | 완전 관리형 FM API | 모델 허브 + 호스팅 | SaaS API | 관리형 FM API |
| 모델 다양성 | 다수 공급자 (Anthropic, Meta 등) | 오픈소스 모델 중심 | OpenAI 모델 전용 | OpenAI 모델 + 일부 오픈소스 |
| 인프라 관리 | 불필요 (서버리스) | 엔드포인트 관리 필요 | 불필요 | 불필요 |
| 커스터마이징 | Fine-tuning, Continued Pre-training | 전체 학습 파이프라인 | Fine-tuning | Fine-tuning |
| RAG 내장 | Knowledge Bases | 직접 구현 필요 | Assistants API | Azure AI Search 연동 |
| 데이터 보안 | VPC, KMS, IAM | VPC, KMS, IAM | API 키 기반 | Azure AD, VNet |
| 적합한 시나리오 | 다양한 모델 비교/선택, AWS 생태계 통합 | 오픈소스 모델 커스텀 학습 | 빠른 프로토타이핑 | Azure 생태계 통합 |

---

## 요약

Amazon Bedrock은 AWS 생태계에서 생성형 AI 애플리케이션을 구축하기 위한 핵심 서비스입니다. 주요 특징을 정리하면 다음과 같습니다.

- 다양한 FM 공급자(Anthropic, Meta, Mistral, Amazon 등)의 모델을 서버리스 API로 제공하여, 인프라 관리 부담 없이 즉시 활용할 수 있습니다.
- Knowledge Bases를 통한 완전 관리형 RAG, Guardrails를 통한 안전한 AI 응답, Agents를 통한 자율적 태스크 수행 등 포괄적인 생성형 AI 빌딩 블록을 제공합니다.
- Fine-tuning과 Continued Pre-training으로 모델을 프라이빗하게 커스터마이징할 수 있으며, 데이터가 AWS 계정 경계를 벗어나지 않습니다.
- Converse API를 통해 모델 간 통일된 인터페이스를 제공하여, 모델 전환 시 코드 변경을 최소화합니다.
- VPC 엔드포인트, KMS 암호화, IAM 세분화 정책, 모델 호출 로깅 등 엔터프라이즈급 보안 및 거버넌스를 지원합니다.

Amazon Bedrock은 생성형 AI를 프로덕션에 도입하려는 조직에게 보안성, 확장성, 운영 편의성을 모두 갖춘 기반 플랫폼으로서 최적의 선택입니다.