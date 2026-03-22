---
title: Auto Scaling Group(ASG)
slug: "auto-scaling-groupasg"
category: cloud
tags: ["asg", "auto-scaling", "aws", "cloudwatch", "ec2", "elastic-load-balancer", "predictive-scaling", "scaling-policies", "scheduled-scaling"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:05.056248+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - Auto Scaling
---
## 📌 Auto Scaling Group이란?

- 실제 서비스에서는 부하가 시간에 따라 변동됩니다.
- 클라우드에서는 **EC2 인스턴스를 빠르게 생성하거나 제거**할 수 있습니다.

### 🎯 ASG의 목적

- **Scale Out**: 증가하는 부하에 맞춰 EC2 인스턴스 추가
- **Scale In**: 감소하는 부하에 따라 EC2 인스턴스 제거
- **Min/Max 개수 유지**: 설정된 범위 내에서 인스턴스 수 유지
- **로드 밸런서에 자동 등록**
- **비정상 인스턴스 자동 교체**

> 💡 ASG 자체는 무료이며, 인스턴스 사용에 따른 비용만 발생합니다.

---

## 🧱 Auto Scaling Group 구조

![](/media/posts/imported/aws/Pasted%20image%2020250706194134.png)

```plaintext
[최소 용량] ---- [원하는 용량] ---- [최대 용량]
        ←      Auto Scaling Group      →
              [EC2 인스턴스들]
```

- 필요 시 EC2 인스턴스를 **동적으로 Scale Out** 또는 Scale In 합니다.

---

## 🔄 Load Balancer와 함께 쓰는 ASG

![](/media/posts/imported/aws/Pasted%20image%2020250706194148.png)

- 사용자의 요청 → **Elastic Load Balancer (ELB)** → ASG 내 EC2 인스턴스로 전달됩니다.
- ELB는 인스턴스의 **Health 상태를 확인**할 수 있습니다.

---

## ⚙️ ASG 구성요소 (Attributes)

### 🧩 Launch Template

![](/media/posts/imported/aws/Pasted%20image%2020250706194230.png)

- AMI + Instance Type
- EC2 User Data
- EBS Volume
- Security Groups
- SSH Key Pair
- IAM Role
- Subnet & Network 정보
- Load Balancer 정보

### 📌 그 외 속성

- Min Size / Max Size / Initial Capacity
- Scaling Policies (확장 정책)

---

## 📈 CloudWatch 기반 Auto Scaling

![](/media/posts/imported/aws/Pasted%20image%2020250706194303.png)

- **CloudWatch Alarm**을 기반으로 ASG 크기를 조정할 수 있습니다.
- 예시 지표: `Average CPU`, 사용자 정의 지표(Custom Metric)
- 정책 종류:
    - **Scale-out**: 인스턴스 추가
    - **Scale-in**: 인스턴스 제거

---

## 📊 Scaling 정책 유형

### 1. Dynamic Scaling

#### 🔹 Target Tracking Scaling

- 설정이 간단하며, 목표값을 기준으로 유지합니다.
- 예: 평균 CPU 사용률을 40%로 유지

#### 🔹 Step Scaling

- 특정 조건을 만족할 때 정해진 수만큼 확장/축소합니다.
- 예: CPU > 70% → +2, CPU < 30% → -1

### 2. Scheduled Scaling

- 시간 기반으로 자동 확장/축소를 설정합니다.
- 예: 금요일 오후 5시에 최소 용량을 10으로 증가

### 3. Predictive Scaling

- 과거 부하를 기반으로 예측하여 미래 부하에 **선제적으로 대응**합니다.
- 일정에 따라 자동 확장 예약을 수행합니다.

---

## 📌 유용한 지표 (Metrics)

|지표|설명|
|---|---|
|**CPUUtilization**|평균 CPU 사용률|
|**RequestCountPerTarget**|인스턴스당 요청 수 안정 유지|
|**NetworkIn/Out**|네트워크 기반 애플리케이션용|
|**Custom Metric**|CloudWatch로 전송한 사용자 지표|

---

## 🧊 Scaling Cooldowns

- **확장 작업 후 일정 시간(기본 300초)** 동안 추가 확장/축소를 방지합니다.
- 이유: **메트릭 안정화 대기**를 위해서입니다.
- 팁: 준비된 AMI를 사용하면 인스턴스 생성 시간을 단축할 수 있습니다.

```plaintext
Scaling 발생
   ↓
Cooldown 적용 여부 확인
   ↓             ↓
 Yes → 무시        No → Launch or Terminate Instance
```

---

## ✅ 요약

|항목|설명|
|---|---|
|구성 요소|Launch Template, Capacity 범위, Scaling Policy 등|
|스케일링 방식|Dynamic, Scheduled, Predictive|
|트리거|CloudWatch Alarm, 시간 조건 등|
|통합 기능|ELB와 연결 가능, Health Check, Cooldown 지원|
|과금|ASG는 무료, EC2 인스턴스 사용량만 과금|
