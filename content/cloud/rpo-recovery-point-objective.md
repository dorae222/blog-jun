---
title: RPO (Recovery Point Objective)
slug: "rpo-recovery-point-objective"
category: cloud
tags: ["aws", "backup", "data-protection", "disaster-recovery", "dr-planning", "high-availability", "rpo", "rto"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.362071+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---
---
aliases:
  - 복구 지점 목표
  - Recovery Point Objective
---

**RPO**는 **Recovery Point Objective**의 약자로,
**시스템이나 서비스가 장애에서 복구되었을 때 허용 가능한 데이터 손실의 시점을 시간 기준으로 나타낸 목표**입니다.

---

## 🔁 RPO (Recovery Point Objective)란?

> **RPO란 시스템 복구 시점에서 얼마나 오래된 데이터까지 복구하면 허용 가능한지를 나타내는 시간 기준입니다.**
> 즉, 장애 발생 시 **"최대 어느 시점까지의 데이터 손실을 감내할 수 있느냐"**를 정의합니다.

---

## 📌 예시로 이해하기

|RPO|의미|
|---|---|
|**5분**|백업 또는 복제가 **5분 간격으로 수행되므로**, 장애 발생 시 **최대 5분치 데이터 손실 허용**|
|**1시간**|장애 발생 시, **최근 1시간 동안 생성된 데이터는 유실될 수 있음**|

> ✅ **RPO는 백업 주기, 복제 간격, 로그 보관 방식 등에 따라 결정됩니다.**

---

## 🎯 RPO를 고려하는 상황

- 재해 복구(Disaster Recovery, DR) 계획 수립
- 백업/복제 전략 설계
- 고가용성 시스템 구축
- 데이터 보호 요구사항 분석

---

## 🔄 RPO vs RTO 차이

| 항목  | RPO (Recovery Point Objective) | RTO (Recovery Time Objective) |
| --- | ------------------------------ | ----------------------------- |
| 의미  | 복구 시 허용 가능한 **데이터 손실 시점**      | 시스템이 **얼마나 빨리 복구되어야 하는가**     |
| 단위  | 시간 (ex: 5분, 1시간)               | 시간 (ex: 10분, 1시간)             |
| 포커스 | **데이터 보호 관점**                  | **업타임/서비스 복원 관점**             |

---

## ✅ 요약

|항목|내용|
|---|---|
|정식 명칭|**Recovery Point Objective (RPO)**|
|의미|**복구 시점 기준으로 허용 가능한 데이터 손실 시간**|
|중요성|데이터 백업, 복제 전략 설계의 핵심 지표|
|예시|RPO가 15분이면, 최근 15분 내 데이터는 유실될 수 있음|

---

필요하시면 RPO/RTO를 기준으로 한 DR 전략이나, AWS에서 RPO를 최소화할 수 있는 서비스(예: Aurora Global DB, AWS Backup 등)에 대해서도 안내해 드리겠습니다!