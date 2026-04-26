<!-- infographic-hero -->
![AWS CloudHSM 완벽 가이드: 하드웨어 보안 모듈을 활용한 암호화 키 관리 핵심 요약](figures/infographic.svg)

*Figure: AWS CloudHSM 완벽 가이드: 하드웨어 보안 모듈을 활용한 암호화 키 관리 한 장 요약 인포그래픽*

## 개요

AWS CloudHSM은 AWS 클라우드에서 전용 하드웨어 보안 모듈(HSM) 인스턴스를 사용하여 암호화 키를 생성하고 관리할 수 있는 서비스입니다. HSM은 암호화 처리 및 키 저장을 위해 설계된 변조 방지(tamper-resistant) 하드웨어 장치입니다.

CloudHSM은 FIPS 140-2 Level 3 인증을 받은 HSM 하드웨어를 제공합니다. 이는 물리적 변조 시도가 있을 경우 키를 자동으로 삭제하는 수준의 보안을 의미합니다. 이러한 높은 수준의 보안은 금융, 의료, 정부 기관 등 규정 준수(Compliance)가 중요한 환경에서 필수적입니다.

### CloudHSM을 사용해야 하는 경우

다음과 같은 요구사항이 있을 때 CloudHSM을 고려해야 합니다.

- **FIPS 140-2 Level 3 인증**이 필요한 경우
- **전용 HSM 하드웨어**가 필요한 경우 (단일 테넌트)
- **암호화 키에 대한 완전한 제어권**이 필요한 경우
- **PKCS#11, JCE(Java Cryptography Extension), CNG(Microsoft Cryptography API: Next Generation)** 표준 인터페이스가 필요한 경우
- **SSL/TLS 오프로딩**을 하드웨어 수준에서 수행해야 하는 경우
- **규정 준수 감사**에서 전용 HSM 사용을 요구하는 경우

## 핵심 기능

### CloudHSM 클러스터

CloudHSM은 클러스터 단위로 운영됩니다. 클러스터는 여러 가용 영역(AZ)에 걸쳐 HSM 인스턴스를 배포하여 고가용성을 제공합니다. 클러스터 내의 모든 HSM은 자동으로 동기화됩니다.

```bash
# CloudHSM 클러스터 생성
aws cloudhsmv2 create-cluster \
  --hsm-type hsm1.medium \
  --subnet-ids subnet-0a1b2c3d subnet-4e5f6g7h \
  --tags Key=Environment,Value=Production Key=Project,Value=Encryption

# 클러스터 상태 확인
aws cloudhsmv2 describe-clusters \
  --query 'Clusters[*].{ClusterId:ClusterId,State:State,HSMCount:Hsms|length(@),SecurityGroup:SecurityGroup}' \
  --output table
```

### HSM 인스턴스 관리

```bash
# 클러스터에 HSM 추가
aws cloudhsmv2 create-hsm \
  --cluster-id cluster-abc123def456 \
  --availability-zone ap-northeast-2a

# HSM 인스턴스 목록 확인
aws cloudhsmv2 describe-clusters \
  --filters clusterIds=cluster-abc123def456 \
  --query 'Clusters[0].Hsms[*].{HsmId:HsmId,AZ:AvailabilityZone,State:State,IP:EniIp}' \
  --output table

# HSM 삭제
aws cloudhsmv2 delete-hsm \
  --cluster-id cluster-abc123def456 \
  --hsm-id hsm-abc123def456
```

### 클러스터 초기화

CloudHSM 클러스터를 사용하기 위해서는 초기화 과정이 필요합니다.

```bash
# 1. 클러스터 CSR 가져오기
aws cloudhsmv2 describe-clusters \
  --filters clusterIds=cluster-abc123def456 \
  --query 'Clusters[0].Certificates.ClusterCsr' \
  --output text > cluster-csr.pem

# 2. 자체 서명 인증서로 CSR 서명 (OpenSSL)
openssl x509 -req -days 3652 \
  -in cluster-csr.pem \
  -signkey customerCA.key \
  -out cluster-cert.pem

# 3. 서명된 인증서로 클러스터 초기화
aws cloudhsmv2 initialize-cluster \
  --cluster-id cluster-abc123def456 \
  --signed-cert file://cluster-cert.pem \
  --trust-anchor file://customerCA.crt
```

### CloudHSM Client 설치 및 설정

HSM과 상호작용하기 위해서는 CloudHSM Client를 설치해야 합니다.

```bash
# Amazon Linux 2에 CloudHSM Client 설치
sudo yum install -y aws-cloudhsm-client

# 클러스터 IP 설정
sudo /opt/cloudhsm/bin/configure -a <HSM_IP_ADDRESS>

# CloudHSM Client 시작
sudo systemctl start cloudhsm-client

# CloudHSM CLI 도구 실행
/opt/cloudhsm/bin/cloudhsm-cli interactive
```

CloudHSM CLI에서 사용자를 관리하는 명령어는 다음과 같습니다.

```bash
# CloudHSM CLI에서 실행
# 관리자 로그인
login --username admin --role admin

# CU(Crypto User) 생성
user create --username myuser --role crypto-user

# 사용자 목록 확인
user list
```

### 키 관리

CloudHSM에서 암호화 키를 생성하고 관리하는 방법입니다.

```bash
# CloudHSM CLI에서 AES 키 생성
key generate-symmetric aes \
  --key-length-bits 256 \
  --label my-aes-key

# RSA 키 쌍 생성
key generate-asymmetric-pair rsa \
  --modulus-size-bits 2048 \
  --public-label my-rsa-public \
  --private-label my-rsa-private

# 키 목록 확인
key list

# 키 내보내기 (래핑)
key wrap \
  --filter attr.label=my-aes-key \
  --wrapping-filter attr.label=wrapping-key \
  --path /tmp/wrapped-key.bin
```

## 아키텍처/동작 원리

### CloudHSM 클러스터 아키텍처

CloudHSM 클러스터는 VPC 내에서 운영되며, 다음과 같은 아키텍처를 가집니다.

```
+-------------------+     +-------------------+
|   AZ-a            |     |   AZ-c            |
|  +-------------+  |     |  +-------------+  |
|  |   HSM-1     |  |     |  |   HSM-2     |  |
|  |  (Active)   |  |     |  |  (Active)   |  |
|  +------+------+  |     |  +------+------+  |
|         |         |     |         |         |
|  +------+------+  |     |  +------+------+  |
|  |    ENI      |  |     |  |    ENI      |  |
|  +------+------+  |     |  +------+------+  |
+---------+---------+     +---------+---------+
          |                         |
          +------------+------------+
                       |
              +--------+--------+
              |  CloudHSM       |
              |  Client         |
              |  (EC2 Instance) |
              +-----------------+
```

핵심적인 아키텍처 특성은 다음과 같습니다.

1. **단일 테넌트 HSM**: 각 HSM 인스턴스는 고객 전용 하드웨어입니다. 다른 고객과 공유하지 않습니다.
2. **VPC 내 배치**: HSM은 고객의 VPC 내 프라이빗 서브넷에 배치되어 네트워크 격리가 보장됩니다.
3. **자동 동기화**: 클러스터 내 모든 HSM은 키와 사용자 정보를 자동으로 동기화합니다.
4. **AWS 접근 불가**: AWS 직원은 HSM 내부의 키에 접근할 수 없습니다. 고객만이 키를 관리합니다.

### HSM 사용자 유형

CloudHSM은 세 가지 사용자 유형을 지원합니다.

| 사용자 유형 | 약어 | 역할 |
|------------|------|------|
| Precrypto Officer | PRECO | 초기 관리자, CO 생성 후 삭제됨 |
| Crypto Officer | CO | 사용자 관리, HSM 설정 |
| Crypto User | CU | 키 생성/삭제, 암호화/복호화, 서명/검증 |

PRECO는 클러스터 초기화 시 자동으로 생성되며, CO를 생성한 후 PRECO는 삭제됩니다.

### 키 동기화 메커니즘

CloudHSM 클러스터 내의 HSM 간 키 동기화는 자동으로 이루어집니다. 새 HSM이 클러스터에 추가되면, 기존 HSM에서 모든 키와 사용자 정보가 자동으로 복제됩니다. 이 동기화는 암호화된 채널을 통해 이루어지며, HSM 간 직접 통신합니다.

## 실전 활용

### SSL/TLS 오프로딩

CloudHSM을 사용하여 웹 서버의 SSL/TLS 처리를 하드웨어 수준에서 수행할 수 있습니다. 이를 통해 Private Key가 소프트웨어에 노출되지 않으므로 보안이 강화됩니다.

Nginx와 CloudHSM을 연동하는 구성 예시입니다.

```bash
# OpenSSL Dynamic Engine 설치
sudo yum install -y aws-cloudhsm-dyn

# Nginx 설정에서 CloudHSM 엔진 사용
# /etc/nginx/nginx.conf
```

```yaml
# nginx.conf (관련 섹션)
ssl_engine cloudhsm;

server {
    listen 443 ssl;
    server_name example.com;

    ssl_certificate /etc/nginx/ssl/server.crt;
    ssl_certificate_key /etc/nginx/ssl/fake_PEM.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-GCM-SHA256;
}
```

`fake_PEM.key`는 CloudHSM에 저장된 실제 Private Key에 대한 참조(handle)입니다. 실제 키는 HSM에서 벗어나지 않습니다.

### KMS Custom Key Store

CloudHSM을 AWS KMS의 사용자 정의 키 스토어로 사용할 수 있습니다. 이를 통해 KMS의 편리한 인터페이스를 사용하면서도 키를 CloudHSM 하드웨어에 저장할 수 있습니다.

```bash
# KMS Custom Key Store 생성
aws kms create-custom-key-store \
  --custom-key-store-name my-cloudhsm-keystore \
  --cloud-hsm-cluster-id cluster-abc123def456 \
  --key-store-password "MyKeyStorePassword123!" \
  --trust-anchor-certificate file://customerCA.crt

# Custom Key Store 연결
aws kms connect-custom-key-store \
  --custom-key-store-id cks-abc123def456

# Custom Key Store에서 KMS 키 생성
aws kms create-key \
  --origin AWS_CLOUDHSM \
  --custom-key-store-id cks-abc123def456 \
  --description "HSM-backed encryption key"
```

### Oracle TDE (Transparent Data Encryption)

Oracle Database의 TDE 마스터 키를 CloudHSM에 저장하여 데이터베이스 암호화 키를 하드웨어 수준에서 보호할 수 있습니다.

```bash
# Oracle PKCS#11 라이브러리 설정
export CLOUDHSM_ROLE=crypto-user
export CLOUDHSM_PIN=myuser:mypassword

# Oracle Wallet 생성 (CloudHSM 사용)
orapki wallet create -wallet /opt/oracle/wallet -auto_login
```

### Java 애플리케이션 통합

JCE Provider를 통해 Java 애플리케이션에서 CloudHSM을 사용할 수 있습니다.

```python
# Python에서 PKCS#11을 통한 CloudHSM 사용 예시
import pkcs11
from pkcs11 import Mechanism

# CloudHSM PKCS#11 라이브러리 로드
lib = pkcs11.lib('/opt/cloudhsm/lib/libcloudhsm_pkcs11.so')
token = lib.get_token()

# 세션 열기
with token.open(user_pin='myuser:mypassword') as session:
    # AES 키 생성
    key = session.generate_key(
        pkcs11.KeyType.AES,
        256,
        label='my-python-key',
        store=True
    )
    
    # 데이터 암호화
    plaintext = b'Hello, CloudHSM!'
    iv, ciphertext = key.encrypt(plaintext, mechanism=Mechanism.AES_CBC_PAD)
    
    # 데이터 복호화
    decrypted = key.decrypt(ciphertext, mechanism=Mechanism.AES_CBC_PAD, mechanism_param=iv)
    print(f'Decrypted: {decrypted.decode()}')
```

## 모범 사례/보안

### 고가용성 구성

프로덕션 환경에서는 반드시 최소 2개 이상의 HSM을 서로 다른 가용 영역에 배치해야 합니다.

```bash
# 프로덕션 클러스터: 2개 AZ에 HSM 배치
aws cloudhsmv2 create-hsm \
  --cluster-id cluster-abc123def456 \
  --availability-zone ap-northeast-2a

aws cloudhsmv2 create-hsm \
  --cluster-id cluster-abc123def456 \
  --availability-zone ap-northeast-2c
```

### 백업 관리

CloudHSM은 자동으로 클러스터 백업을 생성합니다. 백업은 HSM 하드웨어에 고유한 키로 암호화되어 S3에 저장됩니다.

```bash
# 클러스터 백업 목록 확인
aws cloudhsmv2 describe-backups \
  --filters clusterIds=cluster-abc123def456 \
  --query 'Backups[*].{BackupId:BackupId,State:BackupState,CreateTime:CreateTimestamp}' \
  --output table

# 백업에서 클러스터 복원
aws cloudhsmv2 create-cluster \
  --hsm-type hsm1.medium \
  --source-backup-id backup-abc123def456 \
  --subnet-ids subnet-0a1b2c3d subnet-4e5f6g7h
```

### 보안 권장 사항

1. **네트워크 격리**: CloudHSM은 프라이빗 서브넷에 배치하고, 보안 그룹으로 접근을 제한합니다.
2. **Quorum Authentication**: 중요한 관리 작업에 대해 다중 승인(M of N)을 설정합니다.
3. **감사 로깅**: CloudTrail과 CloudHSM 감사 로그를 활성화하여 모든 키 사용을 기록합니다.
4. **키 순환**: 정기적으로 암호화 키를 순환합니다.
5. **최소 권한 원칙**: CU에게 필요한 최소한의 권한만 부여합니다.

```bash
# CloudTrail에서 CloudHSM 이벤트 확인
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=cloudhsmv2.amazonaws.com \
  --max-results 10 \
  --query 'Events[*].{Time:EventTime,Event:EventName,User:Username}' \
  --output table
```

### 비용 고려사항

CloudHSM은 시간당 과금되며, 비용이 상당히 높은 서비스입니다.

| 항목 | 비용 (서울 리전 기준) |
|------|---------------------|
| HSM 인스턴스 | 시간당 약 $1.50 |
| 월간 비용 (1개 HSM) | 약 $1,080 |
| 프로덕션 (2개 HSM) | 약 $2,160/월 |

따라서 CloudHSM은 규정 준수 요구사항이 있거나, FIPS 140-2 Level 3 인증이 필수인 경우에만 사용을 권장합니다.

## 관련 서비스 비교

### AWS KMS vs AWS CloudHSM

| 항목 | AWS KMS | AWS CloudHSM |
|------|---------|-------------|
| 테넌시 | 멀티 테넌트 | 단일 테넌트 (전용 HSM) |
| FIPS 인증 | FIPS 140-2 Level 2 (일부 Level 3) | FIPS 140-2 Level 3 |
| 키 제어권 | AWS와 공유 | 고객 완전 제어 |
| 비용 | 키당 $1/월 + API 호출 | HSM당 ~$1,080/월 |
| 관리 | 완전 관리형 | 고객 관리 (클러스터 운영) |
| API | AWS KMS API | PKCS#11, JCE, CNG |
| 통합 | 대부분의 AWS 서비스 | KMS Custom Key Store 통해 연동 |
| 성능 | 초당 수천 요청 | 초당 수만 요청 (하드웨어 가속) |
| 키 유형 | 대칭(AES), 비대칭(RSA, ECC) | 대칭, 비대칭, 해시, HMAC 등 다양 |

### CloudHSM을 선택해야 하는 결정 기준

- FIPS 140-2 Level 3가 필수인가? -> CloudHSM
- 단일 테넌트 HSM이 필요한가? -> CloudHSM
- PKCS#11/JCE 인터페이스가 필요한가? -> CloudHSM
- 관리 부담을 최소화하고 싶은가? -> KMS
- 비용을 최소화하고 싶은가? -> KMS
- 대부분의 AWS 서비스와 쉽게 통합하고 싶은가? -> KMS

## 요약

AWS CloudHSM은 최고 수준의 암호화 키 보안이 필요한 환경을 위한 서비스입니다.

1. **FIPS 140-2 Level 3 인증**을 받은 전용 HSM 하드웨어를 제공합니다.
2. **단일 테넌트** 모델로 고객만이 키에 접근할 수 있으며, AWS도 접근할 수 없습니다.
3. **클러스터 기반** 아키텍처로 고가용성을 보장하며, HSM 간 자동 동기화가 이루어집니다.
4. **PKCS#11, JCE, CNG** 등 표준 암호화 인터페이스를 지원합니다.
5. **KMS Custom Key Store**를 통해 KMS의 편의성과 CloudHSM의 보안을 결합할 수 있습니다.
6. **SSL/TLS 오프로딩**, **데이터베이스 TDE**, **코드 서명** 등 다양한 용도로 활용됩니다.
7. 비용이 높으므로 **규정 준수 요구사항이 명확한 경우**에만 사용을 권장합니다.
8. 프로덕션 환경에서는 반드시 **2개 이상의 AZ에 HSM을 배치**하여 고가용성을 확보해야 합니다.