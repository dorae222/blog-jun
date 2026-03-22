---
title: SVCS(System View Service Class Statistics) — Redshift WLM 서비스 클래스별 성능 통계
slug: "svcssystem-view-service-class-statistics--redshift-wlm-서비스-클래스별-성능-통계"
category: cloud
tags: ["amazon-redshift", "aws", "cloud", "database-performance", "monitoring", "query-performance", "sql", "svcs", "wlm"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.823076+00:00"
---

## SVCS란?

**SVCS(System View Service Class Statistics)** 는 Amazon Redshift에서 **워크로드 관리(WLM) 서비스 클래스별 쿼리 실행 통계와 성능 지표를 제공하는 시스템 뷰**입니다.

- ✔️ 서비스 클래스(WLM 큐) 기준
- ✔️ 쿼리 처리량·대기 시간·실행 시간 분석
- ✔️ 성능 튜닝 및 병목 분석 용도
- ✔️ 읽기 전용

---

## 한 줄 정의

> **SVCS는 Redshift WLM 서비스 클래스별 쿼리 성능 통계를 제공하는 시스템 뷰다.**

---

## SVCS가 중요한 이유

Redshift에서 성능 문제의 많은 원인은 다음과 같습니다:

- 특정 **WLM 큐(서비스 클래스)** 가 과부하
- 쿼리 대기 시간 증가
- 잘못된 리소스 할당

👉 **SVCS는 “어느 서비스 클래스가 병목인지”를 바로 보여줍니다.**

---

## SVCS에서 확인할 수 있는 주요 정보

- 서비스 클래스 ID
- 실행된 쿼리 수
- 평균 실행 시간
- 평균 대기 시간
- CPU 사용 시간
- 디스크 I/O

예:

```sql
SELECT * FROM svcs_query_summary;
```

---

## STL / STV / SVL / SVCS 비교 (최종 정리)

|구분|의미|목적|
|---|---|---|
|**STL**|System Table Logs|상세 실행 로그|
|**STV**|System Table Views|실시간 상태|
|**SVL**|System View Logs|로그 요약|
|**SVCS**|Service Class Stats|WLM 성능 분석|

---

## 언제 SVCS를 쓰나?

- 장기 실행 쿼리 원인 분석
- WLM 큐 튜닝
- 사용자/쿼리 그룹별 리소스 사용 분석
- 운영 성능 모니터링

---

## 핵심 포인트

- **SVCS = WLM / 서비스 클래스**
- “큐별 성능” → SVCS
- “리소스 할당/대기 시간” → SVCS