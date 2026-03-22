---
title: Redshift WLM(Workload Management) 개요
slug: "redshift-wlmworkload-management-개요"
category: cloud
tags: ["auto-wlm", "aws", "monitoring", "performance-tuning", "query-optimization", "query-routing", "redshift", "wlm", "workload-management"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.419337+00:00"
---

Category: Cloud
Subcategory: 11.AWS
Quality grade: A

---

- 짧고 빠른 쿼리 우선화 vs. 길고 느린 쿼리
- 쿼리 큐 기반 분리
- 콘솔, CLI 또는 API로 설정 가능

## 한 줄 정의

> **WLM은 Redshift에서 쿼리를 큐(서비스 클래스)로 분리해 리소스를 배분하고 성능을 관리하는 메커니즘이다.**

---

## 왜 WLM이 필요한가?

Redshift에서는 동시에 다음과 같은 다양한 쿼리가 혼합되어 실행됩니다:

- 짧은 운영 쿼리
- 장기 배치/리포트 쿼리
- adhoc 분석 쿼리

WLM이 없으면 장기 쿼리가 시스템 리소스를 소모해 전체 성능을 저하시킬 수 있습니다.

---

## WLM의 핵심 개념

### 1️⃣ 서비스 클래스(Service Class)

- WLM의 기본 단위, 즉 "큐"
- 각 큐는 서로 다른 리소스 비율을 가집니다

예:

- 운영 쿼리 큐
- ETL 전용 큐
- BI 전용 큐

---

### 2️⃣ 큐별 리소스 할당

- 메모리 비율
- 동시 실행 가능한 쿼리 수
- 우선순위

---

### 3️⃣ 쿼리 라우팅

- 사용자
- 사용자 그룹
- 쿼리 그룹
- SQL 레이블

위 항목들에 따라 쿼리가 자동으로 적절한 큐에 배정됩니다.

---

### 4️⃣ 쿼리 모니터링 규칙(QMR)

- 실행 시간 초과
- 스캔량 과다
- CPU 사용 과다

조건 발생 시 다음과 같은 조치를 취할 수 있습니다:

- 쿼리 취소
- 우선순위 변경
- 경고 기록

---

## WLM 유형

### 🔹 Manual WLM

- 큐와 리소스를 수동으로 설정
- 세밀한 제어 가능
- 운영 부담이 있음

### 🔹 Auto WLM (권장)

- Redshift가 자동으로 조정
- 워크로드 변화에 유연하게 대응
- 관리 오버헤드 최소화

---

## WLM과 시스템 뷰의 관계

- SVCS: 서비스 클래스별 성능 통계
- STL_ALERT_EVENT_LOG: QMR 관련 경고 로그
- STL_WLM_QUERY: 쿼리와 큐의 매핑 정보

---

## 언제 WLM을 튜닝하나?

- 장기 실행 쿼리로 인해 전체 성능이 저하될 때
- 특정 사용자나 팀의 쿼리가 전체에 영향을 줄 때
- BI 대시보드 응답이 느려질 때

---

## 포인트

- WLM = 큐 기반 성능 관리
- “장기 쿼리 격리”를 위해 WLM 사용
- “서비스 클래스”가 WLM의 핵심 단위
- “QMR”로 쿼리의 이상 상태를 감지하고 제어
