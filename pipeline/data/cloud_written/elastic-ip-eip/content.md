## 개요

Elastic IP(EIP)는 AWS에서 제공하는 고정 퍼블릭 IPv4 주소입니다. EC2 인스턴스에 기본으로 할당되는 퍼블릭 IP 주소는 인스턴스를 중지했다가 다시 시작하면 변경됩니다. 반면 EIP는 사용자가 명시적으로 해제하기 전까지 동일한 IP 주소를 유지하므로, 고정 IP가 필요한 워크로드에 필수적입니다.

EIP는 단순히 고정 IP 주소를 넘어서 여러 중요한 기능을 제공합니다. EIP를 다른 인스턴스로 빠르게 리매핑(Remapping)하여 장애 복구에 활용할 수 있으며, ENI(Elastic Network Interface)에 연결하여 네트워크 인터페이스 단위로 관리할 수도 있습니다.

특히 2024년 2월부터 AWS는 모든 퍼블릭 IPv4 주소(EIP 포함)에 대해 시간당 요금을 부과하기 시작했습니다. 이전에는 실행 중인 인스턴스에 연결된 EIP는 무료였지만, 이제는 사용 여부와 관계없이 모든 퍼블릭 IPv4에 비용이 발생합니다. 이러한 변화로 인해 EIP 관리와 비용 최적화의 중요성이 더욱 높아졌습니다.

이 글에서는 EIP의 핵심 개념, 동작 원리, 실전 활용법, 그리고 비용 최적화 전략을 상세히 살펴보겠습니다.

## 핵심 기능

### EIP 할당(Allocation)과 연결(Association)

EIP의 라이프사이클은 두 단계로 나뉩니다.

**할당(Allocation):** AWS의 퍼블릭 IP 풀에서 IP 주소를 예약합니다. 할당된 EIP는 사용자의 AWS 계정에 속하며, 해제(Release)하기 전까지 유지됩니다.

**연결(Association):** 할당된 EIP를 EC2 인스턴스, NAT Gateway, Network Load Balancer 등의 리소스에 연결합니다. 연결을 해제(Disassociation)하더라도 EIP는 여전히 계정에 할당된 상태로 유지됩니다.

### EIP와 ENI의 관계

EIP는 실제로 EC2 인스턴스가 아닌 ENI(Elastic Network Interface)에 연결됩니다. 인스턴스에 EIP를 연결하면 인스턴스의 기본 ENI(Primary ENI)에 EIP가 바인딩됩니다.

ENI에 직접 EIP를 연결할 수도 있으며, 이 경우 해당 ENI를 다른 인스턴스로 이동하면 EIP도 함께 이동합니다.

```json
{
  "NetworkInterface": {
    "NetworkInterfaceId": "eni-0123456789abcdef0",
    "PrivateIpAddress": "10.0.1.100",
    "Association": {
      "AllocationId": "eipalloc-0123456789abcdef0",
      "PublicIp": "52.xx.xx.xx"
    }
  }
}
```

### 리매핑(Remapping)

EIP의 가장 강력한 기능 중 하나는 리매핑입니다. 인스턴스에 장애가 발생하면 EIP를 다른 정상 인스턴스로 신속하게 이동할 수 있습니다. 리매핑은 일반적으로 수초 이내에 완료됩니다.

리매핑 과정:
1. 장애 인스턴스에서 EIP 연결 해제
2. 정상 인스턴스에 EIP 연결
3. DNS 변경 없이 동일 IP로 서비스 재개

### 퍼블릭 IPv4 주소 과금 (2024년 2월 이후)

AWS는 2024년 2월 1일부터 모든 퍼블릭 IPv4 주소에 대해 시간당 $0.005 (리전별 상이)의 요금을 부과합니다. 이 변경 사항은 다음에 적용됩니다.

- EC2 인스턴스에 할당된 퍼블릭 IPv4
- Elastic IP (연결 여부 무관)
- NAT Gateway에 할당된 퍼블릭 IPv4
- ALB/NLB의 퍼블릭 IPv4
- 기타 AWS 서비스의 퍼블릭 IPv4

월간 비용 예시: 1개 EIP x $0.005/시간 x 730시간 = 약 $3.65/월

### BYOIP (Bring Your Own IP)

BYOIP를 통해 자체 보유한 퍼블릭 IPv4 주소 대역을 AWS로 가져와서 EIP로 사용할 수 있습니다. 이는 기존 IP 주소의 평판(reputation)을 유지하거나, 파트너사의 방화벽 허용 목록 변경을 피하기 위해 유용합니다.

### EIP 할당 한도

기본적으로 리전당 5개의 EIP를 할당할 수 있습니다. 더 많은 EIP가 필요한 경우 AWS에 한도 증가를 요청할 수 있습니다.

## 아키텍처/동작 원리

### EIP와 NAT의 관계

EC2 인스턴스에 EIP를 연결하면 AWS는 내부적으로 1:1 NAT(Network Address Translation)를 수행합니다.

```
인바운드 트래픽:
[인터넷] ---> 52.xx.xx.xx (EIP) ---> NAT ---> 10.0.1.100 (Private IP)

아웃바운드 트래픽:
10.0.1.100 (Private IP) ---> NAT ---> 52.xx.xx.xx (EIP) ---> [인터넷]
```

EC2 인스턴스의 운영체제에서는 EIP를 직접 볼 수 없습니다. 인스턴스의 네트워크 인터페이스에는 프라이빗 IP만 설정되어 있으며, AWS의 인프라 레벨에서 NAT가 처리됩니다.

### 퍼블릭 IP vs EIP

| 특성 | 자동 할당 퍼블릭 IP | Elastic IP |
|------|---------------------|------------|
| 영속성 | 인스턴스 중지 시 변경 | 명시적 해제까지 유지 |
| 리매핑 | 불가 | 가능 |
| ENI 연결 | 기본 ENI만 | 모든 ENI |
| 비용 | $0.005/시간 | $0.005/시간 |
| 할당 방식 | 자동 (서브넷 설정) | 수동 할당 |

### EIP 장애 복구 패턴

```
정상 상태:
[클라이언트] --> 52.xx.xx.xx (EIP) --> [인스턴스 A (Active)]
                                      [인스턴스 B (Standby)]

장애 발생 후:
[클라이언트] --> 52.xx.xx.xx (EIP) --> [인스턴스 A (장애)]
                          |            [인스턴스 B (Active)] <-- EIP 리매핑
                          +----------> [인스턴스 B]
```

EIP 리매핑은 DNS TTL에 의존하지 않으므로 매우 빠르게 장애 복구가 가능합니다. 다만 이 패턴은 수동 또는 자동화 스크립트에 의한 조치가 필요합니다.

## 실전 활용

### EIP 할당 및 인스턴스 연결

```bash
# EIP 할당
aws ec2 allocate-address \
  --domain vpc \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=web-server-eip},{Key=Environment,Value=Production}]'

# 결과에서 AllocationId 확인
# {
#   "AllocationId": "eipalloc-0123456789abcdef0",
#   "PublicIp": "52.xx.xx.xx",
#   "Domain": "vpc"
# }

# EIP를 EC2 인스턴스에 연결
aws ec2 associate-address \
  --allocation-id eipalloc-0123456789abcdef0 \
  --instance-id i-0123456789abcdef0
```

### EIP를 ENI에 연결

```bash
# ENI에 보조 프라이빗 IP 추가
aws ec2 assign-private-ip-addresses \
  --network-interface-id eni-0123456789abcdef0 \
  --secondary-private-ip-address-count 1

# EIP를 ENI의 보조 프라이빗 IP에 연결
aws ec2 associate-address \
  --allocation-id eipalloc-0123456789abcdef0 \
  --network-interface-id eni-0123456789abcdef0 \
  --private-ip-address 10.0.1.101
```

### EIP 리매핑 (장애 복구)

```bash
# 장애 인스턴스에서 EIP 연결 해제
aws ec2 disassociate-address \
  --association-id eipassoc-0123456789abcdef0

# 정상 인스턴스에 EIP 연결
aws ec2 associate-address \
  --allocation-id eipalloc-0123456789abcdef0 \
  --instance-id i-standby-instance

# 또는 --allow-reassociation 옵션으로 한 번에 이동
aws ec2 associate-address \
  --allocation-id eipalloc-0123456789abcdef0 \
  --instance-id i-standby-instance \
  --allow-reassociation
```

### EIP 관리 및 모니터링

```bash
# 모든 EIP 목록 조회
aws ec2 describe-addresses \
  --query 'Addresses[*].{PublicIP:PublicIp,AllocationId:AllocationId,InstanceId:InstanceId,AssociationId:AssociationId,Name:Tags[?Key==`Name`]|[0].Value}' \
  --output table

# 연결되지 않은 (유휴) EIP 찾기
aws ec2 describe-addresses \
  --filters 'Name=association-id,Values=' \
  --query 'Addresses[*].{PublicIP:PublicIp,AllocationId:AllocationId,Name:Tags[?Key==`Name`]|[0].Value}' \
  --output table
```

### 유휴 EIP 정리 자동화

```bash
# 연결되지 않은 EIP 식별 및 해제
UNUSED_EIPS=$(aws ec2 describe-addresses \
  --query 'Addresses[?AssociationId==null].AllocationId' \
  --output text)

for EIP_ID in $UNUSED_EIPS; do
  echo "Releasing unused EIP: $EIP_ID"
  aws ec2 release-address --allocation-id $EIP_ID
done
```

### BYOIP 설정

```bash
# IP 주소 대역 가져오기 (사전에 ROA 구성 필요)
aws ec2 provision-byoip-cidr \
  --cidr 198.51.100.0/24 \
  --cidr-authorization-context \
    Message="1|aws|123456789012|198.51.100.0/24|20250101|20261231",Signature="base64-encoded-signature"

# BYOIP 상태 확인
aws ec2 describe-byoip-cidrs \
  --max-results 10 \
  --query 'ByoipCidrs[*].{Cidr:Cidr,State:State}' \
  --output table

# BYOIP 대역에서 EIP 할당
aws ec2 allocate-address \
  --domain vpc \
  --address 198.51.100.10 \
  --tag-specifications 'ResourceType=elastic-ip,Tags=[{Key=Name,Value=byoip-eip}]'
```

### 퍼블릭 IPv4 사용량 확인 (IPAM)

```bash
# VPC IPAM을 통한 퍼블릭 IPv4 사용량 확인
aws ec2 get-ipam-discovered-public-addresses \
  --ipam-resource-discovery-id ipam-res-disco-0123456789abcdef0 \
  --address-region ap-northeast-2 \
  --query 'IpamDiscoveredPublicAddresses[*].{IP:Address,Type:AddressType,Service:Service,Resource:ResourceId}' \
  --output table
```

## 모범 사례/보안

### 비용 최적화

1. **사용하지 않는 EIP를 즉시 해제합니다.** 연결되지 않은 EIP에도 시간당 요금이 부과됩니다. 정기적으로 유휴 EIP를 식별하고 해제합니다.

2. **퍼블릭 IP 의존성을 줄입니다.** 가능한 경우 프라이빗 통신으로 전환합니다.
   - VPC Endpoint를 사용하여 AWS 서비스에 프라이빗하게 접근합니다.
   - ALB 대신 내부 ALB + PrivateLink 조합을 고려합니다.
   - IPv6를 활용하여 퍼블릭 IPv4 의존성을 줄입니다.

3. **EC2 Instance Connect Endpoint를 활용합니다.** SSH 접근을 위해 인스턴스에 퍼블릭 IP를 할당하는 대신 EC2 Instance Connect Endpoint를 사용하면 프라이빗 서브넷의 인스턴스에 퍼블릭 IP 없이 접근할 수 있습니다.

4. **AWS IPAM(IP Address Manager)을 사용합니다.** IPAM의 Public IP Insights 기능으로 조직 전체의 퍼블릭 IPv4 사용량을 추적하고 최적화 기회를 식별합니다.

### 보안 모범 사례

1. **EIP가 연결된 인스턴스의 보안 그룹을 엄격하게 설정합니다.** EIP가 있으면 인터넷에서 직접 접근이 가능하므로 필요한 포트만 열어야 합니다.

2. **EIP 변경에 대한 CloudTrail 알림을 설정합니다.** 승인되지 않은 EIP 할당, 연결, 해제 등의 활동을 감지합니다.

3. **IAM 정책으로 EIP 관련 권한을 제한합니다.** EIP 할당과 해제는 비용과 보안에 직접적인 영향을 미치므로 권한을 최소한으로 제한합니다.

4. **태깅 정책을 강제합니다.** 모든 EIP에 소유자, 용도, 환경 등의 태그를 필수로 부착하여 관리 가시성을 확보합니다.

### 가용성 고려사항

- EIP 리매핑은 수동 조치가 필요하므로, 자동 장애 복구가 필요한 경우 ALB/NLB 또는 Auto Scaling을 사용하는 것이 더 적합합니다.
- EIP는 단일 AZ에 연결되므로, 멀티 AZ 가용성이 필요한 경우 각 AZ에 별도의 EIP와 인스턴스를 구성해야 합니다.

## 관련 서비스 비교

| 특성 | Elastic IP | Auto-assigned Public IP | Global Accelerator (Anycast IP) | NLB Static IP |
|------|-----------|------------------------|-------------------------------|---------------|
| IP 고정 여부 | 고정 | 변경 가능 | 고정 | 고정 |
| 범위 | 리전 (단일 AZ) | 인스턴스 수명 | 글로벌 | AZ별 |
| 리매핑 | 수동 가능 | 불가 | 자동 | 불가 |
| 장애 복구 | 수동 리매핑 | 해당 없음 | 자동 페일오버 | 자동 (AZ 내) |
| 비용 | $0.005/시간 | $0.005/시간 | 고정 + DT 프리미엄 | 포함 |
| 적합한 용도 | 단일 인스턴스 | 임시 워크로드 | 글로벌 가속 | L4 부하 분산 |

### EIP 대안

- **로드 밸런서(ALB/NLB)**: 고가용성이 필요한 웹 서비스에는 EIP 대신 로드 밸런서를 사용합니다.
- **Global Accelerator**: 글로벌 고정 IP가 필요한 경우 Global Accelerator의 Anycast IP를 사용합니다.
- **Route 53**: DNS 기반의 장애 복구가 가능한 경우 EIP 리매핑 대신 Route 53의 Health Check + Failover 라우팅을 사용합니다.

## 요약

Elastic IP는 AWS에서 고정 퍼블릭 IPv4 주소를 제공하는 기본적이지만 중요한 네트워킹 리소스입니다. 주요 내용을 정리하면 다음과 같습니다.

- EIP는 할당(Allocation)과 연결(Association)의 두 단계 라이프사이클을 가집니다.
- EIP는 실제로 ENI에 연결되며, 인스턴스 간 빠른 리매핑이 가능합니다.
- 2024년 2월부터 모든 퍼블릭 IPv4(EIP 포함)에 시간당 $0.005의 요금이 부과됩니다.
- BYOIP를 통해 자체 IP 대역을 AWS에서 사용할 수 있습니다.
- 유휴 EIP를 정기적으로 정리하여 비용을 최적화해야 합니다.
- 고가용성이 필요한 경우 EIP 리매핑보다 로드 밸런서나 Auto Scaling이 더 적합합니다.
- VPC Endpoint, IPv6, EC2 Instance Connect Endpoint 등을 활용하여 퍼블릭 IPv4 의존성을 줄이는 것이 비용과 보안 모두에 유리합니다.