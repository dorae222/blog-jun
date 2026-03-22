---
title: AWS Direct Connect – Resiliency (복원력 설계)
slug: "aws-direct-connect--resiliency-복원력-설계"
category: cloud
tags: ["aws", "aws-direct-connect", "bgp", "direct-connect", "disaster-recovery", "high-availability", "lag", "networking", "resiliency", "vpn"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.462809+00:00"
---

Direct Connect(DX)는 네트워크 장애 상황에서도 **서비스 연속성**을 유지하기 위한 다양한 **복원력 설계 옵션**을 제공합니다.

---
## 🛡️ AWS Direct Connect – Resiliency (복원력)

> **Resiliency**는 네트워크 장애, 링크 단절, 장비 고장 등이 발생했을 때  
> **AWS Direct Connect 연결이 중단되지 않도록 구성하는 고가용성 설계 방법**입니다.

---
## 💡 왜 Resiliency가 중요한가?

|상황|위험 요소|
|---|---|
|라우터 장애|단일 라우터에 의존하면 전체 연결이 끊길 수 있음|
|회선 장애|물리적 링크 장애 시 데이터 손실 또는 서비스 다운 발생 가능|
|지역 재해|특정 리전 또는 위치에 문제가 생기면 전체 서비스에 영향 가능|

---
## 🏗️ Direct Connect Resiliency 옵션 구조

AWS는 공식적으로 다음 **4가지 복원력 모델**을 제시합니다:

|모델|설명|중복성|권장 용도|
|---|---|---|---|
|**Low Resiliency**|단일 연결만 구성|❌ 없음|테스트 또는 비생산 환경|
|**Failover (2 LoC)**|서로 다른 로케이션에 Direct Connect 두 개 구성|✅ 고가용성|일반적 프로덕션 환경|
|**Maximum Resiliency**|두 리전에 걸쳐 4개 연결 구성 (각 리전에 2개씩)|✅✅ 리전 중복|재해 복구, 금융 등 고신뢰성 환경|
|**Hosted + VPN Backup**|Hosted DX + Site-to-Site VPN 결합|✔ 중간 비용|DX + 인터넷 이중화 대안|

---
## 🧬 AWS의 Resiliency 추천 아키텍처

### 1. 🔄 이중 연결 (Two Dedicated Connections)

- **동일 리전** 내 두 개의 DX 로케이션에 연결하거나
- **다른 리전**의 DX 로케이션에 연결
- **BGP를 통해 자동 장애 조치**가 이루어짐

### 2. 🌍 최대 복원력 (Maximum Resiliency)

- 서로 다른 **2개의 AWS 리전**에 각각 2개씩, 총 4개의 연결 구성
- 이를 통해 **리전 수준의 지리적 이중화(Region level DR)**가 가능함

### 3. 🔁 VPN 백업

- **Direct Connect + Site-to-Site VPN**을 동시에 구성
- DX 장애 시 VPN이 백업 경로 역할을 수행함

---
## 📦 Resiliency Toolkit – AWS 제공 기능

|기능|설명|
|---|---|
|**Link Aggregation Group (LAG)**|여러 Dedicated 연결을 **하나의 논리적 그룹**으로 묶어 자동 failover를 지원|
|**BGP Multipath**|다중 경로를 동시에 사용하여 **로드 밸런싱 및 자동 장애 조치** 제공|
|**CloudWatch + Alarms**|연결 상태를 실시간으로 모니터링하고 알림을 발생시킴|
|**Route Priority 설정**|BGP 경로 우선순위를 조정하여 **주/백업 경로 제어** 가능|

---
## 📝 복원력 설계 시 고려사항

|항목|권장 사항|
|---|---|
|**리전 이중화**|가능하면 DX 연결을 서로 다른 리전에 구성할 것|
|**물리적 경로 이중화**|동일 통신사의 회선에만 의존하지 않도록 설계할 것|
|**VPN 백업 구성**|최소한 VPN을 통해 백업 경로를 확보할 것|
|**모니터링 및 자동화**|장애 탐지를 위해 CloudWatch와 SNS 알림을 설정할 것|

---
## ✅ 요약

|항목|내용|
|---|---|
|목적|AWS Direct Connect의 **고가용성 및 장애 대비 설계**|
|핵심 전략|이중 연결, 지리적 분산, LAG, BGP 다중 경로|
|실무 팁|**DX + VPN 이중화**, CloudWatch 모니터링, 서로 다른 통신사 회선 선택|

- Architecture Modes