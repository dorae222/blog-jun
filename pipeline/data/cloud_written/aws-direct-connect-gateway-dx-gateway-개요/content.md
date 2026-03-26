# AWS Direct Connect Gateway (DX Gateway) 심층 분석

## 개요

AWS Direct Connect Gateway(DX Gateway)는 Direct Connect 연결을 통해 여러 AWS 리전에 걸친 VPC(Virtual Private Cloud)와 Transit Gateway에 접근할 수 있게 해주는 글로벌 리소스입니다. DX Gateway가 없다면 각 리전의 VPC에 접근하기 위해 리전별로 별도의 Direct Connect 연결과 프라이빗 VIF를 설정해야 합니다. DX Gateway를 사용하면 하나의 Direct Connect 연결에서 전 세계의 VPC에 접근할 수 있습니다.

Direct Connect Gateway는 AWS 계정의 글로벌 리소스로, 특정 리전에 종속되지 않습니다. 하나의 DX Gateway에 최대 10개의 VGW(Virtual Private Gateway) 또는 Transit Gateway를 연결할 수 있으며, 최대 30개의 프라이빗 VIF 또는 트랜짓 VIF를 연결할 수 있습니다.

### DX Gateway가 필요한 이유

**DX Gateway 없이**: 서울 리전 VPC에 접근하려면 서울의 DX Location에서 연결을 설정하고, 도쿄 리전 VPC에도 접근하려면 도쿄의 DX Location에서 별도 연결을 설정해야 합니다.

**DX Gateway 사용**: 하나의 DX Location에서 하나의 연결을 설정하고, DX Gateway를 통해 서울, 도쿄, 버지니아 등 여러 리전의 VPC에 모두 접근할 수 있습니다.

이는 네트워크 구성을 대폭 단순화하고 비용을 절감하는 핵심 아키텍처 요소입니다.

## 핵심 기능

### 1. DX Gateway 생성

```bash
# Direct Connect Gateway 생성
aws directconnect create-direct-connect-gateway \
  --direct-connect-gateway-name "global-dx-gateway" \
  --amazon-side-asn 64512

# DX Gateway 목록 조회
aws directconnect describe-direct-connect-gateways \
  --query 'directConnectGateways[].{Id:directConnectGatewayId,Name:directConnectGatewayName,ASN:amazonSideAsn,State:directConnectGatewayState}' \
  --output table
```

amazon-side-asn은 DX Gateway에서 BGP로 사용할 ASN(Autonomous System Number)입니다. 64512-65534 범위의 프라이빗 ASN을 사용합니다.

### 2. VGW(Virtual Private Gateway) 연결

DX Gateway를 VPC의 VGW와 연결하면, Direct Connect를 통해 해당 VPC에 접근할 수 있습니다.

```bash
# 서울 리전 VPC에 VGW 생성
aws ec2 create-vpn-gateway \
  --type ipsec.1 \
  --amazon-side-asn 64513 \
  --region ap-northeast-2

# VGW를 VPC에 연결
aws ec2 attach-vpn-gateway \
  --vpn-gateway-id "vgw-seoul-abc123" \
  --vpc-id "vpc-seoul-abc123" \
  --region ap-northeast-2

# DX Gateway와 VGW 연결 (Virtual Gateway Association)
aws directconnect create-direct-connect-gateway-association \
  --direct-connect-gateway-id "dxgw-abc123" \
  --gateway-id "vgw-seoul-abc123" \
  --add-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.0.0.0/16"}]'

# 도쿄 리전 VGW도 동일한 DX Gateway에 연결
aws directconnect create-direct-connect-gateway-association \
  --direct-connect-gateway-id "dxgw-abc123" \
  --gateway-id "vgw-tokyo-def456" \
  --add-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.1.0.0/16"}]'

# 연결 상태 확인
aws directconnect describe-direct-connect-gateway-associations \
  --direct-connect-gateway-id "dxgw-abc123" \
  --query 'directConnectGatewayAssociations[].{GatewayId:associatedGateway.id,Region:associatedGateway.region,State:associationState,Prefixes:allowedPrefixesToDirectConnectGateway}' \
  --output table
```

### 3. Transit Gateway 연결

DX Gateway를 Transit Gateway(TGW)와 연결하면 TGW에 연결된 모든 VPC에 접근할 수 있습니다. 이는 대규모 환경에서 VPC 수가 많을 때 특히 유용합니다.

```bash
# Transit Gateway 생성
aws ec2 create-transit-gateway \
  --description "프로덕션 Transit Gateway" \
  --options '{
    "AmazonSideAsn": 64515,
    "AutoAcceptSharedAttachments": "disable",
    "DefaultRouteTableAssociation": "enable",
    "DefaultRouteTablePropagation": "enable",
    "DnsSupport": "enable"
  }' \
  --region ap-northeast-2

# DX Gateway와 Transit Gateway 연결 제안 생성
aws directconnect create-direct-connect-gateway-association-proposal \
  --direct-connect-gateway-id "dxgw-abc123" \
  --direct-connect-gateway-owner-account "111111111111" \
  --gateway-id "tgw-abc123" \
  --add-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.0.0.0/8"}]'

# 제안 수락 (DX Gateway 소유자 계정에서)
aws directconnect accept-direct-connect-gateway-association-proposal \
  --direct-connect-gateway-id "dxgw-abc123" \
  --association-proposal-id "proposal-abc123" \
  --associated-gateway-owner-account "222222222222" \
  --override-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.0.0.0/8"}]'
```

### 4. 프라이빗 VIF와 트랜짓 VIF 연결

DX Gateway에 VIF를 연결합니다.

```bash
# 프라이빗 VIF를 DX Gateway에 연결
aws directconnect create-private-virtual-interface \
  --connection-id "dxcon-abc123" \
  --new-private-virtual-interface '{
    "virtualInterfaceName": "private-vif-to-dxgw",
    "vlan": 101,
    "asn": 65000,
    "authKey": "bgp-auth-key",
    "amazonAddress": "169.254.100.1/30",
    "customerAddress": "169.254.100.2/30",
    "directConnectGatewayId": "dxgw-abc123",
    "addressFamily": "ipv4"
  }'

# 트랜짓 VIF를 DX Gateway에 연결 (TGW 사용 시)
aws directconnect create-transit-virtual-interface \
  --connection-id "dxcon-abc123" \
  --new-transit-virtual-interface '{
    "virtualInterfaceName": "transit-vif-to-dxgw",
    "vlan": 102,
    "asn": 65000,
    "authKey": "bgp-auth-key",
    "amazonAddress": "169.254.200.1/30",
    "customerAddress": "169.254.200.2/30",
    "directConnectGatewayId": "dxgw-abc123",
    "addressFamily": "ipv4"
  }'
```

### 5. 교차 계정(Cross-Account) 공유

DX Gateway는 AWS Organizations의 다른 계정과 공유할 수 있습니다. 하나의 계정에서 DX Gateway를 생성하고, 다른 계정의 VGW나 TGW와 연결할 수 있습니다.

```bash
# 계정 B에서 계정 A의 DX Gateway에 연결 제안
# (계정 B가 VGW/TGW를 소유)
aws directconnect create-direct-connect-gateway-association-proposal \
  --direct-connect-gateway-id "dxgw-abc123" \
  --direct-connect-gateway-owner-account "111111111111" \
  --gateway-id "vgw-account-b-abc123" \
  --add-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.2.0.0/16"}]'

# 계정 A(DX Gateway 소유자)에서 제안 확인
aws directconnect describe-direct-connect-gateway-association-proposals \
  --direct-connect-gateway-id "dxgw-abc123" \
  --query 'directConnectGatewayAssociationProposals[].{ProposalId:proposalId,State:proposalState,RequestAccount:requestedAllowedPrefixesToDirectConnectGateway}'

# 계정 A에서 제안 수락
aws directconnect accept-direct-connect-gateway-association-proposal \
  --direct-connect-gateway-id "dxgw-abc123" \
  --association-proposal-id "proposal-xyz789" \
  --associated-gateway-owner-account "222222222222"
```

## 아키텍처/동작 원리

### DX Gateway 아키텍처

```
[온프레미스]          [DX Gateway]              [AWS 리전별 VPC]
                    (글로벌 리소스)
+-----------+                              +-------------------+
|           |    +------------------+      | ap-northeast-2    |
| 라우터    |    |                  |      | +-------+         |
| (BGP)     |====| Private VIF     |====> | | VGW   |-> VPC-1 |
|           |    |  VLAN 101       |      | +-------+         |
|           |    |                  |      +-------------------+
|           |    |   DX Gateway    |
|           |    |   (dxgw-xxx)    |      +-------------------+
|           |    |                  |      | us-east-1         |
|           |    |  Transit VIF    |====> | +-------+         |
|           |====|  VLAN 102       |      | | TGW   |-> VPCs  |
|           |    |                  |      | +-------+         |
+-----------+    +------------------+      +-------------------+
                                          
                                          +-------------------+
                                          | eu-west-1         |
                                          | +-------+         |
                                     ====>| | VGW   |-> VPC-3 |
                                          | +-------+         |
                                          +-------------------+
```

### VGW 연결 vs TGW 연결 비교

| 항목 | VGW (프라이빗 VIF) | TGW (트랜짓 VIF) |
|------|-------------------|-------------------|
| VPC 접근 | VGW당 1개 VPC | TGW에 연결된 모든 VPC |
| 최대 연결 수 | DX Gateway당 10개 VGW | DX Gateway당 3개 TGW |
| VPC 간 통신 | 불가 (DX Gateway 경유) | TGW 라우팅으로 가능 |
| 대역폭 | 연결 대역폭 공유 | 연결 대역폭 공유 |
| 사용 사례 | 소수의 VPC | 다수의 VPC |
| 비용 | VIF만 과금 | TGW 데이터 처리 비용 추가 |

### 라우팅 동작 원리

DX Gateway를 통한 라우팅에서 중요한 제약사항이 있습니다.

**허용**: 온프레미스 -> DX Gateway -> VPC/TGW
**불허**: VPC-A -> DX Gateway -> VPC-B (DX Gateway를 통한 VPC 간 통신 불가)

이는 DX Gateway가 트래픽 전달(Transit) 목적이 아닌, 온프레미스와 AWS 간의 연결 목적으로 설계되었기 때문입니다. VPC 간 통신이 필요하면 Transit Gateway 또는 VPC Peering을 사용해야 합니다.

```bash
# 허용 접두사(Allowed Prefixes) 확인
# DX Gateway에서 온프레미스로 광고하는 경로를 제어합니다
aws directconnect describe-direct-connect-gateway-associations \
  --direct-connect-gateway-id "dxgw-abc123" \
  --query 'directConnectGatewayAssociations[].{Gateway:associatedGateway.id,Prefixes:allowedPrefixesToDirectConnectGateway[].cidr}' \
  --output json

# 허용 접두사 업데이트
aws directconnect update-direct-connect-gateway-association \
  --association-id "assoc-abc123" \
  --add-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.3.0.0/16"}]' \
  --remove-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.99.0.0/16"}]'
```

### 접두사 광고(Prefix Advertisement)

- **온프레미스 -> AWS 방향**: 고객 라우터에서 BGP로 온프레미스 네트워크 경로를 광고합니다.
- **AWS -> 온프레미스 방향**: DX Gateway가 연결된 VGW/TGW의 CIDR을 광고합니다. Allowed Prefixes로 광고 범위를 제어합니다.

## 실전 활용

### 사례 1: 글로벌 엔터프라이즈 네트워크

여러 리전에 VPC를 운영하는 글로벌 엔터프라이즈의 네트워크 구성입니다.

```bash
# 1. DX Gateway 생성 (한 번만)
aws directconnect create-direct-connect-gateway \
  --direct-connect-gateway-name "enterprise-dxgw" \
  --amazon-side-asn 64512

# 2. 서울 리전 VGW 연결
aws directconnect create-direct-connect-gateway-association \
  --direct-connect-gateway-id "dxgw-enterprise" \
  --gateway-id "vgw-seoul" \
  --add-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.10.0.0/16"}]'

# 3. 버지니아 리전 TGW 연결
aws directconnect create-direct-connect-gateway-association \
  --direct-connect-gateway-id "dxgw-enterprise" \
  --gateway-id "tgw-virginia" \
  --add-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.20.0.0/16"}, {"cidr": "10.21.0.0/16"}]'

# 4. 프랑크푸르트 리전 VGW 연결
aws directconnect create-direct-connect-gateway-association \
  --direct-connect-gateway-id "dxgw-enterprise" \
  --gateway-id "vgw-frankfurt" \
  --add-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.30.0.0/16"}]'
```

### 사례 2: 멀티 계정 환경에서의 DX 공유

AWS Organizations의 여러 계정이 하나의 Direct Connect 연결과 DX Gateway를 공유하는 패턴입니다.

```bash
# 네트워크 관리 계정에서 DX Gateway 생성
aws directconnect create-direct-connect-gateway \
  --direct-connect-gateway-name "shared-dxgw"

# 개발 계정의 TGW 연결 요청 수락
aws directconnect accept-direct-connect-gateway-association-proposal \
  --direct-connect-gateway-id "dxgw-shared" \
  --association-proposal-id "proposal-dev-123" \
  --associated-gateway-owner-account "333333333333" \
  --override-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.100.0.0/16"}]'

# 스테이징 계정의 VGW 연결 요청 수락
aws directconnect accept-direct-connect-gateway-association-proposal \
  --direct-connect-gateway-id "dxgw-shared" \
  --association-proposal-id "proposal-stg-456" \
  --associated-gateway-owner-account "444444444444" \
  --override-allowed-prefixes-to-direct-connect-gateway '[{"cidr": "10.200.0.0/16"}]'
```

### 사례 3: DX 이중화와 DX Gateway

두 개의 Direct Connect 연결에서 각각 VIF를 생성하고 동일한 DX Gateway에 연결하여 이중화를 구현합니다.

```bash
# 주 연결에서 프라이빗 VIF 생성
aws directconnect create-private-virtual-interface \
  --connection-id "dxcon-primary" \
  --new-private-virtual-interface '{
    "virtualInterfaceName": "primary-vif",
    "vlan": 101,
    "asn": 65000,
    "directConnectGatewayId": "dxgw-abc123",
    "addressFamily": "ipv4"
  }'

# 보조 연결에서 프라이빗 VIF 생성 (동일 DX Gateway)
aws directconnect create-private-virtual-interface \
  --connection-id "dxcon-secondary" \
  --new-private-virtual-interface '{
    "virtualInterfaceName": "secondary-vif",
    "vlan": 201,
    "asn": 65000,
    "directConnectGatewayId": "dxgw-abc123",
    "addressFamily": "ipv4"
  }'
```

## 모범 사례/보안

### 라우팅 설계

- Allowed Prefixes를 최소한으로 설정하여 의도하지 않은 경로 광고를 방지합니다.
- CIDR이 겹치지 않도록 IP 주소 계획을 수립합니다.
- BGP AS-PATH prepending으로 트래픽 경로 선호도를 제어합니다.

### IAM 접근 제어

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "directconnect:DescribeDirectConnectGateways",
        "directconnect:DescribeDirectConnectGatewayAssociations",
        "directconnect:DescribeDirectConnectGatewayAttachments"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "directconnect:CreateDirectConnectGatewayAssociation",
        "directconnect:DeleteDirectConnectGatewayAssociation",
        "directconnect:UpdateDirectConnectGatewayAssociation"
      ],
      "Resource": "arn:aws:directconnect::111111111111:dx-gateway/dxgw-*",
      "Condition": {
        "StringEquals": {
          "aws:PrincipalTag/Team": "NetworkOps"
        }
      }
    }
  ]
}
```

### 모니터링 및 알림

```bash
# DX Gateway 연결 상태 모니터링
aws directconnect describe-direct-connect-gateway-associations \
  --direct-connect-gateway-id "dxgw-abc123" \
  --query 'directConnectGatewayAssociations[].{Gateway:associatedGateway.id,State:associationState,StateChangeError:stateChangeError}'

# VIF 상태 모니터링
aws directconnect describe-virtual-interfaces \
  --query 'virtualInterfaces[?directConnectGatewayId==`dxgw-abc123`].{Name:virtualInterfaceName,State:virtualInterfaceState,BGPStatus:bgpPeers[0].bgpStatus}' \
  --output table
```

### 제한사항 인지

- DX Gateway당 최대 10개 VGW 연결
- DX Gateway당 최대 3개 TGW 연결
- DX Gateway당 최대 30개 VIF
- DX Gateway를 통한 VPC 간 통신 불가
- 하나의 VGW에 하나의 DX Gateway만 연결 가능

## 관련 서비스 비교

### DX Gateway + VGW vs DX Gateway + TGW

| 항목 | DX Gateway + VGW | DX Gateway + TGW |
|------|-----------------|------------------|
| 확장성 | VPC당 별도 VGW 필요 | TGW에 다수 VPC 연결 |
| VPC 간 라우팅 | 불가 | TGW 라우팅으로 가능 |
| 복잡성 | 단순 (소규모) | 복잡 (대규모에 적합) |
| 비용 | VIF 비용만 | TGW 데이터 처리 비용 추가 |
| 최대 VPC 수 | 10개 (DX Gateway 한도) | 수천 개 (TGW 한도) |

### Direct Connect Gateway vs Transit Gateway

| 항목 | DX Gateway | Transit Gateway |
|------|-----------|------------------|
| 역할 | DX 연결과 VPC/TGW 매핑 | VPC/VPN/DX 간 허브 라우터 |
| 범위 | 글로벌 | 리전별 (Inter-Region Peering 가능) |
| VPC 간 통신 | 불가 | 가능 |
| VPN 지원 | 불가 | 가능 |
| 비용 | 무료 (DX 비용에 포함) | 연결당 + 데이터 처리당 |

두 서비스는 상호 보완적입니다. DX Gateway는 온프레미스-AWS 간의 글로벌 연결을, Transit Gateway는 AWS 내부 네트워크 허브 역할을 담당합니다.

## 요약

AWS Direct Connect Gateway는 Direct Connect 연결을 여러 리전과 VPC에 확장하기 위한 핵심 글로벌 리소스입니다. 하나의 물리적 연결에서 전 세계 AWS 리전의 VPC에 접근할 수 있게 하여, 하이브리드 네트워크 아키텍처를 크게 단순화합니다.

핵심 포인트를 정리하면 다음과 같습니다.

- DX Gateway는 글로벌 리소스로, 하나의 DX 연결에서 여러 리전의 VPC/TGW에 접근할 수 있습니다.
- VGW 연결(프라이빗 VIF)은 소규모 환경에, TGW 연결(트랜짓 VIF)은 대규모 환경에 적합합니다.
- 교차 계정 공유를 통해 AWS Organizations의 여러 계정이 DX 연결을 공유할 수 있습니다.
- DX Gateway를 통한 VPC 간 통신은 불가능하므로, VPC 간 라우팅이 필요하면 Transit Gateway를 함께 사용해야 합니다.
- Allowed Prefixes를 최소한으로 설정하여 라우팅 보안을 확보합니다.
- 이중화를 위해 여러 VIF를 동일한 DX Gateway에 연결할 수 있습니다.
- DX Gateway 자체는 추가 비용이 없으며, Direct Connect 연결과 데이터 전송 비용만 발생합니다.