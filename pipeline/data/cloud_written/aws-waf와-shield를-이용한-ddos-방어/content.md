# AWS WAF와 Shield를 이용한 DDoS 방어 - 웹 애플리케이션 보안 전략

## 개요

AWS WAF(Web Application Firewall)와 AWS Shield는 웹 애플리케이션과 인프라를 DDoS(Distributed Denial of Service) 공격으로부터 보호하는 AWS의 핵심 보안 서비스입니다. WAF는 Layer 7(애플리케이션 계층) 수준의 웹 요청을 필터링하고, Shield는 Layer 3/4(네트워크/전송 계층) 수준의 볼류메트릭 공격을 자동으로 탐지하고 완화합니다.

두 서비스를 결합하면 네트워크 수준의 대용량 트래픽 공격부터 애플리케이션 수준의 정교한 공격까지 다계층 방어 체계를 구축할 수 있습니다. 특히 CloudFront, ALB, API Gateway 등 AWS 엣지 서비스와 통합하여 공격 트래픽을 오리진에 도달하기 전에 차단하는 것이 핵심 전략입니다.

## 핵심 기능

### AWS Shield

AWS Shield는 두 가지 티어를 제공합니다.

| 항목 | Shield Standard | Shield Advanced |
|------|----------------|----------------|
| 비용 | 무료 (모든 AWS 계정) | 월 $3,000 + 데이터 전송 |
| 보호 계층 | Layer 3/4 | Layer 3/4/7 |
| 자동 탐지 | SYN Flood, UDP Reflection 등 | 고급 탐지 + ML 기반 이상 감지 |
| DRT 지원 | 미지원 | 24/7 DDoS Response Team 접근 |
| 비용 보호 | 미지원 | DDoS로 인한 스케일링 비용 크레딧 |
| 가시성 | 미지원 | CloudWatch 메트릭, 공격 진단 |
| 사전 대응 | 미지원 | Proactive Engagement (사전 연락) |
| 적용 대상 | 모든 AWS 리소스 | CloudFront, ALB, NLB, EIP, Global Accelerator |

**Shield Standard**는 모든 AWS 계정에 자동으로 적용되며, SYN Flood, UDP Reflection, DNS Amplification 등 일반적인 Layer 3/4 DDoS 공격을 자동으로 탐지하고 완화합니다.

**Shield Advanced**는 대규모 공격에 대한 추가 보호, 실시간 공격 가시성, DDoS Response Team(DRT)의 전문가 지원, 공격으로 인한 비용 보호를 제공합니다.

### AWS WAF

AWS WAF는 웹 요청을 검사하여 악의적인 트래픽을 차단하는 Layer 7 방화벽입니다.

#### 적용 가능 리소스

- Amazon CloudFront Distribution
- Application Load Balancer (ALB)
- Amazon API Gateway REST API
- AWS AppSync GraphQL API
- Amazon Cognito User Pool
- AWS App Runner Service
- AWS Verified Access Instance

#### WAF 구성 요소

| 구성 요소 | 설명 |
|-----------|------|
| Web ACL | WAF 규칙의 컨테이너, 리소스에 연결 |
| Rule | 요청 검사 조건 + 액션 (Allow/Block/Count) |
| Rule Group | 규칙의 재사용 가능한 모음 |
| Managed Rule Group | AWS/마켓플레이스 제공 사전 정의 규칙 |
| IP Set | 허용/차단할 IP 주소 목록 |
| Regex Pattern Set | 정규식 패턴 집합 |

#### 주요 WAF 규칙 유형

- **Rate-based Rule**: 5분 간 IP당 요청 수 제한 (최소 100~최대 20억)
- **Geographic Match**: 특정 국가의 요청 차단/허용
- **IP Set Match**: 특정 IP 범위 차단/허용
- **String Match**: URI, 헤더, 바디 내 문자열 매칭
- **Size Constraint**: 요청 크기 기반 필터링
- **SQL Injection**: SQL 인젝션 패턴 탐지
- **XSS**: 크로스 사이트 스크립팅 패턴 탐지

### AWS Managed Rules

AWS가 관리하는 사전 정의 규칙 그룹으로, 별도의 규칙 작성 없이 활성화할 수 있습니다.

| 규칙 그룹 | 용도 |
|-----------|------|
| AWSManagedRulesCommonRuleSet | OWASP Top 10 일반 위협 |
| AWSManagedRulesKnownBadInputsRuleSet | 알려진 악성 입력 패턴 |
| AWSManagedRulesSQLiRuleSet | SQL 인젝션 방어 |
| AWSManagedRulesLinuxRuleSet | Linux 관련 취약점 |
| AWSManagedRulesAmazonIpReputationList | 악성 IP 평판 목록 |
| AWSManagedRulesBotControlRuleSet | 봇 트래픽 관리 |
| AWSManagedRulesATPRuleSet | 계정 탈취 방지 |

## 아키텍처 및 동작 원리

### 다계층 DDoS 방어 아키텍처

```
[공격 트래픽]
    |
    v
[Layer 3/4: AWS Shield Standard/Advanced]
    |  SYN Flood, UDP Reflection, DNS Amplification 자동 완화
    v
[CloudFront Edge Location]
    |  글로벌 분산으로 공격 트래픽 흡수
    v
[AWS WAF (Web ACL)]
    |  Layer 7 규칙 적용
    |  +-- Rate Limiting (IP당 요청 수 제한)
    |  +-- Managed Rules (SQL Injection, XSS 차단)
    |  +-- Geo Blocking (국가별 차단)
    |  +-- Bot Control (봇 트래픽 관리)
    |  +-- Custom Rules (비즈니스 로직 기반)
    v
[ALB / API Gateway]
    |  정상 트래픽만 전달
    v
[EC2 / Lambda / ECS]
    (오리진 서버)
```

### Shield Advanced의 ML 기반 탐지

Shield Advanced는 보호 대상 리소스의 정상 트래픽 패턴을 학습하고, 이상 트래픽을 자동으로 탐지합니다. HTTP Flood, Slowloris 등 Layer 7 DDoS 공격도 탐지할 수 있으며, 탐지된 공격에 대해 자동 완화 규칙을 WAF에 적용합니다.

## 실전 활용

### AWS CLI를 사용한 WAF 구성

```bash
# IP Set 생성 (차단할 IP 목록)
aws wafv2 create-ip-set \
    --name blocked-ips \
    --scope REGIONAL \
    --ip-address-version IPV4 \
    --addresses '["203.0.113.0/24", "198.51.100.0/24"]'

# Web ACL 생성 (Rate Limiting + Managed Rules)
aws wafv2 create-web-acl \
    --name production-waf \
    --scope REGIONAL \
    --default-action '{"Allow": {}}' \
    --rules '[
        {
            "Name": "RateLimit-1000",
            "Priority": 1,
            "Statement": {
                "RateBasedStatement": {
                    "Limit": 1000,
                    "AggregateKeyType": "IP"
                }
            },
            "Action": {"Block": {}},
            "VisibilityConfig": {
                "SampledRequestsEnabled": true,
                "CloudWatchMetricsEnabled": true,
                "MetricName": "RateLimit1000"
            }
        },
        {
            "Name": "AWS-CommonRules",
            "Priority": 2,
            "Statement": {
                "ManagedRuleGroupStatement": {
                    "VendorName": "AWS",
                    "Name": "AWSManagedRulesCommonRuleSet"
                }
            },
            "OverrideAction": {"None": {}},
            "VisibilityConfig": {
                "SampledRequestsEnabled": true,
                "CloudWatchMetricsEnabled": true,
                "MetricName": "AWSCommonRules"
            }
        },
        {
            "Name": "AWS-IPReputation",
            "Priority": 3,
            "Statement": {
                "ManagedRuleGroupStatement": {
                    "VendorName": "AWS",
                    "Name": "AWSManagedRulesAmazonIpReputationList"
                }
            },
            "OverrideAction": {"None": {}},
            "VisibilityConfig": {
                "SampledRequestsEnabled": true,
                "CloudWatchMetricsEnabled": true,
                "MetricName": "AWSIPReputation"
            }
        },
        {
            "Name": "AWS-SQLInjection",
            "Priority": 4,
            "Statement": {
                "ManagedRuleGroupStatement": {
                    "VendorName": "AWS",
                    "Name": "AWSManagedRulesSQLiRuleSet"
                }
            },
            "OverrideAction": {"None": {}},
            "VisibilityConfig": {
                "SampledRequestsEnabled": true,
                "CloudWatchMetricsEnabled": true,
                "MetricName": "AWSSQLInjection"
            }
        }
    ]' \
    --visibility-config '{
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "ProductionWAF"
    }'

# Web ACL을 ALB에 연결
aws wafv2 associate-web-acl \
    --web-acl-arn arn:aws:wafv2:ap-northeast-2:123456789012:regional/webacl/production-waf/abc123 \
    --resource-arn arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/app/my-alb/abc123

# WAF 로깅 활성화 (S3)
aws wafv2 put-logging-configuration \
    --logging-configuration '{
        "ResourceArn": "arn:aws:wafv2:ap-northeast-2:123456789012:regional/webacl/production-waf/abc123",
        "LogDestinationConfigs": [
            "arn:aws:s3:::aws-waf-logs-my-bucket"
        ]
    }'

# 차단된 요청 샘플 확인
aws wafv2 get-sampled-requests \
    --web-acl-arn arn:aws:wafv2:ap-northeast-2:123456789012:regional/webacl/production-waf/abc123 \
    --rule-metric-name RateLimit1000 \
    --scope REGIONAL \
    --time-window '{"StartTime":"2024-01-01T00:00:00Z","EndTime":"2024-01-02T00:00:00Z"}' \
    --max-items 10
```

### Shield Advanced 활성화

```bash
# Shield Advanced 구독 (월 $3,000)
aws shield create-subscription

# 보호 대상 리소스 추가
aws shield create-protection \
    --name production-alb \
    --resource-arn arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/app/my-alb/abc123

# 보호 상태 확인
aws shield list-protections \
    --query 'Protections[].{Name:Name,Resource:ResourceArn}' \
    --output table

# DDoS 공격 이벤트 확인
aws shield list-attacks \
    --start-time '{"FromInclusive":"2024-01-01T00:00:00Z","ToExclusive":"2024-01-02T00:00:00Z"}' \
    --query 'AttackSummaries[].{Id:AttackId,Resource:ResourceArn,Vectors:AttackVectors[].VectorType,Start:StartTime}'

# Shield Advanced 자동 Layer 7 DDoS 완화 활성화
aws shield enable-application-layer-automatic-response \
    --resource-arn arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/app/my-alb/abc123 \
    --action '{"Block": {}}'
```

## 모범 사례 및 보안

### DDoS 방어 아키텍처 설계 원칙

- CloudFront를 최전방에 배치하여 글로벌 엣지에서 공격 트래픽을 흡수합니다. CloudFront에는 Shield Standard가 자동 적용됩니다.
- WAF Web ACL을 CloudFront와 ALB 모두에 적용하여 이중 방어합니다.
- Rate-based Rule을 가장 높은 우선순위로 설정하여 IP당 요청 수를 제한합니다.
- AWS Managed Rules를 기본 적용하고, 비즈니스 로직에 맞는 커스텀 규칙을 추가합니다.

### WAF 규칙 우선순위 권장 순서

1. IP 차단 목록 (알려진 악성 IP)
2. Rate Limiting (IP당 요청 수 제한)
3. AWS Managed Rules (OWASP, SQL Injection, XSS)
4. Geographic Blocking (필요 시)
5. Custom Rules (비즈니스 로직)
6. Default Action: Allow

### 비용 최적화

- Shield Standard는 무료이므로 모든 환경에서 활용합니다.
- Shield Advanced는 월 $3,000의 고정 비용이 발생하므로, 비즈니스 크리티컬 워크로드에만 적용합니다.
- WAF는 Web ACL, Rule, 요청 수 기준으로 과금되므로, 불필요한 규칙을 정리합니다.
- WAF 로깅은 S3에 저장하되, 로그 수명주기 정책을 설정하여 오래된 로그를 자동 삭제합니다.

### 모니터링 및 대응

- CloudWatch 대시보드에 WAF 메트릭(AllowedRequests, BlockedRequests, CountedRequests)을 추가합니다.
- Rate Limiting으로 차단된 IP를 분석하여 정상 사용자의 오탐(False Positive)을 확인합니다.
- Shield Advanced의 Proactive Engagement를 활성화하면, 대규모 공격 감지 시 AWS DRT가 선제적으로 연락합니다.
- WAF 로그를 Athena로 분석하여 공격 패턴을 식별하고 규칙을 개선합니다.

## 관련 서비스 비교

| 항목 | AWS WAF | AWS Shield Standard | AWS Shield Advanced | Security Groups | Network ACL |
|------|---------|--------------------|--------------------|-----------------|-------------|
| 보호 계층 | Layer 7 | Layer 3/4 | Layer 3/4/7 | Layer 4 | Layer 3/4 |
| DDoS 방어 | 부분적 (Rate Limit) | 기본 자동 | 고급 자동 + ML | 미지원 | 미지원 |
| 규칙 커스터마이징 | 완전 지원 | 미지원 | WAF 연동 | IP/포트 기반 | IP/포트 기반 |
| 비용 | Web ACL + 규칙 + 요청 | 무료 | 월 $3,000 | 무료 | 무료 |
| 적용 대상 | CloudFront, ALB, APIGW | 모든 AWS 리소스 | CF, ALB, NLB, EIP | EC2, ENI | 서브넷 |

## 요약

AWS WAF와 Shield를 결합하면 Layer 3부터 Layer 7까지 포괄적인 DDoS 방어 체계를 구축할 수 있습니다. Shield Standard는 무료로 모든 AWS 계정에 적용되어 기본적인 네트워크 계층 공격을 자동 완화하며, WAF는 Rate Limiting, Managed Rules, 커스텀 규칙을 통해 애플리케이션 계층 공격을 차단합니다. CloudFront를 최전방에 배치하고, WAF를 ALB와 CloudFront 모두에 적용하여 이중 방어를 구축하는 것이 핵심 모범 사례입니다. 비즈니스 크리티컬 워크로드에는 Shield Advanced를 추가하여 24/7 DRT 지원과 비용 보호를 확보할 수 있습니다.