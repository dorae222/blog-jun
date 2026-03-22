---
title: "🌐 BGP란?"
slug: "-bgp란"
category: cloud
tags: ["asn", "aws", "bgp", "cloud-networking", "direct-connect", "networking", "routing", "site-to-site-vpn", "transit-gateway"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.292519+00:00"
---

## 🌐 BGP란?

> **BGP (Border Gateway Protocol)**는
> 인터넷 또는 대규모 네트워크 간에 **라우팅 정보를 교환**하기 위한 **동적 라우팅 프로토콜**입니다.

즉, **어떤 경로(네트워크 경로)를 통해 목적지 IP에 도달할지 결정하는 규칙을 외부 네트워크와 교환하는 데 사용**됩니다.

---

## 📡 BGP의 핵심 특징

|항목|설명|
|---|---|
|**라우팅 목적**|네트워크 간 경로 정보 교환 (인터넷의 "우편배달 경로"와 같음)|
|**동적 라우팅**|연결된 네트워크들이 자동으로 최적 경로를 결정|
|**경로 선택 기준**|홉 수, 경로 정책, 우선순위 등|
|**대상 환경**|주로 **ISP, 기업 네트워크, 클라우드 네트워크 간 통신**|

---

## 🏗️ AWS에서의 BGP 사용 예시

- **Site-to-Site VPN** 연결 시  
    `Customer Gateway ↔ Virtual Private Gateway` 간에 BGP 사용  
    → **온프레미스와 AWS 간 경로를 자동으로 학습/추적**
    
- **AWS Direct Connect** 연결  
    → **사설 연결**을 위한 BGP 기반 경로 교환
    
- **AWS Transit Gateway** 연결  
    → 여러 VPC 및 VPN 간 자동 라우팅 구성 가능
    
---

## 📦 BGP의 구성 요소

|구성 요소|설명|
|---|---|
|**ASN (Autonomous System Number)**|BGP 네트워크의 고유 식별자|
|**Prefix**|특정 네트워크 블록 (예: 10.0.0.0/16)|
|**Path**|네트워크 경로 (어떤 ASN들을 거쳐 목적지에 도달하는지)|
|**Neighbor**|서로 라우팅 정보를 교환하는 BGP 장비 쌍|

---

## ✅ BGP vs 정적 라우팅

|항목|BGP (동적)|정적 라우팅|
|---|---|---|
|관리|자동 (경로 학습)|수동으로 경로 지정|
|확장성|대규모 네트워크에 적합|소규모 구성에 적합|
|회복성|경로 장애 시 자동 대체 가능|수동 수정 필요|
|AWS 권장|VPN, DX, TGW 등에서 BGP 선호||

---

## 📝 예: AWS VPN에서 BGP 사용

```text
Customer Gateway ASN: 65001  
AWS Virtual Private Gateway ASN: 64512

→ AWS는 BGP를 통해 온프레미스에 10.0.0.0/16 경로를 알리고,  
   고객 네트워크는 192.168.0.0/16 경로를 AWS에 알림.
```

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**BGP (Border Gateway Protocol)**|
|역할|**네트워크 간 경로 정보 자동 교환**|
|AWS 활용|Site-to-Site VPN, Direct Connect, Transit Gateway|
|이점|확장성, 자동성, 장애 복구성 우수|
