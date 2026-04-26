<!-- infographic-hero -->
![Amazon Cognito 핵심 요약](figures/infographic.svg)

*Figure: Amazon Cognito 한 장 요약 인포그래픽*

# Amazon Cognito 사용자 인증 서비스 개요

## 개요

Amazon Cognito는 웹과 모바일 애플리케이션을 위한 완전 관리형 사용자 인증, 인가, 사용자 관리 서비스입니다. 2014년 출시된 이래 수많은 AWS 기반 B2C 애플리케이션의 인증 백엔드로 사용되어 왔으며, 2024년에는 대규모 재설계를 통해 User Pool과 Identity Pool의 사용성을 통합하는 방향으로 발전하고 있습니다.

Cognito는 다음과 같은 핵심 가치를 제공합니다.

- **완전 관리형**: 회원가입, 로그인, 비밀번호 재설정, MFA 등 인증 인프라를 직접 구축할 필요 없음
- **AWS 통합**: API Gateway, ALB, AppSync 등과 네이티브 통합
- **Federation**: Google, Facebook, Apple, SAML, OIDC 등 외부 IdP 지원
- **확장성**: 수백만 명의 사용자를 자동 확장으로 처리
- **보안**: Adaptive Authentication, Compromised Credentials 검사

Cognito는 두 개의 독립적인 서비스로 구성됩니다.

- **User Pool**: 사용자 디렉토리. 회원가입/로그인 처리. JWT 토큰 발급.
- **Identity Pool (Federated Identities)**: 인증된 또는 익명 사용자에게 임시 AWS 자격 증명 발급.

이 둘은 함께 사용할 수도 있고 독립적으로 사용할 수도 있습니다. User Pool만으로는 자체 백엔드 API에 대한 인증을, Identity Pool과 결합하면 사용자가 직접 S3, DynamoDB 같은 AWS 리소스에 접근하는 모델을 구현할 수 있습니다.

자체 인증 시스템을 구축하면 비밀번호 해싱, 토큰 관리, MFA, 소셜 로그인, 세션 관리, 보안 패치 등 끊임없는 작업이 발생하지만, Cognito는 이 모든 것을 추상화합니다.

---

## 핵심 기능

### 1. User Pool

User Pool은 사용자 디렉토리이자 인증 서비스입니다. 다음 기능을 제공합니다.

- **회원가입/로그인**: 이메일, 전화번호, 사용자명 기반 가입
- **비밀번호 정책**: 최소 길이, 대소문자, 숫자, 특수문자 요구사항
- **MFA**: SMS, TOTP(인증 앱) 지원
- **이메일/SMS 검증**: SES, SNS와 통합
- **JWT 토큰 발급**: ID Token, Access Token, Refresh Token

```bash
# User Pool 생성
aws cognito-idp create-user-pool \
  --pool-name MyAppUserPool \
  --policies '{
    "PasswordPolicy": {
      "MinimumLength": 12,
      "RequireUppercase": true,
      "RequireLowercase": true,
      "RequireNumbers": true,
      "RequireSymbols": true
    }
  }' \
  --auto-verified-attributes email \
  --mfa-configuration OPTIONAL \
  --schema Name=email,Required=true,Mutable=true \
           Name=name,Required=false,Mutable=true
```

User Pool에는 App Client를 등록하여 클라이언트(웹/모바일 앱)가 통신합니다.

```bash
# App Client 생성
aws cognito-idp create-user-pool-client \
  --user-pool-id ap-northeast-2_AbCdEf123 \
  --client-name MyAppClient \
  --explicit-auth-flows ALLOW_USER_SRP_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --token-validity-units '{
    "AccessToken": "minutes",
    "IdToken": "minutes",
    "RefreshToken": "days"
  }' \
  --access-token-validity 60 \
  --id-token-validity 60 \
  --refresh-token-validity 30
```

### 2. Identity Pool (Federated Identities)

Identity Pool은 외부 인증 결과를 받아 임시 AWS 자격 증명을 발급합니다.

- **인증된 사용자(Authenticated)**: User Pool, Google, Facebook, SAML 등에서 검증된 사용자
- **게스트 사용자(Unauthenticated)**: 로그인하지 않은 사용자에게도 제한된 권한 부여 가능

각 사용자 그룹은 IAM Role과 매핑되며, 클라이언트는 해당 Role의 임시 자격 증명을 받아 AWS 리소스(S3, DynamoDB 등)에 직접 접근할 수 있습니다.

```bash
# Identity Pool 생성 (User Pool 연동)
aws cognito-identity create-identity-pool \
  --identity-pool-name MyAppIdentityPool \
  --allow-unauthenticated-identities \
  --cognito-identity-providers \
    ProviderName=cognito-idp.ap-northeast-2.amazonaws.com/ap-northeast-2_AbCdEf123,ClientId=1example23456789,ServerSideTokenCheck=true

# Role 매핑
aws cognito-identity set-identity-pool-roles \
  --identity-pool-id ap-northeast-2:abc12345-def6-7890-abcd-1234567890ab \
  --roles authenticated=arn:aws:iam::123456789012:role/Cognito_Authenticated,unauthenticated=arn:aws:iam::123456789012:role/Cognito_Guest
```

### 3. 인증 흐름(Auth Flow)

User Pool은 여러 인증 흐름을 지원하며, 각각 보안 수준이 다릅니다.

| 흐름 | 설명 | 권장도 |
|------|------|--------|
| `ALLOW_USER_SRP_AUTH` | SRP(Secure Remote Password) 프로토콜. 비밀번호가 네트워크로 전송되지 않음 | 가장 권장 |
| `ALLOW_USER_PASSWORD_AUTH` | 평문 비밀번호 전송 (HTTPS 위) | 비권장 |
| `ALLOW_ADMIN_USER_PASSWORD_AUTH` | 관리자가 서버에서 사용자 인증 | 백엔드용 |
| `ALLOW_REFRESH_TOKEN_AUTH` | Refresh Token으로 새 Access Token 발급 | 항상 활성화 |
| `ALLOW_CUSTOM_AUTH` | 커스텀 인증 (Lambda Trigger) | 패스워드리스 등 특수 케이스 |

SRP 흐름은 비밀번호 검증을 위한 수학적 증명을 클라이언트와 서버 사이에서 교환하므로, 중간자 공격(MITM)에 강합니다.

```javascript
// AWS Amplify를 사용한 SRP 로그인 (JavaScript)
import { Auth } from 'aws-amplify';

const user = await Auth.signIn(username, password);
console.log(user.signInUserSession.idToken.jwtToken);
```

### 4. JWT 토큰 구조

User Pool은 로그인 성공 시 세 가지 JWT 토큰을 발급합니다.

| 토큰 | 용도 | 기본 수명 |
|------|------|----------|
| ID Token | 사용자 정보 (claims). 클라이언트 식별용 | 1시간 |
| Access Token | API 호출 시 인가 헤더에 포함 | 1시간 |
| Refresh Token | Access Token 갱신용 | 30일 |

ID Token의 페이로드 예시:

```json
{
  "sub": "abc12345-def6-7890-abcd-1234567890ab",
  "email": "user@example.com",
  "email_verified": true,
  "cognito:username": "user@example.com",
  "cognito:groups": ["Admin", "PowerUser"],
  "iss": "https://cognito-idp.ap-northeast-2.amazonaws.com/ap-northeast-2_AbCdEf123",
  "aud": "1example23456789",
  "exp": 1700000000,
  "iat": 1699996400
}
```

API Gateway, ALB는 이 JWT를 자동 검증할 수 있습니다.

### 5. Federation (외부 IdP 연동)

Cognito User Pool은 외부 IdP를 통한 로그인을 지원합니다.

- **소셜 IdP**: Google, Facebook, Amazon, Apple
- **OpenID Connect (OIDC)**: 모든 OIDC 호환 IdP
- **SAML 2.0**: 기업용 SSO (Okta, Azure AD, ADFS)

```bash
# Google IdP 추가
aws cognito-idp create-identity-provider \
  --user-pool-id ap-northeast-2_AbCdEf123 \
  --provider-name Google \
  --provider-type Google \
  --provider-details client_id=GOOGLE_CLIENT_ID.apps.googleusercontent.com,client_secret=GOOGLE_CLIENT_SECRET,authorize_scopes="email openid profile" \
  --attribute-mapping email=email,name=name,picture=picture
```

외부 IdP로 로그인한 사용자는 User Pool 내부에 자동으로 사용자 레코드가 생성됩니다.

### 6. Hosted UI

Hosted UI는 Cognito가 제공하는 사전 구현된 로그인 페이지입니다. 회원가입, 로그인, 비밀번호 재설정, MFA 설정 등 모든 인증 화면을 즉시 사용할 수 있습니다.

- 도메인 설정: `https://<your-prefix>.auth.<region>.amazoncognito.com` 또는 커스텀 도메인
- 로고, 색상, 폰트 등 기본적인 브랜딩 가능
- OAuth 2.0 플로우 (Authorization Code, Implicit) 지원

```bash
# 도메인 설정
aws cognito-idp create-user-pool-domain \
  --user-pool-id ap-northeast-2_AbCdEf123 \
  --domain my-app-auth
```

OAuth 콜백 URL은 App Client 설정에서 등록합니다.

### 7. Lambda Triggers

Cognito는 인증 라이프사이클의 여러 시점에서 Lambda 함수를 실행할 수 있습니다. 이를 통해 비즈니스 로직을 인증 흐름에 통합할 수 있습니다.

| 트리거 | 호출 시점 | 사용 사례 |
|--------|----------|----------|
| PreSignUp | 회원가입 직전 | 도메인 화이트리스트 검증, 자동 확인 |
| PostConfirmation | 이메일/SMS 확인 후 | DB에 사용자 프로필 생성 |
| PreAuthentication | 로그인 직전 | 추가 검증, 봇 차단 |
| PostAuthentication | 로그인 직후 | 로그인 이력 기록 |
| PreTokenGeneration | JWT 발급 직전 | 커스텀 클레임 추가 |
| MigrateUser | 외부 시스템에서 마이그레이션 | 기존 DB 사용자 자동 가져오기 |
| CustomMessage | 이메일/SMS 발송 직전 | 다국어 메시지 커스터마이징 |
| DefineAuthChallenge | 커스텀 인증 흐름 정의 | 패스워드리스, OTP 인증 |

```python
# PreTokenGeneration Lambda 예시 - 커스텀 클레임 추가
def lambda_handler(event, context):
    event['response']['claimsOverrideDetails'] = {
        'claimsToAddOrOverride': {
            'tenant_id': get_tenant_id(event['userName']),
            'subscription_plan': 'premium'
        }
    }
    return event
```

### 8. Advanced Security

User Pool의 Advanced Security 기능은 추가 비용($0.05/MAU)으로 다음을 제공합니다.

- **Adaptive Authentication**: 위험 점수 기반으로 MFA 강제 또는 차단
- **Compromised Credentials**: 외부에서 유출된 비밀번호 사용 시 차단
- **Risk-based Logging**: 의심스러운 로그인 시도 기록

위험 점수는 IP 평판, 디바이스 식별, 행동 패턴 등을 종합하여 계산됩니다.

---

## 아키텍처

### Cognito User Pool + Identity Pool 통합 흐름

전형적인 모바일 앱이 S3에 직접 접근하는 시나리오:

```
[Mobile App]
    |
    | (1) USER_SRP_AUTH (username/password)
    v
[Cognito User Pool]
    |
    | (2) JWT Tokens (ID, Access, Refresh)
    v
[Mobile App]
    |
    | (3) GetCredentialsForIdentity (with ID Token)
    v
[Cognito Identity Pool]
    |
    | (4) STS AssumeRoleWithWebIdentity
    v
[AWS STS]
    |
    | (5) Temporary AWS Credentials
    v
[Mobile App]
    |
    | (6) S3 PutObject (with temp credentials)
    v
[Amazon S3]
```

이 모델의 장점은 백엔드 서버 없이 모바일 앱이 직접 AWS 리소스에 접근할 수 있다는 점입니다. IAM Role의 Condition으로 사용자별 디렉토리 분리도 가능합니다.

```json
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:PutObject"],
  "Resource": "arn:aws:s3:::user-uploads/${cognito-identity.amazonaws.com:sub}/*"
}
```

### API Gateway + Cognito Authorizer

Cognito User Pool을 API Gateway에 직접 연결하여 JWT 검증을 위임할 수 있습니다.

```
[Client]
   |
   | (1) Login -> User Pool -> JWT 획득
   v
[Client]
   |
   | (2) API 호출 (Authorization: Bearer <JWT>)
   v
[API Gateway + Cognito Authorizer]
   |
   | (3) JWT 자동 검증 (서명, 만료, claims)
   v
[Lambda / Backend]
```

API Gateway는 JWT의 `cognito:groups` 클레임으로 OAuth Scope 기반 인가도 수행할 수 있습니다.

### ALB Authenticate Action

ALB는 Cognito와 통합하여 Layer 7에서 인증을 강제할 수 있습니다.

```
[User] -> [ALB] -> [Cognito Hosted UI] -> [User] -> [ALB] -> [Backend]
                       (login)                       (cookie)
```

ALB는 인증 후 사용자 정보를 백엔드로 헤더(`X-Amzn-Oidc-Identity`, `X-Amzn-Oidc-Data`)로 전달합니다. 백엔드는 이를 검증만 하면 됩니다.

---

## 실전 사용

### 1. SPA 인증 (React + Amplify)

```javascript
import { Auth } from 'aws-amplify';

// 회원가입
await Auth.signUp({
  username: 'user@example.com',
  password: 'SecurePass123!',
  attributes: { email: 'user@example.com', name: '홍길동' }
});

// 이메일 확인
await Auth.confirmSignUp('user@example.com', '123456');

// 로그인
const user = await Auth.signIn('user@example.com', 'SecurePass123!');
const idToken = user.signInUserSession.idToken.jwtToken;

// API 호출
const response = await fetch('/api/profile', {
  headers: { Authorization: `Bearer ${idToken}` }
});
```

### 2. 백엔드에서 JWT 검증 (Node.js)

```javascript
const { CognitoJwtVerifier } = require('aws-jwt-verify');

const verifier = CognitoJwtVerifier.create({
  userPoolId: 'ap-northeast-2_AbCdEf123',
  tokenUse: 'access',
  clientId: '1example23456789'
});

try {
  const payload = await verifier.verify(token);
  console.log('Valid token:', payload.sub);
} catch (e) {
  console.error('Invalid token:', e);
}
```

### 3. 사용자 마이그레이션

기존 인증 시스템에서 Cognito로 마이그레이션 시 MigrateUser Lambda Trigger를 사용하면 사용자가 처음 로그인하는 시점에 자동으로 Cognito에 등록됩니다.

```python
def lambda_handler(event, context):
    if event['triggerSource'] == 'UserMigration_Authentication':
        # 기존 DB에서 사용자 검증
        user = legacy_auth(event['userName'], event['request']['password'])
        if user:
            event['response']['userAttributes'] = {
                'email': user.email,
                'email_verified': 'true',
                'name': user.name
            }
            event['response']['finalUserStatus'] = 'CONFIRMED'
            event['response']['messageAction'] = 'SUPPRESS'
    return event
```

---

## 가격/한도

### 가격 (us-east-1, MAU 기반)

| 항목 | 가격 |
|------|------|
| User Pool MAU (월간 활성 사용자) | 첫 50,000 무료, 이후 $0.0055/MAU |
| Federation MAU (SAML/OIDC) | 첫 50 무료, 이후 $0.015/MAU |
| Advanced Security | MAU당 추가 $0.05 |
| SMS (US) | 메시지당 $0.00645 (SNS 비용 별도) |
| Identity Pool | 무료 (STS 호출만 과금) |

소셜 IdP(Google, Facebook 등) 사용은 추가 비용이 없습니다. SAML/OIDC는 별도 과금됩니다.

### 주요 한도

| 항목 | 기본 한도 |
|------|----------|
| User Pool당 사용자 수 | 4천만 |
| User Pool당 App Client 수 | 1,000 |
| User Pool당 IdP 수 | 33 |
| User Pool당 Lambda Trigger 수 | 1개/트리거 종류 |
| API 요청 한도 | 10~25 RPS (작업별, 증가 요청 가능) |
| 비밀번호 최대 길이 | 256자 |

---

## Best Practice

### 1. SRP 흐름 사용

`ALLOW_USER_SRP_AUTH`만 활성화하고 `ALLOW_USER_PASSWORD_AUTH`는 비활성화합니다. 평문 비밀번호 전송을 차단합니다.

### 2. 토큰 수명 최적화

- Access Token / ID Token: 짧게 (15~60분). 탈취 시 영향 최소화.
- Refresh Token: 적당히 (7~30일). UX와 보안의 균형.
- 보안이 중요한 앱은 Refresh Token도 1일 이내로 설정하고 백그라운드 갱신을 구현합니다.

### 3. MFA 필수화

관리자 계정과 민감 데이터 접근 사용자에게는 MFA를 필수로 설정합니다. TOTP(Google Authenticator 등)가 SMS보다 안전합니다.

```bash
aws cognito-idp set-user-pool-mfa-config \
  --user-pool-id ap-northeast-2_AbCdEf123 \
  --mfa-configuration ON \
  --software-token-mfa-configuration Enabled=true
```

### 4. Hosted UI 활용

자체 로그인 페이지를 구현하기보다 Hosted UI를 사용하면 OAuth 표준 준수, 보안 패치 자동 적용, 다양한 IdP 통합이 즉시 가능합니다.

### 5. Lambda Trigger로 일관성 보장

PostConfirmation Trigger로 사용자 가입 시 자체 DB에도 프로필 레코드를 자동 생성하여 양쪽 데이터를 동기화합니다.

### 6. Group 기반 권한 관리

Cognito User Group을 활용하여 사용자별 권한을 관리합니다. JWT의 `cognito:groups` 클레임으로 백엔드에서 권한을 판단할 수 있습니다.

```bash
aws cognito-idp create-group \
  --group-name Admin \
  --user-pool-id ap-northeast-2_AbCdEf123 \
  --precedence 1
```

---

## 관련 서비스 비교

| 항목 | Amazon Cognito | Auth0 | Firebase Auth |
|------|---------------|-------|---------------|
| 배포 모델 | AWS 관리형 | SaaS (Auth0 호스팅) | Google 관리형 |
| AWS 통합 | 네이티브 (API GW, ALB, IAM) | 외부 통합 필요 | 약함 |
| Federation | 소셜, SAML, OIDC | 광범위 | 소셜 위주 |
| 가격 | MAU 기반 ($0.0055~) | MAU 기반 ($0.023~) | 무료 ~ MAU 기반 |
| 커스터마이징 | Lambda Trigger | Actions/Rules | Cloud Functions |
| 기업용 SSO | SAML 지원 (추가 과금) | 강력함 | 제한적 |
| 적합 사례 | AWS 기반 B2C 앱 | 멀티 클라우드 기업용 | Firebase 기반 모바일 앱 |

---

## 관련 서비스

| 서비스 | 통합 |
|--------|------|
| API Gateway | Cognito Authorizer로 JWT 검증 위임 |
| Application Load Balancer | Authenticate Action으로 인증 강제 |
| AWS AppSync | GraphQL API의 인증 |
| AWS Amplify | 프론트엔드 SDK + Cognito 자동 통합 |
| AWS IAM | Identity Pool로 임시 IAM 자격 증명 발급 |
| AWS WAF | Cognito 보호용 WAF Rule |
| AWS SES / SNS | 이메일/SMS 발송 백엔드 |

---

## 관련 문서

- [[aws-iam-identity-and-access-management-개요|AWS IAM]] - Identity Pool로 IAM 임시 자격 증명 발급
- [[aws-kms-key-management-service-개요|AWS KMS]] - User Pool 데이터 암호화
- [[amazon-rds|Amazon RDS]] - 사용자 프로필 데이터 저장 백엔드
