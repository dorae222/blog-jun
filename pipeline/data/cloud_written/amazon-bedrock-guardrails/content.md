## 개요

Amazon Bedrock Guardrails는 생성형 AI 애플리케이션의 입력과 출력에 안전장치(Safeguard)를 적용할 수 있는 완전 관리형 서비스입니다. 파운데이션 모델(FM)이 부적절하거나 유해한 콘텐츠를 생성하는 것을 방지하고, 기업의 정책과 규정을 준수하도록 보장합니다.

생성형 AI가 실제 비즈니스에 배포될 때, 모델의 출력을 제어하지 않으면 다음과 같은 위험이 발생할 수 있습니다.

- 유해하거나 부적절한 콘텐츠 생성
- 개인식별정보(PII)의 노출
- 비즈니스와 무관한 주제에 대한 응답
- 사실과 다른 정보 생성(할루시네이션)
- 기업 정책에 위배되는 응답

Bedrock Guardrails는 이러한 위험을 체계적으로 관리할 수 있는 정책 기반 프레임워크를 제공합니다. 중요한 점은 Guardrails가 특정 Bedrock 모델에 종속되지 않으며, 모든 FM과 심지어 자체 호스팅 모델에도 적용할 수 있다는 것입니다.

---

## 핵심 기능

### 1. 콘텐츠 필터 (Content Filters)

유해 콘텐츠 카테고리별로 필터 강도를 설정합니다. 입력(프롬프트)과 출력(응답) 모두에 적용됩니다.

지원하는 유해 콘텐츠 카테고리는 다음과 같습니다.

- **Hate**: 혐오 발언 및 차별적 콘텐츠
- **Insults**: 모욕적 콘텐츠
- **Sexual**: 성적 콘텐츠
- **Violence**: 폭력적 콘텐츠
- **Misconduct**: 범죄 또는 비윤리적 행위 조장
- **Prompt Attack**: 프롬프트 인젝션/탈옥 시도

각 카테고리에 대해 NONE, LOW, MEDIUM, HIGH 강도를 설정할 수 있습니다.

```bash
# Guardrail 생성 (콘텐츠 필터 설정)
aws bedrock create-guardrail \
  --name "enterprise-safety-guardrail" \
  --description "엔터프라이즈 안전 가드레일" \
  --content-policy-config '{
    "filtersConfig": [
      {"type": "HATE", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "INSULTS", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "SEXUAL", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "VIOLENCE", "inputStrength": "MEDIUM", "outputStrength": "HIGH"},
      {"type": "MISCONDUCT", "inputStrength": "HIGH", "outputStrength": "HIGH"},
      {"type": "PROMPT_ATTACK", "inputStrength": "HIGH", "outputStrength": "NONE"}
    ]
  }' \
  --blocked-input-messaging "입력이 안전 정책에 의해 차단되었습니다. 다른 방식으로 질문해 주십시오." \
  --blocked-output-messaging "요청하신 내용에 대한 응답을 생성할 수 없습니다. 다른 질문을 해 주십시오." \
  --region us-east-1
```

### 2. 거부 주제 (Denied Topics)

특정 주제에 대한 응답을 명시적으로 차단합니다. 비즈니스와 무관한 주제나 민감한 주제를 사전에 정의하여 에이전트가 해당 영역으로 벗어나지 않도록 합니다.

```bash
# 거부 주제가 포함된 Guardrail 생성
aws bedrock create-guardrail \
  --name "financial-advisor-guardrail" \
  --description "금융 자문 서비스용 가드레일" \
  --topic-policy-config '{
    "topicsConfig": [
      {
        "name": "investment-advice",
        "definition": "특정 주식, 채권, 암호화폐 등에 대한 투자 권유 또는 매수/매도 추천",
        "examples": [
          "삼성전자 주식을 지금 사야 할까요?",
          "비트코인에 투자하는 것이 좋을까요?",
          "어떤 ETF를 추천하시나요?"
        ],
        "type": "DENY"
      },
      {
        "name": "competitor-discussion",
        "definition": "경쟁사 서비스에 대한 추천이나 비교 분석",
        "examples": [
          "Azure와 AWS 중 어디가 더 좋나요?",
          "GCP로 마이그레이션하는 것이 나을까요?"
        ],
        "type": "DENY"
      },
      {
        "name": "political-opinions",
        "definition": "정치적 의견이나 특정 정당/정치인에 대한 평가",
        "examples": [
          "현 정부의 경제 정책에 대해 어떻게 생각하시나요?",
          "어떤 정당을 지지해야 할까요?"
        ],
        "type": "DENY"
      }
    ]
  }' \
  --blocked-input-messaging "해당 주제에 대해서는 답변을 드리기 어렵습니다." \
  --blocked-output-messaging "해당 주제에 대해서는 답변을 드리기 어렵습니다." \
  --region us-east-1
```

### 3. 단어 필터 (Word Filters)

특정 단어나 구문을 직접 차단합니다. 기업 고유의 금칙어, 경쟁사 이름, 비속어 등을 필터링할 수 있습니다.

```bash
# 단어 필터 설정 포함
aws bedrock create-guardrail \
  --name "brand-protection-guardrail" \
  --description "브랜드 보호용 가드레일" \
  --word-policy-config '{
    "wordsConfig": [
      {"text": "경쟁사A"},
      {"text": "경쟁사B"},
      {"text": "비속어1"}
    ],
    "managedWordListsConfig": [
      {"type": "PROFANITY"}
    ]
  }' \
  --blocked-input-messaging "부적절한 표현이 포함되어 있습니다." \
  --blocked-output-messaging "응답에 부적절한 내용이 포함되어 차단되었습니다." \
  --region us-east-1
```

### 4. 민감 정보 필터 (Sensitive Information Filters)

개인식별정보(PII)를 감지하여 차단하거나 마스킹합니다.

```bash
# PII 필터 설정이 포함된 Guardrail
aws bedrock create-guardrail \
  --name "pii-protection-guardrail" \
  --description "개인정보 보호 가드레일" \
  --sensitive-information-policy-config '{
    "piiEntitiesConfig": [
      {"type": "EMAIL", "action": "ANONYMIZE"},
      {"type": "PHONE", "action": "ANONYMIZE"},
      {"type": "NAME", "action": "ANONYMIZE"},
      {"type": "SSN", "action": "BLOCK"},
      {"type": "CREDIT_DEBIT_CARD_NUMBER", "action": "BLOCK"},
      {"type": "US_BANK_ACCOUNT_NUMBER", "action": "BLOCK"},
      {"type": "IP_ADDRESS", "action": "ANONYMIZE"}
    ],
    "regexesConfig": [
      {
        "name": "korean-resident-number",
        "description": "한국 주민등록번호 패턴",
        "pattern": "[0-9]{6}-[0-9]{7}",
        "action": "BLOCK"
      },
      {
        "name": "internal-account-id",
        "description": "내부 계정 ID 패턴",
        "pattern": "ACC-[A-Z0-9]{10}",
        "action": "ANONYMIZE"
      }
    ]
  }' \
  --blocked-input-messaging "민감한 개인정보가 포함되어 있어 처리할 수 없습니다." \
  --blocked-output-messaging "응답에 민감한 정보가 포함되어 차단되었습니다." \
  --region us-east-1
```

### 5. 컨텍스트 근거 확인 (Contextual Grounding Check)

RAG 파이프라인에서 FM의 응답이 제공된 컨텍스트에 근거하는지 검증하여 할루시네이션을 방지합니다.

```bash
# 컨텍스트 근거 확인이 포함된 Guardrail
aws bedrock create-guardrail \
  --name "rag-grounding-guardrail" \
  --description "RAG 할루시네이션 방지 가드레일" \
  --contextual-grounding-policy-config '{
    "filtersConfig": [
      {
        "type": "GROUNDING",
        "threshold": 0.7
      },
      {
        "type": "RELEVANCE",
        "threshold": 0.7
      }
    ]
  }' \
  --blocked-input-messaging "질문을 처리할 수 없습니다." \
  --blocked-output-messaging "제공된 문서에서 해당 질문에 대한 충분한 정보를 찾을 수 없습니다. 다른 방식으로 질문해 주십시오." \
  --region us-east-1
```

### 6. Guardrail 버전 관리

```bash
# Guardrail 버전 생성 (프로덕션 배포용)
aws bedrock create-guardrail-version \
  --guardrail-identifier "guardrail-abc123" \
  --description "v1.0 - 초기 프로덕션 배포" \
  --region us-east-1

# Guardrail 버전 목록 조회
aws bedrock list-guardrails \
  --guardrail-identifier "guardrail-abc123" \
  --region us-east-1
```

---

## 아키텍처/동작 원리

### Guardrails 처리 파이프라인

```
[사용자 입력 (프롬프트)]
    |
    v
[입력 Guardrail 평가]
  +--- 콘텐츠 필터 (유해성 검사)
  +--- 거부 주제 검사
  +--- 단어 필터 검사
  +--- PII 검사 (차단/마스킹)
  +--- 프롬프트 공격 감지
    |
    |--- [차단됨] ---> 차단 메시지 반환
    |--- [통과] ---|
                   v
            [FM 모델 추론]
                   |
                   v
            [출력 Guardrail 평가]
              +--- 콘텐츠 필터
              +--- 거부 주제 검사
              +--- 단어 필터 검사
              +--- PII 검사
              +--- 컨텍스트 근거 확인 (RAG 사용 시)
                   |
                   |--- [차단됨] ---> 차단 메시지 반환
                   |--- [통과] ---|
                                  v
                           [최종 응답 반환]
```

### ApplyGuardrail API를 통한 독립 사용

Guardrails는 Bedrock 모델 호출 없이도 독립적으로 사용할 수 있습니다. 자체 호스팅 모델이나 서드파티 LLM의 입출력에도 적용할 수 있습니다.

```python
import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# ApplyGuardrail API로 독립적으로 텍스트 검증
response = bedrock_runtime.apply_guardrail(
    guardrailIdentifier='guardrail-abc123',
    guardrailVersion='1',
    source='OUTPUT',
    content=[
        {
            'text': {
                'text': '고객님의 이메일 주소는 user@example.com이고 전화번호는 010-1234-5678입니다.',
                'qualifiers': ['query']
            }
        }
    ]
)

print(f"Action: {response['action']}")
# GUARDRAIL_INTERVENED 또는 NONE

for output in response.get('outputs', []):
    print(f"처리된 텍스트: {output['text']}")
    # PII가 마스킹된 텍스트 출력

for assessment in response.get('assessments', []):
    if 'sensitiveInformationPolicy' in assessment:
        for pii in assessment['sensitiveInformationPolicy'].get('piiEntities', []):
            print(f"감지된 PII: {pii['type']} - Action: {pii['action']}")
```

### Converse API와의 통합

```python
import boto3

client = boto3.client('bedrock-runtime', region_name='us-east-1')

response = client.converse(
    modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
    messages=[
        {
            'role': 'user',
            'content': [{'text': '고객 데이터를 분석해 주십시오.'}]
        }
    ],
    guardrailConfig={
        'guardrailIdentifier': 'guardrail-abc123',
        'guardrailVersion': '1',
        'trace': 'enabled'
    }
)

# Guardrail trace 확인
if 'trace' in response:
    guardrail_trace = response['trace'].get('guardrail', {})
    print(f"입력 평가: {guardrail_trace.get('inputAssessment', {})}")
    print(f"출력 평가: {guardrail_trace.get('outputAssessments', [])}")
```

---

## 실전 활용

### 사례 1: 금융 서비스 챗봇의 다중 보호 계층

```python
import boto3
import json

def create_financial_guardrail():
    bedrock = boto3.client('bedrock', region_name='us-east-1')
    
    response = bedrock.create_guardrail(
        name='financial-service-guardrail',
        description='금융 서비스 챗봇용 종합 가드레일',
        topicPolicyConfig={
            'topicsConfig': [
                {
                    'name': 'specific-investment-advice',
                    'definition': '특정 금융 상품에 대한 매수/매도/투자 추천',
                    'examples': [
                        '삼성전자 주식을 사야 할까요?',
                        '비트코인 지금 매수 타이밍인가요?'
                    ],
                    'type': 'DENY'
                },
                {
                    'name': 'illegal-financial-activity',
                    'definition': '자금 세탁, 탈세, 내부자 거래 등 불법 금융 활동 관련 질문',
                    'examples': [
                        '세금을 피하는 방법을 알려주십시오',
                        '자금 출처를 숨기는 방법이 있나요?'
                    ],
                    'type': 'DENY'
                }
            ]
        },
        contentPolicyConfig={
            'filtersConfig': [
                {'type': 'HATE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'INSULTS', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'SEXUAL', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'VIOLENCE', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'MISCONDUCT', 'inputStrength': 'HIGH', 'outputStrength': 'HIGH'},
                {'type': 'PROMPT_ATTACK', 'inputStrength': 'HIGH', 'outputStrength': 'NONE'}
            ]
        },
        sensitiveInformationPolicyConfig={
            'piiEntitiesConfig': [
                {'type': 'CREDIT_DEBIT_CARD_NUMBER', 'action': 'BLOCK'},
                {'type': 'US_BANK_ACCOUNT_NUMBER', 'action': 'BLOCK'},
                {'type': 'SSN', 'action': 'BLOCK'},
                {'type': 'EMAIL', 'action': 'ANONYMIZE'},
                {'type': 'PHONE', 'action': 'ANONYMIZE'},
                {'type': 'NAME', 'action': 'ANONYMIZE'}
            ],
            'regexesConfig': [
                {
                    'name': 'korean-resident-number',
                    'description': '주민등록번호',
                    'pattern': '[0-9]{6}-[0-9]{7}',
                    'action': 'BLOCK'
                }
            ]
        },
        blockedInputMessaging='해당 요청은 서비스 정책에 의해 처리할 수 없습니다.',
        blockedOutputsMessaging='안전 정책에 따라 해당 응답을 제공할 수 없습니다.'
    )
    
    return response['guardrailId']
```

### 사례 2: Guardrail 평가 결과 모니터링

```bash
# CloudWatch 메트릭 조회 - Guardrail 개입 횟수
aws cloudwatch get-metric-statistics \
  --namespace "AWS/Bedrock" \
  --metric-name "GuardrailIntervention" \
  --dimensions Name=GuardrailId,Value=guardrail-abc123 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum \
  --region us-east-1
```

---

## 모범 사례/보안

### 설계 원칙

- **계층적 보호**: 콘텐츠 필터, 주제 차단, 단어 필터, PII 보호를 조합하여 다중 방어 계층을 구성합니다.
- **점진적 강화**: 처음에는 낮은 강도로 시작하여 로그를 분석한 후 점진적으로 강도를 높입니다.
- **테스트 주도 설정**: 다양한 경계 케이스를 포함한 테스트 셋을 구성하여 Guardrail의 정확도를 검증합니다.
- **버전 관리**: 프로덕션 변경 전 반드시 새 버전을 생성하여 롤백이 가능하도록 합니다.

### 비용 고려사항

Guardrails 비용은 평가된 텍스트 단위(Text Unit, 1000자)당 과금됩니다. 각 정책 구성 요소별로 별도 과금이 적용되므로, 필요한 정책만 활성화하여 비용을 최적화합니다.

- 콘텐츠 필터: 텍스트 단위당 과금
- 거부 주제: 텍스트 단위당 과금
- 민감 정보 필터: 텍스트 단위당 과금
- 컨텍스트 근거 확인: 텍스트 단위당 과금
- 단어 필터: 추가 비용 없음

---

## 관련 서비스 비교

| 항목 | Bedrock Guardrails | OpenAI Moderation API | Azure Content Safety | 자체 구현 |
|------|--------------------|-----------------------|---------------------|-----------|
| 콘텐츠 필터링 | 6개 카테고리, 강도 조절 | 고정 카테고리 | 4개 카테고리, 강도 조절 | 커스텀 |
| 주제 차단 | 커스텀 주제 정의 | 미지원 | 커스텀 블랙리스트 | 커스텀 |
| PII 보호 | 내장 (차단/마스킹) | 미지원 | 미지원 | 별도 구현 필요 |
| 할루시네이션 방지 | Contextual Grounding | 미지원 | Groundedness 감지 | 별도 구현 필요 |
| 프롬프트 공격 감지 | 내장 | 미지원 | Prompt Shield | 별도 구현 필요 |
| 독립 사용 | ApplyGuardrail API | 독립 사용 가능 | 독립 사용 가능 | 해당 없음 |
| AWS 통합 | 네이티브 | 미지원 | Azure 네이티브 | SDK 필요 |

---

## 요약

Amazon Bedrock Guardrails는 생성형 AI 애플리케이션에 체계적인 안전장치를 구현할 수 있는 완전 관리형 서비스입니다. 주요 특징을 정리하면 다음과 같습니다.

- 콘텐츠 필터(6개 유해 카테고리), 거부 주제, 단어 필터, PII 보호, 컨텍스트 근거 확인의 5가지 보호 메커니즘을 조합하여 다중 방어 계층을 구성합니다.
- 입력과 출력 모두에 안전 정책을 적용하여, 부적절한 프롬프트 차단과 유해한 응답 생성 방지를 동시에 수행합니다.
- ApplyGuardrail API를 통해 Bedrock FM뿐만 아니라 자체 호스팅 모델이나 서드파티 LLM에도 독립적으로 적용할 수 있습니다.
- PII 감지 시 BLOCK(완전 차단) 또는 ANONYMIZE(마스킹) 동작을 선택할 수 있으며, 정규식 기반 커스텀 패턴도 지원합니다.
- Contextual Grounding Check를 통해 RAG 파이프라인에서의 할루시네이션을 효과적으로 방지합니다.
- 버전 관리를 통해 프로덕션 환경에서 안전하게 정책을 변경하고 롤백할 수 있습니다.

Guardrails는 책임 있는 AI(Responsible AI)를 구현하기 위한 필수 구성 요소로, 생성형 AI를 프로덕션에 배포하는 모든 조직에서 활용해야 하는 서비스입니다.