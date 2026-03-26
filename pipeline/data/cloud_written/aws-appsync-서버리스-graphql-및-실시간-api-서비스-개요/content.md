## 개요

AWS AppSync는 GraphQL API를 완전관리형으로 생성, 배포, 운영할 수 있는 서비스입니다. GraphQL은 Facebook이 2015년에 오픈소스로 공개한 API 쿼리 언어로, REST API의 여러 한계를 해결하기 위해 설계되었습니다.

REST API에서는 클라이언트가 필요한 데이터를 얻기 위해 여러 엔드포인트를 호출해야 하는 경우가 많고(Under-fetching), 반대로 필요 이상의 데이터를 받아오는 경우도 흔합니다(Over-fetching). GraphQL은 클라이언트가 필요한 데이터의 구조를 정확히 명시할 수 있어 이러한 문제를 해결합니다.

AWS AppSync는 이러한 GraphQL의 장점에 AWS의 완전관리형 서비스 특성을 결합합니다. 개발자는 스키마를 정의하고 리졸버를 작성하면 되며, 서버 프로비저닝, 확장, 보안, 모니터링 등은 AppSync가 처리합니다.

AppSync의 핵심 차별점은 실시간 데이터 구독(Subscription) 기능입니다. WebSocket 기반으로 동작하며, 데이터 변경이 발생하면 구독 중인 모든 클라이언트에 자동으로 업데이트를 전송합니다. 채팅, 라이브 대시보드, 협업 도구 등 실시간 기능이 필요한 애플리케이션에 적합합니다.

또한 AppSync는 오프라인 데이터 동기화를 기본 지원합니다. AWS Amplify DataStore와 결합하면 모바일/웹 앱에서 오프라인 상태에서도 데이터를 읽고 쓸 수 있으며, 온라인 복귀 시 자동으로 서버와 동기화됩니다.

## 핵심 기능

### GraphQL 스키마

AppSync API는 GraphQL 스키마를 중심으로 동작합니다. 스키마는 API의 데이터 구조와 허용되는 작업(Query, Mutation, Subscription)을 정의합니다.

```graphql
# AppSync GraphQL 스키마 예시
type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  comments: [Comment!]
  createdAt: AWSDateTime!
  updatedAt: AWSDateTime!
  tags: [String!]
}

type User {
  id: ID!
  name: String!
  email: AWSEmail!
  posts: [Post!]
}

type Comment {
  id: ID!
  postId: ID!
  content: String!
  author: User!
  createdAt: AWSDateTime!
}

type Query {
  getPost(id: ID!): Post
  listPosts(limit: Int, nextToken: String): PostConnection!
  searchPosts(keyword: String!): [Post!]
}

type Mutation {
  createPost(input: CreatePostInput!): Post!
  updatePost(input: UpdatePostInput!): Post!
  deletePost(id: ID!): Post
  addComment(input: AddCommentInput!): Comment!
}

type Subscription {
  onCreatePost: Post @aws_subscribe(mutations: ["createPost"])
  onAddComment(postId: ID!): Comment @aws_subscribe(mutations: ["addComment"])
}

input CreatePostInput {
  title: String!
  content: String!
  tags: [String!]
}

input UpdatePostInput {
  id: ID!
  title: String
  content: String
  tags: [String!]
}

input AddCommentInput {
  postId: ID!
  content: String!
}

type PostConnection {
  items: [Post!]!
  nextToken: String
}
```

### 데이터 소스

AppSync는 다양한 AWS 서비스를 데이터 소스로 연결할 수 있습니다.

- **Amazon DynamoDB**: NoSQL 데이터 저장 및 조회
- **AWS Lambda**: 커스텀 비즈니스 로직 실행
- **Amazon RDS (Aurora Serverless)**: 관계형 데이터베이스 쿼리
- **Amazon OpenSearch Service**: 전문 검색
- **Amazon EventBridge**: 이벤트 발행
- **HTTP 엔드포인트**: 외부 REST API 호출
- **None (Local Resolver)**: 데이터 소스 없이 로컬에서 처리

### 리졸버 (Resolver)

리졸버는 GraphQL 필드와 데이터 소스를 연결하는 로직입니다. AppSync는 두 가지 리졸버 런타임을 지원합니다.

**JavaScript 리졸버 (APPSYNC_JS)**

최신 권장 방식으로, JavaScript로 리졸버를 작성합니다.

**VTL(Apache Velocity Template Language) 리졸버**

기존 방식으로, VTL 템플릿으로 리졸버를 작성합니다.

### 인증 방식

AppSync는 다양한 인증 방식을 지원하며, 하나의 API에 여러 인증 방식을 동시에 적용할 수 있습니다.

- **Amazon Cognito User Pools**: 사용자 인증 및 그룹 기반 권한 부여
- **API Key**: 간단한 인증 (개발/퍼블릭 API용)
- **AWS IAM**: AWS IAM 역할/사용자 기반 인증
- **OpenID Connect (OIDC)**: 외부 ID 제공자 연동
- **Lambda Authorizer**: 커스텀 인증 로직

## 아키텍처/동작 원리

### AppSync 요청 처리 흐름

1. 클라이언트가 GraphQL 요청(Query/Mutation/Subscription)을 AppSync 엔드포인트로 전송합니다.
2. AppSync는 인증/인가를 수행합니다.
3. GraphQL 스키마를 기반으로 요청을 파싱하고 검증합니다.
4. 해당 필드의 리졸버를 실행합니다.
5. 리졸버가 데이터 소스(DynamoDB, Lambda 등)에 요청을 보냅니다.
6. 응답을 GraphQL 스키마에 맞게 변환하여 클라이언트에 반환합니다.

```bash
# AppSync API 생성
aws appsync create-graphql-api \
  --name "blog-api" \
  --authentication-type AMAZON_COGNITO_USER_POOLS \
  --user-pool-config '{
    "userPoolId": "ap-northeast-2_xxxxxxxx",
    "awsRegion": "ap-northeast-2",
    "defaultAction": "ALLOW"
  }' \
  --additional-authentication-providers '[{
    "authenticationType": "API_KEY"
  }]' \
  --xray-enabled
```

```bash
# GraphQL 스키마 업로드
aws appsync start-schema-creation \
  --api-id abcdefghijklmnop \
  --definition fileb://schema.graphql

# 스키마 생성 상태 확인
aws appsync get-schema-creation-status \
  --api-id abcdefghijklmnop
```

### 데이터 소스 및 리졸버 설정

```bash
# DynamoDB 데이터 소스 생성
aws appsync create-data-source \
  --api-id abcdefghijklmnop \
  --name PostTable \
  --type AMAZON_DYNAMODB \
  --service-role-arn arn:aws:iam::123456789012:role/AppSyncDynamoDBRole \
  --dynamodb-config '{
    "tableName": "Post",
    "awsRegion": "ap-northeast-2"
  }'

# Lambda 데이터 소스 생성
aws appsync create-data-source \
  --api-id abcdefghijklmnop \
  --name SearchFunction \
  --type AWS_LAMBDA \
  --service-role-arn arn:aws:iam::123456789012:role/AppSyncLambdaRole \
  --lambda-config '{
    "lambdaFunctionArn": "arn:aws:lambda:ap-northeast-2:123456789012:function:search-posts"
  }'
```

### JavaScript 리졸버 예시

```javascript
// getPost 리졸버 (DynamoDB 직접 조회)
import { util } from '@aws-appsync/utils';

export function request(ctx) {
  return {
    operation: 'GetItem',
    key: util.dynamodb.toMapValues({ id: ctx.args.id })
  };
}

export function response(ctx) {
  if (ctx.error) {
    util.error(ctx.error.message, ctx.error.type);
  }
  return ctx.result;
}
```

```javascript
// listPosts 리졸버 (페이지네이션)
import { util } from '@aws-appsync/utils';

export function request(ctx) {
  const { limit = 20, nextToken } = ctx.args;
  return {
    operation: 'Scan',
    limit: Math.min(limit, 100),
    nextToken: nextToken || undefined
  };
}

export function response(ctx) {
  return {
    items: ctx.result.items,
    nextToken: ctx.result.nextToken
  };
}
```

### 파이프라인 리졸버

복잡한 로직이 필요한 경우, 여러 함수를 순차적으로 실행하는 파이프라인 리졸버를 사용할 수 있습니다.

```bash
# 파이프라인 리졸버용 함수 생성
aws appsync create-function \
  --api-id abcdefghijklmnop \
  --name ValidateInput \
  --data-source-name NONE_DS \
  --runtime '{"name": "APPSYNC_JS", "runtimeVersion": "1.0.0"}' \
  --code 'export function request(ctx) { 
    const input = ctx.args.input;
    if (!input.title || input.title.length < 3) {
      util.error("Title must be at least 3 characters");
    }
    return {};
  }
  export function response(ctx) { return ctx.prev.result; }'

aws appsync create-function \
  --api-id abcdefghijklmnop \
  --name SavePost \
  --data-source-name PostTable \
  --runtime '{"name": "APPSYNC_JS", "runtimeVersion": "1.0.0"}' \
  --code 'import { util } from "@aws-appsync/utils";
  export function request(ctx) {
    const id = util.autoId();
    const now = util.time.nowISO8601();
    return {
      operation: "PutItem",
      key: util.dynamodb.toMapValues({ id }),
      attributeValues: util.dynamodb.toMapValues({
        ...ctx.args.input,
        authorId: ctx.identity.sub,
        createdAt: now,
        updatedAt: now
      })
    };
  }
  export function response(ctx) { return ctx.result; }'
```

## 실전 활용

### 사례 1: 실시간 채팅 애플리케이션

AppSync의 Subscription 기능을 활용하면 실시간 채팅을 구현할 수 있습니다.

```graphql
# 채팅 관련 스키마
type Message {
  id: ID!
  roomId: ID!
  content: String!
  sender: User!
  createdAt: AWSDateTime!
}

type Mutation {
  sendMessage(roomId: ID!, content: String!): Message!
}

type Subscription {
  onNewMessage(roomId: ID!): Message
    @aws_subscribe(mutations: ["sendMessage"])
}
```

클라이언트에서 Subscription을 사용하는 예시입니다.

```javascript
// React 클라이언트에서 AppSync Subscription 사용
import { generateClient } from 'aws-amplify/api';

const client = generateClient();

// 메시지 구독
const subscription = client.graphql({
  query: `subscription OnNewMessage($roomId: ID!) {
    onNewMessage(roomId: $roomId) {
      id
      content
      sender { name }
      createdAt
    }
  }`,
  variables: { roomId: 'room-001' }
}).subscribe({
  next: ({ data }) => {
    console.log('New message:', data.onNewMessage);
  },
  error: (error) => {
    console.error('Subscription error:', error);
  }
});
```

### 사례 2: 멀티 데이터 소스 통합

하나의 GraphQL 쿼리로 DynamoDB, RDS, 외부 API의 데이터를 동시에 조회할 수 있습니다.

```bash
# API 상태 및 데이터 소스 확인
aws appsync list-data-sources \
  --api-id abcdefghijklmnop \
  --query 'dataSources[*].{Name:name,Type:type}' \
  --output table

# API 키 목록 조회
aws appsync list-api-keys \
  --api-id abcdefghijklmnop
```

### 사례 3: 캐싱 설정

AppSync는 서버 측 캐싱을 지원하여 반복적인 쿼리의 응답 속도를 높일 수 있습니다.

```bash
# API 캐싱 활성화
aws appsync create-api-cache \
  --api-id abcdefghijklmnop \
  --type T2_SMALL \
  --api-caching-behavior FULL_REQUEST_CACHING \
  --ttl 3600 \
  --transit-encryption-enabled \
  --at-rest-encryption-enabled
```

## 모범 사례/보안

### 보안 모범 사례

1. **다중 인증 방식 활용**: 퍼블릭 쿼리는 API Key, 인증된 사용자 작업은 Cognito, 서비스 간 통신은 IAM으로 분리합니다.
2. **필드 수준 권한 제어**: `@aws_auth` 디렉티브를 사용하여 필드별로 접근 권한을 설정합니다.
3. **쿼리 복잡도 제한**: 과도하게 중첩된 쿼리로 인한 자원 남용을 방지합니다.
4. **WAF 연동**: AWS WAF를 AppSync API 앞에 배치하여 악성 요청을 필터링합니다.
5. **X-Ray 추적**: X-Ray를 활성화하여 API 성능을 모니터링하고 병목을 식별합니다.

```bash
# WAF WebACL을 AppSync API에 연결
aws wafv2 associate-web-acl \
  --web-acl-arn arn:aws:wafv2:ap-northeast-2:123456789012:regional/webacl/appsync-protection/xxx \
  --resource-arn arn:aws:appsync:ap-northeast-2:123456789012:apis/abcdefghijklmnop
```

### 성능 최적화

1. **배치 리졸버 활용**: N+1 문제를 방지하기 위해 BatchGetItem, BatchInvoke 등을 사용합니다.
2. **서버 측 캐싱**: 자주 조회되는 데이터에 캐싱을 적용합니다.
3. **DynamoDB 단일 테이블 설계**: AppSync와 DynamoDB 조합 시, 단일 테이블 설계를 통해 리졸버 호출 수를 최소화합니다.
4. **Projection**: 클라이언트가 요청한 필드만 데이터 소스에서 조회하도록 리졸버를 최적화합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "appsync:GraphQL"
      ],
      "Resource": [
        "arn:aws:appsync:ap-northeast-2:123456789012:apis/abcdefghijklmnop/types/Query/fields/getPost",
        "arn:aws:appsync:ap-northeast-2:123456789012:apis/abcdefghijklmnop/types/Query/fields/listPosts"
      ]
    }
  ]
}
```

## 관련 서비스 비교

| 항목 | AWS AppSync | Amazon API Gateway (REST) | Amazon API Gateway (HTTP) |
|------|------------|--------------------------|---------------------------|
| API 유형 | GraphQL | REST | HTTP/REST |
| 실시간 지원 | WebSocket Subscription | WebSocket API (별도) | 미지원 |
| 데이터 소스 통합 | DynamoDB, Lambda, RDS 등 직접 연동 | Lambda 프록시 필요 | Lambda 프록시 필요 |
| 오프라인 지원 | Amplify DataStore 연동 | 미지원 | 미지원 |
| 스키마 정의 | GraphQL SDL | OpenAPI/Swagger | OpenAPI |
| 캐싱 | 서버 측 캐싱 내장 | API Gateway 캐시 | 미지원 |
| 인증 | Cognito, IAM, API Key, OIDC, Lambda | Cognito, IAM, API Key, Lambda | Cognito, IAM |
| 비용 | 쿼리/데이터 전송량 | 요청 수 + 데이터 전송 | 요청 수 + 데이터 전송 |
| 적합한 사용 사례 | 복잡한 데이터 모델, 실시간 앱 | 전통적 REST API | 경량 HTTP API |

**AppSync를 선택해야 하는 경우**: 여러 데이터 소스를 단일 API로 통합하고, 실시간 구독이나 오프라인 동기화가 필요한 경우에 적합합니다.

**API Gateway를 선택해야 하는 경우**: 전통적인 REST API가 필요하거나, 기존 REST 기반 마이크로서비스와의 호환이 중요한 경우에 적합합니다.

## 요약

AWS AppSync는 GraphQL API를 완전관리형으로 제공하는 서비스로, 다음과 같은 핵심 가치를 제공합니다.

- **GraphQL 완전관리형**: 스키마 정의와 리졸버 작성만으로 프로덕션 수준의 GraphQL API를 구축할 수 있습니다.
- **다중 데이터 소스 통합**: DynamoDB, Lambda, RDS, OpenSearch, HTTP 엔드포인트를 단일 API로 통합합니다.
- **실시간 구독**: WebSocket 기반의 실시간 데이터 업데이트를 기본 지원합니다.
- **오프라인 동기화**: Amplify DataStore와 연동하여 오프라인/온라인 데이터 동기화를 지원합니다.
- **유연한 인증**: Cognito, IAM, API Key, OIDC, Lambda Authorizer 등 다양한 인증 방식을 동시에 사용할 수 있습니다.
- **서버리스 확장**: 트래픽에 따라 자동으로 확장되며, 사용한 만큼만 과금됩니다.
- **개발 생산성**: Amplify CLI/SDK와의 통합으로 프론트엔드 개발자의 생산성을 높입니다.

AppSync는 특히 모바일 앱, SPA(Single Page Application), 실시간 협업 도구 등 복잡한 데이터 요구사항을 가진 프론트엔드 중심 애플리케이션에서 큰 가치를 발휘합니다.