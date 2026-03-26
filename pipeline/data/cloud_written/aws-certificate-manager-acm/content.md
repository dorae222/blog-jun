## 개요

AWS Certificate Manager(ACM)는 AWS 서비스 및 내부 연결 리소스에 사용할 수 있는 공인 및 사설 SSL/TLS 인증서를 쉽게 프로비저닝, 관리 및 배포할 수 있는 서비스입니다.

SSL/TLS 인증서를 직접 관리하는 것은 상당히 번거로운 작업입니다. 인증서 구매, CSR(Certificate Signing Request) 생성, 도메인 검증, 인증서 설치, 갱신 관리 등 여러 단계를 거쳐야 합니다. ACM은 이러한 복잡한 과정을 자동화하여 개발자가 인프라 보안에 집중할 수 있도록 도와줍니다.

ACM의 핵심 장점은 다음과 같습니다.

- **무료 공인 인증서**: ACM에서 발급하는 공인 인증서는 비용이 발생하지 않습니다.
- **자동 갱신**: ACM이 인증서 만료 전에 자동으로 갱신합니다.
- **통합 관리**: AWS 서비스와 원활하게 통합되어 별도의 인증서 배포가 필요 없습니다.
- **와일드카드 인증서 지원**: `*.example.com` 형태의 와일드카드 인증서를 발급할 수 있습니다.

## 핵심 기능

### 공인 인증서 발급

ACM에서 공인 인증서를 발급하는 과정은 다음과 같습니다.

```bash
# 공인 인증서 요청
aws acm request-certificate \
  --domain-name example.com \
  --subject-alternative-names "*.example.com" "www.example.com" \
  --validation-method DNS \
  --tags Key=Environment,Value=Production Key=Project,Value=MyWebApp
```

인증서 요청 후 도메인 검증이 필요합니다. ACM은 두 가지 검증 방법을 지원합니다.

**DNS 검증 (권장)**

DNS 검증은 도메인의 DNS 레코드에 CNAME 레코드를 추가하여 도메인 소유권을 증명하는 방법입니다. Route 53을 사용하는 경우 ACM이 자동으로 DNS 레코드를 생성할 수 있습니다.

```bash
# 인증서 상태 및 검증 정보 확인
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:ap-northeast-2:123456789012:certificate/abc12345-1234-1234-1234-abc123456789 \
  --query 'Certificate.DomainValidationOptions'
```

출력 예시는 다음과 같습니다.

```json
[
  {
    "DomainName": "example.com",
    "ValidationDomain": "example.com",
    "ValidationStatus": "PENDING_VALIDATION",
    "ResourceRecord": {
      "Name": "_abc123.example.com.",
      "Type": "CNAME",
      "Value": "_def456.acm-validations.aws."
    },
    "ValidationMethod": "DNS"
  }
]
```

Route 53을 사용하는 경우 다음과 같이 DNS 레코드를 자동으로 생성할 수 있습니다.

```bash
# Route 53에 검증 레코드 자동 생성
aws acm request-certificate \
  --domain-name example.com \
  --validation-method DNS \
  --domain-validation-options DomainName=example.com,ValidationDomain=example.com
```

**이메일 검증**

이메일 검증은 도메인의 관리자 이메일 주소로 검증 이메일을 보내는 방법입니다. DNS 검증이 불가능한 경우에 사용합니다.

```bash
# 이메일 검증으로 인증서 요청
aws acm request-certificate \
  --domain-name example.com \
  --validation-method EMAIL \
  --domain-validation-options DomainName=example.com,ValidationDomain=example.com
```

### 사설 인증서 (Private CA)

ACM Private CA를 사용하면 조직 내부에서 사용할 수 있는 사설 인증서를 발급할 수 있습니다. 이는 내부 API 통신, 마이크로서비스 간 mTLS(상호 TLS), IoT 디바이스 인증 등에 활용됩니다.

```bash
# Private CA 생성
aws acm-pca create-certificate-authority \
  --certificate-authority-configuration '{
    "KeyAlgorithm": "RSA_2048",
    "SigningAlgorithm": "SHA256WITHRSA",
    "Subject": {
      "Country": "KR",
      "Organization": "MyCompany",
      "OrganizationalUnit": "Engineering",
      "CommonName": "MyCompany Internal CA"
    }
  }' \
  --certificate-authority-type SUBORDINATE \
  --tags Key=Environment,Value=Production

# Private CA에서 사설 인증서 발급
aws acm request-certificate \
  --domain-name internal.mycompany.com \
  --certificate-authority-arn arn:aws:acm-pca:ap-northeast-2:123456789012:certificate-authority/abc12345 \
  --tags Key=Service,Value=InternalAPI
```

Private CA는 월 $400의 비용이 발생하므로 사용량과 필요성을 신중히 검토해야 합니다.

### 인증서 가져오기

외부 CA에서 발급받은 인증서를 ACM으로 가져와 관리할 수 있습니다. 다만, 가져온 인증서는 자동 갱신이 지원되지 않습니다.

```bash
# 외부 인증서 가져오기
aws acm import-certificate \
  --certificate fileb://certificate.pem \
  --private-key fileb://private-key.pem \
  --certificate-chain fileb://certificate-chain.pem \
  --tags Key=Source,Value=External Key=Provider,Value=DigiCert
```

### 인증서 목록 및 상태 관리

```bash
# 모든 인증서 목록 조회
aws acm list-certificates \
  --certificate-statuses ISSUED PENDING_VALIDATION \
  --query 'CertificateSummaryList[*].{Domain:DomainName,ARN:CertificateArn,Status:Status}' \
  --output table

# 만료 예정 인증서 확인 (30일 이내)
aws acm list-certificates \
  --certificate-statuses ISSUED \
  --query 'CertificateSummaryList[?NotAfter<=`2024-02-15`]'
```

## 아키텍처/동작 원리

### 인증서 검증 프로세스

ACM 인증서 발급의 전체 흐름은 다음과 같습니다.

1. **인증서 요청**: 사용자가 ACM API를 통해 인증서를 요청합니다.
2. **도메인 검증**: DNS 또는 이메일을 통해 도메인 소유권을 검증합니다.
3. **인증서 발급**: 검증이 완료되면 ACM이 인증서를 발급합니다.
4. **인증서 배포**: 사용자가 ALB, CloudFront 등 AWS 서비스에 인증서를 연결합니다.
5. **자동 갱신**: 만료 60일 전부터 ACM이 자동으로 갱신을 시도합니다.

DNS 검증의 경우, 최초 한 번 CNAME 레코드를 등록하면 이후 자동 갱신에도 동일한 레코드가 사용되므로 추가 작업이 필요 없습니다. 이것이 DNS 검증이 권장되는 주된 이유입니다.

### 자동 갱신 메커니즘

ACM은 인증서 만료 60일 전부터 자동 갱신을 시도합니다. 자동 갱신이 실패하는 경우는 다음과 같습니다.

- DNS 검증 레코드가 삭제된 경우
- 인증서가 어떤 AWS 리소스에도 연결되지 않은 경우
- 도메인 검증에 실패한 경우

```bash
# 인증서 갱신 상태 확인
aws acm describe-certificate \
  --certificate-arn arn:aws:acm:ap-northeast-2:123456789012:certificate/abc12345 \
  --query 'Certificate.{Status:Status,RenewalSummary:RenewalSummary,NotAfter:NotAfter}'

# 갱신 실패 시 수동 갱신 요청
aws acm renew-certificate \
  --certificate-arn arn:aws:acm:ap-northeast-2:123456789012:certificate/abc12345
```

### 리전 제약

ACM 인증서는 리전별로 관리됩니다. 이 점에서 주의해야 할 사항이 있습니다.

- **CloudFront**: us-east-1(버지니아 북부) 리전에서만 인증서를 발급해야 합니다.
- **ALB, NLB, API Gateway**: 해당 리소스와 동일한 리전에서 인증서를 발급해야 합니다.

```bash
# CloudFront용 인증서는 반드시 us-east-1에서 발급
aws acm request-certificate \
  --region us-east-1 \
  --domain-name example.com \
  --subject-alternative-names "*.example.com" \
  --validation-method DNS
```

## 실전 활용

### ALB + ACM 구성

가장 일반적인 ACM 활용 패턴인 ALB와의 연동을 살펴보겠습니다.

```bash
# 1. 인증서 발급
CERT_ARN=$(aws acm request-certificate \
  --domain-name api.example.com \
  --validation-method DNS \
  --query 'CertificateArn' \
  --output text)

echo "Certificate ARN: $CERT_ARN"

# 2. ALB에 HTTPS 리스너 추가
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/app/my-alb/1234567890abcdef \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=$CERT_ARN \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:targetgroup/my-targets/1234567890abcdef \
  --ssl-policy ELBSecurityPolicy-TLS13-1-2-2021-06

# 3. HTTP에서 HTTPS로 리다이렉트 설정
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/app/my-alb/1234567890abcdef \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=redirect,RedirectConfig='{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}'
```

### CloudFront + ACM + S3 정적 웹사이트

```bash
# 1. us-east-1에서 인증서 발급 (CloudFront 필수)
CF_CERT_ARN=$(aws acm request-certificate \
  --region us-east-1 \
  --domain-name www.example.com \
  --subject-alternative-names example.com \
  --validation-method DNS \
  --query 'CertificateArn' \
  --output text)

# 2. CloudFront 배포 생성 (인증서 연결)
aws cloudfront create-distribution \
  --distribution-config '{
    "CallerReference": "my-unique-ref-2024",
    "Aliases": {
      "Quantity": 2,
      "Items": ["www.example.com", "example.com"]
    },
    "Origins": {
      "Quantity": 1,
      "Items": [{
        "Id": "S3Origin",
        "DomainName": "my-bucket.s3.amazonaws.com",
        "S3OriginConfig": {"OriginAccessIdentity": ""}
      }]
    },
    "DefaultCacheBehavior": {
      "TargetOriginId": "S3Origin",
      "ViewerProtocolPolicy": "redirect-to-https",
      "ForwardedValues": {"QueryString": false, "Cookies": {"Forward": "none"}},
      "MinTTL": 0
    },
    "ViewerCertificate": {
      "ACMCertificateArn": "'"$CF_CERT_ARN"'",
      "SSLSupportMethod": "sni-only",
      "MinimumProtocolVersion": "TLSv1.2_2021"
    },
    "Enabled": true,
    "Comment": "My website distribution",
    "DefaultRootObject": "index.html"
  }'
```

### API Gateway + ACM 커스텀 도메인

```bash
# 1. API Gateway 커스텀 도메인 생성
aws apigatewayv2 create-domain-name \
  --domain-name api.example.com \
  --domain-name-configurations CertificateArn=$CERT_ARN

# 2. API 매핑 생성
aws apigatewayv2 create-api-mapping \
  --domain-name api.example.com \
  --api-id abc123def4 \
  --stage production
```

### Terraform을 활용한 ACM 자동화

```python
# boto3를 활용한 인증서 만료 모니터링 스크립트
import boto3
from datetime import datetime, timezone, timedelta

def check_certificate_expiry(region='ap-northeast-2', days_threshold=30):
    acm = boto3.client('acm', region_name=region)
    
    paginator = acm.get_paginator('list_certificates')
    expiring_certs = []
    
    for page in paginator.paginate(CertificateStatuses=['ISSUED']):
        for cert_summary in page['CertificateSummaryList']:
            cert_detail = acm.describe_certificate(
                CertificateArn=cert_summary['CertificateArn']
            )['Certificate']
            
            not_after = cert_detail.get('NotAfter')
            if not_after:
                days_until_expiry = (not_after - datetime.now(timezone.utc)).days
                if days_until_expiry <= days_threshold:
                    expiring_certs.append({
                        'DomainName': cert_detail['DomainName'],
                        'CertificateArn': cert_detail['CertificateArn'],
                        'DaysUntilExpiry': days_until_expiry,
                        'RenewalEligibility': cert_detail.get('RenewalEligibility', 'N/A')
                    })
    
    return expiring_certs

if __name__ == '__main__':
    certs = check_certificate_expiry()
    for cert in certs:
        print(f"[WARNING] {cert['DomainName']} expires in {cert['DaysUntilExpiry']} days")
        print(f"  ARN: {cert['CertificateArn']}")
        print(f"  Renewal: {cert['RenewalEligibility']}")
```

## 모범 사례/보안

### SSL/TLS 정책 선택

ALB에서 사용할 SSL/TLS 정책을 적절히 선택하는 것이 중요합니다.

| 정책 | 최소 TLS 버전 | 권장 용도 |
|------|-------------|----------|
| ELBSecurityPolicy-TLS13-1-2-2021-06 | TLS 1.2 | TLS 1.3 지원이 필요한 경우 (권장) |
| ELBSecurityPolicy-TLS-1-2-2017-01 | TLS 1.2 | 일반적인 프로덕션 환경 |
| ELBSecurityPolicy-2016-08 | TLS 1.0 | 레거시 클라이언트 지원 필요 시 |

```bash
# HTTPS 리스너의 SSL 정책 업데이트
aws elbv2 modify-listener \
  --listener-arn arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:listener/app/my-alb/1234567890/abcdef123456 \
  --ssl-policy ELBSecurityPolicy-TLS13-1-2-2021-06
```

### Certificate Transparency 로그

ACM이 발급하는 모든 공인 인증서는 CT(Certificate Transparency) 로그에 기록됩니다. CT 로그 비활성화 옵션도 있지만, 보안상 활성화된 상태를 유지하는 것이 권장됩니다.

```bash
# CT 로그 비활성화 (권장하지 않음)
aws acm request-certificate \
  --domain-name example.com \
  --validation-method DNS \
  --options CertificateTransparencyLoggingPreference=DISABLED
```

### 인증서 만료 경보 설정

EventBridge를 통해 인증서 상태 변경 이벤트를 모니터링할 수 있습니다.

```bash
# EventBridge 규칙 생성 (인증서 만료 예정 알림)
aws events put-rule \
  --name ACMCertificateExpiring \
  --event-pattern '{
    "source": ["aws.acm"],
    "detail-type": ["ACM Certificate Approaching Expiration"]
  }'

# SNS 대상 추가
aws events put-targets \
  --rule ACMCertificateExpiring \
  --targets 'Id=1,Arn=arn:aws:sns:ap-northeast-2:123456789012:security-alerts'
```

### 핵심 보안 권장 사항

1. **DNS 검증을 사용**하여 자동 갱신이 원활하게 이루어지도록 합니다.
2. **TLS 1.2 이상**을 최소 프로토콜 버전으로 설정합니다.
3. **와일드카드 인증서는 신중하게** 사용합니다. 인증서가 유출되면 모든 서브도메인이 위험해집니다.
4. **ACM Private CA**를 사용하여 내부 서비스 간 mTLS를 구현합니다.
5. **인증서 핀닝(Certificate Pinning)을 피합니다**. ACM이 인증서를 갱신하면 공개키가 변경될 수 있습니다.

## 관련 서비스 비교

### ACM vs Let's Encrypt

| 항목 | ACM | Let's Encrypt |
|------|-----|---------------|
| 비용 | 무료 (AWS 서비스 사용) | 무료 |
| 인증서 유효기간 | 13개월 | 90일 |
| 갱신 | 자동 (AWS 관리) | certbot 등 도구 필요 |
| 호환성 | AWS 서비스만 | 모든 서버 |
| 와일드카드 | 지원 | 지원 (DNS 검증 필요) |
| Private Key 추출 | 불가 | 가능 |

ACM의 인증서 Private Key는 추출할 수 없습니다. 이는 보안을 강화하지만, EC2 인스턴스의 Nginx, Apache 등에 직접 인증서를 설치해야 하는 경우에는 ACM을 사용할 수 없다는 의미이기도 합니다. 이런 경우 Let's Encrypt 또는 외부 CA 인증서를 사용해야 합니다.

### ACM Public vs ACM Private CA

| 항목 | ACM Public | ACM Private CA |
|------|-----------|----------------|
| 비용 | 무료 | 월 $400 + 인증서당 비용 |
| 용도 | 외부 HTTPS | 내부 통신, mTLS, IoT |
| 신뢰 범위 | 공개적으로 신뢰 | 조직 내부만 신뢰 |
| 발급 속도 | 검증 후 수분 | 즉시 |
| Private Key 추출 | 불가 | 가능 |

## 요약

AWS Certificate Manager는 SSL/TLS 인증서의 전체 수명 주기를 자동화하는 핵심 서비스입니다.

1. **무료 공인 인증서**를 발급받아 ALB, CloudFront, API Gateway 등에 배포할 수 있습니다.
2. **DNS 검증**을 사용하면 자동 갱신이 원활하게 이루어집니다.
3. **CloudFront**에 연결할 인증서는 반드시 **us-east-1** 리전에서 발급해야 합니다.
4. EC2에 직접 인증서를 설치해야 하는 경우에는 ACM 인증서를 사용할 수 없으므로, ALB를 앞에 두거나 외부 CA 인증서를 사용해야 합니다.
5. **Private CA**는 내부 서비스 간 mTLS 구현에 활용할 수 있으나 비용이 발생합니다.
6. **EventBridge**를 활용하여 인증서 상태 변경을 모니터링하고, 만료 전 알림을 받을 수 있습니다.
7. **TLS 1.2 이상**을 최소 프로토콜 버전으로 설정하는 것이 보안 모범 사례입니다.