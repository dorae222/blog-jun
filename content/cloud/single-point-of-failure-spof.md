---
title: Single Point of Failure (SPOF)
slug: "single-point-of-failure-spof"
category: cloud
tags: ["auto-scaling", "aws", "high-availability", "multi-az", "nat-gateway", "rds", "spof", "transit-gateway", "vpc"]
status: published
post_type: article
quality_score: 8.0
created_at: "2026-03-02T01:08:08.221595+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A


---
---
aliases:
  - SPOF
  - Single Point of Failure
---
**Single Point of Failure (SPOF)**는 **시스템 전체의 가용성이나 동작을 위협할 수 있는 단일 장애 지점**을 의미합니다. 즉, **하나의 구성 요소가 고장 나면 전체 시스템이 멈추는 구조**를 말합니다.

---

## ⚠️ Single Point of Failure(SPOF)란?

> **SPOF(단일 장애 지점)**은 시스템 내에서 **어떤 하나라도 고장 나면 전체 서비스가 중단되는 구성 요소**입니다. 이 지점에서 장애가 발생하면 서비스 전반에 큰 영향을 미치므로, **고가용성(HA)** 설계 시 반드시 제거하거나 보완해야 합니다.

---

## 📌 예시로 이해하기

|예시|설명|
|---|---|
|**단일 EC2 인스턴스**|웹 애플리케이션이 하나의 서버에만 배포되어 있고 해당 인스턴스 장애 시 전체 서비스가 중단됨|
|**단일 RDS 인스턴스**|RDS가 Multi-AZ로 구성되지 않았고 단일 인스턴스에만 의존하는 경우|
|**NAT 인스턴스 1대만 존재**|해당 NAT 인스턴스에 장애가 발생하면 프라이빗 서브넷의 인스턴스들이 인터넷에 접근 불가|
|**단일 AZ에만 리소스 배치**|가용 영역(AZ) 단독 장애 시 애플리케이션 전체가 정지될 수 있음|

---

## 🧠 SPOF를 제거하는 방법 (AWS 기준)

|SPOF 요소|개선 방법|
|---|---|
|EC2 단일 인스턴스|Auto Scaling 그룹 + 로드 밸런서(ALB/NLB) 구성|
|RDS 단일 인스턴스|Multi-AZ 또는 Aurora 클러스터 사용|
|단일 가용 영역|**멀티 AZ/멀티 리전** 배포|
|단일 NAT 인스턴스|AWS 관리형 NAT Gateway + AZ별 복제|
|단일 VPC 피어링|**Transit Gateway**로 허브-앤-스포크 구조 구성|

---

## 🎯 SPOF가 중요한 이유

- 장애 발생 시 **서비스 전체 중단** 위험이 커집니다.
- SLA 위반 가능성이 증가합니다.
- 비즈니스 손실과 사용자 불만을 초래할 수 있습니다.
- 보안 측면에서도 단일 실패 지점은 공격에 취약합니다.

---

## ✅ 요약

|항목|내용|
|---|---|
|용어|**Single Point of Failure (SPOF)**|
|의미|장애 시 전체 시스템이 중단될 수 있는 **단일 구성 요소**|
|피해|서비스 다운, 데이터 손실, 고객 불만|
|방지 방법|**중복 구성, 고가용성 아키텍처, 자동 복구 설계**|

---

### 💡 관련 개념

- **High Availability (HA)**: SPOF가 없는 구조
- **Fault Tolerance**: 장애 발생에도 **무중단 운영**이 가능한 상태
- **Elasticity**: 자동으로 확장/축소하는 능력
