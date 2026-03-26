## 개요

AWS Secrets Manager를 사용하다 보면 여러 개의 비밀을 한 번에 조회해야 하는 상황이 자주 발생합니다. 마이크로서비스 환경에서 하나의 서비스가 데이터베이스 자격 증명, API 키, 외부 서비스 토큰 등 여러 비밀을 필요로 하는 것은 매우 일반적인 패턴입니다.

이때 각 비밀을 개별적으로 `GetSecretValue` API를 호출하여 조회하면, API 호출 수가 증가하고, 애플리케이션 시작 시간이 길어지며, 비용도 증가합니다.

그렇다면 AWS Secrets Manager에 `BatchGetSecretValue` API가 존재할까요? 결론부터 말하면, 존재합니다. AWS는 2023년 11월에 `BatchGetSecretValue` API를 정식으로 출시했습니다. 이 API를 사용하면 최대 20개의 비밀을 단일 API 호출로 조회할 수 있습니다.

### BatchGetSecretValue가 필요한 이유

| 시나리오 | 개별 조회 | 배치 조회 |
|---------|----------|----------|
| 10개 비밀 조회 | 10회 API 호출 | 1회 API 호출 |
| 네트워크 왕복 | 10회 | 1회 |
| 지연 시간 | ~500ms (10 x ~50ms) | ~80ms |
| API 비용 | 10건 과금 | 1건 과금 |

특히 Lambda 함수의 콜드 스타트 시간을 줄이거나, ECS 태스크의 시작 시간을 최적화하는 데 큰 효과가 있습니다.

## 핵심 기능

### BatchGetSecretValue API 사용법

```bash
# SecretId 목록으로 배치 조회
aws secretsmanager batch-get-secret-value \
  --secret-id-list \
    production/database/mysql \
    production/api/payment \
    production/api/notification \
    production/cache/redis

# 필터를 사용한 배치 조회
aws secretsmanager batch-get-secret-value \
  --filters Key=name,Values=production/database

# 태그 기반 필터로 배치 조회
aws secretsmanager batch-get-secret-value \
  --filters Key=tag-key,Values=Environment Key=tag-value,Values=Production
```

### 응답 구조

`BatchGetSecretValue`의 응답은 다음과 같은 구조를 가집니다.

```json
{
  "SecretValues": [
    {
      "ARN": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:production/database/mysql-AbCdEf",
      "Name": "production/database/mysql",
      "VersionId": "abc12345-1234-1234-1234-abc123456789",
      "SecretString": "{\"username\":\"admin\",\"password\":\"MyStr0ngP@ssw0rd!\",\"host\":\"mydb.abc123.ap-northeast-2.rds.amazonaws.com\",\"port\":3306}",
      "VersionStages": ["AWSCURRENT"],
      "CreatedDate": "2024-01-15T09:30:00Z"
    },
    {
      "ARN": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:production/api/payment-GhIjKl",
      "Name": "production/api/payment",
      "VersionId": "def67890-5678-5678-5678-def678901234",
      "SecretString": "{\"api_key\":\"pk_live_abc123\"}",
      "VersionStages": ["AWSCURRENT"],
      "CreatedDate": "2024-01-10T14:00:00Z"
    }
  ],
  "Errors": [
    {
      "SecretId": "production/api/notification",
      "ErrorCode": "ResourceNotFoundException",
      "Message": "Secrets Manager can't find the specified secret."
    }
  ]
}
```

중요한 점은 `Errors` 배열입니다. 일부 비밀 조회가 실패하더라도 나머지 비밀은 정상적으로 반환됩니다. 따라서 애플리케이션에서는 반드시 `Errors` 배열을 확인하고 적절히 처리해야 합니다.

### 제한 사항

| 항목 | 제한 |
|------|------|
| 한 번에 조회 가능한 최대 비밀 수 | 20개 |
| SecretId 목록과 필터 동시 사용 | 불가 |
| 바이너리 비밀 | 지원 |
| 특정 버전 지정 | 미지원 (AWSCURRENT만 반환) |
| 크로스 리전 조회 | 미지원 |

## 아키텍처/동작 원리

### 내부 동작 원리

`BatchGetSecretValue`는 내부적으로 여러 `GetSecretValue` 호출을 병렬로 실행하고 결과를 집계하여 반환합니다. 하지만 사용자 입장에서는 단일 API 호출로 처리되므로 다음과 같은 이점이 있습니다.

1. **네트워크 왕복 최소화**: 단일 HTTP 요청으로 여러 비밀을 받아옵니다.
2. **원자적 응답**: 모든 결과가 하나의 응답에 포함됩니다.
3. **부분 실패 처리**: 일부 실패해도 성공한 비밀은 반환됩니다.

### 비용 구조

`BatchGetSecretValue` API 호출 비용은 다음과 같습니다.

- 각 비밀의 조회는 개별 API 호출로 과금됩니다.
- 즉, 10개의 비밀을 배치 조회하면 10건의 API 호출 비용이 발생합니다.
- 비용 절감 효과는 네트워크 지연 시간 감소와 코드 복잡도 감소에 있습니다.

그러나 실질적인 비용 절감을 위해서는 클라이언트 캐싱을 병행하는 것이 중요합니다.

### 필터 기반 조회 동작

필터를 사용하면 비밀 이름이나 태그를 기준으로 동적으로 비밀을 조회할 수 있습니다. 이는 비밀이 추가되거나 이름이 변경될 때 코드를 수정할 필요가 없다는 장점이 있습니다.

```bash
# 이름 프리픽스로 필터링
aws secretsmanager batch-get-secret-value \
  --filters Key=name,Values=production/

# 태그 기반 필터링
aws secretsmanager batch-get-secret-value \
  --filters Key=tag-key,Values=Service Key=tag-value,Values=PaymentAPI

# 설명 기반 필터링
aws secretsmanager batch-get-secret-value \
  --filters Key=description,Values="database credentials"
```

필터 사용 시 주의할 점은 필터 조건에 매칭되는 비밀이 20개를 초과하면 `NextToken`을 사용한 페이지네이션이 필요하다는 것입니다.

```bash
# 페이지네이션 처리
NEXT_TOKEN=""
while true; do
  if [ -z "$NEXT_TOKEN" ]; then
    RESPONSE=$(aws secretsmanager batch-get-secret-value \
      --filters Key=name,Values=production/ \
      --max-results 20 \
      --output json)
  else
    RESPONSE=$(aws secretsmanager batch-get-secret-value \
      --filters Key=name,Values=production/ \
      --max-results 20 \
      --next-token "$NEXT_TOKEN" \
      --output json)
  fi
  
  echo "$RESPONSE" | python3 -c "import sys,json; data=json.load(sys.stdin); [print(s['Name']) for s in data.get('SecretValues', [])]"
  
  NEXT_TOKEN=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('NextToken', ''))" 2>/dev/null)
  
  if [ -z "$NEXT_TOKEN" ]; then
    break
  fi
done
```

## 실전 활용

### Python에서 BatchGetSecretValue 사용

```python
import json
import boto3
from typing import Dict, List, Optional

class SecretsLoader:
    """BatchGetSecretValue를 활용한 대량 비밀 로더"""
    
    def __init__(self, region_name: str = 'ap-northeast-2'):
        self.client = boto3.client('secretsmanager', region_name=region_name)
    
    def load_secrets_by_ids(self, secret_ids: List[str]) -> Dict[str, dict]:
        """비밀 ID 목록으로 배치 조회"""
        results = {}
        errors = []
        
        # 20개씩 분할하여 배치 조회
        for i in range(0, len(secret_ids), 20):
            batch = secret_ids[i:i+20]
            response = self.client.batch_get_secret_value(
                SecretIdList=batch
            )
            
            for secret in response.get('SecretValues', []):
                name = secret['Name']
                if 'SecretString' in secret:
                    try:
                        results[name] = json.loads(secret['SecretString'])
                    except json.JSONDecodeError:
                        results[name] = secret['SecretString']
                else:
                    results[name] = secret['SecretBinary']
            
            for error in response.get('Errors', []):
                errors.append({
                    'SecretId': error['SecretId'],
                    'ErrorCode': error['ErrorCode'],
                    'Message': error['Message']
                })
        
        if errors:
            print(f"[WARNING] {len(errors)}개 비밀 조회 실패:")
            for err in errors:
                print(f"  - {err['SecretId']}: {err['ErrorCode']}")
        
        return results
    
    def load_secrets_by_filter(self, name_prefix: str) -> Dict[str, dict]:
        """이름 프리픽스로 필터링하여 배치 조회"""
        results = {}
        next_token = None
        
        while True:
            kwargs = {
                'Filters': [{'Key': 'name', 'Values': [name_prefix]}],
                'MaxResults': 20
            }
            if next_token:
                kwargs['NextToken'] = next_token
            
            response = self.client.batch_get_secret_value(**kwargs)
            
            for secret in response.get('SecretValues', []):
                name = secret['Name']
                if 'SecretString' in secret:
                    try:
                        results[name] = json.loads(secret['SecretString'])
                    except json.JSONDecodeError:
                        results[name] = secret['SecretString']
            
            next_token = response.get('NextToken')
            if not next_token:
                break
        
        return results

# 사용 예시
loader = SecretsLoader()

# 개별 비밀 ID로 조회
secrets = loader.load_secrets_by_ids([
    'production/database/mysql',
    'production/api/payment',
    'production/api/notification',
    'production/cache/redis'
])

db_config = secrets['production/database/mysql']
payment_key = secrets['production/api/payment']['api_key']

# 프리픽스로 조회
all_prod_secrets = loader.load_secrets_by_filter('production/')
```

### Lambda 콜드 스타트 최적화

Lambda 함수에서 여러 비밀을 사용하는 경우, `BatchGetSecretValue`를 핸들러 외부에서 호출하여 콜드 스타트 시간을 최적화할 수 있습니다.

```python
import json
import boto3

# 핸들러 외부에서 비밀 로드 (콜드 스타트 시 1회 실행)
secretsmanager = boto3.client('secretsmanager')

response = secretsmanager.batch_get_secret_value(
    SecretIdList=[
        'production/database/mysql',
        'production/api/external-service',
        'production/auth/jwt-secret'
    ]
)

SECRETS = {}
for secret in response.get('SecretValues', []):
    SECRETS[secret['Name']] = json.loads(secret['SecretString'])

def lambda_handler(event, context):
    # 이미 로드된 비밀 사용
    db_host = SECRETS['production/database/mysql']['host']
    api_key = SECRETS['production/api/external-service']['api_key']
    jwt_secret = SECRETS['production/auth/jwt-secret']['secret']
    
    # 비즈니스 로직 수행
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Success'})
    }
```

### Django 설정에서 활용

```python
# settings.py
import json
import boto3

def load_secrets():
    client = boto3.client('secretsmanager', region_name='ap-northeast-2')
    response = client.batch_get_secret_value(
        SecretIdList=[
            'production/django/database',
            'production/django/secret-key',
            'production/django/email'
        ]
    )
    secrets = {}
    for s in response.get('SecretValues', []):
        secrets[s['Name']] = json.loads(s['SecretString'])
    return secrets

_secrets = load_secrets()

SECRET_KEY = _secrets['production/django/secret-key']['key']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': _secrets['production/django/database']['dbname'],
        'USER': _secrets['production/django/database']['username'],
        'PASSWORD': _secrets['production/django/database']['password'],
        'HOST': _secrets['production/django/database']['host'],
        'PORT': _secrets['production/django/database']['port'],
    }
}

EMAIL_HOST_USER = _secrets['production/django/email']['username']
EMAIL_HOST_PASSWORD = _secrets['production/django/email']['password']
```

### IAM 정책 설정

`BatchGetSecretValue`를 사용하기 위한 IAM 정책입니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:BatchGetSecretValue",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:production/*"
    },
    {
      "Effect": "Allow",
      "Action": "secretsmanager:ListSecrets",
      "Resource": "*"
    }
  ]
}
```

`ListSecrets` 권한은 필터 기반 조회 시 필요합니다. SecretId 목록을 직접 지정하는 경우에는 `GetSecretValue` 권한만 있으면 됩니다.

## 모범 사례/보안

### 성능 최적화 전략

1. **캐싱과 병행**: `BatchGetSecretValue`로 초기 로드하고, 이후에는 캐시에서 조회합니다.
2. **필터 활용**: 비밀 이름에 일관된 프리픽스를 사용하여 필터 기반 조회를 활용합니다.
3. **비동기 조회**: 비동기 환경에서는 aioboto3를 사용하여 논블로킹 조회를 수행합니다.
4. **적절한 배치 크기**: 20개 이상의 비밀을 조회하는 경우 병렬 배치 호출을 고려합니다.

### 오류 처리 전략

```python
import logging

logger = logging.getLogger(__name__)

def safe_batch_load(secret_ids: list, required_secrets: list = None):
    """안전한 배치 비밀 로드 (필수 비밀 검증 포함)"""
    client = boto3.client('secretsmanager')
    
    try:
        response = client.batch_get_secret_value(SecretIdList=secret_ids)
    except client.exceptions.ClientError as e:
        logger.error(f"BatchGetSecretValue 호출 실패: {e}")
        raise
    
    secrets = {}
    for s in response.get('SecretValues', []):
        secrets[s['Name']] = json.loads(s['SecretString'])
    
    # 오류 로깅
    for err in response.get('Errors', []):
        logger.warning(f"비밀 조회 실패: {err['SecretId']} - {err['ErrorCode']}")
    
    # 필수 비밀 검증
    if required_secrets:
        missing = [s for s in required_secrets if s not in secrets]
        if missing:
            raise RuntimeError(f"필수 비밀 누락: {missing}")
    
    return secrets
```

### 보안 권장 사항

1. **최소 권한**: 필요한 비밀에만 접근 권한을 부여합니다.
2. **VPC 엔드포인트**: 프라이빗 네트워크에서 Secrets Manager에 접근합니다.
3. **메모리 보안**: 비밀을 로드한 후 불필요하게 로깅하거나 직렬화하지 않습니다.
4. **정기적 교체**: `BatchGetSecretValue`는 항상 AWSCURRENT 버전을 반환하므로, 자동 교체와 자연스럽게 연동됩니다.

## 관련 서비스 비교

### GetSecretValue vs BatchGetSecretValue

| 항목 | GetSecretValue | BatchGetSecretValue |
|------|---------------|---------------------|
| 조회 단위 | 1개 | 최대 20개 |
| 버전 지정 | 가능 (VersionId, VersionStage) | 불가 (AWSCURRENT만) |
| 필터 지원 | 불가 | 가능 (이름, 태그, 설명) |
| 부분 실패 처리 | N/A | Errors 배열로 반환 |
| 네트워크 왕복 | 비밀 수만큼 | 1회 (20개 이하) |
| 출시 시기 | 초기 | 2023년 11월 |

### 다른 AWS 서비스의 배치 API 비교

| 서비스 | 배치 API | 최대 배치 크기 |
|--------|---------|---------------|
| Secrets Manager | BatchGetSecretValue | 20 |
| DynamoDB | BatchGetItem | 100 |
| SQS | ReceiveMessage | 10 |
| S3 | (없음, Select/Multipart 활용) | - |
| SSM Parameter Store | GetParameters | 10 |

## 요약

AWS Secrets Manager의 `BatchGetSecretValue` API는 대량 비밀 조회를 최적화하는 핵심 기능입니다.

1. **2023년 11월 정식 출시**되었으며, 최대 **20개 비밀**을 단일 API 호출로 조회할 수 있습니다.
2. **SecretId 목록** 또는 **필터**(이름, 태그, 설명)를 사용하여 비밀을 지정할 수 있습니다.
3. **부분 실패 처리**가 가능하여, 일부 비밀 조회가 실패해도 나머지는 정상 반환됩니다.
4. **Lambda 콜드 스타트**, **ECS 태스크 시작**, **Django 설정 로드** 등 다양한 시나리오에서 성능을 개선합니다.
5. 비용 절감보다는 **네트워크 지연 시간 감소**와 **코드 간소화**에 더 큰 가치가 있습니다.
6. **클라이언트 캐싱**과 병행하여 사용하면 최적의 성능을 달성할 수 있습니다.
7. IAM 정책에서 `BatchGetSecretValue` 액션을 별도로 허용해야 하며, 필터 사용 시 `ListSecrets` 권한도 필요합니다.