## 개요

Virtual Private Gateway(VGW)는 VPC 측에서 VPN 또는 Direct Connect 연결의 종단점(Endpoint) 역할을 하는 AWS 관리형 게이트웨이입니다. 온프레미스 네트워크와 AWS VPC를 연결하는 하이브리드 네트워크 아키텍처에서 VGW는 VPC 측의 핵심 구성 요소입니다.

VGW는 IGW(Internet Gateway)가 VPC와 인터넷을 연결하는 것처럼, VPC와 온프레미스 네트워크를 연결합니다. 다만 VGW는 IGW와 달리 암호화된 VPN 터널이나 전용 Direct Connect 연결을 통해 통신합니다.

VGW는 고가용성을 위해 여러 AZ에 걸쳐 중복적으로 배포됩니다. 또한 BGP(Border Gateway Protocol)를 지원하여 온프레미스 라우터와 동적으로 경로를 교환할 수 있습니다.

Transit Gateway가 등장한 이후 VGW의 역할이 줄어들었지만, 단일 VPC와의 VPN/Direct Connect 연결에는 여전히 VGW가 적합한 경우가 많습니다. 이 글에서는 VGW의 핵심 기능, 동작 원리, 실전 구성 방법, 그리고 Transit Gateway와의 비교를 상세히 살펴보겠습니다.

## 핵심 기능

### VPN 연결 종단점

VGW는 AWS 측에서 Site-to-Site VPN의 종단점 역할을 합니다. 하나의 VGW에 최대 10개의 VPN Connection을 연결할 수 있습니다. 각 VPN Connection은 두 개의 IPsec 터널을 가지며, 이는 고가용성을 위한 구성입니다.

```
온프레미스                          AWS
+----------+                      +-------+--------+
| Customer |  VPN Connection      | VGW   | VPC    |
| Gateway  |---Tunnel 1 (Active)-->|       |        |
| (Router) |---Tunnel 2 (Standby)->|       |        |
+----------+                      +-------+--------+
```

### Direct Connect 연결 종단점

VGW는 Direct Connect의 Private Virtual Interface(VIF)를 통해 온프레미스와 연결할 수도 있습니다. 또한 Direct Connect Gateway(DXGW)를 통해 여러 리전의 VGW에 Direct Connect를 연결할 수 있습니다.

```
온프레미스 --> DX Connection --> DX Location --> Private VIF --> VGW --> VPC
또는
온프레미스 --> DX Connection --> DX Location --> Private VIF --> DXGW --> VGW --> VPC
```

### BGP 지원

VGW는 BGP를 지원하여 온프레미스 라우터와 동적으로 라우팅 정보를 교환합니다. VGW에는 Amazon 측 ASN(Autonomous System Number)을 지정할 수 있으며, 기본값은 64512입니다.

BGP를 사용하면 다음과 같은 이점이 있습니다.
- 경로 변경 시 자동 업데이트
- 장애 감지 및 자동 페일오버
- 온프레미스 네트워크 구성 변경 시 수동 라우팅 업데이트 불필요

### 경로 전파(Route Propagation)

VGW 경로 전파를 활성화하면 VPN 또는 Direct Connect를 통해 수신된 BGP 경로가 VPC의 라우팅 테이블에 자동으로 추가됩니다. 이를 통해 온프레미스 네트워크의 경로를 VPC에서 자동으로 인식할 수 있습니다.

```json
{
  "RouteTable": {
    "Routes": [
      { "Destination": "10.0.0.0/16", "Target": "local", "Origin": "local" },
      { "Destination": "192.168.0.0/16", "Target": "vgw-xxxx", "Origin": "propagated" },
      { "Destination": "172.16.0.0/12", "Target": "vgw-xxxx", "Origin": "propagated" }
    ]
  }
}
```

전파된 경로와 정적 경로가 겹치는 경우, 정적 경로가 우선합니다.

### ASN 설정

VGW를 생성할 때 Amazon 측 BGP ASN을 지정할 수 있습니다. 기본값은 64512이며, 사설 ASN 범위(64512-65534) 또는 공인 ASN을 사용할 수 있습니다.

온프레미스 라우터의 ASN과 VGW의 ASN은 서로 달라야 합니다 (eBGP 설정).

## 아키텍처/동작 원리

### VGW의 고가용성

VGW는 AWS 관리형 서비스로 여러 AZ에 걸쳐 중복적으로 배포됩니다. VPN Connection의 두 터널은 서로 다른 AWS 엔드포인트를 사용하여 단일 장애점을 제거합니다.

```
온프레미스 Router
  |
  +-- IPsec Tunnel 1 --> AWS Endpoint 1 (AZ-a) --> VGW --> VPC
  |
  +-- IPsec Tunnel 2 --> AWS Endpoint 2 (AZ-c) --> VGW --> VPC
```

### VPN 경로 선택 우선순위

VGW에서 동일한 목적지에 대해 여러 경로가 존재할 때 다음 순서로 경로를 선택합니다.

1. **가장 구체적인 경로** (Longest Prefix Match)
2. **Direct Connect 경로** (VPN보다 우선)
3. **정적 VPN 경로** (BGP 경로보다 우선)
4. **AS-PATH가 짧은 BGP 경로**
5. **Multi Exit Discriminator(MED)가 낮은 경로**

이 우선순위는 하이브리드 네트워크 설계에서 트래픽 경로를 제어할 때 매우 중요합니다.

### VGW와 VPC의 관계

- 하나의 VGW는 하나의 VPC에만 연결할 수 있습니다.
- 하나의 VPC에는 하나의 VGW만 연결할 수 있습니다.
- VGW를 다른 VPC로 이동하려면 현재 VPC에서 분리한 후 새 VPC에 연결해야 합니다.
- VGW를 분리해도 VPN Connection은 유지됩니다.

### VGW vs Transit Gateway 아키텍처

**VGW 기반 아키텍처:**
```
온프레미스 --> VPN --> VGW --> VPC-A (단일 VPC만 연결 가능)
                              VPC-B에 접근하려면 별도 VPN/VGW 필요
```

**Transit Gateway 기반 아키텍처:**
```
온프레미스 --> VPN --> TGW --> VPC-A
                          --> VPC-B
                          --> VPC-C
```

## 실전 활용

### VGW 생성 및 VPC 연결

```bash
# VGW 생성 (사설 ASN 지정)
aws ec2 create-vpn-gateway \
  --type ipsec.1 \
  --amazon-side-asn 65000 \
  --tag-specifications 'ResourceType=vpn-gateway,Tags=[{Key=Name,Value=prod-vgw}]'

# VGW를 VPC에 연결
aws ec2 attach-vpn-gateway \
  --vpn-gateway-id vgw-0123456789abcdef0 \
  --vpc-id vpc-0123456789abcdef0

# 연결 상태 확인
aws ec2 describe-vpn-gateways \
  --vpn-gateway-ids vgw-0123456789abcdef0 \
  --query 'VpnGateways[0].{Id:VpnGatewayId,State:State,ASN:AmazonSideAsn,Attachments:VpcAttachments}' \
  --output json
```

### 경로 전파 설정

```bash
# VGW 경로 전파 활성화 (프라이빗 서브넷 라우팅 테이블)
aws ec2 enable-vgw-route-propagation \
  --gateway-id vgw-0123456789abcdef0 \
  --route-table-id rtb-private-az1

# 퍼블릭 서브넷에도 필요한 경우 활성화
aws ec2 enable-vgw-route-propagation \
  --gateway-id vgw-0123456789abcdef0 \
  --route-table-id rtb-public

# 경로 전파 상태 확인
aws ec2 describe-route-tables \
  --route-table-ids rtb-private-az1 \
  --query 'RouteTables[0].{Routes:Routes[*].{Dest:DestinationCidrBlock,Target:GatewayId,Origin:Origin},Propagations:PropagatingVgws}' \
  --output json
```

### Site-to-Site VPN 연결 생성

```bash
# Customer Gateway 생성
aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip 203.0.113.1 \
  --bgp-asn 65001 \
  --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=onprem-router}]'

# VPN Connection 생성 (BGP 동적 라우팅)
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-0123456789abcdef0 \
  --vpn-gateway-id vgw-0123456789abcdef0 \
  --options '{
    "StaticRoutesOnly": false,
    "TunnelInsideIpVersion": "ipv4",
    "TunnelOptions": [
      {
        "TunnelInsideCidr": "169.254.10.0/30",
        "PreSharedKey": "SecurePreSharedKey1",
        "Phase1EncryptionAlgorithms": [{"Value": "AES256"}],
        "Phase2EncryptionAlgorithms": [{"Value": "AES256"}],
        "IKEVersions": [{"Value": "ikev2"}]
      },
      {
        "TunnelInsideCidr": "169.254.10.4/30",
        "PreSharedKey": "SecurePreSharedKey2",
        "Phase1EncryptionAlgorithms": [{"Value": "AES256"}],
        "Phase2EncryptionAlgorithms": [{"Value": "AES256"}],
        "IKEVersions": [{"Value": "ikev2"}]
      }
    ]
  }' \
  --tag-specifications 'ResourceType=vpn-connection,Tags=[{Key=Name,Value=prod-vpn}]'
```

### VPN 상태 모니터링

```bash
# VPN Connection 상태 확인
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-0123456789abcdef0 \
  --query 'VpnConnections[0].{
    Id:VpnConnectionId,
    State:State,
    VgwId:VpnGatewayId,
    CgwId:CustomerGatewayId,
    Tunnel1:{Status:VgwTelemetry[0].Status,OutsideIP:VgwTelemetry[0].OutsideIpAddress,AcceptedRoutes:VgwTelemetry[0].AcceptedRouteCount},
    Tunnel2:{Status:VgwTelemetry[1].Status,OutsideIP:VgwTelemetry[1].OutsideIpAddress,AcceptedRoutes:VgwTelemetry[1].AcceptedRouteCount}
  }' \
  --output json

# CloudWatch에서 VPN 메트릭 확인
aws cloudwatch get-metric-statistics \
  --namespace AWS/VPN \
  --metric-name TunnelState \
  --dimensions Name=VpnId,Value=vpn-0123456789abcdef0 Name=TunnelIpAddress,Value=52.xx.xx.xx \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Average

# VPN 데이터 전송량 확인
aws cloudwatch get-metric-statistics \
  --namespace AWS/VPN \
  --metric-name TunnelDataOut \
  --dimensions Name=VpnId,Value=vpn-0123456789abcdef0 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum
```

### VGW와 Direct Connect Gateway 연결

```bash
# Direct Connect Gateway 생성
aws directconnect create-direct-connect-gateway \
  --direct-connect-gateway-name "prod-dxgw" \
  --amazon-side-asn 64512

# VGW를 DXGW에 연결
aws directconnect create-direct-connect-gateway-association \
  --direct-connect-gateway-id dxgw-0123456789abcdef0 \
  --gateway-id vgw-0123456789abcdef0 \
  --add-allowed-prefixes-to-direct-connect-gateway cidr=10.0.0.0/16

# 연결 상태 확인
aws directconnect describe-direct-connect-gateway-associations \
  --direct-connect-gateway-id dxgw-0123456789abcdef0 \
  --query 'directConnectGatewayAssociations[*].{GatewayId:virtualGatewayId,State:associationState,Prefixes:allowedPrefixesToDirectConnectGateway}' \
  --output json
```

### VGW 분리 및 재연결

```bash
# VGW를 현재 VPC에서 분리
aws ec2 detach-vpn-gateway \
  --vpn-gateway-id vgw-0123456789abcdef0 \
  --vpc-id vpc-old

# 새 VPC에 연결
aws ec2 attach-vpn-gateway \
  --vpn-gateway-id vgw-0123456789abcdef0 \
  --vpc-id vpc-new
```

## 모범 사례/보안

### 설계 모범 사례

1. **단일 VPC 연결에는 VGW를, 다수 VPC 연결에는 Transit Gateway를 사용합니다.** VGW는 하나의 VPC에만 연결 가능하므로, 여러 VPC에 온프레미스 접근이 필요한 경우 Transit Gateway가 적합합니다.

2. **경로 전파를 활성화합니다.** 수동으로 정적 경로를 관리하는 것보다 BGP 경로 전파를 사용하는 것이 운영 부담을 줄입니다.

3. **두 터널 모두 활성화 상태를 유지합니다.** VPN Connection의 두 터널 중 하나가 Down 상태이면 장애 복구 능력이 저하됩니다. CloudWatch 알람으로 터널 상태를 모니터링합니다.

4. **ASN을 신중하게 선택합니다.** VGW의 ASN은 생성 후 변경할 수 없습니다. 향후 네트워크 확장을 고려하여 ASN을 계획합니다.

5. **VPN과 Direct Connect를 동일 VGW에 연결하여 백업 구성을 합니다.** Direct Connect가 주 경로이고 VPN이 백업 경로로 동작합니다.

### 보안 모범 사례

1. **VPN 터널에 강력한 암호화를 적용합니다.** AES-256과 IKEv2를 사용합니다.

2. **BGP 인증(MD5)을 사용합니다.** BGP 세션의 무결성을 보장합니다.

3. **VPC 보안 그룹과 NACL을 적절히 설정합니다.** 온프레미스에서 VPC로의 접근을 최소 권한으로 제한합니다.

4. **CloudTrail로 VGW 관련 API 호출을 감사합니다.** VGW 생성, 삭제, VPN 연결 변경 등의 활동을 모니터링합니다.

### 마이그레이션 고려사항 (VGW에서 Transit Gateway로)

VGW에서 Transit Gateway로 마이그레이션할 때 고려해야 할 사항입니다.

- Transit Gateway는 VGW 대비 추가 비용이 발생합니다.
- VPN Connection을 VGW에서 Transit Gateway로 이동하려면 새로운 VPN Connection을 생성해야 합니다.
- 마이그레이션 중 다운타임을 최소화하려면 병렬 실행 후 전환하는 방식을 사용합니다.
- Transit Gateway는 ECMP를 지원하므로 대역폭 확장이 가능합니다.

## 관련 서비스 비교

| 특성 | Virtual Private Gateway | Transit Gateway | Direct Connect Gateway |
|------|------------------------|-----------------|----------------------|
| 연결 대상 | 단일 VPC | 다수 VPC + VPN + DX | DX와 VGW/TGW 연결 |
| VPN 지원 | 최대 10개 | 최대 20개 | 해당 없음 |
| ECMP | 미지원 | 지원 | 해당 없음 |
| 크로스 리전 | 미지원 | 피어링 지원 | 지원 |
| BGP | 지원 | 지원 | 지원 |
| 경로 전파 | VPC RT로 전파 | TGW RT로 전파 | 해당 없음 |
| 네트워크 세그멘테이션 | 제한적 | 라우팅 테이블 기반 | 해당 없음 |
| 비용 | VPN 요금만 | TGW 요금 + VPN | DX 요금 |
| 관리 복잡성 | 낮음 | 중간 | 낮음 |

## 요약

Virtual Private Gateway는 VPC와 온프레미스 네트워크를 연결하는 하이브리드 네트워크의 VPC 측 종단점입니다. 주요 내용을 정리하면 다음과 같습니다.

- VGW는 VPN과 Direct Connect 연결의 VPC 측 종단점 역할을 합니다.
- 하나의 VGW는 하나의 VPC에만 연결할 수 있으며, VPC당 하나의 VGW만 가능합니다.
- BGP를 지원하여 온프레미스 라우터와 동적으로 경로를 교환합니다.
- 경로 전파를 활성화하면 BGP로 수신된 온프레미스 경로가 VPC 라우팅 테이블에 자동 추가됩니다.
- Direct Connect가 VPN보다 우선하므로, 두 연결을 함께 사용하면 자연스럽게 백업 구성이 됩니다.
- ECMP를 지원하지 않으므로 VPN 대역폭 확장이 필요한 경우 Transit Gateway를 사용합니다.
- 다수 VPC 연결이 필요한 경우 Transit Gateway로의 마이그레이션을 고려해야 합니다.
- ASN은 생성 후 변경할 수 없으므로 신중하게 계획해야 합니다.