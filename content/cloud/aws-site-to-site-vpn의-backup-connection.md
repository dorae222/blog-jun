---
title: "AWS Site-to-Site VPN의 Backup Connection"
slug: "aws-site-to-site-vpn의-backup-connection"
category: cloud
tags: ["aws", "bgp", "cloudwatch", "direct-connect", "high-availability", "hybrid-cloud", "site-to-site-vpn", "transit-gateway", "vpn"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.252377+00:00"
---

**AWS Site-to-Site VPN의 Backup Connection**은 **기본 VPN 연결이 장애를 일으켰을 때 자동으로 대체 경로로 전환되도록 구성한 보조 연결**을 의미합니다. 이는 **고가용성(HA) 및 장애 복구(DR)** 전략에서 핵심 요소입니다.

---

## 🛡️ Site-to-Site VPN의 Backup Connection이란?

> **Backup Connection**은 AWS와 온프레미스 간 **Site-to-Site VPN**에서
> **기본 터널이 다운될 경우 자동으로 트래픽을 전환할 수 있도록 구성한 대체 경로**입니다.

즉, **트래픽 중단 없이 연결을 유지하기 위한 장애 조치(failover) 구조**를 의미합니다.

---

## 🔧 구성 방식 요약

AWS Site-to-Site VPN은 기본적으로 **이중 터널**로 구성됩니다:

```
Customer Gateway (온프레미스)
       │
 ┌─────┴─────┐
 │ 터널 1 (Tunnel 1) │  ← 기본 터널
 │ 터널 2 (Tunnel 2) │  ← 백업 터널
 └─────┬─────┘
       │
 Virtual Private Gateway (VGW) or Transit Gateway
```

- **기본 터널(Tunnel 1)**: 일반 트래픽 처리
- **백업 터널(Tunnel 2)**: Tunnel 1 장애 시 **자동 활성화**
- 두 터널 모두 **IPSec** 기반이며 **BGP 또는 정적 라우팅**으로 구성 가능

---

## 🧩 Backup Connection 구성 옵션

|유형|설명|예시|
|---|---|---|
|**VPN 이중 터널 (기본 + 백업)**|하나의 Site-to-Site VPN 연결에 포함됨|AWS 기본 제공|
|**다른 VPN 연결을 백업용으로 구성**|다른 리전/라우터/인터넷 회선을 활용|수동 구성|
|**Direct Connect + VPN 백업**|Direct Connect가 기본, VPN이 백업|**Hybrid Backup** 구조|
|**Transit Gateway + 여러 VPN 연결**|다수의 VPN 연결로 TGW에 연결|고급 백업 시나리오|

---

## ⚙️ BGP 기반 장애 조치 (자동화 핵심)

- BGP(Border Gateway Protocol)를 통해 **라우팅 우선순위(MED, AS Path 등)**를 설정할 수 있습니다
- 하나의 터널이 비활성화되면 BGP 경로가 자동으로 변경됩니다
- **CloudWatch 경고 + Lambda로 경로 재설정 자동화도 가능**합니다

---

## ✅ 장점

|항목|설명|
|---|---|
|**고가용성**|기본 터널에 장애 발생 시 자동 전환 가능|
|**중단 없는 서비스**|백업 연결이 **연속성**을 제공|
|**비용 효율**|VPN은 인터넷 기반이므로 저비용 백업 경로로 적합|
|**복구 시간 최소화**|자동 전환으로 RTO가 짧음|

---

## 🔁 Backup 구성 예시

### 1. **이중 터널 구성 (AWS 기본)**

- Site-to-Site VPN 생성 시 **2개의 터널이 자동으로 제공**됩니다
- 라우팅 테이블 또는 BGP로 우선순위를 설정합니다


### 2. **DX + VPN Backup**

- Direct Connect가 기본 연결입니다
- VPN을 **백업 연결로 설정**하여 Direct Connect 장애 시 자동 전환하도록 구성합니다


### 3. **Multi-VPN Backup**

- 동일한 VGW에 대해 **서로 다른 CGW(고정 IP)**를 이용해 **다중 VPN 연결을 구성**합니다

---

## 📌 Best Practice

|전략|권장 사항|
|---|---|
|터널 헬스체크|**CloudWatch와 TunnelState metric**을 활용|
|자동 장애 조치|**BGP 기반 구성** + 경로 우선순위 조정|
|장애 경고|SNS + Lambda 조합으로 알림 및 자동 처리|
|지리적 이중화|**여러 리전에 백업 VPN** 구성 고려|

---

## ✅ 요약

| 항목     | 설명                                                              |
| ------ | --------------------------------------------------------------- |
| 정의     | 기본 Site-to-Site VPN 연결이 실패할 경우를 대비한 **대체 터널 또는 연결**             |
| 구성 방식  | **기본 2 터널 자동 제공**, 또는 **여러 VPN 연결 구성**                          |
| 특징     | **BGP로 자동 장애 조치 가능**, 비용 효율적인 백업 경로 |
| 주요 사용처 | 고가용성이 요구되는 하이브리드 네트워크, Direct Connect 백업                         |
