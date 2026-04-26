<!-- infographic-hero -->
![Amazon VPC (Virtual Private Cloud) 개요 핵심 요약](figures/infographic.svg)

*Figure: Amazon VPC (Virtual Private Cloud) 개요 한 장 요약 인포그래픽*

# Amazon VPC (Virtual Private Cloud) 개요

## 개요

Amazon VPC(Virtual Private Cloud)는 AWS가 2009년에 출시한 격리된 가상 네트워크 서비스입니다. 사용자는 자체 IP 주소 범위, 서브넷, 라우팅 테이블, 네트워크 게이트웨이를 정의하여 AWS 클라우드 위에 논리적으로 분리된 네트워크를 구성할 수 있습니다. 모든 EC2, RDS, Lambda(VPC 모드), ECS 등 대부분의 AWS 리소스는 VPC 내부에 배치되어 동작하며, VPC는 AWS 인프라의 가장 기본이 되는 네트워크 빌딩 블록입니다.

VPC가 제공하는 핵심 가치는 다음과 같습니다.

- **격리성(Isolation)**: 각 VPC는 다른 고객의 트래픽과 완전히 분리됩니다.
- **유연한 IP 설계**: RFC 1918 사설 IP 범위를 자유롭게 할당할 수 있습니다.
- **세분화된 보안 통제**: Security Group과 NACL로 인스턴스 단위/서브넷 단위 통제가 가능합니다.
- **하이브리드 연결**: VPN, Direct Connect로 온프레미스와 안전하게 연결됩니다.
- **서비스 통합**: VPC Endpoint를 통해 AWS 서비스와 프라이빗하게 통신할 수 있습니다.

VPC를 처음 설계할 때는 향후 확장 가능성, 다른 VPC 또는 온프레미스와의 연결, 운영 환경(prod/stage/dev) 분리 전략을 종합적으로 고려해야 합니다.

---

## 핵심 기능

### 1. CIDR 블록과 IP 주소 체계

VPC 생성 시 CIDR(Classless Inter-Domain Routing) 블록을 지정합니다.

- **IPv4**: `/16`(65,536개) ~ `/28`(16개) 범위 지원. RFC 1918 사설 대역 사용 권장.
- **IPv6**: `/56` 블록을 AWS가 할당하거나 BYOIP 가능.
- VPC당 최대 5개의 IPv4 CIDR 블록 추가 가능(Secondary CIDR).

권장 사설 대역은 다음과 같습니다.

| 범위 | 크기 | 용도 |
|------|------|------|
| `10.0.0.0/8` | 16,777,216 IP | 대규모 조직 |
| `172.16.0.0/12` | 1,048,576 IP | 중규모 조직 |
| `192.168.0.0/16` | 65,536 IP | 소규모 조직 |

> AWS는 각 서브넷에서 처음 4개 IP와 마지막 1개 IP를 예약합니다(예: `/24` 서브넷은 256개 중 251개만 사용 가능).

### 2. 서브넷 (Subnet)

서브넷은 VPC 내부를 가용 영역(AZ) 단위로 분할한 네트워크 세그먼트입니다. AZ별로 분리해야 고가용성이 확보됩니다. 일반적으로 다음 세 가지 유형으로 구분합니다.

| 유형 | 라우팅 | 용도 |
|------|--------|------|
| Public Subnet | Internet Gateway 라우트 보유 | ALB, NAT Gateway, Bastion Host |
| Private Subnet | NAT Gateway 라우트 (아웃바운드) | 애플리케이션 서버, ECS, Lambda |
| Isolated Subnet | 인터넷 라우트 없음 | RDS, ElastiCache, 내부 데이터 저장소 |

```bash
# VPC 생성
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=prod-vpc}]" \
  --region ap-northeast-2

# Public Subnet (AZ a)
aws ec2 create-subnet \
  --vpc-id vpc-0123456789abcdef0 \
  --cidr-block 10.0.1.0/24 \
  --availability-zone ap-northeast-2a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=prod-public-2a}]" \
  --region ap-northeast-2

# Private Subnet (AZ a)
aws ec2 create-subnet \
  --vpc-id vpc-0123456789abcdef0 \
  --cidr-block 10.0.10.0/24 \
  --availability-zone ap-northeast-2a \
  --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=prod-private-2a}]" \
  --region ap-northeast-2
```

### 3. 라우팅 (Route Table)

라우팅 테이블은 서브넷의 트래픽이 어디로 향할지 결정합니다. 각 서브넷은 정확히 하나의 라우팅 테이블에 연결되며, 같은 라우팅 테이블이 여러 서브넷에 연결될 수 있습니다.

| 컴포넌트 | 역할 |
|----------|------|
| Internet Gateway (IGW) | VPC와 인터넷을 연결하는 양방향 게이트웨이 |
| NAT Gateway | Private Subnet에서 인터넷으로 아웃바운드만 허용 |
| Egress-only IGW | IPv6 전용. 아웃바운드만 허용 |
| Virtual Private Gateway (VGW) | VPN 연결 종단점 |
| Transit Gateway Attachment | TGW로 향하는 라우트 |
| VPC Endpoint | AWS 서비스(S3 등)로 향하는 프라이빗 라우트 |

```bash
# Internet Gateway 생성 및 VPC 연결
aws ec2 create-internet-gateway --region ap-northeast-2
aws ec2 attach-internet-gateway \
  --internet-gateway-id igw-0123456789abcdef0 \
  --vpc-id vpc-0123456789abcdef0 \
  --region ap-northeast-2

# Public Subnet 라우팅 테이블에 IGW 라우트 추가
aws ec2 create-route \
  --route-table-id rtb-0public123456789 \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-0123456789abcdef0 \
  --region ap-northeast-2

# NAT Gateway 생성 (Public Subnet에 배치)
aws ec2 allocate-address --domain vpc --region ap-northeast-2
aws ec2 create-nat-gateway \
  --subnet-id subnet-0public2a \
  --allocation-id eipalloc-0123456789abcdef0 \
  --region ap-northeast-2
```

### 4. 보안: Security Group vs NACL

VPC는 두 계층의 네트워크 보안을 제공합니다.

| 항목 | Security Group | Network ACL |
|------|----------------|-------------|
| 적용 단위 | ENI(인스턴스) | Subnet |
| Stateful | Yes (응답 자동 허용) | No (인/아웃 별도) |
| 규칙 종류 | Allow only | Allow + Deny |
| 평가 순서 | 모든 규칙 평가 | 번호 순서대로 평가 |
| 기본 동작 | 모든 인바운드 deny | 기본 NACL은 모두 allow |

Security Group은 stateful이므로 인바운드 허용 시 응답 트래픽은 자동으로 허용됩니다. 반면 NACL은 stateless라서 인바운드/아웃바운드 규칙을 모두 정의해야 합니다.

```bash
# Security Group 생성 (웹 서버용)
aws ec2 create-security-group \
  --group-name web-sg \
  --description "Web server SG" \
  --vpc-id vpc-0123456789abcdef0 \
  --region ap-northeast-2

# 인바운드 규칙: ALB SG에서 80/443 허용
aws ec2 authorize-security-group-ingress \
  --group-id sg-0web \
  --protocol tcp \
  --port 443 \
  --source-group sg-0alb \
  --region ap-northeast-2
```

### 5. VPC 연결 옵션

여러 VPC 또는 온프레미스 네트워크와 연결하기 위한 다양한 옵션이 있습니다.

| 방법 | 특징 | 사용 사례 |
|------|------|----------|
| VPC Peering | 1:1 연결. 전이적 라우팅 불가 | 소수 VPC 직접 연결 |
| Transit Gateway (TGW) | Hub-and-Spoke 라우팅 허브 | 다수 VPC, 멀티 리전 통합 |
| Site-to-Site VPN | IPsec 터널 | 온프레미스와 암호화 연결 |
| Direct Connect (DX) | 전용 회선 | 대용량/저지연 온프레미스 연결 |
| AWS PrivateLink | 인터페이스 엔드포인트 | SaaS / 다른 VPC 서비스 노출 |
| VPC Lattice | 애플리케이션 레이어 서비스 메시 | 마이크로서비스 간 통신 |

### 6. VPC Endpoint

VPC Endpoint는 AWS 서비스에 인터넷을 거치지 않고 프라이빗하게 접근하는 기능입니다.

- **Gateway Endpoint**: S3, DynamoDB만 지원. 라우팅 테이블에 라우트 추가. 무료.
- **Interface Endpoint (PrivateLink)**: 대부분의 AWS 서비스 + 사용자 정의 서비스 지원. ENI 기반. 시간당 + 데이터 처리 요금 발생.

```bash
# S3 Gateway Endpoint 생성
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --service-name com.amazonaws.ap-northeast-2.s3 \
  --route-table-ids rtb-0private \
  --region ap-northeast-2

# Secrets Manager Interface Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.ap-northeast-2.secretsmanager \
  --subnet-ids subnet-0private2a subnet-0private2c \
  --security-group-ids sg-0endpoint \
  --private-dns-enabled \
  --region ap-northeast-2
```

### 7. IPAM 및 Reachability Analyzer

- **IPAM (IP Address Manager)**: 조직 전체의 IP 주소 풀과 할당 현황을 중앙에서 관리합니다. CIDR 충돌 방지, 사용률 추적이 가능합니다.
- **Reachability Analyzer**: 두 ENI 사이의 네트워크 도달성을 정적 분석합니다. SG, NACL, 라우팅, 게이트웨이 구성 오류를 사전에 식별합니다.
- **Network Access Analyzer**: 외부 노출, 인터넷 접근 가능 경로 등을 정책 기반으로 검증합니다.

---

## 아키텍처

### 표준 3-Tier VPC 설계

대부분의 프로덕션 VPC는 다음과 같은 3-Tier 구조로 설계됩니다.

```
                      [Internet]
                          |
                       [IGW]
                          |
   +----------------------+----------------------+
   |                      |                      |
[Public 2a]           [Public 2b]           [Public 2c]
  ALB / NAT             ALB / NAT             ALB / NAT
   |                      |                      |
[Private App 2a]      [Private App 2b]      [Private App 2c]
  EC2 / ECS / Lambda
   |                      |                      |
[Isolated DB 2a]      [Isolated DB 2b]      [Isolated DB 2c]
  RDS / ElastiCache
```

각 계층의 핵심 원칙은 다음과 같습니다.

1. **Public Subnet**: 인터넷에서 접근 가능한 최소한의 컴포넌트(ALB, NAT, Bastion)만 배치합니다.
2. **Private App Subnet**: 애플리케이션 서버는 NAT를 통해서만 인터넷으로 아웃바운드합니다.
3. **Isolated DB Subnet**: 데이터베이스는 인터넷 라우트를 갖지 않습니다.
4. **3개 AZ**: 단일 AZ 장애에 대비하기 위해 모든 계층을 3개 AZ에 분산합니다.

### Hub-and-Spoke (Transit Gateway)

다수의 VPC를 운영할 때는 VPC Peering의 N:N 복잡도를 피하기 위해 Transit Gateway를 중심으로 한 Hub-and-Spoke 구조가 표준입니다.

```
                  [On-Premises]
                       |
                   [VPN / DX]
                       |
   [Prod VPC] -- [Transit Gateway] -- [Stage VPC]
                       |
                  [Shared VPC]
                  (DNS, AD, Tools)
```

Transit Gateway는 멀티 리전 피어링도 지원하므로 글로벌 네트워크 메시를 단순화할 수 있습니다.

---

## 실전 사용

### 1. Terraform으로 표준 3-Tier VPC 생성

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "prod-vpc"
  cidr = "10.0.0.0/16"

  azs              = ["ap-northeast-2a", "ap-northeast-2b", "ap-northeast-2c"]
  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  private_subnets  = ["10.0.10.0/24", "10.0.11.0/24", "10.0.12.0/24"]
  database_subnets = ["10.0.20.0/24", "10.0.21.0/24", "10.0.22.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = true

  enable_dns_hostnames = true
  enable_dns_support   = true

  enable_flow_log                      = true
  create_flow_log_cloudwatch_log_group = true
  create_flow_log_cloudwatch_iam_role  = true
  flow_log_max_aggregation_interval    = 60

  tags = {
    Environment = "production"
    ManagedBy   = "terraform"
  }
}
```

### 2. Security Group 계층 설계

각 계층별로 SG를 분리하고, 인바운드 규칙은 다른 SG를 source로 사용하면 명확한 의존 관계가 만들어집니다.

```hcl
resource "aws_security_group" "alb" {
  name   = "alb-sg"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "app" {
  name   = "app-sg"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
}

resource "aws_security_group" "db" {
  name   = "db-sg"
  vpc_id = module.vpc.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
}
```

### 3. NAT Gateway 비용 최적화

NAT Gateway는 시간당 + 데이터 처리 요금이 모두 발생하여 의외로 비용이 큰 요소입니다.

- 개발 환경에서는 단일 NAT Gateway만 사용해 비용을 절감합니다.
- 프로덕션은 AZ당 1개씩 배치해 가용성을 확보합니다.
- S3, DynamoDB로의 트래픽은 Gateway Endpoint로 우회시켜 데이터 처리 요금을 회피합니다.
- 다른 AWS 서비스도 Interface Endpoint로 우회 가능한지 검토합니다.

### 4. VPC Flow Logs

VPC 내 트래픽 메타데이터를 기록하여 네트워크 가시성을 확보합니다. 자세한 내용은 [[vpc-flow-logs|VPC Flow Logs]] 포스트를 참고하세요.

```bash
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-0123456789abcdef0 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flowlogs \
  --deliver-logs-permission-arn arn:aws:iam::123456789012:role/flowlogs-role \
  --region ap-northeast-2
```

---

## 가격 / 한도

### 주요 비용 (서울 리전 기준)

| 항목 | 가격 |
|------|------|
| VPC 자체 | 무료 |
| Internet Gateway | 무료 (전송 데이터 비용만) |
| NAT Gateway | $0.045 / 시간 + $0.045 / GB 처리 |
| VPC Peering | 무료 (AZ 간 데이터 전송 $0.01/GB 별도) |
| Transit Gateway Attachment | $0.07 / 시간 + $0.02 / GB 처리 |
| Site-to-Site VPN | $0.05 / 시간 |
| PrivateLink (Interface Endpoint) | $0.013 / 시간 / AZ + $0.01 / GB |
| S3/DynamoDB Gateway Endpoint | 무료 |
| VPC Flow Logs | CloudWatch/S3 저장 비용 |

### 주요 한도 (Soft Limit, Quota 신청으로 증가 가능)

| 항목 | 기본 한도 |
|------|-----------|
| 리전당 VPC | 5개 |
| VPC당 서브넷 | 200개 |
| VPC당 Security Group | 2,500개 |
| SG당 규칙 (인바운드/아웃바운드) | 60개 |
| 라우팅 테이블당 라우트 | 50개 |
| VPC당 IGW | 1개 |
| 계정당 EIP | 5개 |

---

## Best Practice

### 설계 단계

1. **/16 이상 CIDR 권장**: 향후 확장성을 위해 충분히 큰 블록을 할당합니다.
2. **다른 VPC와 CIDR 겹치지 않게**: Peering, TGW 연결 시 충돌 방지를 위해 IPAM으로 관리합니다.
3. **3개 AZ 분산**: 모든 서브넷 계층을 3개 AZ에 분산합니다.
4. **계층별 서브넷 분리**: Public/Private/Isolated 3계층 구조를 표준으로 채택합니다.

### 보안

1. **Default SG 사용 금지**: 항상 명시적으로 SG를 생성합니다.
2. **0.0.0.0/0 인바운드 최소화**: ALB만 허용하고 EC2는 절대 직접 노출하지 않습니다.
3. **Bastion 대신 SSM Session Manager 권장**: 인바운드 22 포트 자체를 닫을 수 있습니다.
4. **Flow Logs 활성화**: 보안 사고 분석과 트래픽 분석에 필수입니다.
5. **Network Firewall 검토**: 7계층 위협 대응이 필요하면 도입합니다.

### 운영

1. **태깅 일관성**: Environment, Tier, ManagedBy 등 표준 태그를 강제합니다.
2. **VPC Endpoint 적극 활용**: 보안 + NAT 비용 절감 효과가 큽니다.
3. **Reachability Analyzer 정기 실행**: 의도하지 않은 경로 변화를 사전 탐지합니다.
4. **NAT Gateway 이중화**: 프로덕션은 AZ당 1개씩 배치합니다.
5. **Transit Gateway 표준화**: 3개 이상 VPC를 운영하면 Peering 대신 TGW로 전환합니다.

---

## 관련 서비스

| 서비스 | 관계 |
|--------|------|
| AWS Transit Gateway | 다수 VPC와 온프레미스를 통합하는 라우팅 허브 |
| AWS PrivateLink | VPC 간 서비스 노출. 인터페이스 엔드포인트로 접근 |
| AWS Direct Connect | 온프레미스와 전용선 연결 |
| AWS Network Firewall | L7 위협 탐지/차단 |
| AWS WAF | 웹 애플리케이션 방어. ALB/CloudFront와 통합 |
| AWS Cloud WAN | 글로벌 네트워크 자동 구성 |
| Amazon Route 53 Resolver | VPC DNS 해결 + 온프레미스 DNS 통합 |

---

## 관련 문서

- [[vpc-flow-logs|VPC Flow Logs]] - VPC 트래픽 메타데이터 수집 및 분석
- [[amazon-route-53-dns-서비스-개요|Amazon Route 53]] - VPC와 통합되는 DNS 서비스
- [[amazon-elb-application-load-balancer-개요|Amazon ELB]] - VPC 내부 로드밸런싱
- [[amazon-rds|Amazon RDS]] - VPC 내 관계형 DB 배치
