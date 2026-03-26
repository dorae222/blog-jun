## 개요

AWS Transit Gateway(TGW)는 여러 VPC와 온프레미스 네트워크를 중앙 허브를 통해 연결하는 네트워크 전송 서비스입니다. Transit Gateway가 등장하기 전에는 VPC 간 연결을 위해 VPC Peering을 사용해야 했는데, N개의 VPC를 완전 연결(Full Mesh)하려면 N*(N-1)/2개의 Peering 연결이 필요했습니다. VPC가 10개만 되어도 45개의 Peering이 필요하며, 관리가 극도로 복잡해집니다.

Transit Gateway는 이 문제를 허브-스포크(Hub-and-Spoke) 모델로 해결합니다. 모든 VPC와 온프레미스 연결을 Transit Gateway라는 하나의 중앙 허브에 연결하면, 각 네트워크는 허브를 통해 다른 모든 네트워크와 통신할 수 있습니다. N개의 네트워크를 연결하는 데 N개의 Attachment만 필요합니다.

Transit Gateway는 단순한 연결 허브를 넘어서 고급 라우팅 기능, 네트워크 세그멘테이션, 멀티캐스트, 그리고 리전 간 피어링까지 지원하는 강력한 네트워크 서비스입니다. 이 글에서는 Transit Gateway의 모든 핵심 기능과 실전 활용법을 상세히 살펴보겠습니다.

## 핵심 기능

### Attachment (연결)

Transit Gateway에 네트워크를 연결하는 것을 Attachment라고 합니다. 지원되는 Attachment 유형은 다음과 같습니다.

- **VPC Attachment**: VPC를 Transit Gateway에 연결합니다. 서브넷을 지정하여 연결하며, 각 가용 영역(AZ)에서 하나의 서브넷을 선택합니다.
- **VPN Attachment**: Site-to-Site VPN을 Transit Gateway에 연결합니다. ECMP를 지원하여 대역폭 확장이 가능합니다.
- **Direct Connect Gateway Attachment**: Direct Connect Gateway를 통해 온프레미스와 연결합니다.
- **Transit Gateway Peering Attachment**: 다른 리전 또는 다른 계정의 Transit Gateway와 피어링합니다.
- **Connect Attachment**: SD-WAN 등의 서드파티 가상 어플라이언스와 GRE 터널로 연결합니다.

### 라우팅 테이블

Transit Gateway는 독립적인 라우팅 테이블을 가지며, 이를 통해 네트워크 세그멘테이션을 구현할 수 있습니다.

**기본 라우팅 동작:**
- 기본 라우팅 테이블이 하나 생성됩니다.
- 모든 Attachment는 기본적으로 이 라우팅 테이블에 연결(Association)되고 경로를 전파(Propagation)합니다.
- 이 상태에서는 모든 네트워크가 서로 통신할 수 있습니다 (Any-to-Any).

**커스텀 라우팅 테이블:**
- 여러 개의 라우팅 테이블을 생성하여 네트워크를 분리할 수 있습니다.
- 각 Attachment는 하나의 라우팅 테이블에 연결되지만, 여러 라우팅 테이블에 경로를 전파할 수 있습니다.

```json
{
  "RouteTables": [
    {
      "Name": "prod-rt",
      "Associations": ["VPC-Prod-A", "VPC-Prod-B"],
      "Propagations": ["VPC-Prod-A", "VPC-Prod-B", "VPN-OnPrem"]
    },
    {
      "Name": "dev-rt",
      "Associations": ["VPC-Dev-A", "VPC-Dev-B"],
      "Propagations": ["VPC-Dev-A", "VPC-Dev-B"]
    },
    {
      "Name": "shared-rt",
      "Associations": ["VPC-Shared-Services"],
      "Propagations": ["VPC-Prod-A", "VPC-Prod-B", "VPC-Dev-A", "VPC-Dev-B"]
    }
  ]
}
```

### Appliance Mode

Appliance Mode는 VPC 내의 네트워크 어플라이언스(방화벽, IDS/IPS 등)를 통해 트래픽을 검사할 때 사용합니다. 이 모드를 활성화하면 Transit Gateway가 소스와 목적지 사이의 트래픽이 항상 동일한 AZ의 어플라이언스를 통과하도록 보장합니다. 이를 통해 스테이트풀 방화벽의 세션 유지 문제를 해결할 수 있습니다.

### Multicast

Transit Gateway는 멀티캐스트 라우팅을 지원합니다. IGMPv2 프로토콜을 사용하거나 정적 멀티캐스트 그룹을 구성할 수 있습니다. 미디어 스트리밍, 금융 데이터 피드 등의 워크로드에 유용합니다.

### Transit Gateway Network Manager

Network Manager는 글로벌 네트워크를 시각화하고 모니터링하는 서비스입니다. Transit Gateway, Site-to-Site VPN, Direct Connect, SD-WAN 등을 포함하는 전체 네트워크 토폴로지를 하나의 대시보드에서 확인할 수 있습니다.

## 아키텍처/동작 원리

### 허브-스포크 토폴로지

```
                    +-------------------+
                    | Transit Gateway   |
                    |                   |
        +-----------+---+---+-----------+
        |           |   |   |           |
   +----+---+  +----+--+  +-+----+  +---+----+
   | VPC    |  | VPC   |  | VPC  |  | VPN    |
   | Prod-A |  | Prod-B|  | Dev  |  | OnPrem |
   +--------+  +-------+  +------+  +--------+
```

이 토폴로지에서 Transit Gateway는 중앙 라우터 역할을 합니다. 각 VPC와 VPN은 Transit Gateway에 연결(Attach)되며, Transit Gateway의 라우팅 테이블에 따라 트래픽이 전달됩니다.

### 네트워크 세그멘테이션

실제 엔터프라이즈 환경에서는 모든 네트워크가 서로 통신하는 것은 보안상 바람직하지 않습니다. Transit Gateway의 라우팅 테이블을 활용하여 네트워크를 분리할 수 있습니다.

**격리된 네트워크 세그멘테이션 예시:**

```
Prod 라우팅 테이블:
  연결(Association): VPC-Prod-A, VPC-Prod-B
  전파(Propagation): VPC-Prod-A, VPC-Prod-B, VPC-Shared, VPN-OnPrem
  -> Prod VPC들은 서로 통신 가능, Shared VPC 및 OnPrem과 통신 가능

Dev 라우팅 테이블:
  연결(Association): VPC-Dev-A, VPC-Dev-B
  전파(Propagation): VPC-Dev-A, VPC-Dev-B, VPC-Shared
  -> Dev VPC들은 서로 통신 가능, Shared VPC와만 통신 가능 (OnPrem 접근 불가)

Shared 라우팅 테이블:
  연결(Association): VPC-Shared
  전파(Propagation): VPC-Prod-A, VPC-Prod-B, VPC-Dev-A, VPC-Dev-B, VPN-OnPrem
  -> Shared VPC는 모든 네트워크와 통신 가능
```

이 구성에서 Prod VPC와 Dev VPC는 서로 직접 통신할 수 없습니다. 두 환경 모두 Shared VPC(DNS, Active Directory 등)에는 접근할 수 있습니다.

### 크로스 리전 피어링

Transit Gateway Peering을 통해 서로 다른 리전의 Transit Gateway를 연결할 수 있습니다. 이를 통해 글로벌 네트워크를 구성할 수 있습니다.

```
ap-northeast-2 (서울)          us-east-1 (버지니아)
+------------------+           +------------------+
| TGW-Seoul        |<-- 피어링 -->| TGW-Virginia   |
|  +-- VPC-A       |           |  +-- VPC-C       |
|  +-- VPC-B       |           |  +-- VPC-D       |
+------------------+           +------------------+
```

Transit Gateway Peering은 정적 라우팅만 지원합니다. BGP 동적 라우팅은 지원하지 않으므로 경로를 수동으로 설정해야 합니다.

## 실전 활용

### Transit Gateway 생성 및 VPC 연결

```bash
# Transit Gateway 생성
aws ec2 create-transit-gateway \
  --description "Production Transit Gateway" \
  --options '{
    "AmazonSideAsn": 64512,
    "AutoAcceptSharedAttachments": "disable",
    "DefaultRouteTableAssociation": "disable",
    "DefaultRouteTablePropagation": "disable",
    "VpnEcmpSupport": "enable",
    "DnsSupport": "enable",
    "MulticastSupport": "disable"
  }' \
  --tag-specifications 'ResourceType=transit-gateway,Tags=[{Key=Name,Value=prod-tgw}]'
```

### VPC Attachment 생성

```bash
# Prod VPC-A Attachment
aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id tgw-0123456789abcdef0 \
  --vpc-id vpc-prod-a \
  --subnet-ids subnet-prod-a-az1 subnet-prod-a-az2 \
  --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=prod-vpc-a-attachment}]'

# Prod VPC-B Attachment
aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id tgw-0123456789abcdef0 \
  --vpc-id vpc-prod-b \
  --subnet-ids subnet-prod-b-az1 subnet-prod-b-az2 \
  --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=prod-vpc-b-attachment}]'

# Shared Services VPC Attachment
aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id tgw-0123456789abcdef0 \
  --vpc-id vpc-shared \
  --subnet-ids subnet-shared-az1 subnet-shared-az2 \
  --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=shared-vpc-attachment}]'
```

### 커스텀 라우팅 테이블로 네트워크 세그멘테이션 구현

```bash
# Prod 라우팅 테이블 생성
aws ec2 create-transit-gateway-route-table \
  --transit-gateway-id tgw-0123456789abcdef0 \
  --tag-specifications 'ResourceType=transit-gateway-route-table,Tags=[{Key=Name,Value=prod-rt}]'

# Dev 라우팅 테이블 생성
aws ec2 create-transit-gateway-route-table \
  --transit-gateway-id tgw-0123456789abcdef0 \
  --tag-specifications 'ResourceType=transit-gateway-route-table,Tags=[{Key=Name,Value=dev-rt}]'

# Shared 라우팅 테이블 생성
aws ec2 create-transit-gateway-route-table \
  --transit-gateway-id tgw-0123456789abcdef0 \
  --tag-specifications 'ResourceType=transit-gateway-route-table,Tags=[{Key=Name,Value=shared-rt}]'
```

### Attachment를 라우팅 테이블에 연결 및 전파 설정

```bash
# Prod VPC-A를 Prod 라우팅 테이블에 연결
aws ec2 associate-transit-gateway-route-table \
  --transit-gateway-route-table-id tgw-rtb-prod \
  --transit-gateway-attachment-id tgw-attach-prod-vpc-a

# Prod 라우팅 테이블에 Shared VPC 경로 전파
aws ec2 enable-transit-gateway-route-table-propagation \
  --transit-gateway-route-table-id tgw-rtb-prod \
  --transit-gateway-attachment-id tgw-attach-shared-vpc

# Shared 라우팅 테이블에 모든 VPC 경로 전파
aws ec2 enable-transit-gateway-route-table-propagation \
  --transit-gateway-route-table-id tgw-rtb-shared \
  --transit-gateway-attachment-id tgw-attach-prod-vpc-a

aws ec2 enable-transit-gateway-route-table-propagation \
  --transit-gateway-route-table-id tgw-rtb-shared \
  --transit-gateway-attachment-id tgw-attach-prod-vpc-b

aws ec2 enable-transit-gateway-route-table-propagation \
  --transit-gateway-route-table-id tgw-rtb-shared \
  --transit-gateway-attachment-id tgw-attach-dev-vpc-a
```

### 정적 경로 추가 (기본 경로 예시)

```bash
# Inspection VPC를 통한 인터넷 트래픽 라우팅 (0.0.0.0/0)
aws ec2 create-transit-gateway-route \
  --transit-gateway-route-table-id tgw-rtb-prod \
  --destination-cidr-block 0.0.0.0/0 \
  --transit-gateway-attachment-id tgw-attach-inspection-vpc
```

### RAM을 통한 Transit Gateway 공유 (멀티 계정)

AWS Resource Access Manager(RAM)를 사용하여 다른 계정과 Transit Gateway를 공유할 수 있습니다.

```bash
# RAM 리소스 공유 생성
aws ram create-resource-share \
  --name "tgw-shared-with-dev-account" \
  --resource-arns arn:aws:ec2:ap-northeast-2:123456789012:transit-gateway/tgw-0123456789abcdef0 \
  --principals 987654321098 \
  --tags Key=Environment,Value=Production

# 공유 상태 확인
aws ram get-resource-shares \
  --resource-owner SELF \
  --query 'resourceShares[*].{Name:name,Status:status,Principals:principals}' \
  --output table
```

### Transit Gateway 피어링 (크로스 리전)

```bash
# 서울 리전에서 버지니아 리전의 TGW와 피어링 요청
aws ec2 create-transit-gateway-peering-attachment \
  --transit-gateway-id tgw-seoul \
  --peer-transit-gateway-id tgw-virginia \
  --peer-region us-east-1 \
  --peer-account-id 123456789012 \
  --tag-specifications 'ResourceType=transit-gateway-attachment,Tags=[{Key=Name,Value=seoul-virginia-peering}]'

# 버지니아 리전에서 피어링 수락
aws ec2 accept-transit-gateway-peering-attachment \
  --transit-gateway-attachment-id tgw-attach-peering \
  --region us-east-1

# 피어링을 통한 정적 경로 추가
aws ec2 create-transit-gateway-route \
  --transit-gateway-route-table-id tgw-rtb-prod \
  --destination-cidr-block 10.100.0.0/16 \
  --transit-gateway-attachment-id tgw-attach-peering
```

### 모니터링

```bash
# Transit Gateway 상태 확인
aws ec2 describe-transit-gateways \
  --transit-gateway-ids tgw-0123456789abcdef0 \
  --query 'TransitGateways[0].{Id:TransitGatewayId,State:State,ASN:Options.AmazonSideAsn,ECMP:Options.VpnEcmpSupport}' \
  --output json

# Attachment 목록 확인
aws ec2 describe-transit-gateway-attachments \
  --filters 'Name=transit-gateway-id,Values=tgw-0123456789abcdef0' \
  --query 'TransitGatewayAttachments[*].{Id:TransitGatewayAttachmentId,Type:ResourceType,State:State,Name:Tags[?Key==`Name`]|[0].Value}' \
  --output table

# 라우팅 테이블 경로 확인
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id tgw-rtb-prod \
  --filters 'Name=type,Values=propagated,static' \
  --query 'Routes[*].{Destination:DestinationCidrBlock,Type:Type,State:State,Attachment:TransitGatewayAttachments[0].TransitGatewayAttachmentId}' \
  --output table
```

## 모범 사례/보안

### 설계 모범 사례

1. **기본 라우팅 테이블 사용을 비활성화합니다.** DefaultRouteTableAssociation과 DefaultRouteTablePropagation을 disable로 설정하여 명시적인 라우팅 제어를 수행합니다.

2. **전용 서브넷을 사용합니다.** VPC Attachment에 사용하는 서브넷은 워크로드 서브넷과 분리된 전용 서브넷(/28 이상)을 사용합니다.

3. **네트워크 세그멘테이션을 구현합니다.** 환경(Prod/Dev/Staging)별 또는 보안 요구사항별로 별도의 라우팅 테이블을 구성합니다.

4. **Shared Services VPC 패턴을 활용합니다.** DNS, Active Directory, 패키지 저장소 등의 공통 서비스를 Shared Services VPC에 배치하고 모든 환경에서 접근 가능하도록 합니다.

5. **Inspection VPC 패턴을 고려합니다.** 보안 요구사항에 따라 중앙 집중식 방화벽/IDS 검사를 위한 Inspection VPC를 구성합니다. 이때 Appliance Mode를 활성화합니다.

### 보안 모범 사례

1. **RAM을 통한 공유 시 최소 권한 원칙을 적용합니다.** 필요한 계정에만 Transit Gateway를 공유합니다.

2. **VPC 라우팅 테이블을 올바르게 설정합니다.** Transit Gateway Attachment가 있는 서브넷의 라우팅 테이블에 적절한 경로를 추가해야 합니다.

3. **Flow Logs를 활성화합니다.** Transit Gateway 수준의 Flow Logs를 활성화하여 네트워크 트래픽을 감사합니다.

4. **블랙홀 경로를 활용합니다.** 특정 CIDR에 대한 트래픽을 차단하려면 블랙홀 경로를 추가합니다.

```bash
# 블랙홀 경로 추가 (특정 CIDR 차단)
aws ec2 create-transit-gateway-route \
  --transit-gateway-route-table-id tgw-rtb-prod \
  --destination-cidr-block 10.99.0.0/16 \
  --blackhole
```

### 비용 고려사항

- Transit Gateway는 Attachment당 시간 요금 + 데이터 처리 요금이 부과됩니다.
- 같은 AZ 내의 통신은 데이터 전송 요금이 없지만, AZ 간 통신에는 추가 비용이 발생합니다.
- VPC Peering은 Transit Gateway보다 데이터 처리 비용이 낮으므로, 단순히 두 VPC 간 연결만 필요한 경우 VPC Peering이 더 비용 효율적일 수 있습니다.

## 관련 서비스 비교

| 특성 | Transit Gateway | VPC Peering | PrivateLink |
|------|----------------|-------------|-------------|
| 토폴로지 | 허브-스포크 | 점대점 | 서비스 지향 |
| 전이적 라우팅 | 지원 | 미지원 | 해당 없음 |
| CIDR 겹침 | 불가 | 불가 | 허용 |
| 대역폭 | 50 Gbps/AZ | 무제한 | 10 Gbps |
| 온프레미스 연결 | VPN/DX 지원 | 미지원 | 간접 지원 |
| 멀티캐스트 | 지원 | 미지원 | 미지원 |
| 크로스 리전 | 피어링 지원 | 지원 | 지원 |
| 비용 | 시간+데이터 | 데이터만 | 시간+데이터 |

## 요약

AWS Transit Gateway는 대규모 네트워크 아키텍처의 핵심 구성 요소입니다. 주요 내용을 정리하면 다음과 같습니다.

- 허브-스포크 모델로 VPC, VPN, Direct Connect를 중앙에서 관리합니다.
- 커스텀 라우팅 테이블을 통해 네트워크 세그멘테이션을 구현할 수 있습니다.
- ECMP를 지원하여 VPN 대역폭을 확장할 수 있습니다.
- RAM을 통해 멀티 계정 환경에서 Transit Gateway를 공유할 수 있습니다.
- Transit Gateway Peering으로 리전 간 연결이 가능합니다.
- Appliance Mode를 활성화하면 스테이트풀 방화벽과의 통합이 가능합니다.
- 기본 라우팅 테이블을 비활성화하고 명시적인 라우팅 제어를 수행하는 것이 모범 사례입니다.
- VPC Peering 대비 비용이 높을 수 있으므로, 네트워크 규모와 복잡성에 따라 적절한 서비스를 선택해야 합니다.