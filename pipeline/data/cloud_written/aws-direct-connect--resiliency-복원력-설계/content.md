<!-- infographic-hero -->
![AWS Direct Connect Resiliency(복원력) 설계 핵심 요약](figures/infographic.svg)

*Figure: AWS Direct Connect Resiliency(복원력) 설계 한 장 요약 인포그래픽*

## 개요

AWS Direct Connect는 온프레미스 데이터센터와 AWS 클라우드 간에 전용 네트워크 연결을 제공하는 서비스입니다. 인터넷을 경유하지 않고 AWS와 직접 연결하기 때문에 일관된 네트워크 성능, 낮은 지연 시간, 높은 대역폭을 확보할 수 있습니다.

그러나 Direct Connect 연결 자체가 단일 장애점(Single Point of Failure)이 될 수 있다는 점은 반드시 고려해야 합니다. 물리적 회선 장애, Direct Connect 로케이션 장애, 또는 AWS 리전 내 이슈가 발생할 경우 전체 하이브리드 네트워크가 단절될 수 있습니다. 따라서 프로덕션 환경에서는 복원력(Resiliency) 설계가 필수적입니다.

AWS는 Direct Connect Resiliency Toolkit을 통해 네 가지 복원력 모델을 제시하고 있으며, 각 모델은 비용과 복원력 수준 사이의 트레이드오프를 나타냅니다. 이 글에서는 각 복원력 모델의 아키텍처, 구성 방법, 장애 시나리오별 동작, 그리고 실전에서 고려해야 할 사항을 상세히 살펴보겠습니다.

## 핵심 기능

### Direct Connect Resiliency Toolkit

AWS는 2019년에 Direct Connect Resiliency Toolkit을 도입하여 복원력 설계를 체계화했습니다. 이 툴킷은 AWS Management Console에서 직접 사용할 수 있으며, 복원력 수준에 따라 네 가지 모델을 제공합니다.

**1. Maximum Resiliency (최대 복원력)**

최대 복원력 모델은 서로 다른 두 개의 Direct Connect 로케이션에 각각 두 개의 연결을 구성하여 총 네 개의 연결을 사용합니다. 이 구성에서는 단일 연결 장애, 단일 로케이션 장애, 심지어 한 로케이션의 모든 연결이 동시에 실패하더라도 서비스가 중단되지 않습니다.

**2. High Resiliency (높은 복원력)**

높은 복원력 모델은 서로 다른 두 개의 Direct Connect 로케이션에 각각 하나의 연결을 구성합니다. 총 두 개의 연결을 사용하며, 단일 연결 장애 또는 단일 로케이션 장애 시에도 서비스가 유지됩니다. 대부분의 프로덕션 환경에서 권장되는 모델입니다.

**3. Development and Test (개발/테스트)**

단일 Direct Connect 로케이션에 두 개의 연결을 구성합니다. 단일 연결 장애에는 대응할 수 있지만, 로케이션 자체의 장애에는 대응할 수 없습니다. 개발 및 테스트 환경에 적합합니다.

**4. 단일 연결 (No Resiliency)**

하나의 Direct Connect 로케이션에 하나의 연결만 구성하는 모델입니다. 복원력이 전혀 없으므로 프로덕션 환경에서는 권장하지 않습니다.

### Link Aggregation Group (LAG)

LAG는 여러 개의 Direct Connect 연결을 하나의 논리적 인터페이스로 묶어 관리하는 기능입니다. LAG를 사용하면 여러 연결의 대역폭을 집약할 수 있으며, 하나의 BGP 세션으로 여러 물리적 연결을 관리할 수 있습니다.

```json
{
  "lagName": "MyProductionLAG",
  "connectionsBandwidth": "10Gbps",
  "numberOfConnections": 2,
  "location": "EqTY2",
  "minimumLinks": 1
}
```

LAG의 `minimumLinks` 파라미터는 LAG가 활성 상태를 유지하기 위한 최소 연결 수를 지정합니다. 이 값 이하로 활성 연결이 줄어들면 LAG 전체가 비활성화됩니다.

### Bidirectional Forwarding Detection (BFD)

BFD는 BGP 세션의 장애를 빠르게 감지하기 위한 프로토콜입니다. 기본 BGP keepalive 타이머는 장애 감지까지 수십 초가 걸릴 수 있지만, BFD를 활성화하면 300ms 이내에 장애를 감지하고 페일오버를 시작할 수 있습니다.

Direct Connect에서 BFD는 기본적으로 비활성화되어 있으므로 라우터 측에서 명시적으로 설정해야 합니다.

## 아키텍처/동작 원리

### Maximum Resiliency 아키텍처

Maximum Resiliency 모델의 전체 아키텍처를 살펴보겠습니다.

```
온프레미스 DC
    |
    +-- Router A --+-- DX 연결 1 --> DX 로케이션 A --> AWS (VGW/DXGW)
    |              +-- DX 연결 2 --> DX 로케이션 A --> AWS (VGW/DXGW)
    |
    +-- Router B --+-- DX 연결 3 --> DX 로케이션 B --> AWS (VGW/DXGW)
                   +-- DX 연결 4 --> DX 로케이션 B --> AWS (VGW/DXGW)
```

이 아키텍처에서 핵심 원칙은 **단일 장애점 제거**입니다.

- **물리적 다양성(Physical Diversity)**: 서로 다른 두 개의 DX 로케이션을 사용하여 로케이션 수준의 장애에 대비합니다.
- **디바이스 다양성(Device Diversity)**: 온프레미스 측에서도 서로 다른 두 대의 라우터를 사용하여 장비 장애에 대비합니다.
- **연결 다양성(Connection Diversity)**: 각 로케이션에 두 개의 연결을 구성하여 단일 연결 장애에 대비합니다.

### BGP 라우팅과 페일오버 메커니즘

Direct Connect는 BGP(Border Gateway Protocol)를 사용하여 라우팅 정보를 교환합니다. 복원력 구성에서 페일오버는 BGP 라우팅 메커니즘을 통해 자동으로 이루어집니다.

**Active/Active 구성**에서는 모든 연결이 동시에 트래픽을 전달합니다. BGP AS-PATH prepending이나 Local Preference를 사용하여 트래픽 분배를 제어할 수 있습니다.

**Active/Passive 구성**에서는 주 연결(Active)이 장애 시 보조 연결(Passive)로 자동 전환됩니다. 이때 AS-PATH prepending을 사용하여 보조 경로의 우선순위를 낮춥니다.

```
# Active 경로: AS-PATH = 65001
# Passive 경로: AS-PATH = 65001 65001 65001 (prepended)
```

페일오버 시간은 BFD 설정 여부에 따라 크게 달라집니다.

| 구성 | 장애 감지 시간 | 페일오버 완료 시간 |
|------|---------------|-------------------|
| BGP만 사용 | 90초 (기본 holdtime) | 90~120초 |
| BGP + BFD | 300ms | 1~2초 |

### Direct Connect Gateway와의 통합

Direct Connect Gateway(DXGW)를 사용하면 하나의 Direct Connect 연결로 여러 리전의 VPC에 접근할 수 있습니다. 복원력 구성에서 DXGW는 중요한 역할을 합니다.

```
DX 연결 1 (로케이션 A) --> VIF --> DXGW --> VGW (ap-northeast-2)
DX 연결 2 (로케이션 B) --> VIF --> DXGW --> VGW (ap-northeast-2)
                                         --> VGW (us-east-1)
```

DXGW를 사용할 때 중요한 점은, 하나의 DXGW에 연결된 모든 VIF가 Active/Active로 동작한다는 것입니다. AWS는 가장 짧은 AS-PATH를 가진 경로를 선호하므로, 경로 제어를 위해서는 BGP 커뮤니티 태그를 활용해야 합니다.

## 실전 활용

### Maximum Resiliency 구성 실습

**Step 1: 첫 번째 DX 로케이션에 연결 생성**

```bash
# 첫 번째 로케이션에 연결 생성
aws directconnect create-connection \
  --location EqTY2 \
  --bandwidth 10Gbps \
  --connection-name "prod-dx-loc1-conn1" \
  --tags Key=Environment,Value=Production Key=Location,Value=Primary

# 같은 로케이션에 두 번째 연결 생성
aws directconnect create-connection \
  --location EqTY2 \
  --bandwidth 10Gbps \
  --connection-name "prod-dx-loc1-conn2" \
  --tags Key=Environment,Value=Production Key=Location,Value=Primary
```

**Step 2: 두 번째 DX 로케이션에 연결 생성**

```bash
# 두 번째 로케이션에 연결 생성
aws directconnect create-connection \
  --location EqTY5 \
  --bandwidth 10Gbps \
  --connection-name "prod-dx-loc2-conn1" \
  --tags Key=Environment,Value=Production Key=Location,Value=Secondary

# 같은 로케이션에 두 번째 연결 생성
aws directconnect create-connection \
  --location EqTY5 \
  --bandwidth 10Gbps \
  --connection-name "prod-dx-loc2-conn2" \
  --tags Key=Environment,Value=Production Key=Location,Value=Secondary
```

**Step 3: Direct Connect Gateway 생성**

```bash
# DXGW 생성
aws directconnect create-direct-connect-gateway \
  --direct-connect-gateway-name "prod-dxgw" \
  --amazon-side-asn 64512
```

**Step 4: Virtual Interface(VIF) 생성**

각 연결에 Private VIF를 생성하여 DXGW에 연결합니다.

```bash
# 첫 번째 연결에 Private VIF 생성
aws directconnect create-private-virtual-interface \
  --connection-id dxcon-xxxxxxx1 \
  --new-private-virtual-interface \
    virtualInterfaceName=prod-vif-loc1-1,\
    vlan=100,\
    asn=65001,\
    authKey=MyBGPAuthKey1,\
    amazonAddress=169.254.100.1/30,\
    customerAddress=169.254.100.2/30,\
    directConnectGatewayId=dxgw-xxxxxxxx
```

**Step 5: VGW를 DXGW에 연결**

```bash
# Virtual Private Gateway를 DXGW에 연결
aws directconnect create-direct-connect-gateway-association \
  --direct-connect-gateway-id dxgw-xxxxxxxx \
  --gateway-id vgw-xxxxxxxx \
  --add-allowed-prefixes-to-direct-connect-gateway \
    cidr=10.0.0.0/8
```

### LAG 구성

```bash
# LAG 생성
aws directconnect create-lag \
  --location EqTY2 \
  --number-of-connections 2 \
  --connections-bandwidth 10Gbps \
  --lag-name "prod-lag-loc1" \
  --tags Key=Environment,Value=Production

# 기존 연결을 LAG에 추가
aws directconnect associate-connection-with-lag \
  --connection-id dxcon-xxxxxxx1 \
  --lag-id dxlag-xxxxxxxx

# LAG 상태 확인
aws directconnect describe-lags \
  --lag-id dxlag-xxxxxxxx
```

### 연결 상태 모니터링

```bash
# 모든 Direct Connect 연결 상태 확인
aws directconnect describe-connections \
  --query 'connections[*].{Name:connectionName,State:connectionState,Bandwidth:bandwidth,Location:location}' \
  --output table

# VIF 상태 확인
aws directconnect describe-virtual-interfaces \
  --query 'virtualInterfaces[*].{Name:virtualInterfaceName,State:virtualInterfaceState,VLAN:vlan,BGPStatus:bgpPeers[0].bgpStatus}' \
  --output table

# CloudWatch를 통한 연결 메트릭 확인
aws cloudwatch get-metric-statistics \
  --namespace AWS/DX \
  --metric-name ConnectionState \
  --dimensions Name=ConnectionId,Value=dxcon-xxxxxxx1 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Average
```

### VPN을 백업으로 구성

Direct Connect의 백업으로 Site-to-Site VPN을 구성하는 것도 일반적인 복원력 패턴입니다. VPN은 인터넷을 통해 연결되므로 Direct Connect 인프라 전체가 장애인 경우에도 연결을 유지할 수 있습니다.

```bash
# Customer Gateway 생성
aws ec2 create-customer-gateway \
  --type ipsec.1 \
  --public-ip 203.0.113.1 \
  --bgp-asn 65001 \
  --tag-specifications 'ResourceType=customer-gateway,Tags=[{Key=Name,Value=prod-cgw}]'

# VPN Connection 생성 (VGW에 연결)
aws ec2 create-vpn-connection \
  --type ipsec.1 \
  --customer-gateway-id cgw-xxxxxxxx \
  --vpn-gateway-id vgw-xxxxxxxx \
  --options '{"StaticRoutesOnly":false}' \
  --tag-specifications 'ResourceType=vpn-connection,Tags=[{Key=Name,Value=prod-vpn-backup}]'
```

Direct Connect와 VPN이 동일한 VGW에 연결된 경우, AWS는 항상 Direct Connect 경로를 우선합니다. Direct Connect 경로가 사라지면 자동으로 VPN 경로로 페일오버됩니다.

### 장애 테스트 (Resiliency Testing)

AWS는 Direct Connect Resiliency Toolkit의 일부로 Failover Testing 기능을 제공합니다. 이를 통해 실제 연결을 일시적으로 비활성화하여 페일오버 동작을 검증할 수 있습니다.

```bash
# 장애 테스트 시작 (특정 VIF에 대해 BGP 세션 중단)
aws directconnect start-bgp-failover-test \
  --virtual-interface-id dxvif-xxxxxxxx \
  --bgp-peers 169.254.100.1 \
  --test-duration-in-minutes 10

# 테스트 상태 확인
aws directconnect list-virtual-interface-test-history \
  --virtual-interface-id dxvif-xxxxxxxx \
  --status in-progress

# 테스트 중단
aws directconnect stop-bgp-failover-test \
  --virtual-interface-id dxvif-xxxxxxxx \
  --test-id dxtest-xxxxxxxx
```

## 모범 사례/보안

### 복원력 설계 모범 사례

1. **프로덕션 환경에서는 최소 High Resiliency 이상을 구성합니다.** 서로 다른 DX 로케이션에 연결을 분산하여 로케이션 수준의 장애에 대비해야 합니다.

2. **BFD를 반드시 활성화합니다.** BGP 기본 keepalive 타이머만으로는 장애 감지에 최대 90초가 걸릴 수 있습니다. BFD를 활성화하면 300ms 이내로 단축할 수 있습니다.

3. **VPN 백업을 구성합니다.** Direct Connect 인프라 전체 장애에 대비하여 Site-to-Site VPN을 백업 경로로 구성하는 것을 권장합니다. 다만 VPN은 Direct Connect 대비 대역폭과 지연 시간이 열등하므로 이를 감안해야 합니다.

4. **정기적으로 장애 테스트를 수행합니다.** AWS의 Failover Testing 기능을 활용하여 분기별 또는 반기별로 페일오버 동작을 검증해야 합니다.

5. **CloudWatch 알람을 설정합니다.** ConnectionState, VirtualInterfaceBpsEgress/Ingress 등의 메트릭에 대해 알람을 설정하여 장애를 빠르게 인지할 수 있도록 합니다.

### 보안 고려사항

1. **BGP 인증을 사용합니다.** VIF 생성 시 BGP MD5 인증 키를 설정하여 BGP 세션의 무결성을 보장합니다.

2. **MACsec 암호화를 고려합니다.** 10Gbps 및 100Gbps 전용 연결에서는 MACsec(IEEE 802.1AE)를 지원합니다. MACsec를 활성화하면 Direct Connect 연결 구간의 데이터가 암호화됩니다.

```bash
# MACsec 키 연결 생성
aws directconnect associate-mac-sec-key \
  --connection-id dxcon-xxxxxxx1 \
  --secret-arn arn:aws:secretsmanager:ap-northeast-2:123456789012:secret:MacSecKey
```

3. **IAM 정책으로 Direct Connect 리소스 접근을 제한합니다.** 최소 권한 원칙에 따라 필요한 작업만 허용하도록 IAM 정책을 구성합니다.

4. **CloudTrail을 통해 API 호출을 감사합니다.** Direct Connect 관련 모든 API 호출이 CloudTrail에 기록되므로 이를 모니터링하여 비정상적인 활동을 탐지합니다.

### 비용 최적화

- 복원력 수준이 높을수록 비용도 증가합니다. Maximum Resiliency는 네 개의 연결 비용이 발생하므로, 워크로드의 중요도에 따라 적절한 복원력 수준을 선택해야 합니다.
- Hosted Connection을 사용하면 전용 연결보다 낮은 비용으로 Direct Connect를 이용할 수 있습니다. 다만 대역폭이 제한적입니다.
- 데이터 전송 비용도 고려해야 합니다. Direct Connect를 통한 아웃바운드 데이터 전송 비용은 인터넷 전송보다 저렴하지만, 무료는 아닙니다.

## 관련 서비스 비교

| 특성 | Direct Connect (Maximum Resiliency) | Direct Connect (High Resiliency) | Site-to-Site VPN |
|------|--------------------------------------|-----------------------------------|------------------|
| 복원력 수준 | 매우 높음 | 높음 | 중간 |
| 연결 수 | 4개 (2 로케이션 x 2) | 2개 (2 로케이션 x 1) | 2개 (터널) |
| 대역폭 | 최대 400Gbps | 최대 200Gbps | 최대 1.25Gbps |
| 지연 시간 | 매우 낮음 | 매우 낮음 | 가변적 |
| 구축 시간 | 수주~수개월 | 수주~수개월 | 수분~수시간 |
| 월 비용 (예시) | 높음 | 중간 | 낮음 |
| 암호화 | MACsec (옵션) | MACsec (옵션) | IPsec (기본) |
| 로케이션 장애 대응 | 가능 | 가능 | 해당 없음 |

### Direct Connect vs VPN

Direct Connect는 전용 물리적 연결을 사용하므로 일관된 성능을 제공하지만, 구축에 시간이 오래 걸리고 비용이 높습니다. VPN은 인터넷을 통해 빠르게 구축할 수 있지만 대역폭이 제한적이고 지연 시간이 가변적입니다.

가장 좋은 방법은 두 가지를 함께 사용하는 것입니다. Direct Connect를 주 연결로, VPN을 백업으로 구성하면 비용 효율적이면서도 높은 가용성을 확보할 수 있습니다.

### Direct Connect Gateway vs Transit Gateway

Direct Connect Gateway는 Direct Connect 연결을 여러 리전의 VPC에 분배하는 역할을 합니다. Transit Gateway는 여러 VPC와 온프레미스 네트워크를 중앙 허브로 연결하는 역할을 합니다. 두 서비스를 함께 사용하면 대규모 하이브리드 네트워크를 효율적으로 구성할 수 있습니다.

## 요약

AWS Direct Connect의 복원력 설계는 프로덕션 환경에서 반드시 고려해야 하는 핵심 아키텍처 요소입니다. 주요 내용을 정리하면 다음과 같습니다.

- AWS는 네 가지 복원력 모델(Maximum, High, Dev/Test, No Resiliency)을 제공하며, 프로덕션에서는 최소 High Resiliency 이상을 권장합니다.
- Maximum Resiliency는 서로 다른 두 DX 로케이션에 각각 두 개의 연결을 구성하여 총 네 개의 연결로 최대 복원력을 확보합니다.
- LAG를 사용하여 여러 물리적 연결을 하나의 논리적 인터페이스로 관리할 수 있습니다.
- BFD를 활성화하면 장애 감지 시간을 300ms 이내로 단축할 수 있습니다.
- Site-to-Site VPN을 백업 경로로 구성하여 Direct Connect 인프라 전체 장애에 대비할 수 있습니다.
- AWS의 Failover Testing 기능을 통해 정기적으로 페일오버 동작을 검증해야 합니다.
- MACsec 암호화, BGP 인증, IAM 정책 등을 통해 보안을 강화할 수 있습니다.

복원력 수준은 비용과 직접적인 트레이드오프 관계에 있으므로, 워크로드의 중요도와 예산을 종합적으로 고려하여 적절한 모델을 선택하는 것이 중요합니다.