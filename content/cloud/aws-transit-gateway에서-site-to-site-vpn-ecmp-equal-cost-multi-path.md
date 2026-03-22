---
title: "AWS Transit Gateway에서 Site-to-Site VPN ECMP (Equal-Cost Multi-Path)"
slug: "aws-transit-gateway에서-site-to-site-vpn-ecmp-equal-cost-multi-path"
category: cloud
tags: ["aws", "bgp", "cloud-networking", "ecmp", "high-availability", "load-balancing", "site-to-site-vpn", "transit-gateway", "vpn"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.882722+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

AWS **Transit Gateway에서의 AWS Site-to-Site VPN ECMP(Equal-Cost Multi-Path)**는
여러 개의 **동일한 비용(BGP metric)의 VPN 경로를 동시에 사용하는 기능**으로,
**고가용성과 로드 밸런싱을 동시에 제공**하는 실무에 유용한 네트워크 아키텍처입니다.

- 일종의 라우팅 전략
- 기업 데이터 센터를 VPC에 연결한 경우 사용할 수 없는 기능

---

## 🚍 ECMP란?

> **ECMP (Equal-Cost Multi-Path Routing)**란
> 목적지까지의 **라우팅 경로가 여러 개 존재하고 그 비용이 같을 때**,
> 이들을 **동시에 사용하여 트래픽을 분산**하는 라우팅 기법입니다.

AWS에서는 **Transit Gateway(TGW)**에서 ECMP를 통해 **여러 VPN 터널을 동시에 활성화**해
**성능과 내구성**을 모두 향상시킬 수 있습니다.

---

## 🌐 Transit Gateway에서 Site-to-Site VPN ECMP 구성

### 구성 예시:

```text
         On-Premises
        ┌─────────────┐
        │ Customer GW │
        └────┬─┬──────┘
             │ │
   VPN 1 ────┘ └─── VPN 2
             ↓     ↓
     ┌────────────────────┐
     │  AWS Transit GW    │
     └────────┬───────────┘
              ↓
            VPCs
```

- 두 개의 Site-to-Site VPN 연결이 **동일한 Customer Gateway**와 연결됨

- **각 VPN 연결에 대해 두 개의 터널**이 존재

- **Transit Gateway는 BGP 경로를 통해 동일 비용 경로를 감지**

- **최대 4개의 터널을 통해 트래픽을 동시 분산 (ECMP)**

---

## 🧩 구성 요건

|항목|요구 사항|
|---|---|
|**BGP 활성화**|각 터널에 대해 BGP 라우팅 사용 필수|
|**Transit Gateway와 연결**|Site-to-Site VPN을 TGW에 연결해야 ECMP 적용|
|**라우팅 비용 동일**|모든 경로의 **BGP metric 동일**해야 ECMP 작동|
|**Customer Gateway당 최대 2개의 터널**|2개의 VPN 연결 × 2 터널 = 최대 4개의 ECMP 경로|

---

## ⚙️ 작동 방식 요약

- Transit Gateway는 **동일한 BGP 비용의 여러 경로**를 감지하면
  자동으로 **로드 밸런싱**을 수행합니다.

- **Flow Hashing** 기법으로 각 세션이 하나의 경로에 고정되며,
  여러 세션은 **여러 경로로 분산 처리**됩니다.

- 터널 중 일부가 실패하면 **자동 장애 조치(Failover)**도 지원됩니다.

---

## ✅ 장점

|항목|설명|
|---|---|
|**고가용성**|하나의 VPN 터널에 문제가 생겨도 나머지 터널로 트래픽 유지|
|**로드 밸런싱**|여러 터널 간 트래픽 분산 가능|
|**확장성**|최대 4개의 ECMP 경로 구성 가능 (2 VPN 연결 × 2 터널)|
|**자동 장애 조치**|터널 다운 시 자동 경로 전환 (BGP로 감지)|

---

## 📌 실무 팁

|항목|권장 사항|
|---|---|
|BGP 설정|Customer Gateway에서도 BGP 활성화 필요|
|모니터링|CloudWatch VPN 상태 지표 활용 (`TunnelState`)|
|터널 수 제한|TGW + 동일한 CGW 조합으로는 **4개 터널까지 ECMP 가능**|
|Hybrid 환경|ECMP는 **Direct Connect에는 적용되지 않음** (VPN 전용)|

---

## ✅ 요약

|항목|내용|
|---|---|
|정의|**Transit Gateway가 VPN 터널 여러 개에 걸쳐 트래픽을 자동 분산**|
|기술|**ECMP (Equal-Cost Multi-Path)**|
|요구 사항|**BGP 구성**, 동일 비용 경로, 최대 4개 터널|
|장점|고가용성, 로드 밸런싱, 자동 장애 조치|

---

필요하시면 ECMP 구성 예제, BGP 라우팅 설정 방법, 실전 아키텍처 예시도 제공해 드릴게요!