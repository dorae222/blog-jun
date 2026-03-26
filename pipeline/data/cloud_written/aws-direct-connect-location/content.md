# AWS Direct Connect Location - 물리적 네트워크 접속 지점 완벽 가이드

## 개요

AWS Direct Connect Location은 사용자의 온프레미스 네트워크를 AWS 클라우드에 전용 회선으로 직접 연결할 수 있는 물리적 데이터센터 시설입니다. 인터넷을 경유하지 않는 전용 네트워크 연결을 통해 안정적인 대역폭, 일관된 지연 시간, 강화된 보안을 확보할 수 있습니다.

Direct Connect Location은 전 세계 100개 이상의 도시에 분포하며, Equinix, Digital Realty, CyrusOne 등 글로벌 데이터센터 사업자와 현지 통신사업자가 운영하는 시설에 위치합니다. 한국에서는 서울 리전(ap-northeast-2)을 대상으로 LG U+ IDC, KINX 등에서 Direct Connect 접속이 가능합니다.

Direct Connect Location을 이해하는 것은 하이브리드 클라우드 아키텍처 설계에서 매우 중요합니다. 물리적 접속 지점의 위치, 가용 대역폭, 파트너 네트워크에 따라 연결 방식과 비용이 크게 달라지기 때문입니다.

## 핵심 기능

### 물리적 연결 유형

Direct Connect Location에서는 두 가지 물리적 연결 유형을 제공합니다.

| 연결 유형 | 대역폭 | 연결 방식 | 비용 |
|-----------|--------|-----------|------|
| Dedicated Connection | 1Gbps, 10Gbps, 100Gbps | 전용 물리 포트 | 포트 시간 + 데이터 전송 |
| Hosted Connection | 50Mbps ~ 10Gbps | 파트너 공유 포트 | 파트너 요금 + 데이터 전송 |

**Dedicated Connection**은 사용자가 직접 AWS 라우터의 물리 포트를 할당받는 방식입니다. Direct Connect Location 내에 장비를 배치(콜로케이션)하거나 크로스 커넥트를 통해 연결합니다.

**Hosted Connection**은 AWS Direct Connect Partner를 통해 논리적 연결을 제공받는 방식입니다. 물리적 인프라를 직접 관리할 필요가 없어 소규모 연결에 적합합니다.

### 콜로케이션 (Co-location)

Direct Connect Location 내에 사용자의 네트워크 장비(라우터, 스위치)를 직접 배치하여 AWS 라우터와 크로스 커넥트로 연결하는 방식입니다. 가장 낮은 지연 시간과 최대 제어권을 확보할 수 있습니다.

### Letter of Authorization (LOA-CFA)

Dedicated Connection을 생성하면 AWS가 LOA-CFA(Letter of Authorization and Connecting Facility Assignment) 문서를 발행합니다. 이 문서에는 AWS 라우터의 위치, 포트 번호, 크로스 커넥트 사양이 명시되어 있으며, 데이터센터 사업자에게 이 문서를 제출하여 물리적 케이블링을 요청합니다.

### Virtual Interface (VIF)

물리적 연결이 완료되면, 논리적 인터페이스인 VIF를 생성하여 실제 트래픽을 라우팅합니다.

| VIF 유형 | 용도 | 대상 |
|---------|------|------|
| Private VIF | VPC 내 리소스 접근 | Virtual Private Gateway / Direct Connect Gateway |
| Public VIF | AWS 퍼블릭 서비스 접근 | S3, DynamoDB 등 퍼블릭 엔드포인트 |
| Transit VIF | 여러 VPC 접근 | Transit Gateway |

### Direct Connect Gateway

Direct Connect Gateway를 사용하면 하나의 Direct Connect 연결로 여러 리전의 VPC에 접근할 수 있습니다. 리전 간 트래픽이 AWS 글로벌 백본 네트워크를 통해 전달되므로 인터넷을 경유하지 않습니다.

## 아키텍처 및 동작 원리

Direct Connect의 전체 연결 아키텍처는 다음과 같습니다.

```
[온프레미스 데이터센터]
    |
    | (전용 회선 / 파트너 회선)
    v
[Direct Connect Location]
    |-- [사용자 라우터] <-크로스 커넥트-> [AWS 라우터]
    |                                      |
    |                              [Direct Connect Endpoint]
    |                                      |
    |                              +-------+-------+
    |                              |               |
    |                        [Private VIF]   [Public VIF]
    |                              |               |
    |                        [VGW / DXGW]   [AWS Public Services]
    |                              |               (S3, DynamoDB...)
    |                        [VPC Subnets]
    |                              |
    |                        [EC2, RDS, etc.]
```

### BGP 라우팅

Direct Connect는 BGP(Border Gateway Protocol)를 사용하여 동적 라우팅을 수행합니다. 사용자의 라우터와 AWS 라우터 간 BGP 피어링을 설정하여 네트워크 경로를 교환합니다.

- Private VIF: 사용자의 프라이빗 ASN과 AWS의 프라이빗 ASN 간 피어링
- Public VIF: 사용자의 퍼블릭 ASN과 AWS의 퍼블릭 ASN(7224) 간 피어링
- MD5 인증을 통한 BGP 세션 보안

### 이중화 구성

AWS는 프로덕션 워크로드에 대해 최소 두 개의 Direct Connect 연결을 권장합니다.

- **동일 Location 이중화**: 같은 Location에 두 개의 Dedicated Connection
- **다중 Location 이중화**: 서로 다른 Location에 각각 하나씩 연결 (최고 수준 이중화)
- **Active/Passive**: 하나를 주 회선, 다른 하나를 백업으로 구성 (BGP AS Path Prepending)
- **Active/Active**: 두 회선을 동시 활용 (ECMP 또는 BGP 커뮤니티 기반 부하 분산)

## 실전 활용

### AWS CLI를 사용한 Direct Connect 관리

```bash
# 사용 가능한 Direct Connect Location 목록 조회
aws directconnect describe-locations \
    --query 'locations[?region==`ap-northeast-2`].{Name:locationName,Code:locationCode,Partners:availableProviders}' \
    --output table

# Dedicated Connection 생성 요청
aws directconnect create-connection \
    --location "KINX-Seoul" \
    --bandwidth 1Gbps \
    --connection-name prod-dc-primary \
    --tags '[{"key":"Environment","value":"production"},{"key":"Purpose","value":"primary"}]'

# LOA-CFA 다운로드
aws directconnect describe-loa \
    --connection-id dxcon-abc123 \
    --output-file-format pdf > loa-cfa.pdf

# 연결 상태 확인
aws directconnect describe-connections \
    --query 'connections[].{Name:connectionName,State:connectionState,Bandwidth:bandwidth,Location:location,VLAN:vlan}' \
    --output table

# Private Virtual Interface 생성
aws directconnect create-private-virtual-interface \
    --connection-id dxcon-abc123 \
    --new-private-virtual-interface '{
        "virtualInterfaceName": "prod-private-vif",
        "vlan": 101,
        "asn": 65000,
        "authKey": "my-bgp-auth-key",
        "amazonAddress": "169.254.100.1/30",
        "customerAddress": "169.254.100.2/30",
        "virtualGatewayId": "vgw-0abc123"
    }'

# Direct Connect Gateway 생성
aws directconnect create-direct-connect-gateway \
    --direct-connect-gateway-name global-dxgw \
    --amazon-side-asn 64512

# Transit VIF 생성 (Transit Gateway 연동)
aws directconnect create-transit-virtual-interface \
    --connection-id dxcon-abc123 \
    --new-transit-virtual-interface '{
        "virtualInterfaceName": "prod-transit-vif",
        "vlan": 201,
        "asn": 65000,
        "directConnectGatewayId": "dxgw-abc123"
    }'

# VIF BGP 피어 상태 확인
aws directconnect describe-virtual-interfaces \
    --query 'virtualInterfaces[].{Name:virtualInterfaceName,State:virtualInterfaceState,BGP:bgpPeers[0].bgpStatus,VLAN:vlan}' \
    --output table
```

### 한국 리전 Direct Connect 구성 예시

서울 리전에서 Direct Connect를 구성하는 일반적인 절차는 다음과 같습니다.

1. AWS 콘솔에서 Dedicated Connection 생성 (Location: KINX 또는 LG U+)
2. LOA-CFA 문서를 다운로드하여 데이터센터 사업자에 크로스 커넥트 요청
3. 물리적 연결 완료 후 Connection 상태가 'available'로 변경
4. Private VIF 생성하여 VPC와 연결
5. 온프레미스 라우터에서 BGP 설정
6. 라우팅 테이블 업데이트하여 트래픽 전환

파트너를 통한 Hosted Connection의 경우, AWS Direct Connect Partner(LG U+, KT, SK브로드밴드 등)에 연결을 신청하면 파트너가 물리적 인프라를 구성하고 논리적 연결을 제공합니다.

## 모범 사례 및 보안

### 고가용성 설계

- 프로덕션 워크로드에는 최소 2개의 Direct Connect 연결을 구성합니다.
- 서로 다른 Direct Connect Location에 각각 연결하여 단일 시설 장애에 대비합니다.
- VPN을 백업 경로로 구성하여 Direct Connect 전체 장애 시에도 연결을 유지합니다.
- BFD(Bidirectional Forwarding Detection)를 활성화하여 링크 장애를 빠르게 감지합니다.

### 보안

- BGP 세션에 MD5 인증을 적용하여 라우팅 스푸핑을 방지합니다.
- MACsec 암호화(10Gbps/100Gbps 전용)를 활성화하여 Layer 2 수준의 데이터 암호화를 적용합니다.
- Private VIF를 통해 VPC에 접근하면 인터넷을 경유하지 않으므로 트래픽 보안이 강화됩니다.
- IAM 정책으로 Direct Connect 리소스 생성/삭제 권한을 제한합니다.

### 비용 최적화

- 데이터 전송량이 월 10TB 미만이면 VPN이 더 비용 효율적일 수 있습니다.
- 데이터 전송량이 월 10TB 이상이면 Direct Connect가 VPN보다 저렴합니다.
- 여러 리전에 접근해야 하면 Direct Connect Gateway를 활용하여 단일 연결로 다중 리전에 접근합니다.
- 포트 시간 비용은 연결이 DOWN 상태여도 발생하므로, 미사용 연결은 즉시 삭제합니다.

## 관련 서비스 비교

| 항목 | Direct Connect (Dedicated) | Direct Connect (Hosted) | Site-to-Site VPN | Client VPN |
|------|---------------------------|------------------------|-----------------|------------|
| 연결 유형 | 전용 물리 포트 | 파트너 공유 포트 | IPSec 터널 | SSL/TLS |
| 대역폭 | 1/10/100 Gbps | 50Mbps~10Gbps | 최대 1.25 Gbps | 가변 |
| 지연 시간 | 가장 낮음 | 낮음 | 가변 (인터넷 경유) | 가변 |
| 이중화 | 수동 (다중 연결) | 수동 | 자동 (듀얼 터널) | 자동 |
| 구축 기간 | 수주~수개월 | 수일~수주 | 수분~수시간 | 수분 |
| 비용 | 높음 (포트+전송) | 중간 | 낮음 (시간+전송) | 낮음 (시간) |
| 암호화 | MACsec (옵션) | 미지원 | IPSec (기본) | TLS (기본) |

## 요약

AWS Direct Connect Location은 온프레미스 네트워크와 AWS 클라우드를 전용 회선으로 연결하는 물리적 접속 지점입니다. 전 세계 100개 이상의 Location에서 Dedicated Connection(1/10/100Gbps)과 Hosted Connection(50Mbps~10Gbps)을 제공하며, BGP 기반 동적 라우팅으로 VPC와 AWS 퍼블릭 서비스에 접근합니다. 한국에서는 KINX, LG U+ IDC 등에서 서울 리전에 대한 Direct Connect 연결을 구성할 수 있습니다. 프로덕션 환경에서는 다중 Location 이중화와 VPN 백업 경로를 반드시 구성하여 고가용성을 확보하는 것이 모범 사례입니다.