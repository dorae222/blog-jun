## 개요

AWS Secrets Manager는 애플리케이션에서 사용하는 데이터베이스 자격 증명, API 키, OAuth 토큰 등 민감한 정보(비밀, Secret)를 안전하게 저장, 관리, 교체할 수 있는 서비스입니다.

전통적으로 개발자들은 데이터베이스 비밀번호나 API 키를 환경 변수, 설정 파일, 소스 코드에 하드코딩하는 경우가 많았습니다. 이는 심각한 보안 취약점을 만들어내며, 자격 증명 교체 시 모든 애플리케이션을 수동으로 업데이트해야 하는 운영 부담도 발생합니다.

Secrets Manager는 이러한 문제를 해결합니다.

- **중앙 집중 관리**: 모든 비밀을 한 곳에서 관리합니다.
- **자동 교체**: Lambda 함수를 사용하여 비밀을 자동으로 교체합니다.
- **세밀한 접근 제어**: IAM 정책으로 비밀에 대한 접근을 세밀하게 제어합니다.
- **암호화**: 모든 비밀은 AWS KMS를 사용하여 암호화됩니다.
- **감사**: AWS CloudTrail을 통해 모든 비밀 접근을 감사할 수 있습니다.

## 핵심 기능

### 비밀 생성

```bash
# 키-값 쌍으로 비밀 생성
aws secretsmanager create-secret \
  --name production/database/mysql \
  --description "Production MySQL database credentials" \
  --secret-string '{"username":"admin","password":"MyStr0ngP@ssw0rd!","engine":"mysql","host":"mydb.cluster-abc123.ap-northeast-2.rds.amazonaws.com","port":3306,"dbname":"myapp"}' \
  --tags Key=Environment,Value=Production Key=Service,Value=Database

# 바이너리 비밀 생성 (인증서, 키 파일 등)
aws secretsmanager create-secret \
  --name production/certificates/tls-key \
  --description "TLS private key" \
  --secret-binary fileb://private-key.der

# 랜덤 비밀번호로 비밀 생성
aws secretsmanager get-random-password \
  --password-length 32 \
  --require-each-included-type \
  --exclude-punctuation
```

### 비밀 조회

```bash
# 비밀 값 조회
aws secretsmanager get-secret-value \
  --secret-id production/database/mysql \
  --query 'SecretString' \
  --output text

# 특정 버전의 비밀 조회
aws secretsmanager get-secret-value \
  --secret-id production/database/mysql \
  --version-stage AWSPREVIOUS

# 비밀 메타데이터 조회 (값 제외)
aws secretsmanager describe-secret \
  --secret-id production/database/mysql

# 비밀 목록 조회
aws secretsmanager list-secrets \
  --filters Key=name,Values=production \
  --query 'SecretList[*].{Name:Name,ARN:ARN,LastRotated:LastRotatedDate}' \
  --output table
```

### 비밀 업데이트

```bash
# 비밀 값 업데이트
aws secretsmanager update-secret \
  --secret-id production/database/mysql \
  --secret-string '{"username":"admin","password":"NewStr0ngP@ssw0rd!","engine":"mysql","host":"mydb.cluster-abc123.ap-northeast-2.rds.amazonaws.com","port":3306,"dbname":"myapp"}'

# 비밀 값의 특정 버전에 스테이징 레이블 이동
aws secretsmanager update-secret-version-stage \
  --secret-id production/database/mysql \
  --version-stage AWSCURRENT \
  --move-to-version-id new-version-id \
  --remove-from-version-id old-version-id
```

### 비밀 삭제

```bash
# 비밀 삭제 (복구 대기 기간 7일)
aws secretsmanager delete-secret \
  --secret-id production/database/mysql \
  --recovery-window-in-days 7

# 즉시 삭제 (복구 불가)
aws secretsmanager delete-secret \
  --secret-id production/database/mysql \
  --force-delete-without-recovery

# 삭제 예정 비밀 복구
aws secretsmanager restore-secret \
  --secret-id production/database/mysql
```

### 버전 관리

Secrets Manager는 비밀의 여러 버전을 관리합니다. 각 버전에는 스테이징 레이블이 할당됩니다.

| 스테이징 레이블 | 의미 |
|---------------|------|
| AWSCURRENT | 현재 활성 버전 |
| AWSPREVIOUS | 이전 버전 |
| AWSPENDING | 교체 중인 새 버전 |

이 버전 관리 메커니즘은 비밀 교체 시 안전한 롤백을 가능하게 합니다.

## 아키텍처/동작 원리

### 비밀 자동 교체 (Rotation)

Secrets Manager의 가장 강력한 기능은 자동 교체입니다. Lambda 함수를 사용하여 비밀을 자동으로 교체합니다.

교체 프로세스는 4단계로 이루어집니다.

1. **createSecret**: 새 비밀 값을 생성하고 AWSPENDING 레이블을 부여합니다.
2. **setSecret**: 새 비밀 값을 실제 서비스(예: RDS)에 적용합니다.
3. **testSecret**: 새 비밀 값으로 서비스에 연결을 테스트합니다.
4. **finishSecret**: AWSCURRENT 레이블을 새 버전으로 이동하고, 이전 버전에 AWSPREVIOUS를 부여합니다.

```bash
# RDS MySQL 자동 교체 설정
aws secretsmanager rotate-secret \
  --secret-id production/database/mysql \
  --rotation-lambda-arn arn:aws:lambda:ap-northeast-2:123456789012:function:SecretsManagerRotation \
  --rotation-rules '{"AutomaticallyAfterDays": 30}'

# 즉시 교체 실행
aws secretsmanager rotate-secret \
  --secret-id production/database/mysql
```

### RDS 자동 교체 구성

RDS 데이터베이스 자격 증명의 자동 교체는 가장 일반적인 사용 사례입니다.

```bash
# 1. RDS 비밀 생성 (교체 가능 형식)
aws secretsmanager create-secret \
  --name production/rds/mydb \
  --description "RDS MySQL master credentials" \
  --secret-string '{
    "username": "admin",
    "password": "InitialP@ssw0rd!",
    "engine": "mysql",
    "host": "mydb.cluster-abc123.ap-northeast-2.rds.amazonaws.com",
    "port": 3306,
    "dbname": "myapp",
    "masterarn": ""
  }'

# 2. 교체 Lambda 함수를 위한 VPC 설정 (RDS 접근 필요)
# Lambda가 RDS에 접근할 수 있도록 동일 VPC의 프라이빗 서브넷에 배치

# 3. 교체 활성화 (스케줄 표현식 사용)
aws secretsmanager rotate-secret \
  --secret-id production/rds/mydb \
  --rotation-lambda-arn arn:aws:lambda:ap-northeast-2:123456789012:function:SecretsManagerRDSMySQLRotation \
  --rotation-rules '{"ScheduleExpression": "rate(30 days)"}'
```

### 교체 전략: 단일 사용자 vs 교대 사용자

**단일 사용자 교체(Single User Rotation)**

하나의 데이터베이스 사용자의 비밀번호를 교체합니다. 교체 중 잠깐의 연결 실패가 발생할 수 있습니다.

**교대 사용자 교체(Alternating Users Rotation)**

두 개의 데이터베이스 사용자를 번갈아 사용합니다. 하나를 교체하는 동안 다른 하나로 연결하므로 다운타임이 없습니다.

```bash
# 교대 사용자 교체를 위한 마스터 비밀 설정
aws secretsmanager create-secret \
  --name production/rds/mydb-app \
  --description "Application DB user (alternating rotation)" \
  --secret-string '{
    "username": "appuser",
    "password": "AppP@ssw0rd!",
    "engine": "mysql",
    "host": "mydb.cluster-abc123.ap-northeast-2.rds.amazonaws.com",
    "port": 3306,
    "dbname": "myapp",
    "masterarn": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:production/rds/mydb-master"
  }'
```

### 암호화

Secrets Manager의 모든 비밀은 AWS KMS를 사용하여 암호화됩니다. 기본적으로 AWS 관리형 키(`aws/secretsmanager`)를 사용하지만, 고객 관리형 키(CMK)를 사용할 수도 있습니다.

```bash
# 고객 관리형 KMS 키로 비밀 생성
aws secretsmanager create-secret \
  --name production/api/payment-key \
  --description "Payment API key" \
  --kms-key-id arn:aws:kms:ap-northeast-2:123456789012:key/abc12345 \
  --secret-string '{"api_key":"pk_live_abc123def456"}'
```

크로스 계정 비밀 공유 시에는 고객 관리형 KMS 키를 사용해야 합니다. AWS 관리형 키는 다른 계정에서 사용할 수 없기 때문입니다.

## 실전 활용

### Python 애플리케이션에서 Secrets Manager 사용

```python
import json
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name, region_name='ap-northeast-2'):
    """Secrets Manager에서 비밀을 조회하는 함수"""
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'DecryptionFailureException':
            raise Exception("KMS 키로 복호화할 수 없습니다.")
        elif error_code == 'ResourceNotFoundException':
            raise Exception(f"비밀 '{secret_name}'을(를) 찾을 수 없습니다.")
        elif error_code == 'InvalidRequestException':
            raise Exception("요청이 유효하지 않습니다.")
        else:
            raise e
    
    if 'SecretString' in response:
        return json.loads(response['SecretString'])
    else:
        return response['SecretBinary']

# 사용 예시
db_credentials = get_secret('production/database/mysql')
connection = mysql.connector.connect(
    host=db_credentials['host'],
    user=db_credentials['username'],
    password=db_credentials['password'],
    database=db_credentials['dbname'],
    port=db_credentials['port']
)
```

### 캐싱을 통한 성능 최적화

Secrets Manager API 호출을 최소화하기 위해 AWS에서 제공하는 클라이언트 캐싱 라이브러리를 사용할 수 있습니다.

```python
# AWS Secrets Manager Caching Library 사용
from aws_secretsmanager_caching import SecretCache, SecretCacheConfig

cache_config = SecretCacheConfig(
    max_cache_size=1000,
    exception_retry_delay_base=1,
    exception_retry_growth_factor=2,
    exception_retry_delay_max=3600,
    default_secret_version_stage='AWSCURRENT',
    secret_refresh_interval=3600,  # 1시간마다 갱신
    secret_version_stage_refresh_interval=3600
)

cache = SecretCache(config=cache_config)

# 캐시에서 비밀 조회 (캐시 미스 시 자동으로 API 호출)
secret_string = cache.get_secret_string('production/database/mysql')
db_credentials = json.loads(secret_string)
```

### 크로스 계정 비밀 공유

리소스 정책을 사용하여 다른 AWS 계정과 비밀을 공유할 수 있습니다.

```bash
# 비밀에 리소스 정책 추가
aws secretsmanager put-resource-policy \
  --secret-id production/shared/api-key \
  --resource-policy '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "AWS": "arn:aws:iam::987654321098:role/CrossAccountSecretReader"
        },
        "Action": [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ],
        "Resource": "*"
      }
    ]
  }'
```

### ECS/EKS에서 Secrets Manager 사용

ECS 태스크 정의에서 Secrets Manager 비밀을 환경 변수로 주입할 수 있습니다.

```json
{
  "containerDefinitions": [
    {
      "name": "my-app",
      "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/my-app:latest",
      "secrets": [
        {
          "name": "DB_USERNAME",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:production/database/mysql:username::"
        },
        {
          "name": "DB_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:production/database/mysql:password::"
        }
      ]
    }
  ]
}
```

EKS에서는 AWS Secrets and Configuration Provider (ASCP)를 사용합니다.

```yaml
# SecretProviderClass 정의
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: aws-secrets
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "production/database/mysql"
        objectType: "secretsmanager"
        jmesPath:
          - path: username
            objectAlias: db_username
          - path: password
            objectAlias: db_password
```

## 모범 사례/보안

### 비밀 명명 규칙

일관된 명명 규칙을 사용하여 비밀을 체계적으로 관리합니다.

```
{environment}/{service-type}/{service-name}

예시:
- production/database/mysql-main
- staging/api/payment-gateway
- production/certificates/tls-wildcard
- shared/integrations/slack-webhook
```

### IAM 정책 설계

최소 권한 원칙에 따라 IAM 정책을 설계합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": "arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:production/database/*",
      "Condition": {
        "StringEquals": {
          "secretsmanager:VersionStage": "AWSCURRENT"
        }
      }
    }
  ]
}
```

### 핵심 보안 권장 사항

1. **자동 교체 활성화**: 최소 90일마다 비밀을 교체합니다.
2. **VPC 엔드포인트 사용**: 프라이빗 서브넷에서 인터넷을 거치지 않고 Secrets Manager에 접근합니다.
3. **CloudTrail 모니터링**: 비밀 접근에 대한 감사 로그를 항상 활성화합니다.
4. **리소스 정책 활용**: 크로스 계정 접근 시 리소스 정책을 사용합니다.
5. **태그 기반 접근 제어**: ABAC(Attribute-Based Access Control)를 활용합니다.

```bash
# Secrets Manager VPC 엔드포인트 생성
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0a1b2c3d4e5f6g7h8 \
  --service-name com.amazonaws.ap-northeast-2.secretsmanager \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-private-a subnet-private-c \
  --security-group-ids sg-0a1b2c3d4e5f6g7h8 \
  --private-dns-enabled
```

## 관련 서비스 비교

### Secrets Manager vs Systems Manager Parameter Store

| 항목 | Secrets Manager | Parameter Store |
|------|----------------|------------------|
| 자동 교체 | 내장 지원 (Lambda) | 미지원 (직접 구현 필요) |
| 비용 | $0.40/비밀/월 + API 호출 | 무료 (Standard) / $0.05 (Advanced) |
| 크로스 계정 공유 | 리소스 정책 지원 | 미지원 |
| 생성/관리 API 호출 | $0.05/만 건 | 무료 (Standard) |
| 암호화 | KMS 필수 (자동) | KMS 선택적 |
| 크기 제한 | 64KB | 4KB (Standard) / 8KB (Advanced) |
| 버전 관리 | 스테이징 레이블 기반 | 자동 버전 번호 |
| RDS 통합 교체 | 내장 Lambda 템플릿 | 미지원 |

**선택 기준**: 자동 교체가 필요하거나 RDS 자격 증명을 관리하는 경우 Secrets Manager를, 단순 설정값 저장이나 비용이 중요한 경우 Parameter Store를 선택합니다.

### Secrets Manager vs HashiCorp Vault

| 항목 | Secrets Manager | HashiCorp Vault |
|------|----------------|------------------|
| 관리 | 완전 관리형 | 자체 관리 또는 HCP |
| 멀티 클라우드 | AWS 전용 | 멀티 클라우드 |
| 동적 비밀 | Lambda 교체 | 네이티브 동적 비밀 |
| PKI | ACM Private CA 연동 | 내장 PKI 엔진 |
| 비용 | 사용량 기반 | 라이선스 또는 운영 비용 |

## 요약

AWS Secrets Manager는 애플리케이션의 민감한 정보를 안전하게 관리하는 핵심 서비스입니다.

1. **데이터베이스 자격 증명, API 키, 토큰** 등 모든 유형의 비밀을 안전하게 저장합니다.
2. **자동 교체 기능**을 통해 비밀을 정기적으로 교체할 수 있으며, RDS 교체용 Lambda 템플릿이 기본 제공됩니다.
3. **버전 관리**를 통해 교체 중 문제 발생 시 안전하게 롤백할 수 있습니다.
4. **ECS, EKS, Lambda** 등 AWS 컴퓨팅 서비스와 원활하게 통합됩니다.
5. **크로스 계정 공유**를 리소스 정책을 통해 지원합니다.
6. **캐싱 라이브러리**를 사용하여 API 호출 비용과 지연 시간을 최적화할 수 있습니다.
7. 단순 설정값 관리에는 **Parameter Store**가 비용 효율적이며, 자격 증명 관리에는 **Secrets Manager**가 적합합니다.