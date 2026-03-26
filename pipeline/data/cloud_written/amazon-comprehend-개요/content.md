## 개요

Amazon Comprehend는 자연어 처리(Natural Language Processing, NLP)를 활용하여 텍스트에서 의미 있는 인사이트를 추출하는 완전 관리형 서비스입니다. ML 전문 지식 없이도 API 호출만으로 텍스트의 감정, 핵심 구문, 개체명(Entity), 언어, 주제 등을 분석할 수 있습니다.

비정형 텍스트 데이터는 기업이 보유한 데이터의 약 80%를 차지하지만, 이를 체계적으로 분석하고 활용하는 것은 쉽지 않습니다. Amazon Comprehend는 이러한 비정형 텍스트 데이터를 구조화된 인사이트로 변환하여 비즈니스 의사결정에 활용할 수 있게 합니다.

### Amazon Comprehend의 주요 사용 사례

- 고객 리뷰 및 피드백의 감정 분석
- 지원 티켓의 자동 분류 및 라우팅
- 의료 문서에서의 의학 용어 및 관계 추출 (Comprehend Medical)
- 법률 문서의 핵심 조항 추출
- 소셜 미디어 모니터링 및 브랜드 평판 분석
- 개인식별정보(PII) 탐지 및 마스킹

---

## 핵심 기능

### 1. 감정 분석 (Sentiment Analysis)

텍스트의 전체적인 감정 톤을 POSITIVE, NEGATIVE, NEUTRAL, MIXED 중 하나로 분류합니다.

```bash
# 단일 텍스트 감정 분석
aws comprehend detect-sentiment \
  --text "이 제품은 정말 훌륭합니다. 배송도 빠르고 품질도 기대 이상이었습니다." \
  --language-code ko \
  --region us-east-1
```

응답 예시는 다음과 같습니다.

```json
{
  "Sentiment": "POSITIVE",
  "SentimentScore": {
    "Positive": 0.9876,
    "Negative": 0.0012,
    "Neutral": 0.0089,
    "Mixed": 0.0023
  }
}
```

```python
import boto3
import json

comprehend = boto3.client('comprehend', region_name='us-east-1')

# 배치 감정 분석 (최대 25개 텍스트)
reviews = [
    "배송이 너무 느려서 실망했습니다.",
    "가격 대비 성능이 뛰어납니다. 재구매 의사가 있습니다.",
    "보통입니다. 특별히 좋지도 나쁘지도 않습니다.",
    "제품은 좋은데 포장이 엉망이었습니다."
]

response = comprehend.batch_detect_sentiment(
    TextList=reviews,
    LanguageCode='ko'
)

for i, result in enumerate(response['ResultList']):
    print(f"리뷰 {i+1}: {result['Sentiment']} "
          f"(긍정: {result['SentimentScore']['Positive']:.3f}, "
          f"부정: {result['SentimentScore']['Negative']:.3f})")
```

### 2. 개체명 인식 (Entity Recognition)

텍스트에서 사람, 장소, 조직, 날짜, 수량 등의 개체명을 식별합니다.

```bash
# 개체명 인식
aws comprehend detect-entities \
  --text "삼성전자는 2024년 1월 서울에서 Galaxy S24 시리즈를 공개했습니다. 가격은 1,199,000원부터 시작합니다." \
  --language-code ko \
  --region us-east-1
```

인식 가능한 개체 유형은 다음과 같습니다.

| 유형 | 설명 | 예시 |
|------|------|------|
| PERSON | 사람 이름 | 이재용, Jeff Bezos |
| ORGANIZATION | 조직/기업 | 삼성전자, AWS |
| LOCATION | 장소 | 서울, AWS Seoul Region |
| DATE | 날짜/시간 | 2024년 1월, 다음 주 월요일 |
| QUANTITY | 수량 | 1,000개, 50% |
| COMMERCIAL_ITEM | 상품 | Galaxy S24, iPhone 15 |
| EVENT | 이벤트 | re:Invent, CES 2024 |
| TITLE | 직함 | CEO, CTO |
| OTHER | 기타 | 분류되지 않는 개체 |

### 3. 핵심 구문 추출 (Key Phrase Extraction)

텍스트에서 가장 중요한 구문(명사구)을 추출합니다.

```bash
# 핵심 구문 추출
aws comprehend detect-key-phrases \
  --text "Amazon Comprehend는 자연어 처리를 활용한 완전 관리형 텍스트 분석 서비스입니다. 기계 학습 모델을 직접 학습시키지 않아도 텍스트에서 유용한 인사이트를 추출할 수 있습니다." \
  --language-code ko \
  --region us-east-1
```

### 4. 언어 감지 (Language Detection)

```bash
# 우세 언어 감지
aws comprehend detect-dominant-language \
  --text "This is a sample text for language detection." \
  --region us-east-1

# 배치 언어 감지
aws comprehend batch-detect-dominant-language \
  --text-list "Hello, how are you?" "Bonjour, comment allez-vous?" "안녕하세요, 잘 지내시나요?" "Hola, como estas?" \
  --region us-east-1
```

### 5. PII 탐지 및 마스킹

텍스트에서 개인식별정보를 탐지하고, 필요에 따라 마스킹(익명화)합니다.

```bash
# PII 엔티티 탐지
aws comprehend detect-pii-entities \
  --text "고객 김철수님의 전화번호는 010-1234-5678이며, 이메일은 chulsoo@example.com입니다." \
  --language-code ko \
  --region us-east-1

# PII 마스킹 (익명화)
aws comprehend contains-pii-entities \
  --text "고객 김철수님의 전화번호는 010-1234-5678이며, 이메일은 chulsoo@example.com입니다." \
  --language-code ko \
  --region us-east-1
```

```python
import boto3

comprehend = boto3.client('comprehend', region_name='us-east-1')

text = "고객 김철수님의 전화번호는 010-1234-5678이며, 이메일은 chulsoo@example.com입니다."

# PII 엔티티 위치 확인
response = comprehend.detect_pii_entities(
    Text=text,
    LanguageCode='ko'
)

# PII 마스킹 수행
masked_text = list(text)
for entity in sorted(response['Entities'], key=lambda x: x['BeginOffset'], reverse=True):
    start = entity['BeginOffset']
    end = entity['EndOffset']
    pii_type = entity['Type']
    masked_text[start:end] = list(f'[{pii_type}]')

print(''.join(masked_text))
# 출력: 고객 [NAME]님의 전화번호는 [PHONE]이며, 이메일은 [EMAIL]입니다.
```

### 6. 주제 모델링 (Topic Modeling)

대량의 문서에서 공통 주제를 발견하는 비지도 학습 기반 분석입니다.

```bash
# 주제 모델링 작업 시작
aws comprehend start-topics-detection-job \
  --input-data-config '{
    "S3Uri": "s3://my-comprehend-input/documents/",
    "InputFormat": "ONE_DOC_PER_LINE"
  }' \
  --output-data-config '{
    "S3Uri": "s3://my-comprehend-output/topics/"
  }' \
  --data-access-role-arn "arn:aws:iam::123456789012:role/ComprehendDataAccessRole" \
  --number-of-topics 10 \
  --job-name "customer-review-topics" \
  --language-code ko \
  --region us-east-1

# 작업 상태 확인
aws comprehend describe-topics-detection-job \
  --job-id "job-abc123" \
  --region us-east-1
```

### 7. 커스텀 분류기 (Custom Classifier)

비즈니스 도메인에 특화된 텍스트 분류 모델을 학습시킵니다.

```bash
# 커스텀 분류기 학습 시작
aws comprehend create-document-classifier \
  --document-classifier-name "support-ticket-classifier" \
  --data-access-role-arn "arn:aws:iam::123456789012:role/ComprehendDataAccessRole" \
  --input-data-config '{
    "S3Uri": "s3://my-training-data/support-tickets.csv",
    "DataFormat": "COMPREHEND_CSV"
  }' \
  --output-data-config '{
    "S3Uri": "s3://my-comprehend-output/classifiers/"
  }' \
  --language-code ko \
  --mode "MULTI_CLASS" \
  --region us-east-1

# 분류기 상태 확인
aws comprehend describe-document-classifier \
  --document-classifier-arn "arn:aws:comprehend:us-east-1:123456789012:document-classifier/support-ticket-classifier" \
  --region us-east-1
```

학습 데이터 형식(CSV)은 다음과 같습니다.

```
BILLING,"청구서 금액이 잘못되었습니다. 확인 부탁드립니다."
TECHNICAL,"로그인이 안 됩니다. 비밀번호를 재설정해도 같은 문제가 발생합니다."
SHIPPING,"주문한 지 일주일이 넘었는데 아직 배송이 시작되지 않았습니다."
RETURN,"제품에 하자가 있어서 반품하고 싶습니다."
```

### 8. 커스텀 개체 인식기 (Custom Entity Recognizer)

```bash
# 커스텀 엔티티 인식기 학습
aws comprehend create-entity-recognizer \
  --recognizer-name "product-entity-recognizer" \
  --data-access-role-arn "arn:aws:iam::123456789012:role/ComprehendDataAccessRole" \
  --input-data-config '{
    "EntityTypes": [
      {"Type": "PRODUCT_NAME"},
      {"Type": "PRODUCT_CODE"},
      {"Type": "DEFECT_TYPE"}
    ],
    "Documents": {"S3Uri": "s3://my-training-data/documents.txt"},
    "Annotations": {"S3Uri": "s3://my-training-data/annotations.csv"}
  }' \
  --language-code ko \
  --region us-east-1
```

---

## 아키텍처/동작 원리

### Comprehend 서비스 아키텍처

```
[클라이언트]
    |
    v
[Amazon Comprehend API]
    |
    +---> [실시간 분석 (Synchronous)]
    |       +--- Detect Sentiment
    |       +--- Detect Entities
    |       +--- Detect Key Phrases
    |       +--- Detect Language
    |       +--- Detect PII
    |       +--- Classify Document (Custom)
    |
    +---> [비동기 작업 (Asynchronous)]
    |       +--- Topic Modeling
    |       +--- 대용량 감정 분석
    |       +--- 대용량 개체 인식
    |       +--- Events Detection
    |
    +---> [커스텀 모델]
    |       +--- Custom Classifier 학습/추론
    |       +--- Custom Entity Recognizer 학습/추론
    |
    +---> [엔드포인트 (실시간 추론)]
            +--- Custom Classifier Endpoint
            +--- Custom Entity Recognizer Endpoint
```

### 동기식 vs 비동기식 처리

**동기식 API**: 단일 텍스트 또는 소규모 배치(최대 25개)를 실시간으로 처리합니다. 지연 시간이 짧아 실시간 애플리케이션에 적합합니다.

**비동기식 작업**: S3에 저장된 대용량 문서 컬렉션을 처리합니다. 주제 모델링, 대규모 감정 분석 등에 사용됩니다. 결과는 S3에 저장됩니다.

### 커스텀 모델 배포 아키텍처

```
[학습 데이터 (S3)] ---> [모델 학습 (비동기 작업)]
                              |
                              v
                     [학습된 모델 (S3 저장)]
                              |
                    +---------+---------+
                    |                   |
                    v                   v
        [실시간 엔드포인트]      [비동기 분석 작업]
        (항상 가동, 과금)       (온디맨드, 작업 단위 과금)
```

---

## 실전 활용

### 사례 1: 고객 리뷰 분석 파이프라인

```python
import boto3
import json
from collections import Counter

def analyze_reviews(reviews):
    """
    고객 리뷰를 종합적으로 분석합니다.
    """
    comprehend = boto3.client('comprehend', region_name='us-east-1')
    
    results = []
    
    # 배치 처리 (25개씩)
    for i in range(0, len(reviews), 25):
        batch = reviews[i:i+25]
        
        # 감정 분석
        sentiment_response = comprehend.batch_detect_sentiment(
            TextList=batch,
            LanguageCode='ko'
        )
        
        # 핵심 구문 추출
        keyphrase_response = comprehend.batch_detect_key_phrases(
            TextList=batch,
            LanguageCode='ko'
        )
        
        # 개체명 인식
        entity_response = comprehend.batch_detect_entities(
            TextList=batch,
            LanguageCode='ko'
        )
        
        for j, review in enumerate(batch):
            results.append({
                'text': review,
                'sentiment': sentiment_response['ResultList'][j]['Sentiment'],
                'sentiment_scores': sentiment_response['ResultList'][j]['SentimentScore'],
                'key_phrases': [
                    kp['Text'] for kp in keyphrase_response['ResultList'][j]['KeyPhrases']
                ],
                'entities': [
                    {'text': e['Text'], 'type': e['Type']}
                    for e in entity_response['ResultList'][j]['Entities']
                ]
            })
    
    # 집계 분석
    sentiment_dist = Counter(r['sentiment'] for r in results)
    all_phrases = [p for r in results for p in r['key_phrases']]
    top_phrases = Counter(all_phrases).most_common(10)
    
    return {
        'total_reviews': len(results),
        'sentiment_distribution': dict(sentiment_dist),
        'top_key_phrases': top_phrases,
        'detailed_results': results
    }
```

### 사례 2: 대용량 문서 비동기 분석

```bash
# 대용량 감정 분석 작업 시작
aws comprehend start-sentiment-detection-job \
  --input-data-config '{
    "S3Uri": "s3://my-comprehend-input/reviews/",
    "InputFormat": "ONE_DOC_PER_LINE"
  }' \
  --output-data-config '{
    "S3Uri": "s3://my-comprehend-output/sentiment-results/"
  }' \
  --data-access-role-arn "arn:aws:iam::123456789012:role/ComprehendDataAccessRole" \
  --language-code ko \
  --job-name "monthly-review-analysis" \
  --region us-east-1

# 작업 목록 조회
aws comprehend list-sentiment-detection-jobs \
  --filter '{"JobStatus": "IN_PROGRESS"}' \
  --region us-east-1
```

### 사례 3: 실시간 커스텀 분류 엔드포인트

```bash
# 커스텀 분류기 엔드포인트 생성
aws comprehend create-endpoint \
  --endpoint-name "ticket-classifier-endpoint" \
  --model-arn "arn:aws:comprehend:us-east-1:123456789012:document-classifier/support-ticket-classifier/version/v1" \
  --desired-inference-units 1 \
  --region us-east-1

# 실시간 분류 수행
aws comprehend classify-document \
  --endpoint-arn "arn:aws:comprehend:us-east-1:123456789012:document-classifier-endpoint/ticket-classifier-endpoint" \
  --text "결제가 이중으로 처리되었습니다. 확인 후 환불 부탁드립니다." \
  --region us-east-1
```

---

## 모범 사례/보안

### 보안 설정

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "comprehend:DetectSentiment",
        "comprehend:DetectEntities",
        "comprehend:DetectKeyPhrases",
        "comprehend:DetectDominantLanguage",
        "comprehend:DetectPiiEntities",
        "comprehend:BatchDetect*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "comprehend:ClassifyDocument"
      ],
      "Resource": "arn:aws:comprehend:us-east-1:123456789012:document-classifier-endpoint/*"
    }
  ]
}
```

### VPC 엔드포인트 설정

```bash
# Comprehend VPC 엔드포인트 생성
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --service-name com.amazonaws.us-east-1.comprehend \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-0123456789abcdef0 \
  --security-group-ids sg-0123456789abcdef0 \
  --private-dns-enabled \
  --region us-east-1
```

### 비용 최적화

- 실시간 분석이 필요 없는 대량 처리는 비동기 작업(Start*Job API)을 사용합니다.
- 커스텀 분류기 엔드포인트는 사용하지 않을 때 삭제하여 비용을 절감합니다.
- 배치 API(BatchDetect*)를 활용하여 API 호출 횟수를 줄입니다.
- Auto Scaling을 설정하여 엔드포인트의 추론 유닛을 트래픽에 맞게 조절합니다.

---

## 관련 서비스 비교

| 항목 | Amazon Comprehend | Amazon Bedrock (FM) | Google Cloud NLP | Azure Text Analytics |
|------|-------------------|--------------------|-----------------|-----------------------|
| 서비스 유형 | 전용 NLP API | 범용 FM API | 전용 NLP API | 전용 NLP API |
| 감정 분석 | 내장 | 프롬프트로 구현 | 내장 | 내장 |
| 개체명 인식 | 내장 + 커스텀 | 프롬프트로 구현 | 내장 + 커스텀 | 내장 + 커스텀 |
| 커스텀 분류 | AutoML 기반 학습 | Fine-tuning | AutoML 기반 학습 | 커스텀 학습 |
| 주제 모델링 | 내장 | 프롬프트로 구현 | 미지원 | 미지원 |
| PII 탐지 | 내장 | Guardrails 필요 | 내장 (DLP) | 내장 |
| 한국어 지원 | 대부분 기능 지원 | FM 의존 | 지원 | 지원 |
| 비용 모델 | 문자 단위 과금 | 토큰 단위 과금 | 문자 단위 과금 | 문자 단위 과금 |
| 적합한 시나리오 | 대량 텍스트 분석, 구조화된 NLP | 복잡한 텍스트 이해, 생성 | 대량 텍스트 분석 | 대량 텍스트 분석 |

Amazon Comprehend는 정형화된 NLP 태스크(감정 분석, 개체 인식 등)에 특화되어 있으며, 비용 효율적으로 대량 처리할 수 있습니다. 반면 Amazon Bedrock의 FM은 더 복잡한 텍스트 이해와 자유 형식의 분석에 적합합니다.

---

## 요약

Amazon Comprehend는 텍스트 데이터에서 구조화된 인사이트를 추출하는 완전 관리형 NLP 서비스입니다. 주요 특징을 정리하면 다음과 같습니다.

- 감정 분석, 개체명 인식, 핵심 구문 추출, 언어 감지, PII 탐지 등 사전 학습된 NLP 기능을 API 호출만으로 사용할 수 있습니다.
- 커스텀 분류기(Custom Classifier)와 커스텀 엔티티 인식기(Custom Entity Recognizer)를 통해 비즈니스 도메인에 특화된 모델을 학습시킬 수 있습니다.
- 동기식 API(실시간)와 비동기식 작업(대용량)을 모두 지원하여 다양한 규모의 워크로드에 대응합니다.
- 주제 모델링(Topic Modeling)으로 대량 문서에서 숨겨진 주제 패턴을 자동으로 발견합니다.
- Comprehend Medical을 통해 의료 텍스트 분석에 특화된 기능도 제공합니다.
- VPC 엔드포인트, IAM 정책, KMS 암호화를 통해 엔터프라이즈급 보안을 지원합니다.

Amazon Comprehend는 대량의 텍스트 데이터를 체계적으로 분석하여 비즈니스 인사이트를 도출하는 모든 워크로드에서 핵심적인 역할을 수행합니다.