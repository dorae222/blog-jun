<!-- infographic-hero -->
![Amazon EKS 핵심 요약](figures/infographic.svg)

*Figure: Amazon EKS 한 장 요약 인포그래픽*

# Amazon EKS(Elastic Kubernetes Service) 개요

## 개요

Amazon EKS(Elastic Kubernetes Service)는 2018년 6월에 일반 출시(GA)된 AWS의 관리형 Kubernetes 서비스입니다. Kubernetes는 사실상의 컨테이너 오케스트레이션 표준이 되었지만, 컨트롤 플레인(API Server, etcd, Scheduler, Controller Manager)을 직접 운영하는 것은 매우 복잡한 일입니다. 인증서 갱신, etcd 백업/복원, 컴포넌트 버전 호환성 관리, 고가용성 구성 등 모든 작업을 직접 처리해야 하기 때문입니다.

EKS는 이 컨트롤 플레인을 AWS가 완전히 관리하며, 사용자는 워커 노드와 워크로드에만 집중할 수 있습니다. 또한 EKS는 CNCF 인증을 받은 표준 Kubernetes를 그대로 사용하므로, 온프레미스 또는 다른 클라우드의 Kubernetes 워크로드를 코드 변경 없이 그대로 마이그레이션할 수 있는 이식성을 제공합니다.

EKS의 등장 배경에는 다음과 같은 시장 요구가 있었습니다.

- AWS 자체 컨테이너 오케스트레이터인 ECS는 Kubernetes 표준이 아니라 AWS 종속적입니다.
- 기업이 멀티클라우드 또는 하이브리드 전략을 채택하기 위해 표준화된 Kubernetes가 필요했습니다.
- 컨트롤 플레인 운영의 부담을 제거하면서도 Kubernetes의 강력한 기능을 그대로 활용하고 싶은 수요가 있었습니다.

EKS는 현재 마이크로서비스 플랫폼, 머신러닝 학습/추론 인프라(Kubeflow, KServe), CI/CD 파이프라인(ArgoCD, Tekton), 데이터 처리(Spark on K8s) 등 다양한 영역에서 활용되고 있습니다.

---

## 핵심 기능

### 1. 관리형 컨트롤 플레인

EKS는 Kubernetes 컨트롤 플레인을 3개의 가용 영역(AZ)에 자동으로 분산 배치하여 고가용성을 보장합니다.

- **자동 패치/업그레이드**: 마이너 버전 업그레이드는 사용자가 트리거하지만 그 이후의 패치는 AWS가 자동으로 적용합니다.
- **etcd 자동 백업**: AWS가 자동으로 etcd 스냅샷을 관리합니다.
- **고가용성**: 컨트롤 플레인은 multi-AZ로 배포되며, AWS가 SLA 99.95%를 보장합니다.
- **로깅 통합**: API Server, Audit, Authenticator, Controller Manager, Scheduler 로그를 CloudWatch Logs로 직접 전송할 수 있습니다.

```bash
# EKS 클러스터 생성 (eksctl 사용)
eksctl create cluster \
  --name my-eks-cluster \
  --region ap-northeast-2 \
  --version 1.30 \
  --vpc-cidr 10.0.0.0/16 \
  --without-nodegroup

# CloudWatch Logs 전송 활성화
aws eks update-cluster-config \
  --name my-eks-cluster \
  --logging '{"clusterLogging":[{"types":["api","audit","authenticator","controllerManager","scheduler"],"enabled":true}]}' \
  --region ap-northeast-2
```

### 2. 워커 노드 옵션

EKS는 워커 노드를 두 가지 방식으로 제공합니다.

| 항목 | EC2 노드 그룹 | Fargate |
|------|---------------|---------|
| 관리 책임 | 노드 OS, kubelet 업그레이드 | 완전 관리형 (Pod 단위) |
| 가격 | EC2 인스턴스 시간 | vCPU/메모리 시간 |
| Pod 밀도 | 인스턴스당 다수 | Pod당 microVM 1개 |
| GPU/Spot 지원 | 지원 | 미지원 |
| DaemonSet | 지원 | 미지원 (호환성 제한) |
| HostNetwork/HostPort | 지원 | 미지원 |

**Managed Node Groups**: AWS가 EC2 인스턴스 라이프사이클(생성, 업데이트, 종료, drain)을 관리합니다. AMI 업그레이드도 한 번의 API 호출로 가능합니다.

**Self-managed Node Groups**: 사용자가 직접 EC2 Auto Scaling Group을 관리합니다. 커스텀 AMI나 부트스트랩 스크립트가 필요한 경우에 유용합니다.

```bash
# Managed Node Group 생성
eksctl create nodegroup \
  --cluster my-eks-cluster \
  --name standard-workers \
  --node-type m6g.large \
  --nodes 3 \
  --nodes-min 1 \
  --nodes-max 10 \
  --managed \
  --region ap-northeast-2

# Fargate 프로파일 생성 (default 네임스페이스의 모든 Pod)
eksctl create fargateprofile \
  --cluster my-eks-cluster \
  --name fp-default \
  --namespace default \
  --region ap-northeast-2
```

### 3. IAM 인증과 RBAC

EKS는 두 가지 인증/인가 시스템을 결합합니다.

- **AWS IAM**: 클러스터 접근 자격 증명 (`aws eks update-kubeconfig`)
- **Kubernetes RBAC**: 네임스페이스/리소스 단위 권한 제어

또한 Pod에 IAM 권한을 부여하기 위한 두 가지 메커니즘이 있습니다.

**IRSA (IAM Roles for Service Accounts)**: ServiceAccount에 OIDC 기반으로 IAM Role을 매핑합니다. 2019년부터 표준이었으나 OIDC Provider 설정과 신뢰 정책 관리가 다소 복잡합니다.

**EKS Pod Identity (2023년 11월 출시)**: IRSA의 후속으로, OIDC 없이 EKS Pod Identity Agent가 자격 증명을 직접 제공합니다. 설정이 간단하고 신뢰 정책이 단순화되며, IAM Role 재사용성이 향상됩니다.

```bash
# IRSA용 OIDC Provider 연결
eksctl utils associate-iam-oidc-provider \
  --cluster my-eks-cluster \
  --approve

# IRSA로 ServiceAccount + IAM Role 생성
eksctl create iamserviceaccount \
  --name s3-reader \
  --namespace default \
  --cluster my-eks-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --approve

# Pod Identity Add-on 설치
aws eks create-addon \
  --cluster-name my-eks-cluster \
  --addon-name eks-pod-identity-agent \
  --region ap-northeast-2

# Pod Identity Association 생성
aws eks create-pod-identity-association \
  --cluster-name my-eks-cluster \
  --namespace default \
  --service-account s3-reader \
  --role-arn arn:aws:iam::123456789012:role/s3-reader-role \
  --region ap-northeast-2
```

### 4. EKS Add-ons

EKS Add-ons는 클러스터에 필수적인 컴포넌트를 AWS가 관리하는 형태로 설치/업그레이드/구성하는 기능입니다.

| Add-on | 역할 |
|--------|------|
| VPC CNI | Pod에 VPC IP 할당 |
| CoreDNS | 클러스터 내부 DNS 해석 |
| kube-proxy | iptables/IPVS 기반 서비스 라우팅 |
| EBS CSI Driver | EBS 볼륨 동적 프로비저닝 |
| EFS CSI Driver | EFS 파일 시스템 마운트 |
| AWS Load Balancer Controller | ALB/NLB 자동 프로비저닝 |
| Cluster Autoscaler / Karpenter | 노드 자동 확장 |
| Pod Identity Agent | Pod에 IAM 자격 증명 제공 |

```bash
# 사용 가능한 Add-on 목록
aws eks describe-addon-versions --kubernetes-version 1.30 \
  --query "addons[].addonName" --output table

# EBS CSI Add-on 설치
aws eks create-addon \
  --cluster-name my-eks-cluster \
  --addon-name aws-ebs-csi-driver \
  --addon-version v1.30.0-eksbuild.1 \
  --service-account-role-arn arn:aws:iam::123456789012:role/AmazonEKS_EBS_CSI_DriverRole \
  --region ap-northeast-2
```

### 5. EKS Auto Mode

2024년 re:Invent에서 발표된 EKS Auto Mode는 워커 노드, 네트워킹, 스토리지, 로드밸런서, DNS 등 운영 컴포넌트를 모두 AWS가 관리하는 모드입니다.

- **Karpenter 기반 노드 프로비저닝**: 워크로드 요구사항에 맞춰 EC2 인스턴스 타입을 자동 선택
- **노드 자동 패치**: 21일 주기로 자동 교체
- **통합 관리**: VPC CNI, EBS CSI, AWS Load Balancer Controller가 모두 사전 설치
- **추가 비용**: EC2 인스턴스 비용 + 12% 관리 수수료

EKS Auto Mode는 Kubernetes 운영 부담을 거의 0에 가깝게 줄여주며, 빠른 시작이 필요한 팀이나 운영 인력이 부족한 조직에 적합합니다.

```bash
# Auto Mode 클러스터 생성
aws eks create-cluster \
  --name auto-mode-cluster \
  --version 1.31 \
  --role-arn arn:aws:iam::123456789012:role/eks-cluster-role \
  --resources-vpc-config subnetIds=subnet-aaa,subnet-bbb \
  --compute-config enabled=true,nodePools=general-purpose,system \
  --kubernetes-network-config ipFamily=ipv4,elasticLoadBalancing={enabled=true} \
  --storage-config blockStorage={enabled=true} \
  --region ap-northeast-2
```

---

## 아키텍처

### EKS 클러스터 구성도

```
[AWS-managed VPC]                      [고객 VPC]
+------------------+                   +-------------------------+
| Control Plane    |                   |  Data Plane             |
|  - API Server    |  ENI(ENI Trunk)   |   +------------------+  |
|  - etcd          | <---------------> |   | Worker Node (EC2)|  |
|  - Scheduler     |                   |   |  - kubelet       |  |
|  - Controller    |                   |   |  - container     |  |
+------------------+                   |   |  - VPC CNI       |  |
                                       |   +------------------+  |
                                       |   +------------------+  |
                                       |   | Fargate Pod       |  |
                                       |   +------------------+  |
                                       +-------------------------+
```

1. **컨트롤 플레인**: AWS가 별도 VPC에서 운영하며, 사용자는 EKS API를 통해서만 접근합니다.
2. **ENI Trunk 또는 Cross-account ENI**: 컨트롤 플레인이 워커 노드와 통신하기 위해 고객 VPC에 ENI를 생성합니다.
3. **워커 노드**: 사용자 VPC 내 EC2 또는 Fargate microVM에 Pod가 배포됩니다.

### VPC CNI 네트워킹

기본 네트워크 플러그인인 AWS VPC CNI는 각 Pod에 VPC IP를 직접 할당합니다.

- **IP 할당**: ENI당 IP 풀을 미리 확보(`WARM_IP_TARGET`, `WARM_ENI_TARGET`)
- **Security Groups for Pods**: Pod 단위로 SG 부착 가능 (`SecurityGroupPolicy` CRD)
- **Prefix Delegation**: /28 prefix를 ENI에 할당하여 Pod 밀도 16배 향상
- **대안 CNI**: Calico (NetworkPolicy 강화), Cilium (eBPF 기반)

```yaml
# Security Groups for Pods 예시
apiVersion: vpcresources.k8s.aws/v1beta1
kind: SecurityGroupPolicy
metadata:
  name: db-client-sg
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: db-client
  securityGroups:
    groupIds:
      - sg-0a1b2c3d4e5f67890
```

### 스토리지 통합

| CSI Driver | 스토리지 유형 | 특징 |
|------------|---------------|------|
| EBS CSI | 블록 스토리지 (RWO) | gp3, io2 동적 프로비저닝 |
| EFS CSI | NFS 파일 시스템 (RWX) | 다중 Pod 동시 마운트 |
| FSx CSI | Lustre / OpenZFS / NetApp | 고성능 워크로드 |
| S3 Mountpoint CSI | S3 버킷 마운트 | 읽기 중심 워크로드 |

```yaml
# StorageClass 예시 (gp3)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
```

---

## 실전 사용

### 1. 클러스터 구축 후 첫 Pod 배포

```bash
# kubeconfig 갱신
aws eks update-kubeconfig --name my-eks-cluster --region ap-northeast-2

# 클러스터 상태 확인
kubectl get nodes
kubectl get pods -A

# 샘플 Deployment 배포
kubectl create deployment nginx --image=nginx:1.27 --replicas=3
kubectl expose deployment nginx --port=80 --type=LoadBalancer
```

### 2. Karpenter로 노드 자동 확장

Karpenter는 Cluster Autoscaler보다 빠르고 인스턴스 타입 선택이 유연합니다(2024년 v1.0 GA).

```yaml
# NodePool 정의
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      nodeClassRef:
        name: default
        group: karpenter.k8s.aws
        kind: EC2NodeClass
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64", "arm64"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["spot", "on-demand"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["m", "c", "r"]
  limits:
    cpu: 1000
  disruption:
    consolidationPolicy: WhenUnderutilized
```

### 3. ALB Ingress 구성

AWS Load Balancer Controller가 Ingress 리소스를 ALB로 변환합니다.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:ap-northeast-2:123456789012:certificate/abc123
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
spec:
  ingressClassName: alb
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-service
                port:
                  number: 80
```

---

## 가격/한도

### 가격 모델

| 항목 | 가격 (us-east-1) |
|------|------------------|
| 컨트롤 플레인 | 시간당 $0.10 (월 약 $73) |
| EKS Auto Mode 관리 수수료 | EC2 비용의 12% |
| Fargate (vCPU) | 시간당 $0.04048 |
| Fargate (메모리 GB) | 시간당 $0.004445 |
| EKS Extended Support | 시간당 $0.50 (4-26개월) |
| EKS Anywhere (자체 구독) | 별도 구독 |

표준 지원 기간 외에 최대 26개월간 사용 가능한 Extended Support가 있으며, 시간당 $0.50의 추가 비용이 발생합니다(컨트롤 플레인 비용의 5배).

### 주요 한도

| 항목 | 기본 한도 |
|------|-----------|
| 클러스터 수 (계정/리전) | 100 |
| 노드 그룹 수 (클러스터당) | 30 |
| Managed Node Group의 노드 수 | 450 (1.30+) / 1000 (Karpenter) |
| Fargate 프로파일 (클러스터당) | 100 |
| Fargate 프로파일 selector | 5 |
| Pod 수 (노드당) | 인스턴스 타입별 ENI/IP 한도 |

```bash
# 인스턴스 타입별 최대 Pod 수 확인
kubectl get nodes -o custom-columns=NAME:.metadata.name,POD_LIMIT:.status.allocatable.pods
```

---

## Best Practice

### 권장 패턴

1. **Pod Identity 우선 사용**: 신규 클러스터는 IRSA보다 Pod Identity로 시작하여 운영 단순화
2. **Karpenter로 노드 관리**: Cluster Autoscaler 대비 빠른 응답과 비용 최적화
3. **EKS Add-ons 표준화**: 핵심 컴포넌트는 Self-managed 대신 Add-on으로 설치
4. **etcd 우회 액세스 차단**: 컨트롤 플레인 엔드포인트는 Private 또는 Hybrid로 설정
5. **로깅 통합**: 5종 컨트롤 플레인 로그를 CloudWatch Logs로 활성화 후 보존 정책 적용
6. **GitOps 도입**: ArgoCD 또는 Flux로 선언적 배포 표준화
7. **GuardDuty for EKS Protection**: 런타임 위협 탐지 활성화

### 안티 패턴

1. **인스턴스 IAM Role에 과도한 권한 부여**: kube2iam, kiam 같은 레거시 솔루션은 폐기하고 IRSA/Pod Identity 사용
2. **Public Endpoint만 사용**: 컨트롤 플레인을 인터넷에 노출하면 보안 리스크 증가
3. **VPC CNI 단일 IP 모드**: Prefix Delegation 미적용 시 작은 인스턴스에서 Pod 밀도 부족
4. **노드 OS 직접 패치**: Managed Node Group에서는 AWS API로 업데이트해야 일관성 유지
5. **수동 kubectl apply**: 변경 추적 불가 - GitOps 또는 Terraform으로 일관성 확보

```yaml
# 권장: PodDisruptionBudget으로 가용성 보호
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: app-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: critical-service
```

---

## 관련 서비스

| 서비스 | 관계 |
|--------|------|
| Amazon ECR | 컨테이너 이미지 저장소 |
| AWS Fargate | Pod를 서버리스로 실행 |
| Amazon EBS / EFS / FSx | 영구 스토리지 |
| AWS Load Balancer Controller | ALB/NLB 자동 프로비저닝 |
| Amazon Route 53 | 외부 DNS 통합 (ExternalDNS) |
| AWS Secrets Manager / Parameter Store | 시크릿 동기화 (CSI Secret Store) |
| Amazon CloudWatch Container Insights | Pod/노드 메트릭 수집 |
| AWS App Mesh | 서비스 메시 (현재 deprecated) |
| AWS PrivateLink | EKS API 프라이빗 액세스 |
| Karpenter | 차세대 노드 오토스케일러 |
| AWS Distro for OpenTelemetry (ADOT) | 통합 관측성 |

---

## 관련 문서

- [[aws-fargate-서버리스-컨테이너-실행-개요|AWS Fargate]] - EKS 워커 노드의 서버리스 옵션
- [[amazon-elastic-container-service-amazon-ecs|Amazon ECS]] - AWS 자체 컨테이너 오케스트레이터, EKS와 비교 대상
- [[aws-lambda-개요-및-실전-활용-가이드|AWS Lambda]] - 함수형 서버리스, 짧은 워크로드에 적합
- [[amazon-ebs-elastic-block-store-개요|Amazon EBS]] - EBS CSI Driver를 통해 영구 볼륨 제공
- [[amazon-efs-elastic-file-system-개요|Amazon EFS]] - 다중 Pod 공유 스토리지
