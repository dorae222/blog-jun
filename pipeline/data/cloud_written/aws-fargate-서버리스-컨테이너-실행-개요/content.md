<!-- infographic-hero -->
![AWS Fargate 핵심 요약](figures/infographic.svg)

*Figure: AWS Fargate 한 장 요약 인포그래픽*

# AWS Fargate 서버리스 컨테이너 실행 개요

## 개요

AWS Fargate는 2017년 11월 re:Invent에서 발표된 서버리스 컨테이너 컴퓨트 엔진입니다. 기존 ECS/EKS는 컨테이너를 실행하기 위해 EC2 인스턴스를 프로비저닝하고 클러스터에 등록해야 했고, 인스턴스의 OS 패치, 보안 업데이트, Auto Scaling 그룹 관리 등을 사용자가 직접 처리해야 했습니다.

Fargate는 이러한 부담을 완전히 제거합니다. 사용자는 컨테이너 이미지와 실행에 필요한 vCPU/메모리만 지정하면 되고, 그 아래의 EC2 인스턴스, OS, 커널, 클러스터 노드 관리는 모두 AWS가 처리합니다. 결제는 컨테이너가 실제로 실행된 vCPU-시간과 메모리-시간 단위로 이루어지며, 1초 단위(최소 1분)로 청구됩니다.

Fargate가 해결하는 핵심 문제는 다음과 같습니다.

- **인프라 운영 부담 제거**: EC2 인스턴스 관리, AMI 패치, 클러스터 capacity provider 튜닝 등이 불필요
- **격리성 향상**: Firecracker microVM 기반으로 태스크별 강력한 격리 제공
- **빠른 시작 시간**: EC2 인스턴스 부팅 없이 태스크 단위로 빠르게 시작
- **세밀한 과금**: 실제 사용한 컴퓨트 자원만 1초 단위로 결제

Fargate는 ECS와 EKS 양쪽에서 모두 사용 가능합니다(ECS Fargate, EKS Fargate Profile). 동일한 Fargate 엔진이지만 인터페이스와 구성 방식이 약간 다릅니다.

---

## 핵심 기능

### 1. 유연한 vCPU/메모리 조합

Fargate는 다양한 vCPU/메모리 조합을 지원하여 워크로드에 정확히 맞는 자원을 할당할 수 있습니다.

| vCPU | 메모리 옵션 |
|------|-------------|
| 0.25 | 0.5GB, 1GB, 2GB |
| 0.5 | 1GB - 4GB (1GB 단위) |
| 1 | 2GB - 8GB |
| 2 | 4GB - 16GB |
| 4 | 8GB - 30GB |
| 8 | 16GB - 60GB |
| 16 | 32GB - 120GB |

또한 ARM 기반 Graviton2 프로세서를 지원하여 x86 대비 40% 가격 대비 성능 향상을 제공합니다(`runtimePlatform.cpuArchitecture: ARM64`).

```bash
# ECS 태스크 정의에서 vCPU/메모리 지정
aws ecs register-task-definition \
  --family my-fargate-task \
  --network-mode awsvpc \
  --requires-compatibilities FARGATE \
  --cpu "1024" \
  --memory "2048" \
  --runtime-platform "operatingSystemFamily=LINUX,cpuArchitecture=ARM64" \
  --execution-role-arn arn:aws:iam::123456789012:role/ecsTaskExecutionRole \
  --container-definitions '[{
    "name": "app",
    "image": "123456789012.dkr.ecr.ap-northeast-2.amazonaws.com/my-app:latest",
    "essential": true,
    "portMappings": [{"containerPort": 8080, "protocol": "tcp"}],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/my-fargate-task",
        "awslogs-region": "ap-northeast-2",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]' \
  --region ap-northeast-2
```

### 2. ECS Fargate

ECS Fargate는 ECS 클러스터 내에서 실행되는 Fargate 태스크입니다.

- **Capacity Provider**: `FARGATE`, `FARGATE_SPOT`을 지정하여 결정
- **서비스 통합**: ECS Service로 관리하면 Auto Scaling, ALB/NLB 통합 자동 처리
- **CloudFormation/CDK 친화적**: AWS IaC 도구와 자연스럽게 통합

```bash
# ECS Fargate 서비스 생성
aws ecs create-service \
  --cluster my-cluster \
  --service-name my-app-service \
  --task-definition my-fargate-task \
  --desired-count 3 \
  --launch-type FARGATE \
  --capacity-provider-strategy "capacityProvider=FARGATE,weight=1,base=1" "capacityProvider=FARGATE_SPOT,weight=4" \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-aaa,subnet-bbb],securityGroups=[sg-app],assignPublicIp=DISABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:ap-northeast-2:123456789012:targetgroup/my-tg/abc,containerName=app,containerPort=8080" \
  --region ap-northeast-2
```

### 3. EKS Fargate

EKS Fargate는 Kubernetes Pod를 Fargate microVM에서 실행합니다.

- **Fargate Profile**: 네임스페이스 + 라벨 셀렉터로 어떤 Pod가 Fargate에서 실행될지 결정
- **Pod 1개 = microVM 1개**: 강력한 격리, 단 DaemonSet 미지원
- **kube-proxy/CoreDNS 호환**: 단, kube-proxy는 자동 적용

```bash
# EKS Fargate 프로파일 생성 (예: kube-system 제외, 모든 default Pod)
aws eks create-fargate-profile \
  --cluster-name my-eks-cluster \
  --fargate-profile-name fp-app \
  --pod-execution-role-arn arn:aws:iam::123456789012:role/AmazonEKSFargatePodExecutionRole \
  --selectors '[{"namespace":"default"}]' \
  --subnets subnet-aaa subnet-bbb \
  --region ap-northeast-2
```

### 4. awsvpc 네트워크 모드

Fargate는 항상 `awsvpc` 네트워크 모드를 사용합니다.

- **태스크당 ENI 1개**: 각 태스크는 독립된 ENI(Elastic Network Interface)를 가짐
- **VPC IP 직접 할당**: VPC 내 다른 리소스에서 직접 접근 가능
- **Security Group 부착**: 태스크별 Security Group 적용
- **Public IP 옵션**: `assignPublicIp` 설정으로 인터넷 접근 제어

이 모델은 보안과 네트워크 격리에 유리하지만, ENI 한도와 IP 주소 소비에 주의해야 합니다.

```yaml
# Fargate 호환 awsvpc 구성 예시 (ECS)
networkConfiguration:
  awsvpcConfiguration:
    subnets:
      - subnet-0a1b2c3d
      - subnet-1b2c3d4e
    securityGroups:
      - sg-0123456789abcdef0
    assignPublicIp: DISABLED
```

### 5. Fargate Spot

Fargate Spot은 AWS 여유 용량을 활용하여 일반 Fargate 대비 최대 70% 할인된 가격을 제공합니다.

- **2분 사전 알림**: 회수 전 SIGTERM과 함께 알림
- **무중단 워크로드 부적합**: 배치, 빌드 파이프라인, fault-tolerant 큐 처리에 적합
- **EKS 미지원**: ECS Fargate에서만 사용 가능 (EKS는 Karpenter + EC2 Spot으로 우회)

```bash
# Fargate Spot 비율 설정 (capacity provider strategy)
aws ecs put-cluster-capacity-providers \
  --cluster my-cluster \
  --capacity-providers FARGATE FARGATE_SPOT \
  --default-capacity-provider-strategy "capacityProvider=FARGATE_SPOT,weight=4,base=0" "capacityProvider=FARGATE,weight=1,base=2" \
  --region ap-northeast-2
```

---

## 아키텍처

### Fargate 실행 환경 구조

```
[ECS/EKS API]
       |
       v
[Fargate Scheduler]
       |
       v
[Capacity Pool (AZ별)]
       |
       v
[Firecracker microVM]
   - Linux 커널
   - container runtime (containerd)
   - 사용자 컨테이너 (1개 이상)
       |
       v
[ENI in 고객 VPC]
       |
       v
[Subnet / Security Group]
```

1. **Firecracker microVM**: Lambda와 동일한 경량 VM 기술. 부팅 시간이 매우 짧고 강한 격리성을 제공합니다.
2. **태스크 = microVM 1개**: 한 태스크 내 여러 컨테이너는 같은 microVM을 공유합니다(같은 IP, 같은 시스템 자원).
3. **ENI Trunk**: AWS가 microVM에서 고객 VPC의 subnet으로 ENI를 직접 연결합니다.

### 콜드 스타트 분석

Fargate 태스크가 시작되기까지의 단계별 시간은 대략 다음과 같습니다.

| 단계 | 일반적 소요 시간 |
|------|------------------|
| Scheduler 배치 | 1-5초 |
| microVM 프로비저닝 | 5-10초 |
| ENI 생성 및 연결 | 5-10초 |
| 이미지 풀링 (1GB 기준) | 5-15초 |
| 컨테이너 실행 | 1-5초 |
| 헬스체크 통과 | 5-30초 |
| **합계** | 30-60초 |

이 시간을 단축하기 위한 권장사항:

- **이미지 크기 최소화**: distroless, Alpine, multi-stage build
- **ECR 사용**: 동일 리전 ECR이 가장 빠름
- **Seekable OCI(SOCI)**: 이미지 풀링 병렬화로 시작 시간 단축
- **헬스체크 튜닝**: 빠른 startup probe 적용

### 스토리지

- **Ephemeral Storage**: 기본 20GB(공유), 최대 200GB까지 증설 가능
- **EFS**: 영구 스토리지가 필요한 경우 EFS를 마운트
- **EBS (2024+)**: ECS Fargate는 EBS 볼륨 부착 지원(EKS Fargate는 미지원)

```bash
# Ephemeral storage 200GB로 증설
aws ecs register-task-definition \
  --family my-large-task \
  --requires-compatibilities FARGATE \
  --cpu "2048" \
  --memory "8192" \
  --ephemeral-storage "sizeInGiB=200" \
  --container-definitions file://container.json \
  --region ap-northeast-2
```

---

## 실전 사용

### 1. 배치 작업 (단발성)

매일 자정 데이터를 집계하는 ETL 잡을 Fargate로 실행하는 패턴입니다.

```bash
# 단발 태스크 실행 (RunTask)
aws ecs run-task \
  --cluster my-cluster \
  --task-definition daily-etl-job \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-aaa],securityGroups=[sg-etl],assignPublicIp=DISABLED}" \
  --count 1 \
  --region ap-northeast-2

# EventBridge 스케줄로 자동 실행
aws events put-rule \
  --name daily-etl-schedule \
  --schedule-expression "cron(0 15 * * ? *)" \
  --region ap-northeast-2
```

### 2. 마이크로서비스 (장기 실행 서비스)

ECS Service로 컨테이너 N개를 항상 실행 상태로 유지하며 ALB와 통합합니다.

```yaml
# CDK (TypeScript) 예시
const taskDef = new ecs.FargateTaskDefinition(this, 'TaskDef', {
  cpu: 1024,
  memoryLimitMiB: 2048,
  runtimePlatform: { cpuArchitecture: ecs.CpuArchitecture.ARM64 },
});

taskDef.addContainer('app', {
  image: ecs.ContainerImage.fromEcrRepository(repo, 'latest'),
  portMappings: [{ containerPort: 8080 }],
  logging: ecs.LogDrivers.awsLogs({ streamPrefix: 'app' }),
});

new ecs.FargateService(this, 'Service', {
  cluster,
  taskDefinition: taskDef,
  desiredCount: 3,
  capacityProviderStrategies: [
    { capacityProvider: 'FARGATE_SPOT', weight: 4 },
    { capacityProvider: 'FARGATE', weight: 1, base: 1 },
  ],
});
```

### 3. EKS Fargate Pod 예시

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:1.27
          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "500m"
              memory: "1Gi"
```

Fargate는 `requests.cpu/memory`를 기준으로 가장 가까운 vCPU/메모리 조합을 자동 선택합니다.

---

## 가격/한도

### 가격 모델 (us-east-1, x86)

| 항목 | 가격 |
|------|------|
| vCPU | 시간당 $0.04048 |
| 메모리 | GB-시간당 $0.004445 |
| Ephemeral Storage (20GB 초과분) | GB-시간당 $0.000111 |
| Fargate Spot (vCPU) | 시간당 $0.012144 (약 70% 할인) |
| Fargate Spot (메모리) | GB-시간당 $0.001335 |
| Graviton ARM (vCPU) | 시간당 $0.03238 (약 20% 할인) |
| Windows Container | x86 Linux 대비 약 50% 추가 |

**계산 예시**: 1 vCPU, 2GB, 24시간/30일 운영
- vCPU: 0.04048 * 24 * 30 = $29.15
- 메모리: 0.004445 * 2 * 24 * 30 = $6.40
- 합계: 약 $35.55/월

EC2 t3.small(약 $14)보다 비싸지만, OS 패치/관리/스케줄링 노력을 고려하면 운영 인력 비용을 절감할 수 있습니다.

### 주요 한도

| 항목 | 기본 한도 |
|------|-----------|
| 동시 실행 태스크 (계정/리전) | 1000 |
| 태스크당 컨테이너 수 | 10 |
| ENI 한도 (subnet당) | 32,768 (계정당 5000) |
| Ephemeral Storage 최대 | 200GB |
| Spot 회수 알림 | 2분 |

```bash
# 동시 실행 한도 조회
aws service-quotas get-service-quota \
  --service-code fargate \
  --quota-code L-3032A538 \
  --region ap-northeast-2
```

---

## Best Practice

### 권장 패턴

1. **Spot + On-demand 혼합**: 무중단 워크로드는 일부 On-demand로 베이스 확보, 나머지는 Spot으로 비용 절감
2. **Graviton ARM 우선 사용**: 대부분의 컨테이너 이미지는 멀티아키 빌드로 ARM 지원
3. **이미지 최적화**: distroless, multi-stage build로 시작 시간 단축
4. **awsvpc IP 풀 모니터링**: subnet의 가용 IP 주소 부족이 가장 흔한 장애 원인
5. **CloudWatch Container Insights**: vCPU/메모리 사용률을 추적하여 right-sizing
6. **Application Auto Scaling**: CPU/메모리/큐 길이 기반 ECS Service Auto Scaling 활성화
7. **Task Role과 Execution Role 분리**: 태스크 코드용 권한과 ECR/Logs 풀링용 권한을 분리

### 안티 패턴

1. **고트래픽 + 24/365 워크로드**: vCPU 시간 비용이 EC2 capacity provider 대비 2-3배 비쌀 수 있음
2. **DaemonSet 의존**: EKS Fargate는 DaemonSet 미지원 - 사이드카 컨테이너로 우회 필요
3. **HostNetwork/HostPort 사용**: Fargate는 awsvpc 강제로 hostNetwork 미지원
4. **GPU 워크로드**: Fargate는 GPU 미지원 - EC2 g4dn/p4 인스턴스 필요
5. **장기 SSH 접속**: Fargate는 SSH 미지원 - ECS Exec(`aws ecs execute-command`) 사용

```bash
# ECS Exec로 컨테이너 진입 (SSH 대안)
aws ecs execute-command \
  --cluster my-cluster \
  --task abc123def456 \
  --container app \
  --interactive \
  --command "/bin/sh" \
  --region ap-northeast-2
```

### Fargate vs EC2 capacity provider

| 항목 | Fargate | EC2 (Auto Scaling Group) |
|------|---------|---------------------------|
| 인프라 관리 | 없음 | 사용자 책임 |
| 시작 시간 | 30-60초 | 인스턴스 부팅 후 즉시 |
| 비용 (고밀도) | 비쌈 | 저렴 |
| 비용 (저밀도) | 저렴 | 비쌈 (idle 인스턴스) |
| GPU | 미지원 | 지원 |
| Spot | 지원 (70% 할인) | 지원 (90% 할인 가능) |
| 스토리지 옵션 | Ephemeral, EFS, EBS(ECS) | Ephemeral, EBS, instance store, EFS |

---

## 관련 서비스

| 서비스 | 관계 |
|--------|------|
| Amazon ECS | Fargate 태스크 오케스트레이션 |
| Amazon EKS | Kubernetes Pod를 Fargate에서 실행 |
| Amazon ECR | 컨테이너 이미지 저장소 |
| Application Load Balancer / NLB | Fargate 태스크에 트래픽 라우팅 |
| Amazon CloudWatch | 로그 및 Container Insights 메트릭 |
| AWS App Runner | Fargate 위에 빌드된 더 단순한 PaaS |
| AWS Batch | Fargate 기반 배치 작업 실행 |
| AWS Step Functions | Fargate 태스크 오케스트레이션 |
| Amazon EFS | 영구 파일 스토리지 마운트 |
| AWS Copilot | ECS Fargate IaC CLI |

---

## 관련 문서

- [[amazon-elastic-container-service-amazon-ecs|Amazon ECS]] - Fargate의 주된 실행 플랫폼
- [[amazon-eks-elastic-kubernetes-service-개요|Amazon EKS]] - Kubernetes 환경에서 Fargate 활용
- [[aws-lambda-개요-및-실전-활용-가이드|AWS Lambda]] - 더 짧은 워크로드용 서버리스, 콜드 스타트가 더 빠름
- [[amazon-efs-elastic-file-system-개요|Amazon EFS]] - Fargate 태스크의 영구 파일 스토리지
