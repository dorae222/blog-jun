---
title: AWS Transit Gateway (TGW)
slug: "aws-transit-gateway-tgw"
category: cloud
tags: ["aws", "aws-cloud-wan", "aws-ram", "direct-connect", "networking", "site-to-site-vpn", "tgw", "transit-gateway", "vpc", "vpc-peering"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.566177+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
---
aliases:
  - TGW
  - AWS TGW
  - 전송 게이트웨이
---
> **NOTE:**
> - Transit Gateway를 통해 각 VPC 또는 VPN 간의 트래픽을 라우팅합니다.
> - 복잡한 피어링 관계를 제거하여 네트워크를 간소화합니다.
> - ![](/media/posts/imported/aws/Pasted%20image%2020250704100254.png)

**AWS Transit Gateway**는 여러 Amazon VPC, 온프레미스 네트워크, VPN, Direct Connect 등을 **하나의 중앙 허브를 통해 연결**할 수 있도록 해주는 **완전관리형 네트워크 라우팅 서비스**입니다.

---

## 🧠 AWS Transit Gateway란?

> **AWS Transit Gateway (TGW)**는 **다수의 VPC, 온프레미스 네트워크, AWS 계정 간 네트워크 연결을 중앙 집중화**하고,
> 라우팅을 단순화하며 확장성을 높이기 위해 사용하는 **공유 허브(hub)** 역할을 합니다.

---

## 🧱 전통적인 문제점 vs Transit Gateway

기존에는 VPC 간 통신을 위해 다음 방법을 사용해야 했습니다:

- **VPC Peering**: VPC 1 ↔ VPC 2 ↔ VPC 3 등 **N:1 방식** (관리 복잡, 라우팅 어려움)

> 10개 VPC 간 모두 연결하려면 **45개의 피어링이 필요**합니다.

**Transit Gateway**를 사용하면:

> 모든 VPC가 **하나의 Transit Gateway에 연결**되므로
> → **모든 VPC 간 통신 가능**하며 관리가 단순해집니다.

---

## 📌 주요 기능

|기능|설명|
|---|---|
|**중앙 허브**|여러 VPC, VPN, Direct Connect를 중앙에서 연결|
|**스케일링**|수천 개의 VPC와 연결 가능 (확장성 뛰어남)|
|**라우팅 제어**|세부적인 **route table 분리**로 보안성과 유연성 확보|
|**멀티 리전 지원**|리전 간 TGW 피어링으로 **글로벌 네트워크 허브 구축 가능**|
|**공유 가능 (RAM)**|여러 AWS 계정 간 공유 가능 (AWS Resource Access Manager)|

---

## 🎯 사용 예시

- 대기업이 계열사마다 각각의 AWS 계정과 VPC를 운영 중일 때
- 온프레미스 네트워크를 AWS와 연결하고, 동시에 여러 VPC 간에 보안 통신이 필요할 때
- VPN, Direct Connect, VPC를 **하나의 경로로 통합**하고 싶을 때

---

## 🔁 Transit Gateway vs VPC Peering vs Cloud WAN

|항목|Transit Gateway|VPC Peering|AWS Cloud WAN|
|---|---|---|---|
|연결 구조|**허브 앤 스포크**|**N:N 직접 연결**|글로벌 SD-WAN|
|확장성|수천 개 VPC 가능|수십 개 이상은 비효율|글로벌 수준|
|멀티 리전|✅ TGW 피어링|❌ 불가능|✅ 전역 지원|
|관리 복잡도|낮음|높음|복잡하지만 고급 기능|

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**AWS Transit Gateway (TGW)**|
|용도|**다수의 VPC와 온프레미스 네트워크를 하나의 허브로 연결**|
|장점|**확장성, 단순성, 라우팅 제어, 멀티 리전 지원**|
|대상|**복잡한 네트워크 아키텍처**, 대규모 환경에서 필수|

- AWS RAM
- Site-to-Site VPN ECMP
