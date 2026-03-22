---
title: AWS Gateway Load Balancer (GWLB) 개요
slug: "aws-gateway-load-balancer-gwlb-개요"
category: cloud
tags: ["aws", "deep-packet-inspection", "firewall", "gateway-load-balancer", "geneve", "gwlb", "ids-ips", "networking", "third-party-security"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.850563+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - GWLB
---
## 📌 개요

![](/media/posts/imported/aws/Pasted%20image%2020250706143914.png)

- AWS에서 **서드파티 네트워크 가상 어플라이언스**(예: 방화벽, IDS/IPS, DPI 등)를 배포·확장·관리할 수 있도록 지원하는 로드 밸런서입니다.
- **네트워크 계층(Layer 3)**에서 동작하며, **IP 패킷 레벨**에서 트래픽을 처리합니다.

---

## 🔐 주요 사용 사례

- 방화벽(Firewall)
- 침입 탐지 및 방지 시스템(IDS/IPS)
- Deep Packet Inspection(DPI)
- 페이로드 변조 / 보안 게이트웨이

---

## ⚙️ 핵심 기능

|기능|설명|
|---|---|
|**Transparent Network Gateway**|모든 트래픽의 단일 진입·출구점 역할|
|**Load Balancer**|가상 어플라이언스 풀로 트래픽을 분산|
|**GATEWAY + LB 기능 통합**|보안 장비 배포 및 운영을 단순화|

- **Gv2 기반 GENEVE 프로토콜(포트 6081)**을 사용하여 트래픽을 캡슐화합니다.

---

## 📥 트래픽 흐름

```plaintext
사용자 요청 → Route Table → Gateway Load Balancer
                             ↓
       Target Group (3rd party 보안 어플라이언스)
                             ↓
                    최종 애플리케이션으로 전달
```

---

## 🎯 Target Groups

![](/media/posts/imported/aws/Pasted%20image%2020250706143954.png)

GWLB는 다음과 같은 대상을 트래픽 전달 대상으로 지원합니다:

|대상 타입|조건|
|---|---|
|**EC2 Instances**|프라이빗 서브넷 내 인스턴스|
|**IP Addresses**|반드시 **Private IP** 사용|

- 각 Target Group은 GWLB가 관리하며, **3rd party 보안 어플라이언스**는 EC2 인스턴스 또는 별도의 IP 형태로 배포될 수 있습니다.

---

## ✅ 요약 정리

|항목|내용|
|---|---|
|계층|L3 (네트워크 계층, IP 패킷)|
|대상|EC2, Private IP 기반 어플라이언스|
|프로토콜|GENEVE (포트 6081)|
|특징|보안 네트워크 장비의 배포 및 트래픽 분산 최적화|
|주요 기능|Transparent Gateway + Load Balancer 통합|
|사용 시나리오|방화벽, IDS, DPI, 서드파티 보안 솔루션|
