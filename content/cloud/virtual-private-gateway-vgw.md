---
title: Virtual Private Gateway (VGW)
slug: "virtual-private-gateway-vgw"
category: cloud
tags: ["aws", "bgp", "cloudwatch", "customer-gateway", "site-to-site-vpn", "transit-gateway", "virtual-private-gateway", "vpc", "vpn"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.045894+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---

---
aliases:
  - VGW
  - VPGW
---
**Virtual Private Gateway (VGW)**는 **AWS VPC와 외부 네트워크(예: 온프레미스 데이터 센터)** 간에 **암호화된 VPN 연결을 생성하는 AWS 측 엔드포인트**입니다.

---

## 🔐 Virtual Private Gateway (VGW)란?

> **Virtual Private Gateway**는 AWS에서 제공하는 **가상 네트워크 장비**로,
> **VPC와 외부 네트워크(온프레미스, 타 클라우드 등)** 간에 **Site-to-Site VPN 연결을 생성할 때**
> **AWS 쪽 터널 종단점 역할**을 수행합니다.

즉, 온프레미스 쪽의 VPN 장비(**Customer Gateway**)와 연결되는 **AWS 측 관문(Gateway)**입니다.
- Route Propagation
- ICMP

---

## 🧱 구성도 예시

```
[온프레미스 라우터]  ←→  [Customer Gateway] 
                                 ↑
                         암호화된 VPN 터널 (IPSec)
                                 ↓
                       [Virtual Private Gateway]
                                 ↓
                            [VPC 내부 자원]
```

---

## 🛠️ 주요 특징

|항목|설명|
|---|---|
|**AWS 측 VPN 엔드포인트**|VPC와 Site-to-Site VPN을 연결하는 **필수 구성요소**|
|**고가용성 기본 제공**|두 개의 VPN 터널 자동 생성 (멀티 AZ 내 이중화)|
|**라우팅 지원**|정적 또는 동적 라우팅 (BGP) 구성 가능|
|**VPN 연결당 1개 필요**|VPN 연결을 만들기 위해 **VGW 1개와 CGW 1개** 필요|
|**CloudWatch 모니터링 가능**|터널 상태, 패킷 수 등 지표 확인 가능|

---

## 💡 언제 사용하는가?

|상황|설명|
|---|---|
|**온프레미스 ↔ VPC 연결**|보안 터널을 통해 하이브리드 클라우드 구현|
|**리전 간 VPN 구성**|다른 AWS 리전 간 보안 통신|
|**테스트 또는 비용 절감용**|Direct Connect 대안 또는 백업용|

---

## 🆚 Transit Gateway와 차이점

|항목|Virtual Private Gateway (VGW)|AWS Transit Gateway (TGW)|
|---|---|---|
|연결 구조|**1:1 연결 (VPC 전용)**|**N:1 허브 앤 스포크 모델**|
|확장성|제한적|고확장성 (수십 VPC 연결 가능)|
|설정 복잡도|낮음|높음 (복잡한 라우팅 지원)|
|추천 사용|단일 VPC, 소규모 하이브리드|다수의 VPC 및 외부 네트워크 연결|

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**Virtual Private Gateway (VGW)**|
|역할|**AWS VPC와 외부 네트워크 간 VPN 연결의 AWS 측 엔드포인트**|
|암호화|**IPSec 기반 Site-to-Site VPN**|
|구성 필수요소|**Customer Gateway + Virtual Private Gateway + VPN Connection**|
|고가용성|두 개의 터널 기본 제공 (이중화)|