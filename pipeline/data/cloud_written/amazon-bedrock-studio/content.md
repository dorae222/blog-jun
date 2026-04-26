<!-- infographic-hero -->
![Amazon Bedrock Studio 핵심 요약](figures/infographic.svg)

*Figure: Amazon Bedrock Studio 한 장 요약 인포그래픽*

## 개요

Amazon Bedrock Studio는 AWS Management Console 내에서 제공되는 웹 기반 시각적 개발 환경으로, 코딩 없이도 생성형 AI 애플리케이션을 구축, 테스트, 공유할 수 있게 합니다. 데이터 과학자, 비즈니스 분석가, 프로덕트 매니저 등 비개발자가 직접 FM을 실험하고 프로토타입을 만들 수 있다는 점에서 생성형 AI의 민주화를 지향하는 서비스입니다.

기존에 Bedrock의 기능을 활용하려면 SDK를 사용한 코딩이 필요했습니다. Bedrock Studio는 이 장벽을 제거하여 다음과 같은 가치를 제공합니다.

- **노코드 AI 개발**: 시각적 인터페이스로 프롬프트 테스트, Knowledge Base 연동, Agent 구성을 수행합니다.
- **빠른 프로토타이핑**: 아이디어를 즉시 프로토타입으로 만들어 검증할 수 있습니다.
- **팀 협업**: 프로젝트를 팀원과 공유하고 함께 개선할 수 있습니다.
- **안전한 실험**: IAM Identity Center 기반 인증으로 기업의 보안 정책을 준수하면서 실험할 수 있습니다.

---

## 핵심 기능

### 1. 프로젝트 (Project) 관리

Bedrock Studio에서 모든 작업은 프로젝트 단위로 관리됩니다. 프로젝트 안에서 다양한 AI 앱을 생성하고 관리합니다.

```bash
# Bedrock Studio가 사용할 IAM Identity Center 설정 확인
aws sso-admin list-instances \
  --region us-east-1

# Bedrock Studio에 할당된 사용자 확인
aws sso-admin list-account-assignments \
  --instance-arn "arn:aws:sso:::instance/ssoins-abc123" \
  --account-id "123456789012" \
  --permission-set-arn "arn:aws:sso:::permissionSet/ssoins-abc123/ps-xyz789" \
  --region us-east-1
```

### 2. 플레이그라운드 (Playground)

Bedrock Studio의 플레이그라운드에서는 다양한 FM을 즉시 테스트할 수 있습니다. 모델별 성능 비교, 프롬프트 엔지니어링 실험, 파라미터 튜닝을 시각적으로 수행합니다.

지원하는 플레이그라운드 유형은 다음과 같습니다.

- **Chat Playground**: 대화형 인터페이스에서 FM과 상호작용합니다.
- **Text Playground**: 단일 프롬프트-응답 방식으로 텍스트 생성을 테스트합니다.
- **Image Playground**: 이미지 생성 모델을 실험합니다.

```bash
# 사용 가능한 모델 목록 확인 (Studio에서 표시할 모델)
aws bedrock list-foundation-models \
  --by-inference-type ON_DEMAND \
  --query 'modelSummaries[?contains(outputModalities, `TEXT`)].{ModelId:modelId, Provider:providerName, Name:modelName}' \
  --output table \
  --region us-east-1

# 모델 접근 권한 상태 확인
aws bedrock list-foundation-model-agreement-offers \
  --model-id "anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --region us-east-1
```

### 3. 앱 빌더 (App Builder)

App Builder는 Bedrock Studio의 핵심 기능으로, 시각적 인터페이스를 통해 생성형 AI 앱을 구성합니다.

**앱 유형**:

- **Chat App**: FM과의 대화형 인터페이스
- **Knowledge Base App**: RAG 기반 질의응답
- **Agent App**: Action Groups와 Knowledge Bases를 조합한 자율형 에이전트

각 앱에서 설정할 수 있는 주요 항목은 다음과 같습니다.

- 사용할 FM 선택
- 시스템 프롬프트 작성
- 추론 파라미터 (Temperature, Top P, Max Tokens)
- Knowledge Base 연결
- Guardrail 적용
- Action Group 정의

### 4. 프롬프트 관리 (Prompt Management)

프롬프트 템플릿을 생성하고 버전 관리하며, 변수를 활용하여 재사용 가능한 프롬프트를 설계합니다.

```bash
# 프롬프트 생성 (Bedrock Prompt Management API)
aws bedrock create-prompt \
  --name "customer-email-template" \
  --description "고객 이메일 응답 생성 프롬프트" \
  --default-variant "v1" \
  --variants '[{
    "name": "v1",
    "templateType": "TEXT",
    "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "templateConfiguration": {
      "text": {
        "text": "당신은 {{company_name}}의 고객 서비스 담당자입니다.\n고객 이름: {{customer_name}}\n문의 내용: {{inquiry}}\n위 문의에 대해 전문적이고 친절한 답변을 작성해 주십시오.",
        "inputVariables": [
          {"name": "company_name"},
          {"name": "customer_name"},
          {"name": "inquiry"}
        ]
      }
    },
    "inferenceConfiguration": {
      "text": {
        "temperature": 0.7,
        "maxTokens": 1024
      }
    }
  }]' \
  --region us-east-1

# 프롬프트 버전 생성
aws bedrock create-prompt-version \
  --prompt-identifier "prompt-abc123" \
  --description "v1.0 - 초기 프로덕션 버전" \
  --region us-east-1
```

### 5. 프롬프트 흐름 (Prompt Flows)

Prompt Flows는 여러 단계의 프롬프트를 시각적으로 연결하여 복잡한 AI 워크플로를 구성하는 기능입니다.

```bash
# Prompt Flow 생성
aws bedrock-agent create-flow \
  --name "document-analysis-flow" \
  --description "문서 분석 및 요약 파이프라인" \
  --execution-role-arn "arn:aws:iam::123456789012:role/BedrockFlowRole" \
  --definition '{
    "nodes": [
      {
        "name": "input",
        "type": "Input",
        "outputs": [{"name": "document", "type": "String"}]
      },
      {
        "name": "extract_key_points",
        "type": "Prompt",
        "configuration": {
          "prompt": {
            "sourceConfiguration": {
              "inline": {
                "modelId": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                "templateType": "TEXT",
                "templateConfiguration": {
                  "text": {
                    "text": "다음 문서에서 핵심 요점 5가지를 추출해 주십시오:\n{{document}}"
                  }
                },
                "inferenceConfiguration": {
                  "text": {"temperature": 0.3, "maxTokens": 1024}
                }
              }
            }
          }
        },
        "inputs": [{"name": "document", "type": "String", "expression": "$.data"}],
        "outputs": [{"name": "modelCompletion", "type": "String"}]
      },
      {
        "name": "generate_summary",
        "type": "Prompt",
        "configuration": {
          "prompt": {
            "sourceConfiguration": {
              "inline": {
                "modelId": "anthropic.claude-3-haiku-20240307-v1:0",
                "templateType": "TEXT",
                "templateConfiguration": {
                  "text": {
                    "text": "다음 핵심 요점을 바탕으로 3문장 이내의 요약문을 작성해 주십시오:\n{{key_points}}"
                  }
                },
                "inferenceConfiguration": {
                  "text": {"temperature": 0.5, "maxTokens": 512}
                }
              }
            }
          }
        },
        "inputs": [{"name": "key_points", "type": "String", "expression": "$.data"}],
        "outputs": [{"name": "modelCompletion", "type": "String"}]
      },
      {
        "name": "output",
        "type": "Output",
        "inputs": [{"name": "summary", "type": "String", "expression": "$.data"}]
      }
    ],
    "connections": [
      {"name": "conn1", "source": "input", "target": "extract_key_points", "type": "Data", "configuration": {"data": {"sourceOutput": "document", "targetInput": "document"}}},
      {"name": "conn2", "source": "extract_key_points", "target": "generate_summary", "type": "Data", "configuration": {"data": {"sourceOutput": "modelCompletion", "targetInput": "key_points"}}},
      {"name": "conn3", "source": "generate_summary", "target": "output", "type": "Data", "configuration": {"data": {"sourceOutput": "modelCompletion", "targetInput": "summary"}}}
    ]
  }' \
  --region us-east-1
```

---

## 아키텍처/동작 원리

### Bedrock Studio 아키텍처

```
[사용자 (브라우저)]
    |
    v
[IAM Identity Center 인증]
    |
    v
[Amazon Bedrock Studio (웹 UI)]
    |
    +---> [프로젝트 관리] --- S3 (설정/프롬프트 저장)
    +---> [플레이그라운드] --- Bedrock Runtime API
    +---> [App Builder]
    |       +---> [Knowledge Bases] --- OpenSearch Serverless / Aurora
    |       +---> [Agents] --- Lambda Functions
    |       +---> [Guardrails]
    +---> [Prompt Flows] --- Bedrock Agent Runtime
    +---> [Prompt Management] --- Bedrock API
```

### IAM Identity Center 기반 접근 제어

Bedrock Studio는 IAM Identity Center(구 AWS SSO)를 통해 사용자 인증과 권한 관리를 수행합니다. 이를 통해 조직 내 사용자에게 적절한 수준의 접근 권한을 부여할 수 있습니다.

```bash
# IAM Identity Center 사용자에게 Bedrock Studio 접근 권한 부여
aws sso-admin create-account-assignment \
  --instance-arn "arn:aws:sso:::instance/ssoins-abc123" \
  --target-id "123456789012" \
  --target-type AWS_ACCOUNT \
  --permission-set-arn "arn:aws:sso:::permissionSet/ssoins-abc123/ps-bedrock" \
  --principal-type USER \
  --principal-id "user-id-abc123" \
  --region us-east-1
```

### Prompt Flows 실행 원리

Prompt Flows는 DAG(Directed Acyclic Graph) 형태로 노드를 연결하여 복잡한 AI 파이프라인을 구성합니다.

```
[Input Node] ---> [Prompt Node A] ---> [Condition Node]
                                            |
                                  [True]----+----[False]
                                    |                |
                                    v                v
                            [Prompt Node B]  [Prompt Node C]
                                    |                |
                                    +----> [Collector Node]
                                                |
                                                v
                                         [Output Node]
```

지원하는 노드 유형은 다음과 같습니다.

- **Input/Output Node**: 흐름의 시작과 끝을 정의합니다.
- **Prompt Node**: FM을 호출하여 텍스트를 생성합니다.
- **Knowledge Base Node**: Knowledge Base에서 정보를 검색합니다.
- **Condition Node**: 조건에 따라 분기합니다.
- **Lambda Node**: Lambda 함수를 실행합니다.
- **Collector Node**: 여러 분기의 결과를 수집합니다.
- **S3 Storage Node**: S3에서 데이터를 읽거나 씁니다.

---

## 실전 활용

### 사례 1: 비개발자를 위한 AI 프로토타이핑 워크숍

비즈니스 팀이 Bedrock Studio를 활용하여 AI 프로토타입을 만드는 과정을 설명합니다.

**Step 1**: IAM Identity Center에서 워크숍 참가자 계정을 생성합니다.

```bash
# 워크숍 참가자 그룹 생성
aws identitystore create-group \
  --identity-store-id d-abc1234567 \
  --display-name "AI-Workshop-Participants" \
  --description "Bedrock Studio 워크숍 참가자 그룹" \
  --region us-east-1
```

**Step 2**: Bedrock Studio에서 프로젝트를 생성하고 팀원을 초대합니다.

**Step 3**: 플레이그라운드에서 다양한 모델을 비교 테스트합니다.

**Step 4**: App Builder로 비즈니스 요구사항에 맞는 AI 앱을 구성합니다.

### 사례 2: Prompt Flow를 활용한 문서 처리 파이프라인

```bash
# Prompt Flow 준비 (변경 사항 적용)
aws bedrock-agent prepare-flow \
  --flow-identifier "flow-abc123" \
  --region us-east-1

# Flow 별칭 생성
aws bedrock-agent create-flow-alias \
  --flow-identifier "flow-abc123" \
  --name "production" \
  --description "프로덕션 배포" \
  --routing-configuration '[{"flowVersion": "1"}]' \
  --region us-east-1

# Flow 실행
aws bedrock-agent-runtime invoke-flow \
  --flow-identifier "flow-abc123" \
  --flow-alias-identifier "alias-xyz789" \
  --inputs '[{
    "content": {"document": {"text": "분석할 문서 내용..."}},
    "nodeName": "input",
    "nodeOutputName": "document"
  }]' \
  --region us-east-1
```

---

## 모범 사례/보안

### 접근 제어 모범 사례

- IAM Identity Center를 통해 조직 내 사용자에게만 접근을 허용합니다.
- 프로젝트별로 접근 가능한 FM을 제한하여 비용을 통제합니다.
- 민감한 데이터를 다루는 프로젝트는 별도의 권한 그룹으로 관리합니다.
- Guardrails를 모든 앱에 기본 적용하여 안전한 실험 환경을 보장합니다.

### 비용 관리

Bedrock Studio 자체는 추가 비용이 없으며, 비용은 실제 사용하는 Bedrock 서비스(FM 호출, Knowledge Base, 벡터 DB 등)에 대해서만 발생합니다.

- 프로젝트별 예산 한도를 설정하여 비용 초과를 방지합니다.
- 프로토타이핑에는 비용이 낮은 모델(Haiku, Titan Express 등)을 사용합니다.
- CloudWatch 알람을 설정하여 비용 임계값 도달 시 알림을 받습니다.

```bash
# Bedrock 사용량 모니터링을 위한 CloudWatch 알람
aws cloudwatch put-metric-alarm \
  --alarm-name "bedrock-cost-alert" \
  --alarm-description "Bedrock 일일 사용량 경고" \
  --metric-name "InvocationCount" \
  --namespace "AWS/Bedrock" \
  --statistic Sum \
  --period 86400 \
  --threshold 10000 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1 \
  --alarm-actions "arn:aws:sns:us-east-1:123456789012:bedrock-alerts" \
  --region us-east-1
```

---

## 관련 서비스 비교

| 항목 | Bedrock Studio | Amazon SageMaker Canvas | Azure AI Studio | Google Vertex AI Studio |
|------|---------------|------------------------|-----------------|------------------------|
| 대상 사용자 | 비개발자 + 개발자 | 비개발자 (ML 전문가 아닌) | 개발자 + 비개발자 | 개발자 + 비개발자 |
| 주요 기능 | 생성형 AI 앱 빌더 | AutoML + 생성형 AI | 생성형 AI + ML 전체 | 생성형 AI + ML 전체 |
| 프롬프트 관리 | 내장 (Prompt Management) | 제한적 | Prompt Flow 내장 | Prompt Gallery |
| 워크플로 빌더 | Prompt Flows | 미지원 | Prompt Flow | Vertex AI Pipelines |
| 협업 | 프로젝트 공유 | 공유 제한적 | Azure DevOps 통합 | 프로젝트 공유 |
| 비용 | 사용한 서비스만 과금 | Canvas 시간당 과금 | 사용한 서비스만 과금 | 사용한 서비스만 과금 |
| 노코드 수준 | 높음 | 매우 높음 | 중간 | 중간 |

---

## 요약

Amazon Bedrock Studio는 생성형 AI 애플리케이션 개발의 진입 장벽을 크게 낮추는 시각적 개발 환경입니다. 주요 특징을 정리하면 다음과 같습니다.

- 코딩 없이 웹 브라우저에서 FM을 실험하고, Knowledge Bases와 Agents를 조합한 AI 앱을 구축할 수 있습니다.
- 플레이그라운드에서 다양한 모델을 비교하고, 프롬프트 엔지니어링을 시각적으로 수행합니다.
- App Builder를 통해 Chat App, Knowledge Base App, Agent App 등 다양한 유형의 AI 앱을 구성합니다.
- Prompt Flows로 여러 단계의 프롬프트를 DAG 형태로 연결하여 복잡한 AI 파이프라인을 구축합니다.
- Prompt Management를 통해 프롬프트 템플릿을 버전 관리하고 재사용합니다.
- IAM Identity Center 기반 인증으로 기업의 보안 정책을 준수하면서 팀 협업이 가능합니다.

Bedrock Studio는 특히 비개발자가 AI 프로토타입을 빠르게 만들어 아이디어를 검증하고, 개발팀에 넘겨 프로덕션으로 발전시키는 워크플로에 적합합니다.