---
title: Customer Gateway (CGW)
slug: "customer-gateway-cgw"
category: cloud
tags: ["aws", "bgp", "cloud", "customer-gateway", "ipsec", "networking", "site-to-site-vpn", "transit-gateway", "virtual-private-gateway", "vpc"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.474479+00:00"
---

---
Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
---
aliases:
  - CGW
---
**Customer Gateway (CGW)**는 **온프레미스 네트워크 또는 외부 네트워크 쪽의 VPN 엔드포인트를 AWS에 등록하는 객체**입니다.  
즉, **AWS VPC와 고객 네트워크 간의 Site-to-Site VPN 연결**을 설정하기 위해
**고객 쪽 장비(라우터, 방화벽, 가상 어플라이언스 등)를 대표하는 AWS 리소스**입니다.

---

## 🧩 Customer Gateway란?

> **Customer Gateway (CGW)**는 AWS에서 **온프레미스 네트워크의 VPN 디바이스**를 나타내는 논리적 리소스입니다.  
> VPN 연결을 생성할 때 AWS는 이 CGW 정보(IP 주소, 라우팅 타입 등)를 참조하여
> **AWS 측 Virtual Private Gateway (VGW)** 또는 **Transit Gateway**와 **암호화된 터널(IPSec)**을 구성합니다.

---

## 🔧 구성 요소

|항목|설명|
|---|---|
|**온프레미스 장비**|라우터, 방화벽, VPN 어플라이언스 등|
|**정적 IP 주소**|공인 IP 주소 (고정 IP)|
|**라우팅 옵션**|BGP(동적) 또는 정적 라우팅|
|**CGW 리소스**|AWS에 등록되어 VPN 연결의 대상이 됨|

---

## 🖼️ 동작 예시

```
[온프레미스 라우터] ←▶︎ [Customer Gateway]
                              ⇅ 암호화 터널 (IPSec)
                        [Virtual Private Gateway]
                              ↓
                            [AWS VPC]
```

---

## 🔐 Customer Gateway에 포함되는 정보

- 공인 IP 주소 (정적 IP 필수)
    
- BGP ASN (동적 라우팅 시)
    
- 디바이스 타입 (선택 사항)
    
- 라우팅 옵션 (정적 또는 BGP)
    

---

## 🛠️ 설정 흐름 요약

1. **온프레미스에 VPN 디바이스 준비** (정적 IP 필요)
    
2. AWS에서 `Customer Gateway` 리소스 생성
    
3. AWS에서 `Virtual Private Gateway` 연결
    
4. 둘을 연결하여 `VPN Connection` 생성
    
5. AWS에서 생성한 **구성 파일(Configuration File)**을 온프레미스 장비에 적용
    

---

## 🆚 Customer Gateway vs Virtual Private Gateway

|항목|Customer Gateway (CGW)|Virtual Private Gateway (VGW)|
|---|---|---|
|위치|고객(온프레미스) 측|AWS 측|
|역할|VPN의 외부 네트워크 엔드포인트|VPN의 VPC 엔드포인트|
|관리 주체|고객 또는 외부|AWS|
|필수 조건|정적 공인 IP 필요|없음|

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**Customer Gateway (CGW)**|
|역할|**AWS가 온프레미스 VPN 장비와 터널을 구성하기 위한 정보 객체**|
|필요 조건|**정적 공인 IP 주소**, 라우팅 정보(BGP/Static)|
|관련 구성|반드시 **VPN Gateway(VGW)** 또는 **Transit Gateway**와 연결됨|
|사용 목적|**Site-to-Site VPN 연결을 위한 고객측 엔드포인트 등록**|
