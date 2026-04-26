<!-- infographic-hero -->
![AWS Wavelength 핵심 요약](figures/infographic.svg)

*Figure: AWS Wavelength 한 장 요약 인포그래픽*

## 개요

AWS Wavelength는 5G 통신사(Carrier) 네트워크의 엣지에 AWS 컴퓨팅과 스토리지 서비스를 배치하는 서비스입니다. 이를 통해 모바일 디바이스와 최종 사용자에게 한 자릿수 밀리초(single-digit milliseconds) 수준의 초저지연 서비스를 제공할 수 있습니다.

일반적인 모바일 애플리케이션에서 요청은 모바일 디바이스 -> 5G 기지국 -> 통신사 네트워크 -> 인터넷 -> AWS 리전 순서로 전달됩니다. 이 과정에서 수십 밀리초의 지연이 발생합니다. Wavelength를 사용하면 통신사 네트워크 내부에 AWS 컴퓨팅이 배치되므로, 인터넷을 거치지 않고 통신사 네트워크 내에서 직접 응답할 수 있습니다.

AWS Wavelength가 해결하는 핵심 문제는 다음과 같습니다.

- 5G 초저지연 요구사항: AR/VR, 실시간 게임, 자율주행 등 밀리초 단위의 응답이 필요한 서비스
- 대역폭 최적화: 대용량 데이터를 통신사 네트워크 내에서 처리하여 백홀 트래픽을 줄임
- 엣지 컴퓨팅: 데이터 발생 지점에서 가까운 곳에서 처리하여 사용자 경험을 개선

현재 Wavelength를 지원하는 통신사는 Verizon(미국), Vodafone(유럽), KDDI(일본), SK Telecom(한국), Bell Canada(캐나다) 등이 있습니다.

## 핵심 기능

### Wavelength Zone

Wavelength Zone은 통신사 데이터센터 내에 배치된 AWS 인프라 배포 단위입니다. 각 Wavelength Zone은 AWS 리전의 VPC를 확장하는 서브넷으로 구성됩니다.

```bash
# 사용 가능한 Wavelength Zone 조회
aws ec2 describe-availability-zones \
  --filters Name=zone-type,Values=wavelength-zone \
  --region us-east-1

# Wavelength Zone 활성화 (옵트인)
aws ec2 modify-availability-zone-group \
  --group-name us-east-1-wl1 \
  --opt-in-status opted-in

# Wavelength Zone에 서브넷 생성
aws ec2 create-subnet \
  --vpc-id vpc-0123456789abcdef0 \
  --cidr-block 10.0.100.0/24 \
  --availability-zone us-east-1-wl1-bos-wlz-1 \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=wavelength-subnet}]'
```

### 캐리어 게이트웨이 (Carrier Gateway)

Wavelength Zone에서 통신사 네트워크(5G/LTE)로의 인바운드/아웃바운드 트래픽을 라우팅하는 게이트웨이입니다. 인터넷 게이트웨이와 유사한 역할을 하지만, 통신사 네트워크를 대상으로 합니다.

```bash
# 캐리어 게이트웨이 생성
aws ec2 create-carrier-gateway \
  --vpc-id vpc-0123456789abcdef0 \
  --tag-specifications 'ResourceType=carrier-gateway,Tags=[{Key=Name,Value=my-carrier-gw}]'

# 캐리어 게이트웨이 조회
aws ec2 describe-carrier-gateways \
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0

# 라우트 테이블에 캐리어 게이트웨이 경로 추가
aws ec2 create-route \
  --route-table-id rtb-wavelength-0123456789 \
  --destination-cidr-block 0.0.0.0/0 \
  --carrier-gateway-id cagw-0123456789abcdef0
```

### 캐리어 IP 주소

Wavelength Zone의 EC2 인스턴스에 할당할 수 있는 공인 IP 주소입니다. 통신사 네트워크에서 직접 접근 가능한 주소입니다.

```bash
# 캐리어 IP 주소 할당
aws ec2 allocate-address \
  --domain vpc \
  --network-border-group us-east-1-wl1-bos-wlz-1

# 캐리어 IP를 EC2 인스턴스에 연결
aws ec2 associate-address \
  --allocation-id eipalloc-0123456789abcdef0 \
  --network-interface-id eni-0123456789abcdef0
```

### 지원되는 서비스

Wavelength Zone에서 사용할 수 있는 AWS 서비스는 다음과 같습니다.

- Amazon EC2 (t3, g4dn, r5, m5 등)
- Amazon EBS (gp2 볼륨)
- Amazon ECS
- Amazon EKS
- Amazon VPC (서브넷, 보안 그룹, ENI)
- AWS IAM
- Amazon CloudWatch
- AWS CloudFormation

리전에서만 사용 가능한 서비스(RDS, S3, DynamoDB 등)에 접근하려면 VPC를 통해 리전으로 트래픽을 라우팅합니다.

## 아키텍처/동작 원리

### 네트워크 아키텍처

Wavelength의 네트워크 아키텍처는 다음과 같이 구성됩니다.

1. **5G 디바이스**: 최종 사용자의 모바일 디바이스가 5G 기지국에 연결됩니다.
2. **통신사 5G 네트워크**: 기지국에서 통신사의 코어 네트워크로 트래픽이 전달됩니다.
3. **Wavelength Zone**: 통신사 네트워크 내부에 위치한 AWS 인프라에서 요청을 처리합니다.
4. **AWS 리전**: Wavelength Zone에서 처리할 수 없는 요청은 VPC를 통해 리전으로 전달됩니다.

이 구조에서 핵심은 5G 디바이스의 트래픽이 인터넷을 거치지 않고 통신사 네트워크 내부에서 직접 Wavelength Zone으로 라우팅된다는 점입니다. 이를 통해 일반적으로 10~20ms 이상인 지연 시간을 5ms 이하로 줄일 수 있습니다.

### VPC 확장 모델

Wavelength Zone은 기존 VPC의 서브넷으로 구성됩니다. 하나의 VPC가 여러 Wavelength Zone으로 확장될 수 있으며, 리전의 AZ 서브넷과 Wavelength Zone 서브넷 간에 VPC 내부 통신이 가능합니다.

리전 AZ의 리소스에서 Wavelength Zone의 리소스로 접근할 때는 VPC 내부 라우팅을 사용합니다. 이때 트래픽은 AWS 백본 네트워크를 통해 전달되므로 통신사 네트워크를 거치지 않습니다.

### 트래픽 흐름 패턴

**패턴 1: 5G 디바이스 -> Wavelength Zone (초저지연)**
5G 사용자 트래픽이 캐리어 게이트웨이를 통해 Wavelength Zone의 EC2 인스턴스에 직접 도달합니다.

**패턴 2: Wavelength Zone -> AWS 리전 (백엔드 처리)**
Wavelength Zone의 EC2 인스턴스가 VPC 라우팅을 통해 리전의 RDS, DynamoDB, S3 등에 접근합니다.

**패턴 3: 인터넷 -> Wavelength Zone (비5G 접근)**
캐리어 게이트웨이를 통해 일반 인터넷에서도 Wavelength Zone에 접근할 수 있습니다.

## 실전 활용

### 실시간 게임 서버

5G 환경에서 초저지연 게임 서버를 구축하는 예제입니다.

```bash
# Wavelength Zone에 게임 서버 인스턴스 실행
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type c5.xlarge \
  --subnet-id subnet-wavelength-0123456789 \
  --security-group-ids sg-0123456789abcdef0 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=game-server-wl1}]' \
  --user-data file://game-server-init.sh

# 캐리어 IP 할당 및 연결
ALLOC_ID=$(aws ec2 allocate-address \
  --domain vpc \
  --network-border-group us-east-1-wl1-bos-wlz-1 \
  --query 'AllocationId' --output text)

aws ec2 associate-address \
  --allocation-id $ALLOC_ID \
  --instance-id i-0123456789abcdef0
```

### AR/VR 스트리밍 서비스

5G 네트워크를 통한 AR/VR 콘텐츠 스트리밍 아키텍처입니다. GPU 인스턴스를 Wavelength Zone에 배치하여 렌더링을 처리합니다.

```bash
# GPU 인스턴스로 AR/VR 렌더링 서버 배포
aws ec2 run-instances \
  --image-id ami-gpu-rendering-0123 \
  --instance-type g4dn.2xlarge \
  --subnet-id subnet-wavelength-0123456789 \
  --security-group-ids sg-0123456789abcdef0 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=ar-vr-renderer}]'
```

### EKS on Wavelength

Wavelength Zone에서 EKS를 사용하여 컨테이너 기반 애플리케이션을 배포하는 예제입니다.

```bash
# EKS 클러스터의 노드 그룹을 Wavelength Zone에 생성
aws eks create-nodegroup \
  --cluster-name edge-cluster \
  --nodegroup-name wavelength-nodes \
  --subnets subnet-wavelength-0123456789 \
  --instance-types c5.xlarge \
  --scaling-config minSize=1,maxSize=5,desiredSize=2 \
  --node-role arn:aws:iam::123456789012:role/EKSNodeRole
```

### 멀티 Wavelength Zone 배포

여러 Wavelength Zone에 걸쳐 배포하여 지리적으로 분산된 초저지연 서비스를 구축할 수 있습니다.

```python
import boto3

def deploy_to_wavelength_zones(vpc_id, ami_id, instance_type='c5.xlarge'):
    """여러 Wavelength Zone에 인스턴스를 배포합니다."""
    ec2 = boto3.client('ec2', region_name='us-east-1')
    
    # Wavelength Zone 목록 조회
    zones = ec2.describe_availability_zones(
        Filters=[{'Name': 'zone-type', 'Values': ['wavelength-zone']}]
    )['AvailabilityZones']
    
    deployed_instances = []
    
    for zone in zones:
        zone_name = zone['ZoneName']
        
        # 각 Wavelength Zone에 서브넷 생성 (이미 존재하는 경우 스킵)
        try:
            subnet = ec2.create_subnet(
                VpcId=vpc_id,
                CidrBlock=f'10.0.{len(deployed_instances) + 100}.0/24',
                AvailabilityZone=zone_name
            )['Subnet']
            subnet_id = subnet['SubnetId']
        except Exception as e:
            print(f"서브넷 생성 실패 ({zone_name}): {e}")
            continue
        
        # 인스턴스 배포
        response = ec2.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            SubnetId=subnet_id,
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[{
                'ResourceType': 'instance',
                'Tags': [
                    {'Key': 'Name', 'Value': f'edge-server-{zone_name}'},
                    {'Key': 'WavelengthZone', 'Value': zone_name}
                ]
            }]
        )
        
        instance_id = response['Instances'][0]['InstanceId']
        deployed_instances.append({
            'zone': zone_name,
            'instance_id': instance_id,
            'subnet_id': subnet_id
        })
    
    return deployed_instances
```

### IoT 데이터 실시간 처리

제조 공장이나 스마트 시티의 IoT 센서 데이터를 5G 네트워크를 통해 Wavelength Zone에서 실시간으로 처리하는 아키텍처를 구성할 수 있습니다.

```bash
# IoT 데이터 처리 서버 배포
aws ec2 run-instances \
  --image-id ami-iot-processor-0123 \
  --instance-type m5.2xlarge \
  --subnet-id subnet-wavelength-0123456789 \
  --security-group-ids sg-0123456789abcdef0 \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=iot-edge-processor}]'

# 처리된 데이터를 리전의 S3로 전송하는 경로 확인
aws ec2 describe-route-tables \
  --filters Name=association.subnet-id,Values=subnet-wavelength-0123456789
```

## 모범 사례/보안

### 아키텍처 설계

1. **2-tier 아키텍처**: 지연 시간에 민감한 로직은 Wavelength Zone에, 상태 저장이나 복잡한 처리는 리전에 배치하는 2-tier 아키텍처를 권장합니다.
2. **상태 비저장 설계**: Wavelength Zone의 인스턴스는 가능한 한 상태 비저장(Stateless)으로 설계합니다. 상태가 필요한 경우 리전의 DynamoDB나 ElastiCache에 저장합니다.
3. **폴백 전략**: Wavelength Zone이 불가용할 경우 리전으로 폴백하는 전략을 구성합니다.

### 보안

1. **보안 그룹 설정**: Wavelength Zone의 보안 그룹에서 필요한 포트만 개방합니다.
2. **VPC Flow Logs**: Wavelength Zone 서브넷의 트래픽을 VPC Flow Logs로 모니터링합니다.
3. **암호화**: 전송 중 데이터와 저장 데이터 모두 암호화합니다. EBS 볼륨 암호화를 활성화합니다.

```bash
# Wavelength Zone 서브넷에 VPC Flow Logs 활성화
aws ec2 create-flow-logs \
  --resource-type Subnet \
  --resource-ids subnet-wavelength-0123456789 \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name /vpc/wavelength-flow-logs \
  --deliver-logs-permission-arn arn:aws:iam::123456789012:role/FlowLogsRole
```

### 비용 최적화

1. **필요한 서비스만 Wavelength에 배치**: 모든 것을 Wavelength Zone에 배치하지 않고, 저지연이 필요한 컴포넌트만 배치합니다.
2. **Auto Scaling 활용**: 트래픽 패턴에 따라 인스턴스를 자동으로 스케일링합니다.
3. **데이터 전송 비용**: Wavelength Zone과 리전 간 데이터 전송 비용을 고려하여 아키텍처를 설계합니다.

## 관련 서비스 비교

### Wavelength vs Local Zones

| 항목 | Wavelength | Local Zones |
|------|-----------|-------------|
| 위치 | 5G 통신사 네트워크 내부 | AWS 관리 시설 (대도시 인근) |
| 대상 사용자 | 5G 모바일 디바이스 | 일반 인터넷 사용자 |
| 지연 시간 | 초저지연 (5ms 이하) | 저지연 (10ms 이하) |
| 접근 방식 | 캐리어 게이트웨이 | 인터넷 게이트웨이 |
| 서비스 범위 | 제한적 (EC2, EBS, ECS, EKS) | 더 넓음 (RDS, ElastiCache 포함) |
| 적합한 사용 사례 | 5G 기반 실시간 앱 | 일반 저지연 앱 |

### Wavelength vs AWS Outposts

| 항목 | Wavelength | Outposts |
|------|-----------|----------|
| 위치 | 통신사 데이터센터 | 고객 데이터센터 |
| 하드웨어 관리 | AWS | AWS |
| 네트워크 | 5G 통신사 네트워크 | 고객 자체 네트워크 |
| 주요 목적 | 5G 엣지 컴퓨팅 | 하이브리드 클라우드, 데이터 레지던시 |
| 서비스 범위 | 제한적 | 넓음 (S3, RDS 포함) |

### Wavelength vs CloudFront

CloudFront는 CDN 서비스로 정적 콘텐츠 캐싱에 최적화되어 있습니다. Wavelength는 동적 컴퓨팅 처리에 특화되어 있으며, 5G 네트워크와의 직접 연결이라는 차별점이 있습니다. 실시간 컴퓨팅이 필요한 경우 Wavelength를, 정적 콘텐츠 전달이 필요한 경우 CloudFront를 사용합니다.

## 요약

AWS Wavelength는 5G 통신사 네트워크 엣지에 AWS 컴퓨팅을 배치하여 한 자릿수 밀리초의 초저지연 서비스를 가능하게 하는 서비스입니다. Wavelength Zone이라는 배포 단위를 통해 기존 VPC를 통신사 네트워크까지 확장하며, 캐리어 게이트웨이를 통해 5G 디바이스와 직접 통신합니다.

실시간 게임, AR/VR 스트리밍, 자율주행 차량 데이터 처리, IoT 실시간 분석 등 초저지연이 필수적인 서비스에 적합합니다. 지연 시간에 민감한 로직만 Wavelength Zone에 배치하고, 나머지는 리전에 두는 2-tier 아키텍처를 권장합니다.

도입 시에는 지원되는 통신사와 Wavelength Zone 위치를 확인하고, 캐리어 게이트웨이와 캐리어 IP 설정을 적절히 구성해야 합니다. Local Zones, Outposts 등 유사한 엣지 서비스와의 차이를 이해하고 워크로드 특성에 맞는 서비스를 선택하는 것이 중요합니다.