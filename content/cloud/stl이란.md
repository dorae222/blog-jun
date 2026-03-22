---
title: "STL이란?"
slug: stl이란
category: cloud
tags: ["amazon-redshift", "database-logs", "performance-analysis", "query-logs", "sql", "stl", "system-tables", "troubleshooting"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-02T01:08:07.933499+00:00"
---

## STL이란?

**STL(System Table Logs)**은 Amazon Redshift가 **쿼리 실행 중 발생하는 모든 내부 이벤트·통계·경고를 기록하는 시스템 로그 테이블 집합**입니다.

> ✔️ Redshift 클러스터가 내부적으로 생성
> ✔️ 쿼리 성능 분석·트러블슈팅 용도
> ✔️ 읽기 전용

---

## STL의 핵심 역할

- 쿼리 실행 과정을 추적
- 장기 실행 쿼리의 원인 분석
- 성능 저하·병목·경고 이벤트 파악
- 쿼리 최적화 판단 근거 제공

---

## STL vs 다른 시스템 테이블

| 구분   | 역할 |
| ------ | ---- |
| **STL** | **실제 쿼리 실행 중 발생한 로그(이상/경고/실행 기록)** |
| STV    | 실시간 상태(View) |
| SVL    | STL + STV 요약(View) |
| SVCS   | 서비스 수준 통계 |

---

### 🔑 포인트

- **STL = System Table Logs**
- “경고 / 이상 / 최적화 경고” → **STL Alert Event Log**
- “실행 계획” → STL Plan Info
- “메트릭” → STL Query Metrics