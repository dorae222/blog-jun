## 개요

AWS PrivateLink는 VPC, AWS 서비스, 그리고 온프레미스 네트워크 간에 프라이빗 연결을 제공하는 기술입니다. PrivateLink를 사용하면 트래픽이 퍼블릭 인터넷을 경유하지 않고 AWS 네트워크 내에서만 이동하므로, 보안이 강화되고 데이터 노출 위험이 줄어듭니다.

일반적으로 VPC 내의 리소스가 AWS 서비스(예: S3, DynamoDB, CloudWatch)에 접근하려면 인터넷 게이트웨이나 NAT 게이트웨이를 통해 퍼블릭 인터넷으로 트래픽을 보내야 합니다. 이는 보안 측면에서 바람직하지 않으며, NAT 게이트웨이를 사용할 경우 추가 비용도 발생합니다.

PrivateLink는 이 문제를 해결합니다. VPC 내에 ENI(Elastic Network Interface)를 생성하여 AWS 서비스나 다른 VPC의 서비스에 프라이빗하게 접근할 수 있게 합니다. 이 글에서는 PrivateLink의 핵심 구성 요소인 VPC Endpoint, Endpoint Service, 그리고 이들의 동작 원리를 상세히 살펴보겠습니다.

## 핵심 기능

### VPC Endpoint 유형

PrivateLink는 두 가지 유형의 VPC Endpoint를 제공합니다.

**1. Interface Endpoint**

Interface Endpoint는 서브넷 내에 ENI(Elastic Network Interface)를 생성하여 프라이빗 IP 주소를 통해 서비스에 접근할 수 있게 합니다. 이 ENI는 지원되는 AWS 서비스, 다른 AWS 계정의 Endpoint Service, 또는 AWS Marketplace 파트너 서비스로의 트래픽 진입점 역할을 합니다.

Interface Endpoint의 특징은 다음과 같습니다.
- 서브넷당 하나의 ENI가 생성됩니다.
- 보안 그룹을 연결하여 접근을 제어할 수 있습니다.
- 프라이빗 DNS를 활성화하면 기존 서비스 DNS 이름이 자동으로 프라이빗 IP로 해석됩니다.
- 시간당 요금 + 데이터 처리 요금이 부과됩니다.

**2. Gateway Endpoint**

Gateway Endpoint는 라우팅 테이블에 항목을 추가하여 트래픽을 AWS 서비스로 직접 라우팅합니다. 현재 S3와 DynamoDB만 지원합니다.

Gateway Endpoint의 특징은 다음과 같습니다.
- ENI를 생성하지 않으며, 라우팅 테이블 수정 방식으로 동작합니다.
- 보안 그룹 대신 VPC Endpoint 정책으로 접근을 제어합니다.
- 추가 비용이 없습니다 (무료).
- 동일 리전의 서비스에만 사용할 수 있습니다.

### Gateway Load Balancer Endpoint

Gateway Load Balancer(GWLB) Endpoint는 세 번째 유형의 VPC Endpoint입니다. 네트워크 트래픽을 검사하기 위한 서드파티 가상 어플라이언스(방화벽, IDS/IPS 등)로 트래픽을 전달하는 데 사용됩니다.

### Endpoint Service (서비스 제공자 측)

Endpoint Service는 자신의 VPC에서 호스팅하는 서비스를 다른 VPC에 PrivateLink를 통해 노출하기 위한 구성 요소입니다. Network Load Balancer(NLB) 또는 Gateway Load Balancer(GWLB) 뒤에 있는 서비스를 Endpoint Service로 등록할 수 있습니다.

```json
{
  "ServiceConfiguration": {
    "ServiceName": "com.amazonaws.vpce.ap-northeast-2.vpce-svc-0123456789abcdef",
    "ServiceType": "Interface",
    "NetworkLoadBalancerArns": [
      "arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/net/my-nlb/abcdef"
    ],
    "AcceptanceRequired": true,
    "PrivateDnsName": "api.myservice.com"
  }
}
```

### Private DNS

Interface Endpoint에서 Private DNS를 활성화하면, 서비스의 기본 퍼블릭 DNS 이름(예: `ec2.ap-northeast-2.amazonaws.com`)이 VPC 내에서 프라이빗 IP 주소로 해석됩니다. 이를 통해 애플리케이션 코드를 변경하지 않고도 PrivateLink를 사용할 수 있습니다.

Private DNS가 동작하려면 VPC의 `enableDnsSupport`와 `enableDnsHostnames` 설정이 모두 `true`여야 합니다.

## 아키텍처/동작 원리

### Interface Endpoint 동작 원리

```
VPC (소비자)
+----------------------------------+
| Subnet A (AZ-a)                  |
|   [EC2] --> [ENI: 10.0.1.100]    |
|              (vpce-xxxx)         |
|                  |               |
| Subnet B (AZ-c)                  |
|   [EC2] --> [ENI: 10.0.2.100]    |
|              (vpce-xxxx)         |
+-------------|--------------------+
              |
         AWS PrivateLink
              |
+-------------|--------------------+
| AWS 서비스 (예: STS, SSM, EC2)   |
+----------------------------------+
```

Interface Endpoint를 생성하면 선택한 서브넷에 ENI가 생성됩니다. 이 ENI에는 서브넷의 CIDR 범위에서 프라이빗 IP 주소가 할당됩니다. VPC 내의 리소스는 이 ENI의 IP 주소를 통해 서비스에 접근합니다.

Private DNS가 활성화된 경우, Route 53 Resolver가 서비스의 퍼블릭 DNS 쿼리를 가로채서 ENI의 프라이빗 IP로 해석합니다.

### Gateway Endpoint 동작 원리

```
VPC
+----------------------------------+
| Route Table:                     |
|   10.0.0.0/16 -> local           |
|   pl-xxxx (S3) -> vpce-xxxx      |
|                                  |
| Subnet A                         |
|   [EC2] ---> (라우팅 테이블 경유) |
|          ---> Gateway Endpoint   |
|          ---> S3                 |
+----------------------------------+
```

Gateway Endpoint는 라우팅 테이블에 Prefix List를 대상으로 하는 경로를 추가합니다. S3나 DynamoDB로의 트래픽이 이 경로를 통해 AWS 네트워크 내에서 직접 전달됩니다.

### 서비스 간 PrivateLink 연결 (서비스 제공자-소비자 모델)

```
서비스 소비자 VPC                    서비스 제공자 VPC
+-------------------+               +-------------------+
| [EC2]             |               | [NLB]             |
|   |               |               |   |               |
| [ENI] <-- PrivateLink --> [Endpoint Service]           |
| (Interface        |               | (NLB 기반)        |
|  Endpoint)        |               |   |               |
+-------------------+               | [EC2/ECS/Lambda]  |
                                    +-------------------+
```

서비스 제공자는 NLB 뒤에 서비스를 배치하고 Endpoint Service를 생성합니다. 서비스 소비자는 Endpoint Service의 이름을 사용하여 Interface Endpoint를 생성합니다. 이후 소비자의 VPC에서 ENI를 통해 제공자의 서비스에 프라이빗하게 접근할 수 있습니다.

이 모델의 핵심 장점은 두 VPC의 CIDR이 겹치더라도 통신이 가능하다는 것입니다. PrivateLink는 일방향 연결이므로 소비자에서 제공자 방향으로만 트래픽이 흐릅니다.

## 실전 활용

### S3 Gateway Endpoint 생성

```bash
# VPC ID 확인
aws ec2 describe-vpcs \
  --query 'Vpcs[*].{VpcId:VpcId,CidrBlock:CidrBlock,Name:Tags[?Key==`Name`]|[0].Value}' \
  --output table

# S3 Gateway Endpoint 생성
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --service-name com.amazonaws.ap-northeast-2.s3 \
  --vpc-endpoint-type Gateway \
  --route-table-ids rtb-0123456789abcdef0 rtb-abcdef0123456789 \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=s3-gateway-endpoint}]'
```

### Interface Endpoint 생성 (SSM 예시)

Systems Manager Session Manager를 프라이빗 서브넷에서 사용하려면 여러 Interface Endpoint가 필요합니다.

```bash
# SSM Interface Endpoint 생성
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --service-name com.amazonaws.ap-northeast-2.ssm \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-aaaa1111 subnet-bbbb2222 \
  --security-group-ids sg-0123456789abcdef0 \
  --private-dns-enabled \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=ssm-endpoint}]'

# SSM Messages Interface Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --service-name com.amazonaws.ap-northeast-2.ssmmessages \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-aaaa1111 subnet-bbbb2222 \
  --security-group-ids sg-0123456789abcdef0 \
  --private-dns-enabled \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=ssmmessages-endpoint}]'

# EC2 Messages Interface Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --service-name com.amazonaws.ap-northeast-2.ec2messages \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-aaaa1111 subnet-bbbb2222 \
  --security-group-ids sg-0123456789abcdef0 \
  --private-dns-enabled \
  --tag-specifications 'ResourceType=vpc-endpoint,Tags=[{Key=Name,Value=ec2messages-endpoint}]'
```

### Endpoint Service 생성 (서비스 제공자)

자체 서비스를 다른 VPC에 노출하는 Endpoint Service를 생성합니다.

```bash
# Endpoint Service 생성 (NLB 기반)
aws ec2 create-vpc-endpoint-service-configuration \
  --network-load-balancer-arns arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:loadbalancer/net/my-service-nlb/abcdef \
  --acceptance-required \
  --tag-specifications 'ResourceType=vpc-endpoint-service,Tags=[{Key=Name,Value=my-api-service}]'

# 특정 AWS 계정에 연결 권한 부여
aws ec2 modify-vpc-endpoint-service-permissions \
  --service-id vpce-svc-0123456789abcdef0 \
  --add-allowed-principals arn:aws:iam::987654321098:root

# 연결 요청 수락
aws ec2 accept-vpc-endpoint-connections \
  --service-id vpce-svc-0123456789abcdef0 \
  --vpc-endpoint-ids vpce-0123456789abcdef0
```

### VPC Endpoint 정책 구성

VPC Endpoint 정책을 사용하여 접근할 수 있는 리소스를 세밀하게 제어합니다.

```bash
# S3 Gateway Endpoint에 특정 버킷만 허용하는 정책 적용
aws ec2 modify-vpc-endpoint \
  --vpc-endpoint-id vpce-0123456789abcdef0 \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Sid": "AllowSpecificBucket",
        "Effect": "Allow",
        "Principal": "*",
        "Action": [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::my-approved-bucket",
          "arn:aws:s3:::my-approved-bucket/*"
        ]
      }
    ]
  }'
```

### VPC Endpoint 상태 확인

```bash
# 모든 VPC Endpoint 상태 확인
aws ec2 describe-vpc-endpoints \
  --query 'VpcEndpoints[*].{Id:VpcEndpointId,Service:ServiceName,Type:VpcEndpointType,State:State,DNS:DnsEntries[0].DnsName}' \
  --output table

# 특정 Endpoint의 상세 정보
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids vpce-0123456789abcdef0 \
  --query 'VpcEndpoints[0].{Id:VpcEndpointId,Service:ServiceName,State:State,SubnetIds:SubnetIds,SecurityGroups:Groups[*].GroupId,PrivateDns:PrivateDnsEnabled}' \
  --output json

# 사용 가능한 서비스 목록 확인
aws ec2 describe-vpc-endpoint-services \
  --query 'ServiceNames' \
  --output json \
  --region ap-northeast-2
```

## 모범 사례/보안

### 보안 모범 사례

1. **VPC Endpoint 정책을 반드시 구성합니다.** 기본 정책은 모든 접근을 허용하므로, 최소 권한 원칙에 따라 필요한 리소스와 작업만 허용하도록 정책을 커스터마이즈합니다.

2. **Interface Endpoint에 보안 그룹을 적용합니다.** Interface Endpoint의 ENI에 연결된 보안 그룹으로 어떤 소스에서 접근할 수 있는지 제어합니다. 일반적으로 VPC CIDR에서 HTTPS(443) 포트만 허용합니다.

3. **Private DNS를 활성화합니다.** Private DNS를 활성화하면 애플리케이션 코드 변경 없이 트래픽이 자동으로 PrivateLink를 통해 라우팅됩니다.

4. **S3 버킷 정책에서 VPC Endpoint 조건을 사용합니다.** S3 버킷에 대한 접근을 특정 VPC Endpoint를 통해서만 허용하도록 설정합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyNonVPCEndpointAccess",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::my-secure-bucket",
        "arn:aws:s3:::my-secure-bucket/*"
      ],
      "Condition": {
        "StringNotEquals": {
          "aws:sourceVpce": "vpce-0123456789abcdef0"
        }
      }
    }
  ]
}
```

5. **Endpoint Service에서 수락 필수(Acceptance Required) 옵션을 활성화합니다.** 이를 통해 승인된 소비자만 서비스에 연결할 수 있습니다.

### 가용성 모범 사례

1. **여러 가용 영역에 Interface Endpoint를 생성합니다.** 하나의 AZ에만 ENI를 생성하면 해당 AZ 장애 시 서비스 접근이 불가능합니다.

2. **S3는 Gateway Endpoint를 우선 사용합니다.** Gateway Endpoint는 무료이고 라우팅 테이블 기반으로 동작하므로 가용성이 높습니다. 온프레미스에서의 접근이 필요한 경우에만 Interface Endpoint를 추가로 고려합니다.

### 비용 최적화

- Interface Endpoint는 시간당 약 $0.01 + GB당 $0.01의 데이터 처리 비용이 발생합니다. 여러 서비스에 대한 Endpoint를 생성하면 비용이 누적되므로 반드시 필요한 서비스만 Endpoint를 생성합니다.
- Gateway Endpoint(S3, DynamoDB)는 무료이므로 적극 활용합니다.
- NAT Gateway를 통한 AWS 서비스 접근 비용과 Interface Endpoint 비용을 비교하여 최적의 방식을 선택합니다.

## 관련 서비스 비교

| 특성 | PrivateLink (Interface) | Gateway Endpoint | VPC Peering | Transit Gateway |
|------|------------------------|-------------------|-------------|------------------|
| 통신 방향 | 단방향 | 단방향 | 양방향 | 양방향 |
| CIDR 겹침 | 허용 | 해당 없음 | 불가 | 불가 |
| 대상 서비스 | 대부분 AWS 서비스 | S3, DynamoDB만 | VPC 간 | VPC 간 |
| 비용 | 시간+데이터 | 무료 | 데이터 전송 | 시간+데이터 |
| 온프레미스 접근 | Direct Connect/VPN 가능 | 불가 | 불가 | 가능 |
| 확장성 | 서비스 단위 | 서비스 단위 | VPC 쌍 단위 | 허브-스포크 |
| 보안 그룹 | 지원 | 미지원 | 지원 | 미지원 |

### PrivateLink vs VPC Peering

VPC Peering은 두 VPC 간 양방향 네트워크 연결을 제공하지만, CIDR이 겹치면 사용할 수 없고 전이적 라우팅(Transitive Routing)을 지원하지 않습니다. PrivateLink는 단방향이지만 CIDR 겹침이 허용되고, 서비스 제공자가 소비자에게 노출하는 포트와 서비스를 세밀하게 제어할 수 있습니다.

서비스 지향적인 연결이 필요한 경우 PrivateLink를, 전체 네트워크 수준의 연결이 필요한 경우 VPC Peering을 선택합니다.

## 요약

AWS PrivateLink는 AWS 네트워크 내에서 프라이빗하게 서비스에 접근할 수 있게 하는 핵심 네트워킹 기술입니다. 주요 내용을 정리하면 다음과 같습니다.

- Interface Endpoint는 ENI 기반으로 동작하며 대부분의 AWS 서비스를 지원합니다.
- Gateway Endpoint는 라우팅 테이블 기반으로 동작하며 S3와 DynamoDB를 무료로 지원합니다.
- Endpoint Service를 통해 자체 서비스를 다른 VPC에 프라이빗하게 노출할 수 있습니다.
- VPC Endpoint 정책과 보안 그룹으로 세밀한 접근 제어가 가능합니다.
- Private DNS를 활성화하면 애플리케이션 코드 변경 없이 PrivateLink를 사용할 수 있습니다.
- CIDR 겹침이 허용되므로 멀티 계정, 멀티 VPC 환경에서 유연하게 사용할 수 있습니다.
- 보안과 비용 측면에서 NAT Gateway를 통한 접근보다 유리한 경우가 많습니다.