---
title: AWS Direct Connect Gateway (DX Gateway) 개요
slug: "aws-direct-connect-gateway-dx-gateway-개요"
category: cloud
tags: ["aws", "aws-direct-connect", "cloud-networking", "direct-connect-gateway", "dx-gateway", "multi-region", "networking", "transit-gateway", "vpc"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:03.723562+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - DX Gateway
  - Direct Connect Gateway
---

**AWS Direct Connect Gateway (DX Gateway)**는 여러 AWS 리전의 VPC와 **중앙에서 직접 연결**할 수 있게 해주는 **글로벌 라우팅 허브 역할**을 하는 리소스입니다.

---

## 🌐 Direct Connect Gateway란?

> **Direct Connect Gateway (DX Gateway)**는  
> 하나의 AWS Direct Connect 연결을 사용해  
> **여러 리전(VPC)과 연결할 수 있는 글로벌 게이트웨이**입니다.
> 
> 즉, **Direct Connect와 다양한 리전의 VPC를 중앙에서 라우팅**할 수 있게 해주는 **확장성 높은 허브**입니다.

---

## 🖼️ 아키텍처 개념

```text
         [On-premises network]
                  │
        (Direct Connect physical connection)
                  │
      [Direct Connect Gateway (DXGW)]
             ╱             ╲
   [VPC in Region A]     [VPC in Region B]
   (via VGW)             (via VGW)
```

---

## 🧩 주요 특징

|기능|설명|
|---|---|
|**멀티 리전 지원**|Direct Connect는 한 리전에 연결되지만, DX Gateway를 사용하면 **다른 리전의 VPC와도 연결 가능**|
|**중앙 집중식 관리**|여러 VPC 간의 **라우팅 관리를 단순화**|
|**글로벌 라우팅 허브**|Direct Connect 하나로 미국, 아시아 등 **여러 리전의 AWS 리소스를 연결** 가능|
|**보안 격리**|VPC 간 직접 통신 불가 → 네트워크 격리 가능|

---

## 🎯 언제 사용하나요?

|상황|사용 이유|
|---|---|
|**멀티 리전 운영**|서울 리전에 연결된 Direct Connect로 도쿄, 싱가포르 VPC도 사용해야 할 때|
|**VPC 간 독립 유지**|VPC 간 통신은 막고, 온프레미스 ↔ 각 VPC 연결만 허용하고 싶을 때|
|**라우팅 단순화**|Direct Connect 연결 하나만 관리하면서 여러 VPC와 연결하고 싶을 때|

---

## 🔄 구성 흐름 요약

1. AWS에서 **Direct Connect Gateway 생성**
    
2. **Virtual Private Gateway (VGW)**를 각 VPC에 연결
    
3. DX Gateway와 VGW 간의 **연결(Association)** 생성
    
4. 라우팅 테이블에 경로 추가
    

---

## 🔧 DX Gateway vs Transit Gateway

|항목|Direct Connect Gateway|Transit Gateway|
|---|---|---|
|주 목적|온프레미스 ↔ VPC 연결 (리전 간)|VPC ↔ VPC / VPC ↔ VPN 등 내부 통신|
|리전 지원|**글로벌** (멀티 리전 연결 지원)|단일 리전 (지역 제한, 다리 연결 필요)|
|네트워크 통합|온프레미스 중심|AWS 내부 중심|
|라우팅 제어|VGW 기반|TGW 라우팅 테이블 기반|

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**Direct Connect Gateway (DX Gateway)**|
|역할|**하나의 Direct Connect 연결로 여러 리전의 VPC와 연결**|
|장점|글로벌 확장, 라우팅 단순화, 보안 분리|
|필수 구성|Direct Connect 연결, DX Gateway, VPC의 Virtual Private Gateway(VGW)|
