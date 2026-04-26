<!-- infographic-hero -->
![Amazon EC2 Enhanced Networking - 네트워크 성능 향상 기능 완벽 가이드 핵심 요약](figures/infographic.svg)

*Figure: Amazon EC2 Enhanced Networking - 네트워크 성능 향상 기능 완벽 가이드 한 장 요약 인포그래픽*

## 개요

Amazon EC2 Enhanced Networking은 단일 루트 I/O 가상화(SR-IOV) 기술을 활용하여 EC2 인스턴스의 네트워크 성능을 획기적으로 향상시키는 기능입니다. 일반적인 가상화 환경에서 네트워크 트래픽은 하이퍼바이저를 거쳐야 하므로 지연(Latency)이 발생하고 CPU 오버헤드가 증가합니다. Enhanced Networking은 이 하이퍼바이저 병목을 제거하여 더 높은 대역폭, 더 낮은 지연, 더 적은 지터(Jitter)를 제공합니다.

고성능 컴퓨팅(HPC), 실시간 데이터 처리, 대규모 분산 데이터베이스, 금융 거래 시스템 등 네트워크 성능이 중요한 워크로드에서 Enhanced Networking은 선택이 아닌 필수입니다.

본 글에서는 Enhanced Networking의 기술적 원리, 두 가지 구현 방식의 차이, 활성화 방법, 그리고 최적의 네트워크 성능을 위한 아키텍처 설계까지 상세히 다루겠습니다.

## 핵심 기능

### SR-IOV (Single Root I/O Virtualization)

Enhanced Networking의 핵심은 SR-IOV 기술입니다. SR-IOV는 하나의 물리적 네트워크 어댑터를 여러 개의 가상 함수(Virtual Function, VF)로 분할하여, 각 VM이 하이퍼바이저를 거치지 않고 직접 네트워크 어댑터에 접근할 수 있게 합니다.

| 항목 | 일반 네트워킹 | Enhanced Networking |
|------|-------------|--------------------|
| I/O 경로 | VM -> 하이퍼바이저 -> 물리 NIC | VM -> VF -> 물리 NIC (직접) |
| CPU 오버헤드 | 높음 | 낮음 |
| 지연(Latency) | 높음 | 매우 낮음 |
| 대역폭 | 제한적 | 최대 100 Gbps |
| 추가 비용 | - | 무료 |

### ENA (Elastic Network Adapter)

ENA는 AWS가 자체 개발한 고성능 네트워크 어댑터로, 최대 100 Gbps의 네트워크 대역폭을 지원합니다. 현재 대부분의 최신 인스턴스 유형에서 기본적으로 ENA를 사용합니다.

```bash
# 인스턴스의 ENA 지원 여부 확인
aws ec2 describe-instances \
  --instance-ids i-0abc123def456789 \
  --query 'Reservations[0].Instances[0].EnaSupport'

# AMI의 ENA 지원 여부 확인
aws ec2 describe-images \
  --image-ids ami-0abc123def456789 \
  --query 'Images[0].EnaSupport'
```

**ENA 지원 인스턴스 유형 확인:**

```bash
# ENA를 지원하는 인스턴스 유형 조회
aws ec2 describe-instance-types \
  --filters "Name=network-info.ena-support,Values=required" \
  --query 'InstanceTypes[*].{Type: InstanceType, MaxBandwidth: NetworkInfo.NetworkCards[0].PeakBandwidthInGbps}' \
  --output table
```

### Intel 82599 VF (ixgbevf)

구세대 Enhanced Networking 구현으로, Intel 82599 Virtual Function 인터페이스를 사용합니다. 최대 10 Gbps 대역폭을 지원하며, C3, C4, R3 등 구형 인스턴스 유형에서 사용됩니다.

```bash
# 인스턴스의 sriov-net-support 속성 확인 (Intel 82599 VF)
aws ec2 describe-instance-attribute \
  --instance-id i-0abc123def456789 \
  --attribute sriovNetSupport
```

### ENA Express

ENA Express는 AWS Scalable Reliable Datagram(SRD) 프로토콜을 활용하여 단일 흐름(single-flow)에서도 최대 25 Gbps 대역폭과 마이크로초 수준의 꼬리 지연(tail latency)을 제공하는 차세대 기능입니다.

```bash
# ENA Express 활성화
aws ec2 modify-instance-attribute \
  --instance-id i-0abc123def456789 \
  --ena-srd-specification '{"EnaSrdEnabled": true, "EnaSrdUdpSpecification": {"EnaSrdUdpEnabled": true}}'

# ENA Express 상태 확인
aws ec2 describe-instances \
  --instance-ids i-0abc123def456789 \
  --query 'Reservations[0].Instances[0].NetworkInterfaces[0].Attachment.EnaSrdSpecification'
```

### 네트워크 성능 지표

```bash
# 인스턴스 유형별 네트워크 성능 상세 조회
aws ec2 describe-instance-types \
  --instance-types c5n.18xlarge c6i.metal m5.xlarge \
  --query 'InstanceTypes[*].{
    Type: InstanceType,
    MaxInterfaces: NetworkInfo.MaximumNetworkInterfaces,
    IPv4PerInterface: NetworkInfo.Ipv4AddressesPerInterface,
    MaxBandwidth: NetworkInfo.NetworkCards[0].PeakBandwidthInGbps,
    EnaSupport: NetworkInfo.EnaSupport,
    EfaSupported: NetworkInfo.EfaSupported
  }' \
  --output table
```

## 아키텍처/동작 원리

### 네트워크 I/O 경로 비교

**일반 네트워킹:**
```
[애플리케이션] -> [Guest OS 커널] -> [vNIC 에뮬레이션]
     -> [하이퍼바이저 (Xen/Nitro)] -> [물리 NIC]
```

**Enhanced Networking (SR-IOV):**
```
[애플리케이션] -> [Guest OS 커널] -> [ENA/VF 드라이버]
     -> [물리 NIC의 VF] (하이퍼바이저 바이패스)
```

### Nitro 시스템과의 관계

AWS Nitro 시스템은 Enhanced Networking을 한 단계 더 발전시킨 아키텍처입니다. Nitro 카드가 네트워크, 스토리지, 보안 기능을 전담 처리하므로, 호스트의 모든 CPU 리소스를 인스턴스에 할당할 수 있습니다.

- **Nitro 카드 (네트워크)**: VPC 네트워킹, EBS 연결, 인스턴스 스토리지를 하드웨어 수준에서 처리
- **Nitro 보안 칩**: 하드웨어 기반 보안으로 하이퍼바이저 접근 차단
- **Nitro 하이퍼바이저**: 경량화된 하이퍼바이저로 최소한의 오버헤드

### Placement Group과 네트워크 최적화

Enhanced Networking의 성능을 최대화하려면 Placement Group과 함께 사용하는 것이 중요합니다.

```bash
# Cluster Placement Group 생성 (최저 지연)
aws ec2 create-placement-group \
  --group-name "hpc-cluster" \
  --strategy cluster \
  --tag-specifications 'ResourceType=placement-group,Tags=[{Key=Purpose,Value=HPC}]'

# Placement Group에 인스턴스 배치
aws ec2 run-instances \
  --image-id ami-0abc123def456789 \
  --instance-type c5n.18xlarge \
  --placement GroupName=hpc-cluster \
  --network-interfaces '[{
    "DeviceIndex": 0,
    "SubnetId": "subnet-abc123",
    "Groups": ["sg-abc123"],
    "InterfaceType": "efa"
  }]' \
  --count 4
```

| Placement Strategy | 지연 | 가용성 | 적합한 워크로드 |
|-------------------|------|--------|---------------|
| Cluster | 최저 | 단일 AZ | HPC, 실시간 처리 |
| Spread | 보통 | 최고 | 고가용성 필요 |
| Partition | 보통 | 높음 | HDFS, Cassandra |

### EFA (Elastic Fabric Adapter)

EFA는 Enhanced Networking을 넘어서는 HPC 전용 네트워크 인터페이스입니다. OS 바이패스 기능을 제공하여 인스턴스 간 통신에서 커널을 우회하므로, MPI(Message Passing Interface) 워크로드에서 극도로 낮은 지연을 달성합니다.

```bash
# EFA 지원 인스턴스 유형 조회
aws ec2 describe-instance-types \
  --filters "Name=network-info.efa-supported,Values=true" \
  --query 'InstanceTypes[*].InstanceType' \
  --output text

# EFA 네트워크 인터페이스 생성
aws ec2 create-network-interface \
  --subnet-id subnet-abc123 \
  --groups sg-abc123 \
  --interface-type efa \
  --description "EFA interface for HPC"
```

## 실전 활용

### 사례 1: Enhanced Networking 활성화 확인 및 설정

```bash
# 현재 실행 중인 인스턴스의 Enhanced Networking 상태 전체 확인
aws ec2 describe-instances \
  --instance-ids i-0abc123def456789 \
  --query 'Reservations[0].Instances[0].{
    InstanceType: InstanceType,
    EnaSupport: EnaSupport,
    SriovNetSupport: SriovNetSupport,
    NetworkInterfaces: NetworkInterfaces[*].{
      InterfaceId: NetworkInterfaceId,
      InterfaceType: InterfaceType,
      Attachment: Attachment.{Status: Status, DeviceIndex: DeviceIndex}
    }
  }'
```

**ENA가 아직 활성화되지 않은 인스턴스에서 ENA 활성화:**

```bash
# 1. 인스턴스 중지
aws ec2 stop-instances --instance-ids i-0abc123def456789
aws ec2 wait instance-stopped --instance-ids i-0abc123def456789

# 2. ENA 지원 활성화
aws ec2 modify-instance-attribute \
  --instance-id i-0abc123def456789 \
  --ena-support

# 3. 인스턴스 시작
aws ec2 start-instances --instance-ids i-0abc123def456789
aws ec2 wait instance-running --instance-ids i-0abc123def456789

# 4. ENA 활성화 확인
aws ec2 describe-instances \
  --instance-ids i-0abc123def456789 \
  --query 'Reservations[0].Instances[0].EnaSupport'
```

### 사례 2: 고성능 네트워크를 위한 인스턴스 구성

```bash
# c5n.18xlarge: 100 Gbps 네트워크 대역폭
aws ec2 run-instances \
  --image-id ami-0abc123def456789 \
  --instance-type c5n.18xlarge \
  --placement GroupName=hpc-cluster \
  --network-interfaces '[{
    "DeviceIndex": 0,
    "SubnetId": "subnet-abc123",
    "Groups": ["sg-abc123"],
    "AssociatePublicIpAddress": false
  }]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=hpc-node-1}]' \
  --count 1
```

### 사례 3: 네트워크 성능 측정

인스턴스 간 네트워크 성능을 측정하려면 iperf3를 활용합니다.

```bash
# 서버 측 (인스턴스 A에서 실행)
# iperf3 -s -p 5201

# 클라이언트 측 (인스턴스 B에서 실행)
# 단일 스트림 대역폭 테스트
# iperf3 -c <server-ip> -p 5201 -t 30

# 다중 스트림 대역폭 테스트 (Enhanced Networking 효과 극대화)
# iperf3 -c <server-ip> -p 5201 -t 30 -P 16

# UDP 지연 테스트
# iperf3 -c <server-ip> -p 5201 -u -b 1G -t 30
```

### 사례 4: Jumbo Frame 설정

Enhanced Networking은 Jumbo Frame(MTU 9001)을 지원하여 대용량 데이터 전송 효율을 높입니다.

```bash
# VPC 내 인스턴스 간 MTU 확인
# ip link show eth0

# MTU 설정 (인스턴스 내부에서)
# sudo ip link set dev eth0 mtu 9001

# Path MTU Discovery를 활용한 최적 MTU 확인
# ping -M do -s 8972 <target-ip>
```

주의: Jumbo Frame은 같은 VPC 내 인스턴스 간에만 적용됩니다. VPN, 인터넷 게이트웨이, VPC 피어링 등을 통한 트래픽은 MTU 1500으로 제한됩니다.

### 사례 5: 네트워크 대역폭 모니터링

```bash
# CloudWatch에서 네트워크 메트릭 조회
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name NetworkIn \
  --dimensions Name=InstanceId,Value=i-0abc123def456789 \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 300 \
  --statistics Average Maximum \
  --unit Bytes

# ENA 드라이버 레벨 메트릭 확인 (인스턴스 내부에서)
# ethtool -S eth0 | grep -E 'tx_timeout|suspend|rx_drops'
```

## 모범 사례/보안

### 1. 인스턴스 유형 선택 가이드

- **최대 대역폭이 필요한 경우**: c5n.18xlarge (100 Gbps), c6in.32xlarge (200 Gbps) 등 "n" 접미사가 붙은 네트워크 최적화 인스턴스를 선택합니다.
- **HPC 워크로드**: EFA를 지원하는 인스턴스(c5n, c6i, p4d, hpc6a 등)를 사용합니다.
- **범용 워크로드**: 최신 세대 인스턴스(5세대 이상)는 기본적으로 ENA를 지원하므로 별도 설정이 필요 없습니다.

### 2. 보안 그룹 최적화

```bash
# 필요한 포트만 허용하는 보안 그룹 설정
aws ec2 create-security-group \
  --group-name "enhanced-net-sg" \
  --description "Security group for enhanced networking instances" \
  --vpc-id vpc-abc123

# 클러스터 내부 통신 허용
aws ec2 authorize-security-group-ingress \
  --group-id sg-newgroup123 \
  --protocol -1 \
  --source-group sg-newgroup123
```

### 3. 드라이버 관리

- ENA 드라이버를 최신 버전으로 유지합니다. AWS에서 제공하는 최적화된 AMI(Amazon Linux 2, Ubuntu Pro 등)를 사용하면 최신 드라이버가 기본 포함됩니다.
- 커스텀 AMI를 사용하는 경우 ENA 드라이버를 수동으로 업데이트해야 합니다.

### 4. 네트워크 흐름 로그 활용

```bash
# VPC Flow Logs 활성화
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids vpc-abc123 \
  --traffic-type ALL \
  --log-destination-type s3 \
  --log-destination "arn:aws:s3:::my-flow-logs-bucket/vpc-logs/"
```

### 5. 비용 고려사항

Enhanced Networking 자체는 추가 비용이 없습니다. 다만, 높은 네트워크 대역폭을 활용하려면 더 큰 인스턴스 유형이 필요할 수 있으므로, 워크로드의 실제 네트워크 요구량을 측정한 후 적절한 인스턴스를 선택하는 것이 중요합니다.

## 관련 서비스 비교

| 항목 | Enhanced Networking (ENA) | EFA | Global Accelerator | Transit Gateway |
|------|--------------------------|-----|--------------------|-----------------|
| 범위 | 인스턴스 수준 NIC | 인스턴스 수준 NIC | 글로벌 네트워크 | VPC 간 연결 |
| 주요 목적 | 고성능 인스턴스 네트워킹 | HPC 인스턴스 간 통신 | 글로벌 가속 | 네트워크 허브 |
| 최대 대역폭 | 200 Gbps | 400 Gbps | N/A | 50 Gbps |
| 지연 최적화 | VPC 내부 | VPC 내부 (OS 바이패스) | 글로벌 | VPC 간 |
| 프로토콜 | TCP/UDP | Libfabric (MPI 등) | TCP/UDP | 모든 프로토콜 |
| 추가 비용 | 무료 | 무료 | 유료 | 유료 |
| 적합한 워크로드 | 범용 고성능 | HPC, ML 분산학습 | 글로벌 서비스 | 멀티 VPC |

## 요약

Amazon EC2 Enhanced Networking은 SR-IOV 기술을 활용하여 하이퍼바이저 오버헤드를 제거하고 네트워크 성능을 극대화하는 기능입니다. 핵심 내용을 정리하면 다음과 같습니다.

- **ENA (Elastic Network Adapter)**: AWS 자체 개발 어댑터로 최대 200 Gbps 대역폭을 지원하며, 최신 인스턴스에서 기본 활성화됩니다.
- **ENA Express**: SRD 프로토콜 기반으로 단일 흐름에서도 25 Gbps 대역폭과 마이크로초 수준 지연을 제공합니다.
- **무료**: Enhanced Networking 자체는 추가 비용 없이 사용 가능합니다.
- **Placement Group**: Cluster Placement Group과 함께 사용하면 네트워크 성능을 극대화할 수 있습니다.
- **EFA**: HPC 워크로드에서는 OS 바이패스를 지원하는 EFA를 추가로 활용합니다.
- **Jumbo Frame**: VPC 내부에서 MTU 9001을 사용하여 대용량 전송 효율을 높일 수 있습니다.
- **Nitro 시스템**: 최신 Nitro 기반 인스턴스에서 Enhanced Networking의 성능이 가장 우수합니다.

네트워크 지연이 중요한 워크로드를 운영한다면, 적절한 인스턴스 유형 선택과 Placement Group 구성, 그리고 ENA Express 활성화를 통해 최적의 성능을 달성할 수 있습니다.