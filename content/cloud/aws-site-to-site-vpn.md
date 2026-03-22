---
title: "AWS Site-to-Site VPN"
slug: "aws-site-to-site-vpn"
category: cloud
tags: ["aws", "hybrid-cloud", "ipsec", "site-to-site-vpn", "transit-gateway", "virtual-private-gateway", "vpc", "vpn"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:04.440576+00:00"
---

> **NOTE:**
> **AWS Site-to-Site VPN**은 온프레미스(회사 내부) 네트워크와 AWS 클라우드 네트워크(VPC)를 **보안된 방식으로 연결**하는 서비스입니다.

---

## 🌐 AWS Site-to-Site VPN란?

> **AWS Site-to-Site VPN**은 기업의 **온프레미스 데이터센터 또는 지사 네트워크**를 **AWS Virtual Private Cloud (VPC)**와 **암호화된 IPsec VPN 연결**을 통해 안전하게 연결하는 서비스입니다.

---

## 🔐 주요 특징

| 항목                 | 설명                                                                      |
| ------------------ | ----------------------------------------------------------------------- |
| **보안 연결**          | IPsec 프로토콜을 사용한 **암호화된 터널** 제공                                          |
| **양방향 통신**         | 온프레미스 ↔ AWS 간의 트래픽을 주고받을 수 있음                                             |
| **이중 터널**          | 기본적으로 **2개의 VPN 터널**이 생성되어 **고가용성 구성**이 가능                               |
| **CloudWatch 통합**  | 터널 상태 및 트래픽을 모니터링할 수 있음                                                 |
| **VPN Gateway 필요** | AWS 측에 **Virtual Private Gateway (VGW)** 또는 **Transit Gateway**를 구성해야 함 |

---

## 🏢 언제 사용하나요?

- 온프레미스에서 AWS에 있는 EC2, RDS 등 자원에 **직접 접근**해야 할 때
- **하이브리드 클라우드** 아키텍처를 구성할 때
- 백업, 데이터 복제, 파일 전송 등 **보안 연결**이 필요할 때

---

## 🔁 구성 요소

| 구성 요소                                                        | 역할                                      |
| ------------------------------------------------------------ | --------------------------------------- |
| **Customer Gateway (CGW)**                               | 온프레미스 라우터 또는 방화벽                        |
| **Virtual Private Gateway (VGW)** 또는 **Transit Gateway** | AWS 측 라우팅 지점                            |
| **VPN 연결**                                                   | 이 두 지점을 연결하는 **IPsec 터널 2개**로 구성된 가상 연결 |

---

## 🎯 장점 vs. 다른 옵션

|항목|Site-to-Site VPN|AWS Direct Connect|
|---|---|---|
|연결 방식|인터넷을 통한 암호화 터널|전용 회선|
|보안성|암호화(IPsec)|전용망 기반|
|대역폭/지연|상대적으로 낮음|높음 (전용 회선)|
|구축 시간|빠름 (몇 분 이내)|느림 (며칠~몇 주 소요)|
|비용|저렴|비쌈|

---

## ✅ 요약

> **AWS Site-to-Site VPN은** 온프레미스 네트워크와 AWS 클라우드를 **암호화된 안전한 터널(IPsec)**로 연결하는 서비스입니다. **하이브리드 환경**, **보안 전송**, **빠른 연결 구성**에 적합한 솔루션입니다.


### AWS VPN CloudHub


### Resiliency


### Backup Connection