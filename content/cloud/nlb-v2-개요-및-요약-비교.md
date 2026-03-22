---
title: NLB (v2) 개요 및 요약 비교
slug: "nlb-v2-개요-및-요약-비교"
category: cloud
tags: ["alb", "aws", "elastic-ip", "high-performance", "load-balancing", "network-load-balancer", "nlb", "tcp", "udp"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.181560+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - NLB
---
## 📌 개요

- **NLB (v2)** 는 **Layer 4 (TCP/UDP)** 수준에서 동작하는 로드 밸런서입니다.

- 초고속·초저지연 환경에 최적화된 로드 밸런서입니다.

- NLB는 <u>AZ(가용 영역)마다 하나의 Static IP</u>를 제공하며 Elastic IP 할당을 지원합니다.
  - 이는 특정 IP를 화이트리스트에 등록할 때 유용합니다.
---

## 🚀 주요 기능

- **TCP 및 UDP 트래픽 전달** 지원
  - NLB에 TLS 수신기를 구성하고 서버 인증서를 추가하면 웹 계층으로 전달되는 데이터의 보안을 강화할 수 있습니다.

- 초당 수백만 요청 처리 가능

- 매우 낮은 지연 시간 제공

- <mark style="background: #FFF3A3A6;">AZ(가용 영역)마다 고정된 Static IP 제공</mark>

- Elastic IP 할당 가능 → 특정 IP 화이트리스트 등록에 유리

- **AWS Free Tier에는 포함되지 않음**

---

## 🔁 라우팅 예시

![](/media/posts/imported/aws/Pasted%20image%2020250706143614.png)

```plaintext
[사용자 요청: TCP or HTTP]
↓
[External Network Load Balancer (v2)]
↓
[Target Group: Users / Search 애플리케이션]
```

- TCP 기반 및 룰 기반으로 Target Group에 요청을 전달합니다.

- HTTP 요청도 L4 수준의 TCP 포워딩으로 처리할 수 있습니다.

---

## 🧱 Target Group 구성 요소

![](/media/posts/imported/aws/Pasted%20image%2020250706143713.png)

|타입|설명|
|---|---|
|EC2 Instances|일반적인 인스턴스 대상|
|IP Addresses|Private IP만 사용 가능|
|Application Load Balancer|ALB 자체도 타겟으로 설정 가능|

- Health Check는 **<u>TCP, HTTP, HTTPS 프로토콜 지원</u>**

- EC2 인스턴스와 IP 주소 기반의 백엔드 구성이 가능합니다.

- ALB를 NLB의 타겟으로 사용 가능하여 하이브리드 구성이 가능합니다.

---

## ✅ 요약 비교 (vs ALB)

|항목|NLB (v2)|ALB (v2)|
|---|---|---|
|계층|L4 (TCP/UDP)|L7 (HTTP/HTTPS)|
|트래픽 처리|수백만 요청/초|수천~수만 요청/초|
|고정 IP|제공 (Static IP per AZ)|미제공|
|대상|EC2, IP, ALB|EC2, Lambda, ECS|
|Health Check|TCP, HTTP, HTTPS|HTTP, HTTPS|
|사용 목적|고성능, 게임, 실시간 서비스 등|웹 앱, API, 컨테이너 기반 서비스|
