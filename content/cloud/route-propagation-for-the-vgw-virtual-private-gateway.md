---
title: “Route propagation for the VGW (Virtual Private Gateway)”
slug: "route-propagation-for-the-vgw-virtual-private-gateway"
category: cloud
tags: ["aws", "bgp", "networking", "route-propagation", "routing", "site-to-site-vpn", "vgw", "virtual-private-gateway", "vpc"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.470902+00:00"
---

**“Route propagation for the VGW (Virtual Private Gateway)”**는  
**AWS VPC의 라우팅 테이블(route table)**이  
**VPN 연결을 통해 자동으로 학습한 경로(BGP 등)를 자동 반영하도록 설정하는 기능**입니다.

---

## 📡 Route Propagation for VGW란?

> **Route propagation**은 Virtual Private Gateway(VGW)를 통해  
> **온프레미스 네트워크에서 전달받은 경로(BGP 등)를 VPC의 라우팅 테이블에 자동으로 추가**하는 기능입니다.
> 
> 이 기능이 활성화되면, **수동으로 경로를 입력할 필요 없이**  
> VPN을 통해 동적으로 학습된 **온프레미스 네트워크 경로가 자동 반영**됩니다.

---

## 🖼️ 구성 개념 예시

```
[온프레미스 라우터]
     ↕ BGP (동적 라우팅)
[Customer Gateway]
     ⇅ VPN 터널
[Virtual Private Gateway]
     ⇅
[Route Table in VPC] ← "Route propagation: ✅ 활성화"
```

- BGP로 전달받은 경로가 라우팅 테이블에 **자동 등록됨**
- 반대로, 비활성화된 경우에는 **사용자가 수동으로 추가해야 함**

---

## 🔧 설정 위치

- **VPC → Route Tables → [해당 라우팅 테이블] → Route Propagation 탭**
- VGW가 연결된 상태에서 “**Propagation 활성화(Enable Propagation)**” 체크

---

## ✅ Route Propagation 활성화 효과

|항목|설명|
|---|---|
|**자동 경로 수집**|BGP로 전달받은 온프레미스 네트워크 경로를 자동 등록|
|**운영 간소화**|경로 변경 시 재설정할 필요 없음|
|**동적 라우팅 필수 조건**|VPN에서 BGP를 사용하는 경우 필요|
|**오류 방지**|수동 경로 누락 또는 잘못 입력 방지|

---

## ⚠️ 비활성화 시 주의사항

- **BGP가 작동하더라도 라우팅 테이블에 경로가 반영되지 않음**
- 이 경우, 수동으로 `Destination`과 `Target`을 명시해야 함

---

## ✅ 요약

|항목|내용|
|---|---|
|용어|**Route propagation for the Virtual Private Gateway**|
|기능|**VPN 경로(BGP 등)를 VPC 라우팅 테이블에 자동 추가**|
|적용 위치|VPC의 **Route Table 설정**|
|필요 조건|VGW를 통한 **Site-to-Site VPN** 사용 시|
|이점|자동화, 오버헤드 감소, 오류 예방|