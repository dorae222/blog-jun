---
title: Disaster Recovery(재해 복구)
slug: "disaster-recovery재해-복구"
category: cloud
tags: ["amazon-s3", "aurora", "aws", "aws-elastic-disaster-recovery", "backup", "disaster-recovery", "route53", "rpo", "rto"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:06.567011+00:00"
---

**Disaster Recovery(재해 복구)**는 IT 시스템이나 서비스가 **장애, 자연재해, 사이버 공격 등 비상 상황에서 중단되었을 때, 이를 빠르게 복구하여 업무를 재개할 수 있도록 하는 전략 및 절차**를 말합니다.

---

## 🌪️ Disaster Recovery(재해 복구)란?

> **Disaster Recovery(DR)**는 시스템이 심각한 장애를 겪었을 때,
> **데이터 손실을 최소화하고 서비스 복원을 빠르게 수행**하기 위한 **사전 계획과 기술적 실행 전략**입니다.

즉, **“장애가 나면 어떻게 복구할 것인가?”**에 대한 사전 준비입니다.

---

## 🎯 DR의 핵심 목표

| 목표 | 설명 |
| --- | --- |
| **RPO (Recovery Point Objective)** | 복구 시 허용 가능한 **데이터 손실의 최대 시점** |
| **RTO (Recovery Time Objective)** | 장애 발생 후 시스템을 **복구하는 데 걸리는 최대 시간** |

예를 들어:

- RPO: 10분 → 장애 시 **최대 10분치 데이터는 유실될 수 있음**
- RTO: 30분 → 장애 후 **30분 이내에 복구되어야 함**

---

## 🧱 재해 복구 전략 유형 (AWS 기준)

| 전략 수준 | 설명 | 비용 | 복구 속도 |
| --- | --- | --- | --- |
| **백업 & 복원** | 정기적으로 S3, Glacier 등에 백업하고, 필요시 복구 | 저 | 느림 |
| **Pilot Light** | 핵심 서비스만 대기 상태로 유지, 장애 시 확장 | 중 | 보통 |
| **Warm Standby** | 소규모 버전이 항상 실행 중, 장애 시 확장 | 중상 | 빠름 |
| **Active-Active (Multi-Site)** | 이중화된 전체 시스템이 항상 활성화 | 고 | 매우 빠름 (무중단 가능) |

---

## 🛠️ AWS에서 활용 가능한 DR 관련 서비스

| 서비스 | 용도 |
| --- | --- |
| **Amazon S3 + AWS Backup** | 백업 저장소 및 정기 백업 |
| **Amazon RDS Multi-AZ** | DB 자동 장애 조치 및 복구 |
| **AWS Elastic Disaster Recovery (DRS)** | EC2, 온프레미스 시스템 복구 자동화 |
| **Amazon Route 53** | 헬스 체크 기반 DNS 장애 조치 (Failover Routing) |
| **Amazon Aurora Global Database** | 리전 간 복제 기반의 빠른 DR |
| **CloudEndure (이전 서비스명)** | 마이그레이션 및 DR 자동화 도구 |

---

## 🧪 예시 시나리오

> 서울 리전에서 호스팅된 서비스에 **지진, 정전 등으로 리전 전체 장애 발생**
> → 도쿄 리전에 복제된 인프라로 자동 전환
> → RTO: 15분, RPO: 5분

---

## ✅ 요약

| 항목 | 내용 |
| --- | --- |
| 이름 | **Disaster Recovery (재해 복구)** |
| 목적 | **장애 발생 시 빠르게 복구하고 데이터 손실 최소화** |
| 핵심 지표 | RTO (복구 시간), RPO (데이터 손실 허용 시간) |
| 전략 유형 | 백업-복원, Pilot Light, Warm Standby, Active-Active |
| AWS 관련 서비스 | S3, Backup, Route 53, DRS, Aurora Global 등 |