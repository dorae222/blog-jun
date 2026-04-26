<!-- infographic-hero -->
![Amazon ELB와 Application Load Balancer 개요 핵심 요약](figures/infographic.svg)

*Figure: Amazon ELB와 Application Load Balancer 개요 한 장 요약 인포그래픽*

# Amazon ELB와 Application Load Balancer 개요

## 개요

Amazon Elastic Load Balancing(ELB)은 AWS가 제공하는 완전 관리형 로드 밸런싱 서비스 군으로, 들어오는 트래픽을 여러 대상(Target)에 자동으로 분산시켜 가용성과 확장성을 확보합니다. ELB는 트래픽 폭주에도 자동으로 확장되며, 비정상 인스턴스를 자동으로 격리합니다. 모든 ELB는 Multi-AZ 배포를 기본으로 하므로 단일 가용 영역(AZ) 장애에도 서비스가 지속됩니다.

ELB는 다음 4가지 종류로 구성됩니다.

| 종류 | 계층 | 프로토콜 | 주요 사용 사례 |
|------|------|----------|----------------|
| Application Load Balancer (ALB) | L7 | HTTP, HTTPS, gRPC, WebSocket | 마이크로서비스, 웹 API, 컨테이너 |
| Network Load Balancer (NLB) | L4 | TCP, UDP, TLS | 게임, IoT, 초저 지연/고처리량 |
| Gateway Load Balancer (GWLB) | L3 | IP / GENEVE 캡슐화 | 가상 어플라이언스(방화벽, IDS/IPS) |
| Classic Load Balancer (CLB) | L4/L7 | HTTP, HTTPS, TCP, SSL | 레거시 (사용 권장 안 함) |

CLB는 EC2 Classic 시대의 잔재로 신규 워크로드에서는 사용하지 않습니다. 대부분의 웹/API 트래픽은 ALB를, 초저 지연이나 TCP 기반 워크로드는 NLB를 선택하는 것이 표준입니다.

이 문서에서는 ELB 전체 종류를 비교하면서 ALB의 L7 라우팅 기능을 중심으로 다룹니다.

---

## 핵심 기능

### 1. Application Load Balancer (ALB)

ALB는 OSI 7계층(Application Layer)에서 동작하며, HTTP 요청의 내용을 검사하여 라우팅을 결정합니다.

**주요 기능**

- 경로(Path) 기반 라우팅: `/api/*` → API 서비스, `/static/*` → 정적 콘텐츠
- 호스트(Host Header) 기반 라우팅: `api.example.com` 과 `web.example.com` 분리
- HTTP 헤더, 쿼리 스트링, 메서드, 소스 IP 기반 라우팅
- HTTP/2, gRPC, WebSocket 지원
- 서버 이름 표시(SNI) 기반 다중 인증서
- AWS WAF, Cognito, OIDC 통합
- Lambda 함수를 직접 Target으로 등록 가능
- 컨테이너용 동적 포트 매핑(ECS service)

### 2. Listener와 Listener Rule

ALB의 라우팅은 Listener와 Listener Rule로 구성됩니다.

- **Listener**: 프로토콜과 포트 조합(예: HTTPS:443)에서 들어오는 연결을 수신합니다.
- **Listener Rule**: Listener 내에서 조건과 액션의 우선순위 목록을 평가합니다.

| 조건(Condition) | 예시 |
|-----------------|------|
| host-header | `*.example.com` |
| path-pattern | `/api/v1/*` |
| http-header | `X-Custom-Header: foo` |
| http-request-method | `POST` |
| query-string | `user_id=*` |
| source-ip | `203.0.113.0/24` |

| 액션(Action) | 동작 |
|--------------|------|
| forward | Target Group으로 전달 |
| redirect | 다른 URL로 리다이렉트 (HTTP→HTTPS 강제) |
| fixed-response | 고정된 본문/상태 코드 반환 |
| authenticate-cognito | Cognito 사용자 풀로 인증 |
| authenticate-oidc | 외부 OIDC IdP 인증 |

```bash
# Listener Rule: /api/* 경로를 api-tg로 라우팅
aws elbv2 create-rule \
  --listener-arn arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:listener/app/my-alb/abc/def \
  --priority 10 \
  --conditions '[{"Field":"path-pattern","Values":["/api/*"]}]' \
  --actions '[{"Type":"forward","TargetGroupArn":"arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:targetgroup/api-tg/abcdef"}]' \
  --region ap-northeast-2
```

### 3. Target Group

Target Group은 트래픽을 받을 대상의 묶음입니다. ALB는 다음 Target 유형을 지원합니다.

| 타입 | 대상 |
|------|------|
| instance | EC2 인스턴스 ID |
| ip | VPC 내 IP 주소 (Fargate, 온프레미스 IP via DX/VPN) |
| lambda | Lambda 함수 |
| alb | 다른 ALB (ALB-to-NLB 체이닝의 반대) |

각 Target Group은 자체 Health Check 정책, Sticky Session 설정, Deregistration Delay를 가집니다.

```bash
# IP 타입 Target Group 생성 (Fargate용)
aws elbv2 create-target-group \
  --name api-tg \
  --protocol HTTP \
  --port 8080 \
  --vpc-id vpc-0123456789abcdef0 \
  --target-type ip \
  --health-check-protocol HTTP \
  --health-check-path /health \
  --health-check-interval-seconds 15 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3 \
  --region ap-northeast-2
```

### 4. SSL/TLS Termination과 ACM 통합

ALB는 HTTPS Listener에서 TLS 종료(Termination)를 수행합니다. 인증서는 AWS Certificate Manager(ACM) 또는 IAM에 업로드한 인증서를 사용합니다. ACM은 무료로 발급되며 자동 갱신되므로 표준 옵션입니다.

- **SNI(Server Name Indication)**: 단일 ALB에 여러 인증서를 연결하고 호스트명에 따라 선택합니다.
- **Security Policy**: TLS 버전과 암호화 스위트 조합을 선택합니다(예: `ELBSecurityPolicy-TLS13-1-2-2021-06`).
- **mTLS(Mutual TLS)**: 클라이언트 인증서 검증 지원.

```bash
# HTTPS Listener 생성
aws elbv2 create-listener \
  --load-balancer-arn arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/app/my-alb/abc \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:ap-northeast-2:123456789012:certificate/abcd-efgh \
  --ssl-policy ELBSecurityPolicy-TLS13-1-2-2021-06 \
  --default-actions Type=forward,TargetGroupArn=arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:targetgroup/web-tg/xyz \
  --region ap-northeast-2
```

### 5. Sticky Session과 Cross-zone Load Balancing

**Sticky Session (Session Affinity)**

- ALB가 발급한 쿠키(`AWSALB`)로 동일 클라이언트를 같은 타깃으로 라우팅합니다.
- 애플리케이션 쿠키 기반 stickiness도 지원합니다.
- 세션 상태를 외부에 저장하지 않은 레거시 애플리케이션에 유용합니다.

**Cross-zone Load Balancing**

- 모든 AZ의 모든 타깃에 트래픽을 균등 분산합니다.
- ALB는 항상 활성화(무료), NLB는 옵션(데이터 처리 요금 추가).

### 6. Network Load Balancer (NLB)

NLB는 OSI 4계층(Transport Layer)에서 동작하며, ALB가 처리할 수 없는 요구사항을 커버합니다.

- 초당 수백만 요청 처리 가능
- 마이크로초 수준의 매우 낮은 지연 시간
- 정적 IP 또는 Elastic IP 할당 가능 (방화벽 화이트리스트에 유리)
- 프로토콜: TCP, UDP, TLS, TCP_UDP
- 클라이언트 IP가 그대로 보존됨 (X-Forwarded-For 불필요)
- TLS 종료 지원

ALB는 클라이언트 IP를 X-Forwarded-For 헤더로 전달하지만 NLB는 IP 자체가 보존되어 백엔드에서 그대로 보입니다.

### 7. Gateway Load Balancer (GWLB)

GWLB는 가상 네트워크 어플라이언스(방화벽, 침입 탐지 시스템, 트래픽 분석기)를 투명하게 배포하는 데 특화된 로드 밸런서입니다.

- L3 IP 패킷을 GENEVE(UDP 6081)로 캡슐화하여 어플라이언스로 전달.
- 어플라이언스 풀의 자동 확장과 헬스 체크 제공.
- VPC Endpoint(GWLBe)로 트래픽 라우팅을 단순화.

엔터프라이즈 보안 어플라이언스 통합 시나리오 외에는 직접 다룰 일이 적습니다.

---

## 아키텍처

### ALB 내부 동작

```
[Client]
   |
   v
[ALB DNS (AAAA + A)]
   |
   v
[ALB Node (AZ별)] ─── Listener (HTTPS:443)
   |                        |
   |                  Listener Rule 평가
   |                        |
   |                +-------+--------+
   |                | Path? Host?    |
   |                +-------+--------+
   |                        |
   v                        v
[Target Group]      Forward / Redirect / Auth
   |
   v
[EC2 / Fargate / Lambda / IP]
```

1. Route 53이 ALB의 DNS 이름(이중 스택)을 응답합니다.
2. 클라이언트는 ALB가 위치한 AZ 중 하나의 ENI로 연결합니다.
3. ALB가 Listener Rule을 우선순위에 따라 평가하고 Target Group으로 forward합니다.
4. Target Group은 자체 Health Check 결과를 기반으로 정상 타깃에만 트래픽을 분배합니다.

### 헬스 체크 동작

ALB는 Target Group마다 정의된 헬스 체크 경로(예: `/health`)에 주기적으로 HTTP 요청을 보냅니다.

- HealthCheckIntervalSeconds: 헬스 체크 주기 (기본 30초)
- HealthyThresholdCount: 연속 성공 횟수 (기본 5회)
- UnhealthyThresholdCount: 연속 실패 횟수 (기본 2회)
- Matcher: 정상으로 간주할 HTTP 코드 (기본 200)

비정상 판정 시 Target은 트래픽을 받지 않으며, Deregistration Delay(기본 300초) 동안 기존 연결을 마무리한 뒤 제외됩니다.

### Connection Draining (Deregistration Delay)

배포 시 인스턴스를 제거하면 ALB는 즉시 트래픽 차단을 시작하지만, 진행 중인 요청은 Deregistration Delay 동안 정상 처리합니다. 이 값을 너무 길게 잡으면 배포가 느려지고, 너무 짧으면 사용자 요청이 끊깁니다. 보통 30~60초가 적절합니다.

---

## 실전 사용

### 1. Terraform으로 ALB + Target Group 구성

```hcl
resource "aws_lb" "app" {
  name               = "prod-app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets

  enable_deletion_protection = true
  enable_http2               = true
  idle_timeout               = 60

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "alb"
    enabled = true
  }

  tags = {
    Environment = "production"
  }
}

resource "aws_lb_target_group" "web" {
  name        = "web-tg"
  port        = 8080
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = module.vpc.vpc_id

  health_check {
    path                = "/health"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
  }

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 86400
    enabled         = true
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.app.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

# HTTP -> HTTPS 리다이렉트
resource "aws_lb_listener" "http_redirect" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}
```

### 2. 경로 기반 라우팅 + 호스트 라우팅 조합

```hcl
resource "aws_lb_listener_rule" "api_v1" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10

  condition {
    host_header {
      values = ["api.example.com"]
    }
  }

  condition {
    path_pattern {
      values = ["/v1/*"]
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_v1.arn
  }
}

resource "aws_lb_listener_rule" "api_v2" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 20

  condition {
    host_header {
      values = ["api.example.com"]
    }
  }

  condition {
    path_pattern {
      values = ["/v2/*"]
    }
  }

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api_v2.arn
  }
}
```

### 3. 가중치 기반 카나리 배포

ALB는 단일 Listener Rule 내에서 여러 Target Group에 가중치를 분배할 수 있습니다.

```bash
aws elbv2 modify-listener \
  --listener-arn $LISTENER_ARN \
  --default-actions '[{
    "Type": "forward",
    "ForwardConfig": {
      "TargetGroups": [
        {"TargetGroupArn": "arn:.../stable-tg/...", "Weight": 90},
        {"TargetGroupArn": "arn:.../canary-tg/...", "Weight": 10}
      ]
    }
  }]' \
  --region ap-northeast-2
```

### 4. WAF + Cognito 통합

ALB 앞단에 AWS WAF를 연결하여 SQL Injection, XSS, 봇 공격을 차단합니다. 또한 `authenticate-cognito` 액션으로 사용자 인증을 ALB 레벨에서 강제할 수 있어, 백엔드는 인증 로직을 구현하지 않아도 됩니다.

```bash
aws wafv2 associate-web-acl \
  --web-acl-arn arn:aws:wafv2:ap-northeast-2:123456789012:regional/webacl/my-waf/abc \
  --resource-arn arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/app/my-alb/abc \
  --region ap-northeast-2
```

---

## 가격 / 한도

### 주요 비용 (서울 리전 기준)

| 항목 | ALB | NLB |
|------|-----|-----|
| 시간당 고정 | $0.0225 | $0.0225 |
| 사용량 단위 | LCU | NLCU |
| LCU/NLCU 가격 | $0.008 / 시간 | $0.006 / 시간 |
| 데이터 전송 | EC2 표준 요금 | 동일 |

LCU(Load Balancer Capacity Unit)는 다음 4가지 요소 중 가장 큰 값으로 산정됩니다.

- 새 연결 수 / 초
- 활성 연결 수 / 분
- 처리 바이트 / 시간
- Listener Rule 평가 수

대부분의 워크로드에서는 처리 바이트가 지배적인 요소입니다.

### 주요 한도

| 항목 | ALB | NLB |
|------|-----|-----|
| Listener 수 | 50 | 50 |
| Listener Rule 수 (LB당) | 100 (Soft) | - |
| Target Group 수 (LB당) | 100 | 50 |
| Target Group당 타깃 | 1,000 | 500 |
| 인증서 수 (Listener당) | 25 | 25 |
| Idle Timeout 최대 | 4,000초 | 350초 |

---

## Best Practice

### 설계

1. **ALB 우선, 필요 시 NLB**: HTTP 트래픽은 ALB를 표준으로 채택합니다.
2. **WAF 통합**: 인터넷 노출 ALB는 WAF를 반드시 연결합니다.
3. **HTTP→HTTPS 강제**: HTTP Listener는 항상 301 리다이렉트만 수행합니다.
4. **TLS 1.2 이상**: SSL/TLS 정책을 최신 버전으로 유지합니다.
5. **다중 AZ 서브넷**: 최소 2개, 권장 3개의 AZ에 ALB 서브넷을 배치합니다.

### 운영

1. **Access Log를 S3에 저장**: 디버깅과 보안 분석에 필수입니다.
2. **Target Group 모니터링**: `HealthyHostCount`, `TargetResponseTime`, `HTTPCode_Target_5XX_Count` 알람을 설정합니다.
3. **Connection Draining 적절히**: 30~60초가 일반적입니다.
4. **Deletion Protection 활성화**: 프로덕션 ALB는 실수 삭제 방지를 활성화합니다.
5. **Cognito 인증 액션 활용**: 내부 도구 보호에 매우 효율적입니다.

### 비용 최적화

1. **불필요한 ALB 통합**: 마이크로서비스마다 ALB를 두지 말고, Listener Rule로 통합합니다.
2. **Target Group 재사용**: 같은 백엔드를 여러 Listener에서 공유합니다.
3. **Idle Timeout 조정**: 장기 연결이 필요 없다면 60초로 유지해 LCU 사용량을 줄입니다.
4. **Lambda Target Group 검토**: 트래픽이 적은 백엔드는 Lambda + ALB 조합이 EC2보다 저렴할 수 있습니다.

### 보안

1. **SG 인/아웃 모두 정의**: ALB SG는 `0.0.0.0/0:443`만, App SG는 ALB SG에서만 허용.
2. **mTLS 옵션**: B2B API에서 클라이언트 검증이 필요하면 활용.
3. **OIDC 통합**: Cognito 외 IdP(Auth0, Okta)도 OIDC 액션으로 인증 가능.
4. **Drop Invalid Header Fields**: HTTP 헤더 위장 공격 방지 옵션을 활성화합니다.

---

## 관련 서비스

| 서비스 | 관계 |
|--------|------|
| Amazon Route 53 | ALB DNS를 Alias 레코드로 매핑 |
| AWS Certificate Manager | ALB HTTPS Listener 인증서 무료 발급 |
| AWS WAF | L7 위협 차단 (ALB와 직접 연결) |
| Amazon Cognito | ALB 레벨 사용자 인증 |
| Amazon ECS / EKS | 컨테이너 워크로드의 표준 LB |
| AWS Auto Scaling | Target Tracking으로 타깃 그룹의 RequestCount 기반 스케일링 |
| AWS Global Accelerator | 글로벌 Anycast IP를 ALB/NLB 앞단에 배치 |

> ALBERT(자연어 처리 모델)와 본 글의 ALB는 약자가 비슷할 뿐 무관합니다. 검색 시 혼동하지 않도록 주의하세요.

---

## 관련 문서

- [[amazon-vpc-virtual-private-cloud-개요|Amazon VPC]] - ALB가 배치되는 네트워크 환경
- [[amazon-route-53-dns-서비스-개요|Amazon Route 53]] - ALB Alias 레코드 매핑
- [[amazon-cloudfront|Amazon CloudFront]] - ALB 앞단의 CDN
- [[amazon-elastic-container-service-amazon-ecs|Amazon ECS]] - ALB Target Group 기반 컨테이너 라우팅
- [[amazon-eks-elastic-kubernetes-service-개요|Amazon EKS]] - AWS Load Balancer Controller로 ALB 자동 프로비저닝
