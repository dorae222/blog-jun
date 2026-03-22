---
title: 아키텍처 모드(Architecture Modes)
slug: "아키텍처-모드architecture-modes"
category: cloud
tags: ["aws", "aws-certification", "cloud-architecture", "direct-connect", "disaster-recovery", "high-availability", "resiliency", "rto-rpo", "vpc"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.204069+00:00"
---

**아키텍처 모드(Architecture Modes)**는 **고가용성, 확장성, 복원력 등을 달성하기 위한 설계 유형 또는 패턴**을 의미합니다.

이 개념은 특히 **재해 복구(Disaster Recovery)**나 **Direct Connect, VPC, 데이터베이스 설계**처럼 **복원력(Resiliency)**이 중요한 시나리오에서 자주 등장합니다.

---

## 🧱 아키텍처 모드(Architecture Modes)란?

> AWS에서 아키텍처 모드란,
> **서비스나 인프라를 설계할 때 따르는 표준화된 구성 방식 또는 복원력 수준에 따른 분류**를 말합니다.

이 용어는 특히 다음 두 가지에서 자주 언급됩니다:

1. **Disaster Recovery 전략 모드**

2. **Direct Connect Resiliency 모드**

---

## 📦 1. Disaster Recovery 아키텍처 모드 (4가지 DR 전략)

|모드|설명|복구 시간 (RTO)|복구 시점 (RPO)|비용|
|---|---|---|---|---|
|**백업 & 복원** (Backup & Restore)|데이터 백업만 유지하고 필요시 복구|수 시간 ~ 수일|수 시간 이상|💰 낮음|
|**파일럿 라이트** (Pilot Light)|핵심 인프라만 AWS에 유지, 장애 시 전체 확장|수 분 ~ 수 시간|수 분|💰 중간|
|**웜 스탠바이** (Warm Standby)|축소된 전체 환경을 항상 실행, 장애 시 스케일업|수 분|수 분|💰 높음|
|**멀티 사이트 활성-활성** (Multi-Site Active/Active)|온프레미스와 AWS 모두에서 동시에 운영|거의 즉시|거의 0|💰 매우 높음|

✅ **시험에서 매우 자주 등장**하므로 각 모드의 특성과 RTO/RPO, 비용 비교는 꼭 기억하세요.

---

## 📡 2. Direct Connect Resiliency 아키텍처 모드

| 모드                     | 설명                                      | 복원력 수준       |
| ---------------------- | --------------------------------------- | ------------ |
| **Low Resiliency**     | 단일 DX 연결, 백업 없음 | ❌ 없음         |
| **Failover (2 LoC)**   | 서로 다른 DX 로케이션에 2개 연결                    | ✅ 고가용성       |
| **Maximum Resiliency** | 2개 리전에 걸쳐 4개 연결 구성                      | ✅✅ 최고 수준 DR  |
| **DX + VPN Backup**    | Direct Connect 연결 + VPN 백업 경로           | 🔄 혼합형 백업 경로 |

이 역시 **시험에 자주 나오는 패턴**으로,
**“어떤 아키텍처 모드가 고가용성과 재해 복구를 가장 잘 제공하는가?”** 와 같은 문제로 출제됩니다.

---

## 📌 AWS 시험에서의 포인트

|질문 유형|예시|
|---|---|
|복원력 모드|“장애 발생 시 자동 전환이 가능한 아키텍처는?”|
|DR 전략|“가장 낮은 비용으로 데이터 복구를 하려면?”|
|DX 연결 설계|“멀티 리전에서 고가용성을 제공하려면 어떤 DX 모드?”|
|비용-성능 균형|“Warm standby와 Active-active의 비용/RTO 차이는?”|

---

## ✅ 요약

|항목|설명|
|---|---|
|**Architecture Modes**|AWS에서 고가용성·복원력 등을 달성하기 위한 **표준 설계 유형**|
|**주요 유형**|Disaster Recovery (4가지), Direct Connect Resiliency (4가지) 등|
|**시험 포인트**|RTO/RPO, 비용, 장애 복구 시간, 트래픽 자동 전환 여부 등 비교|