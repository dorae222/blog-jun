<!-- infographic-hero -->
![Amazon API Gateway 핵심 요약](figures/infographic.svg)

*Figure: Amazon API Gateway 한 장 요약 인포그래픽*

# Amazon API Gateway 심층 분석

## 개요

Amazon API Gateway는 개발자가 규모에 관계없이 API를 손쉽게 생성, 게시, 유지 관리, 모니터링, 보안할 수 있는 완전관리형 서비스입니다. API Gateway는 트래픽 관리, CORS 지원, 권한 부여 및 액세스 제어, 스로틀링, 모니터링, API 버전 관리 등 API 호출의 수락 및 처리와 관련된 모든 작업을 처리합니다.

현대 애플리케이션 아키텍처에서 API는 프론트엔드와 백엔드, 마이크로서비스 간 통신, 외부 파트너 연동 등의 핵심 인터페이스입니다. API Gateway는 이러한 API의 관문(Gateway) 역할을 하며, 백엔드 서비스의 복잡성을 추상화하여 클라이언트에게 일관된 API 경험을 제공합니다.

API Gateway는 서버를 프로비저닝하거나 관리할 필요가 없으며, 수십만 개의 동시 API 호출을 자동으로 처리할 수 있습니다. 사용한 만큼만 비용을 지불하는 과금 모델을 따릅니다.

### API 유형

API Gateway는 세 가지 유형의 API를 지원합니다.

- **REST API**: 전통적인 RESTful API, 풍부한 기능 세트 제공
- **HTTP API**: REST API보다 저렴하고 빠른 경량 API
- **WebSocket API**: 실시간 양방향 통신 API

## 핵심 기능

### 1. REST API vs HTTP API

두 API 유형의 차이를 이해하는 것이 API Gateway 활용의 첫 단계입니다.

| 항목 | REST API | HTTP API |
|------|----------|----------|
| 비용 | $3.50/100만 요청 | $1.00/100만 요청 |
| 지연 시간 | ~29ms | ~10ms |
| API 키 관리 | 지원 | 미지원 |
| 리소스 정책 | 지원 | 미지원 |
| 요청/응답 변환 | 지원 (매핑 템플릿) | 미지원 |
| 캐싱 | 지원 | 미지원 |
| WAF 통합 | 지원 | 미지원 |
| 사용량 계획 | 지원 | 미지원 |
| 프라이빗 엔드포인트 | 지원 | 미지원 |

```bash
# REST API 생성
aws apigateway create-rest-api \
  --name "order-service-api" \
  --description "주문 서비스 REST API" \
  --endpoint-configuration types=REGIONAL \
  --tags Environment=Production,Team=Backend

# HTTP API 생성
aws apigatewayv2 create-api \
  --name "lightweight-api" \
  --protocol-type HTTP \
  --description "경량 HTTP API" \
  --cors-configuration '{
    "AllowOrigins": ["https://www.example.com"],
    "AllowMethods": ["GET", "POST", "PUT", "DELETE"],
    "AllowHeaders": ["Content-Type", "Authorization"],
    "MaxAge": 3600
  }'
```

### 2. 리소스와 메서드 구성

REST API에서는 리소스(URL 경로)와 메서드(HTTP 메서드)를 조합하여 API 엔드포인트를 구성합니다.

```bash
# 루트 리소스 ID 조회
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id "abc123" \
  --query 'items[?path==`/`].id' \
  --output text)

# /orders 리소스 생성
ORDERS_ID=$(aws apigateway create-resource \
  --rest-api-id "abc123" \
  --parent-id "$ROOT_ID" \
  --path-part "orders" \
  --query 'id' \
  --output text)

# /orders/{orderId} 리소스 생성
ORDER_ID=$(aws apigateway create-resource \
  --rest-api-id "abc123" \
  --parent-id "$ORDERS_ID" \
  --path-part "{orderId}" \
  --query 'id' \
  --output text)

# GET /orders 메서드 생성
aws apigateway put-method \
  --rest-api-id "abc123" \
  --resource-id "$ORDERS_ID" \
  --http-method GET \
  --authorization-type "COGNITO_USER_POOLS" \
  --authorizer-id "auth123"

# POST /orders 메서드 생성
aws apigateway put-method \
  --rest-api-id "abc123" \
  --resource-id "$ORDERS_ID" \
  --http-method POST \
  --authorization-type "COGNITO_USER_POOLS" \
  --authorizer-id "auth123" \
  --request-validator-id "validator123"
```

### 3. Lambda 프록시 통합

API Gateway와 Lambda를 연동하는 가장 일반적인 패턴은 Lambda 프록시 통합입니다. 이 방식에서는 전체 HTTP 요청이 Lambda 함수로 전달되며, Lambda가 직접 HTTP 응답 형식을 반환합니다.

```bash
# Lambda 프록시 통합 설정
aws apigateway put-integration \
  --rest-api-id "abc123" \
  --resource-id "$ORDERS_ID" \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:ap-northeast-2:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-northeast-2:123456789012:function:get-orders/invocations"

# Lambda 함수에 API Gateway 호출 권한 부여
aws lambda add-permission \
  --function-name "get-orders" \
  --statement-id "apigateway-invoke" \
  --action "lambda:InvokeFunction" \
  --principal "apigateway.amazonaws.com" \
  --source-arn "arn:aws:execute-api:ap-northeast-2:123456789012:abc123/*/GET/orders"
```

Lambda 함수의 응답 형식은 다음과 같아야 합니다.

```python
import json
import boto3

def lambda_handler(event, context):
    # event에서 요청 정보 추출
    http_method = event['httpMethod']
    path_parameters = event.get('pathParameters', {})
    query_parameters = event.get('queryStringParameters', {})
    body = json.loads(event.get('body', '{}')) if event.get('body') else {}
    
    # 비즈니스 로직 처리
    orders = get_orders_from_db(query_parameters)
    
    # API Gateway가 기대하는 응답 형식
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'orders': orders,
            'count': len(orders)
        })
    }

def get_orders_from_db(params):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('Orders')
    response = table.scan(Limit=params.get('limit', 20))
    return response['Items']
```

### 4. 인증 및 인가

API Gateway는 다양한 인증/인가 메커니즘을 지원합니다.

**Cognito 사용자 풀 인증:**

```bash
# Cognito 인증자 생성
aws apigateway create-authorizer \
  --rest-api-id "abc123" \
  --name "cognito-authorizer" \
  --type COGNITO_USER_POOLS \
  --provider-arns "arn:aws:cognito-idp:ap-northeast-2:123456789012:userpool/ap-northeast-2_abc123" \
  --identity-source "method.request.header.Authorization"
```

**Lambda 인증자 (Custom Authorizer):**

```bash
# Lambda 인증자 생성
aws apigateway create-authorizer \
  --rest-api-id "abc123" \
  --name "custom-jwt-authorizer" \
  --type TOKEN \
  --authorizer-uri "arn:aws:apigateway:ap-northeast-2:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-northeast-2:123456789012:function:jwt-authorizer/invocations" \
  --identity-source "method.request.header.Authorization" \
  --authorizer-result-ttl-in-seconds 300
```

Lambda 인증자 함수 예시입니다.

```python
import jwt

def lambda_handler(event, context):
    token = event['authorizationToken'].replace('Bearer ', '')
    
    try:
        decoded = jwt.decode(token, 'secret-key', algorithms=['HS256'])
        user_id = decoded['sub']
        
        return generate_policy(user_id, 'Allow', event['methodArn'])
    except jwt.ExpiredSignatureError:
        raise Exception('Unauthorized')
    except jwt.InvalidTokenError:
        raise Exception('Unauthorized')

def generate_policy(principal_id, effect, resource):
    return {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [{
                'Action': 'execute-api:Invoke',
                'Effect': effect,
                'Resource': resource
            }]
        },
        'context': {
            'userId': principal_id
        }
    }
```

### 5. 스테이지와 배포

API Gateway에서는 스테이지를 통해 API의 여러 버전을 관리합니다.

```bash
# API 배포 생성
DEPLOYMENT_ID=$(aws apigateway create-deployment \
  --rest-api-id "abc123" \
  --description "v2.1 배포 - 주문 검색 기능 추가" \
  --query 'id' \
  --output text)

# 스테이지 생성
aws apigateway create-stage \
  --rest-api-id "abc123" \
  --stage-name "production" \
  --deployment-id "$DEPLOYMENT_ID" \
  --description "프로덕션 스테이지" \
  --variables '{"lambdaAlias": "live", "tableName": "Orders-Prod"}' \
  --tags Environment=Production

# 스테이지 변수 활용: Lambda 별칭으로 트래픽 제어
aws apigateway update-stage \
  --rest-api-id "abc123" \
  --stage-name "production" \
  --patch-operations \
    op=replace,path=/variables/lambdaAlias,value=live-v2
```

### 6. 스로틀링과 사용량 계획

```bash
# 사용량 계획 생성
aws apigateway create-usage-plan \
  --name "standard-plan" \
  --description "표준 사용량 계획" \
  --throttle burstLimit=100,rateLimit=50 \
  --quota limit=10000,period=MONTH \
  --api-stages '[{"apiId":"abc123","stage":"production"}]'

# API 키 생성
aws apigateway create-api-key \
  --name "partner-a-key" \
  --description "파트너 A용 API 키" \
  --enabled

# API 키를 사용량 계획에 연결
aws apigateway create-usage-plan-key \
  --usage-plan-id "plan123" \
  --key-id "key123" \
  --key-type "API_KEY"
```

## 아키텍처/동작 원리

### API Gateway 요청 처리 흐름

```
[클라이언트]     [API Gateway]                          [백엔드]
    |                |                                      |
    |-- HTTP 요청 -->|                                      |
    |                |-- 1. 인증/인가 확인                   |
    |                |-- 2. 요청 검증                        |
    |                |-- 3. 요청 매핑/변환                   |
    |                |-- 4. 스로틀링 확인                    |
    |                |-- 5. 캐시 확인 (REST API)             |
    |                |-- 6. 백엔드 호출 ------------------>  |
    |                |                  <-- 응답 ----------  |
    |                |-- 7. 응답 매핑/변환                   |
    |                |-- 8. 로깅/메트릭                      |
    |<-- HTTP 응답 --|                                      |
```

### 엔드포인트 유형

API Gateway REST API는 세 가지 엔드포인트 유형을 지원합니다.

- **Edge-Optimized**: CloudFront를 통해 글로벌 클라이언트에 최적화 (기본값)
- **Regional**: 같은 리전의 클라이언트에 최적화
- **Private**: VPC 내부에서만 접근 가능

```bash
# 프라이빗 API 생성
aws apigateway create-rest-api \
  --name "internal-api" \
  --description "내부 전용 API" \
  --endpoint-configuration types=PRIVATE \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": "*",
      "Action": "execute-api:Invoke",
      "Resource": "execute-api:/*",
      "Condition": {
        "StringEquals": {
          "aws:sourceVpce": "vpce-abc123"
        }
      }
    }]
  }'
```

### WebSocket API 동작 원리

```
[클라이언트]     [API Gateway WebSocket]        [백엔드]
    |                    |                         |
    |-- $connect ------->|-- Lambda(connect) ------>|
    |<-- 101 Switching --|                         |
    |                    |                         |
    |-- 메시지 전송 ---->|-- Lambda(message) ------>|
    |                    |<-- @connections API -----|  (서버에서 클라이언트로)
    |<-- 메시지 수신 ----|                         |
    |                    |                         |
    |-- $disconnect ---->|-- Lambda(disconnect) --->|
```

```bash
# WebSocket API 생성
aws apigatewayv2 create-api \
  --name "chat-websocket-api" \
  --protocol-type WEBSOCKET \
  --route-selection-expression '$request.body.action'

# $connect 라우트 설정
aws apigatewayv2 create-route \
  --api-id "ws-abc123" \
  --route-key '$connect'

# 메시지 라우트 설정
aws apigatewayv2 create-route \
  --api-id "ws-abc123" \
  --route-key "sendMessage"
```

## 실전 활용

### 사례 1: 서버리스 마이크로서비스 아키텍처

API Gateway + Lambda + DynamoDB로 구성하는 서버리스 마이크로서비스 패턴입니다.

```bash
# OpenAPI(Swagger) 정의로 API 일괄 생성
aws apigateway import-rest-api \
  --body file://api-definition.yaml \
  --fail-on-warnings
```

```yaml
# api-definition.yaml
openapi: "3.0.1"
info:
  title: "Order Service API"
  version: "2.0"
paths:
  /orders:
    get:
      summary: "주문 목록 조회"
      x-amazon-apigateway-integration:
        type: aws_proxy
        httpMethod: POST
        uri: "arn:aws:apigateway:ap-northeast-2:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-northeast-2:123456789012:function:list-orders/invocations"
    post:
      summary: "주문 생성"
      x-amazon-apigateway-integration:
        type: aws_proxy
        httpMethod: POST
        uri: "arn:aws:apigateway:ap-northeast-2:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-northeast-2:123456789012:function:create-order/invocations"
  /orders/{orderId}:
    get:
      summary: "주문 상세 조회"
      parameters:
        - name: orderId
          in: path
          required: true
          schema:
            type: string
      x-amazon-apigateway-integration:
        type: aws_proxy
        httpMethod: POST
        uri: "arn:aws:apigateway:ap-northeast-2:lambda:path/2015-03-31/functions/arn:aws:lambda:ap-northeast-2:123456789012:function:get-order/invocations"
```

### 사례 2: 커스텀 도메인 설정

```bash
# ACM 인증서 생성 (us-east-1 리전, Edge-optimized API의 경우)
aws acm request-certificate \
  --domain-name "api.example.com" \
  --validation-method DNS \
  --region us-east-1

# 커스텀 도메인 생성
aws apigateway create-domain-name \
  --domain-name "api.example.com" \
  --certificate-arn "arn:aws:acm:us-east-1:123456789012:certificate/cert-id" \
  --security-policy TLS_1_2

# API 매핑
aws apigateway create-base-path-mapping \
  --domain-name "api.example.com" \
  --rest-api-id "abc123" \
  --stage "production" \
  --base-path "v2"
```

### 사례 3: 요청/응답 캐싱

```bash
# 스테이지에 캐싱 활성화
aws apigateway update-stage \
  --rest-api-id "abc123" \
  --stage-name "production" \
  --patch-operations \
    op=replace,path=/cacheClusterEnabled,value=true \
    op=replace,path=/cacheClusterSize,value=0.5

# 특정 메서드에 캐싱 설정 적용
aws apigateway update-method \
  --rest-api-id "abc123" \
  --resource-id "resource123" \
  --http-method GET \
  --patch-operations \
    op=replace,path=/cacheKeyParameters/method.request.querystring.category,value=true

# 캐시 무효화 (특정 클라이언트)
# Cache-Control: max-age=0 헤더를 포함하여 요청
```

## 모범 사례/보안

### WAF 통합

```bash
# WAF WebACL을 API Gateway 스테이지에 연결
aws wafv2 associate-web-acl \
  --web-acl-arn "arn:aws:wafv2:ap-northeast-2:123456789012:regional/webacl/api-protection/abc123" \
  --resource-arn "arn:aws:apigateway:ap-northeast-2::/restapis/abc123/stages/production"
```

### 로깅 설정

```bash
# CloudWatch 로그 그룹 생성
aws logs create-log-group \
  --log-group-name "API-Gateway/abc123/production"

# 스테이지에 액세스 로깅 활성화
aws apigateway update-stage \
  --rest-api-id "abc123" \
  --stage-name "production" \
  --patch-operations \
    op=replace,path=/accessLogSettings/destinationArn,value="arn:aws:logs:ap-northeast-2:123456789012:log-group:API-Gateway/abc123/production" \
    op=replace,path=/accessLogSettings/format,value='{"requestId":"$context.requestId","ip":"$context.identity.sourceIp","caller":"$context.identity.caller","user":"$context.identity.user","requestTime":"$context.requestTime","httpMethod":"$context.httpMethod","resourcePath":"$context.resourcePath","status":"$context.status","protocol":"$context.protocol","responseLength":"$context.responseLength"}'
```

### 비용 최적화

- 단순한 프록시 기능만 필요하다면 HTTP API를 선택합니다 (REST API 대비 약 70% 저렴).
- API 응답 캐싱을 활성화하여 백엔드 호출을 줄입니다.
- 사용량 계획과 스로틀링으로 과도한 사용을 방지합니다.

### 요청 검증

```bash
# 요청 검증기 생성
aws apigateway create-request-validator \
  --rest-api-id "abc123" \
  --name "body-and-params-validator" \
  --validate-request-body \
  --validate-request-parameters
```

## 관련 서비스 비교

### API Gateway vs ALB (Application Load Balancer)

| 항목 | API Gateway | ALB |
|------|------------|-----|
| 목적 | API 관리 | HTTP/HTTPS 로드 밸런싱 |
| 인증 | Cognito, Lambda 인증자, IAM | Cognito, OIDC |
| 스로틀링 | 기본 제공 | 미지원 |
| WebSocket | 지원 | 지원 |
| 비용 모델 | 요청당 과금 | 시간당 + LCU |
| 서버리스 통합 | Lambda 네이티브 | Lambda 대상 그룹 |

### API Gateway vs AppSync

| 항목 | API Gateway | AppSync |
|------|------------|----------|
| 프로토콜 | REST/HTTP/WebSocket | GraphQL |
| 실시간 | WebSocket API | Subscriptions |
| 데이터 소스 | Lambda/HTTP/AWS 서비스 | DynamoDB/Lambda/RDS/HTTP 직접 연결 |
| 오프라인 지원 | 미지원 | Amplify DataStore 지원 |

### API Gateway REST API vs HTTP API

REST API는 풍부한 기능(캐싱, WAF, 요청 변환, API 키 관리 등)이 필요할 때, HTTP API는 단순한 프록시나 비용이 중요한 경우에 선택합니다.

## 요약

Amazon API Gateway는 서버리스 아키텍처의 핵심 구성요소로, API의 생성부터 보안, 모니터링, 버전 관리까지 전체 생명주기를 관리합니다.

핵심 포인트를 정리하면 다음과 같습니다.

- REST API, HTTP API, WebSocket API 세 가지 유형 중 요구 사항에 맞는 유형을 선택해야 합니다.
- Lambda 프록시 통합이 가장 일반적인 백엔드 연동 패턴이며, 서버리스 마이크로서비스 아키텍처의 기반입니다.
- Cognito, Lambda 인증자, IAM 등 다양한 인증/인가 메커니즘을 지원하며, 사용 사례에 맞게 선택합니다.
- 스테이지와 스테이지 변수를 활용하여 API 버전과 환경을 관리합니다.
- WAF 통합, 스로틀링, 요청 검증으로 API 보안을 강화합니다.
- HTTP API는 REST API 대비 약 70% 저렴하고 지연 시간도 짧으므로, 고급 기능이 불필요한 경우 HTTP API를 선택하는 것이 비용 효과적입니다.