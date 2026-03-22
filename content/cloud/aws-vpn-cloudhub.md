---
title: AWS VPN CloudHub
slug: "aws-vpn-cloudhub"
category: cloud
tags: ["aws", "aws-vpn-cloudhub", "bgp", "cloud-networking", "customer-gateway", "ipsec", "site-to-site-vpn", "vgw", "vpn"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:04.592477+00:00"
---

**AWS VPN CloudHub**는 여러 개의 온프레미스 지사를 **AWS를 중심으로 서로 연결할 수 있도록** 해주는  
**Site-to-Site VPN 기반의 허브 앤 스포크(Hub-and-Spoke) 아키텍처**입니다.

---

## ☁️ AWS VPN CloudHub란?

> **AWS VPN CloudHub**는  
> **여러 지사나 데이터 센터 간을 AWS를 경유하는 VPN 터널로 상호 연결**하여  
> **지사 간 통신을 가능하게 하는 구조**입니다.

각 지사는 AWS Virtual Private Gateway(VGW)와 **Site-to-Site VPN 연결**을 구성하며,  
AWS는 중앙 허브 역할을 하여 지사들 간 **보안 통신을 중계**합니다.

---

## 🖼️ 아키텍처 예시

```
       [지사 A - CGW1]
              ⇅
        Site-to-Site VPN
              ⇅
       [VGW in AWS Region]
              ⇅
        Site-to-Site VPN
              ⇅
       [지사 B - CGW2]
```

이처럼 지사 A와 지사 B는 **AWS VGW를 중심으로 상호 연결**됩니다.

---

## 🧱 구성 조건

|항목|설명|
|---|---|
|**2개 이상의 Customer Gateway (CGW)**|각 지사별 고정 IP 주소 필요|
|**1개의 Virtual Private Gateway (VGW)**|VPC에 연결되는 중앙 게이트웨이|
|**Site-to-Site VPN 연결**|각 CGW ↔ VGW 사이에 VPN 터널 구성|
|**BGP 사용 권장**|라우팅 경로 교환을 자동화하여 관리 편의성 제공|

---

## ✅ CloudHub의 특징

|항목|설명|
|---|---|
|**지사 간 통신 가능**|AWS를 통해 **다른 지사와 직접 통신**할 수 있음|
|**인터넷 기반**|전용선 없이 **IPSec 터널만으로** 연결 가능|
|**저렴한 비용**|AWS VPN 요금만 부과되어 Direct Connect보다 비용 효율적|
|**보안성 확보**|트래픽은 **암호화된 IPSec 터널**을 통해 전송|
|**확장성**|지사 수가 증가하면 VPN 연결만 추가하면 되어 유연함|

---

## 🆚 CloudHub vs 일반 VPN

|항목|일반 Site-to-Site VPN|VPN CloudHub|
|---|---|---|
|연결 대상|온프레미스 ↔ VPC (1:1)|온프레미스 ↔ AWS ↔ 온프레미스 (n:n via hub)|
|목적|하이브리드 구성|지사 간 상호 연결|
|허브 역할|없음|VGW가 허브 역할|
|확장성|제한적|뛰어남 (여러 CGW 지원)|

---

## 🔧 설정 요약

1. **VPC에 Virtual Private Gateway(VGW)** 연결    
2. **각 지사에 Customer Gateway(CGW)** 생성    
3. **각 CGW ↔ VGW 간 Site-to-Site VPN 연결 구성**    
4. **라우팅 테이블 또는 BGP 통해 경로 자동화**    
5. 서로 다른 지사 간 통신 가능 여부 확인    

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**AWS VPN CloudHub**|
|목적|**여러 지사를 AWS를 통해 서로 연결**|
|핵심 구성|VGW + 다수의 Site-to-Site VPN + 여러 CGW|
|프로토콜|**IPSec**, BGP 권장|
|사용 예|본사 ↔ AWS ↔ 지사1, 지사2 등 지사 통신|