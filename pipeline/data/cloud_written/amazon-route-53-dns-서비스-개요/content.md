<!-- infographic-hero -->
![Amazon Route 53 DNS 서비스 개요 핵심 요약](figures/infographic.svg)

*Figure: Amazon Route 53 DNS 서비스 개요 한 장 요약 인포그래픽*

# Amazon Route 53 DNS 서비스 개요

## 개요

Amazon Route 53은 AWS가 2010년에 출시한 가용성과 확장성이 높은 권한(Authoritative) DNS 서비스이자 도메인 등록 대행 서비스입니다. 이름의 "53"은 DNS 표준 포트 번호 TCP/UDP 53에서 따왔습니다. Route 53은 글로벌 Anycast 네트워크 위에서 동작하며, 100% 가용성 SLA를 제공하는 유일한 AWS 서비스입니다.

Route 53은 크게 세 가지 주요 기능을 제공합니다.

- **도메인 등록 (Domain Registration)**: ICANN 인증 등록 대행자(Accredited Registrar)로 도메인을 직접 등록합니다.
- **DNS 라우팅 (DNS Routing)**: 도메인 이름을 IP 주소 또는 AWS 리소스에 매핑합니다.
- **Health Checking**: 엔드포인트의 상태를 모니터링하고 장애 시 트래픽을 정상 엔드포인트로 라우팅합니다.

Route 53의 강점은 단순한 DNS 응답을 넘어 트래픽 관리(Traffic Flow)에 있습니다. 7가지 라우팅 정책을 조합하여 가중치 기반 카나리 배포, 지연 시간 최적화, 지역별 차별화된 서비스, 자동 Failover 등 복잡한 시나리오를 DNS 레벨에서 구현할 수 있습니다.

---

## 핵심 기능

### 1. Hosted Zone

Hosted Zone은 한 도메인 이름과 그 하위 도메인의 DNS 레코드 집합을 담는 컨테이너입니다.

| 종류 | 설명 |
|------|------|
| Public Hosted Zone | 인터넷에 공개된 도메인. 누구나 조회 가능 |
| Private Hosted Zone | 특정 VPC 내부에서만 해석되는 내부 DNS |

Hosted Zone을 생성하면 4개의 NS(Name Server) 레코드가 자동으로 할당됩니다. 도메인 등록 기관에서 이 NS 레코드를 등록해야 Route 53이 권한 DNS로 동작합니다.

```bash
# Public Hosted Zone 생성
aws route53 create-hosted-zone \
  --name example.com \
  --caller-reference "create-2026-04-26" \
  --hosted-zone-config Comment="Production zone"

# Private Hosted Zone 생성 (VPC 연결)
aws route53 create-hosted-zone \
  --name internal.example.com \
  --vpc VPCRegion=ap-northeast-2,VPCId=vpc-0123456789abcdef0 \
  --caller-reference "private-2026-04-26" \
  --hosted-zone-config Comment="Internal zone",PrivateZone=true
```

### 2. 레코드 유형

Route 53은 표준 DNS 레코드 유형을 지원하며, AWS 전용의 Alias 레코드를 추가로 제공합니다.

| 유형 | 용도 |
|------|------|
| A | IPv4 주소 매핑 |
| AAAA | IPv6 주소 매핑 |
| CNAME | 다른 도메인 이름의 별칭 |
| MX | 메일 서버 |
| TXT | 임의 텍스트 (SPF, DKIM, 도메인 검증) |
| NS | Name Server 위임 |
| SOA | Zone 권한 정보 |
| PTR | 역방향 DNS |
| SRV | 서비스 위치 |
| CAA | 인증서 발급 권한 정의 |
| Alias | AWS 리소스 직접 매핑 (Route 53 전용) |

### 3. Alias 레코드

Alias는 Route 53의 핵심 기능 중 하나입니다. CNAME과 비슷하지만 다음 차이가 있습니다.

| 항목 | CNAME | Alias |
|------|-------|-------|
| Zone Apex 사용 | 불가 (`example.com`에 사용 불가) | 가능 |
| 비용 | 쿼리당 과금 | 무료 |
| 응답 형태 | 타깃 도메인 반환 후 재조회 | A/AAAA 레코드로 직접 반환 |
| AWS 리소스 변경 추적 | 수동 관리 | 자동 추적 |

Alias가 매핑할 수 있는 AWS 리소스는 다음과 같습니다.

- ALB / NLB / CLB (Elastic Load Balancing)
- CloudFront 배포
- API Gateway
- S3 정적 웹사이트
- Elastic Beanstalk 환경
- VPC Interface Endpoint
- Global Accelerator
- 동일 Hosted Zone 내 다른 레코드

### 4. 7가지 라우팅 정책

Route 53은 동일 도메인 이름에 여러 레코드를 등록하고, 라우팅 정책에 따라 응답할 IP를 선택합니다.

| 정책 | 동작 |
|------|------|
| Simple | 단일 또는 다중 값 응답. 정책 없음 |
| Weighted | 가중치에 비례하여 응답 분배 (예: 90:10 카나리) |
| Latency | 클라이언트와 가장 지연 시간이 낮은 리전 응답 |
| Failover | Primary/Secondary 구성. Health Check 실패 시 Secondary로 전환 |
| Geolocation | 클라이언트 위치(국가/대륙) 기반 응답 |
| Geoproximity | 리소스와 클라이언트의 지리적 거리 + Bias 값 기반 |
| Multi-Value Answer | 최대 8개의 정상 IP를 무작위로 응답 |

```bash
# Weighted 정책 (90:10 카나리 배포)
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "SetIdentifier": "stable",
          "Weight": 90,
          "TTL": 60,
          "ResourceRecords": [{"Value": "192.0.2.10"}]
        }
      },
      {
        "Action": "CREATE",
        "ResourceRecordSet": {
          "Name": "api.example.com",
          "Type": "A",
          "SetIdentifier": "canary",
          "Weight": 10,
          "TTL": 60,
          "ResourceRecords": [{"Value": "192.0.2.20"}]
        }
      }
    ]
  }'
```

### 5. Health Check

Health Check는 엔드포인트의 상태를 주기적으로 검사합니다.

| 유형 | 검사 대상 |
|------|----------|
| Endpoint | HTTP/HTTPS/TCP 응답 확인 |
| CloudWatch Alarm | 알람 상태 기반 |
| Calculated | 다른 Health Check 결과를 AND/OR 조합 |

- 글로벌 15개 이상의 위치에서 동시 검사합니다.
- 기본 30초 간격, Fast Interval은 10초입니다.
- 연속 3회 실패하면 unhealthy 처리됩니다.
- Failover 라우팅, Multi-Value Answer 라우팅과 결합하여 자동 트래픽 전환을 구현합니다.

```bash
# HTTPS Health Check 생성
aws route53 create-health-check \
  --caller-reference "hc-api-2026" \
  --health-check-config '{
    "IPAddress": "192.0.2.10",
    "Port": 443,
    "Type": "HTTPS",
    "ResourcePath": "/health",
    "FullyQualifiedDomainName": "api.example.com",
    "RequestInterval": 30,
    "FailureThreshold": 3
  }'
```

### 6. Private Hosted Zone

Private Hosted Zone은 VPC 내부에서만 해석되는 DNS 영역입니다.

- 동일 VPC, 다른 VPC(Peering), 다른 리전 VPC와 연결 가능합니다.
- 같은 도메인을 Public/Private에 모두 두는 Split-Horizon DNS 구성도 지원합니다.
- 서비스 디스커버리(Cloud Map과 결합), 내부 API 라우팅에 활용됩니다.

### 7. DNSSEC

DNSSEC(DNS Security Extensions)는 DNS 응답에 디지털 서명을 추가하여 변조를 방지하는 표준입니다.

- KMS 비대칭 키 기반으로 동작합니다.
- 등록 기관에 DS 레코드 등록이 필요합니다.
- 활성화 시 약간의 응답 지연이 추가될 수 있습니다.

```bash
# DNSSEC 서명 활성화
aws route53 enable-hosted-zone-dnssec \
  --hosted-zone-id Z1234567890ABC

# KSK(Key Signing Key) 생성
aws route53 create-key-signing-key \
  --caller-reference "ksk-2026-04" \
  --hosted-zone-id Z1234567890ABC \
  --key-management-service-arn arn:aws:kms:us-east-1:123456789012:key/abcd-ef-ksk-key \
  --name MyKsk \
  --status ACTIVE
```

### 8. Route 53 Resolver

Route 53 Resolver는 VPC의 기본 DNS 리졸버이며, 두 가지 엔드포인트로 온프레미스 DNS와의 통합을 지원합니다.

- **Inbound Endpoint**: 온프레미스에서 VPC의 Private Hosted Zone을 조회 가능.
- **Outbound Endpoint + 전달 규칙**: VPC에서 온프레미스 도메인 쿼리를 포워딩.

이를 통해 하이브리드 환경에서 단일 DNS 네임스페이스를 구성할 수 있습니다.

---

## 아키텍처

### 글로벌 Anycast 네트워크

Route 53의 응답이 빠른 이유는 전 세계에 분산된 Anycast 네트워크 때문입니다.

```
[Client (Korea)]                  [Client (USA)]
       |                                  |
   가까운 Edge POP                    가까운 Edge POP
       |                                  |
       +------- Route 53 Anycast ---------+
                       |
                  [권한 응답 데이터]
```

수백 개의 Edge POP이 같은 Anycast IP를 광고하여, 클라이언트는 BGP 기반으로 가장 가까운 POP에 자동으로 라우팅됩니다.

### Failover 시나리오

Active-Passive Failover 구성은 다음과 같이 동작합니다.

```
Client → Route 53 → Health Check
                       |
              +--------+--------+
              | Healthy?        |
              +--------+--------+
                       |
        Yes ───────────┴─────────── No
         |                          |
   Primary 응답                Secondary 응답
   (us-east-1 ALB)            (us-west-2 ALB)
```

Health Check가 unhealthy로 판정되면 30~60초 이내에 Secondary IP로 응답이 전환됩니다.

### Latency-Based Routing

Latency Routing은 AWS가 측정한 클라이언트 ↔ 리전 간 RTT 데이터를 기반으로 응답을 결정합니다. 사용자가 한국에 있고 us-east-1, ap-northeast-2 두 리전에 동일한 서비스가 배포되어 있다면 ap-northeast-2 IP를 응답합니다.

---

## 실전 사용

### 1. ALB에 Alias 레코드 매핑

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "blog.example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "ZWKZPGTI48KDX",
          "DNSName": "dualstack.my-alb-1234567890.ap-northeast-2.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        }
      }
    }]
  }'
```

`HostedZoneId`는 ALB의 ELB Hosted Zone ID이며 리전마다 고정값이 있습니다(서울은 `ZWKZPGTI48KDX`). `EvaluateTargetHealth=true`로 설정하면 ALB의 Health Check 결과가 DNS 응답에 반영됩니다.

### 2. Terraform으로 멀티 리전 Failover

```hcl
resource "aws_route53_health_check" "primary" {
  fqdn              = "api-primary.example.com"
  port              = 443
  type              = "HTTPS"
  resource_path     = "/health"
  request_interval  = 30
  failure_threshold = 3
}

resource "aws_route53_record" "primary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.example.com"
  type    = "A"
  set_identifier = "primary"

  failover_routing_policy {
    type = "PRIMARY"
  }
  health_check_id = aws_route53_health_check.primary.id

  alias {
    name                   = aws_lb.primary.dns_name
    zone_id                = aws_lb.primary.zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "secondary" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.example.com"
  type    = "A"
  set_identifier = "secondary"

  failover_routing_policy {
    type = "SECONDARY"
  }

  alias {
    name                   = aws_lb.secondary.dns_name
    zone_id                = aws_lb.secondary.zone_id
    evaluate_target_health = true
  }
}
```

### 3. Multi-Value Answer 라우팅

Multi-Value Answer는 ELB 같은 중앙 LB 없이 클라이언트 측에서 여러 IP 중 하나를 선택하도록 하는 라우팅입니다. Health Check를 함께 사용하면 unhealthy IP는 응답에서 제외됩니다.

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "service.example.com",
        "Type": "A",
        "SetIdentifier": "node-1",
        "MultiValueAnswer": true,
        "TTL": 60,
        "ResourceRecords": [{"Value": "10.0.1.10"}],
        "HealthCheckId": "abcdef-12345"
      }
    }]
  }'
```

---

## 가격 / 한도

### 주요 비용

| 항목 | 가격 |
|------|------|
| Hosted Zone | $0.50 / 월 / Zone (처음 25개) |
| 표준 쿼리 | $0.40 / 100만 쿼리 (처음 10억) |
| Latency / Geo / Geoproximity 쿼리 | $0.60 / 100만 |
| Alias 쿼리 (AWS 리소스 매핑) | 무료 |
| Health Check (AWS 엔드포인트) | $0.50 / 월 |
| Health Check (외부 엔드포인트) | $0.75 / 월 |
| 도메인 등록 | TLD별 상이 (.com 약 $13/년) |
| Resolver Endpoint | $0.125 / 시간 / ENI |

### 주요 한도

| 항목 | 한도 |
|------|------|
| 계정당 Hosted Zone | 500개 (Soft) |
| Hosted Zone당 레코드 | 10,000개 (Soft) |
| 계정당 Health Check | 200개 (Soft) |
| 계정당 Resolver 규칙 | 1,000개 (Soft) |

---

## Best Practice

### 도메인/Zone 관리

1. **Apex 도메인은 Alias 사용**: `example.com`을 ALB로 매핑할 때 CNAME 대신 Alias 사용.
2. **TTL 균형**: 안정 운영 시 300~3600초, 마이그레이션 직전에는 60초로 단축.
3. **NS 레코드 보호**: Hosted Zone의 NS 레코드를 함부로 수정하지 않습니다.
4. **외부 등록 도메인 위임**: 다른 등록 기관 도메인은 NS 레코드 4개를 정확히 등록.

### 보안

1. **DNSSEC 검토**: 금융, 정부 도메인은 DNSSEC 활성화 권장.
2. **CAA 레코드 추가**: 허용된 CA(예: Amazon, Let's Encrypt)만 명시.
3. **Private Hosted Zone 활용**: 내부 서비스는 외부에 노출하지 않습니다.
4. **IAM 최소 권한**: Hosted Zone 단위로 권한을 분리합니다.

### 가용성

1. **Failover + Health Check 조합**: 멀티 리전 DR 구성의 표준.
2. **Health Check 외부 모니터링 분리**: 한 모니터링 시스템 장애가 DNS 전체에 영향 주지 않도록 설계.
3. **Alias의 EvaluateTargetHealth 활성화**: ALB 자체 헬스 정보가 자동 반영됩니다.
4. **Application Recovery Controller**: 멀티 리전 Failover의 의사결정 자동화.

### 운영

1. **Change Set 사용**: 다수 레코드 변경은 단일 ChangeBatch로 원자적 적용.
2. **Query Logging**: CloudWatch로 DNS 쿼리 로그 수집해 트래픽 패턴 분석.
3. **Terraform/CDK 관리**: 수동 변경을 지양하고 IaC로 추적합니다.

---

## 관련 서비스

| 서비스 | 관계 |
|--------|------|
| Amazon CloudFront | CDN. Route 53 Alias로 매핑하는 대표 대상 |
| Elastic Load Balancing | ALB/NLB Alias 매핑 |
| AWS Global Accelerator | 글로벌 Anycast IP. Route 53 Latency 정책 대안 |
| AWS Cloud Map | 마이크로서비스 디스커버리 |
| AWS Certificate Manager | TLS 인증서 발급/검증을 DNS 검증으로 진행 |
| Amazon VPC | Private Hosted Zone과 Resolver로 통합 |
| Application Recovery Controller | 멀티 리전 Failover 의사결정 |

> **Route 53 vs CloudFront**: 두 서비스는 경쟁이 아닌 보완 관계입니다. CloudFront는 캐싱과 콘텐츠 배포를 담당하고, Route 53은 DNS 레벨에서 라우팅 결정을 합니다. 일반적으로 도메인 → Route 53 → CloudFront → 오리진(ALB/S3) 흐름으로 함께 사용됩니다.

---

## 관련 문서

- [[amazon-cloudfront|Amazon CloudFront]] - 글로벌 CDN. Route 53 Alias로 매핑
- [[amazon-vpc-virtual-private-cloud-개요|Amazon VPC]] - Private Hosted Zone 연결
- [[amazon-elb-application-load-balancer-개요|Amazon ELB]] - ALB/NLB Alias 매핑 대상
