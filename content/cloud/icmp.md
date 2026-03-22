---
title: ICMP
slug: icmp
category: cloud
tags: ["aws", "cloud", "icmp", "ip", "network-diagnostics", "networking", "network-protocols", "network-security", "ping", "traceroute"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:07.013056+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---

---
aliases:
  - ICMP
---
**ICMP**는 네트워크의 **진단 및 오류 보고용 프로토콜**입니다.  
인터넷에서 흔히 쓰이는 **핑(ping) 명령어도 ICMP의 일종**입니다.

---

## 🌐 ICMP란?

> **ICMP (Internet Control Message Protocol)**는  
> 네트워크 장비(라우터, 호스트 등) 간에 **진단 메시지나 오류 메시지를 주고받기 위한 제어용 프로토콜**입니다.
> 
> IP 프로토콜군의 일부이며, **IP 패킷의 전달 성공 여부나 장애 상황을 알려주는 역할**을 합니다.

---

## 🧩 ICMP의 주요 역할

|기능|설명|
|---|---|
|**Ping**|네트워크 연결 여부를 확인 (`echo request/reply`)|
|**Traceroute**|목적지까지 경로 추적 (ICMP 시간 초과 메시지 사용)|
|**네트워크 오류 알림**|목적지 도달 불가, 라우팅 실패, 패킷 손실 등|
|**속도 느림 알림**|네트워크 혼잡 시 `source quench` 메시지 전달|

---

## 🧪 예시: Ping 명령어

```bash
ping 8.8.8.8
```

- 이 명령은 대상 IP에 **ICMP Echo Request**를 보내고,
    
- 상대방이 **Echo Reply**를 응답하면 연결이 된 것으로 판단합니다.
    
📍 **ICMP는 연결을 설정하지 않고 동작하는, 매우 가벼운 프로토콜입니다.**

---

## 🛡️ 보안 측면에서의 주의사항

- ICMP는 보안상 차단되거나 제한되는 경우가 많습니다.
    
    - 예: **방화벽에서 ICMP Ping 차단** → 연결이 되지 않는 것처럼 보일 수 있음
        
- 공격자에 의해 **네트워크 스캐닝 또는 DDoS에 악용**될 수 있습니다.
    
    - 예: ICMP Flood 공격
        

---

## 📑 ICMP 주요 메시지 유형

|유형|설명|
|---|---|
|0|Echo Reply (ping 응답)|
|3|Destination Unreachable (도달 불가)|
|5|Redirect (더 나은 경로 제안)|
|8|Echo Request (ping 요청)|
|11|Time Exceeded (traceroute에서 사용됨)|

---

## ✅ 요약

|항목|설명|
|---|---|
|이름|**ICMP (Internet Control Message Protocol)**|
|역할|**IP 네트워크에서 오류/진단 메시지 전달**|
|대표 사용|**ping, traceroute**|
|특징|**비신뢰성, 연결 없음**, 라우팅/네트워크 상태 점검에 유용|
|보안 주의|ICMP 차단 여부가 통신에 영향을 줄 수 있음|