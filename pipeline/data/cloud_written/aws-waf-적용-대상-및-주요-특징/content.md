<!-- infographic-hero -->
![AWS WAF 적용 대상 및 주요 특징 핵심 요약](figures/infographic.svg)

*Figure: AWS WAF 적용 대상 및 주요 특징 한 장 요약 인포그래픽*

# AWS WAF 적용 대상 및 주요 특징

## 개요

AWS WAF(Web Application Firewall)는 웹 애플리케이션으로 들어오는 HTTP/HTTPS 트래픽을 필터링하여 SQL Injection, Cross-Site Scripting(XSS), 악성 봇 등 다양한 웹 기반 공격으로부터 애플리케이션을 보호하는 관리형 보안 서비스입니다.

AWS WAF는 OSI 모델의 Layer 7(애플리케이션 계층)에서 동작하며, HTTP 요청의 헤더, 본문, URI, 쿼리 스트링 등을 세밀하게 검사할 수 있습니다. 네트워크 레벨 방화벽(Security Group, Network ACL)으로는 탐지하기 어려운 애플리케이션 레벨의 공격을 효과적으로 차단할 수 있다는 점이 가장 큰 차별점입니다.

특히 AWS WAF는 단독으로 사용되기보다는 CloudFront, Application Load Balancer, API Gateway 등 AWS의 주요 서비스와 통합되어 동작합니다. 이러한 통합을 통해 별도의 인프라 구축 없이도 웹 애플리케이션에 즉시 보안 계층을 추가할 수 있다는 것이 큰 장점입니다. 본 포스트에서는 AWS WAF의 적용 대상 서비스, 핵심 기능, 동작 원리, 그리고 실전 활용 방법을 상세히 다루겠습니다.

## 핵심 기능

### 적용 대상 서비스

AWS WAF는 다음 AWS 서비스에 연동하여 사용할 수 있습니다.

| 적용 대상 서비스 | 설명 | Web ACL 스코프 |
|---|---|---|
| Amazon CloudFront | CDN 엣지 로케이션에서 트래픽을 사전 필터링하여 오리진 서버 보호 | 글로벌 (us-east-1) |
| Application Load Balancer (ALB) | HTTP/HTTPS 트래픽을 분산하는 로드밸런서에 WAF를 연동하여 백엔드 보호 | 리전별 |
| Amazon API Gateway | REST API 및 HTTP API 엔드포인트 보호 | 리전별 |
| AWS AppSync GraphQL API | GraphQL API 엔드포인트에 대한 악성 쿼리 차단 | 리전별 |
| Amazon Cognito User Pool | 사용자 인증 엔드포인트를 보호하여 계정 탈취 시도 차단 | 리전별 |
| AWS App Runner | 컨테이너 애플리케이션 보호 | 리전별 |
| AWS Verified Access | 제로 트러스트 액세스 보호 | 리전별 |

주의할 점은 **Network Load Balancer(NLB)에는 WAF를 직접 적용할 수 없다**는 것입니다. NLB는 Layer 4에서 동작하므로 Layer 7 기반인 WAF와 호환되지 않습니다. NLB를 사용하면서 WAF를 적용하려면 NLB 앞에 ALB를 두거나 CloudFront를 사용하는 방식으로 우회해야 합니다.

### Web ACL (Web Access Control List)

Web ACL은 AWS WAF의 핵심 구성 요소로, 웹 요청을 허용(Allow), 차단(Block), 카운트(Count), 또는 CAPTCHA 챌린지를 수행하는 규칙들의 집합입니다. 하나의 Web ACL에는 여러 규칙 또는 규칙 그룹을 포함할 수 있으며, 각 규칙에는 우선순위(Priority)가 부여됩니다.

```
Web ACL 구조
  +-- Default Action (Allow / Block)
  +-- Rule 1 (Priority: 0) - AWS Managed Rule: IP Reputation List
  +-- Rule 2 (Priority: 1) - AWS Managed Rule: Core Rule Set
  +-- Rule 3 (Priority: 2) - AWS Managed Rule: SQL Injection
  +-- Rule 4 (Priority: 3) - Rate-based Rule (2000/5min)
  +-- Rule 5 (Priority: 4) - IP Set Rule (Block list)
  +-- Rule 6 (Priority: 5) - Custom Rule (Geo restriction)
  +-- Rule 7 (Priority: 6) - Custom Rule (URI path match)
```

규칙은 우선순위 순으로 평가되며, 첫 번째로 매칭되는 규칙의 액션이 적용됩니다. 어떤 규칙에도 매칭되지 않으면 Web ACL의 기본 동작(Default Action)이 수행됩니다.

### 규칙 유형

AWS WAF에서 사용할 수 있는 주요 규칙 유형은 다음과 같습니다.

- **IP Set 규칙**: 특정 IP 주소 또는 CIDR 범위를 기반으로 트래픽을 허용하거나 차단합니다.
- **Rate-based 규칙**: 동일한 IP에서 5분 내에 설정된 임계값을 초과하는 요청이 발생하면 자동으로 차단합니다. 최소 임계값은 100입니다.
- **SQL Injection 탐지 규칙**: 요청 내용에서 SQL 인젝션 패턴을 탐지합니다.
- **XSS 탐지 규칙**: Cross-Site Scripting 공격 패턴을 탐지합니다.
- **Geo Match 규칙**: 요청의 출발 국가를 기반으로 필터링합니다.
- **Size Constraint 규칙**: 요청 본문이나 헤더의 크기를 기준으로 필터링합니다.
- **Regex Pattern Set 규칙**: 정규 표현식을 사용하여 요청 내용을 매칭합니다.
- **Label Match 규칙**: 다른 규칙이 추가한 레이블을 기반으로 추가 필터링합니다.

### AWS Managed Rules

AWS에서 사전 구성하여 제공하는 관리형 규칙 그룹으로, 별도의 규칙 작성 없이도 일반적인 웹 취약점에 대한 보호를 즉시 적용할 수 있습니다.

| 규칙 그룹 | 설명 | WCU |
|---|---|---|
| AWSManagedRulesCommonRuleSet | OWASP Top 10 핵심 규칙 | 700 |
| AWSManagedRulesSQLiRuleSet | SQL Injection 방어 | 200 |
| AWSManagedRulesKnownBadInputsRuleSet | 알려진 악성 입력 차단 | 200 |
| AWSManagedRulesLinuxRuleSet | Linux 관련 공격 방어 | 200 |
| AWSManagedRulesAmazonIpReputationList | 악성 IP 차단 | 25 |
| AWSManagedRulesAnonymousIpList | VPN, Tor 등 익명 IP 차단 | 50 |
| AWSManagedRulesBotControlRuleSet | 봇 관리 (유료) | 50 |
| AWSManagedRulesATPRuleSet | 계정 탈취 방어 (유료) | 50 |

WCU(Web ACL Capacity Units)는 각 규칙이 소비하는 처리 용량을 나타내며, Web ACL당 기본 한도는 1,500 WCU입니다.

## 아키텍처/동작 원리

### Layer 7 기반 트래픽 필터링

AWS WAF는 OSI 7계층(애플리케이션 계층)에서 동작합니다. 이는 HTTP 프로토콜의 세부 내용을 분석할 수 있다는 것을 의미합니다. 구체적으로 다음과 같은 요소들을 검사합니다.

- HTTP 메서드 (GET, POST, PUT, DELETE 등)
- URI 경로
- 쿼리 스트링 파라미터
- HTTP 헤더 (User-Agent, Referer, Cookie 등)
- 요청 본문 (POST body)
- IP 주소 및 지리적 위치 정보

### Web ACL의 리전 특성

Web ACL의 스코프(Scope)는 적용 대상 서비스에 따라 달라집니다. 이 차이를 이해하지 못하면 Web ACL 생성 후 연동이 되지 않는 문제가 발생할 수 있으므로 반드시 숙지해야 합니다.

- **CloudFront에 연동하는 경우**: Web ACL은 반드시 `--scope CLOUDFRONT`와 `--region us-east-1`로 생성해야 합니다. CloudFront는 글로벌 서비스이므로 Web ACL도 글로벌 스코프로 생성됩니다.
- **ALB, API Gateway, AppSync, Cognito 등에 연동하는 경우**: Web ACL은 `--scope REGIONAL`로 해당 리소스와 같은 리전에 생성해야 합니다.

### 트래픽 처리 흐름

```
클라이언트 요청
    |
    v
[CloudFront / ALB / API Gateway]
    |
    v
[AWS WAF - Web ACL 규칙 평가]
    |
    +-- 규칙 매칭 --> Block (403 응답) / Count (로그만 기록) / CAPTCHA
    |
    +-- 규칙 미매칭 --> Default Action (Allow 또는 Block)
    |
    v
[백엔드 애플리케이션]
```

### 인바운드 전용 필터링

AWS WAF는 **인바운드 트래픽 필터링에만 특화**되어 있습니다. 웹 애플리케이션으로 들어오는 요청을 분석하고 차단하는 것이 주요 목적이며, 아웃바운드 트래픽(서버에서 외부로 나가는 응답)에 대한 필터링은 지원하지 않습니다.

아웃바운드 트래픽 제어가 필요한 경우에는 Security Group, Network ACL, 또는 AWS Network Firewall 등을 별도로 구성해야 합니다.

### WCU 소비 구조

규칙의 복잡도에 따라 소비하는 WCU가 다릅니다.

| 규칙 유형 | WCU 소비 |
|---|---|
| IP Set 매칭 | 1 |
| Geo Match | 1 |
| 문자열 매칭 (단일) | 1-10 |
| Regex Match | 25 |
| Rate-based | 2 |
| SQL Injection 매칭 | 20 |
| XSS 매칭 | 40 |

## 실전 활용

### Web ACL 생성 및 관리형 규칙 추가 (AWS CLI)

다음은 AWS CLI를 사용하여 프로덕션 환경에 권장되는 Web ACL을 생성하는 예시입니다.

```bash
# Web ACL 생성 (리전 스코프 - ALB/API Gateway용)
aws wafv2 create-web-acl \
  --name "production-web-acl" \
  --scope REGIONAL \
  --default-action Allow={} \
  --region ap-northeast-2 \
  --rules '[
    {
      "Name": "AWSManagedRulesAmazonIpReputationList",
      "Priority": 0,
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesAmazonIpReputationList"
        }
      },
      "OverrideAction": { "None": {} },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "IPReputation"
      }
    },
    {
      "Name": "AWSManagedRulesCommonRuleSet",
      "Priority": 1,
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesCommonRuleSet"
        }
      },
      "OverrideAction": { "None": {} },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "CommonRuleSet"
      }
    },
    {
      "Name": "AWSManagedRulesSQLiRuleSet",
      "Priority": 2,
      "Statement": {
        "ManagedRuleGroupStatement": {
          "VendorName": "AWS",
          "Name": "AWSManagedRulesSQLiRuleSet"
        }
      },
      "OverrideAction": { "None": {} },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "SQLiRuleSet"
      }
    },
    {
      "Name": "RateLimitPerIP",
      "Priority": 3,
      "Statement": {
        "RateBasedStatement": {
          "Limit": 2000,
          "AggregateKeyType": "IP"
        }
      },
      "Action": { "Block": {} },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RateLimit"
      }
    }
  ]' \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=productionWebACL
```

### CloudFront용 Web ACL 생성 (글로벌 스코프)

```bash
# CloudFront에 연동할 Web ACL은 반드시 us-east-1에 CLOUDFRONT 스코프로 생성
aws wafv2 create-web-acl \
  --name "cloudfront-web-acl" \
  --scope CLOUDFRONT \
  --default-action Allow={} \
  --region us-east-1 \
  --rules '[
    {
      "Name": "RateLimitRule",
      "Priority": 0,
      "Statement": {
        "RateBasedStatement": {
          "Limit": 2000,
          "AggregateKeyType": "IP"
        }
      },
      "Action": { "Block": {} },
      "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "RateLimitRule"
      }
    }
  ]' \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=cloudfrontWebACL
```

### Web ACL을 ALB에 연동

```bash
# Web ACL 목록 확인
aws wafv2 list-web-acls --scope REGIONAL --region ap-northeast-2

# ALB에 Web ACL 연동
aws wafv2 associate-web-acl \
  --web-acl-arn arn:aws:wafv2:ap-northeast-2:123456789012:regional/webacl/production-web-acl/abc123 \
  --resource-arn arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/app/my-alb/1234567890abcdef
```

### IP Set을 활용한 화이트리스트/블랙리스트 구성

```bash
# IP Set 생성 (블랙리스트용)
aws wafv2 create-ip-set \
  --name "blocked-ips" \
  --scope REGIONAL \
  --ip-address-version IPV4 \
  --addresses "203.0.113.0/24" "198.51.100.0/24" \
  --region ap-northeast-2

# IP Set 생성 (화이트리스트용 - 사무실 IP)
aws wafv2 create-ip-set \
  --name "office-ips" \
  --scope REGIONAL \
  --ip-address-version IPV4 \
  --addresses "10.0.0.0/8" "172.16.0.0/12" \
  --region ap-northeast-2
```

### Python Boto3를 활용한 WAF 관리

```python
import boto3

wafv2 = boto3.client('wafv2', region_name='ap-northeast-2')

# 현재 Web ACL 목록 조회
response = wafv2.list_web_acls(Scope='REGIONAL')
for acl in response['WebACLs']:
    print(f"Name: {acl['Name']}, ARN: {acl['ARN']}")

# Web ACL에 연동된 리소스 확인
response = wafv2.list_resources_for_web_acl(
    WebACLArn='arn:aws:wafv2:ap-northeast-2:123456789012:regional/webacl/my-web-acl/abc123',
    ResourceType='APPLICATION_LOAD_BALANCER'
)
print(f"Associated ALBs: {response['ResourceArns']}")

# 관리형 규칙 그룹 목록 조회
managed_rules = wafv2.list_available_managed_rule_groups(Scope='REGIONAL')
for rule_group in managed_rules['ManagedRuleGroups']:
    if rule_group['VendorName'] == 'AWS':
        print(f"{rule_group['Name']}: {rule_group.get('Description', 'N/A')}")
```

### Geo Match 규칙으로 국가별 접근 제어

```json
{
  "Name": "GeoBlockRule",
  "Priority": 4,
  "Statement": {
    "GeoMatchStatement": {
      "CountryCodes": ["CN", "RU", "KP"]
    }
  },
  "Action": {"Block": {}},
  "VisibilityConfig": {
    "SampledRequestsEnabled": true,
    "CloudWatchMetricsEnabled": true,
    "MetricName": "GeoBlockRule"
  }
}
```

### 로깅 설정

```bash
# WAF 로깅 활성화 (S3로 전송 - 버킷 이름은 aws-waf-logs-로 시작해야 함)
aws wafv2 put-logging-configuration \
  --logging-configuration '{
    "ResourceArn": "arn:aws:wafv2:ap-northeast-2:123456789012:regional/webacl/production-web-acl/abc123",
    "LogDestinationConfigs": [
      "arn:aws:s3:::aws-waf-logs-my-bucket"
    ],
    "RedactedFields": [
      {"SingleHeader": {"Name": "authorization"}},
      {"SingleHeader": {"Name": "cookie"}}
    ]
  }'

# CloudWatch Logs로 전송하는 경우
aws wafv2 put-logging-configuration \
  --logging-configuration '{
    "ResourceArn": "arn:aws:wafv2:ap-northeast-2:123456789012:regional/webacl/production-web-acl/abc123",
    "LogDestinationConfigs": [
      "arn:aws:logs:ap-northeast-2:123456789012:log-group:aws-waf-logs-production"
    ]
  }'
```

## 모범 사례 및 보안

### 단계적 규칙 적용 (Count -> Block)

새로운 WAF 규칙을 적용할 때는 즉시 Block 모드로 설정하지 않는 것이 좋습니다. 먼저 Count 모드로 설정하여 1-2주간 모니터링한 후, 정상 트래픽이 오탐(false positive)으로 차단되지 않는 것을 확인한 다음에 Block 모드로 전환하는 것을 권장합니다.

### 로깅 및 모니터링 필수 활성화

AWS WAF 로그를 반드시 활성화하여 차단 및 허용된 요청에 대한 가시성을 확보해야 합니다. 로그는 Amazon S3, CloudWatch Logs, 또는 Amazon Kinesis Data Firehose로 전송할 수 있습니다. 민감한 헤더(Authorization, Cookie 등)는 RedactedFields를 통해 마스킹 처리하는 것을 권장합니다.

### CloudWatch 경보 설정

BlockedRequests 메트릭이 급증하면 공격이 진행 중일 가능성이 높으며, AllowedRequests가 급감하면 오탐 규칙이 적용되었을 가능성이 있습니다. CloudWatch 경보를 설정하여 이러한 이상 징후를 실시간으로 감지할 수 있도록 구성합니다.

### AWS Managed Rules 우선 적용

커스텀 규칙을 작성하기 전에 AWS Managed Rules를 먼저 적용하는 것을 권장합니다. AWS의 보안 전문가가 지속적으로 업데이트하는 규칙이므로 새로운 위협에 대한 빠른 대응이 가능합니다.

### WCU 한도 관리

각 규칙은 WCU를 소비하며, Web ACL당 기본 1,500 WCU까지 사용할 수 있습니다. 복잡한 규칙일수록 더 많은 WCU를 소비하므로, 규칙 구성 시 WCU 사용량을 모니터링하고 한도 증가가 필요한 경우 AWS Support에 요청합니다.

### 비용 구조 이해

| 항목 | 비용 |
|---|---|
| Web ACL | $5.00/월 |
| 규칙 (Rule) | $1.00/규칙/월 |
| 요청 수 | $0.60/100만 요청 |
| Bot Control | $10.00/월 + $1.00/100만 요청 |
| Account Takeover Prevention | $10.00/월 + 분석 건수당 과금 |

### 정기적인 규칙 검토

최소 분기별로 WAF 규칙을 검토하여 불필요한 규칙을 제거하고, 새로운 위협에 대응하는 규칙을 추가해야 합니다. 샘플링된 요청 데이터와 CloudWatch 메트릭을 활용하여 규칙의 효과성을 평가합니다.

## 관련 서비스 비교

| 서비스 | 동작 계층 | 주요 목적 | 특징 |
|---|---|---|---|
| AWS WAF | Layer 7 (HTTP) | 웹 애플리케이션 공격 방어 | SQL Injection, XSS, 봇 차단 등 HTTP 레벨 필터링 |
| AWS Shield | Layer 3/4 | DDoS 공격 방어 | SYN Flood, UDP Reflection 등 네트워크 레벨 DDoS 방어 |
| Security Group | Layer 3/4 | 인스턴스 레벨 방화벽 | Stateful, IP/포트 기반 인바운드/아웃바운드 제어 |
| Network ACL | Layer 3/4 | 서브넷 레벨 방화벽 | Stateless, IP/포트 기반, 서브넷 단위 적용 |
| AWS Network Firewall | Layer 3-7 | VPC 레벨 방화벽 | IPS/IDS, 도메인 필터링, Suricata 기반 상태 검사 |
| AWS Firewall Manager | 관리 계층 | 중앙 집중 보안 정책 관리 | 다수 계정/리소스에 WAF, Shield, SG 규칙 일괄 적용 |

### AWS WAF vs AWS Network Firewall

AWS WAF는 HTTP/HTTPS 트래픽에 특화된 웹 애플리케이션 방화벽인 반면, AWS Network Firewall은 VPC 레벨에서 모든 종류의 네트워크 트래픽을 검사할 수 있는 범용 방화벽입니다. 웹 애플리케이션 보호가 목적이라면 WAF를, VPC 전체의 네트워크 트래픽 제어가 목적이라면 Network Firewall을 선택합니다.

### AWS WAF vs Security Group

Security Group은 IP 주소와 포트 기반의 단순한 필터링만 가능하지만, AWS WAF는 HTTP 요청의 내용(헤더, 본문, URI 등)을 분석하여 애플리케이션 레벨 공격을 탐지할 수 있습니다. 두 서비스는 상호 보완적으로 함께 사용하는 것이 일반적입니다.

## 요약

AWS WAF는 Layer 7 기반의 관리형 웹 애플리케이션 방화벽으로, ALB, API Gateway, CloudFront, AppSync, Cognito User Pool, App Runner, Verified Access 등의 AWS 서비스에 연동하여 사용할 수 있습니다. 인바운드 HTTP 트래픽을 분석하여 SQL Injection, XSS, 악성 봇 등의 공격을 차단하며, AWS Managed Rules를 통해 별도의 규칙 작성 없이도 즉시 보호를 적용할 수 있습니다.

Web ACL은 CloudFront에 연동할 경우 글로벌 스코프(us-east-1, CLOUDFRONT)로, 그 외 서비스에는 리전 스코프(REGIONAL)로 생성해야 한다는 점을 반드시 기억해야 합니다. 효과적인 WAF 운영을 위해서는 Count 모드를 통한 단계적 규칙 적용, 로깅 활성화, CloudWatch 경보 설정, WCU 한도 관리 등의 모범 사례를 준수하는 것이 중요합니다.

아웃바운드 트래픽 필터링은 WAF의 영역이 아니므로, 필요한 경우 Security Group, Network ACL, AWS Network Firewall 등을 별도로 구성하여 다층 방어(Defense in Depth) 체계를 구축하는 것을 권장합니다.