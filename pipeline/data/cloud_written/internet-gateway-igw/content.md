## 개요

Internet Gateway(IGW)는 VPC와 인터넷 간의 통신을 가능하게 하는 AWS의 기본 네트워킹 구성 요소입니다. VPC는 기본적으로 격리된 가상 네트워크이므로, IGW 없이는 VPC 내의 리소스가 인터넷에 접근하거나 인터넷에서 접근을 받을 수 없습니다.

IGW는 수평적으로 확장되고 가용성이 높으며 중복적인 AWS 관리형 서비스입니다. 대역폭 제한이나 가용성 문제를 걱정할 필요가 없으며, 추가 비용도 발생하지 않습니다 (데이터 전송 비용은 별도).

단순해 보이지만 IGW는 VPC 네트워킹의 핵심 구성 요소이며, 퍼블릭 서브넷과 프라이빗 서브넷의 구분, NAT 동작, 라우팅 테이블 설계 등 VPC 네트워크 아키텍처의 기반이 됩니다. 이 글에서는 IGW의 동작 원리부터 실전 구성까지 상세히 살펴보겠습니다.

## 핵심 기능

### 양방향 인터넷 통신

IGW는 VPC와 인터넷 간의 양방향 통신을 제공합니다.

- **아웃바운드**: VPC 내의 리소스가 인터넷의 외부 서비스에 접근 (예: 소프트웨어 업데이트, API 호출)
- **인바운드**: 인터넷의 사용자가 VPC 내의 리소스에 접근 (예: 웹 서버, API 서버)

IGW를 통한 인터넷 통신이 가능하려면 다음 조건이 모두 충족되어야 합니다.

1. VPC에 IGW가 연결(Attach)되어 있어야 합니다.
2. 서브넷의 라우팅 테이블에 IGW를 대상으로 하는 경로가 있어야 합니다.
3. 리소스에 퍼블릭 IP 주소(자동 할당 또는 EIP)가 있어야 합니다.
4. 보안 그룹과 NACL에서 해당 트래픽을 허용해야 합니다.

### 1:1 NAT 기능

IGW의 중요하지만 잘 알려지지 않은 기능이 1:1 NAT입니다. EC2 인스턴스의 운영체제에는 프라이빗 IP 주소만 설정되어 있고, 퍼블릭 IP 주소는 설정되어 있지 않습니다. IGW가 아웃바운드 트래픽의 소스 IP를 프라이빗 IP에서 퍼블릭 IP로 변환하고, 인바운드 트래픽의 목적지 IP를 퍼블릭 IP에서 프라이빗 IP로 변환합니다.

```
아웃바운드:
인스턴스 (src: 10.0.1.100) --> IGW (NAT: src 10.0.1.100 -> 52.xx.xx.xx) --> 인터넷

인바운드:
인터넷 (dst: 52.xx.xx.xx) --> IGW (NAT: dst 52.xx.xx.xx -> 10.0.1.100) --> 인스턴스
```

이 NAT는 퍼블릭 IP가 있는 리소스에 대해서만 수행됩니다. 퍼블릭 IP가 없는 리소스의 트래픽은 IGW를 통과할 수 없습니다.

### 퍼블릭 서브넷 vs 프라이빗 서브넷

서브넷 자체에 "퍼블릭" 또는 "프라이빗" 속성이 있는 것은 아닙니다. 라우팅 테이블의 설정에 따라 구분됩니다.

**퍼블릭 서브넷**: 라우팅 테이블에 `0.0.0.0/0 -> igw-xxxx` 경로가 있는 서브넷
**프라이빗 서브넷**: IGW로의 기본 경로가 없는 서브넷 (NAT Gateway를 통한 경로만 있거나 없음)

```json
{
  "PublicSubnetRouteTable": {
    "Routes": [
      { "Destination": "10.0.0.0/16", "Target": "local" },
      { "Destination": "0.0.0.0/0", "Target": "igw-xxxx" }
    ]
  },
  "PrivateSubnetRouteTable": {
    "Routes": [
      { "Destination": "10.0.0.0/16", "Target": "local" },
      { "Destination": "0.0.0.0/0", "Target": "nat-xxxx" }
    ]
  }
}
```

### Egress-Only Internet Gateway

Egress-Only Internet Gateway는 IPv6 트래픽 전용 게이트웨이로, VPC에서 인터넷으로의 아웃바운드 IPv6 트래픽만 허용하고 인바운드 트래픽은 차단합니다. IPv6 주소는 모두 글로벌 유니캐스트 주소(퍼블릭)이므로, 프라이빗 서브넷의 IPv6 리소스가 인터넷에 접근할 때 NAT Gateway 대신 Egress-Only IGW를 사용합니다.

IPv4에서 NAT Gateway가 하는 역할을 IPv6에서는 Egress-Only IGW가 담당한다고 이해하면 됩니다.

### 고가용성

IGW는 AWS가 관리하는 서비스로 다음과 같은 특성을 가집니다.

- 수평적으로 자동 확장됩니다.
- 여러 AZ에 걸쳐 중복적으로 배포됩니다.
- 대역폭 병목이 없습니다.
- 별도의 가용성 설계가 필요 없습니다.
- VPC당 하나의 IGW만 연결 가능합니다.

## 아키텍처/동작 원리

### IGW를 통한 트래픽 흐름

```
인터넷
   |
   v
+--IGW--+
   |
   | (퍼블릭 IP <-> 프라이빗 IP NAT)
   |
+--VPC (10.0.0.0/16)--+
|                      |
| 퍼블릭 서브넷        | 프라이빗 서브넷
| (10.0.1.0/24)       | (10.0.2.0/24)
| RT: 0.0.0.0/0->igw  | RT: 0.0.0.0/0->nat
|                      |
| [EC2 + 퍼블릭 IP]    | [EC2 프라이빗만]
| [ALB]               | [RDS]
| [NAT Gateway]       | [ElastiCache]
+----------------------+
```

### 인바운드 트래픽 흐름 상세

클라이언트가 퍼블릭 서브넷의 웹 서버에 접근하는 과정입니다.

1. 클라이언트가 `52.xx.xx.xx:443` (EIP)으로 HTTPS 요청을 보냅니다.
2. IGW가 요청을 수신하고 목적지 IP를 `52.xx.xx.xx`에서 `10.0.1.100`으로 변환합니다 (1:1 NAT).
3. VPC 라우팅 테이블에 의해 트래픽이 해당 서브넷으로 전달됩니다.
4. NACL이 인바운드 규칙을 확인합니다 (stateless).
5. 보안 그룹이 인바운드 규칙을 확인합니다 (stateful).
6. EC2 인스턴스가 요청을 수신합니다.

### IPv6와 IGW

IPv6를 사용하는 경우 IGW의 동작이 약간 다릅니다. IPv6 주소는 모두 글로벌 유니캐스트(퍼블릭) 주소이므로 NAT가 필요 없습니다. IGW는 IPv6 트래픽에 대해 NAT 없이 직접 라우팅만 수행합니다.

```
IPv4: 인스턴스 (10.0.1.100) --> IGW (NAT) --> 인터넷 (52.xx.xx.xx)
IPv6: 인스턴스 (2001:db8::1) --> IGW (NAT 없음) --> 인터넷 (2001:db8::1)
```

## 실전 활용

### VPC 생성 및 IGW 연결

```bash
# VPC 생성
aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=prod-vpc}]'

# IGW 생성
aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=prod-igw}]'

# IGW를 VPC에 연결
aws ec2 attach-internet-gateway \
  --internet-gateway-id igw-0123456789abcdef0 \
  --vpc-id vpc-0123456789abcdef0
```

### 퍼블릭/프라이빗 서브넷 구성

```bash
# 퍼블릭 서브넷 생성
aws ec2 create-subnet \
  --vpc-id vpc-0123456789abcdef0 \
  --cidr-block 10.0.1.0/24 \
  --availability-zone ap-northeast-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=public-subnet-az1}]'

# 프라이빗 서브넷 생성
aws ec2 create-subnet \
  --vpc-id vpc-0123456789abcdef0 \
  --cidr-block 10.0.2.0/24 \
  --availability-zone ap-northeast-2a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=private-subnet-az1}]'

# 퍼블릭 서브넷용 라우팅 테이블 생성
aws ec2 create-route-table \
  --vpc-id vpc-0123456789abcdef0 \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=public-rt}]'

# IGW로의 기본 경로 추가 (이것이 서브넷을 '퍼블릭'으로 만듦)
aws ec2 create-route \
  --route-table-id rtb-public \
  --destination-cidr-block 0.0.0.0/0 \
  --gateway-id igw-0123456789abcdef0

# 퍼블릭 서브넷에 라우팅 테이블 연결
aws ec2 associate-route-table \
  --route-table-id rtb-public \
  --subnet-id subnet-public-az1

# 퍼블릭 서브넷에서 자동 퍼블릭 IP 할당 활성화
aws ec2 modify-subnet-attribute \
  --subnet-id subnet-public-az1 \
  --map-public-ip-on-launch
```

### Egress-Only Internet Gateway 구성 (IPv6)

```bash
# VPC에 IPv6 CIDR 블록 추가
aws ec2 associate-vpc-cidr-block \
  --vpc-id vpc-0123456789abcdef0 \
  --amazon-provided-ipv6-cidr-block

# Egress-Only IGW 생성
aws ec2 create-egress-only-internet-gateway \
  --vpc-id vpc-0123456789abcdef0 \
  --tag-specifications 'ResourceType=egress-only-internet-gateway,Tags=[{Key=Name,Value=prod-eigw}]'

# 프라이빗 서브넷의 라우팅 테이블에 IPv6 아웃바운드 경로 추가
aws ec2 create-route \
  --route-table-id rtb-private \
  --destination-ipv6-cidr-block ::/0 \
  --egress-only-internet-gateway-id eigw-0123456789abcdef0
```

### IGW 상태 확인

```bash
# IGW 목록 및 연결 상태 확인
aws ec2 describe-internet-gateways \
  --query 'InternetGateways[*].{Id:InternetGatewayId,VpcId:Attachments[0].VpcId,State:Attachments[0].State,Name:Tags[?Key==`Name`]|[0].Value}' \
  --output table

# 특정 VPC의 IGW 확인
aws ec2 describe-internet-gateways \
  --filters 'Name=attachment.vpc-id,Values=vpc-0123456789abcdef0' \
  --output json

# 라우팅 테이블에서 IGW 경로 확인
aws ec2 describe-route-tables \
  --filters 'Name=vpc-id,Values=vpc-0123456789abcdef0' \
  --query 'RouteTables[*].{RTId:RouteTableId,Name:Tags[?Key==`Name`]|[0].Value,Routes:Routes[?GatewayId!=`local`].{Dest:DestinationCidrBlock,Target:GatewayId}}' \
  --output json
```

### 완전한 VPC 네트워크 구성 예시

```bash
# 1. VPC 생성
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --query 'Vpc.VpcId' \
  --output text \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=prod-vpc}]')

# 2. DNS 호스트 이름 활성화
aws ec2 modify-vpc-attribute \
  --vpc-id $VPC_ID \
  --enable-dns-hostnames

# 3. IGW 생성 및 연결
IGW_ID=$(aws ec2 create-internet-gateway \
  --query 'InternetGateway.InternetGatewayId' \
  --output text \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=prod-igw}]')

aws ec2 attach-internet-gateway \
  --internet-gateway-id $IGW_ID \
  --vpc-id $VPC_ID

echo "VPC: $VPC_ID, IGW: $IGW_ID"
```

## 모범 사례/보안

### 보안 모범 사례

1. **퍼블릭 서브넷을 최소화합니다.** 인터넷에 직접 노출되어야 하는 리소스(ALB, NAT Gateway, Bastion Host 등)만 퍼블릭 서브넷에 배치합니다. 데이터베이스, 캐시, 내부 서비스 등은 반드시 프라이빗 서브넷에 배치합니다.

2. **보안 그룹을 최소 권한으로 설정합니다.** 퍼블릭 서브넷의 리소스에는 필요한 포트만 열어야 합니다. 특히 SSH(22), RDP(3389) 포트는 특정 IP에서만 접근 가능하도록 제한합니다.

3. **NACL을 추가 방어층으로 활용합니다.** NACL은 서브넷 수준의 방화벽으로, 보안 그룹과 함께 심층 방어(Defense in Depth)를 구현합니다.

4. **VPC Flow Logs를 활성화합니다.** IGW를 통한 모든 트래픽을 기록하여 비정상적인 접근을 탐지합니다.

```bash
# VPC Flow Logs 활성화
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-0123456789abcdef0 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /aws/vpc/flow-logs \
  --deliver-logs-permission-arn arn:aws:iam::123456789012:role/VPCFlowLogsRole
```

5. **불필요한 IGW를 제거합니다.** 인터넷 접근이 필요 없는 VPC에는 IGW를 연결하지 않습니다. 이를 통해 실수로 인한 인터넷 노출을 방지합니다.

### 아키텍처 모범 사례

1. **멀티 AZ로 서브넷을 구성합니다.** 최소 두 개 이상의 AZ에 퍼블릭/프라이빗 서브넷을 구성하여 가용성을 확보합니다.

2. **서브넷 CIDR을 적절히 계획합니다.** 향후 확장을 고려하여 충분한 IP 주소 공간을 확보합니다. 일반적으로 퍼블릭 서브넷은 /24, 프라이빗 서브넷은 더 큰 범위를 할당합니다.

3. **IPv6 지원을 고려합니다.** IPv6를 활성화하면 퍼블릭 IPv4 주소 비용을 절감할 수 있습니다. 아웃바운드 전용 통신에는 Egress-Only IGW를 사용합니다.

## 관련 서비스 비교

| 특성 | Internet Gateway | NAT Gateway | Egress-Only IGW | VPC Endpoint |
|------|-----------------|-------------|-----------------|-------------|
| 통신 방향 | 양방향 | 아웃바운드만 | 아웃바운드만 (IPv6) | 프라이빗 |
| IP 버전 | IPv4, IPv6 | IPv4 | IPv6 | IPv4, IPv6 |
| NAT 수행 | 1:1 NAT | Many:1 NAT | 없음 | 없음 |
| 비용 | 무료 | 시간 + 데이터 | 무료 | 유형별 상이 |
| 대역폭 | 무제한 | 최대 100 Gbps | 무제한 | 서비스별 |
| 가용성 | AWS 관리 (고가용) | AZ 단위 | AWS 관리 (고가용) | AWS 관리 |
| 사용 대상 | 퍼블릭 서브넷 | 프라이빗 서브넷 | 프라이빗 서브넷 | 프라이빗 서브넷 |

### IGW vs NAT Gateway

IGW와 NAT Gateway는 서로 보완적인 관계입니다. IGW는 퍼블릭 서브넷의 리소스가 인터넷과 양방향으로 통신하게 하며, NAT Gateway는 프라이빗 서브넷의 리소스가 인터넷으로 아웃바운드 통신만 할 수 있게 합니다. NAT Gateway 자체도 퍼블릭 서브넷에 위치하며 IGW를 통해 인터넷에 접근합니다.

## 요약

Internet Gateway는 VPC의 인터넷 통신을 가능하게 하는 기본적이면서도 핵심적인 네트워킹 구성 요소입니다. 주요 내용을 정리하면 다음과 같습니다.

- IGW는 VPC와 인터넷 간의 양방향 통신을 제공하며, VPC당 하나만 연결할 수 있습니다.
- IGW는 퍼블릭 IP가 있는 리소스에 대해 1:1 NAT를 수행합니다.
- 퍼블릭 서브넷은 라우팅 테이블에 IGW로의 기본 경로가 있는 서브넷입니다.
- Egress-Only IGW는 IPv6 아웃바운드 전용 게이트웨이로, IPv4의 NAT Gateway 역할을 합니다.
- IGW는 AWS 관리형 서비스로 고가용성이 보장되며 추가 비용이 없습니다.
- 보안을 위해 퍼블릭 서브넷을 최소화하고, 보안 그룹과 NACL을 적절히 구성해야 합니다.
- VPC Flow Logs를 활성화하여 IGW를 통한 트래픽을 모니터링해야 합니다.