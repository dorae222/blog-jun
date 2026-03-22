---
title: Amazon Elastic Container Service (Amazon ECS)
slug: "amazon-elastic-container-service-amazon-ecs"
category: cloud
tags: ["amazon-ecs", "aws", "cloud", "containers", "devops", "ec2", "fargate", "orchestration"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.138046+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - ECS
  - Amazon ECS
---
**Amazon Elastic Container Service (Amazon ECS)**는 AWS에서 제공하는 **완전관리형 컨테이너 오케스트레이션 서비스**로, Docker 컨테이너를 손쉽게 실행·중지·관리할 수 있도록 설계된 서비스입니다. Kubernetes와 같은 복잡한 오케스트레이터 없이도 컨테이너 기반 애플리케이션을 배포하고 운영할 수 있습니다.

---

## 🧱 핵심 개념

### 1. **클러스터 (Cluster)**

ECS에서 컨테이너가 실행되는 논리적 그룹입니다. 클러스터는 **Fargate**(서버리스) 또는 **EC2**(직접 관리하는 노드) 모드 중 하나로 운영할 수 있습니다.

### 2. **태스크 정의 (Task Definition)**

컨테이너 실행에 필요한 설정을 담은 JSON 템플릿입니다. 사용할 이미지, 노출할 포트, 메모리/CPU 리소스, 환경 변수 등 실행 관련 정보를 정의합니다.

### 3. **태스크 (Task)**

실제로 실행되는 컨테이너의 집합입니다. 태스크는 태스크 정의를 기반으로 생성되며, ECS가 이를 스케줄링하여 실행합니다.

### 4. **서비스 (Service)**

태스크의 **지속적 실행**과 자동 확장/축소를 관리하는 ECS 리소스입니다. 예를 들어 항상 3개의 태스크를 유지하도록 설정할 수 있습니다.

---

## 🚀 두 가지 실행 모드

|모드|설명|특징|
|---|---|---|
|**Fargate**|AWS가 인프라를 완전히 관리|서버리스, 더 간편, 비용은 약간 높을 수 있음|
|**EC2**|사용자가 EC2 인스턴스를 직접 관리|더 많은 제어 권한, 비용 절감 가능성|

### Fargate
![](Pasted image 20250728164434.png)

### EC2

![](Pasted image 20250728164559.png)
---

## 🛠️ ECS vs EKS vs Docker

|항목|ECS|EKS (Kubernetes)|Docker 자체 사용|
|---|---|---|---|
|관리 편의성|가장 간단|복잡함|중간|
|학습 난이도|낮음|높음|낮음|
|오토스케일링|지원|지원 (복잡)|수동 설정 필요|
|AWS 통합|매우 뛰어남|뛰어남|낮음|

---

## 📦 예시: ECS 서비스 실행 흐름

1. **Docker 이미지 빌드 및 ECR에 푸시**

2. **태스크 정의 생성** (image, CPU, port 등 명시)

3. **클러스터 생성**

4. **서비스 생성** (태스크 개수, 로드밸런서 연결 등)

5. **Fargate 또는 EC2에 배포**

---

## 📈 장점

- **서버리스 옵션 (Fargate)**: 인프라 관리가 필요 없음

- **높은 AWS 통합성**: IAM, CloudWatch, ALB 등과의 연동이 용이함

- **자동 확장 및 로드밸런싱**

- **CI/CD 파이프라인과의 연계 용이** (예: CodePipeline, CodeDeploy)

---

## 📚 참고 자료

- [공식 문서](https://docs.aws.amazon.com/ko_kr/AmazonECS/latest/developerguide/Welcome.html)

- [ECS vs EKS 비교](https://aws.amazon.com/ecs/eks/)

- [AWS Fargate란?](https://aws.amazon.com/fargate/)
