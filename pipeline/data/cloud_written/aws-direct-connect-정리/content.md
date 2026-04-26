<!-- infographic-hero -->
![AWS Direct Connect 정리 핵심 요약](figures/infographic.svg)

*Figure: AWS Direct Connect 정리 한 장 요약 인포그래픽*

# AWS Direct Connect 정리

## 개요

AWS Direct Connect(DX)는 사용자의 온프레미스 데이터센터, 지사, 코로케이션 환경과 AWS 간을 **전용 물리 회선으로 직접 연결**해 주는 네트워크 서비스입니다. 일반적인 인터넷 연결이나 VPN과 달리 **공용 인터넷을 거치지 않고 AWS 글로벌 백본 네트워크에 직접 접속**하므로, 더 안정적이고 빠르며 예측 가능한 네트워크 성능을 제공합니다.

Direct Connect는 포트당 1Gbps, 10Gbps, 100Gbps의 연결 속도를 지원하며, AWS 파트너를 통해 50Mbps부터 시작하는 소규모 연결도 가능합니다. 다만 물리적인 회선을 구성해야 하므로 **설치 기간이 한 달 이상** 소요되는 점을 반드시 고려해야 합니다.

기본적으로 암호화를 제공하지 않지만, 전용 물리 회선이므로 인터넷 기반 공격에 대한 노출이 원천적으로 차단됩니다. 추가적인 암호화가 필요한 경우 Direct Connect 위에 VPN(IPsec)을 구성하여 이중 보안을 적용할 수 있습니다.

## 핵심 기능

### 전용 물리 회선

Direct Connect는 인터넷이 아닌 **전용 물리적 선로**를 사용합니다. 이를 통해 인터넷 혼잡으로 인한 대역폭 변동이나 지연 시간 증가 없이 일관된 네트워크 성능을 보장합니다. 대용량 데이터 전송이 빈번한 환경에서는 인터넷 전송 비용을 절감하는 효과도 있습니다.

### 가상 인터페이스(Virtual Interface, VIF)

하나의 Direct Connect 물리 연결 위에 여러 개의 **가상 인터페이스(VIF)**를 생성하여 다양한 AWS 리소스에 접근할 수 있습니다.

| VIF 유형 | 용도 | 연결 대상 |
|---|---|---|
| **Private VIF** | VPC 내부 리소스에 프라이빗하게 접근 | EC2, RDS, ElastiCache 등 |
| **Public VIF** | AWS 퍼블릭 서비스에 직접 접근 | S3, DynamoDB, CloudFront 등 |
| **Transit VIF** | Transit Gateway를 통해 여러 VPC에 연결 | 다수의 VPC, VPN 연결 |

### 연결 유형

Direct Connect는 다양한 연결 유형을 제공하여 조직의 규모와 요구사항에 맞는 선택이 가능합니다.

| 유형 | 설명 | 대역폭 | 주체 |
|---|---|---|---|
| **Dedicated Connection** | AWS와 직접 계약하여 물리적 포트를 프로비저닝 | 1G/10G/100Gbps | 고객 직접 |
| **Hosted Connection** | AWS 파트너를 통해 가상 포트 제공 | 50Mbps ~ 10Gbps | AWS 파트너 |
| **Hosted VIF** | 파트너가 VIF만 제공하고 실제 포트는 공유 | 50Mbps ~ 5Gbps | AWS 파트너 |
| **LAG** | 여러 Dedicated Connection을 하나의 논리 연결로 묶음 | 여러 포트 묶음 | 고객 직접 |

### Link Aggregation Group (LAG)

LAG는 여러 개의 물리 연결을 하나의 논리적 연결로 번들링하여 대역폭을 확장하고 고가용성을 확보하는 기능입니다. LAG 내의 모든 연결은 동일한 속도여야 하며, 최소 연결 수(Minimum Links)를 설정하여 일정 수 이상의 활성 연결이 유지되지 않으면 전체 LAG가 비활성화되도록 구성할 수 있습니다.

### 고가용성 구성

Direct Connect는 단일 연결만으로는 단일 장애점(SPOF)이 됩니다. AWS에서는 다음과 같은 고가용성 구성을 권장합니다.

- **이중화 연결**: 서로 다른 Direct Connect Location에 두 개의 연결을 구성합니다.
- **VPN 백업**: Direct Connect가 실패할 경우 Site-to-Site VPN으로 자동 페일오버되도록 구성합니다.
- **Active/Passive 또는 Active/Active**: BGP 우선순위를 조정하여 트래픽 분산 또는 백업 경로를 설정합니다.

## 아키텍처/동작 원리

### Direct Connect의 전체 아키텍처

```text
[온프레미스 데이터센터]
        |
   (전용 광케이블)
        |
[Direct Connect Location]
   (AWS 라우터 + 고객 라우터)
        |
   (AWS 백본 네트워크)
        |
   +---------+---------+
   |         |         |
[Private  [Public   [Transit
  VIF]     VIF]      VIF]
   |         |         |
[VPC]    [S3 등]  [Transit GW]
                       |
              +--------+--------+
              |        |        |
           [VPC A]  [VPC B]  [VPC C]
```

### 동작 원리

1. **물리 연결 구성**: 사용자는 Direct Connect Location에 위치한 데이터센터에서 AWS Direct Connect 라우터까지 전용 이더넷 케이블(1Gbps ~ 100Gbps)로 연결합니다.
2. **BGP 세션 설정**: 사용자 라우터와 AWS 라우터 간에 BGP(Border Gateway Protocol) 세션을 설정하여 라우팅 정보를 교환합니다.
3. **VIF 생성**: 물리 연결 위에 Private VIF, Public VIF, Transit VIF 중 필요한 가상 인터페이스를 생성합니다.
4. **VLAN 태깅**: 각 VIF는 고유한 VLAN ID(802.1Q)로 태깅되어 하나의 물리 연결에서 논리적으로 분리됩니다.
5. **트래픽 라우팅**: BGP를 통해 온프레미스와 AWS 간의 라우팅 경로가 자동으로 교환되고, 이에 따라 트래픽이 전달됩니다.

### 암호화 옵션

Direct Connect 자체는 기본적으로 암호화를 제공하지 않습니다. 하지만 다음과 같은 방법으로 암호화를 적용할 수 있습니다.

- **Direct Connect + VPN**: Direct Connect Public VIF 위에 Site-to-Site VPN을 구성하여 IPsec 암호화를 적용합니다.
- **MACsec(IEEE 802.1AE)**: 10Gbps 및 100Gbps Dedicated Connection에서 지원되는 레이어 2 암호화 기능입니다. 물리 회선 수준에서 암호화를 수행하므로 별도의 VPN 설정 없이도 전송 데이터를 보호할 수 있습니다.

## 실전 활용

### Direct Connect 연결 생성

```bash
# Dedicated Connection 생성 요청
aws directconnect create-connection \
  --location EqSL1 \
  --bandwidth 1Gbps \
  --connection-name "prod-dx-connection"
```

### Private VIF 생성

```bash
# Private Virtual Interface 생성
aws directconnect create-private-virtual-interface \
  --connection-id dxcon-abc12345 \
  --new-private-virtual-interface '{
    "virtualInterfaceName": "prod-private-vif",
    "vlan": 101,
    "asn": 65000,
    "authKey": "myBGPKey123",
    "amazonAddress": "169.254.100.1/30",
    "customerAddress": "169.254.100.2/30",
    "virtualGatewayId": "vgw-abc12345"
  }'
```

### Public VIF 생성

```bash
# Public Virtual Interface 생성 (S3, DynamoDB 등 접근용)
aws directconnect create-public-virtual-interface \
  --connection-id dxcon-abc12345 \
  --new-public-virtual-interface '{
    "virtualInterfaceName": "prod-public-vif",
    "vlan": 102,
    "asn": 65000,
    "authKey": "myBGPKey456",
    "amazonAddress": "203.0.113.1/30",
    "customerAddress": "203.0.113.2/30",
    "routeFilterPrefixes": [{"cidr": "52.95.0.0/16"}]
  }'
```

### LAG 생성

```bash
# Link Aggregation Group 생성
aws directconnect create-lag \
  --location EqSL1 \
  --number-of-connections 2 \
  --connections-bandwidth 10Gbps \
  --lag-name "prod-lag" \
  --minimum-links 1
```

### 연결 상태 확인

```bash
# Direct Connect 연결 상태 조회
aws directconnect describe-connections

# VIF 상태 조회
aws directconnect describe-virtual-interfaces

# LAG 상태 조회
aws directconnect describe-lags
```

### CloudWatch 모니터링

```bash
# Direct Connect 연결의 상태 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace AWS/DX \
  --metric-name ConnectionState \
  --dimensions Name=ConnectionId,Value=dxcon-abc12345 \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 300 \
  --statistics Average
```

## 모범 사례 및 보안

### 고가용성 설계

- **이중 연결 필수**: 프로덕션 환경에서는 반드시 서로 다른 Direct Connect Location에 두 개 이상의 연결을 구성합니다.
- **VPN 백업 구성**: Direct Connect 연결 실패 시 Site-to-Site VPN으로 자동 페일오버되도록 설계합니다. BGP 우선순위 설정으로 Direct Connect가 복구되면 자동으로 전환됩니다.
- **장애 테스트**: AWS Resiliency Toolkit을 활용하여 정기적으로 장애 시나리오를 테스트합니다.

### 보안 모범 사례

- **MACsec 활성화**: 10G/100G Dedicated Connection에서는 MACsec을 활성화하여 레이어 2 암호화를 적용합니다.
- **VPN over DX**: 민감한 데이터 전송이 필요한 경우 Direct Connect 위에 VPN을 구성하여 IPsec 암호화를 추가합니다.
- **VLAN 분리**: Private VIF와 Public VIF를 별도의 VLAN으로 분리하여 트래픽을 격리합니다.
- **BGP 인증**: MD5 인증 키를 사용하여 BGP 세션을 보호합니다.

### 비용 최적화

- **데이터 전송 방향 고려**: AWS에서 온프레미스로의 데이터 전송(Data Transfer Out)에 요금이 발생합니다. 반대 방향은 무료입니다.
- **리전 내 전송 비용 확인**: Direct Connect를 통한 데이터 전송 비용은 리전마다 다르므로, 사전에 비용을 산정합니다.
- **Hosted Connection 검토**: 1Gbps 미만의 대역폭이 필요한 경우 Dedicated Connection보다 Hosted Connection이 비용 효율적입니다.

## 관련 서비스 비교

| 항목 | AWS Direct Connect | AWS Site-to-Site VPN | AWS Client VPN | AWS Transit Gateway |
|---|---|---|---|---|
| 연결 경로 | 전용 물리 회선 | 인터넷(IPsec 암호화) | 인터넷(OpenVPN/IKEv2) | 허브형 라우팅 |
| 지연 시간 | 매우 낮음 | 인터넷 품질에 의존 | 인터넷 품질에 의존 | AWS 내부 네트워크 |
| 최대 대역폭 | 100Gbps | ~1.25Gbps/터널 | 제한적 | VPC당 50Gbps |
| 안정성 | 매우 높음 | 인터넷 영향 | 인터넷 영향 | 매우 높음 |
| 암호화 | 선택적(MACsec/VPN) | IPsec 기본 | TLS 기본 | 경유 트래픽에 의존 |
| 설치 기간 | 1개월 이상 | 수분 | 수분 | 수분 |
| 비용 | 높음(회선 + 포트) | 저렴 | 저렴 | 중간 |
| 적합 환경 | 대용량 전송, 금융, 게임 | 소규모 하이브리드 | 원격 접속 | 다수 VPC 연결 |

## 요약

AWS Direct Connect는 온프레미스와 AWS 간의 **고속, 저지연, 고안정성 전용 네트워크 연결**을 제공하는 서비스입니다. 인터넷을 거치지 않는 전용 물리 회선을 사용하므로 일관된 네트워크 성능을 보장하며, 대용량 데이터 전송에서의 비용 효율성도 뛰어납니다.

| 항목 | 내용 |
|---|---|
| 서비스명 | AWS Direct Connect (DX) |
| 핵심 가치 | 전용 물리 회선 기반의 고속, 저지연 AWS 연결 |
| 지원 대역폭 | 50Mbps ~ 100Gbps |
| VIF 유형 | Private VIF, Public VIF, Transit VIF |
| 연결 유형 | Dedicated, Hosted Connection, Hosted VIF, LAG |
| 설치 소요 시간 | 1개월 이상 |
| 암호화 | 기본 미제공, MACsec 또는 VPN over DX로 적용 가능 |
| 적합 환경 | 금융, 게임, 대기업, 하이브리드 클라우드 |

안정적인 하이브리드 클라우드 환경을 구축하고자 한다면, Direct Connect를 기반으로 하되 VPN 백업을 병행하는 아키텍처를 설계하는 것이 가장 바람직합니다.