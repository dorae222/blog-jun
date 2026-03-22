---
title: Elastic IP (EIP)
slug: "elastic-ip-eip"
category: cloud
tags: ["alb", "aws", "ec2", "eip", "elastic-ip", "ipv4", "nat-gateway", "network-load-balancer", "public-ip"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.733610+00:00"
---

**EIP**는 **Elastic IP address**의 약자로, AWS에서 제공하는 **고정(static) 공인 IP 주소**입니다.

---

## 🌐 Elastic IP (EIP)란?

### ✅ 정의:

> **Elastic IP 주소**는 **동적으로 할당되지만 고정처럼 사용할 수 있는 퍼블릭 IPv4 주소**입니다.  
> AWS 계정에 연결되며, **필요한 EC2 인스턴스나 Network Load Balancer(NLB)** 등에 자유롭게 연결할 수 있습니다.

---

## 🔍 주요 특징

|특징|설명|
|---|---|
|**고정(public static)**|인스턴스를 재부팅하거나 중지해도 IP가 변하지 않습니다.|
|**탄력적(elastic)**|필요에 따라 다른 인스턴스나 리소스에 다시 할당할 수 있습니다.|
|**퍼블릭 접근 가능**|인터넷에서 직접 접근 가능한 공인 IP입니다.|
|**IPv4 전용**|현재는 IPv6에는 EIP 개념이 없습니다.|
|**요금**|EIP를 할당했으나 사용하지 않으면 과금되므로 비용 효율을 고려해야 합니다.|

---

## 💡 EIP 사용 예시

1. **EC2 인스턴스에 EIP 연결**  
    → 외부 시스템이나 사용자에게 항상 동일한 IP 주소로 서비스 제공 가능
    
2. **NAT Gateway에 EIP 연결**  
    → 프라이빗 서브넷의 EC2 인스턴스가 인터넷으로 나갈 때 고정 IP 사용
    
3. **NLB(Network Load Balancer)에 EIP 연결**  
    → 외부 클라이언트가 **고정 IP 기반 방화벽**을 통해 접근 가능
    
---

## 📌 실제 용도 예:

> “우리 고객의 방화벽은 허용된 IP만 접속할 수 있게 되어 있다.  
> 따라서 우리는 **NLB에 EIP를 연결하여 고정 IP**를 제공해야 한다.”

---

## 🛑 반대로 ALB는?

- **ALB (Application Load Balancer)**는 EIP를 지원하지 않으며, 자동으로 할당된 동적 IP를 사용합니다.
- 따라서 **IP 고정이 중요한 보안 요구가 있는 환경에는 부적합**합니다.

---

## ✨ 요약:

|항목|EIP (Elastic IP)|
|---|---|
|고정 IP인가?|✅ 예|
|탄력적으로 재할당 가능한가?|✅ 예|
|EC2, NAT GW, NLB에 연결 가능한가?|✅ 예|
|사용하지 않으면 비용 발생하나?|✅ 예|
|ALB에 연결 가능한가?|❌ 아니요|

---

필요하다면 EIP 설정 방법, 할당 절차도 알려드릴게요!