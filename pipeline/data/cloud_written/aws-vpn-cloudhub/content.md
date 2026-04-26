<!-- infographic-hero -->
![AWS VPN CloudHub 핵심 요약](figures/infographic.svg)

*Figure: AWS VPN CloudHub 한 장 요약 인포그래픽*

## 개요

AWS VPN CloudHub는 여러 Site-to-Site VPN 연결을 하나의 Virtual Private Gateway(VGW)에 연결하여 온프레미스 사이트 간 통신을 가능하게 하는 네트워크 패턴입니다. 이는 독립적인 AWS 서비스가 아니라 VGW의 BGP 라우팅 특성을 활용한 아키텍처 패턴입니다.

일반적으로 AWS Site-to-Site VPN은 온프레미스와 AWS VPC 간의 연결을 위해 사용됩니다. 그런데 여러 온프레미스 사이트가 동일한 VGW에 VPN으로 연결되면, VGW가 BGP 라우터 역할을 하여 각 사이트의 경로를 다른 사이트에 광고합니다. 이를 통해 사이트 간 트래픽이 AWS를 경유하여 전달될 수 있습니다.

VPN CloudHub는 전용 WAN(MPLS 등)을 구축하기 어렵거나 비용이 부담되는 환경에서 여러 지점(branch office) 간 통신을 위한 비용 효율적인 대안이 될 수 있습니다. 또한 기존 전용 WAN의 백업 경로로도 활용할 수 있습니다.

이 글에서는 VPN CloudHub의 동작 원리, 구성 방법, 제한사항, 그리고 Transit Gateway 기반 대안과의 비교를 상세히 살펴보겠습니다.

## 핵심 기능

### 허브-스포크 VPN 토폴로지

VPN CloudHub의 핵심은 VGW가 중앙 허브 역할을 하고, 각 온프레미스 사이트가 스포크 역할을 하는 토폴로지입니다.

```
사이트 A (서울)
  CGW-A (ASN 65001)
       \
        \  VPN
         \
          +-- VGW (AWS) --+-- VPC
         /                 
        /  VPN            
       /                  
saite B (부산)        사이트 C (대전)
  CGW-B (ASN 65002)     CGW-C (ASN 65003)
       \                /
        \  VPN         /  VPN
         \            /
          +-- VGW ---+
```

각 사이트는 고유한 BGP ASN(Autonomous System Number)을 사용해야 합니다. VGW는 각 사이트에서 수신한 BGP 경로를 다른 사이트에 재광고하여 사이트 간 라우팅을 가능하게 합니다.

### BGP 경로 교환 메커니즘

VPN CloudHub에서 BGP 경로가 교환되는 과정을 살펴보겠습니다.

1. 사이트 A(서울)가 자신의 네트워크 `10.1.0.0/16`을 BGP로 VGW에 광고합니다.
2. 사이트 B(부산)가 자신의 네트워크 `10.2.0.0/16`을 BGP로 VGW에 광고합니다.
3. 사이트 C(대전)가 자신의 네트워크 `10.3.0.0/16`을 BGP로 VGW에 광고합니다.
4. VGW는 사이트 A에게 사이트 B와 C의 경로를 광고합니다.
5. VGW는 사이트 B에게 사이트 A와 C의 경로를 광고합니다.
6. VGW는 사이트 C에게 사이트 A와 B의 경로를 광고합니다.

```
사이트 A가 수신하는 BGP 경로:
  10.2.0.0/16 via VGW (AS-PATH: 64512 65002)  # 사이트 B
  10.3.0.0/16 via VGW (AS-PATH: 64512 65003)  # 사이트 C
  172.16.0.0/16 via VGW (AS-PATH: 64512)       # VPC
```

### 고유한 BGP ASN 요구사항

각 Customer Gateway는 반드시 고유한 BGP ASN을 사용해야 합니다. 이는 BGP의 루프 방지 메커니즘 때문입니다. BGP는 AS-PATH에 자신의 ASN이 포함된 경로를 수신하면 해당 경로를 폐기합니다. 만약 두 사이트가 동일한 ASN을 사용하면 VGW가 재광고한 경로를 수신하더라도 자신의 ASN이 포함되어 있으므로 해당 경로를 무시하게 됩니다.

### VPC 통신

VPN CloudHub 구성에서 각 사이트는 VGW에 연결된 VPC와도 통신할 수 있습니다. VGW는 VPC의 CIDR을 각 사이트에 광고하므로, 사이트에서 VPC로의 라우팅이 자동으로 설정됩니다.

다만 VPN CloudHub의 주 목적은 사이트 간 통신이며, VPC와의 통신은 부가적인 기능입니다.

## 아키텍처/동작 원리

### 트래픽 흐름

사이트 A에서 사이트 B로의 트래픽 흐름을 살펴보겠습니다.

```
사이트 A (10.1.0.0/16)           사이트 B (10.2.0.0/16)
  [서버]                            [서버]
    |                                 ^
    v                                 |
  [Router/CGW-A]                   [Router/CGW-B]
    |                                 ^
    | IPsec VPN Tunnel                | IPsec VPN Tunnel
    v                                 |
  [VGW] -------- BGP 라우팅 ------->[VGW]
        (AWS 네트워크 내부 전달)
```

트래픽은 사이트 A에서 IPsec 터널을 통해 AWS VGW에 도달하고, VGW의 BGP 라우팅에 따라 사이트 B로 향하는 IPsec 터널을 통해 사이트 B에 도달합니다. 전체 경로가 IPsec으로 암호화되어 있으므로 보안이 유지됩니다.

### 장애 시나리오

**단일 VPN 터널 장애:**
각 VPN Connection은 두 개의 터널을 가지며, 하나의 터널이 장애이면 다른 터널로 자동 전환됩니다.

**VPN Connection 장애:**
사이트의 전체 VPN Connection이 장애이면 해당 사이트와의 통신이 중단됩니다. 이를 대비하여 각 사이트에서 두 개의 Customer Gateway(서로 다른 라우터)를 사용하여 이중화할 수 있습니다.

**VGW 장애:**
VGW는 AWS 관리형 서비스이므로 AWS가 고가용성을 보장합니다. 그러나 VGW가 위치한 리전 전체가 장애인 경우에는 모든 사이트 간 통신이 중단됩니다.

### 성능 제한

VPN CloudHub는 Site-to-Site VPN의 성능 제한을 그대로 상속합니다.

- 각 VPN 터널의 최대 대역폭: 약 1.25 Gbps
- 사이트 간 트래픽은 AWS를 경유하므로 추가 지연이 발생합니다.
- VGW에서는 ECMP를 지원하지 않으므로 대역폭 확장이 제한적입니다.

## 실전 활용

### VPN CloudHub 구성 단계

**Step 1: Virtual Private Gateway 생성 및 VPC 연결**

```bash
# VGW 생성
aws ec2 create-vpn-gateway \
  --type ipsec.1 \
  --amazon-side-asn 64512 \
  --tag-specifications 'ResourceType=vpn-gateway,Tags=[{Key=Name,Value=cloudhub-vgw}]'

# VGW를 VPC에 연결
aws ec2 attach-vpn-gateway \
  --vpn-gateway-id vgw-0123456789abcdef0 \
  --vpc-id vpc-0123456789abcdef0

# VGW 경로 전파 활성화
aws ec2 enable-vgw-route-propagation \
  --gateway-id vgw-0123456789abcdef0 \
  --route-table-id rtb-0123456789abcdef0
```

**Step 2: 각 사이트의 Customer Gateway 생성**

```bash
# 사이트 A (서울) - CGW 생성
aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip 203.0.113.1 \
  --bgp-asn 65001 \
  --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=site-seoul}]'

# 사이트 B (부산) - CGW 생성
aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip 203.0.113.2 \
  --bgp-asn 65002 \
  --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=site-busan}]'

# 사이트 C (대전) - CGW 생성
aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip 203.0.113.3 \
  --bgp-asn 65003 \
  --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=site-daejeon}]'
```

**Step 3: 각 사이트에 대한 VPN Connection 생성**

```bash
# 사이트 A VPN Connection
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-seoul \
  --vpn-gateway-id vgw-0123456789abcdef0 \
  --options '{"StaticRoutesOnly": false}' \
  --tag-specifications 'ResourceType=vpn-connection,Tags=[{Key=Name,Value=vpn-seoul}]'

# 사이트 B VPN Connection
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-busan \
  --vpn-gateway-id vgw-0123456789abcdef0 \
  --options '{"StaticRoutesOnly": false}' \
  --tag-specifications 'ResourceType=vpn-connection,Tags=[{Key=Name,Value=vpn-busan}]'

# 사이트 C VPN Connection
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-daejeon \
  --vpn-gateway-id vgw-0123456789abcdef0 \
  --options '{"StaticRoutesOnly": false}' \
  --tag-specifications 'ResourceType=vpn-connection,Tags=[{Key=Name,Value=vpn-daejeon}]'
```

**Step 4: VPN 구성 다운로드 및 적용**

```bash
# VPN 구성 다운로드 (라우터 설정용)
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-seoul \
  --query 'VpnConnections[0].CustomerGatewayConfiguration' \
  --output text > vpn-seoul-config.xml
```

### VPN 상태 모니터링

```bash
# 모든 VPN Connection 상태 확인
aws ec2 describe-vpn-connections \
  --filters 'Name=vpn-gateway-id,Values=vgw-0123456789abcdef0' \
  --query 'VpnConnections[*].{
    Name:Tags[?Key==`Name`]|[0].Value,
    State:State,
    CGW:CustomerGatewayId,
    Tunnel1Status:VgwTelemetry[0].Status,
    Tunnel1IP:VgwTelemetry[0].OutsideIpAddress,
    Tunnel2Status:VgwTelemetry[1].Status,
    Tunnel2IP:VgwTelemetry[1].OutsideIpAddress
  }' \
  --output table

# CloudWatch에서 VPN 터널 상태 모니터링
aws cloudwatch get-metric-statistics \
  --namespace AWS/VPN \
  --metric-name TunnelState \
  --dimensions Name=VpnId,Value=vpn-seoul \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Average
```

### CloudWatch 알람 설정

```bash
# VPN 터널 다운 알람 생성
aws cloudwatch put-metric-alarm \
  --alarm-name "vpn-seoul-tunnel-down" \
  --alarm-description "Seoul VPN tunnel is down" \
  --metric-name TunnelState \
  --namespace AWS/VPN \
  --statistic Maximum \
  --period 300 \
  --evaluation-periods 2 \
  --threshold 1 \
  --comparison-operator LessThanThreshold \
  --dimensions Name=VpnId,Value=vpn-seoul \
  --alarm-actions arn:aws:sns:ap-northeast-2:123456789012:network-alerts
```

## 모범 사례/보안

### 설계 모범 사례

1. **각 사이트에 고유한 BGP ASN을 할당합니다.** 동일한 ASN을 사용하면 BGP 루프 방지 메커니즘에 의해 사이트 간 경로가 전파되지 않습니다.

2. **BGP를 반드시 사용합니다.** VPN CloudHub는 BGP 동적 라우팅에 의존합니다. 정적 라우팅으로는 사이트 간 경로 교환이 불가능합니다.

3. **각 사이트에서 고유한 CIDR을 사용합니다.** 사이트 간 IP 주소 대역이 겹치면 라우팅 충돌이 발생합니다.

4. **MPLS/전용 WAN의 백업으로 활용합니다.** VPN CloudHub를 기존 전용 WAN의 백업 경로로 구성하면 WAN 장애 시에도 사이트 간 통신을 유지할 수 있습니다.

5. **사이트 수가 많거나 대역폭 요구사항이 높은 경우 Transit Gateway를 고려합니다.** VPN CloudHub는 소규모 환경에 적합하며, 대규모 환경에서는 Transit Gateway가 더 유연합니다.

### 보안 모범 사례

1. **강력한 Pre-Shared Key를 사용합니다.** 각 VPN Connection마다 서로 다른 강력한 PSK를 설정합니다.

2. **IKEv2를 사용합니다.** IKEv1보다 보안성과 성능이 우수합니다.

3. **VPC 보안 그룹과 NACL을 적절히 구성합니다.** 사이트에서 VPC로의 접근을 최소 권한 원칙에 따라 제한합니다.

4. **VPN 로그를 모니터링합니다.** CloudWatch Logs로 VPN 로그를 전송하여 비정상적인 연결 시도를 감지합니다.

```bash
# VPN 연결 로깅 활성화
aws ec2 modify-vpn-connection-options \
  --vpn-connection-id vpn-seoul \
  --vpn-connection-options '{
    "EnableAcceleration": false,
    "LocalIpv4NetworkCidr": "0.0.0.0/0",
    "RemoteIpv4NetworkCidr": "0.0.0.0/0",
    "TunnelInsideIpVersion": "ipv4"
  }'
```

### 제한사항

- VGW에서는 ECMP를 지원하지 않으므로, 사이트당 최대 대역폭이 1.25 Gbps로 제한됩니다.
- 사이트 간 트래픽이 AWS를 경유하므로 지연 시간이 증가합니다.
- VGW당 최대 10개의 VPN Connection을 연결할 수 있습니다.
- 트래픽 검사(방화벽 등)를 사이트 간 트래픽에 적용하기 어렵습니다.

## 관련 서비스 비교

| 특성 | VPN CloudHub (VGW) | Transit Gateway + VPN | MPLS/전용 WAN |
|------|-------------------|----------------------|---------------|
| 사이트 간 통신 | 지원 (BGP 경유) | 지원 | 지원 |
| 중앙 허브 | VGW | Transit Gateway | 통신사 라우터 |
| ECMP | 미지원 | 지원 | 지원 |
| 최대 대역폭 | 1.25 Gbps | 확장 가능 | 계약에 따라 |
| VPC 연결 | 1개 VPC | 다수 VPC | 별도 구성 필요 |
| BGP 요구사항 | 필수 | 필수 (ECMP 시) | 선택 |
| 관리 복잡성 | 낮음 | 중간 | 높음 |
| 비용 | VPN 요금만 | TGW + VPN 요금 | 높음 |
| 네트워크 세그멘테이션 | 제한적 | 라우팅 테이블 | 다양 |
| 트래픽 검사 | 어려움 | Inspection VPC | 가능 |

### VPN CloudHub vs Transit Gateway

Transit Gateway는 VPN CloudHub의 상위 호환이라고 볼 수 있습니다. Transit Gateway는 ECMP 지원, 다수 VPC 연결, 네트워크 세그멘테이션, Direct Connect 통합 등 VPN CloudHub에서 제공하지 않는 다양한 기능을 지원합니다.

다만 Transit Gateway는 추가 비용(Attachment 시간당 요금 + 데이터 처리 요금)이 발생합니다. 사이트 수가 적고(2~3개) 대역폭 요구사항이 낮으며 VPC가 하나인 단순한 환경에서는 VPN CloudHub가 더 비용 효율적일 수 있습니다.

## 요약

AWS VPN CloudHub는 VGW의 BGP 라우팅을 활용하여 여러 온프레미스 사이트 간 통신을 가능하게 하는 아키텍처 패턴입니다. 주요 내용을 정리하면 다음과 같습니다.

- VGW에 여러 VPN Connection을 연결하면 VGW가 BGP 경로를 재광고하여 사이트 간 통신을 가능하게 합니다.
- 각 사이트는 반드시 고유한 BGP ASN을 사용해야 합니다.
- BGP 동적 라우팅이 필수이며, 정적 라우팅으로는 사이트 간 경로 교환이 불가능합니다.
- 전용 WAN(MPLS)의 비용 효율적인 대안 또는 백업으로 활용할 수 있습니다.
- VGW에서는 ECMP를 지원하지 않으므로 대역폭이 제한적입니다 (터널당 1.25 Gbps).
- 사이트 수가 많거나 고급 기능이 필요한 경우 Transit Gateway로의 마이그레이션을 고려해야 합니다.
- 각 사이트에 고유한 CIDR을 사용하고, 강력한 암호화 설정을 적용하는 것이 보안 모범 사례입니다.