## 개요

AWS Outposts는 AWS 인프라, 서비스, API, 도구를 사용자의 온프레미스 데이터센터나 코로케이션 시설에 확장하는 완전관리형 하이브리드 클라우드 서비스입니다. 물리적 하드웨어를 AWS가 직접 사용자의 시설에 설치하고 관리하며, 클라우드와 동일한 AWS 서비스를 로컬에서 실행할 수 있게 합니다.

데이터 레지던시(Data Residency) 요구사항, 초저지연 처리 필요성, 로컬 데이터 처리 요건 등으로 인해 모든 워크로드를 퍼블릭 클라우드로 마이그레이션할 수 없는 조직이 많습니다. Outposts는 이러한 조직이 온프레미스에서도 AWS와 동일한 경험을 제공받을 수 있게 합니다.

AWS Outposts는 두 가지 폼 팩터로 제공됩니다.

- **Outposts Rack**: 42U 표준 랙 단위로 제공됩니다. EC2, EBS, S3, RDS, ECS, EKS 등 다양한 AWS 서비스를 지원합니다.
- **Outposts Server**: 1U 또는 2U 서버 단위로 제공됩니다. 공간이 제한된 소규모 환경(지점, 공장, 소매점 등)에 적합합니다.

## 핵심 기능

### Outposts Rack

Outposts Rack은 완전한 AWS 랙 형태로 제공되며, 다양한 인스턴스 타입과 AWS 서비스를 지원합니다.

지원하는 주요 서비스는 다음과 같습니다.

- Amazon EC2 (다양한 인스턴스 패밀리)
- Amazon EBS (gp2, io1)
- Amazon S3 on Outposts
- Amazon RDS (MySQL, PostgreSQL)
- Amazon ECS / Amazon EKS
- Amazon ElastiCache
- Amazon EMR
- Application Load Balancer

```bash
# Outposts 목록 조회
aws outposts list-outposts \
  --region ap-northeast-2

# 특정 Outpost 정보 조회
aws outposts get-outpost \
  --outpost-id op-0123456789abcdef0

# Outpost에서 사용 가능한 인스턴스 타입 조회
aws outposts get-outpost-instance-types \
  --outpost-id op-0123456789abcdef0
```

### Outposts Server

Outposts Server는 더 작은 폼 팩터로 제공되며, EC2와 EBS를 기본적으로 지원합니다. AWS Graviton2 프로세서 기반의 1U 서버 또는 Intel 기반의 2U 서버를 선택할 수 있습니다.

```bash
# Outposts Server에서 EC2 인스턴스 실행
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type c6gd.medium \
  --placement '{"HostId": "h-0123456789abcdef0"}' \
  --subnet-id subnet-outpost-0123456789
```

### S3 on Outposts

S3 on Outposts는 로컬에 S3 호환 스토리지를 제공합니다. 데이터가 Outpost에 로컬로 저장되며, S3 API와 동일한 인터페이스를 사용합니다.

```bash
# S3 on Outposts 버킷 생성
aws s3control create-bucket \
  --bucket my-outpost-bucket \
  --outpost-id op-0123456789abcdef0

# S3 on Outposts 엔드포인트 생성
aws s3outposts create-endpoint \
  --outpost-id op-0123456789abcdef0 \
  --subnet-id subnet-0123456789abcdef0 \
  --security-group-id sg-0123456789abcdef0

# S3 on Outposts 버킷 목록 조회
aws s3control list-regional-buckets \
  --account-id 123456789012 \
  --outpost-id op-0123456789abcdef0
```

### 네트워크 연결

Outposts는 AWS 리전과 서비스 링크(Service Link)를 통해 연결됩니다. 이 연결은 Outpost 관리, 서비스 업데이트, 메트릭 전송 등에 사용됩니다.

서비스 링크 요구사항은 다음과 같습니다.

- 최소 대역폭: 1Gbps (권장 10Gbps 이상)
- 최대 지연 시간: 서비스에 따라 다름 (일반적으로 150ms 이하)
- 암호화: 모든 통신이 자동으로 암호화됩니다.

### 로컬 게이트웨이 (Local Gateway)

Outpost에서 온프레미스 네트워크로의 통신을 위해 로컬 게이트웨이가 제공됩니다.

```bash
# 로컬 게이트웨이 조회
aws ec2 describe-local-gateways \
  --filters Name=outpost-arn,Values=arn:aws:outposts:ap-northeast-2:123456789012:outpost/op-0123456789abcdef0

# 로컬 게이트웨이 라우트 테이블 조회
aws ec2 describe-local-gateway-route-tables \
  --local-gateway-route-table-ids lgw-rtb-0123456789abcdef0

# 로컬 게이트웨이 VPC 연결
aws ec2 create-local-gateway-route-table-vpc-association \
  --local-gateway-route-table-id lgw-rtb-0123456789abcdef0 \
  --vpc-id vpc-0123456789abcdef0
```

## 아키텍처/동작 원리

### 물리적 아키텍처

Outposts Rack은 표준 42U 랙으로 제공되며, 컴퓨팅, 스토리지, 네트워킹 하드웨어가 통합되어 있습니다. 랙에는 다음 구성 요소가 포함됩니다.

- **컴퓨팅 서버**: Nitro System 기반의 EC2 호스트 서버
- **스토리지 서버**: EBS 및 S3 on Outposts용 스토리지
- **네트워킹 장비**: Top-of-Rack 스위치, 서비스 링크 연결용 장비
- **전원 장치**: 이중화된 전원 공급 장치

### 논리적 아키텍처

1. **컨트롤 플레인**: AWS 리전에 위치하며, API 호출 처리, 리소스 관리, 서비스 업데이트를 담당합니다.
2. **데이터 플레인**: Outpost 로컬에 위치하며, 워크로드 실행, 데이터 저장, 로컬 네트워킹을 처리합니다.
3. **서비스 링크**: 컨트롤 플레인과 데이터 플레인을 연결하는 암호화된 VPN 터널입니다.

### 장애 시 동작

서비스 링크가 끊어져도 로컬에서 실행 중인 EC2 인스턴스와 EBS 볼륨은 계속 동작합니다. 다만, 새로운 인스턴스 시작이나 API 호출은 서비스 링크가 복구될 때까지 불가능합니다. 이러한 설계로 인해 Outposts는 연결 장애에 대한 내결함성을 제공합니다.

### 용량 관리

Outpost의 용량은 초기 주문 시 결정되며, 이후 추가 용량을 주문할 수 있습니다.

```bash
# Outpost 용량 정보 조회
aws outposts get-outpost \
  --outpost-id op-0123456789abcdef0 \
  --query '{OutpostId: Outpost.OutpostId, AvailabilityZone: Outpost.AvailabilityZone, LifeCycleStatus: Outpost.LifeCycleStatus}'

# 카탈로그에서 사용 가능한 Outpost 구성 조회
aws outposts list-catalog-items \
  --region ap-northeast-2
```

## 실전 활용

### 데이터 레지던시 요구사항 대응

금융, 의료, 공공 부문에서는 데이터가 특정 지역 또는 시설 내에 물리적으로 저장되어야 하는 규제를 준수해야 합니다. Outposts를 사용하면 데이터를 온프레미스에 유지하면서 AWS 서비스를 활용할 수 있습니다.

```bash
# Outpost 서브넷에서 RDS 인스턴스 생성 (로컬 데이터 저장)
aws rds create-db-instance \
  --db-instance-identifier local-db \
  --db-instance-class db.m5.large \
  --engine postgres \
  --master-username admin \
  --master-user-password MySecurePassword123 \
  --db-subnet-group-name outpost-subnet-group \
  --availability-zone ap-northeast-2a-op1
```

### 저지연 로컬 처리

제조 공장의 IoT 데이터 수집, 실시간 비디오 분석, 게임 서버 등 밀리초 단위의 지연 시간이 중요한 워크로드에 적합합니다.

```bash
# Outpost 서브넷에 저지연 처리용 인스턴스 실행
aws ec2 run-instances \
  --image-id ami-0123456789abcdef0 \
  --instance-type c5.2xlarge \
  --subnet-id subnet-outpost-0123456789 \
  --placement '{"Tenancy": "default"}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Purpose,Value=low-latency-processing}]'
```

### 하이브리드 EKS 클러스터

EKS on Outposts를 사용하면 온프레미스와 클라우드에 걸친 하이브리드 Kubernetes 클러스터를 구성할 수 있습니다.

```bash
# Outpost에서 EKS 클러스터 생성
aws eks create-cluster \
  --name hybrid-cluster \
  --role-arn arn:aws:iam::123456789012:role/EKSClusterRole \
  --resources-vpc-config '{
    "subnetIds": ["subnet-outpost-01", "subnet-cloud-01"],
    "securityGroupIds": ["sg-0123456789abcdef0"]
  }' \
  --outpost-config '{
    "outpostArns": ["arn:aws:outposts:ap-northeast-2:123456789012:outpost/op-0123456789abcdef0"],
    "controlPlaneInstanceType": "m5.large"
  }'
```

### CloudFormation을 통한 IaC 관리

Outpost 리소스도 CloudFormation으로 관리할 수 있습니다.

```yaml
# cloudformation-outpost.yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: Outpost EC2 Instance

Resources:
  OutpostInstance:
    Type: AWS::EC2::Instance
    Properties:
      InstanceType: m5.xlarge
      ImageId: ami-0123456789abcdef0
      SubnetId: subnet-outpost-0123456789
      Tags:
        - Key: Name
          Value: outpost-workload

  OutpostVolume:
    Type: AWS::EC2::Volume
    Properties:
      AvailabilityZone: ap-northeast-2a
      Size: 100
      VolumeType: gp2
      OutpostArn: arn:aws:outposts:ap-northeast-2:123456789012:outpost/op-0123456789abcdef0
```

## 모범 사례/보안

### 네트워크 설계

1. **이중화된 서비스 링크**: 서비스 링크 연결을 이중화하여 단일 장애 지점을 제거합니다.
2. **충분한 대역폭**: 워크로드 특성에 따라 서비스 링크 대역폭을 적절히 산정합니다. 최소 1Gbps, 권장 10Gbps 이상입니다.
3. **로컬 게이트웨이 설정**: 온프레미스 네트워크와의 통신을 위해 로컬 게이트웨이를 적절히 구성합니다.

### 보안

1. **물리적 보안**: Outpost 랙이 설치된 시설의 물리적 접근 통제를 강화합니다.
2. **암호화**: 서비스 링크를 통한 모든 통신은 자동으로 암호화됩니다. EBS 볼륨 암호화도 활성화합니다.
3. **IAM 정책**: Outpost 리소스에 대한 접근 권한을 IAM 정책으로 제어합니다.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "outposts:Get*",
        "outposts:List*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": "ec2:RunInstances",
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:outpostArn": "arn:aws:outposts:ap-northeast-2:123456789012:outpost/op-0123456789abcdef0"
        }
      }
    }
  ]
}
```

4. **AWS Nitro System**: Outpost의 모든 서버는 Nitro System을 기반으로 하여, AWS 운영자도 고객 데이터에 접근할 수 없습니다.

### 운영

1. **AWS 관리형 인프라**: 하드웨어 유지보수, 펌웨어 업데이트, 장애 교체 등은 AWS가 직접 수행합니다.
2. **모니터링**: CloudWatch를 통해 Outpost 리소스를 모니터링합니다. 온프레미스와 동일한 메트릭과 알람을 사용할 수 있습니다.
3. **용량 계획**: 초기 용량을 신중히 계획하고, 필요에 따라 추가 용량을 주문합니다.

## 관련 서비스 비교

### AWS Outposts vs AWS Local Zones

| 항목 | AWS Outposts | AWS Local Zones |
|------|-------------|------------------|
| 위치 | 고객 데이터센터 | AWS 관리 시설 (대도시 근접) |
| 관리 주체 | AWS (고객 시설에 설치) | AWS |
| 하드웨어 소유 | AWS | AWS |
| 연결 방식 | 서비스 링크 (고객 네트워크) | AWS 백본 |
| 주요 목적 | 데이터 레지던시, 온프레미스 통합 | 저지연 (대도시 사용자) |
| 비용 모델 | 3년 약정 (월/선불) | 온디맨드 (일반 EC2와 유사) |

### AWS Outposts vs Azure Stack Hub

| 항목 | AWS Outposts | Azure Stack Hub |
|------|-------------|------------------|
| 관리 모델 | AWS 완전관리 | 고객 자체 관리 |
| 하드웨어 | AWS 전용 하드웨어 | 인증된 파트너 하드웨어 |
| 서비스 범위 | 다수의 AWS 서비스 | Azure 서비스 서브셋 |
| 연결 끊김 시 | 기존 워크로드 유지 | 독립 실행 가능 |

### AWS Outposts vs AWS Wavelength

Wavelength는 5G 통신사 네트워크 엣지에 AWS 컴퓨팅을 배치하는 서비스입니다. 모바일 사용자를 대상으로 한 초저지연 서비스에 적합합니다. Outposts는 기업 데이터센터에 배치되므로 용도가 다릅니다.

### AWS Outposts vs AWS Snow Family

Snow Family(Snowcone, Snowball, Snowmobile)는 데이터 마이그레이션과 엣지 컴퓨팅용 휴대형 장비입니다. Outposts는 장기적인 하이브리드 인프라 운영용이고, Snow Family는 일시적인 데이터 전송이나 연결이 제한된 환경의 엣지 컴퓨팅에 적합합니다.

## 요약

AWS Outposts는 AWS 인프라와 서비스를 온프레미스 환경으로 확장하는 하이브리드 클라우드 서비스입니다. Outposts Rack은 풀 랙 형태로 다양한 AWS 서비스를 지원하며, Outposts Server는 소규모 환경에 적합한 1U/2U 서버 형태로 제공됩니다.

데이터 레지던시 규제 준수, 초저지연 로컬 처리, 온프레미스 시스템과의 긴밀한 통합이 필요한 워크로드에 적합합니다. AWS가 하드웨어 유지보수, 소프트웨어 업데이트 등 인프라 관리를 전담하므로, 사용자는 애플리케이션 운영에 집중할 수 있습니다.

도입 시에는 서비스 링크 이중화, 충분한 네트워크 대역폭 확보, 물리적 보안 강화, 적절한 용량 계획을 사전에 수립하는 것이 중요합니다. Local Zones, Wavelength, Snow Family 등 유사한 서비스와의 차이점을 이해하고, 워크로드 특성에 맞는 서비스를 선택해야 합니다.