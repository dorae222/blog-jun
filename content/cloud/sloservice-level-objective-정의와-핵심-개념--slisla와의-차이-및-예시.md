---
title: SLO(Service Level Objective) 정의와 핵심 개념 — SLI/SLA와의 차이 및 예시
slug: "sloservice-level-objective-정의와-핵심-개념--slisla와의-차이-및-예시"
category: cloud
tags: ["availability", "data-mesh", "observability", "service-level-indicator", "service-level-objective", "sla", "sli", "slo", "sre"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.865086+00:00"
---

**SLO(Service Level Objective)**는 서비스 품질에 대해 조직 내부에서 설정한 목표 수준입니다.

---

## 한 줄 정의

> **SLO는 서비스가 달성해야 할 품질 목표(SLA)를 수치로 정의한 내부 목표값이다.**

---

## SLO의 핵심 특징

### 1️⃣ 내부 목표 (Not a contract)

- 고객과의 법적 계약 ❌
- 운영·엔지니어링 기준
- SLA를 만족하기 위한 내부 관리 목표

---

### 2️⃣ 측정 가능한 수치

- 퍼센트
- 시간
- 횟수

예:

- 가용성 99.95%
- 응답 시간 p95 < 300ms
- 데이터 최신성 < 10분

---

### 3️⃣ SLI를 기반으로 설정

- **SLI(Service Level Indicator)**로 측정
- 측정 결과로 SLO 충족 여부를 판단

---

## SLO vs SLA vs SLI (정리)

|구분|의미|대상|
|---|---|---|
|**SLI**|측정 지표|실제 수치|
|**SLO**|목표|내부 운영 기준|
|**SLA**|약속/계약|외부 고객|

관계:

> **SLI → SLO → SLA**

---

## 예시로 이해하기

### 웹 서비스

- SLI: 평균 응답 시간
- SLO: p95 응답 시간 ≤ 200ms
- SLA: 월 가용성 99.9%

### 데이터 파이프라인

- SLI: 데이터 적재 완료 시각
- SLO: 매일 07:50 이전 적재 완료
- SLA: 매일 08:00 이전 데이터 제공

---

## Data Mesh에서의 SLO

- 각 데이터 제품은 다음 항목에 대한 SLO를 명시:
  - **Freshness**
  - **Completeness**
  - **Accuracy**
- 이러한 SLO들은 SLA의 기반이 된다.