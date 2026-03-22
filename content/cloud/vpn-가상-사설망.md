---
title: VPN (가상 사설망)
slug: "vpn-가상-사설망"
category: cloud
tags: ["aws", "client-vpn", "direct-connect", "ipsec", "networking", "openvpn", "site-to-site-vpn", "transit-gateway", "vpn"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:08.055434+00:00"
---

**VPN**은 "Virtual Private Network", 즉 **가상 사설망**을 의미합니다.  
인터넷 같은 공용 네트워크를 사용하되, **안전하고 암호화된 통신 터널을 형성**하여 기업 내부망처럼 사용할 수 있게 해주는 기술입니다.

---

## 🌐 VPN이란?

> **VPN (Virtual Private Network)**은  
> **공용 네트워크(예: 인터넷)를 통해 두 지점을 안전하게 연결**하는 **암호화된 가상 터널**입니다.  
> 이를 통해 사용자는 **원격지에서도 사설 네트워크(회사 내부망 등)에 접근**할 수 있고,  
> **데이터는 안전하게 전송**됩니다.

---

## 🔐 VPN의 주요 기능

|기능|설명|
|---|---|
|**암호화**|트래픽을 암호화하여 도청이나 위조를 방지|
|**보안 터널링**|인터넷을 통해서도 **사설망처럼 안전한 통신 경로를 생성**|
|**IP 숨김**|VPN 서버를 통해 인터넷에 접속 → 실제 IP 주소가 숨겨짐|
|**원격 접근**|재택근무자나 출장자가 사무실 네트워크에 접속 가능|
|**지역 제한 우회**|특정 지역에서만 접근 가능한 콘텐츠를 VPN으로 우회 가능|

---

## 🧱 VPN의 주요 구성 요소

|구성 요소|설명|
|---|---|
|**VPN 클라이언트**|사용자 장치 (노트북, PC, 모바일 등)|
|**VPN 서버**|연결 대상 서버 또는 네트워크 (AWS, 기업 내부망 등)|
|**암호화 터널**|두 장치 간 안전한 통신 경로 (IPSec, SSL 등 프로토콜 사용)|

---

## 🏗️ AWS에서의 VPN 사용 예시

|유형|설명|
|---|---|
|**Site-to-Site VPN**|온프레미스 네트워크와 AWS VPC 간의 보안 연결|
|**Client VPN**|직원의 개인 장치에서 AWS 또는 사내망에 직접 접속|
|**Transit Gateway VPN**|여러 VPC 또는 네트워크와의 중앙 통합 연결|

---

## 🆚 VPN vs Direct Connect

|항목|VPN|AWS Direct Connect|
|---|---|---|
|연결 방식|인터넷 기반 (IPSec)|전용 물리 회선|
|보안|암호화됨|암호화 없음 (원하면 VPN 병행 필요)|
|지연 시간|상대적으로 높음|낮음 (품질 우수)|
|비용|저렴|비쌈 (대역폭 단가 높음)|

---

## ✅ 요약

|항목|내용|
|---|---|
|이름|**VPN (Virtual Private Network)**|
|목적|공용 네트워크를 통해 **사설 네트워크처럼 안전하게 통신**|
|장점|보안, 원격 접속, 암호화|
|AWS 예시|Site-to-Site VPN, Client VPN, Transit Gateway VPN|
|사용 프로토콜|**IPSec, SSL, OpenVPN** 등|