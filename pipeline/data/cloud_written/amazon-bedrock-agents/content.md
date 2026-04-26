<!-- infographic-hero -->
![Amazon Bedrock Agents 핵심 요약](figures/infographic.svg)

*Figure: Amazon Bedrock Agents 한 장 요약 인포그래픽*

## 개요

Amazon Bedrock Agents는 파운데이션 모델(FM)이 외부 시스템과 상호작용하며 복잡한 태스크를 자율적으로 수행할 수 있도록 하는 완전 관리형 에이전트 프레임워크입니다. 단순한 텍스트 생성을 넘어, FM이 사용자의 요청을 이해하고, 필요한 정보를 검색하고, 외부 API를 호출하여 실제 작업을 완료하는 지능형 AI 에이전트를 구축할 수 있습니다.

기존의 LLM 기반 애플리케이션은 모델이 학습된 지식 범위 내에서만 응답할 수 있다는 한계가 있었습니다. Bedrock Agents는 이 한계를 극복하여 다음과 같은 기능을 제공합니다.

- **Action Groups**: FM이 Lambda 함수나 외부 API를 호출하여 실제 작업을 수행합니다.
- **Knowledge Bases 연동**: RAG 패턴으로 최신 데이터를 검색하여 응답에 반영합니다.
- **다단계 추론**: ReAct(Reasoning + Acting) 방식으로 복잡한 문제를 단계적으로 해결합니다.
- **메모리 관리**: 대화 컨텍스트를 유지하여 연속적인 상호작용을 지원합니다.
- **Code Interpreter**: 코드를 직접 생성하고 실행하여 데이터 분석 등을 수행합니다.

---

## 핵심 기능

### 1. Agent 생성 및 구성

```bash
# Bedrock Agent 생성
aws bedrock-agent create-agent \
  --agent-name "customer-service-agent" \
  --description "고객 서비스 자동화 에이전트" \
  --foundation-model "anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --instruction "당신은 전자상거래 고객 서비스 에이전트입니다. 주문 조회, 반품 처리, 제품 추천 업무를 수행합니다. 항상 친절하고 정확한 정보를 제공하십시오. 고객의 개인정보는 안전하게 처리하십시오." \
  --agent-resource-role-arn "arn:aws:iam::123456789012:role/BedrockAgentRole" \
  --idle-session-ttl-in-seconds 1800 \
  --region us-east-1
```

### 2. Action Groups (액션 그룹)

Action Group은 에이전트가 수행할 수 있는 작업의 집합입니다. OpenAPI 스키마로 API를 정의하고, Lambda 함수로 실제 로직을 구현합니다.

**OpenAPI 스키마 정의**:

```yaml
# order-api-schema.yaml
openapi: 3.0.0
info:
  title: Order Management API
  version: 1.0.0
  description: 주문 관리 API
paths:
  /orders/{orderId}:
    get:
      summary: 주문 상세 조회
      description: 주문 ID로 주문 상세 정보를 조회합니다.
      operationId: getOrder
      parameters:
        - name: orderId
          in: path
          required: true
          schema:
            type: string
          description: 조회할 주문 ID
      responses:
        '200':
          description: 주문 상세 정보
          content:
            application/json:
              schema:
                type: object
                properties:
                  orderId:
                    type: string
                  status:
                    type: string
                  items:
                    type: array
                    items:
                      type: object
                      properties:
                        productName:
                          type: string
                        quantity:
                          type: integer
                        price:
                          type: number
  /orders/{orderId}/return:
    post:
      summary: 반품 요청
      description: 주문에 대한 반품을 요청합니다.
      operationId: requestReturn
      parameters:
        - name: orderId
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                reason:
                  type: string
                  description: 반품 사유
              required:
                - reason
      responses:
        '200':
          description: 반품 요청 결과
```

**Lambda 함수 구현**:

```python
import json
import boto3

def lambda_handler(event, context):
    """
    Bedrock Agent Action Group의 Lambda 핸들러입니다.
    """
    agent = event.get('agent', {})
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    http_method = event.get('httpMethod', '')
    parameters = event.get('parameters', [])
    request_body = event.get('requestBody', {})
    
    # 파라미터 추출
    params = {p['name']: p['value'] for p in parameters}
    
    if api_path == '/orders/{orderId}' and http_method == 'GET':
        order_id = params.get('orderId')
        result = get_order(order_id)
    elif api_path == '/orders/{orderId}/return' and http_method == 'POST':
        order_id = params.get('orderId')
        body = request_body.get('content', {}).get('application/json', {}).get('properties', {})
        reason = body.get('reason', {}).get('value', '')
        result = request_return(order_id, reason)
    else:
        result = {'error': '지원하지 않는 작업입니다.'}
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpMethod': http_method,
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(result, ensure_ascii=False)
                }
            }
        }
    }

def get_order(order_id):
    # 실제 주문 데이터 조회 로직
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Orders')
    response = table.get_item(Key={'orderId': order_id})
    return response.get('Item', {'error': '주문을 찾을 수 없습니다.'})

def request_return(order_id, reason):
    # 반품 처리 로직
    return {
        'returnId': f'RET-{order_id}',
        'status': 'PENDING',
        'message': f'반품 요청이 접수되었습니다. 사유: {reason}'
    }
```

```bash
# Action Group 생성
aws bedrock-agent create-agent-action-group \
  --agent-id "AGENT123456" \
  --agent-version "DRAFT" \
  --action-group-name "OrderManagement" \
  --description "주문 조회 및 반품 처리" \
  --action-group-executor '{"lambda": "arn:aws:lambda:us-east-1:123456789012:function:order-management"}' \
  --api-schema '{"s3": {"s3BucketName": "my-agent-schemas", "s3ObjectKey": "order-api-schema.yaml"}}' \
  --region us-east-1
```

### 3. Knowledge Base 연동

에이전트에 Knowledge Base를 연결하여 RAG 기능을 추가합니다.

```bash
# Agent에 Knowledge Base 연결
aws bedrock-agent associate-agent-knowledge-base \
  --agent-id "AGENT123456" \
  --agent-version "DRAFT" \
  --knowledge-base-id "KB12345678" \
  --description "제품 카탈로그 및 FAQ 문서" \
  --knowledge-base-state "ENABLED" \
  --region us-east-1
```

### 4. Agent 준비 및 별칭 생성

에이전트를 사용하려면 준비(Prepare) 단계를 거쳐야 합니다.

```bash
# Agent 준비 (변경 사항 적용)
aws bedrock-agent prepare-agent \
  --agent-id "AGENT123456" \
  --region us-east-1

# Agent 별칭 생성 (프로덕션 배포용)
aws bedrock-agent create-agent-alias \
  --agent-id "AGENT123456" \
  --agent-alias-name "production" \
  --description "프로덕션 배포 별칭" \
  --region us-east-1
```

### 5. Agent 호출

```python
import boto3
import json
import uuid

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

def invoke_agent(agent_id, agent_alias_id, user_input, session_id=None):
    if session_id is None:
        session_id = str(uuid.uuid4())
    
    response = bedrock_agent_runtime.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        sessionId=session_id,
        inputText=user_input,
        enableTrace=True
    )
    
    result_text = ''
    trace_info = []
    
    for event in response['completion']:
        if 'chunk' in event:
            chunk = event['chunk']
            result_text += chunk['bytes'].decode('utf-8')
        if 'trace' in event:
            trace_info.append(event['trace'])
    
    return {
        'response': result_text,
        'session_id': session_id,
        'traces': trace_info
    }

# 사용 예시
result = invoke_agent(
    agent_id='AGENT123456',
    agent_alias_id='ALIAS789',
    user_input='주문번호 ORD-2024-001의 배송 상태를 확인해 주십시오.'
)
print(result['response'])
```

### 6. Code Interpreter

Bedrock Agents의 Code Interpreter 기능은 에이전트가 Python 코드를 생성하고 실행하여 데이터 분석, 시각화, 수학 계산 등을 수행할 수 있게 합니다.

```bash
# Code Interpreter가 활성화된 Action Group 생성
aws bedrock-agent create-agent-action-group \
  --agent-id "AGENT123456" \
  --agent-version "DRAFT" \
  --action-group-name "CodeInterpreter" \
  --parent-action-group-signature "AMAZON.CodeInterpreter" \
  --action-group-state "ENABLED" \
  --region us-east-1
```

---

## 아키텍처/동작 원리

### ReAct (Reasoning + Acting) 루프

Bedrock Agents는 ReAct 패턴을 기반으로 동작합니다. FM이 사용자 요청을 분석하고, 필요한 행동을 결정하고, 결과를 관찰한 후, 다음 행동을 계획하는 과정을 반복합니다.

```
[사용자 입력]
    |
    v
[Pre-processing] --- 입력 검증 및 분류
    |
    v
[Orchestration Loop (ReAct)]
    |
    +---> [Thought] FM이 현재 상황을 분석하고 다음 행동을 계획
    |         |
    |         v
    +---> [Action] 선택된 Action Group의 API 호출 또는 KB 검색
    |         |
    |         v
    +---> [Observation] 행동 결과를 관찰
    |         |
    |         v
    +---> [반복 또는 최종 응답 결정]
    |
    v
[Post-processing] --- 응답 형식 지정 및 검증
    |
    v
[최종 응답 반환]
```

### 실행 추적 (Trace) 구조

에이전트의 의사결정 과정을 추적할 수 있습니다.

```json
{
  "trace": {
    "orchestrationTrace": {
      "rationale": {
        "text": "사용자가 주문 상태를 확인하려 합니다. OrderManagement API의 getOrder를 호출해야 합니다."
      },
      "invocationInput": {
        "actionGroupInvocationInput": {
          "actionGroupName": "OrderManagement",
          "apiPath": "/orders/{orderId}",
          "verb": "GET",
          "parameters": [
            {"name": "orderId", "value": "ORD-2024-001"}
          ]
        }
      },
      "observation": {
        "actionGroupInvocationOutput": {
          "text": "{\"orderId\": \"ORD-2024-001\", \"status\": \"SHIPPED\"}"
        }
      }
    }
  }
}
```

### 멀티 에이전트 협업 아키텍처

Bedrock Agents는 에이전트 간 협업도 지원합니다. 수퍼바이저 에이전트가 하위 에이전트에게 태스크를 위임하는 구조를 구성할 수 있습니다.

```
[수퍼바이저 에이전트]
    |
    +---> [주문 관리 에이전트] --- 주문 조회, 반품 처리
    +---> [제품 추천 에이전트] --- 제품 검색, 추천
    +---> [기술 지원 에이전트] --- 기술 문제 해결
```

```bash
# 수퍼바이저 에이전트의 하위 에이전트 연결
aws bedrock-agent create-agent-action-group \
  --agent-id "SUPERVISOR_AGENT_ID" \
  --agent-version "DRAFT" \
  --action-group-name "SubAgentCollaboration" \
  --parent-action-group-signature "AMAZON.AgentCollaborator" \
  --action-group-state "ENABLED" \
  --region us-east-1
```

---

## 실전 활용

### 사례 1: IT 운영 자동화 에이전트

클라우드 인프라의 상태를 확인하고 문제를 해결하는 에이전트를 구축하는 예시입니다.

```python
def lambda_handler(event, context):
    """IT 운영 에이전트의 Action Group Lambda"""
    api_path = event.get('apiPath', '')
    parameters = {p['name']: p['value'] for p in event.get('parameters', [])}
    
    ec2 = boto3.client('ec2')
    cloudwatch = boto3.client('cloudwatch')
    
    if api_path == '/instances/{instanceId}/status':
        instance_id = parameters['instanceId']
        response = ec2.describe_instance_status(
            InstanceIds=[instance_id],
            IncludeAllInstances=True
        )
        status = response['InstanceStatuses'][0] if response['InstanceStatuses'] else {}
        result = {
            'instanceId': instance_id,
            'instanceState': status.get('InstanceState', {}).get('Name', 'unknown'),
            'systemStatus': status.get('SystemStatus', {}).get('Status', 'unknown'),
            'instanceStatus': status.get('InstanceStatus', {}).get('Status', 'unknown')
        }
    elif api_path == '/instances/{instanceId}/metrics':
        instance_id = parameters['instanceId']
        metric_name = parameters.get('metricName', 'CPUUtilization')
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName=metric_name,
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime='2024-01-01T00:00:00Z',
            EndTime='2024-01-02T00:00:00Z',
            Period=3600,
            Statistics=['Average', 'Maximum']
        )
        result = {'metrics': str(response['Datapoints'][:5])}
    else:
        result = {'error': '지원하지 않는 작업입니다.'}
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event['actionGroup'],
            'apiPath': api_path,
            'httpMethod': event['httpMethod'],
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {'body': json.dumps(result)}
            }
        }
    }
```

### 사례 2: 세션 관리를 활용한 대화 유지

```python
def multi_turn_conversation():
    client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
    session_id = str(uuid.uuid4())
    
    conversations = [
        "저는 서울에 사는 김철수입니다. 주문번호 ORD-2024-001을 확인해 주십시오.",
        "해당 주문의 배송 예정일은 언제입니까?",
        "반품을 요청하고 싶습니다. 사이즈가 맞지 않습니다."
    ]
    
    for user_input in conversations:
        print(f"사용자: {user_input}")
        response = client.invoke_agent(
            agentId='AGENT123456',
            agentAliasId='ALIAS789',
            sessionId=session_id,  # 동일한 세션 ID 유지
            inputText=user_input
        )
        
        agent_response = ''
        for event in response['completion']:
            if 'chunk' in event:
                agent_response += event['chunk']['bytes'].decode('utf-8')
        
        print(f"에이전트: {agent_response}")
        print("---")
```

---

## 모범 사례/보안

### 에이전트 설계 원칙

- **명확한 지침 작성**: 에이전트의 instruction은 구체적이고 명확하게 작성합니다. 에이전트가 수행할 수 있는 작업과 수행하면 안 되는 작업을 명시합니다.
- **Action Group 세분화**: 하나의 Action Group에 너무 많은 API를 넣지 않습니다. 도메인별로 분리하여 에이전트의 선택 정확도를 높입니다.
- **오류 처리**: Lambda 함수에서 적절한 오류 메시지를 반환하여 에이전트가 사용자에게 유용한 피드백을 제공할 수 있게 합니다.
- **Trace 모니터링**: enableTrace를 활용하여 에이전트의 추론 과정을 모니터링하고 개선합니다.

### 보안 고려사항

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeAgent"
      ],
      "Resource": "arn:aws:bedrock:us-east-1:123456789012:agent-alias/AGENT123456/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:order-management",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalServiceName": "bedrock.amazonaws.com"
        }
      }
    }
  ]
}
```

### 비용 관리

- Agent 호출 비용은 FM 토큰 사용량에 비례합니다. ReAct 루프의 각 단계에서 토큰이 소비되므로, 효율적인 프롬프트 설계가 중요합니다.
- Knowledge Base 검색 비용(임베딩 + 벡터 DB 쿼리)이 추가로 발생합니다.
- Lambda 함수 실행 비용도 고려해야 합니다.
- 불필요한 ReAct 루프 반복을 줄이기 위해 Action Group의 API 설명을 상세하게 작성합니다.

---

## 관련 서비스 비교

| 항목 | Amazon Bedrock Agents | LangChain Agents | OpenAI Assistants API | AutoGen |
|------|----------------------|------------------|-----------------------|---------|
| 관리 방식 | 완전 관리형 | 자체 호스팅 | SaaS | 자체 호스팅 |
| 추론 패턴 | ReAct | 다양한 패턴 지원 | 내부 구현 | 대화 기반 |
| 도구 통합 | Lambda + OpenAPI | 커스텀 도구 | Function Calling | 커스텀 함수 |
| RAG | Knowledge Bases 내장 | 직접 구현 | Vector Store 내장 | 직접 구현 |
| 코드 실행 | Code Interpreter | Python REPL | Code Interpreter | 자동 실행 |
| 멀티 에이전트 | Agent Collaborator | LangGraph | Swarm(실험적) | 기본 지원 |
| 인프라 관리 | 불필요 | EC2/ECS 등 필요 | 불필요 | EC2/ECS 등 필요 |
| AWS 통합 | 네이티브 | SDK 기반 수동 | 미지원 | SDK 기반 수동 |

---

## 요약

Amazon Bedrock Agents는 FM 기반의 지능형 AI 에이전트를 완전 관리형으로 구축할 수 있는 프레임워크입니다. 주요 특징을 정리하면 다음과 같습니다.

- ReAct 패턴 기반의 추론-행동 루프로 복잡한 다단계 태스크를 자율적으로 수행합니다.
- Action Groups를 통해 Lambda 함수와 외부 API를 연동하여, FM이 실제 시스템을 조작할 수 있습니다.
- Knowledge Bases와의 네이티브 통합으로 RAG 기능을 손쉽게 추가할 수 있습니다.
- Code Interpreter를 통해 데이터 분석, 수학 계산, 시각화 등을 에이전트가 직접 수행합니다.
- 멀티 에이전트 협업을 통해 복잡한 비즈니스 프로세스를 여러 전문 에이전트가 분담하여 처리합니다.
- Trace 기능으로 에이전트의 의사결정 과정을 투명하게 관찰하고 디버깅할 수 있습니다.

Bedrock Agents는 고객 서비스, IT 운영 자동화, 데이터 분석 등 다양한 도메인에서 AI 에이전트를 빠르고 안전하게 배포할 수 있는 최적의 선택입니다.