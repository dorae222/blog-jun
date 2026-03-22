---
title: Virtual Interface (VIF)
slug: "virtual-interface-vif"
category: cloud
tags: ["aws", "aws-direct-connect", "bgp", "networking", "private-vif", "public-vif", "transit-vif", "vif", "virtual-interface"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.039350+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - Virtual Interface
  - VIF
---

**Virtual Interface (VIF)**는 **AWS Direct Connect 연결에서 AWS 리소스와 실제 통신을 가능하게 해주는 논리적 인터페이스**입니다. 즉, **Direct Connect 물리 회선을 통해 어떤 AWS 서비스에 연결할지를 정의**하는 구성 요소입니다.

---

## 🧩 Virtual Interface (VIF)란?

> **VIF (Virtual Interface)**는  
> **Direct Connect 물리 연결**을 통해  
> **Amazon VPC 또는 퍼블릭 AWS 서비스(S3, DynamoDB 등)와 연결하는 논리적 통신 경로**입니다.

하나의 Direct Connect 회선에 **여러 개의 VIF를 구성**하여  
**다양한 AWS 서비스 또는 VPC와 동시에 연결**할 수 있습니다.

---

## 🛠️ VIF의 주요 종류

|VIF 종류|설명|사용 예시|
|---|---|---|
|**Private VIF**|VPC 내의 리소스와 연결 (EC2, RDS 등)|온프레미스 ↔ VPC 내부 통신|
|**Public VIF**|AWS의 퍼블릭 서비스(S3, DynamoDB 등)와 직접 연결|온프레미스 ↔ S3, CloudWatch 등|
|**Transit VIF**|Transit Gateway를 통해 여러 VPC에 연결|다수의 VPC와 중앙 통합 연결|

---

## 🖼️ 구성 구조 예시

```
[온프레미스 네트워크]
        ⇅
[Direct Connect 물리 회선]
        ⇅
     [Virtual Interface (VIF)]
        ⇅
[Amazon VPC or AWS 서비스]
```

---

## 📦 VIF 생성 시 필요한 정보

|항목|설명|
|---|---|
|VLAN ID|전용 네트워크 태그 (802.1Q)|
|BGP ASN|BGP 라우팅을 위한 ASN 번호|
|IP 주소 범위|양쪽 인터페이스 간 통신용 주소|

---

## 🔍 각 VIF 타입 비교

|항목|Private VIF|Public VIF|Transit VIF|
|---|---|---|---|
|대상|VPC (EC2 등)|S3, CloudWatch 등|여러 VPC 연결용|
|용도|하이브리드 클라우드|퍼블릭 서비스에 대한 전용 접근|확장성 높은 중앙 허브|
|사용 서비스|EC2, RDS, EKS 등|S3, SNS, DynamoDB 등|Transit Gateway 대상|
|VPC 연결|1:1|없음|N:1 (다수의 VPC)|

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**Virtual Interface (VIF)**|
|위치|AWS Direct Connect의 **논리적 연결 지점**|
|종류|**Private / Public / Transit**|
|역할|온프레미스 네트워크를 AWS 리소스와 **논리적으로 연결**|
|특징|하나의 Direct Connect에 여러 VIF를 구성 가능|
