<!-- infographic-hero -->
![AWS KMS 핵심 요약](figures/infographic.svg)

*Figure: AWS KMS 한 장 요약 인포그래픽*

# AWS KMS (Key Management Service) 개요

## 개요

AWS KMS(Key Management Service)는 데이터 암호화에 사용되는 암호화 키를 중앙에서 생성, 관리, 사용, 감사할 수 있는 완전 관리형 서비스입니다. 2014년 출시되었으며, AWS의 거의 모든 데이터 서비스(S3, EBS, RDS, DynamoDB, Lambda, Secrets Manager 등)와 통합되어 클라우드 암호화의 표준이 되었습니다.

KMS의 가장 큰 특징은 **FIPS 140-2 Level 3 인증**을 받은 HSM(Hardware Security Module) 위에서 동작한다는 점입니다. 마스터 키는 평문 형태로 HSM 외부로 절대 노출되지 않으며, 모든 암호화/복호화 연산은 HSM 내부에서 수행됩니다. 이 덕분에 KMS는 규제가 엄격한 금융, 의료, 정부 기관에서도 안심하고 사용할 수 있습니다.

KMS는 다음과 같은 핵심 가치를 제공합니다.

- **중앙화된 키 관리**: 수십 개의 서비스에서 사용하는 키를 한 곳에서 관리
- **세분화된 접근 제어**: Key Policy + IAM Policy + Grant의 3중 인가 모델
- **자동 키 회전**: 키 자체와 데이터를 분리한 안전한 회전
- **감사 로깅**: 모든 키 사용이 CloudTrail에 기록
- **고가용성**: 리전 내 다중 AZ로 자동 복제

KMS는 직접 데이터를 암호화하기보다는, **데이터 키를 보호하는 마스터 키**의 역할에 집중합니다. 이를 Envelope Encryption이라고 하며, 후술합니다.

---

## 핵심 기능

### 1. KMS Key의 3가지 종류

KMS Key(구 CMK, Customer Master Key)는 소유권에 따라 세 가지로 구분됩니다.

| 종류 | 별칭 형식 | 특징 | 비용 |
|------|----------|------|------|
| Customer Managed Key (CMK) | 사용자 정의 | 사용자가 직접 생성/관리/회전 | 키당 월 $1 + API 비용 |
| AWS Managed Key | `aws/<service>` | AWS 서비스가 자동 생성/관리 | 무료 (API 비용만) |
| AWS Owned Key | (보이지 않음) | AWS가 다중 계정에 걸쳐 공유 | 완전 무료 |

CMK는 가장 강력한 제어를 제공하지만 비용이 발생합니다. AWS Managed Key는 `aws/s3`, `aws/rds`, `aws/secretsmanager` 같은 형태로 자동 생성되며, 별도 관리 없이 사용할 수 있습니다. 단, AWS Managed Key는 Key Policy 수정이 불가하고 자동 회전 주기(1년)도 변경할 수 없습니다.

```bash
# CMK 생성 (대칭 키)
aws kms create-key \
  --description "Production application encryption key" \
  --key-usage ENCRYPT_DECRYPT \
  --customer-master-key-spec SYMMETRIC_DEFAULT \
  --tags TagKey=Environment,TagValue=production

# 별칭(Alias) 생성
aws kms create-alias \
  --alias-name alias/my-app-key \
  --target-key-id 1234abcd-12ab-34cd-56ef-1234567890ab
```

### 2. 키 사양(Key Spec)

KMS는 다양한 암호화 알고리즘을 지원합니다.

**대칭 키(Symmetric)**

- `SYMMETRIC_DEFAULT`: AES-256-GCM. 가장 일반적이며 데이터 암호화에 사용.
- HMAC: `HMAC_224`, `HMAC_256`, `HMAC_384`, `HMAC_512`. 메시지 무결성 검증.

**비대칭 키(Asymmetric)**

- RSA: `RSA_2048`, `RSA_3072`, `RSA_4096`. 암호화/복호화 또는 서명/검증.
- ECC: `ECC_NIST_P256`, `ECC_NIST_P384`, `ECC_NIST_P521`, `ECC_SECG_P256K1`. 디지털 서명.
- SM2: 중국 국가 표준 알고리즘. 중국 리전에서만 사용 가능.

```bash
# RSA 비대칭 키 생성 (서명용)
aws kms create-key \
  --customer-master-key-spec RSA_2048 \
  --key-usage SIGN_VERIFY \
  --description "Code signing key"

# 데이터 서명
aws kms sign \
  --key-id alias/code-signing-key \
  --message fileb://document.txt \
  --signing-algorithm RSASSA_PSS_SHA_256
```

### 3. Envelope Encryption

KMS의 핵심 설계 원칙은 Envelope Encryption입니다. KMS는 직접 대용량 데이터를 암호화하지 않고, 데이터 키를 암호화하는 데 집중합니다.

**Envelope Encryption 흐름**

1. 애플리케이션이 KMS에 `GenerateDataKey` API 호출
2. KMS는 평문 Data Key + 암호화된 Data Key 두 가지를 반환
3. 애플리케이션은 평문 Data Key로 데이터를 AES 암호화
4. 평문 Data Key는 즉시 메모리에서 폐기
5. 암호화된 Data Key + 암호화된 데이터를 함께 저장

복호화 시에는 KMS에 암호화된 Data Key를 보내 평문을 받아 복호화합니다.

```python
import boto3
from cryptography.fernet import Fernet

kms = boto3.client('kms')

# 1. Data Key 생성 (평문 + 암호화된 형태 동시 반환)
response = kms.generate_data_key(
    KeyId='alias/my-app-key',
    KeySpec='AES_256'
)
plaintext_key = response['Plaintext']
encrypted_key = response['CiphertextBlob']

# 2. 평문 키로 데이터 암호화 (로컬에서 수행)
fernet = Fernet(base64.urlsafe_b64encode(plaintext_key))
encrypted_data = fernet.encrypt(b"sensitive data")

# 3. 평문 키 즉시 폐기, 암호화된 키만 저장
del plaintext_key
store(encrypted_data, encrypted_key)
```

이 방식의 장점은 다음과 같습니다.

- **성능**: 대용량 데이터를 KMS API로 전송할 필요 없음 (KMS는 4KB까지만 직접 암호화 지원)
- **비용**: API 호출 횟수 최소화
- **확장성**: Data Key는 무제한 생성 가능

S3, EBS, DynamoDB 등 모든 AWS 서비스 통합은 내부적으로 Envelope Encryption을 사용합니다.

### 4. Key Policy + IAM Policy + Grant

KMS는 3중 인가 모델로 매우 세밀한 접근 제어를 제공합니다.

**Key Policy (필수)**

각 KMS Key에 직접 부착되는 Resource-based Policy. 비어있을 수 없으며, 최소 한 명의 Principal에게 키 관리 권한을 부여해야 합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EnableIAMUserPermissions",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "AllowAppRoleToUseKey",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::123456789012:role/AppRole"},
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:GenerateDataKey",
        "kms:DescribeKey"
      ],
      "Resource": "*"
    }
  ]
}
```

**IAM Policy**

IAM User/Role에 부착되는 Identity-based Policy. Key Policy가 IAM Policy를 위임(`"AWS": "...:root"`)한 경우에만 IAM Policy로 권한을 부여할 수 있습니다.

**Grant**

임시적이고 세분화된 권한 부여 메커니즘. 주로 AWS 서비스가 사용자 대신 키를 사용해야 할 때 사용됩니다(예: EBS 볼륨 마운트 시).

```bash
# Grant 생성
aws kms create-grant \
  --key-id alias/my-app-key \
  --grantee-principal arn:aws:iam::123456789012:role/EBSMountRole \
  --operations Encrypt Decrypt GenerateDataKey \
  --constraints EncryptionContextSubset={Department=Finance}
```

### 5. 키 회전(Key Rotation)

키 회전은 보안의 기본이지만, 회전 주기 동안 이미 암호화된 데이터를 어떻게 처리할지가 중요합니다.

**자동 회전 (Automatic Rotation)**

- AWS Managed Key: 1년 자동 회전 (변경 불가)
- Customer Managed Key: 옵션 활성화 시 1~2,557일(약 7년) 사이 선택 가능

자동 회전은 KMS Key의 백킹 키(Backing Key)만 새로 생성하며, Key ID와 ARN은 유지됩니다. 따라서 애플리케이션 코드 변경이 필요 없습니다. 이전 백킹 키는 KMS 내부에 보관되어 과거 데이터의 복호화에 사용됩니다.

```bash
# 자동 회전 활성화 (1년 주기)
aws kms enable-key-rotation \
  --key-id alias/my-app-key \
  --rotation-period-in-days 365

# 회전 상태 확인
aws kms get-key-rotation-status --key-id alias/my-app-key
```

**수동 회전 (Manual Rotation)**

새로운 KMS Key를 생성하고 별칭(Alias)을 새 키로 가리키게 하는 방식. 키 자체가 변경되므로 더 강력한 보안을 제공하지만, 데이터 재암호화가 필요할 수 있습니다.

비대칭 키와 HMAC 키는 자동 회전을 지원하지 않습니다.

### 6. KMS Multi-Region Keys

Multi-Region Key는 동일한 키 자료(Key Material)를 여러 리전에 복제하여, Cross-Region 워크로드에서 데이터 이동 시 재암호화 없이 사용할 수 있게 합니다. 2021년 출시되었습니다.

- 모든 복제본은 동일한 Key ID를 가집니다 (`mrk-`로 시작).
- 각 복제본은 독립적인 Key Policy를 가질 수 있습니다.
- 글로벌 DynamoDB Table, Cross-Region S3 Replication에 유용합니다.

```bash
# Primary 리전에서 Multi-Region Key 생성
aws kms create-key \
  --multi-region \
  --description "Multi-region key for global app" \
  --region us-east-1

# 다른 리전으로 복제
aws kms replicate-key \
  --key-id mrk-1234abcd5678efgh \
  --replica-region ap-northeast-2
```

---

## 아키텍처

### KMS HSM 아키텍처

```
[애플리케이션]
      |
      | API 호출 (Encrypt/Decrypt/GenerateDataKey)
      v
[KMS API 엔드포인트 (TLS 1.2+)]
      |
      v
[KMS Service Layer]
      | Key ID -> Backing Key 매핑
      v
[FIPS 140-2 Level 3 HSM Cluster]
      | 평문 키는 HSM 외부로 절대 노출되지 않음
      v
[암호화된 결과 반환]
```

KMS HSM은 다음 보호를 제공합니다.

- 물리적 변조 감지 시 키 자동 삭제
- 다중 AZ 클러스터링으로 가용성 보장
- 모든 연산은 HSM 내부에서 수행
- 외부 키 가져오기(Import) 시에도 HSM 내부에서 래핑

### CloudHSM과의 차이

| 항목 | KMS | CloudHSM |
|------|-----|----------|
| 모델 | 멀티 테넌트 (AWS 관리) | 단일 테넌트 (사용자 전용) |
| 인증 | FIPS 140-2 Level 3 | FIPS 140-2 Level 3 |
| 키 제어 | AWS와 공유 | 완전 사용자 제어 |
| API | KMS API | PKCS#11, JCE, OpenSSL |
| 가격 | 키당 $1/월 + API | HSM당 시간당 $1.45 (~$1,000/월) |
| 사용 사례 | 일반 AWS 서비스 통합 | 외부 PKI, 디지털 서명, 규제 요구사항 |

### Custom Key Store

Custom Key Store는 KMS의 사용성과 CloudHSM의 키 격리를 결합한 하이브리드 옵션입니다.

- KMS API로 키를 사용하지만, 실제 키 자료는 사용자 소유 CloudHSM 클러스터에 저장됩니다.
- 2023년부터 외부 키 관리자(External Key Store, XKS)도 지원합니다. 온프레미스 HSM이나 타사 KMS와 연동 가능합니다.

```bash
# Custom Key Store 생성
aws kms create-custom-key-store \
  --custom-key-store-name my-cloudhsm-store \
  --cloud-hsm-cluster-id cluster-1a23b456cde \
  --trust-anchor-certificate file://customerCA.crt \
  --key-store-password 'YourSecurePassword'
```

---

## 실전 사용

### 1. S3 객체 암호화

S3는 SSE-KMS(Server-Side Encryption with KMS)를 통해 KMS와 통합됩니다.

```bash
# 버킷 기본 암호화 설정
aws s3api put-bucket-encryption \
  --bucket my-secure-bucket \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "alias/my-app-key"
      },
      "BucketKeyEnabled": true
    }]
  }'
```

`BucketKeyEnabled: true`는 버킷 단위로 Data Key를 캐싱하여 KMS API 호출을 최대 99% 줄여줍니다. 비용 절감에 매우 효과적입니다.

### 2. EBS 볼륨 암호화

```bash
# 리전 기본 EBS 암호화 활성화
aws ec2 enable-ebs-encryption-by-default --region ap-northeast-2
aws ec2 modify-ebs-default-kms-key-id \
  --kms-key-id alias/my-ebs-key \
  --region ap-northeast-2
```

### 3. Secrets Manager와 통합

Secrets Manager는 시크릿을 KMS로 암호화하여 저장합니다.

```bash
# 커스텀 KMS 키로 시크릿 생성
aws secretsmanager create-secret \
  --name prod/db/password \
  --secret-string '{"username":"admin","password":"S3cur3P@ss"}' \
  --kms-key-id alias/secrets-key
```

### 4. Cross-Account Key Sharing

다른 AWS 계정과 키를 공유하려면 Key Policy에 외부 계정의 Principal을 추가합니다.

```json
{
  "Sid": "AllowExternalAccountUsage",
  "Effect": "Allow",
  "Principal": {"AWS": "arn:aws:iam::987654321098:role/CrossAccountRole"},
  "Action": ["kms:Decrypt", "kms:DescribeKey"],
  "Resource": "*"
}
```

또한 외부 계정의 IAM Policy에서도 해당 KMS Key ARN을 명시적으로 허용해야 합니다.

### 5. Encryption Context

Encryption Context는 추가적인 인증 데이터(AAD)로, 암호화 시 함께 전달되어 복호화 시 동일한 값이 제공되어야 합니다. 데이터 무결성과 의도된 사용 범위를 보장합니다.

```python
# 암호화 시 컨텍스트 지정
kms.encrypt(
    KeyId='alias/my-app-key',
    Plaintext=b'sensitive data',
    EncryptionContext={
        'Department': 'Finance',
        'DataType': 'Salary'
    }
)

# 복호화 시 동일한 컨텍스트 필요
kms.decrypt(
    CiphertextBlob=encrypted,
    EncryptionContext={
        'Department': 'Finance',
        'DataType': 'Salary'
    }
)
```

Key Policy의 Condition으로 특정 Encryption Context만 허용할 수도 있습니다.

---

## 가격/한도

### 가격 (us-east-1 기준)

| 항목 | 가격 |
|------|------|
| Customer Managed Key | 키당 월 $1 |
| AWS Managed Key | 무료 |
| Symmetric API 호출 | 10,000건당 $0.03 |
| Asymmetric API 호출 (RSA 2048) | 10,000건당 $0.15 |
| Asymmetric API 호출 (RSA 4096+) | 10,000건당 $12 |
| Multi-Region Key | 리전당 월 $1 |
| Custom Key Store | KMS 비용 + CloudHSM 비용 |

### 주요 한도

| 항목 | 기본 한도 |
|------|----------|
| 계정/리전당 KMS Key 수 | 100,000 |
| 키당 별칭(Alias) 수 | 50 |
| 키당 Grant 수 | 50,000 |
| API 요청 한도 (CryptographicOperation) | 5,500~30,000 RPS (리전별 다름) |
| 직접 암호화 가능한 평문 크기 | 4KB |
| GenerateDataKey 최대 키 크기 | 1,024 바이트 |

API 한도는 리전마다 다르며, AWS 지원에 요청하여 증가시킬 수 있습니다.

---

## Best Practice

### 1. AWS Managed Key 우선 사용

비용 절감과 관리 부담 경감을 위해 가능한 경우 AWS Managed Key(`aws/<service>`)를 사용합니다. CMK는 다음 경우에만 사용합니다.

- 키 정책을 세분화해야 할 때
- 자동 회전 주기를 변경해야 할 때
- 다른 AWS 계정과 키를 공유해야 할 때
- Cross-Region 복제가 필요할 때 (Multi-Region Key)

### 2. 별칭(Alias) 사용 강제

Key ID(`1234abcd-12ab-34cd-56ef-1234567890ab`) 대신 별칭(`alias/my-app-key`)을 사용하여 코드 가독성을 높이고, 키 교체 시 코드 변경 없이 별칭만 다시 가리키도록 합니다.

### 3. Key Policy 최소 권한

Key Policy는 다음과 같이 권한을 분리합니다.

- **Key Administrator**: 키 생성/삭제/회전 권한. 주로 보안팀.
- **Key User**: 암호화/복호화 권한. 애플리케이션 Role.
- 두 역할의 분리(SoD, Separation of Duties)를 유지합니다.

### 4. CloudTrail 모니터링

다음 이벤트는 알람을 설정합니다.

- `DisableKey`, `ScheduleKeyDeletion`: 의도하지 않은 키 비활성화/삭제
- `Decrypt` 실패율 급증: 잘못된 권한 또는 공격 시도
- 외부 계정의 `Decrypt` 호출: 예상치 못한 Cross-Account 사용

### 5. Bucket Key 활성화

S3 SSE-KMS 사용 시 반드시 Bucket Key를 활성화하여 KMS API 비용을 99% 절감합니다.

### 6. 키 삭제는 신중하게

KMS Key를 삭제하면 해당 키로 암호화된 모든 데이터를 영구적으로 복호화할 수 없게 됩니다.

- 삭제는 즉시 적용되지 않고 7~30일 대기 기간이 있습니다.
- 대기 기간 동안 `CancelKeyDeletion`으로 취소 가능합니다.
- 삭제보다는 `DisableKey`로 비활성화를 우선 고려합니다.

```bash
# 키 삭제 예약 (30일 대기)
aws kms schedule-key-deletion \
  --key-id alias/old-key \
  --pending-window-in-days 30

# 취소
aws kms cancel-key-deletion --key-id alias/old-key
```

---

## 관련 서비스

| 서비스 | 통합 방식 |
|--------|----------|
| Amazon S3 | SSE-KMS, Bucket Key |
| Amazon EBS | 볼륨/스냅샷 암호화 |
| Amazon RDS | 저장 데이터 암호화 |
| Amazon DynamoDB | 테이블 암호화 |
| AWS Lambda | 환경 변수 암호화 |
| AWS Secrets Manager | 시크릿 암호화 |
| AWS Certificate Manager | 프라이빗 키 보호 |
| AWS CloudHSM | Custom Key Store 백엔드 |
| AWS IAM | Key Policy + IAM Policy 이중 인가 |

---

## 관련 문서

- [[aws-iam-identity-and-access-management-개요|AWS IAM]] - Key Policy와 함께 이중 인가 모델 구성
- [[amazon-rds|Amazon RDS]] - KMS로 저장 데이터 암호화
- [[amazon-cognito-사용자-인증-서비스-개요|Amazon Cognito]] - User Pool 데이터 암호화에 KMS 사용
